import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { DealScoreBadge } from '../DealScoreBadge';

describe('DealScoreBadge', () => {
  it('score=85 → зелёный фон, текст "🔥 85"', () => {
    const { container } = render(<DealScoreBadge score={85} />);
    const badge = container.querySelector('.inline-flex');
    
    expect(badge).toHaveTextContent('🔥');
    expect(badge).toHaveTextContent('85');
    expect(badge).toHaveClass('from-green-500');
    expect(badge).toHaveClass('to-emerald-600');
  });

  it('score=70 → зелёный фон, текст "🔥 70"', () => {
    const { container } = render(<DealScoreBadge score={70} />);
    const badge = container.querySelector('.inline-flex');
    
    expect(badge).toHaveTextContent('🔥');
    expect(badge).toHaveTextContent('70');
    expect(badge).toHaveClass('from-green-500');
    expect(badge).toHaveClass('to-emerald-600');
  });

  it('score=40 → жёлтый фон, текст "👍 40"', () => {
    const { container } = render(<DealScoreBadge score={40} />);
    const badge = container.querySelector('.inline-flex');

    expect(badge).toHaveTextContent('👍');
    expect(badge).toHaveTextContent('40');
    expect(badge).toHaveClass('from-yellow-400');
    expect(badge).toHaveClass('to-orange-500');
  });

  it("size='sm' → маленький размер", () => {
    const { container } = render(<DealScoreBadge score={80} size="sm" />);
    const badge = container.querySelector('.inline-flex');
    
    expect(badge).toHaveClass('text-[11px]');
    expect(badge).toHaveClass('px-1.5');
    expect(badge).toHaveClass('py-0.5');
  });

  it("size='lg' → большой размер", () => {
    const { container } = render(<DealScoreBadge score={80} size="lg" />);
    const badge = container.querySelector('.inline-flex');
    
    expect(badge).toHaveClass('text-sm');
    expect(badge).toHaveClass('px-2.5');
    expect(badge).toHaveClass('py-1');
  });

  it('label prop → кастомный label', () => {
    const { container } = render(<DealScoreBadge score={85} label="🎯 SUPER" />);
    const badge = container.querySelector('.inline-flex');
    
    expect(badge).toHaveTextContent('🎯 SUPER');
    expect(badge).toHaveTextContent('85');
  });

  it('className prop → дополнительные классы', () => {
    const { container } = render(<DealScoreBadge score={85} className="custom-class" />);
    const badge = container.querySelector('.inline-flex');
    
    expect(badge).toHaveClass('custom-class');
  });

  it('Hover tooltip → показывает title', () => {
    const { container } = render(<DealScoreBadge score={85} />);
    const badge = container.querySelector('.inline-flex');
    
    expect(badge).toHaveAttribute('title', 'Deal Score: 85/100');
  });

  it('score=0 → серый фон, не отображается (ниже порога)', () => {
    const { container } = render(<DealScoreBadge score={0} />);
    const badge = container.querySelector('.inline-flex');
    
    expect(badge).toBeNull();
  });

  it('score=100 → зелёный фон', () => {
    const { container } = render(<DealScoreBadge score={100} />);
    const badge = container.querySelector('.inline-flex');
    
    expect(badge).toHaveTextContent('🔥');
    expect(badge).toHaveTextContent('100');
    expect(badge).toHaveClass('from-green-500');
    expect(badge).toHaveClass('to-emerald-600');
  });

  it('score=59 → зелёный (>=50)', () => {
    const { container } = render(<DealScoreBadge score={59} />);
    const badge = container.querySelector('.inline-flex');

    expect(badge).toHaveTextContent('🔥');
    expect(badge).toHaveTextContent('59');
    expect(badge).toHaveClass('from-green-500');
    expect(badge).toHaveClass('to-emerald-600');
  });

  it('score=60 → зелёный (>=50)', () => {
    const { container } = render(<DealScoreBadge score={60} />);
    const badge = container.querySelector('.inline-flex');

    expect(badge).toHaveTextContent('🔥');
    expect(badge).toHaveTextContent('60');
    expect(badge).toHaveClass('from-green-500');
    expect(badge).toHaveClass('to-emerald-600');
  });
});
