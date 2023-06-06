from bs4 import BeautifulSoup
from src.webdriver import WebDriver
from ..schemas.scraper import Scraper, IncompleteManga
from time import sleep
import aiohttp


class LeerCapitulo(Scraper):
    __URL = "https://www.leercapitulo.com"
    
    @staticmethod
    async def get_manga_list(page: int):
        initial = *map(chr, range(65, 91)), *range(10) #Tuple with A-Z and 0-9
        contents = []
        async with aiohttp.ClientSession() as session:
            for letter in initial:
                async with session.get(f"{LeerCapitulo.__URL}/initial/{letter}/?page={page}") as response:
                    if response.status == 200:
                        contents.append(await response.text())
                    else:
                        contents.append(False)
                    sleep(0.25)
        mangas = []
        for content in contents:
            if not content:
                mangas.append({})
                continue
            
            soup = BeautifulSoup("".join(content), "html.parser")
            elements = soup.select("div.cover-manga a")
            for element in elements:
                title = element.get("title")
                name_url = element.get("href")
                cover_url = element.find("img") and element.find("img").get("src")
                mangas.append({
                    "title": title,
                    "nameURL": name_url,
                    "coverURL": cover_url,
                    "server": "LeerCapitulo"
                })
        if all(len(el) == 0 for el in mangas):
            return []
        return mangas
    
    @staticmethod
    async def get_manga_info(manga: IncompleteManga):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{LeerCapitulo.__URL}{manga['nameURL']}") as response:
                if response.status != 200:
                    print(await response.text())
                    return False
                soup = BeautifulSoup("".join(await response.text()), "html.parser")

        output_manga = manga.copy()
        if not output_manga.get("title"):
            output_manga["title"] =  soup.select_one("h1", {"class": "title-manga"}).text
        
        common_info = soup.find("p", {"class": "description-update"})
        if not output_manga.get("typeOf"):
            for data in common_info.find_all("span"):
                if "Escribe:" in data.text:
                    output_manga["typeOf"] = data.text.split("Escribe: ")[-1]
        if not output_manga.get("rating"):
            output_manga["rating"] = 0.0
        if not output_manga.get("genre"):
            output_manga["genre"] = [*map(lambda el: (el.text).capitalize(), common_info.find_all("a"))]

        if not output_manga.get("overview"):
            output_manga["overview"] = soup.select_one("div.manga-content p").text.strip()
        
        if not output_manga.get("coverURL"):
            img =  soup.select_one("div.manga-detail img")
            output_manga["coverURL"] = img.get("src") if img else None
        if not output_manga.get("chapterList"):
            chapters = soup.select("div.chapter-list a")
            output_manga["chapterList"] = [
                *map(
                        lambda el: el.get("href").split("/")[-2], 
                        chapters
                    )
                ]
        
        return output_manga
    
    @staticmethod  
    async def get_manga_chapter(name_url:str, chapter: str):
        name_url = "/".join(name_url.split("/")[2:])
        driver = WebDriver.get_driver()
        request = WebDriver.awaitToGet(
            driver,
            f"{LeerCapitulo.__URL}/leer/{name_url}{chapter}/",
            "#page_select"
        )
        
        if not request:
            return False
        
        soup = BeautifulSoup(request, "html.parser")
        images = soup.select("select#page_select > option")
        
        return [el.get("value") for el in images]