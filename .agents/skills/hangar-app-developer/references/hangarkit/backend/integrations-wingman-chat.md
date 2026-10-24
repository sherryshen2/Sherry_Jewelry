# Wingman Chat integration

ID: `backend.integration.wingman_chat`
Category: `backend`

Submit a managed Wingman Chat turn and poll its bot-owned run without holding an HTTP request open.

## Import

`from hangarkit.integrations import wingman_chat`

`from hangarkit import ctx`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `wingman_chat.start(message, session_id=None, metadata=None, app_id=None, idempotency_key=None, timeout=300, workspace=None, agent_prompt=None, identity_prompt=None)`
- `wingman_chat.get_run(run_id, timeout=30)`
- `wingman_chat.get_events(run_id, after=0, timeout=30)`
- `wingman_chat.put_file(workspace, filename, content, content_type="application/octet-stream", timeout=30)`
- `wingman_chat.list_files(workspace, timeout=30)`
- `wingman_chat.get_file(workspace, filename, timeout=30)`
- `wingman_chat.delete_file(workspace, filename, timeout=30)`

## Details

Use `wingman_chat` for a managed Wingman conversation. It has Wingman's built-in tools, including Toolverse-backed capabilities where available, and can use the platform's managed agent behavior. App code **cannot configure the model, system prompt, tool definitions, tool choice, or tool-execution loop** for this integration. `agent_prompt` and `identity_prompt` are app-provided conversation instructions on the first turn, not authentication identities or a system-prompt override.

Hangar chooses the conversation identity from the app's saved integration setting. In **current-user** mode, the request must carry a valid runtime session and the approved current user's Wingman token is used. In **app-owner** mode, Hangar uses the app owner's token. App code cannot choose or override either identity with request fields.
The app owner selects the mode in Craft > Integrations > Wingman Chat and saves the integration. App-owner mode is the default for existing apps. The saved `settings.integrations.wingman_chat.auth_mode` is `app` or `user`; app mode also uses `app_provider: "owner_token"`.

Use `start()` and `get_run()` for every new Wingman Chat integration. Each call is a short HTTP request; the bot owns the long-running turn. Do not wait for the answer inside a Hangar backend request or hold one gateway connection open. A frontend can call a backend `def` route to submit, retain the returned `run_id`, then poll a separate backend `def` route every few seconds. Avoid a blocking poll loop inside either route.

`start()` accepts **one user message**, never a message history, and returns `{run_id, session_id, status}` without waiting for the answer. When `session_id` is omitted, the bot creates a new session in the background; the initial response has a null `session_id`. Its `timeout` is the bot turn limit (1-600 seconds), not an HTTP gateway timeout. `get_run()` returns `queued`, `running`, `completed`, or `failed`. Completed runs include `result` with `content`, `message`, `tool_calls`, `usage`, and the newly created `session_id`; failed runs include `error`.

To show activity while a turn runs, call `get_events(run_id, after=cursor)` from a separate backend route. Its response is `{run_id, status, next_cursor, has_more, events}`: `status` is the run's current state, `next_cursor` is the last returned event's sequence number (or the supplied `after` if the page is empty), and `has_more` means another page is already available. Each event has an increasing `seq`, a UTC `created_at`, a `type`, and type-specific `data`:

| `type` | `data` | Meaning |
| --- | --- | --- |
| `status` | `{"state": "queued" \| "running" \| "completed" \| "failed"}` | The run was accepted, began executing, finished, or failed. |
| `tool.started` | `{"call_id": "...", "name": "..."}` | A tool call began. `call_id` can be an empty string when upstream omits it; `name` can be `"unknown"`. |
| `tool.completed` | `{"call_id": "...", "name": "...", "status": "success" \| "error" \| "unknown"}` | A tool call ended. `error` means upstream reported an error; `success` means its result included a non-null `success` field without an error flag (even if that field was `false`); `unknown` means no explicit outcome was supplied, not necessarily a failure. |
| `progress` | `{"summary": "Using <tool name>"}` | A short activity label emitted when a tool starts, **not** the model's thinking. |

For example, a page requested with `after=2` during execution may look like:

```json
{
  "run_id": "a8c07b1f-2a48-4c1b-b975-12b08cff524c",
  "status": "running",
  "next_cursor": 4,
  "has_more": false,
  "events": [
    {"seq": 3, "created_at": "2026-09-29T06:00:00+00:00", "type": "tool.started", "data": {"call_id": "call-1", "name": "jira.search"}},
    {"seq": 4, "created_at": "2026-09-29T06:00:00+00:00", "type": "progress", "data": {"summary": "Using jira.search"}}
  ]
}
```

