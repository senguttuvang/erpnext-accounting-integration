"""
Advanced ERPNext Reporting and Account Management
Provides utilities for financial reporting, analysis, and account hierarchy management

Features:
- Trial Balance generation
- Profit & Loss statement
- Balance Sheet
- Account reconciliation
- Account hierarchy management
- Multi-currency consolidation
"""

from erpnext_client import ERPNextClient, ERPNextConfig
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json
import csv


class ERPNextReporter:
    """
    Advanced reporting functionality for ERPNext
    """

    def __init__(self, client: ERPNextClient, company: str):
        self.client = client
        self.company = company

    # ============================================================
    # TRIAL BALANCE
    # ============================================================

    def generate_trial_balance(
        self,
        from_date: str,
        to_date: str,
        currency: str = "INR",
        include_opening: bool = True
    ) -> Dict[str, Any]:
        """
        Generate trial balance report

        Args:
            from_date: Report start date
            to_date: Report end date
            currency: Reporting currency
            include_opening: Include opening balances

        Returns:
            Trial balance data
        """
        print("=" * 70)
        print(f"TRIAL BALANCE - {from_date} to {to_date}")
        print(f"Company: {self.company}")
        print(f"Currency: {currency}")
        print("=" * 70)

        # Get all accounts
        accounts = self.client.list_accounts(
            filters={"company": self.company, "is_group": 0, "disabled": 0},
            limit_page_length=1000
        )

        # Get GL entries for the period
        gl_entries = self.client.get_general_ledger(
            from_date=from_date,
            to_date=to_date,
            company=self.company
        )

        # Calculate balances
        balances = defaultdict(lambda: {'debit': 0, 'credit': 0})

        for entry in gl_entries:
            account = entry['account']
            balances[account]['debit'] += entry.get('debit', 0)
            balances[account]['credit'] += entry.get('credit', 0)

        # Generate report
        report_data = []
        total_debit = 0
        total_credit = 0

        print(f"\n{'Account':50} {'Debit':>15} {'Credit':>15}")
        print("-" * 82)

        for account in accounts:
            acc_name = account['account_name']
            full_name = account['name']

            if full_name in balances:
                debit = balances[full_name]['debit']
                credit = balances[full_name]['credit']
                balance = debit - credit

                # Determine display columns based on balance
                if balance > 0:
                    debit_display = balance
                    credit_display = 0
                else:
                    debit_display = 0
                    credit_display = abs(balance)

                if debit_display != 0 or credit_display != 0:
                    report_data.append({
                        'account': acc_name,
                        'account_number': account.get('account_number', ''),
                        'account_type': account.get('account_type', ''),
                        'debit': debit_display,
                        'credit': credit_display
                    })

                    total_debit += debit_display
                    total_credit += credit_display

                    print(f"{acc_name:50} {debit_display:>15,.2f} {credit_display:>15,.2f}")

        print("-" * 82)
        print(f"{'TOTAL':50} {total_debit:>15,.2f} {total_credit:>15,.2f}")
        print(f"{'Difference':50} {abs(total_debit - total_credit):>15,.2f}")

        return {
            'from_date': from_date,
            'to_date': to_date,
            'currency': currency,
            'accounts': report_data,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'difference': abs(total_debit - total_credit)
        }

    # ============================================================
    # PROFIT & LOSS STATEMENT
    # ============================================================

    def generate_profit_loss(
        self,
        from_date: str,
        to_date: str,
        currency: str = "INR"
    ) -> Dict[str, Any]:
        """
        Generate Profit & Loss statement

        Args:
            from_date: Period start date
            to_date: Period end date
            currency: Reporting currency

        Returns:
            P&L data
        """
        print("\n" + "=" * 70)
        print(f"PROFIT & LOSS STATEMENT")
        print(f"Period: {from_date} to {to_date}")
        print(f"Company: {self.company}")
        print("=" * 70)

        # Get income and expense accounts
        income_accounts = self.client.list_accounts(
            filters={
                "company": self.company,
                "root_type": "Income",
                "is_group": 0,
                "disabled": 0
            },
            limit_page_length=1000
        )

        expense_accounts = self.client.list_accounts(
            filters={
                "company": self.company,
                "root_type": "Expense",
                "is_group": 0,
                "disabled": 0
            },
            limit_page_length=1000
        )

        # Get GL entries
        gl_entries = self.client.get_general_ledger(
            from_date=from_date,
            to_date=to_date,
            company=self.company
        )

        # Calculate income and expenses
        income_balances = defaultdict(float)
        expense_balances = defaultdict(float)

        income_account_names = {acc['name'] for acc in income_accounts}
        expense_account_names = {acc['name'] for acc in expense_accounts}

        for entry in gl_entries:
            account = entry['account']
            amount = entry.get('credit', 0) - entry.get('debit', 0)

            if account in income_account_names:
                income_balances[account] += amount
            elif account in expense_account_names:
                expense_balances[account] -= amount

        # Display Income
        print("\nINCOME")
        print("-" * 70)
        total_income = 0

        for account in income_accounts:
            acc_name = account['account_name']
            full_name = account['name']
            balance = income_balances.get(full_name, 0)

            if balance != 0:
                print(f"{acc_name:50} {balance:>15,.2f}")
                total_income += balance

        print("-" * 70)
        print(f"{'Total Income':50} {total_income:>15,.2f}")

        # Display Expenses
        print("\nEXPENSES")
        print("-" * 70)
        total_expenses = 0

        for account in expense_accounts:
            acc_name = account['account_name']
            full_name = account['name']
            balance = expense_balances.get(full_name, 0)

            if balance != 0:
                print(f"{acc_name:50} {balance:>15,.2f}")
                total_expenses += balance

        print("-" * 70)
        print(f"{'Total Expenses':50} {total_expenses:>15,.2f}")

        # Calculate Net Profit/Loss
        net_profit = total_income - total_expenses

        print("\n" + "=" * 70)
        print(f"{'Net Profit/(Loss)':50} {net_profit:>15,.2f}")
        print("=" * 70)

        return {
            'from_date': from_date,
            'to_date': to_date,
            'currency': currency,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'income_details': dict(income_balances),
            'expense_details': dict(expense_balances)
        }

    # ============================================================
    # BALANCE SHEET
    # ============================================================

    def generate_balance_sheet(
        self,
        as_of_date: str,
        currency: str = "INR"
    ) -> Dict[str, Any]:
        """
        Generate Balance Sheet

        Args:
            as_of_date: Balance sheet date
            currency: Reporting currency

        Returns:
            Balance sheet data
        """
        print("\n" + "=" * 70)
        print(f"BALANCE SHEET as of {as_of_date}")
        print(f"Company: {self.company}")
        print("=" * 70)

        # Get accounts by type
        asset_accounts = self.client.list_accounts(
            filters={
                "company": self.company,
                "root_type": "Asset",
                "is_group": 0,
                "disabled": 0
            },
            limit_page_length=1000
        )

        liability_accounts = self.client.list_accounts(
            filters={
                "company": self.company,
                "root_type": "Liability",
                "is_group": 0,
                "disabled": 0
            },
            limit_page_length=1000
        )

        equity_accounts = self.client.list_accounts(
            filters={
                "company": self.company,
                "root_type": "Equity",
                "is_group": 0,
                "disabled": 0
            },
            limit_page_length=1000
        )

        # Get GL entries up to date
        gl_entries = self.client.get_general_ledger(
            from_date="1900-01-01",
            to_date=as_of_date,
            company=self.company
        )

        # Calculate balances
        balances = defaultdict(float)
        for entry in gl_entries:
            account = entry['account']
            balances[account] += entry.get('debit', 0) - entry.get('credit', 0)

        # Display Assets
        print("\nASSETS")
        print("-" * 70)
        total_assets = 0

        for account in asset_accounts:
            acc_name = account['account_name']
            full_name = account['name']
            balance = balances.get(full_name, 0)

            if balance != 0:
                print(f"{acc_name:50} {balance:>15,.2f}")
                total_assets += balance

        print("-" * 70)
        print(f"{'Total Assets':50} {total_assets:>15,.2f}")

        # Display Liabilities
        print("\nLIABILITIES")
        print("-" * 70)
        total_liabilities = 0

        for account in liability_accounts:
            acc_name = account['account_name']
            full_name = account['name']
            balance = abs(balances.get(full_name, 0))

            if balance != 0:
                print(f"{acc_name:50} {balance:>15,.2f}")
                total_liabilities += balance

        print("-" * 70)
        print(f"{'Total Liabilities':50} {total_liabilities:>15,.2f}")

        # Display Equity
        print("\nEQUITY")
        print("-" * 70)
        total_equity = 0

        for account in equity_accounts:
            acc_name = account['account_name']
            full_name = account['name']
            balance = abs(balances.get(full_name, 0))

            if balance != 0:
                print(f"{acc_name:50} {balance:>15,.2f}")
                total_equity += balance

        print("-" * 70)
        print(f"{'Total Equity':50} {total_equity:>15,.2f}")

        # Total Liabilities + Equity
        total_liab_equity = total_liabilities + total_equity

        print("\n" + "=" * 70)
        print(f"{'Total Liabilities + Equity':50} {total_liab_equity:>15,.2f}")
        print(f"{'Difference (should be 0)':50} {abs(total_assets - total_liab_equity):>15,.2f}")
        print("=" * 70)

        return {
            'as_of_date': as_of_date,
            'currency': currency,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'difference': abs(total_assets - total_liab_equity)
        }

    # ============================================================
    # ACCOUNT RECONCILIATION
    # ============================================================

    def reconcile_account(
        self,
        account: str,
        from_date: str,
        to_date: str,
        export_csv: Optional[str] = None
    ) -> List[Dict]:
        """
        Reconcile an account with detailed transaction listing

        Args:
            account: Account to reconcile
            from_date: Start date
            to_date: End date
            export_csv: Optional path to export CSV

        Returns:
            List of transactions
        """
        print("\n" + "=" * 70)
        print(f"ACCOUNT RECONCILIATION")
        print(f"Account: {account}")
        print(f"Period: {from_date} to {to_date}")
        print("=" * 70)

        # Get opening balance
        opening_entries = self.client.get_general_ledger(
            from_date="1900-01-01",
            to_date=from_date,
            account=account,
            company=self.company
        )

        opening_balance = sum(
            e.get('debit', 0) - e.get('credit', 0)
            for e in opening_entries
        )

        print(f"\nOpening Balance: {opening_balance:,.2f}")

        # Get period entries
        entries = self.client.get_general_ledger(
            from_date=from_date,
            to_date=to_date,
            account=account,
            company=self.company
        )

        # Display transactions
        print(f"\n{'Date':12} {'Voucher':20} {'Debit':>15} {'Credit':>15} {'Balance':>15}")
        print("-" * 80)

        running_balance = opening_balance
        transactions = []

        for entry in entries:
            date = entry['posting_date']
            voucher = entry['voucher_no']
            debit = entry.get('debit', 0)
            credit = entry.get('credit', 0)
            running_balance += (debit - credit)

            print(f"{date:12} {voucher:20} {debit:>15,.2f} {credit:>15,.2f} {running_balance:>15,.2f}")

            transactions.append({
                'date': date,
                'voucher': voucher,
                'voucher_type': entry.get('voucher_type', ''),
                'debit': debit,
                'credit': credit,
                'balance': running_balance,
                'against': entry.get('against', ''),
                'remarks': entry.get('remarks', '')
            })

        print("-" * 80)
        print(f"{'':12} {'Closing Balance:':20} {'':>15} {'':>15} {running_balance:>15,.2f}")

        # Export to CSV if requested
        if export_csv:
            with open(export_csv, 'w', newline='') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['date', 'voucher', 'voucher_type', 'debit', 'credit', 'balance', 'against', 'remarks']
                )
                writer.writeheader()
                writer.writerows(transactions)
            print(f"\n✓ Exported to {export_csv}")

        return transactions

    # ============================================================
    # MULTI-CURRENCY ANALYSIS
    # ============================================================

    def analyze_forex_exposure(
        self,
        as_of_date: str,
        base_currency: str = "INR"
    ) -> Dict[str, Any]:
        """
        Analyze foreign exchange exposure

        Args:
            as_of_date: Analysis date
            base_currency: Base currency for reporting

        Returns:
            Forex exposure analysis
        """
        print("\n" + "=" * 70)
        print(f"FOREX EXPOSURE ANALYSIS as of {as_of_date}")
        print(f"Base Currency: {base_currency}")
        print("=" * 70)

        # Get all accounts with foreign currencies
        foreign_accounts = self.client.list_accounts(
            filters={
                "company": self.company,
                "disabled": 0
            },
            limit_page_length=1000
        )

        # Filter for foreign currency accounts
        foreign_currency_accounts = [
            acc for acc in foreign_accounts
            if acc.get('account_currency') and acc.get('account_currency') != base_currency
        ]

        # Get balances
        gl_entries = self.client.get_general_ledger(
            from_date="1900-01-01",
            to_date=as_of_date,
            company=self.company
        )

        # Calculate balances by currency
        currency_balances = defaultdict(lambda: defaultdict(float))

        for entry in gl_entries:
            account = entry['account']
            # Find account details
            acc_details = next((a for a in foreign_currency_accounts if a['name'] == account), None)

            if acc_details:
                currency = acc_details.get('account_currency')
                balance = entry.get('debit', 0) - entry.get('credit', 0)
                currency_balances[currency][account] += balance

        # Display results
        print(f"\n{'Currency':10} {'Account':40} {'Balance':>15}")
        print("-" * 70)

        total_by_currency = defaultdict(float)

        for currency, accounts in currency_balances.items():
            print(f"\n{currency}")
            for account, balance in accounts.items():
                if balance != 0:
                    # Find account name
                    acc_name = next(
                        (a['account_name'] for a in foreign_currency_accounts if a['name'] == account),
                        account
                    )
                    print(f"{'':10} {acc_name:40} {balance:>15,.2f}")
                    total_by_currency[currency] += balance

            print(f"{'':10} {'-' * 40} {'-' * 15}")
            print(f"{'':10} {'Total':40} {total_by_currency[currency]:>15,.2f}")

        print("\n" + "=" * 70)
        print("SUMMARY BY CURRENCY")
        print("-" * 70)
        for currency, total in total_by_currency.items():
            print(f"{currency:10} {total:>15,.2f}")

        return {
            'as_of_date': as_of_date,
            'base_currency': base_currency,
            'currency_balances': dict(currency_balances),
            'totals': dict(total_by_currency)
        }


