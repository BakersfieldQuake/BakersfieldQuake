// Review layer for the browser viewer (bklan2): walk the map, press N where something is wrong, type what, and export a
// report with screenshots, map-feet positions, what the crosshair was on (texture / model) and a link back to the exact view.
// Separate file like dev_overlay.js (needs window.__viewer from web_viewer_index.html; deploy_v2_viewer.sh injects the tag).
//   N  new note at this view (screenshot is taken at the key press)      L  copy a link to this exact view
//   H  show / hide this panel                                            Esc  cancel the note form
// URL: ?at=x,y,z,yaw,pitch  (map feet, the generators' frame, same numbers the Dev info panel shows)  ?review=0 starts hidden
// Notes are kept in this browser (localStorage, per map build stamp) until "Clear".
const css = `
#rv { position: fixed; left: 10px; top: 56px; width: 340px; max-height: calc(100vh - 80px); overflow: auto; background: rgba(0,0,0,.84);
      color: #fff; border: 2px solid #4ac8ff; border-radius: 8px; padding: 10px 12px; font: 13px/1.4 ui-monospace, Consolas, monospace;
      z-index: 6; display: none; }
#rv.on { display: block; }
#rv h2 { margin: 0 0 4px; font-size: 16px; color: #4ac8ff; }
#rv .dim { color: #aab; font-size: 12px; }
#rv .look { background: #111c28; border-radius: 6px; padding: 6px 8px; margin: 6px 0; min-height: 3.9em; }
#rv .look b { color: #ffd24a; }
#rv button { font-size: 12px; padding: 4px 8px; margin: 2px 4px 2px 0; }
#rv button.on { background: #4ac8ff; color: #000; }
#rv .row { margin: 4px 0; }
#rv .note { display: grid; grid-template-columns: 84px 1fr; gap: 8px; border-top: 1px solid #345; padding: 6px 0; }
#rv .note img { width: 84px; height: 52px; object-fit: cover; border-radius: 3px; cursor: pointer; }
#rv .cat { font-weight: 700; }
#rv .cat.bug { color: #ff6a5a; } #rv .cat.wrong { color: #ffa23a; } #rv .cat.missing { color: #ffd24a; }
#rv .cat.look { color: #c79bff; } #rv .cat.idea { color: #6ee07a; } #rv .cat.love { color: #ff8fd0; }
#rvform { position: fixed; inset: 0; background: rgba(0,0,0,.6); display: none; align-items: center; justify-content: center; z-index: 8; }
#rvform.on { display: flex; }
#rvform .card { background: #101820; border: 2px solid #4ac8ff; border-radius: 10px; padding: 14px 16px; width: min(560px, 94vw);
                color: #fff; font: 14px/1.4 ui-monospace, Consolas, monospace; }
#rvform img { width: 100%; border-radius: 6px; display: block; margin-bottom: 8px; }
#rvform textarea { width: 100%; height: 90px; box-sizing: border-box; font: 15px/1.4 system-ui, Arial, sans-serif; margin: 6px 0; }
#rvform select, #rvform button { font-size: 14px; padding: 6px 12px; margin-right: 6px; }
#rvform .ctx { color: #ffd24a; font-size: 12px; margin-bottom: 4px; }
#rvtoast { position: fixed; bottom: 60px; left: 50%; transform: translateX(-50%); background: #4ac8ff; color: #000; font: 700 15px ui-monospace, Consolas, monospace;
           padding: 8px 18px; border-radius: 8px; z-index: 9; display: none; }`;

const CATS = [["bug", "Bug / broken"], ["wrong", "Wrong vs. real place"], ["missing", "Missing"], ["look", "Looks bad (lighting, texture)"],
              ["idea", "Idea"], ["love", "Keep this"]];

