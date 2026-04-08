# Part 3: Edge Cases & Assumptions

## Assumptions Made

| Assumption | Reasoning |
|-----------|-----------|
| "Recent sales activity" = sales in last 30 days | 30 days is a common industry standard for "active" inventory |
| Sales tracked via `inventory_logs` with `reason='sale'` | Follows the schema design from Part 2 |
| `change_qty` is negative for sales | Convention: stock removed = negative quantity |
| `days_until_stockout` = stock ÷ avg daily sales | Simple and interpretable; based on last 30 days trend |
| Preferred supplier = `is_preferred=True`, else first linked | Practical fallback when no preference is set |
| Alerts are per warehouse, not per product globally | A product may be fine in one warehouse but critical in another |

---

## Edge Cases Handled

| Edge Case | How It's Handled |
|-----------|-----------------|
| Company not found | Returns `404` with a clear error message |
| Company has no warehouses | Loop doesn't execute; returns `{ "alerts": [], "total_alerts": 0 }` |
| Product has no recent sales (last 30 days) | Skipped — low stock with no sales activity is not an urgent alert |
| No supplier linked to a product | `supplier` field returns `null` — no crash |
| `avg_daily_sales` is 0 despite recent sales | `days_until_stockout` returns `null` safely — no division by zero |
| Same product low in multiple warehouses | Generates one alert per warehouse — each is an independent concern |
| Inactive products (`is_active = False`) | Filtered out in the query — not included in alerts |
| Preferred supplier record exists but supplier row missing | Guarded with `if supplier:` check before accessing fields |
| `inventory_logs` has no records for a product | `scalar() or 0` safely returns 0 — product is then skipped |

---

## Possible Future Improvements

- **Pagination** — Add `?page=` and `?limit=` query params for large result sets
- **Sorting** — Allow sorting by `days_until_stockout` ascending (most urgent first)
- **Filtering** — Filter by warehouse_id, product_type, or urgency level
- **Caching** — Cache results for a few minutes since this is a read-heavy endpoint
- **Urgency levels** — Categorize alerts as Critical / Warning / Watch based on days_until_stockout
- **Email/notification trigger** — Fire a notification when days_until_stockout drops below lead_time_days
