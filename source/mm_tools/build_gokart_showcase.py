#!/usr/bin/env python3
"""build_gokart_showcase.py

Builds scripts/gokart.shader and the 100% self-contained offline WebGL2 3D
Go-Kart Showcase (gokart_showcase.html) from:
  - progs/gokart_{1..6}.md3
  - progs/gk{1..6}_*.png
  - source/mm_tools/out/gokart_{1..6}_meta.json
  - source/mm_tools/gokart_showcase.template.html

By default deploys gokart_showcase.html to VPS root@72.62.241.93:22:
  - /var/www/megaman/gokart_showcase.html
      -> https://bakersfield.larrywew.fun/gokart_showcase.html
      -> https://davidbrazil.site/megaman/gokart_showcase.html
  - /var/www/larrywew/bakersfield-quake/gokarts.html (if directory exists)
      -> https://larrywew.fun/bakersfield-quake/gokarts.html
Does NOT touch /opt/quake or restart the Quake game server.

Usage:
    python source/mm_tools/build_gokart_showcase.py --no-deploy
    python source/mm_tools/build_gokart_showcase.py
"""
import argparse
import base64
import gzip
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib  # noqa: E402

OUT_DIR = os.path.join(HERE, "out")
TEMPLATE_HTML = os.path.join(HERE, "gokart_showcase.template.html")
OUT_HTML = os.path.join(MOD, "gokart_showcase.html")
OUT_SHADER = os.path.join(MOD, "scripts", "gokart.shader")

VPS_HOST = "root@72.62.241.93"
LIVE_URLS = [
    "https://bakersfield.larrywew.fun/gokart_showcase.html",
    "https://davidbrazil.site/megaman/gokart_showcase.html",
    "https://larrywew.fun/bakersfield-quake/gokarts.html",
]

KART_SPECS = [
    (1, "GO-KART #1", "original"),
    (2, "GO-KART #2", "original"),
    (3, "GO-KART #3", "original"),
    (4, "MEGA KART #4", "megaman"),
    (5, "MEGA KART #5", "megaman"),
    (6, "MEGA KART #6", "megaman"),
]


class ArenaPacker:
    def __init__(self):
        self.buf = bytearray()
        self.tex_map = {}
        self.tex_list = []

    def add_bytes(self, raw_bytes):
        while len(self.buf) & 7:
            self.buf.append(0)
        off = len(self.buf)
        self.buf.extend(raw_bytes)
        return [off, len(raw_bytes)]

    def add_tex_file(self, path, max_dim=1024, force_png=False):
        abs_p = os.path.abspath(path)
        if abs_p in self.tex_map:
            return self.tex_map[abs_p]
        im = Image.open(abs_p)
        im.load()
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        w0, h0 = im.size
        if max_dim and max(w0, h0) > max_dim:
            sc = max_dim / float(max(w0, h0))
            im = im.resize(
                (max(1, round(w0 * sc)), max(1, round(h0 * sc))),
                Image.Resampling.LANCZOS,
            )
        bio = io.BytesIO()
        if force_png or im.mode == "RGBA":
            im.save(bio, "PNG", optimize=True)
            mime = "image/png"
        else:
            im.save(bio, "JPEG", quality=90, optimize=True)
            mime = "image/jpeg"
        uri = f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.tex_list)
        self.tex_map[abs_p] = idx
        self.tex_list.append(dict(uri=uri, w=im.size[0], h=im.size[1]))
        return idx


def build_wire_edges(tri_arr):
    e01 = np.sort(tri_arr[:, [0, 1]], axis=1)
    e12 = np.sort(tri_arr[:, [1, 2]], axis=1)
    e20 = np.sort(tri_arr[:, [2, 0]], axis=1)
    return np.unique(np.vstack([e01, e12, e20]), axis=0).astype("<u2")


