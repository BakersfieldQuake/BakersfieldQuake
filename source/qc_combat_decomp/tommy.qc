#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE THOMPSON (see tommy_defs.qc for tunables and frame map)

FunGun_Attack calls Tommy_Press every frame fire is held (exempt from bm_fg_lock).
FunGun_ViewFrame calls Tommy_Anim for the view model's frame, reload/draw foley sounds, and 3rd-person SMG attachment.
================
*/

string	tom_snd_fire;
string	tom_snd_deploy;
string	tom_snd_clipout;
string	tom_snd_clipin;
string	tom_snd_dry;
float	tom_pmodel_ok;
float	tom_fx_hole;
float	tom_fx_spark;

string(string dod, string fallback) Tommy_PickSound =
{
	local float fh;

	fh = fopen (strcat ("sound/", dod), 0);
	if (fh < 0)
		return fallback;
	fclose (fh);
	precache_sound (dod);
	return dod;
};

void() Tommy_Precache =
{
	local float fh;

	tommy_ok = 0;
	tom_pmodel_ok = 0;
	fh = fopen ("progs/v_tommy.md3", 0);
	if (fh < 0)
		return;
	fclose (fh);
	precache_model ("progs/v_tommy.md3");
	fh = fopen ("progs/p_tommy.md3", 0);
	if (fh >= 0)
	{
		fclose (fh);
		precache_model ("progs/p_tommy.md3");
		tom_pmodel_ok = 1;
	}
	precache_model ("progs/muzzleflash1.spr");
	precache_model ("progs/nailcasing.mdl");
	tom_snd_fire = Tommy_PickSound ("dod/thompson_shoot.wav", "weapons/sgun1.wav");
	tom_snd_deploy = Tommy_PickSound ("dod/tommy_draw_slideback.wav", "weapons/pkup.wav");
	tom_snd_clipout = Tommy_PickSound ("dod/tommy_reload_clipout.wav", "weapons/lock4.wav");
	tom_snd_clipin = Tommy_PickSound ("dod/tommy_reload_clipin.wav", "weapons/pkup.wav");
	tom_snd_dry = Tommy_PickSound ("dod/weaponempty.wav", "weapons/lock4.wav");
	tom_fx_hole = particleeffectnum ("m4_hole");
	tom_fx_spark = particleeffectnum ("m4_spark");
	tommy_ok = 1;
};

string() Tommy_VModel =
{
	if (!tommy_ok)
		return "";
	return "progs/v_tommy.md3";
};

float(entity p) Tommy_ShowsReload =
{
	return (tommy_ok && p.weapon == IT_FUNGUN && p.fg_sel == FG_TOMMY && p.bm_rl_slot == BM_FG8);
};

void() Tommy_VwepThink =
{
	local entity p;

	p = self.owner;
	if (!p || p.health <= 0 || p.weapon != IT_FUNGUN || p.fg_sel != FG_TOMMY || (p.items & IT_INVISIBILITY))
	{
		if (p && p.tom_vwep == self)
			p.tom_vwep = world;
		remove (self);
		return;
	}
	self.nextthink = time + 0.05;
};

void() Tommy_UpdateVwep =
{
	local entity e;
	local float show;

	if (!tom_pmodel_ok)
		return;
	show = (self.weapon == IT_FUNGUN && self.fg_sel == FG_TOMMY && self.health > 0 && !(self.items & IT_INVISIBILITY) && self.model == "progs/player_torso.mdl");
	if (!show)
	{
		if (self.tom_vwep)
		{
			remove (self.tom_vwep);
			self.tom_vwep = world;
		}
		return;
	}
	e = self.tom_vwep;
	if (!e)
	{
		e = spawn ();
		e.classname = "tom_vwep";
		e.owner = self;
		e.exteriormodeltoclient = self;
		e.scale = 1.0;
		setattachment (e, self, "");
		e.origin = '12 -9 9';
		e.angles = '0 0 0';
		e.think = Tommy_VwepThink;
		e.nextthink = time + 0.05;
		self.tom_vwep = e;
		setmodel (e, "progs/p_tommy.md3");
	}
};

