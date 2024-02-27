from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

data = []

for y in range(1, 3):
    website = f'https://www.knowde.com/b/markets-personal-care/products/{y}'
    path = '/Users/kdavid3mbp/Python/chrome_driver64/chromedriver'
    driver = webdriver.Chrome(path)
    driver.get(website)

    for x in range(1, 37):
        products = driver.find_elements('xpath', f'//*[@id="__next"]/main/div/div[3]/div[3]/div[1]/div[2]/div[{x}]')

        for product in products:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(('xpath', './div/div/svg'))).click()

            brand = product.find_element('xpath', './a/div[2]/div/p[1]').text
            item = product.find_element('xpath', './a/div[2]/div/p[2]').text
            inci_name = product.find_element('xpath', './a/div[2]/div/div[1]/span[2]').text
            try:
                ingredient_origin = product.find_element('xpath', './a/div[2]/div/div[3]/span[2]').text
            except NoSuchElementException:
                ingredient_origin = 'null'
            try:
                function = product.find_element('xpath', './a/div[2]/div/div[2]/span[2]').text
            except NoSuchElementException:
                function = 'null'
            try:
                benefit_claims = product.find_element('xpath', './a/div[2]/div/div[4]/span[2]').text
            except NoSuchElementException:
                benefit_claims = 'null'
            try:
                description = product.find_element('xpath', './a/div[2]/div/p[3]').text
            except NoSuchElementException:
                description = 'null'
            try:
                labeling_claims = product.find_element('xpath', './a/div[2]/div/div[5]/span[2]').text
            except NoSuchElementException:
                labeling_claims = 'null'
            try:
                compliance = product.find_element('xpath', './a/div[2]/div/div[6]/span[2]').text
            except NoSuchElementException:
                compliance = 'null'
            try:
                hlb_value = product.find_element('xpath', './a/div[2]/div/div[4]/span[2]').text
            except NoSuchElementException:
                hlb_value = 'null'
            try:
                end_uses = product.find_element('xpath', '/a/div[2]/div/div[4]/span[2]').text
            except NoSuchElementException:
                end_uses = 'null'
            try:
                cas_no = product.find_element('xpath', './a/div[2]/div/div[5]/span[2]').text
            except NoSuchElementException:
                cas_no = 'null'
            try:
                chemical_name = product.find_element('xpath', './a/div[2]/div/div[2]/span[2]').text
            except NoSuchElementException:
                chemical_name = 'null'
            try:
                synonyms = product.find_element('xpath', './a/div[2]/div/div[6]/span[2]').text
            except NoSuchElementException:
                synonyms = 'null'
            try:
                chemical_family = product.find_element('xpath', './a/div[2]/div/div[5]/span[2]').text
            except NoSuchElementException:
                chemical_family = 'null'
            try:
                features = product.find_element('xpath', './a/div[2]/div/div[7]/span[2]').text
            except NoSuchElementException:
                features = 'null'
            try:
                grade = product.find_element('xpath', './a/div[2]/div/div[5]/span[2]').text
            except NoSuchElementException:
                grade = 'null'

        dict = {
            'brand': brand,
            'item': item,
            'inci_name': inci_name,
            'ingredient_origin': ingredient_origin,
            'function': function,
            'benefit_claims': benefit_claims,
            'description': description,
            'labeling_claims': labeling_claims,
            'compliance': compliance,
            'hlb_value': hlb_value,
            'end_uses': end_uses,
            'cas_no': cas_no,
            'chemical_name': chemical_name,
            'synonyms': synonyms,
            'chemical_family': chemical_family,
            'features': features,
            'grade': grade
        }

        data.append(dict)
        print('Saving: ', dict['brand'])

# Closes driver once for loop is completed
driver.quit()

df = pd.DataFrame(data)
df.to_csv('/Users/kdavid3mbp/Python/cosmetics_data.csv', index=False)