import sys
import os 

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import MarketDataEngine 

def get_pairs_data():
    print("---Fetching Pair Data (XOM , CVX) ---")
    tickers = ['XOM' , 'CVX']

    engine = MarketDataEngine()

    df = engine.download_data(tickers , start_date = '2020-01-01')

    if not df.empty:
        engine.save_to_sql(df)
        print("---Data Ready for Module 3 ---")
    else:
        print("Error downloading data.")

if __name__ == "__main__":
    get_pairs_data()
