"""
OneView — Real Estate Data Generator
"""
import os
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import date, timedelta, datetime
from sqlalchemy import create_engine

fake = Faker('es_ES')
RANDOM_SEED = int(os.getenv('RANDOM_SEED', 42))
random.seed(RANDOM_SEED + 2)
np.random.seed(RANDOM_SEED + 2)

START = date.fromisoformat(os.getenv('DATA_START_DATE', '2023-01-01'))
END   = date.fromisoformat(os.getenv('DATA_END_DATE',   '2024-12-31'))

DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER','oneview_user')}:"
    f"{os.getenv('POSTGRES_PASSWORD','oneview_secret_2024')}@"
    f"{os.getenv('POSTGRES_HOST','postgres')}:"
    f"{os.getenv('POSTGRES_PORT','5432')}/"
    f"{os.getenv('POSTGRES_DB','oneview')}"
)

PROJECTS = [
    {'name': 'Green Tower La Paz',   'city': 'La Paz',         'type': 'mixed',       'units': 120, 'start': '2022-01-01', 'delivery': '2025-06-01'},
    {'name': 'Green Tower Santa Cruz','city': 'Santa Cruz',    'type': 'residential', 'units': 200, 'start': '2022-06-01', 'delivery': '2025-12-01'},
    {'name': 'Corporate Hub LPZ',    'city': 'La Paz',         'type': 'offices',     'units':  60, 'start': '2023-01-01', 'delivery': '2026-03-01'},
]

UNIT_TYPES = {
    'mixed':       ['studio','1br','2br','3br','penthouse','office'],
    'residential': ['studio','1br','2br','3br','penthouse'],
    'offices':     ['office','office_large','showroom'],
}

PRICE_RANGES = {
    'studio':       (80000,  130000),
    '1br':          (130000, 200000),
    '2br':          (200000, 320000),
    '3br':          (320000, 500000),
    'penthouse':    (600000, 1200000),
    'office':       (150000, 280000),
    'office_large': (280000, 500000),
    'showroom':     (200000, 400000),
}

CHANNELS = ['web','referral','whatsapp','event','portal_inmobiliario','cold_call','social_media']
CAMPAIGNS = ['Black Friday 2023','Lanzamiento Q1 2023','Feria Inmobiliaria Jul',
             'Digital Summer 2023','Referidos VIP','Black Friday 2024','Lanzamiento Q1 2024']
FUNNEL = ['lead','contact','visit','proposal','reserved','closed','lost']


def generate_projects(engine):
    rows = [{
        'name':         p['name'],
        'city':         p['city'],
        'project_type': p['type'],
        'total_units':  p['units'],
        'start_date':   p['start'],
        'delivery_date':p['delivery'],
        'status':       'active',
        'description':  f"Proyecto premium en {p['city']} — {p['type']}",
    } for p in PROJECTS]
    df = pd.DataFrame(rows)
    df.to_sql('projects', engine, schema='realestate', if_exists='append', index=False)
    print(f"  [realestate] projects: {len(df)} rows")
    return df


def generate_units(engine):
    rows = []
    for pid, p in enumerate(PROJECTS, 1):
        utypes = UNIT_TYPES[p['type']]
        for i in range(p['units']):
            utype = utypes[i % len(utypes)]
            lo, hi = PRICE_RANGES[utype]
            price  = random.randint(lo, hi)
            status = random.choices(
                ['available','reserved','sold'],
                weights=[35, 15, 50]
            )[0]
            rows.append({
                'project_id': pid,
                'unit_code':  f"{p['name'][:3].upper()}-{i+1:04d}",
                'unit_type':  utype,
                'floor':      random.randint(1, 40),
                'area_sqm':   round(random.uniform(35, 220), 1),
                'list_price': price,
                'status':     status,
            })
    df = pd.DataFrame(rows)
    df.to_sql('units', engine, schema='realestate', if_exists='append', index=False)
    print(f"  [realestate] units: {len(df)} rows")
    return df


