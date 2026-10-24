<script>
	// @ts-nocheck
	import Icon from '@iconify/svelte'
	import content from '$content'
	import data from '$data'
	import { api, auth, language } from '$hangarkit'

	let polls = $state([])
	let options = $state([])
	let votes = $state([])
	let loading = $state(true)
	let mode = $state('manage')
	let route_poll = $state('')
	let route_email = $state('')
	let selected_poll_id = $state('')
	let selected_option_id = $state('')
	let current_user = $state(null)
	let copied_link = $state('')
	let toast = $state('')
	let busy = $state(false)
	let hydrated_key = ''
	let language_id = $state('en')

	language.subscribe((value) => {
		language_id = value.id || 'en'
	})

	auth.currentUser().then((user) => {
		current_user = user
	}).catch(() => {
		current_user = null
	})

	function t(key, fallback = '') {
		const packs = content.localized_copy || {}
		return packs[language_id]?.[key] || packs.en?.[key] || content[key] || fallback
	}

	let new_poll = $state({
		question: '',
		description: '',
		closes_at: ''
	})
	let new_option_text = $state('')
	let invite_email = $state('')

	data.polls.subscribe((items) => {
		polls = [...items].sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
		loading = false
	})

	data.options.subscribe((items) => {
		options = [...items].sort((a, b) => Number(a.order || 0) - Number(b.order || 0))
	})

	data.votes.subscribe((items) => {
		votes = [...items].sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
	})

	$effect(() => {
		if (typeof window === 'undefined') return
		const params = new URL(window.location.href).searchParams
		route_poll = params.get('poll') || params.get('poll_name') || ''
		route_email = params.get('email') || ''
		mode = route_poll ? 'vote' : 'manage'
	})

	$effect(() => {
		if (!selected_poll_id && polls.length) selected_poll_id = polls[0].id
	})

	let response_poll = $derived(
		polls.find((poll) => poll.slug === route_poll || poll.id === route_poll || poll.question === route_poll)
	)
	let manager_poll = $derived(polls.find((poll) => poll.id === selected_poll_id) || polls[0])
	let active_poll = $derived(mode === 'vote' ? response_poll : manager_poll)
	let poll_options = $derived(
		active_poll ? options.filter((option) => option.poll_id === active_poll.id || option.poll_slug === active_poll.slug) : []
	)
	let poll_votes = $derived(
		active_poll ? votes.filter((vote) => vote.poll_id === active_poll.id || vote.poll_slug === active_poll.slug) : []
	)
	let voter_identity = $derived({
		email: current_user?.email || route_email || '',
		name: current_user?.name || current_user?.email?.split('@')[0] || route_email?.split('@')[0] || ''
	})
	let total_votes = $derived(poll_options.reduce((sum, option) => sum + Number(option.votes || 0), 0))
	let existing_vote = $derived(
		active_poll && voter_identity.email
			? poll_votes.find((vote) => lower(vote.voter_email) === lower(voter_identity.email))
			: null
	)
	let winning_option = $derived(
		poll_options.reduce((winner, option) => (Number(option.votes || 0) > Number(winner?.votes || -1) ? option : winner), null)
	)

	$effect(() => {
		if (!active_poll) return
		const key = `${active_poll.id}:${voter_identity.email}:${existing_vote?.id || 'new'}`
		if (key === hydrated_key) return
		hydrated_key = key
		if (existing_vote) {
			selected_option_id = existing_vote.option_id
		}
	})

	function lower(value) {
		return String(value || '').trim().toLowerCase()
	}

	function slugify(value) {
		return String(value || 'poll')
			.toLowerCase()
			.trim()
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/(^-|-$)/g, '')
			.slice(0, 64)
	}

	function public_link(poll, email = '') {
		if (typeof window === 'undefined' || !poll) return ''
		const url = new URL(window.location.href)
		url.search = ''
		url.searchParams.set('poll', poll.slug || poll.id)
		if (email) url.searchParams.set('email', email)
		return url.toString()
	}

	function percentage(option) {
		if (!total_votes) return 0
		return Math.round((Number(option.votes || 0) / total_votes) * 100)
	}

	async function copy_link(poll, email = '') {
		const link = public_link(poll, email)
		if (!link) return
		await navigator.clipboard?.writeText(link)
		copied_link = link
		toast = 'Poll link copied'
		setTimeout(() => {
			toast = ''
		}, 2200)
	}

	async function create_poll() {
		if (!new_poll.question.trim()) return
		const created = await data.polls.create({
			slug: slugify(new_poll.question),
			question: new_poll.question.trim(),
			description: new_poll.description.trim(),
			status: 'Draft',
			closes_at: new_poll.closes_at,
			created_at: new Date().toISOString()
		})
		selected_poll_id = created?.id || selected_poll_id
		new_poll = { question: '', description: '', closes_at: '' }
	}

	async function add_option() {
		if (!manager_poll || !new_option_text.trim()) return
		await data.options.create({
			poll_id: manager_poll.id,
			poll_slug: manager_poll.slug,
			text: new_option_text.trim(),
			votes: 0,
			order: poll_options.length
		})
		new_option_text = ''
	}

	async function delete_option(option) {
		await data.options.delete(option.id)
	}

	async function update_poll_status(poll, status) {
		await data.polls.update(poll.id, { status })
	}

	async function submit_vote(event) {
		event.preventDefault()
		if (!active_poll || !selected_option_id) return
		if (!voter_identity.email) {
			toast = 'Please sign in to vote.'
			return
		}
		const option = poll_options.find((item) => item.id === selected_option_id)
		if (!option) return
		busy = true

		if (existing_vote && existing_vote.option_id !== selected_option_id) {
			const previous = poll_options.find((item) => item.id === existing_vote.option_id)
			if (previous) await data.options.update(previous.id, { votes: Math.max(0, Number(previous.votes || 0) - 1) })
		}
		if (!existing_vote || existing_vote.option_id !== selected_option_id) {
			await data.options.update(option.id, { votes: Number(option.votes || 0) + 1 })
		}

		const payload = {
			poll_id: active_poll.id,
			poll_slug: active_poll.slug,
			option_id: selected_option_id,
			voter_email: voter_identity.email,
			voter_name: voter_identity.name,
			created_at: existing_vote?.created_at || new Date().toISOString()
		}
		if (existing_vote) await data.votes.update(existing_vote.id, payload)
		else await data.votes.create(payload)
		busy = false
		toast = t('thank_you_message', 'Your vote has been saved.')
	}

	async function email_poll(poll, email = '') {
		if (!poll) return
		const link = public_link(poll, email)
		try {
			const result = await api.post('/share-draft', { kind: 'poll', poll, email, link })
			toast = result.message || 'Poll email draft prepared.'
			if (result.mailto && typeof window !== 'undefined') window.location.href = result.mailto
		} catch (error) {
			const subject = encodeURIComponent(`Vote: ${poll.question}`)
			const body = encodeURIComponent(`Please vote here:\n\n${link}`)
			if (typeof window !== 'undefined') window.location.href = `mailto:${email}?subject=${subject}&body=${body}`
		}
	}
