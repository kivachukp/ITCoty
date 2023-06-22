import re
from datetime import datetime, timedelta
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from sites.write_each_vacancy_to_db import HelperSite_Parser
from settings.browser_settings import options, chrome_driver_path
from utils.additional_variables.additional_variables import admin_database, archive_database

# --- change before push


class EpamGetInformation:

    def __init__(self, **kwargs):

        self.report = kwargs['report'] if 'report' in kwargs else None
        self.search_words = kwargs['search_word'] if 'search_word' in kwargs else None
        self.bot_dict = kwargs['bot_dict'] if 'bot_dict' in kwargs else None
        self.db = kwargs['db'] if 'db' in kwargs else None
        self.helper = kwargs['helper'] if 'helper' in kwargs else None
        self.helper_parser_site = HelperSite_Parser(report=self.report, db=self.db)
        self.db_tables = None
        self.options = None
        self.current_message = None
        self.written_vacancies = 0
        self.rejected_vacancies = 0
        if self.bot_dict:
            self.bot = self.bot_dict['bot']
            self.chat_id = self.bot_dict['chat_id']
        self.browser = None
        self.main_url = 'https://anywhere.epam.com'
        self.count_message_in_one_channel = 1
        self.found_by_link = 0
        self.response = None
        self.current_session = None

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

        self.current_session = await self.helper_parser_site.get_name_session() if self.db else None

        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'https://anywhere.epam.com', disable_web_page_preview=True)
        self.browser.get('https://anywhere.epam.com/en/jobs')
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        vacancy_exists_on_page = await self.get_link_message(self.browser.page_source)
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'anywhere.epam.com parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):
        soup = BeautifulSoup(raw_content, 'lxml')
        open_links = soup.find_all('div', class_='JobCard_panel__56N9f')

        self.list_links = list(set(open_links))

        if self.list_links:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id,
                                                                   f'anywhere.epam.com:\nНайдено {len(self.list_links)} вакансий',
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
        experience = ''
        check_vacancy_not_exists = True
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
            if self.db:
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
                    print(f"error in browser.get {ex}\nvacancy_url: {vacancy_url}")
                if found_vacancy:
                    try:
                        vacancy = soup.find("h1", class_='JobDetailsBanner_title__WI4Kk').text.strip()
                    except AttributeError as ex:
                        vacancy = None
                        print(f"Exception occurred: {ex}")

                    # get title --------------------------
                    try:
                        title = soup.find("h1", class_='JobDetailsBanner_title__WI4Kk').text.strip()
                    except (AttributeError, TypeError) as ex:
                        title = None
                        print(f"Exception occurred: {ex}")

                    # get body --------------------------
                    try:
                        body = soup.find("div", class_="Description_container___XMTb").text.strip()
                    except AttributeError as ex:
                        body = None
                        print(f"Exception occurred: {ex}")

                    # get city --------------------------
                    try:
                        city = soup.find_all('div', class_='IconBullet_list__xKT9i UpperBar_list__ErgW9')[
                            -1].text.strip()
                    except:
                        city = ''

                    # get english level and experience --------------------------
                    english = ''
                    try:
                        english_levels = ['A1+', 'A2+', 'B2+', 'B1+', 'C1+', 'C2+', 'Native', 'English']
                        requirements = self.browser.find_elements(By.CLASS_NAME,
                                                            'AccordionSection_container__Lg5Z_.Description_accordionContainer__gHK8_.AccordionSection_medium___u5_2.Description_medium__sj6N2.AccordionSection_opened__eE0Qc')
                        requirements = requirements[1].find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')
                        for li in requirements:
                            if 'year' in li.text or 'years' in li.text:
                                experience = li.text
                            for level in english_levels:
                                if 'German' in li.text:
                                    english = li.text
                                elif level in li.text:
                                    english = level
                                    break
                    except:
                        english = None

                    # -------------------- compose one writting for ione vacancy ----------------

                    results_dict = {
                            'chat_name': 'https://anywhere.epam.com',
                            'title': title,
                            'body': body,
                            'vacancy': vacancy,
                            'vacancy_url': vacancy_url,
                            'company': 'Epam',
                            'company_link': '',
                            'english': english,
                            'relocation': '',
                            'job_type': '',
                            'city': city,
                            'salary': '',
                            'experience': experience,
                            'time_of_public': '',
                            'contacts': '',
                            'session': self.current_session
                    }
                    return_raw_dictionary = False
                    if not return_raw_dictionary:
                        response = await self.helper_parser_site.write_each_vacancy(results_dict)

                        print('sort profession (33)')
                        await self.output_logs(
                            about_vacancy=response,
                            vacancy=vacancy,
                            vacancy_url=vacancy_url
                        )
                        # return response
                        self.response = response
                    else:
                        self.response = results_dict
                else:
                    print(f"vacancy_url is wrong: {vacancy_url}")
            else:
                self.found_by_link += 1
                print("vacancy link exists")

        # loop for vacancy_url ends

        if self.found_by_link > 0:
            self.count_message_in_one_channel += self.found_by_link
            if self.bot_dict:
                self.current_message = await self.helper.edit_message(
                    bot=self.bot,
                    text=f"\n---\nfound by link: {self.found_by_link}",
                    msg=self.current_message
                )

    async def get_content_from_one_link(self, vacancy_url):
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=None)
        # -------------------- check what is current session --------------
        self.current_session = await self.helper_parser_site.get_name_session()
        self.list_links = [vacancy_url]
        await self.get_content_from_link()
        self.browser.quit()
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


    async def write_to_db_table_companies(self):
        excel_data_df = pd.read_excel('all_geek.xlsx', sheet_name='Sheet1')
        companies = excel_data_df['hiring'].tolist()
        links = excel_data_df['access_hash'].tolist()

        companies = set(companies)
        if self.db:
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

        if self.bot_dict and self.helper:
            if len(f"{self.current_message}\n{self.count_message_in_one_channel}. {vacancy}\n{additional_message}") < 4096:
                new_text = f"\n{self.count_message_in_one_channel}. {vacancy}\n{additional_message}"

                self.current_message = await self.helper.edit_message(
                    bot=self.bot,
                    text=new_text,
                    msg=self.current_message
                )
            else:
                new_text = f"{self.count_message_in_one_channel}. {vacancy}\n{additional_message}"
                self.current_message = await self.helper.send_message(
                    bot=self.bot,
                    chat_id=self.chat_id,
                    text=new_text
                )

        self.count_message_in_one_channel += 1

