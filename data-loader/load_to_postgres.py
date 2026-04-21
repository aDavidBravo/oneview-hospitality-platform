"""
OneView Hospitality Platform
Data Generator & Loader - All Domains

Generates 24 months of realistic synthetic data for:
- Hotel: rooms, guests, reservations, daily KPIs
- Restaurant: menu items, sales tickets, daily summaries  
- Real Estate: leads, interactions, contracts

Runs via Docker as one-time setup job.
"""

import os
import sys
import random
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

import numpy as np
import pandas as pd
from faker import Faker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RANDOM_SEED = int(os.getenv('RANDOM_SEED', 42))
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

fake = Faker(['es_ES', 'en_US', 'pt_BR', 'de_DE', 'fr_FR'])
Faker.seed(RANDOM_SEED)

DATA_START = date(2023, 1, 1)
DATA_END = date(2024, 12, 31)
TOTAL_ROOMS = 120

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://oneview:oneview_secure_2024@localhost:5432/oneview_db')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_season_multiplier(d: date) -> float:
    """Bolivia/South America seasonality: high Dec-Jan-Feb (summer/carnival)"""
    month = d.month
    if month in (12, 1, 2):   # Summer / Carnival
        return 1.35
    elif month in (6, 7, 8):  # Winter but school vacation
        return 1.20
    elif month in (9, 10, 11): # Spring shoulder
        return 1.05
    else:                       # Autumn shoulder
        return 0.95


def get_weekday_multiplier(d: date) -> float:
    """Weekends higher for hotel leisure, weekdays higher for business"""
    dow = d.weekday()  # 0=Mon, 6=Sun
    multipliers = [0.80, 0.82, 0.85, 0.90, 1.05, 1.25, 1.15]  # Mon-Sun
    return multipliers[dow]


def is_holiday_period(d: date) -> bool:
    """Bolivian holidays approximation"""
    # Carnival (approx Feb)
    if d.month == 2 and 5 <= d.day <= 20:
        return True
    # Semana Santa (approx Apr)
    if d.month == 4 and 8 <= d.day <= 16:
        return True
    # Todos Santos (Nov)
    if d.month == 11 and 1 <= d.day <= 3:
        return True
    # Christmas/New Year
    if (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 7):
        return True
    return False


# ============================================================
# HOTEL DATA GENERATION
# ============================================================

def generate_rooms(engine):
    """Generate 120 hotel rooms across 10 floors"""
    logger.info("Generating hotel rooms...")
    
    room_type_map = {
        'STD': (1, 80),   # 80 standard rooms
        'DLX': (2, 24),   # 24 deluxe
        'JRS': (3, 10),   # 10 junior suites
        'STE': (4, 4),    # 4 suites
        'PEN': (5, 2),    # 2 penthouses
    }
    
    rooms = []
    room_counter = 100
    
    for type_code, (type_id, count) in room_type_map.items():
        for i in range(count):
            room_counter += 1
            floor = (room_counter % 10) + 1
            rooms.append({
                'room_number': str(room_counter),
                'room_type_id': type_id,
                'floor': floor,
                'status': 'available'
            })
    
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO hotel.rooms (room_number, room_type_id, floor, status) "
            "VALUES (:room_number, :room_type_id, :floor, :status) "
            "ON CONFLICT (room_number) DO NOTHING"
        ), rooms)
    
    logger.info(f"  Inserted {len(rooms)} rooms")
    return rooms


