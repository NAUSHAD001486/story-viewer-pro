import './globals.css';

export const metadata = {
  title: 'Story Viewer Pro',
  description: 'View and download Instagram content anonymously.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        {/* === यहाँ बदलाव किया गया है === */}
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#1a1a1a" />
        <link rel="apple-touch-icon" href="/logo-192x192.png" />
      </head>
      <body className="main-bg">
        {children}
      </body>
    </html>
  );
}