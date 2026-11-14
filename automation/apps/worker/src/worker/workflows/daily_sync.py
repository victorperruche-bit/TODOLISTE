"""Daily sync of Google Calendar (colles, DS) and Slack announcements into the Todoliste app.

Every morning at 06:30 Europe/Paris, the workflow reads the user's calendar and the
class Slack channels, turns colles/DS/controles and teacher announcements into tasks,
and commits ``tasks.json`` to the app repository so the PWA can pick them up.
"""

from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import mistralai.workflows as workflows
from pydantic import BaseModel, Field


def _settings():
    from env._base import BaseEnv
    from env._mistral_secrets import WorkspaceSecret
    from typing import Annotated

    class SyncSettings(BaseEnv):
        github_repo: str = "victorperruche-bit/TODOLISTE"
        github_branch: str = "main"
        tasks_path: str = "tasks.json"
        slack_channels: str = "#2-math,#3-physique-chimie"
        calendar_id: str = "primary"
        github_token: Annotated[str | None, WorkspaceSecret()] = None
        slack_token: Annotated[str | None, WorkspaceSecret()] = None
        google_service_account_json: Annotated[str | None, WorkspaceSecret()] = None

    return SyncSettings()

_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

_PRIORITY_KEYWORDS = ("colle", "ds", "contrôle", "controle", "interro", "devoir")


class SyncInput(BaseModel):
    dry_run: bool = True
    lookahead_days: int = 7
    lookback_hours: int = 48


class CalendarEvent(BaseModel):
    title: str
    start: datetime
    end: datetime | None = None
    html_link: str | None = None


class SlackMessage(BaseModel):
    channel: str
    text: str
    ts: float
    user: str | None = None


class Task(BaseModel):
    id: str
    text: str
    category: str
    due: int | None = None
    source: str
    url: str | None = None
    done: bool = False


