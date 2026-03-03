import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Separator } from '@/components/ui/separator';

describe('Separator', () => {
  it('renders horizontal Separator', () => {
    const { container } = render(<Separator orientation="horizontal" />);
    expect(container.firstChild).toBeInTheDocument();
    expect(container.firstChild).toHaveAttribute('data-orientation', 'horizontal');
  });

  it('renders vertical Separator', () => {
    const { container } = render(<Separator orientation="vertical" />);
    expect(container.firstChild).toBeInTheDocument();
    expect(container.firstChild).toHaveAttribute('data-orientation', 'vertical');
  });

  it('renders with default orientation', () => {
    const { container } = render(<Separator />);
    expect(container.firstChild).toHaveAttribute('data-orientation', 'horizontal');
  });

  it('applies custom className', () => {
    const { container } = render(<Separator className="custom-separator" />);
    expect(container.firstChild).toHaveClass('custom-separator');
  });

  it('has data-orientation attribute', () => {
    const { container } = render(<Separator />);
    expect(container.firstChild).toHaveAttribute('data-orientation', 'horizontal');
  });

  it('renders between elements', () => {
    const { container } = render(
      <div>
        <span>First</span>
        <Separator />
        <span>Second</span>
      </div>
    );

    expect(container.textContent).toContain('First');
    expect(container.textContent).toContain('Second');
    expect(container.querySelectorAll('[data-orientation]')).toHaveLength(1);
  });
});
