"""
ERPNext API Quick Start Script

This interactive script helps you get started with ERPNext accounting operations.

Run this after creating your config.py file.
"""

import sys
from datetime import datetime, timedelta


def main_menu():
    """Display main menu and get user choice"""
    print("\n" + "=" * 70)
    print("ERPNext Accounting API - Quick Start")
    print("=" * 70)
    print("\n1. Test Connection")
    print("2. View Chart of Accounts")
    print("3. Create Sample Journal Entry")
    print("4. View Recent Journal Entries")
    print("5. Generate Trial Balance")
    print("6. Migrate from Beancount (Dry Run)")
    print("7. Account Hierarchy")
    print("8. Account Reconciliation")
    print("9. Exit")

    choice = input("\nSelect an option (1-9): ").strip()
    return choice


def test_connection():
    """Test ERPNext API connection"""
    print("\n" + "=" * 70)
    print("Testing ERPNext Connection")
    print("=" * 70)

    try:
        from config import config, COMPANY, validate_config
        from erpnext_client import ERPNextClient

        # Validate config
        validate_config()

        # Create client
        client = ERPNextClient(config)

        # Test API call
        response = client._make_request(
            "GET",
            "/api/method/frappe.auth.get_logged_user"
        )

        print(f"\n✓ Connection successful!")
        print(f"✓ Logged in as: {response.get('message')}")
        print(f"✓ Company: {COMPANY}")

        # Test account access
        accounts = client.list_accounts(
            filters={"company": COMPANY},
            limit_page_length=5
        )

        print(f"✓ Found {len(accounts)} accounts (showing first 5)")

        return True

    except ImportError:
        print("\n✗ Error: config.py not found!")
        print("Please create config.py from config_template.py")
        return False
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your ERPNext URL in config.py")
        print("2. Verify API keys are correct")
        print("3. Ensure you have network access to ERPNext")
        return False


