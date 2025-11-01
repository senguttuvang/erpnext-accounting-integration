"""
Basic ERPNext Accounting Operations Examples
Demonstrates common accounting workflows via REST API

Use Cases Covered:
1. Chart of Accounts setup
2. Opening balance entries
3. Revenue recognition (single & multi-currency)
4. Expense recording
5. Cash receipts with forex
6. Retrieving and analyzing transactions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from erpnext_client import ERPNextClient, ERPNextConfig, validate_journal_entry
from datetime import datetime
import json


# ============================================================
# CONFIGURATION
# Replace with your actual ERPNext instance details
# ============================================================

config = ERPNextConfig(
    base_url="https://your-instance.erpnext.com",
    api_key="your_api_key_here",
    api_secret="your_api_secret_here"
)

client = ERPNextClient(config)

# Company configuration
COMPANY = "Demo Company"
COMPANY_SUFFIX = "DC"  # Used in account names like "Cash - DC"


# ============================================================
# EXAMPLE 1: Setup Chart of Accounts
# ============================================================

def example_setup_chart_of_accounts():
    """
    Create account structure for an IT services business

    This example creates a typical Chart of Accounts for:
    - IT consulting/services company
    - Multi-currency operations (USD revenue, INR expenses)
    - Platform-based billing (Upwork, Toptal, etc.)
    """
    print("=" * 70)
    print("Setting up Chart of Accounts for IT Services Business")
    print("=" * 70)

    accounts_to_create = [
        # === ASSETS ===
        {
            "account_name": "Primary Bank Account",
            "parent_account": f"Bank Accounts - {COMPANY_SUFFIX}",
            "account_number": "1110",
            "account_type": "Bank",
            "account_currency": "INR"
        },
        {
            "account_name": "Payment Gateway",
            "parent_account": f"Bank Accounts - {COMPANY_SUFFIX}",
            "account_number": "1120",
            "account_type": "Bank",
            "account_currency": "INR"
        },
        {
            "account_name": "Accounts Receivable - USD",
            "parent_account": f"Accounts Receivable - {COMPANY_SUFFIX}",
            "account_number": "1310",
            "account_type": "Receivable",
            "account_currency": "USD"
        },

        # === LIABILITIES ===
        {
            "account_name": "Business Credit Card",
            "parent_account": f"Duties and Taxes - {COMPANY_SUFFIX}",
            "account_number": "2110",
            "account_type": "Liability",
            "account_currency": "INR"
        },

        # === INCOME ===
        {
            "account_name": "Client Services Revenue",
            "parent_account": f"Income - {COMPANY_SUFFIX}",
            "account_number": "4010",
            "account_type": "Income",
            "account_currency": "USD"  # Leave blank for multi-currency flexibility
        },
        {
            "account_name": "Exchange Gain/Loss",
            "parent_account": f"Income - {COMPANY_SUFFIX}",
            "account_number": "4900",
            "account_type": "Income",
            "account_currency": "INR"
        },

        # === EXPENSES ===
        {
            "account_name": "Platform Service Fees",
            "parent_account": f"Expenses - {COMPANY_SUFFIX}",
            "account_number": "5110",
            "account_type": "Expense",
            "account_currency": "USD"
        },
        {
            "account_name": "Platform Withholding Tax",
            "parent_account": f"Expenses - {COMPANY_SUFFIX}",
            "account_number": "5120",
            "account_type": "Expense",
            "account_currency": "USD"
        },
        {
            "account_name": "Team Compensation",
            "parent_account": f"Expenses - {COMPANY_SUFFIX}",
            "account_number": "5210",
            "account_type": "Expense",
            "account_currency": "INR"
        },
        {
            "account_name": "Software & Tools",
            "parent_account": f"Expenses - {COMPANY_SUFFIX}",
            "account_number": "5310",
            "account_type": "Expense",
            "account_currency": "INR"
        },
        {
            "account_name": "Operations & Admin",
            "parent_account": f"Expenses - {COMPANY_SUFFIX}",
            "account_number": "5410",
            "account_type": "Expense",
            "account_currency": "INR"
        }
    ]

    for account_data in accounts_to_create:
        try:
            result = client.create_account(
                company=COMPANY,
                **account_data
            )
            print(f"✓ Created: {account_data['account_name']} ({account_data['account_number']})")
        except Exception as e:
            print(f"✗ Error creating {account_data['account_name']}: {e}")

    print("\n✓ Chart of Accounts setup complete!\n")


# ============================================================
# EXAMPLE 2: Create Opening Balance Entry
# ============================================================

def example_create_opening_balance():
    """
    Create opening balance entry for the fiscal year

    Common scenario: Setting up initial balances when:
    - Starting a new fiscal year
    - Migrating to ERPNext
    - Beginning accounting records
    """
    print("=" * 70)
    print("Creating Opening Balance Entry")
    print("=" * 70)

    opening_balances = [
        {
            "account": f"Primary Bank Account - {COMPANY_SUFFIX}",
            "debit": 500000.00  # ₹5 lakh opening cash
        },
        {
            "account": f"Equity Opening Balance - {COMPANY_SUFFIX}",
            "credit": 500000.00
        }
    ]

    try:
        result = client.create_opening_entries(
            opening_date="2024-01-01",
            company=COMPANY,
            balances=opening_balances
        )
        print(f"✓ Created opening entry: {result['name']}")
        print(f"  Total Debit: ₹{result.get('total_debit', 0):,.2f}")
        print(f"  Total Credit: ₹{result.get('total_credit', 0):,.2f}")
    except Exception as e:
        print(f"✗ Error creating opening balance: {e}")

    print()


# ============================================================
# EXAMPLE 3: Revenue Recognition (Multi-Currency)
# ============================================================

def example_create_revenue_entry():
    """
    Create revenue recognition entry in foreign currency

    Scenario: IT services company earning USD from international clients
    - Revenue in USD
    - Exchange rate at time of invoice
    - Creates USD-denominated receivable
    """
    print("=" * 70)
    print("Creating Multi-Currency Revenue Recognition Entry")
    print("=" * 70)

    # Exchange rate: 1 USD = 83.50 INR (example rate)
    EXCHANGE_RATE = 83.50
    REVENUE_USD = 23000.00

    print(f"\nRevenue: ${REVENUE_USD:,.2f} USD")
    print(f"Exchange Rate: {EXCHANGE_RATE} INR/USD")
    print(f"INR Equivalent: ₹{REVENUE_USD * EXCHANGE_RATE:,.2f}")

    accounts = [
        {
            "account": f"Accounts Receivable - USD - {COMPANY_SUFFIX}",
            "party_type": "Customer",
            "party": "Generic Client",  # Create this customer first in ERPNext
            "debit_in_account_currency": REVENUE_USD,
            "credit_in_account_currency": 0,
            "account_currency": "USD",
            "exchange_rate": EXCHANGE_RATE
        },
        {
            "account": f"Client Services Revenue - {COMPANY_SUFFIX}",
            "debit_in_account_currency": 0,
            "credit_in_account_currency": REVENUE_USD,
            "account_currency": "USD",
            "exchange_rate": EXCHANGE_RATE
        }
    ]

    try:
        validate_journal_entry(accounts)

        result = client.create_journal_entry(
            posting_date="2024-07-31",
            company=COMPANY,
            voucher_type="Journal Entry",
            multi_currency=True,
            user_remark="July 2024 Revenue Recognition - Client Services",
            accounts=accounts
        )

        print(f"\n✓ Created journal entry: {result['name']}")
        print(f"  Total Debit: ${result.get('total_debit', 0):,.2f}")
        print(f"  Total Credit: ${result.get('total_credit', 0):,.2f}")
        print(f"  INR Value: ₹{result.get('total_debit', 0) * EXCHANGE_RATE:,.2f}")

    except Exception as e:
        print(f"✗ Error creating revenue entry: {e}")

    print()


# ============================================================
# EXAMPLE 4: Platform Fees Entry
# ============================================================

def example_create_platform_fees_entry():
    """
    Record platform fees (Upwork, Toptal, Fiverr, etc.)

    Scenario: Platform-based work typically has:
    - Service fee (10-20% of gross)
    - Withholding tax (0.1-3%)
    - Both reduce receivables
    """
    print("=" * 70)
    print("Creating Platform Fees Entry")
    print("=" * 70)

    EXCHANGE_RATE = 83.50
    GROSS_REVENUE = 23000.00
    SERVICE_FEE_RATE = 0.10  # 10%
    WHT_RATE = 0.001  # 0.1%

    service_fee = GROSS_REVENUE * SERVICE_FEE_RATE
    wht = GROSS_REVENUE * WHT_RATE
    total_fees = service_fee + wht

    print(f"\nGross Revenue: ${GROSS_REVENUE:,.2f}")
    print(f"Service Fee ({SERVICE_FEE_RATE*100}%): ${service_fee:,.2f}")
    print(f"Withholding Tax ({WHT_RATE*100}%): ${wht:,.2f}")
    print(f"Total Fees: ${total_fees:,.2f}")
    print(f"Net to Receive: ${GROSS_REVENUE - total_fees:,.2f}")

    accounts = [
        {
            "account": f"Platform Service Fees - {COMPANY_SUFFIX}",
            "debit_in_account_currency": service_fee,
            "credit_in_account_currency": 0,
            "account_currency": "USD",
            "exchange_rate": EXCHANGE_RATE
        },
        {
            "account": f"Platform Withholding Tax - {COMPANY_SUFFIX}",
            "debit_in_account_currency": wht,
            "credit_in_account_currency": 0,
            "account_currency": "USD",
            "exchange_rate": EXCHANGE_RATE
        },
        {
            "account": f"Accounts Receivable - USD - {COMPANY_SUFFIX}",
            "party_type": "Customer",
            "party": "Generic Client",
            "debit_in_account_currency": 0,
            "credit_in_account_currency": total_fees,
            "account_currency": "USD",
            "exchange_rate": EXCHANGE_RATE
        }
    ]

    try:
        validate_journal_entry(accounts)

        result = client.create_journal_entry(
            posting_date="2024-07-31",
            company=COMPANY,
            voucher_type="Journal Entry",
            multi_currency=True,
            user_remark="July 2024 Platform Fees",
            accounts=accounts
        )

        print(f"\n✓ Created journal entry: {result['name']}")
        print(f"  INR Value: ₹{total_fees * EXCHANGE_RATE:,.2f}")

    except Exception as e:
        print(f"✗ Error creating platform fees entry: {e}")

    print()


# ============================================================
# EXAMPLE 5: Cash Receipt with Forex Gain/Loss
# ============================================================

def example_create_cash_receipt_with_forex():
    """
    Record cash receipt with forex impact

    Key concept: Exchange rate difference between:
    - Revenue recognition date (when invoice created)
    - Cash receipt date (when payment received)
    Creates forex gain or loss
    """
    print("=" * 70)
    print("Creating Cash Receipt with Forex Gain/Loss")
    print("=" * 70)

    # Revenue was recognized at one rate
    REVENUE_RATE = 83.50
    # Cash received at different rate
    RECEIPT_RATE = 78.20
    USD_AMOUNT = 20683.55  # Net after platform fees

    inr_at_revenue_rate = USD_AMOUNT * REVENUE_RATE
    inr_received = USD_AMOUNT * RECEIPT_RATE
    forex_loss = inr_at_revenue_rate - inr_received

    print(f"\nUSD Amount: ${USD_AMOUNT:,.2f}")
    print(f"Revenue Recognition Rate: {REVENUE_RATE} INR/USD")
    print(f"Cash Receipt Rate: {RECEIPT_RATE} INR/USD")
    print(f"Expected INR (at revenue rate): ₹{inr_at_revenue_rate:,.2f}")
    print(f"Actual INR Received: ₹{inr_received:,.2f}")
    print(f"Forex Loss: ₹{forex_loss:,.2f}")

    accounts = [
        {
            "account": f"Primary Bank Account - {COMPANY_SUFFIX}",
            "debit_in_account_currency": inr_received,
            "credit_in_account_currency": 0,
            "account_currency": "INR"
        },
        {
            "account": f"Exchange Gain/Loss - {COMPANY_SUFFIX}",
            "debit_in_account_currency": forex_loss,
            "credit_in_account_currency": 0,
            "account_currency": "INR"
        },
        {
            "account": f"Accounts Receivable - USD - {COMPANY_SUFFIX}",
            "party_type": "Customer",
            "party": "Generic Client",
            "debit_in_account_currency": 0,
            "credit_in_account_currency": USD_AMOUNT,
            "account_currency": "USD",
            "exchange_rate": REVENUE_RATE  # Use original recognition rate
        }
    ]

    try:
        validate_journal_entry(accounts)

        result = client.create_journal_entry(
            posting_date="2024-07-31",
            company=COMPANY,
            voucher_type="Bank Entry",
            multi_currency=True,
            user_remark=f"Cash receipt - Forex loss of ₹{forex_loss:,.2f}",
            accounts=accounts
        )

        print(f"\n✓ Created journal entry: {result['name']}")

    except Exception as e:
        print(f"✗ Error creating cash receipt entry: {e}")

    print()


# ============================================================
# EXAMPLE 6: Record Expenses
# ============================================================

def example_create_expense_entries():
    """
    Record various operating expenses

    Demonstrates:
    - Simple expense entries (bank payment)
    - Split payments (cash + credit card)
    """
    print("=" * 70)
    print("Creating Expense Entries")
    print("=" * 70)

    # Salary payment
    print("\n1. Team Compensation")
    try:
        result = client.create_journal_entry(
            posting_date="2024-07-31",
            company=COMPANY,
            voucher_type="Bank Entry",
            user_remark="July 2024 Team Compensation",
            accounts=[
                {
                    "account": f"Team Compensation - {COMPANY_SUFFIX}",
                    "debit_in_account_currency": 267000,
                    "credit_in_account_currency": 0
                },
                {
                    "account": f"Primary Bank Account - {COMPANY_SUFFIX}",
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": 267000
                }
            ]
        )
        print(f"✓ Created: {result['name']} - ₹267,000")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Operations expenses (split payment)
    print("\n2. Operations Expenses (Cash + Credit Card)")
    try:
        result = client.create_journal_entry(
            posting_date="2024-07-31",
            company=COMPANY,
            voucher_type="Journal Entry",
            user_remark="July 2024 Operations - Mixed payment",
            accounts=[
                {
                    "account": f"Operations & Admin - {COMPANY_SUFFIX}",
                    "debit_in_account_currency": 286668,
                    "credit_in_account_currency": 0
                },
                {
                    "account": f"Primary Bank Account - {COMPANY_SUFFIX}",
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": 189000
                },
                {
                    "account": f"Business Credit Card - {COMPANY_SUFFIX}",
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": 97668
                }
            ]
        )
        print(f"✓ Created: {result['name']}")
        print(f"  Cash: ₹189,000 | Credit: ₹97,668")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()


# ============================================================
# EXAMPLE 7: Retrieve and Analyze Transactions
# ============================================================

def example_retrieve_transactions():
    """
    Query and analyze journal entries

    Demonstrates:
    - Filtering by date range
    - Filtering by status (draft/submitted)
    - Aggregating totals
    """
    print("=" * 70)
    print("Retrieving July 2024 Transactions")
    print("=" * 70)

    try:
        entries = client.list_journal_entries(
            filters={
                "posting_date": ["between", ["2024-07-01", "2024-07-31"]],
                "company": COMPANY,
                "docstatus": 1  # Only submitted entries
            },
            order_by="posting_date asc"
        )

        print(f"\nFound {len(entries)} journal entries\n")

        total_debit = 0
        total_credit = 0

        for entry in entries:
            print(f"{entry['posting_date']} | {entry['name']}")
            print(f"  Type: {entry['voucher_type']}")
            print(f"  Debit: ₹{entry.get('total_debit', 0):,.2f}")
            print(f"  Credit: ₹{entry.get('total_credit', 0):,.2f}")
            print()

            total_debit += entry.get('total_debit', 0)
            total_credit += entry.get('total_credit', 0)

        print(f"{'='*70}")
        print(f"Total Debits: ₹{total_debit:,.2f}")
        print(f"Total Credits: ₹{total_credit:,.2f}")

    except Exception as e:
        print(f"✗ Error retrieving entries: {e}")

    print()


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ERPNext Accounting API - Basic Operations Examples")
    print("=" * 70 + "\n")

    # Uncomment the examples you want to run

    # SETUP (run once)
    # example_setup_chart_of_accounts()
    # example_create_opening_balance()

    # TRANSACTIONS (run for each period)
    # example_create_revenue_entry()
    # example_create_platform_fees_entry()
    # example_create_cash_receipt_with_forex()
    # example_create_expense_entries()

    # ANALYSIS (run anytime)
    # example_retrieve_transactions()

    print("\n✓ Example demonstrations complete!")
    print("\nUncomment the functions in __main__ to run specific examples")
