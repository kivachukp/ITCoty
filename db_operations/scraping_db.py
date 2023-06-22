import configparser
import json
import re
from utils.additional_variables.additional_variables import admin_database, archive_database, admin_table_fields, \
    valid_professions, reject_table as reject_database
from utils.additional_variables.additional_variables import table_list_for_checking_message_in_db, \
    short_session_database, vacancy_table, additional_elements, vacancies_database
import psycopg2
from datetime import datetime
from logs.logs import Logs
from helper_functions import helper_functions as helper
from patterns._export_pattern import export_pattern
import pandas as pd
logs = Logs()

config = configparser.ConfigParser()
config.read("./../settings/config.ini")

# ---------------------DB operations ----------------------
class DataBaseOperations:

    def __init__(self, **kwargs):
        self.con = kwargs['con'] if 'con' in kwargs else None
        if not self.con:
            self.connect_db()
        self.report = kwargs['report'] if 'report' in kwargs else None
        self.admin_check_file = './logs/check_file.txt'

    def connect_db(self):

        if not self.con:
            self.con = None
            config.read("./../settings/config.ini")
            try:
                database = config['DB3']['database']
                user = config['DB3']['user']
                password = config['DB3']['password']
                host = config['DB3']['host']
                port = config['DB3']['port']
            except:
                config.read("./settings/config.ini")
                database = config['DB_local_clone']['database']
                user = config['DB_local_clone']['user']
                password = config['DB_local_clone']['password']
                host = config['DB_local_clone']['host']
                port = config['DB_local_clone']['port']

            try:
                self.con = psycopg2.connect(
                    database=database,
                    user=user,
                    password=password,
                    host=host,
                    port=port
                )
            except:
                print('No connect with db')
        else:
            pass
            # print('You are in connections with database')

        return self.con
    #-------------participants-------------------------
    def push_to_bd_participants(self, participant, all_user_dictionary, channel_name, channel_username):

        logs.write_log(f"scraping_db: function: push_to_bd_participants")

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()
        with self.con:

            cur.execute("""CREATE TABLE IF NOT EXISTS participant_table (
                        id SERIAL PRIMARY KEY,
                        id_participant VARCHAR(40),
                        first_name VARCHAR(150),
                        last_name VARCHAR (150),
                        user_name VARCHAR (40),
                        phone VARCHAR (40),
                        is_bot BOOLEAN,
                        channel VARCHAR (150),
                        entity JSONB
                        );"""
                                )
            # self.con.commit()

        with self.con:

            channel = channel_name
            print('all user len = ', len(all_user_dictionary))
            for i in all_user_dictionary:

                id_participant = i['id']
                first_name = i['first_name']
                last_name = i['last_name']
                user_name = i['user']
                phone = i['phone']
                is_bot = i['is_bot']
                entity = json.dumps(i)

                print(i)


                query = f"""SELECT * FROM participant_table WHERE id_participant='{id_participant}' AND channel='{channel_name}'"""
                cur.execute(query)
                response = cur.fetchall()

                if not response:
                    new_post = f"""INSERT INTO participant_table (id_participant, first_name, last_name, user_name, phone, is_bot, channel, entity)
                                            VALUES ('{id_participant}', '{first_name}', '{last_name}', '{user_name}', '{phone}', '{is_bot}', '{channel}', {entity});"""
                    try:
                        cur.execute(new_post)

                        # self.con.commit()

                        print('!!!!!!!!!!!!!add to users ', i)
                    except Exception as e:
                        print(e)
                else:
                    print('This user exist already', i)
    #--------------------------------------------------
    def check_or_create_table(self, table_name, cur=None, fields=None):
        if not fields:
            fields = vacancy_table

        cur = self.con.cursor()

        with self.con:
            try:
                cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} ({fields});""")
                print(f'table {table_name} has been crated or exists')
            except Exception as ex:
                print(f"error in check_or_create_table: {ex}")

    def push_to_bd(self, results_dict, profession_list=None, agregator_id=None, shorts_session_name=None):

        response_dict = {}
        pro = profession_list['profession']
        self.quant = 1
# -------------------------- create short message --------------------------------
        if type(pro) in [list, set, tuple]:
            pro_set = pro
        else:
            pro_set = [pro]

        for pro in pro_set:
            self.check_or_create_table(table_name=pro)
            response_dict = self.push_to_db_write_message(pro, results_dict, response_dict, agregator_id, shorts_session_name)
        return response_dict

    def push_to_db_write_message(self, pro, results_dict, response_dict, agregator_id, shorts_session_name=None, cur=None):

        logs.write_log(f"scraping_db: function: push_to_db_write_message")

        vacancy_exists = self.check_vacancy_exists_in_db(tables_list=[pro], title=results_dict['title'], body=results_dict['body'])
        if not vacancy_exists['has_been_found']:
            results_dict['sub'] = helper.decompose_from_str_to_list(data_str=results_dict['sub']) if results_dict['sub'] else None
            if results_dict['sub']:
                if pro in results_dict['sub']:
                    results_dict['sub'] = f"{pro}: {', '.join(results_dict['sub'][pro])}"
                else:
                    results_dict['sub'] = f"{pro}: "
            response_dict[pro] = False

            results_dict_for_post = results_dict.copy()

            new_post_to_vacancies_table = self.compose_query(vacancy_dict=results_dict_for_post, table_name=vacancies_database, define_id=True)
            new_post = self.compose_query(vacancy_dict=results_dict_for_post, table_name=pro, define_id=False)

            cur = self.con.cursor()
            with self.con:
                try:
                    cur.execute(new_post)
                    print(self.quant, f'+++++++++++++ The vacancy has been added to DB {pro}\n')
                    cur.execute(new_post_to_vacancies_table)
                    print(self.quant, f'+++++++++++++ The vacancy has been added to DB {vacancies_database}\n')
                    self.quant += 1
                    try:
                        self.push_vacancy_to_main_stats(profession=pro, dict=results_dict)
                        print(f'+++++++++++++ Added to statistics\n')
                    except Exception as e:
                        print('Did not push to statistics', e)
                        pass
                except Exception as e:
                    print('Did not push to DB ', e)
                    pass

                self.quant += 1
            pass
        else:
            pass
            response_dict[pro] = True
            print(self.quant, f'!!!! This message exists already in {pro}\n')

        return response_dict

    def clear_title_or_body(self, text):
        text = text.replace('\'', '\"')
        return text

    def get_all_from_db(self, table_name, param='', without_sort=False, order=None, field='*', curs=None):

        self.connect_db()
        cur = self.con.cursor()
        if not order:
            order = "ORDER BY time_of_public"
        if not without_sort:
            query = f"""SELECT {field} FROM {table_name} {param} {order}"""
        else:
            query = f"""SELECT {field} FROM {table_name} {param} """

        try:
            with self.con:
                try:
                    cur.execute(query)
                    response = cur.fetchall()
                except Exception as e:
                    print(e)
                    return str(e)
            if curs:
                return cur
            return response
        except Exception as ex:
            print(f"\nerror in get_all_from_db: {ex}\n")
            return False

    async def get_all_from_db_async(self, table_name, param='', without_sort=False, order=None, field='*', curs=None):
        response = []
        cur = None
        if self.con:
            self.con.close()
        if not self.con:
            config.read("./../settings/config.ini")
            try:
                database = config['DB3']['database']
                user = config['DB3']['user']
                password = config['DB3']['password']
                host = config['DB3']['host']
                port = config['DB3']['port']
            except:
                config.read("./settings/config.ini")
                database = config['DB_local_clone']['database']
                user = config['DB_local_clone']['user']
                password = config['DB_local_clone']['password']
                host = config['DB_local_clone']['host']
                port = config['DB_local_clone']['port']
            try:
                self.con = psycopg2.connect(
                    database=database,
                    user=user,
                    password=password,
                    host=host,
                    port=port
                )
                cur = self.con.cursor()
                if not order:
                    order = "ORDER BY time_of_public"
                if not without_sort:
                    query = f"""SELECT {field} FROM {table_name} {param} {order}"""
                else:
                    query = f"""SELECT {field} FROM {table_name} {param} """
                try:
                    with self.con:
                        try:
                            cur.execute(query)
                            response = cur.fetchall()
                        except Exception as e:
                            print(e)
                            return str(e)
                except Exception as e:
                    print(e)
            except:
                print('No connect with db')
            finally:
                if self.con:
                    self.con.close()
        if curs:
            return cur
        return response

    def write_current_session(self, current_session):
        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        query = """CREATE TABLE IF NOT EXISTS current_session (
                    id SERIAL PRIMARY KEY,
                    session VARCHAR(15) UNIQUE
                    );"""
        with self.con:
            cur.execute(query)
            print('session create or exists')

        query = f"""INSERT INTO current_session (session) VALUES ({current_session})"""
        with self.con:
            try:
                cur.execute(query)
                print(f'session {current_session} was writing')
            except Exception as e:
                print(e)
            pass

    def delete_data(self, table_name, param):

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        query = f"""DELETE FROM {table_name} {param}"""
        with self.con:
            try:
                cur.execute(query)
                print(f'got it, delete data from {table_name}')
            except Exception as e:
                print(f'did not delete the data from {table_name}: {e}')
                return False
        return True

#-----------просто в одну таблицу записать все сообщения без професии, чтобы потом достать, рассортировать и записать в файл ------------------
    def write_to_one_table(self, results_dict):

        logs.write_log(f"scraping_db: function: write_to_one_table")

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        self.check_or_create_table(cur, 'all_messages')  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1

        chat_name = results_dict['chat_name']
        title = results_dict['title'].replace(f'\'', '"')
        body = str(results_dict['body']).replace(f'\'', '"')
        time_of_public = results_dict['time_of_public']
        created_at = datetime.now()

        with self.con:
            try:
                query = f"""SELECT * FROM all_messages WHERE title='{title}' AND body='{body}'"""
                cur.execute(query)
                r = cur.fetchall()

                if not r:

                    new_post = f"""INSERT INTO all_messages (chat_name, title, body, profession, time_of_public, created_at)
                                               VALUES ('{chat_name}', '{title}', '{body}', '{None}', '{time_of_public}', '{created_at}');"""
                    # cur.execute(new_post) #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    print(f'= Added to DB all_messages\n')

                else:
                    print(f'!!!!! This message exists already in all_messages\n')

            except Exception as e:
                print('Dont push in db, error = ', e)
                # return response_dict['error', telethon]
            pass

    def collect_data_for_send_to_bot(self, profession):
        """

        :param profession: get dict and collect phrase type of qa/middle/senior/
        :return: this phrase
        """

        logs.write_log(f"scraping_db: function: collect_data_for_send_to_bot")

        profession_str = ''

        if not profession['block']:
            if profession['profession'] not in ['ad', 'no_sort']:

                if type(profession['profession']) is set: # we get data in list from Alex filter
                    for i in profession['profession']:
                        profession_str += i + '/'
                else:  # we get str from Ruslan filter
                    profession_str = profession['profession'] + '/'

                if profession['junior']>0:
                    profession_str += 'junior/'
                if profession['middle']>0:
                    profession_str += 'middle/'
                if profession['senior']>0:
                    profession_str += 'senior/'
            else:
                profession_str = profession['profession'] + '/'
        else:
            pass
        pass

        return profession_str

    def clear_text_control(self, text):

        logs.write_log(f"scraping_db: function: clear_text_control")

        text = re.sub(r'<[\W\w\d]{1,7}>', '\n', text)
        return text

    def find_last_record(self, response, title_search=None, body_search=None):

        logs.write_log(f"scraping_db: function: find_last_record")

        result = None
        marker = False
        new_response = []

        print('len response = ', len(response))
        print('Last element = ', response[-1])

        for record in response:

            if marker:
                new_response.append(record)

            elif not marker:
                if re.findall(title_search, record[2]) or re.findall(body_search, record[3]):
                    print(f'Find!!! id = {record[0]}\ntext{record[2]}\n{record[3]}')
                    marker = True
        return new_response

    def check_table_companies(self):

        if not self.con:
            self.con = self.connect_db()
        cur = self.con.cursor()
        query = """CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            company VARCHAR(100)
            );
            """
        with self.con:
            cur.execute(query)
            print('Table companies has been created or exists')

    def write_to_db_companies(self, companies):

        logs.write_log(f"scraping_db: function: write_to_db_companies")

        con = self.connect_db()
        cur = con.cursor()

        for company in companies:

            # if company is recruiter, is not the company, do not write to DB
            if not re.findall(r'[Рр]екрутер', company):
                if '\'' in company:
                    company = company.replace('\'', '')
                query = f"""SELECT * FROM companies WHERE company='{company}'"""
                with con:
                    try:
                        cur.execute(query)
                        response = cur.fetchall()
                    except Exception as e:
                        print(e)


                if not response:
                    query = f"""INSERT INTO companies (company) VALUES ('{company}')"""
                    with con:
                        try:
                            cur.execute(query)
                            print(f'to put: {company}')
                        except Exception as e:
                            print('Company has not been write to db:\n', e)

    def rewrite_to_archive(self):

        logs.write_log(f"scraping_db: function: rewrite_to_archive")

        for i in ['backend', 'frontend', 'devops', 'pm', 'product', 'designer', 'analyst',
                                    'fullstack', 'mobile', 'qa', 'hr', 'game', 'ba', 'marketing', 'junior',
                                    'sales_manager']:
        # for i in ['no_sort', 'middle', 'senior']:
            response = self.get_all_from_db(i)
            if not self.con:
                self.connect_db()
            cur = self.con.cursor()
            table_archive = f"{i}_archive"
            self.check_or_create_table(cur=cur, table_name=table_archive)
            for message in response:
                query = f"""INSERT INTO {table_archive} (chat_name, title, body, profession, time_of_public, created_at)
                        VALUES ('{message[1]}', '{message[2]}', '{message[3]}', '{message[4]}', '{message[5]}', '{message[6]}')"""
                with self.con:
                    try:
                        cur.execute(query)
                        print(f'{i} rewrited to {table_archive}')
                    except Exception as e:
                        print('error: ', e)

    def add_columns_to_tables(self, table_list=None, column_name_type=None):
        fields_types = ''
        if not table_list:
            table_list = [admin_database, ]

        if not column_name_type:
            column_name_type = 'sended_to_agregator VARCHAR(30)'

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        for table_name in table_list:

            if type(column_name_type) not in (set, list, tuple):
                column_name_type = [column_name_type]

            for field in column_name_type:
                query = f"""ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {field}"""
                with self.con:
                    try:
                        cur.execute(query)
                        print(f'Added {field} to {table_name}')
                    except Exception as e:
                        print(e)

    def db_drop_columns(self, columns: list, tables: list):
        if not tables:
            tables = valid_professions.copy()
            tables.extend([admin_database, archive_database])

        for table in tables:
            for column in columns:
                query = f"ALTER TABLE {table} DROP COLUMN {column}"
                try:
                    self.run_free_request(request=query)
                except Exception as ex:
                    print(ex)

    def add_columns_to_stat(self, cur, table_name, column_name_type=None):

        if not table_name:
            table_name = 'stat_db'

        query = f"""ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name_type}"""
        try:
            cur.execute(query)
            print(f'Added {column_name_type} to {table_name}')
        except Exception as e:
            print(e)

    def output_tables(self):

        logs.write_log(f"scraping_db: function: output_tables")
        tables_list = []
        db_tables = []

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        query = """select * from information_schema.tables where table_schema='public';"""
        with self.con:
            cur.execute(query)
            result = cur.fetchall()
        summ = 0
        for i in result:
            query = f"SELECT MAX(id) FROM {i[2]}"
            with self.con:
                try:
                    cur.execute(query)
                    result = cur.fetchall()[0][0]
                    print(f"{i[2]} = {result}")
                    if result:
                        summ += result
                        tables_list.append(i[2])
                except Exception as e:
                    print(e)
        print(f'\nвсего записей: {summ}')
        return tables_list

    def delete_table(self, table_name):
        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        query = f"""DROP TABLE {table_name};"""
        with self.con:
            try:
                cur.execute(query)
                print(f'{table_name} was deleted')
            except Exception as e:
                print(e)

    def append_columns(self, table_name_list, column):

        logs.write_log(f"scraping_db: function: append_columns")

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        for table in table_name_list:
            query = f"""ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column};"""

            with self.con:
                cur.execute(query)
                print(f'Added columns to table {table}')

    def run_free_request(self, request, output_text=None, notification=True):

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        if not output_text:
            output_text = 'free_request has got'

        query = request
        with self.con:
            try:
                cur.execute(query)
                if notification:
                    print(output_text)
            except Exception as e:
                print('ERROR ', e)
                return e
            pass
        if "select" in query.lower()[:10]:
            return cur.fetchall()

    def write_pattern_new(self, key, ma, mex, value, table_name='pattern'):

        logs.write_log(f"scraping_db: function: write_pattern_new")

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()
        query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(100),
                    ma BOOLEAN,
                    mex BOOLEAN,
                    value VARCHAR(250)
                    );"""
        with self.con:
            cur.execute(query)

        query = f"""SELECT * FROM {table_name} WHERE key='{key}' AND value='{value}' AND ma={ma} AND mex={mex}"""
        with self.con:
            cur.execute(query)

        if not cur.fetchall():
            query = f"""INSERT INTO {table_name} (key, ma, mex, value) VALUES ('{key}', {ma}, {mex}, '{value}')"""
            with self.con:
                try:
                    cur.execute(query)
                    print(f'add to {table_name} key {key} ma {ma} mex {mex} value {value}')
                except Exception as e:
                    print('error', e)
        else:
            print(f'exists key {key} ma {ma} mex {mex} value {value}')

    def write_pattern2(self, table_name, values):

        logs.write_log(f"scraping_db: function: write_pattern2")

        """
        :param table_name:
        :param values: dict = {'ma': [tuple], 'mex': [tuple]
        :return:
        """

        table_name = f"pattern_{table_name}"
        if not self.con:
            self.connect_db()
        cur = self.con.cursor()
        query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    mex VARCHAR(70),
                    ma VARCHAR(70)
                    );"""
        with self.con:
            cur.execute(query)

        for i in values['ma']:
            with self.con:
                try:
                    query = f"""SELECT * FROM {table_name} WHERE ma='{i}'"""
                    cur.execute(query)
                except Exception as e:
                    print(e)

                if not cur.fetchall():

                    try:
                        query_ma = f"""INSERT INTO {table_name} (ma) VALUES ('{i}')"""
                        cur.execute(query_ma)
                        print(table_name, i)
                    except Exception as e:
                        print(e)
            pass

        for i in values['mex']:
            with self.con:
                try:
                    query = f"""SELECT * FROM {table_name} WHERE mex='{i}'"""
                    cur.execute(query)
                except Exception as e:
                    print(e)

                if not cur.fetchall():

                    try:
                        query_mex = f"""INSERT INTO {table_name} (mex) VALUES ('{i}')"""
                        cur.execute(query_mex)
                        print(table_name, i)
                    except Exception as e:
                        print(e)
            pass
        pass

    def check_or_create_table_admin(self, cur=None, table_name='admin_last_session'):

        if not cur:
            cur = self.con.cursor()

        with self.con:
            try:
                cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
                                id SERIAL PRIMARY KEY,
                                chat_name VARCHAR(150),
                                title VARCHAR(1000),
                                body VARCHAR (6000),
                                profession VARCHAR (30),
                                vacancy VARCHAR (700),
                                vacancy_url VARCHAR (150),
                                company VARCHAR (200),
                                english VARCHAR (100),
                                relocation VARCHAR (100),
                                job_type VARCHAR (700),
                                city VARCHAR (150),
                                salary VARCHAR (300),
                                salary_from INT,
                                salary_to INT,
                                salary_currency VARCHAR(20),
                                salary_period VARCHAR(50),
                                experience VARCHAR (700),
                                contacts VARCHAR (500),
                                time_of_public TIMESTAMP,
                                created_at TIMESTAMP,
                                agregator_link VARCHAR(200),
                                session VARCHAR(15),
                                sended_to_agregator VARCHAR(30),
                                sub VARCHAR (250),
                                tags VARCHAR (700),
                                full_tags VARCHAR (700),
                                full_anti_tags VARCHAR (700),
                                short_session_numbers VARCHAR (300),
                                level VARCHAR (70),
                                approved VARCHAR (100),
                                FOREIGN KEY (session) REFERENCES current_session(session)
                                );"""
                            )
                # print(f'table {table_name} has created or exists')
            except Exception as e:
                print(e)

    def push_to_admin_table(self, results_dict, profession, check_or_exists=True, table_name=admin_database, params=None):
        # results_dict['title'] = self.clear_title_or_body(results_dict['title'])
        # results_dict['body'] = self.clear_title_or_body(results_dict['body'])

        if check_or_exists:
            tables_list_for_vacancy_searching = set(profession['profession']).copy()
            tables_list_for_vacancy_searching.discard('no_sort')
            tables_list_for_vacancy_searching = tables_list_for_vacancy_searching.union(additional_elements)

            has_been_found = self.check_vacancy_exists_in_db(
                    tables_list=tables_list_for_vacancy_searching,
                    title=results_dict['title'],
                    body=results_dict['body'])
            if has_been_found['has_been_found']:
                return {"has_been_found": True, "response_dict": has_been_found['response_dict']}

            has_been_found = self.check_vacancy_exists_in_db(
                tables_list=tables_list_for_vacancy_searching,
                title=self.clear_title_or_body(results_dict['title']),
                body=self.clear_title_or_body(results_dict['body']))
            if has_been_found['has_been_found']:
                return {"has_been_found": True, "response_dict": has_been_found['response_dict']}
        if results_dict['profession'] == 'no_sort':
            table_name = archive_database

        new_post = self.compose_query(vacancy_dict=results_dict, table_name=table_name)

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()
        self.check_or_create_table_admin(cur)
        with self.con:
            try:
                cur.execute(new_post)
                print(f'+++++++++++++ The vacancy has been added to DB {table_name}\n')
                if self.report:
                    self.report.parsing_report(profession=results_dict['profession'])
                    self.report.parsing_report(has_been_added_to_db=True)
                return {"has_been_found": False, "response_dict": results_dict}

            except Exception as e:
                if self.report:
                    self.report.parsing_report(has_been_added_to_db=False)
                    self.report.parsing_report(error=str(e))

                print(f'-------------- Didn\'t push in ADMIN LAST SESSION {e}\n')
                return {"has_been_found": False, "response_dict": results_dict}


    def check_vacancy_exists_in_db(self, tables_list, title, body):

        response_check = []
        response_check2 = []
        response_check3 = []
        # if results_dict['title']:
        #     results_dict['title'] = self.clear_title_or_body(results_dict['title'])
        # if results_dict['body']:
        #     results_dict['body'] = self.clear_title_or_body(results_dict['body'])
        # if results_dict['company']:
        #     results_dict['company'] = self.clear_title_or_body(results_dict['company'])
        
        for table in tables_list:
            """
            query1 - full text
            query2 - like text
            query3 - text without "'"
            """
            query1 = f"""SELECT * FROM {table} WHERE title='{title}'""" if "'" not in title \
                else f"""SELECT * FROM {table} WHERE title=$${title}$$"""
            query2 = f"""SELECT * FROM {table} WHERE title LIKE '%{title.strip()}%'""" if "'" not in title \
                else f"""SELECT * FROM {table} WHERE title LIKE $$%{title.strip()}%$$"""
            query3 = f"""SELECT * FROM {table} WHERE title='{self.clear_title_or_body(title)}'"""
            
            if body:
                query1 += f" AND body='{body}'" if "'" not in body else f" AND body=$${body}$$"
                query2 += f" AND body LIKE '%{body.strip()}%'" if "'" not in body else f" AND body LIKE $$%{body.strip()}%$$"
                query3 += f" AND body='{self.clear_title_or_body(body)}'"

            try:
                response_check = self.run_free_request(request=query1, notification=False)
                response_check2 = self.run_free_request(request=query2, notification=False)
                response_check3 = self.run_free_request(request=query3, notification=False)
            except Exception as ex:
                print(f'error in push_to_db_write_message: {ex}')

            if response_check or response_check2 or response_check3:
                for response in [response_check, response_check2, response_check3]:
                    if response:
                        response_dict = helper.to_dict_from_admin_response_sync(
                            response=response[0], fields=admin_table_fields
                        )
                        if response_dict:
                            if self.report:
                                self.report.parsing_report(found_body=body)
                                self.report.parsing_report(found_title=title)
                            return {"has_been_found": True, "response_dict": response_dict}
        return {"has_been_found": False, "response_dict": {}}

        #
        #
        # title = self.clear_title_or_body(title)
        # body = self.clear_title_or_body(body)
        #
        # tables_fields = admin_table_fields
        #
        # for one_element in tables_list:
        #     response = self.get_all_from_db(
        #         table_name=f'{one_element}',
        #         param=f"WHERE title='{title}' AND body='{body}'",
        #         field=tables_fields
        #     )
        #     response_like = self.get_all_from_db(
        #         table_name=f'{one_element}',
        #         param=f"WHERE title LIKE '{title}' AND body LIKE '{body}'",
        #         field=tables_fields
        #     )
        #     if response != response_like:
        #         print("\n\nALARM!! ALARM!! ALARM!\n\n")
        #         print(f"response True") if response else print(f"response False")
        #         print(f"response_like True") if response_like else print(f"response_like False")
        #
        #
        #     if response or response_like:
        #         response = response_like if not response else response
        #         response_dict = helper.to_dict_from_admin_response_sync(
        #             response=response[0],
        #             fields=tables_fields
        #         )
        #         if self.report:
        #             self.report.parsing_report(
        #                 found_title=response_dict['title'],
        #                 found_body=response_dict['body'],
        #                 found_id=response_dict['id'],
        #                 found_vacancy_link=response_dict['vacancy_url']
        #             )
        #             self.report.parsing_report(has_been_added_to_db=False)
        #
        #         print(f'!!!!!!!!!!! Vacancy exists in {one_element} table\n')
        #         return {"has_been_found": True, "response_dict": response_dict}
        # return {"has_been_found": False, "response_dict": {}}

    def push_followers_statistics(self, channel_statistic_dict:dict):

        logs.write_log(f"scraping_db: function: push_followers_statistics")

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        for number in range(0, len(channel_statistic_dict['channel'])):
            channel = channel_statistic_dict['channel'][number]
            id_user = channel_statistic_dict['id_user'][number]
            access_hash = channel_statistic_dict['access_hash'][number]
            username = channel_statistic_dict['username'][number]
            first_name = channel_statistic_dict['first_name'][number]
            last_name = channel_statistic_dict['last_name'][number]
            join_time = channel_statistic_dict['join_time'][number]
            is_bot = channel_statistic_dict['is_bot'][number]
            mutual_contact = channel_statistic_dict['mutual_contact'][number]

            print('join_time = ', join_time, type(join_time))
            if type(join_time) is str:
                join_time = join_time.split(' ')
                date = join_time[0].split('-')
                time = join_time[1].split(':')
                join_time = datetime(int(date[2]), int(date[1]), int(date[0]), int(time[0]), int(time[1]), int(time[2]))
            else:
                join_time = None

            with self.con:
                cur.execute(f"""CREATE TABLE IF NOT EXISTS followers_statistics (
                                            id SERIAL PRIMARY KEY,
                                            channel VARCHAR(150),
                                            id_user VARCHAR(30),
                                            access_hash VARCHAR (100),
                                            username VARCHAR (100),
                                            first_name VARCHAR (100),
                                            last_name VARCHAR (100),
                                            join_time TIMESTAMP,
                                            is_bot BOOLEAN,
                                            mutual_contact BOOLEAN
                                            );"""
                            )
            query_check = f"""SELECT * FROM followers_statistics
                            WHERE channel='{channel}' AND id_user='{id_user}'"""
            with self.con:
                cur.execute(query_check)
                r = cur.fetchall()
            if not r:
                pass
                if join_time:
                    new_participant = f"""INSERT INTO followers_statistics
                                    (channel, id_user, access_hash, username, first_name,
                                    last_name, join_time, is_bot, mutual_contact)
                                    VALUES ('{channel}', '{id_user}', '{access_hash}', '{username}', '{first_name}',
                                    '{last_name}', '{join_time}', {is_bot}, {mutual_contact});"""
                else:
                    new_participant = f"""INSERT INTO followers_statistics
                                                        (channel, id_user, access_hash, username, first_name,
                                                        last_name, is_bot, mutual_contact)
                                                        VALUES ('{channel}', '{id_user}', '{access_hash}', '{username}', '{first_name}',
                                                        '{last_name}', {is_bot}, {mutual_contact});"""

                with self.con:
                    cur.execute(new_participant)
                    print(f'{id_user} in {channel} was writed')
            else:
                print(f'{id_user} in {channel} exists already')

    def try_and_delete_after(self):

        logs.write_log(f"scraping_db: function: try_and_delete_after")

        a = 'Mother"s fucker'
        b = f"Mother's fucker 2"
        if not self.con:
            self.connect_db()
        cur = self.con.cursor()
        query = """CREATE TABLE IF NOT EXISTS try (
                    id SERIAL PRIMARY KEY,
                    value VARCHAR(1000)
                    );"""
        with self.con:
            cur.execute(query)
            print('Table created or exists')

        query = f"""INSERT INTO try (value) VALUES ('{a}')"""
        with self.con:
            try:
                cur.execute(query)
                print('Data was creating')
            except Exception as e:
                print(f'Error ', e)

    def add_password_to_user(self, id, password):

        logs.write_log(f"scraping_db: function: add_password_to_user")

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        query = f"""UPDATE users SET password='{password}' WHERE id={id}"""
        try:
            with self.con:
                cur.execute(query)
                print('password added')
        except Exception as e:
            print('Something is wrong ', e)

    def create_table_users(self):
        if not self.con:
            self.connect_db()
        cur = self.con.cursor()
        with self.con:
            cur.execute(f"""CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                id_user VARCHAR(20),
                api_id VARCHAR(20),
                api_hash VARCHAR (50),
                phone_number VARCHAR (25),
                password VARCHAR (100)
                );"""
                        )

    def write_user_without_password(self, id_user, api_id, api_hash, phone_number):
        logs.write_log(f"scraping_db: function: write_user_without_password")

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        self.create_table_users()

        query_does_user_exist = f"""SELECT * FROM users WHERE api_id='{api_id}'"""
        with self.con:
            cur.execute(query_does_user_exist)
        r= cur.fetchall()

        if not r:
            query = f"""INSERT INTO users (id_user, api_id, api_hash, phone_number) VALUES ('{id_user}', '{api_id}', '{api_hash}', '{phone_number}')"""
            try:
                with self.con:
                    cur.execute(query)
                    print(f'user {id_user}has been added to db')
            except Exception as e:
                print(f"Didn't write the user to db. Because: {e}")
        else:
            print('user exists')

    def change_type_column(self, list_table_name, name_and_type='title VARCHAR(4096)'):

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()

        for table_name in list_table_name:
            # query_for_change_type = f"""ALTER TABLE {table_name} ALTER COLUMN {name_and_type}"""

            query_for_change_type = f"""ALTER TABLE {table_name} ALTER COLUMN {name_and_type}"""
            with self.con:
                try:
                    print(query_for_change_type)
                    cur.execute(query_for_change_type)
                    print(f'changed field in {table_name}')
                except Exception as e:
                    print(f"field in {table_name} didn't change for reason {e}")

    def check_admin_temporary(self, cur):
        cur = self.con.cursor()
        with self.con:

            cur.execute(f"""CREATE TABLE IF NOT EXISTS admin_temporary (
                            id SERIAL PRIMARY KEY,
                            id_admin_channel VARCHAR(20),
                            id_admin_last_session_table VARCHAR(20),
                            sended_to_agregator VARCHAR(30)
                            );"""
                        )

    def push_to_admin_temporary(self, composed_message_dict):

        logs.write_log(f"scraping_db: function: push_to_admin_temporary")

        if not self.con:
            self.connect_db()
        cur = self.con.cursor()
        self.check_admin_temporary(cur)

        id_admin_channel = composed_message_dict['id_admin_channel']
        id_admin_last_session_table = composed_message_dict['db_id']
        it_was_sending_to_agregator = composed_message_dict['it_was_sending_to_agregator']

        # -------------- it is for user's check -----------------------
        response = self.get_all_from_db(
            table_name='admin_last_session',
            param=f"WHERE id={id_admin_last_session_table}",
            field="title"
        )
        title_temp = response[0][0]
        # title_temp = re.sub(r"\\u[^\W]+", '', title_temp)

        with open(self.admin_check_file, 'a', encoding="utf-8") as file:
            try:
                file.write(f"--------in function push_to_admin_temporary-------\n"
                           f"id admin_channel = {id_admin_channel}\n"
                           f"id_admin_last_session_table = {id_admin_last_session_table}\n"
                           f"it was sending to agregator = {it_was_sending_to_agregator}\n"
                           f"title = {title_temp[0:50]}\n"
                           f"------------------------------------------------------------\n")
            except Exception as e:
                print(f'Error in the file writing\n{e}\n{title_temp}')
        # ----------------------- end ----------------------------------

        query_check = f"""SELECT * FROM admin_temporary
                WHERE id_admin_channel='{id_admin_channel}'
                AND id_admin_last_session_table = '{id_admin_last_session_table}'"""

        with self.con:
            try:
                cur.execute(query_check)
            except:
                print('It cant check un db')

        if not cur.fetchall():

            query = f"""INSERT INTO admin_temporary (id_admin_channel, id_admin_last_session_table, sended_to_agregator)
                        VALUES ('{id_admin_channel}', '{id_admin_last_session_table}', '{it_was_sending_to_agregator}')"""

            with self.con:
                try:
                    cur.execute(query)
                    print(f'Writed to admin_temporary {id_admin_channel}-{id_admin_last_session_table}-{it_was_sending_to_agregator}')
                except Exception as e:
                    print('Error in admin_temporary ', e)

        else:
            print('Record exists in admin_temporary')

        pass

    def drop_profession_in_admin_db(self, drop_profession):
        current_id_agregator = ''
        query2 = ''
        response_admin_temporary = self.get_all_from_db('admin_temporary', without_sort=True)
        for item in response_admin_temporary:
            new_profession = ''
            id_db = item[2]
            query = f"""SELECT profession FROM admin_last_session WHERE id={id_db}"""
            if not self.con:
                self.connect_db()
            cur = self.con.cursor()
            with self.con:
                cur.execute(query)
            r = cur.fetchall()
            if r:
                professions = r[0][0].split(',')
                print(professions, len(professions))

                if len(professions)>1:
                    for i in professions:
                        i = i.strip()
                        if i != drop_profession:
                            new_profession += f'{i}, '
                    new_profession = new_profession[:-2]
                    query = f"""UPDATE admin_last_session SET profession='{new_profession}' WHERE id={id_db}"""
                    query2 = f"""UPDATE admin_last_session SET sended_to_agregator='{current_id_agregator}' WHERE id={id_db}"""
                else:
                    query = f"""DELETE FROM admin_last_session WHERE id={id_db}"""

                with self.con:
                    try:
                        cur.execute(query)
                        print('got it')
                        if query2:
                            cur.execute(query)
                            print('got it 2')
                    except Exception as e:
                        print('Not changing profession ', e)

        self.delete_table('admin_temporary')
        pass

    def check_doubles(self):
        doubles_dict = {}
        response = self.get_all_from_db(
            table_name='admin_last_session',
            field='id, title, body, profession',
            param="WHERE profession <> 'no_sort'"
        )
        for vacancy1 in response:
            id = vacancy1[0]
            title = vacancy1[1]
            body = vacancy1[2]
            index_from = response.index(vacancy1)
            print('index_from: ', index_from)

            for next_vacancy in range(index_from + 1, len(response)):
                vacancy2 = response[next_vacancy]
                if title == vacancy2[1] and body == vacancy2[2]:
                    doubles_dict[id] = vacancy2[0]
                    print('doubles_dict: ', doubles_dict[id])
                else:
                    pass
        for i in doubles_dict:
            print('results', i, doubles_dict[i])
            print('-------------------------------')
        print('total: ', len(doubles_dict))

        n=1
        for id in doubles_dict:
            response1 = self.get_all_from_db(
                table_name='admin_last_session',
                param=f"WHERE id={int(id)}",
                field='title, body'
            )
            response2 = self.get_all_from_db(
                table_name='admin_last_session',
                param=f"WHERE id={doubles_dict[int(id)]}",
                field='title, body'
            )
            response1 = response1[0]
            response2 = response2[0]
            if response1[0] == response2[0] and response1[1] == response2[1]:
                print(f'{n} id: ', id)
                print('it must be deleted')
                self.delete_data(
                    table_name='admin_last_session',
                    param=f"WHERE id={id}"
                )
                n += 1
        return {'doubles': len(doubles_dict), 'vacancy_numbers': len(response)}

    def check_double_in_professions(self):
        response = self.get_all_from_db(
            table_name='admin_last_session',
            field='id, title, body, profession',
            param="WHERE profession <> 'no_sort'"
        )

        doubles_list = []
        logic_box = []

        for vacancy in response:
            logic_box = []
            id = vacancy[0]
            title = vacancy[1]
            body = vacancy[2]
            profession = vacancy[3].split(', ')

            for table in profession:
                response_from_table = self.get_all_from_db(
                    table_name=table,
                    param=f"WHERE title='{title}' and body='{body}'"
                )
                if response_from_table:
                    logic_box.append(1)
                    print(f'it exists in {table}')
                else:
                    logic_box.append(0)
            if sum(logic_box) > 0:
                doubles_list.append(id)

        print('quantity messages: ', len(response))
        print('total doubles: ', len(doubles_list))
        n = 1
        for id in doubles_list:
            print(f'{n}: It must be deleted - {id}')
            self.delete_data(
                table_name='admin_last_session',
                param=f"WHERE id={id}"
            )
            n += 1
        return {'doubles': len(doubles_list), 'vacancy_numbers': len(response)}

    def remove_completed_professions(self):
        response = self.get_all_from_db(
            table_name='admin_last_session',
            field='id, title, body, profession',
            param="WHERE profession <> 'no_sort'"
        )
        answer_dict = {}
        answer_dict['messages'] = len(response)
        answer_dict['deleted'] = 0
        answer_dict['change_profession'] = 0
        for vacancy in response:
            id = vacancy[0]
            title = vacancy[1]
            body = vacancy[2]
            profession = vacancy[3]

            profession = helper.string_to_list(text=profession, separator=', ')
            for table in profession:
                table_response = self.get_all_from_db(
                    table_name=table,
                    param=f"WHERE title='{title}' AND body='{body}'"
                )
                if table_response:
                    profession.remove(table)
                    if not profession:
                        self.delete_data(table_name='admin_last_session', param=f"WHERE id={id}")
                        answer_dict['deleted'] += 1
                    else:
                        new_profession = helper.list_to_string(raw_list=profession, separator=', ')
                        self.update_table(table_name='admin_last_session', param=f"WHERE id={id}", field='profession', value=new_profession)
                        r = self.get_all_from_db(table_name='admin_last_session', param=f'WHERE id={id}', field='profession')
                        print(r[0][0])
                        answer_dict['change_profession'] += 1

        return answer_dict

    def update_table(self, table_name, field, value, output_text='vacancy has updated', param=""):
        query = f"""UPDATE {table_name} SET {field}='{value}' {param}"""
        self.run_free_request(request=query, output_text=output_text)

    def update_table_multi(self, table_name: str, param: str, values_dict: dict, output_text='vacancy has updated'):
        query = f"""UPDATE {table_name} SET"""
        for key in values_dict:
            if key != 'id':
                query += f" {key}='{values_dict[key]}', " if values_dict[key] else ''

        if query.split(' ')[-1] != "SET":
            query = f"{query[:-2]} {param}"
            try:
                self.run_free_request(request=query, output_text=output_text)
                return True
            except Exception as e:
                print(e)
                return False
        else:
            print('Nothing to write to db')

    def check_exists_message_by_link_or_url(self, title=None, body=None, vacancy_url=None, table_list=None):

        # print("??????????start_check_exists_message_by_link_or_url")

        param = "WHERE "
        length = len(param)

        if not table_list:
            table_list = table_list_for_checking_message_in_db
        if vacancy_url:
            param += f"vacancy_url LIKE '%{vacancy_url}%'"
        elif body or title:
            if title:
                param += f"title='{self.clear_title_or_body(title)}'"
            if body:
                if len(param) > length:
                    param += ' AND '
                param += f"body='{self.clear_title_or_body(body)}'"
        else:
            return {''}

        for table in table_list:
            response = self.get_all_from_db(
                table_name=table,
                param=param,
                field='id, vacancy_url',
                without_sort=True
            )
            if response:
                if self.report:
                    if vacancy_url:
                        self.report.parsing_report(found_id_by_link=response[0][1])
                    else:
                        self.report.parsing_report(found_title=title, found_body=body, found_id=response[0][0])
                # print("??????????finish_check_exists_message_by_link_or_url")
                return False
        # print("??????????finish_check_exists_message_by_link_or_url")
        return True

    def write_short_session(self, short_session_name):
        if not self.con:
            self.connect_db()
        self.create_or_exists_short_session()
        cur = self.con.cursor()
        with self.con:
            cur.execute(f"""INSERT INTO shorts_session_name (session_name) VALUES ('{short_session_name}');""")

    def create_or_exists_short_session(self):
        if not self.con:
            self.connect_db()
        cur = self.con.cursor()
        # self.delete_table('shorts_session_name')
        with self.con:
            query = """CREATE TABLE IF NOT EXISTS shorts_session_name (
                            id SERIAL PRIMARY KEY,
                            session_name VARCHAR(50)
                        );"""
            cur.execute(query)

            print('short_session_name table has created')

    def get_information_about_tables_and_fields(self, only_tables=False):
        tables_list = []
        if not self.con:
            self.con = self.connect_db()
        cur = self.con.cursor()
        query = "select table_name, column_name from information_schema.columns where table_schema='public'"
        with self.con:
            cur.execute(query)
        if not only_tables:
            return cur.fetchall()
        else:
            for table in cur.fetchall():
                if table[0] not in tables_list:
                    tables_list.append(table[0])
            return tables_list



    def transfer_vacancy(self, table_from, table_to, id=None, response_from_db=None):
        keys_str = ''
        values_str = ''

        if not response_from_db:
            response = self.get_all_from_db(
                table_name=table_from,
                param=f"WHERE id={id}",
                field=admin_table_fields
            )
            if response:
                response = response[0]
        else:
            response = response_from_db

        if response:
            if type(response) is dict:
                response_dict = response
            elif type(response) is list:
                response_dict = helper.to_dict_from_admin_response_sync(response, admin_table_fields)
            else:
                return TypeError

            for keys in response_dict:
                if keys != 'id':
                    keys_str += f"{keys}, "
                    values_str += f"'{response_dict[keys]}', "
            query = f"INSERT INTO {table_to} ({keys_str[:-2]}) VALUES ({values_str[:-2]})"
            try:
                self.run_free_request(query)
                return True
            except Exception:
                return False
        else:
            return  False

    def check_or_create_stats_table(self, table_name=None, profession_list=[]):
        if not self.con:
                self.connect_db()
        if not table_name:
            table_name='stats_db'
        if not profession_list:
            profession_list=['designer', 'game', 'product', 'mobile', 'pm', 'sales_manager', 'analyst', 'frontend', 'marketing', 'devops', 'hr', 'backend', 'qa', 'junior']
        self.delete_table(table_name)
        cur = self.con.cursor()
        with self.con:
            cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
                                created_at DATE,
                                chat_name VARCHAR(150)
                                );"""
                            )
        for i in profession_list:
            list=[f'{i}_all', f'{i}_unique']
            for j in list:
                self.add_columns_to_tables(table_list=[table_name], column_name_type = f'{j} INT DEFAULT 0')

        print(f'table {table_name} has been created or exists')

    def push_vacancy_to_main_stats(self, profession, dict, table_name=None):
        if not self.con:
            self.connect_db()
        if not table_name:
            table_name='stats_db'
        created_at = dict['created_at']
        chat_name = dict['chat_name']
        subs_list=helper.decompose_from_str_to_subs_list(dict['sub'])
        all=f'{profession}_all'
        unique=f'{profession}_unique'

        cur = self.con.cursor()
        for sub in subs_list:
            self.add_columns_to_stat(cur,table_name, column_name_type = f'{sub} INT DEFAULT 0')
            self.add_columns_to_stat(cur,table_name, column_name_type = f'{all} INT DEFAULT 0')
            self.add_columns_to_stat(cur,table_name, column_name_type = f'{unique} INT DEFAULT 0')
            query = f"""SELECT * FROM {table_name} WHERE created_at='{created_at}' AND chat_name='{chat_name}'"""

            cur = self.con.cursor()
            cur.execute(query)

            if not cur.fetchall():
                query = f"""INSERT INTO {table_name} (chat_name, created_at, {sub}, {all}) VALUES ('{chat_name}','{created_at}','1', '1')"""

                try:
                    cur.execute(query)
                    print("Vacancy was added to subs_stats")
                except Exception as e:
                    print('error', e)

            else:
                query = f"""UPDATE {table_name} SET {sub} = {sub}+1, {all} = {all}+1 WHERE chat_name = '{chat_name}' AND created_at = '{created_at}'"""

                try:
                    cur.execute(query)
                    print(f"Vacancy was added to subs_stats")
                except Exception as e:
                    print('error', e)

        query = f"""UPDATE {table_name} SET {unique}={unique}+1 WHERE chat_name = '{chat_name}' AND created_at = '{created_at}'"""

        try:
            cur.execute(query)
            print("Vacancy was added to subs_stats")
        except Exception as e:
            print('error', e)

        return dict

    def get_all_from_stat_db(self, table_name=None, param='', order=None, field='*'):

        if not self.con:
            self.connect_db()
        if not table_name:
            table_name='stats_db'

        cur = self.con.cursor()

        if not order:
            order = "ORDER BY created_at"

        query = f"""SELECT {field} FROM {table_name} {param} {order}"""
        with self.con:
            try:
                cur.execute(query)
                response = cur.fetchall()
                column_names = [description[0] for description in cur.description]
            except Exception as e:
                print(e)
                return str(e)

        return {'response':response, 'column_names':column_names}

    def add_old_vacancies_to_stat_db(self,table_list=None, fields=None, table_name=None):

        if not table_list:
            table_list=['designer', 'game', 'product', 'mobile', 'pm', 'sales_manager', 'analyst', 'frontend', 'marketing', 'devops', 'hr', 'backend', 'qa', 'junior']
        fields='created_at, chat_name, profession, sub'
        for i in table_list:
            response=self.get_all_from_db(table_name=i, field=fields)
            for j in response:
                result_dict=helper.to_dict_from_admin_response_sync(j, fields)
                self.push_vacancy_to_main_stats(profession=i,dict=result_dict, table_name=i)
            print(f'All vacancies from {i} were added to stats db')

    def make_report_published_vacancies_excel(self, date1, date2, table_name=None):
        """Input date format: '2023-01-02'"""

        if not table_name:
            table_name='stats_db'

        param=f"WHERE DATE(created_at) BETWEEN '{date1}' AND '{date2}'"
        data = self.get_all_from_stat_db(param=param, table_name=table_name)
        columns=data['column_names']
        all=[i for i in columns if 'all' in i]
        unique=[i for i in columns if 'unique' in i]
        df=pd.DataFrame(data['response'], columns=columns)
        df=df.set_index(['created_at'])
        df['Unique']=df[unique].sum(axis=1)
        df['All']=df[all].sum(axis=1)
        df = df[sorted(df.columns )]
        df = df[['chat_name'] + [x for x in df.columns if x!='chat_name']]
        df.loc[f'Total for period {date1}-{date2}']=df.sum(axis=0, numeric_only=True)
        df2=df.groupby('chat_name').sum(numeric_only=True)
        len=df.shape[0]

        with pd.ExcelWriter(f'./excel/report_{date1}_{date2}.xlsx') as writer:
            df.to_excel(writer, sheet_name="Sheet1")
            df2.to_excel(writer, sheet_name="Sheet1", startrow=len+2,startcol=1, header=False)
            print('Report is done, saved')

    def statistics_total(self, date_in, date_out):
        table_name = 'admin_last_session'
        period = f"'{date_in}' AND '{date_out}'"
        field1 = 'DATE (created_at) AS group_date, COUNT(*)'

        param_to_sort = f"WHERE DATE (created_at) BETWEEN {period} GROUP BY group_date"
        order1 = 'ORDER BY group_date'
        data_to_sort = self.get_all_from_db(table_name=table_name, field=field1, order=order1, param=param_to_sort)
        df_to_sort = pd.DataFrame(data_to_sort, columns=['date', 'to_sort'])
        df_to_sort['to_sort'].fillna(0, inplace=True)

        table_name2 = 'archive'
        param_archive = f"WHERE DATE (created_at) BETWEEN {period} AND profession NOT LIKE 'no_sort' GROUP BY group_date"
        data_archive = self.get_all_from_db(table_name=table_name2, field=field1, order=order1, param=param_archive)
        df_archive = pd.DataFrame(data_archive, columns=['date', 'archive'])
        df_archive['archive'].fillna(0, inplace=True)

        param_no_sort = f"WHERE DATE (created_at) BETWEEN {period} AND profession LIKE 'no_sort' GROUP BY group_date"
        data_no_sort = self.get_all_from_db(table_name=table_name2, field=field1, order=order1, param=param_no_sort)
        df_no_sort = pd.DataFrame(data_no_sort, columns=['date', 'no_sort'])
        df_no_sort['no_sort'].fillna(0, inplace=True)

        df_total_archive = df_no_sort.merge(df_archive, how='outer', on='date').sort_values('date')
        df_total_archive.fillna(0, inplace=True)
        df_total = df_to_sort.merge(df_total_archive, how='outer', on='date').sort_values('date')
        df_total.fillna(0, inplace=True)
        df_total.insert(loc=1, column='Total', value=df_total.no_sort + df_total.to_sort + df_total.archive)
        df_total.loc[f'Total for period'] = df_total.sum(axis=0, numeric_only=True)

        field2 = 'DATE (created_at) AS group_date, chat_name, COUNT(*)'
        order2 = 'ORDER BY group_date, chat_name'

        param_to_sort_channels = f"WHERE DATE (created_at) BETWEEN {period} GROUP BY group_date, chat_name"
        data_to_sort_channels = self.get_all_from_db(table_name=table_name, field=field2, order=order2,
                                                     param=param_to_sort_channels)
        df_to_sort_channels = pd.DataFrame(data_to_sort_channels, columns=['date', 'channel', 'to_sort'])
        df_to_sort_channels['to_sort'].fillna(0, inplace=True)

        param_no_sort_channels = f"WHERE DATE (created_at) BETWEEN {period} AND profession LIKE 'no_sort' GROUP BY group_date, chat_name"
        data_no_sort_channels = self.get_all_from_db(table_name=table_name2, field=field2, order=order2,
                                                     param=param_no_sort_channels)
        df_no_sort_channels = pd.DataFrame(data_no_sort_channels, columns=['date', 'channel', 'no_sort'])
        df_no_sort_channels['no_sort'].fillna(0, inplace=True)

        param_archive_channels = f"WHERE DATE (created_at) BETWEEN {period} AND profession NOT LIKE 'no_sort' GROUP BY group_date, chat_name"
        data_archive_channels = self.get_all_from_db(table_name=table_name2, field=field2, order=order2,
                                                     param=param_archive_channels)
        df_archive_channels = pd.DataFrame(data_archive_channels, columns=['date', 'channel', 'archive'])
        df_archive_channels['archive'].fillna(0, inplace=True)

        df_total_archive_channels = df_no_sort_channels.merge(df_archive_channels, how='outer',
                                                              on=['date', 'channel']).sort_values('date')
        df_total_archive_channels.fillna(0, inplace=True)

        df_total_channels = df_to_sort_channels.merge(df_total_archive_channels, how='outer',
                                                      on=['date', 'channel']).sort_values('date')
        df_total_channels.fillna(0, inplace=True)
        df_total_channels.insert(loc=2, column='Total',
                                 value=df_total_channels.no_sort + df_total_channels.to_sort + df_total_channels.archive)
        df_total_channels.loc[f'Total for period'] = df_total_channels.sum(axis=0, numeric_only=True)

        with pd.ExcelWriter(f'./excel/report_total_{date_in}_{date_out}.xlsx') as writer:
            df_total.to_excel(writer, sheet_name="Total", index=False)
            df_total_channels.to_excel(writer, sheet_name="Channels", index=False)
            print('Report is done, saved')

    def create_table_common(self, field_list, table_name):
        query = f"""Create TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, """
        for field in field_list:
            query += f"{field}, "
        query = query[:-2] + ");"

        cur = self.con.cursor()
        with self.con:
            cur.execute(query)
            print(f'table {table_name} has been crated or exists')

    def push_to_db_common(self, table_name, fields_values_dict, params=None, report=False, notification=False):
        if params:
            set_fields = ''
            for key in fields_values_dict:
                if type(fields_values_dict[key]) in [str, bool, datetime]:
                    if type(fields_values_dict[key]) is str and "'" in fields_values_dict[key]:
                        set_fields += f"{key}=$${fields_values_dict[key]}$$, "
                    else:
                        set_fields += f"{key}='{fields_values_dict[key]}', "
                else:
                    set_fields += f"{key}={fields_values_dict[key]}, "
            set_fields = set_fields[:-2]
            query = f"UPDATE {table_name} SET {set_fields} {params}"

        else:
            query = self.compose_query(vacancy_dict=fields_values_dict, table_name=table_name)
        if notification:
            print(query)
        cur = self.con.cursor()
        with self.con:
            try:
                cur.execute(query)
                if report and self.report:
                    self.report.parsing_report(profession=fields_values_dict['profession'])
                    self.report.parsing_report(has_been_added_to_db=True)
                if notification:
                    # print('Done')
                    print(f'+++++++++++++ It has been added to DB {table_name}\n')
            except Exception as ex:
                print(f"error in push_to_db_common function: {ex}")
                if report and self.report:
                    self.report.parsing_report(has_been_added_to_db=False)
                    self.report.parsing_report(error=str(ex))


    def update_job_types(self, table_list):
        for table in table_list:
            response = self.get_all_from_db(table)
            print(response)

    def rewrite_database_cities(self):
        all_vacancies = self.get_all_from_db(
            table_name=admin_database,
            field=admin_table_fields,
        )
        for vacancy in all_vacancies:
            vacancy_dict = helper.to_dict_from_admin_response(
                response=vacancy,
                fields=admin_table_fields
            )
            url = vacancy_dict['vacancy_url']

    def compose_query(self, vacancy_dict, table_name, update=False, define_id=False):
        # fields_list = []
        # values_str = ''
        # for key in vacancy_dict:
        #     if vacancy_dict[key] and key != 'id':
        #         fields_list.append(key)
        #         if type(vacancy_dict[key]) is int:
        #             values_str += f"{vacancy_dict[key]}, "
        #         else:
        #             values_str += f"'{vacancy_dict[key]}', "
        #     elif define_id:
        #         fields_list.append(key)
        #         values_str += f"{vacancy_dict[key]}, "
        # return f"""INSERT INTO {table_name} ({', '.join(fields_list)}) VALUES ({values_str[:-2]})"""
        keys_str = ''
        values_str = ''
        if not define_id and 'id' in vacancy_dict:
            vacancy_dict.pop('id')
        for key in vacancy_dict:
            if vacancy_dict[key]:
                keys_str += f"{key}, "
                if type(vacancy_dict[key]) in [str, bool, datetime]:
                    if vacancy_dict[key] == "Null":
                        values_str += f"{vacancy_dict[key]}, "
                    elif type(vacancy_dict[key]) is str and "'" in vacancy_dict[key]:
                        values_str += f"$${vacancy_dict[key]}$$, "
                    else:
                        values_str += f"'{vacancy_dict[key]}', "
                else:
                    values_str += f"{vacancy_dict[key]}, "
        keys_str = keys_str[:-2]
        values_str = values_str[:-2]
        if update:
            return f"UPDATE {table_name} SET ({keys_str}) = ({values_str}) WHERE id={vacancy_dict['id']}"
        return f"INSERT INTO {table_name} ({keys_str}) VALUES ({values_str})"
