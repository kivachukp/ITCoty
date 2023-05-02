import re
import time
from datetime import datetime, timedelta
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from db_operations.scraping_db import DataBaseOperations
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters
from sites.write_each_vacancy_to_db import HelperSite_Parser
from settings.browser_settings import options, chrome_driver_path
from utils.additional_variables.additional_variables import sites_search_words, parsing_report_path, \
    admin_database, archive_database
from helper_functions.helper_functions import edit_message, send_message, send_file_to_user
from report.report_variables import report_file_path


class DesignerGetInformation:

    def __init__(self, **kwargs):

        self.report = kwargs['report'] if 'report' in kwargs else None
        self.search_words = kwargs['search_word'] if 'search_word' in kwargs else None
        self.bot_dict = kwargs['bot_dict'] if 'bot_dict' in kwargs else None
        self.find_parameters = FinderAddParameters()
        self.helper_parser_site = HelperSite_Parser(report=self.report)
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
        self.main_url = 'https://designer.ru'
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
        # -------------------- check what is current session --------------
        try:
            self.browser = webdriver.Chrome(
                executable_path=chrome_driver_path,
                options=options
            )
        except:
            self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        self.current_session = await self.helper_parser_site.get_name_session()
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'https://designer.ru/t/', disable_web_page_preview=True)
        self.browser.get('https://designer.ru/t/')
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        vacancy_exists_on_page = await self.get_link_message(self.browser.page_source)
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'designer.ru parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):
        soup = BeautifulSoup(raw_content, 'lxml')
        open_links = soup.find_all('div', class_='z_bx00kk__i')
        closed_links = soup.find_all('div', class_='z_b_1204897897897892734_b_close')
        self.list_links = list(set(open_links) - set(closed_links))
        if self.list_links:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id,
                                                               f'designer.ru:\nНайдено {len(self.list_links)} вакансий',
                                                               disable_web_page_preview=True)
            # --------------------- LOOP -------------------------
            self.written_vacancies = 0
            self.rejected_vacancies = 0
            await self.get_content_from_link()
            # ----------------------- the statistics output ---------------------------
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
                vacancy_url = link.find('a').get('href')
                vacancy_url = self.main_url + vacancy_url
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
                    soup = BeautifulSoup(self.browser.page_source, 'lxml')
                except Exception as ex:
                    found_vacancy = False
                    print(f"error in browser.get {ex}")

                if found_vacancy:
                    full_vacancy = soup.find('h1').text.split()
                    words_list = ['ищет', 'ищем', 'ищут', 'поиске', 'поисках']
                    vacancy = ''
                    for word in words_list:
                        if word in full_vacancy:
                            index_word = full_vacancy.index(word)
                            vacancy = full_vacancy[index_word + 1:]
                            raw_vacancy = ' '.join(vacancy)
                            vacancy = self.normalize_vacancy(raw_vacancy)
                            break
                    if not vacancy:
                        vacancy = 'дизайнер'

                    # get title --------------------------
                    title = vacancy

                    # get body --------------------------
                    body = soup.find('div', class_='z_dtl_text_block_v3').text.strip()
                    body = body.replace('\n\n', '\n')
                    body = re.sub(r'\<[A-Za-z\/=\"\-\>\s\._\<]{1,}\>', " ", body)

                    tags = ''

                    english = ''
                    if re.findall(r'[Аа]нглийский', tags) or re.findall(r'[Ee]nglish', tags):
                        english = 'English'

                    # get city --------------------------
                    try:
                        city = soup.find('div', class_='z_b_72194kjs___head_v2').find('div').find_all('div')[-1].text.strip()
                        match = re.findall(r"\([а-яА-Я\-\s]+\)", city)
                        if match:
                            city = match[0][1:-1]
                        else:
                            city = ''
                    except:
                        city = ''
                    # print('city = ', city)

                    # get company --------------------------
                    try:
                        company = soup.find('div', class_='z_b_72194kjs___intro_v2__www').text.strip()
                    except:
                        company = ''

                    # get salary --------------------------
                    try:
                        salary = soup.find('div', class_='z_b_72194kjs___intro_v2__salary').text.split()[1:]
                        salary = ' '.join(salary)
                    except:
                        salary = ''

                    # get experience --------------------------
                    # raw_job_format = soup.find_all('a', class_="ng-star-inserted")
                    job_format = ''
                    # for format in raw_job_format:
                    #     format = format.find('mat-basic-chip')
                    #     if format:
                    #         job_format += format.text
                    # try:
                    #     experience = soup.find('p', class_='vacancy-description-list-item').find('span').get_text()
                    # except:
                    #     experience = ''
                    # print('experience = ',experience)

                    # print('job_format = ', job_format)

                    contacts = ''

                    try:
                        date = soup.find('div', class_='z_b_72194kjs___head_v2').find('div').find('div').text.strip()
                    except:
                        date = ''
                    if date == 'сегодня':
                        date = datetime.today()
                    elif date == 'вчера':
                        date = datetime.today() - timedelta(days=1)
                    else:
                        date = self.normalize_date(date)

                    # ------------------------- search relocation ----------------------------
                    relocation = ''
                    if re.findall(r'[Rr]elocation', body):
                        relocation = 'релокация'

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
                        'chat_name': 'https://designer.ru/',
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
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=None)
        # -------------------- check what is current session --------------
        self.current_session = await self.helper_parser_site.get_name_session()
        self.list_links= [vacancy_url]
        await self.get_content_from_link()
        return self.response

    def normalize_date(self, date):
        convert = {
            'янв': '01',
            'фев': '02',
            'мар': '03',
            'апр': '04',
            'май': '05',
            'июн': '06',
            'июл': '07',
            'авг': '08',
            'сен': '09',
            'окт': '10',
            'ноя': '11',
            'дек': '12',
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
        text = re.sub(r'Аккаунт зарегистрирован с (публичной почты|email) \*@[a-z.]*[, не email компании!]{0,1}', '',
                      text)
        text = text.replace(f'\n', '')
        return text

    def normalize_vacancy(self, raw_vacancy):
        vacancy = re.sub(r'креативного', 'креативный', raw_vacancy)
        vacancy = re.sub(r'графического', 'графический', vacancy)
        vacancy = re.sub(r'коммуникационного', 'коммуникационный', vacancy)
        vacancy = re.sub(r'продуктового', 'продуктовый', vacancy)
        vacancy = re.sub(r'старшего', 'старший', vacancy)
        vacancy = re.sub(r'технического', 'технический', vacancy)
        vacancy = re.sub(r'главного', 'главный', vacancy)
        vacancy = re.sub(r'ведущего', 'ведущий', vacancy)

        vacancy = re.sub(r'дизайнера', 'дизайнер', vacancy)
        vacancy = re.sub(r'дира', 'дир', vacancy)
        vacancy = re.sub(r'архитектора', 'архитектор', vacancy)
        vacancy = re.sub(r'директора', 'директор', vacancy)
        vacancy = re.sub(r'аэрографиста', 'аэрографист', vacancy)
        vacancy = re.sub(r'супервайзера', 'супервайзер', vacancy)
        vacancy = re.sub(r'графика', 'график', vacancy)
        vacancy = re.sub(r'лида', 'лид', vacancy)
        vacancy = re.sub(r'фоторедактора', 'фоторедактор', vacancy)
        vacancy = re.sub(r'координатора', 'координатор', vacancy)
        vacancy = re.sub(r'иллюстратора', 'иллюстратор', vacancy)
        vacancy = re.sub(r'руководителя', 'руководитель', vacancy)
        vacancy = re.sub(r'конструктора', 'конструктор', vacancy)
        vacancy = re.sub(r'верстальщика', 'верстальщик', vacancy)
        vacancy = re.sub(r'художника', 'художник', vacancy)
        vacancy = re.sub(r'лого-мейкера', 'лого-мейкер', vacancy)

        vacancy = re.sub(r'ого\b', '', vacancy)
        vacancy = re.sub(r'eго\b', '', vacancy)

        if vacancy == raw_vacancy:
            vacancy = 'дизайнер'
        return vacancy

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

        self.count_message_in_one_channel += 1
