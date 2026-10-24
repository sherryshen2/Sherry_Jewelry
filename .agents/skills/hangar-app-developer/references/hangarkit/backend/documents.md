# Document conversion

ID: `backend.documents`
Category: `backend`

Convert supported office documents to PDF through Hangar's private, LibreOffice-backed worker.

## Import

`from hangarkit import documents`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `documents.convert(content, filename="report.docx", target_format="pdf")`
- `await documents.convert_upload(upload, target_format="pdf")`

## Details

Use `documents` when an app backend must convert a user-provided office document to PDF. Hangar verifies the backend token, forwards the bytes to its private document worker, and audits the conversion request. LibreOffice is installed only in that dedicated worker; individual app backend Docker images do not contain it.

The app supplies a filename so Hangar can determine the source format. It does not supply an authoritative input MIME type. The current supported source extensions are `doc`, `docx`, `odt`, `rtf`, `txt`, `xls`, `xlsx`, `ods`, `csv`, `ppt`, `pptx`, and `odp`; the only output format is `pdf`.

For a FastAPI upload route, use the async helper:

```python
from fastapi import APIRouter, UploadFile
from fastapi.responses import Response
from hangarkit import documents

router = APIRouter()

@router.post("/convert")
async def convert_file(upload: UploadFile):
    result = await documents.convert_upload(upload)
    return Response(
        result.content,
        media_type=result.content_type,
        headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
    )
```

For already-available bytes, call `documents.convert()` directly:

```python
from hangarkit import documents

result = documents.convert(source_bytes, filename="quarterly-report.xlsx")
```

The platform limits input/output size, concurrency, and conversion time. A missing worker configuration, an unsupported source type, or a failed conversion raises `documents.DocumentConversionError`. Do not invoke `soffice` directly from app code.
## Quick examples

- `result = await documents.convert_upload(upload); return Response(result.content, media_type=result.content_type)`

## Related capabilities

- `backend.hangarkit`
- `runtime.routing`
