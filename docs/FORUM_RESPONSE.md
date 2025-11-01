# Response to: "API for Accounting Modules" (2014 Forum Question)

**Original Question:** [ERPNext Developer Forum - May 2014](https://discuss.frappe.io/t/api-for-accounting-modules/1390)

> *"Is there any API for integration to the accounting modules? From the samples I see that there is API for creating the documents such as purchase order but how about the API to post entries to the accounting module?*
>
> *We are looking at integrating another system that already has some of the features, such as purchase order, is there any 'convenient' function in the API that allows us provide the details and it will post the necessary entries to the various accounts in the accounting module without us having to create a duplicate document in ERPNext or having to manually post the necessary entries into the different ledgers and accounts?"*

---

## Answer (2024 - Updated & Comprehensive)

**Yes!** ERPNext provides comprehensive REST APIs for direct accounting operations. You can post entries to GL accounts without creating duplicate documents in ERPNext.

### Quick Answer

Use the **Journal Entry** API to post directly to GL accounts:

```bash
POST https://your-instance.erpnext.com/api/resource/Journal Entry
```

```json
{
    "doctype": "Journal Entry",
    "posting_date": "2024-11-01",
    "company": "Your Company",
    "user_remark": "From External PO System - PO#12345",
    "accounts": [
        {
            "account": "Inventory - YC",
            "debit_in_account_currency": 10000,
            "credit_in_account_currency": 0
        },
        {
            "account": "Accounts Payable - YC",
            "debit_in_account_currency": 0,
            "credit_in_account_currency": 10000
        }
    ]
}
```

**Headers:**
```json
{
    "Authorization": "token api_key:api_secret",
    "Content-Type": "application/json"
}
```

---

## Detailed Solutions

### Solution 1: Direct GL Posting (No Duplicate Documents)

This is exactly what you're asking for - post accounting entries without creating Purchase Orders, Invoices, etc. in ERPNext.

**Python Example:**

```python
import requests

# Configuration
BASE_URL = "https://your-instance.erpnext.com"
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"

def create_accounting_entry(posting_date, description, accounts):
    """
    Post entries directly to GL without creating source documents

    Args:
        posting_date: Date of posting (YYYY-MM-DD)
        description: Transaction description
        accounts: List of account entries (debit/credit)
    """
    url = f"{BASE_URL}/api/resource/Journal Entry"

    payload = {
        "doctype": "Journal Entry",
        "posting_date": posting_date,
        "company": "Your Company",
        "user_remark": description,
        "accounts": accounts
    }

    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()

# Example: Record a purchase from your external PO system
result = create_accounting_entry(
    posting_date="2024-11-01",
    description="External PO#12345 - Supplier ABC - 100 units Widget",
    accounts=[
        {
            "account": "Inventory - YC",
            "debit_in_account_currency": 10000,
            "credit_in_account_currency": 0
        },
        {
            "account": "Accounts Payable - Supplier ABC - YC",
            "party_type": "Supplier",
            "party": "Supplier ABC",
            "debit_in_account_currency": 0,
            "credit_in_account_currency": 10000
        }
    ]
)

print(f"Created Journal Entry: {result['data']['name']}")

# Submit the entry to post to GL
submit_url = f"{BASE_URL}/api/resource/Journal Entry/{result['data']['name']}"
requests.put(
    submit_url,
    json={"docstatus": 1},  # 1 = Submitted
    headers=headers
)
```

### Solution 2: Multi-Currency Support

If your external system handles foreign currency transactions:

```python
# Revenue in USD, operating in INR base currency
create_accounting_entry(
    posting_date="2024-11-01",
    description="External Invoice INV-2024-001 - Client XYZ",
    accounts=[
        {
            "account": "Accounts Receivable - USD - YC",
            "party_type": "Customer",
            "party": "Client XYZ",
            "debit_in_account_currency": 5000,  # $5000
            "credit_in_account_currency": 0,
            "account_currency": "USD",
            "exchange_rate": 83.50  # 1 USD = 83.50 INR
        },
        {
            "account": "Sales - YC",
            "debit_in_account_currency": 0,
            "credit_in_account_currency": 5000,  # $5000
            "account_currency": "USD",
            "exchange_rate": 83.50
        }
    ]
)

# ERPNext automatically calculates base currency amounts
# $5000 × 83.50 = ₹417,500 in GL
```

### Solution 3: Batch Processing

If you need to sync multiple transactions:

```python
def sync_daily_transactions(transactions):
    """
    Sync multiple transactions from external system

    Args:
        transactions: List of transaction dicts from your system
    """
    results = []

    for txn in transactions:
        # Map your system's accounts to ERPNext accounts
        accounts = map_external_to_erpnext_accounts(txn)

        # Validate
        if sum(a.get('debit_in_account_currency', 0) for a in accounts) != \
           sum(a.get('credit_in_account_currency', 0) for a in accounts):
            print(f"Skipping unbalanced transaction: {txn['id']}")
            continue

        # Create entry
        try:
            result = create_accounting_entry(
                posting_date=txn['date'],
                description=f"External Ref: {txn['id']} - {txn['description']}",
                accounts=accounts
            )
            results.append(result)
        except Exception as e:
            print(f"Error processing {txn['id']}: {e}")

    return results
```

---

## Available Accounting APIs

### 1. Chart of Accounts

**Get Accounts:**
```bash
GET /api/resource/Account?fields=["name","account_name","account_type"]&filters=[["company","=","Your Company"]]
```

**Create Account:**
```bash
POST /api/resource/Account
```
```json
{
    "account_name": "New Account",
    "parent_account": "Assets - YC",
    "account_type": "Bank",
    "company": "Your Company"
}
```

### 2. Journal Entries

**Create Entry:**
```bash
POST /api/resource/Journal Entry
```

**Get Entries:**
```bash
GET /api/resource/Journal Entry?filters=[["posting_date",">=","2024-01-01"]]
```

**Submit Entry (Post to GL):**
```bash
PUT /api/resource/Journal Entry/{entry_name}
```
```json
{
    "docstatus": 1
}
```

### 3. General Ledger

**Query GL Entries:**
```bash
GET /api/resource/GL Entry?filters=[["posting_date","between",["2024-01-01","2024-12-31"]]]
```

### 4. Payment Entries

**Record Payment:**
```bash
POST /api/resource/Payment Entry
```
```json
{
    "payment_type": "Receive",
    "party_type": "Customer",
    "party": "Client ABC",
    "paid_amount": 10000,
    ...
}
```

---

## Key Benefits of This Approach

### ✅ Advantages

1. **No Duplicate Data**
   - External system remains source of truth
   - ERPNext used only for accounting/GL
   - Single data entry point

2. **Flexible Integration**
   - Any system can integrate (REST API)
   - Language agnostic (Python, JavaScript, Java, etc.)
   - Standard HTTP protocol

3. **Full Accounting Features**
   - Multi-currency support
   - Double-entry enforcement
   - Automatic GL posting
   - Financial reports (P&L, Balance Sheet, etc.)

4. **Audit Trail**
   - All entries logged
   - User tracking
   - Modification history
   - External references maintained

### ⚠️ Considerations

1. **Reference Management**
   - Store ERPNext document IDs in your system
   - Include external IDs in `user_remark` field
   - Implement reconciliation checks

2. **Account Mapping**
   - Map your system's accounts to ERPNext Chart of Accounts
   - Create accounts in ERPNext first
   - Maintain mapping table

3. **Validation**
   - Entries must balance (debits = credits)
   - Accounts must exist
   - Dates must be valid
   - Closed periods cannot be modified

4. **Error Handling**
   - Network failures
   - Validation errors
   - Duplicate entries
   - Implement retry logic

---

## Complete Integration Example

Here's a complete example integrating an external PO system:

```python
class ERPNextAccountingIntegration:
    """
    Integration layer for posting entries from external system to ERPNext
    """

    def __init__(self, base_url, api_key, api_secret, company):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"token {api_key}:{api_secret}",
            "Content-Type": "application/json"
        }
        self.company = company

    def post_purchase_order(self, po_data):
        """
        Post accounting entries for a purchase order from external system

        Args:
            po_data: {
                'po_number': 'PO-12345',
                'date': '2024-11-01',
                'supplier': 'Supplier ABC',
                'amount': 10000,
                'items': [...]
            }
        """
        # Build journal entry
        accounts = [
            {
                "account": f"Inventory - {self.company}",
                "debit_in_account_currency": po_data['amount'],
                "credit_in_account_currency": 0,
                "cost_center": f"Main - {self.company}"
            },
            {
                "account": f"Creditors - {self.company}",
                "party_type": "Supplier",
                "party": po_data['supplier'],
                "debit_in_account_currency": 0,
                "credit_in_account_currency": po_data['amount']
            }
        ]

        # Create journal entry
        payload = {
            "doctype": "Journal Entry",
            "posting_date": po_data['date'],
            "company": self.company,
            "user_remark": f"External PO: {po_data['po_number']}",
            "accounts": accounts
        }

        # Post to ERPNext
        response = requests.post(
            f"{self.base_url}/api/resource/Journal Entry",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()

        entry = response.json()['data']

        # Submit to post to GL
        submit_response = requests.put(
            f"{self.base_url}/api/resource/Journal Entry/{entry['name']}",
            json={"docstatus": 1},
            headers=self.headers
        )
        submit_response.raise_for_status()

        return entry['name']

    def post_sales_invoice(self, invoice_data):
        """Post sales invoice from external system"""
        # Similar pattern...
        pass

    def reconcile_accounts(self, account, from_date, to_date):
        """Get GL entries for reconciliation"""
        response = requests.get(
            f"{self.base_url}/api/resource/GL Entry",
            params={
                "fields": '["posting_date","account","debit","credit","voucher_no"]',
                "filters": f'[["account","=","{account}"],["posting_date",">=","{from_date}"],["posting_date","<=","{to_date}"]]'
            },
            headers=self.headers
        )
        return response.json()['data']

# Usage
integration = ERPNextAccountingIntegration(
    base_url="https://your-instance.erpnext.com",
    api_key="your_key",
    api_secret="your_secret",
    company="YC"
)

# Post a purchase order
entry_id = integration.post_purchase_order({
    'po_number': 'PO-12345',
    'date': '2024-11-01',
    'supplier': 'Supplier ABC',
    'amount': 10000
})

print(f"Posted to ERPNext: {entry_id}")
```

---

## Reference Implementation

For a complete, production-ready implementation, see this open-source guide:

**GitHub:** [github.com/senguttuvang/erpnext-accounting-integration](https://github.com/senguttuvang/erpnext-accounting-integration)

**Features:**
- Complete Python client library
- Multi-currency support
- Batch processing
- Error handling & retry logic
- Migration tools (from other accounting systems)
- Financial reporting
- Comprehensive documentation

**Quick Start:**
```bash
git clone https://github.com/senguttuvang/erpnext-accounting-integration.git
cd erpnext-accounting-integration
pip install -r requirements.txt

# Configure
cp examples/config_template.py config.py
# Edit config.py

# Run examples
python src/examples/basic_operations.py
```

---

## Documentation Resources

- **Official REST API Docs:** https://frappeframework.com/docs/user/en/api/rest
- **ERPNext Accounting Docs:** https://docs.erpnext.com/docs/user/manual/en/accounts
- **This Integration Guide:** [Complete architectural guide and patterns](../ARCHITECTURE.md)
- **API Deep-Dive:** [Detailed accounting API reference](API_GUIDE.md)

---

## Summary

**Yes, you can post accounting entries via API without creating duplicate documents!**

**Key Points:**
1. ✅ Use **Journal Entry** API for direct GL posting
2. ✅ No need to create PO, Invoices in ERPNext if you have them elsewhere
3. ✅ Supports multi-currency, parties (customers/suppliers), cost centers
4. ✅ Full double-entry accounting enforced
5. ✅ All financial reports available
6. ✅ Complete audit trail maintained

**The pattern is:**
```python
External System → Build Journal Entry → Validate → POST to ERPNext → Submit → GL Updated
```

**Example use cases successfully implemented:**
- E-commerce platform → Daily sales to ERPNext
- External PO system → Purchase accounting to ERPNext
- Payment processor → Payment reconciliation to ERPNext
- Time tracking system → Payroll entries to ERPNext
- Multi-currency platform → Forex accounting to ERPNext

---

**Hope this helps! The API is much more mature now (2024) than in 2014, and can definitely handle your use case.** 🎉

For more details and working code, check out the [complete integration guide](https://github.com/senguttuvang/erpnext-accounting-integration).