def generate_leads_and_funnel(engine, units_df):
    date_range = pd.date_range(START, END)
    leads = []
    interactions = []
    contracts = []
    lead_id = 1
    interaction_id = 1
    contract_id = 1

    for pid, p in enumerate(PROJECTS, 1):
        # ~8–15 new leads per project per week
        for week_start in pd.date_range(START, END, freq='W'):
            n_leads = random.randint(6, 14)
            for _ in range(n_leads):
                lead_date = week_start.date() + timedelta(days=random.randint(0, 6))
                if lead_date > END:
                    continue
                channel  = random.choices(CHANNELS, weights=[25,15,20,10,15,5,10])[0]
                campaign = random.choice(CAMPAIGNS)
                interest = random.choices(['cold','warm','hot'], weights=[35,45,20])[0]
                # Determine funnel stage progression
                stage_idx = 0
                stage_weights = [10, 20, 20, 15, 15, 10, 10]
                stage_idx = random.choices(range(len(FUNNEL)), weights=stage_weights)[0]
                stage = FUNNEL[stage_idx]

                utypes = UNIT_TYPES[p['type']]
                leads.append({
                    'project_id':         pid,
                    'full_name':          fake.name(),
                    'email':              fake.email(),
                    'phone':              fake.phone_number(),
                    'source_channel':     channel,
                    'interest_level':     interest,
                    'lead_date':          lead_date,
                    'unit_type_interest': random.choice(utypes),
                    'campaign':           campaign,
                    'funnel_stage':       stage,
                })

                # Generate interactions
                n_interactions = stage_idx + random.randint(0, 2)
                for j in range(n_interactions):
                    idate = datetime.combine(
                        lead_date + timedelta(days=j * random.randint(3, 10)),
                        __import__('datetime').time(random.randint(8,18), random.randint(0,59))
                    )
                    if idate.date() > END:
                        break
                    itype = random.choice(['call','visit','email','meeting','whatsapp'])
                    outcome = random.choice(['interested','not_interested','follow_up','deal_closed'])
                    interactions.append({
                        'lead_id':          lead_id,
                        'interaction_type': itype,
                        'interaction_date': idate,
                        'notes':            fake.sentence(),
                        'outcome':          outcome,
                    })
                    interaction_id += 1

                # Generate contract if closed
                if stage == 'closed':
                    avail_units = units_df[
                        (units_df['project_id'] == pid) & (units_df['status'] == 'sold')
                    ]
                    if len(avail_units) > 0:
                        unit = avail_units.sample(1).iloc[0]
                        discount = round(random.uniform(0, 8), 2)
                        final_price = round(unit['list_price'] * (1 - discount / 100), 2)
                        contract_date = lead_date + timedelta(days=random.randint(15, 90))
                        if contract_date <= END:
                            contracts.append({
                                'lead_id':        lead_id,
                                'unit_id':        int(unit.name) + 1,
                                'contract_date':  contract_date,
                                'final_price':    final_price,
                                'discount_pct':   discount,
                                'payment_method': random.choice(['cash','financing','mixed']),
                                'status':         'active',
                            })
                            contract_id += 1
                lead_id += 1

    leads_df = pd.DataFrame(leads)
    leads_df.to_sql('leads', engine, schema='realestate', if_exists='append',
                    index=False, chunksize=500)
    print(f"  [realestate] leads: {len(leads_df)} rows")

    inter_df = pd.DataFrame(interactions)
    inter_df.to_sql('interactions', engine, schema='realestate', if_exists='append',
                    index=False, chunksize=1000)
    print(f"  [realestate] interactions: {len(inter_df)} rows")

    cont_df = pd.DataFrame(contracts)
    if len(cont_df):
        cont_df.to_sql('contracts', engine, schema='realestate', if_exists='append',
                       index=False)
    print(f"  [realestate] contracts: {len(cont_df)} rows")

    os.makedirs('csv_output', exist_ok=True)
    leads_df.to_csv('csv_output/realestate_leads.csv', index=False)
    cont_df.to_csv('csv_output/realestate_contracts.csv', index=False)


def run():
    engine = create_engine(DB_URL, pool_pre_ping=True)
    print("[realestate] Starting data generation...")
    generate_projects(engine)
    units_df = generate_units(engine)
    generate_leads_and_funnel(engine, units_df)
    print("[realestate] Done!")


if __name__ == '__main__':
    run()
