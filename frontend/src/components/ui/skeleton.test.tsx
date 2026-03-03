import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Skeleton } from '@/components/ui/skeleton';

describe('Skeleton', () => {
  it('renders Skeleton component', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Skeleton className="custom-skeleton" />);
    expect(container.firstChild).toHaveClass('custom-skeleton');
  });

  it('has default classes', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toHaveClass('animate-pulse');
  });

  it('renders as div by default', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild?.tagName).toBe('DIV');
  });

  it('can be used as placeholder', () => {
    render(
      <div>
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-4 w-32" />
      </div>
    );

    const { container } = render(
      <div>
        <Skeleton />
        <Skeleton />
      </div>
    );
    expect(container.querySelectorAll('div').length).toBeGreaterThanOrEqual(2);
  });

  it('applies height classes', () => {
    const { container } = render(<Skeleton className="h-20" />);
    expect(container.firstChild).toHaveClass('h-20');
  });

  it('applies width classes', () => {
    const { container } = render(<Skeleton className="w-64" />);
    expect(container.firstChild).toHaveClass('w-64');
  });

  it('applies rounded classes', () => {
    const { container } = render(<Skeleton className="rounded-full" />);
    expect(container.firstChild).toHaveClass('rounded-full');
  });
});
