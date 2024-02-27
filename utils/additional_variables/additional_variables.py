# for add in vacancy search in db tables
import pandas
from settings.dirs import DIR_EXCEL, DIR_REPORT, DIR_PATTERNS, DIR_UTILS, DIR_LOGS

admin_database = 'admin_last_session'
archive_database = 'archive'
shorts_session_database = 'short_session_numbers'
admin_copy = 'admin_copy'
vacancies_database = 'vacancies'
countries_cities_table = 'countries_cities'
last_autopushing_time_database = 'last_autopushing_time'
short_session_database = 'shorts_session_name'
reject_table = 'reject'
admin_temporary = 'admin_temporary'
admin_temporary_fields = 'id, id_admin_channel, id_admin_last_session_table, sended_to_agregator'
shorts_database = 'shorts_table'
shorts_database_fields = 'id, id_vacancy_from_admin_table'
shorts_database_fields_type = 'id SERIAL PRIMARY KEY, id_vacancy_from_admin_table INT'

profession_table_fields = "id, chat_name, title, body, profession, vacancy, vacancy_url, company, english, relocation, " \
                             "job_type, city, salary, experience, contacts, time_of_public, created_at, agregator_link, " \
                             "session, sub, tags, full_tags, full_anti_tags, short_session_numbers, level, approved"


fields_admin_temporary = "id_admin_channel, id_admin_last_session_table, sended_to_agregator"

additional_elements = {'admin_last_session', 'archive'}

valid_professions = ['junior', 'backend', 'frontend', 'qa', 'devops', 'designer', 'game', 'mobile', 'product', 'pm', 'analyst',
                     'marketing', 'sales_manager', 'hr']
valid_professions_extended = []
valid_professions_extended.extend(valid_professions)
valid_professions_extended.extend(['fullstack'])
tables_for_search_vacancy_existing = [admin_database, 'archive']
# all_tables_for_vacancy_search = ['designer', 'game', 'product', 'mobile', 'pm', 'sales_manager', 'analyst', 'frontend',
#                      'marketing', 'devops', 'hr', 'backend', 'qa', 'junior', admin_database, archive_database]

profession_list_for_pushing_by_schedule = ['hr', 'game', 'marketing', 'sales_manager', 'analyst', 'designer', 'pm', 'qa', 'devops',
                                           'mobile', 'frontend', 'backend']
all_tables_for_vacancy_search = []
all_tables_for_vacancy_search.extend([admin_database, archive_database])
all_tables_for_vacancy_search.extend(valid_professions)
valid_job_types = ['remote', 'office', 'office/remote', 'fulltime', 'flexible']
not_lower_professions = ['pm', 'game', 'designer', 'hr', 'analyst', 'qa', 'ba' 'devops', 'product']

white_admin_list = [1763672666, 556128576, 758905227, 945718420, 5755261667, 5884559465, 5730794427, 758905227]

id_owner = 1763672666
id_developer = 5884559465

#admin database name
channel_id_for_shorts = -1001671844820

# message_for_send = f'<i>Функционал дайджеста находится в состоянии альфа-тестирования, приносим свои ' \
#                                    f'извинения, мы работаем над тем чтобы вы получали информацию максимально ' \
#                                    f'качественную и в сжатые сроки</i>\n\n'

dict_for_title_shorts = {
    '': 'Системных аналитиков',
}

flood_control_logs_path = DIR_EXCEL / "flood_control.txt"
pattern_path = DIR_EXCEL /"pattern.txt"
admin_check_file_path = DIR_LOGS / "check_file.txt"
path_log_check_profession = DIR_EXCEL / "send_log_txt.txt"
report_file_not_actual_vacancy = DIR_EXCEL / "not_actual_vacancies.txt"
shorts_copy_path = DIR_EXCEL / "copy_shorts.txt"

sites_search_words = ['junior', 'стажер', 'designer', 'ui', 'стажировка', 'product manager', 'project manager', 'python', 'php']

table_list_for_checking_message_in_db = ['admin_last_session', 'archive', 'reject']

pre_message_for_shorts = '<i>Функционал дайджеста находится в состоянии альфа-тестирования, приносим свои ' \
                                   f'извинения, мы работаем над тем чтобы вы получали информацию максимально ' \
                                   f'качественную и в сжатые сроки</i>\n\n'

