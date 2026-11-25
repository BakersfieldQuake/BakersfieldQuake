#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE M1 GARAND (see garand_defs.qc for tunables and frame map)

FunGun_Attack calls Garand_Press when fire is pressed (exempt from bm_fg_lock; semi-auto gated by .gar_ready).
FunGun_ViewFrame updates .gar_ready when +attack is released and calls Garand_Anim for viewmodel frames,
8th-round clip ejection, reload/draw foley sounds, and 3rd-person rifle attachment.
================
*/

string	gar_snd_fire;
string	gar_snd_clipin;
string	gar_snd_ping;
string	gar_snd_deploy;
string	gar_snd_dry;
float	gar_pmodel_ok;
float	gar_fx_hole;
float	gar_fx_spark;

string(string dod, string fallback) Garand_PickSound =
{
	local float fh;

	fh = fopen (strcat ("sound/", dod), 0);
	if (fh < 0)
		return fallback;
	fclose (fh);
	precache_sound (dod);
	return dod;
};

void() Garand_Precache =
{
	local float fh;

	garand_ok = 0;
	gar_pmodel_ok = 0;
	fh = fopen ("progs/v_garand.md3", 0);
	if (fh < 0)
		return;
	fclose (fh);
	precache_model ("progs/v_garand.md3");
	fh = fopen ("progs/p_garand.md3", 0);
	if (fh >= 0)
	{
		fclose (fh);
		precache_model ("progs/p_garand.md3");
		gar_pmodel_ok = 1;
	}
	precache_model ("progs/muzzleflash1.spr");
	precache_model ("progs/nailcasing.mdl");
	gar_snd_fire = Garand_PickSound ("dod/garand_shoot.wav", "weapons/sgun1.wav");
	gar_snd_clipin = Garand_PickSound ("dod/garand_reload_clipin.wav", "weapons/pkup.wav");
	gar_snd_ping = Garand_PickSound ("dod/garand_reload_clipding.wav", "weapons/ric1.wav");
	gar_snd_deploy = Garand_PickSound ("dod/rifleselect.wav", "weapons/pkup.wav");
	gar_snd_dry = Garand_PickSound ("dod/weaponempty.wav", "weapons/lock4.wav");
	gar_fx_hole = particleeffectnum ("m4_hole");
	gar_fx_spark = particleeffectnum ("m4_spark");
	garand_ok = 1;
};

string() Garand_VModel =
{
	if (!garand_ok)
		return "";
	return "progs/v_garand.md3";
};

float(entity p) Garand_ShowsReload =
{
	return (garand_ok && p.weapon == IT_FUNGUN && p.fg_sel == FG_GARAND && p.bm_rl_slot == BM_FG9);
};

void() Garand_VwepThink =
{
	local entity p;

	p = self.owner;
	if (!p || p.health <= 0 || p.weapon != IT_FUNGUN || p.fg_sel != FG_GARAND || (p.items & IT_INVISIBILITY) || Veh_Driving (p) || p.veh_ride != world || JohnBird_Flying (p) || RocketRider_Flying (p) || MMTank_Driving (p) || EricCannon_Active (p) || FD_Flying (p))
	{
		if (p && p.gar_vwep == self)
			p.gar_vwep = world;
		remove (self);
		return;
	}
	self.nextthink = time + 0.05;
};

void() Garand_UpdateVwep =
{
	local entity e;
	local float show;

	if (!gar_pmodel_ok)
		return;
	show = (self.weapon == IT_FUNGUN && self.fg_sel == FG_GARAND && self.health > 0 && !(self.items & IT_INVISIBILITY) && self.model == "progs/player_torso.mdl" && !Veh_Driving (self) && self.veh_ride == world && !JohnBird_Flying (self) && !RocketRider_Flying (self) && !MMTank_Driving (self) && !EricCannon_Active (self) && !FD_Flying (self));
	if (!show)
	{
		if (self.gar_vwep)
		{
			remove (self.gar_vwep);
			self.gar_vwep = world;
		}
		return;
	}
	e = self.gar_vwep;
	if (!e)
	{
		e = spawn ();
		e.classname = "gar_vwep";
		e.owner = self;
		e.exteriormodeltoclient = self;
		e.scale = 1.0;
		setattachment (e, self, "");
		e.origin = '12 -9 9';
		e.angles = '0 0 0';
		e.think = Garand_VwepThink;
		e.nextthink = time + 0.05;
		self.gar_vwep = e;
		setmodel (e, "progs/p_garand.md3");
	}
};

