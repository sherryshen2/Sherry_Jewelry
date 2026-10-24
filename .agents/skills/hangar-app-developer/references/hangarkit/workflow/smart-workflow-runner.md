# SMART workflow runner template

ID: `workflow.smart_workflow_runner`
Category: `workflow`

Create a task runner for one deployed SMART workflow, using either a pasted input schema or administrator-managed SMART Project schema import.

## Caller guidance

This page documents a workflow rather than a callable helper. Follow its ordered steps and use the linked capability page before calling a runtime API.

## Details

The SMART workflow runner template supports two onboarding modes:

- **Manual**: paste the SMART `Input` block from Workflow as API. The generated runner keeps workflow output as raw JSON.
- **Admin SMART Project**: select an enabled administrator-managed SMART Project, enter a workflow graph ID or `https://smart.shopee.io/apps/w/:id` URL, and import input plus output parameter metadata from `GET /openapi/v1/workflows/:id/params`.

Hangar administrators manage SMART Project display names and SMART service-account bearer tokens at `/hangar/admin/smart-projects`. The tokens are encrypted at rest with `HANGARKIT_SMART_PROJECT_SECRET_KEY` (or the Hangar session secret when explicitly configured), are never returned to browsers or generated apps, and are used only by Hangar's server-side schema-import endpoint.

Schema import stores only non-secret metadata in the generated app: the SMART Project id, workflow id, import time, and normalized `smart_workflow_input_fields` / `smart_workflow_output_fields` table records. It does not obtain or store the workflow endpoint key.

Every generated runner still requires its own Endpoint Hash ID and Endpoint Key. Those are app secrets exposed to the Python backend as `SMART_ENDPOINT_DEPLOYMENT_HASH_ID` and `SMART_ENDPOINT_DEPLOYMENT_KEY`; never put them in app data, frontend files, Content, Design, task records, or logs.

Generated runners provide separate Tasks, Create task, Task detail, Metrics, and Configuration pages. Tasks are SMART async threads: the runner persists the thread id, polls `get_debug_tree`, records terminal status, shows node-level lifecycle progress, and stores the final output. The Tasks page can search submitted input values, filter by status, and refresh active tasks manually or at a selected interval.

File inputs are first saved through an app-scoped `smart_workflow_task_files` table with a `file` field, so Hangar persists the upload as an app asset. The runner then sends SMART the required data URL representation while task records retain only compact file metadata and the durable asset filename. It never stores raw base64 file content in a task record.

The Configuration page lets app maintainers adjust input and output field metadata. It also exposes cost-estimate rates per 1,000 persisted JSON characters. Metrics report the resulting estimated cost, but this is explicitly not SMART provider billing or token usage.
## Related capabilities

- `runtime.routing`
- `backend.hangarkit`
- `frontend.data`
