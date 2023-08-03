import re
import time
from datetime import timedelta
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from settings.browser_settings import options, chrome_driver_path
from sites.write_each_vacancy_to_db import HelperSite_Parser
from utils.additional_variables.additional_variables import admin_database, archive_database
from helper_functions import helper_functions as helper

params = {
    'english_level': (
        '[Ee]nglish[\W]{0,2}[A-Za-zА-Яа-я][\W]{0,3}[\d]', '[Uu]pper[\W]{0,1}intermediate', '[Ii]ntermediate',
        '[Pp]re[\W]{0,1}[Ii]ntermediate', '[Uu]pper'),
}

country_list = ['Panama', 'Philippines', 'Europe', 'World', 'United Arab Emirates', 'Argentina', 'Armenia',
                'Australia', 'Austria', 'Azerbaijan', 'Belgium', 'Bulgaria', 'Belarus', 'Brazil',
                'Central African Republic', 'Canada', 'Switzerland', 'Chile', 'China', 'Colombia',
                'Costa Rica', 'Cuba', 'Cyprus', 'Czechia', 'Germany', 'Denmark', 'Dominican Republic',
                'Ecuador', 'Egypt', 'Spain', 'Estonia', 'Finland', 'France', 'Great Britain',
                'Georgia', 'Greece', 'Croatia', 'Hungary', 'Indonesia', 'India', 'Ireland',
                'Iceland', 'Israel', 'Italy', 'Japan', 'Kazakhstan', 'Kyrgyzstan', 'South Korea',
                'Lithuania', 'Luxembourg', 'Latvia', 'Monaco', 'Moldova', 'Mexico', 'Montenegro',
                'Mongolia', 'Malaysia', 'Netherlands', 'Norway', 'New Zealand', 'Oman', 'Poland',
                'Portugal', 'Qatar', 'Romania', 'Russian Federation', 'Singapore', 'Serbia',
                'Slovakia', 'Slovenia', 'Sweden', 'Thailand', 'Tajikistan', 'Tunisia', 'Turkey',
                'Ukraine', 'Uruguay', 'USA', 'Uzbekistan', 'Vietnam']


def convert_date_to_timestamp(date_string):
    keywords = {
        'today': timedelta(days=0),
        'yesterday': timedelta(days=1),
        'ago': None
    }

    days_match = re.search(r'(\d+)\s+days', date_string)
    if days_match:
        days_ago = int(days_match.group(1))
        timedelta_obj = timedelta(days=days_ago)
    else:
        timedelta_obj = timedelta()

    for keyword, delta in keywords.items():
        if keyword in date_string.lower():
            if delta is not None:
                timedelta_obj += delta
            break

    timestamp = int((datetime.now() - timedelta_obj).timestamp())
    return timestamp


