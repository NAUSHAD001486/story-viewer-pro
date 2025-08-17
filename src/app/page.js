'use client';
import { AtSymbolIcon, ShieldCheckIcon } from '@heroicons/react/24/solid';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();

  const handleSubmit = (e) => {
    e.preventDefault();
    const username = e.target.username.value.trim().replace('@', '');
    if (username) {
      router.push(`/confirm?username=${encodeURIComponent(username)}`);
    }
  };

  return (
    // लेआउट को स्क्रीन के निचले हिस्से में रखा गया है
    <div className="flex flex-col items-center justify-end min-h-screen p-6 pb-20 sm:justify-center sm:pb-6">
      <main className="w-full max-w-md mx-auto text-center">
        
        {/* === नाम और कंटेंट वही है, लेकिन फॉर्मेट नया है === */}
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight bg-gradient-to-r from-fuchsia-500 to-purple-500 bg-clip-text text-transparent">
          Story Viewer Pro
        </h1>
        <p className="text-gray-300 mt-3 mb-12 text-lg tracking-wide">
          Anonymous Instagram Story Viewer
        </p>

        <form className="space-y-5" onSubmit={handleSubmit}>
          {/* === इनपुट बॉक्स का साइज़ और स्टाइल अपडेट किया गया === */}
          <div className="relative">
            <input
              name="username"
              type="text"
              placeholder="@ Instagram username"
              className="w-full bg-[#3b3b58]/50 backdrop-blur-sm rounded-full py-3.5 px-5 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 text-left text-lg"
              required
            />
          </div>
          
          {/* === बटन का साइज़ और ग्रेडिएंट अपडेट किया गया === */}
          <button
            type="submit"
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-full py-3.5 text-xl 
                       transition-transform duration-200 ease-in-out 
                       hover:scale-105 active:scale-95"
          >
            Select User
          </button>
        </form>
        <div className="flex items-center justify-center mt-5 text-gray-400">
          <ShieldCheckIcon className="w-5 h-5 mr-2 text-green-400" />
          <span>We do not collect any of your data.</span>
        </div>
      </main>
    </div>
  );
}