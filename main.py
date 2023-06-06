from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from src.responses import MainScreen, MangaDetails, MangaSearch
from src.scrapers import LeerCapitulo, Nartag
from src.webdriver import WebDriver
from typing import List
import random
import aiohttp
import base64
import sqlite3
import re
import time

app = FastAPI()
WebDriver()
servers = {
    "LeerCapitulo": LeerCapitulo,
    "Nartag": Nartag
}
genres = ["Guerra", "Cyberpunk", "Girls love", "Demonios", "Aventura", "Romance", "Sobrenatural", "Telenovela", "Ciencia ficción", "Oeste", "Venganza", "Realidad virtual", "Escolar", "Supervivencia", "Murim", "Mecha", "Shounen", "Policíaco", "Música", "Misterio", "Historia", "Militar", "Magia", "Samurái", "Mazmorras", "Apocalíptico", "Tragedia", "Superpoderes", "Ecchi", "Vampiros", "Artes marciales", "Horror", "Drama", "Deporte", "Thriller", "Extranjero", "Género bender", "Harem", "Fantasia", "Boys love", "Realidad", "Parodia", "Niños", "Regresión", "Recuentos de la vida", "Acción", "Psicológico", "Gore", "Animación", "Familia", "Reencarnación", "Comedia", "Crimen"]

regexp = lambda expr, item: re.compile(expr).search(item) is not None
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/main-screen")
def get_main_screen():
    conn = sqlite3.connect("MangaReader.db")
    conn.create_function("REGEXP", 2, regexp)
    cursor = conn.cursor()
    
    cursor.execute(
    """SELECT "Title", "NameURL", "CoverURL" FROM WebComics
    ORDER BY RANDOM()
    LIMIT 15;
    """
    )
    query_carousel = cursor.fetchall()
    
    query_by_genre = {}
    
    
    for genre in random.sample(genres, 5):
        cursor.execute("""SELECT * FROM (
        SELECT "Title", "NameURL", "CoverURL" FROM WebComics 
        WHERE "Genre" REGEXP "{genre}" AND Server = "Nartag"
        ORDER BY RANDOM()
        LIMIT 6
        ) 
        UNION
        SELECT * FROM (
        SELECT "Title", "NameURL", "CoverURL" FROM WebComics 
        WHERE "Genre" REGEXP "{genre}" AND Server = "LeerCapitulo"
        ORDER BY RANDOM()
        LIMIT 6
        );""".format(genre=genre))
        query_by_genre[genre] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return MainScreen(query_carousel, query_by_genre).response


@app.get("/api/manga/details")
async def get_manga_details(nameURL: str):
    conn = sqlite3.connect("MangaReader.db")
    cursor =  conn.cursor()
    
    cursor.execute(f"""SELECT * FROM WebComics WHERE NameURL = "{nameURL}\"""")
    query = [*cursor.fetchone()]
    
    cursor.close()
    conn.close()
    
    scraper = servers[query.pop(5)]
    data = MangaDetails(query).response
    return await scraper.get_manga_info(data)

@app.get("/api/manga/chapter")
async def get_manga_chapter(nameURL, chapter, inBytes: bool = False):
    conn = sqlite3.connect("MangaReader.db")
    cursor = conn.cursor()
    
    cursor.execute(f"""SELECT Server FROM WebComics WHERE NameURL="{nameURL}\"""")
    query = cursor.fetchone()[0]
    scraper = servers[query]
    
    content = await scraper.get_manga_chapter(nameURL, chapter)
    
    if isinstance(content, str):
        return [content]
    
    elif inBytes:
        images = []
        async with aiohttp.ClientSession() as session:
            for img in content:
                async with session.get(img) as file:
                    images.append(
                        base64.b64encode(
                            await file.read()
                        ).decode("utf-8")
                    )
        return images
    else: return content

@app.get("/api/manga/search")
def search(text: str = Query(""), genres: List[str] = Query([])):
    conn = sqlite3.connect("MangaReader.db")
    conn.create_function("REGEXP", 2, regexp)
    cursor = conn.cursor()
    
    cursor.execute(
    "SELECT * FROM WebComics "
    + ("", "WHERE ")[bool(text) or bool(genres)]
    + ("", f"Title LIKE '{text}%'")[bool(text)]
    + ("", " AND ")[bool(text) and bool(genres)]
    + ("", " AND ".join(map(lambda el: (f"Genre REGEXP '{el}'"), genres)))[bool(genres)]
    )
    
    query = cursor.fetchall()
    return MangaSearch(query).response