<script lang="ts">
	import { format_number } from '../lib/data'
	import type { ChartPoint } from '../lib/types'

	let { points, title, subtitle }: { points: ChartPoint[]; title: string; subtitle: string } = $props()
	const colours = ['#5b4ee5', '#16a34a', '#f59e0b', '#ef4444', '#0ea5e9', '#a855f7']
	let total = $derived(points.reduce((sum, point) => sum + point.value, 0))
	let chart = $derived.by(() => {
		let cursor = 0
		return points.slice(0, 6).map((point, index) => {
			const start = total ? cursor / total * 100 : 0
			cursor += point.value
			return `${colours[index % colours.length]} ${start}% ${total ? cursor / total * 100 : 0}%`
		}).join(', ')
	})
</script>

<section class="panel donut-chart">
	<div class="panel-head"><div><p>{subtitle}</p><h2>{title}</h2></div><span>Top {Math.min(points.length, 6)}</span></div>
	{#if points.length}
		<div class="donut-wrap"><div class="donut" style:background={`conic-gradient(${chart})`}><div><strong>{format_number(total)}</strong><small>Total</small></div></div><ul>{#each points.slice(0, 6) as point, index}<li><i style:background={colours[index % colours.length]}></i><span>{point.label}</span><strong>{total ? Math.round(point.value / total * 100) : 0}%</strong></li>{/each}</ul></div>
	{:else}<div class="empty">Load a source to compare category share.</div>{/if}
</section>

<style>
	.panel { border: 1px solid var(--border-color); border-radius: var(--panel-radius); background: var(--panel-background); }.donut-chart { min-height: 314px; padding: 1rem; }.panel-head { display: flex; justify-content: space-between; gap: 1rem; }.panel-head p, h2 { margin: 0; }.panel-head p { color: var(--muted-ink-color); font-size: .7rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }h2 { margin-top: .22rem; font-size: 1rem; }.panel-head > span { color: var(--muted-ink-color); font-size: .75rem; }.donut-wrap { display: grid; grid-template-columns: 130px minmax(0, 1fr); align-items: center; gap: 1.1rem; min-height: 224px; }.donut { display: grid; aspect-ratio: 1; place-items: center; border-radius: 50%; }.donut > div { display: grid; width: 62%; aspect-ratio: 1; place-items: center; align-content: center; border-radius: 50%; background: var(--panel-background); text-align: center; }.donut strong { font-size: .86rem; }.donut small { color: var(--muted-ink-color); font-size: .68rem; }ul { display: grid; gap: .5rem; margin: 0; padding: 0; list-style: none; }li { display: grid; grid-template-columns: .55rem minmax(0, 1fr) auto; align-items: center; gap: .45rem; font-size: .78rem; }li i { width: .55rem; height: .55rem; border-radius: 50%; }li span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }li strong { font-size: .74rem; }.empty { display: grid; min-height: 220px; place-items: center; color: var(--muted-ink-color); text-align: center; font-size: .85rem; }@media (max-width: 460px) { .donut-wrap { grid-template-columns: 1fr; }.donut { width: 140px; justify-self: center; } }
</style>
