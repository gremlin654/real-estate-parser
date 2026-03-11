'use client';

import { DealFilterToggle } from '@/components/filters/DealFilterToggle';
import { useFilterStore } from '@/store/filterStore';

interface FilterByDealProps {
  className?: string;
}

export function FilterByDeal({ className }: FilterByDealProps) {
  const { dealsOnly, discountPercent, setDealsOnly } = useFilterStore();

  const handleToggle = (enabled: boolean) => {
    setDealsOnly(enabled);
  };

  return (
    <DealFilterToggle
      enabled={dealsOnly}
      onToggle={handleToggle}
      discountThreshold={discountPercent}
      className={className}
    />
  );
}
