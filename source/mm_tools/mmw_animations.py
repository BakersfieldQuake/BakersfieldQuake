"""Multi-Frame Animation Rigs for BakersfieldQuake Mega Man Weapon Models ('The Mega-Slinger' Mk.II):
  1. Model A (Flagship): 'THE MEGA-SLINGER' Mk.II Mag-Pneumatic Rail-Catapult Gun (37 frames: idle1..16 + fire1..20 + empty1)
  2. Model B (Variant):  'RANGER GAUNTLET THROW' Articulated Hand-Held Thrower (32 frames: idle1..16 + throw1..16)
  3. Model C (Payload):  Standalone Recreated 'Mega Man' Contraption (16 frames: drive1..16)
"""
import math
from mmw_geometry import (
    MeshPart,
    SLINGER_MM_REST_X,
    SLINGER_MM_REST_Z,
    build_articulated_ranger_hand,
    build_megaman_payload_parts,
    build_slinger_fx_frame,
    build_slinger_static_parts,
    rot_axis,
    rot_x,
    rot_y,
    rot_z,
    transform_megaman_frame,
    vadd,
    vcross,
    vdot,
    vlerp,
    vmul,
    vnorm,
    vsub,
)

# --------------------------------------------------------------------------- Eye-Space Viewmodel Transforms
# Quake 1st-person eye at (0,0,0) looking +X, +Y left, -Y right, +Z up.
# Heroically framed for BOTH 90 deg FOV (studio default) and 111 deg FOV (BakersfieldQuake config.cfg)
# so the player sees the glowing MEGA-CORE reflex sight, canted 0-250 PSI dial, left Ranger support glove,
# glowing cyan twin accelerator rails, both spinning 4-cutout wheels, and gleaming chrome bullet nose!
GUN_SCALE = 0.82
GUN_BASE = (7.25, -5.45, -4.38)
GUN_PITCH = 4.2
GUN_ROLL = -8.0
GUN_YAW = 13.5


def gun_to_eye(p, recoil_dx=0.0, recoil_dy=0.0, recoil_dz=0.0, kick_pitch=0.0, kick_roll=0.0, kick_yaw=0.0):
    q = (p[0] + recoil_dx, p[1] + recoil_dy, p[2] + recoil_dz)
    q = rot_x(q, GUN_ROLL + kick_roll)
    q = rot_y(q, GUN_PITCH + kick_pitch)
    q = vmul(q, GUN_SCALE)
    q = rot_z(q, GUN_YAW + kick_yaw)
    return vadd(q, GUN_BASE)


def gun_nrm_to_eye(n, kick_pitch=0.0, kick_roll=0.0, kick_yaw=0.0):
    qn = rot_x(n, GUN_ROLL + kick_roll)
    qn = rot_y(qn, GUN_PITCH + kick_pitch)
    qn = rot_z(qn, GUN_YAW + kick_yaw)
    return vnorm(qn)


