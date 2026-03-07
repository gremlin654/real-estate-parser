'use client';

import { RoomsFilter } from '@/shared/ui/rooms-filter';

interface FilterByRoomsProps {
  value: number[];
  other?: boolean;
  onChange: (rooms: number[], other?: boolean) => void;
}

export function FilterByRooms({ value, other, onChange }: FilterByRoomsProps) {
  return (
    <div className="w-[200px]">
      <RoomsFilter 
        selectedRooms={value} 
        selectedOther={other}
        onChange={onChange} 
      />
    </div>
  );
}
