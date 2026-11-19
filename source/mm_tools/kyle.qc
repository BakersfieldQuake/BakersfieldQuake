/*
================
THE POCKET KYLE (Fun Gun Slot 8, FG_KYLE = 8, BM_FG8 = 17, impulse 68, key Z / -)
See kyle_defs.qc for constants, skin layout, and sprite layout.
================
*/

void(entity jb, float is_temp) JB_InitEntity;
void() JB_AutopilotThink;
void() KY_RangeInit;

void() Kyle_Precache =
{
	precache_model ("progs/v_kyle.md3");
	precache_model ("progs/kyle_proj.spr32");
	precache_model ("progs/kyle_cash.spr32");
	precache_model ("progs/kyle_scissors.md3");
	precache_model ("progs/kyle_torpedo.md3");

	// User-voted Kyle voice winners (custom pitches baked cleanly; whoa_7 & whoa_10 cut!)
	precache_sound ("kyle/whoa_man.wav");
	precache_sound ("kyle/whoa_1.wav");
	precache_sound ("kyle/whoa_2.wav");
	precache_sound ("kyle/whoa_3.wav");
	precache_sound ("kyle/whoa_4.wav");
	precache_sound ("kyle/whoa_5.wav");
	precache_sound ("kyle/whoa_6.wav");
	precache_sound ("kyle/whoa_8.wav");
	precache_sound ("kyle/whoa_9.wav");
	precache_sound ("kyle/whoa_11.wav");
	precache_sound ("kyle/whoa_12.wav");

	// Action / Latch / Roam voices (ZERO "Will stole my clients" clips!)
	precache_sound ("kyle/kyle_hey.wav");
	precache_sound ("kyle/kyle_hey2.wav");
	precache_sound ("kyle/kyle_cut.wav");
	precache_sound ("kyle/kyle_cut2.wav");
	precache_sound ("kyle/kyle_hey_man.wav");

	// Scissor, Lock, Metallic Bounce & Cash SFX
	precache_sound ("kyle/snip_fast.wav");
	precache_sound ("kyle/snip_heavy.wav");
	precache_sound ("kyle/lock_tick.wav");
	precache_sound ("kyle/lock_ready.wav");
	precache_sound ("kyle/cash_register.wav");
	precache_sound ("kyle/cash_flutter.wav");
	precache_sound ("kyle/plane_whoosh.wav");
	precache_sound ("kyle/scissor_clang1.wav");
	precache_sound ("kyle/scissor_clang2.wav");
	precache_sound ("kyle/scissor_clang3.wav");

	if (mapname == "kyle_range")
		KY_RangeInit ();
};

// DRAW / PULL-OUT: whoa_06_double_warble @ 1.19x, whoa_02_wobble
void(entity e) KY_PlayWhoa =
{
	local float r, pitch;

	r = random ();
	pitch = 0.97 + random () * 0.06;
	if (r < 0.55)
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_6.wav", 0.98, pitch);
	else
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_2.wav", 0.96, pitch);
};

// BIRD LOCK-ON: whoa_05_long @ 1.35x, whoa_08_superman_doppler @ 1.35x
void(entity e) KY_PlayBirdLock =
{
	local float r, pitch;

	r = random ();
	pitch = 0.98 + random () * 0.04;
	if (r < 0.52)
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_5.wav", 0.98, pitch);
	else
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_8.wav", 0.98, pitch);
};

// THROW / SUPERMAN TORPEDO FLIGHT: whoa_08 @ 1.35x, whoa_06 @ 1.19x, whoa_09 @ 1.19x, whoa_02_wobble
void(entity e) KY_PlaySkyWhoa =
{
	local float r, pitch;

	r = random ();
	pitch = 0.97 + random () * 0.06;
	if (r < 0.30)
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_8.wav", 1.0, pitch);
	else if (r < 0.56)
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_6.wav", 1.0, pitch);
	else if (r < 0.80)
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_9.wav", 1.0, pitch);
	else
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_2.wav", 0.98, pitch);
};

// LATCH / CHOP: whoa_11 @ 1.13x, whoa_12, whoa_03_rise, whoa_01_short, edit_02_whoa_give_cut
void(entity e) KY_PlayLatch =
{
	local float r, pitch;

	r = random ();
	pitch = 0.97 + random () * 0.06;
	if (r < 0.24)
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_11.wav", 1.0, pitch);
	else if (r < 0.46)
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_12.wav", 1.0, pitch);
	else if (r < 0.66)
		FG_Snd (e, CHAN_VOICE, "kyle/kyle_cut2.wav", 1.0, pitch);
	else if (r < 0.84)
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_3.wav", 0.98, pitch);
	else
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_1.wav", 0.98, pitch);
};

// ROAM / CHASE: edit_01_hey_man_tight (primary!), plus classic Kyle/cut lines
void(entity e) KY_PlayLine =
{
	local float r, pitch;

	r = random ();
	pitch = 0.96 + random () * 0.08;
	if (r < 0.55)
		FG_Snd (e, CHAN_VOICE, "kyle/kyle_hey_man.wav", 0.98, pitch);
	else if (r < 0.72)
		FG_Snd (e, CHAN_VOICE, "kyle/kyle_cut.wav", 0.96, pitch);
	else if (r < 0.86)
		FG_Snd (e, CHAN_VOICE, "kyle/whoa_man.wav", 0.96, pitch);
	else
		FG_Snd (e, CHAN_VOICE, "kyle/kyle_hey.wav", 0.95, pitch);
};

// ---------------------------------------------------------------- realistic US currency particles

void() KY_CashRemove =
{
	if (self.ky_cash_qprev)
		self.ky_cash_qprev.ky_cash_qnext = self.ky_cash_qnext;
	else if (ky_cash_qhead == self)
		ky_cash_qhead = self.ky_cash_qnext;
	if (self.ky_cash_qnext)
		self.ky_cash_qnext.ky_cash_qprev = self.ky_cash_qprev;
	else if (ky_cash_qtail == self)
		ky_cash_qtail = self.ky_cash_qprev;
	self.ky_cash_qprev = world;
	self.ky_cash_qnext = world;
	ky_cash_count = ky_cash_count - 1;
	remove (self);
};

void() KY_CashRemoveOldest =
{
	local entity oself;

	if (ky_cash_qhead)
	{
		oself = self;
		self = ky_cash_qhead;
		KY_CashRemove ();
		self = oself;
	}
};

void() KY_CashThink =
{
	local float age, f, base, fps, sx, sy;

	age = time - self.fg_born;
	if (age >= 2.6 || pointcontents (self.origin) == CONTENT_SKY)
	{
		KY_CashRemove ();
		return;
	}
	if (age > 2.0)
		self.alpha = max (0.05, 1.0 - (age - 2.0) / 0.6);

	if (self.ky_cash_kind == 0)
	{
		// US $100 bill: airy sinusoidal paper flutter!
		base = 0;
		fps = 10;
		if (!(self.flags & FL_ONGROUND))
		{
			sx = sin (time * 8.0 + self.ky_cash_phase);
			sy = cos (time * 7.2 + self.ky_cash_phase);
			self.velocity_x = self.velocity_x * 0.92 + sx * 28;
			self.velocity_y = self.velocity_y * 0.92 + sy * 28;
			if (self.velocity_z < -55)
				self.velocity_z = -55;
		}
	}
	else if (self.ky_cash_kind == 1)
	{
		base = 8;		// 2024 Washington Silver Quarter
		fps = 16;
	}
	else
	{
		base = 16;		// 2024 Sacagawea Gold Dollar
		fps = 16;
	}

	f = floor (age * fps + self.ky_cash_phase);
	f = f - 8 * floor (f / 8);
	self.frame = base + f;
	self.nextthink = time + 0.05;
};

