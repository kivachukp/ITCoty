import asyncio
import time
import pandas as pd
import os
import random
import re
import urllib
from datetime import datetime, timedelta
import pandas
import requests
from aiogram import Bot, Dispatcher, types
import logging
import configparser
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, Message, Chat
from aiogram.utils import executor
from aiogram.utils.executor import start_polling
from asgiref.sync import sync_to_async, async_to_sync
from telethon.sync import TelegramClient
from telethon.tl import functions
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputUser, InputChannel, ChannelParticipantsSearch, PeerChannel
from db_operations.scraping_db import DataBaseOperations
from helper_functions.cities_and_countries.cities_parser import CitiesAndCountries
from sites.scraping_hhkz import HHKzGetInformation
from sites.scraping_praca import PracaGetInformation
from telegram_chats.scraping_telegramchats2 import WriteToDbMessages, main
from sites.parsing_sites_runner import SitesParser, parser_sites
from logs.logs import Logs
from sites.scraping_dev import DevGetInformation
from sites.scraping_geekjob import GeekGetInformation
from sites.scraping_hh import HHGetInformation
from helper_functions.progress import ShowProgress
from sites.scraping_superjob import SuperJobGetInformation
from sites.scraping_svyazi import SvyaziGetInformation
from sites.scrapping_finder import FinderGetInformation
from sites.scraping_habr import HabrGetInformation
from sites.scraping_rabota import RabotaGetInformation
from sites.scraping_ingamejob import IngameJobGetInformation
from filters.filter_jan_2023.filter_jan_2023 import VacancyFilter
from helper_functions import helper_functions as helper
from utils.additional_variables import additional_variables as variable
from patterns._export_pattern import export_pattern
from patterns.data_pattern._data_pattern import pattern as data_pattern
from multiprocessing import Process
from sites.send_log_txt import send_log_txt
from report.reports import Reports
from report.report_variables import report_file_path
from helper_functions.database_update_data.database_update_data import DatabaseUpdateData

logs = Logs()
import settings.os_getenv as settings
config = configparser.ConfigParser()
config.read("./settings/config.ini")

api_id = settings.api_id
api_hash = settings.api_hash
username = settings.username

api_id_double = settings.api_id_double
api_hash_double = settings.api_hash_double
username_double = settings.username_double

all_participant = []
file_name = ''
marker_code = False
password = 0
con = None

print(f'Bot started at {datetime.now()}')
logs.write_log(f'\n------------------ restart --------------------')




