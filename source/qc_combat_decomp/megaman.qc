#ifndef COMBATPLUS
#define COMBATPLUS
#endif
string() MM_PickVModel =
{
	local float mv, bit;
	local string mdl;

	if (!mm_precached_mask || time >= mm_variant_t)
	{
		mm_variant_cached = floor (cvar ("mm_variant"));
		mm_variant_t = time + 0.25;
	}
	mv = mm_variant_cached;
	if (mv == 1)
	{
		mdl = "progs/v_mm_cannon.md3";
		bit = 2;
	}
	else if (mv == 2)
	{
		mdl = "progs/v_mm_slingshot.md3";
		bit = 4;
	}
	else if (mv == 3)
	{
		mdl = "progs/v_mm_bow.md3";
		bit = 8;
	}
	else if (mv == 4)
	{
		mdl = "progs/v_mm_handthrow.md3";
		bit = 16;
	}
	else
	{
		mdl = "progs/v_megaman.md3";
		bit = 1;
	}
	if (!(mm_precached_mask & bit))
	{
		mm_precached_mask = mm_precached_mask | bit;
		precache_model (mdl);
	}
	return mdl;
};

void() MegaMan_Precache =
{
	precache_model ("progs/megaman.md3");
	// the default viewmodel always (mm_variant can go back to 0 mid-game: a late precache hitches every client), then the active variant
	precache_model ("progs/v_megaman.md3");
	mm_precached_mask = mm_precached_mask | 1;
	MM_PickVModel ();
	precache_sound ("grenade/boom_04_mega_fart.wav");
	precache_sound ("weapons/megamotor.wav");
	precache_sound ("weapons/megahorn.wav");
	precache_sound ("weapons/pkup.wav");
	precache_model ("progs/mm_wheel.md3");
	precache_model ("progs/mm_bar.md3");
	precache_model ("progs/mm_axle.md3");
	precache_model ("progs/mm_cap.md3");
	precache_model ("progs/mm_frag1.md3");
	precache_model ("progs/mm_frag2.md3");
	precache_model ("progs/mm_frag3.md3");
	precache_model ("progs/mm_frag4.md3");
	precache_model ("progs/mm_frag5.md3");
	precache_model ("progs/mm_frag6.md3");
	precache_model ("progs/mm_explode.md3");
	precache_sound ("weapons/tink1.wav");
	precache_sound ("weapons/ric1.wav");
	precache_sound ("weapons/ric2.wav");
	precache_sound ("weapons/ric3.wav");
#ifdef COMBATPLUS
	precache_sound ("megaman/mm_fire.wav");
	precache_sound ("megaman/mm_drive.wav");
	precache_sound ("megaman/tire1.wav");
	precache_sound ("megaman/tire2.wav");
	precache_sound ("megaman/tire3.wav");
	precache_sound ("megaman/boom01.wav");
	precache_sound ("megaman/boom02.wav");
	precache_sound ("megaman/boom03.wav");
	precache_sound ("megaman/boom04.wav");
	precache_sound ("megaman/boom05.wav");
	precache_sound ("megaman/boom06.wav");
	precache_sound ("megaman/boom07.wav");
	precache_sound ("megaman/boom08.wav");
	precache_sound ("megaman/boom09.wav");
	precache_sound ("megaman/boom10.wav");
	precache_sound ("megaman/boom11.wav");
	precache_sound ("megaman/boom12.wav");
	precache_sound ("megaman/boom13.wav");
	precache_sound ("megaman/boom14.wav");
	precache_sound ("megaman/boom15.wav");
	precache_sound ("megaman/boom16.wav");
	precache_sound ("megaman/boom17.wav");
	precache_sound ("megaman/boom18.wav");
	precache_sound ("megaman/boom19.wav");
	precache_sound ("megaman/boom20.wav");
	precache_sound ("megaman/boom21.wav");
	precache_sound ("megaman/boom22.wav");
	precache_sound ("megaman/boom23.wav");
	precache_sound ("megaman/boom24.wav");
	precache_sound ("megaman/boom25.wav");
	precache_sound ("megaman/boom26.wav");
	precache_sound ("megaman/boom27.wav");
#endif
};


float(float y) MM_NormYaw =
{
	return y - 360 * floor (y / 360);
};

// speed in percent; Combat+ scales it with its slow-motion
void(entity e, float chan, string samp, float vol, float speed) MM_Sound =
{
#ifdef COMBATPLUS
	sound7 (e, chan, samp, vol, ATTN_NORM, SNDSPD * speed / 100);
#else
	sound7 (e, chan, samp, vol, ATTN_NORM, speed, 0);
#endif
};

// same, with a gentler falloff so it carries across the map (the motor)
void(entity e, float chan, string samp, float vol, float speed, float atten) MM_SoundA =
{
#ifdef COMBATPLUS
	sound7 (e, chan, samp, vol, atten, SNDSPD * speed / 100);
#else
	sound7 (e, chan, samp, vol, atten, speed, 0);
#endif
};

#ifdef COMBATPLUS
// "megamayan" every throw
void() MegaMan_Larry =
{
	MM_Sound (self, CHAN_VOICE, "megaman/mm_fire.wav", 1, 100);
};

// a random clip when he blows up
string() MegaMan_BoomClip =
{
	local float r;

	r = floor (random () * 27);
	if (r < 1)
		return "megaman/boom01.wav";
	if (r < 2)
		return "megaman/boom02.wav";
	if (r < 3)
		return "megaman/boom03.wav";
	if (r < 4)
		return "megaman/boom04.wav";
	if (r < 5)
		return "megaman/boom05.wav";
	if (r < 6)
		return "megaman/boom06.wav";
	if (r < 7)
		return "megaman/boom07.wav";
	if (r < 8)
		return "megaman/boom08.wav";
	if (r < 9)
		return "megaman/boom09.wav";
	if (r < 10)
		return "megaman/boom10.wav";
	if (r < 11)
		return "megaman/boom11.wav";
	if (r < 12)
		return "megaman/boom12.wav";
	if (r < 13)
		return "megaman/boom13.wav";
	if (r < 14)
		return "megaman/boom14.wav";
	if (r < 15)
		return "megaman/boom15.wav";
	if (r < 16)
		return "megaman/boom16.wav";
	if (r < 17)
		return "megaman/boom17.wav";
	if (r < 18)
		return "megaman/boom18.wav";
	if (r < 19)
		return "megaman/boom19.wav";
	if (r < 20)
		return "megaman/boom20.wav";
	if (r < 21)
		return "megaman/boom21.wav";
	if (r < 22)
		return "megaman/boom22.wav";
	if (r < 23)
		return "megaman/boom23.wav";
	if (r < 24)
		return "megaman/boom24.wav";
	if (r < 25)
		return "megaman/boom25.wav";
	if (r < 26)
		return "megaman/boom26.wav";
	return "megaman/boom27.wav";
};
#endif

#ifndef COMBATPLUS
float() crandom;		// defined in weapons.qc, which comes after this file
#endif

// a few orange sparks flying off from org
void(vector org, float n) MM_Sparks =
{
	local vector d;
	local float i;

	i = 0;
	while (i < n)
	{
		d_x = crandom () * 9;
		d_y = crandom () * 9;
		d_z = 3 + random () * 9;
		particle (org, d, 100 + floor (random () * 8), 6);
		i = i + 1;
	}
};

// play a rubber tyre bounce / squeak
void(entity e, float v) MM_TireBounceSound =
{
	local float k, vol;

	vol = 0.55 + v / 700;
	if (vol > 1)
		vol = 1;
#ifdef COMBATPLUS
	k = floor (random () * 3);
	if (k == 0)
		MM_SoundA (e, CHAN_AUTO, "megaman/tire1.wav", vol, 88 + random () * 30, 1.1);
	else if (k == 1)
		MM_SoundA (e, CHAN_AUTO, "megaman/tire2.wav", vol, 88 + random () * 30, 1.1);
	else
		MM_SoundA (e, CHAN_AUTO, "megaman/tire3.wav", vol, 88 + random () * 30, 1.1);
#else
	MM_SoundA (e, CHAN_AUTO, "weapons/pkup.wav", vol * 0.6, 65 + random () * 20, 1.2);
#endif
};

