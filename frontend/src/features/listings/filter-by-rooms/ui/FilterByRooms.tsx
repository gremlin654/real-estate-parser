'use client';

import { RoomsFilter } from '@/shared/ui/rooms-filter';

interface FilterByRoomsProps {
  value: number[];
  onChange: (rooms: number[]) => void;
}

export function FilterByRooms({ value, onChange }: FilterByRoomsProps) {
  return (
    <div className="w-[200px]">
      <RoomsFilter selectedRooms={value} onChange={onChange} />
    </div>
  );
}
