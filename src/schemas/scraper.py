from abc import ABC, abstractclassmethod
from typing import TypedDict, Literal, List

class Manga(TypedDict):
    title: str
    typeOf: str
    rating: float
    genre: List[str]
    chapterList: List[str]
    overview: str
    server: str
    nameURL: str
    coverURL: str

class IncompleteManga(TypedDict):
    title: str | None
    typeOf: str | None
    rating: float | None
    genre: List[str] | None
    chapterList: List[str] | None
    overview: str | None
    server: str | None
    nameURL: str
    coverURL: str | None

class MangaView(TypedDict):
    title: str
    nameURL: str
    coverURL: str
    server: str

class Scraper(ABC):
    @property
    @abstractclassmethod
    def __URL(self) -> str:
        ...
    
    @staticmethod
    @abstractclassmethod
    async def get_manga_list(page: int) -> List[MangaView]:
        ...
    
    @staticmethod
    @abstractclassmethod
    async def get_manga_info(manga: IncompleteManga) -> Manga | Literal[False]:
        ...
        
    @staticmethod
    @abstractclassmethod
    async def get_manga_chapter(name_url:str, chapter: str) -> List[str] | Literal[False]:
        ...
