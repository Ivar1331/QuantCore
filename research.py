# research.py
import pandas as pd
from sqlalchemy import create_engine, text
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import os

def check_cointegration():
    print("--- Research Phase: Testing Cointegration ---")
    
    # 1. Load Data
    db_path = os.path.join(os.getcwd(), 'data', 'market_data.db')
    engine = create_engine(f'sqlite:///{db_path}')
    
    try:
        # Fetch data
        print("Fetching XOM and CVX data...")
        df_xom = pd.read_sql(text("SELECT Date, Close FROM prices WHERE Ticker='XOM'"), engine, index_col='Date', parse_dates=['Date'])
        df_cvx = pd.read_sql(text("SELECT Date, Close FROM prices WHERE Ticker='CVX'"), engine, index_col='Date', parse_dates=['Date'])
    except Exception as e:
        print(f"Database Error: {e}")
        return

    # 2. Clean and Merge
    # Rename columns to avoid confusion
    df_xom.columns = ['Close_XOM']
    df_cvx.columns = ['Close_CVX']

    # Merge into one DataFrame based on Date
    df = pd.merge(df_xom, df_cvx, left_index=True, right_index=True)
    
    # --- CRITICAL FIX: Force data to be numeric ---
    # Coerce errors will turn non-numbers into NaN (which we can then drop)
    df['Close_XOM'] = pd.to_numeric(df['Close_XOM'], errors='coerce')
    df['Close_CVX'] = pd.to_numeric(df['Close_CVX'], errors='coerce')
    
    # Drop any rows that have missing data (NaN)
    df.dropna(inplace=True)
    
    print(f"Loaded {len(df)} common days of clean data.")

    if len(df) < 100:
        print("Error: Not enough data points to run statistical tests.")
        return

    # 3. Calculate Hedge Ratio
    print("Running OLS Regression...")
    x = df['Close_XOM']
    y = df['Close_CVX']
    x_const = sm.add_constant(x) # Add intercept for the regression
    
    model = sm.OLS(y, x_const).fit()
    hedge_ratio = model.params['Close_XOM']
    print(f"Hedge Ratio: {hedge_ratio:.4f}")
    
    # 4. Construct the Spread
    # spread = Y - (hedge_ratio * X)
    df['Spread'] = df['Close_CVX'] - (hedge_ratio * df['Close_XOM'])
    
    # 5. Run ADF Test
    print("Running Augmented Dickey-Fuller Test...")
    adf_result = adfuller(df['Spread'])
    
    print("\n--- ADF Test Results ---")
    print(f"ADF Statistic: {adf_result[0]:.4f}")
    p_value = adf_result[1]
    print(f"P-Value: {p_value:.4f}")
    
    if p_value < 0.05:
        print("✅ RESULT: The pair is Cointegrated! (P-Value < 0.05)")
        print("   Strategy: Trade this pair.")
    else:
        print("❌ RESULT: The pair is NOT Cointegrated. (P-Value >= 0.05)")
        print("   Strategy: Do not trade.")

if __name__ == "__main__":
    check_cointegration()