"""Build all 4 Disc Sentry Gun 3D concepts, custom 3D floppy projectiles, gibs,
and procedural textures, and validate every MD3 binary with md3lib.

Usage:
    python source/mm_tools/disc_sentry/build_models.py
"""
from __future__ import annotations

import json
import math
import os
import struct
import sys
from typing import Dict, List, Tuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.abspath(os.path.join(HERE, ".."))
OUT_ROOT = os.path.join(MM_TOOLS, "out", "disc_sentry")
TEX_DIR = os.path.join(OUT_ROOT, "tex")
MODEL_DIR = os.path.join(OUT_ROOT, "models")

if MM_TOOLS not in sys.path:
    sys.path.insert(0, MM_TOOLS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib  # noqa: E402
from geom_core import (  # noqa: E402
    MeshPart,
    build_curved_crt_screen,
    build_floppy_disk_mesh,
    combine_parts_frames,
    rot_y,
    rot_z,
    smootherstep,
    vnorm,
    xform_part_vn,
)
import textures as texgen  # noqa: E402

UV_TOWER_FRONT = texgen.UV_TOWER_FRONT
UV_TOWER_SIDE  = texgen.UV_TOWER_SIDE
UV_CRT_BEZEL   = texgen.UV_CRT_BEZEL
UV_CRT_BACK    = texgen.UV_CRT_BACK
UV_TRIPOD      = texgen.UV_TRIPOD
UV_HAZARD      = texgen.UV_HAZARD
UV_DRUM_MAG    = texgen.UV_DRUM_MAG
UV_BARREL      = texgen.UV_BARREL
UV_SPEAKER     = texgen.UV_SPEAKER
UV_CABLE_DARK  = texgen.UV_CABLE_DARK
UV_CHROME      = texgen.UV_CHROME

UV_SPEAKER_MESH = (0.268, 0.768, 0.482, 0.880)
UV_KEYBOARD_TOP = (0.264, 0.916, 0.490, 0.992)

UV_LED_GRN = (0.06, 0.06, 0.44, 0.44)
UV_LED_AMB = (0.56, 0.06, 0.94, 0.44)
UV_LED_RED = (0.06, 0.56, 0.44, 0.94)
UV_LED_CYN = (0.56, 0.56, 0.94, 0.94)


CONCEPT_SPECS = [
    {
        "id": "retro",
        "num": 1,
        "badge": "CONCEPT 1 · RETRO COMPUTER SENTRY",
        "short": "1 · Retro Sentry",
        "title": "Retro Computer Sentry",
        "subtitle": "TF Level 2 Turret Yoke + Horizontal 486 PC + 15\" Radar CRT",
        "accent": "#38bdf8",
        "floppy_name": "LOL.BAT (Classic Black 3.5\")",
        "fire_cadence": 0.24,
        "burst_count": 2,
        "spread": 0.08,
        "proj_speed": 260.0,
        "laser_pts": [[7.8, 0.0, 52.0]],
        "desc": (
            "Team Fortress Level 2 sentry silhouette built around a horizontal 1990s 486 desktop PC "
            "and 15\" radar CRT monitor on a heavy splayed steel tripod, with twin side-mounted "
            "floppy-ejector autocannon pods and laser targeting eye."
        ),
        "highlights": [
            ("TF Sentry Yoke", "Heavy splayed tripod + steel turret cradle holding horizontal 486 desktop PC"),
            ("Twin Floppy Pods", "Side-mounted gunmetal twin-barrel pods with drum mags & cooling shrouds"),
            ("Radar CRT", "15\" recessed-bezel CRT displaying TF-SENTRY OS radar & target lock"),
            ("Projectile", "Custom 3D 'LOL.BAT' black 3.5\" floppy diskettes"),
        ],
        "chips": [
            "1's TF Level 2 Horizontal Cradle",
            "1's Twin Side Floppy Pods",
            "1's Green Radar CRT",
        ],
    },
    {
        "id": "classic",
        "num": 2,
        "badge": "CONCEPT 2 · CLASSIC RETRO STYLE",
        "short": "2 · Classic Retro",
        "title": "Classic Retro Style",
        "subtitle": "1994 486DX2 Tower, Mechanical Keyboard, Speaker Cannons & 15\" CRT",
        "accent": "#fbbf24",
        "floppy_name": "BOOT_95.DSK (Verbatim Blue 3.5\")",
        "fire_cadence": 0.28,
        "burst_count": 2,
        "spread": 0.06,
        "proj_speed": 245.0,
        "laser_pts": [[9.0, -8.2, 42.2]],
        "desc": (
            "Authentic 1994 computer sentry combining a yellowed-beige 486DX2-66 tower, sloped mechanical "
            "keyboard with 3D keycaps, half-inserted 3.5\" floppy, coiled cords, and big 15\" curved CRT "
            "flanked by twin beige multimedia speaker-cannons & a stacked floppy magazine!"
        ),
        "highlights": [
            ("1994 PC Authenticity", "486DX2-66 beige tower + 3D mechanical keyboard + half-inserted 3.5\" floppy"),
            ("Speaker Cannons", "Flush beige multimedia speakers with perforated grilles & brushed-steel twin barrels"),
            ("15\" Curved CRT", "True recessed 3D bezel + rabbit-ear antennas + Messenger Service screen"),
            ("Projectile", "Translucent cobalt-blue 'BOOT_95.DSK' Verbatim 3.5\" floppy disks"),
        ],
        "chips": [
            "2's Authentic 1994 AT Tower & Keyboard",
            "2's Flush Speaker-Grille Cannons",
            "2's Rabbit-Ear CRT & Floppy Rack",
        ],
    },
    {
        "id": "badass",
        "num": 3,
        "badge": "CONCEPT 3 · BADASS WEAPON DESIGN",
        "short": "3 · Badass Weapon",
        "title": "Badass Weapon Design",
        "subtitle": "Armored Gunmetal Gatling Shredder + Roll-Caged Tactical CRT",
        "accent": "#fb7185",
        "floppy_name": "KILL_32.EXE (Armored Crimson 3.5\")",
        "fire_cadence": 0.16,
        "burst_count": 3,
        "spread": 0.11,
        "proj_speed": 310.0,
        "laser_pts": [[9.1, -10.7, 49.8], [9.1, 10.7, 49.8]],
        "desc": (
            "Low-profile automated killing machine retaining retro PC/CRT DNA: matte-black sloped armor hull, "
            "hydraulic 3-claw hazard tripod, twin 6-barrel spinning Gatling floppy-shredders with giant drum "
            "magazines, and a roll-caged CRT flashing blood-red KILL_32.EXE crosshairs!"
        ),
        "highlights": [
            ("Heavy Armor", "Wide hydraulic 3-claw hazard tripod + sloped matte-black armor turret hull"),
            ("Twin Gatlings", "Dual 6-barrel spinning rotary floppy cannons fed by giant drum magazines"),
            ("Roll-Caged CRT", "Armored visor hood + steel roll-cage + twin crimson laser optics & strobe"),
            ("Projectile", "Armored crimson-stripe 'KILL_32.EXE' combat 3.5\" floppy disks"),
        ],
        "chips": [
            "3's Twin 6-Barrel Gatlings",
            "3's Armored Roll-Cage CRT",
            "3's Hydraulic Claw Tripod",
        ],
    },
    {
        "id": "msdos",
        "num": 4,
        "badge": "CONCEPT 4 · MS-DOS MACHINE GUN",
        "short": "4 · MS-DOS MG",
        "title": "MS-DOS Machine Gun",
        "subtitle": "MS-DOS 6.22 CRT + Quad Perforated MG Barrels + Open Floppy Hopper",
        "accent": "#34d399",
        "floppy_name": "MS-DOS 6.22 (Cream/Red Disk #1)",
        "fire_cadence": 0.085,
        "burst_count": 4,
        "spread": 0.24,
        "proj_speed": 295.0,
        "laser_pts": [[9.5, -9.4, 56.2]],
        "desc": (
            "Unhinged MS-DOS 6.22 machine-gun war rig! Displays bright MS-DOS prompts (FORMAT C: /AUTOTARGET) "
            "on its oversized CRT while twin quad-barrel perforated machine guns and an open top-rear rotary "
            "hopper packed with stacked 3.5\" disks spray floppies everywhere!"
        ),
        "highlights": [
            ("MS-DOS 6.22 CRT", "Oversized bright blue/white DOS terminal blasting C:\\> FIRE_EVERYWHERE.BAT"),
            ("Quad Machine Guns", "Perforated cylindrical steel cooling shrouds, quad barrels & flared spitter chutes"),
            ("Open Floppy Hopper", "Top-rear angled ammo hopper visibly crammed with stacked 3.5\" MS-DOS disks"),
            ("Chaotic Storm", "Ultra-high-ROF projectile spray sending floppy disks flying in every direction!"),
        ],
        "chips": [
            "4's MS-DOS 6.22 CRT Screen",
            "4's Quad Perforated MG Barrels",
            "4's Open Stacked Floppy Hopper",
        ],
    },
]


def _add_recessed_crt_housing(
    crt: MeshPart,
    x_back_bezel: float,
    x_front_bezel: float,
    y_half: float,
    z_bot: float,
    z_top: float,
    rear_x: float,
    rear_y: float,
    rear_z0: float,
    rear_z1: float,
    rim_y: float = 1.65,
    rim_z_bot: float = 2.6,
    rim_z_top: float = 1.65,
    uv_trim: Tuple[float, float, float, float] = UV_CRT_BEZEL,
    uv_side: Tuple[float, float, float, float] = UV_TOWER_SIDE,
    uv_back: Tuple[float, float, float, float] = UV_CRT_BACK,
) -> MeshPart:
    """Build a true 3D recessed CRT housing (4-bar front bezel frame + dark inner cavity + tapered rear)
    and return a perfectly fitted curved CRT screen inside the recess with zero Z-fighting!
    """
    # Rear dark backing cavity behind screen glass
    x_cavity = x_front_bezel - 1.15
    crt.add_box(x_back_bezel, x_cavity, -y_half, +y_half, z_bot, z_top, uv_side, uv_px=UV_CABLE_DARK, uv_nx=uv_back)

    # 4-piece 3D front bezel frame surrounding the recessed CRT screen opening!
    # Bottom chin (with dials/badge texture!)
    crt.add_box(x_cavity, x_front_bezel, -y_half, +y_half, z_bot, z_bot + rim_z_bot, uv_side, uv_px=uv_trim)
    # Top brow
    crt.add_box(x_cavity, x_front_bezel, -y_half, +y_half, z_top - rim_z_top, z_top, uv_side, uv_px=uv_side)
    # Left & Right vertical bezel pillars
    crt.add_box(x_cavity, x_front_bezel, +y_half - rim_y, +y_half, z_bot + rim_z_bot, z_top - rim_z_top, uv_side)
    crt.add_box(x_cavity, x_front_bezel, -y_half, -y_half + rim_y, z_bot + rim_z_bot, z_top - rim_z_top, uv_side)

    # Tapered deep CRT rear shell behind x_back_bezel
    crt.add_frustum(
        [(x_back_bezel, -y_half + 0.2, z_bot + 0.2), (x_back_bezel, +y_half - 0.2, z_bot + 0.2),
         (x_back_bezel, +y_half - 0.2, z_top - 0.2), (x_back_bezel, -y_half + 0.2, z_top - 0.2)],
        [(rear_x, -rear_y, rear_z0), (rear_x, +rear_y, rear_z0),
         (rear_x, +rear_y, rear_z1), (rear_x, -rear_y, rear_z1)],
        uv_side,
        uv_top=uv_back,
    )
    # Rear CRT tube cap with property/caution sticker
    crt.add_quad(
        (rear_x, +rear_y, rear_z1), (rear_x, +rear_y, rear_z0),
        (rear_x, -rear_y, rear_z0), (rear_x, -rear_y, rear_z1),
        (uv_back[0], uv_back[1]), (uv_back[0], uv_back[3]),
        (uv_back[2], uv_back[3]), (uv_back[2], uv_back[1]),
        nrm=(-1.0, 0.0, 0.0),
    )

    return build_curved_crt_screen(
        x_front=x_cavity + 0.18,
        y_half=y_half - rim_y + 0.08,
        z_bot=z_bot + rim_z_bot - 0.08,
        z_top=z_top - rim_z_top + 0.08,
        bulge=0.55,
    )


def _add_muzzle_flash_cone(m: MeshPart, pos: Tuple[float, float, float], r: float, length: float, uv) -> None:
    """Crisp 4-fin star-burst muzzle flash (no bulky solid traffic cone)."""
    x0, y0, z0 = pos
    for dy, dz in ((r, 0.0), (0.0, r), (r * 0.7, r * 0.7), (r * 0.7, -r * 0.7)):
        p_a = (x0, y0 - dy, z0 - dz)
        p_b = (x0, y0 + dy, z0 + dz)
        p_t = (x0 + length, y0, z0)
        p_c = (x0 + length * 0.25, y0, z0)
        m.add_quad(p_a, p_c, p_b, p_t, (uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3]))
        m.add_quad(p_b, p_c, p_a, p_t, (uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3]))


