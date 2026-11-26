/*
bklan5_npcs.qc — Bakersfield Street Encounters:
  1) npc_greensuit_wheelman / monster_greensuit_wheelman
     (progs/greensuit_wheelman.spr32 — 248 frames, 8-angle 360° hostile jumping monster!)
     Prowls in Seated Low-Rider Cruise, pops a Wheelie Battle-Cry on spotting a player, sprints in
     Screaming Ab-Roller Torpedo Charge, launches Pipe-Vault Mid-Air Crane-Kick Sky-Point Jumps with
     Axle Shockwave Slams, swings 360° Wheel-Bar Whirlwind Melee, and detonates into Quake Mega-Gibs!
  2) npc_robeguy (progs/robeguy.spr32 — 228 frames, 8-dir 360° harmless "The Flamingo Fiend")

Cheat test impulses (with sv_cheats 1):
  impulse 46  Summon Hostile Green-Suit Wheelman Monster in front of you
  impulse 47  Summon The Flamingo Fiend (robeguy) in front of you
*/

.float	npc_state;
.float	npc_phase_end;
.float	npc_next_stunt;
.float	npc_next_voice;
.float	npc_respawn;
.float	npc_radius;
.vector	npc_home;

.float	gs_anim_t0;
.float	gs_jump_step;
.float	gs_jump_launched;
.float	gs_next_jump;
.float	gs_next_pain;
.float	gs_next_touch;
.float	gs_melee_hit;

void() GreenSuit_Think;
void() GreenSuit_Die;
void() GreenSuit_Touch;
void(entity attacker, float take) GreenSuit_Pain;
void() RobeGuy_Think;
void() RobeGuy_Die;
void(entity attacker, float take) RobeGuy_Pain;

float NPC_SF_QUIET = 2;

float(entity e) NPC_IsVoiceMuted =
{
	if (e.spawnflags & NPC_SF_QUIET)
		return TRUE;
	if (world.model == "maps/soicowboy_bkk.bsp")
		return TRUE;
	return FALSE;
};

// ================================================================================================
// 1. GREEN-SUIT WHEELMAN MONSTER (progs/greensuit_wheelman.spr32 — 248 frames, 8 compass angles)
//   0   + d*4 + k   8-dir Seated Low-Rider Cruise      (k = 0..3, 32f: 0..31)
//   32  + d*4 + k   8-dir Ab-Roller Torpedo Charge     (k = 0..3, 32f: 32..63)
//   64  + d*6 + s   8-dir Pipe-Vault Sky-Point Slam    (s = 0..5, 48f: 64..111)
//   112 + d*4 + s   8-dir 360° Whirlwind Melee         (s = 0..3, 32f: 112..143)
//   144 + d*4 + k   8-dir Wheelie Burnout Battle-Cry   (k = 0..3, 32f: 144..175)
//   176 + d*4 + s   8-dir Impact Recoil & Tire Skid    (s = 0..3, 32f: 176..207)
//   208 + d*5 + s   8-dir Bloody Quake Mega-Gib Death  (s = 0..4, 40f: 208..247)
// ================================================================================================

void() GreenSuit_Precache =
{
	if (greensuit_precached)
		return;
	greensuit_precached = TRUE;
	precache_model("progs/greensuit_wheelman.spr32");
	precache_model("progs/gib1.mdl");
	precache_model("progs/gib2.mdl");
	precache_model("progs/gib3.mdl");
	precache_sound("weapons/r_exp3.wav");
	precache_sound("weapons/lstart.wav");
	precache_sound("weapons/ax1.wav");
	precache_sound("demon/djump.wav");
	precache_sound("demon/dland2.wav");
	precache_sound("player/udeath.wav");
	precache_sound("player/pain4.wav");
	precache_sound("vehicles/idle_coupe.wav");
};

