/* ==========================================================================
   BAKERSFIELD QUAKE (661 LAN) — INTERACTIVE 3D / 360° SPRITE & GAG ENGINE
   Single-Canvas Scissored Multi-Viewport WebGL2 + Fullscreen Holodeck Studio
   Works 100% offline via file:// AND over HTTP/HTTPS!
   ========================================================================== */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);

  // ==================== SCREENSHOT / GIF LIGHTBOX ====================
  let lbItems = [];
  let lbIdx = 0;

  function initLightbox() {
    const wraps = Array.from(document.querySelectorAll('.shot-img-wrap'));
    lbItems = [];
    wraps.forEach((w) => {
      const img = w.querySelector('img');
      if (!img) return;
      const card = w.closest('.shot-card');
      const capEl = card ? card.querySelector('.shot-cap') : null;
      const idx = lbItems.length;
      lbItems.push({
        src: img.getAttribute('src'),
        title: img.getAttribute('alt') || (capEl ? capEl.textContent.trim() : 'BakersfieldQuake Screenshot'),
      });
      w.addEventListener('click', () => openLightbox(idx));
    });

    const modal = $('lightbox-modal');
    if (!modal) return;
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeLightbox();
    });
    const btnClose = $('lb-close');
    if (btnClose) btnClose.addEventListener('click', closeLightbox);
    const btnPrev = $('lb-prev');
    if (btnPrev) btnPrev.addEventListener('click', () => stepLightbox(-1));
    const btnNext = $('lb-next');
    if (btnNext) btnNext.addEventListener('click', () => stepLightbox(+1));
  }

  function openLightbox(idx) {
    if (!lbItems.length) return;
    lbIdx = ((idx % lbItems.length) + lbItems.length) % lbItems.length;
    const item = lbItems[lbIdx];
    const modal = $('lightbox-modal');
    const img = $('lb-img');
    const cap = $('lb-caption');
    const cnt = $('lb-counter');
    if (img) img.src = item.src;
    if (cap) cap.textContent = item.title;
    if (cnt) cnt.textContent = `[${lbIdx + 1} / ${lbItems.length}]`;
    if (modal) modal.classList.add('open');
  }

  function stepLightbox(delta) {
    openLightbox(lbIdx + delta);
  }

  function closeLightbox() {
    const modal = $('lightbox-modal');
    if (modal) modal.classList.remove('open');
  }

  // ==================== UNDERDOG & BLUE SHELL CALCULATOR ====================
  function initUnderdogCalc() {
    const sTop = $('ud-top-slider');
    const sYou = $('ud-you-slider');
    if (!sTop || !sYou) return;

    function update() {
      const topF = parseInt(sTop.value, 10) || 0;
      const youF = parseInt(sYou.value, 10) || 0;
      $('ud-top-val').textContent = topF;
      $('ud-you-val').textContent = youF;

      // Exact math from source/underdog.qc!
      const deficit = Math.max(0, topF - youF);
      const boost = deficit <= 1 ? 0.0 : Math.min(1.0, (deficit - 1) / 12.0);
      const pct = Math.round(boost * 100);

      const hp = 100 + Math.floor(100 * boost);
      let armorTxt = '100 GREEN (30%)';
      if (deficit >= 8) armorTxt = '200 RED (80%)';
      else if (deficit >= 4) armorTxt = '150 YELLOW (60%)';

      const slayer = Math.round(50 * boost);
      const reloadCut = Math.round(40 * boost);
      const regenDelay = (5.0 - 3.0 * boost).toFixed(1);
      const regenHp = Math.round(10 + 25 * boost);
      const isLeader = youF >= topF && topF > 0;
      const regen = isLeader ? '+10 HP/s (5.0s) · 0 AP' : `+${regenHp} HP/s (${regenDelay}s) + AP`;
      const pwr = boost >= 0.60 ? '5s QUAD / INVIS / PENT!' : '3.0s Spawn Shield';

      $('ud-stat-gap').textContent = deficit > 0 ? `-${deficit} Frags` : (youF >= topF ? 'TIED / #1 LEADER!' : '0');
      $('ud-stat-boost').textContent = `${pct}%`;
      $('ud-stat-hp').textContent = `${hp} HP`;
      $('ud-stat-armor').textContent = armorTxt;
      $('ud-stat-slayer').textContent = slayer > 0 ? `+${slayer}% vs Ahead` : 'Base (1.0x)';
      $('ud-stat-reload').textContent = reloadCut > 0 ? `-${reloadCut}% Faster` : 'Standard';
      $('ud-stat-regen').textContent = regen;
      $('ud-stat-pwr').textContent = pwr;

      const bs = $('ud-blueshell-alert');
      if (bs) {
        if (boost >= 0.80) {
          bs.style.background = 'linear-gradient(90deg, #0044aa, #00bbff, #0044aa)';
          bs.style.color = '#ffff00';
          bs.innerHTML = '🔵⚡ <b>BLUE SHELL UNLOCKED (80%+ BOOST)!!</b> Press <b>Key 9</b> — Your next Mega Man glows electric blue (<code>EF_BLUE</code>), ignores everyone else on the map, and hunts ONLY the #1 Leader!';
        } else if (youF >= topF && topF >= 2) {
          bs.style.background = 'linear-gradient(90deg, #661100, #aa3300, #661100)';
          bs.style.color = '#ffe600';
          bs.innerHTML = '👑🔥 <b>YOU ARE THE #1 LEADER!</b> Watch out: you glow gold (+2), carry a +1 Frag Bounty (+4), show through walls (+6/+10), and trailing players deal up to +50% Giant Slayer DMG!';
        } else {
          const need = Math.max(1, 11 - deficit);
          bs.style.background = 'linear-gradient(90deg, #0c1f38, #14365c, #0c1f38)';
          bs.style.color = '#b8e8ff';
          bs.innerHTML = `🛞 Trail the #1 Leader by <b>11+ frags</b> (${need} more behind) to unlock the <b>🔵 BLUE SHELL MEGA MAN</b>!`;
        }
      }

      // Highlight Leader Heat ladder steps based on lead margin (assuming runner-up is youF)
      const leadMargin = Math.max(0, topF - youF);
      document.querySelectorAll('[data-heat-min]').forEach((el) => {
        const hm = parseInt(el.getAttribute('data-heat-min'), 10);
        el.classList.toggle('active-heat', leadMargin >= hm);
      });
    }

    sTop.addEventListener('input', update);
    sYou.addEventListener('input', update);
    update();
  }

  // ==================== MATRIX HELPERS ====================
  function mat4Identity(o) {
    o.fill(0);
    o[0] = o[5] = o[10] = o[15] = 1;
    return o;
  }

  function mat4Persp(o, fovy, aspect, near, far) {
    const f = 1.0 / Math.tan(fovy * 0.5);
    const nf = 1.0 / (near - far);
    o.fill(0);
    o[0] = f / Math.max(0.2, aspect);
    o[5] = f;
    o[10] = (far + near) * nf;
    o[11] = -1;
    o[14] = 2 * far * near * nf;
    return o;
  }

  function mat4LookAt(o, eye, tgt, up) {
    let zx = eye[0] - tgt[0], zy = eye[1] - tgt[1], zz = eye[2] - tgt[2];
    let zl = Math.hypot(zx, zy, zz) || 1;
    zx /= zl; zy /= zl; zz /= zl;
    let xx = up[1] * zz - up[2] * zy;
    let xy = up[2] * zx - up[0] * zz;
    let xz = up[0] * zy - up[1] * zx;
    let xl = Math.hypot(xx, xy, xz);
    if (xl < 1e-5) { xx = 1; xy = 0; xz = 0; xl = 1; }
    xx /= xl; xy /= xl; xz /= xl;
    const yx = zy * xz - zz * xy;
    const yy = zz * xx - zx * xz;
    const yz = zx * xy - zy * xx;
    o[0] = xx; o[1] = yx; o[2] = zx; o[3] = 0;
    o[4] = xy; o[5] = yy; o[6] = zy; o[7] = 0;
    o[8] = xz; o[9] = yz; o[10] = zz; o[11] = 0;
    o[12] = -(xx * eye[0] + xy * eye[1] + xz * eye[2]);
    o[13] = -(yx * eye[0] + yy * eye[1] + yz * eye[2]);
    o[14] = -(zx * eye[0] + zy * eye[1] + zz * eye[2]);
    o[15] = 1;
    return o;
  }

  function mat4Mul(o, a, b) {
    for (let c = 0; c < 4; c++) {
      const b0 = b[c * 4], b1 = b[c * 4 + 1], b2 = b[c * 4 + 2], b3 = b[c * 4 + 3];
      o[c * 4]     = a[0] * b0 + a[4] * b1 + a[8]  * b2 + a[12] * b3;
      o[c * 4 + 1] = a[1] * b0 + a[5] * b1 + a[9]  * b2 + a[13] * b3;
      o[c * 4 + 2] = a[2] * b0 + a[6] * b1 + a[10] * b2 + a[14] * b3;
      o[c * 4 + 3] = a[3] * b0 + a[7] * b1 + a[11] * b2 + a[15] * b3;
    }
    return o;
  }

  // ==================== BINARY GZIP UNPACKER ====================
  async function unpackGzipBase64(b64) {
    const binStr = atob(b64);
    const gz = new Uint8Array(binStr.length);
    for (let i = 0; i < binStr.length; i++) gz[i] = binStr.charCodeAt(i);
    const ds = new DecompressionStream('gzip');
    const stream = new Blob([gz]).stream().pipeThrough(ds);
    return await new Response(stream).arrayBuffer();
  }

  // ==================== MAIN WEBGL2 MULTI-VIEWPORT ENGINE ====================
  async function initWebGLViewer() {
    const PACK = window.BQ_MODELS_PACK;
    const canvas = $('gl-canvas');
    if (!PACK || !canvas) return;

    const gl = canvas.getContext('webgl2', {
      alpha: true,
      premultipliedAlpha: false,
      antialias: true,
      depth: true,
      powerPreference: 'high-performance',
    });
    if (!gl) {
      console.warn('WebGL2 unavailable');
      return;
    }

    const arenaBuf = await unpackGzipBase64(PACK.binGz);
    const i8  = (sl) => new Int8Array(arenaBuf, sl[0], sl[1]);
    const i16 = (sl) => new Int16Array(arenaBuf, sl[0], sl[1] >> 1);
    const u16 = (sl) => new Uint16Array(arenaBuf, sl[0], sl[1] >> 1);
    const f32 = (sl) => new Float32Array(arenaBuf, sl[0], sl[1] >> 2);

    function compileShader(type, src) {
      const sh = gl.createShader(type);
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
        throw new Error(gl.getShaderInfoLog(sh));
      }
      return sh;
    }
    function compileProg(vs, fs) {
      const p = gl.createProgram();
      gl.attachShader(p, compileShader(gl.VERTEX_SHADER, vs));
      gl.attachShader(p, compileShader(gl.FRAGMENT_SHADER, fs));
      gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
        throw new Error(gl.getProgramInfoLog(p));
      }
      return p;
    }
    function uni(p, names) {
      const o = {};
      for (const n of names) o[n] = gl.getUniformLocation(p, n);
      return o;
    }
    function mkBuf(target, data, usage) {
      const b = gl.createBuffer();
      gl.bindBuffer(target, b);
      gl.bufferData(target, data, usage || gl.STATIC_DRAW);
      return b;
    }

    // 1. Sky / Dungeon Studio Backdrop Shader (writes alpha = 1.0 inside viewport!)
    const pSky = compileProg(`#version 300 es
precision highp float;
precision highp int;
layout(location=0) in vec2 aPos;
out vec2 vUv;
void main() { vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.999, 1.0); }`, `#version 300 es
precision highp float;
precision highp int;
in vec2 vUv;
uniform int uTheme;
out vec4 fragColor;
void main() {
  vec3 top = vec3(0.11, 0.06, 0.18);
  vec3 bot = vec3(0.03, 0.02, 0.05);
  if (uTheme == 1) { top = vec3(0.24, 0.04, 0.16); bot = vec3(0.05, 0.01, 0.05); }
  else if (uTheme == 2) { top = vec3(0.05, 0.14, 0.24); bot = vec3(0.02, 0.04, 0.08); }
  else if (uTheme == 3) { top = vec3(0.22, 0.04, 0.04); bot = vec3(0.05, 0.01, 0.02); }
  vec3 c = mix(bot, top, smoothstep(0.0, 1.0, vUv.y));
  float vig = 1.0 - 0.35 * dot(vUv - 0.5, vUv - 0.5);
  fragColor = vec4(c * vig, 1.0);
}`);
    const uSky = uni(pSky, ['uTheme']);

    // 2. Ground Cyber/Quake Grid Shader
    const pGround = compileProg(`#version 300 es
precision highp float;
precision highp int;
layout(location=0) in vec2 aPos;
uniform mat4 uVP;
uniform float uSize;
out vec3 vW;
void main() {
  vW = vec3(aPos.x * uSize, aPos.y * uSize, 0.0);
  gl_Position = uVP * vec4(vW, 1.0);
}`, `#version 300 es
precision highp float;
precision highp int;
in vec3 vW;
uniform float uSize;
uniform float uTime;
out vec4 fragColor;
void main() {
  vec2 g = vec2(vW.x + uTime * 18.0, vW.y) / 24.0;
  vec2 fw = fwidth(g);
  vec2 grid = abs(fract(g - 0.5) - 0.5) / max(fw, 1e-4);
  float line = 1.0 - min(min(grid.x, grid.y), 1.0);
  float fade = 1.0 - smoothstep(uSize * 0.22, uSize * 0.92, length(vW.xy));
  float a = line * fade * 0.34;
  if (a < 0.01) discard;
  fragColor = vec4(0.45, 0.26, 0.68, a);
}`);
    const uGround = uni(pGround, ['uVP', 'uSize', 'uTime']);

    // 3. MorphingLit + Billboard + Shadow Mesh Shader
    const pMesh = compileProg(`#version 300 es
precision highp float;
precision highp int;
layout(location=0) in vec3 aPos0;
layout(location=1) in vec3 aPos1;
layout(location=2) in vec3 aNrm0;
layout(location=3) in vec3 aNrm1;
layout(location=4) in vec2 aUv;
uniform mat4 uVP;
uniform int uBillboard;
uniform vec3 uBillRight;
uniform vec3 uBillUp;
uniform vec3 uOffset;
uniform float uLerp;
uniform float uPosScale;
uniform int uShadowPass;
out vec3 vWPos;
out vec3 vWNrm;
out vec2 vUv;
void main() {
  vec3 pLocal = mix(aPos0, aPos1, uLerp) * uPosScale;
  vec3 nLocal = normalize(mix(aNrm0, aNrm1, uLerp) + vec3(1e-6));
  vec3 p, n;
  if (uBillboard == 1) {
    p = uOffset + pLocal.y * uBillRight + pLocal.z * vec3(0.0, 0.0, 1.0);
    n = normalize(cross(uBillRight, vec3(0.0, 0.0, 1.0)));
  } else if (uBillboard == 2) {
    p = uOffset + pLocal.y * uBillRight + pLocal.z * uBillUp;
    n = normalize(cross(uBillRight, uBillUp));
  } else {
    p = pLocal + uOffset;
    n = nLocal;
  }
  if (uShadowPass == 1) {
    vec3 L = normalize(vec3(0.32, -0.35, 1.25));
    float h = max(0.0, p.z);
    vec3 sp = vec3(p.x - L.x * (h / L.z), p.y - L.y * (h / L.z), 0.08);
    vWPos = sp; vWNrm = vec3(0.0, 0.0, 1.0); vUv = aUv;
    gl_Position = uVP * vec4(sp, 1.0);
  } else {
    vWPos = p; vWNrm = n; vUv = aUv;
    gl_Position = uVP * vec4(p, 1.0);
  }
}`, `#version 300 es
precision highp float;
precision highp int;
in vec3 vWPos;
in vec3 vWNrm;
in vec2 vUv;
uniform sampler2D uTex;
uniform sampler2D uGlowTex;
uniform int uHasGlow;
uniform vec4 uTileRect;
uniform float uScrollV;
uniform vec3 uEye;
uniform float uMetallic;
uniform float uRoughness;
uniform float uSpec;
uniform int uUnlit;
uniform int uAlphaTest;
uniform int uAlphaBlend;
uniform int uShadowPass;
out vec4 fragColor;
void main() {
  vec2 uv = uTileRect.xy + vec2(vUv.x, vUv.y + uScrollV) * uTileRect.zw;
  vec4 texel = texture(uTex, uv);
  if (uAlphaTest == 1 && texel.a < 0.35) discard;
  if (uShadowPass == 1) { fragColor = vec4(0.02, 0.01, 0.05, 0.30); return; }
  float outA = uAlphaBlend == 1 ? texel.a : 1.0;
  if (uUnlit == 1) {
    fragColor = vec4(texel.rgb * 1.06, outA);
    return;
  }
  vec3 N = normalize(gl_FrontFacing ? vWNrm : -vWNrm);
  vec3 V = normalize(uEye - vWPos);
  vec3 L1 = normalize(vec3( 0.45, -0.42, 0.79));
  vec3 L2 = normalize(vec3(-0.62,  0.55, 0.56));
  vec3 L3 = normalize(vec3( 0.15,  0.78, 0.25));
  vec3 hemi = mix(vec3(0.26, 0.24, 0.32), vec3(0.48, 0.52, 0.62), 0.5 + 0.5 * N.z);
  vec3 diff = hemi
            + vec3(1.08, 1.03, 0.98) * max(dot(N, L1), 0.0) * 0.88
            + vec3(0.56, 0.68, 0.86) * max(dot(N, L2), 0.0) * 0.42
            + vec3(0.42, 0.48, 0.60) * max(dot(N, L3), 0.0) * 0.24;
  float shin = mix(145.0, 14.0, uRoughness);
  float sp1 = pow(max(dot(N, normalize(L1 + V)), 0.0), shin);
  vec3 R = reflect(-V, N);
  vec3 envCol = mix(vec3(0.18, 0.20, 0.28), vec3(0.95, 0.98, 1.0), smoothstep(-0.2, 0.6, R.z));
  vec3 lit = texel.rgb * diff * (1.0 - 0.28 * uMetallic)
           + texel.rgb * envCol * (uMetallic * 0.66)
           + vec3(1.05, 1.02, 0.96) * sp1 * uSpec * 0.48;
  if (uHasGlow == 1) lit += texture(uGlowTex, uv).rgb * 1.35;
  lit *= 1.08;
  lit = (lit * (2.51 * lit + 0.03)) / (lit * (2.43 * lit + 0.59) + 0.14);
  fragColor = vec4(lit, outA);
}`);
    const uMesh = uni(pMesh, [
      'uVP', 'uBillboard', 'uBillRight', 'uBillUp', 'uOffset', 'uLerp', 'uPosScale', 'uShadowPass',
      'uTex', 'uGlowTex', 'uHasGlow', 'uTileRect', 'uScrollV', 'uEye',
      'uMetallic', 'uRoughness', 'uSpec', 'uUnlit', 'uAlphaTest', 'uAlphaBlend',
    ]);

    // 4. Wireframe Overlay Shader
    const pWire = compileProg(`#version 300 es
precision highp float;
precision highp int;
layout(location=0) in vec3 aPos0;
layout(location=1) in vec3 aPos1;
uniform mat4 uVP;
uniform int uBillboard;
uniform vec3 uBillRight;
uniform vec3 uBillUp;
uniform vec3 uOffset;
uniform float uLerp;
uniform float uPosScale;
void main() {
  vec3 pLocal = mix(aPos0, aPos1, uLerp) * uPosScale;
  vec3 p = (uBillboard == 1)
    ? (uOffset + pLocal.y * uBillRight + pLocal.z * vec3(0.0, 0.0, 1.0))
    : (pLocal + uOffset);
  gl_Position = uVP * vec4(p, 1.0);
}`, `#version 300 es
precision highp float;
precision highp int;
out vec4 fragColor;
void main() { fragColor = vec4(0.25, 1.0, 0.65, 0.72); }`);
    const uWire = uni(pWire, ['uVP', 'uBillboard', 'uBillRight', 'uBillUp', 'uOffset', 'uLerp', 'uPosScale']);

    const quadVao = gl.createVertexArray();
    gl.bindVertexArray(quadVao);
    mkBuf(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]));
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

    // Checkerboard placeholder texture while base64 WebP/PNG images decode
    function makeFallbackTex() {
      const t = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, t);
      const px = new Uint8Array(32 * 32 * 4);
      for (let y = 0; y < 32; y++) {
        for (let x = 0; x < 32; x++) {
          const v = ((x >> 2) + (y >> 2)) & 1 ? 185 : 110;
          const i = (y * 32 + x) * 4;
          px[i] = v; px[i + 1] = v; px[i + 2] = v + 20; px[i + 3] = 255;
        }
      }
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 32, 32, 0, gl.RGBA, gl.UNSIGNED_BYTE, px);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      return t;
    }
    const fallbackTex = makeFallbackTex();

    // Decode all packed textures asynchronously
    const texImages = new Array(PACK.textures.length);
    PACK.textures.forEach((t, idx) => {
      t.glTex = fallbackTex;
      t._loaded = false;
      const img = new Image();
      texImages[idx] = img;
      img.onload = () => {
        const gt = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, gt);
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
        const wrap = t.wrap ? gl.REPEAT : gl.CLAMP_TO_EDGE;
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wrap);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, wrap);
        if (t.nearest) {
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
        } else if (t.noMip) {
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        } else {
          gl.generateMipmap(gl.TEXTURE_2D);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        }
        t.glTex = gt;
        t._loaded = true;
      };
      img.src = t.uri;
    });

    const models = PACK.models.map((d, idx) => Object.assign({}, d, { idx, _uploaded: false }));
    const modelById = {};
    for (const m of models) modelById[m.id] = m;

    function ensureModelUploaded(m) {
      if (m._uploaded) return;
      const [mn, mx] = m.bbox;
      m.size = [mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]];
      m.center = [(mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5, (mn[2] + mx[2]) * 0.5];
      m.R = Math.max(6.0, Math.hypot(m.size[0], m.size[1], m.size[2]) * 0.48);
      const zOff = (mn[2] >= -2.0 && mn[2] <= 12.0) ? 0.0 : -mn[2];
      m.offset = [-m.center[0], -m.center[1], zOff];

      for (const s of m.surfaces) {
        const stride = s.nv * 4;
        const pArr = new Int16Array(i16(s.pos));
        for (let i = stride; i < pArr.length; i++) pArr[i] = pArr[i - stride] + pArr[i];
        const nArr = new Int8Array(i8(s.nrm));
        for (let i = stride; i < nArr.length; i++) nArr[i] = nArr[i - stride] + nArr[i];

        s.vao = gl.createVertexArray();
        gl.bindVertexArray(s.vao);
        s.bufPos = mkBuf(gl.ARRAY_BUFFER, pArr);
        gl.enableVertexAttribArray(0);
        gl.vertexAttribPointer(0, 3, gl.SHORT, false, 8, 0);
        gl.enableVertexAttribArray(1);
        gl.vertexAttribPointer(1, 3, gl.SHORT, false, 8, 0);
        s.bufNrm = mkBuf(gl.ARRAY_BUFFER, nArr);
        gl.enableVertexAttribArray(2);
        gl.vertexAttribPointer(2, 3, gl.BYTE, true, 4, 0);
        gl.enableVertexAttribArray(3);
        gl.vertexAttribPointer(3, 3, gl.BYTE, true, 4, 0);
        s.bufUv = mkBuf(gl.ARRAY_BUFFER, f32(s.uv));
        gl.enableVertexAttribArray(4);
        gl.vertexAttribPointer(4, 2, gl.FLOAT, false, 0, 0);
        s.ibEdges = mkBuf(gl.ELEMENT_ARRAY_BUFFER, u16(s.edges));
        s.ibTris = mkBuf(gl.ELEMENT_ARRAY_BUFFER, u16(s.tris));
        s._lastKey = -1;
      }
      m._uploaded = true;
    }

    function resolveSurfaceMat(m, s, skinIdx) {
      let tex = s.tex;
      let glowTex = s.glowTex;
      let animFps = s.animFps;
      let unlit = s.unlit;
      let nodraw = false;
      if (m.skins && skinIdx >= 0 && skinIdx < m.skins.length) {
        const ov = m.skins[skinIdx].map && (m.skins[skinIdx].map[s.name] || m.skins[skinIdx].map[s.shader]);
        if (ov) {
          if (ov.tex !== undefined) tex = ov.tex;
          if (ov.glowTex !== undefined) glowTex = ov.glowTex;
          if (ov.animFps !== undefined) animFps = ov.animFps;
          if (ov.unlit !== undefined) unlit = ov.unlit ? 1 : 0;
          if (ov.nodraw) nodraw = true;
        }
      }
      return { tex, glowTex, animFps, unlit, nodraw };
    }

    function getAtlasRect(t, tileIdx) {
      if (!t || t.count <= 1) return [0, 0, 1, 1];
      const k = ((tileIdx % t.count) + t.count) % t.count;
      const c = k % t.cols, r = Math.floor(k / t.cols);
      const cw = t.tileW + 2 * t.pad, ch = t.tileH + 2 * t.pad;
      return [(c * cw + t.pad) / t.w, (r * ch + t.pad) / t.h, t.tileW / t.w, t.tileH / t.h];
    }

    function computeSpriteTile(m, az, clip, tSec, speed, exactFrame) {
      const sm = clip.sprMode;
      if (!sm) return 0;
      let d = 0;
      if (sm.dirs > 1) {
        const sgn = m.turnSign || 1;
        const normAz = (((az * sgn) / (2 * Math.PI)) % 1 + 1) % 1;
        d = Math.round(normAz * sm.dirs) % sm.dirs;
      }
      let f = 0;
      if (sm.fpd > 1) {
        if (exactFrame !== null) f = Math.max(0, Math.min(sm.fpd - 1, Math.floor(exactFrame)));
        else f = Math.floor(tSec * speed * (sm.fps || clip.fps || 10.0)) % sm.fpd;
      }
      return sm.base + d * sm.fpd + f;
    }

    const matP = new Float32Array(16);
    const matV = new Float32Array(16);
    const matVP = new Float32Array(16);

    function defaultOrbitForModel(m, zoomMult) {
      ensureModelUploaded(m);
      return {
        az: m.az !== undefined ? m.az : (m.isSprite ? 0.0 : -0.58),
        el: m.el !== undefined ? m.el : (m.isSprite ? 0.10 : 0.24),
        dist: m.R * 2.55 * (zoomMult || 1.0),
        minDist: Math.max(4.0, m.R * 0.35),
        maxDist: Math.max(400.0, m.R * 8.5),
        pan: [0, 0, 0],
        povYaw: 0,
        povPitch: 0,
      };
    }

    function renderViewportScene(vp, tSec) {
      const m = vp.model;
      ensureModelUploaded(m);
      const clip = m.clips[vp.clipIdx % m.clips.length] || m.clips[0];
      const speed = vp.speed || 1.0;
      const exactFrame = vp.playing === false ? vp.manualFrame : null;

      let fa = 0, fb = 0, frac = 0.0;
      let sprTile = null;
      if (clip.sprMode) {
        sprTile = computeSpriteTile(m, vp.cam.az, clip, tSec, speed, exactFrame);
      } else if (exactFrame !== null) {
        const clp = Math.max(0, Math.min(m.nf - 1, exactFrame));
        fa = Math.floor(clp);
        fb = (fa + 1) % m.nf;
        frac = clp - fa;
      } else if (clip.count <= 1) {
        fa = clip.start; fb = clip.start;
      } else {
        const pos = ((tSec * speed * clip.fps) % clip.count + clip.count) % clip.count;
        const i0 = Math.floor(pos);
        const i1 = (i0 + 1) % clip.count;
        fa = clip.start + i0;
        fb = clip.start + i1;
        frac = pos - i0;
      }

      // 1. Opaque backdrop inside scissor rect (writes alpha = 1.0!)
      gl.disable(gl.BLEND);
      gl.disable(gl.DEPTH_TEST);
      gl.depthMask(false);
      gl.useProgram(pSky);
      const themeIdx = m.cat === 'raunchy' ? 1 : (m.cat === 'megaman' ? 2 : (m.cat === 'gore' ? 3 : 0));
      gl.uniform1i(uSky.uTheme, themeIdx);
      gl.bindVertexArray(quadVao);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      gl.depthMask(true);
      gl.enable(gl.DEPTH_TEST);
      gl.clear(gl.DEPTH_BUFFER_BIT);

      // 2. Camera Matrices
      let eye, tgt, offX, offY, offZ;
      const aspect = Math.max(0.25, vp.aspect || 1.33);
      if (vp.povMode && m.pov) {
        const yaw = vp.cam.povYaw || 0, pitch = vp.cam.povPitch || 0;
        const swayY = vp.playing !== false ? Math.sin(tSec * 2.3) * 0.22 : 0;
        const swayZ = vp.playing !== false ? Math.cos(tSec * 4.6) * 0.16 : 0;
        eye = [0, 0, 0];
        tgt = [100 * Math.cos(pitch) * Math.cos(yaw), 100 * Math.cos(pitch) * Math.sin(yaw), 100 * Math.sin(pitch)];
        offX = 0; offY = swayY; offZ = swayZ;
        const fovH = 90.0 * Math.PI / 180.0;
        const fovV = 2.0 * Math.atan(Math.tan(fovH * 0.5) / Math.max(1.1, aspect));
        mat4Persp(matP, fovV, aspect, 0.5, 650.0);
      } else {
        const pan = vp.cam.pan || [0, 0, 0];
        const baseZ = (m.bbox[0][2] + m.offset[2]) + m.size[2] * 0.48;
        tgt = [pan[0], pan[1], baseZ + pan[2]];
        eye = [
          tgt[0] + vp.cam.dist * Math.cos(vp.cam.el) * Math.cos(vp.cam.az),
          tgt[1] + vp.cam.dist * Math.cos(vp.cam.el) * Math.sin(vp.cam.az),
          tgt[2] + vp.cam.dist * Math.sin(vp.cam.el),
        ];
        offX = m.offset[0]; offY = m.offset[1]; offZ = m.offset[2];
        mat4Persp(matP, 0.60, aspect, Math.max(0.4, m.R * 0.02), Math.max(2600.0, m.R * 18.0));
      }
      mat4LookAt(matV, eye, tgt, [0, 0, 1]);
      mat4Mul(matVP, matP, matV);

      const rx = matV[0], ry = matV[4], rl = Math.hypot(rx, ry) || 1;
      const billRight = [rx / rl, ry / rl, 0];
      const billUp = [matV[1], matV[5], matV[9]];

      // 3. Floor Grid (preserve framebuffer alpha = 1.0 via blendFuncSeparate!)
      if (!(vp.povMode && m.pov)) {
        gl.enable(gl.BLEND);
        gl.blendFuncSeparate(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA, gl.ZERO, gl.ONE);
        gl.depthMask(false);
        gl.useProgram(pGround);
        gl.uniformMatrix4fv(uGround.uVP, false, matVP);
        gl.uniform1f(uGround.uSize, Math.max(180.0, m.R * 3.6));
        gl.uniform1f(uGround.uTime, (clip.lie || m.nf <= 1 || m.isSprite) ? 0.0 : tSec);
        gl.bindVertexArray(quadVao);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
        gl.depthMask(true);
        gl.disable(gl.BLEND);
      }

      // Helper to bind surface pose VAO
      function bindPose(s) {
        const sfa = s.nfGeom <= 1 ? 0 : fa % s.nfGeom;
        const sfb = s.nfGeom <= 1 ? 0 : fb % s.nfGeom;
        const sfrac = s.nfGeom <= 1 ? 0.0 : frac;
        gl.bindVertexArray(s.vao);
        const poseKey = sfa * 65536 + sfb;
        if (s._lastKey !== poseKey) {
          gl.bindBuffer(gl.ARRAY_BUFFER, s.bufPos);
          gl.vertexAttribPointer(0, 3, gl.SHORT, false, 8, sfa * s.nv * 8);
          gl.vertexAttribPointer(1, 3, gl.SHORT, false, 8, sfb * s.nv * 8);
          gl.bindBuffer(gl.ARRAY_BUFFER, s.bufNrm);
          gl.vertexAttribPointer(2, 3, gl.BYTE, true, 4, sfa * s.nv * 4);
          gl.vertexAttribPointer(3, 3, gl.BYTE, true, 4, sfb * s.nv * 4);
          s._lastKey = poseKey;
        }
        return sfrac;
      }

      // 4. Planar Ground Shadow (3D models in orbit view)
      if (!(vp.povMode && m.pov) && !m.isSprite && eye[2] > 2.0) {
        gl.enable(gl.BLEND);
        gl.blendFuncSeparate(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA, gl.ZERO, gl.ONE);
        gl.useProgram(pMesh);
        gl.uniformMatrix4fv(uMesh.uVP, false, matVP);
        gl.uniform3f(uMesh.uOffset, offX, offY, offZ);
        gl.uniform1i(uMesh.uShadowPass, 1);
        gl.uniform1i(uMesh.uAlphaTest, 0);
        gl.uniform4f(uMesh.uTileRect, 0, 0, 1, 1);
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, fallbackTex);
        gl.uniform1i(uMesh.uTex, 0);
        for (const s of m.surfaces) {
          if (s.additive || s.alphaBlend || s.billboard) continue;
          const ms = resolveSurfaceMat(m, s, vp.skinIdx);
          if (ms.nodraw) continue;
          const sfrac = bindPose(s);
          gl.uniform1f(uMesh.uLerp, sfrac);
          gl.uniform1f(uMesh.uPosScale, s.posScale);
          gl.uniform1i(uMesh.uBillboard, 0);
          gl.drawElements(gl.TRIANGLES, s.nt * 3, gl.UNSIGNED_SHORT, 0);
        }
        gl.disable(gl.BLEND);
      }

      // 5. Two-Pass Mesh Rendering (Pass 0 = Opaque/AlphaTest, Pass 1 = AlphaBlend/Additive)
      gl.useProgram(pMesh);
      gl.uniformMatrix4fv(uMesh.uVP, false, matVP);
      gl.uniform3f(uMesh.uOffset, offX, offY, offZ);
      gl.uniform3fv(uMesh.uBillRight, billRight);
      gl.uniform3fv(uMesh.uBillUp, billUp);
      gl.uniform3fv(uMesh.uEye, eye);
      gl.uniform1i(uMesh.uShadowPass, 0);
      gl.uniform1i(uMesh.uTex, 0);
      gl.uniform1i(uMesh.uGlowTex, 1);

      for (let pass = 0; pass < 2; pass++) {
        for (const s of m.surfaces) {
          const ms = resolveSurfaceMat(m, s, vp.skinIdx);
          if (ms.nodraw) continue;
          const isTrans = !!(s.additive || s.alphaBlend);
          if ((pass === 0 && isTrans) || (pass === 1 && !isTrans)) continue;

          if (pass === 0) {
            gl.disable(gl.BLEND);
            gl.depthMask(true);
          } else {
            gl.enable(gl.BLEND);
            gl.depthMask(false);
            if (s.additive) gl.blendFuncSeparate(gl.SRC_ALPHA, gl.ONE, gl.ZERO, gl.ONE);
            else gl.blendFuncSeparate(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA, gl.ZERO, gl.ONE);
          }

          const sfrac = bindPose(s);
          const tObj = PACK.textures[ms.tex];
          gl.activeTexture(gl.TEXTURE0);
          gl.bindTexture(gl.TEXTURE_2D, tObj ? tObj.glTex : fallbackTex);

          let rect = [0, 0, 1, 1];
          if (sprTile !== null && tObj && tObj.count > 1) {
            rect = getAtlasRect(tObj, sprTile);
          } else if (ms.animFps > 0 && tObj && tObj.count > 1) {
            const seqLen = s.animOrder ? s.animOrder.length : tObj.count;
            const step = Math.floor(tSec * speed * ms.animFps) % seqLen;
            rect = getAtlasRect(tObj, s.animOrder ? s.animOrder[step] : step);
          }
          gl.uniform4fv(uMesh.uTileRect, rect);
          gl.uniform1f(uMesh.uScrollV, s.scrollV ? (tSec * s.scrollV) % 1.0 : 0.0);

          const gObj = ms.glowTex >= 0 ? PACK.textures[ms.glowTex] : null;
          if (gObj) {
            gl.activeTexture(gl.TEXTURE1);
            gl.bindTexture(gl.TEXTURE_2D, gObj.glTex);
            gl.uniform1i(uMesh.uHasGlow, 1);
          } else {
            gl.uniform1i(uMesh.uHasGlow, 0);
          }

          gl.uniform1f(uMesh.uLerp, sfrac);
          gl.uniform1f(uMesh.uPosScale, s.posScale);
          gl.uniform1i(uMesh.uBillboard, (vp.povMode && m.pov) ? 0 : s.billboard);
          gl.uniform1f(uMesh.uMetallic, s.metallic);
          gl.uniform1f(uMesh.uRoughness, s.roughness);
          gl.uniform1f(uMesh.uSpec, s.spec);
          gl.uniform1i(uMesh.uUnlit, ms.unlit);
          gl.uniform1i(uMesh.uAlphaTest, s.alphaTest);
          gl.uniform1i(uMesh.uAlphaBlend, s.alphaBlend);
          gl.drawElements(gl.TRIANGLES, s.nt * 3, gl.UNSIGNED_SHORT, 0);
        }
      }
      gl.depthMask(true);
      gl.disable(gl.BLEND);

      // 6. Optional Wireframe Overlay
      if (vp.wire) {
        gl.enable(gl.BLEND);
        gl.blendFuncSeparate(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA, gl.ZERO, gl.ONE);
        gl.useProgram(pWire);
        gl.uniformMatrix4fv(uWire.uVP, false, matVP);
        gl.uniform3f(uWire.uOffset, offX, offY, offZ);
        gl.uniform3fv(uWire.uBillRight, billRight);
        gl.uniform3fv(uWire.uBillUp, billUp);
        for (const s of m.surfaces) {
          const ms = resolveSurfaceMat(m, s, vp.skinIdx);
          if (ms.nodraw) continue;
          const sfrac = bindPose(s);
          gl.uniform1f(uWire.uLerp, sfrac);
          gl.uniform1f(uWire.uPosScale, s.posScale);
          gl.uniform1i(uWire.uBillboard, (vp.povMode && m.pov) ? 0 : s.billboard);
          gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.ibEdges);
          gl.drawElements(gl.LINES, s.ne * 2, gl.UNSIGNED_SHORT, 0);
          gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.ibTris);
        }
        gl.disable(gl.BLEND);
      }
    }

    // ==================== INLINE VIEWPORT MOUNTING ====================
    const inlineViewports = [];

    function bindOrbitDragAndZoom(stageEl, vpObj, onInteract) {
      let dragging = 0, lx = 0, ly = 0;
      stageEl.addEventListener('contextmenu', (e) => e.preventDefault());
      stageEl.addEventListener('pointerdown', (e) => {
        if (e.target.closest('button, select, input, a')) return;
        dragging = (e.button === 2 || e.button === 1 || e.shiftKey) ? 2 : 1;
        lx = e.clientX; ly = e.clientY;
        stageEl.classList.add('dragging');
        try { stageEl.setPointerCapture(e.pointerId); } catch (_) {}
        if (onInteract) onInteract();
      });
      stageEl.addEventListener('pointermove', (e) => {
        if (!dragging) return;
        const dx = e.clientX - lx, dy = e.clientY - ly;
        lx = e.clientX; ly = e.clientY;
        if (vpObj.povMode && vpObj.model.pov) {
          vpObj.cam.povYaw = Math.max(-0.6, Math.min(0.6, (vpObj.cam.povYaw || 0) - dx * 0.0035));
          vpObj.cam.povPitch = Math.max(-0.45, Math.min(0.45, (vpObj.cam.povPitch || 0) - dy * 0.0035));
          return;
        }
        if (dragging === 1) {
          vpObj.cam.az -= dx * 0.0095;
          vpObj.cam.el = Math.max(-1.20, Math.min(1.42, vpObj.cam.el + dy * 0.008));
        } else {
          const sc = vpObj.cam.dist * 0.0015;
          const rx = -Math.sin(vpObj.cam.az), ry = Math.cos(vpObj.cam.az);
          vpObj.cam.pan[0] -= rx * dx * sc;
          vpObj.cam.pan[1] -= ry * dx * sc;
          vpObj.cam.pan[2] += dy * sc;
        }
      });
      const stop = () => { dragging = 0; stageEl.classList.remove('dragging'); };
      stageEl.addEventListener('pointerup', stop);
      stageEl.addEventListener('pointercancel', stop);

      stageEl.addEventListener('wheel', (e) => {
        e.preventDefault();
        if (vpObj.povMode && vpObj.model.pov) {
          vpObj.povMode = false;
          if (vpObj.syncUi) vpObj.syncUi();
        }
        vpObj.cam.dist = Math.max(vpObj.cam.minDist, Math.min(vpObj.cam.maxDist, vpObj.cam.dist * Math.exp(e.deltaY * 0.0012)));
      }, { passive: false });
    }

    function mountStageElement(stageEl) {
      if (stageEl._bqMounted) return;
      const mid = stageEl.getAttribute('data-model');
      const m = modelById[mid];
      if (!m) return;
      stageEl._bqMounted = true;

      const initSkin = parseInt(stageEl.getAttribute('data-skin') || '0', 10) || 0;
      const initClip = parseInt(stageEl.getAttribute('data-clip') || '0', 10) || 0;
      const initPovAttr = stageEl.getAttribute('data-pov');
      const initPov = initPovAttr !== null ? initPovAttr === '1' : !!m.defaultPov;
      const initSpinAttr = stageEl.getAttribute('data-spin');
      const initSpin = initSpinAttr !== null ? initSpinAttr !== '0' : !initPov;
      const zoomMult = parseFloat(stageEl.getAttribute('data-zoom') || '1.0') || 1.0;

      const vp = {
        el: stageEl,
        model: m,
        cam: defaultOrbitForModel(m, zoomMult),
        clipIdx: initClip % m.clips.length,
        skinIdx: (m.skins && m.skins.length) ? (initSkin % m.skins.length) : 0,
        povMode: initPov,
        spin: initSpin,
        wire: false,
        playing: true,
        speed: 1.0,
        aspect: 1.33,
      };

      // Build clean retro mini-HUD & interactive controls right inside .vp-stage!
      const topHud = document.createElement('div');
      topHud.className = 'vp-overlay-top';
      const badgeEl = document.createElement('span');
      badgeEl.className = 'vp-badge';
      const hintEl = document.createElement('span');
      hintEl.className = 'vp-hint';
      hintEl.textContent = m.turnDirs > 1 ? `🖱 Drag ${m.turnDirs}-Dir · Wheel Zoom` : '🖱 Drag 360° · Wheel Zoom';
      topHud.appendChild(badgeEl);
      topHud.appendChild(hintEl);

      const bar = document.createElement('div');
      bar.className = 'vp-toolbar';
      const grpL = document.createElement('div');
      grpL.className = 'vp-btn-group';
      const grpR = document.createElement('div');
      grpR.className = 'vp-btn-group';

      const btnSpin = document.createElement('button');
      btnSpin.type = 'button';
      btnSpin.className = 'vp-btn';
      btnSpin.textContent = '🔄 Spin';
      btnSpin.onclick = () => { vp.spin = !vp.spin; syncUi(); };
      grpL.appendChild(btnSpin);

      let btnClip = null;
      if (m.clips.length > 1) {
        btnClip = document.createElement('button');
        btnClip.type = 'button';
        btnClip.className = 'vp-btn';
        btnClip.onclick = () => {
          vp.clipIdx = (vp.clipIdx + 1) % m.clips.length;
          syncUi();
        };
        grpL.appendChild(btnClip);
      }

      let btnSkin = null;
      if (m.skins && m.skins.length > 1) {
        btnSkin = document.createElement('button');
        btnSkin.type = 'button';
        btnSkin.className = 'vp-btn skin-accent';
        btnSkin.onclick = () => {
          vp.skinIdx = (vp.skinIdx + 1) % m.skins.length;
          syncUi();
        };
        grpL.appendChild(btnSkin);
      }

      let btnPov = null;
      if (m.pov) {
        btnPov = document.createElement('button');
        btnPov.type = 'button';
        btnPov.className = 'vp-btn';
        btnPov.textContent = '👁 POV';
        btnPov.onclick = () => {
          vp.povMode = !vp.povMode;
          if (!vp.povMode && m.defaultPov) vp.cam.dist = m.R * 2.4;
          syncUi();
        };
        grpL.appendChild(btnPov);
      }

      const btnZoomIn = document.createElement('button');
      btnZoomIn.type = 'button';
      btnZoomIn.className = 'vp-btn';
      btnZoomIn.textContent = '➕';
      btnZoomIn.title = 'Zoom In';
      btnZoomIn.onclick = () => {
        vp.povMode = false;
        vp.cam.dist = Math.max(vp.cam.minDist, vp.cam.dist * 0.78);
        syncUi();
      };

      const btnZoomOut = document.createElement('button');
      btnZoomOut.type = 'button';
      btnZoomOut.className = 'vp-btn';
      btnZoomOut.textContent = '➖';
      btnZoomOut.title = 'Zoom Out';
      btnZoomOut.onclick = () => {
        vp.povMode = false;
        vp.cam.dist = Math.min(vp.cam.maxDist, vp.cam.dist * 1.28);
        syncUi();
      };

      const btnFull = document.createElement('button');
      btnFull.type = 'button';
      btnFull.className = 'vp-btn full-accent';
      btnFull.textContent = '⛶ FULL 3D';
      btnFull.onclick = () => openHolodeckModal(m.id, vp.skinIdx, vp.clipIdx, vp.povMode);

      grpR.appendChild(btnZoomIn);
      grpR.appendChild(btnZoomOut);
      grpR.appendChild(btnFull);
      bar.appendChild(grpL);
      bar.appendChild(grpR);

      stageEl.appendChild(topHud);
      stageEl.appendChild(bar);

      function syncUi() {
        const c = m.clips[vp.clipIdx];
        const sk = (m.skins && m.skins[vp.skinIdx]) ? ` · ${m.skins[vp.skinIdx].label}` : '';
        badgeEl.textContent = `${c ? c.label : m.badge}${sk}`;
        btnSpin.classList.toggle('active', vp.spin && !vp.povMode);
        if (btnClip) btnClip.textContent = `🎬 Anim (${vp.clipIdx + 1}/${m.clips.length})`;
        if (btnSkin) btnSkin.textContent = `🎨 Skin (${vp.skinIdx + 1}/${m.skins.length})`;
        if (btnPov) btnPov.classList.toggle('active', vp.povMode);
      }
      vp.syncUi = syncUi;
      syncUi();

      bindOrbitDragAndZoom(stageEl, vp, () => {
        vp.spin = false;
        syncUi();
      });

      inlineViewports.push(vp);
    }

    function scanAndMountStages(root) {
      (root || document).querySelectorAll('.vp-stage[data-model]').forEach(mountStageElement);
    }
    scanAndMountStages(document);

    // ==================== HOLODECK SHOWROOM FILTERABLE GRID ====================
    const holoShowroomWrap = $('holodeck-showroom-grid');
    let curShowroomCat = 'featured';
    const FEATURED_12 = [
      'pinklady_spr', 'v_wewcannon', 'wheelman_dance_spr',
      'megaman', 'pickle_diva', 'pink_supercar',
    ];

    function renderShowroomCards(cat) {
      if (!holoShowroomWrap) return;
      curShowroomCat = cat;
      // Remove old dynamically mounted showroom viewports from inlineViewports
      for (let i = inlineViewports.length - 1; i >= 0; i--) {
        if (holoShowroomWrap.contains(inlineViewports[i].el)) {
          inlineViewports.splice(i, 1);
        }
      }
      holoShowroomWrap.innerHTML = '';

      let list;
      if (cat === 'featured') {
        list = FEATURED_12.map((id) => modelById[id]).filter(Boolean);
      } else if (cat === 'all') {
        list = models;
      } else {
        list = models.filter((m) => m.cat === cat);
      }

      const themeByCat = {
        raunchy: 'pink',
        wheelman: 'silver',
        megaman: 'cyan',
        gore: 'blood',
        arsenal: 'lime',
      };

      for (const m of list) {
        const card = document.createElement('div');
        card.className = `vp-card ${themeByCat[m.cat] || ''}`;
        card.innerHTML = `
          <div class="vp-hdr">
            <span class="vp-hdr-title" title="${m.title}">${m.title}</span>
            <span class="vp-fmt-pill">${m.fmt}</span>
          </div>
          <div class="vp-stage short" data-model="${m.id}"></div>
          <div class="vp-foot">${m.desc}</div>
        `;
        holoShowroomWrap.appendChild(card);
      }
      scanAndMountStages(holoShowroomWrap);

      document.querySelectorAll('[data-holo-cat]').forEach((b) => {
        b.classList.toggle('active', b.getAttribute('data-holo-cat') === cat);
      });
    }

    document.querySelectorAll('[data-holo-cat]').forEach((btn) => {
      btn.addEventListener('click', () => renderShowroomCards(btn.getAttribute('data-holo-cat')));
    });
    renderShowroomCards('featured');

    // ==================== FULLSCREEN 3D & SPRITE HOLODECK MODAL ====================
    const holoModal = $('holodeck-modal');
    const holoStage = $('holodeck-stage');
    const holo2dCanvas = $('holo-2d-canvas');
    const holo2dCtx = holo2dCanvas ? holo2dCanvas.getContext('2d') : null;

    const modalVp = {
      el: holoStage,
      model: models[0],
      cam: defaultOrbitForModel(models[0], 0.92),
      clipIdx: 0,
      skinIdx: 0,
      povMode: false,
      spin: true,
      wire: false,
      pix2d: false,
      playing: true,
      manualFrame: 0,
      speed: 1.0,
      aspect: 1.6,
    };

    if (holoStage) {
      bindOrbitDragAndZoom(holoStage, modalVp, () => {
        modalVp.spin = false;
        syncHolodeckModalUi();
      });
    }

    function populateHolodeckSidebar(filterText) {
      const side = $('holo-sidebar-list');
      if (!side) return;
      const q = (filterText || '').trim().toLowerCase();
      side.innerHTML = '';
      for (const m of models) {
        if (q && !(`${m.title} ${m.badge} ${m.cat} ${m.file}`.toLowerCase().includes(q))) continue;
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'holo-item' + (m.id === modalVp.model.id ? ' active' : '');
        b.innerHTML = `<b>${m.title}</b><br><span style="color:#9ad7ff;font-size:10px">${m.fmt} · ${m.badge}</span>`;
        b.onclick = () => openHolodeckModal(m.id, 0, 0, !!m.defaultPov);
        side.appendChild(b);
      }
    }

    function syncHolodeckModalUi() {
      const m = modalVp.model;
      if (!m) return;
      if ($('holo-title')) $('holo-title').textContent = m.title;
      if ($('holo-meta')) {
        const triStr = m.turnDirs > 1 ? `${m.turnDirs} Turnaround Angles · ${m.nf} Sprites` : `${m.nt.toLocaleString()} Tris · ${m.nv.toLocaleString()} Verts · ${m.nf}f`;
        $('holo-meta').textContent = `${m.fmt} · ${m.file} · ${triStr}`;
      }
      if ($('holo-desc')) $('holo-desc').textContent = m.desc;

      const clipSel = $('holo-clip-sel');
      if (clipSel) {
        clipSel.innerHTML = '';
        m.clips.forEach((c, idx) => {
          const opt = document.createElement('option');
          opt.value = idx;
          opt.textContent = c.label;
          if (idx === modalVp.clipIdx) opt.selected = true;
          clipSel.appendChild(opt);
        });
      }

      const skinWrap = $('holo-skin-btns');
      if (skinWrap) {
        skinWrap.innerHTML = '';
        if (m.skins && m.skins.length > 1) {
          m.skins.forEach((sk, idx) => {
            const sb = document.createElement('button');
            sb.type = 'button';
            sb.className = 'win98-btn' + (idx === modalVp.skinIdx ? ' active' : '');
            sb.textContent = sk.label;
            sb.onclick = () => { modalVp.skinIdx = idx; syncHolodeckModalUi(); };
            skinWrap.appendChild(sb);
          });
        }
      }

      if ($('holo-btn-spin')) $('holo-btn-spin').classList.toggle('active', modalVp.spin);
      if ($('holo-btn-wire')) $('holo-btn-wire').classList.toggle('active', modalVp.wire);
      if ($('holo-btn-play')) $('holo-btn-play').textContent = modalVp.playing ? '⏸ Pause' : '▶ Play';
      if ($('holo-btn-pov')) {
        $('holo-btn-pov').style.display = m.pov ? 'inline-flex' : 'none';
        $('holo-btn-pov').classList.toggle('active', modalVp.povMode);
      }
      const can2d = !!(m.isSprite || m.fmt.includes('2D'));
      if ($('holo-btn-2d')) {
        $('holo-btn-2d').style.display = can2d ? 'inline-flex' : 'none';
        $('holo-btn-2d').classList.toggle('active', modalVp.pix2d && can2d);
      }
      if (holoStage) holoStage.classList.toggle('pix2d', modalVp.pix2d && can2d);

      const scrub = $('holo-scrub');
      if (scrub) {
        const c = m.clips[modalVp.clipIdx] || m.clips[0];
        const maxF = c.sprMode ? Math.max(0, c.sprMode.fpd - 1) : Math.max(0, m.nf - 1);
        scrub.max = String(maxF);
      }
    }

    function openHolodeckModal(modelId, skinIdx, clipIdx, povMode) {
      const m = modelById[modelId] || models[0];
      modalVp.model = m;
      modalVp.cam = defaultOrbitForModel(m, 0.90);
      modalVp.skinIdx = skinIdx || 0;
      modalVp.clipIdx = clipIdx || 0;
      modalVp.povMode = povMode !== undefined ? !!povMode : !!m.defaultPov;
      modalVp.spin = !modalVp.povMode;
      modalVp.pix2d = false;
      modalVp.playing = true;
      if (holoModal) holoModal.classList.add('open');
      document.body.classList.add('holodeck-open');
      populateHolodeckSidebar($('holo-search') ? $('holo-search').value : '');
      syncHolodeckModalUi();
    }
    window.openHolodeckModal = openHolodeckModal;

    function closeHolodeckModal() {
      if (holoModal) holoModal.classList.remove('open');
      document.body.classList.remove('holodeck-open');
    }
    window.closeHolodeckModal = closeHolodeckModal;

    if ($('holo-close')) $('holo-close').onclick = closeHolodeckModal;
    if ($('holo-search')) $('holo-search').oninput = (e) => populateHolodeckSidebar(e.target.value);
    if ($('holo-clip-sel')) {
      $('holo-clip-sel').onchange = (e) => {
        modalVp.clipIdx = parseInt(e.target.value, 10) || 0;
        syncHolodeckModalUi();
      };
    }
    if ($('holo-btn-spin')) $('holo-btn-spin').onclick = () => { modalVp.spin = !modalVp.spin; syncHolodeckModalUi(); };
    if ($('holo-btn-wire')) $('holo-btn-wire').onclick = () => { modalVp.wire = !modalVp.wire; syncHolodeckModalUi(); };
    if ($('holo-btn-pov')) $('holo-btn-pov').onclick = () => { modalVp.povMode = !modalVp.povMode; syncHolodeckModalUi(); };
    if ($('holo-btn-2d')) $('holo-btn-2d').onclick = () => { modalVp.pix2d = !modalVp.pix2d; syncHolodeckModalUi(); };
    if ($('holo-btn-play')) $('holo-btn-play').onclick = () => { modalVp.playing = !modalVp.playing; syncHolodeckModalUi(); };
    if ($('holo-btn-reset')) {
      $('holo-btn-reset').onclick = () => {
        modalVp.cam = defaultOrbitForModel(modalVp.model, 0.90);
        modalVp.spin = !modalVp.povMode;
        syncHolodeckModalUi();
      };
    }
    if ($('holo-scrub')) {
      $('holo-scrub').oninput = (e) => {
        modalVp.playing = false;
        modalVp.manualFrame = parseFloat(e.target.value) || 0;
        syncHolodeckModalUi();
      };
    }

    function draw2DSpritePreview(vp, tSec) {
      if (!holo2dCtx || !holo2dCanvas) return;
      const m = vp.model;
      const s0 = m.surfaces[0];
      const ms = resolveSurfaceMat(m, s0, vp.skinIdx);
      const tObj = PACK.textures[ms.tex];
      const img = texImages[ms.tex];
      if (!tObj || !img || !tObj._loaded) return;
      const clip = m.clips[vp.clipIdx] || m.clips[0];
      let tile = 0;
      if (clip.sprMode) {
        tile = computeSpriteTile(m, vp.cam.az, clip, tSec, vp.speed, vp.playing ? null : vp.manualFrame);
      } else if (ms.animFps > 0) {
        tile = Math.floor(tSec * ms.animFps) % tObj.count;
      }
      const k = ((tile % tObj.count) + tObj.count) % tObj.count;
      const c = k % tObj.cols, r = Math.floor(k / tObj.cols);
      const sx = c * (tObj.tileW + 2 * tObj.pad) + tObj.pad;
      const sy = r * (tObj.tileH + 2 * tObj.pad) + tObj.pad;
      if (holo2dCanvas.width !== tObj.tileW || holo2dCanvas.height !== tObj.tileH) {
        holo2dCanvas.width = tObj.tileW;
        holo2dCanvas.height = tObj.tileH;
      }
      holo2dCtx.clearRect(0, 0, tObj.tileW, tObj.tileH);
      holo2dCtx.imageSmoothingEnabled = false;
      holo2dCtx.drawImage(img, sx, sy, tObj.tileW, tObj.tileH, 0, 0, tObj.tileW, tObj.tileH);
    }

    // ==================== 60FPS SCISSORED RENDER LOOP ====================
    let lastTs = performance.now();
    function frame(now) {
      const dt = Math.min(0.08, (now - lastTs) * 0.001);
      lastTs = now;
      const tSec = now * 0.001;

      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const cw = Math.floor(window.innerWidth * dpr);
      const ch = Math.floor(window.innerHeight * dpr);
      if (canvas.width !== cw || canvas.height !== ch) {
        canvas.width = cw;
        canvas.height = ch;
      }

      gl.disable(gl.SCISSOR_TEST);
      gl.viewport(0, 0, cw, ch);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      const lbOpen = $('lightbox-modal') && $('lightbox-modal').classList.contains('open');
      const holoOpen = holoModal && holoModal.classList.contains('open');

      if (!lbOpen) {
        gl.enable(gl.SCISSOR_TEST);
        if (holoOpen && holoStage) {
          if (modalVp.spin && !modalVp.povMode) modalVp.cam.az += dt * 0.62;
          if (modalVp.pix2d && (modalVp.model.isSprite || modalVp.model.fmt.includes('2D'))) {
            draw2DSpritePreview(modalVp, tSec);
          } else {
            const r = holoStage.getBoundingClientRect();
            if (r.width > 12 && r.height > 12) {
              const vx = Math.round(r.left * dpr);
              const vy = Math.round((window.innerHeight - r.bottom) * dpr);
              const vw = Math.round(r.width * dpr);
              const vh = Math.round(r.height * dpr);
              modalVp.aspect = vw / Math.max(1, vh);
              gl.viewport(vx, vy, vw, vh);
              gl.scissor(vx, vy, vw, vh);
              renderViewportScene(modalVp, tSec);
            }
          }
        } else {
          const winH = window.innerHeight;
          const winW = window.innerWidth;
          for (const vp of inlineViewports) {
            const r = vp.el.getBoundingClientRect();
            if (r.bottom < 2 || r.top > winH - 2 || r.right < 2 || r.left > winW - 2) continue;
            if (r.width < 16 || r.height < 16) continue;
            if (vp.spin && !vp.povMode) vp.cam.az += dt * 0.58;

            const vx = Math.round(r.left * dpr);
            const vy = Math.round((winH - r.bottom) * dpr);
            const vw = Math.round(r.width * dpr);
            const vh = Math.round(r.height * dpr);
            vp.aspect = vw / Math.max(1, vh);
            gl.viewport(vx, vy, vw, vh);
            gl.scissor(vx, vy, vw, vh);
            renderViewportScene(vp, tSec);
          }
        }
        gl.disable(gl.SCISSOR_TEST);
      }

      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  // ==================== DOM READY BOOTSTRAP ====================
  document.addEventListener('DOMContentLoaded', () => {
    const btnCopyIp = $('btn-copy-connect');
    if (btnCopyIp) {
      btnCopyIp.addEventListener('click', () => {
        const cmd = 'connect 72.62.241.93:26000';
        if (navigator.clipboard) navigator.clipboard.writeText(cmd).catch(() => {});
        btnCopyIp.textContent = 'Copied!';
        setTimeout(() => { btnCopyIp.textContent = 'Copy'; }, 1800);
      });
    }

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeLightbox();
        if (window.closeHolodeckModal) window.closeHolodeckModal();
      } else if ($('lightbox-modal') && $('lightbox-modal').classList.contains('open')) {
        if (e.key === 'ArrowLeft') stepLightbox(-1);
        else if (e.key === 'ArrowRight') stepLightbox(+1);
      }
    });

    initLightbox();
    initUnderdogCalc();
    initWebGLViewer().catch((err) => console.error('WebGL viewer init error:', err));
  });
})();
