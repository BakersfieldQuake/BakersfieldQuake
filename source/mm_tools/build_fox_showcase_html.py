r"""Builds the 100% self-contained single-file HTML showcase page:
  G:\Quake\Combat\BakersfieldQuake\fox_showcase.html

Zero external dependencies: embeds all 29 smooth-shaded .md3 models (gzipped binary arena +
base64 diffuse & emissive glow atlases for an interactive WebGL2 3D Prop Museum), 20 side-by-side
Real Bakersfield Reference vs. Compiled fox.bsp In-Map renders, and 19 custom 2D murals,
wallpapers, alpha cutouts, and prop texture atlases.
"""
import base64
import gzip
import io
import json
import math
import os
import re
import struct
import sys

import numpy as np
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import md3lib  # noqa: E402

PROGS_FOX = os.path.join(MOD, "progs", "fox")
TEX_DIR = os.path.join(MOD, "textures")
REF_DIR = os.path.join(HERE, "fox_ref")
SHOTS_DIR = r"C:\Users\qxdc\.gemini\antigravity\brain\5db7f067-c47d-4c2e-842c-13740d7b7f15\scratch\fox_shots"
OUT_HTML = os.path.join(MOD, "fox_showcase.html")


def img_to_jpeg_uri(path, max_w=880, max_h=560, quality=85, crop_fit=None):
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        # Subtle dark checkerboard for alpha textures
        bg = Image.new("RGBA", im.size, (22, 28, 40, 255))
        px = bg.load()
        w, h = im.size
        step = max(8, min(w, h) // 16)
        for y in range(h):
            for x in range(w):
                if ((x // step) + (y // step)) & 1:
                    px[x, y] = (36, 45, 62, 255)
        bg.alpha_composite(im)
        im = bg.convert("RGB")
    else:
        im = im.convert("RGB")
    if crop_fit:
        im = ImageOps.fit(im, crop_fit, method=Image.Resampling.LANCZOS)
    else:
        im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    bio = io.BytesIO()
    im.save(bio, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode("ascii")


class ArenaPacker:
    def __init__(self):
        self.buf = bytearray()
        self.textures = []

    def add_bytes(self, raw_bytes):
        while len(self.buf) & 3:
            self.buf.append(0)
        off = len(self.buf)
        self.buf.extend(raw_bytes)
        return [off, len(raw_bytes)]

    def add_tex(self, path, max_dim=1024, quality=90):
        im = Image.open(path).convert("RGB")
        if max(im.size) > max_dim:
            im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        bio = io.BytesIO()
        im.save(bio, "JPEG", quality=quality, optimize=True)
        uri = "data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.textures)
        self.textures.append({"uri": uri, "w": im.size[0], "h": im.size[1]})
        return idx


def build_wire_edges(tri_arr):
    e01 = np.sort(tri_arr[:, [0, 1]], axis=1)
    e12 = np.sort(tri_arr[:, [1, 2]], axis=1)
    e20 = np.sort(tri_arr[:, [2, 0]], axis=1)
    return np.unique(np.vstack([e01, e12, e20]), axis=0).astype("<u2")


# Count exact misc_model placements in compiled maps/fox.bsp
def count_bsp_instances():
    d = open(os.path.join(MOD, "maps", "fox.bsp"), "rb").read()
    eo, en = struct.unpack("<2i", d[4:12])
    ents = d[eo:eo + en].decode("latin1")
    counts = {}
    for m in re.finditer(r"\{([^}]*)\}", ents):
        kv = dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', m.group(1)))
        if kv.get("classname") == "misc_model":
            nm = kv["mdl"].split("/")[-1].replace(".md3", "")
            counts[nm] = counts.get(nm, 0) + 1
    return counts


PROP_SPECS = [
    # Historic Fox Theater (6)
    ("fox_chandelier",  "Spanish Wrought-Iron & Gold Lobby Chandelier", "fox",      "Ceiling-hung Spanish Revival chandelier with 8 warm glowing candle bulbs in the Skouras Main Lobby & Mezzanine."),
    ("fox_clockpost",   "1930 4-Dial Bronze 'HOPE' Street Clock",       "fox",      "15.7-ft fluted bronze sidewalk clock on 20th St & 20th/H corners with 4 illuminated Roman-numeral faces."),
    ("fox_guitar",      "Stage-Left Green Room Electric Guitar",        "fox",      "Contoured sunburst double-cutaway electric guitar with white pickguard & maple neck on tubular A-frame stand."),
    ("fox_palm",        "25-ft California Fan Palm (Washingtonia)",     "fox",      "Full-height downtown Bakersfield palm with diamond-patterned trunk, tan shag skirt & 18 arched fan fronds."),
    ("fox_palm_sm",     "15.5-ft Courtyard / Planter Fan Palm",         "fox",      "Medium streetscape & courtyard California fan palm framing Today Cleaners and downtown plazas."),
    ("fox_streetlamp",  "Twin-Globe Cast-Iron Sidewalk Streetlamp",     "fox",      "14.6-ft historic Bakersfield double-scroll bronze streetlamp with glowing frosted-glass acorn globes."),

    # The Padre Hotel (19)
    ("pad_chand_drum",  "Grand Lobby Two-Tier Gold Drum Chandelier",    "padre",    "Warm amber-lit double-drum fabric & brass chandelier suspended inside The Padre Hotel's 1928 Grand Lobby."),
    ("pad_sofa_leather","Tufted Cognac Leather Chesterfield Sofa",      "padre",    "Deep-buttoned cognac leather lounge sofa with rolled arms & brass nailhead trim in Lobby & Oil Baron Suite."),
    ("pad_sofa_red",    "Crimson Velvet Chesterfield Suite Sofa",       "padre",    "Plush crimson velvet Chesterfield sofa set against the black-and-white Rococo mirror wall in Farmer's Daughter Suite."),
    ("pad_chair_club",  "Espresso Leather Lobby Club Armchair",         "padre",    "Wide rolled-arm espresso leather lounge armchair paired around the Grand Lobby check-in & Fireside Room."),
    ("pad_chair_hound", "Black & White Houndstooth Accent Armchair",    "padre",    "Signature boutique Padre guest-room accent armchair upholstered in crisp black-and-white houndstooth weave."),
    ("pad_stool_yellow","Yellow Powder-Coated Tolix Cafe Barstool",     "padre",    "Industrial metal bistro barstool along the 18th St Farmacy sidewalk patio and cafe counter."),
    ("pad_stool_white", "Distressed White Tolix Brimstone Barstool",    "padre",    "High-top metal barstool lining Brimstone Bar's main counter and communal lounge tables."),
    ("pad_pooltable",   "Brimstone Red-Felt Billiard Table",            "padre",    "Tournament slate pool table in Brimstone Lounge with crimson championship felt, leather pockets, cues & racked balls."),
    ("pad_chand_fringe","Brimstone 3-Tier Amber Gold-Fringe Chandelier","padre",    "Glowing three-tier vintage fringe pendant lamp illuminating the Brimstone communal high-top & pool table."),
    ("pad_banquet_set", "Clover Ballroom Draped Banquet Round & 6 Chairs","padre",  "6-ft floor-length white linen banquet table surrounded by 6 cushioned event chairs in Clover 1 & 2 Ballroom."),
    ("pad_chand_brass", "Clover Ballroom 6-Light Brass Chandelier",     "padre",    "Classic 6-arm polished brass chandelier lighting the Clover Ballroom & upstairs luxury suites."),
    ("pad_treadmill",   "Sub-Grade Gym Commercial Precor Treadmill",    "padre",    "Commercial running deck with angled LED console, heart-rate grips & side rails in the B1 24-Hr Fitness Center."),
    ("pad_elliptical",  "Sub-Grade Gym Cross-Trainer Elliptical",       "padre",    "Dual-stride commercial elliptical trainer facing the full-wall mirror in the Padre basement gym."),
    ("pad_bike",        "Sub-Grade Gym Upright Studio Spin Bike",       "padre",    "Weighted-flywheel upright exercise bike with racing saddle & console in the B1 Fitness Center."),
    ("pad_watercooler", "Sub-Grade Gym Bottled Water Dispenser",        "padre",    "Chilled 5-gallon clear polycarbonate water jug & stainless hydration stand in the B1 gym."),
    ("pad_chair_yellow","Conference Room Mustard-Yellow Swivel Chair",  "padre",    "Ribbed mid-century yellow task chair on 5-star chrome casters surrounding the Floor 2 boardroom table."),
    ("pad_chand_linear","Conference Room Linear Architectural Pendant", "padre",    "Sleek suspended rectangular architectural light bar casting even warm light over the Floor 2 conference table."),
    ("pad_heater",      "Prairie Fire Glowing Mushroom Patio Heater",   "padre",    "7.4-ft hammered-bronze outdoor propane heater with glowing amber emitter dome on the 2nd-floor Prairie Fire terrace."),
    ("pad_bed_king",    "Luxury Suite Carved Dark-Wood King Bed",       "padre",    "4-poster / panel dark walnut King bed with crisp white duvet, crimson throw runner & bolster pillows."),
    ("pad_bed_queen",   "Boutique Guest Room Carved Queen Bed",         "padre",    "Custom dark-wood Queen bed arranged in pairs inside Room 406 and upper Padre guest rooms."),
    ("pad_jacuzzi",     "Oil Baron Suite Corner Jetted Whirlpool Tub",  "padre",    "Sculpted acrylic corner jacuzzi tub with chrome waterfall filler & hydro-jets in the 6th-floor Oil Baron Suite."),

    # Downtown Bakersfield (2 additional unique civic props)
    ("get_bus",         "38-ft Golden Empire Transit ('GET bus') Coach","downtown", "1:1 low-floor Bakersfield transit bus in blue/gold/green swoop livery with glowing LED route sign & rooftop CNG pod."),
    ("bvm_bikerack",    "Buena Vista Museum Green Bicycle Rack",        "downtown", "Powder-coated green bicycle-silhouette sidewalk rack outside the Buena Vista Museum of Natural History on Chester Ave."),
]


TOUR_PAIRS = [
    # Fox Theater
    ("fox_corner",     "gal_109.jpg",            "fox",      "01 Postcard 20th & H",
     "20th & H St Corner: 116-ft Fox Clock Tower & Wrap-Around Marquee",
     "1:1 Spanish Colonial Revival corner tower with 4 illuminated navy clocks, ribbed silver-blue dome, alpha-cutout cursive 'Fox' neon channel letters, 1930 HOPE clock, fan palms & streetlamps."),
    ("fox_marquee",    "fox_block/fblk_020.jpg", "fox",      "02 Fox Front H St",
     "H Street Marquee Wing, Readerboard & Spanish Tile Skirt",
     "Photo-matched Feb 2026 marquee readerboards ('ALI SIDDIQ', 'BABY BASH MC'), terracotta tile skirt, divided arched clerestory transoms, and parked street vehicles."),
    ("fox_clock_20th", "gal_042.jpg",            "fox",      "01 Postcard 20th & H",
     "20th Street South Gable & 1930 4-Dial Bronze 'HOPE' Clock",
     "Custom smooth-shaded fox_clockpost.md3 with 4 glowing Roman-numeral clock faces alongside 25-ft California fan palms and Spanish storefront awnings."),
    ("fox_vestibule",  "gal_112.jpg",            "fox",      "02 Fox Front H St",
     "Outer Rainbow Terrazzo Vestibule & Illuminated 2026 Show Posters",
     "Geometric rainbow terrazzo floor, island ticket booth, navy starlit ceiling soffit, and bespoke illuminated fx_post26 poster trio in bronze cases."),
    ("fox_tapestry",   "gal_114.jpg",            "fox",      "26 Main Lobby",
     "Foyer Alcove: Custom Spanish California Pastoral Tapestry",
     "High-res painted fx_tapestry wall hanging framed in warm architectural downlighting above the tufted crimson velvet bench."),
    ("fox_lobby",      "gal_115.jpg",            "fox",      "26 Main Lobby",
     "Main Skouras Lobby: Sky-Blue Fresco Ceiling & Iron Chandeliers",
     "Stepped sky-blue & rose-medallion fresco ceiling bays with four custom wrought-iron & candle-glow fox_chandelier.md3 fixtures and 1953 concession stand."),
    ("fox_auditorium", "fox_block/fblk_020.jpg", "fox",      "25 Auditorium",
     "1,500-Seat Atmospheric Auditorium, Box Valances & 9-Plume Sunburst",
     "48'×27' proscenium, gilded velvet fx_boxval box-seat valances, 3 orchestra seating banks, 2 balcony tiers, FOH truss & Stage-Left Green Room with 3D electric guitars."),

    # Padre Hotel
    ("padre_corner",   "padre/padre_052.jpg",    "padre",    "03 Padre Hotel SE",
     "18th & H St SE Corner: 8-Story 1928 Padre Hotel & Blade Sign",
     "Full 8-story + basement Spanish Revival landmark with vertical 'PADRE HOTEL' neon corner blade, H St canopy, concrete bollards, mast-arm traffic signals & ladder crosswalks."),
    ("padre_front",    "padre/padre_028.jpg",    "padre",    "04 Padre 18th St",
     "1702 18th St Entrance, Farmacy Patio & Yellow Tolix Barstools",
     "Curved Mission Revival entrance gable, playable white steel fire escape, striped awnings, and 17 smooth-shaded pad_stool_yellow.md3 sidewalk stools."),
    ("padre_lobby",    "padre/padre_171.jpg",    "padre",    "06 Padre Grand Lobby",
     "Grand Lobby: Cowgirl Lasso Mural, Drum Chandeliers & Club Chairs",
     "Custom pad_mural cowgirl painting behind reception, two glowing pad_chand_drum.md3 fixtures, espresso club armchairs, diamond marble tile & {farm_sign blade cutout."),
    ("padre_brimstone","padre/padre_188.jpg",    "padre",    "07 Padre Brimstone",
     "Brimstone Bar & Lounge: White Tolix Stools, Fringe Lamp & Pool Table",
     "23 pad_stool_white.md3 barstools, glowing 3-tier amber pad_chand_fringe.md3 chandelier, back-lit liquor bar, and red-felt pad_pooltable.md3."),
    ("padre_gym",      "padre/padre_190.jpg",    "padre",    "08 Padre Sub-Grade",
     "Sub-Grade B1 24-Hr Fitness Center: Treadmills, Elliptical & Spin Bike",
     "Full basement gym equipped with 2 Precor treadmills, elliptical cross-trainer, studio spin bike, bottled water dispenser & full-wall mirror."),
    ("padre_dandy",    "padre/padre_091.jpg",    "padre",    "10 Padre Upper Lobby",
     "Floor 2 Mezzanine: Seamless Dandelion Accent Wall & Wainscoting",
     "Height-aligned pad_dandy dandelion botanical mural wallpaper seamlessly meeting white paneled wainscoting along the 2nd-floor event promenade."),
    ("padre_conf",     "padre/padre_113.jpg",    "padre",    "11 Padre Conference",
     "Floor 2 Boardroom: 16 Yellow Swivel Chairs & Linear Pendant",
     "16 pad_chair_yellow.md3 conference chairs around the boardroom table beneath pad_chand_linear.md3, flanked by dandelion walls & Padre wall screen."),
    ("padre_prairie",  "padre/padre_182.jpg",    "padre",    "12 Padre Prairie Fire",
     "Floor 2 Prairie Fire Rooftop Terrace: Mushroom Heaters -> Fox View",
     "Outdoor bar & lounge terrace featuring 3 glowing bronze pad_heater.md3 propane heaters with a direct sightline north to the Fox Clock Tower."),
    ("padre_oilbaron", "padre/padre_140.jpg",    "padre",    "15 Padre Oil Baron",
     "Floor 6 Oil Baron Suite: Corner Jacuzzi, Cognac Sofa & King Bed",
     "Presidential suite combining sculpted pad_jacuzzi.md3 whirlpool tub, tufted cognac Chesterfield sofa, King bed & archival Kern oil-derrick art."),
    ("padre_farmers",  "padre/padre_144.jpg",    "padre",    "16 Padre Farmer's",
     "Floor 7 Farmer's Daughter Suite: Rococo Mirror Wall & Red Velvet",
     "Custom black-and-white damask pad_rococo accent wall with gilded Rococo mirror behind the crimson velvet Chesterfield sofa, looking toward the Fox."),
    ("padre_rooftop",  "padre/padre_173.jpg",    "padre",    "17 Padre 8th-Floor",
     "Floor 8 Rooftop Parapet & Dual Neon 'PADRE HOTEL' Scaffold Signs",
     "Walkable 8th-floor Spanish tile parapet crowned by the iconic SE and North red neon structural steel scaffold signs."),

    # Downtown Bakersfield
    ("dt_nile",        "fox_block/fblk_133.jpg", "downtown", "18 Nile Theater",
     "19th Street Historic Nile Theater Marquee & Vertical Blade Sign",
     "Restored 1924 Nile Theater facade on 19th St with twin ticket booths, illuminated marquee readerboard & towering vertical 'NILE' neon blade."),
    ("dt_eyemural",    "gal_100.jpg",            "downtown", "18 Nile Theater",
     "19th St Block: Surrealist Eye & Floating Umbrellas Mural",
     "Custom wide-format fn_mural street mural overlooking the west downtown parking court just behind the Nile Theater."),
    ("dt_thirst",      "fox_block/fblk_046.jpg", "downtown", "03 Padre Hotel SE",
     "SW 19th & H St: 'Thirst Trap — Prairie Fire' Padre Billboard",
     "Elevated steel billboard structure displaying our custom-painted & night-glowing fn_thirst Padre Hotel rooftop bar advertisement."),
    ("dt_gearmural",   "fox_block/fblk_343.jpg", "downtown", "21 18th & H Gear",
     "SE 18th & H St: CAA Blue & Orange Mechanical Gear Mural",
     "Full-facade fn_caamur geometric ribbon & gear mural directly across 18th St from The Padre Hotel with yellow ladder crosswalks."),
    ("dt_bvm_bus",     "fox_block/fblk_163.jpg", "downtown", "22 Buena Vista",
     "Chester Ave: Buena Vista Museum, Green Bike Rack & GET Transit Bus",
     "Paleo-shark fn_bvm museum mural, custom green bicycle-shaped bvm_bikerack.md3 on the sidewalk, and 38-ft Golden Empire Transit get_bus.md3 coach."),
]


ART_GALLERY = [
    ("textures/fx_tapestry.png",        "fx_tapestry",        "Fox Theater",  "1930 Spanish California Pastoral Tapestry (Vestibule Alcove)"),
    ("textures/fx_post26.png",          "fx_post26 (+glow)",  "Fox Theater",  "Illuminated 2026 Fox Theater Show Poster Trio"),
    ("textures/fx_boxval.png",          "fx_boxval",          "Fox Theater",  "Auditorium Crimson Velvet & Gold Bullion Box-Seat Valance"),
    ("textures/pad_mural.png",          "pad_mural",          "Padre Hotel",  "Grand Lobby Reception Vintage Cowgirl & Lasso Mural"),
    ("textures/{farm_sign.png",         "{farm_sign (alpha)", "Padre Hotel",  "Wrought-Iron Pitchfork & Tractor 'FARMACY CAFE' Cutout Sign"),
    ("textures/farm_art.png",           "farm_art",           "Padre Hotel",  "Farmacy Cafe Vibrant Pop-Art Botanical Crown Portrait I"),
    ("textures/farm_art2.png",          "farm_art2",          "Padre Hotel",  "Farmacy Cafe Vibrant Pop-Art Regal Portrait II"),
    ("textures/pad_dandy.png",          "pad_dandy",          "Padre Hotel",  "Floor 2 Mezzanine & Conference Seamless Dandelion Wallpaper"),
    ("textures/pad_rococo.png",         "pad_rococo",         "Padre Hotel",  "Farmer's Daughter Suite Damask & Gilded Rococo Mirror Wall"),
    ("textures/pad_oilart.png",         "pad_oilart",         "Padre Hotel",  "Oil Baron Suite Kern River Oil-Field Archival Sepia Triptych"),
    ("textures/pad_tv.png",             "pad_tv (+glow)",     "Padre Hotel",  "Guest Suite Wall-Mounted Flatscreen TV ('Bakersfield Live')"),
    ("textures/pad_curt_rd.png",        "pad_curt_rd",        "Padre Hotel",  "Luxury Suite Tailored Crimson Velvet Full-Height Drapery"),
    ("textures/pad_curt_gy.png",        "pad_curt_gy",        "Padre Hotel",  "Guest Room Tailored Charcoal Pleated Blackout Drapery"),
    ("textures/fn_mural.png",           "fn_mural",           "Downtown",     "19th St Surrealist Eye, Pyramids & Floating Umbrellas Mural"),
    ("textures/fn_caamur.png",          "fn_caamur",          "Downtown",     "SE 18th & H St CAA Blue & Orange Mechanical Gear Street Mural"),
    ("textures/fn_thirst.png",          "fn_thirst (+glow)",  "Downtown",     "SW 19th & H St 'Thirst Trap' Padre Rooftop Lounge Billboard"),
    ("textures/fn_bvm.png",             "fn_bvm",             "Downtown",     "Chester Ave Buena Vista Museum Shark & Fossil Facade Mural"),
    ("progs/fox/fox_materials.png",     "fox_materials",      "3D Prop Atlas","1024×1024 Master Wood, Leather, Velvet, Brass, Marble & Foliage Atlas"),
    ("progs/fox/get_bus_tex.png",       "get_bus_tex",        "3D Prop Atlas","1024×1024 Golden Empire Transit ('GET bus') Livery & LED Atlas"),
]


def main():
    assert len(PROP_SPECS) == 29, f"Expected 29 props, got {len(PROP_SPECS)}"
    inst_counts = count_bsp_instances()
    packer = ArenaPacker()

    t_mat = packer.add_tex(os.path.join(PROGS_FOX, "fox_materials.png"), max_dim=1024, quality=91)
    t_mat_glow = packer.add_tex(os.path.join(PROGS_FOX, "fox_materials_glow.png"), max_dim=1024, quality=89)
    t_bus = packer.add_tex(os.path.join(PROGS_FOX, "get_bus_tex.png"), max_dim=1024, quality=91)
    t_bus_glow = packer.add_tex(os.path.join(PROGS_FOX, "get_bus_tex_glow.png"), max_dim=1024, quality=89)

    models_out = []
    tot_verts = 0
    tot_tris = 0
    for key, title, zone, desc in PROP_SPECS:
        md3_p = os.path.join(PROGS_FOX, key + ".md3")
        assert os.path.isfile(md3_p), f"Missing {md3_p}"
        m = md3lib.read(md3_p)
        surfs = []
        pts_all = []
        mv, mt = 0, 0
        for s in m["surfaces"]:
            vv = np.asarray(s["frames"][0][0], dtype="<f4")
            nn = np.asarray(s["frames"][0][1], dtype="<f4")
            nlen = np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-8)
            nn_i8 = np.clip(np.round((nn / nlen) * 127.0), -127, 127).astype("<i1")
            # Pad i8 normal to 4 bytes per vertex for clean WebGL alignment
            nn_pad = np.zeros((len(vv), 4), dtype="<i1")
            nn_pad[:, :3] = nn_i8
            uv = np.asarray(s["st"], dtype="<f4")
            tris = np.asarray(s["tris"], dtype="<u2")
            edges = build_wire_edges(tris)
            pts_all.append(vv)
            mv += len(vv)
            mt += len(tris)
            is_bus = "get_bus" in s["shader"]
            surfs.append({
                "nv": len(vv),
                "nt": len(tris),
                "ne": len(edges),
                "pos": packer.add_bytes(vv.tobytes()),
                "nrm": packer.add_bytes(nn_pad.tobytes()),
                "uv": packer.add_bytes(uv.tobytes()),
                "tris": packer.add_bytes(tris.tobytes()),
                "edges": packer.add_bytes(edges.tobytes()),
                "tex": t_bus if is_bus else t_mat,
                "glow": t_bus_glow if is_bus else t_mat_glow,
            })
        pts = np.vstack(pts_all)
        bmin = pts.min(axis=0).round(2).tolist()
        bmax = pts.max(axis=0).round(2).tolist()
        tot_verts += mv
        tot_tris += mt
        models_out.append({
            "id": key,
            "title": title,
            "zone": zone,
            "desc": desc,
            "nv": mv,
            "nt": mt,
            "count": inst_counts.get(key, 0),
            "bmin": bmin,
            "bmax": bmax,
            "ceiling": key in ("fox_chandelier", "pad_chand_drum", "pad_chand_fringe", "pad_chand_brass", "pad_chand_linear"),
            "surfaces": surfs,
        })

    gz_arena = gzip.compress(bytes(packer.buf), compresslevel=9)
    print(f"Packed 29 MD3 models ({tot_verts} verts, {tot_tris} tris): {len(packer.buf)/1e3:.1f} KB raw -> {len(gz_arena)/1e3:.1f} KB gzipped")

    tour_out = []
    for shot_id, ref_rel, zone, spot_q, title, desc in TOUR_PAIRS:
        shot_p = os.path.join(SHOTS_DIR, shot_id + ".jpg")
        ref_p = os.path.join(REF_DIR, ref_rel.replace("/", os.sep))
        assert os.path.isfile(shot_p), f"Missing shot {shot_p}"
        assert os.path.isfile(ref_p), f"Missing ref {ref_p}"
        tour_out.append({
            "id": shot_id,
            "zone": zone,
            "spot": spot_q,
            "title": title,
            "desc": desc,
            "refName": ref_rel,
            "refUri": img_to_jpeg_uri(ref_p, crop_fit=(640, 380), quality=84),
            "mapUri": img_to_jpeg_uri(shot_p, crop_fit=(640, 380), quality=86),
        })

    art_out = []
    for rel_p, code_nm, cat, caption in ART_GALLERY:
        full_p = os.path.join(MOD, rel_p.replace("/", os.sep))
        assert os.path.isfile(full_p), f"Missing art {full_p}"
        im_orig = Image.open(full_p)
        art_out.append({
            "code": code_nm,
            "cat": cat,
            "caption": caption,
            "dims": f"{im_orig.size[0]}×{im_orig.size[1]}",
            "uri": img_to_jpeg_uri(full_p, max_w=640, max_h=640, quality=87),
        })

    payload = {
        "textures": packer.textures,
        "models": models_out,
        "tour": tour_out,
        "art": art_out,
        "binGz": base64.b64encode(gz_arena).decode("ascii"),
    }

    html = HTML_TEMPLATE.replace("/*__FOX_SHOWCASE_DATA__*/null", json.dumps(payload, separators=(",", ":")), 1)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote 100% self-contained showcase HTML: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)")


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Historic Fox Theater, The Padre Hotel &amp; Downtown Bakersfield · Quake Map &amp; 3D Asset Showcase</title>
<style>
:root {
  --bg: #080c15;
  --bg2: #0e1525;
  --card: #121b2e;
  --card-hi: #17233b;
  --line: rgba(255, 255, 255, 0.12);
  --line-gold: rgba(245, 184, 65, 0.55);
  --text: #f1f5fb;
  --muted: #9aa8bf;
  --gold: #f5b841;
  --gold-ink: #1b1203;
  --cyan: #38bdf8;
  --mint: #34d399;
  --rose: #fb7185;
  color-scheme: dark;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: radial-gradient(1200px 600px at 20% -10%, rgba(245,184,65,0.11), transparent 65%),
              radial-gradient(1000px 550px at 85% 0%, rgba(56,189,248,0.10), transparent 60%),
              var(--bg);
  color: var(--text);
  font: 14.5px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
.mono { font-family: ui-monospace, "Cascadia Mono", Consolas, monospace; }
.wrap { max-width: 1520px; margin: 0 auto; padding: 20px 22px 72px; }

/* Hero */
.hero {
  background: linear-gradient(145deg, rgba(22,32,54,0.92), rgba(12,18,32,0.94));
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 24px 26px;
  box-shadow: 0 22px 50px rgba(0,0,0,0.45);
  margin-bottom: 22px;
}
.kicker {
  color: var(--gold);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.hero h1 {
  margin: 0 0 8px;
  font-size: clamp(24px, 3vw, 36px);
  font-weight: 850;
  letter-spacing: -0.02em;
}
.hero p.lead {
  margin: 0 0 18px;
  color: var(--muted);
  max-width: 98ch;
  font-size: 15px;
}
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}
.stat-box {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 11px 14px;
}
.stat-box .big { font-size: 21px; font-weight: 850; color: var(--text); }
.stat-box .big span { color: var(--gold); }
.stat-box .lbl { font-size: 12.5px; color: var(--muted); }

.cta-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}
.cta-group { display: flex; flex-wrap: wrap; gap: 9px; align-items: center; }
.btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font: inherit;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text);
  background: #1a2640;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 9px 15px;
  text-decoration: none;
  cursor: pointer;
  transition: 0.15s ease;
}
.btn:hover { background: #223254; border-color: rgba(255,255,255,0.28); }
.btn.gold { background: var(--gold); color: var(--gold-ink); border-color: var(--gold); }
.btn.gold:hover { filter: brightness(1.08); }
.btn.cyan { background: rgba(56,189,248,0.14); border-color: rgba(56,189,248,0.45); color: #bae6fd; }
.cmd-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #090e19;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 13px;
}
.cmd-pill code { color: var(--mint); font-weight: 700; }

/* Section headers */
.sec-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  margin: 34px 0 14px;
}
.sec-head h2 { margin: 0; font-size: clamp(20px, 2.2vw, 27px); font-weight: 820; }
.sec-head p { margin: 4px 0 0; color: var(--muted); font-size: 13.8px; }
.tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.tab {
  font: inherit;
  font-size: 12.5px;
  font-weight: 750;
  color: var(--muted);
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 6px 13px;
  cursor: pointer;
}
.tab.active, .tab:hover { color: var(--text); border-color: var(--line-gold); background: rgba(245,184,65,0.14); }