void(vector org, float count, float speed_mult) KY_SpawnCashBurst =
{
	local float i, r;
	local entity c;
	local vector dir;

	i = 0;
	while (i < count)
	{
		if (ky_cash_count >= KY_CASH_MAX)
			KY_CashRemoveOldest ();

		c = spawn ();
		c.classname = "kyle_cash";
		c.solid = SOLID_NOT;
		c.effects = EF_FULLBRIGHT;
		c.fg_born = time;
		c.ky_cash_phase = random () * 8;
		r = random ();
		if (r < 0.56)
		{
			c.ky_cash_kind = 0;		// US $100 bill (~10-13u wide)
			c.movetype = MOVETYPE_TOSS;
			c.gravity = 0.22;
			c.scale = 0.105 + random () * 0.035;
		}
		else if (r < 0.78)
		{
			c.ky_cash_kind = 1;		// 2024 Silver Quarter (~4-5.4u wide)
			c.movetype = MOVETYPE_BOUNCE;
			c.gravity = 0.75;
			c.bouncefactor = 0.55;
			c.scale = 0.062 + random () * 0.022;
		}
		else
		{
			c.ky_cash_kind = 2;		// 2024 Sacagawea Gold Dollar (~4.4-5.8u wide)
			c.movetype = MOVETYPE_BOUNCE;
			c.gravity = 0.75;
			c.bouncefactor = 0.55;
			c.scale = 0.068 + random () * 0.022;
		}

		setmodel (c, "progs/kyle_cash.spr32");
		setsize (c, VEC_ORIGIN, VEC_ORIGIN);
		dir_x = crandom ();
		dir_y = crandom ();
		dir_z = 0.55 + random () * 0.95;
		dir = normalize (dir);
		setorigin (c, org + dir * 10);
		c.velocity = dir * ((120 + random () * 190) * speed_mult);
		c.frame = c.ky_cash_kind * 8;
		c.think = KY_CashThink;
		c.nextthink = time + 0.04;

		c.ky_cash_qprev = ky_cash_qtail;
		c.ky_cash_qnext = world;
		if (ky_cash_qtail)
			ky_cash_qtail.ky_cash_qnext = c;
		else
			ky_cash_qhead = c;
		ky_cash_qtail = c;
		ky_cash_count = ky_cash_count + 1;
		i = i + 1;
	}
};

// ---------------------------------------------------------------- enemy & lock-on targeting

float(entity own, entity e) KY_IsValidTarget =
{
	if (e == world || bm_wasfreed (e))
		return FALSE;
	if (e.health <= 0 || !e.takedamage || e.solid == SOLID_NOT)
		return FALSE;
	if (e.classname == "misc_vehicle_johnbird")
	{
		if (e.jb_dying)
			return FALSE;
		if (e.jb_pilot == own && !autocvar_kyle_test)
			return FALSE;
		if (teamplay && e.jb_pilot != world && e.jb_pilot.team > 0 && e.jb_pilot.team == own.team)
			return FALSE;
		return TRUE;
	}
	if (e.classname == "player")
	{
		if (e == own)
			return (autocvar_kyle_test != 0);
		if (e.jb_vehicle != world)
			return FALSE;		// target the Winged John Bird vehicle itself!
		if (teamplay && e.team > 0 && e.team == own.team)
			return FALSE;
		return TRUE;
	}
	if (e.flags & FL_MONSTER)
		return TRUE;
	return FALSE;
};

// Returns TRUE if entity is an airborne bird, plane, sky vehicle, or flying enemy!
float(entity e) KY_IsSkyVehicle =
{
	if (e.classname == "misc_vehicle_johnbird")
		return TRUE;
	if (e.classname == "monster_floathead")
		return TRUE;
	if (e.classname == "player" && e.jp_on)
		return TRUE;
	return FALSE;
};

// Scans ONLY sky birds / airborne vehicles inside hairspray-counter range (<= KY_BIRD_LOCK_RANGE = 780u)!
// If a bird is spotted in the crosshair cone beyond 780u, sets ky_far_bird so CSQC shows "BIRD TOO FAR" cleanly!
entity(entity p) KY_FindLockTarget =
{
	local vector eye, delta;
	local entity e, best;
	local float best_score, dist, dot, score;

	makevectors (p.v_angle);
	eye = p.origin + p.view_ofs;
	best = world;
	best_score = -1;
	ky_far_bird = world;
	ky_far_dist = 0;

	// Scan Winged John Birds (hairspray-counter range <= 780u; sticky hysteresis cone once locking!)
	e = find (world, classname, "misc_vehicle_johnbird");
	while (e)
	{
		if (KY_IsValidTarget (p, e))
		{
			delta = (e.origin + '0 0 24') - eye;
			dist = vlen (delta);
			if (dist > 32 && dist <= 2400)
			{
				dot = normalize (delta) * v_forward;
				if (dot >= ((e == p.ky_lock_ent) ? 0.76 : 0.86))	// ~31 deg acquire, sticky ~40 deg track on diving birds!
				{
					traceline (eye, e.origin + '0 0 24', TRUE, p);
					if (trace_fraction >= 0.94)
					{
						if (dist <= ((e == p.ky_lock_ent) ? (KY_BIRD_LOCK_RANGE + 80) : KY_BIRD_LOCK_RANGE))
						{
							score = dot + 0.15;
							if (score > best_score)
							{
								best_score = score;
								best = e;
							}
						}
						else if (ky_far_bird == world || dist < ky_far_dist)
						{
							ky_far_bird = e;
							ky_far_dist = dist;
						}
					}
				}
			}
		}
		e = find (e, classname, "misc_vehicle_johnbird");
	}

	// Also allow locking onto flying Floatheads or airborne jetpackers within 780u!
	if (best == world)
	{
		e = findradius (eye, KY_BIRD_LOCK_RANGE);
		while (e)
		{
			if (e.classname != "misc_vehicle_johnbird" && KY_IsSkyVehicle (e) && KY_IsValidTarget (p, e))
			{
				delta = (e.origin + '0 0 18') - eye;
				dist = vlen (delta);
				if (dist > 32)
				{
					dot = normalize (delta) * v_forward;
					if (dot >= 0.92)
					{
						traceline (eye, e.origin + '0 0 18', TRUE, p);
						if (trace_fraction >= 0.94)
						{
							if (dot > best_score)
							{
								best_score = dot;
								best = e;
							}
						}
					}
				}
			}
			e = e.chain;
		}
	}
	return best;
};

// ---------------------------------------------------------------- projectile sprite & AI

float() KY_ShowAll =
{
	return TRUE;
};

// 8-direction x 8-frame + From-Below (8f) + From-Above (8f) sprite orientation (272f in progs/kyle_proj.spr32)
//   KY_ANIM_RUN      (0):   0..63   (13 FPS)
//   KY_ANIM_OVERHEAD (1):  64..127  (13 FPS)
//   KY_ANIM_FRONT    (2): 128..191  (14 FPS)
//   KY_ANIM_IDLE     (3): 192..255  ( 8 FPS)
//   KY_ANIM_BELOW    (4): 256..263  (13 FPS — looking UP from below / sky throw with scissors ABOVE him!)
//   KY_ANIM_ABOVE    (5): 264..271  (12 FPS — looking DOWN from above / bird's-eye!)
float() KY_ProjCustomize =
{
	local float rel, d, k, dt, base, fps, dz, horiz;
	local vector delta, eye;

	eye = other.origin + other.view_ofs;
	delta = eye - self.origin;
	dz = (self.origin_z + 28) - eye_z;
	delta_z = 0;
	horiz = vlen (delta);

	// Above / Below vertical perspective switching!
	// When thrown up into the sky (or viewed from below), show real studio From-Below view with scissors ABOVE him!
	if ((self.ky_sky_throw && dz > 14 && self.movetype == MOVETYPE_TOSS) || (dz > 44 && dz > horiz * 0.36))
	{
		k = floor ((time - self.ky_anim_t) * 14);
		k = k - 8 * floor (k / 8);
		self.frame = 256 + k;
		return TRUE;
	}
	// When viewed steeply from above (balcony, ledge, or flying Winged John Bird), show real From-Above view!
	if (dz < -56 && (0 - dz) > horiz * 0.45 && self.ky_mode != KY_MODE_LATCHED)
	{
		k = floor ((time - self.ky_anim_t) * 12);
		k = k - 8 * floor (k / 8);
		self.frame = 264 + k;
		return TRUE;
	}

	dt = time - self.fg_born;
	if (other == self.owner && dt < 0.48 && self.ky_mode != KY_MODE_LATCHED && self.ky_mode != KY_MODE_DYING)
	{
		// Slow, watchable Milky-style palm emergence: lifts off your open palm facing you, then twirls 360 deg!
		if (dt < 0)
			dt = 0;
		k = dt / 0.48;
		k = k * k * (3 - 2 * k);
		rel = 360 * k;
	}
	else
	{
		if (horiz > 8)
			rel = vectoyaw (delta) - self.angles_y;
		else
			rel = 0;
	}
	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 45.0 + 0.5);
	if (d >= 8)
		d = 0;

	if (self.ky_anim == KY_ANIM_OVERHEAD)
	{
		base = 64;
		fps = self.ky_sky_throw ? 15 : 13;
	}
	else if (self.ky_anim == KY_ANIM_FRONT)
	{
		base = 128;
		fps = 14;
	}
	else if (self.ky_anim == KY_ANIM_IDLE)
	{
		base = 192;
		fps = 8;
	}
	else
	{
		base = 0;
		fps = 13;
	}

	k = floor ((time - self.ky_anim_t) * fps);
	k = k - 8 * floor (k / 8);
	self.frame = base + d * 8 + k;
	return TRUE;
};

