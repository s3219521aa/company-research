import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from backend.scrapers.business import BusinessScraper

MOCK_HTML = """
<div class="search-result">
  <a class="company-link" href="/detail/91110108551385082J">字节跳动科技有限公司</a>
</div>
"""

MOCK_DETAIL_HTML = """
<html><body>
  <span>法定代表人</span><span>张一鸣</span>
  <span>注册资本</span><span>50000万元</span>
  <span>成立日期</span><span>2012-03-09</span>
  <span>登记状态</span><span>存续</span>
  <span>登记机关</span><span>北京市</span>
  <span>住所</span><span>北京市海淀区</span>
  <span>经营范围</span><span>互联网信息服务</span>
</body></html>
"""


@pytest.mark.asyncio
async def test_search_returns_results():
    scraper = BusinessScraper()
    with patch.object(scraper, "_sync_search_html", return_value=MOCK_HTML):
        results = await scraper.search("字节跳动")
    assert len(results) == 1
    assert results[0]["credit_code"] == "91110108551385082J"
    assert results[0]["name"] == "字节跳动科技有限公司"


@pytest.mark.asyncio
async def test_scrape_returns_business_data():
    scraper = BusinessScraper()
    with patch.object(scraper, "_sync_detail_html", return_value=MOCK_DETAIL_HTML):
        result = await scraper.scrape("91110108551385082J", "字节跳动科技有限公司")
    assert result["name"] == "字节跳动科技有限公司"
    assert result["credit_code"] == "91110108551385082J"


@pytest.mark.asyncio
async def test_scrape_raises_on_fetch_failure():
    scraper = BusinessScraper()
    with patch.object(scraper, "_sync_detail_html", side_effect=Exception("超时")):
        with pytest.raises(Exception, match="超时"):
            await scraper.scrape("CODE", "Company")


@pytest.mark.asyncio
async def test_search_returns_empty_on_playwright_error():
    scraper = BusinessScraper()
    with patch.object(scraper, "_sync_search_html", side_effect=NotImplementedError()):
        results = await scraper.search("字节跳动")
    assert results == []
