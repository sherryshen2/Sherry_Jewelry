# POP Feature Requests

Use this reference when a Hangar app needs POP Feature Request (`SPCPM-*`) data. Read [the POP integration capability page](hangarkit/backend/integrations-pop.md) first for auth modes, helper signatures, and live schema discovery.

## Read workflow

Use `hangarkit.integrations.pop`; do not connect an app directly to POP MCP. HangarKit routes through Wingman, which owns the POP credentials, MCP lifecycle, and MGW authentication.

```python
from hangarkit.integrations import pop

search = pop.feature_request_search(
    request_name="checkout",
    target_countries=["SG"],
    page_num=1,
    page_size=20,
)
detail = pop.feature_request_detail_get(request_key="SPCPM-123456")
history = pop.feature_request_audit_log_list(request_key="SPCPM-123456", page_num=1, page_size=20)
comments = pop.feature_request_get_comments(request_key="SPCPM-123456")
```

Start with `feature_request_search` to find a request key. Use `feature_request_detail_get` for the full request, `feature_request_audit_log_list` for field history, and `feature_request_get_comments` for discussion. Strip HTML before presenting comment bodies.

Use `pop.tool_schema("feature_request_search")` before relying on newly added or changed filters. Prefer the named helpers; reserve `pop.call_tool()` for tools without a helper and `pop.raw_mcp()` for advanced debugging only.

## Search filters

Use these reliable filters when applicable:

```python
pop.feature_request_search(
    request_keys=["SPCPM-123456"],
    request_name="keyword",
    target_countries=["SG"],
    main_product_lines=["Checkout"],
    supporting_product_lines=["PDP"],
    classifications=["Supply Chain"],
    current_assignee="user@shopee.com",
    original_priorities=["P1"],
    submission_types=["Urgent"],
    ba_statuses=["Approved"],
    request_submission_cycle=["Cycle 19"],
    submission_date_start="2026-07-01",
    submission_date_end="2026-07-31",
)
```

Post-filter locally rather than trusting these server-side filters alone: `request_statuses`, `reviewer_priorities`, `business_line`, and `market_specific_request`.

## Response shape

Named HangarKit helpers unwrap the MCP text response when it is JSON. Normal search results are therefore usually a dictionary with `requests`, `page_num`, `page_size`, and `total`, rather than the outer JSON-RPC envelope.

Handle both normalized and raw MCP shapes at integration boundaries:

```python
def feature_request_items(value):
    if not isinstance(value, dict):
        return []
    structured = value.get("result", {}).get("structuredContent")
    payload = structured if isinstance(structured, dict) else value
    return payload.get("requests") if isinstance(payload.get("requests"), list) else []
```

Do not treat an MCP HTTP 200 as a successful tool call by itself. Check a raw response's `result.isError`, or catch `PopError` from HangarKit helpers.

## Submission cycles

Use `request_submission_cycle=["Cycle N"]` to filter Feature Requests by their assigned submission cycle. The expected returned field is `submission_cycle`.

Current limitation observed through the Wingman POP proxy on 2026-07-24: `feature_request_search` and `feature_request_detail_get` returned no `submission_cycle` field, and the `feature://field-options` resource returned an empty field list. Do not infer an individual request's assigned cycle when that field is absent; surface it as unavailable.

For the calendar submission cycle only, the POP skill fallback mapping defines January 2025 as Cycle 1 through December 2026 as Cycle 24:

```python
from datetime import date

def calendar_submission_cycle(today=None):
    today = today or date.today()
    cycle = (today.year - 2025) * 12 + today.month
    return cycle if 1 <= cycle <= 24 else None
```

This computes the calendar cycle, not a request's assigned cycle. Refresh the mapping from POP when a later cycle range is published.

## Mutations

POP Feature Request write tools include create, general-info update, reviewer reassignment, regional-approval update, ETA update, re-review, watchers, PRD subscribers, comments, product-line updates, market opt-in/out updates, Epic management, and Key Project links.

Before every write:

1. Read the target request and current state.
2. Resolve valid enum labels with the live schema or POP field options.
3. Show the user the exact target and fields that will change.
4. Obtain explicit confirmation.

Never call POP write tools merely to explore available values or infer a submission cycle.
