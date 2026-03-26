import asyncio
import random
from abc import ABC, abstractmethod
from typing import Any

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class BaseScraper(ABC):
    def __init__(
        self,
        max_retries: int = 2,
        retry_delay: float = 3.0,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.min_delay = min_delay
        self.max_delay = max_delay

    def random_ua(self) -> str:
        return random.choice(USER_AGENTS)

    async def random_delay(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    @abstractmethod
    async def scrape(self, credit_code: str, company_name: str) -> Any:
        """Return scraped data dict. Raise on failure."""
        ...

    async def run(self, credit_code: str, company_name: str) -> dict:
        last_error = ""
        for attempt in range(self.max_retries + 1):
            try:
                await self.random_delay()
                data = await self.scrape(credit_code, company_name)
                return {"status": "done", "data": data}
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
        return {"status": "error", "error": last_error, "data": None}
