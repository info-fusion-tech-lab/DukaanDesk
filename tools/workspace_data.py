from datetime import datetime
import math
import os
import re
from collections.abc import Mapping

from tools.encrypted_json import load_json, save_json
from tools.paths import storage_file


_DATA_FILENAME = "DukaanDeskWorkspace.json"
_SETTINGS_FILENAME = "DukaanDeskSettings.json"
_COLLECTIONS = ("products", "customers", "suppliers", "staff", "sales")


def _number(value, default=0):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _iso_date(value):
    if not value:
        return datetime.now().astimezone().isoformat()
    return str(value).replace(" ", "T", 1)


def _migrate_legacy_data():
    from tools import CustomerManager, SalesManager, StorageManager

    products = StorageManager.load_products()
    customers = CustomerManager.load_customers()
    sales = SalesManager.load_sales()
    customer_ids = {}

    migrated_customers = []
    for phone, record in customers.items():
        customer_id = "customer_" + str(phone)
        customer_ids[str(phone)] = customer_id
        migrated_customers.append(
            {
                "id": customer_id,
                "name": record.get("Name", ""),
                "phone": str(record.get("Phone", phone)),
                "balance": _number(record.get("Balance")),
                "transactions": [
                    {
                        "id": "transaction_" + str(index),
                        "date": _iso_date(transaction.get("Timestamp")),
                        "type": transaction.get("Type", "GAVE"),
                        "amount": _number(transaction.get("Amount")),
                        "note": transaction.get("Note", ""),
                        "balance": _number(transaction.get("NewBalance")),
                    }
                    for index, transaction in enumerate(record.get("Transactions", []))
                ],
            }
        )

    migrated_products = [
        {
            "id": str(code),
            "code": str(code),
            "name": record.get("Name", ""),
            "cost": _number(record.get("CostPrice", record.get("Cost", 0))),
            "price": _number(record.get("Price")),
            "quantity": int(_number(record.get("Quantity"))),
            "minimum": int(_number(record.get("MinStockLevel", 5))),
            "category": record.get("Category", "General"),
        }
        for code, record in products.items()
    ]

    migrated_sales = []
    for sale_id, record in sales.items():
        payment_type = record.get("PaymentType", "cash")
        split = record.get("PaymentSplit") or {}
        total = _number(record.get("TotalAmount"))
        phone = str(record.get("CustomerPhone") or "")
        cash = _number(split.get("cash")) if payment_type == "split" else 0
        online = _number(split.get("online")) if payment_type == "split" else 0
        credit = _number(split.get("udhari")) if payment_type == "split" else 0
        if payment_type == "cash":
            cash = total
        elif payment_type == "online":
            online = total
        elif payment_type == "udhari":
            credit = total

        items = record.get("Items", [])
        migrated_sales.append(
            {
                "id": str(sale_id),
                "date": _iso_date(record.get("Timestamp")),
                "customerId": customer_ids.get(phone),
                "customerName": next(
                    (
                        customer["name"]
                        for customer in migrated_customers
                        if customer["phone"] == phone
                    ),
                    "Walk-in",
                ),
                "phone": phone,
                "items": [
                    {
                        "productId": str(item.get("ProductCode", "")),
                        "code": str(item.get("ProductCode", "")),
                        "name": item.get("ProductName", ""),
                        "qty": int(_number(item.get("Quantity"))),
                        "price": _number(item.get("SellingPrice")),
                    }
                    for item in items
                ],
                "total": total,
                "cash": cash,
                "online": online,
                "credit": credit,
                "note": record.get("Note", ""),
                "voided": False,
            }
        )

    return {
        "products": migrated_products,
        "customers": migrated_customers,
        "suppliers": [],
        "staff": [],
        "sales": migrated_sales,
    }


