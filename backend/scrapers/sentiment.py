import asyncio
from playwright.async_api import async_playwright
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
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=self.random_ua())
            await page.goto(
                f"https://www.zhihu.com/search?type=content&q={query}",
                timeout=30000,
            )
            await page.wait_for_load_state("networkidle", timeout=15000)
            content = await page.content()
            await browser.close()
        return self._parse_zhihu(content)

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
