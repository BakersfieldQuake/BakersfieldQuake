"""Post-processes out/web/warehouse5 (exported from maps/bklan5.bsp by export_web_viewer.py) to add:
  1. Live animated 8-frame video textures & 3D screen quads for all `bk_tv` entities (including all 4 Daniel videos!)
  2. True 360° 8-angle × 6-frame RGBA billboard sprites extracted from .spr32 for:
       - `npc_greensuit_wheelman` (cruising the Fox Downtown route & E 21st St)
       - `npc_robeguy` (The Flamingo Fiend roaming Fox Plaza & LAN Courtyard)
       - `npc_david_squad` (David Ojeda + all 3 chasing Pregnant Women outside Golden West Casino)
       - `monster_daniel` (360° Bakersfield LAN Station inside Larry's Warehouse)
  3. DarkPlaces-matched 4x overbright + gamma shader curve + real-time Lighting Preset Switcher (`lm_<preset>.jpg`)
     so the user can compare Soft Daylight, Sunny Balanced, Warm Amber, Twilight Neon, and Before (Blown-Out) live!

Usage:
  python enhance_bklan5_web.py out/web/warehouse5
"""
import io
import json
import os
import shutil
import struct
import sys
import zipfile

from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", ".."))
STAGED = os.path.normpath(os.path.join(MOD, "..", "_bakersfield_dev", "staged_assets"))
PK3_PATH = os.path.join(MOD, "bakersfield.pk3")
_PK3 = zipfile.ZipFile(PK3_PATH, "r") if os.path.isfile(PK3_PATH) else None
_PK3_NAMES = set(_PK3.namelist()) if _PK3 else set()


def mod_bytes(rel_posix: str):
    for base in (MOD, STAGED):
        disk = os.path.join(base, rel_posix.replace("/", os.sep))
        if os.path.isfile(disk):
            with open(disk, "rb") as fp:
                return fp.read()
    if _PK3 and rel_posix in _PK3_NAMES:
        return _PK3.read(rel_posix)
    return None


def parse_bsp_ents(bsp_path: str):
    with open(bsp_path, "rb") as f:
        hdr = f.read(4 + 15 * 8)
        magic = hdr[:4]
        assert magic in (b"\x1d\x00\x00\x00", b"BSP2")
        ent_ofs, ent_len = struct.unpack_from("<ii", hdr, 4)
        f.seek(ent_ofs)
        txt = f.read(ent_len).decode("latin-1", errors="ignore")
    import re
    out = []
    for blk in re.findall(r"\{([^}]*)\}", txt):
        out.append(dict(re.findall(r'"([^"]+)"\s+"([^"]*)"', blk)))
    return out


