# SMART

ID: `connector_integration.smart`
Category: `connector_integration`

Use Connector's SPACE-derived SMART credential for native APIs and MCP tools, separately from template schema import.

## Import

`from hangarkit.integrations import smart`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `smart.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `smart.request(method, path, *, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`
- `smart.call_tool(tool, arguments=None, *, timeout=60, full_response=False)`

## Details

Read `connector_integration.native_apis` first. SMART uses a Connector-managed, SPACE-derived PAT on fixed `https://smart.shopee.io`. Connector revalidates the selected person's linked SPACE access before using SMART. Do not supply a PAT in app settings or headers. There are no `env`, `region`, or `domain_id` flags and no browser Relay setup.

Search/describe `provider="smart"` and prefer `smart.call` for reviewed catalog operations, including the cataloged MCP tool adapter. `smart.call_tool(tool, arguments)` is the verified `/call/:tool` transport adapter: fix the reviewed tool name in backend code and provide a dictionary of validated arguments. It returns the provider's decoded response unchanged. An HTTP 2xx can still contain an MCP/application-level error or `isError` result; inspect that envelope rather than treating HTTP success as completed workflow success. The helper does not discover tools or automatically retry uncertain writes.

Use `smart.request` only for independently verified uncataloged SMART API paths. Bound workflow/task inputs and output sizes, confirm writes, and show a feature-scoped status/retry. Use the common HTTP error contract, and ask the selected user or owner to repair linked SPACE/SMART access when necessary.

This first-class integration is distinct from Hangar's existing SMART workflow-runner template and administrator-managed schema importer. It does not expose or reuse an administrator's template-import credential. Test the actual workflow/tool as the configured account; a schema import or successful app grant is not proof of runtime SMART permission.
## Related capabilities

- `connector_integration.native_apis`
- `workflow.smart_workflow_runner`
