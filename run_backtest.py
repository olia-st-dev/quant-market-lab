# run_backtest.py
from datetime import datetime
import os
from typing import Optional

import pandas as pd
import quantstats as qs
import backtrader as bt

# Tools
from tools.equity_tracker import EquityTracker

# Strategies
from strategies.sma_rsi_strategy import SmaRsiStrategy
from strategies.rsi_trend_strategy import RsiTrendStrategy
from strategies.rsi_macd_strategy import RsiMacdStrategy
from strategies.rsi_macd_trend_strategy import RsiMacdTrendStrategy
from strategies.rsi_trend_with_TP_SL import RsiTrendWithTPSLStrategy
from strategies.hft_mean_reversion_strategy import HFTMeanReversionStrategy
from strategies.sma_price_action_strategy import SMAPriceActionStrategy


# =========================
# Configuration (edit here)
# =========================
PAIR = "EURUSD"              # currency pair to backtest, e.g. "EURUSD", "USDCAD", etc.
STRATEGY = SMAPriceActionStrategy   # pick one of the imported strategies
DATA_PATH = "data"                  # folder with CSVs like EURUSD_1m.csv, etc.
CASH_START = 10_000
ORDER_SIZE = 1_000                  # fixed units
MAIN_TF = "1h"                      # which feed to use as main: "1m", "15m", "1h", "4h", "1d"
ADD_TREND_TF: Optional[str] = None  # e.g. "1h" or "1d" if your strategy reads datas[1]
MAKE_PLOT = False                   # set True to show Backtrader chart at the end
# =========================


# Map timeframe string -> (bt.TimeFrame, compression, dtformat, filename_suffix)
TF_MAP = {
    "1m":  (bt.TimeFrame.Minutes, 1,   "%Y-%m-%d %H:%M:%S", "_1m.csv"),
    "15m": (bt.TimeFrame.Minutes, 15,  "%Y-%m-%d %H:%M:%S", "_15m.csv"),
    "1h":  (bt.TimeFrame.Minutes, 60,  "%Y-%m-%d %H:%M:%S", "_1h.csv"),
    "4h":  (bt.TimeFrame.Minutes, 240, "%Y-%m-%d %H:%M:%S", "_4h.csv"),
    "1d":  (bt.TimeFrame.Days,    1,   "%Y-%m-%d",          "_1d.csv"),
}


def feed_path(pair: str, tf: str) -> str:
    """Builds CSV path like data/EURUSD_15m.csv"""
    suffix = TF_MAP[tf][3]
    return os.path.join(DATA_PATH, f"{pair}{suffix}")


def make_feed(pair: str, tf: str) -> bt.feeds.GenericCSVData:
    """Create a GenericCSVData feed for a given timeframe."""
    if tf not in TF_MAP:
        raise ValueError(f"Unknown timeframe '{tf}'. Supported: {list(TF_MAP.keys())}")

    timeframe, compression, dtformat, _ = TF_MAP[tf]
    return bt.feeds.GenericCSVData(
        dataname=feed_path(pair, tf),
        dtformat=dtformat,
        timeframe=timeframe,
        compression=compression,
        openinterest=-1,
        nullvalue=0.0,
        headers=True,
    )


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def build_report_folder(strategy_cls, pair: str, tf: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = f"reports/{strategy_cls.__name__}_{pair}_{tf}_{stamp}/"
    ensure_dir(folder)
    return folder


def run_backtest():
    report_path = build_report_folder(STRATEGY, PAIR, MAIN_TF)

    # --- Cerebro setup ---
    cerebro = bt.Cerebro()
    cerebro.addstrategy(STRATEGY)
    cerebro.addanalyzer(EquityTracker, _name="equity")

    # Data feeds
    data_main = make_feed(PAIR, MAIN_TF)
    cerebro.adddata(data_main)  # data[0]

    data_trend = None
    if ADD_TREND_TF:
        data_trend = make_feed(PAIR, ADD_TREND_TF)
        cerebro.adddata(data_trend)  # data[1]
        print(f"Added trend TF: {ADD_TREND_TF}")

    # Broker & sizing
    cerebro.broker.setcash(CASH_START)
    cerebro.addsizer(bt.sizers.FixedSize, stake=ORDER_SIZE)

    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")

    # --- Run ---
    results = cerebro.run()
    strat = results[0]

    # --- Equity from analyzer (use exact bt timestamps) ---
    equity_values = strat.analyzers.equity.values
    equity_times = pd.DatetimeIndex(strat.analyzers.equity.datetimes)

    # De-duplicate timestamps just in case (keep last tick of same timestamp)
    eq = pd.Series(equity_values, index=equity_times)
    eq = eq[~eq.index.duplicated(keep="last")]

    # --- Daily drawdown (based on EOD equity) ---
    equity_daily = eq.resample("1D").last().dropna()
    daily_returns = equity_daily.pct_change().dropna()
    daily_curve = (1 + daily_returns).cumprod()
    daily_dd = daily_curve / daily_curve.cummax() - 1.0
    max_daily_dd = daily_dd.min()

    print(f"\nMax Daily Drawdown: {max_daily_dd:.2%}")
    daily_dd.to_csv(os.path.join(report_path, "daily_drawdown.csv"))
    print("Daily drawdown saved to 'daily_drawdown.csv'")

    # --- QuantStats report (use daily returns) ---
    qs_report_filename = "qs_report.html"
    qs_report_path = os.path.join(report_path, qs_report_filename)

    qs.reports.html(
        daily_returns,
        output=qs_report_path,
        title=f"{PAIR} Strategy Performance",
    )
    print(f"QuantStats report saved as '{qs_report_path}'")

    # Save a copy into docs/ for GitHub Pages
    ensure_dir("docs")
    qs_docs_filename = (
        f"{STRATEGY.__name__}_{PAIR}_{MAIN_TF}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_qs_report.html"
    )
    qs_docs_path = os.path.join("docs", qs_docs_filename)
    import shutil
    shutil.copy(qs_report_path, qs_docs_path)
    print(f"QuantStats report also copied to '{qs_docs_path}' for GitHub Pages")

    # --- Summary ---
    final_value = cerebro.broker.getvalue()
    profit = final_value - CASH_START
    roi = (profit / CASH_START) * 100

    print("\n--- Performance Summary ---")
    print(f"Final Portfolio Value: ${final_value:.2f}")
    print(f"Total Profit: ${profit:.2f}")
    print(f"ROI: {roi:.2f}%")

    if MAKE_PLOT:
        cerebro.plot(style="candlestick")


if __name__ == "__main__":
    run_backtest()
