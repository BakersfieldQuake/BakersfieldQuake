/*
================
LOLMAP1 INTERACTIVE PROPS (Combat+)

1. func_megaman_wheel:
   Giant hollow climbable brush entity (MOVETYPE_PUSH, SOLID_BSP) representing a
   Mega Man wheel/drum or hub rotating around a configurable axis.
   Map keys:
     rotate      vector   Rotation axis in Quake avelocity space (pitch_Y, yaw_Z, roll_X).
                          Defaults to '1 0 0' (spins around Y axle; use '0 0 1' for X axle).
                          If speed == 0 and vlen(rotate) > 1.5, vlen(rotate) is used as idle speed.
     speed       float    Idle spin speed in deg/s (default 20; set -1 or spawnflags 1 for 0).
     speed2      float    TURBO SPIN speed in deg/s when shot or .use'd (default 300).
     wait        float    TURBO SPIN duration in seconds (default 9.0).
     dmg         float    Optional pinch damage on block (default 0, light/non-crushing).
     count       float    Paddle/jump fling multiplier (default 1.0).
     targetname  string   Optional targetname so shootable func_button / gong can trigger turbo.
     target      string   Optional target fired once when entering turbo spin.
     spawnflags  1 = MMW_START_IDLE (idle speed 0 instead of 20)
                 2 = MMW_REVERSE    (reverse spin direction)

2. func_gong_shrine:
   Wat Mega Man shootable Temple Gong brush entity (MOVETYPE_PUSH, SOLID_BSP).
   Never dies; shooting or .use'ing plays deep bronze gong resonance, emits golden sparks,
   and fires target(s) with wait cooldown.
   Map keys:
     wait        float    Retrigger cooldown in seconds (default 1.0).
     dmg         float    Optional radial knockback impulse when struck (default 0).
     target      string   Optional target(s) fired when gong is struck.
     targetname  string   Optional targetname for external .use triggering.
     spawnflags  1 = GONG_SHOCKWAVE (gentle radial knockback pulse even if dmg == 0)
================
*/

float	MMW_START_IDLE	= 1;
float	MMW_REVERSE		= 2;
float	GONG_SHOCKWAVE	= 1;

float	lol_props_precached;
float	lol_fx_sparks;

.float	speed2;
.float	mmw_idle_spd;
.float	mmw_cur_spd;
.float	mmw_turbo_until;
.float	mmw_snd_t;
.float	mmw_spark_t;
.float	mmw_pinch_t;
.float	mmw_in_turbo;
.float	mmw_fling_t;
.float	gong_cool_t;
.entity	gong_shock_atk;		// Gong_Ring -> Gong_Shockwave: who struck it

void() LolProps_Precache =
{
	if (lol_props_precached)
		return;
	lol_props_precached = TRUE;

	precache_sound ("weapons/megamotor.wav");
	precache_sound ("megaman/mm_drive.wav");
	precache_sound ("megaman/tire1.wav");
	precache_sound ("vehicles/clang1.wav");
	precache_sound ("vehicles/clang2.wav");
	precache_sound ("vehicles/hit_metal1.wav");
	precache_sound ("hammer/hammer_clang.wav");
	precache_sound ("hammer/hammer_clang2.wav");
	precache_sound ("bikes/bell_ring.wav");
	precache_sound ("weapons/tink1.wav");

	lol_fx_sparks = particleeffectnum ("veh_sparks");
};

vector(entity e) Lol_BrushCenter =
{
	if (e.origin != VEC_ORIGIN)
		return e.origin;
	return (e.absmin + e.absmax) * 0.5;
};

// Tangential velocity (units/s) at world position `pos` due to bmodel `avelocity` around `center`
vector(entity wheel, vector pos) MWheel_TangentVel =
{
	local vector r, w;
	local float deg2rad;

	deg2rad = 0.01745329;
	r = pos - Lol_BrushCenter (wheel);
	// Quake avelocity = (pitch_around_Y, yaw_around_Z, roll_around_X)
	w_x = wheel.avelocity_z * deg2rad;
	w_y = wheel.avelocity_x * deg2rad;
	w_z = wheel.avelocity_y * deg2rad;

	// w x r
	return (
		(w_y * r_z - w_z * r_y) * '1 0 0'
		+ (w_z * r_x - w_x * r_z) * '0 1 0'
		+ (w_x * r_y - w_y * r_x) * '0 0 1'
	);
};

