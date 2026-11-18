"""Warn when a new package changes a base pk3 compared with the latest published release.

python -I base_pk3_guard.py <owner/repo> <new BAKOQUAKE.zip> <entry> [<entry> ...]

Players update by downloading only files whose contents changed, and the two base pk3s are ~920 MB together.
Content belongs in zz_<feature>.pk3 overlays (see AGENTS.md), so a change here is almost always a mistake.
Reads only the central directory of the published zip (HTTP range requests), never the whole file, and compares
each entry's CRC-32 and size. Always exits 0: the result is a ::warning:: plus a job-summary line, not a failure.
Needs GH_TOKEN (the Actions token is enough).
"""
import json
import os
import sys
import urllib.request
import zipfile

API = "https://api.github.com"


def gh(path):
    req = urllib.request.Request(API + path, headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                                                      "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


class RangeFile:
    """Minimal seekable file over HTTP range requests, enough for zipfile to read a central directory."""

    def __init__(self, url):
        self.url, self.pos = url, 0
        with self._get("bytes=0-0") as r:
            self.size = int(r.headers["Content-Range"].split("/")[1])

    def _get(self, rng):
        return urllib.request.urlopen(urllib.request.Request(self.url, headers={
            "Range": rng, "Accept": "application/octet-stream",
            "Authorization": "Bearer " + os.environ["GH_TOKEN"]}))

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def read(self, n=-1):
        n = self.size - self.pos if n < 0 else min(n, self.size - self.pos)
        if n <= 0:
            return b""
        with self._get(f"bytes={self.pos}-{self.pos + n - 1}") as r:
            data = r.read()
        self.pos += len(data)
        return data


def summary(line):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as f:
            f.write(line + "\n")


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    repo, new_zip, entries = sys.argv[1], sys.argv[2], sys.argv[3:]
    rel = gh(f"/repos/{repo}/releases/latest")
    asset = next((a for a in rel["assets"] if a["name"] == "BAKOQUAKE.zip"), None)
    if not asset:
        summary(f"Base pk3 guard: latest release {rel['tag_name']} has no BAKOQUAKE.zip; nothing to compare.")
        return
    old = zipfile.ZipFile(RangeFile(asset["url"]))
    new = zipfile.ZipFile(new_zip)
    changed = []
    for name in entries:
        try:
            o = old.getinfo(name)
        except KeyError:
            o = None
        try:
            n = new.getinfo(name)
        except KeyError:
            n = None
        if (o and (o.CRC, o.file_size)) != (n and (n.CRC, n.file_size)):
            size = (n or o).file_size / 1e6
            changed.append(f"{name} ({size:.0f} MB)")
    if changed:
        msg = (f"This release changes a base pk3 compared with {rel['tag_name']} and forces every player to "
               f"re-download it: {', '.join(changed)}. Ship content as zz_<feature>.pk3 overlays (AGENTS.md).")
        print(f"::warning title=Base pk3 changed::{msg}")
        summary(f"**WARNING:** {msg}")
    else:
        msg = f"Base pk3 guard: {len(entries)} base pk3(s) unchanged vs {rel['tag_name']}."
        print(msg)
        summary(msg)


if __name__ == "__main__":
    main()
