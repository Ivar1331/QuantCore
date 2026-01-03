# check_db.py
import pandas as pd
from sqlalchemy import create_engine, text # Import 'text'
import os

# Connect to the database
# We use the absolute path to be safe
db_path = os.path.join(os.getcwd(), 'data', 'market_data.db')
engine = create_engine(f'sqlite:///{db_path}')

# Query the database
try:
    print("--- Inspecting Database ---")
    
    # 1. Count total rows
    with engine.connect() as conn:
        # Wrap the string in text(...)
        result = conn.execute(text("SELECT COUNT(*) FROM prices"))
        count = result.fetchone()[0]
        print(f"Total Rows: {count}")

    # 2. Show first 5 rows
    # Pandas read_sql still accepts raw strings, so this part was fine
    df = pd.read_sql("SELECT * FROM prices LIMIT 5", engine)
    print("\nFirst 5 rows:")
    print(df)
    
except Exception as e:
    print(f"Error: {e}")