void(vector org, vector dir, float cnt) Lol_EmitSparks =
{
	te_spark (org, dir, cnt);
	if (lol_fx_sparks >= 0)
		pointparticles (lol_fx_sparks, org, dir * 0.5, 2);
};

void() MWheel_Think =
{
	local vector ctr, sp_org;
	local float in_turbo, step;

	self.velocity = VEC_ORIGIN;
	in_turbo = (time < self.mmw_turbo_until);
	if (in_turbo)
	{
		step = 45;
		if (self.mmw_cur_spd < self.speed2)
		{
			self.mmw_cur_spd = self.mmw_cur_spd + step;
			if (self.mmw_cur_spd > self.speed2)
				self.mmw_cur_spd = self.speed2;
		}
		self.avelocity = self.movedir * self.mmw_cur_spd;

		if (time >= self.mmw_snd_t)
		{
			self.mmw_snd_t = time + 0.55;
			sound7 (self, CHAN_BODY, "megaman/mm_drive.wav", 0.55, ATTN_NORM, 125 + (self.mmw_cur_spd / self.speed2) * 35);
		}
		if (time >= self.mmw_spark_t)
		{
			self.mmw_spark_t = time + 0.22;
			ctr = Lol_BrushCenter (self);
			sp_org = ctr + randomvec () * 64;
			Lol_EmitSparks (sp_org, '0 0 90', 10);
		}
		self.nextthink = self.ltime + 0.05;
		return;
	}

	// Coast smoothly back down toward idle speed
	self.mmw_in_turbo = FALSE;
	if (self.mmw_cur_spd > self.mmw_idle_spd)
	{
		self.mmw_cur_spd = self.mmw_cur_spd - 14;
		if (self.mmw_cur_spd < self.mmw_idle_spd)
			self.mmw_cur_spd = self.mmw_idle_spd;
		self.avelocity = self.movedir * self.mmw_cur_spd;
		self.nextthink = self.ltime + 0.05;
		return;
	}

	self.mmw_cur_spd = self.mmw_idle_spd;
	self.avelocity = self.movedir * self.mmw_cur_spd;
	if (self.mmw_cur_spd <= 0)
	{
		self.avelocity = VEC_ORIGIN;
		self.nextthink = -1;
		return;
	}
	self.nextthink = self.ltime + 0.25;
};

void(entity attacker, vector hit_org) MWheel_TriggerTurbo =
{
	local float was_turbo;

	self.health = self.max_health;
	self.deadflag = DEAD_NO;
	self.takedamage = DAMAGE_YES;

	was_turbo = (self.mmw_in_turbo && time < self.mmw_turbo_until);
	self.mmw_turbo_until = time + self.wait;
	self.mmw_in_turbo = TRUE;

	// Kick-start non-zero avelocity immediately so DarkPlaces MOVETYPE_PUSH ltime advances
	if (self.mmw_cur_spd < 75)
		self.mmw_cur_spd = 75;
	self.avelocity = self.movedir * self.mmw_cur_spd;
	self.think = MWheel_Think;
	self.nextthink = self.ltime + 0.05;

	if (hit_org == VEC_ORIGIN)
		hit_org = Lol_BrushCenter (self) + randomvec () * 48;
	Lol_EmitSparks (hit_org, '0 0 110', 14);

	if (time >= self.mmw_snd_t - 0.35)
	{
		if (random () < 0.5)
			sound7 (self, CHAN_AUTO, "vehicles/clang1.wav", 0.72, ATTN_NORM, 108 + random () * 16);
		else
			sound7 (self, CHAN_AUTO, "vehicles/clang2.wav", 0.72, ATTN_NORM, 108 + random () * 16);
		if (!was_turbo)
			sound7 (self, CHAN_VOICE, "weapons/megamotor.wav", 0.85, ATTN_NORM, 128);
		self.mmw_snd_t = time + 0.32;
	}

	if (!was_turbo && self.target != "" && self.target != self.targetname)
	{
		activator = attacker;
		SUB_UseTargets ();
	}
};

void(entity attacker, float take) MWheel_Pain =
{
	local vector hit_org;

	hit_org = Lol_BrushCenter (self);
	if (attacker != world)
		hit_org = hit_org + normalize (attacker.origin - hit_org) * 48;
	MWheel_TriggerTurbo (attacker, hit_org);
};

