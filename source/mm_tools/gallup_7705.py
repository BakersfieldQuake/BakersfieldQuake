"""gallup_7705.py — Builds the 1:1 scale centerpiece **7705 Gallup Dr** (`sid=2410`) exterior
(from the 2026 GEMLS/CRMLS listing photo `img_011.jpg` + `img_016..018.jpg`), its walkable
1,250 sq ft honest listing-based interior & backyard, and its three immediate neighbors:
  - `7701` Gallup Dr (`sid=4942`, east neighbor at Deming Ct corner with arched-window garage,
    US flag, brick chimney, solar panels & turquoise swimming pool)
  - `7709` Gallup Dr (`sid=5804`, west neighbor with cream stucco & terracotta roof)
  - East Gallup / Rear Alley House (`sid=2372`, `img_035.jpg` sage stucco, swamp cooler,
    white chimney & weathered wood alley fence)
"""
import math

from gallup_lib import (
    Fit,
    cedar_tree,
    convex_parts,
    fence_line,
    fire_hydrant,
    hiproof,
    jump_pad,
    light,
    oasym_gable,
    obox,
    ogable,
    osloped_panel,
    palm_tree,
    prism,
    shade_tree,
    street_lamp,
    trash_bin,
    tspec,
    vis_core_box,
)

# Exact orientation of 7705 Gallup Dr (`sid=2410`):
# +V (`YAW = 111.9 deg`) points NNW toward Gallup Dr;
# +U (`YAW - 90 = 21.9 deg`) points ENE toward 7701 (Viewer's LEFT from Gallup Dr);
# -U (`YAW + 90 = 201.9 deg`) points WSW toward 7709 (Viewer's RIGHT from Gallup Dr).
YAW = 111.9
_RAD = math.radians(YAW)
_VX, _VY = math.cos(_RAD), math.sin(_RAD)
_UX, _UY = math.sin(_RAD), -math.cos(_RAD)


def wpt_7705(u_ft, v_ft):
    """Converts local `(u_ft, v_ft)` on 7705's lot into world `(x_ft, y_ft)`."""
    return (u_ft * _UX + v_ft * _VX, u_ft * _UY + v_ft * _VY)


def lbox(u0, u1, v0, v1, z0, z1, tex, faces=None, group="detail", solid=None):
    """Places an oriented box in 7705's local `(u, v, z)` coordinate frame."""
    if u1 < u0:
        u0, u1 = u1, u0
    if v1 < v0:
        v0, v1 = v1, v0
    uc, vc = (u0 + u1) * 0.5, (v0 + v1) * 0.5
    hu, hv = (u1 - u0) * 0.5, (v1 - v0) * 0.5
    cx, cy = wpt_7705(uc, vc)
    obox(cx, cy, z0, z1, hu, hv, YAW, tex, faces=faces, group=group, solid=solid)


def roof_z_7705(u_ft):
    """Exact height of the vaulted front roof bottom (`z_ceil`) at local `u_ft` (`u_peak = +0.9`)."""
    if u_ft >= 0.9:
        t = min(1.0, (u_ft - 0.9) / (15.9 - 0.9))
    else:
        t = min(1.0, (0.9 - u_ft) / (0.9 - (-16.9)))
    return 14.6 * (1.0 - t) + 8.9 * t


