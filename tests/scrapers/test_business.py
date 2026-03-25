import pytest
from unittest.mock import patch, AsyncMock
from backend.scrapers.business import BusinessScraper

MOCK_HTML = """
<div class="search-result">
  <a class="company-link" href="/detail/91110108551385082J">字节跳动科技有限公司</a>
</div>
"""

MOCK_DETAIL = {
    "credit_code": "91110108551385082J",
    "name": "字节跳动科技有限公司",
    "legal_person": "张一鸣",
    "registered_capital": "50000万元",
    "established_date": "2012-03-09",
    "status": "存续",
    "province": "北京市",
    "address": "北京市海淀区",
    "business_scope": "互联网信息服务",
}


@pytest.mark.asyncio
async def test_search_returns_results():
    scraper = BusinessScraper()
    with patch.object(scraper, "_fetch_search_page", AsyncMock(return_value=MOCK_HTML)):
        with patch.object(scraper, "_parse_search_results", return_value=[
            {"credit_code": "91110108551385082J", "name": "字节跳动科技有限公司",
             "legal_person": "", "registered_capital": "", "province": "", "status": ""}
        ]):
            results = await scraper.search("字节跳动")
    assert len(results) == 1
    assert results[0]["credit_code"] == "91110108551385082J"


@pytest.mark.asyncio
async def test_scrape_returns_business_data():
    scraper = BusinessScraper()
    with patch.object(scraper, "_fetch_detail", AsyncMock(return_value=MOCK_DETAIL)):
        result = await scraper.scrape("91110108551385082J", "字节跳动科技有限公司")
    assert result["name"] == "字节跳动科技有限公司"
    assert result["legal_person"] == "张一鸣"


@pytest.mark.asyncio
async def test_scrape_raises_on_fetch_failure():
    scraper = BusinessScraper()
    with patch.object(scraper, "_fetch_detail", AsyncMock(side_effect=Exception("超时"))):
        with pytest.raises(Exception, match="超时"):
            await scraper.scrape("CODE", "Company")
