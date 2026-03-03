import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';

describe('Card', () => {
  it('renders Card component', () => {
    render(<Card>Card Content</Card>);
    expect(screen.getByText('Card Content')).toBeInTheDocument();
  });

  it('renders CardHeader', () => {
    render(<CardHeader>Header</CardHeader>);
    expect(screen.getByText('Header')).toBeInTheDocument();
  });

  it('renders CardTitle', () => {
    render(<CardTitle>Title</CardTitle>);
    expect(screen.getByText('Title')).toBeInTheDocument();
  });

  it('renders CardDescription', () => {
    render(<CardDescription>Description</CardDescription>);
    expect(screen.getByText('Description')).toBeInTheDocument();
  });

  it('renders CardContent', () => {
    render(<CardContent>Content</CardContent>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('renders CardFooter', () => {
    render(<CardFooter>Footer</CardFooter>);
    expect(screen.getByText('Footer')).toBeInTheDocument();
  });

  it('renders complete Card structure', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>My Title</CardTitle>
          <CardDescription>My Description</CardDescription>
        </CardHeader>
        <CardContent>My Content</CardContent>
        <CardFooter>My Footer</CardFooter>
      </Card>
    );

    expect(screen.getByText('My Title')).toBeInTheDocument();
    expect(screen.getByText('My Description')).toBeInTheDocument();
    expect(screen.getByText('My Content')).toBeInTheDocument();
    expect(screen.getByText('My Footer')).toBeInTheDocument();
  });

  it('applies custom className to Card', () => {
    render(<Card className="custom-card">Content</Card>);
    expect(screen.getByText('Content')).toHaveClass('custom-card');
  });

  it('applies custom className to CardHeader', () => {
    render(<CardHeader className="custom-header">Header</CardHeader>);
    expect(screen.getByText('Header')).toHaveClass('custom-header');
  });

  it('applies custom className to CardContent', () => {
    render(<CardContent className="custom-content">Content</CardContent>);
    expect(screen.getByText('Content')).toHaveClass('custom-content');
  });
});