def generate_guests(engine, n=800):
    """Generate realistic hotel guests from various countries"""
    logger.info(f"Generating {n} hotel guests...")
    
    country_distribution = [
        ('BO', 'Bolivia', 0.30),
        ('BR', 'Brazil', 0.15),
        ('AR', 'Argentina', 0.12),
        ('CL', 'Chile', 0.08),
        ('PE', 'Peru', 0.08),
        ('US', 'United States', 0.10),
        ('DE', 'Germany', 0.05),
        ('FR', 'France', 0.04),
        ('ES', 'Spain', 0.04),
        ('GB', 'United Kingdom', 0.04),
    ]
    
    countries = [c[0] for c in country_distribution]
    weights = [c[2] for c in country_distribution]
    
    trip_purposes = ['business', 'leisure', 'event', 'honeymoon', 'medical', 'education']
    purpose_weights = [0.35, 0.30, 0.15, 0.08, 0.07, 0.05]
    
    guests = []
    for _ in range(n):
        country = random.choices(countries, weights=weights)[0]
        guests.append({
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.unique.email(),
            'phone': fake.phone_number()[:50],
            'country_code': country,
            'loyalty_tier': random.choices(
                ['standard', 'silver', 'gold', 'platinum'],
                weights=[0.60, 0.25, 0.10, 0.05]
            )[0],
            'total_stays': random.randint(0, 15)
        })
    
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO hotel.guests (first_name, last_name, email, phone, country_code, loyalty_tier, total_stays) "
            "VALUES (:first_name, :last_name, :email, :phone, :country_code, :loyalty_tier, :total_stays) "
            "ON CONFLICT (email) DO NOTHING"
        ), guests)
    
    logger.info(f"  Inserted {len(guests)} guests")


def generate_reservations_and_kpis(engine):
    """Generate 24 months of reservations and compute daily KPIs"""
    logger.info("Generating hotel reservations and KPIs...")
    
    channels = ['direct', 'booking.com', 'expedia', 'airbnb', 'phone', 'travel_agency']
    channel_weights = [0.25, 0.30, 0.20, 0.10, 0.10, 0.05]
    
    trip_purposes = ['business', 'leisure', 'event', 'honeymoon', 'medical']
    purpose_weights = [0.35, 0.30, 0.15, 0.12, 0.08]
    
    # Get rooms and guests from DB
    with engine.connect() as conn:
        rooms_result = conn.execute(text(
            "SELECT r.id, rt.base_rate FROM hotel.rooms r "
            "JOIN hotel.room_types rt ON r.room_type_id = rt.id"
        )).fetchall()
        guest_ids = [row[0] for row in conn.execute(text("SELECT id FROM hotel.guests")).fetchall()]
    
    rooms = [(r[0], float(r[1])) for r in rooms_result]
    
    reservations = []
    res_code = 1000
    current_date = DATA_START
    
    daily_kpis = []
    
    while current_date <= DATA_END:
        season_mult = get_season_multiplier(current_date)
        weekday_mult = get_weekday_multiplier(current_date)
        holiday_bonus = 1.20 if is_holiday_period(current_date) else 1.0
        
        # Base occupancy target
        base_occ = 0.68
        target_occ = min(0.97, base_occ * season_mult * weekday_mult * holiday_bonus)
        target_occ += np.random.normal(0, 0.04)  # noise
        target_occ = max(0.35, min(0.97, target_occ))
        
        occupied = int(TOTAL_ROOMS * target_occ)
        
        # Generate some new reservations that start today
        for i in range(max(1, int(occupied * 0.30))):
            res_code += 1
            room = random.choice(rooms)
            room_id, base_rate = room
            nights = random.choices([1, 2, 3, 4, 5, 7, 10], weights=[0.25, 0.25, 0.20, 0.15, 0.08, 0.05, 0.02])[0]
            
            # Dynamic pricing
            rate = base_rate * season_mult * weekday_mult
            rate *= random.uniform(0.85, 1.20)  # channel/demand variance
            rate = round(rate, 2)
            
            total = round(rate * nights, 2)
            guest_id = random.choice(guest_ids)
            channel = random.choices(channels, weights=channel_weights)[0]
            
            reservations.append({
                'reservation_code': f'RES{res_code:06d}',
                'guest_id': guest_id,
                'room_id': room_id,
                'checkin_date': current_date,
                'checkout_date': current_date + timedelta(days=nights),
                'adults': random.choices([1, 2, 3], weights=[0.3, 0.55, 0.15])[0],
                'children': random.choices([0, 1, 2], weights=[0.7, 0.2, 0.1])[0],
                'channel': channel,
                'trip_purpose': random.choices(trip_purposes, weights=purpose_weights)[0],
                'rate_per_night': rate,
                'total_amount': total,
                'status': random.choices(
                    ['confirmed', 'checked_in', 'checked_out', 'cancelled', 'no_show'],
                    weights=[0.10, 0.05, 0.78, 0.05, 0.02]
                )[0]
            })
        
        # Compute daily revenue
        revenue_estimate = occupied * (np.mean([r[1] for r in rooms[:80]]) * season_mult * weekday_mult)
        adr = revenue_estimate / occupied if occupied > 0 else 0
        revpar = revenue_estimate / TOTAL_ROOMS
        
        daily_kpis.append({
            'kpi_date': current_date,
            'total_rooms': TOTAL_ROOMS,
            'occupied_rooms': occupied,
            'occupancy_rate': round(target_occ * 100, 2),
            'adr': round(adr, 2),
            'revpar': round(revpar, 2),
            'total_revenue': round(revenue_estimate, 2)
        })
        
        current_date += timedelta(days=1)
    
    # Insert reservations in batches
    batch_size = 500
    total_inserted = 0
    with engine.begin() as conn:
        for i in range(0, len(reservations), batch_size):
            batch = reservations[i:i+batch_size]
            conn.execute(text(
                "INSERT INTO hotel.reservations "
                "(reservation_code, guest_id, room_id, checkin_date, checkout_date, adults, children, "
                "channel, trip_purpose, rate_per_night, total_amount, status) "
                "VALUES (:reservation_code, :guest_id, :room_id, :checkin_date, :checkout_date, :adults, :children, "
                ":channel, :trip_purpose, :rate_per_night, :total_amount, :status) "
                "ON CONFLICT (reservation_code) DO NOTHING"
            ), batch)
            total_inserted += len(batch)
        
        conn.execute(text(
            "INSERT INTO hotel.daily_kpis (kpi_date, total_rooms, occupied_rooms, occupancy_rate, adr, revpar, total_revenue) "
            "VALUES (:kpi_date, :total_rooms, :occupied_rooms, :occupancy_rate, :adr, :revpar, :total_revenue) "
            "ON CONFLICT (kpi_date) DO NOTHING"
        ), daily_kpis)
    
    logger.info(f"  Inserted {total_inserted} reservations")
    logger.info(f"  Inserted {len(daily_kpis)} daily KPI records")


