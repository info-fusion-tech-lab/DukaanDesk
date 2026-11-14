import sys
import os
import secrets
from io import BytesIO
from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)

APP_ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.GenerateCode import CodeGenerator
from tools.GenerateQR import generate_labeled_qrcode
from tools import accounts
from tools.encrypted_json import load_bytes
import tools.StorageManager as storage
import tools.CustomerManager as customer_manager
import tools.SalesManager as sales_manager
from tools.paths import (
    get_storage_path,
    reset_profile_storage_path,
    set_profile_storage_path,
)
from werkzeug.utils import safe_join

app = Flask(
    __name__,
    template_folder=os.path.join(APP_ROOT, "frontend", "templates"),
    static_folder=os.path.join(APP_ROOT, "frontend", "static"),
)
app.secret_key = os.environ.get("SHOPMANAGER_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

code_gen = CodeGenerator()


@app.before_request
def require_local_account():
    public_endpoints = {
        "setup",
        "login",
        "login_account",
        "health",
        "favicon",
        "static",
    }
    if request.endpoint in public_endpoints:
        return None

    account_list = accounts.list_accounts()
    if not account_list:
        return redirect(url_for("setup"))
    if request.endpoint == "setup":
        return redirect(url_for("login"))

    account_id = session.get("account_id")
    if not account_id:
        return redirect(url_for("login"))

    account = accounts.get_account(account_id)
    if not account:
        session.clear()
        return redirect(url_for("login"))

    g.storage_path_token = set_profile_storage_path(
        accounts.profile_directory(account_id)
    )
    return None


@app.teardown_request
def reset_request_storage_path(error=None):
    token = getattr(g, "storage_path_token", None)
    if token is not None:
        reset_profile_storage_path(token)


@app.context_processor
def inject_shop_info():
    account_id = session.get("account_id")
    account = accounts.get_account(account_id) if account_id else None
    return {
        "shop_name": account["shop_name"] if account else "DukaanDesk",
        "shop_owner": account["username"] if account else "",
        "is_shop_owner": bool(account and account.get("is_owner")),
    }


@app.route("/", methods=["GET"])
def landing():
    if session.get("account_id"):
        return redirect(url_for("dashboard"))
    if accounts.list_accounts():
        return redirect(url_for("login"))
    return redirect(url_for("setup"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if accounts.list_accounts():
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form.get("username", "")
        shop_name = request.form.get("shop_name", "")
        password = request.form.get("password") or None
        confirmation = request.form.get("confirm_password", "")
        if password and password != confirmation:
            flash("The passwords do not match.", "error")
        else:
            try:
                account = accounts.create_account(username, shop_name, password)
            except ValueError as error:
                flash(str(error), "error")
            else:
                session.clear()
                session["account_id"] = account["id"]
                return redirect(url_for("dashboard"))

    return render_template("setup.html")


@app.route("/login", methods=["GET"])
def login():
    account_list = accounts.list_accounts()
    if not account_list:
        return redirect(url_for("setup"))
    if session.get("account_id") and accounts.get_account(session["account_id"]):
        return redirect(url_for("dashboard"))
    return render_template("login.html", accounts=account_list)


@app.route("/login/<account_id>", methods=["POST"])
def login_account(account_id):
    account = accounts.get_account(account_id)
    if not account or not accounts.verify_password(
        account, request.form.get("password", "")
    ):
        flash("The password is incorrect. Try again.", "error")
        return redirect(url_for("login"))

    session.clear()
    session["account_id"] = account["id"]
    return redirect(url_for("dashboard"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/accounts", methods=["GET", "POST"])
def manage_accounts():
    owner = accounts.get_account(session["account_id"])
    if not owner.get("is_owner"):
        abort(403)

    if request.method == "POST":
        username = request.form.get("username", "")
        shop_name = request.form.get("shop_name", "")
        password = request.form.get("password") or None
        if password and password != request.form.get("confirm_password", ""):
            flash("The passwords do not match.", "error")
        else:
            try:
                accounts.create_account(username, shop_name, password)
            except ValueError as error:
                flash(str(error), "error")
            else:
                flash("Local account created successfully.", "success")
                return redirect(url_for("manage_accounts"))

    return render_template("accounts.html", accounts=accounts.list_accounts())


@app.route("/account", methods=["GET", "POST"])
def account_settings():
    account = accounts.get_account(session["account_id"])
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirmation = request.form.get("confirm_password", "")
        remove_password = request.form.get("remove_password") == "on"

        if remove_password and new_password:
            flash("Choose either a new password or passwordless sign-in.", "error")
        elif new_password and new_password != confirmation:
            flash("The passwords do not match.", "error")
        elif account.get("password_hash") and not accounts.verify_password(
            account, request.form.get("current_password", "")
        ):
            flash("The current password is incorrect.", "error")
        else:
            try:
                accounts.update_account(
                    account["id"],
                    shop_name=request.form.get("shop_name", ""),
                    password=new_password or None,
                    remove_password=remove_password,
                )
            except ValueError as error:
                flash(str(error), "error")
            else:
                flash("Account settings saved.", "success")
                return redirect(url_for("account_settings"))

    return render_template("account_settings.html", account=account)

# ---------- FAVICON ----------
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(APP_ROOT, 'store.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    """Dashboard with full stats"""
    products = storage.load_products()
    customers = customer_manager.load_customers()
    sales = sales_manager.load_sales()  # dict of sales

    total_products = len(products)
    total_inventory_items = sum(p.get('Quantity', 0) for p in products.values())
    
    # Customer financials
    total_receivables = customer_manager.get_total_receivables()  # positive balances
    total_payable = sum(abs(c['Balance']) for c in customers.values() if c['Balance'] < 0)
    
    # Sales stats
    total_sales_count = len(sales)
    total_revenue = sum(sale.get('TotalAmount', 0) for sale in sales.values())
    
    # Low stock count
    low_stock_count = sum(1 for p in products.values() if p.get('Quantity', 0) <= p.get('MinStockLevel', 5))
    
    # Recent sales (last 5)
    recent_sales = sorted(sales.items(), key=lambda x: x[1].get('Timestamp', ''), reverse=True)[:5]
    
    return render_template('index.html',
                           total_products=total_products,
                           total_inventory_items=total_inventory_items,
                           total_receivables=total_receivables,
                           total_payable=total_payable,
                           total_sales_count=total_sales_count,
                           total_revenue=total_revenue,
                           low_stock_count=low_stock_count,
                           customers_count=len(customers),
                           recent_sales=recent_sales)

# ---------- INVENTORY ----------
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price', 0))
        cost_price = float(request.form.get('cost_price', 0))
        size = request.form.get('size', 'Normal')
        size_custom = request.form.get('size_custom', '').strip()
        if size_custom:
            size = size_custom
        quantity = int(request.form.get('quantity', 0))
        min_stock = int(request.form.get('min_stock', 5))
        category = request.form.get('category', 'General')

        # Auto-generate custom code
        code = code_gen.unique_code(product_name=name, product_price=price, size=size)

        new_product = {
            "Code": code,
            "Name": name,
            "Price": price,
            "CostPrice": cost_price,
            "Size": size,
            "Quantity": quantity,
            "MinStockLevel": min_stock,
            "Category": category
        }

        if storage.save_new_product(new_product):
            generate_labeled_qrcode(product_code=code)
            flash(f"Product '{name}' added successfully!", "success")
        else:
            flash(f"Product code already exists or failed to save.", "error")

        return redirect(url_for('inventory'))

    products = storage.load_products()
    return render_template('inventory.html', products=products)

# ---------- CUSTOMERS ----------
@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if request.method == 'POST':
        phone = request.form.get('phone')
        name = request.form.get('name')

        if customer_manager.add_customer(phone, name):
            flash(f"Customer '{name}' registered successfully!", "success")
        else:
            flash(f"Customer with phone {phone} already exists.", "error")

        return redirect(url_for('customers'))

    all_customers = customer_manager.load_customers()
    return render_template('customers.html', customers=all_customers)

# ---------- TRANSACTION ----------
@app.route('/transaction', methods=['POST'])
def record_transaction():
    phone = request.form.get('phone')
    amount = float(request.form.get('amount', 0))
    txn_type = request.form.get('txn_type')  # 'GAVE' or 'GOT'
    note = request.form.get('note', '')

    if customer_manager.add_transaction(phone, amount, txn_type, note):
        flash(f"Transaction recorded successfully!", "success")
    else:
        flash("Failed to record transaction.", "error")

    return redirect(url_for('customers'))

# ---------- QR CODE SERVING ----------
@app.route('/storage/qrcodes/<path:filename>')
def product_qr(filename):
    qr_directory = os.path.join(get_storage_path(), "ProductQRs")
    image_path = safe_join(qr_directory, filename)
    if not image_path or not os.path.isfile(image_path):
        abort(404)
    return send_file(BytesIO(load_bytes(image_path)), mimetype="image/png")

# ---------- PRODUCT API ----------
@app.route('/api/product/<product_code>', methods=['GET'])
def get_product(product_code):
    product = storage.get_product(product_code)
    if not product:
        return jsonify({"success": False, "message": "Product not found."}), 404
    response = dict(product)
    response["Code"] = product_code
    response["QRUrl"] = url_for('product_qr', filename=f"{product_code}.png")
    return jsonify({"success": True, "product": response})

@app.route('/api/product/<product_code>/update', methods=['POST'])
def update_product(product_code):
    # Convert to dict to allow mutation
    data = request.get_json(silent=True) or request.form.to_dict()

    # Handle custom size: if size_custom is provided, use it; else use 'Size' field
    if 'size_custom' in data and data['size_custom'].strip():
        data['Size'] = data['size_custom'].strip()
    if 'size_custom' in data:
        del data['size_custom']  # now safe because data is a dict

    allowed_fields = ["Name", "Price", "CostPrice", "Size", "Quantity", "MinStockLevel", "Category"]
    updates = {}
    for field in allowed_fields:
        if field in data and data[field] not in (None, ""):
            if field in ("Price", "CostPrice"):
                updates[field] = float(data[field])
            elif field in ("Quantity", "MinStockLevel"):
                updates[field] = int(data[field])
            else:
                updates[field] = data[field]

    success = storage.update_product(product_code, updates)
    if success:
        return jsonify({"success": True, "message": "Product updated successfully."})
    return jsonify({"success": False, "message": "Product not found or update failed."}), 404

@app.route('/api/product/<product_code>/delete', methods=['POST'])
def delete_product(product_code):
    success = storage.remove_product(product_code)
    if success:
        return jsonify({"success": True, "message": "Product removed successfully."})
    return jsonify({"success": False, "message": "Product not found."}), 404

@app.route('/api/products/low-stock', methods=['GET'])
def low_stock_products():
    return jsonify({"success": True, "products": storage.get_low_stock_products()})

# ---------- CUSTOMER API ----------
@app.route('/api/customer/<phone>', methods=['GET'])
def get_customer(phone):
    summary = customer_manager.get_customer_summary(phone)
    if not summary:
        return jsonify({"success": False, "message": "Customer not found."}), 404
    return jsonify({"success": True, "customer": summary})

@app.route('/api/customer/<phone>/update', methods=['POST'])
def update_customer_route(phone):
    data = request.get_json(silent=True) or request.form
    new_name = data.get('name') or data.get('Name')
    new_phone = data.get('phone') or data.get('Phone')

    success = customer_manager.update_customer(phone, new_name=new_name, new_phone=new_phone)
    if success:
        return jsonify({"success": True, "message": "Customer updated successfully."})
    return jsonify({"success": False, "message": "Customer not found or update failed."}), 404

@app.route('/api/customer/<phone>/delete', methods=['POST'])
def delete_customer_route(phone):
    success = customer_manager.remove_customer(phone)
    if success:
        return jsonify({"success": True, "message": "Customer removed successfully."})
    return jsonify({"success": False, "message": "Customer not found."}), 404

# ---------- SALES PAGE ----------
@app.route('/sales')
def sales_page():
    """Render the sales page with products and customers"""
    products = storage.load_products()
    customers = customer_manager.load_customers()
    return render_template('sales.html', products=products, customers=customers)

# ---------- SALES API ----------
@app.route('/api/sales', methods=['POST'])
def create_sale():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "JSON required"}), 400
    result = sales_manager.record_sale(
        items=data.get('items', []),
        payment_type=data.get('payment_type'),
        payment_split=data.get('payment_split'),
        customer_phone=data.get('customer_phone'),
        note=data.get('note', '')
    )
    return jsonify(result), 200 if result["success"] else 400

@app.route('/api/sales/history', methods=['GET'])
def sales_history():
    limit = request.args.get('limit', type=int)
    return jsonify({"success": True, "sales": sales_manager.get_sales_history(limit=limit)})

# ---------- REPORTS ----------
@app.route('/reports')
def reports():
    sales_data = sales_manager.get_sales_history()  # dict
    # Convert to list with sale_id
    sales_list = []
    for sid, sale in sales_data.items():
        sales_list.append({'id': sid, **sale})
    # Sort by timestamp descending (already sorted in get_sales_history)
    return render_template('reports.html', sales=sales_list)

# ---------- MAIN ----------
if __name__ == '__main__':
    host = os.environ.get("SHOPMANAGER_HOST", "127.0.0.1")
    port = int(os.environ.get("SHOPMANAGER_PORT", "5000"))
    if os.environ.get("SHOPMANAGER_DESKTOP") == "1":
        from waitress import serve
        serve(app, host=host, port=port, threads=8)
    else:
        import webbrowser
        webbrowser.open(f'http://{host}:{port}')
        app.run(
            host=host,
            port=port,
            debug=os.environ.get("SHOPMANAGER_DEBUG", "0") == "1",
            use_reloader=False,
        )