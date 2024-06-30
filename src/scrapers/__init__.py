from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from abc import ABC, abstractmethod

from src.database.models import Manga
from src.database.schemas import MangaScheme, MangaPreviewScheme

class Scraper(ABC):
    __URL: str
    __WORKING: bool

    # Regenerate Methods
    @staticmethod
    @abstractmethod
    async def __get_list(server_id: int, page: str) -> List[MangaPreviewScheme]:
        """
        Returns a list of mangas of the server to be scraped.

        Arguments:
        ----------
        server_id: `int`
            Server ID in the database

        page: `str`
            Specifies the page number to scrape from. Each page number corresponds to a unique set of mangas on the server.
        """

    @staticmethod
    @abstractmethod
    async def get_info(server_id: int, name_url: str) -> Optional[MangaScheme]:
        """
        Returns information about a specific manga.

        Arguments:
        ----------
        server_id: `int`
            Server ID in the database

        name_url: `str`
            The URL associated with the manga on the server. This URL is used to locate and retrieve the manga's information.
        """

    # Persisten Methods
    @staticmethod
    @abstractmethod
    async def get_chapter(name_url: str, chapter_url: str) -> Optional[List[str]]:
        """
        Returns the resources that make up a specific chapter of the manga.

        Arguments:
        ---------
        name_url: `str`
            The URL associated with the manga on the server. This URL is used to locate and retrieve the manga's information.

        chapter_url: `str`
            Chapter from which resources need to be obtained.
        """

    @staticmethod
    @abstractmethod
    async def scan(server_id: int, force: bool, db: Session):
        """
        It makes a scan of the sleeves that the server has and extracts information, for this it makes use of the methods `__get_list`, to extract the items, and `get_info`, to complete the information, later it compares that it is not in the database and adds them, if necessary.

        Arguments:
        ---------
            server_id: `int`
                Server ID in the database

            force: `bool`
                If true, it will add the record regardless of the fact that no information could be obtained from it.

            db: `Session`
                Instance of the database to be able to execute queries
        """

    @staticmethod
    @abstractmethod
    async def update(server_id: int, force: bool, elements: List[Manga], db: Session):
        """
        Updates the information of the given elements, this by using the `get_info` method.

        Arguments:
        ---------
            server_id: `int`
                Server ID in the database

            force: `bool`
                If true, it will add the record regardless of the fact that no information could be obtained from it.

            elements: `List[Manga]`
                List of the elements to update

            db: `Session`
                Instance of the database to be able to execute queries
        """
    
    @staticmethod
    @abstractmethod
    def in_working() -> bool:
        """Return current status of scraper"""


from .nartag import Nartag
from .ikigai import Ikigai
from .leercapitulo import LeerCapitulo

SCRAPERS: Dict[str, Scraper] = {
    "Nartag": Nartag,
    "Ikigai": Ikigai,
    "LeerCapitulo": LeerCapitulo
}
