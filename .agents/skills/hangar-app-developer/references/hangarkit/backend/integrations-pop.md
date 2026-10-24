# POP integration

ID: `backend.integration.pop`
Category: `backend`

Call Product Operation Platform tools through Wingman POP proxy from backend code.

## Import

`from hangarkit.integrations import pop`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `pop.client()`
- `pop.call_tool(module, tool, arguments=None, timeout=60, parse_text_json=True)`
- `pop.request(method, module, json=None, data=None, headers=None, timeout=30)`
- `pop.raw_mcp(module, payload, timeout=30)`
- `pop.tool_schema(tool, module=None), pop.tool_schemas(module=None)`
- `pop.feature_request_search(**filters)`
- `pop.feature_request_detail_get(issue_key)`
- `pop.key_project_get(kp_key=None, key_project_id=None, **filters)`
- `pop.key_project_create(**fields), pop.key_project_basic_update(**fields), pop.key_project_impact_update(**fields)`
- `pop.llm_request_get(request_key=None, request_id=None, **filters)`
- `pop.data_request_get(request_key, **filters)`
- `pop.model_request_get(model_request_key, **filters)`

## Details

Use this module for Product Operation Platform calls through Wingman’s POP proxy. HangarKit does not connect to POP MCP directly. The runtime calls Wingman, and Wingman handles MCP session setup and upstream POP authorization.

Configure POP like other user/app integrations:

```json
{ "integrations": { "pop": { "auth_mode": "user" } } }
```

For app-level access through the app owner’s linked POP account, use:

```json
{ "integrations": { "pop": { "auth_mode": "app", "app_provider": "owner_token" } } }
```

For a fixed POP token stored on the app, use:

```json
{ "integrations": { "pop": { "auth_mode": "app", "app_provider": "service_token", "credential": "..." } } }
```

Supported modules are `feature_request`, `key_project`, `llm_request`, `data_request`, and `model_request`. Prefer the named helpers for common reads and `call_tool()` for newly added POP tools. `raw_mcp()` is available only for advanced JSON-RPC passthrough.

Feature request helpers include search, detail, audit log, comments, and known write tools such as reassignment, ETA update, re-review, opt update/transition, epic creation, and supporting product-line add. Key project helpers include search, read, comments, audit log, create/update/transition, planned effort, and supporting key project operations. Only call write helpers after the user confirms the exact target and change.

Use `pop.tool_schema("feature_request_search")` or `pop.tool_schemas("feature_request")` when app code needs the exact JSON schema at runtime.

## Parameter Reference

Generated from POP MCP `tools/list` on 2026-06-23. The `smart_platform_normal_token` compatibility field is intentionally omitted; HangarKit sends auth through Wingman.

### `feature_request`

#### `feature_request_audit_log_list`
List the paginated audit log (field change history) for a POP Feature Request by issue key, e.g. SPCPM-1902.

Required: `issue_key`

| Parameter | Type | Notes |
|---|---|---|
| `issue_key` | `string` | Required. Unique issue key of the feature request, e.g. SPCPM-1902. |
| `page_num` | `integer` | Page number, 1-based. Defaults to 1. |
| `page_size` | `integer` | Page size. Defaults to 20. |

#### `feature_request_detail_get`
Get the full detail of a single POP Feature Request by issue key (e.g. SPCPM-1902), including overview (status, assignees, dates), details (description, business goal, product line), and operations history. Use feature_request_search first if you don't have the issue key.

Required: `issue_key`

| Parameter | Type | Notes |
|---|---|---|
| `issue_key` | `string` | Required. Unique issue key of the feature request, e.g. SPCPM-1902. |

#### `feature_request_epic_create`
Create and link a Jira Epic for a feature request product line/component.

Required: `issue_key`, `product_line_name`, `component_name`, `jira_epic_name`, `jira_epic_assignee`

| Parameter | Type | Notes |
|---|---|---|
| `actual_release_date` | `string` | Optional. Actual release date, format accepted by upstream. |
| `component_name` | `string` | Required. Component name under the product line. |
| `estimated_dev_effort` | `number` | Optional. Estimated development effort. |
| `estimated_prd_signoff_date` | `string` | Optional. Estimated PRD signoff date, format accepted by upstream. |
| `estimated_qa_effort` | `number` | Optional. Estimated QA effort. |
| `issue_key` | `string` | Required. Unique issue key of the feature request, e.g. SPCPM-1902. |
| `jira_epic_assignee` | `string` | Required. Jira Epic assignee email. Free-form: must be a staff email address (e.g. user@shopee.com). Name is not accepted by the API. |
| `jira_epic_name` | `string` | Required. Jira Epic summary/name to create. |
| `planned_release_date` | `string` | Optional. Planned release date, format accepted by upstream. |
| `prd_link` | `string` | Optional. PRD/FRF document link. |
| `product_line_name` | `string` | Required. The main or supporting Product line name of the feature request. |

#### `feature_request_get_comments`
Get all comments and replies for a POP Feature Request in a tree structure. Provide the issue_key (e.g. SPCPM-1234) or the physical request_tab_id. The body field of each comment is HTML-formatted text.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `issue_key` | `string` | Issue key of the feature request (e.g. SPCPM-1234). Preferred identifier. |
| `request_tab_id` | `integer` | Physical numeric ID of the feature request. Use issue_key when possible. |

#### `feature_request_opt_transition`
Transition market opt-in/out state for a feature request. Use human-readable to_status labels from feature://field-options field_key opt_in_out_status, e.g. Opted In, Opted Out, or Closed.

