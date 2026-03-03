import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '@/components/ui/accordion';

describe('Accordion', () => {
  it('renders Accordion component', () => {
    render(
      <Accordion type="single">
        <AccordionItem value="item1">
          <AccordionTrigger>Trigger 1</AccordionTrigger>
          <AccordionContent>Content 1</AccordionContent>
        </AccordionItem>
      </Accordion>
    );

    expect(screen.getByText('Trigger 1')).toBeInTheDocument();
  });

  it('renders AccordionItem', () => {
    render(
      <Accordion type="single">
        <AccordionItem value="item1">Item Content</AccordionItem>
      </Accordion>
    );

    expect(screen.getByText('Item Content')).toBeInTheDocument();
  });

  it('renders AccordionTrigger', () => {
    render(
      <Accordion type="single">
        <AccordionItem value="item1">
          <AccordionTrigger>Click to expand</AccordionTrigger>
          <AccordionContent>Hidden content</AccordionContent>
        </AccordionItem>
      </Accordion>
    );

    expect(screen.getByText('Click to expand')).toBeInTheDocument();
  });

  it('renders AccordionContent', () => {
    render(
      <Accordion type="single" defaultValue="item1">
        <AccordionItem value="item1">
          <AccordionTrigger>Trigger</AccordionTrigger>
          <AccordionContent>Visible content</AccordionContent>
        </AccordionItem>
      </Accordion>
    );

    expect(screen.getByText('Visible content')).toBeInTheDocument();
  });

  it('renders with multiple items', () => {
    render(
      <Accordion type="single">
        <AccordionItem value="item1">
          <AccordionTrigger>First</AccordionTrigger>
          <AccordionContent>First content</AccordionContent>
        </AccordionItem>
        <AccordionItem value="item2">
          <AccordionTrigger>Second</AccordionTrigger>
          <AccordionContent>Second content</AccordionContent>
        </AccordionItem>
      </Accordion>
    );

    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
  });

  it('renders with type multiple', () => {
    render(
      <Accordion type="multiple">
        <AccordionItem value="item1">
          <AccordionTrigger>Trigger</AccordionTrigger>
          <AccordionContent>Content</AccordionContent>
        </AccordionItem>
      </Accordion>
    );

    expect(screen.getByText('Trigger')).toBeInTheDocument();
  });

  it('applies custom className to Accordion', () => {
    render(
      <Accordion type="single" className="custom-accordion">
        <AccordionItem value="item1">
          <AccordionTrigger>Trigger</AccordionTrigger>
        </AccordionItem>
      </Accordion>
    );

    expect(screen.getByText('Trigger')).toBeInTheDocument();
  });

  it('applies custom className to AccordionItem', () => {
    render(
      <Accordion type="single">
        <AccordionItem value="item1" className="custom-item">
          <AccordionTrigger>Trigger</AccordionTrigger>
        </AccordionItem>
      </Accordion>
    );

    expect(screen.getByText('Trigger')).toBeInTheDocument();
  });
});
