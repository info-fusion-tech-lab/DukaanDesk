# Shop Management System

A shop management system with inventory, customer ledger, sales and reports. The
desktop application runs locally and stores business records on the computer
where it is installed. A separate product website project provides information
and release downloads.

---

## ✨ Features

### 🔐 Core Modules
- **Dashboard** – Key metrics: products, stock, customers, sales, revenue, receivables, payables, low‑stock alerts.
- **Inventory** – Add, edit, delete products with auto‑generated unique codes, QR codes, and custom sizes.
- **Customers** – Register customers with phone number, track balance, transaction history (GAVE/GOT), receivables.
- **Sales** – Bulk sales (add multiple items), payment types: Cash, Online, Udhari (credit), Split payments.
- **Reports** – Sales history with date range & payment type filters, summary stats.

### 🧰 Tools & Utilities
- **QR Code Generation** – Each product gets a unique QR code (with product code label) stored in `storage/ProductQRs/`.
- **Product Code Generator** – Deterministic code based on name, price, size.
- **Low‑Stock Warnings** – Visual badges and alerts when stock falls below minimum level.
- **Search** – Quick search across products (name/code) and customers (name/phone).
- **Responsive Design** – Works on desktop and mobile (touch‑friendly).
- **Beginner‑Friendly UI** – Clean, modern, with modals, toast notifications, and intuitive navigation.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.x + Flask |
| Frontend | HTML5, CSS3, JavaScript (vanilla) |
| Storage | JSON files (no database required) |
| QR Codes | `qrcode` + `Pillow` (Python) |
| Desktop application | Electron + TypeScript |
| Product website | Next.js, deployed on Vercel |

---

## 📁 Project Structure

```
Shop Management System/
├── app.py                  # Flask application (routes, main)
├── tools/                  # Backend modules
│   ├── GenerateCode.py     # Unique product code generator
│   ├── GenerateQR.py       # QR image generator with label
│   ├── StorageManager.py   # Product JSON CRUD
│   ├── CustomerManager.py  # Customer ledger & transactions
│   └── SalesManager.py     # Sales logic (single/bulk, payments)
├── frontend/
│   ├── static/
│   │   └── style.css       # All custom styles
│   └── templates/
│       ├── base.html       # Layout (sidebar, header, footer)
│       ├── landing.html    # Public landing page
│       ├── index.html      # Dashboard
│       ├── inventory.html  # Product management
│       ├── customers.html  # Customer management
│       ├── sales.html      # Bulk sales with payment options
│       └── reports.html    # Sales history & filters
├── storage/                # Data & QR images
│   ├── ProductQRs/         # Generated QR images (code.png)
│   ├── ProductList.json
│   ├── CustomerList.json
│   └── SalesLog.json
├── requirements.txt        # Python dependencies
├── requirements-build.txt  # PyInstaller build dependency
├── desktop/                # Electron desktop shell and installer config
├── website/                # Product information website (Vercel root)
├── scripts/build_backend.py # PyInstaller build for the local service
├── scripts/set_release_version.mjs # Set installer version from a release tag
├── .github/workflows/      # Cross-platform release builds
└── README.md
```

---

## Run from source

### 1. Clone or download the project
```bash
git clone <your-repo-url>
cd "Shop Management System"
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
# Activate:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### Run the Flask interface in a browser
```bash
python app.py
```

The development server opens at `http://127.0.0.1:5000`. By default, source
development continues to use the project `storage/` directory.

## Desktop application

The Electron shell starts the local Flask service, opens the existing interface
in a desktop window and stops the service when the app exits. The packaged
application binds only to `127.0.0.1` and runs without Flask debug mode.

### Develop the desktop app

1. Install the Python requirements and Node.js 22 or later.
2. Install Electron dependencies:
   ```bash
   cd desktop
   npm install
   ```
3. Run the app from the repository root context:
   ```bash
   npm run dev
   ```
   The desktop development mode uses the repository's existing `storage/`
   directory. Set `SHOPMANAGER_PYTHON` if your Python executable is not on PATH.

### Build a local installer

From the repository root, install `requirements-build.txt` in the active Python
environment, then run:

