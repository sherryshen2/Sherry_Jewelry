from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from dashboard.csv_source import read_csv_bytes
from dashboard.datasuite_source import read_datasuite
from dashboard.gsheet_source import read_google_sheet

router = APIRouter()


class GoogleSheetRequest(BaseModel):
    spreadsheet: str = Field(min_length=1)
    range_name: str = "Sheet1!A:ZZ"


class DatasuiteRequest(BaseModel):
    api_name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    scope: list[str] = Field(default_factory=list)
    parameters: dict = Field(default_factory=dict)
    enable_cache: bool = True


def dataset_response(dataset):
    return {"ok": True, "dataset": dataset.payload()}


@router.post("/csv")
async def load_csv(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one CSV file")
    datasets = []
    errors = []
    for uploaded in files:
        name = uploaded.filename or "upload.csv"
        try:
            datasets.append(read_csv_bytes(name, await uploaded.read()).payload())
        except Exception as exc:
            errors.append({"name": name, "error": str(exc)})
    return {"ok": bool(datasets), "datasets": datasets, "errors": errors}


@router.post("/google-sheet")
def load_google_sheet(payload: GoogleSheetRequest):
    try:
        return dataset_response(read_google_sheet(payload.spreadsheet, payload.range_name))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/datasuite")
def load_datasuite(payload: DatasuiteRequest):
    try:
        return dataset_response(read_datasuite(
            api_name=payload.api_name,
            version=payload.version,
            scope=payload.scope,
            parameters=payload.parameters,
            enable_cache=payload.enable_cache,
        ))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
