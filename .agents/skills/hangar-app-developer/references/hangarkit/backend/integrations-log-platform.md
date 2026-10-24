# Log Platform integration

ID: `backend.integration.log_platform`
Category: `backend`

Search live and nonlive Log Platform logs from backend code by CMDB/query, trace id, or copied Log Platform URL.

## Import

`from hangarkit.integrations import log_platform`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `log_platform.search(...), async_search(...)`
- `log_platform.search_live(...), search_nonlive(...)`
- `log_platform.async_search_live(...), async_search_nonlive(...)`
- `log_platform.request(environment="live", method="POST", path="/openapi/v3/search", **kwargs)`
- `log_platform.async_request(...)`

## Details

Use this module for Log Platform searches from backend code. It supports sync and async helpers, optional copied Log Platform URLs, `timeout` for upstream requests, and `wait_timeout` for how long the helper waits before returning a resumable `state_id`.

Configuration is app-scoped under `settings.integrations.log_platform`. Use `{ "auth_mode": "user" }` to search with the current app user's linked Log Platform account, or `{ "auth_mode": "app", "app_provider": "owner_token" }` to search with the app owner's linked Log Platform account through Wingman.

When `env` or `region` is provided, HangarKit appends them to `query` as `@env=<env>` and `@cid=<region>` unless those filters are already present.

Search input schema:

```python
{
    "environment": "live" | "nonlive",     # optional; defaults to "live"; can be inferred from logplatform_url
    "cmdbs": list[str] | str | None,       # required unless trace or continue_state_id is provided
    "query": str | None,                   # required unless trace or continue_state_id is provided
    "trace": str | None,                   # optional 32-character trace id
    "env": str | None,                     # optional PQL @env filter, e.g. "live", "staging"; appended to query
    "region": str | None,                  # optional PQL @cid filter, e.g. "sg"; appended to query
    "start_time": str | int | None,        # RFC3339 or Unix milliseconds; defaults to one hour ago
    "end_time": str | int | None,          # RFC3339 or Unix milliseconds; defaults to now
    "limit": int,                          # optional; defaults to 1; minimum 1
    "return_logplatform_url": bool,        # optional; returns a view URL when true
    "logplatform_url": str | None,         # optional copied Log Platform URL; extracts cmdbs/query/time/environment
    "continue_state_id": str | None,       # optional id returned by a previous partial search
    "timeout": int | float | dict | None,  # upstream HTTP timeout; dict may include total/read/connect
    "wait_timeout": int | float,           # seconds to wait before returning partial state; defaults to 50
    "domain": str | None,                  # optional Log Platform domain override; normally omit
}
```

Search output schema:

```python
{
    "logs": list[dict],
    "errors": list[str] | None,
    "logplatform_url": str | None,
    "state_id": str | None,  # present when wait_timeout elapsed before the search finished
}
```

Each item in `logs` is the raw Log Platform log object returned by upstream. The exact fields are provider-defined and can vary by CMDB, query type, and endpoint. HangarKit preserves the object as-is and only treats these id fields specially for deduplication:

```python
{
    "id": str | int,   # optional
    "_id": str | int,  # optional
    "@id": str | int,  # optional
    "...": object,     # all other upstream log fields are passed through unchanged
}
```

Common fields observed from live `/openapi/v3/search` SSE events include:

```python
{
    "@id": str,
    "@timestamp": str | int,
    "@message": str,
    "@service": str,
    "@env": str,
    "@cid": str,
    "@host": str,
    "@severity": str,
    "@trace_id": str,
    "@source": str,
    "@category": str,
    "@az": str,
    "@idc": str,
    "@sequence": str | int,
    "_message_base64_encoded_": bool | str,
    "pod_name": str,
    "...": object,
}
```

Streaming search responses from `/openapi/v3/search` are SSE `data:` events. Each event is normally one log object. If an event has both `status` and `message`, HangarKit treats it as an upstream error and appends `"Error {status}: {message}"` to `errors`.

Trace search uses two upstream response shapes:

```python
# POST /openapi/v2/trace/jobs
{
    "id": str,  # trace job id
    "...": object,
}

# GET /openapi/v2/search/jobs/{job_id}
{
    "entries": list[dict],    # preferred when present
    "logs": list[dict],
    "results": list[dict],
    "items": list[dict],
    "hits": list[dict],
    "data": list[dict] | {"logs": list[dict]},
    "total_size": int | None,
    "status": str | None,
    "state": str | None,
    "job_status": str | None,
    "code": int | None,
    "message": str | None,
}
```

`logplatform_url` parsing extracts:

```python
{
    "cmdbs": "selected-applications",
    "query": "pipeline-search-input",
    "start_time": "date-time.start",
    "end_time": "date-time.end",
    "environment": "live" | "nonlive",
}
```

Raw request schema:

```python
log_platform.request(
    environment="live" | "nonlive",
    method="GET" | "POST" | "PUT" | "PATCH" | "DELETE",
    path="/openapi/v3/search",
    params=dict | None,
    json=dict | list | None,
    data=str | bytes | None,
    headers=dict | None,
    timeout=int | float | dict | None,
    domain=str | None,
)
```
## Quick examples

- `logs = log_platform.search_live(cmdbs=["order-service"], query="error AND @env=live AND @cid=sg", limit=20, timeout=60)`
- `logs = await log_platform.async_search(logplatform_url=shared_url, limit=20, wait_timeout=30)`

## Related capabilities

- `backend.integrations`
