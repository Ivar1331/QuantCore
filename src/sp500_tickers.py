# src/sp500_tickers.py
import pandas as pd
import requests
from io import StringIO

def get_sp500_tickers():
    """
    Scrapes the Wikipedia page for the S&P 500 list using a fake User-Agent
    to avoid 403 Forbidden errors.
    """
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    # This is the "Fake ID" we present to Wikipedia
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }

    try:
        # 1. Fetch the raw HTML content using requests with headers
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Check for errors (like 403 or 404)
        
        # 2. Use Pandas to read the HTML table from the text
        # StringIO wraps the string so pandas treats it like a file
        tables = pd.read_html(StringIO(response.text))
        
        # The first table usually contains the constituents
        sp500_table = tables[0]
        
        # Extract the 'Symbol' column and convert to a list
        tickers = sp500_table['Symbol'].tolist()
        
        # Clean tickers: Yahoo Finance uses '-' instead of '.' (e.g., BRK.B -> BRK-B)
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        
        print(f"Successfully retrieved {len(tickers)} tickers.")
        return tickers
        
    except Exception as e:
        print(f"Error fetching tickers: {e}")
        return []

if __name__ == "__main__":
    # Test the function if run directly
    tickers = get_sp500_tickers()
    print(tickers[:5]) # Print first 5