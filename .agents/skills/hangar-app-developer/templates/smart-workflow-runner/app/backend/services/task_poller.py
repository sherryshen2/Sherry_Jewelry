from datetime import datetime
import json
from typing import Any, Optional

from . import smart_client, task_store


TERMINAL_STATUSES = {"success", "failed", "skipped", "cancelled"}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _first_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ("message", "error_message", "detail", "error"):
            text = _first_text(value.get(key))
            if text:
                return text
    return ""


def _normalise_error(value: Any) -> str:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (TypeError, ValueError):
            return value.strip()
        return _normalise_error(decoded)
    if isinstance(value, dict):
        message = _first_text(value)
        if message:
            return message
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return _first_text(value)


def _humanise_error(value: Any) -> str:
    message = _normalise_error(value)
    lowered = message.lower()
    if "rate limit" in lowered or "too many request" in lowered or "429" in lowered:
        return "Rate limit reached. Retry after the provider's cooldown."
    if "timeout" in lowered or "timed out" in lowered or "deadline exceeded" in lowered:
        return "Execution timed out before SMART received a response."
    if "tool" in lowered and any(token in lowered for token in ("fail", "error", "invoke", "call")):
        return f"Tool invocation failed: {message}"
    if any(token in lowered for token in ("llm", "model", "gateway")) and any(token in lowered for token in ("fail", "error", "unavailable")):
        return f"LLM provider error: {message}"
    return message


def _find_business_error(value: Any, depth: int = 0) -> Optional[dict[str, Any]]:
    """Find SMART's workflow-level business error convention anywhere in output."""
    if depth > 8:
        return None
    if isinstance(value, dict):
        code = value.get("_business_error_code")
        message = value.get("_business_error_msg")
        if code not in (None, "", 0, "0") or message:
            return {"code": str(code or "business_error"), "message": _first_text(message) or "SMART reported a business error."}
        for child in value.values():
            found = _find_business_error(child, depth + 1)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_business_error(child, depth + 1)
            if found:
                return found
    return None


