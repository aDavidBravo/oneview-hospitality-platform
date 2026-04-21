"""
OneView — Restaurant Data Generator
"""
import os
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import date, time, timedelta, datetime
from sqlalchemy import create_engine

fake = Faker('es_ES')
RANDOM_SEED = int(os.getenv('RANDOM_SEED', 42))
random.seed(RANDOM_SEED + 1)
np.random.seed(RANDOM_SEED + 1)

START = date.fromisoformat(os.getenv('DATA_START_DATE', '2023-01-01'))
END   = date.fromisoformat(os.getenv('DATA_END_DATE',   '2024-12-31'))

DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER','oneview_user')}:"
    f"{os.getenv('POSTGRES_PASSWORD','oneview_secret_2024')}@"
    f"{os.getenv('POSTGRES_HOST','postgres')}:"
    f"{os.getenv('POSTGRES_PORT','5432')}/"
    f"{os.getenv('POSTGRES_DB','oneview')}"
)

MENU_ITEMS = [
    # category, name, cost, sell
    ('breakfast', 'Continental Breakfast',    8,  22),
    ('breakfast', 'Full English Breakfast',  10,  28),
    ('breakfast', 'Acai Bowl',                6,  18),
    ('breakfast', 'Eggs Benedict',            9,  24),
    ('lunch',     'Club Sandwich Premium',   12,  32),
    ('lunch',     'Quinoa Salad',             8,  26),
    ('lunch',     'Grilled Salmon',          18,  52),
    ('lunch',     'Wagyu Burger',            20,  58),
    ('dinner',    'Filet Mignon 8oz',        35, 110),
    ('dinner',    'Lobster Thermidor',       45, 135),
    ('dinner',    'Risotto ai Funghi',       14,  48),
    ('dinner',    'Rack of Lamb',            38, 115),
    ('drinks',    'Negroni Clásico',          4,  16),
    ('drinks',    'Champagne Moët',          20,  75),
    ('drinks',    'Mocktail Signature',       3,  12),
    ('desserts',  'Crème Brûlée',             5,  18),
    ('desserts',  'Chocolate Fondant',        6,  20),
    ('desserts',  'Cheesecake NY',            5,  17),
]

SERVICE_HOURS = {
    'breakfast':   (7, 10),
    'lunch':       (12, 15),
    'dinner':      (19, 23),
    'room_service': (0, 24),
}

def daily_covers(d: date, service: str) -> int:
    """Simulate covers per service based on day & season."""
    base = {'breakfast': 60, 'lunch': 45, 'dinner': 55, 'room_service': 20}[service]
    if d.weekday() >= 4:   base = int(base * 1.25)
    if d.month in {12, 1, 7, 8}: base = int(base * 1.20)
    noise = int(np.random.normal(0, base * 0.1))
    return max(5, base + noise)


def generate_menu_items(engine):
    rows = [{
        'name': name,
        'category': cat,
        'cost_price': cost,
        'sell_price': sell,
    } for cat, name, cost, sell in MENU_ITEMS]
    df = pd.DataFrame(rows)
    df.to_sql('menu_items', engine, schema='restaurant', if_exists='append', index=False)
    print(f"  [restaurant] menu_items: {len(df)} rows")
    return df


def generate_inventory(engine):
    ingredients = [
        ('Beef Wagyu', 'kg', 12.0, 3.0, 85),
        ('Fresh Salmon', 'kg', 8.5, 2.0, 60),
        ('Lobster', 'kg', 5.0, 1.5, 95),
        ('Eggs', 'unit', 200, 50, 0.4),
        ('Heavy Cream', 'liter', 15, 5, 8),
        ('Wine Red', 'bottle', 30, 10, 18),
        ('Wine White', 'bottle', 25, 10, 16),
        ('Champagne', 'bottle', 10, 3, 45),
        ('Truffles', 'gr', 100, 30, 2.5),
        ('Quinoa', 'kg', 20, 5, 6),
    ]
    rows = [{
        'ingredient': name,
        'unit': unit,
        'stock_qty': stock,
        'min_stock': min_s,
        'unit_cost': cost,
    } for name, unit, stock, min_s, cost in ingredients]
    df = pd.DataFrame(rows)
    df.to_sql('inventory', engine, schema='restaurant', if_exists='append', index=False)
    print(f"  [restaurant] inventory: {len(df)} rows")


