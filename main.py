import pandas as pd

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

TICKER_FILE = "TiongWoon.txt"

def load_tickers(file):
    with open(file) as f:
        return [line.strip() for line in f if line.strip()]

tickers = load_tickers(TICKER_FILE)

results = []

for ticker in tickers:
    try:
        #quant
        info = get_info(ticker)
        company_name = (
            info.get("longName")
            or info.get("shortName")
            or ticker
        )
        avg_volume = info.get("averageVolume")
        price = info.get("currentPrice")

        avg_daily_value = None
        if avg_volume and price:
            avg_daily_value = avg_volume * price

        ratios = extract_ratios(info)
        sector = info.get("sector", "Unknown")

        from analysis.gov_exposure import gov_spend_sensitivity
        gov_score = gov_spend_sensitivity(sector)

        quant_score = score_quant(ratios, sector)

        from analysis.turnaround import turnaround_flag
        is_turnaround = turnaround_flag(ratios)

        #asia-style
        pe = ratios.get("pe")
        sector_median_pe = get_sector_median_pe(sector)
        val_score = valuation_score(pe, sector_median_pe)
        div_yield = info.get("dividendYield")  # yfinance gives this as decimal
        div_adj = dividend_adjustment(div_yield)

        adj_val_score = min(val_score + div_adj, 1.0)

        #qual
        headlines = get_headlines(ticker)

        cat_score, cat_triggers = catalyst_score(headlines)

        from analysis.order_momentum import order_momentum

        order_score, order_signal = order_momentum(headlines)

        if order_score > 0:
            decision_rationale.append(order_signal)

        print(f"{ticker} headlines count:", len(headlines))
        print(f"\n{ticker} qualitative events:")
        for h in headlines:
            print(f"- [{classify_event(h)}] {h}")

        sentiment, event_count = sentiment_score(headlines)
        qual_score = score_qual(sentiment, event_count)

        llm_summary = None

        if qual_score != 0:
            try:
                llm_summary = summarize_events(ticker, headlines)
            except Exception as e:
                print(f"LLM failed for {ticker}: {e}")
                llm_summary = "LLM summary unavailable"

        #final
        total_score = quant_score * 1.5 + qual_score

        MAX_QUANT = 5 * 1.5  
        MAX_QUAL = 2
        MAX_TOTAL = MAX_QUANT + MAX_QUAL  

        score_pct = total_score / MAX_TOTAL

        rules = SECTOR_RULES.get(sector, DEFAULT_RULES)

        breakdown = factor_breakdown(ratios, rules)
        flags = risk_flags(ratios)
        triggers = scenario_triggers(ratios)

        # Asia-style conviction score
        asia_conviction = (
            quant_score * 1.2
            + qual_score
            + cat_score * 1.5
        )

        decision_rationale = []

        # catalyst
        if cat_score >= 3:
            decision_rationale.append("Strong near-term catalyst")
        elif cat_score >= 2:
            decision_rationale.append("Potential catalyst developing")

        # fundamentals
        if quant_score >= 3:
            decision_rationale.append("Solid fundamentals")
        elif quant_score <= 1:
            decision_rationale.append("Weak fundamentals")

        # sentiment
        if qual_score < 0:
            decision_rationale.append("Negative sentiment risk")

        # valuation
        if adj_val_score >= 0.8:
            decision_rationale.append("Attractive valuation vs sector")
        elif adj_val_score <= 0.3:
            decision_rationale.append("Valuation risk")

        if div_yield and div_yield >= 0.04:
            decision_rationale.append("Attractive dividend yield")

        # fallback
        if not decision_rationale:
            decision_rationale.append("No clear upside drivers")

        #decision logic
        if cat_score >= 3 and quant_score >= 3 and val_score >= 0.6:
            decision = "CATALYST BUY"

        elif cat_score >= 2 and val_score >= 0.7:
            decision = "VALUE + CATALYST"

        elif adj_val_score >= 0.8 and quant_score >= 2:
            decision = "DEEP VALUE"

        elif quant_score >= 3:
            decision = "QUALITY HOLD"

        elif cat_score >= 2:
            decision = "SPECULATIVE"

        else:
            decision = "AVOID"

        if decision == "AVOID" and is_turnaround:
            decision = "TURNAROUND / SPECULATIVE"

        print(f"\n{ticker} ({sector})")
        print("-" * 40)

        print("Factor breakdown:")
        for k, v in breakdown.items():
            print(f"  {k}: {v}")

        print("Risk flags:")
        if flags:
            for f in flags:
                print(f"  - {f}")
        else:
            print("  None")

        print("What would change the view:")
        if triggers:
            for t in triggers:
                print(f"  - {t}")
        else:
            print("  None")

        results.append({
            "CompanyName": company_name,
            "Ticker": ticker,
            "Sector": sector,
            "QuantScore": quant_score,
            "QualScore": qual_score,
            "CatalystScore":cat_score,
            "OrderScore": order_score,
            "GovScore": gov_score,
            "ValuationScore": val_score,
            "AdjValuationScore": adj_val_score,
            "DividendYield": div_yield,
            "ScorePct": round(score_pct, 2),
            "Decision": decision,
            "DecisionRationale": "; ".join(decision_rationale),
            "PassedFactors": ", ".join([k for k, v in breakdown.items() if v == "PASS"]),
            "RiskFlags": "; ".join(flags),
            "ScenarioTriggers": "; ".join(triggers),
            "CatalystTriggers": "; ".join(cat_triggers),
            "AvgDailyValue": avg_daily_value,
            "Turnaround": is_turnaround,
        })
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
)

