#!/usr/bin/env python3
"""Build a self-contained HTML showcase for SkyPad Projectile Launches & Realistic Vehicle Pad Flight,
deploy progs.dat + HTML to VPS (root@72.62.241.93:22), and notify Telegram BAKOQUAKE.

Usage:
    python source/mm_tools/build_skypad_proj_vans_showcase.py --html
    python source/mm_tools/build_skypad_proj_vans_showcase.py --deploy
    TG_BOT_TOKEN=... python source/mm_tools/build_skypad_proj_vans_showcase.py --telegram
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import subprocess
import tarfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
MOD = HERE.parent.parent
SHOWCASE_HTML = MOD / "docs" / "skypad_projectiles_vans_showcase.html"

VPS_HOST = "root@72.62.241.93"
TG_CHAT_ID = "-4993867752"

REMOTE_HTML_MEGAMAN = "/var/www/megaman/skypad_projectiles_vans_showcase.html"
REMOTE_HTML_LARRYWEW = "/var/www/larrywew/bakersfield-quake/skypad-projectiles-vans.html"

LIVE_URLS = [
    "https://bakersfield.larrywew.fun/skypad_projectiles_vans_showcase.html",
    "https://davidbrazil.site/megaman/skypad_projectiles_vans_showcase.html",
    "https://larrywew.fun/bakersfield-quake/skypad-projectiles-vans.html",
]


def encode_shot(path: Path, max_w: int = 960, quality: int = 86) -> str:
    img = Image.open(path).convert("RGB")
    if img.width > max_w:
        h = int(img.height * (max_w / img.width))
        img = img.resize((max_w, h), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def build_html(shot_paths: list[tuple[str, str, Path]]) -> Path:
    cards = []
    for title, desc, p in shot_paths:
        uri = encode_shot(p)
        cards.append(
            f'<div class="shot-card">'
            f'<img src="{uri}" alt="{title}" loading="lazy"/>'
            f'<div class="shot-body"><h3>{title}</h3><p>{desc}</p></div>'
            f'</div>'
        )
    shots_html = "\n".join(cards)

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>BakersfieldQuake — SkyPad Projectiles &amp; Go-Kart Vehicle Pad Physics</title>
<style>
  :root {{
    --bg: #0b1018;
    --panel: #121a26;
    --panel2: #172233;
    --border: #273852;
    --text: #e6eef8;
    --muted: #98abc4;
    --cyan: #3ee6ff;
    --gold: #ffbe3b;
    --green: #4ade80;
    --pink: #ff6ea9;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background: radial-gradient(circle at 20% 0%, #15253d 0%, var(--bg) 55%);
    color: var(--text); line-height: 1.55;
  }}
  .wrap {{ max-width: 1120px; margin: 0 auto; padding: 28px 20px 64px; }}
  .hero {{
    background: linear-gradient(135deg, rgba(62,230,255,0.12), rgba(255,190,59,0.08));
    border: 1px solid var(--border); border-radius: 16px; padding: 26px 28px; margin-bottom: 24px;
  }}
  .eyebrow {{ color: var(--cyan); font-size: 12px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; margin: 0 0 8px; }}
  h1 {{ margin: 0 0 10px; font-size: 30px; line-height: 1.2; }}
  .sub {{ color: var(--muted); margin: 0 0 16px; max-width: 78ch; }}
  .pills {{ display: flex; flex-wrap: wrap; gap: 10px; }}
  .pill {{
    background: var(--panel2); border: 1px solid var(--border); border-radius: 999px;
    padding: 6px 14px; font-size: 13px; color: var(--text);
  }}
  code {{
    background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.08);
    padding: 1px 6px; border-radius: 5px; font-family: ui-monospace, Consolas, monospace; font-size: 0.92em; color: var(--cyan);
  }}
  h2 {{ margin: 30px 0 14px; font-size: 21px; border-left: 4px solid var(--cyan); padding-left: 12px; }}
  .grid-2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 16px; }}
  .grid-3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 16px; }}
  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 18px 20px;
  }}
  .card h3 {{ margin: 0 0 8px; font-size: 16px; color: var(--gold); }}
  .card ul {{ margin: 8px 0 0 18px; padding: 0; color: var(--muted); }}
  .card li {{ margin-bottom: 6px; }}
  .shot-card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px; overflow: hidden;
  }}
  .shot-card img {{ width: 100%; display: block; border-bottom: 1px solid var(--border); }}
  .shot-body {{ padding: 14px 16px; }}
  .shot-body h3 {{ margin: 0 0 6px; font-size: 15px; color: var(--cyan); }}
  .shot-body p {{ margin: 0; font-size: 13.5px; color: var(--muted); }}
  .sim-box {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 16px;
  }}
  canvas {{ width: 100%; height: 270px; display: block; background: #080d14; border-radius: 10px; border: 1px solid #1e2d44; }}
  .sim-controls {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; align-items: center; }}
  button {{
    background: #1a2a40; color: var(--text); border: 1px solid var(--border); border-radius: 8px;
    padding: 7px 13px; cursor: pointer; font-weight: 600; font-size: 13px;
  }}
  button:hover {{ border-color: var(--cyan); color: var(--cyan); }}
  table {{ width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; font-size: 14px; }}
  th, td {{ text-align: left; padding: 11px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  th {{ background: var(--panel2); color: var(--gold); font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; }}
  tr:last-child td {{ border-bottom: none; }}
  .tag {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
  .tag-arc {{ background: rgba(74,222,128,0.14); color: var(--green); }}
  .tag-sky {{ background: rgba(62,230,255,0.14); color: var(--cyan); }}
  .tag-home {{ background: rgba(255,190,59,0.16); color: var(--gold); }}
  .footer {{ margin-top: 34px; text-align: center; color: var(--muted); font-size: 13px; }}
</style>
</head>
<body>
<div class="wrap">
  <section class="hero">
    <p class="eyebrow">BakersfieldQuake Gameplay Update · Commit 1453f4f</p>
    <h1>SkyPad Projectile Launches &amp; Go-Kart Vehicle Pad Physics</h1>
    <p class="sub">
      All weapon, Fun Gun, custom-steered, and monster projectiles now get launched by <code>info_skypad</code> super jump pads,
      and road vehicles (vans, sedans, coupes, trucks, buses, golf carts, tuk-tuks) fly cleanly like go-karts instead of spinning wildly.
    </p>
    <div class="pills">
      <span class="pill">Live Server: <code>connect 72.62.241.93:26000</code></span>
      <span class="pill">Pad Scope: <code>info_skypad</code> (wall ladders untouched)</span>
      <span class="pill">Homing Pause: <code>0.75s</code></span>
      <span class="pill">Pad Cooldown: <code>0.65s</code> / entity</span>
    </div>
  </section>

  <h2>In-Game Zircon Captures (<code>soicowboy_bkk</code>)</h2>
  <div class="grid-3">
    {shots_html}
  </div>

  <h2>Interactive Trajectory &amp; Vehicle Attitude Preview</h2>
  <div class="sim-box">
    <canvas id="sim" width="980" height="270"></canvas>
    <div class="sim-controls">
      <button onclick="fireSim('grenade')">Launch Grenade / Mega Man (Parabolic Arc)</button>
      <button onclick="fireSim('rocket')">Launch Rocket / Nail (Straight Sky-Vector)</button>
      <button onclick="fireSim('homing')">Launch Kyle / LT / Milky (0.75s Fling then Re-Home)</button>
      <button onclick="fireSim('van')">Launch Cargo Van (Go-Kart Pitch, Zero Spin)</button>
    </div>
  </div>

  <h2>Design Notes &amp; What Changed</h2>
  <div class="grid-2">
    <div class="card">
      <h3>1. SkyPad Projectile Launching</h3>
      <ul>
        <li><b>Both engine &amp; custom physics:</b> <code>SkyPad_Touch</code> handles standard engine projectiles while <code>SkyPad_Frame</code> sweeps <code>pc_head</code>/<code>pc_spike_head</code> plus <code>MOVETYPE_NONE</code>/<code>NOCLIP</code> entities (<code>wc_shot</code>, <code>robdob</code>, <code>ec_tube</code>, <code>milky</code>, <code>ghost_follower</code>, <code>face</code>) so nothing tunnels or slips past.</li>
        <li><b>Preserves native gravity &amp; timers:</b> Gravity projectiles (grenades, Mega Man, pickles, green jar/mini guys, Wheelman, Eric Cannon) arc across the map to <code>pos1</code>; zero-gravity flyers (rockets, nails, lasers, Big Banana, Dookie) shoot straight along the launch vector into the sky. Existing fuses stay untouched.</li>
        <li><b>0.75s steering pause:</b> Guided shots (Kyle torpedo, LT Gun head, Milky, Mega Man Blue Shell, Green Mini Guys, Rob Dob drone, Eric Cannon, Shalrath/Reiver/Wizard/Carnivean/Warlord homing shots) pause steering for <code>0.75s</code> on launch so the SkyPad visibly flings them off-course before they resume mid-air.</li>
        <li><b>Throttled pad FX:</b> Plays <code>skypad/launch.wav</code> and <code>TE_TELEPORT</code> throttled at <code>0.15s</code> per pad.</li>
      </ul>
    </div>
    <div class="card">
      <h3>2. Realistic Van &amp; Car Pad Flight (Go-Kart Parity)</h3>
      <ul>
        <li><b>No more crazy spin:</b> Replaced <code>Veh_StartPadStunt</code> in <code>Veh_CheckPads</code> (for both <code>info_skypad</code> and <code>trigger_push</code>) with <code>Veh_ResetPadStunt</code>, aligning <code>angles_y = vectoyaw(hvel)</code> toward the launch trajectory and zeroing <code>veh_yawrate</code>.</li>
        <li><b>Smooth go-kart pitch &amp; level roll:</b> Driven and coasting road vehicles now smoothly pitch nose-up on climb and nose-down on descent (<code>bound(-22, veh_vz * 0.03, 22)</code>) while leveling roll (<code>angles_z -&gt; 0</code>) using <code>Veh_AngDelta</code>.</li>
        <li><b>Clean 1st-person view:</b> Without <code>veh_pad_spin</code> forced on, 1st-person drivers stay smoothly in the cab instead of snapping to spin camera or spamming horn honks.</li>
      </ul>
    </div>
  </div>

  <h2>Projectile Coverage Matrix</h2>
  <table>
    <thead>
      <tr><th>Category</th><th>Classnames</th><th>SkyPad Behavior</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><b>Weapon Projectiles</b></td>
        <td><code>missile</code>, <code>grenade</code>, <code>proximity_grenade</code> (unarmed), <code>spike</code>, <code>hiplaser</code>, <code>playershot</code>, <code>mm_tank_bar</code>, <code>jb_*</code></td>
        <td><span class="tag tag-arc">TOSS/BOUNCE -&gt; Arc</span> <span class="tag tag-sky">FLYMISSILE -&gt; Sky Vector</span></td>
      </tr>
      <tr>
        <td><b>Fun Guns &amp; Drones</b></td>
        <td><code>megaman</code>, <code>kyle_proj</code>, <code>wc_shot</code>, <code>milky</code>, <code>robdob</code>, <code>dookie_shot</code>, <code>dookie_glob</code>, <code>bigbanana</code>, <code>minibanana</code>, <code>pickle</code>, <code>greenjar_proj</code>, <code>greenguy_mini</code>, <code>netsend_disk</code>, <code>ltg_head</code>, <code>ec_tube</code></td>
        <td><span class="tag tag-home">0.75s Steering Pause</span> Grounded <code>MOVETYPE_STEP</code> runners lift off into <code>MOVETYPE_TOSS</code>.</td>
      </tr>
      <tr>
        <td><b>Monster Projectiles</b></td>
        <td><code>wizspike</code>, <code>knightspike</code>, <code>knight2spike</code>, <code>gruntspike</code>, <code>afritspike</code>, <code>furyspike</code>, <code>jimrocket</code>, <code>carniv_projectile</code>, <code>slimeball</code>, <code>ShalrathMissile</code>, <code>Reiver_fireball</code>, <code>ghost_follower</code>, <code>shamblerbeam</code>, <code>MiniGrenade</code>, <code>hknight2_homing</code>, <code>yakman_projectile</code>, <code>skull</code>, <code>skull_fly</code>, <code>face</code></td>
        <td><span class="tag tag-home">0.75s Homing Pause</span> <span class="tag tag-sky">Instant SkyPad Fling</span></td>
      </tr>
      <tr>
        <td><b>Excluded</b></td>
        <td>Shell casings, gibs, <code>bike_debris</code>, stuck <code>netsend_pc</code>, latched <code>kyle_proj</code>, stuck <code>pickle</code> / <code>proximity_grenade</code></td>
        <td>Ignored so decorative debris &amp; planted traps stay put.</td>
      </tr>
    </tbody>
  </table>

  <h2>Modified Source Files</h2>
  <table>
    <thead>
      <tr><th>File</th><th>Summary</th></tr>
    </thead>
    <tbody>
      <tr><td><code>source/qc_combat_decomp/skypad.qc</code></td><td><code>SkyPad_IsProjectile</code>, <code>SkyPad_LaunchProjectile</code>, <code>SkyPad_Frame</code> sweep/class scanner, <code>SkyPad_Touch</code> hook.</td></tr>
      <tr><td><code>source/qc_combat_decomp/vehicle_drive.qc</code></td><td>Go-kart parity in <code>Veh_CheckPads</code> (heading snap, zero spin) &amp; <code>Veh_AngDelta</code> mid-air pitch/roll smoothing.</td></tr>
      <tr><td><code>source/qc_combat_decomp/world.qc</code> &amp; <code>bm_defs.qc</code></td><td>Added <code>skypad_head</code>, <code>skypad_steer_t</code>, <code>skypad_fx_t</code>, and hooked <code>SkyPad_Frame()</code> in <code>StartFrame()</code>.</td></tr>
      <tr><td>13 Homing / Steered QC Modules</td><td>Respect <code>time &lt; skypad_steer_t</code> pause in <code>kyle.qc</code>, <code>ltgun.qc</code>, <code>milky.qc</code>, <code>megaman.qc</code>, <code>greenjar.qc</code>, <code>floathead.qc</code>, <code>wcannon.qc</code>, <code>eric_cannon.qc</code>, <code>shalrath.qc</code>, <code>reiver.qc</code>, <code>wizard.qc</code>, <code>carnivean.qc</code>, <code>warlord.qc</code>.</td></tr>
    </tbody>
  </table>

  <p class="footer">BakersfieldQuake · Self-contained showcase (zero external dependencies) · <code>connect 72.62.241.93:26000</code></p>
</div>

<script>
(() => {{
  const c = document.getElementById('sim');
  const ctx = c.getContext('2d');
  let active = null;
  let trail = [];
  let t0 = 0;

  window.fireSim = (mode) => {{
    active = mode;
    trail = [];
    t0 = performance.now();
  }};

  function step(now) {{
    ctx.clearRect(0, 0, c.width, c.height);
    // Ground & pad
    ctx.fillStyle = '#182436';
    ctx.fillRect(0, 235, c.width, 35);
    ctx.fillStyle = '#3ee6ff';
    ctx.fillRect(140, 228, 66, 8);
    ctx.fillStyle = '#ffbe3b';
    ctx.fillRect(820, 228, 66, 8);
    ctx.fillStyle = '#98abc4';
    ctx.font = '12px system-ui, sans-serif';
    ctx.fillText('info_skypad', 140, 255);
    ctx.fillText('landing pos1', 816, 255);

    if (active) {{
      const elapsed = (now - t0) / 1000;
      let x = 35, y = 212, pitch = 0, label = '';
      if (elapsed < 0.4) {{
        const k = elapsed / 0.4;
        x = 35 + k * 138;
        y = 212;
        label = active === 'van' ? 'Cargo Van approaches SkyPad' : 'Projectile enters SkyPad';
      }} else {{
        const ft = Math.min(elapsed - 0.4, 2.2);
        if (active === 'rocket') {{
          x = 173 + ft * 420;
          y = 212 - ft * 220;
          pitch = -0.48;
          label = 'MOVETYPE_FLYMISSILE: fires straight along launch vector into sky';
        }} else if (active === 'homing') {{
          if (ft < 0.75) {{
            x = 173 + ft * 330;
            y = 212 - ft * 200 + 80 * ft * ft;
            pitch = -0.35;
            label = '0.75s SkyPad fling (homing paused)';
          }} else {{
            const rt = ft - 0.75;
            x = 173 + 0.75 * 330 + rt * 280;
            y = (212 - 0.75 * 200 + 80 * 0.75 * 0.75) + rt * 110;
            pitch = 0.35;
            label = 'Steering resumed mid-air!';
          }}
        }} else {{
          const dur = 1.9;
          const u = Math.min(ft / dur, 1);
          x = 173 + u * (853 - 173);
          y = 212 - 4 * 170 * u * (1 - u);
          const dy = -4 * 170 * (1 - 2 * u) / dur;
          const dx = (853 - 173) / dur;
          pitch = Math.atan2(dy, dx);
          label = active === 'van'
            ? 'Cargo Van: nose aligned to trajectory, smooth pitch, zero barrel-roll spin'
            : 'MOVETYPE_TOSS / BOUNCE: parabolic arc to landing pos1';
        }}
      }}
      trail.push([x, y]);
      if (trail.length > 90) trail.shift();
      ctx.strokeStyle = active === 'van' ? '#4ade80' : '#3ee6ff';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      trail.forEach(([px, py], i) => i ? ctx.lineTo(px, py) : ctx.moveTo(px, py));
      ctx.stroke();

      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(pitch);
      if (active === 'van') {{
        ctx.fillStyle = '#e6eef8';
        ctx.fillRect(-20, -11, 40, 18);
        ctx.fillStyle = '#3ee6ff';
        ctx.fillRect(8, -9, 10, 7);
        ctx.fillStyle = '#0b1018';
        ctx.beginPath(); ctx.arc(-11, 8, 5, 0, Math.PI * 2); ctx.arc(11, 8, 5, 0, Math.PI * 2); ctx.fill();
      }} else {{
        ctx.fillStyle = '#ffbe3b';
        ctx.beginPath(); ctx.arc(0, 0, 7, 0, Math.PI * 2); ctx.fill();
      }}
      ctx.restore();
      ctx.fillStyle = '#e6eef8';
      ctx.fillText(label, 24, 28);
      if (elapsed > 2.8) fireSim(active);
    }} else {{
      ctx.fillStyle = '#98abc4';
      ctx.fillText('Click a launch mode below to preview the trajectory & vehicle orientation.', 24, 28);
    }}
    requestAnimationFrame(step);
  }}
  requestAnimationFrame(step);
  fireSim('van');
}})();
</script>
</body>
</html>
"""
    SHOWCASE_HTML.parent.mkdir(parents=True, exist_ok=True)
    SHOWCASE_HTML.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {SHOWCASE_HTML} ({SHOWCASE_HTML.stat().st_size:,} bytes)")
    return SHOWCASE_HTML


