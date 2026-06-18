import json,os,datetime
os.makedirs("knowledge-base",exist_ok=True)
try:
    import yfinance as yf
    tickers=["BTC-USD","ETH-USD","SPY","QQQ","BRL=X"]
    data={t:{"price":getattr(yf.Ticker(t).fast_info,"last_price",None)} for t in tickers}
except ImportError:
    data={"error":"yfinance not available"}
card={"id":"market-data","updated":datetime.datetime.utcnow().isoformat()+"Z","data":data}
json.dump(card,open("knowledge-base/market-data.json","w"),indent=2)
print("Market done")
