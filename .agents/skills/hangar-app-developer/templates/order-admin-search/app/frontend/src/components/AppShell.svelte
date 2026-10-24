<script lang="ts">
	import type { Snippet } from 'svelte'

	let { title = '', children }: { title: string; children: Snippet } = $props()
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
		font-family: Inter, "Helvetica Neue", Arial, sans-serif;
		color: #1d292e;
		background: #f5f7f7;
	}

	.app-shell {
		min-height: 100vh;
		box-sizing: border-box;
	}
</style>