# ===========================================================================
# 1. BUILD FLAGSHIP MODEL A: 'THE MEGA-SLINGER' MK.II MAG-PNEUMATIC CATAPULT
# ===========================================================================
def build_slinger_gun_schedule():
    """37-frame schedule (100% synced with megaman.qc frame timings!):
      Frames  0..15 (16 frames): Lively motorized idle! Seamless 360 deg wheel spin + 1080 deg brass roller spin,
                                 visible pneumatic tire suspension bobble, Quake figure-8 weapon sway, quivering 195 PSI needle!
      Frames 16..18 ( 3 frames): Pre-launch mag-charge & rail acceleration! Claws snap open, PSI spikes to 246, rail arcs crackle!
      Frame  19     ( 1 frame ): SUPERSONIC MUZZLE LAUNCH! Crescent sabot slams forward stop, Mega Man rockets clear off muzzle
                                 inside a 3D starburst flash + feathered Mach cone + angled compensator gas plumes!
      Frames 20..24 ( 5 frames): Weighty two-stage pneumatic recoil kick, pressurized gas blowoff & smooth hydraulic sabot return!
      Frames 25..35 (11 frames): Full-scale (1.0x) spring-elevator pop-up reload, tire spin-up & crisp retention-jaw clamp lock!
      Frame  36     ( 1 frame ): Empty standby state ('empty1') while out of ammo.
    """
    sched = []
    # --- Frames 0..15: Lively Motorized Idle Loop ---
    for i in range(16):
        ph = 2.0 * math.pi * (i / 16.0)
        sched.append(dict(
            name=f"idle{i + 1}",
            dx=0.18 * math.sin(ph),
            dy=0.14 * math.cos(ph),
            dz=0.22 * math.sin(ph * 2.0 + 0.45),
            kp=0.65 * math.sin(ph + 0.35),
            kr=0.85 * math.cos(ph),
            ky=0.55 * math.sin(ph),
            mm_show=True,
            mm_x=SLINGER_MM_REST_X + 0.04 * math.sin(ph * 2.0),
            # Authentic motorized rubber-tire suspension bobble & rock on the drive rollers!
            mm_z=SLINGER_MM_REST_Z + 0.14 * math.sin(ph * 2.0) + 0.05 * math.cos(ph * 4.0),
            mm_pitch=1.15 * math.cos(ph * 2.0),
            mm_roll=2.35 * math.sin(ph * 2.0 + 0.5),
            mm_scale=1.0,
            mm_spin=i * 22.5,      # exact 360 deg wheel rotation across 16 frames
            roller_spin=i * 67.5,  # exact 1080 deg (3x) tangent roller spin — 100% seamless loop!
            ram_x=SLINGER_MM_REST_X - 5.02,
            clamp_open=0.03 + 0.02 * math.sin(ph * 2.0),
            elev_z=0.0,
            psi=195.0 + 6.5 * math.sin(ph * 2.0 + 0.3),
            armed=True,
            trig_pull=0.0,
            blast=0.0,
            arc=0.0,
            steam=0.0,
        ))

    # --- Frames 16..35: Fire, Launch, Two-Stage Recoil, Gas Blowoff & Full-Scale Reload + Frame 36 Empty ---
    fire_specs = [
        # 16..17 (fire1..2): Coiled anticipation tuck! Trigger squeezes, retention claws snap wide open, wheels rev hard, PSI redlines!
        dict(name="fire1",  dx=+0.15, dy=-0.06, dz=-0.10, kp=-0.8, kr=+0.9, ky=-0.3, mm_x=13.52, mm_z=2.50, mm_p=+0.6, mm_r=-1.5, mm_sc=1.0, spin=48,  ram=8.50,  clmp=0.58, elv=0.0,  psi=224, arm=True,  trig=0.60, bl=0.00, arc=0.38, stm=0.00),
        dict(name="fire2",  dx=+0.28, dy=-0.10, dz=-0.18, kp=-1.5, kr=+1.6, ky=-0.5, mm_x=13.45, mm_z=2.54, mm_p=+1.2, mm_r=+1.8, mm_sc=1.0, spin=118, ram=8.42,  clmp=1.00, elv=0.0,  psi=246, arm=True,  trig=1.00, bl=0.00, arc=0.82, stm=0.00),
        # 18 (fire3): RAIL SLAM ACCELERATION! Crescent sabot surges forward down glowing rails (no premature shock-ring yet!)
        dict(name="fire3",  dx=-0.95, dy=+0.12, dz=+0.28, kp=+3.8, kr=-2.2, ky=+0.9, mm_x=19.85, mm_z=2.52, mm_p=-0.8, mm_r=0.0,  mm_sc=1.0, spin=215, ram=14.80, clmp=1.00, elv=0.0,  psi=148, arm=True,  trig=1.00, bl=0.00, arc=1.00, stm=0.28),
        # 19 (fire4): SUPERSONIC MUZZLE LAUNCH! Full-scale Mega Man blasts off muzzle inside starburst flash + Mach cone!
        dict(name="fire4",  dx=-2.65, dy=+0.34, dz=+0.68, kp=+9.2, kr=-5.2, ky=+2.2, mm_x=27.20, mm_z=2.66, mm_p=-2.2, mm_r=0.0,  mm_sc=1.0, spin=335, ram=20.65, clmp=1.00, elv=0.0,  psi=28,  arm=False, trig=1.00, bl=1.00, arc=1.00, stm=0.88),
        # 20..21 (fire5..6): Heavy follow-through recoil absorption & billowing forward compensator gas plumes!
        dict(name="fire5",  dx=-2.85, dy=+0.38, dz=+0.74, kp=+10.0,kr=-5.8, ky=+2.4, mm_x=26.50, mm_z=2.55, mm_p=0.0,  mm_r=0.0,  mm_sc=0.001, spin=440, ram=20.45, clmp=1.00, elv=0.0, psi=18, arm=False, trig=0.85, bl=0.52, arc=0.48, stm=1.00),
        dict(name="fire6",  dx=-2.10, dy=+0.26, dz=+0.52, kp=+7.0, kr=-3.8, ky=+1.6, mm_x=6.00,  mm_z=0.35, mm_p=0.0,  mm_r=0.0,  mm_sc=0.001, spin=520, ram=18.10, clmp=1.00, elv=0.0, psi=26, arm=False, trig=0.58, bl=0.18, arc=0.16, stm=0.82),
        # 22..24 (fire7..9): Hydraulic sabot pistons hiss & retract smoothly back to breech!
        dict(name="fire7",  dx=-1.30, dy=+0.15, dz=+0.28, kp=+4.0, kr=-2.0, ky=+0.9, mm_x=6.00,  mm_z=0.35, mm_p=0.0,  mm_r=0.0,  mm_sc=0.001, spin=0,   ram=14.40, clmp=1.00, elv=0.0,  psi=48,  arm=False, trig=0.32, bl=0.00, arc=0.00, stm=0.50),
        dict(name="fire8",  dx=-0.68, dy=+0.06, dz=+0.08, kp=+1.8, kr=-0.8, ky=+0.4, mm_x=6.00,  mm_z=0.35, mm_p=0.0,  mm_r=0.0,  mm_sc=0.001, spin=0,   ram=10.80, clmp=0.96, elv=0.0,  psi=78,  arm=False, trig=0.12, bl=0.00, arc=0.00, stm=0.22),
        dict(name="fire9",  dx=-0.28, dy=+0.00, dz=-0.08, kp=+0.4, kr=-0.2, ky=+0.1, mm_x=13.60, mm_z=-3.80, mm_p=0.0, mm_r=0.0,  mm_sc=0.001, spin=0,   ram=8.72,  clmp=0.94, elv=-2.4, psi=108, arm=False, trig=0.00, bl=0.00, arc=0.00, stm=0.05),
        # 25..30 (fire10..15): FULL-SCALE (1.0x) spring-elevator pop-up reload from underneath w/ crisp settle bounce!
        dict(name="fire10", dx=-0.16, dy=-0.04, dz=-0.22, kp=-0.8, kr=+0.5, ky=0.0,  mm_x=13.60, mm_z=-3.60, mm_p=+7.5, mm_r=-2.5, mm_sc=1.00, spin=24,  ram=8.58, clmp=0.94, elv=-2.2, psi=130, arm=False, trig=0.00, bl=0.00, arc=0.00, stm=0.00),
        dict(name="fire11", dx=-0.12, dy=-0.05, dz=-0.26, kp=-1.3, kr=+0.8, ky=0.0,  mm_x=13.60, mm_z=-1.35, mm_p=+5.0, mm_r=-1.6, mm_sc=1.00, spin=62,  ram=8.58, clmp=0.96, elv=-1.1, psi=148, arm=False, trig=0.00, bl=0.00, arc=0.00, stm=0.00),
        dict(name="fire12", dx=-0.06, dy=-0.03, dz=-0.16, kp=-1.0, kr=+0.6, ky=0.0,  mm_x=13.60, mm_z=+0.85, mm_p=+2.5, mm_r=-0.6, mm_sc=1.00, spin=106, ram=8.58, clmp=0.95, elv=-0.1, psi=164, arm=False, trig=0.00, bl=0.00, arc=0.00, stm=0.00),
        dict(name="fire13", dx=+0.02, dy=+0.02, dz=+0.04, kp=+0.2, kr=-0.2, ky=0.0,  mm_x=13.60, mm_z=+2.28, mm_p=+0.6, mm_r=+1.2, mm_sc=1.00, spin=154, ram=8.58, clmp=0.86, elv=+0.6, psi=176, arm=False, trig=0.00, bl=0.00, arc=0.00, stm=0.00),
        dict(name="fire14", dx=+0.08, dy=+0.05, dz=+0.18, kp=+0.9, kr=-0.8, ky=0.0,  mm_x=13.60, mm_z=+2.80, mm_p=-1.2, mm_r=+3.0, mm_sc=1.00, spin=202, ram=8.58, clmp=0.52, elv=+0.9, psi=186, arm=True,  trig=0.00, bl=0.00, arc=0.14, stm=0.00),
        dict(name="fire15", dx=+0.05, dy=+0.03, dz=+0.08, kp=+0.4, kr=-0.3, ky=0.0,  mm_x=13.60, mm_z=+2.46, mm_p=+0.4, mm_r=-1.4, mm_sc=1.00, spin=245, ram=8.58, clmp=0.12, elv=+0.3, psi=192, arm=True,  trig=0.00, bl=0.00, arc=0.24, stm=0.00),
        # 31..35 (fire16..20): Retention jaws CLAMP SHUT with tactile downward lock-jolt & cyan spark; settles cleanly to idle1!
        dict(name="fire16", dx=-0.08, dy=-0.04, dz=-0.16, kp=-1.0, kr=+1.3, ky=-0.2, mm_x=13.60, mm_z=+2.44, mm_p=0.0,  mm_r=+1.2, mm_sc=1.00, spin=280, ram=8.58, clmp=0.00, elv=+0.05,psi=196, arm=True,  trig=0.00, bl=0.00, arc=0.12, stm=0.00),
        dict(name="fire17", dx=-0.04, dy=+0.02, dz=-0.06, kp=-0.4, kr=+0.9, ky=-0.1, mm_x=13.60, mm_z=+2.52, mm_p=+0.5, mm_r=+1.6, mm_sc=1.00, spin=304, ram=8.58, clmp=0.02, elv=0.0,  psi=198, arm=True,  trig=0.00, bl=0.00, arc=0.00, stm=0.00),
        dict(name="fire18", dx=+0.02, dy=+0.08, dz=+0.04, kp=+0.1, kr=+0.8, ky=0.0,  mm_x=13.60, mm_z=+2.51, mm_p=+0.8, mm_r=+1.4, mm_sc=1.00, spin=322, ram=8.58, clmp=0.02, elv=0.0,  psi=197, arm=True,  trig=0.00, bl=0.00, arc=0.00, stm=0.00),
        dict(name="fire19", dx=+0.01, dy=+0.12, dz=+0.08, kp=+0.2, kr=+0.85,ky=0.0,  mm_x=13.60, mm_z=+2.52, mm_p=+1.0, mm_r=+1.2, mm_sc=1.00, spin=338, ram=8.58, clmp=0.03, elv=0.0,  psi=196, arm=True,  trig=0.00, bl=0.00, arc=0.00, stm=0.00),
        dict(name="fire20", dx=+0.00, dy=+0.14, dz=+0.10, kp=+0.2, kr=+0.85,ky=0.0,  mm_x=13.60, mm_z=+2.53, mm_p=+1.1, mm_r=+1.1, mm_sc=1.00, spin=350, ram=8.58, clmp=0.03, elv=0.0,  psi=196, arm=True,  trig=0.00, bl=0.00, arc=0.00, stm=0.00),
        # 36 (empty1): Out-of-ammo standby state (megaman.qc)
        dict(name="empty1", dx=+0.00, dy=+0.00, dz=+0.00, kp=+0.0, kr=+0.0, ky=+0.0, mm_x=6.00,  mm_z=+0.35, mm_p=0.0,  mm_r=0.0,  mm_sc=0.001, spin=0,   ram=8.58, clmp=0.92, elv=0.0,  psi=55,  arm=False, trig=0.00, bl=0.00, arc=0.00, stm=0.00),
    ]
    for fs in fire_specs:
        sched.append(dict(
            name=fs["name"],
            dx=fs["dx"], dy=fs["dy"], dz=fs["dz"], kp=fs["kp"], kr=fs["kr"], ky=fs["ky"],
            mm_show=fs["mm_sc"] > 0.01,
            mm_x=fs["mm_x"], mm_z=fs["mm_z"], mm_pitch=fs["mm_p"], mm_roll=fs["mm_r"],
            mm_scale=fs["mm_sc"], mm_spin=fs["spin"],
            roller_spin=fs["spin"] * 3.0,
            ram_x=fs["ram"],
            clamp_open=fs["clmp"],
            elev_z=fs["elv"],
            psi=fs["psi"],
            armed=fs["arm"],
            trig_pull=fs["trig"],
            blast=fs["bl"], arc=fs["arc"], steam=fs["stm"],
        ))
    assert len(sched) == 37
    return sched


