#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE M4 (see m4_defs.qc for the rules and frame map)

FunGun_Attack calls M4_Press every frame fire is held (exempt from bm_fg_lock).
FunGun_ViewFrame calls M4_Anim for the view model's frame, reload/draw foley sounds, and third-person rifle attachment.
================
*/

string	m4_snd_fire1;
string	m4_snd_fire2;
string	m4_snd_clipout;
string	m4_snd_clipin;
string	m4_snd_bolt;
string	m4_snd_deploy;
string	m4_snd_dry;
float	m4_pmodel_ok;
float	m4_fx_hole;
float	m4_fx_spark;

// the CS sound when the file exists, else a stock sound that is precached anyway
string(string cs, string fallback) M4_PickSound =
{
	local float fh;

	fh = fopen (strcat ("sound/", cs), 0);
	if (fh < 0)
		return fallback;
	fclose (fh);
	precache_sound (cs);
	return cs;
};

void() M4_Precache =
{
	local float fh;

	m4_ok = 0;
	m4_pmodel_ok = 0;
	fh = fopen ("progs/v_m4.md3", 0);
	if (fh < 0)
		return;
	fclose (fh);
	precache_model ("progs/v_m4.md3");
	fh = fopen ("progs/p_m4.md3", 0);
	if (fh >= 0)
	{
		fclose (fh);
		precache_model ("progs/p_m4.md3");
		m4_pmodel_ok = 1;
	}
	precache_model ("progs/muzzleflash1.spr");
	precache_model ("progs/nailcasing.mdl");
	m4_snd_fire1 = M4_PickSound ("cs16/m4a1_unsil-1.wav", "weapons/sgun1.wav");
	m4_snd_fire2 = M4_PickSound ("cs16/m4a1_unsil-2.wav", m4_snd_fire1);
	m4_snd_clipout = M4_PickSound ("cs16/m4a1_clipout.wav", "weapons/lock4.wav");
	m4_snd_clipin = M4_PickSound ("cs16/m4a1_clipin.wav", "weapons/pkup.wav");
	m4_snd_bolt = M4_PickSound ("cs16/m4a1_boltpull.wav", "weapons/pkup.wav");
	m4_snd_deploy = M4_PickSound ("cs16/m4a1_deploy.wav", "weapons/pkup.wav");
	m4_snd_dry = M4_PickSound ("cs16/dryfire_rifle.wav", "weapons/lock4.wav");
	m4_fx_hole = particleeffectnum ("m4_hole");
	m4_fx_spark = particleeffectnum ("m4_spark");
	m4_ok = 1;
};

string() M4_VModel =
{
	if (!m4_ok)
		return "";
	return "progs/v_m4.md3";
};

// the reload plays on the view model even though bm_reload.qc puts every other gun away while it reloads
float(entity p) M4_ShowsReload =
{
	return (m4_ok && p.weapon == IT_FUNGUN && p.fg_sel == FG_M4 && p.bm_rl_slot == BM_FG7);
};

void() M4_VwepThink =
{
	local entity p;

	p = self.owner;
	if (!p || p.health <= 0 || p.weapon != IT_FUNGUN || p.fg_sel != FG_M4 || (p.items & IT_INVISIBILITY) || Veh_Driving (p) || p.veh_ride != world || JohnBird_Flying (p) || RocketRider_Flying (p) || MMTank_Driving (p) || EricCannon_Active (p) || FD_Flying (p))
	{
		if (p && p.m4_vwep == self)
			p.m4_vwep = world;
		remove (self);
		return;
	}
	self.nextthink = time + 0.05;
};

void() M4_UpdateVwep =
{
	local entity e;
	local float show;

	if (!m4_pmodel_ok)
		return;
	show = (self.weapon == IT_FUNGUN && self.fg_sel == FG_M4 && self.health > 0 && !(self.items & IT_INVISIBILITY) && self.model == "progs/player_torso.mdl" && !Veh_Driving (self) && self.veh_ride == world && !JohnBird_Flying (self) && !RocketRider_Flying (self) && !MMTank_Driving (self) && !EricCannon_Active (self) && !FD_Flying (self));
	if (!show)
	{
		if (self.m4_vwep)
		{
			remove (self.m4_vwep);
			self.m4_vwep = world;
		}
		return;
	}
	e = self.m4_vwep;
	if (!e)
	{
		e = spawn ();
		e.classname = "m4_vwep";
		e.owner = self;
		e.exteriormodeltoclient = self;
		e.scale = 1.0;
		setattachment (e, self, "");
		e.origin = '12 -9 9';
		e.angles = '0 0 0';
		e.think = M4_VwepThink;
		e.nextthink = time + 0.05;
		self.m4_vwep = e;
		setmodel (e, "progs/p_m4.md3");
	}
};