void() Tommy_MuzzleAndBrass =
{
	local entity fl, c;
	local vector ejectpos;

	if (self.waterlevel < 3)
	{
		fl = spawn ();
		fl.movetype = 0;
		fl.solid = 0;
		fl.viewmodelforclient = self;
		fl.owner = self;
		fl.classname = "flash";
		fl.effects = EF_ADDITIVE;
		setmodel (fl, "progs/muzzleflash1.spr");
		fl.scale = 0.34 + random () * 0.09;
		fl.alpha = 0.85;
		setsize (fl, VEC_ORIGIN, VEC_ORIGIN);
		// Aligned with baked v_tommy.md3 Cutts compensator tip [46.17, -9.44, -5.51]
		setorigin (fl, '46.6 -9.4 -5.5');
		fl.think = SUB_Remove;
		fl.nextthink = time + 0.045;

		sendParticle ("nailgun_muzzleflash", (self.origin + self.view_ofs) + v_forward * 24 + v_right * 10 - v_up * 5, self.velocity * 20, 1);
	}

	if (autocvar_shellcasing)
	{
		c = spawn ();
		ejectpos = (self.origin + self.view_ofs) + v_forward * 14 + v_right * 10 - v_up * 6;
		c.angles = self.v_angle;
		c.angles_x = 0 - c.angles_x;
		setorigin (c, ejectpos);
		setmodel (c, "progs/nailcasing.mdl");
		c.scale = 0.62;
		setsize (c, VEC_ORIGIN, VEC_ORIGIN);
		c.alpha = 1;
		c.movetype = MOVETYPE_BOUNCE;
		c.solid = SOLID_TRIGGER;
		c.touch = nailcasing_touch;
		c.takedamage = 0;
		c.velocity = (self.velocity * 0.75) + v_right * (80 + random () * 28) + v_up * (75 + random () * 25) + v_forward * (20 + crandom () * 12);
		if (coop || deathmatch)
		{
			c.casetype = CASING_NAIL;
			c.SendEntity = casing_sendtocsqc;
			c.SendFlags = c.SendFlags | 1;
			c.think = SUB_Remove;
			c.nextthink = time + 0.01;
		}
		else
		{
			c.avelocity = '420 260 440' + randomvec () * 60;
			c.nextthink = time;
			c.think = casing_placement;
			c.cansplash = TRUE;
			c.gravity = 1.3;
		}
	}
};

void(vector dir) Tommy_WallImpact =
{
	local float surfacenum, r;
	local string tex;

	if (pointcontents (trace_endpos) == CONTENT_SKY || pointcontents (trace_endpos - dir * 2) == CONTENT_SKY)
		return;
	if (trace_ent == world)
	{
		surfacenum = getsurfacenearpoint (world, trace_endpos);
		if (surfacenum >= 0)
		{
			tex = getsurfacetexture (world, surfacenum);
			if (tex == "black" || substring (tex, 0, 3) == "sky")
				return;
		}
	}

	if (tom_fx_hole >= 0)
		pointparticles (tom_fx_hole, trace_endpos, VEC_ORIGIN, 1);
	else
		sendParticle ("TE_GUNSHOT", trace_endpos - dir * 1, VEC_ORIGIN, 1);

	if (tom_fx_spark >= 0)
		pointparticles (tom_fx_spark, trace_endpos + trace_plane_normal * 1.5, trace_plane_normal * 95, 1);
	else
		sendParticle ("TE_SPIKE", trace_endpos + trace_plane_normal * 1.5, VEC_ORIGIN, 1);

	if (random () < 0.25)
	{
		r = random ();
		if (r < 0.34)
			pointsound (trace_endpos, "weapons/ric1.wav", 0.40, ATTN_NORM);
		else if (r < 0.67)
			pointsound (trace_endpos, "weapons/ric2.wav", 0.40, ATTN_NORM);
		else
			pointsound (trace_endpos, "weapons/ric3.wav", 0.40, ATTN_NORM);
	}
};

