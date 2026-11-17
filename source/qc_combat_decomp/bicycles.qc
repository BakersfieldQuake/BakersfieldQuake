#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
SHOOTABLE / TIRE-FLYING 3D BICYCLES - implementation (Combat+)

Models, skins, textures, shaders & sounds built by:
  - source/mm_tools/bicycles_mesh_tex.py
  - source/mm_tools/build_bicycles_assets.py
================
*/

void() Bike_Think;
void() Bike_Die;
void() Bike_CrashNow;
void(entity attacker, float take) Bike_Pain;
void(entity b, float kind) Bike_InitEntity;

// ---------------------------------------------------------------- Precache

void() Bikes_Precache =
{
	if (bikes_precached)
		return;
	bikes_precached = TRUE;

	precache_model ("progs/bike_cruiser.md3");
	precache_model ("progs/bike_cruiser_wreck.md3");
	precache_model ("progs/bike_cruiser_wheel.md3");
	precache_model ("progs/bike_cruiser_bars.md3");
	precache_model ("progs/bike_cruiser_saddle.md3");
	precache_model ("progs/bike_cruiser_extra.md3");

	precache_model ("progs/bike_bmx.md3");
	precache_model ("progs/bike_bmx_wreck.md3");
	precache_model ("progs/bike_bmx_wheel.md3");
	precache_model ("progs/bike_bmx_bars.md3");
	precache_model ("progs/bike_bmx_saddle.md3");
	precache_model ("progs/bike_bmx_extra.md3");

	precache_model ("progs/bike_road.md3");
	precache_model ("progs/bike_road_wreck.md3");
	precache_model ("progs/bike_road_wheel.md3");
	precache_model ("progs/bike_road_bars.md3");
	precache_model ("progs/bike_road_saddle.md3");
	precache_model ("progs/bike_road_extra.md3");

	precache_sound ("bikes/bell_ring.wav");
	precache_sound ("bikes/spoke_ping.wav");
	precache_sound ("bikes/tire_pop.wav");
	precache_sound ("bikes/tire_bounce.wav");
	precache_sound ("bikes/frame_crash.wav");

	bike_fx_sparks = particleeffectnum ("TE_GUNSHOT");
};

// ---------------------------------------------------------------- Geometry & Asset Lookup Helpers

float(float a) Bike_NormYaw =
{
	while (a >= 360)
		a = a - 360;
	while (a < 0)
		a = a + 360;
	return a;
};

string(float kind) Bike_IntactModel =
{
	if (kind == BIKE_CRUISER)
		return "progs/bike_cruiser.md3";
	if (kind == BIKE_BMX)
		return "progs/bike_bmx.md3";
	return "progs/bike_road.md3";
};

string(float kind) Bike_WreckModel =
{
	if (kind == BIKE_CRUISER)
		return "progs/bike_cruiser_wreck.md3";
	if (kind == BIKE_BMX)
		return "progs/bike_bmx_wreck.md3";
	return "progs/bike_road_wreck.md3";
};

string(float kind) Bike_WheelModel =
{
	if (kind == BIKE_CRUISER)
		return "progs/bike_cruiser_wheel.md3";
	if (kind == BIKE_BMX)
		return "progs/bike_bmx_wheel.md3";
	return "progs/bike_road_wheel.md3";
};

string(float kind) Bike_BarsModel =
{
	if (kind == BIKE_CRUISER)
		return "progs/bike_cruiser_bars.md3";
	if (kind == BIKE_BMX)
		return "progs/bike_bmx_bars.md3";
	return "progs/bike_road_bars.md3";
};

string(float kind) Bike_SaddleModel =
{
	if (kind == BIKE_CRUISER)
		return "progs/bike_cruiser_saddle.md3";
	if (kind == BIKE_BMX)
		return "progs/bike_bmx_saddle.md3";
	return "progs/bike_road_saddle.md3";
};

string(float kind) Bike_ExtraModel =
{
	if (kind == BIKE_CRUISER)
		return "progs/bike_cruiser_extra.md3";
	if (kind == BIKE_BMX)
		return "progs/bike_bmx_extra.md3";
	return "progs/bike_road_extra.md3";
};

float(float kind) Bike_MaxHP =
{
	if (kind == BIKE_CRUISER)
		return 95;
	if (kind == BIKE_BMX)
		return 85;
	return 80;
};

