-- ============================================================
-- OneView Hospitality Platform - Database Schema
-- PostgreSQL 15
-- ============================================================

-- Create schemas per domain
CREATE SCHEMA IF NOT EXISTS hotel;
CREATE SCHEMA IF NOT EXISTS restaurant;
CREATE SCHEMA IF NOT EXISTS realestate;
CREATE SCHEMA IF NOT EXISTS analytics;

-- ============================================================
-- HOTEL SCHEMA
-- ============================================================

CREATE TABLE IF NOT EXISTS hotel.room_types (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,  -- STD, DLX, STE, PEN
    name        VARCHAR(100) NOT NULL,
    capacity    INTEGER NOT NULL DEFAULT 2,
    base_rate   NUMERIC(10,2) NOT NULL,
    description TEXT,
    amenities   JSONB DEFAULT '[]',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hotel.rooms (
    id           SERIAL PRIMARY KEY,
    room_number  VARCHAR(10) UNIQUE NOT NULL,
    room_type_id INTEGER REFERENCES hotel.room_types(id),
    floor        INTEGER NOT NULL,
    status       VARCHAR(20) DEFAULT 'available', -- available, occupied, maintenance
    notes        TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hotel.guests (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(200) UNIQUE,
    phone           VARCHAR(50),
    country_code    CHAR(2) NOT NULL,  -- ISO 3166-1 alpha-2
    nationality     VARCHAR(100),
    document_type   VARCHAR(20),  -- passport, dni, cedula
    document_number VARCHAR(50),
    loyalty_tier    VARCHAR(20) DEFAULT 'standard', -- standard, silver, gold, platinum
    total_stays     INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hotel.reservations (
    id              SERIAL PRIMARY KEY,
    reservation_code VARCHAR(20) UNIQUE NOT NULL,
    guest_id        INTEGER REFERENCES hotel.guests(id),
    room_id         INTEGER REFERENCES hotel.rooms(id),
    checkin_date    DATE NOT NULL,
    checkout_date   DATE NOT NULL,
    adults          INTEGER NOT NULL DEFAULT 2,
    children        INTEGER DEFAULT 0,
    channel         VARCHAR(50) NOT NULL,  -- direct, booking.com, expedia, airbnb, phone
    trip_purpose    VARCHAR(50),  -- business, leisure, event, honeymoon
    rate_per_night  NUMERIC(10,2) NOT NULL,
    total_amount    NUMERIC(12,2) NOT NULL,
    status          VARCHAR(30) DEFAULT 'confirmed', -- confirmed, checked_in, checked_out, cancelled, no_show
    special_requests TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hotel.daily_kpis (
    id               SERIAL PRIMARY KEY,
    kpi_date         DATE UNIQUE NOT NULL,
    total_rooms      INTEGER NOT NULL,
    occupied_rooms   INTEGER NOT NULL,
    occupancy_rate   NUMERIC(5,2) NOT NULL,  -- percentage 0-100
    adr              NUMERIC(10,2) NOT NULL,  -- Average Daily Rate
    revpar           NUMERIC(10,2) NOT NULL,  -- Revenue Per Available Room
    total_revenue    NUMERIC(12,2) NOT NULL,
    adr_vs_lw        NUMERIC(6,2),  -- vs last week %
    occ_vs_lw        NUMERIC(6,2),  -- vs last week %
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- RESTAURANT SCHEMA
-- ============================================================

CREATE TABLE IF NOT EXISTS restaurant.menu_categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    active      BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS restaurant.menu_items (
    id              SERIAL PRIMARY KEY,
    category_id     INTEGER REFERENCES restaurant.menu_categories(id),
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    sale_price      NUMERIC(10,2) NOT NULL,
    cost_price      NUMERIC(10,2) NOT NULL,
    margin_pct      NUMERIC(5,2) GENERATED ALWAYS AS (
                        ROUND(((sale_price - cost_price) / sale_price * 100), 2)
                    ) STORED,
    service_type    VARCHAR(30) NOT NULL, -- breakfast, lunch, dinner, bar, room_service
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS restaurant.sales_tickets (
    id              SERIAL PRIMARY KEY,
    ticket_number   VARCHAR(20) UNIQUE NOT NULL,
    sale_datetime   TIMESTAMPTZ NOT NULL,
    service_type    VARCHAR(30) NOT NULL,  -- breakfast, lunch, dinner, bar, room_service, event
    table_number    VARCHAR(10),
    covers          INTEGER DEFAULT 1,  -- number of diners
    subtotal        NUMERIC(10,2) NOT NULL,
    tax_amount      NUMERIC(10,2) NOT NULL DEFAULT 0,
    tip_amount      NUMERIC(10,2) DEFAULT 0,
    total_amount    NUMERIC(10,2) NOT NULL,
    payment_method  VARCHAR(30),  -- cash, card, room_charge
    guest_id        INTEGER REFERENCES hotel.guests(id),  -- cross-domain link
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS restaurant.ticket_items (
    id          SERIAL PRIMARY KEY,
    ticket_id   INTEGER REFERENCES restaurant.sales_tickets(id),
    menu_item_id INTEGER REFERENCES restaurant.menu_items(id),
    quantity    INTEGER NOT NULL DEFAULT 1,
    unit_price  NUMERIC(10,2) NOT NULL,
    total_price NUMERIC(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS restaurant.inventory (
    id              SERIAL PRIMARY KEY,
    ingredient_name VARCHAR(200) NOT NULL,
    unit            VARCHAR(20) NOT NULL,  -- kg, ltr, unit, box
    current_stock   NUMERIC(10,3) NOT NULL DEFAULT 0,
    min_stock       NUMERIC(10,3) NOT NULL DEFAULT 0,
    unit_cost       NUMERIC(10,2) NOT NULL,
    last_updated    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS restaurant.daily_sales_summary (
    id              SERIAL PRIMARY KEY,
    sale_date       DATE NOT NULL,
    service_type    VARCHAR(30) NOT NULL,
    total_tickets   INTEGER NOT NULL DEFAULT 0,
    total_covers    INTEGER NOT NULL DEFAULT 0,
    total_revenue   NUMERIC(12,2) NOT NULL DEFAULT 0,
    avg_ticket      NUMERIC(10,2),
    UNIQUE(sale_date, service_type)
);

-- ============================================================
-- REAL ESTATE SCHEMA
-- ============================================================

CREATE TABLE IF NOT EXISTS realestate.projects (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    city            VARCHAR(100) NOT NULL,
    zone            VARCHAR(100),
    project_type    VARCHAR(50) NOT NULL,  -- residential, offices, mixed
    total_units     INTEGER NOT NULL,
    start_date      DATE,
    delivery_date   DATE,
    status          VARCHAR(50) DEFAULT 'presale',  -- presale, construction, delivered
    description     TEXT,
    amenities       JSONB DEFAULT '[]',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS realestate.units (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER REFERENCES realestate.projects(id),
    unit_code       VARCHAR(30) NOT NULL,  -- e.g. T1-0301
    unit_type       VARCHAR(50) NOT NULL,  -- studio, 1br, 2br, 3br, office_s, office_m, office_l
    floor           INTEGER,
    area_sqm        NUMERIC(8,2) NOT NULL,
    list_price      NUMERIC(14,2) NOT NULL,
    status          VARCHAR(30) DEFAULT 'available',  -- available, reserved, sold
    bedrooms        INTEGER DEFAULT 0,
    bathrooms       NUMERIC(3,1) DEFAULT 1,
    parking_spots   INTEGER DEFAULT 1,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS realestate.leads (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(200),
    phone           VARCHAR(50),
    source_channel  VARCHAR(50) NOT NULL,  -- web, referral, social, billboard, event, cold_call
    interest_level  VARCHAR(20) DEFAULT 'warm',  -- cold, warm, hot
    project_id      INTEGER REFERENCES realestate.projects(id),
    unit_type_interest VARCHAR(50),
    budget_min      NUMERIC(14,2),
    budget_max      NUMERIC(14,2),
    status          VARCHAR(30) DEFAULT 'new',  -- new, contacted, nurturing, qualified, converted, lost
    assigned_to     VARCHAR(100),  -- sales agent name
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS realestate.interactions (
    id              SERIAL PRIMARY KEY,
    lead_id         INTEGER REFERENCES realestate.leads(id),
    interaction_type VARCHAR(50) NOT NULL,  -- call, email, whatsapp, showroom_visit, virtual_tour
    interaction_date TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER,
    notes           TEXT,
    outcome         VARCHAR(50),  -- interested, not_interested, callback, visit_scheduled
    agent_name      VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS realestate.contracts (
    id              SERIAL PRIMARY KEY,
    lead_id         INTEGER REFERENCES realestate.leads(id),
    unit_id         INTEGER REFERENCES realestate.units(id),
    contract_date   DATE NOT NULL,
    final_price     NUMERIC(14,2) NOT NULL,
    discount_pct    NUMERIC(5,2) DEFAULT 0,
    payment_method  VARCHAR(50),  -- cash, mortgage, installments, mixed
    installment_plan TEXT,
    agent_name      VARCHAR(100),
    status          VARCHAR(30) DEFAULT 'signed',  -- signed, active, completed, cancelled
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ANALYTICS SCHEMA (Data Mart)
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.model_registry (
    id              SERIAL PRIMARY KEY,
    model_name      VARCHAR(100) NOT NULL,
    domain          VARCHAR(50) NOT NULL,  -- hotel, restaurant, realestate
    version         VARCHAR(20) NOT NULL,
    algorithm       VARCHAR(100),
    rmse            NUMERIC(10,4),
    mae             NUMERIC(10,4),
    r2_score        NUMERIC(6,4),
    auc_roc         NUMERIC(6,4),
    accuracy        NUMERIC(6,4),
    trained_at      TIMESTAMPTZ DEFAULT NOW(),
    model_path      VARCHAR(500),
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS analytics.predictions_log (
    id              SERIAL PRIMARY KEY,
    model_name      VARCHAR(100) NOT NULL,
    prediction_date TIMESTAMPTZ DEFAULT NOW(),
    input_data      JSONB,
    prediction      JSONB,
    confidence      NUMERIC(5,4)
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_reservations_dates ON hotel.reservations(checkin_date, checkout_date);
CREATE INDEX IF NOT EXISTS idx_reservations_status ON hotel.reservations(status);
CREATE INDEX IF NOT EXISTS idx_reservations_channel ON hotel.reservations(channel);
CREATE INDEX IF NOT EXISTS idx_daily_kpis_date ON hotel.daily_kpis(kpi_date);

CREATE INDEX IF NOT EXISTS idx_sales_tickets_datetime ON restaurant.sales_tickets(sale_datetime);
CREATE INDEX IF NOT EXISTS idx_sales_tickets_service ON restaurant.sales_tickets(service_type);
CREATE INDEX IF NOT EXISTS idx_daily_sales_date ON restaurant.daily_sales_summary(sale_date);

CREATE INDEX IF NOT EXISTS idx_leads_status ON realestate.leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_project ON realestate.leads(project_id);
CREATE INDEX IF NOT EXISTS idx_units_status ON realestate.units(status);
CREATE INDEX IF NOT EXISTS idx_interactions_lead ON realestate.interactions(lead_id);

-- ============================================================
-- SEED: Room Types
-- ============================================================
INSERT INTO hotel.room_types (code, name, capacity, base_rate, description) VALUES
    ('STD', 'Standard Room', 2, 180.00, 'Comfortable standard room with city view'),
    ('DLX', 'Deluxe Room', 2, 280.00, 'Spacious deluxe room with premium amenities'),
    ('JRS', 'Junior Suite', 3, 420.00, 'Junior suite with living area and mountain view'),
    ('STE', 'Suite', 4, 650.00, 'Full suite with separate living room and butler service'),
    ('PEN', 'Penthouse', 6, 1200.00, 'Exclusive penthouse with panoramic views and private terrace')
ON CONFLICT DO NOTHING;

-- ============================================================
-- SEED: Menu Categories
-- ============================================================
INSERT INTO restaurant.menu_categories (name, description) VALUES
    ('Entradas', 'Appetizers and starters'),
    ('Sopas y Cremas', 'Soups and cream soups'),
    ('Platos Principales', 'Main courses'),
    ('Postres', 'Desserts and sweets'),
    ('Bebidas Sin Alcohol', 'Non-alcoholic beverages'),
    ('Vinos y Cocteles', 'Wines and cocktails'),
    ('Desayuno', 'Breakfast items'),
    ('Room Service', 'Room service specialties')
ON CONFLICT DO NOTHING;

-- ============================================================
-- SEED: Real Estate Projects
-- ============================================================
INSERT INTO realestate.projects (name, city, zone, project_type, total_units, start_date, delivery_date, status, description) VALUES
    ('Torre Norte Residencial', 'La Paz', 'Zona Norte', 'residential', 80, '2022-03-01', '2024-12-31', 'construction',
     'Modern residential tower with 80 premium apartments, rooftop pool and gym'),
    ('Central Business Tower', 'Santa Cruz', 'Equipetrol', 'offices', 60, '2023-01-15', '2025-06-30', 'presale',
     'Class A office tower in the financial district, LEED certified'),
    ('Residencias del Parque', 'Santa Cruz', 'Parque Industrial', 'mixed', 120, '2021-06-01', '2024-03-31', 'delivered',
     'Mixed-use complex with residential and commercial spaces')
ON CONFLICT DO NOTHING;
