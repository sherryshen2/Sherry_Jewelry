# Scheduled cron jobs

ID: `backend.cron`
Category: `backend`

Register published Python functions for Hangar-managed scheduling, wake-up, retries, run history, and manual execution.

## Import

`from hangarkit import cron`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `cron.job(name=None, *, schedule, timezone="UTC", timeout_seconds=300, retries=0, concurrency="forbid", misfire_grace_seconds=300, enabled=True)`
- `cron.current_run()`
- `cron.is_scheduled_run()`

## Details

Use `@cron.job` to declare work that Hangar must run on a schedule. Hangar records the manifest during a successful automatic update. Saved coherent edits update schedules after the Craft turn completes; incomplete or failed builds do not replace the active code. Jobs are checked against the active version and fail closed if schedule reconciliation is incomplete. Retry repairs reconciliation.

Published backends remain scale-to-zero: Hangar prewarms the released backend shortly before a due job, invokes the job with an internal token, and lets the backend stop again after its idle window. Ordinary app traffic uses the same on-demand lifecycle.

New apps and source-growing edits support 80 MiB across the serialized virtual
filesystem. This aggregate includes frontend and backend files; splitting source
into smaller files does not reduce the total. Existing oversized apps continue
to run and may shrink, but cannot grow further.

```python
from hangarkit import cron, table

@cron.job(
    name="daily-summary",
    schedule="0 9 * * 1-5",
    timezone="Asia/Singapore",
    timeout_seconds=300,
    retries=2,
    concurrency="forbid",
    misfire_grace_seconds=300,
)
def daily_summary(run: cron.Run):
    pending = table("items").list(filter='status = "pending"', perPage=100)
    return {"processed": len(pending), "run_id": run.id}
```

`schedule` is a standard five-field cron expression: minute, hour, day of month, month, and day of week. `timezone` must be an IANA timezone name such as `UTC` or `Asia/Singapore`.

The decorated function may be synchronous or asynchronous and may accept either zero arguments or one `cron.Run` argument. A run provides `id`, `job_name`, `scheduled_at`, `triggered_at`, `attempt`, `trigger`, and `idempotency_key`. External side effects should use `idempotency_key` because scheduled delivery is at least once and retries may repeat work after an uncertain failure.

`concurrency="forbid"` skips a new occurrence while an earlier run is active. `concurrency="allow"` permits overlap. A missed occurrence runs once after Hangar recovers only when it is within `misfire_grace_seconds`.

Scheduled functions run as the app's backend system identity. `table`, cache, secrets, and app-auth integrations are available. There is no signed-in browser user, so `ctx.current_user` is empty and integrations that require `auth_mode="user"` cannot borrow a user credential.

Craft's Others > Scheduled panel shows the published jobs, next run, pause override, manual Run now control, attempts, results, and errors. Its internal tab ID remains `automations` for existing links. Pausing is a platform override; publishing new code preserves it. Removing a decorator disables the published job while retaining its history.
## Quick examples

- `@cron.job(name="daily-sync", schedule="0 9 * * *", timezone="Asia/Singapore")`

## Related capabilities

- `backend.hangarkit`
- `backend.integrations`
- `runtime.routing`
