# 🏪 Shop Management System – New Fashion House

A complete offline shop management system built with Flask (Python) and vanilla HTML/CSS/JavaScript.  
Designed for single‑PC use (localhost) – no internet required.  
Created for **New Fashion House**, managed by Basanta Sa.

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

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.x + Flask |
| Frontend | HTML5, CSS3, JavaScript (vanilla) |
| Storage | JSON files (no database required) |
| QR Codes | `qrcode` + `Pillow` (Python) |
| Icons | Font Awesome 6 |
| Font | Google Inter |

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
└── README.md
```

---

## 🚀 Installation & Setup

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

### 4. Run the application
```bash
python app.py
```

The server will start at `http://localhost:5000` and automatically open in your browser.

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
- All data is stored in **JSON files** inside the `storage/` folder.
- No external database required – the system works fully offline.
- QR images are saved as PNG files under `storage/ProductQRs/`.

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