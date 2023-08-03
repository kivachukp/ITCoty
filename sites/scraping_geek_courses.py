from selenium.webdriver.common.by import By
import pandas as pd
from sites.scraping_careerspace import CareerSpaceGetInformation
from utils.additional_variables.additional_variables import excel_name_courses

class Courses(CareerSpaceGetInformation):

    def __init__(self):
        self.common_dict = {}
        self.key = ''
        self.link_list = []
        self.pages = []
        self.cards = []
        super().__init__()
        self.url = 'https://geeklink.io/it-courses/'

    async def get_content(self, db_tables=None):
        await super().get_content()
        await self.post_to_excel()
        return self.common_dict

    async def get_link_message(self, raw_content):
        boxes = self.browser.find_elements(By.XPATH, "//*[@class='cat-details-inner']/div/h3/a")
        print("len boxes: ", len(boxes))
        for box in boxes:
            link = box.get_attribute('href')
            self.link_list.append(link)

        for link in self.link_list:
            self.browser.get(link)
            self.key = self.browser.find_element(By.XPATH, "//*[@class='rtcl-listing-header']/h1").text
            self.common_dict[self.key] = []
            print(self.key.capitalize())
            self.pages = self.browser.find_elements(By.XPATH, "//*[@class='page-item']/a")
            page_amount = self.pages[-2].text.split('\n')[-1].strip()
            for n in range(1, int(page_amount)+1):
                self.browser.get(link + f"page/{n}/")
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await self.get_card_content()
                print('n= ', n)
            print('NEXT')

    async def get_card_content(self):
        card = "//*[@class='rtin-compare rtin-el-button buttontocourse']/a"
        course = "//*[@class='listing-title rtcl-listing-title']/a"
        sites = self.browser.find_elements(By.XPATH, card)
        courses = self.browser.find_elements(By.XPATH, course)

        for n in range(0, len(sites)):
            link = sites[n].get_attribute('href')
            course_name = courses[n].text
            self.common_dict[self.key].append({'link': link, 'course': course_name})

    async def post_to_excel(self, common_dict=None):
        if common_dict:
            self.common_dict = common_dict
        excel_data_dict = {}
        for key in self.common_dict:
            courses_name = []
            links = []

            for i in self.common_dict[key]:
                courses_name.append(i['course'])
                links.append(i['link'])
            excel_data_dict[key] = courses_name.copy()
            excel_data_dict[f"{key}: links"] = links.copy()

        length = 0
        for i in excel_data_dict.values():
            if length < len(i):
                length = len(i)

        for key in excel_data_dict:
            if len(excel_data_dict[key]) < length:
                for i in range(len(excel_data_dict[key]), length):
                    excel_data_dict[key].append('')

        df = pd.DataFrame(excel_data_dict)
        try:
            df.to_excel(excel_name_courses, sheet_name='Courses')
            print('got it')
        except:
            pass





