import json,os,glob,requests
URL=os.environ.get("WISEBASE_API_URL","")
KEY=os.environ.get("WISEBASE_API_KEY","")
if not URL or not KEY:
    print("Secrets not set, skipping");exit(0)
h={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"}
for fp in glob.glob("knowledge-base/*.json"):
    card=json.load(open(fp))
    try:r=requests.post(f"{URL}/cards",headers=h,json=card,timeout=10);print(f"Synced {fp}:{r.status_code}")
    except Exception as e:print(f"Err {fp}:{e}")
print("Sync done")
