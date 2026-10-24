<script lang="ts">
	let { title = '', children } = $props()
</script>

<svelte:head>
	<title>{title}</title>
</svelte:head>

<main class="app-shell">
	{@render children?.()}
</main>

<style>
	:global(body) {
		margin: 0;
		font-family: var(--font-family, "Avenir Next", ui-sans-serif, system-ui, sans-serif);
		color: var(--body-text-color, #253041);
		background:
			radial-gradient(circle at top left, rgba(181, 93, 53, 0.12), transparent 28%),
			linear-gradient(180deg, #f7f4ed 0%, var(--page-background, #f4f1ea) 100%);
	}

	.app-shell {
		min-height: 100vh;
		padding: var(--page-padding, 2rem);
		box-sizing: border-box;
	}
</style>