// debris piece hits world geometry: rubber thuds, steel clanks and sparks
void() MM_DebrisTouch =
{
	local float v;

	if (other.takedamage)
		return;
	v = vlen (self.velocity);
	if (self.classname == "mmtire" || self.classname == "mmrubber")
	{
		if (time < self.mm_bouncetime + 0.25 || v < 55)
			return;
		self.mm_bouncetime = time;
		self.mm_bounces = self.mm_bounces + 1;
		MM_TireBounceSound (self, v);
		return;
	}
	if (time < self.mm_bouncetime + 0.25 || v < 80)
		return;
	self.mm_bouncetime = time;
	self.mm_bounces = self.mm_bounces + 1;
	MM_Sparks (self.origin, 3);
	if (random () < 0.5)
		MM_SoundA (self, CHAN_AUTO, "weapons/tink1.wav", 0.8, 85 + random () * 50, 1.35);
	else
		MM_SoundA (self, CHAN_AUTO, "weapons/ric2.wav", 0.48, 105 + random () * 45, 1.5);
};

// sparks keep spitting out of sheared metal wreckage until it settles and fades away
void() MM_DebrisThink =
{
	local float age, rem, p;

	self.nextthink = time + 0.08;
	if (time > self.mm_born + self.mm_life || pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	age = time - self.mm_born;
	rem = self.mm_life - age;
	if (rem < 0.5)
		self.alpha = rem / 0.5;

	if (self.flags & FL_ONGROUND)
		self.avelocity = '0 0 0';

	if (self.classname == "mmrubber")
		return;

	self.effects = 0;
	if (age < 2.6)
	{
		p = 0.65 - age * 0.20;
		if (p < 0.12)
			p = 0.12;
		if (random () < p)
			MM_Sparks (self.origin, 1 + floor (random () * 2));
	}
};

entity(string mdl, vector org, vector vel, float life) MM_Debris =
{
	local entity d;

	d = spawn ();
	d.classname = "mmdebris";
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_TRIGGER;		// bounces off the world, never blocks anyone
	d.bouncefactor = 0.46;
	d.bouncestop = 0.08;
	d.alpha = 1;
	d.velocity = vel;
	d.avelocity_x = crandom () * 650;
	d.avelocity_y = crandom () * 650;
	d.avelocity_z = crandom () * 650;
	d.angles_y = random () * 360;
	d.mm_born = time;
	d.mm_life = life;
	d.touch = MM_DebrisTouch;
	d.think = MM_DebrisThink;
	d.nextthink = time + 0.05;
	setmodel (d, mdl);
	setsize (d, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (d, org);
	return d;
};

/*
================
MM_WheelThink

Each blown-off wheel bounces first with elastic tire rebound while spinning via its
16 MD3 frames (avoiding pitch/roll gimbal lock), then catches traction on the floor
and rolls in a banked gyroscopic curve, reflects off walls, drops off ledges, enters
an Euler's-disk coin-wobble precession as it slows down, and flops flat onto its
rubber sidewall before fading out.
================
*/
void() MM_WheelThink =
{
	local float age, rem, dt, step, f, rad, sn, cs, zh, spd_frac, target_lean, wob, ndot;
	local vector fwd, next_xy, refl;

	dt = 0.04;
	self.nextthink = time + dt;
	if (time > self.mm_born + self.mm_life || pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	age = time - self.mm_born;
	rem = self.mm_life - age;
	if (rem < 0.5)
		self.alpha = rem / 0.5;

	if (self.mm_state == 0)
	{
		// Airborne elastic bounce phase: spin tread via self.frame, keep angles_x = 0
		self.angles_x = 0;
		self.mm_dist = self.mm_dist + 13;
		f = self.mm_dist / MM_WHEEL_FRAME;
		self.frame = floor (f - 16 * floor (f / 16));

		if (vlen (self.velocity) > 40)
			self.mm_roll_yaw = vectoyaw (self.velocity);
		self.angles_y = self.mm_roll_yaw;
		self.mm_lean = self.mm_lean + self.mm_side * 55 * dt;
		if (self.mm_lean > 42)
			self.mm_lean = 42;
		if (self.mm_lean < -42)
			self.mm_lean = -42;
		self.angles_z = self.mm_lean;

		// Check if wheel has settled onto floor after bouncing -> engage ground rolling!
		if ((self.flags & FL_ONGROUND) || (self.mm_bounces >= 2 && fabs (self.velocity_z) < 85))
		{
			traceline (self.origin + '0 0 16', self.origin - '0 0 24', TRUE, self);
			if (trace_fraction < 1 && trace_plane_normal_z > 0.7)
			{
				self.mm_state = 1;
				self.movetype = MOVETYPE_NONE;
				self.avelocity = '0 0 0';
				self.mm_speed = vlen (self.velocity - '0 0 1' * self.velocity_z);
				if (self.mm_speed < 190)
					self.mm_speed = 190 + random () * 85;
				if (self.mm_speed > 320)
					self.mm_speed = 320;
				self.velocity = '0 0 0';
				self.mm_lean = self.mm_side * (20 + random () * 14);
				self.angles_x = 0;
				self.angles_y = self.mm_roll_yaw;
				self.angles_z = self.mm_lean;
			}
		}
		return;
	}

	// Ground rolling & coin-wobble precession phase (MOVETYPE_NONE)
	if (self.mm_speed > 2)
	{
		step = self.mm_speed * dt;
		makevectors ('0 1 0' * self.mm_roll_yaw);
		fwd = v_forward;

		// Bounce off walls & pillars cleanly
		traceline (self.origin + '0 0 3', self.origin + '0 0 3' + fwd * (step + 13), TRUE, self);
		if (trace_fraction < 1 && trace_plane_normal_z < 0.65)
		{
			ndot = fwd * trace_plane_normal;
			refl = fwd - trace_plane_normal * (2 * ndot);
			self.mm_roll_yaw = vectoyaw (refl);
			self.mm_speed = self.mm_speed * 0.76;
			MM_TireBounceSound (self, self.mm_speed);
			makevectors ('0 1 0' * self.mm_roll_yaw);
			fwd = v_forward;
			step = self.mm_speed * dt;
		}

		next_xy = self.origin + fwd * step;
		traceline (next_xy + '0 0 18', next_xy - '0 0 34', TRUE, self);
		if (trace_fraction == 1)
		{
			// Rolled off a ledge or step: become airborne again and bounce down!
			self.mm_state = 0;
			self.movetype = MOVETYPE_BOUNCE;
			self.flags = self.flags - (self.flags & FL_ONGROUND);
			self.mm_bounces = 1;
			self.velocity = fwd * self.mm_speed + '0 0 -25';
			return;
		}

		// Advance wheel spin frame from distance rolled
		self.mm_dist = self.mm_dist + step;
		f = self.mm_dist / MM_WHEEL_FRAME;
		self.frame = floor (f - 16 * floor (f / 16));

		// Banked gyroscopic curvature: leaning wheel steers smoothly into an arc
		self.mm_roll_yaw = MM_NormYaw (self.mm_roll_yaw - self.mm_lean * 0.16);
		self.mm_speed = self.mm_speed * 0.968 - 2.3;
		if (self.mm_speed < 0)
			self.mm_speed = 0;

		spd_frac = self.mm_speed / 210;
		if (spd_frac > 1)
			spd_frac = 1;
		// Progressive lean from ~22 deg upright bank -> 88 deg flat coin precession
		target_lean = 22 + (1 - spd_frac) * (1 - spd_frac) * 66;
		wob = sin (time * (14 + (1 - spd_frac) * 12));
		self.mm_lean = self.mm_side * target_lean + wob * 8 * spd_frac;
		if (self.mm_speed < 48)
			self.mm_roll_yaw = MM_NormYaw (self.mm_roll_yaw - self.mm_side * 11);

		rad = fabs (self.mm_lean) * 0.0174533;
		sn = sin (rad);
		cs = cos (rad);
		zh = 12.0 * cs + 4.95 * sn;

		self.angles_x = 0;
		self.angles_y = self.mm_roll_yaw;
		self.angles_z = self.mm_lean;
		setorigin (self, trace_endpos + '0 0 1' * zh);
	}
	else
	{
		// Settled flat on rubber sidewall
		self.mm_lean = self.mm_side * 88;
		self.angles_x = 0;
		self.angles_z = self.mm_lean;
	}
};

entity(vector org, vector vel, float side_sgn) MM_SpawnWheel =
{
	local entity w;

	w = MM_Debris ("progs/mm_wheel.md3", org, vel, 6.5);
	w.classname = "mmtire";
	w.bouncefactor = 0.74;
	w.bouncestop = 0.08;
	w.avelocity = '0 0 0';
	w.mm_state = 0;
	w.mm_side = side_sgn;
	w.mm_lean = side_sgn * 16;
	w.mm_roll_yaw = vectoyaw (vel);
	w.angles = '0 0 0';
	w.angles_y = w.mm_roll_yaw;
	w.think = MM_WheelThink;
	w.nextthink = time + 0.04;
	return w;
};

/*
================
MM_BarThink

The central brushed stainless steel bar (progs/mm_bar.md3, cylinder axis along +X)
launches end-over-end clanging and sparking, settles horizontal onto the floor, and
rolls across the floor perpendicular to its axis before rocking gently to rest.
================
*/
void() MM_BarThink =
{
	local float age, rem, dt, step, wob;
	local vector rdir, next_xy;

	dt = 0.04;
	self.nextthink = time + dt;
	if (time > self.mm_born + self.mm_life || pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	age = time - self.mm_born;
	rem = self.mm_life - age;
	if (rem < 0.5)
		self.alpha = rem / 0.5;
	self.effects = 0;

	if (self.mm_state == 0)
	{
		// Airborne end-over-end tumble with occasional sparks
		if (age < 1.8 && random () < 0.28)
			MM_Sparks (self.origin, 2);

		if ((self.flags & FL_ONGROUND) || (self.mm_bounces >= 2 && fabs (self.velocity_z) < 70))
		{
			traceline (self.origin + '0 0 14', self.origin - '0 0 22', TRUE, self);
			if (trace_fraction < 1 && trace_plane_normal_z > 0.7)
			{
				self.mm_state = 1;
				self.movetype = MOVETYPE_NONE;
				self.avelocity = '0 0 0';
				self.angles_x = 0;
				makevectors ('0 1 0' * self.angles_y);
				if ((self.velocity * v_right) >= 0)
					self.mm_side = 1;
				else
					self.mm_side = -1;
				self.mm_speed = vlen (self.velocity - '0 0 1' * self.velocity_z);
				if (self.mm_speed < 145)
					self.mm_speed = 145 + random () * 65;
				if (self.mm_speed > 250)
					self.mm_speed = 250;
				self.velocity = '0 0 0';
				setorigin (self, trace_endpos + '0 0 2.1');
			}
		}
		return;
	}

	// Horizontal cylinder rolling perpendicular to bar axis (v_right * mm_side)
	if (self.mm_speed > 2)
	{
		step = self.mm_speed * dt;
		makevectors ('0 1 0' * self.angles_y);
		rdir = v_right * self.mm_side;

		traceline (self.origin + '0 0 2', self.origin + '0 0 2' + rdir * (step + 8), TRUE, self);
		if (trace_fraction < 1 && trace_plane_normal_z < 0.65)
		{
			self.mm_side = 0 - self.mm_side;
			self.mm_speed = self.mm_speed * 0.65;
			MM_Sparks (self.origin, 2);
			MM_SoundA (self, CHAN_AUTO, "weapons/tink1.wav", 0.65, 95 + random () * 35, 1.4);
			rdir = v_right * self.mm_side;
			step = self.mm_speed * dt;
		}

		next_xy = self.origin + rdir * step;
		traceline (next_xy + '0 0 14', next_xy - '0 0 28', TRUE, self);
		if (trace_fraction == 1)
		{
			// Rolled off a ledge: tumble down to the next floor
			self.mm_state = 0;
			self.movetype = MOVETYPE_BOUNCE;
			self.flags = self.flags - (self.flags & FL_ONGROUND);
			self.mm_bounces = 1;
			self.velocity = rdir * self.mm_speed + '0 0 -20';
			self.avelocity_x = crandom () * 280;
			self.avelocity_z = self.mm_side * 420;
			return;
		}

		// Spin around local +X cylinder axis (angles_z = roll, R = 2.0 -> 28.65 deg per unit)
		self.angles_x = 0;
		self.angles_z = MM_NormYaw (self.angles_z + step * 28.65 * self.mm_side);
		self.mm_speed = self.mm_speed * 0.952 - 2.1;
		if (self.mm_speed < 0)
			self.mm_speed = 0;
		setorigin (self, trace_endpos + '0 0 2.1');
	}
	else if (rem > 0.5)
	{
		// Gentle out-of-round settle rock on the floor
		wob = sin (time * 9.5);
		self.angles_z = self.angles_z + wob * 0.6;
	}
};

entity(vector org, vector vel, float yaw0) MM_SpawnBar =
{
	local entity b;

	b = MM_Debris ("progs/mm_bar.md3", org, vel, 6.2);
	b.classname = "mmbar";
	b.bouncefactor = 0.48;
	b.bouncestop = 0.08;
	b.angles = '35 0 0';
	b.angles_y = yaw0;
	b.avelocity_x = (380 + random () * 240) * (1 - 2 * floor (random () * 2));
	b.avelocity_y = crandom () * 220;
	b.avelocity_z = 420 + random () * 260;
	b.mm_state = 0;
	b.think = MM_BarThink;
	b.nextthink = time + 0.04;
	return b;
};

// 20-frame 3D core shatter burst (progs/mm_explode.md3) at detonation center
void() MM_BurstThink =
{
	self.frame = self.frame + 1;
	if (self.frame >= 20)
	{
		remove (self);
		return;
	}
	if (self.frame > 3)
		self.effects = 0;
	if (self.frame >= 14)
		self.alpha = (20 - self.frame) / 6;
	self.nextthink = time + 0.03;
};

/*
================
MM_Breakup

The contraption violently blows apart into 3D Voronoi shrapnel, snapped cross-axles,
blown rear cap, two intact pneumatic wheels that bounce and roll around in banked
gyroscopic curves, and the central stainless steel bar that clangs end-over-end and
rolls across the floor.
================
*/
void(float rocket) MM_Breakup =		// rocket: he is going off like a rocket, so no blue flash and no clank (the rocket sound and effect do that)
{
	local vector org, ax, v, dir;
	local entity f, d;
	local float i, m;
	local string fmdl;

	org = self.origin + '0 0 12';
	makevectors ('0 1 0' * self.angles_y);
	ax = v_right;		// the axle runs side to side

	// 1. 20-frame 3D core shatter burst right at detonation origin
	f = spawn ();
	f.classname = "mmburst";
	f.movetype = MOVETYPE_NONE;
	f.solid = SOLID_NOT;
	f.angles_y = self.angles_y;
	f.frame = 0;
	f.alpha = 1;
	setmodel (f, "progs/mm_explode.md3");
	setsize (f, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (f, org - '0 0 10');
	f.think = MM_BurstThink;
	f.nextthink = time + 0.03;

	// 2. Two intact wheels: blast off opposite ends of the axle, bounce, and roll around!
	v = ax * (185 + random () * 95) + v_forward * (95 + crandom () * 110) + '0 0 1' * (225 + random () * 110);
	MM_SpawnWheel (org + ax * 14, v, 1);
	v = ax * (-185 - random () * 95) + v_forward * (-85 + crandom () * 110) + '0 0 1' * (235 + random () * 115);
	MM_SpawnWheel (org - ax * 14, v, -1);

	// 3. Central brushed stainless steel bar: launches end-over-end, clangs & rolls across floor!
	v = v_forward * (70 + crandom () * 95) + ax * (crandom () * 95) + '0 0 1' * (265 + random () * 110);
	MM_SpawnBar (org + '0 0 2', v, self.angles_y + crandom () * 35);

	// 4. Snapped cross-axles & blown-off black Delrin rear cap
	v = ax * (110 + random () * 90) + '0 0 1' * (210 + random () * 110) + v_forward * crandom () * 85;
	MM_Debris ("progs/mm_axle.md3", org + ax * 5, v, 4.8);
	v = ax * (-110 - random () * 90) + '0 0 1' * (210 + random () * 110) + v_forward * crandom () * 85;
	MM_Debris ("progs/mm_axle.md3", org - ax * 5, v, 4.8);

	v = v_forward * (-190 - random () * 90) + ax * (crandom () * 70) + '0 0 1' * (195 + random () * 95);
	MM_Debris ("progs/mm_cap.md3", org - v_forward * 8 + '0 0 6', v, 4.6);

	// 5. 12 randomized 3D Voronoi shrapnel pieces (sheared steel, scorched collar, tire rubber, white rim shards)
	i = 0;
	while (i < 12)
	{
		m = i - 6 * floor (i / 6);
		if (m < 1)
			fmdl = "progs/mm_frag1.md3";
		else if (m < 2)
			fmdl = "progs/mm_frag2.md3";
		else if (m < 3)
			fmdl = "progs/mm_frag3.md3";
		else if (m < 4)
			fmdl = "progs/mm_frag4.md3";
		else if (m < 5)
			fmdl = "progs/mm_frag5.md3";
		else
			fmdl = "progs/mm_frag6.md3";

		dir_x = crandom ();
		dir_y = crandom ();
		dir_z = 0.35 + random () * 0.85;
		dir = normalize (dir);
		v = dir * (170 + random () * 210);
		v_z = 165 + random () * 210;
		d = MM_Debris (fmdl, org + dir * 4, v, 3.8 + random () * 1.6);
		if (m >= 2 && m < 4)
		{
			d.classname = "mmrubber";
			d.bouncefactor = 0.68;
		}
		i = i + 1;
	}

	MM_Sparks (org, 22);

	if (rocket)
		return;

	MM_SoundA (self, CHAN_WEAPON, "weapons/ric3.wav", 1, 80, 0.8);
	MM_SoundA (self, CHAN_ITEM, "weapons/tink1.wav", 1, 60, 0.8);
};

#ifdef COMBATPLUS
// the fire, bang, rumble, sparks and fire sprite of a rocket going off, no damage (T_MissileTouch's effects)
void(entity hit) MM_RocketBoom =
{
	if (pointcontents (self.origin) == CONTENT_SLIME)
		sendParticle ("slimesplash", self.origin + '0 0 12', VEC_ORIGIN, 1, 0);
	else if (autocvar_effects_classic_explosion == 1)
		sendParticle ("rocket_explo_classic", self.origin + '0 0 12', VEC_ORIGIN, 1, 0);
	else if (hit != world && autocvar_explosiondebris == 0)
		sendParticle ("rocket_explosion_nodebris", self.origin + '0 0 12', VEC_ORIGIN, 1, 0);
	else
		sendParticle ("rocket_explosion", self.origin + '0 0 12', VEC_ORIGIN, 1, 0);
	if (pointcontents (self.origin) == CONTENT_WATER || pointcontents (self.origin) == CONTENT_SLIME || pointcontents (self.origin) == CONTENT_LAVA)
	{
		MM_Sound (self, CHAN_WEAPON, "weapons/xpld_wat.wav", 1, 100);
		MM_Sound (self, CHAN_AUTO, "weapons/explodedist.wav", 0.5, 100);
	}
	else
	{
		MM_Sound (self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, 100);
		sound7 (self, CHAN_AUTO, "weapons/explodedist.wav", 0.3, 0.4, SNDSPD);
		sound (self, CHAN_BODY, "misc/null.wav", 1, ATTN_NORM);		// the motor stops with him
	}
	sparklers (1);
};
#endif

void(entity hit) MegaMan_Explode =
{
	dprint ("Mega Man exploded at ", vtos (self.origin), "\n");
	// he still had takedamage and health: his own splash found him, killed him and ran MegaMan_Dud (a second boom,
	// a second set of debris) before this went on
	self.takedamage = DAMAGE_NO;
	self.touch = SUB_Null;
	self.classname = "mmdead";		// the explosion sprite must not count as a live Mega Man (MegaMan_Launch sets the oldest off)

	// hit != world: it already took the direct damage, skip it in the splash
	mm_inflicting = TRUE;
#ifdef COMBATPLUS
	T_RadiusDamage (self, self.owner, 105, hit);
	mm_inflicting = FALSE;
	MM_RocketBoom (hit);
#else
	T_RadiusDamage (self, self.owner, 120, hit);
	mm_inflicting = FALSE;
#endif

	MM_Breakup (TRUE);
#ifdef COMBATPLUS
	BecomeExplosion ();
#else
	remove (self);
#endif
};

// no enemy to be had, wedged, his time is up, or shot down: he goes up in the same fire as a rocket, but harmlessly
// (no splash damage), and the parts fly.
void() MegaMan_Dud =
{
	dprint ("Mega Man fell apart at ", vtos (self.origin), "\n");
	self.takedamage = DAMAGE_NO;
	self.touch = SUB_Null;
	self.classname = "mmdead";		// see MegaMan_Explode
#ifdef COMBATPLUS
	MM_Sound (self, CHAN_VOICE, MegaMan_BoomClip (), 1, 100);
	MM_RocketBoom (world);
	MM_Breakup (TRUE);
	BecomeExplosion ();
#else
	MM_Breakup (FALSE);
	remove (self);
#endif
};

void() MegaMan_SpinWheels =
{
	local float f;

	f = self.mm_dist / MM_WHEEL_FRAME;
	self.frame = floor (f - 16 * floor (f / 16));
};

// somebody it should go for (and may go off on): another player in deathmatch (never the owner, never a teammate
// under teamplay, never an invisible Rob Dob pilot), a monster otherwise. self = the Mega Man.
float(entity e) MM_IsEnemy =
{
	if (!e || e == self.owner || e.health <= 0 || !e.takedamage)
		return FALSE;
	if (deathmatch)
	{
		if (e.classname != "player")
			return FALSE;
		if (e.flags & FL_NOTARGET)
			return FALSE;
	}
	else if (!(e.flags & FL_MONSTER))
		return FALSE;
	if (teamplay && e.team > 0 && e.team == self.owner.team)
		return FALSE;
	return TRUE;
};

/*
================
MegaMan_FindTarget

Nearest enemy within sight and range. In deathmatch that means other players
(never the owner, never a teammate under teamplay). Outside deathmatch it
chases monsters, so the gun is still fun in single player and coop.
================
*/
entity() MegaMan_FindTarget =
{
	local entity e, sight, scent;
	local float d, dd, sightd, scentd;

#ifdef COMBATPLUS
	if (self.ud_hunt && self.ud_hunt.health > 0)
	{
		traceline (self.origin + '0 0 12', self.ud_hunt.origin, TRUE, self);
		mm_los = (trace_fraction == 1);
		return self.ud_hunt;		// Blue Shell: only the leader
	}
#endif
	sight = world;
	scent = world;
	sightd = MM_SEEK_RANGE * 2;
	scentd = MM_SEEK_RANGE * 2;

	// in deathmatch only players count (MM_IsEnemy): walk the frame's player list instead of a 4000-unit findradius,
	// which took in nearly every edict on the map (debris, gibs, goo) 20 times a second per Mega Man
	if (deathmatch)
		e = bm_player_head;
	else
		e = findradius (self.origin, MM_SEEK_RANGE);
	while (e)
	{
		d = vlen (e.origin - self.origin);
		if (d <= MM_SEEK_RANGE && MM_IsEnemy (e))
		{
			dd = d;
			if (e == self.mm_target)
				dd = d * 0.7;		// stick with the one it is after rather than flip between two
			if (dd < scentd)
			{
				scentd = dd;
				scent = e;
			}
			if (dd < sightd)
			{
				// walls and doors block the view; other entities don't
				traceline (self.origin + '0 0 12', e.origin, TRUE, self);
				if (trace_fraction == 1)
				{
					sightd = dd;
					sight = e;
				}
			}
		}
		if (deathmatch)
			e = e.bm_player_next;
		else
			e = e.chain;
	}

	// somebody in plain sight is the one to run down; otherwise it still heads for the nearest enemy
	// anywhere on the map, steering round whatever is in the way
	if (sight)
	{
		mm_los = TRUE;
		return sight;
	}
	mm_los = FALSE;
	return scent;
};

/*
================
MM_Clear

How far (0..1 of dist) Mega Man could drive along yaw before its body hits a
wall: sweeps its own collision box, lifted above step height so stairs don't count.
================
*/
float(float yaw, float dist) MM_Clear =
{
	local vector org;

	makevectors ('0 1 0' * yaw);
	org = self.origin + '0 0 18';
	tracebox (org, self.mins, self.maxs, org + v_forward * dist, TRUE, self);
	if (trace_startsolid)
	{
		// low ceiling: sweep from just off the floor instead
		org = self.origin + '0 0 2';
		tracebox (org, self.mins, self.maxs, org + v_forward * dist, TRUE, self);
	}
	return trace_fraction;
};

/*
================
MM_OpenYaw

The direction closest to yaw that is clear for dist units, searching outward
both ways (preferred side first). Falls back to the most open direction.
================
*/
float(float yaw, float dist) MM_OpenYaw =
{
	local float off, f, best, bestf;

	if (!self.mm_side)
		self.mm_side = 1;

	best = yaw;
	bestf = MM_Clear (yaw, dist);
	if (bestf == 1)
		return yaw;

	off = 20;
	while (off <= 180)
	{
		f = MM_Clear (yaw + off * self.mm_side, dist);
		if (f == 1)
			return MM_NormYaw (yaw + off * self.mm_side);
		if (f > bestf)
		{
			bestf = f;
			best = yaw + off * self.mm_side;
		}

		f = MM_Clear (yaw - off * self.mm_side, dist);
		if (f == 1)
		{
			self.mm_side = 0 - self.mm_side;	// stick to this side next time
			return MM_NormYaw (yaw + off * self.mm_side);
		}
		if (f > bestf)
		{
			bestf = f;
			best = yaw - off * self.mm_side;
		}
		off = off + 20;
	}
	return MM_NormYaw (best);
};

void(float horn) MegaMan_TakeOff =
{
	self.mm_state = 0;
	self.movetype = MOVETYPE_TOSS;
	self.flags = self.flags - (self.flags & FL_ONGROUND);
	setorigin (self, self.origin + '0 0 2');
	if (horn)
		MM_Sound (self, CHAN_VOICE, "weapons/megahorn.wav", 1, horn);
};

// just spotted someone: a little hop with a blast of the horn
void() MegaMan_Hop =
{
	makevectors ('0 1 0' * self.angles_y);
	self.velocity = v_forward * 60 + '0 0 270';
	self.angles_x = -20;
	self.mm_leap_t = time + 1;
	MegaMan_TakeOff (100);
	dprint ("Mega Man spotted ", self.mm_target.netname, "\n");
};

// jump on the target, aiming a little ahead of where it is going
void() MegaMan_Leap =
{
	local vector aim, dir, vel;
	local float dz, dist, t;

	aim = self.mm_target.origin + '0 0 8' + self.mm_target.velocity * 0.2;
	dir = aim - self.origin;
	dz = dir_z;
	dir_z = 0;
	dist = vlen (dir);
	t = dist / 520;
	if (t < 0.3)
		t = 0.3;
	vel = normalize (dir) * (dist / t);
	vel_z = dz / t + 0.5 * cvar ("sv_gravity") * t;
	if (vel_z < 220)
		vel_z = 220;
	if (vel_z > 650)
		vel_z = 650;

	self.velocity = vel;
	self.angles_y = vectoyaw (dir);
	self.angles_x = -35;		// nose up, wheels first
	self.mm_leap_t = time + 1.2;
	MegaMan_TakeOff (120);
	dprint ("Mega Man leaps at ", self.mm_target.netname, "\n");
};

/*
================
MegaMan_Blocked

The drive failed. Someone in the way: that is a hit. A drop in front: roll off
the edge. A step or a lip: hop up onto it. A wall: costs a bounce, then it
turns to the most open direction.
================
*/
void() MegaMan_Blocked =
{
	local vector fwd, org;

	makevectors ('0 1 0' * self.angles_y);
	fwd = v_forward;

	traceline (self.origin + '0 0 8', self.origin + '0 0 8' + fwd * 40, FALSE, self);
	if (trace_ent != world && MM_IsEnemy (trace_ent))
	{
		MegaMan_Explode (world);	// ran into an enemy: that's a hit
		return;
	}

	self.mm_freeticks = 0;
	org = self.origin + '0 0 18';
	tracebox (org, self.mins, self.maxs, org + fwd * 24, TRUE, self);
	if (trace_fraction == 1 && !trace_startsolid && self.mm_hops < 3)
	{
		self.mm_hops = self.mm_hops + 1;
		traceline (self.origin + fwd * 28 + '0 0 4', self.origin + fwd * 28 - '0 0 36', TRUE, self);
		if (trace_fraction == 1)
			self.velocity = fwd * 200;					// nothing under the front wheels: drive off the edge
		else
			self.velocity = fwd * 170 + '0 0 230';		// a step it can't roll up: hop
		MegaMan_TakeOff (0);
		return;
	}

	// repeated blocks within a moment (corners) only cost one bounce
	if (time > self.mm_bouncetime + 0.5)
	{
		if (self.mm_bounces >= MM_MAX_BOUNCES)
		{
			MegaMan_Dud ();
			return;
		}
		self.mm_bounces = self.mm_bounces + 1;
		self.mm_bouncetime = time;
		MM_Sound (self, CHAN_ITEM, "weapons/ric1.wav", 1, 100);
	}

	self.angles_y = MM_OpenYaw (self.angles_y + 30 * self.mm_side, MM_LOOK * 0.5);
	self.mm_heading = self.angles_y;
	dprint ("Mega Man bumped ", ftos (self.mm_bounces), "/", ftos (MM_MAX_BOUNCES), " yaw ", ftos (self.angles_y), "\n");
};

#ifdef COMBATPLUS
void() MegaMan_BlueShellBoom =
{
	local entity e;
	local vector kick;

	self.takedamage = DAMAGE_NO;
	self.touch = SUB_Null;
	self.classname = "mmdead";
	self.scale = 1;

	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_TAREXPLOSION);
	WriteCoord (MSG_BROADCAST, self.origin_x);
	WriteCoord (MSG_BROADCAST, self.origin_y);
	WriteCoord (MSG_BROADCAST, self.origin_z);

	mm_inflicting = TRUE;
	T_RadiusDamage (self, self.owner, 170, world);
	mm_inflicting = FALSE;
	// Massive comic upward sky-launch on anyone caught in the Blue Shell shockwave
	e = findradius (self.origin, 220);
	while (e)
	{
		if (e.health > 0 && (e.movetype == MOVETYPE_WALK || e.movetype == MOVETYPE_STEP))
		{
			kick = e.origin - self.origin;
			kick_z = 0;
			if (vlen (kick) < 1)
				kick = '1 0 0';
			kick = normalize (kick);
			e.flags = e.flags - (e.flags & FL_ONGROUND);
			e.velocity = e.velocity + kick * 420 + '0 0 650';
		}
		e = e.chain;
	}
	MM_RocketBoom (world);
	MM_Breakup (TRUE);
	BecomeExplosion ();
};

void() MegaMan_BlueShellThink =
{
	local vector goal, diff;
	local float d, sw;

	self.nextthink = time + 0.05;
	if (!self.ud_hunt || self.ud_hunt.classname != "player" || self.ud_hunt.health <= 0)
		self.ud_hunt = Underdog_Leader (self.owner);
	if (!self.ud_hunt || self.ud_hunt.health <= 0 || time - self.mm_born > MM_LIFETIME)
	{
		self.scale = 1;
		MegaMan_Dud ();
		return;
	}

	self.mm_dist = self.mm_dist + 36;
	MegaMan_SpinWheels ();
	particle (self.origin + '0 0 10', '0 0 12', 41, 6);

	if (time >= self.mm_motor)
	{
		MM_SoundA (self, CHAN_BODY, "megaman/mm_drive.wav", 0.45, 145, 1);
		self.mm_motor = time + MM_DRIVE_LEN * 100 / 145;
	}

	if (self.ud_shell_stage == 1)
	{
		goal = self.ud_hunt.origin + '0 0 92';
		diff = goal - self.origin;
		d = vlen (diff);
		sw = sin (time * 18);
		self.angles_y = vectoyaw (diff);
		self.angles_x = 16;
		self.angles_z = sw * 14;
		if (d > 1 && time >= self.skypad_steer_t)
			self.velocity = normalize (diff) * 960;
		if (d < 105 || time >= self.ud_shell_t)
		{
			self.ud_shell_stage = 2;
			self.ud_shell_t = time + 0.90;
			self.mm_lastorg = self.ud_hunt.origin;
			self.velocity = '0 0 0';
			setorigin (self, self.ud_hunt.origin + '0 0 88');
			MM_Sound (self, CHAN_VOICE, "weapons/megahorn.wav", 1, 135);
		}
		return;
	}

	if (self.ud_shell_stage == 2)
	{
		if (self.ud_shell_t - time > 0.45)
			self.mm_lastorg = self.ud_hunt.origin;
		self.velocity = '0 0 0';
		setorigin (self, self.mm_lastorg + '0 0 88');
		self.angles_y = MM_NormYaw (self.angles_y + 72);
		self.angles_x = 35;
		self.angles_z = 0;
		if (time >= self.ud_shell_t)
		{
			self.ud_shell_stage = 3;
			self.ud_shell_t = time + 0.30;
			self.angles_x = 85;
			self.velocity = '0 0 -1550';
			MM_Sound (self, CHAN_VOICE, MegaMan_BoomClip (), 1, 115);
		}
		return;
	}

	if (self.origin_z <= self.mm_lastorg_z + 26 || vlen (self.origin - self.ud_hunt.origin) < 48 || time >= self.ud_shell_t)
		MegaMan_BlueShellBoom ();
};
#endif

void() MegaMan_Think =
{
	local float ok, d, look, desired, pitch;
	local vector oldorg, moved;
	local entity targ;

#ifdef COMBATPLUS
	if (self.ud_shell_stage > 0)
	{
		MegaMan_BlueShellThink ();
		return;
	}
#endif
	self.nextthink = time + 0.05;

	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}

	if (time - self.mm_born > MM_LIFETIME)		// (scratch1 is FrikBot's bot-count mask, not a test knob)
	{
		MegaMan_Dud ();
		return;
	}

	if (self.mm_state == 0)
	{
		// in the air; wheels spin while it flies
		self.mm_dist = self.mm_dist + 10;
		MegaMan_SpinWheels ();

		// wedged in a wall (fired point blank): just blow up there, like a rocket would
		if (self.origin == self.mm_lastorg && !(self.flags & FL_ONGROUND))
			self.mm_stuck = self.mm_stuck + 1;
		else
			self.mm_stuck = 0;
		self.mm_lastorg = self.origin;
		if (self.mm_stuck >= 3)
		{
			MegaMan_Dud ();
			return;
		}

		if (self.flags & FL_ONGROUND)
		{
			// landed on its wheels: stand upright and drive on the way it was going
			self.mm_state = 1;
			self.mm_heading = self.angles_y;
			self.movetype = MOVETYPE_STEP;
			self.velocity = '0 0 0';
			self.angles_x = 0;
			self.angles_z = 0;
			self.avelocity = '0 0 0';
			MM_Sound (self, CHAN_ITEM, "grenade/boom_04_mega_fart.wav", 1, 100);
		}
		return;
	}

	targ = MegaMan_FindTarget ();

	if (self.mm_state == 2)
	{
		// crouched, about to spring
		if (!targ || !mm_los)
		{
			self.mm_state = 1;
			self.angles_x = 0;
			return;
		}
		self.mm_target = targ;
		self.angles_y = vectoyaw (targ.origin - self.origin);
		if (time >= self.mm_crouch_t)
			MegaMan_Leap ();
		return;
	}

	// driving
	self.angles_x = 0;
	self.angles_z = 0;
	pitch = 100;
	look = MM_LOOK;

	if (targ)
	{
		if (targ != self.mm_target)
		{
			self.mm_target = targ;
			if (mm_los && time >= self.mm_leap_t)
			{
				MegaMan_Hop ();
				return;
			}
		}
		d = vlen (targ.origin - self.origin);
		if (mm_los && d < MM_PROXIMITY)
		{
			MegaMan_Explode (world);	// close enough, no point driving past
			return;
		}
		if (mm_los && d < MM_LEAP_RANGE && time >= self.mm_leap_t && fabs (targ.origin_z - self.origin_z) < 180)
		{
			// crouch for a moment, then spring at them
			self.mm_state = 2;
			self.mm_crouch_t = time + 0.25;
			self.angles_x = 12;
			return;
		}
		desired = vectoyaw (targ.origin - self.origin);
		if (d - 24 < look)
			look = d - 24;
		// the motor revs up as it closes in
		pitch = 100 + (1 - d / MM_SEEK_RANGE) * 40;
	}
	else
	{
		self.mm_target = world;
		desired = self.mm_heading;
	}

	// keep to the clear way round walls; once round a corner, carry on that way
	self.yaw_speed = MM_TURN_CRUISE;
	if (targ)
		self.yaw_speed = MM_TURN_CHASE;
	if (look > 16 && MM_Clear (desired, look) < 1)
	{
		// the search for a way round costs up to 18 more MM_Clear checks (1-2 traceboxes each): chasing someone round a
		// wall did it every tick. Keep the way found while it stays clear, for up to 0.25 s
		if (time < self.mm_detour_t && MM_Clear (self.mm_detour_yaw, look) >= 1)
			desired = self.mm_detour_yaw;
		else
		{
			desired = MM_OpenYaw (desired, look);
			self.mm_detour_yaw = desired;
			self.mm_detour_t = time + 0.25;
		}
		self.yaw_speed = MM_TURN_AVOID;
		if (!targ)
			self.mm_heading = desired;
	}
	self.ideal_yaw = MM_NormYaw (desired);
	ChangeYaw ();

	if (time >= self.mm_motor)
	{
#ifdef COMBATPLUS
		MM_SoundA (self, CHAN_BODY, "megaman/mm_drive.wav", 0.35, pitch, 1);		// the loudest clip in the game, and it loops
		self.mm_motor = time + MM_DRIVE_LEN * 100 / pitch;	// back to back, no pause
#else
		MM_SoundA (self, CHAN_BODY, "weapons/megamotor.wav", 1, pitch, 0.45);
		self.mm_motor = time + 0.5;
#endif
	}

	oldorg = self.origin;
	ok = walkmove (self.angles_y, MM_DRIVE_STEP);
	if (ok)
	{
		// walkmove can report success while it is wedged against a wall or ledge
		moved = self.origin - oldorg;
		moved_z = 0;
		if (vlen (moved) < MM_DRIVE_STEP * 0.5)
			ok = FALSE;
	}
	if (!ok)
	{
		MegaMan_Blocked ();
		return;
	}
	self.mm_dist = self.mm_dist + MM_DRIVE_STEP;
	MegaMan_SpinWheels ();
	self.mm_freeticks = self.mm_freeticks + 1;
	if (self.mm_freeticks > 6)
		self.mm_hops = 0;
};

void() MegaMan_Touch =
{
	local float damg;

	if (other == self.owner)
		return;
	if (other != world && other.pc_kind > PC_KIND_NONE)
	{
		PC_HandlePair (self, other);
		return;
	}

	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}

	// only living things set it off on touch; walls are handled by the drive
	// (walkmove failing) or just stop it while it is in the air
	if (MM_IsEnemy (other))
	{
		damg = 95 + random()*20;
		if (other.classname == "monster_shambler")
			damg = damg * 0.5;
		mm_inflicting = TRUE;
		T_Damage (other, self, self.owner, damg);
		mm_inflicting = FALSE;
		MegaMan_Explode (other);
	}
};

// shot down on the way: deferred to next tick so T_RadiusDamage never clobbers a caller's findradius .chain!
void() MegaMan_ShotPop =
{
	mm_inflicting = TRUE;
	T_RadiusDamage (self, self.owner, 40, world);
	mm_inflicting = FALSE;
	MegaMan_Dud ();
};

void() MegaMan_Shot =
{
	PC_NoteKilled (self, damage_attacker);
	self.takedamage = DAMAGE_NO;
	self.touch = SUB_Null;
	self.think = MegaMan_ShotPop;
	self.nextthink = time;
};

// Mega Man leaves the hand
float	MM_MAX_LIVE = 2;

void() MegaMan_Launch =
{
	local	entity mm, old;
	local	vector dir;
	local	float live;

	// at most MM_MAX_LIVE out per player: throwing another sets the oldest off
	live = 0;
	old = world;
	mm = find (world, classname, "megaman");
	while (mm)
	{
		if (mm.owner == self
#ifdef COMBATPLUS
			&& mm.ud_shell_stage <= 0
#endif
		)
		{
			live = live + 1;
			if (!old || mm.mm_born < old.mm_born)
				old = mm;
		}
		mm = find (mm, classname, "megaman");
	}
	if (live >= MM_MAX_LIVE)
	{
		// not MegaMan_Shot: that credits damage_attacker (whoever last hurt anything) with a SKEET SHOT reward
		old.takedamage = DAMAGE_NO;
		old.touch = SUB_Null;
		old.think = MegaMan_ShotPop;
		old.nextthink = time;
	}

	self.mm_ammo = self.mm_ammo - 1;
	if (self.weapon == IT_MEGAMAN)
		self.currentammo = self.mm_ammo;
	if (self.mm_ammo < MM_MAX_AMMO && self.mm_regen_t < time)
		self.mm_regen_t = time + MM_REGEN_TIME;

	MM_Sound (self, CHAN_WEAPON, "weapons/grenade.wav", 1, 100);
#ifdef COMBATPLUS
	self.bm_lastshot = time;	// BM_Frame can't see the magazine drop (it reads mm_ammo after the fact), so the idle top-up started at once and hid the gun mid-shot
	MegaMan_Larry ();
#endif

	self.punchangle_x = -2;

	makevectors (self.v_angle);

	mm = spawn ();
	mm.owner = self;
	mm.classname = "megaman";
	mm.movetype = MOVETYPE_TOSS;		// lands and stops on the first floor it touches
	mm.solid = SOLID_BBOX;
	mm.mm_state = 0;
	mm.mm_born = time;
	mm.mm_leap_t = time + 0.6;
	mm.mm_side = 1;
	if (random () < 0.5)
		mm.mm_side = -1;

	// out of the hand: forward and a little up
	dir = aim (self, 1000);
	mm.velocity = dir * 620 + '0 0 120';
	mm.angles = '0 0 0';
	mm.angles_y = self.v_angle_y;

	mm.effects = 0;				// normal scene lighting (no intense blue glow)
	mm.takedamage = DAMAGE_YES;		// you can shoot him down
	mm.health = MM_HEALTH;
	mm.th_die = MegaMan_Shot;
	mm.touch = MegaMan_Touch;
	mm.think = MegaMan_Think;
	mm.nextthink = time + 0.05;

	setmodel (mm, "progs/megaman.md3");
	setsize (mm, '-16 -16 0', '16 16 24');

	// start in front of the player, but not inside a wall
	traceline (self.origin + '0 0 12', self.origin + '0 0 8' + v_forward * 38 + v_right * 8, TRUE, self);
	setorigin (mm, trace_endpos);
	PC_Register (mm, PC_KIND_HEAVY, 28);
#ifdef COMBATPLUS
	Underdog_BlueShell (mm);
#endif
};

// fire pressed with the Mega Man gun out (called from W_Attack)
void() MegaMan_Attack =
{
	self.mm_inspect_t = 0;		// immediately cancel any CoD weapon inspect on fire!
	self.mm_next_inspect = time + 7 + random () * 6;
	if (self.mm_ammo < 1)
	{
		// still recharging: click once per trigger press, never repeat while held
		if (!self.mm_dry_held)
		{
			self.mm_dry_held = TRUE;
			MM_Sound (self, CHAN_WEAPON, "weapons/pkup.wav", 0.4, 100);
		}
		self.attack_finished = time + 0.3;
		return;
	}
	self.mm_dry_held = FALSE;
#ifdef COMBATPLUS
	player_throw1 ();
#else
	player_mm1 ();
#endif
	self.mm_fire_t = time;
	self.mm_launch_t = time + 0.15;
	self.mm_pending = TRUE;
	self.attack_finished = time + 1.2;
	MM_Sound (self, CHAN_AUTO, "weapons/ax1.wav", 0.8, 100);
};

void(float kind) MegaMan_StartInspect =
{
	self.mm_inspect_t = time;
	self.mm_inspect_kind = kind;
	self.mm_glint_ding = FALSE;
	self.mm_next_inspect = time + 9 + random () * 7;
};

// impulse MM_IMPULSE
void() MegaMan_Select =
{
	local float mv;

	self.impulse = 0;
	if (!(self.items & IT_MEGAMAN))
	{
		sprint (self, "no weapon.\n");
		return;
	}
	mv = floor (cvar ("mm_variant"));
	if (self.weapon == IT_MEGAMAN && mv >= 1 && mv <= 4 && self.mm_ammo >= 1 && (!self.mm_fire_t || time - self.mm_fire_t >= 1.2))
	{
		// Pressing impulse 14 while already holding a 4-arsenal variant triggers CoD Weapon Inspect on demand!
		if (self.mm_inspect_kind == 2)
			MegaMan_StartInspect (1);
		else
			MegaMan_StartInspect (2);
		return;
	}
#ifdef COMBATPLUS
	if (self.has_fired == 1)
		return;
	self.idletimer = 1;		// weapon raise animation
	self.switchtimer = -5;
#endif
	self.mm_inspect_t = 0;
	self.mm_next_inspect = time + 4.5 + random () * 4.5;
	self.weapon = IT_MEGAMAN;
	W_SetCurrentAmmo ();
};

// gives a player the gun (spawn, impulse 9)
void(entity p) MegaMan_Give =
{
	p.items = p.items | IT_MEGAMAN;
	if (p.mm_ammo < MM_MAX_AMMO)
		p.mm_ammo = MM_MAX_AMMO;
};

/*
================
The little Mega Man other players see in your hand. Hidden from you unless you
are in third person (chase_active).
================
*/
void() MegaMan_VwepThink =
{
	local entity p;
	local float s;

	p = self.owner;
	if (p.mm_vwep != self || p.classname != "player" || p.health <= 0)
	{
		if (p.mm_vwep == self)
			p.mm_vwep = world;
		remove (self);
		return;
	}
	self.nextthink = time + 0.1;
	self.frame = floor (time * 10);
	self.frame = self.frame - 16 * floor (self.frame / 16);
	s = sin (time * 6.3);
	self.origin_z = s * 1.2;
};

void() MegaMan_UpdateVwep =
{
#ifdef COMBATPLUS
	// Combat+ handles IT_MEGAMAN uniformly via HeldVwep_Update (client.qc)
	if (self.mm_vwep)
	{
		remove (self.mm_vwep);
		self.mm_vwep = world;
	}
	return;
#else
	local entity e;
	local float show;

	show = (self.weapon == IT_MEGAMAN && self.health > 0 && !(self.items & IT_INVISIBILITY) && !(self.effects & EF_NODRAW) && self.model == "progs/player_torso.mdl");
	if (!show)
	{
		if (self.mm_vwep)
		{
			remove (self.mm_vwep);
			self.mm_vwep = world;
		}
		return;
	}

	e = self.mm_vwep;
	if (!e)
	{
		e = spawn ();
		e.classname = "mm_vwep";
		e.owner = self;
		e.exteriormodeltoclient = self;
		e.scale = 0.8;
		setattachment (e, self, "");
		e.origin = '12 -20 0';
		e.think = MegaMan_VwepThink;
		e.nextthink = time + 0.1;
		self.mm_vwep = e;
	}

	// empty hand from the throw until the next one is ready
	if (self.mm_fire_t && time - self.mm_fire_t > 0.15 && time - self.mm_fire_t < 0.6)
		show = FALSE;
	if (self.mm_ammo < 1)
		show = FALSE;
	if (show && e.modelindex == 0)
		setmodel (e, "progs/megaman.md3");
	else if (!show && e.modelindex != 0)
		setmodel (e, "");
#endif
};

// called every frame from W_WeaponFrame: recharge, throw timing, the held Mega Man's animation
// (v_megaman.md3, the Mega-Slinger: 0-15 idle, 16-35 fire and reload, 36 empty rails)
void() MegaMan_ViewFrame =
{
	local float t;
	local float f;
	local float mv;
	local float it;
	local string want_mdl;

#ifdef COMBATPLUS
	if (!autocvar_bm_reload)	// the Bakersfield LAN magazines (bm_reload.qc) reload it instead
#endif
	if (self.mm_ammo < MM_MAX_AMMO && (self.items & IT_MEGAMAN))
	{
		if (!self.mm_regen_t)
			self.mm_regen_t = time + MM_REGEN_TIME;
		else if (time >= self.mm_regen_t)
		{
			self.mm_ammo = self.mm_ammo + 1;
			self.mm_regen_t = 0;
			if (self.weapon == IT_MEGAMAN)
			{
				self.currentammo = self.mm_ammo;
				if (self.mm_ammo == 1 && time - self.mm_fire_t > 0.5)
					self.mm_fire_t = time - 0.5;	// play the pop-up into the empty hand
			}
		}
	}

	if (self.mm_pending && time >= self.mm_launch_t)
	{
		self.mm_pending = FALSE;
#ifdef COMBATPLUS
		if (time - self.mm_launch_t < 0.3 && self.health > 0
			&& !FD_Flying (self) && !Veh_Driving (self) && !JohnBird_Flying (self) && !RocketRider_Flying (self)
			&& !EricCannon_Active (self) && !MMTank_Driving (self))
#else
		if (time - self.mm_launch_t < 0.3 && self.health > 0)
#endif
			MegaMan_Launch ();
	}

	MegaMan_UpdateVwep ();

	if (self.weapon != IT_MEGAMAN)
	{
		self.mm_vm_var = 0;
		return;
	}
#ifdef COMBATPLUS
	if (self.meleeing == 1 || self.throwing == 1
		|| FD_Flying (self) || Veh_Driving (self) || JohnBird_Flying (self) || RocketRider_Flying (self)
		|| EricCannon_Active (self) || MMTank_Driving (self) || Binoc_On (self))
		return;
#endif

	// Optional 4-Weapon Arsenal live switcher via cvar "mm_variant" (0=classic v_megaman, 1=cannon, 2=slingshot, 3=bow, 4=handthrow)
	want_mdl = MM_PickVModel ();
	mv = mm_variant_cached;
	if (self.weaponmodel != want_mdl)
		self.weaponmodel = want_mdl;
	// the Combat+ adjustable view model clears weaponmodel every frame (custom_effects.qc), so a weaponmodel change can't
	// tell when to reset: that cancelled every inspect on the next frame. Reset on switching in or changing mm_variant only.
	if (self.mm_vm_var != mv + 1)
	{
		self.mm_vm_var = mv + 1;
		self.mm_inspect_t = 0;
		self.mm_next_inspect = time + 3.5 + random () * 4.0;
	}

	t = time - self.mm_fire_t;
	if (self.mm_fire_t && t < 1.2)
	{
		self.mm_inspect_t = 0;
		if (t < 0.15)
			f = 16 + floor (t * 20);		// trigger, jaws open, the ram slams; he leaves the rails at 0.15
		else if (t < 0.5)
			f = 19 + floor ((t - 0.15) / 0.35 * 6);	// launch, recoil, steam, ram retracts
		else if (self.mm_ammo < 1)
			f = 36;		// that was the last one: the rails stay empty
		else
		{
			f = 25 + floor ((t - 0.5) / 0.7 * 11);	// the next one rises onto the rails and the jaws lock
			if (f > 35)
				f = 35;
		}
	}
	else if (self.mm_ammo < 1)
	{
		self.mm_inspect_t = 0;
		f = 36;		// empty rails while it recharges
	}
	else if (mv >= 1 && mv <= 4)
	{
		// 89-frame 4-Weapon Arsenal: continuous spinning-wheel + bobbling idle (0..15) + random CoD Inspects (37..60 & 61..88)!
		if (!self.mm_next_inspect)
			self.mm_next_inspect = time + 4.5 + random () * 5.0;

		if (!self.mm_inspect_t && time >= self.mm_next_inspect)
		{
			if (random () < 0.55)
			{
				if (self.mm_inspect_kind == 2)
					MegaMan_StartInspect (1);
				else
					MegaMan_StartInspect (2);
			}
			else if (random () < 0.5)
				MegaMan_StartInspect (2);
			else
				MegaMan_StartInspect (1);
		}

		if (self.mm_inspect_t)
		{
			it = time - self.mm_inspect_t;
			if (self.mm_inspect_kind == 2)
			{
				// CoD Inspect B: Grab the chrome bar w/ red shop rag & clean it! (28 frames: 61..88 @ 12 fps)
				f = 61 + floor (it * 12);
				if (f >= 82 && !self.mm_glint_ding)
				{
					self.mm_glint_ding = TRUE;
					MM_Sound (self, CHAN_AUTO, "weapons/tink1.wav", 0.45, 165);
				}
				if (f > 88)
				{
					self.mm_inspect_t = 0;
					f = floor (time * 12);
					f = f - 16 * floor (f / 16);
				}
			}
			else
			{
				// CoD Inspect A: Hold weapon out left & right to admire! (24 frames: 37..60 @ 12 fps)
				f = 37 + floor (it * 12);
				if (f > 60)
				{
					self.mm_inspect_t = 0;
					f = floor (time * 12);
					f = f - 16 * floor (f / 16);
				}
			}
		}
		else
		{
			f = floor (time * 12);
			f = f - 16 * floor (f / 16);
		}
	}
	else
	{
		f = floor (time * 10);
		f = f - 16 * floor (f / 16);
	}
	self.weaponframe = f;
};
