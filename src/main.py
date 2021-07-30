import os
import re

import requests

from dotenv import load_dotenv

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.errorhandler import WebDriverException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver

def create_driver() -> WebDriver:
    if os.environ.get('HEADLESS'):
        opts = Options()
        opts.headless = True

        return WebDriver(options=opts)

    return WebDriver()


def wait_for_element(driver: WebDriver, attrib: str, value: str) -> WebElement:
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((attrib, value))
        )
    except WebDriverException:
        print('Unable to wait for', attrib, value)
        exit(-1)

    return driver.find_element(attrib, value)


def click_element(driver: WebDriver, attrib: str, value: str) -> None:
    wait_for_element(driver, attrib, value)
    
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((attrib, value))
        ).click()
    except WebDriverException:
        print('Unable to click', attrib, value)

    driver.implicitly_wait(2)
    

def spire_wait(driver: WebDriver):
    while True:
        try:
            WebDriverWait(driver, 60 * 2).until_not(
                EC.visibility_of_any_elements_located((By.ID, "processing"))
            )
            break
        except WebDriverException:
            print("Spire seems to be a little slow, you should try again later.")
            exit(-1)


def text_of(elem: WebElement):
    s = elem.text

    for r in ["\n", "\t", "  "]:
        s = s.replace(r, " ")

    return s.strip()


if __name__ == '__main__':
    load_dotenv()

    driver = create_driver()

    driver.get('https://www.spire.umass.edu/')
    click_element(driver, By.NAME, 'CourseCatalogLink')

    driver.switch_to.frame(wait_for_element(driver, By.ID, 'ptifrmtgtframe'))
    
    spire_wait(driver)

    click_element(driver, By.CSS_SELECTOR, '#CLASS_SRCH_WRK2_SUBJECT\$108\$ > option[value=COMPSCI]')
    click_element(driver, By.CSS_SELECTOR, '#CLASS_SRCH_WRK2_SSR_EXACT_MATCH1 > option[value=G]')
    wait_for_element(driver, By.ID, 'CLASS_SRCH_WRK2_CATALOG_NBR$8$').send_keys("312")
    click_element(driver, By.ID, 'CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')

    spire_wait(driver)

    courses = []
    i = 0
    while True:
        try:
            course = text_of(wait_for_element(driver, By.ID, f'DERIVED_CLSRCH_DESCR200${i}'))

            if re.search(os.getenv('course-regex'), course, re.I):
                courses.append(course)

            i = i + 1
        except:
            break

    driver.close()

    if len(courses) > 0:
        requests.post(os.getenv('hook'), data={
            'content': "@everyone \n" + "\n".join(courses)
        })
