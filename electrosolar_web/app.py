import sqlite3
import bcrypt
import json
import os
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g
from functools import wraps

app = Flask(__name__)
app.secret_key = 'electrosolar-secret-key-change-in-production'

DB_PATH = os.path.join(os.path.dirname(__file__), 'electrosolar.db')

# ── Database helpers ──────────────────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()

def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur

def rows_to_list(rows):
    return [dict(r) for r in rows]

# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def current_user():
    return {'id': session.get('user_id'), 'username': session.get('username'),
            'full_name': session.get('full_name'), 'role': session.get('role')}

def get_settings():
    rows = query("SELECT key, value FROM settings")
    return {r['key']: r['value'] for r in rows}

def next_invoice_no():
    today = datetime.now().strftime('%Y%m%d')
    row = query(f"SELECT invoice_no FROM sales WHERE invoice_no LIKE 'INV-{today}-%' ORDER BY id DESC LIMIT 1", one=True)
    seq = int(row['invoice_no'].split('-')[2]) + 1 if row else 1
    return f"INV-{today}-{seq:04d}"

def next_po_ref():
    today = datetime.now().strftime('%Y%m%d')
    row = query(f"SELECT ref_no FROM purchases WHERE ref_no LIKE 'PO-{today}-%' ORDER BY id DESC LIMIT 1", one=True)
    seq = int(row['ref_no'].split('-')[2]) + 1 if row else 1
    return f"PO-{today}-{seq:04d}"

# ── Context processor - inject into all templates ────────────────────────────

@app.context_processor
def inject_globals():
    s = get_settings() if 'user_id' in session else {}
    low_stock = 0
    if 'user_id' in session:
        r = query("SELECT COUNT(*) as c FROM products WHERE is_active=1 AND quantity <= reorder_level", one=True)
        low_stock = r['c'] if r else 0
    return dict(settings=s, current_user=current_user(), low_stock_count=low_stock,
                now=datetime.now())

