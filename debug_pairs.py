# debug_pairs.py
import os
from sqlalchemy import create_engine, text

db_path = os.path.join(os.getcwd(), 'data', 'market_data.db')
engine = create_engine(f'sqlite:///{db_path}')

with engine.connect() as conn:
    print("--- Database Content Check ---")
    
    # Check XOM
    xom_count = conn.execute(text("SELECT COUNT(*) FROM prices WHERE Ticker='XOM'")).fetchone()[0]
    print(f"Rows for XOM: {xom_count}")
    
    # Check CVX
    cvx_count = conn.execute(text("SELECT COUNT(*) FROM prices WHERE Ticker='CVX'")).fetchone()[0]
    print(f"Rows for CVX: {cvx_count}")
    
    if xom_count == 0 or cvx_count == 0:
        print("\n❌ PROBLEM FOUND: One or both tickers are missing.")
        print("   Solution: You need to run 'setup_pairs.py' again.")
    else:
        print("\n✅ Data looks okay. The issue might be date matching.")