// ---------------------------------------------------------------- bouncing 3D chrome scissors on Kyle's death!

void() KY_ScissorTouch =
{
	local float spd, vol, r;

	if (other.classname == "kyle_scissor_gib")
		return;
	spd = vlen (self.velocity);
	if (spd < 38 || time < self.ky_clang_t)
		return;
	self.ky_clang_t = time + 0.14;
	vol = bound (0.25, spd / 280, 0.95);
	r = random ();
	if (r < 0.34)
		FG_Snd (self, CHAN_AUTO, "kyle/scissor_clang1.wav", vol, 0.94 + random () * 0.14);
	else if (r < 0.68)
		FG_Snd (self, CHAN_AUTO, "kyle/scissor_clang2.wav", vol, 0.94 + random () * 0.14);
	else
		FG_Snd (self, CHAN_AUTO, "kyle/scissor_clang3.wav", vol, 0.94 + random () * 0.14);

	// Damp spin gradually as it bounces and settles flat on the ground
	self.avelocity = self.avelocity * 0.72;
};

void() KY_ScissorThink =
{
	local float age, f;

	age = time - self.fg_born;
	if (age >= 6.5 || pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	if (age > 5.0)
		self.alpha = max (0.05, 1.0 - (age - 5.0) / 1.5);
	// Snap blades while tumbling, then rest slightly open once settled
	if (vlen (self.velocity) > 35)
	{
		f = floor (age * 16 + self.ky_cash_phase);
		self.frame = f - 8 * floor (f / 8);
	}
	else
	{
		self.avelocity = '0 0 0';
		self.angles_x = 0;
		self.angles_z = 0;
	}
	self.nextthink = time + 0.05;
};

void(vector org, float count) KY_SpawnBouncingScissors =
{
	local float i;
	local entity sc;
	local vector dir;

	i = 0;
	while (i < count)
	{
		sc = spawn ();
		sc.classname = "kyle_scissor_gib";
		sc.movetype = MOVETYPE_BOUNCE;
		sc.solid = SOLID_TRIGGER;
		sc.gravity = 0.85;
		sc.bouncefactor = 0.62;
		sc.scale = 1.05 + random () * 0.20;
		sc.fg_born = time;
		sc.ky_cash_phase = random () * 8;
		sc.ky_clang_t = time + 0.05;
		setmodel (sc, "progs/kyle_scissors.md3");
		setsize (sc, '-8 -8 -4', '8 8 4');
		dir_x = crandom ();
		dir_y = crandom ();
		dir_z = 0.65 + random () * 0.95;
		dir = normalize (dir);
		setorigin (sc, org + dir * 10);
		sc.velocity = dir * (175 + random () * 165);
		sc.angles_y = random () * 360;
		sc.avelocity_x = crandom () * 520;
		sc.avelocity_y = crandom () * 520;
		sc.avelocity_z = crandom () * 460;
		sc.touch = KY_ScissorTouch;
		sc.think = KY_ScissorThink;
		sc.nextthink = time + 0.05;
		i = i + 1;
	}
};

void() KY_Pop =
{
	if (self.ky_done)
		return;
	self.ky_done = TRUE;
	remove (self);
};

// Comical death animation: brief 0.26s flailing pop-swell -> EXPLODES into realistic US money + 3 bouncing 3D chrome scissors!
void() KY_ProjDie =
{
	if (self.ky_done || self.ky_mode == KY_MODE_DYING)
		return;
	self.ky_mode = KY_MODE_DYING;
	self.ky_die_t = time + 0.26;
	self.ky_anim = KY_ANIM_OVERHEAD;
	self.ky_anim_t = time;
	self.ky_sky_throw = FALSE;
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	FG_Snd (self, CHAN_VOICE, "kyle/whoa_4.wav", 1.0, 1.18);
	FG_Snd (self, CHAN_WEAPON, "kyle/snip_heavy.wav", 0.9, 1.12);
	self.nextthink = time + 0.03;
};

void(entity targ) KY_StartLatch =
{
	if (self.model != "progs/kyle_proj.spr32")
	{
		setmodel (self, "progs/kyle_proj.spr32");
		setsize (self, '-14 -14 0', '14 14 58');
		self.customizeentityforclient = KY_ProjCustomize;
	}
	self.scale = KY_SCALE;
	self.angles_x = 0;
	self.angles_z = 0;
	self.ky_mode = KY_MODE_LATCHED;
	self.ky_targ = targ;
	self.ky_latch_end = time + KY_LATCH_TIME;
	self.ky_chop_t = time + 0.06;
	self.ky_voice_t = time + 0.15;
	self.ky_anim = KY_ANIM_FRONT;
	self.ky_anim_t = time;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.ky_latch_side = (random () < 0.5) ? -1 : 1;
	FG_Snd (self, CHAN_WEAPON, "kyle/snip_heavy.wav", 0.95, 1.0);
	KY_PlayLatch (self);
	if (targ.classname == "player")
		centerprint (targ, "KYLE WANTS HIS 50% CUT! SHOOT HIM OFF!\n");
	else if (targ.classname == "misc_vehicle_johnbird" && targ.jb_pilot != world)
		centerprint (targ.jb_pilot, "KYLE IS CHOPPING YOUR BIRD'S WINGS! (-50% CUT!)\n");
};

void() KY_EnterGroundStep =
{
	if (self.model != "progs/kyle_proj.spr32")
	{
		setmodel (self, "progs/kyle_proj.spr32");
		setsize (self, '-14 -14 0', '14 14 58');
		self.customizeentityforclient = KY_ProjCustomize;
	}
	self.movetype = MOVETYPE_STEP;
	self.solid = SOLID_SLIDEBOX;
	self.velocity = '0 0 0';
	self.angles_x = 0;
	self.angles_z = 0;
	self.scale = KY_SCALE;
	self.ky_sky_throw = FALSE;
	if (self.ky_mode != KY_MODE_WANDER)
		self.ky_mode = KY_MODE_RUNNER;
	self.ky_anim = KY_ANIM_RUN;
	self.ky_anim_t = time;
};

void(float want_yaw, float step_dist, float update_wander) KY_GroundStep =
{
	local float diff;

	diff = want_yaw - self.angles_y;
	while (diff > 180)
		diff = diff - 360;
	while (diff < -180)
		diff = diff + 360;
	self.angles_y = self.angles_y + diff * 0.38;
	while (self.angles_y >= 360)
		self.angles_y = self.angles_y - 360;
	while (self.angles_y < 0)
		self.angles_y = self.angles_y + 360;

	if (!walkmove (self.angles_y, step_dist))
	{
		if (walkmove (self.angles_y + 42, step_dist * 0.88))
		{
			self.angles_y = self.angles_y + 32;
			if (update_wander)
				self.ky_wand_yaw = self.angles_y;
		}
		else if (walkmove (self.angles_y - 42, step_dist * 0.88))
		{
			self.angles_y = self.angles_y - 32;
			if (update_wander)
				self.ky_wand_yaw = self.angles_y;
		}
		else
		{
			// Blocked by corner/wall -> turn around briskly and keep moving!
			self.angles_y = self.angles_y + 115 + random () * 90;
			while (self.angles_y >= 360)
				self.angles_y = self.angles_y - 360;
			if (update_wander)
				self.ky_wand_yaw = self.angles_y;
			walkmove (self.angles_y, step_dist * 0.8);
		}
	}
};

void() KY_ProjTouch =
{
	if (self.ky_done || self.ky_mode == KY_MODE_LATCHED)
		return;
	if (other == self.owner && !autocvar_kyle_test)
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		KY_Pop ();
		return;
	}
	if (KY_IsValidTarget (self.owner, other))
	{
		KY_StartLatch (other);
		return;
	}
	// Hit floor or wall while flying or tossed -> switch cleanly to MOVETYPE_STEP ground running!
	if (other == world || other.solid == SOLID_BSP)
	{
		if (self.ky_mode == KY_MODE_HOMING)
		{
			if (trace_plane_normal_z > 0.5 || time > self.fg_born + 0.6)
			{
				KY_EnterGroundStep ();
			}
			else
			{
				// Slide/deflect off walls cleanly while homing
				self.velocity = self.velocity - trace_plane_normal * (self.velocity * trace_plane_normal) * 1.4;
			}
		}
		else if (self.movetype == MOVETYPE_TOSS && trace_plane_normal_z > 0.5)
		{
			KY_EnterGroundStep ();
		}
	}
};

entity() KY_FindNearbyEnemy =
{
	local entity e, best;
	local float bd, d;

	best = world;
	bd = 720;
	e = findradius (self.origin, bd);
	while (e)
	{
		if (KY_IsValidTarget (self.owner, e))
		{
			d = vlen (e.origin - self.origin);
			if (d < bd)
			{
				bd = d;
				best = e;
			}
		}
		e = e.chain;
	}
	return best;
};

