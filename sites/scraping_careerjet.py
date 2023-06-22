from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from sites.write_each_vacancy_to_db import HelperSite_Parser
from settings.browser_settings import options, chrome_driver_path
from utils.additional_variables.additional_variables import admin_database, archive_database, sites_search_words


class СareerjetGetInformation:

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
        self.main_url = 'https://www.careerjet.by'
        self.count_message_in_one_channel = 1
        self.found_by_link = 0
        self.response = None
        self.current_session = None
        self.word = None

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
            await self.bot.send_message(self.chat_id, 'https://www.careerjet.by/', disable_web_page_preview=True)
        for word in sites_search_words:
            self.word = word
            self.browser.get(f'https://www.careerjet.by/search/jobs?s={self.word}&l=&radius=25&sort=relevance')

            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            vacancy_exists_on_page = await self.get_link_message(self.browser.page_source)
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'Сareerjet parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):
        soup = BeautifulSoup(raw_content, 'lxml')
        open_links = soup.find_all('article', class_='job')

        self.list_links = list(set(open_links))

        if self.list_links:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id,
                                                               f'Сareerjet:\nПо слову {self.word} найдено {len(self.list_links)} вакансий',
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
            try:
                vacancy_url = link.find('a').get('href')
                vacancy_url = self.main_url + vacancy_url
                print(vacancy_url)
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
                    print(f"error in browser.get {ex}")

                if found_vacancy:
                    try:
                        vacancy = soup.find("h1").text.strip()
                    except AttributeError as ex:
                        vacancy = None
                        print(f"Exception occurred: {ex}")

                    # get title --------------------------
                    try:
                        title = soup.find("h1").text.strip()
                    except (AttributeError, TypeError) as ex:
                        title = None
                        print(f"Exception occurred: {ex}")

                    # get body --------------------------
                    try:
                        body = soup.find("section", class_="content").text.strip()
                    except AttributeError as ex:
                        body = None
                        print(f"Exception occurred: {ex}")

                    # get city and job_format --------------
                    try:


                        job_info = []
                        inner_div = soup.find('ul', class_='details')  # Находим блокf <div class="j-d-h__inner">

                        for li in inner_div.find_all('li'):
                            job_info.append(li.text.strip())
                        city =job_info[0]

                        try:
                            if job_info[1] == 'Полная занятость':
                                job_format = 'Полная занятость'
                            else:
                                job_format = ['Гибрид', 'Удалённо']
                        except:
                            if job_info[1] == 'Полная занятость':
                                job_format = 'Полная занятость'
                            else:
                                job_format = ['Гибрид', 'Удалённо']

                    except AttributeError as ex:
                        job_format = None
                        city = None
                        print(f"AttributeError occurred: {ex}")
                    if job_format:
                        if type(job_format) is list:
                            job_format = ", ".join(job_format)
                    # get company -------------------------
                    try:
                        company = soup.find("p", class_="company").text.strip()
                    except AttributeError as ex:
                        company = None
                        print(f"Exception occurred: {ex}")

                    if company and self.db:
                        self.db.write_to_db_companies([company])

                    # get salary --------------------------
                    try:
                        salary = soup.find("span", class_="price").text.strip()
                    except AttributeError as ex:
                        salary = None
                        print(f"AttributeError occurred: {ex}")


                    # -------------------------public time ----------------------------

                    time_of_public = None
                    tags_ul = soup.find('ul', class_='tags')  # Находим блок <ul class="tags">

                    if tags_ul:
                        span = tags_ul.find('span', class_='badge')
                        if span:
                            time_of_public = span.text.strip()
                    if time_of_public:
                        time_of_public = self.normalize_date(time_of_public)
                    print(time_of_public)

                    # -------------------- compose one writting for ione vacancy ----------------

                    results_dict = {
                        'chat_name': 'https://www.careerjet.by/',
                        'title': title,
                        'body': body,
                        'vacancy': vacancy,
                        'vacancy_url': vacancy_url,
                        'company': company,
                        'company_link': '',
                        'english': '',
                        'relocation': '',
                        'job_type': job_format,
                        'city': city,
                        'salary': salary,
                        'experience': '',
                        'time_of_public': time_of_public,
                        'contacts': '',
                        'session': self.current_session
                    }
                    #print(results_dict)
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
        self.list_links= [vacancy_url]
        await self.get_content_from_link()
        self.browser.quit()
        return self.response


    def normalize_date(self, date):
        date = date.split('.')[0]
        date = date.split(' ')
        number = date[0]
        period = date[1]
        time_of_public = None
        if period == 'д':
            time_of_public = datetime.now() - timedelta(days=int(number))
        elif period == 'ч':
            time_of_public = datetime.now() - timedelta(hours=int(number))
        elif period == 'мес':
            time_of_public = datetime.now() - timedelta(days=int(number)*30)
        else:
            print('date: ', date)
            pass
        return time_of_public


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


