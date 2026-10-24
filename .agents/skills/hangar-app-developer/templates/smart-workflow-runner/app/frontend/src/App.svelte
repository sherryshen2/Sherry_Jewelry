<script lang="ts">
	// @ts-nocheck
	import { onMount } from 'svelte'
	import { nav } from '$hangarkit'
	import AppShell from './components/AppShell.svelte'
	import TasksPage from './pages/TasksPage.svelte'
	import CreateTaskPage from './pages/CreateTaskPage.svelte'
	import TaskDetailPage from './pages/TaskDetailPage.svelte'
	import MetricsPage from './pages/MetricsPage.svelte'
	import ConfigurationPage from './pages/ConfigurationPage.svelte'
	function current_route() { return nav.localPath() || '/' }
	function route_state(value: string) {
		const [, query = ''] = value.split('?')
		const params = new URLSearchParams(query)
		return { view: params.get('view') || '', task_id: params.get('task') || '' }
	}
	let route = $state(current_route())
	function update_route() { route = current_route() }
	onMount(() => { update_route(); window.addEventListener('popstate', update_route); return () => window.removeEventListener('popstate', update_route) })
	let state = $derived(route_state(route))
	let task_id = $derived(state.task_id)
	let page = $derived(state.view === 'metrics' ? 'metrics' : state.view === 'configuration' ? 'configuration' : 'tasks')
</script>
<svelte:head><title>__HANGAR_APP_NAME__</title></svelte:head>
<AppShell current={page}>{#if state.view === 'new'}<CreateTaskPage />{:else if task_id}<TaskDetailPage {task_id} />{:else if state.view === 'metrics'}<MetricsPage />{:else if state.view === 'configuration'}<ConfigurationPage />{:else}<TasksPage />{/if}</AppShell>
