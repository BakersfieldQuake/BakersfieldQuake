"""Syncs BAKOQUAKE release files, manifests, and macOS DMG to the VPS fallback store over SSH.

Uses a content-addressed file store (<remote_dir>/files/<sha256>) shared across all platforms so the VPS holds
only ~1.3 GB for Windows, Linux, and macOS combined, and only uploads blobs that do not already exist there.

Modes:
  1. Release sync (called after publishing non-draft release):
     python -I sync_vps.py --manifests manifest-*.json --zips BAKOQUAKE*.zip
  2. macOS DMG sync (called after notarizing & uploading the DMG):
     python -I sync_vps.py --dmg BAKOQUAKE-macos-arm64.dmg --manifest manifest-macos-app.json

Reads SSH connection settings from CLI flags or environment variables:
  VPS_SYNC_HOST  Hostname or IP (if unset/empty, logs a notice and exits 0 cleanly)
  VPS_SYNC_USER  SSH user (default: bqsync)
  VPS_SYNC_KEY   Private key contents (or path to a key file)
  VPS_SYNC_PORT  SSH port (default: 22)
  VPS_SYNC_DIR   Remote directory (default: /srv/bq-updates)
"""
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path


def is_sha256_hex(name):
    return len(name) == 64 and all(c in "0123456789abcdef" for c in name)


def collect_needed_blobs(manifest_paths):
    """Returns {sha256: [(zip_basename, root_prefix, rel_path, size), ...]} across all manifests."""
    needed = {}
    for mp in manifest_paths:
        m = json.loads(Path(mp).read_text("utf-8"))
        zip_name = os.path.basename(m.get("zip", ""))
        root_prefix = m.get("root", "")
        for rel, info in m.get("files", {}).items():
            sha = info["sha256"]
            needed.setdefault(sha, []).append((zip_name, root_prefix, rel, int(info["size"])))
    return needed


def compute_missing_hashes(needed_hashes, existing_remote_hashes):
    """Returns sorted list of sha256 hashes missing from the VPS."""
    return sorted(set(needed_hashes) - set(existing_remote_hashes))


def update_keep_state(old_state, current_hashes):
    """Computes new {current, previous} keep state, shifting previous only when current changes."""
    cur_sorted = sorted(set(current_hashes))
    old_cur = sorted(set((old_state or {}).get("current", [])))
    old_prev = sorted(set((old_state or {}).get("previous", [])))
    if cur_sorted != old_cur:
        new_prev = old_cur
    else:
        new_prev = old_prev
    return {"current": cur_sorted, "previous": new_prev}


def compute_prune_list(existing_remote_hashes, keep_state):
    """Returns sorted list of sha256 blobs on the VPS no longer referenced by current or previous release."""
    keep = set(keep_state.get("current", [])) | set(keep_state.get("previous", []))
    return sorted(h for h in existing_remote_hashes if is_sha256_hex(h) and h not in keep)


class SshClient:
    def __init__(self, host, user, key_path, port="22"):
        self.target = f"{user}@{host}"
        self.base_cmd = [
            "ssh",
            "-i", str(key_path),
            "-p", str(port),
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=15",
            self.target,
        ]

    def run(self, remote_cmd, input_bytes=None):
        res = subprocess.run(
            [*self.base_cmd, remote_cmd],
            input=input_bytes,
            capture_output=True,
            check=False,
        )
        if res.returncode != 0:
            err = res.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"SSH command failed ({res.returncode}): {err}")
        return res.stdout.decode("utf-8", errors="replace")


