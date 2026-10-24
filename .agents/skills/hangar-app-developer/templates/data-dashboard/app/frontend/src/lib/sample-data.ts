import type { Dataset } from './types'

const records = [
	['Jan', 'SG', 'Marketplace', 132, 18600, 0.29, 16500],
	['Jan', 'MY', 'Marketplace', 98, 12100, 0.25, 11400],
	['Jan', 'PH', 'Partner', 74, 8900, 0.22, 8100],
	['Feb', 'SG', 'Marketplace', 146, 21100, 0.3, 19000],
	['Feb', 'MY', 'Direct', 103, 13700, 0.26, 12400],
	['Feb', 'PH', 'Partner', 86, 10400, 0.23, 9200],
	['Mar', 'SG', 'Direct', 159, 23800, 0.31, 21400],
	['Mar', 'MY', 'Marketplace', 117, 15400, 0.27, 14300],
	['Mar', 'PH', 'Partner', 91, 11100, 0.24, 10400],
	['Apr', 'SG', 'Marketplace', 171, 26400, 0.32, 24000],
	['Apr', 'MY', 'Direct', 122, 16600, 0.27, 15300],
	['Apr', 'PH', 'Partner', 96, 11900, 0.24, 11200]
]

export const LOCAL_DEMO_DATASET: Dataset = {
	name: 'Local demo · Commerce performance',
	source_type: 'local',
	columns: ['order_month', 'region', 'channel', 'orders', 'net_sales', 'gross_margin', 'sales_target', '_source', '_source_row'],
	rows: records.map(([order_month, region, channel, orders, net_sales, gross_margin, sales_target], index) => ({
		order_month,
		region,
		channel,
		orders,
		net_sales,
		gross_margin,
		sales_target,
		_source: 'Local demo · Commerce performance',
		_source_row: index + 1
	})),
	row_count: records.length
}
