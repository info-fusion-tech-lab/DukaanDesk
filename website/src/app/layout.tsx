import type { Metadata } from "next";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { siteName, siteUrl } from "@/lib/site";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  applicationName: siteName,
  title: {
    default: "DukaanDesk | Free Offline Shop Management Software",
    template: "%s | DukaanDesk",
  },
  description:
    "Free offline shop management software for small shops. Track inventory, customers, sales and reports on your computer with no cloud account.",
  keywords: [
    "DukaanDesk",
    "free offline shop management software",
    "inventory management for small shops",
    "retail sales tracker",
    "local shop management app",
  ],
  verification: {
    google: "Lv7vRuVweaHAf0XGFsruOn4nYA7z7d8SSC0QVVH8Ex4",
  },
  openGraph: {
    type: "website",
    siteName,
    title: "DukaanDesk | Free Offline Shop Management Software",
    description:
      "Manage inventory, customer ledgers, sales and reports with a free desktop app that stores records locally on your computer.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "WebSite",
              name: siteName,
              url: siteUrl,
            }),
          }}
        />
        <SiteHeader />
        <main>{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
