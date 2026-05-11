"""
Cooldown store backed by Vercel KV (Upstash Redis REST API).
Falls back to in-memory dict when KV env vars are absent (local testing).
"""
import os
import requests

_url   = os.getenv("KV_REST_API_URL", "")
_token = os.getenv("KV_REST_API_TOKEN", "")

# local fallback when running without KV
_local: dict = {}


def _cmd(*args):
    if not _url:
        return None
    try:
        r = requests.post(
            _url,
            headers={"Authorization": f"Bearer {_token}"},
            json=list(args),
            timeout=5,
        )
        return r.json().get("result") if r.ok else None
    except Exception:
        return None


def is_cooldown(symbol: str, direction: str) -> bool:
    key = f"cooldown:{symbol}:{direction}"
    if _url:
        return _cmd("EXISTS", key) == 1
    return key in _local


def set_cooldown(symbol: str, direction: str, hours: int = None) -> None:
    from lib.config import COOLDOWN_HOURS
    hours = hours or COOLDOWN_HOURS
    key = f"cooldown:{symbol}:{direction}"
    if _url:
        _cmd("SET", key, "1", "EX", str(hours * 3600))
    else:
        _local[key] = True
