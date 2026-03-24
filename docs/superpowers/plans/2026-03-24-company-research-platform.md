# Company Research Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an MVP web app for Chinese job seekers to research companies via on-demand scraping of public Chinese websites, displaying business registration, legal risk, employee reviews, and sentiment data.

**Architecture:** FastAPI backend with asyncio background tasks for parallel scraping across 4 modules; Vue 3 frontend with polling-based progressive loading; SQLite for 24-hour result caching keyed by unified social credit code (统一社会信用代码).

**Tech Stack:** Python 3.11, FastAPI, Playwright, requests, SQLite (aiosqlite), Vue 3, Vite, docker-compose

---

## File Map

```
compan_search_ai/
├── backend/
│   ├── main.py           # FastAPI app, CORS, route registration
│   ├── models.py         # Pydantic request/response models
│   ├── cache.py          # SQLite read/write, 24h TTL
│   ├── tasks.py          # asyncio task orchestration, in-memory state
│   └── scrapers/
│       ├── base.py       # BaseScraper: retry, delay, UA rotation
│       ├── business.py   # 国家企业信用信息公示系统 scraper
│       ├── legal.py      # 裁判文书网 + 执行信息公开网 scraper
│       ├── reviews.py    # 牛客网 public reviews scraper
│       └── sentiment.py  # 知乎 search scraper
├── tests/
│   ├── conftest.py       # pytest fixtures: test client, tmp DB
│   ├── test_cache.py
│   ├── test_tasks.py
│   ├── test_routes.py
│   └── scrapers/
│       ├── test_base.py
│       ├── test_business.py
│       ├── test_legal.py
│       ├── test_reviews.py
│       └── test_sentiment.py
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── src/
│   │   ├── main.js
│   │   ├── router/index.js
│   │   ├── api/company.js       # search(), research(), pollTask(), getCompany()
│   │   ├── views/
│   │   │   ├── Home.vue
│   │   │   └── CompanyDetail.vue
│   │   └── components/
│   │       ├── BusinessInfo.vue
│   │       ├── LegalRisk.vue
│   │       ├── EmployeeReviews.vue
│   │       └── SentimentPanel.vue
├── docker-compose.yml
├── backend/Dockerfile
├── frontend/Dockerfile
└── requirements.txt
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `backend/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/scrapers/__init__.py`
- Create: `backend/scrapers/__init__.py`
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `.gitignore`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
aiosqlite==0.20.0
playwright==1.44.0
requests==2.31.0
pydantic==2.7.1
beautifulsoup4==4.12.3
lxml==5.2.1
pytest==8.2.0
pytest-asyncio==0.23.6
httpx==0.27.0
```

- [ ] **Step 2: Create backend package files**

```bash
mkdir -p backend/scrapers tests/scrapers
touch backend/__init__.py backend/scrapers/__init__.py
touch tests/__init__.py tests/scrapers/__init__.py
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.venv/
venv/
*.db
.env
node_modules/
frontend/dist/
.superpowers/
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_PATH=/app/data/cache.db

  frontend:
    build: ./frontend
    ports:
      - "5173:80"
    depends_on:
      - backend
```

- [ ] **Step 5: Create backend/Dockerfile**

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 6: Install Python dependencies**

```bash
cd backend
python -m venv ../.venv
source ../.venv/Scripts/activate  # Windows: ../.venv/Scripts/activate
pip install -r ../requirements.txt
playwright install chromium
```

- [ ] **Step 7: Commit**

```bash
git add .gitignore requirements.txt docker-compose.yml backend/Dockerfile backend/__init__.py backend/scrapers/__init__.py tests/__init__.py tests/scrapers/__init__.py
git commit -m "chore: project scaffolding and dependencies"
```

---

## Task 2: Data Models

**Files:**
- Create: `backend/models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_models.py`:

