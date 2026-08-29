"""Panel UI -- connections list/connect form + the one required "App
settings" entry point, same shape as every other connector this
session's panels.py.

SIDEBAR CONTENT -- NO CARDS ANYWHERE, per ~/UI_INTERFACE_STANDARD.md's
"left sidebar, no decorated cards" rule. Disconnect lives only in the
"App settings" screen (panels_settings.py). The one secondary "App
settings" button is always the LAST element at the bottom of the sidebar.

PER ~/UI_INTERFACE_STANDARD.md (2026-08-21 addendum): every Input carries
its own visible label (a ui.Text wrapping the ui.Input in a Stack -- ui.Input
itself does not accept label=), the placeholder text is always contextually
specific. The "How do I set this up?" instructions live ONLY in the help
overlay below -- never duplicated as static sidebar text.

KNOWN UI COMPONENT PITFALLS (learned building Ramp/Brex Connectors,
2026-08-29): ui.Form does NOT take a separate ui.Button(submit=True)
child -- use submit_label="..." on ui.Form itself. ui.Input does NOT
accept secret=True -- use ui.Password(param_name=..., placeholder=...)
instead. ui.Stack does NOT accept full_width=True -- only ui.Button does.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers_connection as h


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="settings", on_click=ui.Call("__panel__vantage_settings"),
    )


def _connection_row(c: dict) -> ui.UINode:
    label = c.get("label") or "Vantage connection"
    return ui.Stack(direction="v", gap=1, children=[
        ui.Text(label, variant="body"),
        ui.Text("Connected", variant="caption"),
    ])


def _connections_section(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Text("No Vantage accounts connected yet.", variant="caption")
    children: list[ui.UINode] = []
    for i, c in enumerate(connections):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, children=children)


def _connect_section() -> ui.UINode:
    return ui.Stack(direction="v", gap=2, children=[
        ui.Text("Connect Vantage", variant="heading"),
        ui.Form(
            action="connect_vantage",
            submit_label="Connect Vantage",
            children=[
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Label (optional)", variant="label"),
                    ui.Input(param_name="label", placeholder="e.g. Acme Inc Vantage"),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("API access token", variant="label"),
                    ui.Password(param_name="api_token", placeholder="Read or Read/Write token from the Vantage console"),
                ]),
            ],
        ),
        ui.Button(
            "How do I set this up?", variant="ghost", size="sm", full_width=True,
            on_click=ui.Call("__panel__vantage_connect_help"),
        ),
    ])


@ext.panel("vantage_connect", slot="left", title="Vantage")
async def vantage_connect(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    return ui.Stack(direction="v", gap=3, children=[
        _connections_section(connections),
        ui.Divider(),
        _connect_section(),
        _settings_button(),
    ])


@ext.panel("vantage_connect_help", slot="overlay", title="How do I set this up?")
async def vantage_connect_help(ctx, **kwargs) -> object:
    return ui.Stack(direction="v", gap=2, children=[
        ui.Text(
            "1. Log in to app.vantage.sh and go to Settings > Access Tokens.\n"
            "2. Create a new token -- choose Read scope for reporting only, or Read/Write if you also want "
            "Webbee to create cost reports, folders, or budgets.\n"
            "3. Paste the token above and click Connect Vantage.",
            variant="body",
        ),
    ])