// first-person barrel flash + world muzzle smoke + right-side brass 5.56mm casing ejection
void() M4_MuzzleAndBrass =
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
			fl.scale = 0.09 + random () * 0.04;		// suppressed: barely a flicker at the end of the can
			fl.alpha = 0.45;
			setsize (fl, VEC_ORIGIN, VEC_ORIGIN);
			// the end of the silencer zz_m4.pk3 puts on v_m4.md3 (source/mm_tools/build_m4_pk3.py)
			setorigin (fl, '43.6 -15.4 -6.9');
			fl.think = SUB_Remove;
			fl.nextthink = time + 0.045;
		}

	}

	if (autocvar_shellcasing)
	{
		c = spawn ();
		ejectpos = (self.origin + self.view_ofs) + v_forward * 14 + v_right * 11 - v_up * 6;
		c.angles = self.v_angle;
		c.angles_x = 0 - c.angles_x;
		setorigin (c, ejectpos);
		setmodel (c, "progs/nailcasing.mdl");
		c.scale = 0.65;
		setsize (c, VEC_ORIGIN, VEC_ORIGIN);
		c.alpha = 1;
		c.movetype = MOVETYPE_BOUNCE;
		c.solid = SOLID_TRIGGER;
		c.touch = nailcasing_touch;
		c.takedamage = 0;
		c.velocity = (self.velocity * 0.75) + v_right * (85 + random () * 25) + v_up * (80 + random () * 25) + v_forward * (25 + crandom () * 12);
		if (coop || deathmatch)
		{
			c.casetype = CASING_NAIL;
			c.SendEntity = casing_sendtocsqc;
			c.SendFlags = c.SendFlags | 1;
			c.think = SUB_Remove;
			c.nextthink = time + 0.1;	// was one tick (audit 2026-11-26)
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

// crisp CS 1.6 wall bullet hole + directional spark burst + occasional spatialized ricochet on solid surfaces
void(vector dir) M4_WallImpact =
{
	local float r;

	if (pointcontents (trace_endpos) == CONTENT_SKY || pointcontents (trace_endpos + dir * 2) == CONTENT_SKY || pointcontents (trace_endpos - dir * 2) == CONTENT_SKY)
		return;

	if (m4_fx_hole >= 0)
		pointparticles (m4_fx_hole, trace_endpos, VEC_ORIGIN, 1);
	else
		sendParticle ("TE_GUNSHOT", trace_endpos - dir * 1, VEC_ORIGIN, 1, 0);

	if (m4_fx_spark >= 0)
		pointparticles (m4_fx_spark, trace_endpos + trace_plane_normal * 1.5, trace_plane_normal * 95, 1);
	else
		sendParticle ("TE_SPIKE", trace_endpos + trace_plane_normal * 1.5, VEC_ORIGIN, 1, 0);
	DN3FX_OnWallImpact (trace_endpos + trace_plane_normal * 1.5, trace_plane_normal);

	if (random () < 0.28)
	{
		r = random ();
		if (r < 0.34)
			pointsound (trace_endpos, "weapons/ric1.wav", 0.42, ATTN_NORM);
		else if (r < 0.67)
			pointsound (trace_endpos, "weapons/ric2.wav", 0.42, ATTN_NORM);
		else
			pointsound (trace_endpos, "weapons/ric3.wav", 0.42, ATTN_NORM);
	}
};

// fire held with the M4 out (from FunGun_Attack)
void() M4_Press =
{
	local float a, spr, dt, climb, sway, dist, dmg;
	local vector dir, src;

	if (self.bm_rl_slot == BM_FG7 || time < self.m4_draw_t + M4_DRAW_TIME)
	{
		self.attack_finished = time + 0.05;		// the reload and the draw cannot be shot through
		return;
	}
	a = FunGun_Ammo (self, FG_M4);
	if (a < 1)
	{
		FG_Snd (self, CHAN_WEAPON, m4_snd_dry, 0.85, 1);		// empty click; bm_reload.qc starts reload
		self.attack_finished = time + 0.3;
		return;
	}

	// CS 1.6 spray recovery: bloom builds while holding full-auto (dt ~ 0.09s) and settles quickly once you pause
	if (self.m4_bloom_t > 0)
	{
		dt = time - self.m4_bloom_t;
		if (dt > 0.135)
		{
			self.m4_bloom = max (0, self.m4_bloom - (dt - 0.11) * 3.8);
			if (self.m4_bloom == 0)
				self.m4_shot_n = 0;
		}
	}
	else
	{
		self.m4_bloom = 0;
		self.m4_shot_n = 0;
	}

	FunGun_SetAmmo (self, FG_M4, a - 1);
	self.fg_fire_t = time;
	self.bm_lastshot = time;
	self.m4_bloom_t = time;
	self.attack_finished = time + M4_REFIRE;
	player_mm1 ();
	if (random () < 0.5)
		FG_Snd (self, CHAN_WEAPON, m4_snd_fire1, 0.92, 1);
	else
		FG_Snd (self, CHAN_WEAPON, m4_snd_fire2, 0.92, 1);
	self.punchangle_x = 0 - (M4_RECOIL + self.m4_bloom * 2.1);
	self.punchangle_y = crandom () * (0.55 * self.m4_bloom);

	makevectors (self.v_angle);
	M4_MuzzleAndBrass ();

	spr = M4_SPREAD + (M4_SPREAD_BLOOM * self.m4_bloom * self.m4_bloom) + M4_SPREAD_MOVE * min (1, vlen (self.velocity) / 320);
	if (!(self.flags & FL_ONGROUND))
		spr = spr + M4_SPREAD_AIR;
	climb = M4_CLIMB_MAX * self.m4_bloom;
	sway = 0;
	if (self.m4_bloom > 0.5)
	{
		sway = self.m4_shot_n - 8 * floor (self.m4_shot_n * 0.125);
		if (sway > 4)
			sway = 8 - sway;
		sway = ((sway * 0.5) - 1) * 0.038 * ((self.m4_bloom - 0.5) * 2);
	}

	self.m4_bloom = min (1, self.m4_bloom + 0.16);
	self.m4_shot_n = self.m4_shot_n + 1;

	dir = normalize (v_forward + (sway + crandom () * spr) * v_right + (climb + crandom () * spr) * v_up);
	src = self.origin + self.view_ofs;
	traceline (src, src + (v_forward * 10), TRUE, self);
	src = (trace_fraction < 1) ? (src + (v_forward * max (0, (trace_fraction * 10) - 1))) : (src + (v_forward * 10));
	ClearMultiDamage ();
	traceline (src, src + dir * M4_RANGE, FALSE, self);
	dist = trace_fraction * M4_RANGE;
	dmg = M4_DAMAGE;
	if (dist > 1400)
		dmg = max (M4_DAMAGE * 0.55, M4_DAMAGE * (1 - 0.45 * ((dist - 1400) / 2100)));
	if (!PC_TraceIntercept (self, src, trace_endpos, dmg) && trace_fraction != 1)
	{
		if (trace_ent.takedamage || trace_ent.inflamed == 1)
			TraceAttack (dmg, dir);
		else
			M4_WallImpact (dir);
	}
	W_BulletSplash (dir);
	fg_inflicting = FG_M4;
	ApplyMultiDamage ();
	fg_inflicting = 0;
};

// every frame with the M4 out (from FunGun_ViewFrame): the view model frame, foley events, and 3rd-person rifle
float() M4_Anim =
{
	local float f, fr, t;

	if (time - self.m4_vf_t > 0.25)		// it was not the gun in hand a moment ago: draw it
	{
		self.m4_draw_t = time;
		self.m4_draw_stage = 0;
		self.m4_bloom = 0;
		self.m4_shot_n = 0;
	}
	self.m4_vf_t = time;
	M4_UpdateVwep ();

	if (self.bm_rl_slot == BM_FG7)
	{
		fr = (time - self.bm_rl_start) / max (0.05, self.bm_rl_end - self.bm_rl_start);
		if (fr > 1)
			fr = 1;
		if (self.m4_rl_stage < 1 && fr >= 25 / M4_RELOAD_COUNT)
		{
			self.m4_rl_stage = 1;
			FG_Snd (self, CHAN_ITEM, m4_snd_clipout, 0.9, 1);
		}
		if (self.m4_rl_stage < 2 && fr >= 53 / M4_RELOAD_COUNT)
		{
			self.m4_rl_stage = 2;
			FG_Snd (self, CHAN_ITEM, m4_snd_clipin, 0.9, 1);
		}
		if (self.m4_rl_stage < 3 && fr >= 88 / M4_RELOAD_COUNT)
		{
			self.m4_rl_stage = 3;
			FG_Snd (self, CHAN_ITEM, m4_snd_bolt, 0.92, 1);
		}
		return M4_RELOAD_FIRST + min (M4_RELOAD_COUNT - 1, floor (fr * M4_RELOAD_COUNT));
	}
	self.m4_rl_stage = 0;

	t = time - self.m4_draw_t;
	if (t < M4_DRAW_TIME)
	{
		if (self.m4_draw_stage < 1)
		{
			self.m4_draw_stage = 1;
			FG_Snd (self, CHAN_ITEM, m4_snd_deploy, 0.88, 1);
		}
		if (self.m4_draw_stage < 2 && t >= 17 / M4_DRAW_FPS)
		{
			self.m4_draw_stage = 2;
			FG_Snd (self, CHAN_ITEM, m4_snd_bolt, 0.92, 1);
		}
		return M4_DRAW_FIRST + min (M4_DRAW_COUNT - 1, floor (t * M4_DRAW_FPS));
	}

	t = time - self.fg_fire_t;
	if (self.fg_fire_t && t < M4_FIRE_COUNT / M4_FIRE_FPS)
		return M4_FIRE_FIRST + min (M4_FIRE_COUNT - 1, floor (t * M4_FIRE_FPS));

	f = floor (time * M4_IDLE_FPS);
	f = f - M4_IDLE_COUNT * floor (f / M4_IDLE_COUNT);
	return M4_IDLE_FIRST + f;
};
