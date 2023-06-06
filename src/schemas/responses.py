from typing import TypedDict, List


class MangaPreview(TypedDict):
    title: str
    nameURL: str
    coverURL: str
    
class MangaDetail(TypedDict):
    title: str
    typeOf: str
    rating: float
    genre: List[str]
    overview: str
    nameURL: str
    coverURL: str