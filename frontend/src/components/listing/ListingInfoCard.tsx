interface InfoCardProps {
  label: string;
  value: string;
  icon?: string;
}

export function InfoCard({ label, value, icon }: InfoCardProps) {
  return (
    <div className="p-3 rounded-xl bg-gradient-to-br from-muted/50 to-muted/30 border shadow-sm">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-lg font-bold flex items-center gap-1">
        {icon && <span>{icon}</span>}
        {value}
      </p>
    </div>
  );
}

interface InfoRowProps {
  label: string;
  value: string;
}

export function InfoRow({ label, value }: InfoRowProps) {
  return (
    <div className="flex justify-between items-center p-2 rounded-lg hover:bg-muted/30 transition-colors">
      <span className="text-muted-foreground text-sm">{label}</span>
      <span className="font-medium text-sm text-right">{value}</span>
    </div>
  );
}

interface DateRowProps {
  label: string;
  date: string;
  isDeleted?: boolean;
}

export function DateRow({ label, date, isDeleted }: DateRowProps) {
  return (
    <div className={`flex justify-between items-center ${isDeleted ? 'text-red-500' : ''}`}>
      <span className="text-muted-foreground text-sm">{label}</span>
      <span className="font-medium text-sm bg-primary/10 px-3 py-1 rounded-full">
        {new Date(date).toLocaleDateString("ru-RU", {
          year: "numeric",
          month: "short",
          day: "numeric",
        })}
      </span>
    </div>
  );
}

interface TechRowProps {
  label: string;
  value: string;
}

export function TechRow({ label, value }: TechRowProps) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-muted-foreground text-xs">{label}</span>
      <span className="font-mono text-xs bg-muted px-2 py-1 rounded max-w-[200px] truncate text-right">
        {value}
      </span>
    </div>
  );
}
