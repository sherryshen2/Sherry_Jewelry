<script>
  // @ts-nocheck
	import Icon from '@iconify/svelte'
	import content from '$content'
	import data from '$data'
	import { language } from '$hangarkit'

	let cards = $state([])
	let loading = $state(true)
	let dragging_id = $state(null)
	let drag_over_column = $state(null)
	let adding_to_column = $state(null)
	let editing_card = $state(null)
	let expanded_card = $state(null)
	let language_id = $state('en')

	// Form state
	let form_title = $state('')
	let form_description = $state('')
	let form_priority = $state('medium')
	let form_label = $state('')
	let form_due_date = $state('')

	language.subscribe((value) => {
		language_id = value.id || 'en'
	})

	function t(key, fallback = '') {
		const packs = content.localized_copy || {}
		return packs[language_id]?.[key] || packs.en?.[key] || content[key] || fallback
	}

	const columns = $derived([
		{ id: 'todo', name: t('column_1_name', 'To Do'), icon: 'lucide:circle' },
		{ id: 'progress', name: t('column_2_name', 'In Progress'), icon: 'lucide:loader' },
		{ id: 'done', name: t('column_3_name', 'Done'), icon: 'lucide:check-circle' }
	])

	const labels = $derived([
		{ id: 'feature', name: t('feature', 'Feature'), color: '#8b5cf6' },
		{ id: 'bug', name: t('bug', 'Bug'), color: '#ef4444' },
		{ id: 'docs', name: t('docs', 'Docs'), color: '#3b82f6' },
		{ id: 'design', name: t('design', 'Design'), color: '#ec4899' },
		{ id: 'research', name: t('research', 'Research'), color: '#f59e0b' }
	])

	const priorities = $derived([
		{ id: 'low', name: t('low', 'Low'), icon: 'lucide:arrow-down', color: '#64748b' },
		{ id: 'medium', name: t('medium', 'Medium'), icon: 'lucide:minus', color: '#f59e0b' },
		{ id: 'high', name: t('high', 'High'), icon: 'lucide:arrow-up', color: '#ef4444' }
	])

	data.cards.subscribe(items => {
		cards = items
		loading = false
	})

	function get_column_cards(column_id) {
		return cards
			.filter(c => c.column === column_id)
			.sort((a, b) => (a.order || 0) - (b.order || 0))
	}

	function get_label(label_id) {
		return labels.find(l => l.id === label_id)
	}

	function get_priority(priority_id) {
		return priorities.find(p => p.id === priority_id) || priorities[1]
	}

	function is_overdue(due_date) {
		if (!due_date) return false
		return new Date(due_date) < new Date(new Date().toDateString())
	}

	function format_date(date_str) {
		if (!date_str) return ''
		const date = new Date(date_str)
		const today = new Date()
		const tomorrow = new Date(today)
		tomorrow.setDate(tomorrow.getDate() + 1)
		
		if (date.toDateString() === today.toDateString()) return t('today', 'Today')
		if (date.toDateString() === tomorrow.toDateString()) return t('tomorrow', 'Tomorrow')
		return date.toLocaleDateString(language_id === 'zh' ? 'zh-CN' : 'en-US', { month: 'short', day: 'numeric' })
	}

	function handle_drag_start(e, card) {
		dragging_id = card.id
		e.dataTransfer.effectAllowed = 'move'
	}

	function handle_drag_over(e, column_id) {
		e.preventDefault()
		drag_over_column = column_id
	}

	function handle_drag_leave() {
		drag_over_column = null
	}

	async function handle_drop(e, column_id) {
		e.preventDefault()
		drag_over_column = null
		
		if (dragging_id) {
			const column_cards = get_column_cards(column_id)
			const new_order = column_cards.length > 0 
				? Math.max(...column_cards.map(c => c.order || 0)) + 1 
				: 0
			await data.cards.update(dragging_id, { column: column_id, order: new_order })
			dragging_id = null
		}
	}

	function handle_drag_end() {
		dragging_id = null
		drag_over_column = null
	}

	function reset_form() {
		form_title = ''
		form_description = ''
		form_priority = 'medium'
		form_label = ''
		form_due_date = ''
	}

	function start_adding(column_id) {
		reset_form()
		adding_to_column = column_id
		editing_card = null
	}

	function start_editing(card) {
		form_title = card.title || ''
		form_description = card.description || ''
		form_priority = card.priority || 'medium'
		form_label = card.label || ''
		form_due_date = card.due_date || ''
		editing_card = card.id
		adding_to_column = null
		expanded_card = null
	}

	function cancel_form() {
		adding_to_column = null
		editing_card = null
		reset_form()
	}

	async function save_card(column_id) {
		if (!form_title.trim()) return
		
		if (editing_card) {
			await data.cards.update(editing_card, {
				title: form_title.trim(),
				description: form_description.trim(),
				priority: form_priority,
				label: form_label,
				due_date: form_due_date
			})
			editing_card = null
		} else {
			const column_cards = get_column_cards(column_id)
			const order = column_cards.length > 0 
				? Math.max(...column_cards.map(c => c.order || 0)) + 1 
				: 0
			await data.cards.create({
				title: form_title.trim(),
				description: form_description.trim(),
				priority: form_priority,
				label: form_label,
				due_date: form_due_date,
				column: column_id,
				order
			})
			adding_to_column = null
		}
		reset_form()
	}

	async function delete_card(id) {
		await data.cards.delete(id)
		expanded_card = null
	}

	function toggle_expand(card_id) {
		expanded_card = expanded_card === card_id ? null : card_id
	}

	function handle_keydown(e, column_id) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault()
			save_card(column_id)
		}
		if (e.key === 'Escape') cancel_form()
	}