# ============================================================
# RESTAURANT DATA GENERATION
# ============================================================

def generate_menu_items(engine):
    logger.info("Generating menu items...")
    
    items = [
        # Breakfast (cat 7)
        (7, 'Desayuno Americano Completo', 18.00, 5.50, 'breakfast'),
        (7, 'Eggs Benedict Premium', 22.00, 7.00, 'breakfast'),
        (7, 'Granola con Frutas Frescas', 15.00, 4.00, 'breakfast'),
        (7, 'Smoothie Bowl Tropical', 16.00, 4.50, 'breakfast'),
        (7, 'Crepes con Miel y Frutas', 14.00, 4.00, 'breakfast'),
        # Entradas (cat 1)
        (1, 'Carpaccio de Wagyu', 28.00, 9.00, 'lunch'),
        (1, 'Ceviche de Maríscos Gourmet', 24.00, 8.00, 'lunch'),
        (1, 'Burrata con Tomates Heritage', 22.00, 7.50, 'lunch'),
        (1, 'Tabla de Quesos Artesanales', 32.00, 10.00, 'dinner'),
        # Principales (cat 3)
        (3, 'Lomo a la Pimienta Verde', 48.00, 15.00, 'dinner'),
        (3, 'Salmón con Risotto de Azafrán', 44.00, 14.00, 'dinner'),
        (3, 'Pichón con Foie Gras', 58.00, 18.00, 'dinner'),
        (3, 'Pasta Fresca Trufa Negra', 42.00, 13.00, 'lunch'),
        (3, 'Cordero al Romero', 52.00, 16.00, 'dinner'),
        # Postres (cat 4)
        (4, 'Crème Brûlée Clásica', 16.00, 4.50, 'dinner'),
        (4, 'Soufflé de Chocolate', 18.00, 5.00, 'dinner'),
        (4, 'Helado Artesanal 3 Sabores', 14.00, 4.00, 'lunch'),
        # Bebidas (cat 5)
        (5, 'Agua Mineral Premium', 8.00, 1.50, 'lunch'),
        (5, 'Jugo Fresco de Temporada', 12.00, 2.50, 'breakfast'),
        (5, 'Café Espresso de Origen', 10.00, 2.00, 'breakfast'),
        # Vinos (cat 6)
        (6, 'Vino Malbec Reserva', 65.00, 22.00, 'dinner'),
        (6, 'Champagne Brut', 95.00, 32.00, 'dinner'),
        (6, 'Cóctel Signature del Chef', 22.00, 7.00, 'bar'),
        # Room Service (cat 8)
        (8, 'Club Sandwich Premium', 28.00, 8.00, 'room_service'),
        (8, 'Tabla de Embutidos', 35.00, 11.00, 'room_service'),
    ]
    
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO restaurant.menu_items (category_id, name, sale_price, cost_price, service_type, active) "
            "VALUES (:cat, :name, :sale, :cost, :svc, true) ON CONFLICT DO NOTHING"
        ), [{'cat': i[0], 'name': i[1], 'sale': i[2], 'cost': i[3], 'svc': i[4]} for i in items])
    
    logger.info(f"  Inserted {len(items)} menu items")


