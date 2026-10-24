// @ts-nocheck
import { api } from '$hangarkit'
import type { StarterHealth } from './types'

export const health_api = {
	read: () => api.get('/health') as Promise<StarterHealth>
}
