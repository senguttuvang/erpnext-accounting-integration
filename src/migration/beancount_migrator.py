"""
Beancount to ERPNext Migration Tool
Parses beancount files and creates corresponding entries in ERPNext

This tool helps migrate your existing beancount accounting to ERPNext
"""

import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from decimal import Decimal
from erpnext_client import ERPNextClient, ERPNextConfig, validate_journal_entry
import json


class BeancountParser:
    """
    Parser for beancount ledger files
    Extracts transactions and converts them to ERPNext format
    """

    def __init__(self):
        self.accounts = {}
        self.commodities = set()
        self.transactions = []
        self.prices = {}
        self.opening_balances = {}

    def parse_file(self, filepath: str):
        """Parse a beancount file"""
        with open(filepath, 'r') as f:
            content = f.read()

        self._parse_commodities(content)
        self._parse_accounts(content)
        self._parse_prices(content)
        self._parse_transactions(content)

    def _parse_commodities(self, content: str):
        """Extract commodity definitions"""
        pattern = r'^\d{4}-\d{2}-\d{2}\s+commodity\s+(\w+)'
        for match in re.finditer(pattern, content, re.MULTILINE):
            self.commodities.add(match.group(1))

    def _parse_accounts(self, content: str):
        """Extract account definitions"""
        # Pattern: 1960-01-01 open Assets:Cash:ICICI INR
        pattern = r'^\d{4}-\d{2}-\d{2}\s+open\s+([\w:]+)(?:\s+(\w+))?'
        for match in re.finditer(pattern, content, re.MULTILINE):
            account_name = match.group(1)
            currency = match.group(2) if match.group(2) else None
            self.accounts[account_name] = {
                'name': account_name,
                'currency': currency,
                'type': self._classify_account(account_name)
            }

    def _classify_account(self, account_name: str) -> str:
        """Classify account based on name"""
        if account_name.startswith('Assets:'):
            if 'Cash' in account_name or 'Bank' in account_name:
                return 'Bank'
            elif 'Receivable' in account_name:
                return 'Receivable'
            else:
                return 'Asset'
        elif account_name.startswith('Liabilities:'):
            if 'Payable' in account_name:
                return 'Payable'
            else:
                return 'Liability'
        elif account_name.startswith('Income:'):
            return 'Income'
        elif account_name.startswith('Expenses:'):
            return 'Expense'
        elif account_name.startswith('Equity:'):
            return 'Equity'
        else:
            return 'Unknown'

    def _parse_prices(self, content: str):
        """Extract price/exchange rate definitions"""
        # Pattern: 2025-07-31 price USD 84.20 INR
        pattern = r'^(\d{4}-\d{2}-\d{2})\s+price\s+(\w+)\s+([\d.]+)\s+(\w+)'
        for match in re.finditer(pattern, content, re.MULTILINE):
            date = match.group(1)
            from_curr = match.group(2)
            rate = float(match.group(3))
            to_curr = match.group(4)

            if date not in self.prices:
                self.prices[date] = {}
            self.prices[date][from_curr] = {'rate': rate, 'to': to_curr}

    def _parse_transactions(self, content: str):
        """Extract transactions"""
        # Split content into transaction blocks
        # Pattern: date * "description" followed by postings
        pattern = r'^(\d{4}-\d{2}-\d{2})\s+\*\s+"([^"]+)"\s*\n((?:^\s+.+\n)*)'

        for match in re.finditer(pattern, content, re.MULTILINE):
            date = match.group(1)
            description = match.group(2)
            postings_text = match.group(3)

            postings = self._parse_postings(postings_text)

            self.transactions.append({
                'date': date,
                'description': description,
                'postings': postings
            })

    def _parse_postings(self, postings_text: str) -> List[Dict]:
        """Parse individual postings from transaction"""
        postings = []

        # Pattern for posting line: account amount currency @ rate currency
        # Examples:
        #   Assets:Cash                 500000.00 INR
        #   Income:ClientServices       -23000.00 USD
        #   Assets:AccountsReceivable   -20683.55 USD @ 78.20 INR

        lines = postings_text.strip().split('\n')
        for line in lines:
            # Skip comment lines
            if line.strip().startswith(';'):
                continue

            # Parse posting
            parts = line.strip().split()
            if len(parts) < 2:
                continue

            account = parts[0]

            # Handle amount and currency
            amount_str = parts[1] if len(parts) > 1 else None
            currency = parts[2] if len(parts) > 2 else None

            # Handle exchange rate
            exchange_rate = None
            target_currency = None
            if len(parts) > 3 and parts[3] == '@':
                exchange_rate = float(parts[4]) if len(parts) > 4 else None
                target_currency = parts[5] if len(parts) > 5 else None

            # Parse amount
            if amount_str:
                amount = float(amount_str.replace(',', ''))
            else:
                amount = 0

            posting = {
                'account': account,
                'amount': amount,
                'currency': currency,
                'exchange_rate': exchange_rate,
                'target_currency': target_currency
            }

            postings.append(posting)

        return postings

    def get_account_mapping(self, beancount_account: str, company_suffix: str) -> str:
        """
        Map beancount account names to ERPNext account names

        Args:
            beancount_account: Account name from beancount (e.g., Assets:Cash:ICICI)
            company_suffix: Company suffix for ERPNext (e.g., "PT")

        Returns:
            ERPNext account name
        """
        # Mapping rules
        mappings = {
            'Assets:Cash:ICICI': f'ICICI Bank - {company_suffix}',
            'Assets:Cash:RazorpayX': f'RazorpayX - {company_suffix}',
            'Assets:AccountsReceivable': f'Accounts Receivable - USD - {company_suffix}',
            'Assets:Upwork:Escrow:Mainland:1851': f'Upwork Escrow - Mainland - {company_suffix}',
            'Assets:Upwork:Escrow:Accel:Ticketing': f'Upwork Escrow - Accel - {company_suffix}',
            'Assets:Upwork:Escrow:P2P:General': f'Upwork Escrow - P2P - {company_suffix}',

            'Liabilities:CreditCard:ICICI': f'ICICI Credit Card - {company_suffix}',
            'Liabilities:CreditCard:SBI': f'SBI Credit Card - {company_suffix}',

            'Income:ClientServices': f'Client Services Revenue - {company_suffix}',
            'Income:ForexGain': f'Exchange Gain/Loss - {company_suffix}',
            'Income:MethodA:Total': f'Revenue Method A - {company_suffix}',
            'Income:MethodB:Total': f'Revenue Method B - {company_suffix}',
            'Income:MethodC:Total': f'Revenue Method C - {company_suffix}',

            'Expenses:Platform:Upwork:ServiceFees': f'Upwork Platform Fees - {company_suffix}',
            'Expenses:Platform:Upwork:WHT': f'Upwork Withholding Tax - {company_suffix}',
            'Expenses:Salaries:TeamCompensation': f'Salaries - {company_suffix}',
            'Expenses:Operations:General': f'Operations Expenses - {company_suffix}',
            'Expenses:Technology:General': f'Technology Expenses - {company_suffix}',

            'Equity:Opening-Balances': f'Equity Opening Balance - {company_suffix}',
        }

        # Try exact match first
        if beancount_account in mappings:
            return mappings[beancount_account]

        # Try partial matches
        for bean_acc, erp_acc in mappings.items():
            if beancount_account.startswith(bean_acc):
                return erp_acc

        # Default: convert colons to hyphens and add company suffix
        return f"{beancount_account.replace(':', ' - ')} - {company_suffix}"


