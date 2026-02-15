"""
Market Making Simulator - Main Script
Run Avellaneda-Stoikov strategy backtest
"""

import numpy as np
import argparse
from src.backtest import run_backtest, print_results

# Try to import matplotlib (optional)
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Note: matplotlib not installed, skipping plots")


def plot_results(results, save_path='results/backtest.png'):
    """Create simple performance plots"""
    if not HAS_MATPLOTLIB:
        return
        
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # PnL
    axes[0, 0].plot(results.timestamps, results.pnl_history, 'g-', linewidth=1.5)
    axes[0, 0].set_title('P&L Over Time')
    axes[0, 0].set_xlabel('Time (s)')
    axes[0, 0].set_ylabel('P&L ($)')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    
    # Inventory
    axes[0, 1].plot(results.timestamps, results.inventory_history, 'purple', linewidth=1.5)
    axes[0, 1].set_title('Inventory Position')
    axes[0, 1].set_xlabel('Time (s)')
    axes[0, 1].set_ylabel('Inventory')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    
    # PnL distribution
    pnl_changes = np.diff(results.pnl_history)
    axes[1, 0].hist(pnl_changes, bins=30, color='green', alpha=0.7, edgecolor='black')
    axes[1, 0].set_title('P&L Changes Distribution')
    axes[1, 0].set_xlabel('P&L Change')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].axvline(x=0, color='r', linestyle='--', linewidth=2)
    axes[1, 0].grid(True, alpha=0.3)
    
    # Cumulative PnL with drawdown
    cummax = np.maximum.accumulate(results.pnl_history)
    axes[1, 1].plot(results.timestamps, results.pnl_history, 'g-', linewidth=2, label='P&L')
    axes[1, 1].fill_between(results.timestamps, cummax, results.pnl_history,
                           where=(results.pnl_history < cummax), 
                           alpha=0.3, color='red', label='Drawdown')
    axes[1, 1].set_title('Cumulative P&L with Drawdown')
    axes[1, 1].set_xlabel('Time (s)')
    axes[1, 1].set_ylabel('P&L ($)')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to {save_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Market Making Simulator')
    parser.add_argument('--duration', type=int, default=1800,
                       help='Simulation duration in seconds (default: 1800 = 30min)')
    parser.add_argument('--risk-aversion', type=float, default=0.1,
                       help='Risk aversion parameter gamma (default: 0.1)')
    parser.add_argument('--volatility', type=float, default=0.02,
                       help='Market volatility sigma (default: 0.02)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed (default: 42)')
    parser.add_argument('--no-plot', action='store_true',
                       help='Skip plotting')
    
    args = parser.parse_args()
    
    # Set seed for reproducibility
    np.random.seed(args.seed)
    
    print("="*60)
    print("MARKET MAKING SIMULATOR")
    print("Avellaneda-Stoikov Strategy")
    print("="*60)
    print(f"Duration:      {args.duration}s")
    print(f"Risk Aversion: {args.risk_aversion}")
    print(f"Volatility:    {args.volatility}")
    print(f"Random Seed:   {args.seed}")
    print("="*60 + "\n")
    
    # Run backtest
    results = run_backtest(
        duration=args.duration,
        risk_aversion=args.risk_aversion,
        volatility=args.volatility
    )
    
    # Print results
    print_results(results)
    
    # Plot (if matplotlib available)
    if not args.no_plot and HAS_MATPLOTLIB:
        plot_results(results)
    
    print("\nBacktest complete!")


if __name__ == '__main__':
    main()
