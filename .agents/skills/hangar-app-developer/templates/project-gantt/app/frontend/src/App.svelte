<script>
	// @ts-nocheck
	import Icon from '@iconify/svelte'
	import data from '$data'
	import content from '$content'
	import { api, language } from '$hangarkit'
	import { onMount } from 'svelte'

	const DAY_MS = 24 * 60 * 60 * 1000
	const statuses = ['Planned', 'Ready', 'Active', 'Blocked', 'Complete']
	const risks = ['Low', 'Medium', 'High', 'Waiting on QA', 'Waiting on decision', 'External dependency']
	const status_meta = {
		Planned: { icon: 'lucide:calendar-plus', color: '#5b6472' },
		Ready: { icon: 'lucide:circle-dot', color: '#2563eb' },
		Active: { icon: 'lucide:play-circle', color: '#0f766e' },
		Blocked: { icon: 'lucide:octagon-alert', color: '#c2410c' },
		Complete: { icon: 'lucide:check-circle-2', color: '#15803d' }
	}

	let tasks = $state([])
	let milestones = $state([])
	let loading = $state(true)
	let day_width = $state(34)
	let query = $state('')
	let status_filter = $state('All')
	let owner_filter = $state('All')
	let sort_mode = $state('start')
	let selected_id = $state(null)
	let modal_open = $state(false)
	let editing_id = $state(null)
	let form = $state(empty_form())
	let drag = $state(null)
	let preview = $state({})
	let backend_summary = $state(null)
	let today = $state(start_of_day(new Date()))
	let language_id = $state('en')

	language.subscribe((value) => {
		language_id = value.id || 'en'
	})

	function t(key, fallback) {
		const packs = content.localized_copy || {}
		return packs[language_id]?.[key] || packs.en?.[key] || content[key] || fallback
	}

	data.tasks.subscribe((items) => {
		tasks = [...items].sort((a, b) => Number(a.order || 0) - Number(b.order || 0))
		loading = false
	})

	data.milestones.subscribe((items) => {
		milestones = [...items]
	})

	onMount(() => {
		load_summary()
		window.addEventListener('pointermove', handle_pointer_move)
		window.addEventListener('pointerup', handle_pointer_up)
		return () => {
			window.removeEventListener('pointermove', handle_pointer_move)
			window.removeEventListener('pointerup', handle_pointer_up)
		}
	})

	const owners = $derived(['All', ...Array.from(new Set(tasks.map((task) => task.owner).filter(Boolean))).sort()])
	const timeline_start = $derived(get_timeline_start(tasks, milestones))
	const timeline_end = $derived(get_timeline_end(tasks, milestones))
	const timeline_days = $derived(Math.max(14, diff_days(timeline_start, timeline_end) + 1))
	const timeline_width = $derived(timeline_days * day_width)
	const visible_tasks = $derived(filter_and_sort_tasks(tasks))
	const selected_task = $derived(tasks.find((task) => task.id === selected_id) || visible_tasks[0] || null)
	const active_count = $derived(tasks.filter((task) => task.status === 'Active').length)
	const blocked_count = $derived(tasks.filter((task) => task.status === 'Blocked').length)
	const complete_count = $derived(tasks.filter((task) => task.status === 'Complete').length)
	const overdue_count = $derived(tasks.filter((task) => is_overdue(task)).length)

	function empty_form() {
		const start = iso_date(new Date())
		const end = iso_date(add_days(new Date(), 5))
		return {
			title: '',
			description: '',
			owner: '',
			status: 'Planned',
			start_date: start,
			end_date: end,
			dependencies: '',
			jira_key: '',
			risk: 'Medium',
			progress: 0
		}
	}

	function start_of_day(value) {
		const day = new Date(value)
		day.setHours(0, 0, 0, 0)
		return day
	}

	function parse_date(value) {
		if (!value) return start_of_day(new Date())
		const [year, month, day] = String(value).slice(0, 10).split('-').map(Number)
		if (!year || !month || !day) return start_of_day(new Date())
		return new Date(year, month - 1, day)
	}

	function iso_date(value) {
		const day = start_of_day(value)
		const year = day.getFullYear()
		const month = String(day.getMonth() + 1).padStart(2, '0')
		const date = String(day.getDate()).padStart(2, '0')
		return `${year}-${month}-${date}`
	}

	function add_days(value, amount) {
		const day = start_of_day(value)
		day.setDate(day.getDate() + amount)
		return day
	}

	function diff_days(start, end) {
		return Math.round((start_of_day(end) - start_of_day(start)) / DAY_MS)
	}

	function get_timeline_start(items, flags) {
		const dates = [
			...items.flatMap((task) => [task.start_date, task.end_date]).filter(Boolean).map(parse_date),
			...flags.map((flag) => flag.date).filter(Boolean).map(parse_date),
			today
		]
		const min = new Date(Math.min(...dates.map((date) => date.getTime())))
		return add_days(min, -3)
	}

	function get_timeline_end(items, flags) {
		const dates = [
			...items.flatMap((task) => [task.start_date, task.end_date]).filter(Boolean).map(parse_date),
			...flags.map((flag) => flag.date).filter(Boolean).map(parse_date),
			add_days(today, 14)
		]
		const max = new Date(Math.max(...dates.map((date) => date.getTime())))
		return add_days(max, 5)
	}

	function get_task_dates(task) {
		const override = preview[task.id]
		const start = override?.start_date || task.start_date || iso_date(today)
		const end = override?.end_date || task.end_date || start
		return { start_date: start, end_date: end }
	}

	function task_left(task) {
		const { start_date } = get_task_dates(task)
		return diff_days(timeline_start, parse_date(start_date)) * day_width
	}

	function task_width(task) {
		const { start_date, end_date } = get_task_dates(task)
		return Math.max(day_width, (diff_days(parse_date(start_date), parse_date(end_date)) + 1) * day_width)
	}

	function month_label(index) {
		const day = add_days(timeline_start, index)
		if (day.getDate() !== 1 && index !== 0) return ''
		return day.toLocaleDateString(language_id === 'zh' ? 'zh-CN' : 'en-US', { month: 'short', year: 'numeric' })
	}

	function day_label(index) {
		return add_days(timeline_start, index).getDate()
	}

	function is_weekend(index) {
		const day = add_days(timeline_start, index).getDay()
		return day === 0 || day === 6
	}

	function today_left() {
		return diff_days(timeline_start, today) * day_width
	}

	function milestone_left(milestone) {
		return diff_days(timeline_start, parse_date(milestone.date)) * day_width + day_width / 2
	}

	function format_range(task) {
		const { start_date, end_date } = get_task_dates(task)
		return `${format_date(start_date)} - ${format_date(end_date)}`
	}

	function format_date(value) {
		if (!value) return 'No date'
		return parse_date(value).toLocaleDateString(language_id === 'zh' ? 'zh-CN' : 'en-US', { month: 'short', day: 'numeric' })
	}

	function dependency_titles(task) {
		return String(task.dependencies || '')
			.split(',')
			.map((item) => item.trim())
			.filter(Boolean)
			.map((id) => tasks.find((candidate) => candidate.id === id)?.title || id)
	}

	function duration_days(task) {
		const { start_date, end_date } = get_task_dates(task)
		return diff_days(parse_date(start_date), parse_date(end_date)) + 1
	}

	function is_overdue(task) {
		const end = parse_date(task.end_date)
		return end < today && task.status !== 'Complete'
	}

	function filter_and_sort_tasks(items) {
		const needle = query.trim().toLowerCase()
		return items
			.filter((task) => {
				const haystack = [task.title, task.description, task.owner, task.jira_key, task.risk].join(' ').toLowerCase()
				return !needle || haystack.includes(needle)
			})
			.filter((task) => status_filter === 'All' || task.status === status_filter)
			.filter((task) => owner_filter === 'All' || task.owner === owner_filter)
			.sort((a, b) => {
				if (sort_mode === 'owner') return String(a.owner || '').localeCompare(String(b.owner || ''))
				if (sort_mode === 'risk') return risk_weight(b.risk) - risk_weight(a.risk)
				if (sort_mode === 'status') return statuses.indexOf(a.status) - statuses.indexOf(b.status)
				return parse_date(a.start_date) - parse_date(b.start_date)
			})
	}

	function risk_weight(risk) {
		const value = String(risk || '').toLowerCase()
		if (value.includes('high') || value.includes('waiting')) return 3
		if (value.includes('medium')) return 2
		if (value.includes('low')) return 1
		return 0
	}

	function open_new_task() {
		const order = tasks.length ? Math.max(...tasks.map((task) => Number(task.order || 0))) + 1 : 0
		form = { ...empty_form(), order }
		editing_id = null
		modal_open = true
	}

	function open_edit_task(task) {
		form = {
			title: task.title || '',
			description: task.description || '',
			owner: task.owner || '',
			status: task.status || 'Planned',
			start_date: task.start_date || iso_date(today),
			end_date: task.end_date || task.start_date || iso_date(today),
			dependencies: task.dependencies || '',
			jira_key: task.jira_key || '',
			risk: task.risk || 'Medium',
			progress: Number(task.progress || 0),
			order: Number(task.order || 0)
		}
		editing_id = task.id
		selected_id = task.id
		modal_open = true
	}

	function close_modal() {
		modal_open = false
		editing_id = null
		form = empty_form()
	}

	function normalized_form() {
		let start = parse_date(form.start_date)
		let end = parse_date(form.end_date)
		if (end < start) end = start
		return {
			title: form.title.trim(),
			description: form.description.trim(),
			owner: form.owner.trim(),
			status: form.status,
			start_date: iso_date(start),
			end_date: iso_date(end),
			dependencies: form.dependencies.trim(),
			jira_key: form.jira_key.trim(),
			risk: form.risk.trim() || 'Medium',
			progress: Math.max(0, Math.min(100, Number(form.progress || 0))),
			order: Number(form.order || 0)
		}
	}

	async function save_task() {
		const payload = normalized_form()
		if (!payload.title) return
		if (editing_id) {
			await data.tasks.update(editing_id, payload)
			selected_id = editing_id
		} else {
			const created = await data.tasks.create(payload)
			selected_id = created?.id || selected_id
		}
		close_modal()
		load_summary()
	}

	async function delete_task() {
		if (!editing_id) return
		await data.tasks.delete(editing_id)
		selected_id = null
		close_modal()
		load_summary()
	}

	async function update_status(task, status) {
		await data.tasks.update(task.id, { status, progress: status === 'Complete' ? 100 : Number(task.progress || 0) })
		load_summary()
	}

	function begin_timeline_action(event, task, mode) {
		event.preventDefault()
		event.stopPropagation()
		const dates = get_task_dates(task)
		drag = {
			id: task.id,
			mode,
			start_x: event.clientX,
			start_date: dates.start_date,
			end_date: dates.end_date,
			moved: false
		}
		event.currentTarget.setPointerCapture?.(event.pointerId)
	}

	function handle_pointer_move(event) {
		if (!drag) return
		const delta = Math.round((event.clientX - drag.start_x) / day_width)
		if (delta === 0 && !drag.moved) return
		let start = parse_date(drag.start_date)
		let end = parse_date(drag.end_date)
		if (drag.mode === 'move') {
			start = add_days(start, delta)
			end = add_days(end, delta)
		}
		if (drag.mode === 'resize-start') {
			start = add_days(start, delta)
			if (start > end) start = end
		}
		if (drag.mode === 'resize-end') {
			end = add_days(end, delta)
			if (end < start) end = start
		}
		preview = { ...preview, [drag.id]: { start_date: iso_date(start), end_date: iso_date(end) } }
		drag = { ...drag, moved: true }
	}

	async function handle_pointer_up() {
		if (!drag) return
		const current = preview[drag.id]
		const last_drag = drag
		drag = null
		if (current && last_drag.moved) {
			await data.tasks.update(last_drag.id, current)
			load_summary()
		}
		const next_preview = { ...preview }
		delete next_preview[last_drag.id]
		preview = next_preview
	}

	async function load_summary() {
		try {
			backend_summary = await api.get('/summary')
		} catch (error) {
			backend_summary = null
		}
	}