void() KY_ProjThink =
{
	local entity targ, e;
	local vector aim, pos, desired;
	local float dist, spd, dmg, is_bird, prev_hp, step_dist;

	if (self.ky_done)
		return;

	// ---- MODE 6: COMICAL DEATH POP -> EXPLODES INTO US MONEY + 1 BOUNCING 3D CHROME SCISSORS! ----
	if (self.ky_mode == KY_MODE_DYING)
	{
		if (time >= self.ky_die_t)
		{
			self.ky_done = TRUE;
			KY_SpawnCashBurst (self.origin + '0 0 26', 14, 1.25);
			KY_SpawnBouncingScissors (self.origin + '0 0 28', 1);
			FG_Snd (self, CHAN_AUTO, "kyle/cash_register.wav", 0.90, 1.0);
			FG_Snd (self, CHAN_WEAPON, "kyle/cash_flutter.wav", 0.85, 1.02);
			remove (self);
			return;
		}
		// Quick comical swell & rapid spin right before exploding into bills, coins & clanging scissors!
		spd = 1.0 - (self.ky_die_t - time) / 0.26;
		self.scale = KY_SCALE * (1.0 + 0.42 * spd);
		self.angles_y = self.angles_y + 48;
		if (self.angles_y >= 360)
			self.angles_y = self.angles_y - 360;
		self.nextthink = time + 0.03;
		return;
	}

	if (self.owner == world || bm_wasfreed (self.owner))
	{
		KY_Pop ();
		return;
	}
	if (pointcontents (self.origin) == CONTENT_LAVA || pointcontents (self.origin) == CONTENT_SLIME)
	{
		KY_Pop ();
		return;
	}

	// ---- MODE 3: PERIPHERAL LATCH (PLAYER OR WINGED JOHN BIRD!) ----
	if (self.ky_mode == KY_MODE_LATCHED)
	{
		targ = self.ky_targ;
		if (!KY_IsValidTarget (self.owner, targ) || time >= self.ky_latch_end)
		{
			KY_Pop ();
			return;
		}
		is_bird = (targ.classname == "misc_vehicle_johnbird");
		if (is_bird)
		{
			makevectors (targ.angles);
			pos = targ.origin + v_right * (34 * self.ky_latch_side) + v_forward * 14 - '0 0 18';
			setorigin (self, pos);
			self.angles_y = targ.angles_y + 180;
			// Slow down John Bird's wings while Kyle clings on!
			targ.jb_slow_t = max (targ.jb_slow_t, time + 0.9);
		}
		else
		{
			// Sit right in the victim's forward-side peripheral vision (~34u ahead, +/-22u left/right)!
			makevectors (targ.v_angle);
			desired = targ.origin + targ.view_ofs + v_forward * 34 + v_right * (22 * self.ky_latch_side) - '0 0 28';
			traceline (targ.origin + targ.view_ofs, desired, TRUE, self);
			if (trace_fraction < 1)
				pos = trace_endpos - normalize (desired - (targ.origin + targ.view_ofs)) * 10;
			else
				pos = desired;
			setorigin (self, pos);
			self.angles_y = targ.v_angle_y + 180;
		}

		// Alternate frantic Front Lunge-Chop & Overhead Jump-Chop every 1.6s!
		if (floor ((time - self.fg_born) / 1.6) - 2 * floor (floor ((time - self.fg_born) / 1.6) / 2) == 0)
			self.ky_anim = KY_ANIM_FRONT;
		else
			self.ky_anim = KY_ANIM_OVERHEAD;

		if (time >= self.ky_chop_t)
		{
			self.ky_chop_t = time + KY_CHOP_INTERVAL;
			dmg = is_bird ? (KY_CHOP_DMG * 2) : KY_CHOP_DMG;
			prev_hp = targ.health;
			fg_inflicting = FG_KYLE;
			T_Damage (targ, self, self.owner, dmg);
			fg_inflicting = 0;
			FG_Snd (self, CHAN_WEAPON, "kyle/snip_fast.wav", 0.9, 0.94 + random () * 0.14);
			// ONLY erupt realistic US $100 bills & 2024 coins when Kyle successfully deals damage!
			if (bm_wasfreed (targ) || targ.health < prev_hp)
			{
				KY_SpawnCashBurst (targ.origin + '0 0 18', 5, 0.95);
				if (random () < 0.45)
					FG_Snd (self, CHAN_AUTO, "kyle/cash_flutter.wav", 0.55, 0.95 + random () * 0.10);
			}
			if (!bm_wasfreed (targ) && targ.classname == "player")
			{
				targ.punchangle_x = crandom () * 2.4;
				targ.punchangle_z = self.ky_latch_side * 2.8;
			}
		}
		if (time >= self.ky_voice_t)
		{
			self.ky_voice_t = time + 1.55 + random () * 0.7;
			KY_PlayLatch (self);
		}
		self.nextthink = time + 0.03;
		return;
	}

	// Lifetime check for non-latched Kyle
	if (time >= self.fg_born + KY_LIFE)
	{
		KY_Pop ();
		return;
	}

	// ---- MODE 1: BARREL-ROLLING SUPERMAN-TORPEDO KYLE (Slowly chasing the Bird at bird_speed + 85 u/s!) ----
	if (self.ky_mode == KY_MODE_HOMING)
	{
		if (time - self.fg_born < 0.35)
		{
			spd = (time - self.fg_born) / 0.35;
			self.scale = 0.68 + (1.35 - 0.68) * (spd * spd * (3 - 2 * spd));
		}
		else
			self.scale = 1.35;

		targ = self.ky_targ;
		if (KY_IsValidTarget (self.owner, targ) && time < self.fg_born + 10.0)
		{
			is_bird = (targ.classname == "misc_vehicle_johnbird");
			aim = (targ.origin + (is_bird ? '0 0 18' : '0 0 12')) - self.origin;
			dist = vlen (aim);
			if (dist <= (is_bird ? 92 : 62))
			{
				KY_StartLatch (targ);
				self.nextthink = time + 0.03;
				return;
			}
			// Dynamic Bird-Counter Speed: ONLY a little bit faster than the bird (+85 u/s closing speed!)
			// Slow, tense, hilarious torpedo chase vs diving/cruising birds; full-carve fleeing birds can juke!
			spd = vlen (targ.velocity) + 85;
			if (is_bird)
				spd = bound (410, spd, 920);
			else
				spd = bound (320, spd, 620);
			self.velocity = normalize (self.velocity * 0.72 + normalize (aim) * spd * 0.28) * spd;

			// Laying horizontally on his stomach Superman-style with giant 3D chrome scissors straight out in front,
			// SPINNING SLOWLY IN A FLAT HORIZONTAL CIRCLE (~205 deg/sec = 1 slow full circle every ~1.75s)
			// while cruising steadily after the Winged John Bird at bird_speed + 85 u/s!
			desired = vectoangles (self.velocity);
			if (desired_x > 180)
				desired_x = desired_x - 360;
			self.angles_x = bound (-14, (0 - desired_x) * 0.28, 14);
			self.angles_y = (time - self.fg_born) * 205;
			self.angles_y = self.angles_y - 360 * floor (self.angles_y / 360);
			self.angles_z = 0;
			// Animate 3D chrome scissors snapping straight out in front (frames 0..7 @ 14 FPS)!
			dist = floor ((time - self.fg_born) * 14);
			self.frame = dist - 8 * floor (dist / 8);
		}
		else
		{
			// Target died, escaped, or torpedo fuel ran out -> drop back to Ground-Runner Kyle!
			setmodel (self, "progs/kyle_proj.spr32");
			setsize (self, '-14 -14 0', '14 14 58');
			self.customizeentityforclient = KY_ProjCustomize;
			self.scale = KY_SCALE;
			self.angles_x = 0;
			self.angles_z = 0;
			self.ky_mode = KY_MODE_RUNNER;
			self.ky_anim = KY_ANIM_FRONT;
			self.ky_anim_t = time;
			self.movetype = MOVETYPE_TOSS;
			self.gravity = 0.48;
		}
		if (time >= self.ky_air_snip_t)
		{
			self.ky_air_snip_t = time + 0.22;
			FG_Snd (self, CHAN_WEAPON, "kyle/snip_fast.wav", 0.78, 1.00 + random () * 0.12);
		}
		if (time >= self.ky_voice_t)
		{
			self.ky_voice_t = time + 2.0 + random () * 0.8;
			KY_PlaySkyWhoa (self);
		}
		self.nextthink = time + 0.04;
		return;
	}

	// ---- AIRBORNE THROW FLIGHT (Watchable Sky Overhead Chop vs Forward Lunge Chop!) ----
	if (self.movetype == MOVETYPE_TOSS)
	{
		if (time - self.fg_born < 0.45)
		{
			spd = (time - self.fg_born) / 0.45;
			self.scale = 0.24 + (KY_SCALE - 0.24) * (spd * spd * (3 - 2 * spd));
		}
		else
			self.scale = KY_SCALE;

		if ((self.flags & FL_ONGROUND) || time > self.fg_born + 5.5)
		{
			KY_EnterGroundStep ();
		}
		else
		{
			if (self.ky_sky_throw)
			{
				// Soaring lazily high in the sky: giant scissors ABOVE him furiously chopping & kicking!
				self.ky_anim = KY_ANIM_OVERHEAD;
				if (time - self.fg_born >= 0.48)
				{
					self.angles_y = self.angles_y + 10;
					if (self.angles_y >= 360)
						self.angles_y = self.angles_y - 360;
				}
				if (time >= self.ky_air_snip_t)
				{
					self.ky_air_snip_t = time + 0.24;
					FG_Snd (self, CHAN_WEAPON, "kyle/snip_fast.wav", 0.78, 1.05 + random () * 0.12);
				}
				// Anti-air intercept! If lobbed up near a flying Winged John Bird or enemy, transform into Superman Torpedo & hunt it!
				e = KY_FindNearbyEnemy ();
				if (e != world && vlen (e.origin - self.origin) <= 460)
				{
					setmodel (self, "progs/kyle_torpedo.md3");
					setsize (self, '-16 -16 -14', '16 16 14');
					self.customizeentityforclient = KY_ShowAll;
					self.ky_mode = KY_MODE_HOMING;
					self.ky_targ = e;
					self.ky_sky_throw = FALSE;
					self.movetype = MOVETYPE_FLYMISSILE;
					self.scale = 1.25;
					self.nextthink = time + 0.03;
					return;
				}
			}
			else
			{
				// Forward throw: smooth watchable arc doing front scissor lunges mid-air!
				self.ky_anim = KY_ANIM_FRONT;
				if (vlen (self.velocity) > 30)
					self.angles_y = vectoyaw (self.velocity);
				if (time >= self.ky_air_snip_t)
				{
					self.ky_air_snip_t = time + 0.26;
					FG_Snd (self, CHAN_WEAPON, "kyle/snip_fast.wav", 0.65, 0.96 + random () * 0.10);
				}
				e = KY_FindNearbyEnemy ();
				if (e != world && vlen (e.origin - self.origin) <= 68)
				{
					self.scale = KY_SCALE;
					KY_StartLatch (e);
					self.nextthink = time + 0.03;
					return;
				}
			}
			self.nextthink = time + 0.04;
			return;
		}
	}

	// ---- MODE 2 & 5: ACTIVE GROUND RUNNER & ROAMING KYLE (MOVETYPE_STEP + walkmove) ----
	e = KY_FindNearbyEnemy ();
	if (e != world)
	{
		self.ky_mode = KY_MODE_RUNNER;
		if (self.ky_anim != KY_ANIM_RUN)
		{
			self.ky_anim = KY_ANIM_RUN;
			self.ky_anim_t = time;
		}
		aim = e.origin - self.origin;
		dist = vlen (aim);
		if (dist <= 62)
		{
			KY_StartLatch (e);
			self.nextthink = time + 0.03;
			return;
		}
		aim_z = 0;
		if (vlen (aim) > 4)
			KY_GroundStep (vectoyaw (aim), 13.8, FALSE);		// ~275 u/s readable sprint!
		if (time >= self.ky_voice_t)
		{
			self.ky_voice_t = time + 1.8 + random () * 0.8;
			KY_PlayLine (self);
		}
		self.nextthink = time + 0.05;
		return;
	}

	// No enemies nearby -> actively walk & run around the map looking for people!
	if (self.ky_mode != KY_MODE_WANDER)
	{
		self.ky_mode = KY_MODE_WANDER;
		self.ky_anim = KY_ANIM_RUN;
		self.ky_anim_t = time;
		self.ky_wand_yaw = self.angles_y;
		self.ky_wand_t = time + 2.8 + random () * 1.8;
	}

	if (time >= self.ky_wand_t)
	{
		if (self.ky_anim == KY_ANIM_IDLE)
		{
			// Take off running in a new direction!
			self.ky_anim = KY_ANIM_RUN;
			self.ky_anim_t = time;
			self.ky_wand_yaw = self.angles_y + (random () - 0.5) * 180;
			self.ky_wand_t = time + 2.8 + random () * 2.2;
		}
		else if (random () < 0.35)
		{
			// Brief funny businessman shrug & look around, then run again!
			self.ky_anim = KY_ANIM_IDLE;
			self.ky_anim_t = time;
			self.ky_wand_t = time + 1.1 + random () * 0.7;
			KY_PlayLine (self);
		}
		else
		{
			// Pick a fresh roaming direction and keep running!
			self.ky_wand_yaw = self.angles_y + (random () - 0.5) * 160;
			self.ky_wand_t = time + 2.4 + random () * 2.0;
		}
	}

	if (self.ky_anim == KY_ANIM_RUN)
	{
		// Gentle playful curve while roaming + automatic wall/stair navigation
		self.ky_wand_yaw = self.ky_wand_yaw + (random () - 0.5) * 10;
		step_dist = 10.5;		// ~210 u/s readable energetic run!
		KY_GroundStep (self.ky_wand_yaw, step_dist, TRUE);
		if (time >= self.ky_voice_t)
		{
			self.ky_voice_t = time + 2.6 + random () * 1.6;
			KY_PlayLine (self);
		}
	}
	self.nextthink = time + 0.05;
};