message_not_access = "Sorry, you have not the permissions"
path_last_pattern = DIR_PATTERNS / "last_changes" / "pattern_Alex2809 (6).py"
path_data_pattern = DIR_PATTERNS / "data_pattern" / "_data_pattern.py"

path_filter_error_file = DIR_EXCEL / "filter_jan_errors.txt"
db_fields_for_update_in_parsing = ['job_type', 'relocation', 'city', 'experience', 'english']

cities_file_path = DIR_UTILS / "additional_data" / "data.xlsx"

callba6ck_for_push_shorts = ['*', 'all']

excel_data_df = pandas.read_excel(f'{cities_file_path}', sheet_name='Cities')
excel_dict = {
    'city': excel_data_df['city'].tolist(),
    'country': excel_data_df['country'].tolist(),
}
result_excel_dict = {}
for i in range(0, len(excel_dict['city'])):
    if excel_dict['country'][i] in result_excel_dict:
        result_excel_dict[excel_dict['country'][i]].append(excel_dict['city'][i])
    else:
        result_excel_dict[excel_dict['country'][i]] = [excel_dict['city'][i]]

clear_vacancy_trash_pattern = "[Ии]щем в команду[:]?|[Тт]ребуется[:]?|[Ии]щем[:]?|[Вв]акансия[:]?|[Пп]озиция[:]?|" \
                              "[Дд]олжность[:]|в поиске[:]|[Нн]азвание вакансии[:]|[VACANCYvacancy]{7}[:]?|[Pp]osition[:]?"

how_much_pages = 7
path_post_request_file = DIR_EXCEL / "path_post_request_file.txt"
till = 5
vacancy_fresh_time_days = 7
path_to_excel = "./excel/"
path_push_shorts_report_file = DIR_EXCEL / "report_push_shorts.txt"
tables_list_for_report = ['junior', '*']
developer_chat_id = 5884559465

parsing_report_path = DIR_REPORT / "excel" / "parsing_report.xlsx"
table_parsing_report = DIR_REPORT / "report_parsing_temporary"
pictures_separators_path = DIR_UTILS / "pictures" / "shorts_separators"
# pictures_separators_path = "./utils/pictures/shorts_separators"

valid_subs = {'analyst' : ['sys_analyst', 'data_analyst', 'data_scientist', 'ba'],
              'backend' : ['python', 'c', 'php', 'java', 'ruby', 'scala', 'net', 'nodejs', 'laravel', 'golang', 'delphi', 'abap', 'ml', 'data_engineer', 'unity', 'one_c', 'embedded'],
              'designer' : ['ui_ux', 'motion', 'dd', 'ddd', 'game_designer', 'illustrator', 'graphic', 'uxre_searcher'], 'devops' : [],
              'frontend' : ['vue', 'react', 'angular', 'wordpress', 'bitrix', 'joomla', 'drupal'], 'game' : [], 'hr' : [],
              'marketing' : ['smm', 'copyrighter', 'seo', 'link_builder', 'media_buyer', 'email_marketer', 'context', 'content_manager', 'tech_writer'],
              'mobile' : ['ios', 'android', 'cross_mobile', 'flutter', 'react_native'], 'pm' : ['project', 'product'],
              'qa' : ['manual_qa', 'aqa', 'support'], 'sales_manager' : [], 'non_code_manager' : []}

dict_from_front = {
    "direction": "",
    "specialization": ["Front-end", "Back-end", "Mobile", "Fullstack", "Системный администратор", "Администратор БД", "Администратор приложений", "2D/3D design", "Gamedev design", "Marketing design", "Mobile design", "Motion", "Product design", "UX/UI design", "Web design", "Анимация", "Арт директор", "Бренд дизайн", "Видео", "Графический дизайн", "Дизайн интерьеров", "Иллюстрация", "Инфографика", "Полиграфия","Спецэффекты", "Технический дизайн"],
    "level": ["", "trainee", "entry level", "junior", "middle", "senior", "director", "lead"],
    "country": [],
    "city": [],
    "salary": ["", ""],
            "currency": "",
    "salaryOption": ["Почасовая", "За месяц", "За год", "До вычета налогов", "На руки"],
    "companyScope": [],
    "typeOfEmployment": ["", "fulltime", "parttime", "contract", "freelance", "internship", "volunteering"],
    "companyType": ["", "product", "outsourcing", "outstaff", "consulting", "notTechnical", "startup"],
    "companySize": ["1-200", "201-500", "501-1000", "1000"],
    "job_type": ["remote", "fulltime", "flexible", "office", "office/remote" ]
 }