function start(V) {
  const { THREE, meta, pl, world, scene, renderer } = V;
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const FRAME = meta.frame || [0, 0];
  const ftOf = (o) => [o[0] / 12 + FRAME[0], o[1] / 12 + FRAME[1], o[2] / 12];
  const unitsOf = (f) => [(f[0] - FRAME[0]) * 12, (f[1] - FRAME[1]) * 12, f[2] * 12];
  const toThree = (p) => new THREE.Vector3(p[0], p[2], -p[1]);
  const KEY = "bkreview:" + (meta.built || "map");
  const R = { notes: [], look: null, wire: false, full: false, trig: null, props: true, shot: null };
  try { R.notes = JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { /* private window: notes live for this page only */ }
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(R.notes)); } catch (e) { toast("storage full - download the report now"); } };

  document.head.insertAdjacentHTML("beforeend", "<style>" + css + "</style>");
  document.body.insertAdjacentHTML("beforeend", `
    <div id="rv"><h2>Review &middot; ${esc(meta.built || "")}</h2>
      <div class="dim">N note &middot; L link &middot; H hide &middot; click a thumbnail to go there</div>
      <div class="look" id="rvlook"></div>
      <div class="row"><button id="rvnote">Note (N)</button><button id="rvlink">Copy link (L)</button></div>
      <div class="row dim">Debug:
        <button id="rvwire">Wireframe</button><button id="rvfull">No lightmap</button><button id="rvtrig">Pads + teleports</button><button id="rvprops">Props</button></div>
      <div id="rvlist"></div>
      <div class="row" style="margin-top:8px"><button id="rvcopy">Copy text</button><button id="rvhtml">Download report</button>
        <button id="rvjson">Download JSON</button><button id="rvclear">Clear</button></div></div>
    <div id="rvform"><div class="card"><div class="ctx" id="rvctx"></div><img id="rvimg">
      <select id="rvcat">${CATS.map(([k, t]) => `<option value="${k}">${t}</option>`).join("")}</select>
      <textarea id="rvtext" placeholder="What is wrong / what should it be? (Ctrl+Enter saves, Esc cancels)"></textarea>
      <button id="rvsave">Save note</button><button id="rvcancel">Cancel</button></div></div>
    <div id="rvtoast"></div>`);
  const bar = $("bar");
  if (bar) { const b = document.createElement("button"); b.textContent = "Review"; b.title = "H key"; bar.appendChild(b); b.onclick = () => setPanel(!$("rv").classList.contains("on")); }
  let toastT = 0;
  function toast(t) { const e = $("rvtoast"); e.textContent = t; e.style.display = "block"; clearTimeout(toastT); toastT = setTimeout(() => { e.style.display = "none"; }, 2200); }
  function setPanel(v) { $("rv").classList.toggle("on", v); }

  // ------------------------------------------------------------- what is under the crosshair
  // world children: meta.world groups first, then one InstancedMesh per used (model, surface), in the viewer's loop order
  const propOf = new Map();
  {
    const byModel = meta.models.map(() => []);
    meta.instances.forEach((it) => byModel[it.m].push(it));
    let i = meta.world.length;
    meta.models.forEach((model, mi) => { if (byModel[mi].length) for (const s of model.surfaces) { propOf.set(world.children[i++], { model, list: byModel[mi], tex: s.tex }); } });
  }
  const ray = new THREE.Raycaster();
  function eyeRay() {
    const y = (pl.yaw * Math.PI) / 180, p = (pl.pitch * Math.PI) / 180;
    const eye = [pl.o[0], pl.o[1], pl.o[2] + 22], fw = [Math.cos(p) * Math.cos(y), Math.cos(p) * Math.sin(y), Math.sin(p)];
    ray.set(toThree(eye), new THREE.Vector3(fw[0], fw[2], -fw[1]));
    ray.far = 12000;
  }
  function look() {
    eyeRay();
    const meshes = world.children.filter((m) => m.isMesh && m.visible);
    const hit = ray.intersectObjects(meshes, false)[0];
    if (!hit) return null;
    const pt = [hit.point.x, -hit.point.z, hit.point.y], idx = world.children.indexOf(hit.object);
    const out = { ft: ftOf(pt).map((v) => +v.toFixed(1)), dist: +(hit.distance / 12).toFixed(1) };
    if (propOf.has(hit.object)) {
      const p = propOf.get(hit.object), inst = p.list[hit.instanceId];
      out.kind = "model"; out.name = p.model.name; out.tex = p.tex; out.at = inst ? ftOf(inst.o).map((v) => +v.toFixed(1)) : null;
    } else { out.kind = "surface"; out.name = meta.world[idx] ? meta.world[idx].tex : "?"; out.tex = out.name; }
    return out;
  }
  const near = (o) => { let b = null, bd = 1e12; for (const s of meta.spots) { const d = Math.hypot(s.pos[0] - o[0], s.pos[1] - o[1]); if (d < bd) { bd = d; b = s.name; } } return { name: b, ft: +(bd / 12).toFixed(0) }; };
  const fmt = (a) => a.map((v) => v.toFixed(0)).join(", ");

  let fpsN = 0, fpsT = performance.now(), fps = 0, lookT = 0, shotWanted = null;
  function tick() {
    const now = performance.now();
    fpsN++; if (now - fpsT > 500) { fps = (fpsN * 1000) / (now - fpsT); fpsN = 0; fpsT = now; }
    if (shotWanted) { const cb = shotWanted; shotWanted = null; cb(snapshot()); }      // runs right after the frame was drawn
    if (!$("rv").classList.contains("on")) return;
    if (now - lookT > 200) {
      lookT = now; R.look = look();
      const n = near(pl.o), f = ftOf(pl.o), l = R.look;
      $("rvlook").innerHTML = (l ? `<b>${esc(l.kind)}</b> ${esc(l.name)}${l.kind === "model" ? " <span class=dim>(" + esc(l.tex) + ")</span>" : ""}<br><span class=dim>${l.dist} ft away &middot; at ${fmt(l.ft)} ft</span>`
        : "<span class=dim>(crosshair on sky)</span>") + `<br>near <b>${esc(n.name)}</b> ${n.ft} ft<br><span class=dim>you ${fmt(f)} ft &middot; yaw ${((pl.yaw % 360 + 360) % 360).toFixed(0)} &middot; ${fps.toFixed(0)} fps</span>`;
    }
    for (const s of pins) s.visible = $("rv").classList.contains("on");
  }
  V.tick.push(tick);

  // ------------------------------------------------------------- screenshots
  function snapshot() {
    const c = renderer.domElement, w = 960, h = Math.round((w * c.height) / c.width), t = document.createElement("canvas");
    t.width = w; t.height = h; t.getContext("2d").drawImage(c, 0, 0, w, h);
    return t.toDataURL("image/jpeg", 0.8);
  }

  // ------------------------------------------------------------- notes
  let pending = null;
  function openForm() {
    const l = look(), n = near(pl.o), f = ftOf(pl.o);
    pending = { ft: f.map((v) => +v.toFixed(1)), yaw: +(((pl.yaw % 360) + 360) % 360).toFixed(0), pitch: +pl.pitch.toFixed(0), fly: !!pl.fly,
      near: n.name, nearFt: n.ft, target: l, built: meta.built || "", when: new Date().toISOString() };
    shotWanted = (img) => {
      pending.img = img; $("rvimg").src = img;
      $("rvctx").textContent = (l ? l.kind + ": " + l.name + " - " : "") + "near " + n.name + " (" + n.ft + " ft) - you at " + fmt(f) + " ft";
      if (document.pointerLockElement) document.exitPointerLock();
      $("rvform").classList.add("on"); $("rvtext").value = ""; setTimeout(() => { $("intro").style.display = "none"; $("rvtext").focus(); }, 30);
    };
  }
  function closeForm() { $("rvform").classList.remove("on"); pending = null; }
  function saveNote() {
    if (!pending) return;
    pending.cat = $("rvcat").value; pending.text = $("rvtext").value.trim();
    pending.n = (R.notes.reduce((m, x) => Math.max(m, x.n), 0)) + 1;
    const n = pending.n;
    R.notes.push(pending); save(); closeForm(); renderList(); rebuildPins(); toast("note " + n + " saved");
  }
  $("rvnote").onclick = openForm;
  $("rvsave").onclick = saveNote;
  $("rvcancel").onclick = closeForm;
  // typing must not drive the walker (F = fly, WASD = move) or the dev overlay (M, `)
  for (const id of ["rvtext", "rvcat"]) $(id).addEventListener("keydown", (e) => {
    e.stopPropagation();
    if (e.code === "Escape") closeForm();
    if (e.code === "Enter" && (e.ctrlKey || e.metaKey)) saveNote();
  });
  $("rvform").addEventListener("keyup", (e) => e.stopPropagation());

  function go(nt) {
    const o = unitsOf(nt.ft); pl.o = o; pl.v = [0, 0, 0]; pl.yaw = nt.yaw; pl.pitch = nt.pitch; pl.onground = false;
    if (nt.fly && V.setFly) V.setFly(true);
  }
  const linkFor = (nt) => location.origin + location.pathname + "?at=" + [...nt.ft, nt.yaw, nt.pitch].join(",");
  function hereNote() { return { ft: ftOf(pl.o).map((v) => +v.toFixed(1)), yaw: +(((pl.yaw % 360) + 360) % 360).toFixed(0), pitch: +pl.pitch.toFixed(0) }; }
  function copy(txt, msg) {
    const done = () => toast(msg);
    if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done, () => { console.log(txt); toast("clipboard blocked - see console"); }); else { console.log(txt); toast("see console"); }
  }
  $("rvlink").onclick = () => copy(linkFor(hereNote()), "link to this view copied");

  function renderList() {
    $("rvlist").innerHTML = R.notes.length ? R.notes.map((nt) => `<div class="note" data-n="${nt.n}"><img src="${nt.img}" title="go there">
      <div><span class="cat ${nt.cat}">#${nt.n} ${esc(nt.cat)}</span> <button data-del="${nt.n}" style="float:right">x</button><br>${esc(nt.text) || "<i class=dim>(no text)</i>"}
      <div class="dim">${esc(nt.near)}${nt.target ? " &middot; " + esc(nt.target.name) : ""}</div></div></div>`).join("") : `<div class="dim" style="margin-top:6px">No notes yet. Press N where something is wrong.</div>`;
  }
  $("rvlist").onclick = (e) => {
    const d = e.target.closest("[data-del]");
    if (d) { R.notes = R.notes.filter((x) => x.n !== +d.dataset.del); save(); renderList(); rebuildPins(); return; }
    const row = e.target.closest(".note"); if (row) go(R.notes.find((x) => x.n === +row.dataset.n));
  };

  // ------------------------------------------------------------- numbered pins in the world
  const pins = [];
  function rebuildPins() {
    for (const s of pins) { scene.remove(s); s.material.map.dispose(); s.material.dispose(); }
    pins.length = 0;
    for (const nt of R.notes) {
      const at = nt.target ? nt.target.ft : nt.ft, c = document.createElement("canvas"); c.width = c.height = 64;
      const g = c.getContext("2d"); g.fillStyle = "#4ac8ff"; g.beginPath(); g.arc(32, 32, 28, 0, 7); g.fill(); g.strokeStyle = "#000"; g.lineWidth = 4; g.stroke();
      g.fillStyle = "#000"; g.font = "bold 32px sans-serif"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(nt.n, 32, 34);
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), depthTest: false, sizeAttenuation: false }));
      sp.scale.set(0.045, 0.045, 1); sp.position.copy(toThree(unitsOf(at))); sp.renderOrder = 10; sp.visible = $("rv").classList.contains("on");
      scene.add(sp); pins.push(sp);
    }
  }

  // ------------------------------------------------------------- debug toggles
  const meshes = () => world.children.filter((m) => m.isMesh && !propOf.has(m));
  const white = new THREE.DataTexture(new Uint8Array([128, 128, 128, 255]), 1, 1); white.needsUpdate = true;      // x2 overbright -> flat 1.0
  const flip = (id, on) => $(id).classList.toggle("on", on);
  $("rvwire").onclick = () => { R.wire = !R.wire; for (const m of meshes()) m.material.wireframe = R.wire; flip("rvwire", R.wire); };
  $("rvfull").onclick = () => {
    R.full = !R.full;
    for (const m of meshes()) { const u = m.material.uniforms; u.lm._real = u.lm._real || u.lm.value; u.lm.value = R.full ? white : u.lm._real; }
    flip("rvfull", R.full);
  };
  $("rvprops").classList.add("on");
  $("rvprops").onclick = () => { R.props = !R.props; for (const [m] of propOf) m.visible = R.props; flip("rvprops", R.props); };
  $("rvtrig").onclick = () => {
    if (!R.trig) {
      R.trig = new THREE.Group();
      for (const t of meta.triggers || []) {
        const sz = [0, 1, 2].map((i) => t.max[i] - t.min[i]), g = new THREE.EdgesGeometry(new THREE.BoxGeometry(sz[0], sz[1], sz[2]));
        const ln = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: t.push ? 0xff9a20 : 0x20e0ff, depthTest: false }));
        ln.position.set((t.min[0] + t.max[0]) / 2, (t.min[1] + t.max[1]) / 2, (t.min[2] + t.max[2]) / 2); ln.renderOrder = 9; R.trig.add(ln);
      }
      R.trig.visible = false; world.add(R.trig);
    }
    R.trig.visible = !R.trig.visible; flip("rvtrig", R.trig.visible);
  };

  // ------------------------------------------------------------- export
  const label = (k) => (CATS.find((c) => c[0] === k) || [k, k])[1];
  function text() {
    return `# bklan2 review (map built ${meta.built || "?"}), ${R.notes.length} notes\n\n` + R.notes.map((nt) => {
      const t = nt.target;
      return `## #${nt.n} ${label(nt.cat)}\n${nt.text || "(no text)"}\n- near: ${nt.near} (${nt.nearFt} ft)\n- me: x ${nt.ft[0]} y ${nt.ft[1]} z ${nt.ft[2]} ft, yaw ${nt.yaw}, pitch ${nt.pitch}${nt.fly ? " (flying)" : ""}\n` +
        (t ? `- looking at: ${t.kind} ${t.name}${t.kind === "model" ? " [" + t.tex + "]" : ""}, ${t.dist} ft away, point ${t.ft.join(", ")} ft\n` : "") + `- link: ${linkFor(nt)}\n`;
    }).join("\n");
  }
  function download(name, mime, body) {
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([body], { type: mime })); a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  }
  const stamp = () => (meta.built || "map").replace(/[^0-9a-z]+/gi, "-");
  $("rvcopy").onclick = () => copy(text(), R.notes.length + " notes copied");
  $("rvjson").onclick = () => download("bklan2-review-" + stamp() + ".json", "application/json", JSON.stringify({ map: "bklan2", built: meta.built, notes: R.notes }, null, 1));
  $("rvhtml").onclick = () => download("bklan2-review-" + stamp() + ".html", "text/html", `<!doctype html><meta charset=utf-8><title>bklan2 review</title>
<style>body{font:15px/1.45 system-ui,Arial;max-width:980px;margin:20px auto;padding:0 14px}img{width:100%;border-radius:6px}h2{margin-top:30px}code{background:#eee;padding:1px 4px}</style>
<h1>bklan2 review &middot; map built ${esc(meta.built || "?")} &middot; ${R.notes.length} notes</h1>` + R.notes.map((nt) => {
    const t = nt.target;
    return `<h2>#${nt.n} ${esc(label(nt.cat))}</h2><p><b>${esc(nt.text) || "(no text)"}</b></p><img src="${nt.img}"><p>near <code>${esc(nt.near)}</code> (${nt.nearFt} ft) &middot; me <code>${nt.ft.join(", ")}</code> ft, yaw ${nt.yaw}, pitch ${nt.pitch}` +
      (t ? ` &middot; looking at ${esc(t.kind)} <code>${esc(t.name)}</code>, ${t.dist} ft away` : "") + ` &middot; <a href="${esc(linkFor(nt))}">open this view</a></p>`;
  }).join(""));
  $("rvclear").onclick = () => { if (R.notes.length && confirm("Delete all " + R.notes.length + " notes?")) { R.notes = []; save(); renderList(); rebuildPins(); } };

  // ------------------------------------------------------------- keys + startup
  addEventListener("keydown", (e) => {
    if (e.repeat || $("rvform").classList.contains("on")) return;
    if (e.code === "KeyN") openForm();
    else if (e.code === "KeyL") $("rvlink").click();
    else if (e.code === "KeyH") setPanel(!$("rv").classList.contains("on"));
  });
  const q = new URLSearchParams(location.search);
  const at = (q.get("at") || "").split(",").map(Number);
  if (at.length >= 3 && at.slice(0, 3).every(isFinite)) go({ ft: at.slice(0, 3), yaw: isFinite(at[3]) ? at[3] : 0, pitch: isFinite(at[4]) ? at[4] : 0 });
  renderList(); rebuildPins();
  if (q.get("review") !== "0") setPanel(true);
  window.__review = R;
}

(function wait() { if (window.__viewer && window.__viewer.tick) start(window.__viewer); else setTimeout(wait, 100); })();
