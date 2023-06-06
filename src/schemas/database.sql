--CREATE DATABASE "MangaReader";
--USE "MangaReader";

DROP TABLE IF EXISTS "WebComics";
CREATE TABLE "WebComics" (
    "Title"     TEXT                                               NOT NULL PRIMARY KEY,
    "TypeOf"    TEXT CHECK("TypeOf" IN ("Manga", "Manhwa", "Manhua", "Novel")) NOT NULL,
    "Rating"    NUMERIC CHECK("Rating" BETWEEN 0.0 AND 5.0)                  DEFAULT 0.0,
    "Genre"     TEXT[]                                                       NOT NULL,
    "Overview"  TEXT,
    "Server"    TEXT CHECK("Server" IN ("Nartag", "LeerCapitulo"))           NOT NULL,
    "NameURL"   TEXT                                                         NOT NULL,
    "CoverURL"	TEXT DEFAULT NULL CHECK("CoverURL" REGEXP "(http(s?):)([/|.|\w|\s|-])*\.(?:jpg|gif|png)" OR "CoverURL" IS NULL)
);