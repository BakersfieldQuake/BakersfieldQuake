"""Builds BakersfieldQuake/bklan_accuracy_report.html: a self-contained HTML accuracy audit and before/after proof
page for the unified `bklan` Quake map (including the merged ORCOM CONNECT LAN PARTY building on Sonora St).

Usage:
    python build_accuracy_report.py [scratch_dir]
"""
import base64
import html
import io
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", ".."))
DEFAULT_SCRATCH = r"C:\Users\qxdc\.gemini\antigravity\brain\b7d7f00c-36c9-4360-8285-49d486fd34de\scratch"
SCR = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SCRATCH
OUT = os.path.join(MOD, "bklan_accuracy_report.html")

GAL = os.path.join(SCR, "gallery")
BKF = os.path.join(SCR, "bklan_frames")
OCF = os.path.join(SCR, "orcom_frames")
RV1 = os.path.join(SCR, "rev1_frames")
RV2 = os.path.join(SCR, "rev2_frames")
REF_V2 = os.path.join(HERE, "ref_v2")
REF_OC = os.path.join(HERE, "ref_orcom")
BEF = os.path.join(SCR, "before_shots")
AFT = os.path.join(SCR, "after_shots")

img_count = [0]


def uri(path, maxw=960, q=82):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing report image: {path}")
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (24, 24, 24))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.getchannel("A"))
        im = bg
    im = im.convert("RGB")
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=q)
    img_count[0] += 1
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def card(idx, shot_id, title, rank_badge, source_label, ref_path, diff_text, fix_text):
    bef_path = os.path.join(BEF, f"{shot_id}.png")
    aft_path = os.path.join(AFT, f"{shot_id}.png")
    return f"""
    <article class="audit-card" id="shot-{shot_id}">
      <div class="card-head">
        <div>
          <span class="num">#{idx:02d}</span>
          <h3>{html.escape(title)}</h3>
        </div>
        <span class="badge">{html.escape(rank_badge)}</span>
      </div>
      <p class="src"><strong>Source:</strong> {source_label}</p>
      <div class="grid g3">
        <figure>
          <span class="tag tag-ref">Real Source</span>
          <img loading="lazy" src="{uri(ref_path)}" alt="Source for {html.escape(shot_id)}">
          <figcaption>{html.escape(os.path.basename(ref_path))}</figcaption>
        </figure>
        <figure>
          <span class="tag tag-bef">Before</span>
          <img loading="lazy" src="{uri(bef_path)}" alt="Before {html.escape(shot_id)}">
          <figcaption>Baseline (<code>{"orcom.bsp" if shot_id >= "20_" else "bklan.bsp"}</code> before audit)</figcaption>
        </figure>
        <figure>
          <span class="tag tag-aft">After</span>
          <img loading="lazy" src="{uri(aft_path)}" alt="After {html.escape(shot_id)}">
          <figcaption>Unified <code>bklan.bsp</code> after fix</figcaption>
        </figure>
      </div>
      <div class="notes">
        <p><strong>Audit finding:</strong> {diff_text}</p>
        <p><strong>Generator fix:</strong> {fix_text}</p>
      </div>
    </article>"""


