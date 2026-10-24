<script lang="ts">
	// @ts-nocheck
	import { onMount } from 'svelte'
	import { fly } from 'svelte/transition'
	import Icon from '@iconify/svelte'
	import content from '$content'
	import data from '$data'
	import { auth, language } from '$hangarkit'

	type ChecklistTask = {
		key: string
		title: string
		description: string
		stage: string
		stage_icon: string
		duration: string
		owner: string
		sort_order: number
	}

	type ProgressRecord = {
		id: string
		task_key: string
		done: boolean
		completed_at?: string
		updated_at?: string
	}

	const fallback_items = [
		{
			stage: 'Before day one',
			icon: 'lucide:calendar-check',
			items: [
				{
					key: 'profile-paperwork',
					title: 'Complete employee profile and paperwork',
					description: 'Fill in required HR details, emergency contacts, payroll setup, and policy acknowledgements.',
					duration: '20 min',
					owner: 'People team'
				},
				{
					key: 'workspace-access',
					title: 'Confirm workspace and system access',
					description: 'Check email, chat, calendar, VPN, password manager, and core team tools before your first meeting.',
					duration: '15 min',
					owner: 'IT'
				}
			]
		}
	]

	let progress_records = $state<ProgressRecord[]>([])
	let loading = $state(true)
	let language_id = $state('en')
	let user_label = $state('')
	let active_stage = $state('all')
	let saving_key = $state('')
	let toast_key = $state('')
	let save_error = $state('')

	data.onboarding_progress.subscribe((records: ProgressRecord[]) => {
		progress_records = records || []
		loading = false
	})

	let progress_by_key = $derived.by(() => {
		return new Map(progress_records.map((record) => [record.task_key, record]))
	})

	let localized = $derived.by(() => {
		const dictionary = content.localized_copy || {}
		return dictionary[language_id] || dictionary.en || {}
	})
	let checklist = $derived.by(() => normalize_checklist(localized.checklist_items || content.checklist_items || fallback_items))

	let stages = $derived.by(() => {
		const by_stage = new Map()
		for (const task of checklist) {
			if (!by_stage.has(task.stage)) {
				by_stage.set(task.stage, {
					name: task.stage,
					icon: task.stage_icon,
					total: 0,
					done: 0
				})
			}
			const stage = by_stage.get(task.stage)
			stage.total += 1
			if (is_done(task)) stage.done += 1
		}
		return [...by_stage.values()]
	})

	let visible_tasks = $derived.by(() => {
		if (active_stage === 'all') return checklist
		return checklist.filter((task) => task.stage === active_stage)
	})

	let completed_count = $derived.by(() => checklist.filter((task) => is_done(task)).length)
	let total_count = $derived(checklist.length)
	let progress_percent = $derived(total_count ? Math.round((completed_count / total_count) * 100) : 0)
	let next_task = $derived.by(() => checklist.find((task) => !is_done(task)))
	let is_finished = $derived(total_count > 0 && completed_count === total_count)

	onMount(() => {
		const stop_language = language.subscribe((value) => {
			language_id = value.id
		})
		void load_user()
		return () => stop_language()
	})

	function copy(key: string, fallback = '') {
		return localized?.[key] || content[key] || fallback
	}

	async function load_user() {
		try {
			const user = await auth.currentUser()
			user_label = user?.name || user?.email || copy('signed_in_label', 'New teammate')
		} catch {
			user_label = copy('signed_in_label', 'New teammate')
		}
	}

	function normalize_checklist(input: any): ChecklistTask[] {
		const source = Array.isArray(input) ? input : fallback_items
		const tasks: ChecklistTask[] = []

		source.forEach((entry, section_index) => {
			const stage = String(entry?.stage || entry?.group || 'Getting started')
			const stage_icon = String(entry?.icon || 'lucide:circle-dot')
			const items = Array.isArray(entry?.items) ? entry.items : [entry]

			items.forEach((item, item_index) => {
				const title = String(item?.title || '').trim()
				if (!title) return
				const key = String(item?.key || `${slugify(stage)}-${slugify(title) || item_index}`).trim()
				tasks.push({
					key,
					title,
					description: String(item?.description || ''),
					stage,
					stage_icon,
					duration: String(item?.duration || ''),
					owner: String(item?.owner || ''),
					sort_order: Number(item?.sort_order ?? section_index * 100 + item_index)
				})
			})
		})

		return tasks.sort((a, b) => a.sort_order - b.sort_order)
	}

	function slugify(value: string) {
		return value
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/^-|-$/g, '')
	}

	function is_done(task: ChecklistTask) {
		return Boolean(progress_by_key.get(task.key)?.done)
	}

	async function toggle_task(task: ChecklistTask) {
		const existing = progress_by_key.get(task.key)
		const done = !existing?.done
		const now = new Date().toISOString()
		const patch = {
			task_key: task.key,
			done,
			completed_at: done ? now : '',
			updated_at: now
		}

		saving_key = task.key
		save_error = ''

		try {
			let saved
			if (existing) {
				saved = await data.onboarding_progress.update(existing.id, patch)
				progress_records = progress_records.map((record) => (record.id === existing.id ? saved : record))
			} else {
				saved = await data.onboarding_progress.create({
					...patch,
					_schema: [
						{ name: 'task_key', type: 'text', required: true },
						{ name: 'done', type: 'boolean', default: false },
						{ name: 'completed_at', type: 'date' },
						{ name: 'updated_at', type: 'date' }
					]
				})
				progress_records = [saved, ...progress_records]
			}

			if (done) {
				toast_key = task.key
				setTimeout(() => {
					if (toast_key === task.key) toast_key = ''
				}, 1800)
			}
		} catch {
			save_error = copy('save_error', 'Could not save progress. Please try again.')
		} finally {
			saving_key = ''
		}
	}

	async function reset_progress() {
		saving_key = 'reset'
		save_error = ''

		try {
			const updates = progress_records
				.filter((record) => record.done)
				.map((record) =>
					data.onboarding_progress.update(record.id, {
						done: false,
						completed_at: '',
						updated_at: new Date().toISOString()
					})
				)
			const saved = await Promise.all(updates)
			const saved_by_id = new Map(saved.map((record) => [record.id, record]))
			progress_records = progress_records.map((record) => saved_by_id.get(record.id) || record)
		} catch {
			save_error = copy('reset_error', 'Could not reset progress. Please try again.')
		} finally {
			saving_key = ''
		}
	}
