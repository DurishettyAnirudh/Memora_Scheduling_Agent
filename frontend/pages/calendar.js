import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import dynamic from 'next/dynamic';

// Dynamic import with no SSR to prevent hydration issues
const CalendarView = dynamic(() => import('../components/CalendarView'), {
    ssr: false,
    loading: () => (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-center items-center h-96">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-lg">Loading calendar...</p>
                    <p className="text-sm text-gray-500 mt-2">Setting up your schedule view</p>
                </div>
            </div>
        </div>
    )
});

export default function CalendarPage() {
    const router = useRouter();
    const [pageKey, setPageKey] = useState(0);

    // Force re-render when page is accessed or navigated to
    useEffect(() => {
        const handleRouteChange = (url) => {
            if (url === '/calendar') {
                setPageKey(Date.now());
            }
        };

        setPageKey(Date.now()); // Initial render
        router.events.on('routeChangeComplete', handleRouteChange);
        
        return () => {
            router.events.off('routeChangeComplete', handleRouteChange);
        };
    }, [router]);

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col" key={pageKey}>
            <nav className="bg-white shadow-sm border-b p-4 fixed top-0 left-0 right-0 z-50">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                        <h1 className="text-xl font-semibold">Memora - AI Scheduling Assistant</h1>
                    </div>
                    <div className="space-x-4">
                        <Link href="/chat" className="text-gray-600 hover:text-blue-600 transition-colors pb-1">
                            💬 Chat
                        </Link>
                        <Link href="/calendar" className="text-blue-600 font-medium border-b-2 border-blue-600 pb-1">
                            📅 Calendar
                        </Link>
                        <Link href="/documents" className="text-gray-600 hover:text-blue-600 transition-colors pb-1">
                            📚 Documents
                        </Link>
                    </div>
                </div>
            </nav>
            <div className="flex-1 pt-20">
                <CalendarView />
            </div>
        </div>
    );
}
