import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PriceDropBadge } from './PriceDropBadge';

describe('PriceDropBadge', () => {
  it('не отображается при падении меньше 5%', () => {
    const { container } = render(<PriceDropBadge dropPercent={3} />);
    expect(container.firstChild).toBeNull();
  });

  it('отображается при падении 5%', () => {
    render(<PriceDropBadge dropPercent={5} />);
    expect(screen.getByText('5%')).toBeInTheDocument();
  });

  it('отображается при падении 7% (жёлтый)', () => {
    render(<PriceDropBadge dropPercent={7} />);
    expect(screen.getByText('7%')).toBeInTheDocument();
    expect(screen.getByText('📉')).toBeInTheDocument();
  });

  it('отображается при падении 15% (оранжевый)', () => {
    render(<PriceDropBadge dropPercent={15} />);
    expect(screen.getByText('15%')).toBeInTheDocument();
  });

  it('отображается при падении 25% (красный)', () => {
    render(<PriceDropBadge dropPercent={25} />);
    expect(screen.getByText('25%')).toBeInTheDocument();
  });

  it('отображается при экстремальном падении 40%', () => {
    render(<PriceDropBadge dropPercent={40} />);
    expect(screen.getByText('40%')).toBeInTheDocument();
  });

  it('имеет правильную позицию (absolute top-2 left-2)', () => {
    const { container } = render(<PriceDropBadge dropPercent={10} />);
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv).toHaveClass('absolute', 'top-2', 'left-2');
  });

  it('имеет анимацию fade-in', () => {
    const { container } = render(<PriceDropBadge dropPercent={10} />);
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv).toHaveClass('animate-fade-in');
  });

  it('применяет custom className', () => {
    const { container } = render(<PriceDropBadge dropPercent={10} className="custom-class" />);
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv).toHaveClass('custom-class');
  });

  it('имеет градиент для 5-10% (жёлтый)', () => {
    const { container } = render(<PriceDropBadge dropPercent={7} />);
    // Ищем внутренний div с градиентом по наличию текста с процентами
    const innerDiv = container.querySelector('div.inline-flex') as HTMLElement;
    expect(innerDiv).toHaveClass('from-yellow-400', 'to-yellow-500');
  });

  it('имеет градиент для 10-20% (оранжевый)', () => {
    const { container } = render(<PriceDropBadge dropPercent={15} />);
    const innerDiv = container.querySelector('div.inline-flex') as HTMLElement;
    expect(innerDiv).toHaveClass('from-orange-400', 'to-orange-500');
  });

  it('имеет градиент для 20%+ (красный)', () => {
    const { container } = render(<PriceDropBadge dropPercent={25} />);
    const innerDiv = container.querySelector('div.inline-flex') as HTMLElement;
    expect(innerDiv).toHaveClass('from-red-500', 'to-red-600');
  });
});
