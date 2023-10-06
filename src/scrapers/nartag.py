from bs4 import BeautifulSoup
from ..schemas.scraper import Scraper, IncompleteManga
import aiohttp


class Nartag(Scraper):
    __URL = "https://nartag.com"

    @staticmethod
    async def get_manga_list(page: int):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{Nartag.__URL}/l/page/{page}/") as response:
                if response.status != 200:
                    return []
                soup = BeautifulSoup("".join(await response.text()), "html.parser")

        elements = soup.findAll("div", {"class": "page-item-detail"})
        mangas = []
        for element in elements:
            if element.find("i", {"class": "fa-lock"}):
                continue
            title = element.find("h3").findChild("a").text
            name_url = element.find("h3").findChild("a").get("href").split("/")[-2]
            cover_url = element.find("img") and element.find("img").get("src")
            mangas.append({
                "title": title, 
                "nameURL": name_url, 
                "coverURL": cover_url,
                "server": "Nartag"
            })

        return mangas
    
    @staticmethod
    async def get_manga_info(manga: IncompleteManga):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{Nartag.__URL}/l/{manga['nameURL']}") as response:
                if response.status != 200:
                    return False
                soup = BeautifulSoup("".join(await response.text()), "html.parser")
        
        output_manga = manga.copy()
        if not output_manga.get("title"):
            element = soup.select_one("div.post-content > div.post-title > h1")
            output_manga["title"] = element.text if element else manga["nameURL"].capitalize()
        if not output_manga.get("typeOf"):
            output_manga["typeOf"] = "Manhwa"
        if not output_manga.get("rating"):
            element = soup.select_one("span#averagerate")
            output_manga["rating"] = float(element.text) if element else 0.0
        if not output_manga.get("genre"):
            elements = soup.select("div.genres-content > a")
            output_manga["genre"] = [el.text.capitalize() for el in elements]
        if not output_manga.get("overview"):
            element = soup.select_one("div.manga-about.manga-info")
            output_manga["overview"] = element.text.strip() if element else ""
        if not output_manga.get("coverURL"):
            element = soup.select_one("div.summary_image img")
            output_manga["coverURL"] = element.get("src") if element else None
        if not output_manga.get("chapterList"):
            elements = soup.select("div.chapter__actions")
            output_manga["chapterList"] = [
                el.findChild("a")
                .get("href")
                .split("/")[-1]
                .split("capitulo-")[-1] 
            for el in elements]
            
        return output_manga
    
    @staticmethod
    async def get_manga_chapter(name_url: str, chapter: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{Nartag.__URL}/v/{name_url}/capitulo-{chapter}/") as content:
                if content.status != 200:
                    return False
                soup = BeautifulSoup("".join(await content.text()), "html.parser")
        
        
        images = soup.findAll("div", {"class": "reader__item"})
        if not images:
            text = soup.find("div", {"class": "reading-content"})
            return text.get_text()

        images = [
            *map(
                lambda el: el.findChild("img").get("data-src").strip(),
                images
            )
        ]
        return images