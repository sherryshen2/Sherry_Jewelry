// @ts-nocheck
import { api } from '$hangarkit'
import type { AccessResult, OrderSearch, SearchResult, Target } from './types'

export const order_admin_api = {
	ensureAccess: (target: Target) => api.post('/order-admin/access', target) as Promise<AccessResult>,
	search: (query: OrderSearch) => api.post('/order-admin/search', query) as Promise<SearchResult>
}
