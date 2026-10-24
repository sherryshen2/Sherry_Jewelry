from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from hangarkit import ctx
from importlib import import_module

router = APIRouter()


def _integration(provider: str):
    integrations = import_module("hangarkit.integrations")
    try:
        return getattr(integrations, provider)
    except AttributeError:
        return import_module(f"hangarkit.integrations.{provider}")


PROVIDERS = [
    {
        "id": "jira",
        "label": "Jira",
        "description": "Search and inspect Jira issues through the configured Jira integration.",
        "actions": [
            {
                "id": "search_my_open_issues",
                "label": "Search my open issues",
                "description": "Returns open issues assigned to the current integration user.",
                "fields": [
                    {"id": "project", "label": "Project key", "placeholder": "Optional project key"},
                    {"id": "limit", "label": "Limit", "type": "number", "default": "10"},
                ],
            },
            {
                "id": "get_issue",
                "label": "Get issue",
                "description": "Reads a single Jira issue by key.",
                "fields": [{"id": "issue_key", "label": "Issue key", "required": True, "placeholder": "ABC-123"}],
            },
            {
                "id": "jql",
                "label": "Run JQL",
                "description": "Runs a read-only Jira search query.",
                "fields": [
                    {"id": "query", "label": "JQL", "required": True, "placeholder": "assignee = currentUser() ORDER BY updated DESC"},
                    {"id": "max_results", "label": "Max results", "type": "number", "default": "10"},
                ],
            },
        ],
    },
    {
        "id": "log_platform",
        "label": "Log Platform",
        "description": "Search live or nonlive Log Platform logs through the configured Log Platform integration.",
        "actions": [
            {
                "id": "search",
                "label": "Search logs",
                "description": "Searches logs by CMDB, query, environment, and region.",
                "fields": [
                    {"id": "cmdbs", "label": "CMDBs", "required": True, "placeholder": "service-a,service-b"},
                    {"id": "query", "label": "Query", "required": True, "placeholder": "error"},
                    {"id": "env", "label": "Log env", "default": "live", "placeholder": "live"},
                    {"id": "region", "label": "Region", "default": "sg", "placeholder": "sg"},
                    {"id": "limit", "label": "Limit", "type": "number", "default": "5"},
                    {"id": "timeout", "label": "Timeout seconds", "type": "number", "default": "30"},
                    {"id": "wait_timeout", "label": "Wait timeout seconds", "type": "number", "default": "10"},
                ],
            },
            {
                "id": "search_url",
                "label": "Search copied URL",
                "description": "Searches from a copied Log Platform URL and optional limit.",
                "fields": [
                    {"id": "logplatform_url", "label": "Log Platform URL", "required": True, "type": "textarea"},
                    {"id": "limit", "label": "Limit", "type": "number", "default": "5"},
                    {"id": "timeout", "label": "Timeout seconds", "type": "number", "default": "30"},
                    {"id": "wait_timeout", "label": "Wait timeout seconds", "type": "number", "default": "10"},
                ],
            },
            {
                "id": "trace",
                "label": "Trace search",
                "description": "Searches logs by trace id.",
                "fields": [
                    {"id": "trace", "label": "Trace ID", "required": True},
                    {"id": "env", "label": "Log env", "default": "live", "placeholder": "live"},
                    {"id": "region", "label": "Region", "default": "sg", "placeholder": "sg"},
                    {"id": "limit", "label": "Limit", "type": "number", "default": "10"},
                    {"id": "timeout", "label": "Timeout seconds", "type": "number", "default": "30"},
                    {"id": "wait_timeout", "label": "Wait timeout seconds", "type": "number", "default": "10"},
                ],
            },
        ],
    },
    {
        "id": "confluence",
        "label": "Confluence",
        "description": "Search and read Confluence content.",
        "actions": [
            {
                "id": "search_pages",
                "label": "Search pages",
                "description": "Searches pages by text query.",
                "fields": [
                    {"id": "query", "label": "Query", "required": True, "placeholder": "project notes"},
                    {"id": "space_key", "label": "Space key", "placeholder": "Optional"},
                    {"id": "limit", "label": "Limit", "type": "number", "default": "10"},
                ],
            },
            {
                "id": "get_page",
                "label": "Get page",
                "description": "Reads a page by Confluence page ID.",
                "fields": [{"id": "page_id", "label": "Page ID", "required": True}],
            },
            {
                "id": "get_page_id",
                "label": "Get page ID from URL",
                "description": "Resolves a Confluence URL, display path, or short link to a page ID.",
                "fields": [
                    {
                        "id": "url",
                        "label": "Confluence URL",
                        "required": True,
                        "placeholder": "https://confluence.shopee.io/display/SPACE/Page+Title",
                    }
                ],
            },
            {
                "id": "get_page_markdown",
                "label": "Get page markdown",
                "description": "Fetches and converts a page to markdown.",
                "fields": [{"id": "page_id", "label": "Page ID", "required": True}],
            },
        ],
    },
    {
        "id": "google_docs",
        "label": "Google Docs",
        "description": "Create and inspect Google Docs.",
        "actions": [
            {
                "id": "create_document",
                "label": "Create document",
                "description": "Creates a small test document in the configured Google account.",
                "side_effect": True,
                "fields": [{"id": "title", "label": "Title", "required": True, "default": "Hangar integration test"}],
            },
            {
                "id": "get_document",
                "label": "Get document",
                "description": "Reads document metadata and body content.",
                "fields": [{"id": "document_id", "label": "Document ID or URL", "required": True}],
            },
            {
                "id": "get_text",
                "label": "Get text",
                "description": "Extracts plain text from a document.",
                "fields": [{"id": "document_id", "label": "Document ID or URL", "required": True}],
            },
        ],
    },
    {
        "id": "google_drive",
        "label": "Google Drive",
        "description": "Search, inspect, create folders, and review Drive file permissions.",
        "actions": [
            {
                "id": "list_files",
                "label": "List files",
                "description": "Lists recent Drive files visible to the configured Google account.",
                "fields": [
                    {"id": "page_size", "label": "Page size", "type": "number", "default": "10"},
                    {"id": "query", "label": "Drive query", "placeholder": "Optional Drive API query"},
                ],
            },
            {
                "id": "search_files",
                "label": "Search files",
                "description": "Searches Drive files with a Drive API query.",
                "fields": [
                    {"id": "query", "label": "Drive query", "required": True, "placeholder": "name contains 'report'"},
                    {"id": "page_size", "label": "Page size", "type": "number", "default": "10"},
                ],
            },
            {
                "id": "get_file",
                "label": "Get file",
                "description": "Reads Drive file metadata by file ID.",
                "fields": [{"id": "file_id", "label": "File ID", "required": True}],
            },
            {
                "id": "create_folder",
                "label": "Create folder",
                "description": "Creates a Drive folder in the configured Google account.",
                "side_effect": True,
                "fields": [
                    {"id": "name", "label": "Folder name", "required": True, "default": "Hangar integration test"},
                    {"id": "parent_id", "label": "Parent folder ID", "placeholder": "Optional"},
                ],
            },
            {
                "id": "list_permissions",
                "label": "List permissions",
                "description": "Lists permissions for one Drive file.",
                "fields": [{"id": "file_id", "label": "File ID", "required": True}],
            },
        ],
    },
    {
        "id": "google_mail",
        "label": "Google Mail",
        "description": "Search and inspect Gmail through the configured Google account.",
        "actions": [
            {
                "id": "search_messages",
                "label": "Search messages",
                "description": "Searches Gmail messages and returns metadata summaries.",
                "fields": [
                    {"id": "query", "label": "Gmail query", "placeholder": "newer_than:7d"},
                    {"id": "max_results", "label": "Max results", "type": "number", "default": "10"},
                ],
            },
            {"id": "list_labels", "label": "List labels", "description": "Lists Gmail labels.", "fields": []},
            {
                "id": "get_message",
                "label": "Get message",
                "description": "Reads one Gmail message by ID.",
                "fields": [{"id": "message_id", "label": "Message ID", "required": True}],
            },
        ],
    },
    {
        "id": "google_sheets",
        "label": "Google Sheets",
        "description": "Create spreadsheets and read sheet values.",
        "actions": [
            {
                "id": "create_spreadsheet",
                "label": "Create spreadsheet",
                "description": "Creates a test spreadsheet.",
                "side_effect": True,
                "fields": [{"id": "title", "label": "Title", "required": True, "default": "Hangar integration test"}],
            },
            {
                "id": "get_spreadsheet",
                "label": "Get spreadsheet",
                "description": "Reads spreadsheet metadata.",
                "fields": [{"id": "spreadsheet_id", "label": "Spreadsheet ID or URL", "required": True}],
            },
            {
                "id": "get_values",
                "label": "Get values",
                "description": "Reads values from a range.",
                "fields": [
                    {"id": "spreadsheet_id", "label": "Spreadsheet ID or URL", "required": True},
                    {"id": "range_name", "label": "Range", "required": True, "default": "Sheet1!A1:D10"},
                ],
            },
        ],
    },
    {
        "id": "pmp",
        "label": "PMP",
        "description": "Call PMP endpoints through the configured PMP integration.",
        "actions": [
            {
                "id": "get",
                "label": "GET path",
                "description": "Runs a PMP GET request against a path you provide.",
                "fields": [
                    {"id": "path", "label": "Path", "required": True, "placeholder": "/api/example"},
                    {"id": "params_json", "label": "Query params JSON", "type": "textarea", "placeholder": "{\"id\":\"123\"}"},
                ],
            }
        ],
    },
    {
        "id": "pop",
        "label": "POP",
        "description": "Read POP details and results through the platform connector.",
        "actions": [
            {
                "id": "get_pop_detail",
                "label": "Get POP detail",
                "description": "Reads a POP detail payload.",
                "fields": [{"id": "pop_id", "label": "POP ID", "required": True}],
            },
            {
                "id": "get_pop_results",
                "label": "Get POP results",
                "description": "Reads the results list for a POP.",
                "fields": [{"id": "pop_id", "label": "POP ID", "required": True}],
            },
        ],
    },
    {
        "id": "seatalk",
        "label": "SeaTalk",
        "description": "Inspect SeaTalk bot configuration and call safe bot APIs.",
        "actions": [
            {"id": "configured", "label": "Check configured", "description": "Checks whether required app credentials exist.", "fields": []},
            {"id": "get_joined_groups", "label": "Get joined groups", "description": "Lists groups joined by the bot.", "fields": []},
            {
                "id": "get_bot_subscribers",
                "label": "Get bot subscribers",
                "description": "Lists subscribers of the bot.",
                "fields": [],
            },
        ],
    },
    {
        "id": "space",
        "label": "SPACE",
        "description": "Call SPACE default or domain-specific endpoints.",
        "actions": [
            {
                "id": "get",
                "label": "GET default SPACE path",
                "description": "Runs a GET through the default SPACE connector.",
                "fields": [
                    {"id": "path", "label": "Path", "required": True, "placeholder": "/api/example"},
                    {"id": "params_json", "label": "Query params JSON", "type": "textarea", "placeholder": "{\"id\":\"123\"}"},
                ],
            },
            {
                "id": "domain_get",
                "label": "GET domain path",
                "description": "Runs a GET through a specific SPACE domain connector.",
                "fields": [
                    {"id": "domain", "label": "Domain", "required": True, "placeholder": "space"},
                    {"id": "path", "label": "Path", "required": True, "placeholder": "/api/example"},
                    {"id": "params_json", "label": "Query params JSON", "type": "textarea"},
                ],
            },
        ],
    },
    {
        "id": "llm_chat",
        "label": "LLM Chat",
        "description": "Create a raw OpenAI-compatible chat completion.",
        "actions": [
            {
                "id": "chat",
                "label": "Chat",
                "description": "Sends one non-streaming chat-completions request.",
                "fields": [
                    {"id": "message", "label": "Message", "required": True, "type": "textarea", "default": "Summarize the current integration check."},
                ],
            },
        ],
    },
]


