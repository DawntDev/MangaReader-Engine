from ..schemas.responses import MangaDetail
import json

class MangaDetails:
    def __init__(self, query) -> None:
        keys = MangaDetail.__annotations__.keys()
        self.__response: MangaDetail = dict(zip(keys, query))
        self.__response["genre"] = json.loads(self.__response["genre"])
        
    @property
    def response(self) -> MangaDetail:
        return self.__response