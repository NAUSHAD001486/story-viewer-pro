'use client';
import { RectangleStackIcon, PlayCircleIcon, PlusCircleIcon, PhotoIcon } from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import BackButton from '@/components/BackButton'; // <<< नया इम्पोर्ट

const ActionButton = ({ icon: Icon, text, onClick }) => (
  <div onClick={onClick} className="bg-gray-800/70 rounded-2xl p-4 flex flex-col items-start justify-between h-32 cursor-pointer hover:bg-gray-700/60 transition-colors">
    <Icon className="w-9 h-9 text-gray-300" />
    <span className="font-semibold text-left text-lg">{text}</span>
  </div>
);

export default function UserDashboard({ params }) {
  const router = useRouter();
  const username = params.username;
  const user = { name: 'Naushad alam', username: `@${username}`, avatar: '/profile-pic.jpg', stats: { posts: 166, followers: 977, following: 97 } };

  return (
    // === यहाँ बदलाव किया गया है ===
    <div className="relative min-h-screen p-4">
      <BackButton /> {/* <<< बैक बटन यहाँ जोड़ा गया */}
      <main className="w-full max-w-md mx-auto">
        <div className="flex items-center justify-between mb-6 pt-12"> {/* pt-12 बैक बटन के लिए जगह बनाने के लिए */}
          <h1 className="text-2xl font-bold text-white">
            Story Viewer Pro
          </h1>
          <div className="flex items-center space-x-2 bg-yellow-400/20 text-yellow-300 px-3 py-1 rounded-full">
            <span className="font-bold text-sm">PRO</span>
            <span className="text-yellow-400">👑</span>
          </div>
        </div>
        <div className="flex items-center space-x-4 mb-4">
          <img src={user.avatar} alt="Profile" className="w-24 h-24 rounded-full border-4 border-pink-500 object-cover" />
          <div className="flex justify-around flex-grow text-center">
            {Object.entries(user.stats).map(([key, value]) => (
              <div key={key}>
                <p className="font-bold text-xl">{value}</p>
                <p className="text-gray-400 text-sm capitalize">{key}</p>
              </div>
            ))}
          </div>
        </div>
        <h2 className="text-xl font-bold">{user.name}</h2>
        <p className="text-gray-400 text-md">{user.username}</p>
        <div className="grid grid-cols-2 gap-4 my-8">
          <ActionButton icon={PlayCircleIcon} text="Show Stories" />
          <ActionButton icon={RectangleStackIcon} text="Show Post" onClick={() => router.push(`/user/${username}/posts`)} />
          <ActionButton icon={PlusCircleIcon} text="See Highlights" />
          <ActionButton icon={PhotoIcon} text="Show Profile Photo" />
        </div>
        <button onClick={() => router.push('/')} className="w-full bg-gray-800/70 rounded-xl py-4 font-semibold hover:bg-gray-700/80 transition-colors text-lg">
          Change User
        </button>
        <p className="text-center text-gray-500 text-sm mt-4">
          Last Update: {new Date().toLocaleTimeString()} - {new Date().toLocaleDateString('en-GB')}
        </p>
      </main>
    </div>
  );
}