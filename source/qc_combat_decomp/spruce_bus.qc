#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
spruce_bus.qc — Random Neighborhood School Bus for `spruce`
Periodically spawns `progs/veh_schoolbus.md3` along one of 3 Spruce St / Beech St routes
every 15-35s, drives smoothly around street curves & intersections, lets players roof-surf,
knocks aside pedestrians, and explodes mid-drive using full `vehicles.qc` wreck & debris FX.
*/

.float	sb_route;
.float	sb_wp;
.float	sb_wp_count;
.float	sb_spd;
.float	sb_horn_t;
.float	sb_engine_t;

entity	sb_manager;
entity	sb_active_bus;

float(float a) SB_NormYaw =
{
	while (a >= 360)
		a = a - 360;
	while (a < 0)
		a = a + 360;
	return a;
};

float(float a) SB_NormDelta =
{
	while (a > 180)
		a = a - 360;
	while (a < -180)
		a = a + 360;
	return a;
};

float(float r) SB_RouteLen =
{
	if (r == 0)
		return 22;
	if (r == 1)
		return 10;
	return 15;
};

vector(float r, float idx) SB_Waypoint =
{
	if (r == 0)
	{
		if (idx == 0) return '-5520 -9000 2';
		if (idx == 1) return '-3473 -6418 2';
		if (idx == 2) return '-1879 -4370 2';
		if (idx == 3) return '376 -1397 2';
		if (idx == 4) return '-360 -996 2';
		if (idx == 5) return '-1172 -552 2';
		if (idx == 6) return '-1776 -240 2';
		if (idx == 7) return '-2328 84 2';
		if (idx == 8) return '-2340 576 2';
		if (idx == 9) return '-2054 1388 2';
		if (idx == 10) return '-1860 2328 2';
		if (idx == 11) return '-1668 2873 2';
		if (idx == 12) return '427 2850 2';
		if (idx == 13) return '1312 2842 2';
		if (idx == 14) return '1884 2602 2';
		if (idx == 15) return '2448 2112 2';
		if (idx == 16) return '2748 1680 2';
		if (idx == 17) return '2400 1200 2';
		if (idx == 18) return '1956 623 2';
		if (idx == 19) return '376 -1397 2';
		if (idx == 20) return '1244 -6692 2';
		return '4440 -9240 2';
	}
	if (r == 1)
	{
		if (idx == 0) return '-9240 -7200 2';
		if (idx == 1) return '-7200 -5664 2';
		if (idx == 2) return '-5092 -4025 2';
		if (idx == 3) return '-4369 -3702 2';
		if (idx == 4) return '-3586 -3619 2';
		if (idx == 5) return '-2813 -3781 2';
		if (idx == 6) return '-1879 -4370 2';
		if (idx == 7) return '-502 -5485 2';
		if (idx == 8) return '1244 -6692 2';
		return '4560 -9360 2';
	}
	// Route 2: Reverse Loop E -> N -> W -> SW Spur
	if (idx == 0) return '4440 -9240 2';
	if (idx == 1) return '1244 -6692 2';
	if (idx == 2) return '376 -1397 2';
	if (idx == 3) return '1956 623 2';
	if (idx == 4) return '2748 1680 2';
	if (idx == 5) return '1884 2602 2';
	if (idx == 6) return '427 2850 2';
	if (idx == 7) return '-1668 2873 2';
	if (idx == 8) return '-2054 1388 2';
	if (idx == 9) return '-2328 84 2';
	if (idx == 10) return '-1172 -552 2';
	if (idx == 11) return '376 -1397 2';
	if (idx == 12) return '-1879 -4370 2';
	if (idx == 13) return '-3473 -6418 2';
	return '-5520 -9000 2';
};

void() SB_ManagerThink;

void() SB_ScheduleNext =
{
	if (sb_manager)
	{
		sb_manager.think = SB_ManagerThink;
		sb_manager.nextthink = time + 15 + random () * 20;
	}
};

void() SB_WreckRemove =
{
	if (sb_active_bus == self)
		sb_active_bus = world;
	remove (self);
};

void() SB_BusWreckThink =
{
	Veh_Think ();
	if (self.nextthink <= 0)
		SB_WreckRemove ();
	else
		self.think = SB_BusWreckThink;
};