def build_slinger_gun_md3_surfaces():
    """Builds all 6 clean MD3 surfaces for Model A ('THE MEGA-SLINGER' Mk.II) across 37 frames."""
    mm_parts = build_megaman_payload_parts()
    gun_parts = build_slinger_static_parts()
    dial_center, dial_axis = gun_parts["dial_meta"]
    sched = build_slinger_gun_schedule()

    # Anatomically natural, zero-clipping Left Foregrip C-Grip & Right Pistol Trigger Hand
    rhand_frames_local = []
    lhand_static = build_articulated_ranger_hand(
        palm_center=(10.75, +0.82, -2.38),
        fwd_dir=(+0.90, -0.25, -0.35),
        up_dir=(+0.20, +0.96, -0.18),
        side_sign=+1.0,
        finger_curls=(0.82, 0.86, 0.88, 0.90),
        thumb_curl=0.72,
        thumb_abd=36.0,
        hand_scale=0.80,
        forearm_len=11.0,
        forearm_dir=(-0.72, +0.46, -0.52),
    )
    for fr in sched:
        tp = fr["trig_pull"]
        rh = build_articulated_ranger_hand(
            palm_center=(2.55, -0.78, -2.92),
            fwd_dir=(+0.90, +0.25, -0.35),
            up_dir=(+0.20, -0.96, -0.18),
            side_sign=-1.0,
            finger_curls=(0.45 + 0.40 * tp, 0.86, 0.88, 0.90),
            thumb_curl=0.76,
            thumb_abd=34.0,
            hand_scale=0.82,
            forearm_len=11.5,
            forearm_dir=(-0.68, -0.44, -0.58),
        )
        rhand_frames_local.append(rh)

    # --- Surface 1: gun_metal ---
    sub_gun_list = [
        ("receiver", gun_parts["receiver"]),
        ("ram", gun_parts["ram"]),
        ("clamp_l", gun_parts["clamp_l"]),
        ("clamp_r", gun_parts["clamp_r"]),
        ("roller_l", gun_parts["roller_l"]),
        ("roller_r", gun_parts["roller_r"]),
        ("elevator", gun_parts["elevator"]),
        ("trigger", gun_parts["trigger"]),
    ]
    gm_st, gm_tris = [], []
    v_off = 0
    for _, sp in sub_gun_list:
        gm_st += sp.st
        gm_tris += [(a + v_off, b + v_off, c + v_off) for (a, b, c) in sp.tris]
        v_off += len(sp.verts)

    gm_frames = []
    for fr in sched:
        vv, nn = [], []
        dx, dy, dz, kp, kr, ky = fr["dx"], fr["dy"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]
        roller_spin = fr["roller_spin"]

        for tag, sp in sub_gun_list:
            for p, n in zip(sp.verts, sp.norms):
                lp, ln = p, n
                if tag == "ram":
                    lp = (p[0] + fr["ram_x"], p[1], p[2])
                elif tag == "clamp_l":
                    ang = -60.0 * fr["clamp_open"]
                    lp = rot_x(p, ang)
                    ln = rot_x(n, ang)
                    lp = (lp[0], lp[1] + 1.18, lp[2] + 1.48)
                elif tag == "clamp_r":
                    ang = +60.0 * fr["clamp_open"]
                    lp = rot_x(p, ang)
                    ln = rot_x(n, ang)
                    lp = (lp[0], lp[1] - 1.18, lp[2] + 1.48)
                elif tag == "roller_l":
                    lp = rot_y(p, +roller_spin)
                    ln = rot_y(n, +roller_spin)
                    lp = (lp[0] + 11.08, lp[1] + 5.72, lp[2] - 1.24)
                elif tag == "roller_r":
                    lp = rot_y(p, +roller_spin)
                    ln = rot_y(n, +roller_spin)
                    lp = (lp[0] + 11.08, lp[1] - 5.72, lp[2] - 1.24)
                elif tag == "elevator":
                    lp = (p[0], p[1], p[2] + fr["elev_z"])
                elif tag == "trigger":
                    tang = -26.0 * fr["trig_pull"]
                    lp = rot_y(p, tang)
                    ln = rot_y(n, tang)
                    lp = (lp[0] + 4.35, lp[1], lp[2] - 1.45)

                vv.append(gun_to_eye(lp, dx, dy, dz, kp, kr, ky))
                nn.append(gun_nrm_to_eye(ln, kp, kr, ky))
        gm_frames.append((vv, nn))

    surf_gun = dict(name="slinger_body", shader="progs/mmw_gun_metal", mat="gun_metal", tris=gm_tris, st=gm_st, frames=gm_frames)

    # --- Surface 2 & 3: Mega Man Payload ('chrome_axle' & 'wheel') ---
    ca_sub = [mm_parts["bar_axle"], mm_parts["wheel_hw_l"], mm_parts["wheel_hw_r"]]
    ca_st, ca_tris = [], []
    vo = 0
    for sp in ca_sub:
        ca_st += sp.st
        ca_tris += [(a + vo, b + vo, c + vo) for (a, b, c) in sp.tris]
        vo += len(sp.verts)

    wh_sub = [mm_parts["wheel_l"], mm_parts["wheel_r"]]
    wh_st, wh_tris = [], []
    vo = 0
    for sp in wh_sub:
        wh_st += sp.st
        wh_tris += [(a + vo, b + vo, c + vo) for (a, b, c) in sp.tris]
        vo += len(sp.verts)

    ca_frames, wh_frames = [], []
    for fr in sched:
        dx, dy, dz, kp, kr, ky = fr["dx"], fr["dy"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]
        xf = transform_megaman_frame(
            mm_parts,
            spin_deg=fr["mm_spin"],
            bar_pitch_deg=fr["mm_pitch"],
            roll_deg=fr["mm_roll"],
            pos=(fr["mm_x"], 0.0, fr["mm_z"]),
            scale=fr["mm_scale"],
        )
        cv, cn = [], []
        for k in ("bar_axle", "wheel_hw_l", "wheel_hw_r"):
            pts, nrms = xf[k]
            cv += [gun_to_eye(p, dx, dy, dz, kp, kr, ky) for p in pts]
            cn += [gun_nrm_to_eye(n, kp, kr, ky) for n in nrms]
        ca_frames.append((cv, cn))

        wv, wn = [], []
        for k in ("wheel_l", "wheel_r"):
            pts, nrms = xf[k]
            wv += [gun_to_eye(p, dx, dy, dz, kp, kr, ky) for p in pts]
            wn += [gun_nrm_to_eye(n, kp, kr, ky) for n in nrms]
        wh_frames.append((wv, wn))

    surf_mm_chrome = dict(name="megaman_bar", shader="progs/mmw_chrome_axle", mat="chrome_axle", tris=ca_tris, st=ca_st, frames=ca_frames)
    surf_mm_wheels = dict(name="megaman_wheels", shader="progs/mmw_wheel", mat="wheel", tris=wh_tris, st=wh_st, frames=wh_frames)

    # --- Surface 4: PSI Dial + Rail Chevrons + Animated PSI Needle + Reflex Core ('gauge_glow', unlit!) ---
    glow_base = MeshPart("gauge_glow")
    glow_base.append_part(gun_parts["dial_face"])
    needle_part = gun_parts["psi_needle"]
    glow_base.append_part(needle_part)

    # Holographic rear reflex sight plasma screen nestled cleanly inside the armored sight arch!
    bar_v0 = len(glow_base.verts)
    for v_top, v_bot in ((0.66, 0.81), (0.83, 0.98)):
        glow_base.add_quad(
            (0.62, +0.86, 2.22), (0.62, -0.86, 2.22), (0.88, -0.86, 1.70), (0.88, +0.86, 1.70),
            (0.02, v_top), (0.98, v_top), (0.98, v_bot), (0.02, v_bot),
            nrm=vnorm((-0.89, 0.0, +0.45)),
        )

    glow_frames = []
    for fr in sched:
        dx, dy, dz, kp, kr, ky = fr["dx"], fr["dy"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]
        vv, nn = [], []
        df = gun_parts["dial_face"]
        for p, n in zip(df.verts, df.norms):
            vv.append(gun_to_eye(p, dx, dy, dz, kp, kr, ky))
            nn.append(gun_nrm_to_eye(n, kp, kr, ky))

        psi_frac = max(0.0, min(1.0, fr["psi"] / 250.0))
        n_deg = 135.0 - 270.0 * psi_frac
        for p, n in zip(needle_part.verts, needle_part.norms):
            rp = vadd(dial_center, rot_axis(p, dial_axis, n_deg))
            rn = rot_axis(n, dial_axis, n_deg)
            vv.append(gun_to_eye(rp, dx, dy, dz, kp, kr, ky))
            nn.append(gun_nrm_to_eye(rn, kp, kr, ky))

        for qi in range(2):
            active = (qi == 0 and fr["armed"]) or (qi == 1 and not fr["armed"])
            push_in = (0.0, 0.0, 0.0) if active else (+1.20, 0.0, -0.95)
            for k in range(4):
                bp = vadd(glow_base.verts[bar_v0 + qi * 4 + k], push_in)
                bn = glow_base.norms[bar_v0 + qi * 4 + k]
                vv.append(gun_to_eye(bp, dx, dy, dz, kp, kr, ky))
                nn.append(gun_nrm_to_eye(bn, kp, kr, ky))
        glow_frames.append((vv, nn))

    surf_glow = dict(name="slinger_gauge", shader="progs/mmw_gauge_glow", mat="gauge_glow", unlit=True, tris=glow_base.tris, st=glow_base.st, frames=glow_frames)

    # --- Surface 5: Quake Ranger Hands ---
    rh0 = rhand_frames_local[0]
    off_lh = len(rh0.verts)
    hand_st = list(rh0.st) + list(lhand_static.st)
    hand_tris = list(rh0.tris) + [(a + off_lh, b + off_lh, c + off_lh) for (a, b, c) in lhand_static.tris]
    hand_frames = []
    for fi, fr in enumerate(sched):
        dx, dy, dz, kp, kr, ky = fr["dx"], fr["dy"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]
        rh = rhand_frames_local[fi]
        vv = [gun_to_eye(p, dx, dy, dz, kp, kr, ky) for p in rh.verts]
        nn = [gun_nrm_to_eye(n, kp, kr, ky) for n in rh.norms]
        vv += [gun_to_eye(p, dx, dy, dz, kp, kr, ky) for p in lhand_static.verts]
        nn += [gun_nrm_to_eye(n, kp, kr, ky) for n in lhand_static.norms]
        hand_frames.append((vv, nn))

    surf_hands = dict(name="ranger_hands", shader="progs/mmw_hand", mat="hand", tris=hand_tris, st=hand_st, frames=hand_frames)

    # --- Surface 6: Volumetric Muzzle Starburst, Mach Cone, Rail Plasma & Exhaust Plumes ---
    fx_parts = [build_slinger_fx_frame(fr["blast"], fr["arc"], fr["steam"], fi) for fi, fr in enumerate(sched)]
    fx0 = fx_parts[0]
    fx_frames = []
    for fi, fr in enumerate(sched):
        dx, dy, dz, kp, kr, ky = fr["dx"], fr["dy"], fr["dz"], fr["kp"], fr["kr"], fr["ky"]
        fxp = fx_parts[fi]
        vv = [gun_to_eye(p, dx, dy, dz, kp, kr, ky) for p in fxp.verts]
        nn = [gun_nrm_to_eye(n, kp, kr, ky) for n in fxp.norms]
        fx_frames.append((vv, nn))

    surf_fx = dict(name="slinger_fx", shader="progs/mmw_fx", mat="fx", unlit=True, additive=True, tris=fx0.tris, st=fx0.st, frames=fx_frames)

    return [surf_gun, surf_mm_chrome, surf_mm_wheels, surf_glow, surf_hands, surf_fx], [fr["name"] for fr in sched]


