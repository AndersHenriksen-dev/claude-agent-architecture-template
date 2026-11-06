---
paths:
  - "src/subfinder/lib/statement/**"
  - "src/subfinder/config/statement/**"
  - "tests/statement/**"
---

# Money

- Amounts are `Money` from `lib/statement/transactions.py`: a `Decimal` that crosses JSON and YAML as a string such as `"99.00"`. Never use `float` for money, and never round to hide a difference.
- On the statement, a negative amount is money out. A saving or a monthly cost is a positive amount.
- The statement is made up. Merchants, people and amounts are invented, so keep them invented: no real bank data, no real company names, nothing from an employer.
