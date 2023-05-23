"""{
 "direction": "",
 "specialization": [],
 "programmingLanguage": [], - это на данном этапе в верстке не реализовано, будет приходить пустой массив
 "technologies": [], - это на данном этапе в верстке не реализовано, будет приходить пустой массив
 "level": ["", "trainee", "entry level", "junior", "middle", "senior", "director", "lead"],
 "country": [],
 "city": [],
 "state": [], - это на данном этапе в верстке не реализовано, будет приходить пустой массив
 "salary": ["", ""],
        "currency": "",
 "salaryOption": ["Почасовая", "За месяц", "За год", "До вычета налогов", "На руки"],
 "companyScope": [],
 "typeOfEmployment": ["", "fulltime", "parttime", "contract", "freelance", "internship", "volunteering"],
 "companyType": ["", "product", "outsourcing", "outstaff", "consulting", "notTechnical", "startup"],
 "companySize": ["1-200", "201-500", "501-1000", "1000"],
 "job_type": ["remote", "fulltime", "flexible", "office", "office/remote" ]
 }"""
from filters.filter_jan_2023.filter_jan_2023 import VacancyFilter

"""
The JSON above means how many fields you will receive, them types and values. It's will be static values from check boxes 
exception direction.
The direction field will contain free text.

How I'm doing it:
1. The direction field I can search:
  - through a pattern. I can find all keys words and choose vacancies by this professions. But it will take a more time 
    for pattern loop and get by request from database next step
 - in fields: title, body, profession
 
 I like the second method
 
2. Specialization - there are too many different values to search them in the profession, vacancy, body, title by "OR"

3. Level - the search in level fields. It's more easy than other tasks

4. Country - search in country field in backend. No that field now. I will create it and do the function for searching 
    country.

5. City - the same

6. Salary has two values from and till summ, Currency contain Eur, USD, BYR, RuR for example. I need to get from back 
    vacancies between this values 
 
7. salaryOption - I need to make the method for find this values from text. Add to database the same field with the same 
    values

8. typeOfEmployment - to create the same field in tables and to fill the same values. To find it in the body, the title    

9. companyType - static values. I need to create the same fields in tables on backend and fill them. 

10. companySize - the same

11. job_type - this field exists, but contains only one value - remote. Need to create method for search and fill 
    others static values.  
"""
from db_operations.scraping_db import DataBaseOperations
from utils.additional_variables import additional_variables as variables

class Predictive():
    def __init__(self):
        self.query = ''
        self.db = DataBaseOperations()
        self.tables=variables.valid_professions
        self.search_tables = []

    def get_search_tables(self, request_from_frontend):
        if 'direction' in request_from_frontend:
            profession = request_from_frontend['direction']
            if profession == 'development':
                self.search_tables.extend(['backend', 'frontend', 'mobile'])
            elif profession == 'game':
                self.search_tables.extend(['admin_last_session'])
            if profession in self.search_tables:
                self.search_tables.append(profession)
        else:
            self.search_tables = self.tables
        # tables_list = ''
        # for table in self.search_tables:
        #     tables_list += f'{table}, '
        return self.search_tables

    def get_full_query(self, request_from_frontend):
        print(request_from_frontend)
        query = ''

        for key in request_from_frontend:
            part_of_query = ''
            print(key)
            if key in ['job_type', 'level', 'city']:
                request=request_from_frontend[key]
                print(request)
                if request:
                    part_of_query = self.get_part_of_query(field=key, request=request)
                    print(part_of_query)
            elif key == 'country':
                request=request_from_frontend[key]
                print(request)
                if request:
                    part_of_query = self.get_part_of_query(field='city', request=request)
                    print(part_of_query)
            elif key == 'specialization':
                field = 'sub'
                print (field)
                request = request_from_frontend[key]
                print(request)
                if request:
                    part_of_query = self.get_part_of_query(field, request)
                    print(part_of_query)
            elif key == 'salary':
                part_of_query = self.get_query_salary(request_from_frontend)
                print(part_of_query)


            if part_of_query:
                query += f"{part_of_query} AND "
                print('QUERY:', query)

        if query:

            full_query = f"WHERE {query[:-5]}"
            print(full_query)
            return full_query


    def get_part_of_query(self, field, request):
        print(field)
        print(request)
        if type(request) is str:
            request = [request, ]
        query_part = "("
        for word in request:
            query_part += f"{field} LIKE '%{word.lower()}%' OR "
            print(query_part)
        return query_part[:-4] + ')'

    def get_query_salary(self, request_from_frontend):
        salary = request_from_frontend["salary"]
        salary_period = request_from_frontend["salaryOption"][0]
        if salary[0] == '':
            salary_from_query = ''
        else:
            salary_from = int(salary[0])
            if salary_period == "За месяц":
                salary_per_month_from = salary_from
            elif salary_period == "За год":
                salary_per_month_from = salary_from/12
            else:
                salary_per_month_from = salary_from * 160
            salary_from_query = f"salary_from_usd_month >= {salary_per_month_from}"

        if salary[1] == '':
            salary_to_query = ''
        else:
            salary_to = int(salary[1])
            if salary_period == "За месяц":
                salary_per_month_to = salary_to
            elif salary_period == "За год":
                salary_per_month_to = salary_to/12
            else:
                salary_per_month_to = salary_to * 160
            salary_to_query = f"salary_from_usd_month <= {salary_per_month_to}"

        if salary_from_query and salary_to_query:
            return f"{salary_from_query} AND {salary_to_query}"
        elif salary_from_query and not salary_to_query:
            return salary_from_query
        elif not salary_from_query and salary_to_query:
            return salary_to_query
        else:
            return ''