def _node_details(tree: dict[str, Any]) -> list[dict[str, Any]]:
    summaries = _as_dict(tree.get("node_id_to_summary"))
    raw_debug_details = tree.get("node_debug_details")
    if isinstance(raw_debug_details, list):
        debug_details = {str(item.get("node_id")): item for item in raw_debug_details if isinstance(item, dict) and item.get("node_id") is not None}
    else:
        debug_details = _as_dict(raw_debug_details)
    parallel_details = _as_dict(tree.get("node_id_to_parallel_debug_details"))
    rows: list[dict[str, Any]] = []
    for node_id in sorted(set(summaries) | set(debug_details), key=str):
        summary = _as_dict(summaries.get(node_id))
        detail = _as_dict(debug_details.get(node_id))
        time_info = _as_dict(summary.get("time_info"))
        errors = summary.get("error_messages") or detail.get("error_messages") or detail.get("errors") or []
        if not isinstance(errors, list):
            errors = [errors]
        node_data = _as_dict(detail.get("node_data"))
        def values(params: Any) -> dict[str, Any]:
            return {
                str(name): _as_dict(meta).get("value")
                for name, meta in _as_dict(params).items()
            }
        rows.append({
            "id": str(node_id),
            "name": detail.get("node_name") or detail.get("name") or summary.get("node_name") or f"Node {node_id}",
            "type": detail.get("node_type") or detail.get("type") or summary.get("node_type") or "workflow node",
            "status": str(summary.get("status") or detail.get("status") or "unknown").lower(),
            "latency": time_info.get("latency") or detail.get("latency"),
            "errors": [text for item in errors if (text := _humanise_error(item))],
            "is_parallel": bool(parallel_details.get(node_id) or detail.get("node_id_to_parallel_debug_details")),
            "inputs": values(node_data.get("input_params")),
            "outputs": values(node_data.get("output_params")),
            "structured_output_setting": _as_dict(_as_dict(node_data.get("workflow_graph_node_settings")).get("structured_output_setting")),
        })
        parallel_children = detail.get("node_id_to_parallel_debug_details") or parallel_details.get(node_id)
        if isinstance(parallel_children, dict):
            for child_id, child_raw in parallel_children.items():
                child = _as_dict(child_raw)
                child_data = _as_dict(child.get("node_data"))
                child_errors = child.get("error_messages") or child.get("errors") or []
                if not isinstance(child_errors, list):
                    child_errors = [child_errors]
                rows.append({
                    "id": f"{node_id}.{child.get('node_id') or child_id}",
                    "name": child.get("node_name") or child.get("name") or f"Parallel node {child_id}",
                    "type": child.get("node_type") or child.get("type") or "parallel workflow node",
                    "status": str(child.get("status") or "unknown").lower(),
                    "latency": _as_dict(child.get("time_info")).get("latency") or child.get("latency"),
                    "errors": [text for item in child_errors if (text := _humanise_error(item))],
                    "is_parallel": True,
                    "inputs": values(child_data.get("input_params")),
                    "outputs": values(child_data.get("output_params")),
                    "structured_output_setting": _as_dict(_as_dict(child_data.get("workflow_graph_node_settings")).get("structured_output_setting")),
                })
    edges: list[dict[str, str]] = []
    for raw_edge in tree.get("traversed_edges") or []:
        edge = _as_dict(raw_edge)
        source = edge.get("from_node_id")
        target = edge.get("to_node_id")
        if source is not None and target is not None:
            edges.append({"from": str(source), "to": str(target)})

    # SMART's node summary is a map, not an execution sequence. The traversed
    # graph edges are the authoritative order for this particular run.
    base_rows = {row["id"]: row for row in rows if "." not in row["id"]}
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in base_rows}
    in_degree: dict[str, int] = {node_id: 0 for node_id in base_rows}
    for edge in edges:
        source, target = edge["from"], edge["to"]
        if source in adjacency and target in adjacency:
            adjacency[source].append(target)
            in_degree[target] += 1

    def order_key(node_id: str):
        time = _as_dict(_as_dict(summaries.get(node_id)).get("time_info"))
        return (float(time.get("start_time_float") or time.get("start_time") or 0), node_id)

    ready = sorted((node_id for node_id, degree in in_degree.items() if degree == 0), key=order_key)
    ordered_ids: list[str] = []
    while ready:
        current = ready.pop(0)
        ordered_ids.append(current)
        for target in sorted(adjacency[current], key=order_key):
            in_degree[target] -= 1
            if in_degree[target] == 0:
                ready.append(target)
                ready.sort(key=order_key)
    # Preserve every node for partial/cyclic debug trees, after graph-ordered nodes.
    ordered_ids.extend(node_id for node_id in sorted(base_rows, key=order_key) if node_id not in ordered_ids)
    row_by_id = {row["id"]: row for row in rows}
    ordered_rows: list[dict[str, Any]] = []
    for node_id in ordered_ids:
        ordered_rows.append(row_by_id[node_id])
        ordered_rows.extend(row for row in rows if row["id"].startswith(f"{node_id}."))
    return ordered_rows


def parsed_progress(tree: dict[str, Any]) -> dict[str, Any]:
    summary = _as_dict(tree.get("summary"))
    return {
        "nodes": _node_details(tree),
        "traversed_edges": [
            {"from": str(_as_dict(edge).get("from_node_id")), "to": str(_as_dict(edge).get("to_node_id"))}
            for edge in tree.get("traversed_edges") or []
            if _as_dict(edge).get("from_node_id") is not None and _as_dict(edge).get("to_node_id") is not None
        ],
        "system_variables": summary.get("system_variables") or tree.get("system_variables") or {},
        "output_variables": summary.get("output_variables") or tree.get("output_variables") or {},
        "structured_output_setting": summary.get("structured_output_setting") or tree.get("structured_output_setting") or {},
    }


