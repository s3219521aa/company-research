import asyncio
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper

SEARCH_URL = "https://www.gsxt.gov.cn/corp-query-homepage-search-1.html"
DETAIL_BASE = "https://www.gsxt.gov.cn"


class BusinessScraper(BaseScraper):
    """Scrapes 国家企业信用信息公示系统 for company registration info."""

    async def search(self, company_name: str) -> list[dict]:
        try:
            html = await asyncio.get_running_loop().run_in_executor(
                None, self._sync_search_html, company_name
            )
            results = self._parse_search_results(html)
            if not results:
                import logging
                logging.getLogger(__name__).warning(
                    "Search returned 0 results. Page snippet: %s", html[:500]
                )
            return results
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Search failed: %s", e)
            return []

    async def scrape(self, credit_code: str, company_name: str) -> dict:
        content = await asyncio.get_running_loop().run_in_executor(
            None, self._sync_detail_html, credit_code
        )
        return self._parse_detail(content, credit_code, company_name)

    # --- sync helpers (run in thread pool) ---

    def _sync_search_html(self, company_name: str) -> str:
        from playwright.sync_api import sync_playwright
        import time
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=self.random_ua())
                page.goto(
                    f"{SEARCH_URL}?searchword={company_name}",
                    timeout=30000,
                    wait_until="domcontentloaded",
                )
                try:
                    page.wait_for_selector(
                        ".search-result, .company-list, .result-list, li.company-item",
                        timeout=8000,
                    )
                except Exception:
                    pass
                time.sleep(1)
                return page.content()
            finally:
                browser.close()

    def _sync_detail_html(self, credit_code: str) -> str:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=self.random_ua())
                page.goto(f"{DETAIL_BASE}/detail/{credit_code}", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=20000)
                return page.content()
            finally:
                browser.close()

    # --- parsers ---

    def _parse_search_results(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        candidates = (
            soup.select(".search-result .company-link")
            or soup.select(".company-list a")
            or soup.select("a[href*='/corp-query-search-info-']")
            or soup.select("ul.result-list li a")
        )
        for item in candidates[:10]:
            href = item.get("href", "")
            credit_code = ""
            if "unifySc=" in href:
                credit_code = href.split("unifySc=")[-1].split("&")[0]
            elif "/" in href:
                credit_code = href.rstrip("/").split("/")[-1]
            results.append({
                "credit_code": credit_code,
                "name": item.get_text(strip=True),
                "legal_person": "",
                "registered_capital": "",
                "province": "",
                "status": "",
            })
        return results

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
