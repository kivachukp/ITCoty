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
from utils.additional_variables.additional_variables import sites_search_words, admin_database, archive_database
from helper_functions.helper_functions import edit_message, send_message, send_file_to_user
from utils.additional_variables import additional_variables as variables
from report.report_variables import report_file_path


class RemotehubGetInformation:

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
        self.main_url = 'https://remotehub.com'
        self.count_message_in_one_channel = 1
        self.found_by_link = 0
        self.response = None

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
        try:
            self.browser = webdriver.Chrome(
                executable_path=chrome_driver_path,
                options=options
            )
        except:
            self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # -------------------- check what is current session --------------
        self.current_session = await self.helper_parser_site.get_name_session()
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, f'https://www.remotehub.com/jobs/search?sort_type=2',
                                    disable_web_page_preview=True)
        self.browser.get(f'https://www.remotehub.com/jobs/search?sort_type=2')
        SCROLL_PAUSE_TIME = 3

        last_height = self.browser.execute_script("return document.body.scrollHeight")
        till = 0
        while till <= 10:
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            till += 1
        await self.get_link_message(self.browser.page_source)
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'remotehub.com parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):
        soup = BeautifulSoup(raw_content, 'lxml')

        self.list_links = soup.find_all('smp-landings-entity', class_='ng-star-inserted')
        if self.list_links:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id,
                                                                   f'remotehub.com:\nНайдено {len(self.list_links)} вакансий',
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
                vacancy_url = link.find('a', class_='entity-detailed-link').get('href')
                vacancy_url = self.main_url + vacancy_url
            except:
                vacancy_url = link

            print(f"\n{vacancy_url}")

            # pre-checking by link
            check_vacancy_not_exists = self.db.check_exists_message_by_link_or_url(
                vacancy_url=vacancy_url,
                table_list=[admin_database, archive_database]
            )
            if check_vacancy_not_exists:
                links.append(vacancy_url)

                try:
                    self.browser.get(vacancy_url)
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    soup = BeautifulSoup(self.browser.page_source, 'lxml')
                except Exception as ex:
                    found_vacancy = False
                    print(f"error in browser.get {ex}")

                if found_vacancy:
                    vacancy = ''
                    try:
                        vacancy = soup.find('h1', class_='title mat-headline').text
                    except Exception:
                        pass

                    if vacancy:
                        title = vacancy

                        body = ''
                        try:
                            body = soup.find('span', class_='mat-subheading-2').text
                            body = body.replace('\n\n', '\n')
                            body = re.sub(r'\<[A-Za-z\/=\"\-\>\s\._\<]{1,}\>', " ", body)
                        except:
                            pass
                        if body:
                            tags = ''
                            try:
                                raw_tags = soup.find_all('span', class_="truncate muted-2")
                                tags = ''
                                for tag in raw_tags:
                                    tags += tag.text
                            except:
                                pass

                            english = ''
                            if tags:
                                if re.findall(r'[Аа]нглийский', tags) or re.findall(r'[Ee]nglish', tags):
                                    english = 'English'

                            try:
                                city = soup.find('span', class_='mat-body-2 text').text
                            except:
                                city = ''

                            try:
                                company = soup.find('div', class_='account-name mat-body-2').text
                            except:
                                company = ''

                            # get salary --------------------------
                            try:
                                salary = soup.find('div', class_='price ng-star-inserted')
                                if not salary:
                                    salary = soup.find('span', class_='label muted ng-star-inserted')
                                salary = salary.text
                                # salary = self.find_parameters.salary_to_set_form(text=salary)
                                # if salary[0]:
                                #     salary = ", ".join(salary)
                            except:
                                salary = ''

                            raw_job_format = ''
                            try:
                                raw_job_format = soup.find_all('a', class_="ng-star-inserted")
                            except:
                                pass
                            job_format = ''
                            format_find = ''
                            if raw_job_format:
                                for format in raw_job_format:
                                    try:
                                        format_find = format.find('mat-basic-chip')
                                    except:
                                        pass
                                    if format_find:
                                        try:
                                            job_format += format_find.text
                                        except:
                                            pass

                            contacts = ''
                            try:
                                date = soup.find('div', class_="mat-body-2 posted-ago muted-2").text.split()[0]
                            except:
                                date = ''
                            if date:
                                date = await self.convert_date(date)

                            # ------------------------- search relocation ----------------------------
                            relocate = ''
                            relocation = ''
                            try:
                                relocate = re.findall(r'[Rr]elocation', body)
                            except:
                                pass
                            if relocate:
                                relocation = 'релокация'

                            self.db.write_to_db_companies([company])

                            # -------------------- compose one writting for ione vacancy ----------------

                            results_dict = {
                                'chat_name': 'https://remotehub.com/',
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

    async def convert_date(self, date):
        if date == 'Today':
            date = datetime.now()
        else:
            date = datetime.now() - timedelta(days=int(date))
        return date

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