void(entity p) KY_EnforceCap =
{
	local entity e, oldest;
	local float n;

	n = 0;
	oldest = world;
	e = find (world, classname, "kyle_proj");
	while (e)
	{
		if (e.owner == p && !e.ky_done)
		{
			n = n + 1;
			if (!oldest || e.fg_born < oldest.fg_born)
				oldest = e;
		}
		e = find (e, classname, "kyle_proj");
	}
	if (n >= KY_MAX_ACTIVE && oldest != world)
	{
		e = self;
		self = oldest;
		KY_Pop ();
		self = e;
	}
};

void(entity p, float is_homing, entity targ, float power) KY_Launch =
{
	local entity k;
	local vector eye, hand_want, org, vel;
	local float spd, is_sky;

	KY_EnforceCap (p);
	makevectors (p.v_angle);
	eye = p.origin + p.view_ofs;
	// Open-palm emergence: spawn cleanly ahead of your extended right throwing hand so he is visible from frame 1!
	hand_want = eye + v_forward * 44 + v_right * 11 - v_up * 2.0;
	tracebox (eye, '-12 -12 0', '12 12 40', hand_want, TRUE, p);
	org = trace_endpos;

	is_sky = (p.v_angle_x < -12);
	power = bound (0, power, 1);

	k = spawn ();
	k.classname = "kyle_proj";
	k.owner = p;
	k.solid = SOLID_BBOX;
	k.takedamage = DAMAGE_AIM;
	k.health = KY_HEALTH;
	k.th_die = KY_ProjDie;
	k.effects = EF_FULLBRIGHT;
	k.fg_born = time;
	k.ky_anim_t = time;
	k.ky_trail_t = time + 0.14;
	k.ky_air_snip_t = time + 0.14;
	k.ky_voice_t = time + 1.0;
	k.angles_y = p.v_angle_y;
	k.ky_wand_yaw = p.v_angle_y;
	k.ky_wand_t = time + 2.8 + random () * 1.6;

	if (is_homing && KY_IsValidTarget (p, targ))
	{
		// SPINNING HORIZONTAL SUPERMAN-TORPEDO KYLE! (Horizontal belly-down w/ 3D snapping scissors straight ahead!)
		setmodel (k, "progs/kyle_torpedo.md3");
		setsize (k, '-16 -16 -14', '16 16 14');
		setorigin (k, org);
		k.scale = 0.68;
		k.ky_mode = KY_MODE_HOMING;
		k.ky_anim = KY_ANIM_OVERHEAD;
		k.ky_sky_throw = FALSE;
		k.ky_targ = targ;
		k.movetype = MOVETYPE_FLYMISSILE;
		spd = bound (410, vlen (targ.velocity) + 85, 920);
		vel = normalize ((targ.origin + '0 0 18') - org);
		k.velocity = vel * spd;
		k.angles_x = 0;
		k.angles_y = vectoyaw (vel);
		k.angles_z = 0;
		// CRITICAL: must return TRUE (SUB_Null returns 0 = engine hides entity from every client!)
		k.customizeentityforclient = KY_ShowAll;
		FG_Snd (p, CHAN_AUTO, "kyle/plane_whoosh.wav", 0.92, 0.94);
		FG_Snd (p, CHAN_WEAPON, "kyle/snip_heavy.wav", 0.78, 1.05);
		KY_PlaySkyWhoa (p);
		p.punchangle_x = -3.8;
		p.punchangle_z = 2.2;
	}
	else if (is_sky)
	{
		// SKY THROW: wind-up power scales throw height/distance! Slow floaty arc w/ scissors ABOVE him!
		setmodel (k, "progs/kyle_proj.spr32");
		setsize (k, '-14 -14 0', '14 14 58');
		setorigin (k, org);
		k.scale = 0.24;
		k.ky_mode = KY_MODE_RUNNER;
		k.ky_anim = KY_ANIM_OVERHEAD;
		k.ky_sky_throw = TRUE;
		k.movetype = MOVETYPE_TOSS;
		k.gravity = 0.30;
		vel = v_forward * (195 + 185 * power) + '0 0 1' * (170 + 120 * power);
		k.velocity = vel;
		k.customizeentityforclient = KY_ProjCustomize;
		FG_Snd (p, CHAN_AUTO, "kyle/plane_whoosh.wav", 0.88, 1.12);
		FG_Snd (p, CHAN_WEAPON, "kyle/snip_heavy.wav", 0.76, 1.12);
		KY_PlaySkyWhoa (p);
		p.punchangle_x = -3.6 - 1.4 * power;
		p.punchangle_z = 2.2;
	}
	else
	{
		// FORWARD / DIRECT THROW: quick tap = slow close lob (195 u/s); full windup = long heroic throw (480 u/s)!
		setmodel (k, "progs/kyle_proj.spr32");
		setsize (k, '-14 -14 0', '14 14 58');
		setorigin (k, org);
		k.scale = 0.24;
		k.ky_mode = KY_MODE_RUNNER;
		k.ky_anim = KY_ANIM_FRONT;
		k.ky_sky_throw = FALSE;
		k.movetype = MOVETYPE_TOSS;
		k.gravity = 0.42;
		vel = v_forward * (195 + 285 * power) + '0 0 1' * (115 + 75 * power);
		k.velocity = vel;
		k.customizeentityforclient = KY_ProjCustomize;
		FG_Snd (p, CHAN_AUTO, "kyle/plane_whoosh.wav", 0.82, 1.00 + 0.14 * power);
		FG_Snd (p, CHAN_WEAPON, "kyle/snip_fast.wav", 0.70, 1.02);
		KY_PlaySkyWhoa (p);
		p.punchangle_x = -2.6 - 1.6 * power;
		p.punchangle_z = 1.8;
	}

	k.touch = KY_ProjTouch;
	k.think = KY_ProjThink;
	k.nextthink = time + 0.03;
};