df["DividendTilt"] = df["DividendYield"].fillna(0).clip(upper=0.06)
df["AdjPortfolioScore"] = (
    df["PortfolioScore"] * (1 + df["DividendTilt"])
)

# NORMALISED CONVICTION SCORE
max_portfolio_score = (
    5 * 1.2   # Quant
    + 2       # Qual
    + 3 * 1.5 # Catalyst
    + 1 * 2   # Valuation
)

df["ConvictionPct"] = df["AdjPortfolioScore"] / max_portfolio_score
df["ConvictionPct"] = df["ConvictionPct"].clip(0, 1)

print(df[["Ticker", "AdjPortfolioScore", "ConvictionPct"]]
      .sort_values("ConvictionPct", ascending=False)
      .head(10))

from analysis.liquidity import liquidity_cap

df["LiquidityCap"] = df["AvgDailyValue"].apply(liquidity_cap)

from analysis.portfolio import allocate_portfolio
df["TargetWeight"] = allocate_portfolio(df)

for scenario in ["Rate Cut", "China Slowdown", "Energy Shock"]:
    df[f"{scenario}Impact"] = portfolio_scenario_impact(df, scenario)
    df[f"{scenario}WeightedImpact"] = (
        df["TargetWeight"] * df[f"{scenario}Impact"]
    )

print("\nPortfolio Scenario Impacts:")
for scenario in ["Rate Cut", "China Slowdown", "Energy Shock"]:
    total_impact = df[f"{scenario}WeightedImpact"].sum()
    print(f"{scenario}: {total_impact:.2%}")

df.to_csv("stock_screen_results.csv", index=False)

df["ReturnProxy"] = df["TargetWeight"] * df["ConvictionPct"]

#to narrow universe
"""
top30 = (
    df[df["TargetWeight"] > 0]
    .sort_values("ReturnProxy", ascending=False)
    .head(30)
)

print("\nTop 30 stocks based on backtest-weighted conviction:")
print(
    top30[[
        "Ticker",
        "Sector",
        "TargetWeight",
        "ConvictionPct",
        "Decision",
        "Turnaround"
    ]]
)
"""

# SIMPLE BACKTEST
bt_returns = run_backtest(
    df,
    start="2021-01-01",
    end="2024-01-01"
)

print("\nBacktest summary:")
print(f"Total return: {(1 + bt_returns).prod() - 1:.2%}")
print(f"Annualised return: {(1 + bt_returns.mean())**12 - 1:.2%}")
print(f"Volatility (monthly): {bt_returns.std():.2%}")

import yfinance as yf

benchmark = yf.download(
    "^STI",
    start="2021-01-01",
    end="2024-01-01",
    interval="1mo",
    auto_adjust=True,
    progress=False,
)["Close"].pct_change().dropna()

benchmark = benchmark.squeeze()

bench_total_return = (1 + benchmark).prod() - 1

print("\nBenchmark (STI):")
print(f"Total return: {bench_total_return:.2%}")

# DRAWDOWN ANALYSIS
dd_series, max_dd = drawdown(bt_returns)

print("\nDrawdown analysis:")
print(f"Max drawdown: {max_dd:.2%}")

# drawdown duration
dd_duration = (dd_series < 0).astype(int).groupby(
    (dd_series == 0).cumsum()
).sum().max()

print(f"Max drawdown duration (months): {dd_duration}")
bench_dd, bench_max_dd = drawdown(benchmark)

dd_series, max_dd = drawdown(bt_returns)

