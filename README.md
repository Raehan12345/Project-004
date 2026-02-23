# Multi-Market Quantitative Execution Engine

## Overview
A modular, production-grade algorithmic trading system built in Python. This framework automates the lifecycle of a long-only equity rebalancing strategy, integrating real-time market data analysis with state-aware execution across SGX, HKEX, NYSE, and NSE.



## Technical Highlights
* **Z-Score Based Entry Signals**: Implements volatility-adjusted mean reversion logic using standard deviation thresholds rather than static percentages.
* **Portfolio Delta Reconciliation**: Custom synchronization engine that calculates the difference between current holdings and target model weights to minimize transaction costs.
* **Multi-Market Ticker Normalization**: A robust fallback system to handle disparate ticker symbology across international exchanges (e.g., resolving .SI, .HK, .NS).
* **Security Standards**: Fully decoupled configuration using environment variables (.env) and RSA-encrypted key management.

## System Architecture
The engine operates in a five-phase execution loop to ensure safety and precision:

1. **Factor-Based Screening**: Scans a custom universe to rank assets based on momentum and liquidity factors.
2. **State Handshake**: Establishes a secure session with the Tiger Brokers Open API and retrieves real-time buying power.
3. **Diagnostic Health Check**: Generates a Target vs. Actual audit table to visualize portfolio drift before execution.
4. **Intraday Signal Scan**: Monitors live price action against volatility-adjusted entry windows.
5. **Autonomous Cleanup**: Identifies and liquidates positions that no longer meet the model's ranking criteria.



## Tech Stack
* **Language**: Python 3.12+
* **APIs**: Tiger Brokers Open API (Trade/Quote SDK)
* **Data Libraries**: yfinance, pandas, numpy
* **Environment Management**: python-dotenv

## Project Structure
* **execution/**
    * **broker_api.py**: RSA Authentication and Connection Management.
    * **order_manager.py**: Position Delta Logic and Risk Guardrails.
* **quant/**
    * **screener_engine.py**: Factor-based Ranking Logic.
    * **intraday_signals.py**: Volatility-adjusted Triggers.
* **main.py**: Main Orchestrator.
* **requirements.txt**: Dependency Manifest.

## Demonstration (Mock Mode)
To view the engine's logic without active API credentials:

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run `python main.py --dry-run` to view the Diagnostic Health Check and Signal Scanning in action using historical sample data.