def _validate_workspace(data):
    if not isinstance(data, dict):
        raise ValueError("Workspace data must be an object.")
    normalized = {}
    for collection in _COLLECTIONS:
        records = data.get(collection)
        if not isinstance(records, list):
            raise ValueError(f"{collection} must be a list.")
        ids = set()
        for record in records:
            if not isinstance(record, Mapping):
                raise ValueError(f"Every {collection} entry must be an object.")
            record_id = record.get("id")
            if not isinstance(record_id, str) or not record_id.strip():
                raise ValueError(f"Every {collection} entry needs an ID.")
            if record_id in ids:
                raise ValueError(f"Duplicate ID in {collection}.")
            ids.add(record_id)
        if collection == "products":
            records = [dict(record) if isinstance(record, Mapping) else record for record in records]
        normalized[collection] = records

    def require_text(record, field, location, allow_empty=False):
        value = record.get(field)
        if not isinstance(value, str) or (not allow_empty and not value.strip()):
            raise ValueError(f"{location}.{field} must be text.")

    def require_number(record, field, location, integer=False, allow_negative=False):
        value = record.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or (not allow_negative and value < 0)
            or (integer and not isinstance(value, int))
        ):
            expected = "whole number" if integer else "number"
            if not allow_negative:
                expected = "non-negative " + expected
            raise ValueError(f"{location}.{field} must be {expected}.")

    def require_transactions(record, location, allowed_types, purchase_items=False):
        transactions = record.get("transactions")
        if not isinstance(transactions, list):
            raise ValueError(f"{location}.transactions must be a list.")
        for index, transaction in enumerate(transactions):
            transaction_location = f"{location}.transactions[{index}]"
            if not isinstance(transaction, Mapping):
                raise ValueError(f"{transaction_location} must be an object.")
            require_text(transaction, "id", transaction_location)
            require_text(transaction, "date", transaction_location)
            transaction_type = transaction.get("type")
            if not isinstance(transaction_type, str) or transaction_type not in allowed_types:
                raise ValueError(f"{transaction_location}.type is invalid.")
            require_number(transaction, "amount", transaction_location)
            require_text(transaction, "note", transaction_location, allow_empty=True)
            if purchase_items and transaction["type"] == "PURCHASE":
                items = transaction.get("items")
                if not isinstance(items, list):
                    raise ValueError(f"{transaction_location}.items must be a list.")
                for item_index, item in enumerate(items):
                    item_location = f"{transaction_location}.items[{item_index}]"
                    if not isinstance(item, Mapping):
                        raise ValueError(f"{item_location} must be an object.")
                    require_text(item, "name", item_location)
                    require_number(item, "qty", item_location, integer=True)
                    require_number(item, "cost", item_location)

    product_codes = set()
    for index, product in enumerate(normalized["products"]):
        location = f"products[{index}]"
        product.setdefault("cost", 0)
        for field in ("code", "name", "category"):
            require_text(product, field, location, allow_empty=field == "category")
        require_number(product, "cost", location)
        require_number(product, "price", location)
        require_number(product, "quantity", location, integer=True)
        require_number(product, "minimum", location, integer=True)
        if product["code"] in product_codes:
            raise ValueError("Product codes must be unique.")
        product_codes.add(product["code"])

    customer_phones = set()
    for index, customer in enumerate(normalized["customers"]):
        location = f"customers[{index}]"
        require_text(customer, "name", location)
        require_text(customer, "phone", location)
        require_number(customer, "balance", location, allow_negative=True)
        if customer["phone"] in customer_phones:
            raise ValueError("Customer phone numbers must be unique.")
        customer_phones.add(customer["phone"])
        require_transactions(customer, location, {"GAVE", "GOT"})
        for transaction in customer["transactions"]:
            require_number(transaction, "balance", location, allow_negative=True)

    for index, supplier in enumerate(normalized["suppliers"]):
        location = f"suppliers[{index}]"
        require_text(supplier, "name", location)
        require_text(supplier, "phone", location, allow_empty=True)
        require_transactions(
            supplier, location, {"PURCHASE", "PAYMENT"}, purchase_items=True
        )

    for index, staff in enumerate(normalized["staff"]):
        location = f"staff[{index}]"
        for field in ("name", "phone", "role", "joinDate"):
            require_text(staff, field, location, allow_empty=field == "phone")
        require_number(staff, "salary", location)
        attendance = staff.get("attendance")
        if not isinstance(attendance, Mapping) or any(
            not isinstance(value, str) or value not in {"present", "absent", "half"}
            for value in attendance.values()
        ):
            raise ValueError(f"{location}.attendance is invalid.")

    for index, sale in enumerate(normalized["sales"]):
        location = f"sales[{index}]"
        for field in ("date", "customerName", "phone", "note"):
            require_text(sale, field, location, allow_empty=field in {"phone", "note"})
        if sale.get("customerId") is not None and not isinstance(sale["customerId"], str):
            raise ValueError(f"{location}.customerId is invalid.")
        for field in ("total", "cash", "online", "credit"):
            require_number(sale, field, location)
        if not isinstance(sale.get("voided"), bool):
            raise ValueError(f"{location}.voided must be a boolean.")
        items = sale.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"{location}.items must contain at least one product.")
        for item_index, item in enumerate(items):
            item_location = f"{location}.items[{item_index}]"
            if not isinstance(item, Mapping):
                raise ValueError(f"{item_location} must be an object.")
            for field in ("productId", "code", "name"):
                require_text(item, field, item_location)
            require_number(item, "qty", item_location, integer=True)
            if item["qty"] < 1:
                raise ValueError(f"{item_location}.qty must be at least one.")
            require_number(item, "price", item_location)
            if "cost" in item:
                require_number(item, "cost", item_location)

    return normalized


