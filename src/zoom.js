// The fall itself: a ring of square drawings, each one holding the next at half size in its middle.
//
// Position T is a real number of drawings: at T = k the screen shows drawing k exactly; at T = k + f it
// shows drawing k enlarged 2^f with k+1 (at half that) and k+2 (a quarter) laid over its middle. Because
// the middle half of every drawing IS the next drawing (the art was built that way, see tools/chain.py),
// nothing changes on screen when k ticks over: the stack just starts one drawing later.
//
// The drawings also move a little. Each has a motion map (tools/motion.py) saying where it has leaves and
// cloth for the wind, where it has water, where it has clouds and smoke, and where it has light. The layer
// shader reads the map and moves only those places: one displaced sample of the drawing, never a blend of
// two, so nothing is softened by moving. Motion is confined to a drawing's own ring and dies away toward both
// of its edges, so that where two drawings overlap neither is moving and the join stays exact.

import { program, NOISE } from './gl.js';

const VS = /* glsl */ `#version 300 es
layout(location = 0) in vec2 a;
uniform vec4 uRect;   // centre.xy, half-size.xy, in clip space
out vec2 vUv;
void main() {
  vUv = vec2(a.x, 1.0 - a.y);
  gl_Position = vec4(uRect.xy + (a * 2.0 - 1.0) * uRect.zw, 0.0, 1.0);
}`;

const FS = /* glsl */ `#version 300 es
precision highp float;
uniform sampler2D uLo, uHi, uMo;
uniform float uMix, uFeather, uTime, uAlive, uTexel, uCrisp;
in vec2 vUv;
out vec4 o;
${NOISE}
void main() {
  vec2 uv = vUv;
  float light = 0.0;
  vec2 c = abs(vUv - 0.5) * 2.0;
  float rho = max(c.x, c.y);                                    // 0 at the middle, 1 at the drawing's edge
  float own = smoothstep(0.5, 0.57, rho) * (1.0 - smoothstep(0.86, 0.94, rho)) * uAlive;
  if (own > 0.0) {
    // the map is two pictures side by side: wind, water and drift in the left one, light in the right
    vec2 mu = vec2(clamp(vUv.x, 0.002, 0.998) * 0.5, vUv.y);
    vec4 m = vec4(textureLod(uMo, mu, 0.0).rgb, textureLod(uMo, mu + vec2(0.5, 0.0), 0.0).r) * own;
    float t = uTime;

    // wind in leaves, cloth, flowers: gusts, a slow push and a quicker flutter
    vec2 p = vUv * 7.0;
    float gust = 0.55 + 0.45 * sin(t * 0.23 + vUv.x * 3.0 + vUv.y * 1.7);
    vec2 w = vec2(vnoise(p + vec2(t * 0.42, 0.0)), vnoise(p.yx * 1.3 + vec2(7.0, t * 0.36))) - 0.5;
    w += 0.45 * (vec2(vnoise(p * 2.7 + vec2(-t * 0.8, 3.0)), vnoise(p * 2.7 + vec2(5.0, t * 0.7))) - 0.5);
    uv += m.r * gust * 0.0034 * w;

    // water: ripples running across it, and the light they throw
    float k = vnoise(vUv * 11.0 + t * 0.05);
    uv.x += m.g * 0.0015 * sin(vUv.y * 380.0 + t * 1.9 + k * 9.0);
    uv.y += m.g * 0.0006 * sin(vUv.x * 150.0 - t * 1.3 + k * 6.0);
    light += m.g * 0.055 * sin(vUv.y * 260.0 - t * 2.3 + k * 12.0);

    // clouds, smoke, steam: slow and wide
    vec2 q = vUv * 2.2;
    vec2 d = vec2(vnoise(q + vec2(t * 0.07, 1.0)), vnoise(q + vec2(4.0, t * 0.055))) - 0.5;
    uv += m.b * (0.011 * d + vec2(0.0035 * sin(t * 0.11 + vUv.y * 4.0), 0.0));

    // light: a flame flickers as one; stars each keep their own time
    float flame = (vnoise(vec2(t * 2.6, 3.0)) - 0.5) * 0.9 + (vnoise(vec2(t * 7.0, 9.0)) - 0.5) * 0.5;
    float star = sin(t * 1.6 + 40.0 * vnoise(vUv * 70.0));
    light += m.a * mix(0.3 * flame, 0.55 * star - 0.12, smoothstep(0.62, 0.9, m.a));
  }
  // (a small negative bias keeps a painting crisp while it is drawn smaller than its file)
  vec3 sharp = texture(uHi, uv, -0.6).rgb;
  if (uCrisp > 0.0) {
    // The more a painting is enlarged, the more its edges are firmed up: each texel is pushed away from the
    // average of its four neighbours, but never past the lightest or darkest of them, so no halos grow.
    vec2 d = vec2(uTexel, 0.0);
    vec3 a = texture(uHi, uv + d.xy, -0.6).rgb, b = texture(uHi, uv - d.xy, -0.6).rgb;
    vec3 c2 = texture(uHi, uv + d.yx, -0.6).rgb, e2 = texture(uHi, uv - d.yx, -0.6).rgb;
    vec3 low = min(sharp, min(min(a, b), min(c2, e2))), high = max(sharp, max(max(a, b), max(c2, e2)));
    sharp = clamp(sharp + uCrisp * (sharp - (a + b + c2 + e2) * 0.25), low, high);
  }
  vec3 col = mix(texture(uLo, uv).rgb, sharp, uMix) * (1.0 + light);
  float e = min(min(vUv.x, 1.0 - vUv.x), min(vUv.y, 1.0 - vUv.y));
  float a = uFeather > 0.0 ? smoothstep(0.0, uFeather, e) : 1.0;
  o = vec4(col * a, a);
}`;

