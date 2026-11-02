"""Generates a clean, simple, zero-fake-stuff g:\\Quake\\Combat\\BakersfieldQuake\\fanpage\\index.html:
- Prominent big "DOWNLOAD" button -> https://bakersfield.larrywew.fun/BakersfieldLAN.zip
- 3 action GIFs + 6 interactive 3D/sprite assets + 4 maps + 3 concise Underdog bullets
- Slims fanpage/assets/models_data.js to ONLY the 6 featured in-game models and prunes unused media.
"""
import base64
import gzip
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FANPAGE_DIR = os.path.join(MOD_ROOT, "fanpage")
INDEX_OUT = os.path.join(FANPAGE_DIR, "index.html")
MODELS_JS = os.path.join(FANPAGE_DIR, "assets", "models_data.js")

DOWNLOAD_URL = "https://bakersfield.larrywew.fun/BakersfieldLAN.zip"


def shot_card(fname, caption, tag=None, contain=False, is_gif=False):
    folder = "gifs" if is_gif else "shots"
    src = f"media/{folder}/{fname}"
    cls_wrap = "shot-img-wrap contain" if contain else "shot-img-wrap"
    tag_html = ""
    if tag:
        tcls = "shot-tag gif" if is_gif else "shot-tag"
        tag_html = f'<span class="{tcls}">{tag}</span>'
    return f"""<div class="shot-card">
  <div class="{cls_wrap}">
    {tag_html}
    <img src="{src}" alt="{caption}" loading="lazy">
  </div>
  <div class="shot-cap"><span>{caption}</span></div>
</div>"""


def vp_card(model_id, title, fmt, foot, theme="", skin=None, pov=None, zoom=None):
    attrs = [f'data-model="{model_id}"']
    if skin is not None:
        attrs.append(f'data-skin="{skin}"')
    if pov is not None:
        attrs.append(f'data-pov="{1 if pov else 0}"')
    if zoom is not None:
        attrs.append(f'data-zoom="{zoom}"')
    c_cls = f"vp-card {theme}".strip()
    return f"""<div class="{c_cls}">
  <div class="vp-hdr">
    <span class="vp-hdr-title" title="{title}">{title}</span>
    <span class="vp-fmt-pill">{fmt}</span>
  </div>
  <div class="vp-stage" {' '.join(attrs)}></div>
  <div class="vp-foot">{foot}</div>
</div>"""


def slim_models_js(keep_ids):
    raw_js = open(MODELS_JS, "r", encoding="utf-8").read()
    full = json.loads(raw_js.split("=", 1)[1].strip().rstrip(";"))
    by_id = {m["id"]: m for m in full["models"]}
    if [m["id"] for m in full["models"]] == list(keep_ids):
        return set(keep_ids)

    arena_full = gzip.decompress(base64.b64decode(full["binGz"]))
    new_buf = bytearray()
    new_tex_list = []
    tex_remap = {}

    def map_tex(old_idx):
        if old_idx is None or old_idx < 0:
            return -1
        if old_idx not in tex_remap:
            tex_remap[old_idx] = len(new_tex_list)
            new_tex_list.append(full["textures"][old_idx])
        return tex_remap[old_idx]

    def copy_slice(sl):
        pad = (-len(new_buf)) & 3
        if pad:
            new_buf.extend(b"\x00" * pad)
        off = len(new_buf)
        chunk = arena_full[sl[0]:sl[0] + sl[1]]
        new_buf.extend(chunk)
        return [off, len(chunk)]

    out_models = []
    for mid in keep_ids:
        m = json.loads(json.dumps(by_id[mid]))
        for s in m["surfaces"]:
            s["tris"] = copy_slice(s["tris"])
            s["edges"] = copy_slice(s["edges"])
            s["uv"] = copy_slice(s["uv"])
            s["pos"] = copy_slice(s["pos"])
            s["nrm"] = copy_slice(s["nrm"])
            s["tex"] = map_tex(s.get("tex", -1))
            s["glowTex"] = map_tex(s.get("glowTex", -1))
        for sk in m.get("skins", []):
            for _, ov in sk.get("map", {}).items():
                if "tex" in ov:
                    ov["tex"] = map_tex(ov["tex"])
                if "glowTex" in ov:
                    ov["glowTex"] = map_tex(ov["glowTex"])
        out_models.append(m)

    gz = gzip.compress(bytes(new_buf), compresslevel=9)
    slim = dict(textures=new_tex_list, models=out_models, binGz=base64.b64encode(gz).decode("ascii"))
    with open(MODELS_JS, "w", encoding="utf-8") as f:
        f.write("window.BQ_MODELS_PACK = " + json.dumps(slim, separators=(",", ":")) + ";\n")
    return set(keep_ids)


HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bakersfield Quake</title>
  <link rel="icon" type="image/gif" href="media/gifs/quake_rune_spin.gif">
  <link rel="stylesheet" href="styles.css">
</head>
<body>

  <canvas id="gl-canvas"></canvas>

  <div class="page-shell">

    <!-- ==================== HERO + BIG DOWNLOAD BUTTON ==================== -->
    <div class="hero-banner">
      <div class="hero-title-row">
        <img class="hero-rune" src="media/gifs/quake_rune_spin.gif" alt="Quake Rune">
        <h1 class="hero-h1">BAKERSFIELD QUAKE</h1>
        <img class="hero-rune" src="media/gifs/quake_rune_spin.gif" alt="Quake Rune">
      </div>

      <div class="download-cta-wrap">
        <a class="download-cta-btn" href="{DOWNLOAD_URL}" download="BakersfieldLAN.zip">DOWNLOAD</a>
        <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;justify-content:center;font-size:12px;color:#d8d0e0;">
          <span>Unzip &amp; run <code>Play.cmd</code></span>
          <span>·</span>
          <span>Server: <span class="console-cmd">connect 72.62.241.93:26000</span></span>
          <button type="button" id="btn-copy-connect" class="win98-btn">Copy</button>
        </div>
      </div>

      <div class="grid-3" style="margin-top:10px;">
        {shot_card("milky_pinklady_attack.gif", "Pink Lady (Key 5)", "GIF", is_gif=True)}
        {shot_card("wewcannon_bend_blast.gif", "WEW Cannon (Key G)", "GIF", is_gif=True)}
        {shot_card("wm_gibs.gif", "Wheelman Blast", "GIF", contain=True, is_gif=True)}
      </div>
    </div>

    <div class="fire-divider"></div>

    <!-- ==================== 6 INTERACTIVE 3D / SPRITE ASSETS ==================== -->
    <div class="sec-hdr pink">
      <h2 class="sec-title">WEAPONS &amp; ASSETS</h2>
      <div class="sec-sub">Drag to Spin · Scroll to Zoom</div>
    </div>

    <table class="geo-table">
      <tr>
        <td class="geo-cell">
          <div class="grid-3">
            {vp_card("pinklady_spr", "Pink Lady (Key 5)", "SPRITE",
                     "Chases players &amp; whites out your screen in milk.", theme="pink")}
            {vp_card("v_wewcannon", "WEW Cannon (Key G)", "3D MD3",
                     "Hold fire to bend barrel +58&deg; &amp; launch Wheelman.", theme="silver", pov=False, zoom=0.88)}
            {vp_card("wheelman_dance_spr", "Survivor Wheelman", "SPRITE",
                     "8 post-explosion dances — click Anim to cycle.", theme="silver")}
            {vp_card("megaman", "Mega Man (Key 9)", "3D MD3",
                     "Boat-motor headcrab — click Skin for Blue Shell.", theme="cyan")}
            {vp_card("pickle_diva", "Pickle Surprise (Key X)", "SPRITE",
                     "Giant screaming pickle trap — 4 skins.", theme="lime")}
            {vp_card("pink_supercar", "V12 Supercar", "3D MD3",
                     "Rideable cruiser in bklan4 &amp; bklan5.", theme="pink", zoom=0.88)}
          </div>
        </td>
      </tr>
    </table>

    <div class="fire-divider"></div>

    <!-- ==================== 4 MAPS ==================== -->
    <div class="sec-hdr">
      <h2 class="sec-title">MAPS</h2>
      <div class="sec-sub">Click Any Map to Enlarge</div>
    </div>

    <table class="geo-table gold-theme">
      <tr>
        <td class="geo-cell">
          <div class="grid-2">
            {shot_card("map_bklan_larry_facade.jpg", "bklan5 — Warehouse, Casino &amp; Room 120A", "BKLAN5")}
            {shot_card("map_nana_arch.jpg", "nanaplaza — 3-Tier Neon Courtyard", "NANAPLAZA")}
            {shot_card("map_fox_marquee.jpg", "fox — Fox Theater &amp; Padre Hotel", "FOX")}
            {shot_card("map_spruce_water_tower.jpg", "spruce — Streets &amp; 105-ft Water Tower", "SPRUCE")}
          </div>
        </td>
      </tr>
    </table>

    <div class="fire-divider"></div>

    <!-- ==================== UNDERDOG RULES + BOTTOM DOWNLOAD ==================== -->
    <div class="sec-hdr lime">
      <h2 class="sec-title">UNDERDOG RULES</h2>
    </div>

    <table class="geo-table toxic-theme">
      <tr>
        <td class="geo-cell">
          <ul class="rules-list">
            <li><b>Behind in Frags:</b> Spawn with up to <b>200 HP + 200 Red Armor</b>, faster reloads, and up to <b>+50% damage</b> vs players ahead.</li>
            <li><b>11+ Frags Behind:</b> Your next <b>Mega Man (Key 9)</b> turns into a <b>Blue Shell</b> that hunts #1 across the map.</li>
            <li><b>#1 Leader Heat:</b> Leading the lobby lights you up gold, puts a <b>+1 frag bounty</b> on your head, and reveals you through walls.</li>
          </ul>
        </td>
      </tr>
    </table>

    <div class="download-cta-wrap" style="margin:20px 0 8px 0;">
      <a class="download-cta-btn" href="{DOWNLOAD_URL}" download="BakersfieldLAN.zip">DOWNLOAD</a>
    </div>

  </div>

  <!-- FULLSCREEN 3D VIEWER MODAL -->
  <div id="holodeck-modal">
    <div class="holo-modal-top">
      <div>3D &amp; Sprite Viewer — <span id="holo-title">Asset</span></div>
      <button type="button" id="holo-close" class="win98-btn" style="background:#aa0000;color:#fff;">✖ CLOSE [ESC]</button>
    </div>

    <div id="holo-sidebar-list" class="holo-sidebar"></div>

    <div id="holodeck-stage">
      <canvas id="holo-2d-canvas"></canvas>
      <div class="holo-hud-overlay">
        <div class="holo-hud-box">
          <div id="holo-meta" style="font-family:'Courier New',monospace;font-size:11px;color:#7affff;margin-bottom:3px;"></div>
          <div id="holo-desc" style="font-size:12px;color:#f4ecdc;"></div>
          <div id="holo-skin-btns" style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;"></div>
        </div>
      </div>
    </div>

    <div class="holo-modal-bot">
      <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">
        <select id="holo-clip-sel" style="font-size:11px;padding:2px 4px;background:#0e0a16;color:#fff;border:1px solid #8866aa;"></select>
        <button type="button" id="holo-btn-play" class="win98-btn">⏸ Pause</button>
        <input id="holo-scrub" type="range" min="0" max="30" step="0.25" value="0" style="width:120px;">
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:5px;align-items:center;">
        <button type="button" id="holo-btn-spin" class="win98-btn">🔄 Auto-Spin</button>
        <button type="button" id="holo-btn-pov" class="win98-btn">👁 1st-Person POV</button>
        <button type="button" id="holo-btn-2d" class="win98-btn">🖼 2D Sprite</button>
        <button type="button" id="holo-btn-wire" class="win98-btn">🕸 Wireframe</button>
        <button type="button" id="holo-btn-reset" class="win98-btn">🎯 Reset</button>
      </div>
    </div>
  </div>

  <!-- IMAGE LIGHTBOX -->
  <div id="lightbox-modal">
    <div class="lb-window">
      <div class="lb-titlebar">
        <span><span id="lb-counter">[1/1]</span></span>
        <button type="button" id="lb-close" class="win98-btn" style="padding:0 6px;">✖</button>
      </div>
      <div class="lb-body">
        <img id="lb-img" src="" alt="Screenshot">
      </div>
      <div class="lb-cap">
        <button type="button" id="lb-prev" class="win98-btn">◀ Prev</button>
        <span id="lb-caption">Caption</span>
        <button type="button" id="lb-next" class="win98-btn">Next ▶</button>
      </div>
    </div>
  </div>

  <script src="assets/models_data.js"></script>
  <script src="viewer.js"></script>
