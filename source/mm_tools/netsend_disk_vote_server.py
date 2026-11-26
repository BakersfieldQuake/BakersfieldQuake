#!/usr/bin/env python3
"""Vote & feedback JSON API for the THE DISK viewmodel vote (docs/netsend_disk_vote/), modelled on the Mega-Bow one.

Runs on the VPS as netsend-disk-vote.service on 127.0.0.1:3957 behind nginx (location = /api/netsend-disk-vote).
Each vote is appended to /opt/netsend-disk-vote/votes.json and, if TG_BOT_TOKEN / TG_CHAT_ID are set (systemd
EnvironmentFile, root-only), posted to the Telegram group so the result lands where the preview was sent.
The page may be opened from a downloaded file (Origin: null), so that origin is allowed too.
"""
from __future__ import annotations

import fcntl
import json
import os
import threading
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 3957
API_PATH = "/api/netsend-disk-vote"
DATA_DIR = Path(os.environ.get("VOTE_DIR", "/opt/netsend-disk-vote"))
VOTES_FILE = DATA_DIR / "votes.json"
LOCK_FILE = DATA_DIR / "votes.lock"
MAX_BODY_BYTES = 32 * 1024
OPTIONS = ("A", "B", "C")
TITLES = {"A": "Frisbee Pro", "B": "Trickster", "C": "Showboat"}
ALLOWED_ORIGINS = {
    "https://bakersfield.larrywew.fun",
    "https://davidbrazil.site",
    "https://www.davidbrazil.site",
    "https://larrywew.fun",
    "https://www.larrywew.fun",
    "null",
}
_LOCK = threading.Lock()


def _read():
    if not VOTES_FILE.exists():
        return []
    raw = VOTES_FILE.read_text(encoding="utf-8").strip()
    data = json.loads(raw) if raw else []
    return data if isinstance(data, list) else []


def load_votes():
    with _LOCK, open(LOCK_FILE, "a+") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_SH)
        try:
            return _read()
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


def append_vote(entry):
    with _LOCK, open(LOCK_FILE, "a+") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            votes = _read()
            votes.append(entry)
            tmp = DATA_DIR / ("votes.json.tmp.%d" % os.getpid())
            tmp.write_text(json.dumps(votes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(tmp, VOTES_FILE)
            return votes
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


def summary(votes):
    wins = {k: 0 for k in OPTIONS}
    sums = {k: 0 for k in OPTIONS}
    cnts = {k: 0 for k in OPTIONS}
    for v in votes:
        if v.get("winner") in wins:
            wins[v["winner"]] += 1
        for k in OPTIONS:
            r = (v.get("ratings") or {}).get(k)
            if isinstance(r, int) and 1 <= r <= 5:
                sums[k] += r
                cnts[k] += 1
    return {"winners": wins, "avgRatings": {k: (round(sums[k] / cnts[k], 2) if cnts[k] else None) for k in OPTIONS},
            "ratingCounts": cnts}


def payload(votes, new=None):
    out = {"ok": True, "count": len(votes), "summary": summary(votes), "votes": list(reversed(votes[-200:]))}
    if new is not None:
        out["vote"] = new
    return out


def validate(body):
    if not isinstance(body, dict):
        raise ValueError("JSON body must be an object")
    winner = body.get("winner")
    if winner not in OPTIONS:
        raise ValueError("winner must be one of A, B, C")
    voter = body.get("voter") or ""
    if not isinstance(voter, str):
        raise ValueError("voter must be a string")
    voter = voter.strip()[:64] or "Anonymous"
    ratings = {}
    rin = body.get("ratings") or {}
    if not isinstance(rin, dict):
        raise ValueError("ratings must be an object")
    for k in OPTIONS:
        val = rin.get(k)
        if val in (None, ""):
            ratings[k] = None
        elif isinstance(val, bool) or not isinstance(val, int) or not 1 <= val <= 5:
            raise ValueError("ratings.%s must be 1..5 or null" % k)
        else:
            ratings[k] = val
    fb = {}
    fin = body.get("feedback") or {}
    if not isinstance(fin, dict):
        raise ValueError("feedback must be an object")
    for k in OPTIONS + ("throw", "idle", "projectile", "overall"):
        val = fin.get(k) or ""
        if not isinstance(val, str):
            raise ValueError("feedback.%s must be a string" % k)
        if val.strip():
            fb[k] = val.strip()[:2000]
    fav = body.get("favoriteClips") or []
    if not isinstance(fav, list):
        raise ValueError("favoriteClips must be a list")
    fav = [str(x)[:60] for x in fav[:12]]
    return {"id": uuid.uuid4().hex[:12], "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "voter": voter, "winner": winner, "ratings": ratings, "feedback": fb, "favoriteClips": fav}


def notify(entry, votes):
    token, chat = os.environ.get("TG_BOT_TOKEN"), os.environ.get("TG_CHAT_ID")
    if not token or not chat:
        return
    s = summary(votes)
    lines = ["\U0001F4BE THE DISK vote from %s: Set %s (%s)" % (entry["voter"], entry["winner"], TITLES[entry["winner"]])]
    rs = ", ".join("%s %s" % (k, entry["ratings"][k]) for k in OPTIONS if entry["ratings"].get(k))
    if rs:
        lines.append("Ratings: " + rs)
    if entry["favoriteClips"]:
        lines.append("Favourite clips: " + ", ".join(entry["favoriteClips"]))
    for k, v in entry["feedback"].items():
        lines.append("%s: %s" % (k if k not in TITLES else "Set %s" % k, v))
    lines.append("Tally: " + "  ".join("%s=%d" % (k, s["winners"][k]) for k in OPTIONS) + " (%d votes)" % len(votes))
    data = urllib.parse.urlencode({"chat_id": chat, "text": "\n".join(lines)[:3900],
                                   "disable_web_page_preview": "true"}).encode()
    try:
        urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % token, data=data, timeout=10).read()
    except Exception:
        pass


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        return

    def _cors(self):
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")

    def _json(self, status, data):
        raw = (json.dumps(data, ensure_ascii=False) + "\n").encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _ok_path(self):
        if self.path.split("?", 1)[0] != API_PATH:
            self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
            return False
        return True

    def do_OPTIONS(self):
        if not self._ok_path():
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self._ok_path():
            self._json(HTTPStatus.OK, payload(load_votes()))

    def do_POST(self):
        if not self._ok_path():
            return
        try:
            cl = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            cl = -1
        if cl <= 0 or cl > MAX_BODY_BYTES:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "bad body size"})
            return
        try:
            entry = validate(json.loads(self.rfile.read(cl).decode("utf-8")))
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        votes = append_vote(entry)
        threading.Thread(target=notify, args=(entry, votes), daemon=True).start()
        self._json(HTTPStatus.CREATED, payload(votes, entry))


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not VOTES_FILE.exists():
        VOTES_FILE.write_text("[]\n", encoding="utf-8")
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    srv.daemon_threads = True
    srv.serve_forever()


if __name__ == "__main__":
    main()
