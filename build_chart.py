#!/usr/bin/env python3
"""
QQQ 일봉 차트를 정적 HTML로 만들어 docs/index.html에 쓴다.
GitHub Actions가 매일 이 스크립트를 돌리고 GitHub Pages로 배포한다.
"""

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SYMBOL = "QQQ"
YAHOO_URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?range=1y&interval=1d"
OUT_PATH = Path(__file__).resolve().parent / "docs" / "index.html"
NY = ZoneInfo("America/New_York")


def fetch_daily():
    req = urllib.request.Request(YAHOO_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = json.loads(r.read().decode())

    result = raw["chart"]["result"][0]
    meta = result["meta"]
    closes = result["indicators"]["quote"][0]["close"]
    pairs = [
        (datetime.fromtimestamp(ts, NY).strftime("%m/%d"), round(c, 2))
        for ts, c in zip(result["timestamp"], closes)
        if c is not None
    ]
    return meta, pairs


def render(meta, pairs):
    labels = [p[0] for p in pairs]
    prices = [p[1] for p in pairs]
    price = meta["regularMarketPrice"]
    # meta.previousClose는 range=1y에서 안 오고, chartPreviousClose는 range 시작 시점(1년 전) 값이라
    # 둘 다 못 씀 — 실제 일별 종가 배열의 마지막 두 값으로 직접 계산한다.
    prev = prices[-2]
    delta = price - prev
    pct = delta / prev * 100
    sign = "+" if delta >= 0 else ""
    color = "#3fb950" if delta >= 0 else "#f85149"
    updated = datetime.now(NY).strftime("%Y-%m-%d %H:%M ET")

    return f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{SYMBOL}</title>
<style>
  body {{ margin:0; background:#0f1117; color:#e8e9ed; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; padding:20px 24px; }}
  .sym {{ font-size:14px; color:#8b8d98; letter-spacing:0.5px; }}
  .price {{ font-size:32px; font-weight:600; margin:4px 0 2px; }}
  .delta {{ font-size:14px; font-weight:600; color:{color}; }}
  .updated {{ font-size:11px; color:#5c5e68; margin-top:6px; }}
  #chart {{ margin-top:20px; height:280px; }}
</style>
</head>
<body>
  <div class="sym">{SYMBOL} · 일봉</div>
  <div class="price">${price:,.2f}</div>
  <div class="delta">{sign}{delta:,.2f} ({sign}{pct:.2f}%)</div>
  <div id="chart"><canvas id="c"></canvas></div>
  <div class="updated">업데이트: {updated}</div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
  <script>
    const labels = {json.dumps(labels)};
    const prices = {json.dumps(prices)};
    new Chart(document.getElementById('c'), {{
      type: 'line',
      data: {{ labels, datasets: [{{
        data: prices, borderColor: '{color}', backgroundColor: '{color}22',
        fill: true, borderWidth: 2, pointRadius: 0, tension: 0.1
      }}] }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ callbacks: {{ label: (ctx) => '$' + ctx.parsed.y.toFixed(2) }} }}
        }},
        scales: {{
          x: {{ grid: {{ display:false }}, ticks: {{ color:'#5c5e68', maxTicksLimit:8, font:{{size:11}} }} }},
          y: {{ grid: {{ color:'#1f2129' }}, ticks: {{ color:'#5c5e68', font:{{size:11}}, callback:(v)=>'$'+v }} }}
        }}
      }}
    }});
  </script>
</body></html>
"""


def main():
    meta, pairs = fetch_daily()
    html = render(meta, pairs)
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"작성 완료: {OUT_PATH} ({len(pairs)}일치)")


if __name__ == "__main__":
    main()
