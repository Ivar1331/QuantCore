# src/pairs_strategy.py
import numpy as np
import pandas as pd
from src.event import SignalEvent
from src.strategy import Strategy

class PairsTradingStrategy(Strategy):
    def __init__(self, bars, events, hedge_ratio=1.055):
        """
        bars: DataHandler
        events: Event Queue
        hedge_ratio: Calculated from research.py (Slope of OLS)
        """
        self.bars = bars
        self.events = events
        self.hedge_ratio = hedge_ratio
        self.tickers = bars.symbol_list # Expecting ['XOM', 'CVX']
        
        # Parameters
        self.window = 30         # Rolling window for Mean/Std Dev
        self.entry_z = 2.0       # Enter trade when Z-score > 2 or < -2
        self.exit_z = 0.5        # Exit when spread returns to normal
        
        # History for calculation
        self.spread_history = [] 
        
        # Track position state
        self.long_spread = False 
        self.short_spread = False

    def calculate_xy_signals(self, event):
        """
        Compute the Spread, Z-Score, and generate Signals.
        """
        if event.type == 'MARKET':
            # 1. Get latest prices for both assets
            x_ticker = self.tickers[0] # XOM
            y_ticker = self.tickers[1] # CVX
            
            x_bar = self.bars.get_latest_bar(x_ticker)
            y_bar = self.bars.get_latest_bar(y_ticker)
            
            if x_bar is None or y_bar is None:
                return # Not enough data yet

            # Extract Close Prices
            x_price = x_bar[1]['Close']
            y_price = y_bar[1]['Close']
            dt = x_bar[0] # Date
            
            # 2. Calculate Spread
            # Spread = Y - (Hedge_Ratio * X)
            spread = y_price - (self.hedge_ratio * x_price)
            self.spread_history.append(spread)
            
            # We need enough history to calculate Z-Score
            if len(self.spread_history) < self.window:
                return

            # 3. Calculate Z-Score
            # Take the last 'window' days
            rolling_spreads = self.spread_history[-self.window:]
            mean = np.mean(rolling_spreads)
            std = np.std(rolling_spreads)
            
            if std == 0:
                return
            
            z_score = (spread - mean) / std
            
            # print(f"Date: {dt} | Z-Score: {z_score:.2f}") # Debug
            
            # 4. Logic: Generate Signals
            
            # --- ENTRY LOGIC ---
            # If Z < -2 (Spread too low) -> BUY Spread (Buy Y, Sell X)
            if z_score < -self.entry_z and not self.long_spread:
                print(f"[{dt.date()}] ENTRY LONG Spread (Z: {z_score:.2f})")
                self.events.put(SignalEvent(y_ticker, dt, 'LONG'))  # Buy CVX
                self.events.put(SignalEvent(x_ticker, dt, 'SHORT')) # Sell XOM
                self.long_spread = True
                self.short_spread = False # Flip

            # If Z > +2 (Spread too high) -> SELL Spread (Sell Y, Buy X)
            elif z_score > self.entry_z and not self.short_spread:
                print(f"[{dt.date()}] ENTRY SHORT Spread (Z: {z_score:.2f})")
                self.events.put(SignalEvent(y_ticker, dt, 'SHORT')) # Sell CVX
                self.events.put(SignalEvent(x_ticker, dt, 'LONG'))  # Buy XOM
                self.short_spread = True
                self.long_spread = False

            # --- EXIT LOGIC ---
            # If Z returns to normal (between -0.5 and 0.5) -> CLOSE ALL
            elif abs(z_score) < self.exit_z:
                if self.long_spread or self.short_spread:
                    print(f"[{dt.date()}] EXIT (Z: {z_score:.2f} - Normal)")
                    # Simple Exit: Just flatten everything
                    # In a real engine, we'd check specific positions, 
                    # but here we just reverse the flag logic implicitly or send "EXIT" signals.
                    # For this Module, we will just send OPPOSITE signals to flatten.
                    
                    if self.long_spread:
                        # We were Long Y / Short X. So Sell Y / Buy X.
                        self.events.put(SignalEvent(y_ticker, dt, 'SHORT'))
                        self.events.put(SignalEvent(x_ticker, dt, 'LONG'))
                        self.long_spread = False
                        
                    if self.short_spread:
                        # We were Short Y / Long X. So Buy Y / Sell X.
                        self.events.put(SignalEvent(y_ticker, dt, 'LONG'))
                        self.events.put(SignalEvent(x_ticker, dt, 'SHORT'))
                        self.short_spread = False