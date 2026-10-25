#!/usr/bin/env python3
"""Refresh live-token prices in oracle-feed.json (CoinGecko public API). Run every 15 minutes, then publish."""
import json, sys, urllib.request, datetime, os, fcntl, zoneinfo
D = os.path.dirname(os.path.abspath(__file__))
lock = open(os.path.join(D, '.prices.lock'), 'w'); fcntl.flock(lock, fcntl.LOCK_EX)
F = os.path.join(D, 'oracle-feed.json')
feed = json.load(open(F))
live = [w for w in feed.get('watchlist', []) if w.get('cg_id') and w.get('price') is not None]
if not live: print('no live tokens'); sys.exit(0)
ids = ','.join(sorted({w['cg_id'] for w in live}))
req = urllib.request.Request('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=100&ids=' + ids, headers={'User-Agent': 'oracle-desk'})
data = {c['id']: c for c in json.load(urllib.request.urlopen(req, timeout=30))}
now = datetime.datetime.now(zoneinfo.ZoneInfo('America/Chicago')).replace(microsecond=0).isoformat()
n = 0
for w in live:
    c = data.get(w['cg_id'])
    if not c or c.get('current_price') is None: continue
    w['price'] = c['current_price']
    if c.get('market_cap'): w['market_cap'] = c['market_cap']
    if c.get('total_volume') is not None: w['volume_24h'] = c['total_volume']
    w['price_updated'] = now; w['last_update'] = now; n += 1
feed['prices_updated'] = now
feed = json.loads(json.dumps(feed))
tmp = F + '.tmp'; json.dump(feed, open(tmp, 'w'), indent=1, ensure_ascii=False); os.replace(tmp, F)
print('updated', n, 'tokens at', now)
