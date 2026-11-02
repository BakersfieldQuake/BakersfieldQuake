"""spruce_3003_interior.py — Full 1:1 walkable interior & backyard of 3003 Spruce St ("David Ojeda" house)
built from the 15 Zillow MLS reference photos (img2_032.jpg .. img2_046.jpg) + Dec 2011 Street View (img2_023.jpg):
  - Carpeted Living & Dining Room (vertical-blind picture window, sheer curtains, 'HELLO / GOODBYE' doormat, ceiling fan, fireplace mass)
  - Galley Kitchen & Breakfast Nook (wood-plank floor, white arched cabinets, granite counters, grey subway tile, double sink,
    5-burner gas stove, LG stainless microwave, blue-and-white tile square, tall pantry, fluorescent ceiling light)
  - Central Vestibule (upper cabinets, wrought-iron marble bench, open tan 3-panel door)
  - 3 Carpeted Bedrooms (twin blind windows, sheer curtains, 5-blade ceiling fans, marble/iron bench)
  - Turquoise Bathroom (bright turquoise walls, wood vanity & mirror, wood-blind window, niche, white toilet, tub & coastal starfish shower curtain)
  - Backyard Concrete Patio, Detached Tan-Stucco Outbuilding/Garage (sid=2891), Rustic Wood Shed & Privacy Fences!
"""
import math
from spruce_lib import (
    Fit,
    brush_vehicle,
    ceiling_fan,
    frustum_ring,
    hiproof,
    light,
    obox,
    ogable,
    road_ribbon,
    trash_bin,
    tspec,
)


