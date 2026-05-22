# ⚡ ElectroSolar Manager — Localhost Edition

Offline Inventory & Sales Management System  
Built with **Python Flask + SQLite** — runs in any browser on your computer.

---

## Quick Start (3 steps)

### Step 1 — Install Python
Download Python 3.10 or higher from https://python.org/downloads  
During installation on Windows, **tick "Add Python to PATH"** ✓

### Step 2 — Install dependencies
Open Command Prompt (Windows) or Terminal (Mac/Linux) in this folder:
```bash
pip install -r requirements.txt
```
Or on Mac/Linux:
```bash
pip3 install -r requirements.txt
```

### Step 3 — Run the app

**Windows:** Double-click `start.bat`

**Mac / Linux:**
```bash
chmod +x start.sh
./start.sh
```

**Or directly:**
```bash
python app.py          # Windows
python3 app.py         # Mac/Linux
```

Then open your browser at: **http://localhost:5000**

---

## Default Login

| Username | Password  | Role  |
|----------|-----------|-------|
| `admin`  | `admin123`| Admin — full access |
| `staff`  | `staff123`| Staff — sales and stock |

⚠ **Change passwords** immediately: go to **Users → Reset Password**

---

## Requirements

```
Flask==3.0.3
Flask-Login==0.6.3
bcrypt==4.1.3
```

Python 3.10+ required.

---

## Project Structure

```
electrosolar_web/
│
├── app.py                 ← Main app: all routes + database logic
├── requirements.txt       ← Python packages to install
├── start.bat              ← Windows one-click launcher
├── start.sh               ← Mac/Linux launcher
├── electrosolar.db        ← SQLite database (auto-created on first run)
│
├── templates/
│   ├── base.html          ← Sidebar layout (all pages extend this)
│   ├── login.html
│   ├── dashboard.html
│   ├── products.html
│   ├── categories.html
│   ├── brands.html
│   ├── stock_in.html
│   ├── stock_out.html
│   ├── stock_damaged.html
│   ├── stock_movements.html
│   ├── pos.html           ← Point of Sale
│   ├── sales.html         ← Sales history
│   ├── receipt.html       ← Printable receipt
│   ├── customers.html
│   ├── customer_history.html
│   ├── suppliers.html
│   ├── purchases.html
│   ├── purchase_detail.html
│   ├── reports.html       ← All 7 report types
│   ├── users.html
│   └── settings.html
│
└── static/
    ├── css/style.css      ← All styles
    └── js/main.js         ← Modal, toast, table filter helpers
```

---

## Pages & Features

| Page | URL | Description |
|------|-----|-------------|
| Login | `/login` | Secure login |
| Dashboard | `/dashboard` | Stats, chart, low stock alert |
| Products | `/products` | Full product management |
| Categories | `/categories` | Category CRUD |
| Brands | `/brands` | Brand CRUD |
| Stock In | `/stock/in` | Add stock |
| Stock Out | `/stock/out` | Remove stock manually |
| Damaged | `/stock/damaged` | Record damaged items |
| Movements | `/stock/movements` | Full stock audit trail |
| POS | `/pos` | Point of Sale — create new sales |
| Sales History | `/sales` | All past sales with filter |
| Receipt | `/sales/<id>` | View & print receipt |
| Customers | `/customers` | Customer management |
| Customer History | `/customers/<id>/history` | Purchase history per customer |
| Suppliers | `/suppliers` | Supplier management |
| Purchases | `/purchases` | Purchase orders — auto stock update |
| Reports | `/reports` | 7 report types |
| Users | `/users` | User management (admin only) |
| Settings | `/settings` | Shop details, currency, receipt (admin only) |

---

## Report Types

| Report | Filter |
|--------|--------|
| Sales Report | Date range |
| Profit Report | Date range |
| Stock Balance | All time |
| Low Stock | All time |
| Top Products | Date range |
| Customer Debt | All time |
| Supplier Purchases | Date range |

All reports are printable via the 🖨 Print button.

---

## Data Location

Your database is stored in `electrosolar.db` in the same folder as `app.py`.

**Back it up regularly** — copy this file to a USB drive or cloud storage.

To restore: replace `electrosolar.db` with your backup copy and restart the app.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `pip install` fails | Try `pip install -r requirements.txt --user` |
| Port 5000 busy | Edit `app.py` last line — change `port=5000` to `port=5001` |
| Can't find Python | Make sure "Add Python to PATH" was checked during install |
| bcrypt error on install | Run `pip install bcrypt==4.1.3 --only-binary :all:` |
| White page / error | Check the terminal window for error messages |
| Forgot admin password | Delete `electrosolar.db` — the app will recreate it with default users |

---

## Making It Available on Your Local Network

If you want other computers on the same WiFi to access the system:

1. Find your computer's IP address (e.g. `192.168.1.5`)
2. The app already listens on `0.0.0.0` so it's reachable at `http://192.168.1.5:5000`
3. Other computers on the same network can open that URL in their browser

---

*ElectroSolar Manager v1.0 — Python Flask + SQLite*