float() GreenSuit_Customize =
{
	local float rel, d, k, st, s;
	local vector delta;

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 26');
	rel = vectoyaw(delta) - self.angles_y;
	rel = rel - 360 * floor(rel / 360);
	d = floor(rel / 45 + 0.5);
	if (d >= 8)
		d = 0;

	if (self.npc_dead)
	{
		s = floor(self.npc_dstep * 0.5);
		if (s < 0)
			s = 0;
		if (s > 4)
			s = 4;
		self.frame = 208 + d * 5 + s;
		return TRUE;
	}

	st = self.npc_state;
	if (st == 6)	// Pain recoil (4 steps)
	{
		s = floor((time - self.gs_anim_t0) * 11.5);
		if (s < 0)
			s = 0;
		if (s > 3)
			s = 3;
		self.frame = 176 + d * 4 + s;
		return TRUE;
	}
	if (st == 3)	// Pipe-Vault Sky-Point Jump & Slam (6 steps)
	{
		s = floor(self.gs_jump_step * 0.5);
		if (s < 0)
			s = 0;
		if (s > 5)
			s = 5;
		self.frame = 64 + d * 6 + s;
		return TRUE;
	}
	if (st == 4)	// 360° Whirlwind Battering-Ram Melee (4 steps)
	{
		s = floor((time - self.gs_anim_t0) * 7.5);
		if (s < 0)
			s = 0;
		if (s > 3)
			s = 3;
		self.frame = 112 + d * 4 + s;
		return TRUE;
	}
	if (st == 5)	// Wheelie Burnout Battle-Cry (4-step loop)
	{
		k = floor(time * 8 + self.origin_x * 0.01);
		k = k - 4 * floor(k / 4);
		self.frame = 144 + d * 4 + k;
		return TRUE;
	}
	if (st == 2)	// Screaming Ab-Roller Torpedo Charge (4-step loop)
	{
		k = floor(time * 10 + self.origin_x * 0.01 + self.origin_y * 0.01);
		k = k - 4 * floor(k / 4);
		self.frame = 32 + d * 4 + k;
		return TRUE;
	}

	// Default st == 1: Seated Low-Rider Cruise (4-step loop)
	k = floor(time * 7.5 + self.origin_x * 0.01 + self.origin_y * 0.01);
	k = k - 4 * floor(k / 4);
	self.frame = d * 4 + k;
	return TRUE;
};

entity() GreenSuit_FindPlayer =
{
	local entity p, best;
	local float dist, best_d;

	best = world;
	best_d = 1450;
	p = find(world, classname, "player");
	while (p)
	{
		if (p.health > 0 && p.solid != SOLID_NOT && !(p.flags & FL_NOTARGET))
		{
			dist = vlen(p.origin - self.origin);
			if (dist < best_d)
			{
				traceline(self.origin + '0 0 32', p.origin + '0 0 24', TRUE, self);
				if (trace_fraction >= 0.98 || dist < 320)
				{
					best = p;
					best_d = dist;
				}
			}
		}
		p = find(p, classname, "player");
	}
	return best;
};

void(float rad, float dmg) GreenSuit_SlamBlast =
{
	local entity e;
	local vector dir;

	particle(self.origin + '0 0 8', '0 0 40', 232, 48);
	e = findradius(self.origin, rad);
	while (e)
	{
		if (e != self && e.takedamage && e.health > 0 && e.classname != "npc_greensuit_wheelman")
		{
			T_Damage(e, self, self, dmg);
			dir = normalize((e.origin + '0 0 16') - self.origin);
			e.velocity = e.velocity + dir * 250 + '0 0 150';
			if (e.flags & FL_ONGROUND)
				e.flags = e.flags - FL_ONGROUND;
		}
		e = e.chain;
	}
};

void() GreenSuit_Touch =
{
	local vector dir;
	local float dmg;

	if (self.npc_dead || self.health <= 0)
		return;
	if (other == world || !other.takedamage || other.health <= 0)
		return;
	if (other.classname == "npc_greensuit_wheelman")
		return;
	if (time < self.gs_next_touch)
		return;

	if (self.npc_state == 3 && self.gs_jump_launched == 1)
		dmg = 24;	// Flying Crane-Kick / Stainless Pipe Dive impact!
	else if (self.npc_state == 2)
		dmg = 12;	// Ab-Roller Torpedo ramming contact!
	else
		return;

	self.gs_next_touch = time + 0.45;
	sound(self, CHAN_WEAPON, "demon/dland2.wav", 0.9, ATTN_NORM);
	T_Damage(other, self, self, dmg);
	dir = normalize((other.origin + '0 0 16') - self.origin);
	other.velocity = other.velocity + dir * 240 + '0 0 130';
	if (other.flags & FL_ONGROUND)
		other.flags = other.flags - FL_ONGROUND;
};

