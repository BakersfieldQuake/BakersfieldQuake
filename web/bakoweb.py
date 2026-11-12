#!/usr/bin/env python3
"""bakoweb: the one extra program a BakersfieldQuake server needs for browser players.

  http://<host>:8080/     serves the play page, the engine (darkplaces-wasm.js) and the game files from --root
  ws://<host>:8080/ws     carries the game: each browser connection gets its own UDP socket to the
                          DarkPlaces server (--game), one WebSocket message per UDP packet, both ways

The DarkPlaces server is unchanged: browser players look like normal UDP clients coming from this machine.
Windows players keep connecting to the server's UDP port directly.

Python 3.8+ standard library only, nothing to install.
  python3 bakoweb.py --root site-out --game 127.0.0.1:26000 --http-port 8080
"""
import argparse
import asyncio
import base64
import hashlib
import json
import logging
import mimetypes
import os
import struct
import time
from urllib.parse import unquote, urlsplit

log = logging.getLogger("bakoweb")

WS_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
# Emscripten opens every emulated UDP socket with this 10-byte message (FF FF FF FF "port" + 2 port bytes).
# It is not a game packet, so it is dropped.
EM_PORT_PREFIX = b"\xff\xff\xff\xffport"
MAX_MESSAGE = 1 << 20          # Quake packets are under 1500 bytes, anything this big is garbage
MAX_SESSIONS = 64
SEND_BUFFER_LIMIT = 1 << 20    # a browser this far behind loses packets instead of growing a queue (UDP rules)

mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("application/json", ".json")
for ext in (".pak", ".pk3", ".dat", ".bsp", ".lit", ".dem"):
    mimetypes.add_type("application/octet-stream", ext)
for ext in (".cfg", ".rc", ".txt"):
    mimetypes.add_type("text/plain", ext)


class GameSocket(asyncio.DatagramProtocol):
    def __init__(self, session):
        self.session = session

    def datagram_received(self, data, addr):
        self.session.to_browser(data)

    def error_received(self, exc):
        # the game server is down or restarting: the browser will time out and show its own message
        log.debug("udp error for %s: %s", self.session.peer, exc)


