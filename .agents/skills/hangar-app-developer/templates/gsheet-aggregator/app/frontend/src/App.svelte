<script lang="ts">
	// @ts-nocheck
	import Icon from '@iconify/svelte'
	import { onMount } from 'svelte'
	import { api, language } from '$hangarkit'
	import content from '$content'
	import data from '$data'

	let sources = $state([])
	let rows = $state([])
	let runs = $state([])
	let dashboard = $state(null)
	let loading = $state(true)
	let syncing = $state(false)
	let error = $state('')
	let language_id = $state('en')
	let active_source_id = $state('source-demo')
	let source_form = $state({
		name: '',
		spreadsheet_url: '',
		sheet_name: '',
		range_name: '',
		group_by: 'Month',
		value_field: 'Revenue',
		operation: 'sum',
		enabled: true
	})

	language.subscribe((value) => {
		language_id = value.id || 'en'
	})

	data.sheet_sources.subscribe((items) => {
		sources = [...items]
		if (!active_source_id && items[0]) active_source_id = items[0].id
		const active = items.find((item) => item.id === active_source_id) || items[0]
		if (active) source_form = form_from_source(active)
	})

	data.sheet_rows.subscribe((items) => {
		rows = [...items]
	})

	data.sync_runs.subscribe((items) => {
		runs = [...items].sort((a, b) => time_value(b.started_at) - time_value(a.started_at)).slice(0, 8)
	})

	function t(key: string, fallback: string) {
		const packs = content.localized_copy || {}
		return packs[language_id]?.[key] || packs.en?.[key] || content[key] || fallback
	}

	function form_from_source(source) {
		return {
			name: source.name || '',
			spreadsheet_url: source.spreadsheet_url || '',
			sheet_name: source.sheet_name || 'Sheet1',
			range_name: source.range_name || 'Sheet1!A1:E100',
			group_by: source.group_by || 'Month',
			value_field: source.value_field || 'Revenue',
			operation: source.operation || 'sum',
			enabled: source.enabled !== false
		}
	}

	let active_source = $derived(sources.find((source) => source.id === active_source_id) || sources[0] || null)
	let chart = $derived(dashboard?.chart || local_chart())
	let max_value = $derived(Math.max(...chart.map((item) => Number(item.value) || 0), 1))
	let total_value = $derived(chart.reduce((sum, item) => sum + (Number(item.value) || 0), 0))
	let sample_mode = $derived(Boolean(active_source && !active_source.spreadsheet_url))

	function local_chart() {
		const groups = new Map()
		for (const row of rows) {
			const key = row.group || 'Uncategorized'
			const item = groups.get(key) || { label: key, value: 0, count: 0 }
			item.value += Number(row.value) || 0
			item.count += 1
			groups.set(key, item)
		}
		return [...groups.values()].sort((a, b) => a.label.localeCompare(b.label))
	}

	function time_value(value) {
		const time = new Date(value || 0).getTime()
		return Number.isFinite(time) ? time : 0
	}

	function format_number(value) {
		return new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 }).format(Number(value) || 0)
	}

	function format_date(value) {
		if (!value) return 'Not synced'
		return new Date(value).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
	}

	async function load_dashboard() {
		try {
			dashboard = await api.get('/dashboard')
		} catch (err) {
			error = err instanceof Error ? err.message : 'Dashboard failed to load'
		} finally {
			loading = false
		}
	}

	async function save_source() {
		if (!active_source) return
		error = ''
		try {
			await api.post('/sources', { id: active_source.id, ...source_form })
			await load_dashboard()
		} catch (err) {
			error = err instanceof Error ? err.message : 'Source update failed'
		}
	}

	async function sync_source() {
		if (!active_source) return
		syncing = true
		error = ''
		try {
			await save_source()
			const result = await api.post('/sync', { source_id: active_source.id })
			if (result.ok === false) throw new Error(result.error || 'Sync failed')
			await load_dashboard()
		} catch (err) {
			error = err instanceof Error ? err.message : 'Sync failed'
		} finally {
			syncing = false
		}
	}

	onMount(() => {
		load_dashboard()
	})
</script>

<svelte:head>
	<title>{content.app_title || '__HANGAR_APP_NAME__'}</title>
</svelte:head>

