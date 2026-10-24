import os
from typing import Any

import httpx

SMART_BASE_URL = "https://smart.shopee.io/apis/smart/v1"


class SmartWorkflowError(RuntimeError):
    pass


def _credentials() -> tuple[str, str]:
    hash_id = os.getenv("SMART_ENDPOINT_DEPLOYMENT_HASH_ID", "").strip()
    endpoint_key = os.getenv("SMART_ENDPOINT_DEPLOYMENT_KEY", "").strip()
    if not hash_id or not endpoint_key:
        raise SmartWorkflowError("SMART endpoint credentials are not configured. Update the app secrets and redeploy the backend.")
    return hash_id, endpoint_key


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = httpx.post(f"{SMART_BASE_URL}{path}", json=payload, timeout=httpx.Timeout(30.0, connect=10.0))
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SmartWorkflowError(f"SMART request failed: {exc}") from exc
    try:
        body = response.json()
    except ValueError as exc:
        raise SmartWorkflowError("SMART returned an invalid JSON response.") from exc
    if not isinstance(body, dict):
        raise SmartWorkflowError("SMART returned an unexpected response shape.")
    if body.get("status") not in (None, "success") or body.get("code") not in (None, 0):
        message = body.get("error_message") or body.get("error") or "SMART rejected the request."
        raise SmartWorkflowError(str(message))
    return body


def invoke_async(input_variables: dict[str, Any], user_id: str = "") -> dict[str, Any]:
    hash_id, endpoint_key = _credentials()
    body = _post("/workflow_orchestrator/deployments/invoke", {
        "channel": "endpoint_deployment",
        "endpoint_deployment_hash_id": hash_id,
        "endpoint_deployment_key": endpoint_key,
        "mode": "async",
        "start_user_variables": input_variables,
        **({"user_id": user_id} if user_id else {}),
    })
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    if data.get("success") is False:
        raise SmartWorkflowError(str(data.get("error") or "SMART did not start the workflow."))
    thread_id = str(data.get("thread_id") or body.get("thread_id") or "").strip()
    if not thread_id:
        raise SmartWorkflowError("SMART did not return a workflow thread ID.")
    return {"thread_id": thread_id, "response": body}


def get_debug_tree(thread_id: str) -> dict[str, Any]:
    hash_id, endpoint_key = _credentials()
    body = _post("/workflow_orchestrator/get_debug_tree", {
        "channel": "endpoint_deployment",
        "endpoint_deployment_hash_id": hash_id,
        "endpoint_deployment_key": endpoint_key,
        "thread_id": thread_id,
        "session_type": "deployed",
    })
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    tree = data.get("debug_tree")
    if not isinstance(tree, dict):
        raise SmartWorkflowError("SMART did not return a debug tree for this workflow thread.")
    return tree


def continue_interrupt(thread_id: str, interrupt_type: str, interrupt_command: dict[str, Any], user_id: str = "") -> dict[str, Any]:
    hash_id, endpoint_key = _credentials()
    body = _post("/workflow_orchestrator/deployments/continue_interrupt", {
        "channel": "endpoint_deployment",
        "endpoint_deployment_hash_id": hash_id,
        "endpoint_deployment_key": endpoint_key,
        "thread_id": thread_id,
        "interrupt_type": interrupt_type,
        "interrupt_command": interrupt_command,
        "mode": "async",
        **({"user_id": user_id} if user_id else {}),
    })
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    if data.get("success") is False:
        raise SmartWorkflowError(str(data.get("error") or "SMART did not continue the workflow."))
    return body
