// @ts-nocheck
import { api } from '$hangarkit'
import type { Dataset } from './types'

type DatasetResponse = { ok: boolean; dataset: Dataset; detail?: string }

export async function upload_csv(files: File[]): Promise<{ datasets: Dataset[]; errors: { name: string; error: string }[] }> {
	const form = new FormData()
	files.forEach((file) => form.append('files', file))
	return api.request('/dashboard/csv', { method: 'POST', body: form })
}

export async function load_google_sheet(spreadsheet: string, range_name: string): Promise<Dataset> {
	const response = await api.post('/dashboard/google-sheet', { spreadsheet, range_name }) as DatasetResponse
	return response.dataset
}

export async function load_datasuite(payload: { api_name: string; version: string; scope: string[]; parameters: Record<string, unknown>; enable_cache: boolean }): Promise<Dataset> {
	const response = await api.post('/dashboard/datasuite', payload) as DatasetResponse
	return response.dataset
}
