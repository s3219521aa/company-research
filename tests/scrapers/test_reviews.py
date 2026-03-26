import pytest
from unittest.mock import patch, AsyncMock
from backend.scrapers.reviews import ReviewsScraper

MOCK_ITEMS = [
    {"source": "牛客网", "content": "氛围不错，加班较多", "date": "2024-01", "rating": 4},
    {"source": "牛客网", "content": "技术氛围好", "date": "2024-02", "rating": 5},
]


@pytest.mark.asyncio
async def test_scrape_returns_reviews_data():
    scraper = ReviewsScraper()
    with patch.object(scraper, "_fetch_niuke_reviews", AsyncMock(return_value=MOCK_ITEMS)):
        result = await scraper.scrape("CODE123", "字节跳动")
    assert result["source_count"] == 2
    assert result["items"][0]["source"] == "牛客网"


@pytest.mark.asyncio
async def test_scrape_returns_empty_on_failure():
    scraper = ReviewsScraper()
    with patch.object(scraper, "_fetch_niuke_reviews", AsyncMock(side_effect=Exception("403"))):
        result = await scraper.scrape("CODE123", "字节跳动")
    assert result["source_count"] == 0
    assert result["items"] == []
