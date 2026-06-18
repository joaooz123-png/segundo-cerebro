import yfinance as yf
import json
import os
from datetime import datetime

TICKERS = {
    'PETR4.SA': 'Petrobras',
    'VALE3.SA': 'Vale',
    'ITUB4.SA': 'Itau',
    '^BVSP': 'IBOVESPA',
    'USDBRL=X': 'USD/BRL',
    'BTC-USD': 'Bitcoin'
}

out_dir = 'data-feeds/market'
history_dir = f'{out_dir}/historical'
os.makedirs(out_dir, exist_ok=True)
os.makedirs(history_dir, exist_ok=True)

data = {'timestamp': datetime.now().isoformat(), 'timezone': 'America/Sao_Paulo', 'quotes': {}}

for ticker, name in TICKERS.items():
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        last = float(info.last_price)
        prev = float(info.previous_close)
        change_pct = round((last - prev) / prev * 100, 2)
        data['quotes'][ticker] = {
            'name': name, 'price': round(last, 2),
            'prev_close': round(prev, 2), 'change_pct': change_pct,
            'direction': 'UP' if change_pct > 0 else 'DOWN'
        }
        print(f'OK: {name} ({ticker}) = {round(last,2)} ({change_pct:+.2f}%)')
    except Exception as e:
        print(f'ERRO {ticker}: {e}')
        data['quotes'][ticker] = {'name': name, 'error': str(e)}

date_str = datetime.now().strftime('%Y-%m-%d')
with open(f'{out_dir}/latest.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
with open(f'{history_dir}/{date_str}.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f'Market fetch concluido: {date_str}')