void() SB_BusExplode =
{
	Veh_ExplodeNow ();
	// Run full Veh_Think wreck flip/roll & lingering flame animation, then prune when finished
	self.think = SB_BusWreckThink;
};

void() SB_BusDie =
{
	if (damage_attacker != world && damage_attacker != self && !damage_attacker.veh_kind)
		self.veh_igniter = damage_attacker;
	else if (damage_attacker.veh_kind && damage_attacker.veh_igniter != world)
		self.veh_igniter = damage_attacker.veh_igniter;
	self.movetype = MOVETYPE_NONE;
	self.velocity = VEC_ORIGIN;
	self.avelocity = VEC_ORIGIN;
	if (sb_active_bus == self)
		sb_active_bus = world;
	SB_ScheduleNext ();
	// not right here: a rocket's T_RadiusDamage may be what killed it, and the bus blast's own findradius would rewrite
	// the .chain list that loop is still walking. It goes off on its next think (Veh_Explode does the same)
	self.takedamage = DAMAGE_NO;
	self.touch = SUB_Null;
	self.think = SB_BusExplode;
	self.nextthink = time;
};

void() SB_BusTouch =
{
	local vector d;
	local float top_z;

	if (self.veh_state == VEH_STATE_WRECK)
		return;
	if (!other || other == world)
		return;

	top_z = self.origin_z + self.maxs_z;
	// Allow players to surf on the roof cleanly
	if (other.classname == "player" && (other.origin_z + other.mins_z) >= top_z - 16)
		return;

	// Heavy front/side roadkill knockback against players & NPCs
	if (other.takedamage && (other.classname == "player" || other.classname == "npc_spruce_worker") && time >= other.veh_hit_t)
	{
		other.veh_hit_t = time + 0.75;
		d = other.origin - self.origin;
		d_z = 0;
		if (vlen (d) > 1)
			d = normalize (d);
		else
			d = '1 0 0';
		other.velocity = d * 260 + normalize (self.velocity) * 200 + '0 0 240';
		other.flags = other.flags - (other.flags & FL_ONGROUND);
		sound (self, CHAN_AUTO, "vehicles/horn.wav", 0.9, ATTN_NORM);
		T_Damage (other, self, self, 30);
	}
};

void() SB_BusBlocked =
{
	local vector d;

	if (!other || other == world)
		return;
	// Clear parked/wrecked vehicles out of the street lane so the bus never stalls
	if (other.veh_kind > 0 && other != self)
	{
		other.solid = SOLID_NOT;
		T_Damage (other, self, self, 999);
		return;
	}
	if (other.takedamage)
	{
		d = other.origin - self.origin;
		d_z = 0;
		d = (vlen (d) > 1) ? normalize (d) : '1 0 0';
		other.velocity = d * 260 + '0 0 260';
		other.flags = other.flags - (other.flags & FL_ONGROUND);
		if (time >= other.veh_hit_t)
		{
			other.veh_hit_t = time + 0.75;
			T_Damage (other, self, self, 32);
		}
	}
};

