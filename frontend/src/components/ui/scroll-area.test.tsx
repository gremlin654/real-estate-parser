import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { ScrollArea } from '@/components/ui/scroll-area';

describe('ScrollArea', () => {
  it('renders ScrollArea component', () => {
    const { container } = render(
      <ScrollArea className="h-[200px]">
        <div>Scrollable content</div>
      </ScrollArea>
    );
    expect(container.textContent).toContain('Scrollable content');
  });

  it('renders with children', () => {
    const { container } = render(
      <ScrollArea>
        <div>Child content</div>
      </ScrollArea>
    );
    expect(container.textContent).toContain('Child content');
  });

  it('applies custom className', () => {
    const { container } = render(
      <ScrollArea className="custom-scroll">
        <div>Content</div>
      </ScrollArea>
    );
    expect(container.firstChild).toHaveClass('custom-scroll');
  });

  it('renders with multiple children', () => {
    const { container } = render(
      <ScrollArea>
        <div>Item 1</div>
        <div>Item 2</div>
        <div>Item 3</div>
      </ScrollArea>
    );
    expect(container.textContent).toContain('Item 1');
    expect(container.textContent).toContain('Item 2');
    expect(container.textContent).toContain('Item 3');
  });
});
