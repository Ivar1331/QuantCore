# src/event.py

class Event:
    """
    Base class for all events.
    """
    pass

class MarketEvent(Event):
    """
    Triggered when new market data (OHLCV) is available.
    """
    def __init__(self):
        self.type = 'MARKET'

class SignalEvent(Event):
    """
    Triggered by the Strategy. Tells the Portfolio to buy/sell.
    """
    def __init__(self, symbol, datetime, signal_type):
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type # 'LONG' or 'SHORT'

class OrderEvent(Event):
    """
    Triggered by the Portfolio. Requests execution from the Broker.
    """
    def __init__(self, symbol, order_type, quantity, direction):
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type # 'MKT' or 'LMT'
        self.quantity = quantity
        self.direction = direction # 'BUY' or 'SELL'
    
    def print_order(self):
        print(f"Order: {self.direction} {self.quantity} {self.symbol} @ {self.order_type}")

class FillEvent(Event):
    """
    Triggered by the Execution Handler. Represents a completed trade.
    """
    def __init__(self, timeindex, symbol, exchange, quantity, 
                 direction, fill_cost, commission=None):
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        
        # Simple commission model (e.g., Interactive Brokers min)
        if commission is None:
            self.commission = max(1.3, 0.01 * quantity)
        else:
            self.commission = commission