import asyncio
import re
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from db_operations.scraping_db import DataBaseOperations
from helper_functions import helper_functions
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters
from sites.sites_additional_utils.get_structure import get_structure_advance, get_structure_sviazi
from sites.write_each_vacancy_to_db import HelperSite_Parser
from settings.browser_settings import options, chrome_driver_path
from utils.additional_variables.additional_variables import sites_search_words, parsing_report_path, admin_database, \
    archive_database
from helper_functions.helper_functions import edit_message, send_message, send_file_to_user, get_field_for_shorts_sync
from report.report_variables import report_file_path


class SvyaziGetInformation:

    def __init__(self, **kwargs):

        self.report = kwargs['report'] if 'report' in kwargs else None
        self.search_words = kwargs['search_word'] if 'search_word' in kwargs else sites_search_words
        self.bot_dict = kwargs['bot_dict'] if 'bot_dict' in kwargs else None
        self.helper_parser_site = HelperSite_Parser(report=self.report)
        self.find_parameters = FinderAddParameters()
        self.db = DataBaseOperations(report=self.report)
        self.db_tables = None
        self.options = None
        self.page = None
        self.page_number = 1
        self.current_message = None
        self.msg = None
        self.written_vacancies = 0
        self.rejected_vacancies = 0
        if self.bot_dict:
            self.bot = self.bot_dict['bot']
            self.chat_id = self.bot_dict['chat_id']
        self.browser = None
        self.main_url = 'https://www.vseti.app'
        self.count_message_in_one_channel = 1
        self.found_by_link = 0
        self.response = None


    async def get_content(self, db_tables=None):
        self.db_tables = db_tables
        await self.get_info()
        if self.report:
            await self.report.add_to_excel()
            await send_file_to_user(
                bot=self.bot,
                chat_id=self.chat_id,
                path=report_file_path['parsing'],
            )
        self.browser.quit()

    async def get_info(self):
        try:
            self.browser = webdriver.Chrome(
                executable_path=chrome_driver_path,
                options=options
            )
        except:
            self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # -------------------- check what is current session --------------
        self.current_session = await self.helper_parser_site.get_name_session()
        try:
            if self.bot_dict:
                await self.bot.send_message(self.chat_id, f'https://www.vseti.app/jobs',
                                  disable_web_page_preview=True)
            self.browser.get(f'https://www.vseti.app/jobs')
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(1)
            await self.get_link_message(self.browser.page_source)
            # await asyncio.sleep(3)
        except:
            pass
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'www.vseti.app parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):
        soup = BeautifulSoup(raw_content, 'lxml')
        self.list_links = soup.find_all('div', role='listitem')
        if self.list_links:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id, f'www.vseti.app:\nНайдено {len(self.list_links)} вакансий', disable_web_page_preview=True)
            # --------------------- LOOP -------------------------
            self.written_vacancies = 0
            self.rejected_vacancies = 0
            await self.get_content_from_link()
            #----------------------- the statistics output ---------------------------
            self.written_vacancies = 0
            self.rejected_vacancies = 0
            return True
        else:
            return False

    async def get_content_from_link(self):
        links = []
        soup = None
        self.found_by_link = 0
        english = ''
        relocation = ''
        job_type = ''
        city = ''
        contacts = ''
        for link in self.list_links:
            found_vacancy = True
            try:
                vacancy_url = link.find('a').get('href')
            except:
                vacancy_url = link
            print(f"\n{vacancy_url}\n")

            # pre-checking by link
            check_vacancy_not_exists = self.db.check_exists_message_by_link_or_url(
                vacancy_url=vacancy_url,
                table_list=[admin_database, archive_database]
            )
            if check_vacancy_not_exists:
                links.append(vacancy_url)
                try:
                    self.browser.get(vacancy_url)
                    await asyncio.sleep(2)
                    soup = BeautifulSoup(self.browser.page_source, 'lxml')
                except Exception as ex:
                    found_vacancy = False
                    print(f"error in browser.get {ex}")

                if found_vacancy:
                    try:
                        vacancy = soup.find('h1', class_='heading-9').get_text()
                    except:
                        vacancy = ''

                    # get title --------------------------
                    title = vacancy

                    body = ''
                    try:
                        body_block = soup.find('div', class_='rich-text-block w-richtext')
                        structure_list = await get_structure_sviazi(body_block)

                        body_p = list(body_block.find_all('p'))
                        body_h = list(body_block.find_all('h4'))
                        body_ul = list(body_block.find_all('li'))

                        for element in structure_list:
                            if element == 'p':
                                if body_p[0].text:
                                    body += f"{body_p[0].text}\n\n"
                                body_p.pop(0)
                            if element == 'h':
                                if body_h[0].text:
                                    body += f"{body_h[0].text}\n"
                                body_h.pop(0)
                            if element == 'l':
                                if body_ul[0].text:
                                    body += f"{body_ul[0].text}\n"
                                body_ul.pop(0)
                    except:
                        pass

                    try:
                        date = soup.find_all('p', class_='paragraph-21 date-tag')
                        if len(date)>1:
                            date = date[1].text
                            date = date.split('/')
                            date = datetime(int(date[2]), int(date[1]), int(date[0]), 12, 0, 0)
                        else:
                            date = datetime.now()
                    except:
                        date = datetime.now()

                    try:
                        match_dict = {
                            'junior': "джун|jun",
                            'middle': "миддл|мидл|middle",
                            'senior': "сеньор|синьор|senior"
                        }
                        level = ''
                        level_list = soup.find_all('p', class_='paragraph-9')
                        for i in level_list:
                            if i.text:
                                for key in match_dict:
                                    match = re.findall(fr"{match_dict[key]}", i.text.lower())
                                    if match:
                                        level += f"{key}, "
                                level += f"{i.text.lower()}, "
                        level = level[:-2]
                    except:
                        pass

                    try:
                        content = soup.find_all('p', class_='paragraph-21')
                        content = content[-1].text
                        content = content.split(',')
                        if len(content) > 1:
                            job_type_raw = content[-1]
                            city = ', '.join(content[:-1])
                        else:
                            job_type_raw = content[0]
                        if job_type_raw:
                            if job_type_raw.lower() in ['удаленно', 'удалённо', 'удаленка', 'удалёнка']:
                                job_type += 'remote, '
                            if job_type_raw.lower() in ['релокация']:
                                job_type += 'relocation, '
                            if job_type_raw.lower() in ['офис', 'office']:
                                job_type += 'office, '
                        job_type = job_type[:-2]
                        pass
                    except:
                        pass

                    try:
                        salary = soup.find('p', class_='paragraph-22').text
                    except:
                        salary = ''

                    try:
                        company = soup.find('p', class_='paragraph-23').text
                    except:
                        company = ''

                    #-------------------- compose one writting for ione vacancy ----------------
                    results_dict = {
                        'chat_name': self.main_url,
                        'title': title,
                        'body': body,
                        'vacancy': vacancy,
                        'vacancy_url': vacancy_url,
                        'company': company,
                        'company_link': '',
                        'english': english,
                        'relocation': relocation,
                        'job_type': job_type,
                        'city': city,
                        'salary': salary,
                        'experience': '',
                        'time_of_public': date,
                        'contacts': contacts,
                        'session': self.current_session
                    }

                    response = await self.helper_parser_site.write_each_vacancy(results_dict)

                    await self.output_logs(
                        about_vacancy=response,
                        vacancy=vacancy,
                        vacancy_url=vacancy_url
                    )
                    self.response = response
            else:
                self.found_by_link += 1
                print("vacancy link exists")

        if self.found_by_link > 0:
            self.count_message_in_one_channel += self.found_by_link
            if self.bot_dict:
                self.current_message = await edit_message(
                    bot=self.bot,
                    text=f"\n---\nfound by link: {self.found_by_link}",
                    msg=self.current_message
                )

    async def get_content_from_one_link(self, vacancy_url):
        try:
            self.browser = webdriver.Chrome(
                executable_path=chrome_driver_path,
                options=options
            )
        except:
            self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # -------------------- check what is current session --------------
        self.current_session = await self.helper_parser_site.get_name_session()
        self.list_links= [vacancy_url]
        await self.get_content_from_link()
        self.browser.quit()
        return self.response

    async def compose_in_one_file(self):
        hiring = []
        link = []
        contacts = []

        for i in range(1, 48):
            excel_data_df = pd.read_excel(f'./../messages/geek{i}.xlsx', sheet_name='Sheet1')

            hiring.extend(excel_data_df['hiring'].tolist())
            link.extend(excel_data_df['hiring_link'].tolist())
            contacts.extend(excel_data_df['contacts'].tolist())

        df = pd.DataFrame(
            {
            'hiring': hiring,
            'access_hash': link,
            'contacts': contacts,
            }
        )

        df.to_excel(f'all_geek.xlsx', sheet_name='Sheet1')

    async def write_to_db_table_companies(self):
        excel_data_df = pd.read_excel('all_geek.xlsx', sheet_name='Sheet1')
        companies = excel_data_df['hiring'].tolist()
        links = excel_data_df['access_hash'].tolist()

        companies = set(companies)

        self.db.write_to_db_companies(companies)


    async def output_logs(self, about_vacancy, vacancy, word=None, vacancy_url=None):
        additional_message = ''

        if about_vacancy['response']['vacancy'] in ['found in db by link', 'found in db by title-body']:
            additional_message = f'-exists in db\n\n'
            self.rejected_vacancies += 1

        elif about_vacancy['response']['vacancy'] == 'no vacancy by anti-tags':
            additional_message = f'-ANTI-TAG by vacancy\n\n'
            self.rejected_vacancies += 1

        elif about_vacancy['response']['vacancy'] == 'written to db':
            if about_vacancy['profession']:
                profession = about_vacancy['profession']
                prof_str = ", ".join(profession['profession'])
                additional_message = f"<b>+w: {prof_str}</b>\n{vacancy_url}\n{profession['tag']}\n{profession['anti_tag']}\n\n"
                self.written_vacancies += 1
            else:
                additional_message = 'written to db'
                self.written_vacancies += 1

        if self.bot_dict:
            if len(f"{self.current_message}\n{self.count_message_in_one_channel}. {vacancy}\n{additional_message}") < 4096:
                new_text = f"\n{self.count_message_in_one_channel}. {vacancy}\n{additional_message}"

                self.current_message = await edit_message(
                    bot=self.bot,
                    text=new_text,
                    msg=self.current_message
                )
            else:
                new_text = f"{self.count_message_in_one_channel}. {vacancy}\n{additional_message}"
                self.current_message = await send_message(
                    bot=self.bot,
                    chat_id=self.chat_id,
                    text=new_text
                )

        # print(f"\n{self.count_message_in_one_channel} from_channel remote-job.ru search {word}")
        self.count_message_in_one_channel += 1
