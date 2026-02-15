"""
Simple Backtesting Framework
"""

import numpy as np
from dataclasses import dataclass
from src.order_book import LimitOrderBook, Side
from src.avellaneda_stoikov import AvellanedaStoikovMM


@dataclass
class BacktestResults:
    """Results from backtest"""
    final_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    num_trades: int
    avg_spread: float
    final_inventory: int
    pnl_history: list
    inventory_history: list
    timestamps: list


def generate_price_path(n_steps: int, initial_price: float = 100.0, 
                       volatility: float = 0.02, dt: float = 0.1) -> np.ndarray:
    """
    Generate realistic price path using Geometric Brownian Motion
    
    Args:
        n_steps: Number of time steps
        initial_price: Starting price
        volatility: Annual volatility
        dt: Time step in seconds
        
    Returns:
        Array of prices
    """
    prices = np.zeros(n_steps)
    prices[0] = initial_price
    
    for i in range(1, n_steps):
        # GBM with some noise
        dW = np.random.normal(0, np.sqrt(dt))
        drift = 0  # No drift for simplicity
        diffusion = volatility * prices[i-1] * dW
        
        # Add microstructure noise
        noise = np.random.choice([-1, 0, 1]) * 0.01 * 0.5
        
        prices[i] = prices[i-1] + drift + diffusion + noise
        
    return prices


def initialize_book(lob: LimitOrderBook, price: float):
    """Seed the order book with initial liquidity"""
    for i in range(1, 11):
        bid = price - i * 0.01
        ask = price + i * 0.01
        size = np.random.randint(10, 30)
        
        lob.submit_order(bid, size, Side.BID)
        lob.submit_order(ask, size, Side.ASK)


def simulate_order_flow(lob: LimitOrderBook, intensity: float = 5.0, dt: float = 0.1):
    """Simulate random market orders"""
    # Poisson arrivals
    n_buys = np.random.poisson(intensity * dt)
    n_sells = np.random.poisson(intensity * dt)
    
    for _ in range(n_buys):
        size = np.random.randint(1, 10)
        lob.execute_market_order(size, Side.BID)
        
    for _ in range(n_sells):
        size = np.random.randint(1, 10)
        lob.execute_market_order(size, Side.ASK)


def run_backtest(
    duration: int = 3600,
    dt: float = 0.1,
    risk_aversion: float = 0.1,
    volatility: float = 0.02,
    quote_freq: int = 10
) -> BacktestResults:
    """
    Run Avellaneda-Stoikov backtest
    
    Args:
        duration: Simulation duration in seconds
        dt: Time step
        risk_aversion: Strategy risk aversion
        volatility: Market volatility
        quote_freq: How often to update quotes (in steps)
        
    Returns:
        BacktestResults
    """
    print(f"Running backtest: {duration}s duration, γ={risk_aversion}, σ={volatility}")
    
    # Generate market data
    n_steps = int(duration / dt)
    prices = generate_price_path(n_steps, volatility=volatility, dt=dt)
    
    # Initialize
    lob = LimitOrderBook(tick_size=0.01)
    initialize_book(lob, prices[0])
    
    strategy = AvellanedaStoikovMM(
        risk_aversion=risk_aversion,
        terminal_time=1.0,
        volatility=volatility
    )
    
    # Tracking
    pnl_history = []
    inventory_history = []
    timestamps = []
    num_trades = 0
    
    # Run simulation
    for step in range(n_steps):
        lob.current_time = step * dt
        time_remaining = max(0, 1.0 - (step / n_steps))
        
        # Update quotes periodically
        if step % quote_freq == 0:
            strategy.update_quotes(lob, time_remaining)
        
        # Check for fills
        bid_filled, ask_filled = strategy.check_fills(lob)
        
        if bid_filled:
            num_trades += 1
            best_bid = lob.get_best_bid()
            if best_bid:
                strategy.update_cash(best_bid, strategy.order_size, bought=True)
                
        if ask_filled:
            num_trades += 1
            best_ask = lob.get_best_ask()
            if best_ask:
                strategy.update_cash(best_ask, strategy.order_size, bought=False)
        
        # Simulate market activity
        simulate_order_flow(lob, intensity=5.0, dt=dt)
        
        # Record state
        pnl = strategy.calculate_pnl(prices[step])
        pnl_history.append(pnl)
        inventory_history.append(strategy.inventory)
        timestamps.append(step * dt)
        
        # Progress
        if step % 1000 == 0:
            print(f"  Step {step}/{n_steps}, PnL: ${pnl:.2f}, Inventory: {strategy.inventory}")
    
    # Calculate metrics
    pnl_array = np.array(pnl_history)
    pnl_returns = np.diff(pnl_array)
    
    sharpe = np.mean(pnl_returns) / (np.std(pnl_returns) + 1e-8) * np.sqrt(252 * 6.5 * 3600 / dt)
    
    cummax = np.maximum.accumulate(pnl_array)
    drawdown = pnl_array - cummax
    max_dd = np.min(drawdown)
    
    avg_spread = np.mean(strategy.spread_history) if strategy.spread_history else 0
    
    return BacktestResults(
        final_pnl=pnl_history[-1],
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        num_trades=num_trades,
        avg_spread=avg_spread,
        final_inventory=strategy.inventory,
        pnl_history=pnl_history,
        inventory_history=inventory_history,
        timestamps=timestamps
    )


def print_results(results: BacktestResults):
    """Print backtest results"""
    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    print(f"Final P&L:        ${results.final_pnl:>10.2f}")
    print(f"Sharpe Ratio:     {results.sharpe_ratio:>14.2f}")
    print(f"Max Drawdown:     ${results.max_drawdown:>10.2f}")
    print(f"Num Trades:       {results.num_trades:>14}")
    print(f"Avg Spread:       {results.avg_spread*10000:>10.2f} bps")
    print(f"Final Inventory:  {results.final_inventory:>14}")
    print("="*60)