def build_7705_and_neighbors(by_sid):
    STUC_7705 = tspec("ga_stuc_7705", 8)
    WALL_INT = tspec("ga_wall_int", 8)
    TRIM_BRN = tspec("ga_trim_brn", 6)
    ROOF_7705 = tspec("ga_roof_7705", 8)
    FLOOR_WD = tspec("ga_floor_wd", 6)
    FLOOR_TL = tspec("ga_floor_tl", 6)
    BRICK_FP = tspec("ga_brick_fp", 5)
    CAB_OAK = tspec("ga_cab_oak", 4, 3)
    COUNTER = tspec("ga_counter", 4)
    CONC = tspec("sp_conc", 8)
    LAWN = tspec("sp_lawn", 12)
    DRYLAWN = tspec("sp_drylawn", 12)
    MULCH_RED = tspec("ga_mulch_red", 5)
    BLOCK_TAN = tspec("ga_block_tan", 8, 6)
    WOOD_FNC = tspec("ga_wood_fnc", 6, 6)
    HEDGE_GRN = tspec("ga_hedge_grn", 5, 5)

    # Mark hero SIDs handled so generic GIS builder skips them
    for s in (2410, 4942, 5804, 2372):
        by_sid["done"].add(s)

    # ==========================================================================
    # 1. 7705 GALLUP DR (`sid=2410`) — FRONT YARD, DRIVEWAY & CURB (`img_011.jpg`)
    # ==========================================================================
    # Concrete driveway on Viewer's LEFT (`u = +14.2 .. +34.5`, `v = +29.0 .. +63.6`) + walkway to entry
    lbox(14.2, 34.5, 28.8, 63.6, -0.05, 0.14, CONC, solid=False)
    lbox(-2.2, 14.4, 22.4, 29.4, -0.05, 0.16, CONC, solid=False)
    # Smooth sloped entry threshold (`z = 0.16 -> 0.42`) so players glide inside with zero step bump!
    lbox(-2.0, 3.6, 22.6, 25.6, 0.0, 0.30, CONC, solid=False)

    # Stenciled '7705' curb number on Gallup Dr vertical curb face right beside the driveway apron (`img_011.jpg`!)
    lbox(9.6, 13.4, 63.0, 63.85, 0.02, 0.40, CONC,
         faces={"front": Fit("ga_curb_7705")}, solid=False)

    # Lush emerald front lawn (`img_011.jpg`) + red-mulch foundation beds
    lbox(-16.5, 14.2, 29.4, 59.2, -0.05, 0.11, LAWN, solid=False)
    lbox(5.0, 14.4, 25.5, 29.3, -0.04, 0.13, MULCH_RED, solid=False)
    lbox(-15.8, -3.2, 25.5, 29.3, -0.04, 0.13, MULCH_RED, solid=False)

    # Left property-line tall lush hedge (`img_011.jpg` far left) + tucked tan bin + dual curb mailboxes (`img_016.jpg`)
    lbox(38.2, 41.2, 26.5, 58.2, 0.0, 8.4, HEDGE_GRN)
    lbox(34.5, 38.2, -4.5, 29.2, -0.04, 0.14, CONC, solid=False)  # Smooth side-yard breezeway path!
    tb_x, tb_y = wpt_7705(35.6, 29.8)
    trash_bin(tb_x, tb_y, YAW, col_tex="ga_stuc_tan")
    for mu, mcol in ((35.8, "ga_trim_brn"), (42.8, "ga_stuc_wht")):
        lbox(mu - 0.16, mu + 0.16, 59.8, 60.12, 0.0, 3.4, "ga_stuc_wht")
        lbox(mu - 0.42, mu + 0.42, 59.3, 60.8, 3.4, 4.15, mcol)

    # Foundation shrubs (`img_011.jpg`: square clipped boxwoods + potted agave under striped awning)
    lbox(7.4, 11.2, 26.1, 28.6, 0.12, 3.1, HEDGE_GRN)
    lbox(-4.8, -2.2, 25.9, 28.3, 0.12, 2.7, HEDGE_GRN)
    # Potted agave in dark planter pot beneath right awning (`img_011.jpg`)
    lbox(-12.2, -10.4, 26.2, 28.0, 0.12, 1.35, "ga_trim_brn")
    ag_x, ag_y = wpt_7705(-11.3, 27.1)
    for ayaw in (15, 75, 135):
        obox(ag_x, ag_y, 1.2, 3.4, 1.25, 0.05, ayaw, "{sp_invis",
             {"front": Fit("{ga_olive"), "back": Fit("{ga_olive")}, group="illus", solid=False)

    # Crimson/burgundy ornamental red-leaf tree on right side of front yard (`img_011.jpg`!)
    rl_x, rl_y = wpt_7705(-13.8, 30.8)
    shade_tree(rl_x, rl_y, h=15.8, r_crown=6.8, leaf_tex="{ga_redleaf", z_clear=4.8)

    # Curved concrete mow-strip + green boxwood hedge row along right edge of front lawn (`img_011.jpg`!)
    mow_pts = [wpt_7705(u_, v_) for u_, v_ in ((-14.8, 33.0), (-16.2, 39.5), (-18.4, 46.5), (-18.8, 53.5), (-16.0, 58.2))]
    fence_line(mow_pts, 0.0, 0.24, "sp_conc", thick=0.55, solid=False)
    for bu, bv in ((-15.2, 35.5), (-16.5, 40.5), (-17.8, 45.5), (-18.4, 50.5), (-17.5, 55.2)):
        lbox(bu - 1.4, bu + 1.4, bv - 2.1, bv + 2.1, 0.10, 2.6, HEDGE_GRN)

    # Tall California fan palm rising above the right/7709 roofline (`img_011.jpg` far right!)
    pm_x, pm_y = wpt_7705(-27.0, -10.0)
    palm_tree(pm_x, pm_y, h=42.0)

    # ==========================================================================
    # 2. 7705 ATTACHED 2-CAR GARAGE WING (Viewer's LEFT, `u = +14.8 .. +34.5`, `v = -0.5 .. +29.0`)
    # ==========================================================================
    # Solid garage structure + axial worldspawn VIS core inside garage!
    gar_poly = [wpt_7705(15.2, -0.5), wpt_7705(34.5, -0.5), wpt_7705(34.5, 29.0), wpt_7705(15.2, 29.0)]
    vis_core_box(gar_poly, 8.2, STUC_7705, margin=2.0)
    lbox(14.8, 34.5, -0.5, 28.4, 0.0, 8.8, STUC_7705)
    # Left & right front stucco piers + top lintel + recessed taupe-grey 8-window double garage door (`ga_gar_7705`)
    lbox(32.5, 34.5, 28.4, 29.1, 0.0, 8.8, STUC_7705)
    lbox(14.8, 16.8, 28.4, 29.1, 0.0, 8.8, STUC_7705)
    lbox(16.8, 32.5, 28.4, 29.1, 7.3, 8.8, STUC_7705)
    lbox(16.8, 32.5, 28.2, 28.75, 0.14, 7.3, STUC_7705, faces={"front": Fit("ga_gar_7705")})
    # Two black coach sconces flanking garage door (`img_011.jpg`)
    for su in (15.8, 33.5):
        lbox(su - 0.22, su + 0.22, 29.1, 29.45, 5.7, 6.75, TRIM_BRN, group="illus", solid=False)
    # Walkable hipped shingle roof over garage (`img_011.jpg`)
    hiproof(
        [wpt_7705(14.5, -1.0), wpt_7705(34.6, -1.0), wpt_7705(34.6, 29.2), wpt_7705(14.5, 29.2)],
        8.8, ROOF_7705, eave=1.15, pitch=4.2 / 12.0, fascia_tex=TRIM_BRN,
    )

    # ==========================================================================
    # 3. 7705 WALKABLE MAIN HOUSE (`u = -15.8 .. +18.2`, `v = -46.0 .. +25.5`)
    #    Exterior strictly from `img_011.jpg`; Interior strictly from MLS listing!
    # ==========================================================================
    # Warm wood floor slab + kitchen/bath tile zones
    lbox(-15.8, 18.2, -46.0, 25.5, 0.0, 0.42, FLOOR_WD, solid=False)
    lbox(3.6, 17.8, -8.0, 10.5, 0.02, 0.43, FLOOR_TL, solid=False)     # Kitchen tile
    lbox(3.6, 17.8, -31.6, -22.2, 0.02, 0.43, FLOOR_TL, solid=False)   # Hall bath tile
    lbox(5.0, 17.8, -38.4, -32.0, 0.02, 0.43, FLOOR_TL, solid=False)   # Primary bath tile

    # --- 3A. Front Asymmetric Vaulted Gable Facade (`v = +25.5`, `img_011.jpg`!) ---
    # Two crisp vertical light-stucco piers rising to the vaulted gable roof (`img_011.jpg`)!
    lbox(3.5, 5.1, 22.8, 26.2, 0.42, roof_z_7705(4.3), STUC_7705)
    lbox(-3.3, -1.7, 22.8, 26.2, 0.42, roof_z_7705(-2.5), STUC_7705)

    # Center recessed tall vaulted entry (`u = -1.7 .. +3.5`, `v = +22.8`):
    # Wide 4.8-ft open entry doorway (`z = 0.42 .. 7.2`) + swung-open dark espresso door leaf (`ga_door_7705`)
    # + arched clerestory window & '7705' transom (`ga_arch_7705`, `z = 7.2 .. 13.5`)!
    lbox(-1.7, 3.5, 22.6, 23.3, 7.2, 13.5, STUC_7705,
         faces={"front": Fit("ga_arch_7705"), "back": Fit("ga_arch_7705")})
    lbox(-1.7, 3.5, 22.6, 23.3, 13.5, 14.6, STUC_7705)
    # Swung-open entry door leaf (`group="illus"` so players never clip on it!)
    lbox(-1.65, -1.35, 18.2, 22.7, 0.42, 7.15, TRIM_BRN,
         faces={"right": Fit("ga_door_7705"), "left": Fit("ga_door_7705")}, group="illus", solid=False)

    # Left Front Bay (`u = +5.1 .. +14.8`, `v = +25.0 .. +25.6`):
    # Stucco lower wall + 3-pane bronze window (`ga_win_3p`) + dark-brown wood siding in gable!
    lbox(5.1, 14.8, 24.9, 25.6, 0.42, 3.2, STUC_7705)
    lbox(5.1, 6.2, 24.9, 25.6, 3.2, 6.8, STUC_7705)
    lbox(13.0, 14.8, 24.9, 25.6, 3.2, 6.8, STUC_7705)
    lbox(6.2, 13.0, 24.95, 25.55, 3.2, 6.8, WALL_INT,
         faces={"front": Fit("ga_win_3p"), "back": Fit("ga_win_3p")})
    # Flush dark-brown gable wood siding up to sloped roof (`z = 6.8 .. roof_z`, zero sky gaps!)
    for k in range(8):
        ua = 5.1 + k * (9.7 / 8.0)
        ub = ua + (9.7 / 8.0)
        zt = roof_z_7705(ub) + 0.56
        lbox(ua, ub, 24.9, 25.6, 6.8, zt, WALL_INT, faces={"front": TRIM_BRN})

    # Right Front Bay (`u = -15.8 .. -3.3`, `v = +25.0 .. +25.6`):
    # Stucco wall + 3-pane window + iconic Black-and-White Striped Awning (`ga_awning_bw` in `img_011.jpg`!)
    lbox(-15.8, -3.3, 24.9, 25.6, 0.42, 3.2, STUC_7705)
    lbox(-15.8, -13.2, 24.9, 25.6, 3.2, 6.7, STUC_7705)
    lbox(-5.2, -3.3, 24.9, 25.6, 3.2, 6.7, STUC_7705)
    lbox(-13.2, -5.2, 24.95, 25.55, 3.2, 6.7, WALL_INT,
         faces={"front": Fit("ga_win_3p"), "back": Fit("ga_win_3p")})
    for k in range(10):
        ua = -15.8 + k * 1.25
        ub = ua + 1.25
        zt = roof_z_7705(ua) + 0.56
        lbox(ua, ub, 24.9, 25.6, 6.7, zt, STUC_7705, faces={"back": WALL_INT})
    # Sloped black-and-white striped awning over right window (`img_011.jpg`!)
    aw_cx, aw_cy = wpt_7705(-9.2, 26.75)
    osloped_panel(aw_cx, aw_cy, 6.45, 7.75, 4.4, 1.15, YAW, Fit("ga_awning_bw"), thick=0.18,
                  edge_tex="ga_trim_brn", group="detail", solid=False)

    # --- 3B. Exterior Side & Rear Walls (`u = -15.8`, `u = +18.2`, `v = -46.0`) ---
    # West exterior wall (`u = -15.8 .. -15.1`, `v = -46.0 .. +25.5`)
    lbox(-15.8, -15.1, -46.0, 25.5, 0.42, 9.0, STUC_7705, faces={"right": WALL_INT})
    # East exterior wall (`u = +17.5 .. +18.2`, `v = -46.0 .. -0.5`; garage shares `v = -0.5 .. +25.5`)
    lbox(14.6, 15.3, -0.5, 25.5, 0.42, 9.0, WALL_INT)
    lbox(14.8, 18.2, -0.8, -0.1, 0.42, 9.0, STUC_7705, faces={"back": WALL_INT})
    lbox(17.5, 18.2, -46.0, -0.5, 0.42, 9.0, STUC_7705, faces={"left": WALL_INT})

    # Rear exterior wall (`v = -46.0 .. -45.3`) with wide 5.4-ft open Primary Suite patio door (`u = -8.2 .. -2.8`)!
    lbox(-15.8, -8.2, -46.0, -45.3, 0.42, 3.2, STUC_7705, faces={"front": WALL_INT})
    lbox(-15.8, -13.2, -46.0, -45.3, 3.2, 6.8, STUC_7705, faces={"front": WALL_INT})
    lbox(-13.2, -8.2, -45.95, -45.35, 3.2, 6.8, WALL_INT, faces={"back": Fit("ga_win_3p"), "front": Fit("ga_win_3p")})
    lbox(-15.8, -8.2, -46.0, -45.3, 6.8, 9.0, STUC_7705, faces={"front": WALL_INT})
    # Open Primary Suite patio doorway lintel (`u = -8.2 .. -2.8`, `z = 7.4 .. 9.0`)
    lbox(-8.2, -2.8, -46.0, -45.3, 7.4, 9.0, STUC_7705, faces={"front": WALL_INT})
    # Remainder of rear wall (`u = -2.8 .. +18.2`)
    lbox(-2.8, 18.2, -46.0, -45.3, 0.42, 9.0, STUC_7705, faces={"front": WALL_INT})

    # --- 3C. Honest Listing-Based Interior Partitions & Features ---
    # 1) Cozy 1983 Red-Brick Fireplace in Vaulted Living Room (`u = -15.1 .. -12.6`, `v = +8.5 .. +16.5`)
    #    + White Stucco Chimney rising above right roof slope (`img_011.jpg`!)
    lbox(-15.1, -11.8, 7.8, 17.2, 0.42, 1.35, BRICK_FP)     # Raised brick hearth
    lbox(-15.1, -12.7, 8.5, 10.6, 1.35, 5.2, BRICK_FP)      # Left fireplace pier
    lbox(-15.1, -12.7, 14.4, 16.5, 1.35, 5.2, BRICK_FP)     # Right fireplace pier
    lbox(-15.1, -14.2, 10.6, 14.4, 1.35, 5.2, TRIM_BRN)     # Dark firebox back
    lbox(-15.1, -12.7, 8.5, 16.5, 5.2, 9.4, BRICK_FP)       # Upper brick chimney breast
    lbox(-15.1, -12.2, 8.2, 16.8, 5.2, 5.55, TRIM_BRN, group="illus", solid=False)  # Wood mantel shelf
    fp_lx, fp_ly = wpt_7705(-13.2, 12.5)
    light(fp_lx, fp_ly, 2.6, 95, "255 155 70")
    # Exterior white stucco chimney above roof (`img_011.jpg`!)
    lbox(-15.4, -12.6, 10.2, 14.8, 8.6, 16.8, "ga_stuc_wht")
    lbox(-15.6, -12.4, 10.0, 15.0, 16.8, 17.2, TRIM_BRN, group="illus", solid=False)

    # 2) Open Kitchen (`u = +3.8 .. +17.5`, `v = -7.8 .. +10.5`) connected seamlessly to Dining Area (`v = +10.5 .. +24.8`):
    #    Ample oak cabinetry (`ga_cab_oak`) + laminate counters (`ga_counter`)!
    # Peninsula breakfast bar (`u = +5.2 .. +14.6`, `v = +9.2 .. +11.4`)
    lbox(5.2, 14.6, 9.2, 11.2, 0.42, 3.25, CAB_OAK)
    lbox(5.0, 14.8, 9.0, 11.5, 3.25, 3.45, COUNTER)
    # East wall counter + upper oak cabinets (`u = +12.4 .. +14.6`, `v = -7.4 .. +9.2`)
    lbox(12.4, 14.6, -7.4, 9.2, 0.42, 3.25, CAB_OAK)
    lbox(12.2, 14.6, -7.4, 9.2, 3.25, 3.45, COUNTER)
    lbox(13.2, 14.6, -7.4, 8.8, 5.6, 8.2, CAB_OAK, group="illus", solid=False)
    # Rear kitchen wall counter + upper oak cabinets (`u = +4.2 .. +14.6`, `v = -7.8 .. -5.6`)
    lbox(4.2, 12.4, -7.8, -5.6, 0.42, 3.25, CAB_OAK)
    lbox(4.2, 12.4, -7.8, -5.4, 3.25, 3.45, COUNTER)
    lbox(4.2, 13.2, -7.8, -6.4, 5.6, 8.2, CAB_OAK, group="illus", solid=False)

    # 3) Partition between Front Living/Kitchen and Rear Bedroom Zone (`v = -8.2 .. -7.6`),
    #    leaving a wide `5.6-ft` central hall archway (`u = -2.2 .. +3.4`)!
    lbox(-15.1, -2.2, -8.2, -7.6, 0.42, 9.0, WALL_INT)
    lbox(-2.2, 3.4, -8.2, -7.6, 7.6, 9.0, WALL_INT)
    lbox(3.4, 17.5, -8.2, -7.6, 0.42, 9.0, WALL_INT)
    # Exact flush triangular gable drop wall filling `z = 8.9 .. 14.8` at `v = -7.9` (zero stair-step sky gaps!)
    gw_cx, gw_cy = wpt_7705(0.0, -7.9)
    oasym_gable(gw_cx, gw_cy, 8.85, 14.85, -15.8, 0.9, 15.6, 0.45, YAW, WALL_INT, WALL_INT, eave=0.0, solid=False)

    # 4) Central Hallway (`u = -2.2 .. +3.4`, `v = -32.0 .. -8.2`) + Bedrooms 2 & 3 + Hall Bath:
    # West hall wall (`u = -2.8 .. -2.2`) with 4.6-ft doorway into Bedroom 3 (`v = -17.5 .. -12.9`)
    lbox(-2.8, -2.2, -12.9, -8.2, 0.42, 9.0, WALL_INT)
    lbox(-2.8, -2.2, -17.5, -12.9, 7.4, 9.0, WALL_INT)
    lbox(-2.8, -2.2, -32.0, -17.5, 0.42, 9.0, WALL_INT)
    # Partition inside West wing (`v = -22.5`, separating Bedroom 3 from Primary Suite)
    lbox(-15.1, -2.8, -32.0, -31.4, 0.42, 9.0, WALL_INT)

    # East hall wall (`u = +3.4 .. +4.0`) with doorways into Bedroom 2 (`v = -16.8 .. -12.2`) & Hall Bath (`v = -28.6 .. -24.0`)
    lbox(3.4, 4.0, -12.2, -8.2, 0.42, 9.0, WALL_INT)
    lbox(3.4, 4.0, -16.8, -12.2, 7.4, 9.0, WALL_INT)
    lbox(3.4, 4.0, -24.0, -16.8, 0.42, 9.0, WALL_INT)
    lbox(3.4, 4.0, -28.6, -24.0, 7.4, 9.0, WALL_INT)
    lbox(3.4, 4.0, -32.0, -28.6, 0.42, 9.0, WALL_INT)
    # Partition between Bedroom 2 and Hall Bath (`v = -22.2 .. -21.6`) + Hall Bath vanity
    lbox(4.0, 17.5, -22.2, -21.6, 0.42, 9.0, WALL_INT)
    lbox(8.5, 13.5, -22.6, -24.4, 0.42, 3.0, CAB_OAK)
    lbox(8.4, 13.6, -22.6, -24.5, 3.0, 3.2, COUNTER)

    # 5) Primary Suite (`v = -45.3 .. -32.0`):
    #    Hallway enters Primary Suite via wide `4.8-ft` doorway (`u = -2.2 .. +2.6`, `v = -32.0`)!
    lbox(-2.2, 2.6, -32.0, -31.4, 7.4, 9.0, WALL_INT)
    lbox(2.6, 17.5, -32.0, -31.4, 0.42, 9.0, WALL_INT)
    #    Walk-in Closet (`u = +5.2 .. +11.2`, `v = -45.3 .. -38.8`) + Private Bath (`u = +5.2 .. +17.5`, `v = -38.8 .. -32.0`)
    lbox(4.6, 5.2, -45.3, -43.2, 0.42, 9.0, WALL_INT)
    lbox(4.6, 5.2, -43.2, -39.2, 7.4, 9.0, WALL_INT)  # Closet doorway
    lbox(4.6, 5.2, -39.2, -37.2, 0.42, 9.0, WALL_INT)
    lbox(4.6, 5.2, -37.2, -33.0, 7.4, 9.0, WALL_INT)  # Private bath doorway
    lbox(4.6, 5.2, -33.0, -32.0, 0.42, 9.0, WALL_INT)
    lbox(5.2, 17.5, -39.0, -38.4, 0.42, 9.0, WALL_INT)
    # Primary bath oak vanity
    lbox(8.0, 13.8, -33.8, -32.0, 0.42, 3.0, CAB_OAK)
    lbox(7.9, 13.9, -33.9, -32.0, 3.0, 3.2, COUNTER)

    # --- 3D. True Vaulted Front Roof (`v = -8.5 .. +26.8`) & Walkable Rear Roof (`v = -46.8 .. -7.5`) ---
    # Front Left Vaulted Slope (`u = +0.9 .. +15.9`, `z = 14.6 -> 8.9`, `WALL_INT` ceiling below, `ROOF_7705` shingles above!)
    sl_lx, sl_ly = wpt_7705((0.9 + 15.9) * 0.5, (-8.5 + 26.8) * 0.5)
    osloped_panel(sl_lx, sl_ly, 8.9, 14.6, 35.3 * 0.5, 15.0 * 0.5, YAW - 90.0,
                  ROOF_7705, thick=0.65, edge_tex=WALL_INT, group="detail", solid=False)
    # Front Right Vaulted Slope (`u = -16.9 .. +0.9`, `z = 14.6 -> 8.9`)
    sl_rx, sl_ry = wpt_7705((-16.9 + 0.9) * 0.5, (-8.5 + 26.8) * 0.5)
    osloped_panel(sl_rx, sl_ry, 8.9, 14.6, 35.3 * 0.5, 17.8 * 0.5, YAW + 90.0,
                  ROOF_7705, thick=0.65, edge_tex=WALL_INT, group="detail", solid=False)
    # Dark-brown front gable rake fascia boards (`img_011.jpg` signature dark-brown roof trim!) + interior exposed ridge beam
    rk_lx, rk_ly = wpt_7705((0.9 + 15.9) * 0.5, 26.55)
    osloped_panel(rk_lx, rk_ly, 8.85, 14.65, 0.45, 15.0 * 0.5, YAW - 90.0,
                  TRIM_BRN, thick=0.72, edge_tex=TRIM_BRN, group="detail", solid=False)
    rk_rx, rk_ry = wpt_7705((-16.9 + 0.9) * 0.5, 26.55)
    osloped_panel(rk_rx, rk_ry, 8.85, 14.65, 0.45, 17.8 * 0.5, YAW + 90.0,
                  TRIM_BRN, thick=0.72, edge_tex=TRIM_BRN, group="detail", solid=False)
    lbox(0.55, 1.25, -7.8, 25.0, 14.1, 14.7, TRIM_BRN, group="illus", solid=False)

    # Rear Bedroom Wing ceiling (`z = 9.0 .. 9.4`) + walkable hipped shingle roof (`v = -46.2 .. -7.2`)
    lbox(-15.8, 18.2, -46.0, -7.6, 9.0, 9.45, WALL_INT, faces={"t": ROOF_7705}, solid=False)
    hiproof(
        [wpt_7705(-15.8, -46.0), wpt_7705(18.2, -46.0), wpt_7705(18.2, -7.2), wpt_7705(-15.8, -7.2)],
        9.45, ROOF_7705, eave=1.2, pitch=4.4 / 12.0, fascia_tex=TRIM_BRN,
    )

    # Warm inviting interior lights across all rooms of 7705 Gallup Dr!
    for lu, lv, lz, lval in (
        (-6.0, 12.0, 11.2, 165),   # Vaulted Living Room
        (9.2, 16.5, 10.5, 150),    # Dining Area
        (9.2, 1.5, 10.2, 155),     # Open Kitchen
        (0.6, -20.0, 8.2, 130),    # Central Hall
        (-8.8, -14.0, 8.2, 130),   # Bedroom 3
        (10.5, -15.0, 8.2, 130),   # Bedroom 2
        (10.5, -27.0, 8.2, 115),   # Hall Bath
        (-5.5, -38.5, 8.2, 150),   # Primary Suite
        (11.5, -35.2, 8.2, 115),   # Primary Bath
    ):
        lx, ly = wpt_7705(lu, lv)
        light(lx, ly, lz, lval, "255 244 222")

    # ==========================================================================
    # 4. 7705 BACKYARD (`v = -84.0 .. -46.0`): PATIO, FEB 2025 CARRIER HVAC & MATURE TREES
    # ==========================================================================
    # Backyard lawn pad + generous concrete patio slab + smooth threshold ramp into Primary Suite
    lbox(-16.5, 35.0, -84.0, -46.0, -0.05, 0.10, LAWN, solid=False)
    lbox(-14.5, 17.5, -60.5, -46.0, -0.04, 0.18, CONC, solid=False)
    lbox(-8.4, -2.6, -48.5, -45.8, 0.0, 0.30, CONC, solid=False)
    # Side-yard concrete walkway along east side (`u = +18.2 .. +25.0`, `v = -46.0 .. -0.5`) + open breezeway gate!
    lbox(18.2, 24.5, -46.0, -0.5, -0.04, 0.14, CONC, solid=False)
    # Brand-new Feb 2025 Carrier HVAC condenser (`ga_hvac`) on concrete equipment pad (`u = +18.6 .. +21.6, v = -24.0 .. -21.0`)!
    lbox(18.4, 21.8, -24.4, -20.6, 0.10, 0.32, CONC, solid=False)
    lbox(18.7, 21.5, -24.1, -20.9, 0.32, 3.25, "ga_hvac")

    # Backyard privacy walls (`6.0 ft` slump-stone & wood fence), leaving an open 4.5-ft side gate at `u = +35.0, v = -4.5 .. 0`!
    by_pts_w = [wpt_7705(-16.5, 25.0), wpt_7705(-16.5, -84.0), wpt_7705(38.2, -84.0), wpt_7705(38.2, -5.0)]
    fence_line(by_pts_w, 0.0, 6.0, "ga_block_tan", thick=0.45)

    # Mature backyard shade trees rising behind 7705's roof (`img_011.jpg` background!)
    for tu, tv, th in ((-7.0, -72.0, 34.0), (18.0, -70.0, 32.0)):
        tx, ty = wpt_7705(tu, tv)
        shade_tree(tx, ty, h=th, r_crown=11.5, leaf_tex="{sp_leaf", z_clear=10.0)

    # ==========================================================================
    # 5. IMMEDIATE NEIGHBORS: `7701` (`sid=4942`), `7709` (`sid=5804`), & ALLEY HOUSE (`sid=2372`)
    # ==========================================================================
    # --- 5A. `7701` East Neighbor (SW Corner of Gallup Dr & Deming Ct, `sid=4942`, `img_016.jpg`, `img_058.jpg`) ---
    yaw_7701 = 114.5
    rad_01 = math.radians(yaw_7701)
    vx1, vy1 = math.cos(rad_01), math.sin(rad_01)
    ux1, uy1 = math.sin(rad_01), -math.cos(rad_01)

    def p01(uu, vv):
        return (63.0 + uu * ux1 + vv * vx1, 25.0 + uu * uy1 + vv * vy1)

    # Corner patchy summer lawn (`img_058.jpg`) + concrete driveway to Gallup Dr (`img_016.jpg`)
    obox(*p01(14.0, 18.0), -0.04, 0.11, 22.0, 22.0, yaw_7701, DRYLAWN, solid=False)
    obox(*p01(-12.5, 36.0), -0.04, 0.15, 9.5, 15.5, yaw_7701, CONC, solid=False)

    # Main house volume + axial VIS core + white-siding front garage wing (`ga_gar_7701` with 8 arched fanlight windows!)
    vis_core_box([p01(-22, -16), p01(18, -16), p01(18, 16), p01(-22, 16)], 8.4, "ga_stuc_wht", margin=2.0)
    obox(*p01(-2.0, 0.0), 0.0, 9.2, 20.5, 16.5, yaw_7701, tspec("ga_stuc_wht", 8),
         faces={"right": Fit("ga_win_wht", (2.0, 1.0))})
    hiproof([p01(-22.5, -16.5), p01(18.5, -16.5), p01(18.5, 16.5), p01(-22.5, 16.5)],
            9.2, tspec("ga_roof_drk", 8), eave=1.1, pitch=4.4 / 12.0, fascia_tex="ga_siding_wht")
    # Projecting white-siding garage wing (`u = -22.5 .. -2.5`, `v = +4.0 .. +21.5`)
    obox(*p01(-12.5, 12.8), 0.0, 9.0, 10.0, 8.8, yaw_7701, tspec("ga_siding_wht", 6),
         faces={"front": Fit("ga_gar_7701")})
    ogable(*p01(-12.5, 12.8), 9.0, 13.0, 10.0, 8.8, yaw_7701, tspec("ga_roof_drk", 8), tspec("ga_siding_wht", 6), eave=1.0)
    # Blue rollout bin tucked beside right garage pier (`img_016.jpg`), US flag (`img_058.jpg`), & red-brick chimney!
    trash_bin(*p01(-23.8, 19.5), yaw_7701, col_tex="sp_bin_blu")
    obox(*p01(1.5, 18.2), 4.8, 8.2, 0.06, 1.8, yaw_7701, "{sp_invis",
         {"right": Fit("{sp_usflag"), "left": Fit("{sp_usflag")}, group="illus", solid=False)
    obox(*p01(18.8, 2.0), 0.0, 15.2, 1.8, 2.2, yaw_7701, BRICK_FP)
    # Rooftop solar array (`sp_solar`) on 7701's rear slope
    osloped_panel(*p01(-2.0, -8.5), 9.8, 12.2, 8.5, 3.8, yaw_7701 + 180.0, Fit("sp_solar", (2.0, 1.0)))
    # Corner white fire hydrant + decorative post-top street lamp (`img_058.jpg`!) + backyard palms
    fire_hydrant(86.5, 96.5)
    street_lamp(80.5, 101.0, arm_yaw=115.0, h=16.0, cobra=False)
    palm_tree(*p01(8.0, -28.0), h=38.0)

    # 7701 Enclosed Backyard + Sparkling Turquoise Swimming Pool (`ga_pool_wtr`, fun jump-pad splash target!)
    pool_cx, pool_cy = p01(-4.0, -34.0)
    obox(pool_cx, pool_cy, -0.05, 0.16, 16.0, 11.0, yaw_7701, CONC, solid=False)
    obox(pool_cx, pool_cy, 0.16, 0.38, 11.5, 7.2, yaw_7701, "ga_pool_wtr", solid=False)
    fence_line([p01(18.5, -2.0), p01(24.0, -18.0), p01(16.0, -50.0), p01(-24.0, -50.0)], 0.0, 5.8, "ga_block_tan", thick=0.45)

    # --- 5B. `7709` West Neighbor (`sid=5804`, `cx=-53.6, cy=-29.7`, `img_011.jpg` right edge!) ---
    yaw_7709 = 110.5
    rad_09 = math.radians(yaw_7709)
    vx9, vy9 = math.cos(rad_09), math.sin(rad_09)
    ux9, uy9 = math.sin(rad_09), -math.cos(rad_09)

    def p09(uu, vv):
        return (-53.6 + uu * ux9 + vv * vx9, -29.7 + uu * uy9 + vv * vy9)

    vis_core_box([p09(-22, -18), p09(22, -18), p09(22, 18), p09(-22, 18)], 8.4, "ga_stuc_crm", margin=2.0)
    # Warm cream stucco body + dark-brown gable bay above right window + terracotta-brown roof (`img_011.jpg` right!)
    obox(*p09(0.0, 0.0), 0.0, 9.0, 23.0, 19.0, yaw_7709, tspec("ga_stuc_crm", 8))
    obox(*p09(11.0, 19.1), 2.8, 6.6, 5.2, 0.35, yaw_7709, "ga_stuc_crm", faces={"front": Fit("ga_win_3p")})
    obox(*p09(11.0, 19.05), 6.6, 9.2, 5.2, 0.35, yaw_7709, TRIM_BRN)
    obox(*p09(-10.5, 19.1), 0.14, 7.3, 8.0, 0.35, yaw_7709, "ga_stuc_crm", faces={"front": Fit("ga_gar_7705")})
    obox(*p09(-11.0, 35.0), -0.04, 0.14, 9.2, 16.0, yaw_7709, CONC, solid=False)
    ogable(*p09(0.0, 0.0), 9.0, 14.0, 23.0, 19.0, yaw_7709, tspec("ga_roof_terra", 8), tspec("ga_stuc_crm", 8), eave=1.2)
    # White stucco chimney at left eave (`img_011.jpg` right!)
    obox(*p09(22.2, 12.0), 0.0, 15.2, 1.5, 1.8, yaw_7709, "ga_stuc_wht")

    # --- 5C. East Gallup / Rear Alley House (`sid=2372`, `cx=185.0, cy=136.3`, `img_035.jpg`!) ---
    b2372 = by_sid["map"].get(2372, [None])[0]
    if b2372:
        pts_a = b2372["pts"]
        for part in convex_parts(pts_a):
            vis_core_box(part, 8.4, "ga_stuc_sage", margin=2.0)
            prism(part, 0.0, 9.2, tspec("ga_roof_gry", 8), side=tspec("ga_stuc_sage", 8), group="detail", solid=True)
            hiproof(part, 9.2, tspec("ga_roof_gry", 8), eave=1.15, pitch=4.6 / 12.0, fascia_tex="ga_stuc_wht")
        # Rooftop swamp cooler + white stucco chimney + rear windows facing alley (`img_035.jpg`!)
        obox(184.0, 138.0, 11.8, 14.6, 1.6, 1.6, 42.0, "sp_cooler")
        obox(198.5, 154.5, 0.0, 14.2, 1.6, 1.8, 42.0, "ga_stuc_wht")
        obox(191.5, 158.0, 3.0, 6.4, 4.8, 0.35, 42.0, "ga_stuc_sage", faces={"front": Fit("ga_win_wht", (2.0, 1.0))})
        # Weathered vertical wood-plank fence along the rear service alley (`img_035.jpg`!)
        fence_line([(228.0, 142.0), (204.0, 178.0), (178.0, 198.0), (150.0, 168.0)], 0.0, 5.8, WOOD_FNC, thick=0.30)

    # ==========================================================================
    # 6. TACTICAL JUMP PADS AROUND 7705 GALLUP DR & POOL!
    # ==========================================================================
    # Pad A: 7705 Driveway Apron -> Vaulted Gable Roof Ridge of 7705!
    drv_px, drv_py = wpt_7705(28.5, 46.0)
    rf7705_x, rf7705_y = wpt_7705(1.0, 8.0)
    jump_pad(drv_px, drv_py, 0.14, target=(rf7705_x, rf7705_y, 15.6), over=14.0, size=5.6)

    # Pad B: 7705 Backyard Patio -> Splash/Vault over block wall straight onto 7701's Pool Deck / Roof!
    byp_x, byp_y = wpt_7705(13.0, -56.0)
    jump_pad(byp_x, byp_y, 0.18, target=(pool_cx, pool_cy, 1.2), over=18.0, size=5.4)

    # Pad C: 7701 Poolside -> 7705 Vaulted Roof Ridge (fast loop back over the hedge!)
    pl_pad_x, pl_pad_y = p01(6.5, -24.0)
    jump_pad(pl_pad_x, pl_pad_y, 0.16, target=(rf7705_x, rf7705_y, 15.6), over=16.0, size=5.4)

    return {
        "pool": (pool_cx, pool_cy),
        "roof_7705": (rf7705_x, rf7705_y, 15.6),
    }
