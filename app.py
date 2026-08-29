"""Extension declaration, secrets, lifecycle hooks.

WHY BYOK, same reasoning as every other connector here -- the user's own
multi-cloud billing data (AWS/Azure/GCP/Kubernetes/Datadog/Snowflake/
MongoDB spend) is already aggregated inside THEIR OWN Vantage account.

WHY A STATIC BEARER API TOKEN (confirmed against docs.vantage.sh/api/
authentication, 2026-08-29): Vantage issues a Read or Read/Write scoped
API access token from its own console, passed as a Bearer token, with
no expiry or refresh to manage -- same simplicity class as Expensify/Brex.

WHY VQL IS A RAW STRING PARAM, NOT A DSL BUILDER: Vantage's own cost
query language (VQL) is how their quickstart teaches cost-report
creation -- exposing it as a raw filter string keeps this connector
aligned with how Vantage users already think about queries, rather than
inventing a parallel query builder that would drift from Vantage's own
docs.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "vantage-connector",
    version="0.1.0",
    display_name="Vantage",
    icon="icon.svg",
    capabilities=["vantage:read", "vantage:write"],
    description=(
        "Connect your own Vantage Cost Management account (bring your own Read/Write-scoped API access token "
        "from the Vantage console) to read cost reports, folders, dashboards, resource reports, budgets, and "
        "cloud providers, plus value-add spend overview and budget-alert reports. Cost report, folder, and "
        "budget creation are supported using Vantage's own VQL query language."
    ),
)

chat = ChatExtension(ext)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether a Vantage API-token connection is configured."""
    raw = await ctx.secrets.get("vantage_connections")
    return {
        "healthy": bool(raw),
        "detail": (
            "Vantage connection configured."
            if raw
            else "Not connected yet — run connect_vantage."
        ),
    }
