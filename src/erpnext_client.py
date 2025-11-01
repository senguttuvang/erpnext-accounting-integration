"""
ERPNext API Client for Accounting Operations
Comprehensive wrapper for ERPNext REST API with focus on accounting operations

Author: Generated for PearlThoughts
Date: 2025-11-01
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class AccountType(Enum):
    """Standard ERPNext Account Types"""
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    INCOME = "Income"
    EXPENSE = "Expense"
    BANK = "Bank"
    CASH = "Cash"
    RECEIVABLE = "Receivable"
    PAYABLE = "Payable"
    TAX = "Tax"


class VoucherType(Enum):
    """Journal Entry Types"""
    JOURNAL_ENTRY = "Journal Entry"
    BANK_ENTRY = "Bank Entry"
    CASH_ENTRY = "Cash Entry"
    CREDIT_CARD_ENTRY = "Credit Card Entry"
    DEBIT_NOTE = "Debit Note"
    CREDIT_NOTE = "Credit Note"
    CONTRA_ENTRY = "Contra Entry"
    EXCISE_ENTRY = "Excise Entry"
    WRITE_OFF_ENTRY = "Write Off Entry"
    OPENING_ENTRY = "Opening Entry"
    DEPRECIATION_ENTRY = "Depreciation Entry"


@dataclass
class ERPNextConfig:
    """Configuration for ERPNext connection"""
    base_url: str
    api_key: str
    api_secret: str

    @property
    def auth_token(self) -> str:
        """Generate authorization token"""
        return f"{self.api_key}:{self.api_secret}"

    @property
    def headers(self) -> Dict[str, str]:
        """Standard headers for API requests"""
        return {
            "Authorization": f"token {self.auth_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }


class ERPNextClient:
    """
    Main client for ERPNext API operations

    Usage:
        config = ERPNextConfig(
            base_url="https://your-instance.erpnext.com",
            api_key="your_api_key",
            api_secret="your_api_secret"
        )
        client = ERPNextClient(config)
    """

    def __init__(self, config: ERPNextConfig):
        self.config = config
        self.base_url = config.base_url.rstrip('/')

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to ERPNext API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            requests.exceptions.RequestException: On API errors
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.config.headers,
                json=data if method in ['POST', 'PUT'] else None,
                params=params if method == 'GET' else data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    # ============================================================
    # CHART OF ACCOUNTS OPERATIONS
    # ============================================================

    def list_accounts(
        self,
        fields: Optional[List[str]] = None,
        filters: Optional[Dict] = None,
        order_by: str = "name asc",
        limit_start: int = 0,
        limit_page_length: int = 20
    ) -> List[Dict]:
        """
        Get list of accounts from Chart of Accounts

        Args:
            fields: List of fields to retrieve
            filters: Filter conditions
            order_by: Sort order
            limit_start: Pagination start
            limit_page_length: Number of records per page

        Returns:
            List of account records

        Example:
            accounts = client.list_accounts(
                fields=["name", "account_name", "account_type", "parent_account"],
                filters={"is_group": 0, "disabled": 0}
            )
        """
        if fields is None:
            fields = [
                "name", "account_name", "parent_account",
                "account_type", "root_type", "account_number",
                "account_currency", "is_group", "disabled"
            ]

        payload = {
            "fields": json.dumps(fields),
            "filters": json.dumps(filters or []),
            "order_by": order_by,
            "limit_start": limit_start,
            "limit_page_length": limit_page_length
        }

        response = self._make_request(
            "GET",
            "/api/resource/Account",
            params=payload
        )
        return response.get("data", [])

    def get_account(self, account_name: str) -> Dict:
        """
        Get single account details

        Args:
            account_name: Account name or number

        Returns:
            Account details
        """
        response = self._make_request(
            "GET",
            f"/api/resource/Account/{account_name}"
        )
        return response.get("data", {})

    def create_account(
        self,
        account_name: str,
        parent_account: str,
        account_number: Optional[str] = None,
        account_type: Optional[str] = None,
        account_currency: str = "INR",
        is_group: bool = False,
        company: str = None,
        **kwargs
    ) -> Dict:
        """
        Create new account in Chart of Accounts

        Args:
            account_name: Name of the account
            parent_account: Parent account name
            account_number: Account number/code
            account_type: Type of account (Asset, Liability, etc.)
            account_currency: Currency for the account
            is_group: Whether this is a group account
            company: Company name
            **kwargs: Additional account properties

        Returns:
            Created account details

        Example:
            account = client.create_account(
                account_name="Upwork Fees",
                parent_account="Expenses - PT",
                account_number="5110",
                account_type="Expense",
                account_currency="USD"
            )
        """
        payload = {
            "account_name": account_name,
            "parent_account": parent_account,
            "is_group": 1 if is_group else 0,
            "account_currency": account_currency
        }

        if account_number:
            payload["account_number"] = account_number
        if account_type:
            payload["account_type"] = account_type
        if company:
            payload["company"] = company

        payload.update(kwargs)

        response = self._make_request(
            "POST",
            "/api/resource/Account",
            data=payload
        )
        return response.get("data", {})

    def update_account(
        self,
        account_name: str,
        updates: Dict[str, Any]
    ) -> Dict:
        """
        Update existing account

        Args:
            account_name: Account to update
            updates: Fields to update

        Returns:
            Updated account details
        """
        response = self._make_request(
            "PUT",
            f"/api/resource/Account/{account_name}",
            data=updates
        )
        return response.get("data", {})

    def delete_account(self, account_name: str) -> Dict:
        """
        Delete an account

        Args:
            account_name: Account to delete

        Returns:
            Deletion confirmation
        """
        response = self._make_request(
            "DELETE",
            f"/api/resource/Account/{account_name}"
        )
        return response

    def get_account_hierarchy(
        self,
        root_account: Optional[str] = None,
        company: Optional[str] = None
    ) -> List[Dict]:
        """
        Get account hierarchy tree structure

        Args:
            root_account: Root account to start from
            company: Filter by company

        Returns:
            Hierarchical account structure
        """
        filters = {}
        if root_account:
            filters["parent_account"] = root_account
        if company:
            filters["company"] = company

        # Get all accounts
        accounts = self.list_accounts(
            filters=filters,
            limit_page_length=1000
        )

        # Build hierarchy
        return self._build_tree(accounts)

    def _build_tree(self, accounts: List[Dict]) -> List[Dict]:
        """Helper to build hierarchical tree from flat account list"""
        account_map = {acc["name"]: {**acc, "children": []} for acc in accounts}
        root_accounts = []

        for account in accounts:
            parent = account.get("parent_account")
            if parent and parent in account_map:
                account_map[parent]["children"].append(account_map[account["name"]])
            else:
                root_accounts.append(account_map[account["name"]])

        return root_accounts

    # ============================================================
    # JOURNAL ENTRY OPERATIONS
    # ============================================================

    def create_journal_entry(
        self,
        posting_date: str,
        accounts: List[Dict],
        company: str,
        voucher_type: str = "Journal Entry",
        user_remark: Optional[str] = None,
        cheque_no: Optional[str] = None,
        cheque_date: Optional[str] = None,
        multi_currency: bool = False,
        **kwargs
    ) -> Dict:
        """
        Create a Journal Entry (single or multi-currency)

        Args:
            posting_date: Date of posting (YYYY-MM-DD)
            accounts: List of account entries with debit/credit
            company: Company name
            voucher_type: Type of voucher
            user_remark: Description/narration
            cheque_no: Cheque number if applicable
            cheque_date: Cheque date if applicable
            multi_currency: Whether this is multi-currency transaction
            **kwargs: Additional journal entry fields

        Returns:
            Created journal entry details

        Example - Single Currency:
            je = client.create_journal_entry(
                posting_date="2025-07-31",
                company="PearlThoughts",
                user_remark="July salary payment",
                accounts=[
                    {
                        "account": "Salaries - PT",
                        "debit_in_account_currency": 267000,
                        "credit_in_account_currency": 0
                    },
                    {
                        "account": "ICICI Bank - PT",
                        "debit_in_account_currency": 0,
                        "credit_in_account_currency": 267000
                    }
                ]
            )

        Example - Multi Currency:
            je = client.create_journal_entry(
                posting_date="2025-07-31",
                company="PearlThoughts",
                multi_currency=1,
                user_remark="Upwork revenue recognition",
                accounts=[
                    {
                        "account": "Accounts Receivable - USD - PT",
                        "party_type": "Customer",
                        "party": "Upwork",
                        "debit_in_account_currency": 20683.55,
                        "credit_in_account_currency": 0,
                        "account_currency": "USD",
                        "exchange_rate": 86.25
                    },
                    {
                        "account": "Client Services Revenue - PT",
                        "debit_in_account_currency": 0,
                        "credit_in_account_currency": 20683.55,
                        "account_currency": "USD",
                        "exchange_rate": 86.25
                    }
                ]
            )
        """
        payload = {
            "doctype": "Journal Entry",
            "posting_date": posting_date,
            "company": company,
            "voucher_type": voucher_type,
            "accounts": accounts,
            "multi_currency": 1 if multi_currency else 0
        }

        if user_remark:
            payload["user_remark"] = user_remark
        if cheque_no:
            payload["cheque_no"] = cheque_no
        if cheque_date:
            payload["cheque_date"] = cheque_date

        payload.update(kwargs)

        response = self._make_request(
            "POST",
            "/api/resource/Journal Entry",
            data=payload
        )
        return response.get("data", {})

    def list_journal_entries(
        self,
        fields: Optional[List[str]] = None,
        filters: Optional[Dict] = None,
        order_by: str = "posting_date desc",
        limit_start: int = 0,
        limit_page_length: int = 20
    ) -> List[Dict]:
        """
        Get list of journal entries

        Args:
            fields: Fields to retrieve
            filters: Filter conditions
            order_by: Sort order
            limit_start: Pagination start
            limit_page_length: Records per page

        Returns:
            List of journal entries

        Example:
            entries = client.list_journal_entries(
                filters={
                    "posting_date": [">=", "2025-07-01"],
                    "docstatus": 1  # Submitted entries only
                },
                fields=["name", "posting_date", "total_debit", "total_credit", "user_remark"]
            )
        """
        if fields is None:
            fields = [
                "name", "posting_date", "voucher_type",
                "total_debit", "total_credit", "user_remark",
                "docstatus", "multi_currency"
            ]

        payload = {
            "fields": json.dumps(fields),
            "filters": json.dumps(filters or []),
            "order_by": order_by,
            "limit_start": limit_start,
            "limit_page_length": limit_page_length
        }

        response = self._make_request(
            "GET",
            "/api/resource/Journal Entry",
            params=payload
        )
        return response.get("data", [])

    def get_journal_entry(self, entry_name: str) -> Dict:
        """
        Get single journal entry details

        Args:
            entry_name: Journal entry name/ID

        Returns:
            Journal entry with all account lines
        """
        response = self._make_request(
            "GET",
            f"/api/resource/Journal Entry/{entry_name}"
        )
        return response.get("data", {})

    def update_journal_entry(
        self,
        entry_name: str,
        updates: Dict[str, Any]
    ) -> Dict:
        """
        Update journal entry (only if in draft status)

        Args:
            entry_name: Entry to update
            updates: Fields to update

        Returns:
            Updated journal entry
        """
        response = self._make_request(
            "PUT",
            f"/api/resource/Journal Entry/{entry_name}",
            data=updates
        )
        return response.get("data", {})

    def delete_journal_entry(self, entry_name: str) -> Dict:
        """
        Delete a journal entry (only if in draft status)

        Args:
            entry_name: Entry to delete

        Returns:
            Deletion confirmation
        """
        response = self._make_request(
            "DELETE",
            f"/api/resource/Journal Entry/{entry_name}"
        )
        return response

    def submit_journal_entry(self, entry_name: str) -> Dict:
        """
        Submit a journal entry (post to ledger)

        Args:
            entry_name: Entry to submit

        Returns:
            Submitted journal entry
        """
        # Get current entry
        entry = self.get_journal_entry(entry_name)

        # Submit using docstatus
        updates = {"docstatus": 1}

        response = self._make_request(
            "PUT",
            f"/api/resource/Journal Entry/{entry_name}",
            data=updates
        )
        return response.get("data", {})

    def cancel_journal_entry(self, entry_name: str) -> Dict:
        """
        Cancel a submitted journal entry

        Args:
            entry_name: Entry to cancel

        Returns:
            Cancelled journal entry
        """
        updates = {"docstatus": 2}

        response = self._make_request(
            "PUT",
            f"/api/resource/Journal Entry/{entry_name}",
            data=updates
        )
        return response.get("data", {})

    # ============================================================
    # ADVANCED OPERATIONS
    # ============================================================

    def get_account_balance(
        self,
        account: str,
        date: Optional[str] = None,
        company: Optional[str] = None
    ) -> Dict:
        """
        Get account balance as of a specific date

        Args:
            account: Account name
            date: Balance as of date (defaults to today)
            company: Company filter

        Returns:
            Balance information
        """
        params = {"account": account}
        if date:
            params["date"] = date
        if company:
            params["company"] = company

        response = self._make_request(
            "GET",
            "/api/method/erpnext.accounts.utils.get_balance_on",
            params=params
        )
        return response

    def create_opening_entries(
        self,
        opening_date: str,
        company: str,
        balances: List[Dict[str, Any]]
    ) -> Dict:
        """
        Create opening balance entries

        Args:
            opening_date: Opening balance date
            company: Company name
            balances: List of account balances

        Returns:
            Created journal entry

        Example:
            opening = client.create_opening_entries(
                opening_date="2025-01-01",
                company="PearlThoughts",
                balances=[
                    {"account": "ICICI Bank - PT", "debit": 500000},
                    {"account": "Equity Opening Balance - PT", "credit": 500000}
                ]
            )
        """
        accounts = []
        for bal in balances:
            account_entry = {
                "account": bal["account"],
                "debit_in_account_currency": bal.get("debit", 0),
                "credit_in_account_currency": bal.get("credit", 0)
            }
            if "party_type" in bal:
                account_entry["party_type"] = bal["party_type"]
            if "party" in bal:
                account_entry["party"] = bal["party"]
            accounts.append(account_entry)

        return self.create_journal_entry(
            posting_date=opening_date,
            company=company,
            voucher_type="Opening Entry",
            user_remark="Opening Balances",
            accounts=accounts,
            is_opening="Yes"
        )

    def get_general_ledger(
        self,
        from_date: str,
        to_date: str,
        account: Optional[str] = None,
        company: Optional[str] = None,
        party_type: Optional[str] = None,
        party: Optional[str] = None
    ) -> List[Dict]:
        """
        Get General Ledger entries

        Args:
            from_date: Start date
            to_date: End date
            account: Filter by account
            company: Filter by company
            party_type: Filter by party type
            party: Filter by party

        Returns:
            List of GL entries
        """
        filters = {
            "posting_date": ["between", [from_date, to_date]]
        }

        if account:
            filters["account"] = account
        if company:
            filters["company"] = company
        if party_type:
            filters["party_type"] = party_type
        if party:
            filters["party"] = party

        payload = {
            "fields": json.dumps([
                "name", "posting_date", "account", "debit",
                "credit", "against", "voucher_type", "voucher_no",
                "party_type", "party", "against_voucher"
            ]),
            "filters": json.dumps(filters),
            "order_by": "posting_date asc, creation asc",
            "limit_page_length": 10000
        }

        response = self._make_request(
            "GET",
            "/api/resource/GL Entry",
            params=payload
        )
        return response.get("data", [])


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def format_date(date_obj: datetime) -> str:
    """Format datetime to ERPNext date string"""
    return date_obj.strftime("%Y-%m-%d")


def validate_journal_entry(accounts: List[Dict]) -> bool:
    """
    Validate that journal entry is balanced

    Args:
        accounts: List of account entries

    Returns:
        True if balanced, raises ValueError otherwise
    """
    total_debit = sum(
        acc.get("debit_in_account_currency", 0) or acc.get("debit", 0)
        for acc in accounts
    )
    total_credit = sum(
        acc.get("credit_in_account_currency", 0) or acc.get("credit", 0)
        for acc in accounts
    )

    if abs(total_debit - total_credit) > 0.01:  # Allow for rounding
        raise ValueError(
            f"Journal entry not balanced! Debit: {total_debit}, Credit: {total_credit}"
        )

    return True
