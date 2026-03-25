import asyncio
import requests
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper

ZXGK_SEARCH = "https://zxgk.court.gov.cn/zhixing/searchIndex.do"


class LegalScraper(BaseScraper):
    """Scrapes legal risk data from 裁判文书网 and 执行信息公开网."""

    async def scrape(self, credit_code: str, company_name: str) -> dict:
        results = await asyncio.gather(
            self._safe_fetch(self._fetch_lawsuits, company_name),
            self._safe_fetch(self._fetch_enforcement, company_name),
            self._safe_fetch(self._fetch_dishonest, company_name),
        )
        lawsuits, enforcements, dishonest = results
        all_items = lawsuits + enforcements + dishonest
        return {
            "lawsuit_count": len(lawsuits),
            "enforcement_count": len(enforcements),
            "dishonest_count": len(dishonest),
            "items": all_items,
        }

    async def _safe_fetch(self, func, *args) -> list:
        try:
            return await func(*args)
        except Exception:
            return []

    async def _fetch_lawsuits(self, company_name: str) -> list[dict]:
        headers = {"User-Agent": self.random_ua()}
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.post(
                "https://wenshu.court.gov.cn/website/parse/rest.q4w",
                json={"pageNum": 1, "pageSize": 10, "sortType": 1,
                      "conditions": {"searchWord": company_name, "vjkl5": ""}},
                headers={**headers, "Content-Type": "application/json"},
                timeout=15,
            )
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        items = []
        for record in data.get("queryResult", {}).get("resultList", []):
            items.append({
                "type": "lawsuit",
                "title": record.get("s2", ""),
                "date": record.get("s31", ""),
                "court": record.get("s8", ""),
                "result": record.get("s9", ""),
            })
        return items

    async def _fetch_enforcement(self, company_name: str) -> list[dict]:
        headers = {"User-Agent": self.random_ua()}
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.get(
                ZXGK_SEARCH,
                params={"pname": company_name, "pageNum": 0},
                headers=headers,
                timeout=15,
            )
        )
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        for row in soup.select("table tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                items.append({
                    "type": "enforcement",
                    "title": cols[0].get_text(strip=True),
                    "date": cols[2].get_text(strip=True) if len(cols) > 2 else "",
                    "court": cols[1].get_text(strip=True) if len(cols) > 1 else "",
                    "result": "",
                })
        return items

    async def _fetch_dishonest(self, company_name: str) -> list[dict]:
        headers = {"User-Agent": self.random_ua()}
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.get(
                "https://zxgk.court.gov.cn/shixin/searchIndex.do",
                params={"pname": company_name, "pageNum": 0},
                headers=headers,
                timeout=15,
            )
        )
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        for row in soup.select("table tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                items.append({
                    "type": "dishonest",
                    "title": cols[0].get_text(strip=True),
                    "date": cols[-1].get_text(strip=True) if cols else "",
                    "court": "",
                    "result": "",
                })
        return items