# ── Init DB ───────────────────────────────────────────────────────────────────

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            category_id INTEGER REFERENCES categories(id),
            brand_id INTEGER REFERENCES brands(id),
            model_number TEXT,
            wattage REAL,
            voltage REAL,
            amperage REAL,
            capacity TEXT,
            warranty TEXT,
            cost_price REAL NOT NULL DEFAULT 0,
            selling_price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            reorder_level INTEGER NOT NULL DEFAULT 5,
            unit TEXT NOT NULL DEFAULT 'piece',
            description TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            credit_limit REAL NOT NULL DEFAULT 0,
            credit_balance REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE NOT NULL,
            customer_id INTEGER REFERENCES customers(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            subtotal REAL NOT NULL DEFAULT 0,
            discount REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            amount_paid REAL NOT NULL DEFAULT 0,
            balance REAL NOT NULL DEFAULT 0,
            payment_method TEXT NOT NULL DEFAULT 'cash',
            status TEXT NOT NULL DEFAULT 'paid',
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            subtotal REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ref_no TEXT UNIQUE NOT NULL,
            supplier_id INTEGER REFERENCES suppliers(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            total_cost REAL NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            subtotal REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            reason TEXT,
            reference_id INTEGER,
            reference_type TEXT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    db.commit()

    # Seed users
    cur = db.execute("SELECT id FROM users WHERE username='admin'")
    if not cur.fetchone():
        ph_admin = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
        ph_staff = bcrypt.hashpw(b'staff123', bcrypt.gensalt()).decode()
        db.execute("INSERT INTO users (username,password_hash,full_name,role) VALUES (?,?,?,?)",
                   ('admin', ph_admin, 'Administrator', 'admin'))
        db.execute("INSERT INTO users (username,password_hash,full_name,role) VALUES (?,?,?,?)",
                   ('staff', ph_staff, 'Sales Staff', 'staff'))

    # Seed settings
    for k, v in [('shop_name','ElectroSolar Shop'),('shop_address','123 Solar Street, Lagos'),
                  ('shop_phone','08012345678'),('currency','₦'),
                  ('receipt_footer','Thank you for your business!'),('tax_rate','0')]:
        db.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (k, v))

    # Seed categories
    for c in ['Solar Panels','Batteries','Inverters','Charge Controllers','Bulbs & Lighting',
               'Wires & Cables','Sockets & Switches','Circuit Breakers & Fuses','Connectors','Accessories']:
        db.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (c,))

    # Seed brands
    for b in ['Luminous','Felicity Solar','Sukam','Prag','UTL','Genus','Nexus','Ritar','Generic','Nexus']:
        db.execute("INSERT OR IGNORE INTO brands (name) VALUES (?)", (b,))

    # Seed sample products
    cur = db.execute("SELECT id FROM products WHERE sku='SOL-001'")
    if not cur.fetchone():
        def cid(name): return db.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()[0]
        def bid(name):
            r = db.execute("SELECT id FROM brands WHERE name=?", (name,)).fetchone()
            return r[0] if r else None
        prods = [
            ('150W Mono Solar Panel','SOL-001',cid('Solar Panels'),bid('Felicity Solar'),'FP-150M',150,18,None,None,'1 year',45000,58000,12,5,'piece','150W monocrystalline solar panel'),
            ('300W Poly Solar Panel','SOL-002',cid('Solar Panels'),bid('Prag'),'PRG-300P',300,24,None,None,'1 year',82000,105000,8,3,'piece','300W polycrystalline solar panel'),
            ('100Ah AGM Battery','BAT-001',cid('Batteries'),bid('Luminous'),'LUM-100AGM',None,12,None,'100Ah','18 months',38000,50000,5,4,'piece','100Ah 12V sealed AGM deep cycle battery'),
            ('200Ah Tubular Battery','BAT-002',cid('Batteries'),bid('Sukam'),'SK-200T',None,12,None,'200Ah','2 years',65000,82000,3,4,'piece','200Ah 12V flooded tubular battery'),
            ('1.5kVA Pure Sine Inverter','INV-001',cid('Inverters'),bid('UTL'),'UTL-1500',1500,24,None,'1.5kVA','1 year',55000,72000,6,3,'piece','1.5kVA 24V pure sine wave inverter'),
            ('3.5kVA Hybrid Inverter','INV-002',cid('Inverters'),bid('Luminous'),'LUM-3500H',3500,48,None,'3.5kVA','2 years',95000,125000,4,2,'piece','3.5kVA 48V hybrid solar inverter'),
            ('30A MPPT Controller','CHG-001',cid('Charge Controllers'),bid('Generic'),'MPPT-30A',None,12,30,None,'1 year',12000,17500,10,5,'piece','30A MPPT solar charge controller'),
            ('40A PWM Controller','CHG-002',cid('Charge Controllers'),bid('Generic'),'PWM-40A',None,12,40,None,'1 year',8500,12000,15,5,'piece','40A PWM solar charge controller'),
            ('9W LED Bulb','BLB-001',cid('Bulbs & Lighting'),bid('Nexus'),'NX-9W',9,220,None,None,'6 months',850,1400,2,10,'piece','9W E27 LED bulb warm white'),
            ('4mm² Solar Cable','WIR-001',cid('Wires & Cables'),bid('Generic'),'SC-4MM',None,None,None,None,None,380,600,200,50,'metre','4mm² DC solar cable per metre'),
            ('6mm² Solar Cable','WIR-002',cid('Wires & Cables'),bid('Generic'),'SC-6MM',None,None,None,None,None,520,850,150,50,'metre','6mm² DC solar cable per metre'),
            ('32A Single Pole MCB','MCB-001',cid('Circuit Breakers & Fuses'),bid('Generic'),'MCB-32SP',None,230,32,None,'1 year',1800,2800,20,10,'piece','32A single pole MCB'),
            ('PVC 3-Pin Socket','SOC-001',cid('Sockets & Switches'),bid('Generic'),'PVC-3P',None,230,13,None,'6 months',450,800,30,10,'piece','13A PVC 3-pin wall socket'),
            ('MC4 Connector Pair','CON-001',cid('Connectors'),bid('Generic'),'MC4-PAIR',None,None,None,None,None,350,600,50,20,'pair','MC4 solar connector pair M+F'),
        ]
        for p in prods:
            db.execute("""INSERT INTO products
                (name,sku,category_id,brand_id,model_number,wattage,voltage,amperage,capacity,warranty,
                 cost_price,selling_price,quantity,reorder_level,unit,description)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", p)

    # Seed customers
    cur = db.execute("SELECT id FROM customers WHERE phone='08011111111'")
    if not cur.fetchone():
        db.execute("INSERT INTO customers (name,phone,address,credit_limit) VALUES (?,?,?,?)",
                   ('Emeka Solar Ltd','08011111111','15 Industrial Road, Lagos',500000))
        db.execute("INSERT INTO customers (name,phone,address,credit_limit,credit_balance) VALUES (?,?,?,?,?)",
                   ('Bright Electrical','08022222222','42 Market Street, Abuja',300000,45000))
        db.execute("INSERT INTO customers (name,phone,address,credit_limit) VALUES (?,?,?,?)",
                   ('Green Energy Co.','08033333333','7 Solar Avenue, Enugu',200000))

    # Seed suppliers
    cur = db.execute("SELECT id FROM suppliers WHERE phone='08066666666'")
    if not cur.fetchone():
        db.execute("INSERT INTO suppliers (name,contact_person,phone,email) VALUES (?,?,?,?)",
                   ('Felicity Solar Nigeria','John Okafor','08066666666','john@felicity.com.ng'))
        db.execute("INSERT INTO suppliers (name,contact_person,phone,email) VALUES (?,?,?,?)",
                   ('Luminous Distributors','Mary Eze','08077777777','mary@luminous.ng'))
        db.execute("INSERT INTO suppliers (name,contact_person,phone,email) VALUES (?,?,?,?)",
                   ('Nexus Electronics','David Adeyemi','08088888888','david@nexusng.com'))

    db.commit()
    db.close()
    print("✓ Database initialized")

# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        u = query("SELECT * FROM users WHERE username=? AND is_active=1",
                  (request.form['username'],), one=True)
        if u and bcrypt.checkpw(request.form['password'].encode(), u['password_hash'].encode()):
            session.update({'user_id': u['id'], 'username': u['username'],
                            'full_name': u['full_name'], 'role': u['role']})
            return redirect(url_for('dashboard'))
        error = 'Invalid username or password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today().isoformat()
    month_start = today[:7] + '-01'
    stats = {
        'total_products':     query("SELECT COUNT(*) c FROM products WHERE is_active=1", one=True)['c'],
        'low_stock_count':    query("SELECT COUNT(*) c FROM products WHERE is_active=1 AND quantity<=reorder_level", one=True)['c'],
        'today_sales':        query("SELECT COALESCE(SUM(total),0) c FROM sales WHERE date(created_at)=?", (today,), one=True)['c'],
        'today_transactions': query("SELECT COUNT(*) c FROM sales WHERE date(created_at)=?", (today,), one=True)['c'],
        'month_sales':        query("SELECT COALESCE(SUM(total),0) c FROM sales WHERE date(created_at)>=?", (month_start,), one=True)['c'],
        'total_customers':    query("SELECT COUNT(*) c FROM customers", one=True)['c'],
        'credit_outstanding': query("SELECT COALESCE(SUM(credit_balance),0) c FROM customers", one=True)['c'],
    }
    recent_sales = query("""SELECT s.*, COALESCE(c.name,'Walk-in') customer_name
        FROM sales s LEFT JOIN customers c ON s.customer_id=c.id
        ORDER BY s.created_at DESC LIMIT 8""")
    low_stock = query("""SELECT p.*, c.name category_name FROM products p
        LEFT JOIN categories c ON p.category_id=c.id
        WHERE p.is_active=1 AND p.quantity<=p.reorder_level ORDER BY p.quantity LIMIT 8""")
    # 7-day chart data
    chart = query("""SELECT date(created_at) day, COUNT(*) tx, COALESCE(SUM(total),0) rev
        FROM sales WHERE date(created_at) >= date('now','-6 days')
        GROUP BY date(created_at) ORDER BY day""")
    return render_template('dashboard.html', stats=stats, recent_sales=recent_sales,
                           low_stock=low_stock, chart=rows_to_list(chart))

@app.route('/reset-monthly-sales', methods=['POST'])
@admin_required
def reset_monthly_sales():
    today = date.today().isoformat()
    month_start = today[:7] + '-01'
    try:
        db = get_db()
        # Get all sales from this month to delete associated items
        sales_ids = query("SELECT id FROM sales WHERE date(created_at)>=?", (month_start,))
        # Delete sale items
        for s in sales_ids:
            db.execute("DELETE FROM sale_items WHERE sale_id=?", (s['id'],))
        # Delete sales
        db.execute("DELETE FROM sales WHERE date(created_at)>=?", (month_start,))
        db.commit()
        return jsonify({'success': True, 'message': 'Monthly sales cleared'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ── Products ──────────────────────────────────────────────────────────────────

@app.route('/products')
@login_required
def products():
    items = query("""SELECT p.*, c.name category_name, b.name brand_name
        FROM products p LEFT JOIN categories c ON p.category_id=c.id
        LEFT JOIN brands b ON p.brand_id=b.id WHERE p.is_active=1 ORDER BY p.name""")
    cats = query("SELECT * FROM categories ORDER BY name")
    brands = query("SELECT * FROM brands ORDER BY name")
    return render_template('products.html', products=rows_to_list(items), categories=rows_to_list(cats), brands=rows_to_list(brands))

@app.route('/products/save', methods=['POST'])
@login_required
def products_save():
    f = request.form
    pid = f.get('id')
    def nv(k): return f.get(k) or None
    def nf(k): v = f.get(k); return float(v) if v else None
    def ni(k): v = f.get(k); return int(v) if v else None
    try:
        if pid:
            execute("""UPDATE products SET name=?,sku=?,category_id=?,brand_id=?,model_number=?,
                wattage=?,voltage=?,amperage=?,capacity=?,warranty=?,cost_price=?,selling_price=?,
                reorder_level=?,unit=?,description=?,updated_at=datetime('now') WHERE id=?""",
                (f['name'],f['sku'],ni('category_id'),ni('brand_id'),nv('model_number'),
                 nf('wattage'),nf('voltage'),nf('amperage'),nv('capacity'),nv('warranty'),
                 float(f['cost_price']),float(f['selling_price']),int(f.get('reorder_level',5)),
                 f.get('unit','piece'),nv('description'),pid))
            flash('Product updated successfully', 'success')
        else:
            qty = int(f.get('quantity') or 0)
            cur = execute("""INSERT INTO products
                (name,sku,category_id,brand_id,model_number,wattage,voltage,amperage,capacity,warranty,
                 cost_price,selling_price,quantity,reorder_level,unit,description)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f['name'],f['sku'],ni('category_id'),ni('brand_id'),nv('model_number'),
                 nf('wattage'),nf('voltage'),nf('amperage'),nv('capacity'),nv('warranty'),
                 float(f['cost_price']),float(f['selling_price']),qty,
                 int(f.get('reorder_level',5)),f.get('unit','piece'),nv('description')))
            if qty > 0:
                execute("INSERT INTO stock_movements (product_id,movement_type,quantity,reason,user_id) VALUES (?,?,?,?,?)",
                        (cur.lastrowid,'in',qty,'Opening stock',session['user_id']))
            flash('Product added successfully', 'success')
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('products'))

