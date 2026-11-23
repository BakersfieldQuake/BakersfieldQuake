/*
================
THE WHEELMAN CANNON (see wcannon_defs.qc for the rules and numbers)

FunGun_Attack calls WC_Press when fire goes down; FunGun_ViewFrame calls WC_Frame every frame, which charges while fire is
held and launches (WC_Fire) on release or at full charge. The shot (WC_Touch, WC_Think) is the driving sprite of
progs/wheelman.spr32. He is a driving projectile, not a rocket: MOVETYPE_NONE with his own physics in WC_Think: gravity, he hugs
the floor at his speed and follows ramps up and down, leaves a crest in an arc, drives over steps, crashes into walls, ceilings and
anyone he hits, and can be shot (WC_HEALTH). No flames or trail. The crash (WC_Crash) deals radius damage, triggers a normal rocket
explosion (WC_Boom) with flying wheels, bars, gibs and sparks (WC_Debris), and launches the crazed Wheelman (WC_Dancer) sprinting
around really fast while cycling through all 8 crazy 360-degree animations of progs/wheelman_dance.spr32.
================
*/

float	wc_fx_spark, wc_fx_muzzle, wc_fx_chunk;
float	wc_last_boom, wc_last_run, wc_boom_dur;
var float	autocvar_wc_debug = 0;

// the two Wheelman sprites (~10.5 MB) load the first time the cannon starts charging, not on every map
float	wc_sprites_loaded;
void() WC_PrecacheSprites =
{
	if (wc_sprites_loaded)
		return;
	wc_sprites_loaded = TRUE;
	precache_model ("progs/wheelman.spr32");
	precache_model ("progs/wheelman_dance.spr32");
};

void() WC_Precache =
{
	precache_model ("progs/v_wewcannon.md3");
	precache_model ("progs/wc_bar.md3");
	precache_model ("progs/mm_wheel.md3");
	precache_model ("progs/s_explod.spr");
	precache_model ("progs/s_explodbig.spr");
	precache_model ("progs/gib1.mdl");
	precache_model ("progs/gib2.mdl");
	precache_model ("progs/gib3.mdl");
	precache_sound ("wcannon/wc_charge.wav");
	precache_sound ("wcannon/wc_shoot.wav");
	precache_sound ("wcannon/wc_scream.wav");
	precache_sound ("wcannon/wc_boom.wav");
	precache_sound ("wcannon/wc_lboom1.wav");
	precache_sound ("wcannon/wc_lboom2.wav");
	precache_sound ("wcannon/wc_lboom3.wav");
	precache_sound ("wcannon/wc_lboom4.wav");
	precache_sound ("wcannon/wc_lboom5.wav");
	precache_sound ("wcannon/wc_lboom6.wav");
	precache_sound ("wcannon/wc_lboom7.wav");
	precache_sound ("wcannon/wc_lboom8.wav");
	precache_sound ("wcannon/wc_lrun01.wav");
	precache_sound ("wcannon/wc_lrun02.wav");
	precache_sound ("wcannon/wc_lrun03.wav");
	precache_sound ("wcannon/wc_lrun04.wav");
	precache_sound ("wcannon/wc_lrun05.wav");
	precache_sound ("wcannon/wc_lrun06.wav");
	precache_sound ("wcannon/wc_lrun07.wav");
	precache_sound ("wcannon/wc_lrun08.wav");
	precache_sound ("wcannon/wc_lrun09.wav");
	precache_sound ("wcannon/wc_lrun10.wav");
	precache_sound ("wcannon/wc_lrun11.wav");
	precache_sound ("wcannon/wc_lrun12.wav");
	precache_sound ("friends/gowewd.wav");
	precache_sound ("weapons/r_exp3.wav");
	precache_sound ("weapons/xpld_wat.wav");
	precache_sound ("weapons/explodedist.wav");
	precache_sound ("weapons/tink1.wav");
	precache_sound ("weapons/ric1.wav");
	precache_sound ("weapons/ric2.wav");
	precache_sound ("misc/null.wav");
	wc_fx_spark = particleeffectnum ("wc_sparks");
	wc_fx_muzzle = particleeffectnum ("wc_muzzle");
	wc_fx_chunk = particleeffectnum ("wc_chunk");
};

// non-repeating Larry explosion shout via pointsound (survives BecomeExplosion() removal at 0.6s)
float(entity e) WC_PlayLarryBoom =
{
	local float k;

	k = floor (random () * 7.99) + 1;
	if (k == wc_last_boom)
	{
		k = k + 1;
		if (k > 8)
			k = 1;
	}
	wc_last_boom = k;
	if (k == 1) { pointsound (e.origin, "wcannon/wc_lboom1.wav", WC_LINE_VOL, ATTN_NORM); return 0.98; }
	if (k == 2) { pointsound (e.origin, "wcannon/wc_lboom2.wav", WC_LINE_VOL, ATTN_NORM); return 1.73; }
	if (k == 3) { pointsound (e.origin, "wcannon/wc_lboom3.wav", WC_LINE_VOL, ATTN_NORM); return 2.03; }
	if (k == 4) { pointsound (e.origin, "wcannon/wc_lboom4.wav", WC_LINE_VOL, ATTN_NORM); return 2.60; }
	if (k == 5) { pointsound (e.origin, "wcannon/wc_lboom5.wav", WC_LINE_VOL, ATTN_NORM); return 1.89; }
	if (k == 6) { pointsound (e.origin, "wcannon/wc_lboom6.wav", WC_LINE_VOL, ATTN_NORM); return 2.70; }
	if (k == 7) { pointsound (e.origin, "wcannon/wc_lboom7.wav", WC_LINE_VOL, ATTN_NORM); return 2.25; }
	pointsound (e.origin, "wcannon/wc_lboom8.wav", WC_LINE_VOL, ATTN_NORM);
	return 2.70;
};

