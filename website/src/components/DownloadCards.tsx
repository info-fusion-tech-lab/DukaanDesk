"use client";

import { useEffect, useState } from "react";

type Platform = "windows" | "macos" | "linux";

const releasesUrl =
  "https://github.com/info-fusion-tech-lab/DukaanDesk/releases/latest";
const releaseApiUrl =
  "https://api.github.com/repos/info-fusion-tech-lab/DukaanDesk/releases/latest";

const platforms: Array<{
  id: Platform;
  name: string;
  packageName: string;
  details: string;
  icon: string;
}> = [
  {
    id: "windows",
    name: "Windows",
    packageName: "Windows installer (.exe)",
    details: "Windows 10 or later · 64-bit",
    icon: "⊞",
  },
  {
    id: "macos",
    name: "macOS",
    packageName: "macOS disk image (.dmg)",
    details: "Apple Silicon (ARM64) only",
    icon: "⌘",
  },
  {
    id: "linux",
    name: "Linux",
    packageName: "Linux AppImage",
    details: "64-bit · AppImage format",
    icon: "◆",
  },
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function matchesPlatformAsset(name: string, platform: Platform): boolean {
  const lowerCaseName = name.toLowerCase();
  if (platform === "windows") {
    return lowerCaseName.endsWith(".exe");
  }
  if (platform === "macos") {
    return lowerCaseName.endsWith(".dmg");
  }
  return lowerCaseName.endsWith(".appimage");
}

function isDukaanDeskReleaseAsset(value: unknown): value is string {
  if (typeof value !== "string") {
    return false;
  }

  try {
    const url = new URL(value);
    return url.protocol === "https:"
      && url.hostname === "github.com"
      && !url.username
      && !url.password
      && url.pathname.toLowerCase().startsWith(
        "/info-fusion-tech-lab/dukaandesk/releases/download/",
      );
  } catch {
    return false;
  }
}

export function DownloadCards() {
  const [downloads, setDownloads] = useState<Partial<Record<Platform, string>>>(
    {},
  );
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadLatestRelease(): Promise<void> {
      try {
        const response = await fetch(releaseApiUrl, {
          headers: { Accept: "application/vnd.github+json" },
          cache: "no-store",
        });
        if (!response.ok) {
          throw new Error(`GitHub returned HTTP ${response.status}.`);
        }

        const release: unknown = await response.json();
        if (!isRecord(release) || !Array.isArray(release.assets)) {
          throw new Error("The latest release response has no asset list.");
        }

        const assets = release.assets.filter(isRecord);
        const nextDownloads: Partial<Record<Platform, string>> = {};
        for (const platform of platforms) {
          const asset = assets.find((candidate) => {
            return typeof candidate.name === "string"
              && matchesPlatformAsset(candidate.name, platform.id);
          });
          if (asset && isDukaanDeskReleaseAsset(asset.browser_download_url)) {
            nextDownloads[platform.id] = asset.browser_download_url;
          }
        }

        if (active) {
          setDownloads(nextDownloads);
        }
      } catch {
        if (active) {
          setLoadFailed(true);
        }
      }
    }

    void loadLatestRelease();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="download-grid">
      {platforms.map((platform) => {
        const downloadUrl = downloads[platform.id];
        return (
          <article className="card download-card" key={platform.id}>
            <div className="card-icon" aria-hidden="true">{platform.icon}</div>
            <h3>{platform.name}</h3>
            <p>{platform.packageName}</p>
            <p>{platform.details}</p>
            <a className="button" href={downloadUrl || releasesUrl} rel="noreferrer">
              {downloadUrl ? "Download latest installer" : "Open GitHub releases"}
              <span aria-hidden="true"> ↗</span>
            </a>
            <p className="download-status" aria-live="polite">
              {downloadUrl
                ? "Direct download for the latest release."
                : loadFailed
                  ? "Could not retrieve the direct download. You can still choose a file on GitHub."
                  : "If no direct installer is available, choose a file from GitHub Releases."}
            </p>
          </article>
        );
      })}
    </div>
  );
}
