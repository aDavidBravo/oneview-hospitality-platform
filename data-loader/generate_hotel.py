"""
OneView — Hotel Data Generator
Generates 24 months of realistic synthetic hotel data with seasonality.
"""
import os
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import date, timedelta
from sqlalchemy import create_engine, text

fake = Faker(['es_ES', 'en_US', 'pt_BR'])
RANDOM_SEED = int(os.getenv('RANDOM_SEED', 42))
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
fake.seed_instance(RANDOM_SEED)

START = date.fromisoformat(os.getenv('DATA_START_DATE', '2023-01-01'))
END   = date.fromisoformat(os.getenv('DATA_END_DATE',   '2024-12-31'))

DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER','oneview_user')}:"
    f"{os.getenv('POSTGRES_PASSWORD','oneview_secret_2024')}@"
    f"{os.getenv('POSTGRES_HOST','postgres')}:"
    f"{os.getenv('POSTGRES_PORT','5432')}/"
    f"{os.getenv('POSTGRES_DB','oneview')}"
)

# ── Room catalogue ─────────────────────────────────────────────────
ROOM_TYPES = {
    'standard':     {'count': 60, 'base_rate': 150, 'capacity': 2},
    'deluxe':       {'count': 40, 'base_rate': 220, 'capacity': 2},
    'suite':        {'count': 20, 'base_rate': 380, 'capacity': 3},
    'presidential': {'count': 5,  'base_rate': 650, 'capacity': 4},
}
TOTAL_ROOMS = sum(v['count'] for v in ROOM_TYPES.values())  # 125 rooms

# ── Seasonality helper ────────────────────────────────────────────
HIGH_SEASON_MONTHS = {1, 2, 7, 8, 12}  # Jan, Feb, Jul, Aug, Dec
WEEKEND_DAYS = {4, 5, 6}  # Fri, Sat, Sun

def occupancy_multiplier(d: date) -> float:
    base = 0.62
    if d.month in HIGH_SEASON_MONTHS:
        base += 0.18
    if d.weekday() in WEEKEND_DAYS:
        base += 0.10
    # Add slight random noise
    return min(0.97, max(0.30, base + np.random.normal(0, 0.04)))

def rate_multiplier(d: date) -> float:
    base = 1.0
    if d.month in HIGH_SEASON_MONTHS:
        base += 0.25
    if d.weekday() in WEEKEND_DAYS:
        base += 0.12
    return base + np.random.normal(0, 0.05)


def generate_rooms(engine):
    rows = []
    room_num = 101
    floor_start = 1
    for rtype, cfg in ROOM_TYPES.items():
        for i in range(cfg['count']):
            rows.append({
                'room_number': str(room_num),
                'room_type': rtype,
                'capacity': cfg['capacity'],
                'base_rate': cfg['base_rate'],
                'floor': floor_start + (i // 10),
            })
            room_num += 1
        floor_start += cfg['count'] // 10 + 1
    df = pd.DataFrame(rows)
    df.to_sql('rooms', engine, schema='hotel', if_exists='append', index=False)
    print(f"  [hotel] rooms: {len(df)} rows")
    return df


def generate_guests(engine, n=3000):
    countries = ['Bolivia','Argentina','Brasil','Chile','Colombia','Peru','EEUU','Alemania','España','Francia']
    purposes  = ['tourism','business','event','honeymoon']
    rows = []
    for _ in range(n):
        rows.append({
            'first_name':     fake.first_name(),
            'last_name':      fake.last_name(),
            'email':          fake.unique.email(),
            'country':        random.choice(countries),
            'travel_purpose': random.choices(purposes, weights=[50,30,15,5])[0],
            'loyalty_tier':   random.choices(['standard','silver','gold','platinum'],
                                             weights=[60,25,12,3])[0],
        })
    df = pd.DataFrame(rows)
    df.to_sql('guests', engine, schema='hotel', if_exists='append', index=False)
    print(f"  [hotel] guests: {len(df)} rows")
    return df


def generate_reservations_and_kpis(engine, rooms_df):
    channels = ['direct','booking.com','expedia','corporate','airbnb','travel_agency']
    date_range = pd.date_range(START, END)
    reservations = []
    kpis = []

    # Pre-load room ids per type for fast lookup
    room_ids = rooms_df.reset_index()['index'].add(1).tolist()  # sequential ids

    for dt in date_range:
        d = dt.date()
        occ = occupancy_multiplier(d)
        rm  = rate_multiplier(d)
        occupied = max(1, int(TOTAL_ROOMS * occ))
        daily_revenue = 0.0

        sampled_rooms = random.sample(range(1, TOTAL_ROOMS + 1), occupied)
        for room_id in sampled_rooms:
            # Determine room type & rate
            rt_idx = room_id - 1
            type_cumul = 0
            chosen_type = 'standard'
            chosen_rate = 150
            for rtype, cfg in ROOM_TYPES.items():
                type_cumul += cfg['count']
                if rt_idx < type_cumul:
                    chosen_type = rtype
                    chosen_rate = cfg['base_rate']
                    break
            rate = round(chosen_rate * rm * random.uniform(0.9, 1.1), 2)
            nights = random.choices([1,2,3,4,5,6,7],[30,28,20,12,6,3,1])[0]
            total = round(rate * nights, 2)
            daily_revenue += rate
            reservations.append({
                'room_id':       room_id,
                'guest_id':      random.randint(1, 3000),
                'checkin_date':  d,
                'checkout_date': d + timedelta(days=nights),
                'status':        random.choices(['confirmed','checked_in','checked_out','cancelled'],
                                               weights=[10,25,63,2])[0],
                'channel':       random.choices(channels, weights=[30,25,15,15,10,5])[0],
                'rate_charged':  rate,
                'total_amount':  total,
            })

        adr    = round(daily_revenue / occupied, 2) if occupied else 0
        revpar = round(daily_revenue / TOTAL_ROOMS, 2)
        kpis.append({
            'kpi_date':       d,
            'total_rooms':    TOTAL_ROOMS,
            'occupied_rooms': occupied,
            'occupancy_rate': round(occ * 100, 2),
            'adr':            adr,
            'revpar':         revpar,
            'total_revenue':  round(daily_revenue, 2),
        })

    # Batch insert
    res_df = pd.DataFrame(reservations)
    res_df.to_sql('reservations', engine, schema='hotel', if_exists='append', index=False,
                  chunksize=1000)
    kpi_df = pd.DataFrame(kpis)
    kpi_df.to_sql('daily_kpis', engine, schema='hotel', if_exists='append', index=False)

    os.makedirs('csv_output', exist_ok=True)
    res_df.to_csv('csv_output/hotel_reservations.csv', index=False)
    kpi_df.to_csv('csv_output/hotel_daily_kpis.csv', index=False)
    print(f"  [hotel] reservations: {len(res_df)} rows")
    print(f"  [hotel] daily_kpis:   {len(kpi_df)} rows")


def run():
    engine = create_engine(DB_URL, pool_pre_ping=True)
    print("[hotel] Starting data generation...")
    rooms_df = generate_rooms(engine)
    generate_guests(engine)
    generate_reservations_and_kpis(engine, rooms_df)
    print("[hotel] Done!")


if __name__ == '__main__':
    run()
