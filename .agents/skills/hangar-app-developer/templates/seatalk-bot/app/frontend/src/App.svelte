<script lang="ts">
  // @ts-nocheck
  import { onMount } from 'svelte'
  import content from '$content'
  import { api, language, nav, table } from '$hangarkit'

  type SeatalkEvent = {
    id: string
    event_id?: string
    event_type?: string
    conversation_key?: string
    employee_code?: string
    group_id?: string
    thread_id?: string
    message_id?: string
    message_link?: string
    handler?: string
    summary?: string
    status?: string
    processed?: boolean
    payload?: Record<string, any>
    error?: string
    created?: string
  }

  type SeatalkMessage = {
    id: string
    conversation_key?: string
    direction?: 'inbound' | 'outbound' | 'thread'
    event_type?: string
    seatalk_message_id?: string
    message_link?: string
    thread_id?: string
    employee_code?: string
    group_id?: string
    sender?: Record<string, any>
    text?: string
    payload?: Record<string, any>
    status?: string
    error?: string
    created?: string
  }

  type SeatalkThread = {
    id: string
    thread_id?: string
    conversation_key?: string
    group_id?: string
    employee_code?: string
    source_event_type?: string
    message_count?: number
    last_message_id?: string
    last_message_text?: string
    last_sender?: Record<string, any>
    last_synced_at?: string
    status?: string
    error?: string
    created?: string
  }

  type SeatalkGroup = {
    id: string
    group_id?: string
    group_name?: string
    member_count?: number
    status?: string
    last_synced_at?: string
    error?: string
  }

  type BotSkill = {
    id: string
    title?: string
    instructions?: string
    enabled?: boolean
    created?: string
  }

  const callback_url = 'https://hangar.invalid/hangar/api/callback/seatalk/hangar-template-app'
  const message_link_base = 'https://link.seatalk.io/message/open?message_id='
  const events_table = table('seatalk_events')
  const messages_table = table('seatalk_messages')
  const threads_table = table('seatalk_threads')
  const groups_table = table('seatalk_groups')
  const skills_table = table('seatalk_bot_skills')

  let route = $state('/')
  let events = $state<SeatalkEvent[]>([])
  let messages = $state<SeatalkMessage[]>([])
  let threads = $state<SeatalkThread[]>([])
  let groups = $state<SeatalkGroup[]>([])
  let skills = $state<BotSkill[]>([])
  let loading = $state(true)
  let syncing_groups = $state(false)
  let syncing_thread = $state(false)
  let copied = $state(false)
  let health = $state({ status: 'unknown', configured: false, app: '', handled_event_types: [] })
  let reply_text = $state('')
  let reply_busy = $state(false)
  let reply_error = $state('')
  let skill_saving = $state(false)
  let skill_error = $state('')
  let skill_form = $state({ id: '', title: '', instructions: '', enabled: true })
  let language_id = $state('en')

  let active_thread_id = $derived.by(() => {
    const parts = route.split('/').filter(Boolean)
    return parts[0] === 'threads' && parts[1] ? decodeURIComponent(parts[1]) : ''
  })
  let page = $derived.by(() => route.split('/').filter(Boolean)[0] || 'dashboard')
  let selected_thread = $derived.by(() => threads.find((thread) => thread.thread_id === active_thread_id))
  let latest_event = $derived.by(() => events[0])
  let latest_thread = $derived.by(() => threads[0])
  let failed_messages = $derived.by(() => messages.filter((message) => message.status === 'failed'))
  let thread_messages = $derived.by(() =>
    messages
      .filter((message) => message.thread_id === active_thread_id)
      .sort((a, b) => date_value(a.created) - date_value(b.created))
  )
  let inbound_count = $derived.by(() => messages.filter((message) => message.direction === 'inbound').length)
  let outbound_count = $derived.by(() => messages.filter((message) => message.direction === 'outbound').length)
  let failed_count = $derived.by(() => failed_messages.length + threads.filter((thread) => thread.status === 'failed').length)
  let pending_count = $derived.by(() => events.filter((event) => !event.processed).length)
  let enabled_skill_count = $derived.by(() => skills.filter((skill) => skill.enabled !== false).length)
  let localized = $derived.by(() => {
    const dictionary = content.localized_copy || {}
    return dictionary[language_id] || dictionary.en || {}
  })

  onMount(() => {
    const stop_language = language.subscribe((value) => {
      language_id = value.id
    })
    update_route()
    window.addEventListener('popstate', update_route)
    void refresh()
    return () => {
      stop_language()
      window.removeEventListener('popstate', update_route)
    }
  })

  function copy(key: string, fallback = '') {
    return localized?.[key] || content[key] || fallback
  }

  function update_route() {
    route = nav.localPath().split('?')[0] || '/'
  }

  function go(path: string) {
    nav.navigate(path)
    update_route()
  }

  async function refresh() {
    loading = true
    try {
      await Promise.all([load_events(), load_messages(), load_threads(), load_groups(), load_skills(), check_health()])
    } finally {
      loading = false
    }
  }

  async function load_events() {
    events = await events_table.list({ sort: '-created', perPage: 100 })
  }

  async function load_messages() {
    messages = await messages_table.list({ sort: '-created', perPage: 300 })
  }

  async function load_threads() {
    threads = await threads_table.list({ sort: '-last_synced_at', perPage: 100 })
  }

  async function load_groups() {
    groups = await groups_table.list({ sort: '-last_synced_at', perPage: 50 })
  }

  async function load_skills() {
    skills = await skills_table.list({ sort: '-created', perPage: 50 })
  }

  async function check_health() {
    try {
      health = await api.get('/health')
    } catch (error) {
      health = { status: 'offline', configured: false, app: '', handled_event_types: [] }
    }
  }

  async function sync_groups() {
    syncing_groups = true
    try {
      await api.get('/seatalk/groups/sync')
      await load_groups()
    } finally {
      syncing_groups = false
    }
  }

  async function sync_thread(thread: SeatalkThread) {
    syncing_thread = true
    try {
      await api.post('/seatalk/thread/sync', {
        thread_id: thread.thread_id,
        group_id: thread.group_id,
        employee_code: thread.employee_code,
        message_id: thread.last_message_id,
      })
      await Promise.all([load_threads(), load_messages()])
    } finally {
      syncing_thread = false
    }
  }

  async function send_reply() {
    if (!selected_thread || !reply_text.trim()) return
    reply_busy = true
    reply_error = ''
    try {
      await api.post('/seatalk/reply', {
        text: reply_text.trim(),
        thread_id: selected_thread.thread_id,
        group_id: selected_thread.group_id,
        employee_code: selected_thread.employee_code,
        message_id: selected_thread.last_message_id,
      })
      reply_text = ''
      await Promise.all([load_messages(), load_threads()])
    } catch (error) {
      reply_error = error instanceof Error ? error.message : String(error)
    } finally {
      reply_busy = false
    }
  }

  async function mark_processed(event: SeatalkEvent) {
    await api.post('/seatalk/mark-processed', { id: event.id })
    await load_events()
  }

  function edit_skill(skill: BotSkill) {
    skill_form = {
      id: skill.id,
      title: skill.title || '',
      instructions: skill.instructions || '',
      enabled: skill.enabled !== false,
    }
  }

  function reset_skill_form() {
    skill_form = { id: '', title: '', instructions: '', enabled: true }
    skill_error = ''
  }

  async function save_skill() {
    if (!skill_form.title.trim() || !skill_form.instructions.trim()) return
    skill_saving = true
    skill_error = ''
    const payload = {
      title: skill_form.title.trim(),
      instructions: skill_form.instructions.trim(),
      enabled: skill_form.enabled,
    }
    try {
      if (skill_form.id) {
        await skills_table.update(skill_form.id, payload)
      } else {
        await skills_table.create(payload)
      }
      reset_skill_form()
      await load_skills()
    } catch (error) {
      skill_error = error instanceof Error ? error.message : String(error)
    } finally {
      skill_saving = false
    }
  }

  async function toggle_skill(skill: BotSkill) {
    await skills_table.update(skill.id, { enabled: skill.enabled === false })
    await load_skills()
  }

  async function delete_skill(skill: BotSkill) {
    if (!window.confirm(`Delete skill "${skill.title || skill.id}"?`)) return
    await skills_table.delete(skill.id)
    if (skill_form.id === skill.id) reset_skill_form()
    await load_skills()
  }

  async function copy_callback() {
    await navigator.clipboard.writeText(callback_url)
    copied = true
    window.setTimeout(() => (copied = false), 1200)
  }

  function date_value(value?: string) {
    const parsed = Date.parse(value || '')
    return Number.isFinite(parsed) ? parsed : 0
  }

  function format_time(value?: string) {
    if (!value) return 'Never'
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return value
    return parsed.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  function preview(value?: string, fallback = 'No text captured') {
    const text = String(value || '').replace(/\s+/g, ' ').trim()
    return text || fallback
  }

  function sender_label(sender?: Record<string, any>) {
    if (!sender) return copy('unknown_sender', 'Unknown')
    if (sender.bot) return copy('bot_sender', 'Bot')
    return sender.email || sender.username || sender.employee_code || sender.seatalk_id || copy('unknown_sender', 'Unknown')
  }

  function initials(value?: string) {
    const text = String(value || 'ST').trim()
    return text.slice(0, 2).toUpperCase()
  }

  function message_link(message_id?: string, existing?: string) {
    return existing || (message_id ? message_link_base + encodeURIComponent(message_id) : '')
  }

  function payload_preview(payload?: Record<string, any>) {
    if (!payload) return '{}'
    return JSON.stringify(payload, null, 2).slice(0, 1600)
  }

  function thread_path(thread_id?: string) {
    return `/threads/${encodeURIComponent(thread_id || '')}`
  }
</script>

<div class="app-shell">
  <aside class="side-nav">
    <div class="brand">
      <div class="brand-mark">ST</div>
      <div>
        <strong>{copy('app_title', 'SeaTalk bot')}</strong>
        <span>{health.configured ? copy('integration_ready', 'Integration ready') : copy('needs_setup', 'Needs setup')}</span>
      </div>
    </div>

    <nav aria-label={copy('app_sections_aria', 'App sections')}>
      <button class:active={page === 'dashboard'} type="button" onclick={() => go('/')}><span>{copy('nav_overview', 'Overview')}</span><small>{copy('nav_overview_hint', 'Health and groups')}</small></button>
      <button class:active={page === 'events'} type="button" onclick={() => go('/events')}><span>{copy('nav_events', 'Events')}</span><small>{copy('nav_events_hint', 'Webhook audit')}</small></button>
      <button class:active={page === 'threads'} type="button" onclick={() => go('/threads')}><span>{copy('nav_threads', 'Threads')}</span><small>{copy('nav_threads_hint', 'Conversation review')}</small></button>
      <button class:active={page === 'skills'} type="button" onclick={() => go('/skills')}><span>{copy('nav_skills', 'Skills')}</span><small>{copy('nav_skills_hint', 'Agent behavior')}</small></button>
    </nav>

    <section class="bot-policy">
      <p>{copy('agent_skills_label', 'Agent skills')}</p>
      <strong>{copy('active_skills_count', '{count} active').replace('{count}', String(enabled_skill_count))}</strong>
      <span>{copy('agent_skills_hint', 'Enabled skill instructions are injected before Wingman Chat handles a user message.')}</span>
    </section>

    <section class="callback-card">
      <span>{copy('callback_label', 'Callback URL')}</span>
      <code>{callback_url}</code>
      <button type="button" onclick={() => void copy_callback()}>{copied ? copy('copied', 'Copied') : copy('copy_url', 'Copy URL')}</button>
    </section>
  </aside>

  <main>
    {#if page === 'dashboard'}
      <section class="hero-panel">
        <div class="hero-copy">
          <p>{copy('eyebrow', 'SeaTalk bot console')}</p>
          <h1>{copy('hero_title', 'Manage, audit, and tune your bot from one Hangar app.')}</h1>
          <span>{copy('intro_text', 'Monitor webhook delivery, sync joined groups, inspect thread context, and prepare custom reply logic.')}</span>
        </div>
        <div class="hero-actions">
          <button class="secondary" type="button" onclick={() => go('/threads')}>{copy('review_threads', 'Review threads')}</button>
          <button class="primary" type="button" onclick={() => void refresh()}>{loading ? copy('refreshing', 'Refreshing...') : copy('refresh_console', 'Refresh console')}</button>
        </div>
      </section>

      <section class="metrics">
        <article><span>Backend</span><strong>{health.status}</strong><small>{health.configured ? 'Callbacks accepted' : 'Missing credentials'}</small></article>
        <article><span>Handled events</span><strong>{events.length}</strong><small>{pending_count} pending review</small></article>
        <article><span>Threads</span><strong>{threads.length}</strong><small>{latest_thread ? `Latest ${format_time(latest_thread.last_synced_at)}` : 'No sync yet'}</small></article>
        <article><span>Agent skills</span><strong>{enabled_skill_count}</strong><small>{skills.length} configured</small></article>
      </section>

      <section class="dashboard-grid">
        <div class="panel operations-panel">
          <div class="section-heading">
            <div><h2>Operational readiness</h2><span>What the bot can safely do right now</span></div>
          </div>
          <div class="readiness-list">
            <div><strong>Webhook signature</strong><span class:ok={health.configured}>{health.configured ? 'Configured' : 'Waiting for credentials'}</span></div>
            <div><strong>Thread context</strong><span class:ok={threads.length > 0}>{threads.length > 0 ? 'Syncing from SeaTalk' : 'No thread events yet'}</span></div>
            <div><strong>Agent skills</strong><span class:ok={enabled_skill_count > 0}>{enabled_skill_count > 0 ? `${enabled_skill_count} active` : 'No active skills'}</span></div>
          </div>
        </div>

        <div class="panel groups-panel">
          <div class="section-heading">
            <div><h2>Joined groups</h2><span>Groups where this bot can receive mentions</span></div>
            <button type="button" onclick={() => void sync_groups()}>{syncing_groups ? 'Syncing...' : 'Sync groups'}</button>
          </div>
          {#if groups.length === 0}
            <div class="empty-state"><strong>No groups synced</strong><span>Use Sync groups after credentials are configured.</span></div>
          {:else}
            <ul class="group-list">
              {#each groups as group (group.id)}
                <li>
                  <div class="avatar">{initials(group.group_name || group.group_id)}</div>
                  <div><strong>{group.group_name || group.group_id}</strong><span>{group.group_id}</span></div>
                  <small>{group.member_count || 0} members</small>
                </li>
              {/each}
            </ul>
          {/if}
        </div>

        <div class="panel recent-panel">
          <div class="section-heading">
            <div><h2>Recent thread context</h2><span>Fetched using SeaTalk thread APIs</span></div>
            <button type="button" onclick={() => go('/threads')}>View all</button>
          </div>
          {#if threads.length === 0}
            <div class="empty-state"><strong>No threads yet</strong><span>Mention the bot in a group or direct chat to start a trace.</span></div>
          {:else}
            <ul class="compact-list">
              {#each threads.slice(0, 5) as thread (thread.id)}
                <li>
                  <button class="link-row" type="button" onclick={() => go(thread_path(thread.thread_id))}>
                    <strong>{thread.thread_id}</strong>
                    <span>{preview(thread.last_message_text)}</span>
                  </button>
                  <small>{format_time(thread.last_synced_at)}</small>
                </li>
              {/each}
            </ul>
          {/if}
        </div>

        <div class="panel events-panel">
          <div class="section-heading">
            <div><h2>Latest webhook</h2><span>Most recent handled callback</span></div>
            <button type="button" onclick={() => go('/events')}>Open audit</button>
          </div>
          {#if latest_event}
            <div class="event-card">
              <span class="pill">{latest_event.event_type}</span>
              <strong>{preview(latest_event.summary)}</strong>
              <small>{format_time(latest_event.created)} · {latest_event.thread_id || latest_event.group_id || latest_event.employee_code}</small>
            </div>
          {:else}
            <div class="empty-state"><strong>No callbacks</strong><span>Events will appear here after SeaTalk calls the webhook.</span></div>
          {/if}
        </div>
      </section>
    {:else if page === 'events'}
      <section class="page-header"><div><p>Webhook audit</p><h1>Handled events</h1><span>Only events handled by this template are stored.</span></div></section>
      <section class="panel">
        {#if events.length === 0}
          <div class="empty-state"><strong>{content.empty_events || 'No handled callbacks received yet.'}</strong><span>Trigger a mention or direct message to populate this page.</span></div>
        {:else}
          <ul class="timeline">
            {#each events as event (event.id)}
              <li>
                <div class="row-main">
                  <div class="row-title"><strong>{event.event_type || 'callback'}</strong><span class="pill">{event.processed ? 'processed' : event.status || 'handled'}</span></div>
                  <p>{event.summary || event.handler || 'Handled SeaTalk callback'}</p>
                  <div class="meta"><span>{event.thread_id || event.conversation_key}</span>{#if event.group_id}<span>group {event.group_id}</span>{/if}</div>
                  <details><summary>Payload</summary><pre>{payload_preview(event.payload)}</pre></details>
                </div>
                <div class="row-side">
                  <time>{format_time(event.created)}</time>
                  {#if message_link(event.message_id, event.message_link)}<a href={message_link(event.message_id, event.message_link)} target="_blank" rel="noreferrer">Open SeaTalk</a>{/if}
                  {#if !event.processed}<button type="button" onclick={() => void mark_processed(event)}>Mark done</button>{/if}
                </div>
              </li>
            {/each}
          </ul>
        {/if}
      </section>
    {:else if page === 'skills'}
      <section class="page-header">
        <div><p>Agent behavior</p><h1>Bot skills</h1><span>Enabled skills are added to the Wingman Chat context before each generated reply.</span></div>
        <div class="actions"><button type="button" onclick={() => void load_skills()}>Refresh</button><button class="primary" type="button" onclick={reset_skill_form}>New skill</button></div>
      </section>

      <section class="skills-layout">
        <form class="skill-editor" onsubmit={(event) => { event.preventDefault(); void save_skill() }}>
          <div class="section-heading">
            <div><h2>{skill_form.id ? 'Edit skill' : 'Add skill'}</h2><span>Write durable instructions the agent should follow when relevant.</span></div>
          </div>
          <label>
            <span>Title</span>
            <input bind:value={skill_form.title} placeholder="Escalation triage" />
          </label>
          <label>
            <span>Instructions</span>
            <textarea bind:value={skill_form.instructions} placeholder="When users report an incident, ask for region, impact, request id, and recent changes. Then summarize next actions."></textarea>
          </label>
          <label class="toggle-row">
            <input type="checkbox" bind:checked={skill_form.enabled} />
            <span>Enabled</span>
          </label>
          {#if skill_error}<p class="error">{skill_error}</p>{/if}
          <div class="form-actions">
            <button type="button" onclick={reset_skill_form}>Clear</button>
            <button class="primary" type="submit" disabled={skill_saving || !skill_form.title.trim() || !skill_form.instructions.trim()}>{skill_saving ? 'Saving...' : skill_form.id ? 'Save changes' : 'Add skill'}</button>
          </div>
        </form>

        <div class="panel">
          <div class="section-heading">
            <div><h2>Configured skills</h2><span>{enabled_skill_count} active of {skills.length}</span></div>
          </div>
          {#if skills.length === 0}
            <div class="empty-state"><strong>No skills configured.</strong><span>Add a skill to tune how the bot answers SeaTalk messages.</span></div>
          {:else}
            <ul class="skill-list">
              {#each skills as skill (skill.id)}
                <li class:disabled={skill.enabled === false}>
                  <div>
                    <div class="row-title"><strong>{skill.title || 'Untitled skill'}</strong><span class="pill">{skill.enabled === false ? 'off' : 'active'}</span></div>
                    <p>{preview(skill.instructions, 'No instructions')}</p>
                    <small>{format_time(skill.created)}</small>
                  </div>
                  <div class="skill-actions">
                    <button type="button" onclick={() => edit_skill(skill)}>Edit</button>
                    <button type="button" onclick={() => void toggle_skill(skill)}>{skill.enabled === false ? 'Enable' : 'Disable'}</button>
                    <button type="button" onclick={() => void delete_skill(skill)}>Delete</button>
                  </div>
                </li>
              {/each}
            </ul>
          {/if}
        </div>
      </section>
    {:else if page === 'threads' && active_thread_id}
      <section class="page-header">
        <div><p>Conversation thread</p><h1>{active_thread_id}</h1><span>{selected_thread?.group_id ? `Group ${selected_thread.group_id}` : `Subscriber ${selected_thread?.employee_code || ''}`}</span></div>
        <div class="actions"><button type="button" onclick={() => go('/threads')}>Back</button>{#if selected_thread}<button class="primary" type="button" onclick={() => void sync_thread(selected_thread)}>{syncing_thread ? 'Syncing...' : 'Sync thread'}</button>{/if}</div>
      </section>

      <section class="chat-layout">
        <div class="chat-panel">
          {#if thread_messages.length === 0}
            <div class="empty-state"><strong>No messages synced</strong><span>Run Sync thread to fetch context from SeaTalk.</span></div>
          {:else}
            {#each thread_messages as message (message.id)}
              <article class:bot={message.direction === 'outbound'} class="bubble">
                <div><strong>{sender_label(message.sender)}</strong><time>{format_time(message.created)}</time></div>
                <p>{preview(message.text)}</p>
                {#if message_link(message.seatalk_message_id, message.message_link)}<a href={message_link(message.seatalk_message_id, message.message_link)} target="_blank" rel="noreferrer">Open message</a>{/if}
              </article>
            {/each}
          {/if}
        </div>
        <form class="reply-box" onsubmit={(event) => { event.preventDefault(); void send_reply() }}>
          <div><label for="reply">Bot reply draft</label><span>Later this can be generated from your custom Python policy.</span></div>
          <textarea id="reply" bind:value={reply_text} placeholder="Type a reply as the bot"></textarea>
          {#if reply_error}<p class="error">{reply_error}</p>{/if}
          <button class="primary" type="submit" disabled={reply_busy || !reply_text.trim()}>{reply_busy ? 'Sending...' : 'Send reply'}</button>
        </form>
      </section>
    {:else if page === 'threads'}
      <section class="page-header"><div><p>Conversation index</p><h1>SeaTalk threads</h1><span>Review context, sender attribution, and bot responses by thread id.</span></div></section>
      <section class="panel">
        {#if threads.length === 0}
          <div class="empty-state"><strong>No thread rows yet.</strong><span>Threads are created after mention or thread-message callbacks.</span></div>
        {:else}
          <ul class="thread-list">
            {#each threads as thread (thread.id)}
              <li>
                <button type="button" onclick={() => go(thread_path(thread.thread_id))}>
                  <div><strong>{thread.thread_id}</strong><span>{preview(thread.last_message_text)}</span></div>
                  <small>{thread.message_count || 0} messages · {format_time(thread.last_synced_at)}</small>
                </button>
              </li>
            {/each}
          </ul>
        {/if}
      </section>
    {/if}
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    background: var(--page-background, #f4f7f6);
    color: var(--ink-color, #18212f);
    font-family: var(--font-family, Inter), ui-sans-serif, system-ui, sans-serif;
    overflow-x: hidden;
  }

  :global(*) {
    box-sizing: border-box;
  }

  button, input, textarea { font: inherit; }
  button { cursor: pointer; border: 1px solid var(--border-color, #d9e2ea); background: #fff; color: inherit; border-radius: 7px; padding: 0.58rem 0.78rem; transition: border-color 140ms ease, background 140ms ease, transform 140ms ease; }
  button:hover { border-color: var(--accent-color, #0f8f75); transform: translateY(-1px); }
  button.primary, .callback-card button { background: var(--accent-color, #0f8f75); border-color: var(--accent-color, #0f8f75); color: #fff; }
  button.secondary { background: var(--muted-panel, #eef5f2); }
  button:disabled { cursor: not-allowed; opacity: 0.55; transform: none; }
  a { color: var(--accent-color, #0f8f75); text-decoration: none; }
  h1, h2, p { margin: 0; }

  .app-shell { width: 100%; max-width: 100vw; min-height: 100vh; display: grid; grid-template-columns: 292px minmax(0, 1fr); overflow-x: hidden; }
  .side-nav { min-width: 0; border-right: 1px solid var(--border-color, #d9e2ea); background: rgba(255, 255, 255, 0.92); padding: 1rem; display: flex; flex-direction: column; gap: 1rem; position: sticky; top: 0; height: 100vh; box-sizing: border-box; }
  .brand { display: flex; gap: 0.78rem; align-items: center; padding: 0.35rem; }
  .brand-mark { width: 46px; height: 46px; border-radius: 8px; background: linear-gradient(135deg, var(--accent-color, #0f8f75), #126b82); color: #fff; display: grid; place-items: center; font-weight: 800; box-shadow: 0 12px 28px rgba(15, 143, 117, 0.18); }
  .brand strong, .brand span { display: block; overflow-wrap: anywhere; }
  .brand span, .page-header p, .page-header span, small, .meta, .empty-state span, .bot-policy span { color: var(--muted-ink-color, #607083); }
  nav { display: grid; gap: 0.35rem; }
  nav button { text-align: left; border-color: transparent; background: transparent; display: grid; gap: 0.1rem; }
  nav button span { font-weight: 700; }
  nav button small { font-size: 0.76rem; }
  nav button.active { background: var(--muted-panel, #eef5f2); color: var(--accent-color, #0f8f75); }
  .bot-policy, .callback-card { display: grid; gap: 0.55rem; padding: 0.85rem; border: 1px solid var(--border-color, #d9e2ea); border-radius: var(--panel-radius, 8px); background: #fff; }
  .bot-policy p, .callback-card span { color: var(--muted-ink-color, #607083); font-size: 0.78rem; font-weight: 700; text-transform: uppercase; }
  .bot-policy strong { font-size: 0.98rem; }
  .callback-card code { font-size: 0.75rem; overflow-wrap: anywhere; color: var(--muted-ink-color, #607083); }
  .callback-card { margin-top: auto; background: var(--muted-panel, #eef5f2); }

  main { min-width: 0; width: 100%; padding: var(--page-padding, 1.5rem); padding-right: clamp(2rem, 4vw, 4rem); display: grid; gap: 1rem; align-content: start; }
  .hero-panel, .page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; border: 1px solid var(--border-color, #d9e2ea); border-radius: var(--panel-radius, 8px); background: var(--panel-background, #fff); padding: 1.1rem; }
  .hero-copy { max-width: 780px; }
  .hero-copy p, .page-header p { color: var(--accent-color, #0f8f75); font-weight: 800; text-transform: uppercase; font-size: 0.76rem; letter-spacing: 0; }
  .hero-copy h1, .page-header h1 { font-size: clamp(1.85rem, 4vw, 3.2rem); line-height: 1; margin: 0.2rem 0 0.45rem; letter-spacing: 0; }
  .hero-copy span { color: var(--muted-ink-color, #607083); line-height: 1.5; }
  .hero-actions, .actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
  .metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.75rem; }
  .metrics article, .panel, .chat-panel, .reply-box, .skill-editor { min-width: 0; background: var(--panel-background, #fff); border: 1px solid var(--border-color, #d9e2ea); border-radius: var(--panel-radius, 8px); box-shadow: 0 14px 40px rgba(24, 33, 47, 0.045); }
  .metrics article { padding: 1rem; display: grid; gap: 0.28rem; }
  .metrics span { color: var(--muted-ink-color, #607083); font-size: 0.82rem; }
  .metrics strong { font-size: 1.75rem; letter-spacing: 0; }
  .dashboard-grid { display: grid; grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr); gap: 1rem; }
  .recent-panel, .events-panel { min-height: 250px; }
  .panel { padding: 1rem; }
  .section-heading { min-width: 0; display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; margin-bottom: 1rem; }
  .section-heading > div { min-width: 0; }
  .section-heading span { color: var(--muted-ink-color, #607083); font-size: 0.88rem; }
  .readiness-list { display: grid; gap: 0.65rem; }
  .readiness-list div { display: flex; justify-content: space-between; gap: 1rem; border: 1px solid var(--border-color, #d9e2ea); border-radius: 7px; padding: 0.75rem; }
  .readiness-list span { color: var(--signal-color, #d9462f); }
  .readiness-list span.ok { color: var(--accent-color, #0f8f75); }
  .group-list, .compact-list, .timeline, .thread-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.65rem; }
  .group-list li, .compact-list li, .timeline li, .thread-list li button { width: 100%; min-width: 0; box-sizing: border-box; display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; padding: 0.75rem; border: 1px solid var(--border-color, #d9e2ea); border-radius: 7px; background: #fff; text-align: left; }
  .group-list li { align-items: center; justify-content: start; }
  .compact-list li { display: grid; grid-template-columns: minmax(0, 1fr) max-content; }
  .compact-list small { white-space: nowrap; }
  .avatar { width: 34px; height: 34px; border-radius: 7px; background: var(--muted-panel, #eef5f2); color: var(--accent-color, #0f8f75); display: grid; place-items: center; font-weight: 800; flex: 0 0 auto; }
  .group-list small { margin-left: auto; }
  .compact-list strong, .compact-list span, .link-row strong, .link-row span, .thread-list strong, .thread-list span, .group-list strong, .group-list span { display: block; min-width: 0; overflow-wrap: anywhere; }
  .compact-list span, .link-row span, .thread-list span, .group-list span { color: var(--muted-ink-color, #607083); font-size: 0.84rem; margin-top: 0.2rem; }
  .link-row { min-width: 0; max-width: 100%; border: 0; padding: 0; background: transparent; display: block; box-shadow: none; }
  .event-card { display: grid; gap: 0.65rem; }
  .event-card strong { font-size: 1.15rem; line-height: 1.35; }
  .timeline li { align-items: stretch; }
  .row-main { display: grid; gap: 0.45rem; min-width: 0; }
  .row-title { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
  .pill { border-radius: 999px; background: var(--muted-panel, #eef5f2); color: var(--accent-color, #0f8f75); padding: 0.16rem 0.5rem; font-size: 0.76rem; width: fit-content; }
  .meta { display: flex; gap: 0.65rem; flex-wrap: wrap; font-size: 0.8rem; }
  .row-side { display: grid; justify-items: end; gap: 0.4rem; min-width: 120px; }
  .empty-state { display: grid; gap: 0.25rem; padding: 1.2rem; border: 1px dashed var(--border-color, #d9e2ea); border-radius: 7px; background: var(--muted-panel, #eef5f2); }
  details pre { overflow: auto; max-height: 260px; background: #0f172a; color: #e2e8f0; border-radius: 6px; padding: 0.75rem; font-size: 0.78rem; }

  .chat-layout { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 1rem; align-items: start; }
  .chat-panel { padding: 1rem; min-height: 460px; display: grid; gap: 0.75rem; align-content: start; }
  .bubble { max-width: min(720px, 90%); border: 1px solid var(--border-color, #d9e2ea); border-radius: 8px; padding: 0.78rem; background: var(--muted-panel, #eef5f2); display: grid; gap: 0.4rem; }
  .bubble.bot { margin-left: auto; background: #e8f8f3; border-color: rgba(15, 143, 117, 0.35); }
  .bubble div { display: flex; justify-content: space-between; gap: 1rem; color: var(--muted-ink-color, #607083); font-size: 0.82rem; }
  .reply-box { padding: 1rem; display: grid; gap: 0.65rem; position: sticky; top: 1rem; }
  .reply-box div { display: grid; gap: 0.2rem; }
  .reply-box label { font-weight: 800; }
  .reply-box span { color: var(--muted-ink-color, #607083); font-size: 0.82rem; }
  .reply-box textarea { min-height: 190px; resize: vertical; border: 1px solid var(--border-color, #d9e2ea); border-radius: 7px; padding: 0.75rem; }
  .error { color: var(--signal-color, #d9462f); font-size: 0.86rem; }

  .skills-layout { display: grid; grid-template-columns: minmax(280px, 380px) minmax(0, 1fr); gap: 1rem; align-items: start; }
  .skill-editor { padding: 1rem; display: grid; gap: 0.8rem; position: sticky; top: 1rem; }
  .skill-editor label { display: grid; gap: 0.35rem; font-weight: 800; }
  .skill-editor label span { color: var(--muted-ink-color, #607083); font-size: 0.82rem; }
  .skill-editor input:not([type="checkbox"]), .skill-editor textarea { width: 100%; min-width: 0; border: 1px solid var(--border-color, #d9e2ea); border-radius: 7px; padding: 0.72rem; color: var(--ink-color, #18212f); background: #fff; }
  .skill-editor textarea { min-height: 260px; resize: vertical; line-height: 1.45; }
  .toggle-row { display: flex !important; grid-template-columns: none; align-items: center; gap: 0.5rem; width: fit-content; }
  .toggle-row input { width: 1rem; height: 1rem; accent-color: var(--accent-color, #0f8f75); }
  .form-actions, .skill-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
  .form-actions { justify-content: flex-end; }
  .skill-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.7rem; }
  .skill-list li { display: grid; grid-template-columns: minmax(0, 1fr) max-content; gap: 1rem; align-items: start; border: 1px solid var(--border-color, #d9e2ea); border-radius: 7px; background: #fff; padding: 0.85rem; }
  .skill-list li.disabled { opacity: 0.68; background: var(--muted-panel, #eef5f2); }
  .skill-list p { color: var(--muted-ink-color, #607083); line-height: 1.45; margin-top: 0.35rem; overflow-wrap: anywhere; }
  .skill-list small { display: block; margin-top: 0.45rem; }
  .skill-actions { justify-content: flex-end; }

  @media (max-width: 980px) {
    .app-shell { grid-template-columns: 1fr; }
    .side-nav { position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--border-color, #d9e2ea); }
    main { padding-right: var(--page-padding, 1.5rem); }
    .metrics, .dashboard-grid, .chat-layout, .skills-layout { grid-template-columns: 1fr; }
    .skill-editor { position: static; }
    .hero-panel, .page-header, .timeline li { flex-direction: column; }
    .row-side { justify-items: start; }
  }

  @media (max-width: 640px) {
    main { padding: 1rem; }
    .compact-list li { grid-template-columns: 1fr; }
    .compact-list small { white-space: normal; }
    .skill-list li { grid-template-columns: 1fr; }
    .skill-actions { justify-content: flex-start; }
  }
</style>
