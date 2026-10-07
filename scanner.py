"""StockSense scanner: ranks liquid NSE stocks with REAL indicators.

Run:  python scanner.py            (top 5)
      python scanner.py --top 10
Data: Yahoo Finance via yfinance (free, delayed ~15 min, can occasionally be wrong/missing).
This is a screening aid, NOT financial advice. Always check before buying.
"""
import argparse
import pandas as pd
import yfinance as yf
from indicators import sma, rsi, macd, atr

# Liquid large caps (add/remove freely). ".NS" = NSE symbols on Yahoo.
UNIVERSE = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL",
    "ITC", "LT", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "BAJFINANCE", "MARUTI",
    "SUNPHARMA", "NTPC", "POWERGRID", "ONGC", "COALINDIA",
    "TATASTEEL", "WIPRO", "HCLTECH", "M&M", "ADANIPORTS", "TITAN", "ULTRACEMCO",
    "BANKBARODA", "PNB", "SAIL", "IOC", "GAIL", "IDFCFIRSTB", "IRFC", "NHPC", "RECLTD", "CANBK", "BEL", "HAL",
]


def analyse(ticker: str, df: pd.DataFrame):
    df = df.dropna()
    if len(df) < 60:
        return None
    close, high, low, vol = df["Close"], df["High"], df["Low"], df["Volume"]

    price = float(close.iloc[-1])
    sma20, sma50 = sma(close, 20), sma(close, 50)
    r = rsi(close)
    _, _, hist = macd(close)
    a = float(atr(high, low, close).iloc[-1])
    vol_ratio = float(vol.iloc[-1] / vol.iloc[-21:-1].mean())

    score, reasons = 0, []

    if price > sma50.iloc[-1]:
        score += 25
        reasons.append(f"Price {price:.2f} above 50-day average {sma50.iloc[-1]:.2f} (uptrend)")
    if sma20.iloc[-1] > sma50.iloc[-1]:
        score += 15
        reasons.append("20-day average is above 50-day average")

    rv = float(r.iloc[-1])
    if 45 <= rv <= 65:
        score += 20
        reasons.append(f"RSI {rv:.1f}: healthy momentum, not overbought")
    elif rv > 70:
        score -= 15
        reasons.append(f"RSI {rv:.1f}: overbought, risk of pullback")
    elif rv < 30:
        reasons.append(f"RSI {rv:.1f}: oversold (could bounce, but trend is weak)")

    if hist.iloc[-1] > 0 and hist.iloc[-1] > hist.iloc[-2]:
        score += 20
        reasons.append("MACD histogram positive and rising")

    if vol_ratio >= 1.2:
        score += 20
        reasons.append(f"Volume {vol_ratio:.1f}x the 20-day average")

    # ATR-based levels: stop 1.5 ATR below, target 3 ATR above (1:2 risk-reward)
    stop = round(price - 1.5 * a, 2)
    target = round(price + 3.0 * a, 2)

    return {
        "ticker": ticker, "price": round(price, 2), "score": max(score, 0),
        "rsi": round(rv, 1), "vol_ratio": round(vol_ratio, 2),
        "target": target, "stoploss": stop, "reasons": reasons,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()

    symbols = [f"{t}.NS" for t in UNIVERSE]
    data = yf.download(symbols, period="8mo", interval="1d",
                       group_by="ticker", auto_adjust=True, progress=False)

    results = []
    for t in UNIVERSE:
        try:
            res = analyse(t, data[f"{t}.NS"])
            if res:
                results.append(res)
        except Exception as e:
            print(f"skip {t}: {e}")

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"\nTop {args.top} by score (real data, last close):\n")
    for r in results[: args.top]:
        print(f"{r['ticker']:12} score {r['score']:3}  price {r['price']}  "
              f"target {r['target']}  stoploss {r['stoploss']}")
        for why in r["reasons"]:
            print(f"    - {why}")
        print()
    print("Not financial advice. Prices are delayed. Never invest money you can't afford to lose.")


if __name__ == "__main__":
    main()