def deploy_to_vps() -> None:
    progs_dat = MOD / "progs.dat"
    progs_lno = MOD / "progs.lno"
    assert progs_dat.is_file(), f"Missing {progs_dat}"
    assert SHOWCASE_HTML.is_file(), f"Missing {SHOWCASE_HTML}"

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=3) as tf:
        tf.add(progs_dat, arcname="bq_game/progs.dat")
        if progs_lno.is_file():
            tf.add(progs_lno, arcname="bq_game/progs.lno")
        tf.add(SHOWCASE_HTML, arcname="web/skypad_projectiles_vans_showcase.html")
    payload = buf.getvalue()

    stamp = time.strftime("%Y%m%d-%H%M%S")
    remote_cmd = (
        "set -e; "
        "TMPD=$(mktemp -d); "
        "tar -xzf - -C \"$TMPD\"; "
        "QDIR=/opt/quake/BakersfieldQuake; "
        f"BK=/opt/quake/backup/{stamp}-skypad-proj-vans; "
        "mkdir -p \"$BK\"; "
        "for f in progs.dat progs.lno; do "
        "  if [ -f \"$QDIR/$f\" ]; then cp -p \"$QDIR/$f\" \"$BK/$f\"; fi; "
        "done; "
        "cp -f \"$TMPD/bq_game/\"* \"$QDIR/\"; "
        "chown quake:quake \"$QDIR/progs.dat\"; "
        "if [ -f \"$QDIR/progs.lno\" ]; then chown quake:quake \"$QDIR/progs.lno\"; fi; "
        "chmod a+r \"$QDIR/progs.dat\"; "
        "mkdir -p /var/www/megaman; "
        f"cp -f \"$TMPD/web/skypad_projectiles_vans_showcase.html\" {REMOTE_HTML_MEGAMAN}; "
        f"chmod a+r {REMOTE_HTML_MEGAMAN}; "
        "if [ -d /var/www/larrywew/bakersfield-quake ]; then "
        f"  cp -f \"$TMPD/web/skypad_projectiles_vans_showcase.html\" {REMOTE_HTML_LARRYWEW}; "
        f"  chmod a+r {REMOTE_HTML_LARRYWEW}; "
        "fi; "
        "PEERS=$(ss -unp | grep ':26000' || true); "
        "if [ -z \"$PEERS\" ]; then "
        "  systemctl restart quake-bakersfield.service; sleep 2; "
        "  echo \"SERVICE_RESTARTED=$(systemctl is-active quake-bakersfield.service)\"; "
        "else "
        "  echo \"PLAYERS_ACTIVE_SKIPPED_RESTART: $PEERS\"; "
        "fi; "
        "rm -rf \"$TMPD\"; "
        f"ls -lh \"$QDIR/progs.dat\" {REMOTE_HTML_MEGAMAN}"
    )
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-p", "22", VPS_HOST, remote_cmd],
        input=payload, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True,
    )
    print(proc.stdout.decode("utf-8", errors="replace"))

    for u in LIVE_URLS:
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "BakoDeployVerifier/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"[HTTP {resp.status}] {u} ({resp.headers.get('Content-Length', '?')} bytes)")
            assert resp.status == 200


