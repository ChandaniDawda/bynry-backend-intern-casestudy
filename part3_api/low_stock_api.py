"""
Part 3: API Implementation — Low-Stock Alerts
==============================================

Endpoint: GET /api/companies/{company_id}/alerts/low-stock

Business Rules Implemented:
  - Alert only for products whose current stock is below their low_stock_threshold
  - Only include products with at least 1 sale in the last 30 days (recent activity)
  - Handle multiple warehouses per company — each warehouse generates its own alert
  - Include supplier contact info for reordering
  - Calculate days_until_stockout from average daily sales

Assumptions documented (due to incomplete requirements):
  - "Recent sales activity" = at least 1 unit sold in the last 30 days
  - Sales are recorded in inventory_logs with reason='sale' and negative change_qty
  - days_until_stockout = current_stock / average_daily_sales (over last 30 days)
  - The preferred supplier is identified by is_preferred=True in product_suppliers;
    if none is marked preferred, the first linked supplier is used
  - A product can generate alerts in multiple warehouses independently
  - Bundle products are treated the same as standard products for alerting
"""

from flask import jsonify
from datetime import datetime, timedelta
from sqlalchemy import func


@app.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def low_stock_alerts(company_id):

    # ── Validate company exists ───────────────────────────────────────────────
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": f"Company with id '{company_id}' not found"}), 404

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    alerts = []

    # ── Get all warehouses for this company ───────────────────────────────────
    # Edge case: if the company has no warehouses, this returns [] cleanly
    warehouses = Warehouse.query.filter_by(company_id=company_id).all()

    for warehouse in warehouses:

        # ── Find inventory items below their low_stock_threshold ──────────────
        # Only active products belonging to this company
        low_stock_items = (
            db.session.query(Inventory, Product)
            .join(Product, Inventory.product_id == Product.id)
            .filter(
                Inventory.warehouse_id == warehouse.id,
                Product.company_id == company_id,
                Product.is_active == True,
                Inventory.quantity < Product.low_stock_threshold
            )
            .all()
        )

        for inventory, product in low_stock_items:

            # ── Check recent sales activity ───────────────────────────────────
            # Sum of units sold (as positive number) in the last 30 days
            # inventory_logs stores sales as negative change_qty, so we use abs()
            recent_sales = db.session.query(
                func.sum(func.abs(InventoryLog.change_qty))
            ).filter(
                InventoryLog.product_id == product.id,
                InventoryLog.warehouse_id == warehouse.id,
                InventoryLog.reason == 'sale',
                InventoryLog.changed_at >= thirty_days_ago
            ).scalar() or 0

            # Skip products with no recent sales — not actively moving stock
            # (e.g. discontinued or seasonal items sitting in warehouse)
            if recent_sales == 0:
                continue

            # ── Calculate days until stockout ─────────────────────────────────
            avg_daily_sales = recent_sales / 30

            if avg_daily_sales > 0:
                days_until_stockout = int(inventory.quantity / avg_daily_sales)
            else:
                # Defensive: if somehow avg is 0 despite recent_sales > 0
                days_until_stockout = None

            # ── Get preferred supplier ────────────────────────────────────────
            # First try to find the explicitly preferred supplier
            product_supplier = ProductSupplier.query.filter_by(
                product_id=product.id,
                is_preferred=True
            ).first()

            # Fall back to first linked supplier if none is marked preferred
            if not product_supplier:
                product_supplier = ProductSupplier.query.filter_by(
                    product_id=product.id
                ).first()

            # Build supplier data — gracefully returns None if no supplier exists
            supplier_data = None
            if product_supplier:
                supplier = Supplier.query.get(product_supplier.supplier_id)
                if supplier:
                    supplier_data = {
                        "id": supplier.id,
                        "name": supplier.name,
                        "contact_email": supplier.contact_email
                    }

            # ── Build alert object ────────────────────────────────────────────
            alerts.append({
                "product_id": product.id,
                "product_name": product.name,
                "sku": product.sku,
                "warehouse_id": warehouse.id,
                "warehouse_name": warehouse.name,
                "current_stock": inventory.quantity,
                "threshold": product.low_stock_threshold,
                "days_until_stockout": days_until_stockout,
                "supplier": supplier_data
            })

    # ── Return response ───────────────────────────────────────────────────────
    return jsonify({
        "alerts": alerts,
        "total_alerts": len(alerts)
    }), 200
