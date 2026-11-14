from datetime import datetime, timedelta, timezone

import pytest
from datetime import timedelta

import pytest
from mistralai.workflows.testing import create_test_worker

from mistralai.workflows.core.activity import get_all_temporal_activities

from worker.workflows.daily_sync import (
    CalendarEvent,
    DailySync,
    SlackMessage,
    build_tasks,
)

WORKFLOW_EXECUTION_TIMEOUT = timedelta(seconds=10)


def _event(title: str, hours_from_now: float) -> CalendarEvent:
    start = datetime.now(tz=timezone.utc) + timedelta(hours=hours_from_now)
    return CalendarEvent(title=title, start=start, end=start + timedelta(hours=1))


def test_build_tasks_filters_and_maps() -> None:
    events = [
        _event("Colle Maths — Moutawakil (gr 10)", 24),
        _event("DS Maths — TSI1", 48),
        _event("Maths — Regnaud (cours)", 3),
        _event("Interro de cours physique", 30),
    ]
    messages = [
        SlackMessage(channel="#2-math", text="Programme de colles en ligne", ts=1763000000.0),
        SlackMessage(channel="#3-physique-chimie", text="Interro lundi sur le chapitre 6", ts=1763000100.0),
    ]
    tasks = build_tasks(events, messages)
    assert [t.category for t in tasks if t.source == "agenda"] == ["devoir"] * 3
    assert not any("Regnaud" in t.text for t in tasks)
    assert len([t for t in tasks if t.source == "slack"]) == 2
    assert all(t.due is not None for t in tasks if t.source == "agenda")
    ids = [t.id for t in tasks]
    assert len(ids) == len(set(ids))


def test_build_tasks_empty_inputs() -> None:
    assert build_tasks([], []) == []


@pytest.mark.asyncio
async def test_daily_sync_dry_run(temporal_env) -> None:
    import asyncio

    async with create_test_worker(
        temporal_env,
        workflows=[DailySync],
        activities=[
            a for a in get_all_temporal_activities()
            if getattr(a, "__name__", "") in ("fetch_calendar_events", "fetch_slack_messages", "push_tasks")
        ],
    ):
        handle = await temporal_env.client.start_workflow(
            "daily_sync",
            {"dry_run": True},
            id="test-daily-sync",
            task_queue="test-task-queue",
            execution_timeout=WORKFLOW_EXECUTION_TIMEOUT,
        )
        result = await asyncio.wait_for(handle.result(), timeout=15)
    assert result["dry_run"] is True
    assert result["pushed"] is False
    assert result["commit_url"] is None
    assert result["tasks"] == []
    assert "dry-run" in result["summary"]