def _build_tripod_parts(concept_id: str):
    hub = MeshPart("hub")
    if concept_id == "badass":
        hub.add_cylinder((0, 0, 10.5), (0, 0, 19.5), 8.2, 6.8, UV_TRIPOD, segs=12)
        hub.add_cylinder((0, 0, 16.5), (0, 0, 19.0), 9.0, 9.0, UV_HAZARD, segs=12)
        hub.add_cylinder((0, 0, 19.5), (0, 0, 21.0), 5.6, 5.6, UV_CHROME, segs=12)
    elif concept_id == "classic":
        # Authentic steel pedestal cart base with lower surge-strip shelf
        hub.add_cylinder((0, 0, 9.5), (0, 0, 18.8), 5.8, 5.2, UV_TRIPOD, segs=12)
        hub.add_box(-6.8, 6.8, -6.8, 6.8, 10.5, 12.2, UV_TRIPOD)
        # Surge strip sitting on shelf
        hub.add_box(-3.2, 4.8, -5.0, -1.8, 12.2, 13.6, UV_TOWER_SIDE)
        hub.add_cylinder((0, 0, 18.8), (0, 0, 20.4), 4.6, 4.6, UV_CHROME, segs=12)
    elif concept_id == "msdos":
        hub.add_cylinder((0, 0, 10.0), (0, 0, 19.2), 7.4, 6.2, UV_TRIPOD, segs=12)
        hub.add_cylinder((0, 0, 15.0), (0, 0, 17.2), 8.0, 8.0, UV_HAZARD, segs=12)
        hub.add_cylinder((0, 0, 19.2), (0, 0, 20.8), 5.0, 5.0, UV_CHROME, segs=12)
    else:  # retro
        hub.add_cylinder((0, 0, 10.0), (0, 0, 19.0), 6.8, 5.8, UV_TRIPOD, segs=12)
        hub.add_cylinder((0, 0, 17.2), (0, 0, 19.0), 7.4, 7.4, UV_HAZARD, segs=12)
        hub.add_cylinder((0, 0, 19.0), (0, 0, 20.6), 5.0, 5.0, UV_CHROME, segs=12)

    legs = []
    yaws = (52.0, -52.0, 180.0) if concept_id != "badass" else (56.0, -56.0, 180.0)
    reach = 18.2 if concept_id == "badass" else (16.0 if concept_id == "msdos" else 15.2)
    top_z = 16.0 if concept_id != "badass" else 16.8
    for yaw in yaws:
        lp = MeshPart(f"leg_{int(yaw)}")
        w_leg = 1.7 if concept_id == "badass" else 1.25
        lp.add_tube(
            [(3.8, 0.0, top_z), (reach * 0.58, 0.0, top_z * 0.54), (reach - 0.8, 0.0, 1.4)],
            [w_leg * 1.15, w_leg, w_leg * 0.92],
            UV_TRIPOD,
            segs=8,
        )
        lp.add_cylinder((4.8, 0.0, 11.0), (reach * 0.72, 0.0, 4.4), 0.65, 0.55, UV_CHROME, segs=8)
        pad_r = 2.9 if concept_id == "badass" else 2.2
        lp.add_box(reach - pad_r, reach + pad_r, -pad_r, pad_r, 0.0, 1.7, UV_CABLE_DARK)
        if concept_id == "badass":
            lp.add_box(reach + pad_r - 0.6, reach + pad_r + 1.5, -1.1, 1.1, 0.0, 1.4, UV_HAZARD)
        lp_rot = MeshPart(lp.name)
        lp_rot.append(lp, lambda p, y=yaw: rot_z(p, y), lambda n, y=yaw: rot_z(n, y))
        legs.append((lp_rot, yaw, top_z))
    return hub, legs


