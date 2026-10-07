"""Scans the universe and writes data.json (read by index.html)."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import yfinance as yf
from scanner import UNIVERSE, analyse

data = yf.download([f"{t}.NS" for t in UNIVERSE], period="8mo", interval="1d",
                   group_by="ticker", auto_adjust=True, progress=False)
picks = []
for t in UNIVERSE:
    try:
        r = analyse(t, data[f"{t}.NS"])
        if r:
            picks.append(r)
    except Exception as e:
        print("skip", t, e)
picks.sort(key=lambda x: x["score"], reverse=True)
out = {"updated": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST"),
       "picks": picks}
json.dump(out, open("data.json", "w"), indent=1)
print(f"wrote {len(picks)} picks")
