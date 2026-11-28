#!/usr/bin/env python3
"""Film the page.

    python3 tools/video.py [port]          # serves the site (default port 7841) and waits for frames
    then open  http://localhost:7841/?capture=1080&record=1     (&pace=3 seconds a painting, &fps=30)
    or, one still:  /?capture=2000&still=21.35&name=music-room   (video/stills/music-room.png)

Nothing is screen-recorded. In capture mode the page renders one exact frame at a time (src/app.js, `shoot`),
with the walk at a stated depth and the animation at a stated time, and posts its raw pixels here; this
server pipes them straight into ffmpeg. The result is video/silent.mp4: one whole lap, beginning and ending
on the first painting filling the frame, so it loops. tools/music.py writes the score and joins the two.
"""
import os
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'video')
FFMPEG = os.environ.get('FFMPEG') or 'ffmpeg'
state = {'ffmpeg': None, 'frames': 0, 'size': 0}
lock = threading.Lock()       # one frame at a time into ffmpeg, whatever thread it arrives on


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def reply(self, code, text):
        body = text.encode()
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        url = urlparse(self.path)
        data = self.rfile.read(int(self.headers.get('Content-Length') or 0))
        with lock:
            self.post(url, data)

    def post(self, url, data):
        if url.path == '/start':
            q = parse_qs(url.query)
            w, h, fps = int(q['w'][0]), int(q['h'][0]), q.get('fps', ['30'])[0]
            os.makedirs(OUT, exist_ok=True)
            if state['ffmpeg']:
                state['ffmpeg'].stdin.close()
                state['ffmpeg'].wait()
            state['ffmpeg'] = subprocess.Popen(
                [FFMPEG, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '%dx%d' % (w, h),
                 '-r', fps, '-i', '-', '-vf', 'vflip', '-c:v', 'libx264', '-preset', 'slow', '-crf', '12',
                 '-pix_fmt', 'yuv420p', '-movflags', '+faststart', os.path.join(OUT, 'silent.mp4')],
                stdin=subprocess.PIPE)
            state['frames'], state['size'] = 0, w * h * 4
            print('filming %dx%d at %s fps' % (w, h, fps), flush=True)
            return self.reply(200, 'ok')
        if url.path == '/frame':
            if not state['ffmpeg'] or len(data) != state['size']:
                return self.reply(400, 'not started, or a frame of the wrong size')
            state['ffmpeg'].stdin.write(data)
            state['frames'] += 1
            if state['frames'] % 300 == 0:
                print('  %d frames' % state['frames'], flush=True)
            return self.reply(200, 'ok')
        if url.path == '/still':
            from PIL import Image
            q = parse_qs(url.query)
            w, h = int(q['w'][0]), int(q['h'][0])
            name = os.path.basename(q.get('name', ['still'])[0]) or 'still'
            os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
            path = os.path.join(OUT, 'stills', name + '.png')
            Image.frombytes('RGBA', (w, h), data).transpose(Image.FLIP_TOP_BOTTOM).convert('RGB').save(path)
            print('still: video/stills/%s.png' % name, flush=True)
            return self.reply(200, 'ok')
        if url.path == '/fail':
            q = parse_qs(url.query)
            print('the page stopped at frame %s: %s' % (q.get('at', ['?'])[0], q.get('why', ['?'])[0]), flush=True)
            return self.reply(200, 'ok')
        if url.path == '/done':
            if state['ffmpeg']:
                state['ffmpeg'].stdin.close()
                code = state['ffmpeg'].wait()
                state['ffmpeg'] = None
                print('wrote video/silent.mp4: %d frames (ffmpeg exit %d)' % (state['frames'], code), flush=True)
            return self.reply(200, str(state['frames']))
        self.reply(404, 'no')


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7841
    print('serving %s on http://localhost:%d  (open /?capture=1080&record=1 to film)' % (ROOT, port), flush=True)
    # threaded: a browser parks idle connections on a server, and a one-at-a-time server waits on them for ever
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.serve_forever()
