from db_operations.scraping_db import DataBaseOperations
from filters.filter_jan_2023.filter_jan_2023 import VacancyFilter
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters
from utils.additional_variables.additional_variables import table_list_for_checking_message_in_db as tables

class HelperSite_Parser:
    def __init__(self, **kwargs):
        self.report = kwargs['report'] if 'report' in kwargs else None
        self.db = DataBaseOperations(report=self.report)
        self.filter = VacancyFilter(report=self.report)
        self.find_parameters = FinderAddParameters()

    async def write_each_vacancy(self, results_dict):
        response = {}
        profession = []
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


                # #city and country refactoring
                # city_country = await self.find_parameters.find_city_country(text=results_dict['city'])
                # with open("./excel/city.txt", 'a', encoding="utf-8") as file:
                #     file.write(f"---------------\nfrom parser: {results_dict['city']}\nresult: {city_country}")
                # print(f"city_country: {city_country}")

                # salary refactoring
                if 'salary' in results_dict and results_dict['salary']:
                    salary = self.find_parameters.salary_to_set_form(text=results_dict['salary'])
                    results_dict['salary'] = ", ".join(salary)

                response_from_db = self.db.push_to_admin_table(
                    results_dict=results_dict,
                    profession=profession,
                    check_or_exists=True
                )
                response['vacancy'] = 'found in db by title-body' if response_from_db else 'written to db'
            else:
                response['vacancy'] = 'no vacancy by anti-tags'
        else:
            response['vacancy'] = 'found in db by link'
        if self.report:
            self.report.parsing_switch_next(switch=True)
        return {'response': response, "profession": profession}

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

