import { HashRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from '@/widgets/AppLayout';
import { Dashboard } from '@/pages/Dashboard';
import { Listings } from '@/pages/Listings';
import { ListingDetail } from '@/pages/ListingDetail';
import { Settings } from '@/pages/Settings';
import { Statistics } from '@/pages/Statistics';
import { PricePerM2AnalyticsPage } from '@/pages/PricePerM2AnalyticsPage';
import { DealsPage } from '@/pages/Deals';
import { PriceDropsPage } from '@/pages/PriceDrops';
import { FavoritesPage } from '@/pages/Favorites';
import TelegramWebApp from '@/pages/TelegramWebApp/ui/TelegramWebApp';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 минут
      retry: 1,
      refetchOnWindowFocus: false, // Не обновлять при фокусе окна
      refetchOnMount: false, // Не обновлять при монтировании если данные есть
    },
  },
});



function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <HashRouter>
        <Routes>
          <Route path="/" element={<AppLayout><Dashboard /></AppLayout>} />
          <Route path="/listings" element={<AppLayout><Listings /></AppLayout>} />
          <Route path="/listings/:id" element={<AppLayout><ListingDetail /></AppLayout>} />
          <Route path="/favorites" element={<AppLayout><FavoritesPage /></AppLayout>} />
          <Route path="/deals" element={<AppLayout><DealsPage /></AppLayout>} />
          <Route path="/price-drops" element={<AppLayout><PriceDropsPage /></AppLayout>} />
          <Route path="/statistics" element={<AppLayout><Statistics /></AppLayout>} />
          <Route path="/analytics/price-per-m2" element={<AppLayout><PricePerM2AnalyticsPage /></AppLayout>} />
          <Route path="/settings" element={<AppLayout><Settings /></AppLayout>} />
          <Route path="/telegram-webapp" element={<TelegramWebApp />} />
        </Routes>
      </HashRouter>
    </QueryClientProvider>
  );
}

export default App;
