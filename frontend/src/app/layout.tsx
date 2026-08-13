import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import APIStatusBanner from "@/components/APIStatusBanner";
import KeepAlive from "@/components/KeepAlive";

export const metadata: Metadata = {
  title: "YouTube Global Intelligence Platform",
  description: "Real-time YouTube trend analytics, virality scoring, and ranking intelligence across 8 countries.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" data-theme="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Sidebar />
        <main
          className="transition-all duration-300 min-h-screen"
          style={{ marginLeft: 240, padding: "24px 32px" }}
        >
          <APIStatusBanner />
          <KeepAlive />
          {children}
        </main>
      </body>
    </html>
  );
}
