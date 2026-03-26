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

db: Database = Database(DATABASE_PATH)
task_manager: TaskManager = None

_db_initialized = False
_init_lock = asyncio.Lock()


async def _ensure_initialized():
    global db, task_manager, _db_initialized
    if not _db_initialized:
        async with _init_lock:
            if not _db_initialized:
                db_path = os.getenv("DATABASE_PATH", "cache.db")
                if db.db_path != db_path:
                    db = Database(db_path)
                await db.init()
                task_manager = TaskManager(db)
                _db_initialized = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db, task_manager, _db_initialized
    db_path = os.getenv("DATABASE_PATH", "cache.db")
    db = Database(db_path)
    await db.init()
    task_manager = TaskManager(db)
    _db_initialized = True
    yield
    await db.close()
    _db_initialized = False


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
    await _ensure_initialized()
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
    await _ensure_initialized()
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
    await _ensure_initialized()
    cached = await db.is_company_cached(credit_code)
    if not cached:
        raise HTTPException(status_code=404, detail="Company not found in cache")
    modules = await db.get_all_modules(credit_code)
    return TaskResponse(
        task_id="",
        overall_status="done",
        modules={k: ModuleStatus(**v) for k, v in modules.items()},
    )
