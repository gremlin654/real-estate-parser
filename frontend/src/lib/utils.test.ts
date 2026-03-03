import { describe, it, expect } from 'vitest';
import { cn } from './utils';
import { formatDateMinsk, formatDateTime } from './utils';

describe('utils', () => {
  describe('cn', () => {
    it('merges class names correctly', () => {
      expect(cn('foo', 'bar')).toBe('foo bar');
    });

    it('handles falsy values', () => {
      expect(cn('foo', false, null, undefined, 'bar')).toBe('foo bar');
    });

    it('handles arrays', () => {
      expect(cn(['foo', 'bar'])).toBe('foo bar');
    });

    it('handles objects', () => {
      expect(cn({ foo: true, bar: false, baz: true })).toBe('foo baz');
    });

    it('handles nested arrays and objects', () => {
      expect(cn('foo', ['bar', { baz: true }])).toBe('foo bar baz');
    });

    it('handles tailwind class merging', () => {
      expect(cn('p-4', 'p-2')).toBe('p-2');
    });

    it('handles complex tailwind classes', () => {
      expect(cn('text-red-500 bg-blue-100', 'text-blue-500')).toBe('bg-blue-100 text-blue-500');
    });

    it('returns empty string for no input', () => {
      expect(cn()).toBe('');
    });

    it('handles single class', () => {
      expect(cn('single')).toBe('single');
    });
  });

  describe('formatDateMinsk', () => {
    it('formats date to Russian locale with Minsk timezone', () => {
      const result = formatDateMinsk('2026-03-01T10:00:00Z');
      expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}:\d{2}/);
    });

    it('handles different dates', () => {
      const result = formatDateMinsk('2025-12-25T15:30:45Z');
      expect(result).toContain('2025');
    });

    it('handles invalid date', () => {
      const result = formatDateMinsk('invalid');
      expect(result).toBe('Invalid Date');
    });
  });

  describe('formatDateTime', () => {
    it('formats date to compact Russian format', () => {
      const result = formatDateTime('2026-03-01T10:00:00Z');
      expect(result).toMatch(/\d{2}\.\d{2}\.\d{2}, \d{2}:\d{2}/);
    });

    it('handles different dates', () => {
      const result = formatDateTime('2025-06-15T08:30:00Z');
      expect(result).toContain('25');
    });

    it('handles invalid date', () => {
      const result = formatDateTime('invalid');
      expect(result).toBe('Invalid Date');
    });
  });
});
