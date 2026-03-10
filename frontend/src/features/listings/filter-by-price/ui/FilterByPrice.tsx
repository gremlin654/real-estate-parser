'use client';

import { Input } from '@/shared/ui/input';
import { Button } from '@/shared/ui/button';
import { useState, useEffect } from 'react';

interface FilterByPriceProps {
  priceFrom?: number | null;
  priceTo?: number | null;
  onChange: (priceFrom: number | null, priceTo: number | null) => void;
}

export function FilterByPrice({ priceFrom, priceTo, onChange }: FilterByPriceProps) {
  const [localFrom, setLocalFrom] = useState(priceFrom?.toString() || '');
  const [localTo, setLocalTo] = useState(priceTo?.toString() || '');

  // Синхронизация локального state с props
  useEffect(() => {
    setLocalFrom(priceFrom?.toString() || '');
  }, [priceFrom]);

  useEffect(() => {
    setLocalTo(priceTo?.toString() || '');
  }, [priceTo]);

  const handleApply = () => {
    onChange(
      localFrom ? parseInt(localFrom, 10) : null,
      localTo ? parseInt(localTo, 10) : null
    );
  };

  const handleClear = () => {
    setLocalFrom('');
    setLocalTo('');
    onChange(null, null);
  };

  return (
    <div className="flex items-center gap-2">
      <Input
        type="number"
        placeholder="От"
        className="w-[100px]"
        value={localFrom}
        onChange={(e) => setLocalFrom(e.target.value)}
        data-testid="price-min-input"
      />
      <Input
        type="number"
        placeholder="До"
        className="w-[100px]"
        value={localTo}
        onChange={(e) => setLocalTo(e.target.value)}
        data-testid="price-max-input"
      />
      <Button size="sm" onClick={handleApply}>
        Применить
      </Button>
      <Button size="sm" variant="ghost" onClick={handleClear}>
        Сброс
      </Button>
    </div>
  );
}
