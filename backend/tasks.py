import asyncio
import uuid
from backend.cache import Database
from backend.scrapers.business import BusinessScraper
from backend.scrapers.legal import LegalScraper
from backend.scrapers.reviews import ReviewsScraper
from backend.scrapers.sentiment import SentimentScraper

MODULES = ["business", "legal", "reviews", "sentiment"]


class TaskManager:
    def __init__(self, db: Database):
        self.db = db
        # In-memory module status: {task_id: {module: {status, data, error}}}
        self._in_memory: dict[str, dict] = {}

    async def create_task(self, credit_code: str, company_name: str) -> str:
        task_id = str(uuid.uuid4())
        await self.db.create_task(task_id, credit_code)
        self._in_memory[task_id] = {
            m: {"status": "pending", "data": None, "error": None} for m in MODULES
        }
        return task_id

    async def get_task_status(self, task_id: str) -> dict | None:
        task = await self.db.get_task(task_id)
        if task is None:
            return None

        modules = self._in_memory.get(task_id, {})

        # If not in memory (process restart), read from DB
        if not modules:
            db_modules = await self.db.get_all_modules(task["credit_code"])
            modules = {
                m: db_modules.get(m, {"status": "pending", "data": None, "error": None})
                for m in MODULES
            }

        statuses = [m["status"] for m in modules.values()]
        if all(s in ("done", "error") for s in statuses):
            overall = "done"
        elif any(s == "scraping" for s in statuses):
            overall = "scraping"
        else:
            overall = task["status"]

        return {
            "task_id": task_id,
            "overall_status": overall,
            "modules": modules,
        }

    async def run_task(self, task_id: str, credit_code: str, company_name: str):
        await self.db.update_task_status(task_id, "scraping")

        scraper_map = {
            "business": BusinessScraper(),
            "legal": LegalScraper(),
            "reviews": ReviewsScraper(),
            "sentiment": SentimentScraper(),
        }

        async def run_module(module: str):
            if task_id in self._in_memory:
                self._in_memory[task_id][module]["status"] = "scraping"
            scraper = scraper_map[module]
            result = await scraper.run(credit_code, company_name)
            if task_id in self._in_memory:
                self._in_memory[task_id][module] = result
            await self.db.save_module_data(
                credit_code, module, result["status"],
                result.get("data"), result.get("error")
            )

        await asyncio.gather(*[run_module(m) for m in MODULES])
        await self.db.update_task_status(task_id, "done")
        await self.db.upsert_company(credit_code, company_name)
