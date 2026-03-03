import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Table, TableHeader, TableBody, TableFooter, TableHead, TableRow, TableCell, TableCaption } from '@/components/ui/table';

describe('Table', () => {
  it('renders Table component', () => {
    render(<Table>Content</Table>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('renders TableHeader', () => {
    render(<TableHeader>Header</TableHeader>);
    expect(screen.getByText('Header')).toBeInTheDocument();
  });

  it('renders TableBody', () => {
    render(<TableBody>Body</TableBody>);
    expect(screen.getByText('Body')).toBeInTheDocument();
  });

  it('renders TableFooter', () => {
    render(<TableFooter>Footer</TableFooter>);
    expect(screen.getByText('Footer')).toBeInTheDocument();
  });

  it('renders TableHead', () => {
    render(
      <table>
        <TableRow>
          <TableHead>Head</TableHead>
        </TableRow>
      </table>
    );
    expect(screen.getByText('Head')).toBeInTheDocument();
  });

  it('renders TableRow', () => {
    render(
      <table>
        <TableRow>Cell</TableRow>
      </table>
    );
    expect(screen.getByText('Cell')).toBeInTheDocument();
  });

  it('renders TableCell', () => {
    render(
      <table>
        <TableRow>
          <TableCell>Cell</TableCell>
        </TableRow>
      </table>
    );
    expect(screen.getByText('Cell')).toBeInTheDocument();
  });

  it('renders TableCaption', () => {
    render(
      <table>
        <TableCaption>Caption</TableCaption>
      </table>
    );
    expect(screen.getByText('Caption')).toBeInTheDocument();
  });

  it('renders complete table structure', () => {
    render(
      <Table>
        <TableCaption>Test Caption</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Header 1</TableHead>
            <TableHead>Header 2</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Cell 1</TableCell>
            <TableCell>Cell 2</TableCell>
          </TableRow>
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell>Footer</TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    );

    expect(screen.getByText('Test Caption')).toBeInTheDocument();
    expect(screen.getByText('Header 1')).toBeInTheDocument();
    expect(screen.getByText('Header 2')).toBeInTheDocument();
    expect(screen.getByText('Cell 1')).toBeInTheDocument();
    expect(screen.getByText('Cell 2')).toBeInTheDocument();
    expect(screen.getByText('Footer')).toBeInTheDocument();
  });

  it('applies custom className to Table', () => {
    render(<Table className="custom-table">Content</Table>);
    expect(screen.getByText('Content')).toHaveClass('custom-table');
  });

  it('applies custom className to TableCell', () => {
    render(
      <table>
        <TableRow>
          <TableCell className="custom-cell">Cell</TableCell>
        </TableRow>
      </table>
    );
    expect(screen.getByText('Cell')).toHaveClass('custom-cell');
  });
});