def smart_usage(tree: dict[str, Any]) -> dict[str, Any]:
    summary = _as_dict(tree.get("summary"))
    usage = _as_dict(summary.get("model_id_to_token_usage_info"))
    if not usage:
        usage = {}
        for node in _as_dict(tree.get("node_id_to_summary")).values():
            node_usage = _as_dict(_as_dict(node).get("model_id_to_token_usage_info"))
            for model_id, info in node_usage.items():
                if not isinstance(info, dict):
                    continue
                current = usage.setdefault(str(model_id), {})
                for key, value in info.items():
                    if isinstance(value, (int, float)):
                        current[key] = float(current.get(key) or 0) + value
                    elif key not in current:
                        current[key] = value
    total_input = total_output = 0
    total_cost = 0.0
    models: dict[str, Any] = {}
    for model_id, info in usage.items():
        if not isinstance(info, dict):
            continue
        input_tokens = int(info.get("total_input_tokens") or info.get("input_tokens") or 0)
        output_tokens = int(info.get("total_output_tokens") or info.get("output_tokens") or 0)
        cost = sum(float(info.get(key) or 0) for key in ("total_input_cost", "total_output_cost", "total_cached_input_cost", "audio_input_cost"))
        total_input += input_tokens
        total_output += output_tokens
        total_cost += cost
        models[str(model_id)] = {"input_tokens": input_tokens, "output_tokens": output_tokens, "cost": cost, "input_price": info.get("input_price"), "output_price": info.get("output_price")}
    return {"models": models, "input_tokens": total_input, "output_tokens": total_output, "provider_cost": total_cost, "reported": bool(models)}


def progress_from_tree(tree: dict[str, Any], status: str) -> dict[str, int]:
    values = list(_as_dict(tree.get("node_id_to_summary")).values())
    values = [item for item in values if isinstance(item, dict)]
    total_nodes = len(values)
    completed_nodes = sum(1 for item in values if str(item.get("status") or "").lower() in TERMINAL_STATUSES)
    running_nodes = sum(1 for item in values if str(item.get("status") or "").lower() in {"running", "processing"})
    if status in {"success", "failed"}:
        completed_nodes = total_nodes
    return {"total_nodes": total_nodes, "completed_nodes": completed_nodes, "running_nodes": running_nodes}


def refresh_task(task: dict[str, Any]) -> dict[str, Any]:
    thread_id = str(task.get("smart_thread_id") or "").strip()
    if not thread_id:
        return task_store.update_task(task["id"], {"status": "failed", "error_messages": ["Task does not have a SMART thread ID."], "completed_at": task_store.now()})
    tree = smart_client.get_debug_tree(thread_id)
    summary = _as_dict(tree.get("summary"))
    output = tree.get("output")
    business_error = _find_business_error(output) or _find_business_error(summary.get("output_variables"))
    is_interrupted = bool(summary.get("is_interrupted") or tree.get("is_interrupted"))
    status = "interrupted" if is_interrupted else str(summary.get("status") or "running").lower()
    if business_error and status == "success":
        status = "failed"
    progress = progress_from_tree(tree, status)
    progress_percent = 100 if status in {"success", "failed"} else max(1, int(progress["completed_nodes"] / progress["total_nodes"] * 100)) if progress["total_nodes"] else 1
    usage = smart_usage(tree)
    patch: dict[str, Any] = {
        "status": status, "debug_tree": tree, "last_polled_at": task_store.now(), "progress_summary": progress,
        "progress_percent": progress_percent, "parsed_progress": parsed_progress(tree), "smart_usage": usage,
        "interrupt": {"is_interrupted": True, "interrupt_type": summary.get("interrupt_type") or tree.get("interrupt_type") or "human_in_loop", "message": summary.get("interrupt_message") or tree.get("interrupt_message") or "Workflow needs your input.", "extra_data": summary.get("interrupt_extra_data") or tree.get("interrupt_extra_data") or {}} if is_interrupted else None,
    }
    if status == "success":
        patch.update({"output": output, "provider_cost": usage["provider_cost"] if usage["reported"] else None, "completed_at": task.get("completed_at") or task_store.now()})
    elif status == "failed":
        errors = summary.get("error_messages") or []
        if not isinstance(errors, list): errors = [errors]
        messages = [text for value in errors if (text := _humanise_error(value))]
        if business_error:
            messages.insert(0, f"{business_error['code']}: {business_error['message']}")
        patch.update({"error_messages": messages or ["SMART reported a failed workflow run."], "business_error": business_error, "completed_at": task.get("completed_at") or task_store.now()})
    if patch.get("completed_at") and task.get("started_at"):
        try:
            patch["duration_ms"] = int((datetime.fromisoformat(patch["completed_at"].replace("Z", "+00:00")) - datetime.fromisoformat(task["started_at"].replace("Z", "+00:00"))).total_seconds() * 1000)
        except (TypeError, ValueError):
            pass
    return task_store.update_task(task["id"], patch)