// ---------------------------------------------------------------- player weapon controls

void(entity p) KY_ResetPlayer =
{
	p.ky_locking = 0;
	p.ky_lock_prog = 0;
	p.ky_windup = 0;
	p.ky_bird_locking = FALSE;
	p.ky_lock_ready = FALSE;
	p.ky_lock_ent = world;
	p.ky_throw_at = 0;
	p.ky_fire_t = 0;
	p.ky_threw_t = 0;
	p.ky_draw_t = 0;
	p.ky_cool = 0;
	p.ky_empty = FALSE;
	p.ky_pending_homing = FALSE;
	p.ky_pending_power = 0;
	p.ky_pending_targ = world;
	p.ky_st_mode = 0;
	p.ky_st_prog = 0;
	p.ky_st_dist = 0;
};

void(entity p) KY_CleanupOwner =
{
	local entity e, nx, oself;

	e = find (world, classname, "kyle_proj");
	while (e)
	{
		nx = find (e, classname, "kyle_proj");
		if (e.owner == p)
		{
			oself = self;
			self = e;
			KY_Pop ();
			self = oself;
		}
		e = nx;
	}
};

void() KY_Press =
{
	if (self.ky_locking > 0 || self.ky_throw_at > 0 || time < self.ky_cool)
		return;
	self.ky_locking = time;
	self.ky_lock_prog = 0;
	self.ky_windup = 0;
	self.ky_bird_locking = FALSE;
	self.ky_lock_ready = FALSE;
	self.ky_lock_ent = world;
	self.ky_lock_snip_t = time + 0.05;
	self.ky_lock_tick_t = time + 0.12;
	self.ky_lock_msg_t = 0;
	self.bm_lastshot = time + 1.5;
	self.attack_finished = time + 0.12;
};

void() KY_Frame =
{
	local float held, req_t, ammo, d;
	local entity t;
	local vector tp;

	// Complete delayed throw launch right as fingers snap open!
	if (self.health <= 0)
	{
		self.ky_throw_at = 0;
		self.ky_locking = 0;
		self.ky_st_mode = 0;
		self.ky_st_prog = 0;
		return;
	}
	if (self.ky_throw_at > 0 && time >= self.ky_throw_at)
	{
		self.ky_throw_at = 0;
		self.ky_threw_t = time;
		KY_Launch (self, self.ky_pending_homing, self.ky_pending_targ, self.ky_pending_power);
		self.ky_pending_homing = FALSE;
		self.ky_pending_power = 0;
		self.ky_pending_targ = world;
	}

	if (!self.ky_locking)
	{
		self.ky_st_mode = 0;
		self.ky_st_prog = 0;
		return;
	}

	// Abort if switched weapon
	if (self.weapon != IT_FUNGUN || self.fg_sel != FG_KYLE)
	{
		self.ky_locking = 0;
		self.ky_lock_prog = 0;
		self.ky_windup = 0;
		self.ky_bird_locking = FALSE;
		self.ky_lock_ent = world;
		self.ky_st_mode = 0;
		self.ky_st_prog = 0;
		return;
	}

	held = time - self.ky_locking;
	self.bm_lastshot = time + 1.0;

	// Frantic scissor SNIP SFX while holding to lock or wind up!
	if (time >= self.ky_lock_snip_t)
	{
		self.ky_lock_snip_t = time + (self.ky_bird_locking ? 0.18 : 0.24);
		FG_Snd (self, CHAN_WEAPON, "kyle/snip_fast.wav", 0.56, 0.96 + 0.20 * max (self.ky_lock_prog, self.ky_windup));
	}

	// Dual Hold-Fire Behavior:
	//   A) Aiming at a Winged John Bird / sky vehicle INSIDE hairspray-counter range (<= 780u) -> DEDICATED BIRD LOCK-ON!
	//   B) Aiming anywhere else (or bird > 780u away) -> WIND UP THROW POWER to throw Kyle farther!
	t = KY_FindLockTarget (self);
	if (t != world)
	{
		if (!self.ky_bird_locking && time >= self.ky_lock_snd_t)
		{
			self.ky_lock_snd_t = time + 1.25;
			KY_PlayBirdLock (self);
		}
		self.ky_bird_locking = TRUE;
		if (t != self.ky_lock_ent)
		{
			self.ky_lock_ent = t;
			self.ky_lock_prog = 0;
			self.ky_lock_ready = FALSE;
		}
		req_t = (t.classname == "misc_vehicle_johnbird") ? KY_LOCK_BIRD_TIME : KY_LOCK_TIME;
		self.ky_lock_prog = min (1.0, self.ky_lock_prog + frametime / req_t);
		tp = t.origin + '0 0 24';
		d = floor (vlen (tp - (self.origin + self.view_ofs)));
		self.ky_st_dist = d;
		self.ky_st_tx = floor (tp_x);
		self.ky_st_ty = floor (tp_y);
		self.ky_st_tz = floor (tp_z);
		self.ky_st_prog = floor (self.ky_lock_prog * 100);
		if (self.ky_lock_prog >= 1.0)
		{
			self.ky_st_mode = 3;
			if (!self.ky_lock_ready)
			{
				self.ky_lock_ready = TRUE;
				FG_Snd (self, CHAN_AUTO, "kyle/lock_ready.wav", 0.90, 1.0);
			}
		}
		else
		{
			self.ky_st_mode = 2;
			if (time >= self.ky_lock_tick_t)
			{
				self.ky_lock_tick_t = time + 0.13;
				FG_Snd (self, CHAN_AUTO, "kyle/lock_tick.wav", 0.55, 0.90 + 0.40 * self.ky_lock_prog);
			}
		}
	}
	else
	{
		self.ky_bird_locking = FALSE;
		self.ky_lock_ent = world;
		self.ky_lock_prog = 0;
		self.ky_lock_ready = FALSE;
		// Wind up throw power smoothly over KY_WINDUP_MAX_T (1.10s) to throw Kyle farther!
		self.ky_windup = min (1.0, held / KY_WINDUP_MAX_T);
		if (ky_far_bird != world)
		{
			// Bird spotted in crosshair, but TOO FAR (>780u hairspray-counter range)!
			tp = ky_far_bird.origin + '0 0 24';
			self.ky_st_mode = 4;
			self.ky_st_dist = floor (ky_far_dist);
			self.ky_st_tx = floor (tp_x);
			self.ky_st_ty = floor (tp_y);
			self.ky_st_tz = floor (tp_z);
			self.ky_st_prog = floor (self.ky_windup * 100);
		}
		else if (held >= 0.14)
		{
			self.ky_st_mode = 1;
			self.ky_st_prog = floor (self.ky_windup * 100);
			self.ky_st_dist = 0;
		}
		else
		{
			self.ky_st_mode = 0;
			self.ky_st_prog = 0;
		}
	}

	// Still holding fire button? Keep locking or winding up!
	if (self.button0)
	{
		self.attack_finished = time + 0.12;
		return;
	}

	// RELEASED FIRE -> THROW POCKET KYLE (Superman Torpedo if locked on bird, else power-scaled throw!)
	ammo = FunGun_Ammo (self, FG_KYLE);
	self.ky_locking = 0;
	self.ky_st_mode = 0;
	self.ky_st_prog = 0;
	if (ammo < 1)
		return;

	FunGun_SetAmmo (self, FG_KYLE, ammo - 1);
	FunGun_Lock (FG_KYLE);
	self.fg_fire_t = time;
	self.ky_fire_t = time;
	self.ky_throw_at = time + KY_THROW_DELAY;
	self.ky_cool = time + KY_COOLDOWN;
	self.ky_pending_homing = (self.ky_lock_ready && KY_IsValidTarget (self, self.ky_lock_ent));
	self.ky_pending_targ = self.ky_pending_homing ? self.ky_lock_ent : world;
	self.ky_pending_power = self.ky_windup;
	self.ky_lock_ent = world;
	self.ky_lock_prog = 0;
	self.ky_windup = 0;
	self.ky_bird_locking = FALSE;
	self.ky_lock_ready = FALSE;
	self.punchangle_x = 1.8;				// cock-back anticipation before explosive launch whip!
	self.punchangle_z = -1.4;
	FG_Snd (self, CHAN_WEAPON, "kyle/snip_fast.wav", 0.68, 1.12);
	player_mm1 ();
	self.attack_finished = time + KY_THROW_DELAY + KY_FOLLOW_TIME;
};

