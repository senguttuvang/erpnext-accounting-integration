"""
ERPNext API Configuration Template

Instructions:
1. Copy this file to config.py
2. Fill in your ERPNext instance details
3. Never commit config.py to version control (add to .gitignore)

To generate API keys:
1. Login to ERPNext
2. Go to User List → Select your user
3. Settings tab → API Access section
4. Click "Generate Keys"
5. Copy API Secret immediately (shown only once!)
"""

from erpnext_client import ERPNextConfig

# ============================================================
# ERPNext Instance Configuration
# ============================================================

# Your ERPNext instance URL (without trailing slash)
ERPNEXT_URL = "https://your-instance.erpnext.com"

# API Credentials (generate from User settings)
API_KEY = "your_api_key_here"
API_SECRET = "your_api_secret_here"

# ============================================================
# Company Configuration
# ============================================================

# Your company name as it appears in ERPNext
COMPANY = "PearlThoughts"

# Short company suffix used in account names (e.g., "PT" for PearlThoughts)
COMPANY_SUFFIX = "PT"

# Base currency for your company
BASE_CURRENCY = "INR"

# ============================================================
# Create Config Object
# ============================================================

config = ERPNextConfig(
    base_url=ERPNEXT_URL,
    api_key=API_KEY,
    api_secret=API_SECRET
)

# ============================================================
# Account Mapping Configuration (for Beancount migration)
# ============================================================

# Map your beancount account names to ERPNext account names
# Customize this based on your account structure
ACCOUNT_MAPPINGS = {
    # Assets
    'Assets:Cash:ICICI': f'ICICI Bank - {COMPANY_SUFFIX}',
    'Assets:Cash:RazorpayX': f'RazorpayX - {COMPANY_SUFFIX}',
    'Assets:AccountsReceivable': f'Accounts Receivable - USD - {COMPANY_SUFFIX}',

    # Liabilities
    'Liabilities:CreditCard:ICICI': f'ICICI Credit Card - {COMPANY_SUFFIX}',
    'Liabilities:CreditCard:SBI': f'SBI Credit Card - {COMPANY_SUFFIX}',

    # Income
    'Income:ClientServices': f'Client Services Revenue - {COMPANY_SUFFIX}',
    'Income:ForexGain': f'Exchange Gain/Loss - {COMPANY_SUFFIX}',

    # Expenses
    'Expenses:Platform:Upwork:ServiceFees': f'Upwork Platform Fees - {COMPANY_SUFFIX}',
    'Expenses:Platform:Upwork:WHT': f'Upwork Withholding Tax - {COMPANY_SUFFIX}',
    'Expenses:Salaries:TeamCompensation': f'Salaries - {COMPANY_SUFFIX}',
    'Expenses:Operations:General': f'Operations Expenses - {COMPANY_SUFFIX}',
    'Expenses:Technology:General': f'Technology Expenses - {COMPANY_SUFFIX}',

    # Equity
    'Equity:Opening-Balances': f'Equity Opening Balance - {COMPANY_SUFFIX}',
}

# ============================================================
# Default Parent Accounts (for account creation)
# ============================================================

DEFAULT_PARENTS = {
    'Asset': f'Application of Funds (Assets) - {COMPANY_SUFFIX}',
    'Liability': f'Source of Funds (Liabilities) - {COMPANY_SUFFIX}',
    'Income': f'Income - {COMPANY_SUFFIX}',
    'Expense': f'Expenses - {COMPANY_SUFFIX}',
    'Equity': f'Equity - {COMPANY_SUFFIX}',
    'Bank': f'Bank Accounts - {COMPANY_SUFFIX}',
    'Cash': f'Cash In Hand - {COMPANY_SUFFIX}',
}

# ============================================================
# Exchange Rates (optional - for reference)
# ============================================================

# Common exchange rates (update as needed)
EXCHANGE_RATES = {
    'USD': {
        'to': 'INR',
        'rate': 86.25,  # Update with current rate
        'as_of': '2025-07-31'
    },
    'EUR': {
        'to': 'INR',
        'rate': 95.00,  # Update with current rate
        'as_of': '2025-07-31'
    }
}

# ============================================================
# Migration Settings
# ============================================================

# Default settings for beancount migration
MIGRATION_SETTINGS = {
    'dry_run': True,  # Always start with dry run
    'auto_submit': False,  # Don't auto-submit initially
    'skip_opening_balance': False,  # Set True if opening balance already exists
    'date_format': '%Y-%m-%d',  # Beancount date format
}

# ============================================================
# Reporting Settings
# ============================================================

# Fiscal year settings
FISCAL_YEAR_START = '04-01'  # April 1st (MM-DD format)
FISCAL_YEAR_END = '03-31'    # March 31st (MM-DD format)

# Report formats
REPORT_SETTINGS = {
    'currency_symbol': '₹',
    'thousands_separator': ',',
    'decimal_places': 2,
    'export_format': 'csv',  # csv, xlsx, pdf
}

# ============================================================
# Validation
# ============================================================

def validate_config():
    """
    Validate configuration before use
    Returns True if valid, raises ValueError if not
    """
    if API_KEY == "your_api_key_here":
        raise ValueError("Please set API_KEY in config.py")

    if API_SECRET == "your_api_secret_here":
        raise ValueError("Please set API_SECRET in config.py")

    if ERPNEXT_URL == "https://your-instance.erpnext.com":
        raise ValueError("Please set ERPNEXT_URL in config.py")

    if COMPANY == "YourCompanyName":
        raise ValueError("Please set COMPANY in config.py")

    print("✓ Configuration validated successfully")
    return True


# ============================================================
# Usage Example
# ============================================================

if __name__ == "__main__":
    """
    Test your configuration
    """
    print("Testing ERPNext Configuration...")
    print(f"URL: {ERPNEXT_URL}")
    print(f"Company: {COMPANY}")
    print(f"Company Suffix: {COMPANY_SUFFIX}")
    print(f"Base Currency: {BASE_CURRENCY}")

    try:
        validate_config()

        # Test connection
        from erpnext_client import ERPNextClient

        client = ERPNextClient(config)

        # Try to fetch user info
        response = client._make_request(
            "GET",
            "/api/method/frappe.auth.get_logged_user"
        )

        print(f"\n✓ Connection successful!")
        print(f"Logged in as: {response.get('message')}")

    except Exception as e:
        print(f"\n✗ Configuration test failed: {e}")
        print("\nPlease check:")
        print("1. Your ERPNext URL is correct")
        print("2. API keys are valid")
        print("3. You have network access to the ERPNext instance")
