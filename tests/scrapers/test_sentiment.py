import pytest
from unittest.mock import patch, AsyncMock
from backend.scrapers.sentiment import SentimentScraper

MOCK_ITEMS = [
    {"source": "知乎", "title": "字节跳动工作体验如何？", "url": "https://zhihu.com/q/1",
     "date": "2024-01", "snippet": "整体不错，但是压力大"},
]


@pytest.mark.asyncio
async def test_scrape_returns_sentiment_data():
    scraper = SentimentScraper()
    with patch.object(scraper, "_fetch_zhihu", AsyncMock(return_value=MOCK_ITEMS)):
        result = await scraper.scrape("CODE123", "字节跳动")
    assert result["item_count"] == 1
    assert result["items"][0]["source"] == "知乎"


@pytest.mark.asyncio
async def test_scrape_returns_empty_on_failure():
    scraper = SentimentScraper()
    with patch.object(scraper, "_fetch_zhihu", AsyncMock(side_effect=Exception("反爬"))):
        result = await scraper.scrape("CODE123", "字节跳动")
    assert result["item_count"] == 0
