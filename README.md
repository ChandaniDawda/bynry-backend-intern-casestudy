# 🏭 StockFlow — Backend Engineering Intern Case Study
**Submitted by:** Chandani Dawda  
**Role:** Backend Engineering Intern — Bynry Inc.  
**Date:** April 8, 2026

---

## 📋 Overview

This repository contains my solution to the **StockFlow Inventory Management System** case study for Bynry's Backend Engineering Intern position.

StockFlow is a B2B SaaS platform that helps small businesses track products across multiple warehouses and manage supplier relationships.

---

## 📁 Repository Structure

```
bynry-backend-intern-casestudy/
│
├── part1_debugging/
│   ├── original_buggy_code.py      # Original code with issues
│   └── fixed_api.py                # Corrected implementation with explanations
│
├── part2_database/
│   ├── schema.sql                  # Full database schema (SQL DDL)
│   └── design_notes.md            # Design decisions and questions for product team
│
├── part3_api/
│   ├── low_stock_api.py            # Low-stock alert endpoint implementation
│   └── edge_cases.md              # Edge cases handled and assumptions
│
└── README.md
```

---

## 🔍 Part 1: Code Review & Debugging

### Issues Found in Original Code

| # | Issue | Severity |
|---|-------|----------|
| 1 | No input validation — missing fields cause `KeyError` crash | 🔴 Critical |
| 2 | No SKU uniqueness check before insert | 🔴 Critical |
| 3 | Two separate `db.session.commit()` calls — data corruption if 2nd fails | 🔴 Critical |
| 4 | No HTTP status codes (should return `201` on creation) | 🟡 Medium |
| 5 | Price not validated — accepts negative or non-numeric values | 🔴 Critical |
| 6 | `initial_quantity` crashes if field is absent (no default) | 🟡 Medium |
| 7 | `warehouse_id` not validated against database | 🟡 Medium |

### Key Fix: Atomic Transaction
The most critical fix was replacing two separate `commit()` calls with a single atomic transaction using `db.session.flush()` + one final `commit()`. This ensures **both Product and Inventory records are saved together, or neither is** — preventing orphaned data.

➡️ See full solution: [`part1_debugging/fixed_api.py`](part1_debugging/fixed_api.py)

---

## 🗄️ Part 2: Database Design

### Tables Designed

| Table | Purpose |
|-------|---------|
| `companies` | Companies using StockFlow |
| `warehouses` | Warehouses belonging to a company |
| `products` | Products with SKU, price, type, and threshold |
| `inventory` | Stock levels per product per warehouse |
| `inventory_logs` | Audit trail of every stock change |
| `suppliers` | Supplier contact information |
| `product_suppliers` | Many-to-many: products linked to suppliers |
| `bundle_items` | Components that make up a bundle product |

### Key Design Decisions
- **`UNIQUE(product_id, warehouse_id)`** on inventory — enforced at DB level, not just application code
- **`inventory_logs`** table — full audit trail enabling daily sales calculations for stockout prediction
- **`DECIMAL(10,2)`** for price — avoids floating-point precision errors in financial data
- **`low_stock_threshold`** per product — smarter, flexible alerts instead of one global value
- **`is_active` boolean** — soft deletes preserve historical data

➡️ See full schema: [`part2_database/schema.sql`](part2_database/schema.sql)  
➡️ See design notes: [`part2_database/design_notes.md`](part2_database/design_notes.md)

---

## 🚨 Part 3: Low-Stock Alert API

### Endpoint
```
GET /api/companies/{company_id}/alerts/low-stock
```

### Business Logic
- Alerts only for products **below their `low_stock_threshold`**
- Only includes products with **sales activity in the last 30 days**
- Calculates **`days_until_stockout`** = current stock ÷ average daily sales
- Includes **supplier contact info** for easy reordering
- Loops across **all warehouses** for the company

### Key Assumptions Documented
- "Recent sales activity" = at least 1 sale in last 30 days
- Sales tracked in `inventory_logs` with `reason = 'sale'`
- First supplier in `product_suppliers` = preferred supplier

### Edge Cases Handled
- Company not found → `404`
- No warehouses → empty alerts list (not an error)
- Product with no recent sales → skipped
- No supplier linked → `supplier: null` (no crash)
- Zero daily sales → `days_until_stockout: null` (no division by zero)

➡️ See full implementation: [`part3_api/low_stock_api.py`](part3_api/low_stock_api.py)

---

## 🛠️ Tech Stack
- **Language:** Python
- **Framework:** Flask
- **ORM:** SQLAlchemy
- **Database:** MySQL / PostgreSQL compatible

---

## 👩‍💻 About Me

I'm Chandani Dawda, a Computer Science postgraduate (M.Sc, Nagpur University) with a strong foundation in both software development and technical education.

- 🎓 B.Sc — Physics, Mathematics, Computer Science (2017)
- 🎓 M.Sc — Computer Science (2020)
- 💼 2.5 years experience as an IT Teacher — teaching programming concepts, web technologies
- 🌐 Skills: HTML, CSS, JavaScript, React JS, Python, SQL

I am actively seeking opportunities in backend/full-stack development and am excited about Bynry's mission to modernize utility infrastructure through smart software.

---

*Thank you for the opportunity — I look forward to the live discussion session!*