void() MWheel_Die =
{
	self.health = self.max_health;
	self.deadflag = DEAD_NO;
	self.solid = SOLID_BSP;
	self.movetype = MOVETYPE_PUSH;
	self.takedamage = DAMAGE_YES;
	MWheel_TriggerTurbo (damage_attacker, Lol_BrushCenter (self));
};

void() MWheel_Use =
{
	MWheel_TriggerTurbo (activator, Lol_BrushCenter (self));
};

void() MWheel_Touch =
{
	local vector tvel, r;
	local float spd_frac;

	if (other.classname != "player" || other.health <= 0)
		return;
	if (self.mmw_cur_spd < 90)
		return;
	if (time < other.mmw_fling_t)
		return;

	// Fling when airborne (jumping inside wheel) or riding fast spinning paddles
	r = other.origin - Lol_BrushCenter (self);
	if ((other.flags & FL_ONGROUND) && r_z < 12 && self.mmw_cur_spd < 180)
		return;

	other.mmw_fling_t = time + 0.40;
	other.flags = other.flags - (other.flags & FL_ONGROUND);
	tvel = MWheel_TangentVel (self, other.origin);
	spd_frac = self.mmw_cur_spd / 300;
	if (spd_frac > 1.5)
		spd_frac = 1.5;

	other.velocity = other.velocity * 0.4 + tvel * (0.75 * self.count);
	if (other.velocity_z < 280 + 160 * spd_frac * self.count)
		other.velocity_z = 280 + 160 * spd_frac * self.count;

	sound7 (other, CHAN_AUTO, "megaman/tire1.wav", 0.55, ATTN_NORM, 110 + random () * 15);
};

void() MWheel_Blocked =
{
	local vector ctr, d, tvel, push_org;

	if (other == world)
		return;

	ctr = Lol_BrushCenter (self);
	d = other.origin - ctr;
	if (vlen (d) < 4)
		d = '0 0 1';
	else
		d = normalize (d);

	if (other.classname == "player" || (other.flags & FL_MONSTER))
	{
		other.flags = other.flags - (other.flags & FL_ONGROUND);
		tvel = MWheel_TangentVel (self, other.origin);
		other.velocity = d * 190 + tvel * 0.5 + '0 0 260';

		// Gently free pinched player so DarkPlaces MOVETYPE_PUSH never stalls
		push_org = other.origin + '0 0 8';
		tracebox (push_org, other.mins, other.maxs, push_org, FALSE, other);
		if (!trace_startsolid && !trace_allsolid)
			setorigin (other, push_org);

		if (self.dmg > 0 && other.takedamage && time >= self.mmw_pinch_t)
		{
			self.mmw_pinch_t = time + 0.35;
			T_Damage (other, self, self, self.dmg);
		}
		return;
	}

	if (other.movetype == MOVETYPE_TOSS || other.movetype == MOVETYPE_BOUNCE)
	{
		other.flags = other.flags - (other.flags & FL_ONGROUND);
		other.velocity = d * 200 + '0 0 220';
	}
};

void() func_megaman_wheel =
{
	local float rlen;

	LolProps_Precache ();

	self.classname = "func_megaman_wheel";
	self.movetype = MOVETYPE_PUSH;
	self.solid = SOLID_BSP;
	self.velocity = VEC_ORIGIN;
	setmodel (self, self.model);
	setorigin (self, self.origin);
	setsize (self, self.mins, self.maxs);

	// Axis in Quake avelocity space (pitch_Y, yaw_Z, roll_X)
	if (self.rotate == VEC_ORIGIN)
		self.rotate = '1 0 0';
	rlen = vlen (self.rotate);
	self.movedir = normalize (self.rotate);
	if (self.spawnflags & MMW_REVERSE)
		self.movedir = self.movedir * -1;

	if (self.spawnflags & MMW_START_IDLE)
		self.mmw_idle_spd = 0;
	else if (self.speed < 0)
		self.mmw_idle_spd = 0;
	else if (self.speed > 0)
		self.mmw_idle_spd = self.speed;
	else if (rlen > 1.5)
		self.mmw_idle_spd = rlen;
	else
		self.mmw_idle_spd = 20;

	if (self.speed2 <= 0)
		self.speed2 = 300;
	if (self.wait <= 0)
		self.wait = 9.0;
	if (self.count <= 0)
		self.count = 1.0;
	if (self.dmg < 0)
		self.dmg = 0;

	self.max_health = 999999;
	self.health = self.max_health;
	self.takedamage = DAMAGE_YES;
	self.th_pain = MWheel_Pain;
	self.th_die = MWheel_Die;
	self.use = MWheel_Use;
	self.blocked = MWheel_Blocked;
	self.touch = MWheel_Touch;

	self.mmw_cur_spd = self.mmw_idle_spd;
	self.mmw_in_turbo = FALSE;
	self.mmw_turbo_until = 0;

	if (self.mmw_cur_spd > 0)
	{
		self.avelocity = self.movedir * self.mmw_cur_spd;
		self.think = MWheel_Think;
		self.nextthink = self.ltime + 0.2;
	}
	else
	{
		self.avelocity = VEC_ORIGIN;
		self.think = MWheel_Think;
		self.nextthink = -1;
	}
};

