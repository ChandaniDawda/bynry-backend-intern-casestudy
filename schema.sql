-- ============================================================
-- Part 2: Database Design — StockFlow Schema
-- ============================================================
-- Compatible with MySQL and PostgreSQL
-- All tables use surrogate primary keys (AUTO_INCREMENT / SERIAL)
-- Foreign keys enforce referential integrity at the database level
-- ============================================================


-- ── Companies using the StockFlow platform ──────────────────
CREATE TABLE companies (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ── Warehouses belonging to a company ───────────────────────
-- Design note: A company can have many warehouses (one-to-many).
CREATE TABLE warehouses (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    company_id  INT NOT NULL,
    name        VARCHAR(255) NOT NULL,
    location    VARCHAR(500),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);


-- ── Products ─────────────────────────────────────────────────
-- Design note: SKU is UNIQUE across the entire platform (not per company).
-- product_type distinguishes standard vs bundle products.
-- low_stock_threshold is per-product so alerts can be tuned individually.
-- is_active enables soft deletes — preserves historical data.
CREATE TABLE products (
    id                  INT PRIMARY KEY AUTO_INCREMENT,
    company_id          INT NOT NULL,
    name                VARCHAR(255) NOT NULL,
    sku                 VARCHAR(100) UNIQUE NOT NULL,
    price               DECIMAL(10, 2) NOT NULL,         -- DECIMAL avoids floating-point issues
    product_type        VARCHAR(50) DEFAULT 'standard',  -- 'standard' or 'bundle'
    low_stock_threshold INT DEFAULT 10,                  -- per-product threshold for alerts
    is_active           BOOLEAN DEFAULT TRUE,            -- soft delete flag
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Index on SKU for fast uniqueness checks on every product creation
CREATE INDEX idx_products_sku ON products(sku);
-- Index to quickly fetch all active products for a company
CREATE INDEX idx_products_company ON products(company_id, is_active);


-- ── Inventory: stock level per product per warehouse ─────────
-- Design note: UNIQUE(product_id, warehouse_id) prevents duplicate rows
-- and is enforced at DB level — not relying on application code alone.
CREATE TABLE inventory (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    product_id      INT NOT NULL,
    warehouse_id    INT NOT NULL,
    quantity        INT NOT NULL DEFAULT 0,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE (product_id, warehouse_id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

-- Index for fast low-stock queries (Part 3 API uses this heavily)
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id, quantity);


-- ── Inventory Logs: audit trail of every stock change ────────
-- Design note: This table powers the "recent sales activity" check
-- and daily sales calculation needed for days_until_stockout.
-- reason captures context: 'sale', 'restock', 'adjustment', 'transfer'
-- change_qty is signed: positive = stock added, negative = stock removed
CREATE TABLE inventory_logs (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    product_id      INT NOT NULL,
    warehouse_id    INT NOT NULL,
    change_qty      INT NOT NULL,
    reason          VARCHAR(50),    -- 'sale', 'restock', 'adjustment', 'transfer'
    notes           VARCHAR(500),   -- optional free-text context
    changed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

-- Index for fast sales history queries (used in low-stock alert API)
CREATE INDEX idx_logs_product_warehouse_date
    ON inventory_logs(product_id, warehouse_id, changed_at, reason);


-- ── Suppliers ────────────────────────────────────────────────
CREATE TABLE suppliers (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(255) NOT NULL,
    contact_email   VARCHAR(255),
    phone           VARCHAR(50),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ── Product Suppliers: many-to-many ──────────────────────────
-- Design note: A product can have multiple suppliers;
-- a supplier can supply multiple products.
-- lead_time_days helps estimate reorder timing.
CREATE TABLE product_suppliers (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    product_id      INT NOT NULL,
    supplier_id     INT NOT NULL,
    lead_time_days  INT,            -- days needed for supplier to restock
    is_preferred    BOOLEAN DEFAULT FALSE,  -- marks the primary/preferred supplier
    UNIQUE (product_id, supplier_id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);


-- ── Bundle Items: components that make up a bundle product ───
-- Design note: Self-referential relationship on products.
-- bundle_id = the parent bundle product
-- component_id = an individual product inside that bundle
-- quantity = how many units of the component are in one bundle
CREATE TABLE bundle_items (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    bundle_id       INT NOT NULL,
    component_id    INT NOT NULL,
    quantity        INT NOT NULL DEFAULT 1,
    FOREIGN KEY (bundle_id) REFERENCES products(id),
    FOREIGN KEY (component_id) REFERENCES products(id)
);
