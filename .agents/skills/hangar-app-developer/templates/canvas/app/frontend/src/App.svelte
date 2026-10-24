<script>
  // @ts-nocheck
	import Icon from "@iconify/svelte";
	import { asset, language, proxy } from "$hangarkit";
	import content from "$content";
	import data from "$data";
	import { tick } from "svelte";
	import { fade } from "svelte/transition";
	import { flip } from "svelte/animate";

	let notes = $state([]);
	let deleted_notes = $state([]);
	let loading = $state(true);
	let editing_id = $state(null);
	let show_type_picker = $state(false);
	let show_trash = $state(false);
	let search = $state("");
	let fetching_og = $state(false);
	let language_id = $state("en");
	let image_uploading = $state(false);
	let image_upload_error = $state("");

	let dragging_id = $state(null);
	let drag_over_id = $state(null);
	let drag_position = $state(null);

	language.subscribe((value) => {
		language_id = value.id || "en";
	});

	function t(key, fallback = "") {
		const packs = content.localized_copy || {};
		return packs[language_id]?.[key] || packs.en?.[key] || content[key] || fallback;
	}

	$effect(() => {
		const unsubscribe = data.notes.subscribe((items) => {
			const snapshot = $state.snapshot(items);
			const seen = new Set();
			notes = snapshot.filter((n) => {
				if (seen.has(n.id)) return false;
				seen.add(n.id);
				return true;
			});
			loading = false;
		});
		return unsubscribe;
	});

	$effect(() => {
		const unsubscribe = data.deleted_notes.subscribe((items) => {
			const snapshot = $state.snapshot(items);
			const seen = new Set();
			deleted_notes = snapshot.filter((n) => {
				if (seen.has(n.id)) return false;
				seen.add(n.id);
				return true;
			});
		});
		return unsubscribe;
	});

	let filtered_notes = $derived.by(() => {
		const sorted = [...notes].sort((a, b) => {
			if (a.pinned && !b.pinned) return -1;
			if (!a.pinned && b.pinned) return 1;
			if (a.order !== undefined && b.order !== undefined)
				return a.order - b.order;
			return new Date(b.updated) - new Date(a.updated);
		});
		if (!search) return sorted;
		const q = search.toLowerCase();
		return sorted.filter((n) => {
			if (n.title?.toLowerCase().includes(q)) return true;
			if (n.type === "text" && n.body?.toLowerCase().includes(q)) return true;
			if (
				n.type === "checklist" &&
				parse_json(n.items, []).some((i) => i.text.toLowerCase().includes(q))
			)
				return true;
			if (
				n.type === "link" &&
				(n.url?.toLowerCase().includes(q) ||
					n.link_title?.toLowerCase().includes(q))
			)
				return true;
			if (n.type === "embed" && n.embed_code?.toLowerCase().includes(q))
				return true;
			return false;
		});
	});

	let trash_count = $derived(deleted_notes.length);
	let editing_note = $derived(
		editing_id ? notes.find((n) => n.id === editing_id) : null,
	);

	function parse_json(str, fallback) {
		if (!str) return fallback;
		if (typeof str === "object") return str;
		try {
			return JSON.parse(str);
		} catch {
			return fallback;
		}
	}

	async function fetch_og_data(url, noteId) {
		if (!url || fetching_og) return;
		try {
			fetching_og = true;
			const html = await proxy.text(url);
			const doc = new DOMParser().parseFromString(html, "text/html");
			const updates = {};
			const og_image = doc.querySelector('meta[property="og:image"]')?.content;
			const og_title =
				doc.querySelector('meta[property="og:title"]')?.content ||
				doc.querySelector("title")?.textContent;
			const og_desc =
				doc.querySelector('meta[property="og:description"]')?.content ||
				doc.querySelector('meta[name="description"]')?.content;
			if (og_image) updates.link_image = og_image;
			if (og_title) updates.link_title = og_title;
			if (og_desc) updates.link_desc = og_desc;
			if (Object.keys(updates).length > 0 && noteId)
				await update_note(noteId, updates);
		} catch (e) {
			console.warn("Failed to fetch OG data:", e);
		} finally {
			fetching_og = false;
		}
	}

	function handle_url_paste(e, noteId) {
		const pasted = e.clipboardData?.getData("text") || "";
		if (pasted.match(/^https?:\/\//))
			setTimeout(() => fetch_og_data(pasted, noteId), 100);
	}

	async function handle_global_paste(e) {
		if (
			e.target.tagName === "INPUT" ||
			e.target.tagName === "TEXTAREA" ||
			e.target.isContentEditable
		)
			return;
		const pasted = e.clipboardData?.getData("text") || "";
		if (pasted.trim().startsWith("<iframe")) {
			e.preventDefault();
			await create_embed_note(pasted.trim());
		}
	}

	async function create_embed_note(embed_code) {
		const maxOrder = Math.max(0, ...notes.map((n) => n.order ?? 0));
		const created = await data.notes.create({
			type: "embed",
			title: "",
			embed_code,
			order: maxOrder + 1,
			updated: new Date().toISOString(),
			created: new Date().toISOString(),
		});
		await tick();
		editing_id = created.id;
	}

	async function create_note(type) {
		show_type_picker = false;
		const maxOrder = Math.max(0, ...notes.map((n) => n.order ?? 0));
		const base = {
			type,
			title: "",
			order: maxOrder + 1,
			updated: new Date().toISOString(),
			created: new Date().toISOString(),
		};
		let note_data = { ...base };
		if (type === "checklist")
			note_data.items = JSON.stringify([
				{ id: Date.now().toString(), text: "", done: false },
			]);
		if (type === "table")
			note_data.rows = JSON.stringify([
				["", ""],
				["", ""],
			]);
		if (type === "text") note_data.body = "";
		if (type === "link") note_data.url = "";
		if (type === "image") note_data.src = "";
		if (type === "embed") note_data.embed_code = "";
		const created = await data.notes.create(note_data);
		await tick();
		editing_id = created.id;
	}

	async function update_note(id, updates) {
		await data.notes.update(id, {
			...updates,
			updated: new Date().toISOString(),
		});
	}

	async function delete_note(id) {
		const note = notes.find((n) => n.id === id);
		if (!note) return;
		editing_id = null;
		await tick();
		const { id: _, ...noteData } = note;
		await data.deleted_notes.create({
			...noteData,
			deleted_at: new Date().toISOString(),
		});
		await data.notes.delete(id);
	}

	async function restore_note(id) {
		const note = deleted_notes.find((n) => n.id === id);
		if (!note) return;
		const { id: _, deleted_at, ...noteData } = note;
		await data.notes.create({ ...noteData, updated: new Date().toISOString() });
		await data.deleted_notes.delete(id);
	}

	async function permanently_delete(id) {
		await data.deleted_notes.delete(id);
	}

	async function empty_trash() {
		if (
			!confirm("Permanently delete all items in trash? This cannot be undone.")
		)
			return;
		await Promise.all(
			deleted_notes.map((n) => data.deleted_notes.delete(n.id)),
		);
	}

	function handle_keydown(e) {
		if (e.key === "Escape") {
			editing_id = null;
			show_type_picker = false;
			show_trash = false;
		}
	}

	function handle_drag_start(e, noteId) {
		dragging_id = noteId;
		e.dataTransfer.effectAllowed = "move";
		e.dataTransfer.setData("text/plain", noteId);
	}

	function handle_drag_end() {
		dragging_id = null;
		drag_over_id = null;
		drag_position = null;
	}

	function handle_drag_over(e, noteId) {
		e.preventDefault();
		e.dataTransfer.dropEffect = "move";
		if (noteId === dragging_id) return;
		drag_over_id = noteId;
		const rect = e.currentTarget.getBoundingClientRect();
		drag_position = e.clientY < rect.top + rect.height / 2 ? "before" : "after";
	}

	function handle_drag_leave(e) {
		if (!e.currentTarget.contains(e.relatedTarget)) {
			drag_over_id = null;
			drag_position = null;
		}
	}

	async function handle_drop(e, targetNoteId) {
		e.preventDefault();
		if (!dragging_id || dragging_id === targetNoteId) {
			handle_drag_end();
			return;
		}
		const orderedNotes = [...filtered_notes];
		const draggedIndex = orderedNotes.findIndex((n) => n.id === dragging_id);
		const targetIndex = orderedNotes.findIndex((n) => n.id === targetNoteId);
		if (draggedIndex === -1 || targetIndex === -1) {
			handle_drag_end();
			return;
		}
		const [draggedNote] = orderedNotes.splice(draggedIndex, 1);
		let newIndex = targetIndex;
		if (draggedIndex < targetIndex) newIndex--;
		if (drag_position === "after") newIndex++;
		orderedNotes.splice(newIndex, 0, draggedNote);
		await Promise.all(
			orderedNotes.map((note, index) =>
				data.notes.update(note.id, { order: index }),
			),
		);
		handle_drag_end();
	}

	function get_items_for_note(noteId) {
		const note = notes.find((n) => n.id === noteId);
		return note ? parse_json(note.items, []) : [];
	}

	function get_rows_for_note(noteId) {
		const note = notes.find((n) => n.id === noteId);
		return note
			? parse_json(note.rows, [
					["", ""],
					["", ""],
				])
			: [
					["", ""],
					["", ""],
				];
	}

	async function toggle_item(noteId, item_id) {
		const items = get_items_for_note(noteId);
		await update_note(noteId, {
			items: JSON.stringify(
				items.map((i) => (i.id === item_id ? { ...i, done: !i.done } : i)),
			),
		});
	}

	async function update_item_text(noteId, item_id, text) {
		const items = get_items_for_note(noteId);
		await update_note(noteId, {
			items: JSON.stringify(
				items.map((i) => (i.id === item_id ? { ...i, text } : i)),
			),
		});
	}

	async function add_item(noteId) {
		const items = get_items_for_note(noteId);
		await update_note(noteId, {
			items: JSON.stringify([
				...items,
				{ id: Date.now().toString(), text: "", done: false },
			]),
		});
	}

	async function remove_item(noteId, item_id) {
		const items = get_items_for_note(noteId);
		if (items.length > 1)
			await update_note(noteId, {
				items: JSON.stringify(items.filter((i) => i.id !== item_id)),
			});
	}

	async function update_cell(noteId, r, c, val) {
		const rows = get_rows_for_note(noteId);
		await update_note(noteId, {
			rows: JSON.stringify(
				rows.map((row, ri) =>
					ri === r ? row.map((cell, ci) => (ci === c ? val : cell)) : row,
				),
			),
		});
	}

	async function add_row(noteId) {
		const rows = get_rows_for_note(noteId);
		await update_note(noteId, {
			rows: JSON.stringify([...rows, new Array(rows[0]?.length || 2).fill("")]),
		});
	}

	async function add_col(noteId) {
		const rows = get_rows_for_note(noteId);
		await update_note(noteId, {
			rows: JSON.stringify(rows.map((r) => [...r, ""])),
		});
	}

	async function remove_row(noteId, idx) {
		const rows = get_rows_for_note(noteId);
		if (rows.length > 1)
			await update_note(noteId, {
				rows: JSON.stringify(rows.filter((_, i) => i !== idx)),
			});
	}

	async function handle_image_upload(noteId, e) {
		const file = e.target.files?.[0];
		if (!file || image_uploading) return;
		image_uploading = true;
		image_upload_error = "";
		try {
			await update_note(noteId, { image: file, src: "" });
		} catch {
			image_upload_error = t("image_upload_failed", "Image upload failed. Please try again.");
		} finally {
			image_uploading = false;
			e.target.value = "";
		}
	}

	function image_source(note, thumbnail = false) {
		// Keep existing URL/legacy inline images readable; new uploads store filenames.
		return note.image ? asset(note.image, thumbnail ? { thumb: "640x360" } : undefined) : note.src || "";
	}

	function handle_text_keydown(e) {
		if (e.metaKey || e.ctrlKey) {
			if (e.key === "b") {
				e.preventDefault();
				document.execCommand("bold");
			}
			if (e.key === "i") {
				e.preventDefault();
				document.execCommand("italic");
			}
		}
	}

	function handle_checklist_keydown(e, noteId, itemId) {
		if (e.key === "Enter") {
			e.preventDefault();
			const currentLength = get_items_for_note(noteId).length;
			add_item(noteId);
			setTimeout(
				() =>
					document
						.querySelectorAll(".checklist-editor input[type=text]")
						[currentLength]?.focus(),
				50,
			);
		}
		if (e.key === "Backspace" && !e.target.value) {
			const items = get_items_for_note(noteId);
			if (items.length > 1) {
				e.preventDefault();
				remove_item(noteId, itemId);
			}
		}
	}

	let text_editor_el = $state(null);
	let text_editor_initial = $state("");

	$effect(() => {
		if (editing_note?.type === "text")
			text_editor_initial = editing_note.body || "";
	});
	$effect(() => {
		if (
			text_editor_el &&
			editing_note?.type === "text" &&
			text_editor_el.innerHTML !== text_editor_initial
		)
			text_editor_el.innerHTML = text_editor_initial;
	});

	function handle_text_input(e) {
		update_note(editing_id, { body: e.target.innerHTML });
	}

	const type_icons = {
		text: "lucide:file-text",
		checklist: "lucide:check-square",
		link: "lucide:link",
		image: "lucide:image",
		embed: "lucide:code",
		table: "lucide:table",
	};
	function get_type_icon(type) {
		return type_icons[type] || "lucide:file";
	}

	function format_relative_time(dateStr) {
		const diff = new Date() - new Date(dateStr);
		const mins = Math.floor(diff / 60000);
		const hours = Math.floor(diff / 3600000);
		const days = Math.floor(diff / 86400000);
		if (mins < 1) return "Just now";
		if (mins < 60) return `${mins}m ago`;
		if (hours < 24) return `${hours}h ago`;
		if (days < 7) return `${days}d ago`;
		return new Date(dateStr).toLocaleDateString();
	}
</script>

{#snippet iconButton(icon, onclick, className = "", title = "")}
	<button class={className} {onclick} {title}
		><Icon {icon} width={18} /></button>
{/snippet}

{#snippet typePickerButton(type, icon, label)}
	<button onclick={() => create_note(type)}
		><Icon {icon} width={20} /><span>{label}</span></button>
{/snippet}

{#snippet notePreview(note)}
	{@const items = parse_json(note.items, [])}
	{@const rows = parse_json(note.rows, [
		["", ""],
		["", ""],
	])}
	{#if note.type === "text"}
		<div class="card-body text-preview">
			{@html note.body || `<span class="muted">${t("empty_note", "Empty note")}</span>`}
		</div>
	{:else if note.type === "checklist"}
		<div class="card-body checklist-preview">
			{#each items as item}
				<button
					class="check-item-btn"
					class:done={item.done}
					onclick={(e) => {
						e.stopPropagation();
						toggle_item(note.id, item.id);
					}}>
					<Icon
						icon={item.done ? "lucide:check-square" : "lucide:square"}
						width={16} />
					<span>{item.text || t("empty_item", "Empty item")}</span>
				</button>
			{/each}
		</div>
	{:else if note.type === "link"}
		<div class="card-body link-preview">
			{#if note.link_image}<img
					src={note.link_image}
					alt=""
					class="link-img" />{/if}
			<a
				href={note.url}
				target="_blank"
				rel="noopener noreferrer"
				class="link-title"
				onclick={(e) => e.stopPropagation()}
				>{note.link_title || note.url || t("no_url", "No URL")}</a>
			{#if note.link_desc}<div class="link-desc">{note.link_desc}</div>{/if}
		</div>
	{:else if note.type === "image"}
		<div class="card-body image-preview">
			{#if image_source(note)}<img src={image_source(note, true)} alt={note.caption || ""} loading="lazy" decoding="async" />{:else}<div
					class="no-image">
					<Icon icon="lucide:image" width={32} />
				</div>{/if}
			{#if note.caption}<div class="caption">{note.caption}</div>{/if}
		</div>
	{:else if note.type === "table"}
		<div class="card-body table-preview">
			<table>
				{#each rows.slice(0, 4) as row}<tr
						>{#each row.slice(0, 3) as cell}<td>{cell || ""}</td
							>{/each}{#if row.length > 3}<td class="more">...</td>{/if}</tr
					>{/each}
			</table>
			{#if rows.length > 4}<div class="more">+{rows.length - 4} rows</div>{/if}
		</div>
	{:else if note.type === "embed"}
		<div class="card-body embed-preview-active">
			{#if note.embed_code}
				<div class="embed-wrapper">{@html note.embed_code}</div>
			{:else}
				<div class="no-embed">
					<Icon icon="lucide:code" width={32} />
				</div>
			{/if}
		</div>
	{/if}
{/snippet}

{#snippet noteEditor(note)}
	{@const items = parse_json(note.items, [])}
	{@const rows = parse_json(note.rows, [
		["", ""],
		["", ""],
	])}
	{#if note.type === "text"}
		<div
			class="text-editor"
			contenteditable="true"
			bind:this={text_editor_el}
			oninput={handle_text_input}
			onkeydown={handle_text_keydown}
			data-placeholder={t("start_writing", "Start writing... (Cmd+B bold, Cmd+I italic)")}>
		</div>
	{:else if note.type === "checklist"}
		<div class="checklist-editor">
			{#each items as item}
				<div class="check-row">
					<button
						class="check-toggle"
						onclick={() => toggle_item(editing_id, item.id)}
						><Icon
							icon={item.done ? "lucide:check-square" : "lucide:square"}
							width={20} /></button>
					<input
						type="text"
						value={item.text}
						oninput={(e) =>
							update_item_text(editing_id, item.id, e.target.value)}
						onkeydown={(e) => handle_checklist_keydown(e, editing_id, item.id)}
						placeholder="List item..."
						class:done={item.done} />
				</div>
			{/each}
			<button class="add-item" onclick={() => add_item(editing_id)}
				><Icon icon="lucide:plus" width={16} /><span>{t("add_item", "Add item")}</span></button>
		</div>
	{:else if note.type === "link"}
		<div class="link-editor">
			<input
				type="url"
				value={note.url || ""}
				oninput={(e) => update_note(editing_id, { url: e.target.value })}
				onpaste={(e) => handle_url_paste(e, editing_id)}
				placeholder="https://..." />
			<input
				type="text"
				value={note.link_title || ""}
				oninput={(e) => update_note(editing_id, { link_title: e.target.value })}
				placeholder="Link title" />
			<textarea
				value={note.link_desc || ""}
				oninput={(e) => update_note(editing_id, { link_desc: e.target.value })}
				placeholder="Description (optional)"
				rows="2"></textarea>
			<input
				type="url"
				value={note.link_image || ""}
				oninput={(e) => update_note(editing_id, { link_image: e.target.value })}
				placeholder="Preview image URL (optional)" />
		</div>
	{:else if note.type === "image"}
		<div class="image-editor">
			{#if image_source(note)}
				<img src={image_source(note)} alt="" class="preview" />
				<button
					class="remove-img"
					onclick={() => update_note(editing_id, { image: "", src: "" })}
					><Icon icon="lucide:x" width={16} />Remove</button>
			{:else}
				<label class="upload-area"
					><Icon icon="lucide:upload" width={24} /><span>{image_uploading ? t("image_uploading", "Uploading…") : t("image_upload", "Click to upload")}</span
					><input
						type="file"
						accept="image/*"
						disabled={image_uploading}
						onchange={(e) => handle_image_upload(editing_id, e)}
						hidden /></label>
				<div class="or">or</div>
				<input
					type="url"
					value={note.src || ""}
					oninput={(e) => update_note(editing_id, { src: e.target.value })}
					placeholder="Paste image URL" />
			{/if}
			{#if image_upload_error}<p role="alert">{image_upload_error}</p>{/if}
			<input
				type="text"
				value={note.caption || ""}
				oninput={(e) => update_note(editing_id, { caption: e.target.value })}
				placeholder="Caption (optional)"
				class="caption-input" />
		</div>
	{:else if note.type === "table"}
		<div class="table-editor">
			<div class="table-scroll">
				<table>
					<tbody>
						{#each rows as row, ri}
							<tr>
								{#each row as cell, ci}<td
										><input
											type="text"
											value={cell}
											oninput={(e) =>
												update_cell(editing_id, ri, ci, e.target.value)} /></td
									>{/each}
								<td class="row-action"
									><button
										onclick={() => remove_row(editing_id, ri)}
										title="Remove row"
										><Icon icon="lucide:minus" width={14} /></button
									></td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			<div class="table-actions">
				<button onclick={() => add_row(editing_id)}
					><Icon icon="lucide:plus" width={14} /> Row</button>
				<button onclick={() => add_col(editing_id)}
					><Icon icon="lucide:plus" width={14} /> Column</button>
			</div>
		</div>
	{:else if note.type === "embed"}
		<div class="embed-editor">
			<textarea
				value={note.embed_code || ""}
				oninput={(e) => update_note(editing_id, { embed_code: e.target.value })}
				placeholder="Paste iframe embed code here..."
				rows="4"></textarea>
			{#if note.embed_code}
				<div class="embed-preview-frame">{@html note.embed_code}</div>
			{:else}
				<div class="embed-placeholder">
					<Icon icon="lucide:code" width={32} />
					<p>Paste an embed code (iframe) from YouTube, Vimeo, Spotify, etc.</p>
				</div>
			{/if}
		</div>
	{/if}
{/snippet}

{#snippet trashItem(note)}
	<div class="trash-item">
		<div class="trash-item-icon">
			<Icon icon={get_type_icon(note.type)} width={18} />
		</div>
		<div class="trash-item-info">
			<div class="trash-item-title">
				{note.title || `Untitled ${note.type}`}
			</div>
			<div class="trash-item-meta">
				Deleted {format_relative_time(note.deleted_at)}
			</div>
		</div>
		<div class="trash-item-actions">
			<button
				class="restore-btn"
				onclick={() => restore_note(note.id)}
				title="Restore"><Icon icon="lucide:undo-2" width={16} /></button>
			<button
				class="delete-forever-btn"
				onclick={() => permanently_delete(note.id)}
				title={t("delete_forever", "Delete forever")}><Icon icon="lucide:x" width={16} /></button>
		</div>
	</div>
{/snippet}

{#snippet noteCard(note)}
	{@const isDragOver = drag_over_id === note.id}
	<div
		class="card-wrapper"
		class:drag-over-before={isDragOver && drag_position === "before"}
		class:drag-over-after={isDragOver && drag_position === "after"}>
		<div
			class="card"
			class:dragging={dragging_id === note.id}
			draggable="true"
			ondragstart={(e) => handle_drag_start(e, note.id)}
			ondragend={handle_drag_end}
			ondragover={(e) => handle_drag_over(e, note.id)}
			ondragleave={handle_drag_leave}
			ondrop={(e) => handle_drop(e, note.id)}>
			<div class="card-header" style:margin-bottom={note.title ? '0.5rem' : ''}>
				{#if note.title}<div class="card-title">{note.title}</div>{:else}<div>
					</div>{/if} 
				<div class="card-actions">
					{#if note.pinned}
						<div class="pin-indicator">
							<Icon icon="lucide:pin" width={14} />
						</div>
					{/if}
					<button
						class="edit-card-btn"
						onclick={() => (editing_id = note.id)}
						title="Edit">
						<Icon icon="lucide:pencil" width={14} />
					</button>
				</div>
			</div>

			{@render notePreview(note)}
		</div>
	</div>
{/snippet}

<svelte:window onkeydown={handle_keydown} onpaste={handle_global_paste} />

<div class="app">
	<header class="header">
		<div class="app-title">
			<span class="app-icon" aria-hidden="true">
				<Icon icon="mdi:collage-outline" width={24} />
			</span>
			<h1>{t("app_title", "Canvas")}</h1>
		</div>
		<div class="search-wrap">
			<Icon icon="lucide:search" width={18} />
			<input
				type="text"
				bind:value={search}
				placeholder={t("search_placeholder", "Search...")} />
		</div>
		<button class="trash-btn" onclick={() => (show_trash = true)} title={t("trash", "Trash")}>
			<Icon icon="lucide:trash-2" width={20} />
			{#if trash_count > 0}<span class="trash-badge">{trash_count}</span>{/if}
		</button>
	</header>

	<main class="main">
		{#if loading}
			<p class="empty">{t("loading", "Loading...")}</p>
		{:else if filtered_notes.length === 0}
			<p class="empty">{search ? t("no_results", "No notes found") : t("empty", "No notes yet. Tap + to create one.")}</p>
		{:else}
			<div class="masonry">
				{#each filtered_notes as note (note.id)}
					<div in:fade={{ duration: 200 }} animate:flip={{ duration: 200 }}>{@render noteCard(note)}</div>
				{/each}
			</div>
		{/if}
	</main>

	<button class="fab" onclick={() => (show_type_picker = true)}
		><Icon icon="lucide:plus" width={24} /></button>

	{#if show_type_picker}
		<div
			class="overlay"
			role="presentation"
			onclick={() => (show_type_picker = false)}
			transition:fade={{ duration: 100 }}>
			<div class="picker" role="dialog" onclick={(e) => e.stopPropagation()}>
				{@render typePickerButton("text", "lucide:file-text", t("text", "Text"))}
				{@render typePickerButton(
					"checklist",
					"lucide:check-square",
					t("checklist", "Checklist"),
				)}
				{@render typePickerButton("link", "lucide:link", t("link", "Link"))}
				{@render typePickerButton("image", "lucide:image", t("image", "Image"))}
				{@render typePickerButton("table", "lucide:table", t("table", "Table"))}
				{@render typePickerButton("embed", "lucide:code", t("embed", "Embed"))}
			</div>
		</div>
	{/if}

	{#if show_trash}
		<div
			class="overlay"
			role="presentation"
			onclick={() => (show_trash = false)}
			transition:fade={{ duration: 100 }}>
			<div
				class="trash-modal"
				role="dialog"
				onclick={(e) => e.stopPropagation()}>
				<div class="trash-header">
					<h2><Icon icon="lucide:trash-2" width={20} /> {t("trash", "Trash")}</h2>
					{@render iconButton(
						"lucide:x",
						() => (show_trash = false),
						"close-btn",
					)}
				</div>
				<div class="trash-body">
					{#if deleted_notes.length === 0}
						<div class="trash-empty">
							<Icon icon="lucide:trash-2" width={48} />
							<p>{t("trash_empty", "Trash is empty")}</p>
						</div>
					{:else}
						<div class="trash-list">
							{#each deleted_notes as note}{@render trashItem(note)}{/each}
						</div>
					{/if}
				</div>
				{#if deleted_notes.length > 0}
					<div class="trash-footer">
						<button class="empty-trash-btn" onclick={empty_trash}
							><Icon icon="lucide:trash-2" width={16} />{t("empty_trash", "Empty Trash")}</button>
					</div>
				{/if}
			</div>
		</div>
	{/if}

	{#if editing_note}
		<div
			class="overlay"
			role="presentation"
			onclick={() => (editing_id = null)}
			transition:fade={{ duration: 100 }}>
			<div
				class="editor-modal"
				role="dialog"
				onclick={(e) => e.stopPropagation()}>
				<div class="editor-header">
					<input
						type="text"
						class="title-input"
						value={editing_note.title || ""}
						oninput={(e) => update_note(editing_id, { title: e.target.value })}
						placeholder={t("title_placeholder", "Title (optional)")} />
					<button
						class="pin-btn"
						class:pinned={editing_note.pinned}
						onclick={() =>
							update_note(editing_id, { pinned: !editing_note.pinned })}
						title={editing_note.pinned ? t("unpin", "Unpin") : t("pin", "Pin")}>
						<Icon
							icon={editing_note.pinned ? "lucide:pin-off" : "lucide:pin"}
							width={18} />
					</button>
					{@render iconButton(
						"lucide:trash-2",
						() => delete_note(editing_id),
						"delete-btn",
					)}
					{@render iconButton(
						"lucide:x",
						() => (editing_id = null),
						"close-btn",
					)}
				</div>
				<div class="editor-body">{@render noteEditor(editing_note)}</div>
				<div class="editor-footer">
					<span class="last-updated"
						>Edited {format_relative_time(editing_note.updated)}</span>
				</div>
			</div>
		</div>
	{/if}

	<footer class="footer">built with Hangar</footer>
</div>

<style>
  
  .app {
    min-height: 100vh;
    min-height: 100dvh;
    background: var(--page-background);
    font-family: var(--body-font);
    display: flex;
    flex-direction: column;
  }
	.header {
		padding: 24px 24px 16px;
		display: flex;
		align-items: center;
		gap: 16px;
		flex-wrap: wrap;
	}
	.app-title {
		display: flex;
		align-items: center;
		gap: 10px;
		min-width: 0;
	}
	.app-icon {
		width: 40px;
		height: 40px;
		border-radius: 10px;
		background: var(--card-background);
		border: 1px solid var(--border-color);
		color: var(--accent-color);
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
		flex: 0 0 auto;
	}
	.header h1 {
		font-size: 24px;
		font-weight: 700;
		color: var(--heading-color);
		margin: 0;
	}
	.search-wrap {
		display: flex;
		align-items: center;
		gap: 8px;
		background: var(--card-background);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		padding: 8px 12px;
		flex: 1;
		max-width: 300px;
	}
	.search-wrap input {
		border: none;
		background: transparent;
		font-size: 15px;
		color: var(--text-color);
		width: 100%;
	}
	.search-wrap input:focus {
		outline: none;
	}
	.search-wrap input::placeholder {
		color: var(--muted-color);
	}
	.trash-btn {
		position: relative;
		width: 38px;
		height: 38px;
		border: none;
		background: var(--card-background);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		cursor: pointer;
		color: var(--muted-color);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s;
	}
	.trash-btn:hover {
		background: var(--hover-background);
		color: var(--text-color);
	}
	.trash-badge {
		position: absolute;
		top: -6px;
		right: -6px;
		min-width: 18px;
		height: 18px;
		padding: 0 5px;
		background: #ef4444;
		color: white;
		font-size: 11px;
		font-weight: 600;
		border-radius: 9px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
  .main {
    flex: 1;
    padding: 0 24px 100px;
  }
	.empty {
		text-align: center;
		color: var(--muted-color);
		padding: 48px 16px;
	}
	.masonry {
		column-count: 4;
		column-gap: 16px;
	}
	@media (max-width: 1200px) {
		.masonry {
			column-count: 3;
		}
	}
	@media (max-width: 900px) {
		.masonry {
			column-count: 2;
		}
	}
	@media (max-width: 600px) {
		.masonry {
			column-count: 1;
		}
	}
	.card-wrapper {
		position: relative;
		break-inside: avoid;
		margin-bottom: 16px;
	}
	.card-wrapper.drag-over-before::before,
	.card-wrapper.drag-over-after::after {
		content: "";
		position: absolute;
		left: 0;
		right: 0;
		height: 3px;
		background: var(--accent-color);
		border-radius: 2px;
		z-index: 10;
	}
	.card-wrapper.drag-over-before::before {
		top: -8px;
	}
	.card-wrapper.drag-over-after::after {
		bottom: -8px;
	}
	.card {
		background: var(--card-background);
		border: 1px solid var(--border-color);
		border-radius: 12px;
		padding: 16px;
		text-align: left;
		width: 100%;
		position: relative;
		transition:
			box-shadow 0.15s,
			transform 0.15s,
			opacity 0.15s;
		/* box-sizing: border-box; */
	}
	.card.dragging {
		opacity: 0.5;
		transform: scale(0.98);
		box-shadow: none;
	}
	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 8px;
	}
	.card-title {
		font-weight: 600;
		font-size: 15px;
		color: var(--heading-color);
		flex: 1;
		word-break: break-word;
	}
	.card-actions {
		display: flex;
		align-items: center;
		gap: 4px;
		flex-shrink: 0;
	}
	.pin-indicator {
		color: var(--accent-color);
		display: flex;
	}
	.edit-card-btn {
		background: transparent;
		border: none;
		color: var(--muted-color);
		cursor: pointer;
		display: flex;
		opacity: 0;
		transition: opacity 0.2s;
		position: absolute;
		right: 0.5rem;
		background: var(--card-background);
		border-radius: 0.25rem;
		padding: 0.5rem;
		top: 0.5rem;
	}
	.edit-card-btn:hover {
		background: var(--hover-background);
		color: var(--text-color);
	}
	.card:hover .edit-card-btn {
		opacity: 1;
	}
	.card-body {
		font-size: 14px;
		color: var(--text-color);
		line-height: 1.5;
	}
	.text-preview {
		overflow: hidden;
		display: -webkit-box;
		-webkit-line-clamp: 6;
		-webkit-box-orient: vertical;
	}
	.text-preview :global(b),
	.text-preview :global(strong) {
		font-weight: 600;
	}
	.text-preview :global(i),
	.text-preview :global(em) {
		font-style: italic;
	}
	/* Checklist now interactive */
	.checklist-preview .check-item-btn {
		display: flex;
		align-items: flex-start;
		gap: 8px;
		padding: 4px 0;
		color: var(--text-color);
		background: none;
		border: none;
		text-align: left;
		cursor: pointer;
		width: 100%;
		font-size: inherit;
		font-family: inherit;
	}
	.checklist-preview .check-item-btn:hover {
		color: var(--heading-color);
	}
	.checklist-preview .check-item-btn.done {
		color: var(--muted-color);
		text-decoration: line-through;
	}
	.checklist-preview .check-item-btn.done:hover {
		color: var(--muted-color);
	}
	.link-preview .link-img {
		width: 100%;
		height: 120px;
		object-fit: cover;
		border-radius: 6px;
		margin-bottom: 8px;
	}
	.link-preview .link-title {
		font-weight: 500;
		color: var(--accent-color);
		word-break: break-all;
		text-decoration: none;
		display: block;
	}
	.link-preview .link-title:hover {
		text-decoration: underline;
	}
	.link-preview .link-desc {
		font-size: 13px;
		color: var(--muted-color);
		margin-top: 4px;
	}
	.image-preview img {
		width: 100%;
		border-radius: 6px;
	}
	.image-preview .no-image {
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--muted-color);
		background: var(--hover-background);
		border-radius: 6px;
	}
	.image-preview .caption {
		font-size: 13px;
		color: var(--muted-color);
		margin-top: 8px;
	}
	.table-preview table {
		width: 100%;
		font-size: 12px;
		border-collapse: collapse;
	}
	.table-preview td {
		padding: 4px 8px;
		border: 1px solid var(--border-color);
		max-width: 80px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	/* Embed active styling */
	.embed-preview-active .embed-wrapper {
		width: 100%;
		border-radius: 8px;
		overflow: hidden;
		background: #000;
	}
	.embed-preview-active .embed-wrapper :global(iframe) {
		width: 100%;
		aspect-ratio: 16/9;
		border: none;
		display: block;
	}
	.no-embed {
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--muted-color);
		background: var(--hover-background);
		border-radius: 6px;
	}
	.more {
		font-size: 12px;
		color: var(--muted-color);
		margin-top: 4px;
	}
	.muted {
		color: var(--muted-color);
	}
	.fab {
		position: fixed;
		bottom: 24px;
		right: 24px;
		width: 56px;
		height: 56px;
		border-radius: 16px;
		background: var(--accent-color);
		color: white;
		border: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
		transition: transform 0.15s;
		z-index: 50;
	}
	.fab:hover {
		transform: scale(1.05);
	}
	.fab:active {
		transform: scale(0.95);
	}
	.overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 100;
		padding: 16px;
	}
	.picker {
		background: var(--card-background);
		border-radius: 16px;
		padding: 8px;
		display: grid;
		grid-template-columns: 1fr 1fr 1fr;
		gap: 4px;
		flex-wrap: wrap;
		max-width: 360px;
	}
	.picker button {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
		padding: 16px 20px;
		border: none;
		background: transparent;
		border-radius: 12px;
		cursor: pointer;
		color: var(--text-color);
		font-size: 13px;
	}
	.picker button:hover {
		background: var(--hover-background);
	}
	.trash-modal {
		background: var(--card-background);
		border-radius: 16px;
		width: 100%;
		max-width: 480px;
		max-height: 80vh;
		max-height: 80dvh;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}
	.trash-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16px;
		border-bottom: 1px solid var(--border-color);
	}
	.trash-header h2 {
		display: flex;
		align-items: center;
		gap: 8px;
		margin: 0;
		font-size: 18px;
		font-weight: 600;
		color: var(--heading-color);
	}
	.trash-body {
		flex: 1;
		overflow-y: auto;
		padding: 8px;
	}
	.trash-empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 12px;
		padding: 48px 16px;
		color: var(--muted-color);
	}
	.trash-empty p {
		margin: 0;
		font-size: 15px;
	}
	.trash-list {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.trash-item {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 12px;
		border-radius: 8px;
		transition: background 0.15s;
	}
	.trash-item:hover {
		background: var(--hover-background);
	}
	.trash-item-icon {
		width: 36px;
		height: 36px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--hover-background);
		border-radius: 8px;
		color: var(--muted-color);
	}
	.trash-item-info {
		flex: 1;
		min-width: 0;
	}
	.trash-item-title {
		font-size: 14px;
		font-weight: 500;
		color: var(--text-color);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.trash-item-meta {
		font-size: 12px;
		color: var(--muted-color);
		margin-top: 2px;
	}
	.trash-item-actions {
		display: flex;
		gap: 4px;
	}
	.restore-btn,
	.delete-forever-btn {
		width: 32px;
		height: 32px;
		border: none;
		background: transparent;
		border-radius: 6px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--muted-color);
		transition: all 0.15s;
	}
	.restore-btn:hover {
		background: #dcfce7;
		color: #16a34a;
	}
	.delete-forever-btn:hover {
		background: #fef2f2;
		color: #dc2626;
	}
	.trash-footer {
		padding: 12px 16px;
		border-top: 1px solid var(--border-color);
	}
	.empty-trash-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		width: 100%;
		padding: 10px 16px;
		border: none;
		background: #fef2f2;
		color: #dc2626;
		border-radius: 8px;
		font-size: 14px;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.15s;
	}
	.empty-trash-btn:hover {
		background: #fee2e2;
	}
	.editor-modal {
		background: var(--card-background);
		border-radius: 16px;
		width: 100%;
		max-width: 600px;
		max-height: 90vh;
		max-height: 90dvh;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}
	.editor-header {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 16px;
		border-bottom: 1px solid var(--border-color);
	}
	.title-input {
		flex: 1;
		font-size: 18px;
		font-weight: 600;
		border: none;
		background: transparent;
		color: var(--heading-color);
	}
	.title-input:focus {
		outline: none;
	}
	.title-input::placeholder {
		color: var(--muted-color);
	}
	.delete-btn,
	.close-btn {
		width: 36px;
		height: 36px;
		border: none;
		background: transparent;
		border-radius: 8px;
		cursor: pointer;
		color: var(--muted-color);
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.delete-btn:hover {
		background: #fef2f2;
		color: #dc2626;
	}
	.close-btn:hover {
		background: var(--hover-background);
	}
	.pin-btn {
		width: 36px;
		height: 36px;
		border: none;
		background: transparent;
		border-radius: 8px;
		cursor: pointer;
		color: var(--muted-color);
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.pin-btn:hover {
		background: var(--hover-background);
	}
	.pin-btn.pinned {
		color: var(--accent-color);
	}
	.editor-body {
		flex: 1;
		overflow-y: auto;
		padding: 16px;
	}
	.editor-footer {
		padding: 12px 16px;
		border-top: 1px solid var(--border-color);
	}
	.last-updated {
		font-size: 12px;
		color: var(--muted-color);
	}
	.text-editor {
		min-height: 200px;
		font-size: 15px;
		line-height: 1.7;
		color: var(--text-color);
		outline: none;
	}
	.text-editor:empty::before {
		content: attr(data-placeholder);
		color: var(--muted-color);
	}
	.text-editor :global(b),
	.text-editor :global(strong) {
		font-weight: 600;
	}
	.text-editor :global(i),
	.text-editor :global(em) {
		font-style: italic;
	}
	.checklist-editor {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.check-row {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.check-toggle {
		border: none;
		background: transparent;
		cursor: pointer;
		color: var(--accent-color);
		padding: 4px;
		border-radius: 4px;
	}
	.check-row input {
		flex: 1;
		border: none;
		background: transparent;
		font-size: 15px;
		color: var(--text-color);
		padding: 8px 0;
	}
	.check-row input:focus {
		outline: none;
	}
	.check-row input::placeholder {
		color: var(--muted-color);
	}
	.check-row input.done {
		text-decoration: line-through;
		color: var(--muted-color);
	}
	.add-item {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px;
		border: none;
		background: transparent;
		color: var(--muted-color);
		cursor: pointer;
		font-size: 14px;
		border-radius: 6px;
	}
	.add-item:hover {
		background: var(--hover-background);
		color: var(--text-color);
	}
	.link-editor {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.link-editor input,
	.link-editor textarea {
		width: 100%;
		padding: 12px;
		border: 1px solid var(--border-color);
		border-radius: 8px;
		font-size: 15px;
		background: var(--input-background);
		color: var(--text-color);
		box-sizing: border-box;
	}
	.link-editor input:focus,
	.link-editor textarea:focus {
		outline: none;
		border-color: var(--accent-color);
	}
	.link-editor textarea {
		resize: vertical;
		font-family: inherit;
	}
	.image-editor {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.image-editor .preview {
		max-width: 100%;
		border-radius: 8px;
	}
	.upload-area {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
		padding: 32px;
		border: 2px dashed var(--border-color);
		border-radius: 8px;
		cursor: pointer;
		color: var(--muted-color);
	}
	.upload-area:hover {
		border-color: var(--accent-color);
		background: var(--hover-background);
	}
	.image-editor .or {
		text-align: center;
		color: var(--muted-color);
		font-size: 13px;
	}
	.image-editor input {
		width: 100%;
		padding: 12px;
		border: 1px solid var(--border-color);
		border-radius: 8px;
		font-size: 15px;
		background: var(--input-background);
		color: var(--text-color);
		box-sizing: border-box;
	}
	.image-editor input:focus {
		outline: none;
		border-color: var(--accent-color);
	}
	.remove-img {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 8px 12px;
		border: none;
		background: #fef2f2;
		color: #dc2626;
		border-radius: 6px;
		cursor: pointer;
		font-size: 14px;
		align-self: flex-start;
	}
	.table-editor {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.table-scroll {
		overflow-x: auto;
	}
	.table-editor table {
		border-collapse: collapse;
		min-width: 100%;
	}
	.table-editor td {
		padding: 0;
		border: 1px solid var(--border-color);
	}
	.table-editor td input {
		width: 100%;
		min-width: 80px;
		padding: 10px;
		border: none;
		background: transparent;
		font-size: 14px;
		color: var(--text-color);
		box-sizing: border-box;
	}
	.table-editor td input:focus {
		outline: none;
		background: var(--hover-background);
	}
	.table-editor .row-action {
		border: none;
		padding: 0 4px;
	}
	.table-editor .row-action button {
		padding: 4px;
		border: none;
		background: transparent;
		color: var(--muted-color);
		cursor: pointer;
		border-radius: 4px;
	}
	.table-editor .row-action button:hover {
		background: #fef2f2;
		color: #dc2626;
	}
	.table-actions {
		display: flex;
		gap: 8px;
	}
	.table-actions button {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 8px 12px;
		border: 1px solid var(--border-color);
		background: transparent;
		border-radius: 6px;
		cursor: pointer;
		font-size: 13px;
		color: var(--text-color);
	}
	.table-actions button:hover {
		background: var(--hover-background);
	}
	.embed-editor {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.embed-editor textarea {
		width: 100%;
		padding: 12px;
		border: 1px solid var(--border-color);
		border-radius: 8px;
		font-size: 14px;
		font-family: monospace;
		background: var(--input-background);
		color: var(--text-color);
		box-sizing: border-box;
		resize: vertical;
	}
	.embed-editor textarea:focus {
		outline: none;
		border-color: var(--accent-color);
	}
	.embed-preview-frame {
		position: relative;
		width: 100%;
		border-radius: 8px;
		overflow: hidden;
	}
	.embed-preview-frame :global(iframe) {
		width: 100%;
		aspect-ratio: 16/9;
		border: none;
	}
	.embed-placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 12px;
		padding: 40px 20px;
		background: var(--hover-background);
		border-radius: 8px;
		color: var(--muted-color);
		text-align: center;
	}
	.embed-placeholder p {
		margin: 0;
		font-size: 13px;
		max-width: 280px;
		line-height: 1.5;
	}
	@media (max-width: 600px) {
		.header {
			padding: 16px;
			padding-top: max(16px, env(safe-area-inset-top));
		}
		.header h1 {
			font-size: 20px;
		}
		.app-icon {
			width: 36px;
			height: 36px;
			border-radius: 9px;
		}
		.search-wrap {
			flex: 1 1 100%;
			max-width: none;
			order: 3;
		}
		.trash-btn {
			margin-left: auto;
		}
  /* @media (max-width: 600px) */
.main {
    padding: 0 16px 100px;
  }
		.fab {
			bottom: max(24px, env(safe-area-inset-bottom));
			right: 16px;
		}
		.picker {
			flex-wrap: wrap;
			justify-content: center;
			max-width: 280px;
		}
		.picker button {
			flex: 0 0 calc(33% - 4px);
			padding: 12px 8px;
		}
	}
	.footer {
		padding-top: 8px;
		padding-bottom: max(8px, env(safe-area-inset-bottom));
		font-size: 11px;
		color: var(--muted-color);
		text-align: center;
		background: var(--page-background);
	}
	.footer a {
		color: inherit;
	}
</style>
