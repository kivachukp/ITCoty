import re
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from db_operations.scraping_db import DataBaseOperations
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters
from sites.write_each_vacancy_to_db import HelperSite_Parser
from settings.browser_settings import options, chrome_driver_path
from utils.additional_variables.additional_variables import sites_search_words, till, parsing_report_path, \
    admin_database, archive_database
from helper_functions.helper_functions import edit_message, send_message, send_file_to_user
from report.report_variables import report_file_path


class GeekGetInformation:

    def __init__(self, **kwargs):

        self.report = kwargs['report'] if 'report' in kwargs else None
        self.search_words = kwargs['search_word'] if 'search_word' in kwargs else sites_search_words
        self.bot_dict = kwargs['bot_dict'] if 'bot_dict' in kwargs else None
        self.helper_parser_site = HelperSite_Parser(report=self.report)
        self.find_parameters = FinderAddParameters()
        self.db = DataBaseOperations(report=self.report)
        self.page_number = 1
        self.current_message = None
        self.msg = None
        self.written_vacancies = 0
        self.rejected_vacancies = 0
        if self.bot_dict:
            self.bot = self.bot_dict['bot']
            self.chat_id = self.bot_dict['chat_id']
        self.browser = None
        self.main_url = 'https://geekjob.ru'
        self.count_message_in_one_channel = 1
        self.found_by_link = 0

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

        for self.page_number in range(1, till):
            try:
                if self.bot_dict:
                    await self.bot.send_message(self.chat_id, f'https://geekjob.ru/vacancies/{self.page_number}',
                                                disable_web_page_preview=True)
                self.browser.get(f'https://geekjob.ru/vacancies/{self.page_number}')
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                vacancy_exists_on_page = await self.get_link_message(self.browser.page_source)
                if not vacancy_exists_on_page:
                    break
            except:
                break
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'geekjob.ru parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):
        soup = BeautifulSoup(raw_content, 'lxml')

        self.list_links = soup.find_all('a', class_='title')
        if self.list_links:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id, f'geekjob.ru:\nНайдено {len(self.list_links)} вакансий на странице {self.page_number}', disable_web_page_preview=True)
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
        for link in self.list_links:
            found_vacancy = True
            try:
                vacancy_url = link.get('href')
                vacancy_url = self.main_url + vacancy_url
            except:
                vacancy_url = link

            # pre-checking by link
            check_vacancy_not_exists = self.db.check_exists_message_by_link_or_url(
                vacancy_url=vacancy_url,
                table_list=[admin_database, archive_database]
            )
            if check_vacancy_not_exists:
                links.append(vacancy_url)
                try:
                    self.browser.get(vacancy_url)
                    soup = BeautifulSoup(self.browser.page_source, 'lxml')
                except Exception as ex:
                    found_vacancy = False
                    print(f"error in browser.get {ex}")

                if found_vacancy:
                    # get vacancy ------------------------
                    try:
                        vacancy = soup.find('h1').get_text()
                    except:
                        vacancy = ''

                    if vacancy:
                        title = vacancy

                        try:
                            body = soup.find('div', id='vacancy-description').get_text()
                            body = body.replace('\n\n', '\n')
                            body = re.sub(r'\<[A-Za-z\/=\"\-\>\s\._\<]{1,}\>', " ", body)
                        except:
                            body = ''
                        # get tags --------------------------
                        level = ''
                        try:
                            level = soup.find('div', class_='category').get_text()
                        except:
                            pass

                        tags = ''
                        try:
                            tags = soup.find('div', class_="tags").get_text()
                            tags = f'{level}, {tags}'
                        except:
                            pass

                        english = ''
                        if re.findall(r'[Аа]нглийский', tags) or re.findall(r'[Ee]nglish', tags):
                            english = 'English'

                        # get city --------------------------
                        try:
                            city = soup.find('div', class_='location').get_text()
                        except:
                            city = ''
                        # get company --------------------------
                        try:
                            company = soup.find('h5', class_='company-name').get_text()
                            company = company.replace('\xa0', ' ')
                            if 'Прямой работодатель ' in company:
                                company = company.replace('Прямой работодатель ', '')
                            company = company.replace('\n', ' ')

                        except:
                            company = ''
                        # get salary --------------------------
                        try:
                            salary = soup.find('div', class_='jobinfo').find('span', class_='salary').get_text()
                        except:
                            salary = ''

                        # get experience --------------------------
                        try:
                            job_format = soup.find('div', class_='jobinfo').find('span', class_='jobformat').get_text()
                        except:
                            job_format = ''
                        # try:
                        #     experience = soup.find('p', class_='vacancy-description-list-item').find('span').get_text()
                        # except:
                        #     experience = ''
                        # print('experience = ',experience)

                        # print('job_format = ', job_format)

                        contacts = ''

                        try:
                            date = soup.find('div', class_="time").get_text()
                        except:
                            date = ''
                        if date:
                            date = self.normalize_date(date)

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

                        #-------------------- compose one writting for ione vacancy ----------------

                        results_dict = {
                            'chat_name': 'https://geekjob.ru/',
                            'title': title,
                            'body': body,
                            'vacancy': vacancy,
                            'vacancy_url': vacancy_url,
                            'company': company,
                            'company_link': '',
                            'english': english,
                            'relocation': relocation,
                            'job_type': job_format,
                            'city':city,
                            'salary':salary,
                            'experience': '',
                            'time_of_public':date,
                            'contacts':contacts,
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


    def normalize_date(self, date):
        convert = {
            'января': '01',
            'февраля': '02',
            'марта': '03',
            'апреля': '04',
            'мая': '05',
            'июня': '06',
            'июля': '07',
            'августа': '08',
            'сентября': '09',
            'октября': '10',
            'ноября': '11',
            'декабря': '12',
        }

        date = date.split(f' ')
        month = date[1]
        day = date[0]

        year = datetime.now().strftime('%Y')
        date = datetime(int(year), int(convert[month]), int(day), 12, 00, 00)

        return date

    def clean_company_name(self, text):
        text = re.sub('Прямой работодатель', '', text)
        text = re.sub(r'[(]{1} [a-zA-Z0-9\W\.]{1,30} [)]{1}', '', text)
        text = re.sub(r'Аккаунт зарегистрирован с (публичной почты|email) \*@[a-z.]*[, не email компании!]{0,1}', '', text)
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
