#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
MOVING STREET TRAFFIC CARS (Combat+)

Lightweight, jump-on-able moving street vehicles built with MOVETYPE_PUSH + SOLID_BBOX
using existing bakersfield.pk3 MD3 models (zero new asset files).

Entity: misc_traffic_car
Map keys:
  origin    "x y z"     Initial spawn position on road surface Z (tires sit at z = 0 in MD3)
  pos1      "x y z"     Lane loop start (wrap-to endpoint). Optional if distance is set.
  pos2      "x y z"     Lane loop end (wrap-from endpoint). Optional if distance is set.
  angles    "0 yaw 0"   Facing yaw (auto-derived from pos2 - pos1 when pos1/pos2 are set)
  angle     yaw         Alternative single-float yaw when using distance mode
  distance  float       Travel length along yaw when pos1/pos2 are omitted (default 1024)
  cnt       float       Model preset (also accepts style if cnt == 0):
                          0 = auto-variety across presets 1..5 from origin hash
                          1 = sedan   (progs/veh_sedan.md3,     half 98x39,  height 54)
                          2 = coupe   (progs/veh_coupe.md3,     half 93x39,  height 48)
                          3 = gtcar   (progs/veh_gtcar.md3,     half 99x40,  height 50)
                          4 = truck   (progs/veh_truck.md3,     half 116x46, height 52)
                          5 = tuktuk  (progs/veh_tuktuk.md3,    half 56x28,  height 68)
                          6 = van     (progs/veh_van.md3,       half 110x44, height 88)
                          7 = bus     (progs/veh_schoolbus.md3, half 165x47, height 96)
  model     string      Optional explicit model path (overrides cnt/style)
  speed     float       Travel speed in units/sec (default 260)
  colormod  "r g b"     Optional RGB tint ('0 0 0' auto-picks street/taxi color variety)
  dmg       float       Optional bump damage on block/road hit (default 0, never insta-kills)
================
*/

float	TC_SEDAN	= 1;
float	TC_COUPE	= 2;
float	TC_GTCAR	= 3;
float	TC_TRUCK	= 4;
float	TC_TUKTUK	= 5;
float	TC_VAN		= 6;
float	TC_BUS		= 7;

float	tc_precached;

.vector	tc_dir;			// unit travel direction from pos1 -> pos2
.float	tc_len;			// lane length vlen(pos2 - pos1)
.float	tc_end_dot;		// pos2 * tc_dir
.float	tc_boom_t;		// cooldown preventing duplicate blast triggers

void() Traffic_Precache =
{
	if (tc_precached)
		return;
	tc_precached = TRUE;
	precache_model ("progs/veh_sedan.md3");
	precache_model ("progs/veh_coupe.md3");
	precache_model ("progs/veh_gtcar.md3");
	precache_model ("progs/veh_truck.md3");
	precache_model ("progs/veh_tuktuk.md3");
	precache_sound ("vehicles/car_boom1.wav");
	precache_sound ("weapons/r_exp3.wav");
};

string(float kind) Traffic_ModelForKind =
{
	if (kind == TC_COUPE)  return "progs/veh_coupe.md3";
	if (kind == TC_GTCAR)  return "progs/veh_gtcar.md3";
	if (kind == TC_TRUCK)  return "progs/veh_truck.md3";
	if (kind == TC_TUKTUK) return "progs/veh_tuktuk.md3";
	if (kind == TC_VAN)    return "progs/veh_van.md3";
	if (kind == TC_BUS)    return "progs/veh_schoolbus.md3";
	return "progs/veh_sedan.md3";
};

// Local half-length (hl), half-width (hw), and rideable top height (ht)
vector(float kind) Traffic_DimsForKind =
{
	if (kind == TC_COUPE)  return '93 39 48';
	if (kind == TC_GTCAR)  return '99 40 50';
	if (kind == TC_TRUCK)  return '116 46 52';
	if (kind == TC_TUKTUK) return '56 28 68';
	if (kind == TC_VAN)    return '110 44 88';
	if (kind == TC_BUS)    return '165 47 96';
	return '98 39 54';
};

void(entity e, vector dims, float yaw_deg) Traffic_SetRotatedBounds =
{
	local float rad, sn, cs, acs, asn, hx, hy;
	local vector bmin, bmax;

	rad = yaw_deg * 0.0174533;
	sn = sin (rad);
	cs = cos (rad);
	acs = fabs (cs);
	asn = fabs (sn);
	hx = acs * dims_x + asn * dims_y;
	hy = asn * dims_x + acs * dims_y;

	bmin_x = 0 - hx;
	bmin_y = 0 - hy;
	bmin_z = 0;
	bmax_x = hx;
	bmax_y = hy;
	bmax_z = dims_z;
	setsize (e, bmin, bmax);
};

