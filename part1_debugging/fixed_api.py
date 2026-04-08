"""
Part 1: Code Review & Debugging — Fixed Implementation
=======================================================

ISSUES FOUND IN ORIGINAL CODE:
-----------------------------------------------------------------------
Issue 1: No Input Validation
  - Problem : Missing fields like 'name', 'sku', 'price' crash with KeyError
  - Impact  : API crashes on any incomplete request; vulnerability to malformed input
  - Fix     : Validate all required fields before processing

Issue 2: No SKU Uniqueness Check
  - Problem : No check if SKU already exists before inserting
  - Impact  : Duplicate SKUs break inventory tracking and billing
  - Fix     : Query for existing SKU and return 409 Conflict if found

Issue 3: Two Separate db.session.commit() Calls (CRITICAL)
  - Problem : If the second commit (Inventory) fails, Product is already saved
  - Impact  : Data corruption — orphaned products with no inventory record
  - Fix     : Use db.session.flush() to get product.id, then ONE final commit()

Issue 4: No HTTP Status Codes
  - Problem : Returns default 200 even on creation; no error codes on failure
  - Impact  : API consumers cannot distinguish success from failure
  - Fix     : Return 201 on creation, 400/404/409/500 for errors

Issue 5: Price Not Validated
  - Problem : Price is stored as raw input — accepts negatives or non-numeric strings
  - Impact  : Corrupt pricing data, database errors, financial miscalculations
  - Fix     : Parse and validate price as a positive Decimal

Issue 6: Missing Default for initial_quantity
  - Problem : data['initial_quantity'] crashes if field is absent
  - Impact  : Any request without this optional field fails with KeyError
  - Fix     : Use data.get('initial_quantity', 0) to default to zero

Issue 7: No Warehouse Validation
  - Problem : warehouse_id is not checked against the database
  - Impact  : Products can be linked to non-existent warehouses
  - Fix     : Query warehouse before proceeding; return 404 if not found
-----------------------------------------------------------------------
"""

from flask import request, jsonify
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import IntegrityError


@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json

    # ── FIX 1: Validate all required fields are present ──────────────────────
    required_fields = ['name', 'sku', 'price', 'warehouse_id']
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({"error": f"Missing required field: '{field}'"}), 400

    # ── FIX 5: Validate price is a positive decimal ───────────────────────────
    try:
        price = Decimal(str(data['price']))
        if price <= 0:
            return jsonify({"error": "Price must be a positive value"}), 400
    except InvalidOperation:
        return jsonify({"error": "Invalid price format — must be a numeric value"}), 400

    # ── FIX 7: Validate warehouse exists in the database ─────────────────────
    warehouse = Warehouse.query.get(data['warehouse_id'])
    if not warehouse:
        return jsonify({"error": f"Warehouse with id '{data['warehouse_id']}' not found"}), 404

    # ── FIX 2: Check SKU uniqueness before inserting ─────────────────────────
    existing = Product.query.filter_by(sku=data['sku']).first()
    if existing:
        return jsonify({"error": f"A product with SKU '{data['sku']}' already exists"}), 409

    # ── FIX 3 & 6: Single atomic transaction + default for initial_quantity ──
    try:
        product = Product(
            name=data['name'],
            sku=data['sku'],
            price=price,                          # FIX 5: validated Decimal
            warehouse_id=data['warehouse_id']
        )
        db.session.add(product)

        # flush() writes to DB and gives us product.id WITHOUT committing yet.
        # This is the key to making both inserts atomic.
        db.session.flush()

        inventory = Inventory(
            product_id=product.id,
            warehouse_id=data['warehouse_id'],
            quantity=data.get('initial_quantity', 0)  # FIX 6: default to 0
        )
        db.session.add(inventory)

        # ONE commit — both Product and Inventory succeed or both roll back.
        db.session.commit()

        # ── FIX 4: Return correct HTTP 201 Created status ─────────────────
        return jsonify({
            "message": "Product created successfully",
            "product_id": product.id
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error — possible duplicate entry"}), 409

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