SECTIONS = [
    (
        "block",
        "1. 118 E 21st St, Surrounding Block, Sacramento St & GCI / Capri Motel",
        "Street View gallery (Feb 2026, ~100 photos), OpenStreetMap / Bakersfield GIS footprints, and owner review videos "
        "(<code>2026-10-30 17-40-08.mp4</code> &amp; <code>22-56-37.mp4</code>).",
        [
            (
                1, "01_118_front", "118 / 120 E 21st St South-West Front Facade (Preserved Baseline Check)",
                "Baseline Verified · High Certainty",
                "Street View <code>sv-front-118e21st-...-yaw45.jpg</code> (Feb 2026)",
                os.path.join(GAL, "sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw45.jpg"),
                "Verified established facts: 118/120 E 21st St faces south-west with its tall blank cream fascia parapet, "
                "dark storefront windows, red/blue painted piers on the east storefront, and only the legible signs "
                "<code>BATERIAS $55</code>, <code>120A</code>, and <code>120B</code>.",
                "Preserved all established facade proportions and signage in <code>make_bklan.py</code> while converting "
                "ground-flush road/sidewalk slabs to <code>func_detail</code>.",
            ),
            (
                2, "02_e21_south_121", "South Side of E 21st St: #105 Performance Driveline & #1 (121 E. 21st Breeze-Block Yard)",
                "Rank #2 · High Visibility · High Certainty",
                "Street View <code>sv-front-118e21st-...-yaw135.jpg</code> &amp; <code>yaw180.jpg</code> (Feb 2026)",
                os.path.join(GAL, "sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw180.jpg"),
                "Across from 118 E 21st, OSM building #1 was rendered as a generic brown industrial warehouse, whereas "
                "2026 Street View shows that warehouse was demolished into an open dirt salvage yard behind a distinctive "
                "7-bay tan quatrefoil breeze-block wall (<code>121 E. 21st</code>) with a grey modular office trailer inside "
                "and a red ladder-rack utility pickup at the curb. Next door (#105, Performance Driveline) was plain tan "
                "instead of bright red corrugated metal with a black sloped front awning.",
                "Replaced #1 with the open dirt yard, 7 bays of alpha-tested <code>{lattice</code> breeze-block wall + "
                "<code>bk_121sign</code>, slid iron gate, modular trailer, salvage cars, and ladder-rack pickup; styled #105 "
                "with <code>bk_redcorr</code>, black sloped prism awning, dark windows, and <code>bk_pdsign</code>.",
            ),
            (
                3, "03_110_gci", "110 E 21st St (J Appliances) & GCI Equipment Rental Boom-Lift Fleet",
                "Rank #3 · High Visibility · High Certainty",
                "Street View <code>sv-west-110e21st-...-yaw0.jpg</code> &amp; <code>22-56-37.mp4</code> (<code>118 s</code>)",
                os.path.join(GAL, "sv-west-110e21st-pano-3JI52yTJxq_XrO4WDd2NCQ-yaw0.jpg"),
                "Building #2 (<code>110 E 21st St</code>) was in the <code>HEROES</code> skip set without hand-built geometry, "
                "leaving an empty asphalt gap west of 118 E 21st! West of #2, the GCI Equipment Rental yard lacked its black "
                "wrought-iron fence, grass parkway, white service pickups, and rows of bright blue Genie boom lifts.",
                "Built #2 (<code>110 E 21st St</code>) in ribbed tan metal (<code>bk_110tan</code>) with overhanging cream "
                "fascia, cropped yellow <code>APPLIANCES</code> banner (<code>bk_110sale</code>), dark windows, and yucca "
                "planter; added GCI's grass parkway, iron fence, white service pickups, tan telehandlers, and 32 blue boom lifts.",
            ),
            (
                4, "04_capri_motel", "Capri Motel NW Corner Monument Wall, Yellow Marquee, Pitched Roofs & GCI Corner",
                "Rank #4 · High Visibility · High Certainty",
                "Owner review video <code>2026-10-30 22-56-37.mp4</code> at <code>118 s</code> (<code>ref_v2/118.jpg</code>)",
                os.path.join(REF_V2, "118.jpg"),
                "At the W 21st / Union corner, Capri Motel (#7) had flat roofs and lacked its tall salmon/tan corner monument "
                "wall (<code>Capri MOTEL</code> in red script), yellow rectangular marquee sign, brick/hedge planter, 2nd-floor "
                "balcony walkway, and corner traffic signal mast arm; across the street, GCI lacked its blue pylon sign and "
                "lavender floral utility box.",
                "Added <code>bk_capriwall</code> monument on brick/hedge base, <code>bk_capriylw</code> marquee, brown shingle "
                "<code>hiproof</code> roofs on #7, 2nd-floor balcony + iron railing, traffic signal mast arm, and GCI's "
                "<code>bk_gcisign</code> pylon + <code>bk_floralbox</code> utility cabinet.",
            ),
            (
                5, "05_sac_celeb", "Building 45 (Celebrity Bodyworks) Sacramento St Bands, White North Sign Wall & Gate",
                "Rank #5 · High Visibility · High Certainty",
                "Street View <code>sv-sacramento-848-...-yaw270.jpg</code> &amp; <code>yaw225.jpg</code>",
                os.path.join(GAL, "sv-sacramento-848-pano-0xhYYQLO2ibyNjLvSd2Lgw-yaw270.jpg"),
                "Building 45's east wall on Sacramento St was painted solid red end-to-end with the <code>Celebrity</code> "
                "sign placed on the red east wall. Street View proves the Sacramento wall has white south/mid bays, a bright "
                "green shop bay, a projecting white SE corner canopy, and red north bay, while the colorful <code>Celebrity</code> "
                "sign sits on Building 45's <em>white north wall</em> facing the half-iron / half-white-slatted BODY SHOP yard.",
                "Rebuilt Building 45's Sacramento St wall bands (white, green, white, red + door placards + silver fire hydrant "
                "and red curb), added the SE corner white canopy, moved <code>bk_celeb</code> to the white north wall, built "
                "the half-iron / half-white-slatted yard fence, and added #74's low-pitch metal roof + vent pipe.",
            ),
        ],
    ),
    (
        "lan130a",
        "2. LAN Lot & Unit 130A Interior / Back Room (B-LAN 2001)",
        "Compared frame-by-frame against <code>D:\\Local\\Video\\Capture Homevids\\bklan.wmv</code> (53 min, 320&times;240).",
        [
            (
                6, "06_lan_lot_north", "LAN Lot Looking North: Striped Delineators, STOP & UNION AVE Street Signs",
                "Rank #9 · Medium Visibility · High Certainty",
                "<code>bklan.wmv</code> at <code>1325 s</code> (<code>01326.jpg</code>) &amp; <code>64–68 s</code>",
                os.path.join(BKF, "01326.jpg"),
                "The traffic cones in the lot and hall were plain solid-orange rectangular posts without reflective white "
                "bands or dark bases, and the north end of the lot lacked the octagonal red <code>STOP</code> sign and green "
                "<code>UNION AVE &rarr;</code> sign visible at <code>1325 s</code>.",
                "Upgraded <code>cone()</code> with dark rubber bases and dual white reflective bands (<code>bk_conestr</code>), "
                "added the mid-building white canopy on Building 45's west wall (<code>1324 s</code>), and placed the steel-post "
                "<code>bk_stop</code> and <code>bk_unionsn</code> signs at the north wall.",
            ),
            (
                7, "07_130a_ext", "Unit 130A Exterior: Cone-Mounted Foil/Cardboard B-LAN Sign & Tan Commercial Dumpster",
                "Rank #7 · High Visibility · High Certainty",
                "<code>bklan.wmv</code> at <code>1334 s</code> (<code>01335.jpg</code>) &amp; <code>58 s</code>",
                os.path.join(BKF, "01335.jpg"),
                "The hand-drawn <code>B-LAN / 130A / ENTER &rarr;</code> sign was pasted flat onto the masonry pier, whereas "
                "<code>1334 s</code> shows it is a cardboard placard wrapped in aluminum foil at the top and mounted atop a "
                "tall striped delineator cone outside the door; also, the tan/mustard commercial dumpster with black plastic "
                "lid right south of 130A (<code>58 s</code>, <code>1110 s</code>) was missing.",
                "Modeled the 3D cardboard-and-foil <code>bk_blansign</code> assembly atop a striped delineator cone outside "
                "130A, shifted the crate stair stack south, and added the <code>bk_dumpster</code> bin with black lid.",
            ),
            (
                8, "08_lan_hall_in", "Unit 130A Main LAN Hall Looking In from Roll-Up Door",
                "Baseline + Prop Detail · High Certainty",
                "<code>bklan.wmv</code> at <code>2020–2024 s</code> (<code>02021.jpg</code>)",
                os.path.join(BKF, "02021.jpg"),
                "Checked hall orientation, joists, parallel strip lights, galvanized supply duct + flared diffuser drop, "
                "south &amp; north PC rows, wooden podium, and drinks table.",
                "Preserved verified hall geometry and lighting (<code>290</code> tube strips) while adding the Razor kick "
                "scooters and striped delineator cones near the entrance.",
            ),
            (
                9, "09_lan_panel_jamb", "Unit 130A Roll-Up Jamb, Open Breaker Panel, Drinks Table & Razor Kick Scooters",
                "Rank #10 · Medium Visibility · High Certainty",
                "<code>bklan.wmv</code> at <code>2484–2494 s</code> (<code>02485.jpg</code>) &amp; <code>84–90 s</code>",
                os.path.join(BKF, "02485.jpg"),
                "At <code>2484–2494 s</code>, attendees ride and park silver-and-red Razor kick scooters on the concrete floor "
                "by the roll-up door and drinks table; these iconic 2001 LAN props were missing, and the doorway cones lacked "
                "white reflective stripes.",
                "Added two non-blocking (<code>func_detail_illusionary</code>) silver aluminum Razor scooters with red wheels "
                "and red foam handlebar grips near the roll-up entrance alongside the striped delineator cones.",
            ),
            (
                10, "10_lan_backroom", "Unit 130A Back Room: Enclosed Corner Bathroom, Toilet, 2 Cones & Folded Metal Cots",
                "Rank #6 · High Visibility · High Certainty",
                "<code>bklan.wmv</code> at <code>2710–2714 s</code> (<code>02711.jpg</code>, <code>02712.jpg</code>)",
                os.path.join(BKF, "02711.jpg"),
                "The back room was missing its enclosed south-east corner bathroom (<code>2711–2712 s</code>: cream partition "
                "walls, inward-swung white door, white porcelain toilet + tank + floor tissue rolls inside), the pair of tall "
                "striped traffic cones standing right outside the bathroom jamb, and the folded dark-metal tubular bed/cot "
                "frames leaning against the cream back wall.",
                "Built the enclosed 9.2 ft corner bathroom with open <code>bk_door</code>, porcelain toilet, floor rolls, and "
                "interior light; placed two striped cones outside the jamb and two leaning tubular metal cot frames + white "
                "bucket along the wall (clearing all spawns and items in <code>check_placed()</code>).",
            ),
        ],
    ),
    (
        "palace",
        "3. Bakersfield Sign, Sillect Ave & Buck Owens' Crystal Palace",
        "Compared against <code>2026-10-30 22-56-37.mp4</code> (<code>0–105 s</code>), Street View stills in <code>ref_v2/</code>, "
        "and OSM site geometry (<code>bklan_site_palace.json</code>).",
        [
            (
                11, "11_bf_sign_west", "Bakersfield Sign Arch Over Sillect Ave (Looking East) & 2-Tone 4-Storey Office",
                "Rank #11 · Medium Visibility · High Certainty",
                "<code>22-56-37.mp4</code> at <code>0 s</code> (<code>ref_v2/0.jpg</code>) &amp; <code>bklan_sign.py</code>",
                os.path.join(REF_V2, "0.jpg"),
                "Verified measured sign dimensions (97 ft tower c-c, 62 ft road, 31 ft roof peak, ~4.7 ft letters). The north "
                "4-storey office building used a uniform bright cream facade on all 4 floors instead of darker grey-brown band "
                "masonry on floors 1–2 and cream upper bands + cornice on floors 3–4; the south tower lacked its shaped green "
                "hedge and wrought-iron lot fence.",
                "Split the 4-storey Sillect office into <code>bk_officedk</code> (floors 1–2) and <code>bk_office</code> "
                "(floors 3–4) with overhanging cornice, and added the shaped hedge round the south tower plus Sillect iron fence.",
            ),
            (
                12, "12_bf_sign_east", "Bakersfield Sign East Approach Looking West Toward Buck Owens Blvd",
                "Rank #12 · Medium Visibility · High Certainty",
                "<code>22-56-37.mp4</code> at <code>14 s</code> (<code>ref_v2/14.jpg</code>)",
                os.path.join(REF_V2, "14.jpg"),
                "Verified east-side arch lettering, tower emblems, 2-tone north office facade, and high curved street-light "
                "luminaire arms rising above the Buck Owens / Sillect traffic signal poles.",
                "Added high luminaire mast extensions (<code>z = 29.5 ft</code>) above all four Buck Owens &amp; Sillect "
                "signal poles and extended the wrought-iron perimeter fence.",
            ),
            (
                13, "13_palace_north", "Crystal Palace North Service Drive, 2-Storey KUZZ Porte-Cochere & KUZZ Radio Van",
                "Rank #8 · High Visibility · High Certainty",
                "<code>22-56-37.mp4</code> at <code>69 s</code> (<code>ref_v2/69.jpg</code>, @35.3859219,-119.0427674)",
                os.path.join(REF_V2, "69.jpg"),
                "At <code>69 s</code>, the owner pauses on the north side of Buck Owens' Crystal Palace showing the 2-storey "
                "covered porte-cochere / balcony with tan columns, brown hip roof, upper railing, and a dark blue/white "
                "<code>KUZZ</code> radio broadcast van parked underneath behind the black wrought-iron fence — all missing.",
                "Added the paved north service drive, 2-storey columned porte-cochere with <code>bk_cpshingle</code> hip roof "
                "and upper iron railing, and custom-textured <code>bk_kuzz</code> broadcast van behind the Sillect iron fence.",
            ),
            (
                14, "14_palace_west", "Buck Owens' Crystal Palace West Frontage & Western False-Front Parapets",
                "Rank #13 · Medium Visibility · High Certainty",
                "<code>22-56-37.mp4</code> at <code>80 s</code> (<code>ref_v2/80.jpg</code>) &amp; <code>65 s</code>",
                os.path.join(REF_V2, "80.jpg"),
                "The south-west museum wing of Crystal Palace had only a plain hip roof without the Western frontier-town "
                "stepped wood/tan false-front parapets visible along Buck Owens Blvd at <code>80 s</code>.",
                "Added stepped Western false-front parapet facades with dark cornice trim along the SW frontage of Crystal Palace.",
            ),
        ],
    ),
    (
        "manning",
        "4. 1608 Manning St (House, White Van, Driveway, Backyard) & Amberton Park",
        "Compared against <code>2026-10-30 22-56-37.mp4</code> (<code>154–255 s</code>) and OSM / GIS footprints "
        "(<code>bklan_site_manning.json</code>).",
        [
            (
                15, "15_manning_van", "1608 Manning St North Lawn: Detailed White Ram ProMaster Van & Mature Front Trees",
                "Rank #1a · Critical Visibility · High Certainty",
                "<code>22-56-37.mp4</code> at <code>163 s</code> (<code>ref_v2/163.jpg</code>) &amp; <code>154 s</code>",
                os.path.join(REF_V2, "163.jpg"),
                "The white van was a featureless white box parked at the wrong spot (blocking the driveway), and the front "
                "yard had only a tiny palm stick instead of the two mature leafy shade trees overhanging the north lawn.",
                "Moved the van to the north curb (<code>M((93.5, 126))</code>) and detailed <code>van()</code> as a high-roof "
                "Ram ProMaster with black lower body cladding/bumpers, cab glass, driver-side rear dark window, rear double-door "
                "windows + vertical red tail lights, and roof solar panel; added both mature front shade trees.",
            ),
            (
                16, "16_manning_driveway", "1608 Manning St Unblocked 3-Car Driveway, Brick-Bordered Walk & South Trash Carts",
                "Rank #1b · Critical Visibility · High Certainty",
                "<code>22-56-37.mp4</code> at <code>164 s</code> (<code>ref_v2/164.jpg</code>) &amp; <code>167 s</code>",
                os.path.join(REF_V2, "164.jpg"),
                "In the baseline screenshot, the white van sat dead-center across the driveway apron, completely hiding the "
                "lime-green, white, and light-blue cars! The two black wheeled trash carts were also north of the apron instead "
                "of at the south curb, and the front walkway + red brick step borders were missing.",
                "Cleared the driveway apron so all three parked cars are unobstructed from the street, moved both black wheeled "
                "trash carts south of the driveway (<code>by = 67.5, 71.5</code>), and added the concrete front walk with "
                "<code>bk_brick</code> borders.",
            ),
            (
                17, "17_manning_backyard", "1608 Manning St Rear Covered Patio Overhang & Backyard",
                "Rank #14 · Medium Visibility · High Certainty",
                "<code>22-56-37.mp4</code> at <code>217 s</code> (<code>ref_v2/217.jpg</code>)",
                os.path.join(REF_V2, "217.jpg"),
                "Satellite/aerial inspection at <code>217 s</code> shows a secondary covered patio overhang extending along the "
                "south-east rear wing of 1608 Manning St in addition to the NE patio.",
                "Added the SE rear covered patio roof slab, concrete pad, and support posts in <code>make_bklan_v2.py</code>.",
            ),
            (
                18, "18_amberton_park", "Amberton Park Covered Picnic Shelter, Tan Planter, Swing Set, Light Poles & Backflow Pipe",
                "Rank #8 · High Visibility · High Certainty",
                "<code>22-56-37.mp4</code> at <code>240 s</code> &amp; <code>243 s</code> (<code>ref_v2/240.jpg</code>, <code>243.jpg</code>)",
                os.path.join(REF_V2, "243.jpg"),
                "In <code>18_amberton_park</code> before, the picnic pad had bare picnic tables in the open sun with no roof! "
                "The video at <code>240–243 s</code> clearly shows a large low-slope white metal picnic shelter roof on brown "
                "posts, a tan concrete planter box at its corner, a 2-bay swing set, park benches, tall black light poles, "
                "restroom outbuilding, and a red backflow preventer pipe loop at the curb.",
                "Built the pitched white metal shelter roof on 8 brown posts, corner tan planter + hedge, 2-bay swing set, "
                "park benches, light poles, small park building, and foreground red backflow pipe.",
            ),
        ],
    ),
    (
        "orcom",
        "5. ORCOM CONNECT LAN PARTY Merged Building & Interior Audit (Dec 2002)",
        "Merged from standalone <code>orcom</code> into <code>make_bklan_orcom.py</code> at the vacant SW corner of Sumner St "
        "&amp; Sonora St (<code>x = 344..448, y = 288..348</code>), audited against <code>D:\\Local\\Video\\Capture Homevids\\Orcom 2.mpg</code>.",
        [
            (
                19, "19_orcom_exterior", "Sonora St Exterior Shell & Enterable East Porch (Site Chosen for Zero Collision)",
                "Merge Requirement · Architecture Shell (Labeled Guess)",
                "OSM / aerial site check (<code>aerial-z17-sat.jpg</code>) + <code>Orcom 2.mpg</code> east-door layout",
                os.path.join(GAL, "aerial-z17-sat.jpg"),
                "Previously <code>orcom</code> was a separate BSP, and Sonora St's SW corner at Sumner was an empty paved lot. "
                "The prompt required merging ORCOM into <code>bklan</code> with an enterable exterior building shell on the "
                "east entrance side without colliding with any existing building, street, sign, or park.",
                "Built the banquet-hall shell at <code>x = 344..448, y = 288..348</code> flush with Sonora St's west sidewalk "
                "(<code>x = 448</code>), with masonry wainscot, covered east porch, warm soffit light, and open carved wood door "
                "leaf so players walk straight in from Sonora St (and out the south exit to the 22 ft alley).",
            ),
            (
                20, "20_orcom_vestibule", "ORCOM East Entrance Vestibule Looking West Into Main Hall",
                "Merge + Walk-In Doorway · High Certainty",
                "<code>Orcom 2.mpg</code> at <code>20 s</code> (<code>ref_orcom/20.jpg</code>) &amp; <code>1866 s</code>",
                os.path.join(REF_OC, "20.jpg"),
                "Previously both carved double doors in the east vestibule were shut solid, preventing walk-through from an "
                "exterior street. Indoor lighting also needed to stay at ~165–175 inside a map with outdoor <code>_sunlight 115</code>.",
                "Kept the south carved wood leaf closed for visual reference and swung the north carved leaf 90&deg; open into "
                "the vestibule (43-unit clear walkthrough); sealed the hall under a 5 ft thick <code>world</code> roof slab so "
                "zero outdoor sunlight leaks inside.",
            ),
            (
                21, "21_orcom_aisle", "ORCOM Main Center Aisle, Inlaid Floor Border, Burgundy Chairs & Beige CRTs",
                "Merge Verification · High Certainty",
                "<code>Orcom 2.mpg</code> at <code>656 s</code> (<code>ref_orcom/656.jpg</code>) &amp; <code>674 s</code>",
                os.path.join(REF_OC, "656.jpg"),
                "Verified full banquet hall proportions (76 &times; 52 &times; 10 ft), cream speckled VCT floor with black/grey "
                "inlaid border cross, 21 recessed fluorescent troffers, 8 ft woodgrain tables, CRTs/towers, and burgundy chairs.",
                "All furniture/props emit as <code>func_detail</code> / <code>func_detail_illusionary</code>; added 12 deathmatch "
                "spawns, full weapon/item loadout, and 6 <code>ORCOM</code> entries in <code>SPOTS</code>.",
            ),
            (
                22, "22_orcom_bawls_exit", "South Wall: BAWLS Banner, Corrected Coolers & Recessed Green EXIT Corridor",
                "Rank #5 (ORCOM) · High Visibility · High Certainty",
                "<code>Orcom 2.mpg</code> at <code>1880 s</code> (<code>ref_orcom/1880.jpg</code>) &amp; <code>1712 s</code> (<code>01713.jpg</code>)",
                os.path.join(REF_OC, "1880.jpg"),
                "In standalone <code>orcom</code>, the south exit door was flush-closed against a dead wall, an invented blue "
                "cooler sat on the left, and the red/white coolers were reversed. In <code>Orcom 2.mpg</code>, <code>1880 s</code> "
                "shows the large white cooler on the right and smaller red cooler + open blue BAWLS carton on the left, while "
                "<code>55 s</code> and <code>1712 s</code> show the door propped open into a green exit vestibule with lockers "
                "and panic-bar exterior doors.",
                "Fixed the cooler sizes/order + open BAWLS box under <code>oc_bawls</code>, added the 4-inch black vinyl cove "
                "base round the hall, and built the walkable recessed green south exit vestibule opening to the south alley.",
            ),
            (
                23, "23_orcom_counter_se", "South-East Corner: Honey-Oak L-Counter, Bracket Whiteboard, US Flag & Display Case",
                "Audit Verification · High Certainty",
                "<code>Orcom 2.mpg</code> at <code>8 s</code> (<code>ref_orcom/8.jpg</code>) &amp; <code>94 s</code>",
                os.path.join(REF_OC, "8.jpg"),
                "Checked SE honey-oak L-counter, white louvered door, bracket whiteboard on wooden easel, US flag, and "
                "<code>ORTHODOX CHRISTIAN MISSIONS CENTER</code> wood-and-glass display case; wall base lacked its black vinyl cove.",
                "Preserved all SE props and added the continuous black vinyl cove base molding visible at <code>8 s</code>.",
            ),
            (
                24, "24_orcom_tv_ne", "North-East Corner: Big-Screen Projection TV, Potted Ficus, Stacked Chairs & Officer Board",
                "Rank #15 · Medium Visibility · High Certainty",
                "<code>Orcom 2.mpg</code> at <code>726 s</code> (<code>ref_orcom/726.jpg</code>) &amp; <code>498 s</code>",
                os.path.join(REF_OC, "726.jpg"),
                "At <code>726 s</code>, the past-officers portrait board on the east wall has a stepped/peaked wood header crest "
                "above its central plaque, and <code>498 s</code> shows spare burgundy banquet chairs stacked by the NE wall.",
                "Added the stepped wood header crest atop <code>oc_portraits</code> and a stack of spare burgundy banquet chairs "
                "in the NE corner.",
            ),
            (
                25, "25_orcom_kitchen_w", "West Wall: Kitchen Door, Folding Wood Pass-Through Shutter, Gingham Table & NW EXIT Alcove",
                "Rank #12 (ORCOM) · Medium Visibility · High Certainty",
                "<code>Orcom 2.mpg</code> at <code>1122 s</code> (<code>ref_orcom/1122.jpg</code>) &amp; <code>718 s</code> (<code>00719.jpg</code>)",
                os.path.join(REF_OC, "1122.jpg"),
                "The kitchen pass-through window lacked its warm-wood folding shutter panel on the right jamb (<code>1122 s</code>), "
                "and the NW corner had a narrow flush door instead of the wide recessed exit alcove with orange-wood left panel "
                "(<code>718 s</code>).",
                "Added the wood folding shutter + stainless pass-through counter trim, and rebuilt the NW corner with its wide "
                "recessed dark alcove, illuminated <code>EXIT</code> sign, and left orange-wood panel.",
            ),
            (
                26, "26_orcom_computer_n", "North Wall: Corrected 'Computer RENAISSANCE' Sponsor Banner",
                "Rank #3 (ORCOM) · High Visibility · High Certainty",
                "<code>Orcom 2.mpg</code> at <code>684 s</code> (<code>ref_orcom/684.jpg</code>)",
                os.path.join(REF_OC, "684.jpg"),
                "The baseline <code>oc_computer</code> texture had an invented large black <code>C</code> circle emblem on the "
                "left and shortened tagline. Frame <code>684 s</code> clearly shows no <code>C</code> circle: it reads "
                "<code>Computer</code> (with a green <code>o</code>), spaced <code>R E N A I S S A N C E</code>, italic "
                "<code>Where Computers Suddenly Make Sense</code>, and <code>Westchester Village, Stockdale and California</code>.",
                "Redrew <code>oc_computer</code> in <code>build_bklan_textures.py</code> directly against <code>ref_orcom/684.jpg</code>, "
                "removing the invented logo and matching the exact typography, green <code>o</code>, and two-line subtitle.",
            ),
        ],
    ),
]

