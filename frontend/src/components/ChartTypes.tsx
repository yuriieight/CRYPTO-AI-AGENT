import React from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

interface ChartData {
  timestamp: string;
  close: number;
  volume?: number;
  open?: number;
  high?: number;
  low?: number;
}

interface DynamicChartProps {
  data: ChartData[];
  type: 'line' | 'area' | 'bar' | 'volume';
  color?: string;
  height?: number;
}

const AXIS_STYLE    = { fontSize: 11, fill: 'var(--c-text-3)' };
const AXIS_STROKE   = 'var(--c-border)';
const GRID_STROKE   = 'var(--c-border)';
const TOOLTIP_STYLE = {
  background: 'var(--c-bg-1)',
  border: '1px solid var(--c-border-hover)',
  borderRadius: 8,
  color: 'var(--c-text-2)',
  fontSize: 12,
};
const TOOLTIP_LABEL_STYLE = { color: 'var(--c-text-3)' };

const formatDate  = (ts: string) =>
  new Date(ts).toLocaleDateString('uk-UA', { month: 'short', day: 'numeric' });

const formatPrice = (v: number) =>
  `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export const DynamicChart: React.FC<DynamicChartProps> = ({
  data,
  type,
  color = '#00d4ff',
  height = 300,
}) => {
  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-xl"
        style={{ height, background: 'var(--c-bg-2)', border: '1px solid var(--c-border)' }}
      >
        <p style={{ color: 'var(--c-text-3)' }} className="text-sm">Немає даних для відображення</p>
      </div>
    );
  }

  const commonAxis = {
    xAxis: (
      <XAxis
        dataKey="timestamp"
        tickFormatter={formatDate}
        stroke={AXIS_STROKE}
        tick={AXIS_STYLE}
        axisLine={{ stroke: AXIS_STROKE }}
        tickLine={{ stroke: AXIS_STROKE }}
      />
    ),
    yAxis: (
      <YAxis
        tickFormatter={formatPrice}
        stroke={AXIS_STROKE}
        tick={AXIS_STYLE}
        axisLine={{ stroke: AXIS_STROKE }}
        tickLine={{ stroke: AXIS_STROKE }}
        width={80}
      />
    ),
    grid: <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} opacity={0.6} vertical={false} />,
    tooltip: (
      <Tooltip
        contentStyle={TOOLTIP_STYLE}
        labelStyle={TOOLTIP_LABEL_STYLE}
        formatter={(v: number) => [formatPrice(v), 'Ціна']}
        labelFormatter={formatDate}
      />
    ),
  };

  if (type === 'line') {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          {commonAxis.grid}
          {commonAxis.xAxis}
          {commonAxis.yAxis}
          {commonAxis.tooltip}
          <Line
            type="monotone" dataKey="close" stroke={color}
            strokeWidth={2} dot={false} activeDot={{ r: 4, fill: color }}
            name="Ціна"
          />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (type === 'area') {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={color} stopOpacity={0.35} />
              <stop offset="95%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          {commonAxis.grid}
          {commonAxis.xAxis}
          {commonAxis.yAxis}
          {commonAxis.tooltip}
          <Area
            type="monotone" dataKey="close" stroke={color}
            strokeWidth={2} fill="url(#areaGrad)" name="Ціна"
            dot={false} activeDot={{ r: 4, fill: color }}
          />
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  /* bar / volume */
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        {commonAxis.grid}
        {commonAxis.xAxis}
        <YAxis
          stroke={AXIS_STROKE}
          tick={AXIS_STYLE}
          axisLine={{ stroke: AXIS_STROKE }}
          tickLine={{ stroke: AXIS_STROKE }}
          width={80}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          labelStyle={TOOLTIP_LABEL_STYLE}
          labelFormatter={formatDate}
        />
        <Bar dataKey="volume" fill={color} name="Обсяг" opacity={0.8} radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
};

/* ── Chart type selector ─────────────────────────────────────────────────── */
interface ChartTypeSelectorProps {
  currentType: string;
  onTypeChange: (type: string) => void;
}

const CHART_TYPES = [
  { value: 'line',   label: 'Лінія' },
  { value: 'area',   label: 'Область' },
  { value: 'volume', label: 'Обсяг' },
];

export const ChartTypeSelector: React.FC<ChartTypeSelectorProps> = ({
  currentType,
  onTypeChange,
}) => (
  <div
    className="flex gap-1 rounded-lg p-1"
    style={{ background: 'var(--c-bg-3)' }}
  >
    {CHART_TYPES.map(t => (
      <button
        key={t.value}
        onClick={() => onTypeChange(t.value)}
        className="px-3 py-1 rounded-md text-xs font-semibold transition-all duration-150"
        style={
          currentType === t.value
            ? { background: 'var(--c-accent)', color: 'var(--c-accent-text)' }
            : { color: 'var(--c-text-3)' }
        }
        onMouseEnter={e => {
          if (currentType !== t.value)
            (e.currentTarget as HTMLButtonElement).style.color = 'var(--c-text-2)';
        }}
        onMouseLeave={e => {
          if (currentType !== t.value)
            (e.currentTarget as HTMLButtonElement).style.color = 'var(--c-text-3)';
        }}
      >
        {t.label}
      </button>
    ))}
  </div>
);
