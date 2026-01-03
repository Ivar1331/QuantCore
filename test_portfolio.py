# test_portfolio.py
import queue
import pandas as pd
from src.event import SignalEvent, FillEvent
from src.portfolio import Portfolio

# Mock DataHandler (Fake Class just for testing)
class MockHandler:
    def __init__(self):
        self.symbol_list = ['ABBV']
        self.latest_symbol_data = {'ABBV': [{'Close': 70.00}]}

def test_portfolio():
    print("--- Testing Portfolio Logic ---")
    
    # 1. Setup
    events = queue.Queue()
    bars = MockHandler()
    # Start with $100,000
    port = Portfolio(bars, events, start_date='2020-01-01', initial_capital=100000.0)
    
    print(f"Initial Cash: ${port.current_holdings['Cash']}")
    
    # 2. Simulate a "Buy" Signal
    print("\n[Step 1] Strategy sends Signal: BUY ABBV")
    sig = SignalEvent('ABBV', '2020-01-01', 'LONG')
    port.update_signal(sig)
    
    # Check if Order was created
    if not events.empty():
        order = events.get()
        print(f"Portfolio generated Order: {order.direction} {order.quantity} {order.symbol}")
    else:
        print("ERROR: No order generated!")

    # 3. Simulate a "Fill" (The Broker executed the trade)
    print("\n[Step 2] Broker Fills Order at $70.00")
    # Buy 100 shares @ $70. Commission = $5
    fill = FillEvent(
        timeindex='2020-01-01', 
        symbol='ABBV', 
        exchange='ARCA', 
        quantity=100, 
        direction='BUY', 
        fill_cost=70.00, 
        commission=5.00
    )
    port.update_fill(fill)
    
    # 4. Check Final Balances
    print("\n--- Final Balances ---")
    print(f"Shares Held (ABBV): {port.current_positions['ABBV']}")
    print(f"Cash Remaining: ${port.current_holdings['Cash']}")
    
    # Math Check: 100,000 - (100 * 70) - 5 = 92,995
    expected_cash = 92995.0
    if port.current_holdings['Cash'] == expected_cash:
        print("SUCCESS: Cash calculation is perfect.")
    else:
        print(f"FAIL: Expected {expected_cash}, got {port.current_holdings['Cash']}")

if __name__ == "__main__":
    test_portfolio()