void() Tommy_Press =
{
	local float a, spr, spd, dist, dmg;
	local vector dir, src;

	if (self.bm_rl_slot == BM_FG8 || time < self.tom_draw_t + TOM_DRAW_LOCK)
	{
		self.attack_finished = time + 0.05;
		return;
	}
	a = FunGun_Ammo (self, FG_TOMMY);
	if (a < 1)
	{
		FG_Snd (self, CHAN_WEAPON, tom_snd_dry, 0.85, 1);
		self.attack_finished = time + 0.3;
		return;
	}

	// recovery only once the trigger has been let go (like the M4): decaying on every full-auto shot took 0.0135 off per
	// 0.0045 added, so the bloom never built at all
	if (self.tom_heat_t > 0)
	{
		if (time - self.tom_heat_t > TOM_REFIRE * 1.5)
			self.tom_heat = max (0, self.tom_heat - (time - self.tom_heat_t - TOM_REFIRE) * TOM_HEAT_DECAY);
	}
	else
		self.tom_heat = 0;

	spd = min (320, vlen (self.velocity));
	spr = TOM_SPREAD_STAND + (spd / 320) * TOM_SPREAD_MOVE + self.tom_heat;
	if (!(self.flags & FL_ONGROUND))
		spr = spr + TOM_SPREAD_AIR;

	self.tom_heat = min (TOM_HEAT_MAX, self.tom_heat + TOM_HEAT_SHOT);
	self.tom_heat_t = time;

	FunGun_SetAmmo (self, FG_TOMMY, a - 1);
	self.fg_fire_t = time;
	self.bm_lastshot = time;
	self.attack_finished = time + TOM_REFIRE;
	self.tom_alt = 1 - self.tom_alt;
	self.tom_shootanim = 1 + self.tom_alt;
	self.tom_shoot_t = time;

	player_mm1 ();
	self.effects = self.effects | EF_MUZZLEFLASH;
	FG_Snd (self, CHAN_WEAPON, tom_snd_fire, 0.92, 0.98 + random () * 0.04);
	self.punchangle_x = 0 - (TOM_RECOIL + self.tom_heat * 18);
	self.punchangle_y = crandom () * (0.45 + self.tom_heat * 10);

	makevectors (self.v_angle);
	Tommy_MuzzleAndBrass ();

	dir = normalize (v_forward + (crandom () * spr) * v_right + (crandom () * spr) * v_up);
	src = self.origin + self.view_ofs + (v_forward * 10);
	ClearMultiDamage ();
	traceline (src, src + dir * TOM_RANGE, FALSE, self);
	if (trace_fraction != 1)
	{
		if (trace_ent.takedamage || trace_ent.inflamed == 1)
		{
			dist = trace_fraction * TOM_RANGE;
			dmg = TOM_DAMAGE;
			if (dist > 1200)
				dmg = max (TOM_DAMAGE * 0.50, TOM_DAMAGE * (1 - 0.50 * ((dist - 1200) / 2000)));
			TraceAttack (dmg, dir);
		}
		else
			Tommy_WallImpact (dir);
	}
	W_BulletSplash (dir);
	fg_inflicting = FG_TOMMY;
	ApplyMultiDamage ();
	fg_inflicting = 0;
};

float() Tommy_Anim =
{
	local float f, fr, t;

	if (time - self.tom_vf_t > 0.25)
	{
		self.tom_draw_t = time;
		self.tom_draw_snd = 0;
		self.tom_shootanim = 0;
		self.tom_heat = 0;
	}
	self.tom_vf_t = time;
	Tommy_UpdateVwep ();

	if (self.bm_rl_slot == BM_FG8)
	{
		self.tom_shootanim = 0;
		fr = (time - self.bm_rl_start) / max (0.05, self.bm_rl_end - self.bm_rl_start);
		if (fr > 1)
			fr = 1;
		if (self.tom_rl_stage < 1 && fr >= TOM_EVT_CLIPOUT / TOM_RELOAD_TIME)
		{
			self.tom_rl_stage = 1;
			FG_Snd (self, CHAN_ITEM, tom_snd_clipout, 0.9, 1);
		}
		if (self.tom_rl_stage < 2 && fr >= TOM_EVT_CLIPIN / TOM_RELOAD_TIME)
		{
			self.tom_rl_stage = 2;
			FG_Snd (self, CHAN_ITEM, tom_snd_clipin, 0.9, 1);
		}
		return TOM_RELOAD_FIRST + min (TOM_RELOAD_COUNT - 1, floor (fr * TOM_RELOAD_COUNT));
	}
	self.tom_rl_stage = 0;

	t = time - self.tom_draw_t;
	if (!self.tom_shootanim && t < TOM_DRAW_COUNT / TOM_DRAW_FPS)
	{
		if (!self.tom_draw_snd)
		{
			self.tom_draw_snd = 1;
			FG_Snd (self, CHAN_ITEM, tom_snd_deploy, 0.88, 1);
		}
		return TOM_DRAW_FIRST + min (TOM_DRAW_COUNT - 1, floor (t * TOM_DRAW_FPS));
	}

	if (self.tom_shootanim)
	{
		t = time - self.tom_shoot_t;
		if (self.tom_shootanim == 1)
		{
			f = floor (t * TOM_SHOOT1_FPS);
			if (f < TOM_SHOOT1_COUNT)
				return TOM_SHOOT1_FIRST + f;
		}
		else
		{
			f = floor (t * TOM_SHOOT2_FPS);
			if (f < TOM_SHOOT2_COUNT)
				return TOM_SHOOT2_FIRST + f;
		}
		self.tom_shootanim = 0;
	}

	if (FunGun_Ammo (self, FG_TOMMY) < 1)
		return TOM_EMPTY_FIRST;

	f = floor (time * TOM_IDLE_FPS);
	f = f - TOM_IDLE_COUNT * floor (f / TOM_IDLE_COUNT);
	return TOM_IDLE_FIRST + f;
};