</script>

<div class="page">
	<header class="topbar">
		<div>
			<p class="eyebrow">{t('eyebrow', 'Project timeline')}</p>
			<h1>{t('title', 'Project Gantt')}</h1>
			<p class="subtitle">{t('subtitle', 'Plan work, sequence dependencies, and adjust dates directly on the timeline.')}</p>
		</div>
		<div class="header-actions">
			<button class="ghost" onclick={load_summary}>
				<Icon icon="lucide:refresh-cw" width={16} />
				{t('refresh', 'Refresh')}
			</button>
			<button class="primary" onclick={open_new_task}>
				<Icon icon="lucide:plus" width={17} />
				{t('new_task', 'New task')}
			</button>
		</div>
	</header>

	<section class="metrics">
		<div class="metric">
			<span>{t('tasks', 'Tasks')}</span>
			<strong>{tasks.length}</strong>
		</div>
		<div class="metric active">
			<span>{t('active', 'Active')}</span>
			<strong>{active_count}</strong>
		</div>
		<div class="metric blocked">
			<span>{t('blocked', 'Blocked')}</span>
			<strong>{blocked_count}</strong>
		</div>
		<div class="metric overdue">
			<span>{t('overdue', 'Overdue')}</span>
			<strong>{overdue_count}</strong>
		</div>
		<div class="metric">
			<span>{t('complete', 'Complete')}</span>
			<strong>{complete_count}</strong>
		</div>
		<div class="summary">
			<Icon icon="lucide:activity" width={18} />
			<span>{backend_summary?.message || t('backend_fallback', 'Backend summary will appear after publish.')}</span>
		</div>
	</section>

	<section class="toolbar">
		<label class="search">
			<Icon icon="lucide:search" width={17} />
			<input bind:value={query} placeholder={t('search_placeholder', 'Search task, owner, Jira key, risk...')} />
		</label>
		<select bind:value={status_filter}>
			<option>All</option>
			{#each statuses as status}
				<option>{status}</option>
			{/each}
		</select>
		<select bind:value={owner_filter}>
			{#each owners as owner}
				<option>{owner}</option>
			{/each}
		</select>
		<select bind:value={sort_mode}>
			<option value="start">Sort by start</option>
			<option value="status">Sort by status</option>
			<option value="owner">Sort by owner</option>
			<option value="risk">Sort by risk</option>
		</select>
		<div class="zoom">
			<button aria-label="Zoom out" onclick={() => (day_width = Math.max(22, day_width - 4))}>
				<Icon icon="lucide:minus" width={15} />
			</button>
			<span>{day_width}px/day</span>
			<button aria-label="Zoom in" onclick={() => (day_width = Math.min(56, day_width + 4))}>
				<Icon icon="lucide:plus" width={15} />
			</button>
		</div>
	</section>

	<main class="planner">
		<aside class="task-panel">
			<div class="panel-header">
				<div>
					<p>{t('work_items', 'Work items')}</p>
					<strong>{visible_tasks.length} {t('shown_suffix', 'shown')}</strong>
				</div>
			</div>
			<div class="task-list">
				{#if loading}
					<div class="empty">{t('loading', 'Loading timeline...')}</div>
				{:else if !visible_tasks.length}
					<div class="empty">{t('no_match', 'No tasks match this view.')}</div>
				{:else}
					{#each visible_tasks as task (task.id)}
						<button
							class="task-row"
							class:selected={selected_task?.id === task.id}
							onclick={() => (selected_id = task.id)}
							ondblclick={() => open_edit_task(task)}
						>
							<span class="status-dot" style={`--dot:${status_meta[task.status]?.color || '#64748b'}`}></span>
							<span class="task-main">
								<strong>{task.title}</strong>
								<small>{task.owner || t('unassigned', 'Unassigned')} · {format_range(task)}</small>
							</span>
							<span class="risk" class:hot={risk_weight(task.risk) >= 3}>{task.risk || t('no_risk', 'No risk')}</span>
						</button>
					{/each}
				{/if}
			</div>
		</aside>

		<section class="timeline-shell">
			<div class="timeline-scroll">
				<div class="calendar" style={`width:${timeline_width}px`}>
					<div class="month-row">
						{#each Array(timeline_days) as _, index}
							<div class="month-cell" style={`width:${day_width}px`}>{month_label(index)}</div>
						{/each}
					</div>
					<div class="day-row">
						{#each Array(timeline_days) as _, index}
							<div class:weekend={is_weekend(index)} class="day-cell" style={`width:${day_width}px`}>{day_label(index)}</div>
						{/each}
					</div>
				</div>

				<div class="chart" style={`width:${timeline_width}px`}>
					{#each Array(timeline_days) as _, index}
						<div class:weekend={is_weekend(index)} class="grid-line" style={`left:${index * day_width}px`}></div>
					{/each}
					{#if today_left() >= 0 && today_left() <= timeline_width}
						<div class="today-line" style={`left:${today_left()}px`}>
							<span>{t('today', 'Today')}</span>
						</div>
					{/if}
					{#each milestones as milestone (milestone.id)}
						{#if milestone.date}
							<div class="milestone" style={`left:${milestone_left(milestone)}px`}>
								<Icon icon="lucide:flag" width={14} />
								<span>{milestone.name}</span>
							</div>
						{/if}
					{/each}

					<div class="bars">
						{#each visible_tasks as task (task.id)}
							<div class="bar-row">
								<button
									class="task-bar"
									class:selected={selected_task?.id === task.id}
									class:dragging={drag?.id === task.id}
									style={`left:${task_left(task)}px;width:${task_width(task)}px;--status:${status_meta[task.status]?.color || '#64748b'}`}
									onclick={() => (selected_id = task.id)}
									ondblclick={() => open_edit_task(task)}
									onpointerdown={(event) => begin_timeline_action(event, task, 'move')}
									title="Drag to move dates"
								>
									<span
										class="handle left"
										role="presentation"
										onpointerdown={(event) => begin_timeline_action(event, task, 'resize-start')}
										title="Drag to change start date"
									></span>
									<span class="bar-fill" style={`width:${Math.max(0, Math.min(100, Number(task.progress || 0)))}%`}></span>
									<span class="bar-label">
										<strong>{task.title}</strong>
										<small>{duration_days(task)}d</small>
									</span>
									<span
										class="handle right"
										role="presentation"
										onpointerdown={(event) => begin_timeline_action(event, task, 'resize-end')}
										title="Drag to change end date"
									></span>
								</button>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</section>
	</main>

	<section class="details">
		{#if selected_task}
			<div class="detail-main">
				<div>
					<p class="eyebrow">{t('selected_task', 'Selected task')}</p>
					<h2>{selected_task.title}</h2>
				</div>
				<button class="ghost" onclick={() => open_edit_task(selected_task)}>
					<Icon icon="lucide:pencil" width={15} />
					{t('edit', 'Edit')}
				</button>
			</div>
			<p>{selected_task.description || t('no_description', 'No description yet.')}</p>
			<div class="detail-grid">
				<span><Icon icon="lucide:user" width={15} /> {selected_task.owner || t('unassigned', 'Unassigned')}</span>
				<span><Icon icon={status_meta[selected_task.status]?.icon || 'lucide:circle'} width={15} /> {selected_task.status}</span>
				<span><Icon icon="lucide:calendar-days" width={15} /> {format_range(selected_task)}</span>
				<span><Icon icon="lucide:git-branch" width={15} /> {selected_task.jira_key || t('no_jira', 'No Jira key')}</span>
			</div>
			{#if dependency_titles(selected_task).length}
				<div class="dependencies">
					<strong>{t('dependencies', 'Dependencies')}</strong>
					{#each dependency_titles(selected_task) as dependency}
						<span>{dependency}</span>
					{/each}
				</div>
			{/if}
		{:else}
			<div class="empty detail-empty">{t('select_task', 'Select a task to inspect details.')}</div>
		{/if}
	</section>

	<section class="integrations">
		<article class="integration-card">
			<Icon icon="simple-icons:jira" width={17} />
			{t('jira_context', 'Pull Jira context')}
		</article>
		<article class="integration-card">
			<Icon icon="lucide:video" width={17} />
			{t('project_meetings', 'Project meetings')}
		</article>
		<article class="integration-card">
			<Icon icon="simple-icons:confluence" width={17} />
			{t('project_docs', 'Project docs')}
		</article>
		<article class="integration-card">
			<Icon icon="lucide:table" width={17} />
			{t('export_plan', 'Export plan')}
		</article>
	</section>
</div>

{#if modal_open}
	<div class="modal-backdrop" role="presentation" onclick={close_modal} onkeydown={(event) => event.key === 'Escape' && close_modal()}>
		<div
			class="modal"
			role="dialog"
			tabindex="-1"
			aria-modal="true"
			aria-label={editing_id ? t('edit_task', 'Edit task') : t('create_task', 'Create task')}
			onclick={(event) => event.stopPropagation()}
			onkeydown={(event) => event.key === 'Escape' && close_modal()}
		>
			<header>
				<div>
					<p class="eyebrow">{editing_id ? t('edit_task', 'Edit task') : t('create_task', 'Create task')}</p>
					<h2>{editing_id ? t('update_item', 'Update timeline item') : t('add_item', 'Add a planned item')}</h2>
				</div>
				<button class="icon-btn" aria-label="Close" onclick={close_modal}>
					<Icon icon="lucide:x" width={18} />
				</button>
			</header>

			<label>
				<span>Title</span>
				<input bind:value={form.title} placeholder="Launch readiness review" />
			</label>
			<label>
				<span>Description</span>
				<textarea bind:value={form.description} rows="3" placeholder="Scope, acceptance criteria, notes..."></textarea>
			</label>

			<div class="form-grid">
				<label>
					<span>Owner</span>
					<input bind:value={form.owner} placeholder="Engineering" />
				</label>
				<label>
					<span>Status</span>
					<select bind:value={form.status}>
						{#each statuses as status}
							<option>{status}</option>
						{/each}
					</select>
				</label>
				<label>
					<span>Start</span>
					<input type="date" bind:value={form.start_date} />
				</label>
				<label>
					<span>End</span>
					<input type="date" bind:value={form.end_date} />
				</label>
				<label>
					<span>Jira key</span>
					<input bind:value={form.jira_key} placeholder="PRJ-24" />
				</label>
				<label>
					<span>Risk</span>
					<input bind:value={form.risk} list="risk-options" placeholder="Medium" />
					<datalist id="risk-options">
						{#each risks as risk}
							<option value={risk}></option>
						{/each}
					</datalist>
				</label>
			</div>

			<label>
				<span>Dependencies</span>
				<input bind:value={form.dependencies} placeholder="task-build, task-qa" />
			</label>

			<label>
				<span>Progress {form.progress}%</span>
				<input type="range" min="0" max="100" step="5" bind:value={form.progress} />
			</label>

			<footer>
				{#if editing_id}
					<button class="danger" onclick={delete_task}>
						<Icon icon="lucide:trash-2" width={15} />
						{t('delete', 'Delete')}
					</button>
				{/if}
				<span></span>
				<button class="ghost" onclick={close_modal}>{t('cancel', 'Cancel')}</button>
				<button class="primary" onclick={save_task}>
					<Icon icon="lucide:save" width={15} />
					{t('save_task', 'Save task')}
				</button>
			</footer>
		</div>
	</div>
{/if}

<style>
	:global(body) {
		margin: 0;
		background: #eef3f8;
		color: #162033;
		font-family:
			Inter,
			ui-sans-serif,
			system-ui,
			-apple-system,
			BlinkMacSystemFont,
			"Segoe UI",
			sans-serif;
	}

	button,
	input,
	select,
	textarea {
		font: inherit;
	}

	button {
		cursor: pointer;
	}

	.page {
		min-height: 100vh;
		padding: 28px;
		box-sizing: border-box;
	}

	.topbar,
	.metrics,
	.toolbar,
	.planner,
	.details,
	.integrations {
		max-width: 1500px;
		margin: 0 auto;
	}

	.topbar {
		display: flex;
		justify-content: space-between;
		gap: 24px;
		align-items: flex-start;
		margin-bottom: 18px;
	}

	.eyebrow {
		margin: 0 0 6px;
		color: #64748b;
		font-size: 12px;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0;
	}

	h1,
	h2 {
		margin: 0;
		letter-spacing: 0;
	}

	h1 {
		font-size: clamp(30px, 4vw, 52px);
		line-height: 1;
	}

	h2 {
		font-size: 22px;
	}

	.subtitle {
		margin: 10px 0 0;
		color: #5b6678;
		max-width: 620px;
	}

	.header-actions,
	.toolbar,
	.zoom,
	.integrations,
	.detail-main,
	.detail-grid,
	.dependencies,
	button {
		display: flex;
		align-items: center;
	}

	.header-actions,
	.integrations {
		gap: 10px;
	}

	.primary,
	.ghost,
	.danger,
	.icon-btn,
	.integration-card,
	.zoom button {
		border: 1px solid #cfd8e5;
		border-radius: 7px;
		background: #fff;
		color: #172033;
		min-height: 38px;
		gap: 8px;
		padding: 0 13px;
		font-weight: 750;
	}

	.primary {
		border-color: #111827;
		background: #111827;
		color: #fff;
	}

	.danger {
		border-color: #fecaca;
		color: #b91c1c;
	}

	.icon-btn,
	.zoom button {
		width: 36px;
		justify-content: center;
		padding: 0;
	}

	.metrics {
		display: grid;
		grid-template-columns: repeat(5, minmax(110px, 1fr)) minmax(260px, 2fr);
		gap: 10px;
		margin-bottom: 14px;
	}

	.metric,
	.summary,
	.toolbar,
	.task-panel,
	.timeline-shell,
	.details,
	.integrations {
		background: rgba(255, 255, 255, 0.92);
		border: 1px solid #d6dee8;
		box-shadow: 0 16px 35px rgba(15, 23, 42, 0.08);
	}

	.metric,
	.summary {
		border-radius: 8px;
		padding: 14px;
	}

	.metric span {
		display: block;
		color: #667085;
		font-size: 12px;
		font-weight: 750;
	}

	.metric strong {
		display: block;
		margin-top: 7px;
		font-size: 26px;
	}

	.metric.active strong {
		color: #0f766e;
	}

	.metric.blocked strong,
	.metric.overdue strong {
		color: #c2410c;
	}

	.summary {
		gap: 10px;
		color: #455468;
	}

	.toolbar {
		border-radius: 8px;
		padding: 10px;
		gap: 10px;
		margin-bottom: 14px;
	}

	.search {
		flex: 1;
		min-width: 240px;
		display: flex;
		align-items: center;
		gap: 8px;
		border: 1px solid #cfd8e5;
		border-radius: 7px;
		background: #f8fafc;
		padding: 0 10px;
		height: 38px;
	}

	.search input {
		border: 0;
		background: transparent;
		outline: none;
		width: 100%;
	}

	select,
	input,
	textarea {
		border: 1px solid #cfd8e5;
		border-radius: 7px;
		background: #fff;
		color: #162033;
		min-height: 38px;
		padding: 0 10px;
		box-sizing: border-box;
	}

	textarea {
		padding-top: 9px;
		resize: vertical;
	}

	.zoom {
		margin-left: auto;
		gap: 8px;
		color: #64748b;
		font-size: 12px;
		font-weight: 800;
	}

	.planner {
		display: grid;
		grid-template-columns: 360px minmax(0, 1fr);
		gap: 14px;
		align-items: stretch;
	}

	.task-panel,
	.timeline-shell {
		border-radius: 8px;
		overflow: hidden;
		min-height: 560px;
	}

	.panel-header {
		padding: 16px;
		border-bottom: 1px solid #dbe3ee;
		background: #f8fafc;
	}

	.panel-header p {
		margin: 0;
		color: #64748b;
		font-size: 12px;
		font-weight: 800;
		text-transform: uppercase;
	}

	.panel-header strong {
		display: block;
		margin-top: 4px;
		font-size: 18px;
	}

	.task-list {
		padding: 10px;
		display: grid;
		gap: 8px;
		max-height: 618px;
		overflow: auto;
	}

	.task-row {
		width: 100%;
		text-align: left;
		border: 1px solid #e0e7ef;
		background: #fff;
		border-radius: 8px;
		padding: 11px;
		display: grid;
		grid-template-columns: 10px minmax(0, 1fr) auto;
		gap: 10px;
		align-items: center;
	}

	.task-row:hover,
	.task-row.selected {
		border-color: #111827;
		box-shadow: 0 8px 20px rgba(17, 24, 39, 0.1);
	}

	.status-dot {
		width: 9px;
		height: 9px;
		border-radius: 999px;
		background: var(--dot);
	}

	.task-main {
		min-width: 0;
	}

	.task-main strong,
	.task-main small {
		display: block;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.task-main small {
		margin-top: 3px;
		color: #64748b;
		font-size: 12px;
	}

	.risk {
		border-radius: 999px;
		background: #eef2f7;
		color: #475569;
		padding: 4px 8px;
		font-size: 11px;
		font-weight: 800;
		max-width: 92px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.risk.hot {
		background: #fff1e8;
		color: #c2410c;
	}

	.timeline-scroll {
		overflow: auto;
		height: 100%;
		background: #fff;
	}

	.calendar {
		position: sticky;
		top: 0;
		z-index: 8;
		background: #f8fafc;
		border-bottom: 1px solid #dbe3ee;
	}

	.month-row,
	.day-row {
		display: flex;
	}

	.month-cell,
	.day-cell {
		box-sizing: border-box;
		border-right: 1px solid #e3e9f1;
		min-height: 28px;
		padding: 6px 7px;
		color: #64748b;
		font-size: 11px;
		font-weight: 800;
	}

	.day-cell {
		text-align: center;
		color: #334155;
	}

	.weekend {
		background: #f3f6fa;
	}

	.chart {
		position: relative;
		min-height: 500px;
		padding: 16px 0 20px;
		box-sizing: border-box;
	}

	.grid-line,
	.today-line {
		position: absolute;
		top: 0;
		bottom: 0;
		width: 1px;
		background: #e3e9f1;
		pointer-events: none;
	}

	.today-line {
		background: #dc2626;
		z-index: 3;
	}

	.today-line span {
		position: sticky;
		top: 62px;
		display: inline-block;
		transform: translateX(7px);
		background: #dc2626;
		color: #fff;
		border-radius: 999px;
		padding: 3px 7px;
		font-size: 11px;
		font-weight: 800;
	}

	.milestone {
		position: absolute;
		top: 8px;
		bottom: 0;
		z-index: 4;
		width: 2px;
		background: #7c3aed;
		color: #5b21b6;
		pointer-events: none;
	}

	.milestone :global(svg) {
		position: absolute;
		top: -2px;
		left: -6px;
		background: #fff;
	}

	.milestone span {
		position: absolute;
		top: 18px;
		left: 7px;
		white-space: nowrap;
		background: #f5f3ff;
		border: 1px solid #ddd6fe;
		border-radius: 999px;
		padding: 3px 7px;
		font-size: 11px;
		font-weight: 800;
	}

	.bars {
		position: relative;
		z-index: 5;
		display: grid;
		gap: 8px;
		padding-top: 42px;
	}

	.bar-row {
		position: relative;
		height: 52px;
		border-top: 1px solid #eef2f7;
	}

	.task-bar {
		position: absolute;
		top: 10px;
		height: 34px;
		border: 1px solid color-mix(in srgb, var(--status), white 35%);
		border-radius: 7px;
		background: color-mix(in srgb, var(--status), white 82%);
		color: #102033;
		padding: 0;
		overflow: hidden;
		box-shadow: 0 8px 16px rgba(15, 23, 42, 0.12);
		user-select: none;
		touch-action: none;
	}

	.task-bar:hover,
	.task-bar.selected {
		box-shadow: 0 10px 24px rgba(15, 23, 42, 0.22);
	}

	.task-bar.dragging {
		opacity: 0.88;
	}

	.bar-fill {
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		background: color-mix(in srgb, var(--status), white 55%);
		pointer-events: none;
	}

	.bar-label {
		position: relative;
		z-index: 2;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		width: 100%;
		padding: 0 14px;
		box-sizing: border-box;
		overflow: hidden;
	}

	.bar-label strong {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 13px;
	}

	.bar-label small {
		flex: 0 0 auto;
		color: #475569;
		font-size: 11px;
		font-weight: 800;
	}

	.handle {
		position: absolute;
		top: 0;
		bottom: 0;
		z-index: 3;
		width: 10px;
		background: rgba(15, 23, 42, 0.12);
		cursor: ew-resize;
	}

	.handle.left {
		left: 0;
	}

	.handle.right {
		right: 0;
	}

	.details,
	.integrations {
		border-radius: 8px;
		margin-top: 14px;
		padding: 16px;
	}

	.detail-main {
		justify-content: space-between;
		gap: 12px;
	}

	.details p {
		color: #526071;
		line-height: 1.55;
	}

	.detail-grid {
		flex-wrap: wrap;
		gap: 8px;
	}

	.detail-grid span,
	.dependencies span {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		border: 1px solid #dbe3ee;
		background: #f8fafc;
		border-radius: 999px;
		padding: 6px 10px;
		color: #344054;
		font-size: 12px;
		font-weight: 750;
	}

	.dependencies {
		margin-top: 12px;
		gap: 8px;
		flex-wrap: wrap;
	}

	.dependencies strong {
		font-size: 12px;
		color: #64748b;
		text-transform: uppercase;
	}

	.integrations {
		gap: 10px;
		flex-wrap: wrap;
	}

	.empty {
		border: 1px dashed #cbd5e1;
		border-radius: 8px;
		padding: 18px;
		color: #64748b;
		background: #f8fafc;
		text-align: center;
	}

	.detail-empty {
		width: 100%;
	}

	.modal-backdrop {
		position: fixed;
		inset: 0;
		z-index: 30;
		display: grid;
		place-items: center;
		padding: 22px;
		background: rgba(15, 23, 42, 0.42);
	}

	.modal {
		width: min(760px, 100%);
		max-height: min(840px, 92vh);
		overflow: auto;
		background: #fff;
		border-radius: 10px;
		box-shadow: 0 26px 70px rgba(15, 23, 42, 0.32);
		padding: 22px;
		box-sizing: border-box;
		display: grid;
		gap: 14px;
	}

	.modal header,
	.modal footer {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
		gap: 12px;
		align-items: center;
	}

	.modal footer {
		grid-template-columns: auto minmax(0, 1fr) auto auto;
		border-top: 1px solid #e2e8f0;
		padding-top: 14px;
	}

	label {
		display: grid;
		gap: 6px;
		color: #344054;
		font-size: 13px;
		font-weight: 750;
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 12px;
	}

	input[type='range'] {
		padding: 0;
	}

	@media (max-width: 980px) {
		.page {
			padding: 18px;
		}

		.topbar,
		.toolbar {
			flex-direction: column;
			align-items: stretch;
		}

		.header-actions,
		.zoom {
			margin-left: 0;
		}

		.metrics {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.summary {
			grid-column: 1 / -1;
		}

		.planner {
			grid-template-columns: 1fr;
		}

		.task-panel {
			min-height: 0;
		}

		.task-list {
			max-height: 320px;
		}

		.form-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
