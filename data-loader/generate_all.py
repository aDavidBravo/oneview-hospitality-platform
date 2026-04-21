"""
OneView — Master data generator
Runs all domain generators in sequence.
"""
import time
print("OneView — Synthetic Data Generator")
print("=" * 42)

print("\n[1/3] Generating HOTEL data...")
time.sleep(1)
from generate_hotel import run as hotel_run
hotel_run()

print("\n[2/3] Generating RESTAURANT data...")
time.sleep(1)
from generate_restaurant import run as rest_run
rest_run()

print("\n[3/3] Generating REAL ESTATE data...")
time.sleep(1)
from generate_realestate import run as re_run
re_run()

print("\n✅ All synthetic data generated successfully!")
print("   CSV files saved in: ./csv_output/")
