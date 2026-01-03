# inspect_data.py
import pandas as pd
from sqlalchemy import create_engine, text
import os

db_path = os.path.join(os.getcwd(), 'data', 'market_data.db')
engine = create_engine(f'sqlite:///{db_path}')

print("--- Inspecting Raw Data ---")

# 1. Load raw XOM data WITHOUT parsing dates first (to see the raw string)
df_xom = pd.read_sql(text("SELECT Date, Close FROM prices WHERE Ticker='XOM' LIMIT 5"), engine)

print("\n[Raw XOM Data Sample]")
print(df_xom)
print("\n[Column Types]")
print(df_xom.dtypes)

# 2. Check a specific value in the Close column
sample_price = df_xom['Close'].iloc[0]
print(f"\nSample Price Value: {sample_price} (Type: {type(sample_price)})")
print(f"Sample Date Value: {df_xom['Date'].iloc[0]} (Type: {type(df_xom['Date'].iloc[0])})")