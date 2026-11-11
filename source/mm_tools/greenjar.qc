// ---------------------------------------------------------------- 2. JAR O' GREEN GUYS (fun gun 2, impulse 62)
// Hold a clear specimen mason jar filled with swirling neon-green mist and a tiny photo-digitized Green-Suit Guy
// spazzing out across 4 manic antics (hamster-wheeling the glass, squishing his grinning/screaming face on the glass,
// pogo-bonking the perforated lid, and tornado-spinning).
//   * Hold Fire (`+attack`) to cocktail-shake the jar; release to whip-throw (`progs/greenjar_proj.spr32`)!
//   * Shatters on impact into glittering glass & igniting neon-green smoke (`progs/greenjar_burst.spr32`), unleashing
//     12 featherweight, high-pitched giggling/screaming Mini-Green-Guys (`progs/greenguy_mini.spr32`)!
//   * They scurry fast across floors, pogo-bounce, and climb vertically straight up building walls & pillars!
//   * On reaching a target, they swarm tightly around them for 5 full orbits (`1800 deg`) jumping right across their
//     eyes/camera to block their view, dealing 1%-2% non-lethal annoyance pokes (CLAMPED >= 1 HP so they NEVER kill!),
//     and then swell like party balloons and POP into rainbow confetti!
//   * 1-Hit Low-HP Comedy Spin: shooting any gremlin sends it into a shrieking 360-degree punctured-helium-balloon
//     cartwheel spin ricocheting off walls before bursting into rainbow confetti!

void() GreenJar_Precache =
{
	registercvar ("gj_test", "0");
	precache_model ("progs/v_greenjar.md3");
	precache_model ("progs/greenjar_proj.spr32");
	precache_model ("progs/greenjar_burst.spr32");
	precache_model ("progs/greenguy_mini.spr32");

	precache_sound ("greenjar/jar_muffle1.wav");
	precache_sound ("greenjar/jar_muffle2.wav");
	precache_sound ("greenjar/jar_shake.wav");
	precache_sound ("greenjar/jar_throw.wav");
	precache_sound ("greenjar/jar_shatter.wav");
	precache_sound ("greenjar/mini_giggle1.wav");
	precache_sound ("greenjar/mini_giggle2.wav");
	precache_sound ("greenjar/mini_giggle3.wav");
	precache_sound ("greenjar/mini_scream1.wav");
	precache_sound ("greenjar/mini_spin_shriek.wav");
	precache_sound ("greenjar/mini_pop.wav");
	precache_sound ("greenjar/mini_boing.wav");
};

void(entity p) GJ_ResetPlayer =
{
	p.gj_shaking = 0;
	p.gj_next_rattle = 0;
	p.gj_next_muffle = 0;
	p.gj_fire_t = 0;
	p.gj_throw_at = 0;
	p.gj_threw_t = 0;
	p.gj_reload_t = 0;
	p.gj_empty = FALSE;
	p.gj_charge_bonus = 0;
};

//Valid target check: enemies (or thrower too when `gj_test` cvar > 0 for solo testing!)
float(entity m, entity targ) GJ_IsValidTarget =
{
	if (!targ || targ == world)
		return FALSE;
	if (targ.health <= 0 || !targ.takedamage)
		return FALSE;
	if (targ.classname == "greenguy_mini")
		return FALSE;
	if (targ == m.owner)
	{
		if (cvar ("gj_test") > 0)
			return TRUE;
		return FALSE;
	}
	if (targ.classname == "player")
	{
		if (teamplay && m.owner && m.owner.team > 0 && targ.team == m.owner.team)
			return FALSE;
		return TRUE;
	}
	if (targ.flags & FL_MONSTER)
		return TRUE;
	return FALSE;
};

entity(entity m) GJ_FindTarget =
{
	local entity e, best;
	local float d, best_d;

	best = world;
	best_d = 1900;
	e = findradius (m.origin, 1850);
	while (e)
	{
		if (GJ_IsValidTarget (m, e))
		{
			d = vlen (e.origin - m.origin);
			if (d < best_d)
			{
				best_d = d;
				best = e;
			}
		}
		e = e.chain;
	}
	return best;
};