void() GreenSuit_Respawn =
{
	setorigin(self, self.npc_home + '0 0 12');
	setmodel(self, "progs/greensuit_wheelman.spr32");
	self.scale = 0.8036;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 165;
	self.max_health = 165;
	self.takedamage = DAMAGE_AIM;
	self.effects = 0;
	self.alpha = 1;
	self.enemy = world;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	self.npc_state = 1;
	self.gs_jump_step = 0;
	self.gs_jump_launched = 0;
	self.npc_phase_end = time + 2.0;
	self.gs_next_jump = time + 1.5;
	if (self.target != "")
		self.goalentity = find(world, targetname, self.target);
	setsize(self, '-18 -18 0', '18 18 54');
	droptofloor();
	self.touch = GreenSuit_Touch;
	self.think = GreenSuit_Think;
	self.nextthink = time + 0.05;
};

void() GreenSuit_DeathStep =
{
	self.npc_dstep = self.npc_dstep + 1;
	if (self.npc_dstep <= 9)
	{
		self.think = GreenSuit_DeathStep;
		self.nextthink = time + 0.065;
		return;
	}
	self.effects = 0;
	if (self.npc_dstep == 10)
	{
		self.think = GreenSuit_DeathStep;
		self.nextthink = time + 2.2;
		return;
	}
	if (self.npc_dstep <= 16)
	{
		self.alpha = 1.0 - (self.npc_dstep - 10) * 0.15;
		self.think = GreenSuit_DeathStep;
		self.nextthink = time + 0.07;
		return;
	}
	self.alpha = 1;
	if (self.npc_respawn > 0)
	{
		setmodel(self, "");
		self.think = GreenSuit_Respawn;
		self.nextthink = time + self.npc_respawn;
		return;
	}
	remove(self);
};

void() GreenSuit_Die =
{
	if (self.npc_dead)
		return;
	self.npc_dead = 2;
	self.npc_dstep = 0;
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.effects = EF_DIMLIGHT;

	sound(self, CHAN_VOICE, "player/udeath.wav", 1, ATTN_NORM);
	sound(self, CHAN_AUTO, "weapons/r_exp3.wav", 0.85, ATTN_NORM);
	ThrowGib("progs/gib1.mdl", -75);
	ThrowGib("progs/gib2.mdl", -85);
	ThrowGib("progs/gib3.mdl", -95);
	particle(self.origin + '0 0 24', '0 0 30', 73, 55);

	self.think = GreenSuit_DeathStep;
	self.nextthink = time + 0.065;
};

void(entity attacker, float take) GreenSuit_Pain =
{
	if (self.health <= 0 || self.npc_dead)
		return;
	if (attacker != world && attacker != self && attacker.takedamage && attacker.classname != "npc_greensuit_wheelman")
		self.enemy = attacker;

	// Do not interrupt mid-air Pipe-Vault Jump ballistic physics
	if (self.npc_state == 3 && self.gs_jump_launched == 1)
		return;
	if (time < self.gs_next_pain)
		return;

	self.gs_next_pain = time + 1.35;
	self.npc_state = 6;
	self.gs_anim_t0 = time;
	self.npc_phase_end = time + 0.35;
	self.movetype = MOVETYPE_STEP;
	sound(self, CHAN_VOICE, "player/pain4.wav", 1, ATTN_NORM);
};