def generate_sales(engine, menu_df):
    date_range = pd.date_range(START, END)
    tickets = []
    ticket_items_rows = []
    summaries = []
    ticket_id = 1
    menu_items_by_cat = {}
    for i, row in menu_df.iterrows():
        cat = row['category']
        menu_items_by_cat.setdefault(cat, []).append((i + 1, row['sell_price']))

    for dt in date_range:
        d = dt.date()
        for service, (h_start, h_end) in SERVICE_HOURS.items():
            covers = daily_covers(d, service)
            tickets_count = max(1, covers // random.randint(1, 3))
            service_revenue = 0.0
            service_covers = 0
            for _ in range(tickets_count):
                h = random.randint(h_start, max(h_start, h_end - 1))
                m = random.randint(0, 59)
                tick_covers = random.randint(1, 4)
                # Select items
                cat_pool = (
                    [service] if service in menu_items_by_cat
                    else ['lunch', 'drinks', 'desserts']
                )
                subtotal = 0.0
                items_selected = []
                for _ in range(random.randint(1, 4)):
                    cat_choice = random.choice(cat_pool)
                    if cat_choice not in menu_items_by_cat:
                        continue
                    item_id, price = random.choice(menu_items_by_cat[cat_choice])
                    qty = random.randint(1, tick_covers)
                    line = round(price * qty, 2)
                    subtotal += line
                    items_selected.append((item_id, qty, price, line))

                subtotal = round(subtotal, 2)
                tax = round(subtotal * 0.13, 2)
                total = round(subtotal + tax, 2)
                channel = 'salon' if service != 'room_service' else 'room_service'
                tickets.append({
                    'ticket_date':   d,
                    'ticket_time':   time(h, m),
                    'service_type':  service,
                    'table_number':  f"T{random.randint(1,30)}",
                    'channel':       channel,
                    'subtotal':      subtotal,
                    'tax_amount':    tax,
                    'total_amount':  total,
                    'covers':        tick_covers,
                })
                for it in items_selected:
                    ticket_items_rows.append({
                        'ticket_id':   ticket_id,
                        'menu_item_id': it[0],
                        'quantity':    it[1],
                        'unit_price':  it[2],
                        'line_total':  it[3],
                    })
                service_revenue += total
                service_covers  += tick_covers
                ticket_id += 1

            avg_tick = round(service_revenue / max(tickets_count, 1), 2)
            summaries.append({
                'sale_date':     d,
                'service_type':  service,
                'total_revenue': round(service_revenue, 2),
                'total_covers':  service_covers,
                'avg_ticket':    avg_tick,
            })

    # Insert
    tick_df = pd.DataFrame(tickets)
    tick_df.to_sql('sales_tickets', engine, schema='restaurant', if_exists='append',
                   index=False, chunksize=500)
    print(f"  [restaurant] sales_tickets: {len(tick_df)} rows")

    items_df = pd.DataFrame(ticket_items_rows)
    items_df.to_sql('ticket_items', engine, schema='restaurant', if_exists='append',
                    index=False, chunksize=1000)
    print(f"  [restaurant] ticket_items: {len(items_df)} rows")

    summ_df = pd.DataFrame(summaries)
    summ_df.to_sql('daily_sales_summary', engine, schema='restaurant', if_exists='append',
                   index=False)
    print(f"  [restaurant] daily_sales_summary: {len(summ_df)} rows")

    os.makedirs('csv_output', exist_ok=True)
    tick_df.to_csv('csv_output/restaurant_tickets.csv', index=False)
    summ_df.to_csv('csv_output/restaurant_daily_summary.csv', index=False)


def run():
    engine = create_engine(DB_URL, pool_pre_ping=True)
    print("[restaurant] Starting data generation...")
    menu_df = generate_menu_items(engine)
    generate_inventory(engine)
    generate_sales(engine, menu_df)
    print("[restaurant] Done!")


if __name__ == '__main__':
    run()
