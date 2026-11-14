import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_PATH = os.path.join(BASE_DIR, "storage")
CUSTOMER_FILE = os.path.join(STORAGE_PATH, "CustomerList.json")

os.makedirs(STORAGE_PATH, exist_ok=True)

# Sample Schema structure for context:
# {
#     "9876543210": {
#         "Name": "John Doe",
#         "Phone": "9876543210",
#         "Balance": 150.0,  # Positive (+) = Customer owes shop | Negative (-) = Shop owes customer
#         "Transactions": [
#             {
#                 "Timestamp": "2026-08-02 10:30:00",
#                 "Type": "GAVE", # Credit / Sale given to customer
#                 "Amount": 200.0,
#                 "Note": "Bought goods on credit",
#                 "NewBalance": 200.0
#             },
#             {
#                 "Timestamp": "2026-08-02 11:00:00",
#                 "Type": "GOT",  # Payment received from customer
#                 "Amount": 50.0,
#                 "Note": "Partial cash payment",
#                 "NewBalance": 150.0
#             }
#         ]
#     }
# }

def load_customers():
    """Loads all customer account data from JSON."""
    if not os.path.exists(CUSTOMER_FILE) or os.path.getsize(CUSTOMER_FILE) == 0:
        return {}
    with open(CUSTOMER_FILE, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}

def save_customers(data):
    """Saves updated customer ledger data back to JSON."""
    with open(CUSTOMER_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def add_customer(phone, name):
    """Creates a new customer account using their phone number as the key."""
    customers = load_customers()
    phone_str = str(phone).strip()
    
    if phone_str in customers:
        print(f"Customer with phone number {phone_str} already exists.")
        return False
        
    customers[phone_str] = {
        "Name": name,
        "Phone": phone_str,
        "Balance": 0.0,
        "Transactions": []
    }
    
    save_customers(customers)
    print(f"Customer '{name}' added successfully.")
    return True

def add_transaction(phone, amount, txn_type, note=""):
    """
    Records a Khatabook style transaction.
    - txn_type = 'GAVE' (You gave credit/goods -> Customer balance increases)
    - txn_type = 'GOT'  (You received money -> Customer balance decreases)
    """
    customers = load_customers()
    phone_str = str(phone).strip()
    
    if phone_str not in customers:
        print(f"Error: Customer with phone '{phone_str}' not found.")
        return False
    
    txn_type = txn_type.upper()
    if txn_type not in ["GAVE", "GOT"]:
        print("Error: Invalid transaction type. Use 'GAVE' or 'GOT'.")
        return False
        
    amount = float(amount)
    current_balance = customers[phone_str]["Balance"]
    
    if txn_type == "GAVE":
        new_balance = current_balance + amount
    else:  # GOT
        new_balance = current_balance - amount
        
    transaction_record = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Type": txn_type,
        "Amount": amount,
        "Note": note,
        "NewBalance": new_balance
    }
    
    customers[phone_str]["Balance"] = new_balance
    customers[phone_str]["Transactions"].append(transaction_record)
    
    save_customers(customers)
    
    action_text = "Gave Credit" if txn_type == "GAVE" else "Received Payment"
    print(f"Success! {action_text} of {amount} for {customers[phone_str]['Name']}. Updated Balance: {new_balance}")
    return True

def update_customer(phone, new_name=None, new_phone=None):
    """
    Edits a customer's Name and/or Phone number.
    Phone is the dict key, so renaming it means moving the record to a
    new key while keeping the Balance and full Transaction history intact.
    """
    customers = load_customers()
    phone_str = str(phone).strip()

    if phone_str not in customers:
        print(f"Error: Customer with phone '{phone_str}' not found.")
        return False

    record = customers[phone_str]

    if new_name:
        record["Name"] = new_name

    if new_phone and str(new_phone).strip() != phone_str:
        new_phone_str = str(new_phone).strip()
        if new_phone_str in customers:
            print(f"Error: Phone number '{new_phone_str}' is already in use.")
            return False
        record["Phone"] = new_phone_str
        del customers[phone_str]
        customers[new_phone_str] = record
    else:
        customers[phone_str] = record

    save_customers(customers)
    print(f"Customer '{record['Name']}' updated successfully.")
    return True

def remove_customer(phone):
    """Deletes a customer account entirely, including their transaction history."""
    customers = load_customers()
    phone_str = str(phone).strip()

    if phone_str not in customers:
        print(f"Customer with phone '{phone_str}' does not exist.")
        return False

    del customers[phone_str]
    save_customers(customers)
    print(f"Customer '{phone_str}' removed successfully.")
    return True

def get_customer_summary(phone):
    """Retrieves account balance and complete transaction history for a customer."""
    customers = load_customers()
    phone_str = str(phone).strip()
    return customers.get(phone_str, None)

def get_total_receivables():
    """Calculates total money pending to be collected from all customers."""
    customers = load_customers()
    total_due = sum(c["Balance"] for c in customers.values() if c["Balance"] > 0)
    return total_due
