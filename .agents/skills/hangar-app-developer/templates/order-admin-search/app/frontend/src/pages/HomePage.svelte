<script lang="ts">
	// @ts-nocheck
	import content from '$content'
	import { CircleAlert, CircleCheck, Link, LoaderCircle, RefreshCw } from 'lucide-svelte'
	import { order_admin_api } from '../lib/api'
	import type { AccessResult, Order, OrderSearch, SearchResult, Target } from '../lib/types'

	let env = $state('test')
	let region = $state('sg')
	let checking = $state(false)
	let error = $state('')
	let result = $state<AccessResult | null>(null)
	let checkedTarget = $state<Target | null>(null)
	let orderKey = $state('')
	let buyer = $state('')
	let seller = $state('')
	let beStatus = $state('')
	let feStatus = $state('')
	let payment = $state('')
	let courier = $state('')
	let checkoutId = $state('')
	let shopId = $state('')
	let crossBorder = $state('')
	let purchasedFrom = $state('')
	let purchasedTo = $state('')
	let updatedFrom = $state('')
	let updatedTo = $state('')
	let filtersOpen = $state(false)
	let searching = $state(false)
	let searchError = $state('')
	let searchResult = $state<SearchResult | null>(null)
	let lastQuery = $state<OrderSearch | null>(null)

	const selected = $derived({ env: env.trim().toLowerCase(), region: region.trim().toLowerCase() })
	const targetChanged = $derived(
		checkedTarget !== null && (selected.env !== checkedTarget.env || selected.region !== checkedTarget.region)
	)
	const ready = $derived(result?.state === 'ready' && !targetChanged && !checking)
	const connecting = $derived(result?.state === 'pending' && result.mode === 'user' && result.next_action?.actor !== 'owner')
	const accessLabel = $derived(
		checking ? 'Checking access' : targetChanged ? 'Check new target' : error ? 'Check failed' :
		ready ? 'Access confirmed' : connecting ? 'Connecting' : result ? 'Needs attention' : 'Not connected'
	)
	const checkLabel = $derived(
		checking ? 'Checking access…' : targetChanged ? 'Check access' : ready ? 'Check again' :
		error || result ? 'Try again' : 'Connect Order Admin'
	)
	const targetLabel = $derived(`${selected.env || 'environment'} / ${(selected.region || 'region').toUpperCase()}`)
	const extraFilterCount = $derived([
		checkoutId, crossBorder, beStatus, feStatus, payment, courier,
		purchasedFrom, purchasedTo, updatedFrom, updatedTo
	].filter(Boolean).length)

	async function checkAccess() {
		if (checking || searching) return
		const target = { ...selected }
		if (!target.env || !target.region) {
			error = 'Choose an environment and region to check.'
			return
		}
		checking = true
		error = ''
		result = null
		checkedTarget = null
		searchResult = null
		lastQuery = null
		searchError = ''
		try {
			const response = await order_admin_api.ensureAccess(target)
			if (selected.env !== target.env || selected.region !== target.region) return
			result = response
			checkedTarget = target
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'We could not check Order Admin access. Try again.'
		} finally {
			checking = false
		}
		if (ready) await loadOrders(buildQuery(target, 0))
	}

	function optionalId(value: string): string | null {
		return value.trim() || null
	}

	function dateSeconds(value: string, end = false): number | null {
		if (!value) return null
		const date = new Date(`${value}T00:00:00`)
		if (end) date.setDate(date.getDate() + 1)
		return Math.floor(date.getTime() / 1000) - (end ? 1 : 0)
	}

	function buildQuery(target: Target, offset: number): OrderSearch {
		return {
			...target,
			order_key: orderKey.trim(),
			buyer_name: buyer.trim(),
			seller_name: seller.trim(),
			courier: courier.trim(),
			cross_border: crossBorder === '' ? null : crossBorder === 'true',
			be_status: optionalId(beStatus),
			fe_status: optionalId(feStatus),
			payment_method: optionalId(payment),
			checkout_id: optionalId(checkoutId),
			shop_id: optionalId(shopId),
			ctime_gte: dateSeconds(purchasedFrom),
			ctime_lte: dateSeconds(purchasedTo, true),
			mtime_gte: dateSeconds(updatedFrom),
			mtime_lte: dateSeconds(updatedTo, true),
			offset
		}
	}

	async function loadOrders(query: OrderSearch) {
		if (searching) return
		if ([query.be_status, query.fe_status, query.payment_method, query.checkout_id, query.shop_id]
			.some((value) => value !== null && !/^\d+$/.test(value))) {
			searchError = 'ID filters must contain digits only.'
			return
		}
		if ((query.ctime_gte != null && query.ctime_lte != null && query.ctime_gte > query.ctime_lte) ||
			(query.mtime_gte != null && query.mtime_lte != null && query.mtime_gte > query.mtime_lte)) {
			searchError = 'The end date must be on or after the start date.'
			return
		}
		searching = true
		searchError = ''
		try {
			const response = await order_admin_api.search(query)
			if (selected.env === query.env && selected.region === query.region) {
				searchResult = response
				lastQuery = query
			}
		} catch (cause) {
			searchResult = null
			searchError = cause instanceof Error ? cause.message : 'Order search did not complete. Check access and try again.'
		} finally {
			searching = false
		}
	}

	async function search(offset = 0) {
		if (!ready || searching) return
		await loadOrders(offset && lastQuery ? { ...lastQuery, offset } : buildQuery(selected, offset))
	}

	function clearFilters() {
		orderKey = ''
		buyer = ''
		seller = ''
		beStatus = ''
		feStatus = ''
		payment = ''
		courier = ''
		checkoutId = ''
		shopId = ''
		crossBorder = ''
		purchasedFrom = ''
		purchasedTo = ''
		updatedFrom = ''
		updatedTo = ''
		if (ready) void search()
	}

	function dateLabel(value: number | null) {
		if (!value) return '—'
		const date = new Date(value < 1e12 ? value * 1000 : value)
		return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString()
	}

	function statusLabel(value: Order['be_status']) {
		return value?.name || (value?.id != null ? String(value.id) : '—')
	}

	function recovery() {
		if (!result || result.state === 'ready') return null
		const owner = result.next_action?.actor === 'owner' || result.mode === 'app'
		const action = result.next_action?.code
		if (owner) return {
			title: 'The app owner needs to restore access',
			body: `Ask the app owner to check Order Admin for ${targetLabel}. Their Connector grant, website sign-in, or Relay may need attention; installing Relay on your computer will not fix owner access.`,
			setup: false
		}
		if (result.state === 'grant_missing' || action === 'connect_grant') return {
			title: 'Allow this app to use Order Admin',
			body: `This is a permission for ${content.app_title || 'this app'}, separate from signing in to the Order Admin website. Complete the Connector approval for this app, then return and try again.`,
			setup: false
		}
		if (result.state === 'pending' || action === 'complete_sign_in' || action === 'complete_relay_task') return {
			title: 'Connecting your website session',
			body: `Connector is preparing Order Admin access for ${targetLabel}. Wait a moment, then try again. If sign-in is requested, complete it on your paired computer.`,
			setup: true
		}
		if (result.state === 'relay_offline' || ['pair_relay', 'start_relay', 'check_relay_setup'].includes(action || '')) return {
			title: 'Connect the Relay helper',
			body: `Order Admin needs a fresh website session for ${targetLabel}, but Connector cannot reach your Relay. Set up or restart Relay on your computer, then try again.`,
			setup: true
		}
		if (result.state === 'denied') return {
			title: 'Order Admin did not allow this target',
			body: `Check that ${targetLabel} is the right environment and region. Your website account may need Order Admin permission for this target; ask your administrator if access is denied.`,
			setup: false
		}
		return {
			title: 'Access could not be verified',
			body: `Connector could not confirm Order Admin access for ${targetLabel}. Try again in a moment. This does not necessarily mean Relay is missing.`,
			setup: false
		}
	}