# ============================================================
# ACCOUNT HIERARCHY MANAGER
# ============================================================

class AccountHierarchyManager:
    """
    Manage account hierarchy and structure
    """

    def __init__(self, client: ERPNextClient, company: str):
        self.client = client
        self.company = company

    def display_hierarchy(self, root_type: Optional[str] = None):
        """
        Display account hierarchy as a tree

        Args:
            root_type: Filter by root type (Asset, Liability, etc.)
        """
        filters = {"company": self.company, "disabled": 0}
        if root_type:
            filters["root_type"] = root_type

        accounts = self.client.list_accounts(
            filters=filters,
            order_by="lft asc",  # Tree traversal order
            limit_page_length=1000
        )

        print("\n" + "=" * 70)
        print(f"ACCOUNT HIERARCHY - {root_type or 'All Types'}")
        print("=" * 70 + "\n")

        # Build tree
        tree = self._build_tree(accounts)

        # Display tree
        self._print_tree(tree)

    def _build_tree(self, accounts: List[Dict]) -> List[Dict]:
        """Build hierarchical tree structure"""
        account_map = {acc['name']: {**acc, 'children': []} for acc in accounts}

        root_accounts = []

        for account in accounts:
            parent = account.get('parent_account')
            if parent and parent in account_map:
                account_map[parent]['children'].append(account_map[account['name']])
            else:
                root_accounts.append(account_map[account['name']])

        return root_accounts

    def _print_tree(self, nodes: List[Dict], level: int = 0):
        """Recursively print tree structure"""
        for node in nodes:
            indent = "  " * level
            is_group = "📁" if node.get('is_group') else "📄"
            acc_num = f"[{node.get('account_number')}]" if node.get('account_number') else ""
            currency = f"({node.get('account_currency')})" if node.get('account_currency') else ""

            print(f"{indent}{is_group} {node['account_name']} {acc_num} {currency}")

            if node.get('children'):
                self._print_tree(node['children'], level + 1)

    def move_account(
        self,
        account_name: str,
        new_parent: str
    ) -> Dict:
        """
        Move account to a different parent

        Args:
            account_name: Account to move
            new_parent: New parent account

        Returns:
            Updated account details
        """
        print(f"\nMoving account: {account_name}")
        print(f"New parent: {new_parent}")

        result = self.client.update_account(
            account_name=account_name,
            updates={"parent_account": new_parent}
        )

        print("✓ Account moved successfully")
        return result


