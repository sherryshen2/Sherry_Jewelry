// @ts-nocheck
import { api } from '$hangarkit'

export const smart_api = {
	create_task: (payload) => api.post('/tasks', payload),
	get_task: (task_id) => api.get(`/tasks/${encodeURIComponent(task_id)}`),
	refresh_task: (task_id) => api.post(`/tasks/${encodeURIComponent(task_id)}/refresh`, {}),
	continue_interrupt: (task_id, payload) => api.post(`/tasks/${encodeURIComponent(task_id)}/continue-interrupt`, payload),
	get_metrics: (granularity = 'daily') => api.get(`/workflow-metrics?granularity=${encodeURIComponent(granularity)}`)
}