</script>

<div class="page">
	<header class="header">
		<div class="header-content">
			<h1>{t('board_title', 'Project Board')}</h1>
			<p class="subtitle">{cards.length} {cards.length === 1 ? t('task_singular', 'task') : t('task_plural', 'tasks')}</p>
		</div>
	</header>

	<div class="board">
		{#each columns as column (column.id)}
			<div 
				class="column"
				class:drag-over={drag_over_column === column.id}
				ondragover={(e) => handle_drag_over(e, column.id)}
				ondragleave={handle_drag_leave}
				ondrop={(e) => handle_drop(e, column.id)}
			>
				<div class="column-header">
					<div class="column-title">
						<Icon icon={column.icon} width={16} />
						<h2>{column.name}</h2>
					</div>
					<span class="count">{get_column_cards(column.id).length}</span>
				</div>

				<div class="cards">
					{#if loading}
						<div class="loading">
							<Icon icon="lucide:loader-2" width={20} class="spin" />
							<span>{t('loading', 'Loading...')}</span>
						</div>
					{:else}
						{#each get_column_cards(column.id) as card (card.id)}
							{#if editing_card === card.id}
								<div class="card-form">
									<input
										type="text"
										bind:value={form_title}
										placeholder={t('task_title_placeholder', 'Task title...')}
										onkeydown={(e) => handle_keydown(e, card.column)}
										autofocus
									/>
									<textarea
										bind:value={form_description}
										placeholder={t('description_placeholder', 'Add description...')}
										rows="2"
									></textarea>
									<div class="form-row">
										<select bind:value={form_priority}>
											{#each priorities as p}
												<option value={p.id}>{p.name}</option>
											{/each}
										</select>
										<select bind:value={form_label}>
											<option value="">{t('no_label', 'No label')}</option>
											{#each labels as l}
												<option value={l.id}>{l.name}</option>
											{/each}
										</select>
									</div>
									<input type="date" bind:value={form_due_date} />
									<div class="form-actions">
										<button class="save-btn" onclick={() => save_card(card.column)}>{t('save', 'Save')}</button>
										<button class="cancel-btn" onclick={cancel_form}>{t('cancel', 'Cancel')}</button>
									</div>
								</div>
							{:else}
								<div
									class="card"
									class:dragging={dragging_id === card.id}
									class:expanded={expanded_card === card.id}
									draggable="true"
									ondragstart={(e) => handle_drag_start(e, card)}
									ondragend={handle_drag_end}
								>
									{#if card.label}
										{@const label = get_label(card.label)}
										{#if label}
											<span class="card-label" style="background: {label.color}">{label.name}</span>
										{/if}
									{/if}
									<div class="card-main">
										<span class="card-title" onclick={() => toggle_expand(card.id)}>{card.title}</span>
										<div class="card-actions">
											<button class="action-btn" onclick={() => start_editing(card)} title="Edit">
												<Icon icon="lucide:pencil" width={14} />
											</button>
											<button class="action-btn delete" onclick={() => delete_card(card.id)} title="Delete">
												<Icon icon="lucide:trash-2" width={14} />
											</button>
										</div>
									</div>
									{#if card.description && expanded_card === card.id}
										<p class="card-description">{card.description}</p>
									{/if}
									<div class="card-meta">
										<span class="priority" style="color: {get_priority(card.priority).color}" title="{get_priority(card.priority).name} priority">
											<Icon icon={get_priority(card.priority).icon} width={14} />
										</span>
										{#if card.due_date}
											<span class="due-date" class:overdue={is_overdue(card.due_date)}>
												<Icon icon="lucide:calendar" width={12} />
												{format_date(card.due_date)}
											</span>
										{/if}
										{#if card.description}
											<span class="has-description" title="Has description">
												<Icon icon="lucide:align-left" width={12} />
											</span>
										{/if}
									</div>
								</div>
							{/if}
						{:else}
							{#if !adding_to_column}
								<div class="empty-column">
									<Icon icon="lucide:inbox" width={24} />
									<span>{t('no_tasks', 'No tasks yet')}</span>
								</div>
							{/if}
						{/each}
					{/if}

					{#if adding_to_column === column.id}
						<div class="card-form">
							<input
								type="text"
								bind:value={form_title}
								placeholder={t('task_title_placeholder', 'Task title...')}
								onkeydown={(e) => handle_keydown(e, column.id)}
								autofocus
							/>
							<textarea
								bind:value={form_description}
								placeholder={t('description_placeholder', 'Add description...')}
								rows="2"
							></textarea>
							<div class="form-row">
								<select bind:value={form_priority}>
									{#each priorities as p}
										<option value={p.id}>{p.name}</option>
									{/each}
								</select>
								<select bind:value={form_label}>
									<option value="">{t('no_label', 'No label')}</option>
									{#each labels as l}
										<option value={l.id}>{l.name}</option>
									{/each}
								</select>
							</div>
							<input type="date" bind:value={form_due_date} />
							<div class="form-actions">
								<button class="save-btn" onclick={() => save_card(column.id)}>{t('add_button', 'Add Card')}</button>
								<button class="cancel-btn" onclick={cancel_form}>{t('cancel', 'Cancel')}</button>
							</div>
						</div>
					{:else}
						<button class="add-card-btn" onclick={() => start_adding(column.id)}>
							<Icon icon="lucide:plus" width={16} />
							{t('add_card_text', 'Add a card')}
						</button>
					{/if}
				</div>
			</div>
		{/each}
	</div>
	<footer class="footer">built with Hangar</footer>
</div>

<style>
	.page {
		min-height: 100vh;
		background: var(--page-background, #f1f5f9);
		font-family: var(--body-font, system-ui, sans-serif);
		display: flex;
		flex-direction: column;
	}

	.header {
		padding: 1.5rem 2rem;
		background: var(--header-background, #ffffff);
		border-bottom: 1px solid var(--border-color, #e2e8f0);
	}

	.header-content {
		display: flex;
		align-items: baseline;
		gap: 1rem;
	}

	.header h1 {
		margin: 0;
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--heading-text-color, #1e293b);
	}

	.subtitle {
		margin: 0;
		font-size: 0.875rem;
		color: var(--secondary-text-color, #64748b);
	}

	.board {
		display: flex;
		gap: 1rem;
		padding: 1.5rem;
		flex: 1;
		overflow-x: auto;
	}

	.column {
		width: 320px;
		min-width: 320px;
		background: var(--column-background, #ffffff);
		border-radius: var(--column-radius, 12px);
		padding: 1rem;
		display: flex;
		flex-direction: column;
		max-height: calc(100vh - 180px);
		border: 1px solid var(--border-color, #e2e8f0);
		transition: all 0.2s ease;
	}

	.column.drag-over {
		background: var(--drag-over-background, #f8fafc);
		border-color: var(--accent-color, #3b82f6);
		border-style: dashed;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}

	.column-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
		padding-bottom: 0.75rem;
		border-bottom: 1px solid var(--border-color, #e2e8f0);
	}

	.column-title {
		display: flex;
		align-items: center;
		gap: 8px;
		color: var(--heading-text-color, #1e293b);
	}

	.column-header h2 {
		margin: 0;
		font-size: 0.875rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.025em;
	}

	.count {
		background: var(--count-background, #f1f5f9);
		color: var(--secondary-text-color, #64748b);
		font-size: 0.75rem;
		font-weight: 600;
		padding: 2px 8px;
		border-radius: 10px;
	}

	.cards {
		flex: 1;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.card {
		background: var(--card-background, #ffffff);
		border: 1px solid var(--card-border, #e2e8f0);
		border-radius: var(--card-radius, 8px);
		padding: 12px;
		cursor: grab;
		display: flex;
		flex-direction: column;
		gap: 8px;
		transition: all 0.2s ease;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
	}

	.card:hover {
		border-color: var(--card-hover-border, #cbd5e1);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
		transform: translateY(-1px);
	}

	.card.dragging {
		opacity: 0.5;
		cursor: grabbing;
		transform: rotate(2deg);
	}

	.card.expanded {
		border-color: var(--accent-color, #3b82f6);
	}

	.card-label {
		padding: 2px 8px;
		border-radius: 4px;
		font-size: 0.7rem;
		font-weight: 600;
		color: #fff;
		align-self: flex-start;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.card-main {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 8px;
	}

	.card-title {
		color: var(--body-text-color, #334155);
		font-size: 0.9rem;
		font-weight: 500;
		line-height: 1.4;
		word-break: break-word;
		cursor: pointer;
	}

	.card-description {
		margin: 0;
		color: var(--secondary-text-color, #64748b);
		font-size: 0.8rem;
		line-height: 1.5;
		padding: 8px;
		background: var(--page-background, #f8fafc);
		border-radius: 6px;
	}

	.card-actions {
		display: flex;
		gap: 4px;
		opacity: 0;
		transition: opacity 0.15s;
	}

	.card:hover .card-actions {
		opacity: 1;
	}

	.action-btn {
		background: none;
		border: none;
		color: var(--secondary-text-color, #94a3b8);
		cursor: pointer;
		padding: 4px;
		border-radius: 4px;
		transition: all 0.15s;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.action-btn:hover {
		background: var(--page-background, #f1f5f9);
		color: var(--body-text-color, #334155);
	}

	.action-btn.delete:hover {
		color: var(--danger-color, #ef4444);
		background: #fef2f2;
	}

	.card-meta {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 0.75rem;
	}

	.priority {
		display: flex;
		align-items: center;
	}

	.due-date {
		display: flex;
		align-items: center;
		gap: 4px;
		color: var(--secondary-text-color, #64748b);
		background: var(--page-background, #f8fafc);
		padding: 2px 6px;
		border-radius: 4px;
	}

	.due-date.overdue {
		color: var(--danger-color, #ef4444);
		background: #fef2f2;
	}

	.has-description {
		color: var(--secondary-text-color, #94a3b8);
		display: flex;
		align-items: center;
	}

	.empty-column {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
		padding: 2rem 1rem;
		color: var(--secondary-text-color, #94a3b8);
		font-size: 0.875rem;
	}

	.add-card-btn {
		background: none;
		border: 1px dashed var(--border-color, #e2e8f0);
		color: var(--secondary-text-color, #64748b);
		cursor: pointer;
		padding: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		font-size: 0.875rem;
		border-radius: var(--card-radius, 8px);
		transition: all 0.15s;
		width: 100%;
		margin-top: auto;
	}

	.add-card-btn:hover {
		background: var(--hover-background, #f8fafc);
		border-color: var(--secondary-text-color, #94a3b8);
		color: var(--body-text-color, #334155);
	}

	.card-form {
		display: flex;
		flex-direction: column;
		gap: 8px;
		background: var(--card-background, #ffffff);
		border: 1px solid var(--accent-color, #3b82f6);
		border-radius: var(--card-radius, 8px);
		padding: 12px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.card-form input[type="text"],
	.card-form textarea {
		padding: 10px 12px;
		border: 1px solid var(--border-color, #e2e8f0);
		border-radius: 6px;
		font-size: 0.9rem;
		color: var(--body-text-color, #334155);
		background: var(--input-background, #ffffff);
		font-family: inherit;
		resize: none;
	}

	.card-form input:focus,
	.card-form textarea:focus,
	.card-form select:focus {
		outline: none;
		border-color: var(--accent-color, #3b82f6);
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}

	.card-form input::placeholder,
	.card-form textarea::placeholder {
		color: var(--placeholder-color, #94a3b8);
	}

	.form-row {
		display: flex;
		gap: 8px;
	}

	.card-form select,
	.card-form input[type="date"] {
		padding: 8px 10px;
		border: 1px solid var(--border-color, #e2e8f0);
		border-radius: 6px;
		font-size: 0.8rem;
		color: var(--body-text-color, #334155);
		background: var(--input-background, #ffffff);
		flex: 1;
	}

	.form-actions {
		display: flex;
		gap: 8px;
		margin-top: 4px;
	}

	.save-btn {
		padding: 8px 16px;
		background: var(--accent-color, #3b82f6);
		color: #ffffff;
		border: none;
		border-radius: 6px;
		font-weight: 500;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.15s;
	}

	.save-btn:hover {
		filter: brightness(1.1);
	}

	.cancel-btn {
		padding: 8px 16px;
		background: none;
		border: 1px solid var(--border-color, #e2e8f0);
		color: var(--secondary-text-color, #64748b);
		border-radius: 6px;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.15s;
	}

	.cancel-btn:hover {
		background: var(--page-background, #f8fafc);
		color: var(--body-text-color, #334155);
	}

	.loading {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		color: var(--secondary-text-color, #64748b);
		font-size: 0.875rem;
		padding: 2rem 1rem;
	}

	:global(.spin) {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.footer {
		text-align: center;
		padding: 1rem;
		font-size: 0.75rem;
		color: var(--secondary-text-color, #94a3b8);
	}

	.footer a {
		color: inherit;
		text-decoration: none;
	}

	.footer a:hover {
		text-decoration: underline;
	}
</style>
