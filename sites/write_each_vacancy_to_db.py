from datetime import datetime

from db_operations.scraping_db import DataBaseOperations
from filters.filter_jan_2023.filter_jan_2023 import VacancyFilter
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters
from utils.additional_variables.additional_variables import vacancy_table, reject_table, \
    table_list_for_checking_message_in_db as tables, \
    admin_database, archive_database, admin_table_fields
from helper_functions.helper_functions import get_salary_usd_month, replace_NoneType, get_tags, \
    get_additional_values_fields, compose_simple_list_to_str, compose_to_str_from_list

class HelperSite_Parser:
    def __init__(self, **kwargs):
        self.report = kwargs['report'] if 'report' in kwargs else None
        self.db = DataBaseOperations(report=self.report)
        self.filter = VacancyFilter(report=self.report)
        self.find_parameters = FinderAddParameters()
        self.results_dict = {}
        self.profession = {}


    async def write_each_vacancy(self, results_dict):
        self.results_dict = results_dict
        response = {}
        response_from_db = {}

        if self.report:
            self.report.parsing_report(
                link_current_vacancy = self.results_dict['vacancy_url'],
                title = self.results_dict['title'],
                body = self.results_dict['body'],
            )
        check_vacancy_not_exists = True

        # search this vacancy in database
        if 'vacancy_url' in self.results_dict and self.results_dict['vacancy_url']:
            check_vacancy_not_exists = self.db.check_exists_message_by_link_or_url(
                vacancy_url=self.results_dict['vacancy_url'],
                table_list=tables
            )

        # get profession's parameters
        if check_vacancy_not_exists:
            self.profession = self.filter.sort_profession(
                title=self.results_dict['title'],
                body=self.results_dict['body'],
                get_params=False,
                check_vacancy=True,
                check_vacancy_only_mex=True,
                check_contacts=False,
                vacancy_dict=self.results_dict
            )

            self.profession = self.profession['profession']

            if self.report:
                self.report.parsing_report(ma=self.profession['tag'], mex=self.profession['anti_tag'])

            # fill all fields
            await self.fill_all_fields()

            if self.profession['profession']:
                self.results_dict['approved'] = 'approves by filter'
                response_from_db = self.db.push_to_admin_table(
                    results_dict=self.results_dict,
                    profession=self.profession,
                    check_or_exists=True
                )
                if self.report:
                    self.report.parsing_report(approved=self.results_dict['approved'])
                if not response_from_db:
                    return False
                response['vacancy'] = 'found in db by title-body' if response_from_db['has_been_found'] else 'written to db'
            else:
                self.results_dict['profession'] = ''

                self.results_dict['approved'] = 'rejects by filter'
                self.db.check_or_create_table(
                    table_name=reject_table,
                    fields=vacancy_table
                )
                self.db.push_to_db_common(
                    table_name=reject_table,
                    fields_values_dict=self.results_dict,
                    notification=True
                )
                if self.report:
                    self.report.parsing_report(approved=self.results_dict['approved'])

                response['vacancy'] = 'no vacancy by anti-tags'
        else:
            response['vacancy'] = 'found in db by link'
        if self.report:
            self.report.parsing_switch_next(switch=True)

        # print('??????????? finish_write_each_vacancy')

        return {'response': response, "profession": self.profession, 'response_dict': response_from_db}

    async def get_name_session(self):
        current_session = self.db.get_all_from_db(
            table_name='current_session',
            param='ORDER BY id DESC LIMIT 1',
            without_sort=True,
            order=None,
            field='session',
            curs=None
        )
        for value in current_session:
            current_session = value[0]
        return  current_session

    async def fill_all_fields(self):

        for key in set(self.results_dict.keys()).difference(set(admin_table_fields.split(", "))):
            self.results_dict.pop(key)
        for key in self.results_dict:
            if type(self.results_dict[key]) in (set, list, tuple):
                self.results_dict[key] = ", ".join(self.results_dict[key])

        # refactoring and filling additional vacancy fields
        self.results_dict['tags'] = get_tags(self.profession)
        self.results_dict['full_tags'] = self.profession['tag'].replace("'", "")
        self.results_dict['full_anti_tags'] = self.profession['anti_tag'].replace("'", "")
        self.results_dict['created_at'] = datetime.now()
        self.results_dict['level'] = self.profession['level']
        self.results_dict['company'] = self.db.clear_title_or_body(self.results_dict['company'])
        self.results_dict['profession'] = compose_simple_list_to_str(data_list=self.profession['profession'], separator=', ')
        self.results_dict['sub'] = compose_to_str_from_list(data_list=self.profession['sub'])
        if not self.results_dict['time_of_public']:
            self.results_dict['time_of_public'] = datetime.now()
        self.results_dict = get_additional_values_fields(
            dict_in=self.results_dict
        )
        # salary refactoring
        region = 'BY' if 'praca.by' in self.results_dict['vacancy_url'] else None
        if 'salary' in self.results_dict and self.results_dict['salary']:
            salary = self.find_parameters.salary_to_set_form(text=self.results_dict['salary'], region=region)
            salary = await self.find_parameters.compose_salary_dict_from_salary_list(salary)
            for key in salary:
                self.results_dict[key] = salary[key]
            self.results_dict = await get_salary_usd_month(
                vacancy_dict=self.results_dict
            )
        self.results_dict['job_type'] = await self.find_parameters.get_job_types(self.results_dict)
        self.results_dict = await replace_NoneType(results_dict=self.results_dict)

        # city and country refactoring
        if self.results_dict['city']:
            city_country = await self.find_parameters.find_city_country(text=self.results_dict['city'])
            print(f"city_country: {self.results_dict['city']} -> {city_country}")
            if city_country:
                self.results_dict['city'] = city_country
            else:
                self.results_dict['city'] = ''