def build_3003_house(by_sid, stage=3):
    CONC = tspec("sp_conc", 8)
    c3_x, c3_y, c3_yaw = -57.5, -230.3, 322.0
    r3 = math.radians(c3_yaw)
    v3x, v3y = math.cos(r3), math.sin(r3)       # +V = SE (Front toward Spruce St), -V = NW (Rear toward Backyard)
    u3x, u3y = -math.sin(r3), math.cos(r3)      # +U = NE (Viewer's left-to-right when facing 3003 from Spruce St!)

    def wpt(du, dv):
        return (c3_x + du * u3x + dv * v3x, c3_y + du * u3y + dv * v3y)

    def hbox(u1, u2, v1, v2, z1, z2, tex, se=None, nw=None, ne=None, sw=None, t=None, b=None, group="detail", solid=True):
        """Local box in 3003's coordinates:
        u1..u2 = SW(-21) -> NE(+21), v1..v2 = NW(-16) -> SE(+16), z1..z2 = vertical feet.
        """
        if u2 < u1:
            u1, u2 = u2, u1
        if v2 < v1:
            v1, v2 = v2, v1
        um, vm = 0.5 * (u1 + u2), 0.5 * (v1 + v2)
        hu, hv = 0.5 * (u2 - u1), 0.5 * (v2 - v1)
        wx, wy = wpt(um, vm)
        faces = {}
        if se is not None:
            faces["front"] = se
        if nw is not None:
            faces["back"] = nw
        if ne is not None:
            faces["left"] = ne      # In obox, (-ux, -uy) = +u3 (NE)!
        if sw is not None:
            faces["right"] = sw     # In obox, (+ux, +uy) = -u3 (SW)!
        if t is not None:
            faces["t"] = t
        if b is not None:
            faces["b"] = b
        obox(wx, wy, z1, z2, hu, hv, c3_yaw, tex, faces=faces, group=group, solid=solid)

    def wall_with_openings_v(v1, v2, u_min, u_max, z_bot, z_top, openings, base_tex, se=None, nw=None):
        """Builds a wall along U (`v1..v2`) pierced by clean 3D rectangular door/window openings `(ou1, ou2, oz1, oz2)`."""
        ops = sorted(openings, key=lambda o: o[0])
        cur = u_min
        for ou1, ou2, oz1, oz2 in ops:
            if ou1 > cur + 0.05:
                hbox(cur, ou1, v1, v2, z_bot, z_top, base_tex, se=se, nw=nw)
            if oz1 > z_bot + 0.05:
                hbox(ou1, ou2, v1, v2, z_bot, oz1, base_tex, se=se, nw=nw)
            if z_top > oz2 + 0.05:
                hbox(ou1, ou2, v1, v2, oz2, z_top, base_tex, se=se, nw=nw)
            cur = ou2
        if u_max > cur + 0.05:
            hbox(cur, u_max, v1, v2, z_bot, z_top, base_tex, se=se, nw=nw)

    def wall_with_openings_u(u1, u2, v_min, v_max, z_bot, z_top, openings, base_tex, ne=None, sw=None):
        """Builds a wall along V (`u1..u2`) pierced by clean 3D rectangular door/window openings `(ov1, ov2, oz1, oz2)`."""
        ops = sorted(openings, key=lambda o: o[0])
        cur = v_min
        for ov1, ov2, oz1, oz2 in ops:
            if ov1 > cur + 0.05:
                hbox(u1, u2, cur, ov1, z_bot, z_top, base_tex, ne=ne, sw=sw)
            if oz1 > z_bot + 0.05:
                hbox(u1, u2, ov1, ov2, z_bot, oz1, base_tex, ne=ne, sw=sw)
            if z_top > oz2 + 0.05:
                hbox(u1, u2, ov1, ov2, oz2, z_top, base_tex, ne=ne, sw=sw)
            cur = ov2
        if v_max > cur + 0.05:
            hbox(u1, u2, cur, v_max, z_bot, z_top, base_tex, ne=ne, sw=sw)

    stuc = tspec("sp_stuc_crm", 10)
    roof = tspec("sp_roof_brn", 8)
    w_liv = tspec("sp_wall_liv", 8)
    w_kit = tspec("sp_wall_kit", 8)
    w_trq = tspec("sp_wall_turq", 8)
    ceil_t = tspec("sp_ceil_wht", 10)
    carp = tspec("sp_carpet", 5)
    wflr = tspec("sp_woodflr", 5)
    btil = tspec("sp_bathtile", 4)
    trim_w = tspec("sp_stuc_wht", 4)

    ZF = 1.35   # Walkable interior floor height (top of 4 front red steps & 3 rear concrete steps!)
    ZC = 9.35   # Interior ceiling height (8.0 ft = 96 Quake units!)

    # ==========================================================================
    # 1. FOUNDATION / ROOM FLOORS, CEILING SLAB & HIPPED ROOF + CHIMNEY
    # ==========================================================================
    # Carpeted Living/Dining & Bedrooms (`sp_carpet`)
    hbox(-21.0, 21.0, -0.8, 16.0, 0.04, ZF, stuc, t=carp)                 # Front half: Bedroom 3 + Living/Dining
    hbox(-21.0, -11.4, -16.0, -0.8, 0.04, ZF, stuc, t=carp)               # SW Rear: Bedroom 2
    hbox(-11.4, -2.8, -6.2, -0.8, 0.04, ZF, stuc, t=carp)                 # Inner Hallway
    hbox(-2.8, 4.4, -16.0, -0.8, 0.04, ZF, stuc, t=carp)                  # Rear Center: Bedroom 1
    # Turquoise Bathroom ceramic tile floor (`sp_bathtile`, img2_042)
    hbox(-11.4, -2.8, -16.0, -6.2, 0.04, ZF, stuc, t=btil)
    # Galley Kitchen, Breakfast Nook & Central Vestibule wood-plank floor (`sp_woodflr`, img2_032..036)
    hbox(4.4, 21.0, -16.0, -0.8, 0.04, ZF, stuc, t=wflr)

    # Full white plaster ceiling slab (`z = 9.35 .. 9.58`) + outer eave collar + brown hipped roof (`z0 = 9.88 -> 9.88-0.35 = 9.53 > 9.35` so ceiling stays crisp white!)
    hbox(-21.0, 21.0, -16.0, 16.0, ZC, 9.58, stuc, b=ceil_t)
    hbox(-21.0, 21.0, 15.4, 16.0, ZC, 9.56, stuc)
    hbox(-21.0, 21.0, -16.0, -15.4, ZC, 9.56, stuc)
    hbox(-21.0, -20.4, -15.4, 15.4, ZC, 9.56, stuc)
    hbox(20.4, 21.0, -15.4, 15.4, ZC, 9.56, stuc)
    roof_pts = [wpt(-21.0, -16.0), wpt(-21.0, 16.0), wpt(21.0, 16.0), wpt(21.0, -16.0)]
    hiproof(roof_pts, 9.88, roof, eave=1.6, pitch=4.8 / 12.0, fascia_tex="sp_trim_grn")

    # Tall cream-stucco chimney rising above front-left fireplace + rooftop swamp cooler (`img2_023`, `img2_044`)
    hbox(-4.8, -2.5, 7.2, 9.5, 9.55, 19.4, stuc)
    hbox(-10.2, -6.6, -4.8, -1.2, 13.4, 16.8, "sp_cooler", solid=False)

    # ==========================================================================
    # 2. EXTERIOR WALLS WITH REAL 3D DOORWAYS, WINDOWS, BLINDS & SHEER CURTAINS
    # ==========================================================================
    # --- SE FRONT WALL (`v = 15.4 .. 16.0`, facing Spruce St, `img2_023`, `037`, `044`) ---
    # Split at `u = -7.8` so Bedroom 3 gets tan interior & Living Room gets greige interior
    wall_with_openings_v(15.4, 16.0, -21.0, -7.8, ZF, ZC,
                         [(-15.6, -11.4, 3.6, 7.7)], stuc, se=stuc, nw=w_liv)
    wall_with_openings_v(15.4, 16.0, -7.8, 21.0, ZF, ZC, [
        (-5.8, 3.2, 2.5, 7.9),     # Wide Living Room vertical-blind picture window (img2_037!)
        (4.3, 8.5, ZF, 8.35),      # Walkable Front Doorway (4.2 ft = 50.4u wide!)
        (12.2, 16.6, 3.4, 7.8),    # Front-right Dining window w/ sheer curtain (img2_037/038!)
    ], stuc, se=stuc, nw=w_liv)

    # Window panes (dark exterior glass outside, bright vertical/horizontal blinds inside!)
    hbox(-15.6, -11.4, 15.55, 15.88, 3.6, 7.7, trim_w, se=Fit("sp_win_dark"), nw=Fit("sp_hblinds"))
    hbox(-5.8, 3.2, 15.55, 15.88, 2.5, 7.9, trim_w, se=Fit("sp_win_pic"), nw=Fit("sp_vblinds"))
    hbox(12.2, 16.6, 15.55, 15.88, 3.4, 7.8, trim_w, se=Fit("sp_win_dark"), nw=Fit("sp_hblinds"))
    hbox(11.8, 17.0, 15.22, 15.32, 1.5, 8.1, "{sp_invis", nw=Fit("{sp_sheer"), group="fence", solid=False)

    # Open 6-panel Front Door swung inward (`sp_door_3003` / `sp_door_wht`) + 'HELLO / GOODBYE' doormat + '3003' fascia plaque + mailbox!
    hbox(8.52, 8.74, 11.8, 15.35, ZF + 0.02, 8.25, trim_w, sw=Fit("sp_door_wht"), ne=Fit("sp_door_3003"), solid=False)
    hbox(4.6, 8.2, 13.0, 15.1, ZF, ZF + 0.05, "sp_doormat", t=Fit("sp_doormat"), solid=False)
    hbox(5.2, 7.6, 17.56, 17.70, 9.52, 9.90, "sp_trim_grn", se=Fit("sp_num3003"), solid=False)
    hbox(8.9, 10.0, 16.02, 16.22, 4.4, 5.0, "sp_rollup", solid=False)

    # --- NE SIDE WALL (`u = 20.4 .. 21.0`, Dining room + Galley Kitchen sink wall, `img2_032..038`) ---
    wall_with_openings_u(20.4, 21.0, -0.8, 15.4, ZF, ZC,
                         [(3.6, 11.6, 3.0, 7.9)], stuc, ne=stuc, sw=w_liv)
    wall_with_openings_u(20.4, 21.0, -16.0, -0.8, ZF, ZC, [
        (-13.8, -10.4, 3.4, 7.8),  # Breakfast nook NE sheer window (img2_034 right)
        (-7.4, -4.2, 4.5, 7.8),    # Galley Kitchen over-sink window (img2_032, 034!)
    ], stuc, ne=stuc, sw=w_kit)
    hbox(20.55, 20.88, 3.6, 11.6, 3.0, 7.9, trim_w, ne=Fit("sp_win_whtw"), sw=Fit("sp_hblinds"))
    hbox(20.18, 20.28, 3.2, 12.0, 1.5, 8.1, "{sp_invis", sw=Fit("{sp_sheer", (2.0, 1.0)), group="fence", solid=False)
    hbox(20.55, 20.88, -7.4, -4.2, 4.5, 7.8, trim_w, ne=Fit("sp_win_wht"), sw=Fit("sp_hblinds"))
    hbox(20.55, 20.88, -13.8, -10.4, 3.4, 7.8, trim_w, ne=Fit("sp_win_wht"), sw=Fit("sp_hblinds"))
    hbox(20.18, 20.28, -14.0, -10.2, 1.5, 8.0, "{sp_invis", sw=Fit("{sp_sheer"), group="fence", solid=False)

    # --- NW REAR WALL (`v = -16.0 .. -15.4`, facing Backyard, 1:1 with `img2_046`!) ---
    # Kitchen section (`u = 4.4 .. 20.4`): Breakfast sheer window + Walkable Rear Kitchen Door!
    wall_with_openings_v(-16.0, -15.4, 4.4, 20.4, ZF, ZC, [
        (9.5, 13.7, ZF, 8.25),     # Walkable Rear Kitchen Doorway (4.2 ft = 50.4u wide!)
        (14.5, 18.3, 3.4, 7.8),    # Rear Kitchen sheer-curtain window (img2_033, 034!)
    ], stuc, nw=stuc, se=w_kit)
    # Bedroom 1 section (`u = -2.8 .. 4.4`): Twin side-by-side windows (`img2_039` & `img2_046`!)
    wall_with_openings_v(-16.0, -15.4, -2.8, 4.4, ZF, ZC, [
        (-2.1, 0.5, 3.5, 7.8),
        (1.0, 3.6, 3.5, 7.8),
    ], stuc, nw=stuc, se=w_liv)
    # Turquoise Bathroom section (`u = -11.4 .. -2.8`): Smaller wood-blind window (`img2_042` & `img2_046`!)
    wall_with_openings_v(-16.0, -15.4, -11.4, -2.8, ZF, ZC, [
        (-8.4, -5.8, 4.2, 7.8),
    ], stuc, nw=stuc, se=w_trq)
    # Bedroom 2 section (`u = -21.0 .. -11.4`): Rear bedroom window (`img2_041` & `img2_046`!)
    wall_with_openings_v(-16.0, -15.4, -21.0, -11.4, ZF, ZC, [
        (-17.8, -13.6, 3.5, 7.8),
    ], stuc, nw=stuc, se=w_liv)

    hbox(14.5, 18.3, -15.88, -15.55, 3.4, 7.8, trim_w, nw=Fit("sp_win_dark"), se=Fit("sp_hblinds"))
    hbox(14.2, 18.6, -15.32, -15.22, 1.5, 8.0, "{sp_invis", se=Fit("{sp_sheer"), group="fence", solid=False)
    # Open white Rear Kitchen Door swung inward (`u = 9.35`)
    hbox(9.28, 9.48, -15.35, -12.0, ZF + 0.02, 8.15, trim_w, ne=Fit("sp_door_wht"), sw=Fit("sp_door_wht"), solid=False)
    hbox(-2.1, 0.5, -15.88, -15.55, 3.5, 7.8, trim_w, nw=Fit("sp_win_dark"), se=Fit("sp_hblinds"))
    hbox(1.0, 3.6, -15.88, -15.55, 3.5, 7.8, trim_w, nw=Fit("sp_win_dark"), se=Fit("sp_hblinds"))
    hbox(-8.4, -5.8, -15.88, -15.55, 4.2, 7.8, trim_w, nw=Fit("sp_win_dark"), se=Fit("sp_wblinds"))
    hbox(-17.8, -13.6, -15.88, -15.55, 3.5, 7.8, trim_w, nw=Fit("sp_win_dark"), se=Fit("sp_hblinds"))
    hbox(-18.1, -13.3, -15.32, -15.22, 1.5, 8.0, "{sp_invis", se=Fit("{sp_sheer"), group="fence", solid=False)

    # --- SW SIDE WALL (`u = -21.0 .. -20.4`, Bedroom 2 & Bedroom 3 side windows, `img2_040`, `041`) ---
    wall_with_openings_u(-21.0, -20.4, -15.4, 15.4, ZF, ZC, [
        (-12.2, -8.0, 3.5, 7.8),   # Bedroom 2 SW blind window (img2_041 right)
        (4.0, 8.4, 3.5, 7.8),      # Bedroom 3 SW sheer window (img2_040 left)
    ], stuc, sw=stuc, ne=w_liv)
    hbox(-20.88, -20.55, -12.2, -8.0, 3.5, 7.8, trim_w, sw=Fit("sp_win_dark"), ne=Fit("sp_hblinds"))
    hbox(-20.88, -20.55, 4.0, 8.4, 3.5, 7.8, trim_w, sw=Fit("sp_win_dark"), ne=Fit("sp_hblinds"))
    hbox(-20.32, -20.22, 3.7, 8.7, 1.5, 8.0, "{sp_invis", ne=Fit("{sp_sheer"), group="fence", solid=False)

    # ==========================================================================
    # 3. INTERIOR PARTITIONS & WALKABLE DOORWAYS (ALL >= 4.2 ft = 50u WIDE!)
    # ==========================================================================
    # Main E-W Spine Wall (`v = -1.2 .. -0.8`) separating Front Rooms from Kitchen / Inner Hall:
    #   - Doorway 1 (`u = -7.3 .. -3.0`):  Living Room <-> Inner Hallway
    #   - Doorway 2 (`u = 12.4 .. 16.7`):  Dining/Living Room <-> Galley Kitchen (`img2_032` & `038`!)
    wall_with_openings_v(-1.2, -0.8, -20.4, 8.8, ZF, ZC, [
        (-7.3, -3.0, ZF, 8.35),
    ], w_liv, se=w_liv, nw=w_liv)
    wall_with_openings_v(-1.2, -0.8, 8.8, 20.4, ZF, ZC, [
        (12.4, 16.7, ZF, 8.35),
    ], w_kit, se=w_liv, nw=w_kit)
    # Crisp white casing around Kitchen <-> Living Room doorway (`img2_032`!)
    hbox(12.15, 12.4, -1.25, -0.75, ZF, 8.5, trim_w, solid=False)
    hbox(16.7, 16.95, -1.25, -0.75, ZF, 8.5, trim_w, solid=False)
    hbox(12.15, 16.95, -1.25, -0.75, 8.35, 8.55, trim_w, solid=False)

    # Living Room <-> Bedroom 3 partition (`u = -7.8 .. -7.4, v = -0.8 .. 15.4`) w/ walkable Bedroom 3 doorway (`v = -0.4 .. 3.9`) + Fireplace under chimney!
    wall_with_openings_u(-7.8, -7.4, -0.8, 15.4, ZF, ZC, [
        (-0.4, 3.9, ZF, 8.30),
    ], w_liv, ne=w_liv, sw=w_liv)
    hbox(-7.4, -2.6, 4.6, 10.0, ZF, ZC, w_liv)

    # Galley Kitchen West Wall (`u = 8.4 .. 8.8, v = -15.4 .. -0.8`) w/ wide opening to Central Vestibule (`v = -14.9 .. -10.1`, `img2_036`)
    wall_with_openings_u(8.4, 8.8, -15.4, -0.8, ZF, ZC, [
        (-14.9, -10.1, ZF, 8.35),
    ], w_kit, ne=w_kit, sw=w_kit)
    # Shallow recessed white linen/ironing-board cabinet door on Kitchen/Vestibule corner (`img2_034`, `036`!)
    hbox(8.78, 8.88, -10.0, -9.0, 2.6, 7.6, trim_w, ne=Fit("sp_cab_wht"), solid=False)

    # Closet mass between Kitchen West Wall & Bedroom 1 (`u = 4.4 .. 8.4, v = -9.6 .. -1.2`)
    hbox(4.4, 8.4, -9.6, -1.2, ZF, ZC, w_liv, ne=w_kit, nw=w_kit)
    # Vestibule <-> Bedroom 1 Wall (`u = 4.1 .. 4.5, v = -15.4 .. -9.6`) w/ open doorway + ajar tan 3-panel door (`img2_036`, `039`!)
    wall_with_openings_u(4.1, 4.5, -15.4, -9.6, ZF, ZC, [
        (-14.0, -9.7, ZF, 8.25),
    ], w_liv, ne=w_kit, sw=w_liv)
    hbox(4.52, 4.72, -9.7, -6.9, ZF + 0.02, 8.15, trim_w, ne=Fit("sp_door_tan"), sw=Fit("sp_door_tan"), solid=False)

    # Bedroom 1 <-> Bathroom & Inner Hall Wall (`u = -2.8 .. -2.4, v = -15.4 .. -1.2`) w/ open Hallway doorway (`v = -5.6 .. -1.4`)
    wall_with_openings_u(-2.8, -2.4, -15.4, -6.2, ZF, ZC, [], w_liv, ne=w_liv, sw=w_trq)
    wall_with_openings_u(-2.8, -2.4, -6.2, -1.2, ZF, ZC, [
        (-5.6, -1.4, ZF, 8.30),
    ], w_liv, ne=w_liv, sw=w_liv)

    # Inner Hallway <-> Turquoise Bathroom Wall (`v = -6.4 .. -6.0, u = -11.4 .. -2.8`) w/ open Bathroom doorway (`u = -9.2 .. -5.0`)
    wall_with_openings_v(-6.4, -6.0, -11.4, -2.8, ZF, ZC, [
        (-9.2, -5.0, ZF, 8.25),
    ], w_trq, se=w_liv, nw=w_trq)

    # Inner Hallway / Bathroom <-> Bedroom 2 Wall (`u = -11.8 .. -11.4, v = -15.4 .. -1.2`) w/ open Bedroom 2 doorway (`v = -5.6 .. -1.4`)
    wall_with_openings_u(-11.8, -11.4, -15.4, -6.2, ZF, ZC, [], w_liv, ne=w_trq, sw=w_liv)
    wall_with_openings_u(-11.8, -11.4, -6.2, -1.2, ZF, ZC, [
        (-5.6, -1.4, ZF, 8.30),
    ], w_liv, ne=w_liv, sw=w_liv)

    # ==========================================================================
    # 4. GALLEY KITCHEN CABINETS, GRANITE, SINK, GAS STOVE & LG MICROWAVE (`img2_032..036`)
    # ==========================================================================
    cab = Fit("sp_cab_wht", (2.0, 1.0))
    gran = tspec("sp_granite", 3)
    sub = tspec("sp_subtile", 3)

    # East (`+u`) Sink Run (`u = 18.2 .. 20.4, v = -10.2 .. -1.4`)
    hbox(18.3, 20.4, -10.2, -1.4, ZF, 4.15, trim_w, sw=Fit("sp_cab_wht", (4.0, 1.0)))
    hbox(18.15, 20.4, -10.3, -7.2, 4.15, 4.32, gran)
    hbox(18.15, 20.4, -7.2, -4.4, 4.15, 4.32, gran, t=Fit("sp_sink_top"))
    hbox(18.15, 20.4, -4.4, -1.35, 4.15, 4.32, gran)
    # Chrome gooseneck sink faucet + grey subway-tile backsplash (`sp_subtile`) + potted plant (`img2_032` left!)
    hbox(19.95, 20.15, -5.9, -5.7, 4.32, 5.05, "sp_wt_tank", solid=False)
    hbox(19.45, 20.05, -5.9, -5.7, 4.95, 5.10, "sp_wt_tank", solid=False)
    hbox(20.28, 20.4, -10.2, -1.4, 4.32, 5.85, sub)
    hbox(18.9, 20.4, -10.2, -7.4, 5.85, 8.85, trim_w, sw=cab)
    hbox(18.9, 20.4, -4.2, -1.4, 5.85, 8.85, trim_w, sw=cab)
    hbox(19.2, 20.4, -7.4, -4.2, 7.80, 8.85, trim_w, sw=Fit("sp_cab_wht", (2.0, 0.5)))
    hbox(18.5, 19.3, -10.0, -9.2, 4.32, 4.85, trim_w, solid=False)
    hbox(18.35, 19.45, -10.15, -9.05, 4.85, 5.65, tspec("sp_hedge", 2), solid=False)

    # West (`-u`) Gas Stove, LG Microwave, Blue-Tile Accent & Tall White Pantry (`u = 8.8 .. 11.0`, `img2_032, 033, 036`)
    hbox(8.8, 10.9, -4.0, -1.4, ZF, 4.15, trim_w, ne=cab)
    hbox(8.8, 11.05, -4.0, -1.35, 4.15, 4.32, gran)
    hbox(8.8, 8.92, -4.0, -1.4, 4.32, 5.85, sub)
    # 5-Burner Gas Stove / Oven (`v = -6.7 .. -4.0`) + Blue-and-white tile square (`sp_bluetile`) + LG Microwave (`sp_micro`)
    hbox(8.85, 11.05, -6.7, -4.0, ZF, 4.34, "sp_rollup", ne=Fit("sp_stove_fr"), t=Fit("sp_stove_tp"))
    hbox(8.8, 8.92, -6.75, -3.6, 4.34, 5.65, Fit("sp_bluetile"), ne=Fit("sp_bluetile"), solid=False)
    hbox(8.8, 10.45, -6.7, -4.0, 5.65, 7.05, "sp_wt_tank", ne=Fit("sp_micro"))
    hbox(8.8, 10.3, -6.7, -4.0, 7.05, 8.85, trim_w, ne=Fit("sp_cab_wht", (2.0, 0.6)))
    hbox(8.8, 10.3, -4.0, -1.4, 5.85, 8.85, trim_w, ne=cab)
    # Tall White Pantry Cabinet (`v = -9.6 .. -6.8`, `img2_032, 033, 036`)
    hbox(8.8, 11.0, -9.6, -6.8, ZF, 8.85, trim_w, ne=Fit("sp_cab_wht", (1.0, 2.0)), nw=Fit("sp_cab_wht", (1.0, 2.0)))

    # Kitchen Fluorescent Ceiling Light (`sp_fluor`, `img2_032`) + Vestibule Cabinets & Wrought-Iron Marble Bench (`img2_036`)
    hbox(13.6, 15.6, -7.8, -3.2, 9.16, ZC, "sp_fluor", b=Fit("sp_fluor"), solid=False)
    hbox(4.6, 8.4, -15.35, -14.1, 6.25, 8.85, trim_w, se=Fit("sp_cab_wht", (2.0, 1.0)))
    hbox(5.2, 8.0, -15.3, -14.25, 2.75, 2.95, tspec("sp_stuc_tan", 3), solid=True)     # Bench marble top
    hbox(5.3, 5.5, -15.2, -14.3, ZF, 2.75, "sp_rollup", solid=False)
    hbox(7.7, 7.9, -15.2, -14.3, ZF, 2.75, "sp_rollup", solid=False)

    # Bedroom 1 Wrought-Iron & Marble Bench beneath twin NW windows (`img2_039` left!)
    hbox(-1.6, 2.4, -15.2, -13.8, 2.65, 2.85, tspec("sp_stuc_tan", 3), solid=True)
    hbox(-1.5, -1.3, -15.1, -13.9, ZF, 2.65, "sp_rollup", solid=False)
    hbox(2.1, 2.3, -15.1, -13.9, ZF, 2.65, "sp_rollup", solid=False)

    # ==========================================================================
    # 5. TURQUOISE BATHROOM FIXTURES (`img2_042`: Vanity, Mirror, Niche, Toilet, Tub & Starfish Curtain!)
    # ==========================================================================
    # Left (`-u`) Wood Vanity (`sp_vanity`), Speckled Countertop & Sink, Wood-Framed Mirror (`sp_mirror`) + Chrome Towel Bar!
    hbox(-11.35, -9.55, -12.0, -8.6, ZF, 4.0, Fit("sp_vanity"), ne=Fit("sp_vanity"))
    hbox(-11.35, -9.45, -12.1, -8.5, 4.0, 4.16, tspec("sp_stuc_tan", 2), t=Fit("sp_sink_top"))
    hbox(-11.35, -11.18, -11.7, -8.9, 4.45, 7.25, "sp_vanity", ne=Fit("sp_mirror"), solid=False)
    hbox(-11.35, -11.05, -11.4, -9.2, 7.35, 7.65, "sp_fluor", solid=False)              # 3-bulb vanity light bar
    hbox(-11.35, -11.15, -8.3, -6.6, 4.85, 4.95, "sp_wt_tank", solid=False)             # Chrome towel bar
    # Recessed wall niche frame below window + White Porcelain Toilet (`img2_042` center-right!)
    hbox(-8.0, -6.4, -15.42, -15.28, 2.1, 3.5, trim_w, se=w_trq, solid=False)
    hbox(-5.6, -4.2, -15.3, -14.5, ZF, 3.85, trim_w)                                    # Toilet tank
    hbox(-5.5, -4.3, -14.5, -13.1, ZF, 2.65, trim_w)                                    # Toilet bowl
    # Right (`+u`) White Bathtub + Patterned Starfish/Coral Shower Curtain (`{sp_shwcurt`, `img2_042` right!)
    hbox(-4.65, -2.85, -12.8, -6.45, ZF, 2.85, trim_w)
    hbox(-4.73, -4.63, -12.75, -6.50, 1.8, 7.9, "{sp_invis", sw=Fit("{sp_shwcurt", (2.0, 1.0)), group="fence", solid=False)

    # ==========================================================================
    # 6. CEILING FANS & WARM INTERIOR ROOM LIGHTING (`img2_032..042`)
    # ==========================================================================
    for du_f, dv_f, btex, htex in (
        (14.2, 7.6, "sp_vanity", "sp_rollup"),          # Dining/Living bronze 5-blade fan (img2_037/038)
        (15.4, -12.6, "sp_stuc_wht", "sp_stuc_wht"),    # Kitchen NW nook white 5-blade fan (img2_034)
        (0.8, -10.2, "sp_stuc_wht", "sp_stuc_wht"),     # Bedroom 1 white 5-blade fan (img2_039)
        (-16.1, -10.6, "sp_wt_tank", "sp_wt_tank"),     # Bedroom 2 brushed-nickel 5-blade fan (img2_041)
        (-14.2, 7.2, "sp_vanity", "sp_rollup"),         # Bedroom 3 wood-blade fan (img2_040)
    ):
        fx, fy = wpt(du_f, dv_f)
        ceiling_fan(fx, fy, ZC, blade_tex=btex, hub_tex=htex, yaw_deg=c3_yaw)

    for du_l, dv_l, zl, lval, lcol in (
        (1.5, 8.2, 8.1, 155, "255 244 224"),            # Living Room warm daylight fill
        (14.2, 7.6, 7.9, 165, "255 240 214"),           # Dining ceiling fan light
        (14.6, -5.5, 8.6, 195, "248 250 255"),          # Galley Kitchen bright fluorescent light
        (14.6, -12.6, 7.9, 145, "248 248 244"),         # Kitchen breakfast nook + vestibule light
        (6.4, -12.2, 8.2, 130, "255 242 218"),          # Vestibule warm sconce
        (0.5, -10.2, 7.9, 150, "252 246 234"),          # Bedroom 1 ceiling fan light
        (-7.2, -3.5, 8.2, 125, "255 244 224"),          # Inner Hallway light
        (-8.2, -10.2, 8.0, 170, "240 252 255"),         # Turquoise Bathroom bright vanity light
        (-15.6, -10.6, 7.9, 145, "250 246 238"),        # Bedroom 2 ceiling fan light
        (-14.2, 7.2, 7.9, 145, "255 242 220"),          # Bedroom 3 ceiling fan light
    ):
        lx, ly = wpt(du_l, dv_l)
        light(lx, ly, zl, val=lval, color=lcol)

    # ==========================================================================
    # 7. FRONT STOOP, WALKWAY, CLOUD TOPIARY & FULL ZILLOW BACKYARD (`img2_023, 043..046`)
    # ==========================================================================
    # 4 wide terracotta-red front steps (`sp_redstep`, easy auto-step `0.34 ft` risers!)
    for sk in range(4):
        dv_s = 16.0 + sk * 0.95
        zt_s = ZF - sk * 0.33
        hbox(3.4, 9.6, dv_s, dv_s + 0.96, 0.04, zt_s, tspec("sp_redstep", 4))

    walk_3003 = [wpt(6.5, 20.0), wpt(8.5, 29.0), wpt(10.5, 41.0)]
    road_ribbon(walk_3003, 3.6, CONC, z_bot=0.0, z_top=0.14, curbs=False)

    # Manicured pom-pom topiaries & curved concrete-edged mulch bed w/ cloud-pruned bonsai tree (`img2_023, 044`)
    for du_p, tiers in ((-10.2, 2), (10.8, 3)):
        px, py = wpt(du_p, 17.5)
        frustum_ring(px, py, 0.24, 0.20, 0.04, 1.8 + tiers * 1.4, tspec("sp_bark", 2), sides=6, group="detail", solid=False)
        for tk in range(tiers):
            frustum_ring(px, py, 1.45 - tk * 0.14, 1.25 - tk * 0.14, 0.8 + tk * 1.85, 1.95 + tk * 1.85,
                         tspec("sp_hedge", 3), sides=8, group="detail", solid=True)

    bed_cx, bed_cy = wpt(-1.5, 29.5)
    obox(bed_cx, bed_cy, 0.04, 0.28, 3.4, 7.8, c3_yaw + 18.0, CONC, group="detail", solid=True)
    obox(bed_cx, bed_cy, 0.06, 0.31, 2.8, 7.2, c3_yaw + 18.0, tspec("sp_mulch", 4), group="detail", solid=True)
    bx_t, by_t = wpt(-0.3, 27.0)
    frustum_ring(bx_t, by_t, 0.45, 0.30, 0.30, 5.2, tspec("sp_bark", 2), sides=6, group="detail", solid=True)
    for pd_u, pd_v, z0_p, z1_p, pr in ((0.0, 0.0, 4.8, 7.6, 3.2), (-2.2, 0.8, 2.8, 4.2, 1.8), (2.0, 0.5, 3.2, 4.6, 1.9), (0.2, 2.2, 2.2, 3.5, 1.6)):
        tx, ty = wpt(-0.3 + pd_u, 27.0 + pd_v)
        frustum_ring(tx, ty, pr, pr * 0.88, z0_p, z1_p, tspec("sp_hedge", 3), sides=8, group="detail", solid=True)

    # --- BACKYARD (`v = -55.0 .. -16.0`, `img2_045` & `img2_046`!) ---
    # 3-tier concrete rear steps outside Rear Kitchen Door (`u = 8.4 .. 14.4`)
    for rk in range(3):
        dv_r = -16.0 - (rk + 1) * 1.05
        zt_r = ZF - rk * 0.42
        hbox(8.4, 14.4, dv_r, dv_r + 1.06, 0.04, zt_r, CONC)

    # Wide poured-concrete backyard patio & driveway (`u = 4.2 .. 21.8, v = -55.0 .. -16.0`, `img2_045`!) + dry backyard grass (`img2_046`)
    hbox(4.2, 21.8, -55.0, -16.0, 0.02, 0.14, CONC)
    hbox(-21.2, 4.2, -53.5, -16.0, 0.02, 0.10, tspec("sp_drylawn", 12))

    # Detached Tan-Stucco Outbuilding / Garage (`sid=2891`, `u = 5.6 .. 21.2, v = -54.0 .. -34.5`, `img2_045` right & `img2_046` left!)
    gar_tan = tspec("sp_stuc_tan", 9)
    hbox(5.6, 21.2, -54.0, -34.5, 0.14, 8.8, gar_tan)
    gar_pts = [wpt(5.6, -54.0), wpt(5.6, -34.5), wpt(21.2, -34.5), wpt(21.2, -54.0)]
    hiproof(gar_pts, 8.8, roof, eave=1.1, pitch=4.4 / 12.0, fascia_tex="sp_rollup")
    # Dark walk-in door + framed window facing SE toward patio (`img2_045`) + side window facing SW yard (`img2_046` left!)
    hbox(9.8, 13.0, -34.55, -34.35, 0.20, 7.5, "sp_door_3003", se=Fit("sp_door_3003"), solid=False)
    hbox(15.2, 18.8, -34.55, -34.35, 3.2, 7.2, trim_w, se=Fit("sp_win_dark"), solid=False)
    hbox(5.45, 5.65, -45.5, -41.5, 3.2, 7.2, trim_w, sw=Fit("sp_win_dark"), solid=False)

    # Rustic Weathered Vertical-Wood Backyard Shed w/ double doors & 2 white windows (`img2_045` center-back!)
    hbox(-9.6, 4.2, -53.2, -43.2, 0.10, 7.6, tspec("sp_redfnc", 6), se=Fit("sp_shed_wd"))
    sh_cx, sh_cy = wpt(-2.7, -48.2)
    ogable(sh_cx, sh_cy, 7.6, 9.4, 6.9, 5.0, c3_yaw, roof, tspec("sp_redfnc", 6), eave=0.6)

    # Weathered Wooden Privacy Fences enclosing `3003`'s yard (`img2_044, 045, 046`) w/ open rear alley gate at `u = 0.0 .. 5.2`!
    wfnc = tspec("sp_woodfnc", 7)
    hbox(-21.6, -21.2, -53.5, 14.0, 0.10, 6.0, wfnc)        # SW side yard fence
    hbox(21.6, 22.0, -54.5, 14.0, 0.10, 6.0, wfnc)          # NE side yard fence (`img2_043` right!)
    hbox(-21.6, -9.6, -53.6, -53.2, 0.10, 6.0, wfnc)        # NW rear fence (west of wood shed)

    if stage >= 3:
        # Blue roll-out trash cart beside detached backyard garage (`img2_045` right!)
        tb_x, tb_y = wpt(20.2, -32.2)
        trash_bin(tb_x, tb_y, c3_yaw, col_tex="sp_bin_blu", z0=0.14)
        # Destructible pickup truck parked at 3003's front SE curb (`img2_023` foreground right!)
        pk_x, pk_y = wpt(20.5, 36.5)
        brush_vehicle(pk_x, pk_y, 232.0, "sp_stuc_gry", kind="pickup", z0=0.12)

    by_sid["done"].update({2145, 2891})
    return wpt
