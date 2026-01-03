# visualize.py
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# ----------------

from src.data_handler import HistoricSQLDataHandler
from src.pairs_strategy import PairsTradingStrategy
from src.portfolio import Portfolio
from src.execution import SimulatedExecutionHandler
import queue

def run_and_plot():
    print("--- Re-Running Simulation for Visualization ---")
    
    # 1. Setup Engine
    events = queue.Queue()
    db_path = os.path.join(current_dir, 'data', 'market_data.db')
    symbol_list = ['XOM', 'CVX']
    
    data = HistoricSQLDataHandler(events, db_path, symbol_list)
    portfolio = Portfolio(data, events, '2020-01-01', initial_capital=100000.0)
    strategy = PairsTradingStrategy(data, events, hedge_ratio=1.0552)
    broker = SimulatedExecutionHandler(events)
    
    # 2. Run Loop
    print("Processing Data...")
    while True:
        if data.continue_backtest:
            data.update_bars()
        else:
            break
        
        while True:
            try:
                event = events.get(False)
            except queue.Empty:
                break
            
            if event.type == 'MARKET':
                strategy.calculate_xy_signals(event)
                portfolio.update_timeindex()
            elif event.type == 'SIGNAL':
                portfolio.update_signal(event)
            elif event.type == 'ORDER':
                broker.execute_order(event)
            elif event.type == 'FILL':
                latest_bar = data.get_latest_bar(event.symbol)
                if latest_bar:
                    event.fill_cost = latest_bar[1]['Close']
                portfolio.update_fill(event)

    # 3. Extract Data for Plotting
    print("Generating Charts...")
    
    # Convert portfolio history to DataFrame
    curve = pd.DataFrame(portfolio.all_holdings)
    # The 'all_holdings' list doesn't have dates by default in our simple Portfolio class
    # We need to rely on the index being sequential days.
    
    # Create the Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Portfolio Value
    ax1.plot(curve['Total'], label='Portfolio Value', color='green')
    ax1.set_title('Strategy Equity Curve')
    ax1.set_ylabel('Capital ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Z-Score Signals
    # We'll extract Z-scores from the strategy history
    z_scores = strategy.spread_history
    # We need to align lengths (strategy starts calculating after 'window' days)
    # This is a rough visualization, so simple slicing is fine for now
    ax2.plot(z_scores, label='Spread Z-Score', color='blue', alpha=0.6)
    ax2.axhline(2.0, color='red', linestyle='--', label='Short Threshold (+2)')
    ax2.axhline(-2.0, color='green', linestyle='--', label='Long Threshold (-2)')
    ax2.set_title('Z-Score & Trade Signals')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    print("Displaying Plot...")
    plt.show()

if __name__ == "__main__":
    run_and_plot()