# SCRAPER

An institutional-style systematic equity investment framework focused on Singapore and Asia mid-caps. 

## Framework Architecture
- **Quant Layer:** Factor-based scoring (ROE, Margins, Valuations).
- **Qualitative Layer:** News-driven catalyst and event classification.
- **Risk Engine:** Liquidity-adjusted position sizing and scenario modeling.

## Setup
1. Clone the repo: `git clone <url>`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the screener: `python main.py`

## Backtest Metrics
Currently tracking Drawdown-adjusted Sharpe and Rolling 12M Returns.
