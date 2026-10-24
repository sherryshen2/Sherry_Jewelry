<script lang="ts">
	// @ts-nocheck
	import data from '$data'
	import { navigate } from '../lib/navigation'
	import { smart_api } from '../lib/smart-api'
	let fields = $state([]), values = $state({}), files = $state({}), title = $state(''), saving = $state(false), error = $state('')
	data.smart_workflow_input_fields.subscribe((items) => fields = [...items].sort((a, b) => (a.order || 0) - (b.order || 0)))
	function update(name, value) { values = { ...values, [name]: value } }
	function choose_file(name, event, multiple = false) {
		const selection = event.currentTarget.files
		files = { ...files, [name]: multiple ? Array.from(selection || []) : selection?.[0] || null }
	}
	async function file_data_url(file) { return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = reject; reader.readAsDataURL(file) }) }
	async function persist_file(field, file) {
		const record = await data.smart_workflow_task_files.create({
			field_name: field.name,
			file,
			original_name: file.name,
			mime_type: file.type || 'application/octet-stream',
			size_bytes: file.size,
			created_at: new Date().toISOString()
		})
		return { record_id: record.id, field_name: field.name, asset_filename: record.file, original_name: file.name, mime_type: file.type || 'application/octet-stream', size_bytes: file.size }
	}
	function value_for(field) { return values[field.name] === undefined ? field.default_value : values[field.name] }
	function is_json_field(type) { return ['object', 'array_string', 'array_number', 'array_integer', 'array_boolean', 'array_object', 'array_array_string'].includes(type) }
	function placeholder_for(field) {
		if (field.placeholder) return field.placeholder
		if (field.type === 'object') return '{"key": "value"}'
		if (field.type === 'array_string') return '["value-a", "value-b"]'
		if (field.type === 'array_number') return '[1.5, 2, 3]'
		if (field.type === 'array_integer') return '[1, 2, 3]'
		if (field.type === 'array_boolean') return '[true, false]'
		if (field.type === 'array_object') return '[{"key": "value"}]'
		if (field.type === 'array_array_string') return '[["a", "b"], ["c"]]'
		return ''
	}
	function parse_json_value(field, value) {
		if (typeof value !== 'string' || !value.trim()) return value
		try { return JSON.parse(value) } catch { error = `${field.label || field.name} must be valid JSON`; return undefined }
	}
	function selected_files(field) {
		const selected = files[field.name]
		return Array.isArray(selected) ? selected : selected ? [selected] : []
	}
	function file_size(size) {
		if (!size) return '0 B'
		const units = ['B', 'KB', 'MB', 'GB']
		const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1)
		return `${(size / (1024 ** index)).toFixed(index ? 1 : 0)} ${units[index]}`
	}
	async function submit() {
		error = ''; const input_variables = {}, file_assets = []
		for (const field of fields) {
			let value = value_for(field)
			if (field.type === 'file' && files[field.name]) {
				file_assets.push(await persist_file(field, files[field.name]))
				value = await file_data_url(files[field.name])
			}
			if (field.type === 'array_file' && Array.isArray(files[field.name]) && files[field.name].length) {
				for (const file of files[field.name]) file_assets.push(await persist_file(field, file))
				value = await Promise.all(files[field.name].map(file_data_url))
			}
			if (field.type === 'object' || is_json_field(field.type)) {
				value = parse_json_value(field, value)
				if (error) return
			}
			if (field.type === 'number' && typeof value === 'string' && value.trim()) {
				value = Number(value)
				if (Number.isNaN(value)) { error = `${field.label || field.name} must be a valid number`; return }
			}
			if (field.type === 'integer' && typeof value === 'string' && value.trim()) {
				value = Number(value)
				if (!Number.isInteger(value)) { error = `${field.label || field.name} must be a valid integer`; return }
			}
			if (field.required && (value === undefined || value === null || value === '')) { error = `${field.label || field.name} is required`; return }
			if (field.required && field.type === 'array_file' && (!Array.isArray(value) || !value.length)) { error = `${field.label || field.name} is required`; return }
			if (value !== undefined && value !== null && value !== '') input_variables[field.name] = value
		}
		saving = true; try {
			const { task } = await smart_api.create_task({ title: title.trim(), input_variables, file_assets })
			await Promise.all(file_assets.map((item) => data.smart_workflow_task_files.update(item.record_id, { task_id: task.id })))
			navigate(`/?task=${encodeURIComponent(task.id)}`)
		} catch (err) { error = err instanceof Error ? err.message : String(err) } finally { saving = false }
	}
