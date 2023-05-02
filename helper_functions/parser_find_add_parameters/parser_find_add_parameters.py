import re
from helper_functions.parser_find_add_parameters import parser_find_data
from db_operations.scraping_db import DataBaseOperations
from utils.additional_variables.additional_variables import countries_cities_table, valid_job_types
from helper_functions.cities_and_countries.cities_parser import CitiesAndCountries
from patterns._export_pattern import export_pattern

class FinderAddParameters:

    def __init__(self,):
        self.db = DataBaseOperations()
        self.cities_countries = CitiesAndCountries()

    def clean_text_special_symbols(self, main_dict=True, input_dict=None):
        special_symbols = {}
        if main_dict:
            special_symbols = parser_find_data.special_symbols
        if type(input_dict) is dict:
            special_symbols.update(input_dict)
        for item in special_symbols:
            try:
                self.text = self.text.replace(item, special_symbols[item])
            except:
                pass

    def salary_to_set_form(self, **kwargs):
        currency_dict = parser_find_data.currency_dict

        self.text = kwargs['text'] if 'text' in kwargs else ''
        if not self.text:
            response = ['-', '-', '-', '-']
            print(response)
            return response

        self.region = kwargs['region'] if 'region' in kwargs else None
        match self.region:
            case "BY": currency_dict =  parser_find_data.by_dict

        # search numbers
        print('-'*10)
        print('add_parameters: self.text: ', self.text)
        self.clean_text_special_symbols()
        match = re.findall(r"[0-9,]+[\s]?[0-9]+[\s]?[0-9]{0,4}", self.text)
        self.salary_list = [number.replace(' ', '').replace(',', '') for number in match]
        if 'тыс' in self.text:
            salary_list = []
            for number in self.salary_list:
                salary_list.append(f"{number}000")
            self.salary_list = salary_list


        # search currency
        if self.salary_list:
            match = []
            if len(self.salary_list) < 2:
                self.salary_list.append('-')
            for key in currency_dict:
                match = re.findall(fr"{key.lower()}", self.text.lower())
                if match and match[0]:
                    self.salary_list.append(currency_dict[key])
                    break
            if not match:
                salary = self.salary_list[0]
                if len(salary) > 5:
                    self.salary_list.append('RuR')
            if len(self.salary_list)<3:
                self.salary_list.append('-')

        # searching Per Period
        if self.salary_list:
            match = []
            period_dict = parser_find_data.period_dict
            for period in period_dict:
                for value in period_dict[period]:
                    match = re.findall(fr"{value.lower()}", self.text.lower())
                    if match and match[0]:
                        self.salary_list.append(period)
                        break
            if not match and len(self.salary_list) < 4:
                self.salary_list.append('Per Month')

        if not self.salary_list:
            self.salary_list = ['-', '-', '-', '-']

        print(self.salary_list)

        return self.salary_list

    async def compose_salary_dict_from_salary_list(self, salary_list):
        if salary_list:
            try:
                salary_from = int(salary_list[0]) if salary_list[0] and salary_list[0] != '-' else None
            except Exception as e:
                salary_from = None
                print(e)
            try:
                salary_to = int(salary_list[1]) if salary_list[1] and salary_list[1] != '-' else None
            except Exception as e:
                salary_to = None
                print(e)
            if salary_from or salary_to:
                salary_currency = salary_list[2] if salary_list[2] and salary_list[2] != '-' else None
                salary_period = salary_list[3] if salary_list[3] and salary_list[3] != '-' else None
            else:
                salary_currency = salary_period = None
            return {"salary_from": salary_from, "salary_to": salary_to, "salary_currency": salary_currency, "salary_period": salary_period}
        else:
            return False

    async def find_city_country(self, text):
        if not text:
            return False
        text = text.replace('ё', 'е')
        text_list = text.split(',')

        remove_elements = []
        for item in text_list:
            match = re.findall(r'[a-zA-Zа-яА-Я\s\-]+', item)
            if match and len(match[0]) != len(item):
                remove_elements.append(item)

        for item in remove_elements:
            text_list.remove(item)

        if len(text_list) == 2:
            city = text_list[0].strip().title()
            country = text_list[1].strip().title()
            if city == country:
                city = ''
            return await self.check_and_write_city_country(city=city, country=country)
        elif len(text_list) == 1:
            return await self.check_and_write_city_country(city_or_country=text_list[0])
        elif len(text_list) > 2:
            results_list = []
            for element in text_list:
                result = await self.check_and_write_city_country(city_or_country=element)
                if result and len(result.split(', ')) == 2 and result.split(', ')[0]:
                    return result
                else:
                    if result:
                        results_list.append(result)
            for element in results_list:
                if re.findall(rf", [a-zA-Z\s]+", element):
                    return element
            return results_list[0]
                # if result:
                #     return result

    async def check_and_write_city_country(self, **kwargs):
        country_pin = ''
        city_or_country = kwargs['city_or_country'].strip() if 'city_or_country' in kwargs else ''
        city = kwargs['city'].strip() if 'city' in kwargs else ''
        country = kwargs['country'].strip() if 'country' in kwargs else ''
        if not city and not country and not city_or_country:
            return False

        if city_or_country:
            city_or_country = await self.cities_countries.google_translate_to_english(word=city_or_country)
            city_or_country = await self.refactoring_country(city_or_country)
            response = self.db.get_all_from_db(
                table_name=countries_cities_table,
                param=f"WHERE city LIKE '%{city_or_country.strip()}%'",
                field='city, country',
                without_sort=True
            )
            if response:
                response_country = self.db.get_all_from_db(
                    table_name=countries_cities_table,
                    param=f"WHERE country LIKE '%{city_or_country.strip()}%'",
                    field='country',
                    without_sort=True
                )
                if response_country:
                    return f", {response_country[0][0]}"

                if len(response) == 1:
                    return f"{response[0][0]}, {response[0][1]}"
                else:
                    return f"{city_or_country.strip()}, "
            else:
                # city_or_country = await self.refactoring_country(city_or_country)
                response = self.db.get_all_from_db(
                    table_name=countries_cities_table,
                    param=f"WHERE country LIKE '%{city_or_country.strip()}%'",
                    field='city, country',
                    without_sort=True
                )
                if response:
                    if len(response) == 1:
                        return f"{response[0][0]}, {response[0][1]}"
                    else:
                        return f", {city_or_country.strip()}"

        if city:
            city = await self.cities_countries.google_translate_to_english(word=city)
            city = await self.refactoring_country(city)
        if country:
            country = await self.cities_countries.google_translate_to_english(word=country)
            country = await self.refactoring_country(country)

        if city and country:
            response = self.db.get_all_from_db(
                table_name=countries_cities_table,
                param=f"WHERE LOWER(country) LIKE '%{country.lower()}%' and LOWER(city) LIKE '%{city.lower()}%'",
                field='city, country',
                without_sort = True
            )
            if response:
                return f"{response[0][0]}, {response[0][1]}"
            else:
                city = await self.refactoring_country(city)
                response = self.db.get_all_from_db(
                    table_name=countries_cities_table,
                    param=f"WHERE LOWER(country) LIKE '%{city.lower()}%' and LOWER(city) LIKE '%{country.lower()}%'",
                    field='city, country',
                    without_sort=True
                )
                if response:
                    return f"{response[0][0]}, {response[0][1]}"
                else:
                    country_pin = country
                    country = ''

        if city and not country:
            response = self.db.get_all_from_db(
                table_name=countries_cities_table,
                param=f"WHERE LOWER(city) LIKE '%{city.lower()}%'",
                field='city, country',
                without_sort=True
            )
            if response:
                if len(response) == 1:
                    return f"{response[0][0]}, {response[0][1]}"
                else:
                    response = self.db.get_all_from_db(
                        table_name=countries_cities_table,
                        param=f"WHERE LOWER(country) LIKE '%{city.lower()}%'",
                        field='country',
                        without_sort=True
                    )
                    if response:
                        return f", {response[0][0]}"
                    else:
                        return f"{city}, "
            else:
                if country_pin:
                    city = ''
                    country = country_pin

        if country and not city:
            response = self.db.get_all_from_db(
                table_name=countries_cities_table,
                param=f"WHERE LOWER(country) LIKE '%{country.lower()}%'",
                field='country',
                without_sort = True
            )
            if response:
                return f", {country.strip()}"
            else:
                return False
        return False

    async def refactoring_country(self, country):
        if "america" in country.lower() or country.lower() in ["usa", "сша"]:
            country = 'United States'
        if "england" in country.lower():
            country = 'United Kingdom'
        if 'españa' in country.lower():
            country = 'Spain'
        if country.lower() in ['рф', 'rf', 'ru']:
            country = 'Russia'
        if country.lower() in ["by", "bу", "ву"]:
            country = 'Belarus'
        return country

    async def get_parameter(self, presearch_results: list, pattern: str, return_value: str):
        for element in presearch_results:
            for pattern_item in pattern:
                match = re.findall(rf"{pattern_item}", element)
                if match:
                    return return_value
    async def get_job_types(self, return_dict):
        job_types_var = valid_job_types
        self.job_types = ''
        for i in job_types_var:
            parameter = await self.get_parameter(
                presearch_results=[
                    return_dict['job_type'],
                    return_dict['title'] + return_dict['body'],
                ],
                pattern=export_pattern['others'][i]['ma'],
                return_value=i,
            )
            if parameter:
                if len(self.job_types)>0:
                    self.job_types += ", "
                self.job_types += parameter
            if not self.job_types:
                self.job_types += 'office'
        return self.job_types

# f= FinderAddParameters()
# f.salary_to_set_form(text='$15,000 - $30,000 ')