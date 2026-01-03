# main_pairs.py
import queue
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

def run_pairs_trading():
    print("--- Starting Statistical Arbitrage Backtest ---")
    
    # 1. Configuration
    events = queue.Queue()
    db_path = os.path.join(current_dir, 'data', 'market_data.db')
    
    # PAIRS TRADING: We need exactly these two
    symbol_list = ['XOM', 'CVX']
    
    initial_capital = 100000.0
    start_date = '2020-01-01'

    # 2. Initialize Components
    data = HistoricSQLDataHandler(events, db_path, symbol_list)
    portfolio = Portfolio(data, events, start_date, initial_capital=initial_capital)
    
    # Initialize Strategy with the Hedge Ratio we found (1.055)
    strategy = PairsTradingStrategy(data, events, hedge_ratio=1.0552)
    
    broker = SimulatedExecutionHandler(events)
    
    # 3. The Main Event Loop
    print("Engine Running...")
    
    while True:
        # A. Update the Market
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
                # CALL THE NEW STRATEGY METHOD
                strategy.calculate_xy_signals(event)
                portfolio.update_timeindex()

            elif event.type == 'SIGNAL':
                portfolio.update_signal(event)

            elif event.type == 'ORDER':
                broker.execute_order(event)

            elif event.type == 'FILL':
                # Price Simulation Logic
                latest_bar = data.get_latest_bar(event.symbol)
                if latest_bar is not None:
                    event.fill_cost = latest_bar[1]['Close']
                    
                portfolio.update_fill(event)

    # 4. Results
    print("\n--- Backtest Complete ---")
    final_value = portfolio.current_holdings['Total']
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    
    ret = ((final_value - initial_capital) / initial_capital) * 100.0
    print(f"Return: {ret:.2f}%")

if __name__ == "__main__":
    run_pairs_trading()