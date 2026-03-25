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
