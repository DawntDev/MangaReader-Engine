from bs4 import BeautifulSoup
from typing import List, Optional
from sqlalchemy.orm import Session
from logging import Logger as LoggerT
import time

from . import Scraper
from src.database.models import Manga
from src.database.schemas import (
    MangaScheme,
    MangaPreviewScheme,
    ChapterScheme
)
from src.utils import Logger
from src.utils.requesters import request, WebDriver


class LeerCapitulo(Scraper):
    __URL = "https://www.leercapitulo.co"
    __WORKING = False

    @Logger(__name__, "leercapitulo")
    @staticmethod
    async def __get_list(
        server_id: int, 
        page: str, 
        logger: LoggerT = None
    ) -> List[MangaPreviewScheme]:
        mangas: List[MangaPreviewScheme] = []
        
        for section in LeerCapitulo.__sections:    
            response = await request(
                f"{LeerCapitulo.__URL}/status/{section}/?page={page}"
            )
            time.sleep(0.25)
            if not response:
                LeerCapitulo.__sections.remove(section)
                continue
            
            soup = BeautifulSoup(response, "html.parser")
            items = soup.select("div.cover-manga a")
            
            for item in items:
                try:
                    title = item.get("title")
                    name_url = item.get("href").split("/manga/")
                    
                    mangas.append(
                        MangaPreviewScheme(
                            title=title,
                            name_url=name_url[-1][:-1],
                            server=server_id
                        )
                    )
                except Exception as err:
                    logger.exception(
                        f"LEERCAPITULO SERVER EXCEPTION IN __get_list:\nFUNCTION CALL:\n\t__get_list(\n\t\tpage:str = '{page}'\n\t\tserver_id: int = {server_id}\n\t)\nHTML ITEM: {item.prettify(encoding=None) if item else None}\nEXCEPTION:\n{err}"
                    )
        
        return mangas


    @Logger(__name__, "leercapitulo")
    @staticmethod
    async def get_info(
        server_id: int, 
        name_url: str, 
        logger: LoggerT = None
    ) -> Optional[MangaScheme]:
        response = await request(f"{LeerCapitulo.__URL}/manga/{name_url}/")
        if not response:
            return

        soup = BeautifulSoup(response, "html.parser")
        card = soup.select_one("div.media.manga-detail")
        chapters = soup.select_one("div.col-md-12.mar-top")
        manga = MangaScheme(
            title=name_url.capitalize(),
            server=server_id,
            name_url=name_url,
            rating=0.0,
            nsfw=False
        )
        
        try:
            title = card.select_one("h1.title-manga").text
            if title:
                manga.title = title.strip()
            
            cover_url = card.select_one("img").get("src")
            manga.cover_url = f"{LeerCapitulo.__URL}{cover_url}" if cover_url else None
            
            manga.type_of = "manga"
            for data in card.select("div.media-body p span"):
                if "Escribe:" in data.text:
                    manga.type_of = data.text.split("Escribe: ")[-1].lower()
                    break
            
            genres = card.select("div.media-body p a")
            manga.genres = [
                genre.text.strip().lower() 
                for genre in genres 
                if genre.text
            ]
            
            overview = chapters.select_one("div.manga-content p").text
            manga.overview = overview.strip() if overview else None
            
            chapters_list = chapters.select("div.total-chapter div.chapter-list ul li h4 a")
            
            manga.chapters_list = [
                ChapterScheme(
                    name=chapter.text,
                    url_name=chapter.get("href")[:-1].split("/")[-1]
                )
                for chapter in chapters_list
                if chapter.text
            ]
            
            return manga
        except Exception as err:
            logger.exception(
                f"LEERCAPITULO SERVER EXCEPTION IN get_info:\nFUNCTION CALL:\n\tget_info(\n\t\tserver_id:int = {server_id}\n\t\tname_url: str = '{name_url}'\n\t)\nHTML CARD: {card.prettify(encoding=None) if card else None}\nHTML CHAPTERS: {chapters.prettify(encoding=None) if chapters else None}\nEXCEPTION:\n{err}"
            )
    
    @staticmethod
    async def get_chapter(name_url: str, chapter_url: str) -> Optional[List[str]]:
        driver = WebDriver()
        response = driver.lazy_request(
            f"{LeerCapitulo.__URL}/leer/{name_url}/{chapter_url}/",
            "#page_select"
        )
        driver.quit()

        if not response:
            return
        
        soup = BeautifulSoup(response, "html.parser")
        images = soup.select("select#page_select > option")

        return [el.get("value") for el in images] 
    
    
    @staticmethod
    async def scan(server_id: int, force: bool, db: Session):
        i = 1
        LeerCapitulo.__WORKING = True
        LeerCapitulo.__sections = ["completed", "ongoing", "paused" , "cancelled"]

        while LeerCapitulo.__WORKING:
            elements = await LeerCapitulo.__get_list(server_id, i)
            mangas = []

            if not elements:
                LeerCapitulo.__WORKING = False
                break

            for element in elements[:]:
                manga = await LeerCapitulo.get_info(server_id, element.name_url)
                time.sleep(1)

                if not manga:
                    continue

                manga = manga.model_dump()
                if force:
                    passing = False
                    for value in manga.values():
                        if value is None:
                            passing = True
                            break
                    if passing:
                        continue

                exist = (
                    db.query(Manga)
                    .filter(
                        (Manga.name_url == manga["name_url"])
                        &
                        (Manga.server == manga["server"])
                    )
                    .first()
                )

                if exist:
                    continue

                manga.pop("chapters_list")
                mangas.append(Manga(**manga))

            db.bulk_save_objects(mangas)
            db.commit()
            i += 1

    @staticmethod
    async def update(
        server_id: int, 
        force: bool, 
        elements: List[Manga], 
        db: Session
    ): 
        LeerCapitulo.__WORKING = True
        for element in elements:
            manga = await LeerCapitulo.get_info(server_id, element.name_url)
            time.sleep(1)
            
            if not manga and not force:
                db.query(Manga).filter_by(name_url=element.name_url).delete()
            else:
                manga = manga.model_dump()
                if force:
                    passing = False
                    for value in manga.values():
                        if value is None:
                            passing = True
                            break
                    if passing:
                        continue
                    
                manga.pop("chapters_list")
                db.query(Manga).filter_by(name_url=element.name_url).update(manga)

            db.commit()

        LeerCapitulo.__WORKING = False

    @staticmethod
    def in_working() -> bool:
        return LeerCapitulo.__WORKING