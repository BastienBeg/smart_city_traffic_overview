import type { Metadata } from "next";
import { Inter, Orbitron } from "next/font/google";
import { MainLayout } from "@/components/layout";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import QueryProvider from "@/components/providers/QueryProvider";
import "leaflet/dist/leaflet.css";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

const orbitron = Orbitron({
  variable: "--font-orbitron",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
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
      <body className={`${inter.variable} ${orbitron.variable} antialiased font-sans`}>
        <QueryProvider>
            <WebSocketProvider>
            <MainLayout>{children}</MainLayout>
            </WebSocketProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