def resolve_tex_path(tex_ref):
    rel = tex_ref.replace("\\", "/").lstrip("/")
    if not rel.startswith("progs/") and not os.path.isfile(os.path.join(MOD, rel)):
        rel = "progs/" + rel
    cand = os.path.join(MOD, rel)
    if os.path.isfile(cand):
        return cand
    for ext in (".png", ".tga", ".jpg", ".jpeg"):
        p = os.path.join(MOD, os.path.splitext(rel)[0] + ext)
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(f"Missing texture file for '{tex_ref}' (checked {cand})")


def is_flame_shader(shader_name, surf_name="", mat_cfg=None):
    mat_cfg = mat_cfg or {}
    s_low = shader_name.lower()
    n_low = surf_name.lower()
    return (
        "flame" in s_low
        or "flame" in n_low
        or bool(mat_cfg.get("additive"))
        or bool(mat_cfg.get("unlit"))
    )


def generate_shader_file(kart_metas):
    """Generates scripts/gokart.shader covering all shaders in gokart_{1..6}_meta.json."""
    os.makedirs(os.path.dirname(OUT_SHADER), exist_ok=True)
    seen = {}
    order = []

    for meta in kart_metas:
        textures = meta.get("textures", {})
        materials = meta.get("materials", {})
        for sh_name, tex_path in textures.items():
            sh_clean = sh_name.strip()
            sh_key = sh_clean.lower()
            if sh_key and sh_key not in seen:
                seen[sh_key] = (sh_clean, tex_path, materials.get(sh_name, materials.get(sh_clean, {})))
                order.append(sh_key)
        for sh_name, mat_cfg in materials.items():
            sh_clean = sh_name.strip()
            sh_key = sh_clean.lower()
            if sh_key and sh_key not in seen:
                seen[sh_key] = (sh_clean, sh_clean + ".png", mat_cfg)
                order.append(sh_key)

    lines = [
        "// written by source/mm_tools/build_gokart_showcase.py",
        "// Go-Kart shaders for BakersfieldQuake (progs/gokart_1..6.md3)",
        "",
    ]
    for sh_key in order:
        sh_name, tex_path, mat_cfg = seen[sh_key]
        map_ref = os.path.splitext(tex_path.replace("\\", "/"))[0]
        if not map_ref.startswith("progs/"):
            map_ref = "progs/" + map_ref
        flame = is_flame_shader(sh_name, "", mat_cfg)
        lines.append(sh_name)
        lines.append("{")
        lines.append("\tcull none")
        lines.append("\t{")
        lines.append(f"\t\tmap {map_ref}")
        if flame:
            lines.append("\t\tblendfunc add")
            lines.append("\t\trgbGen vertex")
        else:
            lines.append("\t\trgbGen lightingDiffuse")
        lines.append("\t}")
        lines.append("}")
        lines.append("")

    content = "\n".join(lines)
    with open(OUT_SHADER, "w", encoding="ascii", newline="\n") as f:
        f.write(content)
    print(f"   [OK] {OUT_SHADER} ({len(order)} shaders)", flush=True)
    return OUT_SHADER


