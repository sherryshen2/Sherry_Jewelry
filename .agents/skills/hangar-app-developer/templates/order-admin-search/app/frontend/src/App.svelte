<script lang="ts">
	// @ts-nocheck
	import content from '$content'
	import AppShell from './components/AppShell.svelte'
	import HomePage from './pages/HomePage.svelte'
</script>

<AppShell title={content.app_title || 'Order Search'}>
	<HomePage />
</AppShell>