void(entity m) GJ_PlayRandomLaugh =
{
	local float r, p;

	r = random ();
	p = 0.94 + random () * 0.16;
	if (r < 0.28)
		FG_Snd (m, CHAN_VOICE, "greenjar/mini_giggle1.wav", 0.88, p);
	else if (r < 0.56)
		FG_Snd (m, CHAN_VOICE, "greenjar/mini_giggle2.wav", 0.88, p);
	else if (r < 0.80)
		FG_Snd (m, CHAN_VOICE, "greenjar/mini_giggle3.wav", 0.88, p);
	else
		FG_Snd (m, CHAN_VOICE, "greenjar/mini_scream1.wav", 0.92, p);
};

// ================================================================
// MINI-GREMLIN BALLOON SWELL -> RAINBOW CONFETTI POP & 1-HIT SPIN
// ================================================================

void() GJ_BalloonPopStep =
{
	self.gj_step = self.gj_step + 1;
	if (self.gj_step == 4)
	{
		// Frame 308: Balloon bursts into shockwave ring + rainbow party confetti!
		FG_Snd (self, CHAN_VOICE, "greenjar/mini_pop.wav", 0.95, 0.95 + random () * 0.14);
		sendParticle ("pk_puff", self.origin + '0 0 12', '0 0 0', 1, 0);
	}
	if (self.gj_step >= 16)
	{
		remove (self);
		return;
	}
	self.frame = 304 + self.gj_step;
	self.think = GJ_BalloonPopStep;
	self.nextthink = time + 0.045;
};

void(entity m, float immediate_pop) GJ_StartBalloonPop =
{
	m.gj_state = 5;
	m.takedamage = DAMAGE_NO;
	m.solid = SOLID_NOT;
	m.movetype = MOVETYPE_NONE;
	m.velocity = '0 0 0';
	if (immediate_pop)
	{
		m.gj_step = 3;		// next tick hits step 4 -> immediate confetti burst!
		m.frame = 307;
	}
	else
	{
		m.gj_step = 0;		// 4 frames of pressurized 1.46x balloon swell -> POP!
		m.frame = 304;
	}
	m.think = GJ_BalloonPopStep;
	m.nextthink = time + 0.045;
};

void() GJ_ShotSpinStep =
{
	// Keep bouncing wildly around the room like a punctured helium balloon!
	self.gj_step = self.gj_step + 1;
	if (self.flags & FL_ONGROUND)
	{
		self.flags = self.flags - FL_ONGROUND;
		self.velocity_x = self.velocity_x + crandom () * 220;
		self.velocity_y = self.velocity_y + crandom () * 220;
		self.velocity_z = 210 + random () * 140;
	}
	if (self.gj_step >= 15)
	{
		GJ_StartBalloonPop (self, FALSE);
		return;
	}
	self.frame = 288 + self.gj_step;
	self.think = GJ_ShotSpinStep;
	self.nextthink = time + 0.04;
};

void() GJ_MiniDie =
{
	local vector away;

	// If already balloon-popping, ignore
	if (self.gj_state == 5)
		return;

	// Shooting a gremlin a 2nd time mid-spin pops it into rainbow confetti immediately!
	if (self.gj_state == 4)
	{
		GJ_StartBalloonPop (self, TRUE);
		return;
	}

	// 1st Hit: Enter hilarious 360-degree Punctured-Helium-Balloon Cartwheel Spin!
	self.gj_state = 4;
	self.gj_step = 0;
	self.health = 1;
	self.takedamage = DAMAGE_AIM;		// still shootable mid-spin for instant pop!
	self.movetype = MOVETYPE_BOUNCE;
	self.bouncefactor = 0.88;
	self.gravity = 0.65;
	if (self.flags & FL_ONGROUND)
		self.flags = self.flags - FL_ONGROUND;

	if (damage_attacker && damage_attacker != world)
		away = normalize ((self.origin + '0 0 12') - (damage_attacker.origin + '0 0 16'));
	else
		away = '0 0 1';
	self.velocity = away * (320 + random () * 160);
	self.velocity_x = self.velocity_x + crandom () * 190;
	self.velocity_y = self.velocity_y + crandom () * 190;
	self.velocity_z = 260 + random () * 150;

	FG_Snd (self, CHAN_VOICE, "greenjar/mini_spin_shriek.wav", 1.0, 0.94 + random () * 0.14);
	self.frame = 288;
	self.think = GJ_ShotSpinStep;
	self.nextthink = time + 0.04;
};

void(entity attacker, float take) GJ_MiniPain =
{
	damage_attacker = attacker;
	GJ_MiniDie ();
};

