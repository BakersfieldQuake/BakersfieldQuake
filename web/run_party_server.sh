#!/usr/bin/env bash
# One command on the party server (any Linux box with Docker and git): builds whatever is missing, makes the
# web pack from the game folder, and starts two containers:
#   bako-game   DarkPlaces dedicated server, UDP 26000 (Windows players connect here directly)
#   bako-web    bakoweb.py: the browser page + WebSocket bridge on TCP 8080
#
#   ./run_party_server.sh /path/to/BAKOQUAKE              (folder with id1, quake15, BakersfieldQuake)
#   NET_ADDRESS=192.168.1.50 ./run_party_server.sh ...    only if the box has two IPs on the LAN (see README-WEB.md)
#
# Stop:  docker rm -f bako-game bako-web        Logs:  docker logs -f bako-game   /   docker logs -f bako-web
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
GAME_DIR="$(cd "${1:-$HERE/../../dist/BAKOQUAKE}" && pwd)"
NET_ADDRESS="${NET_ADDRESS:-}"
GAME_PORT="${GAME_PORT:-26000}"
WEB_PORT="${WEB_PORT:-8080}"
cd "$HERE"
for d in id1 quake15 BakersfieldQuake; do
	[ -d "$GAME_DIR/$d" ] || { echo "no $d in $GAME_DIR"; exit 1; }
done

docker build -q -t bakoweb-runtime:local server >/dev/null
[ -x server-out/darkplaces-dedicated ] || DP_WORK="$HERE/.work-server" ./server/build_server.sh server-out
[ -f wasm-out/darkplaces-wasm.js ] || DP_WORK="$HERE/.work-wasm" ./engine/build_wasm.sh wasm-out

# the pack copies the game files next to the page; run it in the runtime image so the host needs no python
docker run --rm -u "$(id -u):$(id -g)" -v "$HERE:/srv/web" -v "$GAME_DIR:/srv/game:ro" bakoweb-runtime:local \
	python3 /srv/web/make_web_pack.py --game-dir /srv/game --engine /srv/web/wasm-out/darkplaces-wasm.js --out /srv/web/site-out

bind=()
[ -n "$NET_ADDRESS" ] && bind=(+net_address "$NET_ADDRESS")
docker rm -f bako-game bako-web >/dev/null 2>&1 || true

# Host networking so the Windows launcher's LAN search (UDP broadcast) still finds the server.
# Flood limits off: every browser player arrives from this machine's address, and the default 5 s per-address
# connect block keeps a second browser out while the first one is joining.
docker run -d --name bako-game --restart unless-stopped --network host \
	-v "$GAME_DIR:/srv/game" -v "$HERE/server-out:/srv/server-out:ro" -w /srv/game bakoweb-runtime:local \
	/srv/server-out/darkplaces-dedicated -basedir /srv/game -dedicated 16 -port "$GAME_PORT" "${bind[@]}" \
	-game quake15 -game BakersfieldQuake +exec server.cfg \
	+net_connectfloodblockingtimeout 0 +net_challengefloodblockingtimeout 0 >/dev/null

docker run -d --name bako-web --restart unless-stopped --network host \
	-v "$HERE:/srv/web:ro" bakoweb-runtime:local \
	python3 /srv/web/bakoweb.py --root /srv/web/site-out --http-port "$WEB_PORT" \
	--game "${NET_ADDRESS:-127.0.0.1}:$GAME_PORT" >/dev/null

ip="${NET_ADDRESS:-$(hostname -I 2>/dev/null | awk '{print $1}')}"
echo
echo "  Browser players open:   http://$ip:$WEB_PORT"
echo "  Windows players:        PLAY finds the server on the LAN, or console: connect $ip:$GAME_PORT"
echo "  Logs:                   docker logs -f bako-game   /   docker logs -f bako-web"
