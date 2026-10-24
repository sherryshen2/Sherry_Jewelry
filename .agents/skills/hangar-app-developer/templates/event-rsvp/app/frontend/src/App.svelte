<script>
	// @ts-nocheck
	import Icon from '@iconify/svelte'
	import content from '$content'
	import data from '$data'
	import { api, auth, language } from '$hangarkit'

	let events = $state([])
	let guests = $state([])
	let loading = $state(true)
	let mode = $state('manage')
	let route_event = $state('')
	let route_email = $state('')
	let selected_event_id = $state('')
	let copied_link = $state('')
	let draft_message = $state('')
	let busy = $state(false)
	let hydrated_key = ''
	let language_id = $state('en')
	let current_user = $state(null)

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

	let new_event = $state({
		name: '',
		event_date: '',
		event_time: '',
		location: '',
		tagline: '',
		description: '',
		host_email: ''
	})

	let invite_email = $state('')
	let invite_name = $state('')
	let respondent = $state({
		status: 'attending',
		guests_count: 1,
		dietary: '',
		message: ''
	})

	data.events.subscribe((items) => {
		events = [...items].sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
		loading = false
	})

	data.guests.subscribe((items) => {
		guests = [...items].sort((a, b) =>
			String(b.responded_at || b.created_at || '').localeCompare(String(a.responded_at || a.created_at || ''))
		)
	})

	$effect(() => {
		if (typeof window === 'undefined') return
		const params = new URL(window.location.href).searchParams
		route_event = params.get('event') || params.get('event_name') || ''
		route_email = params.get('email') || ''
		mode = route_event ? 'respond' : 'manage'
	})

	$effect(() => {
		if (!selected_event_id && events.length) selected_event_id = events[0].id
	})

	let response_event = $derived(
		events.find((event) => event.slug === route_event || event.id === route_event || event.name === route_event)
	)
	let manager_event = $derived(events.find((event) => event.id === selected_event_id) || events[0])
	let active_event = $derived(mode === 'respond' ? response_event : manager_event)
	let event_guests = $derived(
		active_event ? guests.filter((guest) => guest.event_id === active_event.id || guest.event_slug === active_event.slug) : []
	)
	let respondent_identity = $derived({
		email: current_user?.email || route_email || '',
		name: current_user?.name || current_user?.email?.split('@')[0] || route_email?.split('@')[0] || ''
	})
	let existing_response = $derived(
		active_event && respondent_identity.email
			? event_guests.find((guest) => lower(guest.email) === lower(respondent_identity.email))
			: null
	)
	let going_count = $derived(
		event_guests
			.filter((guest) => guest.status === 'attending')
			.reduce((sum, guest) => sum + Number(guest.guests_count || 1), 0)
	)
	let maybe_count = $derived(event_guests.filter((guest) => guest.status === 'maybe').length)
	let declined_count = $derived(event_guests.filter((guest) => guest.status === 'declined').length)
	let invited_count = $derived(event_guests.filter((guest) => guest.status === 'invited').length)

	$effect(() => {
		if (!active_event) return
		const key = `${active_event.id}:${respondent_identity.email}:${existing_response?.id || 'new'}`
		if (key === hydrated_key) return
		hydrated_key = key
		if (existing_response) {
			respondent = {
				status: existing_response.status === 'invited' ? 'attending' : existing_response.status || 'attending',
				guests_count: Number(existing_response.guests_count || 1) || 1,
				dietary: existing_response.dietary || '',
				message: existing_response.message || ''
			}
		}
	})

	function lower(value) {
		return String(value || '').trim().toLowerCase()
	}

	function slugify(value) {
		return String(value || 'event')
			.toLowerCase()
			.trim()
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/(^-|-$)/g, '')
			.slice(0, 64)
	}

	function public_link(event, email = '') {
		if (typeof window === 'undefined' || !event) return ''
		const url = new URL(window.location.href)
		url.search = ''
		url.searchParams.set('event', event.slug || event.id)
		if (email) url.searchParams.set('email', email)
		return url.toString()
	}

	async function copy_link(event, email = '') {
		const link = public_link(event, email)
		if (!link) return
		await navigator.clipboard?.writeText(link)
		copied_link = link
		setTimeout(() => {
			if (copied_link === link) copied_link = ''
		}, 2200)
	}

	async function create_event() {
		if (!new_event.name.trim()) return
		const now = new Date().toISOString()
		const slug = slugify(new_event.name)
		const created = await data.events.create({
			slug,
			name: new_event.name.trim(),
			event_type: t('default_event_type', 'RSVP') || "You're Invited",
			tagline: new_event.tagline.trim(),
			event_date: new_event.event_date,
			event_time: new_event.event_time,
			location: new_event.location.trim(),
			description: new_event.description.trim(),
			host_email: new_event.host_email.trim(),
			status: 'Draft',
			created_at: now
		})
		selected_event_id = created?.id || selected_event_id
		new_event = { name: '', event_date: '', event_time: '', location: '', tagline: '', description: '', host_email: '' }
	}

	async function add_invitee() {
		if (!manager_event || !invite_email.trim()) return
		await data.guests.create({
			event_id: manager_event.id,
			event_slug: manager_event.slug,
			name: invite_name.trim() || invite_email.split('@')[0],
			email: invite_email.trim(),
			status: 'invited',
			guests_count: 0,
			dietary: '',
			message: '',
			invited_at: new Date().toISOString(),
			responded_at: '',
			created_at: new Date().toISOString()
		})
		invite_name = ''
		invite_email = ''
	}

	async function update_event_status(event, status) {
		await data.events.update(event.id, { status })
	}

	async function submit_rsvp(event) {
		event.preventDefault()
		if (!active_event) return
		if (!respondent_identity.email) {
			draft_message = 'Please sign in to RSVP.'
			return
		}
		busy = true
		const payload = {
			event_id: active_event.id,
			event_slug: active_event.slug,
			name: respondent_identity.name,
			email: respondent_identity.email,
			status: respondent.status,
			guests_count: respondent.status === 'attending' ? Number(respondent.guests_count || 1) : 0,
			dietary: respondent.dietary.trim(),
			message: respondent.message.trim(),
			responded_at: new Date().toISOString(),
			created_at: existing_response?.created_at || new Date().toISOString()
		}
		if (existing_response) {
			await data.guests.update(existing_response.id, payload)
		} else {
			await data.guests.create(payload)
		}
		busy = false
		draft_message = t('thank_you_message', 'Your RSVP has been saved.')
	}

	async function email_invite(event, email = '') {
		if (!event) return
		const link = public_link(event, email)
		try {
			const result = await api.post('/share-draft', { kind: 'rsvp', event, email, link })
			draft_message = result.message || 'Invite draft prepared.'
			if (result.mailto && typeof window !== 'undefined') window.location.href = result.mailto
		} catch (error) {
			const subject = encodeURIComponent(`RSVP: ${event.name}`)
			const body = encodeURIComponent(`Please RSVP for ${event.name}:\n\n${link}`)
			if (typeof window !== 'undefined') window.location.href = `mailto:${email}?subject=${subject}&body=${body}`
		}
	}

	function status_icon(status) {
		if (status === 'attending') return 'lucide:check-circle'
		if (status === 'maybe') return 'lucide:help-circle'
		if (status === 'declined') return 'lucide:x-circle'
		return 'lucide:mail'
	}