# ===========================================================================
# 2. BUILD VARIANT MODEL B: 'RANGER GAUNTLET THROW' (Articulated Hand-Throw)
# ===========================================================================
def build_hand_throw_md3_surfaces():
    """32-frame articulated Quake Ranger hand-held Mega Man weapon."""
    mm_parts = build_megaman_payload_parts()
    MM_SC = 0.78

    def pipe_grip_and_axis(mm_pos, pitch_deg, yaw_deg, roll_deg):
        ax = rot_z(rot_y(rot_x((1.0, 0.0, 0.0), roll_deg), pitch_deg), yaw_deg)
        up = rot_z(rot_y(rot_x((0.0, 0.0, 1.0), roll_deg), pitch_deg), yaw_deg)
        grip_pt = vadd(mm_pos, vmul(ax, -2.85 * MM_SC))
        return grip_pt, vnorm(ax), vnorm(up)

    sched = []
    for i in range(16):
        ph = 2.0 * math.pi * (i / 16.0)
        mm_p = (
            16.8 + 0.22 * math.sin(ph),
            -5.45 + 0.24 * math.cos(ph),
            -2.30 + 0.26 * math.sin(ph * 2.0 + 0.4),
        )
        pitch_d = 46.0 + 1.8 * math.sin(ph + 0.3)
        yaw_d = 16.5 + 1.2 * math.cos(ph)
        roll_d = -6.0 + 2.2 * math.sin(ph * 2.0)
        gp, p_ax, p_up = pipe_grip_and_axis(mm_p, pitch_d, yaw_d, roll_d)
        sched.append(dict(
            name=f"idle{i + 1}",
            mm_pos=mm_p, mm_pitch=pitch_d, mm_yaw=yaw_d, mm_roll=roll_d, mm_scale=MM_SC,
            mm_spin=i * 22.5,
            hand_grip=gp, pipe_ax=p_ax, pipe_up=p_up,
            rel_blend=0.0,
            arm_dir=(-0.58, -0.52, -0.63),
            curls=(0.86, 0.90, 0.92, 0.94),
            tcurl=0.72 + 0.06 * math.sin(ph * 2.0),
            tabd=38.0,
            wake=0.0,
        ))

    throw_kf = [
        dict(n="wind1",  mp=(15.4, -6.1, -1.7), p=52.0, y=11.5, r=-12.0, sc=MM_SC, sp=45,  hg=None, rb=0.0, ad=(-0.56,-0.55,-0.62), c=(0.90,0.92,0.94,0.95), tc=0.82, wk=0.0),
        dict(n="wind2",  mp=(13.7, -7.0, -1.0), p=60.0, y=6.0,  r=-17.0, sc=MM_SC, sp=110, hg=None, rb=0.0, ad=(-0.54,-0.58,-0.61), c=(0.92,0.94,0.96,0.96), tc=0.86, wk=0.0),
        dict(n="wind3",  mp=(12.9, -7.4, -0.7), p=64.0, y=4.0,  r=-20.0, sc=MM_SC, sp=190, hg=None, rb=0.0, ad=(-0.52,-0.60,-0.61), c=(0.92,0.94,0.96,0.96), tc=0.86, wk=0.15),
        dict(n="throw1", mp=(18.4, -4.1, -1.8), p=30.0, y=18.5, r=-4.0,  sc=MM_SC, sp=290, hg=(15.8, -4.9, -3.4), rb=0.55, ad=(-0.60,-0.48,-0.64), c=(0.45,0.48,0.52,0.55), tc=0.35, wk=0.85),
        dict(n="throw2", mp=(28.5, -2.0, -0.9), p=14.0, y=19.5, r=0.0,   sc=MM_SC, sp=410, hg=(17.0, -4.2, -3.2), rb=1.00, ad=(-0.64,-0.44,-0.63), c=(0.08,0.10,0.12,0.15), tc=0.08, wk=1.00),
        dict(n="throw3", mp=(44.0, -0.6, -0.1), p=6.0,  y=19.0, r=0.0,   sc=MM_SC, sp=540, hg=(16.5, -4.5, -3.8), rb=1.00, ad=(-0.62,-0.46,-0.64), c=(0.06,0.08,0.10,0.14), tc=0.06, wk=0.65),
        dict(n="throw4", mp=(65.0, +0.2, +0.4), p=2.0,  y=18.5, r=0.0,   sc=MM_SC, sp=680, hg=(15.0, -5.2, -4.9), rb=0.85, ad=(-0.58,-0.48,-0.66), c=(0.15,0.18,0.22,0.25), tc=0.15, wk=0.25),
        dict(n="reach1", mp=(12.0, -9.0, -18.0), p=46.0, y=16.5, r=-6.0, sc=0.001, sp=0,   hg=(13.2, -6.2, -7.0), rb=0.50, ad=(-0.54,-0.50,-0.68), c=(0.35,0.38,0.42,0.45), tc=0.30, wk=0.0),
        dict(n="reach2", mp=(12.0, -9.0, -18.0), p=46.0, y=16.5, r=-6.0, sc=0.001, sp=0,   hg=(12.0, -7.0, -8.8), rb=0.25, ad=(-0.52,-0.52,-0.68), c=(0.55,0.58,0.62,0.65), tc=0.45, wk=0.0),
        dict(n="grab1",  mp=(14.2, -7.2, -7.6),  p=54.0, y=13.5, r=-10.0, sc=MM_SC, sp=40,  hg=None, rb=0.0, ad=(-0.56,-0.52,-0.64), c=(0.75,0.78,0.82,0.85), tc=0.62, wk=0.0),
        dict(n="raise1", mp=(15.6, -6.1, -4.5),  p=50.0, y=15.5, r=-8.0,  sc=MM_SC, sp=105, hg=None, rb=0.0, ad=(-0.57,-0.52,-0.64), c=(0.82,0.86,0.88,0.90), tc=0.68, wk=0.0),
        dict(n="raise2", mp=(16.9, -5.3, -1.7),  p=43.0, y=17.2, r=-5.0,  sc=MM_SC, sp=175, hg=None, rb=0.0, ad=(-0.58,-0.51,-0.63), c=(0.68,0.72,0.75,0.78), tc=0.55, wk=0.0),
        dict(n="catch1", mp=(17.1, -5.2, -1.8),  p=44.5, y=17.0, r=-5.5,  sc=MM_SC, sp=235, hg=None, rb=0.0, ad=(-0.58,-0.51,-0.63), c=(0.88,0.92,0.94,0.96), tc=0.78, wk=0.12),
        dict(n="settle1",mp=(16.7, -5.5, -2.45), p=47.0, y=16.2, r=-6.5,  sc=MM_SC, sp=285, hg=None, rb=0.0, ad=(-0.58,-0.52,-0.63), c=(0.88,0.91,0.93,0.95), tc=0.75, wk=0.0),
        dict(n="settle2",mp=(16.8, -5.46,-2.33), p=46.2, y=16.4, r=-6.1,  sc=MM_SC, sp=325, hg=None, rb=0.0, ad=(-0.58,-0.52,-0.63), c=(0.86,0.90,0.92,0.94), tc=0.73, wk=0.0),
        dict(n="settle3",mp=(16.8, -5.45,-2.30), p=46.0, y=16.5, r=-6.0,  sc=MM_SC, sp=352, hg=None, rb=0.0, ad=(-0.58,-0.52,-0.63), c=(0.86,0.90,0.92,0.94), tc=0.72, wk=0.0),
    ]
    for tk in throw_kf:
        gp, p_ax, p_up = pipe_grip_and_axis(tk["mp"], tk["p"], tk["y"], tk["r"])
        if tk["hg"] is not None:
            gp = tk["hg"]
            p_ax = vnorm((0.66, +0.21, +0.72))
            p_up = vnorm((-0.55, +0.20, +0.81))
        sched.append(dict(
            name=tk["n"],
            mm_pos=tk["mp"], mm_pitch=tk["p"], mm_yaw=tk["y"], mm_roll=tk["r"], mm_scale=tk["sc"],
            mm_spin=tk["sp"],
            hand_grip=gp, pipe_ax=p_ax, pipe_up=p_up,
            rel_blend=tk["rb"],
            arm_dir=tk["ad"],
            curls=tk["c"], tcurl=tk["tc"], tabd=38.0 if tk["tc"] > 0.4 else 52.0,
            wake=tk["wk"],
        ))
    assert len(sched) == 32

    ca_sub = [mm_parts["bar_axle"], mm_parts["wheel_hw_l"], mm_parts["wheel_hw_r"]]
    ca_st, ca_tris = [], []
    vo = 0
    for sp in ca_sub:
        ca_st += sp.st
        ca_tris += [(a + vo, b + vo, c + vo) for (a, b, c) in sp.tris]
        vo += len(sp.verts)

    wh_sub = [mm_parts["wheel_l"], mm_parts["wheel_r"]]
    wh_st, wh_tris = [], []
    vo = 0
    for sp in wh_sub:
        wh_st += sp.st
        wh_tris += [(a + vo, b + vo, c + vo) for (a, b, c) in sp.tris]
        vo += len(sp.verts)

    ca_frames, wh_frames, hand_meshes, wake_meshes = [], [], [], []
    for fr in sched:
        xf = transform_megaman_frame(
            mm_parts,
            spin_deg=fr["mm_spin"],
            bar_pitch_deg=fr["mm_pitch"],
            pos=fr["mm_pos"],
            yaw_deg=fr["mm_yaw"],
            roll_deg=fr["mm_roll"],
            scale=fr["mm_scale"],
        )
        cv, cn = [], []
        for k in ("bar_axle", "wheel_hw_l", "wheel_hw_r"):
            pts, nrms = xf[k]
            cv += pts
            cn += nrms
        ca_frames.append((cv, cn))

        wv, wn = [], []
        for k in ("wheel_l", "wheel_r"):
            pts, nrms = xf[k]
            wv += pts
            wn += nrms
        wh_frames.append((wv, wn))

        P_ax = fr["pipe_ax"]
        f_hint = (+0.68, +0.72, +0.08)
        F_pipe = vnorm(vsub(f_hint, vmul(P_ax, vdot(f_hint, P_ax))))
        U_pipe = vnorm(vcross(F_pipe, P_ax))

        rb = fr["rel_blend"]
        F_open = vnorm((+0.78, +0.26, +0.57))
        U_open = vnorm((+0.22, -0.88, +0.42))
        F_hand = vnorm(vlerp(F_pipe, F_open, rb))
        U_raw = vlerp(U_pipe, U_open, rb)
        U_hand = vnorm(vsub(U_raw, vmul(F_hand, vdot(U_raw, F_hand))))

        palm_c = vadd(fr["hand_grip"], vadd(vmul(U_hand, 0.94), vmul(F_hand, -0.48)))

        hm = build_articulated_ranger_hand(
            palm_center=palm_c,
            fwd_dir=F_hand,
            up_dir=U_hand,
            side_sign=-1.0,
            finger_curls=fr["curls"],
            thumb_curl=fr["tcurl"],
            thumb_abd=fr["tabd"],
            hand_scale=0.88,
            forearm_len=11.5,
            forearm_dir=fr["arm_dir"],
        )
        hand_meshes.append(hm)

        wm = MeshPart("fx")
        wk = fr["wake"]
        for sgn in (-1.0, +1.0):
            if wk > 0.01:
                w_c = vadd(fr["mm_pos"], (0.0, sgn * 4.2, 0.0))
                pts = [vadd(w_c, (-6.5 * wk, 0.0, -0.8 * wk)), vadd(w_c, (-2.8 * wk, 0.0, -0.3 * wk)), w_c]
                rads = [0.05, 0.28 * wk, 0.42 * wk]
            else:
                pts = [(2.0, -20.0, -20.0), (2.02, -20.0, -20.0), (2.04, -20.0, -20.0)]
                rads = [0.001, 0.001, 0.001]
            wm.add_tube(pts, rads, segs=6, uv_rect=(0.03, 0.03, 0.47, 0.47))
        wake_meshes.append(wm)

    h0 = hand_meshes[0]
    w0 = wake_meshes[0]
    surfs = [
        dict(name="megaman_bar", shader="progs/mmw_chrome_axle", mat="chrome_axle", tris=ca_tris, st=ca_st, frames=ca_frames),
        dict(name="megaman_wheels", shader="progs/mmw_wheel", mat="wheel", tris=wh_tris, st=wh_st, frames=wh_frames),
        dict(name="ranger_gauntlet", shader="progs/mmw_hand", mat="hand", tris=h0.tris, st=h0.st, frames=[(m.verts, m.norms) for m in hand_meshes]),
        dict(name="throw_wake", shader="progs/mmw_fx", mat="fx", unlit=True, additive=True, tris=w0.tris, st=w0.st, frames=[(m.verts, m.norms) for m in wake_meshes]),
    ]
    return surfs, [fr["name"] for fr in sched]


