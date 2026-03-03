import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Progress } from '@/components/ui/progress';

describe('Progress', () => {
  it('renders progress bar', () => {
    const { container } = render(<Progress value={50} />);
    expect(container.querySelector('[role="progressbar"]')).toBeInTheDocument();
  });

  it('renders with default value', () => {
    const { container } = render(<Progress />);
    const progressbar = container.querySelector('[role="progressbar"]');
    expect(progressbar).toBeInTheDocument();
  });

  it('renders with specified value', () => {
    const { container } = render(<Progress value={75} />);
    const progressbar = container.querySelector('[role="progressbar"]');
    expect(progressbar).toBeInTheDocument();
  });

  it('renders with value 0', () => {
    const { container } = render(<Progress value={0} />);
    expect(container.querySelector('[role="progressbar"]')).toBeInTheDocument();
  });

  it('renders with value 100', () => {
    const { container } = render(<Progress value={100} />);
    expect(container.querySelector('[role="progressbar"]')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Progress value={50} className="custom-progress" />);
    expect(container.querySelector('[role="progressbar"]')).toHaveClass('custom-progress');
  });

  it('has progress element', () => {
    const { container } = render(<Progress value={50} />);
    const progressbar = container.querySelector('[role="progressbar"]');
    expect(progressbar).toHaveClass('bg-primary/20');
  });
});
