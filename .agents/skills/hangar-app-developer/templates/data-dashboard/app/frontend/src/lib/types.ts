export type DataRow = Record<string, unknown>

export type SourceType = 'csv' | 'google_sheets' | 'datasuite' | 'local'

export type Dataset = {
	name: string
	source_type: SourceType
	rows: DataRow[]
	columns: string[]
	row_count: number
}

export type DataSourceSummary = Pick<Dataset, 'name' | 'source_type' | 'columns' | 'row_count'>

export type Aggregation = 'count' | 'sum' | 'average' | 'minimum' | 'maximum'

export type ChartPoint = { label: string; value: number; count: number }