Required: `opt_in_out_id`, `to_status`

| Parameter | Type | Notes |
|---|---|---|
| `opt_in_out_id` | `string` | Required. Physical ID for opt in/out, e.g. "100238". |
| `to_status` | `string` | Required. Human-readable target opt-in/out status, only 'Opted In', 'Opted Out' allowed. |

#### `feature_request_opt_update`
Update market opt-in/out details for a feature request, including assignee, people involved, priority, and remarks.

Required: `opt_in_out_id`

| Parameter | Type | Notes |
|---|---|---|
| `assignee` | `string` | Optional. New opt-in/out assignee email. Free-form: must be a staff email address (e.g. user@shopee.com). Name is not accepted by the API. |
| `opt_in_out_id` | `string` | Required. Physical ID for opt in/out, e.g. "100238". |
| `priority` | `string` | Optional. opt status, ENUM:P1,P2,P3. e.g. P1 |
| `remarks` | `string` | Optional. free text remarks. |

#### `feature_request_re_assign`
Reassign the business approval reviewer for a feature request.

Required: `issue_key`, `assignee`

| Parameter | Type | Notes |
|---|---|---|
| `assignee` | `string` | Required. New business approval reviewer email. Free-form: must be a staff email address (e.g. user@shopee.com). Name is not accepted by the API. |
| `issue_key` | `string` | Required. Unique issue key of the feature request, e.g. SPCPM-1902. |

#### `feature_request_re_review`
Reset a feature request business approval state to Re-review.

Required: `issue_key`

| Parameter | Type | Notes |
|---|---|---|
| `issue_key` | `string` | Required. Unique issue key of the feature request, e.g. SPCPM-1902. |

#### `feature_request_search`
Search POP Feature Requests with filters and pagination. Supports filtering by request ID, name, progress status, priority, country, product line, assignee, review type, submission cycle, business line, date ranges, and more. Use feature_request_detail_get to fetch full details after finding a request ID.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `ba_statuses` | `array | null` | UI: 'Business Approval Status'. Filter by business approval status labels. |
| `bpm_pic` | `string` | UI: 'BPM Assignee'. Free-form: must be a staff email address (e.g. user@shopee.com). Name is not accepted by the API. |
| `business_approval_date_end` | `string` | UI: 'Business Approval Date' end. Free-form: format YYYY-MM-DD. |
| `business_approval_date_start` | `string` | UI: 'Business Approval Date' start. Free-form: format YYYY-MM-DD. |
| `business_labels` | `array | null` | UI: 'Business Label'. string array, Free-form: custom business labels attached to the request. e.g. ["label"] |
| `business_line` | `array | null` | UI: 'Business Line'. Enum array: values must match labels from resource feature://field-options (field_key: business_line). e.g. ["OPS", "Marketing"]. |
| `classifications` | `array | null` | UI: 'Business Line (Classification)'. Enum array: values must match labels from resource feature://field-options (field_key: classification). e.g. ["OPS"] |
| `current_assignee` | `string` | UI: 'Current Assignee'. Free-form: must be a staff email address (e.g. user@shopee.com). Name is not accepted by the API. |
| `issue_keys` | `array | null` | Issue Keys, e.g. ["SPCPM-50078"]. |
| `main_product_lines` | `array | null` | UI: 'Main Product Line'. Enum array: values must match labels from resource feature://field-options (field_key: product_line). e.g. ["Affiliate", "Logistics"]. |
| `market_specific_request` | `string` | UI: 'Market Specific Request'. Fixed values: 'Yes' or 'No'. |
| `opt_statuses` | `array | null` | UI: 'Market Opt In/Out'. Strict format: '{COUNTRY}-{IN|OUT|PENDING}', uppercase country code + hyphen + IN/OUT/PENDING, e.g. ["SG-IN","TW-OUT","MY-PENDING"]. Do NOT use 'Opted In'/'Opted Out' labels here (those are only for the opt transition tool). |
| `original_priorities` | `array | null` | UI: 'Original Priority'. Enum: values must match labels from resource feature://field-options (field_key: priority). e.g. ["P1", "P2"] |
| `page_num` | `integer` | Page number, 1-based. Defaults to 1. |
| `page_size` | `integer` | Page size. Defaults to 20. |
| `planned_eta_month` | `string` | UI: 'Planned Live ETA'. Free-form: month in format 'MMM YYYY', e.g. 'Feb 2026'. |
| `priorities` | `array | null` | Legacy combined priority filter. Prefer original_priorities. Enum: values must match labels from resource feature://field-options (field_key: priority). e.g. ["P1", "P2"] |
| `request_name` | `string` | UI: 'Request Name'. Free-form partial match on the feature request title. |
| `request_statuses` | `array | null` | UI: 'Request Progress'. Enum: values must match labels from resource feature://field-options (field_key: request_status). |
| `request_submission_cycle` | `array | null` | UI: 'Request Submission Cycle'. Enum array: values must match labels from resource feature://field-options (field_key: submission_cycle). e.g.["Cycle 23","Cycle 24"] |
| `request_type` | `array | null` | UI: 'Request Type'. Enum: values must match labels from resource feature://field-options (field_key: request_type). e.g. ["Regional Business Initiative", "Market Specific"]. |
| `reviewer_priorities` | `array | null` | UI: 'Reviewer Priority'. Filter by reviewer-assigned priority labels. |
| `submission_date_end` | `string` | UI: 'Submission Date' end. Free-form: format YYYY-MM-DD. |
| `submission_date_start` | `string` | UI: 'Submission Date' start. Free-form: format YYYY-MM-DD. |
| `submission_types` | `array | null` | UI: 'Submission Type'. Enum Array: values must match labels from resource feature://field-options (field_key: submission_type). e.g.["Roadmap"] |
| `supporting_product_lines` | `array | null` | UI: 'Supporting Product Line array'. Enum: values must match labels from resource feature://field-options (field_key: product_line). e.g. ["Affiliate", "Logistics"] |
| `target_countries` | `array | null` | UI: 'Target Country'. Enum array: values must match labels from resource feature://field-options (field_key: target_country). e.g. ["SG", "TW"] |

