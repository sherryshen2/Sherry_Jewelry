<script lang="ts">
	import type { Dataset } from '../lib/types'

	let { datasets, busy = false, on_csv, on_sheet, on_datasuite, on_use_local_demo }: {
		datasets: Dataset[]
		busy?: boolean
		on_csv: (files: File[]) => void
		on_sheet: (spreadsheet: string, range_name: string) => void
		on_datasuite: (config: { api_name: string; version: string; scope: string[]; parameters: Record<string, unknown>; enable_cache: boolean }) => void
		on_use_local_demo: () => void
	} = $props()

	let sheet_url = $state('')
	let range_name = $state('Sheet1!A:ZZ')
	let api_name = $state('')
	let version = $state('')
	let scope = $state('')
	let parameters = $state('{"pageSize": "100", "pageNum": "1"}')
	let datasuite_open = $state(false)
	let form_error = $state('')

	function add_files(event: Event) {
		const files = [...((event.currentTarget as HTMLInputElement).files || [])]
		if (files.length) on_csv(files)
	}

	function add_datasuite() {
		form_error = ''
		try {
			const parsed = JSON.parse(parameters)
			if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error('Parameters must be a JSON object.')
			on_datasuite({ api_name, version, scope: scope.split(',').map((item) => item.trim()).filter(Boolean), parameters: parsed, enable_cache: true })
		} catch (error) {
			form_error = error instanceof Error ? error.message : 'Parameters must be valid JSON.'
		}
	}
</script>

<section class="source-config" aria-label="Data source configuration">
	<div class="page-heading"><div><p>Configuration</p><h2>Add a data source</h2><span>Connect sources here. The dashboard homepage stays focused on the results.</span></div><span class="counter">{datasets.length} active</span></div>
	<div class="source-grid">
		<article class="source-card local"><div><span class="source-tag">Local data</span><h3>Demo commerce data</h3><p>Start with built-in records so the dashboard has charts immediately.</p></div><button type="button" onclick={on_use_local_demo}>Use local demo</button></article>
		<article class="source-card"><div><span class="source-tag">CSV</span><h3>Upload one or more files</h3><p>Each file becomes a named datasource. Fields are unioned in the records view.</p></div><label class="upload"><input type="file" accept=".csv,text/csv" multiple onchange={add_files} disabled={busy} /><span>Choose CSV files</span></label></article>
		<article class="source-card"><div><span class="source-tag">Google Sheets</span><h3>Read a sheet range</h3></div><div class="source-form"><label>Spreadsheet URL or ID<input bind:value={sheet_url} placeholder="URL or spreadsheet ID" disabled={busy} /></label><label>A1 range<input bind:value={range_name} placeholder="Sheet1!A:ZZ" disabled={busy} /></label><button type="button" onclick={() => on_sheet(sheet_url, range_name)} disabled={busy || !sheet_url.trim()}>Add Google Sheet</button></div></article>
		<article class="source-card datasuite-card"><button type="button" class="disclosure" onclick={() => datasuite_open = !datasuite_open} aria-expanded={datasuite_open}><span><span class="source-tag">Datasuite API</span><h3>Run an API query</h3></span><span>{datasuite_open ? '−' : '+'}</span></button>{#if datasuite_open}<div class="source-form"><label>API name<input bind:value={api_name} placeholder="namespace.api_name" disabled={busy} /></label><label>Version<input bind:value={version} placeholder="version hash" disabled={busy} /></label><label>Scope<input bind:value={scope} placeholder="scope1, scope2" disabled={busy} /></label><label>Parameters (JSON)<textarea bind:value={parameters} rows="4" disabled={busy}></textarea></label>{#if form_error}<p class="form-error">{form_error}</p>{/if}<button type="button" onclick={add_datasuite} disabled={busy || !api_name || !version}>Run query</button><small>Credentials stay in Datasuite secrets; they never enter this page.</small></div>{/if}</article>
	</div>
</section>

<style>
	.source-config { display: grid; gap: 1.2rem; }.page-heading { display: flex; justify-content: space-between; gap: 1rem; align-items: start; }.page-heading p, h2, h3 { margin: 0; }.page-heading p, .source-tag { color: var(--accent-color); font-size: .7rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }.page-heading h2 { margin-top: .25rem; font-size: 1.35rem; }.page-heading span:not(.counter) { display: block; max-width: 620px; margin-top: .5rem; color: var(--muted-ink-color); line-height: 1.45; }.counter { padding: .4rem .65rem; border-radius: 999px; color: var(--accent-color); background: color-mix(in srgb, var(--accent-color) 10%, white); font-size: .76rem; font-weight: 750; white-space: nowrap; }.source-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .85rem; }.source-card { display: grid; gap: .9rem; align-content: start; padding: 1rem; border: 1px solid var(--border-color); border-radius: var(--panel-radius); background: var(--panel-background); }.source-card.local { border-color: color-mix(in srgb, var(--accent-color) 35%, var(--border-color)); background: linear-gradient(145deg, color-mix(in srgb, var(--accent-color) 8%, white), var(--panel-background)); }.source-card h3 { margin-top: .25rem; font-size: .95rem; }.source-card p { margin: .4rem 0 0; color: var(--muted-ink-color); font-size: .82rem; line-height: 1.45; }.source-form { display: grid; gap: .6rem; } label { display: grid; gap: .3rem; color: var(--muted-ink-color); font-size: .74rem; font-weight: 700; } input, textarea { min-width: 0; box-sizing: border-box; width: 100%; border: 1px solid var(--border-color); border-radius: 7px; padding: .58rem .65rem; color: var(--ink-color); background: var(--page-background); font: inherit; font-size: .82rem; } textarea { resize: vertical; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; } button, .upload { border: 0; border-radius: 7px; padding: .62rem .75rem; color: white; background: var(--accent-color); font: inherit; font-size: .8rem; font-weight: 750; cursor: pointer; text-align: center; }button:disabled { opacity: .5; cursor: wait; }.upload input { display: none; }.disclosure { display: flex; justify-content: space-between; align-items: start; padding: 0; color: var(--ink-color); background: transparent; text-align: left; }.datasuite-card { gap: .75rem; }.datasuite-card small { color: var(--muted-ink-color); font-size: .72rem; }.form-error { margin: 0; color: #b42318; font-size: .76rem; }@media (max-width: 760px) { .source-grid { grid-template-columns: 1fr; }.page-heading { flex-direction: column; } }
</style>