def pack_md3_to_arena(packer, md3_path, meta):
    m = md3lib.read(md3_path)
    nf = m["nframes"]
    assert nf == 64, f"Expected 64 frames in {md3_path}, got {nf}"

    textures_cfg = meta.get("textures", {})
    materials_cfg = meta.get("materials", {})

    surfs_out = []
    tot_v, tot_t = 0, 0
    idle_min = np.array([1e9, 1e9, 1e9], dtype=np.float32)
    idle_max = np.array([-1e9, -1e9, -1e9], dtype=np.float32)
    super_min = np.array([1e9, 1e9, 1e9], dtype=np.float32)
    super_max = np.array([-1e9, -1e9, -1e9], dtype=np.float32)

    for s in m["surfaces"]:
        nv = len(s["st"])
        uv_arr = np.asarray(s["st"], dtype="<f4")
        tri_arr = np.asarray(s["tris"], dtype="<u2")
        edges_arr = build_wire_edges(tri_arr)
        nt = len(tri_arr)
        tot_v += nv
        tot_t += nt

        all_v = np.stack([np.asarray(fr[0], dtype=np.float32) for fr in s["frames"]], axis=0)
        all_n = np.stack([np.asarray(fr[1], dtype=np.float32) for fr in s["frames"]], axis=0)

        sh_name = s["shader"]
        mat_cfg = materials_cfg.get(sh_name, {})
        flame = is_flame_shader(sh_name, s["name"], mat_cfg)

        if not flame:
            idle_min = np.minimum(idle_min, all_v[:12].min(axis=(0, 1)))
            idle_max = np.maximum(idle_max, all_v[:12].max(axis=(0, 1)))
        super_min = np.minimum(super_min, all_v[28:44].min(axis=(0, 1)))
        super_max = np.maximum(super_max, all_v[28:44].max(axis=(0, 1)))

        pos_u16 = np.zeros((nf, nv, 4), dtype="<i2")
        pos_u16[:, :, :3] = np.clip(np.round(all_v * 64.0), -32767, 32767).astype("<i2")
        dpos = pos_u16.copy()
        dpos[1:] = (
            (pos_u16[1:].astype(np.int32) - pos_u16[:-1].astype(np.int32)) & 0xFFFF
        ).astype("<u2").view("<i2")

        n_len = np.maximum(np.linalg.norm(all_n, axis=2, keepdims=True), 1e-8)
        nrm_i8 = np.zeros((nf, nv, 4), dtype="<i1")
        nrm_i8[:, :, :3] = np.clip(np.round((all_n / n_len) * 127.0), -127, 127).astype("<i1")
        dnrm = nrm_i8.copy()
        dnrm[1:] = (
            (nrm_i8[1:].astype(np.int32) - nrm_i8[:-1].astype(np.int32)) & 0xFF
        ).astype("<u1").view("<i1")

        tex_ref = textures_cfg.get(sh_name, sh_name + ".png")
        tex_abs = resolve_tex_path(tex_ref)
        tex_idx = packer.add_tex_file(tex_abs, max_dim=1024, force_png=flame)

        surfs_out.append(
            dict(
                name=s["name"],
                shader=sh_name,
                nv=nv,
                nt=nt,
                ne=len(edges_arr),
                posScale=1.0 / 64.0,
                tris=packer.add_bytes(tri_arr.tobytes()),
                edges=packer.add_bytes(edges_arr.tobytes()),
                uv=packer.add_bytes(uv_arr.tobytes()),
                pos=packer.add_bytes(dpos.tobytes()),
                nrm=packer.add_bytes(dnrm.tobytes()),
                tex=tex_idx,
                metallic=float(mat_cfg.get("metallic", 0.35)),
                roughness=float(mat_cfg.get("roughness", 0.40)),
                spec=float(mat_cfg.get("spec", 0.55)),
                unlit=1 if flame else 0,
                additive=1 if flame else 0,
            )
        )

    packed = dict(nf=nf, nv=tot_v, nt=tot_t, surfaces=surfs_out)
    bbox_idle = [round(float(x), 1) for x in idle_min] + [round(float(x), 1) for x in idle_max]
    bbox_super = [round(float(x), 1) for x in super_min] + [round(float(x), 1) for x in super_max]
    return packed, bbox_idle, bbox_super