void() GreenSuit_Think =
{
	local float want, diff, step_dist, dist, elapsed;
	local vector flat_d, jump_dir;
	local entity targ;

	if (self.health <= 0)
	{
		GreenSuit_Die();
		return;
	}

	// 1. Handle active Pipe-Vault Mid-Air Crane-Kick Jump & Axle Shockwave Slam!
	if (self.npc_state == 3)
	{
		elapsed = time - self.gs_anim_t0;
		if (self.gs_jump_launched == 0)
		{
			// Brief 0.16s stainless pipe-vault plant before rocketing skyward!
			self.gs_jump_step = floor(elapsed * 18);
			if (self.gs_jump_step > 2)
				self.gs_jump_step = 2;
			if (self.enemy != world && self.enemy.health > 0)
				self.angles_y = vectoyaw(self.enemy.origin - self.origin);
			if (elapsed >= 0.16)
			{
				self.gs_jump_launched = 1;
				self.movetype = MOVETYPE_TOSS;
				if (self.flags & FL_ONGROUND)
					self.flags = self.flags - FL_ONGROUND;
				makevectors('0 1 0' * self.angles_y);
				jump_dir = v_forward;
				self.velocity = jump_dir * 465 + '0 0 355';
				self.origin_z = self.origin_z + 2;
				setorigin(self, self.origin);
				sound(self, CHAN_VOICE, "demon/djump.wav", 1, ATTN_NORM);
			}
			self.think = GreenSuit_Think;
			self.nextthink = time + 0.05;
			return;
		}
		else if (self.gs_jump_launched == 1)
		{
			// Airborne Crane-Kick & Sky-Point arc!
			if (self.velocity_z > 80)
				self.gs_jump_step = 4;
			else if (self.velocity_z > -80)
				self.gs_jump_step = 6;		// Peak Hero Sky-Point ("OOOO!")
			else
				self.gs_jump_step = 8;		// Meteor Axle Dive!

			if ((elapsed > 0.32 && (self.flags & FL_ONGROUND)) || elapsed > 1.45)
			{
				// Touchdown -> Spark-Shower Axle Shockwave Slam!
				self.gs_jump_launched = 2;
				self.gs_jump_step = 10;
				self.movetype = MOVETYPE_STEP;
				self.velocity = '0 0 0';
				droptofloor();
				sound(self, CHAN_BODY, "demon/dland2.wav", 1, ATTN_NORM);
				GreenSuit_SlamBlast(135, 20);
				self.npc_phase_end = time + 0.22;
			}
			self.think = GreenSuit_Think;
			self.nextthink = time + 0.05;
			return;
		}
		else
		{
			// Slam recovery frames (10..11) -> back to Torpedo Charge!
			self.gs_jump_step = 11;
			if (time >= self.npc_phase_end)
			{
				self.npc_state = 2;
				self.gs_next_jump = time + 2.4 + random() * 1.2;
			}
			self.think = GreenSuit_Think;
			self.nextthink = time + 0.05;
			return;
		}
	}

	// 2. Handle Pain Recoil window
	if (self.npc_state == 6)
	{
		if (time < self.npc_phase_end)
		{
			self.think = GreenSuit_Think;
			self.nextthink = time + 0.05;
			return;
		}
		self.npc_state = 2;
	}

	// 3. Handle 360° Wheel-Bar Whirlwind Battering-Ram Melee!
	if (self.npc_state == 4)
	{
		elapsed = time - self.gs_anim_t0;
		if (!self.gs_melee_hit && elapsed >= 0.22)
		{
			self.gs_melee_hit = TRUE;
			GreenSuit_SlamBlast(122, 18);
		}
		if (elapsed < 0.52)
		{
			self.think = GreenSuit_Think;
			self.nextthink = time + 0.05;
			return;
		}
		self.npc_state = 2;
	}

	// 4. Handle Wheelie Burnout Battle-Cry Taunt!
	if (self.npc_state == 5)
	{
		if (self.enemy != world && self.enemy.health > 0)
			self.angles_y = vectoyaw(self.enemy.origin - self.origin);
		if (time < self.npc_phase_end)
		{
			self.think = GreenSuit_Think;
			self.nextthink = time + 0.05;
			return;
		}
		self.effects = 0;
		self.npc_state = 2;
	}

	// 5. Validate or acquire live hostile target!
	if (self.enemy != world && (self.enemy.health <= 0 || self.enemy.solid == SOLID_NOT || (self.enemy.flags & FL_NOTARGET)))
		self.enemy = world;

	if (self.enemy == world)
	{
		targ = GreenSuit_FindPlayer();
		if (targ != world)
		{
			self.enemy = targ;
			self.npc_state = 5;		// Pop a Wheelie Battle-Cry when spotting prey!
			self.effects = EF_DIMLIGHT;
			self.gs_anim_t0 = time;
			self.npc_phase_end = time + 0.50;
			self.gs_next_jump = time + 1.1;
			sound(self, CHAN_VOICE, "weapons/lstart.wav", 0.9, ATTN_NORM);
			self.think = GreenSuit_Think;
			self.nextthink = time + 0.05;
			return;
		}
	}

	// Rolling tire/axle hum
	if (time > self.npc_next_voice)
	{
		sound(self, CHAN_BODY, "vehicles/idle_coupe.wav", 0.30, 2.0);
		self.npc_next_voice = time + 3.2 + random() * 1.4;
	}

	// 6. Hostile Combat Pursuit vs Peaceful Seated Low-Rider Patrol!
	if (self.enemy != world)
	{
		self.npc_state = 2;		// Screaming Ab-Roller Torpedo Charge!
		flat_d = self.enemy.origin - self.origin;
		flat_d_z = 0;
		dist = vlen(flat_d);
		want = vectoyaw(flat_d);

		// Close range -> 360° Wheel-Bar Whirlwind Battering-Ram!
		if (dist < 112)
		{
			self.npc_state = 4;
			self.gs_anim_t0 = time;
			self.gs_melee_hit = FALSE;
			self.angles_y = want;
			sound(self, CHAN_WEAPON, "weapons/ax1.wav", 1, ATTN_NORM);
			self.think = GreenSuit_Think;
			self.nextthink = time + 0.05;
			return;
		}

		// Mid range -> Pipe-Vault Sky-Point Jump & Axle Slam!
		if (dist >= 145 && dist <= 520 && time >= self.gs_next_jump)
		{
			traceline(self.origin + '0 0 36', self.enemy.origin + '0 0 28', TRUE, self);
			if (trace_fraction >= 0.95)
			{
				self.npc_state = 3;
				self.gs_anim_t0 = time;
				self.gs_jump_step = 0;
				self.gs_jump_launched = 0;
				self.angles_y = want;
				self.think = GreenSuit_Think;
				self.nextthink = time + 0.05;
				return;
			}
		}
	}
	else
	{
		self.npc_state = 1;		// Cheeky Seated Low-Rider Cruise!
		if (self.goalentity != world && (self.goalentity.flags & (FL_CLIENT | FL_MONSTER)))
			self.goalentity = world;
		if (self.target != "" && self.goalentity == world)
			self.goalentity = find(world, targetname, self.target);

		if (self.goalentity != world && !(self.goalentity.flags & (FL_CLIENT | FL_MONSTER)))
		{
			flat_d = self.goalentity.origin - self.origin;
			flat_d_z = 0;
			if (vlen(flat_d) < 110 && self.goalentity.target != "")
				self.goalentity = find(world, targetname, self.goalentity.target);
			want = vectoyaw(self.goalentity.origin - self.origin);
		}
		else if (self.npc_radius > 0 && vlen(self.origin - self.npc_home) > self.npc_radius)
			want = vectoyaw(self.npc_home - self.origin) + (random() - 0.5) * 35;
		else
			want = self.angles_y + (random() - 0.5) * 18;
	}

	diff = want - self.angles_y;
	while (diff > 180)
		diff = diff - 360;
	while (diff < -180)
		diff = diff + 360;
	self.angles_y = self.angles_y + diff * 0.34;

	step_dist = 11.5;		// ~230 u/s Seated Low-Rider Cruise
	if (self.npc_state == 2)
		step_dist = 18.0;	// ~360 u/s Ab-Roller Torpedo Charge!

	if (!walkmove(self.angles_y, step_dist))
	{
		if (!walkmove(self.angles_y + 42, step_dist * 0.85))
		{
			if (!walkmove(self.angles_y - 42, step_dist * 0.85))
			{
				self.angles_y = self.angles_y + 115 + random() * 70;
				while (self.angles_y >= 360)
					self.angles_y = self.angles_y - 360;
				walkmove(self.angles_y, step_dist * 0.75);
			}
			else
				self.angles_y = self.angles_y - 32;
		}
		else
			self.angles_y = self.angles_y + 32;
	}

	self.think = GreenSuit_Think;
	self.nextthink = time + 0.05;
};

