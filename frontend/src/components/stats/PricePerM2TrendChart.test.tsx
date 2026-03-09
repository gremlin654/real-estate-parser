import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PricePerM2TrendChart } from './PricePerM2TrendChart';

// Mock recharts
vi.mock('recharts', () => ({
  LineChart: ({ children, data }: any) => (
    <div data-testid="line-chart">
      {typeof children === 'function' ? children(data) : children}
    </div>
  ),
  Line: ({ dataKey, name, stroke }: any) => (
    <div data-testid={`line-${dataKey}`} data-name={name} data-stroke={stroke} />
  ),
  XAxis: ({ dataKey }: any) => <div data-testid="x-axis" data-key={dataKey} />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => (
    <div style={{ width: '100%', height: 350 }}>{children}</div>
  ),
}));

describe('PricePerM2TrendChart', () => {
  const mockData = [
    { date: '2025-01-01', average: 2450, median: 2400, count: 45 },
    { date: '2025-01-02', average: 2480, median: 2430, count: 52 },
    { date: '2025-01-03', average: 2510, median: 2460, count: 48 },
  ];

  it('должен рендерить график с данными', () => {
    render(<PricePerM2TrendChart data={mockData} currency="USD" />);
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    expect(screen.getByTestId('line-average')).toBeInTheDocument();
    expect(screen.getByTestId('line-median')).toBeInTheDocument();
  });

  it('должен показывать сообщение когда нет данных', () => {
    render(<PricePerM2TrendChart data={[]} currency="USD" />);
    expect(screen.getByText('Нет данных для отображения')).toBeInTheDocument();
  });

  it('должен рендерить две линии (средняя и медиана)', () => {
    render(<PricePerM2TrendChart data={mockData} currency="USD" />);
    const lines = screen.getAllByTestId(/line-(average|median)/);
    expect(lines).toHaveLength(2);
  });

  it('должен использовать правильные цвета для линий', () => {
    render(<PricePerM2TrendChart data={mockData} currency="USD" />);
    const averageLine = screen.getByTestId('line-average');
    const medianLine = screen.getByTestId('line-median');
    
    expect(averageLine.getAttribute('data-stroke')).toBe('#3b82f6');
    expect(medianLine.getAttribute('data-stroke')).toBe('#22c55e');
  });

  it('должен отображать правильные названия для линий', () => {
    render(<PricePerM2TrendChart data={mockData} currency="USD" />);
    const averageLine = screen.getByTestId('line-average');
    const medianLine = screen.getByTestId('line-median');
    
    expect(averageLine.getAttribute('data-name')).toBe('Средняя');
    expect(medianLine.getAttribute('data-name')).toBe('Медиана');
  });

  it('должен работать с BYN валютой', () => {
    render(<PricePerM2TrendChart data={mockData} currency="BYN" />);
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('должен рендерить с period prop', () => {
    render(<PricePerM2TrendChart data={mockData} currency="USD" period={90} />);
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });
});
