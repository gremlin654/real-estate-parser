import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationPrevious,
  PaginationNext,
  PaginationEllipsis,
} from './pagination';

describe('Pagination', () => {
  it('renders Pagination component with correct attributes', () => {
    render(
      <Pagination>
        <PaginationContent>
          <PaginationItem>
            <PaginationLink href="#">1</PaginationLink>
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );

    const nav = screen.getByRole('navigation', { name: 'pagination' });
    expect(nav).toBeInTheDocument();
  });

  it('renders PaginationContent', () => {
    render(
      <Pagination>
        <PaginationContent data-testid="content">
          <PaginationItem>
            <PaginationLink href="#">1</PaginationLink>
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );

    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('renders PaginationItem', () => {
    render(
      <Pagination>
        <PaginationContent>
          <PaginationItem data-testid="item">
            <PaginationLink href="#">1</PaginationLink>
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );

    expect(screen.getByTestId('item')).toBeInTheDocument();
  });

  it('renders PaginationLink with correct attributes', () => {
    render(
      <Pagination>
        <PaginationContent>
          <PaginationItem>
            <PaginationLink href="#page-1" data-testid="link">
              1
            </PaginationLink>
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );

    const link = screen.getByTestId('link');
    expect(link).toHaveAttribute('href', '#page-1');
    expect(link).not.toHaveAttribute('aria-current');
  });

  it('renders PaginationLink with isActive state', () => {
    render(
      <Pagination>
        <PaginationContent>
          <PaginationItem>
            <PaginationLink href="#page-2" isActive data-testid="active-link">
              2
            </PaginationLink>
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );

    const link = screen.getByTestId('active-link');
    expect(link).toHaveAttribute('aria-current', 'page');
  });

  it('renders PaginationPrevious with correct label and icon', () => {
    render(
      <Pagination>
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious href="#prev" data-testid="prev" />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );

    const prev = screen.getByTestId('prev');
    expect(prev).toHaveAttribute('aria-label', 'Go to previous page');
    expect(prev).toHaveTextContent('Previous');
  });

  it('renders PaginationNext with correct label and icon', () => {
    render(
      <Pagination>
        <PaginationContent>
          <PaginationItem>
            <PaginationNext href="#next" data-testid="next" />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );

    const next = screen.getByTestId('next');
    expect(next).toHaveAttribute('aria-label', 'Go to next page');
    expect(next).toHaveTextContent('Next');
  });

  it('renders PaginationEllipsis', () => {
    render(
      <Pagination>
        <PaginationContent>
          <PaginationItem>
            <PaginationEllipsis data-testid="ellipsis" />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );

    const ellipsis = screen.getByTestId('ellipsis');
    expect(ellipsis).toBeInTheDocument();
    expect(screen.getByText('More pages', { selector: '.sr-only' })).toBeInTheDocument();
  });

  it('applies custom className to Pagination', () => {
    render(
      <Pagination className="custom-class" data-testid="pagination">
        <PaginationContent>
          <PaginationItem>
            <PaginationLink href="#">1</PaginationLink>
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );

    expect(screen.getByTestId('pagination')).toHaveClass('custom-class');
  });

  it('applies custom className to PaginationContent', () => {
    render(
      <Pagination>
        <PaginationContent className="custom-gap" data-testid="content">
          <PaginationItem>
            <PaginationLink href="#">1</PaginationLink>
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );

    expect(screen.getByTestId('content')).toHaveClass('custom-gap');
  });
});
