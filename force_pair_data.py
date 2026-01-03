# force_pair_data.py
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
import os

def force_download():
    # 1. Setup Database Connection
    db_path = os.path.join(os.getcwd(), 'data', 'market_data.db')
    engine = create_engine(f'sqlite:///{db_path}')
    
    tickers = ['XOM', 'CVX']
    print("--- Force Downloading Data (Robust Mode) ---")

    for ticker in tickers:
        print(f"\nProcessing {ticker}...")
        
        # Download single ticker
        # We use auto_adjust=True so we get 'Close' (which is actually Adj Close)
        df = yf.download(ticker, start='2020-01-01', auto_adjust=True, progress=False)
        
        if df.empty:
            print(f"CRITICAL ERROR: No data found for {ticker}")
            continue

        # --- FIX: FLATTEN COLUMNS ---
        # If columns are MultiIndex (e.g., ('Close', 'XOM')), flatten them to just 'Close'
        if isinstance(df.columns, pd.MultiIndex):
            print("  - Detected MultiIndex columns. Flattening...")
            df.columns = df.columns.get_level_values(0)

        # Move Date from Index to Column
        df = df.reset_index()
        
        # Debug: Print columns to be sure
        # print(f"  - Columns found: {df.columns.tolist()}")

        df['Ticker'] = ticker
        
        # Ensure 'Close' exists. 
        if 'Close' not in df.columns:
            print(f"  - Warning: 'Close' column missing. Trying to rename 'Adj Close'...")
            if 'Adj Close' in df.columns:
                df.rename(columns={'Adj Close': 'Close'}, inplace=True)
            else:
                print(f"  - CRITICAL: Could not find Price column. Available: {df.columns}")
                continue
            
        # Select strictly the columns we need
        # We iterate and check existence to avoid KeyErrors
        target_cols = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
        available_cols = [c for c in target_cols if c in df.columns]
        df = df[available_cols]
        
        # Remove any empty rows
        original_len = len(df)
        df = df.dropna(subset=['Close'])
        
        # 2. Delete old broken data for this ticker
        print(f"  - Deleting old data for {ticker}...")
        with engine.connect() as conn:
            conn.execute(text(f"DELETE FROM prices WHERE Ticker = '{ticker}'"))
            conn.commit()

        # 3. Save new clean data
        print(f"  - Saving {len(df)} valid rows (dropped {original_len - len(df)} Empty/NaN)...")
        df.to_sql('prices', engine, if_exists='append', index=False)
        print("  - Success.")

    print("\n--- Data Repair Complete ---")

if __name__ == "__main__":
    force_download()