parts = []
add = parts.append

add("""
<header>
  <p class="kicker">BakersfieldQuake &middot; Unified Map <code>bklan.bsp</code> &middot; Accuracy Audit &amp; ORCOM Merge</p>
  <h1>B-LAN 2001 &amp; ORCOM Connect Accuracy Report</h1>
  <p class="lede">Comprehensive visual audit of <code>bklan</code> and <code>orcom</code> against all four videos
  (<code>bklan.wmv</code>, <code>Orcom 2.mpg</code>, and both owner review recordings), ~100 Google Street View / satellite
  images, and OpenStreetMap / Bakersfield GIS footprints &mdash; with <code>orcom</code> merged into <code>bklan</code> as an
  enterable banquet-hall building on Sonora St.</p>
  <div class="stat-row">
    <div class="stat"><strong>1 BSP</strong><span>Unified <code>maps/bklan.bsp</code> + <code>.lit</code> (<code>orcom.bsp</code> retired)</span></div>
    <div class="stat"><strong>26 / 26</strong><span>Matched Before vs. After DarkPlaces viewpoints</span></div>
    <div class="stat"><strong>0 Leaks / 0 Warnings</strong><span><code>qbsp</code> BSP2 clean; <code>skip</code> in <code>bklan.wad</code></span></div>
    <div class="stat"><strong>68.4 s <code>vis</code></strong><span>Down from ~1 hr (725 world + 4,322 <code>func_detail</code> brushes)</span></div>
  </div>
</header>
<nav>
  <a href="#orcom-merge">ORCOM Merge &amp; Site</a>
  <a href="#block">1 Block &amp; E 21st</a>
  <a href="#lan130a">2 Unit 130A (B-LAN)</a>
  <a href="#palace">3 Sign &amp; Crystal Palace</a>
  <a href="#manning">4 Manning St &amp; Park</a>
  <a href="#orcom">5 ORCOM Hall</a>
  <a href="#honesty">Guesses &amp; Uncovered Areas</a>
</nav>

<section id="orcom-merge">
  <h2>ORCOM Connect Merge Architecture &amp; Site Rationale</h2>
  <div class="callout">
    <p><strong>Where ORCOM was placed in <code>bklan</code> &mdash; and why:</strong></p>
    <ul>
      <li><strong>Coordinates:</strong> SW corner parcel of Sumner St &amp; Sonora St &mdash; hall interior at
      <code>x = 360..436, y = 295..347</code> (76 &times; 52 &times; 10 ft), exterior building shell at
      <code>x = 344..448, y = 288..348</code> (<code>source/mm_tools/make_bklan_orcom.py</code>).</li>
      <li><strong>Zero collisions:</strong> OpenStreetMap / Bakersfield GIS (<code>bklan_osm.json</code>) and the aerial photos
      show this corner lot is vacant paved ground. Placing the building here collides with zero existing buildings, roads,
      rail tracks, Street View hero facades, the Bakersfield Sign, Crystal Palace, 1608 Manning St, or Amberton Park.</li>
      <li><strong>True cardinal orientation &amp; street walk-in:</strong> Because Sonora St runs along the east edge of the
      parcel (west sidewalk at <code>x = 448..460</code>), the hall sits at its exact video orientation without rotation:
      <strong>kitchen on the west</strong>, <strong>carved-door entrance vestibule on the east</strong> opening directly onto
      Sonora St's sidewalk, <strong>BAWLS banner + recessed green EXIT vestibule on the south</strong> opening onto a 22 ft
      alley (<code>y = 266.2..288</code> above building #59), and <strong>Computer RENAISSANCE banner on the north</strong>.</li>
      <li><strong>Indoor lighting isolation:</strong> A sealed 5 ft thick <code>world</code> roof slab (<code>z = 10..15 ft</code>)
      and solid perimeter walls block 100% of outdoor <code>_sunlight 115</code>. Inside, 21 fluorescent ceiling troffers at
      <code>175</code> (with <code>_dirt -1</code> so outdoor AO does not muddy the lay-in ceiling) preserve the exact indoor
      banquet-hall exposure while keeping outdoor sunny-day brightness untouched.</li>
      <li><strong>Web viewer &amp; retirement:</strong> Added 6 <code>ORCOM</code> entries to <code>SPOTS</code> (led by
      <code>ORCOM CONNECT LAN PARTY</code>), added <code>?spot=...</code> deep-linking to <code>web_viewer_index.html</code>,
      removed standalone <code>maps/orcom.bsp</code>, <code>maps/orcom.lit</code>, <code>view_orcom.sh</code>, and
      <code>deploy_orcom_viewer.sh</code>, and replaced <code>https://bakersfield.larrywew.fun/orcom/</code> with an instant
      redirect to <code>https://bakersfield.larrywew.fun/warehouse/?spot=ORCOM%20CONNECT%20LAN%20PARTY</code>.</li>
    </ul>
  </div>
</section>
""")

