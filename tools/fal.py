"""Tiny fal.ai queue client (standard library only).

Reads the key from the FAL_KEY environment variable; never prints it.

    import fal
    url = fal.upload('canvas.png')
    out = fal.run('openai/gpt-image-2.6/sunburst/edit', {...})
    fal.download(out['images'][0]['url'], 'frame.png')
"""
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

QUEUE = 'https://queue.fal.run/'
REST = 'https://rest.alpha.fal.ai'
T2I = 'openai/gpt-image-2.6/sunburst/text-to-image'
EDIT = 'openai/gpt-image-2.6/sunburst/edit'


def _key():
    k = os.environ.get('FAL_KEY')
    if not k:
        raise SystemExit('FAL_KEY is not set')
    return k


def _call(url, method='GET', body=None, headers=None, timeout=180, auth=True):
    h = dict(headers or {})
    if auth:
        h['Authorization'] = 'Key ' + _key()
    data = None
    if body is not None:
        if isinstance(body, (bytes, bytearray)):
            data = bytes(body)
        else:
            data = json.dumps(body).encode()
            h.setdefault('Content-Type', 'application/json')
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:2000]
        raise RuntimeError('HTTP %s from %s: %s' % (e.code, url.split('?')[0], detail))
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {'_raw': raw}


def upload(path):
    """Upload a local file to fal storage and return its URL."""
    ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
    init = _call(REST + '/storage/upload/initiate?storage_type=fal-cdn-v3', 'POST',
                 {'file_name': os.path.basename(path), 'content_type': ctype})
    with open(path, 'rb') as f:
        blob = f.read()
    _call(init['upload_url'], 'PUT', blob, {'Content-Type': ctype}, timeout=600, auth=False)
    return init['file_url']


def run(endpoint, payload, label='', poll=5, timeout=3600, log=sys.stderr):
    """Submit to the queue, wait, and return the result JSON."""
    t0 = time.time()
    sub = _call(QUEUE + endpoint, 'POST', payload)
    status_url, response_url = sub['status_url'], sub['response_url']
    last = None
    while True:
        try:
            st = _call(status_url)
        except RuntimeError as e:  # transient
            print('  [%s] status error: %s' % (label, str(e)[:160]), file=log)
            time.sleep(poll)
            continue
        s = st.get('status')
        if s != last:
            print('  [%s] %s (%.0fs)' % (label, s, time.time() - t0), file=log)
            log.flush()
            last = s
        if s == 'COMPLETED':
            break
        if s not in ('IN_QUEUE', 'IN_PROGRESS'):
            raise RuntimeError('unexpected status: %r' % (st,))
        if time.time() - t0 > timeout:
            raise RuntimeError('timed out after %ss' % timeout)
        time.sleep(poll)
    out = _call(response_url)
    print('  [%s] done in %.0fs' % (label, time.time() - t0), file=log)
    return out


def download(url, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'python-urllib'})
    with urllib.request.urlopen(req, timeout=600) as r, open(path, 'wb') as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    return path