post_request_for_example = {
    'profession': '',
    'specialization':
    'frontend',
    'programmingLanguage': ['js'],
    'technologies': ['react'],
    'level': ['all', 'trainee', 'entry level', 'junior', 'midle', 'senior', 'director', 'lead'],
    'country': 'BY',
    'city': '',
    'state': '',
    'salary': ['200', '400'],
    'salaryOption': ['hourly', 'perMonth', 'perYear', 'beforeTaxes', 'inHand'],
    'companyScope': '',
    'typeOfEmployment': ['all', 'fulltime', 'parttime', 'tempJob', 'contract', 'freelance', 'internship', 'volunteering'],
    'companyType': ['all', 'product', 'outsourcing', 'outstaff', 'consulting', 'notTechnical', 'startup'],
    'companySize': ['1-200', '201-500', '501-1000', '1000+'],
    'job_type': ['remote']
}

admin_table_fields = "id, chat_name, title, body, profession, vacancy, vacancy_url, company, english, relocation, " \
                     "job_type, city, salary, experience, contacts, time_of_public, created_at, agregator_link, " \
                     "session, sended_to_agregator, sub, tags, full_tags, full_anti_tags, short_session_numbers, " \
                     "level, approved, closed, salary_from, salary_to, salary_currency, salary_period, rate, " \
                     "salary_from_usd_month, salary_to_usd_month"

vacancy_table = "id SERIAL PRIMARY KEY," \
                "chat_name VARCHAR(150)," \
                "title VARCHAR(1000)," \
                "body VARCHAR (6000)," \
                "profession VARCHAR (30)," \
                "vacancy VARCHAR (700)," \
                "vacancy_url VARCHAR (150)," \
                "company VARCHAR (200)," \
                "english VARCHAR (100)," \
                "relocation VARCHAR (100)," \
                "job_type VARCHAR (700)," \
                "city VARCHAR (150)," \
                "salary VARCHAR (300)," \
                "salary_from INT," \
                "salary_to INT," \
                "salary_currency VARCHAR(20)," \
                "salary_period VARCHAR(50)," \
                "experience VARCHAR (700)," \
                "contacts VARCHAR (500)," \
                "time_of_public TIMESTAMP," \
                "created_at TIMESTAMP," \
                "agregator_link VARCHAR(200)," \
                "session VARCHAR(15)," \
                "sended_to_agregator VARCHAR(30)," \
                "sub VARCHAR (250)," \
                "tags VARCHAR (700)," \
                "full_tags VARCHAR (700)," \
                "full_anti_tags VARCHAR (700)," \
                "short_session_numbers VARCHAR (300)," \
                "level VARCHAR (70)," \
                "approved VARCHAR (100), " \
                "closed BOOLEAN, " \
                "rate REAL, " \
                "salary_from_usd_month INT, " \
                "salary_to_usd_month INT, " \
                "FOREIGN KEY (session) REFERENCES current_session(session)"

