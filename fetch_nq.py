"""
Fetch NQ (E-mini Nasdaq-100, front month) 1-minute and 5-minute bars from
Yahoo Finance and write one CSV per CME trading session.

A CME session runs 18:00 ET (previous calendar day) -> 17:00 ET.
Files are named by the session date (the day of the 17:00 close), so
data/1m/NQ_2026-09-16_1m.csv contains bars from 2026-09-15 18:00 ET
through 2026-09-16 17:00 ET, i.e. overnight + RTH + post-close of 16 Sep.

Yahoo keeps 1m history for ~7 days and 5m for ~60 days, so this must run
daily; every run rewrites the sessions it can see, which self-heals
missed days within that window.
"""

import os
import sys
from datetime import timedelta

import pandas as pd
import yfinance as yf

SYMBOL = "NQ=F"
TZ = "America/New_York"
OUT_DIR = "data"

INTERVALS = {
    "1m": "7d",   # Yahoo limit: 1m only for the last 7 days
    "5m": "60d",  # 5m available for the last 60 days
}


def fetch(interval: str, period: str) -> pd.DataFrame:
    df = yf.download(
        SYMBOL,
        interval=interval,
        period=period,
        auto_adjust=False,
        prepost=True,
        progress=False,
        threads=False,
    )
    if df is None or df.empty:
        raise RuntimeError(f"No data returned for {SYMBOL} {interval}")

    # yfinance >= 0.2 returns MultiIndex columns for a single ticker
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]

    # Ensure tz-aware, then convert to New York time
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert(TZ)
    df.index.name = "time_et"
    return df


def add_session_date(df: pd.DataFrame) -> pd.DataFrame:
    """Session date = calendar date of the 17:00 ET close.
    Bars at/after 18:00 ET belong to the NEXT day's session."""
    idx = df.index
    shifted = idx + timedelta(hours=6)  # 18:00 -> 00:00 next day
    df = df.copy()
    df["session_date"] = shifted.strftime("%Y-%m-%d")
    return df


def write_sessions(df: pd.DataFrame, interval: str) -> list[str]:
    out = os.path.join(OUT_DIR, interval)
    os.makedirs(out, exist_ok=True)
    written = []
    for session, chunk in df.groupby("session_date"):
        # skip sessions with almost no bars (weekend stubs / partial current day)
        if len(chunk) < 20:
            continue
        chunk = chunk.drop(columns=["session_date"]).copy()
        chunk.insert(0, "time_et", chunk.index.strftime("%Y-%m-%d %H:%M"))
        chunk = chunk.reset_index(drop=True)
        chunk["open"] = chunk["open"].round(2)
        chunk["high"] = chunk["high"].round(2)
        chunk["low"] = chunk["low"].round(2)
        chunk["close"] = chunk["close"].round(2)
        chunk["volume"] = chunk["volume"].fillna(0).astype("int64")
        path = os.path.join(out, f"NQ_{session}_{interval}.csv")
        chunk.to_csv(path, index=False)
        written.append(path)
    return written


def main() -> int:
    total = []
    for interval, period in INTERVALS.items():
        df = fetch(interval, period)
        df = add_session_date(df)
        paths = write_sessions(df, interval)
        print(f"{interval}: {len(df)} bars -> {len(paths)} session files")
        total.extend(paths)

    # Simple index so the latest session is easy to find
    with open(os.path.join(OUT_DIR, "INDEX.md"), "w") as f:
        f.write("# NQ session files\n\n")
        for p in sorted(total):
            f.write(f"- {p}\n")

    if not total:
        print("Nothing written", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
