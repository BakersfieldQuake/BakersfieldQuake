"""Parallel 16-Core Builder for Bryan's DOZEN (12) Over-The-Top 360° High-FPS
Conspiracy Theorist, Nunchuck, Sword & Nerd Animation Sets!

Each of the 12 sets generates:
  - 8 full 360° camera directions (0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°)
  - 24 distinct fluid frames per direction = 192 RGBA frames per set (2,304 new frames total!)
  - Packed into an 8x24 RGBA WebP sprite-sheet atlas in bryan_sprite/atlases/<id>.webp
    for 60-120 FPS hardware-accelerated <canvas> playback in bryan_demons.html!
"""
import concurrent.futures
import math
import os
import random
import sys
import time
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conspiracy_props as cp

MOD_DIR = r"G:\Quake\Combat\BakersfieldQuake"
WEB_DIR = os.path.join(MOD_DIR, "bryan_sprite")
ATLAS_DIR = os.path.join(WEB_DIR, "atlases")
os.makedirs(ATLAS_DIR, exist_ok=True)

FW, FH = cp.FW, cp.FH
CX, GY = cp.CX, cp.GY
NF = 24  # 24 high-FPS frames per angle x 8 angles = 192 frames per animation set!

DOZEN_SPECS = [
    ("flat_earth", "🌍❄️ Flat Earth Frisbee & Globe Punt", "Conspiracy", 50),
    ("corkboard", "🧶📌 Pepe Silvia Red-String Meltdown", "Conspiracy", 55),
    ("chemtrails", "✈️🐸 Chemtrail Gay-Frog Leafblower", "Conspiracy", 50),
    ("five_g", "📡🐦 5G Tower vs. Faraday Dome", "Conspiracy", 60),
    ("illuminati", "👁️🔺 Illuminati Eye Megaphone Blast", "Conspiracy", 50),
    ("ufo_naruto", "🛸🏃 Area-51 Naruto-Run & Backup Hat", "Conspiracy", 60),
    ("nunchuck_god", "🥢🔥 Quad Flaming Nunchucks + BONK!", "Weapons", 60),
    ("katana_anime", "⚔️🌸 Dual Katana Anime Judgment-Cut", "Weapons", 60),
    ("lightsaber_paladin", "🗡️⚡ Rune Greatsword & Dual Lightsaber", "Weapons", 60),
    ("dnd_nat20", "🎲🧙 D&D Critical Nat-20 Fireball", "Nerd", 50),
    ("super_saiyan", "🔥⚡ Super-Tinfoil Saiyan Kamehameha", "Nerd", 60),
    ("matrix_larp", "🕶️💊 Matrix 62° Bullet-Time & Power-Glove", "Nerd", 60),
]


def build_props_bundle():
    return {
        "flat_disc": cp.make_flat_earth_disc(),
        "globe": cp.make_nasa_globe(),
        "cork_f": cp.make_corkboard(True),
        "cork_b": cp.make_corkboard(False),
        "jet": cp.make_jet_plane(),
        "frog": cp.make_rainbow_frog(),
        "tower": cp.make_5g_tower(),
        "pigeon": cp.make_pigeon_drone(),
        "pyramid": cp.make_illuminati_pyramid(),
        "ufo": cp.make_ufo_saucer(),
        "katana": cp.make_katana(),
        "greatsword": cp.make_rune_greatsword(),
        "lightsaber": cp.make_dual_lightsaber(),
        "d20": cp.make_d20_die(False),
        "d20_crit": cp.make_d20_die(True),
        "dm_screen": cp.make_dm_screen(),
        "bullet": cp.make_matrix_bullet(),
    }


