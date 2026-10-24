from hangarkit import cron
import sync


@cron.job(
    name="google-sheets-sync",
    schedule="*/5 * * * *",
    timezone="UTC",
    timeout_seconds=300,
    retries=2,
    concurrency="forbid",
)
def scheduled_sync(run: cron.Run):
    result = sync.sync_all()
    return {**result, "run_id": run.id, "idempotency_key": run.idempotency_key}
