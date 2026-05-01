import type { Metadata } from "next";
import Sidebar from "@/components/layout/Sidebar";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "NHL Stanley Cup Predictions",
  description: "ML-powered Stanley Cup prediction engine",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-bg text-text min-h-screen">
        <Sidebar />
        <main className="ml-64 p-8 min-h-screen">{children}</main>
      </body>
    </html>
  );
}