vector(float idx) Traffic_AutoColor =
{
	local float c;

	c = idx - 8 * floor (idx / 8);
	if (c == 0) return '0.95 0.95 0.95';	// original paint
	if (c == 1) return '1.08 0.38 0.65';	// Bangkok pink taxi
	if (c == 2) return '1.08 0.98 0.30';	// yellow-gold taxi
	if (c == 3) return '0.38 1.02 0.52';	// emerald taxi
	if (c == 4) return '1.05 1.05 1.05';	// pearl white / silver
	if (c == 5) return '0.45 0.68 1.08';	// cobalt blue
	if (c == 6) return '1.08 0.42 0.35';	// crimson red
	return '1.08 0.68 0.30';				// amber orange
};

vector(vector col) Traffic_ClampColor =
{
	local float mx;

	mx = col_x;
	if (col_y > mx) mx = col_y;
	if (col_z > mx) mx = col_z;
	if (mx > 1.10)
		col = col * (1.10 / mx);
	return col;
};

void() Traffic_Touch =
{
	local float foot_z, top_z, want_h, need_vz;
	local vector d;

	if (other.classname != "player" || other.health <= 0)
		return;
	foot_z = other.origin_z + other.mins_z;
	top_z = self.origin_z + self.maxs_z;

	// Already on roof/hood level: keep riding smoothly
	if (foot_z >= top_z - 4)
		return;

	// Airborne jump alongside or onto the car -> vault cleanly onto roof
	if (!(other.flags & FL_ONGROUND) && other.velocity_z > 60 && foot_z >= self.origin_z + 6)
	{
		want_h = (top_z - foot_z) + 10;
		if (want_h > 0 && want_h <= 66)
		{
			need_vz = sqrt (1600 * want_h);
			if (need_vz > 330)
				need_vz = 330;
			if (other.velocity_z < need_vz)
				other.velocity_z = need_vz;
		}
		return;
	}

	// Road-level side/front contact: pop slightly upward & clear without trapping
	if (time >= other.veh_hit_t && (other.flags & FL_ONGROUND))
	{
		other.veh_hit_t = time + 0.65;
		d = other.origin - self.origin;
		d_z = 0;
		if (vlen (d) > 1)
			d = normalize (d);
		else
			d = self.tc_dir;
		other.velocity = self.tc_dir * (self.speed * 0.5) + d * 150 + '0 0 240';
		other.flags = other.flags - (other.flags & FL_ONGROUND);
		if (self.dmg > 0)
			T_Damage (other, self, self, self.dmg);
	}
};

void() Traffic_Blocked =
{
	local vector d;

	if (!other.takedamage)
		return;
	d = other.origin - self.origin;
	d_z = 0;
	if (vlen (d) > 1)
		d = normalize (d);
	else
		d = self.tc_dir;

	// Pop blocked entity up & clear so MOVETYPE_PUSH ltime never stalls
	other.velocity = d * 240 + '0 0 280';
	other.flags = other.flags - (other.flags & FL_ONGROUND);
	if (self.dmg > 0 && other.classname == "player" && time >= other.veh_hit_t)
	{
		other.veh_hit_t = time + 0.65;
		T_Damage (other, self, self, self.dmg);
	}
};

void() Traffic_Wrap =
{
	local entity p;
	local float top_z;

	top_z = self.pos1_z + self.maxs_z;
	p = bm_player_head;
	while (p)
	{
		if (p.groundentity == self)
		{
			p.groundentity = world;
			p.flags = p.flags - (p.flags & FL_ONGROUND);
			if (p.velocity_z < 180)
				p.velocity_z = 180;
		}
		else if (p.health > 0)
		{
			// Prevent wrapping directly over a player standing at pos1
			if (fabs (p.origin_x - self.pos1_x) < self.maxs_x + 28
				&& fabs (p.origin_y - self.pos1_y) < self.maxs_y + 28
				&& (p.origin_z + p.mins_z) < top_z
				&& (p.origin_z + p.maxs_z) > self.pos1_z)
			{
				setorigin (p, p.origin + '0 0 1' * (top_z - (p.origin_z + p.mins_z) + 4));
				p.flags = p.flags - (p.flags & FL_ONGROUND);
				if (p.velocity_z < 140)
					p.velocity_z = 140;
			}
		}
		p = p.bm_player_next;
	}
	setorigin (self, self.pos1);
};