// ---------------------------------------------------------------- held Pocket Kyle viewmodel (v_kyle.md3)

void(entity vm, float is_quad) Kyle_ViewFrame =
{
	local entity p;
	local float ammo, u, k, ease, idx, sw1, sw2, sw3, spd, dt_f, fly_t;
	local vector vxy;

	p = vm.owner;
	if (p.weapon != IT_FUNGUN || p.fg_sel != FG_KYLE)
	{
		if (vm.kyvm_on)
		{
			vm.skin = is_quad ? 1 : 0;
			vm.origin = '0 0 0';
			vm.angles = '0 0 0';
			vm.kyvm_on = FALSE;
		}
		return;
	}

	if (is_quad && vm.alpha < 0)
		vm.alpha = 0.5;

	vm.frame = 0;
	vm.origin = '0 0 0';
	vm.angles = '0 0 0';
	ammo = FunGun_Ammo (p, FG_KYLE);

	// Pull Out Gun -> play random "Whoa man!" voice + 12-frame surprised pop-up!
	if (!vm.kyvm_on)
	{
		vm.kyvm_on = TRUE;
		if (ammo >= 1 && p.ky_throw_at <= 0 && (!p.ky_threw_t || time >= p.ky_threw_t + KY_FOLLOW_TIME))
		{
			if (!is_quad)
			{
				p.ky_draw_t = time;
				KY_PlayWhoa (p);
			}
		}
		else if (ammo < 1)
			p.ky_empty = TRUE;
	}

	// 1. Dual Hold-Fire Animation: BRAND-NEW Dedicated Horizontal Superman Bird Lock-On vs Progressive Throw Wind-Up!
	if (p.ky_locking > 0)
	{
		p.ky_empty = FALSE;
		sw1 = sin (time * 38.0);
		sw2 = cos (time * 32.0);
		if (p.ky_bird_locking)
		{
			// BRAND-NEW Dedicated Bird Lock-On (skins 72..95): hand tilts horizontal Superman Kyle up at the bird snapping scissors & battle-yelling!
			idx = floor ((time - p.ky_locking) * (24 + 8 * p.ky_lock_prog));
			idx = idx - KY_VM_BIRDLOCK_COUNT * floor (idx / KY_VM_BIRDLOCK_COUNT);
			vm.skin = KY_VM_BIRDLOCK_SKIN + idx;
			vm.origin_x = 1.4 * p.ky_lock_prog;
			vm.origin_y = 1.8 * p.ky_lock_prog + sw1 * (0.18 + 0.34 * p.ky_lock_prog);
			vm.origin_z = 1.6 * p.ky_lock_prog + sw2 * (0.14 + 0.26 * p.ky_lock_prog);
			vm.angles_x = -4.2 * p.ky_lock_prog;
		}
		else
		{
			// Ground Throw Power Wind-Up (skins 48..71): pulls hand farther back & down as throw distance climbs 0% -> 100%!
			idx = floor ((time - p.ky_locking) * (22 + 12 * p.ky_windup));
			idx = idx - KY_VM_LOCK_COUNT * floor (idx / KY_VM_LOCK_COUNT);
			vm.skin = KY_VM_LOCK_SKIN + idx;
			vm.origin_x = -2.4 * p.ky_windup + sw1 * (0.14 + 0.30 * p.ky_windup);
			vm.origin_y = -2.0 * p.ky_windup + sw2 * (0.18 + 0.34 * p.ky_windup);
			vm.origin_z = -3.2 * p.ky_windup + sw1 * (0.14 + 0.26 * p.ky_windup);
			vm.angles_x = 5.2 * p.ky_windup;
			vm.angles_z = 6.5 * p.ky_windup + sw2 * (1.2 * p.ky_windup);
		}
		return;
	}

	// 2. BRAND-NEW 42-Skin Real Physical Throw (0..14 cock-back & forward Superman drive -> 15..34 empty open-palm launch & goose-neck flick -> 35..41 "WHOA!" pop-up!)
	if (p.ky_fire_t > 0 && time < p.ky_fire_t + KY_THROW_DELAY + KY_FOLLOW_TIME)
	{
		dt_f = time - p.ky_fire_t;
		if (dt_f < KY_THROW_DELAY)
		{
			// Stage A & B (skins 96..110 = 15 skins: 0..8 overhand cock-back + 9..14 forward Superman drive right up to release!)
			u = dt_f / KY_THROW_DELAY;
			if (u < 0) u = 0;
			if (u > 0.999) u = 0.999;
			idx = floor (u * 15);
			vm.skin = KY_VM_FIRE_SKIN + idx;
			if (u < 0.56)
			{
				// Deep overhand cock-back pull-back with panic shudder!
				k = u / 0.56;
				ease = k * k * (3 - 2 * k);
				sw1 = sin (dt_f * 44.0);
				sw2 = cos (dt_f * 37.0);
				vm.origin_x = -2.6 * ease + 0.22 * sw1 * ease;
				vm.origin_y = -2.2 * ease + 0.26 * sw2 * ease;
				vm.origin_z = -3.2 * ease + 0.20 * sw1 * ease;
				vm.angles_x = 5.2 * ease;
				vm.angles_z = 4.8 * ease + 1.2 * sw1 * ease;
			}
			else
			{
				// Explosive forward arm-drive & whip right into open-palm release at dt_f == KY_THROW_DELAY!
				k = (u - 0.56) / 0.44;
				ease = k * k * (3 - 2 * k);
				vm.origin_x = -2.6 * (1 - ease) + 4.4 * ease;
				vm.origin_y = -2.2 * (1 - ease) + 5.6 * ease;
				vm.origin_z = -3.2 * (1 - ease) + 3.2 * ease;
				vm.angles_x = 5.2 * (1 - ease) - 7.2 * ease;
				vm.angles_z = 4.8 * (1 - ease) - 5.6 * ease;
			}
			return;
		}
		// Stage C: EXACT open-palm release (skins 15..34) as REAL 3D Kyle flies from your fingertips, then goose-neck flick!
		fly_t = dt_f - KY_THROW_DELAY;
		if (fly_t < 0.72)
		{
			// Skins 15..34 (20 skins): splayed open-palm release -> recoil -> classic goose-neck wrist-flick sweep down!
			u = fly_t / 0.72;
			if (u > 0.999) u = 0.999;
			idx = 15 + floor (u * 20);
			vm.skin = KY_VM_FIRE_SKIN + idx;
			ease = max (0, (u - 0.58) / 0.42);
			ease = ease * ease;
			vm.origin_x = 4.4 * (1 - 0.8 * u);
			vm.origin_y = 5.6 * (1 - 0.65 * u);
			vm.origin_z = 3.2 - 3.5 * u - 14.5 * ease;
			vm.angles_x = -7.2 + 8.0 * u + 12.0 * ease;
			vm.angles_z = -5.6 * (1 - u);
			return;
		}
		if (ammo < 1)
		{
			p.ky_empty = TRUE;
			vm.alpha = -1;
			return;
		}
		// Stage D: next fresh Pocket Kyle pops boingily up with wide-eyed "WHOA!" face (skins 35..41 = 7 skins)
		u = (fly_t - 0.72) / (KY_FOLLOW_TIME - 0.72);
		if (u < 0) u = 0;
		if (u > 0.999) u = 0.999;
		idx = 35 + floor (u * 7);
		if (idx >= KY_VM_FIRE_COUNT)
			idx = KY_VM_FIRE_COUNT - 1;
		vm.skin = KY_VM_FIRE_SKIN + idx;
		ease = 1 - (1 - u) * (1 - u);
		vm.origin_z = -18.0 * (1 - ease);
		return;
	}

	// 3. Out of charges: keep hand put away cleanly until next Kyle recharges
	if (ammo < 1)
	{
		p.ky_empty = TRUE;
		vm.alpha = -1;
		return;
	}
	if (p.ky_empty)
	{
		p.ky_empty = FALSE;
		if (!is_quad)
			p.ky_draw_t = time;
	}

	// 4. Pull-out Draw / Recharge Pop-Up (skins 100..111 @ 24 FPS + smooth Milky raise-up)
	if (p.ky_draw_t > 0 && time >= p.ky_draw_t && time < p.ky_draw_t + KY_DRAW_TIME)
	{
		u = (time - p.ky_draw_t) / KY_DRAW_TIME;
		if (u < 0) u = 0;
		if (u > 0.999) u = 0.999;
		idx = floor (u * KY_VM_DRAW_COUNT);
		vm.skin = KY_VM_DRAW_SKIN + idx;
		ease = 1 - (1 - u) * (1 - u);
		vm.origin_z = -18.0 * (1 - ease);
		return;
	}

	// 5. Quiet Chillin' 24-FPS Idle Loop (skins 0..47, ZERO scissor SFX at idle!)
	idx = floor (time * 24);
	idx = idx - KY_VM_IDLE_COUNT * floor (idx / KY_VM_IDLE_COUNT);
	vm.skin = KY_VM_IDLE_SKIN + idx;

	vxy = p.velocity;
	vxy_z = 0;
	spd = vlen (vxy) / 320;
	if (spd > 1) spd = 1;
	sw1 = sin (time * 2.2);
	sw2 = sin (time * 4.4);
	sw3 = sin (time * 8.0);
	vm.origin_y = 0.16 * sw1 + 0.40 * spd * sw3;
	vm.origin_z = 0.14 * sw2 - 0.34 * spd * fabs (sw3);
	vm.angles_z = 0.35 * sw1 + 0.85 * spd * sw3;
};

