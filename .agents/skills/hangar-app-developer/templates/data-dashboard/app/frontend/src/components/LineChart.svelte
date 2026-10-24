<script lang="ts">
	import { format_number } from '../lib/data'
	import type { ChartPoint } from '../lib/types'

	let { points, title, subtitle }: { points: ChartPoint[]; title: string; subtitle: string } = $props()
	const width = 620
	const height = 250
	const left = 36
	const right = 18
	const top = 20
	const bottom = 42
	let maximum = $derived(Math.max(...points.map((point) => point.value), 1))
	let path = $derived(points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${left + index * ((width - left - right) / Math.max(points.length - 1, 1))} ${height - bottom - point.value / maximum * (height - top - bottom)}`).join(' '))
	function x(index: number) { return left + index * ((width - left - right) / Math.max(points.length - 1, 1)) }
	function y(value: number) { return height - bottom - value / maximum * (height - top - bottom) }
</script>

<section class="panel line-chart">
	<div class="panel-head"><div><p>{subtitle}</p><h2>{title}</h2></div><strong>{points.length ? format_number(points.at(-1)?.value || 0) : '—'}</strong></div>
	{#if points.length}
		<svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
			<line x1={left} y1={height - bottom} x2={width - right} y2={height - bottom} class="axis" />
			<line x1={left} y1={top} x2={left} y2={height - bottom} class="axis" />
			<path d={path} class="trend" />
			{#each points as point, index}<g><circle cx={x(index)} cy={y(point.value)} r="4" /><text x={x(index)} y={height - 16} text-anchor="middle">{point.label}</text></g>{/each}
		</svg>
	{:else}<div class="empty">Load a source with a date, period, or category field to see a trend.</div>{/if}
</section>

<style>
	.panel { border: 1px solid var(--border-color); border-radius: var(--panel-radius); background: var(--panel-background); }.line-chart { min-height: 314px; padding: 1rem; }.panel-head { display: flex; justify-content: space-between; gap: 1rem; }.panel-head p, h2 { margin: 0; }.panel-head p { color: var(--muted-ink-color); font-size: .7rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }h2 { margin-top: .22rem; font-size: 1rem; }.panel-head strong { color: var(--accent-color); font-size: 1.15rem; }svg { width: 100%; height: 240px; margin-top: .6rem; overflow: visible; }.axis { stroke: var(--border-color); stroke-width: 1; }.trend { fill: none; stroke: var(--accent-color); stroke-linecap: round; stroke-linejoin: round; stroke-width: 3; }circle { fill: var(--panel-background); stroke: var(--accent-color); stroke-width: 3; }text { fill: var(--muted-ink-color); font-size: 11px; }.empty { display: grid; min-height: 220px; place-items: center; color: var(--muted-ink-color); text-align: center; font-size: .85rem; }
</style>