/* 3D Prop Museum */
.museum-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.85fr);
  gap: 16px;
  align-items: stretch;
}
@media (max-width: 1080px) { .museum-grid { grid-template-columns: 1fr; } }

.stage-shell {
  position: relative;
  min-height: 540px;
  height: 620px;
  background: #09101f;
  border: 1.5px solid var(--line);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 18px 42px rgba(0,0,0,0.48);
  user-select: none;
  touch-action: none;
  cursor: grab;
}
.stage-shell.drag { cursor: grabbing; }
.stage-shell.fullscreen {
  position: fixed; inset: 0; z-index: 999; height: 100vh; border-radius: 0; border: 0;
}
canvas#gl { width: 100%; height: 100%; display: block; }

.stage-top {
  position: absolute; top: 12px; left: 14px; right: 14px;
  display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; pointer-events: none;
}
.stage-top > * { pointer-events: auto; display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.pill {
  background: rgba(8,13,24,0.84);
  backdrop-filter: blur(8px);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 750;
}
.pill.gold { color: var(--gold); border-color: var(--line-gold); }
.tbtn {
  font: inherit; font-size: 12px; font-weight: 750;
  color: var(--text); background: rgba(13,21,38,0.86);
  border: 1px solid var(--line); border-radius: 8px;
  padding: 5px 10px; cursor: pointer;
}
.tbtn[aria-pressed="true"], .tbtn.active {
  background: rgba(245,184,65,0.22); border-color: var(--gold); color: #fde68a;
}

.stage-bot {
  position: absolute; left: 14px; right: 14px; bottom: 12px;
  background: rgba(8,13,24,0.86);
  backdrop-filter: blur(10px);
  border: 1px solid var(--line);
  border-radius: 13px;
  padding: 11px 14px;
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px;
}
.stage-info h3 { margin: 0 0 2px; font-size: 16px; }
.stage-info p { margin: 0; color: var(--muted); font-size: 12.8px; max-width: 68ch; }
.cam-row { display: flex; gap: 5px; flex-wrap: wrap; }

.prop-roster {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  max-height: 620px;
}
.prop-list {
  margin-top: 10px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 8px;
  padding-right: 4px;
}
.pcard {
  text-align: left;
  font: inherit;
  color: var(--text);
  background: rgba(255,255,255,0.035);
  border: 1px solid var(--line);
  border-radius: 11px;
  padding: 9px 11px;
  cursor: pointer;
  transition: 0.12s ease;
}
.pcard:hover { background: rgba(255,255,255,0.07); }
.pcard.active {
  background: rgba(245,184,65,0.15);
  border-color: var(--gold);
  box-shadow: 0 0 0 1px rgba(245,184,65,0.35);
}
.pcard .ptop { display: flex; justify-content: space-between; align-items: center; gap: 6px; margin-bottom: 3px; }
.pcard .ztag {
  font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em;
  padding: 2px 6px; border-radius: 99px;
}
.ztag.fox { background: rgba(251,113,133,0.18); color: #fda4af; }
.ztag.padre { background: rgba(245,184,65,0.18); color: #fcd34d; }
.ztag.downtown { background: rgba(56,189,248,0.18); color: #7dd3fc; }
.pcard .cnt { font-size: 11px; color: var(--mint); font-weight: 700; }
.pcard .pname { font-size: 13px; font-weight: 750; line-height: 1.28; margin-bottom: 3px; }
.pcard .pmeta { font-size: 11px; color: var(--muted); }

/* Comparison Tour */
.tour-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(640px, 1fr));
  gap: 16px;
}
@media (max-width: 720px) { .tour-grid { grid-template-columns: 1fr; } }
.tcard {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.tpair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2px;
  background: #060911;
}
.tfig { position: relative; margin: 0; cursor: zoom-in; overflow: hidden; aspect-ratio: 16 / 9.5; }
.tfig img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.22s ease; }
.tfig:hover img { transform: scale(1.03); }
.tfig .lbl {
  position: absolute; top: 8px; left: 8px;
  font-size: 10.5px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;
  padding: 3px 8px; border-radius: 6px;
  background: rgba(8,12,21,0.84); border: 1px solid var(--line);
}
.tfig .lbl.map { color: var(--gold); border-color: var(--line-gold); }
.tbody { padding: 13px 16px 15px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
.tbody-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.tbody h3 { margin: 0; font-size: 16px; }
.tbody p { margin: 0; color: var(--muted); font-size: 13.2px; }
.tp-link {
  font-size: 12px; font-weight: 750; color: var(--cyan); text-decoration: none; white-space: nowrap;
}
.tp-link:hover { text-decoration: underline; }

/* 2D Art Gallery */
.art-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}
.acard {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 14px;
  overflow: hidden;
  cursor: zoom-in;
  transition: 0.15s ease;
}
.acard:hover { border-color: var(--line-gold); transform: translateY(-2px); }
.acard .aimg {
  height: 200px;
  background: #0a101d;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.acard img { width: 100%; height: 100%; object-fit: contain; display: block; }
.acard .abody { padding: 10px 13px 12px; }
.acard .acode { display: flex; justify-content: space-between; font-size: 11.5px; color: var(--gold); font-weight: 750; margin-bottom: 3px; }
.acard .acap { font-size: 12.8px; color: var(--text); line-height: 1.35; }

/* Lightbox Modal */
#lightbox {
  position: fixed; inset: 0; z-index: 2000;
  background: rgba(4, 7, 14, 0.92);
  backdrop-filter: blur(8px);
  display: none; align-items: center; justify-content: center; flex-direction: column;
  padding: 24px; cursor: zoom-out;
}
#lightbox.open { display: flex; }
#lightbox img { max-width: 94vw; max-height: 82vh; border-radius: 12px; border: 1px solid var(--line); box-shadow: 0 24px 60px rgba(0,0,0,0.7); }
#lb-cap { margin-top: 12px; font-size: 14.5px; color: var(--text); text-align: center; max-width: 85ch; }

footer {
  margin-top: 48px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 13px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
}
</style>
</head>
<body>
<div class="wrap">

  <header class="hero">
    <div class="kicker">BakersfieldQuake · 1:1 Downtown Architectural Overhaul · Self-Contained Showcase</div>
    <h1>Historic Fox Theater, The Padre Hotel &amp; Downtown Bakersfield (<span class="mono">fox.bsp</span>)</h1>
    <p class="lead">
      Complete 1:1 scale (<span class="mono">12 u/ft</span>) architectural audit and custom asset expansion spanning G Street to K Street and 18th Street to 21st Street:
      <b>29 smooth-shaded 3D <span class="mono">.md3</span> props</b> (165 placed instances with emissive <span class="mono">_glow</span> shaders),
      <b>194 custom WAD &amp; PNG textures</b> including bespoke murals, boutique suite wallpapers, alpha-cutout signage, and full <span class="mono">BSP2</span> + <span class="mono">-extra4</span> colored <span class="mono">.lit</span> lighting.
    </p>

    <div class="stats-row">
      <div class="stat-box">
        <div class="big"><span>29</span> Custom 3D Models</div>
        <div class="lbl">165 placed <span class="mono">misc_model</span> props · 16,027 verts · 19,618 tris</div>
      </div>
      <div class="stat-box">
        <div class="big"><span>194</span> Map Textures</div>
        <div class="lbl">35 emissive <span class="mono">_glow</span> maps · 11 bespoke murals &amp; wallpapers</div>
      </div>
      <div class="stat-box">
        <div class="big"><span>115,200</span> World Tris</div>
        <div class="lbl">Compiled <span class="mono">BSP2</span> + <span class="mono">-extra4</span> colored <span class="mono">.lit</span> lightmaps (0 leaks)</div>
      </div>
      <div class="stat-box">
        <div class="big"><span>9</span> Playable Levels</div>
        <div class="lbl">Padre B1 24-Hr Gym through 8th-Floor Rooftop + Fox Auditorium &amp; Fly Grid</div>
      </div>
    </div>

    <div class="cta-bar">
      <div class="cta-group">
        <a class="btn gold" href="https://bakersfield.larrywew.fun/fox/" target="_blank" rel="noopener">🚶 Launch Live 3D Walk-Around Map Viewer</a>
        <a class="btn cyan" href="https://bakersfield.larrywew.fun/fox/fox_map_pack.zip">📦 Download fox_map_pack.zip</a>
        <a class="btn" href="#sec-museum">🧊 3D Prop Museum (29)</a>
        <a class="btn" href="#sec-tour">🏛️ Real vs. Quake Tour (23)</a>
        <a class="btn" href="#sec-art">🎨 Murals &amp; Wallpapers (19)</a>
      </div>
      <div class="cmd-pill">
        <span>Live Server:</span>
        <code id="srv-cmd" class="mono">connect 72.62.241.93:26000</code>
        <button type="button" class="tbtn" id="btn-copy">Copy</button>
      </div>
    </div>
  </header>

  <!-- ==================== SECTION 1: 3D PROP MUSEUM ==================== -->
  <div class="sec-head" id="sec-museum">
    <div>
      <h2>🧊 Interactive WebGL2 3D Prop Museum (All 29 Custom <span class="mono">.md3</span> Assets)</h2>
      <p>Drag to orbit 360&deg;, right-drag to pan, scroll wheel to zoom, or press <span class="mono">[</span> / <span class="mono">]</span> to cycle every custom Fox, Padre &amp; Downtown model.</p>
    </div>
    <div class="tabs" id="prop-tabs">
      <button type="button" class="tab active" data-zone="all">All Props (29)</button>
      <button type="button" class="tab" data-zone="fox">Fox Theater (6)</button>
      <button type="button" class="tab" data-zone="padre">The Padre Hotel (21)</button>
      <button type="button" class="tab" data-zone="downtown">Downtown Streetscape (2)</button>
    </div>
  </div>

  <section class="museum-grid">
    <div class="stage-shell" id="stage">
      <canvas id="gl"></canvas>
      <div class="stage-top">
        <div>
          <span class="pill gold mono" id="hud-file">progs/fox/fox_chandelier.md3</span>
          <span class="pill" id="hud-poly">0 verts · 0 tris</span>
          <span class="pill" id="hud-dims">0 × 0 × 0 ft</span>
          <span class="pill" id="hud-inst">×4 in map</span>
        </div>
        <div>
          <button type="button" class="tbtn" id="btn-spin" aria-pressed="true">↻ Auto-Spin</button>
          <button type="button" class="tbtn" id="btn-glow" aria-pressed="true">💡 Glow ON</button>
          <button type="button" class="tbtn" id="btn-wire" aria-pressed="false">🕸 Wireframe</button>
          <button type="button" class="tbtn" id="btn-lit">☀ Warm Hotel</button>
          <button type="button" class="tbtn" id="btn-full">⛶ Fullscreen</button>
        </div>
      </div>
      <div class="stage-bot">
        <div class="stage-info">
          <h3 id="hud-title">Loading 3D Arena…</h3>
          <p id="hud-desc">Decompressing embedded gzipped MD3 geometry &amp; textures…</p>
        </div>
        <div class="cam-row">
          <button type="button" class="tbtn" id="btn-prev">◀ Prev</button>
          <button type="button" class="tbtn" id="btn-next">Next ▶</button>
          <button type="button" class="tbtn" data-cam="hero">3/4</button>
          <button type="button" class="tbtn" data-cam="front">Front</button>
          <button type="button" class="tbtn" data-cam="side">Side</button>
          <button type="button" class="tbtn" data-cam="top">Top</button>
        </div>
      </div>
    </div>

    <div class="prop-roster">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <b style="font-size:13.5px;">Click Any Prop to Inspect in 3D</b>
        <span style="font-size:12px;color:var(--muted);" id="roster-count">Showing 29 of 29</span>
      </div>
      <div class="prop-list" id="prop-list"></div>
    </div>
  </section>

  <!-- ==================== SECTION 2: REAL VS IN-MAP TOUR ==================== -->
  <div class="sec-head" id="sec-tour">
    <div>
      <h2>🏛️ Real-World Bakersfield Reference vs. Compiled <span class="mono">fox.bsp</span> In-Map Tour</h2>
      <p>Click any reference photo or in-map render to zoom fullscreen, or jump straight to that exact camera spot in the live browser viewer.</p>
    </div>
    <div class="tabs" id="tour-tabs">
      <button type="button" class="tab active" data-tzone="all">All Scenes (23)</button>
      <button type="button" class="tab" data-tzone="fox">Fox Theater (7)</button>
      <button type="button" class="tab" data-tzone="padre">The Padre Hotel (11)</button>
      <button type="button" class="tab" data-tzone="downtown">Downtown Landmarks (5)</button>
    </div>
  </div>
  <section class="tour-grid" id="tour-grid"></section>

  <!-- ==================== SECTION 3: CUSTOM 2D ARTWORK & ATLASES ==================== -->
  <div class="sec-head" id="sec-art">
    <div>
      <h2>🎨 Custom Murals, Boutique Wallpapers, Alpha Signage &amp; 3D Texture Atlases</h2>
      <p>All 19 custom-painted murals, seamless wallpapers, alpha-tested signs, and 1024&times;1024 diffuse/emissive prop atlases embedded at native aspect ratio.</p>
    </div>
  </div>
  <section class="art-grid" id="art-grid"></section>

  <footer>
    <div><b>Historic Fox Theater &amp; The Padre Hotel (<span class="mono">fox.bsp</span>)</b> · Built for BakersfieldQuake (DarkPlaces / BSP2)</div>
    <div>100% Self-Contained Offline HTML Showcase · Live Walk-Around: <a href="https://bakersfield.larrywew.fun/fox/" style="color:var(--gold)">bakersfield.larrywew.fun/fox/</a></div>
  </footer>
</div>

<div id="lightbox" onclick="this.classList.remove('open')">
  <img id="lb-img" src="" alt="">
  <div id="lb-cap"></div>
</div>

<script>
const DATA = /*__FOX_SHOWCASE_DATA__*/null;
const $ = (id) => document.getElementById(id);

function openLightbox(uri, cap) {
  $("lb-img").src = uri;
  $("lb-cap").textContent = cap;
  $("lightbox").classList.add("open");
}
addEventListener("keydown", (e) => {
  if (e.key === "Escape") $("lightbox").classList.remove("open");
});

$("btn-copy").onclick = () => {
  navigator.clipboard?.writeText("connect 72.62.241.93:26000");
  $("btn-copy").textContent = "Copied!";
  setTimeout(() => { $("btn-copy").textContent = "Copy"; }, 1600);
};

// Render Comparison Tour
const tourGrid = $("tour-grid");
function renderTour(zone) {
  tourGrid.innerHTML = "";
  for (const item of DATA.tour) {
    if (zone !== "all" && item.zone !== zone) continue;
    const card = document.createElement("article");
    card.className = "tcard";
    const viewerUrl = "https://bakersfield.larrywew.fun/fox/?spot=" + encodeURIComponent(item.spot);
    card.innerHTML = `
      <div class="tpair">
        <figure class="tfig" data-uri="${item.refUri}" data-cap="Real Reference (${item.refName}) — ${item.title}">
          <span class="lbl">Real Photo</span>
          <img src="${item.refUri}" alt="${item.title} reference">
        </figure>
        <figure class="tfig" data-uri="${item.mapUri}" data-cap="Compiled fox.bsp + .lit + .md3 — ${item.title}">
          <span class="lbl map">In-Map fox.bsp</span>
          <img src="${item.mapUri}" alt="${item.title} in-map">
        </figure>
      </div>
      <div class="tbody">
        <div class="tbody-top">
          <span class="pcard" style="padding:0;border:0;background:none;cursor:default"><span class="ztag ${item.zone}">${item.zone}</span></span>
          <a class="tp-link" href="${viewerUrl}" target="_blank" rel="noopener">Teleport in 3D Viewer ↗</a>
        </div>
        <h3>${item.title}</h3>
        <p>${item.desc}</p>
      </div>`;
    card.querySelectorAll(".tfig").forEach((fg) => {
      fg.onclick = () => openLightbox(fg.dataset.uri, fg.dataset.cap);
    });
    tourGrid.appendChild(card);
  }
}
renderTour("all");
$("tour-tabs").querySelectorAll(".tab").forEach((b) => {
  b.onclick = () => {
    $("tour-tabs").querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === b));
    renderTour(b.dataset.tzone);
  };
});

