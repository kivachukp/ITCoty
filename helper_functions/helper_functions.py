import os
import re
import time
from datetime import datetime
from filters.filter_jan_2023.filter_jan_2023 import VacancyFilter
from patterns._export_pattern import export_pattern
from patterns.pseudo_pattern.pseudo_export_pattern import export_pattern as pseudo_export_pattern
from utils.additional_variables.additional_variables import flood_control_logs_path, admin_table_fields, \
    pictures_separators_path, valid_professions, admin_database, archive_database


def compose_to_str_from_list(data_list):
    sub_str = ''
    for key in data_list:
        if type(data_list[key]) is list:
            sub_str += f"{key}: {', '.join(data_list[key])}; "
        elif type(data_list[key]) is str:
            sub_str += f"{key}: {data_list[key]}; "
    sub_str = sub_str[:-2]
    pass
    return sub_str

def decompose_from_str_to_list(data_str):
    if data_str:
        data_dict = {}
        data_list = data_str.split('; ')
        for i in data_list:
            i = i.split(': ')
            key = i[0]
            sub_items = i[1]
            if sub_items:
                data_dict[key] = sub_items.split(', ')
            else:
                data_dict[key] = []
        return data_dict
    else:
        return {}

def compose_simple_list_to_str(data_list, separator):
    return f'{separator}'.join(data_list)

def string_to_list(text, separator):
    return text.split(separator)

def list_to_string(raw_list, separator):
    return separator.join(raw_list)

async def to_dict_from_admin_response(response, fields):
    response_dict = {}
    fields = fields.split(', ')
    try:
        for i in range(0, len(fields)):
            response_dict[fields[i]] = response[i]
    except Exception as ex:
        print(f"error in to_dict_from_admin_response: {ex}")
        return False
    return response_dict

def to_dict_from_admin_response_sync(response, fields):
    response_dict = {}
    fields = fields.split(', ')
    try:
        for i in range(0, len(fields)):
            response_dict[fields[i]] = response[i]
    except Exception as ex:
        print(f"error in to_dict_from_admin_response_sync: {ex}")
        return False
    return response_dict

async def to_dict_from_temporary_response(response, fields):
    response_dict = {}
    fields = fields.split(', ')
    for i in range(0, len(fields)):
        response_dict[fields[i]] = response[i]
    return response_dict

async def get_pattern(path, pseudo=False):
    print('\n\n---------------------------------------\n\n')
    message = ''
    if pseudo:
        pattern = pseudo_export_pattern
    else:
        pattern = export_pattern
    for key in pattern:
        message += f"{key}:\n"

        if type(pattern[key]) is dict:
            for key2 in pattern[key]:
                message += f"\t{key2}:\n"

                if type(pattern[key][key2]) is dict:
                    for key3 in pattern[key][key2]:
                        message += f"\t\t{key3}:\n"

                        if type(pattern[key][key2][key3]) is dict and pattern[key][key2][key3]:
                            for key4 in pattern[key][key2][key3]:
                                message += f"\t\t\t{key4}:\n"

                                if type(pattern[key][key2][key3][key4]) is dict:
                                    for key5 in pattern[key][key2][key3][key4]:
                                        message += f"\t\t\t\t{key5}:\n"

                                        if type(pattern[key][key2][key3][key4][key5]) is dict:
                                            for key6 in pattern[key][key2][key3][key4][key5]:
                                                message += f"\t\t\t\t\t{key6}:\n"
                                        else:
                                            message += f"\t\t\t\t\t\t{pattern[key][key2][key3][key4][key5]}\n"
                                else:
                                    message += f"\t\t\t\t\t{pattern[key][key2][key3][key4]}\n"
                        else:
                            message += f"\t\t\t{pattern[key][key2][key3]}\n"
                else:
                    message += f"\t\t{pattern[key][key2]}\n"
        else:
            message += f"\t{pattern[key]}\n"

    print(message)
    with open(path, "w", encoding='utf-8') as file:
        file.write(message)
        print('Done')

async def transformTitleBodyBeforeDb(text=None, title=None, body=None):
    if text:
        title = text.partition(f'\n')[0]
        body = text.replace(title, '').replace(f'\n\n', f'\n')
    elif title+body:
        if title:
            title = title
        if body:
            body = body.replace(f'\n\n', f'\n')
    return {'title': title, 'body': body}

