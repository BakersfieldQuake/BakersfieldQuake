# Bakersfield Quake in the browser

Browser players (Mac or Windows; Chrome, Edge, Firefox or Safari 15+) open one address on the LAN and play in
the same match as people using the normal BAKOQUAKE zip. Nothing to install.

```
Browser ── http://<server>:8080  page + engine + game files (kept in the browser after the first visit)
        └─ ws://<server>:8080/ws ── bakoweb.py ── UDP ──► darkplaces-dedicated :26000 ◄── UDP ── Windows players
```

- **Engine:** DarkPlaces compiled to WebAssembly (WebGL2), pinned at `ef764984`, with the fixes in
  `engine/patches/` (see below). It's built by `engine/build_wasm.sh`.
- **Bridge:** `bakoweb.py` (Python 3, standard library only).
  - It serves the page and the files.
  - It turns each browser's WebSocket into its own UDP socket to the game server.
  - The game server is unchanged: browser players look like normal clients coming from the server machine.
- **Game server:** the same DarkPlaces the VPS runs (`72ae1712` from 2017, plus the VPS patches), built by
  `server/build_server.sh`.

## Party night: Linux box with Docker

```bash
./run_party_server.sh /path/to/BAKOQUAKE
```

`/path/to/BAKOQUAKE` is the unpacked zip: the folder holding `id1`, `quake15` and `BakersfieldQuake`.

**What the script does:**
- The first run builds the two engines in Docker, about 5 minutes. Later runs reuse them.
- It copies the game files into `site-out/` and starts two containers, `bako-game` and `bako-web`.
- It prints the address to hand out, for example `http://192.168.1.50:8080`.

**Server settings.** The match uses `BakersfieldQuake/server.cfg` from that folder, the same as the Windows
"Start Server". That covers map, rotation, time limit and the mod settings.

**Ports.** UDP 26000 for the game and TCP 8080 for the page. Open both if the box has a firewall.

**The server box has two IP addresses on the LAN (wired and Wi-Fi, or two NICs)?** Start it like this, with
the address players use:

```bash
NET_ADDRESS=192.168.1.50 ./run_party_server.sh /path/to/BAKOQUAKE
```

Without it, the server can answer from the other address, and the Windows game ignores those replies
("Connect: Failed"). Browsers are not affected.

**Stop and logs:**
```bash
docker rm -f bako-game bako-web
```
```bash
docker logs -f bako-web
```

## Party night: Windows server instead

1. Run the zip's `Start Server.cmd` as usual.
2. Check `BakersfieldQuake\server.cfg` has the browser settings (in it since 2026-11-12; see "Server settings the
   party needs" below).
3. Copy a built `site-out\` folder over. The engine has to be built on Linux, for example cccbox. It must be built
   from the same game folder and `server.cfg` the server runs: browsers only get the maps that file names.
4. Run `py bakoweb.py --root site-out --game 127.0.0.1:26000 --http-port 8080`.
5. Allow TCP 8080 in the Windows firewall (Private network).

## Server settings the party needs (BakersfieldQuake/server.cfg)

| Setting | Why |
| --- | --- |
| `bm_preload 2` | The Wheelman Cannon (300 MB of sprites) and Mystery Box characters load with the map. Loading them on first use froze every player for ~3 s (measured in the browser; native clients stall too). |
| `monster_health_crosshair 0` and the other 5 crosshair/psycho cvars | Combat+ sends them to every player every frame as reliable data. Same fix as the VPS: a laggy or paused player can't overflow the queue and get dropped. |
| `net_connectfloodblockingtimeout 0`, `net_challengefloodblockingtimeout 0` | All browsers come from the bridge's address; the 5 s per-address block refuses the second one. |

**Maps.** A vote or rotation map the pack doesn't have kicks browser players. A map missing on the server only
prints "no map file" and play goes on. `run_party_server.sh` rebuilds the pack from `server.cfg` each start, so edit
`server.cfg` first, then run it.

## For players

1. Open the address and type a name.
2. Wait for the bar to fill, then press **PLAY**.
   - The first visit downloads about 1.8 GB: under a minute on wired gigabit, several minutes on busy Wi-Fi.
   - Later visits load from the browser's own storage.
3. Click the game to grab the mouse. **Esc** lets go of it.
4. Same keys as the Windows game.
5. If the screen goes black or the game stops, the page says so and shows **Rejoin** (about a minute, nothing
   to download). If that doesn't bring it back, close the tab and open the address in a new one.

## Known differences from the Windows game

- **No full-screen post-processing.** It draws a black screen in the browser build, so `site/web.cfg` turns it off:
  - neutral gamma and contrast, so the picture is a little darker than on Windows
  - no screen flashes on pickup, damage or quad
- **Lighter graphics.** No water reflections, relief mapping or realtime shadow maps.
- **Memory.** A browser tab holds the whole game in memory, about 2 GB on top of the browser itself, and the
  engine's own memory peaked at 1.2 GB of its 2 GB limit (bakolansmall after downtown, with `bm_preload 2`). Close
  other heavy tabs. Under GPU or memory pressure a browser can drop the game's WebGL context; the page then offers
  Rejoin (seen once in a 4-client test on one PC).
- **Gun skins** (M4, Thompson, M1 Garand) live in `models/cs16/` and `models/dod/`. `build_pk3.py` packs `models/`
  since 2026-11-12; before that the skins only existed as loose files on the dev PC.
- **Package gap, also in the Windows zip:** `progs/wheelman_historic.spr32` (used only by the intro) exists nowhere.

## Testing and debugging

- **URL options:**
  - `?map=start` plays offline, no server.
  - `?debug` copies the engine console to the browser console.
  - `?extra=%2Bcvar%20value` adds command-line options.
  - `?server=host:port` is used as the `connect` address. The bridge decides the real target with `--game`.
- **From the browser devtools console:**
  `Module.ccall('bako_cmd', null, ['string'], ['condump x.txt'])`, then
  `Module.FS.readFile('/home/web_user/.darkplaces/BakersfieldQuake/x.txt', {encoding: 'utf8'})`.
  Don't touch other `Module.*` internals: the engine aborts on unexported ones.
- **Test rig on cccbox:** `/mnt/user/appdata/bakoweb`. Containers `bakoweb-sv` (UDP 26010) and `bakoweb-test`
  (page on 8099).

## Engine patches (engine/patches)

| Patch | Fixes |
| --- | --- |
| 0001 | Cube map size was never read on WebGL, so the first cubemap aborted the engine |
| 0002 | `bako_cmd` console hook, plus the FS/ccall exports for the page and debugging |
| 0003 | libpng, libjpeg and libvorbis linked in. They were dlopen-only, so no PNG textures, JPEG TVs or OGG sound |
| 0004 | `CLOCK_MONOTONIC_RAW` returns garbage in the browser runtime; the game clock froze and maps never finished loading |

`engine/pre.js` replaces DarkPlaces' file loader: the page hands it the downloaded files, and stdin is kept
empty, because the default stdin opens a browser prompt every frame.