def _action_map() -> dict[str, dict[str, dict[str, Any]]]:
    return {
        provider["id"]: {action["id"]: action for action in provider["actions"]}
        for provider in PROVIDERS
    }


def _required_fields(provider_id: str, action_id: str) -> list[str]:
    action = _action_map().get(provider_id, {}).get(action_id, {})
    return [field["id"] for field in action.get("fields", []) if field.get("required")]


def _text(inputs: dict[str, Any], key: str, default: str = "") -> str:
    value = inputs.get(key, default)
    return str(value or "").strip()


def _int(inputs: dict[str, Any], key: str, default: int, minimum: int = 1, maximum: int = 100) -> int:
    try:
        parsed = int(inputs.get(key) or default)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _json_object(inputs: dict[str, Any], key: str) -> dict[str, Any]:
    import json

    raw = _text(inputs, key)
    if not raw:
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"{key} must be a JSON object.")
    return parsed


def _ok(provider: str, action: str, result: Any, inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "provider": provider,
        "action": action,
        "app": ctx.app_slug,
        "user": ctx.user_email,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "result": jsonable_encoder(result),
    }


def _error(provider: str, action: str, error: Exception, inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": False,
        "provider": provider,
        "action": action,
        "app": ctx.app_slug,
        "user": ctx.user_email,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "error": {
            "type": error.__class__.__name__,
            "message": str(error),
        },
    }


