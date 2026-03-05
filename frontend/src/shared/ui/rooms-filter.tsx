import * as React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/shared/ui/popover';
import { Button } from '@/shared/ui/button';
import { Separator } from '@/shared/ui/separator';

export interface RoomsFilterOption {
  value: string;
  label: string;
  type: 'room' | 'other';
}

export interface RoomsFilterProps {
  selectedRooms: number[];
  selectedOther?: boolean;
  onChange: (rooms: number[]) => void;
}

const ROOM_OPTIONS: RoomsFilterOption[] = [
  { value: '1', label: '1 комната', type: 'room' },
  { value: '2', label: '2 комнаты', type: 'room' },
  { value: '3', label: '3 комнаты', type: 'room' },
  { value: '4', label: '4 комнаты', type: 'room' },
];

export function RoomsFilter({
  selectedRooms,
  selectedOther,
  onChange,
}: RoomsFilterProps) {
  const [open, setOpen] = React.useState(false);

  const toggleRoom = (room: number) => {
    if (selectedRooms.includes(room)) {
      onChange(selectedRooms.filter((r) => r !== room));
    } else {
      onChange([...selectedRooms, room]);
    }
  };

  const clearAll = () => {
    onChange([]);
  };

  const hasSelection = selectedRooms.length > 0 || selectedOther;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-[180px] h-9 shadow-sm bg-card border justify-between"
        >
          <span className="truncate">
            {hasSelection
              ? `${selectedRooms.length}${selectedOther ? '+' : ''} комн.`
              : 'Комнаты'}
          </span>
          {hasSelection && (
            <span className="ml-1 text-xs text-muted-foreground">
              ({selectedRooms.length}{selectedOther ? '+' : ''})
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0" align="start">
        <div className="p-2">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Комнаты</span>
            {hasSelection && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAll}
                className="h-6 text-xs hover:text-red-500"
              >
                Сброс
              </Button>
            )}
          </div>
          <div className="space-y-1">
            {ROOM_OPTIONS.map((option) => {
              const room = parseInt(option.value, 10);
              const isSelected = selectedRooms.includes(room);

              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => toggleRoom(room)}
                  className={cn(
                    'w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm hover:bg-accent transition-colors',
                    isSelected && 'bg-accent/50'
                  )}
                >
                  <div
                    className={cn(
                      'h-4 w-4 rounded border flex items-center justify-center',
                      isSelected
                        ? 'bg-primary border-primary'
                        : 'border-input'
                    )}
                  >
                    {isSelected && (
                      <Check className="h-3 w-3 text-primary-foreground" />
                    )}
                  </div>
                  <span>{option.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
