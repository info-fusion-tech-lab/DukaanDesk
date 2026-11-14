import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const tag = process.env.GITHUB_REF_NAME ?? "";
const version = tag.replace(/^v/, "");

if (!/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/.test(version)) {
  throw new Error(`Expected a semantic version tag, received "${tag}".`);
}

const packagePath = resolve(root, "desktop", "package.json");
const lockPath = resolve(root, "desktop", "package-lock.json");
const packageJson = JSON.parse(readFileSync(packagePath, "utf8"));
const packageLock = JSON.parse(readFileSync(lockPath, "utf8"));

packageJson.version = version;
packageLock.version = version;
if (packageLock.packages?.[""]) {
  packageLock.packages[""].version = version;
}

writeFileSync(packagePath, `${JSON.stringify(packageJson, null, 2)}\n`);
writeFileSync(lockPath, `${JSON.stringify(packageLock, null, 2)}\n`);