def build_base_md3(concept_id: str) -> Dict:
    hub, legs = _build_tripod_parts(concept_id)
    nf = 16
    parts_frames = []

    hub_frames = []
    for fi in range(nf):
        if fi <= 11:
            t = smootherstep(fi / 11.0)
            dz = -9.5 * (1.0 - t) + (0.6 if fi == 10 else 0.0)
            sc = 0.25 + 0.75 * t
        else:
            dz = -0.35 * math.sin((fi - 11) * math.pi / 4.0) if fi < 14 else 0.0
            sc = 1.0
        hub_frames.append(xform_part_vn(hub, offset=(0.0, 0.0, dz), pivot=(0.0, 0.0, 0.0), scale=sc))
    parts_frames.append((hub, hub_frames))

    for leg_part, yaw, top_z in legs:
        lframes = []
        for fi in range(nf):
            if fi <= 11:
                t = smootherstep(fi / 11.0)
                fold_ang = -62.0 * (1.0 - t)
                sc = 0.25 + 0.75 * t
                dz = -4.0 * (1.0 - t)
                vv, nn = [], []
                for p, n in zip(leg_part.verts, leg_part.norms):
                    q = (p[0] * sc, p[1] * sc, p[2] * sc)
                    ql = rot_z(q, -yaw)
                    nl = rot_z(n, -yaw)
                    ql = rot_y((ql[0], ql[1], ql[2] - top_z * sc), fold_ang)
                    ql = (ql[0], ql[1], ql[2] + top_z * sc + dz)
                    nl = rot_y(nl, fold_ang)
                    vv.append(rot_z(ql, yaw))
                    nn.append(vnorm(rot_z(nl, yaw)))
                lframes.append((vv, nn))
            else:
                lframes.append((list(leg_part.verts), list(leg_part.norms)))
        parts_frames.append((leg_part, lframes))

    merged_body, frames_body = combine_parts_frames(parts_frames)
    surf = dict(
        name="base_body",
        shader=f"progs/ds_{concept_id}_body",
        tris=merged_body.tris,
        st=merged_body.st,
        frames=frames_body,
    )
    return dict(
        name=f"ds_{concept_id}_base",
        surfaces=[surf],
        nframes=nf,
        frame_names=[f"deploy_{i:02d}" if i < 12 else f"idle_{i:02d}" for i in range(nf)],
    )


