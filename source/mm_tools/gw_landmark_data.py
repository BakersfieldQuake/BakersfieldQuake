"""Landmarks along S Union Ave, read from the Street View gallery by four reviewers (ref_sources/golden_west_landmarks/part_A..D.md).
Pure data, used by gw_route.py (placement) and build_gw_textures.py (textures gl_<id> and gw_w_<colour>).
Positions are cross street + dy (true feet north of the cross street's centre line) + side (E = east / +x, W = west). Cross-street
y values are the OSM junction positions where they exist, estimates (+-100 ft) otherwise. Text that could not be read in the photos is
left off the signs."""

STREET_Y = {"Belle": 646, "Daniels": 1267, "TerraceWay": 1962, "Churchill": 2400, "Tollhouse": 2800, "Brundage": 3262, "Lloyd": 3450,
            "Wilkins": 3560, "First": 3665, "Marcus": 4450, "Texas": 4562, "Third": 5046, "Bill": 5400, "Fourth": 5738, "Fifth": 6066,
            "Sixth": 6423, "Seventh": 6751, "Eighth": 7059, "Ninth": 7464, "Tenth": 7809, "Eleventh": 8155, "California": 8555,
            "Hayden": 9000, "Seventeenth": 10643, "Eureka": 10758, "Eighteenth": 10993, "Nineteenth": 11339, "Twentieth": 11679,
            "TwentyFirst": 12032}

RED, WHITE, YEL, BLUE, BLK, GRN, TAN, BRN, ORG, TEAL, CREAM = (196, 40, 36), (244, 244, 238), (246, 206, 40), (30, 70, 160), (24, 24, 28), (30, 120, 70), \
    (206, 184, 140), (96, 60, 40), (232, 100, 24), (30, 140, 140), (240, 228, 196)

