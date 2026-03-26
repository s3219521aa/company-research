import pytest
from unittest.mock import AsyncMock, patch
from backend.scrapers.base import BaseScraper


class ConcreteScraper(BaseScraper):
    async def scrape(self, credit_code: str, company_name: str):
        return {"ok": True}


@pytest.mark.asyncio
async def test_run_returns_done_on_success():
    s = ConcreteScraper()
    result = await s.run("CODE123", "Test Corp")
    assert result["status"] == "done"
    assert result["data"]["ok"] is True


@pytest.mark.asyncio
async def test_run_returns_error_after_retries():
    class FailingScraper(BaseScraper):
        async def scrape(self, credit_code, company_name):
            raise Exception("网络错误")

    s = FailingScraper(max_retries=2, retry_delay=0)
    result = await s.run("CODE123", "Test Corp")
    assert result["status"] == "error"
    assert "网络错误" in result["error"]


@pytest.mark.asyncio
async def test_random_ua_is_non_empty():
    s = ConcreteScraper()
    ua = s.random_ua()
    assert len(ua) > 10


@pytest.mark.asyncio
async def test_random_delay_range():
    s = ConcreteScraper(min_delay=0, max_delay=0)
    # Should not raise
    await s.random_delay()
