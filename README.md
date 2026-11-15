# DukaanDesk

DukaanDesk is a free desktop shop-management app for independent retailers. It
helps track products and stock, customer balances, sales and reports. The
desktop application works offline and stores shop records locally on the
computer where it is installed. It does not require a cloud account.

The public product website is a separate Next.js site. It contains product
information, setup guidance and links to the desktop installers; it does not
receive shop records.

## Features

- Inventory management with per-item cost prices, cost-based stock valuation and low-stock indicators
- Customer accounts, balances and transaction histories
- Supplier purchase/payment ledgers and staff attendance/payroll
- Multi-item sales with cash, online, credit and split payment options
- Dashboard summaries, cost-of-goods-sold profit, finance view and sales reports
- Account-scoped JSON data import/export and appearance settings
- Local accounts with optional passwords and separate shop-data profiles
- Password-verified account deletion, with export and extra confirmations for passwordless accounts
- Encrypted local records, protected by the operating system's secure storage
- Desktop interface and bundled fonts/icons, so the app itself does not need an
  internet connection

The app is designed for one computer and one local data store. It does not sync
records between devices.

## Supported desktop downloads

| Operating system | Installer | Architecture |
|---|---|---|
| Windows | NSIS `.exe` installer | x64 |
| macOS | `.dmg` disk image | Apple Silicon (ARM64) |
| Linux | `.AppImage` | x64 |

Linux is currently AppImage-only, and macOS builds target Apple Silicon.
Installers are unsigned, so Windows or macOS may display security warnings.

The website's download buttons look up the latest public GitHub Release and
link directly to the matching installer. If the lookup is unavailable, the
buttons open the release page so a visitor can choose a file.

## Repository layout

```text
app.py                       Flask app running locally inside the desktop app
tools/                       Accounts, encrypted workspace, inventory and sales
frontend/templates/          Local app interface
frontend/static/             Local styles, icons and font assets
desktop/                     Electron shell and installer configuration
scripts/                     Backend packaging, icons and release helpers
website/                     Next.js product website (Vercel root directory)
.github/workflows/release.yml Cross-platform installer and GitHub Release workflow
```

## Run the local app from source

Requirements: Python 3.12 is used by the release build workflow.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

This runs the Flask interface for local development. Use the Electron desktop
app for normal use with the operating system-protected encryption key.

## Develop the desktop app

Install the Python requirements above, then install Node.js 22 or later.
From the repository root:

```powershell
python -m pip install -r requirements-build.txt
python scripts/generate_app_icons.py
python scripts/build_backend.py
Set-Location desktop
npm ci
npm run dev
```

The Electron shell starts the local Flask service and opens it in a desktop
window. Set `SHOPMANAGER_PYTHON` if Python is not on `PATH`.

To build an installer on the current operating system:

```powershell
npm run dist
```

The generated installer is placed in `desktop/release/`. Build on each target
operating system to produce that platform's installer. The app ID remains
`com.infofusion.shopmanagementsystem` for installer identity continuity.

## Local data, encryption and backups

Packaged app data is kept in Electron's per-user data directory. DukaanDesk
continues to use the existing `Shop Management System` data-directory name so
existing accounts and encrypted records remain available after the visible
rebrand. Use **File > Open Data Folder** in the app to locate it.

Shop records and generated QR images are encrypted at rest. The encryption key
is protected by the operating system's secure storage. Linux requires a Secret
Service or KWallet keyring; the app refuses to use Linux's unprotected
`basic_text` storage backend.

Back up the complete data directory, including `encryption-key.dat`, while
keeping the backup private. If the key is lost, the encrypted records cannot be
opened. Because the key is protected by the operating system, restoring data
under a different computer or user profile may not work. The app does not
currently provide a cross-device transfer feature.

Passwordless sign-in is convenient, but does not stop another person using the
same operating-system account from opening that shop profile.

On first use of the updated interface, existing product, customer and sales
records are migrated into the encrypted, per-account workspace file. Use the
app's Settings page to export or import workspace JSON; keep exports private
because they contain customer and sales information.

## Product website and deployment

The website is in `website/`. To run it locally:

```powershell
Set-Location website
npm ci
npm run dev
```

The Vercel project uses `website/` as its root directory. Its configured URL is
<https://dukaandesk-info-fusion.vercel.app>. After changes are
pushed to the connected GitHub repository's production branch, Vercel builds
and deploys the website. The `robots.txt` and `sitemap.xml` files are generated
for the canonical URL in `website/src/lib/site.ts`.

The download page links to public GitHub Release assets; Vercel does not host
the installers. A new desktop installer is published separately by pushing a
version tag, for example:

```powershell
git tag v1.0.1
git push origin v1.0.1
```

The GitHub Actions workflow builds Windows, macOS and Linux packages and creates
a release for a pushed `v*` tag. A regular push to the production branch updates
the website, but does not publish a new desktop installer.

For Google Search Console, verify the current Vercel URL (or a custom domain
after it is connected) and submit its `/sitemap.xml`. The verification tag in
the website metadata is public by design; it is not an API key or password.
Search indexing and ranking depend on search engines and cannot be guaranteed.

## Tests and checks

Run Python tests from the repository root:

```powershell
python -m unittest discover -s tests
```

Check/build the Electron app from `desktop/`:

```powershell
npm run build
```

Check/build the website from `website/`:

```powershell
npm run typecheck
npm run build
```

## Security notes

- The desktop backend binds to `127.0.0.1` and runs without Flask debug mode
  when launched by Electron.
- The website does not handle or store shop records.
- Never commit shop data, encryption keys, passwords, signing credentials or
  private tokens.
- The Google Search Console HTML verification value is intentionally public
  metadata and does not grant access to a Google account.