// ---------------------------------------------------------------- temporary practice & simulation map (kyle_range)

void() KY_DummyDie =
{
	FG_Snd (self, CHAN_VOICE, "player/death1.wav", 0.9, 1.0);
	ky_range_enemy = world;
	ky_range_enemy_t = time + 3.0;
	remove (self);
};

void() KY_DummyThink =
{
	local float f;

	if (self.health <= 0)
		return;
	// Patrol gently back & forth across the sunny practice courtyard (X = -320..+320, Y = +200)
	if (self.origin_x > 300)
		self.angles_y = 180;
	else if (self.origin_x < -300)
		self.angles_y = 0;
	if (!walkmove (self.angles_y, 7.5))
		self.angles_y = self.angles_y + 180;
	f = floor (time * 10);
	self.frame = 6 + (f - 6 * floor (f / 6));		// standard Quake player run frames 6..11
	self.nextthink = time + 0.05;
};

void(entity attacker, float damage) KY_DummyPain =
{
	// Never interrupt patrol or crash FoundTarget when Kyle chops Practice Enemy!
	self.think = KY_DummyThink;
	self.nextthink = time + 0.05;
};

void() KY_RangeSpawnEnemy =
{
	local entity d;

	d = spawn ();
	d.classname = "monster_kyle_dummy";
	d.netname = "Practice Enemy";
	d.flags = FL_MONSTER;
	d.solid = SOLID_SLIDEBOX;
	d.movetype = MOVETYPE_STEP;
	d.takedamage = DAMAGE_AIM;
	d.health = 140;
	d.max_health = 140;
	d.th_stand = KY_DummyThink;
	d.th_walk = KY_DummyThink;
	d.th_run = KY_DummyThink;
	d.th_melee = KY_DummyThink;
	d.th_pain = KY_DummyPain;
	d.th_die = KY_DummyDie;
	d.angles_y = 0;
	setmodel (d, "progs/player.mdl");
	setsize (d, VEC_HULL_MIN, VEC_HULL_MAX);
	setorigin (d, '-120 220 30');
	droptofloor ();
	d.think = KY_DummyThink;
	d.nextthink = time + 0.05;
	ky_range_enemy = d;
};

void() KY_RangeSpawnBird =
{
	local entity jb;

	jb = spawn ();
	jb.angles = '0 0 0';
	jb.angles_y = 0;
	setorigin (jb, '0 220 215');
	JB_InitEntity (jb, TRUE);
	jb.movetype = MOVETYPE_NONE;
	setsize (jb, '-28 -36 -4', '28 36 58');
	jb.jb_spawn_org = '0 220 215';
	jb.jb_ai = TRUE;
	jb.jb_ai_strafe = 1;
	jb.jb_ai_mode = 0;
	jb.jb_ai_mode_t = time + 999;
	jb.jb_ai_fire_t = time + 99999;		// peaceful flying target practice bird!
	jb.jb_flap_t = time + 0.1;
	jb.jb_voice_t = time + 9999;
	jb.think = JB_AutopilotThink;
	jb.nextthink = time + 0.05;
	ky_range_bird = jb;
};

void() KY_RangeThink =
{
	local entity p;

	if (mapname != "kyle_range")
	{
		remove (self);
		return;
	}
	// Keep 1 patrolling enemy & 1 circling flying Winged John Bird alive in the practice yard!
	if (ky_range_enemy == world || bm_wasfreed (ky_range_enemy) || ky_range_enemy.health <= 0)
	{
		if (!ky_range_enemy_t)
			ky_range_enemy_t = time + 0.5;
		if (time >= ky_range_enemy_t)
		{
			ky_range_enemy_t = 0;
			KY_RangeSpawnEnemy ();
		}
	}
	if (ky_range_bird == world || bm_wasfreed (ky_range_bird) || ky_range_bird.health <= 0 || ky_range_bird.jb_dying)
	{
		if (!ky_range_bird_t)
			ky_range_bird_t = time + 0.8;
		if (time >= ky_range_bird_t)
		{
			ky_range_bird_t = 0;
			KY_RangeSpawnBird ();
		}
	}
	else
	{
		// Keep peaceful flying practice bird from shooting hairspray bombs at the tester!
		ky_range_bird.jb_ai_fire_t = time + 99999;
	}
	// Auto-give Pocket Kyle on spawn in kyle_range so you can jump right into practicing!
	p = find (world, classname, "player");
	while (p)
	{
		if (p.health > 0 && !p.ky_range_given)
		{
			p.ky_range_given = TRUE;
			p.impulse = 68;
			FunGun_SetAmmo (p, FG_KYLE, FG_KYLE_MAX);
			centerprint (p, "KYLE PRACTICE RANGE\nPatrolling Enemy + Flying Bird Overhead!\nHold FIRE to Lock, Aim UP for Sky Chop, Shoot Kyle for Money + 3D Scissors!\n");
		}
		p = find (p, classname, "player");
	}
	self.nextthink = time + 0.25;
};

void() KY_RangeInit =
{
	if (ky_range_ctrl != world && !bm_wasfreed (ky_range_ctrl))
		return;
	ky_range_enemy = world;
	ky_range_bird = world;
	ky_range_enemy_t = time + 0.6;
	ky_range_bird_t = time + 0.8;
	ky_range_ctrl = spawn ();
	ky_range_ctrl.classname = "kyle_range_ctrl";
	ky_range_ctrl.think = KY_RangeThink;
	ky_range_ctrl.nextthink = time + 0.4;
};
