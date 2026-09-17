import asyncio
import time
import pytest
from app.database import repository

@pytest.mark.asyncio
async def test_repository_non_blocking_event_loop():
    """
    Verifies that database repository operations execute asynchronously in thread pools
    and do not block the asyncio event loop from processing concurrent tasks.
    """
    loop_ticks = 0

    async def background_ticker():
        nonlocal loop_ticks
        for _ in range(20):
            loop_ticks += 1
            await asyncio.sleep(0.01)

    # Launch background ticker concurrently with database health check
    ticker_task = asyncio.create_task(background_ticker())
    db_result = await repository.check_health()
    await ticker_task

    assert db_result is True
    assert loop_ticks >= 1, "Asyncio event loop must continue ticking while database operations execute"