Start with `after=0`, render events, and persist the returned `next_cursor`. Each page contains at most 100 events. When `has_more` is true, fetch the next page immediately; otherwise poll every few seconds while the run is active. Once top-level `status` is `completed` or `failed`, **drain any remaining pages before stopping**, then call `get_run(run_id)` for the final answer (`result.content`) or failure (`error`). An empty page preserves the cursor; do not infer completion from an empty `events` array. Tool activity is best-effort: not every upstream tool emits these events. The live timeline does not expose raw thinking, tool arguments, or tool outputs. Events have the same app/user scope and seven-day retention as their run.

The completed run's `result.events` is a separate, sanitized result history, **not** the paginated live timeline above. Completed run `result.tool_calls` and `result.events` retain their keys but contain safe activity only; raw tool arguments, outputs, and session credentials are not returned by the async run API. The older synchronous `chat()` and `stream()` helpers retain their legacy response shape.

The app owns conversation continuity. Save the completed `session_id` in your own record, browser state, or app-scoped table and pass it to the next `start()` call. Save the `run_id` to resume polling after a refresh. Supply a stable `idempotency_key` per turn and reuse it when retrying an uncertain submission; a new key can create another turn. Reusing a key for different input or submitting another active turn on the same existing session is rejected. Results are retained by the bot for seven days. Polling must use the same app/user integration identity as submission.

The bot-managed working folder is exactly `hangar_chat/<app-key>/<workspace>`, selected by the Hangar app's backend; no actor or chat-session directory is appended. Omit `workspace` to reuse `default` across turns and users. Two users given the same name share the entire working folder, but not their chat session IDs or run results. To separate work, the app owner can pass a stable team key, an authenticated `ctx.user_email.strip().lower()` (import `ctx` from `hangarkit`), or an app-generated conversation key chosen before the first turn as the workspace name. The bot's session ID arrives later and is not a workspace name by default. Do not trust an arbitrary workspace name from the browser when isolation matters. The app owner can manage every workspace's files. Runtime credential homes live outside the working folder and are keyed by workspace and Wingman credential subject, not app actor: owner-permission turns in one workspace share a credential home; current-user turns keep separate credential homes. The optional workspace is a 1-254 character ASCII name beginning with a letter or digit and otherwise using letters, digits, dots, dashes, underscores, `@`, or `+`; it is never a filesystem path. Prompts are limited to 8000 characters each and are applied only once, at the chat session's first turn. On subsequent turns, omit these options or send the same values. Old workspace files under `session/` are not automatically moved to the flat folder; older chat sessions may continue but cannot be assigned a new workspace.

`put_file()` creates or replaces a file by name in that workspace's `uploads/` directory; `list_files()` returns `{"files": [{"name": ..., "size": ..., "path": "uploads/<name>"}]}`, `get_file()` returns bytes, and `delete_file()` removes it. These operations use the Hangar-derived app identity and need no chat session ID, so files may be uploaded before the first turn. Files uploaded by one app user are visible to other users of the same app workspace and to the app owner in Craft. Names must be flat ASCII names (1-128 characters, beginning with a letter or digit); paths and subdirectories are not accepted. The bot limits each upload to 10 MiB and each workspace to 100 files or 50 MiB. Mention `uploads/<name>` in a chat turn when the agent should use an uploaded file; upload alone does not add it to model context. These helpers cannot access or delete the agent's other files or `codex_home`.

Existing synchronous helpers remain callable for older apps, but new apps should use the submit/poll flow.

This is a backend runtime helper injected by Hangar. It is not a local Python package in a plain dev environment.
## Quick examples

- `run = wingman_chat.start("Trace API ownership", idempotency_key="turn-123")`
- `run = wingman_chat.start("Investigate", workspace="triage", agent_prompt="Cite evidence.", identity_prompt="You are a triage assistant.", idempotency_key="turn-456")`
- `run = wingman_chat.start("Investigate", workspace=ctx.user_email.strip().lower(), idempotency_key="turn-789")`
- `wingman_chat.put_file("triage", "brief.md", b"# Background\n...")`
- `status = wingman_chat.get_run(run["run_id"])`
- `activity = wingman_chat.get_events(run["run_id"], after=0)`

## Related capabilities

- `backend.integrations`
- `backend.integration.platform`
- `backend.integration.llm_chat`