def validate_html_js(html):
    assert not re.search(r'<script[^>]+src\s*=\s*["\']https?://', html, re.I), "External <script src> found!"
    assert not re.search(r'<link[^>]+href\s*=\s*["\']https?://', html, re.I), "External <link href> found!"
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    assert scripts, "No inline <script> blocks found in template"

    node_bin = shutil.which("node")
    if node_bin:
        for i, s in enumerate(scripts):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tf:
                tf.write(s)
                tp = tf.name
            try:
                res = subprocess.run([node_bin, "--check", tp], capture_output=True, text=True)
            finally:
                if os.path.exists(tp):
                    os.unlink(tp)
            assert res.returncode == 0, f"JS syntax error in block {i}: {res.stderr}"
        print(f"   [OK] node --check passed ({len(scripts)} script blocks)", flush=True)
    else:
        for i, s in enumerate(scripts):
            assert s.count("{") == s.count("}"), f"Unbalanced braces in script block {i}"
        print(f"   [OK] python script sanity check passed ({len(scripts)} blocks)", flush=True)


def build_showcase():
    print("1. Loading gokart_{1..6}_meta.json & generating scripts/gokart.shader...", flush=True)
    metas = []
    for num, _, _ in KART_SPECS:
        meta_path = os.path.join(OUT_DIR, f"gokart_{num}_meta.json")
        assert os.path.isfile(meta_path), f"Missing metadata JSON: {meta_path}"
        with open(meta_path, "r", encoding="utf-8") as f:
            metas.append(json.load(f))

    driver_meta_path = os.path.join(OUT_DIR, "gokart_driver_meta.json")
    assert os.path.isfile(driver_meta_path), f"Missing driver metadata JSON: {driver_meta_path}"
    with open(driver_meta_path, "r", encoding="utf-8") as f:
        driver_meta = json.load(f)

    extra_metas = [driver_meta]
    shell_meta_path = os.path.join(OUT_DIR, "gk_shell_meta.json")
    if os.path.isfile(shell_meta_path):
        with open(shell_meta_path, "r", encoding="utf-8") as f:
            extra_metas.append(json.load(f))

    generate_shader_file(metas + extra_metas)

    print("2. Packing progs/gokart_{1..6}.md3 + gokart_driver.md3 + PNG textures into ArenaPacker...", flush=True)
    packer = ArenaPacker()
    driver_md3_abs = os.path.join(MOD, "progs", "gokart_driver.md3")
    assert os.path.isfile(driver_md3_abs), f"Missing driver MD3: {driver_md3_abs}"
    driver_packed, _, _ = pack_md3_to_arena(packer, driver_md3_abs, driver_meta)
    print(f"   [OK] progs/gokart_driver.md3 | 64f | 1 surf | {driver_packed['nv']:4d}v / {driver_packed['nt']:4d}t", flush=True)
    karts_out = []

    for (num, badge, group), meta in zip(KART_SPECS, metas):
        md3_rel = f"progs/gokart_{num}.md3"
        skin_rel = f"progs/gokart_{num}.md3_0.skin"
        md3_abs = os.path.join(MOD, md3_rel)
        assert os.path.isfile(md3_abs), f"Missing MD3: {md3_abs}"

        packed, bbox_idle, bbox_super = pack_md3_to_arena(packer, md3_abs, meta)
        print(
            f"   [OK] {md3_rel} | 64f | {len(packed['surfaces']):2d} surfs | "
            f"{packed['nv']:4d}v / {packed['nt']:4d}t | idle Z=[{bbox_idle[2]:+.2f}..{bbox_idle[5]:+.2f}]",
            flush=True,
        )
        karts_out.append(
            dict(
                id=meta.get("id", f"kart{num}"),
                num=num,
                group=group,
                badge=badge,
                name=meta["name"],
                tagline=meta.get("tagline", ""),
                palette=meta.get("palette", []),
                description=meta.get("description", ""),
                highlights=meta.get("highlights", []),
                seat_pos=meta.get("seat_pos", {"x": -9.0, "y": 0.0, "z": 9.5}),
                steer_pos=meta.get("steer_pos", {"x": 13.0, "y": 0.0, "z": 24.0}),
                exhaust_tips=meta.get("exhaust_tips", []),
                md3File=md3_rel,
                skinFile=skin_rel if os.path.isfile(os.path.join(MOD, skin_rel)) else "",
                bboxIdle=bbox_idle,
                bboxSuper=bbox_super,
                model=packed,
            )
        )

    bin_gz = base64.b64encode(gzip.compress(bytes(packer.buf), compresslevel=9)).decode("ascii")
    payload = dict(
        karts=karts_out,
        driverModel=driver_packed,
        textures=packer.tex_list,
        binGz=bin_gz,
        shaderFile="scripts/gokart.shader",
    )

    print("3. Rendering gokart_showcase.html & validating JS...", flush=True)
    assert os.path.isfile(TEMPLATE_HTML), f"Missing template: {TEMPLATE_HTML}"
    with open(TEMPLATE_HTML, "r", encoding="utf-8") as f:
        tpl = f.read()
    assert "/*__GOKART_DATA__*/null" in tpl, "Missing /*__GOKART_DATA__*/null marker in template"
    html = tpl.replace("/*__GOKART_DATA__*/null", json.dumps(payload, separators=(",", ":")), 1)
    validate_html_js(html)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    sz_kb = os.path.getsize(OUT_HTML) / 1024.0
    print(f"   [OK] {OUT_HTML} ({sz_kb:.1f} KB, {len(packer.tex_list)} textures)", flush=True)
    return OUT_HTML


