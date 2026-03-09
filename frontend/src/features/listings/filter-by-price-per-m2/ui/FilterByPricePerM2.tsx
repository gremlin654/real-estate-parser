'use client';

import { Input } from '@/shared/ui/input';
import { Button } from '@/shared/ui/button';
import { useState, useEffect } from 'react';

interface FilterByPricePerM2Props {
  pricePerM2Min?: number | null;
  pricePerM2Max?: number | null;
  onChange: (min: number | null, max: number | null) => void;
}

export function FilterByPricePerM2({ pricePerM2Min, pricePerM2Max, onChange }: FilterByPricePerM2Props) {
  const [localMin, setLocalMin] = useState(pricePerM2Min?.toString() || '');
  const [localMax, setLocalMax] = useState(pricePerM2Max?.toString() || '');

  // Синхронизация локального state с props
  useEffect(() => {
    setLocalMin(pricePerM2Min?.toString() || '');
  }, [pricePerM2Min]);

  useEffect(() => {
    setLocalMax(pricePerM2Max?.toString() || '');
  }, [pricePerM2Max]);

  const handleApply = () => {
    onChange(
      localMin ? parseFloat(localMin) : null,
      localMax ? parseFloat(localMax) : null
    );
  };

  const handleClear = () => {
    setLocalMin('');
    setLocalMax('');
    onChange(null, null);
  };

  return (
    <div className="flex items-center gap-2">
      <Input
        type="number"
        placeholder="От"
        className="w-[100px]"
        value={localMin}
        onChange={(e) => setLocalMin(e.target.value)}
        step="100"
      />
      <Input
        type="number"
        placeholder="До"
        className="w-[100px]"
        value={localMax}
        onChange={(e) => setLocalMax(e.target.value)}
        step="100"
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
