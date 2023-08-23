import asyncio
import configparser
from datetime import date, timedelta
import json
import os
import time
from multiprocessing import Process
import time
import psycopg2
from aiogram.types import Message, Chat
from flask import Flask
import random
from db_operations.scraping_db import DataBaseOperations
from utils.additional_variables.additional_variables import admin_database, admin_table_fields, preview_fields_for_web
from helper_functions.helper_functions import to_dict_from_admin_response
from flask_cors import CORS
from flask import request
from utils.additional_variables.additional_variables import path_post_request_file, post_request_for_example, \
    valid_professions, preview_fields_for_web, vacancies_database
from patterns._export_pattern import export_pattern
from patterns.data_pattern._data_pattern import pattern
from filters.filter_jan_2023.filter_jan_2023 import VacancyFilter
from helper_functions import helper_functions as helper
from utils.additional_variables import additional_variables as variable
import requests
from invite_bot_ver2 import InviteBot, start_hardpushing
from _apps.endpoints.predictive_method import Predictive
from _apps.endpoints.client_init import ClientTelethon

db=DataBaseOperations()
vacancy_search = VacancyFilter()
config = configparser.ConfigParser()
config.read("./settings/config.ini")

database = config['DB_local_clone']['database']
user = config['DB_local_clone']['user']
password = config['DB_local_clone']['password']
host = config['DB_local_clone']['host']
port = config['DB_local_clone']['port']
localhost = config['Host']['host']

con = psycopg2.connect(
    database=database,
    user=user,
    password=password,
    host=host,
    port=port
)

admin_table = variable.admin_copy

