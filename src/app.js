// Day In, Day In: the page.
//
// An endless scroll into a ring of paintings. Scrolling (or dragging, or the arrow keys) is a push along the
// walk; left alone it drifts slowly inward. Each frame the stack of drawings for the current depth is composed
// into one picture, with the small movements inside the drawings added as it is drawn (see zoom.js), and the
// paper pass lays that picture on one sheet.

import { STORY } from './story.js';
import { quad as makeQuad, target } from './gl.js';
import { Zoom } from './zoom.js';
import { Paper } from './paper.js';

const $ = (sel) => document.querySelector(sel);
const canvas = $('#fall');
const body = document.body;
const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
const N = STORY.frames.length;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

// ?capture=1080 turns the page into a camera for tools/video.py: a fixed square canvas at that many pixels, no
// title, and nothing drawn until a frame is asked for (mmm.shoot). Add &record=1 and it films itself.
const query = new URLSearchParams(location.search);
const capture = Number(query.get('capture')) || 0;
if (capture) body.classList.add('capture');

// errors are the only writing: no title, no cards
function say(msg) {
  const p = document.createElement('p');
  p.className = 'plain';
  p.textContent = msg;
  body.append(p);
}

const gl = canvas.getContext('webgl2', { antialias: false, alpha: false, powerPreference: 'high-performance' });
if (!gl) {
  say('this drawing needs WebGL 2, which this browser does not have');
  throw new Error('no WebGL2');
}

const quad = makeQuad(gl);
const zoom = new Zoom(gl, quad, STORY);
zoom.force = query.get('tier');          // ?tier=hi and ?sharp=0 are for comparing; nothing links to them
const sharp = query.has('sharp') ? Number(query.get('sharp')) : 0.45;
if (query.get('sharp') === '0') zoom.crisp = 0;
const paper = new Paper(gl, quad);
let scene = null;                     // the composed picture

let W = 0, H = 0, dpr = 1, cw = 0, ch = 0;
function resize() {
  W = capture || innerWidth; H = capture || innerHeight;
  dpr = capture ? 1 : Math.min(devicePixelRatio || 1, 2);
  while (W * H * dpr * dpr > 9.5e6 && dpr > 1) dpr -= 0.25;     // every device pixel, up to about a 4K screen
  cw = Math.max(2, Math.round(W * dpr)); ch = Math.max(2, Math.round(H * dpr));
  canvas.width = cw; canvas.height = ch;
  scene?.free();
  scene = target(gl, cw, ch);
  zoom.setTier(capture ? 4096 : Math.max(cw, ch));       // filming always uses the largest paintings
  if (capture) canvas.style.width = canvas.style.height = `${capture}px`;
}
addEventListener('resize', resize);
resize();

// ---- the fall ---------------------------------------------------------------------------------------------
const CRUISE = 0.085;                 // drawings per second when left alone
const MAX_RATE = 3.2;
let T = STORY.start;                  // position on the ring of drawings
let fallen = 0;                       // drawings fallen since the visit began (never wraps)
let rate = 0;                         // drawings per second; negative is back out
let heading = 1;                      // which way it drifts when left alone: the way it was last pushed
let resting = still;                  // space bar (or reduced motion): no drift
let begun = false;

function begin() {                    // the walk has started
  if (begun) return;
  begun = true;
  body.classList.add('begun');
}

function push(d) {
  rate = clamp(rate + d, -MAX_RATE, MAX_RATE);
  if (Math.abs(rate) > 0.06) heading = Math.sign(rate);
  resting = still;
  if (ready) begin();
}

// ---- input -------------------------------------------------------------------------------------------------
const keys = new Set();
let drag = null;

addEventListener('wheel', (e) => {
  e.preventDefault();
  const unit = e.deltaMode === 1 ? 32 : e.deltaMode === 2 ? H : 1;
  push(clamp(e.deltaY * unit, -240, 240) * 0.0022);
}, { passive: false });

canvas.addEventListener('pointerdown', (e) => {
  canvas.setPointerCapture(e.pointerId);
  drag = { y: e.clientY };
  canvas.classList.add('dragging');
});
canvas.addEventListener('pointermove', (e) => {
  if (!drag) return;
  push((drag.y - e.clientY) * 0.008);               // finger up the screen: deeper
  drag.y = e.clientY;
});
const letGo = () => { drag = null; canvas.classList.remove('dragging'); };
canvas.addEventListener('pointerup', letGo);
canvas.addEventListener('pointercancel', letGo);

addEventListener('keydown', (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if ([' ', 'arrowup', 'arrowdown', 'pageup', 'pagedown'].includes(k)) e.preventDefault();
  if (k === ' ' && !e.repeat) { resting = !resting; if (ready) begin(); }
  else if (k === 'f' && !e.repeat) (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen?.());
  else keys.add(k);
});
addEventListener('keyup', (e) => keys.delete(e.key.toLowerCase()));
addEventListener('blur', () => { keys.clear(); letGo(); });

// ---- the loop -----------------------------------------------------------------------------------------------
let ready = false;
let last = performance.now();
let clock = 0;                         // seconds of animation inside the drawings (stands still under reduced motion)
let dim = 1;                           // 1 = blank paper, eases to 0 when the drawings are in

