# src/data_loader.py
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
import os

class MarketDataEngine:
    def __init__(self, db_name='market_data.db'):
        """
        Initialize the engine with a database connection.
        """
        # 1. Get the path of the current script (data_loader.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Go up one level to the project root (QuantCore)
        project_root = os.path.dirname(current_dir)
        
        # 3. Construct the full path to the data folder
        data_dir = os.path.join(project_root, 'data')
        
        # 4. Create the data directory if it doesn't exist (safety check)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # 5. Build the full database path
        db_path = os.path.join(data_dir, db_name)
        
        # 6. Create the Connection String
        # SQLite needs 3 slashes /// for relative, 4 //// for absolute paths on Unix/Mac
        # We are using an absolute path here.
        self.db_url = f'sqlite:///{db_path}'
        
        print(f"--- [DEBUG] Database URL: {self.db_url} ---")
        self.engine = create_engine(self.db_url)

    def download_data(self, tickers, start_date='2020-01-01', end_date=None):
        """
        Downloads data for a list of tickers.
        """
        print(f"Downloading data for {len(tickers)} tickers...")
        
        # yfinance bulk download
        data = yf.download(
            tickers, 
            start=start_date, 
            end=end_date, 
            group_by='ticker', 
            auto_adjust=True,
            actions=False, 
            threads=True 
        )
        
        return data

    def save_to_sql(self, data):
        """
        Transforms the complex yfinance DataFrame and saves to SQL.
        """
        if data.empty:
            print("No data to save.")
            return

        print("Transforming data format...")
        
        # 1. Stack the data to get Tickers into rows
        # We use future_stack=True to fix the warning you saw earlier
        data_stacked = data.stack(level=0, future_stack=True).reset_index()
        
        # 2. Fix Column Names
        # reset_index() might create a column named 'level_1' for the Ticker
        if 'level_1' in data_stacked.columns:
            data_stacked = data_stacked.rename(columns={'level_1': 'Ticker'})
            
        # 3. Filter: Keep ONLY the columns we need
        # This fixes the "8 columns vs 7 columns" crash. 
        # We explicitly grab only these 7, ignoring any extra 'Adj Close' or 'Dividends' columns.
        target_cols = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
        
        # Safety check: Ensure all target columns actually exist before selecting
        available_cols = [c for c in target_cols if c in data_stacked.columns]
        data_stacked = data_stacked[available_cols]
        
        print(f"Saving {len(data_stacked)} rows to database...")
        data_stacked.to_sql('prices', self.engine, if_exists='replace', index=False)
        print("Data saved successfully!")
    

if __name__ == "__main__":
    test_tickers = ['AAPL', 'MSFT']
    engine = MarketDataEngine()
    df = engine.download_data(test_tickers)
    engine.save_to_sql(df)