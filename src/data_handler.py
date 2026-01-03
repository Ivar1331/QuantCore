# src/data_handler.py
import pandas as pd
from sqlalchemy import create_engine, text
import os
from src.event import MarketEvent

class DataHandler:
    """
    DataHandler is an abstract base class providing an interface for
    all subsequent (inherited) data handlers (both live and historic).
    """
    def get_latest_bar(self, symbol):
        raise NotImplementedError("Should implement get_latest_bar()")

    def update_bars(self):
        raise NotImplementedError("Should implement update_bars()")

class HistoricSQLDataHandler(DataHandler):
    """
    HistoricSQLDataHandler is designed to read a SQL database for
    each requested symbol and provide an interface to obtain the
    "latest" bar in a manner identical to a live trading interface.
    """
    def __init__(self, events_queue, db_path, symbol_list):
        """
        events_queue: The Queue object where we push 'MARKET' events.
        db_path: Path to the SQLite database.
        symbol_list: List of ticker symbols (e.g., ['AAPL', 'MSFT'])
        """
        self.events_queue = events_queue
        self.db_path = db_path
        self.symbol_list = symbol_list
        
        self.symbol_data = {} # Stores all loaded data (Iterators)
        self.latest_symbol_data = {} # Stores the list of bars we have "seen" so far
        self.continue_backtest = True       
        
        # Connect to DB
        self.engine = create_engine(f'sqlite:///{db_path}')
        
        # Load the data immediately
        self._load_data()

    def _load_data(self):
        """
        Internal method to load data from SQL into Pandas Iterators.
        """
        print("Loading data from database...")
        combined_index = None
        
        for symbol in self.symbol_list:
            # Load data for this symbol
            query = text(f"SELECT * FROM prices WHERE Ticker = '{symbol}' ORDER BY Date ASC")
            self.symbol_data[symbol] = pd.read_sql(query, self.engine, index_col='Date', parse_dates=['Date'])
            
            # Combine index to align dates
            if combined_index is None:
                combined_index = self.symbol_data[symbol].index
            else:
                combined_index = combined_index.union(self.symbol_data[symbol].index)
            
            # Create a generator (iterator)
            self.symbol_data[symbol] = self.symbol_data[symbol].iterrows()
            
            # Initialize container for the latest bar
            self.latest_symbol_data[symbol] = []

    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed iterator.
        """
        try:
            return next(self.symbol_data[symbol])
        except StopIteration:
            self.continue_backtest = False
            return None

    def get_latest_bar(self, symbol):
        """
        Returns the last bar from the latest_symbol_data list.
        Returns: (Date, Series) or None
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
            if not bars_list:
                return None
            
            # The list stores just the 'row' (Series). 
            # We need to return (Date, Series) to satisfy the Strategy.
            latest_series = bars_list[-1]
            return (latest_series.name, latest_series)
            
        except KeyError:
            print(f"Symbol {symbol} not found in data.")
            return None

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list.
        """
        for symbol in self.symbol_list:
            try:
                bar = self._get_new_bar(symbol)
                if bar is not None:
                    # bar is a tuple (index, row_series)
                    timestamp, row = bar
                    # We store just the row Series in the list
                    self.latest_symbol_data[symbol].append(row)
            except StopIteration:
                self.continue_backtest = False
        
        # If backtest is still going, trigger a Market Event
        if self.continue_backtest:
            self.events_queue.put(MarketEvent())