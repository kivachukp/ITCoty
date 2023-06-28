import asyncio
import configparser
import re
import random

from helper_functions import helper_functions as helper
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageEntityTextUrl
import time
from sites.parsing_sites_runner import parser_sites
from utils.additional_variables.additional_variables import table_list_for_checking_message_in_db as tables
from db_operations.scraping_db import DataBaseOperations
from utils.tg_channels.links import digest_links
from helper_functions import helper_functions as helper

config = configparser.ConfigParser()
config.read("./settings/config.ini")


class DigestParser():

    def __init__(self, **kwargs):

        self.client = kwargs['client'] if 'client' in kwargs else None
        self.bot_dict = kwargs['bot_dict'] if 'bot_dict' in kwargs else None
        self.bot = self.bot_dict['bot']
        self.chat_id = self.bot_dict['chat_id']
        self.channel = 'https://t.me/young_june'
        self.report = kwargs['report'] if 'report' in kwargs else None
        self.db = DataBaseOperations(report=self.report)
        self.links = digest_links
        self.helper = helper

    async def get_all_messages(self, channel, limit_msg):

        print('GET MESSAGES FROM', channel)

        self.count_message_in_one_channel = 1
        block = False
        offset_msg = 0  # номер записи, с которой начинается считывание
        # limit_msg = 1   # максимальное число записей, передаваемых за один раз
        all_messages = []  # список всех сообщений
        total_messages = 0
        total_count_limit = limit_msg  # значение 0 = все сообщения
        history = None

        new_text = f"<em>channel {channel}</em>"

        self.msg = await helper.send_message(
            bot=self.bot_dict['bot'],
            chat_id=self.bot_dict['chat_id'],
            text=new_text
        )


        try:
            history = await self.client(GetHistoryRequest(
                peer=channel,
                offset_id=offset_msg,
                offset_date=None, add_offset=0,
                limit=limit_msg, max_id=0, min_id=0,
                hash=0))
        except Exception as e:
            await self.bot_dict['bot'].send_message(
                self.bot_dict['chat_id'],
                f"Getting history:\n{str(e)}: {channel}\npause 25-30 seconds...",
                parse_mode="HTML",
                disable_web_page_preview=True)
            time.sleep(2)

        # if not history.messages:
        if not history:
            print(f'Not history for channel {channel}')
            await self.bot_dict['bot'].send_message(self.bot_dict['chat_id'], f'Not history for channel {channel}',
                                                    disable_web_page_preview=True)
        messages = history.messages
        print('MESSAGES', messages)
        for message in messages:
            print('MESSAGE', 'ID=', message.id, message)
            print('MESSAGE.MESSAGE', message.message)
            if not message.message:  # если сообщение пустое, например "Александр теперь в группе"
                pass
            else:
                all_messages.append(message.to_dict())
                await self.parse_message(message, channel)
        print(all_messages)
        print('pause 5-12 sec.')
        await asyncio.sleep(random.randrange(5, 12))

    async def db_check_add_single_vacancy(self, url, channel, message_id):
        print(f"START CHECKING VACANCY {url}")
        url = url.strip()
        urls = [url]
        site_url = re.split(r'\/', url, maxsplit=3)
        domain = site_url[2]
        if domain == 'hh.ru' or domain == 'nn.hh.ru':
            site_url[2] = 'spb.hh.ru'
            url_new = '/'.join(site_url)
            urls.append(url_new)
        for url in urls:
            for pro in tables:
                print(pro)
                response = self.db.get_all_from_db(
                    table_name=pro,
                    field='title, body',
                    param=f"WHERE vacancy_url='{url}'"
                )
                print(response)
                if response:
                    text = f"Vacancy FOUND in {pro} table\n{response[0][0][0:40]}"
                    status = "found in db by url"
                    print(text)
                    if self.report:
                        self.report.parsing_report(
                            report_type = 'digest',
                            link_current_vacancy=url,
                            status=status, channel=channel, message_id=message_id, site=domain
                        )
                        self.report.parsing_switch_next(report_type='digest', switch=True)
                        return text
        try:
            parser = parser_sites.get(domain)
            if parser:
                print('START PARSING VACANCY')
                parser_response = await parser(report=self.report, bot_dict=self.bot_dict).get_content_from_one_link(
                    url)
                text = ''
                if parser_response['response_dict']:
                    if parser_response['response']['vacancy']:
                        text += f"Status: {parser_response['response']['vacancy'].capitalize()}\n"
                    text += f"url: {parser_response['response_dict']['response_dict']['vacancy_url'] if 'vacancy_url' in parser_response['response_dict']['response_dict'] else '-'}\n"
                    text += f"title: {parser_response['response_dict']['response_dict']['title'][:40]}\n"
                    text += f"profession: {parser_response['response_dict']['response_dict']['profession']}\n"
                    text += f"tags: {parser_response['response_dict']['response_dict']['full_tags'] if parser_response['response_dict']['response_dict']['full_tags'] else '-'}\n"
                    text += f"anti_tags: {parser_response['response_dict']['response_dict']['full_anti_tags'] if parser_response['response_dict']['response_dict']['full_anti_tags'] else '-'}\n"
                else:
                    text = f"{parser_response['response']['vacancy']}\n" \
                           f"profession: {parser_response['profession']['profession'] if parser_response['profession']['profession'] else '-'}\n" \
                           f"tags: {parser_response['profession']['tag'] if parser_response['profession']['tag'] else '-'}\n" \
                           f"anti_tags: {parser_response['profession']['anti_tag'] if parser_response['profession']['anti_tag'] else '-'}"
                status = f"{parser_response['response']['vacancy']}"
                print(text)
                if self.report:
                    self.report.parsing_report(
                        report_type='digest',
                        link_current_vacancy=url,
                        status=status, channel=channel, message_id=message_id, site=domain
                    )
            else:
                text = f"NO PARSER for {domain}"
                status = "no parser"
            print(text)
            if self.report:
                self.report.parsing_report(
                    report_type='digest',
                    link_current_vacancy=url,
                    status=status, channel=channel,
                    message_id=message_id, site=domain
                )
            if self.report:
                self.report.parsing_switch_next(report_type='digest', switch=True)
            return text
        except Exception as e:
            return e

    async def parse_message(self, message, channel):
        print('START parsing message')
        print (message.message)
        message_idi = str(message.id)
        message_id = channel + '/' + message_idi

        urls = []
        for url_entity, inner_text in message.get_entities_text(MessageEntityTextUrl):
            url = url_entity.url
            print(url)
            if '/t.me/' in url or 'youtube' in url or 'forms.gle' in url:
                pass
            else:
                res = re.findall(r'http[\:\/a-zA-Z0-9\.\=&-]*', url)
                if res:
                    urls += res
        print(urls)
        if not urls:
            print('NO URL ENTITIES')
            urls = re.findall(r'http[\:\/a-zA-Z0-9\.\=&-]*', message.message)
            print(urls)
        for i in urls:
            print(i)
            result = await self.db_check_add_single_vacancy(i, channel, message_id)


    async def main_start(self, limit_msg=3):

        print('main_start')
        print(self.links)
        for url in self.links:
            print(url)
            messages = await self.get_all_messages(url, limit_msg)
            print(messages)

        print('READY TO PRINT REPORT')
        if self.report and self.helper:
            try:
                await self.report.add_to_excel(report_type='digest')
                await self.helper.send_file_to_user(
                    bot=self.bot,
                    chat_id=self.chat_id,
                    path=self.report.keys.report_file_path['digest'],
                )
            except Exception as ex:
                print(f"Error: {ex}")


async def main(report, client, bot_dict, action='get_message'):
    get_messages = DigestParser(client=client, bot_dict=bot_dict, report=report)
    print('START')
    await get_messages.main_start(digest_links, limit_msg=20, action=action)  # get_participants get_message