```python
from backend.models import (
    SearchResult, SearchResponse,
    ResearchRequest, ResearchResponse,
    ModuleStatus, TaskResponse,
    BusinessData, LegalData, LegalItem,
    ReviewsData, ReviewItem,
    SentimentData, SentimentItem,
)

def test_search_result_fields():
    r = SearchResult(
        credit_code="91110108551385082J",
        name="字节跳动科技有限公司",
        legal_person="张一鸣",
        registered_capital="50000万元",
        province="北京市",
        status="存续",
    )
    assert r.credit_code == "91110108551385082J"

def test_module_status_done():
    m = ModuleStatus(status="done", data={"key": "val"})
    assert m.status == "done"
    assert m.data == {"key": "val"}

def test_module_status_error():
    m = ModuleStatus(status="error", error="403 Forbidden")
    assert m.error == "403 Forbidden"
    assert m.data is None

def test_task_response_overall_status():
    t = TaskResponse(
        task_id="abc",
        overall_status="scraping",
        modules={
            "business": ModuleStatus(status="done", data={}),
            "legal": ModuleStatus(status="scraping"),
        }
    )
    assert t.overall_status == "scraping"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest ../tests/test_models.py -v
```
Expected: ImportError (module doesn't exist yet)

- [ ] **Step 3: Create backend/models.py**

```python
from typing import Any, Optional
from pydantic import BaseModel


class SearchResult(BaseModel):
    credit_code: str
    name: str
    legal_person: str = ""
    registered_capital: str = ""
    province: str = ""
    status: str = ""


class SearchResponse(BaseModel):
    results: list[SearchResult]


class ResearchRequest(BaseModel):
    credit_code: str
    company_name: str


class ResearchResponse(BaseModel):
    task_id: str
    cached: bool


class ModuleStatus(BaseModel):
    status: str  # pending | scraping | done | error
    data: Optional[Any] = None
    error: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    overall_status: str
    modules: dict[str, ModuleStatus]


class BusinessData(BaseModel):
    credit_code: str
    name: str
    legal_person: str = ""
    registered_capital: str = ""
    established_date: str = ""
    status: str = ""
    province: str = ""
    address: str = ""
    business_scope: str = ""


class LegalItem(BaseModel):
    type: str  # lawsuit | enforcement | dishonest
    title: str
    date: str = ""
    court: str = ""
    result: str = ""


class LegalData(BaseModel):
    lawsuit_count: int = 0
    enforcement_count: int = 0
    dishonest_count: int = 0
    items: list[LegalItem] = []


class ReviewItem(BaseModel):
    source: str
    content: str
    date: str = ""
    rating: Optional[int] = None


class ReviewsData(BaseModel):
    source_count: int = 0
    items: list[ReviewItem] = []


class SentimentItem(BaseModel):
    source: str
    title: str
    url: str = ""
    date: str = ""
    snippet: str = ""


class SentimentData(BaseModel):
    item_count: int = 0
    items: list[SentimentItem] = []
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest ../tests/test_models.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/models.py tests/test_models.py
git commit -m "feat: add Pydantic data models"
```

---

## Task 3: Database / Cache Layer

**Files:**
- Create: `backend/cache.py`
- Create: `tests/test_cache.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cache.py`:

```python
import asyncio
import pytest
import time
from backend.cache import Database

@pytest.fixture
async def db(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    await db.init()
    yield db
    await db.close()

@pytest.mark.asyncio
async def test_init_creates_tables(db):
    # If init didn't raise, tables exist
    assert True

@pytest.mark.asyncio
async def test_save_and_get_module_data(db):
    data = {"name": "Test Corp", "status": "存续"}
    await db.save_module_data("CODE123", "business", "done", data)
    result = await db.get_module_data("CODE123", "business")
    assert result["status"] == "done"
    assert result["data"]["name"] == "Test Corp"

@pytest.mark.asyncio
async def test_get_missing_module_returns_none(db):
    result = await db.get_module_data("NOTEXIST", "business")
    assert result is None

@pytest.mark.asyncio
async def test_is_cached_false_when_missing(db):
    assert await db.is_company_cached("NOTEXIST") is False

@pytest.mark.asyncio
async def test_is_cached_true_after_save(db):
    await db.upsert_company("CODE123", "Test Corp")
    assert await db.is_company_cached("CODE123") is True

@pytest.mark.asyncio
async def test_cache_expires_after_ttl(db):
    await db.upsert_company("CODE123", "Test Corp", ttl_seconds=1)
    await asyncio.sleep(1.1)
    assert await db.is_company_cached("CODE123") is False

@pytest.mark.asyncio
async def test_create_and_get_task(db):
    await db.create_task("task-1", "CODE123")
    task = await db.get_task("task-1")
    assert task["status"] == "pending"
    assert task["credit_code"] == "CODE123"

@pytest.mark.asyncio
async def test_update_task_status(db):
    await db.create_task("task-1", "CODE123")
    await db.update_task_status("task-1", "done")
    task = await db.get_task("task-1")
    assert task["status"] == "done"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest ../tests/test_cache.py -v
```
Expected: ImportError

- [ ] **Step 3: Create backend/cache.py**

```python
import json
import time
import aiosqlite
from typing import Any, Optional


class Database:
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def init(self):
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS company_cache (
                credit_code  TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                created_at   INTEGER NOT NULL,
                expires_at   INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS module_data (
                credit_code  TEXT NOT NULL,
                module       TEXT NOT NULL,
                status       TEXT NOT NULL,
                data_json    TEXT,
                error_msg    TEXT,
                updated_at   INTEGER NOT NULL,
                PRIMARY KEY (credit_code, module)
            );
            CREATE TABLE IF NOT EXISTS tasks (
                task_id     TEXT PRIMARY KEY,
                credit_code TEXT NOT NULL,
                created_at  INTEGER NOT NULL,
                status      TEXT NOT NULL
            );
        """)
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def upsert_company(self, credit_code: str, company_name: str, ttl_seconds: int = 86400):
        now = int(time.time())
        await self._conn.execute(
            "INSERT OR REPLACE INTO company_cache VALUES (?, ?, ?, ?)",
            (credit_code, company_name, now, now + ttl_seconds),
        )
        await self._conn.commit()

    async def is_company_cached(self, credit_code: str) -> bool:
        now = int(time.time())
        async with self._conn.execute(
            "SELECT 1 FROM company_cache WHERE credit_code = ? AND expires_at > ?",
            (credit_code, now),
        ) as cur:
            return await cur.fetchone() is not None

    async def save_module_data(
        self, credit_code: str, module: str, status: str,
        data: Optional[Any] = None, error_msg: Optional[str] = None
    ):
        await self._conn.execute(
            """INSERT OR REPLACE INTO module_data
               (credit_code, module, status, data_json, error_msg, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (credit_code, module, status,
             json.dumps(data, ensure_ascii=False) if data is not None else None,
             error_msg, int(time.time())),
        )
        await self._conn.commit()

    async def get_module_data(self, credit_code: str, module: str) -> Optional[dict]:
        async with self._conn.execute(
            "SELECT status, data_json, error_msg FROM module_data WHERE credit_code = ? AND module = ?",
            (credit_code, module),
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return {
            "status": row["status"],
            "data": json.loads(row["data_json"]) if row["data_json"] else None,
            "error": row["error_msg"],
        }

    async def get_all_modules(self, credit_code: str) -> dict:
        async with self._conn.execute(
            "SELECT module, status, data_json, error_msg FROM module_data WHERE credit_code = ?",
            (credit_code,),
        ) as cur:
            rows = await cur.fetchall()
        return {
            row["module"]: {
                "status": row["status"],
                "data": json.loads(row["data_json"]) if row["data_json"] else None,
                "error": row["error_msg"],
            }
            for row in rows
        }

    async def create_task(self, task_id: str, credit_code: str):
        await self._conn.execute(
            "INSERT INTO tasks VALUES (?, ?, ?, ?)",
            (task_id, credit_code, int(time.time()), "pending"),
        )
        await self._conn.commit()

    async def get_task(self, task_id: str) -> Optional[dict]:
        async with self._conn.execute(
            "SELECT task_id, credit_code, status FROM tasks WHERE task_id = ?",
            (task_id,),
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return dict(row)

    async def update_task_status(self, task_id: str, status: str):
        await self._conn.execute(
            "UPDATE tasks SET status = ? WHERE task_id = ?",
            (status, task_id),
        )
        await self._conn.commit()
```

- [ ] **Step 4: Create tests/conftest.py**

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
```

Also add `pytest.ini` at project root:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest ../tests/test_cache.py -v
```
Expected: 8 PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/cache.py tests/test_cache.py tests/conftest.py pytest.ini
git commit -m "feat: add SQLite cache layer with TTL"
```

---

## Task 4: Scraper Base Class

**Files:**
- Create: `backend/scrapers/base.py`
- Create: `tests/scrapers/test_base.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/scrapers/test_base.py
import pytest
from unittest.mock import AsyncMock, patch
from backend.scrapers.base import BaseScraper


class ConcreteScraper(BaseScraper):
    async def scrape(self, credit_code: str, company_name: str):
        return {"ok": True}


@pytest.mark.asyncio
async def test_run_returns_done_on_success():
    s = ConcreteScraper()
    result = await s.run("CODE123", "Test Corp")
    assert result["status"] == "done"
    assert result["data"]["ok"] is True


@pytest.mark.asyncio
async def test_run_returns_error_after_retries():
    class FailingScraper(BaseScraper):
        async def scrape(self, credit_code, company_name):
            raise Exception("网络错误")

    s = FailingScraper(max_retries=2, retry_delay=0)
    result = await s.run("CODE123", "Test Corp")
    assert result["status"] == "error"
    assert "网络错误" in result["error"]


@pytest.mark.asyncio
async def test_random_ua_is_non_empty():
    s = ConcreteScraper()
    ua = s.random_ua()
    assert len(ua) > 10


def test_random_delay_range():
    import asyncio
    s = ConcreteScraper(min_delay=0, max_delay=0)
    # Should not raise
    asyncio.get_event_loop().run_until_complete(s.random_delay())
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest ../tests/scrapers/test_base.py -v
```
Expected: ImportError

- [ ] **Step 3: Create backend/scrapers/base.py**

```python
import asyncio
import random
from abc import ABC, abstractmethod
from typing import Any, Optional

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest ../tests/scrapers/test_base.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/scrapers/base.py tests/scrapers/test_base.py
git commit -m "feat: add scraper base class with retry and UA rotation"
```

---

## Task 5: Business Info Scraper

**Files:**
- Create: `backend/scrapers/business.py`
- Create: `tests/scrapers/test_business.py`

The business scraper queries `https://www.gsxt.gov.cn` (国家企业信用信息公示系统) using requests + BeautifulSoup for the search, then Playwright for the detail page which requires JS rendering.

- [ ] **Step 1: Write the failing tests**

```python
# tests/scrapers/test_business.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest ../tests/scrapers/test_business.py -v
```
Expected: ImportError

- [ ] **Step 3: Create backend/scrapers/business.py**

```python
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
```

Also add `beautifulsoup4==4.12.3` and `lxml==5.2.1` to `requirements.txt`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pip install beautifulsoup4 lxml
pytest ../tests/scrapers/test_business.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/scrapers/business.py tests/scrapers/test_business.py requirements.txt
git commit -m "feat: add business info scraper (国家企信网)"
```

---

## Task 6: Legal Risk Scraper

**Files:**
- Create: `backend/scrapers/legal.py`
- Create: `tests/scrapers/test_legal.py`

Scrapes 中国裁判文书网 (wenshu.court.gov.cn) and 失信被执行人名单 (zxgk.court.gov.cn).

- [ ] **Step 1: Write the failing tests**

```python
# tests/scrapers/test_legal.py
import pytest
from unittest.mock import patch, AsyncMock
from backend.scrapers.legal import LegalScraper

MOCK_LAWSUIT_DATA = {
    "lawsuit_count": 2,
    "enforcement_count": 0,
    "dishonest_count": 0,
    "items": [
        {"type": "lawsuit", "title": "劳动合同纠纷", "date": "2023-05-12",
         "court": "海淀区法院", "result": "调解"},
    ]
}


@pytest.mark.asyncio
async def test_scrape_returns_legal_data():
    scraper = LegalScraper()
    with patch.object(scraper, "_fetch_lawsuits", AsyncMock(return_value=MOCK_LAWSUIT_DATA["items"])):
        with patch.object(scraper, "_fetch_enforcement", AsyncMock(return_value=[])):
            with patch.object(scraper, "_fetch_dishonest", AsyncMock(return_value=[])):
                result = await scraper.scrape("CODE123", "字节跳动")
    assert result["lawsuit_count"] == 1
    assert result["items"][0]["type"] == "lawsuit"


@pytest.mark.asyncio
async def test_scrape_aggregates_all_sources():
    scraper = LegalScraper()
    lawsuit_items = [{"type": "lawsuit", "title": "A", "date": "", "court": "", "result": ""}]
    enforcement_items = [{"type": "enforcement", "title": "B", "date": "", "court": "", "result": ""}]
    with patch.object(scraper, "_fetch_lawsuits", AsyncMock(return_value=lawsuit_items)):
        with patch.object(scraper, "_fetch_enforcement", AsyncMock(return_value=enforcement_items)):
            with patch.object(scraper, "_fetch_dishonest", AsyncMock(return_value=[])):
                result = await scraper.scrape("CODE123", "Test")
    assert result["lawsuit_count"] == 1
    assert result["enforcement_count"] == 1
    assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_partial_failure_returns_available_data():
    scraper = LegalScraper()
    with patch.object(scraper, "_fetch_lawsuits", AsyncMock(side_effect=Exception("超时"))):
        with patch.object(scraper, "_fetch_enforcement", AsyncMock(return_value=[])):
            with patch.object(scraper, "_fetch_dishonest", AsyncMock(return_value=[])):
                result = await scraper.scrape("CODE123", "Test")
    assert result["lawsuit_count"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest ../tests/scrapers/test_legal.py -v
```
Expected: ImportError

- [ ] **Step 3: Create backend/scrapers/legal.py**

```python
import asyncio
import requests
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper

WENSHU_SEARCH = "https://wenshu.court.gov.cn/website/wenshu/181029CR4M5A62CH/index.html"
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
        # 失信被执行人 — same court system, different endpoint
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest ../tests/scrapers/test_legal.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/scrapers/legal.py tests/scrapers/test_legal.py
git commit -m "feat: add legal risk scraper (裁判文书网/执行信息公开网)"
```

---

## Task 7: Employee Reviews Scraper

**Files:**
- Create: `backend/scrapers/reviews.py`
- Create: `tests/scrapers/test_reviews.py`

Scrapes 牛客网 public company reviews (no login required for basic content).

- [ ] **Step 1: Write the failing tests**

```python
# tests/scrapers/test_reviews.py
import pytest
from unittest.mock import patch, AsyncMock
from backend.scrapers.reviews import ReviewsScraper

MOCK_ITEMS = [
    {"source": "牛客网", "content": "氛围不错，加班较多", "date": "2024-01", "rating": 4},
    {"source": "牛客网", "content": "技术氛围好", "date": "2024-02", "rating": 5},
]


@pytest.mark.asyncio
async def test_scrape_returns_reviews_data():
    scraper = ReviewsScraper()
    with patch.object(scraper, "_fetch_niuke_reviews", AsyncMock(return_value=MOCK_ITEMS)):
        result = await scraper.scrape("CODE123", "字节跳动")
    assert result["source_count"] == 2
    assert result["items"][0]["source"] == "牛客网"


@pytest.mark.asyncio
async def test_scrape_returns_empty_on_failure():
    scraper = ReviewsScraper()
    with patch.object(scraper, "_fetch_niuke_reviews", AsyncMock(side_effect=Exception("403"))):
        result = await scraper.scrape("CODE123", "字节跳动")
    assert result["source_count"] == 0
    assert result["items"] == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest ../tests/scrapers/test_reviews.py -v
```
Expected: ImportError

- [ ] **Step 3: Create backend/scrapers/reviews.py**

```python
import asyncio
import requests
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper

NIUKE_SEARCH = "https://www.nowcoder.com/companies"


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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest ../tests/scrapers/test_reviews.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/scrapers/reviews.py tests/scrapers/test_reviews.py
git commit -m "feat: add employee reviews scraper (牛客网)"
```

---

## Task 8: Sentiment Scraper

**Files:**
- Create: `backend/scrapers/sentiment.py`
- Create: `tests/scrapers/test_sentiment.py`

Scrapes 知乎 search results for company mentions.

- [ ] **Step 1: Write the failing tests**

```python
# tests/scrapers/test_sentiment.py
import pytest
from unittest.mock import patch, AsyncMock
from backend.scrapers.sentiment import SentimentScraper

MOCK_ITEMS = [
    {"source": "知乎", "title": "字节跳动工作体验如何？", "url": "https://zhihu.com/q/1",
     "date": "2024-01", "snippet": "整体不错，但是压力大"},
]


@pytest.mark.asyncio
async def test_scrape_returns_sentiment_data():
    scraper = SentimentScraper()
    with patch.object(scraper, "_fetch_zhihu", AsyncMock(return_value=MOCK_ITEMS)):
        result = await scraper.scrape("CODE123", "字节跳动")
    assert result["item_count"] == 1
    assert result["items"][0]["source"] == "知乎"


@pytest.mark.asyncio
async def test_scrape_returns_empty_on_failure():
    scraper = SentimentScraper()
    with patch.object(scraper, "_fetch_zhihu", AsyncMock(side_effect=Exception("反爬"))):
        result = await scraper.scrape("CODE123", "字节跳动")
    assert result["item_count"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest ../tests/scrapers/test_sentiment.py -v
```
Expected: ImportError

- [ ] **Step 3: Create backend/scrapers/sentiment.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest ../tests/scrapers/test_sentiment.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/scrapers/sentiment.py tests/scrapers/test_sentiment.py
git commit -m "feat: add sentiment scraper (知乎)"
```

---

## Task 9: Task Orchestration

**Files:**
- Create: `backend/tasks.py`
- Create: `tests/test_tasks.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tasks.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.tasks import TaskManager
from backend.cache import Database


@pytest.fixture
async def db(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    await db.init()
    yield db
    await db.close()


@pytest.fixture
def task_manager(db):
    return TaskManager(db)


@pytest.mark.asyncio
async def test_create_task_returns_task_id(task_manager):
    task_id = await task_manager.create_task("CODE123", "Test Corp")
    assert len(task_id) > 0


@pytest.mark.asyncio
async def test_get_task_status_pending(task_manager):
    task_id = await task_manager.create_task("CODE123", "Test Corp")
    status = await task_manager.get_task_status(task_id)
    assert status["overall_status"] == "pending"


@pytest.mark.asyncio
async def test_get_nonexistent_task_returns_none(task_manager):
    result = await task_manager.get_task_status("nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_run_task_completes_with_mock_scrapers(task_manager, db):
    mock_result = {"status": "done", "data": {"name": "Test Corp"}}

    with patch("backend.tasks.BusinessScraper") as MockBiz, \
         patch("backend.tasks.LegalScraper") as MockLegal, \
         patch("backend.tasks.ReviewsScraper") as MockReviews, \
         patch("backend.tasks.SentimentScraper") as MockSent:

        for Mock in [MockBiz, MockLegal, MockReviews, MockSent]:
            instance = Mock.return_value
            instance.run = AsyncMock(return_value=mock_result)

        task_id = await task_manager.create_task("CODE123", "Test Corp")
        await task_manager.run_task(task_id, "CODE123", "Test Corp")

    status = await task_manager.get_task_status(task_id)
    assert status["overall_status"] == "done"
    assert status["modules"]["business"]["status"] == "done"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest ../tests/test_tasks.py -v
```
Expected: ImportError

- [ ] **Step 3: Create backend/tasks.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest ../tests/test_tasks.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/tasks.py tests/test_tasks.py
git commit -m "feat: add asyncio task orchestration for parallel scraping"
```

---

## Task 10: FastAPI Routes

**Files:**
- Create: `backend/main.py`
- Create: `tests/test_routes.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_routes.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client(tmp_path):
    import os
    os.environ["DATABASE_PATH"] = str(tmp_path / "test.db")
    from backend.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_search_returns_results(client):
    mock_results = [
        {"credit_code": "CODE123", "name": "字节跳动", "legal_person": "",
         "registered_capital": "", "province": "", "status": ""}
    ]
    with patch("backend.main.BusinessScraper") as MockScraper:
        instance = MockScraper.return_value
        instance.search = AsyncMock(return_value=mock_results)
        resp = await client.get("/api/search?name=字节跳动")
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1


@pytest.mark.asyncio
async def test_research_creates_task(client):
    with patch("backend.main.task_manager") as mock_tm:
        mock_tm.create_task = AsyncMock(return_value="task-abc")
        resp = await client.post("/api/company/research", json={
            "credit_code": "CODE123",
            "company_name": "字节跳动"
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data


@pytest.mark.asyncio
async def test_task_status_not_found(client):
    with patch("backend.main.task_manager") as mock_tm:
        mock_tm.get_task_status = AsyncMock(return_value=None)
        resp = await client.get("/api/task/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_company_not_cached_returns_404(client):
    with patch("backend.main.db") as mock_db:
        mock_db.is_company_cached = AsyncMock(return_value=False)
        resp = await client.get("/api/company/CODE123")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest ../tests/test_routes.py -v
```
Expected: ImportError

- [ ] **Step 3: Create backend/main.py**

```python
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from backend.models import (
    SearchResponse, SearchResult,
    ResearchRequest, ResearchResponse,
    TaskResponse, ModuleStatus,
)
from backend.cache import Database
from backend.tasks import TaskManager
from backend.scrapers.business import BusinessScraper

DATABASE_PATH = os.getenv("DATABASE_PATH", "cache.db")

db: Database = None
task_manager: TaskManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db, task_manager
    db = Database(DATABASE_PATH)
    await db.init()
    task_manager = TaskManager(db)
    yield
    await db.close()


app = FastAPI(title="Company Research API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:80"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/search", response_model=SearchResponse)
async def search(name: str):
    scraper = BusinessScraper(min_delay=0, max_delay=0)
    results = await scraper.search(name)
    return SearchResponse(results=[SearchResult(**r) for r in results])


@app.post("/api/company/research", response_model=ResearchResponse)
async def research(req: ResearchRequest, background_tasks: BackgroundTasks):
    cached = await db.is_company_cached(req.credit_code)
    if cached:
        return ResearchResponse(task_id="", cached=True)

    task_id = await task_manager.create_task(req.credit_code, req.company_name)
    background_tasks.add_task(
        task_manager.run_task, task_id, req.credit_code, req.company_name
    )
    return ResearchResponse(task_id=task_id, cached=False)


@app.get("/api/task/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    status = await task_manager.get_task_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(
        task_id=status["task_id"],
        overall_status=status["overall_status"],
        modules={k: ModuleStatus(**v) for k, v in status["modules"].items()},
    )


@app.get("/api/company/{credit_code}", response_model=TaskResponse)
async def get_company(credit_code: str):
    cached = await db.is_company_cached(credit_code)
    if not cached:
        raise HTTPException(status_code=404, detail="Company not found in cache")
    modules = await db.get_all_modules(credit_code)
    return TaskResponse(
        task_id="",
        overall_status="done",
        modules={k: ModuleStatus(**v) for k, v in modules.items()},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest ../tests/test_routes.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Run all backend tests**

```bash
pytest ../tests/ -v
```
Expected: All PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/main.py tests/test_routes.py
git commit -m "feat: add FastAPI routes for search, research, task polling, and cache"
```

---

## Task 11: Vue 3 Frontend Setup

**Files:**
- Create: `frontend/` (Vite + Vue 3 project)
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/api/company.js`

- [ ] **Step 1: Scaffold Vue 3 project**

```bash
cd compan_search_ai
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm install vue-router@4
```

- [ ] **Step 2: Create frontend/src/router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import CompanyDetail from '../views/CompanyDetail.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/company/:creditCode', component: CompanyDetail, props: true },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
```

- [ ] **Step 3: Update frontend/src/main.js**

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'

createApp(App).use(router).mount('#app')
```

- [ ] **Step 4: Create frontend/src/api/company.js**

```javascript
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function search(name) {
  const res = await fetch(`${BASE}/api/search?name=${encodeURIComponent(name)}`)
  if (!res.ok) throw new Error('搜索失败')
  return res.json()
}

export async function research(creditCode, companyName) {
  const res = await fetch(`${BASE}/api/company/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credit_code: creditCode, company_name: companyName }),
  })
  if (!res.ok) throw new Error('发起爬取失败')
  return res.json()
}

export async function pollTask(taskId) {
  const res = await fetch(`${BASE}/api/task/${taskId}`)
  if (!res.ok) throw new Error('查询任务状态失败')
  return res.json()
}

export async function getCompany(creditCode) {
  const res = await fetch(`${BASE}/api/company/${creditCode}`)
  if (!res.ok) throw new Error('获取公司数据失败')
  return res.json()
}
```

- [ ] **Step 5: Create frontend/.env.development**

```
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 6: Verify dev server starts**

```bash
cd frontend
npm run dev
```
Expected: Server running at http://localhost:5173

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Vue 3 frontend with router and API client"
```

---

## Task 12: Home Page

**Files:**
- Create: `frontend/src/views/Home.vue`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Update frontend/src/App.vue**

```vue
<template>
  <RouterView />
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; color: #1a1a2e; }
</style>
```

- [ ] **Step 2: Create frontend/src/views/Home.vue**

```vue
<template>
  <div class="home">
    <div class="hero">
      <h1>公司调研平台</h1>
      <p class="subtitle">了解你要去的公司，做出更明智的选择</p>
      <div class="search-box">
        <input
          v-model="query"
          placeholder="输入公司名称，如：字节跳动"
          @keyup.enter="doSearch"
        />
        <button @click="doSearch" :disabled="loading">
          {{ loading ? '搜索中...' : '搜索' }}
        </button>
      </div>
    </div>

    <div class="results" v-if="results.length > 0">
      <div
        v-for="r in results"
        :key="r.credit_code"
        class="result-item"
        @click="goToCompany(r)"
      >
        <div class="result-name">{{ r.name }}</div>
        <div class="result-meta">
          {{ r.province }} · {{ r.registered_capital }} · {{ r.status }}
        </div>
      </div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { search } from '../api/company.js'

const router = useRouter()
const query = ref('')
const results = ref([])
const loading = ref(false)
const error = ref('')

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  error.value = ''
  results.value = []
  try {
    const data = await search(query.value.trim())
    results.value = data.results
    if (results.value.length === 0) error.value = '未找到相关公司'
  } catch (e) {
    error.value = '搜索失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function goToCompany(company) {
  router.push({
    path: `/company/${company.credit_code}`,
    query: { name: company.name },
  })
}
</script>

<style scoped>
.home { min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 80px 24px 40px; }
.hero { text-align: center; max-width: 600px; width: 100%; }
h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
.subtitle { color: #888; margin-bottom: 32px; }
.search-box { display: flex; gap: 8px; background: #fff; border-radius: 10px; padding: 6px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.search-box input { flex: 1; border: none; outline: none; font-size: 15px; padding: 8px 12px; }
.search-box button { background: #4a7cf0; color: #fff; border: none; border-radius: 8px; padding: 8px 20px; font-size: 14px; cursor: pointer; white-space: nowrap; }
.search-box button:disabled { opacity: 0.6; cursor: not-allowed; }
.results { margin-top: 32px; width: 100%; max-width: 600px; }
.result-item { background: #fff; border-radius: 10px; padding: 16px 20px; margin-bottom: 10px; cursor: pointer; box-shadow: 0 1px 4px rgba(0,0,0,0.06); transition: box-shadow 0.2s; }
.result-item:hover { box-shadow: 0 4px 16px rgba(74,124,240,0.15); }
.result-name { font-weight: 600; font-size: 15px; margin-bottom: 4px; }
.result-meta { color: #888; font-size: 13px; }
.error { margin-top: 24px; color: #e05050; }
</style>
```

- [ ] **Step 3: Verify in browser**

```bash
cd frontend && npm run dev
```
Open http://localhost:5173, verify search box renders correctly.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/Home.vue frontend/src/App.vue
git commit -m "feat: add Home page with company search"
```

---

## Task 13: Tab Components

**Files:**
- Create: `frontend/src/components/BusinessInfo.vue`
- Create: `frontend/src/components/LegalRisk.vue`
- Create: `frontend/src/components/EmployeeReviews.vue`
- Create: `frontend/src/components/SentimentPanel.vue`

- [ ] **Step 1: Create frontend/src/components/BusinessInfo.vue**

```vue
<template>
  <div class="tab-panel">
    <div v-if="!data" class="loading">数据加载中...</div>
    <div v-else class="grid">
      <div class="card"><div class="label">法定代表人</div><div class="val">{{ data.legal_person || '—' }}</div></div>
      <div class="card"><div class="label">成立日期</div><div class="val">{{ data.established_date || '—' }}</div></div>
      <div class="card"><div class="label">注册资本</div><div class="val">{{ data.registered_capital || '—' }}</div></div>
      <div class="card"><div class="label">经营状态</div><div class="val" :class="data.status === '存续' ? 'green' : ''">{{ data.status || '—' }}</div></div>
      <div class="card full"><div class="label">注册地址</div><div class="val">{{ data.address || '—' }}</div></div>
      <div class="card full"><div class="label">经营范围</div><div class="val">{{ data.business_scope || '—' }}</div></div>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: Object })
</script>

<style scoped>
.tab-panel { padding: 20px 0; }
.loading { color: #888; text-align: center; padding: 40px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.card { background: #fff; border-radius: 10px; padding: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.card.full { grid-column: 1 / -1; }
.label { color: #aaa; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.val { color: #1a1a2e; font-weight: 500; font-size: 14px; line-height: 1.5; }
.green { color: #2a8a50; }
</style>
```

- [ ] **Step 2: Create frontend/src/components/LegalRisk.vue**

```vue
<template>
  <div class="tab-panel">
    <div v-if="!data" class="loading">数据加载中...</div>
    <template v-else>
      <div class="summary">
        <div class="stat" :class="data.lawsuit_count > 0 ? 'warn' : 'ok'">
          <div class="num">{{ data.lawsuit_count }}</div><div class="desc">诉讼案件</div>
        </div>
        <div class="stat" :class="data.enforcement_count > 0 ? 'bad' : 'ok'">
          <div class="num">{{ data.enforcement_count }}</div><div class="desc">被执行</div>
        </div>
        <div class="stat" :class="data.dishonest_count > 0 ? 'bad' : 'ok'">
          <div class="num">{{ data.dishonest_count }}</div><div class="desc">失信记录</div>
        </div>
      </div>
      <div v-if="data.items.length === 0" class="empty">暂无法律风险记录</div>
      <div v-for="item in data.items" :key="item.title" class="item">
        <span class="tag" :class="item.type">{{ typeLabel(item.type) }}</span>
        <span class="title">{{ item.title }}</span>
        <span class="meta">{{ item.date }} {{ item.court }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({ data: Object })
function typeLabel(t) { return { lawsuit: '诉讼', enforcement: '被执行', dishonest: '失信' }[t] || t }
</script>

<style scoped>
.tab-panel { padding: 20px 0; }
.loading, .empty { color: #888; text-align: center; padding: 40px; }
.summary { display: flex; gap: 12px; margin-bottom: 20px; }
.stat { flex: 1; background: #fff; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.num { font-size: 28px; font-weight: 700; }
.desc { color: #888; font-size: 12px; margin-top: 4px; }
.ok .num { color: #2a8a50; }
.warn .num { color: #f0a030; }
.bad .num { color: #e05050; }
.item { background: #fff; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }
.lawsuit { background: #fff3e0; color: #e65100; }
.enforcement { background: #fce4ec; color: #c62828; }
.dishonest { background: #fce4ec; color: #c62828; }
.title { flex: 1; font-size: 13px; }
.meta { color: #aaa; font-size: 12px; white-space: nowrap; }
</style>
```

- [ ] **Step 3: Create frontend/src/components/EmployeeReviews.vue**

```vue
<template>
  <div class="tab-panel">
    <div v-if="!data" class="loading">数据加载中...</div>
    <template v-else>
      <div class="count">共 {{ data.source_count }} 条评价</div>
      <div v-if="data.items.length === 0" class="empty">暂无员工评价数据</div>
      <div v-for="(item, i) in data.items" :key="i" class="review">
        <div class="review-header">
          <span class="source">{{ item.source }}</span>
          <span class="stars" v-if="item.rating">{{ '★'.repeat(item.rating) }}{{ '☆'.repeat(5 - item.rating) }}</span>
          <span class="date">{{ item.date }}</span>
        </div>
        <p class="content">{{ item.content }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({ data: Object })
</script>

<style scoped>
.tab-panel { padding: 20px 0; }
.loading, .empty { color: #888; text-align: center; padding: 40px; }
.count { color: #888; font-size: 13px; margin-bottom: 16px; }
.review { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.review-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.source { background: #e8f0fe; color: #4a7cf0; font-size: 11px; padding: 2px 8px; border-radius: 4px; }
.stars { color: #f0a030; font-size: 13px; }
.date { color: #aaa; font-size: 12px; margin-left: auto; }
.content { color: #444; font-size: 14px; line-height: 1.6; }
</style>
```

- [ ] **Step 4: Create frontend/src/components/SentimentPanel.vue**

```vue
<template>
  <div class="tab-panel">
    <div v-if="!data" class="loading">数据加载中...</div>
    <template v-else>
      <div class="count">共 {{ data.item_count }} 条相关讨论</div>
      <div v-if="data.items.length === 0" class="empty">暂无网络舆情数据</div>
      <div v-for="(item, i) in data.items" :key="i" class="sentiment-item">
        <div class="item-header">
          <span class="source">{{ item.source }}</span>
          <span class="date">{{ item.date }}</span>
        </div>
        <a class="title" :href="item.url" target="_blank" rel="noopener">{{ item.title }}</a>
        <p class="snippet" v-if="item.snippet">{{ item.snippet }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({ data: Object })
</script>

<style scoped>
.tab-panel { padding: 20px 0; }
.loading, .empty { color: #888; text-align: center; padding: 40px; }
.count { color: #888; font-size: 13px; margin-bottom: 16px; }
.sentiment-item { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.item-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.source { background: #e8f5ee; color: #2a8a50; font-size: 11px; padding: 2px 8px; border-radius: 4px; }
.date { color: #aaa; font-size: 12px; margin-left: auto; }
.title { font-size: 14px; font-weight: 500; color: #4a7cf0; text-decoration: none; display: block; margin-bottom: 6px; }
.title:hover { text-decoration: underline; }
.snippet { color: #666; font-size: 13px; line-height: 1.6; }
</style>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add BusinessInfo, LegalRisk, EmployeeReviews, SentimentPanel components"
```

---

## Task 14: Company Detail Page

**Files:**
- Create: `frontend/src/views/CompanyDetail.vue`

- [ ] **Step 1: Create frontend/src/views/CompanyDetail.vue**

```vue
<template>
  <div class="detail">
    <!-- Header -->
    <div class="company-header">
      <button class="back" @click="$router.push('/')">← 返回</button>
      <div class="company-info">
        <div class="avatar">{{ (companyName || '?')[0] }}</div>
        <div>
          <h2>{{ companyName }}</h2>
          <p class="meta">统一社会信用代码：{{ creditCode }}</p>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
        <span v-if="moduleStatus(tab.key) === 'error'" class="badge error">!</span>
        <span v-else-if="moduleStatus(tab.key) !== 'done'" class="badge loading">…</span>
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <div v-if="moduleStatus(activeTab) === 'error'" class="error-msg">
        数据获取失败，可能因目标网站限制
      </div>
      <template v-else>
        <BusinessInfo v-if="activeTab === 'business'" :data="moduleData('business')" />
        <LegalRisk v-if="activeTab === 'legal'" :data="moduleData('legal')" />
        <EmployeeReviews v-if="activeTab === 'reviews'" :data="moduleData('reviews')" />
        <SentimentPanel v-if="activeTab === 'sentiment'" :data="moduleData('sentiment')" />
      </template>
    </div>

    <!-- Global status -->
    <div v-if="overallStatus === 'scraping' || overallStatus === 'pending'" class="status-bar">
      <span class="dot"></span> 数据爬取中，已完成的模块实时显示...
    </div>
    <div v-if="timedOut" class="status-bar error">
      爬取超时，请<button class="retry" @click="startResearch">重新搜索</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { research, pollTask, getCompany } from '../api/company.js'
import BusinessInfo from '../components/BusinessInfo.vue'
import LegalRisk from '../components/LegalRisk.vue'
import EmployeeReviews from '../components/EmployeeReviews.vue'
import SentimentPanel from '../components/SentimentPanel.vue'

const route = useRoute()
const creditCode = route.params.creditCode
const companyName = route.query.name || creditCode

const tabs = [
  { key: 'business', label: '工商信息' },
  { key: 'legal', label: '法律风险' },
  { key: 'reviews', label: '员工评价' },
  { key: 'sentiment', label: '舆情风评' },
]
const activeTab = ref('business')
const modules = ref({})
const overallStatus = ref('pending')
const timedOut = ref(false)

let pollInterval = null
let pollStart = null

function moduleStatus(key) {
  return modules.value[key]?.status || 'pending'
}
function moduleData(key) {
  const m = modules.value[key]
  return m?.status === 'done' ? m.data : null
}

async function startResearch() {
  timedOut.value = false
  overallStatus.value = 'pending'
  modules.value = {}
  pollStart = Date.now()

  const { task_id, cached } = await research(creditCode, companyName)

  if (cached) {
    const data = await getCompany(creditCode)
    modules.value = data.modules
    overallStatus.value = 'done'
    return
  }

  pollInterval = setInterval(async () => {
    if (Date.now() - pollStart > 120_000) {
      clearInterval(pollInterval)
      timedOut.value = true
      return
    }
    const status = await pollTask(task_id)
    modules.value = status.modules
    overallStatus.value = status.overall_status
    if (status.overall_status === 'done') {
      clearInterval(pollInterval)
    }
  }, 3000)
}

onMounted(startResearch)
onUnmounted(() => clearInterval(pollInterval))
</script>

<style scoped>
.detail { max-width: 800px; margin: 0 auto; padding: 24px; }
.company-header { background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.back { background: none; border: none; color: #4a7cf0; cursor: pointer; font-size: 14px; margin-bottom: 16px; padding: 0; }
.company-info { display: flex; align-items: center; gap: 16px; }
.avatar { width: 50px; height: 50px; background: #e8f0fe; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #4a7cf0; font-size: 22px; font-weight: bold; flex-shrink: 0; }
h2 { font-size: 18px; margin-bottom: 4px; }
.meta { color: #888; font-size: 12px; }
.tabs { display: flex; gap: 4px; background: #fff; border-radius: 12px; padding: 8px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.tab { flex: 1; padding: 8px; border: none; background: none; cursor: pointer; border-radius: 8px; font-size: 13px; color: #888; position: relative; }
.tab.active { background: #4a7cf0; color: #fff; font-weight: 500; }
.badge { position: absolute; top: 4px; right: 4px; font-size: 10px; width: 14px; height: 14px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.badge.error { background: #e05050; color: #fff; }
.badge.loading { background: #f0a030; color: #fff; }
.tab-content { background: #fff; border-radius: 12px; padding: 20px 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); min-height: 200px; }
.error-msg { color: #e05050; text-align: center; padding: 40px; }
.status-bar { background: #fff8ed; border: 1px solid #fde8b0; border-radius: 10px; padding: 10px 16px; margin-top: 12px; font-size: 13px; color: #b07020; display: flex; align-items: center; gap: 8px; }
.status-bar.error { background: #fef0f0; border-color: #fcc; color: #c00; }
.dot { width: 8px; height: 8px; background: #f0a030; border-radius: 50%; flex-shrink: 0; }
.retry { background: none; border: none; color: #4a7cf0; cursor: pointer; text-decoration: underline; }
</style>
```

- [ ] **Step 2: Verify full flow in browser**

Start backend: `cd backend && uvicorn main:app --reload`
Start frontend: `cd frontend && npm run dev`

1. Open http://localhost:5173
2. Search for a company
3. Click a result
4. Verify detail page loads with tabs and polling

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/CompanyDetail.vue
git commit -m "feat: add CompanyDetail page with progressive tab loading and polling"
```

---

## Task 15: Frontend Docker + Final Integration

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`

- [ ] **Step 1: Build frontend for production**

```bash
cd frontend && npm run build
```
Expected: `frontend/dist/` created

- [ ] **Step 2: Create frontend/nginx.conf**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 3: Create frontend/Dockerfile**

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] **Step 4: Test docker-compose build**

```bash
cd compan_search_ai
docker-compose build
docker-compose up
```
Expected: Frontend at http://localhost:5173, backend at http://localhost:8000

- [ ] **Step 5: Run full backend test suite one final time**

```bash
pytest tests/ -v
```
Expected: All PASSED

- [ ] **Step 6: Final commit and push**

```bash
git add frontend/Dockerfile frontend/nginx.conf
git commit -m "feat: add frontend Docker build with nginx proxy"
git push origin master
```

---

## Summary

| Task | What It Builds |
|------|---------------|
| 1 | Project scaffolding, docker, dependencies |
| 2 | Pydantic data models |
| 3 | SQLite cache layer with TTL |
| 4 | Scraper base class (retry, UA rotation) |
| 5 | Business info scraper (国家企信网) |
| 6 | Legal risk scraper (裁判文书网) |
| 7 | Employee reviews scraper (牛客网) |
| 8 | Sentiment scraper (知乎) |
| 9 | Asyncio task orchestration |
| 10 | FastAPI routes (search, research, poll, cache) |
| 11 | Vue 3 setup, router, API client |
| 12 | Home page (search + results) |
| 13 | Tab components (4 modules) |
| 14 | Company detail page (polling + progressive load) |
| 15 | Docker integration + final verification |
