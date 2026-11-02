#!/usr/bin/env python3
"""Server-side packager run on VPS (root@72.62.241.93) to build:
  /var/www/megaman/custom-assets/
    raw/                        Every single individual custom asset file (progs, sound, textures, gfx, scripts, glb, vault, maps)
    thumbs/textures/            Fast 224px WebP thumbnails for all 1,044 custom textures & skyboxes
    bundles/<canonical_id>.zip  Self-contained Quake asset pack (.zip) for EVERY SINGLE 3D model & sprite (362 packs!)
    downloads/                  Master 'Download Everything' ZIP + 7 Category Sub-ZIPs
    vps_manifest.json           Exact file counts, sizes, and metadata for the web UI
"""
import glob
import io
import json
import os
import re
import shutil
import struct
import time
import zipfile
from PIL import Image

QUAKE_DIR = "/opt/quake/BakersfieldQuake"
PK3_PATH = os.path.join(QUAKE_DIR, "bakersfield.pk3")
VAULT_ZIP = "/tmp/vault_extras.zip"
OUT_ROOT = "/var/www/megaman/custom-assets"
RAW_DIR = os.path.join(OUT_ROOT, "raw")
THUMBS_DIR = os.path.join(OUT_ROOT, "thumbs")
BUNDLES_DIR = os.path.join(OUT_ROOT, "bundles")
DL_DIR = os.path.join(OUT_ROOT, "downloads")


def canon_id(rel_path):
    return rel_path.replace("\\", "/").lstrip("/").lower().replace("/", "__").replace(".", "_")


def classify_model_cat(rel_low):
    bn = os.path.basename(rel_low)
    if (
        bn.startswith(("veh_", "skyveh_", "pink_supercar", "van_walkin", "jesskart"))
        or rel_low == "progs/fox/get_bus.md3"
        or bn.startswith(("sr_vehicle_", "sr_carframe_", "sr_vehiclesupport_"))
    ):
        return "cars"
    if (
        bn.startswith((
            "v_", "p_", "g_", "megaman.", "mm_explode", "mm_wheel", "mm_axle", "mm_bar", "mm_cap", "mm_frag",
            "wc_bar", "milksplat", "pickle_bomb", "pickle_throw", "pickle_gib", "proj_mysterybox",
            "netsend_", "ltg_v3d", "ltg_view", "ltg_p.", "ltg_g.", "ltg_aura", "ltg_laser", "ltg_type_",
            "goo.", "sight.", "spark_", "turr", "tgib", "hackmon", "hd_", "paddle", "fg_pongball",
            "sledge", "ccc.", "laser.", "zap", "grenade.", "jw_wave", "fr_johnhand", "jetpack", "aura.",
            "girl."
        ))
    ):
        return "guns"
    if (
        rel_low.endswith((".spr32", ".spr"))
        or bn in (
            "pinklady.md3", "pickle.md3", "ltg_head.md3", "floathead.mdl",
            "john_bird_head.md3", "johnhead3d.md3", "mm_suit_rider.md3", "mm_squat_rider.md3",
            "bigears.md3", "fedora.md3", "robeguy.mdl", "suitguy.mdl", "wifeguy.mdl",
        )
    ):
        return "sprites"
    if rel_low.startswith("progs/fox/"):
        return "fox_props"
    if bn.startswith("sr_") and not bn.startswith("sr_computer_"):
        return "warehouse"
    return "lan_props"


def parse_shaders(raw_dir):
    shaders = {}
    shader_sources = {}
    for sp in sorted(glob.glob(os.path.join(raw_dir, "scripts", "*.shader"))):
        rel_s = "scripts/" + os.path.basename(sp)
        raw_txt = open(sp, "r", encoding="utf-8", errors="replace").read()
        clean = re.sub(r"//.*", "", raw_txt)
        pos = 0
        while True:
            m = re.search(r"([^\s\{\}]+)\s*\{", clean[pos:])
            if not m:
                break
            sh_name = m.group(1).strip().lower()
            bstart = pos + m.end()
            depth = 1
            i = bstart
            while i < len(clean) and depth > 0:
                if clean[i] == "{":
                    depth += 1
                elif clean[i] == "}":
                    depth -= 1
                i += 1
            body = clean[bstart:i - 1]
            shaders[sh_name] = body
            shader_sources[sh_name] = rel_s
            pos = i
    return shaders, shader_sources


