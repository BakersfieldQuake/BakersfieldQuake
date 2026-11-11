"""Build zz_greenjar.pk3 and sync the latest progs.dat + Jar o' Green Guys / Green-Suit Wheelman
assets to the live BakersfieldQuake dedicated server on root@72.62.241.93:22.
"""
import os
import shutil
import subprocess
import sys
import time
import zipfile
import zlib

HOST = "root@72.62.241.93"
SSH = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", HOST]
SCP = ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]

COMBAT = r"G:\Quake\Combat"
MOD = os.path.join(COMBAT, "BakersfieldQuake")
DIST_MOD = os.path.join(COMBAT, "dist", "BAKOQUAKE", "BakersfieldQuake")
PK3_MAIN = os.path.join(MOD, "bakersfield.pk3")
PK3_GJ = os.path.join(MOD, "zz_greenjar.pk3")
PROGS_DAT = os.path.join(MOD, "progs.dat")

STORE_EXTS = {".png", ".jpg", ".jpeg", ".ogg"}


def file_crc32(path: str) -> int:
    crc = 0
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            crc = zlib.crc32(chunk, crc)
    return crc & 0xFFFFFFFF


def build_zz_greenjar_pk3() -> int:
    t0 = time.perf_counter()
    rel_files = [
        "progs/v_greenjar.md3",
        "progs/greenjar_proj.spr32",
        "progs/greenjar_burst.spr32",
        "progs/greenguy_mini.spr32",
        "scripts/greenjarvm.shader",
    ]
    for i in range(112):
        rel_files.append(f"progs/v_greenjar.md3_{i}.skin")
        rel_files.append(f"progs/gjvm_{i:03d}.png")

    snd_dir = os.path.join(MOD, "sound", "greenjar")
    for fn in sorted(os.listdir(snd_dir)):
        if fn.lower().endswith(".wav"):
            rel_files.append(f"sound/greenjar/{fn}")

    # Check if greensuit_wheelman.spr32 in bakersfield.pk3 already matches loose progs/greensuit_wheelman.spr32
    gs_rel = "progs/greensuit_wheelman.spr32"
    gs_abs = os.path.join(MOD, "progs", "greensuit_wheelman.spr32")
    include_gs = True
    if os.path.isfile(PK3_MAIN) and os.path.isfile(gs_abs):
        with zipfile.ZipFile(PK3_MAIN, "r") as zf:
            if gs_rel in zf.namelist():
                pk3_crc = zf.getinfo(gs_rel).CRC & 0xFFFFFFFF
                loose_crc = file_crc32(gs_abs)
                if pk3_crc == loose_crc:
                    print(f"[check] {gs_rel} already in bakersfield.pk3 (CRC32 {loose_crc:08x} matches 100%)")
                    include_gs = False
    if include_gs and os.path.isfile(gs_abs):
        print(f"[check] Including updated {gs_rel} in zz_greenjar.pk3")
        rel_files.append(gs_rel)

    tmp_pk3 = PK3_GJ + ".tmp"
    if os.path.isfile(tmp_pk3):
        os.remove(tmp_pk3)

    raw_bytes = 0
    with zipfile.ZipFile(tmp_pk3, "w", allowZip64=True) as zf:
        for rel in sorted(rel_files):
            src = os.path.join(MOD, rel.replace("/", os.sep))
            if not os.path.isfile(src):
                raise FileNotFoundError(f"Missing required runtime asset: {src}")
            raw_bytes += os.path.getsize(src)
            ext = os.path.splitext(rel)[1].lower()
            if ext in STORE_EXTS:
                zf.write(src, rel, compress_type=zipfile.ZIP_STORED)
            else:
                zf.write(src, rel, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

    os.replace(tmp_pk3, PK3_GJ)
    pk3_size = os.path.getsize(PK3_GJ)
    dt = time.perf_counter() - t0
    print(
        f"[pk3] Built {PK3_GJ}: {len(rel_files)} files, "
        f"{raw_bytes / 1048576:.2f} MB raw -> {pk3_size / 1048576:.2f} MB pk3 in {dt:.1f}s"
    )
    return pk3_size


def sync_local_dist() -> None:
    if not os.path.isdir(DIST_MOD):
        return
    for src_path in (PROGS_DAT, PK3_GJ):
        dst_path = os.path.join(DIST_MOD, os.path.basename(src_path))
        try:
            shutil.copy2(src_path, dst_path)
            print(f"[dist] Synced {dst_path}")
        except PermissionError as exc:
            print(f"[dist] Skipped locked {dst_path}: {exc}")


def run_ssh(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(SSH + [cmd], capture_output=True, text=True, check=check)


def main() -> None:
    if not os.path.isfile(PROGS_DAT):
        raise FileNotFoundError(PROGS_DAT)
    progs_size = os.path.getsize(PROGS_DAT)
    print(f"[progs] Local progs.dat: {progs_size:,} bytes")

    pk3_size = build_zz_greenjar_pk3()
    sync_local_dist()

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_dir = f"/opt/quake/backup/{stamp}-greenjar"
    print(f"[vps] Backing up current server files to {backup_dir} ...")
    run_ssh(
        f"mkdir -p {backup_dir} && "
        f"cp -a /opt/quake/BakersfieldQuake/progs.dat {backup_dir}/ && "
        f"cp -a /opt/quake/BakersfieldQuake/server_vps.cfg {backup_dir}/ && "
        f"cp -a /etc/nginx/conf.d/quake-download.conf {backup_dir}/"
    )

    print("[vps] Uploading progs.dat and zz_greenjar.pk3 ...")
    subprocess.run(
        SCP + [PROGS_DAT, PK3_GJ, f"{HOST}:/opt/quake/BakersfieldQuake/"],
        check=True,
    )

    patch_py = r"""
import pathlib

# 1. Whitelist /zz_greenjar.pk3 on nginx :8097 fast-download server
ng_path = pathlib.Path("/etc/nginx/conf.d/quake-download.conf")
ng_txt = ng_path.read_text(encoding="utf-8")
if "location = /zz_greenjar.pk3" not in ng_txt:
    target = "location = /zz_tone1.pk3 { }"
    if target not in ng_txt:
        raise RuntimeError("Could not find zz_tone1.pk3 location in quake-download.conf")
    ng_txt = ng_txt.replace(target, target + "\n    location = /zz_greenjar.pk3 { }", 1)
    ng_path.write_text(ng_txt, encoding="utf-8")
    print("PATCHED_NGINX")
else:
    print("NGINX_ALREADY_OK")

# 2. Add scripts/greenjarvm.shader marker to sv_curl_serverpackages in server_vps.cfg
cfg_path = pathlib.Path("/opt/quake/BakersfieldQuake/server_vps.cfg")
cfg_txt = cfg_path.read_text(encoding="utf-8")
marker = "scripts/greenjarvm.shader"
if marker not in cfg_txt:
    lines = cfg_txt.splitlines(keepends=True)
    updated = False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("sv_curl_serverpackages"):
            q1 = ln.find('"')
            q2 = ln.rfind('"')
            if q1 != -1 and q2 > q1:
                pkgs = ln[q1 + 1:q2].strip()
                lines[i] = f'{ln[:q1 + 1]}{pkgs} {marker}{ln[q2:]}'
                updated = True
                break
    if not updated:
        raise RuntimeError("Could not find sv_curl_serverpackages in server_vps.cfg")
    cfg_path.write_text("".join(lines), encoding="utf-8")
    print("PATCHED_SERVER_CFG")
else:
    print("SERVER_CFG_ALREADY_OK")
"""
    res = subprocess.run(
        SSH + ["python3 -"],
        input=patch_py,
        capture_output=True,
        text=True,
        check=True,
    )
    print("[vps] Config patch result:", res.stdout.strip().replace("\n", ", "))

    print("[vps] Fixing ownership, reloading nginx, and restarting quake-bakersfield.service ...")
    verify_cmd = (
        "chown quake:quake /opt/quake/BakersfieldQuake/progs.dat "
        "/opt/quake/BakersfieldQuake/zz_greenjar.pk3 "
        "/opt/quake/BakersfieldQuake/server_vps.cfg && "
        "chmod 644 /opt/quake/BakersfieldQuake/progs.dat "
        "/opt/quake/BakersfieldQuake/zz_greenjar.pk3 "
        "/opt/quake/BakersfieldQuake/server_vps.cfg && "
        "nginx -t && systemctl reload nginx && "
        "curl -fsSI http://127.0.0.1:8097/zz_greenjar.pk3 | head -n 5 && "
        "systemctl restart quake-bakersfield && "
        "sleep 6 && "
        "systemctl is-active quake-bakersfield && "
        "journalctl -u quake-bakersfield --since '-12 sec' --no-pager"
    )
    v = run_ssh(verify_cmd, check=True)
    print(v.stdout)

    bad = []
    for err_kw in ("Host_Error", "Failed to load", "couldn't load", "Segmentation", "PRVM_"):
        if err_kw.lower() in v.stdout.lower():
            bad.append(err_kw)
    if bad:
        print(f"[ERROR] Detected engine error keywords in startup log: {bad}", file=sys.stderr)
        sys.exit(2)

    print(
        f"[SUCCESS] VPS live server updated cleanly! "
        f"progs.dat={progs_size:,} B, zz_greenjar.pk3={pk3_size:,} B"
    )


if __name__ == "__main__":
    main()