@app.route('/products/delete/<int:pid>', methods=['POST'])
@admin_required
def products_delete(pid):
    execute("UPDATE products SET is_active=0 WHERE id=?", (pid,))
    flash('Product archived', 'success')
    return redirect(url_for('products'))

# ── Categories ────────────────────────────────────────────────────────────────

@app.route('/categories')
@login_required
def categories():
    items = query("""SELECT c.*, (SELECT COUNT(*) FROM products WHERE category_id=c.id AND is_active=1) pc
        FROM categories c ORDER BY name""")
    return render_template('categories.html', categories=items)

@app.route('/categories/save', methods=['POST'])
@admin_required
def categories_save():
    f = request.form
    if f.get('id'):
        execute("UPDATE categories SET name=?,description=? WHERE id=?", (f['name'],f.get('description',''),f['id']))
    else:
        execute("INSERT INTO categories (name,description) VALUES (?,?)", (f['name'],f.get('description','')))
    flash('Category saved', 'success')
    return redirect(url_for('categories'))

@app.route('/categories/delete/<int:cid>', methods=['POST'])
@admin_required
def categories_delete(cid):
    used = query("SELECT id FROM products WHERE category_id=? AND is_active=1 LIMIT 1", (cid,), one=True)
    if used:
        flash('Cannot delete: category has products assigned', 'error')
    else:
        execute("DELETE FROM categories WHERE id=?", (cid,))
        flash('Category deleted', 'success')
    return redirect(url_for('categories'))

