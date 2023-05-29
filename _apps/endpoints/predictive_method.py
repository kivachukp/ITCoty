from db_operations.scraping_db import DataBaseOperations
from utils.additional_variables import additional_variables as variables

class Predictive():
    def __init__(self, request_from_frontend):
        self.query = ''
        self.db = DataBaseOperations()
        self.tables = variables.valid_professions
        self.search_tables = []
        self.request_from_frontend = request_from_frontend

    def get_search_tables(self):
        if 'direction' in self.request_from_frontend:
            profession = self.request_from_frontend['direction']
            if profession == 'development':
                self.search_tables.extend(['backend', 'frontend', 'mobile'])
            elif profession in self.tables:
                self.search_tables.append(profession)
            else:
                self.search_tables = self.tables
        else:
            self.search_tables = self.tables

        return self.search_tables

    def get_full_query(self):

        query = ''
        for key in self.request_from_frontend:
            part_of_query = ''
            if key in ['job_type', 'level', 'city']:
                request = self.request_from_frontend[key]
                if request:
                    part_of_query = self.get_part_of_query(field=key, request=request)
            elif key == 'country':
                request = self.request_from_frontend[key]
                if request:
                    part_of_query = self.get_part_of_query(field='city', request=request)
            elif key == 'specialization':
                subs_list = [x for y in variables.valid_subs.values() for x in y]
                request = self.request_from_frontend[key]
                if request:
                    for sub in request:
                        if sub not in subs_list:
                            part_of_query = ''
                        else:
                            if sub == 'unity':
                                self.search_tables.append('backend')
                            part_of_query = self.get_part_of_query(field='sub', request=request)

            elif key == 'salary':
                part_of_query = self.get_query_salary()

            if part_of_query:
                query += f"{part_of_query} AND "

        if query:
            full_query = f"WHERE {query[:-5]}"
            return full_query

    def get_part_of_query (self, field, request):
        if type(request) is str:
            request = [request, ]
        query_part = "("
        for word in request:
            query_part += f"{field} LIKE '%{word}%' OR "
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
