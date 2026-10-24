<script lang="ts">
	let { status = 'queued' } = $props()
</script>
<span class:success={status === 'success'} class:failed={status === 'failed'} class:running={status === 'running' || status === 'idle'} class:interrupted={status === 'interrupted'}>{status}</span>
<style>
	span { width: fit-content; border-radius: 999px; padding: .2rem .52rem; color: #5d6570; background: #e9edf3; font-size: .75rem; font-weight: 650; text-transform: capitalize; }
	span.success { color: var(--success-color, #138a5b); background: color-mix(in srgb, var(--success-color, #138a5b) 12%, white); } span.failed { color: var(--danger-color, #cc3b45); background: color-mix(in srgb, var(--danger-color, #cc3b45) 12%, white); } span.running { color: var(--warning-color, #bf6d10); background: color-mix(in srgb, var(--warning-color, #bf6d10) 12%, white); } span.interrupted { color:#7647b6; background:#f1e9ff; }
</style>
