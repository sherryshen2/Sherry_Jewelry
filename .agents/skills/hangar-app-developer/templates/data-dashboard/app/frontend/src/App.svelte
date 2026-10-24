<script lang="ts">
	// @ts-nocheck
	import content from '$content'
	import SourcePanel from './components/SourcePanel.svelte'
	import ChartPanel from './components/ChartPanel.svelte'
	import DataTable from './components/DataTable.svelte'
	import DonutChart from './components/DonutChart.svelte'
	import LineChart from './components/LineChart.svelte'
	import { load_datasuite, load_google_sheet, upload_csv } from './lib/api'
	import { aggregate, combine_datasets, columns_for, data_columns, filter_rows, format_number, numeric_columns, preferred_column, series, sum_values } from './lib/data'
	import { LOCAL_DEMO_DATASET } from './lib/sample-data'
	import type { Aggregation, Dataset } from './lib/types'

	type Page = 'home' | 'sources' | 'records' | 'config'
	const pages: { id: Page; label: string }[] = [
		{ id: 'home', label: 'Home' },
		{ id: 'sources', label: 'Data sources' },
		{ id: 'records', label: 'Records' },
		{ id: 'config', label: 'Configuration' }
	]

	let page = $state<Page>('home')
	let datasets = $state<Dataset[]>([LOCAL_DEMO_DATASET])
	let busy = $state(false)
	let error = $state('')
	let notice = $state('Local demo data is ready to explore.')
	let search = $state('')
	let filter_column = $state('')
	let filter_values = $state<string[]>([])
	let record_group = $state('')
	let record_metric = $state('__count')
	let record_operation = $state<Aggregation>('count')

	let rows = $derived(combine_datasets(datasets))
	let fields = $derived(data_columns(rows))
	let numeric = $derived(numeric_columns(rows))
	let displayed_columns = $derived(['_source', ...fields.slice(0, 11)])
	let filtered_rows = $derived(filter_rows(rows, search, filter_column, filter_values))
	let available_values = $derived(filter_column ? [...new Set(rows.map((row) => String(row[filter_column] ?? '(blank)')))].sort().slice(0, 80) : [])

	let metric_field = $derived(preferred_column(numeric, ['netsales', 'sales', 'revenue', 'amount'], numeric[0] || ''))
	let trend_field = $derived(preferred_column(fields, ['month', 'date', 'week', 'period'], fields[0] || ''))
	let region_field = $derived(preferred_column(fields, ['region', 'country', 'market', 'area'], trend_field))
	let segment_field = $derived(preferred_column(fields, ['channel', 'segment', 'type', 'category'], region_field))
	let target_field = $derived(preferred_column(numeric, ['target', 'goal', 'budget'], ''))
	let trend_points = $derived(trend_field ? series(rows, trend_field, metric_field || '__count') : [])
	let region_points = $derived(region_field ? aggregate(rows, region_field, metric_field || '__count', metric_field ? 'sum' : 'count') : [])
	let segment_points = $derived(segment_field ? aggregate(rows, segment_field, metric_field || '__count', metric_field ? 'sum' : 'count') : [])
	let record_points = $derived(record_group ? aggregate(filtered_rows, record_group, record_metric, record_operation) : [])
	let metric_total = $derived(metric_field ? sum_values(rows, metric_field) : rows.length)
	let target_total = $derived(target_field ? sum_values(rows, target_field) : 0)

	async function run(action: () => Promise<void>) {
		busy = true
		error = ''
		notice = ''
		try { await action() } catch (cause) { error = cause instanceof Error ? cause.message : 'The source could not be loaded.' } finally { busy = false }
	}

	function add_dataset(dataset: Dataset) {
		datasets = [...datasets.filter((item) => item.name !== dataset.name), dataset]
		notice = `${dataset.name} loaded with ${dataset.row_count.toLocaleString()} records.`
	}

	async function add_csv(files: File[]) { await run(async () => { const result = await upload_csv(files); result.datasets.forEach(add_dataset); if (result.errors.length) error = result.errors.map((item) => `${item.name}: ${item.error}`).join(' ') }) }
	async function add_sheet(spreadsheet: string, range_name: string) { await run(async () => add_dataset(await load_google_sheet(spreadsheet, range_name))) }
	async function add_datasuite(config) { await run(async () => add_dataset(await load_datasuite(config))) }
	function use_local_demo() { add_dataset(LOCAL_DEMO_DATASET); page = 'home' }
	function remove_dataset(name: string) { datasets = datasets.filter((dataset) => dataset.name !== name); notice = `${name} removed.` }
	function open_records(label: string) { filter_column = region_field; filter_values = [label]; page = 'records' }
	function clear_record_filters() { search = ''; filter_column = ''; filter_values = [] }
	function source_label(type: string) { return type === 'google_sheets' ? 'Google Sheets' : type === 'datasuite' ? 'Datasuite API' : type === 'local' ? 'Local data' : 'CSV upload' }
