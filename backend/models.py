from typing import Any, Optional
from pydantic import BaseModel


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
    status: str  # pending | scraping | done | error
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
    type: str  # lawsuit | enforcement | dishonest
    title: str
    date: str = ""
    court: str = ""
    result: str = ""


class LegalData(BaseModel):
    lawsuit_count: int = 0
    enforcement_count: int = 0
    dishonest_count: int = 0
    items: list[LegalItem] = []


class ReviewItem(BaseModel):
    source: str
    content: str
    date: str = ""
    rating: Optional[int] = None


class ReviewsData(BaseModel):
    source_count: int = 0
    items: list[ReviewItem] = []


class SentimentItem(BaseModel):
    source: str
    title: str
    url: str = ""
    date: str = ""
    snippet: str = ""


class SentimentData(BaseModel):
    item_count: int = 0
    items: list[SentimentItem] = []
