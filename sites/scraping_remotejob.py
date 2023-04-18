import re
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from db_operations.scraping_db import DataBaseOperations
from sites.write_each_vacancy_to_db import HelperSite_Parser
from settings.browser_settings import options, chrome_driver_path
from utils.additional_variables.additional_variables import sites_search_words, parsing_report_path
from helper_functions.helper_functions import edit_message, send_message, send_file_to_user
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters
from report.report_variables import report_file_path


class RemoteJobGetInformation:

    def __init__(self, **kwargs):

        self.report = kwargs['report'] if 'report' in kwargs else None
        self.search_word = kwargs['search_word'] if 'search_word' in kwargs else sites_search_words
        self.bot_dict = kwargs['bot_dict'] if 'bot_dict' in kwargs else None
        self.helper_parser_site = HelperSite_Parser(report=self.report)
        self.db = DataBaseOperations(report=self.report)
        self.find_parameters = FinderAddParameters()
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
        self.main_url = 'https://remote-job.ru'

    async def get_content(self, db_tables=None):
        self.db_tables = db_tables
        self.count_message_in_one_channel = 1
        await self.get_info()
        await self.report.add_to_excel()
        await send_file_to_user(
            bot=self.bot,
            chat_id=self.chat_id,
            path=report_file_path['parsing'],
        )
        self.browser.quit()

    async def get_info(self):
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # -------------------- check what is current session --------------
        self.current_session = await self.helper_parser_site.get_name_session()
        while True:
            try:
                await self.bot.send_message(self.chat_id,
                                            f'https://remote-job.ru/search?search%5Bquery%5D=&search%5BsearchType%5D=vacancy&period=1&page={self.page_number}',
                                            disable_web_page_preview=True)
                self.browser.get(
                    f'https://remote-job.ru/search?search%5Bquery%5D=&search%5BsearchType%5D=vacancy&period=1&page={self.page_number}')
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                vacancy_exists_on_page = await self.get_link_message(self.browser.page_source)
                self.page_number += 1
                if not vacancy_exists_on_page:
                    break
            except:
                break
        await self.bot.send_message(self.chat_id, 'remote-job.ru parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):

        links = []
        soup = BeautifulSoup(raw_content, 'lxml')

        self.list_links = soup.find_all('div', class_='vacancy_item')
        if self.list_links:
            self.current_message = await self.bot.send_message(self.chat_id,
                                                               f'remote-job.ru:\nНайдено {len(self.list_links)} вакансий на странице {self.page_number}',
                                                               disable_web_page_preview=True)

            # --------------------- LOOP -------------------------
            self.written_vacancies = 0
            self.rejected_vacancies = 0

            # for i in list_links:
            #     await self.get_content_from_link(i, links)
            await self.get_content_from_link()
            # ----------------------- the statistics output ---------------------------
            self.written_vacancies = 0
            self.rejected_vacancies = 0
            return True
        else:
            return False

    async def get_content_from_link(self):
        links = []
        for link in self.list_links:
            vacancy_url = link.find('a').get('href')
            vacancy_url = self.main_url + vacancy_url
            # print('vacancy_url = ', vacancy_url)
            links.append(vacancy_url)

            # print('self.broswer.get(vacancy_url)')
            # await self.bot.send_message(self.chat_id, vacancy_url, disable_web_page_preview=True)
            # self.browser = browser
            self.browser.get(vacancy_url)
            # self.browser.get('https://google.com')
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # print('soup = BeautifulSoup(self.browser.page_source, \'lxml\')')
            soup = BeautifulSoup(self.browser.page_source, 'lxml')
            # print('passed soup = BeautifulSoup(self.browser.page_source, \'lxml\')')

            # get vacancy ------------------------
            vacancy = soup.find('h1').text.split()
            vacancy = ' '.join(vacancy)
            # print('vacancy = ', vacancy)

            # get title --------------------------
            title = vacancy
            # print('title = ', title)

            # get body --------------------------
            body = soup.find('div', class_='row p-y-3').find('div', class_='col-md-12').text.split()
            body = ' '.join(body)
            body = body.replace('\n\n', '\n')
            body = body.replace('Откликнуться на вакансию', '')
            body = re.sub(r'\<[A-Za-z\/=\"\-\>\s\._\<]{1,}\>', " ", body)
            # print('body = ', body)

            # get tags --------------------------
            level = ''
            # try:
            #     level = soup.find('div', class_='category').get_text()
            # except:
            #     pass

            tags = ''
            # try:
            #     tags = soup.find('div', class_="tags").get_text()
            #     tags = f'{level}, {tags}'
            # except:
            #     pass
            # print('tags = ', tags)

            english = ''
            if re.findall(r'[Аа]нглийский', tags) or re.findall(r'[Ee]nglish', tags):
                english = 'English'

            # get city --------------------------
            try:
                city = soup.find('div', class_='location').get_text()
            except:
                city = ''
            # print('city = ', city)

            # get company --------------------------
            try:
                company = soup.find('div', class_='col-md-12 m-t-1').find('h4').text.strip()
                company = company.replace('\xa0', ' ')
                if 'Прямой работодатель ' in company:
                    company = company.replace('Прямой работодатель ', '')
                company = company.replace('\n', ' ')

            except:
                company = ''
            # print('company = ', company)

            # get salary --------------------------
            try:
                salary = soup.find('div', class_='panel-heading').find('div', class_='col-md-4').find('b').text.strip()
                # salary = salary.strip().split()
                # salary = ' '.join(salary)
                salary = self.find_parameters.salary_to_set_form(text=salary)
                if salary[0]:
                    salary = ", ".join(salary)
            except:
                salary = ''
            # print('salary = ', salary)

            # get experience --------------------------
            # job_format = soup.find('div', class_='jobinfo').find('span', class_='jobformat').get_text()
            job_format = ''
            try:
                experience = soup.find('div', class_='panel-heading').find_all('div', class_='col-md-4')[1].find('b').text
            except:
                experience = ''
            # print('experience = ', experience)

            # print('job_format = ', job_format)

            contacts = ''

            try:
                date = datetime.today()
            except:
                date = ''
            # if date:
            #     date = self.normalize_date(date)
            # print('date = ', date)

            # ------------------------- search relocation ----------------------------
            relocation = ''
            if re.findall(r'[Рр]елокация', body):
                relocation = 'релокация'

            # ------------------------- search city ----------------------------
            # city = ''
            # for key in cities_pattern:
            #     for item in cities_pattern[key]:
            #         match = re.findall(rf"{item}", body)
            #         if match and key != 'others':
            #             for i in match:
            #                 city += f"{i} "

            # ------------------------- search english ----------------------------
            # english_additional = ''
            # for item in params['english_level']:
            #     match1 = re.findall(rf"{item}", body)
            #     match2 = re.findall(rf"{item}", tags)
            #     if match1:
            #         for i in match1:
            #             english_additional += f"{i} "
            #     if match2:
            #         for i in match2:
            #             english_additional += f"{i} "
            #
            # if english and ('upper' in english_additional or 'b1' in english_additional or 'b2' in english_additional \
            #         or 'internediate' in english_additional or 'pre' in english_additional):
            #     english = english_additional
            # elif not english and english_additional:
            #     english = english_additional

            self.db.write_to_db_companies([company])

            # -------------------- compose one writting for ione vacancy ----------------

            results_dict = {
                'chat_name': 'https://remote-job.ru',
                'title': title,
                'body': body,
                'vacancy': vacancy,
                'vacancy_url': vacancy_url,
                'company': company,
                'company_link': '',
                'english': english,
                'relocation': relocation,
                'job_type': job_format,
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

    def clean_company_name(self, text):
        text = re.sub('Прямой работодатель', '', text)
        text = re.sub(r'[(]{1} [a-zA-Z0-9\W\.]{1,30} [)]{1}', '', text)
        text = re.sub(r'Аккаунт зарегистрирован с (публичной почты|email) \*@[a-z.]*[, не email компании!]{0,1}', '',
                      text)
        text = text.replace(f'\n', '')
        return text

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
