# Part 2: Database Design Notes

## Design Decisions & Justifications

| Decision | Justification |
|----------|--------------|
| `UNIQUE(product_id, warehouse_id)` on inventory | Prevents duplicate inventory rows per warehouse; enforced at DB level, not just application code |
| `inventory_logs` table | Full audit trail of every stock change — enables daily sales calculation needed for stockout prediction |
| `DECIMAL(10,2)` for price | Avoids floating-point precision errors in financial calculations |
| `low_stock_threshold` on products | Per-product thresholds instead of one global value — makes alerts smarter and configurable |
| `product_type` column | Distinguishes standard vs. bundle products without a separate table; simpler to query |
| `bundle_items` as separate table | Handles many-to-many relationship between bundles and components cleanly, with quantity per component |
| `product_suppliers` junction table | A product can have multiple suppliers; a supplier can supply many products — requires many-to-many |
| `is_active` boolean | Enables soft deletes — products can be deactivated without losing historical data |
| `is_preferred` on product_suppliers | Marks the primary supplier for a product, used in low-stock alert reorder info |
| Indexes on `inventory_logs` | The low-stock API queries this table on every request — indexing by product, warehouse, date, and reason is critical for performance |

---

## Questions I Would Ask the Product Team

Before finalizing this schema, I would ask the following to fill in missing requirements:

1. **Product ownership** — Can a product belong to multiple companies, or is each product owned by exactly one company?

2. **"Recent sales activity" definition** — What window defines "recent"? Last 7 days, 30 days, or is this configurable per company?

3. **Low-stock threshold scope** — Is the threshold set per product globally, per product per warehouse, or per product category/type?

4. **Bundle stock tracking** — For bundle products, is stock tracked at the bundle level, or should it be computed dynamically from component quantities?

5. **Negative inventory** — Can inventory go negative (i.e., are backorders allowed)? Or should the system block any operation that would take stock below zero?

6. **Multiple suppliers** — When a product has multiple suppliers, how do we determine which one to show in a low-stock alert? Cheapest? Fastest lead time? Manually marked preferred?

7. **User accounts & roles** — Do we need a `users` table with roles like admin, warehouse manager, or viewer? This affects access control for the API.

8. **Inventory transfers** — When stock moves from one warehouse to another, should that generate two log entries (one negative, one positive) or a single "transfer" record?

9. **Data volume expectations** — How many products, warehouses, and daily transactions does a typical customer have? This affects indexing and potential partitioning strategy for `inventory_logs`.

10. **Hard vs. soft deletes** — Should deleting a company cascade to warehouses and products, or should everything be soft-deleted with `is_active` flags?