# ===========================================================================
# 3. BUILD STANDALONE RECREATED PAYLOAD ('megaman_clean.md3', 16 drive frames)
# ===========================================================================
def build_standalone_megaman_md3_surfaces():
    """16-frame clean recreated Mega Man world/projectile model at authentic -34.7 deg bar rest angle."""
    mm_parts = build_megaman_payload_parts()
    ca_sub = [mm_parts["bar_axle"], mm_parts["wheel_hw_l"], mm_parts["wheel_hw_r"]]
    ca_st, ca_tris = [], []
    vo = 0
    for sp in ca_sub:
        ca_st += sp.st
        ca_tris += [(a + vo, b + vo, c + vo) for (a, b, c) in sp.tris]
        vo += len(sp.verts)

    wh_sub = [mm_parts["wheel_l"], mm_parts["wheel_r"]]
    wh_st, wh_tris = [], []
    vo = 0
    for sp in wh_sub:
        wh_st += sp.st
        wh_tris += [(a + vo, b + vo, c + vo) for (a, b, c) in sp.tris]
        vo += len(sp.verts)

    ca_frames, wh_frames = [], []
    names = []
    for i in range(16):
        names.append(f"drive{i + 1}")
        xf = transform_megaman_frame(
            mm_parts,
            spin_deg=i * 22.5,
            bar_pitch_deg=-34.7,
            pos=(0.0, 0.0, 4.02),
            scale=1.6,
        )
        cv, cn = [], []
        for k in ("bar_axle", "wheel_hw_l", "wheel_hw_r"):
            pts, nrms = xf[k]
            cv += pts
            cn += nrms
        ca_frames.append((cv, cn))

        wv, wn = [], []
        for k in ("wheel_l", "wheel_r"):
            pts, nrms = xf[k]
            wv += pts
            wn += nrms
        wh_frames.append((wv, wn))

    return [
        dict(name="megaman_bar", shader="progs/mmw_chrome_axle", mat="chrome_axle", tris=ca_tris, st=ca_st, frames=ca_frames),
        dict(name="megaman_wheels", shader="progs/mmw_wheel", mat="wheel", tris=wh_tris, st=wh_st, frames=wh_frames),
    ], names
