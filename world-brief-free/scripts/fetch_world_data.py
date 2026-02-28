#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_JSON = DATA_DIR / "world.json"
OUT_MD = DATA_DIR / "daily_brief.md"


def fetch_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "world-brief-free/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_usgs(limit: int = 80) -> list[dict[str, Any]]:
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    data = fetch_json(url)
    events: list[dict[str, Any]] = []
    for feature in data.get("features", [])[:limit]:
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [None, None])
        mag = props.get("mag")
        events.append(
            {
                "id": f"usgs-{feature.get('id', '')}",
                "title": props.get("title", "Earthquake"),
                "category": "earthquake",
                "lat": coords[1] if len(coords) > 1 else None,
                "lon": coords[0] if len(coords) > 0 else None,
                "time": iso_from_epoch_ms(props.get("time")),
                "source": "USGS",
                "url": props.get("url"),
                "severity": mag if isinstance(mag, (int, float)) else None,
            }
        )
    return events


def fetch_eonet(limit: int = 60) -> list[dict[str, Any]]:
    url = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=200"
    data = fetch_json(url)
    events: list[dict[str, Any]] = []
    for event in data.get("events", [])[:limit]:
        geom = event.get("geometry", [])
        latest = geom[-1] if geom else {}
        coords = latest.get("coordinates", [None, None])
        categories = event.get("categories", [])
        category = categories[0].get("id", "natural") if categories else "natural"
        events.append(
            {
                "id": f"eonet-{event.get('id', '')}",
                "title": event.get("title", "Natural Event"),
                "category": str(category).lower(),
                "lat": coords[1] if len(coords) > 1 else None,
                "lon": coords[0] if len(coords) > 0 else None,
                "time": latest.get("date"),
                "source": "NASA EONET",
                "url": event.get("link"),
                "severity": None,
            }
        )
    return events


def fetch_reliefweb(limit: int = 40) -> list[dict[str, Any]]:
    params = {
        "appname": "world-brief-free",
        "limit": str(limit),
        "sort[]": "date.created:desc",
        "profile": "full",
    }
    url = "https://api.reliefweb.int/v1/disasters?" + urllib.parse.urlencode(params)
    data = fetch_json(url)
    events: list[dict[str, Any]] = []
    for item in data.get("data", [])[:limit]:
        fields = item.get("fields", {})
        countries = fields.get("country", [])
        country_name = countries[0].get("name") if countries else "Unknown"
        types_ = fields.get("type", [])
        dtype = types_[0].get("name", "disaster") if types_ else "disaster"
        title = fields.get("name") or f"{dtype} in {country_name}"
        events.append(
            {
                "id": f"rw-{item.get('id', '')}",
                "title": title,
                "category": "humanitarian",
                "lat": None,
                "lon": None,
                "time": fields.get("date", {}).get("created"),
                "source": "ReliefWeb",
                "url": fields.get("url"),
                "severity": None,
            }
        )
    return events


def iso_from_epoch_ms(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def build_brief(payload: dict[str, Any]) -> str:
    counts: dict[str, int] = {}
    for event in payload["events"]:
        cat = event["category"]
        counts[cat] = counts.get(cat, 0) + 1

    top_lines = []
    for cat, n in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:8]:
        top_lines.append(f"- {cat}: {n}")

    latest_items = sorted(
        payload["events"],
        key=lambda e: e.get("time") or "",
        reverse=True,
    )[:15]
    latest_lines = [
        f"- {e.get('time', 'n/a')} | {e['source']} | {e['title']}"
        for e in latest_items
    ]

    lines = [
        "# Daily World Brief",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- total_events: {len(payload['events'])}",
        "",
        "## Categories",
        *top_lines,
        "",
        "## Latest 15",
        *latest_lines,
        "",
        "## Notes",
        "- This report is rule-based, not an LLM summary.",
        "- It runs fully free on GitHub Actions + static hosting.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_events: list[dict[str, Any]] = []
    errors: list[str] = []

    for name, fn in (
        ("USGS", fetch_usgs),
        ("NASA EONET", fetch_eonet),
        ("ReliefWeb", fetch_reliefweb),
    ):
        try:
            all_events.extend(fn())
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    generated_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "generated_at": generated_at,
        "event_count": len(all_events),
        "errors": errors,
        "sources": [
            {"name": "USGS", "url": "https://earthquake.usgs.gov/"},
            {"name": "NASA EONET", "url": "https://eonet.gsfc.nasa.gov/"},
            {"name": "ReliefWeb API", "url": "https://api.reliefweb.int/"},
        ],
        "events": all_events,
        "build": {"version": "0.1.0", "duration_ms": int(time.time() * 1000)},
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_brief(payload), encoding="utf-8")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    if errors:
        print("errors:")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