class RemocateGetInformation:

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
        self.main_url = 'https://www.remocate.app/'
        self.count_message_in_one_channel = 1
        self.found_by_link = 0
        self.response = None
        self.current_session = None
        self.categories = ['Support', 'UX/UI', 'HR', 'QA', 'Analytics', 'Design', 'Development', 'Marketing']
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

        self.current_session = await self.helper_parser_site.get_name_session() if self.db else None

        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'https://www.remocate.app/', disable_web_page_preview=True)
        self.browser.get('https://www.remocate.app/')

        # scrolling ---------------------------------------------------
        while True:
            self.browser.execute_script("window.scrollBy(0, 2500);")
            time.sleep(0.5)
            current_height = self.browser.execute_script("return window.pageYOffset;")
            full_height = self.browser.execute_script("return document.documentElement.scrollHeight;")
            window_height = self.browser.execute_script("return window.innerHeight;")
            if current_height + window_height >= full_height:
                break

        vacancy_exists_on_page = await self.get_link_message()
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'remocate.app parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self):
        open_links = self.browser.find_elements(By.CLASS_NAME, "job-card")
        self.list_links = list(set(open_links))

        if self.list_links:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id,
                                                                   f'remocate.app:\nНайдено {len(self.list_links)} вакансий',
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
        check_vacancy_not_exists = True
        links = []
        soup = None
        self.found_by_link = 0
        for link in self.list_links:
            found_vacancy = True

            category_element = link.find_element(
                By.CSS_SELECTOR,
                "div.job-card-bubble[fs-cmsfilter-field='category']"
            )

            category_emoj = category_element.text.strip()
            category = re.sub(r'[^a-zA-Z]', '', category_emoj)
            # if category not in self.categories:
            #     continue

            try:
                vacancy_url = link.get_attribute("href")

                self.browser.execute_script("window.open(arguments[0])", vacancy_url)
                self.browser.switch_to.window(self.browser.window_handles[-1])
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
                except Exception as ex:
                    found_vacancy = False
                    print(f"error in browser.get {ex}")

                if found_vacancy:
                    try:
                        title = self.browser.find_element(By.CSS_SELECTOR, ".job-top-title").text.strip()
                    except AttributeError as ex:
                        title = None
                        print(f"Exception occurred: {ex}")

                    # get body --------------------------
                    try:
                        body_elements = self.browser.find_elements(By.CSS_SELECTOR, "div.job-description.w-richtext")
                        body = ' '.join(element.text.strip() for element in body_elements)
                    except AttributeError as ex:
                        body = None
                        print(f"Exception occurred: {ex}")

                    # get company -------------------------------
                    company = self.browser.find_element(By.CLASS_NAME, "job-top-company").text.strip()

                    # get job_type and relocation -------------------------------
                    job_info = self.browser.find_element(By.CLASS_NAME, "job-top-tags").text.strip()
                    job_info = re.sub(r'[^a-zA-Z]', ' ', job_info).split()
                    relocation = ""
                    for tags in job_info:
                        if tags == "Remote":
                            job_type = "удаленно"
                        elif tags == "Relocation":
                            relocation = "релокация"
                        else:
                            job_type = ""

                    # get date -------------------------------
                    date = self.browser.find_element(By.CLASS_NAME, "job-top-right").text.strip()
                    date = convert_date_to_timestamp(date)

                    # get english -------------------------------
                    english = ''
                    if re.findall(r'[Аа]нглийский', body, re.IGNORECASE) or re.findall(r'[Ee]nglish', body):
                        english_additional = ''
                        for item in params['english_level']:
                            matches = re.findall(rf"{item}", body, re.IGNORECASE)
                            for match in matches:
                                english_additional += f"{match}"

                        if re.search(r'\b(intermediate|upper|b1|b2|pre)\b', english_additional, re.IGNORECASE):
                            english = english_additional.strip()

                    if not english and (
                            re.findall(r'[Аа]нглийский', body, re.IGNORECASE) or re.findall(r'[Ee]nglish', body)):
                        english = 'English'

                    # get city -------------------------------
                    city_info = self.browser.find_element(By.CLASS_NAME, "job-top-tags").text.strip().split()
                    city = ''
                    for tag in city_info:
                        if tag in country_list:
                            city = tag
                            break

                    # get salary --------------------------
                    salary = ''
                    for line in body.split('\n'):
                        if re.search(r'\b[sS]alary\b', line):
                            salary = line

                    # get experience --------------------------
                    experience = ''
                    for line in body.split('\n'):
                        if re.search(r'\b[Ee]xperience&[Yy]ear|[Yy]ears\b', line):
                            experience = line
                        elif re.search(r'\b[Ee]xperience\b', line):
                            experience = line

                    # -------------------- compose one writting for ione vacancy ----------------

                    results_dict = {
                        'chat_name': 'https://www.remocate.app',
                        'title': title,
                        'body': body,
                        'profession': '',
                        'vacancy': title,
                        'vacancy_url': vacancy_url,
                        'company': company,
                        'english': english,
                        'relocation': relocation,
                        'job_type': job_type,
                        'city': city,
                        'salary': salary,
                        'experience': experience,
                        'contacts': '',
                        'time_of_public': date,
                        'created_at': '',
                        'agregator_link': '',
                        'session': self.current_session,
                        'sended_to_agregator ': '',
                        'sub ': '',
                    }
                    print(' ')

                    response = await self.helper_parser_site.write_each_vacancy(results_dict)
                    self.response = response

                    self.browser.close()
                    self.browser.switch_to.window(self.browser.window_handles[0])

            else:
                self.found_by_link += 1
                print("vacancy link exists")

        if self.found_by_link > 0:
            self.count_message_in_one_channel += self.found_by_link
            if self.bot_dict:
                self.current_message = await self.helper.edit_message(
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
        self.list_links = [vacancy_url]
        await self.get_content_from_link()
        self.browser.quit()
        return self.response

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
