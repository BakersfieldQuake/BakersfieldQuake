"""One-off: turns qc_src/quakec/megaman.qc (vanilla-only) into the shared sources
BakersfieldQuake/source/mm_tools/megaman_defs.qc + BakersfieldQuake/source/mm_tools/megaman.qc, which build for both vanilla and
Combat+ (#define COMBATPLUS). python -I split_megaman.py"""
import re

SRC = r"G:\Quake\Combat\qc_src\quakec\megaman.qc"
OUT = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\mm_tools\\"

s = open(SRC, encoding="utf-8").read()


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:70])
    s = s.replace(old, new)


cut = s.index("void() MegaMan_Precache =")
defs, body = s[:cut], s[cut:]

# ---------------------------------------------------------------- defs
defs = defs.replace('''void(entity e, float chan, string samp, float vol, float atten, float speed, float flags) sound7 = #8;
void(entity e, entity tagentity, string tagname) setattachment = #443;
float(float f) sin = #60;
void(vector v1, vector mins, vector maxs, vector v2, float nomonsters, entity forent) tracebox = #90;
.float	scale;
.entity	exteriormodeltoclient;
''', '''#ifndef COMBATPLUS
// Darkplaces extensions the id code doesn't declare (Combat+ already has them)
void(entity e, float chan, string samp, float vol, float atten, float speed, float flags) sound7 = #8;
void(entity e, entity tagentity, string tagname) setattachment = #443;
float(float f) sin = #60;
void(vector v1, vector mins, vector maxs, vector v2, float nomonsters, entity forent) tracebox = #90;
.float	scale;
.entity	exteriormodeltoclient;
#endif
''')
defs = defs.replace('''void() BecomeExplosion;
void() W_SetCurrentAmmo;
void() player_mm1;
''', '''float	mm_inflicting;		// TRUE while a Mega Man is dealing damage (for the obituary)

void() BecomeExplosion;
void() W_SetCurrentAmmo;
void() player_mm1;
void() MegaMan_Precache;
void() MegaMan_Attack;
void() MegaMan_Select;
void(entity p) MegaMan_Give;
void() MegaMan_ViewFrame;
''')
defs = defs.replace("Its own weapon (IT_MEGAMAN, impulse MM_IMPULSE); every player carries it.",
                    "Its own weapon (IT_MEGAMAN, impulse MM_IMPULSE); every player carries it.\nShared by the vanilla (BakersfieldMemes) and Combat+ (CombatMegaMan) builds;\nCombat+ compiles it with COMBATPLUS defined.")
defs += "\n"

# ---------------------------------------------------------------- body
s = body
rep('''	precache_sound ("weapons/megahorn.wav");
};''', '''	precache_sound ("weapons/megahorn.wav");
	precache_sound ("weapons/pkup.wav");
};''')

rep('''float(float y) MM_NormYaw =
{
	return y - 360 * floor (y / 360);
};
''', '''float(float y) MM_NormYaw =
{
	return y - 360 * floor (y / 360);
};

// speed in percent; Combat+ scales it with its slow-motion
void(entity e, float chan, string samp, float vol, float speed) MM_Sound =
{
#ifdef COMBATPLUS
	sound7 (e, chan, samp, vol, ATTN_NORM, SNDSPD * speed / 100);
#else
	sound7 (e, chan, samp, vol, ATTN_NORM, speed, 0);
#endif
};
''')

