import pytest
from unittest.mock import AsyncMock, patch
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