// ================================================================
// PER-CLIENT 16-ANGLE SPRITE CUSTOMIZER (`progs/greenguy_mini.spr32`)
//   0   + d*6 + k   16-dir Scurry          (0..95)
//   96  + d*6 + k   16-dir Wall-Climb      (96..191)
//   192 + d*6 + k   16-dir Pogo Face-Jump  (192..287)
//   288 .. 303      16f Punctured Shot-Spin
//   304 .. 319      16f Balloon Swell & Rainbow Confetti Pop
// ================================================================

float() GJ_MiniCustomize =
{
	local float rel, d, k;
	local vector delta;

	if (self.gj_state == 4)
	{
		self.frame = 288 + min (15, self.gj_step);
		return TRUE;
	}
	if (self.gj_state == 5)
	{
		self.frame = 304 + min (15, self.gj_step);
		return TRUE;
	}

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 12');
	rel = vectoyaw (delta) - self.angles_y;
	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 22.5 + 0.5);
	if (d >= 16)
		d = 0;

	k = floor ((time - self.gj_anim_t0) * 18);
	k = k - 6 * floor (k / 6);

	if (self.gj_state == 2)
		self.frame = 96 + d * 6 + k;		// Vertical building/wall climber!
	else if (self.gj_state == 3 || !(self.flags & FL_ONGROUND) || self.gj_role == 1)
		self.frame = 192 + d * 6 + k;		// Mid-air / Face-blocking pogo jumper!
	else
		self.frame = d * 6 + k;				// Hyper-speed floor zoomer!
	return TRUE;
};

// Non-lethal 1%-2% annoyance poke (NEVER kills a player — strictly clamped so health >= 1!)
void(entity m, entity victim) GJ_AnnoyPoke =
{
	local float maxh, dmg;

	if (time < m.gj_next_poke)
		return;
	m.gj_next_poke = time + 2.4 + random () * 1.8;

	// Annoying view-jiggle & high-pitched giggle right in their ears!
	if (victim.classname == "player")
	{
		victim.punchangle_x = crandom () * 1.1;
		victim.punchangle_z = crandom () * 1.4;
	}
	if (time >= m.gj_next_voice)
	{
		GJ_PlayRandomLaugh (m);
		m.gj_next_voice = time + 0.65 + random () * 0.55;
	}

	// Whole swarm only does ~1%-2% total annoyance chip damage, and NEVER kills (clamped >= 1 HP)!
	if (victim.health <= 2 || random () > 0.22)
		return;

	maxh = victim.max_health;
	if (maxh <= 0)
		maxh = 100;
	dmg = floor (maxh * 0.01 + 0.5);	// 1% chip damage (1 HP on 100 HP player)
	if (dmg < 1)
		dmg = 1;
	if (dmg > victim.health - 1)
		dmg = victim.health - 1;
	if (dmg <= 0)
		return;

	fg_inflicting = FG_PONG;
	T_Damage (victim, m, m.owner, dmg);
	fg_inflicting = 0;
	if (victim.health < 1)
		victim.health = 1;
};

void() GJ_MiniTouch =
{
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	if (self.gj_state >= 4)
		return;

	if (GJ_IsValidTarget (self, other))
	{
		self.enemy = other;
		if (self.gj_state != 3)
		{
			self.gj_state = 3;
			self.gj_orbit_ang = vectoyaw (self.origin - other.origin);
		}
		GJ_AnnoyPoke (self, other);
		return;
	}
};

// ================================================================
// MINI-GREMLIN AI: FAST SCURRY, VERTICAL BUILDING CLIMB & 5x EYE-ORBIT
// ================================================================

