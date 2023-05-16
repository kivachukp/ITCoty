from db_operations.scraping_db import DataBaseOperations
from filters.filter_jan_2023.filter_jan_2023 import VacancyFilter
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters
from utils.additional_variables.additional_variables import table_list_for_checking_message_in_db as tables, \
    admin_database, archive_database
from helper_functions.helper_functions import get_salary_usd_month

class HelperSite_Parser:
    def __init__(self, **kwargs):
        self.report = kwargs['report'] if 'report' in kwargs else None
        self.db = DataBaseOperations(report=self.report)
        self.filter = VacancyFilter(report=self.report)
        self.find_parameters = FinderAddParameters()

    async def write_each_vacancy(self, results_dict):
        response = {}
        profession = []
        response_from_db = {}
        # print('??????????? start_write_each_vacancy')

        if self.report:
            self.report.parsing_report(
                link_current_vacancy = results_dict['vacancy_url'],
                title = results_dict['title'],
                body = results_dict['body'],
            )
        check_vacancy_not_exists = True
        if 'vacancy_url' in results_dict and results_dict['vacancy_url']:
            check_vacancy_not_exists = self.db.check_exists_message_by_link_or_url(
                vacancy_url=results_dict['vacancy_url'],
                table_list=tables
            )

        if check_vacancy_not_exists:
            profession = self.filter.sort_profession(
                title=results_dict['title'],
                body=results_dict['body'],
                get_params=False,
                check_vacancy=True,
                check_vacancy_only_mex=True,
                check_contacts=False
            )

            profession = profession['profession']

            if self.report:
                self.report.parsing_report(ma=profession['tag'], mex=profession['anti_tag'])

            if profession['profession']:
                #city and country refactoring
                if results_dict['city']:
                    city_country = await self.find_parameters.find_city_country(text=results_dict['city'])
                    print(f"city_country: {results_dict['city']} -> {city_country}")
                    if city_country:
                        results_dict['city'] = city_country
                    else:
                        results_dict['city'] = ''

                # salary refactoring
                if 'praca.by' in results_dict['vacancy_url']:
                    region = 'BY'
                else:
                    region = None

                if 'salary' in results_dict and results_dict['salary']:
                    salary = self.find_parameters.salary_to_set_form(text=results_dict['salary'], region=region)
                    salary = await self.find_parameters.compose_salary_dict_from_salary_list(salary)
                    for key in salary:
                        results_dict[key] = salary[key]
                    pass

                    results_dict = await get_salary_usd_month(
                        vacancy_dict=results_dict
                    )

                results_dict['job_type'] = await self.find_parameters.get_job_types(results_dict)

                response_from_db = self.db.push_to_admin_table(
                    results_dict=results_dict,
                    profession=profession,
                    check_or_exists=True
                )
                if not response_from_db:
                    return False
                response['vacancy'] = 'found in db by title-body' if response_from_db['has_been_found'] else 'written to db'
            else:
                response['vacancy'] = 'no vacancy by anti-tags'
        else:
            response['vacancy'] = 'found in db by link'
        if self.report:
            self.report.parsing_switch_next(switch=True)

        # print('??????????? finish_write_each_vacancy')

        return {'response': response, "profession": profession, 'response_dict': response_from_db}

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

