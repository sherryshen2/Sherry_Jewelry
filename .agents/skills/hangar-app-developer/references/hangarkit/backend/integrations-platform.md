# Platform integrations

ID: `backend.integration.platform`
Category: `backend`

Platform and proxy-backed backend helpers for POP, PMP, and Wingman Chat.

## Import

`from hangarkit.integrations import pop, pmp, wingman_chat`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `pop.call_tool(module, tool, arguments=None), pop.feature_request_detail_get(issue_key), pop.request(method, module, ...)`
- `pmp.get(path), pmp.post(path), pmp.put(path), pmp.patch(path), pmp.delete(path), pmp.request(method, path, ...)`
- `wingman_chat.start(message, session_id=None, metadata=None, app_id=None, idempotency_key=None, timeout=300, workspace=None, agent_prompt=None, identity_prompt=None), get_run(run_id, timeout=30), put_file(workspace, filename, content, content_type="application/octet-stream", timeout=30), list_files(workspace), get_file(workspace, filename), delete_file(workspace, filename)`

## Details

Use these modules for platform or proxy-backed backend integrations. POP defaults to app owner-token auth, can be configured for explicit user auth or saved service-token auth, and routes through Wingman’s POP proxy. Wingman Chat is platform-provided, includes managed Wingman tools such as Toolverse, and defaults to app-owner permission without saved integration settings. Submit a turn with `start()`, poll with `get_run()`, and persist the completed `session_id` to continue a conversation; app code can name its bot-managed workspace and supply first-turn conversation prompts but cannot configure its LLM or tools.

These modules are backend runtime helpers. They are injected by Hangar and are not local Python packages in a plain dev environment.
## Quick examples

- `detail = pop.feature_request_detail_get("SPCPM-123456")`
- `run = wingman_chat.start("Summarize this app state", idempotency_key="turn-123")`

## Related capabilities

- `backend.integrations`
- `backend.integration.pop`
- `backend.integration.pmp`
- `backend.integration.wingman_chat`
