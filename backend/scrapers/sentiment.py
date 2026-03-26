import asyncio
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper


class SentimentScraper(BaseScraper):
    """Scrapes 知乎 search results for company sentiment."""

    async def scrape(self, credit_code: str, company_name: str) -> dict:
        try:
            items = await self._fetch_zhihu(company_name)
        except Exception:
            items = []
        return {
            "item_count": len(items),
            "items": items,
        }

    async def _fetch_zhihu(self, company_name: str) -> list[dict]:
        query = f"{company_name} 工作 评价"
        content = await asyncio.get_running_loop().run_in_executor(
            None, self._sync_zhihu_html, query
        )
        return self._parse_zhihu(content)

    def _sync_zhihu_html(self, query: str) -> str:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=self.random_ua())
                page.goto(
                    f"https://www.zhihu.com/search?type=content&q={query}",
                    timeout=30000,
                )
                page.wait_for_load_state("networkidle", timeout=15000)
                return page.content()
            finally:
                browser.close()

    def _parse_zhihu(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        items = []
        for item in soup.select(".SearchResult-Card")[:10]:
            title_tag = item.select_one("h2, .ContentItem-title")
            snippet_tag = item.select_one(".RichText, .ContentItem-summary")
            link_tag = item.select_one("a[href]")
            if not title_tag:
                continue
            items.append({
                "source": "知乎",
                "title": title_tag.get_text(strip=True),
                "url": link_tag["href"] if link_tag else "",
                "date": "",
                "snippet": snippet_tag.get_text(strip=True)[:200] if snippet_tag else "",
            })
        return items
