from . import Base
from sqlalchemy import (
    Column,
    Integer,
    PrimaryKeyConstraint,
    String,
    Boolean,
    CheckConstraint,
    Numeric,
    ARRAY,
    ForeignKey
)


class Server(Base):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True, autoincrement="auto")
    name = Column(String, nullable=False)
    nsfw = Column(Boolean, nullable=False)


class Manga(Base):
    __tablename__ = "mangas"
    __table_args__ = (PrimaryKeyConstraint("name_url", "server"),)
    
    title = Column(String, nullable=False)
    type_of = Column(
        String,
        CheckConstraint(
            "type_of IN ('manga', 'manhwa', 'manhua', 'novel', 'one shot', 'doujinshi', 'oel')"
        ),
        nullable=False
    )
    rating = Column(
        Numeric,
        CheckConstraint("rating BETWEEN 0.0 AND 5.0"),
        nullable=True
    )
    genres = Column(ARRAY(String), nullable=True)
    overview = Column(String, nullable=True)
    server = Column(
        Integer,
        ForeignKey(Server.id),
        nullable=False
    )
    name_url = Column(String, nullable=False)
    cover_url = Column(String, nullable=True)
    nsfw = Column(Boolean, nullable=False)