void() GJ_MiniThink =
{
	local vector dir, fwd_ang, goal, wall_check, roof_check, to_goal;
	local float dist, spd, step_deg, eye_z, bob_z;

	if (self.gj_state >= 4)
		return;
	if (self.health <= 0)
	{
		GJ_MiniDie ();
		return;
	}
	if (time >= self.gj_die_at)
	{
		GJ_StartBalloonPop (self, FALSE);
		return;
	}

	// Continuous overlapping helium laughing, screaming & giggling!
	if (time >= self.gj_next_voice)
	{
		GJ_PlayRandomLaugh (self);
		self.gj_next_voice = time + 0.75 + random () * 0.95;
	}

	// Refresh target if none or dead
	if (!GJ_IsValidTarget (self, self.enemy))
	{
		self.enemy = GJ_FindTarget (self);
		if (self.gj_state == 3)
			self.gj_state = 1;
	}

	// ------------------------------------------------------------
	// STATE 3: 5-ORBIT VIEW-BLOCKING FACE SWARM -> BALLOON POP!
	// ------------------------------------------------------------
	if (self.gj_state == 3 && GJ_IsValidTarget (self, self.enemy))
	{
		dist = vlen (self.enemy.origin - self.origin);
		if (dist > 290)
		{
			self.gj_state = 1;		// victim escaped far away; chase again!
		}
		else
		{
			step_deg = (29 + self.gj_role * 5) * self.gj_orbit_dir;		// ~580..780 deg/s = ~1.8 orbits/sec!
			self.gj_orbit_ang = self.gj_orbit_ang + step_deg;
			self.gj_orbit_deg = self.gj_orbit_deg + fabs (step_deg);

			// Completed 5 full circles (5 * 360 = 1800 deg) around the victim -> swell & confetti POP!
			if (self.gj_orbit_deg >= GJ_ORBITS_TO_POP)
			{
				GJ_StartBalloonPop (self, FALSE);
				return;
			}

			fwd_ang = '0 0 0';
			fwd_ang_y = self.gj_orbit_ang;
			makevectors (fwd_ang);

			eye_z = self.enemy.view_ofs_z;
			if (eye_z <= 4)
				eye_z = 22;
			// Jump up and down right across eye/camera height so all 12 block their view!
			bob_z = sin ((time - self.gj_anim_t0) * 13.5);
			bob_z = bob_z * 16;
			goal = self.enemy.origin + v_forward * self.gj_orbit_rad;
			goal_z = self.enemy.origin_z + eye_z - 6 + bob_z;

			to_goal = goal - self.origin;
			if (self.flags & FL_ONGROUND)
				self.flags = self.flags - FL_ONGROUND;
			self.velocity = to_goal * 11.5;
			if (vlen (self.velocity) > 680)
				self.velocity = normalize (self.velocity) * 680;

			// Face straight at the victim while circling & jumping in their face!
			self.angles_y = vectoyaw (self.enemy.origin - self.origin);
			GJ_AnnoyPoke (self, self.enemy);

			self.think = GJ_MiniThink;
			self.nextthink = time + 0.05;
			return;
		}
	}

	// ------------------------------------------------------------
	// STATE 2: VERTICAL BUILDING / PILLAR WALL-CLIMB!
	// ------------------------------------------------------------
	if (self.gj_state == 2)
	{
		// Probe straight into the wall we are climbing (`-gj_wall_n`)
		wall_check = self.origin + '0 0 10' - self.gj_wall_n * 26;
		traceline (self.origin + '0 0 10', wall_check, TRUE, self);
		if (trace_fraction >= 0.98)
		{
			// Cleared the top ledge / roof of the building! Vault onto the roof with a boing!
			self.gj_state = 1;
			self.velocity = ('0 0 0' - self.gj_wall_n) * 230 + '0 0 210';
			FG_Snd (self, CHAN_BODY, "greenjar/mini_boing.wav", 0.75, 1.0 + random () * 0.15);
			self.think = GJ_MiniThink;
			self.nextthink = time + 0.05;
			return;
		}
		// Check ceiling overhead OR max climb time so indoor wall-climbers parkour-kick back into the room!
		roof_check = self.origin + '0 0 34';
		traceline (self.origin + '0 0 12', roof_check, TRUE, self);
		if (trace_fraction < 0.95 || time >= self.gj_climb_end)
		{
			self.gj_state = 1;
			self.gj_wall_cool = time + 1.8;
			self.angles_y = vectoyaw (self.gj_wall_n) + crandom () * 45;
			self.velocity = self.gj_wall_n * 310 + '0 0 -60';
			FG_Snd (self, CHAN_BODY, "greenjar/mini_boing.wav", 0.75, 1.08);
			self.think = GJ_MiniThink;
			self.nextthink = time + 0.05;
			return;
		}

		// Scale rapidly straight up the vertical wall!
		if (self.flags & FL_ONGROUND)
			self.flags = self.flags - FL_ONGROUND;
		self.velocity = ('0 0 0' - self.gj_wall_n) * 75 + '0 0 285';
		self.angles_y = vectoyaw ('0 0 0' - self.gj_wall_n);
		self.think = GJ_MiniThink;
		self.nextthink = time + 0.05;
		return;
	}

	// ------------------------------------------------------------
	// STATE 1: HYPER-FAST FLOOR SCURRY, POGO BOUNCE & WALL LATCH
	// ------------------------------------------------------------
	if (GJ_IsValidTarget (self, self.enemy))
	{
		dist = vlen (self.enemy.origin - self.origin);
		if (dist < 165)
		{
			// Reached enemy -> enter 5-Orbit View-Blocking Face Swarm!
			self.gj_state = 3;
			self.gj_orbit_ang = vectoyaw (self.origin - self.enemy.origin);
			FG_Snd (self, CHAN_BODY, "greenjar/mini_boing.wav", 0.85, 1.05);
			self.think = GJ_MiniThink;
			self.nextthink = time + 0.05;
			return;
		}
		dir = normalize ((self.enemy.origin - self.origin) + v_right * crandom () * 45);
		self.angles_y = vectoyaw (dir) + crandom () * 18;
	}
	else
	{
		// Dumb feral animal wandering & bouncing wildly all over the map!
		self.angles_y = self.angles_y + crandom () * 34;
	}
	self.angles_y = self.angles_y - 360 * floor (self.angles_y / 360);

	fwd_ang = '0 0 0';
	fwd_ang_y = self.angles_y;
	makevectors (fwd_ang);

	// Check if a vertical building/wall is right ahead -> climb straight up it!
	if (time >= self.gj_wall_cool)
	{
		traceline (self.origin + '0 0 10', self.origin + '0 0 10' + v_forward * 24, TRUE, self);
		if (trace_fraction < 0.95 && fabs (trace_plane_normal_z) < 0.28)
		{
			self.gj_state = 2;
			self.gj_wall_n = trace_plane_normal;
			self.gj_climb_end = time + 1.15;
			if (self.flags & FL_ONGROUND)
				self.flags = self.flags - FL_ONGROUND;
			self.velocity = ('0 0 0' - self.gj_wall_n) * 65 + '0 0 280';
			self.think = GJ_MiniThink;
			self.nextthink = time + 0.05;
			return;
		}
	}

	spd = 370 + self.gj_role * 35;
	self.velocity_x = v_forward_x * spd;
	self.velocity_y = v_forward_y * spd;

	// Rubber-flea pogo bounces!
	if ((self.flags & FL_ONGROUND) && time >= self.gj_next_boing)
	{
		if (self.gj_role == 1 || random () < 0.35)
		{
			self.flags = self.flags - FL_ONGROUND;
			self.velocity_z = 245 + random () * 135;
			if (random () < 0.45)
				FG_Snd (self, CHAN_BODY, "greenjar/mini_boing.wav", 0.65, 0.95 + random () * 0.2);
			self.gj_next_boing = time + (0.22 + random () * 0.35);
		}
		else
			self.gj_next_boing = time + 0.25;
	}

	self.think = GJ_MiniThink;
	self.nextthink = time + 0.05;
};

