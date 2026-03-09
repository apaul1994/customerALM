from pydantic import BaseModel
from typing import Optional

class AnalyzeEntityRequest(BaseModel):
    entity_name: str
    entity_description: str
    country: str
    url: Optional[str] = None

class GetUrlContentRequest(BaseModel):
    entity_name: str
    entity_description: str
    country: str

class GetUrlContentResponse(BaseModel):
    links: list[str]

class AnalyzeEntityResponse(BaseModel):
    matching_score: int  # Matching of the person with a reference content (0-100)
    involved_in_criminal_activity: bool
    involved_in_monetary_fraud: bool
    content: str = ""
    date: str = ""

class FetchArticleRequest(BaseModel):
    url: str

class FetchArticleResponse(BaseModel):
    content: str
    date: str