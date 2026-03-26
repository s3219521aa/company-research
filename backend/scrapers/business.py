import asyncio
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from backend.scrapers.base import BaseScraper

SEARCH_URL = "https://www.gsxt.gov.cn/corp-query-homepage-search-1.html"
DETAIL_BASE = "https://www.gsxt.gov.cn"


class BusinessScraper(BaseScraper):
    """Scrapes 国家企业信用信息公示系统 for company registration info."""

    async def search(self, company_name: str) -> list[dict]:
        html = await self._fetch_search_page(company_name)
        return self._parse_search_results(html)

    async def scrape(self, credit_code: str, company_name: str) -> dict:
        return await self._fetch_detail(credit_code, company_name)

    async def _fetch_search_page(self, company_name: str) -> str:
        headers = {"User-Agent": self.random_ua()}
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.get(
                SEARCH_URL,
                params={"searchword": company_name},
                headers=headers,
                timeout=15,
            )
        )
        resp.raise_for_status()
        return resp.text

    def _parse_search_results(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for item in soup.select(".search-result .company-link")[:10]:
            href = item.get("href", "")
            credit_code = href.split("/")[-1] if "/" in href else ""
            results.append({
                "credit_code": credit_code,
                "name": item.get_text(strip=True),
                "legal_person": "",
                "registered_capital": "",
                "province": "",
                "status": "",
            })
        return results

    async def _fetch_detail(self, credit_code: str, company_name: str) -> dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=self.random_ua())
            await page.goto(f"{DETAIL_BASE}/detail/{credit_code}", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)
            content = await page.content()
            await browser.close()
        return self._parse_detail(content, credit_code, company_name)

    def _parse_detail(self, html: str, credit_code: str, company_name: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")

        def get_field(label: str) -> str:
            tag = soup.find(string=lambda t: t and label in t)
            if tag and tag.parent and tag.parent.next_sibling:
                return tag.parent.next_sibling.get_text(strip=True)
            return ""

        return {
            "credit_code": credit_code,
            "name": company_name,
            "legal_person": get_field("法定代表人") or get_field("负责人"),
            "registered_capital": get_field("注册资本"),
            "established_date": get_field("成立日期") or get_field("注册日期"),
            "status": get_field("登记状态") or get_field("经营状态"),
            "province": get_field("登记机关"),
            "address": get_field("住所") or get_field("注册地址"),
            "business_scope": get_field("经营范围"),
        }
