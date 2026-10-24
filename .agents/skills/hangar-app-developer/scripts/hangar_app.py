#!/usr/bin/env python3
"""Synchronize a local Hangar app folder through Hangar's external API.

The local folder mirrors the Hangar virtual filesystem. App files and table
data use separate commands so source sync never replaces runtime records.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.client
import http.cookiejar
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


API_SUFFIX = "/api/external/hangar"
REQUIRED_FILES = (
    "frontend/src/App.svelte",
    "backend/main.py",
    "backend/requirements.txt",
    "design/design.md",
)
IGNORED_PARTS = {
    ".git", ".hangar", ".hangarkit", ".local", ".venv", ".codex", ".openai",
    "dev", "venv", "node_modules", "__pycache__", ".DS_Store",
}
RESERVED_TOP_LEVEL = {"data", "hangar-app.json"}
METADATA_KEYS = ("name", "slug", "spaces", "settings", "content", "design", "storage", "custom_instructions")
CHUNK_BYTES = 262144
MAX_BATCH_CHUNKS = 128
MAX_BATCH_JSON_BYTES = 512 * 1024
RETRY_ATTEMPTS = 3
PUBLISH_ACTIVE = {"queued", "building", "starting_backend", "activating"}
PUBLISH_TERMINAL = {"ready", "failed", "superseded"}


class CliError(RuntimeError):
    pass


class ApiError(CliError):
    def __init__(self, status: int, detail: str):
        super().__init__(f"Hangar API {status}: {detail}")
        self.status = status
        self.detail = detail


class TransportError(CliError):
    """A request may have reached the server; only idempotent work can retry."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        raise CliError("Runtime verification redirected; sign-in or runtime access is not ready.")


def json_text(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_vfs_path(value: str) -> str:
    path = PurePosixPath(str(value).replace("\\", "/"))
    if not value or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CliError(f"Invalid Hangar virtual filesystem path: {value!r}")
    return path.as_posix()


def read_wingman_token() -> str:
    for key in ("WINGMAN_TOKEN", "HANGARKIT_WINGMAN_TOKEN"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    path = Path.home() / ".wingman" / "auth.json"
    try:
        payload = json.loads(path.read_text())
        token = str(payload.get("accessToken") or "").strip()
        expires_at = int(payload.get("expiresAt") or 0)
        if token and expires_at > time.time() + 30:
            return token
    except (OSError, ValueError, TypeError):
        pass
    return ""


@dataclass
class Client:
    base_url: str
    token: str
    user_token: str
    timeout: int = 60

    @property
    def api_url(self) -> str:
        base = self.base_url.rstrip("/")
        return base if base.endswith(API_SUFFIX) else f"{base}{API_SUFFIX}"

    @property
    def host_url(self) -> str:
        return self.api_url[:-len(API_SUFFIX)]

    def redact(self, value: str) -> str:
        for secret in (self.token, self.user_token):
            if secret:
                value = value.replace(secret, "[redacted]")
        return value

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Any | None = None,
        revision: str = "",
        raw: bool = False,
    ) -> Any:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.user_token:
            headers["X-Hangarkit-User-Token"] = self.user_token
        if revision:
            headers["If-Match"] = revision
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(f"{self.api_url}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
                if raw:
                    return payload, dict(response.headers)
                return json.loads(payload.decode("utf-8")) if payload else {}
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(payload).get("message") or json.loads(payload).get("error") or payload
            except (ValueError, AttributeError):
                detail = payload or exc.reason
            raise ApiError(exc.code, self.redact(str(detail))) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as exc:
            raise TransportError("Hangar request interrupted; the server outcome may be unknown.") from exc

    def app(self, ref: str, *, compact: bool = False) -> dict[str, Any]:
        query = "?fields=id,slug,revision,app_url" if compact else ""
        try:
            return self.request("GET", f"/apps/{urllib.parse.quote(ref, safe='')}{query}")["app"]
        except ApiError as exc:
            if exc.status != 404:
                raise
        response = self.request("GET", f"/apps?slug={urllib.parse.quote(ref, safe='')}&limit=100")
        apps = response.get("apps") or []
        matches = [app for app in apps if app.get("slug") == ref]
        if len(matches) != 1:
            raise CliError(f"No editable app found for {ref!r}")
        return self.request("GET", f"/apps/{urllib.parse.quote(matches[0]['id'], safe='')}{query}")["app"]

    def verify_runtime(self, app: dict[str, Any], url: str, health_path: str) -> dict[str, Any]:
        host = urllib.parse.urlsplit(self.host_url)
        target = urllib.parse.urlsplit(url)
        if (target.scheme, target.netloc) != (host.scheme, host.netloc):
            raise CliError("Refusing runtime verification on a different origin.")
        if "/apps/" not in target.path or target.username or target.password or target.query or target.fragment:
            raise CliError("Invalid published runtime URL.")
        if not health_path.startswith("/api/") or "?" in health_path or "#" in health_path:
            raise CliError("--health-path must be an app-relative /api/ route.")
        if any(part in {".", ".."} for part in health_path.split("/")):
            raise CliError("Invalid health route.")
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), NoRedirect(),
        )

        def fetch(request: urllib.request.Request) -> tuple[bytes, str]:
            try:
                with opener.open(request, timeout=self.timeout) as response:
                    return response.read(), response.headers.get("Content-Type", "")
            except urllib.error.HTTPError as exc:
                raise CliError(f"Authenticated runtime verification failed (HTTP {exc.code}).") from exc
            except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as exc:
                raise CliError("Authenticated runtime verification could not reach Hangar.") from exc

        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
        if self.user_token:
            # Disposable local-user tokens are valid only on non-production Hangar.
            headers["X-Hangarkit-User-Token"] = self.user_token
        else:
            payload, _ = fetch(urllib.request.Request(
                f"{self.host_url}/api/auth/token/browser-session", data=b"{}",
                headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
                method="POST",
            ))
            try:
                success = json.loads(payload).get("success") is True
            except (ValueError, AttributeError):
                success = False
            if not success:
                raise CliError("Could not establish a fresh Hangar browser session.")
        shell, content_type = fetch(urllib.request.Request(url, headers=headers))
        if "text/html" not in content_type.lower() or not shell.strip():
            raise CliError("Published runtime did not return an HTML app shell.")
        health, _ = fetch(urllib.request.Request(url.rstrip("/") + health_path, headers=headers))
        try:
            value = json.loads(health)
        except ValueError as exc:
            raise CliError("Published health route did not return JSON.") from exc
        if not isinstance(value, dict) or not (value.get("status") == "ok" or value.get("ok") is True):
            raise CliError("Published health route is not healthy.")
        if health_path == "/api/_hangarkit/health" and value.get("app_id") != app_id(app):
            raise CliError("Published runner health belongs to a different app.")
        return {"shell": "ok", "health": "ok", "app_url": url}