// Detonate a moving street car when struck by heavy tank fire and respawn at lane start
void(entity car, entity atk) Traffic_BlastExplode =
{
	local vector boom_org;
	local float fx;
	local entity inf, oldself;

	if (car == world || time < car.tc_boom_t)
		return;
	car.tc_boom_t = time + 1.0;

	boom_org = car.origin + '0 0 28';
	fx = particleeffectnum ("veh_explode");
	if (fx > 0)
		pointparticles (fx, boom_org, '0 0 0', 1);
	else
		pointparticles (particleeffectnum ("TE_EXPLOSION"), boom_org, '0 0 0', 1);

	inf = spawn ();
	inf.classname = "traffic_car_blast";
	setorigin (inf, boom_org);
	sound7 (inf, CHAN_WEAPON, "vehicles/car_boom1.wav", 1.0, 0.25, 96 + random () * 8);
	sound7 (inf, CHAN_AUTO, "weapons/r_exp3.wav", 0.90, 0.35, 100);
	if (atk == world)
		atk = car;
	T_RadiusDamage (inf, atk, 140, car);
	remove (inf);

	oldself = self;
	self = car;
	Traffic_Wrap ();
	self = oldself;
};

void() Traffic_Think =
{
	local float dot, rem, dt;

	dot = (self.origin - self.pos2) * self.tc_dir;
	if (dot >= 0)
	{
		Traffic_Wrap ();
		rem = self.tc_len;
	}
	else
		rem = 0 - dot;

	dt = rem / self.speed;
	if (dt > 0.25)
		dt = 0.25;
	else if (dt < 0.05)
		dt = 0.05;

	self.velocity = self.tc_dir * self.speed;
	self.nextthink = self.ltime + dt;
};

void() misc_traffic_car =
{
	local float kind, hash, dt;
	local string mdl;
	local vector dims, span;

	Traffic_Precache ();

	// Deterministic hash from initial origin for variety
	hash = floor (fabs (self.origin_x * 0.017 + self.origin_y * 0.031 + self.origin_z * 0.011));

	kind = floor (self.cnt);
	if (kind <= 0)
		kind = floor (self.style);
	if (kind < 1 || kind > 7)
		kind = 1 + (hash - 5 * floor (hash / 5));

	if (self.model != "")
	{
		mdl = self.model;
		precache_model (mdl);
	}
	else
		mdl = Traffic_ModelForKind (kind);

	if (kind == TC_VAN)
		precache_model ("progs/veh_van.md3");
	else if (kind == TC_BUS)
		precache_model ("progs/veh_schoolbus.md3");

	if (self.speed <= 0)
		self.speed = 260;

	if (self.pos1 == VEC_ORIGIN && self.pos2 == VEC_ORIGIN)
	{
		if (self.distance <= 0)
			self.distance = 1024;
		makevectors ('0 1 0' * self.angles_y);
		self.pos1 = self.origin;
		self.pos2 = self.origin + v_forward * self.distance;
	}

	span = self.pos2 - self.pos1;
	self.tc_len = vlen (span);
	if (self.tc_len < 16)
	{
		remove (self);
		return;
	}
	self.tc_dir = span * (1 / self.tc_len);
	self.tc_end_dot = self.pos2 * self.tc_dir;
	self.angles = '0 0 0';
	self.angles_y = vectoyaw (self.tc_dir);

	if (kind == TC_TUKTUK)
		self.colormod = '1 1 1';	// keep painted Thai Tuk Tuk livery instead of solid pink/neon tint
	else if (self.colormod == VEC_ORIGIN)
		self.colormod = Traffic_AutoColor (hash + kind);
	else
		self.colormod = Traffic_ClampColor (self.colormod);

	self.classname = "misc_traffic_car";
	self.movetype = MOVETYPE_PUSH;
	self.solid = SOLID_BBOX;
	self.takedamage = DAMAGE_NO;
	self.frame = 0;
	self.touch = Traffic_Touch;
	self.blocked = Traffic_Blocked;

	setmodel (self, mdl);
	dims = Traffic_DimsForKind (kind);
	Traffic_SetRotatedBounds (self, dims, self.angles_y);
	setorigin (self, self.origin);

	self.velocity = self.tc_dir * self.speed;
	self.think = Traffic_Think;
	dt = (0 - ((self.origin - self.pos2) * self.tc_dir)) / self.speed;
	if (dt > 0.25)
		dt = 0.25;
	else if (dt < 0.05)
		dt = 0.05;
	self.nextthink = self.ltime + dt;
};