# ── Brands ────────────────────────────────────────────────────────────────────

@app.route('/brands')
@login_required
def brands():
    items = query("""SELECT b.*, (SELECT COUNT(*) FROM products WHERE brand_id=b.id AND is_active=1) pc
        FROM brands b ORDER BY name""")
    return render_template('brands.html', brands=items)

@app.route('/brands/save', methods=['POST'])
@admin_required
def brands_save():
    f = request.form
    if f.get('id'):
        execute("UPDATE brands SET name=?,description=? WHERE id=?", (f['name'],f.get('description',''),f['id']))
    else:
        execute("INSERT INTO brands (name,description) VALUES (?,?)", (f['name'],f.get('description','')))
    flash('Brand saved', 'success')
    return redirect(url_for('brands'))

@app.route('/brands/delete/<int:bid>', methods=['POST'])
@admin_required
def brands_delete(bid):
    used = query("SELECT id FROM products WHERE brand_id=? AND is_active=1 LIMIT 1", (bid,), one=True)
    if used:
        flash('Cannot delete: brand has products assigned', 'error')
    else:
        execute("DELETE FROM brands WHERE id=?", (bid,))
        flash('Brand deleted', 'success')
    return redirect(url_for('brands'))

# ── Stock ─────────────────────────────────────────────────────────────────────

@app.route('/stock/in', methods=['GET','POST'])
@login_required
def stock_in():
    if request.method == 'POST':
        f = request.form
        pid, qty = int(f['product_id']), int(f['quantity'])
        execute("UPDATE products SET quantity=quantity+?, updated_at=datetime('now') WHERE id=?", (qty, pid))
        execute("INSERT INTO stock_movements (product_id,movement_type,quantity,reason,user_id) VALUES (?,?,?,?,?)",
                (pid,'in',qty,f.get('reason','Stock in'),session['user_id']))
        flash(f'Stock added successfully', 'success')
        return redirect(url_for('stock_in'))
    prods = query("SELECT * FROM products WHERE is_active=1 ORDER BY name")
    history = query("""SELECT sm.*,p.name product_name,u.full_name user_name
        FROM stock_movements sm JOIN products p ON sm.product_id=p.id JOIN users u ON sm.user_id=u.id
        WHERE sm.movement_type='in' ORDER BY sm.created_at DESC LIMIT 30""")
    return render_template('stock_in.html', products=prods, history=history)