// Render 2D Art Gallery
const artGrid = $("art-grid");
for (const a of DATA.art) {
  const el = document.createElement("div");
  el.className = "acard";
  el.innerHTML = `
    <div class="aimg"><img src="${a.uri}" alt="${a.code}"></div>
    <div class="abody">
      <div class="acode mono"><span>${a.code}</span><span style="color:var(--muted)">${a.dims}</span></div>
      <div class="acap">${a.caption}</div>
    </div>`;
  el.onclick = () => openLightbox(a.uri, `${a.code} (${a.cat}, ${a.dims}) — ${a.caption}`);
  artGrid.appendChild(el);
}

// ==================== WEBGL2 3D PROP MUSEUM ====================
async function gunzip(b64) {
  const bin = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const ds = new DecompressionStream("gzip");
  const w = ds.writable.getWriter();
  w.write(bin);
  w.close();
  return await new Response(ds.readable).arrayBuffer();
}

function mat4Persp(out, fovy, aspect, near, far) {
  const f = 1.0 / Math.tan(fovy * 0.5), nf = 1.0 / (near - far);
  out.fill(0);
  out[0] = f / aspect; out[5] = f; out[10] = (far + near) * nf; out[11] = -1; out[14] = 2 * far * near * nf;
  return out;
}
function mat4LookAt(out, eye, ctr, up) {
  let zx = eye[0]-ctr[0], zy = eye[1]-ctr[1], zz = eye[2]-ctr[2];
  let l = Math.hypot(zx, zy, zz) || 1; zx/=l; zy/=l; zz/=l;
  let xx = up[1]*zz - up[2]*zy, xy = up[2]*zx - up[0]*zz, xz = up[0]*zy - up[1]*zx;
  l = Math.hypot(xx, xy, xz) || 1; xx/=l; xy/=l; xz/=l;
  const yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;
  out[0]=xx; out[1]=yx; out[2]=zx; out[3]=0;
  out[4]=xy; out[5]=yy; out[6]=zy; out[7]=0;
  out[8]=xz; out[9]=yz; out[10]=zz; out[11]=0;
  out[12]=-(xx*eye[0]+xy*eye[1]+xz*eye[2]);
  out[13]=-(yx*eye[0]+yy*eye[1]+yz*eye[2]);
  out[14]=-(zx*eye[0]+zy*eye[1]+zz*eye[2]);
  out[15]=1;
  return out;
}
function mat4Mul(out, a, b) {
  const r = new Float32Array(16);
  for (let c = 0; c < 4; c++) {
    for (let rw = 0; rw < 4; rw++) {
      r[c*4+rw] = a[0*4+rw]*b[c*4+0] + a[1*4+rw]*b[c*4+1] + a[2*4+rw]*b[c*4+2] + a[3*4+rw]*b[c*4+3];
    }
  }
  out.set(r);
  return out;
}