def generate_restaurant_sales(engine):
    logger.info("Generating restaurant sales (24 months)...")
    
    # Get menu items
    with engine.connect() as conn:
        menu_items = conn.execute(text(
            "SELECT id, sale_price, service_type FROM restaurant.menu_items WHERE active = true"
        )).fetchall()
        guest_ids = [row[0] for row in conn.execute(text("SELECT id FROM hotel.guests")).fetchall()]
    
    items_by_service = {}
    for item in menu_items:
        svc = item[2]
        if svc not in items_by_service:
            items_by_service[svc] = []
        items_by_service[svc].append((item[0], float(item[1])))
    
    services_schedule = {
        'breakfast': {'start': 7, 'end': 11, 'base_covers': 45},
        'lunch': {'start': 12, 'end': 16, 'base_covers': 35},
        'dinner': {'start': 19, 'end': 23, 'base_covers': 55},
        'bar': {'start': 17, 'end': 24, 'base_covers': 20},
        'room_service': {'start': 0, 'end': 24, 'base_covers': 15},
    }
    
    all_tickets = []
    all_ticket_items = []
    daily_summaries = []
    ticket_num = 10000
    
    current_date = DATA_START
    while current_date <= DATA_END:
        season_mult = get_season_multiplier(current_date)
        weekday_mult = get_weekday_multiplier(current_date)
        
        day_summaries = {}
        
        for service_type, schedule in services_schedule.items():
            base_covers = schedule['base_covers']
            
            # Restaurant has different patterns
            if service_type == 'dinner':
                covers = int(base_covers * season_mult * weekday_mult * random.uniform(0.8, 1.3))
            elif service_type == 'breakfast':
                # Breakfast linked to hotel occupancy
                covers = int(base_covers * season_mult * random.uniform(0.7, 1.1))
            else:
                covers = int(base_covers * random.uniform(0.6, 1.4))
            
            covers = max(2, covers)
            
            # Generate individual tickets
            service_items = items_by_service.get(service_type, items_by_service.get('lunch', []))
            if not service_items:
                continue
            
            service_revenue = 0
            service_tickets = 0
            
            for _ in range(max(1, covers // 2)):  # ~2 people per ticket avg
                ticket_num += 1
                hour = random.randint(schedule['start'], min(schedule['end'] - 1, 23))
                minute = random.randint(0, 59)
                dt = datetime.combine(current_date, datetime.min.time()).replace(
                    hour=hour, minute=minute
                )
                
                # Items per ticket
                n_items = random.choices([1, 2, 3, 4, 5], weights=[0.15, 0.25, 0.30, 0.20, 0.10])[0]
                selected_items = random.choices(service_items, k=n_items)
                
                subtotal = sum(price for _, price in selected_items)
                subtotal = round(subtotal, 2)
                tax = round(subtotal * 0.13, 2)  # 13% IVA Bolivia
                tip = round(subtotal * random.uniform(0, 0.15), 2)
                total = round(subtotal + tax + tip, 2)
                
                ticket = {
                    'ticket_number': f'TK{ticket_num:08d}',
                    'sale_datetime': dt,
                    'service_type': service_type,
                    'table_number': f'T{random.randint(1, 30):02d}',
                    'covers': random.randint(1, 4),
                    'subtotal': subtotal,
                    'tax_amount': tax,
                    'tip_amount': tip,
                    'total_amount': total,
                    'payment_method': random.choices(
                        ['card', 'cash', 'room_charge'],
                        weights=[0.55, 0.25, 0.20]
                    )[0],
                    'guest_id': random.choice(guest_ids) if random.random() < 0.4 else None
                }
                all_tickets.append(ticket)
                service_revenue += total
                service_tickets += 1
            
            day_summaries[service_type] = {
                'sale_date': current_date,
                'service_type': service_type,
                'total_tickets': service_tickets,
                'total_covers': covers,
                'total_revenue': round(service_revenue, 2),
                'avg_ticket': round(service_revenue / service_tickets, 2) if service_tickets > 0 else 0
            }
        
        daily_summaries.extend(day_summaries.values())
        current_date += timedelta(days=1)
    
    # Insert in batches
    batch_size = 1000
    logger.info(f"  Inserting {len(all_tickets)} restaurant tickets...")
    
    with engine.begin() as conn:
        for i in range(0, len(all_tickets), batch_size):
            batch = all_tickets[i:i+batch_size]
            conn.execute(text(
                "INSERT INTO restaurant.sales_tickets "
                "(ticket_number, sale_datetime, service_type, table_number, covers, subtotal, tax_amount, tip_amount, total_amount, payment_method, guest_id) "
                "VALUES (:ticket_number, :sale_datetime, :service_type, :table_number, :covers, :subtotal, :tax_amount, :tip_amount, :total_amount, :payment_method, :guest_id) "
                "ON CONFLICT (ticket_number) DO NOTHING"
            ), batch)
        
        for i in range(0, len(daily_summaries), batch_size):
            batch = daily_summaries[i:i+batch_size]
            conn.execute(text(
                "INSERT INTO restaurant.daily_sales_summary "
                "(sale_date, service_type, total_tickets, total_covers, total_revenue, avg_ticket) "
                "VALUES (:sale_date, :service_type, :total_tickets, :total_covers, :total_revenue, :avg_ticket) "
                "ON CONFLICT (sale_date, service_type) DO NOTHING"
            ), batch)
    
    logger.info(f"  Inserted {len(all_tickets)} tickets and {len(daily_summaries)} daily summaries")


# ============================================================
# REAL ESTATE DATA GENERATION
# ============================================================

def generate_units(engine):
    logger.info("Generating real estate units...")
    
    # Projects: 1=80 units residential, 2=60 offices, 3=120 mixed
    unit_configs = [
        # (project_id, unit_type, count, area_min, area_max, price_min, price_max)
        (1, 'studio', 10, 45, 55, 95000, 115000),
        (1, '1br', 25, 65, 80, 130000, 165000),
        (1, '2br', 30, 90, 115, 180000, 230000),
        (1, '3br', 15, 130, 160, 260000, 320000),
        (2, 'office_s', 20, 50, 80, 120000, 180000),
        (2, 'office_m', 25, 90, 150, 200000, 320000),
        (2, 'office_l', 15, 160, 280, 350000, 580000),
        (3, 'studio', 20, 42, 52, 88000, 108000),
        (3, '1br', 35, 62, 78, 125000, 155000),
        (3, '2br', 40, 88, 110, 175000, 220000),
        (3, '3br', 15, 125, 155, 250000, 310000),
        (3, 'office_s', 10, 48, 75, 115000, 170000),
    ]
    
    units = []
    unit_counter = 0
    
    for proj_id, utype, count, area_min, area_max, price_min, price_max in unit_configs:
        for i in range(count):
            unit_counter += 1
            floor = random.randint(1, 20)
            area = round(random.uniform(area_min, area_max), 1)
            price = round(random.uniform(price_min, price_max), -3)  # Round to 1000
            
            units.append({
                'project_id': proj_id,
                'unit_code': f'P{proj_id}-{utype[:2].upper()}{unit_counter:04d}',
                'unit_type': utype,
                'floor': floor,
                'area_sqm': area,
                'list_price': price,
                'status': random.choices(
                    ['available', 'reserved', 'sold'],
                    weights=[0.35, 0.15, 0.50]
                )[0],
                'bedrooms': {'studio': 0, '1br': 1, '2br': 2, '3br': 3}.get(utype, 0),
                'bathrooms': {'studio': 1.0, '1br': 1.0, '2br': 2.0, '3br': 3.0}.get(utype, 1.0),
                'parking_spots': 1 if 'office' not in utype else 2
            })
    
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO realestate.units "
            "(project_id, unit_code, unit_type, floor, area_sqm, list_price, status, bedrooms, bathrooms, parking_spots) "
            "VALUES (:project_id, :unit_code, :unit_type, :floor, :area_sqm, :list_price, :status, :bedrooms, :bathrooms, :parking_spots) "
            "ON CONFLICT DO NOTHING"
        ), units)
    
    logger.info(f"  Inserted {len(units)} units")


