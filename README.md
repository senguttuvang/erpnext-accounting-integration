# ERPNext Accounting Integration Guide

> **A comprehensive architectural guide and reference implementation for integrating ERPNext with external accounting systems and workflows**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![ERPNext Compatible](https://img.shields.io/badge/ERPNext-v14%2B-green.svg)](https://erpnext.com/)

## 🎯 Purpose

This repository serves as a **practical guide and architectural reference** for anyone looking to:

- **Integrate ERPNext** with external business systems and workflows
- **Understand ERPNext's Accounting Module** from an integration perspective
- **Migrate from other accounting systems** (with Beancount as a concrete example)
- **Build custom accounting workflows** using ERPNext's REST API
- **Learn system design patterns** for ERP integration

## 🤔 Why This Guide?

ERPNext's official documentation focuses on generic DocType operations, which can be challenging when working with specialized modules like **Accounting**. This guide bridges that gap by providing:

✅ **Concrete examples** based on real-world accounting scenarios
✅ **Multi-currency operations** with forex gain/loss handling
✅ **Account hierarchy management** and Chart of Accounts setup
✅ **Journal Entry workflows** (single & multi-currency)
✅ **Financial reporting** (Trial Balance, P&L, Balance Sheet)
✅ **Migration patterns** from existing accounting systems
✅ **System architecture** for ERP integration

## 📁 Repository Structure

```
ERPNext Integration Demo/
├── src/
│   ├── erpnext_client.py          # Core API client library
│   ├── examples/
│   │   ├── basic_operations.py    # CRUD operations for accounting
│   │   ├── multi_currency.py      # Multi-currency examples
│   │   └── bulk_operations.py     # Batch processing
│   ├── reporting/
│   │   ├── financial_reports.py   # Trial Balance, P&L, Balance Sheet
│   │   └── reconciliation.py      # Account reconciliation tools
│   └── migration/
│       └── beancount_migrator.py  # Example: Beancount → ERPNext
│
├── examples/
│   ├── sample_data/               # Sample accounting data
│   │   ├── it_services.beancount  # IT consulting business example
│   │   └── multi_method.beancount # Multiple revenue recognition methods
│   └── config_template.py         # Configuration template
│
├── docs/
│   ├── ARCHITECTURE.md            # System design and architecture
│   ├── API_GUIDE.md               # ERPNext API deep-dive for accounting
│   ├── MIGRATION.md               # Migration strategies and patterns
│   ├── COOKBOOK.md                # Common recipes and patterns
│   └── FAQ.md                     # Frequently asked questions
│
├── tests/
│   └── test_*.py                  # Unit tests
│
├── scripts/
│   └── quickstart.py              # Interactive quick-start tool
│
├── requirements.txt               # Python dependencies
├── LICENSE                        # MIT License
└── README.md                      # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- ERPNext instance (v14 or later)
- API credentials (API Key + API Secret)

### Installation

```bash
# Clone the repository
git clone https://github.com/senguttuvang/erpnext-accounting-integration.git
cd erpnext-accounting-integration

# Install dependencies
pip install -r requirements.txt

# Configure connection
cp examples/config_template.py config.py
# Edit config.py with your ERPNext URL and API credentials
```

### Quick Test

```bash
# Test your connection
python scripts/quickstart.py

# Or run examples directly
python -c "
from src.erpnext_client import ERPNextClient, ERPNextConfig

config = ERPNextConfig(
    base_url='https://your-instance.erpnext.com',
    api_key='your_key',
    api_secret='your_secret'
)

client = ERPNextClient(config)
accounts = client.list_accounts(limit_page_length=5)
print(f'✓ Connected! Found {len(accounts)} accounts')
"
```

## 📚 Documentation

### Core Concepts

1. **[Architecture Guide](docs/ARCHITECTURE.md)** - System design, integration patterns, best practices
2. **[API Deep-Dive](docs/API_GUIDE.md)** - ERPNext Accounting API from first principles
3. **[Migration Guide](docs/MIGRATION.md)** - Strategies for migrating from other systems
4. **[Cookbook](docs/COOKBOOK.md)** - Common patterns and recipes

### Use Cases

This guide covers real-world scenarios:

- **IT Services Business** - Project-based billing, multi-currency revenue
- **Multi-Currency Operations** - Forex gain/loss, exchange rate management
- **Platform Integration** - Payment processors, marketplace platforms
- **Revenue Recognition** - Multiple methods (cash, accrual, project completion)

## 🎓 Learning Path

### For Beginners

1. Start with **[Quick Start](#-quick-start)** above
2. Read **[API Guide](docs/API_GUIDE.md)** to understand ERPNext's accounting structure
3. Try **[Basic Examples](src/examples/basic_operations.py)**
4. Explore **[Cookbook](docs/COOKBOOK.md)** for common patterns

### For Integration Developers

1. Review **[Architecture Guide](docs/ARCHITECTURE.md)** for design patterns
2. Study the **[Migration Guide](docs/MIGRATION.md)** for your specific use case
3. Examine **[Beancount Migrator](src/migration/beancount_migrator.py)** as a reference implementation
4. Customize the **[Core Client](src/erpnext_client.py)** for your needs

### For ERPNext Administrators

1. Understand the **[Chart of Accounts](docs/API_GUIDE.md#chart-of-accounts)** setup
2. Learn **[Journal Entry](docs/API_GUIDE.md#journal-entries)** patterns
3. Use **[Financial Reports](src/reporting/financial_reports.py)** for analysis
4. Implement **[Reconciliation](src/reporting/reconciliation.py)** workflows

## 💡 Key Features

### 1. Comprehensive API Client

```python
from src.erpnext_client import ERPNextClient

client = ERPNextClient(config)

# Chart of Accounts
accounts = client.list_accounts(filters={"root_type": "Asset"})
account = client.create_account(
    account_name="Operating Cash",
    parent_account="Bank Accounts - CO",
    account_currency="USD"
)

# Journal Entries (Multi-Currency)
entry = client.create_journal_entry(
    posting_date="2024-11-01",
    company="Your Company",
    multi_currency=True,
    accounts=[
        {
            "account": "Revenue - USD - CO",
            "credit_in_account_currency": 10000,
            "account_currency": "USD",
            "exchange_rate": 83.50
        },
        {
            "account": "Accounts Receivable - CO",
            "debit_in_account_currency": 10000,
            "account_currency": "USD",
            "exchange_rate": 83.50
        }
    ]
)

# Financial Reports
from src.reporting.financial_reports import ERPNextReporter

reporter = ERPNextReporter(client, "Your Company")
trial_balance = reporter.generate_trial_balance("2024-01-01", "2024-12-31")
pl_statement = reporter.generate_profit_loss("2024-01-01", "2024-12-31")
```

### 2. Migration Framework

Example migration from Beancount (adaptable to any system):

```python
from src.migration.beancount_migrator import BeancountToERPNextMigrator

migrator = BeancountToERPNextMigrator(client, "Your Company", "CO")

# Dry run first
migrator.migrate_from_file("your_ledger.beancount", dry_run=True)

# Execute migration
migrator.migrate_from_file("your_ledger.beancount", dry_run=False)
```

### 3. Financial Reporting

```python
from src.reporting.financial_reports import ERPNextReporter

reporter = ERPNextReporter(client, "Your Company")

# Trial Balance
reporter.generate_trial_balance("2024-01-01", "2024-12-31")

# Profit & Loss
reporter.generate_profit_loss("2024-01-01", "2024-12-31")

# Balance Sheet
reporter.generate_balance_sheet("2024-12-31")

# Account Reconciliation
reporter.reconcile_account(
    account="Bank Account - CO",
    from_date="2024-11-01",
    to_date="2024-11-30",
    export_csv="reconciliation.csv"
)
```

## 🏗️ Architecture Highlights

### Design Principles

1. **Stateless Operations** - Each API call is independent
2. **Validation First** - All entries validated before posting
3. **Error Recovery** - Comprehensive error handling
4. **Dry-Run Mode** - Preview changes before committing
5. **Idempotent** - Safe to retry operations

### Integration Patterns

```
┌─────────────────┐
│ External System │
│  (Your App)     │
└────────┬────────┘
         │
         │ REST API
         │
    ┌────▼─────────────────┐
    │  ERPNext Client      │
    │  - Validation        │
    │  - Transformation    │
    │  - Error Handling    │
    └────┬─────────────────┘
         │
         │ HTTPS
         │
    ┌────▼─────────────────┐
    │  ERPNext Instance    │
    │  - Accounting Module │
    │  - GL Processing     │
    │  - Reports           │
    └──────────────────────┘
```

### Multi-Currency Flow

```
Revenue Recognition (USD) @ Rate 1
         │
         ▼
Journal Entry (multi_currency=True)
         │
         ├─► Account Receivable (USD)
         └─► Revenue (USD)

Cash Receipt (USD) @ Rate 2
         │
         ▼
Journal Entry (with forex)
         │
         ├─► Bank (Base Currency)
         ├─► Account Receivable (USD) @ Rate 1
         └─► Forex Gain/Loss (Base Currency)
```

## 🌟 Example Use Cases

### Use Case 1: IT Services Company

**Scenario:** Multi-currency project billing with platform fees

See: [`examples/sample_data/it_services.beancount`](examples/sample_data/it_services.beancount)

- Revenue in USD from international clients
- Operating expenses in INR (local currency)
- Platform fees (Upwork, Toptal, etc.)
- Forex gain/loss tracking

### Use Case 2: Multi-Method Revenue Recognition

**Scenario:** Compare different revenue recognition approaches

See: [`examples/sample_data/multi_method.beancount`](examples/sample_data/multi_method.beancount)

- Method A: Transaction posting date
- Method B: Invoice generation date (filtered scope)
- Method C: Invoice generation date (complete scope)
- Comparative analysis

### Use Case 3: E-commerce Integration

**Scenario:** Daily sales reconciliation from external platform

```python
# Pseudo-code for Shopify/WooCommerce integration
daily_sales = fetch_from_platform(date)

for order in daily_sales:
    client.create_journal_entry(
        posting_date=order.date,
        accounts=[
            {"account": "Sales", "credit": order.amount},
            {"account": "Platform Fees", "debit": order.fees},
            {"account": "Bank", "debit": order.net_amount}
        ]
    )
```

## 🔧 Answering the Community Question

**Original Question (2014):**
> *"Is there any API for integration to the accounting modules? We are looking at integrating another system... is there any 'convenient' function in the API that allows us provide the details and it will post the necessary entries to the various accounts?"*

**Answer (2024):**

Yes! ERPNext provides comprehensive REST APIs for accounting operations. Here's how:

### 1. Direct Journal Entry Posting

```python
# POST to /api/resource/Journal Entry
{
    "doctype": "Journal Entry",
    "posting_date": "2024-11-01",
    "company": "Your Company",
    "accounts": [
        {
            "account": "Expenses - CO",
            "debit_in_account_currency": 1000,
            "credit_in_account_currency": 0
        },
        {
            "account": "Cash - CO",
            "debit_in_account_currency": 0,
            "credit_in_account_currency": 1000
        }
    ]
}
```

### 2. Without Creating Duplicate Documents

You can post directly to GL without creating Purchase Orders, etc.:

```python
# Scenario: External PO system, just need accounting entries
client.create_journal_entry(
    posting_date="2024-11-01",
    company="Your Company",
    user_remark="From External PO#12345",
    accounts=[
        {"account": "Inventory", "debit": 10000},
        {"account": "Accounts Payable", "credit": 10000}
    ]
)
```

### 3. This Repository

This integration guide demonstrates:
- ✅ Direct GL posting without duplicate documents
- ✅ Multi-currency handling
- ✅ Batch operations
- ✅ Validation and error handling
- ✅ Migration from external systems

See **[API Guide](docs/API_GUIDE.md)** for complete details.

## 🤝 Contributing

This is an open-source educational resource. Contributions welcome!

### Ways to Contribute

- 📖 Improve documentation
- 🐛 Report bugs or issues
- 💡 Share your integration patterns
- 🔧 Add more examples
- 🌍 Translate documentation

### Guidelines

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ERPNext Team** - For building an amazing open-source ERP
- **Frappe Framework** - For the excellent REST API foundation
- **Beancount** - For inspiring clean accounting system design
- **Community** - For questions that drive better documentation

## 📞 Support

- 📚 **Documentation**: [docs/](docs/)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/senguttuvang/erpnext-accounting-integration/discussions)
- 🐛 **Issues**: [GitHub Issues](https://github.com/senguttuvang/erpnext-accounting-integration/issues)
- 🌐 **ERPNext Forum**: [discuss.frappe.io](https://discuss.frappe.io/)

## 🗺️ Roadmap

- [ ] Add more migration examples (QuickBooks, Xero, etc.)
- [ ] Video tutorials
- [ ] Docker-based demo environment
- [ ] Performance optimization guides
- [ ] Real-time sync patterns
- [ ] Webhook integration examples
- [ ] GraphQL adapter

---

**Built with ❤️ for the ERPNext community**

*Making ERP integration accessible to everyone*