#### `feature_request_set_eta`
Set Planned Live ETA for a feature request product line. Requires issue_key, planned_eta_month, and planned_eta_change_reason. Use feature://field-options field_key planned_eta_change_reason for valid reason labels.

Required: `issue_key`, `planned_eta_month`, `planned_eta_change_reason`

| Parameter | Type | Notes |
|---|---|---|
| `issue_key` | `string` | Required. Unique issue key of the feature request, e.g. SPCPM-1902. |
| `planned_eta_change_reason` | `string` | Required. Human-readable reason label from feature://field-options field_key planned_eta_change_reason. |
| `planned_eta_month` | `string` | Required. Planned Live ETA month, e.g. 'Feb 2026'. |

#### `feature_request_supporting_product_line_add`
Add supporting product lines to a feature request.

Required: `issue_key`, `product_line_names`

| Parameter | Type | Notes |
|---|---|---|
| `issue_key` | `string` | Required. Unique issue key of the feature request, e.g. SPCPM-1902. |
| `product_line_names` | `array | null` | Required. Product line names to add as supporting product lines. Enum: values must match labels from resource feature://field-options (field_key: product_line). e.g. ["Affiliate", "Logistics"]. |

### `key_project`

#### `key_project_basic_update`
Update Basic Information For a single Key Project in one call: basic info, exclude impact data. key_project_id or kp_key is required to identify the KP. kp_name is mandatory. To update impact info, please use `key_project_impact_update` tool. All enum fields (kp_type, kp_category, kp_markets, kp_product_team, kp_tech_team, etc.) must provide human-readable labels. Read the kp://field-options resource to see all valid label values.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `change_reason` | `string` | Change Reason, Mandatory when you want to modify Key Project ETA. free text. |
| `key_project_id` | `integer` | Physical KP ID. Preferred if known. |
| `kp_business_line_pic_emails` | `array | null` | Business line PIC emails. Optional. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_category` | `string` | KP category label, Optional.Enum: values must match labels from resource kp://field-options (field_key: kp_category_code). e.g. "Growth", "Efficiency". |
| `kp_description` | `string` | KP description. free text, Optional. |
| `kp_eta` | `string` | Key Project ETA date. Optional. Format: YYYY-MM-DD. |
| `kp_key` | `string` | KP key, e.g. KP-1234. Case-insensitive. |
| `kp_key_initiatives` | `string` | Key initiatives summary. free text, Optional. |
| `kp_markets` | `array | null` | Market labels, Optional.Enum: values must match labels from resource kp://field-options (field_key: kp_market). e.g. ["SG", "MY"]. |
| `kp_name` | `string` | KP title. free text, Mandatory. |
| `kp_owner_emails` | `array | null` | Owner staff emails. Optional. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_pm_pic_emails` | `array | null` | PM PIC emails. Optional when KpType is "Business" e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_product_team` | `string` | Product team label, Mandatory when KpType is updated to "Business". Enum: values must match labels from resource kp://field-options (field_key: kp_product_team_id). e.g. "Digital Product". |
| `kp_rx_team` | `string` | RX team label,Optional, Enum: values must match labels from resource kp://field-options (field_key: kp_rx_team_code).e.g. "RBX", "Not Required". |
| `kp_supporting_doc_list` | `array | null` | Supporting document URLs. |
| `kp_tech_lead_emails` | `array | null` | Tech lead emails. Optional. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_tech_pic_emails` | `array | null` | Tech PIC emails. Optional. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_tech_team` | `string` | Tech team label,Mandatory when KpType is updated to "Technical".Enum: values must match labels from resource kp://field-options (field_key: kp_tech_team_id). e.g. "Marketplace Core". |
| `kp_type` | `string` | KP type , Optional. Enum: values must match labels from resource kp://field-options (field_key: kp_type_code). e.g. "Business" or "Technical". |

#### `key_project_create`
Create a single Key Project in one call: basic info, team assignments All enum fields (kp_type, kp_category, kp_markets, kp_product_team, kp_tech_team, etc.) must provide human-readable labels. Read the kp://field-options resource to see all valid label values.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `kp_business_line_pic_emails` | `array | null` | Business line PIC emails. Optional. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_category` | `string` | KP category label, mandatory.Enum: values must match labels from resource kp://field-options (field_key: kp_category_code). e.g. "Growth", "Efficiency". |
| `kp_description` | `string` | KP description. free text, Mandatory. |
| `kp_eta` | `string` | Estimated delivery date.Mandatory. Format: YYYY-MM-DD. |
| `kp_key_initiatives` | `string` | Key initiatives summary. free text, Optional. |
| `kp_markets` | `array | null` | Market labels, Mandatory.Enum: values must match labels from resource kp://field-options (field_key: kp_market). e.g. ["SG", "MY"]. |
| `kp_name` | `string` | KP title.free text, Mandatory. |
| `kp_owner_emails` | `array | null` | Owner staff emails. Mandatory. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_pm_pic_emails` | `array | null` | PM PIC emails. Mandatory when KpType is "Business" e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_product_team` | `string` | Product team label, Mandatory when KpType is "Business". Enum: values must match labels from resource kp://field-options (field_key: kp_product_team_id). e.g. "Digital Product". |
| `kp_rx_team` | `string` | RX team label,Optional, Enum: values must match labels from resource kp://field-options (field_key: kp_rx_team_code).e.g. "RBX", "Not Required". |
| `kp_supporting_doc_list` | `array | null` | Supporting document URLs. |
| `kp_target_impact` | `number` | Target impact , optional, unit: USD. |
| `kp_target_impact_summary` | `string` | Target impact summary,Mandatory. free text. |
| `kp_tech_lead_emails` | `array | null` | Tech lead emails. Optional. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_tech_pic_emails` | `array | null` | Tech PIC emails. Mandatory. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_tech_team` | `string` | Tech team label,Mandatory when KpType is "Technical".Enum: values must match labels from resource kp://field-options (field_key: kp_tech_team_id). e.g. "Marketplace Core". |
| `kp_type` | `string` | KP type , Mandatory. Enum: values must match labels from resource kp://field-options (field_key: kp_type_code). e.g. "Business" or "Technical". |