def get_additional_values_fields(dict_in):


    results_dict = {}
    hybrid_shorts = {}
    for key in dict_in:
        results_dict[key] = dict_in[key]

    params = VacancyFilter().sort_profession(
        title=results_dict['title'],
        body=results_dict['body'],
        check_contacts=False,
        check_level=False,
        check_vacancy=False,
        check_profession=False,
        get_params=True
    )['params']

    # english
    english = get_field_for_shorts_sync(
        presearch_results=[results_dict['english'], results_dict['title'], results_dict['body']],
        pattern=export_pattern['others']['english_for_shorts']['ma'],
        return_value='english'
    )

    if english['match']:
        results_dict['english'] = english['match']
    elif english['element_is_not_empty']:
        results_dict['english'] = 'B1+'
    else:
        results_dict['english'] = ''

    # #job_type
    # job_type_shorts = ''
    # remote_shorts = get_field_for_shorts_sync(
    #     presearch_results=[
    #         results_dict['job_type'],
    #         results_dict['title'] + results_dict['body'],
    #     ],
    #     pattern=export_pattern['others']['remote']['ma'],
    #     return_value='remote',
    # )
    # remote_shorts = remote_shorts['return_value']
    # if remote_shorts:
    #     job_type_shorts += remote_shorts
    #
    # full_time_shorts = get_field_for_shorts_sync(
    #     presearch_results=[
    #         results_dict['job_type'],
    #         results_dict['title'] + results_dict['body'],
    #     ],
    #     pattern=export_pattern['others']['full_time']['ma'],
    #     return_value='fulltime',
    # )
    # full_time_shorts = full_time_shorts['return_value']
    # if full_time_shorts:
    #     if len(job_type_shorts) > 0:
    #         job_type_shorts += ", "
    #     job_type_shorts += full_time_shorts
    #
    # office_shorts = get_field_for_shorts_sync(
    #     presearch_results=[
    #         results_dict['job_type'], results_dict['body'],
    #     ],
    #     pattern=export_pattern['others']['office']['ma'],
    #     return_value='office',
    # )
    # office_shorts = office_shorts['return_value']
    #
    # if office_shorts:
    #     if len(job_type_shorts) > 0:
    #         job_type_shorts += ", "
    #     job_type_shorts += office_shorts
    #
    # flexible_shorts = get_field_for_shorts_sync(
    #     presearch_results=[
    #         results_dict['job_type'], results_dict['body'],
    #     ],
    #     pattern=export_pattern['others']['flexible']['ma'],
    #     return_value='flexible',
    # )
    # flexible_shorts = flexible_shorts['return_value']
    #
    # if flexible_shorts:
    #     if len(job_type_shorts) > 0:
    #         job_type_shorts += ", "
    #     job_type_shorts += flexible_shorts
    #
    # # hybrid_shorts = get_field_for_shorts_sync(
    # #     presearch_results=[
    # #         results_dict['job_type'], results_dict['body'],
    # #     ],
    # #     pattern=export_pattern['others']['hybrid']['ma'],
    # #     return_value='office/remote',
    # # )
    # if hybrid_shorts:
    #     hybrid_shorts = hybrid_shorts['return_value']
    #
    #
    # if hybrid_shorts:
    #     if len(job_type_shorts) > 0:
    #         job_type_shorts += ", "
    #     job_type_shorts += hybrid_shorts

    # if job_type_shorts:
    #     results_dict['job_type'] = job_type_shorts

    #relocation
    relocate_shorts = get_field_for_shorts_sync(
        presearch_results=[
            results_dict['job_type'],
            results_dict['relocation'],
            results_dict['title'] + results_dict['body'],
            params['relocation']
        ],
        pattern=export_pattern['others']['relocate']['ma'],
        return_value='relocate'
    )
    relocate_shorts = relocate_shorts['return_value']
    if relocate_shorts:
        results_dict['relocation'] = relocate_shorts

    experience_shorts = get_field_for_shorts_sync(
        presearch_results=[
            results_dict['experience'],
            results_dict['job_type']
        ],
        pattern=export_pattern['others']['experience']['ma'],
        return_value='experience'
    )
    if experience_shorts['match']:
        experience_shorts = experience_shorts['match']
        experience_shorts = re.findall(r'[0-9]{1,2}', experience_shorts)
        if experience_shorts:
            experience_shorts = experience_shorts[0]
    else:
        experience_shorts = ''
    if experience_shorts:
        results_dict['experience'] = experience_shorts

    # salary_shorts = get_field_for_shorts_sync(
    #     presearch_results=[
    #         results_dict['salary'],
    #         results_dict['title'] + results_dict['body']
    #     ],
    #     pattern=export_pattern['others']['salary_for_shorts']['ma'],
    #     return_value='salary'
    # )
    # salary_shorts = salary_shorts['match']
    # salary_shorts = salary_shorts.replace('до', '-').replace('  ', ' ')
    # if salary_shorts:
    #     results_dict['salary'] = salary_shorts
    # # print('salary = ', salary_shorts)

    city_shorts = get_city_vacancy_for_shorts_sync(
        presearch_results=[
            results_dict['city'],
            results_dict['job_type'],
            results_dict['title'] + results_dict['body'],
        ],
        pattern=export_pattern['others']['city_for_shorts']['ma'],
        return_value='match'
    )
    if city_shorts['return_value']:
        city_shorts = city_shorts['return_value']
    elif city_shorts['element_is_not_empty']:
        if results_dict['city']:
            city_shorts = results_dict['city']
        else:
            city_shorts = ''
    else:
        city_shorts = ''
    if city_shorts:
        results_dict['city'] = city_shorts

    return results_dict