float(float kind) Bike_WheelRadius =
{
	if (kind == BIKE_CRUISER)
		return 13.2;
	if (kind == BIKE_BMX)
		return 10.2;
	return 13.6;
};

float(float kind) Bike_WheelHalfWidth =
{
	if (kind == BIKE_CRUISER)
		return 1.20;
	if (kind == BIKE_BMX)
		return 1.35;
	return 0.75;
};

float(float kind) Bike_AxleX =
{
	if (kind == BIKE_CRUISER)
		return 22.0;
	if (kind == BIKE_BMX)
		return 17.8;
	return 19.8;
};

void(entity b, float kind) Bike_SetRotatedBounds =
{
	local float hl, hw, ht, rad, sn, cs, acs, asn, hx, hy;
	local vector bmin, bmax;

	if (kind == BIKE_CRUISER)
	{
		hl = 35.5;
		hw = 13.5;
		ht = 43.0;
	}
	else if (kind == BIKE_BMX)
	{
		hl = 28.5;
		hw = 14.0;
		ht = 39.0;
	}
	else
	{
		hl = 34.0;
		hw = 11.5;
		ht = 39.5;
	}

	rad = b.angles_y * 0.0174533;
	sn = sin (rad);
	cs = cos (rad);
	acs = fabs (cs);
	asn = fabs (sn);
	hx = acs * hl + asn * hw;
	hy = asn * hl + acs * hw;

	bmin_x = 0 - hx;
	bmin_y = 0 - hy;
	bmin_z = 0;
	bmax_x = hx;
	bmax_y = hy;
	bmax_z = ht;
	setsize (b, bmin, bmax);
};

// ---------------------------------------------------------------- Detached Debris & Gyroscopic Rolling Tire Physics

void(entity e) Bike_RemoveDebris =
{
	if (bike_debris_count > 0)
		bike_debris_count = bike_debris_count - 1;
	remove (e);
};

void(entity e, float spd) Bike_TireSound =
{
	local float vol;

	vol = 0.45 + spd / 620;
	if (vol > 0.95)
		vol = 0.95;
	sound7 (e, CHAN_AUTO, "bikes/tire_bounce.wav", vol, ATTN_NORM, 92 + random () * 24);
};

void() Bike_DebrisTouch =
{
	local float spd, vol;

	if (other.takedamage)
		return;
	spd = vlen (self.velocity);
	if (self.classname == "bike_wheel")
	{
		if (time < self.mm_bouncetime + 0.18 || spd < 45)
			return;
		self.mm_bouncetime = time;
		self.mm_bounces = self.mm_bounces + 1;
		Bike_TireSound (self, spd);
		return;
	}
	if (time < self.mm_bouncetime + 0.20 || spd < 60)
		return;
	self.mm_bouncetime = time;
	self.mm_bounces = self.mm_bounces + 1;
	pointparticles (bike_fx_sparks, self.origin, '0 0 0', 1);
	vol = 0.42 + spd / 850;
	if (vol > 0.88)
		vol = 0.88;
	sound7 (self, CHAN_AUTO, "bikes/spoke_ping.wav", vol, ATTN_NORM, 84 + random () * 32);
};

void() Bike_DebrisThink =
{
	local float age, rem;

	self.nextthink = time + 0.08;
	if (time > self.mm_born + self.mm_life || pointcontents (self.origin) == CONTENT_SKY)
	{
		Bike_RemoveDebris (self);
		return;
	}
	age = time - self.mm_born;
	rem = self.mm_life - age;
	if (rem < 0.8)
		self.alpha = rem / 0.8;

	if (self.flags & FL_ONGROUND)
	{
		self.avelocity = self.avelocity * 0.45;
		if (vlen (self.avelocity) < 25)
			self.avelocity = '0 0 0';
	}
	if (age < 1.6 && random () < (0.35 - age * 0.18))
		pointparticles (bike_fx_sparks, self.origin, '0 0 0', 1);
};

