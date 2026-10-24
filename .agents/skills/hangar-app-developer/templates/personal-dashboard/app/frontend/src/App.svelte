<script lang="ts">
	// @ts-nocheck
	import { onMount } from 'svelte'
	import content from '$content'
	import { api, language, preferences, table } from '$hangarkit'

	type Task = {
		id: string
		title: string
		area?: string
		priority?: string
		done?: boolean
		due?: string
		created?: string
	}

	type Note = {
		id: string
		title: string
		body?: string
		mood?: string
		created?: string
	}

	type Link = {
		id: string
		label: string
		url: string
		category?: string
	}

	type Metric = {
		id: string
		label: string
		value: number
		unit?: string
		trend?: string
	}

	const tasks_table = table('tasks')
	const notes_table = table('notes')
	const links_table = table('links')
	const metrics_table = table('dashboard_metrics')

	let tasks = $state<Task[]>([])
	let notes = $state<Note[]>([])
	let links = $state<Link[]>([])
	let metrics = $state<Metric[]>([])
	let loading = $state(true)
	let locale = $state('en')
	let language_id = $state('en')
	let summary = $state('')
	let new_task = $state('')
	let new_note = $state('')
	let selected_area = $state('All')

	let areas = $derived.by(() => [
		'All',
		...Array.from(new Set(tasks.map((task) => task.area || 'Personal')))
	])
	let visible_tasks = $derived.by(() =>
		tasks.filter(
			(task) =>
				selected_area === 'All' || (task.area || 'Personal') === selected_area
		)
	)
	let open_tasks = $derived.by(() => tasks.filter((task) => !task.done))
	let completed_today = $derived.by(
		() =>
			tasks.filter(
				(task) => task.done && same_day(task.created, new Date().toISOString())
			).length
	)
	let next_task = $derived.by(() => open_tasks[0])
	let headline_metric = $derived.by(() => metrics[0])
	let localized = $derived.by(() => {
		const dictionary = content.localized_copy || {}
		return dictionary[language_id] || dictionary.en || {}
	})

	onMount(() => {
		const stop_preferences = preferences.subscribe((value) => {
			locale = value.locale || 'en'
		})
		const stop_language = language.subscribe((value) => {
			language_id = value.id
		})
		void refresh()
		return () => {
			stop_preferences()
			stop_language()
		}
	})

	function copy(key: string, fallback = '') {
		return localized?.[key] || content[key] || fallback
	}

	async function refresh() {
		loading = true
		try {
			await Promise.all([
				load_tasks(),
				load_notes(),
				load_links(),
				load_metrics(),
				load_summary()
			])
		} finally {
			loading = false
		}
	}

	async function load_tasks() {
		tasks = await tasks_table.list({
			sort: 'done,-priority,due,-created',
			perPage: 80
		})
	}

	async function load_notes() {
		notes = await notes_table.list({ sort: '-created', perPage: 6 })
	}

	async function load_links() {
		links = await links_table.list({ sort: 'category,label', perPage: 24 })
	}

	async function load_metrics() {
		metrics = await metrics_table.list({ sort: 'label', perPage: 12 })
	}

	async function load_summary() {
		try {
			const result = await api.get('/summary')
			summary = result.message
		} catch {
			summary = copy('backend_unavailable')
		}
	}

	async function add_task() {
		const title = new_task.trim()
		if (!title) return
		const created = await tasks_table.create({
			title,
			area: selected_area === 'All' ? 'Personal' : selected_area,
			priority: 'P2',
			done: false,
			_schema: task_schema()
		})
		tasks = [created, ...tasks]
		new_task = ''
		await load_summary()
	}

	async function toggle_task(task: Task) {
		const updated = await tasks_table.update(task.id, { done: !task.done })
		tasks = tasks.map((item) => (item.id === task.id ? updated : item))
		await load_summary()
	}

	async function add_note() {
		const body = new_note.trim()
		if (!body) return
		const created = await notes_table.create({
			title: body.split('\n')[0].slice(0, 60),
			body,
			mood: 'Clear',
			_schema: note_schema()
		})
		notes = [created, ...notes].slice(0, 6)
		new_note = ''
	}

	function task_schema() {
		return [
			{ name: 'title', type: 'text', required: true },
			{ name: 'area', type: 'text' },
			{ name: 'priority', type: 'text' },
			{ name: 'done', type: 'boolean', default: false },
			{ name: 'due', type: 'date' }
		]
	}

	function note_schema() {
		return [
			{ name: 'title', type: 'text', required: true },
			{ name: 'body', type: 'text' },
			{ name: 'mood', type: 'text' }
		]
	}

	function same_day(left?: string, right?: string) {
		if (!left || !right) return false
		return new Date(left).toDateString() === new Date(right).toDateString()
	}

	function format_date(value?: string) {
		if (!value) return copy('no_date_label')
		const parsed = new Date(value)
		if (Number.isNaN(parsed.getTime())) return copy('no_date_label')
		return new Intl.DateTimeFormat(locale, {
			month: 'short',
			day: 'numeric'
		}).format(parsed)
	}

	function initials(value?: string) {
		return String(value || 'PD')
			.trim()
			.slice(0, 2)
			.toUpperCase()
	}