</script>

<div class="workspace">
	<header class="topbar">
		<div class="brand"><span class="brand-mark" aria-hidden="true">O</span><span>{content.app_title || 'Order Search'}</span></div>
		<span class="source">ORDER ADMIN <span class="source-dot">·</span> SEARCH WORKSPACE</span>
	</header>

	<main>
		<div class="page-heading">
			<div>
				<p class="overline">ORDER ADMIN</p>
				<h1>{content.page_title || 'Find orders'}</h1>
				<p class="subhead">{content.intro_text || 'Choose a website target, confirm access, then search its orders.'}</p>
			</div>
			{#if ready}
				<span class="target-chip"><span class="status-dot"></span>{checkedTarget?.env} / {checkedTarget?.region.toUpperCase()}</span>
			{/if}
		</div>

		<section class="target-section" aria-labelledby="target-title">
			<div class="section-heading">
				<div>
					<p class="step">01 / ACCESS</p>
					<h2 id="target-title">Website target</h2>
				</div>
				<span class="state-label" class:success={ready} class:active={checking || connecting && !targetChanged}>{accessLabel}</span>
			</div>
			<form class="target-form" aria-busy={checking} onsubmit={(event) => { event.preventDefault(); void checkAccess() }}>
				<label>
					<span>Environment</span>
					<input name="environment" list="environments" bind:value={env} autocomplete="off" maxlength="32" required disabled={checking} placeholder="e.g. test" />
					<datalist id="environments">
						{#each ['test', 'uat', 'staging', 'stable', 'live'] as value}<option value={value}></option>{/each}
					</datalist>
				</label>
				<label>
					<span>Region</span>
					<input name="region" list="regions" bind:value={region} autocomplete="off" maxlength="16" required disabled={checking} placeholder="e.g. sg" />
					<datalist id="regions">
						{#each ['sg', 'ar', 'br', 'cl', 'co', 'id', 'kh', 'la', 'mm', 'mx', 'my', 'ph', 'th', 'tw', 'vn', 'xx'] as code}<option value={code}></option>{/each}
					</datalist>
				</label>
				<button class="primary check-button" type="submit" disabled={checking || searching}>
					{#if checking}<LoaderCircle size={16} class="spin" aria-hidden="true" />
					{:else if ready || error || result}<RefreshCw size={16} aria-hidden="true" />
					{:else}<Link size={16} aria-hidden="true" />{/if}
					<span>{checkLabel}</span>
				</button>
			</form>
			{#if targetChanged}
				<div class="connection-status" role="status">
					<Link size={20} aria-hidden="true" />
					<div><h3>Check the new target</h3><p>Confirm access for {targetLabel} before searching its orders.</p></div>
				</div>
			{:else if checking}
				<div class="connection-status is-loading" role="status" aria-live="polite" aria-atomic="true">
					<LoaderCircle size={20} class="spin" aria-hidden="true" />
					<div>
						<h3>Checking Order Admin access</h3>
						<p>Verifying your website session for {targetLabel}. This may take a moment.</p>
					</div>
				</div>
			{:else if error}
				<div class="connection-status is-error" role="alert">
					<CircleAlert size={20} aria-hidden="true" />
					<div><h3>Connection check did not complete</h3><p>{error}</p></div>
				</div>
			{:else if result && result.state !== 'ready'}
				{@const help = recovery()}
				{#if help}
					<div class="connection-status recovery" class:is-loading={connecting} role="status" aria-live="polite" aria-atomic="true">
						{#if connecting}<LoaderCircle size={20} class="spin" aria-hidden="true" />
						{:else}<CircleAlert size={20} aria-hidden="true" />{/if}
						<div>
							<h3>{help.title}</h3>
							<p>{help.body}</p>
							{#if help.setup}
								<details class="setup">
									<summary>{result.state === 'pending' && result.relay.connection === 'online' ? 'Check whether sign-in needs you' : 'Set up or continue Connector Relay'}</summary>
									<ol>
										{#if result.relay.connection !== 'online'}
											<li><a href="https://connector.shopee.io/docs/cli" target="_blank" rel="noopener noreferrer">Download Connector CLI and read the setup guide</a> on the computer that will supply your Order Admin session.</li>
											<li>Sign in with <code>connector login</code>. Check <code>connector relay status --local</code>.</li>
											<li>If unpaired, run <code>connector relay pair</code>. Install or restart the helper with <code>connector relay service install</code>.</li>
										{/if}
										{#if result.state === 'pending'}<li>Check <code>connector relay actions list</code>. If it reports a job, continue only that job with <code>connector relay actions continue --job &lt;job-id&gt;</code> and finish any sign-in in the Relay browser. If it reports no action, wait briefly and check access again.</li>{/if}
									</ol>
								</details>
							{/if}
						</div>
					</div>
				{/if}
			{:else if ready}
				<div class="connection-status is-ready" role="status">
					<CircleCheck size={20} aria-hidden="true" />
					<div>
						<h3>Connected to {targetLabel}</h3>
						<p>Order Admin access is confirmed.</p>
						{#if result?.relay.connection === 'offline'}<p class="subtle">A cached session is working even though Relay is offline.</p>{/if}
					</div>
				</div>
			{:else}
				<div class="connection-status" role="status">
					<Link size={20} aria-hidden="true" />
					<div><h3>Ready to connect</h3><p>Check Order Admin access for {targetLabel}. A saved session will be used when available.</p></div>
				</div>
			{/if}
		</section>

		{#if ready}
			<section class="search-section" aria-labelledby="search-title">
				<div class="section-heading">
					<div>
						<p class="step">02 / ORDERS</p>
						<h2 id="search-title">Search orders</h2>
					</div>
					<span class="state-label">READ ONLY</span>
				</div>
				<form class="search-form" onsubmit={(event) => { event.preventDefault(); void search() }}>
					<div class="search-fields">
						<label class="key-field"><span>Order ID or SN</span><input bind:value={orderKey} placeholder="Optional" maxlength="64" /></label>
						<label><span>Seller username</span><input bind:value={seller} placeholder="Any seller" /></label>
						<label><span>Buyer username</span><input bind:value={buyer} placeholder="Any buyer" /></label>
						<label><span>Shop ID</span><input inputmode="numeric" pattern="[0-9]*" bind:value={shopId} placeholder="Any shop" /></label>
					</div>
					<div class="search-actions">
						<button class="primary" type="submit" disabled={searching}>{searching ? 'Searching…' : 'Search orders'}</button>
						<button class="secondary" type="button" disabled={searching} onclick={clearFilters}>Clear filters</button>
						<button class="text-button" type="button" onclick={() => filtersOpen = !filtersOpen} aria-expanded={filtersOpen} aria-controls="advanced-filters">
							{filtersOpen ? 'Fewer filters' : 'More filters'}{extraFilterCount ? ` (${extraFilterCount})` : ''}
						</button>
					</div>
					{#if filtersOpen}
						<div class="filters" id="advanced-filters">
							<label><span>Checkout ID</span><input inputmode="numeric" pattern="[0-9]*" bind:value={checkoutId} placeholder="Any checkout" /></label>
							<label><span>Cross-border</span><select bind:value={crossBorder}><option value="">Any</option><option value="true">Yes</option><option value="false">No</option></select></label>
							<label><span>Backend status ID</span><input inputmode="numeric" pattern="[0-9]*" bind:value={beStatus} placeholder="Any status" /></label>
							<label><span>Frontend status ID</span><input inputmode="numeric" pattern="[0-9]*" bind:value={feStatus} placeholder="Any status" /></label>
							<label><span>Payment method ID</span><input inputmode="numeric" pattern="[0-9]*" bind:value={payment} placeholder="Any method" /></label>
							<label><span>Courier</span><input bind:value={courier} placeholder="Any courier" /></label>
							<fieldset class="date-range">
								<legend>Purchased on</legend>
								<label><span>From</span><input type="date" bind:value={purchasedFrom} max={purchasedTo || undefined} /></label>
								<label><span>To</span><input type="date" bind:value={purchasedTo} min={purchasedFrom || undefined} /></label>
							</fieldset>
							<fieldset class="date-range">
								<legend>Status updated on</legend>
								<label><span>From</span><input type="date" bind:value={updatedFrom} max={updatedTo || undefined} /></label>
								<label><span>To</span><input type="date" bind:value={updatedTo} min={updatedFrom || undefined} /></label>
							</fieldset>
						</div>
					{/if}
				</form>
				{#if searchError}<p class="alert" role="alert">{searchError}</p>{/if}
				<div class="result-head">
					<strong>Results</strong>
					<span>{searching ? 'Loading…' : searchResult ? `${searchResult.orders.length} ${searchResult.orders.length === 1 ? 'order' : 'orders'} on this page` : 'No search yet'}</span>
				</div>
				<div class="table-wrap">
					<table>
						<thead><tr><th>Order ID / SN</th><th>Buyer · Seller</th><th>Status</th><th>Payment / checkout</th><th>Courier / fulfilment</th><th>Purchased</th></tr></thead>
						<tbody>
							{#each searchResult?.orders || [] as order, index (order.order_sn || `${order.order_id}-${index}`)}
								<tr>
									<td><strong>{order.order_id ?? '—'}</strong><small>{order.order_sn || '—'}</small></td>
									<td>{order.buyer_name || '—'}<small>{order.seller_name || '—'}{order.shop_id != null ? ` · Shop ${order.shop_id}` : ''}</small></td>
									<td>{statusLabel(order.be_status)}<small>FE: {statusLabel(order.fe_status)}{order.cross_border != null ? ` · Cross-border: ${order.cross_border ? 'Yes' : 'No'}` : ''}</small></td>
									<td>{order.payment_method || '—'}<small>Checkout ID: {order.checkout_id ?? '—'}</small></td>
									<td>{order.courier || order.fulfilment_channel?.name || '—'}<small>Channel ID: {order.fulfilment_channel?.id ?? '—'}</small></td>
									<td>{dateLabel(order.ctime)}<small>Updated: {dateLabel(order.mtime)}</small></td>
								</tr>
							{:else}
								<tr><td colspan="6" class="empty">{searching ? 'Searching orders…' : searchResult ? 'No orders match this search.' : 'Check access to browse orders.'}</td></tr>
							{/each}
						</tbody>
					</table>
				</div>
				{#if searchResult && (searchResult.offset > 0 || searchResult.has_more)}
					<nav class="pagination" aria-label="Results pages">
						<button type="button" disabled={searching || searchResult.offset === 0} onclick={() => void search(Math.max(0, searchResult!.offset - searchResult!.limit))}>Previous</button>
						<span>Page {Math.floor(searchResult.offset / searchResult.limit) + 1}</span>
						<button type="button" disabled={searching || !searchResult.has_more} onclick={() => void search(searchResult!.offset + searchResult!.limit)}>Next</button>
					</nav>
				{/if}
			</section>
		{:else}
			<section class="locked" aria-label="Order search unavailable">
				<span class="locked-number">02</span>
				<div><h2>Order search</h2><p>Check access for a website target to open the search workspace.</p></div>
			</section>
		{/if}
	</main>
</div>

<style>
	* { box-sizing: border-box; }
	button, input, select { font: inherit; }
	button { cursor: pointer; }
	button:disabled { cursor: not-allowed; opacity: .55; }
	button:focus-visible, a:focus-visible, summary:focus-visible { outline: 2px solid #0d777e; outline-offset: 3px; }
	a { color: #126a70; }
	.workspace { min-height: 100vh; }
	.topbar { height: 62px; border-bottom: 1px solid #dae3e3; background: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 max(24px, calc((100vw - 1240px) / 2)); }
	.brand { display: flex; align-items: center; gap: 10px; font-weight: 750; font-size: 16px; color: #183437; }
	.brand-mark { display: grid; place-items: center; width: 30px; height: 30px; background: #0d6c71; color: #fff; font-size: 17px; font-weight: 800; }
	.source { font-size: 10px; font-weight: 750; color: #68767a; letter-spacing: .08em; }
	.source-dot { padding: 0 8px; color: #a5afb0; }
	main { max-width: 1240px; margin: auto; padding: 36px 24px 80px; }
	.page-heading { display: flex; justify-content: space-between; align-items: flex-end; gap: 20px; margin-bottom: 32px; }
	.overline, .step { margin: 0 0 9px; font-size: 10px; font-weight: 800; color: #14757a; letter-spacing: .08em; }
	h1 { margin: 0; font-size: 32px; line-height: 1.18; font-weight: 730; }
	.subhead { margin: 7px 0 0; color: #647479; font-size: 14px; }
	.target-chip { flex: none; display: inline-flex; align-items: center; gap: 9px; padding: 8px 11px; font-size: 12px; font-weight: 700; color: #156a50; border: 1px solid #bcd9cb; background: #eaf5ee; border-radius: 4px; text-transform: uppercase; }
	.status-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #22a76f; flex: none; }
	.target-section, .search-section { border-top: 1px solid #cbd6d7; padding-top: 21px; margin-bottom: 35px; }
	.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 23px; }
	h2 { margin: 0; font-size: 19px; line-height: 1.3; font-weight: 720; }
	.state-label { font-size: 10px; font-weight: 800; letter-spacing: .06em; color: #758488; }
	.state-label.success { color: #1b7b57; }
	.state-label.active { color: #126a70; }
	.target-form { display: grid; grid-template-columns: minmax(150px, 220px) minmax(150px, 220px) auto; align-items: end; gap: 12px; }
	label { min-width: 0; display: grid; gap: 7px; font-size: 12px; color: #4b5c61; font-weight: 650; }
	input, select { min-width: 0; width: 100%; height: 40px; border: 1px solid #c7d2d3; border-radius: 4px; color: #1d292e; background: #fff; padding: 0 12px; outline: none; font-size: 13px; }
	input:focus-visible, select:focus-visible { border-color: #0d777e; box-shadow: 0 0 0 3px #d1ebeb; }
	input::placeholder { color: #9aa6a7; }
	input:disabled { background: #edf2f2; color: #68797b; cursor: not-allowed; }
	.primary { height: 40px; border: 1px solid #0c666b; border-radius: 4px; padding: 0 19px; color: #fff; background: #0c6b70; font-size: 13px; font-weight: 700; white-space: nowrap; }
	.primary:not(:disabled):hover { background: #09575b; }
	.check-button { justify-self: start; min-width: 186px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; }
	.check-button:disabled { opacity: 1; background: #537d80; border-color: #537d80; }
	.alert { margin: 15px 0 0; color: #a23431; font-size: 13px; }
	.subtle { color: #647479; }
	.connection-status { display: flex; align-items: flex-start; gap: 12px; min-height: 88px; margin-top: 20px; padding: 17px 0; border-top: 1px solid #dce5e4; color: #68797b; }
	.connection-status > :global(svg) { flex: none; margin-top: 1px; }
	.connection-status > div { min-width: 0; }
	.connection-status h3 { color: #30484c; }
	.connection-status p { margin: 0; font-size: 13px; line-height: 1.55; color: #647479; overflow-wrap: anywhere; }
	.connection-status.is-loading { color: #126a70; }
	.connection-status.is-ready, .connection-status.is-ready h3 { color: #1b6d4d; }
	.connection-status.is-error, .connection-status.is-error h3 { color: #a23431; }
	.recovery { color: #946024; }
	.recovery h3 { color: #73521e; }
	.recovery.is-loading h3 { color: #30484c; }
	h3 { margin: 1px 0 6px; font-size: 14px; }
	:global(.spin) { animation: connection-spin 1s linear infinite; }
	@keyframes connection-spin { to { transform: rotate(360deg); } }
	@media (prefers-reduced-motion: reduce) { :global(.spin) { animation: none; } }
	.setup { margin-top: 14px; color: #385a60; font-size: 13px; }
	.setup summary { cursor: pointer; font-weight: 700; }
	.setup ol { margin: 11px 0 0; padding-left: 20px; line-height: 1.75; }
	.setup li { padding-left: 3px; margin-bottom: 5px; }
	code { padding: 2px 4px; color: #203d41; background: #e8edeb; border-radius: 3px; font-size: 12px; overflow-wrap: anywhere; }
	.search-form { display: grid; gap: 14px; }
	.search-fields { display: grid; grid-template-columns: 1.3fr 1fr 1fr minmax(130px, .8fr); gap: 12px; }
	.search-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
	.secondary { height: 40px; border: 1px solid #c7d2d3; border-radius: 4px; padding: 0 14px; background: #fff; color: #41565a; font-size: 13px; font-weight: 650; }
	.text-button { border: 0; padding: 9px 5px; background: transparent; color: #126b70; font-weight: 700; font-size: 12px; }
	.filters { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px 12px; padding: 20px 0; border-top: 1px solid #e1e7e7; }
	.date-range { grid-column: span 2; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; min-width: 0; margin: 0; padding: 0; border: 0; }
	.date-range legend { padding: 0 0 8px; color: #4b5c61; font-size: 12px; font-weight: 650; }
	.result-head { display: flex; align-items: center; justify-content: space-between; padding: 13px 0; border-top: 1px solid #d8e1e1; color: #243a3d; font-size: 13px; }
	.result-head span { color: #819094; font-size: 12px; }
	.table-wrap { width: 100%; overflow-x: auto; background: #fff; border: 1px solid #dce5e4; }
	table { border-collapse: collapse; width: 100%; min-width: 860px; font-size: 12px; text-align: left; }
	th { background: #f0f4f3; padding: 12px 14px; color: #526368; font-size: 11px; font-weight: 700; white-space: nowrap; }
	td { padding: 20px 14px; border-top: 1px solid #e6eceb; }
	td strong { display: block; font-weight: 700; white-space: nowrap; }
	td small { display: block; margin-top: 4px; color: #738285; font-size: 11px; white-space: nowrap; }
	.empty { color: #718085; text-align: center; padding: 48px 16px; line-height: 1.5; }
	.pagination { display: flex; justify-content: flex-end; align-items: center; gap: 14px; padding: 14px 0; color: #526368; font-size: 12px; }
	.pagination button { border: 1px solid #c7d2d3; border-radius: 4px; background: #fff; padding: 7px 12px; color: #126b70; font-weight: 650; }
	.locked { display: flex; align-items: center; gap: 17px; padding: 21px 0; border-top: 1px solid #dbe3e3; color: #8d9a9e; }
	.locked-number { font-size: 23px; font-weight: 700; }
	.locked h2 { color: #637277; font-size: 16px; }
	.locked p { margin: 3px 0 0; font-size: 12px; }
	@media (max-width: 650px) {
		.topbar { padding: 0 18px; }
		.source { display: none; }
		main { padding: 26px 18px 60px; }
		.page-heading { align-items: flex-start; flex-direction: column; margin-bottom: 28px; }
		h1 { font-size: 28px; }
		.target-form { grid-template-columns: repeat(2, minmax(0, 1fr)); }
		.check-button { grid-column: 1 / -1; width: 100%; }
		.target-section .section-heading { align-items: flex-start; }
		.state-label { text-align: right; max-width: 120px; }
		.search-fields, .filters { grid-template-columns: 1fr; }
		.date-range { grid-column: 1; }
		.search-actions .primary { flex: 1; }
	}
	@media (min-width: 651px) and (max-width: 950px) {
		.search-fields { grid-template-columns: repeat(2, minmax(0, 1fr)); }
	}
</style>
