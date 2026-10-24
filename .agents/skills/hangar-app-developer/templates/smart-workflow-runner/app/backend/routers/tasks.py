from fastapi import APIRouter, HTTPException

from hangarkit import ctx

from schemas import ContinueInterruptRequest, CreateTaskRequest
from services import smart_client, task_poller, task_store

router = APIRouter(prefix="/tasks", tags=["tasks"])


def task_or_404(task_id: str):
    try:
        return task_store.get_task(task_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Workflow task not found.") from exc


@router.get("/{task_id}")
def get_task(task_id: str):
    return {"task": task_or_404(task_id)}


@router.post("")
def create_task(payload: CreateTaskRequest):
    task = task_store.create_task(payload.title.strip(), payload.input_variables, payload.file_assets)
    try:
        invocation = smart_client.invoke_async(payload.input_variables, ctx.user_email or ctx.user or "")
        task = task_store.update_task(task["id"], {
            "status": "running",
            "smart_thread_id": invocation["thread_id"],
            "last_polled_at": task_store.now(),
            "progress_percent": 1,
        })
    except smart_client.SmartWorkflowError as exc:
        task = task_store.update_task(task["id"], {
            "status": "failed",
            "error_messages": [str(exc)],
            "completed_at": task_store.now(),
        })
        raise HTTPException(status_code=502, detail="SMART could not start the workflow. The failed task was recorded.") from exc
    return {"task": task}


@router.post("/{task_id}/refresh")
def refresh_task(task_id: str):
    task = task_or_404(task_id)
    try:
        return {"task": task_poller.refresh_task(task)}
    except smart_client.SmartWorkflowError as exc:
        task = task_store.update_task(task_id, {"error_messages": [str(exc)], "last_polled_at": task_store.now()})
        return {"task": task}


@router.post("/{task_id}/continue-interrupt")
def continue_interrupt(task_id: str, payload: ContinueInterruptRequest):
    task = task_or_404(task_id)
    if str(task.get("status") or "") != "interrupted":
        raise HTTPException(status_code=409, detail="This task is not waiting for an interrupt response.")
    try:
        smart_client.continue_interrupt(task["smart_thread_id"], payload.interrupt_type, payload.interrupt_command, ctx.user_email or ctx.user or "")
        return {"task": task_store.update_task(task_id, {"status": "running", "interrupt": None, "last_polled_at": task_store.now()})}
    except smart_client.SmartWorkflowError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