void() Garand_MuzzleAndBrass =
{
	local entity fl, c;
	local vector ejectpos;

	if (self.waterlevel < 3)
	{
		if (self.ishuman == 1)
		{
			fl = spawn ();
			fl.movetype = 0;
			fl.solid = 0;
			fl.viewmodelforclient = self;
			fl.owner = self;
			fl.classname = "flash";
			fl.effects = EF_ADDITIVE;
			setmodel (fl, "progs/muzzleflash1.spr");
			fl.scale = 0.62 + random () * 0.14;
			fl.alpha = 0.90;
			setsize (fl, VEC_ORIGIN, VEC_ORIGIN);
			// Aligned with baked v_garand.md3 barrel tip [84.05, -7.11, -3.79]
			setorigin (fl, '84.8 -7.1 -3.8');
			fl.think = SUB_Remove;
			fl.nextthink = time + 0.05;
		}

		sendParticle ("nailgun_muzzleflash", (self.origin + self.view_ofs) + v_forward * 26 + v_right * 9 - v_up * 4, self.velocity * 20, 1, 0);
	}

	if (autocvar_shellcasing)
	{
		c = spawn ();
		ejectpos = (self.origin + self.view_ofs) + v_forward * 15 + v_right * 10 - v_up * 5;
		c.angles = self.v_angle;
		c.angles_x = 0 - c.angles_x;
		setorigin (c, ejectpos);
		setmodel (c, "progs/nailcasing.mdl");
		c.scale = 0.78;
		setsize (c, VEC_ORIGIN, VEC_ORIGIN);
		c.alpha = 1;
		c.movetype = MOVETYPE_BOUNCE;
		c.solid = SOLID_TRIGGER;
		c.touch = nailcasing_touch;
		c.takedamage = 0;
		c.velocity = (self.velocity * 0.75) + v_right * (95 + random () * 30) + v_up * (95 + random () * 30) + v_forward * (30 + crandom () * 14);
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
			c.avelocity = '460 300 480' + randomvec () * 70;
			c.nextthink = time;
			c.think = casing_placement;
			c.cansplash = TRUE;
			c.gravity = 1.3;
		}
	}
};

void(vector dir) Garand_WallImpact =
{
	local float r;

	if (pointcontents (trace_endpos) == CONTENT_SKY || pointcontents (trace_endpos + dir * 2) == CONTENT_SKY || pointcontents (trace_endpos - dir * 2) == CONTENT_SKY)
		return;

	if (gar_fx_hole >= 0)
		pointparticles (gar_fx_hole, trace_endpos, VEC_ORIGIN, 1);
	else
		sendParticle ("TE_GUNSHOT", trace_endpos - dir * 1, VEC_ORIGIN, 1, 0);

	if (gar_fx_spark >= 0)
		pointparticles (gar_fx_spark, trace_endpos + trace_plane_normal * 1.5, trace_plane_normal * 110, 1);
	else
		sendParticle ("TE_SPIKE", trace_endpos + trace_plane_normal * 1.5, VEC_ORIGIN, 1, 0);

	if (random () < 0.35)
	{
		r = random ();
		if (r < 0.34)
			pointsound (trace_endpos, "weapons/ric1.wav", 0.48, ATTN_NORM);
		else if (r < 0.67)
			pointsound (trace_endpos, "weapons/ric2.wav", 0.48, ATTN_NORM);
		else
			pointsound (trace_endpos, "weapons/ric3.wav", 0.48, ATTN_NORM);
	}
};

