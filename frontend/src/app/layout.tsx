import type { Metadata } from "next";
import "./globals.css";
import { Navigation } from "@/components/Navigation";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Mishmash - Collaborative Data Analysis",
  description:
    "Upload, analyze, and share datasets. Reproduce findings, combine data, and publish results.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <Navigation />
          <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
