import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from '@/widgets/AppLayout';
import { Dashboard } from '@/pages/Dashboard';
import { Listings } from '@/pages/Listings';
import { ListingDetail } from '@/pages/ListingDetail';
import { Settings } from '@/pages/Settings';
import { Statistics } from '@/pages/Statistics';

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

// Компонент для установки заголовка страницы
function PageTitle({ title }: { title: string }) {
  useEffect(() => {
    document.title = `${title} | Kufar Monitor`;
  }, [title]);
  return null;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <PageTitle title="Панель управления" />
        <AppLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/listings" element={<Listings />} />
            <Route path="/listings/:id" element={<ListingDetail />} />
            <Route path="/statistics" element={<Statistics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </AppLayout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
