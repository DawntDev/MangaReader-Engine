from fake_useragent import FakeUserAgent
from typing import Dict, Optional, Union
from logging import Logger as LoggerT
from .logger import Logger

from aiohttp import ClientSession

@Logger(__name__, "requests")
async def request(
    url: str, 
    headers: Dict[str, Union[str, int, bool]] = {},
    cookies:Dict[str, Union[str, int, bool]] = None, 
    logger: LoggerT = None
) -> Optional[str]:
    
    if "User-Agent" not in headers:
        headers["User-Agent"] = FakeUserAgent().random
    
    async with ClientSession(headers=headers, cookies=cookies) as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(
                        f"REQUEST FAILED:\n\tSTATUS CODE: {response.status}\n\tURL: {url}\n\tRESPONSE: {response.content}"
                    )
                    return None
                logger.info(f"REQUEST SUCCESS: {url}")
                return "".join(await response.text())
        except Exception as err:
            logger.exception(f"REQUEST EXCEPTION:\nURL:{url}\n{err}")
            return None


from selenium.webdriver import Remote
from selenium.webdriver.edge.options import Options
from selenium_stealth import stealth
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import os

class WebDriver(Remote):
    __cmd_executor = os.getenv("SELENIUM_HOST")
    __base_options = Options()

    def __init__(self, stealth_bypass: bool = False) -> None:
        self.__base_options.add_argument(f"user-agent={FakeUserAgent().random}")
        super().__init__(
            command_executor=self.__cmd_executor,
            options=self.__base_options
        )
        
        if stealth_bypass:
            stealth(
                self,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True
            )

    @Logger(__name__, "requests")
    def lazy_request(
        self,
        url: str, 
        target: int, 
        time: int = 10, 
        logger: LoggerT = None
    ) -> Optional[str]:
        try:
            self.get(url)
            WebDriverWait(self, time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, target))
            )
            return self.page_source

        except TimeoutException:
            logger.exception(f"SELENIUM TARGET NOT FOUND:\n\tURL: {url}\n\t TIME: {time}\n\t TARGET: {target}")
        except Exception as err:
            logger.exception(f"SELENIUM EXCEPTION:\n\tURL: {url}\n\t TIME: {time}\n\t TARGET: {target}\nEXCEPTION:\n{err}")