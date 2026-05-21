import os
import json
from datetime import date

LOANS_FILE = "loans.json"

def load_loans():
    if not os.path.exists(LOANS_FILE):
        return []
    try:
        with open(LOANS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content: 
                return []
            return json.loads(content)
    except (json.JSONDecodeError, ValueError, OSError):
        return []

def save_loans(loans):
    with open(LOANS_FILE, "w", encoding="utf-8") as f:
        json.dump(loans, f, indent=4)

def next_loan_id(loans):
    if not loans:
        return 1
    return max(loan["loan_id"] for loan in loans) + 1

def get_active_loans_for_member(member_id):
    loans = load_loans()
    return [loan for loan in loans if loan["member_id"] == member_id and loan.get("return_date") is None]

def get_loan_by_book_isbn(isbn):
    loans = load_loans()
    for loan in loans:
        if loan["book_isbn"] == isbn and loan.get("return_date") is None:
            return loan
    return None