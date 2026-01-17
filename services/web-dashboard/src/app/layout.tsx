import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { MainLayout } from "@/components/layout";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "Smart City Sentinel - Mission Control",
  description: "Real-time traffic monitoring and anomaly detection dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} antialiased`}>
        <WebSocketProvider>
          <MainLayout>{children}</MainLayout>
        </WebSocketProvider>
      </body>
    </html>
  );
}
