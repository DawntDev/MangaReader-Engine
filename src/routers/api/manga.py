from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.database.models import Server, Manga
from src.database.schemas import MangaScheme
from src.scrapers import SCRAPERS

manga_router = APIRouter(prefix="/manga")


def validate_data(name_url: str, db: Session):
    manga = db.query(Manga).filter_by(name_url=name_url).first()
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    server = db.query(Server).filter_by(id=manga.server).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    scraper = SCRAPERS.get(server.name)
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper not found",
        )

    return manga, server, scraper


@manga_router.get("/details")
async def get_details(
    name_url: str, db: Session = Depends(get_db)
) -> MangaScheme:
    _, server, scraper = validate_data(name_url, db)
    response = await scraper.get_info(server.id, name_url)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server fetch failed",
        )

    return response


@manga_router.get("/chapter")
async def get_chapter(
    name_url: str, chapter_url: str, db: Session = Depends(get_db)
) -> List[str]:
    *_, scraper = validate_data(name_url, db)
    chapter = await scraper.get_chapter(name_url, chapter_url)

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server fetch failed",
        )

    return chapter


@manga_router.get("/search")
def get_search(
        title: str = Query(""), 
        genres: List[str] = Query([]),
        db: Session = Depends(get_db)
    ) -> List[MangaScheme]:
    query = db.query(Manga)
    
    if title:
        query = query.filter(Manga.title.like(f"{title}%"))
    
    if genres:
        for genre in genres:
            query = query.filter(Manga.genres.any(genre))
    
    return query.all()