def app_id(app: dict[str, Any]) -> str:
    value = str(app.get("id") or "")
    if not value:
        raise CliError("Hangar response did not contain an app id")
    return value


def app_revision(app: dict[str, Any]) -> str:
    return str(app.get("revision") or app.get("updated") or "")


def resolve_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise CliError(f"Local app directory does not exist: {path}")
    return path


def collect_local_files(
    root: Path, *, require_shape: bool = True, source_dirs: Iterable[str] | None = None,
) -> dict[str, str]:
    root = root.resolve()
    files: dict[str, str] = {}
    scopes = [root / safe_vfs_path(value) for value in source_dirs] if source_dirs else [root]
    for scope in scopes:
        if not scope.is_dir() or scope.resolve() != scope or any(part in IGNORED_PARTS | RESERVED_TOP_LEVEL for part in scope.relative_to(root).parts):
            raise CliError(f"Invalid source directory: {scope}")
        for directory, folders, names in os.walk(scope):
            folders[:] = [
                name for name in folders
                if name not in IGNORED_PARTS and not (Path(directory) / name).is_symlink()
                and not (Path(directory) == root and name in RESERVED_TOP_LEVEL)
            ]
            for name in names:
                path = Path(directory) / name
                relative = path.relative_to(root)
                if path.is_symlink() or name in IGNORED_PARTS or name == ".user-token" or name == ".env" or name.startswith(".env."):
                    continue
                if relative.parts[0] in RESERVED_TOP_LEVEL:
                    continue
                virtual_path = safe_vfs_path(relative.as_posix())
                try:
                    files[virtual_path] = path.read_bytes().decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise CliError(f"App file is not UTF-8 text: {path}") from exc
    if require_shape:
        missing = [path for path in REQUIRED_FILES if path not in files]
        if missing:
            raise CliError("Local app is missing required Hangar files: " + ", ".join(missing))
    return files


def remote_files(client: Client, app: dict[str, Any]) -> dict[str, str]:
    response = client.request("GET", f"/apps/{urllib.parse.quote(app_id(app), safe='')}/files?include_content=true")
    result: dict[str, str] = {}
    for file in response.get("files") or []:
        if file.get("type") == "directory":
            continue
        path = safe_vfs_path(str(file.get("path") or ""))
        result[path] = str(file.get("content") or "")
    return result


def compare(local: dict[str, str], remote: dict[str, str]) -> dict[str, list[str]]:
    local_paths = set(local)
    remote_paths = set(remote)
    return {
        "local_only": sorted(local_paths - remote_paths),
        "remote_only": sorted(remote_paths - local_paths),
        "changed": sorted(path for path in local_paths & remote_paths if sha256_text(local[path]) != sha256_text(remote[path])),
        "same": sorted(path for path in local_paths & remote_paths if sha256_text(local[path]) == sha256_text(remote[path])),
    }


def progress(message: str) -> None:
    print(message, file=sys.stderr)


def retryable(exc: CliError) -> bool:
    return isinstance(exc, TransportError) or isinstance(exc, ApiError) and exc.status in {408, 429, 500, 502, 503, 504}


def retry_request(client: Client, method: str, path: str, *, body: Any = None, deadline: float | None = None) -> Any:
    for attempt in range(RETRY_ATTEMPTS):
        remaining = deadline - time.monotonic() if deadline is not None else None
        if remaining is not None and remaining <= 0:
            raise TransportError("Hangar operation reached its wait timeout.")
        original_timeout = getattr(client, "timeout", None)
        if original_timeout is not None and remaining is not None:
            client.timeout = min(original_timeout, remaining)
        try:
            return client.request(method, path, body=body)
        except CliError as exc:
            if not retryable(exc) or attempt == RETRY_ATTEMPTS - 1:
                raise
            delay = min(2 ** attempt, 4)
            time.sleep(min(delay, max(0, deadline - time.monotonic())) if deadline is not None else delay)
        finally:
            if original_timeout is not None:
                client.timeout = original_timeout


def file_manifest(client: Client, app: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], str, str]:
    identifier = urllib.parse.quote(app_id(app), safe="")
    response = retry_request(client, "GET", f"/apps/{identifier}/files")
    revision = response.get("revision")
    if not isinstance(revision, str) or not revision or not isinstance(response.get("files"), list):
        raise CliError("Server lacks revision/hash manifests; upgrade Hangar before source sync or release.")
    files: dict[str, dict[str, Any]] = {}
    for item in response["files"]:
        if item.get("type") == "directory":
            continue
        path = safe_vfs_path(str(item.get("path") or ""))
        size, digest = item.get("size"), item.get("sha256")
        if type(size) is not int or size < 0 or not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise CliError("Server lacks UTF-8 byte sizes/SHA-256 manifests; upgrade Hangar before source sync or release.")
        if path in files:
            raise CliError("Server returned duplicate manifest paths.")
        files[path] = {"path": path, "size": size, "sha256": digest}
    source_hash = response.get("source_hash") or ""
    if not isinstance(source_hash, str):
        raise CliError("Invalid manifest source hash.")
    return files, revision, source_hash


