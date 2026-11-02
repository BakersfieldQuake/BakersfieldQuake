"""Build mystery_box_vote.html: ONE page to vote which monsters the Mystery Box can spawn AND what each one sounds like.

The box now spawns ONE random monster (it used to spawn two). The page merges the two older pages
(mystery_box_monster_vote.html = who is in the pool, mystery_box_sound_vote.html = drive + explode sound per monster)
and covers every character that has a sprite or model now: the old 16 plus Bryan & Demons, Dennis, Paul, QuakeGuy,
Mr DIY and Rubber Finger.

Run (numpy, scipy, PIL, ffmpeg needed; python3 from WindowsApps has them, NOT with -I):
  python3 make_vote_thumbs.py            # only when a thumbnail is missing (needs PIL)
  python3 make_mbox_vote_page.py

It reuses make_mbox_sound_vote.py (the synthesised / cut clips, the whole-game sound library, the audio engine) and swaps in
mbox_vote_page_template.html and the larger monster table below. Output: <mod>/mystery_box_vote.html (self-contained).
The result is a pool (`set mb_pool "..."` line) plus a drive + explode pick per monster in the pool.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_mbox_sound_vote as sv   # noqa: E402

MOD = sv.MOD
sv.PAGE = os.path.join(MOD, "mystery_box_vote.html")
sv.TEMPLATE_FILE = os.path.join(HERE, "mbox_vote_page_template.html")

# the sprite sound folder the user added after the last vote
sv.FUN_FOLDERS.insert(1, ("bryan", "Bryan & Demons"))

(SUIT, SQUAT, WHEEL, JESS, KYLE, ROB, ROLL) = (sv.SUIT, sv.SQUAT, sv.WHEEL, sv.JESS, sv.KYLE, sv.ROB, sv.ROLL)
MEGA, PINK, PC, HORSE, EARS, FORK = "megaman", "pink_supercar", "netsend_pc", "casino_horse", "big_ears", "forklift"
EARHEAD, PICKLE, HAND = "earhead", "pickle_surprise", "johns_hand"
BRY, DEN, PAUL, QG, DIY, FING = "bryan_demons", "dennis", "paul", "quakeguy", "mr_diy", "rubber_finger"

TAG_NOW = sv.TAG_NOW
M, D_mod = sv.M, sv.D_mod
SR = sv.SR


def cut(rel, secs):
    """First `secs` of a game sound (one-shots must stay under ~3 s)."""
    return lambda: sv.mod_wav(rel)[:int(secs * SR)]


def ext(path):
    """A sound that lives outside sound/ (decoded to the page's rate)."""
    def f():
        with open(os.path.join(MOD, path), "rb") as fh:
            return sv.decode(fh.read())
    return f


def ext_loop(path, start, dur, xf):
    return lambda: sv.loop_from(ext(path)(), start, dur, xf)


# ----------------------------------------------------------------------------- extra curated clips for the new characters
# Only cuts / repeats of sounds that exist (game folders, the sprite folders): no new synthesis, so the seeded random stream of the older
# clips is untouched and they come out byte for byte the same.
sv.DRIVE += [
    ("drv_bryan_noway", "Bryan: No Way (loop)", "The game's bryan/noway clip, made seamless.", TAG_NOW, "sound/bryan/noway.wav (looped)",
     D_mod("bryan/noway.wav", reps=1, xf=0.1), [BRY]),
    ("drv_bryan_detector", "Bryan: Detector Beeps", "The game's bryan/detector clip, repeated.", TAG_NOW, "sound/bryan/detector.wav (looped)",
     D_mod("bryan/detector.wav", reps=2, xf=0.08), [BRY]),
    ("drv_hm_hacking", "Hackmon: Hacking Loop", "A 2 s slice of the game's hackmon/hm_hacking clip.", TAG_NOW, "sound/hackmon/hm_hacking.wav (2 s slice)",
     D_mod("hackmon/hm_hacking.wav", start=0.2, dur=2.0, xf=0.15), [PC]),
    ("drv_mrdiy_laugh", "Mr DIY's Laugh (loop)", "The laugh recorded for the Mr DIY sprite, made seamless.", TAG_NOW, "mrdiy_sprite/mrdiy_laugh.wav (2 s slice)",
     ext_loop("mrdiy_sprite/mrdiy_laugh.wav", 0.2, 2.0, 0.15), [DIY]),
    ("drv_friends_johnny", "Friends: Johnnnny (loop)", "The game's friends/johnnnny clip, repeated.", TAG_NOW, "sound/friends/johnnnny.wav (looped)",
     D_mod("friends/johnnnny.wav", reps=2, xf=0.05), [HAND]),
    ("drv_floathead_idle", "Floathead Idle Hum", "The game's floathead/idle clip, made seamless.", TAG_NOW, "sound/floathead/idle.wav (looped)",
     D_mod("floathead/idle.wav", reps=1, xf=0.1), [EARHEAD, EARS]),
]
sv.EXPLODE += [
    ("exp_bryan_whirl", "Bryan: Whirl", "The first 3 s of the game's bryan/whirl clip.", TAG_NOW, "sound/bryan/whirl.wav (first 3 s)", cut("bryan/whirl.wav", 3.0), [BRY]),
    ("exp_bryan_portal", "Bryan: Portal Die", "The game's bryan/portal_die clip.", TAG_NOW, "sound/bryan/portal_die.wav", M("bryan/portal_die.wav"), [BRY]),
    ("exp_bryan_slash", "Bryan: Slash", "The first 3 s of the game's bryan/slash clip.", TAG_NOW, "sound/bryan/slash.wav (first 3 s)", cut("bryan/slash.wav", 3.0), [BRY]),
    ("exp_hm_crash", "Hackmon: Crash", "The game's hackmon/hm_crash clip.", TAG_NOW, "sound/hackmon/hm_crash.wav", M("hackmon/hm_crash.wav"), [PC]),
    ("exp_hm_fatal", "Hackmon: Fatal", "The game's hackmon/hm_fatal clip.", TAG_NOW, "sound/hackmon/hm_fatal.wav", M("hackmon/hm_fatal.wav"), [PC]),
    ("exp_quakeahh", "Quake AHH", "The first 3 s of the game's funny/quakeahh clip.", TAG_NOW, "sound/funny/quakeahh.wav (first 3 s)", cut("funny/quakeahh.wav", 3.0), [PAUL, QG]),
    ("exp_mrdiy_laugh", "Mr DIY's Laugh", "The laugh recorded for the Mr DIY sprite, as the goodbye.", TAG_NOW, "mrdiy_sprite/mrdiy_laugh.wav", ext("mrdiy_sprite/mrdiy_laugh.wav"), [DIY]),
    ("exp_pickle_surprise", "Pickle Surprise", "The game's pickle/surprise clip.", TAG_NOW, "sound/pickle/surprise.wav", M("pickle/surprise.wav"), [PICKLE, FING]),
    ("exp_pickle_throw", "Pickle Throw", "The game's pickle/throw clip.", TAG_NOW, "sound/pickle/throw.wav", M("pickle/throw.wav"), [PICKLE]),
    ("exp_floathead_boing", "Floathead Boing", "The game's floathead/boing clip.", TAG_NOW, "sound/floathead/boing.wav", M("floathead/boing.wav"), [EARHEAD, EARS, FING]),
    ("exp_friends_no", "Friends: No", "The game's friends/no clip.", TAG_NOW, "sound/friends/no.wav", M("friends/no.wav"), [WHEEL]),
]
# the Mr DIY jingle ("Lagu Jingle MR. DIY.mp3", 62 s, ~120 bpm; converted to sound/mrdiy/mrdiy_jingle.wav, 44.1 kHz mono).
# Beats fall at 0.294 s + n * 0.501 s, so a bar (4 beats) is 2.004 s and every loop below starts on a beat.
JINGLE = "mrdiy/mrdiy_jingle.wav"
BAR, BEAT0 = 2.004, 0.294


def jingle_bar(k):
    return lambda: sv.loop_from(sv.mod_wav(JINGLE), BEAT0 + k * BAR, BAR, 0.06)


def jingle_tail():
    a = sv.mod_wav(JINGLE)
    end = len(a) / SR - 1.5                        # the music stops 1.5 s before the file ends
    return a[int((end - 2.9) * SR):int(end * SR)]


sv.DRIVE += [
    ("drv_diy_jingle_a", "Mr DIY Jingle: bar at 0:08", "One 4-beat bar of the jingle from about 8 s in, looped on the beat.", TAG_NOW,
     "sound/mrdiy/mrdiy_jingle.wav (bar at 0:08)", jingle_bar(4), [DIY]),
    ("drv_diy_jingle_b", "Mr DIY Jingle: bar at 0:22", "One 4-beat bar from about 22 s in, looped on the beat.", TAG_NOW,
     "sound/mrdiy/mrdiy_jingle.wav (bar at 0:22)", jingle_bar(11), [DIY]),
    ("drv_diy_jingle_c", "Mr DIY Jingle: bar at 0:42", "One 4-beat bar from about 42 s in (the loud part), looped on the beat.", TAG_NOW,
     "sound/mrdiy/mrdiy_jingle.wav (bar at 0:42)", jingle_bar(21), [DIY]),
]
sv.EXPLODE += [
    ("exp_diy_jingle_open", "Mr DIY Jingle: opening", "The first 3 s of the jingle.", TAG_NOW, "sound/mrdiy/mrdiy_jingle.wav (first 3 s)",
     lambda: sv.mod_wav(JINGLE)[int(0.7 * SR):int(3.7 * SR)], [DIY]),
    ("exp_diy_jingle_end", "Mr DIY Jingle: finale", "The last 3 s of the jingle, up to where the music stops.", TAG_NOW, "sound/mrdiy/mrdiy_jingle.wav (last 3 s)",
     jingle_tail, [DIY]),
]
sv.FUN_FOLDERS.insert(2, ("mrdiy", "Mr DIY"))

# curated clips that are one unmodified game sound (only the level differs)
sv.DIRECT_GAME_PATH.update({
    "exp_bryan_portal": "bryan/portal_die.wav", "exp_hm_crash": "hackmon/hm_crash.wav", "exp_hm_fatal": "hackmon/hm_fatal.wav",
    "exp_pickle_surprise": "pickle/surprise.wav", "exp_pickle_throw": "pickle/throw.wav", "exp_floathead_boing": "floathead/boing.wav",
    "exp_friends_no": "friends/no.wav",
})

# ----------------------------------------------------------------------------- the monsters
# (key, name, short name, note, game id (mb_pool), thumbnail file)
sv.MONSTERS += [
    (MEGA, "Mega Man Contraption", "Mega Man", "The Mega Man contraption (3D model)", 1, "01_megaman_contraption.png"),
    (PINK, "Exotic Pink Supercar", "Pink Supercar", "A pink supercar (3D model)", 3, "03_pink_supercar.png"),
    (PC, "NetSend 90s CRT PC", "NetSend PC", "The NetSend gun's old CRT PC (3D model)", 5, "05_netsend_pc.png"),
    (HORSE, "Golden West Casino Horse", "Casino Horse", "The horse from the Golden West Casino (3D model)", 6, "06_gw_horse.png"),
    (EARS, "Big-Ears Head", "Big-Ears", "The big-eared floating head (3D model)", 7, "07_bigears_head.png"),
    (FORK, "Larry's Warehouse Forklift", "Forklift", "The orange forklift from the warehouse (3D model)", 8, "08_forklift.png"),
    (EARHEAD, "Earhead", "Earhead", "A head with huge ears (24 sprite frames made)", 12, "12_earhead.png"),
    (PICKLE, "Pickle Surprise", "Pickle", "The pickle goblin from the Pickle Surprise bomb (one image)", 13, "13_pickle_surprise.png"),
    (HAND, "John Wave Hand", "John's Hand", "A hand holding a face, the John Wave gun's sprite", 15, "15_john_wave_hand.png"),
    (BRY, "Bryan & Demons", "Bryan", "Bryan with his demons: run, scan, surge, whirl and death animations", 17, "17_bryan_demons.png"),
    (DEN, "Dennis", "Dennis", "Dennis in a suit: idle, run in 8 directions, reading frames", 18, "18_dennis.png"),
    (PAUL, "Paul", "Paul", "Paul in a suit: idle, run in 8 directions, scream frames", 19, "19_paul.png"),
    (QG, "QuakeGuy", "QuakeGuy", "The guy in the Quake-logo shirt: idle, run, launch frames", 20, "20_quakeguy.png"),
    (DIY, "Mr DIY", "Mr DIY", "Mr DIY with his tools circling him: run frames and a laugh", 21, "21_mr_diy.png"),
    (FING, "Rubber Finger", "Rubber Finger", "A man running with a big rubber finger: run and bonk frames", 22, "22_rubber_finger.png"),
]

_NOTES = {ROB: "Friend Rob running (sprite)", ROLL: "Wheelman rolling along on his wheel (sprite)", WHEEL: "A guy on a single big wheel (sprite)",
          JESS: "Two women on a go-kart/trike (sprite)", KYLE: "Running with scissors (sprite)"}
sv.MONSTERS[:] = sorted(((k, n, s, _NOTES.get(k, d), g, t) for k, n, s, d, g, t in sv.MONSTERS), key=lambda r: r[4])

# kind (2D sprite / 3D model), ready: 2 = already a Mystery Box monster, 1 = sprite/frames exist but are not wired in, 0 = nothing built
NEW_IDS = {17, 18, 19, 20, 21, 22}
LAST_POOL = {2, 4, 9, 10, 11, 14, 16}              # the vote of 2026-10-31
KIND3D = {1, 2, 3, 4, 5, 6, 7, 8}
READY = {i: 2 for i in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 16, 17)}
READY.update({12: 1, 15: 1, 18: 1, 19: 1, 20: 1, 21: 1, 22: 1, 13: 0})
STAT = {2: "3D model, in the game", 1: "Built, not in the box yet", 0: "Only a still image so far"}
STATS_SPECIAL = {9: "Sprite, in the game", 10: "Sprite, in the game", 11: "Sprite, in the game", 14: "Sprite, in the game",
                 16: "Sprite, in the game", 17: "Sprite, in the game",
                 12: "Frames made, not in game yet", 15: "Wave-hand only, no run frames",
                 18: "Sprite built, not wired in", 19: "Sprite built, not wired in",
                 20: "Sprite built, not wired in", 21: "Sprite built, not wired in",
                 22: "Sprite built, not wired in", 13: "Only a still image so far"}