for sec_id, sec_title, sec_desc, cards in SECTIONS:
    add(f'<section id="{sec_id}"><h2>{sec_title}</h2><p>{sec_desc}</p>')
    for c in cards:
        add(card(*c))
    add("</section>")

add("""
<section id="honesty">
  <h2>Honesty Ledger: What Remains a Guess vs. Uncovered by Any Source</h2>
  <p>Per project rules, nothing was invented where a source was silent or illegible. Every remaining approximation or
  unfilmed area in the unified map is explicitly documented below:</p>
  <table class="ledger">
    <thead>
      <tr><th>Area / Element</th><th>Status</th><th>Reason &amp; Source Coverage</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>ORCOM exterior shell &amp; street address</strong></td>
        <td><span class="pill pill-guess">Labeled Guess</span></td>
        <td><code>Orcom 2.mpg</code> (32 min) was shot 100% indoors at night/day and never shows the exterior facade, street
        signage, or venue address (only interior clues: <em>Orthodox Christian Missions Center</em> display case and Bakersfield
        <em>Computer Renaissance</em> banner). The outer stucco/wainscot shell on Sonora St is a clean, unbranded architectural
        wrapper with zero invented signs.</td>
      </tr>
      <tr>
        <td><strong>ORCOM kitchen room behind pass-through</strong></td>
        <td><span class="pill pill-guess">Labeled Guess</span></td>
        <td>Only glimpsed obliquely through the open door and pass-through window (<code>1122 s</code>, <code>1164 s</code>:
        stainless shelves, fridge, fluorescent strip). Room depth and counter placement inside the kitchen are approximate.</td>
      </tr>
      <tr>
        <td><strong>ORCOM exact PC station count per row</strong></td>
        <td><span class="pill pill-guess">Estimate</span></td>
        <td>Pans across the banquet hall (<code>656–684 s</code>) confirm four table bands (north wall, south wall, and two
        double-sided center rows) with beige CRTs/towers and burgundy chairs, plus occasional laptop/empty slots; exact per-seat
        equipment variations are representative.</td>
      </tr>
      <tr>
        <td><strong>Unit 120A interior, closed warehouse bays &amp; crate stairs</strong></td>
        <td><span class="pill pill-guess">Kept Guess</span></td>
        <td>No interior video or Street View exists inside <code>120A</code> (battery shop), closed bays <code>130C</code>/<code>W3</code>,
        or on the roof of Building 45; existing gameplay layout and crate stairs to the roof were preserved as-is.</td>
      </tr>
      <tr>
        <td><strong>Unit 130A back-room bathroom deep corners</strong></td>
        <td><span class="pill pill-blur">Blurry / Dark</span></td>
        <td><code>bklan.wmv</code> <code>2711–2712 s</code> clearly shows the corner partition, inward-opening white door,
        porcelain toilet + tank, floor tissue rolls, and two striped cones outside, but <code>2713–2716 s</code> is too dark to
        resolve a sink or mirror on the opposite wall, so none were invented.</td>
      </tr>
      <tr>
        <td><strong>Small sub-text on 110 E 21st &amp; Sacramento St placards</strong></td>
        <td><span class="pill pill-blur">Too Blurry</span></td>
        <td>On 110 E 21st's yellow banner (<code>sv-west-110e21st-yaw0.jpg</code>), <code>APPLIANCES</code> is legible while
        smaller bullet lines are weathered/blurred; photo-cropped directly from Street View rather than inventing text. Likewise
        the white paper notices above Building 45's east doors (<code>yaw225</code>) are illegible at Street View resolution.</td>
      </tr>
      <tr>
        <td><strong>Residential &amp; commercial interiors (Manning St, Crystal Palace, Capri Motel)</strong></td>
        <td><span class="pill pill-none">Uncovered</span></td>
        <td><code>22-56-37.mp4</code> and Street View cover exteriors, yards, driveways, and aerial roofs only; those buildings
        remain solid exterior hulls. Notice also that 1608 Manning St, Crystal Palace, Bakersfield Sign, and Amberton Park are
        intentionally transplanted east/south of Sonora St per user design rather than miles away at true city coordinates.</td>
      </tr>
    </tbody>
  </table>
</section>
""")