// non-repeating Larry voice clip while crazed Larry sprints & bounces around after exploding
float(entity e) WC_PlayLarryRun =
{
	local float k, p;

	k = floor (random () * 11.99) + 1;
	if (k == wc_last_run)
	{
		k = k + 1;
		if (k > 12)
			k = 1;
	}
	wc_last_run = k;
	p = SNDSPD * (0.98 + random () * 0.05);
	if (k == 1)  { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun01.wav", WC_LINE_VOL, ATTN_NORM, p); return 2.30; }
	if (k == 2)  { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun02.wav", WC_LINE_VOL, ATTN_NORM, p); return 2.60; }
	if (k == 3)  { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun03.wav", WC_LINE_VOL, ATTN_NORM, p); return 2.50; }
	if (k == 4)  { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun04.wav", WC_LINE_VOL, ATTN_NORM, p); return 1.76; }
	if (k == 5)  { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun05.wav", WC_LINE_VOL, ATTN_NORM, p); return 2.04; }
	if (k == 6)  { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun06.wav", WC_LINE_VOL, ATTN_NORM, p); return 1.37; }
	if (k == 7)  { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun07.wav", WC_LINE_VOL, ATTN_NORM, p); return 2.12; }
	if (k == 8)  { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun08.wav", WC_LINE_VOL, ATTN_NORM, p); return 2.00; }
	if (k == 9)  { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun09.wav", WC_LINE_VOL, ATTN_NORM, p); return 1.90; }
	if (k == 10) { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun10.wav", WC_LINE_VOL, ATTN_NORM, p); return 1.05; }
	if (k == 11) { sound7 (e, CHAN_VOICE, "wcannon/wc_lrun11.wav", WC_LINE_VOL, ATTN_NORM, p); return 0.99; }
	sound7 (e, CHAN_VOICE, "wcannon/wc_lrun12.wav", WC_LINE_VOL, ATTN_NORM, p);
	return 1.16;
};

// the picture of a sprite that has a ring of 8 views (0 = seen from the front, 4 = from behind): which view 'other' sees
float(vector from) WC_View =
{
	local vector delta;
	local float rel, d;

	delta = (other.origin + other.view_ofs) - from;
	rel = vectoyaw (delta) - self.angles_y;
	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 45 + 0.5);
	if (d >= 8)
		d = 0;
	return d;
};

// the shot: two thirds of the time he just drives (frames 8 + d * 6 + k, or the overhead / underneath views when the viewer is
// steeply above or below him), the rest of the time one of the weird ones (WC_Think picks): 56 screaming, 136 fire-wheels,
// 168 weightlifting bar (no jetpack frames: owner's review 2026-11-01). In the air he screams.
float() WC_ShotCustomize =
{
	local float d, k, a, dz, hd;
	local vector delta;

	d = WC_View (self.origin + '0 0 24');
	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 24');
	dz = delta_z;
	delta_z = 0;
	hd = vlen (delta);
	if (dz > hd * 1.73)
	{
		k = floor (time * 15);
		k = k - 3 * floor (k / 3);
		self.frame = 88 + d * 3 + k;
		return TRUE;
	}
	if (dz > hd * 0.58)
	{
		k = floor (time * 15);
		k = k - 3 * floor (k / 3);
		self.frame = 200 + d * 3 + k;
		return TRUE;
	}
	a = self.wc_anim;
	if (self.wc_air)
		a = 1;
	if (a == 0)
	{
		if (dz < 0 - hd * 0.55)
		{
			k = floor (time * 15);
			k = k - 3 * floor (k / 3);
			self.frame = 112 + d * 3 + k;
			return TRUE;
		}
		k = floor (time * 10 + self.origin_x * 0.025);
		k = k - 6 * floor (k / 6);
		self.frame = 8 + d * 6 + k;
		return TRUE;
	}
	k = floor (time * 12);
	k = k - 4 * floor (k / 4);
	if (a == 1)
		self.frame = 56 + d * 4 + k;
	else if (a == 2)
		self.frame = 136 + d * 4 + k;
	else
		self.frame = 168 + d * 4 + k;
	return TRUE;
};

// ---------------------------------------------------------------- the crash

void() WC_ChunkTouch =
{
	if (other != world || time < self.wc_snd || vlen (self.velocity) < 90)
		return;
	self.wc_snd = time + 0.25;
	if (random () < 0.5)
		sound (self, CHAN_AUTO, "weapons/tink1.wav", 0.7, ATTN_NORM);
	else
		sound (self, CHAN_AUTO, "weapons/ric1.wav", 0.6, ATTN_NORM);
	pointparticles (wc_fx_spark, self.origin, '0 0 70', 4);
};

void() WC_ChunkThink =
{
	local float left;

	left = self.fg_born + self.wc_until - time;
	if (left <= 0)
	{
		remove (self);
		return;
	}
	if (left < 1)
		self.scale = self.dmg * left;
	self.nextthink = time + 0.1;
};

// one flying piece (a wheel or a bar)
void(string mdl, vector org, vector vel, float sc, float life) WC_Chunk =
{
	local entity d;

	d = spawn ();
	d.classname = "wc_debris";
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_TRIGGER;		// touches the world (the bounce sound) but never blocks anyone
	d.fg_born = time;
	d.wc_until = life;
	d.dmg = sc;
	d.scale = sc;
	setmodel (d, mdl);
	setsize (d, '-6 -6 -6', '6 6 6');
	setorigin (d, org);
	d.velocity = vel;
	d.avelocity = '0 0 0';
	d.avelocity_x = crandom () * 700;
	d.avelocity_y = crandom () * 700;
	d.avelocity_z = crandom () * 400;
	d.bouncefactor = 0.55;
	d.bouncestop = 0.1;
	d.traileffectnum = wc_fx_chunk;
	d.touch = WC_ChunkTouch;
	d.think = WC_ChunkThink;
	d.nextthink = time + 0.1;
};

vector(float lift) WC_Fling =
{
	local vector v;

	v_x = crandom () * 620;
	v_y = crandom () * 620;
	v_z = lift + random () * 420;
	return v;
};

// wheels, bars, gibs and sparks. self = the explosion entity (ThrowGib throws from self)
void(vector org, float tier) WC_Debris =
{
	local float n, i, gcount;

	n = 1 + (tier >= 2);		// fewer visible wheels in the explosion (was 3 + tier)
	i = 0;
	while (i < n)
	{
		WC_Chunk ("progs/mm_wheel.md3", org + '0 0 20', WC_Fling (260 + tier * 40), 0.85, 2.5 + random () * 1.5);
		i = i + 1;
	}
	n = 1 + (tier >= 2);		// bars
	i = 0;
	while (i < n)
	{
		WC_Chunk ("progs/wc_bar.md3", org + '0 0 24', WC_Fling (260 + tier * 40), 1, 5 + random () * 2);
		i = i + 1;
	}
	gcount = 4 + tier * 3;		// more gibs
	i = 0;
	while (i < gcount)
	{
		ThrowGib ("progs/gib1.mdl", -70 - tier * 25);
		ThrowGib ("progs/gib2.mdl", -85 - tier * 30);
		if (i < 4)
			ThrowGib ("progs/gib3.mdl", -95 - tier * 35);
		i = i + 2;
	}
	pointparticles (wc_fx_spark, org + '0 0 24', '0 0 160', 35 + tier * 20);
};

// normal rocket explosion at 'org' (no custom Wheelman explosion sprite), plus flying wheels, bars and gibs
void(vector org, float tier, entity hit) WC_Boom =
{
	local entity b, me;
	local vector detonate;
	local float pc;

	detonate = org + '0 0 16';
	if (vlen (self.velocity) > 1)
	{
		detonate = detonate - 8 * normalize (self.velocity);
		if (pointcontents (detonate) == CONTENT_SOLID)
			detonate = org + '0 0 16';
	}
	b = spawn ();
	setorigin (b, detonate);
	pc = pointcontents (detonate);
	if (pc == CONTENT_SLIME)
		sendParticle ("slimesplash", detonate, VEC_ORIGIN, 1, 0);
	else if (autocvar_effects_classic_explosion == 1)
		sendParticle ("rocket_explo_classic", detonate, VEC_ORIGIN, 1, 0);
	else if (autocvar_explosiondebris == 0 && hit && hit.health)
		sendParticle ("rocket_explosion_nodebris", detonate, VEC_ORIGIN, 1, 0);
	else
		sendParticle ("rocket_explosion", detonate, VEC_ORIGIN, 1, 0);
	if (pc == CONTENT_WATER || pc == CONTENT_SLIME || pc == CONTENT_LAVA)
	{
		sound7 (b, CHAN_WEAPON, "weapons/xpld_wat.wav", 1, ATTN_NORM, SNDSPD - 10);
		sound7 (b, CHAN_AUTO, "weapons/explodedist.wav", 0.5, 0.4, SNDSPD - 10);
	}
	else
	{
		sound7 (b, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
		sound7 (b, CHAN_AUTO, "weapons/explodedist.wav", 0.3, 0.4, SNDSPD);
	}
	wc_boom_dur = WC_PlayLarryBoom (b);
	me = self;
	self = b;
	if (hit && hit.health)
		sparklers (2);
	sparklers (0);
	WC_Debris (org, tier);
	BecomeExplosion ();
	self = me;
};

// ---------------------------------------------------------------- the post-crash crazed runner
// progs/wheelman_dance.spr32 (build_hd_npc_sprites.py + build_npc_death_anims.py + build_wheelman_dance.py, 496 frames at 80x80 tight-cropped, type 2 SPR_VP_PARALLEL, scale 0.8645):
//   0..39    (0) run_stuck      0 + d * 5 + k
//   40..79   (1) run_overhead   40 + d * 5 + k
//   80..127  (2) dance          80 + d * 6 + k
//   128..167 (3) hands_up_kick  128 + d * 5 + k
//   168..215 (4) spin_bar       168 + d * 6 + k
//   216..263 (5) weightlift     216 + d * 6 + k
//   264..311 (6) throw_rig      264 + d * 6 + k
//   312..367 (7) turn_robot     312 + d * 7 + step
//   368..399     8-dir x 4-step death frames (used by crowd_npcs.qc)
//   400..447     8-dir x 6-step above45 overhead dance (400 + d * 6 + k, centered origin)
//   448..495     8-dir x 6-step above90 overhead dance (448 + d * 6 + k, centered origin)

float() WC_DancerCustomize =
{
	local float d, k, a, step, dz, hd;
	local vector delta;

	d = WC_View (self.origin + '0 0 28');
	k = floor ((time - self.wc_t0) * 12);
	if (k < 0)
		k = 0;
	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 28');
	dz = delta_z;
	delta_z = 0;
	hd = vlen (delta);
	if (dz > hd * 1.73)
	{
		self.frame = 448 + d * 6 + k - 6 * floor (k / 6);
		return TRUE;
	}
	if (dz > hd * 0.58)
	{
		self.frame = 400 + d * 6 + k - 6 * floor (k / 6);
		return TRUE;
	}
	a = self.wc_anim;
	if (a == 0)
		self.frame = d * 5 + k - 5 * floor (k / 5);
	else if (a == 1)
		self.frame = 40 + d * 5 + k - 5 * floor (k / 5);
	else if (a == 2)
		self.frame = 80 + d * 6 + k - 6 * floor (k / 6);
	else if (a == 3)
		self.frame = 128 + d * 5 + k - 5 * floor (k / 5);
	else if (a == 4)
		self.frame = 168 + d * 6 + k - 6 * floor (k / 6);
	else if (a == 5)
		self.frame = 216 + d * 6 + k - 6 * floor (k / 6);
	else if (a == 6)
		self.frame = 264 + d * 6 + k - 6 * floor (k / 6);
	else
	{
		if (k < 4)
			step = k;
		else
			step = 4 + (k - 4) - 3 * floor ((k - 4) / 3);
		self.frame = 312 + d * 7 + step;
	}
	return TRUE;
};

void() WC_DancerThink =
{
	local float dt, g, i, rem, frac, grounded, na, yaw, turn;
	local vector n, nh, f, v0;

	dt = time - self.wc_t;
	if (dt > 0.1)
		dt = 0.1;
	if (dt < 0)
		dt = 0;
	self.wc_t = time;
	self.nextthink = time + 0.02;

	if (time >= self.wc_until)
	{
		pointparticles (wc_fx_spark, self.origin + '0 0 28', '0 0 120', 40);
		remove (self);
		return;
	}
	if (pointcontents (self.origin + '0 0 8') == CONTENT_SKY)
	{
		remove (self);
		return;
	}

	grounded = FALSE;
	n = '0 0 1';		// only read when grounded; set so it is never uninitialised
	traceline (self.origin + '0 0 6', self.origin - '0 0 6', TRUE, self);
	if (trace_fraction < 1 && !trace_startsolid && trace_plane_normal_z >= 0.7)
	{
		n = trace_plane_normal;
		if (self.velocity * n < 80)
			grounded = TRUE;
	}

	// switch rapidly across all 8 crazy animations while juking and sprinting at hyper-speed
	if (time >= self.wc_anim_t)
	{
		self.wc_anim_t = time + 0.55 + random () * 0.55;
		na = floor (random () * 7.99);
		if (na == self.wc_anim)
			na = na + 1 - 8 * floor ((na + 1) / 8);
		self.wc_anim = na;
		self.wc_t0 = time;
		self.wc_speed = WC_DANCE_SPEED * (0.9 + random () * 0.35);
		turn = 45 + random () * 95;
		if (random () < 0.5)
			turn = 0 - turn;
		yaw = vectoyaw (self.wc_dir) + turn;
		makevectors ('0 1 0' * yaw);
		self.wc_dir = v_forward;
		if (grounded && random () < 0.35)
		{
			self.velocity_z = 165 + random () * 95;
			grounded = FALSE;
		}
	}

	if (grounded)
	{
		f = self.wc_dir - n * (self.wc_dir * n);
		self.velocity = normalize (f) * self.wc_speed;
	}
	else
	{
		g = bm_cvar_grav;
		if (g <= 0)
			g = 800;
		self.velocity_x = self.wc_dir_x * self.wc_speed;
		self.velocity_y = self.wc_dir_y * self.wc_speed;
		self.velocity_z = self.velocity_z - g * dt;
	}
	self.angles_y = vectoyaw (self.wc_dir);

	// 50 Hz world-only physics: sprints up stairs/ramps, drops off ledges, ricochets wildly off walls
	rem = dt;
	i = 0;
	while (i < 3 && rem > 0.0001)
	{
		tracebox (self.origin, self.mins, self.maxs, self.origin + self.velocity * rem, TRUE, self);
		if (trace_startsolid)
		{
			tracebox (self.origin + '0 0 18', self.mins, self.maxs, self.origin + '0 0 18', TRUE, self);
			if (trace_startsolid)
			{
				pointparticles (wc_fx_spark, self.origin + '0 0 24', '0 0 120', 30);
				remove (self);
				return;
			}
			setorigin (self, self.origin + '0 0 18');
			break;
		}
		setorigin (self, trace_endpos);
		if (trace_fraction == 1)
			break;
		frac = trace_fraction;
		n = trace_plane_normal;
		if (n_z >= 0.7)
		{
			self.velocity = self.velocity - n * (self.velocity * n);
		}
		else
		{
			v0 = self.velocity;
			v0_z = 0;
			if (vlen (v0) >= 1)
			{
				tracebox (self.origin + '0 0 18', self.mins, self.maxs, self.origin + '0 0 18' + normalize (v0) * 16, TRUE, self);
				if (trace_fraction == 1 && !trace_startsolid)
				{
					setorigin (self, self.origin + '0 0 18');
					rem = rem * (1 - frac);
					i = i + 1;
					continue;
				}
			}
			// wall hit: ricochet into open space and keep sprinting at full tilt
			nh = n;
			nh_z = 0;
			if (vlen (nh) > 0.01)
			{
				nh = normalize (nh);
				f = self.wc_dir - 2 * (self.wc_dir * nh) * nh;
				yaw = vectoyaw (f) + crandom () * 35;
			}
			else
				yaw = self.angles_y + 140 + random () * 80;
			makevectors ('0 1 0' * yaw);
			self.wc_dir = v_forward;
			self.angles_y = yaw;
			self.velocity_x = self.wc_dir_x * self.wc_speed;
			self.velocity_y = self.wc_dir_y * self.wc_speed;
		}
		rem = rem * (1 - frac);
		i = i + 1;
	}
	if (grounded && self.velocity_z <= 0)
	{
		tracebox (self.origin, self.mins, self.maxs, self.origin - '0 0 16', TRUE, self);
		if (trace_fraction < 1 && !trace_startsolid && trace_plane_normal_z >= 0.7)
			setorigin (self, trace_endpos);
	}

	if (time >= self.wc_snd)
	{
		self.wc_snd = time + WC_PlayLarryRun (self) + 1 + random ();
	}
};

// bursts straight out of the explosion sprinting wildly and cycling through all 8 crazy Wheelman animations
void(vector org, vector in_dir) WC_Dancer =
{
	local entity d;
	local vector spot, best_dir;
	local float base_yaw, yaw, best_frac, k;

	spot = org + '0 0 2';
	tracebox (spot, '-12 -12 0', '12 12 48', spot, TRUE, world);
	if (trace_startsolid)
	{
		spot = org - in_dir * 16 + '0 0 8';
		tracebox (spot, '-12 -12 0', '12 12 48', spot, TRUE, world);
	}
	if (trace_startsolid)
	{
		spot = org + '0 0 20';
		tracebox (spot, '-12 -12 0', '12 12 48', spot, TRUE, world);
	}
	if (trace_startsolid)
	{
		spot = org - '0 0 28';
		tracebox (spot, '-12 -12 0', '12 12 48', spot, TRUE, world);
	}
	if (trace_startsolid)
		return;

	// pick a direction with open room so he bolts out of the blast instead of straight into a wall
	if (vlen (in_dir) > 0.01)
		base_yaw = vectoyaw ('0 0 0' - in_dir) + crandom () * 60;
	else
		base_yaw = random () * 360;
	best_frac = -1;
	best_dir = '1 0 0';
	k = 0;
	while (k < 8)
	{
		yaw = base_yaw + k * 45;
		makevectors ('0 1 0' * yaw);
		traceline (spot + '0 0 24', spot + '0 0 24' + v_forward * 160, TRUE, world);
		if (trace_fraction > best_frac)
		{
			best_frac = trace_fraction;
			best_dir = v_forward;
		}
		k = k + 1;
	}

	d = spawn ();
	d.classname = "wc_dancer";
	d.movetype = MOVETYPE_NONE;
	d.solid = SOLID_NOT;
	d.fg_born = time;
	d.wc_t = time;
	d.wc_t0 = time;
	d.wc_until = time + WC_DANCE_LIFE;
	d.wc_anim = floor (random () * 7.99);
	d.wc_anim_t = time + 0.6 + random () * 0.5;
	d.wc_speed = WC_DANCE_SPEED * (0.95 + random () * 0.25);
	d.wc_dir = best_dir;
	d.angles_y = vectoyaw (best_dir);
	if (wc_boom_dur > 0.5)
		d.wc_snd = time + wc_boom_dur * 0.72;
	else
		d.wc_snd = time + 0.55;
	setmodel (d, "progs/wheelman_dance.spr32");
	d.scale = 0.8645;		// 80x80 tight-cropped sprite scaled to player height (0.1921 * 360/80)
	setsize (d, '-12 -12 0', '12 12 48');
	setorigin (d, spot);
	d.velocity = best_dir * d.wc_speed + '0 0 175';
	d.customizeentityforclient = WC_DancerCustomize;
	d.think = WC_DancerThink;
	d.nextthink = time + 0.02;
};

// his owner left: no blast in an empty (or reused) slot's name, he just sparks out
void() WC_Fizzle =
{
	sound (self, CHAN_VOICE, "misc/null.wav", 1, ATTN_NONE);		// the scream stops
	pointparticles (wc_fx_spark, self.origin + '0 0 24', '0 0 120', 30);
	remove (self);
};

void(entity hit) WC_Crash =
{
	local vector org, in_dir, kick;
	local float tier, dmg, dir_bonus;
	local entity e;

	if (self.owner.classname != "player")
	{
		WC_Fizzle ();
		return;
	}
	org = self.origin;
	in_dir = self.wc_dir;
	tier = self.wc_tier;
	self.takedamage = DAMAGE_NO;		// his own blast must not shoot him down again
	self.solid = SOLID_NOT;
	setsize (self, '0 0 0', '0 0 0');		// T_Damage pushes away from the middle of the inflictor's box: with his 48 high box the blast sat above you and pushed you into the floor
	dmg = WC_DMG_BASE + tier * WC_DMG_STEP;
	dir_bonus = WC_DMG_DIRECT + tier * 12;
	dprint (strcat ("wcannon: crash tier ", strcat (ftos (tier), strcat (" at ", strcat (vtos (org), "\n")))));
	sound (self, CHAN_VOICE, "misc/null.wav", 1, ATTN_NONE);		// the scream stops
	fg_inflicting = FG_WCANNON;
	if (hit && hit.takedamage)
		T_Damage (hit, self, self.owner, dmg + dir_bonus);
	T_RadiusDamage (self, self.owner, dmg, hit);
	fg_inflicting = 0;
	if (tier <= 1)
	{
		e = findradius (org, dmg + 60);
		while (e)
		{
			if (e != self.owner && e.health > 0 && (e.movetype == MOVETYPE_WALK || e.movetype == MOVETYPE_STEP))
			{
				kick = e.origin - org;
				kick_z = 0;
				if (vlen (kick) < 1)
					kick = in_dir;
				kick = normalize (kick);
				e.flags = e.flags - (e.flags & FL_ONGROUND);
				e.velocity = e.velocity + kick * 260 + '0 0 220';
			}
			e = e.chain;
		}
	}
	WC_Boom (org, tier, hit);
	WC_Dancer (org, in_dir);
	remove (self);
};

void() WC_DieNow =
{
	WC_Crash (world);
};

// shot down: he blows up where he is, on a think of his own (not inside the T_RadiusDamage that may have killed him,
// whose .chain list his own blast would rewrite)
void() WC_Die =
{
	dprint ("wcannon: shot down\n");
	PC_NoteKilled (self, damage_attacker);
	self.takedamage = DAMAGE_NO;
	self.touch = SUB_Null;
	self.velocity = '0 0 0';
	self.think = WC_DieNow;
	self.nextthink = time;
};

// something ran into him (he is solid: the engine calls this when it moves into him)
void() WC_Touch =
{
	if (other == self.owner)
		return;
	if (other != world && other.pc_kind > PC_KIND_NONE)
	{
		PC_HandlePair (self, other);
		return;
	}
	if (other.takedamage)
		WC_Crash (other);
};

// his own physics, every 0.02 s: heading, gravity, driving along the floor (up ramps, over steps), the crash
void() WC_Think =
{
	local float dt, g, i, rem, frac, grounded, c;
	local vector n, f, v0;

	dt = time - self.wc_t;
	if (dt > 0.1)
		dt = 0.1;
	if (dt < 0)
		dt = 0;
	self.wc_t = time;
	self.nextthink = time + 0.02;
	if (self.owner.classname != "player")
	{
		WC_Fizzle ();		// owner left
		return;
	}
	if (time - self.fg_born > WC_LIFE)
	{
		WC_Crash (world);
		return;
	}
	if (self.takedamage == DAMAGE_NO && time >= self.fg_born + 0.22)
		self.takedamage = DAMAGE_AIM;
	c = pointcontents (self.origin + '0 0 8');
	if (c == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	if (c != CONTENT_EMPTY)
	{
		WC_Crash (world);		// water, slime or lava: he blows up
		return;
	}
	f = self.velocity;
	f_z = 0;
	if (vlen (f) > 60)
		self.wc_dir = normalize (f);
	// is there a floor under him that he is not moving away from?
	grounded = FALSE;
	n = '0 0 1';		// only read when grounded; set so it is never uninitialised
	if (time >= self.skypad_steer_t)
	{
		traceline (self.origin + '0 0 6', self.origin - '0 0 6', TRUE, self);
		if (trace_fraction < 1 && !trace_startsolid && trace_plane_normal_z >= 0.7)
		{
			n = trace_plane_normal;
			if (self.velocity * n < 40)
				grounded = TRUE;
		}
	}
	if (grounded)
	{
		f = self.wc_dir - n * (self.wc_dir * n);		// his heading, flattened onto the floor: up a ramp, down a ramp
		self.velocity = normalize (f) * self.wc_speed;
	}
	else
	{
		g = bm_cvar_grav;
		if (g <= 0)
			g = 800;
		self.velocity_z = self.velocity_z - g * dt;
	}
	self.wc_air = !grounded;
	self.angles_y = vectoyaw (self.wc_dir);
	// move: slide along floors and ramps, drive over low steps, crash into anything else
	rem = dt;
	i = 0;
	while (i < 3 && rem > 0.0001)
	{
		tracebox (self.origin, self.mins, self.maxs, self.origin + self.velocity * rem, FALSE, self);
		if (trace_startsolid)
		{
			WC_Crash (world);
			return;
		}
		setorigin (self, trace_endpos);
		if (trace_fraction == 1)
			break;
		frac = trace_fraction;
		if (trace_ent != world && trace_ent.pc_kind > PC_KIND_NONE)
		{
			if (PC_HandlePair (self, trace_ent))
				return;
		}
		else if (trace_ent != world && trace_ent.takedamage)
		{
			WC_Crash (trace_ent);
			return;
		}
		n = trace_plane_normal;
		if (n_z >= 0.7)
		{
			self.velocity = self.velocity - n * (self.velocity * n);
		}
		else
		{
			v0 = self.velocity;
			v0_z = 0;
			if (vlen (v0) < 1)
			{
				WC_Crash (trace_ent);
				return;
			}
			tracebox (self.origin + '0 0 1' * WC_STEPUP, self.mins, self.maxs, self.origin + '0 0 1' * WC_STEPUP + normalize (v0) * 16, FALSE, self);
			if (trace_fraction < 1 || trace_startsolid)
			{
				WC_Crash (world);		// a wall, a ceiling, anything he cannot drive over
				return;
			}
			setorigin (self, self.origin + '0 0 1' * WC_STEPUP);
		}
		rem = rem * (1 - frac);
		i = i + 1;
	}
	if (grounded && self.velocity_z < 0)
	{
		tracebox (self.origin, self.mins, self.maxs, self.origin - '0 0 16', FALSE, self);		// stay on a downhill
		if (trace_fraction < 1 && !trace_startsolid && trace_plane_normal_z >= 0.7)
			setorigin (self, trace_endpos);
	}
	// two thirds of the time he just drives, one third one of the weird animations (screaming, fire-wheels, bar)
	if (time >= self.wc_anim_t)
	{
		self.wc_anim_t = time + 1 + random () * 1.2;
		if (random () < 0.34)
		{
			self.wc_anim = 1 + floor (random () * 3);
			if (self.wc_anim > 3)
				self.wc_anim = 3;
		}
		else
			self.wc_anim = 0;
	}
	if (autocvar_wc_debug && time >= self.wc_dbg)
	{
		self.wc_dbg = time + 0.4;
		dprint (strcat ("wcannon: at ", strcat (vtos (self.origin), strcat (" vel ", strcat (vtos (self.velocity), strcat (" air ", strcat (ftos (self.wc_air), strcat (" anim ", strcat (ftos (self.wc_anim), "\n")))))))));
	}
	if (time >= self.wc_snd)
	{
		self.wc_snd = time + WC_SCREAM_GAP;
		sound (self, CHAN_VOICE, "wcannon/wc_scream.wav", WC_SCREAM_VOL, ATTN_NORM);
	}
};

// ---------------------------------------------------------------- the player side

void(float c) WC_Fire =
{
	local entity p;
	local float a, tier, spd;
	local vector org, aim;
	local entity me;

	WC_PrecacheSprites ();
	a = FunGun_Ammo (self, FG_WCANNON);
	self.wc_charging = 0;
	centerprint (self, "");
	sound (self, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NONE);		// the charge whine stops
	if (a < 1 || c < WC_MIN_CHARGE)
	{
		self.wc_cool = time + 0.3;
		return;
	}
	self.wc_cool = time + WC_COOLDOWN;
	self.attack_finished = time + WC_COOLDOWN;
	FunGun_SetAmmo (self, FG_WCANNON, a - 1);
	FunGun_Lock (FG_WCANNON);
	self.fg_fire_t = time;
	tier = floor (c * 4);
	if (tier > 3)
		tier = 3;
	spd = WC_SPEED_MIN + (WC_SPEED_MAX - WC_SPEED_MIN) * c;
	if (cvar ("wc_speed") > 0)
		spd = cvar ("wc_speed");		// test: a slow Wheelman to look at (zz_wcannon2.cfg)
	makevectors (self.v_angle);
	aim = v_forward;
	org = FG_Muzzle (36);
	if (aim_z > 0.14)
	{
		// aiming upward at rooftops/jetpackers: launch cleanly into the air instead of snapping down to the floor!
		tracebox (self.origin + '0 0 12', '-14 -14 0', '14 14 48', org - '0 0 12', TRUE, self);
		org = trace_endpos;
	}
	else
	{
		traceline (org, org - '0 0 70', TRUE, self);
		if (trace_fraction < 1 && !trace_startsolid)
			org = trace_endpos + '0 0 1';		// he starts on the floor in front of you (his sprite stands on its origin)
		else
			org = org - '0 0 24';
	}
	makevectors ('0 1 0' * self.v_angle_y);
	p = spawn ();
	p.classname = "wc_shot";
	p.owner = self;
	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_BBOX;
	p.takedamage = DAMAGE_NO;		// 0.22s spawn grace so stray shotgun pellets right at the muzzle don't self-pop!
	p.health = WC_HEALTH;
	p.th_die = WC_Die;
	p.fg_born = time;
	p.wc_t = time;
	p.wc_tier = tier;
	p.wc_speed = spd;
	p.wc_dir = v_forward;
	p.angles_y = self.v_angle_y;
	setmodel (p, "progs/wheelman.spr32");
	p.scale = WC_SCALE;
	setsize (p, '-14 -14 0', '14 14 48');
	setorigin (p, org);
	p.velocity = aim * spd;		// he leaves along your aim; once he is on the floor he drives
	p.customizeentityforclient = WC_ShotCustomize;
	p.touch = WC_Touch;
	p.think = WC_Think;
	p.nextthink = time + 0.02;
	p.wc_snd = time + WC_SCREAM_GAP;
	PC_Register (p, PC_KIND_HEAVY, 32);
	sound (p, CHAN_VOICE, "wcannon/wc_scream.wav", WC_SCREAM_VOL, ATTN_NORM);
	FG_Snd (self, CHAN_WEAPON, "wcannon/wc_shoot.wav", 0.8, 1);
	dprint (strcat ("wcannon: fire tier ", strcat (ftos (tier), strcat (" speed ", strcat (ftos (spd), "\n")))));
	pointparticles (wc_fx_muzzle, org + '0 0 30', aim * 120, 1);
	self.punchangle_x = -6 - 4 * c;
	centerprint (self, "");
	player_mm1 ();
	if (cvar ("wc_test") == 2)		// test aid: he crashes at once on the floor 230 units ahead (zz_fb3_wc2.cfg)
	{
		makevectors ('0 1 0' * self.v_angle_y);
		traceline (self.origin + v_forward * 230, self.origin + v_forward * 230 - '0 0 200', TRUE, self);
		setorigin (p, trace_endpos + '0 0 6');
		me = self;
		self = p;
		WC_Crash (world);
		self = me;
		return;
	}
	// aimed steeply down at the floor: he crashes right under you and the blast throws you up (a rocket jump)
	if (aim_z < 0 - WC_DOWN)
	{
		traceline (self.origin + '0 0 16', self.origin + '0 0 16' + aim * 150, TRUE, self);
		if (trace_fraction < 1 && !trace_startsolid)
		{
			setorigin (p, trace_endpos + trace_plane_normal * 6);
			me = self;
			self = p;
			WC_Crash (world);
			self = me;
		}
	}
};

string(float c) WC_Bar =
{
	local string s;
	local float i, n;

	s = "";
	n = floor (c * 12 + 0.5);
	i = 0;
	while (i < 12)
	{
		if (i < n)
			s = strcat (s, "#");
		else
			s = strcat (s, "-");
		i = i + 1;
	}
	return s;
};

string(float tier) WC_TierName =
{
	if (tier == 0)
		return "classic";
	if (tier == 1)
		return "napalm";
	if (tier == 2)
		return "plasma tornado";
	return "THERMONUCLEAR";
};

// fire pressed with the cannon out (FunGun_Attack): the charge begins
void() WC_Press =
{
	if (self.wc_charging || time < self.wc_cool)
		return;
	WC_PrecacheSprites ();
	self.wc_charging = time;
	self.wc_msg = 0;
	FG_Snd (self, CHAN_WEAPON, "wcannon/wc_charge.wav", 1, 1);
};

// every frame (FunGun_ViewFrame): charge while fire is held, launch on release or at full charge
void() WC_Frame =
{
	local float c, tier;
	local entity e;

	if (self.impulse == 125 && autocvar_sv_cheats)
	{
		// test (impulse 125; it was 82, which the sedan spawn in vehicles.qc never got to see): hurt the first Wheelman in the world as if somebody shot him (zz_wcannon2.cfg)
		self.impulse = 0;
		e = find (world, classname, "wc_shot");
		if (e)
			T_Damage (e, self, self, 60);
	}
	if (self.impulse == 126 && autocvar_sv_cheats)
	{
		// test (impulse 126; it was 83, the van spawn): shoot the first pickle in the world (zz_tone.cfg)
		self.impulse = 0;
		e = find (world, classname, "pickle");
		if (e)
			T_Damage (e, self, self, 30);
	}
	if (!self.wc_charging)
		return;
	if (self.health <= 0 || self.weapon != IT_FUNGUN || self.fg_sel != FG_WCANNON || time - self.wc_charging > WC_CHARGE_TIME + 1)
	{
		self.wc_charging = 0;
		sound (self, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NONE);
		return;
	}
	c = (time - self.wc_charging) / WC_CHARGE_TIME;
	if (c > 1)
		c = 1;
	if (!self.button0 || c >= 1)
	{
		WC_Fire (c);
		return;
	}
	self.punchangle_z = (random () - 0.5) * c * 3;
	if (time >= self.wc_msg)
	{
		self.wc_msg = time + 0.3;		// a centerprint is reliable traffic
		tier = floor (c * 4);
		if (tier > 3)
			tier = 3;
		centerprint (self, strcat ("WHEELMAN CANNON\n[", strcat (WC_Bar (c), strcat ("]\n", WC_TierName (tier)))));
	}
};
