from ..schemas.responses import MangaPreview
from typing import List

class MainScreen:
    def __init__(self, query_carousel, query_by_genre) -> None:
        self.__response = {
            "carousel": [
                {
                    "title": title, 
                    "nameURL": name_url, 
                    "coverURL": cover_url
                }
            for (title, name_url, cover_url) in query_carousel]
        }
        
        for genre, value in query_by_genre.items():
            self.__response[genre] = [
                {
                    "title": title,
                    "nameURL": name_url,
                    "coverURL": cover_url
                }
            for (title, name_url, cover_url) in value]

    @property
    def response(self) -> dict[str, List[MangaPreview]]:
        return self.__response
    