void() npc_greensuit_wheelman =
{
	if (BM_NoMapNPC ())		// no map NPCs unless bm_npcs 1 (2026-11-26)
	{
		remove (self);
		return;
	}
	GreenSuit_Precache();
	self.classname = "npc_greensuit_wheelman";
	setmodel(self, "progs/greensuit_wheelman.spr32");
	self.scale = 0.8036;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 165;
	self.max_health = 165;
	self.takedamage = DAMAGE_AIM;
	self.th_stand = GreenSuit_Think;
	self.th_walk = GreenSuit_Think;
	self.th_run = GreenSuit_Think;
	self.th_melee = GreenSuit_Think;
	self.th_missile = GreenSuit_Think;
	self.th_pain = GreenSuit_Pain;
	self.th_die = GreenSuit_Die;
	self.touch = GreenSuit_Touch;
	self.customizeentityforclient = GreenSuit_Customize;
	self.npc_state = 1;
	self.gs_jump_step = 0;
	self.gs_jump_launched = 0;
	self.npc_phase_end = time + 2.0 + random() * 1.5;
	self.gs_next_jump = time + 1.2 + random() * 1.5;
	self.npc_next_voice = time + 0.8 + random() * 1.5;
	if (self.npc_respawn == 0)
		self.npc_respawn = 25;		// -1 (a summon) = never comes back
	if (self.npc_radius <= 0)
		self.npc_radius = 680;
	self.flags = FL_MONSTER;
	setsize(self, '-18 -18 0', '18 18 54');
	droptofloor();
	self.npc_home = self.origin;
	self.think = GreenSuit_Think;
	self.nextthink = time + 0.1 + random() * 0.2;
};

