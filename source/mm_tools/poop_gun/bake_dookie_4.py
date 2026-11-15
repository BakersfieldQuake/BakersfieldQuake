"""Bake all 4 escalating forward-aiming Dookie Bazooka designs (`dookie_mk1` .. `dookie_mk4`)."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from dookie_rig import (
    PROJ_WH,
    TP_WH,
    VM_WH,
    key_forward_cannon_rig,
    load_rgba,
    load_shared_assets,
    make_contact_sheet,
    render_proj_sequence,
    render_tp_sequence,
    render_vm_sequence,
    save_rgba,
)
from poop_core import WORK_DIR

ART_DIR = r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841"

ALL_HEAD_KEYS = [
    "head_cross",
    "head_turban_grin",
    "head_oiled_yell",
    "head_turban_yell",
    "head_scream_front",
    "head_wide_grin",
    "head_side_yell_l",
    "head_side_yell_r",
    "head_laugh_tilt",
    "head_sky_gasp",
]


def _make_head_slots(coords: List[tuple]) -> List[Dict[str, Any]]:
    slots = []
    n = len(ALL_HEAD_KEYS)
    for i, (cx, cy, sz) in enumerate(coords):
        k0 = ALL_HEAD_KEYS[i % n]
        k1 = ALL_HEAD_KEYS[(i + 3) % n]
        k2 = ALL_HEAD_KEYS[(i + 6) % n]
        slots.append({
            "cx": cx,
            "cy": cy,
            "size": sz,
            "keys": [k0, k1, k2],
            "amp_x": 5.5 + (i % 3) * 1.5,
            "amp_y": 6.5 + (i % 2) * 2.0,
            "tilt": -6.0 if i % 2 == 0 else 6.0,
        })
    return slots


VARIANT_SPECS: List[Dict[str, Any]] = [
    {
        "id": "dookie_mk1",
        "num": 1,
        "title": "MK-I: DOOKIE BAZOOKA",
        "subtitle": "Forward Tactical Plunger • 4-Head Glass Tube",
        "accent": "#f59e0b",
        "tagline": "Re-angled forward FPS aim with a giant crystal head chamber, 4 calmly arguing blokes, dual tricolor flags, PSI gauge & 4 tank-orbiting flies.",
        "proj_style": "sprint",
        "proj_kind": "sprint",
        "src_jpg": os.path.join(ART_DIR, "cannon_forward_c3_1794702254910.jpg"),
        "vm_scale": 0.72,
        "vm_offset": (96.0, 42.0),
        "nudge_left_arm": (40.0, -52.0),
        "psi_dials": [
            {"center": (814.5, 507.5), "radius": 47.0, "seg": ((795.0, 490.0), (855.0, 535.0))}
        ],
        "glass_poly": [(442, 240), (620, 215), (865, 345), (850, 515), (690, 500), (430, 380)],
        "plunger_cut": (402, 468, 0.56, 248.0, 304.0),
        "plunger_pivot": (292.0, 285.0),
        "head_slots": _make_head_slots([
            (504, 312, 128),
            (604, 356, 136),
            (708, 402, 142),
            (802, 442, 134),
        ]),
        "slosh_amp": 9.0,
        "slosh_level": 0.72,
        "soup_rgb": (96, 74, 24),
        "n_bubbles": 10,
        "flags": [
            {"anchor": (395.0, 315.0), "pole_vec": (-30.0, -148.0), "size": (196, 122), "pole_left": False, "angle": 9.0, "thick": 7},
            {"anchor": (838.0, 256.0), "pole_vec": (14.0, -144.0), "size": (192, 120), "pole_left": True, "angle": -6.0, "thick": 7},
        ],
        "mud_globs": [(230, 190, 56), (350, 285, 48), (745, 690, 52)],
        "muzzle_pt": (205.0, 240.0),
        "n_flies": 4,
        "recoil_mult": 1.0,
        "blast_mult": 1.0,
    },
    {
        "id": "dookie_mk2",
        "num": 2,
        "title": "MK-II: TURBO FLUSHER",
        "subtitle": "Twin Plungers • 4-Head Poop-Soup Aquarium",
        "accent": "#22c55e",
        "tagline": "Doubled over-under plunger muzzles + dripping toilet-brush bayonet + MEGA STINK gauge + 4 calmly bobbing heads in sloshing poop soup!",
        "proj_style": "sprint",
        "proj_kind": "turbo",
        "src_jpg": os.path.join(ART_DIR, "cannon_mk2_turbo_wide_1794702438113.jpg"),
        "vm_scale": 0.72,
        "vm_offset": (96.0, 44.0),
        "psi_dials": [
            {"center": (828.5, 517.5), "radius": 44.0, "seg": ((826.0, 520.0), (870.0, 492.0))}
        ],
        "glass_poly": [(300, 160), (470, 155), (890, 330), (880, 540), (700, 530), (295, 335)],
        "plunger_cut": (352, 548, 0.25, 220.0, 315.0),
        "plunger_pivot": (268.0, 240.0),
        "head_slots": _make_head_slots([
            (388, 260, 118),
            (522, 326, 134),
            (668, 396, 142),
            (806, 464, 136),
        ]),
        "tank_tint": (98, 128, 42),
        "tank_alpha": 124,
        "slosh_amp": 18.0,
        "slosh_level": 0.54,
        "soup_rgb": (104, 86, 22),
        "soup_alpha": 175,
        "n_bubbles": 14,
        "flags": [
            {"anchor": (318.0, 185.0), "pole_vec": (-32.0, -110.0), "size": (205, 126), "pole_left": False, "angle": 10.0, "thick": 7},
            {"anchor": (815.0, 228.0), "pole_vec": (14.0, -138.0), "size": (200, 124), "pole_left": True, "angle": -6.0, "thick": 7},
        ],
        "mud_globs": [(180, 145, 60), (140, 375, 50), (545, 610, 56), (885, 680, 54)],
        "muzzle_pt": (175.0, 200.0),
        "n_flies": 5,
        "fly_scale": 0.96,
        "recoil_mult": 1.15,
        "blast_mult": 1.15,
    },
    {
        "id": "dookie_mk3",
        "num": 3,
        "title": "MK-III: PORCELAIN THRONE",
        "subtitle": "Crowned Toilet Bazooka • 5 Dome Heads + Bowl Stowaway",
        "accent": "#38bdf8",
        "tagline": "Royally gilded porcelain toilet cannon! 5 readable heads in the crowned dome + stowaway bloke peeking out of the toilet bowl + 3 flags!",
        "proj_style": "sprint",
        "proj_kind": "torpedo",
        "src_jpg": os.path.join(ART_DIR, "cannon_mk3_porcelain_v2_1794702443259.jpg"),
        "vm_scale": 0.72,
        "vm_offset": (96.0, 44.0),
        "protect_boxes": [(55, 420, 550, 940), (780, 720, 1020, 920)],
        "keep_toilet_3p": True,
        "psi_dials": [
            {"center": (830.5, 492.5), "radius": 38.0, "seg": ((815.0, 492.0), (866.0, 535.0))}
        ],
        "glass_poly": [(430, 175), (620, 155), (895, 310), (885, 535), (675, 520), (425, 370)],
        "plunger_cut": (340, 435, 0.35, 220.0, 290.0),
        "plunger_pivot": (280.0, 235.0),
        "head_slots": _make_head_slots([
            (504, 290, 122),
            (584, 344, 130),
            (666, 310, 134),
            (748, 398, 138),
            (824, 418, 132),
        ]),
        "toilet_stowaway": (378.0, 512.0, 92),
        "slosh_amp": 14.0,
        "slosh_level": 0.65,
        "soup_rgb": (118, 92, 26),
        "n_bubbles": 14,
        "flags": [
            {"anchor": (338.0, 225.0), "pole_vec": (-30.0, -125.0), "size": (184, 114), "pole_left": False, "angle": 9.0, "thick": 6},
            {"anchor": (718.0, 62.0), "pole_vec": (-8.0, -56.0), "size": (146, 92), "pole_left": True, "angle": -4.0, "thick": 5},
            {"anchor": (866.0, 255.0), "pole_vec": (22.0, -142.0), "size": (186, 116), "pole_left": True, "angle": -8.0, "thick": 6},
        ],
        "mud_globs": [(155, 145, 58), (118, 530, 52), (415, 765, 54)],
        "muzzle_pt": (175.0, 200.0),
        "n_flies": 6,
        "fly_scale": 1.0,
        "recoil_mult": 1.25,
        "blast_mult": 1.25,
    },
    {
        "id": "dookie_mk4",
        "num": 4,
        "title": "MK-IV: OMEGA BFG-9000",
        "subtitle": "Winning Design • 5 Reactor Heads + Slow Tank Flies + Hand-Waving Runner",
        "accent": "#ef4444",
        "tagline": "CHOSEN WINNER! Caged toxic reactor with 5 calm bobbing heads, Chakra turbine wheel, 4 flags, 7 slow flies orbiting the tank & ONE hand-waving bloke projectile!",
        "proj_style": "sprint",
        "proj_kind": "cyclone",
        "src_jpg": os.path.join(ART_DIR, "cannon_mk4_omega_1794702432523.jpg"),
        "vm_scale": 0.66,
        "vm_offset": (164.0, 44.0),
        "psi_dials": [
            {"center": (827.0, 515.0), "radius": 47.0, "seg": ((810.0, 498.0), (868.0, 538.0))},
            {"center": (940.0, 548.0), "radius": 38.0, "seg": ((925.0, 535.0), (976.0, 565.0))},
        ],
        "glass_poly": [(445, 245), (625, 195), (895, 325), (890, 540), (705, 525), (445, 390)],
        "plunger_cut": (392, 435, 0.35, 220.0, 320.0),
        "plunger_pivot": (285.0, 225.0),
        "head_slots": _make_head_slots([
            (504, 286, 126),
            (584, 328, 134),
            (668, 372, 140),
            (750, 412, 136),
            (828, 444, 126),
        ]),
        "head_spin": False,
        "tank_tint": (88, 168, 42),
        "tank_alpha": 135,
        "slosh_amp": 20.0,
        "slosh_level": 0.48,
        "soup_rgb": (110, 145, 28),
        "soup_alpha": 180,
        "bubble_rgb": (175, 255, 85, 210),
        "n_bubbles": 18,
        "chakra_wheel": (795.0, 425.0, 120),
        "neon_pulse": [(480, 535, 72), (885, 835, 84)],
        "flags": [
            {"anchor": (368.0, 245.0), "pole_vec": (-34.0, -130.0), "size": (190, 118), "pole_left": False, "angle": 10.0, "thick": 7},
            {"anchor": (615.0, 190.0), "pole_vec": (-14.0, -108.0), "size": (150, 94), "pole_left": False, "angle": 4.0, "thick": 6},
            {"anchor": (748.0, 222.0), "pole_vec": (-8.0, -148.0), "size": (146, 92), "pole_left": True, "angle": -4.0, "thick": 6},
            {"anchor": (862.0, 272.0), "pole_vec": (4.0, -108.0), "size": (140, 88), "pole_left": True, "angle": -8.0, "thick": 6},
        ],
        "mud_globs": [(155, 125, 64), (108, 305, 56), (725, 675, 58), (885, 745, 56)],
        "muzzle_pt": (195.0, 215.0),
        "n_flies": 7,
        "fly_scale": 0.96,
        "recoil_mult": 1.38,
        "blast_mult": 1.38,
    },
]


def bake_variant(cfg: Dict[str, Any], assets: Dict[str, Any]) -> None:
    vid = cfg["id"]
    out_dir = os.path.join(WORK_DIR, vid)
    os.makedirs(out_dir, exist_ok=True)
    # Remove stale sequence PNGs before saving updated frame counts
    import glob as _glob
    for old_f in _glob.glob(os.path.join(out_dir, "*.png")):
        os.remove(old_f)

    print(f"[{vid}] Keying & building rig from {os.path.basename(cfg['src_jpg'])}...")
    rig = key_forward_cannon_rig(cfg)

    print(f"[{vid}] Rendering VM idle (120), fire (20), reload (18)...")
    vm_idle = render_vm_sequence(rig, cfg, assets, "idle", 120)
    vm_fire = render_vm_sequence(rig, cfg, assets, "fire", 20)
    vm_reload = render_vm_sequence(rig, cfg, assets, "reload", 18)

    for prefix, seq in [("vm_idle", vm_idle), ("vm_fire", vm_fire), ("vm_reload", vm_reload)]:
        for i, fr in enumerate(seq):
            save_rgba(fr, os.path.join(out_dir, f"{prefix}_{i:03d}.png"))

    print(f"[{vid}] Rendering 16x8 escalating projectile ({cfg['proj_kind']})...")
    proj_files = render_proj_sequence(assets, cfg["proj_kind"], out_dir)

    print(f"[{vid}] Rendering 3P enemy idle (60), fire (20), reload (16)...")
    tp_idle = render_tp_sequence(rig, cfg, assets, "idle", 60)
    tp_fire = render_tp_sequence(rig, cfg, assets, "fire", 20)
    tp_reload = render_tp_sequence(rig, cfg, assets, "reload", 16)
    for prefix, seq in [("tp_idle", tp_idle), ("tp_fire", tp_fire), ("tp_reload", tp_reload)]:
        for i, fr in enumerate(seq):
            save_rgba(fr, os.path.join(out_dir, f"{prefix}_{i:03d}.png"))

    # Save visual verification contact sheets
    vm_sample = vm_idle[::24] + vm_fire[::4] + vm_reload[::4]
    vm_lbls = [f"vi_{i*24:03d}" for i in range(len(vm_idle[::24]))] + [f"vf_{i*4:02d}" for i in range(len(vm_fire[::4]))] + [f"vr_{i*4:02d}" for i in range(len(vm_reload[::4]))]
    save_rgba(make_contact_sheet(vm_sample, 5, (210, 180), vm_lbls), os.path.join(out_dir, "sheet_vm.png"))

    tp_sample = tp_idle[::10] + tp_fire[::4] + tp_reload[::4]
    tp_lbls = [f"ti_{i*10:02d}" for i in range(len(tp_idle[::10]))] + [f"tf_{i*4:02d}" for i in range(len(tp_fire[::4]))] + [f"tr_{i*4:02d}" for i in range(len(tp_reload[::4]))]
    save_rgba(make_contact_sheet(tp_sample, 5, (160, 160), tp_lbls), os.path.join(out_dir, "sheet_tp.png"))

    p_sample = [load_rgba(os.path.join(out_dir, proj_files[a][f])) for a in range(0, 16, 4) for f in range(0, 8, 2)]
    p_lbls = [f"a{a:02d}f{f}" for a in range(0, 16, 4) for f in range(0, 8, 2)]
    save_rgba(make_contact_sheet(p_sample, 4, (140, 158), p_lbls), os.path.join(out_dir, "sheet_proj.png"))

    scale_g = cfg.get("vm_scale", 0.72)
    ox, oy = cfg.get("vm_offset", (96.0, 44.0))
    mx, my = cfg["muzzle_pt"]
    manifest = {
        "id": vid,
        "title": cfg["title"],
        "subtitle": cfg["subtitle"],
        "tagline": cfg["tagline"],
        "fps": 60,
        "vm_size": list(VM_WH),
        "proj_size": list(PROJ_WH),
        "tp_size": list(TP_WH),
        "muzzle_norm": [(ox + mx * scale_g) / (VM_WH[0] * 2.0), (oy + my * scale_g) / (VM_WH[1] * 2.0)],
        "vm_idle": [f"vm_idle_{i:03d}.png" for i in range(len(vm_idle))],
        "vm_fire": [f"vm_fire_{i:03d}.png" for i in range(len(vm_fire))],
        "vm_reload": [f"vm_reload_{i:03d}.png" for i in range(len(vm_reload))],
        "proj": {"angles": 16, "frames_per_angle": 8, "files": proj_files},
        "tp_idle": [f"tp_idle_{i:03d}.png" for i in range(len(tp_idle))],
        "tp_fire": [f"tp_fire_{i:03d}.png" for i in range(len(tp_fire))],
        "tp_reload": [f"tp_reload_{i:03d}.png" for i in range(len(tp_reload))],
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2)
    print(f"[{vid}] Complete -> {out_dir}")


if __name__ == "__main__":
    shared = load_shared_assets()
    for cfg in VARIANT_SPECS:
        bake_variant(cfg, shared)
    print("[bake_dookie_4] ALL 4 DOOKIE BAZOOKA TIERS BAKED SUCCESSFULLY!")
