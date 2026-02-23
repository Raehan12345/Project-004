# quant/screener_engine.py

import time
import pandas as pd
import os
import yfinance as yf

from quant.data import get_info
from quant.ratios import extract_ratios
from quant.score_quant import score_quant
from qual.scrape_news import get_headlines
from qual.sentiment import sentiment_score
from qual.score_qual import score_qual
from quant.sector_rules import SECTOR_RULES, DEFAULT_RULES
from analysis.factor_breakdown import factor_breakdown
from analysis.risk_flags import risk_flags
from analysis.scenarios import scenario_triggers
from qual.event_classifier import classify_event
from qual.llm_summary import summarize_events
from analysis.catalyst_score import catalyst_score
from analysis.valuation_score import valuation_score
from analysis.sector_pe import get_sector_median_pe
from analysis.dividend_adjustment import dividend_adjustment
from analysis.portfolio_scenarios import portfolio_scenario_impact
from analysis.backtest import run_backtest
from analysis.drawdown import drawdown
from quant.technical import get_technical_signals
from analysis.volatility import get_volatility_multiplier
from analysis.gov_exposure import gov_spend_sensitivity
from analysis.turnaround import turnaround_flag
from analysis.order_momentum import order_momentum
from analysis.liquidity import liquidity_cap
from analysis.portfolio import allocate_portfolio

def get_market_regime(benchmark="^STI"):
    try:
        hist = yf.Ticker(benchmark).history(period="1y")
        if len(hist) < 200:
            return "BULL" 
        ma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        current = hist['Close'].iloc[-1]
        return "BULL" if current > ma200 else "BEAR"
    except Exception as e:
        print(f"Regime detection failed: {e}")
        return "BULL"

def run_full_screener():
    TICKER_FILE = "tickers.txt"

    def load_tickers(file):
        if not os.path.exists(file):
            print(f"Error: {file} not found.")
            return []
        with open(file) as f:
            return [line.strip() for line in f if line.strip()]

    tickers = load_tickers(TICKER_FILE)
    results = []

    regime = get_market_regime()
    print(f"Current Market Regime Detected: {regime}")
    print(f"Starting screening for {len(tickers)} tickers...")

    for ticker in tickers:
        try:
            info = get_info(ticker)
            company_name = info.get("longName") or info.get("shortName") or ticker
            avg_volume = info.get("averageVolume")
            price = info.get("currentPrice")
            avg_daily_value = (avg_volume * price) if avg_volume and price else None

            ratios = extract_ratios(info)
            sector = info.get("sector", "Unknown")
            gov_score = gov_spend_sensitivity(sector)
            quant_score = score_quant(ratios, sector)
            is_turnaround = turnaround_flag(ratios)

            pe = ratios.get("pe")
            sector_median_pe = get_sector_median_pe(sector)
            val_score = valuation_score(pe, sector_median_pe)
            div_yield = info.get("dividendYield")
            div_adj = dividend_adjustment(div_yield)
            
            if regime == "BEAR":
                div_adj = div_adj * 1.5 
                
            adj_val_score = min(val_score + div_adj, 1.0)

            headlines = get_headlines(ticker)
            cat_score, cat_triggers = catalyst_score(headlines)
            order_score, order_signal = order_momentum(headlines)
            
            sentiment, event_count = sentiment_score(headlines)
            qual_score = score_qual(sentiment, event_count)

            tech_data = get_technical_signals(ticker)
            tech_score = tech_data["tech_score"]
            tech_trend = tech_data["trend"]
            tech_rsi = tech_data["rsi"]
            vol_multiplier = get_volatility_multiplier(ticker)
            
            if regime == "BEAR":
                vol_multiplier = vol_multiplier * 0.8 

            rules = SECTOR_RULES.get(sector, DEFAULT_RULES)
            breakdown = factor_breakdown(ratios, rules)
            flags = risk_flags(ratios)
            triggers = scenario_triggers(ratios)

            decision_rationale = []
            if order_score > 0: decision_rationale.append(order_signal)
            if cat_score >= 3: decision_rationale.append("Strong near-term catalyst")
            if quant_score >= 3: decision_rationale.append("Solid fundamentals")
            if qual_score < 0: decision_rationale.append("Negative sentiment risk")
            if adj_val_score >= 0.8: decision_rationale.append("Attractive valuation vs sector")
            if div_yield and div_yield >= 0.04: decision_rationale.append("Attractive dividend yield")

            if quant_score >= 4 and qual_score >= 2 and adj_val_score >= 0.5 and tech_score > 0:
                decision = "CORE LONG"
            elif cat_score >= 3 and qual_score >= 2:
                decision = "CATALYST BUY"
            elif adj_val_score >= 0.8 and (qual_score >= 1 or tech_rsi < 30):
                decision = "VALUE ACCUMULATE"
            elif quant_score >= 4:
                decision = "QUALITY HOLD"
            elif qual_score <= -2 or (quant_score <= 1 and adj_val_score <= 0.3) or tech_score <= -2:
                decision = "AVOID / EXIT"
            else:
                decision = "NEUTRAL / WATCH"

            results.append({
                "CompanyName": company_name,
                "Ticker": ticker,
                "Sector": sector,
                "QuantScore": quant_score,
                "QualScore": qual_score,
                "CatalystScore": cat_score,
                "OrderScore": order_score,
                "GovScore": gov_score,
                "ValuationScore": val_score,
                "AdjValuationScore": adj_val_score,
                "DividendYield": div_yield,
                "Decision": decision,
                "DecisionRationale": "; ".join(decision_rationale) if decision_rationale else "No clear upside drivers",
                "PassedFactors": ", ".join([k for k, v in breakdown.items() if v == "PASS"]),
                "RiskFlags": "; ".join(flags),
                "ScenarioTriggers": "; ".join(triggers),
                "CatalystTriggers": "; ".join(cat_triggers),
                "AvgDailyValue": avg_daily_value,
                "Turnaround": is_turnaround,
                "TechScore": tech_score,
                "Trend": tech_trend,
                "RSI": tech_rsi,
                "VolMultiplier": vol_multiplier,
                "QuantWeighted": quant_score * 1.5,
                "QualWeighted": qual_score
            })

            time.sleep(1)

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    df = pd.DataFrame(results)

    df["PortfolioScore"] = (
        df["QuantScore"] * 1.2
        + df["QualScore"]
        + df["CatalystScore"] * 1.5
        + df["OrderScore"] * 1.2
        + df["GovScore"] * 0.5
        + df["AdjValuationScore"] * 2
        + df["TechScore"] * 1.0
    )

    df["DividendTilt"] = df["DividendYield"].fillna(0).clip(upper=0.06)
    df["AdjPortfolioScore"] = (
        df["PortfolioScore"] * (1 + df["DividendTilt"]) * df["VolMultiplier"]
    )

    df["LiquidityCap"] = df["AvgDailyValue"].apply(liquidity_cap)
    df["TargetWeight"] = allocate_portfolio(df)

    df.to_csv("stock_screen_results.csv", index=False)
    print("Screening Complete. File saved.")

if __name__ == "__main__":
    run_full_screener()