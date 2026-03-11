import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { DealBadge } from './DealBadge';

describe('DealBadge', () => {
  it('не отображается при выгоде меньше 10%', () => {
    render(<DealBadge dealPercent={-5} />);
    expect(screen.queryByText(/-5%/)).not.toBeInTheDocument();
  });

  it('не отображается при выгоде ровно -10%', () => {
    render(<DealBadge dealPercent={-10} />);
    expect(screen.queryByText(/-10%/)).not.toBeInTheDocument();
  });

  it('отображается при выгоде -11%', () => {
    render(<DealBadge dealPercent={-11} />);
    // Текст разбит на элементы (🔥, -11, %), используем regex
    expect(screen.getByText(/-11/)).toBeInTheDocument();
  });

  it('имеет оранжевый градиент при выгоде от -10% до -15%', () => {
    const { container } = render(<DealBadge dealPercent={-12} />);
    const innerDiv = container.querySelector('.inline-flex');
    expect(innerDiv).toHaveClass('from-orange-400');
    expect(innerDiv).toHaveClass('to-orange-500');
  });

  it('имеет красно-оранжевый градиент при выгоде от -15% до -20%', () => {
    const { container } = render(<DealBadge dealPercent={-17} />);
    const innerDiv = container.querySelector('.inline-flex');
    expect(innerDiv).toHaveClass('from-orange-500');
    expect(innerDiv).toHaveClass('to-red-500');
  });

  it('имеет красный градиент при выгоде больше -20%', () => {
    const { container } = render(<DealBadge dealPercent={-25} />);
    const innerDiv = container.querySelector('.inline-flex');
    expect(innerDiv).toHaveClass('from-red-500');
    expect(innerDiv).toHaveClass('to-red-600');
  });

  it('имеет анимацию fade-in', () => {
    const { container } = render(<DealBadge dealPercent={-15} />);
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv).toHaveClass('animate-fade-in');
  });

  it('применяет дополнительные className', () => {
    const { container } = render(<DealBadge dealPercent={-15} className="custom-class" />);
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv).toHaveClass('custom-class');
  });

  it('корректно округляет проценты', () => {
    render(<DealBadge dealPercent={-15.7} />);
    // Текст разбит на элементы, используем regex
    expect(screen.getByText(/-16/)).toBeInTheDocument();
  });

  it('имеет правильную структуру DOM', () => {
    const { container } = render(<DealBadge dealPercent={-20} />);
    const outerDiv = container.firstChild as HTMLElement;
    const innerDiv = outerDiv?.firstChild as HTMLElement;

    // Позиционирование изменено на left-2 для избежания наложения на статус
    expect(outerDiv).toHaveClass('absolute', 'top-2', 'left-2', 'z-10', 'animate-fade-in');
    expect(innerDiv).toHaveClass('rounded-full', 'px-2', 'py-1', 'text-xs', 'font-bold');
  });
});