# id: (background, border, [(text, colour)])
SIGNS = {
    "carnitas": (RED, WHITE, [("CARNITAS", WHITE), ("BIRRIA", YEL)]),
    "elcharro": (RED, YEL, [("El Charro", WHITE), ("MEXICAN FOOD", YEL)]),
    "desertstar": (WHITE, RED, [("Desert Star", RED), ("MOTEL", RED), ("FREE TV", BLUE)]),
    "circlek": (WHITE, RED, [("Circle K", RED)]),
    "gilbreath": (TAN, BLUE, [("GILBREATH", BLUE)]),
    "uhaul": (ORG, WHITE, [("U-HAUL", WHITE), ("MOVING & STORAGE", WHITE)]),
    "carlsjr": (RED, YEL, [("Carl's Jr.", YEL)]),
    "villainn": (WHITE, RED, [("VILLA INN", RED), ("MOTEL", RED)]),
    "jackbox": (RED, WHITE, [("JACK IN", WHITE), ("THE BOX", WHITE)]),
    "parkhouse": (RED, WHITE, [("Parkhouse", WHITE), ("TIRE", WHITE)]),
    "countertop": (TEAL, WHITE, [("The Countertop", WHITE), ("Store", WHITE)]),
    "karz": (BLUE, WHITE, [("Karz", WHITE)]),
    "firestone": (RED, WHITE, [("Firestone", WHITE)]),
    "quality": (GRN, WHITE, [("Q Quality", WHITE), ("INN", WHITE)]),
    "seguros": (TEAL, WHITE, [("INSURANCE", WHITE), ("ASEGURANZA", YEL)]),
    "econo": (WHITE, BLUE, [("ECONO AIR inc.", BLUE), ("AIR CONDITIONING", BLUE), ("HEATING", BLUE)]),
    "usedtire": (BRN, CREAM, [("USED TIRE", CREAM), ("CENTER", CREAM)]),
    "birria": (WHITE, RED, [("BIRRIA Y", RED), ("MARISCOS", RED)]),
    "autorepair": (YEL, BLK, [("AUTO REPAIR", BLK), ("& ALIGNMENT", BLK)]),
    "motelyel": (YEL, BLK, [("MOTEL", BLK)]),
    "plazamotel": (RED, WHITE, [("PLAZA", WHITE), ("MOTEL", WHITE)]),
    "superior": (WHITE, RED, [("SUPERIOR", RED), ("GROCERS", RED)]),
    "uniontires": (YEL, GRN, [("UNION TIRES", GRN)]),
    "gasyel": (YEL, RED, [("GAS", RED), ("REGULAR 4.79", BLK)]),
    "shamrock": (WHITE, GRN, [("Shamrock", GRN)]),
    "tacos": (BLK, YEL, [("Tacos La Villa", WHITE), ("MEXICAN GRILL", YEL)]),
    "mcdonalds": (RED, YEL, [("McDonald's", YEL)]),
    "mobil": (BLUE, RED, [("Mobil", WHITE), ("REGULAR 4.69", WHITE)]),
    "seven": (WHITE, GRN, [("7-ELEVEN", GRN), ("GAS  4.79", RED)]),
    "autoglass": (WHITE, BLUE, [("AutoGlassNow", BLUE)]),
    "labuena": (RED, WHITE, [("La Buena", WHITE), ("LIQUOR", WHITE)]),
    "shawn": (RED, WHITE, [("SHAWN", WHITE), ("LIQUOR", WHITE)]),
    "casa": (CREAM, RED, [("CASA", RED), ("MEXICAN FOOD", RED)]),
    "salvation": (RED, WHITE, [("Salvation Army", WHITE), ("Family Store", WHITE)]),
    "automotive": (BLUE, WHITE, [("Automotive", WHITE), ("SMOG CHECK", YEL)]),
    "gci": (BLUE, WHITE, [("GCI", WHITE)]),
    "alignments": (WHITE, RED, [("ALIGNMENTS", RED)]),
    "truckrepair": (WHITE, BLUE, [("TRUCK & TRAILER", BLUE), ("REPAIR", BLUE)]),
    "bill_blue": ((40, 90, 170), WHITE, [("", WHITE)]),
    "bill_red": ((190, 60, 50), WHITE, [("", WHITE)]),
    "bill_luch": ((30, 60, 120), YEL, [("TU LUCHADOR", YEL)]),
    "bill_tan": ((200, 180, 130), BRN, [("", WHITE)]),
}

# (cross street, dy, side, sign id, face width ft, face height ft, height of the top above the road ft, distance behind the kerb ft)
POLES = [
    ("Belle", 30, "W", "carnitas", 7, 5, 22, 6), ("Daniels", 60, "W", "elcharro", 8, 6, 32, 6), ("TerraceWay", 20, "E", "desertstar", 8, 8, 28, 6),
    ("Churchill", 40, "E", "circlek", 9, 6, 30, 6), ("Churchill", -60, "W", "truckrepair", 8, 4, 18, 6), ("Tollhouse", 60, "E", "gilbreath", 14, 5, 22, 8),
    ("Brundage", 50, "E", "uhaul", 10, 8, 32, 6), ("Brundage", -50, "W", "carlsjr", 8, 8, 34, 6),
    ("Lloyd", 30, "E", "villainn", 8, 8, 28, 6), ("Lloyd", 110, "E", "jackbox", 8, 8, 30, 6), ("Wilkins", 40, "W", "parkhouse", 14, 6, 26, 6),
    ("First", 80, "E", "countertop", 8, 6, 24, 6), ("First", 190, "E", "karz", 6, 6, 24, 6), ("Marcus", -50, "W", "firestone", 8, 8, 30, 6),
    ("Texas", 90, "E", "quality", 8, 9, 32, 6), ("Third", 40, "E", "seguros", 10, 5, 18, 6), ("Bill", 40, "E", "econo", 10, 8, 22, 6),
    ("Bill", 150, "E", "usedtire", 8, 7, 24, 6), ("Fourth", 70, "W", "shamrock", 8, 8, 30, 6), ("Fifth", 40, "W", "birria", 8, 7, 22, 6),
    ("Fifth", 120, "E", "autorepair", 8, 5, 18, 6), ("Sixth", 40, "W", "motelyel", 6, 14, 32, 6), ("Seventh", 40, "W", "plazamotel", 8, 12, 34, 6),
    ("Eighth", 20, "E", "gasyel", 8, 8, 28, 6), ("Tenth", 120, "W", "superior", 10, 6, 28, 6), ("Eleventh", 20, "E", "uniontires", 8, 5, 18, 6),
    ("California", 30, "W", "gasyel", 7, 9, 36, 6), ("Hayden", 40, "E", "tacos", 8, 7, 24, 6), ("Hayden", 120, "W", "alignments", 8, 4, 16, 6),
    ("Seventeenth", 20, "W", "autoglass", 10, 4, 18, 6), ("Seventeenth", 90, "W", "labuena", 8, 5, 20, 6), ("Eureka", 40, "W", "shawn", 8, 5, 20, 6),
    ("Eureka", -40, "E", "casa", 8, 8, 24, 6), ("Eighteenth", 60, "E", "mcdonalds", 10, 12, 30, 12), ("Eighteenth", -10, "W", "mobil", 8, 14, 34, 6),
    ("Nineteenth", 40, "E", "seven", 8, 10, 28, 6), ("Nineteenth", 140, "W", "salvation", 10, 4, 14, 6), ("Twentieth", 40, "E", "automotive", 8, 4, 16, 6),
    ("Twentieth", 120, "E", "motelyel", 6, 12, 26, 6), ("TwentyFirst", 60, "E", "gci", 8, 6, 22, 6),
]

