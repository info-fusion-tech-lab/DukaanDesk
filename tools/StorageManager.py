import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_PATH = os.path.join(BASE_DIR, "storage")
JSON_FILE = os.path.join(STORAGE_PATH, "ProductList.json")

os.makedirs(STORAGE_PATH, exist_ok=True)

def load_products():
    if not os.path.exists(JSON_FILE) or os.path.getsize(JSON_FILE) == 0:
        return {}
    with open(JSON_FILE, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}

def get_product(product_code):
    products = load_products()
    return products.get(product_code, None)

def is_product(product_code):
    products = load_products()
    
    if product_code not in products:
        return False
    else:
        return True

def save_new_product(product):
    existing_products = load_products()
    product_code = product.get("Code")
    
    if not product_code:
        print("Error: Product missing 'Code' primary key.")
        return False

    if product_code in existing_products:
        print(f"Product with Code '{product_code}' already exists.")
        return False  
        
    product_details = product.copy()
    del product_details["Code"]
    
    existing_products[product_code] = product_details
    
    with open(JSON_FILE, 'w') as file:
        json.dump(existing_products, file, indent=4)
        
    print(f"Product '{product_details.get('Name')}' saved successfully.")
    return True

def update_quantity(product_code, net_change, is_sale=True):
    existing_products = load_products()
    
    if product_code not in existing_products:
        print(f"Product '{product_code}' not found.")
        return False
        
    current_quantity = existing_products[product_code]["Quantity"]

    if is_sale:
        if current_quantity < net_change:
            print(f"Error: Insufficient stock. Requested: {net_change}, Available: {current_quantity}.")
            return False
        existing_products[product_code]["Quantity"] -= net_change
    else:
        existing_products[product_code]["Quantity"] += net_change
    
    with open(JSON_FILE, 'w') as file:
        json.dump(existing_products, file, indent=4)
        
    print(f"Quantity updated. New balance for {product_code}: {existing_products[product_code]['Quantity']}")
    return True

def update_product(product_code, updates):
    """
    Edits an existing product's details. The Code itself (the dict key)
    can never be changed here - only fields inside it (Name, Price,
    CostPrice, Size, Quantity, MinStockLevel, Category).
    'updates' is a dict of only the fields that should change.
    """
    existing_products = load_products()

    if product_code not in existing_products:
        print(f"Product '{product_code}' not found.")
        return False

    # Never allow the Code field to be edited through this function.
    safe_updates = {k: v for k, v in updates.items() if k != "Code"}
    existing_products[product_code].update(safe_updates)

    with open(JSON_FILE, 'w') as file:
        json.dump(existing_products, file, indent=4)

    print(f"Product '{product_code}' updated successfully.")
    return True

def get_low_stock_products():
    """Returns {code: product} for every product at or below its MinStockLevel."""
    products = load_products()
    return {
        code: p for code, p in products.items()
        if p.get('Quantity', 0) <= p.get('MinStockLevel', 5)
    }

def remove_product(product_code):
    existing_products = load_products()
    
    if product_code not in existing_products:
        print(f"Product '{product_code}' does not exist.")
        return False
    
    del existing_products[product_code]
    
    with open(JSON_FILE, 'w') as file:
        json.dump(existing_products, file, indent=4)
    
    print(f"Product '{product_code}' removed successfully.")
    return True