a = s.index("void(entity hit) MegaMan_Explode =")
b = s.index("void() MegaMan_SpinWheels =")
s = s[:a] + '''void(entity hit) MegaMan_Explode =
{
	dprint ("Mega Man exploded at ", vtos (self.origin), "\\n");

	// hit != world: it already took the direct damage, skip it in the splash
	mm_inflicting = TRUE;
#ifdef COMBATPLUS
	if (pointcontents (self.origin) == CONTENT_SLIME)
		sendParticle ("slimesplash", self.origin, VEC_ORIGIN, 1, 0);
	else if (autocvar_effects_classic_explosion == 1)
		sendParticle ("rocket_explo_classic", self.origin, VEC_ORIGIN, 1, 0);
	else
		sendParticle ("rocket_explosion", self.origin, VEC_ORIGIN, 1, 0);
	T_RadiusDamage (self, self.owner, autocvar_player_rocket_radius, hit);
	mm_inflicting = FALSE;
	if (pointcontents (self.origin) == CONTENT_WATER || pointcontents (self.origin) == CONTENT_SLIME || pointcontents (self.origin) == CONTENT_LAVA)
		MM_Sound (self, CHAN_WEAPON, "weapons/xpld_wat.wav", 1, 90);
	else
	{
		MM_Sound (self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, 100);
		sound7 (self, CHAN_AUTO, "weapons/explodedist.wav", 0.3, ATTN_NONE, SNDSPD);
	}
#else
	T_RadiusDamage (self, self.owner, 120, hit);
	mm_inflicting = FALSE;

	MM_Sound (self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, 100);

	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, self.origin_x);
	WriteCoord (MSG_BROADCAST, self.origin_y);
	WriteCoord (MSG_BROADCAST, self.origin_z);
#endif

	BecomeExplosion ();
};

''' + s[b:]

rep('''		if (e != self.owner && e.health > 0)
		{
			if (e.classname == "player")
				ok = TRUE;
			else if (!deathmatch && (e.flags & FL_MONSTER))
				ok = TRUE;
		}
''', '''		if (e != self.owner && e.health > 0)
		{
			if (deathmatch)
				ok = (e.classname == "player");
			else
				ok = (e.flags & FL_MONSTER);	// single player / coop: monsters, never teammates
		}
''')
rep("Nearest enemy within sight and range. In deathmatch that means other players\n(never the owner, never a teammate under teamplay). Outside deathmatch it will\nalso chase monsters, so the gun is still fun in single player and coop.",
    "Nearest enemy within sight and range. In deathmatch that means other players\n(never the owner, never a teammate under teamplay). Outside deathmatch it\nchases monsters, so the gun is still fun in single player and coop.")

# plain sound calls -> MM_Sound
s, n1 = re.subn(r'sound \((\w+), (CHAN_\w+), ("[^"]+"), ([\d.]+), ATTN_NORM\);', r'MM_Sound (\1, \2, \3, \4, 100);', s)
s, n2 = re.subn(r'sound7 \(self, (CHAN_\w+), ("[^"]+"), ([\d.]+), ATTN_NORM, (\w+), 0\);', r'MM_Sound (self, \1, \2, \3, \4);', s)
print("sound calls converted:", n1, n2)

rep('''		T_Damage (other, self, self.owner, damg);
		MegaMan_Explode (other);''', '''		mm_inflicting = TRUE;
		T_Damage (other, self, self.owner, damg);
		mm_inflicting = FALSE;
		MegaMan_Explode (other);''')

rep('''	local entity p;

	p = self.owner;''', '''	local entity p;
	local float s;

	p = self.owner;''')
rep("	self.origin_z = sin (time * 6.3) * 1.2;", "	s = sin (time * 6.3);\n	self.origin_z = s * 1.2;")

rep('''// gives a player the gun (spawn, impulse 9)''', '''// impulse MM_IMPULSE
void() MegaMan_Select =
{
	self.impulse = 0;
	if (!(self.items & IT_MEGAMAN))
	{
		sprint (self, "no weapon.\\n");
		return;
	}
#ifdef COMBATPLUS
	if (self.has_fired == 1)
		return;
	self.idletimer = 1;		// weapon raise animation
	self.switchtimer = -5;
#endif
	self.weapon = IT_MEGAMAN;
	W_SetCurrentAmmo ();
};

// gives a player the gun (spawn, impulse 9)''')

open(OUT + "megaman_defs.qc", "w", encoding="utf-8").write(defs)
open(OUT + "megaman.qc", "w", encoding="utf-8").write(s)
print("wrote megaman_defs.qc", defs.count("\n"), "lines; megaman.qc", s.count("\n"), "lines")
