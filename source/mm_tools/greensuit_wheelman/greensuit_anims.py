r"""All 12 Expressive 3D Animations, Preview Diagnostic Renderer, Full 360° 8-Angle Sprite Renderer,
and Animated .GLB Exporter for Green-Suit Wheelman!

Animations (each rendered across all 8 360° directions d=0..7):
  1. seated_cruise     (12f) — Classic Photo-4 Seated Wheel-Cruise (warm smile, spinning tires, suspension bounce)
  2. scream_turbo      (12f) — Photo-3 Straining Battle-Cry Overdrive & Bullet-Tip Floor Sparks
  3. plank_rollout     (12f) — Photo-2 Living-Room Ab-Roller Plank Launch ('OOOO!' face)
  4. hero_crane_point  (12f) — Photo-1 One-Leg Crane Kick & Sky-Point ('OOOO!' face + cradling wheel rig)
  5. overhead_press    (12f) — Heavy Barbell Squat-Clean & Overhead Lockout Press
  6. cyclone_spin      (12f) — 360° Helicopter Wheel-Barbell Tornado w/ Neon Plasma Trails
  7. wheelie_backflip  (14f) — Sparks Wheelie Launch -> Full Mid-Air 360° Backflip -> Shockwave Land
  8. bazooka_ram       (12f) — Sprinting Chrome-Rod Joust / Rocket Battering-Ram Charge
  9. throw_boomerang   (14f) — Heavy 3D Wheel-Rig Hurl, Spinning Flight & Clean Catch
  10. breakdance_flare (12f) — Green-Suit B-Boy Rolling Axle Handstand V-Flare
  11. victory_groove   (12f) — Electric Wheel-Guitar Shred & Disco Side-Kick Groove
  12. gib_explosion    (14f) — Quake Mega-Gib & Flying Tires / Chrome Rod Detonation

Run preview diagnostic (renders 8 key frames + contact sheet in ~4s):
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P source/mm_tools/greensuit_wheelman/greensuit_anims.py -- --preview

Run full 1,200-frame 360° render + .GLB export:
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P source/mm_tools/greensuit_wheelman/greensuit_anims.py
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from typing import Callable, Dict, List, Tuple

import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import greensuit_rig as gr

OUT_RAW = os.path.join(HERE, "renders_raw")
PREV_DIR = os.path.join(HERE, "ref", "preview_renders")
GLB_OUT = os.path.join(HERE, "greensuit_wheelman_3d.glb")
os.makedirs(OUT_RAW, exist_ok=True)
os.makedirs(PREV_DIR, exist_ok=True)

ARGV = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
PREVIEW_MODE = "--preview" in ARGV

TAU = 2.0 * math.pi
R_TIRE = 0.190

ANIM_SPECS: List[Dict] = [
    {"id": "seated_cruise",    "frames": 12, "fps": 18, "title": "Seated Wheel-Cruise",       "cam": (2.28, 0.60, 0.44)},
    {"id": "scream_turbo",     "frames": 12, "fps": 24, "title": "Battle-Cry Turbo Sparks",   "cam": (2.32, 0.60, 0.44)},
    {"id": "plank_rollout",    "frames": 12, "fps": 16, "title": "Ab-Roller Plank Rollout",   "cam": (3.35, 0.78, 0.40)},
    {"id": "hero_crane_point", "frames": 12, "fps": 16, "title": "One-Leg Crane & Sky-Point", "cam": (3.30, 0.96, 0.92)},
    {"id": "overhead_press",   "frames": 12, "fps": 16, "title": "Heavy Barbell Squat-Press", "cam": (3.70, 1.08, 1.04)},
    {"id": "cyclone_spin",     "frames": 12, "fps": 24, "title": "360° Wheel-Rig Cyclone",    "cam": (3.15, 0.94, 0.88)},
    {"id": "wheelie_backflip", "frames": 14, "fps": 20, "title": "Wheelie & Mid-Air Backflip","cam": (3.30, 0.96, 0.80)},
    {"id": "bazooka_ram",      "frames": 12, "fps": 22, "title": "Chrome-Rod Rocket Joust",   "cam": (3.15, 0.94, 0.88)},
    {"id": "throw_boomerang",  "frames": 14, "fps": 18, "title": "3D Wheel-Rig Boomerang",    "cam": (3.55, 0.96, 0.88)},
    {"id": "breakdance_flare", "frames": 12, "fps": 20, "title": "Axle Handstand V-Flare",    "cam": (3.25, 0.96, 0.88)},
    {"id": "victory_groove",   "frames": 12, "fps": 18, "title": "Wheel-Guitar Disco Groove", "cam": (3.18, 0.96, 0.90)},
    {"id": "gib_explosion",    "frames": 14, "fps": 18, "title": "Quake Mega-Gib Detonation", "cam": (3.55, 0.92, 0.72)},
]


# ---------------------------------------------------------------------------
# World-Space Bone & Rig Posing Helpers
# ---------------------------------------------------------------------------

class RigContext:
    def __init__(self, sc, cam_rig, cam_obj, mats, arm_obj, body_obj, head_obj, ik_ctrl, wheel_rig, vfx):
        self.sc = sc
        self.cam_rig = cam_rig
        self.cam_obj = cam_obj
        self.mats = mats
        self.arm = arm_obj
        self.body = body_obj
        self.head = head_obj
        self.ik = ik_ctrl
        self.wrig = wheel_rig
        self.vfx = vfx

    def reset_frame(self) -> None:
        self.body.hide_render = False
        self.head.hide_render = False
        self.body.scale = (1.0, 1.0, 1.0)
        self.wrig["root"].hide_render = False
        for ch in self.wrig["root"].children_recursive:
            ch.hide_render = False
        self.wrig["wheel_L"].location = (+0.375, 0.0, 0.0)
        self.wrig["wheel_R"].location = (-0.375, 0.0, 0.0)
        self.wrig["wheel_L"].rotation_euler = (0.0, 0.0, 0.0)
        self.wrig["wheel_R"].rotation_euler = (0.0, 0.0, 0.0)
        self.wrig["rod_pivot"].location = (0.0, 0.0, 0.0)
        self.wrig["rod_pivot"].rotation_euler = (math.radians(56.0), 0.0, 0.0)
        self.wrig["shadow"].hide_render = False
        self.wrig["shadow"].location = (0.0, -0.05, 0.001)
        self.wrig["shadow"].scale = (1.10, 1.00, 1.0)

        for pb in self.arm.pose.bones:
            pb.matrix_basis = Matrix.Identity(4)

        for grp in self.vfx.values():
            for o in grp:
                o.hide_render = True

    def pose_torso_chain(
        self,
        pelvis_pos: Tuple[float, float, float],
        pelvis_rot: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        spine_add: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        chest_add: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        head_world_rot: Tuple[float, float, float] | None = None,
        head_add: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        """Sets Pelvis -> Spine -> Chest -> Neck -> Head using intuitive World Euler angles (rad):
        rx > 0 leans forward (-Y), ry > 0 tilts left (+X), rz > 0 turns left (+X)."""
        pb = self.arm.pose.bones

        def apply_rot(bname: str, w_rot: Matrix, w_head: Vector | None = None) -> None:
            b = pb[bname]
            rest3 = b.bone.matrix_local.to_3x3()
            m3 = w_rot @ rest3
            pos = w_head if w_head is not None else b.head
            m4 = m3.to_4x4()
            m4.translation = pos
            b.matrix = m4
            bpy.context.view_layer.update()

        r_pel = Euler(pelvis_rot, "XYZ").to_matrix()
        apply_rot("Pelvis", r_pel, Vector(pelvis_pos))

        r_sp = Euler(spine_add, "XYZ").to_matrix() @ r_pel
        apply_rot("Spine", r_sp)

        r_ch = Euler(chest_add, "XYZ").to_matrix() @ r_sp
        apply_rot("Chest", r_ch)

        if head_world_rot is not None:
            r_hd = Euler(head_world_rot, "XYZ").to_matrix()
        else:
            r_hd = Euler(head_add, "XYZ").to_matrix() @ r_ch
        r_nk = r_ch.to_quaternion().slerp(r_hd.to_quaternion(), 0.45).to_matrix()
        apply_rot("Neck", r_nk)
        apply_rot("Head", r_hd)

    def set_wheel_rig(
        self,
        pos: Tuple[float, float, float],
        rot_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        wheel_spin_rad: float = 0.0,
        rod_pitch_deg: float = 56.0,
    ) -> Matrix:
        root = self.wrig["root"]
        root.location = pos
        root.rotation_euler = tuple(math.radians(a) for a in rot_deg)
        self.wrig["rod_pivot"].rotation_euler = (math.radians(rod_pitch_deg), 0.0, 0.0)
        # Positive spin_rad around -X rolls forward (-Y)!
        self.wrig["wheel_L"].rotation_euler = (-wheel_spin_rad, 0.0, 0.0)
        self.wrig["wheel_R"].rotation_euler = (-wheel_spin_rad, 0.0, 0.0)
        bpy.context.view_layer.update()
        return root.matrix_world.copy()

    def grip_axle_hands(
        self,
        rig_mat: Matrix,
        grip_x: float = 0.135,
        elbow_out: float = 0.34,
        elbow_back: float = 0.28,
        elbow_up: float = 0.22,
    ) -> None:
        """Locks both green-gloved hands directly onto the steel axle bar at X = +-grip_x!"""
        for side, sx in (("R", -1.0), ("L", +1.0)):
            w_grip = rig_mat @ Vector((sx * grip_x, 0.024, -0.008))
            self.ik[f"hand_{side}"].location = w_grip
            self.ik[f"pole_arm_{side}"].location = rig_mat @ Vector((sx * elbow_out, elbow_back, elbow_up))
            # Curl fingers snugly around the axle bar!
            pb = self.arm.pose.bones
            pb[f"Index.{side}"].rotation_euler = (0.0, 0.0, sx * -1.15)
            pb[f"Fingers.{side}"].rotation_euler = (0.0, 0.0, sx * -1.25)
            pb[f"Thumb.{side}"].rotation_euler = (0.65, 0.0, sx * 0.45)

    def plant_feet_on_axle(self, rig_mat: Matrix, foot_x: float = 0.255, knee_spread: float = 0.44, knee_up: float = 0.46) -> None:
        """Perches green-socked feet right on the outer steel axle shafts with wide V-splayed knees (Photos 3 & 4)!"""
        for side, sx in (("R", -1.0), ("L", +1.0)):
            self.ik[f"foot_{side}"].location = rig_mat @ Vector((sx * foot_x, 0.035, 0.035))
            self.ik[f"pole_leg_{side}"].location = rig_mat @ Vector((sx * knee_spread, -0.08, knee_up))


# ---------------------------------------------------------------------------
# The 12 Animations
# ---------------------------------------------------------------------------

def pose_animation(ctx: RigContext, anim_id: str, t: float) -> None:
    """t in [0.0, 1.0) across one seamless loop (or one-shot sequence)."""
    ctx.reset_frame()
    ang = TAU * t
    pb = ctx.arm.pose.bones

    if anim_id == "seated_cruise":
        # Photo 4: Classic Seated Wheel-Cruise with cheeky smile & spinning pneumatic tires!
        gr.set_face_expression(ctx.mats, "smile")
        bob = 0.018 * math.sin(ang * 2.0)
        sway = 0.016 * math.sin(ang)
        rig_m = ctx.set_wheel_rig(
            pos=(sway, -0.18, R_TIRE),
            rot_deg=(2.5 * math.sin(ang * 2.0), 2.2 * math.sin(ang), -3.5 * math.cos(ang)),
            wheel_spin_rad=ang * 2.0,
            rod_pitch_deg=56.0 + 2.0 * math.sin(ang * 2.0),
        )
        ctx.pose_torso_chain(
            pelvis_pos=(sway * 0.8, +0.23, 0.165 + bob),
            pelvis_rot=(0.46, 0.04 * math.sin(ang), 0.0),
            spine_add=(0.24 + 0.04 * math.sin(ang * 2.0), 0.0, 0.0),
            chest_add=(0.16, 0.0, -0.05 * math.sin(ang)),
            head_world_rot=(0.06 + 0.03 * math.sin(ang * 2.0), 0.04 * math.sin(ang), -0.06 * math.cos(ang)),
        )
        ctx.grip_axle_hands(rig_m, grip_x=0.115, elbow_out=0.14, elbow_back=0.30, elbow_up=0.22)
        ctx.plant_feet_on_axle(rig_m, foot_x=0.260, knee_spread=0.52, knee_up=0.46 + 0.03 * math.sin(ang * 2.0))
        ctx.wrig["shadow"].location = (sway, 0.0, 0.001)
        ctx.wrig["shadow"].scale = (1.15, 0.95, 1.0)

    elif anim_id == "scream_turbo":
        # Photo 3: Intense Battle-Cry Overdrive + Bullet-Tip Grinding Sparks!
        gr.set_face_expression(ctx.mats, "scream")
        vib = 0.014 * math.sin(ang * 4.0)
        surge = 0.045 * math.sin(ang * 2.0)
        rig_m = ctx.set_wheel_rig(
            pos=(0.012 * math.cos(ang * 3.0), -0.20 - surge, R_TIRE),
            rot_deg=(3.0 * math.sin(ang * 4.0), 3.0 * math.cos(ang * 2.0), 0.0),
            wheel_spin_rad=ang * 4.0,
            rod_pitch_deg=55.5,
        )
        ctx.pose_torso_chain(
            pelvis_pos=(0.0, +0.21 - surge * 0.7, 0.165 + vib),
            pelvis_rot=(0.50, 0.0, 0.0),
            spine_add=(0.28 + 0.06 * math.sin(ang * 2.0), 0.0, 0.0),
            chest_add=(0.22, 0.0, 0.08 * math.sin(ang * 2.0)),
            head_world_rot=(0.14 + 0.04 * math.sin(ang * 4.0), 0.05 * math.sin(ang * 2.0), 0.0),
        )
        ctx.grip_axle_hands(rig_m, grip_x=0.115, elbow_out=0.15, elbow_back=0.28, elbow_up=0.24)
        ctx.plant_feet_on_axle(rig_m, foot_x=0.260, knee_spread=0.54, knee_up=0.48)

        # Shower of glowing golden 3D grinding sparks from the bullet tip on the floor!
        tip_world = ctx.wrig["rod_pivot"].matrix_world @ Vector((0.0, 0.0, -0.335))
        for i, sp in enumerate(ctx.vfx["sparks"][:12]):
            sp.hide_render = False
            ph = (t * 3.0 + i * 0.17) % 1.0
            vx = ((i % 5) - 2.0) * 0.16 + 0.05 * math.sin(i * 3.1 + ang)
            vy = 0.35 + (i % 3) * 0.18
            vz = 0.42 * ph - 0.55 * (ph * ph) + 0.06 * (i % 4)
            sp.location = (tip_world.x + vx * ph, tip_world.y + vy * ph, max(0.015, vz))
            sp.rotation_euler = (0.4, 0.0, math.atan2(vx, vy))
            sc_s = max(0.2, 1.15 * (1.0 - ph))
            sp.scale = (0.28 * sc_s, 2.6 * sc_s, 0.28 * sc_s)

    elif anim_id == "plank_rollout":
        # Photo 2: Full-Body Ab-Roller Plank Launch & Pike Recoil ('OOOO!' face)
        ext = 0.5 - 0.5 * math.cos(ang)  # 0 = compact pike, 1 = full super-extended plank!
        gr.set_face_expression(ctx.mats, "ooo" if ext > 0.30 else "scream")
        rig_y = -0.22 - 0.46 * ext
        rig_m = ctx.set_wheel_rig(
            pos=(0.0, rig_y, R_TIRE),
            rot_deg=(0.0, 0.0, 0.0),
            wheel_spin_rad=ext * 3.4,
            rod_pitch_deg=56.0,
        )
        hip_z = 0.68 - 0.34 * ext
        hip_y = +0.26 + 0.16 * ext
        lean_fwd = 1.12 + 0.32 * ext  # ~64° -> ~83° horizontal plank!
        ctx.pose_torso_chain(
            pelvis_pos=(0.0, hip_y, hip_z),
            pelvis_rot=(lean_fwd, 0.0, 0.0),
            spine_add=(0.08 * (1.0 - ext), 0.0, 0.0),
            chest_add=(-0.06 * ext, 0.0, 0.0),
            head_world_rot=(0.18, 0.0, 0.0),  # Looks forward at camera in shock!
        )
        ctx.grip_axle_hands(rig_m, grip_x=0.145, elbow_out=0.32, elbow_back=0.12, elbow_up=0.35)
        for side, sx in (("R", -1.0), ("L", +1.0)):
            ctx.ik[f"foot_{side}"].location = (sx * 0.13, +0.76 + 0.22 * ext, 0.055)
            ctx.ik[f"pole_leg_{side}"].location = (sx * 0.16, +0.42, 0.08)
        ctx.wrig["shadow"].location = (0.0, 0.12, 0.001)
        ctx.wrig["shadow"].scale = (0.95, 1.65, 1.0)

    elif anim_id == "hero_crane_point":
        # Photo 1: Standing on Right Leg, Left Knee Kicked Up High, Cradling Wheel Rig Across Chest,
        #          Left Arm Extended Skyward w/ Pointing Index Finger & 'OOOO!' Face!
        gr.set_face_expression(ctx.mats, "ooo")
        bob = 0.028 * math.sin(ang)
        kick_bob = 0.055 * math.sin(ang * 2.0)

        ctx.pose_torso_chain(
            pelvis_pos=(-0.04, 0.0, 0.88 + bob),
            pelvis_rot=(-0.06, -0.10, -0.18),
            spine_add=(0.0, -0.05, 0.06),
            chest_add=(-0.04, -0.06, 0.10),
            head_world_rot=(0.02, 0.04 * math.sin(ang), -0.14),
        )
        # Cradle wheel contraption diagonally across chest (top wheel behind right shoulder, bottom wheel near hip!)
        rig_m = ctx.set_wheel_rig(
            pos=(-0.06, -0.22, 1.16 + bob),
            rot_deg=(24.0, 48.0 + 4.0 * math.sin(ang), -18.0),
            wheel_spin_rad=ang,
            rod_pitch_deg=85.0,
        )
        # Right hand grips center axle/cylinder across chest
        ctx.ik["hand_R"].location = rig_m @ Vector((-0.02, -0.05, 0.02))
        ctx.ik["pole_arm_R"].location = (-0.48, +0.18, 1.12 + bob)
        pb["Index.R"].rotation_euler = (0.0, 0.0, 1.15)
        pb["Fingers.R"].rotation_euler = (0.0, 0.0, 1.25)

        # Left arm heroically extended up-left (+X, +Z) pointing index finger at the sky!
        pt_pulse = 0.045 * math.sin(ang * 2.0)
        ctx.ik["hand_L"].location = (+0.62 + pt_pulse, -0.14, 1.72 + bob + pt_pulse)
        ctx.ik["pole_arm_L"].location = (+0.35, +0.32, 1.32 + bob)
        # Pointing index straight (0), other 3 fingers curled!
        pb["Index.L"].rotation_euler = (0.0, 0.0, 0.0)
        pb["Fingers.L"].rotation_euler = (0.0, 0.0, -1.45)
        pb["Thumb.L"].rotation_euler = (0.55, 0.0, 0.55)

        # Plant right foot solidly on floor; kick left knee & flexed green foot up high!
        ctx.ik["foot_R"].location = (-0.06, 0.02, 0.055)
        ctx.ik["pole_leg_R"].location = (-0.10, -0.60, 0.48)
        ctx.ik["foot_L"].location = (+0.42, -0.14, 0.52 + kick_bob)
        ctx.ik["pole_leg_L"].location = (+0.38, -0.52, 0.92 + kick_bob * 0.6)
        ctx.wrig["shadow"].location = (-0.02, 0.0, 0.001)
        ctx.wrig["shadow"].scale = (0.85, 0.85, 1.0)

    elif anim_id == "overhead_press":
        # Heavy Olympic Barbell Squat-Clean & Overhead Lockout Press!
        # t=0..0.25 deep squat grab -> 0.25..0.55 explosive clean & press -> 0.55..0.75 overhead hold -> 0.75..1.0 lower
        if t < 0.25:
            u = t / 0.25
            lift = 0.0
            sq = math.sin(u * math.pi * 0.5)
            gr.set_face_expression(ctx.mats, "scream")
        elif t < 0.58:
            u = (t - 0.25) / 0.33
            s = u * u * (3.0 - 2.0 * u)
            lift = s
            sq = 1.0 - s
            gr.set_face_expression(ctx.mats, "scream")
        elif t < 0.76:
            u = (t - 0.58) / 0.18
            lift = 1.0 + 0.03 * math.sin(u * math.pi * 2.0)
            sq = 0.0
            gr.set_face_expression(ctx.mats, "smile")
        else:
            u = (t - 0.76) / 0.24
            s = u * u * (3.0 - 2.0 * u)
            lift = 1.0 - s
            sq = 0.35 * math.sin(u * math.pi)
            gr.set_face_expression(ctx.mats, "ooo")

        bar_z = R_TIRE + 1.66 * lift
        bar_y = -0.26 * (1.0 - lift) - 0.04 * lift
        rig_m = ctx.set_wheel_rig(
            pos=(0.0, bar_y, bar_z),
            rot_deg=(-35.0 * lift, 0.0, 0.0),
            wheel_spin_rad=lift * 4.5,
            rod_pitch_deg=56.0,
        )
        pel_z = 0.89 - 0.36 * sq
        lean = 0.45 * sq - 0.08 * lift
        ctx.pose_torso_chain(
            pelvis_pos=(0.0, +0.08 * sq, pel_z),
            pelvis_rot=(lean, 0.0, 0.0),
            spine_add=(0.16 * sq - 0.05 * lift, 0.0, 0.0),
            chest_add=(0.10 * sq - 0.05 * lift, 0.0, 0.0),
            head_world_rot=(-0.10 * lift, 0.0, 0.0),
        )
        ctx.grip_axle_hands(rig_m, grip_x=0.185, elbow_out=0.38, elbow_back=0.35, elbow_up=-0.18 if lift > 0.5 else 0.22)
        for side, sx in (("R", -1.0), ("L", +1.0)):
            ctx.ik[f"foot_{side}"].location = (sx * 0.19, 0.02, 0.055)
            ctx.ik[f"pole_leg_{side}"].location = (sx * 0.28, -0.62, 0.48)

    elif anim_id == "cyclone_spin":
        # 360° Helicopter Wheel-Barbell Tornado!
        gr.set_face_expression(ctx.mats, "scream")
        yaw = ang  # Full 360° body + barbell whirl!
        ca, sa = math.cos(yaw), math.sin(yaw)
        # Rig orbits forward of spinning chest at radius 0.34m
        rx_w = sa * 0.34
        ry_w = -ca * 0.34
        rig_m = ctx.set_wheel_rig(
            pos=(rx_w, ry_w, 0.96 + 0.04 * math.sin(ang * 2.0)),
            rot_deg=(12.0, 18.0 * math.sin(ang * 2.0), math.degrees(yaw)),
            wheel_spin_rad=ang * 3.0,
            rod_pitch_deg=90.0,
        )
        ctx.pose_torso_chain(
            pelvis_pos=(0.0, 0.0, 0.84 + 0.03 * math.sin(ang * 2.0)),
            pelvis_rot=(-0.14, 0.0, yaw),
            spine_add=(-0.06, 0.0, 0.0),
            chest_add=(-0.06, 0.0, 0.0),
            head_add=(0.08, 0.0, 0.0),
        )
        ctx.grip_axle_hands(rig_m, grip_x=0.16, elbow_out=0.36, elbow_back=0.28, elbow_up=0.10)
        for side, sx in (("R", -1.0), ("L", +1.0)):
            step_z = 0.055 + 0.06 * max(0.0, math.sin(ang * 2.0 + (0.0 if side == "L" else math.pi)))
            fx = sx * 0.16 * ca
            fy = sx * 0.16 * sa
            ctx.ik[f"foot_{side}"].location = (fx, fy, step_z)
            ctx.ik[f"pole_leg_{side}"].location = (fx + sa * 0.55, fy - ca * 0.55, 0.48)

        # Glowing neon-green & gold cyclone plasma rings!
        for ti, tr in enumerate(ctx.vfx["trails"][:4]):
            tr.hide_render = False
            tr.location = (0.0, 0.0, 0.72 + ti * 0.16)
            tr.rotation_euler = (0.12 * math.sin(ang + ti), 0.12 * math.cos(ang + ti), yaw + ti * 0.8)
            sc_t = 1.15 + 0.12 * math.sin(ang * 2.0 + ti)
            tr.scale = (sc_t, sc_t, 1.0)

    elif anim_id == "wheelie_backflip":
        # Seated Cruise -> Sparks Wheelie -> Full Mid-Air 360° Tucked Backflip -> Cushioned Landing!
        if t < 0.20:
            # Pop steep wheelie!
            u = t / 0.20
            pitch = -0.55 * math.sin(u * math.pi * 0.5)
            z_off = 0.06 * u
            gr.set_face_expression(ctx.mats, "ooo")
        elif t < 0.78:
            # Mid-air 360° backflip (-X pitch from -0.55 through -2*pi)!
            u = (t - 0.20) / 0.58
            arc = 4.0 * u * (1.0 - u)
            z_off = 0.06 + 0.92 * arc
            pitch = -0.55 - (TAU - 0.55) * (u * u * (3.0 - 2.0 * u))
            gr.set_face_expression(ctx.mats, "scream" if 0.2 < u < 0.8 else "ooo")
        else:
            # Stick the landing with suspension compression!
            u = (t - 0.78) / 0.22
            comp = math.sin(u * math.pi)
            z_off = -0.03 * comp
            pitch = 0.12 * comp
            gr.set_face_expression(ctx.mats, "smile")

        cm_y = 0.02
        cm_z = 0.36 + z_off
        rot_m = Euler((pitch, 0.0, 0.0), "XYZ").to_matrix().to_4x4()
        pivot = Matrix.Translation((0.0, cm_y, cm_z)) @ rot_m

        rig_world = pivot @ Matrix.Translation((0.0, -0.20, -0.17))
        rig_pos = rig_world.to_translation()
        rig_eul = rig_world.to_euler("XYZ")
        rig_m = ctx.set_wheel_rig(
            pos=(rig_pos.x, rig_pos.y, max(R_TIRE * 0.85, rig_pos.z)),
            rot_deg=tuple(math.degrees(a) for a in rig_eul),
            wheel_spin_rad=ang * 3.0,
            rod_pitch_deg=56.0,
        )

        pel_world = pivot @ Vector((0.0, +0.18, -0.19))
        ctx.pose_torso_chain(
            pelvis_pos=(pel_world.x, pel_world.y, max(0.12, pel_world.z)),
            pelvis_rot=(pitch + 0.48, 0.0, 0.0),
            spine_add=(0.26, 0.0, 0.0),
            chest_add=(0.18, 0.0, 0.0),
            head_add=(-0.22, 0.0, 0.0),
        )
        ctx.grip_axle_hands(rig_m, grip_x=0.130, elbow_out=0.32, elbow_back=0.22, elbow_up=0.28)
        ctx.plant_feet_on_axle(rig_m, foot_x=0.255, knee_spread=0.46, knee_up=0.46)
        sh_s = max(0.45, 1.15 - 0.45 * z_off)
        ctx.wrig["shadow"].scale = (sh_s, sh_s * 0.9, 1.0)

    elif anim_id == "bazooka_ram":
        # Full-Tilt Sprinting Chrome-Rod Battering-Ram / Rocket Joust!
        gr.set_face_expression(ctx.mats, "scream")
        bob = abs(math.sin(ang)) * 0.065
        ctx.pose_torso_chain(
            pelvis_pos=(0.0, 0.04, 0.84 + bob),
            pelvis_rot=(0.28, 0.0, 0.08 * math.sin(ang)),
            spine_add=(0.12, 0.0, -0.06 * math.sin(ang)),
            chest_add=(0.08, 0.0, -0.06 * math.sin(ang)),
            head_world_rot=(0.06, 0.0, 0.0),
        )
        # Aim bullet-tip stainless rod straight forward (-Y) like a rocket lance!
        joust = 0.06 * math.sin(ang * 2.0)
        rig_m = ctx.set_wheel_rig(
            pos=(0.0, -0.34 - joust, 0.96 + bob * 0.7),
            rot_deg=(34.0, 0.0, 0.0),  # rod_pitch=56 + 34 = 90° -> rod points dead horizontal along -Y!
            wheel_spin_rad=ang * 4.0,
            rod_pitch_deg=56.0,
        )
        ctx.grip_axle_hands(rig_m, grip_x=0.145, elbow_out=0.35, elbow_back=0.32, elbow_up=0.05)

        # Athletic 2-beat sprint stride!
        for side, sx, ph in (("L", +1.0, 0.0), ("R", -1.0, math.pi)):
            s = math.sin(ang + ph)
            c = math.cos(ang + ph)
            fy = -0.34 * s
            fz = 0.055 + 0.22 * max(0.0, c)
            ctx.ik[f"foot_{side}"].location = (sx * 0.12, fy, fz)
            ctx.ik[f"pole_leg_{side}"].location = (sx * 0.16, fy - 0.55, 0.52)

        # Rocket exhaust sparks behind him!
        for i, sp in enumerate(ctx.vfx["sparks"][:8]):
            sp.hide_render = False
            ph = (t * 2.0 + i * 0.13) % 1.0
            sp.location = (((i % 3) - 1) * 0.14, 0.25 + 0.65 * ph, 0.85 - 0.25 * ph)
            sp.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
            sp.scale = (0.3, 2.8 * (1.0 - ph * 0.6), 0.3)

    elif anim_id == "throw_boomerang":
        # Winds up deep, hurls 3D stainless wheel rig spinning forward like a boomerang, & catches it!
        if t < 0.22:
            # Windup twist
            u = t / 0.22
            gr.set_face_expression(ctx.mats, "scream")
            yaw = -0.65 * math.sin(u * math.pi * 0.5)
            ctx.pose_torso_chain(
                pelvis_pos=(0.0, 0.06, 0.83),
                pelvis_rot=(0.15, 0.0, yaw * 0.5),
                spine_add=(0.08, 0.0, yaw * 0.3),
                chest_add=(0.06, 0.0, yaw * 0.4),
                head_world_rot=(0.05, 0.0, 0.0),
            )
            rig_m = ctx.set_wheel_rig(
                pos=(-0.28 * u, +0.05 * u - 0.18, 0.96),
                rot_deg=(15.0, 0.0, math.degrees(yaw)),
                wheel_spin_rad=0.0,
            )
            ctx.grip_axle_hands(rig_m, grip_x=0.16)
        elif t < 0.82:
            # Boomerang flight out & back!
            u = (t - 0.22) / 0.60
            gr.set_face_expression(ctx.mats, "ooo")
            dist_out = math.sin(u * math.pi)
            spin_z = u * 720.0
            rig_y = -0.28 - 0.92 * dist_out
            rig_x = 0.28 * math.sin(u * TAU)
            rig_z = 0.98 + 0.18 * math.sin(u * math.pi)
            ctx.set_wheel_rig(
                pos=(rig_x, rig_y, rig_z),
                rot_deg=(72.0, 18.0 * math.cos(u * TAU), spin_z),
                wheel_spin_rad=u * TAU * 3.0,
                rod_pitch_deg=90.0,
            )
            rel = math.exp(-u * 5.0)
            catch = math.exp(-((1.0 - u) * 5.0))
            ctx.pose_torso_chain(
                pelvis_pos=(0.0, 0.02, 0.88),
                pelvis_rot=(0.22 * rel + 0.12 * catch, 0.0, 0.45 * rel),
                spine_add=(0.08 * rel, 0.0, 0.25 * rel),
                chest_add=(0.05, 0.0, 0.20 * rel),
                head_world_rot=(0.04, 0.0, 0.12 * math.sin(u * TAU)),
            )
            # Arms follow-through / reach forward in amazement!
            ctx.ik["hand_R"].location = (-0.22, -0.44 - 0.14 * rel, 1.24)
            ctx.ik["hand_L"].location = (+0.22, -0.44 - 0.14 * catch, 1.24)
            ctx.ik["pole_arm_R"].location = (-0.45, +0.20, 1.15)
            ctx.ik["pole_arm_L"].location = (+0.45, +0.20, 1.15)
        else:
            # Snatch catch recoil + grin!
            u = (t - 0.82) / 0.18
            rec = math.sin(u * math.pi)
            gr.set_face_expression(ctx.mats, "smile")
            ctx.pose_torso_chain(
                pelvis_pos=(0.0, +0.06 * rec, 0.88 - 0.06 * rec),
                pelvis_rot=(0.14 * rec, 0.0, 0.0),
                spine_add=(0.08 * rec, 0.0, 0.0),
                head_world_rot=(0.04, 0.0, 0.0),
            )
            rig_m = ctx.set_wheel_rig(pos=(0.0, -0.24 + 0.05 * rec, 0.94 - 0.04 * rec), wheel_spin_rad=(1.0 - u) * 2.0)
            ctx.grip_axle_hands(rig_m, grip_x=0.16)

        for side, sx in (("R", -1.0), ("L", +1.0)):
            ctx.ik[f"foot_{side}"].location = (sx * 0.16, 0.02 if side == "R" else -0.10, 0.055)
            ctx.ik[f"pole_leg_{side}"].location = (sx * 0.22, -0.60, 0.48)

    elif anim_id == "breakdance_flare":
        # Green-Suit B-Boy Axle Handstand V-Straddle Spin!
        gr.set_face_expression(ctx.mats, "smile")
        roll_x = 0.10 * math.sin(ang)
        rig_m = ctx.set_wheel_rig(
            pos=(roll_x, -0.06, R_TIRE),
            rot_deg=(0.0, 3.5 * math.sin(ang), 18.0 * math.cos(ang)),
            wheel_spin_rad=math.sin(ang) * 2.2,
            rod_pitch_deg=56.0,
        )
        # Inverted torso balanced over the axle!
        yaw_sw = 0.42 * math.sin(ang)
        ctx.pose_torso_chain(
            pelvis_pos=(roll_x, +0.04, 1.04 + 0.03 * math.sin(ang * 2.0)),
            pelvis_rot=(math.pi * 0.92, 0.12 * math.cos(ang), yaw_sw),
            spine_add=(-0.10, 0.0, 0.0),
            chest_add=(-0.12, 0.0, 0.0),
            head_world_rot=(0.22, 0.0, yaw_sw * 0.4),  # Head tilted up to smile right at camera!
        )
        ctx.grip_axle_hands(rig_m, grip_x=0.165, elbow_out=0.38, elbow_back=0.32, elbow_up=0.35)
        # Wide B-Boy V-straddle legs bicycling/flaring in the air!
        for side, sx, ph in (("L", +1.0, 0.0), ("R", -1.0, math.pi)):
            kick_y = 0.22 * math.sin(ang + ph)
            kick_z = 1.56 + 0.14 * math.cos(ang + ph)
            ctx.ik[f"foot_{side}"].location = (roll_x + sx * 0.52, kick_y, kick_z)
            ctx.ik[f"pole_leg_{side}"].location = (roll_x + sx * 0.35, -0.45, 1.25)

    elif anim_id == "victory_groove":
        # Electric Wheel-Guitar Shred & High Side-Kick Disco Groove!
        gr.set_face_expression(ctx.mats, "smile" if math.sin(ang * 2.0) >= -0.3 else "ooo")
        hip_sway = 0.09 * math.sin(ang)
        bob = abs(math.cos(ang)) * 0.045
        ctx.pose_torso_chain(
            pelvis_pos=(hip_sway, 0.0, 0.87 + bob),
            pelvis_rot=(-0.08, 0.12 * math.sin(ang), 0.16 * math.sin(ang)),
            spine_add=(0.0, -0.08 * math.sin(ang), -0.08 * math.sin(ang)),
            chest_add=(-0.05, -0.06 * math.sin(ang), 0.0),
            head_world_rot=(0.04 * math.sin(ang * 2.0), 0.10 * math.cos(ang), -0.08 * math.sin(ang)),
        )
        # Hold contraption diagonally across front like a double-wheel heavy-metal guitar!
        rig_m = ctx.set_wheel_rig(
            pos=(hip_sway * 0.5, -0.25, 1.02 + bob),
            rot_deg=(68.0, 32.0 + 6.0 * math.sin(ang * 2.0), 12.0 * math.sin(ang)),
            wheel_spin_rad=ang * 2.0,
            rod_pitch_deg=90.0,
        )
        # Left hand frets upper wheel axle; right hand strums central chrome cylinder!
        ctx.ik["hand_L"].location = rig_m @ Vector((+0.24, -0.04, 0.02))
        ctx.ik["pole_arm_L"].location = (+0.48, +0.22, 1.05)
        strum = 0.10 * math.sin(ang * 4.0)
        ctx.ik["hand_R"].location = rig_m @ Vector((-0.04, -0.08, strum))
        ctx.ik["pole_arm_R"].location = (-0.46, +0.22, 1.15)

        # Alternating funky side-taps / kicks!
        s_leg = math.sin(ang)
        if s_leg >= 0:
            ctx.ik["foot_R"].location = (-0.10, 0.02, 0.055)
            ctx.ik["foot_L"].location = (+0.26 + 0.18 * s_leg, -0.10, 0.055 + 0.24 * s_leg)
        else:
            k = -s_leg
            ctx.ik["foot_L"].location = (+0.10, 0.02, 0.055)
            ctx.ik["foot_R"].location = (-0.26 - 0.18 * k, -0.10, 0.055 + 0.24 * k)
        ctx.ik["pole_leg_L"].location = (+0.24, -0.60, 0.48)
        ctx.ik["pole_leg_R"].location = (-0.24, -0.60, 0.48)

    elif anim_id == "gib_explosion":
        # Act 1 (t < 0.28): Overload Swell & Tremor -> Act 2 (t >= 0.28): Quake Fireball + Flying Wheels & Chrome Rod!
        if t < 0.28:
            u = t / 0.28
            gr.set_face_expression(ctx.mats, "ooo" if u < 0.5 else "scream")
            jit = 0.035 * math.sin(u * 42.0) * u
            swell = 1.0 + 0.16 * (u * u)
            ctx.body.scale = (swell, swell, 1.0 + 0.06 * u)
            rig_m = ctx.set_wheel_rig(pos=(jit, -0.18, R_TIRE), wheel_spin_rad=u * 6.0)
            ctx.pose_torso_chain(
                pelvis_pos=(jit, +0.20, 0.17),
                pelvis_rot=(0.42, 0.0, 0.0),
                spine_add=(0.22, 0.0, 0.0),
                chest_add=(0.16, 0.0, 0.0),
                head_world_rot=(0.08, jit * 2.0, 0.0),
            )
            ctx.grip_axle_hands(rig_m, grip_x=0.13)
            ctx.plant_feet_on_axle(rig_m, foot_x=0.255)
            # Pre-detonation core glow!
            fl0 = ctx.vfx["flames"][0]
            fl0.hide_render = False
            fl0.location = (0.0, 0.0, 0.45)
            s_glow = 0.5 + 2.4 * (u ** 2)
            fl0.scale = (s_glow, s_glow, s_glow)
        else:
            u = (t - 0.28) / 0.72
            ctx.body.hide_render = True
            # Detached helmeted/hooded head launches spinning up & forward with 'OOOO!' shock!
            gr.set_face_expression(ctx.mats, "ooo")
            hz = max(0.11, 0.52 + 1.55 * u - 1.85 * (u * u))
            ctx.pose_torso_chain(
                pelvis_pos=(0.12 * u, -0.18 * u, hz - 1.52),
                pelvis_rot=(u * 5.2, u * 3.1, u * 4.4),
            )

            # Detach & launch Left Wheel, Right Wheel, and Chrome Rod outward in 3D with floor bounce!
            ctx.wrig["root"].location = (0.0, 0.0, 0.0)
            ctx.wrig["root"].rotation_euler = (0.0, 0.0, 0.0)
            ctx.wrig["axle"].hide_render = True

            def bounce_z(z0: float, vz: float, uu: float, r_min: float) -> float:
                z = z0 + vz * uu - 2.35 * (uu * uu)
                if z < r_min:
                    z = r_min + abs(z - r_min) * 0.48
                return z

            ctx.wrig["wheel_L"].location = (+0.38 + 0.85 * u, -0.25 * u, bounce_z(0.22, 1.65, u, R_TIRE))
            ctx.wrig["wheel_L"].rotation_euler = (u * 9.0, u * 5.0, u * 4.0)

            ctx.wrig["wheel_R"].location = (-0.38 - 0.82 * u, +0.22 * u, bounce_z(0.22, 1.50, u, R_TIRE))
            ctx.wrig["wheel_R"].rotation_euler = (-u * 8.5, -u * 4.5, u * 5.2)

            ctx.wrig["rod_pivot"].location = (-0.15 * u, -0.45 * u, bounce_z(0.32, 1.95, u, 0.08))
            ctx.wrig["rod_pivot"].rotation_euler = (1.0 + u * 11.0, u * 4.2, u * 3.5)

            # Fireball burst (peaks early, dissipates smoothly)
            if u < 0.62:
                fu = u / 0.62
                for fi, fl in enumerate(ctx.vfx["flames"]):
                    fl.hide_render = False
                    fa = fi * 2.39996
                    rad = (0.12 + 0.78 * fu) * (0.5 + 0.5 * ((fi % 4) / 3.0))
                    fl.location = (
                        math.cos(fa) * rad,
                        math.sin(fa) * rad,
                        0.38 + 0.55 * fu * math.sin(fi * 1.7) + 0.25 * fu,
                    )
                    fs = max(0.05, 1.85 * math.sin(fu * math.pi) * (1.0 - 0.04 * fi))
                    fl.scale = (fs, fs, fs)

            # Flying green morphsuit & Quake gib chunks!
            for gi, gb in enumerate(ctx.vfx["gibs"]):
                gb.hide_render = False
                ga = gi * 2.39996 + 0.4
                spd = 0.55 + 0.55 * ((gi % 5) / 4.0)
                vz = 1.35 + 0.75 * ((gi % 4) / 3.0)
                gb.location = (
                    math.cos(ga) * spd * u,
                    math.sin(ga) * spd * u,
                    bounce_z(0.42, vz, u, 0.05),
                )
                gb.rotation_euler = (u * (6.0 + gi), u * 4.0, ga)

            # Golden explosion sparks!
            for si, sp in enumerate(ctx.vfx["sparks"]):
                if u < 0.78:
                    sp.hide_render = False
                    sa = si * 1.95
                    sr = (0.2 + 1.35 * u) * (0.6 + 0.4 * (si % 3))
                    sp.location = (math.cos(sa) * sr, math.sin(sa) * sr, max(0.03, 0.48 + 1.1 * u - 1.9 * u * u + 0.1 * (si % 4)))
                    sp.rotation_euler = (0.3, 0.0, sa)
                    sc_sp = max(0.15, 1.3 * (1.0 - u / 0.78))
                    sp.scale = (0.32 * sc_sp, 2.8 * sc_sp, 0.32 * sc_sp)


# ---------------------------------------------------------------------------
# Animated .GLB Export (Seated Cruise Loop Baked cleanly for Real-Time WebGL!)
# ---------------------------------------------------------------------------

def export_showcase_glb(ctx: RigContext, out_path: str) -> None:
    """Exports a clean, lightweight, textured PBR .glb of Green-Suit Wheelman baked in his iconic
    Seated Wheel-Cruise pose (with separate WheelPivot_L/R nodes so WebGL2 spins the 3D tires live!)."""
    pose_animation(ctx, "seated_cruise", 0.0)
    gr.set_face_expression(ctx.mats, "smile")
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()

    # 1) Create glTF-native PBR materials (pure Principled BSDF + ImageTexture) for posed Body & Head!
    m_suit_glb = bpy.data.materials.new("MatGreenSuit_GLB")
    m_suit_glb.use_nodes = True
    bs_s = m_suit_glb.node_tree.nodes["Principled BSDF"]
    bs_s.inputs["Base Color"].default_value = gr.SUIT_LINEAR_COL
    bs_s.inputs["Metallic"].default_value = 0.0
    bs_s.inputs["Roughness"].default_value = 0.46

    m_head_glb = bpy.data.materials.new("MatHeadFace_GLB")
    m_head_glb.use_nodes = True
    hnt = m_head_glb.node_tree
    bs_h = hnt.nodes["Principled BSDF"]
    bs_h.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bs_h.inputs["Metallic"].default_value = 0.0
    bs_h.inputs["Roughness"].default_value = 0.48
    tex_node = hnt.nodes.new("ShaderNodeTexImage")
    head_glb_img_path = os.path.join(gr.TEX_DIR, "head_glb_smile.png")
    if not os.path.exists(head_glb_img_path):
        head_glb_img_path = os.path.join(gr.TEX_DIR, "face_smile.png")
    tex_node.image = bpy.data.images.load(head_glb_img_path, check_existing=True)
    hnt.links.new(tex_node.outputs["Color"], bs_h.inputs["Base Color"])

    # 2) Bake posed world-space Body & Head meshes onto temporary objects (preserving WheelRig hierarchy!)
    body_eval = ctx.body.evaluated_get(deps)
    posed_body_mesh = bpy.data.meshes.new_from_object(body_eval, preserve_all_data_layers=True, depsgraph=deps)
    posed_body_mesh.transform(ctx.body.matrix_world)
    posed_body_mesh.materials.clear()
    posed_body_mesh.materials.append(m_suit_glb)
    tmp_body = bpy.data.objects.new("GreenSuitBody_Posed", posed_body_mesh)
    ctx.sc.collection.objects.link(tmp_body)

    head_eval = ctx.head.evaluated_get(deps)
    posed_head_mesh = bpy.data.meshes.new_from_object(head_eval, preserve_all_data_layers=True, depsgraph=deps)
    posed_head_mesh.transform(ctx.head.matrix_world)
    uv_face = posed_head_mesh.uv_layers.get("UVFace")
    uv_fmask = posed_head_mesh.uv_layers.get("UVFrontMask")
    if uv_face is not None and uv_fmask is not None:
        for li in range(len(uv_face.data)):
            if uv_fmask.data[li].uv[0] < 0.5:
                uv_face.data[li].uv = (0.02, 0.98)
        posed_head_mesh.uv_layers.remove(uv_fmask)
        uv_face.active = True
        uv_face.active_render = True
    posed_head_mesh.materials.clear()
    posed_head_mesh.materials.append(m_head_glb)
    tmp_head = bpy.data.objects.new("GreenSuitHead_Posed", posed_head_mesh)
    ctx.sc.collection.objects.link(tmp_head)

    bpy.ops.object.select_all(action="DESELECT")
    export_objs = [tmp_body, tmp_head, ctx.wrig["root"]] + list(ctx.wrig["root"].children_recursive)
    for o in export_objs:
        o.hide_viewport = False
        o.select_set(True)
    bpy.context.view_layer.objects.active = tmp_body

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_texcoords=True,
        export_normals=True,
        export_skins=False,
        export_animations=False,
    )

    # Clean up temporary GLB baking objects so 1,200-frame sprite render is 100% unaffected!
    bpy.data.objects.remove(tmp_body, do_unlink=True)
    bpy.data.objects.remove(tmp_head, do_unlink=True)
    bpy.data.meshes.remove(posed_body_mesh)
    bpy.data.meshes.remove(posed_head_mesh)
    bpy.data.materials.remove(m_suit_glb)
    bpy.data.materials.remove(m_head_glb)
    print("Exported posed 3D GLB ->", out_path, f"({os.path.getsize(out_path) // 1024} KB)")


# ---------------------------------------------------------------------------
# Main Render Pipeline (Preview Mode vs. Full 1,200-Frame 360° Production Render)
# ---------------------------------------------------------------------------

def main() -> None:
    t_start = time.time()
    res = 440 if PREVIEW_MODE else 384
    sc, cam_rig, cam_obj = gr.setup_studio_scene(res_w=res, res_h=res, samples=16 if PREVIEW_MODE else 12)
    mats = gr.build_materials()
    arm_obj, body_obj, head_obj, ik_ctrl = gr.build_character_and_armature(sc, mats)
    wheel_rig = gr.build_stainless_wheel_rig(sc, mats)
    vfx = gr.build_vfx_pool(sc, mats)

    ctx = RigContext(sc, cam_rig, cam_obj, mats, arm_obj, body_obj, head_obj, ik_ctrl, wheel_rig, vfx)

    if PREVIEW_MODE:
        spec_map = {s["id"]: s["cam"] for s in ANIM_SPECS}
        previews = [
            ("01_seated_000",   "seated_cruise",    0.0,  0, spec_map["seated_cruise"]),
            ("02_seated_045",   "seated_cruise",    0.0,  1, spec_map["seated_cruise"]),
            ("03_seated_090",   "seated_cruise",    0.0,  2, spec_map["seated_cruise"]),
            ("04_seated_180",   "seated_cruise",    0.0,  4, spec_map["seated_cruise"]),
            ("05_scream_000",   "scream_turbo",     0.25, 0, spec_map["scream_turbo"]),
            ("06_plank_045",    "plank_rollout",    0.50, 1, spec_map["plank_rollout"]),
            ("07_crane_000",    "hero_crane_point", 0.25, 0, spec_map["hero_crane_point"]),
            ("08_press_000",    "overhead_press",   0.65, 0, spec_map["overhead_press"]),
            ("09_backflip_045", "wheelie_backflip", 0.48, 1, spec_map["wheelie_backflip"]),
            ("10_flare_000",    "breakdance_flare", 0.25, 0, spec_map["breakdance_flare"]),
            ("11_guitar_000",   "victory_groove",   0.25, 0, spec_map["victory_groove"]),
            ("12_explode_000",  "gib_explosion",    0.52, 0, spec_map["gib_explosion"]),
        ]
        for tag, aid, tf, d_idx, cam_cfg in previews:
            gr.set_camera_framing(cam_obj, *cam_cfg)
            cam_rig.rotation_euler = (0.0, 0.0, math.radians(d_idx * 45.0))
            pose_animation(ctx, aid, tf)
            bpy.context.view_layer.update()
            sc.render.filepath = os.path.join(PREV_DIR, f"{tag}.png")
            bpy.ops.render.render(write_still=True)
        export_showcase_glb(ctx, GLB_OUT)
        print(f"Preview 12 frames + GLB done in {time.time() - t_start:.1f}s -> {PREV_DIR}")
        return

    # Full 1,200-frame 8-angle 360° Sprite Render + GLB Export!
    export_showcase_glb(ctx, GLB_OUT)
    total_frames = sum(a["frames"] * 8 for a in ANIM_SPECS)
    done = 0
    for spec in ANIM_SPECS:
        aid = spec["id"]
        nf = spec["frames"]
        gr.set_camera_framing(cam_obj, *spec["cam"])
        anim_dir = os.path.join(OUT_RAW, aid)
        os.makedirs(anim_dir, exist_ok=True)
        t_anim = time.time()
        for fi in range(nf):
            tf = fi / float(nf)
            pose_animation(ctx, aid, tf)
            for d_idx in range(8):
                cam_rig.rotation_euler = (0.0, 0.0, math.radians(d_idx * 45.0))
                bpy.context.view_layer.update()
                sc.render.filepath = os.path.join(anim_dir, f"d{d_idx}_f{fi:02d}.png")
                bpy.ops.render.render(write_still=True)
                done += 1
        print(f"[{done}/{total_frames}] Rendered {aid} (8x{nf}) in {time.time() - t_anim:.1f}s", flush=True)

    with open(os.path.join(OUT_RAW, "manifest.json"), "w", encoding="utf-8") as fp:
        json.dump(ANIM_SPECS, fp, indent=2)
    print(f"ALL {total_frames} 3D SPRITE FRAMES RENDERED in {time.time() - t_start:.1f}s!")


if __name__ == "__main__":
    main()
