// Dev overlay for the browser viewer: shows where you are, for screen recordings that someone else has to read later.
// A separate file so edits to the viewer and the map generators do not collide with it. It needs window.__viewer
// (THREE, meta, pl, world, scene, renderer, tick) from web_viewer_index.html and adds its own CSS, panel and button.
//   `  (backquote) or the Dev info button, or ?dev=1   show / hide the panel
//   M                                                 drop a numbered mark (big banner on screen; "Copy marks" lists them)
// Panel: nearest named spot, position in map feet (the generators' frame: make_bklan.py / make_orcom.py coordinates),
// facing, a top-down map with a red arrow for you, and the build stamp of the map so a recording can be matched to the
// version of the map it was made on.
const css = `
#dev { position: fixed; top: 58px; right: 10px; width: 280px; background: rgba(0,0,0,.82); color: #fff; border: 2px solid #ffd24a;
       border-radius: 8px; padding: 10px 12px; font: 600 17px/1.35 ui-monospace, Consolas, monospace; display: none; z-index: 5; }
#dev.on { display: block; }
#dev .near { color: #ffd24a; font-size: 18px; margin-bottom: 4px; }
#dev .dim { color: #bbb; font-weight: 400; font-size: 13px; }
#dev canvas { display: block; width: 256px; height: 256px; margin: 8px 0 6px; background: #223; border-radius: 4px; }
#dev button { font-size: 13px; padding: 4px 8px; margin-right: 6px; }
#mark { position: fixed; top: 38%; left: 50%; transform: translateX(-50%); background: #ffd24a; color: #000; padding: 10px 22px;
        border-radius: 10px; font: 800 34px ui-monospace, Consolas, monospace; display: none; text-align: center; z-index: 5; }
#mark small { display: block; font: 600 16px ui-monospace, Consolas, monospace; }`;