void(entity who) GJ_MakeRoomMinis =
{
	local entity e, oldest;
	local float n, best_t;

	n = 0;
	best_t = time + 9999;
	oldest = world;
	e = find (world, classname, "greenguy_mini");
	while (e)
	{
		if (e.owner == who && e.gj_state < 5)
		{
			n = n + 1;
			if (e.fg_born < best_t)
			{
				best_t = e.fg_born;
				oldest = e;
			}
		}
		e = find (e, classname, "greenguy_mini");
	}
	if (n >= GJ_MAX_MINIS && oldest != world)
		GJ_StartBalloonPop (oldest, TRUE);
};

void(vector org, entity who, float idx) GJ_SpawnMini =
{
	local entity m;
	local vector ang_v;
	local float yaw;

	GJ_MakeRoomMinis (who);

	m = spawn ();
	m.classname = "greenguy_mini";
	m.netname = "Mini Green Guy";
	m.owner = who;
	m.fg_born = time;
	m.gj_anim_t0 = time - random () * 0.5;
	m.gj_state = 1;
	m.gj_role = idx - 3 * floor (idx / 3);		// 0=zoomer, 1=pogo, 2=wall-climber
	m.gj_orbit_dir = (idx - 2 * floor (idx / 2)) * 2 - 1;	// alternating CW / CCW orbits!
	m.gj_orbit_rad = 36 + (idx - 4 * floor (idx / 4)) * 6;	// 36..54u tight screen-filling ring
	m.gj_orbit_deg = 0;
	m.gj_die_at = time + 12.5 + random () * 2.5;
	m.gj_next_voice = time + 0.08 * idx + random () * 0.25;
	m.gj_next_boing = time + random () * 0.25;
	m.gj_next_poke = time + 0.2;

	m.movetype = MOVETYPE_BOUNCE;
	m.solid = SOLID_BBOX;
	m.bouncefactor = 0.62;
	m.bouncestop = 0.05;
	m.gravity = 0.75;
	m.health = 1;
	m.max_health = 1;
	m.takedamage = DAMAGE_AIM;
	m.th_pain = GJ_MiniPain;
	m.th_die = GJ_MiniDie;
	m.touch = GJ_MiniTouch;
	m.customizeentityforclient = GJ_MiniCustomize;

	setmodel (m, "progs/greenguy_mini.spr32");
	m.scale = 0.44;
	setsize (m, '-14 -14 0', '14 14 30');

	yaw = idx * (360 / GJ_MINI_COUNT) + crandom () * 14;
	ang_v = '0 0 0';
	ang_v_y = yaw;
	makevectors (ang_v);

	setorigin (m, org + v_forward * 10 + '0 0 8');
	m.angles = '0 0 0';
	m.angles_y = yaw;
	m.velocity = v_forward * (260 + random () * 210);
	m.velocity_z = 180 + random () * 210;

	m.enemy = GJ_FindTarget (m);
	m.think = GJ_MiniThink;
	m.nextthink = time + 0.06 + idx * 0.01;
};