</script>

{#if loading}
	<div class="page centered">
		<Icon icon="lucide:loader-2" class="spin" width={28} />
	</div>
{:else if mode === 'vote'}
	<div class="page vote-page">
		{#if !response_poll}
			<section class="poll-card">
				<Icon icon="lucide:badge-alert" width={34} />
				<h1>Poll not found</h1>
				<p>Ask the sender for a fresh poll link.</p>
			</section>
		{:else}
			<section class="poll-card">
				<div class="poll-kicker">
					<Icon icon="lucide:radio" width={18} />
					Live poll · {response_poll.status}
				</div>
				<h1>{response_poll.question}</h1>
				{#if response_poll.description}
					<p class="description">{response_poll.description}</p>
				{/if}

				<form class="vote-form" onsubmit={submit_vote}>
					<div class="identity-note">
						<Icon icon="lucide:user-check" width={16} />
						<span>{voter_identity.email ? `Voting as ${voter_identity.email}` : 'Sign in to vote'}</span>
					</div>

					<div class="options">
						{#each poll_options as option (option.id)}
							<button
								type="button"
								class="option"
								class:selected={selected_option_id === option.id}
								onclick={() => (selected_option_id = option.id)}
							>
								<div class="option-top">
									<strong>{option.text}</strong>
									<span>{percentage(option)}%</span>
								</div>
								<div class="bar"><span style={`width: ${percentage(option)}%`}></span></div>
								<small>{option.votes || 0} votes</small>
							</button>
						{/each}
					</div>

					<button class="primary" type="submit" disabled={busy || response_poll.status === 'Closed' || !voter_identity.email}>
						<span class:spin={busy}><Icon icon={busy ? 'lucide:loader-2' : 'lucide:vote'} width={18} /></span>
						{existing_vote ? 'Update vote' : t('vote_button_label', 'Submit vote')}
					</button>
				</form>

				{#if toast}
					<p class="notice">{toast}</p>
				{/if}
			</section>
		{/if}
	</div>
{:else}
	<div class="page manager-page">
		<header class="manager-header">
			<div>
				<p class="eyebrow">Poll Manager</p>
				<h1>{t('manager_title', 'Polls')}</h1>
				<p>{t('manager_intro', 'Create reusable polls, share voting links, and watch results.')}</p>
			</div>
			<div class="header-actions">
				<button class="ghost" onclick={() => manager_poll && copy_link(manager_poll)}>
					<Icon icon="lucide:copy" width={16} /> {t('copy_link_label', 'Copy link')}
				</button>
				<button class="primary" onclick={() => email_poll(manager_poll, invite_email)}>
					<Icon icon="lucide:mail-plus" width={16} /> {t('email_draft_label', 'Prepare email')}
				</button>
			</div>
		</header>

		<main class="manager-grid">
			<aside class="poll-list">
				<div class="panel-title">
					<h2>Polls</h2>
					<span>{polls.length}</span>
				</div>
				{#each polls as poll (poll.id)}
					<button class="poll-row" class:active={manager_poll?.id === poll.id} onclick={() => (selected_poll_id = poll.id)}>
						<span class="poll-name">{poll.question}</span>
						<span class="poll-meta">{poll.status} · {poll.closes_at || 'No close date'}</span>
					</button>
				{/each}

				<form class="create-card" onsubmit={(event) => { event.preventDefault(); create_poll() }}>
					<h3>New poll</h3>
					<input bind:value={new_poll.question} placeholder="Poll question" required />
					<textarea bind:value={new_poll.description} rows="3" placeholder="Short description"></textarea>
					<input type="date" bind:value={new_poll.closes_at} aria-label="Close date" />
					<button class="primary" type="submit"><Icon icon="lucide:plus" width={16} /> Create poll</button>
				</form>
			</aside>

			{#if manager_poll}
				<section class="workspace">
					<div class="workspace-head">
						<div>
							<div class="poll-kicker">Reusable poll</div>
							<h2>{manager_poll.question}</h2>
							<p>{manager_poll.description}</p>
						</div>
						<select value={manager_poll.status} onchange={(event) => update_poll_status(manager_poll, event.currentTarget.value)}>
							<option>Draft</option>
							<option>Open</option>
							<option>Closed</option>
							<option>Archived</option>
						</select>
					</div>

					<div class="stats">
						<div><strong>{total_votes}</strong><span>Total votes</span></div>
						<div><strong>{poll_options.length}</strong><span>Options</span></div>
						<div><strong>{winning_option?.text || 'No votes'}</strong><span>Leading</span></div>
					</div>

					<div class="share-panel">
						<div>
							<label>Public link</label>
							<code>{public_link(manager_poll)}</code>
						</div>
						<button class="ghost" onclick={() => copy_link(manager_poll)}><Icon icon="lucide:copy" width={16} /> Copy</button>
					</div>

					<form class="invite-panel" onsubmit={(event) => { event.preventDefault(); email_poll(manager_poll, invite_email) }}>
						<input type="email" bind:value={invite_email} placeholder="respondent@example.com" />
						<button class="ghost" type="button" onclick={() => copy_link(manager_poll, invite_email)}>
							<Icon icon="lucide:link" width={16} /> Copy personal link
						</button>
						<button class="primary" type="submit">
							<Icon icon="lucide:mail" width={16} /> Draft email
						</button>
					</form>

					<form class="option-add" onsubmit={(event) => { event.preventDefault(); add_option() }}>
						<input bind:value={new_option_text} placeholder="Add poll option" />
						<button class="primary" type="submit"><Icon icon="lucide:plus" width={16} /> Add option</button>
					</form>

					<div class="result-list">
						{#each poll_options as option (option.id)}
							<article class="result-card" class:leader={winning_option?.id === option.id && total_votes > 0}>
								<div class="result-top">
									<strong>{option.text}</strong>
									<span>{option.votes || 0} votes · {percentage(option)}%</span>
								</div>
								<div class="bar"><span style={`width: ${percentage(option)}%`}></span></div>
								<button class="link-button" onclick={() => delete_option(option)}>Remove</button>
							</article>
						{:else}
							<p class="empty">Add options before sharing this poll.</p>
						{/each}
					</div>

					<div class="vote-table">
						<div class="panel-title">
							<h3>Recent voters</h3>
							<span>{poll_votes.length}</span>
						</div>
						{#each poll_votes.slice(0, 8) as vote (vote.id)}
							<div class="vote-row">
								<span>{vote.voter_name || vote.voter_email}</span>
								<small>{poll_options.find((option) => option.id === vote.option_id)?.text || 'Unknown option'}</small>
							</div>
						{:else}
							<p class="empty">No votes yet.</p>
						{/each}
					</div>
				</section>
			{/if}
		</main>

		{#if toast}
			<div class="toast">{toast}</div>
		{/if}
	</div>
{/if}

<style>
	:global(*) {
		box-sizing: border-box;
	}

	.page {
		min-height: 100vh;
		background: var(--page-background, #f4f7fb);
		color: var(--body-text, #334155);
		font-family: var(--body-font, Inter, system-ui, sans-serif);
		padding: 24px;
	}

	.centered,
	.vote-page {
		display: grid;
		place-items: center;
	}

	.spin {
		animation: spin 1s linear infinite;
	}

	.manager-header,
	.manager-grid {
		max-width: 1180px;
		margin: 0 auto;
	}

	.manager-header {
		display: flex;
		align-items: end;
		justify-content: space-between;
		gap: 18px;
		padding: 18px 0 22px;
	}

	.eyebrow,
	.poll-kicker {
		color: var(--accent-color, #4f46e5);
		font-size: 0.78rem;
		font-weight: 850;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	h1,
	h2,
	h3,
	p {
		margin-top: 0;
	}

	h1,
	h2,
	h3 {
		color: var(--heading-color, #172033);
		letter-spacing: 0;
	}

	.manager-header h1,
	.poll-card h1 {
		font-size: clamp(2rem, 5vw, 3.5rem);
		line-height: 1;
		margin-bottom: 10px;
	}

	.manager-header p,
	.workspace-head p,
	.description {
		color: var(--secondary-text, #64748b);
	}

	.header-actions,
	.invite-panel,
	.option-add {
		display: flex;
		gap: 10px;
	}

	button,
	input,
	textarea,
	select {
		font: inherit;
		border-radius: var(--control-radius, 6px);
	}

	input,
	textarea,
	select {
		width: 100%;
		border: 1px solid var(--border-color, #d8e1ec);
		background: #fff;
		color: var(--body-text, #334155);
		padding: 10px 12px;
	}

	textarea {
		resize: vertical;
	}

	button {
		border: 0;
		cursor: pointer;
	}

	.primary,
	.ghost {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		min-height: 38px;
		padding: 10px 14px;
		font-weight: 850;
		white-space: nowrap;
	}

	.primary {
		background: var(--accent-color, #4f46e5);
		color: #fff;
	}

	.ghost {
		background: var(--surface-background, #fff);
		color: var(--heading-color, #172033);
		border: 1px solid var(--border-color, #d8e1ec);
	}

	.manager-grid {
		display: grid;
		grid-template-columns: 340px minmax(0, 1fr);
		gap: 18px;
		align-items: start;
	}

	.poll-list,
	.workspace,
	.poll-card {
		background: var(--surface-background, #fff);
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: var(--card-radius, 8px);
		box-shadow: 0 20px 50px rgba(23, 32, 51, 0.08);
	}

	.poll-list,
	.workspace {
		padding: 16px;
	}

	.panel-title,
	.workspace-head,
	.share-panel,
	.result-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 14px;
	}

	.panel-title h2,
	.panel-title h3,
	.workspace-head h2 {
		margin-bottom: 0;
	}

	.poll-row {
		width: 100%;
		display: grid;
		gap: 4px;
		text-align: left;
		background: transparent;
		border: 1px solid transparent;
		padding: 12px;
		border-radius: var(--control-radius, 6px);
		color: inherit;
	}

	.poll-row.active,
	.poll-row:hover {
		background: var(--panel-background, #f8fafc);
		border-color: var(--border-color, #d8e1ec);
	}

	.poll-name {
		font-weight: 850;
		color: var(--heading-color, #172033);
	}

	.poll-meta,
	.empty,
	.vote-row small,
	.result-top span {
		color: var(--secondary-text, #64748b);
		font-size: 0.86rem;
	}

	.create-card,
	.vote-form {
		display: grid;
		gap: 10px;
	}

	.identity-note {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: var(--control-radius, 6px);
		background: var(--panel-background, #f8fafc);
		color: var(--secondary-text, #64748b);
		padding: 10px 12px;
		font-size: 0.9rem;
		font-weight: 750;
	}

	.create-card {
		margin-top: 18px;
		padding-top: 16px;
		border-top: 1px solid var(--border-color, #d8e1ec);
	}

	.stats {
		display: grid;
		grid-template-columns: 120px 120px minmax(0, 1fr);
		gap: 10px;
		margin: 18px 0;
	}

	.stats div,
	.share-panel,
	.invite-panel,
	.option-add,
	.result-card,
	.vote-row {
		background: var(--panel-background, #f8fafc);
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: var(--card-radius, 8px);
		padding: 12px;
	}

	.stats strong {
		display: block;
		color: var(--heading-color, #172033);
		font-size: 1.3rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.stats span {
		color: var(--secondary-text, #64748b);
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
	}

	.share-panel,
	.invite-panel,
	.option-add,
	.result-card,
	.vote-table {
		margin-bottom: 12px;
	}

	code {
		display: block;
		max-width: 100%;
		overflow: hidden;
		text-overflow: ellipsis;
		color: var(--accent-color, #4f46e5);
	}

	.result-list,
	.options {
		display: grid;
		gap: 10px;
	}

	.result-card.leader {
		border-color: var(--success-color, #2f8f62);
	}

	.option {
		display: grid;
		gap: 8px;
		width: 100%;
		text-align: left;
		background: var(--panel-background, #f8fafc);
		border: 2px solid var(--border-color, #d8e1ec);
		border-radius: var(--card-radius, 8px);
		padding: 14px;
		color: inherit;
	}

	.option.selected {
		border-color: var(--accent-color, #4f46e5);
		background: #eef2ff;
	}

	.option-top {
		display: flex;
		justify-content: space-between;
		gap: 12px;
	}

	.bar {
		height: 9px;
		background: #e2e8f0;
		border-radius: 999px;
		overflow: hidden;
	}

	.bar span {
		display: block;
		height: 100%;
		background: linear-gradient(90deg, var(--accent-color, #4f46e5), var(--success-color, #2f8f62));
		border-radius: inherit;
		transition: width 0.25s ease;
	}

	.link-button {
		background: transparent;
		color: var(--accent-color, #4f46e5);
		padding: 6px 0 0;
		font-weight: 800;
	}

	.vote-row {
		display: flex;
		justify-content: space-between;
		gap: 12px;
	}

	.poll-card {
		width: min(100%, 640px);
		padding: 28px;
	}

	label {
		display: grid;
		gap: 6px;
		color: var(--heading-color, #172033);
		font-size: 0.86rem;
		font-weight: 850;
	}

	.notice,
	.toast {
		background: #ecfdf5;
		color: var(--success-color, #2f8f62);
		border: 1px solid #bbf7d0;
		border-radius: var(--control-radius, 6px);
		padding: 10px 12px;
	}

	.toast {
		position: fixed;
		right: 22px;
		bottom: 22px;
		box-shadow: 0 12px 28px rgba(23, 32, 51, 0.16);
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	@media (max-width: 860px) {
		.page {
			padding: 14px;
		}

		.manager-header,
		.manager-grid,
		.header-actions,
		.invite-panel,
		.option-add {
			display: grid;
			grid-template-columns: 1fr;
		}

		.stats {
			grid-template-columns: 1fr;
		}
	}
</style>
