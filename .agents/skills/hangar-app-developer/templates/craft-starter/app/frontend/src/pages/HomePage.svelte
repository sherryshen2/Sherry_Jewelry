<script lang="ts">
	// @ts-nocheck
	import { onMount } from 'svelte'
	import content from '$content'
	import { health_api } from '../lib/api'
	import type { StarterCard, StarterHealth } from '../lib/types'

	let health = $state<StarterHealth | null>(null)
	let health_error = $state('')
	let loading = $state(true)

	const cards = $derived.by<StarterCard[]>(() => [
		{
			title: content.frontend_card_title || 'Frontend pages',
			body: content.frontend_card_body || 'Build screens in pages/, reuse UI in components/, and keep shared helpers in lib/.',
			paths: ['frontend/src/pages/', 'frontend/src/components/', 'frontend/src/lib/']
		},
		{
			title: content.backend_card_title || 'Backend routes',
			body: content.backend_card_body || 'Compose routers in backend/main.py, put endpoints in routers/, and move business logic into services/.',
			paths: ['backend/main.py', 'backend/routers/', 'backend/services/']
		},
		{
			title: content.data_card_title || 'App data',
			body: content.data_card_body || 'Start without seeded tables. Add app-scoped data only when your feature needs it.',
			paths: ['project.data', 'project.storage']
		}
	])

	const health_label = $derived(health?.status || content.health_fallback || 'Backend status is not available yet.')

	async function load_health() {
		loading = true
		health_error = ''
		try {
			health = await health_api.read()
		} catch (error) {
			health = null
			health_error = error instanceof Error ? error.message : String(error)
		} finally {
			loading = false
		}
	}

	onMount(() => {
		void load_health()
	})

	function copy(key: string, fallback = '') {
		const localized = content.localized_copy || {}
		return localized?.en?.[key] || content[key] || fallback
	}
</script>

<section class="hero">
	<p class="eyebrow">{copy('eyebrow', 'Craft starter')}</p>
	<h1>{copy('app_title', '__HANGAR_APP_NAME__')}</h1>
	<p class="lede">{copy('intro_text', 'A clean Hangar starter with separate frontend and backend structure.')}</p>
</section>

<section class="layout-card">
	<div class="section-head">
		<h2>{copy('structure_title', 'Project structure')}</h2>
		<p>Start from the folders below instead of deleting sample business logic.</p>
	</div>

	<div class="card-grid">
		{#each cards as card}
			<article class="structure-card">
				<h3>{card.title}</h3>
				<p>{card.body}</p>
				<ul>
					{#each card.paths as path}
						<li><code>{path}</code></li>
					{/each}
				</ul>
			</article>
		{/each}
	</div>
</section>

<section class="layout-card health-panel">
	<div class="section-head">
		<h2>{copy('health_title', 'Backend health')}</h2>
		<p>The starter includes one backend route so you can confirm the app runtime is wired correctly.</p>
	</div>

	<div class="health-status">
		<span class:ready={Boolean(health)}>{loading ? copy('health_loading', 'Checking backend health...') : health_label}</span>
		<button onclick={() => void load_health()}>Refresh</button>
	</div>

	<div class="health-grid">
		<div>
			<span class="meta-label">{copy('health_route_label', 'Health route')}</span>
			<strong>{copy('health_route_value', '/health')}</strong>
		</div>
		<div>
			<span class="meta-label">Backend file</span>
			<strong>backend/routers/health.py</strong>
		</div>
		<div>
			<span class="meta-label">Next step</span>
			<strong>Add your first route or page</strong>
		</div>
	</div>

	{#if health}
		<pre>{JSON.stringify(health, null, 2)}</pre>
	{:else if health_error}
		<p class="error">{health_error}</p>
	{/if}
</section>

<footer class="footer-note">
	{copy('footer_note', 'Use this starter when you want a clean folder structure without demo business logic.')}
</footer>

<style>
	.hero,
	.layout-card,
	.footer-note {
		width: min(980px, 100%);
		margin: 0 auto;
	}

	.hero {
		padding: clamp(1rem, 3vw, 2.5rem) 0 1.2rem;
		display: grid;
		gap: 0.75rem;
	}

	.eyebrow,
	h1,
	h2,
	h3,
	p,
	.meta-label,
	strong {
		margin: 0;
	}

	.eyebrow {
		color: var(--accent-color, #b55d35);
		font-size: 0.76rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	h1 {
		color: var(--heading-text-color, #1b2230);
		font-size: clamp(2.1rem, 7vw, 4.5rem);
		line-height: 0.95;
		max-width: 11ch;
	}

	.lede,
	.section-head p,
	.structure-card p,
	.footer-note,
	.health-status span,
	.error {
		color: var(--muted-text-color, #6c7483);
		line-height: 1.6;
	}

	.layout-card {
		margin-top: 1rem;
		padding: clamp(1rem, 3vw, 1.5rem);
		border: 1px solid var(--border-color, #ded6ca);
		border-radius: var(--card-radius, 14px);
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(251, 248, 241, 0.98));
		box-shadow: var(--card-shadow, 0 24px 60px rgba(41, 35, 24, 0.08));
		display: grid;
		gap: 1rem;
	}

	.card-grid,
	.health-grid {
		display: grid;
		gap: 0.9rem;
	}

	.card-grid {
		grid-template-columns: repeat(3, minmax(0, 1fr));
	}

	.structure-card,
	.health-grid > div,
	pre {
		padding: 1rem;
		border: 1px solid var(--border-color, #ded6ca);
		border-radius: calc(var(--control-radius, 10px) + 2px);
		background: var(--card-background, #ffffff);
	}

	.structure-card {
		display: grid;
		gap: 0.7rem;
	}

	h2,
	h3 {
		color: var(--heading-text-color, #1b2230);
	}

	ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 0.45rem;
	}

	code,
	pre {
		font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
	}

	code {
		padding: 0.18rem 0.42rem;
		border-radius: 999px;
		color: var(--accent-color, #b55d35);
		background: color-mix(in srgb, var(--accent-color, #b55d35) 10%, #fff);
	}

	.health-panel {
		margin-bottom: 1rem;
	}

	.health-status {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	.health-status span.ready {
		color: var(--status-color, #1f7a5a);
		font-weight: 700;
	}

	button {
		min-height: 40px;
		border: 0;
		border-radius: var(--control-radius, 10px);
		padding: 0 0.95rem;
		color: white;
		background: var(--accent-color, #b55d35);
		font: inherit;
		font-weight: 800;
		cursor: pointer;
	}

	.health-grid {
		grid-template-columns: repeat(3, minmax(0, 1fr));
	}

	.meta-label {
		color: var(--muted-text-color, #6c7483);
		font-size: 0.72rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}

	.health-grid strong {
		margin-top: 0.35rem;
		display: block;
		color: var(--body-text-color, #253041);
	}

	pre {
		margin: 0;
		overflow: auto;
		font-size: 0.8rem;
		line-height: 1.5;
	}

	.footer-note {
		padding-bottom: 2rem;
		font-size: 0.95rem;
	}

	@media (max-width: 780px) {
		.card-grid,
		.health-grid {
			grid-template-columns: 1fr;
		}

		.health-status {
			flex-direction: column;
			align-items: stretch;
		}
	}
</style>
