-- =============================================================
-- OneView Hospitality Platform — PostgreSQL Schema
-- =============================================================

-- ─── SCHEMAS ────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS hotel;
CREATE SCHEMA IF NOT EXISTS restaurant;
CREATE SCHEMA IF NOT EXISTS realestate;
CREATE SCHEMA IF NOT EXISTS analytics;

-- =============================================================
-- HOTEL SCHEMA
-- =============================================================

CREATE TABLE IF NOT EXISTS hotel.rooms (
    id              SERIAL PRIMARY KEY,
    room_number     VARCHAR(10) NOT NULL UNIQUE,
    room_type       VARCHAR(30) NOT NULL,  -- standard, deluxe, suite, presidential
    capacity        INT NOT NULL DEFAULT 2,
    base_rate       NUMERIC(10,2) NOT NULL,
    floor           INT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hotel.guests (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(80) NOT NULL,
    last_name       VARCHAR(80) NOT NULL,
    email           VARCHAR(120) UNIQUE,
    country         VARCHAR(60),
    travel_purpose  VARCHAR(30),   -- business, tourism, event
    loyalty_tier    VARCHAR(20) DEFAULT 'standard',  -- standard, silver, gold, platinum
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hotel.reservations (
    id              SERIAL PRIMARY KEY,
    room_id         INT NOT NULL REFERENCES hotel.rooms(id),
    guest_id        INT NOT NULL REFERENCES hotel.guests(id),
    checkin_date    DATE NOT NULL,
    checkout_date   DATE NOT NULL,
    nights          INT GENERATED ALWAYS AS (checkout_date - checkin_date) STORED,
    status          VARCHAR(20) DEFAULT 'confirmed',  -- confirmed, checked_in, checked_out, cancelled
    channel         VARCHAR(30),   -- direct, booking.com, expedia, corporate, ota
    rate_charged    NUMERIC(10,2) NOT NULL,
    total_amount    NUMERIC(12,2),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hotel.daily_kpis (
    id              SERIAL PRIMARY KEY,
    kpi_date        DATE NOT NULL UNIQUE,
    total_rooms     INT NOT NULL,
    occupied_rooms  INT NOT NULL,
    occupancy_rate  NUMERIC(5,2),   -- percentage 0-100
    adr             NUMERIC(10,2),  -- Average Daily Rate
    revpar          NUMERIC(10,2),  -- Revenue per Available Room
    total_revenue   NUMERIC(14,2),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- RESTAURANT SCHEMA
-- =============================================================

CREATE TABLE IF NOT EXISTS restaurant.menu_items (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    category        VARCHAR(50),   -- breakfast, lunch, dinner, drinks, desserts
    cost_price      NUMERIC(8,2),
    sell_price      NUMERIC(8,2),
    margin_pct      NUMERIC(5,2) GENERATED ALWAYS AS (
                        CASE WHEN sell_price > 0
                        THEN ((sell_price - cost_price) / sell_price * 100)
                        ELSE 0 END
                    ) STORED,
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS restaurant.sales_tickets (
    id              SERIAL PRIMARY KEY,
    ticket_date     DATE NOT NULL,
    ticket_time     TIME,
    service_type    VARCHAR(20),    -- breakfast, lunch, dinner, room_service, event
    table_number    VARCHAR(10),
    channel         VARCHAR(30),    -- salon, room_service, event, delivery
    subtotal        NUMERIC(10,2) NOT NULL,
    tax_amount      NUMERIC(8,2),
    total_amount    NUMERIC(10,2) NOT NULL,
    covers          INT DEFAULT 1,  -- number of diners
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS restaurant.ticket_items (
    id              SERIAL PRIMARY KEY,
    ticket_id       INT NOT NULL REFERENCES restaurant.sales_tickets(id),
    menu_item_id    INT NOT NULL REFERENCES restaurant.menu_items(id),
    quantity        INT DEFAULT 1,
    unit_price      NUMERIC(8,2),
    line_total      NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS restaurant.inventory (
    id              SERIAL PRIMARY KEY,
    ingredient      VARCHAR(120) NOT NULL,
    unit            VARCHAR(20),
    stock_qty       NUMERIC(10,3),
    min_stock       NUMERIC(10,3),
    unit_cost       NUMERIC(8,2),
    last_updated    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS restaurant.daily_sales_summary (
    id              SERIAL PRIMARY KEY,
    sale_date       DATE NOT NULL,
    service_type    VARCHAR(20) NOT NULL,
    total_revenue   NUMERIC(12,2),
    total_covers    INT,
    avg_ticket      NUMERIC(8,2),
    UNIQUE(sale_date, service_type)
);

-- =============================================================
-- REAL ESTATE SCHEMA
-- =============================================================

CREATE TABLE IF NOT EXISTS realestate.projects (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    city            VARCHAR(80),
    project_type    VARCHAR(30),   -- residential, offices, mixed
    total_units     INT,
    start_date      DATE,
    delivery_date   DATE,
    status          VARCHAR(30) DEFAULT 'active',
    description     TEXT
);

CREATE TABLE IF NOT EXISTS realestate.units (
    id              SERIAL PRIMARY KEY,
    project_id      INT NOT NULL REFERENCES realestate.projects(id),
    unit_code       VARCHAR(20) NOT NULL,
    unit_type       VARCHAR(30),   -- studio, 1br, 2br, 3br, penthouse, office
    floor           INT,
    area_sqm        NUMERIC(8,2),
    list_price      NUMERIC(14,2),
    status          VARCHAR(20) DEFAULT 'available',  -- available, reserved, sold
    UNIQUE(project_id, unit_code)
);

CREATE TABLE IF NOT EXISTS realestate.leads (
    id              SERIAL PRIMARY KEY,
    project_id      INT REFERENCES realestate.projects(id),
    full_name       VARCHAR(120),
    email           VARCHAR(120),
    phone           VARCHAR(30),
    source_channel  VARCHAR(40),   -- web, referral, whatsapp, event, portal, cold_call
    interest_level  VARCHAR(20) DEFAULT 'warm',  -- cold, warm, hot
    lead_date       DATE NOT NULL,
    unit_type_interest VARCHAR(30),
    campaign        VARCHAR(80),
    funnel_stage    VARCHAR(30) DEFAULT 'lead',  -- lead, contact, visit, proposal, reserved, closed, lost
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS realestate.interactions (
    id              SERIAL PRIMARY KEY,
    lead_id         INT NOT NULL REFERENCES realestate.leads(id),
    interaction_type VARCHAR(30),  -- call, visit, email, meeting, whatsapp
    interaction_date TIMESTAMP NOT NULL,
    notes           TEXT,
    outcome         VARCHAR(30)    -- interested, not_interested, follow_up, deal_closed
);

CREATE TABLE IF NOT EXISTS realestate.contracts (
    id              SERIAL PRIMARY KEY,
    lead_id         INT NOT NULL REFERENCES realestate.leads(id),
    unit_id         INT NOT NULL REFERENCES realestate.units(id),
    contract_date   DATE NOT NULL,
    final_price     NUMERIC(14,2),
    discount_pct    NUMERIC(5,2) DEFAULT 0,
    payment_method  VARCHAR(30),   -- cash, financing, mixed
    status          VARCHAR(20) DEFAULT 'active'
);

-- =============================================================
-- ANALYTICS SCHEMA
-- =============================================================

CREATE TABLE IF NOT EXISTS analytics.model_registry (
    id              SERIAL PRIMARY KEY,
    model_name      VARCHAR(80) NOT NULL,
    domain          VARCHAR(30),   -- hotel, restaurant, realestate
    algorithm       VARCHAR(60),
    version         VARCHAR(20),
    rmse            NUMERIC(10,4),
    mae             NUMERIC(10,4),
    roc_auc         NUMERIC(6,4),
    trained_at      TIMESTAMP DEFAULT NOW(),
    model_path      VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS analytics.predictions (
    id              SERIAL PRIMARY KEY,
    model_name      VARCHAR(80),
    prediction_date DATE,
    target_date     DATE,
    predicted_value NUMERIC(14,4),
    actual_value    NUMERIC(14,4),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ─── Indexes ────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_reservations_checkin    ON hotel.reservations(checkin_date);
CREATE INDEX IF NOT EXISTS idx_reservations_room       ON hotel.reservations(room_id);
CREATE INDEX IF NOT EXISTS idx_reservations_status     ON hotel.reservations(status);
CREATE INDEX IF NOT EXISTS idx_tickets_date            ON restaurant.sales_tickets(ticket_date);
CREATE INDEX IF NOT EXISTS idx_tickets_service         ON restaurant.sales_tickets(service_type);
CREATE INDEX IF NOT EXISTS idx_leads_funnel            ON realestate.leads(funnel_stage);
CREATE INDEX IF NOT EXISTS idx_leads_project           ON realestate.leads(project_id);
CREATE INDEX IF NOT EXISTS idx_units_status            ON realestate.units(status);
