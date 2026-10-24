export type Target = {
	env: string
	region: string
}

export type AccessResult = {
	state: 'ready' | 'pending' | 'relay_offline' | 'denied' | 'grant_missing' | 'unavailable'
	mode: 'user' | 'app'
	reason?: string
	target: Target
	access: {
		verified: boolean
		proof: 'order_admin_auth_info' | 'connector_site_auth' | 'none'
	}
	session: {
		state: 'active' | 'expired' | 'invalid' | 'needs_login' | 'missing' | 'unknown'
		source: 'relay_local_capture' | 'soup_mint' | 'unknown'
		verified: boolean | null
		expires_at?: string
	}
	relay: {
		pairing: 'paired' | 'not_paired' | 'unknown'
		connection: 'online' | 'offline' | 'unknown'
	}
	local_cli: {
		installed: 'unknown'
		connected: 'unknown'
		reason: 'not_observable_from_hangar_server'
	}
	next_action: {
		code: string
		actor: 'user' | 'owner'
	} | null
}

export type Order = {
	order_id: string | null
	order_sn: string | null
	checkout_id: string | null
	buyer_name: string | null
	seller_name: string | null
	shop_id: string | null
	be_status: { id: number; name: string } | null
	fe_status: { id: number; name: string } | null
	payment_method: string | null
	courier: string | null
	fulfilment_channel: { id: number; name: string; masked?: boolean } | null
	currency: string | null
	grand_total: number | null
	ctime: number | null
	mtime: number | null
	cross_border: boolean | null
}

export type OrderSearch = Target & {
	order_key: string
	buyer_name: string
	seller_name: string
	courier: string
	cross_border: boolean | null
	be_status: string | null
	fe_status: string | null
	payment_method: string | null
	checkout_id: string | null
	shop_id: string | null
	ctime_gte: number | null
	ctime_lte: number | null
	mtime_gte: number | null
	mtime_lte: number | null
	offset: number
}

export type SearchResult = {
	orders: Order[]
	has_more: boolean
	offset: number
	limit: number
}