class InviteBot():

    def __init__(self, token_in=None, double=False, telethon_username=None):
        username = telethon_username if telethon_username else settings.username
        self.chat_id = None
        self.start_time_listen_channels = datetime.now()
        self.start_time_scraping_channels = None
        self.valid_profession_list = variable.valid_professions
        self.markup = None
        self.api_id = api_id
        self.api_hash = api_hash
        self.current_session = ''
        self.current_customer = None
        self.api_id: int
        self.api_hash: str
        self.phone_number = '' # str
        self.hash_phone = '' # str
        self.code = '' # str
        self.password = '' #str
        self.peerchannel = False
        self.percent = None
        self.message = None
        self.last_id_message_agregator = None
        self.message_for_send = ''
        self.feature = ''
        self.quantity_in_statistics = 0
        self.quantity_entered_to_admin_channel = 0
        self.out_from_admin_channel = 0
        self.quantity_entered_to_shorts = 0
        self.participants_dict = {}
        self.white_admin_list = variable.white_admin_list
        self.marker = False
        self.all_participant = []
        self.channel = None
        self.admin_check_file = variable.admin_check_file_path
        self.message_for_send_dict = {}
        self.schedule_pushing_shorts = True
        self.task = None
        self.parser_at_work = False
        self.shorts_at_work = False
        self.show_vacancies = {
            'table': '',
            'offset': 0,
            'message': '',
            'profession': ''
        }
        if double:
            self.client = TelegramClient(username_double, int(api_id_double), api_hash_double)
        else:
            self.client = TelegramClient(username, int(api_id), api_hash)
        try:
            self.client.start()
        except Exception as e:
            print(e)
            self.client.connect()
        self.report = Reports(show_in_console=False)
        self.db = DataBaseOperations(report=self.report)
        self.tg_parser = WriteToDbMessages(report=self.report)
        self.temporary_data = {}
        logging.basicConfig(level=logging.DEBUG, filename="py_log.log",filemode="w")

        if token_in:
            self.token = token_in
        else:
            self.token = settings.token
        self.bot_aiogram = Bot(token=self.token)
        storage = MemoryStorage()
        self.dp = Dispatcher(self.bot_aiogram, storage=storage)
        try:
            self.db.push_to_db_common(
                table_name="shorts_at_work",
                fields_values_dict={"shorts_at_work": False},
                params="WHERE id=1"
                )
            print('Set value False for shorts_at_work')
        except Exception as e:
            print(e)
        try:
            self.db.push_to_db_common(
                table_name='parser_at_work',
                fields_values_dict={"parser_at_work": False},
                params = "WHERE id=1"
            )
            print('Set value False for parser_at_work')
        except Exception as e:
            print(e)


    def main_invitebot(self):

        async def connect_with_client(message, id_user):

            e=None
            self.client = TelegramClient(str(id_user), int(self.api_id), self.api_hash)

            await self.client.connect()
            print('Client_is_on_connection')

            if not await self.client.is_user_authorized():
                try:
                    print('But it is not authorized')
                    phone_code_hash = await self.client.send_code_request(str(self.phone_number))
                    self.hash_phone = phone_code_hash.phone_code_hash

                except Exception as e:
                    await self.bot_aiogram.send_message(message.chat.id, str(e))

                if not e:
                    await get_code(message)
            else:
                await self.bot_aiogram.send_message(message.chat.id, 'Connection is ok')

        class Form_participants(StatesGroup):
            channel = State()

        class Form_params(StatesGroup):
            vacancy = State()

        class Form_delete(StatesGroup):
            date = State()

        class Form_hhkz(StatesGroup):
            word = State()

        class Form(StatesGroup):
            api_id = State()
            api_hash = State()
            phone_number = State()
            code = State()
            password = State()

        class Form_hh(StatesGroup):
            word = State()

        class Form_geek(StatesGroup):
            word = State()

        class Form_emergency_push(StatesGroup):
            profession = State()

        class Form_check(StatesGroup):
            title = State()
            body = State()
            vacancy = State()

        class Form_check_link(StatesGroup):
            link = State()

        class Form_user(StatesGroup):
            user_data = State()

        class Form_clean(StatesGroup):
            profession = State()
            quantity_leave = State()

        class Form_pattern(StatesGroup):
            profession = State()
            sub = State()
            sub_profession = State()
            sub_sub = State()

        class Form_db(StatesGroup):
            name = State()

        class Form_check_url(StatesGroup):
            url = State()

        class Form_check_url_to_add(StatesGroup):
            url = State()

        class Form_vacancy_names(StatesGroup):
            profession = State()

        class Form_rollback(StatesGroup):
            short_session_name = State()

        class Form_vacancy_name(StatesGroup):
            profession = State()

        class Form_report(StatesGroup):
            date_in = State()
            date_out = State()

        class Form_report_total(StatesGroup):
            date_in = State()
            date_out = State()

        class Form_add_field(StatesGroup):
            field = State()

        class Form_profession_name(StatesGroup):
            profession = State()

        class Form_pick_up_forcibly_from_admin(StatesGroup):
            profession = State()

        @self.dp.message_handler(commands=['start'])
        async def send_welcome(message: types.Message):

            self.chat_id = message.chat.id
            print("user_id: ", message.from_user.id)
            self.user_id = message.from_user.id

            logs.write_log(f'\n------------------ start --------------------')
            # -------- make a parse keyboard for admin ---------------
            parsing_kb = ReplyKeyboardMarkup(resize_keyboard=True)
            # parsing_button1 = KeyboardButton('Get news from channels')
            parsing_button2 = KeyboardButton('Subscr.statistics')
            parsing_button3 = KeyboardButton('Digest')
            # parsing_button4 = KeyboardButton('Invite people')
            # parsing_button5 = KeyboardButton('Get participants')

            parsing_kb.row(parsing_button3, parsing_button2)

            await self.bot_aiogram.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!', reply_markup=parsing_kb)
            await self.bot_aiogram.send_message(variable.id_owner, f'User {message.from_user.id} has started')
            config2 = configparser.ConfigParser()
            config2.read("./settings/config_keys.ini")
            if self.token == config2['Token']['token_red']:
                await get_news(message=message)
                pass

        @self.dp.message_handler(commands=['help'])
        async def get_logs(message: types.Message):
            if len(variable.help_text) >4096:
                separator = "\n\n"
                text_list = await helper.cut_message_for_parts(text=variable.help_text, separator=separator)
            else:
                text_list = [variable.help_text]
            for text in text_list:
                await self.bot_aiogram.send_message(message.chat.id, text)

        @self.dp.message_handler(commands=['update_city_field'])
        async def update_city_field(message: types.Message):
            updater = DatabaseUpdateData()
            await updater.update_city_field()

        @self.dp.message_handler(commands=['update_salary_field'])
        async def update_city_field(message: types.Message):
            updater = DatabaseUpdateData()
            await updater.update_salary_fields()

        @self.dp.message_handler(commands=['get_admin_vacancies_table'])
        async def get_admin_vacancies_table(message: types.Message):
            table_list = self.valid_profession_list.copy()
            table_list.append(variable.admin_database)
            table_list.append(variable.archive_database)
            table_list = [variable.admin_database]
            for table in table_list:
                result_dict = {}
                responses = self.db.get_all_from_db(
                    table_name=table,
                    field=variable.admin_table_fields
                )
                for response in responses:
                    response_dict = await helper.to_dict_from_admin_response(response, variable.admin_table_fields)
                    for key in response_dict:
                        if key not in result_dict:
                            result_dict[key] = []
                        result_dict[key].append(response_dict[key])
                try:
                    df = pd.DataFrame(result_dict)
                    path = f'./excel/excel/{table}_vacancies.xlsx'
                    df.to_excel(path, sheet_name='Sheet1')
                    print('got it')
                    await self.send_file_to_user(message, path)

                except Exception as e:
                    print(e)

        @self.dp.message_handler(commands=['cities_and_countries'])
        async def get_log_file(message: types.Message):
            """
            the function receive all countries and cities to dictionary and write  to database
            in table countries_and_cities like city and country
            """
            cities_and_countries = CitiesAndCountries()
            await cities_and_countries.get_all_countries_and_cities()

        @self.dp.message_handler(commands=['get_log_file'])
        async def get_log_file(message: types.Message):
            try:
                await helper.send_file_to_user(
                    bot=self.bot_aiogram,
                    chat_id=message.chat.id,
                    path="./py_log.log",
                    caption="take the logs"
                )
            except Exception as ex:
                print(f'error for sending logs: {ex}')

        @self.dp.message_handler(commands=['hard_push_by_web'])
        async def hard_push_by_web_command(message: types.Message):
            for i in ["http://localhost:5000/hard-push", "http://1118013-cw00061.tw1.ru/hard-push"]:
                response = requests.get(i)
                if response.status_code == 200:
                    break

        @self.dp.message_handler(commands=['change_body_10000'])
        async def change_body_10000(message: types.Message):
            list_table_name = []
            list_table_name.append(variable.admin_database)
            list_table_name.append(variable.archive_database)
            list_table_name.extend(variable.valid_professions)
            for table in list_table_name:
                self.db.run_free_request(
                    request=f"""ALTER TABLE {table} ALTER COLUMN session TYPE VARCHAR (50);"""
                )
                self.db.run_free_request(
                    request=f"""ALTER TABLE {table} ALTER COLUMN body TYPE VARCHAR (10000);"""
                )

        @self.dp.message_handler(commands=['pick_up_forcibly_from_admin'])
        async def pick_up_forcibly_from_admin_command(message: types.Message):
            await Form_pick_up_forcibly_from_admin.profession.set()
            await self.bot_aiogram.send_message(message.chat.id, 'type the profession')

        @self.dp.message_handler(state=Form_pick_up_forcibly_from_admin.profession)
        async def pick_up_forcibly_from_admin_command_form(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['profession'] = message.text
                profession = message.text
            await state.finish()
            await self.push_shorts_attempt_to_make_multi_function(
                message=message,
                callback_data='each',
                hard_push_profession=profession,
                only_pick_up_from_admin=True
            )

        @self.dp.message_handler(commands=['check_vacancies_for_relevance'])
        async def check_vacancies_for_relevance_command(message: types.Message):
            await check_vacancies_for_relevance(message)

        @self.dp.message_handler(commands=['transpose_no_sort_to_archive'])
        async def transpose_no_sort_to_archive_command(message: types.Message):
            await transpose_no_sort_to_archive(message)

        @self.dp.message_handler(commands=['show_db_records'])
        async def show_db_records_command(message: types.Message):
            await Form_profession_name.profession.set()
            await self.bot_aiogram.send_message(message.chat.id, 'type the profession')

        @self.dp.message_handler(state=Form_profession_name.profession)
        async def show_db_records_form(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['profession'] = message.text
                profession = message.text
            await state.finish()
            message_for_send = ''
            responses = self.db.get_all_from_db(
                table_name=variable.admin_database,
                param=f"WHERE profession LIKE '%{profession}%'",
                field=variable.admin_table_fields
            )
            if responses:
                number = random.randrange(0, len(responses))
                response_dict = await helper.to_dict_from_admin_response(responses[number], variable.admin_table_fields)
                for key in response_dict:
                    message_for_send += f"{key}: {response_dict[key]}\n"
                await self.bot_aiogram.send_message(message.chat.id, message_for_send)
            else:
                await self.bot_aiogram.send_message(message.chat.id, 'No vacancies')

        @self.dp.message_handler(commands=['get_channel_members'])
        async def get_channel_members_commands(message: types.Message):
            dialogs = await self.client.get_dialogs(200)
            groups = [dialog.entity for dialog in dialogs if dialog.is_group]
            for group in groups:
                print(group.title)

        @self.dp.message_handler(commands=['hard_pushing_by_schedule'])
        async def hard_pushing_by_schedule_commands(message: types.Message):
            if message.from_user.id in variable.white_admin_list:
                profession_list = variable.profession_list_for_pushing_by_schedule
                await self.bot_aiogram.send_message(message.chat.id, f"professions in the list: {profession_list}")

                # my_thread = threading.Thread(
                #     target=await hard_pushing_by_schedule, args=(message, profession_list))
                # my_thread.start()
                #
                await self.hard_pushing_by_schedule(
                    message=message,
                    profession_list=profession_list
                )

        @self.dp.message_handler(commands=['stop_hard_pushing_by_schedule'])
        async def hard_pushing_by_schedule_commands(message: types.Message):
            self.schedule_pushing_shorts = False

        @self.dp.message_handler(commands=['report_push_shorts'])
        async def report_push_shorts_commands(message: types.Message):
            await self.send_file_to_user(
                message=message,
                path=variable.path_push_shorts_report_file,
                caption="take the shorts report"
            )

        @self.dp.message_handler(commands=['add_copy_admin_table'])
        async def add_copy_admin_table_commands(message: types.Message):
            await add_copy_admin_table(message)

        @self.dp.message_handler(commands=['vacancies_from'])
        async def vacancies_from_commands(message: types.Message):
            date_in = datetime.now().strftime('%Y-%m-%d')
            for table in variable.tables_list_for_report:
                statistics_message = await vacancies_from(
                    profession=table,
                    date_in=date_in
                )
                if statistics_message:
                    await self.bot_aiogram.send_message(message.chat.id, f"{date_in}:\n{table}\n{statistics_message}",
                                                        disable_web_page_preview=True)
                else:
                    await self.bot_aiogram.send_message(message.chat.id, f"{date_in}:\n{table}\ndb is empty",
                                                        disable_web_page_preview=True)

        @self.dp.message_handler(commands=['rewrite_additional_db_fields'])
        async def rewrite_additional_db_fields_commands(message: types.Message):
            tables_list = []
            tables_list.extend(variable.valid_professions)
            tables_list.extend(variable.admin_database)
            for table_name in tables_list:
                responses = self.db.get_all_from_db(
                    table_name=table_name,
                    param="WHERE profession NOT LIKE '%no_sort%'",
                    field=variable.admin_table_fields
                )
                count = 0
                for vacancy in responses:
                    print(count, '.')
                    count += 1
                    vacancy_dict = await helper.to_dict_from_admin_response(vacancy, variable.admin_table_fields)
                    updated_vacancy_dict = helper.get_additional_values_fields(vacancy_dict)
                    data_for_change = {}
                    for field in variable.db_fields_for_update_in_parsing:
                        # print(f"regular {field}: {vacancy_dict[field]}")
                        # print(f"updated {field}: {updated_vacancy_dict[field]}")
                        if vacancy_dict[field] != updated_vacancy_dict[field]:
                            data_for_change[field] = updated_vacancy_dict[field]
                    if data_for_change:
                        self.db.update_table_multi(
                            table_name=variable.admin_database,
                            param=f"WHERE id={updated_vacancy_dict['id']}",
                            values_dict=data_for_change,
                            output_text="multi update has done"
                        )

        @self.dp.message_handler(commands=['copy_prof_tables_to_archive_prof_tables'])
        async def copy_prof_tables_to_archive_prof_tables_command(message: types.Message):
            await copy_prof_tables_to_archive_prof_tables()

        @self.dp.message_handler(commands=['add_field_into_tables_db'])
        async def add_field_into_tables_db_command(message: types.Message):
            await Form_add_field.field.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the name and field type')

        @self.dp.message_handler(state=Form_add_field.field)
        async def add_field_into_tables_db_form(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['profession'] = message.text
                field = message.text
            await state.finish()
            try:
                await add_field_into_tables_db(message, field)
                await self.bot_aiogram.send_message(message.chat.id, 'Done!')
            except Exception as e:
                await self.bot_aiogram.send_message(message.chat.id, str(e))

        @self.dp.message_handler(commands=['get_and_write_level'])
        async def get_from_admin_command(message: types.Message):
            await get_and_write_level(message)

        @self.dp.message_handler(commands=['update_level'])
        async def get_from_admin_command(message: types.Message):
            await update_level(message)

        @self.dp.message_handler(commands=['get_from_admin'])
        async def get_from_admin_command(message: types.Message):
            await get_from_admin(message)

        @self.dp.message_handler(commands=['get_vacancies_name_by_profession'])
        async def get_vacancies_name_by_profession_command(message: types.Message):
            await Form_vacancy_names.profession.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the profession')

        @self.dp.message_handler(state=Form_vacancy_names.profession)
        async def get_vacancies_name_by_profession_form(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['profession'] = message.text
                profession = message.text
            await state.finish()
            if profession not in variable.valid_professions:
                await Form_vacancy_names.profession.set()
                await self.bot_aiogram.send_message(message.chat.id, 'Type the correct profession')
            else:
                await get_vacancies_name_by_profession(message,profession)

        @self.dp.message_handler(commands=['rollback_last_short_session'])
        async def rollback_by_number_short_session_command(message: types.Message):
            await rollback_by_number_short_session(
                message=message
            )

        @self.dp.message_handler(commands=['rollback_by_number_short_session'])
        async def rollback_by_number_short_session_command(message: types.Message):
            await Form_rollback.short_session_name.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the shorts_session_name from you bot message')

        @self.dp.message_handler(state=Form_rollback.short_session_name)
        async def rollback_by_number_short_session_form(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['short_session_name'] = message.text
                short_session_name = message.text
            await state.finish()
            await rollback_by_number_short_session(
                message=message,
                short_session_number=short_session_name
            )

        @self.dp.message_handler(commands=['add_tags_to_DB'])
        async def add_tags_to_db_command(message: types.Message):
            await add_tags_to_db(message=message)

        @self.dp.message_handler(commands=['get_vacancy_names'])
        async def get_vacancy_names_command(message: types.Message):
            await Form_vacancy_names.profession.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the profession and bot shows you vacancy_names')

        @self.dp.message_handler(state=Form_vacancy_names.profession)
        async def get_vacancy_names_form(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['profession'] = message.text
                profession = message.text
            await state.finish()
            await get_vacancy_names(message, profession)
        
        @self.dp.message_handler(commands=['update_stats'])
        async def full_update_stats_table(message: types.Message):
            self.db.check_or_create_stats_table(table_name='stats_db')
            self.db.add_old_vacancies_to_stat_db()

        @self.dp.message_handler(commands=['get_post_request'])
        async def get_post_request_command(message: types.Message):
            await self.send_file_to_user(
                message=message,
                path=variable.path_post_request_file
            )

        @self.dp.message_handler(commands=['get_vacancy_from_backend'])
        async def get_vacancy_from_backend_command(message: types.Message):
            self.message = None
            self.show_vacancies['table'] = variable.admin_database
            self.show_vacancies['profession'] = 'junior'
            await get_vacancy_from_backend(message)

        @self.dp.message_handler(commands=['add_and_push_subs'])
        async def add_and_push_subs_command(message: types.Message):
            await add_subs()
            await push_subs(message=message)

        @self.dp.message_handler(commands=['get_vacancy_for_example'])
        async def get_vacancy_for_example_command(message: types.Message):
            response_dict = {}
            response = self.db.get_all_from_db(
                table_name=variable.admin_database,
                field=variable.admin_table_fields
            )
            if response:
                response_dict = await helper.to_dict_from_admin_response(
                    response=response[random.randrange(0, len(response))],
                    fields=variable.admin_table_fields
                )
                if len(str(response_dict))<4096:
                    await self.bot_aiogram.send_message(message.chat.id, response_dict)
                else:
                    await self.bot_aiogram.send_message(message.chat.id, 'to long')

            else:
                await self.bot_aiogram.send_message(message.chat.id, 'not response')

        @self.dp.message_handler(commands=['get_profession_parsing_tags_log'])
        async def get_profession_parsing_tags_log_command(message: types.Message):
            if message.from_user.id in self.white_admin_list:
                await self.send_file_to_user(
                    message=message,
                    path=variable.path_log_check_profession,
                    caption="take the tags"
                )

            else:
                await self.bot_aiogram.send_message(message.chat.id, "Sorry, your permission is wrong")

        @self.dp.message_handler(commands=['get_flood_error_logs'])
        async def get_flood_error_logs_commands(message: types.Message):
            await self.send_file_to_user(
                message=message,
                path=variable.flood_control_logs_path,
                caption="take the exception logs"
            )

        @self.dp.message_handler(commands=['how_many_records_in_db_table'])
        async def how_many_records_in_db_table_commands(message: types.Message):
            await Form_db.name.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the table name like the profession')

        @self.dp.message_handler(state=Form_db.name)
        async def emergency_push_profession(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['name'] = message.text
                db_name = message.text
            await state.finish()
            response = self.db.get_all_from_db(
                table_name=db_name,
                field='id'
            )
            if type(response) is not str:
                await self.bot_aiogram.send_message(message.chat.id, f'{len(response)} records')
            else:
                await self.bot_aiogram.send_message(message.chat.id, f'{str(response)}')

        @self.dp.message_handler(commands=['how_many_vacancies_published'])
        async def how_many_vacancies_published_commands(message: types.Message):

            # self.db.check_or_create_stats_table()
            # self.db.add_old_vacancies_to_stat_db()

            await Form_report.date_in.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the starting date in format: YYYY-MM-DD')

        @self.dp.message_handler(state=Form_report.date_in)
        async def report_published (message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['date_in'] = message.text
                date = data['date_in']
                try:
                    valid_date = datetime.strptime(date, '%Y-%m-%d')
                    await Form_report.date_out.set()
                    await self.bot_aiogram.send_message(message.chat.id, 'Type the ending date in format: YYYY-MM-DD \n or put 1 for one-day report')
                except ValueError:
                    await self.bot_aiogram.send_message(message.chat.id, 'Invalid date!')
                    await Form_report.date_in.set()
                    await self.bot_aiogram.send_message(message.chat.id, 'Type the starting date in format: YYYY-MM-DD')

        @self.dp.message_handler(state=Form_report.date_out)
        async def report_published (message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['date_out'] = message.text
                date_in = data['date_in']
                date_out = data['date_out']
                if date_out != '1':
                    try:
                        valid_date = datetime.strptime(date_out, '%Y-%m-%d')
                    except ValueError:
                        await self.bot_aiogram.send_message(message.chat.id, 'Invalid date!')
                        await Form_report.date_out.set()
                        await self.bot_aiogram.send_message(message.chat.id, 'Type the ending date in format: YYYY-MM-DD')
                if date_out != '1' and datetime.strptime(date_in, '%Y-%m-%d') > datetime.strptime(date_out, '%Y-%m-%d'):
                    await self.bot_aiogram.send_message(message.chat.id, 'Check the dates! Ending date should be later than starting date.')
                    await Form_report.date_in.set()
                    await self.bot_aiogram.send_message(message.chat.id, 'Type the starting date in format: YYYY-MM-DD')
            await state.finish()
            if date_out == '1':
                date_out = date_in
            self.db.make_report_published_vacancies_excel(date1=date_in, date2=date_out)

            await self.send_file_to_user(message, f'./excel/report_{date_in}_{date_out}.xlsx')

        @self.dp.message_handler(commands=['how_many_vacancies_total'])
        async def how_many_vacancies_total(message: types.Message):
            await Form_report_total.date_in.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the starting date in format: YYYY-MM-DD not earlier than 2023-01-01')

        @self.dp.message_handler(state=Form_report_total.date_in)
        async def report_total (message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['date_in'] = message.text
                date = data['date_in']
                try:
                    valid_date = datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    await self.bot_aiogram.send_message(message.chat.id, 'Invalid date!')
                    await Form_report_total.date_in.set()
                    await self.bot_aiogram.send_message(message.chat.id, 'Type the starting date in format: YYYY-MM-DD')
                if datetime.strptime(date, '%Y-%m-%d') < datetime(2023, 1, 1):
                    await self.bot_aiogram.send_message(message.chat.id, 'Check the dates! Starting date should be later 2023-01-01')
                    await Form_report_total.date_in.set()
                    await self.bot_aiogram.send_message(message.chat.id, 'Type the starting date in format: YYYY-MM-DD')
                else:
                    await Form_report_total.date_out.set()
                    await self.bot_aiogram.send_message(message.chat.id, 'Type the ending date in format: YYYY-MM-DD \n or put 1 for one-day report')

        @self.dp.message_handler(state=Form_report_total.date_out)
        async def report_total (message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['date_out'] = message.text
                date_in = data['date_in']
                date_out = data['date_out']
                if date_out != '1':
                    try:
                        valid_date = datetime.strptime(date_out, '%Y-%m-%d')
                    except ValueError:
                        await self.bot_aiogram.send_message(message.chat.id, 'Invalid date!')
                        await Form_report_total.date_out.set()
                        await self.bot_aiogram.send_message(message.chat.id, 'Type the ending date in format: YYYY-MM-DD')
                if date_out != '1' and datetime.strptime(date_in, '%Y-%m-%d') > datetime.strptime(date_out, '%Y-%m-%d'):
                    await self.bot_aiogram.send_message(message.chat.id, 'Check the dates! Ending date should be later than starting date.')
                    await Form_report_total.date_in.set()
                    await self.bot_aiogram.send_message(message.chat.id, 'Type the starting date in format: YYYY-MM-DD')

            await state.finish()
            if date_out == '1':
                date_out = date_in
            self.db.statistics_total(date_in=date_in, date_out=date_out)

            await self.send_file_to_user(message, f'./excel/report_total_{date_in}_{date_out}.xlsx')

        @self.dp.message_handler(commands=['invite_people'])
        async def invite_people_command(message: types.Message):
            await invite_people(message)

        @self.dp.message_handler(commands=['get_news'])
        async def get_news_command(message: types.Message):
            await get_news(message)

        @self.dp.message_handler(commands=['schedule'])
        async def schedule_command(message: types.Message):
            if message.from_user.id in self.white_admin_list:
                await schedule(message)
            else:
                await self.bot_aiogram.send_message(message.chat.id, "Sorry, your permission is wrong")

        @self.dp.message_handler(commands=['restore_from_admin'])
        async def restore_from_admin_command(message: types.Message):
            await restore_from_admin(message, 110)

        @self.dp.message_handler(commands=['read_pattern_row'])
        async def stop_commands(message: types.Message):
            excel_dict = {}
            pattern = data_pattern
            for key in pattern:
                if type(pattern[key]) is not dict:
                    excel_dict = await compose_excel_dict(
                        key='profession',
                        value=key,
                        key_list=['profession', 'sub', 'sub_profession', 'sub_sub'],
                        excel_dict=excel_dict
                    )
                    for key2 in pattern[key]:
                        if type(pattern[key][key2]) is not dict:
                            excel_dict = await compose_excel_dict(
                                key='sub',
                                value=key2,
                                key_list=['profession', 'sub', 'sub_profession', 'sub_sub'],
                                excel_dict=excel_dict
                            )
                            for key3 in pattern[key][key2]:
                                if type(pattern[key][key2][key3]) is not dict:
                                    excel_dict = await compose_excel_dict(
                                        key='sub_profession',
                                        value=key3,
                                        key_list=['profession', 'sub', 'sub_profession', 'sub_sub'],
                                        excel_dict=excel_dict
                                    )

        @self.dp.message_handler(commands=['stop'])
        async def stop_commands(message: types.Message):
            self.msg = await self.bot_aiogram.send_message(message.chat.id, 'Please wait...')
            if self.task:
                was_cancelled = self.task.cancel()
                await self.msg.edit_text(f"{self.msg.text}\nProcess was stopped. Status: {was_cancelled}")
                print(f"Process was stopped. Status: {was_cancelled}")
                self.task = None
            else:
                await self.msg.edit_text(f"{self.msg.text}\nSorry, no one parser works")


        @self.dp.message_handler(commands=['db_check_url_vacancy'])
        async def db_check_url_vacancy_commands(message: types.Message):
            await Form_check_url.url.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the vacancy_url to looking for in the database')

        @self.dp.message_handler(state=Form_check_url.url)
        async def db_check_url_vacancy_form(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['url'] = message.text
                url = message.text
            await state.finish()
            vacancy_text = await db_check_url_vacancy(message, url=url)
            if vacancy_text:
                await self.bot_aiogram.send_message(message.chat.id, vacancy_text)

        @self.dp.message_handler(commands=['db_check_add_single_vacancy'])
        async def db_check_url_vacancy_commands(message: types.Message):
            await Form_check_url_to_add.url.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the vacancy_url to check in db and add')

        @self.dp.message_handler(state=Form_check_url_to_add.url)
        async def db_check_url_vacancy_form(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['url'] = message.text
                url = message.text
            await state.finish()
            vacancy_text = await db_check_add_single_vacancy(message, url=url)
            # if vacancy_text:
            #     await self.bot_aiogram.send_message(message.chat.id, vacancy_text)

        @self.dp.message_handler(commands=['emergency_push'])
        async def emergency_push(message: types.Message):
            await Form_emergency_push.profession.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the profession')

        @self.dp.message_handler(state=Form_emergency_push.profession)
        async def emergency_push_profession(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['profession'] = message.text
                profession = message.text
            await state.finish()
            await self.push_shorts_attempt_to_make_multi_function(
                message=message,
                callback_data=f'PUSH shorts to {profession.lower()}'
            )

        @self.dp.message_handler(commands=['logs', 'log'])
        async def get_logs(message: types.Message):
            path = './logs/logs.txt'
            await self.send_file_to_user(message, path)

        @self.dp.message_handler(commands=['numbers_of_archive'])
        async def get_numbers_of_archive_commands(message: types.Message):
            response = self.db.get_all_from_db(
                table_name='archive',
                field='id'
            )
            await self.bot_aiogram.send_message(message.chat.id, f"There are {len(response)} vacancies in archive table")

        @self.dp.message_handler(commands=['get_pattern'])
        async def get_logs(message: types.Message):
            if message.from_user.id in variable.white_admin_list:
                path = variable.pattern_path
                await helper.get_pattern(path)
                await self.send_file_to_user(message, path, 'Please take the pattern')
                await self.send_file_to_user(message, variable.path_last_pattern, 'There are all merges')
                await self.send_file_to_user(message, variable.path_data_pattern, 'All data have got from it')
            else:
                await self.bot_aiogram.send_message(message.chat.id, variable.message_not_access)

        @self.dp.message_handler(commands=['get_pattern_pseudo'])
        async def get_pattern_pseudo_commands(message: types.Message):
            if message.from_user.id in variable.white_admin_list:
                path = variable.pattern_path
                await helper.get_pattern(path, pseudo=True)
                await self.send_file_to_user(message, path, 'Please take the pattern')
            else:
                await self.bot_aiogram.send_message(message.chat.id, variable.message_not_access)

        @self.dp.message_handler(commands=['debugs'])
        async def get_debugs(message: types.Message):
            await debug_function()

        @self.dp.message_handler(commands=['get_tables_and_fields'])
        async def get_tables_and_fields(message: types.Message):
            dict_tables = {}
            info = self.db.get_information_about_tables_and_fields()
            for i in info:
                if i[0] not in dict_tables:
                    dict_tables[i[0]] = []
                dict_tables[i[0]].append(i[1])
            for i in dict_tables:
                print(f"{i}:")
                count = 0
                message_for_send = f"{i}:\n"
                for element in dict_tables[i]:
                    print(f"   {count}-{element}")
                    message_for_send += f"   {count}-{element}\n"
                    count += 1
                await self.bot_aiogram.send_message(message.chat.id, message_for_send)
                await asyncio.sleep(random.randrange(1, 2))
                print('--------\n')

        @self.dp.message_handler(commands=['get_backup_db'])
        async def get_logs(message: types.Message):
            try:
                await self.send_file_to_user(
                message=message,
                path='./db_backup/backup_from_server.backup',
                caption='Take the backup from server'
            )
            except Exception as e:
                print(e)

        @self.dp.message_handler(commands=['check_doubles'])
        async def get_doubles(message: types.Message):
            await get_remove_doubles(message)

        @self.dp.message_handler(commands=['clear_db_table'])
        async def dp_clear_db_table(message: types.Message):
            await Form_clean.profession.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the profession you want to delete')

        # ------------------------ fill profession form ----------------------------------
        @self.dp.message_handler(state=Form_clean.profession)
        async def process_api_id(message: types.Message, state: FSMContext):
            if message.text in variable.valid_professions:
                async with state.proxy() as data:
                    data['profession'] = message.text
                await Form_clean.quantity_leave.set()
                await self.bot_aiogram.send_message(message.chat.id, 'Type what is vacancy quantity you want to leave')
            else:
                await Form_clean.profession.set()
                await self.bot_aiogram.send_message(message.chat.id, 'Type the profession you want to delete')

        @self.dp.message_handler(state=Form_clean.quantity_leave)
        async def process_api_id(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['quantity_leave'] = message.text
                quantity_leave = message.text
                profession = data['profession']
            await state.finish()
            msg = await self.bot_aiogram.send_message(message.chat.id, "Please waite a few seconds")
            await clear_db_table(
                profession, quantity_leave
            )
            await msg.edit_text(f"{msg.text}\nDone!")

        @self.dp.message_handler(commands=['refresh'])
        async def refresh_vacancies(message: types.Message):
            # refresh all professions
            await refresh(message)

        @self.dp.message_handler(commands=['refresh_and_save_changes'])  #
        async def refresh_vacancies_and_save(message: types.Message):
            with open(variable.path_filter_error_file, 'w') as f:
                f.write(str(datetime.now().strftime('%d-%m-%y %H:%M')))

            # refresh all professions
            await refresh(message, save_changes=True)
            # remove doubles in admin
            await get_remove_doubles(message)
            # remove completed professions
            await transpose_no_sort_to_archive(message)
            # await remove_completed_professions(message)

            await self.send_file_to_user(
                message=message,
                path=variable.path_filter_error_file,
                caption='wrong words in pattern'
            )

        @self.dp.message_handler(commands=['remove_completed_professions'])
        async def remove_prof(message: types.Message):
            await remove_completed_professions(message)

        @self.dp.message_handler(commands=['get_participants'])
        async def get_participants(message: types.Message):
            await main(
                report=self.report,
                client=self.client,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id},
                action='get_participants'
            )

        @self.dp.message_handler(commands=['peerchannel'])
        async def get_logs(message: types.Message):
            await self.bot_aiogram.send_message(message.chat.id, 'Type the channel link and get channel data')
            self.peerchannel = True

        @self.dp.message_handler(commands=['download'])
        async def download(message: types.Message):
            if message.from_user.id in self.white_admin_list:
                await get_excel_tags_from_admin(message)
            else:
                await self.bot_aiogram.send_message(message.chat.id, '🚀 Sorry, this options available only for admin')

        @self.dp.message_handler(commands=['geek'])
        async def geek(message: types.Message):

            geek = GeekGetInformation(
                search_word=None,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            )
            await geek.get_content()

        @self.dp.message_handler(commands=['svyazi'])
        async def geek(message: types.Message):

            svyazi = SvyaziGetInformation(
                search_word=None,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            )
            await svyazi.get_content()

        @self.dp.message_handler(commands=['rabota'])
        async def geek(message: types.Message):

            rabota = RabotaGetInformation(
                search_word=None,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            )
            await rabota.get_content()

        @self.dp.message_handler(commands=['superjob'])
        async def geek(message: types.Message):

            superjob = SuperJobGetInformation(
                search_word=None,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            )
            await superjob.get_content()

        @self.dp.message_handler(commands=['dev'])
        async def geek(message: types.Message):

            dev = DevGetInformation(
                search_word=None,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            )
            await dev.get_content()

        @self.dp.message_handler(commands=['finder'])
        async def finder(message: types.Message):

            finder = FinderGetInformation(
                search_word=None,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            )
            await finder.get_content()

        @self.dp.message_handler(commands=['habr'])
        async def finder(message: types.Message):
            habr = HabrGetInformation(
                search_word=None,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            )
            await habr.get_content()

        @self.dp.message_handler(commands=['ingame'])
        async def ingame(message: types.Message):

            ingame = IngameJobGetInformation(
                search_word=None,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id},
                report=self.report
            )
            await ingame.get_content()

        @self.dp.message_handler(commands=['get_user_data'])
        async def get_user_data(message: types.Message):
            await Form_user.user_data.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the username or the id')

            # ------------------------ fill search user form ----------------------------------
            # user
            @self.dp.message_handler(state=Form_user.user_data)
            async def process_api_id(message: types.Message, state: FSMContext):
                async with state.proxy() as data:
                    data['user_data'] = message.text
                    user_data = message.text
                await state.finish()
                info = await self.client.get_entity(user_data)
                await self.bot_aiogram.send_message(message.chat.id, info)

        @self.dp.message_handler(commands=['praca'])
        async def praca_commands(message: types.Message):
            praca = PracaGetInformation(
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            )
            await praca.get_content()
            await self.send_file_to_user(
                message=message,
                path=variable.path_log_check_profession,
                caption=""
            )

        @self.dp.message_handler(commands=['hh_kz'])
        async def hh_kz_commands(message: types.Message):
            await Form_hhkz.word.set()
            await self.bot_aiogram.send_message(message.chat.id,
                                                'Type word for getting more vacancies from hh.kz\nor /cancel')

        # ------------------------ fill search word form ----------------------------------
        # word
        @self.dp.message_handler(state=Form_hhkz.word)
        async def process_api_id(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['word'] = message.text
                search_word = message.text
            await state.finish()
            await send_log_txt(text='', write_mode='w')
            hh_kz = HHKzGetInformation(
                search_word=search_word,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            )
            await hh_kz.get_content()
            await self.send_file_to_user(
                message=message,
                path=variable.path_log_check_profession,
                caption=""
            )

        @self.dp.message_handler(commands=['magic_word'])
        async def magic_word(message: types.Message):
            await Form_hh.word.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type word for getting more vacancies from hh.ru\nor /cancel')

        # ------------------------ fill search word form ----------------------------------
        # word
        @self.dp.message_handler(state=Form_hh.word)
        async def process_api_id(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['word'] = message.text
                search_word = message.text
            await state.finish()
            await send_log_txt(text='', write_mode='w')
            hh = HHGetInformation(
                search_word=search_word,
                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id},
                report=self.report
            )
            await hh.get_content()
            await self.send_file_to_user(
                message=message,
                path=variable.path_log_check_profession,
                caption=""
            )

            # pool = Pool(processes=3)
            # result = pool.apply_async(hh.get_content, ())
            # print(result.get(timeout=1))

# -----------------------------------------------------------------------
        @self.dp.message_handler(commands=['check_title_body'])
        async def check_in_db(message: types.Message):
            if message.from_user.id in self.white_admin_list:
                await Form_check.title.set()
                await self.bot_aiogram.send_message(message.chat.id, 'Text in title')
            else:
                await self.bot_aiogram.send_message(message.chat.id, '🚀 Sorry, this options available only for admin')

        @self.dp.message_handler(state=Form_check.title)
        async def process_api_id(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['title'] = message.text
            await Form_check.body.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Text in body')

        @self.dp.message_handler(state=Form_check.body)
        async def process_api_id(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['body'] = message.text
                title = data['title']
                body = data['body']
            await state.finish()
            results = await search_vacancy_in_db(title, body)
            if not results['len']:
                await self.bot_aiogram.send_message(message.chat.id, f"not found")
            else:
                message_for_send = ''
                for i in results:
                    message_for_send += f"{i}: {results[i]}\n"
                await self.bot_aiogram.send_message(message.chat.id, f"search results:\n{message_for_send}")

        @self.dp.message_handler(commands=['check_link_hh'])
        async def check_in_db(message: types.Message):
            if message.from_user.id in self.white_admin_list:
                await Form_check_link.link.set()
                await self.bot_aiogram.send_message(message.chat.id, 'Insert the HH link')
            else:
                await self.bot_aiogram.send_message(message.chat.id, '🚀 Sorry, this options available only for admin')

        @self.dp.message_handler(state=Form_check_link.link)
        async def process_api_id(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['link'] = message.text
                link = message.text
            await state.finish()
            if 'https://hh.ru/vacancy/' in link:
                hh = HHGetInformation(
                    bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id},
                    search_word=None
                )
                await hh.get_content_by_link_alone(link)

# -----------------------------------------------------------------------

        @self.dp.message_handler(commands=['delete_till'])
        async def download(message: types.Message):
            if message.from_user.id in self.white_admin_list:
                await Form_delete.date.set()
                await self.bot_aiogram.send_message(message.chat.id,
                                               'Until what date to delete (exclusive)? Format YYYY-MM-DD\nor /cancel')
            else:
                await self.bot_aiogram.send_message(message.chat.id, '🚀 Sorry, this options available only for admin')

        # ------------------------ fill date form ----------------------------------
        # date
        @self.dp.message_handler(state=Form_delete.date)
        async def process_api_id(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['date'] = message.text
                await delete_since(tables_list=['admin_last_session'], param=f"""WHERE DATE(created_at)<'{data['date']}'""")

            await state.finish()

        @self.dp.message_handler(commands=['ambulance'])
        async def ambulance(message: types.Message):
            short = ''
            shorts_list = []
            with open('excel/ambulance/ambulance_shorts.txt', 'r') as file:
                shorts = file.read()
            if len(shorts)<4096:
                return await self.bot_aiogram.send_message(message.chat.id, shorts, parse_mode='html')
            else:
                shorts = shorts.split('\n\n')
                for i in shorts:
                    if len(f"{short}{i}\n\n") < 4096:
                        short += f"{i}\n\n"
                    else:
                        shorts_list.append(short)
                        short = f"{i}\n\n"
                n_count = 1
                for i in shorts_list:
                    await self.bot_aiogram.send_message(message.chat.id, i, parse_mode='html')
                    print(n_count, 'short ambulance')
                    n_count += 1
                    await asyncio.sleep(random.randrange(1, 3))

        @self.dp.message_handler(commands=['add_statistics'])
        async def add_statistics(message: types.Message):
            stat_dict = {}

            for channel in self.valid_profession_list:
                try:
                    messages = await self.get_tg_history_messages(
                        message=message,
                        channel=config['My_channels'][f"{channel}_channel"],
                        limit_msg=100
                    )
                    for vacancy in messages:
                        year = int(vacancy['date'].strftime('%Y'))
                        month = int(vacancy['date'].strftime('%m'))
                        day = int(vacancy['date'].strftime('%d'))

                        if datetime(year, month, day) > datetime(2022, 10, 15):
                            date = vacancy['date'].strftime("%d.%m.%y")
                            if date not in stat_dict:
                                stat_dict[date] = {}
                            if channel not in stat_dict[date]:
                                stat_dict[date][channel] = 0
                            stat_dict[date][channel] += len(re.findall(r"Вакансия: ", vacancy['message']))
                except:
                    print(f'channel {channel} has the accidence')
                    await self.bot_aiogram.send_message(message.chat.id, f'channel {channel} has the accidence')

                await asyncio.sleep(3)

            for i in stat_dict:
                print(f"{i}: {stat_dict[i]}")

            pass

        @self.dp.message_handler(commands=['get_participants'])
        async def download(message: types.Message):
            await Form_participants.channel.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Type the channel link\nor /cancel')

        # ------------------------ fill channel form ----------------------------------
        # channel
        @self.dp.message_handler(state=Form_participants.channel)
        async def process_api_id(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['channel'] = message.text
                # wtdm = WriteToDbMessages(
                #     client=self.client,
                #     # bot_dict={
                #     #     'bot': self.bot_aiogram,
                #     #     'chat_id': message.chat.id
                #     # }
                # )
                path = await self.tg_parser.dump_all_participants(
                    channel=data['channel'],
                    bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
                )
            await state.finish()
            if path:
                with open(path, 'rb') as file:
                    await self.bot_aiogram.send_document(message.chat.id, file, caption='There are all subscribers from channel you order')
            else:
                await self.bot_aiogram.send_message(message.chat.id, 'Sorry, No file')

        @self.dp.message_handler(commands=['check_parameters'])
        async def check_parameters(message: types.Message):
            await Form_params.vacancy.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Forward the vacancy now for checking outputs from pattern filter\nor /cancel')

        # ------------------------ fill parameters form ----------------------------------
        # parameters
        @self.dp.message_handler(state=Form_params.vacancy)
        async def check_parameters_form(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['vacancy'] = message.text
                vacancy = data['vacancy']
            await state.finish()
            if '\n' in vacancy:
                title = vacancy.split('\n', 1)[0]
                body = vacancy.split('\n', 1)[1]
            else:
                title = vacancy
                body = ''

            dict_response = VacancyFilter().sort_profession(
                body=body,
                title=title,
                check_contacts=True,
                check_vacancy=True,
                # check_vacancy_only_mex=True
            )

            profession = dict_response['profession']

            message_for_send = "<b>PATTERN'S RESULTS:</b>\n\n"
            message_for_send += f"<b>PROFESSIONS:</b>\n{profession['profession']}\n" \
                                f"<b>MA:</b>\n{profession['tag']}\n" \
                                f"<b>MEX:</b>\n{profession['anti_tag']}"

            await self.bot_aiogram.send_message(message.chat.id, message_for_send, parse_mode='html')

        @self.dp.message_handler(commands=['refresh_pattern'])
        async def get_logs(message: types.Message):
            path = './patterns/pattern_test.py'
            await refresh_pattern(path)

        @self.dp.message_handler(commands=['update_job_types'])
        async def update_job_types(message: types.Message):
            await update_job_types(message)

        @self.dp.message_handler(commands=['id'])
        async def get_logs(message: types.Message):
            # 311614392
            # 533794904
            # 857262125
            # 1359259501
            # 537301906
            for i in [311614392, 533794904, 857262125, 1359259501, 537301906]:
                try:
                    # peer = PeerUser(i)
                    data = await self.client.get_entity(i)
                    await self.bot_aiogram.send_message(message.chat.id, str(data))
                    await asyncio.sleep(6)
                except Exception as e:
                    await self.bot_aiogram.send_message(message.chat.id, f"{i}: {str(e)}")
                    await asyncio.sleep(6)

        @self.dp.message_handler(commands=['restore'])
        async def get_logs(message: types.Message):
            profession_list = {}
            results_dict = {}

            for profession in self.valid_profession_list:
                channel = config['My_channels'][f'{profession}_channel']
                all_message = await self.get_tg_history_messages(message, channel)
                if all_message:
                    for vacancy in all_message:
                        results_dict['title'] = vacancy['message'].partition(f'\n')[0]
                        results_dict['body'] = vacancy['message'].replace(results_dict['title'], '').replace(f'\n\n', f'\n')
                        results_dict['time_of_public'] = (vacancy['date'] + timedelta(hours=3))
                        results_dict['created_at'] = results_dict['time_of_public']
                        results_dict['chat_name'] = ''
                        results_dict['vacancy'] = ''
                        results_dict['vacancy_url'] = ''
                        results_dict['company'] = ''
                        results_dict['english'] = ''
                        results_dict['relocation'] = ''
                        results_dict['job_type'] = ''
                        results_dict['city'] = ''
                        results_dict['salary'] = ''
                        results_dict['experience'] = ''
                        results_dict['contacts'] = ''
                        results_dict['session'] = '20221114114824'
                        results_dict['sub'] = ''

                        sub = VacancyFilter().sort_profession(
                            title=results_dict['title'],
                            body=results_dict['body'],
                            check_contacts=False,
                            check_vacancy=True,
                            get_params=False
                        )['profession']['sub']

                        if profession in sub:
                            results_dict['sub'] = f"{profession}: {', '.join(results_dict['sub'][profession])}"
                        else:
                            results_dict['sub'] = f"{profession}: "

                        is_exist = self.db.get_all_from_db(
                            table_name=profession,
                            param=f"""WHERE title='{results_dict['title']}' AND body='{results_dict['body']}'"""
                        )
                        pass
                        if not is_exist:
                            print('NOT IN DB')
                            print('profession: ', profession)

                            profession_list['profession'] = [profession,]
                            self.db.push_to_bd(
                                results_dict=results_dict,
                                profession_list=profession_list
                            )
                        else:
                            print('*** IN DB EXISTS ***')
                            print('profession: ', profession)

                            profession_list['profession'] = [profession, ]
                            self.db.push_to_bd(
                                results_dict=results_dict,
                                profession_list=profession_list
                            )

            # vacancies loop
            # get one channel, get vacancies
            # check prof. db
            # if not exists do write

        # Возможность отмены, если пользователь передумал заполнять
        @self.dp.message_handler(state='*', commands=['cancel', 'start'])
        @self.dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
        async def cancel_handler(message: types.Message, state: FSMContext):
            current_state = await state.get_state()
            if current_state is None:
                return

            await state.finish()
            await message.reply('ОК')

        #------------------------ api id----------------------------------
        # api_id
        @self.dp.message_handler(state=Form.api_id)
        async def process_api_id(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['api_id'] = message.text

            await Form.next()
            await self.bot_aiogram.send_message(message.chat.id, "Введите api_hash (отменить /cancel)")

        #-------------------------- api_hash ------------------------------
        # api_hash
        @self.dp.message_handler(state=Form.api_hash)
        async def process_api_hash(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['api_hash'] = message.text

            await Form.next()
            await self.bot_aiogram.send_message(message.chat.id, "Type your phone number +XXXXXXXXXX (11 numbers with + and country code)\nor cancel for exit")

        #-------------------------- phone number ------------------------------
        # phone_number
        @self.dp.message_handler(state=Form.phone_number)
        async def process_phone_number(message: types.Message, state: FSMContext):

            # global phone_number

            logs.write_log(f"invite_bot_2: Form.phone number")

            async with state.proxy() as data:
                data['phone_number'] = message.text

                logs.write_log(f"invite_bot_2: phone number: {data['phone_number']}")

                await self.bot_aiogram.send_message(
                    message.chat.id,
                    f"Your api_id: {data['api_id']}\nYour api_hash: {data['api_hash']}\nYour phone number: {data['phone_number']}")

                self.api_id = data['api_id']
                self.api_hash = data['api_hash']
                self.phone_number = data['phone_number']

            self.db.write_user_without_password(
                id_user=message.from_user.id,
                api_id=int(self.api_id),
                api_hash=self.api_hash,
                phone_number=self.phone_number
            )
            self.password = None

            await connect_with_client(message, id_user=message.from_user.id)

        #-------------------------- code ------------------------------
        # code
        async def get_code(message):

            logs.write_log(f"invite_bot_2: function get_code")

            await Form.code.set()
            await self.bot_aiogram.send_message(message.chat.id, 'Введите код в формате 12345XXXXX6789, где ХХХХХ - цифры телеграм кода (отмена* /cancel)')

        @self.dp.message_handler(state=Form.code)
        async def process_phone_number(message: types.Message, state: FSMContext):

            # global client, hash_phone, phone_number

            logs.write_log(f"invite_bot_2: Form.code")

            async with state.proxy() as data:
                data['code'] = message.text
                self.code = data['code'][5:10]

                logs.write_log(f"invite_bot_2: Form.code: {data['code']}")

                # ask to get password (always)
                if not self.password:
                    await Form.password.set()
                    await self.bot_aiogram.send_message(message.chat.id,
                                               "Please type your password 2 step verify if you have\n"
                                               "Type 0 if you don't\n(type /cancel for exit)")
                else:
                    await state.finish()
                    await client_sign_in(message)

        # -------------------------- password ------------------------------
        # password
        @self.dp.message_handler(state=Form.password)
        async def process_api_hash(message: types.Message, state: FSMContext):
            logs.write_log('invite_bot_2: Form.password')

            async with state.proxy() as data:
                data['password'] = message.text
            self.password = data['password']
            logs.write_log(f"invite_bot_2: Form.password: {data['password']}")
            # self.db.add_password_to_user(id=self.current_customer[0], password=self.password)

            await state.finish()
            await client_sign_in(message)

            # await Form.next()
            # await bot_aiogram.send_message(message.chat.id, "Введите номер телефона (отменить /cancel)")

        async def client_sign_in(message):
            try:

                if self.password == '0':
                    await self.client.sign_in(phone=self.phone_number, code=self.code, phone_code_hash=self.hash_phone)
                    await self.bot_aiogram.send_message(message.chat.id, 'Connection is ok')

                else:
                    # await client.sign_in(phone=self.phone_number, password=self.password, code=self.code, phone_code_hash=self.hash_phone)
                    await self.client.sign_in(password=self.password, code=self.code)

                    await self.bot_aiogram.send_message(message.chat.id, 'Connection is ok')

            except Exception as e:
                await self.bot_aiogram.send_message(message.chat.id, str(e))

        @self.dp.callback_query_handler()
        async def catch_callback(callback: types.CallbackQuery):
            short_digest = ''
            response = []
            if callback.data == '>>':
                self.show_vacancies['offset'] += 1
                await get_vacancy_from_backend(callback.message)

            if callback.data == '<<':
                self.show_vacancies['offset'] -= 1
                await get_vacancy_from_backend(callback.message)

            if callback.data == 'personal':
                await invite_users(
                    message=callback.message,
                    channel=self.channel,
                )

            if callback.data == 'group':
                await invite_set_users(
                    message=callback.message,
                    channel=self.channel,
                )

            if callback.data == 'consolidated_table':
                await output_consolidated_table(callback.message)

            if callback.data == 'go_by_admin': # next step if callback.data[2:] in self.valid_profession_list:
                # make the keyboard with all professions
                if callback.message.from_user.id in variable.white_admin_list:
                    self.markup = await compose_inline_keyboard(prefix='admin')
                    await self.bot_aiogram.send_message(callback.message.chat.id, 'choose the channel for vacancy checking', reply_markup=self.markup)
                else:
                    await self.bot_aiogram.send_message(callback.message.chat.id, "Sorry, You have not the permissions")

            if callback.data[0:5] == 'admin':
                tables = self.db.get_information_about_tables_and_fields(only_tables=True)
                if "shorts_at_work" not in tables:
                    self.db.create_table_common(
                        field_list=["shorts_at_work BOOLEAN"],
                        table_name="shorts_at_work"
                    )
                    self.db.push_to_db_common(
                        table_name='shorts_at_work',
                        fields_values_dict={"shorts_at_work": False}
                    )
                self.shorts_at_work = self.db.get_all_from_db(
                    table_name="shorts_at_work",
                    param="WHERE id=1",
                    without_sort=True,
                )[0][1]

                if not self.shorts_at_work:
                    self.db.push_to_db_common(
                        table_name="shorts_at_work",
                        fields_values_dict={"shorts_at_work": True},
                        params="WHERE id=1"
                    )
                    await self.send_vacancy_to_admin_channel(callback.message, callback.data)
                else:
                    await self.bot_aiogram.send_message(callback.message.chat.id, "Sorry shorts at work now. Please wait some time")

            if callback.data == 'one_day_statistics':
                self.feature = 'one_day_statistics'
                await self.bot_aiogram.send_message(callback.message.chat.id, "Type the date (format YYYY-MM-DD)")
                # today_statistics = f"Statistics today {datetime.now().strftime('%Y-%m-%d')}:\n\n"
                # print(datetime.now().strftime('%Y-%m-%d'))

            if callback.data == 'hard_push':
                button_all_vacancies = InlineKeyboardButton('all', callback_data='all')
                button_each_vacancy = InlineKeyboardButton('choose profession', callback_data='each_profession')
                markup = InlineKeyboardMarkup()
                markup.row(button_all_vacancies, button_each_vacancy)
                await self.bot_aiogram.send_message(callback.message.chat.id, "It's the pushing without admin", reply_markup=markup)

            elif 'PUSH' in callback.data and 'shorts' in callback.data:

                helper.add_to_report_file(
                    path=variable.path_push_shorts_report_file,
                    write_mode='a',
                    text=f"[BUTTON] shorts callback.data: {callback.data}\n"
                )

                await self.push_shorts_attempt_to_make_multi_function(
                    message = callback.message,
                    callback_data=callback.data
                )

            if callback.data == 'all':
                await self.push_shorts_attempt_to_make_multi_function(
                    message = callback.message,
                    callback_data = callback.data,
                    hard_pushing=True,
                    hard_push_profession='*'
                )
                # await hard_post(callback.message)

            if callback.data == 'each_profession':
                markup = await compose_inline_keyboard(prefix='each')
                await self.bot_aiogram.send_message(callback.message.chat.id, "Choose profession", reply_markup=markup, parse_mode='html')

            elif 'each' in callback.data:
                channel = callback.data.split('/')[1]
                # await hard_post(callback.message, channels=channel)
                await self.push_shorts_attempt_to_make_multi_function(
                    message=callback.message,
                    callback_data=callback.data,
                    hard_pushing=True,
                    hard_push_profession=channel
                )

            if callback.data == 'choose_one_channel':  # compose keyboard for each profession

                self.markup = await compose_inline_keyboard(prefix='//')
                await self.bot_aiogram.send_message(callback.message.chat.id, 'Choose the channel', reply_markup=self.markup)
                pass

            # if callback.data[2:] in self.valid_profession_list:
            #     logs.write_log(f"invite_bot_2: Callback: one_of_profession {callback.data}")
            #     if not self.current_session:
            #         self.current_session = await get_last_session()
            #     await WriteToDbMessages(
            #         client=self.client,
            #         bot_dict={'bot': self.bot_aiogram,
            #                   'chat_id': callback.message.chat.id}).get_last_and_tgpublic_shorts(
            #         current_session=self.current_session,
            #         shorts=False, fulls_all=True, one_profession=callback.data)  # get from profession's tables and put to tg channels
            #     pass

            if callback.data == 'show_info_last_records':
                """
                Show the parsing statistics
                """
                await self.bot_aiogram.send_message(callback.message.chat.id, 'Please wait a few seconds ...')
                message_for_send = await self.show_statistics()
                await self.bot_aiogram.send_message(callback.message.chat.id, message_for_send, parse_mode='html',
                                                    reply_markup=self.markup)

        @self.dp.message_handler(content_types=['text'])
        async def messages(message):

            # global all_participant, file_name, marker_code, client
            channel_to_send = None
            user_to_send = []
            msg = None
            if self.peerchannel:
                data = await self.client.get_entity(message.text)
                await self.bot_aiogram.send_message(message.chat.id, str(data))
                self.peerchannel = False

            if self.feature == 'one_day_statistics':
                one_day_statistics = f'<b>Statistics {message.text}</b>\n\n'
                counter = 0
                try:
                    for prof in self.valid_profession_list:
                        response = self.db.get_all_from_db(
                            table_name=prof,
                            param=f"""WHERE DATE(created_at)='{message.text}'"""
                        )
                        one_day_statistics += f"{prof}: {len(response)} vacancies\n"
                        counter += len(response)
                    one_day_statistics += f"____________\nSumm: {counter}"
                    await self.bot_aiogram.send_message(message.chat.id, one_day_statistics, parse_mode='html')
                    self.feature = ''

                except Exception as e:
                    await self.bot_aiogram.send_message(message.chat.id, 'Type the correct date')


            if self.marker:
                self.channel = message.text
                markup = InlineKeyboardMarkup()
                button1 = InlineKeyboardButton('group', callback_data='group')
                button2 = InlineKeyboardButton('personal', callback_data='personal')
                markup.row(button1, button2)
                await self.bot_aiogram.send_message(message.chat.id, 'group or personal', reply_markup=markup)

                # await invite_users(
                #     message=message,
                #     channel=message.text,
                #     all_participant=all_participant
                # )

                # await invite_set_users(
                #     message=message,
                #     channel=message.text,
                #     all_participant=all_participant
                # )
                self.marker = False

            else:
                if message.text == 'Get participants':

                    if message.text == 'Get participants':

                        if message.from_user.id in self.white_admin_list:
                            logs.write_log(f"invite_bot_2: content_types: Get participants")

                            await self.bot_aiogram.send_message(
                                message.chat.id,
                                'it is parsing subscribers...',
                                parse_mode='HTML')
                            await main(
                                report=self.report,
                                client=self.client,
                                bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id},
                                action='get_participants')
                        else:
                            await self.bot_aiogram.send_message(message.chat.id,
                                                           '🚀 Sorry, this options available only for admin')

                # if message.text == 'Get news from channels':
                #     await get_news(message=message)

                #----------------------- Listening channels at last --------------------------------------

                # if message.text == 'Invite people':
                #     await invite_people(message=message)

                # if message.text == 'Listen to channels':
                #
                #     # await bot.delete_message(message.chat.id, message.message_id)
                #     # await bot.send_message(message.chat.id, "Bot is listening TG channels and it will send notifications here")
                #     # ListenChats()
                #     # await client.run_until_disconnected()
                #     await get_subscribers_statistic(message)
                #     pass

                if message.text == 'Digest':

                    logs.write_log(f"invite_bot_2: content_types: Digest")

                    self.markup = InlineKeyboardMarkup(row_width=1)
                    but_show = InlineKeyboardButton('Unsorted vacancies (new vacancies)',
                                                    callback_data='show_info_last_records')
                    # but_send_digest_full = InlineKeyboardButton('Разлить fulls посл сессию',
                    #                                             callback_data='send_digest_full')
                    # but_send_digest_full_all = InlineKeyboardButton('Разлить fulls всё',
                    #                                                 callback_data='send_digest_full_all')
                    # but_separate_channel = InlineKeyboardButton('Залить в 1 канал',
                    #                                             callback_data='choose_one_channel')
                    but_do_by_admin = InlineKeyboardButton('ADMIN AREA👀✈️',
                                                                callback_data='go_by_admin')
                    but_stat_today = InlineKeyboardButton('One day statistics', callback_data='one_day_statistics')
                    but_excel_all_statistics = InlineKeyboardButton('Whole posted vacancies (EXCEL)', callback_data='consolidated_table')
                    but_hard_push = InlineKeyboardButton('HARD PUSHING 🧨🧨🧨', callback_data='hard_push')

                    # self.markup.row(but_show, but_send_digest_full)
                    # self.markup.row(but_send_digest_full_all, but_separate_channel)
                    self.markup.add(but_show)
                    self.markup.add(but_stat_today)
                    self.markup.add(but_excel_all_statistics)
                    self.markup.add(but_hard_push)
                    self.markup.add(but_do_by_admin)

                    time_start = await get_time_start()
                    await self.bot_aiogram.send_message(
                        message.chat.id,
                        f"Выберите действие со полученными и не распределенными вакансиями:", reply_markup=self.markup)
                    # show inline menu:
                    # - show numbers of last records from each table
                    # - download excel with last records, rewrite all changes and put messages in the channels
                    # - send digest to the channels without change
                    pass

                if message.text == 'Subscr.statistics':

                    logs.write_log(f"invite_bot_2: content_types: Subscr.statistics")

                    await get_subscribers_statistic(message)
                    # await send_excel(message)
                else:
                    pass
                    # await bot.send_message(message.chat.id, 'Отправьте файл')

        async def get_separate_time(time_in):

            logs.write_log(f"invite_bot_2: function: get_separate_time")

            start_time = {}
            start_time['year'] = time_in.strftime('%Y')
            start_time['month'] = time_in.strftime('%m')
            start_time['day'] = time_in.strftime('%d')
            start_time['hour'] = time_in.strftime('%H')
            start_time['minute'] = time_in.strftime('%M')
            start_time['sec'] = time_in.strftime('%S')
            return start_time

        @self.dp.message_handler(content_types=['document'])
        async def download_doc(message: types.Message):

            # global all_participant, file_name

            logs.write_log(f"invite_bot_2: function: content_type['document']")

            if self.client.is_connected():

                self.all_participant = []
                excel_data_df = None

                document_id = message.document.file_id
                file_info = await self.bot_aiogram.get_file(document_id)
                fi = file_info.file_path
                file_name = message.document.file_name
                urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{self.token}/{fi}', f'./{file_name}')

                try:
                    excel_data_df = pandas.read_excel(f'{file_name}', sheet_name='Sheet1')
                except Exception as e:
                    await self.bot_aiogram.send_message(message.chat.id, f'{e}')

                if 'id_participant' in excel_data_df.columns and 'access_hash' and 'status' in excel_data_df.columns:

                    excel_dict = {
                        'id_participant': excel_data_df['id_participant'].tolist(),
                        'access_hash': excel_data_df['access_hash'].tolist(),
                        'user': excel_data_df['username'].tolist(),
                        'status': excel_data_df['status'].tolist()
                    }
                    print(excel_dict)
                    self.participants_dict = excel_dict
                    n = 0
                    while n<len(excel_dict['id_participant']):
                        self.all_participant.append([int(excel_dict['id_participant'][n]), int(excel_dict['access_hash'][n]), excel_dict['user'][n], excel_dict['status'][n]])
                        n += 1

                    for iii in self.all_participant:
                        for jjj in iii:
                            print(jjj, type(jjj))

                    print('all_participant = ', self.all_participant)

                    await self.bot_aiogram.send_message(
                        message.chat.id,
                        f'Получен файл с {len(self.all_participant)} пользователями\n'
                        f'Введите url канала в формате https//t.me/<имя канала> без @:\n'
                    )

                    self.marker = True
                else:
                    await self.bot_aiogram.send_message(message.chat.id, 'В файле нет id_participant или access_hash')

            else:
                await self.bot_aiogram.send_message(message.chat.id, 'Для авторизации нажмите /start')

        async def invite_users(message, channel):
            logs.write_log(f"invite_bot_2: invite_users: if marker")
            msg = None
            channel_short_name = f"@{channel.split('/')[-1]}"
            # channel = message.text

        # receiving the channel entity
            try:
                channel = await self.client.get_entity(channel)
                channel_to_send = InputChannel(channel.id, channel.access_hash)  # был InputPeerChannel
            except Exception as e:
                # await bot_aiogram.send_message(message.chat.id, f'{telethon}\nУкажате канал в формате https//t.me/<имя канала> (без @)\n'
                #                                         f'Обратите внимание на то, что <b>и Вы и этот бот</b> в этом канале должны быть <b>администраторами</b>', parse_mode='html')
                await self.bot_aiogram.send_message(message.chat.id, 'Это сообщение вместо того, по которому была ошибка')
                return False

        #
            try:
                await self.bot_aiogram.send_message(message.chat.id, f'<b>{channel_short_name}</b>: Инвайт запущен',
                                               parse_mode='html')
                n = 0
                numbers_invite = 0
                numbers_failure = 0
                was_subscribe = 0

                self.participants_dict['status'] = []
                # ---------------------------- отправлять по одному инвайту---------------------------------

                print(f'\nLEN ALL_PARTICIPANTS IS {len(self.all_participant)}\n')

                sp = ShowProgress({'bot': self.bot_aiogram, 'chat_id': message.chat.id})
                current_step = 0
                length = len(self.all_participant)
                msg_2 = await self.bot_aiogram.send_message(message.chat.id, 'process 0%')

                for user in self.all_participant:
                    index = self.all_participant.index(user)

                    text = f"id:  {user[0]} hash {user[1]} username {user[2]} status {user[3]}\n"
                    await add_log_inviter(text)

                    print('id: ', user[0], 'hash', user[1], 'username', user[2], 'status', user[3])
                    id_user = int(user[0])
                    access_hash_user = int(user[1])
                    username = user[2]
                    status = user[3]

                    # -----------------------------------------------------try---------------------------------------------------------------
                    try:
                        user_channel_status = await self.bot_aiogram.get_chat_member(chat_id=channel_short_name,
                                                                                user_id=id_user)
                        if user_channel_status.status != types.ChatMemberStatus.LEFT:
                            if msg:
                                await msg.delete()
                                msg = None
                            # msg = await bot_aiogram.send_message(message.chat.id, f'<b>{channel_short_name}</b>: пользователь с id={id_user} уже подписан', parse_mode='html')
                            print('Пользователь уже подписан')
                            text = f"Пользователь уже подписан\n"
                            await add_log_inviter(text)
                            self.all_participant[index][-1] = 'user already subscribed'

                            # self.participants_dict['status'].append('уже подписан')
                            was_subscribe += 1
                            user_exists = True
                        else:
                            print('Пользователь новый')
                            text = f"Пользователь новый\n"
                            await add_log_inviter(text)

                            user_exists = False

                    except Exception as e:
                        print('Пользователь новый')
                        text = f"Пользователь новый\n"
                        await add_log_inviter(text)

                        user_exists = False
                        if msg:
                            await msg.delete()
                            msg = None
                        # await bot_aiogram.send_message(message.chat.id, f"813: {str(telethon)}")
                        print(f"#813: if username != None {str(e)}")
                        text = f"#813: if username != None {str(e)}\n"
                        await add_log_inviter(text)

                    # ----------------------------------------------------end---------------------------------------------------------------
                    if not user_exists and status.lower() == 'new':
                        if username != 'None':
                            # -----------------------------------------------------try---------------------------------------------------------------
                            try:
                                user_to_send = [await self.client.get_input_entity(username)]
                            except Exception as e:
                                try:
                                    await asyncio.sleep(5)
                                    user_to_send = [await self.client.get_entity(username)]
                                except Exception as e:
                                    try:
                                        user_to_send = [InputUser(id_user, access_hash_user)]
                                    except Exception as e:
                                        # await bot_aiogram.send_message(message.chat.id, f"#824: if username != None {str(telethon)}")
                                        print(f"#824: if username != None {str(e)}")
                                        text = f"#824: if username != None {str(e)}\n"
                                        await add_log_inviter(text)

                        # ----------------------------------------------------end---------------------------------------------------------------
                        else:
                            # -----------------------------------------------------try---------------------------------------------------------------
                            try:
                                user_to_send = [InputUser(id_user, access_hash_user)]  # (PeerUser(id_user))
                            except Exception as e:
                                # await bot_aiogram.send_message(message.chat.id, f"#831: if username = None {str(telethon)}")
                                print(f"#831: if username = None {str(e)}")
                                text = f"#831: if username = None {str(e)}\n"
                                await add_log_inviter(text)

                        # ----------------------------------------------------end---------------------------------------------------------------
                        # -----------------------------------------------------try---------------------------------------------------------------
                        if msg:
                            await msg.delete()
                            msg = None
                        try:
                            # client.invoke(InviteToChannelRequest(channel_to_send,  [user_to_send]))
                            # await client(InviteToChannelRequest(channel_to_send, user_to_send))  #work!!!!!
                            await self.client(functions.channels.InviteToChannelRequest(channel_to_send, user_to_send))
                            # self.participants_dict['status'].append('инвайт прошел')
                            self.all_participant[index][-1] = 'invite +'


                            msg = await self.bot_aiogram.send_message(message.chat.id,
                                                                 f'<b>{channel_short_name}:</b> {user[0]} заинвайлся успешно\n'
                                                                 f'({numbers_invite + 1} инвайтов)',
                                                                 parse_mode='html')
                            print(f'{channel_short_name}: {user[0]} заинвайлся успешно\n'
                                  f'({numbers_invite + 1} инвайтов)\n\n')
                            text = f"{channel_short_name}: {user[0]} заинвайлся успешно\n({numbers_invite + 1} инвайтов)\n\n\n"
                            await add_log_inviter(text)
                            await asyncio.sleep(random.randrange(15, 20))

                            numbers_invite += 1

                        except Exception as e:
                            if re.findall(r'seconds is required (caused by InviteToChannelRequest)', str(e)) or \
                                    str(e) == "Too many requests (caused by InviteToChannelRequest)" or re.findall(
                                r'seconds is required', str(e)) or 'maximum number of users has been exceeded' in str(e):
                                await self.bot_aiogram.send_message(message.chat.id, str(e))
                                print(str(e))
                                break
                            else:
                                if msg:
                                    await msg.delete()
                                    msg = None
                                # -----------------------------------------------------try---------------------------------------------------------------
                                try:
                                    # await bot_aiogram.send_message(message.chat.id, f'<b>{channel_short_name}</b>: Для пользователя id={user[0]}\n{str(telethon)}', parse_mode='html')
                                    # self.participants_dict['status'].append(str(telethon))
                                    self.all_participant[index][-1] = str(e)

                                    print(f'{channel_short_name}: Для пользователя id={user[0]}\n{str(e)}\n\n')
                                    text = f"{channel_short_name}: Для пользователя id={user[0]}\n{str(e)}\n\n\n"
                                    await add_log_inviter(text)

                                except Exception:
                                    print('exception: #861')
                                    # await bot_aiogram.send_message(message.chat.id, "exception: #861")
                                # ----------------------------------------------------end---------------------------------------------------------------
                                numbers_failure += 1
                                msg = None
                        # ----------------------------------------------------end---------------------------------------------------------------
                        print('---------------------------------------------')
                        text = f'{datetime.now().strftime("%d-%m %H:%M:%S")}\n'
                        await add_log_inviter(text)

                        # n += 1
                        # if n >= 198:
                        #     if msg:
                        #         await msg.delete()
                        #         msg = None
                        #     msg = await bot_aiogram.send_message(message.chat.id,
                        #                                          f'<b>{channel_short_name}</b>: инвайт продолжится через 24 часа из-за ограничений Телеграм.\nНе завершайте сессию с ботом.\n'
                        #                                          f'Пока запущено ожидание по каналу {channel_short_name}, Вы можете отправить еще один файл (с другим названием) для инвайта в <b>ДРУГОЙ канал</b>',
                        #                                          parse_mode='html')
                        #     await asyncio.sleep(60 * 24 + 15)
                        #     n = 0

                    current_step += 1
                    await sp.show_the_progress(msg_2, current_step, length)

                id = []
                for i in range(0, len(self.all_participant)):
                    id.append(self.all_participant[i][0])

                df = pd.DataFrame(
                    {
                        'id_participant': [str(self.all_participant[i][0]) for i in range(0, len(self.all_participant))],
                        'access_hash': [str(self.all_participant[i][1]) for i in range(0, len(self.all_participant))],
                        'username': [self.all_participant[i][2] for i in range(0, len(self.all_participant))],
                        'status': [self.all_participant[i][3] for i in range(0, len(self.all_participant))],
                    }
                )
                try:
                    df.to_excel(f'./excel/excel/invite_report.xlsx', sheet_name='Sheet1')
                    print('got it')
                    await self.send_file_to_user(message, f'./excel/excel/invite_report.xlsx')
                except Exception as e:
                    await self.bot_aiogram.send_message(message.chat.id, f"Something is wrong: {str(e)}")
                    print(f"Something is wrong: {str(e)}")
                # ---------------------------- end отправлять по одному инвайту---------------------------------

                if msg:
                    await msg.delete()
                    msg = None
                await self.bot_aiogram.send_message(message.chat.id,
                                               f'<b>{channel_short_name}</b>: {numbers_invite} пользователей заинвайтились, проверьте в канале\n'
                                               f'{numbers_failure} не заинватились в канал\n'
                                               f'{was_subscribe} были уже подписаны на канал', parse_mode='html')
                print(
                    f'886: {channel_short_name}: {numbers_invite} пользователей заинвайтились, проверьте в канале\n'
                    f'{numbers_failure} не заинватились в канал\n'
                    f'{was_subscribe} были уже подписаны на канал')
                self.all_participant = []
                self.marker = False
                os.remove(f'{file_name}')
            except Exception as e:
                if msg:
                    await msg.delete()
                    msg = None
                # await bot_aiogram.send_message(message.chat.id, f'bottom: #897: {telethon}')
                print(f'bottom: #897: {e}')

                await self.send_file_to_user(message, 'inviter_log.txt')

        async def invite_set_users(message, channel):
            logs.write_log(f"invite_bot_2: invite_set_users")
            msg = None
            channel_short_name = f"@{channel.split('/')[-1]}"

            # receiving the channel entity
            try:
                channel = await self.client.get_entity(channel)
                channel_to_send = InputChannel(channel.id, channel.access_hash)  # был InputPeerChannel
            except Exception as e:
                # await bot_aiogram.send_message(message.chat.id, f'{telethon}\nУкажате канал в формате https//t.me/<имя канала> (без @)\n'
                #                                         f'Обратите внимание на то, что <b>и Вы и этот бот</b> в этом канале должны быть <b>администраторами</b>', parse_mode='html')
                await self.bot_aiogram.send_message(message.chat.id, 'Это сообщение вместо того, по которому была ошибка')
                return False

            #
            await self.bot_aiogram.send_message(message.chat.id, f'<b>{channel_short_name}</b>: Инвайт запущен',
                                           parse_mode='html')

            while len(self.all_participant) > 0:
                if len(self.all_participant) > 50:
                    part_of_all_participant = self.all_participant
                    self.all_participant = self.all_participant[50:]
                else:
                    part_of_all_participant = self.all_participant
                    self.all_participant = []
                user_to_send = []
                for i in range(0, len(part_of_all_participant)):
                    user_to_send.append(InputUser(part_of_all_participant[i][0], part_of_all_participant[i][1]))

                try:
                    response_from_invite = await self.client(functions.channels.InviteToChannelRequest(channel_to_send, user_to_send))
                    print('!!!!!!!!!!!!!!! success!\n', response_from_invite)
                except Exception as e:
                    print('No invite: ', e)

                if len(self.all_participant)>0:
                    await self.bot_aiogram.send_message(message.chat.id, 'set has done')
                    await asyncio.sleep(15, 25)

            await self.bot_aiogram.send_message(message.chat.id, 'inviting has done, check please inside you channel')

        async def check_customer(message, id_customer):

            logs.write_log(f"invite_bot_2: unction: check_customer")

            files = os.listdir('./')
            sessions = filter(lambda x: x.endswith('.session'), files)

            for session in sessions:
                print(session)
                if session == f'{id_customer}.session':
                    print('session exists')
                    return True

            await Form.api_id.set()
            await self.bot_aiogram.send_message(message.chat.id, "Введите api_id (отменить /cancel)")


        async def get_time_start():
            time_start = None
            if self.start_time_scraping_channels:
                if self.start_time_scraping_channels <= self.start_time_listen_channels:
                    time_start = await get_separate_time(self.start_time_scraping_channels)
                else:
                    time_start = await get_separate_time(self.start_time_listen_channels)
            else:
                time_start = await get_separate_time(self.start_time_listen_channels)
            return time_start

        async def get_subscribers_statistic(message):

            logs.write_log(f"invite_bot_2: function: get_subscribers_statistic")

            id_user_list = []
            access_hash_list = []
            username_list = []
            first_name_list = []
            last_name_list = []
            join_time_list = []
            is_bot_list = []
            mutual_contact_list = []
            is_admin_list = []
            channel_list = []

            msg = await self.bot_aiogram.send_message(message.chat.id, f'Followers statistics')

            for channel in self.valid_profession_list:
                self.marker = False
                channel_name = channel
                channel = config['My_channels'][f'{channel}_channel']

                offset_user = 0  # номер участника, с которого начинается считывание
                limit_user = 100  # максимальное число записей, передаваемых за один раз

                all_participants = []  # список всех участников канала
                filter_user = ChannelParticipantsSearch('')

                # channel = channel[4:]
                try:
                    channel = await self.client.get_input_entity(int(channel))
                    self.marker = True
                except:
                    try:
                        channel = channel[4:]
                        channel = await self.client.get_input_entity(int(channel))
                        self.marker = True
                    except Exception as e:
                        await self.bot_aiogram.send_message(message.chat.id, f'The error with channel {channel}: {str(e)}')
                        time.sleep(random.randrange(3, 6))

                if self.marker:
                    participants = await self.client(GetParticipantsRequest(
                        channel, filter_user, offset_user, limit_user, hash=0))

                    # for participant in participants.users:
                    #     print(participant)
                    users = {}
                    users['users'] = [i for i in participants.users]
                    users['date'] = [i for i in participants.participants]


                    for i in range(0, len(users['users'])):
                        id_user = users['users'][i].id
                        access_hash = users['users'][i].access_hash
                        username = users['users'][i].username
                        first_name = users['users'][i].first_name
                        last_name = users['users'][i].last_name
                        try:
                            join_time = users['date'][i].date
                        except Exception as e:
                            join_time = None

                        try:
                            is_bot = users['users'][i].bot
                        except Exception:
                            is_bot = None

                        try:
                            mutual_contact = users['users'][i].mutual_contact
                        except Exception:
                            mutual_contact = None

                        is_admin = False
                        try:
                            if users['date'][i].admin_rigths:
                                is_admin = True
                        except Exception:
                            pass

                        print(f"\n{i}")
                        print('id = ', id_user)
                        print('access_hash = ', access_hash)
                        print('username = ', username)
                        print('first_name = ', first_name)
                        print('last_name = ', last_name)
                        print('join_time = ', join_time)
                        print('is_bot = ', is_bot)
                        print('mutual_contact = ', mutual_contact)
                        print('is_admin = ', is_admin)

                        channel_list.append(channel_name)
                        id_user_list.append(id_user)
                        access_hash_list.append(access_hash)
                        username_list.append(username)
                        first_name_list.append(first_name)
                        last_name_list.append(last_name)
                        if join_time:
                            join_time = join_time.strftime('%d-%m-%Y %H:%M:%S')
                        join_time_list.append(join_time)
                        is_bot_list.append(is_bot)
                        mutual_contact_list.append(mutual_contact)
                        is_admin_list.append(is_admin)



                    msg = await self.bot_aiogram.edit_message_text(f'{msg.text}\nThere are <b>{i}</b> subscribers in <b>{channel_name}</b>...\n', msg.chat.id, msg.message_id, parse_mode='html')

                    print(f'\nsleep...')
                    time.sleep(random.randrange(3, 6))

            # compose dict for push to DB
            channel_statistic_dict = {
                'channel': channel_list,
                'id_user': id_user_list,
                'access_hash': access_hash_list,
                'username': username_list,
                'first_name': first_name_list,
                'last_name': last_name_list,
                'join_time': join_time_list,
                'is_bot': is_bot_list,
                'mutual_contact': mutual_contact_list,
            }

            # push to DB
            msg = await self.bot_aiogram.edit_message_text(
                f'{msg.text}\n\nAll getting statistics is writting to bd, please wait ... ', msg.chat.id,
                msg.message_id, parse_mode='html')

            db = self.db
            db.push_followers_statistics(channel_statistic_dict)

            df = pd.DataFrame(
                {
                'channel': channel_list,
                'id_user': id_user_list,
                'access_hash': access_hash_list,
                'username': username_list,
                'first_name': first_name_list,
                'last_name': last_name_list,
                'join_time': join_time_list,
                'is_bot': is_bot_list,
                'mutual_contact': mutual_contact_list,
                'is_admin': is_admin_list,
                }
            )

            df.to_excel(f'./excel/excel/followers_statistics.xlsx', sheet_name='Sheet1')
            print(f'\nExcel was writting')

            await self.send_file_to_user(message, path='excel/excel/excel/followers_statistics.xlsx')

        async def refresh_pattern(path):
            pattern = "pattern = " + "{\n"
            response = self.db.get_all_from_db('pattern', without_sort=True)
            for i in response:
                print(i)
                pattern += f'{i}\n'
            with open(path, mode='w', encoding='utf-8') as f:
                f.write(pattern)
            pass

        async def compose_inline_keyboard(prefix=None):
            markup = InlineKeyboardMarkup(row_width=4)

            button_dict = {}
            for item in self.valid_profession_list:
                button_dict[item] = InlineKeyboardButton(item, callback_data=f"{prefix}/{item}")

            # button_marketing = InlineKeyboardButton('marketing', callback_data=f'{prefix}/marketing')
            # button_ba = InlineKeyboardButton('ba', callback_data=f'{prefix}/ba')
            # button_game = InlineKeyboardButton('game', callback_data=f'{prefix}/game')
            # button_product = InlineKeyboardButton('product', callback_data=f'{prefix}/product')
            # button_mobile = InlineKeyboardButton('mobile', callback_data=f'{prefix}/mobile')
            # button_pm = InlineKeyboardButton('pm', callback_data=f'{prefix}/pm')
            # button_sales_manager = InlineKeyboardButton('sales_manager', callback_data=f'{prefix}/sales_manager')
            # button_designer = InlineKeyboardButton('designer', callback_data=f'{prefix}/designer')
            # button_devops = InlineKeyboardButton('devops', callback_data=f'{prefix}/devops')
            # button_hr = InlineKeyboardButton('hr', callback_data=f'{prefix}/hr')
            # button_backend = InlineKeyboardButton('backend', callback_data=f'{prefix}/backend')
            # button_frontend = InlineKeyboardButton('frontend', callback_data=f'{prefix}/frontend')
            # button_qa = InlineKeyboardButton('qa', callback_data=f'{prefix}/qa')
            # button_junior = InlineKeyboardButton('junior', callback_data=f'{prefix}/junior')
            # button_analyst = InlineKeyboardButton('analyst', callback_data=f'{prefix}/analyst')
            #
            markup.row(button_dict['designer'], button_dict['game'], button_dict['product'])
            markup.row(button_dict['mobile'], button_dict['pm'], button_dict['sales_manager'], button_dict['analyst'])
            markup.row(button_dict['frontend'], button_dict['marketing'], button_dict['devops'], button_dict['hr'])
            markup.row(button_dict['backend'], button_dict['qa'], button_dict['junior'])
            return markup

        # ------------------- end -------------------------

        async def get_excel_tags_from_admin(message):
            sp = ShowProgress(
                bot_dict={
                    'bot': self.bot_aiogram,
                    'chat_id': message.chat.id
                }
            )
            excel_list = {}
            excel_list['title'] = []
            excel_list['body'] = []
            excel_list['profession'] = []
            excel_list['tag'] = []
            excel_list['anti_tag'] = []
            excel_list['vacancy'] = []
            excel_list['sub'] = []
            n = 0
            for i in [variable.admin_database,]:
                response = self.db.get_all_from_db(
                    table_name=f'{i}',
                    param="""WHERE profession <> 'no_sort'""",
                    field=variable.admin_table_fields,
                    without_sort=True
                )

                await self.bot_aiogram.send_message(message.chat.id, f'There are {len(response)} records from {i}\nPlease wait...')
                msg = await self.bot_aiogram.send_message(message.chat.id, 'progress 0%')
                n=0
                length=len(response)
                for vacancy in response:
                    vacancy_dict = await helper.to_dict_from_admin_response(
                        response=vacancy,
                        fields=variable.admin_table_fields
                    )
                    title = vacancy_dict['title']
                    body = vacancy_dict['body']
                    vac = vacancy_dict['vacancy']
                    full_tags = vacancy_dict['full_tags']
                    full_anti_tags = vacancy_dict['full_anti_tags']
                    profession = vacancy_dict['profession']
                    sub = vacancy_dict['sub']

                    # response_from_filter = VacancyFilter().sort_profession(
                    #     title=title,
                    #     body=body,
                    #     check_vacancy=False,
                    #     check_contacts=False,
                    #     check_profession=False,
                    #     get_params=True
                    # )
                    # # profession = response_from_filter['profession']
                    # params = response_from_filter['params']

                    if vac:
                        excel_list['vacancy'].append(vac)
                    # elif params['vacancy']:
                    #     excel_list['vacancy'].append(params['vacancy'])
                    else:
                        excel_list['vacancy'].append('-')
                    excel_list['title'].append(title)
                    excel_list['body'].append(body)
                    excel_list['profession'].append(profession)
                    excel_list['tag'].append(full_tags)
                    excel_list['anti_tag'].append(full_anti_tags)
                    excel_list['sub'].append(sub)
                    n += 1
                    print(f'step {n} passed')
                    msg = await sp.show_the_progress(
                        message=msg,
                        current_number=n,
                        end_number = length
                    )
            df = pd.DataFrame(
                {
                    'title': excel_list['title'],
                    'body': excel_list['body'],
                    'vacancy': excel_list['vacancy'],
                    'profession': excel_list['profession'],
                    'sub': excel_list['sub'],
                    'tag': excel_list['tag'],
                    'anti_tag': excel_list['anti_tag']
                }
            )

            df.to_excel(f'./excel/excel/statistics.xlsx', sheet_name='Sheet1')
            print('got it')
            await self.send_file_to_user(message, f'excel/excel/statistics.xlsx')

        async def delete_since(tables_list=None, ids_list=None, param=None):
            """
            delete records since time in params in tables in list[]
            """
            """
            DATE(created_at) > '2022-09-24'
            """
            if not tables_list:
                tables_list = ['backend', 'frontend', 'devops', 'pm', 'product', 'designer', 'analyst', 'mobile', 'qa',
                               'hr', 'game',
                               'ba', 'marketing', 'junior', 'sales_manager', 'no_sort', 'admin_last_session']
            for i in tables_list:
                if not ids_list:
                    self.db.delete_data(table_name=i, param=param)
                else:
                    for id in ids_list:
                        self.db.delete_data(table_name=i, param=f"WHERE id={id}")
                        print(f'Was deleted id={id} from {i}')

        async def output_consolidated_table(message):
            dates = []

            info_dict: dict
            info_dict = {}
            for i in self.valid_profession_list:
                info_dict[i] = []
                info_dict['date'] = []
            db = self.db
            date_now = datetime.now()
            start_data = datetime(2022, 9, 15, 0, 0, 0, 0)
            delta = int(str(date_now - start_data).split(' ', 1)[0])
            for date_offset in range(0, delta):
                date = date_now-timedelta(days=date_offset)
                print(date)
                date = date.strftime('%Y-%m-%d')
                info_dict['date'].append(date)
                for table in self.valid_profession_list:
                    response = db.get_all_from_db(
                        table_name=table,
                        param=f"""WHERE DATE(created_at)='{date}'"""
                    )
                    info_dict[table].append(len(response))
            # compose table
            try:
                df = pd.DataFrame(info_dict)
                path = f'./excel/excel/consolidated_table.xlsx'
                df.to_excel(path, sheet_name='Sheet1')
                print('got it')
                await self.send_file_to_user(message, path)

            except Exception as e:
                print(e)

        async def add_log_inviter(text):
            with open('inviter_log.txt', 'a+') as file:
                file.write(text)

        async def print_log(text):
            print(f"{datetime.now().strftime('%H:%M:%S')}:\n{text}")

        async def refresh(message, save_changes=False):
            deleted_vacancy = 0
            transfer_vacancy = 0
            profession = {}
            title_list = []
            body_list = []
            old_prof_list = []
            new_prof_list = []
            tag_list = []
            anti_tag = []
            sub = []

            await self.bot_aiogram.send_message(message.chat.id, 'It will rewrite the professions in all vacancies through the new filter logic\nPlease wait few seconds for start')
            fields = variable.admin_table_fields
            response = self.db.get_all_from_db(
                table_name=variable.admin_database,
                param="""WHERE profession<>'no_sort'""",
                field=fields
            )
            await self.bot_aiogram.send_message(message.chat.id, f"{len(response)} vacancies founded")
            show = ShowProgress(bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id})
            n=0
            length = len(response)
            msg = await self.bot_aiogram.send_message(message.chat.id, 'progress 0%')

            for one_vacancy in response:
                one_vacancy_dict = await helper.to_dict_from_admin_response(
                    response=one_vacancy,
                    fields=fields
                )

                if 'https://t.me' in one_vacancy_dict['chat_name']:
                    profession = VacancyFilter(report=self.report).sort_profession(
                        one_vacancy_dict['title'],
                        one_vacancy_dict['body'],
                        get_params=False
                    )
                else:
                    profession = VacancyFilter(report=self.report).sort_profession(
                        one_vacancy_dict['title'],
                        one_vacancy_dict['body'],
                        check_contacts=False,
                        check_vacancy=True,
                        check_vacancy_only_mex=True,
                        # get_params=False
                    )

                print('new2', profession['profession']['profession'])
                print(f"{profession['profession']['tag']}")
                print(f"{profession['profession']['anti_tag']}")
                print('--------------------------')

                if profession['profession']['profession'] == 'no_sort':
                    pass
                    transfer_completes=self.db.transfer_vacancy(
                        table_from=variable.admin_database,
                        table_to=variable.archive_database,
                        response_from_db=one_vacancy
                    )
                    if transfer_completes:
                        self.db.delete_data(
                            table_name=variable.admin_database,
                            param=f"Where id={int(one_vacancy_dict['id'])}"
                        )
                        transfer_vacancy += 1

                elif not profession['profession']['profession']:
                    self.db.delete_data(
                        table_name=variable.admin_database,
                        param=f"Where id={int(one_vacancy_dict['id'])}"
                    )
                    deleted_vacancy += 1
                else:
                    # checking in db and compose profession
                    profession_str = ''
                    table_list = profession['profession']['profession'].copy()
                    for table in table_list:
                        not_exists = self.db.check_exists_message_by_link_or_url(
                            vacancy_url=one_vacancy_dict['vacancy_url'],
                            table_list=[table]
                        )

                        if not_exists:
                            not_exists = self.db.check_exists_message_by_link_or_url(
                                title=one_vacancy_dict['title'],
                                body=one_vacancy_dict['body'],
                                table_list=table_list
                            )

                        if not_exists:
                            profession_str += f"{table}, "
                    profession_str = profession_str[:-2]

                    print('title = ', one_vacancy_dict['title'])
                    print(f"old prof [{one_vacancy_dict['profession']}]")
                    print(f'new prof [{profession_str}]')
                    print(f"subs {profession['profession']['sub']}")

                    # change the old values to news
                    one_vacancy_dict['profession'] = profession_str
                    one_vacancy_dict['sub'] = helper.compose_to_str_from_list(profession['profession']['sub'])
                    one_vacancy_dict['level'] = profession['profession']['level']
                    one_vacancy_dict['tags'] = helper.get_tags(profession['profession'])
                    one_vacancy_dict['anti_tags'] = profession['profession']['anti_tag'].replace("'", "")
                    one_vacancy_dict['full_tags'] = profession['profession']['anti_tag'].replace("'", "")

                    title_list.append(one_vacancy_dict['title'])
                    body_list.append(one_vacancy_dict['body'])
                    old_prof_list.append(one_vacancy_dict['profession'])
                    new_prof_list.append(profession_str)
                    sub.append(profession['profession']['sub'])
                    tag_list.append(profession['profession']['tag'])
                    anti_tag.append(profession['profession']['anti_tag'])
                    print('\n________________\n')

                    if save_changes:
                        query = ''
                        for field in fields.split(', '):
                            if one_vacancy_dict[field]:
                                if field not in ['id', 'chat_name']:
                                    query  += f"{field}='{one_vacancy_dict[field]}', "
                        if query:
                            query = f"UPDATE {variable.admin_database} SET " + query
                            query = query[:-2] + f" WHERE id={one_vacancy_dict['id']}"
                            # print(query)

                            self.db.run_free_request(
                                request=query,
                                output_text='updated successfully\n___________\n\n'
                            )
                        else:
                            print('no changes')
                n += 1
                await show.show_the_progress(msg, n, length)

            df = pd.DataFrame(
                {
                    'title': title_list,
                    'body': body_list,
                    'old_prof': old_prof_list,
                    'new_prof': new_prof_list,
                    'sub': sub,
                    'tag': tag_list,
                    'anti_tag': anti_tag
                }
            )
            path = 'excel/excel/professions_rewrite.xlsx'

            try:
                df.to_excel(path, sheet_name='Sheet1')
                await self.send_file_to_user(message, path, caption='You win! Take the logs for checking how it was and how it is')
                print('got it')
            except:
                try:
                    await self.send_file_to_user(message, './other_operations/pr.txt', caption="It did not send excel so take txt logs")
                except:
                    await self.bot_aiogram.send_message(message.chat.id, f'Can\'t send the report file')

            await self.bot_aiogram.send_message(message.chat.id, f'Done\n'
                                                                 f'transfer vacancies (no_sort): {transfer_vacancy}\n'
                                                                 f'deleted vacancies (not vacancy): {deleted_vacancy}')

        async def search_vacancy_in_db(title, body):
            f = self.valid_profession_list
            f.append('admin_last_session')
            matches_list = {}
            for i in f:
                print(f'searching in {i}')
                response = self.db.get_all_from_db(
                    table_name=i,
                    param=f"""WHERE title LIKE '%{title}%' AND body LIKE '%{body}%'"""
                )
                if response:
                    matches_list[i] = len(response)
            return matches_list

        async def get_news(message):
            tables = self.db.get_information_about_tables_and_fields(only_tables=True)
            if "parser_at_work" not in tables:
                self.db.create_table_common(
                    field_list=["parser_at_work BOOLEAN"],
                    table_name="parser_at_work"
                )
                self.db.push_to_db_common(
                    table_name='parser_at_work',
                    fields_values_dict={"parser_at_work": False}
                )
            self.parser_at_work = self.db.get_all_from_db(
                table_name="parser_at_work",
                param="WHERE id=1",
                without_sort=True,
            )[0][1]

            if not self.parser_at_work:
                self.db.push_to_db_common(
                    table_name='parser_at_work',
                    fields_values_dict={"parser_at_work": True},
                    params="WHERE id=1"
                )
                # ----------------- make the current session and write it in DB ----------------------
                await send_log_txt(text='', write_mode='w')
                self.current_session = datetime.now().strftime("%Y%m%d%H%M%S")
                self.db.write_current_session(self.current_session)
                await self.bot_aiogram.send_message(message.chat.id, f'Session is {self.current_session}')
                await asyncio.sleep(1)
                self.start_time_scraping_channels = datetime.now()
                print('time_start = ', self.start_time_scraping_channels)
                await asyncio.sleep(1)

                # # -----------------------parsing telegram channels -------------------------------------
                bot_dict = {'bot': self.bot_aiogram, 'chat_id': message.chat.id}
                # self.task = asyncio.create_task(main(report=self.report, client=self.client, bot_dict=bot_dict))
                # await main(report=self.report, client=self.client, bot_dict=bot_dict)
                # await self.report.add_to_excel(report_type='parsing')

                sites_parser = SitesParser(client=self.client, bot_dict=bot_dict, report=self.report)
                # self.task = asyncio.create_task(sites_parser.call_sites())
                await sites_parser.call_sites()
                self.db.push_to_db_common(
                    table_name='parser_at_work',
                    fields_values_dict={"parser_at_work": False},
                    params="WHERE id=1"
                )
                await self.send_file_to_user(
                    message=message,
                    path=variable.flood_control_logs_path,
                    caption="take the exception logs"
                )
                await self.send_file_to_user(
                    message=message,
                    path=variable.path_log_check_profession,
                    caption="take the profession logs"
                )
            else:
                await self.bot_aiogram.send_message(message.chat.id, "Sorry, parser at work. Request a stop from developers")





        async def debug_function():
            response = self.db.get_all_from_db(
                table_name='admin_last_session',
                param="Where profession <> 'no_sort'",
                field='title, body'
            )

            for vacancy in response:
                title = vacancy[0]
                body = vacancy[1]
                profession_dict = VacancyFilter().sort_profession(
                    title,
                    body
                )
                sub_str = ''
                if list(profession_dict['profession']['profession']) != ['no_sort']:
                    sub_str = await helper.compose_to_str_from_list(profession_dict['profession']['sub'])
                    print('------sub_str--------')
                    print(sub_str)
                else:
                    sub_str = ''
                    print(list(profession_dict['profession']['profession']))
                    print('NO_SORT')

                if sub_str:
                    sub_list = await helper.decompose_from_str_to_list(sub_str)
                    print('------sub_list--------')
                    for i in sub_list:
                        print(i, sub_list[i])
                pass

        async def get_remove_doubles(message):
            msg = await self.bot_aiogram.send_message(message.chat.id, 'The double checking from admin db table...')
            answer = self.db.check_doubles()
            await msg.edit_text(f"{msg.text}\nDouble quantity: {answer['doubles']}\nfrom {answer['vacancy_numbers']}")

            # msg = await self.bot_aiogram.send_message(message.chat.id, 'The double checking between professional tables...')
            # answer = self.db.check_double_in_professions()
            # await msg.edit_text(f"{msg.text}\nDouble quantity: {answer['doubles']}\nfrom {answer['vacancy_numbers']}")

        async def remove_completed_professions(message):
            answer_dict = self.db.remove_completed_professions()
            await self.bot_aiogram.send_message(
                message.chat.id,
                f"messages: {answer_dict['messages']}\nremoved to archive: {answer_dict['deleted']}\nchanged profession: {answer_dict['change_profession']}"
            )

        async def clear_db_table(profession, quantity_leave):
            updated = 0
            removed = 0
            response = self.db.get_all_from_db(
                table_name='admin_last_session',
                param=f"WHERE profession LIKE '%{profession}, %' OR profession LIKE '%, {profession}%' OR profession='{profession}'",
                without_sort=False,
                field='profession, id'
            )
            pass

            end_iterations = len(response)-int(quantity_leave)
            for index in range(0, end_iterations):
                prof = helper.string_to_list(
                    text=response[index][0],
                    separator=', '
                )
                prof.remove(profession)
                if prof:
                    new_prof = helper.list_to_string(
                        raw_list=prof,
                        separator=', '
                    )
                    self.db.update_table(
                        table_name='admin_last_session',
                        param=f"WHERE id={response[index][1]}",
                        field='profession',
                        value=new_prof
                    )
                    updated += 1
                else:
                    await self.transfer_vacancy_from_to_table(
                        id_admin_last_session_table=response[index][1],
                    )
                    self.db.delete_data(
                        table_name=variable.admin_database,
                        param=f"WHERE id={response[index][1]}"
                    )
                    removed += 1

        async def compose_excel_dict(key, value, key_list, excel_dict):
            for i in key_list:
                if i == key:
                    excel_dict[i] = value
                else:
                    excel_dict[i] = ''

        async def schedule(message):
            while True:
                # thr1 = threading.Thread(target=get_news, args=(message))
                # thr1.start()
                await get_news(message=message)
                await self.bot_aiogram.send_message(message.chat.id, 'Pause 10 minutes')
                print('Pause 10 minutes')
                await asyncio.sleep(10*60)
                await self.bot_aiogram.send_message(message.chat.id, 'Next loop has been started')

        async def invite_people(message):
            id_customer = message.from_user.id
            customer = await check_customer(message, id_customer)
            if customer:
                get_customer_from_db = self.db.get_all_from_db(table_name='users',
                                                                                param=f"WHERE id_user='{id_customer}'",
                                                                                without_sort=True)
                if not get_customer_from_db:
                    await Form.api_id.set()
                    return await self.bot_aiogram.send_message(message.chat.id, "Введите api_id (отменить /cancel)")

                self.current_customer = get_customer_from_db[0]
                self.api_id = int(self.current_customer[2])
                self.api_hash = self.current_customer[3]
                self.phone_number = self.current_customer[4]
                self.password = self.current_customer[5]
                try:
                    if self.client.is_connected():
                        await self.client.disconnect()
                except:
                    pass
                await connect_with_client(message, id_customer)

        async def restore_from_admin(message, numbers):
            vacancies_from_agregator = await self.get_tg_history_messages(
                message=message,
                channel=config['My_channels']['agregator_channel'],
                limit_msg=numbers
            )
            # vacancies_from_admin = await get_tg_history_messages(
            #     message=message,
            #     channel=config['My_channels']['admin_channel'],
            #     limit_msg=numbers
            #
            #
            positive = 0
            negative = 0
            response_dict = {}
            response_dict['admin_last_session'] = []
            response_dict['archive'] = []
            for vacancy in vacancies_from_agregator:
                print(vacancy['date'])
                vacancy = str(vacancy['message'])
                title = vacancy.split('\n')
                title = title[0].replace('Вакансия : ', '')

                body = vacancy.split('\n\n')
                body = "\n\n".join(body[1:])

                body = body.split('\n')
                body = "\n".join(body[1:])

                body = body.split('----')[0]

                title = self.db.clear_title_or_body(title)
                body = self.db.clear_title_or_body(body)

                prof = VacancyFilter().sort_profession(
                    title=title,
                    body=body,
                    check_contacts=False,
                    check_vacancy=False,
                    get_params=False
                )
                prof = prof['profession']['profession']

                if 'junior' in prof:
                    # print('title: ', title)
                    # print("body: ", body)
                    param = f"WHERE title LIKE '%{title.strip()}%' and body LIKE '%{body.strip()}%'"

                    response = self.db.get_all_from_db(
                        table_name=variable.admin_database,
                        param=param
                    )
                    if response:
                        response_dict['admin_last_session'].append(response[0][0])
                    response2 = self.db.get_all_from_db(
                        table_name='archive',
                        param=param
                    )
                    if response2:
                        response_dict['archive'].append(response2[0][0])

                    if response or response2:
                        print('response')
                        positive += 1
                    else:
                        param = f"WHERE vacancy LIKE '%{title.strip()}%' and body LIKE '%{body.strip()}%'"
                        response = self.db.get_all_from_db(
                            table_name=variable.admin_database,
                            param=param
                        )
                        if response:
                            response_dict['admin_last_session'].append(response[0][0])

                        response2 = self.db.get_all_from_db(
                            table_name='archive',
                            param=param
                        )
                        if response2:
                            response_dict['archive'].append(response2[0][0])
                        if response2 or response:
                            print('response')
                            positive += 1
                        else:
                            print('???')
                            negative += 1
                    print('----------------')
                    pass
                print(f'positive: {positive}\nnegative: {negative}')
            pass



            vacancies_from_admin = await self.get_tg_history_messages(
                message=message,
                channel=config["My_channels"]["admin_channel"],
                limit_msg=5
            )
            for vacancy in vacancies_from_admin:
                vacancy = str(vacancy['message'])
                title = vacancy.split('\n')
                title = title[0].replace('Вакансия : ', '')

                body = vacancy.split('\n\n')
                body = "\n\n".join(body[1:])

                body = body.split('\n')
                body = "\n".join(body[1:])

                body = body.split('----')[0]

                title = self.db.clear_title_or_body(title)
                body = self.db.clear_title_or_body(body)
                param = f"WHERE title LIKE '%{title.strip()}%' and body LIKE '%{body.strip()}%'"

                response = self.db.get_all_from_db(
                    table_name=variable.admin_database,
                    param=param
                )
                if response:
                    response_dict['admin_last_session'].append(response[0][0])
                response2 = self.db.get_all_from_db(
                    table_name='archive',
                    param=param
                )
                if response2:
                    response_dict['archive'].append(response2[0][0])

                if response or response2:
                    print('response')
                    positive += 1
                else:
                    param = f"WHERE vacancy LIKE '%{title.strip()}%' and body LIKE '%{body.strip()}%'"
                    response = self.db.get_all_from_db(
                        table_name=variable.admin_database,
                        param=param
                    )
                    if response:
                        response_dict['admin_last_session'].append(response[0][0])

                    response2 = self.db.get_all_from_db(
                        table_name='archive',
                        param=param
                    )
                    if response2:
                        response_dict['archive'].append(response2[0][0])
                    if response2 or response:
                        print('response')
                        positive += 1
                    else:
                        print('???')
                        negative += 1
                print(f'positive: {positive}\nnegative: {negative}')

                print('----------------')

            pass
            new_profession = ''
            for key in response_dict:
                if key == 'admin_last_session':
                    for id in response_dict[key]:
                        profession = self.db.get_all_from_db(
                            table_name='admin_last_session',
                            param=f"Where id={id}",
                            field='profession'
                        )[0][0]
                        if 'junior' not in profession:
                            new_profession = profession + ', junior'
                        self.db.update_table(
                            table_name='admin_last_session',
                            param=f"WHERE id={id}",
                            field='profession',
                            value=new_profession
                        )
                if key == 'archive':
                    new_profession = 'junior'
                    for id in response_dict[key]:
                        self.db.update_table(
                            table_name='archive',
                            param=f"WHERE id={id}",
                            field='profession',
                            value=new_profession
                        )
                        await self.transfer_vacancy_from_to_table(
                            id_admin_last_session_table=id,
                            table_from='archive',
                            table_to='admin_last_session'
                        )

        async def db_check_url_vacancy(message, url):
            table_list = variable.all_tables_for_vacancy_search
            url = url.strip()

            for pro in table_list:
                response = self.db.get_all_from_db(
                    table_name=pro,
                    field='title, body',
                    param=f"WHERE vacancy_url='{url}'"
                )
                if response:
                    await self.bot_aiogram.send_message(message.chat.id, f"😎 (+)Vacancy FOUND in {pro} table\n{response[0][0][0:40]}")
                    text = f"{response[0][0]}\n{response[0][1]}"
                    return text
            await self.bot_aiogram.send_message(message.chat.id, f"😱 (-)Vacancy NOT FOUND")
            return ''

        async def db_check_add_single_vacancy(message, url):
            table_list = variable.all_tables_for_vacancy_search
            url = url.strip()
            urls = [url]
            site_url = re.split(r'\/', url, maxsplit=3)
            domain = site_url[2]
            if domain == 'hh.ru':
                site_url[2] = 'spb.hh.ru'
                url_new = '/'.join(site_url)
                urls.append(url_new)
            for url in urls:
                for pro in table_list:
                    response = self.db.get_all_from_db(
                        table_name=pro,
                        field='title, body',
                        param=f"WHERE vacancy_url='{url}'"
                    )
                    if response:
                        await self.bot_aiogram.send_message(message.chat.id,
                                                            f"😎 (+)Vacancy FOUND in {pro} table\n{response[0][0][0:40]}")
                        text = f"{response[0][0]}\n{response[0][1]}"
                        return text

            await self.bot_aiogram.send_message(message.chat.id, f"😱 (-)URL NOT FOUND, PLEASE WAIT..")
            try:
                parser = parser_sites.get(domain)
                if parser:
                    parser_response = await parser(report=self.report, bot_dict={'bot': self.bot_aiogram,
                                                                      'chat_id': message.chat.id}).get_content_from_one_link(
                        url)
                    if not parser_response:
                        text = 'Vacancy found in db by title-body with another url'
                    else:
                        text = parser_response['response']['vacancy']
                    await self.bot_aiogram.send_message(message.chat.id, text)
                else:
                    await self.bot_aiogram.send_message(message.chat.id, f"NO PARSER for {domain}")

            except Exception as e:
                return e

        async def add_subs():
            self.db.append_columns(
                table_name_list=variable.valid_professions,
                column='sub VARCHAR (250)'
            )

        async def push_subs(message):
            progress = ShowProgress(
                bot_dict={
                    'bot': self.bot_aiogram,
                    'chat_id': message.chat.id
                }
            )
            sub_write_to_db = ''
            fields = 'id, title, body, profession'


            for table_name in variable.valid_professions:
                response_all_vacancies = self.db.get_all_from_db(
                    table_name=table_name,
                    field=fields
                )
                await self.bot_aiogram.send_message(message.chat.id, table_name)
                length = len(response_all_vacancies)
                n = 0
                msg = await self.bot_aiogram.send_message(message.chat.id, "progress 0%")
                await progress.reset_percent()

                if response_all_vacancies:
                    for vacancy in response_all_vacancies:
                        profession = VacancyFilter().sort_profession(
                            title=vacancy[1],
                            body=vacancy[2],
                            check_contacts=False,
                            check_profession=True,
                            check_vacancy=False,
                            get_params=False
                        )
                        subs = profession['profession']['sub']

                        if table_name in subs:
                            sub_write_to_db = f"{table_name}: {', '.join(subs[table_name])}"
                        else:
                            sub_write_to_db = f"{table_name}: "

                        self.db.update_table(
                            table_name=table_name,
                            param=f"WHERE id={vacancy[0]}",
                            field='sub',
                            value=sub_write_to_db
                        )
                        n += 1
                        await progress.show_the_progress(msg, n, length)

                else:
                    await self.bot_aiogram.send_message(message.chat.id, "Sorry, but it has not any response")

        async def get_vacancy_from_backend(message):
            button_next = InlineKeyboardButton(">>", callback_data='>>')
            button_previous = InlineKeyboardButton("<<", callback_data='<<')
            markup = InlineKeyboardMarkup()
            markup.row(button_previous, button_next)

            response_all_vacancies = self.db.get_all_from_db(
                table_name=self.show_vacancies['table'],
                field=variable.profession_table_fields,
                param=f"WHERE profession = '%{self.show_vacancies['profession']}%'"
            )
            if self.show_vacancies['offset'] > len(response_all_vacancies) -1:
                self.show_vacancies['offset'] = 0
            if self.show_vacancies['offset'] < 0:
                self.show_vacancies['offset'] =  len(response_all_vacancies) -1

            if response_all_vacancies:
                response_dict = await helper.to_dict_from_admin_response(
                    response=response_all_vacancies[self.show_vacancies['offset']],
                    fields=variable.profession_table_fields
                )
                if len(response_dict['body'])>100:
                    response_dict['body'] = response_dict['body'][:97] + '...'
                message_for_send = ''
                for key in response_dict:
                    message_for_send += f"<b>{key}</b>: {response_dict[key]}\n"

                if len(str(response_dict))<4096:
                    if not self.message:
                        self.message = await self.bot_aiogram.send_message(message.chat.id, message_for_send, reply_markup=markup, parse_mode='html', disable_web_page_preview=True)
                    else:
                        await self.message.edit_text(message_for_send, reply_markup=markup, parse_mode='html', disable_web_page_preview=True)

                else:
                    await self.bot_aiogram.send_message(message.chat.id, "Sorry, but it has not any response")
            else:
                await self.bot_aiogram.send_message(message.chat.id, "Sorry, but it has not any response")

        async def get_vacancy_names(message, profession):
            message_for_send = ''
            message_list = []
            responses = self.db.get_all_from_db(
                table_name = variable.admin_database,
                param=f"WHERE profession LIKE '%{profession}%'",
                field=variable.admin_table_fields
            )
            for response in responses:
                response_dict = await helper.to_dict_from_admin_response(
                    response=response,
                    fields=variable.admin_table_fields
                )
                if response_dict['vacancy']:
                    if len(f"{message_for_send}\n{response_dict['vacancy']}\n")<4096:
                        message_for_send += f"{response_dict['vacancy']}\n"
                    else:
                        message_list.append(message_for_send)
                        message_for_send = ''
                else:
                    if len(f"{message_for_send}\n{response_dict['title']}\n")<4096:
                        message_for_send += f"{response_dict['title']}\n"
                    else:
                        message_list.append(message_for_send)
                        message_for_send = ''
                    message_for_send += f"{response_dict['title']}\n"
            message_list.append(message_for_send)

            for i in message_list:
                await self.bot_aiogram.send_message(message.chat.id, i)
                await asyncio.sleep(random.randrange(1,3))

        async def add_tags_to_db(message):
            bot_dict = {'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            progress = ShowProgress(bot_dict)
            # add tags
            table_list = []
            table_list.extend(variable.valid_professions)
            table_list.append(variable.admin_database)
            table_list.append(variable.archive_database)

            # self.db.add_columns_to_tables(
            #     table_list=table_list,
            #     column_name_type="sended_to_agregator VARCHAR (30)"
            # )
            # self.db.add_columns_to_tables(
            #     table_list=table_list,
            #     column_name_type="tags VARCHAR (700)"
            # )
            # self.db.add_columns_to_tables(
            #     table_list=table_list,
            #     column_name_type="full_tags VARCHAR (700)"
            # )
            # self.db.add_columns_to_tables(
            #     table_list=table_list,
            #     column_name_type="full_anti_tags VARCHAR (700)"
            # )
            # self.db.add_columns_to_tables(
            #     table_list=table_list,
            #     column_name_type="short_session_numbers VARCHAR (300)"
            # )

            # get tags from sort_profession and write to each vacancy
            responses = self.db.get_all_from_db(
                table_name=variable.admin_database,
                param="WHERE profession <> 'no_sort'",
                field=variable.admin_table_fields
            )

            msg = await self.bot_aiogram.send_message(message.chat.id, f'Find {len(responses)}\nprogress 0%')
            self.percent = 0
            length = len(responses)
            n = 0
            for response in responses:
                response_dict = await helper.to_dict_from_admin_response(
                    response=response,
                    fields=variable.admin_table_fields
                )
                profession = VacancyFilter().sort_profession(
                    title=response_dict['title'], body=response_dict['body'],
                    check_contacts=False,
                    check_profession=True,
                    get_params=False

                )
                tags = helper.get_tags(profession['profession'])
                # response_dict = await helper.to_dict_from_admin_response(
                #     response=response,
                #     fields=variable.admin_table_fields
                # )
                # profession = VacancyFilter().sort_profession(
                #     title=response_dict['title'], body=response_dict['body'],
                #     check_contacts=False,
                #     check_profession=True,
                #     get_params=False
                #
                # )
                # tag_list = profession['profession']['tag'].split('\n')
                # anti_tag_list = profession['profession']['anti_tag'].split('\n')
                # tags = ''
                # tags_set = set()
                # for tag in tag_list:
                #     if tag:
                #         if 'vacancy' not in tag:
                #             tag_value = tag.split("'")[-2]
                #             tag_word = tag.split("=")[0][3:]
                #             if anti_tag_list:
                #                 for anti_tag in anti_tag_list:
                #                     if anti_tag:
                #                         anti_tag_word = anti_tag.split("=")[0][4:]
                #                         if anti_tag_word != tag_word:
                #                             tags_set.add(tag_value)
                #                     else:
                #                         tags_set.add(tag_value)
                # tags = ", ".join(tags_set)
                print('tags: ', tags)
                profession_name = ", ".join(profession['profession']['profession'])
                if tags:
                    self.db.update_table(
                        table_name=variable.admin_database,
                        param=f"WHERE id={response_dict['id']}",
                        field='tags',
                        value=tags,
                        output_text=f'{n}-tags was updated'
                    )
                if profession['profession']['tag'] :
                    self.db.update_table(
                        table_name=variable.admin_database,
                        param=f"WHERE id={response_dict['id']}",
                        field='full_tags',
                        value=profession['profession']['tag'].replace("'", ""),
                        output_text=f'{n}-full_tags was updated'
                    )
                if profession['profession']['anti_tag']:
                    self.db.update_table(
                        table_name=variable.admin_database,
                        param=f"WHERE id={response_dict['id']}",
                        field='full_anti_tags',
                        value=profession['profession']['anti_tag'].replace("'", ""),
                        output_text = f'{n}-anti_tags was updated'
                    )
                if profession_name != response_dict['profession']:
                    # rewrite profession
                    self.db.update_table(
                        table_name=variable.admin_database,
                        param=f"WHERE id={response_dict['id']}",
                        field='profession',
                        value=profession_name,
                        output_text=f'{n}-profession was updated'
                    )
                    # rewrite sub
                    sub = helper.compose_to_str_from_list(profession['profession']['sub'])
                    self.db.update_table(
                        table_name=variable.admin_database,
                        param=f"WHERE id={response_dict['id']}",
                        field='sub',
                        value=sub,
                        output_text=f'{n}-sub was updated'
                    )
                n += 1
                await progress.show_the_progress(
                    message=msg,
                    current_number=n,
                    end_number=length
                )

        async def rollback_by_number_short_session(message, short_session_number=None):
            msg = await self.bot_aiogram.send_message(message.chat.id, "Please wait a few seconds")

            # responses1 = self.db.get_all_from_db(
            #     table_name='devops',
            #     param="WHERE short_session_numbers LIKE '%20230207231816%'"
            #     # field='short_session_numbers'
            # )
            # responses_admin = self.db.get_all_from_db(
            #     table_name=variable.admin_database,
            #     param="WHERE short_session_numbers LIKE '%20230207231816%'"
            #     # field='short_session_numbers'
            # )
            # responses_archive = self.db.get_all_from_db(
            #     table_name=variable.archive_database,
            #     param="WHERE short_session_numbers LIKE '%20230207231816%'"
            #     # field='short_session_numbers'
            # )
            pass
            # layout: backend: 070220230134
            bot_dict = {'bot': self.bot_aiogram, 'chat_id': message.chat.id}
            progress = ShowProgress(bot_dict)

            if not short_session_number:
                short_session_number = self.db.get_all_from_db(
                    table_name=variable.short_session_database,
                    param=f"WHERE id=(SELECT MAX(id) FROM {variable.short_session_database})",
                    field='session_name',
                    without_sort=True
                )[0][0]

            # add tags
            table_list = []
            table_list.extend(variable.valid_professions)
            table_list.append(variable.admin_database)
            table_list.append(variable.archive_database)

            fields = 'id, profession, short_session_numbers'

            for table_name in table_list:
                responses = self.db.get_all_from_db(
                    table_name=table_name,
                    param=f"WHERE short_session_numbers='{short_session_number}'",
                    field=variable.admin_table_fields
                )
                if responses:
                    for response in responses:
                        response_dict = await helper.to_dict_from_admin_response(
                            response=response,
                            fields=variable.admin_table_fields
                        )
                        if table_name == variable.admin_database:
                            new_profession = response_dict['short_session_numbers'].split(":")[0].strip()
                            professions = response_dict['profession']
                            new_profession = f'{professions}, {new_profession}'
                            self.db.update_table(
                                table_name=variable.admin_database,
                                param=f"WHERE id={response_dict['id']}",
                                field='profession',
                                value=new_profession,
                                output_text="profession was updated"
                            )
                            self.db.update_table(
                                table_name=variable.admin_database,
                                param=f"WHERE id={response_dict['id']}",
                                field='short_session_numbers',
                                value='clear',
                                output_text="shorts_session was updated"
                            )

                        elif table_name == variable.archive_database:
                            new_profession = response_dict['short_session_numbers'].split(":")[0].strip()
                            professions = response_dict['profession']
                            new_profession = f'{professions}, {new_profession}'
                            self.db.update_table(
                                table_name=variable.admin_database,
                                param=f"WHERE id={response_dict['id']}",
                                field='profession',
                                value=new_profession,
                                output_text="profession was updated"
                            )
                            await self.transfer_vacancy_from_to_table(
                                id_admin_last_session_table=response_dict['id'],
                                table_from=variable.archive_database,
                                table_to=variable.admin_database,

                            )
                        else:
                            self.db.delete_data(
                                table_name=table_name,
                                param=f"WHERE id={response_dict['id']}"
                            )
            await msg.edit_text(f"{msg.text}\nDone! Data has restored")

        async def get_vacancies_name_by_profession(message, profession):
            vacancy_name_str = ''
            vacancy_name_list = []
            responses = self.db.get_all_from_db(
                table_name=variable.admin_database,
                field='title, vacancy, full_tags, full_anti_tags, profession, sub',
                param=f"WHERE profession LIKE '%{profession}%'"
            )
            if responses:
                with open(f"{variable.path_to_excel}{profession}.txt", 'a', encoding="utf-8") as file:
                    file.write("")
                vacancy_name_list.append(f"Quantity juniors: {len(responses)}\n\n")
                count = 1
                for response in responses:
                    if response[1]:
                        text = f"{count}\n{response[1]}\nprof: {response[4]}\n{response[2]}\n{response[3]}\nsubs:\n{response[5]}\n----------\n\n"
                    else:
                        text = f"{count}\n{response[0]}\nprof: {response[4]}\n{response[2]}\n{response[3]}\nsubs:\n{response[5]}\n----------\n\n"
                    if len(f"{vacancy_name_str}{text}")>4096:
                        vacancy_name_list.append(vacancy_name_str)
                        vacancy_name_str = text
                    else:
                        vacancy_name_str += text
                    count += 1
                vacancy_name_list.append(vacancy_name_str)
                # for i in vacancy_name_list:
                #     await self.bot_aiogram.send_message(message.chat.id, i)
                #     await asyncio.sleep(random.randrange(1,2))
                with open(f"{variable.path_to_excel}{profession}.txt", 'a', encoding="utf-8") as file:
                    for i in vacancy_name_list:
                        file.write(i)
                await self.send_file_to_user(
                    message=message,
                    path=f"{variable.path_to_excel}{profession}.txt"
                )

        async def get_and_write_level(message):
            response_dict = {}
            level = ''
            table_list = []
            table_list.extend(variable.valid_professions)
            table_list.append(variable.admin_database)
            table_list.append(variable.archive_database)
            self.db.add_columns_to_tables(
                table_list=table_list,
                column_name_type="level VARCHAR (70)"
            )

            responses = self.db.get_all_from_db(
                table_name=variable.admin_database,
                param="WHERE profession <> 'no_sort'",
                field=variable.admin_table_fields
            )
            if responses:
                for response in responses:
                    response_dict = await helper.to_dict_from_admin_response(
                        response=response,
                        fields=variable.admin_table_fields
                    )
                    level = VacancyFilter().sort_profession(
                        title=response_dict['title'],
                        body=response_dict['body'],
                        check_contacts=False,
                        check_vacancy=False,
                        check_profession=False,
                        get_params=False,
                        check_level=True
                    )['profession']['level']
                    pass
                    self.db.update_table(
                        table_name=variable.admin_database,
                        param=f"WHERE id={response_dict['id']}",
                        field="level",
                        value=level,
                        output_text=level
                    )
            await self.bot_aiogram.send_message(message.chat.id, "Done!")

        async def update_job_types(message):
            tables_list = []
            tables_list.extend(variable.valid_professions)
            tables_list.append(variable.admin_database)
            tables_list.append(variable.archive_database)
            fields = "id, title, body, job_type"
            for table_name in tables_list:
                responses = self.db.get_all_from_db(
                    table_name=table_name,
                    param="WHERE profession NOT LIKE '%no_sort%'",
                    field=fields
                )
                count = 0
                for vacancy in responses:
                    print(count, '.')
                    count += 1
                    vacancy_dict = await helper.to_dict_from_admin_response(vacancy, fields)
                    job_type_new = helper.update_job_types(vacancy_dict)
                    field = 'job_type'
                    print(f"regular {field}: {vacancy_dict[field]}")
                    print(f"updated {field}: {job_type_new}")
                    if vacancy_dict['job_type'] != job_type_new:
                        self.db.update_table(
                            table_name=table_name,
                            param=f"WHERE id={vacancy_dict['id']}",
                            field='job_type',
                            value=job_type_new,
                            output_text="update has done"
                        )

            await self.bot_aiogram.send_message(message.chat.id, 'Job_types were updated')

        async def update_level(message):
            response_dict = {}
            level = ''
            table_list = []
            table_list.extend(variable.valid_professions)
            table_list.append(variable.admin_database)
            table_list.append(variable.archive_database)
            fields = 'id, title, body, level'

            for table in table_list:
                responses = self.db.get_all_from_db(
                    table_name=table,
                    param="WHERE profession <> 'no_sort'",
                    field=fields
                )
                if responses:
                    for response in responses:
                        response_dict = await helper.to_dict_from_admin_response(
                            response=response,
                            fields=fields
                        )
                        level = VacancyFilter().sort_profession(
                            title=f"{response_dict['title']}\n{response_dict['level']}",
                            body=response_dict['body'],
                            check_contacts=False,
                            check_vacancy=False,
                            check_profession=False,
                            get_params=False,
                            check_level=True
                        )['profession']['level']

                        self.db.update_table(
                            table_name=table,
                            param=f"WHERE id={response_dict['id']}",
                            field="level",
                            value=level,
                            output_text=level
                        )
            await self.bot_aiogram.send_message(message.chat.id, "Level field was updated!")

        async def get_from_admin(message):
            path = "./excel/vacancy_from_admin.txt"
            with open(path, 'w', encoding='utf-8') as file:
                file.write(f"")

            history_messages = await self.get_tg_history_messages(message)
            for vacancy in history_messages:
                with open(path, 'w', encoding='utf-8') as file:
                    text = vacancy['message'].split('\n')[0]
                    file.write(f"{text}\n")

            await self.send_file_to_user(message, path=path)

        async def add_field_into_tables_db(message, field):
            table_list = []
            table_list.extend(variable.valid_professions)
            table_list.append(variable.admin_database)
            table_list.append(variable.archive_database)
            table_list.append(variable.admin_copy)

            self.db.add_columns_to_tables(
                table_list=table_list,
                column_name_type=field
            )

        async def vacancies_from(profession, date_in):
            statistics_dict = {}
            today = datetime.now().strftime('%Y-%m-%d')
            statistics_message = ''
            fields = 'id, vacancy_url'

            if profession == '*':
                param = f"WHERE DATE(time_of_public) = '{date_in}'"
            else:
                param = f"WHERE profession LIKE '%{profession}%' and DATE(time_of_public) = '{date_in}'"

            responses = self.db.get_all_from_db(
                table_name=variable.admin_database,
                param=param,
                field=fields
            )
            for response in responses:
                response_dict = await helper.to_dict_from_admin_response(
                    response=response,
                    fields=fields
                )
                if 't.me' in response_dict['vacancy_url']:
                    key = "t.me/" + response_dict['vacancy_url'].split('/')[3]
                else:
                    key = response_dict['vacancy_url'].split('/')[2]
                if key not in statistics_dict:
                    statistics_dict[key] = 1
                else:
                    statistics_dict[key] += 1
            for key in statistics_dict:
                statistics_message += f"{key}: {statistics_dict[key]}\n"
            return statistics_message

        async def add_copy_admin_table(message):
            # # check DB for existing
            # text_tables = ''
            # tables_list = self.db.output_tables()
            #
            # # output for user
            # for element in tables_list:
            #     text_tables += f"{element}\n"
            # await self.bot_aiogram.send_message(message.chat.id, text_tables)
            #
            # if exists, delete
            # if variable.admin_copy in tables_list:
            self.db.delete_table(variable.admin_copy)

            # create new
            self.db.check_or_create_table_admin(table_name=variable.admin_copy)


            # transfer from admin to admin_copy
            responses = self.db.get_all_from_db(
                table_name=variable.admin_database,
                param="WHERE profession <> 'no_sort'",
                field='id'
            )
            for response in responses:
                response_dict = await helper.to_dict_from_admin_response(
                    response=response,
                    fields='id'
                )
                self.db.transfer_vacancy(
                    table_from=variable.admin_database,
                    table_to=variable.admin_copy,
                    id=response_dict['id']
                )

        async def transpose_no_sort_to_archive(message):
            no_sort_messages = self.db.get_all_from_db(
                table_name=variable.admin_database,
                param="WHERE profession = 'no_sort'",
                field=variable.admin_table_fields
            )
            no_sort_archive = self.db.get_all_from_db(
                table_name=variable.archive_database,
                param="WHERE profession = 'no_sort'",
                field=variable.admin_table_fields
            )
            message_for_send = f"Previous:\nadmin: {len(no_sort_messages)}\narchive: {len(no_sort_archive)}\n------------\n"
            count = 0
            for vacancy in no_sort_messages:
                if self.db.transfer_vacancy(
                        table_from=variable.admin_database,
                        table_to=variable.archive_database,
                        response_from_db=vacancy
                ):
                    print(count, 'transfer +')
                    self.db.delete_data(
                        table_name=variable.admin_database,
                        param=f"WHERE id={vacancy[0]}"
                    )
                else:
                    print(count, "something is wrong")
                count += 1
            no_sort_messages = self.db.get_all_from_db(
                table_name=variable.admin_database,
                param="WHERE profession = 'no_sort'",
                field=variable.admin_table_fields
            )
            no_sort_archive = self.db.get_all_from_db(
                table_name=variable.archive_database,
                param="WHERE profession = 'no_sort'",
                field=variable.admin_table_fields
            )
            message_for_send += f"processed {count} vacancies\n------\nActual:\nadmin: {len(no_sort_messages)}\narchive: {len(no_sort_archive)}"
            await self.bot_aiogram.send_message(message.chat.id, message_for_send)

        async def check_vacancies_for_relevance(message):
            not_relevance = 0
            relevance = 0
            helper.add_to_report_file(
                path=variable.report_file_not_actual_vacancy,
                write_mode='w',
                text=''
            )
            table_list = []
            table_list.extend([variable.admin_database, variable.archive_database])
            table_list.extend(variable.valid_professions)
            self.db.add_columns_to_tables(
                table_list=table_list,
                column_name_type="closed BOOLEAN"
            )

            all_vacancies = self.db.get_all_from_db(
                table_name=variable.admin_database,
                field=variable.admin_table_fields,
                param="WHERE profession <> 'no_sort'"
            )

            for vacancy in all_vacancies:
                vacancy_dict = await helper.to_dict_from_temporary_response(
                    response=vacancy,
                    fields=variable.admin_table_fields
                )
                vacancy_url = vacancy_dict['vacancy_url']
                if vacancy_url:
                    if 't.me' not in vacancy_url:
                        print(vacancy_url)
                        response = requests.get(vacancy_url)
                        if response.status_code != 200:
                            for i in range(0, 1):
                                response = requests.get(vacancy_url)
                                if response.status_code == 200:
                                    print('Good')
                                    relevance += 1
                                    break
                                else:
                                    helper.add_to_report_file(
                                        path=variable.report_file_not_actual_vacancy,
                                        write_mode='a',
                                        text=f"id: {vacancy_dict['id']}\nurl: {vacancy_url}\n----------\n\n"
                                    )
                                    self.db.update_table(
                                        table_name=variable.admin_database,
                                        field='closed',
                                        value='TRUE',
                                        output_text='field closed updated +'
                                    )
                                    # self.db.transfer_vacancy(
                                    #     table_from=variable.admin_database,
                                    #     table_to=variable.archive_database,
                                    #     response_from_db=vacancy
                                    # )
                                    # self.db.delete_data(
                                    #     table_name=variable.admin_database,
                                    #     param=f"WHERE id={vacancy_dict['id']}"
                                    # )
                                    not_relevance += 1
                                    print('Wrong')
                        else:
                            relevance += 1
                            print('Good')

            await self.bot_aiogram.send_message(message.chat.id, f"Relevance: {relevance} vacancies\nNot relevance: {not_relevance} vacancies")
            await self.send_file_to_user(
                path=variable.report_file_not_actual_vacancy,
                send_to_developer=True
            )

        async def copy_prof_tables_to_archive_prof_tables():
            pass

        # start_polling(self.dp)
        executor.start_polling(self.dp, skip_updates=True)


    async def delete_used_vacancy_from_admin_temporary(self, vacancy, id_admin_last_session_table):
        # ------------------- cleaning the areas for the used vacancy  -------------------
        print('\ndelete vacancy\n')
        await self.client.delete_messages(int(config['My_channels']['admin_channel']), vacancy['id'])
        await asyncio.sleep(random.randrange(2, 3))

        # ----------------- deleting this vacancy's data from admin_temporary -----------------
        self.db.delete_data(
            table_name='admin_temporary',
            param=f"WHERE id_admin_last_session_table='{id_admin_last_session_table}'"
        )

    async def compose_message_for_send_dict(self, composed_message_dict, profession):
        if composed_message_dict['sub_list']:
            n = 0
            for sub in composed_message_dict['sub_list']:
                print(f'~~~~~~~~ iterations from compose_message_for_send_dict: {n}')
                n += 1
                if sub not in self.message_for_send_dict.keys():
                    self.message_for_send_dict[
                        sub] = f"Дайджест вакансий для {sub.capitalize()} за {datetime.now().strftime('%d.%m.%Y')}\n\n"
                self.message_for_send_dict[sub] += f"{composed_message_dict['composed_message']}\n"
        else:
            if profession not in self.message_for_send_dict.keys():
                self.message_for_send_dict[
                    profession] = f"Дайджест вакансий для {profession.capitalize()} за {datetime.now().strftime('%d.%m.%Y')}\n\n"
            self.message_for_send_dict[profession] += f"{composed_message_dict['composed_message']}\n"
        self.quantity_entered_to_shorts += 1

    async def send_file_to_user(self, message, path, caption='Please take it', send_to_developer=False):
        logs.write_log(f"invite_bot_2: function: send_file_to_user")
        with open(path, 'rb') as file:
            try:
                await self.bot_aiogram.send_document(message.chat.id, file, caption=caption)
                if send_to_developer and message.chat.id != variable.developer_chat_id:
                    try:
                        await self.bot_aiogram.send_document(int(variable.developer_chat_id), file, caption=caption)
                    except Exception as e:
                        print(e)
            except:
                await self.client.send_file(int(variable.developer_chat_id), file, caption=caption)

    async def show_progress(self, message, n, len):
        check = n * 100 // len
        if check > self.percent:
            quantity = check // 5
            self.percent = check
            self.message = await self.bot_aiogram.edit_message_text(
                f"progress {'|' * quantity} {self.percent}%", self.message.chat.id, self.message.message_id)
        await asyncio.sleep(random.randrange(1, 2))

    async def delete_and_change_waste_vacancy(self, message, last_id_message_agregator, profession):
        # There are messages, which user deleted in admin. Their profession must be correct (delete current profession)
        response_admin_temporary = self.db.get_all_from_db(
            table_name='admin_temporary',
            without_sort=True
        )
        length = len(response_admin_temporary)
        n = 0
        self.percent = 0

        if response_admin_temporary:
            await self.bot_aiogram.send_message(message.chat.id, 'It clears the temporary database')
            await asyncio.sleep(1)
            self.message = await self.bot_aiogram.send_message(message.chat.id, f'progress {self.percent}%')
            await asyncio.sleep(1)

        # theese vacancy we need to make profession changes
        for i in response_admin_temporary:
            id_admin_last_session_table = i[2]
            response_admin_last_session = self.db.get_all_from_db(
                table_name='admin_last_session',
                param=f"WHERE id='{id_admin_last_session_table}'",
                without_sort=True
            )
            prof_list = response_admin_last_session[0][4].split(', ')
            try:
                await self.update_vacancy_admin_last_session(
                    results_dict=None,
                    profession=profession,
                    prof_list=prof_list,
                    id_admin_last_session_table=id_admin_last_session_table,
                    update_profession=True,
                    update_id_agregator=False
                )
            except Exception as e:
                print('error with deleting from admin temporary ', e)
            n = + 1
            await self.show_progress(message, n, length)
            # -------------------end ----------------------------

    async def compose_message_for_linkedin(self, key, message_for_send, profession, shorts_id=None):
        message = message_for_send.strip()
        message_list = message.split('\n\n')[1:]
        vacancies = (len(message_list))
        if vacancies in [1, 21]:
            vac_text = 'вакансия'
        elif vacancies in [2, 3, 4, 22, 23, 24]:
            vac_text = 'вакансии'
        else:
            vac_text = 'вакансий'
        linkedin_message = f"Дайджест вакансий для {key.capitalize()} за {datetime.now().strftime('%d.%m.%Y')}: {vacancies} {vac_text}\n" \
                           f"Vacancies digest for {key.capitalize()} for {datetime.now().strftime('%d.%m.%Y')}\n\n"
        for i in message_list:
            i = re.sub(r'<a href="https:\S+"><b>', '', i)
            i = re.sub(r'</\w>', '', i)
            if len(linkedin_message + f"{i}\n\n") < 2600:
                linkedin_message += f"{i}\n\n"
        if shorts_id:
            link_to_short = f"{config['Links'][profession]}/{shorts_id}"
            linkedin_message += f"Смотреть все вакансии: {link_to_short} \n\n"
        links_message = ''
        if profession != 'junior':
            links_message += f"Подписывайтесь на канал для {profession.capitalize()} IT специалистов: {config['Links'][profession]}\n" \
                             f"Subscribe to our {profession.capitalize()} IT channel {config['Links'][profession]}\n"
        links_message += f"Подписывайтесь на наш канал с вакансиями для Junior IT специалистов: {config['Links']['junior']}\n" \
                         f"Subscribe to our Junior IT channel: {config['Links']['junior']}\n\n"
        linkedin_message += links_message

        return linkedin_message

    async def get_shorts_id(self, channel, message):
        shorts_id = None
        peer = await self.client.get_entity(int(channel))
        await asyncio.sleep(2)
        channel = PeerChannel(peer.id)
        try:
            history = await self.client(GetHistoryRequest(
                peer=channel,
                offset_id=0,
                offset_date=None, add_offset=0,
                limit=1, max_id=0, min_id=0,
                hash=0))
            shorts_id = history.messages[0].id
            print(shorts_id)
        except Exception as e:
            print(f'\n***Cant get last message***\n{e}\n')
            await self.bot_aiogram.send_message(message.chat.id,
                                                f'\n***Cant get last message***\n{e}\n')
        return shorts_id

    async def cut_message_for_send(self, message_for_send):
        vacancies_list = []
        if len(message_for_send) > 4096:
            message_limit = ''
            messages = message_for_send.split('\n\n')
            for i in messages:
                if len(message_limit + f"{i}\n\n") < 4096:
                    message_limit += f"{i}\n\n"
                else:
                    vacancies_list.append(message_limit)
                    message_limit = f"{i}\n\n"
            vacancies_list.append(message_limit)
        else:
            vacancies_list = [message_for_send]
        return vacancies_list

    async def shorts_public(self, message, profession, channel_for_pushing=False, profession_channel=None):

        with open(variable.shorts_copy_path, mode='w', encoding='utf-8') as shorts_file:
            shorts_file.write('')

        chat_id = config['My_channels'][f'{profession_channel}_channel'] if profession_channel else None
        pre_message = variable.pre_message_for_shorts
        add_pre_message = True
        count = 1
        for key in self.message_for_send_dict:
            message_for_send = self.message_for_send_dict[key]
            if add_pre_message:
                message_for_send = pre_message + message_for_send
                add_pre_message = False
            vacancies_list = await self.cut_message_for_send(message_for_send)

            photo_path = await helper.get_picture_path(key, profession)

            if profession_channel:
                chat_id = config['My_channels'][f'{profession_channel}_channel']
                try:
                    with open(photo_path, 'rb') as file:
                        try:
                            await self.bot_aiogram.send_photo(chat_id=chat_id, photo=file)
                        except Exception as ex:
                            print(f'Key {count}: picture error: {ex}. Chat_id: profession channel')
                            profession_channel = False
                except Exception as e:
                    print(f"Key {count}: Can not open the pictures: {e}. Path: {photo_path}")

            if not profession_channel:
                chat_id = variable.channel_id_for_shorts
                try:
                    with open(photo_path, 'rb') as file:
                        try:
                            await self.bot_aiogram.send_photo(chat_id=chat_id, photo=file)
                        except Exception as ex:
                            print(f'Key {count}: picture error: {ex}. Chat_id: channel for shorts')
                            chat_id = message.chat.id
                except Exception as e:
                    print(f"Key {count}: Can not open the pictures: {e}. Path: {photo_path}")
                    try:
                        with open(photo_path, 'rb') as file:
                            try:
                                await self.bot_aiogram.send_photo(chat_id=chat_id, photo=file)
                            except Exception as ex:
                                print(f'Key {count}: picture error: {ex}. Chat_id: message chat id')
                                print(f'Key {count}: ONE SHORTS HAS BEEN LOOSED')
                    except Exception as e:
                        print(e)
                        # await self.bot_aiogram.send_message(message.chat.id, f"ONE SHORTS HAS BEEN LOOSED{str(e)}")
                        await helper.send_message(self.bot_aiogram, message.chat.id, f"ONE SHORTS HAS BEEN LOOSED{str(e)}")
            count += 1

            for short in vacancies_list:
                try:
                    await helper.send_message(
                        bot=self.bot_aiogram,
                        chat_id=chat_id,
                        text=short,
                        parse_mode='html',
                        disable_web_page_preview=True
                    )
                    await asyncio.sleep(1)
                except:
                    with open(variable.shorts_copy_path, mode='a', encoding='utf-8') as shorts_file:
                        shorts_file.write(f"{short}\n\n")

            try:
                shorts_id=None
                if profession_channel:
                    channel = config['My_channels'][f'{profession_channel}_channel']
                    shorts_id = await self.get_shorts_id(channel, message)

                linkedin_message = await self.compose_message_for_linkedin(key, message_for_send, profession,
                                                                      shorts_id)
                # await self.bot_aiogram.send_message(
                #     variable.channel_id_for_shorts,
                #     'Post for LinkedIn',
                #     parse_mode='html',
                #     disable_web_page_preview=True
                # )
                # await self.bot_aiogram.send_message(
                #     variable.channel_id_for_shorts,
                #     linkedin_message,
                #     parse_mode='html',
                #     disable_web_page_preview=True
                # )
                await helper.send_message(
                    self.bot_aiogram,
                    variable.channel_id_for_shorts,
                    'Post for LinkedIn',
                    parse_mode='html',
                    disable_web_page_preview=True
                )
                await helper.send_message(
                    self.bot_aiogram,
                    variable.channel_id_for_shorts,
                    linkedin_message,
                    parse_mode='html',
                    disable_web_page_preview=True
                )

                # await self.bot_aiogram.send_message(message.chat.id, 'Linkedin message sent to channel_for_shorts')
                await helper.send_message(self.bot_aiogram, message.chat.id, 'Linkedin message sent to channel_for_shorts')
                await asyncio.sleep(random.randrange(1, 2))

            except Exception as e:
                # await self.bot_aiogram.send_message(message.chat.id, f"linkedin report: {str(e)}")
                await helper.send_message(self.bot_aiogram, message.chat.id, f"linkedin report: {str(e)}")

        try:
            await helper.send_file_to_user(
                bot=self.bot_aiogram,
                chat_id=message.chat.id,
                # message=message,
                path=variable.shorts_copy_path,
                caption='Take the shorts has not been added to shorts by sending error '
            )
        except Exception as ex:
            print(ex)

    async def write_to_logs_error(self, text):
        with open("./logs/logs_errors.txt", "a", encoding='utf-8') as file:
            file.write(text)

    async def compose_message(self, one_profession, vacancy_from_admin_dict, full=False, write_changes_to_db=True,
                              message=None):
        profession_list = {}

        if vacancy_from_admin_dict['profession']:
            profession_list['profession'] = []
            print(vacancy_from_admin_dict['profession'])

            if one_profession:
                profession_list['profession'] = [one_profession, ]  # rewrite list if one_profession
            else:
                if ',' in vacancy_from_admin_dict['profession']:
                    pro = vacancy_from_admin_dict['profession'].split(',')
                else:
                    pro = [vacancy_from_admin_dict['profession']]
                # delete all spaces
                for i in pro:
                    profession_list['profession'].append(i.strip())

            vacancy_from_admin_dict['job_type'] = re.sub(r'\<[a-zA-Z\s\.\-\'"=!\<_\/]+\>', " ",
                                                         vacancy_from_admin_dict['job_type'])
            params = VacancyFilter().sort_profession(
                title=vacancy_from_admin_dict['title'],
                body=vacancy_from_admin_dict['body'],
                check_contacts=False,
                check_profession=False,
                check_vacancy=False,
                get_params=True
            )['params']
            if vacancy_from_admin_dict['sub']:
                sub = helper.decompose_from_str_to_list(vacancy_from_admin_dict['sub'])
                print(sub.values())
                # if sub.values():
                #     pass
            else:
                sub = VacancyFilter().sort_profession(
                    title=vacancy_from_admin_dict['title'],
                    body=vacancy_from_admin_dict['body'],
                    check_contacts=False,
                    check_profession=True,
                    check_vacancy=False,
                    get_params=False
                )['profession']['sub']
            # compose message_to_send

            # code for transpose in shorts like reference

            remote_pattern = export_pattern['others']['remote']['ma']
            full_time_pattern = export_pattern['others']['full_time']['ma']
            relocate_pattern = export_pattern['others']['relocate']['ma']
            experience_pattern = export_pattern['others']['experience']['ma']
            english_pattern = export_pattern['others']['english_for_shorts']['ma']
            salary_patterns = export_pattern['others']['salary_for_shorts']['ma']
            city_pattern = export_pattern['others']['city_for_shorts']['ma']
            vacancy_pattern = export_pattern['others']['vacancy']['sub']

            remote_shorts = ''
            relocate_shorts = ''
            experience_shorts = ''
            english_shorts = ''
            salary_shorts = ''
            city_shorts = ''

            if not full:
                job_type_shorts = ''

                remote_shorts = await helper.get_field_for_shorts(
                    presearch_results=[
                        vacancy_from_admin_dict['job_type'],
                        vacancy_from_admin_dict['title'] + vacancy_from_admin_dict['body'],
                    ],
                    pattern=remote_pattern,
                    return_value='remote',
                )
                remote_shorts = remote_shorts['return_value']
                if remote_shorts:
                    job_type_shorts += remote_shorts

                full_time_shorts = await helper.get_field_for_shorts(
                    presearch_results=[
                        vacancy_from_admin_dict['job_type'],
                        vacancy_from_admin_dict['title'] + vacancy_from_admin_dict['body'],
                    ],
                    pattern=full_time_pattern,
                    return_value='fulltime',
                )
                full_time_shorts = full_time_shorts['return_value']
                if full_time_shorts:
                    if len(job_type_shorts) > 0:
                        job_type_shorts += ", "
                    job_type_shorts += full_time_shorts

                if job_type_shorts and write_changes_to_db:
                    self.db.update_table(
                        table_name=variable.admin_database,
                        param=f"WHERE id={vacancy_from_admin_dict['id']}",
                        field='job_type',
                        value=job_type_shorts,
                        output_text='job_type has updated'
                    )

                relocate_shorts = await helper.get_field_for_shorts(
                    presearch_results=[
                        vacancy_from_admin_dict['job_type'],
                        vacancy_from_admin_dict['relocation'],
                        vacancy_from_admin_dict['title'] + vacancy_from_admin_dict['body'],
                        params['relocation']
                    ],
                    pattern=relocate_pattern,
                    return_value='relocate'
                )
                relocate_shorts = relocate_shorts['return_value']

                experience_shorts = await helper.get_field_for_shorts(
                    presearch_results=[
                        vacancy_from_admin_dict['experience'],
                        vacancy_from_admin_dict['job_type']
                    ],
                    pattern=experience_pattern,
                    return_value='relocate'
                )
                if experience_shorts['match']:
                    experience_shorts = experience_shorts['match']
                    experience_shorts = re.findall(r'[0-9]{1,2}', relocate_shorts)
                    if experience_shorts:
                        experience_shorts = experience_shorts[0]
                else:
                    experience_shorts = ''

                english_shorts = await helper.get_field_for_shorts(
                    presearch_results=[
                        vacancy_from_admin_dict['english'],
                        params['english']
                    ],
                    pattern=english_pattern,
                    return_value='english'
                )
                if english_shorts['match']:
                    english_shorts = english_shorts['match']
                elif english_shorts['element_is_not_empty']:
                    english_shorts = 'B1+'
                else:
                    english_shorts = ''

                salary_shorts = await helper.get_field_for_shorts(
                    presearch_results=[
                        vacancy_from_admin_dict['salary'],
                        vacancy_from_admin_dict['title'] + vacancy_from_admin_dict['body']
                    ],
                    pattern=salary_patterns,
                    return_value='salary'
                )
                salary_shorts = salary_shorts['match']
                salary_shorts = salary_shorts.replace('до', '-').replace('  ', ' ')

                print('salary = ', salary_shorts)

                city_shorts = await helper.get_city_vacancy_for_shorts(
                    presearch_results=[
                        vacancy_from_admin_dict['city'],
                        vacancy_from_admin_dict['job_type'],
                        vacancy_from_admin_dict['title'] + vacancy_from_admin_dict['body'],
                    ],
                    pattern=city_pattern,
                    return_value='match'
                )
                if city_shorts['return_value']:
                    city_shorts = city_shorts['return_value']
                elif city_shorts['element_is_not_empty']:
                    if vacancy_from_admin_dict['city']:
                        city_shorts = vacancy_from_admin_dict['city']
                    else:
                        city_shorts = ''
                else:
                    city_shorts = ''

                message_for_send = ''
                vacancy = ''
                if vacancy_from_admin_dict['vacancy']:
                    vacancy = vacancy_from_admin_dict['vacancy']
                elif params['vacancy']:
                    vacancy = params['vacancy']
                if not vacancy:
                    vacancy = await helper.get_city_vacancy_for_shorts(
                        presearch_results=[
                            vacancy_from_admin_dict['title'],
                            vacancy_from_admin_dict['body'],
                        ],
                        pattern=vacancy_pattern,
                        return_value='match'
                    )
                    if "#" not in vacancy['match']:
                        vacancy = vacancy['match']
                if not vacancy:
                    vacancy = f"Вакансия #{random.randrange(100, 5000)}"
                message_for_send += f"<a href=\"{config['My_channels']['agregator_link']}/" \
                                    f"{vacancy_from_admin_dict['sended_to_agregator']}\">" \
                                    f"<b>{vacancy[0:40]}</b></a> "

                company = ''
                if vacancy_from_admin_dict['company']:
                    company = vacancy_from_admin_dict['company']
                elif params['company']:
                    company = params['company']
                if company:
                    message_for_send += f"в {company.strip()[:40]} "

                message_for_send += '('

                if city_shorts:
                    message_for_send += f"{city_shorts[:40]}, "

                if english_shorts:
                    message_for_send += f"eng: {english_shorts[:40]}, "

                if experience_shorts:
                    message_for_send += f"exp: {experience_shorts[:40]} year(s), "

                if relocate_shorts:
                    message_for_send += f"{relocate_shorts.capitalize()[:40]}, "

                # if remote_shorts:
                #     message_for_send += f"{remote_shorts.capitalize()[:40]}, "

                if job_type_shorts:
                    message_for_send += f"{job_type_shorts.capitalize()[:40]}, "

                if salary_shorts:
                    message_for_send += f"{salary_shorts[:40]}, "
            # end of code

            else:

                message_for_send = 'Вакансия '
                if vacancy_from_admin_dict['vacancy']:
                    vacancy = vacancy_from_admin_dict['vacancy']
                elif params['vacancy']:
                    vacancy = params['vacancy']
                else:
                    vacancy = f"#{random.randrange(100, 5000)}"
                message_for_send += f"<b>: {vacancy.replace('.', '').strip()}</b>\n"

                company = ''
                if vacancy_from_admin_dict['company']:
                    company = vacancy_from_admin_dict['company']
                elif params['company']:
                    company = params['company']
                if company:
                    message_for_send += f"Компания: {company.strip()}\n"

                if vacancy_from_admin_dict['city']:
                    message_for_send += f"Город/страна: {vacancy_from_admin_dict['city']}\n"

                english = ''
                if vacancy_from_admin_dict['english']:
                    english = vacancy_from_admin_dict['english']
                elif params['english']:
                    english = params['english']
                if english:
                    message_for_send += f"English: {params['english']}\n"

                job_type = ''
                if vacancy_from_admin_dict['job_type']:
                    job_type = vacancy_from_admin_dict['job_type']
                elif params['job_type']:
                    job_type = params['job_type']
                if job_type:
                    message_for_send += f"Формат работы: {params['job_type']}\n"

                relocation = ''
                if vacancy_from_admin_dict['relocation']:
                    relocation = vacancy_from_admin_dict['relocation']
                elif params['relocation']:
                    relocation = params['relocation']
                if relocation:
                    message_for_send += f"Релокация: {relocation}\n"

                if vacancy_from_admin_dict['salary']:
                    message_for_send += f"Зарплата: {vacancy_from_admin_dict['salary']}\n"

                if vacancy_from_admin_dict['experience']:
                    message_for_send += f"Опыт работы: {vacancy_from_admin_dict['experience']}\n"

                if vacancy_from_admin_dict['contacts']:
                    message_for_send += f"Контакты: {vacancy_from_admin_dict['contacts']}\n"

                elif vacancy_from_admin_dict['vacancy_url'] and 't.me' not in vacancy_from_admin_dict['vacancy_url']:
                    message_for_send += f"Ссылка на вакансию: {vacancy_from_admin_dict['vacancy_url']}\n"

                if vacancy_from_admin_dict['vacancy'].strip() != vacancy_from_admin_dict['title'].strip() or (
                        vacancy_from_admin_dict['vacancy'] and vacancy_from_admin_dict['title']):
                    message_for_send += f"\n<b>{vacancy_from_admin_dict['title']}</b>\n"
                message_for_send += vacancy_from_admin_dict['body']

            if len(message_for_send) > 4096:
                message_for_send = message_for_send[0:4092] + '...'

            if not message_for_send:
                message_for_send = 'The vacancy not found\n\n'
                await self.write_to_logs_error(
                    f"The vacancy not found\n{vacancy_from_admin_dict['title']}{vacancy_from_admin_dict['body']}")

            if not full:
                if message_for_send[-1:] == '(':
                    message_for_send = message_for_send[:-2] + '\n'
                elif message_for_send[-2:] == ', ':
                    message_for_send = message_for_send[0:-2]
                    message_for_send += ')\n'

            sub_list = []
            if type(sub) in [list, set, tuple, dict]:
                for sub_pro in sub:
                    if sub_pro:
                        sub_list.append(sub_pro)
            elif type(sub) is str:
                pass

            try:
                if one_profession in sub_list:
                    if type(sub[one_profession]) is str:
                        sub[one_profession] = sub[one_profession].split(", ")
                    sub_list = sub[one_profession]
                else:
                    sub_list = []
            except:
                sub_list = []

            print('-------------------------------------')
            print('db_remote = ', vacancy_from_admin_dict['job_type'])
            print('db_relocation = ', vacancy_from_admin_dict['relocation'])
            print('params_relocation = ', params['relocation'])
            print('db_salary = ', vacancy_from_admin_dict['salary'])
            print('db_english = ', vacancy_from_admin_dict['english'])
            print('params_english = ', params['english'])
            print('message_for_send ', message_for_send[:100])
            print('-------------------------------------')

            return {'composed_message': message_for_send, 'sub_list': sub_list, 'db_id': vacancy_from_admin_dict['id'],
                    'all_subs': sub}

    async def compose_data_and_push_to_db(self, vacancy_from_admin_dict, profession, shorts_session_name):
        profession_list = {}
        profession_list['profession'] = []
        profession_list['profession'] = [profession, ]

        response_from_db = self.db.push_to_bd(
            results_dict=vacancy_from_admin_dict,
            profession_list=profession_list,
            shorts_session_name=shorts_session_name
        )
        return response_from_db

    async def transfer_vacancy_from_to_table(
            self,
            id_admin_last_session_table,
            table_from=variable.admin_database,
            table_to=variable.archive_database,
            response=None
    ):

        if not response:
            response = self.db.get_all_from_db(
                table_name=f'{table_from}',
                param=f"WHERE id={id_admin_last_session_table}",
                field=variable.admin_table_fields
            )
            response = response[0]

        if response:
            response_dict = await helper.to_dict_from_admin_response(
                response=response,
                fields=variable.admin_table_fields
            )

            # response = response[0]
            query = f"""INSERT INTO {table_to} (
                    chat_name, title, body, profession, vacancy, vacancy_url, company, english, relocation,
                    job_type, city, salary, experience, contacts, time_of_public, created_at, agregator_link,
                    session, sended_to_agregator, sub, tags, full_tags, full_anti_tags, short_session_numbers)
                            VALUES (
                            '{response_dict['chat_name']}', '{response_dict['title']}', '{response_dict['body']}',
                            '{response_dict['profession']}', '{response_dict['vacancy']}', '{response_dict['vacancy_url']}',
                            '{response_dict['company']}',
                            '{response_dict['english']}', '{response_dict['relocation']}', '{response_dict['job_type']}',
                            '{response_dict['city']}', '{response_dict['salary']}', '{response_dict['experience']}',
                            '{response_dict['contacts']}', '{response_dict['time_of_public']}', '{response_dict['created_at']}',
                            '{response_dict['agregator_link']}', '{response_dict['session']}', '{response_dict['sended_to_agregator']}',
                            '{response_dict['sub']}', '{response_dict['tags']}', '{response_dict['full_tags']}',
                            '{response_dict['full_anti_tags']}', '{response_dict['short_session_numbers']}');"""
            self.db.run_free_request(
                request=query,
                output_text="\nThe vacancy has removed from admin to archive\n"
            )

    async def update_vacancy_admin_last_session(
            self,
            results_dict=None,
            profession=None,
            prof_list=None,
            id_admin_last_session_table=None,
            update_profession=False,
            update_id_agregator=False,
            shorts_session_name=None
    ):

        if shorts_session_name:
            self.db.update_table(
                table_name=variable.admin_database,
                param=f"WHERE id={id_admin_last_session_table}",
                field="short_session_numbers",
                value=shorts_session_name
            )

        if update_profession:
            len_prof_list = len(prof_list)
            if len_prof_list < 2:

                await self.transfer_vacancy_from_to_table(id_admin_last_session_table)
                self.db.delete_data(
                    table_name='admin_last_session',
                    param=f"WHERE id={id_admin_last_session_table}"
                )
            # 5. if more that delete current profession from column profession
            else:
                new_profession = ''
                for i in prof_list:
                    i = i.strip()
                    if i != profession:
                        new_profession += f'{i}, '
                new_profession = new_profession[:-2].strip()
                self.db.run_free_request(
                    request=f"UPDATE {variable.admin_database} SET profession='{new_profession}' WHERE id={id_admin_last_session_table}",
                    output_text='profession has updated'
                )

            # write mark as shorts_session_name
            if shorts_session_name:
                self.db.run_free_request(
                    request=f"UPDATE {variable.admin_database} SET short_session_numbers='{shorts_session_name}' WHERE id={id_admin_last_session_table}",
                    output_text='shorts session name has updated'
                )

        if update_id_agregator:
            # 6 Mark vacancy like sended to agregator (write to column sended_to_agregator id_agregator)
            self.db.run_free_request(
                request=f"UPDATE admin_last_session SET sended_to_agregator='{self.last_id_message_agregator}' WHERE id={id_admin_last_session_table}",
                output_text='sended_to_agregator has updated'
            )

            # check the changes
            response_check = self.db.get_all_from_db(
                table_name='admin_last_session',
                param=f"WHERE id={id_admin_last_session_table}",
                without_sort=True,
                field='sended_to_agregator'
            )
            try:
                print('changed id agreg = ', response_check[0][0])
            except Exception as e:
                print('hey, dude, WTF in 2832?\n', e)
                # self.bot_aiogram.send_message(message.chat.id, f"'hey, dude, WTF in 2832?\n{e}")

        # await asyncio.sleep(1)

    async def push_vacancies_to_agregator_from_admin(
            self,
            message,
            vacancy_message,
            # vacancy_from_admin,
            # response,
            # profession,
            # id_admin_last_session_table,
            # response_temp_dict=None,
            prof_stack=None,
            vacancy_from_admin_dict=None,
            links_on_prof_channels=False,
            # from_admin_temporary=True,
    ):

        """
        :param message: message from class bot_aiorgam
        :param vacancy: one vacancy from vacancies list from TG adminka history. Will send to agregator channel
        :param vacancy_from_admin: the same vacancy, but from db admin last session
        :param response: the technical data. [0][3] show agregator id
        :param profession: solo profession
        :param id_admin_last_session_table: last message id from agregator
        :return:
        """
        # if not self.
        if not prof_stack and vacancy_from_admin_dict:
            prof_stack = vacancy_from_admin_dict['profession']

        if vacancy_from_admin_dict:
            if not vacancy_from_admin_dict['sended_to_agregator']:
                print('push vacancy in agregator')
                print(f"{vacancy_from_admin_dict['title'][0:40]}")

                if links_on_prof_channels:
                    links_message = '\n----\nВ этом канале выводятся все собранные вакансии (агрегатор), для вашего удобства мы рекомендуем подписаться на наиболее подходящие для вас каналы (ссылки подобраны в каждом из сообщений):\n'
                    links_message += f"<a href=\"{config['Links']['junior']}\">Канал с вакансиями для Junior IT специалистов\n</a>"
                    prof_stack = prof_stack.split(', ')
                    if 'junior' in prof_stack:
                        prof_stack.remove('junior')
                    for i_prof in prof_stack:
                        i_prof = i_prof.strip()
                        if i_prof in self.valid_profession_list:
                            link = f"<a href=\"{config['Links'][i_prof]}\">Канал с вакансиями для {i_prof.title()} IT специалистов\n</a>"
                            links_message += link
                    if (len(links_message) + len(str(vacancy_message['message']))) <= 4096:
                        send_message = vacancy_message['message'] + links_message
                    else:
                        send_message = vacancy_message['message']
                else:
                    send_message = vacancy_message['message']
                try:
                    await self.bot_aiogram.send_message(int(config['My_channels']['agregator_channel']), send_message,
                                                        parse_mode='html', disable_notification=True, disable_web_page_preview=True)
                    self.last_id_message_agregator += 1
                    await asyncio.sleep(random.randrange(3, 4))
                except Exception as e:
                    print('the problem in func push_vacancies_to_agregator_from_admin', e)

                if vacancy_from_admin_dict:
                    # prof_list = vacancy_from_admin[0][4].split(', ')
                    # 4. if one that delete vacancy from admin_last_session
                    await self.update_vacancy_admin_last_session(
                        # id_admin_last_session_table=response_temp_dict['id_admin_last_session_table'],
                        id_admin_last_session_table=vacancy_from_admin_dict['id'],
                        update_id_agregator=True, results_dict={})
                else:
                    await self.bot_aiogram.send_message(message.chat.id,
                                                        f"<b>For the developer</b>: Hey, bot didn't find this vacancy in admin_last_session",
                                                        parse_mode='html')
            else:
                # await bot_aiogram.send_message(message.chat.id, 'It has sent in agregator some time ago')
                print('It has sent in agregator some time ago')

    async def get_last_admin_channel_id(self, message, channel=config['My_channels']['admin_channel']):
        chat_id = variable.id_owner if not message else message.chat.id

        last_admin_channel_id = None
        await self.bot_aiogram.send_message(channel, 'test')
        await asyncio.sleep(1)
        logs.write_log(f"scraping_telethon2: function: get_last_id_agregator")

        if channel != config['My_channels']['admin_channel']:
            limit_msg = 1
        else:
            limit_msg = 100

        try:
            all_messages = await self.get_tg_history_messages(message, channel, limit_msg)
            last_admin_channel_id = all_messages[0]['id']

            peer_channel = PeerChannel(int(channel))
            for i in all_messages:
                await self.client.delete_messages(peer_channel, i['id'])
        except Exception as e:
            await self.bot_aiogram.send_message(message.chat.id, f'for admin channel: {e}')

        return last_admin_channel_id

    async def get_tg_history_messages(
            self,
            message,
            channel=config['My_channels']['admin_channel'],
            limit_msg=None):

        if not self.client.is_connected():
            await self.client.connect()
        # print('client_id', await self.client.get_peer_id(channel))
        print('code is in get entity')
        try:
            peer = await self.client.get_entity(int(channel))
            channel = PeerChannel(peer.id)
            await asyncio.sleep(2)
        except:
            channel = int(channel)
        # channel = PeerChannel(int(config['My_channels']['admin_channel']))
        # channel = PeerChannel(peer.id)
        if not limit_msg:
            limit_msg = 3000
        logs.write_log(f"scraping_telethon2: function: dump_all_messages")

        print('dump')
        self.count_message_in_one_channel = 1
        block = False
        offset_msg = 0  # номер записи, с которой начинается считывание
        # limit_msg = 1   # максимальное число записей, передаваемых за один раз
        all_messages = []  # список всех сообщений
        total_messages = 0
        total_count_limit = limit_msg  # значение 0 = все сообщения
        history = None

        while True:
            try:
                print('code is in history getting')
                history = await self.client(GetHistoryRequest(
                    peer=channel,
                    offset_id=offset_msg,
                    offset_date=None, add_offset=0,
                    limit=limit_msg, max_id=0, min_id=0,
                    hash=0))
            except Exception as e:
                print(f'\n***Cant get messages from admin***\n{e}\n')
                await self.bot_aiogram.send_message(message.chat.id, f'\n***Cant get messages from admin***\n{e}\n')
                # await self.bot_dict['bot'].send_message(
                #     self.bot_dict['chat_id'],
                #     f"Getting history:\n{str(telethon)}: {channel}\npause 25-30 seconds...",
                #     parse_mode="HTML",
                #     disable_web_page_preview=True)
                time.sleep(2)

            if not history:
                print(f'Not history for channel {channel}')
                await self.bot_aiogram.send_message(message.chat.id, f'Not history for channel {channel}')
                break
            messages = history.messages
            if not messages:
                return all_messages
            for message in messages:
                if not message.message:  # если сообщение пустое, например "Александр теперь в группе"
                    pass
                else:
                    all_messages.append(message.to_dict())

            if not len(all_messages):
                return []
            else:
                offset_msg = messages[len(messages) - 1].id
            total_messages = len(all_messages)
            if (total_count_limit != 0 and total_messages >= total_count_limit) or not len(all_messages):
                break
            await asyncio.sleep(2)

        return all_messages

    async def push_shorts_attempt_to_make_multi_function(
            self,
            message,
            callback_data,
            hard_pushing=False,
            hard_push_profession=None,
            channel_for_pushing=False,
            only_approved_vacancies=False,
            only_pick_up_from_admin=False
    ):
        """
        function push shorts in 3 cases:
            1. compose shorts without admin for all professions
            2. compose shorts without admin for one profession
            3. compose shorts
        """
        # chat_id = variable.id_owner if not message else message.chat.id
        composed_message_dict = {}
        if not message:
            message = Message()
            message.chat = Chat()
            message.chat.id = variable.id_developer

        response_temp_dict = {}
        sp = ShowProgress(
            bot_dict={'bot': self.bot_aiogram, 'chat_id': message.chat.id}
        )
        self.message_for_send_dict = {}
        profession_list = {}
        prof_list = []
        self.percent = 0
        vacancy_from_admin_dict = {}

        if callback_data.split('/')[0] in ['all', 'each']:
            callback_data = 'shorts'

        # define the professions
        if hard_push_profession:
            if hard_push_profession in ['*', 'all']:
                prof_list = variable.profession_list_for_pushing_by_schedule
            else:
                if type(hard_push_profession) is str:
                    prof_list = [hard_push_profession,]
                elif type(hard_push_profession) in [list, tuple, set]:
                    prof_list = hard_push_profession
        else:
            prof_list = [callback_data.split(' ')[-1],]

        for profession in prof_list:
            self.temporary_data = {}
            self.message_for_send_dict = {}

            await sp.reset_percent()
            helper.add_to_report_file(
                path=variable.path_push_shorts_report_file,
                write_mode='a',
                text=f"callback_data.split()[-1]: {profession}\n"
            )

            if not hard_pushing:
                # get messages from TG admin
                history_messages = await self.get_tg_history_messages(message)
                self.out_from_admin_channel = len(history_messages)
                # message_for_send = f'<b>Дайджест вакансий для {profession} за {datetime.now().strftime("%d.%m.%Y")}:</b>\n\n'
            else:
                query = f"WHERE profession LIKE '%{profession}%' AND approved = 'TRUE'" if only_approved_vacancies else f"WHERE profession LIKE '%{profession}%'"
                history_messages = self.db.get_all_from_db(
                    table_name=variable.admin_database,
                    param=query,
                    field=variable.admin_table_fields
                )
            if history_messages:
                self.quantity_in_statistics = len(history_messages)

                # to get last agregator id
                self.last_id_message_agregator = await self.get_last_admin_channel_id(
                    message=message,
                    channel=config['My_channels']['agregator_channel']
                )

                short_session_name = await helper.get_short_session_name(prefix=profession)
                self.db.write_short_session(short_session_name)
                await self.bot_aiogram.send_message(message.chat.id, f"Shorts session: {short_session_name}")
                self.message = await self.bot_aiogram.send_message(message.chat.id, f'progress {self.percent}%')
                await asyncio.sleep(random.randrange(1, 2))

                length = len(history_messages)
                n = 0
                self.quantity_entered_to_shorts = 0

                #shorts_report
                if not self.temporary_data:
                    temporary_response = []
                    try:
                        temporary_response = self.db.get_all_from_db(table_name='admin_temporary', without_sort=True)
                    except Exception as ex:
                        print("Not amin_temporary: ", ex)
                    if temporary_response and type(temporary_response) is not str:
                        for item in temporary_response:
                            if 'in' not in self.temporary_data:
                                self.temporary_data['in'] = {}
                            if 'id_admin_channel' not in self.temporary_data['in']:
                                self.temporary_data['in']['id_admin_channel'] = []
                            if 'id_admin' not in self.temporary_data['in']:
                                self.temporary_data['in']['id_admin'] = []
                            self.temporary_data['in']['id_admin_channel'].append(str(item[0]))
                            self.temporary_data['in']['id_admin'].append(str(item[0]))
                            pass

                for vacancy in history_messages:
                    if hard_pushing:
                        vacancy = await helper.to_dict_from_admin_response(vacancy, variable.admin_table_fields)
                    helper.add_to_report_file(
                        path=variable.path_push_shorts_report_file,
                        write_mode='a',
                        text=f"Message_ID: {vacancy['id']}\n"
                    )

                    if not hard_pushing:
                        response = self.db.get_all_from_db(table_name='admin_temporary', without_sort=True)
                        # for i in response:
                        #     print(i)

                        response = self.db.get_all_from_db(
                            table_name='admin_temporary',
                            param=f"WHERE id_admin_channel='{vacancy['id']}'",
                            without_sort=True,
                            field=variable.fields_admin_temporary
                        )
                        if response:
                            response = response[0]
                            response_temp_dict = await helper.to_dict_from_temporary_response(response,
                                                                                              variable.fields_admin_temporary)
                            helper.add_to_report_file(
                                path=variable.path_push_shorts_report_file,
                                write_mode='a',
                                text=f"Temporary data: {response_temp_dict}\n"
                            )

                        if response:
                            vacancy_from_admin = self.db.get_all_from_db(
                                table_name=variable.admin_database,
                                param=f"WHERE id={response_temp_dict['id_admin_last_session_table']}",
                                without_sort=True,
                                field=variable.admin_table_fields
                            )
                            vacancy_from_admin = vacancy_from_admin[0]
                            vacancy_from_admin_dict = await helper.to_dict_from_admin_response(vacancy_from_admin,
                                                                                               variable.admin_table_fields)

                        else:
                            await self.bot_aiogram.send_message(message.chat.id,
                                                                'There is not response from admin temporary table')

                    else:
                        composed_message_dict = await self.compose_message(
                            vacancy_from_admin_dict=vacancy,
                            one_profession=profession,
                            full=True,
                            message=vacancy,
                        )
                        vacancy_from_admin_dict = vacancy
                    # shorts_report
                    if 'out' not in self.temporary_data:
                        self.temporary_data['out'] = {}
                    if 'id_admin_channel' not in self.temporary_data['out']:
                        self.temporary_data['out']['id_admin_channel'] = []
                    if 'id_admin' not in self.temporary_data['out']:
                        self.temporary_data['out']['id_admin'] = []
                    if 'title' not in self.temporary_data['out']:
                        self.temporary_data['out']['title'] = []
                    if 'body' not in self.temporary_data['out']:
                        self.temporary_data['out']['body'] = []

                    self.temporary_data['out']['id_admin_channel'].append(str(response_temp_dict['id_admin_channel'])) \
                        if not hard_pushing \
                        else self.temporary_data['out']['id_admin_channel'].append('-')

                    self.temporary_data['out']['id_admin'].append(
                        str(response_temp_dict['id_admin_last_session_table'])) \
                        if not hard_pushing \
                        else self.temporary_data['out']['id_admin'].append(str(vacancy['id']))

                    self.temporary_data['out']['title'].append(vacancy_from_admin_dict['title']) \
                        if not hard_pushing \
                        else self.temporary_data['out']['title'].append(str(vacancy['title']))

                    self.temporary_data['out']['body'].append(vacancy_from_admin_dict['body']) \
                        if not hard_pushing \
                        else self.temporary_data['out']['body'].append(str(vacancy['body']))

                    try:
                        helper.add_to_report_file(
                            path=variable.path_push_shorts_report_file,
                            write_mode='a',
                            text=f"DB ID vacancy: {vacancy_from_admin_dict['id']}\nTITLE: {vacancy_from_admin_dict['title']}\nSUB: {vacancy_from_admin_dict['sub']}\n"
                        )
                    except Exception as e:
                        print(e)

                    # if vacancy has sent in agregator already, it doesn't push again. And remove profess from profs or drop vacancy if there is profession alone
                    vacancy_message = {}
                    if type(vacancy) is dict and 'message' in vacancy:
                        vacancy_message['message'] = vacancy['message']
                    else:
                        vacancy_message['message'] = composed_message_dict['composed_message']
                    pass

                    await self.push_vacancies_to_agregator_from_admin(
                        message=message,
                        vacancy_message=vacancy_message,
                        # prof_stack=vacancy_from_admin_dict['profession'],
                        # response_temp_dict=response_temp_dict,
                        vacancy_from_admin_dict=vacancy_from_admin_dict,
                        links_on_prof_channels=True,
                        # id_admin_last_session_table=response_temp_dict['id_admin_last_session_table']
                    )

                    if "full" in callback_data:
                        # ---------- the unique operation block for fulls = pushing to prof channel full message ----------
                        print('push vacancy in channel\n')
                        print(f"\n{vacancy['message'][0:40]}")
                        await self.bot_aiogram.send_message(int(config['My_channels'][f'{profession}_channel']),
                                                            vacancy['message'])
                        await asyncio.sleep(random.randrange(3, 4))
                    # ------------------- end of  pushing to prof channel full message -----------------

                    elif "shorts" in callback_data:
                        # I need to get the newest vacancy
                        vacancy_from_admin = self.db.get_all_from_db(
                            table_name=variable.admin_database,
                            # param=f"WHERE id={response_temp_dict['id_admin_last_session_table']}",
                            param=f"WHERE id={vacancy_from_admin_dict['id']}",
                            without_sort=True,
                            field=variable.admin_table_fields
                        )
                        # transfer response to dict
                        vacancy_from_admin_dict = await helper.to_dict_from_admin_response(
                            response=vacancy_from_admin[0],
                            fields=variable.admin_table_fields
                        )
                        # collect to self.message_for_send_dict by subs
                        composed_message_dict = await self.compose_message(
                            one_profession=profession,
                            vacancy_from_admin_dict=vacancy_from_admin_dict
                        )
                        await self.compose_message_for_send_dict(
                            composed_message_dict,
                            profession
                        )
                        # push to profession tables
                        await self.compose_data_and_push_to_db(
                            vacancy_from_admin_dict=vacancy_from_admin_dict,
                            profession=profession,
                            shorts_session_name=short_session_name
                        )
                        prof_list = vacancy_from_admin_dict['profession'].split(', ')
                        profession_list['profession'] = [profession, ]

                        # update vacancy by profession field
                        await self.update_vacancy_admin_last_session(
                            results_dict=None,
                            profession=profession,
                            prof_list=prof_list,
                            # id_admin_last_session_table=response_temp_dict['id_admin_last_session_table'],
                            id_admin_last_session_table=vacancy_from_admin_dict['id'],
                            update_profession=True,
                            update_id_agregator=False,
                            shorts_session_name=short_session_name,
                        )
                    if not hard_pushing:
                        await self.delete_used_vacancy_from_admin_temporary(vacancy,
                                                                    vacancy_from_admin_dict['id'])
                    n += 1
                    await sp.show_the_progress(
                        message=self.message,
                        current_number=n,
                        end_number=length
                    )
                    # await show_progress(message, n, length)

                if "shorts" in callback_data:
                    if channel_for_pushing:
                        await self.shorts_public(message, profession=profession, profession_channel=profession)
                    else:
                        await self.shorts_public(message, profession=profession, profession_channel=None)


                if not hard_pushing:
                    await self.delete_and_change_waste_vacancy(message=message,
                                                          last_id_message_agregator=self.last_id_message_agregator,
                                                          profession=profession)

                    self.db.delete_table(
                        table_name='admin_temporary'
                    )

                #shorts_report
                try:
                    for n in range(0, len(self.temporary_data['out']['id_admin_channel'])):
                        if 'in' in self.temporary_data and self.temporary_data['out']['id_admin_channel'][n] in self.temporary_data['in']['id_admin_channel']:
                            index = self.temporary_data['in']['id_admin_channel'].index(self.temporary_data['out']['id_admin_channel'][n])

                            self.report.parsing_report(in_admin_channel=self.temporary_data['in']['id_admin_channel'][index], report_type='shorts')
                            self.report.parsing_report(in_id_admin=self.temporary_data['in']['id_admin'][index], report_type='shorts')
                            self.report.parsing_report(in_title=self.temporary_data['in']['title'][index] if 'title' in self.temporary_data['in'] else '-', report_type='shorts')
                            self.report.parsing_report(in_body=self.temporary_data['in']['body'][index] if 'body' in self.temporary_data['in'] else '-', report_type='shorts')
                            self.report.parsing_report(out_admin_channel=self.temporary_data['out']['id_admin_channel'][n], report_type='shorts')
                            self.report.parsing_report(out_id_admin=self.temporary_data['out']['id_admin'][n], report_type='shorts')
                            self.report.parsing_report(out_title=self.temporary_data['out']['title'][n], report_type='shorts')
                            self.report.parsing_report(out_body=self.temporary_data['out']['body'][n], report_type='shorts')
                            self.report.parsing_switch_next(switch=True, report_type='shorts')
                            for key in self.temporary_data['in']:
                                self.temporary_data['in'][key].pop(index)
                        else:
                            self.report.parsing_report(out_admin_channel=self.temporary_data['out']['id_admin_channel'][n], report_type='shorts')
                            self.report.parsing_report(out_id_admin=self.temporary_data['out']['id_admin'][n], report_type='shorts')
                            self.report.parsing_report(out_title=self.temporary_data['out']['title'][n], report_type='shorts')
                            self.report.parsing_report(out_body=self.temporary_data['out']['body'][n], report_type='shorts')
                            self.report.parsing_switch_next(switch=True, report_type='shorts')

                    if 'in' in self.temporary_data and self.temporary_data['in']['id_admin_channel']:
                        for n in range(0, len(self.temporary_data['in']['id_admin_channel'])):
                            self.report.parsing_report(in_admin_channel=self.temporary_data['in']['id_admin_channel'][n], report_type='shorts')
                            self.report.parsing_report(in_id_admin=self.temporary_data['in']['id_admin'][n], report_type='shorts')
                            self.report.parsing_report(in_title=self.temporary_data['in']['title'][n] if 'title' in self.temporary_data['in'] else '-', report_type='shorts')
                            self.report.parsing_report(in_body=self.temporary_data['in']['body'][n] if 'body' in self.temporary_data['in'] else '-', report_type='shorts')
                            self.report.parsing_switch_next(switch=True, report_type='shorts')

                    # await self.report.add_to_excel(report_type='shorts')
                    #
                    # await helper.send_file_to_user(
                    #     bot=self.bot_aiogram,
                    #     chat_id=message.chat.id,
                    #     path=report_file_path['shorts']
                    # )
                except Exception as ex:
                    await self.bot_aiogram.send_message(message.chat.id, f"error in the shorts report: {ex}")

                await self.report.add_to_excel(report_type='shorts')

                await helper.send_file_to_user(
                    bot=self.bot_aiogram,
                    chat_id=message.chat.id,
                    path=report_file_path['shorts']
                )

                await self.bot_aiogram.send_message(
                    message.chat.id,
                    f'<b>Done!</b>\n'
                    f'- in to statistics: {self.quantity_in_statistics}\n'
                    f'- in to admin {self.quantity_entered_to_admin_channel}\n'
                    f'- out from admin {self.out_from_admin_channel}\n'
                    f'- in to shorts {self.quantity_entered_to_shorts}',
                    parse_mode='html'
                )
                self.quantity_in_statistics = 0
                self.quantity_entered_to_admin_channel = 0
                self.out_from_admin_channel = 0
                self.quantity_entered_to_shorts = 0

                helper.add_to_report_file(
                    path=variable.path_push_shorts_report_file,
                    write_mode='a',
                    text=f"------------------------\n"
                )
                await self.send_file_to_user(
                    message=message,
                    path=variable.path_push_shorts_report_file,
                    send_to_developer=True
                )

            else:
                print(f'{profession}: no vacancies')
                await self.bot_aiogram.send_message(message.chat.id, f'{profession}: No vacancies')

        self.db.push_to_db_common(
            table_name="shorts_at_work",
            fields_values_dict={"shorts_at_work": False},
            params="WHERE id=1"
        )

    async def hard_pushing_by_schedule(self, message, profession_list):
        table_set = set()
        time_marker = ''

        if not message:
            message = Message()
            message.chat = Chat()
            message.chat.id = variable.id_developer

        await self.bot_aiogram.send_message(message.chat.id, 'schedule shorts posting has started')
        print('schedule shorts posting has started')

        tables_list = self.db.get_information_about_tables_and_fields()
        for i in tables_list:
            table_set.add(i[0])

        if variable.last_autopushing_time_database not in table_set:
            # get the last pushing time from db
            self.db.create_table_common(
                field_list=["time VARCHAR (10)", ],
                table_name=variable.last_autopushing_time_database
            )
            self.db.push_to_db_common(
                table_name=variable.last_autopushing_time_database,
                fields_values_dict={'time': '0'}
            )



        # self.db.delete_table(table_name=variable.last_autopushing_time_database)
        # self.db.create_table_common(
        #     field_list=["time VARCHAR (10)", ],
        #     table_name=variable.last_autopushing_time_database
        # )
        # self.db.push_to_db_common(
        #     table_name=variable.last_autopushing_time_database,
        #     fields_values_dict={'time': '0'}
        # )



        last_autopushing_time = self.db.get_all_from_db(
            table_name=variable.last_autopushing_time_database,
            field='time',
            param="WHERE id=1",
            without_sort=True
        )

        print('last_autopushing_time', last_autopushing_time)

        time_dict = {
            '09': False,
            '12': False,
            '17': False,
        }
        if last_autopushing_time:
            last_autopushing_time = last_autopushing_time[0][0]
            time_dict[last_autopushing_time] = True

        while True:
            if not self.schedule_pushing_shorts:
                break

            print('the checking pushing schedule time')
            current_time = int(datetime.now().time().strftime("%H"))

            if current_time >= 9 and current_time < 12 and not time_dict['09'] and not time_dict['09']:
                print('hard pushing 09 is starting')
                await self.push_shorts_attempt_to_make_multi_function(
                    message=message,
                    callback_data="each",
                    hard_pushing=True,
                    hard_push_profession=profession_list,
                    channel_for_pushing=True
                )
                time_dict['09'] = True
                time_dict['17'] = False
                time_dict['12'] = False
                time_marker = '9'

            elif current_time >= 12 and current_time < 17 and not time_dict['12']:
                print('hard pushing 12 is starting')
                await self.push_shorts_attempt_to_make_multi_function(
                    message=message,
                    callback_data="each",
                    hard_pushing=True,
                    hard_push_profession=profession_list,
                    channel_for_pushing=True
                )
                time_dict['12'] = True
                time_dict['09'] = False
                time_dict['17'] = False
                time_marker = '12'

            elif current_time >= 17 and current_time < 24 and not time_dict['17']:
                print('hard pushing 17 is starting')
                await self.push_shorts_attempt_to_make_multi_function(
                    message=message,
                    callback_data="each",
                    hard_pushing=True,
                    hard_push_profession=profession_list,
                    channel_for_pushing=True
                )
                time_dict['17'] = True
                time_dict['12'] = False
                time_dict['09'] = False
                time_marker = '17'

            if time_marker:
                self.db.update_table(
                    table_name=variable.last_autopushing_time_database,
                    param="WHERE id=1",
                    field='time',
                    value=time_marker,
                    output_text='time has been updated'
                )
            time_marker = ''

            if (current_time >= 0 and current_time < 7) or (current_time >= 19 and current_time < 24):
                print('the long pause')
                await self.bot_aiogram.send_message(message.chat.id, 'the long pause')
                await asyncio.sleep(1 * 60 * 30)
            else:
                print('the short pause')
                await self.bot_aiogram.send_message(message.chat.id, 'the short pause')
                await asyncio.sleep(1 * 60 * 10)

        return print('Schedule pushing has been stopped')

    async def show_statistics(self):
        result_dict = {}
        # --------- compose data from last session --------------
        result_dict['last_session'] = {}
        result_dict['all'] = {}
        if not self.current_session:
            self.current_session = await self.get_last_session()
        # ------------------------------ new ------------------------------------
        message_for_send = 'Statistics results:\n\n'
        for one_prof in variable.valid_professions:
            param = f"WHERE profession LIKE '%{one_prof}, %' OR profession LIKE '%, {one_prof}%' " \
                    f"OR profession='{one_prof}'" if one_prof == 'ba' else f"WHERE profession LIKE '%{one_prof}%'"
            response_all = self.db.get_all_from_db(
                table_name=variable.admin_database,
                param=param,
                field='id'
            )
            result_dict['all'][one_prof] = len(response_all)

            param += " AND session='{self.current_session}'"

            response_last_session = self.db.get_all_from_db(
                table_name=variable.admin_database,
                param=param,
                field='id'
            )
            result_dict['last_session'][one_prof] = len(response_last_session)
            # prof_dict = helper.string_to_list(
            #     text=variable.admin_table_fields,
            #     separator=', '
            # )
        responses = self.db.get_all_from_db(
            table_name=variable.admin_database,
            param="WHERE profession <> 'no_sort'",
            field='id'
        )
        for item in variable.valid_professions:
            message_for_send += f"{item}: {result_dict['last_session'][item]}/{result_dict['all'][item]}\n"
        message_for_send += f"-----------------\nSumm: {sum(result_dict['last_session'].values())}/{sum(result_dict['all'].values())}\n" \
                            f"vacancies number: {len(responses)}"
        return message_for_send
        # -----------------------------------------------------------------------


    async def get_last_session(self):
        last_session = ''
        current_session = self.db.get_all_from_db(
            table_name='current_session',
            param='ORDER BY id DESC LIMIT 1',
            without_sort=True,
            order=None,
            field='session',
            curs=None
        )
        for value in current_session:
            last_session = value[0]
        return last_session

    async def send_vacancy_to_admin_channel(self, message, callback_data):
        self.shorts_at_work = True
        self.temporary_data = {}
        helper.add_to_report_file(
            path=variable.path_push_shorts_report_file,
            write_mode='a',
            text=f"----------{datetime.now().strftime('%d-%m-%Y')}-----------\n[BUTTON] admin callback.data: {callback_data}\n"
        )

        try:
            self.db.delete_table('admin_temporary')
        except Exception as e:
            print(e)

        # delete messages for channel will be clean to take new messages
        all_messages = await self.get_tg_history_messages(message)
        for i in all_messages:
            await self.client.delete_messages(PeerChannel(int(config['My_channels']['admin_channel'])), i['id'])

        # getting the last message_id
        last_admin_channel_id = await self.get_last_admin_channel_id(message)

        profession = callback_data.split('/')[1]
        if profession == 'ba':
            param = f"WHERE profession LIKE '%{profession}' OR profession LIKE '%{profession},%'"
        else:
            param = f"WHERE profession LIKE '%{profession}%'"
        response = self.db.get_all_from_db(
            table_name='admin_last_session',
            param=param,
            without_sort=True,
            field=variable.admin_table_fields
        )
        self.quantity_in_statistics = len(response)

        if response:
            self.percent = 0
            length = len(response)
            n = 0
            # self.message = await self.bot_aiogram.send_message(message.chat.id, f'progress {self.percent}%')
            self.message = await helper.send_message(bot=self.bot_aiogram, chat_id=message.chat.id, text=f'progress {self.percent}%')
            await asyncio.sleep(random.randrange(2, 3))

            self.quantity_entered_to_admin_channel = 0
            for vacancy in response:
                vacancy_from_admin_dict = await helper.to_dict_from_admin_response(
                    response=vacancy,
                    fields=variable.admin_table_fields
                )
                # shorts_report
                if 'in' not in self.temporary_data:
                    self.temporary_data['in'] = {}
                if 'id_admin_channel' not in self.temporary_data['in']:
                    self.temporary_data['in']['id_admin_channel'] = []
                if 'id_admin' not in self.temporary_data['in']:
                    self.temporary_data['in']['id_admin'] = []
                if 'title' not in self.temporary_data['in']:
                    self.temporary_data['in']['title'] = []
                if 'body' not in self.temporary_data['in']:
                    self.temporary_data['in']['body'] = []
                self.temporary_data['in']['id_admin_channel'].append(str(last_admin_channel_id + 1))
                self.temporary_data['in']['id_admin'].append(str(vacancy_from_admin_dict['id']))
                self.temporary_data['in']['title'].append(vacancy_from_admin_dict['title'])
                self.temporary_data['in']['body'].append(vacancy_from_admin_dict['body'])
                pass

                composed_message_dict = await self.compose_message(
                    vacancy_from_admin_dict=vacancy_from_admin_dict,
                    one_profession=profession,
                    full=True,
                    message=vacancy,
                )
                composed_message_dict['id_admin_channel'] = ''
                composed_message_dict['id_admin_channel'] = last_admin_channel_id + 1
                composed_message_dict['it_was_sending_to_agregator'] = ''
                composed_message_dict['it_was_sending_to_agregator'] = vacancy_from_admin_dict['sended_to_agregator']

                # it needs the checking. It can be in DB. Do it after is better. At the moment writing ti admin las session. Does not matter to write it if it exists in DB

                try:
                    text = composed_message_dict['composed_message']
                    if len(text) > 4096:
                        text = text[:4093] + '...'
                    try:
                        await self.bot_aiogram.send_message(config['My_channels']['admin_channel'], text,
                                                            parse_mode='html', disable_web_page_preview=True)
                        last_admin_channel_id += 1
                    except Exception as e:
                        if 'Flood control exceeded' in str(e):
                            print(f'ERROR {e},\n PLEASE WAIT')
                            await asyncio.sleep(60 * 2)
                            # await self.bot_aiogram.send_message(config['My_channels']['admin_channel'], text,
                            #                                     parse_mode='html', disable_web_page_preview=True)
                            await helper.send_message(bot=self.bot_aiogram, chat_id=config['My_channels']['admin_channel'],
                                                      text=text, parse_mode='html', disable_web_page_preview=True)
                            last_admin_channel_id += 1

                    # -------------- it is for user's check -----------------------
                    with open(self.admin_check_file, 'a', encoding="utf-8") as file:
                        file.write(f"              NEXT                \n"
                                   f"-------- in callback admin -------\n"
                                   f"id admin_channel = {last_admin_channel_id}\n"
                                   f"id_admin_last_session_table = {vacancy[0]}\n"
                                   f"it was sending to agregator = {vacancy[19]}\n"
                                   f"title = {vacancy[2][:50]}\n"
                                   f"--------------------------------------------\n")
                    # ----------------------- end ----------------------------------

                    try:
                        self.db.push_to_admin_temporary(composed_message_dict)
                    except:
                        print('Error in push in db temporary table')

                    self.quantity_entered_to_admin_channel += 1
                    await asyncio.sleep(random.randrange(3, 4))
                except Exception as e:
                    await self.bot_aiogram.send_message(message.chat.id,
                                                        f"It hasn't been pushed to admin_channel : {e}")
                    await self.write_to_logs_error(
                        f"It hasn't been pushed to admin_channel\n{e}\n------------\n{vacancy[2] + vacancy[3]}\n-------------\n\n")
                    await asyncio.sleep(random.randrange(2, 3))
                # write to temporary DB (admin_temporary) id_admin_message and id in db admin_last_session

                n += 1
                await self.show_progress(message, n, length)

                # to say the customer about finish
            print('\nTransfer to admin has finished =======')
            markup = InlineKeyboardMarkup()
            push_full = InlineKeyboardButton(f'PUSH full to {profession.title()}',
                                             callback_data=f'PUSH full to {profession}')
            button_shorts = InlineKeyboardButton(f'PUSH shorts to {profession.title()}',
                                                 callback_data=f'PUSH shorts to {profession}')

            markup.row(push_full, button_shorts)
            await self.bot_aiogram.send_message(message.chat.id, f'{profession.title()} in the Admin channel\n'
                                                                          f'When you will ready, press button PUSH',
                                                reply_markup=markup)
            await asyncio.sleep(random.randrange(2, 3))
        else:
            await self.bot_aiogram.send_message(message.chat.id,
                                                f'There are have not any vacancies in {profession}\n'
                                                f'Please choose others', reply_markup=self.markup)
            await asyncio.sleep(random.randrange(2, 3))

def run(double=False, token_in=None):
    InviteBot(
        token_in=token_in,
        double=double
    ).main_invitebot()

def start_hardpushing():
    message = None
    bot = InviteBot()

    if not message:
        message = Message()
        message.chat = Chat()
        message.chat.id = variable.id_developer

    asyncio.run(bot.hard_pushing_by_schedule(
        message=message,
        profession_list=variable.profession_list_for_pushing_by_schedule
        )
    )



if __name__ == '__main__':
   run()