// ================================================================
// IGNITING NEON-GREEN SMOKE BURST & THROWN SPECIMEN JAR PROJECTILE
// ================================================================

void() GJ_SmokeBurstStep =
{
	self.frame = self.frame + 1;
	if (self.frame >= 16)
	{
		remove (self);
		return;
	}
	if (self.frame >= 4)
		self.effects = 0;		// bright flash fades into billowing green smoke
	self.think = GJ_SmokeBurstStep;
	self.nextthink = time + 0.042;
};

void(vector org, entity who) GJ_ShatterJar =
{
	local entity b;
	local float i;

	FG_Snd (self, CHAN_WEAPON, "greenjar/jar_shatter.wav", 1.0, 1.0);
	sendParticle ("pk_puff", org + '0 0 10', '0 0 0', 5, 0);

	b = spawn ();
	b.classname = "greenjar_burst";
	b.movetype = MOVETYPE_NONE;
	b.solid = SOLID_NOT;
	setmodel (b, "progs/greenjar_burst.spr32");
	b.scale = 1.55;
	b.frame = 0;
	b.effects = EF_DIMLIGHT;
	setorigin (b, org + '0 0 12');
	b.think = GJ_SmokeBurstStep;
	b.nextthink = time + 0.042;

	i = 0;
	while (i < GJ_MINI_COUNT)
	{
		GJ_SpawnMini (org, who, i);
		i = i + 1;
	}
};

void() GJ_ProjTouch =
{
	local vector hit_org;

	if (other == self.owner)
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	hit_org = self.origin - normalize (self.velocity) * 6;
	GJ_ShatterJar (hit_org, self.owner);
	remove (self);
};

void() GJ_ProjThink =
{
	if (time >= self.fg_born + 5.0)
	{
		GJ_ShatterJar (self.origin, self.owner);
		remove (self);
		return;
	}
	self.frame = self.frame + 1;
	if (self.frame >= 16)
		self.frame = 0;
	self.think = GJ_ProjThink;
	self.nextthink = time + 0.035;
};

void() GJ_Launch =
{
	local entity jar;
	local float spd;

	makevectors (self.v_angle);
	self.punchangle_x = 2.6;
	self.punchangle_z = -1.8;

	jar = spawn ();
	jar.classname = "greenjar_proj";
	jar.owner = self;
	jar.fg_born = time;
	jar.movetype = MOVETYPE_TOSS;
	jar.solid = SOLID_BBOX;
	jar.effects = EF_DIMLIGHT;

	spd = 840 + self.gj_charge_bonus * 240;
	jar.velocity = v_forward * spd + v_up * 215 + v_right * 12;

	setmodel (jar, "progs/greenjar_proj.spr32");
	jar.scale = 0.52;
	jar.frame = 0;
	setsize (jar, '-4 -4 -4', '4 4 4');
	setorigin (jar, FG_Muzzle (16));

	jar.touch = GJ_ProjTouch;
	jar.think = GJ_ProjThink;
	jar.nextthink = time + 0.035;
};