```bash
python scripts/build_backend.py
cd desktop
npm ci
npm run dist
```

Installers are written to `desktop/release/`. Build on each target operating
system; PyInstaller produces a backend for the operating system where it runs.
The GitHub Actions workflow builds Windows, macOS and Linux packages when a
version tag such as `v1.0.0` is pushed.

### Local data and backups

Packaged releases store JSON records and generated QR images in the Electron
user-data directory, not beside the installed program. Use **File → Open Data
Folder** in the app to access it. The product website does not receive shop
records.

The first packaged launch can import an existing `storage/` folder placed next
to the installed executable. Back up the old folder before migrating. For
regular use, close the app before copying the data folder to a separate backup
location. Keep backups private because they may contain customer information.

## Product website

The website lives in `website/` and contains the product homepage, product
overview, feature list, quick-start guide, about page and download links.

For local development, run `cd website`, then `npm install` and `npm run dev`.
The development server prints the local preview URL.

For Vercel, import this repository and set **Root Directory** to `website`.
Vercel detects Next.js and builds the site from that directory. The download
page links to the repository's GitHub Releases page; desktop installers are
published there by the release workflow, rather than served as large Vercel
files. Set `NEXT_PUBLIC_RELEASES_URL` in Vercel if releases are hosted at a
different public URL. A public download page cannot deliver assets from a
private GitHub repository to visitors without repository access.

Packaged installers are currently unsigned. Windows and macOS may show
security warnings until platform code-signing certificates are configured.

To publish installers, push a semantic version tag (the tag sets the desktop
installer version) after configuring GitHub Actions permissions to create
releases:

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 🧭 Usage Guide

### Landing Page
- Public entry point – click **Go to Dashboard** to enter the management area.

### Dashboard
- Overview of business health: products, customers, sales, revenue, receivables, payables, low‑stock items.
- Quick actions: add product, customer, or go to sales/reports.

### Inventory
- **Add Product** – Fill in name, price, cost, quantity, min stock, size (or custom), category. Code and QR are auto‑generated.
- **Search** – Filter products by name or code.
- **Edit/Delete** – Update any field (including custom size); delete with confirmation.
- **QR View** – Click the QR icon to see the QR code in a modal and download it.

### Customers
- **Add Customer** – Name and phone number (unique identifier).
- **Search** – Filter by name or phone.
- **View** – See full transaction history and balance.
- **Record Transaction** – Choose **GAVE** (customer owes you) or **GOT** (customer pays). Balance updates automatically.
- **Edit/Delete** – Modify name/phone, or delete customer and all history.

### Sales
- **Bulk Sale** – Add multiple products to cart with quantity and custom selling price.
- **Customer** – Search and select a customer (walk‑in allowed).
- **Payment Types**:
  - Cash / Online – direct payment.
  - Udhari – credit sale (requires customer).
  - Split – divide total among cash, online, and udhari (customer required if udhari > 0).
- **Stock Validation** – Warns if quantity exceeds available stock.
- **Complete Sale** – Deducts stock, records transaction, and shows confirmation.

### Reports
- **Sales History** – Table with sale ID, date, items, total, payment type, customer, note.
- **Filter** – By date range and payment type.
- **Summary Stats** – Total sales count, revenue, cash/online/udhari totals.

---

## 📦 Data Storage
- Development mode stores data in JSON files inside the repository `storage/`
  folder.
- Packaged desktop releases store data in Electron's per-user data directory.
- QR images are stored alongside the local product data in `ProductQRs/`.
- Data is not synchronized between computers. Back up the data folder regularly.

---

## 🔧 Customisation

- **Shop name & owner** – Edit the `inject_shop_info()` context processor in `app.py`.
- **Styles** – Modify `frontend/static/style.css` to match your brand.
- **Currency** – Currently set to ₹ (Indian Rupee); change in templates if needed.

---

## 📝 License
This project is proprietary – developed for **New Fashion House**.  
Not licensed for public redistribution without permission.

---

## 🤝 Contributing
This is a private system; no external contributions are accepted at this time.

---

## 📬 Contact
For support or feature requests, contact the developer.

---

*Built with ❤️ for New Fashion House – 2026*

---