entity(string mdl, vector org, vector vel, vector ang, float life) Bike_SpawnDebris =
{
	local entity d, e, oldest;

	if (bike_debris_count >= 24)
	{
		oldest = world;
		e = nextent (world);
		while (e != world)
		{
			if ((e.classname == "bike_debris" || e.classname == "bike_wheel") && (oldest == world || e.mm_born < oldest.mm_born))
				oldest = e;
			e = nextent (e);
		}
		if (oldest != world)
			Bike_RemoveDebris (oldest);
	}

	bike_debris_count = bike_debris_count + 1;
	d = spawn ();
	d.classname = "bike_debris";
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_TRIGGER;		// collides cleanly with world BSP without snagging players
	d.bouncefactor = 0.48;
	d.bouncestop = 0.08;
	d.alpha = 1;
	d.velocity = vel;
	d.angles = ang;
	d.avelocity_x = crandom () * 560;
	d.avelocity_y = crandom () * 560;
	d.avelocity_z = crandom () * 560;
	d.mm_born = time;
	d.mm_life = life;
	d.touch = Bike_DebrisTouch;
	d.think = Bike_DebrisThink;
	d.nextthink = time + 0.05;
	setmodel (d, mdl);
	setsize (d, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (d, org);
	return d;
};

/*
================
Bike_WheelThink

Detached bicycle wheels pop off their dropouts, bounce elastically on pneumatic rubber tread
while spinning through their 16 MD3 wheel frames, catch the pavement, roll along banked
gyroscopic curves (bouncing off walls & dropping off curbs), precess in an Euler's-disk
coin wobble as they slow down, and flop flat onto their sidewalls!
================
*/
void() Bike_WheelThink =
{
	local float age, rem, dt, step, f, rad, sn, cs, zh, spd_frac, target_lean, wob, ndot, wr;
	local vector fwd, next_xy, refl;

	dt = 0.04;
	self.nextthink = time + dt;
	if (time > self.mm_born + self.mm_life || pointcontents (self.origin) == CONTENT_SKY)
	{
		Bike_RemoveDebris (self);
		return;
	}
	age = time - self.mm_born;
	rem = self.mm_life - age;
	if (rem < 0.8)
		self.alpha = rem / 0.8;

	wr = self.veh_wheel_r;

	if (self.mm_state == 0)
	{
		// Airborne elastic bounce phase: spin spokes & tread via self.frame
		self.angles_x = 0;
		self.mm_dist = self.mm_dist + 14;
		f = self.mm_dist / self.veh_wheel_step;
		self.frame = floor (f - 16 * floor (f / 16));

		if (vlen (self.velocity) > 32)
			self.mm_roll_yaw = vectoyaw (self.velocity);
		self.angles_y = self.mm_roll_yaw;
		self.mm_lean = self.mm_lean + self.mm_side * 56 * dt;
		if (self.mm_lean > 42)
			self.mm_lean = 42;
		if (self.mm_lean < -42)
			self.mm_lean = -42;
		self.angles_z = self.mm_lean;

		if ((self.flags & FL_ONGROUND) || (self.mm_bounces >= 2 && fabs (self.velocity_z) < 90))
		{
			traceline (self.origin + '0 0 18', self.origin - '0 0 1' * (wr + 16), TRUE, self);
			if (trace_fraction < 1 && trace_plane_normal_z > 0.7)
			{
				self.mm_state = 1;
				self.movetype = MOVETYPE_NONE;
				self.avelocity = '0 0 0';
				self.mm_speed = vlen (self.velocity - '0 0 1' * self.velocity_z);
				if (self.mm_speed < 195)
					self.mm_speed = 195 + random () * 105;
				if (self.mm_speed > 420)
					self.mm_speed = 420;
				self.velocity = '0 0 0';
				self.mm_lean = self.mm_side * (16 + random () * 14);
				self.angles_x = 0;
				self.angles_y = self.mm_roll_yaw;
				self.angles_z = self.mm_lean;
			}
		}
		return;
	}

	// Ground banked gyroscopic rolling & coin-wobble phase
	if (self.mm_speed > 2)
	{
		step = self.mm_speed * dt;
		makevectors ('0 1 0' * self.mm_roll_yaw);
		fwd = v_forward;

		// Reflect off walls & curbs cleanly
		traceline (self.origin + '0 0 4', self.origin + '0 0 4' + fwd * (step + wr + 2), TRUE, self);
		if (trace_fraction < 1 && trace_plane_normal_z < 0.65)
		{
			ndot = fwd * trace_plane_normal;
			refl = fwd - trace_plane_normal * (2 * ndot);
			self.mm_roll_yaw = vectoyaw (refl);
			self.mm_speed = self.mm_speed * 0.78;
			Bike_TireSound (self, self.mm_speed);
			makevectors ('0 1 0' * self.mm_roll_yaw);
			fwd = v_forward;
			step = self.mm_speed * dt;
		}

		next_xy = self.origin + fwd * step;
		traceline (next_xy + '0 0 20', next_xy - '0 0 1' * (wr + 26), TRUE, self);
		if (trace_fraction == 1)
		{
			// Rolled off a curb or ledge: become airborne & bounce again!
			self.mm_state = 0;
			self.movetype = MOVETYPE_BOUNCE;
			self.flags = self.flags - (self.flags & FL_ONGROUND);
			self.mm_bounces = 1;
			self.velocity = fwd * self.mm_speed + '0 0 -28';
			return;
		}

		self.mm_dist = self.mm_dist + step;
		f = self.mm_dist / self.veh_wheel_step;
		self.frame = floor (f - 16 * floor (f / 16));

		self.mm_roll_yaw = Bike_NormYaw (self.mm_roll_yaw - self.mm_lean * 0.16);
		self.mm_speed = self.mm_speed * 0.974 - 1.9;
		if (self.mm_speed < 0)
			self.mm_speed = 0;

		spd_frac = self.mm_speed / 220;
		if (spd_frac > 1)
			spd_frac = 1;
		target_lean = 18 + (1 - spd_frac) * (1 - spd_frac) * 70;
		wob = sin (time * (14 + (1 - spd_frac) * 13));
		self.mm_lean = self.mm_side * target_lean + wob * 9 * spd_frac;
		if (self.mm_speed < 50)
			self.mm_roll_yaw = Bike_NormYaw (self.mm_roll_yaw - self.mm_side * 12);

		rad = fabs (self.mm_lean) * 0.0174533;
		sn = sin (rad);
		cs = cos (rad);
		zh = wr * cs + self.veh_wheel_hw * sn;

		self.angles_x = 0;
		self.angles_y = self.mm_roll_yaw;
		self.angles_z = self.mm_lean;
		setorigin (self, trace_endpos + '0 0 1' * zh);
	}
	else
	{
		// Settled flat onto sidewall
		self.mm_lean = self.mm_side * 88;
		self.angles_x = 0;
		self.angles_z = self.mm_lean;
	}
};

entity(float kind, vector org, vector vel, float side_sgn) Bike_SpawnWheel =
{
	local entity w;
	local float wr, whw;

	wr = Bike_WheelRadius (kind);
	whw = Bike_WheelHalfWidth (kind);

	w = Bike_SpawnDebris (Bike_WheelModel (kind), org, vel, '0 0 0', 10.5);
	w.classname = "bike_wheel";
	w.bouncefactor = 0.80;
	w.bouncestop = 0.08;
	w.avelocity = '0 0 0';
	w.veh_wheel_r = wr;
	w.veh_wheel_hw = whw;
	w.veh_wheel_step = (6.283185 * wr) / 16.0;
	w.mm_state = 0;
	w.mm_side = side_sgn;
	w.mm_lean = side_sgn * (12 + random () * 10);
	w.mm_roll_yaw = vectoyaw (vel);
	w.angles = '0 0 0';
	w.angles_y = w.mm_roll_yaw;
	w.think = Bike_WheelThink;
	w.nextthink = time + 0.04;
	return w;
};

// ---------------------------------------------------------------- Tire Popping, Pain & Full Crash

void(entity b, float is_front) Bike_PopSingleTire =
{
	local float kind, ax, wz, side_sgn;
	local vector fwd, lft, wpos, wvel;

	kind = b.bike_kind;
	ax = Bike_AxleX (kind);
	wz = Bike_WheelRadius (kind);

	makevectors ('0 1 0' * b.angles_y);
	fwd = v_forward;
	lft = '0 0 0' - v_right;
	if (random () < 0.5)
		side_sgn = 1;
	else
		side_sgn = -1;

	if (is_front)
	{
		wpos = b.origin + fwd * ax + '0 0 1' * (wz + 2);
		wvel = fwd * (215 + random () * 95) + lft * (side_sgn * (85 + random () * 75)) + '0 0 1' * (235 + random () * 85);
		Bike_SpawnWheel (kind, wpos, wvel, side_sgn);
		b.bike_state = BIKE_STATE_NO_FRONT;
		b.skin = 1;			// hides wheel_f via progs/bike_nodraw while frame & wheel_r remain visible!
		b.frame = 40;
	}
	else
	{
		wpos = b.origin - fwd * ax + '0 0 1' * (wz + 2);
		wvel = fwd * (0 - (215 + random () * 95)) + lft * (side_sgn * (85 + random () * 75)) + '0 0 1' * (235 + random () * 85);
		Bike_SpawnWheel (kind, wpos, wvel, side_sgn);
		b.bike_state = BIKE_STATE_NO_REAR;
		b.skin = 2;			// hides wheel_r via progs/bike_nodraw while frame & wheel_f remain visible!
		b.frame = 58;
	}

	pointparticles (bike_fx_sparks, wpos, '0 0 0', 2);
	sound7 (b, CHAN_VOICE, "bikes/tire_pop.wav", 0.92, ATTN_NORM, 94 + random () * 14);
	if (kind == BIKE_CRUISER || random () < 0.45)
		sound7 (b, CHAN_ITEM, "bikes/bell_ring.wav", 0.78, ATTN_NORM, 98 + random () * 8);

	b.bike_anim = 0;
	b.bike_flinch_end = time + 0.36;
	b.nextthink = time + 0.03;
};

void(entity b, entity attacker) Bike_PopTireFromHit =
{
	local vector fwd, rel;
	local float dot, pop_front;

	if (b.bike_state != BIKE_STATE_INTACT)
		return;

	makevectors ('0 1 0' * b.angles_y);
	fwd = v_forward;

	if (b.bike_hit_t >= time - 0.15)
	{
		rel = b.bike_hit_pos - b.origin;
		dot = rel * fwd;
		pop_front = (dot >= 0);
	}
	else if (attacker != world)
	{
		rel = attacker.origin - b.origin;
		dot = rel * fwd;
		pop_front = (dot >= 0);
	}
	else
		pop_front = (random () < 0.5);

	Bike_PopSingleTire (b, pop_front);
};

void(entity attacker, float take) Bike_Pain =
{
	local vector spk_pos;

	if (self.bike_state == BIKE_STATE_WRECK)
		return;

	if (self.bike_hit_t >= time - 0.10)
		spk_pos = self.bike_hit_pos;
	else
		spk_pos = self.origin + '0 0 20';

	if (time >= self.bike_pain_snd_t)
	{
		self.bike_pain_snd_t = time + 0.08;
		sound7 (self, CHAN_BODY, "bikes/spoke_ping.wav", 0.80, ATTN_NORM, 92 + random () * 22);
		if ((self.bike_kind == BIKE_CRUISER && random () < 0.65) || random () < 0.25)
			sound7 (self, CHAN_ITEM, "bikes/bell_ring.wav", 0.72, ATTN_NORM, 96 + random () * 12);
	}
	pointparticles (bike_fx_sparks, spk_pos, '0 0 0', 1);

	if (self.bike_state == BIKE_STATE_INTACT)
	{
		if (self.health <= self.max_health * 0.58)
		{
			Bike_PopTireFromHit (self, attacker);
			return;
		}
		// Intact HitSpin: both tires spin 360 deg + shimmy, handlebars whip, pedals kick!
		self.bike_flinch_end = time + 0.80;
		self.bike_anim = 0;
		self.frame = 12;
		self.nextthink = time + 0.02;
		return;
	}

	// Already missing one tire: play rapid 1-wheel flinch + wheel spin!
	self.bike_flinch_end = time + 0.36;
	self.bike_anim = 0;
	if (self.bike_state == BIKE_STATE_NO_FRONT)
		self.frame = 40;
	else
		self.frame = 58;
	self.nextthink = time + 0.02;
};

void() Bike_CrashNow =
{
	local float kind, prev_state, ax, wz;
	local vector fwd, lft, wpos, wvel, ppos, pvel;

	if (self.bike_state == BIKE_STATE_WRECK)
		return;

	kind = self.bike_kind;
	prev_state = self.bike_state;
	self.bike_state = BIKE_STATE_WRECK;
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;		// fallen bicycle frame never blocks player movement
	self.skin = 0;

	ax = Bike_AxleX (kind);
	wz = Bike_WheelRadius (kind);
	makevectors ('0 1 0' * self.angles_y);
	fwd = v_forward;
	lft = '0 0 0' - v_right;

	// Any still-attached tire(s) blast off and roll away!
	if (prev_state == BIKE_STATE_INTACT || prev_state == BIKE_STATE_NO_REAR)
	{
		wpos = self.origin + fwd * ax + '0 0 1' * (wz + 2);
		wvel = fwd * (230 + random () * 95) + lft * (95 + random () * 80) + '0 0 1' * (255 + random () * 90);
		Bike_SpawnWheel (kind, wpos, wvel, 1);
	}
	if (prev_state == BIKE_STATE_INTACT || prev_state == BIKE_STATE_NO_FRONT)
	{
		wpos = self.origin - fwd * ax + '0 0 1' * (wz + 2);
		wvel = fwd * (0 - (225 + random () * 95)) - lft * (95 + random () * 80) + '0 0 1' * (245 + random () * 90);
		Bike_SpawnWheel (kind, wpos, wvel, -1);
	}

	// Detached handlebars, saddle, and signature accessory fly outward & clatter!
	ppos = self.origin + fwd * 14 + '0 0 25';
	pvel = fwd * (110 + random () * 85) + lft * (crandom () * 140) + '0 0 1' * (240 + random () * 90);
	Bike_SpawnDebris (Bike_BarsModel (kind), ppos, pvel, self.angles, 8.5);

	ppos = self.origin - fwd * 10 + '0 0 30';
	pvel = fwd * (0 - (95 + random () * 80)) + lft * (crandom () * 140) + '0 0 1' * (225 + random () * 85);
	Bike_SpawnDebris (Bike_SaddleModel (kind), ppos, pvel, self.angles, 8.5);

	ppos = self.origin + fwd * 12 + '0 0 26';
	pvel = fwd * (80 + random () * 95) + lft * (crandom () * 165) + '0 0 1' * (250 + random () * 95);
	Bike_SpawnDebris (Bike_ExtraModel (kind), ppos, pvel, self.angles, 9.0);

	pointparticles (bike_fx_sparks, self.origin + '0 0 20', '0 0 0', 3);
	sound7 (self, CHAN_VOICE, "bikes/tire_pop.wav", 0.92, ATTN_NORM, 92 + random () * 14);
	sound7 (self, CHAN_BODY, "bikes/frame_crash.wav", 0.95, ATTN_NORM, 94 + random () * 12);
	if (kind == BIKE_CRUISER)
		sound7 (self, CHAN_ITEM, "bikes/bell_ring.wav", 0.85, ATTN_NORM, 104 + random () * 10);

	// Swap to 24-frame flipping/bouncing mangled wreck frame!
	setmodel (self, Bike_WreckModel (kind));
	setsize (self, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (self, self.origin);
	self.frame = 0;
	self.bike_anim = 0;
	self.think = Bike_Think;
	self.nextthink = time + 0.05;
};

void() Bike_Die =
{
	Bike_CrashNow ();
};

// ---------------------------------------------------------------- Respawn & Per-Tick Animation State Machine

void() Bike_TryRespawn =
{
	local entity e;

	e = findradius (self.bike_spawn_org, 64);
	while (e)
	{
		if ((e.flags & (FL_CLIENT | FL_MONSTER)) && e.health > 0)
		{
			self.nextthink = time + 2.0;
			return;
		}
		e = e.chain;
	}
	self.origin = self.bike_spawn_org;
	self.angles = self.bike_spawn_ang;
	Bike_InitEntity (self, self.bike_kind);
};

void() Bike_Think =
{
	local float f, rem, idx;

	// ---- STATE 3: Mangled Wreck Flip -> Crash -> Bounce -> Flat Side Rest (frames 0..23)
	if (self.bike_state == BIKE_STATE_WRECK)
	{
		if (self.frame < 23)
		{
			self.frame = self.frame + 1;
			if (self.frame == 10)
			{
				// Airborne frame slams sideways onto the asphalt!
				sound7 (self, CHAN_BODY, "bikes/frame_crash.wav", 0.85, ATTN_NORM, 86 + random () * 14);
				pointparticles (bike_fx_sparks, self.origin + '0 0 8', '0 0 0', 2);
			}
			else if (self.frame == 16)
			{
				// Secondary metallic clatter bounce
				sound7 (self, CHAN_AUTO, "bikes/spoke_ping.wav", 0.60, ATTN_NORM, 82 + random () * 18);
				pointparticles (bike_fx_sparks, self.origin + '0 0 4', '0 0 0', 1);
			}
			self.nextthink = time + 0.05;
			return;
		}

		if (!self.bike_temp && autocvar_bike_respawn > 0)
		{
			self.think = Bike_TryRespawn;
			self.nextthink = time + autocvar_bike_respawn;
			return;
		}
		self.nextthink = -1;
		return;
	}

	// Safety check in case th_pain was skipped by monster_skip_pain_animation_chance
	if (self.bike_state == BIKE_STATE_INTACT && self.health <= self.max_health * 0.58)
		Bike_PopTireFromHit (self, world);

	// ---- STATE 1: Front Tire Gone (skin 1, frames 28..39 continuous rear tire spin, 40..45 flinch)
	if (self.bike_state == BIKE_STATE_NO_FRONT)
	{
		self.nextthink = time + 0.05;
		if (time < self.bike_flinch_end)
		{
			rem = self.bike_flinch_end - time;
			idx = floor ((0.36 - rem) * 16.6);
			if (idx < 0)
				idx = 0;
			if (idx > 5)
				idx = 5;
			self.frame = 40 + idx;
			return;
		}
		self.bike_anim = self.bike_anim + 0.85;
		f = floor (self.bike_anim);
		self.frame = 28 + (f - 12 * floor (f / 12));
		return;
	}

	// ---- STATE 2: Rear Tire Gone (skin 2, frames 46..57 continuous front tire spin, 58..63 flinch)
	if (self.bike_state == BIKE_STATE_NO_REAR)
	{
		self.nextthink = time + 0.05;
		if (time < self.bike_flinch_end)
		{
			rem = self.bike_flinch_end - time;
			idx = floor ((0.36 - rem) * 16.6);
			if (idx < 0)
				idx = 0;
			if (idx > 5)
				idx = 5;
			self.frame = 58 + idx;
			return;
		}
		self.bike_anim = self.bike_anim + 0.85;
		f = floor (self.bike_anim);
		self.frame = 46 + (f - 12 * floor (f / 12));
		return;
	}

	// ---- STATE 0: Intact Parked Idle (frames 0..11) or HitSpin (frames 12..27 when shot!)
	if (time < self.bike_flinch_end)
	{
		self.nextthink = time + 0.05;
		rem = self.bike_flinch_end - time;
		idx = floor ((0.80 - rem) * 20.0);
		if (idx < 0)
			idx = 0;
		if (idx > 15)
			idx = 15;
		self.frame = 12 + idx;
		return;
	}

	// Throttle idle sway thinking when no human player is within 1000 units
	local entity hp;
	local float near_plr;
	near_plr = FALSE;
	hp = bm_player_head;
	while (hp)
	{
		if (hp.ishuman == 1 && vlen (hp.origin - self.origin) < 1000)
		{
			near_plr = TRUE;
			break;
		}
		hp = hp.bm_player_next;
	}
	if (!near_plr)
	{
		self.nextthink = time + 0.5;
		return;
	}

	self.nextthink = time + 0.08;
	self.bike_anim = self.bike_anim + 0.55;
	f = floor (self.bike_anim);
	self.frame = f - 12 * floor (f / 12);
};

// ---------------------------------------------------------------- Initialization & Map Spawn Entities

void(entity b, float kind) Bike_InitEntity =
{
	local vector org_top;

	Bikes_Precache ();
	b.bike_kind = kind;
	b.bike_state = BIKE_STATE_INTACT;
	b.skin = 0;
	b.frame = floor (random () * 12);
	b.bike_anim = b.frame;
	b.bike_flinch_end = 0;
	b.bike_pain_snd_t = 0;
	b.bike_hit_t = -99;

	b.movetype = MOVETYPE_NONE;
	b.solid = SOLID_BBOX;
	b.takedamage = DAMAGE_AIM;
	b.max_health = Bike_MaxHP (kind);
	b.health = b.max_health;
	b.th_pain = Bike_Pain;
	b.th_die = Bike_Die;

	setmodel (b, Bike_IntactModel (kind));
	Bike_SetRotatedBounds (b, kind);

	// Snap tire contact patch cleanly onto map floor (+0.4u above BSP plane)
	org_top = b.origin + '0 0 24';
	traceline (org_top, b.origin - '0 0 192', TRUE, b);
	if (trace_fraction < 1 && !trace_startsolid)
		setorigin (b, trace_endpos + '0 0 0.4');
	else
		setorigin (b, b.origin);

	b.bike_spawn_org = b.origin;
	b.bike_spawn_ang = b.angles;
	b.think = Bike_Think;
	b.nextthink = time + 0.05 + random () * 0.05;
};

void() misc_bike_cruiser =
{
	Bikes_Precache ();
	self.classname = "misc_bike_cruiser";
	Bike_InitEntity (self, BIKE_CRUISER);
};

void() misc_bike_bmx =
{
	Bikes_Precache ();
	self.classname = "misc_bike_bmx";
	Bike_InitEntity (self, BIKE_BMX);
};

void() misc_bike_road =
{
	Bikes_Precache ();
	self.classname = "misc_bike_road";
	Bike_InitEntity (self, BIKE_ROAD);
};

void() misc_bicycle =
{
	local float k;

	Bikes_Precache ();
	k = floor (self.cnt);
	if (k < 1 || k > 3)
	{
		k = floor (fabs (self.origin_x * 0.017 + self.origin_y * 0.023)) + 1;
		k = k - 3 * floor ((k - 1) / 3);
	}
	Bike_InitEntity (self, k);
};

// ---------------------------------------------------------------- Dynamic Spawn / Test Impulses (121..124)

void() Bike_PruneTempWrecks =
{
	local entity e, oldest;
	local float n;

	n = 0;
	oldest = world;
	e = nextent (world);
	while (e != world)
	{
		if (e.bike_temp)
		{
			n = n + 1;
			if (oldest == world || (e.bike_state == BIKE_STATE_WRECK && oldest.bike_state != BIKE_STATE_WRECK))
				oldest = e;
		}
		e = nextent (e);
	}
	if (n > 9 && oldest != world)
		remove (oldest);
};

entity(float kind, vector org, float yaw_deg) Bike_SpawnDynamic =
{
	local entity b;

	Bike_PruneTempWrecks ();
	b = spawn ();
	b.classname = "misc_bicycle";
	b.bike_temp = TRUE;
	b.angles = '0 0 0';
	b.angles_y = Bike_NormYaw (yaw_deg);
	setorigin (b, org);
	Bike_InitEntity (b, kind);
	return b;
};

void() Bicycles_Impulse =
{
	local vector fwd, rgt, base;
	local float yaw_side, k;

	if (self.impulse < 121 || self.impulse > 124 || !autocvar_sv_cheats)
		return;

	makevectors ('0 1 0' * self.v_angle_y);
	fwd = v_forward;
	rgt = v_right;
	yaw_side = Bike_NormYaw (self.v_angle_y + 68);

	if (self.impulse >= 121 && self.impulse <= 123)
	{
		k = self.impulse - 120;
		base = self.origin + fwd * 125 + '0 0 16';
		Bike_SpawnDynamic (k, base, yaw_side);
		if (k == BIKE_CRUISER)
			sprint (self, "Spawned Kern River 26\" Whitewall Cruiser\n");
		else if (k == BIKE_BMX)
			sprint (self, "Spawned #661 Oildale Street Stunt BMX\n");
		else
			sprint (self, "Spawned Kern Canyon Aero 700c Road Racer\n");
		self.impulse = 0;
		return;
	}

	if (self.impulse == 124)
	{
		base = self.origin + fwd * 150 + '0 0 16';
		Bike_SpawnDynamic (BIKE_CRUISER, base - rgt * 92, Bike_NormYaw (self.v_angle_y + 65));
		Bike_SpawnDynamic (BIKE_BMX,     base,            Bike_NormYaw (self.v_angle_y + 78));
		Bike_SpawnDynamic (BIKE_ROAD,    base + rgt * 92, Bike_NormYaw (self.v_angle_y + 105));
		sprint (self, "Spawned all 3 Bakersfield Bicycles (Cruiser, #661 BMX, Aero Road)!\n");
		self.impulse = 0;
	}
};
