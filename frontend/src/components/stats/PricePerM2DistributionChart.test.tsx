import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PricePerM2DistributionChart } from './PricePerM2DistributionChart';

// Mock recharts
vi.mock('recharts', () => ({
  BarChart: ({ children, data }: any) => (
    <div data-testid="bar-chart">
      {typeof children === 'function' ? children(data) : children}
    </div>
  ),
  Bar: ({ dataKey, name, fill, children }: any) => (
    <div data-testid="bar" data-key={dataKey} data-name={name} data-fill={fill}>
      {children}
    </div>
  ),
  Cell: ({ fill }: any) => <div data-testid="cell" data-fill={fill} />,
  XAxis: ({ dataKey }: any) => <div data-testid="x-axis" data-key={dataKey} />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => (
    <div style={{ width: '100%', height: 350 }}>{children}</div>
  ),
}));

describe('PricePerM2DistributionChart', () => {
  const mockData = [
    { range_min: 1000, range_max: 1500, count: 45, percentage: 15.2 },
    { range_min: 1500, range_max: 2000, count: 120, percentage: 40.5 },
    { range_min: 2000, range_max: 2500, count: 85, percentage: 28.7 },
    { range_min: 2500, range_max: 3000, count: 46, percentage: 15.6 },
  ];

  it('должен рендерить график с данными', () => {
    render(<PricePerM2DistributionChart data={mockData} currency="USD" />);
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    expect(screen.getByTestId('bar')).toBeInTheDocument();
  });

  it('должен показывать сообщение когда нет данных', () => {
    render(<PricePerM2DistributionChart data={[]} currency="USD" />);
    expect(screen.getByText('Нет данных для отображения')).toBeInTheDocument();
  });

  it('должен рендерить ячейки для каждого бина', () => {
    render(<PricePerM2DistributionChart data={mockData} currency="USD" />);
    const cells = screen.getAllByTestId('cell');
    expect(cells).toHaveLength(4);
  });

  it('должен использовать правильные названия осей', () => {
    render(<PricePerM2DistributionChart data={mockData} currency="USD" />);
    expect(screen.getByTestId('x-axis')).toBeInTheDocument();
    expect(screen.getByTestId('y-axis')).toBeInTheDocument();
  });

  it('должен работать с BYN валютой', () => {
    render(<PricePerM2DistributionChart data={mockData} currency="BYN" />);
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('должен генерировать разные цвета для разных бинов', () => {
    render(<PricePerM2DistributionChart data={mockData} currency="USD" />);
    const cells = screen.getAllByTestId('cell');
    const fills = cells.map(cell => cell.getAttribute('data-fill'));
    
    // Проверяем что цвета разные
    const uniqueFills = new Set(fills);
    expect(uniqueFills.size).toBe(4);
  });

  it('должен показывать правильные названия в legend', () => {
    render(<PricePerM2DistributionChart data={mockData} currency="USD" />);
    const bar = screen.getByTestId('bar');
    expect(bar.getAttribute('data-name')).toBe('Объявлений');
  });
});
