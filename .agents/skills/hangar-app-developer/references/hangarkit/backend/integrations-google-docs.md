# Google Docs integration

ID: `backend.integration.google_docs`
Category: `backend`

Create, read, update, and extract text/markdown from Google Docs through Hangar integration auth.

## Import

`from hangarkit.integrations import google_docs`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `google_docs.create_document(title), get_document(document_id_or_url, include_tabs_content=False, fields=None, suggestions_view_mode=None), batch_update(document_id_or_url, requests, write_control=None)`
- `google_docs.list_tabs(...), get_tab(...), get_tab_document(...), get_all_tab_documents(...)`
- `google_docs.get_text(...), get_markdown(...), get_all_tab_text(...), get_all_tab_markdown(...)`
- `google_docs.insert_text(document_id_or_url, text, index=None, tab_id=None, segment_id=None, write_control=None), append_text(document_id_or_url, text, ...), replace_all_text(document_id_or_url, text, replace_text, ...), delete_content_range(document_id_or_url, start_index, end_index, ...)`
- `google_docs.create_paragraph_bullets(...), delete_paragraph_bullets(...)`
- `google_docs.update_text_style(...), update_paragraph_style(...), insert_table(...)`
- `google_docs.add_document_tab(...), update_document_tab(...), delete_tab(...)`
- `google_docs.request(method, path, **kwargs)`

## Details

Use this module for Google Docs API operations from backend code. Hangar handles the integration proxy and configured auth mode.

### Document editing workflow

Every helper accepts a Google document ID or a document URL as `document_id_or_url`. `create_document()` returns the upstream document object; use its `documentId` for later calls. `batch_update()` requires a non-empty list of native Google Docs request objects.

```python
from hangarkit.integrations import google_docs

document = google_docs.create_document("Weekly Notes")
document_id = document["documentId"]
google_docs.append_text(document_id, "Status: green\\n")
google_docs.replace_all_text(document_id, "green", "amber")
google_docs.insert_table(document_id, rows=2, columns=3)
```

`insert_text()` appends when `index` is omitted; otherwise it inserts at that document index. `replace_all_text()` takes the search text before its replacement. Range helpers use `start_index` and `end_index`; pass `tab_id` or `segment_id` only when editing a specific tab or segment. Use `get_text()` or `get_markdown()` for the extracted content rather than parsing a raw document response yourself.
## Quick examples

- `doc = google_docs.create_document("Weekly Notes")`

## Related capabilities

- `backend.integrations`
