import pytest
from unittest.mock import patch, AsyncMock
from backend.scrapers.legal import LegalScraper


@pytest.mark.asyncio
async def test_scrape_returns_legal_data():
    scraper = LegalScraper()
    lawsuit_items = [{"type": "lawsuit", "title": "劳动合同纠纷", "date": "2023-05-12", "court": "海淀区法院", "result": "调解"}]
    with patch.object(scraper, "_fetch_lawsuits", AsyncMock(return_value=lawsuit_items)):
        with patch.object(scraper, "_fetch_enforcement", AsyncMock(return_value=[])):
            with patch.object(scraper, "_fetch_dishonest", AsyncMock(return_value=[])):
                result = await scraper.scrape("CODE123", "字节跳动")
    assert result["lawsuit_count"] == 1
    assert result["items"][0]["type"] == "lawsuit"


@pytest.mark.asyncio
async def test_scrape_aggregates_all_sources():
    scraper = LegalScraper()
    lawsuit_items = [{"type": "lawsuit", "title": "A", "date": "", "court": "", "result": ""}]
    enforcement_items = [{"type": "enforcement", "title": "B", "date": "", "court": "", "result": ""}]
    with patch.object(scraper, "_fetch_lawsuits", AsyncMock(return_value=lawsuit_items)):
        with patch.object(scraper, "_fetch_enforcement", AsyncMock(return_value=enforcement_items)):
            with patch.object(scraper, "_fetch_dishonest", AsyncMock(return_value=[])):
                result = await scraper.scrape("CODE123", "Test")
    assert result["lawsuit_count"] == 1
    assert result["enforcement_count"] == 1
    assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_partial_failure_returns_available_data():
    scraper = LegalScraper()
    with patch.object(scraper, "_fetch_lawsuits", AsyncMock(side_effect=Exception("超时"))):
        with patch.object(scraper, "_fetch_enforcement", AsyncMock(return_value=[])):
            with patch.object(scraper, "_fetch_dishonest", AsyncMock(return_value=[])):
                result = await scraper.scrape("CODE123", "Test")
    assert result["lawsuit_count"] == 0