</script>

<main>
	<section class="workspace" aria-label={copy('app_aria', 'Personal dashboard')}>
		<header class="topbar">
			<div>
				<p class="eyebrow">{copy('eyebrow')}</p>
				<h1>{copy('app_title', '__HANGAR_APP_NAME__')}</h1>
			</div>
			<button type="button" onclick={() => void refresh()}
				>{copy('refresh_button')}</button
			>
		</header>

		<section class="hero-strip">
			<div>
				<p class="label">{copy('today_label')}</p>
				<h2>{next_task?.title || copy('clear_day_title')}</h2>
				<p>{summary}</p>
			</div>
			<div class="score">
				<span>{open_tasks.length}</span>
				<small>{copy('open_tasks_label')}</small>
			</div>
		</section>

		<section class="metrics-grid" aria-label={copy('metrics_aria', 'Metrics')}>
			<article>
				<span>{headline_metric?.value ?? completed_today}</span>
				<p>
					{headline_metric
						? headline_metric.label
						: copy('completed_today_label')}
				</p>
				<small>{headline_metric?.trend || copy('metric_hint')}</small>
			</article>
			<article>
				<span>{notes.length}</span>
				<p>{copy('notes_label')}</p>
				<small>{copy('notes_hint')}</small>
			</article>
			<article>
				<span>{links.length}</span>
				<p>{copy('links_label')}</p>
				<small>{copy('links_hint')}</small>
			</article>
		</section>

		<div class="main-grid">
			<section class="panel task-panel" aria-label={copy('focus_tasks_aria', 'Focus tasks')}>
				<div class="panel-title">
					<div>
						<p class="label">{copy('focus_label')}</p>
						<h2>{copy('tasks_title')}</h2>
					</div>
					<select
						bind:value={selected_area}
						aria-label={copy('area_filter_label')}
					>
						{#each areas as area}
							<option value={area}>{area}</option>
						{/each}
					</select>
				</div>

				<form
					class="add-row"
					onsubmit={(event) => {
						event.preventDefault()
						void add_task()
					}}
				>
					<input
						bind:value={new_task}
						placeholder={copy('task_placeholder')}
						aria-label={copy('task_placeholder')}
					/>
					<button type="submit">{copy('add_task_button')}</button>
				</form>

				{#if loading}
					<p class="status">{copy('loading_label')}</p>
				{:else if visible_tasks.length === 0}
					<p class="status">{copy('empty_tasks_label')}</p>
				{:else}
					<ul class="task-list">
						{#each visible_tasks as task (task.id)}
							<li class:done={task.done}>
								<label>
									<input
										type="checkbox"
										checked={task.done}
										onchange={() => void toggle_task(task)}
									/>
									<span>{task.title}</span>
								</label>
								<div>
									<strong>{task.priority || 'P2'}</strong>
									<time>{format_date(task.due || task.created)}</time>
								</div>
							</li>
						{/each}
					</ul>
				{/if}
			</section>

			<aside class="side-stack">
				<section class="panel" aria-label={copy('quick_note_aria', 'Quick note')}>
					<div class="panel-title">
						<div>
							<p class="label">{copy('capture_label')}</p>
							<h2>{copy('notes_title')}</h2>
						</div>
					</div>
					<form
						class="note-form"
						onsubmit={(event) => {
							event.preventDefault()
							void add_note()
						}}
					>
						<textarea
							bind:value={new_note}
							rows="4"
							placeholder={copy('note_placeholder')}
							aria-label={copy('note_placeholder')}
						></textarea>
						<button type="submit">{copy('add_note_button')}</button>
					</form>
					<div class="notes">
						{#each notes as note (note.id)}
							<article>
								<span>{initials(note.mood)}</span>
								<div>
									<strong>{note.title}</strong>
									<p>{note.body || note.title}</p>
								</div>
							</article>
						{/each}
					</div>
				</section>

				<section class="panel" aria-label={copy('quick_links_aria', 'Quick links')}>
					<div class="panel-title">
						<div>
							<p class="label">{copy('launch_label')}</p>
							<h2>{copy('links_title')}</h2>
						</div>
					</div>
					<div class="links">
						{#each links as link (link.id)}
							<a href={link.url} target="_blank" rel="noreferrer">
								<span>{initials(link.label)}</span>
								<div>
									<strong>{link.label}</strong>
									<small
										>{link.category || copy('link_fallback_category')}</small
									>
								</div>
							</a>
						{/each}
					</div>
				</section>
			</aside>
		</div>
	</section>
</main>

<style>
	:global(body) {
		margin: 0;
		font-family: var(
			--font-family,
			Inter,
			ui-sans-serif,
			system-ui,
			sans-serif
		);
		background: var(--page-background, #edf3f7);
		color: var(--ink-color, #18212f);
	}

	main {
		min-height: 100vh;
		padding: var(--page-padding, 1.5rem);
	}

	.workspace {
		width: min(1180px, 100%);
		margin: 0 auto;
		display: grid;
		gap: 1rem;
	}

	.topbar,
	.hero-strip,
	.panel,
	.metrics-grid article {
		border: 1px solid var(--border-color, #d9e2ea);
		border-radius: var(--panel-radius, 8px);
		background: var(--panel-background, #ffffff);
	}

	.topbar {
		min-height: 84px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 1rem 1.25rem;
	}

	.eyebrow,
	.label {
		margin: 0 0 0.35rem;
		color: var(--muted-ink-color, #66788a);
		font-size: 0.76rem;
		font-weight: 800;
		letter-spacing: 0;
		text-transform: uppercase;
	}

	h1,
	h2,
	p {
		margin: 0;
	}

	h1 {
		font-size: clamp(1.7rem, 5vw, 3.25rem);
		line-height: 1;
		letter-spacing: 0;
	}

	h2 {
		font-size: 1.12rem;
		line-height: 1.25;
		letter-spacing: 0;
	}

	button,
	input,
	select,
	textarea {
		font: inherit;
	}

	button {
		border: 0;
		border-radius: var(--control-radius, 6px);
		background: var(--accent-color, #1f7a8c);
		color: var(--button-text-color, #ffffff);
		padding: 0.72rem 0.95rem;
		font-weight: 800;
		cursor: pointer;
	}

	input,
	select,
	textarea {
		min-width: 0;
		border: 1px solid var(--border-color, #d9e2ea);
		border-radius: var(--control-radius, 6px);
		background: #ffffff;
		color: inherit;
		padding: 0.72rem 0.8rem;
	}

	textarea {
		resize: vertical;
	}

	.hero-strip {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 1rem;
		align-items: center;
		padding: 1.25rem;
		background: var(--hero-background, #19323c);
		color: var(--hero-text-color, #f8fbfc);
	}

	.hero-strip p:last-child {
		max-width: 68ch;
		margin-top: 0.45rem;
		color: rgba(248, 251, 252, 0.76);
		line-height: 1.55;
	}

	.score {
		width: 112px;
		height: 112px;
		border-radius: 999px;
		display: grid;
		place-items: center;
		background: var(--highlight-color, #f6bd60);
		color: #19323c;
		text-align: center;
	}

	.score span {
		display: block;
		font-size: 2.4rem;
		font-weight: 900;
		line-height: 1;
	}

	.score small {
		max-width: 72px;
		font-weight: 800;
		line-height: 1.05;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 1rem;
	}

	.metrics-grid article,
	.panel {
		padding: 1rem;
	}

	.metrics-grid span {
		display: block;
		font-size: 2rem;
		font-weight: 900;
		line-height: 1;
	}

	.metrics-grid p {
		margin-top: 0.45rem;
		font-weight: 800;
	}

	.metrics-grid small,
	time,
	.links small,
	.notes p {
		color: var(--muted-ink-color, #66788a);
	}

	.main-grid {
		display: grid;
		grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr);
		gap: 1rem;
	}

	.panel-title {
		display: flex;
		align-items: start;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.add-row {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 0.65rem;
		margin-bottom: 0.8rem;
	}

	.task-list {
		list-style: none;
		display: grid;
		gap: 0.55rem;
		margin: 0;
		padding: 0;
	}

	.task-list li {
		min-height: 58px;
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
		align-items: center;
		gap: 1rem;
		border: 1px solid var(--border-color, #d9e2ea);
		border-radius: var(--control-radius, 6px);
		background: var(--soft-panel, #f7fafb);
		padding: 0.7rem 0.8rem;
	}

	.task-list li.done {
		opacity: 0.58;
	}

	.task-list label {
		min-width: 0;
		display: flex;
		align-items: center;
		gap: 0.7rem;
		font-weight: 800;
	}

	.task-list label span {
		overflow-wrap: anywhere;
	}

	.task-list li > div {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		white-space: nowrap;
	}

	.task-list strong {
		color: var(--accent-color, #1f7a8c);
	}

	.side-stack {
		display: grid;
		gap: 1rem;
		align-content: start;
	}

	.note-form {
		display: grid;
		gap: 0.65rem;
	}

	.notes,
	.links {
		display: grid;
		gap: 0.6rem;
		margin-top: 0.9rem;
	}

	.notes article,
	.links a {
		display: flex;
		gap: 0.72rem;
		align-items: center;
		border: 1px solid var(--border-color, #d9e2ea);
		border-radius: var(--control-radius, 6px);
		padding: 0.72rem;
		background: var(--soft-panel, #f7fafb);
	}

	.links a {
		color: inherit;
		text-decoration: none;
	}

	.notes span,
	.links span {
		width: 38px;
		height: 38px;
		flex: 0 0 auto;
		display: grid;
		place-items: center;
		border-radius: 999px;
		background: var(--highlight-color, #f6bd60);
		color: #19323c;
		font-weight: 900;
		font-size: 0.78rem;
	}

	.notes div,
	.links div {
		min-width: 0;
	}

	.notes strong,
	.links strong {
		display: block;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.notes p {
		display: -webkit-box;
		overflow: hidden;
		line-clamp: 2;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		line-height: 1.35;
	}

	.status {
		color: var(--muted-ink-color, #66788a);
		padding: 1rem 0;
	}

	@media (max-width: 860px) {
		main {
			padding: 0.8rem;
		}

		.topbar,
		.hero-strip,
		.main-grid,
		.metrics-grid {
			grid-template-columns: 1fr;
		}

		.topbar {
			align-items: stretch;
		}

		.score {
			width: 92px;
			height: 92px;
		}
	}

	@media (max-width: 560px) {
		.add-row,
		.task-list li {
			grid-template-columns: 1fr;
		}

		.task-list li > div {
			justify-content: space-between;
		}
	}
</style>