def update_job_types(dict):
    # function for one-time update, can be deleted later

    job_type_new = ''
    remote = get_field_for_shorts_sync(
        presearch_results=[
            dict['job_type'],
            dict['title'] + dict['body'],
        ],
        pattern=export_pattern['others']['remote']['ma'],
        return_value='remote',
    )
    remote = remote['return_value']
    if remote:
        job_type_new += remote

    full_time = get_field_for_shorts_sync(
        presearch_results=[
            dict['job_type'],
            dict['title'] + dict['body'],
        ],
        pattern=export_pattern['others']['full_time']['ma'],
        return_value='fulltime',
    )
    full_time = full_time['return_value']
    if full_time:
        if len(job_type_new) > 0:
            job_type_new += ", "
        job_type_new += full_time

    office = get_field_for_shorts_sync(
        presearch_results=[
            dict['job_type'], dict['body'],
        ],
        pattern=export_pattern['others']['office']['ma'],
        return_value='office',
    )
    office = office['return_value']

    if office:
        if len(job_type_new) > 0:
            job_type_new += ", "
        job_type_new += office

    flexible = get_field_for_shorts_sync(
        presearch_results=[
            dict['job_type'], dict['body'],
        ],
        pattern=export_pattern['others']['flexible']['ma'],
        return_value='flexible',
    )
    flexible = flexible['return_value']

    if flexible:
        if len(job_type_new) > 0:
            job_type_new += ", "
        job_type_new += flexible

    hybrid = get_field_for_shorts_sync(
        presearch_results=[
            dict['job_type'], dict['body'],
        ],
        pattern=export_pattern['others']['office/remote']['ma'],
        return_value='office/remote',
    )
    hybrid = hybrid['return_value']

    if hybrid:
        if len(job_type_new) > 0:
            job_type_new += ", "
        job_type_new += hybrid
    if job_type_new == '':
        job_type_new = 'office'

    return job_type_new

async def get_field_for_shorts(presearch_results: list, pattern: str, return_value='match'):
    element_is_not_empty = False
    for element in presearch_results:
        if element:
            element_is_not_empty = True
            for pattern_item in pattern:
                match = re.findall(rf"{pattern_item}", element)
                if match:
                    return {'return_value': return_value, 'element_is_not_empty': element_is_not_empty, 'match': match[0]}
    return {'return_value': '', 'element_is_not_empty': element_is_not_empty, 'match': ''}

def get_field_for_shorts_sync(presearch_results: list, pattern: str, return_value='match'):
    element_is_not_empty = False
    for element in presearch_results:
        if element:
            element_is_not_empty = True
            for pattern_item in pattern:
                match = re.findall(rf"{pattern_item}", element)
                if match:
                    return {'return_value': return_value, 'element_is_not_empty': element_is_not_empty, 'match': match[0]}
    return {'return_value': '', 'element_is_not_empty': element_is_not_empty, 'match': ''}

