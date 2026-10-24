<script lang="ts">
	// @ts-nocheck
	import Icon from '@iconify/svelte'
	import { api, language } from '$hangarkit'
	import content from '$content'
	import data from '$data'

	type Ticket = Record<string, any>
	type JiraIssue = Record<string, any>

	let tickets = $state<Ticket[]>([])
	let messages = $state<any[]>([])
	let team = $state<any[]>([])
	let import_runs = $state<any[]>([])
	let loading = $state(true)
	let active_ticket_id = $state('')
	let search = $state('')
	let status_filter = $state('active')
	let priority_filter = $state('all')
	let assignee_filter = $state('all')
	let source_filter = $state('all')
	let sort_by = $state('updated_desc')
	let composer_open = $state(false)
	let import_open = $state(false)
	let importing = $state(false)
	let import_error = $state('')
	let import_message = $state('')
	let jira_jql = $state('')
	let jira_results = $state<JiraIssue[]>([])
	let selected_jira_keys = $state<string[]>([])
	let reply_text = $state('')
	let internal_note = $state(true)
	let requester_context = $state<any>(null)
	let context_loading = $state(false)
	let language_id = $state('en')
	let new_ticket = $state({
		subject: '',
		description: '',
		priority: 'medium',
		status: 'open',
		requester_name: '',
		requester_email: '',
		assignee_id: ''
	})

	language.subscribe((value) => {
		language_id = value.id || 'en'
	})

	function t(key: string, fallback: string) {
		const packs = content.localized_copy || {}
		return packs[language_id]?.[key] || packs.en?.[key] || content[key] || fallback
	}

	const statuses = [
		{ id: 'open', label: 'Open', color: '#2563eb', icon: 'lucide:circle-dot' },
		{ id: 'triage', label: 'Triage', color: '#7c3aed', icon: 'lucide:list-filter' },
		{ id: 'in_progress', label: 'In progress', color: '#0891b2', icon: 'lucide:loader' },
		{ id: 'waiting', label: 'Waiting', color: '#d97706', icon: 'lucide:pause-circle' },
		{ id: 'resolved', label: 'Resolved', color: '#16a34a', icon: 'lucide:check-circle' },
		{ id: 'closed', label: 'Closed', color: '#64748b', icon: 'lucide:circle-x' }
	]

	const priorities = [
		{ id: 'urgent', label: 'Urgent', color: '#dc2626', rank: 4 },
		{ id: 'high', label: 'High', color: '#ea580c', rank: 3 },
		{ id: 'medium', label: 'Medium', color: '#ca8a04', rank: 2 },
		{ id: 'low', label: 'Low', color: '#64748b', rank: 1 }
	]

	data.tickets.subscribe((items) => {
		tickets = [...items]
		loading = false
		if (!active_ticket_id && items[0]) active_ticket_id = items[0].id
	})

	data.messages.subscribe((items) => {
		messages = [...items]
	})

	data.team.subscribe((items) => {
		team = [...items]
	})

	data.import_runs.subscribe((items) => {
		import_runs = [...items].sort((a, b) => to_time(b.created_at) - to_time(a.created_at))
	})

	let open_count = $derived.by(() => tickets.filter((ticket) => !is_done(ticket)).length)
	let waiting_count = $derived.by(() => tickets.filter((ticket) => ticket.status === 'waiting').length)
	let urgent_count = $derived.by(() => tickets.filter((ticket) => ticket.priority === 'urgent').length)
	let jira_count = $derived.by(() => tickets.filter((ticket) => ticket.source === 'jira' || ticket.jira_key).length)

	let filtered_tickets = $derived.by(() => {
		let output = [...tickets]
		if (status_filter === 'active') output = output.filter((ticket) => !is_done(ticket))
		else if (status_filter !== 'all') output = output.filter((ticket) => ticket.status === status_filter)
		if (priority_filter !== 'all') output = output.filter((ticket) => ticket.priority === priority_filter)
		if (assignee_filter !== 'all') output = output.filter((ticket) => (ticket.assignee_id || ticket.assignee_name || 'unassigned') === assignee_filter)
		if (source_filter !== 'all') output = output.filter((ticket) => source_for(ticket) === source_filter)
		if (search.trim()) {
			const q = search.trim().toLowerCase()
			output = output.filter((ticket) =>
				[
					ticket.subject,
					ticket.description,
					ticket.requester_name,
					ticket.requester_email,
					ticket.assignee_name,
					ticket.jira_key,
					ticket.status,
					ticket.priority
				]
					.filter(Boolean)
					.some((value) => String(value).toLowerCase().includes(q))
			)
		}
		return output.sort(compare_tickets)
	})

	let active_ticket = $derived.by(() => tickets.find((ticket) => ticket.id === active_ticket_id) || filtered_tickets[0] || null)

	let ticket_messages = $derived.by(() =>
		active_ticket
			? messages
					.filter((message) => message.ticket_id === active_ticket.id)
					.sort((a, b) => to_time(a.created_at) - to_time(b.created_at))
			: []
	)

	let assignee_options = $derived.by(() => {
		const imported = tickets
			.map((ticket) => ticket.assignee_name || ticket.assignee_email)
			.filter(Boolean)
			.map((name) => ({ id: name, name }))
		const local = team.map((member) => ({ id: member.id, name: member.name }))
		return unique_by([...local, ...imported], 'id')
	})

	function unique_by(items: any[], field: string) {
		const seen = new Set()
		return items.filter((item) => {
			const key = item[field]
			if (!key || seen.has(key)) return false
			seen.add(key)
			return true
		})
	}

	function compare_tickets(a: Ticket, b: Ticket) {
		if (sort_by === 'priority_desc') return priority_rank(b.priority) - priority_rank(a.priority) || to_time(b.updated_at || b.created_at) - to_time(a.updated_at || a.created_at)
		if (sort_by === 'status_asc') return status_label(a.status).localeCompare(status_label(b.status)) || to_time(b.updated_at || b.created_at) - to_time(a.updated_at || a.created_at)
		if (sort_by === 'assignee_asc') return assignee_label(a).localeCompare(assignee_label(b)) || to_time(b.updated_at || b.created_at) - to_time(a.updated_at || a.created_at)
		if (sort_by === 'created_desc') return to_time(b.created_at) - to_time(a.created_at)
		return to_time(b.updated_at || b.created_at) - to_time(a.updated_at || a.created_at)
	}

	function to_time(value: any) {
		const time = new Date(value || 0).getTime()
		return Number.isFinite(time) ? time : 0
	}

	function is_done(ticket: Ticket) {
		return ['resolved', 'closed', 'done'].includes(String(ticket.status || '').toLowerCase())
	}

	function status_meta(id: string) {
		return statuses.find((item) => item.id === id) || statuses[0]
	}

	function priority_meta(id: string) {
		return priorities.find((item) => item.id === id) || priorities[2]
	}

	function priority_rank(id: string) {
		return priority_meta(id).rank
	}

	function status_label(id: string) {
		return status_meta(id).label
	}

	function assignee_label(ticket: Ticket) {
		const local = team.find((member) => member.id === ticket.assignee_id)
		return ticket.assignee_name || local?.name || ticket.assignee_email || t('unassigned', 'Unassigned')
	}

	function source_for(ticket: Ticket) {
		if (ticket.jira_key || ticket.source === 'jira') return 'jira'
		if (ticket.source === 'email') return 'email'
		return 'manual'
	}

	function format_date(value: any) {
		if (!value) return 'Not set'
		return new Date(value).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
	}

	function time_ago(value: any) {
		if (!value) return 'No activity'
		const seconds = Math.floor((Date.now() - to_time(value)) / 1000)
		if (seconds < 60) return 'just now'
		if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
		if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
		return `${Math.floor(seconds / 86400)}d ago`
	}

	function toggle_key(key: string) {
		selected_jira_keys = selected_jira_keys.includes(key)
			? selected_jira_keys.filter((item) => item !== key)
			: [...selected_jira_keys, key]
	}

	async function find_my_jira_tickets() {
		importing = true
		import_error = ''
		import_message = ''
		try {
			const result = await api.get('/jira/my-issues?max_results=30')
			jira_results = result.issues || []
			selected_jira_keys = jira_results.map((issue) => issue.key).filter(Boolean)
			import_message = `${jira_results.length} Jira issues found for you.`
			import_open = true
		} catch (err) {
			import_error = err instanceof Error ? err.message : 'Failed to load Jira issues'
		} finally {
			importing = false
		}
	}

	async function search_jira() {
		if (!jira_jql.trim()) return
		importing = true
		import_error = ''
		import_message = ''
		try {
			const result = await api.post('/jira/search', { jql: jira_jql, limit: 50 })
			jira_results = result.issues || []
			selected_jira_keys = jira_results.map((issue) => issue.key).filter(Boolean)
			import_message = `${jira_results.length} Jira issues matched.`
		} catch (err) {
			import_error = err instanceof Error ? err.message : 'Jira search failed'
		} finally {
			importing = false
		}
	}

	async function import_selected() {
		if (selected_jira_keys.length === 0) return
		importing = true
		import_error = ''
		try {
			const result = await api.post('/jira/import', {
				keys: selected_jira_keys,
				issues: jira_results.filter((issue) => selected_jira_keys.includes(issue.key))
			})
			import_message = `Imported ${result.imported || 0} tickets and refreshed ${result.updated || 0}.`
			if (result.tickets?.[0]?.id) active_ticket_id = result.tickets[0].id
		} catch (err) {
			import_error = err instanceof Error ? err.message : 'Import failed'
		} finally {
			importing = false
		}
	}

	async function create_ticket() {
		if (!new_ticket.subject.trim()) return
		const created = await data.tickets.create({
			...new_ticket,
			subject: new_ticket.subject.trim(),
			description: new_ticket.description.trim(),
			source: 'manual',
			created_at: new Date().toISOString(),
			updated_at: new Date().toISOString()
		})
		active_ticket_id = created.id
		composer_open = false
		new_ticket = {
			subject: '',
			description: '',
			priority: 'medium',
			status: 'open',
			requester_name: '',
			requester_email: '',
			assignee_id: ''
		}
	}

	async function patch_ticket(id: string, patch: Record<string, any>) {
		await data.tickets.update(id, { ...patch, updated_at: new Date().toISOString() })
	}

	async function send_message() {
		if (!active_ticket || !reply_text.trim()) return
		await data.messages.create({
			ticket_id: active_ticket.id,
			content: reply_text.trim(),
			author_name: internal_note ? 'Internal note' : 'Support reply',
			is_internal: internal_note,
			created_at: new Date().toISOString()
		})
		await patch_ticket(active_ticket.id, {})
		reply_text = ''
	}

	async function load_requester_context() {
		if (!active_ticket?.requester_email) return
		context_loading = true
		requester_context = null
		try {
			requester_context = await api.get(`/mail/requester-context?email=${encodeURIComponent(active_ticket.requester_email)}`)
		} catch (err) {
			requester_context = { ok: false, message: err instanceof Error ? err.message : 'Requester mail lookup failed' }
		} finally {
			context_loading = false
		}
	}