def send_telegram(token: str) -> None:
    if not token:
        raise SystemExit("Missing TG_BOT_TOKEN (or --token)")
    proc_doc = subprocess.run([
        "curl.exe", "-sS", "--max-time", "120",
        "-F", f"chat_id={TG_CHAT_ID}",
        "-F", "caption=Self-contained SkyPad Projectiles & Go-Kart Vehicle Pad Physics HTML (in-game Zircon shots, interactive trajectory preview, coverage table & changelog)",
        "-F", f"document=@{SHOWCASE_HTML};type=text/html",
        f"https://api.telegram.org/bot{token}/sendDocument",
    ], capture_output=True, text=True, check=True)
    dres = json.loads(proc_doc.stdout)
    print("sendDocument:", json.dumps({"ok": dres.get("ok"), "message_id": dres.get("result", {}).get("message_id")}))
    assert dres.get("ok") is True

    msg = (
        "🚀 <b>SkyPad Projectiles &amp; Realistic Vehicle Pad Flight — Live on VPS!</b>\n\n"
        "<b>What Changed:</b>\n"
        "• <b>All Projectiles Launched by <code>info_skypad</code>:</b> Rockets, grenades, nails, lasers, Fun Guns, monster shots, plus custom-steered projectiles/drones (Wheelman, Milky, Rob Dob drone, Green Mini Guys, Eric Cannon). Keeps native gravity &amp; timers, with a <code>0.75s</code> homing/steering pause so guided shots get flung off-course before re-homing mid-air.\n"
        "• <b>Vans &amp; Cars Match Go-Karts on Jump Pads:</b> Removed wild <code>Veh_StartPadStunt</code> barrel-roll/yaw spin &amp; horn spam on road vehicles; now aligns heading to flight direction with smooth go-kart mid-air pitch and level roll.\n\n"
        "🌐 <b>Self-Contained Showcase:</b>\n"
        f"{LIVE_URLS[0]}\n"
        f"{LIVE_URLS[2]}\n\n"
        "🎮 <b>Server:</b> <code>connect 72.62.241.93:26000</code>"
    )
    data = urllib.parse.urlencode({
        "chat_id": TG_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false",
    }).encode("utf-8")
    with urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST"), timeout=30) as resp:
        mres = json.loads(resp.read().decode("utf-8"))
    print("sendMessage:", json.dumps({"ok": mres.get("ok"), "message_id": mres.get("result", {}).get("message_id")}))
    assert mres.get("ok") is True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--telegram", action="store_true")
    ap.add_argument("--shots-dir", default="")
    ap.add_argument("--token", default=os.environ.get("TG_BOT_TOKEN", ""))
    args = ap.parse_args()

    if args.html:
        sdir = Path(args.shots_dir)
        pngs = sorted(sdir.glob("*.png"))
        assert len(pngs) >= 3, f"Expected >= 3 screenshots in {sdir}, found {len(pngs)}"
        shots = [
            ("1. Rockets & Grenades Hit info_skypad", "Rockets and grenades fired into the glowing Soi Cowboy East SkyPad launch across the district along the pad's trajectory.", pngs[0]),
            ("2. Wheelman (MOVETYPE_NONE) Launch", "Even custom-stepped projectiles like Wheelman trigger the SkyPad vortex flash and soar sky-high.", pngs[1]),
            ("3. Cargo Van — Clean Go-Kart Pad Flight", "Vans and cars align nose-first along the flight path with smooth pitch and zero barrel-roll spin.", pngs[2]),
        ]
        build_html(shots)
    if args.deploy:
        deploy_to_vps()
    if args.telegram:
        send_telegram(args.token)


if __name__ == "__main__":
    main()
