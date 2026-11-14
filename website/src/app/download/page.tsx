import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Download",
  description: "Download the Shop Management System desktop application.",
};

const releasesUrl = process.env.NEXT_PUBLIC_RELEASES_URL
  || "https://github.com/info-fusion-tech-lab/ShopManagementSystem/releases/latest";

const platforms = [
  ["Windows", "Windows installer (.exe)", "Windows 10 or later · 64-bit"],
  ["macOS", "macOS disk image (.dmg)", "Check the release notes for architecture; unsigned builds may require approval in macOS settings."],
  ["Linux", "AppImage or .deb package", "Choose the format supported by your distribution."],
];

export default function DownloadPage() {
  return (
    <>
      <section className="page-hero">
        <div className="page-hero-inner">
          <p className="eyebrow">Downloads</p>
          <h1>Choose a release for your computer.</h1>
          <p className="lead">
            Install the desktop app and keep your shop records on your own device.
            Releases are published on GitHub.
          </p>
        </div>
      </section>
      <section className="section content-section">
        <div className="download-grid">
          {platforms.map(([name, packageName, details]) => (
            <article className="card download-card" key={name}>
              <div className="card-icon" aria-hidden="true">{name === "Windows" ? "⊞" : name === "macOS" ? "⌘" : "◆"}</div>
              <h3>{name}</h3>
              <p>{packageName}</p>
              <p>{details}</p>
              <a className="button" href={releasesUrl} rel="noreferrer" target="_blank">
                View latest release <span aria-hidden="true">↗</span>
              </a>
            </article>
          ))}
        </div>
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