void() Garand_Press =
{
	local float a, spr, spd, dist, dmg;
	local vector dir, src;

	if (!self.gar_ready)
		return;		// semi-auto: release +attack between shots
	if (self.bm_rl_slot == BM_FG9 || (self.gar_empty_t > 0 && time < self.gar_empty_t + GAR_SHOOT_EMPTY_TIME) || time < self.gar_draw_t + GAR_DRAW_LOCK)
	{
		self.attack_finished = time + 0.05;
		return;
	}
	a = FunGun_Ammo (self, FG_GARAND);
	if (a < 1)
	{
		self.gar_ready = 0;
		FG_Snd (self, CHAN_WEAPON, gar_snd_dry, 0.85, 1);
		self.attack_finished = time + 0.25;
		return;
	}

	self.gar_ready = 0;
	a = a - 1;
	FunGun_SetAmmo (self, FG_GARAND, a);
	self.fg_fire_t = time;
	self.bm_lastshot = time;
	self.attack_finished = time + GAR_REFIRE;
	self.gar_shoot_t = time;

	player_mm1 ();
	self.effects = self.effects | EF_MUZZLEFLASH;
	FG_Snd (self, CHAN_WEAPON, gar_snd_fire, 0.96, 1);
	self.punchangle_x = 0 - GAR_RECOIL;
	self.punchangle_y = crandom () * 0.45;

	if (a < 1)
	{
		// 8th round: en-bloc clip visibly flies out + iconic metallic PING!
		self.gar_shootanim = 3;
		self.gar_empty_t = time;
		FG_Snd (self, CHAN_AUTO, gar_snd_ping, 1.0, 1);
	}
	else
	{
		self.gar_alt = 1 - self.gar_alt;
		self.gar_shootanim = 1 + self.gar_alt;
	}

	makevectors (self.v_angle);
	Garand_MuzzleAndBrass ();

	spd = min (320, vlen (self.velocity));
	spr = GAR_SPREAD_STAND + (spd / 320) * GAR_SPREAD_MOVE;
	if (!(self.flags & FL_ONGROUND))
		spr = spr + GAR_SPREAD_AIR;

	dir = normalize (v_forward + (crandom () * spr) * v_right + (crandom () * spr) * v_up);
	src = self.origin + self.view_ofs;
	traceline (src, src + (v_forward * 10), TRUE, self);
	src = (trace_fraction < 1) ? (src + (v_forward * max (0, (trace_fraction * 10) - 1))) : (src + (v_forward * 10));
	ClearMultiDamage ();
	traceline (src, src + dir * GAR_RANGE, FALSE, self);
	dist = trace_fraction * GAR_RANGE;
	dmg = GAR_DAMAGE;
	if (dist > 1400)
		dmg = max (GAR_DAMAGE * 0.55, GAR_DAMAGE * (1 - 0.45 * ((dist - 1400) / 2100)));
	if (!PC_TraceIntercept (self, src, trace_endpos, dmg) && trace_fraction != 1)
	{
		if (trace_ent.takedamage || trace_ent.inflamed == 1)
			TraceAttack (dmg, dir);
		else
			Garand_WallImpact (dir);
	}
	W_BulletSplash (dir);
	fg_inflicting = FG_GARAND;
	ApplyMultiDamage ();
	fg_inflicting = 0;
};

float() Garand_Anim =
{
	local float f, fr, t;

	if (time - self.gar_vf_t > 0.25)
	{
		self.gar_draw_t = time;
		self.gar_draw_empty = (FunGun_Ammo (self, FG_GARAND) < 1);
		self.gar_draw_snd = 0;
		self.gar_shootanim = 0;
		self.gar_empty_t = 0;
	}
	self.gar_vf_t = time;
	Garand_UpdateVwep ();

	if (self.bm_rl_slot == BM_FG9)
	{
		self.gar_shootanim = 0;
		self.gar_empty_t = 0;
		fr = (time - self.bm_rl_start) / max (0.05, self.bm_rl_end - self.bm_rl_start);
		if (fr > 1)
			fr = 1;
		if (self.gar_rl_stage < 1 && fr >= GAR_EVT_CLIPIN / GAR_RELOAD_TIME)
		{
			self.gar_rl_stage = 1;
			FG_Snd (self, CHAN_ITEM, gar_snd_clipin, 0.92, 1);
		}
		return GAR_RELOAD_FIRST + min (GAR_RELOAD_COUNT - 1, floor (fr * GAR_RELOAD_COUNT));
	}
	self.gar_rl_stage = 0;

	t = time - self.gar_draw_t;
	if (!self.gar_shootanim && t < GAR_DRAW_COUNT / GAR_DRAW_FPS)
	{
		if (!self.gar_draw_snd)
		{
			self.gar_draw_snd = 1;
			FG_Snd (self, CHAN_ITEM, gar_snd_deploy, 0.86, 1);
		}
		if (self.gar_draw_empty)
			return GAR_DRAWE_FIRST + min (GAR_DRAWE_COUNT - 1, floor (t * GAR_DRAWE_FPS));
		return GAR_DRAW_FIRST + min (GAR_DRAW_COUNT - 1, floor (t * GAR_DRAW_FPS));
	}

	if (self.gar_shootanim)
	{
		t = time - self.gar_shoot_t;
		if (self.gar_shootanim == 1)
		{
			f = floor (t * GAR_SHOOT1_FPS);
			if (f < GAR_SHOOT1_COUNT)
				return GAR_SHOOT1_FIRST + f;
		}
		else if (self.gar_shootanim == 2)
		{
			f = floor (t * GAR_SHOOT2_FPS);
			if (f < GAR_SHOOT2_COUNT)
				return GAR_SHOOT2_FIRST + f;
		}
		else
		{
			f = floor (t * GAR_SHOOTE_FPS);
			if (f < GAR_SHOOTE_COUNT)
				return GAR_SHOOTE_FIRST + f;
		}
		self.gar_shootanim = 0;
	}

	if (FunGun_Ammo (self, FG_GARAND) < 1)
		return GAR_EMPTY_FIRST;

	f = floor (time * GAR_IDLE_FPS);
	f = f - GAR_IDLE_COUNT * floor (f / GAR_IDLE_COUNT);
	return GAR_IDLE_FIRST + f;
};
