from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from selenium.webdriver.edge.service import Service
from threading import Thread
import os

class WebDriver:
    __drivers: list[webdriver.Edge] = []
    __options = webdriver.EdgeOptions()
    __options.headless = True
    __options.add_argument('log-level=3')
    __PATH = os.path.join(os.getcwd(), "msedgedriver.exe")
    
    def __init__(self) -> None:
        for _ in range(2):
            Thread(
                target= lambda: WebDriver.__drivers.append(
                    webdriver.Edge(
                        WebDriver.__PATH,
                        options=WebDriver.__options
                    )
                )
            ).start()


    @staticmethod
    def get_driver() -> webdriver.Edge:
        Thread(
            target= lambda: WebDriver.__drivers.append(
                webdriver.Edge(
                    WebDriver.__PATH,
                    options=WebDriver.__options
                )
            )
        ).start()
        return WebDriver.__drivers.pop()
        
    @staticmethod
    def awaitToGet(driver, url, target):
        driver.get(url)
        try:
            WebDriverWait(
                driver,
                10
            ).until(EC.presence_of_element_located((By.CSS_SELECTOR, target)))
            content = driver.page_source
            driver.close()
            return content
        except TimeoutException:
            return None