<script lang="ts">
	import type { DataRow } from '../lib/types'

	let { rows, columns }: { rows: DataRow[]; columns: string[] } = $props()
	let sort_column = $state('')
	let sort_direction = $state<1 | -1>(1)
	let page = $state(0)
	let page_size = 20
	let ordered = $derived.by(() => {
		if (!sort_column) return rows
		return [...rows].sort((left, right) => String(left[sort_column] ?? '').localeCompare(String(right[sort_column] ?? ''), undefined, { numeric: true }) * sort_direction)
	})
	let pages = $derived(Math.max(1, Math.ceil(ordered.length / page_size)))
	let visible = $derived(ordered.slice(page * page_size, (page + 1) * page_size))

	function toggle_sort(column: string) { if (sort_column === column) sort_direction = sort_direction === 1 ? -1 : 1; else { sort_column = column; sort_direction = 1; } page = 0 }
	function value(row: DataRow, column: string) { const raw = row[column]; return raw === null || raw === undefined || raw === '' ? '—' : String(raw) }
</script>

<section class="table-panel">
	<div class="table-head"><div><p>Records</p><h2>Raw data</h2></div><span>{rows.length.toLocaleString()} matching rows</span></div>
	{#if rows.length}
		<div class="scroll"><table><thead><tr>{#each columns as column}<th><button type="button" onclick={() => toggle_sort(column)}>{column}{#if sort_column === column}<small>{sort_direction === 1 ? ' ↑' : ' ↓'}</small>{/if}</button></th>{/each}</tr></thead><tbody>{#each visible as row, index (index)}<tr>{#each columns as column}<td title={value(row, column)}>{value(row, column)}</td>{/each}</tr>{/each}</tbody></table></div>
		<footer><span>Page {page + 1} of {pages}</span><div><button type="button" onclick={() => page = Math.max(0, page - 1)} disabled={page === 0}>Previous</button><button type="button" onclick={() => page = Math.min(pages - 1, page + 1)} disabled={page >= pages - 1}>Next</button></div></footer>
	{:else}<div class="empty">No records match the current filters.</div>{/if}
</section>

<style>
	.table-panel { overflow: hidden; border: 1px solid var(--border-color); border-radius: var(--panel-radius); background: var(--panel-background); }.table-head, footer { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1rem; }.table-head { border-bottom: 1px solid var(--border-color); }.table-head p, h2 { margin: 0; }.table-head p { color: var(--muted-ink-color); font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }h2 { margin-top: .2rem; font-size: 1rem; }.table-head > span, footer { color: var(--muted-ink-color); font-size: .78rem; }.scroll { max-width: 100%; overflow: auto; }table { width: 100%; min-width: 680px; border-collapse: collapse; font-size: .8rem; }th { position: sticky; top: 0; z-index: 1; padding: 0; background: var(--page-background); text-align: left; }th button { width: 100%; border: 0; padding: .7rem .85rem; color: var(--muted-ink-color); background: transparent; text-align: left; font: inherit; font-weight: 700; cursor: pointer; }th button:hover { color: var(--accent-color); }td { max-width: 260px; overflow: hidden; padding: .7rem .85rem; border-top: 1px solid var(--border-color); text-overflow: ellipsis; white-space: nowrap; }tbody tr:hover { background: color-mix(in srgb, var(--accent-color) 4%, white); }footer { border-top: 1px solid var(--border-color); }footer div { display: flex; gap: .45rem; }footer button { border: 1px solid var(--border-color); border-radius: 6px; padding: .42rem .6rem; color: var(--ink-color); background: white; font: inherit; font-size: .75rem; cursor: pointer; }footer button:disabled { opacity: .45; cursor: default; }.empty { padding: 3rem 1rem; color: var(--muted-ink-color); text-align: center; }
</style>
