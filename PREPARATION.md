# Vantage Connector -- Preparation (v0.1)

## API surface
Vantage Cost Management API (api.vantage.sh, v2) -- REST/JSON, resources:
costs, cost reports, folders, dashboards, resource_reports, budgets,
providers, virtual tag configs. Confirmed via docs.vantage.sh/api
(2026-08-29).

## Auth model
Static **Bearer API access token** (Read/Write scopes) -- confirmed via
docs.vantage.sh/api/authentication + apis.io/security. Token is generated
in the Vantage console with a chosen scope (Read or Read/Write), passed as
`Authorization: Bearer <TOKEN>`. No expiry, no refresh -- simplest auth
class alongside Expensify/Brex.

## Why BYOK
Same reasoning as every other connector here -- the user's own multi-cloud
billing data (AWS/Azure/GCP/Kubernetes/Datadog/Snowflake/MongoDB spend) is
already aggregated inside THEIR OWN Vantage account. The API token is
generated per Vantage account/team from their own console.

## Scope for v1
Read-heavy: cost reports, folders, dashboards, resource reports, budgets,
providers, virtual tag configs. Write: create cost report (VQL query),
create folder, create budget. Vantage's cost query language (VQL) is
exposed as a raw filter string param rather than a full DSL builder --
users/agents pass VQL expressions directly, matching how Vantage's own
quickstart teaches it.

## Rate limits / known constraints
Standard REST pagination (cursor-based). Read vs Read/Write token scope
is enforced by Vantage itself -- a Read-only token will get 403 on any
write call, surfaced as VANTAGE_FORBIDDEN_SCOPE, same shape as Ramp's
scope-based 403 handling.
