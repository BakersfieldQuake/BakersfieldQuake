"""Every sound the custom guns play, and where in the QC each one is set.  Used by build_gun_sound_editor.py (the page)
and apply_gun_sounds.py (writes the picks back into the QC).

An event is one place the game plays a sound:
  id     short name, unique inside its gun
  label  what you hear it as
  hint   when it plays
  file   QC file in mm_tools
  ctx    regex that finds the sound call; group 1 is the sound's path.  Every match is changed together
         (so an event can be two or three lines in the QC that are really one sound).
  vol    volume the game plays it at;  rate  playback speed (1 = normal; the game's pitch/100)
  loop   the game plays it again each time it ends (the page repeats it in the simulation)
  lenvar (file, regex): the QC constant holding the sound's length for that restart (group 1 = text before the number, group 2 =
         the number); apply_gun_sounds.py rewrites it to the new sound's length
  pool   read-only: a set of clips the game picks from (path pattern with {n}, how many), not changed by the page

A scenario is a short play of the gun: [event id, seconds after the shot, optional {vol, rate} overrides].
"""

GUNS = [
    dict(id="dob", name="Rob Dob", sub="fun gun 1 (impulse 61 or 17): the floating head", file="floathead.qc",
         scenarios=[
             ("Fly, dash, blast", [("launch", 0), ("hum", 0.3), ("hum", 1.66), ("hum", 3.02), ("dash", 3.4), ("blast_bang", 5.0), ("blast_heh", 5.0),
                                   ("minis", 5.3), ("minis", 5.6)]),
             ("Runs out of time", [("launch", 0), ("hum", 0.3), ("hum", 1.66), ("pop", 3.0), ("pop_scream", 3.0), ("minis", 3.3)]),
             ("Gets shot down", [("launch", 0), ("hum", 0.3), ("hurt", 1.2), ("blast_bang", 2.0), ("blast_heh", 2.0), ("minis", 2.3)]),
         ],
         events=[
             dict(id="launch", label="Head launches out of you", hint="a little computer booting up", file="floathead.qc",
                  ctx=r'sound \(h, CHAN_VOICE, "([^"]+)", 0\.6', vol=0.6),
             dict(id="hum", label="Constant hum while flying", hint="played again each time it ends", file="floathead.qc",
                  ctx=r'sound \(self, CHAN_ITEM, "([^"]+)", FD_HUM_VOL', vol=0.4, loop=True,
                  lenvar=("floathead.qc", r'(float\s+FD_HUM_LEN\s*=\s*)([0-9.]+)')),
             dict(id="dash", label="Dash (you click fire)", hint="the head charges", file="floathead.qc",
                  ctx=r'sound \(h, CHAN_VOICE, "([^"]+)", 1, ATTN_NORM\);\n\};', vol=1),
             dict(id="blast_bang", label="Blast: the bang", hint="it hits someone or you click again", file="floathead.qc",
                  ctx=r'sound \(self, CHAN_WEAPON, "([^"]+)", 1, ATTN_NORM\);\n\tsound \(self, CHAN_VOICE, "[^"]+", 1, ATTN_NORM\);\t\t// \.\.\.and a', vol=1),
             dict(id="blast_heh", label="Blast: the voice on top", hint="said as it goes off", file="floathead.qc",
                  ctx=r'sound \(self, CHAN_VOICE, "([^"]+)", 1, ATTN_NORM\);\t\t// \.\.\.and a', vol=1),
             dict(id="minis", label="Little heads bounce", hint="six small heads tumble out of the blast", file="floathead.qc",
                  ctx=r'sound \(self, CHAN_BODY, "([^"]+)", 0\.7', vol=0.7),
             dict(id="pop", label="Time runs out: pop", hint="harmless pop, you are back in your body", file="floathead.qc",
                  ctx=r'sound \(self, CHAN_VOICE, "([^"]+)", 1, ATTN_NORM\);\n\tsound \(self, CHAN_WEAPON, "[^"]+", 1, ATTN_NORM\);\n\tSpawnBlood', vol=1),
             dict(id="pop_scream", label="Time runs out: scream", hint="under the pop", file="floathead.qc",
                  ctx=r'sound \(self, CHAN_WEAPON, "([^"]+)", 1, ATTN_NORM\);\n\tSpawnBlood', vol=1),
             dict(id="hurt", label="Head is shot at", hint="it has 60 health", file="floathead.qc",
                  ctx=r'sound \(self, CHAN_VOICE, "([^"]+)", 1, ATTN_NORM\);\n\};', vol=1),
             dict(id="song", label="The calc song (computer tune)", hint="60 slices, 5 s each, quietly under the hum", file="floathead.qc",
                  pool=("floathead/calc/c{n}.wav", 60), vol=0.2),
         ]),

    dict(id="pong", name="Rally Master", sub="fun gun 2 (impulse 62): ping-pong paddle", file="funguns.qc",
         scenarios=[("Serve and rally", [("fire", 0), ("bounce", 0.25, {"rate": 0.93}), ("bounce", 0.55, {"rate": 1.01}),
                                         ("bounce", 0.9, {"rate": 1.09}), ("hit", 1.25, {"rate": 1.28})])],
         events=[
             dict(id="fire", label="Ball leaves the paddle", hint="pitch varies a little each shot", file="funguns.qc",
                  ctx=r'FG_Snd \(self, CHAN_WEAPON, "([^"]+)", 0\.9', vol=0.9),
             dict(id="bounce", label="Ball bounces", hint="goes up in pitch with every bounce", file="funguns.qc",
                  ctx=r'FG_Snd \(self, CHAN_AUTO, "([^"]+)", 0\.7', vol=0.7, rate=0.95),
             dict(id="hit", label="Ball hits someone", hint="higher with more bounces", file="funguns.qc",
                  ctx=r'FG_Snd \(self, CHAN_AUTO, "([^"]+)", 1, 1 \+', vol=1),
         ]),

    dict(id="pickle", name="Pickle Surprise", sub="fun gun 3 (impulse 63): the sticky pickle", file="pickle.qc",
         scenarios=[("Throw, stick, surprise", [("throw", 0), ("stick", 0.6), ("shout", 3.0), ("shout", 3.0), ("explode", 4.35)])],
         events=[
             dict(id="throw", label="Throw", hint="the pickle leaving your hand", file="pickle.qc",
                  ctx=r'FG_Snd \(self, CHAN_WEAPON, "([^"]+)", 1, 1\);\n\tself\.punchangle', vol=1),
             dict(id="stick", label="Sticks to a surface", hint="quiet and a little low", file="pickle.qc",
                  ctx=r'FG_Snd \(self, CHAN_AUTO, "([^"]+)", 0\.5, 0\.7', vol=0.5, rate=0.7),
             dict(id="shout", label="The shout while it swells", hint="played twice at once, so it is extra loud", file="pickle.qc",
                  ctx=r'FG_Snd \(self, CHAN_(?:VOICE|ITEM), "([^"]+)"', vol=1),
             dict(id="explode", label="Explodes", hint="the green blast", file="pickle.qc",
                  ctx=r'FG_Snd \(self, CHAN_WEAPON, "([^"]+)", 1, 1\);\t\t// the line has just ended', vol=1),
         ]),

    dict(id="sentry", name="Sentry Gun", sub="fun gun 4 (impulse 64, key B): the spanner", file="sentry.qc",
         scenarios=[("Build, spot, shoot, destroyed", [("place", 0), ("ready", 2.0), ("spot", 4.5), ("shoot", 4.7), ("shoot", 5.0), ("shoot", 5.3),
                                                      ("idle", 8.0), ("explode", 10.0)])],
         events=[
             dict(id="place", label="You put it down", hint="the moment you build it", file="sentry.qc",
                  ctx=r'sound7 \(g, CHAN_WEAPON, "([^"]+)"', vol=1),
             dict(id="ready", label="It wakes up", hint="2 seconds later, when it is ready", file="sentry.qc",
                  ctx=r'sound7 \(self, CHAN_VOICE, "([^"]+)", 1, ATTN_NORM, SNDSPD\);\n\tSentry_Stand', vol=1),
             dict(id="spot", label="Spots a target", hint="when it locks on", file="sentry.qc",
                  ctx=r'sound7 \(self, CHAN_VOICE, "([^"]+)", 1, ATTN_NORM, SNDSPD\);\n\tself\.ideal_yaw', vol=1),
             dict(id="shoot", label="Each shot", hint="the sentry firing", file="sentry.qc",
                  ctx=r'sound7 \(self, CHAN_WEAPON, "([^"]+)", 1, ATTN_NORM, SNDSPD\);\n\n\tself\.v_angle', vol=1),
             dict(id="idle", label="Idle sweep", hint="now and then while it scans", file="sentry.qc",
                  ctx=r'sound7 \(self, CHAN_ITEM, "([^"]+)"', vol=1),
             dict(id="explode", label="Destroyed", hint="blows up", file="sentry.qc",
                  ctx=r'sound7 \(self, CHAN_AUTO, "([^"]+)", 1, ATTN_NORM, SNDSPD\);\n\tBecomeExplosion', vol=1),
         ]),

    dict(id="mega", name="Mega Man", sub="key 9 (impulse 14): the little robot", file="megaman.qc",
         scenarios=[("Throw, drive, blow up", [("windup", 0), ("launch", 0.15), ("voice", 0.15), ("land", 0.9), ("horn", 1.4), ("drive", 1.6),
                                               ("drive", 2.2), ("bounce", 3.0), ("explode", 4.0), ("debris_a", 4.6), ("debris_b", 5.0)]),
                    ("Shot down on the way", [("windup", 0), ("launch", 0.15), ("voice", 0.15), ("blast_zing", 1.5), ("blast_clank", 1.5), ("boom", 1.5),
                                              ("debris_a", 2.1), ("debris_b", 2.5)])],
         events=[
             dict(id="windup", label="Fire pressed (wind-up)", hint="a swish as you start the throw", file="megaman.qc",
                  ctx=r'MM_Sound \(self, CHAN_AUTO, "([^"]+)", 0\.8', vol=0.8),
             dict(id="launch", label="Launch", hint="he leaves your hand", file="megaman.qc",
                  ctx=r'MM_Sound \(self, CHAN_WEAPON, "([^"]+)", 1, 100\);\n#ifdef COMBATPLUS\n\tMegaMan_Larry', vol=1),
             dict(id="voice", label="Voice on every throw", hint="the \"megamayan\" shout", file="megaman.qc",
                  ctx=r'MM_Sound \(self, CHAN_VOICE, "([^"]+)", 1, 100\);\n\};\n\n// a random clip', vol=1),
             dict(id="land", label="Lands and starts driving", hint="when he touches down", file="megaman.qc",
                  ctx=r'MM_Sound \(self, CHAN_ITEM, "([^"]+)", 1, 100\);\n\t\t\}\n\t\treturn;', vol=1),
             dict(id="horn", label="Horn", hint="when he takes off after a target", file="megaman.qc",
                  ctx=r'MM_Sound \(self, CHAN_VOICE, "([^"]+)", 1, horn\)', vol=1),
             dict(id="drive", label="Driving motor", hint="played again each time it ends", file="megaman.qc",
                  ctx=r'MM_SoundA \(self, CHAN_BODY, "([^"]+)", 1, pitch, 0\.45\);\n\t\tself\.mm_motor = time \+ MM_DRIVE_LEN', vol=1, loop=True,
                  lenvar=("megaman_defs.qc", r'(float\s+MM_DRIVE_LEN\s*=\s*)([0-9.]+)')),
             dict(id="bounce", label="Bounces", hint="each time he bounces off something", file="megaman.qc",
                  ctx=r'MM_Sound \(self, CHAN_ITEM, "([^"]+)", 1, 100\);\n\t\}\n', vol=1),
             dict(id="explode", label="Explodes", hint="the same explosion as a rocket (sound and effect)", file="megaman.qc",
                  ctx=r'MM_Sound \(self, CHAN_WEAPON, "([^"]+)", 1, 100\);\n#else', vol=1),
             dict(id="blast_zing", label="Shot down: the zing", hint="low, when he is shot down (not a real explosion)", file="megaman.qc",
                  ctx=r'MM_SoundA \(self, CHAN_WEAPON, "([^"]+)", 1, 80', vol=1, rate=0.8),
             dict(id="blast_clank", label="Shot down: the clank", hint="very low, under the zing", file="megaman.qc",
                  ctx=r'MM_SoundA \(self, CHAN_ITEM, "([^"]+)", 1, 60', vol=1, rate=0.6),
             dict(id="boom", label="Shot down: random voice clip", hint="one of 27 clips when he is shot down", file="megaman.qc",
                  pool=("megaman/boom{n:02d}.wav", 27, 1), vol=1),
             dict(id="debris_a", label="Wreckage clank A", hint="a wheel or axle hits something (half the time)", file="megaman.qc",
                  ctx=r'MM_SoundA \(self, CHAN_AUTO, "([^"]+)", 0\.8', vol=0.8, rate=1.1),
             dict(id="debris_b", label="Wreckage clank B", hint="the other half of the time", file="megaman.qc",
                  ctx=r'MM_SoundA \(self, CHAN_AUTO, "([^"]+)", 0\.45', vol=0.45, rate=1.3),
             dict(id="empty", label="Out of ammo", hint="a click while he is still recharging", file="megaman.qc",
                  ctx=r'MM_Sound \(self, CHAN_WEAPON, "([^"]+)", 0\.4', vol=0.4),
         ]),

    dict(id="goo", name="Goo Gun", sub="replaces the shotgun", file="goo.qc",
         scenarios=[("Shoot a wall", [("fire", 0), ("splat", 0.4), ("pop", 6.0)]),
                    ("Shoot a player", [("fire", 0), ("stick", 0.3), ("pop", 6.0)])],
         events=[
             dict(id="fire", label="Fire", hint="the blob leaving the gun", file="goo.qc",
                  ctx=r'Goo_Snd \(self, CHAN_WEAPON, "([^"]+)"', vol=1),
             dict(id="splat", label="Splats on a surface", hint="floor, wall or ceiling", file="goo.qc",
                  ctx=r'Goo_Snd \(self, CHAN_AUTO, "([^"]+)", 0\.9', vol=0.9),
             dict(id="stick", label="Sticks to a player", hint="when it hits someone", file="goo.qc",
                  ctx=r'Goo_Snd \(other, CHAN_AUTO, "([^"]+)"', vol=1),
             dict(id="pop", label="Pops", hint="the puddle bursts after a while", file="goo.qc",
                  ctx=r'Goo_Snd \(self, CHAN_AUTO, "([^"]+)", 0\.8', vol=0.8),
         ]),

    dict(id="sniper", name="Sniper Rifle", sub="replaces the nailgun: hold to charge, release to fire", file="sniper.qc",
         scenarios=[("Take a shot", [("shot", 0)])],
         events=[
             dict(id="shot", label="The shot", hint="on release", file="sniper.qc",
                  ctx=r'sound7 \(self, CHAN_WEAPON, "([^"]+)"', vol=1),
         ]),

    dict(id="hammer", name="Bonk Hammer", sub="replaces the axe", file="hammer.qc",
         scenarios=[("Swing and hit a player", [("swing", 0), ("hit_a", 0.25), ("pan", 0.25, {"vol": 1})]),
                    ("Hit a wall (low, medium, high)", [("wall_low", 0, {"vol": 0.3}), ("wall_low", 1.2, {"vol": 0.6}), ("wall_high", 2.4)]),
                    ("Air dash (low, medium, high)", [("dash_low", 0), ("dash_med", 1.2), ("dash_high", 2.4)]),
                    ("Charge up", [("charge_med", 0), ("charge_full", 1.5)])],
         events=[
             dict(id="swing", label="Swing", hint="every swing, hit or miss", file="hammer.qc",
                  ctx=r'Hammer_Snd \("([^"]+)", 1\);\n\tHammer_Body1', vol=1),
             dict(id="hit_a", label="Hit: version A", hint="half the time", file="hammer.qc",
                  ctx=[r'random \(\) < 0\.5\)\s+Hammer_Snd \("([^"]+)", 1\);\s+else\s+Hammer_Snd \("[^"]+", 1\);'], vol=1),
             dict(id="hit_b", label="Hit: version B", hint="the other half", file="hammer.qc",
                  ctx=[r'random \(\) < 0\.5\)\s+Hammer_Snd \("[^"]+", 1\);\s+else\s+Hammer_Snd \("([^"]+)", 1\);'], vol=1),
             dict(id="pan", label="Frying-pan clang", hint="on a player or a monster kill; louder with charge", file="hammer.qc",
                  ctx=[r'dmg \* 2\);\s+if \(random \(\) < 0\.5\)\s+Hammer_Snd \("[^"]+", 1\);\s+else\s+Hammer_Snd \("[^"]+", 1\);\s+if \(tier == 1\)\s+Hammer_Snd \("([^"]+)", 0\.25\);\s+else if \(tier == 2\)\s+Hammer_Snd \("([^"]+)", 0\.5\);\s+else\s+Hammer_Snd \("([^"]+)", 1\);',
                       r'== "player"\)\s+\{[^}]*?if \(tier == 1\)\s+Hammer_Snd \("([^"]+)", 0\.4\);\s+else if \(tier == 2\)\s+Hammer_Snd \("([^"]+)", 0\.7\);\s+else\s+Hammer_Snd \("([^"]+)", 1\);'], vol=0.7),
             dict(id="wall_low", label="Hits a wall: low and medium charge", hint="the bonk hop", file="hammer.qc",
                  ctx=[r'HM_HOP_(?:LOW|MED);\s+Hammer_Snd \("([^"]+)", 0\.[36]\);'], vol=0.45),
             dict(id="wall_high", label="Hits a wall: full charge", hint="the bonk hop", file="hammer.qc",
                  ctx=[r'HM_HOP_HIGH;\s+Hammer_Snd \("([^"]+)", 0\.8\);'], vol=0.8),
             dict(id="dash_low", label="Air dash: low charge", hint="swing at nothing in the air", file="hammer.qc",
                  ctx=[r'Hammer_Spark \(1, tier\);\s+if \(tier == 1\)\s+Hammer_Snd \("([^"]+)", 0\.25\);'], vol=0.25),
             dict(id="dash_med", label="Air dash: medium charge", hint="", file="hammer.qc",
                  ctx=[r'Hammer_Spark \(1, tier\);\s+if \(tier == 1\)\s+Hammer_Snd \("[^"]+", 0\.25\);\s+else if \(tier == 2\)\s+Hammer_Snd \("([^"]+)", 0\.5\);'], vol=0.5),
             dict(id="dash_high", label="Air dash: full charge", hint="", file="hammer.qc",
                  ctx=[r'Hammer_Spark \(1, tier\);\s+if \(tier == 1\)\s+Hammer_Snd \("[^"]+", 0\.25\);\s+else if \(tier == 2\)\s+Hammer_Snd \("[^"]+", 0\.5\);\s+else\s+Hammer_Snd \("([^"]+)", 1\);'], vol=1),
             dict(id="charge_med", label="Charge reaches medium", hint="while you hold fire", file="hammer.qc",
                  ctx=[r'tier == 2\)\s+Hammer_Snd \("([^"]+)", 0\.4\);\s+else\s+Hammer_Snd \("[^"]+", 0\.8\);'], vol=0.4),
             dict(id="charge_full", label="Charge reaches full", hint="while you hold fire", file="hammer.qc",
                  ctx=[r'tier == 2\)\s+Hammer_Snd \("[^"]+", 0\.4\);\s+else\s+Hammer_Snd \("([^"]+)", 0\.8\);'], vol=0.8),
         ]),

    dict(id="john", name="Grenade Launcher (John's head)", sub="the stock grenade launcher with John's head and a splash", file="jg_splash.qc",
         scenarios=[("Bounce, bounce, splash", [("bounce", 0.4), ("bounce", 0.9), ("boom_a", 2.5)]),
                    ("The other splash", [("bounce", 0.4), ("boom_b", 2.0)])],
         events=[
             dict(id="bounce", label="Bounce", hint="every bounce of the head", file="jg_splash.qc",
                  ctx=r'sound7 \(self, CHAN_WEAPON, "([^"]+)", 1, ATTN_NORM, SNDSPD\)', vol=1),
             dict(id="boom_a", label="Goes off: version A", hint="half the time", file="jg_splash.qc",
                  ctx=r'sound \(self, CHAN_VOICE, "([^"]+)", 1, ATTN_NORM\);\n\telse', vol=1),
             dict(id="boom_b", label="Goes off: version B", hint="the other half", file="jg_splash.qc",
                  ctx=r'else\n\t\tsound \(self, CHAN_VOICE, "([^"]+)"', vol=1),
         ]),

    dict(id="shared", name="Fun guns: shared", sub="played by Rob Dob, Pickle Surprise and Sentry", file="funguns.qc",
         scenarios=[("Fire with no ammo", [("empty", 0)])],
         events=[
             dict(id="empty", label="Out of ammo", hint="a click while a fun gun is still recharging", file="funguns.qc",
                  ctx=r'sound7 \(self, CHAN_WEAPON, "([^"]+)", 0\.4', vol=0.4),
         ]),
]
