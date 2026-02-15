# Market Making Simulator

Implementation of the Avellaneda-Stoikov optimal market making model with a realistic limit order book.

## Overview

This project implements the market making strategy from the paper ["High-frequency Trading in a Limit Order Book"](https://www.math.nyu.edu/faculty/avellane/HighFrequencyTrading.pdf) by Avellaneda & Stoikov (2008).

**Key Features:**
- Limit order book with price-time priority
- Avellaneda-Stoikov optimal quoting strategy
- Inventory risk management
- Backtesting framework with performance metrics

## The Model

The Avellaneda-Stoikov model derives optimal bid/ask quotes using stochastic control theory.

### Key Formulas

**1. Reservation Price:**
```
r(t) = s(t) - q*γ*σ²*(T-t)
```

**2. Optimal Spread:**
```
δ(t) = γ*σ²*(T-t)
```

Where:
- `s(t)` = mid price at time t
- `q` = current inventory position
- `γ` = risk aversion parameter
- `σ` = price volatility
- `T-t` = time remaining until liquidation

### How It Works

The strategy adjusts quotes based on inventory:
- **Long position** (q > 0): Reservation price shifts down → tighter ask, wider bid → encourages selling
- **Short position** (q < 0): Reservation price shifts up → tighter bid, wider ask → encourages buying
- **Neutral position** (q = 0): Quotes symmetric around mid price

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/market-making-simulator.git
cd market-making-simulator
pip install numpy matplotlib
```

### Run Backtest

```bash
# Default: 30 minutes, γ=0.1, σ=0.02
python run.py

# Custom parameters
python run.py --duration 3600 --risk-aversion 0.5 --volatility 0.03

# See all options
python run.py --help
```

### Example Output

```
BACKTEST RESULTS
============================================================
Final P&L:        $     15.23
Sharpe Ratio:            2.08
Max Drawdown:     $     -3.45
Num Trades:                42
Avg Spread:            15.20 bps
Final Inventory:            2
============================================================
```

## Project Structure

```
market-making-simulator/
├── src/
│   ├── order_book.py          # Limit order book implementation
│   ├── avellaneda_stoikov.py  # Market making strategy
│   └── backtest.py            # Backtesting engine
├── run.py                     # Main script
├── results/                   # Output plots
└── README.md
```

## Understanding the Code

### Order Book (`order_book.py`)

The limit order book implements:
- **Price-time priority**: Orders at same price execute FIFO
- **Queue tracking**: Know your position in the queue
- **Market orders**: Execute against resting orders

### Strategy (`avellaneda_stoikov.py`)

Core methods:
- `reservation_price()`: Calculate indifference price based on inventory
- `optimal_spread()`: Determine spread based on risk/time
- `calculate_quotes()`: Generate bid/ask prices

### Backtest (`backtest.py`)

Simulates:
- Realistic price paths (Geometric Brownian Motion)
- Random order flow (Poisson arrivals)
- Performance metrics (Sharpe, drawdown, etc.)

## Results

Typical performance on 1-hour backtest:
- **Sharpe Ratio**: 1.5 - 2.5
- **Average Spread**: 10-20 bps
- **Fill Rate**: 5-10%

*Note: These are simulated results. Real market performance will differ due to adverse selection, latency, and market impact.*

## Parameters to Experiment With

### Risk Aversion (γ)
- **Low (0.01)**: Tighter spreads, more aggressive
- **Medium (0.1)**: Balanced approach
- **High (0.5)**: Wider spreads, more conservative

### Volatility (σ)
- Should match actual market volatility
- Higher vol → wider spreads
- Can estimate from historical data

## Extensions

Potential improvements:
- Add transaction costs
- Model adverse selection
- Multiple assets
- Different price processes
- Real market data

## References

1. Avellaneda, M., & Stoikov, S. (2008). *High-frequency Trading in a Limit Order Book*. Quantitative Finance, 8(3), 217-224.

2. Guéant, O., Lehalle, C. A., & Fernandez-Tapia, J. (2013). *Dealing with the Inventory Risk*. Mathematics and Financial Economics, 7(4), 477-507.

## License

MIT License - see LICENSE file

## Author

Built as a learning project to understand market making and market microstructure.