// ---------------------------------------------------------------- Wat Mega Man Shootable Temple Gong

void() Gong_Shockwave =
{
	local entity e, attacker;
	local vector ctr, d;
	local float rad;

	attacker = self.gong_shock_atk;
	self.gong_shock_atk = world;
	ctr = Lol_BrushCenter (self);
	rad = 220;
	e = findradius (ctr, rad);
	while (e != world)
	{
		if ((e.classname == "player" || (e.flags & FL_MONSTER)) && e.health > 0)
		{
			d = e.origin - ctr;
			d_z = 0;
			if (vlen (d) < 1)
				d = '1 0 0';
			else
				d = normalize (d);
			e.flags = e.flags - (e.flags & FL_ONGROUND);
			e.velocity = e.velocity + d * 260 + '0 0 180';
			if (self.dmg > 0 && e != attacker)
				T_Damage (e, self, attacker, self.dmg);
		}
		e = e.chain;
	}
};

void(entity attacker, vector hit_org) Gong_Ring =
{
	local vector ctr;

	self.health = self.max_health;
	self.deadflag = DEAD_NO;
	self.takedamage = DAMAGE_YES;

	if (time < self.gong_cool_t)
		return;
	self.gong_cool_t = time + self.wait;

	ctr = Lol_BrushCenter (self);
	if (hit_org == VEC_ORIGIN)
		hit_org = ctr;

	// Deep bronze temple gong boom + high shimmer bell overtone
	sound7 (self, CHAN_VOICE, "hammer/hammer_clang.wav", 1.0, 0.35, 52 + random () * 6);
	sound7 (self, CHAN_AUTO, "bikes/bell_ring.wav", 0.65, 0.55, 68 + random () * 6);
	Lol_EmitSparks (hit_org, '0 0 120', 18);

	if ((self.spawnflags & GONG_SHOCKWAVE) || self.dmg > 0)
	{
		// not right here: a rocket's T_RadiusDamage may be what struck the gong, and this findradius would rewrite the
		// .chain list that loop is still walking. MOVETYPE_PUSH thinks on its own .ltime clock
		self.gong_shock_atk = attacker;
		self.think = Gong_Shockwave;
		self.nextthink = self.ltime + 0.001;
	}

	if (self.target != "")
	{
		activator = attacker;
		SUB_UseTargets ();
	}
};

void(entity attacker, float take) Gong_Pain =
{
	local vector hit_org;

	hit_org = Lol_BrushCenter (self);
	if (attacker != world)
		hit_org = hit_org + normalize (attacker.origin - hit_org) * 16;
	Gong_Ring (attacker, hit_org);
};

void() Gong_Die =
{
	self.health = self.max_health;
	self.deadflag = DEAD_NO;
	self.solid = SOLID_BSP;
	self.movetype = MOVETYPE_PUSH;
	self.takedamage = DAMAGE_YES;
	Gong_Ring (damage_attacker, Lol_BrushCenter (self));
};

void() Gong_Use =
{
	Gong_Ring (activator, Lol_BrushCenter (self));
};

void() func_gong_shrine =
{
	LolProps_Precache ();

	self.classname = "func_gong_shrine";
	self.movetype = MOVETYPE_PUSH;
	self.solid = SOLID_BSP;
	setmodel (self, self.model);
	setorigin (self, self.origin);
	setsize (self, self.mins, self.maxs);

	if (self.wait <= 0)
		self.wait = 1.0;
	if (self.dmg < 0)
		self.dmg = 0;

	self.max_health = 999999;
	self.health = self.max_health;
	self.takedamage = DAMAGE_YES;
	self.th_pain = Gong_Pain;
	self.th_die = Gong_Die;
	self.use = Gong_Use;
	self.blocked = SUB_Null;
};