</script>

<main class="page">
	<section class="surface" aria-label={copy('app_aria', 'Employee onboarding checklist')}>
		<header class="hero">
			<div class="hero-copy">
				<p class="eyebrow">{copy('eyebrow')}</p>
				<h1>{copy('app_title', '__HANGAR_APP_NAME__')}</h1>
				<p class="lede">{copy('welcome_text')}</p>
			</div>

			<div class="progress-card" aria-label={copy('progress_label')}>
				<div class="avatar-ring" style={`--progress: ${progress_percent}%`}>
					<span>{progress_percent}%</span>
				</div>
				<div>
					<p>{copy('progress_label')}</p>
					<strong>{completed_count}/{total_count} {copy('complete_label')}</strong>
					<small>{user_label}</small>
				</div>
			</div>
		</header>

		<section class="progress-strip" aria-label={copy('progress_label')}>
			<div class="progress-topline">
				<span>{copy('progress_label')}</span>
				<span>{progress_percent}% {copy('complete_label')}</span>
			</div>
			<div class="progress-track">
				<div class="progress-fill" style={`width: ${progress_percent}%`}></div>
			</div>
		</section>

		<section class="stage-bar" aria-label={copy('stages_aria', 'Checklist stages')}>
			<button class:active={active_stage === 'all'} type="button" onclick={() => (active_stage = 'all')}>
				<Icon icon="lucide:list-checks" width={16} />
				<span>{copy('all_stages_label')}</span>
				<small>{completed_count}/{total_count}</small>
			</button>
			{#each stages as stage (stage.name)}
				<button class:active={active_stage === stage.name} type="button" onclick={() => (active_stage = stage.name)}>
					<Icon icon={stage.icon} width={16} />
					<span>{stage.name}</span>
					<small>{stage.done}/{stage.total}</small>
				</button>
			{/each}
		</section>

		{#if is_finished}
			<section class="completion-banner" transition:fly={{ y: 12, duration: 240 }}>
				<Icon icon="lucide:party-popper" width={24} />
				<div>
					<h2>{copy('finished_title')}</h2>
					<p>{copy('finished_text')}</p>
				</div>
			</section>
		{:else if next_task}
			<section class="next-panel" transition:fly={{ y: 12, duration: 240 }}>
				<p>{copy('next_step_label')}</p>
				<strong>{next_task.title}</strong>
				<span>{next_task.stage}</span>
			</section>
		{/if}

		{#if save_error}
			<p class="error-status">{save_error}</p>
		{/if}

		<section class="checklist-shell">
			{#if loading}
				<p class="status">{copy('loading_message')}</p>
			{:else if checklist.length === 0}
				<p class="status">{copy('empty_state')}</p>
			{:else}
				<div class="task-list">
					{#each visible_tasks as task, index (task.key)}
						<article class:done={is_done(task)} class="task-row" style={`--row-index: ${index}`} transition:fly={{ y: 10, duration: 180 }}>
							<button
								class="check-button"
								type="button"
								aria-label={task.title}
								aria-pressed={is_done(task)}
								disabled={saving_key === task.key}
								onclick={() => void toggle_task(task)}
							>
								{#if saving_key === task.key}
									<Icon icon="lucide:loader-2" width={18} class="spin" />
								{:else if is_done(task)}
									<Icon icon="lucide:check" width={18} />
								{:else}
									<Icon icon="lucide:circle" width={18} />
								{/if}
							</button>

							<div class="task-content">
								<div class="task-heading">
									<span class="stage-pill">
										<Icon icon={task.stage_icon} width={14} />
										{task.stage}
									</span>
									{#if task.duration}<span>{task.duration}</span>{/if}
									{#if task.owner}<span>{task.owner}</span>{/if}
								</div>
								<h2>{task.title}</h2>
								{#if task.description}<p>{task.description}</p>{/if}
							</div>

							{#if toast_key === task.key}
								<div class="toast" transition:fly={{ x: 8, duration: 160 }}>
									<Icon icon="lucide:sparkles" width={15} />
									{copy('completion_toast')}
								</div>
							{/if}
						</article>
					{/each}
				</div>
			{/if}
		</section>

		<footer class="footer">
			<p>{copy('footer_note')}</p>
			<button type="button" disabled={saving_key === 'reset' || completed_count === 0} onclick={() => void reset_progress()}>
				{#if saving_key === 'reset'}
					<Icon icon="lucide:loader-2" width={16} class="spin" />
				{:else}
					<Icon icon="lucide:rotate-ccw" width={16} />
				{/if}
				<span>{copy('reset_button')}</span>
			</button>
		</footer>
	</section>
</main>

<style>
	:global(*) {
		box-sizing: border-box;
	}

	:global(body) {
		margin: 0;
		font-family: var(--font-family, Inter, ui-sans-serif, system-ui, sans-serif);
		color: var(--ink-color, #17211f);
		background:
			radial-gradient(circle at 12% 8%, rgba(228, 87, 46, 0.12), transparent 30rem),
			linear-gradient(135deg, var(--page-background, #f4f7f2), #eef5f8);
	}

	button {
		font: inherit;
	}

	.page {
		min-height: 100vh;
		padding: var(--page-padding, 1.5rem);
		display: grid;
		place-items: start center;
	}

	.surface {
		width: min(1120px, 100%);
		display: grid;
		gap: 1rem;
		padding: clamp(1rem, 3vw, 1.75rem);
		border: 1px solid color-mix(in srgb, var(--border-color, #d9e2dc), transparent 10%);
		border-radius: var(--surface-radius, 8px);
		background: color-mix(in srgb, var(--surface-background, #ffffff), transparent 3%);
		box-shadow: var(--surface-shadow, 0 22px 70px rgba(31, 55, 48, 0.12));
		animation: surface-in 480ms ease-out both;
	}

	.hero {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(260px, 340px);
		gap: 1rem;
		align-items: stretch;
	}

	.hero-copy,
	.progress-card,
	.progress-strip,
	.next-panel,
	.completion-banner,
	.checklist-shell,
	.footer {
		border: 1px solid var(--border-color, #d9e2dc);
		border-radius: var(--surface-radius, 8px);
		background: var(--surface-background, #ffffff);
	}

	.hero-copy {
		min-height: 260px;
		padding: clamp(1.25rem, 4vw, 3rem);
		display: grid;
		align-content: end;
		position: relative;
		overflow: hidden;
	}

	.hero-copy::before {
		content: '';
		position: absolute;
		inset: 1rem 1rem auto auto;
		width: min(34vw, 320px);
		aspect-ratio: 1;
		border-radius: 999px;
		background:
			linear-gradient(135deg, color-mix(in srgb, var(--accent-color, #1f7a6b), transparent 20%), transparent 65%),
			color-mix(in srgb, var(--warm-accent-color, #e4572e), transparent 76%);
		filter: blur(1px);
		opacity: 0.65;
		transform: translate(24%, -32%);
	}

	.eyebrow,
	.progress-topline,
	.next-panel p,
	.task-heading,
	.footer p {
		margin: 0;
		color: var(--muted-ink-color, #60706a);
		font-size: 0.76rem;
		font-weight: 700;
		letter-spacing: 0;
		text-transform: uppercase;
	}

	h1,
	h2,
	p {
		margin: 0;
	}

	h1 {
		max-width: 760px;
		position: relative;
		font-size: clamp(2.4rem, 6vw, 5.2rem);
		line-height: 0.96;
		letter-spacing: 0;
	}

	.lede {
		max-width: 680px;
		position: relative;
		margin-top: 1rem;
		color: var(--muted-ink-color, #60706a);
		font-size: clamp(1rem, 2vw, 1.2rem);
		line-height: 1.6;
	}

	.progress-card {
		padding: 1.25rem;
		display: grid;
		align-content: end;
		gap: 1rem;
		background:
			linear-gradient(145deg, color-mix(in srgb, var(--ink-color, #17211f), #ffffff 6%), var(--accent-color, #1f7a6b));
		color: var(--button-text-color, #ffffff);
		overflow: hidden;
		position: relative;
	}

	.progress-card::after {
		content: '';
		position: absolute;
		inset: auto -18% -34% auto;
		width: 220px;
		aspect-ratio: 1;
		border-radius: 999px;
		background: color-mix(in srgb, var(--warm-accent-color, #e4572e), transparent 18%);
	}

	.avatar-ring {
		width: 132px;
		aspect-ratio: 1;
		display: grid;
		place-items: center;
		border-radius: 999px;
		background:
			radial-gradient(circle at center, var(--accent-color, #1f7a6b) 56%, transparent 57%),
			conic-gradient(var(--button-text-color, #ffffff) var(--progress, 0%), rgba(255, 255, 255, 0.25) 0);
		border: 1px solid rgba(255, 255, 255, 0.28);
		animation: breathe 3.4s ease-in-out infinite;
	}

	.avatar-ring span {
		font-size: 2rem;
		font-weight: 800;
	}

	.progress-card p,
	.progress-card small {
		color: rgba(255, 255, 255, 0.78);
	}

	.progress-card strong {
		display: block;
		margin: 0.25rem 0;
		font-size: 1.6rem;
		line-height: 1.1;
	}

	.progress-strip {
		padding: 1rem;
		display: grid;
		gap: 0.7rem;
	}

	.progress-topline {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
	}

	.progress-track {
		height: 0.65rem;
		border-radius: 999px;
		background: var(--panel-background, #f8fafb);
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		border-radius: inherit;
		background: linear-gradient(90deg, var(--accent-color, #1f7a6b), var(--warm-accent-color, #e4572e));
		transition: width 420ms cubic-bezier(0.2, 0.8, 0.2, 1);
		position: relative;
	}

	.progress-fill::after {
		content: '';
		position: absolute;
		inset: 0;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.38), transparent);
		animation: shine 1.9s linear infinite;
	}

	.stage-bar {
		display: flex;
		gap: 0.6rem;
		overflow-x: auto;
		padding-bottom: 0.15rem;
	}

	.stage-bar button,
	.footer button {
		min-height: 2.55rem;
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		border: 1px solid var(--border-color, #d9e2dc);
		border-radius: var(--control-radius, 6px);
		background: var(--surface-background, #ffffff);
		color: var(--ink-color, #17211f);
		cursor: pointer;
		transition:
			transform 160ms ease,
			border-color 160ms ease,
			background 160ms ease;
	}

	.stage-bar button {
		flex: 0 0 auto;
		padding: 0.65rem 0.8rem;
	}

	.stage-bar button:hover,
	.footer button:hover:not(:disabled) {
		transform: translateY(-1px);
		border-color: var(--accent-color, #1f7a6b);
	}

	.stage-bar button.active {
		background: var(--soft-accent-color, #e1f2ec);
		border-color: color-mix(in srgb, var(--accent-color, #1f7a6b), transparent 35%);
		color: var(--accent-color, #1f7a6b);
	}

	.stage-bar small {
		color: var(--muted-ink-color, #60706a);
	}

	.next-panel,
	.completion-banner {
		padding: 1rem;
		display: flex;
		align-items: center;
		gap: 0.85rem;
		background: var(--panel-background, #f8fafb);
	}

	.next-panel {
		justify-content: space-between;
		flex-wrap: wrap;
	}

	.next-panel strong {
		font-size: 1rem;
	}

	.next-panel span {
		color: var(--muted-ink-color, #60706a);
	}

	.completion-banner {
		border-color: color-mix(in srgb, var(--success-color, #2f9d62), transparent 45%);
		background: color-mix(in srgb, var(--success-color, #2f9d62), white 88%);
	}

	.completion-banner h2 {
		font-size: 1.1rem;
	}

	.completion-banner p {
		margin-top: 0.25rem;
		color: var(--muted-ink-color, #60706a);
	}

	.error-status,
	.status {
		margin: 0;
		padding: 1rem;
		border-radius: var(--control-radius, 6px);
		background: var(--panel-background, #f8fafb);
		color: var(--muted-ink-color, #60706a);
	}

	.error-status {
		background: color-mix(in srgb, var(--warm-accent-color, #e4572e), white 88%);
		color: color-mix(in srgb, var(--warm-accent-color, #e4572e), black 22%);
	}

	.checklist-shell {
		padding: 0.75rem;
	}

	.task-list {
		display: grid;
		gap: 0.65rem;
	}

	.task-row {
		position: relative;
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) auto;
		gap: 0.85rem;
		align-items: center;
		padding: 1rem;
		border: 1px solid var(--border-color, #d9e2dc);
		border-radius: var(--control-radius, 6px);
		background: var(--surface-background, #ffffff);
		transition:
			transform 180ms ease,
			border-color 180ms ease,
			background 180ms ease,
			box-shadow 180ms ease;
		animation: row-in 360ms ease-out both;
		animation-delay: calc(var(--row-index) * 35ms);
	}

	.task-row:hover {
		transform: translateY(-2px);
		border-color: color-mix(in srgb, var(--accent-color, #1f7a6b), transparent 40%);
		box-shadow: 0 12px 26px rgba(31, 55, 48, 0.08);
	}

	.task-row.done {
		background: color-mix(in srgb, var(--soft-accent-color, #e1f2ec), white 46%);
	}

	.check-button {
		width: 2.35rem;
		aspect-ratio: 1;
		display: grid;
		place-items: center;
		border: 1px solid var(--border-color, #d9e2dc);
		border-radius: 999px;
		background: var(--surface-background, #ffffff);
		color: var(--muted-ink-color, #60706a);
		cursor: pointer;
		transition:
			background 180ms ease,
			color 180ms ease,
			transform 180ms ease;
	}

	.task-row.done .check-button {
		background: var(--success-color, #2f9d62);
		color: var(--button-text-color, #ffffff);
		border-color: var(--success-color, #2f9d62);
	}

	.check-button:hover:not(:disabled) {
		transform: scale(1.06);
	}

	.check-button:disabled {
		cursor: wait;
		opacity: 0.7;
	}

	.task-content {
		display: grid;
		gap: 0.45rem;
		min-width: 0;
	}

	.task-heading {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.5rem;
		text-transform: none;
	}

	.stage-pill {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		color: var(--accent-color, #1f7a6b);
	}

	.task-content h2 {
		font-size: clamp(1rem, 2vw, 1.18rem);
		line-height: 1.25;
	}

	.task-row.done h2 {
		text-decoration: line-through;
		text-decoration-thickness: 2px;
		text-decoration-color: color-mix(in srgb, var(--success-color, #2f9d62), transparent 20%);
	}

	.task-content p {
		color: var(--muted-ink-color, #60706a);
		line-height: 1.55;
	}

	.toast {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.45rem 0.6rem;
		border-radius: 999px;
		background: var(--ink-color, #17211f);
		color: var(--button-text-color, #ffffff);
		font-size: 0.78rem;
		font-weight: 700;
		white-space: nowrap;
	}

	.footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
	}

	.footer p {
		text-transform: none;
		font-weight: 600;
	}

	.footer button {
		padding: 0.6rem 0.8rem;
	}

	.footer button:disabled {
		opacity: 0.55;
		cursor: not-allowed;
	}

	:global(.spin) {
		animation: spin 0.8s linear infinite;
	}

	@keyframes surface-in {
		from {
			opacity: 0;
			transform: translateY(12px) scale(0.99);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}

	@keyframes row-in {
		from {
			opacity: 0;
			transform: translateY(8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@keyframes shine {
		from {
			transform: translateX(-100%);
		}
		to {
			transform: translateX(100%);
		}
	}

	@keyframes breathe {
		0%,
		100% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.025);
		}
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	@media (max-width: 820px) {
		.hero {
			grid-template-columns: 1fr;
		}

		.hero-copy {
			min-height: 230px;
		}

		.progress-card {
			grid-template-columns: auto minmax(0, 1fr);
			align-items: center;
		}

		.avatar-ring {
			width: 104px;
		}

		.task-row {
			grid-template-columns: auto minmax(0, 1fr);
		}

		.toast {
			grid-column: 2;
			justify-self: start;
		}
	}

	@media (max-width: 560px) {
		.page {
			padding: 0.65rem;
		}

		.surface {
			padding: 0.75rem;
		}

		.hero-copy {
			padding: 1.15rem;
		}

		.progress-card,
		.footer {
			flex-direction: column;
			align-items: stretch;
		}

		.footer {
			display: grid;
		}
	}
</style>