class Session:
    count = 0
    active = {}

    def __init__(self, reader, writer, peer, game, idle):
        Session.count += 1
        self.id = Session.count
        self.reader, self.writer, self.peer, self.game, self.idle = reader, writer, peer, game, idle
        self.udp = None
        self.up = self.down = self.up_bytes = self.down_bytes = self.dropped = 0
        self.started = time.time()

    def to_browser(self, data):
        if self.writer.is_closing():
            return
        if self.writer.transport.get_write_buffer_size() > SEND_BUFFER_LIMIT:
            self.dropped += 1
            return
        self.down += 1
        self.down_bytes += len(data)
        self.writer.write(ws_frame(0x2, data))

    async def run(self):
        loop = asyncio.get_running_loop()
        self.udp, _ = await loop.create_datagram_endpoint(lambda: GameSocket(self), remote_addr=self.game)
        local = self.udp.get_extra_info("sockname")
        log.info("[%d] browser %s joined -> game %s:%d via udp port %d (%d online)",
                 self.id, self.peer, self.game[0], self.game[1], local[1], len(Session.active) + 1)
        Session.active[self.id] = self
        first = True
        try:
            while True:
                op, payload = await asyncio.wait_for(ws_read_message(self.reader), timeout=self.idle)
                if op == 0x8:  # close
                    break
                if op == 0x9:  # ping
                    self.writer.write(ws_frame(0xA, payload))
                    continue
                if op not in (0x1, 0x2):
                    continue
                if first and len(payload) == 10 and payload.startswith(EM_PORT_PREFIX):
                    first = False
                    continue
                first = False
                self.up += 1
                self.up_bytes += len(payload)
                self.udp.sendto(payload)
        except asyncio.TimeoutError:
            log.info("[%d] browser %s idle for %ds, closing", self.id, self.peer, self.idle)
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        except ValueError as e:
            log.warning("[%d] browser %s sent a bad frame: %s", self.id, self.peer, e)
        finally:
            Session.active.pop(self.id, None)
            if self.udp:
                self.udp.close()
            try:
                self.writer.write(ws_frame(0x8, b""))
            except Exception:
                pass
            log.info("[%d] browser %s left after %ds: %d packets up (%d KB), %d down (%d KB), %d dropped (%d online)",
                     self.id, self.peer, time.time() - self.started, self.up, self.up_bytes // 1024,
                     self.down, self.down_bytes // 1024, self.dropped, len(Session.active))


def ws_frame(op, data):
    n = len(data)
    if n < 126:
        head = struct.pack("!BB", 0x80 | op, n)
    elif n < 65536:
        head = struct.pack("!BBH", 0x80 | op, 126, n)
    else:
        head = struct.pack("!BBQ", 0x80 | op, 127, n)
    return head + data


def unmask(data, mask):
    n = len(data)
    if not n:
        return data
    key = int.from_bytes((mask * (n // 4 + 1))[:n], "big")
    return (int.from_bytes(data, "big") ^ key).to_bytes(n, "big")


async def ws_read_message(reader):
    """One whole message (continuation frames joined). Returns (opcode, payload)."""
    parts, opcode = [], None
    while True:
        b0, b1 = await reader.readexactly(2)
        fin, op, masked, n = b0 & 0x80, b0 & 0x0F, b1 & 0x80, b1 & 0x7F
        if n == 126:
            n = struct.unpack("!H", await reader.readexactly(2))[0]
        elif n == 127:
            n = struct.unpack("!Q", await reader.readexactly(8))[0]
        if n > MAX_MESSAGE:
            raise ValueError("message of %d bytes" % n)
        mask = await reader.readexactly(4) if masked else None
        data = await reader.readexactly(n)
        if mask:
            data = unmask(data, mask)
        if op >= 0x8:  # control frames can arrive between fragments
            return op, data
        if op != 0x0:
            opcode = op
        parts.append(data)
        if fin:
            return opcode, b"".join(parts)


class Server:
    def __init__(self, root, game, idle):
        self.root = os.path.realpath(root)
        self.game = game
        self.idle = idle

    async def handle(self, reader, writer):
        peer = writer.get_extra_info("peername")
        peer = peer[0] if peer else "?"
        try:
            line = await asyncio.wait_for(reader.readline(), 30)
            if not line:
                return
            headers = {}
            for _ in range(100):
                h = await asyncio.wait_for(reader.readline(), 30)
                if h in (b"\r\n", b"\n", b""):
                    break
                k, _, v = h.decode("latin-1").partition(":")
                headers[k.strip().lower()] = v.strip()
            try:
                method, target, _ = line.decode("latin-1").split(" ", 2)
            except ValueError:
                return
            path = unquote(urlsplit(target).path)

            if path == "/ws" and headers.get("upgrade", "").lower() == "websocket":
                await self.websocket(reader, writer, headers, peer)
            elif path == "/bakoweb/status":
                body = json.dumps({"browsers": len(Session.active), "game": "%s:%d" % self.game}).encode()
                self.respond(writer, 200, "OK", body, {"Content-Type": "application/json", "Cache-Control": "no-store"})
            elif method in ("GET", "HEAD"):
                await self.static(writer, path, headers, method == "HEAD")
            else:
                self.respond(writer, 405, "Method Not Allowed", b"")
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionError):
            pass
        except Exception:
            log.exception("request from %s failed", peer)
        finally:
            try:
                await writer.drain()
                writer.close()
            except Exception:
                pass

    async def websocket(self, reader, writer, headers, peer):
        key = headers.get("sec-websocket-key")
        if not key or len(Session.active) >= MAX_SESSIONS:
            self.respond(writer, 503 if key else 400, "Unavailable" if key else "Bad Request", b"")
            return
        accept = base64.b64encode(hashlib.sha1(key.encode() + WS_GUID).digest()).decode()
        lines = ["HTTP/1.1 101 Switching Protocols", "Upgrade: websocket", "Connection: Upgrade",
                 "Sec-WebSocket-Accept: " + accept]
        # Emscripten asks for the "binary" subprotocol; browsers drop the connection unless it is echoed
        protocols = [p.strip() for p in headers.get("sec-websocket-protocol", "").split(",") if p.strip()]
        if protocols:
            lines.append("Sec-WebSocket-Protocol: " + ("binary" if "binary" in protocols else protocols[0]))
        writer.write(("\r\n".join(lines) + "\r\n\r\n").encode())
        await writer.drain()
        sock = writer.get_extra_info("socket")
        if sock is not None:
            import socket
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except OSError:
                pass
        await Session(reader, writer, peer, self.game, self.idle).run()

    def respond(self, writer, code, reason, body, extra=None):
        hdrs = {"Content-Length": str(len(body)), "Connection": "close"}
        hdrs.update(extra or {})
        head = "HTTP/1.1 %d %s\r\n" % (code, reason) + "".join("%s: %s\r\n" % kv for kv in hdrs.items()) + "\r\n"
        writer.write(head.encode() + body)

    async def static(self, writer, path, headers, head_only):
        full = os.path.realpath(os.path.join(self.root, path.lstrip("/")))
        if full != self.root and not full.startswith(self.root + os.sep):
            self.respond(writer, 404, "Not Found", b"not found")
            return
        if os.path.isdir(full):
            full = os.path.join(full, "index.html")
        try:
            st = os.stat(full)
        except OSError:
            self.respond(writer, 404, "Not Found", b"not found")
            return
        etag = '"%x-%x"' % (st.st_size, int(st.st_mtime))
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        extra = {"Content-Type": ctype, "ETag": etag, "Cache-Control": "no-cache"}
        if headers.get("if-none-match") == etag:
            self.respond(writer, 304, "Not Modified", b"", extra)
            return
        extra["Content-Length"] = str(st.st_size)
        extra["Connection"] = "close"
        head = "HTTP/1.1 200 OK\r\n" + "".join("%s: %s\r\n" % kv for kv in extra.items()) + "\r\n"
        writer.write(head.encode())
        if head_only:
            return
        with open(full, "rb") as f:
            while True:
                chunk = f.read(1 << 20)
                if not chunk:
                    break
                writer.write(chunk)
                await writer.drain()


def parse_hostport(s, default_port):
    host, _, port = s.rpartition(":")
    if not host:
        return s, default_port
    return host, int(port)


async def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "site-out"),
                    help="folder with index.html, darkplaces-wasm.js and the game files (make_web_pack.py output)")
    ap.add_argument("--game", default="127.0.0.1:26000", help="DarkPlaces server UDP address (default %(default)s)")
    ap.add_argument("--http-port", type=int, default=8080, help="TCP port for the page and the WebSocket (default %(default)s)")
    ap.add_argument("--bind", default="0.0.0.0", help="address to listen on (default all)")
    ap.add_argument("--idle", type=int, default=60, help="seconds of browser silence before its connection is closed")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    server = Server(a.root, parse_hostport(a.game, 26000), a.idle)
    srv = await asyncio.start_server(server.handle, a.bind, a.http_port)
    log.info("bakoweb: page http://<this machine>:%d/  ->  game server %s:%d  (files from %s)",
             a.http_port, server.game[0], server.game[1], server.root)
    async with srv:
        await srv.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
