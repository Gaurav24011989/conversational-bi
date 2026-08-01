import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { QueryResponse } from '../types/api'

const PIE_COLORS = ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2']

interface ChartViewProps {
  visualization: NonNullable<QueryResponse['visualization']>
  rows: Array<Record<string, unknown>>
}

export function ChartView({ visualization, rows }: ChartViewProps) {
  const xField = visualization.x_axis?.field
  const yField = visualization.y_axis?.field ?? visualization.series?.[0]?.field
  const chartType = visualization.chart_type

  const data = rows.map((row) => {
    const entry: Record<string, string | number> = {}
    for (const [k, v] of Object.entries(row)) {
      entry[k] = typeof v === 'number' ? v : String(v ?? '')
    }
    return entry
  })

  if (!xField && !yField) {
    return <p data-testid="chart-fallback">Unable to render chart — missing axis fields.</p>
  }

  return (
    <div className="chart-container" data-testid={`chart-${chartType}`}>
      <ResponsiveContainer width="100%" height={320}>
        {chartType === 'bar' ? (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xField} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={yField!} fill="#2563eb" />
          </BarChart>
        ) : chartType === 'line' || chartType === 'area' ? (
          chartType === 'area' ? (
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xField} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey={yField!} stroke="#2563eb" fill="#93c5fd" />
            </AreaChart>
          ) : (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xField} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey={yField!} stroke="#2563eb" />
            </LineChart>
          )
        ) : chartType === 'pie' || chartType === 'donut' ? (
          <PieChart>
            <Pie
              data={data}
              dataKey={yField!}
              nameKey={xField}
              cx="50%"
              cy="50%"
              innerRadius={chartType === 'donut' ? 60 : 0}
              outerRadius={100}
              label
            >
              {data.map((_, index) => (
                <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        ) : chartType === 'scatter' ? (
          <ScatterChart>
            <CartesianGrid />
            <XAxis dataKey={xField} type="category" />
            <YAxis dataKey={yField} />
            <Tooltip />
            <Scatter data={data} fill="#2563eb" />
          </ScatterChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xField} />
            <YAxis />
            <Tooltip />
            <Bar dataKey={yField!} fill="#2563eb" />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}
