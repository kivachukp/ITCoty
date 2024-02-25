import time
from selenium import webdriver

# driver = webdriver.Chrome('/path/to/chromedriver')  # Optional argument, if not specified will search path.
# driver.get('http://www.google.com/')
# time.sleep(5)
# # Let the user actually see something!
# search_box = driver.find_element_by_name('q')
# search_box.send_keys('ChromeDriver')
# search_box.submit()
# time.sleep(5) # Let the user actually see something!
# driver.quit()


# import time
# from selenium import webdriver
from selenium.webdriver.chrome.service import Service
# service = Service('/path/to/chromedriver')
# service.start()
# driver = webdriver.Remote(service.service_url)
# driver.get('http://www.google.com/')
# time.sleep(5) # Let the user actually see something!
# driver.quit()
self.browser = webdriver.Chrome(
    executable_path=chrome_driver_path,
    options=options,
)