def main():
    t0 = time.time()
    for d in (OUT_ROOT, RAW_DIR, THUMBS_DIR, BUNDLES_DIR, DL_DIR):
        os.makedirs(d, exist_ok=True)

    print("1. Extracting bakersfield.pk3 + vault_extras.zip + GLBs into raw/ ...", flush=True)
    if not os.path.isdir(os.path.join(RAW_DIR, "progs")):
        with zipfile.ZipFile(PK3_PATH, "r") as z:
            z.extractall(RAW_DIR)

    if os.path.isfile(VAULT_ZIP) and not os.path.isdir(os.path.join(RAW_DIR, "vault")):
        with zipfile.ZipFile(VAULT_ZIP, "r") as z:
            z.extractall(RAW_DIR)

    os.makedirs(os.path.join(RAW_DIR, "glb"), exist_ok=True)
    for gp in sorted(glob.glob(os.path.join(QUAKE_DIR, "*.glb"))):
        shutil.copy2(gp, os.path.join(RAW_DIR, "glb", os.path.basename(gp)))
    mm1 = "/var/www/megaman/megaman1.glb"
    if os.path.isfile(mm1):
        shutil.copy2(mm1, os.path.join(RAW_DIR, "glb", "megaman1.glb"))

    for extra_fn in ("effectinfo.txt", "intro.dem", "readme.txt"):
        src_p = os.path.join(QUAKE_DIR, extra_fn)
        if os.path.isfile(src_p):
            shutil.copy2(src_p, os.path.join(RAW_DIR, extra_fn))

    # Symlink maps/*.bsp & *.lit so they're downloadable at raw/maps/... without duplicating 540 MB!
    maps_dst = os.path.join(RAW_DIR, "maps")
    os.makedirs(maps_dst, exist_ok=True)
    for mp in sorted(glob.glob(os.path.join(QUAKE_DIR, "maps", "*"))):
        if os.path.isfile(mp):
            dst_p = os.path.join(maps_dst, os.path.basename(mp))
            if os.path.lexists(dst_p):
                os.remove(dst_p)
            os.symlink(mp, dst_p)

    # Index all non-symlink files in RAW_DIR
    all_raw = {}
    for root, dirs, files in os.walk(RAW_DIR, followlinks=False):
        for fn in files:
            fp = os.path.join(root, fn)
            if os.path.islink(fp):
                continue
            rel = os.path.relpath(fp, RAW_DIR).replace("\\", "/")
            all_raw[rel.lower()] = rel

    print(f"   Indexed {len(all_raw)} raw custom files in {time.time()-t0:.1f}s", flush=True)

    # Map GLBs to canonical model stems
    glb_by_model = {
        "progs/megaman.md3": "glb/megaman1.glb",
        "progs/mm_explode.md3": "glb/megaman_explode.glb",
        "progs/v_mysterybox.md3": "glb/mystery_box_weapon.glb",
        "progs/proj_mysterybox.md3": "glb/mystery_box_projectile.glb",
        "progs/pink_supercar.md3": "glb/pink_supercar.glb",
        "progs/veh_coupe.md3": "glb/veh_coupe.glb",
        "progs/veh_gtcar.md3": "glb/veh_gtcar.glb",
        "progs/veh_hdtruck.md3": "glb/veh_hdtruck.glb",
        "progs/veh_schoolbus.md3": "glb/veh_schoolbus.glb",
        "progs/veh_sedan.md3": "glb/veh_sedan.glb",
        "progs/veh_truck.md3": "glb/veh_truck.glb",
        "progs/veh_van.md3": "glb/veh_van.glb",
        "progs/g_wewcannon.md3": "glb/wew_cannon_pickup.glb",
        "progs/v_wewcannon.md3": "glb/wew_cannon_weapon.glb",
        "progs/greensuit_wheelman.spr32": "glb/greensuit_wheelman.glb",
    }

    shaders, shader_sources = parse_shaders(RAW_DIR)

    def resolve_tex_files(ref, mdl_dir, visited=None):
        found = set()
        used_shaders = set()
        if not ref:
            return found, used_shaders
        if visited is None:
            visited = set()
        r = ref.replace("\\", "/").lstrip("/").lower()
        key = (r, mdl_dir)
        if key in visited:
            return found, used_shaders
        visited.add(key)
        stem = os.path.splitext(r)[0] if r.endswith((".png", ".tga", ".jpg", ".jpeg")) else r
        bn = os.path.basename(stem)
        for cand in (
            r, stem + ".png", stem + ".tga", stem + ".jpg",
            f"{mdl_dir}/{bn}.png", f"{mdl_dir}/{bn}.tga", f"{mdl_dir}/{bn}.jpg",
            f"progs/{bn}.png", f"progs/{bn}.tga", f"progs/{bn}.jpg",
            f"textures/{bn}.png", f"textures/{bn}.tga",
        ):
            if cand in all_raw:
                found.add(all_raw[cand])
            glow_cand = os.path.splitext(cand)[0] + "_glow.png"
            if glow_cand in all_raw:
                found.add(all_raw[glow_cand])

        for sk in (stem, r):
            if sk in shaders:
                if sk in shader_sources:
                    used_shaders.add(shader_sources[sk])
                body = shaders[sk]
                for am in re.finditer(r"animmap\s+[\d\.]+\s+([^\r\n\}]+)", body, re.I):
                    for tok in am.group(1).split():
                        f2, s2 = resolve_tex_files(tok, mdl_dir, visited)
                        found.update(f2)
                        used_shaders.update(s2)
                for mm in re.finditer(r"\bmap\s+([^\s\r\n\}]+)", body, re.I):
                    tok = mm.group(1)
                    if not tok.startswith("$"):
                        f2, s2 = resolve_tex_files(tok, mdl_dir, visited)
                        found.update(f2)
                        used_shaders.update(s2)
        return found, used_shaders

    print("2. Building 362 individual self-contained model/sprite .zip bundles...", flush=True)
    model_rels = sorted(
        real for k, real in all_raw.items()
        if k.endswith((".md3", ".mdl", ".spr32", ".spr"))
    )
    bundle_info = {}
    cat_file_sets = {
        "cars": set(),
        "guns": set(),
        "sprites": set(),
        "props": set(),
    }

    for rel in model_rels:
        k = rel.lower()
        cid = canon_id(rel)
        mdl_dir = os.path.dirname(k)
        files_for_asset = {rel}
        shader_files = set()

        # Skins
        skin_prefix = k + "_"
        for ak, areal in all_raw.items():
            if ak.startswith(skin_prefix) and ak.endswith(".skin"):
                files_for_asset.add(areal)
                txt = open(os.path.join(RAW_DIR, areal), "r", encoding="latin1", errors="replace").read()
                for line in txt.splitlines():
                    if "," in line and not line.strip().startswith("//"):
                        _, sh = line.split(",", 1)
                        # Avoid bundling all 1,920 bktv jpgs into bk_tvscr's single zip; cap huge bktv set cleanly
                        if sh.strip().lower().startswith("progs/bktv_c"):
                            c_idx = sh.strip().lower()
                            if c_idx in ("progs/bktv_c1", "progs/bktv_c2", "progs/bktv_c3"):
                                tf, sf = resolve_tex_files(sh.strip(), mdl_dir)
                                files_for_asset.update(tf)
                                shader_files.update(sf)
                        else:
                            tf, sf = resolve_tex_files(sh.strip(), mdl_dir)
                            files_for_asset.update(tf)
                            shader_files.update(sf)
            elif ak.startswith(skin_prefix) and ak.endswith((".tga", ".png")):
                files_for_asset.add(areal)

        # Parse MD3 surface shaders
        if k.endswith(".md3"):
            raw_b = open(os.path.join(RAW_DIR, rel), "rb").read()
            if raw_b[:4] == b"IDP3":
                nsurfs = struct.unpack_from("<i", raw_b, 84)[0]
                pos = struct.unpack_from("<i", raw_b, 96)[0]
                for _ in range(nsurfs):
                    sname = raw_b[pos + 4:pos + 68].split(b"\0", 1)[0].decode("latin1")
                    _, _, s_nsh, _, _, _, osh, _, _, oend = struct.unpack_from("<10i", raw_b, pos + 68)
                    sh = raw_b[pos + osh:pos + osh + 64].split(b"\0", 1)[0].decode("latin1") if s_nsh > 0 else ""
                    pos += oend
                    tf, sf = resolve_tex_files(sh or sname, mdl_dir)
                    files_for_asset.update(tf)
                    shader_files.update(sf)

        # Special multi-frame texture companions (pinklady_b*, ltg_head_*, etc.)
        if k == "progs/pinklady.md3":
            for ak, areal in all_raw.items():
                if ak.startswith("progs/pinklady_"):
                    files_for_asset.add(areal)
            if "scripts/pinklady.shader" in all_raw:
                shader_files.add(all_raw["scripts/pinklady.shader"])
        elif k == "progs/ltg_head.md3":
            for ak, areal in all_raw.items():
                if ak.startswith("progs/ltg_head_"):
                    files_for_asset.add(areal)
            if "scripts/ltgun.shader" in all_raw:
                shader_files.add(all_raw["scripts/ltgun.shader"])
        elif k == "progs/milksplat.md3":
            for ak, areal in all_raw.items():
                if ak.startswith("progs/milksplat_"):
                    files_for_asset.add(areal)

        files_for_asset.update(shader_files)
        glb_rel = glb_by_model.get(k)
        if glb_rel and glb_rel.lower() in all_raw:
            files_for_asset.add(all_raw[glb_rel.lower()])

        # Write bundle zip
        bzip_name = f"{cid}.zip"
        bzip_path = os.path.join(BUNDLES_DIR, bzip_name)
        with zipfile.ZipFile(bzip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zb:
            for f_rel in sorted(files_for_asset):
                zb.write(os.path.join(RAW_DIR, f_rel), f_rel)

        cat = classify_model_cat(k)
        bucket = "props" if cat in ("lan_props", "fox_props", "warehouse") else cat
        cat_file_sets[bucket].update(files_for_asset)

        bundle_info[cid] = dict(
            rel=rel,
            cat=cat,
            rawSize=os.path.getsize(os.path.join(RAW_DIR, rel)),
            bundleZip=f"bundles/{bzip_name}",
            bundleSize=os.path.getsize(bzip_path),
            bundleCount=len(files_for_asset),
            glb=glb_rel if (glb_rel and glb_rel.lower() in all_raw) else None,
            glbSize=os.path.getsize(os.path.join(RAW_DIR, all_raw[glb_rel.lower()])) if (glb_rel and glb_rel.lower() in all_raw) else 0,
        )

    print(f"   Built {len(bundle_info)} individual asset bundles in {time.time()-t0:.1f}s", flush=True)

    print("3. Generating 224px WebP thumbnails for all 1,044 textures & skyboxes...", flush=True)
    tex_items = []
    for ak, areal in sorted(all_raw.items()):
        if ak.startswith(("textures/", "gfx/")) and ak.endswith((".png", ".tga", ".jpg")):
            full_p = os.path.join(RAW_DIR, areal)
            thumb_rel = "thumbs/" + os.path.splitext(areal)[0] + ".webp"
            thumb_p = os.path.join(OUT_ROOT, thumb_rel)
            os.makedirs(os.path.dirname(thumb_p), exist_ok=True)
            try:
                im = Image.open(full_p)
                w, h = im.size
                has_alpha = im.mode in ("RGBA", "LA") or ("transparency" in im.info)
                im_c = im.convert("RGBA" if has_alpha else "RGB")
                if max(w, h) > 224:
                    sc = 224.0 / max(w, h)
                    im_c = im_c.resize((max(1, round(w * sc)), max(1, round(h * sc))), Image.Resampling.LANCZOS)
                im_c.save(thumb_p, "WEBP", quality=80, method=4)
                tex_items.append(dict(
                    rel=areal, thumb=thumb_rel, w=w, h=h,
                    alpha=bool(has_alpha), size=os.path.getsize(full_p),
                ))
            except Exception as e:
                print("   thumb warn:", areal, e)

    print(f"   Generated {len(tex_items)} texture/skybox thumbnails in {time.time()-t0:.1f}s", flush=True)

    print("4. Building Sound & Shader & Map manifests...", flush=True)
    import wave
    sound_items = []
    for ak, areal in sorted(all_raw.items()):
        if ak.startswith("sound/") and ak.endswith((".wav", ".ogg")):
            fp = os.path.join(RAW_DIR, areal)
            sz = os.path.getsize(fp)
            dur, hz, ch = 0.0, 0, 0
            if ak.endswith(".wav"):
                try:
                    with wave.open(fp, "rb") as wf:
                        hz = wf.getframerate()
                        ch = wf.getnchannels()
                        dur = round(wf.getnframes() / float(max(1, hz)), 2)
                except Exception:
                    pass
            sound_items.append(dict(rel=areal, size=sz, dur=dur, hz=hz, ch=ch))

    shader_items = []
    for ak, areal in sorted(all_raw.items()):
        if ak.startswith("scripts/") and ak.endswith(".shader"):
            fp = os.path.join(RAW_DIR, areal)
            txt = open(fp, "r", encoding="utf-8", errors="replace").read()
            blocks = re.findall(r"^([^\s/\{\}]+)\s*\{", re.sub(r"//.*", "", txt), re.M)
            shader_items.append(dict(rel=areal, size=os.path.getsize(fp), count=len(blocks), preview=txt[:4000]))

    # Maps manifest
    featured_maps = [
        ("bklan5", "B-LAN 2001 Warehouse, Downtown Bakersfield, OrCom & Crystal Palace (v5 Master)", "https://bakersfield.larrywew.fun/warehouse/"),
        ("bakolansmall", "BakoLAN Small Tight Deathmatch Cut", None),
        ("fox", "Fox Theater, Padre Hotel & Downtown Bakersfield", "https://bakersfield.larrywew.fun/fox/"),
        ("nanaplaza", "Nana Plaza Neon Courtyard Arena", None),
        ("gallup", "Gallup Neighborhood & Street Arena", None),
        ("spruce", "Spruce Street Block Arena", None),
        ("goldenwest", "Golden West Casino & Bronze Horse Block", None),
        ("union3", "Union Ave Overpass & Corridor (v3)", None),
        ("bklan4", "B-LAN Warehouse & Sillect Sign Block (v4)", "https://bakersfield.larrywew.fun/warehouse4/"),
        ("vanwalkin", "Walk-In 6-Man LAN Van Interior Test Map", None),
        ("testbox", "Target-Dummy Weapon Testing Arena", None),
        ("bfarena", "Compact Bakersfield Arena", None),
        ("aerowalk", "Aerowalk LAN Rotation Classic", None),
    ]
    map_items = []
    for stem, title, viewer_url in featured_maps:
        bsp_p = os.path.join(QUAKE_DIR, "maps", stem + ".bsp")
        if not os.path.isfile(bsp_p):
            continue
        lit_p = os.path.join(QUAKE_DIR, "maps", stem + ".lit")
        has_lit = os.path.isfile(lit_p)
        bsp_sz = os.path.getsize(bsp_p)
        lit_sz = os.path.getsize(lit_p) if has_lit else 0
        with open(bsp_p, "rb") as f:
            hdr = f.read(16)
            magic = hdr[:4].decode("latin1", "replace")
        map_items.append(dict(
            stem=stem, title=title, magic=magic,
            bspRel=f"maps/{stem}.bsp", bspSize=bsp_sz,
            litRel=f"maps/{stem}.lit" if has_lit else None, litSize=lit_sz,
            viewerUrl=viewer_url,
        ))

    print("5. Building Category ZIPs & MASTER 'bakersfield_all_custom_assets.zip'...", flush=True)
    dl_packs = []

    def build_pack_zip(zip_fn, title, desc, file_list, comp=zipfile.ZIP_DEFLATED, level=6):
        zp = os.path.join(DL_DIR, zip_fn)
        t_z = time.time()
        raw_total = 0
        with zipfile.ZipFile(zp, "w", compression=comp, compresslevel=level) as zf:
            for item in file_list:
                if isinstance(item, tuple):
                    disk_p, arc_nm = item
                else:
                    disk_p, arc_nm = os.path.join(RAW_DIR, item), item
                raw_total += os.path.getsize(disk_p)
                zf.write(disk_p, arc_nm)
        z_sz = os.path.getsize(zp)
        print(f"   -> {zip_fn}: {len(file_list)} files, {raw_total/1e6:.1f} MB raw -> {z_sz/1e6:.1f} MB zip ({time.time()-t_z:.1f}s)", flush=True)
        entry = dict(
            id=os.path.splitext(zip_fn)[0],
            file=f"downloads/{zip_fn}",
            filename=zip_fn,
            title=title,
            desc=desc,
            count=len(file_list),
            rawBytes=raw_total,
            zipBytes=z_sz,
        )
        dl_packs.append(entry)
        return entry

    # Category zips
    veh_snds = [s["rel"] for s in sound_items if s["rel"].startswith("sound/vehicles/")]
    build_pack_zip(
        "bakersfield_cars_and_vehicles.zip",
        "Cars, Trucks, Buses, Supercar, Karts & Sky-Vehicles Pack",
        "All 7 street vehicles + wrecks & 35 blown-off parts, V12 Pink Supercar, GET Bus, Walk-In Van, JESS-KART, Sky-Chariots, 5 Forklifts, High-Poly .GLBs & vehicle audio.",
        sorted(cat_file_sets["cars"] | set(veh_snds)),
    )

    gun_snds = [s["rel"] for s in sound_items if any(s["rel"].startswith(f"sound/{p}/") for p in ("megaman", "wcannon", "weapons", "hammer", "ltgun", "netsend", "mbox", "milky", "pickle", "jetpack", "ccc", "fungun", "hackmon", "grenade"))]
    build_pack_zip(
        "bakersfield_guns_and_weapons.zip",
        "Custom Guns, Viewmodels, Pickups, Projectiles & Weapon SFX Pack",
        "Every custom BakersfieldQuake weapon (Mega-Slinger, WEW Cannon, Milky Gun, Pickle Surprise, Mystery Box, NetSend LOL.BAT, 3D Laptop, Goo Gun, Bonk Hammer, Sniper, Sentry, Rob Dob, Jetpack + Vault Girlfriend Gun) + textures, shaders, .GLBs & weapon SFX.",
        sorted(cat_file_sets["guns"] | set(gun_snds)),
    )

    spr_snds = [s["rel"] for s in sound_items if any(s["rel"].startswith(f"sound/{p}/") for p in ("daniel", "david", "bryan", "robeguy", "friends", "floathead", "john", "mrdiy"))]
    build_pack_zip(
        "bakersfield_sprites_and_characters.zip",
        "360° Multi-Angle Sprites (.SPR32/.SPR), Sculpted Heads & Characters Pack",
        "All 24 .SPR32/.SPR sprites (Wheelman 744f + 8 Dances 736f, Daniel 344f, David 344f, Flamingo Fiend 336f, Bryan 264f, Green-Suit Wheelman 256f, LAN Friends, Pregnant Runners) + Pink Lady, Pickle Diva, Bird Head, Mega-Man Riders, Vault Player Bodies & character voices.",
        sorted(cat_file_sets["sprites"] | set(spr_snds)),
    )

    bktv_all = [areal for ak, areal in all_raw.items() if ak.startswith("progs/bktv/")]
    build_pack_zip(
        "bakersfield_props_lan_fox_warehouse.zip",
        "2001 LAN Party, BKTV (37 Channels), Fox Theater & Warehouse 3D Props Pack",
        "All 130 B-LAN Warehouse & 2001 CRT/PC rigs, all 29 Fox Theater / Padre Hotel props, 37-channel BKTV screens, Daniel's 4AM Room props & Casino Bronze Horse.",
        sorted(cat_file_sets["props"] | set(bktv_all)),
    )

    build_pack_zip(
        "bakersfield_sounds_all_318.zip",
        "Complete Custom Audio, Larry Prank Calls, Voices & Music Pack (318 Clips)",
        "Every single custom .wav and .ogg sound in BakersfieldQuake across all 30 audio folders (Larry McCart prank calls, Mega Man, Vehicles, Announcer, John, Daniel, David, Bryan, Robeguy, Milky Song & more).",
        [s["rel"] for s in sound_items],
    )

    build_pack_zip(
        "bakersfield_textures_and_skyboxes.zip",
        "Complete Custom Map Textures, Neon Signs, Banners & Skyboxes Pack (1,044 Files)",
        "All 1,025 custom textures/*.png & .tga (Bakersfield Sign, Crystal Palace, OrCom/BAWLS banners, Fox Theater, Nana Plaza, Street View facades) + all 19 skybox & HUD graphics.",
        [t["rel"] for t in tex_items],
    )

    # Custom maps pack (shipped active rotation + signature maps)
    map_pack_files = []
    for m in map_items:
        if m["stem"] in ("bklan5", "bakolansmall", "fox", "nanaplaza", "gallup", "spruce", "vanwalkin", "testbox", "bfarena"):
            map_pack_files.append((os.path.join(QUAKE_DIR, m["bspRel"]), m["bspRel"]))
            if m["litRel"]:
                map_pack_files.append((os.path.join(QUAKE_DIR, m["litRel"]), m["litRel"]))
    build_pack_zip(
        "bakersfield_custom_maps.zip",
        "Custom BakersfieldQuake Maps Pack (.BSP + Colored .LIT Lightmaps)",
        "9 signature compiled playable maps (bklan5 Master Warehouse/Downtown/OrCom, bakolansmall, fox, nanaplaza, gallup, spruce, vanwalkin, testbox, bfarena) with colored .lit lightmaps.",
        map_pack_files,
        level=4,
    )

    # MASTER ALL-IN-ONE CUSTOM ASSETS ZIP!
    readme_master = (
        "BAKERSFIELD QUAKE — COMPLETE CUSTOM ASSETS MASTER ARCHIVE\n"
        "=========================================================\n"
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
        "Live Interactive 3D & Sprite Studio: https://bakersfield.larrywew.fun/custom-assets/\n\n"
        "Included in this Master ZIP:\n"
        "  - progs/          All 354 shipped 3D models (.md3, .mdl), 360-degree sprites (.spr32, .spr), 622 .skin files & 3,268 model/TV textures\n"
        "  - vault/progs/    8 archived bonus models (Girlfriend Gun girl.md3 + v_banana.md3, Player Bodies robeguy/suitguy/wifeguy.mdl, Sky-Chariots v1/v2/v4)\n"
        "  - glb/            All 15 original high-poly glTF 2.0 (.glb) 3D source models (cars, buses, trucks, supercar, weapons)\n"
        "  - sound/          All 318 custom sound effects, voice clips, Larry McCart prank lines & songs (.wav, .ogg)\n"
        "  - textures/       All 1,025 custom Bakersfield map textures, neon signs, posters & banners (.png, .tga)\n"
        "  - gfx/            All 19 custom skyboxes & HUD overlays\n"
        "  - scripts/        All 27 custom DarkPlaces / Quake 3 .shader material scripts\n"
        "  - effectinfo.txt  Custom particle effects definitions\n"
        "  - intro.dem       Custom recorded BakersfieldQuake intro demo\n"
    )
    readme_tmp = "/tmp/BQ_MASTER_README.txt"
    open(readme_tmp, "w", encoding="utf-8").write(readme_master)

    master_files = [(readme_tmp, "README_CUSTOM_ASSETS.txt")]
    for ak, areal in sorted(all_raw.items()):
        master_files.append((os.path.join(RAW_DIR, areal), areal))

    master_entry = build_pack_zip(
        "bakersfield_all_custom_assets.zip",
        "MASTER ARCHIVE — EVERY SINGLE CUSTOM ASSET IN ONE ZIP",
        "Complete all-in-one archive of all 362 3D models & 360° sprites (.MD3/.MDL/.SPR32/.SPR), all 15 .GLB 3D source models, all 622 skins & 27 shaders, all 318 custom sounds, and all 1,044 custom textures & skyboxes!",
        master_files,
        level=5,
    )
    # Put master pack first!
    dl_packs.remove(master_entry)
    dl_packs.insert(0, master_entry)

    manifest = dict(
        generatedAt=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        rawFileCount=len(all_raw),
        modelBundleCount=len(bundle_info),
        soundCount=len(sound_items),
        textureCount=len(tex_items),
        shaderCount=len(shader_items),
        mapCount=len(map_items),
        downloads=dl_packs,
        bundles=bundle_info,
        sounds=sound_items,
        textures=tex_items,
        shaders=shader_items,
        maps=map_items,
    )
    man_path = os.path.join(OUT_ROOT, "vps_manifest.json")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, separators=(",", ":"))
    os.system(f"chmod -R a+rX {OUT_ROOT}")
    print(f"DONE in {time.time()-t0:.1f}s! Wrote {man_path} ({os.path.getsize(man_path)/1e3:.1f} KB)", flush=True)


if __name__ == "__main__":
    main()