help_text = '/log or /logs - get custom logs (useful for developer\n' \
            '/get_participants - ❗️get the channel follower numbers\n' \
            '/delete_till - ❗️delete old vacancy from admin DB till date\n\n' \
            '------------ FOR DEVELOPER: ------------\n' \
            '⛔️/debugs\n' \
            '⛔️/developing\n' \
            '⛔️/get_tables_and_fields\n' \
            '⛔️/get_vacancy_names - you type the profession and bot shows you all titles\n' \
            '⛔️/add_tags_to_DB - (one time usable)\n' \
            '⛔️/rollback_last_short_session - one step back (shorts) you type number short_session (you can see)\n' \
            '⛔️/rollback_by_number_short_session - one step back (shorts) you type number short_session (you can see)\n' \
            '⛔️/get_vacancies_name_by_profession - get vacancies name from DB to file with fields\n' \
            '⛔️/ --- refresh_pattern - to get the modify pattern from DB\n' \
            '⛔️/get_and_write_level - define field level and rewrite to admin DB\n' \
            '⛔️/get_from_admin - get all vacancy_names from admin channel\n' \
            '⛔️/add_field_into_tables_db - type name and field type\n\n' \
            '⛔️/copy_prof_tables_to_archive_prof_tables - type name and field type\n\n' \
            '⛔️/peerchannel - useful for a developer to get id channel\n' \
            '⛔️/getdata - get channel data\n' \
            '⛔️/check_parameters - get vacancy\'s parameters\n' \
            '⛔️/get_backup_db - receive last db backup\n' \
            '⛔️/check_link_hh - doesnt work :)\n' \
            '⛔️/get_participants\n' \
            '⛔️/get_user_data\n' \
            '⛔️/emergency_push\n' \
            '⛔️/get_pattern\n' \
            '⛔️/get_pattern_pseudo\n' \
            '⛔️/clear_db_table\n' \
            '⛔️/numbers_of_archive\n' \
            '⛔️/get_flood_error_logs\n' \
            '⛔️/how_many_records_in_db_table - shows quantity of records in db table\n' \
            '⛔️/get_vacancy_for_example - receivw the random vacancy from admin\n' \
            '⛔️/get_vacancy_from_backend - random vacancy from backend\n' \
            '⛔️/add_and_push_subs - add subs and fill them\n' \
            '⛔️/get_random_vacancy_by_profession \n' \
            '⛔️/get_post_request \n' \
            '⛔️/rewrite_additional_db_fields - like job_type, english, experience, relocation, city\n' \
            '⛔️/show_db_records - random vacancy from db\n' \
            '⛔️/get_channel_members - get user\'s channels name\n' \
            '⛔️/transpose_no_sort_to_archive - all no_sort to archive\n' \
            '/update_salary_field_usd - add usd fields' \
            '/add_vacancies_table' \
            '/refactoring_vacancy_salary - it has been made for replace not valid values in salary fields' \
            '----------------------------------------------------\n\n' \
            '---------------- FILES: ----------------\n' \
            '/report_push_shorts - shorts report \n' \
            '/get_admin_vacancies_table - get all full vacancies from admin\n' \
            '----------------------------------------------------\n\n' \
            '---------------- PARSING: ----------------\n' \
            '🔆/magic_word - input word and get results from hh.ru\n' \
            '🔆/hh_kz - input word and get results from hh.ru\n' \
            '🔆/svyazi - get data from svyazi.app\n' \
            '🔆/finder - get the data from finder.vc\n' \
            '🔆/habr - get the data from career.habr.com\n' \
            '🔆/superjob - get the data from superjob.ru\n' \
            '🔆/rabota - get the data from rabota.by\n' \
            '🔆/dev - get the data from dev.by\n' \
            '🔆/geek - get data from geek.ru\n' \
            '🔆/remotehub - get data from www.remotehub.com\n' \
            '🔆/remotejob - get data from remote-job.ru\n' \
            '🔆/ingame - get data from ingame\n' \
            '🔆/praca - get data from praca.by\n' \
            '---------------------------------------------------\n\n' \
            '/download - ❗️you get excel from admin vacancies with search tags\n' \
            '/ambulance - if bot gets accident in hard pushing and you think you loose the shorts\n' \
            '/check_vacancies_for_relevance - to mark not actual vacancies id DB (closed will be TRUE)\n\n' \
            '---------------- TOOLS: ----------------\n' \
            '🛠/edit_pattern - stop proccess\n' \
            '/db_check_url_vacancy - does vacancy exist by link\n' \
            '/db_check_add_single_vacancy - check and add vacancy by link\n' \
            '/schedule - non-stop parsing\n' \
            '/restore_from_admin - restory the lost vacancies\n' \
            '/invite_people - start to invite followers\n' \
            '/get_news - start to invite followers\n' \
            '🖐️/stop - stop process\n' \
            '➡️/refresh_and_save_changes - One click for the correct refresh. Includes:\n' \
            '✅/refresh - to get the professions in excel format in all vacancies throgh the new filters logic (without rewriting)\n' \
            '✅/check_doubles - remove the vacancy"s doubles\n' \
            '✅/remove_completed_professions - remove complete professions\n' \
            '/post_to_telegraph' \
            '---------------------------------------------------\n\n' \
            '---------------- STATISTICS: ----------------\n' \
            '/how_many_vacancies_published - get the statistic file (created by Anna)\n' \
            '/how_many_vacancies_total - new report (created by Anna)\n' \
            '/vacancies_from - how many juniors have been written today and tomorrow\n' \
            '/check_title_body\n' \
            '/get_profession_parsing_tags_log - send the file with tags and antitags\n' \
            '/get_courses_data - get courses names and links from geek (excel)\n ' \
            '/add_statistics\n\n' \
            '---------------------------------------------------\n\n' \
            '---------------- PUSHING BY SCHEDULE: ----------------\n' \
            '/hard_pushing_by_schedule - run pushing by schedule\n' \
            '/hard_push_by_web - run pushing by schedule through web point\n' \
            '/pick_up_forcibly_from_admin - if vacancies has been sent to the admin channel already and code has stopped\n' \
          '---------------------------------------------------\n\n' \
          '---------------------------------------------------\n\n' \
            '---------------- UPDATERS: ----------------\n' \
            '/update_city_field - update city field by new logic\n' \
            '/update_salary_field - update salary field by new logic\n' \
          '---------------------------------------------------\n\n' \
            '❗️- it is admin options'

