import asyncio
from translate import Translator
from googletrans import Translator as google_translator
import requests
from db_operations.scraping_db import DataBaseOperations
from utils.additional_variables.additional_variables import countries_cities_table

class CitiesAndCountries:

    def __init__(self):
        self.geography_dict = {}
        self.db = DataBaseOperations()


    async def get_all_countries_and_cities(self):
        self.db.create_table_common(
            field_list=["country VARCHAR(60)", "city VARCHAR (150)"],
            table_name=countries_cities_table
        )

        self.geography_dict = {}
        API_KEY = 'cGlwOHRKTHVRcVk5MUkxa3ZyQnhPY3kyYWJnOGppeHVhODVucWNjVg=='
        headers = {
            'X-CSCAPI-KEY': API_KEY
        }
        url_counties = 'https://api.countrystatecity.in/v1/countries'
        url_cities = 'https://api.countrystatecity.in/v1/countries/[ciso]/cities'
        all_countries = requests.request(method='GET', url=url_counties, headers=headers)
        list_countries = all_countries.json()

        for country in list_countries:

            all_cities = requests.request(method='GET', url=f'https://api.countrystatecity.in/v1/countries/{country["iso2"]}/cities', headers=headers)
            list_cities = all_cities.json()

            for city in list_cities:
                if country['name'] not in self.geography_dict:
                    self.geography_dict[country['name']] = []
                self.geography_dict[country['name']].append(city['name'])
                self.db.push_to_db_common(
                    table_name='countries_cities',
                    fields_values_dict={
                        'country': country['name'],
                        'city': city['name']
                    }
                )

    async def translate_to_english(self, word):
        translator = Translator(from_lang="russian", to_lang="English")
        try:
            translation = translator.translate(word)
        except Exception as e:
            print(e)
            translation = ''
        # print(translation)
        return translation if translation != '.' else word

    async def google_translate_to_english(self, word: str):
        translator = google_translator(service_urls=[
            'translate.google.com',
            'translate.google.co.kr',
        ])
        translation = translator.translate(text=word, dest='en')
        print(f"Translator: {word}={translation.text}")
        return translation.text if translation else ''


# cities_parser = CitiesAndCountries()
# asyncio.run(cities_parser.get_all_countries_and_cities())