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
from src.utils import Logger, Cleaner
from src.utils.requesters import request


class Ikigai(Scraper):
    __URL = "https://es.ikigaiweb.lat"
    __WORKING = False

    @Logger(__name__, "ikigai")
    @staticmethod
    async def __get_list(
        server_id: int, 
        page: str, 
        logger: LoggerT
    ) -> List[MangaPreviewScheme]:
        response = await request(
            f"{Ikigai.__URL}/series/?pagina={page}",
            cookies={"nsfw-mode": 1}
        )

        if not response:
            return []

        soup = BeautifulSoup(response, "html.parser")
        items = soup.select("section.container > section > ul > li")
        mangas = []

        for item in items:
            try:
                title = item.findChild("h2").text
                name_url = item.findChild("a").get("href")
                mangas.append(
                    MangaPreviewScheme(
                        title=title.strip(),
                        name_url=name_url.split("/series/")[-1][:-1],
                        server=server_id
                    )
                )
            except Exception as err:
                logger.exception(
                    f"IKIGAI SERVER EXCEPTION IN __get_list:\nFUNCTION CALL:\n\t__get_list(\n\t\tpage:str = '{page}'\n\t\tserver_id: int = {server_id}\n\t)\nHTML ITEM: {item.prettify(encoding=None)}\nEXCEPTION:\n{err}"
                )

        return mangas

    @Logger(__name__, "ikigai")
    @staticmethod
    async def get_info(
        server_id: int, 
        name_url: str, 
        logger: LoggerT = None
    ) -> Optional[MangaScheme]:
        response = await request(
            f"{Ikigai.__URL}/series/{name_url}",
            cookies={"data-saving": 0}
        )

        if not response:
            return

        soup = BeautifulSoup(response, "html.parser")
        card = soup.select_one("div.flex > div.w-full.mx-auto.space-y-8")
        chapters = soup.select_one("div.flex > div.w-full > section.space-y-4")
        manga = MangaScheme(
            title=name_url.capitalize(),
            server=server_id,
            name_url=name_url
        )

        try:
            title = card.select_one("article > div > h1").text
            if title:
                manga.title = title.strip()

            cover_url = card.select_one("article > img").get("src")
            manga.cover_url = cover_url

            type_of = card.select_one("article > ul > li > a").text
            if type_of:
                type_of = type_of.strip().lower()

                if type_of == "comic":
                    manga.type_of = "manhwa"
                else:
                    manga.type_of = "novel"

            rating = card.select_one(
                "div.relative div.text-start > span"
            ).text
            manga.rating = (
                float(rating.split("/")[0]) if rating else None
            )

            genres = card.select("article > div > ul > li a")
            manga.genres = [
                tag.text.strip().lower() for tag in genres if tag.text
            ]

            manga.nsfw = any(
                genre in manga.genres for genre in ("ecchi", "+18")
            )

            overview = card.select_one("article > div > p").text
            manga.overview = Cleaner.text(overview.strip()) if overview else None

        except Exception as err:
            logger.exception(
                f"IKIGAI SERVER EXCEPTION IN get_info:\nFUNCTION CALL:\n\tget_info(\n\t\tserver_id:int = {server_id}\n\t\tname_url: str = '{name_url}'\n\t)\nHTML CARD: {card.prettify(encoding=None)}\nHTML CHAPTERS: {chapters.prettify(encoding=None)}\nEXCEPTION:\n{err}"
            )
            return

        try:
            chapters_list = [
                ChapterScheme(
                    name=el.select_one("div h3.font-semibold").text.strip(),
                    url_name=el.get("href").split("/capitulo/")[-1][:-1],
                )
                for el in chapters.select("ul.grid > li a")
            ]

            max_pagination = max([
                int(pag.text)
                for pag in chapters.select("nav > ul > li span")
                if str.isdigit(f"{pag.text}")
            ])
    
            for pag in range(2, max_pagination):
                response = await request(
                    f"https://es.ikigaiweb.lat/series/{name_url}?pagina={pag}"
                )
                time.sleep(0.25)
                soup = BeautifulSoup(response, "html.parser")
                chapters = soup.select_one(
                    "div.flex > div.w-full > section.space-y-4"
                )
                chapters = [
                    ChapterScheme(
                        name=el.select_one("div h3.font-semibold").text.strip(),
                        url_name=el.get("href").split("/capitulo/")[-1][:-1],
                    )
                    for el in chapters.select("ul.grid > li a")
                ]

                chapters_list = [*chapters_list, *chapters]
            manga.chapters_list = chapters_list

        except Exception as err:
            logger.exception(
                f"IKIGAI SERVER EXCEPTION IN get_info (EXTRACTING_CHAPTER_LIST_EXCEPTION):\nHTML CHAPTERS: {chapters.prettify(encoding=None)}\nPAG: {pag}\nEXCEPTION:\n{err}"
            )
            
            return

        return manga

    @staticmethod
    async def get_chapter(
        name_url: str, chapter_url: str
    ) -> Optional[List[str]]:
        response = await request(
            f"https://es.ikigaiweb.lat/capitulo/{chapter_url}/",
            cookies={"data-saving": 0, "nsfw-mode": 1},
        )
        if not response:
            return

        soup = BeautifulSoup(response, "html.parser")
        container = soup.select_one(
            "section.container.mx-auto.flex-center.flex-col.my-16"
        )

        novel = container.findChild("div", {"class": "prose"})
        if novel:
            return [novel.text]
        else:
            images = [
                img.get("src")
                for img in container.select(
                    "div.w-full > div.w-full > img"
                )
            ]

            return images

    @staticmethod
    async def scan(server_id: int, force: bool, db: Session):
        i = 1
        Ikigai.__WORKING = True

        while Ikigai.__WORKING:
            elements = await Ikigai.__get_list(server_id, i)
            mangas = []

            if not elements:
                Ikigai.__WORKING = False
                break

            for element in elements[:]:
                manga = await Ikigai.get_info(
                    server_id, element.name_url
                )
                time.sleep(1)

                if not manga and not force:
                    continue

                exist = (
                    db.query(Manga)
                    .filter_by(name_url=manga.name_url)
                    .first()
                )
                if exist:
                    continue

                manga = manga.model_dump()
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
        db: Session,
    ):
        Ikigai.__WORKING = True
        for element in elements:
            manga = await Ikigai.get_info(server_id, element.name_url)
            time.sleep(1)

            if not manga and not force:
                db.query(Manga).filter_by(
                    name_url=element.name_url
                ).delete()
            else:
                manga = manga.model_dump()
                manga.pop("chapters_list")

                db.query(Manga).filter_by(
                    name_url=element.name_url
                ).update(manga)

            db.commit()

        Ikigai.__WORKING = False

    @staticmethod
    def in_working() -> bool:
        return Ikigai.__WORKING