class BeancountToERPNextMigrator:
    """
    Migrate beancount ledger to ERPNext
    """

    def __init__(self, client: ERPNextClient, company: str, company_suffix: str):
        self.client = client
        self.company = company
        self.company_suffix = company_suffix
        self.parser = BeancountParser()

    def migrate_from_file(
        self,
        filepath: str,
        dry_run: bool = True,
        auto_submit: bool = False
    ):
        """
        Migrate transactions from beancount file to ERPNext

        Args:
            filepath: Path to beancount file
            dry_run: If True, print what would be done without creating entries
            auto_submit: If True, automatically submit journal entries
        """
        print("=" * 70)
        print(f"Migrating from: {filepath}")
        print(f"Company: {self.company}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print("=" * 70)

        # Parse beancount file
        self.parser.parse_file(filepath)

        print(f"\nParsed:")
        print(f"  Accounts: {len(self.parser.accounts)}")
        print(f"  Transactions: {len(self.parser.transactions)}")
        print(f"  Commodities: {', '.join(self.parser.commodities)}")
        print()

        # Migrate accounts
        print("\nStep 1: Creating Accounts")
        print("-" * 70)
        self._migrate_accounts(dry_run)

        # Migrate transactions
        print("\nStep 2: Creating Journal Entries")
        print("-" * 70)
        self._migrate_transactions(dry_run, auto_submit)

        print("\n" + "=" * 70)
        print("Migration Complete!")
        print("=" * 70)

    def _migrate_accounts(self, dry_run: bool):
        """Create accounts in ERPNext"""
        for account_name, account_data in self.parser.accounts.items():
            erp_account_name = self.parser.get_account_mapping(
                account_name,
                self.company_suffix
            )

            # Determine parent account
            parts = account_name.split(':')
            if len(parts) > 1:
                parent_bean = ':'.join(parts[:-1])
                parent_erp = self.parser.get_account_mapping(
                    parent_bean,
                    self.company_suffix
                )
            else:
                parent_erp = f"{account_data['type']} - {self.company_suffix}"

            print(f"\n{account_name}")
            print(f"  → ERPNext: {erp_account_name}")
            print(f"  → Parent: {parent_erp}")
            print(f"  → Type: {account_data['type']}")
            print(f"  → Currency: {account_data.get('currency', 'INR')}")

            if not dry_run:
                try:
                    # Check if account exists
                    existing = None
                    try:
                        existing = self.client.get_account(erp_account_name)
                    except:
                        pass

                    if existing:
                        print(f"  ✓ Account already exists")
                    else:
                        # Create account
                        result = self.client.create_account(
                            account_name=erp_account_name,
                            parent_account=parent_erp,
                            account_type=account_data['type'] if account_data['type'] not in ['Asset', 'Liability', 'Equity'] else None,
                            account_currency=account_data.get('currency', 'INR'),
                            company=self.company
                        )
                        print(f"  ✓ Created account")
                except Exception as e:
                    print(f"  ✗ Error: {e}")

    def _migrate_transactions(self, dry_run: bool, auto_submit: bool):
        """Create journal entries in ERPNext"""
        created_count = 0
        error_count = 0

        for txn in self.parser.transactions:
            print(f"\n{txn['date']} - {txn['description']}")

            # Convert postings to ERPNext format
            accounts = []
            has_forex = False

            for posting in txn['postings']:
                bean_account = posting['account']
                erp_account = self.parser.get_account_mapping(
                    bean_account,
                    self.company_suffix
                )

                amount = posting['amount']
                currency = posting.get('currency', 'INR')
                exchange_rate = posting.get('exchange_rate')

                # Determine debit/credit
                # In beancount, negative amount = credit, positive = debit
                # But for certain account types (Income, Liabilities), it's reversed
                account_type = self.parser.accounts.get(bean_account, {}).get('type', '')

                if account_type in ['Income', 'Liability', 'Equity']:
                    # Reversed for these account types
                    if amount < 0:
                        debit = abs(amount)
                        credit = 0
                    else:
                        debit = 0
                        credit = amount
                else:
                    # Normal for Assets, Expenses
                    if amount >= 0:
                        debit = amount
                        credit = 0
                    else:
                        debit = 0
                        credit = abs(amount)

                account_entry = {
                    'account': erp_account,
                    'debit_in_account_currency': debit,
                    'credit_in_account_currency': credit
                }

                # Add currency info if not INR
                if currency != 'INR':
                    account_entry['account_currency'] = currency
                    has_forex = True

                    # Add exchange rate if specified
                    if exchange_rate:
                        account_entry['exchange_rate'] = exchange_rate
                    elif txn['date'] in self.parser.prices and currency in self.parser.prices[txn['date']]:
                        account_entry['exchange_rate'] = self.parser.prices[txn['date']][currency]['rate']

                accounts.append(account_entry)

                print(f"  {erp_account}")
                print(f"    Debit: {debit:>12,.2f} {currency}")
                print(f"    Credit: {credit:>12,.2f} {currency}")

            # Validate
            try:
                validate_journal_entry(accounts)
                print(f"  ✓ Balanced")
            except ValueError as e:
                print(f"  ✗ Not balanced: {e}")
                error_count += 1
                continue

            # Create journal entry
            if not dry_run:
                try:
                    result = self.client.create_journal_entry(
                        posting_date=txn['date'],
                        company=self.company,
                        user_remark=txn['description'],
                        accounts=accounts,
                        multi_currency=has_forex
                    )

                    print(f"  ✓ Created: {result['name']}")

                    # Submit if requested
                    if auto_submit:
                        submit_result = self.client.submit_journal_entry(result['name'])
                        print(f"  ✓ Submitted")

                    created_count += 1

                except Exception as e:
                    print(f"  ✗ Error creating entry: {e}")
                    error_count += 1

        print(f"\nSummary:")
        print(f"  Created: {created_count}")
        print(f"  Errors: {error_count}")


# ============================================================
# USAGE EXAMPLE
# ============================================================

if __name__ == "__main__":
    """
    Example usage of beancount to ERPNext migrator
    """

    # Configure ERPNext connection
    config = ERPNextConfig(
        base_url="https://your-instance.erpnext.com",
        api_key="your_api_key",
        api_secret="your_api_secret"
    )

    client = ERPNextClient(config)

    # Create migrator
    migrator = BeancountToERPNextMigrator(
        client=client,
        company="PearlThoughts",
        company_suffix="PT"
    )

    # Migrate from beancount file
    # Set dry_run=True to preview without making changes
    # Set dry_run=False to actually create entries
    # Set auto_submit=True to automatically submit entries

    migrator.migrate_from_file(
        filepath="/Users/SenG/Projects/PearlThoughts-Org/Finance/Accounting/pearlthoughts.beancount",
        dry_run=True,  # Start with dry run
        auto_submit=False
    )

    print("\n" + "=" * 70)
    print("Next Steps:")
    print("1. Review the output above")
    print("2. If everything looks correct, set dry_run=False")
    print("3. Run again to create actual entries")
    print("4. Optionally set auto_submit=True to auto-submit entries")
    print("=" * 70)