</script>

<svelte:head>
	<title>{t('title', 'Ticket Tracker')}</title>
</svelte:head>

<main class="page">
	<header class="topbar">
		<div>
			<p class="eyebrow">{t('eyebrow', 'Support queue')}</p>
			<h1>{t('title', 'Ticket Tracker')}</h1>
		</div>
		<div class="top-actions">
			<button class="ghost" onclick={() => (composer_open = !composer_open)}>
				<Icon icon="lucide:plus" width={16} />
				{t('new_ticket', 'New ticket')}
			</button>
			<button onclick={find_my_jira_tickets} disabled={importing}>
				<Icon icon="logos:jira" width={16} />
				{importing ? t('checking_jira', 'Checking Jira...') : t('find_jira', 'Find my Jira tickets')}
			</button>
		</div>
	</header>

	<section class="metrics" aria-label="Ticket metrics">
		<article>
			<span>{t('open', 'Open')}</span>
			<strong>{open_count}</strong>
		</article>
		<article>
			<span>{t('waiting', 'Waiting')}</span>
			<strong>{waiting_count}</strong>
		</article>
		<article>
			<span>{t('urgent', 'Urgent')}</span>
			<strong>{urgent_count}</strong>
		</article>
		<article>
			<span>{t('jira_cached', 'Jira cached')}</span>
			<strong>{jira_count}</strong>
		</article>
	</section>

	{#if import_error}
		<div class="notice error">
			<Icon icon="lucide:triangle-alert" width={18} />
			{import_error}
		</div>
	{/if}

	{#if import_message}
		<div class="notice">
			<Icon icon="lucide:info" width={18} />
			{import_message}
		</div>
	{/if}

	{#if composer_open}
		<form class="create-panel" onsubmit={(event) => { event.preventDefault(); create_ticket(); }}>
			<label>
				<span>{t('subject', 'Subject')}</span>
				<input bind:value={new_ticket.subject} placeholder="Customer cannot complete checkout" required />
			</label>
			<label>
				<span>{t('description', 'Description')}</span>
				<textarea bind:value={new_ticket.description} placeholder="What happened, who is impacted, and what has already been tried?"></textarea>
			</label>
			<label>
				<span>{t('priority', 'Priority')}</span>
				<select bind:value={new_ticket.priority}>
					{#each priorities as priority}
						<option value={priority.id}>{priority.label}</option>
					{/each}
				</select>
			</label>
			<label>
				<span>{t('requester', 'Requester')}</span>
				<input bind:value={new_ticket.requester_name} placeholder="Requester name" />
			</label>
			<label>
				<span>{t('email', 'Email')}</span>
				<input type="email" bind:value={new_ticket.requester_email} placeholder="requester@example.com" />
			</label>
			<div class="form-actions">
				<button type="button" class="ghost" onclick={() => (composer_open = false)}>{t('cancel', 'Cancel')}</button>
				<button>{t('create_ticket', 'Create ticket')}</button>
			</div>
		</form>
	{/if}

	{#if import_open}
		<section class="import-panel">
			<div class="panel-head">
				<div>
					<p class="eyebrow">{t('jira_import', 'Jira import')}</p>
					<h2>{t('import_title', 'Cache assigned issues into this queue')}</h2>
				</div>
				<button class="ghost icon-only" aria-label="Close Jira import" onclick={() => (import_open = false)}>
					<Icon icon="lucide:x" width={18} />
				</button>
			</div>
			<form class="jql-row" onsubmit={(event) => { event.preventDefault(); search_jira(); }}>
				<input bind:value={jira_jql} placeholder='Optional JQL, e.g. assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC' />
				<button disabled={importing || !jira_jql.trim()}>
					<Icon icon="lucide:search" width={16} />
					{t('search', 'Search')}
				</button>
			</form>
			<div class="import-list">
				{#each jira_results as issue}
					<label class="import-card">
						<input type="checkbox" checked={selected_jira_keys.includes(issue.key)} onchange={() => toggle_key(issue.key)} />
						<div>
							<strong>{issue.key}</strong>
							<span>{issue.summary}</span>
							<small>{issue.status || 'No status'} · {issue.assignee || t('unassigned', 'Unassigned')} · {format_date(issue.updated)}</small>
						</div>
						<span class="priority-chip" style={`--chip:${priority_meta(String(issue.priority || '').toLowerCase()).color}`}>
							{issue.priority || 'Priority'}
						</span>
					</label>
				{/each}
				{#if jira_results.length === 0}
					<p class="empty-inline">Use "Find my Jira tickets" or run a JQL search to preview importable issues.</p>
				{/if}
			</div>
			<div class="form-actions">
				<span>{selected_jira_keys.length} {t('selected', 'selected')}</span>
				<button onclick={import_selected} disabled={importing || selected_jira_keys.length === 0}>
					<Icon icon="lucide:download" width={16} />
					{t('import_selected', 'Import selected')}
				</button>
			</div>
		</section>
	{/if}

	<section class="workspace">
		<aside class="queue">
			<div class="filters">
				<div class="search">
					<Icon icon="lucide:search" width={16} />
						<input bind:value={search} placeholder={t('search_placeholder', 'Search tickets...')} />
				</div>
				<div class="filter-grid">
					<select bind:value={status_filter} aria-label="Status filter">
							<option value="active">{t('active', 'Active')}</option>
							<option value="all">{t('all_statuses', 'All statuses')}</option>
						{#each statuses as status}
							<option value={status.id}>{status.label}</option>
						{/each}
					</select>
					<select bind:value={priority_filter} aria-label="Priority filter">
							<option value="all">{t('all_priorities', 'All priorities')}</option>
						{#each priorities as priority}
							<option value={priority.id}>{priority.label}</option>
						{/each}
					</select>
					<select bind:value={assignee_filter} aria-label="Assignee filter">
							<option value="all">{t('all_assignees', 'All assignees')}</option>
						{#each assignee_options as assignee}
							<option value={assignee.id}>{assignee.name}</option>
						{/each}
							<option value="unassigned">{t('unassigned', 'Unassigned')}</option>
					</select>
					<select bind:value={source_filter} aria-label="Source filter">
							<option value="all">{t('all_sources', 'All sources')}</option>
						<option value="jira">Jira</option>
						<option value="manual">Manual</option>
						<option value="email">Email</option>
					</select>
					<select bind:value={sort_by} aria-label="Sort tickets">
							<option value="updated_desc">{t('sort_updated', 'Updated newest')}</option>
							<option value="priority_desc">{t('sort_priority', 'Priority high to low')}</option>
							<option value="status_asc">{t('sort_status', 'Status')}</option>
							<option value="assignee_asc">{t('sort_assignee', 'Assignee')}</option>
							<option value="created_desc">{t('sort_created', 'Created newest')}</option>
					</select>
				</div>
			</div>

			{#if loading}
					<div class="empty-state">{t('loading_queue', 'Loading queue...')}</div>
			{:else if filtered_tickets.length === 0}
				<div class="empty-state">
					<Icon icon="lucide:inbox" width={34} />
						{t('no_tickets', 'No tickets match this view.')}
				</div>
			{:else}
				<div class="ticket-list">
					{#each filtered_tickets as ticket}
						{@const status = status_meta(ticket.status)}
						{@const priority = priority_meta(ticket.priority)}
						<button class:active={active_ticket?.id === ticket.id} class="ticket-row" onclick={() => (active_ticket_id = ticket.id)}>
							<span class="status-dot" style={`--dot:${status.color}`}></span>
							<div>
								<span class="ticket-title">
									{#if ticket.jira_key}<b>{ticket.jira_key}</b>{/if}
									{ticket.subject}
								</span>
								<small>{assignee_label(ticket)} · {time_ago(ticket.updated_at || ticket.created_at)}</small>
							</div>
							<span class="priority" style={`--priority:${priority.color}`}>{priority.label}</span>
						</button>
					{/each}
				</div>
			{/if}
		</aside>

		<section class="detail">
			{#if active_ticket}
				<div class="detail-head">
					<div>
						<p class="eyebrow">{source_for(active_ticket)} ticket</p>
						<h2>{active_ticket.subject}</h2>
						<div class="meta-line">
							{#if active_ticket.jira_key}
								<a href={active_ticket.jira_url || `https://jira.shopee.io/browse/${active_ticket.jira_key}`} target="_blank" rel="noreferrer">
									<Icon icon="logos:jira" width={14} />
									{active_ticket.jira_key}
								</a>
							{/if}
							<span>{t('sort_updated', 'Updated')} {format_date(active_ticket.updated_at || active_ticket.created_at)}</span>
						</div>
					</div>
					<span class="status-pill" style={`--pill:${status_meta(active_ticket.status).color}`}>{status_label(active_ticket.status)}</span>
				</div>

				<div class="detail-grid">
					<label>
						<span>{t('sort_status', 'Status')}</span>
						<select value={active_ticket.status} onchange={(event) => patch_ticket(active_ticket.id, { status: event.currentTarget.value })}>
							{#each statuses as status}
								<option value={status.id}>{status.label}</option>
							{/each}
						</select>
					</label>
					<label>
						<span>{t('priority', 'Priority')}</span>
						<select value={active_ticket.priority} onchange={(event) => patch_ticket(active_ticket.id, { priority: event.currentTarget.value })}>
							{#each priorities as priority}
								<option value={priority.id}>{priority.label}</option>
							{/each}
						</select>
					</label>
					<label>
						<span>{t('sort_assignee', 'Assignee')}</span>
						<select value={active_ticket.assignee_id || ''} onchange={(event) => patch_ticket(active_ticket.id, { assignee_id: event.currentTarget.value })}>
							<option value="">{t('unassigned', 'Unassigned')}</option>
							{#each team as member}
								<option value={member.id}>{member.name}</option>
							{/each}
						</select>
					</label>
				</div>

				<article class="description">
					<h3>{t('description', 'Description')}</h3>
					<p>{active_ticket.description || 'No description captured yet.'}</p>
				</article>

				<section class="requester">
					<div>
						<h3>{t('requester_context', 'Requester context')}</h3>
						<p>{active_ticket.requester_name || active_ticket.reporter || 'Unknown requester'}</p>
						{#if active_ticket.requester_email}
							<a href={`mailto:${active_ticket.requester_email}`}>{active_ticket.requester_email}</a>
						{/if}
					</div>
					<button class="ghost" onclick={load_requester_context} disabled={!active_ticket.requester_email || context_loading}>
						<Icon icon="lucide:mail-search" width={16} />
						{context_loading ? t('searching', 'Searching...') : t('find_recent_mail', 'Find recent mail')}
					</button>
				</section>

				{#if requester_context}
					<div class="context-box">
						<strong>{requester_context.ok === false ? 'Mail unavailable' : 'Recent mail'}</strong>
						<p>{requester_context.message || `${requester_context.messages?.length || 0} related messages found.`}</p>
					</div>
				{/if}

				<section class="thread">
					<div class="section-head">
						<h3>{t('conversation', 'Conversation')}</h3>
						<span>{ticket_messages.length} {t('notes', 'notes')}</span>
					</div>
					<div class="messages">
						{#each ticket_messages as message}
							<article class:internal={message.is_internal}>
								<div>
									<strong>{message.author_name}</strong>
									<span>{time_ago(message.created_at)}</span>
								</div>
								<p>{message.content}</p>
							</article>
						{/each}
						{#if ticket_messages.length === 0}
							<p class="empty-inline">No conversation yet.</p>
						{/if}
					</div>
					<div class="reply">
						<textarea bind:value={reply_text} placeholder="Add an internal note or customer reply..."></textarea>
						<div class="form-actions">
							<label class="checkbox">
								<input type="checkbox" bind:checked={internal_note} />
								{t('internal_note', 'Internal note')}
							</label>
							<button onclick={send_message} disabled={!reply_text.trim()}>
								<Icon icon="lucide:send" width={16} />
								{t('add_note', 'Add note')}
							</button>
						</div>
					</div>
				</section>
			{:else}
				<div class="empty-state large">
					<Icon icon="lucide:ticket" width={42} />
					{t('empty_detail', 'Select a ticket or import your Jira assignments.')}
				</div>
			{/if}
		</section>

		<aside class="activity">
			<h2>{t('import_history', 'Import history')}</h2>
			{#each import_runs.slice(0, 8) as run}
				<article>
					<strong>{run.source || 'jira'}</strong>
					<span>{run.imported_count || 0} imported · {run.updated_count || 0} refreshed</span>
					<small>{format_date(run.created_at)}</small>
				</article>
			{/each}
			{#if import_runs.length === 0}
				<p class="empty-inline">{t('empty_import', 'Jira import runs will appear here.')}</p>
			{/if}
		</aside>
	</section>
</main>

<style>
	:global(body) {
		margin: 0;
		background: var(--bg-color, #eef3f8);
		color: var(--heading-color, #142033);
		font-family: var(--font, Inter), ui-sans-serif, system-ui, sans-serif;
	}

	button,
	input,
	select,
	textarea {
		font: inherit;
	}

	button {
		border: 0;
		cursor: pointer;
	}

	button:disabled {
		cursor: wait;
		opacity: 0.6;
	}

	.page {
		min-height: 100vh;
		padding: 22px;
	}

	.topbar,
	.metrics,
	.workspace,
	.create-panel,
	.import-panel,
	.notice {
		width: min(1440px, 100%);
		margin-inline: auto;
	}

	.topbar,
	.panel-head,
	.detail-head,
	.section-head,
	.requester,
	.form-actions,
	.top-actions {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
	}

	.eyebrow {
		margin: 0 0 4px;
		color: var(--text-color, #60708a);
		font-size: 12px;
		font-weight: 800;
		letter-spacing: 0;
		text-transform: uppercase;
	}

	h1,
	h2,
	h3,
	p {
		margin: 0;
	}

	h1 {
		font-size: 26px;
	}

	h2 {
		font-size: 20px;
	}

	h3 {
		font-size: 15px;
	}

	.topbar button,
	.form-actions button,
	.jql-row button,
	.requester button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		min-height: 38px;
		border-radius: var(--radius, 8px);
		background: var(--accent-color, #2563eb);
		color: white;
		font-weight: 800;
		padding: 0 14px;
	}

	button.ghost,
	.ghost {
		background: var(--card-bg, #fff);
		color: var(--heading-color, #142033);
		border: 1px solid var(--border-color, #d8e1ec);
	}

	.icon-only {
		width: 38px;
		padding: 0;
	}

	.metrics {
		display: grid;
		grid-template-columns: repeat(4, minmax(140px, 1fr));
		gap: 12px;
		margin-block: 18px;
	}

	.metrics article,
	.queue,
	.detail,
	.activity,
	.create-panel,
	.import-panel,
	.notice {
		background: var(--card-bg, #fff);
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: var(--radius, 8px);
	}

	.metrics article {
		padding: 16px;
		display: grid;
		gap: 6px;
	}

	.metrics span,
	small,
	.meta-line,
	.empty-inline,
	.context-box p {
		color: var(--text-color, #60708a);
	}

	.metrics strong {
		font-size: 28px;
	}

	.notice {
		margin-bottom: 12px;
		padding: 12px 14px;
		display: flex;
		align-items: center;
		gap: 10px;
		background: #ecfdf5;
		border-color: #bbf7d0;
		color: #166534;
	}

	.notice.error {
		background: #fef2f2;
		border-color: #fecaca;
		color: #991b1b;
	}

	.create-panel,
	.import-panel {
		margin-bottom: 14px;
		padding: 16px;
	}

	.create-panel {
		display: grid;
		grid-template-columns: 1.2fr 1.6fr 160px 180px 220px;
		gap: 12px;
		align-items: end;
	}

	label {
		display: grid;
		gap: 6px;
		font-size: 13px;
		font-weight: 800;
	}

	input,
	select,
	textarea {
		width: 100%;
		box-sizing: border-box;
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: 7px;
		background: #fbfdff;
		color: inherit;
		padding: 10px 11px;
	}

	textarea {
		min-height: 78px;
		resize: vertical;
	}

	.jql-row {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 10px;
		margin-top: 12px;
	}

	.import-list {
		display: grid;
		gap: 8px;
		margin: 14px 0;
		max-height: 300px;
		overflow: auto;
	}

	.import-card {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) auto;
		align-items: center;
		gap: 12px;
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: 8px;
		padding: 12px;
		background: #fbfdff;
	}

	.import-card div {
		display: grid;
		gap: 3px;
		min-width: 0;
	}

	.import-card span {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.priority-chip,
	.priority {
		color: var(--chip, var(--priority));
		background: color-mix(in srgb, var(--chip, var(--priority)) 12%, transparent);
		border-radius: 999px;
		padding: 4px 8px;
		font-size: 12px;
		font-weight: 800;
	}

	.workspace {
		display: grid;
		grid-template-columns: 380px minmax(0, 1fr) 260px;
		gap: 14px;
		align-items: start;
	}

	.queue,
	.detail,
	.activity {
		min-height: 620px;
	}

	.queue {
		padding: 14px;
	}

	.filters {
		display: grid;
		gap: 10px;
		margin-bottom: 12px;
	}

	.search {
		position: relative;
	}

	.search :global(svg) {
		position: absolute;
		left: 10px;
		top: 50%;
		transform: translateY(-50%);
		color: var(--text-color, #60708a);
	}

	.search input {
		padding-left: 34px;
	}

	.filter-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
	}

	.filter-grid select:last-child {
		grid-column: span 2;
	}

	.ticket-list {
		display: grid;
		gap: 8px;
		max-height: 540px;
		overflow: auto;
		padding-right: 4px;
	}

	.ticket-row {
		width: 100%;
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) auto;
		gap: 10px;
		align-items: center;
		text-align: left;
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: 8px;
		background: #fff;
		padding: 12px;
	}

	.ticket-row.active {
		border-color: var(--accent-color, #2563eb);
		box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent-color, #2563eb) 12%, transparent);
	}

	.status-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--dot);
	}

	.ticket-title {
		display: block;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-weight: 800;
	}

	.ticket-title b {
		margin-right: 6px;
		color: var(--accent-color, #2563eb);
	}

	.detail {
		padding: 18px;
		display: grid;
		gap: 16px;
	}

	.meta-line {
		display: flex;
		flex-wrap: wrap;
		gap: 10px;
		margin-top: 8px;
		font-size: 13px;
	}

	a {
		color: var(--accent-color, #2563eb);
		text-decoration: none;
		font-weight: 800;
	}

	.meta-line a {
		display: inline-flex;
		gap: 6px;
		align-items: center;
	}

	.status-pill {
		border-radius: 999px;
		background: color-mix(in srgb, var(--pill) 12%, transparent);
		color: var(--pill);
		font-weight: 900;
		padding: 7px 11px;
		white-space: nowrap;
	}

	.detail-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 10px;
	}

	.description,
	.requester,
	.thread,
	.context-box {
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: 8px;
		padding: 14px;
		background: #fbfdff;
	}

	.description {
		display: grid;
		gap: 8px;
	}

	.description p {
		white-space: pre-wrap;
		line-height: 1.55;
	}

	.requester p {
		margin: 4px 0;
		font-weight: 800;
	}

	.context-box {
		display: grid;
		gap: 4px;
	}

	.thread {
		display: grid;
		gap: 12px;
	}

	.messages {
		display: grid;
		gap: 8px;
	}

	.messages article {
		border-radius: 8px;
		background: #fff;
		border: 1px solid var(--border-color, #d8e1ec);
		padding: 12px;
	}

	.messages article.internal {
		background: #fffbeb;
		border-color: #fde68a;
	}

	.messages article div {
		display: flex;
		justify-content: space-between;
		gap: 10px;
		margin-bottom: 6px;
	}

	.messages p {
		white-space: pre-wrap;
		line-height: 1.5;
	}

	.reply {
		display: grid;
		gap: 10px;
	}

	.checkbox {
		display: inline-flex;
		grid-template-columns: none;
		align-items: center;
		gap: 7px;
		font-weight: 700;
	}

	.checkbox input {
		width: auto;
	}

	.activity {
		padding: 16px;
		display: grid;
		align-content: start;
		gap: 10px;
	}

	.activity article {
		display: grid;
		gap: 4px;
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: 8px;
		padding: 10px;
		background: #fbfdff;
	}

	.empty-state {
		min-height: 240px;
		display: grid;
		place-items: center;
		gap: 8px;
		text-align: center;
		color: var(--text-color, #60708a);
	}

	.empty-state.large {
		min-height: 560px;
	}

	@media (max-width: 1180px) {
		.workspace {
			grid-template-columns: 340px minmax(0, 1fr);
		}

		.activity {
			grid-column: 1 / -1;
			min-height: 0;
		}

		.create-panel {
			grid-template-columns: 1fr 1fr;
		}
	}

	@media (max-width: 820px) {
		.page {
			padding: 14px;
		}

		.topbar,
		.requester,
		.form-actions {
			align-items: stretch;
			flex-direction: column;
		}

		.top-actions,
		.metrics,
		.workspace,
		.detail-grid,
		.create-panel,
		.jql-row {
			grid-template-columns: 1fr;
		}

		.queue,
		.detail,
		.activity {
			min-height: 0;
		}
	}
</style>
