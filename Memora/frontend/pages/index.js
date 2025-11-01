import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function HomePage() {
    const router = useRouter();
    
    useEffect(() => {
        router.push('/chat');
    }, [router]);
    
    return (
        <div className="flex justify-center items-center h-screen bg-gray-50">
            <div className="text-center">
                <h1 className="text-2xl font-bold mb-4">� Loading Memora...</h1>
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            </div>
        </div>
    );
}