# dashboard.py
import streamlit as st
import pandas as pd
import time
import os
import sys
import queue

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# ----------------

from src.data_handler import HistoricSQLDataHandler
from src.pairs_strategy import PairsTradingStrategy
from src.portfolio import Portfolio
from src.execution import SimulatedExecutionHandler

# Page Config
st.set_page_config(page_title="QuantCore Live", layout="wide")
st.title("⚡ QuantCore: Live Strategy Dashboard")

# Layout: 3 Columns for Metrics
col1, col2, col3 = st.columns(3)
metric_date = col1.empty()
metric_cash = col2.empty()
metric_value = col3.empty()

# Layout: 2 Charts
st.subheader("💰 Portfolio Equity Curve")
equity_chart = st.line_chart(pd.DataFrame(columns=['Total']))

st.subheader("📊 Spread Z-Score (The Signal)")
z_chart = st.line_chart(pd.DataFrame(columns=['Z-Score']))

def run_dashboard():
    # 1. Setup Engine
    events = queue.Queue()
    db_path = os.path.join(current_dir, 'data', 'market_data.db')
    symbol_list = ['XOM', 'CVX']
    
    data = HistoricSQLDataHandler(events, db_path, symbol_list)
    # Start with $100k
    portfolio = Portfolio(data, events, '2020-01-01', initial_capital=100000.0)
    strategy = PairsTradingStrategy(data, events, hedge_ratio=1.0552)
    broker = SimulatedExecutionHandler(events)
    
    # 2. Simulation Loop
    # We will simulate "Speed" by sleeping slightly
    simulation_speed = st.sidebar.slider("Simulation Speed (ms)", 1, 100, 10) / 1000.0
    
    # Buffers to hold data for the chart
    equity_history = []
    z_history = []
    
    step = 0
    
    while True:
        # A. Update Market
        if data.continue_backtest:
            data.update_bars()
        else:
            break
        
        # B. Handle Events
        while True:
            try:
                event = events.get(False)
            except queue.Empty:
                break
            
            if event.type == 'MARKET':
                strategy.calculate_xy_signals(event)
                portfolio.update_timeindex()
                
                # --- LIVE UPDATE LOGIC ---
                # We update the UI every few steps to prevent lag
                step += 1
                if step % 5 == 0: 
                    # 1. Update Metrics
                    latest_holdings = portfolio.current_holdings
                    # We need a date. In this simple portfolio, we don't store it easily accessible
                    # So we grab it from the strategy's last processed bar
                    if strategy.spread_history:
                         # Just a hack to show activity
                        metric_cash.metric("Cash", f"${latest_holdings['Cash']:,.2f}")
                        metric_value.metric("Net Worth", f"${latest_holdings['Total']:,.2f}")
                    
                    # 2. Update Charts
                    # Append new data to charts
                    if portfolio.all_holdings:
                         new_equity = portfolio.all_holdings[-1]['Total']
                         equity_chart.add_rows([new_equity])
                    
                    if strategy.spread_history:
                        new_z = (strategy.spread_history[-1] - 0) # Raw spread for now, or Z if calculated
                        # Actually, let's plot the Z-score properly if the strategy calculated it.
                        # Since strategy logic is internal, we'll just plot the raw spread for "visual movement"
                        # OR we can modify strategy to expose Z-score.
                        # For now, let's plot the raw spread stored in strategy.
                        z_chart.add_rows([strategy.spread_history[-1]])
                    
                    time.sleep(simulation_speed)

            elif event.type == 'SIGNAL':
                portfolio.update_signal(event)
                st.toast(f"SIGNAL: {event.signal_type} {event.symbol}")

            elif event.type == 'ORDER':
                broker.execute_order(event)

            elif event.type == 'FILL':
                latest_bar = data.get_latest_bar(event.symbol)
                if latest_bar:
                    event.fill_cost = latest_bar[1]['Close']
                portfolio.update_fill(event)

    st.success("Simulation Complete")

if st.button("Start Simulation"):
    run_dashboard()