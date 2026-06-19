import json
import os
from datetime import datetime

import yfinance as yf

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
        info = yf.Ticker(ticker).fast_info
        last = float(info.last_price)
        prev = float(info.previous_close)
        pct = round((last - prev) / prev * 100, 2)
        data['quotes'][ticker] = {'name': name, 'price': round(last, 2), 'prev_close': round(prev, 2), 'change_pct': pct}
        print(f'OK {ticker}')
    except Exception as exc:
        data['quotes'][ticker] = {'name': name, 'error': str(exc)}
        print(f'ERRO {ticker}: {exc}')

date_str = datetime.now().strftime('%Y-%m-%d')
with open(f'{out_dir}/latest.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
with open(f'{history_dir}/{date_str}.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Market fetch concluido')