for key, name, short, note, gid, th in sv.MONSTERS:
    sv.MONSTER_EXTRA[key] = dict(kind="3D" if gid in KIND3D else "2D", isNew=gid in NEW_IDS, prev=gid in LAST_POOL,
                                 ready=READY[gid], stat=STATS_SPECIAL.get(gid) or STAT[READY[gid]])
# the old 7 keep their notes but need the extras too (they were listed above in MONSTERS already)

# ----------------------------------------------------------------------------- suggested sounds (listed after the clips made for each monster)
sv.SUGGEST_BASE.update({
    MEGA: {"drive": ["drv_mm_drive", "drv_megamotor", "drv_engine_grain", "drv_q_train"],
           "explode": ["exp_mm_boom09", "exp_sub_boom", "exp_q_rocket", "exp_car_boom"]},
    PINK: {"drive": ["drv_idle_coupe", "drv_engine_grain", "drv_kart_buzz", "drv_megamotor"],
           "explode": ["exp_car_boom", "exp_sub_boom", "exp_q_rocket", "exp_confetti_horn"]},
    PC: {"drive": ["drv_q_buzz", "drv_kazoo_engine", "drv_tippy_tap"],
         "explode": ["exp_sub_boom", "exp_glass_springs", "exp_q_rocket", "exp_balloon_pop"]},
    HORSE: {"drive": ["drv_boing_hop", "drv_q_hop", "drv_tippy_tap", "drv_icecream"],
            "explode": ["exp_confetti_horn", "exp_tada_chime", "exp_balloon_pop", "exp_boing_bang"]},
    EARS: {"drive": ["drv_boing_hop", "drv_icecream", "drv_kazoo_engine"],
           "explode": ["exp_boing_bang", "exp_sad_trombone", "exp_goo_pop", "exp_balloon_pop"]},
    FORK: {"drive": ["drv_idle_coupe", "drv_cart_rattle", "drv_q_train", "drv_q_drag"],
           "explode": ["exp_car_boom", "exp_sub_boom", "exp_glass_springs", "exp_q_pot_smash"]},
    EARHEAD: {"drive": ["drv_boing_hop", "drv_tippy_tap", "drv_icecream"],
              "explode": ["exp_balloon_pop", "exp_fart_pop", "exp_chicken_pop", "exp_boing_bang"]},
    PICKLE: {"drive": ["drv_boing_hop", "drv_q_hop", "drv_tippy_tap"],
             "explode": ["exp_goo_pop", "exp_fart_pop", "exp_q_zombie_gib", "exp_balloon_pop"]},
    HAND: {"drive": ["drv_tippy_tap", "drv_boing_hop", "drv_scissor_snip"],
           "explode": ["exp_balloon_pop", "exp_bonk_hit", "exp_boing_bang", "exp_confetti_horn"]},
    BRY: {"drive": ["drv_tippy_tap", "drv_q_buzz", "drv_unicycle_whir"],
          "explode": ["exp_scream_launch", "exp_sub_boom", "exp_q_coaled", "exp_mm_boom09"]},
    DEN: {"drive": ["drv_tippy_tap", "drv_tile_skate", "drv_suit_tie", "drv_boing_hop"],
          "explode": ["exp_suit_papers", "exp_sad_trombone", "exp_confetti_horn", "exp_chicken_pop"]},
    PAUL: {"drive": ["drv_tippy_tap", "drv_boing_hop", "drv_tile_skate"],
           "explode": ["exp_scream_launch", "exp_q_zombie_gib", "exp_mega_fart", "exp_sub_boom"]},
    QG: {"drive": ["drv_tippy_tap", "drv_q_hop", "drv_q_buzz"],
         "explode": ["exp_q_rocket", "exp_scream_launch", "exp_sub_boom", "exp_q_coaled"]},
    DIY: {"drive": ["drv_cart_rattle", "drv_scissor_snip", "drv_tippy_tap"],
          "explode": ["exp_glass_springs", "exp_q_pot_smash", "exp_wheel_blowout", "exp_chicken_pop"]},
    FING: {"drive": ["drv_boing_hop", "drv_tippy_tap", "drv_kazoo_engine"],
           "explode": ["exp_bonk_hit", "exp_balloon_pop", "exp_chicken_pop", "exp_fart_pop"]},
})

if __name__ == "__main__":
    sv.main()
