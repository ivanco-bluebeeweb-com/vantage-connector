"""Generic entity layer + explicit writes for Vantage Connector.

list_entities/get_entity cover the bulk read surface (cost_reports,
folders, dashboards, resource_reports, budgets, providers,
virtual_tag_configs). Writes are explicit, narrow chat functions because
Vantage's write surface (create report/folder/budget) is small and each
creates a real, named object in the user's Vantage account.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import vantage_client as vc
from app import chat
from handlers_connection import resolve_or_error
from schemas import (
    ListEntitiesParams, EntityList,
    GetEntityParams, EntityDetail,
    CreateCostReportParams, CreateFolderParams, CreateBudgetParams, WriteResult,
)


@chat.function(
    "list_entities",
    "List Vantage records of any resource type (cost_reports, folders, dashboards, resource_reports, budgets, "
    "providers, virtual_tag_configs) in the connected Vantage account.",
    action_type="read", chain_callable=True, data_model=EntityList,
)
async def list_entities(ctx, params: ListEntitiesParams) -> ActionResult:
    """List Vantage records of any resource type."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    if params.entity not in vc.known_entities():
        return ActionResult.error(
            f"Unknown entity '{params.entity}'. Known: {', '.join(vc.known_entities())}",
            code="VANTAGE_VALIDATION_FAILED",
        )
    query = {"limit": params.limit}
    if params.filter_expr:
        for pair in params.filter_expr.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                query[k] = v
    data = await vc.request(ctx, conn, "GET", vc.entity_path(params.entity), params=query, action=f"list {params.entity}")
    records = data.get(params.entity, data.get("items", [])) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    return ActionResult.ok(EntityList(entity=params.entity, count=len(records), records=records))


@chat.function(
    "get_entity",
    "Read one Vantage record of any resource type in full by its token/id.",
    action_type="read", chain_callable=True, data_model=EntityDetail,
)
async def get_entity(ctx, params: GetEntityParams) -> ActionResult:
    """Read one Vantage record by id."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    if params.entity not in vc.known_entities():
        return ActionResult.error(
            f"Unknown entity '{params.entity}'. Known: {', '.join(vc.known_entities())}",
            code="VANTAGE_VALIDATION_FAILED",
        )
    data = await vc.request(ctx, conn, "GET", vc.entity_path(params.entity, params.record_id), action=f"get {params.entity}")
    return ActionResult.ok(EntityDetail(entity=params.entity, record=data if isinstance(data, dict) else {}))


@chat.function(
    "create_cost_report",
    "Create a new Vantage cost report from a VQL (Vantage Query Language) filter expression -- e.g. all AWS "
    "spend, or spend for a specific team/tag.",
    action_type="write", chain_callable=True, data_model=WriteResult,
    event="vantage-cost-report-created", effects=["create:resource"],
)
async def create_cost_report(ctx, params: CreateCostReportParams) -> ActionResult:
    """Create a new cost report."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    payload = {"title": params.title, "filter": params.filter_vql}
    if params.folder_token:
        payload["folder_token"] = params.folder_token
    data = await vc.request(ctx, conn, "POST", "/cost_reports", json_body=payload, action="create cost report")
    return ActionResult.ok(WriteResult(ok=True, record_id=(data or {}).get("token", "")))


@chat.function(
    "create_folder",
    "Create a new Vantage folder -- a container used to organize cost reports and dashboards.",
    action_type="write", chain_callable=True, data_model=WriteResult,
    event="vantage-folder-created", effects=["create:resource"],
)
async def create_folder(ctx, params: CreateFolderParams) -> ActionResult:
    """Create a new folder."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await vc.request(ctx, conn, "POST", "/folders", json_body={"title": params.title}, action="create folder")
    return ActionResult.ok(WriteResult(ok=True, record_id=(data or {}).get("token", "")))


@chat.function(
    "create_budget",
    "Create a new Vantage budget with a target amount and period, optionally scoped to specific costs via a "
    "VQL filter.",
    action_type="write", chain_callable=True, data_model=WriteResult,
    event="vantage-budget-created", effects=["create:resource"],
)
async def create_budget(ctx, params: CreateBudgetParams) -> ActionResult:
    """Create a new budget."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    payload = {"name": params.name, "amount": str(params.amount), "period": {"period_type": params.period_type}}
    if params.filter_vql:
        payload["filter"] = params.filter_vql
    data = await vc.request(ctx, conn, "POST", "/budgets", json_body=payload, action="create budget")
    return ActionResult.ok(WriteResult(ok=True, record_id=(data or {}).get("token", "")))