#### `key_project_get`
Get the complete detail of a single Key Project in one call: basic info, team assignments, milestones, supporting kps, and KP linkages. Provide either key_project_id (faster) or kp_key (e.g. KP-1234). All enum fields (kp_type, kp_status, kp_category, kp_markets, kp_product_team, kp_tech_team, kp_target_quarter, etc.) are returned as human-readable labels. Read the kp://field-options resource to see all valid label values. Use kp_audit_log separately if you need the field-change history.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `key_project_id` | `integer` | Physical KP ID. Preferred if known; avoids an extra FuzzSearch lookup. |
| `kp_key` | `string` | KP key, e.g. KP-1234. Used when key_project_id is unavailable. Use Upper Case. |

#### `key_project_get_comments`
Get all comments and replies for a Key Project in a tree structure. Provide key_project_id (faster) or kp_key (e.g. KP-1234). The body field of each comment is HTML-formatted text.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `key_project_id` | `integer` | Physical numeric ID of the key project. |
| `kp_key` | `string` | Unique key of the key project (e.g. KP-1234). |

#### `key_project_impact_update`
Update impact Information For a single Key Project in one call: target_impact,actual_impact , key_project_id or kp_key is required

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `change_reason` | `string` | Change Reason, Mandatory when you want to modify Target impact or Actual impact. free text. |
| `key_project_id` | `integer` | Physical KP ID. Preferred if known. |
| `kp_actual_impact` | `number` | Actual impact , optional, unit: USD.. |
| `kp_actual_impact_summary` | `string` | Actual impact summary, optional. free text. |
| `kp_key` | `string` | KP key, e.g. KP-1234. Case-insensitive. |
| `kp_target_impact` | `number` | Target impact , optional, unit: USD. |
| `kp_target_impact_summary` | `string` | Target impact summary,optional. free text. |

#### `key_project_move_forward`
Move a Key Project forward to the next status stage. Check is_able_to_move_kp_forward from key_project_get before calling. Provide either key_project_id (faster) or kp_key (e.g. KP-1234).

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `key_project_id` | `integer` | Physical KP ID. Preferred if known; avoids an extra FuzzSearch lookup. |
| `kp_key` | `string` | KP key, e.g. KP-1234. Used when key_project_id is unavailable. |

#### `key_project_planned_effort_set`
Set all the teams' plan effort For a single Key Project in one call: will override all teams' plan effortTeam Name enum fields (tech_team_name, algo_team_name) must provide human-readable labels. Read the kp://field-options resource to see all valid label values.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `algo_efforts` | `array | null` | Effort data for algo teams |
| `change_reason` | `string` | Change Reason, Mandatory. free text. |
| `eng_efforts` | `array | null` | Effort data for tech teams |
| `key_project_id` | `integer` | Physical KP ID. Preferred if known. |
| `kp_key` | `string` | KP key, e.g. KP-1234. Case-insensitive. |

#### `key_project_roll_back`
Roll a Key Project back to the previous status stage. Check is_able_to_roll_kp_back from key_project_get before calling. Provide either key_project_id (faster) or kp_key (e.g. KP-1234).

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `key_project_id` | `integer` | Physical KP ID. Preferred if known; avoids an extra FuzzSearch lookup. |
| `kp_key` | `string` | KP key, e.g. KP-1234. Used when key_project_id is unavailable. |