# DRAWDOWN-ADJUSTED SHARPE
annualised_return = (1 + bt_returns.mean())**12 - 1
annualised_vol = bt_returns.std() * (12 ** 0.5)

dd_adj_sharpe = annualised_return / (annualised_vol * abs(max_dd))

print("\nRisk-adjusted metrics:")
print(f"Drawdown-adjusted Sharpe: {dd_adj_sharpe:.2f}")

print("\nBenchmark drawdown:")
print(f"Max drawdown: {bench_max_dd:.2%}")
bench_dd_series, bench_max_dd = drawdown(benchmark)

bench_ann_return = (1 + benchmark.mean())**12 - 1
bench_ann_vol = benchmark.std() * (12 ** 0.5)

bench_dd_adj_sharpe = bench_ann_return / (bench_ann_vol * abs(bench_max_dd))

print(f"Benchmark DD-adjusted Sharpe: {bench_dd_adj_sharpe:.2f}")

#for backtest charting
bt_df = pd.DataFrame({
    "StrategyReturn": bt_returns,
    "BenchmarkReturn": benchmark
})

bt_df["StrategyCumulative"] = (1 + bt_df["StrategyReturn"]).cumprod()
bt_df["BenchmarkCumulative"] = (1 + bt_df["BenchmarkReturn"]).cumprod()

bt_df["StrategyDrawdown"] = (
    bt_df["StrategyCumulative"] / bt_df["StrategyCumulative"].cummax() - 1
)
bt_df["BenchmarkDrawdown"] = (
    bt_df["BenchmarkCumulative"] / bt_df["BenchmarkCumulative"].cummax() - 1
)

# Rolling 12-month returns
bt_df["StrategyRolling12M"] = bt_df["StrategyReturn"].rolling(12).apply(
    lambda x: (1 + x).prod() - 1
)
bt_df["BenchmarkRolling12M"] = bt_df["BenchmarkReturn"].rolling(12).apply(
    lambda x: (1 + x).prod() - 1
)

#stats table
stats = {
    "Metric": [
        "Total Return",
        "Annualised Return",
        "Annualised Volatility",
        "Max Drawdown",
        "Max Drawdown Duration (months)",
        "Drawdown-adjusted Sharpe",
    ],
    "Strategy": [
        (1 + bt_returns).prod() - 1,
        annualised_return,
        annualised_vol,
        max_dd,
        dd_duration,
        dd_adj_sharpe,
    ],
    "Benchmark (STI)": [
        bench_total_return,
        bench_ann_return,
        bench_ann_vol,
        bench_max_dd,
        None,
        bench_dd_adj_sharpe,
    ],
}

stats_df = pd.DataFrame(stats)

print("\nSaved results to stock_screen_results.csv")
print(df)

df["QuantWeighted"] = df["QuantScore"] * 1.5
df["QualWeighted"] = df["QualScore"]

df["LeverageRisk"] = df["RiskFlags"].str.contains("leverage", case=False, na=False).astype(int)

df["QualityScore"] = (
    df["PassedFactors"].str.contains("Profitability", na=False).astype(int)
    + df["PassedFactors"].str.contains("Margins", na=False).astype(int)
    + df["PassedFactors"].str.contains("Growth", na=False).astype(int)
)

import xlsxwriter

excel_file = "stock_screen_dashboard.xlsx"

def excel_col(col_num):
    s = ""
    while col_num:
        col_num, r = divmod(col_num - 1, 26)
        s = chr(65 + r) + s
    return s

