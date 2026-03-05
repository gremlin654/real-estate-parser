import { Progress } from '@/shared/ui/progress';
import { Badge } from '@/shared/ui/badge';
import type { ScanProgress } from '@/shared/types';
import { getScanStageLabel, getScanStageProgress, isScanComplete } from '../model';

interface ScanProgressDisplayProps {
  progress: ScanProgress;
}

export function ScanProgressDisplay({ progress }: ScanProgressDisplayProps) {
  const stageLabel = getScanStageLabel(progress.stage);
  const value = getScanStageProgress(progress.stage, progress);
  const isComplete = isScanComplete(progress);

  return (
    <div className="w-full space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{stageLabel}</span>
        {!isComplete && progress.is_stable && (
          <Badge variant="secondary" className="animate-pulse">
            ● Обновляется
          </Badge>
        )}
      </div>
      <Progress value={value} className="h-2" />
      <div className="text-xs text-muted-foreground">
        Страниц: {progress.pages_scraped} • Объявлений: {progress.listings_fetched} •{' '}
        {progress.elapsed_seconds}с
      </div>
    </div>
  );
}
