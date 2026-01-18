import Sidebar from "./Sidebar";

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      {/* Main content offset: matches Sidebar width (5%, min 60px, max 80px) */}
      <main 
        className="min-h-screen"
        style={{ marginLeft: 'clamp(60px, 5%, 80px)' }}
      >
        {children}
      </main>
    </div>
  );
}

