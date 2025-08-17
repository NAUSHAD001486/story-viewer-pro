'use client';
import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import BackButton from '@/components/BackButton'; // <<< सुनिश्चित करें कि यह लाइन सही है
import { fetchInstagramData } from '@/services/api';

// ErrorDisplay और LoadingSpinner कंपोनेंट को इसी फाइल में रखें
function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center">
      <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-purple-500"></div>
      <p className="mt-4 text-lg text-gray-300">Fetching profile...</p>
    </div>
  );
}

function ErrorDisplay({ message, onRetry }) {
  const router = useRouter();
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center p-4">
       <BackButton /> {/* एरर पेज पर भी बैक बटन जोड़ें */}
      <p className="text-xl text-red-400">Oops! Something went wrong.</p>
      <p className="text-gray-400 mt-2">{message}</p>
      <button onClick={onRetry} className="mt-6 bg-purple-600 text-white font-bold rounded-full py-2 px-6 text-lg hover:opacity-90">
        Try Again
      </button>
    </div>
  );
}

// मुख्य कंटेंट कंपोनेंट
function ConfirmContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const username = searchParams.get('username');

  const [apiResponse, setApiResponse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    if (!username) {
        setError("No username provided.");
        setLoading(false);
        return;
    }
    setLoading(true);
    setError(null);
    const profileUrl = `https://www.instagram.com/${username}/`;
    
    try {
      const response = await fetchInstagramData(profileUrl);
      setApiResponse(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [username]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay message={error} onRetry={fetchData} />;
  if (!apiResponse || !apiResponse.data) return null;

  const profileData = apiResponse.data;

  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen p-6 pb-12 sm:pb-6">
      <BackButton />
      <main className="w-full max-w-md mx-auto text-center">
        <img src={profileData.avatar_url || '/profile-pic.jpg'} alt="Profile" className="w-28 h-28 rounded-full mx-auto border-4 border-purple-500 object-cover" />
        
        <div className="flex justify-center space-x-8 my-6">
          {Object.entries(profileData.stats).map(([key, value]) => (
            <div key={key}>
              <p className="font-bold text-xl">{value}</p>
              <p className="text-gray-400 text-sm capitalize">{key}</p>
            </div>
          ))}
        </div>

        <h2 className="text-2xl font-bold">{profileData.name}</h2>
        <p className="text-gray-400 text-md">@{profileData.username}</p>
        <p className="whitespace-pre-line text-gray-300 mt-2">{profileData.bio}</p>

        <div className="mt-8 space-y-4">
          <button onClick={() => router.push(`/user/${encodeURIComponent(username)}`)} className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-full py-3.5 text-xl transition-transform duration-200 ease-in-out hover:scale-105 active:scale-95">
            Confirm User
          </button>
          <button onClick={() => router.back()} className="text-red-400 hover:text-red-300 font-semibold text-lg">
            Change User
          </button>
        </div>
      </main>
    </div>
  );
}

// मुख्य पेज एक्सपोर्ट
export default function ConfirmPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <ConfirmContent />
    </Suspense>
  );
}