def load_workspace():
    path = storage_file(_DATA_FILENAME)
    data = load_json(path, None)
    if not os.path.exists(path):
        data = _migrate_legacy_data()
        data = _validate_workspace(data)
        save_json(path, data)
        return data
    return _validate_workspace(data)


def save_workspace(data):
    validated = _validate_workspace(data)
    save_json(storage_file(_DATA_FILENAME), validated)
    return validated


def default_settings(shop_name):
    return {
        "theme": "system",
        "accent": "#4f46e5",
        "layout": "expanded",
        "density": "comfortable",
        "shopName": shop_name,
        "currency": "₹",
    }


def load_settings(shop_name):
    settings = load_json(storage_file(_SETTINGS_FILENAME), None)
    if settings is None:
        return default_settings(shop_name)
    if not isinstance(settings, dict):
        raise RuntimeError("The saved appearance settings have an invalid format.")
    return {**default_settings(shop_name), **settings}


def save_settings(settings, shop_name):
    if not isinstance(settings, dict):
        raise ValueError("Appearance settings must be an object.")
    validated = {**default_settings(shop_name), **settings}
    if not isinstance(validated["theme"], str) or validated["theme"] not in {
        "system",
        "light",
        "dark",
    }:
        raise ValueError("The selected theme is invalid.")
    if not isinstance(validated["accent"], str) or not re.fullmatch(
        r"#[0-9a-fA-F]{6}", validated["accent"]
    ):
        raise ValueError("The accent color is invalid.")
    if not isinstance(validated["layout"], str) or validated["layout"] not in {
        "expanded",
        "compact",
        "topnav",
    }:
        raise ValueError("The navigation layout is invalid.")
    if not isinstance(validated["density"], str) or validated["density"] not in {
        "comfortable",
        "compact",
    }:
        raise ValueError("The density setting is invalid.")
    if (
        not isinstance(validated["shopName"], str)
        or len(validated["shopName"]) > 80
        or not isinstance(validated["currency"], str)
        or not 1 <= len(validated["currency"]) <= 3
    ):
        raise ValueError("The shop name or currency setting is invalid.")
    save_json(storage_file(_SETTINGS_FILENAME), validated)
    return validated
