import json,os,datetime
TOPICS=[{"id":"ia-trends"},{"id":"blockchain"},{"id":"healthcare-tech"},{"id":"market-overview"}]
os.makedirs("knowledge-base",exist_ok=True)
for t in TOPICS:
    card={"id":t["id"],"updated":datetime.datetime.utcnow().isoformat()+"Z","status":"auto"}
    json.dump(card,open(f"knowledge-base/{t['id']}.json","w"),indent=2)
    print(f"Updated {t['id']}")
print("Done")
