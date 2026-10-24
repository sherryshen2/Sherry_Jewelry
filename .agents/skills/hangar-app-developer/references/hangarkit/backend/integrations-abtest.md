# ABTest integration

ID: `backend.integration.abtest`
Category: `backend`

Call AB Test Platform MCP tools through Wingman ABTest proxy from backend code.

## Import

`from hangarkit.integrations import abtest`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `abtest.client()`
- `abtest.call_tool(tool, arguments=None, timeout=60, parse_text_json=True)`
- `abtest.get_exp_by_id(exp_id, **kwargs)`
- `abtest.list_tools(timeout=30)`
- `abtest.live_tool_schemas(timeout=30)`
- `abtest.tool_schema(tool, live=False), abtest.tool_schemas(live=False)`
- `abtest.raw_mcp(payload, session_id=None, timeout=30)`
- `abtest.initialize(timeout=30)`

## Details

Use this module for AB Test Platform calls through Wingman's ABTest proxy. HangarKit does not connect to ABTest MCP directly. The runtime calls Wingman, and Wingman forwards the app/user ABTest token while injecting the platform MGW credential from Wingman BE config.

Configure ABTest like other user/app integrations:

```json
{ "integrations": { "abtest": { "auth_mode": "user" } } }
```

For app-level access through the app owner's linked ABTest account, use:

```json
{ "integrations": { "abtest": { "auth_mode": "app", "app_provider": "owner_token" } } }
```

For a fixed app credential, store only the ABTest token in `credential`:

```json
{
  "integrations": {
    "abtest": {
      "auth_mode": "app",
      "app_provider": "service_token",
      "credential": "{\"abtest_token\":\"Bearer ...\"}"
    }
  }
}
```

The credential may also be pasted as a raw JWT token or as header lines:

```txt
x-abtest-token: Bearer ...
```

Prefer `call_tool()` or named helpers for normal app code. Use `list_tools()` or `live_tool_schemas()` when the app needs the exact current MCP tool list and JSON input schemas. Live schema discovery requires a valid linked/configured ABTest token, and Wingman BE must have `abtest_config.mgw_agent_auth_token` configured.

## Known Static Schema

Static schemas are intentionally small and only include tools confirmed from the ABTest onboarding docs. Use `live_tool_schemas()` for the full current set.

### `get_exp_by_id`

Get ABTest experiment detail by experiment ID.

Required: `exp_id`

| Parameter | Type | Notes |
|---|---|---|
| `exp_id` | `integer` | ABTest experiment ID, e.g. `995`. |

Example:

```python
from hangarkit.integrations import abtest

exp = abtest.get_exp_by_id(995)
```

Dynamic tool call:

```python
result = abtest.call_tool("get_exp_by_id", {"exp_id": 995})
```

Live schema discovery:

```python
schemas = abtest.live_tool_schemas()
get_exp_schema = schemas.get("get_exp_by_id")
```
## Quick examples

- `exp = abtest.get_exp_by_id(995)`
- `schema = abtest.tool_schema("get_exp_by_id")`
- `live_schemas = abtest.live_tool_schemas()`

## Related capabilities

- `backend.integrations`
- `backend.integration.platform`
