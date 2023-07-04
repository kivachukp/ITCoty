import asyncio
import configparser
import re

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
        self.report = kwargs['report'] if 'report' in kwargs else None
        self.db = DataBaseOperations(report=self.report)
        self.links = digest_links
        self.helper = helper
        self.limit_msg = 3

    async def main_start(self):

        print('digest_parsing_main_start')
        for url in self.links:
            messages = await self.get_all_messages(url)
            for message in messages:
                if not message.message:
                    pass
                else:
                    await self.parse_message(message, url)
        await self.print_digest_report()

    async def get_all_messages(self, channel):

        print('GET MESSAGES FROM', channel)
        offset_msg = 0
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
                limit=self.limit_msg, max_id=0, min_id=0,
                hash=0))
        except Exception as e:
            await self.bot_dict['bot'].send_message(
                self.bot_dict['chat_id'],
                f"Getting history:\n{str(e)}: {channel}\npause 25-30 seconds...",
                parse_mode="HTML",
                disable_web_page_preview=True)
            time.sleep(2)

        if not history:
            print(f'Not history for channel {channel}')
            await self.bot_dict['bot'].send_message(self.bot_dict['chat_id'], f'Not history for channel {channel}',
                                                    disable_web_page_preview=True)
        return history.messages

    async def db_check_add_single_vacancy(self, url):
        print(f"START CHECKING VACANCY {url}")
        url = url.strip()
        urls = [url]
        site_url = re.split(r'\/', url, maxsplit=3)
        domain = site_url[2]
        if domain in ['t.me', 'youtu.be', 'forms.gle', 'docviewer.yandex.by', 'drive.google.com', 'docs.google.com', 'www.youtube.com']:
            return None
        elif domain == 'hh.ru' or domain == 'nn.hh.ru':
            site_url[2] = 'spb.hh.ru'
            url_new = '/'.join(site_url)
            urls.append(url_new)
        for url in urls:
            for table in tables:
                response = self.db.get_all_from_db(
                    table_name=table,
                    field='title, body',
                    param=f"WHERE vacancy_url='{url}'"
                )
                if response:
                    status = "found in db by url"
                    return {'status': status, 'domain': domain}
        try:
            parser = parser_sites.get(domain)
            if parser:
                print('START PARSING VACANCY')
                parser_response = await parser(report=self.report, bot_dict=self.bot_dict).get_content_from_one_link(
                    url)
                if parser_response['response']['vacancy']:
                    status = f"{parser_response['response']['vacancy']}"
            else:
                status = "no parser"
            return {'status': status, 'domain': domain}
        except Exception as e:
            return e

    async def parse_message(self, message, channel):

        message_id = channel + '/' + str(message.id)
        urls = []
        for url_entity, inner_text in message.get_entities_text(MessageEntityTextUrl):
            url = url_entity.url
            res = re.findall(r'http[\:\/a-zA-Z0-9\.\=&_-]*', url)
            if res:
                urls.extend(res)
        urls.extend(re.findall(r'http[\:\/a-zA-Z0-9\.\=&_-]*', message.message))
        for url in urls:
            result = await self.db_check_add_single_vacancy(url)
            if result:
                status = result.get('status')
                domain = result.get('domain')
                if self.report:
                    self.report.parsing_report(
                        report_type='digest',
                        link_current_vacancy=url,
                        status=status, channel=channel,
                        message_id=message_id, site=domain
                    )
                    self.report.parsing_switch_next(report_type='digest', switch=True)

    async def print_digest_report(self):

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

