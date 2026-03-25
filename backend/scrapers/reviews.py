import asyncio
import requests
from backend.scrapers.base import BaseScraper


class ReviewsScraper(BaseScraper):
    """Scrapes employee reviews from 牛客网 (public content, no login required)."""

    async def scrape(self, credit_code: str, company_name: str) -> dict:
        try:
            items = await self._fetch_niuke_reviews(company_name)
        except Exception:
            items = []
        return {
            "source_count": len(items),
            "items": items,
        }

    async def _fetch_niuke_reviews(self, company_name: str) -> list[dict]:
        headers = {"User-Agent": self.random_ua()}
        loop = asyncio.get_event_loop()

        # Step 1: search for company page
        search_resp = await loop.run_in_executor(
            None,
            lambda: requests.get(
                "https://www.nowcoder.com/api/companies/search",
                params={"keyword": company_name, "limit": 5},
                headers=headers,
                timeout=15,
            )
        )
        if search_resp.status_code != 200:
            return []

        data = search_resp.json()
        companies = data.get("data", {}).get("companies", [])
        if not companies:
            return []

        company_id = companies[0].get("companyId")
        if not company_id:
            return []

        # Step 2: fetch reviews for company
        reviews_resp = await loop.run_in_executor(
            None,
            lambda: requests.get(
                f"https://www.nowcoder.com/api/review/companies/{company_id}/reviews",
                params={"pageSize": 20, "page": 1},
                headers=headers,
                timeout=15,
            )
        )
        if reviews_resp.status_code != 200:
            return []

        review_data = reviews_resp.json()
        items = []
        for review in review_data.get("data", {}).get("reviews", []):
            items.append({
                "source": "牛客网",
                "content": review.get("content", ""),
                "date": review.get("createTime", "")[:7] if review.get("createTime") else "",
                "rating": review.get("score"),
            })
        return items
