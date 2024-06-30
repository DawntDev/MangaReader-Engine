from pydantic import BaseModel, field_validator
from typing import Literal, Optional, List
from enum import Enum
import re


class ServerSchema(BaseModel):
    name: str
    nsfw: bool


class FetchLevel(int, Enum):
    UPDATE = 1
    SCAN = 2
    HARD = 3


class ServerFetchSchema(BaseModel):
    id: int
    level: FetchLevel = FetchLevel.UPDATE
    force: bool = False


class MangaPreviewScheme(BaseModel):
    title: str
    name_url: str
    server: int
    cover_url: Optional[str] = None


re_img = re.compile(
    r"(http(s?):)([/|.|\w|\s|-])*\.(?:jpg|gif|png)",
    flags=re.IGNORECASE,
)

class ChapterScheme(BaseModel):
    name: str
    url_name: str

class MangaScheme(BaseModel):
    title: str
    server: int
    name_url: str
    nsfw: Optional[bool] = None
    type_of: Optional[
        Literal[
            "manga",
            "manhwa",
            "manhua",
            "novel",
            "one shot",
            "doujinshi",
            "oel",
        ]
    ] = None
    cover_url: Optional[str] = None
    rating: Optional[float] = None
    genres: Optional[List[str]] = None
    overview: Optional[str] = None
    chapters_list: Optional[List[ChapterScheme]] = None

    @field_validator("cover_url")
    @classmethod
    def check_cover_url(cls, url: Optional[str]):
        if url:
            if not re_img.match(url):
                return None
        return url