def view_chart_of_accounts():
    """View chart of accounts"""
    print("\n" + "=" * 70)
    print("Chart of Accounts")
    print("=" * 70)

    try:
        from config import config, COMPANY
        from erpnext_client import ERPNextClient

        client = ERPNextClient(config)

        # Get account type filter
        print("\nFilter by type:")
        print("1. All")
        print("2. Assets")
        print("3. Liabilities")
        print("4. Income")
        print("5. Expenses")
        print("6. Equity")

        choice = input("Select (1-6): ").strip()

        type_map = {
            '1': None,
            '2': 'Asset',
            '3': 'Liability',
            '4': 'Income',
            '5': 'Expense',
            '6': 'Equity'
        }

        root_type = type_map.get(choice)

        filters = {"company": COMPANY, "disabled": 0}
        if root_type:
            filters["root_type"] = root_type

        accounts = client.list_accounts(
            filters=filters,
            limit_page_length=100
        )

        print(f"\n{'Account Number':15} {'Account Name':40} {'Type':15} {'Currency':10}")
        print("-" * 82)

        for acc in accounts:
            acc_num = acc.get('account_number', 'N/A')
            acc_name = acc['account_name'][:40]
            acc_type = acc.get('account_type', 'N/A')[:15]
            currency = acc.get('account_currency', 'N/A')

            print(f"{acc_num:15} {acc_name:40} {acc_type:15} {currency:10}")

        print(f"\nTotal accounts: {len(accounts)}")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def create_sample_journal_entry():
    """Create a sample journal entry"""
    print("\n" + "=" * 70)
    print("Create Sample Journal Entry")
    print("=" * 70)

    try:
        from config import config, COMPANY
        from erpnext_client import ERPNextClient, validate_journal_entry

        client = ERPNextClient(config)

        print("\nThis will create a sample journal entry.")
        print("Example: Cash payment for expenses")

        # Get date
        date_str = input("\nPosting date (YYYY-MM-DD) [default: today]: ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # Get accounts (you should customize these)
        print("\nEnter account names (or press Enter for defaults):")
        debit_account = input(f"Debit account [Expenses - {COMPANY}]: ").strip()
        if not debit_account:
            debit_account = f"Expenses - {COMPANY}"

        credit_account = input(f"Credit account [Cash - {COMPANY}]: ").strip()
        if not credit_account:
            credit_account = f"Cash - {COMPANY}"

        amount = float(input("Amount: ").strip())
        description = input("Description: ").strip()

        # Create journal entry
        accounts = [
            {
                "account": debit_account,
                "debit_in_account_currency": amount,
                "credit_in_account_currency": 0
            },
            {
                "account": credit_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount
            }
        ]

        # Validate
        validate_journal_entry(accounts)

        # Confirm
        print("\n" + "-" * 70)
        print(f"Date: {date_str}")
        print(f"Debit: {debit_account} = {amount:,.2f}")
        print(f"Credit: {credit_account} = {amount:,.2f}")
        print(f"Description: {description}")
        print("-" * 70)

        confirm = input("\nCreate this entry? (y/n): ").strip().lower()

        if confirm == 'y':
            result = client.create_journal_entry(
                posting_date=date_str,
                company=COMPANY,
                user_remark=description,
                accounts=accounts
            )

            print(f"\n✓ Journal entry created: {result['name']}")
            print(f"  Status: Draft")
            print(f"  Total Debit: {result.get('total_debit', 0):,.2f}")
            print(f"  Total Credit: {result.get('total_credit', 0):,.2f}")
            print("\nNote: Entry is in DRAFT status. Submit it in ERPNext UI to post to ledger.")
        else:
            print("\nCancelled.")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def view_recent_journal_entries():
    """View recent journal entries"""
    print("\n" + "=" * 70)
    print("Recent Journal Entries")
    print("=" * 70)

    try:
        from config import config, COMPANY
        from erpnext_client import ERPNextClient

        client = ERPNextClient(config)

        # Get date range
        days = input("\nShow entries from last N days [default: 30]: ").strip()
        if not days:
            days = 30
        else:
            days = int(days)

        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        entries = client.list_journal_entries(
            filters={
                "posting_date": [">=", from_date],
                "company": COMPANY
            },
            limit_page_length=20
        )

        print(f"\n{'Date':12} {'ID':20} {'Type':15} {'Status':10} {'Debit':>15}")
        print("-" * 75)

        for entry in entries:
            date = entry.get('posting_date', '')
            name = entry.get('name', '')
            vtype = entry.get('voucher_type', '')[:15]
            status = ['Draft', 'Submitted', 'Cancelled'][entry.get('docstatus', 0)]
            debit = entry.get('total_debit', 0)

            print(f"{date:12} {name:20} {vtype:15} {status:10} {debit:>15,.2f}")

        print(f"\nTotal entries: {len(entries)}")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def generate_trial_balance():
    """Generate trial balance"""
    print("\n" + "=" * 70)
    print("Generate Trial Balance")
    print("=" * 70)

    try:
        from config import config, COMPANY
        from erpnext_client import ERPNextClient
        from advanced_reporting import ERPNextReporter

        client = ERPNextClient(config)
        reporter = ERPNextReporter(client, COMPANY)

        # Get date range
        print("\nEnter date range:")
        from_date = input("From date (YYYY-MM-DD): ").strip()
        to_date = input("To date (YYYY-MM-DD): ").strip()

        if not from_date or not to_date:
            print("Both dates are required")
            return

        # Generate report
        reporter.generate_trial_balance(
            from_date=from_date,
            to_date=to_date
        )

    except Exception as e:
        print(f"\n✗ Error: {e}")


def migrate_from_beancount():
    """Migrate from beancount (dry run)"""
    print("\n" + "=" * 70)
    print("Migrate from Beancount (Dry Run)")
    print("=" * 70)

    try:
        from config import config, COMPANY, COMPANY_SUFFIX
        from erpnext_client import ERPNextClient
        from beancount_to_erpnext import BeancountToERPNextMigrator

        client = ERPNextClient(config)

        # Get beancount file
        filepath = input("\nEnter path to beancount file: ").strip()

        if not filepath:
            print("File path is required")
            return

        # Create migrator
        migrator = BeancountToERPNextMigrator(
            client=client,
            company=COMPANY,
            company_suffix=COMPANY_SUFFIX
        )

        # Run dry run
        print("\nRunning in DRY RUN mode (no changes will be made)")
        print("Review the output to verify mappings are correct")

        migrator.migrate_from_file(
            filepath=filepath,
            dry_run=True,
            auto_submit=False
        )

        print("\n" + "=" * 70)
        print("Next steps:")
        print("1. Review the output above")
        print("2. Check account mappings in beancount_to_erpnext.py")
        print("3. If correct, edit the script to set dry_run=False")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error: {e}")


def view_account_hierarchy():
    """View account hierarchy"""
    print("\n" + "=" * 70)
    print("Account Hierarchy")
    print("=" * 70)

    try:
        from config import config, COMPANY
        from erpnext_client import ERPNextClient
        from advanced_reporting import AccountHierarchyManager

        client = ERPNextClient(config)
        hierarchy = AccountHierarchyManager(client, COMPANY)

        # Get root type
        print("\nSelect account type:")
        print("1. Assets")
        print("2. Liabilities")
        print("3. Income")
        print("4. Expenses")
        print("5. Equity")
        print("6. All")

        choice = input("Select (1-6): ").strip()

        type_map = {
            '1': 'Asset',
            '2': 'Liability',
            '3': 'Income',
            '4': 'Expense',
            '5': 'Equity',
            '6': None
        }

        root_type = type_map.get(choice)

        hierarchy.display_hierarchy(root_type=root_type)

    except Exception as e:
        print(f"\n✗ Error: {e}")


def account_reconciliation():
    """Account reconciliation"""
    print("\n" + "=" * 70)
    print("Account Reconciliation")
    print("=" * 70)

    try:
        from config import config, COMPANY
        from erpnext_client import ERPNextClient
        from advanced_reporting import ERPNextReporter

        client = ERPNextClient(config)
        reporter = ERPNextReporter(client, COMPANY)

        # Get account name
        account = input("\nEnter account name: ").strip()
        if not account:
            print("Account name is required")
            return

        # Get date range
        from_date = input("From date (YYYY-MM-DD): ").strip()
        to_date = input("To date (YYYY-MM-DD): ").strip()

        if not from_date or not to_date:
            print("Both dates are required")
            return

        # Ask about CSV export
        export = input("Export to CSV? (y/n): ").strip().lower()
        export_path = None
        if export == 'y':
            export_path = input("CSV filename [reconciliation.csv]: ").strip()
            if not export_path:
                export_path = "reconciliation.csv"

        # Generate reconciliation
        reporter.reconcile_account(
            account=account,
            from_date=from_date,
            to_date=to_date,
            export_csv=export_path
        )

    except Exception as e:
        print(f"\n✗ Error: {e}")


def main():
    """Main application loop"""
    print("\nWelcome to ERPNext Accounting API Quick Start!")

    while True:
        choice = main_menu()

        if choice == '1':
            test_connection()
        elif choice == '2':
            view_chart_of_accounts()
        elif choice == '3':
            create_sample_journal_entry()
        elif choice == '4':
            view_recent_journal_entries()
        elif choice == '5':
            generate_trial_balance()
        elif choice == '6':
            migrate_from_beancount()
        elif choice == '7':
            view_account_hierarchy()
        elif choice == '8':
            account_reconciliation()
        elif choice == '9':
            print("\nGoodbye!")
            sys.exit(0)
        else:
            print("\nInvalid choice. Please select 1-9.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
