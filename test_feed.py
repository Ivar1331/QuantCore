# test_feed.py
import sys
import os
from sqlalchemy import create_engine, text
import pandas as pd
import queue

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# ----------------

from src.data_handler import HistoricSQLDataHandler

def run_test():
    db_path = os.path.join(current_dir, 'data', 'market_data.db')
    
    # 1. DIAGNOSTIC: Check what is actually in the DB
    print(f"--- Diagnosing Database: {db_path} ---")
    if not os.path.exists(db_path):
        print("CRITICAL ERROR: Database file not found!")
        return

    engine = create_engine(f'sqlite:///{db_path}')
    
    try:
        with engine.connect() as conn:
            # Check total rows
            count = conn.execute(text("SELECT COUNT(*) FROM prices")).fetchone()[0]
            print(f"Total Rows in DB: {count}")
            
            if count == 0:
                print("CRITICAL ERROR: Database is empty! Run 'main.py' again.")
                return

            # Find a valid ticker that actually has data
            result = conn.execute(text("SELECT DISTINCT Ticker FROM prices LIMIT 1"))
            valid_ticker = result.fetchone()[0]
            print(f"Found valid ticker to test: {valid_ticker}")
            
            # Use THIS ticker for the test
            tickers = [valid_ticker]
            
    except Exception as e:
        print(f"Database Error: {e}")
        return

    # 2. Run the Simulation
    print(f"\n--- Simulating Feed for {tickers[0]} ---")
    events = queue.Queue()
    
    # Initialize Handler with the VALID ticker
    data = HistoricSQLDataHandler(events, db_path, tickers)
    
    # Loop for 5 ticks
    for i in range(5):
        data.update_bars()
        
        if not events.empty():
            event = events.get()
            print(f"Tick {i+1}: Event Received -> {event.type}")
            
            # Print the price
            latest = data.latest_symbol_data[tickers[0]][-1]
            print(f"   Date: {latest.name.date()} | Close: {latest['Close']:.2f}")
        else:
            print(f"Tick {i+1}: No event generated (End of data?)")

if __name__ == "__main__":
    run_test()