# billboards (two-post, 24 x 10 ft): (street, dy, side, sign id, top height)
BILLBOARDS = [("Wilkins", 120, "W", "bill_red", 36), ("Marcus", 40, "E", "bill_tan", 38), ("Churchill", 120, "W", "bill_blue", 34),
              ("Ninth", 40, "E", "bill_red", 36), ("Tenth", -60, "E", "bill_luch", 34), ("Twentieth", 30, "W", "bill_blue", 34),
              ("Twentieth", 180, "E", "bill_tan", 36)]

# building tints: (street, dy, side, colour) - the footprint nearest to that spot gets that wall colour
TINTS = [("Daniels", 80, "W", "cream"), ("TerraceWay", 30, "E", "white"), ("Texas", 90, "E", "mustard"), ("Fourth", 160, "E", "cream"),
         ("First", 50, "E", "tan"), ("Fourth", 200, "W", "peach"), ("Sixth", 60, "E", "white"), ("Seventh", 40, "W", "white"),
         ("Tenth", 120, "W", "peach"), ("Eleventh", 160, "E", "pink"), ("Seventeenth", 20, "W", "blue"), ("Seventeenth", 90, "W", "peach"),
         ("Eureka", 40, "W", "tan"), ("Eighteenth", 60, "E", "cream"), ("Nineteenth", 150, "W", "khaki"), ("Twentieth", 40, "E", "blue"),
         ("TwentyFirst", -50, "E", "tan"), ("TwentyFirst", 40, "W", "red"), ("Tollhouse", 70, "E", "tan"), ("Wilkins", 60, "W", "white"),
         ("Hayden", 40, "E", "cream")]

# gas station canopies: (street, dy, side, band colour)
CANOPIES = [("Churchill", 40, "E", "red"), ("Eighth", 20, "E", "red"), ("California", 30, "W", "yellow"), ("Fourth", 70, "W", "red"),
            ("Eighteenth", -10, "W", "blue"), ("TerraceWay", -60, "W", "blue")]

TINT_COLORS = {"cream": (232, 222, 196), "mustard": (206, 160, 60), "white": (236, 234, 226), "peach": (232, 184, 150), "pink": (226, 150, 160),
               "tan": (200, 172, 128), "khaki": (176, 160, 112), "blue": (50, 90, 170), "red": (180, 50, 44), "yellow": (240, 200, 50),
               "teal": (60, 150, 140)}
