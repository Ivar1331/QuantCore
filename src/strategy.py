# src/strategy.py
from src.event import SignalEvent
import datetime

class Strategy:
    """
    Strategy is an abstract base class providing an interface for
    all subsequent (inherited) strategy handling objects.
    """
    def calculate_signals(self, event):
        raise NotImplementedError("Should implement calculate_signals()")

class BuyAndHoldStrategy(Strategy):
    """
    A simple test strategy that buys 100 shares of each ticker 
    on the very first day and holds them forever.
    """
    def __init__(self, bars, events):
        """
        bars: The DataHandler object
        events: The Event Queue
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        
        # Keep track if we have bought already
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        """
        For "Buy and Hold", we generate a single signal per symbol
        on the first market event.
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bar(s)
                
                # Check if we have data and haven't bought yet
                if bars is not None and not self.bought[s]:
                    # Create the Signal
                    signal = SignalEvent(s, bars[0], 'LONG')
                    self.events.put(signal)
                    self.bought[s] = True