async def get_city_vacancy_for_shorts(presearch_results: list, pattern: str, return_value='match'):
    key = ''
    element_is_not_empty = False
    for element in presearch_results:
        if element:
            element_is_not_empty = True
            for key in pattern:
                if type(pattern[key]) is not str:
                    for value in pattern[key]:
                        match = re.findall(rf"{value}", element)
                        if match:
                            return {'return_value': f"{key}, {value}", 'element_is_not_empty': element_is_not_empty, 'match': match[0]}
                else:
                    match = re.findall(rf"{pattern[key]}", element)
                    if match:
                        return {'return_value': f"{key}, {key}", 'element_is_not_empty': element_is_not_empty,
                                'match': match[0]}
    return {'return_value': "", 'element_is_not_empty': "", 'match': ""}

def get_city_vacancy_for_shorts_sync(presearch_results: list, pattern: str, return_value='match'):
    element_is_not_empty = False
    for element in presearch_results:
        if element:
            element_is_not_empty = True
            for key in pattern:
                if type(pattern[key]) is not str:
                    for value in pattern[key]:
                        match = re.findall(rf"{value}", element)
                        if match:
                            return {'return_value': f"{key}, {value}", 'element_is_not_empty': element_is_not_empty,
                                    'match': match[0]}
                else:
                    match = re.findall(rf"{pattern[key]}", element)
                    if match:
                        return {'return_value': f"{key}, {key}", 'element_is_not_empty': element_is_not_empty,
                                'match': match[0]}


    return {'return_value': '', 'element_is_not_empty': element_is_not_empty, 'match': ''}

async def send_message(bot, chat_id, text, **kwargs):
    parse_mode = 'html' if 'parse_mode' not in kwargs else kwargs['parse_mode']
    disable_web_page_preview = True if 'disable_web_page_preview' not in kwargs else kwargs['disable_web_page_preview']
    msg = None
    ex = "Flood control"
    while ex.lower() == 'flood control':
        try:
            msg = await bot.send_message(chat_id, text, parse_mode=parse_mode, disable_web_page_preview=disable_web_page_preview)
            ex = ''
        except Exception as e:
            ex = e.args[0]

            with open(flood_control_logs_path, "a") as file:
                file.write(f"{datetime.now().strftime('%d-%m-%y %H:%M%S')} Exception {ex}")

            if 'flood control' in ex.lower():
                print("\n--------------\nFlood control\n--------------\n")
                match = re.findall(r"[0-9]{1,4} seconds", ex)
                if match:
                    seconds = match[0].split(' ')[0]
                    time.sleep(int(seconds) + 5)
    return msg

async def edit_message(bot, text, msg, **kwargs):
    parse_mode = 'html' if 'parse_mode' not in kwargs else kwargs['parse_mode']
    disable_web_page_preview = True if 'disable_web_page_preview' not in kwargs else kwargs['disable_web_page_preview']
    ex = "Flood control"
    while ex.lower() == 'flood control':
        try:
            msg = await bot.edit_message_text(f"{msg.text}{text}", msg.chat.id, msg.message_id, parse_mode=parse_mode, disable_web_page_preview=disable_web_page_preview)
            ex = ''
        except Exception as e:
            ex = e.args[0]

            with open(flood_control_logs_path, "a") as file:
                file.write(f"{datetime.now().strftime('%d-%m-%y %H:%M%S')} Exception {ex}")

            if 'flood control' in ex.lower():
                print("\n--------------\nFlood control\n--------------\n")
                match = re.findall(r"[0-9]{1,4} seconds", ex)
                if match:
                    seconds = match[0].split(' ')[0]
                    time.sleep(int(seconds) + 5)
    return msg

def get_tags(profession):

    tag_list = profession['tag'].split('\n')
    anti_tag_list = profession['anti_tag'].split('\n')
    tags = ''
    tags_set = set()
    for tag in tag_list:
        if tag:
            if 'vacancy' not in tag and 'contacts' not in tag:
                tag_value = tag.split("'")[-2]
                tag_word = tag.split("=")[0][3:]
                if anti_tag_list:
                    for anti_tag in anti_tag_list:
                        if anti_tag:
                            anti_tag_word = anti_tag.split("=")[0][4:]
                            if anti_tag_word != tag_word:
                                tags_set.add(tag_value)
                        else:
                            tags_set.add(tag_value)
    return ", ".join(tags_set)