function tick(dt) {
  if (!still) clock += dt;
  if (!ready) return;
  if (keys.has('arrowdown') || keys.has('pagedown') || keys.has('s')) push(1.7 * dt);
  if (keys.has('arrowup') || keys.has('pageup') || keys.has('w')) push(-1.7 * dt);
  const want = resting ? 0 : CRUISE * heading;
  rate += (want - rate) * (1 - Math.exp(-dt / 1.1));          // a push dies away into the drift
  T = ((T + rate * dt) % N + N) % N;
  fallen += rate * dt;
  if (fallen > 0.45) begin();
  zoom.want(T, Math.sign(rate) || 1);
  dim = Math.max(0, dim - dt / 0.9);
}

function draw(dt) {
  gl.bindFramebuffer(gl.FRAMEBUFFER, scene.fb);
  gl.viewport(0, 0, cw, ch);
  gl.clearColor(0.965, 0.925, 0.824, 1);
  gl.clear(gl.COLOR_BUFFER_BIT);
  if (ready) zoom.draw(T, cw, ch, dt, clock);
  paper.draw({ scene: scene.tex, w: cw, h: ch, dpr, dim, sharp });
}

function frame(now) {
  const dt = Math.min((now - last) / 1000, 0.05);
  last = now;
  tick(dt);
  draw(dt);
  requestAnimationFrame(frame);
}
if (!capture) requestAnimationFrame(frame);

// ---- arrive --------------------------------------------------------------------------------------------------
(async () => {
  try {
    await zoom.preload();
    zoom.want(T, 1);
    ready = true;
    body.classList.remove('loading');
    if (capture && query.has('still')) takeStill();
    else if (capture && query.get('record')) record();
  } catch (err) {
    console.error(err);
    say('the painting could not be fetched; try reloading');
  }
})();

// ---- filming (capture mode only) --------------------------------------------------------------------------------
const breathe = () => new Promise((r) => { const c = new MessageChannel(); c.port1.onmessage = r; c.port2.postMessage(0); });

let film = null;

// One frame of film: the walk at depth t (in paintings) and animation time c (seconds), as raw RGBA rows,
// bottom row first. Waits until the three paintings in view are loaded at full size, so no frame is ever soft.
async function shoot(t, c) {
  T = ((t % N) + N) % N;
  clock = c;
  dim = 0;
  const base = Math.floor(T);
  for (;;) {
    zoom.want(T, 1);
    const sharp = [0, 1, 2].every((k) => zoom.frames[(base + k) % N].state === 'ready');
    const maps = !STORY.motion || [0, 1, 2].every((k) => zoom.frames[(base + k) % N].mo);
    if (ready && sharp && maps) break;
    await breathe();                 // not a timer: a background tab slows timers to one a second
  }
  for (const f of zoom.frames) if (f.state === 'ready') f.fade = 1;
  draw(0);
  // one buffer for every frame: a fresh 4.6 MB array each time outruns the garbage collector, and after a
  // thousand-odd frames the browser runs out of memory
  if (!film || film.length !== cw * ch * 4) film = new Uint8Array(cw * ch * 4);
  gl.readPixels(0, 0, cw, ch, gl.RGBA, gl.UNSIGNED_BYTE, film);
  return film;
}

// Film one whole lap and hand every frame to tools/video.py, which is serving this page.
// pace: seconds per painting; fps: frames a second. The lap begins and ends on painting 0 filling the frame.
async function record() {
  const fps = Number(query.get('fps')) || 30, pace = Number(query.get('pace')) || 3;
  const total = Math.round(N * pace * fps);
  const state = window.recording = { frame: 0, total, done: false, error: null };
  try {
    await fetch(`/start?w=${cw}&h=${ch}&fps=${fps}`, { method: 'POST' });
    for (let n = 0; n < total; n++) {
      const px = await shoot(n / (pace * fps), n / fps);
      const res = await fetch('/frame', { method: 'POST', body: px });
      if (!res.ok) throw new Error(`frame ${n}: ${res.status}`);
      await res.text();
      state.frame = n + 1;
      if (n % 30 === 0) document.title = `filming ${n}/${total}`;
    }
    await fetch('/done', { method: 'POST' });
    state.done = true;
    document.title = 'filmed';
  } catch (err) {
    state.error = String(err);
    document.title = 'filming failed';
    fetch(`/fail?at=${state.frame}&why=${encodeURIComponent(state.error)}`, { method: 'POST' }).catch(() => {});
  }
}

// One still, sent to tools/video.py: ?capture=2000&still=21.35 (the depth) &name=...
async function takeStill() {
  const px = await shoot(Number(query.get('still')) || 0, Number(query.get('clock')) || 5);
  await fetch(`/still?w=${cw}&h=${ch}&name=${encodeURIComponent(query.get('name') || 'still')}`, { method: 'POST', body: px });
  document.title = 'still taken';
}

// for looking under the bonnet from the console
window.mmm = {
  zoom, push, shoot, record,
  get T() { return T; }, set T(v) { T = v; },
  get rate() { return rate; }, set rate(v) { rate = v; },
  get resting() { return resting; }, set resting(v) { resting = v; },
  get clock() { return clock; }, set clock(v) { clock = v; },
  get fallen() { return fallen; },
  // run the world forward by hand (seconds), e.g. when the tab is in the background and frames are scarce
  run(seconds, step = 1 / 60) {
    for (let t = 0; t < seconds; t += step) tick(step);
    for (const f of zoom.frames) if (f.state === 'ready') f.fade = 1;
    draw(step);
  },
};