def _build_turret_geometry(concept_id: str) -> Dict:
    tower = MeshPart("tower")
    crt_case = MeshPart("crt_case")
    gun_left = MeshPart("gun_left")
    gun_right = MeshPart("gun_right")
    rotor_left = MeshPart("rotor_left")
    rotor_right = MeshPart("rotor_right")
    extra_anim = MeshPart("extra_anim")
    leds_static = MeshPart("leds_static")
    muzzle_l = MeshPart("muzzle_l")
    muzzle_r = MeshPart("muzzle_r")

    # ---- CONCEPT 1: RETRO COMPUTER SENTRY (TF Horizontal Cradle + Desktop 486 + 15" CRT) ----
    if concept_id == "retro":
        # Swivel steel yoke base (z=19..22)
        tower.add_cylinder((0, 0, 19.0), (0, 0, 21.8), 6.6, 7.6, UV_TRIPOD, segs=12)
        # Wide horizontal 486 Beige Pizza-Box Desktop PC sitting inside steel turret cradle (z: 21.8..31.5)
        tower.add_box(-10.5, +8.5, -10.8, +10.8, 21.4, 23.0, UV_TRIPOD)
        tower.add_box(-9.8, +8.2, -10.4, +10.4, 23.0, 32.0, UV_TOWER_SIDE, uv_px=UV_TOWER_FRONT)
        tower.add_box(+8.2, +9.0, -10.6, +10.6, 22.9, 32.1, UV_TOWER_SIDE, uv_px=UV_TOWER_FRONT)
        # Rear PSU fan + coiled cables
        tower.add_cylinder((-9.8, 0.0, 27.5), (-11.0, 0.0, 27.5), 3.4, 3.2, UV_DRUM_MAG, segs=10)
        tower.add_tube([(-9.8, -4.5, 29.0), (-12.5, -5.0, 24.5), (-9.5, -4.2, 20.0)], [0.44] * 3, UV_CABLE_DARK, segs=6)

        # 15" Recessed-Bezel CRT Monitor perched on swivel ring (z: 32.2..50.6)
        crt_case.add_cylinder((-0.5, 0.0, 31.8), (-0.5, 0.0, 34.2), 5.0, 5.6, UV_CRT_BACK, segs=12)
        screen = _add_recessed_crt_housing(
            crt_case,
            x_back_bezel=+4.0, x_front_bezel=+8.6,
            y_half=9.8, z_bot=33.8, z_top=50.6,
            rear_x=-10.2, rear_y=5.4, rear_z0=36.8, rear_z1=47.2,
        )
        # Top TF laser sight pod & whip antenna
        crt_case.add_box(-1.8, +7.6, -2.5, +2.5, 50.6, 53.4, UV_HAZARD)
        extra_anim.add_cylinder((0.0, +4.8, 50.6), (+0.8, +6.2, 59.0), 0.36, 0.16, UV_CHROME, segs=6)
        extra_anim.add_sphere((+0.8, +6.2, 59.2), 0.65, UV_CHROME, stacks=6, slices=8)

        # Twin side-mounted TF Floppy-Cannon Pods bolted directly to horizontal PC flanks (y: ±13.6, z: 24..31)
        for gp, sy in ((gun_left, +1.0), (gun_right, -1.0)):
            yc = sy * 13.8
            tower.add_box(-4.0, +4.0, sy * 10.4, sy * 12.2, 25.5, 30.2, UV_TRIPOD)
            gp.add_box(-7.5, +9.6, yc - 2.6, yc + 2.6, 24.2, 31.4, UV_TRIPOD, uv_pz=UV_HAZARD)
            gp.add_cylinder((+9.2, yc, 29.4), (+21.2, yc, 29.4), 1.45, 1.30, UV_BARREL, segs=12)
            gp.add_cylinder((+9.2, yc, 26.2), (+21.2, yc, 26.2), 1.45, 1.30, UV_BARREL, segs=12)
            gp.add_box(+10.2, +17.2, yc - 1.7, yc + 1.7, 25.2, 30.4, UV_BARREL)
            gp.add_cylinder((-2.5, yc + sy * 2.6, 27.8), (-2.5, yc + sy * 5.0, 27.8), 3.7, 3.5, UV_DRUM_MAG, segs=12)

        rotor_left.add_cylinder((+10.5, +13.8, 27.8), (+11.2, +13.8, 27.8), 1.8, 1.8, UV_CHROME, segs=8)
        rotor_right.add_cylinder((+10.5, -13.8, 27.8), (+11.2, -13.8, 27.8), 1.8, 1.8, UV_CHROME, segs=8)

        leds_static.add_box(+8.95, +9.15, +7.2, +7.9, 23.6, 24.3, UV_LED_GRN)
        leds_static.add_box(+8.95, +9.15, +5.8, +6.5, 23.6, 24.3, UV_LED_AMB)
        leds_static.add_sphere((+7.7, 0.0, 52.0), 0.90, UV_LED_RED, stacks=6, slices=8)
        _add_muzzle_flash_cone(muzzle_l, (+21.4, +13.8, 27.8), 1.6, 4.6, UV_LED_CYN)
        _add_muzzle_flash_cone(muzzle_r, (+21.4, -13.8, 27.8), 1.6, 4.6, UV_LED_CYN)
        crt_piv = (0.0, 0.0, 32.5)
        muzzle_pts = [(+21.4, +13.8, 27.8), (+21.4, -13.8, 27.8)]
        yc_l, zc_gun = 13.8, 27.8

    # ---- CONCEPT 2: CLASSIC RETRO STYLE (Authentic 1994 PC Tower + Keyboard + Flush Speaker Cannons + 15" CRT) ----
    elif concept_id == "classic":
        # Swivel base collar
        tower.add_cylinder((0, 0, 18.8), (0, 0, 21.4), 5.8, 6.8, UV_TRIPOD, segs=12)
        # Authentic 1994 Yellowed-Beige Mini-Tower / Desktop Workstation Core (z: 21.4..38.8)
        tower.add_box(-9.8, +8.4, -8.8, +8.8, 21.4, 38.8, UV_TOWER_SIDE, uv_px=UV_TOWER_FRONT)
        tower.add_box(+8.4, +9.2, -9.0, +9.0, 21.3, 38.9, UV_TOWER_SIDE, uv_px=UV_TOWER_FRONT)

        # Cantilevered Front Keyboard Shelf + Sloped 1990s Mechanical Keyboard + 3D Keycap Banks!
        tower.add_box(+5.0, +15.2, -9.8, +9.8, 20.6, 21.8, UV_TRIPOD)
        tower.add_frustum(
            [(+6.2, -9.2, 21.8), (+14.6, -9.2, 21.8), (+14.6, +9.2, 21.8), (+6.2, +9.2, 21.8)],
            [(+6.5, -8.8, 23.6), (+14.2, -8.8, 22.5), (+14.2, +8.8, 22.5), (+6.5, +8.8, 23.6)],
            UV_TOWER_SIDE, uv_top=UV_KEYBOARD_TOP,
        )

        # Half-inserted 3.5" Floppy Disk (actual beveled disk mesh!) + side stacked floppy magazine rack!
        slot_disk_raw = build_floppy_disk_mesh(half_w=2.1, half_h=2.3, half_t=0.18)
        extra_anim.append(
            slot_disk_raw,
            lambda p: (rot_y(p, -90.0)[0] + 10.6, rot_y(p, -90.0)[1] - 3.6, rot_y(p, -90.0)[2] + 30.2),
            lambda n: rot_y(n, -90.0),
        )
        tower.add_box(-3.8, +3.8, +8.8, +11.4, 22.5, 36.8, UV_DRUM_MAG)  # stacked floppy magazine rack
        # Rear coiled PS/2 + BNC + VGA cables
        tower.add_tube([(-9.6, -5.2, 34.0), (-12.8, -6.5, 27.5), (-9.4, -5.0, 19.5)], [0.44] * 3, UV_CABLE_DARK, segs=6)
        tower.add_tube([(-9.4, +4.2, 36.0), (-12.5, +5.2, 29.0), (-9.6, +4.2, 22.0)], [0.40] * 3, UV_CABLE_DARK, segs=6)

        # Authentic 15" Rounded-Back 1994 Beige CRT Monitor with True 3D Recessed Bezel! (z: 40.6..59.2)
        crt_case.add_cylinder((-0.6, 0.0, 38.8), (-0.6, 0.0, 41.2), 5.0, 5.8, UV_CRT_BACK, segs=12)
        screen = _add_recessed_crt_housing(
            crt_case,
            x_back_bezel=+3.6, x_front_bezel=+9.0,
            y_half=10.4, z_bot=40.8, z_top=59.2,
            rear_x=-11.6, rear_y=5.6, rear_z0=44.2, rear_z1=55.2,
            rim_y=1.7, rim_z_bot=2.8, rim_z_top=1.6,
        )
        # Classic chrome rabbit-ear TV/data antennas atop CRT
        extra_anim.add_box(-1.6, +1.6, -2.6, +2.6, 59.2, 60.2, UV_CABLE_DARK)
        extra_anim.add_cylinder((0.0, +1.8, 60.2), (+1.5, +8.6, 66.8), 0.28, 0.14, UV_CHROME, segs=6)
        extra_anim.add_cylinder((0.0, -1.8, 60.2), (+1.5, -8.6, 66.8), 0.28, 0.14, UV_CHROME, segs=6)

        # Flush-Mounted Retro Beige Multimedia Speaker-Pods retrofitted into Twin Steel Floppy Cannons!
        # Positioned snug against tower flanks (y: ±12.6) with perforated speaker grilles & sleek steel twin barrels
        for gp, sy in ((gun_left, +1.0), (gun_right, -1.0)):
            yc = sy * 12.6
            tower.add_box(-4.2, +4.2, sy * 8.8, sy * 10.6, 26.5, 34.5, UV_TRIPOD)
            # Sculpted beige speaker enclosure with real perforated dark speaker grille on front (+X)
            gp.add_box(-6.0, +6.2, yc - 2.6, yc + 2.6, 24.4, 37.6, UV_TOWER_SIDE, uv_px=UV_SPEAKER_MESH)
            # Twin brushed-steel floppy-launcher barrels + sleek machined chrome/blue muzzle clamp
            gp.add_cylinder((+5.8, yc, 33.6), (+20.2, yc, 33.6), 1.38, 1.24, UV_CHROME, segs=12)
            gp.add_cylinder((+5.8, yc, 28.4), (+20.2, yc, 28.4), 1.38, 1.24, UV_CHROME, segs=12)
            gp.add_box(+16.8, +19.6, yc - 1.85, yc + 1.85, 27.1, 34.9, UV_CHROME, uv_px=UV_CABLE_DARK, uv_pz=UV_HAZARD)

        rotor_left.add_cylinder((+6.6, +12.6, 31.0), (+7.2, +12.6, 31.0), 1.6, 1.6, UV_CHROME, segs=8)
        rotor_right.add_cylinder((+6.6, -12.6, 31.0), (+7.2, -12.6, 31.0), 1.6, 1.6, UV_CHROME, segs=8)

        leds_static.add_box(+9.15, +9.35, +6.8, +7.6, 22.8, 23.6, UV_LED_GRN)   # Power LED
        leds_static.add_box(+9.15, +9.35, -5.6, -4.6, 33.4, 34.1, UV_LED_AMB)  # Floppy activity LED
        leds_static.add_sphere((+8.9, -8.2, 42.2), 0.72, UV_LED_GRN, stacks=6, slices=8)
        _add_muzzle_flash_cone(muzzle_l, (+20.4, +12.6, 31.0), 1.6, 4.6, UV_LED_AMB)
        _add_muzzle_flash_cone(muzzle_r, (+20.4, -12.6, 31.0), 1.6, 4.6, UV_LED_AMB)
        crt_piv = (0.0, 0.0, 39.2)
        muzzle_pts = [(+20.8, +12.6, 31.0), (+20.8, -12.6, 31.0)]
        yc_l, zc_gun = 12.6, 31.0

    # ---- CONCEPT 3: BADASS WEAPON DESIGN (Armored Low-Slung Gatling Shredder + Roll-Caged CRT) ----
    elif concept_id == "badass":
        tower.add_cylinder((0, 0, 19.5), (0, 0, 22.2), 7.8, 8.6, UV_TRIPOD, segs=12)
        # Wide low-profile sloped armored gunmetal PC turret hull (z: 22.0..37.5)
        tower.add_box(-11.4, +9.8, -9.8, +9.8, 22.0, 37.5, UV_TOWER_SIDE, uv_px=UV_TOWER_FRONT)
        tower.add_frustum(
            [(-12.0, -10.6, 22.2), (+10.4, -10.6, 22.2), (+10.4, +10.6, 22.2), (-12.0, +10.6, 22.2)],
            [(-10.2, -9.4, 37.4), (+9.2, -9.4, 37.4), (+9.2, +9.4, 37.4), (-10.2, +9.4, 37.4)],
            UV_TRIPOD,
        )
        # Side weapon gantries + huge rotary drum magazines
        for sy in (-1.0, 1.0):
            y0, y1 = (sy * 9.8, sy * 13.0) if sy > 0 else (sy * 13.0, sy * 9.8)
            tower.add_box(-6.0, +5.8, y0, y1, 25.5, 33.5, UV_HAZARD)
            tower.add_cylinder((-4.0, sy * 15.6, 23.0), (+4.0, sy * 15.6, 23.0), 4.9, 4.9, UV_DRUM_MAG, segs=14)

        # Roll-Caged Armored CRT sunk into top cowling (z: 37.5..54.5)
        screen = _add_recessed_crt_housing(
            crt_case,
            x_back_bezel=+2.8, x_front_bezel=+9.0,
            y_half=10.2, z_bot=37.6, z_top=54.2,
            rear_x=-11.6, rear_y=5.8, rear_z0=40.2, rear_z1=51.0,
        )
        # Heavy hazard visor brow + roll-cage bars + twin laser rangefinders + top strobe
        crt_case.add_box(+2.8, +11.6, -11.0, +11.0, 53.6, 56.0, UV_HAZARD)
        for sy in (-10.8, +10.8):
            crt_case.add_cylinder((+9.8, sy, 37.5), (+9.8, sy, 55.0), 0.78, 0.78, UV_CHROME, segs=8)
        crt_case.add_box(-1.5, +8.8, -11.8, -9.6, 48.0, 51.6, UV_TRIPOD)
        crt_case.add_box(-1.5, +8.8, +9.6, +11.8, 48.0, 51.6, UV_TRIPOD)
        extra_anim.add_cylinder((0.0, 0.0, 56.0), (0.0, 0.0, 58.8), 1.9, 1.4, UV_TRIPOD, segs=10)

        # Twin 6-Barrel Spinning Rotary Gatlings!
        for gp, rp, sy in ((gun_left, rotor_left, +1.0), (gun_right, rotor_right, -1.0)):
            yc = sy * 15.6
            gp.add_box(-8.5, +7.2, yc - 3.6, yc + 3.6, 27.2, 34.8, UV_TRIPOD, uv_pz=UV_HAZARD)
            for bi in range(6):
                ang = 2.0 * math.pi * bi / 6.0
                by = yc + 2.1 * math.cos(ang)
                bz = 31.0 + 2.1 * math.sin(ang)
                rp.add_cylinder((+7.0, by, bz), (+25.8, by, bz), 0.64, 0.56, UV_BARREL, segs=8)
            rp.add_cylinder((+14.5, yc, 31.0), (+15.8, yc, 31.0), 3.15, 3.15, UV_HAZARD, segs=12)
            rp.add_cylinder((+22.6, yc, 31.0), (+24.0, yc, 31.0), 3.15, 3.15, UV_CHROME, segs=12)

        leds_static.add_sphere((+9.0, -10.7, 49.8), 0.95, UV_LED_RED, stacks=6, slices=8)
        leds_static.add_sphere((+9.0, +10.7, 49.8), 0.95, UV_LED_RED, stacks=6, slices=8)
        leds_static.add_sphere((0.0, 0.0, 59.5), 1.4, UV_LED_RED, stacks=6, slices=8)
        _add_muzzle_flash_cone(muzzle_l, (+26.0, +15.6, 31.0), 2.0, 5.4, UV_LED_RED)
        _add_muzzle_flash_cone(muzzle_r, (+26.0, -15.6, 31.0), 2.0, 5.4, UV_LED_RED)
        crt_piv = (0.0, 0.0, 37.5)
        muzzle_pts = [(+26.0, +15.6, 31.0), (+26.0, -15.6, 31.0)]
        yc_l, zc_gun = 15.6, 31.0

    # ---- CONCEPT 4: MS-DOS MACHINE GUN (Oversized MS-DOS CRT + Open Floppy Hopper + Quad MG Barrels) ----
    else:  # msdos
        tower.add_cylinder((0, 0, 19.2), (0, 0, 21.6), 7.0, 7.8, UV_TRIPOD, segs=12)
        tower.add_box(-10.2, +9.0, -9.4, +9.4, 21.6, 37.8, UV_TOWER_SIDE, uv_px=UV_TOWER_FRONT)
        tower.add_box(+9.0, +9.8, -9.6, +9.6, 21.5, 37.9, UV_TOWER_SIDE, uv_px=UV_TOWER_FRONT)
        # Open Top-Rear Rotary Floppy Hopper crammed with stacked visible floppies!
        extra_anim.add_box(-10.2, -1.6, -7.2, +7.2, 37.8, 42.2, UV_HAZARD)
        for fi_d in range(6):
            fx = -9.0 + fi_d * 1.25
            extra_anim.add_box(fx, fx + 0.55, -5.8, +5.8, 39.2, 46.2, UV_DRUM_MAG)

        # Oversized High-Visibility MS-DOS 6.22 CRT Monitor (z: 38.2..58.0)
        screen = _add_recessed_crt_housing(
            crt_case,
            x_back_bezel=+2.6, x_front_bezel=+9.6,
            y_half=10.8, z_bot=38.2, z_top=57.8,
            rear_x=-10.8, rear_y=6.0, rear_z0=41.5, rear_z1=53.8,
            rim_y=1.6, rim_z_bot=2.5, rim_z_top=1.5,
        )

        # Quad-Barrel Heavy Machine Guns inside Perforated Steel Cooling Jackets + Flared Eject Chutes
        for gp, rp, sy in ((gun_left, rotor_left, +1.0), (gun_right, rotor_right, -1.0)):
            yc = sy * 15.0
            tower.add_box(-4.2, +5.2, sy * 9.4, sy * 12.8, 26.2, 33.8, UV_HAZARD)
            gp.add_box(-8.0, +8.2, yc - 3.4, yc + 3.4, 25.8, 34.4, UV_TRIPOD)
            gp.add_cylinder((+8.0, yc, 30.1), (+19.8, yc, 30.1), 3.35, 3.15, UV_BARREL, segs=12)
            for by_o, bz_o in ((-1.35, -1.35), (+1.35, -1.35), (+1.35, +1.35), (-1.35, +1.35)):
                rp.add_cylinder((+18.5, yc + by_o, 30.1 + bz_o), (+25.2, yc + by_o, 30.1 + bz_o), 0.72, 0.64, UV_CHROME, segs=8)
            gp.add_box(+22.4, +25.4, yc - 2.7, yc + 2.7, 27.4, 32.8, UV_HAZARD)
            gp.add_box(-3.2, +4.0, yc + sy * 3.4, yc + sy * 6.2, 27.0, 33.2, UV_DRUM_MAG)

        leds_static.add_box(+9.7, +9.9, +7.2, +8.0, 23.2, 24.0, UV_LED_GRN)
        leds_static.add_box(+9.7, +9.9, +5.8, +6.6, 23.2, 24.0, UV_LED_AMB)
        leds_static.add_sphere((+9.4, -9.4, 56.2), 0.9, UV_LED_CYN, stacks=6, slices=8)
        _add_muzzle_flash_cone(muzzle_l, (+25.6, +15.0, 30.1), 2.1, 5.8, UV_LED_AMB)
        _add_muzzle_flash_cone(muzzle_r, (+25.6, -15.0, 30.1), 2.1, 5.8, UV_LED_AMB)
        crt_piv = (0.0, 0.0, 38.0)
        muzzle_pts = [(+25.6, +15.0, 30.1), (+25.6, -15.0, 30.1)]
        yc_l, zc_gun = 15.0, 30.1

    nf = 24
    frame_names = (
        [f"deploy_{i:02d}" for i in range(8)]
        + [f"idle_{i:02d}" for i in range(8)]
        + [f"fire_{i:02d}" for i in range(8)]
    )

    body_parts_defs = [tower, crt_case, gun_left, gun_right, rotor_left, rotor_right, extra_anim]
    body_frames_lists = [[] for _ in body_parts_defs]
    scr_frames = []
    leds_frames = []
    muzl_frames = []
    muzr_frames = []

    for fi in range(nf):
        t_scale = (1.0, 1.0, 1.0)
        t_off = (0.0, 0.0, 0.0)
        crt_scale = 1.0
        crt_off = (0.0, 0.0, 0.0)
        crt_pitch = 0.0
        gl_off = (0.0, 0.0, 0.0)
        gr_off = (0.0, 0.0, 0.0)
        rot_l_ang = 0.0
        rot_r_ang = 0.0
        ex_off = (0.0, 0.0, 0.0)
        ex_yaw = 0.0
        ml_sc = 0.001
        mr_sc = 0.001

        if fi < 8:
            u = smootherstep(fi / 7.0)
            t_scale = (0.28 + 0.72 * u, 0.28 + 0.72 * u, 0.14 + 0.86 * u)
            t_off = (0.0, 0.0, -14.0 * (1.0 - u))
            crt_scale = 0.18 + 0.82 * u
            crt_off = (0.0, 0.0, -22.0 * (1.0 - u))
            crt_pitch = -20.0 * (1.0 - u)
            gl_off = (-5.0 * (1.0 - u), -6.0 * (1.0 - u), -11.0 * (1.0 - u))
            gr_off = (-5.0 * (1.0 - u), +6.0 * (1.0 - u), -11.0 * (1.0 - u))
            ex_off = (0.0, 0.0, -16.0 * (1.0 - u))
        elif fi < 16:
            ph = 2.0 * math.pi * ((fi - 8) / 8.0)
            crt_pitch = 1.4 * math.sin(ph)
            ex_yaw = 16.0 * math.sin(ph)
            rot_l_ang = (fi - 8) * 22.5
            rot_r_ang = -(fi - 8) * 22.5
        else:
            k = fi - 16
            ph = 2.0 * math.pi * (k / 8.0)
            alt_l = 1.0 if (k % 2 == 0) else 0.2
            alt_r = 1.0 if (k % 2 == 1) else 0.2
            recoil_mag = 3.2 if concept_id == "msdos" else 2.6
            gl_off = (-recoil_mag * alt_l, 0.0, 0.0)
            gr_off = (-recoil_mag * alt_r, 0.0, 0.0)
            t_off = (-0.55 * max(alt_l, alt_r), 0.0, -0.25 * math.sin(ph * 2.0))
            crt_pitch = -2.0 * math.sin(ph * 2.0)
            rot_l_ang = k * 45.0
            rot_r_ang = -k * 45.0
            ex_off = (0.0, 0.0, 0.55 * math.sin(ph * 2.0))
            ml_sc = 1.05 if (k in (0, 1)) else 0.001
            mr_sc = 1.05 if (k in (4, 5)) else 0.001

        body_frames_lists[0].append(xform_part_vn(tower, offset=t_off, pivot=(0.0, 0.0, 20.0), scale=t_scale))
        body_frames_lists[1].append(xform_part_vn(crt_case, offset=crt_off, ry=crt_pitch, pivot=crt_piv, scale=crt_scale))
        body_frames_lists[2].append(xform_part_vn(gun_left, offset=gl_off, pivot=(0.0, yc_l, zc_gun), scale=t_scale[0]))
        body_frames_lists[3].append(xform_part_vn(gun_right, offset=gr_off, pivot=(0.0, -yc_l, zc_gun), scale=t_scale[0]))
        body_frames_lists[4].append(xform_part_vn(rotor_left, offset=gl_off, rx=rot_l_ang, pivot=(0.0, yc_l, zc_gun), scale=t_scale[0]))
        body_frames_lists[5].append(xform_part_vn(rotor_right, offset=gr_off, rx=rot_r_ang, pivot=(0.0, -yc_l, zc_gun), scale=t_scale[0]))
        body_frames_lists[6].append(xform_part_vn(extra_anim, offset=ex_off, rz=ex_yaw, pivot=crt_piv, scale=crt_scale))

        scr_frames.append(xform_part_vn(screen, offset=crt_off, ry=crt_pitch, pivot=crt_piv, scale=crt_scale))
        leds_frames.append(xform_part_vn(leds_static, offset=t_off, ry=crt_pitch * 0.4, pivot=crt_piv, scale=crt_scale))
        muzl_frames.append(xform_part_vn(muzzle_l, offset=gl_off, pivot=muzzle_pts[0], scale=ml_sc))
        muzr_frames.append(xform_part_vn(muzzle_r, offset=gr_off, pivot=muzzle_pts[1], scale=mr_sc))

    merged_body, frames_body = combine_parts_frames(list(zip(body_parts_defs, body_frames_lists)))
    merged_leds, frames_leds = combine_parts_frames([
        (leds_static, leds_frames),
        (muzzle_l, muzl_frames),
        (muzzle_r, muzr_frames),
    ])

    surfaces = [
        dict(name="turret_body", shader=f"progs/ds_{concept_id}_body", tris=merged_body.tris, st=merged_body.st, frames=frames_body),
        dict(name="turret_leds", shader="progs/ds_leds", tris=merged_leds.tris, st=merged_leds.st, frames=frames_leds),
        dict(name="crt_screen", shader=f"progs/ds_{concept_id}_scr_active", tris=screen.tris, st=screen.st, frames=scr_frames),
    ]
    return dict(
        name=f"ds_{concept_id}_turret",
        surfaces=surfaces,
        nframes=nf,
        frame_names=frame_names,
        muzzle_pts=muzzle_pts,
    )