// ================================================================
// PLAYER COCKTAIL-SHAKER INPUT & FIRST-PERSON VIEWMODEL (`v_greenjar.md3`)
// ================================================================

void() GJ_BeginThrow =
{
	local float a, held;

	a = FunGun_Ammo (self, FG_PONG);
	if (a < 1 && cvar ("gj_test") > 0)
		a = 1;
	if (a < 1)
	{
		self.gj_shaking = 0;
		return;
	}
	held = time - self.gj_shaking;
	if (held < 0)
		held = 0;
	if (held > 1.0)
		held = 1.0;
	self.gj_charge_bonus = held;
	self.gj_shaking = 0;

	FunGun_SetAmmo (self, FG_PONG, a - 1);
	FunGun_Lock (FG_PONG);
	self.fg_fire_t = time;
	self.bm_lastshot = time + 0.8;
	self.gj_fire_t = time;
	self.gj_throw_at = time + GJ_THROW_DELAY;
	self.punchangle_x = -2.4;
	self.punchangle_z = 1.8;
	player_mm1 ();
	FG_Snd (self, CHAN_WEAPON, "greenjar/jar_throw.wav", 1.0, 1.0);
	self.attack_finished = time + GJ_THROW_DELAY + GJ_FOLLOW_TIME + GJ_RAISE_TIME;
};

void() GJ_Press =
{
	if (self.gj_shaking > 0 || self.gj_throw_at > 0)
		return;
	self.gj_shaking = time;
	self.gj_next_rattle = time + 0.36;
	FG_Snd (self, CHAN_WEAPON, "greenjar/jar_shake.wav", 0.95, 1.0);
	self.attack_finished = time + 0.08;
};

// Called every frame from FunGun_ViewFrame
void() GJ_Frame =
{
	if (self.health <= 0)
	{
		self.gj_shaking = 0;
		self.gj_throw_at = 0;
		return;
	}

	// Spawn tumbling jar right as the gauntlet snaps open at skin 84!
	if (self.gj_throw_at > 0 && time >= self.gj_throw_at)
	{
		self.gj_throw_at = 0;
		self.gj_threw_t = time;
		GJ_Launch ();
	}

	if (self.weapon != IT_FUNGUN || self.fg_sel != FG_PONG)
	{
		self.gj_shaking = 0;
		return;
	}

	// Cocktail-shaker loop while holding Fire (`+attack`)!
	if (self.gj_shaking > 0)
	{
		if (self.button0 && (time - self.gj_shaking) < GJ_MAX_SHAKE)
		{
			self.attack_finished = time + 0.08;
			if (time >= self.gj_next_rattle)
			{
				self.gj_next_rattle = time + 0.38;
				FG_Snd (self, CHAN_WEAPON, "greenjar/jar_shake.wav", 0.95, 1.0 + (time - self.gj_shaking) * 0.12);
			}
			return;
		}
		if ((time - self.gj_shaking) >= 0.08)
			GJ_BeginThrow ();
		return;
	}

	// Muffled inside-the-glass giggles & glass-taps while holding a full jar!
	if (FunGun_Ammo (self, FG_PONG) >= 1 && self.gj_throw_at <= 0 && time >= self.gj_threw_t + GJ_FOLLOW_TIME)
	{
		if (time >= self.gj_next_muffle)
		{
			if (self.gj_next_muffle > 0)
			{
				if (random () < 0.5)
					FG_Snd (self, CHAN_ITEM, "greenjar/jar_muffle1.wav", 0.58, 0.98 + random () * 0.08);
				else
					FG_Snd (self, CHAN_ITEM, "greenjar/jar_muffle2.wav", 0.58, 0.98 + random () * 0.08);
			}
			self.gj_next_muffle = time + 3.8 + random () * 2.4;
		}
	}
};