# ==============================================================================
# SCENE 1: FLAT EARTH ICE-WALL FRISBEE & NASA GLOBE PUNT
# ==============================================================================
def scene_flat_earth(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    cp.draw_shadow(canvas, CX, GY, 28, 7)

    # Orbiting 3D Flat Earth Disc w/ Ice Wall & Firmament Dome + upside-down peeking mini Crimson Demon!
    lx = math.cos(ang) * 78.0
    ly = math.sin(ang) * 86.0
    lz = 112.0 + 18.0 * math.sin(ang * 2.0)
    sx, sy, dz, sc = cp.project_3d(lx, ly, lz, d)
    sx_c = float(np.clip(sx, 50, FW - 50))
    sy_c = float(np.clip(sy, 44, GY - 28))

    # Punted 'FAKE NASA CGI' round basketball globe getting booted skyward on frames 10..23!
    kick_phase = (f - 8) / 15.0 if f >= 8 else -1.0
    g_sx, g_sy, g_dz, g_sc = cp.project_3d(42.0 + max(0.0, kick_phase) * 75.0, -18.0, 18.0 + max(0.0, kick_phase) * 165.0, d)

    def draw_disc_and_demon():
        # Motion trail arc behind flying Flat Earth frisbee
        td = ImageDraw.Draw(canvas)
        for tr in range(1, 5):
            pa = ang - tr * 0.16
            tx, ty, _, _ = cp.project_3d(math.cos(pa) * 78.0, math.sin(pa) * 86.0, 112.0 + 18.0 * math.sin(pa * 2.0), d)
            td.ellipse([tx - 24 + tr * 3, ty - 7 + tr, tx + 24 - tr * 3, ty + 7 - tr],
                       outline=(110, 235, 255, max(20, 145 - tr * 30)), width=2)
        # Cheeky upside-down mini Crimson Demon clinging under the Flat Earth crust!
        c_im, _ = rigs["crimson"][(d + f // 3) % 8]
        cp.paste_rgba_center(canvas, c_im, sx_c, sy_c + 24 * sc, scale=0.22 * sc, rot_deg=180.0 + 14.0 * math.sin(ang * 3))
        cp.paste_rgba_center(canvas, props["flat_disc"], sx_c, sy_c, scale=0.82 * sc, rot_deg=8.0 * math.sin(ang * 2))

    def draw_globe_punt():
        if f < 8:
            # Globe bouncing toward Bryan's sneaker
            by_b = abs(math.sin(ph * 6 * math.pi)) * 18.0
            bx0, by0, _, bsc = cp.project_3d(34.0, -14.0, 16.0 + by_b, d)
            cp.paste_rgba_center(canvas, props["globe"], bx0, by0, scale=0.72 * bsc, rot_deg=f * 32.0)
        elif kick_phase < 0.82:
            cp.paste_rgba_center(canvas, props["globe"], g_sx, g_sy, scale=0.74 * g_sc, rot_deg=f * 55.0)
        else:
            # Explodes into red 'FAKE CGI!!' starburst!
            ed = ImageDraw.Draw(canvas)
            ex, ey = np.clip(g_sx, 36, FW - 36), np.clip(g_sy, 32, 120)
            for i in range(10):
                ea = i * (2 * math.pi / 10) + ph * 4
                r1 = 8 + (kick_phase - 0.82) * 120
                ed.line([(ex, ey), (ex + math.cos(ea) * r1, ey + math.sin(ea) * r1)], fill=(255, 70, 55, 235), width=3)
                ed.ellipse([ex - 10, ey - 10, ex + 10, ey + 10], fill=(255, 240, 110, 210))

    items = [
        (dz, draw_disc_and_demon),
        (g_dz, draw_globe_punt),
        (0.0, lambda: cp.render_bryan_3d(
            canvas, rigs, d, CX, GY,
            lz=abs(math.sin(ang * 2)) * 7.0,
            run_frame=(f // 2) % 6,
            pitch_fwd_deg=-10.0 if (8 <= f <= 12) else 6.0 * math.sin(ang),
        )),
    ]
    for _, fn in sorted(items, key=lambda x: -x[0]):
        fn()


# ==============================================================================
# SCENE 2: PEPE SILVIA RED-STRING CORKBOARD MELTDOWN
# ==============================================================================
def scene_corkboard(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    rng = random.Random(2200 + d * 53 + f * 17)
    # 60 Hz hyper-caffeinated jitter!
    jx = rng.randint(-3, 3)
    jy = rng.randint(-2, 2)
    cp.draw_shadow(canvas, CX + jx, GY, 29, 7)

    # Floating 3D Conspiracy Corkboard positioned at Bryan's front-left (lx=+28, ly=+58, lz=132)
    bsx, bsy, bdz, bsc = cp.project_3d(28.0, 58.0, 132.0 + 4.0 * math.sin(ang * 2), d)
    bsx = float(np.clip(bsx, 48, FW - 48))
    # Board faces roughly toward camera/Bryan front: show front cork if cos(phi - 0.35) >= 0 else wooden duct-tape back!
    phi = math.radians(d * 45.0)
    facing_cam = math.cos(phi - 0.45)
    board_im = props["cork_f"] if facing_cam >= 0 else props["cork_b"]
    # Horizontal 3D perspective squeeze as board turns edge-on!
    w_persp = max(0.28, abs(facing_cam))

    def draw_board():
        bw = max(14, int(round(board_im.width * 0.92 * bsc * w_persp)))
        bh = max(18, int(round(board_im.height * 0.92 * bsc)))
        warped = board_im.resize((bw, bh), Image.BILINEAR)
        cp.paste_rgba_center(canvas, warped, bsx, bsy)

    # 3 Orbiting Radioactive-Green 'TRUTH FUEL' Energy Cans!
    can_items = []
    for ci in range(3):
        ca = ang * 2.0 + ci * (2 * math.pi / 3)
        csx, csy, cdz, csc = cp.project_3d(math.cos(ca) * 44, math.sin(ca) * 44, 72 + 18 * math.sin(ca * 2), d)

        def draw_can(x=csx, y=csy, s=csc, rot=f * 30 + ci * 90):
            im_c = Image.new("RGBA", (18, 26), (0, 0, 0, 0))
            cd = ImageDraw.Draw(im_c)
            cd.rectangle([3, 3, 14, 22], fill=(25, 30, 36, 255), outline=(75, 255, 95, 255), width=2)
            cd.line([(6, 7), (11, 18)], fill=(80, 255, 110, 255), width=2)
            cp.paste_rgba_center(canvas, im_c, x, y, scale=s * 0.85, rot_deg=rot)

        can_items.append((cdz, draw_can))

    hx_out = [CX, GY - 180]

    def draw_bryan():
        hx, hy, _, _ = cp.render_bryan_3d(
            canvas, rigs, d, CX + jx, GY + jy,
            lz=abs(math.sin(ang * 4)) * 5.0,
            run_frame=(f // 2) % 6 if (f % 4 < 2) else None,
            roll_deg=5.5 * math.sin(ang * 3),
        )
        hx_out[0], hx_out[1] = hx, hy

    items = [(bdz, draw_board), (0.0, draw_bryan)] + can_items
    for _, fn in sorted(items, key=lambda x: -x[0]):
        fn()

    # Red Laser Pointer sweeping wildly from Bryan's hand to random pin on the corkboard + exclamation sparks!
    dr = ImageDraw.Draw(canvas)
    hsx, hsy, _, _ = cp.project_3d(22.0, 16.0, 108.0, d, CX + jx, GY + jy)
    tx = bsx + math.sin(ang * 5.0) * 22.0 * w_persp
    ty = bsy + math.cos(ang * 4.0) * 18.0
    cp.draw_glow_line(dr, (hsx, hsy), (tx, ty), (255, 235, 235, 255), (255, 25, 45, 155), 1, 5)
    dr.ellipse([tx - 4, ty - 4, tx + 4, ty + 4], fill=(255, 35, 50, 255))
    # Panicked yellow/red '!!' sparks popping off Bryan's vibrating tinfoil hat
    for si in range(4):
        sa = -math.pi * 0.5 + (si - 1.5) * 0.45 + 0.2 * math.sin(ang * 4)
        x0 = hx_out[0] + math.cos(sa) * 18
        y0 = hx_out[1] + math.sin(sa) * 18
        x1 = hx_out[0] + math.cos(sa) * 30
        y1 = hx_out[1] + math.sin(sa) * 30
        dr.line([(x0, y0), (x1, y1)], fill=(255, 230, 65, 245), width=3)


# ==============================================================================
# SCENE 3: CHEMTRAIL GAY-FROG HAZMAT LEAFBLOWER DEFENSE
# ==============================================================================
def scene_chemtrails(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    cp.draw_shadow(canvas, CX, GY, 28, 7)

    # 2 White Government Jets circling high overhead laying neon pink/lime chemtrail clouds!
    jet_draws = []
    for ji in range(2):
        ja = ang + ji * math.pi
        jsx, jsy, jdz, jsc = cp.project_3d(math.cos(ja) * 82.0, math.sin(ja) * 92.0, 212.0, d)
        vx = -math.sin(ja) * (-math.sin(math.radians(d * 45))) + math.cos(ja) * math.cos(math.radians(d * 45))

        def draw_jet_and_plume(ja0=ja, x=jsx, y=jsy, s=jsc, flip=(vx < 0), idx=ji):
            dr = ImageDraw.Draw(canvas)
            col_c = (255, 95, 215, 115) if idx == 0 else (125, 255, 95, 115)
            for st in range(1, 8):
                pa = ja0 - st * 0.20
                px, py, _, ps = cp.project_3d(math.cos(pa) * 82.0, math.sin(pa) * 92.0, 212.0 - st * 2.0, d)
                r = int((5 + st * 2.1) * ps)
                dr.ellipse([px - r, py - r // 2, px + r, py + r // 2], fill=col_c)
            cp.paste_rgba_center(canvas, props["jet"], x, y, scale=0.82 * s, flip_x=flip)

        jet_draws.append((jdz, draw_jet_and_plume))

    # 3 Hopping Rainbow Frogs bouncing in 3D circles around Bryan's Vans sneakers!
    frog_draws = []
    for fi in range(3):
        fa = -ang + fi * (2 * math.pi / 3)
        hop = abs(math.sin(ang * 3 + fi * 1.1)) * 26.0
        fsx, fsy, fdz, fsc = cp.project_3d(math.cos(fa) * 56.0, math.sin(fa) * 62.0, 12.0 + hop, d)

        def draw_frog(x=fsx, y=fsy, s=fsc, h=hop):
            cp.draw_shadow(canvas, x, GY + 2, 9, 3, alpha=55)
            cp.paste_rgba_center(canvas, props["frog"], x, y, scale=0.88 * s, rot_deg=8.0 if h > 12 else 0.0)

        frog_draws.append((fdz, draw_frog))

    def draw_bryan_and_blower():
        cp.render_bryan_3d(
            canvas, rigs, d, CX, GY,
            lz=abs(math.sin(ang * 2)) * 4.0,
            roll_deg=7.0 * math.sin(ang),
            hat_mode="triple_dish",
        )
        # Swirling upward Cyan/White Leafblower Vortex Tornado blasting from Bryan's hands into the sky!
        hsx, hsy, _, _ = cp.project_3d(24.0, -14.0, 112.0, d)
        dr = ImageDraw.Draw(canvas)
        sway = math.sin(ang * 2) * 28.0
        for lv in range(10):
            u = lv / 9.0
            vy = hsy - u * 135.0
            vx_c = hsx + sway * u + math.sin(ang * 4 + lv) * (4 + 14 * u)
            rw = int(5 + u * 26)
            dr.ellipse([vx_c - rw, vy - 5, vx_c + rw, vy + 5],
                       outline=(115, 245, 255, int(195 * (1.0 - 0.55 * u))), width=2)

    items = jet_draws + frog_draws + [(0.0, draw_bryan_and_blower)]
    for _, fn in sorted(items, key=lambda x: -x[0]):
        fn()


# ==============================================================================
# SCENE 4: 5G MIND-CONTROL TOWER VS. TINFOIL FARADAY DOME ('BIRDS AREN'T REAL')
# ==============================================================================
def scene_five_g(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    cp.draw_shadow(canvas, CX, GY, 29, 7)

    # 3D 5G Cell Tower stationed at (-52, -66)
    tsx, tsy, tdz, tsc = cp.project_3d(-52.0, -66.0, 74.0, d)
    tsx = float(np.clip(tsx, 36, FW - 36))

    # Orbiting 'BIRDS AREN'T REAL' Surveillance Pigeon Drone!
    pa = ang * 2.0
    psx, psy, pdz, psc = cp.project_3d(math.cos(pa) * 68.0, math.sin(pa) * 76.0, 168.0 + 12.0 * math.sin(pa * 2), d)
    psx = float(np.clip(psx, 32, FW - 32))

    head_pos = [CX, GY - 180]

    def draw_tower():
        cp.draw_shadow(canvas, tsx,tsy + 68 * tsc, 18, 5, alpha=65)
        cp.paste_rgba_center(canvas, props["tower"], tsx, tsy, scale=0.88 * tsc)

    def draw_pigeon():
        # Red surveillance laser cone from pigeon camera eye toward Bryan's head!
        dr = ImageDraw.Draw(canvas)
        dr.polygon([(psx, psy), (CX - 12, GY - 148), (CX + 12, GY - 148)], fill=(255, 25, 45, 55))
        cp.paste_rgba_center(canvas, props["pigeon"], psx, psy, scale=0.92 * psc, flip_x=(psx > CX))

    def draw_bryan_faraday():
        hx, hy, _, _ = cp.render_bryan_3d(
            canvas, rigs, d, CX, GY,
            lz=abs(math.sin(ang * 3)) * 3.0,
            roll_deg=3.0 * math.sin(ang * 4),
        )
        head_pos[0], head_pos[1] = hx, hy
        # Glowing Cyan Tinfoil Faraday Force-Dome around Bryan's upper body & hat!
        dr = ImageDraw.Draw(canvas)
        pulse = int(135 + 75 * math.sin(ang * 4))
        dr.arc([CX - 54, hy - 18, CX + 54, GY - 52], start=175, end=365, fill=(95, 245, 255, pulse), width=4)
        dr.arc([CX - 50, hy - 14, CX + 50, GY - 56], start=180, end=360, fill=(255, 255, 255, pulse), width=2)

    items = [(tdz, draw_tower), (pdz, draw_pigeon), (0.0, draw_bryan_faraday)]
    for _, fn in sorted(items, key=lambda x: -x[0]):
        fn()

    # Incoming Magenta 5G Mind-Waves from Tower -> RICOCHETING off Bryan's Tinfoil Hat as Gold/Cyan Faraday Bolts!
    dr = ImageDraw.Draw(canvas)
    em_x, em_y = tsx, tsy - 52 * tsc
    hx, hy = head_pos
    for wi in range(3):
        u = ((ph * 3.0 + wi / 3.0) % 1.0)
        wx = em_x + (hx - em_x) * u
        wy = em_y + (hy - em_y) * u
        r = int(6 + u * 12)
        dr.ellipse([wx - r, wy - r, wx + r, wy + r], outline=(255, 55, 220, int(225 * (1.0 - 0.3 * u))), width=2)
    # Deflection lightning zapping back into the Pigeon Drone!
    mid_x = (hx + psx) * 0.5 + math.sin(ang * 8) * 10
    mid_y = (hy + psy) * 0.5 - 12
    cp.draw_glow_line(dr, (hx, hy + 4), (mid_x, mid_y), (255, 255, 255, 255), (80, 245, 255, 195), 2, 6)
    cp.draw_glow_line(dr, (mid_x, mid_y), (psx, psy), (255, 250, 150, 255), (255, 200, 40, 195), 2, 6)


# ==============================================================================
# SCENE 5: REPTILIAN ILLUMINATI PYRAMID & SOVEREIGN-CITIZEN MEGAPHONE BLAST
# ==============================================================================
def scene_illuminati(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    cp.draw_shadow(canvas, CX, GY, 29, 7)

    # Levitating 3D All-Seeing Pyramid offset front-right (lx=+58, ly=-38) so Bryan's face is 100% clear even at 0°!
    psx, psy, pdz, psc = cp.project_3d(58.0, -38.0 + 10.0 * math.sin(ang), 148.0 + 10.0 * math.sin(ang * 2), d)
    psx = float(np.clip(psx, 42, FW - 42))
    rsx, rsy, rdz, rsc = cp.project_3d(-48.0 * math.cos(ang), -58.0 * math.sin(ang), 96.0, d)
    rsx = float(np.clip(rsx, 42, FW - 42))

    def draw_pyramid():
        dr = ImageDraw.Draw(canvas)
        # Eerie emerald tractor-cone under Illuminati Pyramid
        dr.polygon([(psx, psy), (psx - 28 * psc, GY - 10), (psx + 28 * psc, GY - 10)], fill=(50, 235, 95, 48))
        cp.paste_rgba_center(canvas, props["pyramid"], psx, psy, scale=0.92 * psc, rot_deg=6.0 * math.sin(ang * 2))
        # Golden sonic fracture sparks when megaphone waves slam into the pyramid!
        if f % 3 != 0:
            for k in range(5):
                ka = k * 1.25 + ang * 3
                dr.line([(psx, psy), (psx + math.cos(ka) * 26, psy + math.sin(ka) * 26)], fill=(255, 240, 120, 230), width=2)

    def draw_reaper():
        r_im, _ = rigs["reaper"]
        cp.paste_rgba_center(canvas, r_im, rsx, rsy, scale=0.62 * rsc, alpha_mul=0.82)

    def draw_bryan_megaphone():
        cp.render_bryan_3d(
            canvas, rigs, d, CX, GY,
            lz=abs(math.sin(ang * 2)) * 5.0,
            pitch_fwd_deg=-8.0 + 12.0 * math.sin(ang * 2),
        )
        # Megaphone + Glowing Golden Cross + Expanding 3D Sonic Truth-Rings toward Pyramid!
        msx, msy, _, msc = cp.project_3d(24.0, -8.0, 142.0, d)
        dr = ImageDraw.Draw(canvas)
        # Golden Cross held high in left hand
        csx, csy, _, _ = cp.project_3d(20.0, 24.0, 152.0 + 4.0 * math.sin(ang * 4), d)
        cp.draw_glow_line(dr, (csx, csy - 13), (csx, csy + 13), (255, 250, 190, 255), (255, 200, 40, 190), 3, 7)
        cp.draw_glow_line(dr, (csx - 9, csy - 4), (csx + 9, csy - 4), (255, 250, 190, 255), (255, 200, 40, 190), 3, 7)
        # Sonic rings propagating from (msx, msy) to (psx, psy)
        for ri in range(4):
            u = ((ph * 2.0 + ri * 0.25) % 1.0)
            wx = msx + (psx - msx) * u
            wy = msy + (psy - msy) * u
            rw = int(6 + u * 24)
            dr.ellipse([wx - rw // 2, wy - rw, wx + rw // 2, wy + rw],
                       outline=(255, 220, 65, int(235 * (1.0 - 0.55 * u))), width=3)

    items = [(pdz, draw_pyramid), (rdz, draw_reaper), (0.0, draw_bryan_megaphone)]
    for _, fn in sorted(items, key=lambda x: -x[0]):
        fn()


# ==============================================================================
# SCENE 6: AREA-51 45° NARUTO-RUN & UFO BACKUP-TINFOIL-HAT ABDUCTION
# ==============================================================================
def scene_ufo_naruto(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    cp.draw_shadow(canvas, CX, GY, 32, 7)

    # Speed-mirage Naruto afterimages trailing behind Bryan (-lx)!
    for ghost_i in (2, 1):
        gsx, _, _, _ = cp.project_3d(-ghost_i * 18.0, 0.0, 0.0, d)
        cp.render_bryan_3d(
            canvas, rigs, d, gsx, GY,
            lz=abs(math.sin(ang * 4 - ghost_i * 0.6)) * 8.0,
            run_frame=(f - ghost_i) % 6,
            pitch_fwd_deg=36.0,
            alpha_mul=0.28 if ghost_i == 2 else 0.45,
            tint=(0.45, 1.35, 1.55) if ghost_i == 1 else (1.45, 0.55, 1.45),
        )

    # UFO tractor beam tugging Bryan's main tinfoil hat off his head (revealing his TINY BACKUP TINFOIL HAT!)
    tug = max(0.0, math.sin(ph * math.pi)) ** 1.3
    hat_lift = tug * 30.0
    hx, hy, _, _ = cp.render_bryan_3d(
        canvas, rigs, d, CX, GY,
        lz=abs(math.sin(ang * 4)) * 9.0,
        run_frame=f % 6,
        pitch_fwd_deg=36.0,  # Full 360° Area-51 Naruto lean!
        hat_mode="lifted_backup" if hat_lift > 4.0 else "normal",
        hat_lift=hat_lift,
        hat_tilt=16.0 * math.sin(ang * 3),
    )

    # Supersonic Naruto trailing arm-streaks & white Mach wind-lines behind Bryan's shoulders!
    dr = ImageDraw.Draw(canvas)
    for ly_arm in (-20.0, 20.0):
        s0x, s0y, _, _ = cp.project_3d(-4.0, ly_arm, 124.0, d)
        s1x, s1y, _, _ = cp.project_3d(-56.0, ly_arm * 1.15, 134.0 + 5.0 * math.sin(ang * 4), d)
        cp.draw_glow_line(dr, (s0x, s0y), (s1x, s1y), (255, 220, 185, 235), (255, 95, 210, 145), 5, 10)
    for wl in range(5):
        wy = GY - 35 - wl * 32
        wx0, _, _, _ = cp.project_3d(-25.0 - (f * 9 + wl * 17) % 45, (wl - 2) * 14.0, 35 + wl * 28, d)
        wx1, _, _, _ = cp.project_3d(-68.0 - (f * 9 + wl * 17) % 45, (wl - 2) * 14.0, 35 + wl * 28, d)
        dr.line([(wx0, wy), (wx1, wy)], fill=(220, 248, 255, 185), width=2)

    # Hovering Chrome Flying Saucer UFO + Neon-Green Tractor Beam Cone overhead!
    ufo_x = CX + math.sin(ang * 2) * 14.0
    ufo_y = 32.0 + 4.0 * math.cos(ang * 2)
    dr.polygon([(ufo_x - 14, ufo_y + 10), (ufo_x + 14, ufo_y + 10), (hx + 28, hy + 28), (hx - 28, hy + 28)],
               fill=(85, 255, 145, int(45 + 65 * tug)))
    for ri in range(3):
        ry_b = ufo_y + 16 + ((ph * 3 + ri / 3.0) % 1.0) * max(12.0, (hy - ufo_y))
        rw_b = 12 + (ry_b - ufo_y) * 0.22
        dr.ellipse([ufo_x - rw_b, ry_b - 3, ufo_x + rw_b, ry_b + 3], outline=(150, 255, 185, 175), width=2)
    cp.paste_rgba_center(canvas, props["ufo"], ufo_x, ufo_y, scale=0.88, rot_deg=5.0 * math.sin(ang * 2))


# ==============================================================================
# SCENE 7: QUADRUPLE BLAZING DRAGON NUNCHUCKS + ACCIDENTAL TINFOIL HAT BONK!
# ==============================================================================
def scene_nunchuck_god(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    cp.draw_shadow(canvas, CX, GY, 29, 7)

    bonk = (16 <= f <= 21)
    hx, hy, _, _ = cp.render_bryan_3d(
        canvas, rigs, d, CX, GY,
        lz=(10.0 if f == 16 else abs(math.sin(ang * 3)) * 6.0) if not bonk else 0.0,
        run_frame=(f // 2) % 6 if not bonk else None,
        roll_deg=(-11.0 if f == 16 else 8.0 * math.sin(ang * 6)) if bonk else 5.0 * math.sin(ang * 3),
        squash_x=1.08 if f == 16 else 1.0,
        stretch_y=0.93 if f == 16 else 1.0,
        hat_mode="bonked" if bonk else "normal",
        hat_lift=14.0 if f == 16 else (6.0 if bonk else 0.0),
        hat_tilt=28.0 if bonk else 0.0,
    )

    dr = ImageDraw.Draw(canvas)
    if not bonk:
        # DUAL MACH-3 FLAMING DRAGON NUNCHUCK HELICOPTER TORUSES on BOTH sides of Bryan in 3D!
        for side_sgn in (-1.0, 1.0):
            hsx, hsy, hdz, hsc = cp.project_3d(24.0, side_sgn * 38.0, 118.0 + 12.0 * math.sin(ang * 2 * side_sgn), d)
            spin = ang * 6.0 * side_sgn + (0.8 if side_sgn > 0 else 0.0)
            rx, ry = int(38 * hsc), int(29 * hsc)
            # Blazing orange/gold 60-FPS motion-smear rings!
            dr.arc([hsx - rx, hsy - ry, hsx + rx, hsy + ry], start=math.degrees(spin), end=math.degrees(spin) + 155,
                   fill=(255, 85, 20, 220), width=10)
            dr.arc([hsx - rx, hsy - ry, hsx + rx, hsy + ry], start=math.degrees(spin) + 180, end=math.degrees(spin) + 335,
                   fill=(255, 215, 55, 240), width=6)
            # Spinning ebony & gold nunchuck sticks + chain!
            for arm_k in (0.0, math.pi * 0.78):
                nx = hsx + math.cos(spin + arm_k) * rx
                ny = hsy + math.sin(spin + arm_k) * ry
                dr.line([(hsx, hsy), (nx, ny)], fill=(35, 26, 20, 255), width=5)
                dr.line([(hsx + (nx - hsx) * 0.55, hsy + (ny - hsy) * 0.55), (nx, ny)], fill=(250, 205, 65, 255), width=3)
                dr.ellipse([nx - 5, ny - 5, nx + 5, ny + 5], fill=(255, 145, 30, 225))
    else:
        # FRAME 16..21: *CLANG!!* NUNCHUCK BONKS HIS SILVER TINFOIL HAT + DIZZY STARS & TINY LAUGHING DEMONS!
        if f <= 17:
            # Giant yellow comic impact starburst right on the tinfoil cone!
            for si in range(12):
                sa = si * (math.pi / 6.0) + f * 0.3
                r_out = 28 if si % 2 == 0 else 13
                dr.line([(hx, hy + 8), (hx + math.cos(sa) * r_out, hy + 8 + math.sin(sa) * r_out)],
                        fill=(255, 240, 65, 255), width=3)
            # Rebounding nunchuck stick flying off his hat!
            dr.line([(hx + 8, hy + 4), (hx + 34, hy - 14)], fill=(245, 195, 55, 255), width=5)
        # Orbiting dizzy yellow stars + tiny red demon heads around Bryan's dented tinfoil hat!
        for st_i in range(4):
            oa = ang * 4.0 + st_i * (math.pi * 0.5)
            ox = hx + math.cos(oa) * 28.0
            oy = hy + 8 + math.sin(oa) * 9.0
            if st_i % 2 == 0:
                dr.polygon([(ox, oy - 6), (ox + 2, oy - 2), (ox + 6, oy), (ox + 2, oy + 2),
                            (ox, oy + 6), (ox - 2, oy + 2), (ox - 6, oy), (ox - 2, oy - 2)],
                           fill=(255, 235, 55, 255), outline=(255, 140, 20, 255))
            else:
                dr.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], fill=(235, 38, 45, 255))
                dr.line([(ox - 4, oy - 7), (ox - 2, oy - 4)], fill=(255, 215, 70, 255), width=2)
                dr.line([(ox + 4, oy - 7), (ox + 2, oy - 4)], fill=(255, 215, 70, 255), width=2)


# ==============================================================================
# SCENE 8: MALL-NINJA DUAL KATANA ANIME 'JUDGMENT CUT' ('NOTHING PERSONNEL')
# ==============================================================================
def scene_katana_anime(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    rng = random.Random(8800 + d * 37 + f * 19)

    # Crimson Demon target getting sliced in background/side orbit!
    dsx, dsy, ddz, dsc = cp.project_3d(-44.0, -48.0, 92.0, d)
    dsx = float(np.clip(dsx, 46, FW - 46))

    def draw_sliced_demon():
        c_im, _ = rigs["crimson"][(d + 4) % 8]
        # On frames 15..22, top half of demon slides sideways slightly from anime katana Judgment Cut!
        if 15 <= f <= 22:
            w, h = c_im.size
            top_h = c_im.crop((0, 0, w, h // 2))
            bot_h = c_im.crop((0, h // 2, w, h))
            cp.paste_rgba_center(canvas, bot_h, dsx, dsy + h * 0.16 * dsc, scale=0.66 * dsc)
            cp.paste_rgba_center(canvas, top_h, dsx + 9, dsy - h * 0.16 * dsc - 3, scale=0.66 * dsc)
            dr = ImageDraw.Draw(canvas)
            cp.draw_glow_line(dr, (dsx - 36, dsy), (dsx + 42, dsy - 4), (255, 255, 255, 255), (90, 235, 255, 220), 2, 7)
        else:
            cp.paste_rgba_center(canvas, c_im, dsx, dsy, scale=0.66 * dsc)

    def draw_bryan_katana():
        if 5 <= f <= 14:
            # High-speed anime flash-step teleport dash across 3 positions!
            dash_x = CX + math.sin((f - 5) * 1.4) * 48.0
            dash_z = 16.0 + abs(math.cos((f - 5) * 1.1)) * 22.0
            cp.render_bryan_3d(canvas, rigs, (d + f) % 8, CX - (dash_x - CX) * 0.5, GY, lz=8.0,
                               run_frame=f % 6, pitch_fwd_deg=26.0, alpha_mul=0.38, tint=(0.6, 0.9, 1.8))
            cp.render_bryan_3d(canvas, rigs, (d + f * 2) % 8, dash_x, GY, lz=dash_z,
                               run_frame=f % 6, pitch_fwd_deg=28.0)
            # Twin Katanas slashing wildly!
            cp.paste_rgba_center(canvas, props["katana"], dash_x - 26, GY - 115 - dash_z, scale=0.88, rot_deg=f * 68.0)
            cp.paste_rgba_center(canvas, props["katana"], dash_x + 26, GY - 115 - dash_z, scale=0.88, rot_deg=-f * 68.0 + 45.0)
        else:
            # Cool crouch-unsheathe (0..4) or dramatic post-slash sheath click (15..23)!
            cp.draw_shadow(canvas, CX, GY, 29, 7)
            cp.render_bryan_3d(canvas, rigs, d, CX, GY, squash_x=1.03, stretch_y=0.95 if f < 5 else 1.0, deal_shades=(f >= 15))
            ksx1, ksy1, _, ksc1 = cp.project_3d(24.0, -28.0, 128.0, d)
            ksx2, ksy2, _, ksc2 = cp.project_3d(24.0, 28.0, 128.0, d)
            ang_k = -55.0 if f < 5 else 32.0
            cp.paste_rgba_center(canvas, props["katana"], ksx1, ksy1, scale=0.85 * ksc1, rot_deg=ang_k)
            cp.paste_rgba_center(canvas, props["katana"], ksx2, ksy2, scale=0.85 * ksc2, rot_deg=-ang_k)
            if f in (3, 16, 17):
                # Blinding anime 'SHING!!' hilt star glint!
                dr = ImageDraw.Draw(canvas)
                cp.draw_glow_line(dr, (ksx1 - 24, ksy1 + 18), (ksx1 + 24, ksy1 + 18), (255, 255, 255, 255), (90, 235, 255, 220), 2, 6)
                cp.draw_glow_line(dr, (ksx1, ksy1 - 6), (ksx1, ksy1 + 42), (255, 255, 255, 255), (90, 235, 255, 220), 2, 6)

    for _, fn in sorted([(ddz, draw_sliced_demon), (0.0, draw_bryan_katana)], key=lambda x: -x[0]):
        fn()

    # 360° Outer-Ring Web of Glowing Anime 'Judgment Cut' Slashes + Swirling Pink Sakura Petals!
    dr = ImageDraw.Draw(canvas)
    if 6 <= f <= 20:
        num_cuts = 14 if (14 <= f <= 18) else 8
        for ci in range(num_cuts):
            ca = (ci / float(num_cuts)) * 2.0 * math.pi + ph * 3.0
            rad_c = rng.randint(44, 88)
            x0 = CX + math.cos(ca) * rad_c
            y0 = GY - 102 + math.sin(ca) * (rad_c * 0.78)
            ang_c = ca + math.pi * 0.5 + rng.uniform(-0.35, 0.35)
            ln = rng.randint(36, 68)
            dx_c, dy_c = math.cos(ang_c) * ln, math.sin(ang_c) * ln
            col_g = (95, 225, 255, 180) if ci % 2 == 0 else (255, 105, 220, 170)
            cp.draw_glow_line(dr, (x0 - dx_c, y0 - dy_c), (x0 + dx_c, y0 + dy_c), (255, 255, 255, 240), col_g, 1, 5)
    # Floating pink sakura cherry-blossom petals across all 24 frames!
    for pi in range(12):
        px = (CX - 115 + (pi * 37 + f * 11) % 230)
        py = (24 + (pi * 43 + f * 9) % (GY - 24))
        dr.ellipse([px - 3, py - 2, px + 3, py + 2], fill=(255, 165, 205, 225))


# ==============================================================================
# SCENE 9: COSMIC RUNE-GREATSWORD & DUAL-LIGHTSABER WHIRLWIND TORNADO
# ==============================================================================
def scene_lightsaber_paladin(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    # Bryan leaps up and spins 360° through all 8 directions mid-whirlwind!
    b_dir = (d + (f // 3)) % 8
    leap_z = math.sin(ph * math.pi) * 26.0
    cp.draw_shadow(canvas, CX, GY, int(30 - leap_z * 0.25), 7)

    # Scorched glowing plasma ring carved onto the dungeon floor!
    dr_bg = ImageDraw.Draw(canvas)
    dr_bg.ellipse([CX - 86, GY - 18, CX + 86, GY + 18], outline=(35, 195, 255, 185), width=4)
    dr_bg.ellipse([CX - 72, GY - 14, CX + 72, GY + 14], outline=(255, 55, 95, 185), width=3)

    # Weapon 1 (Right hand): Blazing Blue Rune Greatsword orbiting at +ang
    gx, gy_w, gdz, gsc = cp.project_3d(52.0, -34.0, 122.0 + leap_z, b_dir)
    # Weapon 2 (Left hand): Twirling Double-Bladed Crimson/Emerald Lightsaber orbiting opposite!
    lx_w, ly_w, ldz, lsc = cp.project_3d(52.0, 34.0, 118.0 + leap_z, b_dir)

    def draw_greatsword():
        cp.paste_rgba_center(canvas, props["greatsword"], np.clip(gx, 38, FW - 38), np.clip(gy_w, 46, GY - 20),
                             scale=0.86 * gsc, rot_deg=f * 30.0 - 45.0)

    def draw_saber():
        cp.paste_rgba_center(canvas, props["lightsaber"], np.clip(lx_w, 38, FW - 38), np.clip(ly_w, 48, GY - 20),
                             scale=0.88 * lsc, rot_deg=-f * 45.0)

    def draw_bryan():
        cp.render_bryan_3d(canvas, rigs, b_dir, CX, GY, lz=leap_z, run_frame=f % 6, pitch_fwd_deg=10.0)

    for _, fn in sorted([(gdz, draw_greatsword), (ldz, draw_saber), (0.0, draw_bryan)], key=lambda x: -x[0]):
        fn()

    # Sweeping 360° dual-color plasma slash ribbons & deflected red blaster bolts!
    dr = ImageDraw.Draw(canvas)
    deg = f * 15.0 + d * 45.0
    dr.arc([CX - 94, GY - 156 - int(leap_z), CX + 94, GY - 64 - int(leap_z)],
           start=deg, end=deg + 115, fill=(65, 215, 255, 195), width=7)
    dr.arc([CX - 88, GY - 148 - int(leap_z), CX + 88, GY - 72 - int(leap_z)],
           start=deg + 180, end=deg + 295, fill=(255, 55, 95, 195), width=7)


# ==============================================================================
# SCENE 10: D&D DUNGEON MASTER CRITICAL NAT-20 FIREBALL ROLL
# ==============================================================================
def scene_dnd_nat20(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    cp.draw_shadow(canvas, CX, GY, 28, 7)

    # Golden Arcane Runic Circle on the floor around Bryan!
    dr0 = ImageDraw.Draw(canvas)
    dr0.ellipse([CX - 82, GY - 17, CX + 82, GY + 17], outline=(195, 95, 255, 185), width=3)
    dr0.ellipse([CX - 66, GY - 13, CX + 66, GY + 13], outline=(255, 215, 65, 195), width=2)

    # Floating Wooden DM Screen in front-left + Giant Tumbling Ruby D20!
    msx, msy, mdz, msc = cp.project_3d(38.0, 42.0, 74.0 + 4.0 * math.sin(ang * 2), d)
    is_crit = (f >= 15)
    roll_t = min(1.0, max(0.0, (f - 4) / 11.0))
    bounce_d20 = abs(math.sin(roll_t * 3.0 * math.pi)) * (1.0 - roll_t) * 58.0 if f >= 4 else 68.0
    d20_lx = 22.0 + roll_t * 52.0 if f >= 4 else 22.0
    dsx, dsy, ddz, dsc = cp.project_3d(d20_lx, -18.0, 22.0 + bounce_d20, d)
    dsx = float(np.clip(dsx, 42, FW - 42))

    # Roasted Grey Ram-Horned Demon getting blasted by the Nat-20 Fireball on frames 15..23!
    gsx, gsy, gdz, gsc = cp.project_3d(74.0, -24.0, 88.0, d)
    gsx = float(np.clip(gsx, 46, FW - 46))

    def draw_dm():
        cp.paste_rgba_center(canvas, props["dm_screen"], np.clip(msx, 46, FW - 46), msy, scale=0.82 * msc)

    def draw_d20_and_fireball():
        die_im = props["d20_crit"] if is_crit else props["d20"]
        rot = 0.0 if is_crit else f * 48.0
        sc_d = (1.18 if is_crit else 0.90) * dsc
        cp.paste_rgba_center(canvas, die_im, dsx, dsy, scale=sc_d, rot_deg=rot)
        if is_crit:
            # MASSIVE CRITICAL NAT-20 GOLDEN/MAGENTA FIREBALL ERUPTION + ROASTED DEMON!
            prog = (f - 15) / 8.0
            ram_im, _ = rigs["ram"]
            cp.paste_rgba_center(canvas, ram_im, gsx, gsy - prog * 18.0, scale=0.58 * gsc, rot_deg=prog * 22.0)
            fd = ImageDraw.Draw(canvas)
            fh = int(55 + 115 * math.sin(prog * math.pi * 0.85))
            for k in range(14):
                ky = dsy - (k / 13.0) * fh
                kr = int((26 - k * 1.3) * (0.8 + 0.4 * math.sin(f + k)))
                col = (255, int(75 + k * 12), 35, 185) if k % 2 == 0 else (255, 235, 95, 205)
                fd.ellipse([dsx - kr, ky - kr // 2, dsx + kr, ky + kr // 2], fill=col)

    def draw_bryan_wizard():
        cp.render_bryan_3d(
            canvas, rigs, d, CX, GY,
            lz=(12.0 * abs(math.sin(ang * 4))) if is_crit else 3.0 * abs(math.sin(ang * 2)),
            hat_mode="wizard",
            roll_deg=6.0 * math.sin(ang * 3) if is_crit else 0.0,
        )

    for _, fn in sorted([(mdz, draw_dm), (ddz, draw_d20_and_fireball), (0.0, draw_bryan_wizard)], key=lambda x: -x[0]):
        fn()


# ==============================================================================
# SCENE 11: OVER-9000 SUPER-TINFOIL SAIYAN & 3D KAMEHAMEHA BLAST
# ==============================================================================
def scene_super_saiyan(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi
    firing = (f >= 11)
    rng = random.Random(9001 + d * 41 + f * 23)

    # Cracked golden energy crater on floor
    dr0 = ImageDraw.Draw(canvas)
    dr0.ellipse([CX - 68, GY - 14, CX + 68, GY + 14], fill=(255, 195, 35, 90), outline=(255, 240, 120, 220), width=2)

    # Roaring Multi-Layered Golden DBZ Ki Flame Aura behind Bryan!
    for ai in range(14):
        ay = GY - 12 - (ai / 13.0) * 195.0
        aw = 48.0 * (1.0 - (ai / 16.0) ** 1.4) + rng.uniform(-5, 5)
        col_a = (255, 205, 35, 115) if ai % 2 == 0 else (255, 248, 155, 135)
        dr0.polygon([(CX - aw, ay + 18), (CX + rng.uniform(-8, 8), ay - 22), (CX + aw, ay + 18)], fill=col_a)

    # 5 Levitating 3D Rocks rising around Bryan!
    rock_items = []
    for ri in range(5):
        ra = ang + ri * (2 * math.pi / 5)
        rsx, rsy, rdz, rsc = cp.project_3d(math.cos(ra) * 68.0, math.sin(ra) * 74.0, 26.0 + ((f * 5 + ri * 22) % 115), d)

        def draw_rock(x=rsx, y=rsy, s=rsc):
            rd = ImageDraw.Draw(canvas)
            r = max(4, int(7 * s))
            rd.polygon([(x - r, y), (x - r // 2, y - r), (x + r, y - r // 2), (x + r // 2, y + r)],
                       fill=(128, 112, 96, 255), outline=(255, 225, 95, 210))

        rock_items.append((rdz, draw_rock))

    # 3D KAMEHAMEHA BEAM shooting straight out along Bryan's +lx facing vector!
    hsx, hsy, hdz, _ = cp.project_3d(26.0, 0.0, 116.0, d)
    esx, esy, edz, esc = cp.project_3d(185.0, 0.0, 116.0, d)

    def draw_kamehameha():
        dr = ImageDraw.Draw(canvas)
        if not firing:
            # Charging pulsing cyan-white Ki star cupped between Bryan's hands!
            rad = int(8 + (f / 10.0) * 14)
            dr.ellipse([hsx - rad - 5, hsy - rad - 5, hsx + rad + 5, hsy + rad + 5], fill=(45, 205, 255, 165))
            dr.ellipse([hsx - rad, hsy - rad, hsx + rad, hsy + rad], fill=(255, 255, 255, 255))
        else:
            # MASSIVE 3D KAMEHAMEHA PLASMA BEAM + HELICAL ENERGY RINGS!
            if d in (0, 4):
                # Foreshortened straight toward camera (d=0) or away into distance (d=4), keeping Bryan's face & scouter clear!
                by_f = hsy + (16 if d == 0 else 0)
                r_big = int(24 + 5 * math.sin(ang * 6)) if d == 0 else int(22 + 4 * math.sin(ang * 6))
                for ray_i in range(10):
                    ra_r = ray_i * (math.pi / 5.0) + ang * 4.0
                    dr.line([(hsx, by_f), (hsx + math.cos(ra_r) * (r_big + 24), by_f + math.sin(ra_r) * (r_big + 18))],
                            fill=(85, 235, 255, 215), width=3)
                dr.ellipse([hsx - r_big - 8, by_f - r_big - 8, hsx + r_big + 8, by_f + r_big + 8], fill=(35, 185, 255, 175))
                dr.ellipse([hsx - r_big, by_f - r_big, hsx + r_big, by_f + r_big], fill=(235, 252, 255, 255), outline=(85, 235, 255, 255), width=3)
            else:
                cp.draw_glow_line(dr, (hsx, hsy), (esx, esy), (255, 255, 255, 255), (38, 195, 255, 205), 14, 32)
                for sp_i in range(6):
                    u = sp_i / 5.0
                    bx = hsx + (esx - hsx) * u
                    by = hsy + (esy - hsy) * u
                    dr.ellipse([bx - 10, by - 18, bx + 10, by + 18], outline=(195, 250, 255, 230), width=2)
                dr.ellipse([hsx - 18, hsy - 18, hsx + 18, hsy + 18], fill=(255, 255, 255, 255))

    def draw_bryan_saiyan():
        cp.render_bryan_3d(
            canvas, rigs, d, CX + rng.randint(-2, 2), GY,
            pitch_fwd_deg=16.0 if firing else -6.0,
            squash_x=1.05 if not firing else 1.0,
            stretch_y=0.96 if not firing else 1.02,
            hat_mode="saiyan",
            scouter=True,
        )
        # Blue bio-electricity arcs crackling across Bryan!
        dr = ImageDraw.Draw(canvas)
        for _ in range(4):
            x0, y0 = CX + rng.randint(-26, 26), GY - rng.randint(35, 175)
            dr.line([(x0, y0), (x0 + rng.randint(-14, 14), y0 + rng.randint(-14, 14)),
                     (x0 + rng.randint(-18, 18), y0 + rng.randint(-22, 22))],
                    fill=(110, 240, 255, 245), width=2)

    beam_z = (hdz + edz) * 0.5
    items = rock_items + [(beam_z, draw_kamehameha), (0.0, draw_bryan_saiyan)]
    for _, fn in sorted(items, key=lambda x: -x[0]):
        fn()


# ==============================================================================
# SCENE 12: MATRIX 62° BULLET-TIME DODGE & CYBER POWER-GLOVE HACK
# ==============================================================================
def scene_matrix_larp(canvas, rigs, props, d, f):
    ph = f / NF
    ang = ph * 2.0 * math.pi

    # Cascading 3D Digital Green Matrix Code Rain columns in background & foreground!
    dr0 = ImageDraw.Draw(canvas)
    for col_i in range(14):
        mx = 22 + col_i * 21
        head_r = (f * 13 + col_i * 47) % (FH - 24)
        for seg in range(7):
            ry = head_r - seg * 11
            if 8 < ry < FH - 12:
                al = 240 if seg == 0 else max(30, 190 - seg * 26)
                col_m = (215, 255, 225, al) if seg == 0 else (35, 235, 85, al)
                dr0.rectangle([mx, ry, mx + 3, ry + 6], fill=col_m)

    cp.draw_shadow(canvas, CX, GY, 32, 7)

    # Smooth 62° BACKWARD Neo Bullet-Time Limbo curve across the 24-frame cycle!
    limbo = math.sin(ph * math.pi) ** 0.85
    back_pitch = -62.0 * limbo

    # 6 Slow-Motion Brass Bullets + Supersonic Ripple Rings spiraling past Bryan in 3D!
    bullet_items = []
    for bi in range(6):
        ba = ang + bi * (2 * math.pi / 6)
        blx = math.cos(ba) * 76.0
        bly = math.sin(ba) * 82.0
        blz = 95.0 + 38.0 * math.sin(ba * 2)
        bsx, bsy, bdz, bsc = cp.project_3d(blx, bly, blz, d)
        vx = -math.sin(ba) * (-math.sin(math.radians(d * 45))) + math.cos(ba) * math.cos(math.radians(d * 45))

        def draw_bullet(x=bsx, y=bsy, s=bsc, go_left=(vx < 0), b_ang=ba):
            dr = ImageDraw.Draw(canvas)
            # 3 translucent supersonic bullet-time air-ripple rings trailing behind bullet!
            dir_s = 1 if go_left else -1
            for rr in range(1, 4):
                rx_r = x + dir_s * rr * 12
                dr.ellipse([rx_r - 4, y - 8 - rr * 2, rx_r + 4, y + 8 + rr * 2],
                           outline=(205, 255, 220, max(45, 195 - rr * 42)), width=2)
            cp.paste_rgba_center(canvas, props["bullet"], x, y, scale=0.95 * s, flip_x=go_left)

        bullet_items.append((bdz, draw_bullet))

    def draw_bryan_neo():
        # Motion-trail bullet-time ghost behind leaning Bryan
        if limbo > 0.25:
            cp.render_bryan_3d(canvas, rigs, d, CX, GY, pitch_fwd_deg=back_pitch * 0.68,
                               alpha_mul=0.34, tint=(0.35, 1.55, 0.65), deal_shades=True)
        cp.render_bryan_3d(canvas, rigs, d, CX, GY, pitch_fwd_deg=back_pitch, deal_shades=True)
        # Windmill Neo arm circles + Neon Green Cyber Power-Glove Holo-Terminal!
        dr = ImageDraw.Draw(canvas)
        gsx, gsy, _, gsc = cp.project_3d(26.0, 28.0, 118.0 - 25.0 * limbo, d)
        dr.rectangle([gsx - 16, gsy - 12, gsx + 16, gsy + 12],
                     fill=(18, 65, 32, 165), outline=(65, 255, 120, 240), width=2)
        dr.line([(gsx - 11, gsy - 4), (gsx + 9, gsy - 4)], fill=(155, 255, 180, 255), width=2)
        dr.line([(gsx - 11, gsy + 2), (gsx + 4, gsy + 2)], fill=(155, 255, 180, 255), width=2)

    items = bullet_items + [(0.0, draw_bryan_neo)]
    for _, fn in sorted(items, key=lambda x: -x[0]):
        fn()


SCENE_FUNCS = {
    "flat_earth": scene_flat_earth,
    "corkboard": scene_corkboard,
    "chemtrails": scene_chemtrails,
    "five_g": scene_five_g,
    "illuminati": scene_illuminati,
    "ufo_naruto": scene_ufo_naruto,
    "nunchuck_god": scene_nunchuck_god,
    "katana_anime": scene_katana_anime,
    "lightsaber_paladin": scene_lightsaber_paladin,
    "dnd_nat20": scene_dnd_nat20,
    "super_saiyan": scene_super_saiyan,
    "matrix_larp": scene_matrix_larp,
}


def render_one_set_worker(anim_id):
    """Worker process: renders all 8 angles x 24 frames (192 frames) for `anim_id`,
    saves its 7680x2304 RGBA WebP atlas, and returns 8 representative thumbnail frames for the showcase poster."""
    t0 = time.time()
    rigs = cp.load_compact_rigs()
    props = build_props_bundle()
    fn = SCENE_FUNCS[anim_id]

    atlas = Image.new("RGBA", (FW * NF, FH * 8), (0, 0, 0, 0))
    rep_row = []

    for d in range(8):
        for f in range(NF):
            canvas = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
            fn(canvas, rigs, props, d, f)
            atlas.paste(canvas, (f * FW, d * FH))
            if f == (16 if anim_id in ("nunchuck_god", "dnd_nat20", "super_saiyan", "katana_anime") else 10):
                rep_row.append(canvas)

    out_webp = os.path.join(ATLAS_DIR, f"{anim_id}.webp")
    atlas.save(out_webp, format="WEBP", quality=84, method=2)
    sz_kb = os.path.getsize(out_webp) / 1024.0
    # Return PNG bytes for the 8 representative frames so pickling across processes is tiny & instant
    import io
    rep_bytes = []
    for im in rep_row:
        b = io.BytesIO()
        im.save(b, format="PNG")
        rep_bytes.append(b.getvalue())
    return anim_id, sz_kb, time.time() - t0, rep_bytes


def pack_core_atlases():
    """Also packs the 5 core animations (Solo Run, Solo Scan, Demon-Whirl, Demon-Trio Surge, Hell Portal Death, Toned SPR32)
    into matching RGBA WebP atlases so the 60-120 FPS <canvas> player drives all 17 animations uniformly!"""
    core_specs = [
        ("run", 8, 6, lambda d, f: os.path.join(WEB_DIR, f"bryan_run_d{d}_f{f}.png")),
        ("scan", 8, 6, lambda d, f: os.path.join(WEB_DIR, f"bryan_scan_d{d}_f{f}.png")),
        ("whirl", 8, 8, lambda d, f: os.path.join(WEB_DIR, f"bryan_whirl_d{d}_f{f}.png")),
        ("surge", 8, 8, lambda d, f: os.path.join(WEB_DIR, f"bryan_surge_d{d}_f{f}.png")),
        ("spr32", 8, 6, lambda d, f: os.path.join(WEB_DIR, "spr32", f"f_{8 + d * 6 + f:03d}.png")),
    ]
    for cid, nd, nf, path_fn in core_specs:
        atlas = Image.new("RGBA", (FW * nf, FH * nd), (0, 0, 0, 0))
        for d in range(nd):
            for f in range(nf):
                im = Image.open(path_fn(d, f)).convert("RGBA").resize((FW, FH), Image.LANCZOS)
                atlas.paste(im, (f * FW, d * FH))
        atlas.save(os.path.join(ATLAS_DIR, f"{cid}.webp"), format="WEBP", quality=88, method=3)

    # Death: 1 row x 32 frames (or 4 rows x 8 frames) -> 1 row x 32 frames = 10240 x 288 (well under 16383!)
    d_atlas = Image.new("RGBA", (FW * 32, FH), (0, 0, 0, 0))
    for f in range(32):
        im = Image.open(os.path.join(WEB_DIR, f"bryan_death_{f:02d}.png")).convert("RGBA").resize((FW, FH), Image.LANCZOS)
        d_atlas.paste(im, (f * FW, 0))
    d_atlas.save(os.path.join(ATLAS_DIR, "death.webp"), format="WEBP", quality=88, method=3)


def main():
    t_start = time.time()
    print("Packing 5 core animations into fast <canvas> RGBA WebP atlases...")
    pack_core_atlases()

    print(f"Rendering 12 new 360° x 24-frame sets (2,304 frames total) across {min(12, os.cpu_count() or 8)} CPU workers...")
    anim_ids = [s[0] for s in DOZEN_SPECS]
    results = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(12, os.cpu_count() or 8)) as ex:
        futs = {ex.submit(render_one_set_worker, aid): aid for aid in anim_ids}
        for fut in concurrent.futures.as_completed(futs):
            aid, sz_kb, dt, rep_b = fut.result()
            results[aid] = rep_b
            print(f"  [OK] {aid:20s} -> 192 frames | {sz_kb:6.1f} KB WebP atlas | {dt:.1f}s")

    # Build 12-row x 8-angle Master Showcase Poster (bryan_dozen_showcase_sheet.jpg)
    import io
    tw, th = 160, 144
    W_p, H_p = tw * 8, th * 12
    yy, xx = np.mgrid[0:H_p, 0:W_p]
    chk = np.where(((xx // 12 + yy // 12) % 2) == 0, 36, 25)[..., None].astype(np.uint8)
    poster = Image.fromarray(np.repeat(chk, 3, axis=-1), "RGB")

    for r_i, (aid, _, _, _) in enumerate(DOZEN_SPECS):
        for c_i, png_b in enumerate(results[aid]):
            im = Image.open(io.BytesIO(png_b)).convert("RGBA").resize((tw, th), Image.LANCZOS)
            gx, gy_p = c_i * tw, r_i * th
            sub = poster.crop((gx, gy_p, gx + tw, gy_p + th)).convert("RGBA")
            sub.alpha_composite(im)
            poster.paste(sub.convert("RGB"), (gx, gy_p))

    poster_path = os.path.join(WEB_DIR, "bryan_dozen_showcase_sheet.jpg")
    poster.save(poster_path, quality=91)
    print(f"All 12 sets + poster complete in {time.time() - t_start:.1f}s -> {poster_path}")


if __name__ == "__main__":
    main()