@app.route('/stock/out', methods=['GET','POST'])
@login_required
def stock_out():
    if request.method == 'POST':
        f = request.form
        pid, qty = int(f['product_id']), int(f['quantity'])
        prod = query("SELECT quantity FROM products WHERE id=?", (pid,), one=True)
        if not prod or prod['quantity'] < qty:
            flash('Insufficient stock available', 'error')
        else:
            execute("UPDATE products SET quantity=quantity-?, updated_at=datetime('now') WHERE id=?", (qty, pid))
            execute("INSERT INTO stock_movements (product_id,movement_type,quantity,reason,user_id) VALUES (?,?,?,?,?)",
                    (pid,'out',qty,f.get('reason','Manual stock out'),session['user_id']))
            flash('Stock removed successfully', 'success')
        return redirect(url_for('stock_out'))
    prods = query("SELECT * FROM products WHERE is_active=1 ORDER BY name")
    history = query("""SELECT sm.*,p.name product_name,u.full_name user_name
        FROM stock_movements sm JOIN products p ON sm.product_id=p.id JOIN users u ON sm.user_id=u.id
        WHERE sm.movement_type='out' AND (sm.reference_type IS NULL OR sm.reference_type='manual')
        ORDER BY sm.created_at DESC LIMIT 30""")
    return render_template('stock_out.html', products=prods, history=history)

@app.route('/stock/damaged', methods=['GET','POST'])
@login_required
def stock_damaged():
    if request.method == 'POST':
        f = request.form
        pid, qty = int(f['product_id']), int(f['quantity'])
        prod = query("SELECT quantity FROM products WHERE id=?", (pid,), one=True)
        if not prod or prod['quantity'] < qty:
            flash('Insufficient stock available', 'error')
        else:
            execute("UPDATE products SET quantity=quantity-?, updated_at=datetime('now') WHERE id=?", (qty, pid))
            execute("INSERT INTO stock_movements (product_id,movement_type,quantity,reason,user_id) VALUES (?,?,?,?,?)",
                    (pid,'damaged',qty,f.get('reason','Damaged items'),session['user_id']))
            flash('Damaged items recorded', 'success')
        return redirect(url_for('stock_damaged'))
    prods = query("SELECT * FROM products WHERE is_active=1 ORDER BY name")
    history = query("""SELECT sm.*,p.name product_name,u.full_name user_name
        FROM stock_movements sm JOIN products p ON sm.product_id=p.id JOIN users u ON sm.user_id=u.id
        WHERE sm.movement_type='damaged' ORDER BY sm.created_at DESC LIMIT 30""")
    return render_template('stock_damaged.html', products=prods, history=history)

@app.route('/stock/movements')
@login_required
def stock_movements():
    ftype = request.args.get('type','')
    sql = """SELECT sm.*,p.name product_name,u.full_name user_name
        FROM stock_movements sm JOIN products p ON sm.product_id=p.id JOIN users u ON sm.user_id=u.id"""
    if ftype:
        movements = query(sql + " WHERE sm.movement_type=? ORDER BY sm.created_at DESC LIMIT 200", (ftype,))
    else:
        movements = query(sql + " ORDER BY sm.created_at DESC LIMIT 200")
    return render_template('stock_movements.html', movements=movements, filter_type=ftype)

# ── POS / Sales ───────────────────────────────────────────────────────────────

@app.route('/pos')
@login_required
def pos():
    prods = query("""SELECT p.*, c.name category_name FROM products p
        LEFT JOIN categories c ON p.category_id=c.id
        WHERE p.is_active=1 AND p.quantity>0 ORDER BY p.name""")
    customers = query("SELECT * FROM customers ORDER BY name")
    inv_no = next_invoice_no()
    return render_template('pos.html', products=prods, customers=customers, invoice_no=inv_no)

