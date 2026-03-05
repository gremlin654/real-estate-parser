'use client';

import { useQuery } from '@tanstack/react-query';
import { ScanProgressDisplay } from '@/entities/scan';
import type { ScanProgress } from '@/shared/types';

export function ViewProgress() {
  const { data: progress } = useQuery<ScanProgress>({
    queryKey: ['scanProgress'],
    queryFn: async () => {
      const response = await fetch('/api/v1/scan/progress');
      if (!response.ok) throw new Error('Failed to fetch progress');
      return response.json();
    },
    refetchInterval: 2000,
  });

  if (!progress || !progress.is_scanning) {
    return null;
  }

  return <ScanProgressDisplay progress={progress} />;
}
