"""Value-add reports for Vantage Connector -- spend overview by provider
and budget alerts, same "aggregate raw records into one glance" shape as
every other connector's handlers_reports.py this session.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import vantage_client as vc
from app import chat
from handlers_connection import resolve_or_error
from schemas import (
    GetSpendOverviewParams, SpendOverviewReport,
    GetBudgetAlertsReportParams, BudgetAlertsReport,
)


@chat.function(
    "get_spend_overview_report",
    "Value-add report: summarize recent Vantage cost reports by cloud provider -- total spend per provider.",
    action_type="read", chain_callable=True, data_model=SpendOverviewReport,
)
async def get_spend_overview_report(ctx, params: GetSpendOverviewParams) -> ActionResult:
    """Scan recent cost reports and bucket spend by provider."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await vc.request(ctx, conn, "GET", "/cost_reports", params={"limit": params.limit}, action="list cost reports for spend overview")
    rows = data.get("cost_reports", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    by_provider: dict[str, float] = {}
    for r in rows:
        provider = r.get("provider") or "unknown"
        total = r.get("total_costs_amount") or r.get("total_cost") or 0
        try:
            by_provider[provider] = by_provider.get(provider, 0.0) + float(total)
        except (TypeError, ValueError):
            continue
    return ActionResult.success(SpendOverviewReport(
        report_count=len(rows),
        by_provider={k: round(v, 2) for k, v in by_provider.items()},
    ), summary="Spend overview report retrieved.")


@chat.function(
    "get_budget_alerts_report",
    "Value-add report: scan Vantage budgets and flag every one that is currently over its target amount.",
    action_type="read", chain_callable=True, data_model=BudgetAlertsReport,
)
async def get_budget_alerts_report(ctx, params: GetBudgetAlertsReportParams) -> ActionResult:
    """Scan budgets and flag over-budget ones."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await vc.request(ctx, conn, "GET", "/budgets", params={"limit": params.limit}, action="list budgets for alert scan")
    rows = data.get("budgets", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    over_budget = []
    for b in rows:
        amount = float(b.get("amount") or 0)
        actual = float(b.get("actual_amount") or b.get("actual_spend") or 0)
        if amount and actual > amount:
            over_budget.append({
                "name": b.get("name", ""),
                "token": b.get("token", ""),
                "amount": amount,
                "actual_amount": actual,
            })
    return ActionResult.success(BudgetAlertsReport(budget_count=len(rows), over_budget=over_budget), summary="Budget alerts report retrieved.")
