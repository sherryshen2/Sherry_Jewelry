<script lang="ts">
  // @ts-nocheck
  import { onMount } from 'svelte'
  import content from '$content'
  import { api, language } from '$hangarkit'

  type Field = {
    id: string
    label: string
    description?: string
    placeholder?: string
    type?: 'text' | 'number' | 'textarea' | 'checkbox'
    required?: boolean
    default?: string
  }

  type Action = {
    id: string
    label: string
    description: string
    side_effect?: boolean
    fields: Field[]
  }

  type Provider = {
    id: string
    label: string
    description: string
    actions: Action[]
  }

  const app_name = '__HANGAR_APP_NAME__'

  let providers = $state<Provider[]>([])
  let provider_id = $state('')
  let action_id = $state('')
  let inputs = $state<Record<string, any>>({})
  let result = $state<any>(null)
  let loading = $state(true)
  let running = $state(false)
  let health = $state<any>(null)
  let load_error = $state('')
  let language_id = $state('en')

  let active_provider = $derived(providers.find((provider) => provider.id === provider_id) || providers[0])
  let active_action = $derived(active_provider?.actions.find((action) => action.id === action_id) || active_provider?.actions[0])
  let request_preview = $derived(JSON.stringify({ provider: active_provider?.id, action: active_action?.id, inputs }, null, 2))
  let result_text = $derived(result ? JSON.stringify(result, null, 2) : '')
  let ok_count = $derived(providers.reduce((count, provider) => count + provider.actions.length, 0))
  let localized = $derived.by(() => {
    const dictionary = content.localized_copy || {}
    return dictionary[language_id] || dictionary.en || {}
  })

  onMount(() => {
    const stop_language = language.subscribe((value) => {
      language_id = value.id
    })
    void load_catalog()
    return () => stop_language()
  })

  function copy(key: string, fallback = '') {
    return localized?.[key] || content[key] || fallback
  }

  async function load_catalog() {
    loading = true
    load_error = ''
    try {
      const [catalog, health_result] = await Promise.all([api.get('/catalog'), api.get('/health')])
      providers = catalog.providers || []
      health = health_result
      if (providers.length) {
        provider_id = providers[0].id
        action_id = providers[0].actions[0]?.id || ''
        reset_inputs()
      }
    } catch (error) {
      load_error = error instanceof Error ? error.message : String(error)
    } finally {
      loading = false
    }
  }

  function select_provider(next_provider_id: string) {
    provider_id = next_provider_id
    const provider = providers.find((item) => item.id === next_provider_id)
    action_id = provider?.actions[0]?.id || ''
    result = null
    reset_inputs()
  }

  function select_action(next_action_id: string) {
    action_id = next_action_id
    result = null
    reset_inputs()
  }

  function reset_inputs() {
    const next_inputs: Record<string, any> = {}
    for (const field of active_action?.fields || []) {
      next_inputs[field.id] = field.type === 'checkbox'
          ? field.default !== 'false'
          : field.default || ''
    }
    inputs = next_inputs
  }

  function set_input(field_id: string, value: any) {
    inputs = { ...inputs, [field_id]: value }
  }

  async function run_action() {
    if (!active_provider || !active_action) return
    running = true
    result = null
    try {
      result = await api.post('/run', {
        provider: active_provider.id,
        action: active_action.id,
        inputs
      })
    } catch (error) {
      result = {
        ok: false,
        error: {
          type: error?.constructor?.name || 'Error',
          message: error instanceof Error ? error.message : String(error)
        }
      }
    } finally {
      running = false
    }
  }
</script>