def _run_jira(action: str, inputs: dict[str, Any]) -> Any:
    if action == "search_my_open_issues":
        project = _text(inputs, "project") or None
        return _integration("jira").search_my_open_issues(project=project, limit=_int(inputs, "limit", 10), fields=["summary", "status", "assignee"])
    if action == "get_issue":
        return _integration("jira").get_issue(_text(inputs, "issue_key"), fields=["summary", "status", "assignee", "updated"])
    if action == "jql":
        return _integration("jira").search(_text(inputs, "query"), max_results=_int(inputs, "max_results", 10), fields=["summary", "status", "assignee"])
    raise KeyError(action)


def _cmdbs(inputs: dict[str, Any]) -> list[str]:
    return [item.strip() for item in _text(inputs, "cmdbs").split(",") if item.strip()]


def _run_log_platform(action: str, inputs: dict[str, Any]) -> Any:
    common = {
        "limit": _int(inputs, "limit", 5, maximum=100),
        "timeout": _int(inputs, "timeout", 30, maximum=300),
        "wait_timeout": _int(inputs, "wait_timeout", 10, maximum=60),
    }
    if action == "search":
        return _integration("log_platform").search(
            cmdbs=_cmdbs(inputs),
            query=_text(inputs, "query"),
            env=_text(inputs, "env") or None,
            region=_text(inputs, "region") or None,
            return_logplatform_url=True,
            **common,
        )
    if action == "search_url":
        return _integration("log_platform").search(
            logplatform_url=_text(inputs, "logplatform_url"),
            **common,
        )
    if action == "trace":
        return _integration("log_platform").search(
            trace=_text(inputs, "trace"),
            env=_text(inputs, "env") or None,
            region=_text(inputs, "region") or None,
            **common,
        )
    raise KeyError(action)


