import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client(tmp_path):
    import os
    os.environ["DATABASE_PATH"] = str(tmp_path / "test.db")
    from backend.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_search_returns_results(client):
    mock_results = [
        {"credit_code": "CODE123", "name": "字节跳动", "legal_person": "",
         "registered_capital": "", "province": "", "status": ""}
    ]
    with patch("backend.main.BusinessScraper") as MockScraper:
        instance = MockScraper.return_value
        instance.search = AsyncMock(return_value=mock_results)
        resp = await client.get("/api/search?name=字节跳动")
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1


@pytest.mark.asyncio
async def test_research_creates_task(client):
    with patch("backend.main.task_manager") as mock_tm:
        mock_tm.create_task = AsyncMock(return_value="task-abc")
        resp = await client.post("/api/company/research", json={
            "credit_code": "CODE123",
            "company_name": "字节跳动"
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data


@pytest.mark.asyncio
async def test_task_status_not_found(client):
    with patch("backend.main.task_manager") as mock_tm:
        mock_tm.get_task_status = AsyncMock(return_value=None)
        resp = await client.get("/api/task/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_company_not_cached_returns_404(client):
    with patch("backend.main.db") as mock_db:
        mock_db.is_company_cached = AsyncMock(return_value=False)
        resp = await client.get("/api/company/CODE123")
    assert resp.status_code == 404
