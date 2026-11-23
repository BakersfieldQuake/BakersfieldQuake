#ifndef COMBATPLUS
#define COMBATPLUS
#endif
// ---------------------------------------------------------------- 2. JAR O' GREEN GUYS (fun gun 2, impulse 62)
// Hold a clear specimen mason jar filled with swirling neon-green mist and a tiny photo-digitized Green-Suit Guy
// spazzing out across 4 manic antics (hamster-wheeling the glass, squishing his grinning/screaming face on the glass,
// pogo-bonking the perforated lid, and tornado-spinning).
//   * Hold Fire (`+attack`) to cocktail-shake the jar; release to whip-throw (`progs/greenjar_proj.spr32`)!
//   * Shatters on impact into glittering glass & igniting neon-green smoke (`progs/greenjar_burst.spr32`), unleashing
//     12 bigger, high-pitched giggling/screaming Wheel-Driving Green Men (`progs/greenguy_mini.spr32`, scale 0.9333)!
//   * They wheel/drive fast across floors on spinning pneumatic tires, curb-hop steps, and drive up building walls!
//   * On reaching an enemy, they DO NOT attack right away — they swarm and wheel/drive 3 full laps (`1080 deg`)
//     around the enemy first while giggling & revving, and ONLY THEN lunge in to attack with 1%-2% non-lethal hits
//     (CLAMPED >= 1 HP so they NEVER kill!) before swelling like balloons and popping into rainbow confetti!
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
	if (p.gj_shaking > 0)
		sound (p, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
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

float(entity m, entity e) GJ_IsValidTarget;

void() GJ_BalloonPopStep =
{
	local entity e, nxt;

	self.gj_step = self.gj_step + 1;
	if (self.gj_step == 4)
	{
		// Frame 164: Balloon bursts into shockwave ring + rainbow party confetti!
		FG_Snd (self, CHAN_VOICE, "greenjar/mini_pop.wav", 0.95, 0.95 + random () * 0.14);
		sendParticle ("pk_puff", self.origin + '0 0 12', '0 0 0', 1, 0);
		// Post-frenzy balloon burst deals a 6-dmg confetti pop to nearby enemies (0 dmg if shot down!)
		if (self.gj_attack_end > 0 && self.owner.classname == "player")		// no damage credited to a player who left
		{
			fg_inflicting = FG_PONG;
			e = findradius (self.origin + '0 0 12', 95);
			while (e)
			{
				nxt = e.chain;
				if (GJ_IsValidTarget (self, e))
					T_Damage (e, self, self.owner, 6);
				e = nxt;
			}
			fg_inflicting = 0;
		}
	}
	if (self.gj_step >= 16)
	{
		remove (self);
		return;
	}
	self.frame = 160 + self.gj_step;
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
		m.frame = 163;
	}
	else
	{
		m.gj_step = 0;		// 4 frames of pressurized 1.46x balloon swell -> POP!
		m.frame = 160;
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
	self.frame = 144 + self.gj_step;
	self.think = GJ_ShotSpinStep;
	self.nextthink = time + 0.04;
};

void() GJ_MiniDie =
{
	local vector away;

	// If already balloon-popping, ignore
	if (self.gj_state == 5)
		return;

	// Shot-down gremlins ALWAYS pop harmlessly (rewarding counterplay!)
	self.gj_attack_end = 0;

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
	self.frame = 144;
	self.think = GJ_ShotSpinStep;
	self.nextthink = time + 0.04;
};

void(entity attacker, float take) GJ_MiniPain =
{
	damage_attacker = attacker;
	GJ_MiniDie ();
};

// ================================================================
// PER-CLIENT 8-ANGLE SPRITE CUSTOMIZER (`progs/greenguy_mini.spr32`, 272 frames)
//   0   + d*6 + k   8-dir Seated Wheel-Drive     (0..47)
//   48  + d*6 + k   8-dir Vertical Wall-Drive    (48..95)
//   96  + d*6 + k   8-dir Post-3-Lap Attack Ram  (96..143)
//   144 .. 159      16f Punctured Shot-Spin
//   160 .. 175      16f Balloon Swell & Rainbow Confetti Pop
//   176 + d*6 + k   8-dir Overhead 45-deg View   (176..223)
//   224 + d*6 + k   8-dir Overhead 90-deg View   (224..271)
// ================================================================

float() GJ_MiniCustomize =
{
	local float rel, d, k, dz, hdist;
	local vector delta;

	if (self.gj_state == 4)
	{
		self.frame = 144 + min (15, self.gj_step);
		return TRUE;
	}
	if (self.gj_state == 5)
	{
		self.frame = 160 + min (15, self.gj_step);
		return TRUE;
	}

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 24');
	rel = vectoyaw (delta) - self.angles_y;
	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 45 + 0.5);
	if (d >= 8)
		d = 0;

	k = floor ((time - self.gj_anim_t0) * 18);
	k = k - 6 * floor (k / 6);

	if (self.gj_state == 2)
	{
		self.frame = 48 + d * 6 + k;		// Vertical building wall-driver!
		return TRUE;
	}

	dz = delta_z;
	delta_z = 0;
	hdist = vlen (delta);

	if (dz > hdist * 1.73)
	{
		self.frame = 224 + d * 6 + k;		// >60 deg straight-down overhead hover!
		return TRUE;
	}
	if (dz > hdist * 0.58)
	{
		self.frame = 176 + d * 6 + k;		// 30-60 deg jetpack swoop overhead!
		return TRUE;
	}

	if (self.gj_state == 6)
		self.frame = 96 + d * 6 + k;		// Post-3-Lap Attack Lunge (Torpedo Charge + Sky-Point Ram)!
	else
		self.frame = d * 6 + k;				// Seated Wheel-Driving on spinning pneumatic tires!
	return TRUE;
};

