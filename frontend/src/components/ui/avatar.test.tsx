import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Avatar, AvatarImage, AvatarFallback } from './avatar';

describe('Avatar', () => {
  it('renders Avatar component with fallback', () => {
    render(
      <Avatar>
        <AvatarFallback>A</AvatarFallback>
      </Avatar>
    );

    expect(screen.getByText('A')).toBeInTheDocument();
  });

  it('renders Avatar with fallback text', () => {
    render(
      <Avatar>
        <AvatarFallback>JD</AvatarFallback>
      </Avatar>
    );

    expect(screen.getByText('JD')).toBeInTheDocument();
  });

  it('applies custom className to Avatar', () => {
    const { container } = render(
      <Avatar className="custom-class">
        <AvatarFallback>T</AvatarFallback>
      </Avatar>
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('renders Avatar component structure', () => {
    const { container } = render(
      <Avatar>
        <AvatarFallback>FB</AvatarFallback>
      </Avatar>
    );

    // Check that Avatar renders a span element
    expect(container.querySelector('span')).toBeInTheDocument();
  });
});