<main class="page">
	<header class="topbar">
		<div>
			<p>{sample_mode ? t('sample_mode', 'Sample mode') : 'Google Sheets'}</p>
			<h1>{content.app_title || '__HANGAR_APP_NAME__'}</h1>
			<span>{content.description}</span>
		</div>
		<button onclick={sync_source} disabled={syncing || !active_source}>
			<span class:spin={syncing}>
				<Icon icon={syncing ? 'lucide:loader-2' : 'lucide:refresh-cw'} width={16} />
			</span>
			{syncing ? t('syncing', 'Syncing...') : t('sync_now', 'Sync now')}
		</button>
	</header>

	{#if error}
		<section class="notice">
			<Icon icon="lucide:triangle-alert" width={18} />
			<span>{error}</span>
		</section>
	{/if}

	<section class="metrics" aria-label="Sheet metrics">
		<article>
			<span>Sources</span>
			<strong>{sources.length}</strong>
		</article>
		<article>
			<span>Rows</span>
			<strong>{rows.length}</strong>
		</article>
		<article>
			<span>Total</span>
			<strong>{format_number(total_value)}</strong>
		</article>
		<article>
			<span>{t('last_sync', 'Last sync')}</span>
			<strong>{format_date(active_source?.last_synced_at)}</strong>
		</article>
	</section>

	<section class="layout">
		<aside class="panel source-panel">
			<div class="panel-head">
				<h2>{t('sources_title', 'Sheet sources')}</h2>
				<span>{active_source?.last_status || 'Ready'}</span>
			</div>

			{#if sources.length > 1}
				<label>
					<span>Active source</span>
					<select bind:value={active_source_id}>
						{#each sources as source}
							<option value={source.id}>{source.name}</option>
						{/each}
					</select>
				</label>
			{/if}

			<label>
				<span>{t('source_name', 'Source name')}</span>
				<input bind:value={source_form.name} />
			</label>
			<label>
				<span>{t('spreadsheet_url', 'Spreadsheet URL or ID')}</span>
				<input bind:value={source_form.spreadsheet_url} placeholder="https://docs.google.com/spreadsheets/d/..." />
			</label>
			<div class="two">
				<label>
					<span>{t('sheet_name', 'Sheet name')}</span>
					<input bind:value={source_form.sheet_name} />
				</label>
				<label>
					<span>{t('range_name', 'Range')}</span>
					<input bind:value={source_form.range_name} />
				</label>
			</div>
			<div class="two">
				<label>
					<span>{t('group_by', 'Group by')}</span>
					<input bind:value={source_form.group_by} />
				</label>
				<label>
					<span>{t('value_field', 'Value field')}</span>
					<input bind:value={source_form.value_field} />
				</label>
			</div>
			<label>
				<span>{t('operation', 'Operation')}</span>
				<select bind:value={source_form.operation}>
					<option value="sum">Sum</option>
					<option value="avg">Average</option>
					<option value="count">Count rows</option>
				</select>
			</label>
			<button class="secondary" onclick={save_source}>Save source</button>
		</aside>

		<section class="panel chart-panel">
			<div class="panel-head">
				<h2>{t('chart_title', 'Latest chart')}</h2>
				<span>{source_form.operation}</span>
			</div>

			{#if loading}
				<div class="empty">Loading dashboard...</div>
			{:else if chart.length === 0}
				<div class="empty">{t('no_rows', 'No rows imported yet. Sync a source to populate the dashboard.')}</div>
			{:else}
				<div class="bars">
					{#each chart as item}
						<div class="bar-row">
							<span>{item.label}</span>
							<div class="bar-track">
								<i style={`width:${Math.max(4, ((Number(item.value) || 0) / max_value) * 100)}%`}></i>
							</div>
							<strong>{format_number(item.value)}</strong>
						</div>
					{/each}
				</div>
			{/if}
		</section>
	</section>

	<section class="bottom-grid">
		<section class="panel">
			<div class="panel-head">
				<h2>{t('rows_title', 'Imported rows')}</h2>
				<span>{rows.length}</span>
			</div>
			<div class="table-wrap">
				<table>
					<thead>
						<tr>
							<th>Group</th>
							<th>Label</th>
							<th>Value</th>
							<th>Synced</th>
						</tr>
					</thead>
					<tbody>
						{#each rows.slice(0, 12) as row}
							<tr>
								<td>{row.group}</td>
								<td>{row.label}</td>
								<td>{format_number(row.value)}</td>
								<td>{format_date(row.synced_at)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>

		<section class="panel">
			<div class="panel-head">
				<h2>Sync runs</h2>
				<span>{runs.length}</span>
			</div>
			<div class="runs">
				{#each runs as run}
					<article class:error={run.status === 'error'}>
						<strong>{run.status}</strong>
						<span>{format_date(run.completed_at || run.started_at)}</span>
						<small>{run.rows_saved || 0} rows saved{run.error ? ` · ${run.error}` : ''}</small>
					</article>
				{:else}
					<div class="empty">No sync runs yet.</div>
				{/each}
			</div>
		</section>
	</section>
</main>

<style>
	:global(body) {
		margin: 0;
		background: var(--page-background, #f2f5f7);
		color: var(--ink-color, #172033);
		font-family: var(--font-family, Inter), ui-sans-serif, system-ui, sans-serif;
	}

	.page {
		min-height: 100vh;
		padding: clamp(1rem, 3vw, 2rem);
		display: grid;
		gap: 1rem;
	}

	.topbar,
	.metrics,
	.layout,
	.bottom-grid {
		width: min(1180px, 100%);
		margin: 0 auto;
	}

	.topbar {
		display: flex;
		align-items: end;
		justify-content: space-between;
		gap: 1rem;
	}

	.topbar p,
	.topbar h1 {
		margin: 0;
	}

	.topbar p {
		color: var(--accent-color, #16796f);
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
	}

	.topbar h1 {
		font-size: clamp(1.9rem, 4vw, 3.6rem);
		letter-spacing: 0;
	}

	.topbar span,
	.panel-head span,
	label span,
	td,
	.runs span,
	.runs small {
		color: var(--muted-ink-color, #617083);
	}

	button,
	input,
	select {
		font: inherit;
	}

	button {
		border: 0;
		border-radius: 6px;
		background: var(--accent-color, #16796f);
		color: white;
		padding: 0.68rem 0.9rem;
		font-weight: 800;
		display: inline-flex;
		align-items: center;
		gap: 0.45rem;
		cursor: pointer;
	}

	button:disabled {
		opacity: 0.55;
		cursor: not-allowed;
	}

	button.secondary {
		justify-content: center;
		background: var(--ink-color, #172033);
	}

	.spin {
		animation: spin 0.9s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.notice,
	.panel,
	.metrics article {
		background: var(--panel-background, #ffffff);
		border: 1px solid var(--border-color, #d9e2e6);
		border-radius: var(--panel-radius, 8px);
	}

	.notice {
		width: min(1180px, 100%);
		margin: 0 auto;
		padding: 0.8rem 1rem;
		display: flex;
		gap: 0.6rem;
		color: #b42318;
	}

	.metrics {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.8rem;
	}

	.metrics article {
		padding: 1rem;
		display: grid;
		gap: 0.35rem;
	}

	.metrics span {
		color: var(--muted-ink-color, #617083);
		font-size: 0.8rem;
	}

	.metrics strong {
		font-size: 1.45rem;
	}

	.layout,
	.bottom-grid {
		display: grid;
		grid-template-columns: 360px minmax(0, 1fr);
		gap: 1rem;
		align-items: start;
	}

	.panel {
		padding: 1rem;
		min-width: 0;
	}

	.panel-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.panel-head h2 {
		margin: 0;
		font-size: 1rem;
	}

	.source-panel {
		display: grid;
		gap: 0.8rem;
	}

	label {
		display: grid;
		gap: 0.35rem;
		font-size: 0.82rem;
		font-weight: 700;
	}

	input,
	select {
		width: 100%;
		box-sizing: border-box;
		border: 1px solid var(--border-color, #d9e2e6);
		border-radius: 6px;
		padding: 0.6rem 0.7rem;
		background: var(--soft-panel, #eef4f2);
		color: var(--ink-color, #172033);
	}

	.two {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.65rem;
	}

	.chart-panel {
		min-height: 430px;
	}

	.bars {
		display: grid;
		gap: 0.75rem;
	}

	.bar-row {
		display: grid;
		grid-template-columns: minmax(80px, 0.45fr) minmax(0, 1fr) 80px;
		gap: 0.75rem;
		align-items: center;
	}

	.bar-track {
		height: 28px;
		background: var(--soft-panel, #eef4f2);
		border-radius: 6px;
		overflow: hidden;
	}

	.bar-track i {
		display: block;
		height: 100%;
		background: linear-gradient(90deg, var(--accent-color, #16796f), var(--warm-accent-color, #c26d2e));
	}

	.empty {
		padding: 2rem;
		text-align: center;
		color: var(--muted-ink-color, #617083);
		background: var(--soft-panel, #eef4f2);
		border-radius: 8px;
	}

	.table-wrap {
		overflow: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.88rem;
	}

	th,
	td {
		padding: 0.65rem;
		border-bottom: 1px solid var(--border-color, #d9e2e6);
		text-align: left;
		white-space: nowrap;
	}

	th {
		color: var(--ink-color, #172033);
		font-size: 0.75rem;
		text-transform: uppercase;
	}

	.runs {
		display: grid;
		gap: 0.55rem;
	}

	.runs article {
		display: grid;
		gap: 0.18rem;
		padding: 0.7rem;
		background: var(--soft-panel, #eef4f2);
		border-radius: 6px;
	}

	.runs article.error {
		background: #fff1f2;
	}

	@media (max-width: 860px) {
		.topbar,
		.layout,
		.bottom-grid {
			grid-template-columns: 1fr;
		}

		.topbar {
			align-items: start;
		}

		.metrics {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
</style>
