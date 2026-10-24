<script lang="ts">
	// @ts-nocheck
	import content from '$content'
	import { navigate } from '../lib/navigation'
	let { current = 'tasks', children } = $props()
	const links = [{ id: 'tasks', label: 'Tasks', path: '/' }, { id: 'metrics', label: 'Metrics', path: '/?view=metrics' }, { id: 'configuration', label: 'Configuration', path: '/?view=configuration' }]
</script>

<main class="shell">
	<header>
		<div><p>SMART workflow runner</p><h1>{content.app_title || '__HANGAR_APP_NAME__'}</h1></div>
		<nav aria-label="Application navigation">
			{#each links as link}
				<button class:active={current === link.id} onclick={() => navigate(link.path)}>{link.label}</button>
			{/each}
		</nav>
	</header>
	{@render children?.()}
</main>

<style>
	.shell { min-height: 100vh; padding: clamp(1rem, 3vw, 2.5rem); background: radial-gradient(circle at 18% -10%, #edf3ff 0, transparent 29rem), var(--page-background, #f7f9fc); color: var(--ink-color, #1c2638); font-family: var(--font-family, Inter), ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; letter-spacing: -.008em; }
	header { width: min(1180px, 100%); margin: 0 auto 1.75rem; display: flex; justify-content: space-between; gap: 1rem; align-items: end; }
	p, h1 { margin: 0; } header p { color: var(--accent-color, #3159db); font-size: .72rem; font-weight: 650; letter-spacing: .1em; text-transform: uppercase; } h1 { margin-top: .28rem; font-size: clamp(1.45rem, 3vw, 2rem); font-weight: 600; letter-spacing: -.04em; }
	nav { display: flex; gap: .25rem; padding: .25rem; border: 1px solid #dfe6f0; border-radius: 11px; background: #ffffffb8; box-shadow: 0 1px 2px #1e293b0a; } nav button { border: 0; border-radius: 8px; padding: .52rem .72rem; color: var(--muted-ink-color, #637083); background: transparent; font: inherit; font-weight: 600; cursor: pointer; } nav button:hover { color: var(--ink-color,#1c2638); background: #eff3f8; } nav button.active { color: #2446b8; background: #e8eeff; }
	@media (max-width: 620px) { header { align-items: start; flex-direction: column; } }
</style>
