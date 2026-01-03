# main.py
print("--- [DEBUG] 1. Script has started running ---")

import sys
import os

# Fix path to find local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
print(f"--- [DEBUG] 2. Path set to: {current_dir} ---")

try:
    print("--- [DEBUG] 3. Attempting to import modules ---")
    from src.sp500_tickers import get_sp500_tickers
    from src.data_loader import MarketDataEngine
    print("--- [DEBUG] 4. Imports successful ---")
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    sys.exit(1)

def run_pipeline():
    print("--- [DEBUG] 5. Inside run_pipeline function ---")
    
    # 1. Get the universe
    print("Attempting to fetch tickers...")
    tickers = get_sp500_tickers()
    
    if not tickers:
        print("CRITICAL ERROR: No tickers found. Exiting.")
        return

    print(f"Successfully found {len(tickers)} tickers.")
    
    # Test with just 5 tickers first
    subset_tickers = tickers[:5] 
    print(f"Downloading data for: {subset_tickers}")
    
    # 2. Initialize Engine
    data_engine = MarketDataEngine()
    
    # 3. Download Data
    raw_data = data_engine.download_data(subset_tickers)
    
    # 4. Store Data
    if not raw_data.empty:
        data_engine.save_to_sql(raw_data)
        print("--- [DEBUG] 6. Pipeline Complete! ---")
    else:
        print("No data fetched.")

if __name__ == "__main__":
    run_pipeline()