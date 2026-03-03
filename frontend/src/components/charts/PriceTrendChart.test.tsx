import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { PriceTrendChart } from './PriceTrendChart';

// Mock Recharts
vi.mock('recharts', () => ({
  LineChart: ({ children, data }: any) => (
    <div data-testid="line-chart" data-data={JSON.stringify(data)}>
      {children}
    </div>
  ),
  Line: ({ dataKey }: any) => <div data-testid="line" data-key={dataKey} />,
  XAxis: ({ dataKey }: any) => <div data-testid="xaxis" data-key={dataKey} />,
  YAxis: () => <div data-testid="yaxis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children, height }: any) => (
    <div data-testid="responsive-container" style={{ height }}>
      {children}
    </div>
  ),
}));

describe('PriceTrendChart', () => {
  const mockData = [
    { year: 2024, month: 1, avg_price_usd: 85000, avg_price_byn: 280000 },
    { year: 2024, month: 2, avg_price_usd: 86000, avg_price_byn: 282000 },
    { year: 2024, month: 3, avg_price_usd: 87000, avg_price_byn: 285000 },
    { year: 2024, month: 4, avg_price_usd: 88000, avg_price_byn: 288000 },
    { year: 2024, month: 5, avg_price_usd: 89000, avg_price_byn: 291000 },
    { year: 2024, month: 6, avg_price_usd: 90000, avg_price_byn: 294000 },
  ];

  it('renders loading state', () => {
    render(<PriceTrendChart data={[]} rooms={1} isLoading={true} />);

    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });

  it('renders no data state when data is empty', () => {
    render(<PriceTrendChart data={[]} rooms={1} isLoading={false} />);

    expect(screen.getByText(/No data available/i)).toBeInTheDocument();
  });

  it('renders no data state when data is null', () => {
    render(<PriceTrendChart data={null as any} rooms={1} isLoading={false} />);

    expect(screen.getByText(/No data available/i)).toBeInTheDocument();
  });

  it('renders chart with data', async () => {
    render(<PriceTrendChart data={mockData} rooms={2} isLoading={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    expect(screen.getByTestId('line')).toBeInTheDocument();
    expect(screen.getByTestId('xaxis')).toBeInTheDocument();
    expect(screen.getByTestId('yaxis')).toBeInTheDocument();
    expect(screen.getByTestId('cartesian-grid')).toBeInTheDocument();
    expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('displays correct number of data points', async () => {
    render(<PriceTrendChart data={mockData} rooms={1} isLoading={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    const chart = screen.getByTestId('line-chart');
    const chartData = JSON.parse(chart.getAttribute('data-data') || '[]');
    expect(chartData).toHaveLength(6);
  });

  it('formats month labels correctly', async () => {
    render(<PriceTrendChart data={mockData} rooms={1} isLoading={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    const chart = screen.getByTestId('line-chart');
    const chartData = JSON.parse(chart.getAttribute('data-data') || '[]');
    
    expect(chartData[0].label).toBe('Jan 2024');
    expect(chartData[1].label).toBe('Feb 2024');
    expect(chartData[5].label).toBe('Jun 2024');
  });

  it('renders with different room counts', async () => {
    render(<PriceTrendChart data={mockData} rooms={3} isLoading={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('renders with single data point', async () => {
    const singleData = [
      { year: 2024, month: 1, avg_price_usd: 85000, avg_price_byn: 280000 },
    ];

    render(<PriceTrendChart data={singleData} rooms={1} isLoading={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  it('renders with large dataset', async () => {
    const largeData = Array.from({ length: 24 }, (_, i) => ({
      year: 2024,
      month: (i % 12) + 1,
      avg_price_usd: 80000 + i * 1000,
      avg_price_byn: 260000 + i * 3000,
    }));

    render(<PriceTrendChart data={largeData} rooms={2} isLoading={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    const chart = screen.getByTestId('line-chart');
    const chartData = JSON.parse(chart.getAttribute('data-data') || '[]');
    expect(chartData).toHaveLength(24);
  });

  it('renders chart with correct dataKey', async () => {
    render(<PriceTrendChart data={mockData} rooms={1} isLoading={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    const line = screen.getByTestId('line');
    expect(line.getAttribute('data-key')).toBe('avg_price_usd');
  });

  it('applies correct height to ResponsiveContainer', async () => {
    render(<PriceTrendChart data={mockData} rooms={1} isLoading={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    const container = screen.getByTestId('responsive-container');
    expect(container).toHaveStyle('height: 300px');
  });

  it('handles data with varying prices', async () => {
    const varyingData = [
      { year: 2023, month: 12, avg_price_usd: 50000, avg_price_byn: 160000 },
      { year: 2024, month: 1, avg_price_usd: 100000, avg_price_byn: 320000 },
      { year: 2024, month: 2, avg_price_usd: 75000, avg_price_byn: 240000 },
    ];

    render(<PriceTrendChart data={varyingData} rooms={1} isLoading={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  it('renders chart immediately when not loading', () => {
    const { container } = render(
      <PriceTrendChart data={mockData} rooms={1} isLoading={false} />
    );

    expect(container.querySelector('[data-testid="line-chart"]')).toBeInTheDocument();
  });
});
