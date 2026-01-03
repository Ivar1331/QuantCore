# backtest.py
import queue
import time
import os
import sys

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# ----------------

from src.data_handler import HistoricSQLDataHandler
from src.strategy import BuyAndHoldStrategy
from src.portfolio import Portfolio
from src.execution import SimulatedExecutionHandler

def run_backtest():
    print("--- Starting Backtest Simulation ---")
    
    # 1. Configuration
    events = queue.Queue()
    db_path = os.path.join(current_dir, 'data', 'market_data.db')
    
    # We need to find valid tickers again (just like in our test)
    # Ideally, we would ask the DB, but let's hardcode 'ABBV' since we know it works
    # OR you can use the DB lookup trick if you prefer.
    symbol_list = ['ABBV'] 
    
    initial_capital = 100000.0
    start_date = '2020-01-01'
    heartbeat = 0.0 # No sleep time for backtest (run as fast as possible)

    # 2. Initialize Components
    # Data Feed
    data = HistoricSQLDataHandler(events, db_path, symbol_list)
    
    # Portfolio (The Wallet)
    portfolio = Portfolio(data, events, start_date, initial_capital=initial_capital)
    
    # Strategy (The Brain)
    strategy = BuyAndHoldStrategy(data, events)
    
    # Broker (The Execution)
    broker = SimulatedExecutionHandler(events)
    
    # 3. The Main Event Loop
    print("Engine Running...")
    
    while True:
        # A. Update the Market (Tick)
        if data.continue_backtest:
            data.update_bars()
        else:
            break # End of data
        
        # B. Handle Events
        while True:
            try:
                event = events.get(False) # Non-blocking get
            except queue.Empty:
                break
            
            if event.type == 'MARKET':
                strategy.calculate_signals(event)
                portfolio.update_timeindex()

            elif event.type == 'SIGNAL':
                portfolio.update_signal(event)

            elif event.type == 'ORDER':
                broker.execute_order(event)

            elif event.type == 'FILL':
                # Quick Fix: The Sim Broker didn't put a price on the fill.
                # We fetch the current price from DataHandler to "simulate" execution at current price.
                latest_bar = data.get_latest_bar(event.symbol)
                if latest_bar is not None:
                    # latest_bar is (timestamp, row)
                    fill_price = latest_bar[1]['Close']
                    event.fill_cost = fill_price
                    
                portfolio.update_fill(event)
                
                print(f"Trade Executed: {event.direction} {event.quantity} {event.symbol} @ ${event.fill_cost}")

    # 4. Results
    print("\n--- Backtest Complete ---")
    final_value = portfolio.current_holdings['Total']
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    
    # simple return calc
    ret = ((final_value - initial_capital) / initial_capital) * 100.0
    print(f"Return: {ret:.2f}%")

if __name__ == "__main__":
    run_backtest()