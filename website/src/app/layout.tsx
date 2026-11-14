import type { Metadata } from "next";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { siteName, siteUrl } from "@/lib/site";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  applicationName: siteName,
  title: {
    default: "Shop Management System | Simple tools for independent shops",
    template: "%s | Shop Management System",
  },
  description:
    "Manage products, customers, sales and reports in a straightforward desktop app. Your shop records stay on your computer.",
  openGraph: {
    type: "website",
    siteName,
    title: "Shop Management System | Simple tools for independent shops",
    description:
      "Manage products, customers, sales and reports in a straightforward desktop app. Your shop records stay on your computer.",
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
