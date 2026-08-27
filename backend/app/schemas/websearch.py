from pydantic import BaseModel


class WebSearchResult(BaseModel):
    title: str
    link: str
    snippet: str
    source: str
    queried_source: str
