from bs4 import BeautifulSoup
from typing import List, Optional
from sqlalchemy.orm import Session
from logging import Logger as LoggerT
import time

from . import Scraper
from src.database.models import Manga
from src.database.schemas import MangaScheme, MangaPreviewScheme, ChapterScheme
from src.utils import Logger
from src.utils.requesters import request


class Nartag(Scraper):
    __URL = "https://visortraduccionesamistosas.com"
    __WORKING = False

    @Logger(__name__, "nartag")
    @staticmethod
    async def __get_list(
        server_id: int, 
        page: str, 
        logger: LoggerT = None
    ) -> List[MangaPreviewScheme]:
        response = await request(f"{Nartag.__URL}/biblioteca?page={page}")
        if not response:
            return []

        soup = BeautifulSoup(response, "html.parser")
        items = soup.find_all("div", {"class": "manga__item"})
        mangas = []

        for item in items:
            try:
                title = item.select_one("h4 > a")
                mangas.append(
                    MangaPreviewScheme(
                        title=title.text,
                        name_url=title.get("href").split("/l/")[-1],
                        server=server_id
                    )
                )
            except Exception as err:
                logger.exception(
                    f"NARTAG SERVER EXCEPTION IN __get_list:\nFUNCTION CALL:\n\t__get_list(\n\t\tpage:str = '{page}'\n\t\tserver_id: int = {server_id}\n\t)\nHTML ITEM: {item.prettify(encoding=None) if item else None}\nEXCEPTION:\n{err}"
                )

        return mangas

    @Logger(__name__, "nartag")
    @staticmethod
    async def get_info(
        server_id: int, 
        name_url: str, 
        logger: LoggerT = None
    ) -> Optional[MangaScheme]:
        response = await request(f"{Nartag.__URL}/l/{name_url}")
        if not response:
            return

        soup = BeautifulSoup(response, "html.parser")
        card = soup.find("section", {"class": "manga__card"})
        chapters = soup.find("section", {"class": "manga__chapters"})
        manga = MangaScheme(
            title=name_url.capitalize(),
            server=server_id,
            name_url=name_url,
            nsfw=False
        )

        try:
            title = card.select_one("div.manga__info h2").text
            if title:
                manga.title = title.strip()

            cover_url = card.select_one("div.manga__cover > img").get("data-src")
            manga.cover_url = cover_url

            type_of = card.select_one("div.manga__type > a").text
            manga.type_of = "manhwa"
            if type_of:
                if "Novela" in type_of:
                    manga.type_of = "novel"
                else:
                    manga.type_of = type_of.lower().strip().split("\n")[-1]
            
            rating = card.select_one("div.manga__info div.rating__count").children
            manga.rating = (
                float(x) 
                if (x := next(rating).strip()) 
                else None
            )

            genres = card.select("div.manga__categories div.category__item")
            manga.genres = [
                tag.text.strip().lower() 
                for tag in genres 
                if tag.text
            ]

            overview = card.select_one("div.manga__info > div.manga__description").text
            manga.overview = overview.strip() if overview else None

            chapters_list = chapters.select("div.chapters__list > div.chapter__item")
            manga.chapters_list = [
                ChapterScheme(
                    name=el.find("h4", {"class": "chapter__title"}).text,
                    url_name=el.findChild("a").get("href").split("/")[-1]
                )
                for el in chapters_list
                if not el.find(
                    "button", {"class": "chapter__premium"}
                )
            ]

            return manga

        except Exception as err:
            logger.exception(
                f"NARTAG SERVER EXCEPTION IN get_info:\nFUNCTION CALL:\n\tget_info(\n\t\tserver_id:int = {server_id}\n\t\tname_url: str = '{name_url}'\n\t)\nHTML CARD: {card.prettify(encoding=None) if card else None}\nHTML CHAPTERS: {chapters.prettify(encoding=None) if chapters else None}\nEXCEPTION:\n{err}"
            )

    @staticmethod
    async def get_chapter(name_url: str, chapter_url: str) -> Optional[List[str]]:
        response = await request(f"{Nartag.__URL}/v/{name_url}/{chapter_url}")
        if not response:
            return
        
        soup = BeautifulSoup(response, "html.parser")
        content = soup.find("div", {"class": "view__content"})
        
        if "view__novel" in content["class"]:
            return [content.text]
        
        images = [
            img.get("data-src")
            for img in content.select("div.reader__item > img")
        ]
        
        return images
        
    
    @staticmethod
    async def scan(server_id: int, force: bool, db: Session):
        i = 1
        Nartag.__WORKING = True

        while Nartag.__WORKING:
            elements = await Nartag.__get_list(server_id, i)
            mangas = []

            if not elements:
                Nartag.__WORKING = False
                break

            for element in elements:
                manga = await Nartag.get_info(server_id, element.name_url)
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
        Nartag.__WORKING = True
        for element in elements:
            manga = await Nartag.get_info(server_id, element.name_url)
            time.sleep(1)
            
            if not manga:
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

        Nartag.__WORKING = False

    @staticmethod
    def in_working() -> bool:
        return Nartag.__WORKING
