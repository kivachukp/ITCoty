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
from patterns.data_pattern._data_pattern import filter_main_page_dict
class Predictive():
    def __init__(self):
        self.query = ''
        self.db = DataBaseOperations()
        self.search_tables = set()
        self.pattern_main_page = filter_main_page_dict

    def get_full_query(self, request_from_frontend):
        query = ''
        part_of_query = ''
        professions = set()

        if 'direction' in request_from_frontend:
            query_direction = self.direction_method(text=request_from_frontend['direction'])
        if 'specialization' in request_from_frontend:
            query_specialization = self.specialization_method(request_from_frontend['specialization'])
        # if 'programmingLanguage' in request_from_frontend:
        #     query_programmingLanguage = self.programmingLanguage_method(request_from_frontend['programmingLanguage'])
        # if 'technologies' in request_from_frontend:
        #     query_technologies = self.technologies_method(request_from_frontend['technologies'])
        # if 'level' in request_from_frontend:
        #     query_level = self.level_method(request_from_frontend['level'])
        # if 'country' in request_from_frontend:
        #     query_country = self.country_method(request_from_frontend['country'])
        # if 'city' in request_from_frontend:
        #     query_city = self.city_method(request_from_frontend['city'])
        # if 'state' in request_from_frontend:
        #     query_state = self.state_method(request_from_frontend['state'])
        # if 'salary' in request_from_frontend:
        #     query_salary = self.salary_method(request_from_frontend['salary'])
        # if 'salaryOption' in request_from_frontend:
        #     query_salaryOption = self.salaryOption_method(request_from_frontend['salaryOption'])
        # if 'companyScope' in request_from_frontend:
        #     query_companyScope = self.companyScope_method(request_from_frontend['companyScope'])
        # if 'typeOfEmployment' in request_from_frontend:
        #     query_typeOfEmployment = self.typeOfEmployment_method(request_from_frontend['typeOfEmployment'])
        # if 'companyType' in request_from_frontend:
        #     query_companyType = self.companyType_method(request_from_frontend['companyType'])
        # if 'companySize' in request_from_frontend:
        #     query_companySize = self.job_companySize(request_from_frontend['companySize'])
        # if 'job_type' in request_from_frontend:
        #     query_job_type = self.job_type_method(request_from_frontend['job_type'])


        for key in request_from_frontend:

            if key == 'level':
                fields_list = ['level']
            elif key == 'job_type':
                fields_list = ['job_type']
            elif key == 'salary':
                fields_list = ['salary']
                part_of_query = self.get_query_salary(request_from_frontend[key], fields_list)
            else:
                fields_list = ['body', 'title', 'vacancy', 'profession']

            if key not in ['salary',]:
                part_of_query = self.get_part_of_query(
                    request_list=request_from_frontend[key],
                    fields_list=fields_list,
                    dict_name=key
                )
            if part_of_query:
                query += f"({part_of_query}) AND "
        if query:
            # query = f"SELECT * FROM admin_last_session WHERE {query[:-5]}"
            query = f"WHERE {query[:-5]}"
        return query

    def direction_method(self, text):
        """
        function defines tables by professions and if there are not tables it return part of global query
        """
        part_of_query = ''
        self.search_tables = self.direction_find_professions(text=text)
        if not self.search_tables:
            self.search_tables = variables.valid_professions
            part_of_query = f"(LOWER(title) LIKE '%{text.lower()}%' OR LOWER(body) LIKE '%{text.lower()}%' OR LOWER(vacancy) LIKE '%{text.lower()}%')"
        return part_of_query

        part_of_request = '('
        if not text:
            return ''
        for field in fields_list:
            part_of_request += f"LOWER({field}) LIKE '%{text.lower()}%' OR "
        return part_of_request[:-4] + ')'

    def direction_find_professions(self, text):
        """
        Define professions by export_pattern
        """
        vacancy_filter = VacancyFilter()
        professions = vacancy_filter.sort_profession(
            title=text, body='', check_contacts=False, check_vacancy=False, check_level=False,
            get_params=False, only_one_profession_sub=False
        )
        pass
        return professions['profession']['profession']

    def get_part_of_query(self, request_list, fields_list, dict_name):
        words_list = []
        part_of_request = '('
        if not request_list:
            return ''
        if type(request_list) is str:
            request_list = [request_list,]

        # compose the list from helper dict values by each key
        for key_word in request_list:
            if key_word:
                if key_word in dict_name:
                    words_list.extend(dict_name[key_word.lower()])
                else:
                    words_list.append(key_word.lower())

        for word in words_list:
            part_of_request += f"{self.direction_method(word, fields_list)} OR "

        part_of_request = part_of_request[:-4]
        if part_of_request:
            return part_of_request + ")"
        else:
            return ''

    def get_query_salary(self, request_from_frontend, fields_list):
        salary_from = request_from_frontend["salary"][0]
        salary_to = request_from_frontend["salary"][1]
        salary_period = request_from_frontend["salaryOption"][0]
        if salary_period == "За месяц":
            salary_per_month_from = int(request_from_frontend["salary"][0])
            salary_per_month_to = int(request_from_frontend["salary"][1])

        elif salary_period == "Почасовая":
            salary_per_hour_from = request_from_frontend["salary"][0]
            salary_per_hour_to = request_from_frontend["salary"][1]
            salary_per_month_from = salary_per_hour_from*160
            salary_per_month_to = salary_per_hour_to*160

        elif salary_period == "За год":
            salary_per_year_from = int(request_from_frontend["salary"][0])
            salary_per_year_to = int(request_from_frontend["salary"][1])
            salary_per_month_from = salary_per_year_from/12
            salary_per_month_to = salary_per_year_to/12

        salary_query = f"salary_from_usd_month >= {salary_per_month_from} AND salary_to_usd_month <= {salary_per_month_to}"




    def multipurpose_method(self, one_parameter_dict):
        if one_parameter_dict.keys()[0] in self.pattern_main_page:
            pass

# result = Predictive().get_full_query(request_from_frontend=request_from_frontend)
# print(result)