// Swarm Attack Hit: light 2-dmg comedy pokes + boingy knockback ("was swarmed silly by"!)
void(entity m, entity victim) GJ_AttackHit =
{
	local vector boing;

	if (time < m.gj_next_poke || victim.health <= 0)
		return;
	if (m.owner.classname != "player")		// owner left: GJ_MiniThink pops it on its next tick
		return;
	m.gj_next_poke = time + 0.42 + random () * 0.25;

	// Light view-jiggle + boingy slapstick knockback + high-pitched shriek/giggle!
	if (victim.classname == "player")
	{
		victim.punchangle_x = crandom () * 1.0;
		victim.punchangle_z = crandom () * 1.2;
	}
	if (victim.movetype == MOVETYPE_WALK || victim.movetype == MOVETYPE_STEP)
	{
		boing = victim.origin - m.origin;
		boing_z = 0;
		if (vlen (boing) < 1)
			boing = '1 0 0';
		boing = normalize (boing);
		victim.flags = victim.flags - (victim.flags & FL_ONGROUND);
		victim.velocity = victim.velocity + boing * 180 + '0 0 185';
	}
	if (time >= m.gj_next_voice)
	{
		GJ_PlayRandomLaugh (m);
		m.gj_next_voice = time + 0.55 + random () * 0.45;
	}

	fg_inflicting = FG_PONG;
	T_Damage (victim, m, m.owner, 2);
	fg_inflicting = 0;
};

void() GJ_MiniTouch =
{
	local vector sep;

	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	if (self.gj_state == 4 || self.gj_state == 5)
		return;

	// Gentle go-kart bumper separation so 12 bigger wheeling Green Men never stack on each other
	if (other.classname == "greenguy_mini" && other != self)
	{
		sep = self.origin - other.origin;
		sep_z = 0;
		if (vlen (sep) < 1)
			sep = '1 0 0';
		sep = normalize (sep);
		self.velocity_x = self.velocity_x + sep_x * 65;
		self.velocity_y = self.velocity_y + sep_y * 65;
		return;
	}

	if (GJ_IsValidTarget (self, other))
	{
		self.enemy = other;
		// Bounce gently off target so 12 gremlins never wedge/pin players in corners
		sep = self.origin - other.origin;
		sep_z = 0;
		if (vlen (sep) < 1)
			sep = '1 0 0';
		sep = normalize (sep);
		self.velocity_x = sep_x * 220;
		self.velocity_y = sep_y * 220;
		self.velocity_z = max (self.velocity_z, 120);
		// ONLY attack if orbiting laps around the enemy are already complete (`gj_state == 6`)!
		if (self.gj_state == 6)
		{
			GJ_AttackHit (self, other);
			return;
		}
		// Otherwise begin swarming & orbiting around them FIRST (zero attack)!
		if (self.gj_state != 3)
		{
			self.gj_state = 3;
			self.gj_orbit_ang = vectoyaw (self.origin - other.origin);
			self.gj_prev_yaw = self.gj_orbit_ang;
		}
		return;
	}
};