void() SB_BusThink =
{
	local vector goal, d;
	local float dist, want_yaw, delta, spd, rate, f;

	if (self.veh_state == VEH_STATE_WRECK)
		return;

	self.nextthink = self.ltime + 0.05;

	// Engine idle / shudder + smoke if catching fire
	self.veh_anim = self.veh_anim + 0.65;
	f = floor (self.veh_anim);
	if (self.veh_state == VEH_STATE_FIRE)
	{
		self.frame = 22 + (f - 14 * floor (f / 14));
		if (time >= self.veh_fx_t)
		{
			self.veh_fx_t = time + 0.14;
			pointparticles (veh_fx_fire, self.origin + '0 0 56', '0 0 0', 1);
		}
		if (time >= self.veh_cook_t)
		{
			self.veh_cook_t = time + 0.35;
			self.health = self.health - 12;
			if (self.health <= 0)
			{
				SB_BusDie ();
				return;
			}
		}
	}
	else
	{
		self.frame = f - 16 * floor (f / 16);
	}

	if (time >= self.sb_engine_t)
	{
		self.sb_engine_t = time + 1.0;
		sound7 (self, CHAN_ITEM, "vehicles/idle_van.wav", 0.42, ATTN_STATIC, 88);
	}
	if (time >= self.sb_horn_t)
	{
		self.sb_horn_t = time + 6 + random () * 8;
		sound (self, CHAN_VOICE, "vehicles/horn.wav", 0.72, ATTN_NORM);
	}
	// Big splash wake when plowing through flooded streets!
	if (spruce_flood_z > 14 && random () < 0.7)
		particle (self.origin + '0 0 12', '0 0 110', 42, 16);

	goal = SB_Waypoint (self.sb_route, self.sb_wp);
	d = goal - self.origin;
	d_z = 0;
	dist = vlen (d);
	if (dist < 42)
	{
		self.sb_wp = self.sb_wp + 1;
		if (self.sb_wp >= self.sb_wp_count)
		{
			// Clean exit off the map -> schedule next random school bus pass
			if (sb_active_bus == self)
				sb_active_bus = world;
			SB_ScheduleNext ();
			remove (self);
			return;
		}
		goal = SB_Waypoint (self.sb_route, self.sb_wp);
		d = goal - self.origin;
		d_z = 0;
	}

	want_yaw = vectoyaw (d);
	delta = SB_NormDelta (want_yaw - self.angles_y);
	rate = 115 * 0.05;
	if (delta > rate)
		delta = rate;
	if (delta < 0 - rate)
		delta = 0 - rate;
	self.avelocity = '0 1 0' * (delta * 20);
	Veh_SetRotatedBounds (self, VEH_SCHOOLBUS, FALSE);

	spd = self.sb_spd;
	if (fabs (delta) > 3)
		spd = spd * 0.65;
	if (vlen (d) > 1)
		self.velocity = normalize (d) * spd;
};

void() SB_SpawnBus =
{
	local entity b;
	local vector p0, p1;
	local float r;

	if (sb_active_bus != world)
		return;

	r = floor (random () * 3);
	if (r > 2)
		r = 2;

	b = spawn ();
	b.classname = "spruce_schoolbus";
	b.veh_kind = VEH_SCHOOLBUS;
	b.veh_state = VEH_STATE_IDLE;
	b.veh_temp = TRUE;
	b.sb_route = r;
	b.sb_wp = 1;
	b.sb_wp_count = SB_RouteLen (r);
	b.sb_spd = 310 + random () * 70;

	p0 = SB_Waypoint (r, 0);
	p1 = SB_Waypoint (r, 1);
	b.angles = '0 0 0';
	b.angles_y = vectoyaw (p1 - p0);

	b.movetype = MOVETYPE_PUSH;
	b.solid = SOLID_BBOX;
	b.takedamage = DAMAGE_AIM;
	b.max_health = 450;
	b.health = 450;
	b.th_pain = Veh_Pain;
	b.th_die = SB_BusDie;
	b.touch = SB_BusTouch;
	b.blocked = SB_BusBlocked;

	setmodel (b, "progs/veh_schoolbus.md3");
	setsize (b, '-68 -68 0', '68 68 104');
	setorigin (b, p0);

	b.sb_horn_t = time + 2 + random () * 3;
	b.sb_engine_t = time + 0.2;
	b.think = SB_BusThink;
	b.nextthink = b.ltime + 0.05;
	sb_active_bus = b;
};

void() SB_ManagerThink =
{
	if (sb_active_bus == world)
		SB_SpawnBus ();
	else
		self.nextthink = time + 5;
};

void() misc_spruce_bus_manager =
{
	Vehicles_Precache ();
	precache_model ("progs/veh_schoolbus.md3");	// SB_SpawnBus sets it directly; vehicle bodies are precached per kind now
	precache_model ("progs/veh_schoolbus_wreck.md3");
	precache_model ("progs/veh_schoolbus_wheel.md3");
	precache_model ("progs/veh_schoolbus_hood.md3");
	precache_model ("progs/veh_schoolbus_door.md3");
	precache_model ("progs/veh_schoolbus_extra.md3");
	precache_model ("progs/veh_schoolbus_bumper.md3");
	sb_manager = self;
	sb_active_bus = world;
	self.think = SB_ManagerThink;
	// Spawn first random school bus shortly after level load
	self.nextthink = time + 6 + random () * 5;
};
