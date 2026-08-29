"""Pydantic params/result models for Vantage Connector.

All params models are module-scope (V17 federal invariant, same rule as
every other connector this session's schemas.py).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class NoParams(BaseModel):
    """Explicit empty params model -- V17 disallows untyped handlers."""
    pass


class ConnectionScoped(BaseModel):
    connection_id: str = Field(
        "",
        description="Which connected Vantage account to use (see list_connections). Omit if only one is connected.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Connection -- static Bearer API access token, no OAuth
# ──────────────────────────────────────────────────────────────────────────


class ConnectVantageParams(BaseModel):
    api_token: str = Field("", description="Your Vantage API access token (Read or Read/Write scope, from the Vantage console).")
    label: str = Field("", description="Optional friendly label for this connection, e.g. 'Acme Inc Vantage'.")


class ProviderConnection(BaseModel):
    id: str = ""
    label: str = ""


class ProviderConnectionList(BaseModel):
    connections: list[ProviderConnection] = Field(default_factory=list)


class DisconnectVantageParams(BaseModel):
    connection_id: str = Field(description="Which connection to disconnect (see list_connections).")


class DeleteResult(BaseModel):
    deleted: bool = False
    id: str = ""


# ──────────────────────────────────────────────────────────────────────────
# Generic entity layer
# ──────────────────────────────────────────────────────────────────────────


class ListEntitiesParams(ConnectionScoped):
    entity: str = Field(description="Resource type: cost_reports, folders, dashboards, resource_reports, budgets, providers, virtual_tag_configs.")
    filter_expr: str = Field("", description="Optional query-string filter supported by the resource (e.g. 'folder_token=...').")
    limit: int = Field(50, ge=1, le=200, description="Maximum records to return.")


class EntityList(BaseModel):
    entity: str = ""
    count: int = 0
    records: list[dict] = Field(default_factory=list)


class GetEntityParams(ConnectionScoped):
    entity: str = Field(description="Resource type, same values as list_entities.")
    record_id: str = Field(description="The record's Vantage token/id.")


class EntityDetail(BaseModel):
    entity: str = ""
    record: dict = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────
# Writes
# ──────────────────────────────────────────────────────────────────────────


class CreateCostReportParams(ConnectionScoped):
    title: str = Field(description="Name for the new cost report.")
    filter_vql: str = Field(description="Vantage Query Language (VQL) filter expression, e.g. 'costs.provider = \\'aws\\''.")
    folder_token: str = Field("", description="Optional folder token to place this report in.")


class CreateFolderParams(ConnectionScoped):
    title: str = Field(description="Name for the new folder.")


class CreateBudgetParams(ConnectionScoped):
    name: str = Field(description="Name for the new budget.")
    amount: float = Field(description="Budget amount (in the report's currency).")
    period_type: str = Field("monthly", description="Budget period: monthly, quarterly, or yearly.")
    filter_vql: str = Field("", description="Optional VQL filter to scope the budget to specific costs.")


class WriteResult(BaseModel):
    ok: bool = False
    record_id: str = ""


# ──────────────────────────────────────────────────────────────────────────
# Value-add reports
# ──────────────────────────────────────────────────────────────────────────


class GetSpendOverviewParams(ConnectionScoped):
    limit: int = Field(50, ge=1, le=200, description="Number of recent cost reports to scan for the overview.")


class SpendOverviewReport(BaseModel):
    report_count: int = 0
    by_provider: dict[str, float] = Field(default_factory=dict)


class GetBudgetAlertsReportParams(ConnectionScoped):
    limit: int = Field(50, ge=1, le=200, description="Number of budgets to scan.")


class BudgetAlertsReport(BaseModel):
    budget_count: int = 0
    over_budget: list[dict] = Field(default_factory=list)