def _extract_blob_to_temp(sha, candidates, zip_map, tmp_dir):
    """Finds and extracts a single blob matching `sha` from the provided zips into tmp_dir/sha."""
    # Prefer the zip named by the manifest first, then fall back to any provided zip.
    ordered_attempts = []
    seen = set()
    for zip_name, root_prefix, rel, size in candidates:
        if zip_name in zip_map and (zip_name, root_prefix, rel) not in seen:
            ordered_attempts.append((zip_map[zip_name], root_prefix, rel, size))
            seen.add((zip_name, root_prefix, rel))
    for zp in zip_map.values():
        for _zn, root_prefix, rel, size in candidates:
            key = (zp.filename, root_prefix, rel)
            if key not in seen:
                ordered_attempts.append((zp, root_prefix, rel, size))
                seen.add(key)

    dest = Path(tmp_dir) / sha
    for zf, root_prefix, rel, want_size in ordered_attempts:
        member = root_prefix + rel
        try:
            info = zf.getinfo(member)
        except KeyError:
            continue
        h = hashlib.sha256()
        written = 0
        with zf.open(info) as src, open(dest, "wb") as out:
            for chunk in iter(lambda: src.read(1 << 20), b""):
                h.update(chunk)
                out.write(chunk)
                written += len(chunk)
        if h.hexdigest() == sha and written == want_size:
            return dest
    raise RuntimeError(f"Could not find zip member matching sha256 {sha} ({candidates[0][2]})")


def _stream_tar_files(ssh, remote_unpack_dir, file_pairs):
    """Streams [(local_path, archive_name), ...] via tar over SSH stdin into remote_unpack_dir."""
    if not file_pairs:
        return
    qdir = shlex.quote(remote_unpack_dir)
    proc = subprocess.Popen(
        [*ssh.base_cmd, f"mkdir -p {qdir} && tar -xf - -C {qdir}"],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        with tarfile.open(fileobj=proc.stdin, mode="w|") as tf:
            for local_path, arcname in file_pairs:
                st = os.stat(local_path)
                ti = tarfile.TarInfo(name=arcname)
                ti.size = st.st_size
                ti.mode = 0o644
                ti.mtime = int(time.time())
                with open(local_path, "rb") as f:
                    tf.addfile(ti, f)
    finally:
        if proc.stdin:
            proc.stdin.close()
    stderr_out = proc.stderr.read().decode("utf-8", errors="replace").strip()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"tar-over-SSH upload failed ({rc}): {stderr_out}")


def sync_release(ssh, remote_dir, manifest_paths, zip_paths):
    needed = collect_needed_blobs(manifest_paths)
    qdir = shlex.quote(remote_dir)
    qfiles = shlex.quote(f"{remote_dir}/files")
    qinc = shlex.quote(f"{remote_dir}/.incoming")
    qkeep = shlex.quote(f"{remote_dir}/.keep_hashes.json")

    ssh.run(f"mkdir -p {qfiles} {qinc}")
    ls_out = ssh.run(f"ls -1 {qfiles}")
    existing = {line.strip() for line in ls_out.splitlines() if is_sha256_hex(line.strip())}

    keep_raw = ssh.run(f"cat {qkeep} 2>/dev/null || true").strip()
    try:
        old_keep = json.loads(keep_raw) if keep_raw else {}
    except ValueError:
        old_keep = {}

    missing = compute_missing_hashes(needed.keys(), existing)
    print(f"VPS sync: {len(needed)} unique blobs needed, {len(existing)} present, {len(missing)} to upload")

    zip_map = {Path(zp).name: zipfile.ZipFile(zp) for zp in zip_paths}
    try:
        with tempfile.TemporaryDirectory() as td:
            if missing:
                staged_pairs = []
                total_bytes = 0
                for sha in missing:
                    p = _extract_blob_to_temp(sha, needed[sha], zip_map, td)
                    total_bytes += p.stat().st_size
                    staged_pairs.append((p, sha))
                print(f"Uploading {len(staged_pairs)} new blob(s) ({total_bytes / 1e6:.1f} MB)...")
                _stream_tar_files(ssh, f"{remote_dir}/.incoming/blobs", staged_pairs)
                ssh.run(
                    f"cd {shlex.quote(remote_dir + '/.incoming/blobs')} && "
                    f"for f in *; do [ -e \"$f\" ] && mv -f \"$f\" {qfiles}/\"$f\"; done && "
                    f"rmdir {shlex.quote(remote_dir + '/.incoming/blobs')}"
                )

            # Atomically move manifests into place AFTER blobs exist.
            manifest_pairs = [(Path(mp), Path(mp).name) for mp in manifest_paths]
            _stream_tar_files(ssh, f"{remote_dir}/.incoming/manifests", manifest_pairs)
            ssh.run(
                f"cd {shlex.quote(remote_dir + '/.incoming/manifests')} && "
                f"for f in *.json; do [ -e \"$f\" ] && mv -f \"$f\" {qdir}/\"$f\"; done && "
                f"rmdir {shlex.quote(remote_dir + '/.incoming/manifests')}"
            )

            # Update .keep_hashes.json and prune stale blobs not in current or previous release.
            new_keep = update_keep_state(old_keep, needed.keys())
            keep_file = Path(td) / ".keep_hashes.json"
            keep_file.write_text(json.dumps(new_keep, indent=1) + "\n", "utf-8")
            _stream_tar_files(ssh, remote_dir, [(keep_file, ".keep_hashes.json")])

            prune = compute_prune_list(existing | set(missing), new_keep)
            if prune:
                print(f"Pruning {len(prune)} obsolete blob(s) from VPS...")
                payload = ("\n".join(prune) + "\n").encode("utf-8")
                ssh.run(f"cd {qfiles} && xargs -r rm -f", input_bytes=payload)
    finally:
        for zf in zip_map.values():
            zf.close()
    print("VPS release sync complete.")