def _run_confluence(action: str, inputs: dict[str, Any]) -> Any:
    if action == "search_pages":
        space_key = _text(inputs, "space_key") or None
        return _integration("confluence").search_pages(_text(inputs, "query"), space_key=space_key, limit=_int(inputs, "limit", 10))
    if action == "get_page":
        return _integration("confluence").get_page(_text(inputs, "page_id"))
    if action == "get_page_id":
        return {"page_id": _integration("confluence").get_page_id(_text(inputs, "url"))}
    if action == "get_page_markdown":
        return {"markdown": _integration("confluence").get_page_markdown(_text(inputs, "page_id"))}
    raise KeyError(action)


def _run_google_docs(action: str, inputs: dict[str, Any]) -> Any:
    if action == "create_document":
        return _integration("google_docs").create_document(_text(inputs, "title", "Hangar integration test"))
    if action == "get_document":
        return _integration("google_docs").get_document(_text(inputs, "document_id"))
    if action == "get_text":
        return {"text": _integration("google_docs").get_text(_text(inputs, "document_id"))}
    raise KeyError(action)


def _run_google_drive(action: str, inputs: dict[str, Any]) -> Any:
    drive = _integration("google_drive")
    if action == "list_files":
        return drive.list_files(
            q=_text(inputs, "query") or None,
            page_size=_int(inputs, "page_size", 10, maximum=100),
        )
    if action == "search_files":
        return drive.search_files(
            _text(inputs, "query"),
            page_size=_int(inputs, "page_size", 10, maximum=100),
        )
    if action == "get_file":
        return drive.get_file(_text(inputs, "file_id"))
    if action == "create_folder":
        parent_id = _text(inputs, "parent_id") or None
        return drive.create_folder(_text(inputs, "name", "Hangar integration test"), parent_id=parent_id)
    if action == "list_permissions":
        return drive.list_permissions(_text(inputs, "file_id"))
    raise KeyError(action)


