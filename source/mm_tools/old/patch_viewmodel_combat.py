"""Gives the Combat+ Mega Man its own held weapon (progs/v_megaman.md3) in the rocket launcher slot.
python -I patch_viewmodel_combat.py   (idempotent; run against qc_combat_decomp)"""
import re

ROOT = r"G:\Quake\Combat\BakersfieldQuake\source\qc_combat_decomp"

def rd(n):
    return open(ROOT + "\\" + n, encoding="utf-8", errors="surrogateescape", newline="").read()

def wr(n, s):
    open(ROOT + "\\" + n, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s)

def rep(s, old, new, count=1):
    assert s.count(old) >= 1, "missing: " + old[:60]
    return s.replace(old, new, count)

w = rd("weapons.qc")
if "MegaMan_ViewFrame" in w:
    print("weapons.qc already patched")
else:
    w = rep(w, '\tprecache_model("progs/megaman.md3");\n',
            '\tprecache_model("progs/megaman.md3");\n\tprecache_model("progs/v_megaman.md3");\n')
    w = rep(w, ".float\tmm_whistle;\n",
            ".float\tmm_whistle;\n.float\tmm_fire_t;\n.float\tmm_launch_t;\n.float\tmm_pending;\n")
    # held model instead of the rocket launcher
    w = rep(w, 'self.weaponmodel = "progs/v_rock2_right.mdl";', 'self.weaponmodel = "progs/v_megaman.md3";')
    w = rep(w, 'self.weaponmodel = "progs/v_rock2.mdl";', 'self.weaponmodel = "progs/v_megaman.md3";')
    # W_Attack: start the throw instead of firing instantly
    old = "\t\t\t\t\t\t\t\tW_FireRocket();\n\t\t\t\t\t\t\t\tself.attack_timer = 1;"
    assert old in w
    w = w.replace(old, "\t\t\t\t\t\t\t\tMegaMan_BeginThrow();\n\t\t\t\t\t\t\t\tself.attack_timer = 1;", 1)
    w = rep(w, "\t\t\t\t\t\t\t\t\tself.attack_finished = (time + 0.8);", "\t\t\t\t\t\t\t\t\tself.attack_finished = (time + 0.9);")
    # W_FireRocket: a thump instead of a rocket, throw from the hand
    w = rep(w, 'sound7(self, CHAN_WEAPON, "weapons/sgun1.wav", 1, ATTN_NORM, self.PLR_SNDSPD);\n\tsound7(self, CHAN_ITEM, "weapons/rocket2i.wav", 0.9, ATTN_NORM, self.PLR_SNDSPD);',
            'sound7(self, CHAN_WEAPON, "weapons/grenade.wav", 1, ATTN_NORM, self.PLR_SNDSPD);\n\tsound7(self, CHAN_ITEM, "weapons/ric1.wav", 0.7, ATTN_NORM, self.PLR_SNDSPD);')
    w = rep(w, "mm.velocity = aim(self, 1000) * 450 + '0 0 140';", "mm.velocity = aim(self, 1000) * 620 + '0 0 120';")
    w = rep(w, "traceline(self.origin + '0 0 12', (self.origin + '0 0 12') + v_forward * 40, TRUE, self);",
            "traceline(self.origin + '0 0 12', (self.origin + '0 0 8') + v_forward * 38 + v_right * 8, TRUE, self);")
    # new functions straight after W_FireRocket
    anchor = "void(vector p1, vector p2, entity from, float damage) LightningDamage ="
    assert anchor in w
    block = '''void() MegaMan_BeginThrow =
{
	self.mm_fire_t = time;
	self.mm_launch_t = time + 0.14;
	self.mm_pending = TRUE;
	sound7(self, CHAN_AUTO, "weapons/ax1.wav", 0.8, ATTN_NORM, self.PLR_SNDSPD * 1.2);
};

// drives the held Mega Man's animation (v_megaman.md3: 0-15 idle bob, 16-25 throw and re-arm)
void() MegaMan_ViewFrame =
{
	local float t;
	local float f;

	if (self.mm_pending && (time >= self.mm_launch_t))
	{
		self.mm_pending = FALSE;
		if ((time - self.mm_launch_t) < 0.3)
			W_FireRocket();
	}
	if (self.weapon != IT_ROCKET_LAUNCHER)
		return;
	t = time - self.mm_fire_t;
	if (self.mm_fire_t && (t < 0.85))
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
		f = floor(time * 10);
		f = f - 16 * floor(f / 16);
	}
	self.weaponframe = f;
};

'''
    w = w.replace(anchor, block + anchor, 1)
    # call it every frame
    w = rep(w, "void() W_WeaponFrame =\n{\n", "void() W_WeaponFrame =\n{\n\tMegaMan_ViewFrame();\n")
    wr("weapons.qc", w)
    print("weapons.qc patched")

p = rd("player.qc")
if p.count("IT_ROCKET_LAUNCHER)") >= 6 and "player_rocket1 = [ 107, player_rocket2 ]" in p and p.find("weapon != IT_ROCKET_LAUNCHER", p.find("player_rocket1 =")) != -1:
    print("player.qc already patched")
else:
    for n in range(1, 7):
        old = "\tself.weaponframe = %d;\n" % n
        # only inside player_rocketN
        pat = re.compile(r"(void\(\) player_rocket%d = \[ \d+, \w+ \]\n\{\n)\tself\.weaponframe = %d;\n" % (n, n))
        assert pat.search(p), n
        p = pat.sub(r"\1\tif (self.weapon != IT_ROCKET_LAUNCHER)\n\t\tself.weaponframe = %d;\n" % n, p, 1)
    wr("player.qc", p)
    print("player.qc patched")

