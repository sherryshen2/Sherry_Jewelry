<script lang="ts">
	// @ts-nocheck
	import content from '$content'

	function copy(key: string, fallback = '') {
		const localized = content.localized_copy || {}
		return localized?.en?.[key] || content[key] || fallback
	}
</script>

<main class="page">
	<section class="hero">
		<p class="eyebrow">{copy('eyebrow', 'Simple frontend page')}</p>
		<h1>{copy('app_title', '__HANGAR_APP_NAME__')}</h1>
		<p class="intro">{copy('intro_text', 'A minimal 1-page frontend starter for quick ideas, prototypes, and lightweight internal pages.')}</p>
	</section>

	<section class="panel">
		<h2>{copy('section_title', 'Where to edit')}</h2>
		<p>{copy('section_body', 'Start by editing frontend/src/App.svelte. Add more components only if the page grows beyond one screen.')}</p>
		<div class="path-chip">
			<code>frontend/src/App.svelte</code>
		</div>
	</section>

	<footer class="footer">
		{copy('footer_note', 'This template keeps custom logic in one frontend page and leaves the backend empty by default.')}
	</footer>
</main>

<style>
	:global(body) {
		margin: 0;
		font-family: var(--font-family, "Avenir Next", ui-sans-serif, system-ui, sans-serif);
		color: var(--body-text-color, #27364a);
		background:
			radial-gradient(circle at top left, rgba(217, 111, 50, 0.18), transparent 22%),
			linear-gradient(180deg, #fbf8f1 0%, var(--page-background, #f7f3ea) 100%);
	}

	.page {
		min-height: 100vh;
		padding: clamp(1.25rem, 4vw, 3rem);
		display: grid;
		gap: 1rem;
	}

	.hero,
	.panel,
	.footer {
		width: min(920px, 100%);
		margin: 0 auto;
	}

	.hero {
		padding: clamp(1.5rem, 5vw, 3rem);
		border-radius: var(--panel-radius, 18px);
		background:
			linear-gradient(135deg, color-mix(in srgb, var(--hero-background, #1f3a5f) 92%, white) 0%, var(--hero-background, #1f3a5f) 100%);
		box-shadow: var(--panel-shadow, 0 30px 80px rgba(31, 58, 95, 0.10));
		color: white;
		display: grid;
		gap: 0.8rem;
	}

	.eyebrow,
	h1,
	h2,
	p {
		margin: 0;
	}

	.eyebrow {
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: color-mix(in srgb, white 78%, var(--accent-color, #d96f32));
	}

	h1 {
		font-size: clamp(2.2rem, 8vw, 5rem);
		line-height: 0.95;
		max-width: 10ch;
	}

	.intro {
		max-width: 56ch;
		font-size: 1.05rem;
		line-height: 1.65;
		color: rgba(255, 255, 255, 0.86);
	}

	.panel {
		padding: 1.25rem;
		border: 1px solid var(--border-color, #ded7ca);
		border-radius: var(--panel-radius, 18px);
		background: var(--panel-background, #fffdf8);
		box-shadow: var(--panel-shadow, 0 30px 80px rgba(31, 58, 95, 0.10));
		display: grid;
		gap: 0.85rem;
	}

	h2 {
		color: var(--heading-text-color, #122033);
		font-size: 1.2rem;
	}

	.panel p,
	.footer {
		color: var(--muted-text-color, #6f7b8c);
		line-height: 1.6;
	}

	.path-chip {
		display: flex;
	}

	code {
		padding: 0.45rem 0.7rem;
		border-radius: 999px;
		background: color-mix(in srgb, var(--accent-color, #d96f32) 12%, white);
		color: var(--accent-color, #d96f32);
		font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
		font-size: 0.86rem;
	}

	.footer {
		padding: 0 0.2rem 1rem;
		font-size: 0.95rem;
	}
</style>