async def get_short_session_name(prefix):
    return f"{prefix.strip()}: {datetime.now().strftime('%Y%m%d%H%M%S')}"

def decompose_from_str_to_subs_list(data_str):
    data_list=data_str.split(': ')
    profession=data_list[0]
    i=data_list[1].strip()
    if i=='':
        i='unsorted'
    i=i.split(', ')
    subs_list=[f'{profession}_{j}' for j in i]
    return subs_list

def add_to_report_file(path, write_mode, text):
    with open(path, write_mode, encoding='utf-8') as file:
        file.write(text)

async def remove_one_profession(professions: str, remove_profession: str):
    prof_list = professions.split(', ')
    try:
        prof_list.remove(remove_profession)
    except Exception as e:
        print(e)
    professions = ", ".join(prof_list)
    return professions

async def cut_message_for_parts(text, separator):
    one_text_part = ''
    result_list = []
    if not separator:
        separator = ' '
    if len(text)> 4096:
        text_list = text.split(separator)
        for text_part in text_list:
            if len(f"{one_text_part}{text_part}{separator}") < 4096:
                one_text_part += f'{text_part}{separator}'
            else:
                result_list.append(one_text_part)
                one_text_part = text_part
        result_list.append(one_text_part)
    else:
        return [text]
    return result_list

async def get_picture_path(sub, profession):
    files = os.listdir(pictures_separators_path)
    if f"{sub}.jpg" in files:
        return f"{pictures_separators_path}/{sub}.jpg"
    elif f"{profession}.jpg" in files:
        return f"{pictures_separators_path}/{profession}.jpg"
    else:
        return f"{pictures_separators_path}/common.jpg"

async def send_file_to_user(
        bot, chat_id, path, caption='Please take it',
        client=None, send_to_developer=False, developer_chat_id=None
):
        try:
            with open(path, 'rb') as file:
                try:
                    await bot.send_document(chat_id, file, caption=caption)
                    if send_to_developer and chat_id != developer_chat_id:
                        try:
                            await bot.send_document(int(developer_chat_id), file, caption=caption)
                        except Exception as e:
                            print(e)
                except Exception as ex:
                    if client:
                        await client.send_file(chat_id, file, caption=caption)
                    print(ex)
        except Exception as exc:
            print(f"can't to send file: {exc}")

async def refill_salary_usd(db_class):
    table_list = valid_professions.copy()
    table_list.extend([admin_database, archive_database])
    for table in table_list:
        vacancies = []
        try:
            vacancies = db_class.get_all_from_db(
                table_name=table,
                without_sort=True,
                field=admin_table_fields
            )
        except Exception as ex:
            print(f'error in getting from database from table: {table}: \n{ex}')
        if vacancies:
            for one_vacancy in vacancies:
                if type(one_vacancy) is str:
                    pass
                vacancy_dict = await to_dict_from_admin_response(one_vacancy, admin_table_fields)
                vacancy_dict_new = await get_salary_usd_month(vacancy_dict=vacancy_dict, table=table, db_class=db_class)
                if db_class and vacancy_dict_new['rate']:
                    db_class.update_table_multi(
                        table_name=table,
                        param=f"Where id={vacancy_dict['id']}",
                        values_dict={
                            'salary_from_usd_month': vacancy_dict['salary_from_usd_month'],
                            'salary_to_usd_month': vacancy_dict['salary_to_usd_month'],
                            'rate': vacancy_dict['rate']
                        }
                    )
                    print('GOT!', vacancy_dict['salary_currency'])

