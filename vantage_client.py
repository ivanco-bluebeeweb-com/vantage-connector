"""Thin HTTP client for Vantage Cost Management API.

Static Bearer API access token -- no OAuth, no token refresh at all. Same
"fail()-dict + ClientFail exception" shape as every other connector this
session's *_client.py.
"""
from __future__ import annotations

from typing import Any

import httpx

API_BASE = "https://api.vantage.sh/v2"

VANTAGE_NOT_CONNECTED = "VANTAGE_NOT_CONNECTED"
VANTAGE_UNAUTHORIZED = "VANTAGE_UNAUTHORIZED"
VANTAGE_FORBIDDEN_SCOPE = "VANTAGE_FORBIDDEN_SCOPE"
VANTAGE_NOT_FOUND = "VANTAGE_NOT_FOUND"
VANTAGE_RATE_LIMITED = "VANTAGE_RATE_LIMITED"
VANTAGE_BACKEND_ERROR = "VANTAGE_BACKEND_ERROR"
VANTAGE_VALIDATION_FAILED = "VANTAGE_VALIDATION_FAILED"

_MESSAGES = {
    VANTAGE_NOT_CONNECTED: "No Vantage connection found. Connect Vantage first.",
    VANTAGE_UNAUTHORIZED: "Vantage rejected the API token as invalid.",
    VANTAGE_FORBIDDEN_SCOPE: "Vantage rejected this request -- the connected token is Read-only and this needs Read/Write scope.",
    VANTAGE_NOT_FOUND: "That Vantage record was not found.",
    VANTAGE_RATE_LIMITED: "Vantage rate-limited this request. Try again shortly.",
    VANTAGE_BACKEND_ERROR: "Vantage's API returned an error.",
    VANTAGE_VALIDATION_FAILED: "Vantage rejected the request as invalid.",
}


class ClientFail(Exception):
    def __init__(self, payload: dict):
        self.payload = payload
        super().__init__(payload.get("message", "Vantage request failed"))


def fail(code: str, detail: str = "") -> dict:
    msg = _MESSAGES.get(code, "Vantage request failed.")
    if detail:
        msg = f"{msg} ({detail})"
    return {"ok": False, "code": code, "message": msg}


async def verify_token(api_token: str) -> dict:
    """Verify a token works by calling a harmless read endpoint."""
    if not api_token:
        return fail(VANTAGE_VALIDATION_FAILED, "api_token is required")
    headers = {"Authorization": f"Bearer {api_token}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(f"{API_BASE}/folders", headers=headers, params={"limit": 1})
        except httpx.RequestError as e:
            return fail(VANTAGE_BACKEND_ERROR, str(e))
    if resp.status_code == 401:
        return fail(VANTAGE_UNAUTHORIZED)
    if resp.status_code >= 400:
        return fail(VANTAGE_BACKEND_ERROR, f"HTTP {resp.status_code}")
    return {"ok": True}


def _check_status(resp: httpx.Response, action: str) -> Any:
    if resp.status_code == 401:
        raise ClientFail(fail(VANTAGE_UNAUTHORIZED, action))
    if resp.status_code == 403:
        raise ClientFail(fail(VANTAGE_FORBIDDEN_SCOPE, action))
    if resp.status_code == 404:
        raise ClientFail(fail(VANTAGE_NOT_FOUND, action))
    if resp.status_code == 429:
        raise ClientFail(fail(VANTAGE_RATE_LIMITED, action))
    if resp.status_code >= 400:
        raise ClientFail(fail(VANTAGE_BACKEND_ERROR, f"HTTP {resp.status_code} on {action}"))
    if not resp.content:
        return {}
    try:
        return resp.json()
    except ValueError:
        raise ClientFail(fail(VANTAGE_BACKEND_ERROR, f"non-JSON response on {action}"))


async def request(ctx, conn: dict, method: str, path: str, *, params: dict | None = None,
                   json_body: dict | None = None, action: str = "call Vantage") -> Any:
    headers = {"Authorization": f"Bearer {conn.get('api_token', '')}"}
    url = f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(method, url, headers=headers, params=params, json=json_body)
        except httpx.RequestError as e:
            raise ClientFail(fail(VANTAGE_BACKEND_ERROR, str(e)))
    return _check_status(resp, action)


def known_entities() -> list[str]:
    return ["cost_reports", "folders", "dashboards", "resource_reports", "budgets", "providers", "virtual_tag_configs"]


def entity_path(entity: str, record_id: str = "") -> str:
    if record_id:
        return f"/{entity}/{record_id}"
    return f"/{entity}"
