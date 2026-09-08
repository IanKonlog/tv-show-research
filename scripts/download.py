"""Cache the complete TVmaze show index, with rate limiting and resumability."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import threading
import time
import urllib.request
import urllib.error
import argparse
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
RAW.mkdir(parents=True, exist_ok=True)
lock = threading.Lock()
last = 0.0

def get(url):
    global last
    for attempt in range(6):
        with lock:
            time.sleep(max(0, .55 - (time.monotonic() - last)))
            last = time.monotonic()
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(url)

def page(n):
    path = RAW / f'page-{n:03d}.json'
    if not path.exists():
        body = get(f'https://api.tvmaze.com/shows?page={n}')
        assert isinstance(json.loads(body), list)
        path.write_bytes(body)
    return n, len(json.loads(path.read_text()))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh',action='store_true',help='Archive the current raw snapshot and download all pages again.')
    args=parser.parse_args()
    manifest_path=ROOT/'data/manifest.json'
    if args.refresh:
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        archive=ROOT/'data/archive'/stamp
        archive.mkdir(parents=True)
        shutil.move(str(RAW),str(archive/'raw'))
        RAW.mkdir(parents=True)
        if manifest_path.exists():shutil.move(str(manifest_path),str(archive/'manifest.json'))
        print(f'Archived the previous snapshot to {archive}',flush=True)
    if not (RAW / 'updates.json').exists():
        (RAW / 'updates.json').write_bytes(get('https://api.tvmaze.com/updates/shows'))
    updates = json.loads((RAW / 'updates.json').read_text())
    pages = max(map(int, updates)) // 250 + 1
    total = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for count, (n, size) in enumerate(pool.map(page, range(pages)), 1):
            total += size
            if count % 25 == 0 or count == pages:
                print(f'{count}/{pages} pages; {total:,} records', flush=True)
    manifest = {'source': 'https://www.tvmaze.com/api', 'license': 'CC BY-SA 4.0',
                'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'pages': pages, 'records': total,
                'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(RAW.glob('page-*.json'))}}
    previous=json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    if previous and previous.get('files')==manifest['files']:
        print('All pages match the cached snapshot; preserving its original retrieval date.',flush=True)
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2))
