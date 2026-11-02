"""Gives the vanilla (BakersfieldMemes) Mega Man its own held weapon in the rocket launcher slot.
python -I patch_viewmodel_vanilla.py   (idempotent; run against qc_src\\quakec)"""
import re

ROOT = r"G:\Quake\Combat\qc_src\quakec"

def rd(n):
    s = open(ROOT + "\\" + n, encoding="utf-8", errors="surrogateescape", newline="").read()
    return s.replace("\r\n", "\n"), "\r\n" in s

def wr(n, s, crlf):
    if crlf:
        s = s.replace("\n", "\r\n")
    open(ROOT + "\\" + n, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s)

def rep(s, old, new):
    assert old in s, "missing: " + old[:70]
    return s.replace(old, new, 1)

w, crlf = rd("weapons.qc")
if "MegaMan_ViewFrame" in w:
    print("weapons.qc already patched")
else:
    w = rep(w, '\tprecache_model ("progs/megaman.md3");\t// Mega Man gun projectile\n',
            '\tprecache_model ("progs/megaman.md3");\t// Mega Man gun projectile\n\tprecache_model ("progs/v_megaman.md3");\t// the held Mega Man\n')
    w = rep(w, ".float\tmm_whistle;\t\t// when to whistle next\n",
            ".float\tmm_whistle;\t\t// when to whistle next\n.float\tmm_fire_t;\t\t// when the throw started\n.float\tmm_launch_t;\t// when Mega Man leaves the hand\n.float\tmm_pending;\t\t// throw in progress\n")
    w = rep(w, 'self.weaponmodel = "progs/v_rock2.mdl";', 'self.weaponmodel = "progs/v_megaman.md3";')
    w = rep(w, "\t\tplayer_rocket1();\n\t\tW_FireRocket();\n\t\tself.attack_finished = time + 0.8;",
            "\t\tplayer_rocket1();\n\t\tMegaMan_BeginThrow();\n\t\tself.attack_finished = time + 0.9;")
    w = rep(w, 'sound (self, CHAN_WEAPON, "weapons/sgun1.wav", 1, ATTN_NORM);\n\t//stuffcmd (self, "vibrate tactile/weapons/sgun1.bnvib");',
            'sound (self, CHAN_WEAPON, "weapons/grenade.wav", 1, ATTN_NORM);\n\tsound (self, CHAN_ITEM, "weapons/ric1.wav", 0.7, ATTN_NORM);')
    w = rep(w, "mm.velocity = aim (self, 1000) * 450 + '0 0 140';", "mm.velocity = aim (self, 1000) * 620 + '0 0 120';")
    w = rep(w, "traceline (self.origin + '0 0 12', self.origin + '0 0 12' + v_forward * 40, TRUE, self);",
            "traceline (self.origin + '0 0 12', self.origin + '0 0 8' + v_forward * 38 + v_right * 8, TRUE, self);")
    block = '''
void() MegaMan_BeginThrow =
{
	self.mm_fire_t = time;
	self.mm_launch_t = time + 0.14;
	self.mm_pending = TRUE;
	sound (self, CHAN_AUTO, "weapons/ax1.wav", 0.8, ATTN_NORM);
};

// drives the held Mega Man's animation (v_megaman.md3: 0-15 idle bob, 16-25 throw and re-arm)
void() MegaMan_ViewFrame =
{
	local float t;
	local float f;

	if (self.mm_pending && time >= self.mm_launch_t)
	{
		self.mm_pending = FALSE;
		if (time - self.mm_launch_t < 0.3)
			W_FireRocket ();
	}
	if (self.weapon != IT_ROCKET_LAUNCHER)
		return;
	t = time - self.mm_fire_t;
	if (self.mm_fire_t && t < 0.85)
	{
		if (t < 0.07)
			f = 16;
		else if (t < 0.14)
			f = 17;
		else if (t < 0.19)
			f = 18;
		else if (t < 0.25)
			f = 19;
		else if (t < 0.35)
			f = 20;
		else if (t < 0.5)
			f = 21;
		else if (t < 0.6)
			f = 22;
		else if (t < 0.7)
			f = 23;
		else if (t < 0.78)
			f = 24;
		else
			f = 25;
	}
	else
	{
		f = floor (time * 10);
		f = f - 16 * floor (f / 16);
	}
	self.weaponframe = f;
};
'''
    anchor = "\n/*\n===============================================================================\n"
    i = w.index("void() W_FireRocket =")
    j = w.index(anchor, i)
    w = w[:j] + block + w[j:]
    w = rep(w, "void() W_WeaponFrame =\n{\n", "void() W_WeaponFrame =\n{\n\tMegaMan_ViewFrame ();\n\n")
    wr("weapons.qc", w, crlf)
    print("weapons.qc patched")

p, crlf = rd("player.qc")
if "weapon != IT_ROCKET_LAUNCHER" in p:
    print("player.qc already patched")
else:
    for n in range(1, 7):
        pat = re.compile(r"(void\(\) player_rocket%d\s*=\[\$rockatt%d, \w+\s*\] \{)(\n?)(\s*)self\.weaponframe\s*=\s*%d;" % (n, n, n))
        m = pat.search(p)
        assert m, n
        p = p[:m.start()] + m.group(1) + m.group(2) + m.group(3) + "if (self.weapon != IT_ROCKET_LAUNCHER) self.weaponframe=%d;" % n + p[m.end():]
    wr("player.qc", p, crlf)
    print("player.qc patched")

it, crlf = rd("items.qc")
if "weapon_rocketlauncher" in it and "g_rock2" in it:
    m = re.search(r'(void\(\) weapon_rocketlauncher =\n\{\n)(.*?)(\n\};)', it, re.S)
    body = m.group(2)
    if "megaman" not in body:
        body = body.replace('"progs/g_rock2.mdl"', '"progs/megaman.md3"')
        body = body.replace("setmodel", "self.scale = 1.3;\n\tsetmodel", 1) if False else body
        it = it[:m.start(2)] + body + it[m.end(2):]
        wr("items.qc", it, crlf)
        print("items.qc patched")