def extract_spr32_atlas(spr_rel: str, bank_start: int, stride: int, n_anim: int, cell_w: int, cell_h: int,
                        base_oy: int, bright_gain: float = 1.55) -> Image.Image:
    raw = mod_bytes(spr_rel)
    assert raw is not None, f"Missing sprite: {spr_rel}"
    ident, ver, stype, rad, mw, mh, nf, beam, sync = struct.unpack_from("<4siifiiifi", raw, 0)
    assert ident == b"IDSP" and ver == 32
    frames = []
    ofs = 36
    for _ in range(nf):
        ft, ox, oy, cw, ch = struct.unpack_from("<iiiii", raw, ofs)
        ofs += 20
        px = raw[ofs : ofs + cw * ch * 4]
        ofs += cw * ch * 4
        frames.append((ox, oy, cw, ch, px))

    atlas = Image.new("RGBA", (cell_w * n_anim, cell_h * 8), (0, 0, 0, 0))
    base_ox = -(cell_w // 2)
    for d in range(8):
        for k in range(n_anim):
            idx = bank_start + d * stride + k
            if idx >= len(frames):
                idx = d % len(frames)
            ox, oy, cw, ch, px = frames[idx]
            im = Image.frombytes("RGBA", (cw, ch), px)
            r, g, b, a = im.split()
            rgb = ImageEnhance.Brightness(Image.merge("RGB", (r, g, b))).enhance(bright_gain)
            im = Image.merge("RGBA", (*rgb.split(), a))
            dst_x = ox - base_ox
            dst_y = base_oy - oy
            cell = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
            cell.alpha_composite(im, (max(0, min(cell_w - cw, dst_x)), max(0, min(cell_h - ch, dst_y))))
            atlas.paste(cell, (k * cell_w, d * cell_h))
    return atlas


def build_tv_strip(vid: int, n_frames: int = 8) -> Image.Image:
    imgs = []
    for k in range(n_frames):
        fnum = 10 + k * 6
        raw = None
        for ext in (".jpg", ".png", ".tga"):
            raw = mod_bytes(f"progs/bktv/v{vid}_{fnum:04d}{ext}")
            if raw is not None:
                break
        if raw is None:
            raw = mod_bytes(f"progs/bktv/v{vid}_0000.jpg") or mod_bytes(f"progs/bktv/v{vid}_0000.png")
        if raw is not None:
            im = Image.open(io.BytesIO(raw)).convert("RGB").resize((192, 144), Image.LANCZOS)
        else:
            im = Image.new("RGB", (192, 144), (30, 50, 80))
        imgs.append(im)
    strip = Image.new("RGB", (192 * n_frames, 144))
    for i, im in enumerate(imgs):
        strip.paste(im, (i * 192, 0))
    return strip


def main():
    web_dir = sys.argv[1]
    tex_dir = os.path.join(web_dir, "tex")
    os.makedirs(tex_dir, exist_ok=True)
    bsp_path = os.path.join(MOD, "maps", "bklan5.bsp")
    ents = parse_bsp_ents(bsp_path)
    meta_path = os.path.join(web_dir, "map.json")
    meta = json.load(open(meta_path, encoding="utf-8"))

    # 1. Export TV strips & screen placements
    tvs = []
    used_vids = set()
    for i, e in enumerate(ents):
        if e.get("classname") != "bk_tv":
            continue
        ox, oy, oz = [float(v) for v in e["origin"].split()]
        yaw = float(e.get("angle", "0"))
        sc = float(e.get("scale", "1"))
        cnt = int(float(e.get("cnt", "0")))
        vid = cnt if 8 <= cnt <= 11 else (8 + (i % 4))
        used_vids.add(vid)
        tvs.append({"o": [ox, oy, oz], "yaw": yaw, "s": sc, "vid": vid})
    for vid in sorted(used_vids):
        build_tv_strip(vid, 8).save(os.path.join(tex_dir, f"tv_v{vid}.jpg"), quality=88)

    # 2. Export 360° 8-angle x 6-frame character sprite atlases
    spr_specs = {
        "greensuit": ("progs/greensuit_wheelman.spr32", 8, 6, 6, 224, 224, 196, 1.55, 80.6, 80.6, 70.6),
        "robeguy":   ("progs/robeguy.spr32",            8, 6, 6, 256, 288, 262, 1.55, 71.7, 80.6, 73.4),
        "david":     ("progs/david.spr32",            152, 6, 6, 256, 288, 262, 1.55, 66.6, 74.9, 68.1),
        "preg1":     ("progs/preg_1.spr32",             8, 6, 6, 128, 144, 131, 1.55, 65.3, 73.4, 66.8),
        "preg2":     ("progs/preg_2.spr32",             8, 6, 6, 128, 144, 131, 1.55, 65.3, 73.4, 66.8),
        "preg3":     ("progs/preg_3.spr32",             8, 6, 6, 128, 144, 131, 1.55, 65.3, 73.4, 66.8),
        "daniel_lan":("progs/daniel.spr32",           296, 6, 6, 256, 288, 262, 1.55, 66.6, 74.9, 68.1),
    }
    for key, (rel, b0, st, nf, cw, ch, boy, gain, _, _, _) in spr_specs.items():
        atl = extract_spr32_atlas(rel, b0, st, nf, cw, ch, boy, gain)
        atl = atl.resize((atl.width // 2, atl.height // 2), Image.LANCZOS)
        atl.save(os.path.join(tex_dir, f"spr_{key}.png"))

    by_name = {e.get("targetname"): e for e in ents if e.get("classname") == "bk_route"}
    sprites = []
    for e in ents:
        cls = e.get("classname")
        if cls not in ("npc_greensuit_wheelman", "npc_robeguy", "npc_david_squad", "monster_daniel"):
            continue
        ox, oy, oz = [float(v) for v in e["origin"].split()]
        yaw = float(e.get("angle", "0"))
        if cls == "npc_greensuit_wheelman":
            pts = []
            tgt = e.get("target", "")
            cur = by_name.get(tgt)
            seen = set()
            while cur and id(cur) not in seen:
                seen.add(id(cur))
                pts.append([float(v) for v in cur["origin"].split()])
                cur = by_name.get(cur.get("target"))
            _, _, _, _, _, _, _, _, ww, wh, gnd = spr_specs["greensuit"]
            sprites.append({"kind": "greensuit", "o": [ox, oy, oz], "yaw": yaw, "w": ww, "h": wh, "gnd": gnd,
                            "route": pts if pts else None, "patrol": 220.0, "speed": 230.0})
        elif cls == "npc_robeguy":
            _, _, _, _, _, _, _, _, ww, wh, gnd = spr_specs["robeguy"]
            sprites.append({"kind": "robeguy", "o": [ox, oy, oz], "yaw": yaw, "w": ww, "h": wh, "gnd": gnd,
                            "route": None, "patrol": 145.0, "speed": 175.0})
        elif cls == "monster_daniel":
            _, _, _, _, _, _, _, _, ww, wh, gnd = spr_specs["daniel_lan"]
            sprites.append({"kind": "daniel_lan", "o": [ox, oy, oz], "yaw": yaw, "w": ww, "h": wh, "gnd": gnd,
                            "route": None, "patrol": 0.0, "speed": 0.0})
        elif cls == "npc_david_squad":
            _, _, _, _, _, _, _, _, ww, wh, gnd = spr_specs["david"]
            sprites.append({"kind": "david", "o": [ox, oy, oz], "yaw": yaw, "w": ww, "h": wh, "gnd": gnd,
                            "route": None, "patrol": 185.0, "speed": 245.0, "phase": 0.0})
            for idx_p, pk in enumerate(("preg1", "preg2", "preg3")):
                _, _, _, _, _, _, _, _, pw, ph, pgnd = spr_specs[pk]
                sprites.append({"kind": pk, "o": [ox, oy, oz], "yaw": yaw, "w": pw, "h": ph, "gnd": pgnd,
                                "route": None, "patrol": 185.0, "speed": 245.0, "phase": -0.55 - idx_p * 0.32,
                                "lateral": (idx_p - 1) * 34.0})

    meta["tvs"] = tvs
    meta["sprites"] = sprites
    with open(meta_path, "w", encoding="utf-8") as fp:
        json.dump(meta, fp, separators=(",", ":"))

    # 3. Copy runtime JS libs & generate calibrated warehouse5/index.html
    os.makedirs(os.path.join(web_dir, "lib"), exist_ok=True)
    three_src = os.path.join(HERE, "out", "web", "warehouse", "lib", "three.module.min.js")
    if os.path.isfile(three_src):
        shutil.copy(three_src, os.path.join(web_dir, "lib", "three.module.min.js"))
    for js_fn in ("dev_overlay.js", "dev_review.js"):
        shutil.copy(os.path.join(HERE, js_fn), os.path.join(web_dir, js_fn))

    html = open(os.path.join(HERE, "web_viewer_index.html"), encoding="utf-8").read().replace("\r\n", "\n")
    html = html.replace("<title>Larry's Warehouse</title>", "<title>BakersfieldQuake - bklan5 (Fox, Padre Hotel, Daniel LAN, Wild Vehicles & NPCs)</title>")
    html = html.replace("<h1>Larry's Warehouse</h1>", "<h1>Bakersfield bklan5 &mdash; Fox, Padre Hotel, LAN Party &amp; Street Chaos</h1>")
    html = html.replace(
        '<a href="making-of.html" target="_blank">The Making Of</a>',
        '<select id="lmPreset" title="Explore baked lighting presets">'
        '<option value="soft_daylight">Lighting: Soft Daylight (Default)</option>'
        '<option value="sunny_balanced">Lighting: Sunny Balanced</option>'
        '<option value="warm_amber">Lighting: Warm Afternoon Amber</option>'
        '<option value="twilight_neon">Lighting: Cool Twilight Neon</option>'
        '<option value="before_blownout">Lighting: Before (Old Blown-Out)</option>'
        '</select>'
        '<a href="../bklan5_showcase.html">What\'s New Showcase</a><a href="../warehouse4/">bklan4</a>',
    )
    # Match DarkPlaces 4x overbright + v_contrast 1.125 + v_gamma 1.3125 (2.0 * 2.67 = 5.34 -> pow(c, 1/1.3125)):
    html = html.replace('value="3.6"', 'value="2.65"')
    html = html.replace("const bright = { value: 3.6 };", "const bright = { value: 2.65 };")
    html = html.replace(
        "vec3 c = t.rgb * texture2D(lm, vLm).rgb * 2.0 * bright + texture2D(glow, vUv).rgb;\n    gl_FragColor = vec4(c, 1.0);",
        "vec3 lin = t.rgb * texture2D(lm, vLm).rgb * 2.0 * bright;\n    vec3 c = pow(max(lin, vec3(0.0)), vec3(1.0 / 1.3125)) + texture2D(glow, vUv).rgb;\n    gl_FragColor = vec4(c, 1.0);",
    )
    html = html.replace(
        "vec3 c = texture2D(map, pUv).rgb * vCol * shade * 2.0 * bright + texture2D(glow, pUv).rgb;\n    gl_FragColor = vec4(c, 1.0);",
        "vec3 lin = texture2D(map, pUv).rgb * vCol * shade * 2.0 * bright;\n    vec3 c = pow(max(lin, vec3(0.0)), vec3(1.0 / 1.3125)) + texture2D(glow, pUv).rgb;\n    gl_FragColor = vec4(c, 1.0);",
    )

    extra_js = """
// --- Live Lightmap Preset Switcher + bklan5 Daniel TV screens & 360° 8-angle SPR32 roaming NPCs ---
const lmCache = { soft_daylight: lightmap };
const lmSelect = $("lmPreset");
window.__setPreset = (key) => new Promise((resolve) => {
  if (lmSelect) lmSelect.value = key;
  const url = key === "soft_daylight" ? "lightmap.png" : ("lm_" + key + ".jpg");
  if (lmCache[key]) {
    world.traverse((o) => { if (o.material && o.material.uniforms && o.material.uniforms.lm) o.material.uniforms.lm.value = lmCache[key]; });
    requestAnimationFrame(() => requestAnimationFrame(() => resolve(true)));
    return;
  }
  const t = texLoader.load(url, () => {
    t.needsUpdate = true;
    lmCache[key] = t;
    world.traverse((o) => { if (o.material && o.material.uniforms && o.material.uniforms.lm) o.material.uniforms.lm.value = t; });
    requestAnimationFrame(() => requestAnimationFrame(() => resolve(true)));
  }, undefined, () => resolve(false));
  t.flipY = false;
  t.generateMipmaps = false;
  t.minFilter = THREE.LinearFilter;
  t.colorSpace = THREE.NoColorSpace;
});
if (lmSelect) lmSelect.onchange = () => { window.__setPreset(lmSelect.value); lmSelect.blur(); };

const tvMeshes = (meta.tvs || []).map((tv) => {
  const t = texLoader.load("tex/tv_v" + tv.vid + ".jpg");
  t.colorSpace = THREE.NoColorSpace;
  t.repeat.set(1 / 8, 1);
  const geo = new THREE.PlaneGeometry(48 * tv.s, 36 * tv.s);
  const mat = new THREE.MeshBasicMaterial({ map: t, side: THREE.DoubleSide });
  const m = new THREE.Mesh(geo, mat);
  m.rotation.order = "ZYX";
  const rad = (tv.yaw * Math.PI) / 180;
  m.position.set(tv.o[0] + Math.cos(rad) * 0.6, tv.o[1] + Math.sin(rad) * 0.6, tv.o[2]);
  m.rotation.z = rad + Math.PI / 2;
  m.rotation.x = Math.PI / 2;
  world.add(m);
  return { tv, t };
});

const sprTexCache = {};
function getSprTex(kind) {
  if (sprTexCache[kind]) return sprTexCache[kind];
  const t = texLoader.load("tex/spr_" + kind + ".png");
  t.colorSpace = THREE.NoColorSpace;
  t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearFilter;
  return (sprTexCache[kind] = t);
}

const sprNodes = (meta.sprites || []).map((sp) => {
  if (sp.route && sp.route.length > 1) {
    const pts = [sp.o].concat(sp.route);
    sp.legs = []; sp.total = 0;
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = i + 1 < pts.length ? pts[i + 1] : sp.route[0];
      const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const dt = Math.max(0.05, len / (sp.speed || 220));
      sp.legs.push({ a, b, t0: sp.total, t: dt }); sp.total += dt;
    }
  }
  const baseTex = getSprTex(sp.kind).clone();
  baseTex.needsUpdate = true;
  texLoader.load("tex/spr_" + sp.kind + ".png", (loaded) => {
    baseTex.image = loaded.image;
    baseTex.colorSpace = THREE.NoColorSpace;
    baseTex.repeat.set(1 / 6, 1 / 8);
    baseTex.needsUpdate = true;
  });
  baseTex.repeat.set(1 / 6, 1 / 8);
  const geo = new THREE.PlaneGeometry(sp.w, sp.h);
  const mat = new THREE.MeshBasicMaterial({ map: baseTex, transparent: true, alphaTest: 0.35, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.frustumCulled = false;
  world.add(mesh);
  return { sp, mesh, tex: baseTex };
});

function updateBklan5Extras(now) {
  const sec = now / 1000;
  for (const { tv, t } of tvMeshes) {
    const f = Math.floor(sec * 8 + tv.o[0] * 0.01) % 8;
    t.offset.set(f / 8, 0);
  }
  for (const { sp, mesh, tex } of sprNodes) {
    let x = sp.o[0], y = sp.o[1], z = sp.o[2], yaw = (sp.yaw * Math.PI) / 180;
    if (sp.legs) {
      const tt = sec % sp.total;
      const leg = sp.legs.find((l) => tt < l.t0 + l.t) || sp.legs[sp.legs.length - 1];
      const f = (tt - leg.t0) / leg.t;
      x = leg.a[0] + (leg.b[0] - leg.a[0]) * f;
      y = leg.a[1] + (leg.b[1] - leg.a[1]) * f;
      yaw = Math.atan2(leg.b[1] - leg.a[1], leg.b[0] - leg.a[0]);
    } else if (sp.patrol > 0) {
      const ang = sec * (sp.speed / sp.patrol) * 0.55 + (sp.phase || 0);
      const rx = sp.patrol, ry = sp.patrol * 0.58;
      const cx = sp.o[0] + Math.cos(ang) * rx;
      const cy = sp.o[1] + Math.sin(ang) * ry;
      const vx = -Math.sin(ang) * rx, vy = Math.cos(ang) * ry;
      yaw = Math.atan2(vy, vx);
      const lat = sp.lateral || 0;
      x = cx - Math.sin(yaw) * lat;
      y = cy + Math.cos(yaw) * lat;
    }
    const zCenter = z + (sp.h * 0.5) - (sp.h - sp.gnd);
    mesh.position.set(x, y, zCenter);
    const dx = pl.o[0] - x, dy = pl.o[1] - y;
    const faceYaw = Math.atan2(dy, dx);
    mesh.rotation.set(0, 0, 0);
    mesh.rotateZ(faceYaw + Math.PI / 2);
    mesh.rotateX(Math.PI / 2);
    let rel = ((faceYaw - yaw) * 180) / Math.PI;
    rel = rel - 360 * Math.floor(rel / 360);
    let d = Math.floor(rel / 45 + 0.5) % 8;
    const k = sp.speed > 0 ? (Math.floor(sec * 12) % 6) : (Math.floor(sec * 6) % 6);
    tex.offset.set(k / 6, 1 - (d + 1) / 8);
  }
}
"""
    html = html.replace("// overcast skybox (the map's own)", extra_js + "\n// overcast skybox (the map's own)")
    html = html.replace(
        "updateMovers(now);",
        "const _tNow = window.__fixedNow !== null ? window.__fixedNow : now;\n  updateMovers(_tNow);\n  updateBklan5Extras(_tNow);",
    )
    jump_hook = """window.__assetsReady = false;
THREE.DefaultLoadingManager.onLoad = () => { window.__assetsReady = true; };
window.__fixedNow = null;
window.__jumpTo = (xFt, yFt, zFt, yawDeg, pitchDeg = 0, fixedSec = null, hideUi = true) => {
  const ox = (meta.frame && meta.frame[0]) || -110, oy = (meta.frame && meta.frame[1]) || 225;
  pl.fly = true; pl.v = [0, 0, 0];
  pl.o = [(xFt - ox) * 12, (yFt - oy) * 12, zFt * 12];
  pl.yaw = yawDeg; pl.pitch = pitchDeg;
  window.__fixedNow = fixedSec !== null ? fixedSec * 1000 : null;
  if (hideUi) {
    for (const id of ["intro", "bar", "cross", "load", "tbtns", "stick"]) {
      if ($(id)) $(id).style.display = "none";
    }
  }
};
"""
    assert "}\nrequestAnimationFrame(frame);" in html, "Expected top-level requestAnimationFrame(frame) anchor"
    html = html.replace("}\nrequestAnimationFrame(frame);", "}\n" + jump_hook + "\nrequestAnimationFrame(frame);", 1)
    with open(os.path.join(web_dir, "index.html"), "w", encoding="utf-8") as fp:
        fp.write(html)
    print(f"Enhanced {web_dir}: {len(tvs)} live TVs, {len(sprites)} 360° sprites, DarkPlaces-matched gamma & 5-preset switcher")


if __name__ == "__main__":
    main()
