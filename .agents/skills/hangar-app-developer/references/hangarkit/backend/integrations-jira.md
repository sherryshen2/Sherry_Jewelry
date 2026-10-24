# Jira integration

ID: `backend.integration.jira`
Category: `backend`

Search, read, create, update, transition, comment on, and attach files to Jira issues.

## Import

`from hangarkit.integrations import jira`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `jira.search(jql, start_at=0, max_results=50, fields=None, expand=None), jql(**filters), search_all(jql, limit=100, fields=None, expand=None, ...), search_all_with_comments(jql, limit=100, fields=None), search_all_with_changelog(jql, limit=100, fields=None, expand=None)`
- `jira.search_my_open_issues(project=None, limit=100, fields=None, expand=None, order_by="updated DESC"), get_issue(issue_key, fields=None, expand=None), get_issue_with_changelog(issue_key, fields=None, expand=None), create_issue(fields=None, project_key=None, issue_type=None, summary=None, ...)`
- `jira.update_issue(issue_key, fields=None, update=None, notify_users=None, **field_values), assign_issue(issue_key, assignee), update_developer(issue_key, developer, field_id), update_custom_field(issue_key, field_id, value), update_assignee_and_developer(issue_key, assignee, developer_field_id=None)`
- `jira.get_transitions(...), transition_issue(...)`
- `jira.get_fields(...), get_create_issue_fields(...), get_projects(...), get_project(...), get_issue_types(...)`
- `jira.link_issue(...), get_user(...), find_users(...), user_for_email(...)`
- `jira.get_watchers(...), get_people_involved(...), issue_to_text(...)`
- `jira.add_comment(...), create_comment(...), comment_exists(...), add_comment_once(...), get_comments(...), get_comment(...), update_comment(...), delete_comment(...)`
- `jira.add_attachment(...), add_attachments(...)`
- `jira.quote_jql(...), jira.my_open_issues_jql(...)`
- `jira.request(method, path, **kwargs)`

## Details

Use this module for Jira workflows from backend code. Prefer helper methods over raw REST calls where possible.

### Issue and comment workflow

`create_issue()` accepts either a complete Jira `fields` object or convenient keyword values such as `project_key`, `issue_type`, `summary`, `description`, `assignee`, `labels`, and `priority`. Supply the field IDs returned by `get_create_issue_fields()` for project-specific custom fields.

```python
from hangarkit.integrations import jira

issue = jira.create_issue(
    project_key="ENG",
    issue_type="Task",
    summary="Investigate checkout latency",
    description="Trace the increase after the latest deploy.",
    labels=["performance"],
)
jira.add_comment(issue["key"], "Investigation started.")
jira.transition_issue(issue["key"], transition="31")
```

`update_issue()` requires `fields`, `update`, or one or more field keyword values. `transition_issue(issue_key, transition, fields=None, update=None, history_metadata=None)` accepts a transition ID string or a Jira transition object. Comments use `add_comment(issue_key, body)`, `update_comment(issue_key, comment_id, body)`, and `delete_comment(issue_key, comment_id)`; attachments use `add_attachment(issue_key, filename, content, content_type=None)`.
## Quick examples

- `issue = jira.get_issue("ABC-123")`
- `items = jira.search_my_open_issues()`

## Related capabilities

- `backend.integrations`
