/* BAKOQUAKE page: the pixel-art Bakersfield Sign, hit counter, copy button, download sparks. */
(function () {
  'use strict';

  const forceMotion = /[?&]motion=on/.test(location.search);   // test switch: ignore the OS reduced-motion setting
  const calm = !forceMotion && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (calm) document.documentElement.classList.add('calm');

  // ---------------------------------------------------------------- THE BAKERSFIELD SIGN, AS 1996 PIXEL ART
  // The sign is drawn as an SVG, rendered tiny, posterised and scaled up with no smoothing, so it looks like a Quake texture.
  const Q = (p0, c, p1, t) => (1 - t) * (1 - t) * p0 + 2 * (1 - t) * t * c + t * t * p1;

  function signSVG(phase) {
    const tower = (x) => `
      <g transform="translate(${x},0)">
        <rect x="72" y="14" width="6" height="36" fill="#7A5A2A"/><circle cx="75" cy="14" r="8" fill="#E2B13C"/>
        <polygon points="75,46 150,142 0,142" fill="#8F3E2B"/><polygon points="75,46 0,142 75,142" fill="#B2573C"/>
        <path d="M18 118H132M34 96H116M50 74H100" stroke="#00000040" stroke-width="3"/>
        <rect x="-6" y="140" width="162" height="20" rx="3" fill="#D8BD8A"/>
        <rect x="12" y="160" width="126" height="232" fill="#E6D3A8"/><rect x="108" y="160" width="30" height="232" fill="#00000030"/>
        <rect x="4" y="248" width="142" height="20" rx="2" fill="#C7A56D"/>
        <circle cx="75" cy="212" r="31" fill="#FFF3D2" stroke="#13204D" stroke-width="6"/>
        <circle cx="75" cy="212" r="19" fill="#13204D"/><circle cx="75" cy="212" r="7" fill="#F4C21E"/>
        <rect x="0" y="388" width="150" height="32" fill="#CBB07C"/>
        <path d="M50 388V342a25 25 0 0 1 50 0V388Z" fill="#2A1D18" stroke="#C7A56D" stroke-width="5"/>
      </g>`;
    let bulbs = '';
    for (let k = 0; k <= 22; k++) {
      const t = 0.1 + (0.8 * k) / 22;
      const x = Q(100, 500, 900, t);
      const on = (k + phase) % 3 === 0;
      const fill = on ? '#FFF3B0' : '#7A5F14';
      bulbs += `<circle cx="${x.toFixed(1)}" cy="${(Q(190, 20, 190, t) - 9).toFixed(1)}" r="8" fill="${fill}"/>`;
      bulbs += `<circle cx="${x.toFixed(1)}" cy="${(Q(280, 110, 280, t) + 9).toFixed(1)}" r="8" fill="${fill}"/>`;
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 420" width="1000" height="420">
      <defs><linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FBD84A"/><stop offset="1" stop-color="#E8AE12"/></linearGradient>
      <path id="p" d="M100 262Q500 92 900 262"/></defs>
      <path d="M100 190Q500 20 900 190V280Q500 110 100 280Z" fill="url(#b)" stroke="#9A6E00" stroke-width="5"/>
      <path d="M100 204Q500 34 900 204M100 268Q500 98 900 268" fill="none" stroke="#C28F0A" stroke-width="4"/>
      ${tower(40)}${tower(810)}
      <text font-family="Arial Black, Impact, Arial, sans-serif" font-weight="900" font-size="68" text-anchor="middle" letter-spacing="9"
            fill="#13204D" stroke="#DCE8FF" stroke-width="5" paint-order="stroke" stroke-linejoin="round">
        <textPath href="#p" startOffset="50%">BAKERSFIELD</textPath></text>
      ${bulbs}</svg>`;
  }

  // draw an SVG string into a small canvas, then crush the palette a little (Quake had 256 colours, after all)
  function rasterise(svg, w, h) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const c = document.createElement('canvas'); c.width = w; c.height = h;
        const x = c.getContext('2d', { willReadFrequently: true });
        x.imageSmoothingEnabled = true; x.drawImage(img, 0, 0, w, h);
        const d = x.getImageData(0, 0, w, h), px = d.data;
        for (let i = 0; i < px.length; i += 4) {
          px[i] = Math.round(px[i] / 36) * 36; px[i + 1] = Math.round(px[i + 1] / 36) * 36; px[i + 2] = Math.round(px[i + 2] / 36) * 36;
          px[i + 3] = px[i + 3] > 110 ? 255 : 0;
        }
        x.putImageData(d, 0, 0);
        resolve(c);
      };
      img.onerror = () => resolve(null);
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    });
  }

  async function mountLogos() {
    const hosts = document.querySelectorAll('[data-logo]');
    for (const host of hosts) {
      const hero = host.getAttribute('data-logo') === 'hero';
      const w = hero ? 280 : 160, h = Math.round(w * 0.42);
      const frames = await Promise.all([0, 1, 2].map((p) => rasterise(signSVG(p), w, h)));
      if (!frames[0]) continue;
      const out = document.createElement('canvas'); out.width = w; out.height = h;
      const ctx = out.getContext('2d'); ctx.imageSmoothingEnabled = false;
      host.appendChild(out);
      let f = 0;
      const draw = () => { ctx.clearRect(0, 0, w, h); ctx.drawImage(frames[f % 3], 0, 0); f++; };
      draw();
      if (!calm) setInterval(draw, 420);   // the bulbs chase, at a 1996 frame rate
    }
  }

  // ---------------------------------------------------------------- PAGE EXTRAS
  function hitCounter() {
    const el = document.getElementById('odo');
    if (!el) return;
    let n = 1;
    try { n = (parseInt(localStorage.getItem('bq_visits'), 10) || 0) + 1; localStorage.setItem('bq_visits', String(n)); } catch (e) { /* storage blocked */ }
    const s = String(n).padStart(6, '0');
    el.innerHTML = s.split('').map((d) => `<i>${d}</i>`).join('');
  }

  function copyButtons() {
    document.querySelectorAll('[data-copy]').forEach((b) => b.addEventListener('click', () => {
      const text = b.dataset.copy;
      const done = () => { const old = b.textContent; b.textContent = 'Copied!'; setTimeout(() => { b.textContent = old; }, 1800); };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, done);
      else { const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (e) { /* ignore */ } ta.remove(); done(); }
    }));
  }

  function downloadFx() {
    document.querySelectorAll('a[download]').forEach((a) => a.addEventListener('click', (e) => {
      if (calm) return;
      const x = e.clientX || a.getBoundingClientRect().left + 40, y = e.clientY || a.getBoundingClientRect().top + 20;
      for (let i = 0; i < 28; i++) {
        const s = document.createElement('span');
        s.className = 'sparkle';
        const ang = Math.random() * Math.PI * 2, d = 50 + Math.random() * 150;
        s.style.cssText = `left:${x}px;top:${y}px;--dx:${Math.cos(ang) * d}px;--dy:${Math.sin(ang) * d - 30}px;background:${['#FFFF00', '#FFFFFF', '#C0C0C0', '#FF813F'][i % 4]}`;
        document.body.appendChild(s);
        setTimeout(() => s.remove(), 900);
      }
      a.classList.add('go'); setTimeout(() => a.classList.remove('go'), 500);
    }));
  }

  function init() {
    mountLogos();
    hitCounter(); copyButtons(); downloadFx();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