void() monster_greensuit_wheelman =
{
	npc_greensuit_wheelman();
};

void() GreenSuit_Summon =
{
	local vector flat_ang;
	local entity e, oself;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	e = spawn();
	e.origin = self.origin + v_forward * 220 + '0 0 20';
	e.angles_y = self.v_angle_y + 180;
	e.npc_respawn = -1;		// a summon does not respawn (0 would be read as the default 25 s)
	oself = self;
	self = e;
	npc_greensuit_wheelman();
	self = oself;
};


// ================================================================================================
// 2. THE FLAMINGO FIEND (`robeguy`, progs/robeguy.spr32 — 228 frames, 96x108, scale 0.7467)
//   0..7             8-dir Standing Idle keyposes
//   8 + d*6 + k      8-dir Barefoot Berserker Charge Run (k = 0..5)
//   56 + d*4 + k     8-dir Animated Unhinged Flamingo Whisperer Idle (k = 0..3)
//   88 + d*6 + k     8-dir Heart-Boxers Chest-Hair Laser comedic flash (k = 0..5, 0 damage!)
//   136 + d*6 + k    8-dir Dual Lawn-Flamingo & Hot-Coffee pose (k = 0..5, 0 damage!)
//   184..195         12-frame 4-Act Flamingo Feather & Gib Explosion!
//   196 + d*4 + s    8-dir Falling Collapse Death (s = 0..3)
// ================================================================================================

void() RobeGuy_Precache =
{
	if (robeguy_precached)
		return;
	robeguy_precached = TRUE;
	precache_model("progs/robeguy.spr32");
	precache_model("progs/gib1.mdl");
	precache_model("progs/gib2.mdl");
	precache_model("progs/gib3.mdl");
	precache_sound("robeguy/idle_honk_growl.wav");
	precache_sound("robeguy/berserker_yell.wav");
	precache_sound("robeguy/chest_laser_flash.wav");
	precache_sound("robeguy/flamingo_whack.wav");
	precache_sound("robeguy/feather_gib_boom.wav");
	precache_sound("player/udeath.wav");
};

float() RobeGuy_Customize =
{
	local float rel, d, k, st, s;
	local vector delta;

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 28');
	rel = vectoyaw(delta) - self.angles_y;
	rel = rel - 360 * floor(rel / 360);
	d = floor(rel / 45 + 0.5);
	if (d >= 8)
		d = 0;

	if (self.npc_dead == 2)
	{
		s = floor(self.npc_dstep * 0.5);
		if (s < 0)
			s = 0;
		if (s > 11)
			s = 11;
		self.frame = 184 + s;
		return TRUE;
	}
	if (self.npc_dead == 1)
	{
		s = floor(self.npc_dstep * 0.67);
		if (s < 0)
			s = 0;
		if (s > 3)
			s = 3;
		self.frame = 196 + d * 4 + s;
		return TRUE;
	}

	st = self.npc_state;
	if (st <= 0)
	{
		self.frame = d;
		return TRUE;
	}

	if (st == 1)
	{
		// 6-frame Barefoot Berserker Run
		k = floor(time * 15 + self.origin_x * 0.03);
		k = k - 6 * floor(k / 6);
		self.frame = 8 + d * 6 + k;
		return TRUE;
	}
	if (st == 2)
	{
		// 4-frame Animated Flamingo Whisperer Idle
		k = floor(time * 5 + self.origin_y * 0.01);
		k = k - 4 * floor(k / 4);
		self.frame = 56 + d * 4 + k;
		return TRUE;
	}
	if (st == 3)
	{
		// 6-frame Heart-Boxers Chest-Hair Laser comedic flash
		k = floor(time * 6);
		k = k - 6 * floor(k / 6);
		self.frame = 88 + d * 6 + k;
		return TRUE;
	}
	// st == 4: 6-frame Dual Lawn-Flamingo & Hot-Coffee wave
	k = floor(time * 6);
	k = k - 6 * floor(k / 6);
	self.frame = 136 + d * 6 + k;
	return TRUE;
};