# help_text = '/get_log_file - get file with logs\n' \
#             '---------------- FILES: ----------------\n' \
#             '/report_push_shorts - shorts report \n' \
#             '/get_admin_vacancies_table - get all full vacancies from admin\n' \
#             '----------------------------------------------------\n\n' \
#             '---------------- PARSING: ----------------\n' \
#             '🔆/magic_word - input word and get results from hh.ru\n' \
#             '🔆/hh_kz - input word and get results from hh.ru\n' \
#             '🔆/svyazi - get data from svyazi.app\n' \
#             '🔆/finder - get the data from finder.vc\n' \
#             '🔆/habr - get the data from career.habr.com\n' \
#             '🔆/superjob - get the data from superjob.ru\n' \
#             '🔆/rabota - get the data from rabota.by\n' \
#             '🔆/dev - get the data from dev.by\n' \
#             '🔆/geek - get data from geek.ru\n' \
#             '🔆/remotehub - get data from www.remotehub.com\n' \
#             '🔆/remotejob - get data from remote-job.ru\n' \
#             '🔆/ingame - get data from ingame\n' \
#             '🔆/praca - get data from praca.by\n' \
#             '---------------------------------------------------\n\n' \
#             '/schedule - non-stop parsing\n' \
#             '/get_news - start to invite followers\n' \
#             '🖐️/stop - stop process\n' \
#             '---------------------------------------------------\n\n' \
#             '---------------- STATISTICS: ----------------\n' \
#             '/how_many_vacancies_published - get the statistic file (created by Anna)\n' \
#             '/how_many_vacancies_total - new report (created by Anna)\n' \
#             '---------------------------------------------------\n\n' \
#             '---------------- PUSHING BY SCHEDULE: ----------------\n' \
#             '/hard_pushing_by_schedule - run pushing by schedule\n' \
#             '/hard_push_by_web - run pushing by schedule through web point\n' \
#             '---------------------------------------------------\n\n' \
#             '❗️- it is admin options'

preview_fields_for_web = "id, profession, vacancy, company, " \
                     "job_type, city, salary, created_at, level, salary_from_usd_month, salary_to_usd_month"
vacancies_database = 'vacancies'
manual_posting_shorts = ['junior']
hard_pushing_time_hour = [10, 30]
excel_name_courses = DIR_EXCEL / "courses.xlsx"
fields_for_agregator_vacancy = ['vacancy', 'company', 'salary', 'job_type', 'city', 'english', 'experience', 'vacancy_url', 'title', 'body']
sub_separator = "; "
double_n_before_field = 'vacancy_url'
