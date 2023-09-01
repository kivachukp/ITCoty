import time
import os
import re

from unidecode import unidecode
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from filters.filter_jan_2023.filter_jan_2023 import VacancyFilter
from helper_functions.helper_functions import list_to_string, compose_to_str_from_list
from sites.write_each_vacancy_to_db import HelperSite_Parser


class ParseRemoteWorksHub:

    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.chat_name = 'https://remote.works-hub.com'
        self.all_job_urls = []
        self.all_job_info = []

    def extract_time_delta(self, element):
        pattern_days = r'\b\d+\s*day(s)?\b'
        pattern_months = r'\b\d+\s*month(s)?\b'
        pattern_years = r'\b\d+\s*year(s)?\b'

        days_match = re.search(pattern_days, element)
        months_match = re.search(pattern_months, element)
        years_match = re.search(pattern_years, element)

        if days_match:
            days = int(re.findall(r'\d+', days_match.group())[0])
            return timedelta(days=days)
        elif months_match:
            months = int(re.findall(r'\d+', months_match.group())[0])
            return timedelta(days=months * 30)  # Approximate month to days
        elif years_match:
            years = int(re.findall(r'\d+', years_match.group())[0])
            return timedelta(days=years * 365)  # Approximate years to days
        else:
            return timedelta(days=0)

    def convert_into_timestamp(self, time_of_public):
        current_date = datetime.now()
        time_delta = self.extract_time_delta(time_of_public)
        publication_date = current_date - time_delta
        timestamp = publication_date.strftime('%Y-%m-%d %H:%M:%S')

        return timestamp

    def extract_tech_stack(self, job_soup):
        job_names = []

        list_items = job_soup.find_all('li', class_='chakra-wrap__listitem')
        for item in list_items:
            job_name = item.find('span', class_='css-15muqah').text
            if job_name not in job_names:
                job_names.append(job_name)

        return job_names

    def scrape_job_urls(self):
        url = 'https://remote.works-hub.com/jobs/search'
        self.driver.get(url)

        while True:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            urls = soup.find_all(class_='css-2k1arv')

            for url_element in urls:
                url = url_element.find(class_='chakra-linkbox__overlay css-1y1dcnw')
                if url:
                    job_url = 'https://remote.works-hub.com' + url['href']
                    if job_url not in self.all_job_urls:
                        self.all_job_urls.append(job_url)

            try:
                show_more_button = self.driver.find_element(By.XPATH,
                                                            "//a[contains(@class, 'chakra-button') and contains(@href, 'page=')]")
                show_more_button.click()

                time.sleep(10)  # Give the page time to load new content

            except NoSuchElementException:
                print('No more "Show more jobs" button')
                break

    def get_profession_string(self, job_title, job_body):
        vacancy_filter = VacancyFilter()
        result = vacancy_filter.sort_profession(title=job_title, body=job_body)
        sorted_professions = result['profession']['profession']
        profession_string = list_to_string(sorted_professions, ', ')

        return profession_string

    def scrape_job_info(self, job_url):
        job_info = {}  # Create a new dictionary for each job
        print(f'JOB URL: {job_url}')
        self.driver.get(job_url)

        time.sleep(2)

        job_page_source = self.driver.page_source
        job_soup = BeautifulSoup(job_page_source, 'html.parser')

        job_title_element = job_soup.find(class_='chakra-heading css-1q9iviz')
        job_body_element = job_soup.find('div', class_='css-v2buah')
        job_company_name_element = job_soup.find('h3', class_='chakra-heading css-1y77mwq')
        job_type_element = job_soup.find('p', class_='chakra-text css-1k9bm2e')
        job_salary_element = job_soup.find('p', class_='chakra-text css-1mbviog')
        job_time_of_public = job_soup.find('p', class_='chakra-text css-10p8l4x')

        job_info['chat_name'] = self.chat_name

        if job_title_element:
            job_title = job_title_element.text
            job_info['title'] = job_title
        else:
            return None  # Skip this job if title is not found

        if job_body_element:
            job_body = job_body_element.text
            job_info['body'] = unidecode(job_body)
        else:
            return None

        profession_string = self.get_profession_string(job_title, job_body)

        if profession_string:
            job_info['profession'] = profession_string

        job_info['vacancy'] = job_title
        job_info['vacancy_url'] = job_url

        if job_company_name_element:
            company_name = job_company_name_element.text
            job_info['company'] = company_name
        else:
            return None

        job_info['english'] = ''

        if job_type_element:
            job_type = job_type_element.text
            job_info['relocation'] = unidecode(job_type)
            job_info['job_type'] = unidecode(job_type)

        job_info['city'] = ''

        if job_salary_element:
            job_salary = job_salary_element.text
            job_info['salary'] = job_salary

        job_info['experience'] = ''
        job_info['contacts'] = ''

        if job_time_of_public:
            time_of_public = job_time_of_public.text
            time_of_public_timestamp = self.convert_into_timestamp(time_of_public)
            job_info['time_of_public'] = time_of_public_timestamp
            job_info['created_at'] = time_of_public_timestamp

        job_info['agregator_link'] = ''
        job_info['session'] = ''
        job_info['sended_to_agregator'] = ''

        job_info['sub'] = compose_to_str_from_list({profession_string: self.extract_tech_stack(job_soup)})

        self.all_job_info.append(job_info)

    def run(self):
        helper_parser = HelperSite_Parser()
        self.scrape_job_urls()

        for job_url in self.all_job_urls:
            job_info = self.scrape_job_info(job_url)

            if job_info:
                self.all_job_info.append(job_info)
                #helper_parser.write_each_vacancy(job_info)

        for job_info in self.all_job_info:
            print(job_info)

    def close_driver(self):
        self.driver.quit()


if __name__ == "__main__":
    parser = ParseRemoteWorksHub()
    parser.run()
    parser.close_driver()