void() RobeGuy_Respawn =
{
	setorigin(self, self.npc_home + '0 0 12');
	setmodel(self, "progs/robeguy.spr32");
	self.scale = 0.7467;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 145;
	self.max_health = 145;
	self.takedamage = DAMAGE_AIM;
	self.effects = 0;
	self.alpha = 1;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	self.npc_state = 1;
	self.npc_phase_end = time + 2.8;
	self.npc_next_stunt = time + 4.5;
	setsize(self, '-18 -18 0', '18 18 58');
	droptofloor();
	self.think = RobeGuy_Think;
	self.nextthink = time + 0.05;
};

void() RobeGuy_DeathStep =
{
	self.npc_dstep = self.npc_dstep + 1;
	if (self.npc_dead == 2)
	{
		if (self.npc_dstep <= 23)
		{
			self.think = RobeGuy_DeathStep;
			self.nextthink = time + 0.05;
			return;
		}
		self.effects = 0;
		if (self.npc_respawn > 0)
		{
			setmodel(self, "");
			self.think = RobeGuy_Respawn;
			self.nextthink = time + self.npc_respawn;
			return;
		}
		remove(self);
		return;
	}
	if (self.npc_dstep <= 5)
	{
		self.think = RobeGuy_DeathStep;
		self.nextthink = time + 0.075;
		return;
	}
	if (self.npc_dstep == 6)
	{
		self.think = RobeGuy_DeathStep;
		self.nextthink = time + 2.2;
		return;
	}
	if (self.npc_dstep <= 13)
	{
		self.alpha = 1.0 - (self.npc_dstep - 6) * 0.13;
		self.think = RobeGuy_DeathStep;
		self.nextthink = time + 0.07;
		return;
	}
	self.alpha = 1;
	if (self.npc_respawn > 0)
	{
		setmodel(self, "");
		self.think = RobeGuy_Respawn;
		self.nextthink = time + self.npc_respawn;
		return;
	}
	remove(self);
};

void() RobeGuy_Die =
{
	if (self.npc_dead)
		return;
	self.npc_dstep = 0;
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';

	if (NPC_ShouldGib(self))
	{
		self.npc_dead = 2;
		self.effects = EF_DIMLIGHT;
		if (!NPC_IsVoiceMuted(self))
		{
			sound(self, CHAN_VOICE, "robeguy/feather_gib_boom.wav", 1, ATTN_NORM);
			sound(self, CHAN_AUTO, "player/udeath.wav", 0.85, ATTN_NORM);
		}
		ThrowGib("progs/gib1.mdl", -70);
		ThrowGib("progs/gib2.mdl", -80);
		ThrowGib("progs/gib3.mdl", -90);
		self.think = RobeGuy_DeathStep;
		self.nextthink = time + 0.05;
		return;
	}

	self.npc_dead = 1;
	self.effects = 0;
	self.alpha = 1;
	if (!NPC_IsVoiceMuted(self))
		sound(self, CHAN_VOICE, "robeguy/berserker_yell.wav", 1, ATTN_NORM);
	self.think = RobeGuy_DeathStep;
	self.nextthink = time + 0.075;
};

void(entity attacker, float take) RobeGuy_Pain =
{
	if (self.health <= 0 || self.npc_dead)
		return;
	self.effects = 0;
	self.npc_state = 1;		// Barefoot panic sprint!
	self.npc_phase_end = time + 2.0;
	if (!NPC_IsVoiceMuted(self) && time > self.npc_next_voice)
	{
		sound(self, CHAN_VOICE, "robeguy/berserker_yell.wav", 0.9, ATTN_NORM);
		self.npc_next_voice = time + 1.6;
	}
};

