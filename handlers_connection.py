"""Connection management for Vantage Connector: connect/disconnect/list.

Static Bearer API access token -- verified synchronously against a
harmless read endpoint at connect time. No refresh logic needed (no
expiry).
"""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import vantage_client as vc
from app import chat
from schemas import (
    NoParams,
    ConnectVantageParams,
    ProviderConnection, ProviderConnectionList,
    DisconnectVantageParams, DeleteResult,
)

_SECRET_NAME = "vantage_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


async def resolve_connection(ctx, connection_id: str = "") -> dict | None:
    connections = await _load_connections(ctx)
    if not connections:
        return None
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        return None
    return connections[0]


async def resolve_or_error(ctx, connection_id: str = ""):
    conn = await resolve_connection(ctx, connection_id)
    if not conn:
        return None, ActionResult.error(
            "No Vantage connection found. Connect Vantage first.",
            code="VANTAGE_NOT_CONNECTED",
        )
    return conn, None


@chat.function(
    "connect_vantage",
    "Connect your own Vantage Cost Management account by saving your API access token (Read or Read/Write "
    "scope, from the Vantage console), after checking it actually works.",
    action_type="write", chain_callable=True, data_model=ProviderConnection,
    event="vantage-connector.connect_vantage", effects=["create:connection"],
)
async def connect_vantage(ctx, params: ConnectVantageParams) -> ActionResult:
    """Verify the API token works and save the connection."""
    if not params.api_token:
        return ActionResult.error(
            "api_token is required.",
            code="VANTAGE_VALIDATION_FAILED",
        )
    result = await vc.verify_token(params.api_token)
    if not result.get("ok"):
        return ActionResult.error(result.get("message", "Could not verify the Vantage API token."),
                                   code=result.get("code", "VANTAGE_UNAUTHORIZED"))
    connections = await _load_connections(ctx)
    conn_id = str(uuid.uuid4())
    connections.append({
        "id": conn_id,
        "label": params.label or "Vantage",
        "api_token": params.api_token,
    })
    await _save_connections(ctx, connections)
    return ActionResult.success(ProviderConnection(id=conn_id, label=params.label or "Vantage")), summary="Vantage connected."


@chat.function(
    "list_connections",
    "List the connected Vantage accounts.",
    action_type="read", chain_callable=True, data_model=ProviderConnectionList,
)
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """List saved Vantage connections."""
    connections = await _load_connections(ctx)
    return ActionResult.success(ProviderConnectionList(
        connections=[ProviderConnection(id=c["id"], label=c.get("label", "Vantage")) for c in connections]
    )), summary="Connections listed."


@chat.function(
    "disconnect_vantage",
    "Disconnect a Vantage account: deletes the saved API access token. Nothing in Vantage itself is changed.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="vantage-connector.disconnect_vantage", effects=["delete:connection"],
)
async def disconnect_vantage(ctx, params: DisconnectVantageParams) -> ActionResult:
    """Disconnect a Vantage account: deletes the saved connection."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error("Connection not found.", code="VANTAGE_NOT_CONNECTED")
    await _save_connections(ctx, remaining)
    return ActionResult.success(DeleteResult(deleted=True, id=params.connection_id)), summary="Vantage disconnected."