def deploy_to_vps(html_path):
    print(f"4. Deploying gokart_showcase.html to VPS {VPS_HOST}:22 ...", flush=True)
    assert os.path.isfile(html_path)

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=6) as tf:
        tf.add(html_path, arcname="web_megaman/gokart_showcase.html")
        tf.add(html_path, arcname="web_larrywew/gokarts.html")
    payload = buf.getvalue()
    print(f"   Streaming {len(payload) / 1024.0:.1f} KB tarball to {VPS_HOST} ...", flush=True)

    remote_cmd = (
        "set -e; "
        "TMPD=$(mktemp -d); "
        "tar -xzf - -C \"$TMPD\"; "
        "mkdir -p /var/www/megaman; "
        "cp -f \"$TMPD/web_megaman/gokart_showcase.html\" /var/www/megaman/gokart_showcase.html; "
        "chmod a+r /var/www/megaman/gokart_showcase.html; "
        "if [ -d /var/www/larrywew/bakersfield-quake ]; then "
        "  cp -f \"$TMPD/web_larrywew/gokarts.html\" /var/www/larrywew/bakersfield-quake/gokarts.html; "
        "  chmod a+r /var/www/larrywew/bakersfield-quake/gokarts.html; "
        "fi; "
        "rm -rf \"$TMPD\"; "
        "ls -lh /var/www/megaman/gokart_showcase.html /var/www/larrywew/bakersfield-quake/gokarts.html 2>/dev/null || ls -lh /var/www/megaman/gokart_showcase.html"
    )
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-p", "22", VPS_HOST, remote_cmd],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    print(proc.stdout.decode("utf-8", errors="replace").strip(), flush=True)


def verify_live_urls():
    print("5. Verifying HTTP 200 & >100KB on live HTTPS URLs...", flush=True)
    for u in LIVE_URLS:
        req = urllib.request.Request(u, method="GET", headers={"User-Agent": "GoKartShowcaseVerifier/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read()
            print(f"   [HTTP {resp.status}] {u} ({len(body)} bytes)", flush=True)
            assert resp.status == 200, f"Unexpected HTTP status {resp.status} for {u}"
            assert len(body) > 100_000, f"Live response too small ({len(body)} bytes) for {u}"


def main():
    parser = argparse.ArgumentParser(description="Build & deploy BakersfieldQuake 3D Go-Kart Showcase")
    parser.add_argument("--no-deploy", action="store_true", help="Build locally without VPS upload")
    args = parser.parse_args()

    out_html = build_showcase()
    if not args.no_deploy:
        deploy_to_vps(out_html)
        verify_live_urls()


if __name__ == "__main__":
    main()