def local_manifest(local: dict[str, str]) -> dict[str, dict[str, Any]]:
    return {
        path: {"path": path, "size": len(content.encode("utf-8")), "sha256": sha256_text(content)}
        for path, content in sorted(local.items())
    }


def manifest_changes(local: dict[str, dict[str, Any]], remote: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    return compare(
        {path: item["sha256"] for path, item in local.items()},
        {path: item["sha256"] for path, item in remote.items()},
    )


def upload_response(response: dict[str, Any], identifier: str = "") -> dict[str, Any]:
    upload = response.get("upload")
    if not isinstance(upload, dict) or not upload.get("id") or upload.get("status") not in {"uploading", "committed"}:
        raise CliError("Server lacks staged source uploads; upgrade Hangar before source sync or release.")
    if identifier and upload["id"] != identifier:
        raise CliError("Hangar returned a different upload session.")
    return upload


def commit_upload(client: Client, path: str, upload: dict[str, Any]) -> dict[str, Any]:
    for attempt in range(RETRY_ATTEMPTS):
        try:
            return upload_response(client.request("POST", path + "/commit", body={}), upload["id"])
        except CliError as exc:
            if not retryable(exc):
                raise
            # A timeout can mean the atomic commit already succeeded. Read before retry.
            current = upload_response(retry_request(client, "GET", path), upload["id"])
            if current["status"] == "committed":
                return current
            if attempt == RETRY_ATTEMPTS - 1:
                raise CliError(f"Upload {upload['id']} commit outcome unresolved; re-run the same push to resume.") from exc
            time.sleep(min(2 ** attempt, 4))
    raise CliError("Upload commit did not finish.")


def sync_source(
    client: Client, app: dict[str, Any], local: dict[str, str], *, apply: bool,
    delete: bool = False, require_hash: bool = False,
) -> dict[str, Any]:
    remote, revision, current_hash = file_manifest(client, app)
    manifest = local_manifest(local)
    changes = manifest_changes(manifest, remote)
    writes = sorted(changes["local_only"] + changes["changed"])
    deletes = changes["remote_only"] if delete else []
    result: dict[str, Any] = {
        "app": app_id(app), "revision": revision, "remote_only": changes["remote_only"],
    }
    if not apply:
        return {**result, "would_upload": writes, "would_delete": deletes}
    result.update(uploaded=writes, deleted=deletes)
    if not writes and not deletes:
        if require_hash and not current_hash:
            raise CliError("Server lacks manifest source_hash; upgrade Hangar before publication.")
        return {**result, **({"source_hash": current_hash} if current_hash else {})}
    identifier = urllib.parse.quote(app_id(app), safe="")
    path = f"/apps/{identifier}/uploads"
    body = {"revision": revision, "files": [manifest[name] for name in writes], "delete_paths": deletes}
    try:
        upload = upload_response(retry_request(client, "POST", path, body=body))
    except ApiError as exc:
        if exc.status in {404, 405, 501}:
            raise CliError("Server lacks staged source uploads; upgrade Hangar. No legacy source PATCH or publish was attempted.") from exc
        raise
    path += "/" + urllib.parse.quote(str(upload["id"]), safe="")
    progress(f"Upload {upload['id']}: {len(writes)} files, {sum(manifest[name]['size'] for name in writes)} bytes")
    encoded = {name: local[name].encode("utf-8") for name in writes}
    last_progress = time.monotonic()
    sent_bytes = 0
    while upload["status"] == "uploading" and upload.get("missing"):
        chunk_bytes = upload.get("chunk_bytes", CHUNK_BYTES)
        if type(chunk_bytes) is not int or not 1 <= chunk_bytes <= CHUNK_BYTES:
            raise CliError("Invalid upload chunk limit.")
        chunks: list[dict[str, Any]] = []
        ends: dict[str, int] = {}
        budget = chunk_bytes
        for item in upload["missing"]:
            name, offset, size = item.get("path"), item.get("offset"), item.get("size")
            if name not in encoded or name in ends or type(offset) is not int or type(size) is not int:
                raise CliError("Invalid upload resume manifest.")
            content = encoded[name]
            if size != len(content) or not 0 <= offset < size:
                raise CliError("Upload resume byte size/offset does not match local source.")
            chunk = content[offset:offset + budget]
            candidate = {"path": name, "offset": offset, "data_base64": base64.b64encode(chunk).decode("ascii")}
            if len(json.dumps({"chunks": [*chunks, candidate]}, ensure_ascii=False).encode("utf-8")) > MAX_BATCH_JSON_BYTES:
                if not chunks:
                    raise CliError("Source chunk cannot fit the upload JSON limit.")
                break
            chunks.append(candidate)
            ends[name] = offset + len(chunk)
            budget -= len(chunk)
            if not budget or len(chunks) == MAX_BATCH_CHUNKS:
                break
        upload = upload_response(retry_request(client, "PUT", path, body={"chunks": chunks}), upload["id"])
        remaining = {entry["path"]: entry for entry in upload.get("missing") or []}
        for name, end in ends.items():
            if upload["status"] != "committed" and name in remaining and remaining[name].get("offset", -1) < end:
                raise CliError(f"Upload made no byte progress for {name}; re-run the same push to resume.")
        sent_bytes += chunk_bytes - budget
        if time.monotonic() - last_progress >= 30:
            progress(f"Upload {upload['id']}: {sent_bytes} bytes transferred this run")
            last_progress = time.monotonic()
    if upload["status"] != "committed":
        upload = commit_upload(client, path, upload)
    source_hash = upload.get("source_hash")
    if upload["status"] != "committed" or not isinstance(source_hash, str) or not source_hash:
        raise CliError("Source commit did not return a committed source hash; nothing was published.")
    saved, saved_revision, saved_hash = file_manifest(client, app)
    expected = {**remote, **manifest}
    for name in deletes:
        expected.pop(name, None)
    if saved != expected or saved_hash and saved_hash != source_hash:
        raise CliError("Saved source verification failed or source changed concurrently; nothing was published.")
    result.update(revision=saved_revision, source_hash=source_hash, upload_id=upload["id"])
    progress("Source committed and hash-verified.")
    return result


def print_result(args: argparse.Namespace, value: Any) -> None:
    if args.json:
        print(json_text(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, list):
                print(f"{key}: {len(item)}")
                for path in item:
                    print(f"  {path}")
            else:
                print(f"{key}: {item}")
        return
    print(value)


def write_text(path: Path, content: str, *, force: bool) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") != content and not force:
        raise CliError(f"Refusing to overwrite local change: {path}. Re-run with --force.")
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.replace(path)
    return True


def app_metadata(app: dict[str, Any]) -> dict[str, Any]:
    return {key: app[key] for key in METADATA_KEYS if key in app}


def local_metadata(root: Path) -> dict[str, Any]:
    path = root / "hangar-app.json"
    if not path.exists():
        raise CliError(f"Local app metadata does not exist: {path}. Run metadata pull first.")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise CliError(f"Invalid JSON app metadata: {path}") from exc
    if not isinstance(value, dict):
        raise CliError(f"App metadata must be a JSON object: {path}")
    return {key: value[key] for key in METADATA_KEYS if key in value}


def command_status(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    tables = client.request("GET", f"/apps/{urllib.parse.quote(app_id(app), safe='')}/tables").get("tables") or []
    print_result(args, {
        "id": app_id(app),
        "name": app.get("name"),
        "slug": app.get("slug"),
        "revision": app_revision(app),
        "file_count": app.get("file_count"),
        "tables": [table.get("name") for table in tables],
        "catalog_enabled": bool(app.get("settings", {}).get("catalog_enabled")),
        "app_url": app.get("app_url"),
    })


def command_diff(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app, compact=True)
    remote, _, _ = file_manifest(client, app)
    local = collect_local_files(resolve_dir(args.dir), source_dirs=args.source_dir)
    result = manifest_changes(local_manifest(local), remote)
    result["app"] = app_id(app)
    print_result(args, result)


def command_pull(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    root = resolve_dir(args.dir)
    remote = remote_files(client, app)
    existing = collect_local_files(root, require_shape=False)
    changes = compare(existing, remote)
    if args.dry_run:
        print_result(args, {"app": app_id(app), **changes})
        return
    written = [path for path, content in remote.items() if write_text(root / path, content, force=args.force)]
    deleted: list[str] = []
    if args.delete:
        for path in changes["local_only"]:
            target = root / path
            if target.exists():
                target.unlink()
                deleted.append(path)
    print_result(args, {"app": app_id(app), "written": written, "deleted": deleted})


def command_push(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app, compact=True)
    local = collect_local_files(resolve_dir(args.dir), source_dirs=args.source_dir)
    print_result(args, sync_source(client, app, local, apply=args.apply, delete=args.delete))


def command_create(client: Client, args: argparse.Namespace) -> None:
    root = resolve_dir(args.dir)
    local = collect_local_files(root, source_dirs=args.source_dir)
    if not args.apply:
        print_result(args, {"would_create": args.name, "slug": args.slug or "", "files": sorted(local)})
        return
    files = [{"path": path, "type": "file", "content": content} for path, content in sorted(local.items())]
    metadata = local_metadata(root) if (root / "hangar-app.json").exists() else {}
    body: dict[str, Any] = {**metadata, "name": args.name, "files": files}
    body["settings"] = {"visibility": "private", **(body.get("settings") or {})}
    if args.slug:
        body["slug"] = args.slug
    response = client.request("POST", "/apps", body=body)
    created = response["app"]
    print_result(args, created if args.json else {"id": created.get("id"), "slug": created.get("slug"), "app_url": created.get("app_url")})


def command_check_or_publish(client: Client, args: argparse.Namespace, action: str) -> None:
    if action == "publish":
        command_publish(client, args)
        return
    app = client.app(args.app)
    response = client.request("POST", f"/apps/{urllib.parse.quote(app_id(app), safe='')}/{action}", body={})
    if args.json:
        print_result(args, response)
        return
    print_result(args, action_summary(response))


def action_summary(response: dict[str, Any]) -> dict[str, Any]:
    deployment = response.get("deployment") or {}
    return {
        "success": response.get("success", True),
        "preview_url": response.get("preview_url", ""),
        "published_version": response.get("published_version", ""),
        "backend_status": deployment.get("status", ""),
        "error": response.get("error", ""),
    }


def command_deploy(client: Client, args: argparse.Namespace) -> None:
    command_release(client, args)


def publish_job(response: dict[str, Any], source_hash: str, job_id: str = "") -> dict[str, Any]:
    job = response.get("job")
    if not isinstance(job, dict) or not job.get("id") or job.get("status") not in PUBLISH_ACTIVE | PUBLISH_TERMINAL:
        raise CliError("Server lacks asynchronous publish jobs; upgrade Hangar. No synchronous fallback was attempted.")
    if job_id and job["id"] != job_id:
        raise CliError("Hangar returned a different publication job.")
    if not isinstance(job.get("source_hash"), str) or not job["source_hash"] or source_hash and job["source_hash"] != source_hash:
        raise CliError("Publication job source hash does not match committed source.")
    return job


def wait_for_publish(
    client: Client, app: dict[str, Any], args: argparse.Namespace, *, source_hash: str,
    key: str = "", job_id: str = "", on_job: Any = None,
) -> dict[str, Any]:
    if not 0 < args.wait_timeout <= 3600 or not 0 < args.poll_interval <= 30:
        raise CliError("--wait-timeout must be 1-3600 seconds and --poll-interval must be greater than 0 and at most 30.")
    deadline = time.monotonic() + args.wait_timeout
    path = f"/apps/{urllib.parse.quote(app_id(app), safe='')}/publish"
    if not job_id:
        progress(f"Publication key {key}; source {source_hash}")
        try:
            response = retry_request(client, "POST", path, body={
                "async": True, "idempotency_key": key, "expected_source_hash": source_hash,
            }, deadline=deadline)
        except ApiError as exc:
            if exc.status in {404, 405, 501}:
                raise CliError("Server lacks async publication; upgrade Hangar. No synchronous fallback was attempted.") from exc
            raise
        except TransportError as exc:
            raise CliError(f"Publication outcome unknown. Resume with key {key} and source hash {source_hash}; do not use a new key.") from exc
        job = publish_job(response, source_hash)
        job_id = str(job["id"])
        if on_job:
            on_job(job_id)
    else:
        response = {}
        job = {}
    last_status = ""
    while True:
        if not job:
            try:
                response = retry_request(client, "GET", path + "/jobs/" + urllib.parse.quote(job_id, safe=""), deadline=deadline)
            except TransportError as exc:
                raise CliError(f"Publication {job_id} wait interrupted/timed out. Resume this job; do not start a new publish.") from exc
            job = publish_job(response, source_hash, job_id)
        if not source_hash:
            source_hash = job["source_hash"]
        status = job["status"]
        if status != last_status:
            progress(f"Publication {job_id}: {status}")
            last_status = status
        if status in {"failed", "superseded"}:
            raise CliError(f"Publication {job_id} {status}; no verified release. Inspect the job before starting another publication.")
        if status == "ready":
            result = job.get("result") or {}
            if not isinstance(result, dict) or result.get("success") is False or result.get("superseded"):
                raise CliError(f"Publication {job_id} did not activate successfully.")
            return {
                **response, **result, "job": job, "source_hash": source_hash,
            }
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CliError(f"Publication {job_id} timed out in {status}. Resume this job; do not start a new publish.")
        time.sleep(min(args.poll_interval, remaining))
        job = {}


def command_publish(client: Client, args: argparse.Namespace) -> None:
    if not args.apply:
        raise CliError("publish changes the live app. Re-run with --apply.")
    app = client.app(args.app, compact=True)
    source_hash = args.expected_source_hash
    if not args.job and not source_hash:
        source_hash = sync_source(client, app, {}, apply=True, require_hash=True)["source_hash"]
    key = args.idempotency_key or str(uuid.uuid4())
    response = wait_for_publish(client, app, args, source_hash=source_hash, key=key, job_id=args.job)
    print_result(args, {
        **action_summary(response), "job_id": response["job"]["id"],
        "status": "ready", "source_hash": response["source_hash"],
        "app_url": response.get("app_url", app.get("app_url", "")),
    })


def release_intent(local: dict[str, str], tables: dict[str, dict[str, Any]], delete: bool) -> str:
    value = {
        "files": local_manifest(local),
        "tables": {name: canonical_table_definition(dump) for name, dump in tables.items()},
        "delete": delete,
    }
    return sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


def command_release(client: Client, args: argparse.Namespace) -> None:
    if not args.apply:
        raise CliError("release syncs drafts and publishes live code. Re-run with --apply.")
    if not 0 < args.wait_timeout <= 3600 or not 0 < args.poll_interval <= 30:
        raise CliError("Invalid publication wait/poll timeout.")
    root = resolve_dir(args.dir)
    local = collect_local_files(root, source_dirs=args.source_dir)
    tables = local_tables(root)
    intent = release_intent(local, tables, args.delete)
    app = client.app(args.app, compact=True)
    state_path = root / ".hangar" / "release.json"
    state: dict[str, Any] = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise CliError("Could not read .hangar/release.json; inspect it before starting another publication.") from exc
        if not isinstance(state, dict) or state.get("app") != app_id(app) or state.get("base_url") != client.api_url or state.get("intent") != intent:
            raise CliError("Unfinished release belongs to different source/app/host. Inspect its job before removing .hangar/release.json.")
        if not state.get("source_hash") or not state.get("idempotency_key"):
            raise CliError("Incomplete release state; inspect it before starting another publication.")
        progress("Resuming unfinished release.")
    else:
        source = sync_source(client, app, local, apply=True, delete=args.delete, require_hash=True)
        definitions = sync_table_definitions(client, app, tables, apply=True)
        progress(f"Table definitions: {len(definitions['updated_definitions'])} updated; records untouched.")
        _, _, current_hash = file_manifest(client, app)
        if not current_hash or current_hash != source["source_hash"]:
            raise CliError("Source changed during table-definition sync (or manifest hash is unavailable); nothing was published.")
        identifier = urllib.parse.quote(app_id(app), safe="")
        check = client.request("POST", f"/apps/{identifier}/check", body={})
        if check.get("success") is not True:
            raise CliError("Hangar check failed; nothing was published.")
        if check.get("source_hash") != source["source_hash"]:
            raise CliError("Check source hash changed or is unavailable; nothing was published.")
        progress("Check passed.")
        state = {
            "app": app_id(app), "base_url": client.api_url, "intent": intent,
            "source_hash": source["source_hash"], "idempotency_key": str(uuid.uuid4()),
        }
        write_text(state_path, json_text(state) + "\n", force=True)

    def save_job(job_id: str) -> None:
        state["job_id"] = job_id
        write_text(state_path, json_text(state) + "\n", force=True)

    response = wait_for_publish(
        client, app, args, source_hash=state["source_hash"], key=state["idempotency_key"],
        job_id=state.get("job_id", ""), on_job=save_job,
    )
    url = response.get("app_url") or (response.get("app") or {}).get("app_url") or app.get("app_url")
    if not isinstance(url, str) or not url:
        raise CliError("Ready publication did not return a runtime URL; release remains unverified.")
    verification = client.verify_runtime(app, url, args.health_path)
    state_path.unlink()
    progress("Fresh authenticated shell and health verified.")
    print_result(args, {
        "app": app_id(app), "job_id": response["job"]["id"], "status": "ready",
        "source_hash": state["source_hash"], "published_version": response.get("published_version", ""),
        "verification": verification,
    })


def command_export(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    query = "?include_tables=true" if args.include_tables else ""
    payload, _headers = client.request("GET", f"/apps/{urllib.parse.quote(app_id(app), safe='')}/export{query}", raw=True)
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print_result(args, {"app": app_id(app), "output": str(output), "bytes": len(payload)})


def command_metadata_diff(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    local = local_metadata(resolve_dir(args.dir))
    remote = app_metadata(app)
    print_result(args, {"app": app_id(app), "same": local == remote, "local": local if local != remote else {}, "remote": remote if local != remote else {}})


def command_metadata_pull(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    root = resolve_dir(args.dir)
    if args.dry_run:
        print_result(args, {"app": app_id(app), "would_write": "hangar-app.json"})
        return
    changed = write_text(root / "hangar-app.json", json_text(app_metadata(app)) + "\n", force=args.force)
    print_result(args, {"app": app_id(app), "written": ["hangar-app.json"] if changed else []})


def command_metadata_push(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    updates = local_metadata(resolve_dir(args.dir))
    if not args.apply:
        print_result(args, {"app": app_id(app), "would_update": sorted(updates)})
        return
    response = client.request("PATCH", f"/apps/{urllib.parse.quote(app_id(app), safe='')}", body=updates, revision=app_revision(app))
    result = response.get("app") or app
    print_result(args, {"app": app_id(result), "updated": sorted(updates), "revision": app_revision(result)})


def local_tables(root: Path) -> dict[str, dict[str, Any]]:
    folder = root / "data"
    if not folder.exists():
        return {}
    tables: dict[str, dict[str, Any]] = {}
    for path in sorted(folder.glob("*.json")):
        if path.name == "tables-manifest.json":
            continue
        name = path.stem
        if not name.replace("_", "a").replace("-", "a").isalnum():
            raise CliError(f"Invalid table file name: {path.name}")
        try:
            value = json.loads(path.read_text())
        except ValueError as exc:
            raise CliError(f"Invalid JSON table dump: {path}") from exc
        if not isinstance(value, dict):
            raise CliError(f"Table dump must be a JSON object: {path}")
        tables[name] = value
    return tables


def remote_tables(client: Client, app: dict[str, Any]) -> dict[str, dict[str, Any]]:
    identifier = urllib.parse.quote(app_id(app), safe="")
    names = client.request("GET", f"/apps/{identifier}/tables").get("names") or []
    return {
        str(name): client.request("GET", f"/apps/{identifier}/tables/{urllib.parse.quote(str(name), safe='')}?dump=true").get("data") or {}
        for name in names
    }


def table_manifest(tables: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "tables": [
            {
                "name": name,
                "schema": dump.get("schema") or [],
                "indexes": dump.get("indexes") or [],
                "scope": dump.get("scope") or "app",
                "icon": dump.get("icon") or "mdi:database",
                "access": dump.get("access"),
                "record_count": len(dump.get("records") or []),
            }
            for name, dump in sorted(tables.items())
        ]
    }


def canonical_table_dump(dump: dict[str, Any]) -> dict[str, Any]:
    """Drop storage-only fields and materialize Hangar's table defaults."""
    schema: list[dict[str, Any]] = []
    for field in dump.get("schema") or []:
        item = {
            "name": str(field.get("name") or "").strip(),
            "type": str(field.get("type") or "text"),
            "required": bool(field.get("required")),
            "indexed": bool(field.get("indexed")),
            "unique": bool(field.get("unique")),
        }
        if "default" in field:
            item["default"] = field["default"]
        if "options" in field:
            item["options"] = field["options"]
        schema.append(item)
    records: list[dict[str, Any]] = []
    for row in dump.get("records") or []:
        item = {key: value for key, value in row.items() if key not in {"created", "updated", "owner_label"}}
        item["id"] = str(item.get("id") or "")
        item["owner"] = str(item.get("owner") or "")
        records.append(item)
    records.sort(key=lambda item: item["id"])
    return {
        "schema": schema,
        "indexes": dump.get("indexes") or [],
        "scope": "user" if dump.get("scope") == "user" else "app",
        "access": dump.get("access") or {"read": ["all"], "write": ["all"]},
        "icon": str(dump.get("icon") or "mdi:database"),
        "records": records,
    }


def canonical_table_definition(dump: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in canonical_table_dump({**dump, "records": []}).items() if key != "records"}


def command_tables_diff(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    local = local_tables(resolve_dir(args.dir))
    identifier = urllib.parse.quote(app_id(app), safe="")
    remote = {
        table["name"]: table
        for table in client.request("GET", f"/apps/{identifier}/tables").get("tables") or []
    }
    local_text = {name: json.dumps(canonical_table_definition(value), sort_keys=True, separators=(",", ":")) for name, value in local.items()}
    remote_text = {name: json.dumps(canonical_table_definition(value), sort_keys=True, separators=(",", ":")) for name, value in remote.items()}
    print_result(args, {"app": app_id(app), "records_compared": False, **compare(local_text, remote_text)})


def command_tables_pull(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    root = resolve_dir(args.dir)
    remote = remote_tables(client, app)
    folder = root / "data"
    if args.dry_run:
        print_result(args, {"app": app_id(app), "would_write": sorted(remote)})
        return
    written: list[str] = []
    for name, dump in remote.items():
        path = folder / f"{name}.json"
        if write_text(path, json_text(dump) + "\n", force=args.force):
            written.append(path.relative_to(root).as_posix())
    manifest = folder / "tables-manifest.json"
    write_text(manifest, json_text(table_manifest(remote)) + "\n", force=args.force)
    print_result(args, {"app": app_id(app), "written": written})


def command_tables_export(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    path = f"/apps/{urllib.parse.quote(app_id(app), safe='')}/tables/{urllib.parse.quote(args.table, safe='')}?format=csv"
    payload, headers = client.request("GET", path, raw=True)
    content_type = next((value.lower() for key, value in headers.items() if key.lower() == "content-type"), "")
    if content_type.startswith("application/zip"):
        extension = ".zip"
    elif content_type.startswith("text/csv"):
        extension = ".csv"
    else:
        raise CliError(f"Unexpected table export content type: {content_type or 'missing'}")
    output = Path(args.output).expanduser().resolve().with_suffix(extension)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print_result(args, {"app": app_id(app), "table": args.table, "output": str(output), "bytes": len(payload)})


def command_tables_push(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    local = local_tables(resolve_dir(args.dir))
    print_result(args, sync_table_definitions(client, app, local, apply=args.apply))


def sync_table_definitions(
    client: Client, app: dict[str, Any], local: dict[str, dict[str, Any]], *, apply: bool,
) -> dict[str, Any]:
    identifier = urllib.parse.quote(app_id(app), safe="")
    remote = {
        table["name"]: table
        for table in client.request("GET", f"/apps/{identifier}/tables").get("tables") or []
    }
    local_text = {name: json.dumps(canonical_table_definition(value), sort_keys=True, separators=(",", ":")) for name, value in local.items()}
    remote_text = {name: json.dumps(canonical_table_definition(value), sort_keys=True, separators=(",", ":")) for name, value in remote.items()}
    changes = compare(local_text, remote_text)
    writes = changes["local_only"] + changes["changed"]
    if not apply:
        return {"app": app_id(app), "would_update_definitions": writes, "records_synced": False, "remote_only": changes["remote_only"]}
    for name in writes:
        path = f"/apps/{identifier}/tables/{urllib.parse.quote(name, safe='')}"
        definition = canonical_table_definition(local[name])
        original = canonical_table_definition(remote[name]) if name in remote else None
        revision = app_revision(remote.get(name) or {})
        body = {**definition, **({"expected_updated": revision} if revision else {})}
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = client.request("PATCH", path, body=body)
                if response.get("success") is False:
                    raise CliError(f"Table definition update failed: {name}")
                break
            except CliError as exc:
                if not retryable(exc):
                    raise
                # Definition-only readback distinguishes a saved write from a lost request.
                try:
                    saved = retry_request(client, "GET", path + "?schema_only=true").get("data")
                    if not isinstance(saved, dict):
                        raise CliError(f"Could not verify table definition: {name}")
                except ApiError as read_error:
                    if read_error.status != 404:
                        raise
                    saved = None
                current = canonical_table_definition(saved) if saved is not None else None
                if current == definition:
                    break
                if current != original or revision and app_revision(saved or {}) != revision:
                    raise CliError(f"Table definition changed concurrently: {name}; nothing was published.") from exc
                if attempt == RETRY_ATTEMPTS - 1:
                    raise CliError(f"Table definition outcome unresolved: {name}; re-run sync to inspect saved definitions.") from exc
                time.sleep(min(2 ** attempt, 4))
    return {"app": app_id(app), "updated_definitions": writes, "records_synced": False}


def command_table_records(client: Client, args: argparse.Namespace) -> None:
    app = client.app(args.app)
    name = urllib.parse.quote(args.table, safe="")
    table_path = f"/apps/{urllib.parse.quote(app_id(app), safe='')}/tables/{name}"
    path = table_path + "/records"
    owner = args.owner.strip() if args.tables_command != "clear" else ""
    if args.tables_command == "insert":
        try:
            records = json.loads(Path(args.records_file).read_text())
        except (OSError, ValueError) as exc:
            raise CliError(f"Could not read records JSON: {exc}") from exc
        if not isinstance(records, list) or not 1 <= len(records) <= 100:
            raise CliError("--records-file must contain a JSON array of 1-100 records")
        body = {"records": records, "owner": owner}
        method, path = "POST", table_path + "/record-batches"
        summary = {"insert_count": len(records)}
    elif args.tables_command == "delete-records":
        ids = args.ids
        if len(ids) > 100 or len(set(ids)) != len(ids):
            raise CliError("Supply 1-100 distinct row IDs")
        body = {"ids": ids, "owner": owner}
        method, path = "DELETE", table_path + "/record-batches"
        summary = {"delete_ids": ids}
    else:
        if args.confirm != args.table:
            raise CliError("--confirm must exactly match --table")
        path = table_path + "/record-clear"
        state = client.request("GET", path)
        if state["record_count"] != args.expected_count:
            raise CliError(f"Row count changed: expected {args.expected_count}, current {state['record_count']}")
        body = {
            "confirm": args.confirm,
            "expected_count": args.expected_count,
            "expected_revision": state["revision"],
        }
        method = "POST"
        summary = {"wipe_table": args.table, "expected_count": args.expected_count}
    if not args.apply:
        print_result(args, {"app": app_id(app), "would": summary})
        return
    print_result(args, client.request(method, path, body=body))


def command_delete(client: Client, args: argparse.Namespace) -> None:
    if not args.apply:
        raise CliError("delete permanently removes the app. Re-run with --apply.")
    app = client.app(args.app)
    client.request("DELETE", f"/apps/{urllib.parse.quote(app_id(app), safe='')}", body={}, revision=app_revision(app))
    print_result(args, {"deleted": app_id(app), "slug": app.get("slug")})


def add_app_and_dir(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--app", required=True, help="Hangar app id or slug")
    parser.add_argument("--dir", required=True, help="Local Hangar app directory")


def add_apply(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--apply", action="store_true", help="Perform a write instead of reporting the change")


def add_source_dirs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-dir", action="append", help="Collect only this app-relative directory (repeatable); VFS paths stay unchanged")


def add_wait(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--wait-timeout", type=float, default=900, help="Maximum publication wait seconds (1-3600)")
    parser.add_argument("--poll-interval", type=float, default=2, help="Publication poll seconds (greater than 0, at most 30)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("HANGAR_BASE_URL", "https://wingman.shopee.io/hangar"), help="Hangar base URL")
    parser.add_argument("--token", default="", help="Wingman JWT; defaults to WINGMAN_TOKEN or ~/.wingman/auth.json")
    parser.add_argument("--user-token", default=os.environ.get("HANGARKIT_USER_TOKEN", ""), help="Local Hangar X-Hangarkit-User-Token")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Show app and table metadata")
    status.add_argument("--app", required=True)

    diff = subparsers.add_parser("diff", help="Compare local source files with the app")
    add_app_and_dir(diff)
    add_source_dirs(diff)

    pull = subparsers.add_parser("pull", help="Download remote source files into the local directory")
    add_app_and_dir(pull)
    pull.add_argument("--force", action="store_true", help="Allow overwriting changed local files")
    pull.add_argument("--delete", action="store_true", help="Delete local source files missing remotely")
    pull.add_argument("--dry-run", action="store_true", help="Report the pull without writing files")

    push = subparsers.add_parser("push", help="Upload changed local source files")
    add_app_and_dir(push)
    add_apply(push)
    add_source_dirs(push)
    push.add_argument("--delete", action="store_true", help="Delete remote source files missing locally")

    create = subparsers.add_parser("create", help="Create an app from a local Hangar folder")
    create.add_argument("--dir", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--slug", default="")
    add_apply(create)
    add_source_dirs(create)

    check = subparsers.add_parser("check", help="Compile and server-render an app")
    check.add_argument("--app", required=True)

    publish = subparsers.add_parser("publish", help="Publish the current app files")
    publish.add_argument("--app", required=True)
    add_apply(publish)
    add_wait(publish)
    publish.add_argument("--job", default="", help="Resume polling this job without starting a publication")
    publish.add_argument("--idempotency-key", default="", help="Reuse this key only when recovering an ambiguous publish POST")
    publish.add_argument("--expected-source-hash", default="", help="Committed source hash for publication or recovery")

    for name in ("release", "deploy"):
        release = subparsers.add_parser(name, help="Stage source, sync table definitions, check, publish, and verify runtime")
        add_app_and_dir(release)
        add_apply(release)
        add_source_dirs(release)
        add_wait(release)
        release.add_argument("--delete", action="store_true", help="Explicitly delete remote-only source (including outside scoped directories)")
        release.add_argument("--health-path", default="/api/_hangarkit/health", help="Published app-relative health route")

    export = subparsers.add_parser("export", help="Download an app export zip")
    export.add_argument("--app", required=True)
    export.add_argument("--output", required=True)
    export.add_argument("--include-tables", action="store_true")

    delete = subparsers.add_parser("delete", help="Delete an app")
    delete.add_argument("--app", required=True)
    add_apply(delete)

    metadata = subparsers.add_parser("metadata", help="Synchronize Craft metadata in hangar-app.json")
    metadata_commands = metadata.add_subparsers(dest="metadata_command", required=True)
    for name, help_text in (("diff", "Compare local and remote app metadata"), ("pull", "Download remote app metadata"), ("push", "Upload local app metadata")):
        metadata_command = metadata_commands.add_parser(name, help=help_text)
        add_app_and_dir(metadata_command)
        if name == "pull":
            metadata_command.add_argument("--force", action="store_true", help="Allow overwriting local metadata")
            metadata_command.add_argument("--dry-run", action="store_true")
        if name == "push":
            add_apply(metadata_command)

    tables = subparsers.add_parser("tables", help="Inspect tables and manage definitions or explicit row operations")
    table_commands = tables.add_subparsers(dest="tables_command", required=True)
    for name, help_text in (("diff", "Compare table definitions only"), ("pull", "Download remote table dumps"), ("push", "Sync table definitions only; never records")):
        table_command = table_commands.add_parser(name, help=help_text)
        add_app_and_dir(table_command)
        if name == "pull":
            table_command.add_argument("--force", action="store_true", help="Allow overwriting changed local table files")
            table_command.add_argument("--dry-run", action="store_true")
        if name == "push":
            add_apply(table_command)
    table_export = table_commands.add_parser("export", help="Download a table as CSV or ZIP, like Craft")
    table_export.add_argument("--app", required=True)
    table_export.add_argument("--table", required=True)
    table_export.add_argument("--output", required=True, help="Output path; the extension is set to .csv or .zip")
    for name, help_text in (("insert", "Batch insert rows"), ("delete-records", "Delete explicit row IDs"), ("clear", "Wipe all rows, preserving the table definition")):
        table_command = table_commands.add_parser(name, help=help_text)
        table_command.add_argument("--app", required=True)
        table_command.add_argument("--table", required=True)
        if name != "clear":
            table_command.add_argument("--owner", default="", help="Required for user-scoped tables")
        if name == "insert":
            table_command.add_argument("--records-file", required=True)
        elif name == "delete-records":
            table_command.add_argument("--ids", nargs="+", required=True)
        else:
            table_command.add_argument("--confirm", required=True)
            table_command.add_argument("--expected-count", type=int, required=True)
        add_apply(table_command)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    token = args.token.strip() or read_wingman_token()
    if not token and not args.user_token:
        raise CliError("Set WINGMAN_TOKEN (or --token), or set HANGARKIT_USER_TOKEN for local development.")
    client = Client(args.base_url, token, args.user_token.strip(), max(1, args.timeout))
    if args.command == "status":
        command_status(client, args)
    elif args.command == "diff":
        command_diff(client, args)
    elif args.command == "pull":
        command_pull(client, args)
    elif args.command == "push":
        command_push(client, args)
    elif args.command == "create":
        command_create(client, args)
    elif args.command in {"check", "publish"}:
        command_check_or_publish(client, args, args.command)
    elif args.command == "deploy":
        command_deploy(client, args)
    elif args.command == "release":
        command_release(client, args)
    elif args.command == "export":
        command_export(client, args)
    elif args.command == "delete":
        command_delete(client, args)
    elif args.command == "metadata":
        if args.metadata_command == "diff":
            command_metadata_diff(client, args)
        elif args.metadata_command == "pull":
            command_metadata_pull(client, args)
        else:
            command_metadata_push(client, args)
    elif args.command == "tables":
        if args.tables_command == "diff":
            command_tables_diff(client, args)
        elif args.tables_command == "pull":
            command_tables_pull(client, args)
        elif args.tables_command == "export":
            command_tables_export(client, args)
        elif args.tables_command == "push":
            command_tables_push(client, args)
        else:
            command_table_records(client, args)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
