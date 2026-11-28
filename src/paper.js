// The last pass: everything lands on one sheet of paper.
//
// It takes the finished picture (the stack of paintings), sharpens it a little, and lays the tooth of the paper
// over it. The picture is read pixel for pixel: nothing here moves or softens it.

import { program, NOISE } from './gl.js';

const VS = /* glsl */ `#version 300 es
layout(location = 0) in vec2 a;
void main() { gl_Position = vec4(a * 2.0 - 1.0, 0.0, 1.0); }`;

const FS = /* glsl */ `#version 300 es
precision highp float;
uniform sampler2D uScene;
uniform vec2 uRes;            // device px
uniform float uDpr, uDim, uSharp;
out vec4 o;
${NOISE}

const vec3 PAPER = vec3(0.985, 0.962, 0.905);

void main() {
  vec2 fc = gl_FragCoord.xy;
  ivec2 at = ivec2(fc);
  vec3 col = texelFetch(uScene, at, 0).rgb;

  // sharpen: push each pixel away from the average of its four neighbours, but never past the lightest or
  // darkest of them, so edges get crisper without growing halos
  ivec2 last = textureSize(uScene, 0) - 1;
  vec3 n = texelFetch(uScene, clamp(at + ivec2(0, 1), ivec2(0), last), 0).rgb;
  vec3 s = texelFetch(uScene, clamp(at - ivec2(0, 1), ivec2(0), last), 0).rgb;
  vec3 e = texelFetch(uScene, clamp(at + ivec2(1, 0), ivec2(0), last), 0).rgb;
  vec3 w = texelFetch(uScene, clamp(at - ivec2(1, 0), ivec2(0), last), 0).rgb;
  vec3 low = min(col, min(min(n, s), min(e, w)));
  vec3 high = max(col, max(max(n, s), max(e, w)));
  col = clamp(col + uSharp * (col - (n + s + e + w) * 0.25), low, high);

  // paper: its tooth over everything, and the corners a little shaded as under a lamp
  vec2 g = fc / uDpr;
  float tooth = vnoise(g * 1.9) * 0.5 + vnoise(g * 0.63 + 31.0) * 0.3 + vnoise(g * 0.09 + 7.0) * 0.2;
  col *= 0.962 + 0.076 * tooth;
  vec2 uv = (fc / uRes - 0.5) * 2.0;
  col *= 1.0 - 0.2 * smoothstep(0.75, 1.5, length(uv));
  col = mix(col, PAPER * 0.97, uDim);
  o = vec4(col, 1.0);
}`;

export class Paper {
  constructor(gl, quad) {
    this.gl = gl;
    this.quad = quad;
    this.prog = program(gl, VS, FS);
  }

  draw({ scene, w, h, dpr, dim, sharp = 0.45 }) {
    const gl = this.gl, u = this.prog.u;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, w, h);
    gl.useProgram(this.prog.p);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, scene);
    gl.uniform1i(u.uScene, 0);
    gl.uniform2f(u.uRes, w, h);
    gl.uniform1f(u.uDpr, dpr);
    gl.uniform1f(u.uDim, dim);
    gl.uniform1f(u.uSharp, sharp);
    this.quad.draw();
  }
}
