import type { Metadata } from "next";
import Link from "next/link";
import { DownloadCards } from "@/components/DownloadCards";

export const metadata: Metadata = {
  title: "Download DukaanDesk for Windows, macOS and Linux",
  description:
    "Download free offline shop management software for Windows, Apple Silicon macOS or Linux x64. Get the latest DukaanDesk installer directly.",
};

export default function DownloadPage() {
  return (
    <>
      <section className="page-hero">
        <div className="page-hero-inner">
          <p className="eyebrow">Downloads</p>
          <h1>Choose a release for your computer.</h1>
          <p className="lead">
            Choose your operating system to download the latest installer directly.
            DukaanDesk stores its shop records on your computer and works offline.
          </p>
        </div>
      </section>
      <section className="section content-section">
        <DownloadCards />
      </section>
      <section className="section">
        <div className="notice">
          If no release is listed yet, the installers have not been published.
          Read the <Link href="/how-to-use/">quick-start guide</Link> before installing.
        </div>
      </section>
    </>
  );
}
