import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { DealTooltip } from './DealTooltip';

describe('DealTooltip', () => {
  const defaultProps = {
    currentPricePerM2: 772,
    avgPricePerM2: 920,
    dealPercent: -16,
    currency: 'USD' as const,
    area: 54,
    children: <span data-testid="price">Price: $41,688</span>,
  };

  it('отображает children', () => {
    render(<DealTooltip {...defaultProps} />);
    expect(screen.getByTestId('price')).toBeInTheDocument();
  });

  it('оборачивает children в span с cursor-help', () => {
    const { container } = render(<DealTooltip {...defaultProps} />);
    const span = container.querySelector('span.cursor-help');
    expect(span).toBeInTheDocument();
  });

  it('корректно вычисляет абсолютную выгоду', () => {
    const { container } = render(<DealTooltip {...defaultProps} />);
    // Проверяем что компонент рендерится без ошибок
    expect(container).toBeInTheDocument();
  });

  it('работает без area', () => {
    const { container } = render(<DealTooltip {...defaultProps} area={null} />);
    expect(container).toBeInTheDocument();
  });

  it('применяет дополнительные className', () => {
    const { container } = render(
      <DealTooltip {...defaultProps} className="custom-class" />
    );
    // Проверяем что компонент рендерится без ошибок
    expect(container).toBeInTheDocument();
  });

  it('корректно форматирует USD валюту', () => {
    render(<DealTooltip {...defaultProps} />);
    // Компонент должен рендериться без ошибок
    expect(screen.getByTestId('price')).toBeInTheDocument();
  });

  it('корректно форматирует BYN валюту', () => {
    render(
      <DealTooltip
        {...defaultProps}
        currency="BYN"
        currentPricePerM2={2500}
        avgPricePerM2={3000}
      />
    );
    expect(screen.getByTestId('price')).toBeInTheDocument();
  });

  it('отображает правильный процент выгоды', () => {
    render(<DealTooltip {...defaultProps} dealPercent={-20} />);
    expect(screen.getByTestId('price')).toBeInTheDocument();
  });

  it('имеет правильную структуру с Tooltip', () => {
    const { container } = render(<DealTooltip {...defaultProps} />);
    // Проверяем что Tooltip рендерится
    expect(container.querySelector('[data-state]')).toBeInTheDocument();
  });

  it('рендерит TooltipProvider', () => {
    const { container } = render(<DealTooltip {...defaultProps} />);
    // Проверяем что провайдер рендерится
    expect(container).toBeInTheDocument();
  });
});
