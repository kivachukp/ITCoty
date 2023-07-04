import re
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from db_operations.scraping_db import DataBaseOperations
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters
from sites.write_each_vacancy_to_db import HelperSite_Parser
from settings.browser_settings import options, chrome_driver_path
from utils.additional_variables.additional_variables import sites_search_words, parsing_report_path, admin_database, \
    archive_database
from helper_functions.helper_functions import edit_message, send_message, send_file_to_user
from patterns.data_pattern._data_pattern import cities_pattern, params
from report.report_variables import report_file_path
from helper_functions import helper_functions as helper

class HabrGetInformation:

    def __init__(self, **kwargs):

        self.report = kwargs['report'] if 'report' in kwargs else None
        self.search_word = kwargs['search_word'] if 'search_word' in kwargs else sites_search_words
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
        self.url_main = 'https://career.habr.com'
        self.count_message_in_one_channel = 1
        self.found_by_link = 0
        self.helper = helper

    async def get_content(self, db_tables=None):
        self.db_tables = db_tables
        try:
            await self.get_info()
        except Exception as ex:
            print(f"Error: {ex}")
            if self.bot:
                await self.bot.send_message(self.chat_id, f"Error: {ex}")

        if self.report and self.helper:
            try:
                await self.report.add_to_excel()
                await self.helper.send_file_to_user(
                    bot=self.bot,
                    chat_id=self.chat_id,
                    path=self.report.keys.report_file_path['parsing'],
                )
            except Exception as ex:
                print(f"Error: {ex}")
                if self.bot:
                    await self.bot.send_message(self.chat_id, f"Error: {ex}")
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

        till = 13
        for self.page_number in range(1, till):
            try:
                if self.bot_dict:
                    await self.bot.send_message(self.chat_id, f'https://career.habr.com/vacancies?page={self.page_number}&sort=date&type=all',
                                          disable_web_page_preview=True)
                self.browser.get(f'https://career.habr.com/vacancies?page={self.page_number}&sort=date&type=all')
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                vacancy_exists_on_page = await self.get_link_message(self.browser.page_source)
                if not vacancy_exists_on_page:
                    break
            except:
                break
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'career.habr.com parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):
        soup = BeautifulSoup(raw_content, 'lxml')
        self.list_links = soup.find_all('div', class_='vacancy-card')
        if self.list_links:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id, f'career.habr.com:\nНайдено {len(self.list_links)} вакансий на странице {self.page_number}', disable_web_page_preview=True)
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

    async def get_content_from_link(self, return_raw_dictionary=False):
        links = []
        soup = None
        self.found_by_link = 0
        for link in self.list_links:
            found_vacancy = True
            try:
                vacancy_url = link.find('a').get('href')
                vacancy_url = self.url_main + vacancy_url
            except:
                vacancy_url = link
            print(f"\n{vacancy_url}")

            # pre-checking by link
            check_vacancy_not_exists = self.db.check_exists_message_by_link_or_url(
                vacancy_url=vacancy_url,
                table_list=[admin_database, archive_database]
            )
            if check_vacancy_not_exists or not check_vacancy_not_exists and return_raw_dictionary:
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
                        vacancy = soup.find('div', class_='page-title').get_text()
                    except:
                        vacancy = ''
                    # print('title = ', vacancy)

                    # get title --------------------------
                    title = vacancy
                    # print('title = ',title)

                    # get body --------------------------
                    try:
                        body = 'Описание вакансии:\n'
                        body_content = soup.find('div', class_='vacancy-description__text')
                        structure = await self.get_structure(body_content)
                        body_content_list_p = body_content.find_all('p')
                        body_content_list_ul = body_content.find_all('ul')
                        for element in structure:
                            if element == 'p':
                                try:
                                    temp = body_content_list_p[0].get_text()
                                    body += f"\n{temp}\n"
                                    # print('\n', temp)
                                    body_content_list_p.pop(0)
                                except:
                                    break
                            if element == 'ul':
                                temp = body_content_list_ul[0]
                                for li in temp:
                                    if li != ' ' and li:
                                        body += f"-{li.get_text()}\n"
                                        # print('-', li.get_text())
                                body_content_list_ul.pop(0)
                    except:
                        pass

                    types_job = []
                    header_content = soup.find_all('div', class_='content-section')

                    salary = ''
                    tags = ''
                    job_type = ''
                    for element in header_content:
                        if "Требования" in element.text:
                            tags = element.text.replace('Требования ', '')
                        if "Местоположение и тип занятости" in element.text:
                            job_type = element.text.replace('Местоположение и тип занятости ', '')
                        if "Зарплата" in element.text:
                            salary = element.text.replace('Зарплата ', '')

                    if tags:
                        body = f"{tags}\n{body}"

                    try:
                        company = soup.find('div', class_='company_name').find('a').get_text()
                    except:
                        company = ''

                    time_of_public = ''
                    try:
                        time_of_public = soup.find('div', class_='vacancy-header__date').get_text()
                        time_of_public = self.normalize_date(time_of_public)
                    except Exception as e:
                        pass
                    # print('time_of_public after = ', time_of_public)

                    contacts = ''
                    experience = ''

                    # ------------------------- search relocation ----------------------------
                    relocation = ''
                    if re.findall(r'[Рр]елокация', body):
                        relocation = 'релокация'

                    # ------------------------- search city ----------------------------
                    city = ''
                    try:
                        city_list = link.find_all('span', class_='inline-list')
                        for i in city_list:
                            f_href = ''
                            f = i.find('a')
                            try:
                                f_href = f.get('href')
                            except:
                                pass
                            if 'city' in f_href:
                                city = f.text
                                break
                    except:
                        pass
                    # ------------------------- search english ----------------------------
                    english = ''
                    for item in params['english_level']:
                        match = re.findall(rf"{item}", body)
                        if match:
                            for i in match:
                                english += f"{i} "

                    english_additional = ''
                    for item in params['english_level']:
                        match1 = re.findall(rf"{item}", body)
                        match2 = re.findall(rf"{item}", title)
                        if match1:
                            for i in match1:
                                english_additional += f"{i} "
                        if match2:
                            for i in match2:
                                english_additional += f"{i} "

                    if english and ('upper' in english_additional or 'b1' in english_additional or 'b2' in english_additional \
                            or 'internediate' in english_additional or 'pre' in english_additional):
                        english = english_additional
                    elif not english and english_additional:
                        english = english_additional

                    self.db.write_to_db_companies([company])

                    #-------------------- compose one writting for ione vacancy ----------------

                    results_dict = {
                        'chat_name': 'https://career.habr.com/',
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
                        'experience': experience,
                        'time_of_public': time_of_public,
                        'contacts': contacts,
                        'session': self.current_session
                    }

                    if not return_raw_dictionary:
                        response = await self.helper_parser_site.write_each_vacancy(results_dict)

                        await self.output_logs(
                            about_vacancy=response,
                            vacancy=vacancy,
                            vacancy_url=vacancy_url
                        )
                        self.response = response
                    else:
                        self.response = results_dict
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

    async def get_content_from_one_link(self, vacancy_url, return_raw_dictionary=False):
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
        await self.get_content_from_link(return_raw_dictionary)
        self.browser.quit()
        return self.response


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
            if self.bot_dict:
                new_text = f"\n{self.count_message_in_one_channel}. {vacancy}\n{additional_message}"
                self.current_message = await edit_message(
                    bot=self.bot,
                    text=new_text,
                    msg=self.current_message
                )
        else:
            if self.bot_dict:
                new_text = f"{self.count_message_in_one_channel}. {vacancy}\n{additional_message}"
                self.current_message = await send_message(
                    bot=self.bot,
                    chat_id=self.chat_id,
                    text=new_text
                )

        # print(f"\n{self.count_message_in_one_channel} from_channel remote-job.ru search {word}")
        self.count_message_in_one_channel += 1

    def normalize_text(self, text):
        text = str(text)
        text = text.replace('<div id="vacancy-description">', '')
        text = text.replace('<br>', f'\n').replace('<br/>', '')
        text = text.replace('<p>', f'\n').replace('</p>', '')
        text = text.replace('<li>', f'\n\t- ').replace('</li>', '')
        text = text.replace('<strong>', '').replace('</strong>', '')
        text = text.replace('<div>', '').replace('</div>', '')
        text = text.replace('<h4>', f'\n').replace('</h4>', '')
        text = text.replace('<ul>', '').replace('</ul>', '')
        text = text.replace('<i>', '').replace('</i>', '')
        text = text.replace('<ol>', '').replace('</ol>', '')

        return text

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

    async def get_structure(self, text):

        text = str(text)
        structure_list = []
        index_p = 0


        while index_p != -1:
            index_li = text.find('<ul>')
            index_p = text.find('<p>')

            if index_p < index_li and index_p != -1:
                structure_list.append('p')
                text = text[index_p + 2:]
            else:
                if index_li != -1:
                    structure_list.append('ul')
                    text = text[index_li + 2:]
                else:
                    structure_list.append('p')
                    text = text[index_p + 2:]

        return structure_list


