# ERPNext Accounting Integration - Architecture Guide

This document provides a comprehensive architectural overview of integrating external systems with ERPNext's Accounting module.

## Table of Contents

- [System Overview](#system-overview)
- [Design Principles](#design-principles)
- [Integration Patterns](#integration-patterns)
- [Data Flow](#data-flow)
- [Multi-Currency Architecture](#multi-currency-architecture)
- [Error Handling Strategy](#error-handling-strategy)
- [Performance Considerations](#performance-considerations)
- [Security & Authentication](#security--authentication)

---

## System Overview

###  High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    External System(s)                        │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────┐       │
│  │   Your     │  │  Payment   │  │   Accounting    │       │
│  │   App      │  │  Platform  │  │   System        │       │
│  └──────┬─────┘  └──────┬─────┘  └────────┬────────┘       │
│         │                │                  │                │
└─────────┼────────────────┼──────────────────┼────────────────┘
          │                │                  │
          └────────────────┴──────────────────┘
                           │
                     REST API (HTTPS)
                           │
          ┌────────────────▼──────────────────┐
          │    Integration Layer (This Repo)  │
          │  ┌──────────────────────────────┐ │
          │  │   ERPNext API Client         │ │
          │  │  - Request Building          │ │
          │  │  - Validation                │ │
          │  │  - Error Handling            │ │
          │  │  - Retry Logic               │ │
          │  └──────────┬───────────────────┘ │
          │             │                      │
          │  ┌──────────▼───────────────────┐ │
          │  │   Business Logic Layer       │ │
          │  │  - Account Mapping           │ │
          │  │  - Forex Calculations        │ │
          │  │  - Entry Validation          │ │
          │  └──────────┬───────────────────┘ │
          └─────────────┼──────────────────────┘
                        │
                  REST API Call
                        │
          ┌─────────────▼──────────────────┐
          │      ERPNext Instance          │
          │  ┌──────────────────────────┐  │
          │  │  Frappe Framework        │  │
          │  │  - API Endpoint Handler  │  │
          │  │  - Authentication        │  │
          │  │  - Permissions           │  │
          │  └──────────┬───────────────┘  │
          │             │                   │
          │  ┌──────────▼───────────────┐  │
          │  │  ERPNext Accounting      │  │
          │  │  - DocType Processing    │  │
          │  │  │  GL Entry Posting      │  │
          │  │  - Ledger Updates        │  │
          │  └──────────┬───────────────┘  │
          │             │                   │
          │  ┌──────────▼───────────────┐  │
          │  │      MariaDB/Postgres    │  │
          │  │  - Accounts Table        │  │
          │  │  - Journal Entry Table   │  │
          │  │  - GL Entry Table        │  │
          │  └──────────────────────────┘  │
          └────────────────────────────────┘
```

---

## Design Principles

### 1. **Stateless Operations**

Each API call should be independent and self-contained.

```python
# Good: Self-contained operation
client.create_journal_entry(
    posting_date="2024-11-01",
    company="MyCompany",
    accounts=[...]  # All data provided
)

# Avoid: Stateful operations that depend on previous calls
# (unless explicitly modeling a transaction sequence)
```

**Benefits:**
- Easy to retry failed operations
- Simple error recovery
- Horizontal scaling possible
- No session management complexity

### 2. **Validation First**

Validate all data before making API calls.

```python
# Validate journal entry balance
validate_journal_entry(accounts)  # Raises error if not balanced

# Then create
client.create_journal_entry(...)
```

**Validation Checklist:**
- [ ] Debits equal credits
- [ ] All required fields present
- [ ] Accounts exist in Chart of Accounts
- [ ] Dates are valid
- [ ] Currency codes are correct
- [ ] Exchange rates provided for forex

### 3. **Idempotent Operations**

Design operations to be safely retryable.

```python
# Use unique identifiers/references
client.create_journal_entry(
    posting_date="2024-11-01",
    user_remark="External-Ref: INV-2024-001",  # Unique reference
    accounts=[...]
)

# Before creating, check if already exists
existing = client.list_journal_entries(
    filters={"user_remark": ["like", "%External-Ref: INV-2024-001%"]}
)
if not existing:
    # Safe to create
    client.create_journal_entry(...)
```

### 4. **Fail-Fast Strategy**

Detect errors early before making changes.

```python
# Check all prerequisites first
if not account_exists(debit_account):
    raise ValueError(f"Account {debit_account} not found")

if not account_exists(credit_account):
    raise ValueError(f"Account {credit_account} not found")

# Only then proceed
create_entry(...)
```

### 5. **Dry-Run Capability**

Always provide a preview/dry-run mode.

```python
def migrate_transactions(data, dry_run=True):
    for transaction in data:
        print(f"Would create: {transaction}")

        if not dry_run:
            actual_create(transaction)
```

---

## Integration Patterns

### Pattern 1: Direct GL Posting

**Use Case:** Post accounting entries without creating source documents (PO, Invoice, etc.)

```python
# Scenario: External PO system, need only GL entries
client.create_journal_entry(
    posting_date="2024-11-01",
    user_remark="From External PO #12345",
    accounts=[
        {"account": "Inventory", "debit": 10000},
        {"account": "Accounts Payable", "credit": 10000}
    ]
)
```

**Pros:**
- Simple integration
- No duplicate data entry
- Fast execution

**Cons:**
- Loses some ERPNext features (PO tracking, etc.)
- Need external reference management

**Best For:**
- Systems already handling workflows
- Simple GL-only requirements
- High-volume batch processing

### Pattern 2: Document + GL Posting

**Use Case:** Create both ERPNext documents and GL entries

```python
# Create Purchase Order
po = client.create_document(
    doctype="Purchase Order",
    data={...}
)

# Submit (triggers GL posting)
client.submit_document("Purchase Order", po['name'])
```

**Pros:**
- Full ERPNext features
- Built-in workflows
- Audit trail

**Cons:**
- More complex integration
- Slower execution
- Need to understand ERPNext doctypes

**Best For:**
- Green-field implementations
- Want full ERP features
- Smaller transaction volumes

### Pattern 3: Hybrid Approach

**Use Case:** Mix of both patterns

```python
# High-volume daily sales: Direct GL
create_daily_sales_summary_entry(...)

# Complex purchases: Full document flow
create_purchase_order_with_approval_workflow(...)
```

### Pattern 4: Batch Processing

**Use Case:** Process multiple transactions efficiently

```python
# Collect all transactions
batch = []
for transaction in daily_transactions:
    entry = build_journal_entry(transaction)
    batch.append(entry)

# Validate all
for entry in batch:
    validate_journal_entry(entry['accounts'])

# Process all
for entry in batch:
    try:
        result = client.create_journal_entry(**entry)
        log_success(result)
    except Exception as e:
        log_error(entry, e)
        # Continue with next (don't fail entire batch)
```

**Key Considerations:**
- Transaction isolation
- Error handling per item
- Logging and reporting
- Recovery procedures

---

## Data Flow

### Journal Entry Creation Flow

```
External System
       │
       ▼
   Build Entry
   - Map accounts
   - Calculate amounts
   - Set currencies
   - Determine forex
       │
       ▼
   Validate
   - Check balance
   - Verify accounts exist
   - Validate dates
   - Check permissions
       │
       ▼
   API Call
   POST /api/resource/Journal Entry
       │
       ▼
   ERPNext Processing
   - Create JE document (draft)
   - Docstatus = 0
       │
       ▼
   Submit (optional)
   - Validate business rules
   - Post to GL
   - Docstatus = 1
       │
       ▼
   GL Entries Created
   - Individual account postings
   - Double-entry enforced
   - Ledger updated
       │
       ▼
   Response
   - Document ID
   - Status
   - Error (if any)
```

### Multi-Currency Transaction Flow

```
Transaction in Foreign Currency
       │
       ▼
Determine Exchange Rate
   - From API parameter
   - From ERPNext rate list
   - System default
       │
       ▼
Create Journal Entry
   multi_currency=True
       │
       ├─► Account 1 (Foreign Currency)
       │   - amount_in_account_currency (USD)
       │   - exchange_rate
       │   - amount_in_base_currency (auto-calculated)
       │
       └─► Account 2 (Base or Foreign)
           - amount_in_account_currency
           - exchange_rate (if applicable)
       │
       ▼
Submit Entry
       │
       ├─► GL Entry 1 (Foreign Currency account)
       │   - Debit/Credit in USD
       │   - Debit/Credit in INR (base)
       │
       └─► GL Entry 2
           - Debit/Credit in account currency
           - Debit/Credit in INR (base)
```

---

## Multi-Currency Architecture

### Key Concepts

1. **Account Currency**
   - Each account can have a currency
   - Restricts postings to that currency only
   - Leave blank for multi-currency flexibility

2. **Transaction Currency**
   - Currency of the transaction
   - May differ from account currency

3. **Base Currency**
   - Company's reporting currency
   - All amounts converted to base for GL

4. **Exchange Rates**
   - Required for forex transactions
   - Format: Foreign → Base
   - Example: 1 USD = 83.50 INR

### Multi-Currency Entry Structure

```python
{
    "multi_currency": True,  # Enable forex
    "accounts": [
        {
            "account": "Revenue - USD",
            "credit_in_account_currency": 1000,  # $1000
            "account_currency": "USD",
            "exchange_rate": 83.50  # → ₹83,500 in base
        },
        {
            "account": "Accounts Receivable - USD",
            "debit_in_account_currency": 1000,  # $1000
            "account_currency": "USD",
            "exchange_rate": 83.50  # → ₹83,500 in base
        }
    ]
}
```

### Forex Gain/Loss Handling

Occurs when exchange rates differ between:
- Invoice date (revenue recognition)
- Payment date (cash receipt)

```python
# Step 1: Revenue at Rate 1
create_journal_entry(
    # ...
    accounts=[
        {"account": "A/R - USD", "debit": 1000, "rate": 83.50},  # ₹83,500
        {"account": "Revenue", "credit": 1000, "rate": 83.50}
    ]
)

# Step 2: Payment at Rate 2
create_journal_entry(
    # ...
    accounts=[
        {"account": "Bank", "debit": 78200},  # ₹78,200 received (rate 78.20)
        {"account": "Forex Loss", "debit": 5300},  # ₹5,300 loss
        {"account": "A/R - USD", "credit": 1000, "rate": 83.50}  # Clear at original rate
    ]
)
```

---

## Error Handling Strategy

### Error Categories

1. **Client-Side Errors** (Validation)
   - Invalid data format
   - Unbalanced entries
   - Missing required fields

2. **Authentication Errors**
   - Invalid API keys
   - Expired credentials
   - Insufficient permissions

3. **Business Logic Errors**
   - Account doesn't exist
   - Date in closed period
   - Frozen account

4. **Server Errors**
   - ERPNext server down
   - Database errors
   - Timeout

### Error Handling Pattern

```python
try:
    # Validate first
    validate_journal_entry(accounts)

    # Make API call
    result = client.create_journal_entry(...)

    # Log success
    logger.info(f"Created JE: {result['name']}")

    return result

except ValueError as e:
    # Validation error - fix data
    logger.error(f"Validation failed: {e}")
    raise

except AuthenticationError as e:
    # Auth error - check credentials
    logger.error(f"Auth failed: {e}")
    notify_admin("ERPNext auth failed")
    raise

except requests.exceptions.HTTPError as e:
    # API error
    if e.response.status_code == 404:
        logger.error(f"Account not found: {e}")
    elif e.response.status_code == 500:
        logger.error(f"Server error: {e}")
        # Maybe retry?
    raise

except Exception as e:
    # Unexpected error
    logger.exception(f"Unexpected error: {e}")
    raise
```

### Retry Strategy

```python
def create_with_retry(entry_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.create_journal_entry(**entry_data)
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
                continue
            raise
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:  # Server error
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            raise
```

---

## Performance Considerations

### 1. Batch Size

Don't process too many transactions in one go:

```python
BATCH_SIZE = 100

for i in range(0, len(transactions), BATCH_SIZE):
    batch = transactions[i:i + BATCH_SIZE]
    process_batch(batch)
```

### 2. Rate Limiting

Respect ERPNext server limits:

```python
import time

def rate_limited_create(entries, calls_per_second=5):
    delay = 1.0 / calls_per_second

    for entry in entries:
        client.create_journal_entry(**entry)
        time.sleep(delay)
```

### 3. Caching

Cache frequently accessed data:

```python
# Cache chart of accounts
@lru_cache(maxsize=1000)
def get_account(account_name):
    return client.get_account(account_name)

# Cache for 1 hour
@timed_cache(seconds=3600)
def get_exchange_rate(currency, date):
    return client.get_exchange_rate(currency, date)
```

### 4. Parallel Processing

For independent operations:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(create_journal_entry, entry)
        for entry in entries
    ]

    for future in futures:
        try:
            result = future.result()
        except Exception as e:
            logger.error(f"Failed: {e}")
```

---

## Security & Authentication

### API Key Management

```python
# GOOD: Environment variables
import os

config = ERPNextConfig(
    base_url=os.environ['ERPNEXT_URL'],
    api_key=os.environ['ERPNEXT_API_KEY'],
    api_secret=os.environ['ERPNEXT_API_SECRET']
)

# BAD: Hardcoded credentials
config = ERPNextConfig(
    base_url="https://example.com",
    api_key="abc123",  # Don't do this!
    api_secret="xyz789"
)
```

### HTTPS Only

Always use HTTPS:

```python
if not config.base_url.startswith('https://'):
    raise ValueError("ERPNext URL must use HTTPS")
```

### Permission Checks

Different API keys can have different permissions:

```python
# Create a dedicated API user with minimal permissions
# - Can read accounts
# - Can create/submit Journal Entries
# - Cannot delete
# - Cannot modify closed periods
```

### Audit Trail

Log all operations:

```python
logger.info(f"User: {api_user}, Action: create_je, Entry: {entry_id}, Amount: {amount}")
```

---

## Best Practices Summary

✅ **DO:**
- Validate before API calls
- Use dry-run mode for testing
- Implement error handling
- Cache frequently accessed data
- Use environment variables for secrets
- Log all operations
- Handle forex carefully
- Test with small batches first

❌ **DON'T:**
- Hardcode credentials
- Skip validation
- Process huge batches without testing
- Ignore error responses
- Use HTTP (only HTTPS)
- Modify data without backups
- Skip dry-run mode

---

## Next Steps

- Review [API Guide](API_GUIDE.md) for specific endpoints
- Check [Migration Guide](MIGRATION.md) for migration patterns
- See [Cookbook](COOKBOOK.md) for common recipes
- Explore [example code](../src/examples/) for implementations
