# Multi-Market Quantitative Execution Engine

## Overview
A modular, production-grade algorithmic trading system built in Python. This framework automates the lifecycle of a long-only equity rebalancing strategy, integrating real-time market data analysis with state-aware execution across **SGX, HKEX, NYSE, and NSE**.


## Technical Highlights
* **Z-Score Based Entry Signals**: Implements volatility-adjusted mean reversion logic using standard deviation thresholds rather than static percentages to determine entry points.
* **VWAP Momentum Trigger**: Features a breakout detection system that initiates trades when price action trends above the Volume-Weighted Average Price on surging volume.
* **Portfolio Delta Reconciliation**: Custom synchronization engine that calculates the difference between current holdings and target model weights to minimize transaction costs.
* **Multi-Market Ticker Normalization**: A robust fallback system to handle disparate ticker symbology across international exchanges (e.g., resolving .SI, .HK, .NS).
* **Advanced Risk Management**: Integrated server-side trailing stops (ATR-based) and a 48-hour earnings blackout filter to mitigate binary event risk.

## System Architecture
The engine operates in a five-phase execution loop to ensure safety and precision:

1. **Factor-Based Screening**: Scans a custom universe to rank assets based on momentum, profitability, and liquidity factors.
2. **State Handshake**: Establishes a secure session with the Tiger Brokers Open API and retrieves real-time buying power.
3. **Diagnostic Health Check**: Generates a Target vs. Actual audit table to visualize portfolio drift before any execution occurs.
4. **Intraday Signal Scan**: Monitors live price action against both mean-reversion (Dip Buy) and momentum (Breakout) windows.
5. **Autonomous Cleanup**: Automatically identifies and liquidates positions that no longer meet the model's ranking criteria.


## Quantitative Analysis & Risk Controls
* **Correlation Penalty**: Actively reduces the target weight of assets that exhibit high 90-day correlation (>0.80) to higher-conviction positions to prevent correlated drawdown.
* **Sector Concentration Caps**: Enforces a strict 30% maximum weight per sector to maintain industry diversification.
* **Macro Regime Adaptation**: Dynamically adjusts volatility and dividend multipliers based on whether the benchmark is trending above or below its 200-day moving average.

## Tech Stack
* **Language**: Python 3.12+
* **APIs**: Tiger Brokers Open API (Trade/Quote SDK)
* **Data Libraries**: `yfinance`, `pandas`, `numpy`, `vaderSentiment`
* **Environment Management**: `python-dotenv` for RSA-encrypted key management

## Project Structure
* **`execution/`**: RSA Authentication, Connection Management, and Order Delta Logic.
* **`quant/`**: Alpha Factor generation, Z-score signals, and Earnings Blackout logic.
* **`analysis/`**: Risk-parity allocation, correlation penalties, and backtesting modules.
* **`qual/`**: Sentiment analysis and NLP-based event classification for news headlines.

## Demonstration (Mock Mode)
To view the engine's logic without active API credentials:

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run `python main.py --dry-run` to view the Diagnostic Health Check and Signal Scanning in action using sample data.