</script>
<section class="page">
	<button class="back" onclick={() => navigate('/')}>← Back to tasks</button>
	<div class="hero">
		<div><p class="eyebrow">New SMART execution</p><h2>Run this workflow</h2><p>Provide the workflow inputs below. We’ll save uploaded files as Hangar assets, then keep this run’s progress and output in one task.</p></div>
		<aside><span class="dot"></span><strong>Async workflow</strong><small>Track it from the task list</small></aside>
	</div>
	<form onsubmit={(event) => { event.preventDefault(); void submit() }}>
		<section class="panel run-name">
			<div class="section-title"><div class="step">1</div><div><h3>Name this run</h3><p>Optional, but helpful when comparing tasks later.</p></div></div>
			<label class="field"><span>Task title <em>Optional</em></span><input value={title} placeholder="e.g. Daily reconciliation run" oninput={(event) => title = event.currentTarget.value} /></label>
		</section>
		<section class="panel">
			<div class="section-title"><div class="step">2</div><div><h3>Workflow inputs</h3><p>Fields marked <b>*</b> are required by the SMART workflow.</p></div></div>
			<div class="fields">
				{#each fields as field (field.id)}
					<div class:wide={field.type === 'object' || is_json_field(field.type)} class="field-group">
						<div class="field-label"><label for={`input-${field.id}`}>{field.label || field.name}{field.required ? ' *' : ''}</label><code>{field.type?.replaceAll('_', ' ') || 'string'}</code></div>
						{#if field.description}<p class="help">{field.description}</p>{/if}
						{#if field.type === 'boolean'}
							<label class="boolean-control"><input id={`input-${field.id}`} type="checkbox" checked={Boolean(value_for(field))} onchange={(event) => update(field.name, event.currentTarget.checked)} /><span class="checkbox"></span><span>{Boolean(value_for(field)) ? 'Enabled' : 'Disabled'}</span></label>
						{:else if field.type === 'file' || field.type === 'array_file'}
							<label class="upload-zone" for={`input-${field.id}`}><input id={`input-${field.id}`} type="file" multiple={field.type === 'array_file'} required={field.required} onchange={(event) => choose_file(field.name, event, field.type === 'array_file')} /><span class="upload-icon">↑</span><span><b>Choose {field.type === 'array_file' ? 'files' : 'a file'}</b><small>Stored securely with this task</small></span></label>
							{#if selected_files(field).length}<div class="file-list">{#each selected_files(field) as file (file.name)}<div><span>▣</span><b>{file.name}</b><small>{file_size(file.size)}</small></div>{/each}</div>{/if}
						{:else if field.type === 'number' || field.type === 'integer'}
							<input id={`input-${field.id}`} type="number" step={field.type === 'integer' ? '1' : 'any'} value={value_for(field) ?? ''} placeholder={field.placeholder || 'Enter a value'} required={field.required} oninput={(event) => update(field.name, event.currentTarget.value)} />
						{:else if field.type === 'object' || is_json_field(field.type)}
							<textarea id={`input-${field.id}`} placeholder={placeholder_for(field)} value={value_for(field) === undefined || value_for(field) === null ? '' : typeof value_for(field) === 'string' ? value_for(field) : JSON.stringify(value_for(field), null, 2)} required={field.required} oninput={(event) => update(field.name, event.currentTarget.value)}></textarea>
						{:else}
							<input id={`input-${field.id}`} value={value_for(field) ?? ''} placeholder={field.placeholder || `Enter ${field.label || field.name}`} required={field.required} oninput={(event) => update(field.name, event.currentTarget.value)} />
						{/if}
					</div>
				{/each}
			</div>
			{#if !fields.length}<p class="notice">No input fields were imported. Add fields in Configuration, then return here.</p>{/if}
		</section>
		{#if error}<p class="error">{error}</p>{/if}
		<footer class="submit-bar"><div><strong>Ready to run?</strong><span>SMART will execute asynchronously after you submit.</span></div><div class="actions"><button class="secondary" type="button" onclick={() => navigate('/')}>Cancel</button><button class="primary" disabled={saving || !fields.length}>{saving ? 'Saving assets & starting…' : 'Run workflow →'}</button></div></footer>
	</form>
</section>
<style>
.page { width:min(920px,100%); margin:0 auto; display:grid; gap:1.25rem; }.back { width:fit-content; padding:0; color:var(--accent-color,#3159db); background:transparent; font-weight: 600; }.hero { display:flex; justify-content:space-between; gap:2rem; align-items:end; padding:1.5rem 0 .25rem; }.hero h2,.hero p,h3 { margin:0; }.hero h2 { margin-top:.28rem; font-size:clamp(1.8rem,4vw,2.55rem); letter-spacing:-.045em; }.hero p { max-width:620px; margin-top:.5rem; color:var(--muted-ink-color,#637083); line-height:1.55; }.eyebrow { color:var(--accent-color,#3159db)!important; font-size:.76rem; font-weight: 650; letter-spacing:.09em; text-transform:uppercase; }.hero aside { min-width:150px; display:grid; gap:.25rem; padding:.85rem 1rem; border:1px solid #cfe3d9; border-radius:12px; color:#1c6d4b; background:#f0fbf5; font-size:.83rem; }.hero aside small { color:#4c7f67; }.dot { width:8px; height:8px; border-radius:50%; background:#25a36c; box-shadow:0 0 0 4px #d9f5e6; }.panel { margin-top:1rem; padding:1.35rem; border:1px solid var(--border-color,#dbe2ec); border-radius:16px; background:var(--panel-background,#fff); box-shadow:0 1px 2px rgb(16 24 40 / .03); }.section-title { display:flex; gap:.75rem; align-items:flex-start; margin-bottom:1.25rem; }.step { display:grid; width:27px; height:27px; place-items:center; border-radius:50%; color:white; background:var(--accent-color,#3159db); font-size:.78rem; font-weight: 650; }.section-title h3 { font-size:1rem; }.section-title p,.help { margin:.2rem 0 0; color:var(--muted-ink-color,#637083); font-size:.86rem; line-height:1.45; }.section-title b { color:var(--danger-color,#cc3b45); }.field { display:grid; gap:.45rem; max-width:610px; font-weight: 600; }.field span, .field-label label { font-size:.9rem; font-weight: 600; }.field em { margin-left:.25rem; color:var(--muted-ink-color,#637083); font-style:normal; font-size:.78rem; font-weight:500; }.fields { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem 1.1rem; }.field-group { display:grid; align-content:start; gap:.42rem; min-width:0; }.field-group.wide { grid-column:1 / -1; }.field-label { display:flex; justify-content:space-between; gap:.5rem; align-items:center; }.field-label code { padding:.18rem .38rem; border-radius:5px; color:#52647e; background:#edf2f8; font-size:.68rem; text-transform:capitalize; }input,textarea { box-sizing:border-box; width:100%; border:1px solid #d6dee9; border-radius:9px; padding:.72rem .8rem; color:var(--ink-color,#172033); background:#fff; font:inherit; transition:border .15s,box-shadow .15s; }input:focus,textarea:focus { outline:0; border-color:var(--accent-color,#3159db); box-shadow:0 0 0 3px color-mix(in srgb,var(--accent-color,#3159db) 13%,transparent); }textarea { min-height:138px; resize:vertical; font:.83rem/1.55 ui-monospace,SFMono-Regular,Menlo,monospace; }.boolean-control { display:flex; align-items:center; gap:.55rem; min-height:43px; padding:0 .1rem; color:#43536b; font-size:.88rem; cursor:pointer; }.boolean-control input { position:absolute; width:1px; opacity:0; }.checkbox { width:36px; height:21px; border-radius:99px; background:#cbd5e1; transition:.15s; }.checkbox::after { display:block; width:17px; height:17px; margin:2px; border-radius:50%; background:#fff; box-shadow:0 1px 2px #64748b66; content:''; transition:.15s; }.boolean-control input:checked + .checkbox { background:var(--accent-color,#3159db); }.boolean-control input:checked + .checkbox::after { transform:translateX(15px); }.upload-zone { display:flex; align-items:center; gap:.7rem; min-height:58px; padding:.5rem .7rem; border:1px dashed #aab9cc; border-radius:10px; color:#40516b; background:#fafcff; cursor:pointer; }.upload-zone:hover { border-color:var(--accent-color,#3159db); background:#f6f8ff; }.upload-zone input { position:absolute; width:1px; opacity:0; }.upload-zone b,.upload-zone small { display:block; }.upload-zone b { font-size:.85rem; }.upload-zone small { margin-top:.1rem; color:var(--muted-ink-color,#637083); font-size:.74rem; }.upload-icon { display:grid; width:30px; height:30px; place-items:center; border-radius:8px; color:var(--accent-color,#3159db); background:#e8eeff; font-size:1.15rem; font-weight: 650; }.file-list { display:grid; gap:.35rem; }.file-list div { display:flex; gap:.45rem; align-items:center; padding:.42rem .55rem; border-radius:7px; color:#40516b; background:#f4f7fa; font-size:.78rem; }.file-list div span { color:var(--accent-color,#3159db); }.file-list small { margin-left:auto; color:#708098; }.submit-bar { position:sticky; bottom:1rem; display:flex; justify-content:space-between; gap:1rem; align-items:center; margin-top:1rem; padding:1rem 1.15rem; border:1px solid #d7e0ec; border-radius:14px; background:color-mix(in srgb,#fff 92%,transparent); box-shadow:0 8px 28px rgb(22 34 56 / .12); backdrop-filter:blur(10px); }.submit-bar strong,.submit-bar span { display:block; }.submit-bar span { margin-top:.17rem; color:var(--muted-ink-color,#637083); font-size:.8rem; }.actions { display:flex; justify-content:flex-end; gap:.6rem; }button { border:0; border-radius:8px; padding:.68rem .9rem; color:white; background:var(--accent-color,#3159db); font:inherit; font-weight: 650; cursor:pointer; }button:disabled { cursor:not-allowed; opacity:.65; }.secondary { color:#40516b; background:#edf2f7; }.primary { padding-inline:1.1rem; box-shadow:0 3px 8px color-mix(in srgb,var(--accent-color,#3159db) 30%,transparent); }.error,.notice { margin:1rem 0 0; padding:.8rem .9rem; border-radius:9px; }.error { border:1px solid #f3c5ca; color:var(--danger-color,#cc3b45); background:#fff5f6; }.notice { color:var(--muted-ink-color,#637083); background:#f4f6f8; }@media(max-width:640px){.hero,.submit-bar{align-items:stretch;flex-direction:column;}.hero aside{min-width:0;}.fields{grid-template-columns:1fr;}.field-group.wide{grid-column:auto;}.submit-bar{position:static;}.actions{justify-content:stretch;}.actions button{flex:1;}}
</style>
