<script lang="ts">
	import { format_number } from '../lib/data'
	import type { ChartPoint } from '../lib/types'

	let { points, title, on_select }: { points: ChartPoint[]; title: string; on_select: (label: string) => void } = $props()
	let maximum = $derived(Math.max(...points.map((point) => point.value), 1))
</script>

<section class="panel chart-panel">
	<div class="panel-head"><div><p>Distribution</p><h2>{title}</h2></div><span>Top {points.length}</span></div>
	{#if points.length}
		<div class="bars" role="list" aria-label={title}>
			{#each points as point}
				<button type="button" class="bar-row" onclick={() => on_select(point.label)} title={`Filter to ${point.label}`}>
					<span class="label">{point.label}</span><span class="track"><i style:width={`${Math.max(2, point.value / maximum * 100)}%`}></i></span><strong>{format_number(point.value)}</strong>
				</button>
			{/each}
		</div>
	{:else}<div class="empty">Choose a group-by field and load a source to generate a chart.</div>{/if}
</section>

<style>
	.panel { border: 1px solid var(--border-color); border-radius: var(--panel-radius); background: var(--panel-background); } .chart-panel { padding: 1rem; min-height: 260px; }.panel-head { display: flex; align-items: start; justify-content: space-between; gap: 1rem; }.panel-head p, h2 { margin: 0; }.panel-head p { color: var(--muted-ink-color); font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; } h2 { margin-top: .2rem; font-size: 1rem; }.panel-head > span { color: var(--muted-ink-color); font-size: .75rem; }.bars { display: grid; gap: .5rem; margin-top: 1rem; }.bar-row { display: grid; grid-template-columns: minmax(90px, .85fr) minmax(100px, 2fr) auto; align-items: center; gap: .65rem; width: 100%; border: 0; padding: .27rem 0; color: var(--ink-color); background: transparent; text-align: left; font: inherit; cursor: pointer; }.bar-row:hover .track { background: color-mix(in srgb, var(--accent-color) 16%, var(--page-background)); }.label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: .8rem; }.track { height: .55rem; overflow: hidden; border-radius: 999px; background: var(--page-background); }.track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--accent-color), color-mix(in srgb, var(--accent-color) 55%, #fff)); }.bar-row strong { min-width: 3.5rem; text-align: right; font-size: .78rem; }.empty { display: grid; min-height: 190px; place-items: center; color: var(--muted-ink-color); text-align: center; font-size: .85rem; }
</style>
