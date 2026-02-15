"""
Avellaneda-Stoikov Market Making Strategy

Based on: "High-frequency Trading in a Limit Order Book" (2008)
by Marco Avellaneda and Sasha Stoikov

Key formulas:
1. Reservation price: r = s - q*γ*σ²*(T-t)
2. Optimal spread: δ = γ*σ²*(T-t)

Where:
- s = mid price
- q = inventory position  
- γ = risk aversion
- σ = volatility
- T-t = time remaining
"""

import numpy as np
from src.order_book import LimitOrderBook, Side


class AvellanedaStoikovMM:
    """
    Avellaneda-Stoikov market making strategy
    
    Adjusts quotes based on:
    - Current inventory (inventory risk)
    - Time to end of trading
    - Market volatility
    """
    
    def __init__(
        self,
        risk_aversion: float = 0.1,
        terminal_time: float = 1.0,
        volatility: float = 0.02,
        tick_size: float = 0.01,
        order_size: int = 10,
        max_inventory: int = 100
    ):
        """
        Args:
            risk_aversion: γ - higher = more conservative
            terminal_time: T - time horizon  
            volatility: σ - price volatility
            tick_size: Minimum price increment
            order_size: Size of each quote
            max_inventory: Maximum position
        """
        self.gamma = risk_aversion
        self.T = terminal_time
        self.sigma = volatility
        self.tick_size = tick_size
        self.order_size = order_size
        self.max_inventory = max_inventory
        
        # State
        self.inventory = 0
        self.cash = 0.0
        self.active_bid_id = None
        self.active_ask_id = None
        
        # Tracking
        self.pnl_history = []
        self.inventory_history = []
        self.spread_history = []
        
    def reservation_price(self, mid_price: float, time_remaining: float) -> float:
        """
        Calculate reservation price (indifference price)
        
        Formula: r = s - q*γ*σ²*(T-t)
        
        This is the price at which the market maker is indifferent
        between holding current inventory or not
        """
        return mid_price - self.inventory * self.gamma * (self.sigma ** 2) * time_remaining
    
    def optimal_spread(self, time_remaining: float) -> float:
        """
        Calculate optimal half-spread
        
        Formula: δ = γ*σ²*(T-t)
        
        Spread widens with:
        - Higher risk aversion
        - Higher volatility  
        - More time remaining
        """
        return self.gamma * (self.sigma ** 2) * time_remaining
    
    def calculate_quotes(self, mid_price: float, time_remaining: float) -> tuple:
        """
        Calculate optimal bid and ask prices
        
        Returns:
            (bid_price, ask_price)
        """
        # Get reservation price (adjusts for inventory)
        reservation = self.reservation_price(mid_price, time_remaining)
        
        # Get optimal half-spread
        half_spread = self.optimal_spread(time_remaining)
        
        # Minimum spread
        half_spread = max(half_spread, self.tick_size)
        
        # Calculate quotes around reservation price
        bid = reservation - half_spread
        ask = reservation + half_spread
        
        # Round to tick size
        bid = np.floor(bid / self.tick_size) * self.tick_size
        ask = np.ceil(ask / self.tick_size) * self.tick_size
        
        return bid, ask
    
    def update_quotes(self, lob: LimitOrderBook, time_remaining: float):
        """Update quotes in the order book"""
        mid = lob.get_mid_price()
        if mid is None:
            return
            
        # Cancel old orders
        if self.active_bid_id:
            lob.cancel_order(self.active_bid_id)
            self.active_bid_id = None
        if self.active_ask_id:
            lob.cancel_order(self.active_ask_id)
            self.active_ask_id = None
        
        # Don't quote if at max inventory
        if abs(self.inventory) >= self.max_inventory:
            return
            
        # Get new quotes
        bid, ask = self.calculate_quotes(mid, time_remaining)
        
        # Submit orders
        if self.inventory < self.max_inventory:
            self.active_bid_id = lob.submit_order(bid, self.order_size, Side.BID)
            
        if self.inventory > -self.max_inventory:
            self.active_ask_id = lob.submit_order(ask, self.order_size, Side.ASK)
        
        # Track spread
        self.spread_history.append(ask - bid)
    
    def check_fills(self, lob: LimitOrderBook) -> tuple:
        """
        Check if orders were filled
        
        Returns:
            (bid_filled, ask_filled) - boolean tuple
        """
        bid_filled = False
        ask_filled = False
        
        # Check bid
        if self.active_bid_id and self.active_bid_id not in lob.orders:
            # Order was filled
            self.inventory += self.order_size
            bid_filled = True
            self.active_bid_id = None
            
        # Check ask
        if self.active_ask_id and self.active_ask_id not in lob.orders:
            # Order was filled
            self.inventory -= self.order_size
            ask_filled = True
            self.active_ask_id = None
            
        return bid_filled, ask_filled
    
    def calculate_pnl(self, current_price: float) -> float:
        """
        Calculate P&L = cash + inventory * price
        """
        return self.cash + self.inventory * current_price
    
    def update_cash(self, price: float, size: int, bought: bool):
        """Update cash after trade"""
        if bought:
            self.cash -= price * size
        else:
            self.cash += price * size
