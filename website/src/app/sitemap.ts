import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/site";

export const dynamic = "force-static";

const pages = [
  ["", 1],
  ["product/", 0.8],
  ["features/", 0.8],
  ["how-to-use/", 0.8],
  ["about/", 0.7],
  ["download/", 0.7],
] as const;

export default function sitemap(): MetadataRoute.Sitemap {
  return pages.map(([path, priority]) => ({
    url: `${siteUrl}/${path}`,
    changeFrequency: "monthly",
    priority,
  }));
}