</body>
</html>
"""


def main():
    from PIL import Image
    fac_dst = os.path.join(FANPAGE_DIR, "media", "shots", "map_bklan_larry_facade.jpg")
    fac_src = os.path.abspath(os.path.join(MOD_ROOT, "..", "_bakersfield_dev", "zb4_11_larry_front.png"))
    if not os.path.isfile(fac_dst) and os.path.isfile(fac_src):
        os.makedirs(os.path.dirname(fac_dst), exist_ok=True)
        im = Image.open(fac_src).convert("RGB")
        if im.width > 960:
            im = im.resize((960, round(im.height * (960 / im.width))), Image.Resampling.LANCZOS)
        im.save(fac_dst, "JPEG", quality=86)

    keep_6 = [
        "pinklady_spr",
        "v_wewcannon",
        "wheelman_dance_spr",
        "megaman",
        "pickle_diva",
        "pink_supercar",
    ]
    valid_models = slim_models_js(keep_6)

    clean_html = re.sub(r"`([^`]+)`", r"<code>\1</code>", HTML)
    with open(INDEX_OUT, "w", encoding="utf-8") as f:
        f.write(clean_html)

    ref_srcs = re.findall(r'src="([^"]+)"', clean_html)
    missing_files = []
    for rel in ref_srcs:
        if not rel or rel.startswith(("http://", "https://", "data:")):
            continue
        p = os.path.join(FANPAGE_DIR, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            missing_files.append(rel)

    ref_models = re.findall(r'data-model="([^"]+)"', clean_html)
    missing_models = [mid for mid in ref_models if mid not in valid_models]

    # Assert 0 fake quotes / fake GeoCities gimmicks / unused assets
    forbidden_patterns = [
        "TimesSquare", "Guestbook", "GUESTBOOK", "WebRing", "006610", "PaintShop",
        "Camper661", "WheelmanVictim", "DairyQueen", "Netscape", "LOL.BAT", "netsend-popup",
        "pinklady3d", "pocket_rocket", "david_spr", "preg_spr", "wm_thermonuclear",
    ]
    leaked = [pat for pat in forbidden_patterns if pat in clean_html]
    assert not leaked, f"Forbidden fake/unused text leaked into index.html: {leaked}"

    assert not missing_files, f"Broken media paths: {missing_files}"
    assert not missing_models, f"Broken model IDs: {missing_models}"

    # Prune unreferenced media files (shots, gifs, sfx, ui)
    css_txt = open(os.path.join(FANPAGE_DIR, "styles.css"), "r", encoding="utf-8").read()
    vjs_txt = open(os.path.join(FANPAGE_DIR, "viewer.js"), "r", encoding="utf-8").read()
    all_txt = clean_html + "\n" + css_txt + "\n" + vjs_txt
    pruned = 0
    for sub in ("shots", "gifs", "sfx", "ui"):
        sub_dir = os.path.join(FANPAGE_DIR, "media", sub)
        if not os.path.isdir(sub_dir):
            continue
        for fn in os.listdir(sub_dir):
            if f"media/{sub}/{fn}" not in all_txt:
                os.remove(os.path.join(sub_dir, fn))
                pruned += 1

    n_imgs = len(re.findall(r"<img ", clean_html))
    print(f"[HTML OK] Wrote {INDEX_OUT} ({os.path.getsize(INDEX_OUT)/1024:.1f} KB) | models_data.js: {os.path.getsize(MODELS_JS)/1e6:.2f} MB | Pruned {pruned} media files")
    print(f"  Inline <img> tags: {n_imgs} | Inline 3D/Sprite Stages: {len(ref_models)}")


if __name__ == "__main__":
    main()
