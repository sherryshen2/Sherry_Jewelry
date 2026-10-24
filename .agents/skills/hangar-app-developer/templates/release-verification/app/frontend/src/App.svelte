<script lang="ts">
  // @ts-nocheck
  import content from '$content'
  import data from '$data'
  import { api, asset, auth, language } from '$hangarkit'

  let releases = $state<any[]>([])
  let verifications = $state<any[]>([])
  let release_name = $state('')
  let notes = $state('')
  let canary_verified = $state(false)
  let logs_verified = $state(false)
  let grafana_verified = $state(false)
  let canary_files = $state<File[]>([])
  let logs_files = $state<File[]>([])
  let grafana_files = $state<File[]>([])
  let current_user = $state<any>(null)
  let summary = $state('')
  let saving = $state(false)
  let last_loaded_key = $state('')
  let language_id = $state('en')

  language.subscribe((value) => {
    language_id = value.id || 'en'
  })

  const point_defs = $derived([
    { key: 'canary', label: copy('canary', 'Canary'), field: 'canary_screenshots' },
    { key: 'logs', label: copy('logs', 'Logs'), field: 'logs_screenshots' },
    { key: 'grafana', label: copy('grafana', 'Released Grafana'), field: 'grafana_screenshots' }
  ])

  data.releases.subscribe((items) => {
    releases = [...items].sort((a, b) => String(b.version || '').localeCompare(String(a.version || '')))
    if (!release_name && releases.length) release_name = releases[0].version
  })

  data.verifications.subscribe((items) => {
    verifications = [...items].sort((a, b) => String(b.updated_at || '').localeCompare(String(a.updated_at || '')))
  })

  auth.currentUser().then((user) => {
    current_user = user
  }).catch(() => {})

  $effect(() => {
    void load_summary()
  })

  let normalized_release_name = $derived(release_name.trim())
  let selected_release = $derived.by(() =>
    releases.find((release) => String(release.version || '').toLowerCase() === normalized_release_name.toLowerCase())
  )
  let selected_verification = $derived.by(() => {
    if (!selected_release) return null
    return verifications.find((record) => record.release_id === selected_release.id) || null
  })
  let is_verified = $derived(canary_verified && logs_verified && grafana_verified)
  let user_label = $derived(current_user?.email || current_user?.name || copy('current_user', 'Current user'))
  let total_screenshots = $derived.by(() =>
    verifications.reduce((count, item) =>
      count + asset_list(item.canary_screenshots).length
      + asset_list(item.logs_screenshots).length
      + asset_list(item.grafana_screenshots).length, 0)
  )

  $effect(() => {
    const key = `${selected_release?.id || normalized_release_name}:${selected_verification?.id || 'new'}`
    if (!normalized_release_name || key === last_loaded_key) return
    last_loaded_key = key
    notes = selected_verification?.notes || ''
    canary_verified = Boolean(selected_verification?.canary_verified)
    logs_verified = Boolean(selected_verification?.logs_verified)
    grafana_verified = Boolean(selected_verification?.grafana_verified)
    canary_files = []
    logs_files = []
    grafana_files = []
  })

  function copy(key: string, fallback = '') {
    const packs = content.localized_copy || {}
    return packs[language_id]?.[key] || packs.en?.[key] || content[key] || fallback
  }

  function asset_list(value: any) {
    if (Array.isArray(value)) return value.filter(Boolean)
    return value ? [value] : []
  }

  function point_verified(key: string) {
    if (key === 'canary') return canary_verified
    if (key === 'logs') return logs_verified
    return grafana_verified
  }

  function set_point_verified(key: string, value: boolean) {
    if (key === 'canary') canary_verified = value
    else if (key === 'logs') logs_verified = value
    else grafana_verified = value
  }

  function selected_files(key: string) {
    if (key === 'canary') return canary_files
    if (key === 'logs') return logs_files
    return grafana_files
  }

  function set_point_files(key: string, event: Event) {
    const files = Array.from(event.currentTarget.files || [])
    if (key === 'canary') canary_files = files
    else if (key === 'logs') logs_files = files
    else grafana_files = files
  }

  function proof_files(field: string) {
    return asset_list(selected_verification?.[field])
  }

  async function load_summary() {
    try {
      const result = await api.get('/summary')
      summary = result?.message || ''
    } catch {
      summary = copy('backend_unavailable', 'Backend summary is not available yet.')
    }
  }

  async function ensure_release() {
    if (selected_release) return selected_release
    const version = normalized_release_name
    if (!version) return null
    return await data.releases.create({ version })
  }

  function build_payload(release: any, existing: any) {
    const form = new FormData()
    const payload = {
      release_id: release.id,
      release_version: release.version,
      verifier: user_label,
      notes: notes.trim(),
      canary_verified,
      logs_verified,
      grafana_verified,
      status: is_verified ? copy('verified_label', 'Verified') : copy('not_verified_label', 'Not verified'),
      canary_screenshots: asset_list(existing?.canary_screenshots),
      logs_screenshots: asset_list(existing?.logs_screenshots),
      grafana_screenshots: asset_list(existing?.grafana_screenshots),
      updated_at: new Date().toISOString()
    }
    form.append('_data', JSON.stringify(payload))
    canary_files.forEach((file) => form.append('_file:canary_screenshots', file))
    logs_files.forEach((file) => form.append('_file:logs_screenshots', file))
    grafana_files.forEach((file) => form.append('_file:grafana_screenshots', file))
    return form
  }

  async function save_verification() {
    if (!normalized_release_name || saving) return
    saving = true
    try {
      const release = await ensure_release()
      if (!release) return
      release_name = release.version
      if (!releases.some((item) => item.id === release.id)) releases = [release, ...releases]
      const existing = selected_verification || verifications.find((record) => record.release_id === release.id)
      const payload = build_payload(release, existing)
      const saved = existing
        ? await data.verifications.update(existing.id, payload)
        : await data.verifications.create(payload)
      verifications = existing
        ? verifications.map((record) => record.id === saved.id ? saved : record)
        : [saved, ...verifications]
      canary_files = []
      logs_files = []
      grafana_files = []
      await load_summary()
    } finally {
      saving = false
    }
  }
