import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InfoCard, InfoRow, DateRow, TechRow } from '@/components/listing/ListingInfoCard';

describe('ListingInfoCard', () => {
  describe('InfoCard', () => {
    it('должен рендерить label и value', () => {
      render(<InfoCard label="Цена" value="100 000 BYN" />);

      expect(screen.getByText('Цена')).toBeInTheDocument();
      expect(screen.getByText('100 000 BYN')).toBeInTheDocument();
    });

    it('должен рендерить иконку если предоставлена', () => {
      render(<InfoCard label="Статус" value="Активно" icon="🟢" />);

      expect(screen.getByText('Статус')).toBeInTheDocument();
      expect(screen.getByText('🟢')).toBeInTheDocument();
      expect(screen.getByText('Активно')).toBeInTheDocument();
    });

    it('должен иметь правильные классы стилей', () => {
      const { container } = render(
        <InfoCard label="Площадь" value="50 м²" />
      );

      const card = container.firstChild;
      expect(card).toHaveClass('p-3', 'rounded-xl', 'bg-gradient-to-br');
    });
  });

  describe('InfoRow', () => {
    it('должен рендерить label и value', () => {
      render(<InfoRow label="Этаж" value="3 / 9" />);

      expect(screen.getByText('Этаж')).toBeInTheDocument();
      expect(screen.getByText('3 / 9')).toBeInTheDocument();
    });

    it('должен иметь правильные классы стилей', () => {
      const { container } = render(<InfoRow label="Комнаты" value="2" />);

      const row = container.firstChild;
      expect(row).toHaveClass('flex', 'justify-between', 'items-center', 'p-2');
    });

    it('должен иметь hover эффект', () => {
      const { container } = render(<InfoRow label="Площадь" value="50" />);

      const row = container.firstChild;
      expect(row).toHaveClass('hover:bg-muted/30');
    });
  });

  describe('DateRow', () => {
    it('должен рендерить label и дату', () => {
      render(<DateRow label="Дата создания" date="2024-01-15T10:00:00Z" />);

      expect(screen.getByText('Дата создания')).toBeInTheDocument();
      expect(screen.getByText('15 янв. 2024 г.')).toBeInTheDocument();
    });

    it('должен иметь красный цвет для удалённых', () => {
      const { container } = render(
        <DateRow label="Дата удаления" date="2024-01-20T10:00:00Z" isDeleted />
      );

      const row = container.firstChild;
      expect(row).toHaveClass('text-red-500');
    });

    it('должен форматировать дату в русском формате', () => {
      render(<DateRow label="Дата" date="2024-06-15T10:00:00Z" />);

      expect(screen.getByText('15 июн. 2024 г.')).toBeInTheDocument();
    });

    it('должен иметь стили для значения', () => {
      const { container } = render(
        <DateRow label="Дата" date="2024-01-15T10:00:00Z" />
      );

      const valueSpan = container.querySelector('span:last-child');
      expect(valueSpan).toHaveClass('bg-primary/10', 'px-3', 'py-1', 'rounded-full');
    });
  });

  describe('TechRow', () => {
    it('должен рендерить label и value', () => {
      render(<TechRow label="ID" value="12345" />);

      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('12345')).toBeInTheDocument();
    });

    it('должен иметь моноширинный шрифт для значения', () => {
      const { container } = render(<TechRow label="Kufar ID" value="k123" />);

      const valueSpan = container.querySelector('span:last-child');
      expect(valueSpan).toHaveClass('font-mono');
    });

    it('должен обрезать длинный текст', () => {
      const { container } = render(
        <TechRow label="URL" value="https://re.kufar.by/very-long-url" />
      );

      const valueSpan = container.querySelector('span:last-child');
      expect(valueSpan).toHaveClass('max-w-[200px]', 'truncate');
    });

    it('должен выравнивать значение по правому краю', () => {
      const { container } = render(<TechRow label="Hash" value="abc123" />);

      const valueSpan = container.querySelector('span:last-child');
      expect(valueSpan).toHaveClass('text-right');
    });
  });
});