@app.route('/pos/complete', methods=['POST'])
@login_required
def pos_complete():
    data = request.get_json()
    try:
        db = get_db()
        # Validate stock
        for item in data['items']:
            p = db.execute("SELECT quantity,name FROM products WHERE id=?", (item['product_id'],)).fetchone()
            if not p or p['quantity'] < item['quantity']:
                return jsonify({'success': False, 'message': f"Insufficient stock for {p['name'] if p else 'product'}"})
        # Insert sale
        cur = db.execute("""INSERT INTO sales
            (invoice_no,customer_id,user_id,subtotal,discount,total,amount_paid,balance,payment_method,status,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (data['invoice_no'], data.get('customer_id') or None, session['user_id'],
             data['subtotal'], data.get('discount',0), data['total'],
             data['amount_paid'], data.get('balance',0),
             data.get('payment_method','cash'), data.get('status','paid'), data.get('notes','')))
        sale_id = cur.lastrowid
        for item in data['items']:
            db.execute("INSERT INTO sale_items (sale_id,product_id,product_name,quantity,unit_price,subtotal) VALUES (?,?,?,?,?,?)",
                       (sale_id, item['product_id'], item['product_name'], item['quantity'], item['unit_price'], item['subtotal']))
            db.execute("UPDATE products SET quantity=quantity-?, updated_at=datetime('now') WHERE id=?",
                       (item['quantity'], item['product_id']))
            db.execute("INSERT INTO stock_movements (product_id,movement_type,quantity,reason,reference_id,reference_type,user_id) VALUES (?,?,?,?,?,?,?)",
                       (item['product_id'],'out',item['quantity'],f"Sale: {data['invoice_no']}",sale_id,'sale',session['user_id']))
        # Update customer credit
        if data.get('customer_id') and data.get('balance',0) > 0:
            db.execute("UPDATE customers SET credit_balance=credit_balance+? WHERE id=?",
                       (data['balance'], data['customer_id']))
        db.commit()
        return jsonify({'success': True, 'sale_id': sale_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/sales')
@login_required
def sales():
    from_date = request.args.get('from', date.today().strftime('%Y-%m-01'))
    to_date = request.args.get('to', date.today().isoformat())
    items = query("""SELECT s.*, COALESCE(c.name,'Walk-in') customer_name, u.full_name staff_name
        FROM sales s LEFT JOIN customers c ON s.customer_id=c.id JOIN users u ON s.user_id=u.id
        WHERE date(s.created_at) BETWEEN ? AND ? ORDER BY s.created_at DESC""", (from_date, to_date))
    totals = {'revenue': sum(s['total'] for s in items), 'count': len(items),
              'outstanding': sum(s['balance'] for s in items)}
    return render_template('sales.html', sales=items, totals=totals, from_date=from_date, to_date=to_date)

@app.route('/sales/<int:sid>')
@login_required
def sale_detail(sid):
    sale = query("""SELECT s.*, COALESCE(c.name,'Walk-in') customer_name,
        COALESCE(c.phone,'') customer_phone, u.full_name staff_name
        FROM sales s LEFT JOIN customers c ON s.customer_id=c.id JOIN users u ON s.user_id=u.id
        WHERE s.id=?""", (sid,), one=True)
    items = query("SELECT * FROM sale_items WHERE sale_id=?", (sid,))
    return render_template('receipt.html', sale=sale, items=items)

@app.route('/sales/delete/<int:sid>', methods=['POST'])
@admin_required
def sales_delete(sid):
    db = get_db()
    # Get sale details before deletion
    sale = query("SELECT id FROM sales WHERE id=?", (sid,), one=True)
    if sale:
        # Delete sale items first
        db.execute("DELETE FROM sale_items WHERE sale_id=?", (sid,))
        # Delete sale
        db.execute("DELETE FROM sales WHERE id=?", (sid,))
        db.commit()
        flash('Sale/Transaction deleted successfully', 'success')
    else:
        flash('Sale not found', 'error')
    return redirect(url_for('sales'))

# ── Customers ─────────────────────────────────────────────────────────────────

@app.route('/customers')
@login_required
def customers():
    items = query("SELECT * FROM customers ORDER BY name")
    return render_template('customers.html', customers=items)

@app.route('/customers/save', methods=['POST'])
@login_required
def customers_save():
    f = request.form
    if f.get('id'):
        execute("UPDATE customers SET name=?,phone=?,email=?,address=?,credit_limit=? WHERE id=?",
                (f['name'],f.get('phone',''),f.get('email',''),f.get('address',''),float(f.get('credit_limit',0)),f['id']))
    else:
        execute("INSERT INTO customers (name,phone,email,address,credit_limit) VALUES (?,?,?,?,?)",
                (f['name'],f.get('phone',''),f.get('email',''),f.get('address',''),float(f.get('credit_limit',0))))
    flash('Customer saved', 'success')
    return redirect(url_for('customers'))

@app.route('/customers/delete/<int:cid>', methods=['POST'])
@admin_required
def customers_delete(cid):
    execute("DELETE FROM customers WHERE id=?", (cid,))
    flash('Customer deleted', 'success')
    return redirect(url_for('customers'))

@app.route('/customers/<int:cid>/history')
@login_required
def customer_history(cid):
    customer = query("SELECT * FROM customers WHERE id=?", (cid,), one=True)
    history = query("""SELECT s.*, (SELECT COUNT(*) FROM sale_items WHERE sale_id=s.id) item_count
        FROM sales s WHERE s.customer_id=? ORDER BY s.created_at DESC""", (cid,))
    return render_template('customer_history.html', customer=customer, history=history)

# ── Suppliers ─────────────────────────────────────────────────────────────────

@app.route('/suppliers')
@login_required
def suppliers():
    items = query("SELECT * FROM suppliers ORDER BY name")
    return render_template('suppliers.html', suppliers=items)

@app.route('/suppliers/save', methods=['POST'])
@login_required
def suppliers_save():
    f = request.form
    if f.get('id'):
        execute("UPDATE suppliers SET name=?,contact_person=?,phone=?,email=?,address=? WHERE id=?",
                (f['name'],f.get('contact_person',''),f.get('phone',''),f.get('email',''),f.get('address',''),f['id']))
    else:
        execute("INSERT INTO suppliers (name,contact_person,phone,email,address) VALUES (?,?,?,?,?)",
                (f['name'],f.get('contact_person',''),f.get('phone',''),f.get('email',''),f.get('address','')))
    flash('Supplier saved', 'success')
    return redirect(url_for('suppliers'))

@app.route('/suppliers/delete/<int:sid>', methods=['POST'])
@admin_required
def suppliers_delete(sid):
    execute("DELETE FROM suppliers WHERE id=?", (sid,))
    flash('Supplier deleted', 'success')
    return redirect(url_for('suppliers'))

# ── Purchases ─────────────────────────────────────────────────────────────────

@app.route('/purchases')
@login_required
def purchases():
    items = query("""SELECT p.*, COALESCE(s.name,'—') supplier_name, u.full_name staff_name
        FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id JOIN users u ON p.user_id=u.id
        ORDER BY p.created_at DESC""")
    suppliers_list = query("SELECT * FROM suppliers ORDER BY name")
    products_list = query("SELECT * FROM products WHERE is_active=1 ORDER BY name")
    ref_no = next_po_ref()
    return render_template('purchases.html', purchases=items, suppliers=suppliers_list,
                           products=products_list, ref_no=ref_no)

@app.route('/purchases/save', methods=['POST'])
@login_required
def purchases_save():
    data = request.get_json()
    try:
        db = get_db()
        cur = db.execute("INSERT INTO purchases (ref_no,supplier_id,user_id,total_cost,notes) VALUES (?,?,?,?,?)",
                         (data['ref_no'], data.get('supplier_id') or None, session['user_id'],
                          data['total_cost'], data.get('notes','')))
        purchase_id = cur.lastrowid
        for item in data['items']:
            db.execute("INSERT INTO purchase_items (purchase_id,product_id,product_name,quantity,unit_cost,subtotal) VALUES (?,?,?,?,?,?)",
                       (purchase_id,item['product_id'],item['product_name'],item['quantity'],item['unit_cost'],item['subtotal']))
            db.execute("UPDATE products SET quantity=quantity+?, updated_at=datetime('now') WHERE id=?",
                       (item['quantity'], item['product_id']))
            db.execute("INSERT INTO stock_movements (product_id,movement_type,quantity,reason,reference_id,reference_type,user_id) VALUES (?,?,?,?,?,?,?)",
                       (item['product_id'],'in',item['quantity'],f"Purchase: {data['ref_no']}",purchase_id,'purchase',session['user_id']))
        db.commit()
        flash('Purchase saved and stock updated', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/purchases/<int:pid>')
@login_required
def purchase_detail(pid):
    purchase = query("""SELECT p.*, COALESCE(s.name,'—') supplier_name, u.full_name staff_name
        FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id JOIN users u ON p.user_id=u.id
        WHERE p.id=?""", (pid,), one=True)
    items = query("SELECT * FROM purchase_items WHERE purchase_id=?", (pid,))
    return render_template('purchase_detail.html', purchase=purchase, items=items)

# ── Reports ───────────────────────────────────────────────────────────────────

@app.route('/reports')
@login_required
def reports():
    rtype = request.args.get('type', 'sales')
    from_date = request.args.get('from', date.today().strftime('%Y-%m-01'))
    to_date = request.args.get('to', date.today().isoformat())
    data = []
    
    types = [
        ('sales', 'Sales Summary'),
        ('daily_detail', 'Daily Transactions'),
        ('profit', 'Profit by Product'),
        ('top_products', 'Top Products'),
        ('customer_debt', 'Customer Debt'),
        ('purchases', 'Purchases'),
        ('stock', 'Stock Valuation'),
        ('low_stock', 'Low Stock Items'),
    ]

    if rtype == 'sales':
        data = query("""SELECT date(created_at) day, COUNT(*) transactions,
            COALESCE(SUM(total),0) revenue, COALESCE(SUM(discount),0) discounts
            FROM sales WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY date(created_at) ORDER BY day""", (from_date, to_date))
    elif rtype == 'daily_detail':
        data = query("""SELECT s.id, s.invoice_no, COALESCE(c.name,'Walk-in') customer_name,
            s.total, s.amount_paid, s.balance, s.payment_method, s.status, s.created_at,
            u.full_name staff_name
            FROM sales s LEFT JOIN customers c ON s.customer_id=c.id JOIN users u ON s.user_id=u.id
            WHERE date(s.created_at) BETWEEN ? AND ?
            ORDER BY s.created_at DESC""", (from_date, to_date))
    elif rtype == 'profit':
        data = query("""SELECT si.product_name, si.product_id,
            SUM(si.quantity) qty_sold, SUM(si.subtotal) revenue,
            SUM(si.quantity * p.cost_price) cost,
            SUM(si.subtotal) - SUM(si.quantity * p.cost_price) profit
            FROM sale_items si JOIN sales s ON si.sale_id=s.id JOIN products p ON si.product_id=p.id
            WHERE date(s.created_at) BETWEEN ? AND ?
            GROUP BY si.product_id ORDER BY profit DESC""", (from_date, to_date))
    elif rtype == 'stock':
        data = query("""SELECT p.*, c.name category_name, b.name brand_name,
            (p.quantity * p.cost_price) stock_value
            FROM products p LEFT JOIN categories c ON p.category_id=c.id
            LEFT JOIN brands b ON p.brand_id=b.id WHERE p.is_active=1 ORDER BY c.name, p.name""")
    elif rtype == 'low_stock':
        data = query("""SELECT p.*, c.name category_name FROM products p
            LEFT JOIN categories c ON p.category_id=c.id
            WHERE p.is_active=1 AND p.quantity<=p.reorder_level ORDER BY p.quantity""")
    elif rtype == 'top_products':
        data = query("""SELECT si.product_name, SUM(si.quantity) qty_sold, SUM(si.subtotal) revenue
            FROM sale_items si JOIN sales s ON si.sale_id=s.id
            WHERE date(s.created_at) BETWEEN ? AND ?
            GROUP BY si.product_id ORDER BY qty_sold DESC LIMIT 20""", (from_date, to_date))
    elif rtype == 'customer_debt':
        data = query("""SELECT c.id, c.name, c.phone, c.email, c.credit_limit, c.credit_balance,
            COUNT(DISTINCT s.id) transaction_count, MAX(s.created_at) last_purchase
            FROM customers c LEFT JOIN sales s ON c.id=s.customer_id
            WHERE c.credit_balance > 0
            GROUP BY c.id ORDER BY c.credit_balance DESC""")
    elif rtype == 'purchases':
        data = query("""SELECT p.*, COALESCE(s.name,'—') supplier_name
            FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id
            WHERE date(p.created_at) BETWEEN ? AND ? ORDER BY p.created_at DESC""", (from_date, to_date))

    return render_template('reports.html', report_type=rtype, data=data,
                           from_date=from_date, to_date=to_date, types=types)

# ── Users ─────────────────────────────────────────────────────────────────────

@app.route('/users')
@admin_required
def users():
    items = query("SELECT id,username,full_name,role,is_active,created_at FROM users ORDER BY created_at")
    return render_template('users.html', users=items)

@app.route('/users/save', methods=['POST'])
@admin_required
def users_save():
    f = request.form
    if f.get('id'):
        execute("UPDATE users SET full_name=?,role=?,is_active=? WHERE id=?",
                (f['full_name'],f['role'],int(f.get('is_active',1)),f['id']))
        flash('User updated', 'success')
    else:
        if not f.get('password'):
            flash('Password is required', 'error')
            return redirect(url_for('users'))
        ph = bcrypt.hashpw(f['password'].encode(), bcrypt.gensalt()).decode()
        try:
            execute("INSERT INTO users (username,password_hash,full_name,role) VALUES (?,?,?,?)",
                    (f['username'],ph,f['full_name'],f['role']))
            flash('User created', 'success')
        except Exception as e:
            flash(str(e), 'error')
    return redirect(url_for('users'))

@app.route('/users/reset-password', methods=['POST'])
@admin_required
def reset_password():
    f = request.form
    if len(f.get('password','')) < 6:
        flash('Password must be at least 6 characters', 'error')
    else:
        ph = bcrypt.hashpw(f['password'].encode(), bcrypt.gensalt()).decode()
        execute("UPDATE users SET password_hash=? WHERE id=?", (ph, f['user_id']))
        flash('Password reset successfully', 'success')
    return redirect(url_for('users'))

# ── Settings ──────────────────────────────────────────────────────────────────

@app.route('/settings', methods=['GET','POST'])
@admin_required
def settings_page():
    if request.method == 'POST':
        for k in ['shop_name','shop_address','shop_phone','currency','receipt_footer','tax_rate']:
            execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (k, request.form.get(k,'')))
        flash('Settings saved', 'success')
        return redirect(url_for('settings_page'))
    s = get_settings()
    return render_template('settings.html', s=s)

# ── API: product price lookup ─────────────────────────────────────────────────

@app.route('/api/product/<int:pid>')
@login_required
def api_product(pid):
    p = query("SELECT id,name,selling_price,cost_price,quantity,unit FROM products WHERE id=?", (pid,), one=True)
    return jsonify(dict(p) if p else {})

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("  ⚡ ElectroSolar Manager")
    print("  Running at: http://localhost:5000")
    print("  Login: admin / admin123")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