void(entity vm, float is_quad) GreenJar_ViewFrame =
{
	local entity p;
	local float ammo, u, ease, idx, sw1, sw2, sw3, spd;
	local vector vxy;

	p = vm.owner;
	if (p.weapon != IT_FUNGUN || p.fg_sel != FG_PONG)
	{
		if (vm.gjvm_on)
		{
			if (is_quad)
				vm.skin = 1;
			else
				vm.skin = 0;
			vm.origin = '0 0 0';
			vm.angles = '0 0 0';
			vm.gjvm_on = FALSE;
		}
		return;
	}

	if (is_quad && vm.alpha < 0)
		vm.alpha = 0.5;

	vm.frame = 0;
	vm.origin = '0 0 0';
	vm.angles = '0 0 0';
	ammo = FunGun_Ammo (p, FG_PONG);
	if (ammo < 1 && cvar ("gj_test") > 0)
		ammo = 1;

	if (!vm.gjvm_on)
	{
		vm.gjvm_on = TRUE;
		if (ammo >= 1 && p.gj_throw_at <= 0 && (!p.gj_threw_t || time >= p.gj_threw_t + GJ_FOLLOW_TIME))
		{
			if (!is_quad)
				p.gj_reload_t = time;
		}
		else if (ammo < 1)
			p.gj_empty = TRUE;
	}

	// 1. Cocktail-Shaker Windup (skins 60..75 @ 40 FPS)
	if (p.gj_shaking > 0)
	{
		p.gj_empty = FALSE;
		idx = floor ((time - p.gj_shaking) * 40);
		idx = idx - GJ_VM_SHAKE_COUNT * floor (idx / GJ_VM_SHAKE_COUNT);
		vm.skin = GJ_VM_SHAKE_SKIN + idx;
		sw1 = sin (time * 38.0);
		sw2 = sin (time * 31.0);
		vm.origin_z = sw1 * 0.65;
		vm.origin_y = sw2 * 0.45;
		return;
	}

	// 2. High Cock-Back & Blistering Cross-Screen Whip (skins 76..83)
	if (p.gj_throw_at > 0)
	{
		p.gj_empty = FALSE;
		u = (time - p.gj_fire_t) / GJ_THROW_DELAY;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * GJ_VM_PRE_COUNT);
		vm.skin = GJ_VM_WIND_SKIN + idx;
		return;
	}

	// 3. Splayed Open-Claw Release & Follow-Through (skins 84..93)
	if (p.gj_threw_t > 0 && time < p.gj_threw_t + GJ_FOLLOW_TIME)
	{
		u = (time - p.gj_threw_t) / GJ_FOLLOW_TIME;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * GJ_VM_POST_COUNT);
		vm.skin = GJ_VM_POST_SKIN + idx;
		if (ammo < 1)
			p.gj_empty = TRUE;
		else if (!is_quad)
			p.gj_reload_t = p.gj_threw_t + GJ_FOLLOW_TIME;
		return;
	}

	// 4. Out of jars: hide viewmodel until next jar finishes recharging
	if (ammo < 1)
	{
		p.gj_empty = TRUE;
		vm.alpha = -1;
		return;
	}
	if (p.gj_empty)
	{
		p.gj_empty = FALSE;
		p.gj_reload_t = time;
	}

	// 5. Belt-Snatch Fresh Rattling Jar Raise (skins 94..111)
	if (p.gj_reload_t > 0 && time >= p.gj_reload_t && time < p.gj_reload_t + GJ_RAISE_TIME)
	{
		u = (time - p.gj_reload_t) / GJ_RAISE_TIME;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * GJ_VM_RELOAD_COUNT);
		vm.skin = GJ_VM_RELOAD_SKIN + idx;
		ease = 1 - u;
		vm.origin_z = -1.8 * ease * ease;
		return;
	}

	// 6. 20 FPS 4-Antic Spazzing Green-Suit Guy Idle Loop (skins 0..59 = 3.0s seamless cycle!)
	idx = floor (time * 20);
	idx = idx - GJ_VM_IDLE_COUNT * floor (idx / GJ_VM_IDLE_COUNT);
	vm.skin = GJ_VM_IDLE_SKIN + idx;

	vxy = p.velocity;
	vxy_z = 0;
	spd = vlen (vxy) / 320;
	if (spd > 1)
		spd = 1;
	sw1 = sin (time * 2.4);
	sw2 = sin (time * 4.8);
	sw3 = sin (time * 8.2);
	vm.origin_y = 0.20 * sw1 + 0.50 * spd * sw3;
	vm.origin_z = 0.16 * sw2 - 0.38 * spd * fabs (sw3);
	vm.angles_z = 0.40 * sw1 + 0.95 * spd * sw3;
};
