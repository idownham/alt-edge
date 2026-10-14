"""Paced, unauthenticated GET of Kalshi public endpoints. <=1 req/s, 10s backoff on 429. Saves raw JSON + fetch time."""
import json, sys, time, urllib.parse, hashlib, os, datetime, subprocess
BASE = "https://api.elections.kalshi.com/trade-api/v2"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw")  # gitignored
_last = [0.0]
def get(path, **params):
    q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{BASE}{path}" + (f"?{q}" if q else "")
    for attempt in range(5):
        wait = 1.05 - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        p = subprocess.run(["curl", "-sS", "-m", "30", "-H", "Accept: application/json", "-w", "\n%{http_code}", url], capture_output=True, text=True)
        body, code = p.stdout.rsplit("\n", 1)
        if code == "429":
            print("429 -> sleep 10", file=sys.stderr); time.sleep(10); continue
        if code != "200": raise RuntimeError(f"HTTP {code}: {body[:300]}")
        break
    else:
        raise RuntimeError("still 429 after 5 tries")
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, hashlib.sha1(url.encode()).hexdigest()[:12] + ".json")
    with open(fn, "w") as f: json.dump({"url": url, "fetched_utc": ts, "body": json.loads(body)}, f)
    return json.loads(body), ts
if __name__ == "__main__":
    d, ts = get(sys.argv[1], **dict(a.split("=", 1) for a in sys.argv[2:]))
    print(ts); print(json.dumps(d)[:4000])
