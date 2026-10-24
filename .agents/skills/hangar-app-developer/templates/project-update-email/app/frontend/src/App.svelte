<script lang="ts">
	// @ts-nocheck
	import { onMount } from 'svelte'
	import Icon from '@iconify/svelte'
	import { api, auth, language, nav } from '$hangarkit'
	import content from '$content'

	let jira_input = $state('')
	let recipients = $state('')
	let subject = $state('')
	let loading = $state(false)
	let sending = $state(false)
	let error = $state('')
	let runs = $state([])
	let active_run = $state(null)
	let active_tab = $state('email')
	let lang = $state('en')
	let current_user = $state(null)
	let snapshot_mode = $state(false)

	const copy = $derived(localized_copy(lang))
	const changed_issues = $derived((active_run?.issues || []).filter((issue) => issue.was_updated || issue.is_new))
	const unchanged_issues = $derived((active_run?.issues || []).filter((issue) => !issue.was_updated && !issue.is_new))
	const current_jira_key = $derived(extract_jira_key(jira_input))
	const recipient_count = $derived(recipient_list().length)
	const email_subject = $derived(subject || (active_run ? `${active_run.epic_key}: ${active_run.updated_count || 0} Jira updates` : copy.default_subject))
	const status_entries = $derived(Object.entries(active_run?.summary?.by_status || {}).sort((a, b) => Number(b[1]) - Number(a[1])))
	const top_changed = $derived(changed_issues.slice(0, 6))
	const current_user_email = $derived(current_user?.email || '')
	const email_intro = $derived(active_run
		? `${active_run.epic_key} has ${active_run.updated_count || 0} ticket updates, including ${active_run.new_count || 0} new items.`
		: 'Generate a Jira update to preview the stakeholder email.')

	onMount(() => {
		const stop_language = language.subscribe((value) => {
			lang = value.id || 'en'
		})
		async function init() {
			const params = new URLSearchParams(window.location.search)
			snapshot_mode = params.get('snapshot') === 'email'
			await load_user()
			await load_runs()
			const run_id = params.get('run')
			if (run_id) await load_run(run_id)
		}
		init()
		return () => stop_language()
	})

	function localized_copy(id: string) {
		const packs = content.localized_copy || {}
		return {
			app_title: content.app_title || content['App Title'] || '__HANGAR_APP_NAME__',
			description: content.description || content.Description || 'Turn Jira epic deltas into polished stakeholder emails.',
			source_title: 'Project source',
			report_title: 'Email preview',
			composer_title: 'Send update',
			history_title: 'Recent briefs',
			generate: 'Build email preview',
			generating: 'Building...',
			send: 'Send update',
			sending: 'Sending...',
			default_subject: 'Project update brief',
			...(packs.en || {}),
			...(packs[id] || {})
		}
	}

	async function load_user() {
		try {
			const user = await auth.currentUser()
			current_user = user
			if (!recipients.trim() && user?.email) recipients = user.email
		} catch {
			current_user = null
		}
	}

	function extract_jira_key(value: string) {
		const match = String(value || '').trim().toUpperCase().match(/(?:BROWSE\/)?([A-Z][A-Z0-9]+-\d+)/)
		return match?.[1] || String(value || '').trim().toUpperCase()
	}

	function recipient_list() {
		return recipients.split(/[,\n;]/).map((item) => item.trim()).filter(Boolean)
	}

	async function load_runs() {
		error = ''
		try {
			const result = await api.get('/runs')
			runs = result.items || []
			if (!active_run && runs[0]) apply_run(runs[0])
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load runs'
		}
	}

	async function load_run(id: string) {
		error = ''
		try {
			const run = await api.get(`/runs/${id}`)
			apply_run(run)
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load run'
		}
	}

	function apply_run(run: any) {
		active_run = run
		jira_input = run?.epic_key || jira_input
		const saved = run?.recipients || []
		if (saved.length > 0) recipients = saved.join(', ')
		else if (!recipients.trim() && current_user_email) recipients = current_user_email
		if (!subject && run?.epic_key) subject = `${run.epic_key}: ${run.updated_count || 0} Jira updates`
	}

	async function load_saved_recipients() {
		if (!current_jira_key) return
		try {
			const result = await api.get(`/email-preferences/${encodeURIComponent(current_jira_key)}`)
			const saved = result.recipients || []
			const only_me = current_user_email && recipients.trim() === current_user_email
			if (Array.isArray(saved) && saved.length > 0 && (!recipients.trim() || only_me)) recipients = saved.join(', ')
		} catch {
			// No saved recipients yet.
		}
	}

	async function generate_update() {
		loading = true
		error = ''
		try {
			const result = await api.post('/generate', {
				jira: jira_input,
				compare_mode: 'last',
				compare_since: '',
				recipients: recipient_list()
			})
			apply_run(result.run)
			active_tab = 'email'
			await load_runs()
			if (active_run?.id && !snapshot_mode) history.replaceState({}, '', nav.href(`/?run=${active_run.id}`))
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to generate project update'
		} finally {
			loading = false
		}
	}

	async function send_update_email() {
		if (!active_run?.id) return
		sending = true
		error = ''
		try {
			const result = await api.post(`/runs/${active_run.id}/send`, {
				recipients: recipient_list(),
				subject: email_subject
			})
			apply_run(result.run)
			await load_runs()
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to send project update email'
		} finally {
			sending = false
		}
	}

	function format_time(value?: string) {
		if (!value) return 'Not available'
		return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
	}

	function format_date(value?: string) {
		if (!value) return ''
		return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(value))
	}

	function issue_tone(issue) {
		if (issue.is_new) return 'New'
		if (issue.was_updated) return 'Updated'
		return 'Tracked'
	}

	function update_window() {
		if (!active_run?.compare_since) return 'Auto window'
		return `Since ${format_time(active_run.compare_since)}`
	}

	function share_url() {
		return active_run?.id ? nav.href(`/?run=${active_run.id}`) : '#'
	}

	function snapshot_url() {
		return active_run?.id ? nav.href(`/?run=${active_run.id}&snapshot=email`) : '#'
	}
