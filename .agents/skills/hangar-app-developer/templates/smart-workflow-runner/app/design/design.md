# SMART Workflow Runner

This app runs one SMART workflow as asynchronous, durable tasks. Each task retains the submitted input, SMART thread, parsed node progress, raw debug tree, result, errors, usage, and persisted Hangar file assets.

## Product decisions

- The task detail page has exactly three primary expandable panels: submitted input, workflow progress, and workflow output.
- Initialize the frontend route from HangarKit `nav.localPath()` during SSR, not only after mount, so direct page loads include their route-specific component CSS.
- Panels begin collapsed and the status-relevant panel opens automatically: progress while active or interrupted; output after success or failure.
- Parsed progress is a node timeline and inspector. Preserve raw SMART JSON for inspection, with a bounded scroll area and a copy action in every raw JSON view.
- Parse node names/types and node input/output values from `node_debug_details`; include parallel child nodes when SMART returns them. Show these on demand in the node inspector.
- Order the execution timeline from SMART's `traversed_edges` rather than node IDs, and show the traversed connections between node rows. Parsed input and output values use a bounded, internally scrollable region.
- Expanding the selected node's inspector must not stretch or change the height of timeline rows; keep the left timeline intrinsically sized while the inspector grows or scrolls independently.
- Task detail identifies the creator and uses a compact Started → Duration → Ended execution timeline, with the status chip preceding the task context.
- Field configuration has Input and Output tabs. Each field expands for editing; `show_in_list` controls a task-list column and input `searchable` controls a dedicated task-list filter. Both default off.
- Configured input filters belong in the same toolbar as the standard search, status, and refresh filters; do not add a separate filter-section heading.
- Administrators can paste a sample JSON object to import fields. Nested object samples produce JSON Schema object specs.
- When a run title is blank, generate it from submitted input values: trim each non-empty value to 20 characters and join them with `, `.
- Table cells may visually truncate long values, but their hover text exposes up to 1,000 characters before indicating further truncation.
- Output values that are HTTP(S) URLs are safe external links and open in a new tab.
- Store browser file uploads as `smart_workflow_task_files` assets before invoking SMART. Detail pages must offer view and download actions.
- Costs are SMART-returned model usage only. Never estimate cost from prompt size or configurable rates.
- SMART business errors (`_business_error_code` and `_business_error_msg`) become failed tasks with a concise error summary while raw detail remains available.
- The app does not use legacy paste-only compatibility behavior.

## Visual direction

Quiet operational interface: light panels, compact medium-weight type, restrained blue highlights, small status chips, and clear separation between inspectable raw data and the primary parsed view. Avoid oversized or heavy typography.
# Routing

Use the root app path with query-string views (`?view=new`, `?view=metrics`, `?view=configuration`, and `?task=<id>`) for all browser navigation. This keeps every page reachable when a deployment ingress does not provide SPA fallback for nested app paths. Page implementation remains split across the individual `pages/*.svelte` files.