void() RobeGuy_Think =
{
	local float want, diff, r;

	if (self.health <= 0)
	{
		RobeGuy_Die();
		return;
	}

	if (time >= self.npc_phase_end)
	{
		self.effects = 0;
		if (time >= self.npc_next_stunt)
		{
			r = random();
			if (r < 0.36)
			{
				self.npc_state = 2;		// Flamingo Whisperer Idle
				self.npc_phase_end = time + 1.6;
				if (!NPC_IsVoiceMuted(self))
					sound(self, CHAN_VOICE, "robeguy/idle_honk_growl.wav", 0.55, 1.8);
			}
			else if (r < 0.68)
			{
				self.npc_state = 3;		// Comedic Heart-Boxers Chest-Hair Laser pose (0 dmg!)
				self.effects = 128;		// EF_RED warm magenta-red glow
				self.npc_phase_end = time + 1.05;
				if (!NPC_IsVoiceMuted(self))
					sound(self, CHAN_VOICE, "robeguy/chest_laser_flash.wav", 0.55, 1.8);
			}
			else
			{
				self.npc_state = 4;		// Dual Lawn-Flamingo & Coffee wave (0 dmg!)
				self.npc_phase_end = time + 1.1;
				if (!NPC_IsVoiceMuted(self))
					sound(self, CHAN_VOICE, "robeguy/flamingo_whack.wav", 0.55, 1.8);
			}
			self.npc_next_stunt = time + 5.5 + random() * 3.5;
		}
		else
		{
			self.npc_state = 1;			// Barefoot Berserker Run
			self.npc_phase_end = time + 2.6 + random() * 1.8;
		}
	}

	// Stationary poses hold still until finished
	if (self.npc_state >= 2)
	{
		self.think = RobeGuy_Think;
		self.nextthink = time + 0.05;
		return;
	}

	if (self.npc_radius > 0 && vlen(self.origin - self.npc_home) > self.npc_radius)
		want = vectoyaw(self.npc_home - self.origin) + (random() - 0.5) * 40;
	else
		want = self.angles_y + (random() - 0.5) * 26;

	diff = want - self.angles_y;
	while (diff > 180)
		diff = diff - 360;
	while (diff < -180)
		diff = diff + 360;
	self.angles_y = self.angles_y + diff * 0.28;

	if (!walkmove(self.angles_y, 10.5))
	{
		self.angles_y = self.angles_y + 110 + random() * 90;
		while (self.angles_y >= 360)
			self.angles_y = self.angles_y - 360;
		walkmove(self.angles_y, 8.5);
	}

	self.think = RobeGuy_Think;
	self.nextthink = time + 0.05;
};

void() npc_robeguy =
{
	if (BM_NoMapNPC ())		// no map NPCs unless bm_npcs 1 (2026-11-26)
	{
		remove (self);
		return;
	}
	RobeGuy_Precache();
	self.classname = "npc_robeguy";
	setmodel(self, "progs/robeguy.spr32");
	self.scale = 0.7467;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 145;
	self.max_health = 145;
	self.takedamage = DAMAGE_AIM;
	self.th_stand = RobeGuy_Think;
	self.th_walk = RobeGuy_Think;
	self.th_run = RobeGuy_Think;
	self.th_melee = RobeGuy_Think;
	self.th_missile = RobeGuy_Think;
	self.th_pain = RobeGuy_Pain;
	self.th_die = RobeGuy_Die;
	self.touch = SUB_Null;
	self.customizeentityforclient = RobeGuy_Customize;
	self.npc_state = 1;
	self.npc_phase_end = time + 2.4 + random() * 2.0;
	self.npc_next_stunt = time + 4.5 + random() * 3.0;
	if (self.npc_respawn == 0)
		self.npc_respawn = 25;		// -1 (a summon) = never comes back
	if (self.npc_radius <= 0)
		self.npc_radius = 480;
	// Peaceful ambient RobeGuy: omit FL_MONSTER so joke summons & bots focus on real enemies!
	self.flags = self.flags - (self.flags & FL_MONSTER);
	setsize(self, '-18 -18 0', '18 18 58');
	droptofloor();
	self.npc_home = self.origin;
	self.think = RobeGuy_Think;
	self.nextthink = time + 0.1 + random() * 0.25;
};

void() RobeGuy_Summon =
{
	local vector flat_ang;
	local entity e, oself;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	e = spawn();
	e.origin = self.origin + v_forward * 136 + '0 0 20';
	e.angles_y = self.v_angle_y + 180;
	e.npc_respawn = -1;		// a summon does not respawn (0 would be read as the default 25 s)
	oself = self;
	self = e;
	npc_robeguy();
	self = oself;
	if (!NPC_IsVoiceMuted(e))
		sound(e, CHAN_VOICE, "robeguy/idle_honk_growl.wav", 1, ATTN_NORM);
};
