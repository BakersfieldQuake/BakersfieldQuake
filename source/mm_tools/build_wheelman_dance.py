"""Build progs/wheelman_dance.spr32 with all 8 crazy post-crash 360-degree Wheelman animations
(skipping the unwanted 2D explosion sprite) at 176x176 (wcannon.qc WC_Dancer, scale 0.393):
  0..79    run_stuck      0 + d * 10 + k   (8 views x 10)
  80..159  run_overhead   80 + d * 10 + k  (8 views x 10)
  160..255 dance          160 + d * 12 + k (8 views x 12)
  256..335 hands_up_kick  256 + d * 10 + k (8 views x 10)
  336..431 spin_bar       336 + d * 12 + k (8 views x 12)
  432..527 weightlift     432 + d * 12 + k (8 views x 12)
  528..623 throw_rig      528 + d * 12 + k (8 views x 12)
  624..735 turn_robot     624 + d * 14 + k (8 views x 14)

python3.13 build_wheelman_dance.py"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ACT_DIR = os.path.join(HERE, "wheelman_actions")
if ACT_DIR not in sys.path:
    sys.path.insert(0, ACT_DIR)

import wheelman_actions_core as core
import wheelman_extra_anims as extra
import build_wheelman_actions as act

DST = r"G:\Quake\Combat\BakersfieldQuake\progs\wheelman_dance.spr32"
N = 176


def main():
    skin_samples, grain_hi = core.load_authentic_skin_ref()
    print("[1/8] run_stuck (8x10)...")
    f_run = act.build_anim_1_running(skin_samples, grain_hi)
    print("[2/8] run_overhead (8x10)...")
    f_run_oh = extra.build_anim_6_run_overhead(act.load_cleaned_bare_plate, skin_samples, grain_hi)
    print("[3/8] dance (8x12)...")
    f_dance = act.build_anim_5_dance(skin_samples, grain_hi)
    print("[4/8] hands_up_kick (8x10)...")
    f_hands = act.build_anim_2_hands_up_kick(skin_samples, grain_hi)
    print("[5/8] spin_bar (8x12)...")
    f_spin = extra.build_anim_7_spin_around(act.load_cleaned_bare_plate, skin_samples, grain_hi)
    print("[6/8] weightlift (8x12)...")
    f_lift = act.build_anim_3_weightlift(skin_samples, grain_hi)
    print("[7/8] throw_rig (8x12)...")
    f_throw = act.build_anim_4_throw(skin_samples, grain_hi)
    print("[8/8] turn_robot (8x14)...")
    f_robot = extra.build_anim_9_turn_into_robot(f_run)

    banks = [f_run, f_run_oh, f_dance, f_hands, f_spin, f_lift, f_throw, f_robot]
    out = []
    for bank in banks:
        for d in range(8):
            for im in bank[d]:
                toned = core.tone_for_darkplaces(im)
                out.append(toned.resize((N, N), Image.LANCZOS))

    oy = round(core.GROUND_Y * N / 360.0)
    core.write_spr32(DST, out, ground_y=oy)


if __name__ == "__main__":
    main()
