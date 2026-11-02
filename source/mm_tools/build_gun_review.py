"""Builds G:\\Quake\\Combat\\gun_review.html: a self-contained page to review every custom gun - 3D model (orbit and
in-game view with sliders to adjust the held pose), what it does, how it works, every sound it plays (with players)
and Keep / Change / Remove verdicts with notes.
python -I build_gun_review.py"""
import base64
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib
from PIL import Image
import io

ROOT = "G:\\Quake\\Combat\\"
MOD = ROOT + "BakersfieldQuake\\"
PROPS = "G:\\Downloads\\simready_out\\md3\\progs\\"
FRIENDS = "D:\\vibe\\megamanquake\\MegaKartArena\\public\\assets\\sprites\\"


def b64(b):
    return base64.b64encode(b).decode("ascii")


def wav(rel):
    return "data:audio/wav;base64," + b64(open(MOD + "sound\\" + rel.replace("/", "\\"), "rb").read())


def png_uri(path, maxw=None, darken=1.0):
    im = Image.open(path).convert("RGB")
    if darken != 1.0:
        im = im.point(lambda v: min(255, int(v / darken)))     # undo the in-game darkening for the preview
    if maxw and im.size[0] > maxw:
        im = im.resize((maxw, max(1, im.size[1] * maxw // im.size[0])))
    bio = io.BytesIO()
    im.save(bio, "PNG")
    return "data:image/png;base64," + b64(bio.getvalue())


def mesh(path, texdir, tex_darken=1.0):
    m = md3lib.read(path)
    surfs = []
    for s in m["surfaces"]:
        vv, nn = s["frames"][0]
        pos = b"".join(struct.pack("<3f", *v) for v in vv)
        uv = b"".join(struct.pack("<2f", u, 1 - v) for u, v in s["st"])
        idx = b"".join(struct.pack("<3H", *t) for t in s["tris"])
        tex = texdir + os.path.basename(s["shader"]) + ".png"
        surfs.append(dict(pos=b64(pos), uv=b64(uv), idx=b64(idx),
                          tex=png_uri(tex, 256, tex_darken) if os.path.exists(tex) else None))
    return surfs


def friend_thumbs():
    out = {}
    for n in ["rob"]:
        meta = json.load(open(FRIENDS + n + "_hi.json"))
        im = Image.open(FRIENDS + meta["pages"][0]["file"]).convert("RGBA")
        cw, ch = meta["cellW"], meta["cellH"]
        e = meta["anims"]["idle"]["dirs"][0]
        p = meta["pages"][e["page"]]
        i = e["start"]
        col, row = i % p["cols"], i // p["cols"]
        c = im.crop((col * cw, row * ch, (col + 1) * cw, (row + 1) * ch)).resize((cw * 110 // ch, 110))
        bio = io.BytesIO()
        c.save(bio, "PNG")
        out[n] = "data:image/png;base64," + b64(bio.getvalue())
    # John: the MegaKartArena head views and the hand frames, straight from the sprite sheets the game uses
    sp = "D:/vibe/megamanquake/MegaKartArena/public/assets/sprites/"

    def cellimg(sheet, cols, cw, ch, i):
        im = Image.open(sp + sheet).convert("RGBA")
        c, r = i % cols, i // cols
        c = im.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
        c = c.resize((max(1, c.size[0] * 110 // c.size[1]), 110))
        bio = io.BytesIO()
        c.save(bio, "PNG")
        return "data:image/png;base64," + b64(bio.getvalue())

    for i in (0, 4, 8, 12):
        out["john head, view %d of 16" % (i + 1)] = cellimg("johnhead.webp", 4, 256, 174, i)
    for i, label in ((0, "idle"), (4, "idle, hair swinging"), (8, "throw starts"), (20, "throw"), (35, "head leaves the hand"), (46, "throw ends")):
        out["john hand, %s" % label] = cellimg("johngun_vm.webp", 8, 320, 190, i)
    return out


# pose parameters, exactly as in build_fungun_viewmodels.py: prop, scale, (roll, pitch, yaw), pos (x fwd, y left, z up)
def pose_table():
    import re
    src = open(os.path.dirname(os.path.abspath(__file__)) + "\\build_fungun_viewmodels.py").read()
    block = src[src.index("GUNS = ["):src.index("]\n\n\ndef rot_x") + 1]
    ns = {}
    exec(block, ns)
    return {g[0]: dict(scale=g[2], rot=list(g[3]), pos=list(g[4])) for g in ns["GUNS"]}


poses = pose_table()

GUNS = [
    dict(id="megaman", name="Mega Man Launcher", kind="Thrown robot", key="9 (impulse 14)", model=("v_megaman.md3", None),
         summary="You throw a little wheeled Mega Man. He lands, drives straight, steers round walls, and when he spots someone he hops, honks, chases them and leaps on them like a headcrab.",
         how=["Ammo: 2 Mega Men, one comes back every 5 seconds.",
              "Throw: 1.2 s between throws. He flies out, lands on his wheels and drives about 200 units a second.",
              "Spots an enemy within 800 units: hop + horn, chase, then crouch and leap from 300 units away.",
              "Goes off on touching a player or monster: 60-75 direct damage, plus a 70-damage blast on anyone else close. Five head-on wall hits or 12 seconds and he blows up anyway.",
              "Other players see a little Mega Man in your hand.",
              "He has 40 health: you can shoot him down on the way and he just pops harmlessly (no damage)."],
         kill="X got run over by Y's Mega Man",
         sounds=[("mm_fire.wav", "megaman/mm_fire.wav", "Every throw: the 'megamayan' clip."),
                 ("mm_drive.wav", "megaman/mm_drive.wav", "While he drives: the echoey 'wewwewwew' clip with the silent gaps cut out, restarted the moment it ends so it never pauses."),
                 ("megahorn.wav", "weapons/megahorn.wav", "Foghorn blast when he spots someone and when he leaps (synthesised)."),
                 ("boom01.wav", "megaman/boom01.wav", "Explosion: one of 27 random clips, this one is 'ahlarry'."),
                 ("boom02.wav", "megaman/boom02.wav", "Explosion: one of 27 random clips, this one is 'gowewd'."),
                 ("boom03.wav", "megaman/boom03.wav", "Explosion: one of 27 random clips, this one is 'hello'."),
                 ("boom04.wav", "megaman/boom04.wav", "Explosion: one of 27 random clips, this one is 'hello2'."),
                 ("boom05.wav", "megaman/boom05.wav", "Explosion: one of 27 random clips, this one is 'howdoyoukeythat'."),
                 ("boom06.wav", "megaman/boom06.wav", "Explosion: one of 27 random clips, this one is 'i don\'t use windows 97'."),
                 ("boom07.wav", "megaman/boom07.wav", "Explosion: one of 27 random clips, this one is 'i\'m having a problem with my computer'."),
                 ("boom08.wav", "megaman/boom08.wav", "Explosion: one of 27 random clips, this one is 'i\'m not sure 2'."),
                 ("boom09.wav", "megaman/boom09.wav", "Explosion: one of 27 random clips, this one is 'ilovethatecho'."),
                 ("boom10.wav", "megaman/boom10.wav", "Explosion: one of 27 random clips, this one is 'im not sure'."),
                 ("boom11.wav", "megaman/boom11.wav", "Explosion: one of 27 random clips, this one is 'interesting'."),
                 ("boom12.wav", "megaman/boom12.wav", "Explosion: one of 27 random clips, this one is 'it won\'t boot'."),
                 ("boom13.wav", "megaman/boom13.wav", "Explosion: one of 27 random clips, this one is 'johnnnny'."),
                 ("boom14.wav", "megaman/boom14.wav", "Explosion: one of 27 random clips, this one is 'no'."),
                 ("boom15.wav", "megaman/boom15.wav", "Explosion: one of 27 random clips, this one is 'no 2'."),
                 ("boom16.wav", "megaman/boom16.wav", "Explosion: one of 27 random clips, this one is 'oh windows me'."),
                 ("boom17.wav", "megaman/boom17.wav", "Explosion: one of 27 random clips, this one is 'should i reformat'."),
                 ("boom18.wav", "megaman/boom18.wav", "Explosion: one of 27 random clips, this one is 'thats double good'."),
                 ("boom19.wav", "megaman/boom19.wav", "Explosion: one of 27 random clips, this one is 'thats good'."),
                 ("boom20.wav", "megaman/boom20.wav", "Explosion: one of 27 random clips, this one is 'uhhuh'."),
                 ("boom21.wav", "megaman/boom21.wav", "Explosion: one of 27 random clips, this one is 'wave'."),
                 ("boom22.wav", "megaman/boom22.wav", "Explosion: one of 27 random clips, this one is 'who are you'."),
                 ("boom23.wav", "megaman/boom23.wav", "Explosion: one of 27 random clips, this one is 'who are youuuuuuu'."),
                 ("boom24.wav", "megaman/boom24.wav", "Explosion: one of 27 random clips, this one is 'windows me'."),
                 ("boom25.wav", "megaman/boom25.wav", "Explosion: one of 27 random clips, this one is 'windows me 2'."),
                 ("boom26.wav", "megaman/boom26.wav", "Explosion: one of 27 random clips, this one is 'windowsheh'."),
                 ("boom27.wav", "megaman/boom27.wav", "Explosion: one of 27 random clips, this one is 'youredoublegood'.")],
         stock="Throw also plays the stock grenade thump; the explosion still has the stock rocket boom under the random clip.",
         status="Done and in the game. BALANCE PASS: he used to be a homing rocket (100-120 direct + rocket blast, 3 shots, 3 s refill, 20 s life), so everybody spawning with it meant constant near-unavoidable deaths. Now 2 shots, 5 s refill, 12 s life, weaker hit. The Larry throw clips were replaced by megamayan."),
    dict(id="bonk", name="Whack-a-Mole", kind="Thrown melee", key="F (impulse 61)", prop="sledge", model=("v_sledge.md3", "sledge"),
         summary="You hurl a sledgehammer. A hit does BONK: damage and the victim shrinks to under half size for 7 seconds with little stars circling.",
         how=["Ammo: 3 hammers, one comes back every 3 seconds. Fire delay 0.7 s.",
              "The hammer flies 950 units a second, end over end at double size. One bonk per throw.",
              "35 damage. The victim shrinks to 45% (and their view drops to the floor) for 7 seconds.",
              "Bonk someone who is already tiny: +20 'pancake' damage (55 total), so three hits kill a full-health player.",
              "A hammer bouncing off a wall plays a quiet clank."],
         kill="X got bonked into next week by Y",
         sounds=[("fg_bonk_fire.wav", "fungun/fg_bonk_fire.wav", "Throw whoosh."),
                 ("fg_bonk_hit.wav", "fungun/fg_bonk_hit.wav", "Wood-block BONK followed by a falling slide whistle."),
                 ("fg_bonk_tweet.wav", "fungun/fg_bonk_tweet.wav", "Dizzy birds chirping around the victim."),
                 ("fg_fork_hit.wav", "fungun/fg_fork_hit.wav", "Reused (high-pitched) as the clank when the hammer hits a wall.")],
         stock="",
         status="Built, runs, bonks confirmed in the bot test. BALANCE PASS: two hits used to kill (40 + 70); now it takes three."),
    dict(id="pong", name="Rally Master", kind="Ricochet spam", key="G (impulse 62)", prop="paddle", model=("v_paddle.md3", "paddle"),
         summary="A ping-pong paddle that hits balls at people. Every bounce off a wall makes the ball hit harder, so use the walls.",
         how=["Ammo: 12 balls, one comes back every 0.7 s. Fire delay 0.2 s.",
              "Balls fly 1000 units a second and bounce up to 8 times, then die.",
              "Damage = 4 + 5 per bounce, capped at 34. Three or more bounces shows 'RALLY xN!' on your screen.",
              "After its first bounce the ball can hit you too, for half damage."],
         kill="X lost a ping-pong rally to Y",
         sounds=[("fg_pong_fire.wav", "fungun/fg_pong_fire.wav", "Paddle 'tock' each shot."),
                 ("fg_pong_bounce.wav", "fungun/fg_pong_bounce.wav", "Ball bounce; higher pitched every bounce."),
                 ("fg_pong_hit.wav", "fungun/fg_pong_hit.wav", "Game-show 'ding' when it hits someone, higher with more bounces.")],
         stock="",
         status="Built, runs, kills confirmed in the bot test. BALANCE PASS: it was a 6-shots-a-second machine gun whose balls reached 75 damage in tight rooms. Now slower, capped at 34, and your own ricochets only hurt half."),
    dict(id="hack", name="Hack Attack", kind="Runner projectile + shock", key="X (impulse 63)", model=("v_hackmon.md3", None),
         summary="You hold the monitor (NVIDIA SimReady monitor_a01) and fire a Rob out of it. He appears right in front of you and runs straight ahead for a second, then chases the nearest enemy. When he touches someone he turns into green electricity, clings on and shocks them, then explodes into computer junk and lightning.",
         how=["Ammo: 2 Robs, one comes back every 5 seconds. Fire delay 1.3 s.",
              "Rob is the 8-direction photo sprite from MegaKartArena (turns to face you like a Doom sprite). He appears 56 units in front of you and runs straight ahead for the first second, so you can watch him go.",
              "After that second he chases the closest enemy he can see (up to 1200 units) at 300 units a second, slower than a running player. He beeps while he runs and shouts 'HACKING. HACKING.' when he spots someone.",
              "Within about 48 units of an enemy he turns into strobing green electricity, clings on just behind them (out of their view) for 0.8 seconds and shocks them: 5 damage every 0.2 s, the screen shakes, bolts crackle.",
              "Then he explodes: up to 35 damage and 11 pieces of junk bounce out for 3-5 seconds: always a keyboard, a fedora and a circuit board, plus random mice, floppy disks, CDs, a little monitor, or a sledgehammer. The junk is only decoration.",
              "Green lightning keeps arcing for 1.6 seconds: anyone within about 110 units with a clear line takes 3 every 0.2 s (up to 24).",
              "If nobody is close when his 9 seconds run out, or he gets stuck, he just vibrates and blows up on the spot. He never targets you, or your team under teamplay.",
              "Worst case all of it hits one person who stands still: about 20 shock + 35 blast + 24 field = 79.",
              "Rob has 30 health: shoot him down while he runs and he fizzles in a few sparks and some junk (no damage). Once he is shocking someone he cannot be shot."],
         kill="X got hacked by Y's Rob",
         sounds=[("hm_launch.wav", "hackmon/hm_launch.wav", "Rob appearing: dial-up modem screech and a power-on whine."),
                 ("hm_beep1.wav", "hackmon/hm_beep1.wav", "While Rob runs: rising arpeggio (one of three random beeps every ~0.4 s)."),
                 ("hm_beep2.wav", "hackmon/hm_beep2.wav", "While Rob runs: data-bus chatter."),
                 ("hm_beep3.wav", "hackmon/hm_beep3.wav", "While Rob runs: boop-bep and a glitch stutter."),
                 ("hm_hacking.wav", "hackmon/hm_hacking.wav", "Robot voice 'HACKING. HACKING.' when he spots an enemy, and again, higher pitched, when he starts shocking."),
                 ("hm_zap.wav", "hackmon/hm_zap.wav", "Electric crackle while he shocks and while the field arcs."),
                 ("hm_crash.wav", "hackmon/hm_crash.wav", "The finale: glass smash, CRT bang, error chord, arcing."),
                 ("hm_imin.wav", "hackmon/hm_imin.wav", "Robot 'I'm in' when it goes off next to the target."),
                 ("hm_fatal.wav", "hackmon/hm_fatal.wav", "Robot 'Fatal error' when it goes off with nobody close.")],
         stock="The explosion has no stock sound or fire effect any more, it is all the sounds above plus the lightning. The voices are Windows speech, robotised, so they sound dry; tell me if you want a different voice.",
         status="Tested in the arena: Rob appears in front of you, runs off, turns around and chases, shocks (health dropped 5 at a time), then the junk (keyboard, floppy, fedora) flew out. I have never heard the sounds, only generated them. The in-hand screen is a fixed picture."),
    dict(id="john", name="John Wave Grenade", kind="Thrown head + tidal wave", key="V (impulse 64)", model=("johnhead3d.md3", None),
         summary="From MegaKartArena. Hold fire and John sits in your hand with his hair swaying. Let go and John's head flies out slowly, spinning and chattering. Where it lands a tidal wave spreads out and lifts everyone it passes into the air for a few seconds. It is bad at killing on purpose: the point is where everyone ends up. The thrown head is a 3D model rebuilt in Blender from the MegaKart turntable clip; John in your hand is still the MegaKart picture.",
         how=["Ammo: 2 throws, one comes back every 6 seconds.",
              "Hold fire: John is in your hand (the hand sprite is the 49-frame MegaKart sheet; the hair sways faster the longer you hold). Switching weapons cancels for free. Held longer than 3 seconds it throws by itself.",
              "Let go: the throw animation plays for 0.8 s, then the head leaves at 520 units a second (slower than a rocket). It is the 3D head (1.5x, about 40 units), spinning, and John shouts random voice clips while it flies.",
              "Impact: 30-40 damage to what it hits and 40 splash. Then the wave ring grows out from the spot at 220 units a second to 420 units.",
              "Everyone the wave passes (including you if you are close) is pushed outward and lifted: low gravity for 4 seconds, so a slow rise, a hang, then a fall. You can still shoot and move your aim while floating. 'THE JOHN WAVE, you are floating' appears on their screen.",
              "The landing from height can hurt a little."],
         kill="X got swept away by Y's John wave",
         sounds=[("jwthrow.wav", "john/jwthrow.wav", "On the throw: John's 'John Wave' line from MegaKart."),
                 ("jv00.wav", "john/jv00.wav", "John voice clip 0: plays while the head flies and as the wave lifts you."),
                 ("jv01.wav", "john/jv01.wav", "John voice clip 1: plays while the head flies and as the wave lifts you."),
                 ("jv02.wav", "john/jv02.wav", "John voice clip 2: plays while the head flies and as the wave lifts you."),
                 ("jv03.wav", "john/jv03.wav", "John voice clip 3: plays while the head flies and as the wave lifts you."),
                 ("jv04.wav", "john/jv04.wav", "John voice clip 4: plays while the head flies and as the wave lifts you."),
                 ("jv05.wav", "john/jv05.wav", "John voice clip 5: plays while the head flies and as the wave lifts you."),
                 ("jv06.wav", "john/jv06.wav", "John voice clip 6: plays while the head flies and as the wave lifts you."),
                 ("jv07.wav", "john/jv07.wav", "John voice clip 7: plays while the head flies and as the wave lifts you."),
                 ("jv08.wav", "john/jv08.wav", "John voice clip 8: plays while the head flies and as the wave lifts you."),
                 ("jv09.wav", "john/jv09.wav", "John voice clip 9: plays while the head flies and as the wave lifts you."),
                 ("jv10.wav", "john/jv10.wav", "John voice clip 10: plays while the head flies and as the wave lifts you."),
                 ("jv11.wav", "john/jv11.wav", "John voice clip 11: plays while the head flies and as the wave lifts you."),
                 ("jv12.wav", "john/jv12.wav", "John voice clip 12: plays while the head flies and as the wave lifts you."),
                 ("jv13.wav", "john/jv13.wav", "John voice clip 13: plays while the head flies and as the wave lifts you."),
                 ("jv14.wav", "john/jv14.wav", "John voice clip 14: plays while the head flies and as the wave lifts you."),
                 ("jv15.wav", "john/jv15.wav", "John voice clip 15: plays while the head flies and as the wave lifts you."),
                 ("jv16.wav", "john/jv16.wav", "John voice clip 16: plays while the head flies and as the wave lifts you."),
                 ("jv17.wav", "john/jv17.wav", "John voice clip 17: plays while the head flies and as the wave lifts you."),
                 ("jv18.wav", "john/jv18.wav", "John voice clip 18: plays while the head flies and as the wave lifts you."),
                 ("jv19.wav", "john/jv19.wav", "John voice clip 19: plays while the head flies and as the wave lifts you."),
                 ("jv20.wav", "john/jv20.wav", "John voice clip 20: plays while the head flies and as the wave lifts you."),
                 ("jv21.wav", "john/jv21.wav", "John voice clip 21: plays while the head flies and as the wave lifts you."),
                 ("jv22.wav", "john/jv22.wav", "John voice clip 22: plays while the head flies and as the wave lifts you.")],
         stock="The impact boom is the stock rocket explosion at low pitch.",
         status="Back in with the 3D head. Tested in the arena: hold, throw animation, the 3D head flying, and the wave ring. I have not heard the sounds. The voice clips are the MegaKart ones; I did not check what each says."),
]

# bake
out = []
for g in GUNS:
    d = dict(id=g["id"], name=g["name"], kind=g["kind"], key=g["key"], summary=g["summary"], how=g["how"], kill=g["kill"],
             stock=g["stock"], status=g["status"])
    vm, prop = g["model"]
    if prop:
        p = poses[prop]
        d["adjust"] = dict(prop=prop, scale=p["scale"], rot=p["rot"], pos=p["pos"])
        d["mesh"] = mesh(PROPS + prop + ".md3", MOD + "progs\\", 0.5)
    else:
        d["adjust"] = None
        d["mesh"] = mesh(MOD + "progs\\" + vm, MOD + "progs\\", 1.0)
    d["sounds"] = [dict(file=f, desc=desc, uri=wav(rel)) for f, rel, desc in g["sounds"]]
    out.append(d)

html = open(os.path.dirname(os.path.abspath(__file__)) + "\\gun_review.template.html", encoding="utf-8").read()
html = html.replace("/*GUNS*/[]", json.dumps(out, separators=(",", ":")))
html = html.replace("/*FRIENDS*/{}", json.dumps(friend_thumbs(), separators=(",", ":")))
open(ROOT + "gun_review.html", "w", encoding="utf-8").write(html)
print("wrote gun_review.html", round(os.path.getsize(ROOT + "gun_review.html") / 1e6, 2), "MB")
