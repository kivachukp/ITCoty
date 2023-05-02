
import re
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from db_operations.scraping_db import DataBaseOperations
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters
from sites.sites_additional_utils.get_structure import get_structure, get_structure_advance
from sites.write_each_vacancy_to_db import HelperSite_Parser
from settings.browser_settings import options, chrome_driver_path
from utils.additional_variables.additional_variables import sites_search_words, parsing_report_path, \
    admin_database, archive_database
from helper_functions.helper_functions import edit_message, send_message, send_file_to_user
from report.report_variables import report_file_path


junior_link = 'https://jobs.devby.io/?filter[levels][]=intern&filter[levels][]=junior'
link_search = 'https://jobs.devby.io/?&filter[search]=project%20manager'

class DevGetInformation:

    def __init__(self, **kwargs):

        self.report = kwargs['report'] if 'report' in kwargs else None
        self.search_words = kwargs['search_word'] if 'search_word' in kwargs else sites_search_words
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
        self.main_url = 'https://jobs.devby.io'
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

        for word in self.search_words:
            self.word = word
            self.page_number = 1
            if len(self.word.split(' '))>1:
                word1 = self.word.split(' ')[0]
                word2 = self.word.split(' ')[1]
                link = f'https://jobs.devby.io/?&filter[search]={word1}%20{word2}'
            else:
                link = f'https://jobs.devby.io/?&filter[search]={self.word}'
            if self.bot_dict:
                await self.bot.send_message(self.chat_id, link, disable_web_page_preview=True)

            # print('page link: ', link)
            try:
                self.browser.get(link)
            except Exception as e:
                print('bot could not to get the link', e)

            try:
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            except:
                pass
            await self.get_link_message(self.browser.page_source)

            # till = 13
            # for self.page_number in range(1, till):
            #     try:
            #         await self.bot.send_message(self.chat_id, f'https://hh.ru/search/vacancy?text={self.word}&from=suggest_post&salary=&schedule=remote&no_magic=true&ored_clusters=true&enable_snippets=true&search_period=1&excluded_text=&page={self.page_number}&hhtmFrom=vacancy_search_list',
            #                               disable_web_page_preview=True)
            #         self.browser.get(f'https://hh.ru/search/vacancy?text={self.word}&from=suggest_post&salary=&schedule=remote&no_magic=true&ored_clusters=true&enable_snippets=true&search_period=1&excluded_text=&page={self.page_number}&hhtmFrom=vacancy_search_list')
            #         self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            #         vacancy_exists_on_page = await self.get_link_message(self.browser.page_source, self.word)
            #         if not vacancy_exists_on_page:
            #             break
            #     except:
            #         break
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, 'dev.by parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):

        soup = BeautifulSoup(raw_content, 'lxml')

        self.list_links = soup.find_all('div', class_='vacancies-list-item__position')
        if self.list_links:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id, f'dev.by:\nПо слову {self.word} найдено {len(self.list_links)} вакансий на странице {self.page_number}', disable_web_page_preview=True)

            # --------------------- LOOP -------------------------
            self.written_vacancies = 0
            self.rejected_vacancies = 0

            await self.get_content_from_link()

            #----------------------- the statistics output ---------------------------
            self.written_vacancies = 0
            self.rejected_vacancies = 0
            return True
        else:
            if self.bot_dict:
                self.current_message = await self.bot.send_message(self.chat_id, f'dev.by:\nПо слову {self.word} найдено {len(self.list_links)} вакансий на странице {self.page_number}', disable_web_page_preview=True)

    async def get_content_from_link(self):
        links = []
        soup = None
        self.found_by_link = 0
        for link in self.list_links:
            found_vacancy = True
            try:
                vacancy_url = link.find('a', class_='vacancies-list-item__link_block').get('href')
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
                    soup = BeautifulSoup(self.browser.page_source, 'lxml')
                except Exception as ex:
                    found_vacancy = False
                    print(f"error in browser.get {ex}")

                if found_vacancy:
                    # get vacancy ------------------------
                    vacancy = ''
                    try:
                        vacancy = soup.find('div', class_='vacancy__header__name').get_text().replace('Вакансия ', '')
                    except Exception as e:
                        pass
                    # print('vacancy = ', vacancy)

                    # get title --------------------------
                    title = vacancy
                    # print('title = ',title)

                    # get body --------------------------
                    body = ''
                    body_content = soup.find('div', class_='vacancy__body').find('div', class_='text')
                    structure = await get_structure_advance(body_content)
                    body_content_list_p = body_content.find_all('strong')
                    body_content_list_ul = body_content.find_all('ul')
                    for element in structure:
                        if element == 'p':
                            try:
                                temp = body_content_list_p[0].get_text()
                                body += f"\n{temp}\n"
                                body_content_list_p.pop(0)
                            except:
                                break
                        if element == 'ul':
                            if body_content_list_ul:
                                temp = body_content_list_ul[0]
                                for li in temp:
                                    if li.text != ' ' and li != '\n' and li.text:
                                        try:
                                            body += f"-{li.get_text().strip()}\n"
                                        except:
                                            break
                                body_content_list_ul.pop(0)

                    # get tags --------------------------
                    tags_list = []
                    tags = ''
                    try:
                        tags_list = soup.find_all('div', class_="vacancy__tags__item")
                        for i in tags_list:
                            tags += f"#{i.get_text().replace(' ', '')} "
                        tags = tags[0:-1]
                    except:
                        pass

                    body = f"{body}\n{tags}"

                    tags = ''
                    try:
                        tags_list = soup.find_all('div', class_='vacancy__info-block__item')
                    except Exception as e:
                        pass
                    if tags_list and type(tags_list) is list:
                        for element in tags_list:
                            tags += f'{element.get_text()}, '
                        tags = tags[:-2]

                    level = re.findall(r'Уровень: [a-zA-Zа-яА-Я]+', tags)
                    if level:
                        level = level[0].replace('Уровень:', '').strip()
                    else:
                        level = ''
                    body += f" #{level}"

                    english = re.findall(r'Уровень английского: [a-zA-Zа-яА-Я0-9\s]+', tags)
                    if english:
                        english = english[0].replace('Уровень английского:', '').strip()
                    else:
                        english = ''

                    # get city --------------------------

                    try:
                        city = self.browser.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div[1]/div[2]/div/div/div/div[1]/div[3]/div/div[2]/div[1]/strong')
                        city = city.text
                    except Exception as ex:
                        city = ''

                    # get company --------------------------
                    try:
                        company = soup.find('div', class_='vacancy__footer__company-name').get_text()
                    except:
                        company = ''
                    # print('company = ',company)

                    # get salary --------------------------
                    try:
                        salary = soup.find('span', class_='bloko-header-section-2 bloko-header-section-2_lite').get_text()
                    except:
                        salary = ''
                    print('salary = ',salary)

                    # get experience --------------------------
                    experience = ''
                    try:
                        experience = re.findall(r'Опыт: [a-zA-Zа-яА-Я0-9\s]+', tags)
                    except Exception as e:
                        pass
                    if experience:
                        experience = experience[0].replace('Опыт:', '').strip()
                    else:
                        experience = ''

                    remote = ''
                    try:
                        remote = re.findall(r'Возможна удалённая работа: [a-zA-Z\sа-яА-Я0-9]+', tags)
                    except Exception as e:
                        pass
                    if remote:
                        remote = remote[0].replace('Возможна удалённая работа:', '').strip()
                    else:
                        remote = ''

                    full_time = ''
                    try:
                        full_time = re.findall(r'Режим работы: [a-zA-Zа-яА-Я0-9\s]+', tags)
                    except Exception as e:
                        pass
                    if full_time:
                        full_time = full_time[0].replace('Режим работы:', '').strip()
                    else:
                        full_time = ''
                    # print('full_time = ', full_time)

                    job_type = ''
                    if remote:
                        job_type += f"Удаленный формат: {remote}\n"
                    if full_time:
                        job_type += f"График работы: {full_time}"

                    contacts = ''
                    salary = ''

                    date = datetime.now()

                    # ------------------------- search relocation ----------------------------
                    relocation = ''
                    if re.findall(r'[Рр]елокация', body):
                        relocation = 'релокация'


                    # # ------------------------- search english ----------------------------
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
                        'chat_name': 'https://dev.by',
                        'title': title,
                        'body': body,
                        'vacancy': vacancy,
                        'vacancy_url': vacancy_url,
                        'company': company,
                        'company_link': '',
                        'english': english,
                        'relocation': relocation,
                        'job_type': job_type,
                        'city':city,
                        'salary':salary,
                        'experience':'',
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

        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=None)
        # -------------------- check what is current session --------------
        self.current_session = await self.helper_parser_site.get_name_session()
        self.list_links= [vacancy_url]
        await self.get_content_from_link()
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

        date = date.split(f'\xa0')
        month = date[1]
        day = date[0]
        year = date[2]

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


    async def output_logs(self, about_vacancy, vacancy, vacancy_url=None):
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

        # print(f"\n{self.count_message_in_one_channel} from_channel remote-job.ru search {self.word}")
        self.count_message_in_one_channel += 1
