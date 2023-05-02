import re
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
from utils.additional_variables.additional_variables import sites_search_words, parsing_report_path, admin_database, \
    archive_database
from helper_functions.helper_functions import edit_message, send_message, send_file_to_user
from report.report_variables import report_file_path


class IngameJobGetInformation:

    def __init__(self, **kwargs):

        self.report = kwargs['report'] if 'report' in kwargs else None
        self.search_words = kwargs['search_word'] if 'search_word' in kwargs else None
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
        self.url_main = 'https://ru.ingamejob.com/ru'
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
        till=5
        for self.page_number in range(1, till):
            try:
                if self.bot_dict:
                    await self.bot.send_message(self.chat_id, f'https://ru.ingamejob.com/ru/jobs?page={self.page_number}',
                                          disable_web_page_preview=True)
                self.browser.get(f'https://ru.ingamejob.com/ru/jobs?page={self.page_number}')
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                vacancy_exists_on_page = await self.get_link_message(self.browser.page_source)
                if not vacancy_exists_on_page:
                    break
            except:
                break
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'ru.ingamejob.com/ru parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):

        links = []
        soup = BeautifulSoup(raw_content, 'lxml')

        self.list_links = soup.find_all('div', class_='col-12 p-0')
        if self.list_links:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id, f'ingamejob.com:\nНайдено {len(self.list_links)} вакансий на странице {self.page_number}', disable_web_page_preview=True)
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
        job_type = ''
        links = []
        soup = None
        self.found_by_link = 0
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
                    soup = BeautifulSoup(self.browser.page_source, 'lxml')
                except Exception as ex:
                    found_vacancy = False
                    print(f"error in browser.get {ex}")

                if found_vacancy:
                    # get vacancy ------------------------
                    try:
                        vacancy = soup.find('h1', class_='text-success').text
                    except:
                        vacancy = ''

                    # get title --------------------------
                    title = vacancy

                    # get body --------------------------
                    try:
                        body_content = soup.find_all('div', class_="job-view-single-section mb-3")
                        body = ''
                        for block in body_content:
                            for child in block.children:
                                if child.name == 'p':
                                    brs = child.find_all('br')
                                    for br in brs:
                                        br.replace_with('\n')
                                    body += (f'{child.get_text().strip()}\n')
                                elif child.name == 'h5':
                                    body += (f'\n{child.get_text().strip()}\n')
                                elif child.name == 'ul':
                                    lis = child.find_all('li')
                                    for li in lis:
                                        body += (f'-{li.get_text().strip()}\n')
                    except:
                        body = ''
                    # get date --------------------------
                    try:
                        date = soup.find(string=re.compile('Опубликовано')).text
                    except:
                        date = ''
                    if date:
                        date = self.convert_date(date)
                    # get company info --------------------------
                    company_info = soup.find('div', class_='job-view-lead-position-box col-sm-8').find('a',class_='job-view-lead-position-box')
                    company = company_info.get_text()
                    link = company_info.get('href')

                    #  get job details: type, salary, city, relocation
                    details = {}
                    all = soup.find('div', class_='col-sm-4').find_all('p', class_='m-0')

                    for i in all:
                        try:
                            tag = i.find('i', {'class': re.compile("text-muted la la")})
                            tag_name = tag['class'][2]
                            equals = i.text
                            equals = re.sub("^\s+|\n|\r|\s+$", '', equals)
                            details[tag_name] = equals
                        except Exception as e:
                            pass

                    level = details.get('la-area-chart', '')
                    salary = details.get('la-money', '')

                    city = ''
                    relocation = ''
                    job_types = []
                    job_types.append(details.get('la-briefcase', ''))

                    try:
                        job_details = details.get('la-map-marker', '').split(', ')
                        # print('job_details= ', job_details)
                        for i in job_details:
                            if i == 'Удаленная работа':
                                job_types.append(i)
                            elif i == 'Relocate':
                                relocation = i
                            else:
                                city += f'{i}'
                        job_type = ', '.join(job_types)

                    except Exception as e:
                        pass
                    contacts = ''
                    english = ''

                    # -------------------- compose one writting for one vacancy ----------------
                    results_dict = {
                        'chat_name': self.url_main,
                        'title': title,
                        'body': body,
                        'vacancy': vacancy,
                        'vacancy_url': vacancy_url,
                        'company': company,
                        # 'company_link': link,
                        'english': english,
                        'relocation': relocation,
                        'job_type': job_type,
                        'city': city,
                        'salary': salary,
                        'experience': '',
                        'time_of_public': date,
                        'contacts': contacts,
                        'session': self.current_session,
                        'level': level,
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

        self.bot.write_to_db_companies(companies)

    def convert_date(self, date):
        date_list=date.split(' ')
        date1=re.sub("^\s+|\n|\r|\s+$", '', date_list[1])
        if date1=='сегодня':
            date = datetime.now()-timedelta(days=1)
        elif date1=='вчера':
            date = datetime.now()
        else:
            par = date_list[2]
            if par in ['часа', 'часов']:
                date = datetime.now() - timedelta(hours=int(date1))
            elif par in ['дня', 'дней']:
                date = datetime.now() - timedelta(days=int(date1))
            elif par in ['недель', 'недели', 'неделю']:
                date = datetime.now() - timedelta(weeks=int(date1))
            else:
                date = datetime.now() - timedelta(days=30)
        return date



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
                if self.bot_dict:
                    self.current_message = await send_message(
                        bot=self.bot,
                        chat_id=self.chat_id,
                        text=new_text
                    )

        # print(f"\n{self.count_message_in_one_channel} from_channel remote-job.ru search {word}")
        self.count_message_in_one_channel += 1

    async def one_url(self, url):
        self.list_links = [url]
        self.current_session = await self.helper_parser_site.get_name_session()
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        await self.get_content_from_link()
