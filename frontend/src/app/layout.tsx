import type { Metadata, Viewport } from "next";
import { DM_Sans, Sora } from "next/font/google";
import { AppProviders } from "@/components/AppProviders";
import { Nav } from "@/components/Nav";
import "./globals.css";

const display = Sora({
  subsets: ["latin"],
  variable: "--font-display",
});

const body = DM_Sans({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "BETPREDICT AI — Pronostics sportifs intelligents",
  description:
    "Analyses statistiques et probabilités calibrées pour le football. Service d'information — aucune mise acceptée.",
  manifest: "/manifest.webmanifest",
  applicationName: "BETPREDICT AI",
};

export const viewport: Viewport = {
  themeColor: "#0b1f3a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className={`${display.variable} ${body.variable} antialiased`}>
        <AppProviders>
          <Nav />
          <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-7xl px-4 py-6">{children}</main>
          <footer className="border-t border-[var(--line)] px-4 py-8 text-center text-xs text-muted">
            BETPREDICT AI — analyses statistiques estimées. Aucune certitude. Aucune mise acceptée.
            Respectez la législation locale et le jeu responsable (+18).
          </footer>
        </AppProviders>
      </body>
    </html>
  );
}
