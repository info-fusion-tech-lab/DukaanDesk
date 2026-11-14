import os
import json
import uuid
from datetime import datetime

import tools.StorageManager as storage
import tools.CustomerManager as customer_manager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_PATH = os.path.join(BASE_DIR, "storage")
SALES_FILE = os.path.join(STORAGE_PATH, "SalesLog.json")

VALID_PAYMENT_TYPES = ["cash", "online", "udhari", "split"]

os.makedirs(STORAGE_PATH, exist_ok=True)


def load_sales():
    if not os.path.exists(SALES_FILE) or os.path.getsize(SALES_FILE) == 0:
        return {}
    with open(SALES_FILE, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}


def save_sales(data):
    with open(SALES_FILE, 'w') as file:
        json.dump(data, file, indent=4)


def record_sale(items, payment_type, payment_split=None, customer_phone=None, note=""):
    """
    Records one sale, which can contain one item (single sale) or many
    (bulk sale) - the logic is identical either way.

    items: list of dicts, each: {"ProductCode": str, "Quantity": int,
           "SellingPrice": float (optional - falls back to the stored Price)}
    payment_type: "cash" | "online" | "udhari" | "split"
    payment_split: only used when payment_type == "split", e.g.
           {"cash": 100, "online": 50, "udhari": 30}
    customer_phone: required when payment_type is "udhari", or when
           "split" includes a non-zero "udhari" portion.

    Returns a dict: {"success": bool, "message": str, "sale_id": str|None,
                      "total_amount": float, "low_stock_warnings": [..]}
    """
    payment_type = (payment_type or "").lower().strip()
    if payment_type not in VALID_PAYMENT_TYPES:
        return _fail(f"Invalid payment type '{payment_type}'. Must be one of {VALID_PAYMENT_TYPES}.")

    if not items:
        return _fail("No items provided for sale.")

    products = storage.load_products()

    # --- Pass 1: validate everything BEFORE touching any stock numbers ---
    # This avoids partially deducting stock if item #3 of 5 turns out invalid.
    resolved_items = []
    for raw in items:
        code = raw.get("ProductCode")
        qty = raw.get("Quantity")

        if not code or code not in products:
            return _fail(f"Product code '{code}' not found in inventory.")

        try:
            qty = int(qty)
        except (TypeError, ValueError):
            return _fail(f"Invalid quantity for product '{code}'.")

        if qty <= 0:
            return _fail(f"Quantity must be greater than 0 for product '{code}'.")

        product = products[code]
        available = product.get("Quantity", 0)
        if available < qty:
            return _fail(
                f"Insufficient stock for '{product.get('Name', code)}'. "
                f"Requested {qty}, only {available} available."
            )

        selling_price = raw.get("SellingPrice")
        if selling_price in (None, ""):
            selling_price = product.get("Price", 0)
        else:
            selling_price = float(selling_price)

        resolved_items.append({
            "ProductCode": code,
            "ProductName": product.get("Name", ""),
            "Quantity": qty,
            "SellingPrice": selling_price,
            "LineTotal": round(selling_price * qty, 2)
        })

    total_amount = round(sum(i["LineTotal"] for i in resolved_items), 2)

    # --- Validate payment breakdown ---
    udhari_amount = 0.0
    if payment_type == "udhari":
        udhari_amount = total_amount
        if not customer_phone:
            return _fail("A customer must be selected for 'udhari' (credit) sales.")

    elif payment_type == "split":
        if not payment_split or not isinstance(payment_split, dict):
            return _fail("Split payment requires a payment_split breakdown.")

        cash_amt = float(payment_split.get("cash", 0) or 0)
        online_amt = float(payment_split.get("online", 0) or 0)
        udhari_amount = float(payment_split.get("udhari", 0) or 0)
        split_total = round(cash_amt + online_amt + udhari_amount, 2)

        if abs(split_total - total_amount) > 0.01:
            return _fail(
                f"Split amounts (₹{split_total}) don't add up to the total sale (₹{total_amount})."
            )

        if udhari_amount > 0 and not customer_phone:
            return _fail("A customer must be selected when part of a split sale is 'udhari' (credit).")

    if customer_phone:
        summary = customer_manager.get_customer_summary(customer_phone)
        if not summary:
            return _fail(f"Customer with phone '{customer_phone}' not found.")

    # --- Pass 2: everything validated, now actually deduct stock ---
    low_stock_warnings = []
    for item in resolved_items:
        storage.update_quantity(item["ProductCode"], item["Quantity"], is_sale=True)

    refreshed_products = storage.load_products()
    for item in resolved_items:
        p = refreshed_products.get(item["ProductCode"], {})
        if p.get("Quantity", 0) <= p.get("MinStockLevel", 5):
            low_stock_warnings.append(
                f"'{item['ProductName']}' is low on stock ({p.get('Quantity', 0)} left)."
            )

    # --- Record the udhari/credit portion against the customer's ledger ---
    if customer_phone and udhari_amount > 0:
        credit_note = note or f"Sale: {', '.join(i['ProductName'] for i in resolved_items)}"
        customer_manager.add_transaction(customer_phone, udhari_amount, "GAVE", credit_note)

    # --- Save the sale record itself ---
    sale_id = uuid.uuid4().hex[:10].upper()
    sales = load_sales()
    sales[sale_id] = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Items": resolved_items,
        "PaymentType": payment_type,
        "PaymentSplit": payment_split if payment_type == "split" else None,
        "CustomerPhone": customer_phone,
        "TotalAmount": total_amount,
        "Note": note
    }
    save_sales(sales)

    return {
        "success": True,
        "message": "Sale recorded successfully.",
        "sale_id": sale_id,
        "total_amount": total_amount,
        "low_stock_warnings": low_stock_warnings
    }


def get_sales_history(limit=None):
    sales = load_sales()
    # Most recent first
    ordered = dict(sorted(sales.items(), key=lambda kv: kv[1]["Timestamp"], reverse=True))
    if limit:
        ordered = dict(list(ordered.items())[:limit])
    return ordered


def _fail(message):
    print(f"Sale failed: {message}")
    return {
        "success": False,
        "message": message,
        "sale_id": None,
        "total_amount": 0,
        "low_stock_warnings": []
    }
