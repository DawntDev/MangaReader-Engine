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

from playwright.async_api import async_playwright, TimeoutError

@Logger(__name__, "requests")
async def lazy_request(
    url: str,
    target: str,
    timeout: int = 1000,
    headers: Dict[str, Union[str, int, bool]] = {},
    logger: LoggerT = None
) -> Optional[str]:
    if "User-Agent" not in headers:
        headers["User-Agent"] = FakeUserAgent().random
        
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(extra_http_headers=headers)
        page = await context.new_page()
        
        try:
            await page.goto(url)
            await page.wait_for_selector(target, timeout=timeout)
            return await page.content()
        except TimeoutError:
            logger.exception(f"PLAYWRIGHT TARGET NOT FOUND:\n\tURL: {url}\n\t TIME: {timeout}\n\t TARGET: {target}")
        except Exception as err:
            logger.exception(f"PLAYWRIGHT EXCEPTION:\n\tURL: {url}\n\t TIME: {timeout}\n\t TARGET: {target}\nEXCEPTION:\n{err}")
        finally:
            await browser.close()