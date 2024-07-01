from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    WebSocket,
    status,
    BackgroundTasks
)
from sqlalchemy.orm import Session
from typing import List, Optional, Union

from src.database import get_db
from src.database.models import Server, Manga
from src.database.schemas import (
    ServerFetchSchema,
    ServerGetSchema,
    ServerAddSchema,
    FetchLevel
)
from src.scrapers import SCRAPERS

servers_router = APIRouter(prefix="/servers")


@servers_router.get("/")
def get_servers(
    id: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Union[List[ServerGetSchema], ServerGetSchema]:
    if not (id or name):
        query = db.query(Server).all()
        servers = []
        for element in query:
            scraper = SCRAPERS.get(element.name)
            if scraper:
                elements = len(db.query(Manga).filter_by(server=element.id).all())
                servers.append(
                    ServerGetSchema(
                        id=element.id,
                        name=element.name,
                        nsfw=element.nsfw, 
                        in_working=scraper.in_working(),
                        elements = elements
                    )
                )
        return servers

    query = db.query(Server)
    query = (
        query.filter_by(name=name).all()
        if name
        else query.filter_by(id=id).first()
    )

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The server not found"
        )
    
    scraper = SCRAPERS.get(query.name)
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper not found"
        )
        
    elements = len(db.query(Manga).filter_by(server=query.id))
    return ServerGetSchema(
        id=query.id,
        name=query.name,
        elements=elements,
        nsfw=query.nsfw, 
        in_working=scraper.in_working()
    )


@servers_router.post("/")
def add_server(request: ServerAddSchema, db: Session = Depends(get_db)):
    data = request.model_dump()
    exist = db.query(Server).filter_by(name=data["name"]).first()

    if exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The server already exists"
        )

    server = Server(**data)

    db.add(server)
    db.commit()
    db.refresh(server)

    return Response(
        content="Server Added", 
        status_code=status.HTTP_201_CREATED
    )


@servers_router.delete("/")
def del_server(
    id: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if not (id or name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No information has been provided to identify the server."
        )

    query = db.query(Server)
    query = (
        query.filter_by(name=name) 
        if name 
        else query.filter_by(id=id)
    )
    
    if not query.count():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found."
        )
    
    mangas = db.query(Manga).filter_by(server=query.first().id).delete()
    query.delete()
    
    db.commit()
    remaining_data = db.query(Server).all()

    return {
        "remaining_servers": remaining_data, 
        "rows_affected": mangas
    }


@servers_router.post("/fetch", status_code=status.HTTP_201_CREATED)
def fetch_server(
    request: ServerFetchSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    server = db.query(Server).filter_by(id=request.id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found."
        )

    scraper = SCRAPERS.get(server.name)
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper not found."
        )

    elif scraper.in_working():
        raise HTTPException(
            status_code=status.HTTP_102_PROCESSING,
            detail="The process is in progress"
        )

    if request.level >= FetchLevel.SCAN:
        if request.level == FetchLevel.HARD:
            db.query(Manga).filter_by(server=server.id).delete()
            db.commit()

        background_tasks.add_task(
            scraper.scan,
            request.id, 
            request.force,
            db
        )

    elif request.level == FetchLevel.UPDATE:
        elements = (
            db.query(Manga)
            .filter_by(server=request.id)
            .where(
                (Manga.type_of == None)
                | (Manga.rating == None)
                | (Manga.genres == None)
                | (Manga.overview == None)
                | (Manga.cover_url == None)
            ).all()
        )

        background_tasks.add_task(
            scraper.update, 
            request.id, 
            request.force, 
            elements, 
            db
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The fetch level is no valid"
        )

    return {
        "status": "IN PROGRESS",
        "websocket": servers_router.url_path_for(
            "fetch_status", name=server.name
        ),
    }


@servers_router.websocket("/status/{name}/ws")
async def fetch_status(websocket: WebSocket, name: str):
    await websocket.accept()
    scraper = SCRAPERS.get(name)

    if not scraper:
        await websocket.close(
            code=status.WS_1002_PROTOCOL_ERROR,
            reason=f"Scrapper {name} not found. Closing connection",
        )

    while scraper.in_working():
        with open(f"./logs/{name}.log", "r") as log:
            await websocket.send_text(log.read())
