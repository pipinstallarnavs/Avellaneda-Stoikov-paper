"""
Limit Order Book Implementation
Simple price-time priority matching engine
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Tuple


class Side(Enum):
    """Order side"""
    BID = 1
    ASK = -1


@dataclass
class Order:
    """Limit order"""
    order_id: int
    price: float
    size: int
    side: Side
    timestamp: float


@dataclass
class Trade:
    """Executed trade"""
    price: float
    size: int
    timestamp: float
    

class LimitOrderBook:
    """
    Limit Order Book with price-time priority
    
    Features:
    - Price-time priority (FIFO at each price level)
    - Queue position tracking
    - Bid/ask spread calculation
    - Order book depth
    """
    
    def __init__(self, tick_size: float = 0.01):
        self.tick_size = tick_size
        
        # Order queues at each price level
        self.bids = defaultdict(deque)  # price -> queue of orders
        self.asks = defaultdict(deque)
        
        # Track all orders
        self.orders = {}  # order_id -> order
        
        # Trade history
        self.trades = []
        
        # State
        self.next_order_id = 1
        self.current_time = 0.0
        
    def submit_order(self, price: float, size: int, side: Side) -> int:
        """
        Submit a new limit order
        
        Args:
            price: Limit price
            size: Order size
            side: BID or ASK
            
        Returns:
            order_id
        """
        # Round to tick size
        price = round(price / self.tick_size) * self.tick_size
        
        order = Order(
            order_id=self.next_order_id,
            price=price,
            size=size,
            side=side,
            timestamp=self.current_time
        )
        
        self.next_order_id += 1
        self.orders[order.order_id] = order
        
        # Add to book
        if side == Side.BID:
            self.bids[price].append(order)
        else:
            self.asks[price].append(order)
            
        return order.order_id
    
    def cancel_order(self, order_id: int) -> bool:
        """Cancel an order"""
        if order_id not in self.orders:
            return False
            
        order = self.orders[order_id]
        book = self.bids if order.side == Side.BID else self.asks
        
        try:
            book[order.price].remove(order)
            if len(book[order.price]) == 0:
                del book[order.price]
            del self.orders[order_id]
            return True
        except (ValueError, KeyError):
            return False
    
    def execute_market_order(self, size: int, side: Side) -> List[Trade]:
        """
        Execute a market order against the book
        
        Args:
            size: Order size
            side: BID (buy) or ASK (sell)
            
        Returns:
            List of trades executed
        """
        trades = []
        remaining = size
        
        # Market buy hits asks, market sell hits bids
        book = self.asks if side == Side.BID else self.bids
        prices = sorted(book.keys()) if side == Side.BID else sorted(book.keys(), reverse=True)
        
        for price in prices:
            if remaining == 0:
                break
                
            queue = book[price]
            
            while queue and remaining > 0:
                order = queue[0]
                fill_size = min(remaining, order.size)
                
                # Create trade
                trade = Trade(
                    price=price,
                    size=fill_size,
                    timestamp=self.current_time
                )
                trades.append(trade)
                self.trades.append(trade)
                
                # Update order
                order.size -= fill_size
                remaining -= fill_size
                
                # Remove if fully filled
                if order.size == 0:
                    queue.popleft()
                    del self.orders[order.order_id]
            
            # Clean up empty price level
            if len(queue) == 0:
                del book[price]
        
        return trades
    
    def get_best_bid(self) -> Optional[float]:
        """Get best bid price"""
        return max(self.bids.keys()) if self.bids else None
    
    def get_best_ask(self) -> Optional[float]:
        """Get best ask price"""
        return min(self.asks.keys()) if self.asks else None
    
    def get_mid_price(self) -> Optional[float]:
        """Get mid price"""
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        if bid is None or ask is None:
            return None
        return (bid + ask) / 2
    
    def get_spread(self) -> Optional[float]:
        """Get bid-ask spread"""
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        if bid is None or ask is None:
            return None
        return ask - bid
    
    def get_depth(self, side: Side, levels: int = 5) -> List[Tuple[float, int]]:
        """
        Get order book depth
        
        Returns:
            List of (price, total_size) tuples
        """
        book = self.bids if side == Side.BID else self.asks
        prices = sorted(book.keys(), reverse=(side == Side.BID))[:levels]
        
        depth = []
        for price in prices:
            total_size = sum(order.size for order in book[price])
            depth.append((price, total_size))
        return depth
    
    def get_queue_position(self, order_id: int) -> Optional[int]:
        """Get position in queue (0 = front)"""
        if order_id not in self.orders:
            return None
            
        order = self.orders[order_id]
        book = self.bids if order.side == Side.BID else self.asks
        queue = book.get(order.price, deque())
        
        try:
            return list(queue).index(order)
        except ValueError:
            return None
    
    def __repr__(self):
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        spread = self.get_spread()
        return f"LOB(bid={bid}, ask={ask}, spread={spread})"
