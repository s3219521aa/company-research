from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    credit_code: str
    name: str
    legal_person: str = ""
    registered_capital: str = ""
    province: str = ""
    status: str = ""


class SearchResponse(BaseModel):
    results: list[SearchResult]


class ResearchRequest(BaseModel):
    credit_code: str
    company_name: str


class ResearchResponse(BaseModel):
    task_id: str
    cached: bool


class ModuleStatus(BaseModel):
    status: Literal["pending", "scraping", "done", "error"]
    data: Optional[Any] = None
    error: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    overall_status: str
    modules: dict[str, ModuleStatus]


class BusinessData(BaseModel):
    credit_code: str
    name: str
    legal_person: str = ""
    registered_capital: str = ""
    established_date: str = ""
    status: str = ""
    province: str = ""
    address: str = ""
    business_scope: str = ""


class LegalItem(BaseModel):
    type: Literal["lawsuit", "enforcement", "dishonest"]
    title: str
    date: str = ""
    court: str = ""
    result: str = ""


class LegalData(BaseModel):
    lawsuit_count: int = 0
    enforcement_count: int = 0
    dishonest_count: int = 0
    items: list[LegalItem] = Field(default_factory=list)


class ReviewItem(BaseModel):
    source: str
    content: str
    date: str = ""
    rating: Optional[int] = None


class ReviewsData(BaseModel):
    source_count: int = 0
    items: list[ReviewItem] = Field(default_factory=list)


class SentimentItem(BaseModel):
    source: str
    title: str
    url: str = ""
    date: str = ""
    snippet: str = ""


class SentimentData(BaseModel):
    item_count: int = 0
    items: list[SentimentItem] = Field(default_factory=list)