async def get_salary_usd_month(vacancy_dict, **kwargs):
    table = kwargs['table'] if 'table' in kwargs else None
    # db_class = kwargs['db_class'] if 'db_class' in kwargs else None
    # update_data = kwargs['update_data'] if 'update_data' in kwargs else False
    salary_to_usd_month = None

    currencies_nbrb = {
        "EUR": 2.75,
        "USD": 2.89,
        "KZT": 0.0056,
        "RuR": 0.032,
        "ByR": 1
    }

    if 'salary_currency' in vacancy_dict and vacancy_dict['salary_currency']:
        if vacancy_dict['salary_currency'].lower() == 'rur':
            pass
        if vacancy_dict['salary_currency'].lower() == 'rur' and vacancy_dict['salary_period'] != "Per Hour":
            if vacancy_dict['salary_from'] and vacancy_dict['salary_from'] < 1000:
                vacancy_dict['salary_from'] = vacancy_dict['salary_from'] * 1000
            if vacancy_dict['salary_to'] and vacancy_dict['salary_to'] < 1000:
                vacancy_dict['salary_to'] = vacancy_dict['salary_to'] * 1000

        if vacancy_dict['salary_currency'] in currencies_nbrb:
            currency = vacancy_dict['salary_currency']
            rate = currencies_nbrb[currency]
            if vacancy_dict['salary_from']:

                if 'rate' not in vacancy_dict or rate != vacancy_dict['rate']:
                    if 'rate' not in vacancy_dict:
                        vacancy_dict['rate'] = rate
                        vacancy_dict['salary_from_usd_month'] = None
                        vacancy_dict['salary_to_usd_month'] = None

                    salary_from_usd_month = vacancy_dict['salary_from']*rate/currencies_nbrb['USD'] #if rate>1 else vacancy_dict['salary_from']*rate/currencies_nbrb['USD']
                    if vacancy_dict['salary_to']:
                        salary_to_usd_month = vacancy_dict['salary_to']*rate/currencies_nbrb['USD'] #if rate>1 else vacancy_dict['salary_to']*rate/currencies_nbrb['USD']
                    if vacancy_dict['salary_period'].lower() == 'per year':
                        vacancy_dict['salary_from_usd_month'] = round(salary_from_usd_month/12) if salary_from_usd_month else None
                        vacancy_dict['salary_to_usd_month'] = round(salary_to_usd_month/12) if salary_to_usd_month else None
                    elif vacancy_dict['salary_period'].lower() == "per hour":
                        vacancy_dict['salary_from_usd_month'] = round(salary_from_usd_month*8*22) if salary_from_usd_month else None
                        vacancy_dict['salary_to_usd_month'] = round(salary_to_usd_month*8*22) if salary_to_usd_month else None
                    else:
                        vacancy_dict['salary_from_usd_month'] = round(salary_from_usd_month) if salary_from_usd_month else None
                        vacancy_dict['salary_to_usd_month'] = round(salary_to_usd_month) if salary_to_usd_month else None

                    # if not update_data:
                    return vacancy_dict

                    # if db_class and table:
                    #     db_class.update_table_multi(
                    #         table_name=table,
                    #         param=f"Where id={vacancy_dict['id']}",
                    #         values_dict={
                    #             'salary_from_usd_month': round(salary_from_usd_month) if salary_from_usd_month else None,
                    #             'salary_to_usd_month': round(salary_to_usd_month) if salary_to_usd_month else None,
                    #             'rate': rate
                    #         }
                    #     )
                    #     print('GOT!', vacancy_dict['salary_currency'])
                else:
                    print('data is valid')
                    # if not update_data:
                    return vacancy_dict

        else:
            with open('./excel/errors_in_salary_currency.txt', 'a') as file:
                file.write(f"vacancy_dict['salary_currency']: {vacancy_dict['salary_currency']}\n"
                           f"link: {vacancy_dict['vacancy_url']}\n"
                           f"table: {table if table else None}\n"
                           f"id: {vacancy_dict['id']}\n"
                           f"-------\n\n")
            print('currency not in currencies_nbrb: ', vacancy_dict['salary_currency'])
            # if not update_data:
            return vacancy_dict
    else:
        print('*' * 6)
        # if not update_data:
        return vacancy_dict

async def transform_salary(results_dict):
    salary_format = ''
    if results_dict['salary_from']:
        salary_format += f"from {results_dict['salary_from']}"
    if results_dict['salary_to']:
        salary_format += f" to {results_dict['salary_to']}"
    if results_dict['salary_currency']:
        salary_format += f" {results_dict['salary_currency']}"
    if results_dict['salary_period']:
        salary_format += f" {results_dict['salary_period'].lower()}"
    return salary_format

async def replace_NoneType(results_dict):
    for key in results_dict:
        if results_dict[key] == None:
            results_dict[key] = ''
    return results_dict