class Endpoints:
    def __init__(self):
        self.db_request = None

    async def main_endpoints(self):
        app = Flask(__name__)
        CORS(app)

        @app.route("/get-by-id", methods=['POST'])
        async def get_by_id():
            key = 'id'
            if key in request.json and type(request.json[key]) is str:
                if request.json[key].isdigit():
                    id = int(request.json[key])
                    response = db.get_all_from_db(
                        table_name=variable.admin_database,
                        param=f"WHERE id={id}",
                        field=variable.admin_table_fields
                    )
                    if response:
                        response_dict = helper.to_dict_from_admin_response(response[0], fields=variable.admin_table_fields)

                        if response_dict:
                            return response_dict
                    else:
                        return {}
                else:
                    return {'error': 'value is not integer type'}
            else:
                return {'error': 'wrong key. please use key id'}


        @app.route("/")
        async def hello_world():
            return "It's the empty page"

        # the endpoint for get vacancies by SQL request
        @app.route("/get-vacancies-by-query", methods = ['POST'])
        async def get_vacancies_by_query():
            """
            request layout
            {'query': '<str>'}
            """
            request_data = request.json
            # all_vacancies = await db.get_all_from_db_async(
            #     table_name=variable.admin_database,
            #     param=f"{request_data['query']}",
            #     field=variable.admin_table_fields,
            #     without_sort=True
            # )
            if request_data['query'].lower().split(' ', 1)[0] != 'select':
                return {'vacancies': f"query error: 'Allowed only SELECT method'", "query": request_data, "quantity": 0}

            all_vacancies = db.run_free_request(
                request=f"{request_data['query']}",
                output_text="Done"
            )
            if type(all_vacancies) is list:
                return {'vacancies': await package_list_to_dict(all_vacancies), "query": request_data, "quantity": len(all_vacancies)}
            elif type(all_vacancies) is str:
                return {'vacancies': f"query error: {all_vacancies}", "query": request_data, "quantity": len(all_vacancies)}

        @app.route("/get-all-vacancies_trainee")
        async def get_all_vacancies_trainee():
            return await get_all_vacancies_from_db_trainee()

        @app.route("/get-all-vacancies")
        async def get_all_vacancies():
            return await get_all_vacancies_from_db()

        @app.route("/vacancy", methods = ['GET'])
        async def get_single_vacancy_for_web_vacancy():
            print("124 vacancy")
            await asyncio.sleep(0.2)
            vacancy_id = request.args.get('id')
            return await get_single_vacancies_for_web(vacancy_id)

        @app.route("/vacancies", methods = ['GET'])
        async def get_all_vacancies_for_web_vacancies():
            print('128 vacancies')
            limit = request.args.get('limit')
            start_id = request.args.get('id')
            return await get_all_vacancies_for_web(start_id=start_id, limit=limit)

        @app.route("/vacancies", methods=['POST'])
        async def vacancies_with_filters():
            data = request.json
            if 'limit' in data and data['limit']:
                limit = data['limit']
            else:
                limit = 100
            if 'id' in data and data['id']:
                id_query = f" AND id < {data['id']}"
            else:
                id_query = ''
            query = Predictive(data).get_full_query()
            responses_dict = {}
            amount_response = db.get_all_from_db(
                table_name=vacancies_database,
                param=query,
                without_sort=True,
                field='COUNT(*)'
            )
            if amount_response:
                responses_dict['amount'] = amount_response[0][0]
                param = f'{query}{id_query}'
                vacancies_response = db.get_all_from_db(
                    table_name=vacancies_database,
                    param=param,
                    order=f'ORDER BY id DESC LIMIT {limit}',
                    field=preview_fields_for_web
                )

                if vacancies_response:
                    responses_dict['vacancies'] = await package_list_to_dict(vacancies_response, preview_fields_for_web)
            return responses_dict


        @app.route("/get-all-vacancies-admin")
        async def get_all_vacancies_admin():
            response = await get_all_vacancies_from_db()
            return response

        @app.route("/get")
        async def hello_world2():
            data = await get_from_db()
            index = random.randrange(0, len(data))
            data = data[index]
            print(data)
            data_dict = {
                'vacancy': {
                    'id': data[0],
                    'title': data[2],
                    'body': data[3],
                    'profession': data[4]
                }
            }
            return json.dumps(data_dict, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

        @app.route("/post-vacancies", methods = ['POST'])
        async def post_data():
            request_data = request.json
            await write_to_file(text=request_data)
            all_vacancies = await compose_request_to_db(request_data)
            return all_vacancies

        @app.route("/get-vacancy-offset", methods = ['POST'])
        async def get_vacancy_offset():
            response_dict = {}
            request_data = request.json
            print(request_data)
            responses = db.get_all_from_db(
                table_name=variable.admin_copy,
                param=f"WHERE profession LIKE '%, {request_data['profession']}%' "
                      f"OR profession LIKE '%{request_data['profession']}, %' "
                      f"OR profession = '{request_data['profession']}' "
                      f"ORDER BY id LIMIT 1 OFFSET {request_data['offset']}",
                field=admin_table_fields,
                without_sort=True
            )
            if responses:
                response_dict = await helper.to_dict_from_admin_response(responses[0], admin_table_fields)
                print(f"get each vacancy len={len(responses)} id={response_dict['id']} offset={request_data['offset']}")
            return response_dict

    # ---------------- endpoints by trainee database (Sasha frontend) ------------------
        @app.route("/delete_vacancy_trainee/<int:id>", methods=['DELETE'])
        async def delete_vacancy(id):
            temporary_variable = True
            if temporary_variable:
                if db.delete_data(
                    table_name=admin_table,
                    param=f"WHERE id={id}"
                ):
                    return {'response': f'the vacancy id={id} has been removed to the archive'}
                else:
                    return {'response': 'vacancy has not been deleted'}
            else:
                return {'response': 'vacancy does not exist in DB'}

        @app.route("/change_vacancy_trainee/<int:id>", methods=['PATCH'])
        async def change_vacancy(id):
            request_data = request.json
            print(request_data)
            vacancy = db.get_all_from_db(
                table_name=admin_table,
                param=f"WHERE id={id}",
                field='id'
            )
            if vacancy:
                try:
                    from_db = db.update_table_multi(
                        table_name=admin_table,
                        param=f"WHERE id={id}",
                        values_dict=request_data
                    )
                    if from_db:
                        return {'response': f'id {id} vacancy has been updated'}
                    else:
                        return {'response': 'something wrong'}
                except Exception as e:
                    return {'response': str(e)}
            else:
                return {'response': 'vacancy does not exist in DB'}

        async def get_all_vacancies_from_db_trainee(param="WHERE profession <> 'no_sort'"):
            all_vacancies = {}
            all_vacancies['vacancies'] = {}
            response = db.get_all_from_db(
                table_name=admin_table,
                param=param,
                field=admin_table_fields
            )
            if type(response) is list:
                number = 0
                print(param)
                for vacancy in response:
                    vacancy_dict = await to_dict_from_admin_response(
                        response=vacancy,
                        fields=admin_table_fields
                    )
                    if number < 100:
                        all_vacancies['vacancies'][str(number)] = vacancy_dict
                    number += 1
            elif type(response) is str:
                return {'error': response}
            return all_vacancies
    # ---------------- endpoints by trainee database END (Sasha frontend) ------------------

        @app.route("/three-last-vacancies", methods=['GET'])
        async def three_last_vacancies_request():
            result_dict = await three_last_vacancies()
            return result_dict

        @app.route("/search-by-text", methods = ['POST'])
        async def search_by_text():
            print(request.json)
            query_search = Predictive(request_from_frontend=request.json)
            query = query_search.get_full_query()
            search_tables = query_search.get_search_tables()
            responses_from_db = []
            for table in search_tables:
                response = db.get_all_from_db(
                    table_name=table,
                    param=query,
                    order = "ORDER BY time_of_public DESC LIMIT 20",
                    field=admin_table_fields
                )
                if response:
                    if type(response) is not str:
                        responses_from_db.extend(response)
                    else:
                        print('BAD response: ', response)
                        print(f'QUERY is:\n{query}')
            responses_dict = await package_list_to_dict(responses_from_db)
            responses_dict = {'numbers': len(responses_dict), 'vacancies': responses_dict}
            return responses_dict

    # --------------------- admin panel --------------------------
        @app.route("/admin", methods=['GET'])
        async def admin():
            profession = request.args.get('prof')
            approve = request.args.get('approve')
            table = request.args.get('table')
            limit = request.args.get('limit')
            return await get_admin_vacancies(profession, approve, table, limit)

        async def get_admin_vacancies(profession, approve, table, limit):
            if profession == 'junior':
                pass
            error = False
            ex = ''
            if not table:
                table = variable.admin_database
            approve = True if approve and approve.lower() == 'true' else False
            approve = "approved <> 'approves by admin'" if not approve else ''

            profession = f"profession LIKE '%{profession}%'" if profession else ''

            query = "WHERE " if profession or approve else ""
            if query:
                for item in [profession, approve]:
                    if item:
                        query += f"{item} AND "
            try:
                responses = db.get_all_from_db(
                    table_name=table,
                    param=query[:-4] if query else '',
                    field=variable.admin_table_fields
                )
            except Exception as ex:
                responses = []
                error = True

            if error or type(responses) is str or not responses:
                print(ex)
                return {"error": responses if responses else str(ex)}

            responses_list = []
            for response in responses:
                responses_list.append(await helper.to_dict_from_admin_response(response, variable.admin_table_fields))

            limit = int(limit) if limit and limit.isdigit() and int(limit) < len(responses_list) else len(responses_list)
            return {'amount': len(responses_list[:limit]), 'vacancies': responses_list[:limit]}

        @app.route("/admin-approve", methods=['POST'])
        async def admin_approve():
            card = request.json
            response = db.update_table_multi(
                table_name=variable.admin_database,
                param=f"WHERE id={card['id']}",
                values_dict=card,
                null_if_empty=True
            )
            return {'response': True if response else False}

        @app.route("/admin-delete/<int:id>", methods=['DELETE'])
        async def admin_delete(id):
            transfer_response = db.transfer_vacancy(
                table_from=variable.admin_database,
                table_to=variable.archive_database,
                id=int(id)
            )
            delete_response = db.delete_data(
                table_name=variable.admin_database,
                param=f"WHERE id={int(id)}"
            )
            return {'transfer_response': True if transfer_response else False, 'delete_response': True if delete_response else False}

        @app.route("/admin-push", methods=['GET'])
        async def admin_push():
            token = request.args.get('token')
            prof = request.args.get('prof')
            prof = 'junior' if not prof else prof
            chat_id = request.args.get('chat_id')

            ct = ClientTelethon()
            client = ct.init()

            # loop = asyncio.get_event_loop()
            # loop.create_task(client.start())
            # loop.create_task(client.start())

            bot = InviteBot(token_in=token, telethon_client=client)
            await bot.run_pushing_from_admin_throw_admin_panel(chat_id=chat_id, profession=prof)

            # loop.stop()
            return {}

        @app.route("/admin-change", methods=['PUT'])
        async def admin_change():
            data = request.json
            response = db.update_table_multi(
                table_name=admin_database,
                param=f"WHERE id={data['id']}",
                values_dict=data
            )
            return {}

    # --------------------- admin panel END --------------------------

        async def get_single_vacancies_for_web(vacancy_id):
            response = []
            loop = asyncio.get_running_loop()
            pass
            try:
                response = await loop.create_task(
                    db.get_all_from_db_async2(
                        table_name=vacancies_database,
                        param=f"WHERE id={vacancy_id}",
                        field=variable.admin_table_fields
                    ), name='db_request'
                )
            except Exception as ex:
                print(ex)

            # response = db.get_all_from_db(
            #             table_name=vacancies_database,
            #             param=f"WHERE id={vacancy_id}",
            #             field=variable.admin_table_fields
            #         )
            if response:
                vacancy_dict = await to_dict_from_admin_response(
                    response=response[0],
                    fields=variable.admin_table_fields
                )
                if vacancy_dict:
                    return vacancy_dict
            else:
                return {'error': 'wrong key. please use key id'}



        async def get_from_db():
            cur = con.cursor()
            query = "SELECT * FROM admin_last_session WHERE profession <> 'no_sort'"
            with con:
                cur.execute(query)
            response = cur.fetchall()
            return response

        async def get_all_vacancies_from_db(param="WHERE profession <> 'no_sort'"):
            all_vacancies = {}
            all_vacancies['vacancies'] = {}
            response = db.get_all_from_db(
                table_name=variable.admin_database,
                param=param,
                field=admin_table_fields
            )
            if type(response) is list:
                number = 0
                print(param)
                for vacancy in response:
                    vacancy_dict = await to_dict_from_admin_response(
                        response=vacancy,
                        fields=admin_table_fields
                    )
                    if number < 100:
                        all_vacancies['vacancies'][str(number)] = vacancy_dict
                    number += 1
            elif type(response) is str:
                return {'error': response}
            return all_vacancies

        async def get_all_vacancies_for_web(limit=None, start_id=None):
            all_vacancies = {}
            all_vacancies['vacancies'] = {}
            date_start = date.today() - timedelta(days=20)
            if start_id:
                id_query = f"id < {start_id} AND "
            else:
                id_query = ''
            if not limit:
                limit = 200
            param = f"WHERE {id_query}DATE (created_at) BETWEEN '{date_start}' AND '{date.today()}'"

            response = []
            loop = asyncio.get_running_loop()
            pass
            try:
                response = await loop.create_task(
                    db.get_all_from_db_async2(
                        table_name='vacancies',
                        order=f'ORDER BY id DESC LIMIT {limit}',
                        param=param,
                        field=f'DISTINCT ON (id, body) {preview_fields_for_web}'
                    )
                )
            except Exception as ex:
                print("501 endpoint", ex)

            # response = db.get_all_from_db(
            #     table_name='vacancies',
            #     order=f'ORDER BY id DESC LIMIT {limit}',
            #     param=param,
            #     field=f'DISTINCT ON (id, body) {preview_fields_for_web}'
            # )
            if type(response) is list:
                number = 0
                for vacancy in response:
                    vacancy_dict = await to_dict_from_admin_response(
                        response=vacancy,
                        fields=preview_fields_for_web
                    )
                    all_vacancies['vacancies'][str(number)] = vacancy_dict
                    print(all_vacancies['vacancies'][str(number)]['id'])
                    number += 1
            elif type(response) is str:
                return {'error': response}

            return all_vacancies


        async def write_to_file(text):
            with open(path_post_request_file, 'a', encoding='utf-8') as file:
                file.write(f"{str(text)}\n-----------\n")

        async def get_export_pattern_dict():
            dict_pattern = {}
            for profession in export_pattern['professions']:
                dict_pattern[profession] = {}
                if 'ma' not in dict_pattern[profession]:
                    dict_pattern[profession]['ma'] = []

                dict_pattern[profession]['ma'] = list(export_pattern['professions'][profession]['ma'])
                for sub in export_pattern['professions'][profession]['sub']:
                    if 'sub' not in dict_pattern[profession]:
                        # dict_pattern[profession] = {}
                        dict_pattern[profession]['sub'] = {}

                    if sub not in dict_pattern[profession]['sub']:
                        dict_pattern[profession]['sub'][sub] = {}
                        dict_pattern[profession]['sub'][sub]['ma'] = []

                    dict_pattern[profession]['sub'][sub]['ma'] = list(export_pattern['professions'][profession]['sub'][sub]['ma'])
            return dict_pattern

        async def compose_request_to_db(response_data):
            query_profession = ""
            common_query = "WHERE ("
            if response_data['profession']:
                for item in response_data['profession']:
                    query_profession += f"OR profession LIKE '%{item}%' "
            if 'junior' in response_data['level']:
                query_profession += f"OR profession LIKE '%junior%'"
            if 'all' in response_data['level']:
                query_profession = ''
                for item in valid_professions:
                    query_profession += f"OR profession LIKE '%{item}%' "
            query_profession = f"({query_profession[3:]})"

            common_query += query_profession

            if response_data['city']:
                common_query += f" AND city LIKE '%{response_data['city']}%'"
            all_vacancies = await get_all_vacancies_from_db(param=common_query)

            return all_vacancies

        async def compose_query_loop(request_data_key, search_fields: list):
            param = ''
            if type(request_data_key) is not str:
                param += "("
                count = 0
                for element in request_data_key:
                    field_count = 0
                    for field in search_fields:
                        field += f" LIKE '%{element}%' "
                        field_count += 1
                        param += field
                        if field_count < len(search_fields):
                            param += "OR "
                        else:
                            param += ") "
                    count += 1
                    if count < len(request_data_key):
                        param += "OR ( "
                    else:
                        param += ") "
            else:
                param += ""
                field_count = 0
                for field in search_fields:
                    field += f" LIKE '%{request_data_key}%' "
                    field_count += 1
                    param += field
                    if field_count < len(search_fields):
                        param += "OR "
                    else:
                        param += ") "
            return param

        async def get_http_response(responses, common_key=None, param=None):
            """
            if you want to receive in response query, you must give 'param'
            """
            responses_dict = {}
            if not common_key:
                common_key = 'vacancies'
            responses_dict[common_key] = {}
            responses_dict['quantity'] = len(responses)
            count = 0
            for response in responses:
                responses_dict[common_key][str(count)] = await helper.to_dict_from_admin_response(response, variable.admin_table_fields)
                count += 1
            if param:
                responses_dict['query'] = param
            return responses_dict

        async def three_last_vacancies():
            trainee = 'vacancies'
            common_vacancies = 'common_vacancies'
            result_dict = {}
            result_dict[trainee] = {}

            # get 3 trainee vacancies
            responses = db.get_all_from_db(
                table_name=variable.vacancies_database,
                param="WHERE level LIKE '%trainee%' ORDER BY id DESC LIMIT 4",
                field=variable.preview_fields_for_web,
                without_sort=True
            )
            result_dict[trainee] = await package_list_to_dict(responses_list=responses, fields_list=preview_fields_for_web)

            # get 3 common vacancies
            responses = db.get_all_from_db(
                table_name=variable.vacancies_database,
                param="WHERE level NOT LIKE '%trainee%' ORDER BY id DESC LIMIT 4",
                field=variable.preview_fields_for_web,
                without_sort=True
            )
            result_dict[common_vacancies] = await package_list_to_dict(responses_list=responses, fields_list=preview_fields_for_web)

            return result_dict

        async def package_list_to_dict(responses_list, fields_list=variable.admin_table_fields):
            result_dict = {}
            if responses_list and type(responses_list) is not str:
                count = 0
                for response in responses_list:
                    result_dict[str(count)] = helper.to_dict_from_admin_response_sync(response, fields_list)
                    count += 1
            return result_dict

        app.run(host=localhost, port=int(os.environ.get('PORT', 5000)))

        # @app.route("/vacancy", methods=['GET'])
        # async def get_single_vacancy_for_web():
        #     vacancy_id = request.args.get('id')
        #     return await get_single_vacancies_for_web(vacancy_id)


def run_endpoints():
    endpoints = Endpoints()
    asyncio.run(endpoints.main_endpoints())
    # asyncio.run(main_endpoints())


