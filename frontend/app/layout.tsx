// app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";
import "./phase17.css";


export const metadata: Metadata = {
  title: "FinAgent — AI Financial Research",
  description: "Production-grade AI financial research agent with real-time analysis, risk intelligence, and LLM-powered insights.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
