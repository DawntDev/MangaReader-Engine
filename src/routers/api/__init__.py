import random
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from typing import Dict, List
import os, json, time

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

    mangas = (
        db.query(Manga)
          .filter(Manga.cover_url != None)
          .order_by(func.random())
          .limit(15).all()
    )
    carousel = [
        MangaPreviewScheme(
            title=manga.title,
            name_url=manga.name_url,
            server=manga.server,
            cover_url=manga.cover_url,
        )
        for manga in mangas
    ]

    genres: List[str] = random.choices([*get_genres(db).keys()], k=5)
    order_by_genres = {}

    for genre in genres:
        elements = [
            MangaPreviewScheme(
                title=manga.title,
                name_url=manga.name_url,
                server=manga.server,
                cover_url=manga.cover_url,
            )
            for manga in db.query(Manga)
                .filter(Manga.genres.any(genre) & (Manga.cover_url != None))
                .order_by(func.random())
                .limit(12)
                .all()
        ]
        if len(elements): order_by_genres[genre] = elements

    return {"carousel": carousel, **order_by_genres}


@api_router.get("/genres")
def get_genres(db: Session = Depends(get_db)) -> Dict[str, str]:
    color = lambda:"#" + "".join([random.choice("0123456789ABCDEF") for _ in [0] * 6])
    def query_genres():
        genres = set()
        for genres_pack in db.query(Manga.genres).all():
            genres.update(map(str.lower, genres_pack[-1]))

        return genres

    genres_path = "./src/database/genres.json"
    if not os.path.exists(genres_path):
        genres = {genre:color() for genre in query_genres()}
        with open(genres_path, "w") as f:
            json.dump(
                genres, f, 
                indent=4, 
                ensure_ascii=True
            )

    else:
        life_time = time.time() - os.path.getmtime(genres_path)
        if life_time > 5 * 24 * 60 * 60:
            genres = {genre:color() for genre in query_genres()}
            with open(genres_path, "w") as f:
                json.dump(
                    genres, f, 
                    indent=4, 
                    ensure_ascii=True
                )
        else:
            with open(genres_path, "r") as f:
                genres = json.load(f)

    return genres