def _run_google_mail(action: str, inputs: dict[str, Any]) -> Any:
    if action == "search_messages":
        query = _text(inputs, "query") or None
        return _integration("google_mail").search_messages(query=query, max_results=_int(inputs, "max_results", 10))
    if action == "list_labels":
        return _integration("google_mail").list_labels()
    if action == "get_message":
        return _integration("google_mail").get_message(_text(inputs, "message_id"), format="metadata")
    raise KeyError(action)


def _bool(inputs: dict[str, Any], key: str, default: bool = False) -> bool:
    raw = inputs.get(key)
    if raw is None or raw == "":
        return default
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _run_google_sheets(action: str, inputs: dict[str, Any]) -> Any:
    if action == "create_spreadsheet":
        return _integration("google_sheets").create_spreadsheet(_text(inputs, "title", "Hangar integration test"))
    if action == "get_spreadsheet":
        return _integration("google_sheets").get_spreadsheet(_text(inputs, "spreadsheet_id"))
    if action == "get_values":
        return _integration("google_sheets").get_values(_text(inputs, "spreadsheet_id"), _text(inputs, "range_name", "Sheet1!A1:D10"))
    raise KeyError(action)


def _run_pmp(action: str, inputs: dict[str, Any]) -> Any:
    if action == "get":
        return _integration("pmp").get(_text(inputs, "path"), params=_json_object(inputs, "params_json"))
    raise KeyError(action)


def _run_pop(action: str, inputs: dict[str, Any]) -> Any:
    if action == "get_pop_detail":
        return _integration("pop").get_pop_detail(_text(inputs, "pop_id"))
    if action == "get_pop_results":
        return _integration("pop").get_pop_results(_text(inputs, "pop_id"))
    raise KeyError(action)


def _run_seatalk(action: str, inputs: dict[str, Any]) -> Any:
    if action == "configured":
        return {"configured": _integration("seatalk").configured()}
    if action == "get_joined_groups":
        return _integration("seatalk").get_joined_groups()
    if action == "get_bot_subscribers":
        return _integration("seatalk").get_bot_subscriber_list()
    raise KeyError(action)


def _run_space(action: str, inputs: dict[str, Any]) -> Any:
    if action == "get":
        return _integration("space").get(_text(inputs, "path"), params=_json_object(inputs, "params_json"))
    if action == "domain_get":
        return _integration("space").domain_request(_text(inputs, "domain"), "GET", _text(inputs, "path"), params=_json_object(inputs, "params_json"))
    raise KeyError(action)


def _run_llm_chat(action: str, inputs: dict[str, Any]) -> Any:
    if action == "chat":
        return _integration("llm_chat").chat_completions.create(
            messages=[{"role": "user", "content": _text(inputs, "message")}],
        )
    raise KeyError(action)


RUNNERS = {
    "jira": _run_jira,
    "log_platform": _run_log_platform,
    "confluence": _run_confluence,
    "google_docs": _run_google_docs,
    "google_drive": _run_google_drive,
    "google_mail": _run_google_mail,
    "google_sheets": _run_google_sheets,
    "pmp": _run_pmp,
    "pop": _run_pop,
    "seatalk": _run_seatalk,
    "space": _run_space,
    "llm_chat": _run_llm_chat,
}


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": ctx.app_slug,
        "user": ctx.user_email,
        "integration_count": len(PROVIDERS),
        "action_count": sum(len(provider["actions"]) for provider in PROVIDERS),
    }


@router.get("/catalog")
def catalog():
    return {
        "providers": PROVIDERS,
        "app": ctx.app_slug,
        "user": ctx.user_email,
    }


@router.post("/run")
def run(payload: dict[str, Any]):
    provider = _text(payload, "provider")
    action = _text(payload, "action")
    inputs = payload.get("inputs") if isinstance(payload.get("inputs"), dict) else {}

    if provider not in RUNNERS:
        return _error(provider, action, ValueError(f"Unknown integration provider: {provider}"), inputs)
    if action not in _action_map().get(provider, {}):
        return _error(provider, action, ValueError(f"Unknown action for {provider}: {action}"), inputs)

    missing = [field for field in _required_fields(provider, action) if not _text(inputs, field)]
    if missing:
        return _error(provider, action, ValueError("Missing required field(s): " + ", ".join(missing)), inputs)

    try:
        result = RUNNERS[provider](action, inputs)
        return _ok(provider, action, result, inputs)
    except Exception as error:
        return _error(provider, action, error, inputs)