def sync_dmg(ssh, remote_dir, dmg_path, manifest_path):
    qdir = shlex.quote(remote_dir)
    qinc = shlex.quote(f"{remote_dir}/.incoming/dmg")
    dmg_p = Path(dmg_path)
    man_p = Path(manifest_path)

    print(f"Uploading {dmg_p.name} ({dmg_p.stat().st_size / 1e6:.1f} MB) and {man_p.name} to VPS...")
    _stream_tar_files(ssh, f"{remote_dir}/.incoming/dmg", [
        (dmg_p, dmg_p.name),
        (man_p, man_p.name),
    ])
    ssh.run(
        f"mv -f {qinc}/{shlex.quote(dmg_p.name)} {qdir}/{shlex.quote(dmg_p.name)} && "
        f"mv -f {qinc}/{shlex.quote(man_p.name)} {qdir}/{shlex.quote(man_p.name)} && "
        f"rmdir {qinc}"
    )
    print("VPS DMG sync complete.")


def _resolve_key(key_value):
    p = Path(key_value)
    if "\n" not in key_value and p.is_file():
        return p, None
    tf = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
    content = key_value if key_value.endswith("\n") else key_value + "\n"
    tf.write(content)
    tf.close()
    os.chmod(tf.name, 0o600)
    return Path(tf.name), Path(tf.name)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sync BAKOQUAKE update blobs and manifests to VPS fallback")
    ap.add_argument("--host", default=os.environ.get("VPS_SYNC_HOST", ""))
    ap.add_argument("--user", default=os.environ.get("VPS_SYNC_USER") or "bqsync")
    ap.add_argument("--port", default=os.environ.get("VPS_SYNC_PORT") or "22")
    ap.add_argument("--key", default=os.environ.get("VPS_SYNC_KEY", ""))
    ap.add_argument("--remote-dir", default=os.environ.get("VPS_SYNC_DIR") or "/srv/bq-updates")
    ap.add_argument("--manifests", nargs="+", default=[], help="manifest-*.json files for release sync")
    ap.add_argument("--zips", nargs="+", default=[], help="platform zip files containing blobs")
    ap.add_argument("--dmg", default="", help="BAKOQUAKE-macos-arm64.dmg path for DMG sync")
    ap.add_argument("--manifest", default="", help="manifest-macos-app.json path for DMG sync")
    a = ap.parse_args(argv)

    if not a.host.strip():
        print("VPS sync skipped: VPS_SYNC_HOST is not configured.")
        return 0
    if not a.key.strip():
        print("VPS sync skipped: VPS_SYNC_KEY is not configured.")
        return 0

    key_path, tmp_key = _resolve_key(a.key)
    try:
        ssh = SshClient(a.host.strip(), a.user.strip(), key_path, a.port.strip())
        if a.dmg:
            if not a.manifest:
                ap.error("--manifest is required with --dmg")
            sync_dmg(ssh, a.remote_dir.rstrip("/"), a.dmg, a.manifest)
        elif a.manifests and a.zips:
            sync_release(ssh, a.remote_dir.rstrip("/"), a.manifests, a.zips)
        else:
            ap.error("specify either (--manifests ... --zips ...) or (--dmg ... --manifest ...)")
    finally:
        if tmp_key:
            tmp_key.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
