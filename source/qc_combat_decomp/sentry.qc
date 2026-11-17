#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE SENTRY GUN (see sentry_defs.qc for the rules and numbers)

A port of Team Fortress 2.9's level 2 sentry gun (SENTRY.QC; the build from ENGINEER.QC TeamFortress_FinishedBuilding),
with TF's engineer, metal and spanner menu swapped for a gun: the spanner (the fourth fun gun, funguns.qc) builds one,
then reloads (bm_reload.qc or FunGun_Regen).
TF made the sentry itself the attacker and sorted out frags in its own obituary; here its damage is dealt in its
builder's name (T_Damage attacker = sg_owner) with sg_inflicting set, so frags and the kill message just work.
Hooks: FunGun_Attack calls Sentry_Build; the obituary checks sg_inflicting.
================
*/

void() Sentry_Precache =
{
	precache_model ("progs/turrbase.mdl");
	precache_model ("progs/turrgun.mdl");
	precache_model ("progs/tgib1.mdl");
	precache_model ("progs/tgib2.mdl");
	precache_model ("progs/tgib3.mdl");
	precache_model ("progs/v_span.mdl");
	precache_sound ("weapons/turrset.wav");
	precache_sound ("weapons/turrspot.wav");
	precache_sound ("weapons/turridle.wav");
	precache_sound ("weapons/sniper.wav");
	precache_sound ("weapons/r_exp3.wav");
};

// signed difference a - b in degrees, -180..180
float(float a, float b) Sentry_AngDiff =
{
	return anglemod (a - b + 180) - 180;
};

void() Sentry_Stand;
void() Sentry_Atk1;
void() Sentry_Atk2;
void() Sentry_Atk3;

// ---------------------------------------------------------------- dying