function start(V) {
  const { THREE, meta, pl, world, scene, renderer } = V;
  const $ = (id) => document.getElementById(id);
  document.head.insertAdjacentHTML("beforeend", "<style>" + css + "</style>");
  document.body.insertAdjacentHTML("beforeend",
    `<div id="dev"><div class="near" id="dnear"></div><div id="dpos"></div><div id="dface"></div>
     <canvas id="dmap" width="256" height="256"></canvas>
     <div class="dim">\` hides this &middot; M drops a numbered mark</div>
     <div style="margin-top:6px"><button id="dcopy">Copy marks</button><span class="dim" id="dcount"></span></div>
     <div class="dim" id="dbuild" style="margin-top:4px"></div></div><div id="mark"></div>`);
  const bar = $("bar");
  if (bar) { const b = document.createElement("button"); b.id = "devbtn"; b.textContent = "Dev info"; b.title = "` key"; bar.appendChild(b); b.onclick = () => setDev(!dev.on); }

  const dev = { on: false, marks: [], mm: null };
  const FRAME = meta.frame || [0, 0];
  const ftOf = (o) => [o[0] / 12 + FRAME[0], o[1] / 12 + FRAME[1], o[2] / 12];
  const f1 = (v) => (v >= 0 ? " " : "") + v.toFixed(1);
  const tStart = performance.now();
  $("dbuild").textContent = meta.built ? "map built " + meta.built : "";

  function nearestSpot(o) {
    let best = null, bd = 1e12;
    for (const s of meta.spots) { const d = Math.hypot(s.pos[0] - o[0], s.pos[1] - o[1]); if (d < bd) { bd = d; best = s; } }
    return { name: best.name, ft: bd / 12 };
  }
  const CARD = ["E", "NE", "N", "NW", "W", "SW", "S", "SE"];     // map axes: +x = E, +y = N (the real compass is about 16 deg off)
  function faceText() {
    const yaw = ((pl.yaw % 360) + 360) % 360;
    return "facing map-" + CARD[Math.round(yaw / 45) % 8] + "  yaw " + yaw.toFixed(0) + "  pitch " + pl.pitch.toFixed(0);
  }

  function buildMinimap() {
    const box = new THREE.Box3().setFromObject(world);
    const cx = (box.min.x + box.max.x) / 2, cz = (box.min.z + box.max.z) / 2;
    const half = (Math.max(box.max.x - box.min.x, box.max.z - box.min.z) / 2) * 1.02;
    const N = 1024, rt = new THREE.WebGLRenderTarget(N, N);
    const cam = new THREE.OrthographicCamera(-half, half, half, -half, 1, 100000);
    cam.up.set(0, 0, -1);                                         // screen up = Quake +y
    cam.position.set(cx, 50000, cz);
    cam.lookAt(cx, 0, cz);
    const bg = scene.background; scene.background = new THREE.Color(0x202838);
    renderer.setRenderTarget(rt); renderer.render(scene, cam); renderer.setRenderTarget(null);
    scene.background = bg;
    const px = new Uint8Array(N * N * 4);
    renderer.readRenderTargetPixels(rt, 0, 0, N, N, px);
    if (!px.some((v) => v)) { rt.dispose(); throw new Error("empty render"); }
    const base = document.createElement("canvas"); base.width = base.height = N;
    const ctx = base.getContext("2d"), img = ctx.createImageData(N, N);
    for (let y = 0; y < N; y++) img.data.set(px.subarray((N - 1 - y) * N * 4, (N - y) * N * 4), y * N * 4);   // GL rows run bottom-up
    ctx.putImageData(img, 0, 0);
    rt.dispose();
    dev.mm = { base, cx, cz, half };
  }
  const mmXY = (o) => [((o[0] - dev.mm.cx) / dev.mm.half) * 128 + 128, ((-o[1] - dev.mm.cz) / dev.mm.half) * 128 + 128];
  function drawMinimap() {
    const c = $("dmap").getContext("2d");
    c.drawImage(dev.mm.base, 0, 0, 256, 256);
    c.font = "bold 12px Consolas, monospace";
    for (const mk of dev.marks) {
      const [x, y] = mmXY(mk.o);
      c.fillStyle = "#ffd24a"; c.beginPath(); c.arc(x, y, 5, 0, 7); c.fill();
      c.fillStyle = "#fff"; c.strokeStyle = "#000"; c.lineWidth = 3; c.strokeText(mk.n, x + 6, y - 4); c.fillText(mk.n, x + 6, y - 4);
    }
    const [x, y] = mmXY(pl.o), a = (pl.yaw * Math.PI) / 180;
    c.strokeStyle = "#ff3030"; c.fillStyle = "#ff3030"; c.lineWidth = 3;
    c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(a) * 16, y - Math.sin(a) * 16); c.stroke();    // view direction
    c.beginPath(); c.arc(x, y, 5, 0, 7); c.fill();
    c.strokeStyle = "#fff"; c.lineWidth = 1.5; c.stroke();
  }

  function update() {
    if (!dev.on) return;
    maybeMinimap();
    const f = ftOf(pl.o), n = nearestSpot(pl.o);
    $("dnear").textContent = n.name + " · " + n.ft.toFixed(0) + " ft";
    $("dpos").innerHTML = "x " + f1(f[0]) + "  y " + f1(f[1]) + "  z " + f1(f[2]) + " ft<br><span class=dim>units " +
      pl.o.map((v) => v.toFixed(0)).join(", ") + (pl.fly ? " · flying" : "") + "</span>";
    $("dface").textContent = faceText();
    $("dcount").textContent = dev.marks.length ? dev.marks.length + " marks" : "";
    if (dev.mm) drawMinimap();
  }
  function setDev(v) {
    dev.on = v; $("dev").classList.toggle("on", v);
  }
  let frames = 0, tries = 0;
  function maybeMinimap() {            // built a little after the first frames: at page load the render came out empty
    if (dev.mm || tries >= 4 || !dev.on || ++frames < 30) return;
    frames = 0; tries++;
    try { buildMinimap(); } catch (e) { console.warn("minimap", e); if (tries >= 4) $("dmap").style.display = "none"; }
  }
  let markTimer = 0;
  function dropMark() {
    const f = ftOf(pl.o), n = nearestSpot(pl.o), k = dev.marks.length + 1;
    dev.marks.push({ n: k, o: pl.o.slice(), ft: f.map((v) => +v.toFixed(1)), yaw: +pl.yaw.toFixed(0), pitch: +pl.pitch.toFixed(0),
      near: n.name, secs: +((performance.now() - tStart) / 1000).toFixed(1) });
    const el = $("mark");
    el.innerHTML = "MARK " + k + "<small>" + n.name + " · x " + f[0].toFixed(0) + " y " + f[1].toFixed(0) + " z " + f[2].toFixed(0) + " ft</small>";
    el.style.display = "block"; clearTimeout(markTimer); markTimer = setTimeout(() => { el.style.display = "none"; }, 3500);
    if (!dev.on) setDev(true);
  }
  $("dcopy").onclick = () => {
    const txt = JSON.stringify(dev.marks.map(({ n, ft, yaw, pitch, near, secs }) => ({ n, ft, yaw, pitch, near, secs })), null, 1);
    console.log(txt); if (navigator.clipboard) navigator.clipboard.writeText(txt).catch(() => {});
    $("dcount").textContent = "copied " + dev.marks.length;
  };
  addEventListener("keydown", (e) => {
    if (e.code === "Backquote") setDev(!dev.on);
    if (e.code === "KeyM" && !e.repeat) dropMark();
  });
  V.tick.push(update);
  if (new URLSearchParams(location.search).get("dev")) setDev(true);
  window.__dev = dev;
}

// the viewer builds window.__viewer at the end of its (async) module script: wait for it
(function wait() { if (window.__viewer && window.__viewer.tick) start(window.__viewer); else setTimeout(wait, 100); })();