<main class="shell">
  <aside class="sidebar">
    <div class="brand">
      <span>{copy('brand_label', 'Integration Lab')}</span>
      <strong>{app_name}</strong>
    </div>

    <div class="health">
      <span class:online={health?.status === 'ok'}></span>
      <div>
        <strong>{health?.status || 'loading'}</strong>
        <small>{copy('health_summary', '{providers} integrations · {actions} actions').replace('{providers}', String(providers.length)).replace('{actions}', String(ok_count))}</small>
      </div>
    </div>

    <nav aria-label={copy('integrations_aria', 'Integrations')}>
      {#each providers as provider (provider.id)}
        <button
          type="button"
          class:active={provider.id === provider_id}
          onclick={() => select_provider(provider.id)}
        >
          <strong>{provider.label}</strong>
          <small>{copy('actions_count', '{count} actions').replace('{count}', String(provider.actions.length))}</small>
        </button>
      {/each}
    </nav>
  </aside>

  <section class="workspace">
    {#if loading}
      <div class="empty-state">{copy('loading_catalog', 'Loading integration catalog...')}</div>
    {:else if load_error}
      <div class="empty-state error">{load_error}</div>
    {:else if active_provider && active_action}
      <header class="topbar">
        <div>
          <span>{active_provider.label}</span>
          <h1>{active_action.label}</h1>
          <p>{active_action.description}</p>
        </div>
        <button type="button" class="refresh" onclick={load_catalog}>{copy('refresh_button', 'Refresh')}</button>
      </header>

      <div class="action-strip" aria-label={copy('actions_aria', 'Actions')}>
        {#each active_provider.actions as action (action.id)}
          <button
            type="button"
            class:active={action.id === action_id}
            onclick={() => select_action(action.id)}
          >
            {action.label}
            {#if action.side_effect}
              <span>{copy('changes_data', 'changes data')}</span>
            {/if}
          </button>
        {/each}
      </div>

      <div class="content-grid">
        <form class="panel" onsubmit={(event) => { event.preventDefault(); run_action(); }}>
          <div class="panel-heading">
            <h2>{copy('inputs_title', 'Inputs')}</h2>
            <p>{active_provider.description}</p>
          </div>

          {#if active_action.fields.length}
            <div class="fields">
              {#each active_action.fields as field (field.id)}
                <label>
                  <span>{field.label}{field.required ? ' *' : ''}</span>
                  {#if field.type === 'checkbox'}
                    <input
                      type="checkbox"
                      checked={Boolean(inputs[field.id])}
                      onchange={(event) => set_input(field.id, event.currentTarget.checked)}
                    />
                  {:else if field.type === 'textarea'}
                    <textarea
                      value={inputs[field.id] || ''}
                      placeholder={field.placeholder || ''}
                      oninput={(event) => set_input(field.id, event.currentTarget.value)}
                    ></textarea>
                  {:else}
                    <input
                      type={field.type === 'number' ? 'number' : 'text'}
                      value={inputs[field.id] || ''}
                      placeholder={field.placeholder || ''}
                      oninput={(event) => set_input(field.id, event.currentTarget.value)}
                    />
                  {/if}
                  {#if field.description}
                    <small>{field.description}</small>
                  {/if}
                </label>
              {/each}
            </div>
          {:else}
            <div class="no-inputs">{copy('no_inputs', 'This action does not require inputs.')}</div>
          {/if}

          {#if active_action.side_effect}
            <div class="warning">
              {copy('side_effect_warning', 'This action can create or modify provider-side data. Use a test account when possible.')}
            </div>
          {/if}

          <div class="run-row">
            <button type="submit" disabled={running}>
              {running ? copy('running', 'Running...') : copy('run_action', 'Run action')}
            </button>
            <button type="button" class="secondary" onclick={reset_inputs}>{copy('reset_inputs', 'Reset inputs')}</button>
          </div>
        </form>

        <section class="panel">
          <div class="panel-heading">
            <h2>{copy('request_title', 'Request')}</h2>
            <p>{copy('request_hint', 'Payload sent to backend/main.py.')}</p>
          </div>
          <pre>{request_preview}</pre>
        </section>

        <section class="panel result-panel">
          <div class="panel-heading">
            <h2>{copy('result_title', 'Result')}</h2>
            <p>{copy('result_hint', 'Successful responses and integration errors are shown here.')}</p>
          </div>
          {#if result}
            <div class:success={result.ok} class:failure={!result.ok} class="status-line">
              {result.ok ? copy('success', 'Success') : copy('error', 'Error')}
            </div>
            <pre>{result_text}</pre>
          {:else}
            <div class="no-inputs">{copy('run_to_see_response', 'Run an action to see the response.')}</div>
          {/if}
        </section>
      </div>
    {:else}
      <div class="empty-state">{copy('no_integrations', 'No integrations found.')}</div>
    {/if}
  </section>
</main>

<style>
  :global(*) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    font-family: var(--font-family, Inter, system-ui, sans-serif);
    color: var(--ink-color, #16202a);
    background: var(--page-background, #eef3f7);
  }

  button,
  input,
  textarea {
    font: inherit;
  }

  .shell {
    min-height: 100vh;
    display: grid;
    grid-template-columns: 280px minmax(0, 1fr);
  }

  .sidebar {
    background: var(--sidebar-background, #17212c);
    color: #f8fbfd;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .brand {
    display: grid;
    gap: 0.25rem;
    padding: 0.75rem;
  }

  .brand span,
  .topbar span,
  .health small,
  nav small,
  .panel-heading p,
  label small {
    color: var(--muted-ink-color, #6e7d8e);
    font-size: 0.78rem;
  }

  .brand span {
    color: #9eb0c0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .brand strong {
    font-size: 1.2rem;
  }

  .health {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
  }

  .health > span {
    width: 10px;
    height: 10px;
    border-radius: 999px;
    background: #c44747;
  }

  .health > span.online {
    background: #39c078;
  }

  .health div {
    display: grid;
    gap: 0.1rem;
  }

  .health small {
    color: #9eb0c0;
  }

  nav {
    display: grid;
    gap: 0.45rem;
    overflow: auto;
  }

  nav button,
  .action-strip button {
    border: 1px solid transparent;
    background: transparent;
    text-align: left;
    cursor: pointer;
  }

  nav button {
    display: grid;
    gap: 0.15rem;
    color: #f8fbfd;
    border-radius: 8px;
    padding: 0.75rem;
  }

  nav button:hover,
  nav button.active {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.12);
  }

  nav small {
    color: #9eb0c0;
  }

  .workspace {
    padding: var(--page-padding, 1.25rem);
    display: grid;
    align-content: start;
    gap: 1rem;
  }

  .topbar {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: start;
  }

  .topbar h1 {
    margin: 0.15rem 0 0.35rem;
    font-size: 1.55rem;
  }

  .topbar p,
  .panel-heading p {
    margin: 0;
  }

  .topbar span {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent-color, #286b7f);
  }

  .refresh,
  .run-row button {
    border: 0;
    border-radius: 8px;
    padding: 0.65rem 0.9rem;
    color: #fff;
    background: var(--accent-color, #286b7f);
    cursor: pointer;
  }

  .refresh {
    background: var(--panel-background, #ffffff);
    color: var(--ink-color, #16202a);
    border: 1px solid var(--border-color, #d6e0e8);
  }

  .action-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .action-strip button {
    min-height: 42px;
    border-radius: 8px;
    padding: 0.55rem 0.75rem;
    background: var(--panel-background, #ffffff);
    border-color: var(--border-color, #d6e0e8);
    display: flex;
    align-items: center;
    gap: 0.45rem;
  }

  .action-strip button.active {
    border-color: var(--accent-color, #286b7f);
    color: var(--accent-color, #286b7f);
  }

  .action-strip span {
    font-size: 0.68rem;
    padding: 0.16rem 0.35rem;
    border-radius: 999px;
    background: #fff4df;
    color: #8a5b00;
  }

  .content-grid {
    display: grid;
    grid-template-columns: minmax(280px, 0.92fr) minmax(300px, 1fr);
    gap: 1rem;
    align-items: start;
  }

  .panel {
    background: var(--panel-background, #ffffff);
    border: 1px solid var(--border-color, #d6e0e8);
    border-radius: var(--panel-radius, 8px);
    padding: 1rem;
    display: grid;
    gap: 1rem;
    min-width: 0;
  }

  .result-panel {
    grid-column: 1 / -1;
  }

  .panel-heading h2 {
    margin: 0 0 0.25rem;
    font-size: 1rem;
  }

  .fields {
    display: grid;
    gap: 0.85rem;
  }

  label {
    display: grid;
    gap: 0.35rem;
    font-weight: 650;
  }

  input,
  textarea {
    width: 100%;
    border: 1px solid var(--border-color, #d6e0e8);
    border-radius: 8px;
    padding: 0.65rem 0.75rem;
    background: var(--field-background, #fbfdfe);
    color: var(--ink-color, #16202a);
  }

  textarea {
    min-height: 110px;
    resize: vertical;
  }

  .warning,
  .no-inputs,
  .empty-state {
    border-radius: 8px;
    padding: 0.85rem;
    background: var(--soft-panel, #f2f6f8);
    color: var(--muted-ink-color, #6e7d8e);
  }

  .warning {
    background: #fff7e8;
    color: #805600;
  }

  .run-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
  }

  .run-row button:disabled {
    opacity: 0.65;
    cursor: wait;
  }

  .run-row .secondary {
    background: var(--soft-panel, #f2f6f8);
    color: var(--ink-color, #16202a);
  }

  pre {
    margin: 0;
    overflow: auto;
    max-height: 480px;
    border-radius: 8px;
    background: #101820;
    color: #d9f3ff;
    padding: 1rem;
    font-size: 0.82rem;
    line-height: 1.55;
  }

  .status-line {
    width: fit-content;
    border-radius: 999px;
    padding: 0.25rem 0.6rem;
    font-size: 0.78rem;
    font-weight: 700;
  }

  .status-line.success {
    background: #e6f7ee;
    color: #20784a;
  }

  .status-line.failure,
  .empty-state.error {
    background: #fff0f0;
    color: #a92d2d;
  }

  @media (max-width: 900px) {
    .shell {
      grid-template-columns: 1fr;
    }

    .sidebar {
      max-height: none;
    }

    nav {
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    }

    .content-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