</script>

{#if loading}
	<div class="page centered">
		<Icon icon="lucide:loader-2" class="spin" width={28} />
	</div>
{:else if mode === 'respond'}
	<div class="page respond-page">
		{#if !response_event}
			<section class="response-card">
				<Icon icon="lucide:calendar-x" width={34} />
				<h1>Event not found</h1>
				<p>Ask the host for a fresh RSVP link.</p>
			</section>
		{:else}
			<section class="response-card">
				<div class="event-badge">
					<Icon icon="lucide:calendar" width={18} />
					{response_event.event_type || t('default_event_type', 'RSVP')}
				</div>
				<h1>{response_event.name}</h1>
				<p class="tagline">{response_event.tagline}</p>

				<div class="detail-grid">
					<div><Icon icon="lucide:calendar-days" width={18} /><span>{response_event.event_date}</span></div>
					<div><Icon icon="lucide:clock" width={18} /><span>{response_event.event_time}</span></div>
					<div><Icon icon="lucide:map-pin" width={18} /><span>{response_event.location}</span></div>
				</div>

				{#if response_event.description}
					<p class="description">{response_event.description}</p>
				{/if}

				<form class="rsvp-form" onsubmit={submit_rsvp}>
					<h2>{t('respondent_title', 'Your RSVP')}</h2>
					<div class="identity-note">
						<Icon icon="lucide:user-check" width={16} />
						<span>{respondent_identity.email ? `Responding as ${respondent_identity.email}` : 'Sign in to RSVP'}</span>
					</div>
					<div class="segmented">
						<button type="button" class:selected={respondent.status === 'attending'} onclick={() => (respondent.status = 'attending')}>
							<Icon icon="lucide:check" width={16} /> Going
						</button>
						<button type="button" class:selected={respondent.status === 'maybe'} onclick={() => (respondent.status = 'maybe')}>
							<Icon icon="lucide:help-circle" width={16} /> Maybe
						</button>
						<button type="button" class:selected={respondent.status === 'declined'} onclick={() => (respondent.status = 'declined')}>
							<Icon icon="lucide:x" width={16} /> Decline
						</button>
					</div>
					{#if respondent.status === 'attending'}
						<div class="form-row">
							<label>
								Guest count
								<input type="number" min="1" max="10" bind:value={respondent.guests_count} />
							</label>
							<label>
								Dietary notes
								<input bind:value={respondent.dietary} placeholder="Vegetarian, allergies..." />
							</label>
						</div>
					{/if}
					<label>
						Message
						<textarea bind:value={respondent.message} rows="3" placeholder="Anything the host should know?"></textarea>
					</label>
					<button class="primary" type="submit" disabled={busy || !respondent_identity.email}>
						<span class:spin={busy}><Icon icon={busy ? 'lucide:loader-2' : 'lucide:send'} width={18} /></span>
						{existing_response ? 'Update RSVP' : 'Send RSVP'}
					</button>
				</form>
				{#if draft_message}
					<p class="notice">{draft_message}</p>
				{/if}
			</section>
		{/if}
	</div>
{:else}
	<div class="page manager-page">
		<header class="manager-header">
			<div>
				<p class="eyebrow">RSVP Manager</p>
				<h1>{t('manager_title', 'RSVP events')}</h1>
				<p>{t('manager_intro', 'Create events, share RSVP links, and review responses.')}</p>
			</div>
			<div class="header-actions">
				<button class="ghost" onclick={() => manager_event && copy_link(manager_event)}>
					<Icon icon="lucide:copy" width={16} /> {t('copy_link_label', 'Copy link')}
				</button>
				<button class="primary" onclick={() => email_invite(manager_event)}>
					<Icon icon="lucide:mail-plus" width={16} /> {t('email_draft_label', 'Prepare email')}
				</button>
			</div>
		</header>

		<main class="manager-grid">
			<aside class="event-list">
				<div class="panel-title">
					<h2>Events</h2>
					<span>{events.length}</span>
				</div>
				{#each events as event (event.id)}
					<button class="event-row" class:active={manager_event?.id === event.id} onclick={() => (selected_event_id = event.id)}>
						<span class="event-name">{event.name}</span>
						<span class="event-meta">{event.event_date || 'No date'} · {event.status}</span>
					</button>
				{/each}

				<form class="create-card" onsubmit={(event) => { event.preventDefault(); create_event() }}>
					<h3>New event</h3>
					<input bind:value={new_event.name} placeholder="Event name" required />
					<div class="form-row">
						<input type="date" bind:value={new_event.event_date} aria-label="Event date" />
						<input bind:value={new_event.event_time} placeholder="Time" />
					</div>
					<input bind:value={new_event.location} placeholder="Location" />
					<input bind:value={new_event.tagline} placeholder="Short tagline" />
					<textarea bind:value={new_event.description} rows="3" placeholder="Description"></textarea>
					<input type="email" bind:value={new_event.host_email} placeholder="Host email" />
					<button class="primary" type="submit"><Icon icon="lucide:plus" width={16} /> Create event</button>
				</form>
			</aside>

			{#if manager_event}
				<section class="workspace">
					<div class="workspace-head">
						<div>
							<div class="event-badge">{manager_event.event_type || t('default_event_type', 'RSVP')}</div>
							<h2>{manager_event.name}</h2>
							<p>{manager_event.tagline}</p>
						</div>
						<select value={manager_event.status} onchange={(event) => update_event_status(manager_event, event.currentTarget.value)}>
							<option>Draft</option>
							<option>Open</option>
							<option>Closed</option>
							<option>Archived</option>
						</select>
					</div>

					<div class="stats">
						<div><strong>{going_count}</strong><span>Going</span></div>
						<div><strong>{maybe_count}</strong><span>Maybe</span></div>
						<div><strong>{declined_count}</strong><span>Declined</span></div>
						<div><strong>{invited_count}</strong><span>Invited</span></div>
					</div>

					<div class="share-panel">
						<div>
							<label>Public link</label>
							<code>{public_link(manager_event)}</code>
						</div>
						<button class="ghost" onclick={() => copy_link(manager_event)}><Icon icon="lucide:copy" width={16} /> Copy</button>
					</div>

					<form class="invite-panel" onsubmit={(event) => { event.preventDefault(); add_invitee() }}>
						<input bind:value={invite_name} placeholder="Invitee name" />
						<input type="email" bind:value={invite_email} placeholder="invitee@example.com" required />
						<button class="primary" type="submit"><Icon icon="lucide:user-plus" width={16} /> Add invitee</button>
						<button class="ghost" type="button" onclick={() => email_invite(manager_event, invite_email)}>
							<Icon icon="lucide:mail" width={16} /> Draft email
						</button>
					</form>

					<div class="responses">
						<div class="panel-title">
							<h3>Responses</h3>
							<span>{event_guests.length}</span>
						</div>
						{#each event_guests as guest (guest.id)}
							<article class="guest-card">
								<div class="guest-main">
									<Icon icon={status_icon(guest.status)} width={20} />
									<div>
										<strong>{guest.name}</strong>
										<a href={'mailto:' + guest.email}>{guest.email}</a>
									</div>
								</div>
								<span class={'status ' + guest.status}>{guest.status}</span>
								<div class="guest-notes">
									{#if guest.guests_count}<span>{guest.guests_count} guest(s)</span>{/if}
									{#if guest.dietary}<span>{guest.dietary}</span>{/if}
									{#if guest.message}<span>{guest.message}</span>{/if}
								</div>
								<div class="card-actions">
									<button class="link-button" onclick={() => copy_link(manager_event, guest.email)}>Copy personal link</button>
									<button class="link-button" onclick={() => email_invite(manager_event, guest.email)}>Email</button>
								</div>
							</article>
						{:else}
							<p class="empty">No invitees yet. Add a respondent or share the public link.</p>
						{/each}
					</div>
				</section>
			{/if}
		</main>

		{#if copied_link || draft_message}
			<div class="toast">{copied_link ? 'Link copied' : draft_message}</div>
		{/if}
	</div>
{/if}

<style>
	:global(*) {
		box-sizing: border-box;
	}

	.page {
		min-height: 100vh;
		background: var(--page-background, #f4f2ee);
		color: var(--body-text, #334155);
		font-family: var(--body-font, Inter, system-ui, sans-serif);
		padding: 24px;
	}

	.centered,
	.respond-page {
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
	.event-badge {
		color: var(--accent-color, #256f7c);
		font-size: 0.78rem;
		font-weight: 800;
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

	.manager-header h1 {
		font-size: clamp(2rem, 5vw, 3.4rem);
		line-height: 1;
		margin-bottom: 10px;
	}

	.manager-header p,
	.workspace-head p,
	.tagline,
	.description {
		color: var(--secondary-text, #64748b);
	}

	.header-actions,
	.form-row,
	.invite-panel,
	.card-actions {
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
		font-weight: 800;
		white-space: nowrap;
	}

	.primary {
		background: var(--accent-color, #256f7c);
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

	.event-list,
	.workspace,
	.response-card {
		background: var(--surface-background, #fff);
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: var(--card-radius, 8px);
		box-shadow: 0 20px 50px rgba(23, 32, 51, 0.08);
	}

	.event-list,
	.workspace {
		padding: 16px;
	}

	.panel-title,
	.workspace-head,
	.share-panel,
	.guest-card {
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

	.event-row {
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

	.event-row.active,
	.event-row:hover {
		background: var(--panel-background, #f8fafc);
		border-color: var(--border-color, #d8e1ec);
	}

	.event-name {
		font-weight: 850;
		color: var(--heading-color, #172033);
	}

	.event-meta,
	.guest-card a,
	.guest-notes,
	.empty {
		color: var(--secondary-text, #64748b);
		font-size: 0.86rem;
	}

	.create-card {
		display: grid;
		gap: 10px;
		margin-top: 18px;
		padding-top: 16px;
		border-top: 1px solid var(--border-color, #d8e1ec);
	}

	.stats {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 10px;
		margin: 18px 0;
	}

	.stats div {
		background: var(--panel-background, #f8fafc);
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: var(--card-radius, 8px);
		padding: 14px;
	}

	.stats strong {
		display: block;
		color: var(--heading-color, #172033);
		font-size: 1.5rem;
	}

	.stats span {
		color: var(--secondary-text, #64748b);
		font-size: 0.8rem;
		font-weight: 700;
		text-transform: uppercase;
	}

	.share-panel,
	.invite-panel,
	.guest-card {
		background: var(--panel-background, #f8fafc);
		border: 1px solid var(--border-color, #d8e1ec);
		border-radius: var(--card-radius, 8px);
		padding: 12px;
		margin-bottom: 12px;
	}

	code {
		display: block;
		max-width: 100%;
		overflow: hidden;
		text-overflow: ellipsis;
		color: var(--accent-color, #256f7c);
	}

	.responses {
		margin-top: 18px;
	}

	.guest-card {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
	}

	.guest-main {
		display: flex;
		gap: 10px;
		align-items: center;
		min-width: 0;
	}

	.guest-main div {
		display: grid;
		min-width: 0;
	}

	.status {
		padding: 5px 9px;
		border-radius: 999px;
		background: #eef2ff;
		font-size: 0.75rem;
		font-weight: 800;
		text-transform: capitalize;
	}

	.status.attending {
		background: #dcfce7;
		color: var(--success-color, #268a5b);
	}

	.status.maybe {
		background: #fef3c7;
		color: var(--warning-color, #d09219);
	}

	.status.declined {
		background: #fee2e2;
		color: var(--error-color, #c2414b);
	}

	.guest-notes,
	.card-actions {
		grid-column: 1 / -1;
	}

	.link-button {
		background: transparent;
		color: var(--accent-color, #256f7c);
		padding: 0;
		font-weight: 800;
	}

	.response-card {
		width: min(100%, 620px);
		padding: 28px;
	}

	.response-card h1 {
		font-size: clamp(2rem, 7vw, 4rem);
		line-height: 0.98;
		margin: 8px 0 10px;
	}

	.detail-grid {
		display: grid;
		gap: 10px;
		margin: 18px 0;
	}

	.detail-grid div {
		display: flex;
		gap: 10px;
		align-items: center;
		background: var(--panel-background, #f8fafc);
		border-radius: var(--control-radius, 6px);
		padding: 10px 12px;
	}

	.rsvp-form {
		display: grid;
		gap: 12px;
		margin-top: 20px;
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

	label {
		display: grid;
		gap: 6px;
		color: var(--heading-color, #172033);
		font-size: 0.86rem;
		font-weight: 800;
	}

	.segmented {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 8px;
	}

	.segmented button {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		background: #fff;
		border: 1px solid var(--border-color, #d8e1ec);
		padding: 12px;
	}

	.segmented button.selected {
		background: var(--accent-color, #256f7c);
		color: #fff;
		border-color: var(--accent-color, #256f7c);
	}

	.notice,
	.toast {
		background: #ecfdf5;
		color: var(--success-color, #268a5b);
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
		.form-row,
		.invite-panel {
			display: grid;
			grid-template-columns: 1fr;
		}

		.stats,
		.segmented {
			grid-template-columns: 1fr;
		}
	}
</style>