(async function boot3D() {
  const canvas = $("gl");
  const gl = canvas.getContext("webgl2", { antialias: true, alpha: false });
  if (!gl) {
    $("hud-title").textContent = "WebGL2 Unavailable";
    return;
  }
  const AB = await gunzip(DATA.binGz);

  function prog(vs, fs) {
    const p = gl.createProgram();
    for (const [tp, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const s = gl.createShader(tp);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      gl.attachShader(p, s);
    }
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  }

  const pSky = prog(`#version 300 es
    precision highp float;
    precision highp int;
    layout(location=0) in vec2 aQ;
    out vec2 vUv;
    void main() { vUv = aQ * 0.5 + 0.5; gl_Position = vec4(aQ, 0.9999, 1.0); }`,
    `#version 300 es
    precision highp float;
    precision highp int;
    in vec2 vUv;
    uniform int uLit;
    out vec4 fragColor;
    void main() {
      vec3 top = uLit == 0 ? vec3(0.11, 0.08, 0.16) : vec3(0.07, 0.18, 0.36);
      vec3 bot = uLit == 0 ? vec3(0.20, 0.13, 0.11) : vec3(0.14, 0.28, 0.44);
      fragColor = vec4(mix(bot, top, smoothstep(0.0, 1.0, vUv.y)), 1.0);
    }`);

  const pGrid = prog(`#version 300 es
    precision highp float;
    precision highp int;
    layout(location=0) in vec2 aQ;
    uniform mat4 uVP;
    uniform float uZ;
    uniform float uRad;
    out vec2 vP;
    void main() { vP = aQ * uRad; gl_Position = uVP * vec4(vP, uZ, 1.0); }`,
    `#version 300 es
    precision highp float;
    precision highp int;
    in vec2 vP;
    uniform float uRad;
    out vec4 fragColor;
    void main() {
      vec2 q = vP / 12.0;
      float chk = mod(floor(q.x) + floor(q.y), 2.0);
      vec2 g = abs(fract(q - 0.5) - 0.5) / fwidth(q);
      float ln = 1.0 - min(min(g.x, g.y), 1.0);
      float fade = 1.0 - smoothstep(uRad * 0.28, uRad * 0.95, length(vP));
      vec3 col = mix(vec3(0.10, 0.13, 0.20), vec3(0.14, 0.18, 0.27), chk) + vec3(0.25, 0.20, 0.10) * ln * 0.25;
      fragColor = vec4(col, fade * 0.85);
    }`);

  const pMesh = prog(`#version 300 es
    precision highp float;
    precision highp int;
    layout(location=0) in vec3 aPos;
    layout(location=1) in vec3 aNrm;
    layout(location=2) in vec2 aUv;
    uniform mat4 uVP;
    uniform float uYaw;
    uniform int uShadow;
    uniform float uFloorZ;
    out vec3 vPos;
    out vec3 vNrm;
    out vec2 vUv;
    void main() {
      float c = cos(uYaw), s = sin(uYaw);
      vec3 p = vec3(c * aPos.x - s * aPos.y, s * aPos.x + c * aPos.y, aPos.z);
      vec3 n = vec3(c * aNrm.x - s * aNrm.y, s * aNrm.x + c * aNrm.y, aNrm.z);
      if (uShadow == 1) {
        float h = max(0.0, p.z - uFloorZ);
        vec3 sp = vec3(p.x - 0.26 * h, p.y + 0.22 * h, uFloorZ + 0.08);
        vPos = sp; vNrm = vec3(0,0,1); vUv = aUv;
        gl_Position = uVP * vec4(sp, 1.0);
      } else {
        vPos = p; vNrm = n; vUv = aUv;
        gl_Position = uVP * vec4(p, 1.0);
      }
    }`,
    `#version 300 es
    precision highp float;
    precision highp int;
    in vec3 vPos;
    in vec3 vNrm;
    in vec2 vUv;
    uniform sampler2D uTex;
    uniform sampler2D uGlow;
    uniform vec3 uEye;
    uniform int uLit;
    uniform int uUseGlow;
    uniform int uShadow;
    out vec4 fragColor;
    void main() {
      if (uShadow == 1) {
        fragColor = vec4(0.02, 0.03, 0.06, 0.36);
        return;
      }
      vec3 base = texture(uTex, vUv).rgb;
      vec3 glow = uUseGlow == 1 ? texture(uGlow, vUv).rgb : vec3(0.0);
      if (uLit == 2) {
        fragColor = vec4(base + glow, 1.0);
        return;
      }
      vec3 N = normalize(gl_FrontFacing ? vNrm : -vNrm);
      vec3 V = normalize(uEye - vPos);
      vec3 L1 = normalize(vec3(0.52, -0.44, 0.73));
      vec3 L2 = normalize(vec3(-0.65, 0.52, 0.55));
      vec3 c1 = uLit == 0 ? vec3(1.22, 0.98, 0.76) : vec3(1.10, 1.08, 1.02);
      vec3 c2 = uLit == 0 ? vec3(0.42, 0.50, 0.72) : vec3(0.52, 0.68, 0.88);
      vec3 hemi = mix(vec3(0.24, 0.24, 0.30), vec3(0.46, 0.48, 0.56), 0.5 + 0.5 * N.z);
      vec3 diff = hemi + c1 * max(dot(N, L1), 0.0) * 0.85 + c2 * max(dot(N, L2), 0.0) * 0.38;
      float sp = pow(max(dot(N, normalize(L1 + V)), 0.0), 34.0) * 0.26;
      vec3 col = base * diff + c1 * sp + glow * 1.35;
      col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
      fragColor = vec4(col, 1.0);
    }`);

  const pWire = prog(`#version 300 es
    precision highp float;
    precision highp int;
    layout(location=0) in vec3 aPos;
    uniform mat4 uVP;
    uniform float uYaw;
    void main() {
      float c = cos(uYaw), s = sin(uYaw);
      vec3 p = vec3(c * aPos.x - s * aPos.y, s * aPos.x + c * aPos.y, aPos.z);
      gl_Position = uVP * vec4(p, 1.0);
    }`,
    `#version 300 es
    precision highp float;
    out vec4 fragColor;
    void main() { fragColor = vec4(0.98, 0.82, 0.32, 0.72); }`);

  function mkBuf(target, arr) {
    const b = gl.createBuffer();
    gl.bindBuffer(target, b);
    gl.bufferData(target, arr, gl.STATIC_DRAW);
    return b;
  }

  const quadVao = gl.createVertexArray();
  gl.bindVertexArray(quadVao);
  mkBuf(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]));
  gl.enableVertexAttribArray(0);
  gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

  const glTex = DATA.textures.map((t) => {
    const tx = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tx);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([90,80,70,255]));
    const im = new Image();
    im.onload = () => {
      gl.bindTexture(gl.TEXTURE_2D, tx);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    };
    im.src = t.uri;
    return tx;
  });

  // Upload all 29 MD3 models to VAOs
  for (const m of DATA.models) {
    for (const s of m.surfaces) {
      s.vao = gl.createVertexArray();
      gl.bindVertexArray(s.vao);
      mkBuf(gl.ARRAY_BUFFER, new Float32Array(AB, s.pos[0], s.pos[1] >> 2));
      gl.enableVertexAttribArray(0);
      gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
      mkBuf(gl.ARRAY_BUFFER, new Int8Array(AB, s.nrm[0], s.nrm[1]));
      gl.enableVertexAttribArray(1);
      gl.vertexAttribPointer(1, 3, gl.BYTE, true, 4, 0);
      mkBuf(gl.ARRAY_BUFFER, new Float32Array(AB, s.uv[0], s.uv[1] >> 2));
      gl.enableVertexAttribArray(2);
      gl.vertexAttribPointer(2, 2, gl.FLOAT, false, 0, 0);
      s.ibTris = mkBuf(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(AB, s.tris[0], s.tris[1] >> 1));
      s.ibEdges = mkBuf(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(AB, s.edges[0], s.edges[1] >> 1));
    }
  }

  const state = { idx: 0, spin: true, glow: true, wire: false, lit: 0, modelYaw: 0 };
  const cam = { az: -0.68, el: 0.30, dist: 120, panX: 0, panY: 0, panZ: 24, radius: 40, floorZ: 0 };

  function fitModel(m) {
    const cx = 0.5 * (m.bmin[0] + m.bmax[0]);
    const cy = 0.5 * (m.bmin[1] + m.bmax[1]);
    const cz = 0.5 * (m.bmin[2] + m.bmax[2]);
    const dx = m.bmax[0] - m.bmin[0], dy = m.bmax[1] - m.bmin[1], dz = m.bmax[2] - m.bmin[2];
    const span = Math.max(dx, dy, dz, 12);
    cam.panX = cx; cam.panY = cy; cam.panZ = cz;
    cam.radius = span;
    cam.dist = span * 1.72;
    cam.az = -0.68;
    cam.el = m.ceiling ? -0.16 : 0.28;
    cam.floorZ = m.ceiling ? m.bmax[2] : m.bmin[2];
    state.modelYaw = 0;

    $("hud-file").textContent = `progs/fox/${m.id}.md3`;
    $("hud-poly").textContent = `${m.nv.toLocaleString()} verts · ${m.nt.toLocaleString()} tris`;
    $("hud-dims").textContent = `${(dx/12).toFixed(1)} × ${(dy/12).toFixed(1)} × ${(dz/12).toFixed(1)} ft`;
    $("hud-inst").textContent = `×${m.count} in fox.bsp`;
    $("hud-title").textContent = m.title;
    $("hud-desc").textContent = m.desc;
  }

  const listEl = $("prop-list");
  let activeZone = "all";
  function renderRoster() {
    listEl.innerHTML = "";
    let shown = 0;
    DATA.models.forEach((m, i) => {
      if (activeZone !== "all" && m.zone !== activeZone) return;
      shown++;
      const b = document.createElement("button");
      b.type = "button";
      b.className = "pcard" + (i === state.idx ? " active" : "");
      b.dataset.idx = i;
      b.innerHTML = `
        <div class="ptop">
          <span class="ztag ${m.zone}">${m.zone}</span>
          <span class="cnt">×${m.count} placed</span>
        </div>
        <div class="pname">${m.title}</div>
        <div class="pmeta mono">${m.id}.md3 · ${m.nt} tris</div>`;
      b.onclick = () => selectModel(i);
      listEl.appendChild(b);
    });
    $("roster-count").textContent = `Showing ${shown} of ${DATA.models.length}`;
  }

  function selectModel(i) {
    state.idx = (i + DATA.models.length) % DATA.models.length;
    fitModel(DATA.models[state.idx]);
    listEl.querySelectorAll(".pcard").forEach((b) => b.classList.toggle("active", +b.dataset.idx === state.idx));
  }

  $("prop-tabs").querySelectorAll(".tab").forEach((b) => {
    b.onclick = () => {
      activeZone = b.dataset.zone;
      $("prop-tabs").querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === b));
      renderRoster();
    };
  });

  $("btn-prev").onclick = () => selectModel(state.idx - 1);
  $("btn-next").onclick = () => selectModel(state.idx + 1);
  addEventListener("keydown", (e) => {
    if (e.key === "[") selectModel(state.idx - 1);
    if (e.key === "]") selectModel(state.idx + 1);
  });

  $("btn-spin").onclick = () => { state.spin = !state.spin; $("btn-spin").setAttribute("aria-pressed", state.spin); };
  $("btn-glow").onclick = () => {
    state.glow = !state.glow;
    $("btn-glow").setAttribute("aria-pressed", state.glow);
    $("btn-glow").textContent = state.glow ? "💡 Glow ON" : "💡 Glow OFF";
  };
  $("btn-wire").onclick = () => { state.wire = !state.wire; $("btn-wire").setAttribute("aria-pressed", state.wire); };
  const litLabels = ["☀ Warm Hotel", "🌤 Daylight", "🎨 Unlit Atlas"];
  $("btn-lit").onclick = () => {
    state.lit = (state.lit + 1) % 3;
    $("btn-lit").textContent = litLabels[state.lit];
  };
  $("btn-full").onclick = () => $("stage").classList.toggle("fullscreen");

  document.querySelectorAll("[data-cam]").forEach((b) => {
    b.onclick = () => {
      fitModel(DATA.models[state.idx]);
      const k = b.dataset.cam;
      if (k === "front") { cam.az = 0; cam.el = 0.14; }
      else if (k === "side") { cam.az = -Math.PI / 2; cam.el = 0.14; }
      else if (k === "top") { cam.az = -0.5; cam.el = 1.28; }
    };
  });

  // Pointer Orbit / Pan / Zoom
  const stage = $("stage");
  stage.addEventListener("contextmenu", (e) => e.preventDefault());
  let drag = null;
  stage.addEventListener("pointerdown", (e) => {
    if (e.target.closest("button")) return;
    stage.setPointerCapture(e.pointerId);
    stage.classList.add("drag");
    drag = { id: e.pointerId, x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey };
  });
  stage.addEventListener("pointermove", (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    drag.x = e.clientX; drag.y = e.clientY;
    if (drag.pan) {
      const s = cam.dist * 0.0016;
      cam.panX -= (-Math.sin(cam.az) * dx) * s;
      cam.panY -= ( Math.cos(cam.az) * dx) * s;
      cam.panZ += dy * s;
    } else {
      cam.az -= dx * 0.0085;
      cam.el = Math.max(-1.42, Math.min(1.42, cam.el + dy * 0.0085));
    }
  });
  const endDrag = () => { drag = null; stage.classList.remove("drag"); };
  stage.addEventListener("pointerup", endDrag);
  stage.addEventListener("pointercancel", endDrag);
  stage.addEventListener("wheel", (e) => {
    e.preventDefault();
    cam.dist = Math.max(cam.radius * 0.45, Math.min(cam.radius * 5.0, cam.dist * Math.exp(e.deltaY * 0.0012)));
  }, { passive: false });

  renderRoster();
  selectModel(0);

  const mP = new Float32Array(16), mV = new Float32Array(16), mVP = new Float32Array(16);
  let lastT = performance.now();

  function frame(now) {
    const dt = Math.min(0.05, (now - lastT) / 1000);
    lastT = now;
    if (state.spin && !drag) state.modelYaw += dt * 0.55;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(2, Math.floor(canvas.clientWidth * dpr));
    const h = Math.max(2, Math.floor(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    gl.viewport(0, 0, w, h);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    // 1. Sky backdrop
    gl.disable(gl.DEPTH_TEST);
    gl.useProgram(pSky);
    gl.uniform1i(gl.getUniformLocation(pSky, "uLit"), state.lit);
    gl.bindVertexArray(quadVao);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    // Camera matrices (Quake Z-up)
    const ce = Math.cos(cam.el), se = Math.sin(cam.el);
    const eye = [
      cam.panX + cam.dist * ce * Math.cos(cam.az),
      cam.panY + cam.dist * ce * Math.sin(cam.az),
      cam.panZ + cam.dist * se,
    ];
    mat4Persp(mP, 44 * Math.PI / 180, w / h, Math.max(0.5, cam.radius * 0.03), cam.radius * 18.0);
    mat4LookAt(mV, eye, [cam.panX, cam.panY, cam.panZ], [0, 0, 1]);
    mat4Mul(mVP, mP, mV);

    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

    const cur = DATA.models[state.idx];

    // 2. Floor / Ceiling Reference Grid
    gl.depthMask(false);
    gl.useProgram(pGrid);
    gl.uniformMatrix4fv(gl.getUniformLocation(pGrid, "uVP"), false, mVP);
    gl.uniform1f(gl.getUniformLocation(pGrid, "uZ"), cam.floorZ);
    gl.uniform1f(gl.getUniformLocation(pGrid, "uRad"), Math.max(96, cam.radius * 2.2));
    gl.bindVertexArray(quadVao);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    // 3. Soft Ground Planar Shadow (for floor props)
    if (!cur.ceiling) {
      gl.useProgram(pMesh);
      gl.uniformMatrix4fv(gl.getUniformLocation(pMesh, "uVP"), false, mVP);
      gl.uniform1f(gl.getUniformLocation(pMesh, "uYaw"), state.modelYaw);
      gl.uniform1i(gl.getUniformLocation(pMesh, "uShadow"), 1);
      gl.uniform1f(gl.getUniformLocation(pMesh, "uFloorZ"), cam.floorZ);
      for (const s of cur.surfaces) {
        gl.bindVertexArray(s.vao);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.ibTris);
        gl.drawElements(gl.TRIANGLES, s.nt * 3, gl.UNSIGNED_SHORT, 0);
      }
    }
    gl.depthMask(true);
    gl.disable(gl.BLEND);

    // 4. Shaded 3D MD3 Surfaces + Glow
    gl.useProgram(pMesh);
    gl.uniformMatrix4fv(gl.getUniformLocation(pMesh, "uVP"), false, mVP);
    gl.uniform1f(gl.getUniformLocation(pMesh, "uYaw"), state.modelYaw);
    gl.uniform3fv(gl.getUniformLocation(pMesh, "uEye"), eye);
    gl.uniform1i(gl.getUniformLocation(pMesh, "uLit"), state.lit);
    gl.uniform1i(gl.getUniformLocation(pMesh, "uUseGlow"), state.glow ? 1 : 0);
    gl.uniform1i(gl.getUniformLocation(pMesh, "uShadow"), 0);
    gl.uniform1i(gl.getUniformLocation(pMesh, "uTex"), 0);
    gl.uniform1i(gl.getUniformLocation(pMesh, "uGlow"), 1);

    for (const s of cur.surfaces) {
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, glTex[s.tex]);
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D, glTex[s.glow]);
      gl.bindVertexArray(s.vao);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.ibTris);
      gl.drawElements(gl.TRIANGLES, s.nt * 3, gl.UNSIGNED_SHORT, 0);
    }

    // 5. Optional Wireframe Overlay
    if (state.wire) {
      gl.enable(gl.BLEND);
      gl.useProgram(pWire);
      gl.uniformMatrix4fv(gl.getUniformLocation(pWire, "uVP"), false, mVP);
      gl.uniform1f(gl.getUniformLocation(pWire, "uYaw"), state.modelYaw);
      for (const s of cur.surfaces) {
        gl.bindVertexArray(s.vao);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.ibEdges);
        gl.drawElements(gl.LINES, s.ne * 2, gl.UNSIGNED_SHORT, 0);
      }
      gl.disable(gl.BLEND);
    }

    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
