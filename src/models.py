from dataclasses import dataclass
from typing import Optional


@dataclass
class BarboraWine:
    id: str
    title: str
    brand_name: str
    price: float
    url: str
    category_path_url: str
    image: str
    status: str


@dataclass
class VivinoWine:
    id: str
    name: str
    rate: str
    grapes: Optional[list[str]]
    alcohol: str
    image: str


@dataclass
class BarboraVivinoWine:
    barbora_wine: BarboraWine
    vivino_wines: Optional[list[VivinoWine]]
    verified: bool = False
