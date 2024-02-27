from selenium.webdriver import Chrome, ChromeOptions
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

data = []

options = ChromeOptions()
options.add_argument('--start-maximized')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
driver = Chrome(options=options)
wait = WebDriverWait(driver, 10)

for page in range(1, 3):

    website = f'https://www.knowde.com/b/markets-personal-care/products/{page}'
    driver.get(website)

    print(f"---------------------- page number: {page} ----------------------")
    if page == 1:
        wait.until(EC.visibility_of_element_located((By.ID, 'onetrust-accept-btn-handler'))).click()

    products = driver.find_elements(By.CSS_SELECTOR, 'div[data-cy="product-card"]')

    count = 0
    for product in products:
        if count == 0 or count == count+4:
            product.find_element(By.CSS_SELECTOR, 'svg[data-testid="icon-icomoon--keyboard_arrow_down"]').click()

        brand = product.find_element('xpath', './a/div[2]/div/p[1]').text
        item = product.find_element('xpath', './a/div[2]/div/p[2]').text
        inci_name = product.find_element('xpath', './a/div[2]/div/div[1]/span[2]').text
        count += 1

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

df = pd.DataFrame(data)
df.to_csv('cosmetics_data.csv', index=False)