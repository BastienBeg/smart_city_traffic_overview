import Sidebar from "./Sidebar";

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-[5%] min-w-[calc(100%-80px)] max-w-[calc(100%-60px)] min-h-screen">
        {children}
      </main>
    </div>
  );
}