</script>

{#snippet emailPreview()}
	<section class="email-paper" aria-label="Email preview">
		<div class="email-topline">
			<span>Project brief</span>
			<strong>{active_run ? format_date(active_run.created_at) : 'Draft'}</strong>
		</div>
		<div class="email-hero">
			<div>
				<span>Jira epic</span>
				<h2>{active_run?.epic_key || 'Ready for your Jira epic'}</h2>
				<p>{email_intro}</p>
			</div>
			<div class="score">
				<strong>{active_run?.updated_count || 0}</strong>
				<span>changed</span>
			</div>
		</div>
		<div class="email-subject">
			<span>Subject</span>
			<strong>{email_subject}</strong>
		</div>
		<div class="email-metrics">
			<article>
				<strong>{active_run?.total_count || 0}</strong>
				<span>Total tickets</span>
			</article>
			<article>
				<strong>{active_run?.new_count || 0}</strong>
				<span>New tickets</span>
			</article>
			<article>
				<strong>{unchanged_issues.length}</strong>
				<span>Unchanged</span>
			</article>
		</div>
		<section class="email-section">
			<div class="section-heading">
				<h3>Highlights</h3>
				<span>{update_window()}</span>
			</div>
			{#if active_run && top_changed.length}
				<div class="email-issue-list">
					{#each top_changed as issue}
						<article>
							<div>
								<a href={issue.url || '#'} target="_blank" rel="noreferrer">{issue.key}</a>
								<span>{issue_tone(issue)}</span>
							</div>
							<strong>{issue.summary}</strong>
							<p>{issue.status || 'Unknown'} · {issue.assignee || 'Unassigned'} · updated {format_time(issue.updated)}</p>
						</article>
					{/each}
				</div>
			{:else if active_run}
				<p class="quiet">No issue changed in this automatic window. This email is still useful as a status heartbeat.</p>
			{:else}
				<div class="preview-empty">
					<Icon icon="lucide:mail-check" width={30} />
					<p>Generate a report to see the finished email here.</p>
				</div>
			{/if}
		</section>
		{#if status_entries.length}
			<section class="email-section compact">
				<div class="section-heading">
					<h3>Status mix</h3>
					<span>{status_entries.length} states</span>
				</div>
				<div class="status-pills">
					{#each status_entries.slice(0, 6) as [status, count]}
						<span><strong>{count}</strong>{status}</span>
					{/each}
				</div>
			</section>
		{/if}
		<div class="email-footer">
			<a href={share_url()}>Open live report</a>
			<span>Prepared by {active_run?.created_by || current_user_email || 'Hangar'}</span>
		</div>
	</section>
{/snippet}

{#if snapshot_mode}
	<main class="snapshot-app">
		{@render emailPreview()}
	</main>
{:else}
	<main class="app">
		<header class="topbar">
			<div class="brand">
				<span>Jira email studio</span>
				<h1>{copy.app_title}</h1>
				<p>{copy.description}</p>
			</div>
			<div class="top-actions">
				<div>
					<strong>{active_run ? `${active_run.updated_count || 0} updates ready` : 'Ready to brief'}</strong>
					<span>{current_user_email || 'Signed in'}</span>
				</div>
				<a href={active_run ? snapshot_url() : '#'} class:disabled={!active_run} target="_blank" rel="noreferrer">
					<Icon icon="lucide:eye" width={16} />
					Email view
				</a>
			</div>
		</header>

		<section class="workspace">
			<aside class="rail">
				<section class="panel source">
					<div class="panel-title">
						<Icon icon="lucide:radar" width={18} />
						<h2>{copy.source_title}</h2>
					</div>
					<form onsubmit={(event) => { event.preventDefault(); generate_update() }}>
						<label>
							<span>Jira epic or link</span>
							<input bind:value={jira_input} onblur={load_saved_recipients} placeholder="SPOT-62800 or Jira URL" required />
						</label>
						<div class="auto-window">
							<Icon icon="lucide:history" width={16} />
							<span>Uses last run automatically, or the past 7 days for a new epic.</span>
						</div>
						<button class="primary" disabled={loading}>
							<Icon icon={loading ? 'lucide:loader-2' : 'lucide:sparkles'} width={16} />
							{loading ? copy.generating : copy.generate}
						</button>
					</form>
				</section>

				<section class="panel composer">
					<div class="panel-title">
						<Icon icon="lucide:send" width={18} />
						<h2>{copy.composer_title}</h2>
					</div>
					<label>
						<span>Subject</span>
						<input bind:value={subject} placeholder={email_subject} />
					</label>
					<label>
						<span>Recipients</span>
						<textarea bind:value={recipients} placeholder={current_user_email || 'team@example.com'}></textarea>
					</label>
					<div class="send-summary">
						<strong>{recipient_count}</strong>
						<span>recipient{recipient_count === 1 ? '' : 's'} selected</span>
					</div>
					<button class="primary send" disabled={sending || !active_run?.id || recipient_count === 0} onclick={send_update_email}>
						<Icon icon={sending ? 'lucide:loader-2' : 'lucide:mail'} width={16} />
						{sending ? copy.sending : copy.send}
					</button>
					{#if active_run?.email_sent}<p class="success">Sent. Recipients are saved for {active_run.epic_key}.</p>{/if}
					{#if error}<p class="error">{error}</p>{/if}
				</section>

				<section class="panel history-block">
					<div class="panel-title">
						<Icon icon="lucide:clock-3" width={18} />
						<h2>{copy.history_title}</h2>
					</div>
					<div class="history-list">
						{#each runs as run}
							<button class:active={active_run?.id === run.id} onclick={() => load_run(run.id)}>
								<strong>{run.epic_key}</strong>
								<span>{run.updated_count} updates · {format_time(run.created_at)}</span>
							</button>
						{/each}
						{#if !runs.length}<p class="quiet">No briefs generated yet.</p>{/if}
					</div>
				</section>
			</aside>

			<section class="mainstage">
				<nav class="tabs" aria-label="Preview tabs">
					<button class:active={active_tab === 'email'} onclick={() => active_tab = 'email'}>
						<Icon icon="lucide:mail-check" width={15} />
						{copy.report_title}
					</button>
					<button class:active={active_tab === 'issues'} onclick={() => active_tab = 'issues'}>
						<Icon icon="lucide:list-checks" width={15} />
						Jira detail
					</button>
				</nav>

				{#if active_tab === 'email'}
					{@render emailPreview()}
				{:else}
					<section class="detail-panel">
						<div class="detail-head">
							<div>
								<span>{active_run ? update_window() : 'No report yet'}</span>
								<h2>{active_run ? `${active_run.epic_key} Jira detail` : 'Generate a report'}</h2>
							</div>
							<div class="detail-metrics">
								<article><strong>{active_run?.total_count || 0}</strong><span>Total</span></article>
								<article><strong>{changed_issues.length}</strong><span>Changed</span></article>
								<article><strong>{active_run?.new_count || 0}</strong><span>New</span></article>
							</div>
						</div>
						{#if active_run}
							<div class="issue-list">
								{#each changed_issues.length ? changed_issues : active_run.issues || [] as issue}
									<article class:new={issue.is_new}>
										<div class="issue-key">
											<a href={issue.url || '#'} target="_blank" rel="noreferrer">{issue.key}</a>
											<span>{issue_tone(issue)}</span>
										</div>
										<div>
											<strong>{issue.summary}</strong>
											<p>{issue.assignee || 'Unassigned'} · {issue.priority || 'No priority'} · {format_time(issue.updated)}</p>
										</div>
										<em>{issue.status}</em>
									</article>
								{/each}
							</div>
						{:else}
							<p class="quiet big">Choose a Jira epic and build the first email preview.</p>
						{/if}
					</section>
				{/if}
			</section>
		</section>
	</main>
{/if}

<style>
	:global(body) {
		margin: 0;
		background: var(--page-background, #f3f6fb);
		color: var(--ink-color, #162033);
		font-family: var(--font-family, Inter), ui-sans-serif, system-ui, sans-serif;
	}

	* { box-sizing: border-box; }
	button, input, textarea { font: inherit; }
	button { cursor: pointer; }
	a { color: inherit; }

	.app {
		min-height: 100vh;
		padding: 1rem;
	}

	.topbar {
		max-width: 1500px;
		margin: 0 auto 1rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 1rem 1.1rem;
		background: color-mix(in srgb, var(--panel-background, #ffffff) 92%, transparent);
		border: 1px solid var(--border-color, #d8e0ea);
		border-radius: var(--panel-radius, 8px);
		box-shadow: 0 18px 50px rgba(29, 45, 68, 0.08);
	}

	.brand span,
	.detail-head span,
	.email-topline span,
	.email-subject span,
	label span {
		color: var(--muted-ink-color, #667085);
		font-size: 0.76rem;
		font-weight: 850;
		text-transform: uppercase;
		letter-spacing: 0;
	}

	h1, h2, h3, p { margin-top: 0; }
	h1 { margin: 0.15rem 0 0.25rem; font-size: clamp(1.45rem, 3vw, 2.1rem); line-height: 1.05; }
	h2 { margin: 0; font-size: 1rem; }
	h3 { margin: 0; font-size: 0.95rem; }
	.brand p { margin: 0; color: var(--muted-ink-color, #667085); }

	.top-actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.top-actions > div {
		display: grid;
		gap: 0.18rem;
		text-align: right;
	}

	.top-actions span {
		color: var(--muted-ink-color, #667085);
		font-size: 0.85rem;
	}

	.top-actions a,
	.primary,
	.tabs button,
	.email-footer a {
		border: 0;
		border-radius: 7px;
		min-height: 38px;
		padding: 0 0.85rem;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.45rem;
		background: var(--accent-color, #2f6fed);
		color: #fff;
		font-weight: 850;
		text-decoration: none;
	}

	.top-actions a.disabled {
		opacity: 0.48;
		pointer-events: none;
	}

	.workspace {
		max-width: 1500px;
		margin: 0 auto;
		display: grid;
		grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
		gap: 1rem;
		align-items: start;
	}

	.rail,
	.source form,
	.composer,
	.history-block,
	.mainstage {
		display: grid;
		gap: 0.85rem;
	}

	.panel,
	.detail-panel,
	.email-paper {
		background: var(--panel-background, #ffffff);
		border: 1px solid var(--border-color, #d8e0ea);
		border-radius: var(--panel-radius, 8px);
		box-shadow: 0 18px 50px rgba(29, 45, 68, 0.08);
	}

	.panel {
		padding: 1rem;
	}

	.panel-title {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: var(--ink-color, #162033);
	}

	label {
		display: grid;
		gap: 0.42rem;
		font-weight: 800;
	}

	input,
	textarea {
		width: 100%;
		border: 1px solid var(--border-color, #d8e0ea);
		border-radius: 7px;
		padding: 0.78rem 0.85rem;
		background: var(--input-background, #fbfcfe);
		color: var(--ink-color, #162033);
		outline: none;
	}

	input:focus,
	textarea:focus {
		border-color: var(--accent-color, #2f6fed);
		box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent-color, #2f6fed) 14%, transparent);
	}

	textarea {
		min-height: 108px;
		resize: vertical;
	}

	.auto-window,
	.send-summary,
	.success,
	.error,
	.quiet {
		border-radius: 7px;
		padding: 0.75rem;
		background: var(--soft-panel, #edf3f8);
		color: var(--muted-ink-color, #667085);
	}

	.auto-window {
		display: flex;
		align-items: flex-start;
		gap: 0.55rem;
		font-size: 0.88rem;
	}

	.send-summary {
		display: flex;
		align-items: baseline;
		gap: 0.45rem;
	}

	.send-summary strong {
		font-size: 1.4rem;
		color: var(--accent-color, #2f6fed);
	}

	.success { color: var(--positive-color, #087f5b); }
	.error { color: var(--danger-color, #b42318); }
	button:disabled { opacity: 0.55; cursor: wait; }

	.history-list {
		display: grid;
		gap: 0.55rem;
		max-height: 34vh;
		overflow: auto;
	}

	.history-list button {
		border: 1px solid var(--border-color, #d8e0ea);
		border-radius: 7px;
		background: var(--panel-background, #ffffff);
		color: inherit;
		text-align: left;
		padding: 0.75rem;
		display: grid;
		gap: 0.25rem;
	}

	.history-list button.active {
		border-color: var(--accent-color, #2f6fed);
		box-shadow: inset 4px 0 0 var(--accent-color, #2f6fed);
	}

	.history-list span {
		color: var(--muted-ink-color, #667085);
		font-size: 0.85rem;
	}

	.tabs {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.tabs button {
		background: var(--panel-background, #ffffff);
		color: var(--muted-ink-color, #667085);
		border: 1px solid var(--border-color, #d8e0ea);
	}

	.tabs button.active {
		background: var(--ink-color, #162033);
		color: #fff;
		border-color: var(--ink-color, #162033);
	}

	.email-paper {
		max-width: 860px;
		width: 100%;
		margin: 0 auto;
		overflow: hidden;
	}

	.email-topline {
		min-height: 56px;
		padding: 1rem 1.25rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		border-bottom: 1px solid var(--border-color, #d8e0ea);
		background: linear-gradient(90deg, color-mix(in srgb, var(--accent-color, #2f6fed) 10%, #fff), #fff);
	}

	.email-hero {
		padding: 1.35rem 1.25rem;
		display: grid;
		grid-template-columns: minmax(0, 1fr) 118px;
		gap: 1rem;
		align-items: center;
	}

	.email-hero span {
		color: var(--accent-color, #2f6fed);
		font-weight: 850;
		font-size: 0.8rem;
		text-transform: uppercase;
	}

	.email-hero h2 {
		margin: 0.28rem 0 0.42rem;
		font-size: clamp(1.7rem, 4vw, 2.55rem);
		line-height: 1;
	}

	.email-hero p,
	.email-section p,
	.email-footer span,
	.issue-list p {
		margin: 0;
		color: var(--muted-ink-color, #667085);
	}

	.score {
		aspect-ratio: 1;
		border-radius: 8px;
		background: var(--ink-color, #162033);
		color: #fff;
		display: grid;
		place-items: center;
		align-content: center;
	}

	.score strong {
		font-size: 2.1rem;
		line-height: 1;
	}

	.score span {
		color: color-mix(in srgb, #fff 76%, transparent);
		text-transform: none;
	}

	.email-subject {
		margin: 0 1.25rem 1rem;
		padding: 0.9rem 1rem;
		display: grid;
		gap: 0.2rem;
		border-radius: 8px;
		background: var(--soft-panel, #edf3f8);
	}

	.email-metrics {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.7rem;
		padding: 0 1.25rem 1rem;
	}

	.email-metrics article {
		border: 1px solid var(--border-color, #d8e0ea);
		border-radius: 8px;
		padding: 0.85rem;
		display: grid;
		gap: 0.15rem;
	}

	.email-metrics strong {
		font-size: 1.45rem;
	}

	.email-metrics span {
		color: var(--muted-ink-color, #667085);
		font-size: 0.82rem;
	}

	.email-section {
		margin: 0 1.25rem 1rem;
		padding: 1rem;
		border: 1px solid var(--border-color, #d8e0ea);
		border-radius: 8px;
	}

	.email-section.compact {
		padding-bottom: 0.85rem;
	}

	.section-heading {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 0.75rem;
	}

	.section-heading span {
		color: var(--muted-ink-color, #667085);
		font-size: 0.85rem;
	}

	.email-issue-list {
		display: grid;
		gap: 0.7rem;
	}

	.email-issue-list article {
		display: grid;
		gap: 0.35rem;
		padding: 0 0 0.7rem;
		border-bottom: 1px solid var(--border-color, #d8e0ea);
	}

	.email-issue-list article:last-child {
		border-bottom: 0;
		padding-bottom: 0;
	}

	.email-issue-list div,
	.email-footer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
	}

	.email-issue-list a,
	.issue-key a {
		color: var(--accent-color, #2f6fed);
		font-weight: 900;
		text-decoration: none;
	}

	.email-issue-list div span,
	.issue-key span {
		border-radius: 999px;
		padding: 0.22rem 0.55rem;
		background: color-mix(in srgb, var(--positive-color, #087f5b) 12%, #fff);
		color: var(--positive-color, #087f5b);
		font-size: 0.78rem;
		font-weight: 850;
	}

	.status-pills {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.status-pills span {
		border-radius: 999px;
		padding: 0.42rem 0.65rem;
		background: var(--soft-panel, #edf3f8);
		color: var(--muted-ink-color, #667085);
		display: inline-flex;
		gap: 0.35rem;
		align-items: center;
		font-size: 0.85rem;
	}

	.status-pills strong {
		color: var(--ink-color, #162033);
	}

	.email-footer {
		padding: 1rem 1.25rem 1.25rem;
		background: color-mix(in srgb, var(--soft-panel, #edf3f8) 70%, #fff);
	}

	.email-footer a {
		min-height: 36px;
		background: var(--accent-color, #2f6fed);
	}

	.preview-empty {
		min-height: 190px;
		display: grid;
		place-items: center;
		align-content: center;
		gap: 0.65rem;
		color: var(--muted-ink-color, #667085);
		text-align: center;
	}

	.detail-panel {
		padding: 1rem;
		display: grid;
		gap: 1rem;
	}

	.detail-head {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(260px, 380px);
		gap: 1rem;
		align-items: end;
	}

	.detail-head h2 {
		margin-top: 0.25rem;
		font-size: 1.25rem;
	}

	.detail-metrics {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.5rem;
	}

	.detail-metrics article {
		border-radius: 8px;
		background: var(--soft-panel, #edf3f8);
		padding: 0.75rem;
		display: grid;
		gap: 0.12rem;
	}

	.detail-metrics span {
		color: var(--muted-ink-color, #667085);
		font-size: 0.78rem;
	}

	.issue-list {
		display: grid;
		gap: 0.65rem;
	}

	.issue-list article {
		display: grid;
		grid-template-columns: 110px minmax(0, 1fr) auto;
		gap: 0.85rem;
		align-items: start;
		border: 1px solid var(--border-color, #d8e0ea);
		border-left: 4px solid var(--accent-color, #2f6fed);
		border-radius: 8px;
		padding: 0.85rem;
		background: var(--panel-background, #ffffff);
	}

	.issue-list article.new {
		border-left-color: var(--warning-color, #c77610);
	}

	.issue-key {
		display: grid;
		gap: 0.35rem;
		justify-items: start;
	}

	.issue-list em {
		border-radius: 999px;
		background: var(--soft-panel, #edf3f8);
		padding: 0.28rem 0.6rem;
		font-style: normal;
		font-weight: 850;
		white-space: nowrap;
	}

	.big {
		min-height: 220px;
		display: grid;
		place-items: center;
	}

	.snapshot-app {
		min-height: 100vh;
		padding: 1.5rem;
		display: grid;
		place-items: start center;
		background: var(--page-background, #f3f6fb);
	}

	.snapshot-app .email-paper {
		box-shadow: none;
	}

	@media (max-width: 1120px) {
		.workspace { grid-template-columns: 1fr; }
		.rail { grid-template-columns: repeat(2, minmax(0, 1fr)); }
		.history-block { grid-column: 1 / -1; }
		.topbar,
		.detail-head {
			grid-template-columns: 1fr;
			flex-direction: column;
			align-items: stretch;
		}
		.top-actions { justify-content: space-between; }
		.top-actions > div { text-align: left; }
	}

	@media (max-width: 760px) {
		.app { padding: 0.7rem; }
		.rail,
		.email-hero,
		.email-metrics,
		.detail-metrics,
		.issue-list article {
			grid-template-columns: 1fr;
		}
		.score {
			aspect-ratio: auto;
			min-height: 86px;
		}
		.email-footer,
		.email-issue-list div,
		.section-heading,
		.top-actions {
			align-items: stretch;
			flex-direction: column;
		}
		.email-paper { border-radius: 8px; }
		.snapshot-app { padding: 0.75rem; }
	}
</style>