const LAYERS = 3;
const SIDE = { xl: 4096, hi: 2048, md: 1024 };

export class Zoom {
  constructor(gl, quad, story) {
    this.gl = gl;
    this.quad = quad;
    this.story = story;
    this.count = story.frames.length;
    this.prog = program(gl, VS, FS);
    this.tier = 'hi';
    this.force = null;                       // a tier to use whatever the screen (for comparing)
    this.crisp = 1;                          // 0 turns the per-painting sharpening off
    this.alive = true;                       // false: the drawings hold perfectly still
    this.frames = story.frames.map((name) => ({ name, lo: null, hi: null, mo: null, state: 'none', fade: 0 }));
    this.loading = 0;
    this.queue = [];
    this.aniso = gl.getExtension('EXT_texture_filter_anisotropic');
    this.none = gl.createTexture();          // an empty motion map, for drawings without one
    gl.bindTexture(gl.TEXTURE_2D, this.none);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4));
  }

  // Which set of files to use for the sharp versions. The outermost painting on screen is enlarged by up to
  // 2x as you walk in, so to stay sharp a painting needs about twice as many pixels as the screen is wide:
  // the 4096 px set for anything over about 1100 device pixels. Phones and small tablets stop at 2048 (a
  // 4096 px texture is seventy megabytes, and several are held at once).
  setTier(devicePixelsAcross) {
    const has = (t) => (this.story.tiers || ['hi', 'md', 'lo']).includes(t);
    const gl = this.gl;
    const small = matchMedia('(pointer: coarse)').matches && Math.min(screen.width, screen.height) < 900;
    const big = has('xl') && gl.getParameter(gl.MAX_TEXTURE_SIZE) >= 4096 && !small;
    const tier = this.force || (devicePixelsAcross > 1100 && big ? 'xl' : devicePixelsAcross > 560 ? 'hi' : 'md');
    if (tier === this.tier) return;
    this.tier = tier;
    for (const f of this.frames) {
      if (f.hi) this.gl.deleteTexture(f.hi);
      f.hi = null; f.state = 'none'; f.fade = 0;
    }
  }

  url(frame, tier) { return `${this.story.base}/${tier}/${frame.name}.webp`; }

  async fetchBitmap(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    const blob = await res.blob();
    try {
      return await createImageBitmap(blob, { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
    } catch {
      return createImageBitmap(blob);          // older Safari does not take the options
    }
  }

  upload(bitmap, data = false) {
    const gl = this.gl;
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    if (data) {                                // a motion map: numbers, not a picture, so no mipmaps
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB8, gl.RGB, gl.UNSIGNED_BYTE, bitmap);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    } else {
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB8, gl.RGB, gl.UNSIGNED_BYTE, bitmap);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      if (this.aniso) gl.texParameterf(gl.TEXTURE_2D, this.aniso.TEXTURE_MAX_ANISOTROPY_EXT, 4);
    }
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    bitmap.close?.();
    return tex;
  }

  // Small versions of every drawing, so there is always something to show, and their motion maps.
  async preload(onProgress) {
    let done = 0;
    await Promise.all(this.frames.map(async (f) => {
      f.lo = this.upload(await this.fetchBitmap(this.url(f, 'lo')));
      onProgress?.(++done / this.count);
    }));
    this.upgrade();
    if (this.story.motion) {
      for (const f of this.frames) {            // not waited for: the fall can begin without them
        this.fetchBitmap(`${this.story.motion}/${f.name}.png`).then((b) => { f.mo = this.upload(b, true); }).catch(() => {});
      }
    }
  }

  // The 512 px versions are only a first coat. In the background, one at a time, each is replaced by its
  // 1024 px version, so that scrolling faster than the sharp ones can arrive never shows anything coarse.
  async upgrade() {
    if (!(this.story.tiers || []).includes('md')) return;
    await new Promise((r) => setTimeout(r, 1200));
    const n = this.count, first = Math.floor(this.story.start || 0);
    for (let i = 0; i < n; i++) {
      const f = this.frames[(first + i) % n];
      try {
        const tex = this.upload(await this.fetchBitmap(this.url(f, 'md')));
        this.gl.deleteTexture(f.lo);
        f.lo = tex;
      } catch { /* keep the first coat */ }
    }
  }

  // Ask for the sharp versions around T (more of them ahead, in the direction of travel); drop far ones.
  want(T, dir) {
    const n = this.count;
    const base = Math.floor(T);
    const big = this.tier === 'xl';              // these are 4096 px: keep fewer of them
    const wanted = [0, 1, 2, dir >= 0 ? 3 : -1, dir >= 0 ? -1 : 3];
    if (!big) wanted.push(dir >= 0 ? 4 : -2);
    for (const off of wanted) {
      const f = this.frames[((base + off) % n + n) % n];
      if (f.state === 'none' && !this.queue.includes(f)) this.queue.push(f);
    }
    for (let i = 0; i < n; i++) {
      const f = this.frames[i];
      let d = Math.abs(i - (T % n));
      d = Math.min(d, n - d);
      if (f.state === 'ready' && d > (big ? 3 : 6)) { this.gl.deleteTexture(f.hi); f.hi = null; f.state = 'none'; f.fade = 0; }
    }
    while (this.loading < 3 && this.queue.length) {
      const f = this.queue.shift();
      if (f.state !== 'none') continue;
      const tier = this.tier;
      f.state = 'loading';
      this.loading++;
      this.fetchBitmap(this.url(f, tier)).then((bmp) => {
        if (tier !== this.tier || f.state !== 'loading') { bmp.close?.(); return; }
        f.hi = this.upload(bmp);
        f.state = 'ready';
      }).catch(() => { f.state = 'none'; }).finally(() => { this.loading--; });
    }
  }

  // Draw the stack for position T into the bound framebuffer (w x h device pixels) at animation time `time`.
  draw(T, w, h, dt, time = 0) {
    const gl = this.gl, u = this.prog.u;
    const n = this.count;
    const base = Math.floor(T);
    const f = T - base;
    const side = Math.max(w, h);                 // the drawings are square and cover the screen
    gl.useProgram(this.prog.p);
    gl.uniform1i(u.uLo, 0);
    gl.uniform1i(u.uHi, 1);
    gl.uniform1i(u.uMo, 2);
    gl.uniform1f(u.uTime, time);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    for (let i = 0; i < LAYERS; i++) {
      const frame = this.frames[((base + i) % n + n) % n];
      if (!frame.lo) continue;
      if (frame.state === 'ready') frame.fade = Math.min(1, frame.fade + dt / 0.45);
      const s = Math.pow(2, f - i) * side;
      gl.uniform4f(u.uRect, 0, 0, s / w, s / h);
      gl.uniform1f(u.uMix, frame.hi ? frame.fade : 0);
      gl.uniform1f(u.uFeather, i === 0 ? 0 : 0.03);
      gl.uniform1f(u.uAlive, this.alive && frame.mo ? 1 : 0);
      const texels = SIDE[this.tier] || 2048;
      const enlarged = s / texels;                       // screen pixels per texel of this painting
      gl.uniform1f(u.uTexel, 1 / texels);
      gl.uniform1f(u.uCrisp, frame.hi ? Math.max(0, Math.min(1.5, (enlarged - 0.55) * 1.6)) * this.crisp : 0);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, frame.lo);
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D, frame.hi || frame.lo);
      gl.activeTexture(gl.TEXTURE2);
      gl.bindTexture(gl.TEXTURE_2D, frame.mo || this.none);
      this.quad.draw();
    }
    gl.disable(gl.BLEND);
  }
}
