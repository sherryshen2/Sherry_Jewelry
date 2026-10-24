import type { Aggregation, ChartPoint, DataRow, Dataset } from './types'

export const SYSTEM_COLUMNS = new Set(['_source', '_source_row'])

export function combine_datasets(datasets: Dataset[]): DataRow[] {
	return datasets.flatMap((dataset) => dataset.rows)
}

export function columns_for(rows: DataRow[]): string[] {
	const columns = new Set<string>()
	for (const row of rows) Object.keys(row).forEach((column) => columns.add(column))
	return [...columns]
}

export function data_columns(rows: DataRow[]): string[] {
	return columns_for(rows).filter((column) => !SYSTEM_COLUMNS.has(column))
}

export function numeric_columns(rows: DataRow[]): string[] {
	return data_columns(rows).filter((column) => {
		const values = rows.map((row) => row[column]).filter((value) => value !== null && value !== undefined && value !== '')
		if (!values.length) return false
		return values.filter((value) => Number.isFinite(Number(value))).length / values.length >= 0.8
	})
}

export function filter_rows(rows: DataRow[], search: string, column: string, selected: string[]): DataRow[] {
	const query = search.trim().toLowerCase()
	return rows.filter((row) => {
		const matches_search = !query || Object.values(row).some((value) => String(value ?? '').toLowerCase().includes(query))
		const matches_filter = !column || !selected.length || selected.includes(String(row[column] ?? '(blank)'))
		return matches_search && matches_filter
	})
}

export function aggregate(rows: DataRow[], group_by: string, metric: string, operation: Aggregation): ChartPoint[] {
	const groups = new Map<string, { sum: number; count: number; min: number; max: number }>()
	for (const row of rows) {
		const label = String(row[group_by] ?? '(blank)')
		const value = metric === '__count' ? 1 : Number(row[metric])
		const item = groups.get(label) || { sum: 0, count: 0, min: Infinity, max: -Infinity }
		if (metric === '__count' || Number.isFinite(value)) {
			item.sum += value
			item.count += 1
			item.min = Math.min(item.min, value)
			item.max = Math.max(item.max, value)
		}
		groups.set(label, item)
	}
	return [...groups.entries()]
		.map(([label, item]) => ({
			label,
			count: item.count,
			value: operation === 'count' ? item.count : operation === 'average' ? item.sum / Math.max(item.count, 1) : operation === 'minimum' ? item.min : operation === 'maximum' ? item.max : item.sum
		}))
		.filter((item) => Number.isFinite(item.value))
		.sort((left, right) => right.value - left.value)
		.slice(0, 20)
}

export function series(rows: DataRow[], group_by: string, metric: string): ChartPoint[] {
	const groups = new Map<string, { sum: number; count: number }>()
	for (const row of rows) {
		const label = String(row[group_by] ?? '(blank)')
		const value = metric === '__count' ? 1 : Number(row[metric])
		if (metric !== '__count' && !Number.isFinite(value)) continue
		const item = groups.get(label) || { sum: 0, count: 0 }
		item.sum += value
		item.count += 1
		groups.set(label, item)
	}
	return [...groups.entries()].map(([label, item]) => ({ label, value: item.sum, count: item.count }))
}

export function sum_values(rows: DataRow[], column: string): number {
	return rows.reduce((total, row) => {
		const value = Number(row[column])
		return total + (Number.isFinite(value) ? value : 0)
	}, 0)
}

export function preferred_column(columns: string[], candidates: string[], fallback = ''): string {
	const normalised = columns.map((column) => ({ column, value: column.toLowerCase().replace(/[^a-z0-9]/g, '') }))
	for (const candidate of candidates) {
		const found = normalised.find((item) => item.value.includes(candidate))
		if (found) return found.column
	}
	return fallback || columns[0] || ''
}

export function format_number(value: number): string {
	return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value)
}