def build_floppy_md3(concept_id: str) -> Dict:
    raw = build_floppy_disk_mesh(half_w=3.2, half_h=3.4, half_t=0.25)
    frames, fnames = [], []
    for fi in range(8):
        if fi == 0:
            fnames.append("fly_flat")
            frames.append(xform_part_vn(raw, ry=-90.0))
        else:
            fnames.append(f"stuck_{fi:02d}")
            vib = 0.0 if fi == 1 else (0.35 * math.sin(fi * 2.4))
            frames.append(xform_part_vn(raw, offset=(vib, 0.0, 3.8), ry=-22.0 + vib * 6.0))
    surf = dict(name="floppy_disk", shader=f"progs/ds_{concept_id}_floppy", tris=raw.tris, st=raw.st, frames=frames)
    return dict(name=f"ds_{concept_id}_floppy", surfaces=[surf], nframes=8, frame_names=fnames)


def build_gib_md3s(concept_id: str) -> List[Dict]:
    gibs = []
    g0 = MeshPart("gib_crt")
    g0.add_box(-3.6, 3.6, -5.2, 5.2, -4.2, 4.2, UV_TOWER_SIDE, uv_px=UV_CRT_BEZEL, uv_nx=UV_CRT_BACK)
    g0.add_box(-5.5, -3.4, -3.2, 3.2, -2.8, 2.8, UV_CRT_BACK)
    g1 = MeshPart("gib_tower")
    g1.add_box(-4.8, 4.8, -1.0, 1.0, -5.2, 5.2, UV_TOWER_SIDE, uv_px=UV_TOWER_FRONT)
    g1.add_box(-3.2, 3.2, 0.6, 2.2, -2.5, 2.5, UV_DRUM_MAG)
    g2 = MeshPart("gib_barrel")
    g2.add_cylinder((-6.0, 0.0, 0.0), (+6.5, 0.0, 0.0), 1.6, 1.4, UV_BARREL, segs=10)
    g2.add_box(-4.0, +1.5, -2.2, +2.2, -2.0, +2.0, UV_HAZARD)
    for gi, gp in enumerate((g0, g1, g2)):
        vv, nn = xform_part_vn(gp)
        surf = dict(name=f"gib_{gi}", shader=f"progs/ds_{concept_id}_body", tris=gp.tris, st=gp.st, frames=[(vv, nn)])
        gibs.append(dict(name=f"ds_{concept_id}_gib{gi}", surfaces=[surf], nframes=1, frame_names=["gib0"]))
    return gibs