# ============================================================
# USAGE EXAMPLES
# ============================================================

if __name__ == "__main__":
    """
    Example usage of advanced reporting tools
    """

    # Configure ERPNext connection
    config = ERPNextConfig(
        base_url="https://your-instance.erpnext.com",
        api_key="your_api_key",
        api_secret="your_api_secret"
    )

    client = ERPNextClient(config)

    # Create reporter
    reporter = ERPNextReporter(client, "PearlThoughts")

    # Create hierarchy manager
    hierarchy_manager = AccountHierarchyManager(client, "PearlThoughts")

    # Generate reports
    print("\n" + "=" * 70)
    print("ERPNEXT ADVANCED REPORTING")
    print("=" * 70)

    # Uncomment the reports you want to generate

    # 1. Trial Balance
    # reporter.generate_trial_balance(
    #     from_date="2025-07-01",
    #     to_date="2025-07-31"
    # )

    # 2. Profit & Loss
    # reporter.generate_profit_loss(
    #     from_date="2025-07-01",
    #     to_date="2025-07-31"
    # )

    # 3. Balance Sheet
    # reporter.generate_balance_sheet(
    #     as_of_date="2025-07-31"
    # )

    # 4. Account Reconciliation
    # reporter.reconcile_account(
    #     account="ICICI Bank - PT",
    #     from_date="2025-07-01",
    #     to_date="2025-07-31",
    #     export_csv="icici_reconciliation.csv"
    # )

    # 5. Forex Exposure Analysis
    # reporter.analyze_forex_exposure(
    #     as_of_date="2025-07-31"
    # )

    # 6. Account Hierarchy
    # hierarchy_manager.display_hierarchy(root_type="Asset")

    print("\n✓ Reporting examples completed!")
    print("\nUncomment the functions in __main__ to run specific reports")
