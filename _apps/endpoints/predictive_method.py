from db_operations.scraping_db import DataBaseOperations
from utils.additional_variables import additional_variables as variables
from datetime import date, timedelta
class Predictive():
    def __init__(self, request_from_frontend):
        self.query = ''
        self.db = DataBaseOperations()
        self.tables = variables.valid_professions
        self.search_table = variables.vacancies_database
        self.request_from_frontend = request_from_frontend

    # def get_search_tables(self):
    #     if 'direction' in self.request_from_frontend:
    #         profession = self.request_from_frontend['direction']
    #         if profession == 'development':
    #             self.search_tables.extend(['backend', 'frontend', 'mobile'])
    #         elif profession in self.tables:
    #             self.search_tables.append(profession)
    #         else:
    #             self.search_tables = self.tables
    #     else:
    #         self.search_tables = self.tables
    #
    #     return self.search_tables

    def get_full_query(self):
        print('get_full_query function is starting')
        query = ''
        for key in self.request_from_frontend:
            part_of_query = ''
            request = self.request_from_frontend[key]
            if request:
                if key in ['job_type', 'level', 'city']:
                    part_of_query = self.get_part_of_query(field=key, request=request)
                elif key == 'direction':
                    if request == 'development':
                        request = ['backend', 'frontend', 'mobile']
                    part_of_query = self.get_part_of_query(field='profession', request=request)
                elif key == 'country':
                    part_of_query = self.get_part_of_query(field='city', request=request)
                elif key == 'specialization':
                    subs_list = [x for y in variables.valid_subs.values() for x in y]
                    for sub in request:
                        if sub not in subs_list:
                            part_of_query = ''
                        else:
                            part_of_query = self.get_part_of_query(field='sub', request=request)
                elif key == 'salary':
                    part_of_query = self.get_query_salary()

            if part_of_query:
                query += f"{part_of_query} AND "

        date_start = date.today() - timedelta(days=20)
        full_query = f"WHERE {query} DATE (created_at) BETWEEN '{date_start}' AND '{date.today()}'"
        print(full_query)
        return full_query

    def get_part_of_query (self, field, request):
        if type(request) is str:
            request = [request, ]
        query_part = "("
        for word in request:
            query_part += f"{field} LIKE '%{word}%' OR " if word else ''
        if query_part == "(":
            return ''
        else:
            return query_part[:-4] + ')'

    def get_query_salary(self):
        salary = self.request_from_frontend["salary"]
        salary_period = self.request_from_frontend.get("salaryOption")
        if salary[0] == '':
            salary_from_query = ''
        else:
            salary_from = int(salary[0])
            if salary_period == "perMonth":
                salary_per_month_from = salary_from
            elif salary_period == "perYear":
                salary_per_month_from = salary_from/12
            elif salary_period == "hourly":
                salary_per_month_from = salary_from * 160
            else:
                return ''
            salary_from_query = f"salary_from_usd_month >= {salary_per_month_from}"

        if salary[1] == '':
            salary_to_query = ''
        else:
            salary_to = int(salary[1])
            if salary_period == "perMonth":
                salary_per_month_to = salary_to
            elif salary_period == "perYear":
                salary_per_month_to = salary_to/12
            elif salary_period == "hourly":
                salary_per_month_to = salary_from * 160
            else:
                return ''
            salary_to_query = f"salary_from_usd_month <= {salary_per_month_to}"

        if salary_from_query and salary_to_query:
            return f"{salary_from_query} AND {salary_to_query}"
        elif salary_from_query and not salary_to_query:
            return salary_from_query
        elif not salary_from_query and salary_to_query:
            return salary_to_query
        else:
            return ''