def validate_and_write_md3(model_dict: Dict, out_path: str) -> Tuple[int, int]:
    nf = model_dict["nframes"]
    tot_v, tot_t = 0, 0
    for s in model_dict["surfaces"]:
        nv, nt = len(s["st"]), len(s["tris"])
        assert 0 < nv <= 4096, f"{model_dict['name']}/{s['name']}: nv={nv} > 4096"
        assert 0 < nt <= 8192, f"{model_dict['name']}/{s['name']}: nt={nt} > 8192"
        assert len(s["frames"]) == nf
        for vv, nn in s["frames"]:
            av = np.asarray(vv, dtype=np.float32)
            an = np.asarray(nn, dtype=np.float32)
            assert np.isfinite(av).all() and np.isfinite(an).all()
            assert np.max(np.abs(av)) < 500.0
        tot_v += nv
        tot_t += nt
    md3lib.write(out_path, model_dict)
    with open(out_path, "rb") as f:
        ident, ver = struct.unpack("<4si", f.read(8))
    assert ident == b"IDP3" and ver == 15
    rt = md3lib.read(out_path)
    assert rt["nframes"] == nf
    return tot_v, tot_t


def build_all() -> Dict:
    os.makedirs(TEX_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("[disc_sentry] Rebuilding textures & upgraded 3D MD3 models...")
    texgen.build_leds_texture(TEX_DIR)

    manifest = {"concepts": []}
    for spec in CONCEPT_SPECS:
        cid = spec["id"]
        texgen.build_concept_body_texture(cid, TEX_DIR)
        texgen.build_floppy_texture(cid, TEX_DIR)
        crt_paths = texgen.build_crt_screens_for_concept(cid, TEX_DIR)

        base_m = build_base_md3(cid)
        tur_m = _build_turret_geometry(cid)
        muzzle_pts = tur_m.pop("muzzle_pts")
        floppy_m = build_floppy_md3(cid)
        gib_ms = build_gib_md3s(cid)

        bv, bt = validate_and_write_md3(base_m, os.path.join(MODEL_DIR, f"ds_{cid}_base.md3"))
        tv, tt = validate_and_write_md3(tur_m, os.path.join(MODEL_DIR, f"ds_{cid}_turret.md3"))
        fv, ft = validate_and_write_md3(floppy_m, os.path.join(MODEL_DIR, f"ds_{cid}_floppy.md3"))
        for gi, gm in enumerate(gib_ms):
            validate_and_write_md3(gm, os.path.join(MODEL_DIR, f"ds_{cid}_gib{gi}.md3"))

        print(
            f"  [OK] #{spec['num']} {spec['title']:24s} | "
            f"base {bv:4d}v/{bt:4d}t | turret {tv:4d}v/{tt:4d}t | floppy {fv:3d}v/{ft:3d}t"
        )
        manifest["concepts"].append({
            **spec,
            "base_md3": f"ds_{cid}_base.md3",
            "turret_md3": f"ds_{cid}_turret.md3",
            "floppy_md3": f"ds_{cid}_floppy.md3",
            "gib_md3s": [f"ds_{cid}_gib{gi}.md3" for gi in range(3)],
            "muzzle_pts": muzzle_pts,
            "crt_screens": {k: os.path.basename(v) for k, v in crt_paths.items()},
            "stats": {
                "base_verts": bv, "base_tris": bt,
                "turret_verts": tv, "turret_tris": tt,
                "floppy_verts": fv, "floppy_tris": ft,
            },
        })

    mpath = os.path.join(OUT_ROOT, "models_manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


if __name__ == "__main__":
    build_all()
