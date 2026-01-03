# src/portfolio.py
import pandas as pd
from src.event import OrderEvent
import queue

class Portfolio:
    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        """
        bars: The DataHandler object (to get current prices)
        events: The Queue object (to send Orders)
        """
        self.bars = bars
        self.events = events
        self.start_date = start_date
        self.initial_capital = initial_capital
        
        # 1. Current Positions (Quantity of shares held)
        # e.g., {'AAPL': 100, 'MSFT': 0}
        self.current_positions = {symbol: 0 for symbol in self.bars.symbol_list}
        
        # 2. Current Holdings (Value in Dollars)
        # e.g., {'AAPL': 15000.0, 'Cash': 85000.0, 'Total': 100000.0}
        self.current_holdings = self.construct_current_holdings()
        
        # 3. History (To track performance over time)
        self.all_holdings = [] # List of dictionaries

    def construct_current_holdings(self):
        """
        Sets up the dictionary to track cash and assets.
        """
        h = {symbol: 0.0 for symbol in self.bars.symbol_list}
        h['Cash'] = self.initial_capital
        h['Total'] = self.initial_capital
        return h

    def update_timeindex(self):
        """
        Called at the end of every "Bar" (day).
        Updates the Market Value of our stocks using the latest prices.
        """
        bars = {}
        for sym in self.bars.symbol_list:
            # Get latest data from the DataHandler
            if sym in self.bars.latest_symbol_data and self.bars.latest_symbol_data[sym]:
                bars[sym] = self.bars.latest_symbol_data[sym][-1]
            else:
                bars[sym] = None

        # Update holdings
        dp = {symbol: 0.0 for symbol in self.bars.symbol_list}
        dp['Cash'] = self.current_holdings['Cash']
        dp['Total'] = self.current_holdings['Cash']

        for sym in self.bars.symbol_list:
            # If we have shares and a valid price, calculate value
            if self.current_positions[sym] != 0 and bars[sym] is not None:
                market_price = bars[sym]['Close']
                market_value = self.current_positions[sym] * market_price
                dp[sym] = market_value
                dp['Total'] += market_value
        
        # Record this moment in history
        self.current_holdings = dp
        # Add timestamp if available, else just append
        self.all_holdings.append(self.current_holdings.copy())

    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate an OrderEvent.
        """
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)

    def generate_naive_order(self, signal):
        """
        Simply buys/sells a fixed quantity (e.g., 100 shares) 
        regardless of cash. (We will make this smarter later).
        """
        order = None
        symbol = signal.symbol
        direction = signal.signal_type
        quantity = 100  # Fixed bet size for now
        
        if direction == 'LONG':
            order = OrderEvent(symbol, 'MKT', quantity, 'BUY')
        if direction == 'SHORT':
            order = OrderEvent(symbol, 'MKT', quantity, 'SELL')
            
        return order

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings 
        from a FillEvent.
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def update_positions_from_fill(self, fill):
        """
        Update the share count.
        """
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1
        
        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_fill(self, fill):
        """
        Update the cash balance.
        """
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1
            
        # Cost of the trade = (Price * Quantity) + Commission
        cost = fill_dir * fill.fill_cost * fill.quantity
        self.current_holdings['Cash'] -= (cost + fill.commission)