class SyncOutput(BaseModel):
    dry_run: bool
    generated_at: str
    tasks: list[Task]
    pushed: bool = False
    commit_url: str | None = None
    calendar_events: int = 0
    slack_messages: int = 0
    summary: str = ""


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _google_access_token(service_account_json: str) -> str:
    import httpx

    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    info = json.loads(service_account_json)
    now = int(time.time())
    header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = _b64url(
        json.dumps(
            {
                "iss": info["client_email"],
                "scope": _CALENDAR_SCOPE,
                "aud": info["token_uri"],
                "iat": now,
                "exp": now + 3600,
            }
        ).encode()
    )
    key = serialization.load_pem_private_key(info["private_key"].encode(), password=None)
    signature = key.sign(f"{header}.{claims}".encode(), padding.PKCS1v15(), hashes.SHA256())
    assertion = f"{header}.{claims}.{_b64url(signature)}"
    resp = httpx.post(
        info["token_uri"],
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _parse_google_when(item: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    start_raw = (item.get("start") or {}).get("dateTime") or (item.get("start") or {}).get("date")
    end_raw = (item.get("end") or {}).get("dateTime") or (item.get("end") or {}).get("date")
    start = datetime.fromisoformat(start_raw) if start_raw else None
    end = datetime.fromisoformat(end_raw) if end_raw else None
    return start, end


@workflows.activity()
async def fetch_calendar_events(start_iso: str, end_iso: str) -> list[CalendarEvent]:
    import httpx

    settings = _settings()
    if not settings.google_service_account_json:
        return []
    token = _google_access_token(settings.google_service_account_json)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://www.googleapis.com/calendar/v3/calendars/{settings.calendar_id}/events",
            params={
                "timeMin": start_iso,
                "timeMax": end_iso,
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 100,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    events: list[CalendarEvent] = []
    for item in items:
        start, end = _parse_google_when(item)
        if start is None:
            continue
        events.append(
            CalendarEvent(
                title=item.get("summary") or "(sans titre)",
                start=start,
                end=end,
                html_link=item.get("htmlLink"),
            )
        )
    return events


@workflows.activity()
async def fetch_slack_messages(since_ts: float) -> list[SlackMessage]:
    import httpx

    settings = _settings()
    if not settings.slack_token:
        return []
    wanted = {name.strip().lstrip("#").lower() for name in settings.slack_channels.split(",") if name.strip()}
    headers = {"Authorization": f"Bearer {settings.slack_token}"}
    messages: list[SlackMessage] = []
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://slack.com/api/conversations.list",
            params={"types": "public_channel,private_channel", "exclude_archived": "true", "limit": 200},
            headers=headers,
        )
        resp.raise_for_status()
        channels = [c for c in resp.json().get("channels", []) if c.get("name", "") in wanted]
        for channel in channels:
            hist = await client.get(
                "https://slack.com/api/conversations.history",
                params={"channel": channel["id"], "oldest": since_ts, "limit": 20},
                headers=headers,
            )
            hist.raise_for_status()
            for msg in hist.json().get("messages", []):
                if msg.get("subtype") or msg.get("bot_id"):
                    continue
                text = (msg.get("text") or "").strip()
                if not text:
                    continue
                messages.append(
                    SlackMessage(
                        channel=f"#{channel['name']}",
                        text=text,
                        ts=float(msg.get("ts", 0)),
                        user=msg.get("user"),
                    )
                )
    messages.sort(key=lambda m: m.ts, reverse=True)
    return messages


@workflows.activity()
async def push_tasks(payload: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    import httpx

    settings = _settings()
    if dry_run:
        return {"pushed": False, "commit_url": None}
    if not settings.github_token:
        raise RuntimeError("GITHUB_TOKEN is not configured")
    content = base64.b64encode(json.dumps(payload, ensure_ascii=False, indent=2).encode()).decode()
    api = f"https://api.github.com/repos/{settings.github_repo}/contents/{settings.tasks_path}"
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
    }
    body: dict[str, Any] = {
        "message": "chore: sync tasks from agenda & slack",
        "content": content,
        "branch": settings.github_branch,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        current = await client.get(api, params={"ref": settings.github_branch}, headers=headers)
        if current.status_code == 200:
            body["sha"] = current.json()["sha"]
        elif current.status_code != 404:
            current.raise_for_status()
        resp = await client.put(api, headers=headers, json=body)
        resp.raise_for_status()
        commit = resp.json().get("commit", {})
    return {"pushed": True, "commit_url": commit.get("html_url")}


def build_tasks(events: list[CalendarEvent], messages: list[SlackMessage]) -> list[Task]:
    tasks: list[Task] = []
    for event in events:
        title = event.title.lower()
        if not any(keyword in title for keyword in _PRIORITY_KEYWORDS):
            continue
        due = None
        if event.start.tzinfo is None:
            event.start = event.start.replace(tzinfo=timezone.utc)
        due = int(event.start.timestamp() * 1000)
        tasks.append(
            Task(
                id=f"agenda-{int(event.start.timestamp())}-{event.title[:40]}",
                text=f"{event.title} ({event.start.strftime('%a %d %b %Hh%M')})",
                category="devoir",
                due=due,
                source="agenda",
                url=event.html_link,
            )
        )
    for message in messages:
        when = datetime.fromtimestamp(message.ts, tz=timezone.utc).astimezone()
        tasks.append(
            Task(
                id=f"slack-{message.channel}-{message.ts}",
                text=f"{message.channel} : {message.text[:120]}",
                category="slack",
                due=None,
                source="slack",
                url=None,
            )
        )
    return tasks


@workflows.workflow.define(name="daily_sync")
class DailySync:
    @workflows.workflow.entrypoint
    async def run(self, data: SyncInput) -> SyncOutput:
        now = workflows.workflow.now()
        start = now
        end = now + timedelta(days=data.lookahead_days)
        since_ts = now.timestamp() - data.lookback_hours * 3600
        events = await fetch_calendar_events(start.isoformat(), end.isoformat())
        messages = await fetch_slack_messages(since_ts)
        tasks = build_tasks(events, messages)
        payload = {
            "generated_at": now.isoformat(),
            "tasks": [task.model_dump() for task in tasks],
        }
        push = await push_tasks(payload, dry_run=data.dry_run)
        summary = (
            f"{len(tasks)} tâche(s) synchronisée(s) "
            f"({len([t for t in tasks if t.source == 'agenda'])} agenda, "
            f"{len([t for t in tasks if t.source == 'slack'])} slack) — "
            + ("dry-run, rien n'a été poussé" if data.dry_run else f"poussé : {push.get('commit_url')}")
        )
        return SyncOutput(
            dry_run=data.dry_run,
            generated_at=now.isoformat(),
            tasks=tasks,
            pushed=push.get("pushed", False),
            commit_url=push.get("commit_url"),
            calendar_events=len(events),
            slack_messages=len(messages),
            summary=summary,
        )