</script>

<main class="app-shell" aria-label={copy('app_title', '__HANGAR_APP_NAME__')}>
  <section class="workspace">
    <header class="topbar">
      <div>
        <p>{copy('eyebrow', 'Release verification')}</p>
        <h1>{copy('app_title', '__HANGAR_APP_NAME__')}</h1>
        <span>{copy('intro_text', 'Select or create a release, then attach proof for the three required checks.')}</span>
      </div>
      <div class="summary">
        <span>{copy('updated_by_label', 'Updating as')}</span>
        <strong>{user_label}</strong>
      </div>
    </header>

    <section class="release-row" aria-label={copy('release_picker_title', 'Release version')}>
      <label>
        <span>{copy('release_picker_title', 'Release version')}</span>
        <input
          bind:value={release_name}
          list="release-options"
          placeholder={copy('release_name_placeholder', 'v2.5.0')}
        />
      </label>
      <datalist id="release-options">
        {#each releases as release}
          <option value={release.version}></option>
        {/each}
      </datalist>
      <div class="mini-metrics">
        <span>{releases.length} {copy('metric_releases', 'releases')}</span>
        <span>{verifications.length} {copy('metric_verifications', 'records')}</span>
        <span>{total_screenshots} {copy('metric_screenshots', 'screenshots')}</span>
      </div>
    </section>

    <section class="status-strip" class:verified={is_verified}>
      <strong>{is_verified ? copy('verified_label', 'Verified') : copy('not_verified_label', 'Not verified')}</strong>
      <span>{summary || copy('loading_message', 'Loading release summary...')}</span>
    </section>

    <label class="notes">
      <span>{copy('proof_notes_label', 'Notes')}</span>
      <textarea bind:value={notes} placeholder={copy('proof_notes_placeholder', 'What changed, what was checked, and any remaining risk')}></textarea>
    </label>

    <section class="points" aria-label={copy('points_title', 'Verification points')}>
      {#each point_defs as point}
        <article class="point-card" class:verified={point_verified(point.key)}>
          <header>
            <div>
              <span>{copy('point_label', 'Checkpoint')}</span>
              <h2>{point.label}</h2>
            </div>
            <label class="toggle">
              <input
                type="checkbox"
                checked={point_verified(point.key)}
                onchange={(event) => set_point_verified(point.key, event.currentTarget.checked)}
              />
              <span>{point_verified(point.key) ? copy('verified_label', 'Verified') : copy('not_verified_label', 'Not verified')}</span>
            </label>
          </header>

          <label class="upload">
            <span>{copy('upload_label', 'Upload proof')}</span>
            <input
              type="file"
              accept="image/*"
              multiple
              onchange={(event) => set_point_files(point.key, event)}
            />
            <strong>{selected_files(point.key).length ? `${selected_files(point.key).length} ${copy('selected_suffix', 'selected')}` : copy('upload_hint', 'Choose screenshots')}</strong>
          </label>

          {#if proof_files(point.field).length}
            <div class="proof-grid">
              {#each proof_files(point.field) as filename}
                <a href={asset(filename, { download: true })} target="_blank" rel="noreferrer">
                  <img src={asset(filename, { thumb: '320x200' })} alt={`${point.label} proof`} />
                </a>
              {/each}
            </div>
          {/if}
        </article>
      {/each}
    </section>

    <footer class="actions">
      <button type="button" onclick={save_verification} disabled={!normalized_release_name || saving}>
        {saving ? copy('saving_button', 'Saving...') : copy('save_button', 'Save release verification')}
      </button>
    </footer>
  </section>
</main>

<style>
  :global(body) {
    margin: 0;
    background: var(--page-background, #eef3f7);
    color: var(--text-color, #172033);
    font-family: var(--font-family, Inter), ui-sans-serif, system-ui, sans-serif;
  }

  .app-shell {
    min-height: 100vh;
    padding: var(--page-padding, 1.5rem);
  }

  .workspace {
    max-width: 1180px;
    margin: 0 auto;
    display: grid;
    gap: 1rem;
  }

  .topbar,
  .release-row,
  .status-strip,
  .notes,
  .point-card {
    border: 1px solid var(--border-color, #d8e1ea);
    border-radius: var(--surface-radius, 8px);
    background: var(--surface-background, #ffffff);
    box-shadow: var(--surface-shadow, 0 18px 50px rgba(15, 23, 42, 0.08));
  }

  .topbar {
    padding: clamp(1rem, 3vw, 1.75rem);
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-start;
  }

  p,
  h1,
  h2 {
    margin: 0;
  }

  .topbar p,
  label > span,
  .summary span,
  .point-card header span {
    color: var(--accent-color, #256f7c);
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0;
  }

  h1 {
    margin-top: 0.35rem;
    font-size: clamp(1.8rem, 4vw, 3rem);
    line-height: 1;
  }

  .topbar span,
  .status-strip span,
  .mini-metrics,
  .upload strong {
    color: var(--muted-text-color, #5d6b82);
  }

  .summary {
    min-width: 210px;
    padding: 0.8rem;
    border-radius: var(--control-radius, 6px);
    background: var(--panel-background, #f8fafc);
  }

  .summary strong {
    display: block;
    margin-top: 0.25rem;
    overflow-wrap: anywhere;
  }

  .release-row {
    padding: 1rem;
    display: grid;
    grid-template-columns: minmax(240px, 1fr) auto;
    gap: 1rem;
    align-items: end;
  }

  label,
  .notes {
    display: grid;
    gap: 0.4rem;
  }

  input,
  textarea,
  button {
    font: inherit;
  }

  input,
  textarea {
    width: 100%;
    box-sizing: border-box;
    border: 1px solid var(--border-color, #d8e1ea);
    border-radius: var(--control-radius, 6px);
    background: #ffffff;
    color: var(--text-color, #172033);
    padding: 0.75rem 0.8rem;
  }

  textarea {
    min-height: 104px;
    resize: vertical;
  }

  .mini-metrics {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    justify-content: flex-end;
    font-size: 0.85rem;
  }

  .mini-metrics span {
    padding: 0.5rem 0.65rem;
    border-radius: var(--control-radius, 6px);
    background: var(--panel-background, #f8fafc);
  }

  .status-strip {
    padding: 1rem;
    border-left: 12px solid var(--danger-color, #c2414b);
    background: var(--unverified-background, #fde8e8);
  }

  .status-strip.verified {
    border-left-color: var(--success-color, #2f8f62);
    background: var(--verified-background, #e6f6ed);
  }

  .status-strip strong {
    display: block;
    margin-bottom: 0.25rem;
    font-size: 1.1rem;
  }

  .notes {
    padding: 1rem;
  }

  .points {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
  }

  .point-card {
    display: grid;
    gap: 1rem;
    padding: 1rem;
    border-left: 12px solid var(--danger-color, #c2414b);
    background: var(--unverified-background, #fde8e8);
  }

  .point-card.verified {
    border-left-color: var(--success-color, #2f8f62);
    background: var(--verified-background, #e6f6ed);
  }

  .point-card header {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
  }

  .point-card h2 {
    margin-top: 0.25rem;
    font-size: 1.2rem;
  }

  .toggle {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    justify-self: end;
    white-space: nowrap;
  }

  .toggle input {
    width: 20px;
    height: 20px;
    accent-color: var(--success-color, #2f8f62);
  }

  .upload {
    padding: 0.8rem;
    border: 1px dashed color-mix(in srgb, var(--border-color, #d8e1ea) 70%, var(--text-color, #172033));
    border-radius: var(--control-radius, 6px);
    background: rgba(255, 255, 255, 0.6);
  }

  .upload input {
    padding: 0;
    border: 0;
    background: transparent;
  }

  .proof-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
    gap: 0.5rem;
  }

  .proof-grid a {
    display: block;
    aspect-ratio: 16 / 10;
    overflow: hidden;
    border-radius: var(--control-radius, 6px);
    border: 1px solid var(--border-color, #d8e1ea);
    background: #ffffff;
  }

  .proof-grid img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
  }

  button {
    min-height: 44px;
    border: 0;
    border-radius: var(--control-radius, 6px);
    background: var(--accent-color, #256f7c);
    color: var(--button-text-color, #ffffff);
    font-weight: 800;
    padding: 0.75rem 1.1rem;
    cursor: pointer;
  }

  button:disabled {
    cursor: not-allowed;
    opacity: 0.55;
  }

  @media (max-width: 920px) {
    .topbar,
    .point-card header {
      flex-direction: column;
    }

    .release-row,
    .points {
      grid-template-columns: 1fr;
    }

    .mini-metrics {
      justify-content: flex-start;
    }
  }
</style>
