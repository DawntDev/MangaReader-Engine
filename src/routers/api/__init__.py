import random
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from typing import Dict, List, Set

from .manga import manga_router
from src.database import get_db
from src.database.models import Manga
from src.database.schemas import MangaPreviewScheme

api_router = APIRouter(prefix="/api")
api_router.include_router(manga_router)


@api_router.get("/main-screen")
def main_screen(
    db: Session = Depends(get_db),
) -> Dict[str, List[MangaPreviewScheme]]:

    mangas = db.query(Manga).order_by(func.random()).limit(15).all()
    carousel = [
        MangaPreviewScheme(
            title=manga.title,
            name_url=manga.title,
            server=manga.server,
            cover_url=manga.cover_url,
        )
        for manga in mangas
    ]

    genres: Set[str] = set()
    for genres_pack in db.query(Manga.genres).all():
        genres.update(genres_pack[-1])

    genres: List[str] = random.choices([*genres], k=5)
    order_by_genres = {}

    for genre in genres:
        order_by_genres[genre] = [
            MangaPreviewScheme(
                title=manga.title,
                name_url=manga.name_url,
                server=manga.server,
                cover_url=manga.cover_url,
            )
            for manga in db.query(Manga)
                .filter(Manga.genres.any(genre))
                .order_by(func.random())
                .limit(12)
                .all()
        ]

    return {"carousel": carousel, **order_by_genres}
