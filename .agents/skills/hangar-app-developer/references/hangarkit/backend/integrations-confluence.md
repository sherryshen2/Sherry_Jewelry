# Confluence integration

ID: `backend.integration.confluence`
Category: `backend`

Read and write Confluence pages, content, attachments, and comments from backend code.

## Import

`from hangarkit.integrations import confluence`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `confluence.get_page(page_id, expand="body.storage,version", status=None), get_page_with_version(page_id, version, ...), get_user(username=None, key=None)`
- `confluence.search_pages(query, space_key=None, limit=20, start=0, expand=None), get_child_pages(page_id, limit=None, page_size=25, expand=None), find_existing_page(title, parent_page_id)`
- `confluence.create_page(title, space_key, parent_page_id=None, content="", representation="storage"), update_page(page_id, content, title=None, representation="storage")`
- `confluence.get_page_id(...), get_page_html(...), get_page_markdown(...)`
- `confluence.get_headings(...), get_content_under_headings(...)`
- `confluence.list_attachments(...), upload_attachment(...)`
- `confluence.create_comment(...), update_comment(...)`
- `confluence.request(method, path, **kwargs)`

## Details

Use this module for Confluence content workflows from app backend code.

The module supports app/user integration auth configured by Hangar. Do not copy user tokens into app files.

### Page and attachment workflows

Use Confluence storage-format XHTML for `content` unless the target API accepts another documented `representation`. Creating a page requires a title and space key; updating a page reads its current version and increments it automatically.

```python
from hangarkit.integrations import confluence

page = confluence.create_page(
    title="Runbook",
    space_key="ENG",
    parent_page_id="123456",  # optional
    content="<p>Initial runbook content.</p>",
)
confluence.update_page(page["id"], "<p>Revised content.</p>", title="Runbook")
confluence.upload_attachment(page["id"], "notes.txt", b"details", content_type="text/plain")
```

`upload_attachment(page_id, filename, content, content_type=None, comment=None)` accepts bytes or file-like content. Use `create_comment(page_id, comment, representation="storage")` and `update_comment(comment_id, comment, version=None, representation="storage")` for page comments. Read helpers return upstream Confluence objects unchanged.
## Quick examples

- `page = confluence.get_page_markdown(page_id)`

## Related capabilities

- `backend.integrations`