page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>bklan &amp; ORCOM Connect Accuracy Audit Report</title>
<style>
  :root {
    --bg: #111214; --panel: #1a1c20; --panel2: #22252b; --ink: #ece9e1;
    --muted: #a8a399; --accent: #e8a33d; --green: #4bb571; --blue: #5899e2; --red: #d96557; --line: #2e323a;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.55 system-ui, -apple-system, Segoe UI, Arial, sans-serif; }
  header, nav, section { max-width: 1360px; margin: 0 auto; padding: 0 20px; }
  header { padding-top: 42px; padding-bottom: 18px; }
  .kicker { color: var(--accent); letter-spacing: .08em; text-transform: uppercase; font-size: 12px; font-weight: 700; margin: 0; }
  h1 { font-size: clamp(28px, 4vw, 46px); line-height: 1.08; margin: 8px 0 12px; }
  .lede { color: var(--muted); max-width: 920px; font-size: 17px; margin: 0 0 20px; }
  .stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 18px 0 8px; }
  .stat { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; }
  .stat strong { display: block; font-size: 20px; color: var(--accent); }
  .stat span { font-size: 13px; color: var(--muted); }
  nav { position: sticky; top: 0; z-index: 5; background: rgba(17,18,20,.94); backdrop-filter: blur(6px);
    display: flex; flex-wrap: wrap; gap: 8px 18px; padding-top: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--line); }
  nav a { color: var(--ink); text-decoration: none; font-size: 13.5px; font-weight: 600; }
  nav a:hover { color: var(--accent); }
  h2 { font-size: 24px; margin: 46px 0 8px; padding-bottom: 8px; border-bottom: 2px solid var(--line); }
  h3 { font-size: 17px; margin: 0; display: inline; }
  section > p { color: var(--muted); max-width: 960px; margin-top: 6px; }
  code { background: #292d35; padding: 1px 6px; border-radius: 4px; font-size: .9em; color: #f5d08a; }
  .callout { background: var(--panel); border-left: 4px solid var(--accent); border-radius: 8px; padding: 16px 20px; margin: 14px 0; }
  .callout p { margin: 0 0 8px; }
  .callout ul { margin: 0; padding-left: 20px; color: var(--muted); }
  .callout li { margin: 6px 0; }
  .callout li strong { color: var(--ink); }
  .audit-card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px 18px; margin: 18px 0; }
  .card-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; }
  .num { color: var(--accent); font-weight: 800; font-family: monospace; font-size: 16px; margin-right: 8px; }
  .badge { background: var(--panel2); border: 1px solid #3c424d; color: var(--accent); font-size: 12px; font-weight: 600;
    padding: 3px 9px; border-radius: 999px; white-space: nowrap; }
  .src { font-size: 13.5px; color: var(--muted); margin: 0 0 10px; }
  .grid { display: grid; gap: 12px; }
  .g3 { grid-template-columns: repeat(3, 1fr); }
  @media (max-width: 960px) { .g3, .stat-row { grid-template-columns: 1fr; } }
  figure { margin: 0; background: var(--panel2); padding: 8px; border-radius: 8px; position: relative; border: 1px solid #2d3139; }
  figure img { width: 100%; aspect-ratio: 16 / 9; object-fit: cover; display: block; border-radius: 4px; cursor: zoom-in; background: #0d0e10; }
  figcaption { font-size: 12px; color: var(--muted); margin-top: 6px; line-height: 1.35; }
  .tag { position: absolute; top: 14px; left: 14px; font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .05em; padding: 2px 8px; border-radius: 4px; color: #fff; pointer-events: none; }
  .tag-ref { background: rgba(56, 122, 204, .88); }
  .tag-bef { background: rgba(185, 68, 56, .88); }
  .tag-aft { background: rgba(52, 148, 86, .90); }
  .notes { margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--line); display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .notes p { margin: 0; font-size: 13.8px; color: var(--muted); }
  .notes strong { color: var(--ink); }
  @media (max-width: 960px) { .notes { grid-template-columns: 1fr; } }
  .ledger { width: 100%; border-collapse: collapse; margin: 16px 0 40px; background: var(--panel); border-radius: 8px; overflow: hidden; }
  .ledger th, .ledger td { text-align: left; padding: 11px 14px; border-bottom: 1px solid var(--line); vertical-align: top; font-size: 14px; }
  .ledger th { background: var(--panel2); color: var(--accent); font-size: 12.5px; text-transform: uppercase; letter-spacing: .05em; }
  .ledger td { color: var(--muted); }
  .ledger td strong { color: var(--ink); }
  .pill { display: inline-block; font-size: 11.5px; font-weight: 700; padding: 2px 8px; border-radius: 999px; white-space: nowrap; }
  .pill-guess { background: rgba(232,163,61,.18); color: #f3ba63; border: 1px solid rgba(232,163,61,.4); }
  .pill-blur { background: rgba(88,153,226,.18); color: #84b7f0; border: 1px solid rgba(88,153,226,.4); }
  .pill-none { background: rgba(168,163,153,.16); color: #c7c2b8; border: 1px solid rgba(168,163,153,.35); }
  #lb { position: fixed; inset: 0; background: rgba(0,0,0,.92); display: none; align-items: center; justify-content: center; z-index: 99; cursor: zoom-out; }
  #lb img { max-width: 96vw; max-height: 94vh; border-radius: 6px; box-shadow: 0 12px 40px rgba(0,0,0,.8); }
  footer { max-width: 1360px; margin: 0 auto; padding: 24px 20px 60px; color: var(--muted); font-size: 13px; border-top: 1px solid var(--line); }
</style>
</head>
<body>
@@BODY@@
<footer>
  Generated by <code>source/mm_tools/build_accuracy_report.py</code> &middot; Click any image to inspect full-size &middot;
  Live browser walk-around: <a style="color:var(--accent)" href="https://bakersfield.larrywew.fun/warehouse/">bakersfield.larrywew.fun/warehouse/</a>
  (and <a style="color:var(--accent)" href="https://bakersfield.larrywew.fun/orcom/">/orcom/</a> &rarr; ORCOM spot).
</footer>
<div id="lb"><img alt=""></div>
<script>
  const lb = document.getElementById("lb"), li = lb.querySelector("img");
  document.addEventListener("click", (e) => {
    if (e.target.matches("figure img")) { li.src = e.target.src; lb.style.display = "flex"; }
    else if (lb.contains(e.target)) { lb.style.display = "none"; }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") lb.style.display = "none"; });
</script>
</body>
</html>
""".replace("@@BODY@@", "\n".join(parts))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(page)
print(f"wrote {OUT}: {img_count[0]} embedded images, {len(page) / 1e6:.2f} MB")