// ================================================================
// GREEN MAN AI: WHEEL-DRIVE -> SWARM 3 LAPS AROUND ENEMY -> ATTACK!
// ================================================================

void() GJ_MiniThink =
{
	local vector dir, fwd_ang, goal, wall_check, roof_check, to_goal, vel_xy, tang;
	local float dist, spd, step_deg, cur_yaw, d_yaw, want_yaw, yaw_diff;

	if (self.gj_state == 4 || self.gj_state == 5)
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
	// owner left: stop fighting in an empty (or reused) slot's name; gj_attack_end 0 keeps the pop harmless
	if (self.owner.classname != "player")
	{
		self.gj_attack_end = 0;
		GJ_StartBalloonPop (self, TRUE);
		return;
	}

	// Settle tire bounce after initial radial smoke-pop so their spinning wheels hug the ground smoothly!
	if (time > self.fg_born + 0.38)
		self.bouncefactor = 0.12;

	// Continuous overlapping helium laughing, screaming & giggling!
	if (time >= self.gj_next_voice)
	{
		GJ_PlayRandomLaugh (self);
		self.gj_next_voice = time + 0.75 + random () * 0.95;
	}

	if (time < self.skypad_steer_t)
	{
		self.think = GJ_MiniThink;
		self.nextthink = time + 0.05;
		return;
	}

	// Refresh target if none or dead
	if (!GJ_IsValidTarget (self, self.enemy))
	{
		self.enemy = GJ_FindTarget (self);
		if (self.gj_state == 3 || self.gj_state == 6)
			self.gj_state = 1;
	}

	// ------------------------------------------------------------
	// STATE 6: POST-3-LAP SWARM ATTACK FRENZY -> BALLOON POP!
	// (Unleashed ONLY after driving 3 full laps around the enemy!)
	// ------------------------------------------------------------
	if (self.gj_state == 6 && GJ_IsValidTarget (self, self.enemy))
	{
		if (time >= self.gj_attack_end)
		{
			GJ_StartBalloonPop (self, FALSE);
			return;
		}

		to_goal = (self.enemy.origin + '0 0 18') - self.origin;
		dist = vlen (to_goal);
		self.angles_y = vectoyaw (self.enemy.origin - self.origin);

		fwd_ang = '0 0 0';
		fwd_ang_y = self.angles_y;
		makevectors (fwd_ang);

		spd = 485 + self.gj_role * 25;
		self.velocity_x = v_forward_x * spd;
		self.velocity_y = v_forward_y * spd;

		// Aggressive torpedo / pipe-vault ramming leaps straight at the enemy!
		if ((self.flags & FL_ONGROUND) && time >= self.gj_next_boing)
		{
			self.flags = self.flags - FL_ONGROUND;
			self.velocity_z = 215 + random () * 95;
			FG_Snd (self, CHAN_BODY, "greenjar/mini_boing.wav", 0.72, 0.96 + random () * 0.18);
			self.gj_next_boing = time + 0.38 + random () * 0.24;
		}

		if (dist < 78)
			GJ_AttackHit (self, self.enemy);

		self.think = GJ_MiniThink;
		self.nextthink = time + 0.05;
		return;
	}

	// ------------------------------------------------------------
	// STATE 3: SWARM & WHEEL-DRIVE 3 FULL LAPS AROUND ENEMY FIRST!
	// (Zero damage / zero attacking until 3 laps = 1080 deg done!)
	// ------------------------------------------------------------
	if (self.gj_state == 3 && GJ_IsValidTarget (self, self.enemy))
	{
		dist = vlen (self.enemy.origin - self.origin);
		if (dist > 360)
		{
			self.gj_state = 1;		// victim ran far off; wheel-chase them to finish the 3 laps!
		}
		else
		{
			// Measure real angular sweep around the enemy + steady cornering progress if hugging a wall
			cur_yaw = vectoyaw (self.origin - self.enemy.origin);
			d_yaw = cur_yaw - self.gj_prev_yaw;
			while (d_yaw > 180)
				d_yaw = d_yaw - 360;
			while (d_yaw < -180)
				d_yaw = d_yaw + 360;
			self.gj_prev_yaw = cur_yaw;

			step_deg = fabs (d_yaw);
			if (step_deg > 28)
				step_deg = 28;
			if (step_deg < 6 && dist < 130)
				step_deg = 6;		// ensure cornered enemies against walls still progress smoothly
			self.gj_orbit_deg = self.gj_orbit_deg + step_deg;

			// Completed 3 full driving laps (3 * 360 = 1080 deg) -> UNLEASH SWARM ATTACK!
			if (self.gj_orbit_deg >= GJ_ORBITS_BEFORE_ATK)
			{
				self.gj_state = 6;
				self.gj_attack_end = time + 4.2 + random () * 1.4;
				self.gj_next_poke = time;
				FG_Snd (self, CHAN_VOICE, "greenjar/mini_scream1.wav", 0.95, 1.02 + random () * 0.10);
				if (self.flags & FL_ONGROUND)
					self.flags = self.flags - FL_ONGROUND;
				dir = normalize ((self.enemy.origin + '0 0 20') - self.origin);
				self.velocity = dir * 460 + '0 0 190';
				self.angles_y = vectoyaw (self.enemy.origin - self.origin);
				self.think = GJ_MiniThink;
				self.nextthink = time + 0.05;
				return;
			}

			// Advance target angle ahead along the multi-lane go-kart circle (`R = 72..108u`)
			self.gj_orbit_ang = cur_yaw + (24 + self.gj_role * 3) * self.gj_orbit_dir;
			fwd_ang = '0 0 0';
			fwd_ang_y = self.gj_orbit_ang;
			makevectors (fwd_ang);

			goal = self.enemy.origin + v_forward * (self.gj_orbit_rad * 1.12);
			to_goal = goal - self.origin;
			to_goal_z = 0;

			// Tangential + radial wheel-driving velocity along the floor (tires stay grounded!)
			tang = normalize (to_goal);
			spd = 465 + self.gj_role * 25;
			self.velocity_x = tang_x * spd;
			self.velocity_y = tang_y * spd;

			// Face the forward driving tangent so all 12 visibly MOTOR in a circle on spinning tires!
			vel_xy = self.velocity;
			vel_xy_z = 0;
			if (vlen (vel_xy) > 20)
				self.angles_y = vectoyaw (vel_xy);

			// Small curb/stair hop ONLY if a low step blocks the circle path
			if ((self.flags & FL_ONGROUND) && time >= self.gj_next_boing)
			{
				traceline (self.origin + '0 0 8', self.origin + '0 0 8' + tang * 26, TRUE, self);
				if (trace_fraction < 0.92)
				{
					traceline (self.origin + '0 0 28', self.origin + '0 0 28' + tang * 28, TRUE, self);
					if (trace_fraction > 0.92)
					{
						self.flags = self.flags - FL_ONGROUND;
						self.velocity_z = 175;
						self.gj_next_boing = time + 0.30;
					}
				}
			}

			self.think = GJ_MiniThink;
			self.nextthink = time + 0.05;
			return;
		}
	}

	// ------------------------------------------------------------
	// STATE 2: VERTICAL BUILDING / PILLAR WALL-DRIVE!
	// ------------------------------------------------------------
	if (self.gj_state == 2)
	{
		wall_check = self.origin + '0 0 14' - self.gj_wall_n * 28;
		traceline (self.origin + '0 0 14', wall_check, TRUE, self);
		if (trace_fraction >= 0.98)
		{
			// Cleared the top ledge / roof of the building! Roll onto the roof!
			self.gj_state = 1;
			self.velocity = ('0 0 0' - self.gj_wall_n) * 240 + '0 0 195';
			FG_Snd (self, CHAN_BODY, "greenjar/mini_boing.wav", 0.75, 1.0 + random () * 0.15);
			self.think = GJ_MiniThink;
			self.nextthink = time + 0.05;
			return;
		}
		roof_check = self.origin + '0 0 46';
		traceline (self.origin + '0 0 16', roof_check, TRUE, self);
		if (trace_fraction < 0.95 || time >= self.gj_climb_end)
		{
			self.gj_state = 1;
			self.gj_wall_cool = time + 2.2;
			self.angles_y = vectoyaw (self.gj_wall_n) + crandom () * 45;
			self.velocity = self.gj_wall_n * 310 + '0 0 -50';
			FG_Snd (self, CHAN_BODY, "greenjar/mini_boing.wav", 0.75, 1.08);
			self.think = GJ_MiniThink;
			self.nextthink = time + 0.05;
			return;
		}

		if (self.flags & FL_ONGROUND)
			self.flags = self.flags - FL_ONGROUND;
		self.velocity = ('0 0 0' - self.gj_wall_n) * 75 + '0 0 285';
		self.angles_y = vectoyaw ('0 0 0' - self.gj_wall_n);
		self.think = GJ_MiniThink;
		self.nextthink = time + 0.05;
		return;
	}

	// ------------------------------------------------------------
	// STATE 1: GROUNDED WHEEL-DRIVING ROAM & APPROACH
	// ------------------------------------------------------------
	if (GJ_IsValidTarget (self, self.enemy))
	{
		dist = vlen (self.enemy.origin - self.origin);
		if (dist < 195)
		{
			// Reached enemy -> enter 3-Lap Wheel-Driving Swarm (or resume Attack if 3 laps already done)!
			if (self.gj_orbit_deg >= GJ_ORBITS_BEFORE_ATK)
				self.gj_state = 6;
			else
			{
				self.gj_state = 3;
				self.gj_orbit_ang = vectoyaw (self.origin - self.enemy.origin);
				self.gj_prev_yaw = self.gj_orbit_ang;
			}
			self.think = GJ_MiniThink;
			self.nextthink = time + 0.05;
			return;
		}
		want_yaw = vectoyaw (self.enemy.origin - self.origin) + crandom () * 10;
		yaw_diff = want_yaw - self.angles_y;
		while (yaw_diff > 180)
			yaw_diff = yaw_diff - 360;
		while (yaw_diff < -180)
			yaw_diff = yaw_diff + 360;
		if (yaw_diff > 26)
			yaw_diff = 26;
		if (yaw_diff < -26)
			yaw_diff = -26;
		self.angles_y = self.angles_y + yaw_diff;
	}
	else
	{
		// Smooth curving go-kart steering around the map!
		self.angles_y = self.angles_y + crandom () * 20;
	}
	self.angles_y = self.angles_y - 360 * floor (self.angles_y / 360);

	fwd_ang = '0 0 0';
	fwd_ang_y = self.angles_y;
	makevectors (fwd_ang);

	// Check for stairs (curb-hop) vs tall vertical building wall (wall-drive or steer off!)
	traceline (self.origin + '0 0 8', self.origin + '0 0 8' + v_forward * 28, TRUE, self);
	if (trace_fraction < 0.94)
	{
		traceline (self.origin + '0 0 30', self.origin + '0 0 30' + v_forward * 30, TRUE, self);
		if (trace_fraction > 0.94)
		{
			// Low stair/curb -> smooth wheelie hop up the step!
			if ((self.flags & FL_ONGROUND) && time >= self.gj_next_boing)
			{
				self.flags = self.flags - FL_ONGROUND;
				self.velocity_z = 185;
				self.gj_next_boing = time + 0.25;
			}
		}
		else if (fabs (trace_plane_normal_z) < 0.28)
		{
			if (self.gj_role == 2 && time >= self.gj_wall_cool)
			{
				// Role-2 wall-driver drives straight up the building wall!
				self.gj_state = 2;
				self.gj_wall_n = trace_plane_normal;
				self.gj_climb_end = time + 1.10;
				if (self.flags & FL_ONGROUND)
					self.flags = self.flags - FL_ONGROUND;
				self.velocity = ('0 0 0' - self.gj_wall_n) * 65 + '0 0 280';
				self.think = GJ_MiniThink;
				self.nextthink = time + 0.05;
				return;
			}
			else
			{
				// Steer briskly along/away from the wall and keep wheeling!
				self.angles_y = vectoyaw (trace_plane_normal) + crandom () * 55;
				fwd_ang_y = self.angles_y;
				makevectors (fwd_ang);
			}
		}
	}

	spd = 460 + self.gj_role * 25;
	self.velocity_x = v_forward_x * spd;
	self.velocity_y = v_forward_y * spd;

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
		if (e.owner == who && e.gj_state != 5)
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
	m.netname = "Green Wheelman";
	m.owner = who;
	m.fg_born = time;
	m.gj_anim_t0 = time - random () * 0.5;
	m.gj_state = 1;
	m.gj_role = idx - 3 * floor (idx / 3);					// 0=cruiser, 1=sprinter, 2=wall-driver
	m.gj_orbit_dir = (idx - 2 * floor (idx / 2)) * 2 - 1;	// alternating CW / CCW driving lanes!
	m.gj_orbit_rad = 72 + (idx - 4 * floor (idx / 4)) * 12;	// 72..108u 4-lane go-kart circle around victim!
	m.gj_orbit_deg = 0;
	m.gj_attack_end = 0;
	m.gj_die_at = time + 18.5 + random () * 3.0;
	m.gj_next_voice = time + 0.08 * idx + random () * 0.25;
	m.gj_next_boing = time + 0.35;
	m.gj_next_poke = time + 0.2;

	m.movetype = MOVETYPE_BOUNCE;
	m.solid = SOLID_BBOX;
	m.bouncefactor = 0.42;		// settles to 0.12 after 0.38s so tires hug the floor smoothly!
	m.bouncestop = 0.08;
	m.gravity = 0.85;
	m.health = 1;
	m.max_health = 1;
	m.takedamage = DAMAGE_AIM;
	m.th_pain = GJ_MiniPain;
	m.th_die = GJ_MiniDie;
	m.touch = GJ_MiniTouch;
	m.customizeentityforclient = GJ_MiniCustomize;

	setmodel (m, "progs/greenguy_mini.spr32");
	m.scale = 0.9333;			// ~2.3x bigger in-world: waist-to-chest height mini-wheelman!
	setsize (m, '-8 -8 0', '8 8 34');

	yaw = idx * (360 / GJ_MINI_COUNT) + crandom () * 12;
	ang_v = '0 0 0';
	ang_v_y = yaw;
	makevectors (ang_v);

	setorigin (m, org + v_forward * 14 + '0 0 8');
	m.angles = '0 0 0';
	m.angles_y = yaw;
	m.velocity = v_forward * (280 + random () * 180);
	m.velocity_z = 135 + random () * 115;

	m.enemy = GJ_FindTarget (m);
	m.think = GJ_MiniThink;
	m.nextthink = time + 0.06 + idx * 0.01;
	PC_Register (m, PC_KIND_LIGHT, 18);
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
	sendParticle ("pk_puff", org + '0 0 12', '0 0 0', 6, 0);

	b = spawn ();
	b.classname = "greenjar_burst";
	b.movetype = MOVETYPE_NONE;
	b.solid = SOLID_NOT;
	setmodel (b, "progs/greenjar_burst.spr32");
	b.scale = 1.85;
	b.frame = 0;
	b.effects = EF_DIMLIGHT;
	setorigin (b, org + '0 0 16');
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
	PC_Register (jar, PC_KIND_LIGHT, 20);
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
	local float busy, ammo;

	busy = (self.health <= 0 || self.deadflag || intermission_running
		|| FD_Flying (self) || Veh_Driving (self) || JohnBird_Flying (self) || RocketRider_Flying (self)
		|| EricCannon_Active (self) || MMTank_Driving (self));
	if (busy)
	{
		if (self.gj_shaking > 0)
			sound (self, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
		if (self.gj_throw_at > 0 && self.health > 0 && !self.deadflag && !intermission_running)
		{
			ammo = FunGun_Ammo (self, FG_PONG);
			if (ammo < FunGun_Max (FG_PONG))
				FunGun_SetAmmo (self, FG_PONG, ammo + 1);
		}
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
