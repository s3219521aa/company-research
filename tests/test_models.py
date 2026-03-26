from backend.models import (
    SearchResult, SearchResponse,
    ResearchRequest, ResearchResponse,
    ModuleStatus, TaskResponse,
    BusinessData, LegalData, LegalItem,
    ReviewsData, ReviewItem,
    SentimentData, SentimentItem,
)

def test_search_result_fields():
    r = SearchResult(
        credit_code="91110108551385082J",
        name="字节跳动科技有限公司",
        legal_person="张一鸣",
        registered_capital="50000万元",
        province="北京市",
        status="存续",
    )
    assert r.credit_code == "91110108551385082J"

def test_module_status_done():
    m = ModuleStatus(status="done", data={"key": "val"})
    assert m.status == "done"
    assert m.data == {"key": "val"}

def test_module_status_error():
    m = ModuleStatus(status="error", error="403 Forbidden")
    assert m.error == "403 Forbidden"
    assert m.data is None

def test_task_response_overall_status():
    t = TaskResponse(
        task_id="abc",
        overall_status="scraping",
        modules={
            "business": ModuleStatus(status="done", data={}),
            "legal": ModuleStatus(status="scraping"),
        }
    )
    assert t.overall_status == "scraping"
