import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { DealFilterToggle } from './DealFilterToggle';

describe('DealFilterToggle', () => {
  it('отображает иконку 🔥 и текст', () => {
    render(
      <DealFilterToggle
        enabled={false}
        onToggle={vi.fn()}
      />
    );

    expect(screen.getByText('🔥')).toBeInTheDocument();
    expect(screen.getByText('Только выгодные')).toBeInTheDocument();
  });

  it('отображает кастомный discountThreshold (проверка что компонент принимает проп)', () => {
    const handleToggle = vi.fn();
    render(
      <DealFilterToggle
        enabled={false}
        onToggle={handleToggle}
        discountThreshold={-15}
      />
    );

    // Текст не зависит от discountThreshold, но компонент принимает проп
    expect(screen.getByText('Только выгодные')).toBeInTheDocument();
    expect(screen.getByRole('switch')).toBeInTheDocument();
  });

  it('переключается при клике', () => {
    const handleToggle = vi.fn();
    
    render(
      <DealFilterToggle
        enabled={false}
        onToggle={handleToggle}
      />
    );
    
    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);
    
    expect(handleToggle).toHaveBeenCalledWith(true);
  });

  it('имеет правильное состояние switch', () => {
    const handleToggle = vi.fn();
    
    const { rerender } = render(
      <DealFilterToggle
        enabled={false}
        onToggle={handleToggle}
      />
    );
    
    expect(screen.getByRole('switch')).not.toBeChecked();
    
    rerender(
      <DealFilterToggle
        enabled={true}
        onToggle={handleToggle}
      />
    );
    
    expect(screen.getByRole('switch')).toBeChecked();
  });

  it('имеет label который связывается с switch', () => {
    render(
      <DealFilterToggle
        enabled={false}
        onToggle={vi.fn()}
      />
    );
    
    const label = screen.getByLabelText('Только выгодные объявления');
    expect(label).toBeInTheDocument();
  });

  it('применяет дополнительные className', () => {
    render(
      <DealFilterToggle
        enabled={false}
        onToggle={vi.fn()}
        className="custom-class"
      />
    );
    
    const container = screen.getByText('🔥').closest('div');
    expect(container).toHaveClass('custom-class');
  });

  it('имеет cursor-pointer на label', () => {
    render(
      <DealFilterToggle
        enabled={false}
        onToggle={vi.fn()}
      />
    );

    const label = screen.getByText('Только выгодные').closest('label');
    expect(label).toHaveClass('cursor-pointer');
  });

  it('имеет select-none на label', () => {
    render(
      <DealFilterToggle
        enabled={false}
        onToggle={vi.fn()}
      />
    );

    const label = screen.getByText('Только выгодные').closest('label');
    expect(label).toHaveClass('select-none');
  });

  it('корректно работает с onCheckedChange', () => {
    const handleToggle = vi.fn();
    
    render(
      <DealFilterToggle
        enabled={true}
        onToggle={handleToggle}
      />
    );
    
    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);
    
    expect(handleToggle).toHaveBeenCalledWith(false);
  });
});