</script>

<svelte:head><title>{content.app_title || '__HANGAR_APP_NAME__'}</title></svelte:head>

<main>
	<header class="app-header">
		<div class="brand"><span class="brand-mark">◈</span><div><p>Data workspace</p><strong>{content.app_title || '__HANGAR_APP_NAME__'}</strong></div></div>
		<nav aria-label="Dashboard pages">{#each pages as item}<button class:current={page === item.id} aria-current={page === item.id ? 'page' : undefined} onclick={() => page = item.id}>{item.label}</button>{/each}</nav>
		<div class="source-count"><span class:ready={rows.length > 0}></span>{datasets.length} data source{datasets.length === 1 ? '' : 's'}</div>
	</header>

	{#if error}<div class="notice error"><strong>Could not load source.</strong> {error}</div>{/if}
	{#if notice}<div class="notice success">{notice}</div>{/if}

	{#if page === 'home'}
		<section class="home-hero"><div><p class="eyebrow">Overview</p><h1>{content.app_title || '__HANGAR_APP_NAME__'}</h1><p>{content.description || 'A schema-agnostic dashboard for connected data.'}</p></div><button type="button" onclick={() => page = 'config'}>Configure data sources</button></section>
		<section class="kpis"><article><span>{metric_field || 'Records'}</span><strong>{format_number(metric_total)}</strong><small>across all sources</small></article><article><span>Records</span><strong>{format_number(rows.length)}</strong><small>schema-agnostic rows</small></article><article><span>Fields</span><strong>{fields.length}</strong><small>{numeric.length} numeric fields</small></article><article><span>{target_field ? 'Target variance' : 'Sources'}</span><strong>{target_field ? format_number(metric_total - target_total) : datasets.length}</strong><small>{target_field ? 'actual minus target' : 'currently connected'}</small></article></section>
		<section class="chart-grid primary"><LineChart points={trend_points} title={trend_field ? `${metric_field || 'Records'} over ${trend_field}` : 'Trend'} subtitle="Trend" /><DonutChart points={segment_points} title={segment_field ? `${metric_field || 'Records'} by ${segment_field}` : 'Breakdown'} subtitle="Composition" /></section>
		<section class="chart-grid secondary"><ChartPanel points={region_points} title={region_field ? `${metric_field || 'Records'} by ${region_field}` : 'Top groups'} on_select={open_records} /><section class="source-health"><div><p>Data sources</p><h2>Connected for this view</h2></div><ul>{#each datasets as dataset}<li><span class="dot {dataset.source_type}"></span><div><strong>{dataset.name}</strong><small>{source_label(dataset.source_type)} · {dataset.row_count.toLocaleString()} records</small></div></li>{/each}</ul><button type="button" class="quiet" onclick={() => page = 'sources'}>Manage data sources</button></section></section>
	{:else if page === 'sources'}
		<section class="page-title"><div><p class="eyebrow">Data sources</p><h1>What powers this dashboard</h1><span>Every source keeps its own identity and fields. Records are combined only for analysis.</span></div><button type="button" onclick={() => page = 'config'}>Add a source</button></section>
		<section class="source-list">{#each datasets as dataset}<article><div class="source-icon {dataset.source_type}">{dataset.source_type === 'local' ? '◇' : dataset.source_type === 'csv' ? '↥' : dataset.source_type === 'google_sheets' ? '▦' : '⌁'}</div><div class="source-info"><span>{source_label(dataset.source_type)}</span><h2>{dataset.name}</h2><p>{dataset.row_count.toLocaleString()} records · {dataset.columns.filter((column) => !column.startsWith('_')).length} detected fields</p><div class="field-chips">{#each dataset.columns.filter((column) => !column.startsWith('_')).slice(0, 7) as column}<code>{column}</code>{/each}</div></div><button type="button" class="remove" onclick={() => remove_dataset(dataset.name)}>Remove</button></article>{:else}<div class="empty-state"><h2>No sources yet</h2><p>Add a local, CSV, Google Sheets, or Datasuite source from Configuration.</p></div>{/each}</section>
	{:else if page === 'records'}
		<section class="page-title compact"><div><p class="eyebrow">Records</p><h1>Explore the combined data</h1><span>Search, filter, and inspect raw records without crowding the homepage.</span></div></section>
		<section class="record-controls"><label>Search all records<input bind:value={search} placeholder="Search loaded records" /></label><label>Filter field<select bind:value={filter_column} onchange={() => filter_values = []}><option value="">All fields</option>{#each fields as field}<option value={field}>{field}</option>{/each}</select></label>{#if filter_column}<label>Values<select multiple bind:value={filter_values}>{#each available_values as value}<option value={value}>{value}</option>{/each}</select></label>{/if}<button class="quiet" type="button" onclick={clear_record_filters} disabled={!search && !filter_column}>Clear filters</button></section>
		<section class="record-chart-controls"><label>Group by<select bind:value={record_group}>{#each fields as field}<option value={field}>{field}</option>{/each}</select></label><label>Metric<select bind:value={record_metric}><option value="__count">Record count</option>{#each numeric as field}<option value={field}>{field}</option>{/each}</select></label><label>Aggregation<select bind:value={record_operation}><option value="count">Count</option><option value="sum">Sum</option><option value="average">Average</option><option value="minimum">Minimum</option><option value="maximum">Maximum</option></select></label></section>
		<ChartPanel points={record_points} title={record_group ? `${record_metric === '__count' ? 'Record count' : record_metric} by ${record_group}` : 'Choose a group'} on_select={() => {}} />
		<div class="records-table"><DataTable rows={filtered_rows} columns={displayed_columns} /></div>
	{:else}
		<SourcePanel {datasets} {busy} on_csv={add_csv} on_sheet={add_sheet} on_datasuite={add_datasuite} on_use_local_demo={use_local_demo} />
	{/if}
</main>

<style>
	:global(*) { box-sizing: border-box; }:global(body) { margin: 0; color: var(--ink-color, #18202f); background: var(--page-background, #f6f7fb); font-family: var(--font-family, Inter, ui-sans-serif, system-ui, sans-serif); }main { width: min(1440px, 100%); margin: 0 auto; padding: 1.2rem 2.2rem 2.5rem; }.app-header { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 1.5rem; min-height: 62px; border-bottom: 1px solid var(--border-color); }.brand, .brand > div, nav, .source-count, .source-health li { display: flex; align-items: center; gap: .6rem; }.brand-mark { display: grid; width: 1.85rem; height: 1.85rem; place-items: center; border-radius: 8px; color: white; background: var(--accent-color); }.brand p { margin: 0 0 .1rem; color: var(--muted-ink-color); font-size: .62rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }.brand strong { font-size: .86rem; }nav { justify-content: center; gap: .18rem; }nav button { border: 0; border-radius: 7px; padding: .5rem .65rem; color: var(--muted-ink-color); background: transparent; font: inherit; font-size: .8rem; font-weight: 750; cursor: pointer; }nav button.current { color: var(--accent-color); background: color-mix(in srgb, var(--accent-color) 11%, white); }.source-count { justify-content: end; color: var(--muted-ink-color); font-size: .74rem; white-space: nowrap; }.source-count span { width: .5rem; height: .5rem; border-radius: 50%; background: #98a2b3; }.source-count span.ready { background: #12b76a; }.notice { margin: 1rem 0; padding: .75rem .9rem; border-radius: 8px; font-size: .84rem; }.notice.error { color: #b42318; background: #fef3f2; }.notice.success { color: #067647; background: #ecfdf3; }.home-hero, .page-title { display: flex; justify-content: space-between; align-items: end; gap: 2rem; padding: 2.5rem 0 1.4rem; }.eyebrow { margin: 0 0 .45rem; color: var(--accent-color); font-size: .7rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }h1 { max-width: 760px; margin: 0; font-size: clamp(2rem, 4vw, 3.25rem); letter-spacing: -.055em; }.home-hero p:not(.eyebrow), .page-title span { display: block; max-width: 690px; margin: .65rem 0 0; color: var(--muted-ink-color); line-height: 1.55; }.home-hero > button, .page-title > button { border: 0; border-radius: 8px; padding: .7rem .9rem; color: white; background: var(--accent-color); font: inherit; font-size: .82rem; font-weight: 750; cursor: pointer; white-space: nowrap; }.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; margin-bottom: .9rem; }.kpis article { display: grid; gap: .16rem; padding: .9rem; border: 1px solid var(--border-color); border-radius: var(--panel-radius); background: var(--panel-background); }.kpis span, .kpis small { color: var(--muted-ink-color); font-size: .72rem; }.kpis strong { font-size: 1.42rem; letter-spacing: -.04em; }.chart-grid { display: grid; gap: .85rem; margin-top: .85rem; }.chart-grid.primary { grid-template-columns: minmax(0, 1.45fr) minmax(300px, .8fr); }.chart-grid.secondary { grid-template-columns: minmax(0, 1.45fr) minmax(300px, .8fr); }.source-health { display: grid; gap: .8rem; align-content: start; padding: 1rem; border: 1px solid var(--border-color); border-radius: var(--panel-radius); background: var(--panel-background); }.source-health p, .source-health h2 { margin: 0; }.source-health p { color: var(--muted-ink-color); font-size: .7rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }.source-health h2 { margin-top: .2rem; font-size: 1rem; }.source-health ul { display: grid; gap: .6rem; margin: 0; padding: 0; list-style: none; }.source-health li { align-items: start; }.source-health li div { min-width: 0; }.source-health li strong, .source-health li small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.source-health li strong { font-size: .78rem; }.source-health li small { margin-top: .15rem; color: var(--muted-ink-color); font-size: .7rem; }.dot { width: .52rem; height: .52rem; margin-top: .28rem; border-radius: 50%; background: #64748b; }.dot.csv { background: #2b7fff; }.dot.google_sheets { background: #1a9d5c; }.dot.datasuite { background: #8b5cf6; }.dot.local { background: var(--accent-color); }.quiet, .remove { border: 1px solid var(--border-color); border-radius: 7px; padding: .55rem .7rem; color: var(--ink-color); background: var(--panel-background); font: inherit; font-size: .76rem; font-weight: 700; cursor: pointer; }.quiet { justify-self: start; }.page-title.compact { padding-bottom: 1rem; }.source-list { display: grid; gap: .75rem; }.source-list article { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 1rem; align-items: start; padding: 1rem; border: 1px solid var(--border-color); border-radius: var(--panel-radius); background: var(--panel-background); }.source-icon { display: grid; width: 2.25rem; height: 2.25rem; place-items: center; border-radius: 8px; color: #475467; background: #f1f5f9; font-weight: 800; }.source-icon.csv { color: #1d4ed8; background: #dbeafe; }.source-icon.google_sheets { color: #15803d; background: #dcfce7; }.source-icon.datasuite { color: #7e22ce; background: #f3e8ff; }.source-icon.local { color: var(--accent-color); background: color-mix(in srgb, var(--accent-color) 12%, white); }.source-info { min-width: 0; }.source-info > span { color: var(--muted-ink-color); font-size: .7rem; font-weight: 800; letter-spacing: .07em; text-transform: uppercase; }.source-info h2 { margin: .2rem 0; font-size: 1rem; }.source-info p { margin: 0; color: var(--muted-ink-color); font-size: .78rem; }.field-chips { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .65rem; }.field-chips code { padding: .22rem .38rem; border-radius: 4px; color: #475467; background: var(--page-background); font-size: .68rem; }.remove { color: #b42318; }.empty-state { padding: 3rem; border: 1px dashed var(--border-color); border-radius: var(--panel-radius); color: var(--muted-ink-color); text-align: center; }.empty-state h2 { margin: 0; color: var(--ink-color); font-size: 1rem; }.empty-state p { margin: .4rem 0 0; }.record-controls, .record-chart-controls { display: grid; align-items: end; gap: .6rem; margin-bottom: .8rem; padding: .85rem; border: 1px solid var(--border-color); border-radius: var(--panel-radius); background: var(--panel-background); }.record-controls { grid-template-columns: minmax(150px, 1.4fr) minmax(120px, .9fr) minmax(120px, .9fr) auto; }.record-chart-controls { grid-template-columns: repeat(3, minmax(0, 1fr)); }label { display: grid; gap: .28rem; color: var(--muted-ink-color); font-size: .7rem; font-weight: 750; letter-spacing: .02em; }input, select { min-width: 0; width: 100%; border: 1px solid var(--border-color); border-radius: 6px; padding: .55rem .6rem; color: var(--ink-color); background: var(--page-background); font: inherit; font-size: .8rem; }select[multiple] { min-height: 2.25rem; }.quiet:disabled { opacity: .45; cursor: default; }.records-table { margin-top: .85rem; }@media (max-width: 980px) { .app-header { grid-template-columns: 1fr auto; }.app-header nav { grid-column: 1 / -1; grid-row: 2; justify-content: start; overflow-x: auto; }.chart-grid.primary, .chart-grid.secondary { grid-template-columns: 1fr; }.kpis { grid-template-columns: repeat(2, 1fr); }.record-controls { grid-template-columns: 1fr 1fr; } }@media (max-width: 620px) { main { padding: 1rem; }.home-hero, .page-title { align-items: start; flex-direction: column; gap: 1rem; padding-top: 1.6rem; }.kpis, .record-controls, .record-chart-controls { grid-template-columns: 1fr; }.source-list article { grid-template-columns: auto minmax(0, 1fr); }.source-list .remove { grid-column: 2; justify-self: start; }.source-count { display: none; } }
</style>