#### `key_project_search`
Search Key Projects with filters and pagination. Enum filter fields (kp_type_list, kp_status_list, kp_category_code_list, kp_rx_team_code_list, kp_product_team_id_list, kp_tech_team_id_list, kp_target_quarter_id_list, linked_request_business_line_id_list) accept human-readable label strings. Read the kp://field-options resource first to find the exact valid labels for each field. Result fields (kp_type, kp_status, kp_markets, etc.) are also returned as human-readable labels.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `eta_end` | `string` | ETA range end. Format: YYYY-MM-DD. |
| `eta_start` | `string` | ETA range start. Format: YYYY-MM-DD. |
| `kp_business_line_pic_list` | `array | null` | Free-form filter by business line PIC emails. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_category_code_list` | `array | null` | Enum: values must match labels from resource kp://field-options (field_key: kp_category_code). e.g. ["Growth", "Efficiency"]. |
| `kp_description` | `string` | Free-form partial match on KP description text. |
| `kp_ids` | `array | null` | Free-form filter by physical KP IDs. e.g. [23,36] |
| `kp_keys` | `array | null` | Free-form filter by KP keys, e.g. ["KP-1234"]. Resolved to IDs via FuzzSearch; not-found keys are skipped. |
| `kp_owner_list` | `array | null` | Free-form filter by owner staff emails. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_pm_lead_list` | `array | null` | Free-form filter by PM lead emails. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_pm_pic_list` | `array | null` | Free-form filter by PM PIC emails. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_product_team_id_list` | `array | null` | Enum: values must match labels from resource kp://field-options (field_key: kp_product_team_id). e.g. ["Digital Product", "ShopeePay"]. |
| `kp_rx_team_code_list` | `array | null` | Enum: values must match labels from resource kp://field-options (field_key: kp_rx_team_code). e.g. ["RBX"]. |
| `kp_status_list` | `array | null` | Enum: values must match labels from resource kp://field-options (field_key: kp_status_code). e.g. ["Ongoing", "Delivered"]. |
| `kp_target_quarter_id_list` | `array | null` | Enum: values must match labels from resource kp://field-options (field_key: kp_target_quarter_id). e.g. ["2025 Q1", "2025 Q2"]. |
| `kp_tech_lead_list` | `array | null` | Free-form filter by tech lead emails. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_tech_pic_list` | `array | null` | Free-form filter by tech PIC emails. e.g. ["user@shopee.com", "h@shopee.com"] |
| `kp_tech_team_id_list` | `array | null` | Enum: values must match labels from resource kp://field-options (field_key: kp_tech_team_id). e.g. ["Marketplace Core"]. |
| `kp_type_list` | `array | null` | Enum: values must match labels from resource kp://field-options (field_key: kp_type_code). e.g. ["Business"] or ["Technical"]. |
| `linked_request_business_line_id_list` | `array | null` | Enum: values must match labels from resource kp://field-options (field_key: business_line_id). e.g. ["BD", "MKT"]. |
| `linked_request_issue_key_list` | `array | null` | Free-form filter by linked request issue keys. e.g. ["SPCPM-0000001"] |
| `page_num` | `integer` | Page number, 1-based. Defaults to 1. |
| `page_size` | `integer` | Page size. Defaults to 20. |
| `submission_time_end` | `string` | Submission date range end. Format: YYYY-MM-DD. |
| `submission_time_start` | `string` | Submission date range start. Format: YYYY-MM-DD. |

#### `kp_audit_log`
Get the paginated field-change history for a single Key Project. Each entry shows the operator, change type, old/new values, and timestamp.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `key_project_id` | `integer` | Physical KP ID. Preferred if known. |
| `kp_key` | `string` | KP key, e.g. KP-1234. Case-insensitive. |
| `page_num` | `integer` | Page number, 1-based. Defaults to 1. |
| `page_size` | `integer` | Page size. Defaults to 20. |

#### `supporting_key_project_create`
Create a new Supporting Key Project under a parent main KP. Provide parent_main_kp_id (faster) or parent_kp_key (e.g. KP-1234). skp_name, skp_product_team, and skp_eta are mandatory.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `parent_kp_key` | `string` | Key of the parent main KP, e.g. KP-1234. Used when parent_main_kp_id is unavailable. |
| `parent_main_kp_id` | `integer` | Physical ID of the parent main KP. Preferred if known. |
| `skp_business_pic_emails` | `array | null` | Business PIC emails. Optional. e.g. ["user@shopee.com"]. |
| `skp_description` | `string` | Supporting KP description. Optional. Free text. |
| `skp_eta` | `string` | Estimated delivery date. Mandatory. Format: YYYY-MM-DD. |
| `skp_markets` | `array | null` | Market labels. Optional. Enum: values must match labels from resource kp://field-options (field_key: kp_market). e.g. ["SG", "MY"]. |
| `skp_name` | `string` | Supporting KP title. Mandatory. Free text. |
| `skp_pm_pic_emails` | `array | null` | PM PIC emails. Optional. e.g. ["user@shopee.com"]. |
| `skp_product_team` | `string` | Product team label. Mandatory. Enum: values must match labels from resource kp://field-options (field_key: kp_product_team_id). e.g. "Digital Product". |
| `skp_rx_team` | `string` | RX team label. Optional. Enum: values must match labels from resource kp://field-options (field_key: kp_rx_team_code). e.g. "RBX". Defaults to Not Required. |
| `skp_tech_lead_emails` | `array | null` | Tech lead emails. Optional. e.g. ["user@shopee.com"]. |
| `skp_tech_pic_emails` | `array | null` | Tech PIC emails. Optional. e.g. ["user@shopee.com"]. |
| `skp_tech_team` | `string` | Tech team label. Optional. Enum: values must match labels from resource kp://field-options (field_key: kp_tech_team_id). e.g. "Marketplace Core". |

#### `supporting_key_project_remove`
Remove a Supporting Key Project. Provide supporting_kp_id (faster) or skp_key to identify it. This action is irreversible.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `skp_key` | `string` | Supporting KP key, e.g. SKP-1234. Used when supporting_kp_id is unavailable. |
| `supporting_kp_id` | `integer` | Physical ID of the supporting KP to remove. Preferred if known. |

#### `supporting_key_project_update`
Update an existing Supporting Key Project. Provide supporting_kp_id (faster) or skp_key to identify it. Only fields provided will be updated. change_reason is mandatory when modifying skp_eta.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `change_reason` | `string` | Reason for the change. Mandatory when modifying SkpEta. Free text. |
| `skp_business_pic_emails` | `array | null` | Business PIC emails. Optional. e.g. ["user@shopee.com"]. |
| `skp_description` | `string` | Supporting KP description. Optional. Free text. |
| `skp_eta` | `string` | Estimated delivery date. Optional. Format: YYYY-MM-DD. |
| `skp_key` | `string` | Supporting KP key, e.g. SKP-1234. Used when supporting_kp_id is unavailable. |
| `skp_markets` | `array | null` | Market labels. Optional. Enum: values must match labels from resource kp://field-options (field_key: kp_market). e.g. ["SG", "MY"]. |
| `skp_name` | `string` | Supporting KP title. Optional. Free text. |
| `skp_pm_pic_emails` | `array | null` | PM PIC emails. Optional. e.g. ["user@shopee.com"]. |
| `skp_product_team` | `string` | Product team label. Optional. Enum: values must match labels from resource kp://field-options (field_key: kp_product_team_id). e.g. "Digital Product". |
| `skp_rx_team` | `string` | RX team label. Optional. Enum: values must match labels from resource kp://field-options (field_key: kp_rx_team_code). e.g. "RBX". Defaults to Not Required. |
| `skp_tech_lead_emails` | `array | null` | Tech lead emails. Optional. e.g. ["user@shopee.com"]. |
| `skp_tech_pic_emails` | `array | null` | Tech PIC emails. Optional. e.g. ["user@shopee.com"]. |
| `skp_tech_team` | `string` | Tech team label. Optional. Enum: values must match labels from resource kp://field-options (field_key: kp_tech_team_id). e.g. "Marketplace Core". |
| `supporting_kp_id` | `integer` | Physical ID of the supporting KP. Preferred if known. |

### `llm_request`

#### `llm_request_audit_log_list`
List the paginated audit log (field change history) for a POP LLM Request. Provide either request_id (faster) or request_key (e.g. LLM-123456).

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `page_num` | `integer` | Page number, 1-based. Defaults to 1. |
| `page_size` | `integer` | Page size. Defaults to 20. |
| `request_id` | `integer` | Physical ID of the LLM request. Preferred if known; avoids an extra lookup call. |
| `request_key` | `string` | LLM request key, e.g. LLM-123456. |

#### `llm_request_get`
Get the complete detail of a single POP LLM Request in one call: full general info plus all product-line solutions with their linked Jira epics. Provide either request_id (faster) or request_key (e.g. LLM-123456). Use llm_request_audit_log_list separately if you need the field-change history.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `request_id` | `integer` | Physical ID of the LLM request. Preferred if known; avoids an extra FuzzSearch lookup call. |
| `request_key` | `string` | LLM request key, e.g. LLM-123456. Used when request_id is unavailable. |

#### `llm_request_get_comments`
Get all comments and replies for a POP LLM Request in a tree structure. Provide request_id (faster) or request_key. The body field of each comment is HTML-formatted text.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `request_id` | `integer` | Physical numeric ID of the LLM request. |
| `request_key` | `string` | Unique key of the LLM request. |

#### `llm_request_search`
Search POP LLM Requests with filters and pagination. Supports filtering by request ID/key, name, status, review type, request type, product type, priority, target country, submission cycle, business line, assignees, and submission date range.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `business_labels` | `array | null` | UI: 'Business Labels'. Free-form tags. |
| `business_lines` | `array | null` | UI: 'Business Line'. Enum: values must match labels from resource llm://field-options (field_key: business_line_id). e.g. ["BD", "MKT", "OPS"]. |
| `business_review_priorities` | `array | null` | UI: 'Business Review Priority'. Enum: values must match labels from resource llm://field-options (field_key: business_review_priority_code). e.g. ["P0", "P1"]. |
| `current_assignees` | `array | null` | UI: 'Current Assignee'. Free-form: must be staff email addresses (e.g. user@shopee.com). Name is not accepted by the API. |
| `main_product_lines` | `array | null` | UI: 'Main Product Line'. Enum: values must match labels from resource llm://field-options (field_key: product_line_id). e.g. ["Cart", "Checkout"]. |
| `page_num` | `integer` | Page number, 1-based. Defaults to 1. |
| `page_size` | `integer` | Page size. Defaults to 20. |
| `priorities` | `array | null` | UI: 'Priority'. Enum: values must match labels from resource llm://field-options (field_key: priority_code). e.g. ["P0", "P1"]. |
| `request_ids` | `array | null` | UI: 'Request ID'. Free-form filter by request keys, e.g. ["LLM-123456"]. |
| `request_name` | `string` | UI: 'Request Name'. Free-form partial match on the request title. |
| `request_product_types` | `array | null` | UI: 'Request Product Type'. Enum: values must match labels from resource llm://field-options (field_key: request_product_type_code). Only the first value is used. e.g. ["LLM Project"]. |
| `request_types` | `array | null` | UI: 'Request Type'. Enum: values must match labels from resource llm://field-options (field_key: request_type_code). e.g. ["Local Initiative", "Reg LLM Initiative"]. |
| `review_types` | `array | null` | UI: 'Review Type'. Enum: values must match labels from resource llm://field-options (field_key: review_type_code). e.g. ["Roadmap", "Urgent"]. |
| `statuses` | `array | null` | UI: 'Request Status'. Enum: values must match labels from resource llm://field-options (field_key: request_status_code). e.g. ["Developing", "UAT", "Live"]. |
| `submission_cycles` | `array | null` | UI: 'Submission Cycle'. Enum: values must match labels from resource llm://field-options (field_key: submission_cycle_code). e.g. ["Feb 2025", "Mar 2025"]. |
| `submission_date_end` | `string` | UI: 'Submission Date' range end. Format: YYYY-MM-DD. |
| `submission_date_start` | `string` | UI: 'Submission Date' range start. Format: YYYY-MM-DD. |
| `supporting_product_lines` | `array | null` | UI: 'Supporting Product Line'. Enum: values must match labels from resource llm://field-options (field_key: product_line_id). e.g. ["PDP"]. |
| `target_countries` | `array | null` | UI: 'Target Country'. Enum: values must match labels from resource llm://field-options (field_key: target_country_code). e.g. ["SG", "MY", "TH"]. |

### `data_request`

#### `data_request_audit_log_list`
List the paginated audit log (field change history) for a POP Data Request. Provide either data_request_id (faster) or request_key (e.g. DATA-000123).

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `data_request_id` | `integer` | Physical ID of the data request. Preferred if known; avoids an extra lookup call. |
| `page_num` | `integer` | Page number, 1-based. Defaults to 1. |
| `page_size` | `integer` | Page size. Defaults to 20. |
| `request_key` | `string` | Data request key, e.g. DATA-000123. |

#### `data_request_get`
Get the complete detail of a single POP Data Request in one call: full general info plus all embedded solutions with their Jira components and linked issues. Provide either data_request_id (faster) or request_key (e.g. DATA-000123). Use data_request_audit_log_list separately if you need the field-change history.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `data_request_id` | `integer` | Physical ID of the data request. Preferred if known; avoids an extra FuzzSearch lookup call. |
| `request_key` | `string` | Data request key, e.g. DATA-000123. Used when data_request_id is unavailable. |

#### `data_request_get_comments`
Get all comments and replies for a POP Data Request in a tree structure. Provide data_request_id (faster) or request_key. The body field of each comment is HTML-formatted text.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `data_request_id` | `integer` | Physical numeric ID of the data request. |
| `request_key` | `string` | Unique key of the data request. |

#### `data_request_search`
Search POP Data Requests with filters and pagination. Supports filtering by request ID/key, name, status, review type, request type, data mart, priority, target country, submission cycle, regional approval status/priority, business line, assignees, market-specific flag, and date ranges.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `business_labels` | `array | null` | UI: 'Business Labels'. Free-form tags. |
| `business_lines` | `array | null` | UI: 'Business Line'. Enum: values must match labels from resource data://field-options (field_key: business_line_config_id). e.g. ["POP", "OPS"]. |
| `current_assignees` | `array | null` | UI: 'Current Assignee'. Free-form: must be staff email addresses (e.g. user@shopee.com). Name is not accepted by the API. |
| `data_marts` | `array | null` | UI: 'Data Mart'. Enum: values must match labels from resource data://field-options (field_key: data_mart_config_id). e.g. ["Order Data Mart"]. |
| `market_specific_request` | `string` | UI: 'Market Specific Request'. Fixed values: 'Yes' or 'No'. |
| `page_num` | `integer` | Page number, 1-based. Defaults to 1. |
| `page_size` | `integer` | Page size. Defaults to 20. |
| `regional_approval_statuses` | `array | null` | UI: 'Regional Approval Status'. Enum: values must match labels from resource data://field-options (field_key: regional_approval_status_code). e.g. ["Approved", "Rejected"]. |
| `regional_approval_time_end` | `string` | UI: 'Regional Approval Date' range end. Format: YYYY-MM-DD. |
| `regional_approval_time_start` | `string` | UI: 'Regional Approval Date' range start. Format: YYYY-MM-DD. |
| `regional_priorities` | `array | null` | UI: 'Regional Priority'. Enum: values must match labels from resource data://field-options (field_key: regional_priority_code). e.g. ["P0", "P1"]. |
| `request_keys` | `array | null` | UI: 'Request ID'. Free-form filter by request keys, e.g. ["DATA-000123"]. |
| `request_name` | `string` | UI: 'Request Name'. Free-form partial match on the request title. |
| `request_priorities` | `array | null` | UI: 'Request Priority'. Enum: values must match labels from resource data://field-options (field_key: request_priority_code). e.g. ["P0", "P1"]. |
| `request_types` | `array | null` | UI: 'Request Type'. Enum: values must match labels from resource data://field-options (field_key: request_type_code). e.g. ["Local Initiative", "Regional Business Initiative"]. |
| `review_types` | `array | null` | UI: 'Review Type'. Enum: values must match labels from resource data://field-options (field_key: review_type_code). e.g. ["Roadmap", "Urgent"]. |
| `statuses` | `array | null` | UI: 'Request Progress'. Enum: values must match labels from resource data://field-options (field_key: request_status_code). e.g. ["Developing", "Live", "UAT"]. |
| `submission_cycles` | `array | null` | UI: 'Submission Cycle'. Enum: values must match labels from resource data://field-options (field_key: submission_cycle_code). e.g. ["Cycle 10 - 2025-05-01 to 2025-05-31"]. |
| `submit_time_end` | `string` | UI: 'Submission Date' range end. Format: YYYY-MM-DD. |
| `submit_time_start` | `string` | UI: 'Submission Date' range start. Format: YYYY-MM-DD. |
| `supporting_data_marts` | `array | null` | UI: 'Supporting Data Mart'. Enum: values must match labels from resource data://field-options (field_key: data_mart_config_id). e.g. ["MPI&D - Order Mart"]. |
| `target_countries` | `array | null` | UI: 'Target Country'. Enum: values must match labels from resource data://field-options (field_key: target_country_code). e.g. ["SG", "MY", "TH"]. |

### `model_request`

#### `model_request_audit_log_list`
List the paginated audit log (field change history) for a POP Model Request. Provide either model_request_id (faster) or model_request_key (e.g. MODEL-123456).

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `model_request_id` | `integer` | Physical ID of the model request. Preferred if known; avoids an extra lookup call. |
| `model_request_key` | `string` | Model request key, e.g. MODEL-123456. |
| `page_num` | `integer` | Page number, 1-based. Defaults to 1. |
| `page_size` | `integer` | Page size. Defaults to 20. |

#### `model_request_get`
Get the complete detail of a single POP Model Request in one call: full general info (status, priority, product lines, team, dates, background, requirements, etc.) plus all product-line solutions with their linked Jira epics. Provide either model_request_id (faster) or model_request_key (e.g. MODEL-123456). Use model_request_audit_log_list separately if you need the field-change history.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `model_request_id` | `integer` | Physical ID of the model request. Preferred if known; avoids an extra lookup call. |
| `model_request_key` | `string` | Model request key, e.g. MODEL-123456. Used when model_request_id is unavailable. |

#### `model_request_get_comments`
Get all comments and replies for a POP Model Request in a tree structure. Provide model_request_id (faster) or model_request_key (e.g. MODEL-123456). The body field of each comment is HTML-formatted text.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `model_request_id` | `integer` | Physical numeric ID of the model request. Faster than model_request_key. |
| `model_request_key` | `string` | Unique key of the model request (e.g. MODEL-123456). |

#### `model_request_search`
Search POP Model Requests with filters and pagination. Supports filtering by request ID/key, name, status, review type, submission cycle, target country, priority, product line, assignee, market-specific flag, and submission date range.

Required: none

| Parameter | Type | Notes |
|---|---|---|
| `business_priorities` | `array | null` | UI: 'Business Priority'. Enum: values must match labels from resource model://field-options (field_key: priority_code). e.g. ["P0", "P1"]. |
| `current_assignees` | `array | null` | UI: 'Current Assignee'. Free-form: must be staff email addresses (e.g. user@shopee.com). Name is not accepted by the API. |
| `main_product_lines` | `array | null` | UI: 'Main Product Line'. Enum: values must match labels from resource model://field-options (field_key: model_product_line_id). e.g. ["Cart", "Checkout"]. |
| `market_specific_request` | `string` | UI: 'Market Specific Request'. Fixed values: 'Yes' or 'No'. |
| `model_request_ids` | `array | null` | UI: 'Request ID'. Free-form filter by model request keys, e.g. ["MODEL-123456"]. |
| `model_request_name` | `string` | UI: 'Request Name'. Free-form partial match on the model request title. |
| `page_num` | `integer` | Page number, 1-based. Defaults to 1. |
| `page_size` | `integer` | Page size. Defaults to 20. |
| `request_priorities` | `array | null` | UI: 'Request Priority'. Enum: values must match labels from resource model://field-options (field_key: priority_code). e.g. ["P0", "P1"]. |
| `review_types` | `array | null` | UI: 'Review Type'. Enum: values must match labels from resource model://field-options (field_key: review_type_code). e.g. ["Roadmap", "Urgent"]. |
| `statuses` | `array | null` | UI: 'Request Progress'. Enum: values must match labels from resource model://field-options (field_key: model_request_status). e.g. ["Developing", "UAT", "Live"]. |
| `submission_cycles` | `array | null` | UI: 'Request Submission Cycle'. Enum: values must match labels from resource model://field-options (field_key: submission_cycle_code). e.g. ["Cycle 10 - 2025-05-01 to 2025-05-31"]. |
| `submission_date_end` | `string` | UI: 'Submission Date' range end. Format: YYYY-MM-DD. |
| `submission_date_start` | `string` | UI: 'Submission Date' range start. Format: YYYY-MM-DD. |
| `supporting_product_lines` | `array | null` | UI: 'Supporting Product Line'. Enum: values must match labels from resource model://field-options (field_key: model_product_line_id). e.g. ["PDP"]. |
| `target_countries` | `array | null` | UI: 'Target Country'. Enum: values must match labels from resource model://field-options (field_key: region). e.g. ["SG", "MY", "TH"]. |

This is a backend runtime helper injected by Hangar. It is not a local Python package in a plain dev environment.
## Quick examples

- `detail = pop.feature_request_detail_get("SPCPM-123456")`
- `rows = pop.feature_request_search(request_name="checkout", page_num=1, page_size=10)`
- `comments = pop.call_tool("feature_request", "feature_request_get_comments", {"issue_key": "SPCPM-123456"})`

## Related capabilities

- `backend.integrations`
- `backend.integration.platform`