void() Sentry_Explode =
{
	sg_inflicting = TRUE;
	T_RadiusDamage (self, self.sg_owner, 75, self);
	sg_inflicting = FALSE;
	ThrowGib ("progs/tgib1.mdl", -70);
	ThrowGib ("progs/tgib2.mdl", -70);
	ThrowGib ("progs/tgib3.mdl", -70);
	if (self.sg_base)
		remove (self.sg_base);
	self.sg_base = world;
	sound7 (self, CHAN_AUTO, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
	BecomeExplosion ();
};

void() Sentry_Die =
{
	if (self.sg_owner.sg_sentry == self)
	{
		sprint (self.sg_owner, "Your sentry gun was destroyed.\n");
		self.sg_owner.sg_sentry = world;
	}
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.think = Sentry_Explode;
	self.nextthink = time + 0.1;
};

void(entity attacker, float damage) Sentry_Pain = {};

// TRUE if the sentry is gone (its builder left or replaced it) or just blew up (CheckSentry: knocked off its tripod)
float() Sentry_Gone =
{
	if (self.sg_owner.sg_sentry != self || self.sg_owner.classname != "player")
	{
		if (self.sg_base)
			remove (self.sg_base);
		remove (self);
		return TRUE;
	}
	if (vlen (self.sg_base.origin - self.origin) > 15)
	{
		bprint (strcat (self.sg_owner.netname, "'s sentry gun malfunctioned\n"));
		Sentry_Die ();
		return TRUE;
	}
	return FALSE;
};

// ---------------------------------------------------------------- finding someone to shoot

// Sentry_FindTarget: the nearest player it can see within SG_RANGE, but never its builder
float() Sentry_FindTarget =
{
	local entity e, best;
	local float d, bd;

	best = world;
	bd = SG_RANGE + 1;
	e = find (world, classname, "player");
	while (e)
	{
		if (e != self.sg_owner && e.takedamage && e.health > 0 && !(e.flags & FL_NOTARGET) && !(e.items & IT_INVISIBILITY))
		{
			d = vlen (e.origin - self.origin);
			if (d < bd && visible (e))
			{
				best = e;
				bd = d;
			}
		}
		e = find (e, classname, "player");
	}
	if (!best)
		return FALSE;
	// Sentry_FoundTarget / Sentry_HuntTarget
	self.enemy = best;
	if (self.sg_shells > 0)
		sound7 (self, CHAN_VOICE, "weapons/turrspot.wav", 1, ATTN_NORM, SNDSPD);
	self.ideal_yaw = vectoyaw (self.enemy.origin - self.origin);
	self.think = Sentry_Atk1;
	self.nextthink = time + 0.1;
	return TRUE;
};

// idle: sweep 50 degrees each way
void() Sentry_Rotate =
{
	self.effects = self.effects - (self.effects & EF_DIMLIGHT);
	if (Sentry_Gone ())
		return;
	if (Sentry_FindTarget ())
		return;
	if (self.sg_sweep == 0)
	{
		self.ideal_yaw = self.sg_waitmin;
		ChangeYaw ();
		if (fabs (Sentry_AngDiff (self.angles_y, self.sg_waitmin)) < 1)
		{
			self.sg_sweep = 1;
			if (random () < 0.1)
				sound7 (self, CHAN_ITEM, "weapons/turridle.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
	else
	{
		self.ideal_yaw = self.sg_waitmax;
		ChangeYaw ();
		if (fabs (Sentry_AngDiff (self.angles_y, self.sg_waitmax)) < 1)
			self.sg_sweep = 0;
	}
};

void() Sentry_Face =
{
	self.ideal_yaw = anglemod (vectoyaw (self.enemy.origin - self.origin));
	ChangeYaw ();
};

// ---------------------------------------------------------------- shooting

// Sentry_Fire: only once it has turned to within 10 degrees; 4 pellets of 4 (TF's FireBullets (4, dir, '0.1 0.1 0'),
// whose direction wasn't normalised, so the spread shrinks with distance)
float() Sentry_Fire =
{
	local vector dir, src, direction;
	local float n, spread;

	self.effects = self.effects - (self.effects & EF_DIMLIGHT);
	if (self.enemy.health <= 0)
		return FALSE;
	dir = self.enemy.origin - self.origin;
	if (fabs (Sentry_AngDiff (self.ideal_yaw, self.angles_y)) > 10)
		return FALSE;
	if (self.sg_shells <= 0)
		return FALSE;
	self.sg_shells = self.sg_shells - 1;
	self.effects = self.effects | EF_DIMLIGHT;
	sound7 (self, CHAN_WEAPON, "weapons/sniper.wav", 1, ATTN_NORM, SNDSPD);

	self.v_angle = self.angles;
	makevectors (self.v_angle);
	src = self.origin + v_forward * 10;
	src_z = self.absmin_z + self.size_z * 0.7;
	spread = 0.1 / max (vlen (dir), 1);
	dir = normalize (dir);
	ClearMultiDamage ();
	n = 4;
	while (n > 0)
	{
		direction = normalize (dir + crandom () * spread * v_right + crandom () * spread * v_up);
		traceline (src, src + direction * 2048, FALSE, self);
		if (trace_fraction != 1)
			TraceAttack (3, direction);		// blood or a wall puff; the damage adds up in multi_damage
		n = n - 1;
	}
	if (multi_ent)
	{
		sg_inflicting = TRUE;
		T_Damage (multi_ent, self, self.sg_owner, multi_damage);
		sg_inflicting = FALSE;
	}
	ClearMultiDamage ();

	if (self.sg_shells == 0)
		sprint (self.sg_owner, "Sentry Gun is out of shells.\n");
	else if (self.sg_shells == 20)
		sprint (self.sg_owner, "Sentry Gun is low on shells.\n");
	return TRUE;
};

// TF lvl2_sentry_*: frames 3-5, every frame fires (10 shots a second)
void() Sentry_Stand = [ 3, Sentry_Stand ] { Sentry_Rotate (); };
void() Sentry_Atk1 = [ 4, Sentry_Atk2 ]
{
	if (Sentry_Gone ())
		return;
	Sentry_Face ();
	if (!self.enemy || self.enemy.health <= 0 || !self.enemy.takedamage || !visible (self.enemy) || self.enemy.classname != "player")
		Sentry_Stand ();
	else if (self.sg_shells <= 0)
		Sentry_Stand ();
	else if (!Sentry_Fire ())
		Sentry_Atk3 ();
};
void() Sentry_Atk2 = [ 5, Sentry_Atk3 ] { Sentry_Face (); Sentry_Fire (); };
void() Sentry_Atk3 = [ 3, Sentry_Atk1 ] { Sentry_Face (); Sentry_Fire (); };

// ---------------------------------------------------------------- building

void() Sentry_Built =
{
	self.alpha = 0;
	sound7 (self, CHAN_VOICE, "weapons/turrset.wav", 1, ATTN_NORM, SNDSPD);
	Sentry_Stand ();
};

// the builder's old sentry goes up when a new one is built
void(entity old) Sentry_Replace =
{
	local entity oself;

	oself = self;
	self = old;
	self.sg_owner.sg_sentry = world;
	Sentry_Die ();
	self = oself;
};

void(string why) Sentry_CantBuild =
{
	centerprint (self, why);
};

// TeamFortress_Build + CheckArea + TeamFortress_FinishedBuilding: 64 units ahead, on the floor, with room.
// TRUE = built; FALSE = it told the player why not
float() Sentry_Build =
{
	local vector site, flr;
	local entity e, b, g;
	local float yaw;

	if (!(self.flags & FL_ONGROUND))
	{
		Sentry_CantBuild ("You need your feet on the ground to build\n");
		return FALSE;
	}
	makevectors (self.v_angle_y * '0 1 0');
	site = self.origin + v_forward * 64;
	traceline (self.origin, site, TRUE, self);
	if (trace_fraction < 1)
	{
		Sentry_CantBuild ("Not enough room to build here\n");
		return FALSE;
	}
	traceline (site, site - '0 0 64', TRUE, self);
	if (trace_fraction == 1)
	{
		Sentry_CantBuild ("No floor to build on\n");
		return FALSE;
	}
	flr = trace_endpos;
	tracebox (flr + '0 0 1', '-16 -16 0', '16 16 48', flr + '0 0 1', TRUE, self);
	if (trace_startsolid || trace_allsolid)
	{
		Sentry_CantBuild ("Not enough room to build here\n");
		return FALSE;
	}
	e = findradius (flr + '0 0 24', 64);
	while (e)
	{
		if (e != self && e != self.sg_sentry && e.solid != SOLID_NOT && e.solid != SOLID_TRIGGER
			&& ((e.flags & (FL_CLIENT | FL_MONSTER)) || e.classname == "building_sentrygun"))
		{
			Sentry_CantBuild ("Something is in the way\n");
			return FALSE;
		}
		e = e.chain;
	}

	if (self.sg_sentry)
		Sentry_Replace (self.sg_sentry);

	yaw = anglemod (self.angles_y + 180);		// it faces its builder, like TF's
	b = spawn ();
	b.classname = "building_sentrygun_base";
	b.movetype = MOVETYPE_NONE;
	b.solid = SOLID_NOT;
	b.angles_y = yaw;
	setmodel (b, "progs/turrbase.mdl");
	setsize (b, '-16 -16 0', '16 16 4');
	setorigin (b, flr);

	g = spawn ();
	g.classname = "building_sentrygun";
	g.netname = "sentry gun";
	g.health = SG_HEALTH;
	g.max_health = SG_HEALTH;
	g.th_die = Sentry_Die;
	g.th_pain = Sentry_Pain;
	g.takedamage = DAMAGE_AIM;
	g.solid = SOLID_BBOX;
	g.movetype = MOVETYPE_STEP;
	setmodel (g, "progs/turrgun.mdl");
	setsize (g, '-16 -16 0', '16 16 48');
	setorigin (g, flr + '0 0 8');
	g.view_ofs = '0 0 22';
	g.skin = 1;			// TF's level 2 skin
	g.frame = 3;
	g.colormap = self.colormap;
	g.velocity = '0 0 -8';
	g.flags = g.flags - (g.flags & FL_ONGROUND);
	g.yaw_speed = 10;
	g.angles = '0 1 0' * yaw;
	g.ideal_yaw = yaw;
	g.sg_waitmin = anglemod (yaw - 50);
	g.sg_waitmax = anglemod (yaw + 50);
	g.sg_owner = self;
	g.sg_base = b;
	g.sg_shells = SG_SHELLS;
	g.alpha = 0.5;		// see-through while it sets up
	g.think = Sentry_Built;
	g.nextthink = time + SG_BUILD_TIME;
	sound7 (g, CHAN_WEAPON, "weapons/turrset.wav", 1, ATTN_NORM, SNDSPD);

	self.sg_sentry = g;
	self.sg_swing = time;
	self.show_hostile = time + 1;
	return TRUE;
};