with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df.to_excel(writer, sheet_name="Data", index=False)
    stats_df.to_excel(writer, sheet_name="BacktestStats", index=False)
    bt_df.to_excel(writer, sheet_name="BacktestData")

    workbook  = writer.book
    dashboard_ws = workbook.add_worksheet("Dashboard")


    col_idx = {col: i + 1 for i, col in enumerate(df.columns)}
    n = len(df) + 1  # Excel row count

    # =========================
    # CHART 1 — Score Breakdown
    # =========================
    chart1 = workbook.add_chart({"type": "column", "subtype": "stacked"})

    t_col  = excel_col(col_idx["Ticker"])
    q_col  = excel_col(col_idx["QuantWeighted"])
    ql_col = excel_col(col_idx["QualWeighted"])

    chart1.add_series({
        "name": "Quant",
        "categories": f"=Data!${t_col}$2:${t_col}${n}",
        "values": f"=Data!${q_col}$2:${q_col}${n}",
    })

    chart1.add_series({
        "name": "Qual",
        "categories": f"=Data!${t_col}$2:${t_col}${n}",
        "values": f"=Data!${ql_col}$2:${ql_col}${n}",
    })

    chart1.set_title({"name": "Score Decomposition"})
    dashboard_ws.insert_chart("Q2", chart1)

    # =========================
    # CHART 2 — Business Quality
    # =========================
    chart2 = workbook.add_chart({"type": "column"})

    qual_col = excel_col(col_idx["QualityScore"])

    chart2.add_series({
        "name": "Quality Score",
        "categories": f"=Data!${t_col}$2:${t_col}${n}",
        "values": f"=Data!${qual_col}$2:${qual_col}${n}",
    })

    chart2.set_title({"name": "Business Quality"})
    dashboard_ws.insert_chart("Q20", chart2)

    # =========================
    # CHART 3 — Risk vs Reward
    # =========================
    chart3 = workbook.add_chart({"type": "scatter"})

    risk_col  = excel_col(col_idx["ValuationScore"])
    conv_col  = excel_col(col_idx["ConvictionPct"])

    chart3.add_series({
        "name": "Risk vs Reward",
        "categories": f"=Data!${risk_col}$2:${risk_col}${n}",
        "values": f"=Data!${conv_col}$2:${conv_col}${n}",
        "marker": {"type": "circle"},
    })

    chart3.set_title({"name": "Risk vs Conviction"})
    chart3.set_x_axis({"name": "Valuation Score (Higher = Cheaper)"})
    chart3.set_y_axis({"name": "Conviction (%)"})

    dashboard_ws.insert_chart("Q38", chart3)


    # =========================
    # CHART 4 — Quality vs Conviction
    # =========================
    chart4 = workbook.add_chart({"type": "scatter"})

    qual_col = excel_col(col_idx["QualityScore"])
    conv_col = excel_col(col_idx["ConvictionPct"])

    chart4.add_series({
        "name": "Quality vs Conviction",
        "categories": f"=Data!${qual_col}$2:${qual_col}${n}",
        "values": f"=Data!${conv_col}$2:${conv_col}${n}",
        "marker": {"type": "diamond"},
    })

    chart4.set_title({"name": "Business Quality vs Conviction"})
    chart4.set_x_axis({"name": "Quality Score"})
    chart4.set_y_axis({"name": "Conviction (%)"})

    dashboard_ws.insert_chart("Q56", chart4)

    dashboard_ws.write("A1", "Stock Analysis Dashboard")
    dashboard_ws.write("A19", "Business Quality")
    dashboard_ws.write("A37", "Risk vs Reward")
    dashboard_ws.write("A55", "Quality vs Score")

    # =========================
    # BACKTEST CHARTS SHEET
    # =========================
    bt_ws = workbook.add_worksheet("BacktestCharts")

    #chart 5
    chart5 = workbook.add_chart({"type": "line"})

    chart5.add_series({
        "name": "Strategy",
        "categories": "=BacktestData!$A$2:$A$1048576",
        "values": "=BacktestData!$D$2:$D$1048576",
    })

    chart5.add_series({
        "name": "Benchmark",
        "categories": "=BacktestData!$A$2:$A$1048576",
        "values": "=BacktestData!$E$2:$E$1048576",
    })

    chart5.set_title({"name": "Cumulative Return"})
    chart5.set_y_axis({"name": "Growth of $1"})

    bt_ws.insert_chart("A2", chart5)

    #chart 6
    chart6 = workbook.add_chart({"type": "line"})

    chart6.add_series({
        "name": "Strategy Drawdown",
        "categories": "=BacktestData!$A$2:$A$1048576",
        "values": "=BacktestData!$F$2:$F$1048576",
    })

    chart6.add_series({
        "name": "Benchmark Drawdown",
        "categories": "=BacktestData!$A$2:$A$1048576",
        "values": "=BacktestData!$G$2:$G$1048576",
    })

    chart6.set_title({"name": "Drawdown"})
    chart6.set_y_axis({"name": "Drawdown"})

    bt_ws.insert_chart("A20", chart6)

    #chart 7
    chart7 = workbook.add_chart({"type": "line"})

    chart7.add_series({
        "name": "Strategy Rolling 12M",
        "categories": "=BacktestData!$A$2:$A$1048576",
        "values": "=BacktestData!$H$2:$H$1048576",
    })

    chart7.add_series({
        "name": "Benchmark Rolling 12M",
        "categories": "=BacktestData!$A$2:$A$1048576",
        "values": "=BacktestData!$I$2:$I$1048576",
    })

    chart7.set_title({"name": "Rolling 12-Month Return"})
    chart7.set_y_axis({"name": "Return"})

    bt_ws.insert_chart("A38", chart7)


print("Excel dashboard created successfully.")