def generate_leads_and_interactions(engine):
    logger.info("Generating real estate leads, interactions and contracts...")
    
    sources = ['web', 'referral', 'social_media', 'billboard', 'event', 'cold_call', 'partner']
    source_weights = [0.30, 0.20, 0.20, 0.10, 0.08, 0.07, 0.05]
    
    agents = ['Carlos Mendoza', 'Sofía Quispe', 'Roberto Arce', 'Valentina Paz', 'Diego Flores']
    
    interaction_types = ['call', 'email', 'whatsapp', 'showroom_visit', 'virtual_tour']
    
    leads = []
    interactions_data = []
    contracts_data = []
    
    current_date = DATA_START
    lead_id_counter = 0
    
    # Generate leads over time
    while current_date <= DATA_END:
        # More leads in construction/presale phases
        month = current_date.month
        n_leads_today = random.choices([0, 1, 2, 3, 4], weights=[0.40, 0.30, 0.15, 0.10, 0.05])[0]
        
        for _ in range(n_leads_today):
            lead_id_counter += 1
            project_id = random.choices([1, 2, 3], weights=[0.40, 0.30, 0.30])[0]
            source = random.choices(sources, weights=source_weights)[0]
            
            n_interactions = random.randint(1, 12)
            days_in_funnel = random.randint(3, 180)
            has_visit = n_interactions >= 3 and random.random() > 0.4
            
            # Conversion probability based on features
            p_convert = 0.20
            if has_visit:
                p_convert += 0.25
            if source in ['referral', 'event']:
                p_convert += 0.15
            if n_interactions >= 5:
                p_convert += 0.10
            p_convert = min(0.75, p_convert)
            
            status = 'converted' if random.random() < p_convert else random.choices(
                ['new', 'contacted', 'nurturing', 'qualified', 'lost'],
                weights=[0.05, 0.20, 0.30, 0.25, 0.20]
            )[0]
            
            lead = {
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'email': fake.unique.email(),
                'phone': fake.phone_number()[:50],
                'source_channel': source,
                'interest_level': random.choices(['cold', 'warm', 'hot'], weights=[0.30, 0.45, 0.25])[0],
                'project_id': project_id,
                'unit_type_interest': random.choices(
                    ['studio', '1br', '2br', '3br', 'office_m'],
                    weights=[0.10, 0.25, 0.35, 0.20, 0.10]
                )[0],
                'budget_max': random.choice([150000, 200000, 250000, 300000, 400000, 500000]),
                'status': status,
                'assigned_to': random.choice(agents),
                'created_at': datetime.combine(current_date, datetime.min.time()),
            }
            leads.append(lead)
            
            # Generate interactions for this lead
            interaction_date = current_date
            for j in range(n_interactions):
                itype = 'showroom_visit' if (j == 2 and has_visit) else random.choices(
                    interaction_types, weights=[0.35, 0.25, 0.20, 0.10, 0.10]
                )[0]
                
                interactions_data.append({
                    'lead_idx': lead_id_counter - 1,  # will resolve after insert
                    'interaction_type': itype,
                    'interaction_date': datetime.combine(interaction_date, datetime.min.time()),
                    'duration_minutes': random.randint(5, 60),
                    'notes': f'{itype.replace("_", " ").title()} - lead expressed interest in project',
                    'outcome': random.choices(
                        ['interested', 'not_interested', 'callback', 'visit_scheduled'],
                        weights=[0.45, 0.15, 0.25, 0.15]
                    )[0],
                    'agent_name': lead['assigned_to']
                })
                interaction_date += timedelta(days=random.randint(2, 15))
        
        current_date += timedelta(days=1)
    
    logger.info(f"  Inserting {len(leads)} leads...")
    
    # Insert leads and get their IDs
    with engine.begin() as conn:
        for lead in leads:
            lead_copy = {k: v for k, v in lead.items()}
            conn.execute(text(
                "INSERT INTO realestate.leads "
                "(first_name, last_name, email, phone, source_channel, interest_level, "
                "project_id, unit_type_interest, budget_max, status, assigned_to, created_at) "
                "VALUES (:first_name, :last_name, :email, :phone, :source_channel, :interest_level, "
                ":project_id, :unit_type_interest, :budget_max, :status, :assigned_to, :created_at) "
                "ON CONFLICT DO NOTHING"
            ), lead_copy)
    
    # Get lead IDs and available units
    with engine.connect() as conn:
        db_leads = conn.execute(text(
            "SELECT id, status, project_id FROM realestate.leads ORDER BY id"
        )).fetchall()
        
        units_by_project = {}
        for row in conn.execute(text(
            "SELECT id, project_id, list_price FROM realestate.units WHERE status IN ('sold', 'reserved')"
        )).fetchall():
            pid = row[1]
            if pid not in units_by_project:
                units_by_project[pid] = []
            units_by_project[pid].append((row[0], float(row[2])))
    
    # Generate contracts for converted leads
    contracts_batch = []
    for db_lead in db_leads:
        lead_id, status, project_id = db_lead
        if status == 'converted':
            available_units = units_by_project.get(project_id, [])
            if not available_units:
                continue
            unit_id, list_price = random.choice(available_units)
            discount = random.uniform(0, 0.08)  # 0-8% discount
            final_price = round(list_price * (1 - discount), -2)
            
            contracts_batch.append({
                'lead_id': lead_id,
                'unit_id': unit_id,
                'contract_date': (DATA_START + timedelta(days=random.randint(30, 600))).strftime('%Y-%m-%d'),
                'final_price': final_price,
                'discount_pct': round(discount * 100, 2),
                'payment_method': random.choices(
                    ['mortgage', 'cash', 'installments', 'mixed'],
                    weights=[0.45, 0.20, 0.25, 0.10]
                )[0],
                'agent_name': random.choice(agents),
                'status': 'active'
            })
    
    with engine.begin() as conn:
        if contracts_batch:
            conn.execute(text(
                "INSERT INTO realestate.contracts "
                "(lead_id, unit_id, contract_date, final_price, discount_pct, payment_method, agent_name, status) "
                "VALUES (:lead_id, :unit_id, :contract_date, :final_price, :discount_pct, :payment_method, :agent_name, :status) "
                "ON CONFLICT DO NOTHING"
            ), contracts_batch)
    
    logger.info(f"  Inserted {len(db_leads)} leads, {len(contracts_batch)} contracts")


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    logger.info("=" * 60)
    logger.info("OneView Hospitality Platform - Data Loader")
    logger.info("=" * 60)
    
    import time
    time.sleep(5)  # Wait for postgres to be fully ready
    
    logger.info(f"Connecting to: {DATABASE_URL[:50]}...")
    
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        logger.info("Database connection OK")
        
        # Hotel domain
        logger.info("\n[1/3] Loading HOTEL domain...")
        generate_rooms(engine)
        generate_guests(engine, n=800)
        generate_reservations_and_kpis(engine)
        
        # Restaurant domain
        logger.info("\n[2/3] Loading RESTAURANT domain...")
        generate_menu_items(engine)
        generate_restaurant_sales(engine)
        
        # Real Estate domain
        logger.info("\n[3/3] Loading REAL ESTATE domain...")
        generate_units(engine)
        generate_leads_and_interactions(engine)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Data loading COMPLETE!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        raise


if __name__ == '__main__':
    main()
