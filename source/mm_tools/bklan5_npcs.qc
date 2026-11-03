/*
bklan5_npcs.qc — Harmless, Shootable Roaming NPCs for bklan5:
  1) npc_greensuit_wheelman  (progs/greensuit_wheelman.spr32 — 256 frames, 8-dir 360° two-wheel contraption driver)
  2) npc_robeguy             (progs/robeguy.spr32 — 336 frames, 8-dir 360° "The Flamingo Fiend")

Both NPCs roam peacefully around Bakersfield streets/plazas (following bk_route if "target" is set, or cruising
around their spawn neighborhood), deal ZERO damage to players, and can be shot and killed with full custom
multi-frame gib explosions (respawning 25s later so the streets stay lively).

Cheat test impulses (with sv_cheats 1):
  impulse 46  Summon Green-Suit Wheelman in front of you
  impulse 47  Summon The Flamingo Fiend (robeguy) in front of you
*/

.float	npc_state;
.float	npc_phase_end;
.float	npc_next_stunt;
.float	npc_next_voice;
.float	npc_respawn;
.float	npc_radius;
.vector	npc_home;

void() GreenSuit_Think;
void() GreenSuit_Die;
void(entity attacker, float take) GreenSuit_Pain;
void() RobeGuy_Think;
void() RobeGuy_Die;
void(entity attacker, float take) RobeGuy_Pain;

// ================================================================================================
// 1. GREEN-SUIT WHEELMAN (progs/greensuit_wheelman.spr32)
//   0..7            8-dir Idle (seated_cruise f0)
//   8 + d*6 + k     8-dir Seated Cruise (k = 0..5)
//   56 + d*6 + k    8-dir Scream Turbo Overdrive (k = 0..5)
//   104 + d*6 + k   8-dir Hero Crane Point (k = 0..5)
//   152 + d*6 + k   8-dir Ab-Roller Plank Rollout (k = 0..5)
//   200 + d*7 + s   8-dir Gib Explosion (s = 0..6)
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
	precache_sound("player/udeath.wav");
	precache_sound("player/pain4.wav");
	precache_sound("vehicles/idle_coupe.wav");
};

float() GreenSuit_Customize =
{
	local float rel, d, k, st, fps, s;
	local vector delta;

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 26');
	rel = vectoyaw(delta) - self.angles_y;
	rel = rel - 360 * floor(rel / 360);
	d = floor(rel / 45 + 0.5);
	if (d >= 8)
		d = 0;

	if (self.npc_dead == 2)
	{
		s = self.npc_dstep;
		if (s < 0)
			s = 0;
		if (s > 6)
			s = 6;
		self.frame = 200 + d * 7 + s;
		return TRUE;
	}
	if (self.npc_dead == 1)
	{
		s = self.npc_dstep;
		if (s < 0)
			s = 0;
		if (s > 5)
			s = 5;
		self.frame = 256 + d * 6 + s;
		return TRUE;
	}

	st = self.npc_state;
	if (st <= 0)
	{
		self.frame = d;
		return TRUE;
	}

	fps = 14;
	if (st == 2)
		fps = 18;
	else if (st == 3)
		fps = 11;

	k = floor(time * fps + self.origin_x * 0.02 + self.origin_y * 0.02);
	k = k - 6 * floor(k / 6);

	if (st == 1)
		self.frame = 8 + d * 6 + k;
	else if (st == 2)
		self.frame = 56 + d * 6 + k;
	else if (st == 3)
		self.frame = 104 + d * 6 + k;
	else
		self.frame = 152 + d * 6 + k;

	return TRUE;
};

void() GreenSuit_Respawn =
{
	setorigin(self, self.npc_home + '0 0 12');
	setmodel(self, "progs/greensuit_wheelman.spr32");
	self.scale = 0.36;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 135;
	self.max_health = 135;
	self.takedamage = DAMAGE_AIM;
	self.effects = 0;
	self.alpha = 1;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	self.npc_state = 1;
	self.npc_phase_end = time + 3.0;
	self.npc_next_stunt = time + 5.5;
	if (self.target != "")
		self.goalentity = find(world, targetname, self.target);
	setsize(self, '-18 -18 0', '18 18 54');
	droptofloor();
	self.think = GreenSuit_Think;
	self.nextthink = time + 0.05;
};

void() GreenSuit_DeathStep =
{
	self.npc_dstep = self.npc_dstep + 1;
	if (self.npc_dead == 2)
	{
		if (self.npc_dstep <= 6)
		{
			self.think = GreenSuit_DeathStep;
			self.nextthink = time + 0.07;
			return;
		}
		self.effects = 0;
		if (self.npc_respawn > 0)
		{
			setmodel(self, "");
			self.think = GreenSuit_Respawn;
			self.nextthink = time + self.npc_respawn;
			return;
		}
		remove(self);
		return;
	}
	if (self.npc_dstep <= 5)
	{
		self.think = GreenSuit_DeathStep;
		self.nextthink = time + 0.075;
		return;
	}
	if (self.npc_dstep == 6)
	{
		self.think = GreenSuit_DeathStep;
		self.nextthink = time + 2.2;
		return;
	}
	if (self.npc_dstep <= 13)
	{
		self.alpha = 1.0 - (self.npc_dstep - 6) * 0.13;
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
	self.npc_dstep = 0;
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';

	if (NPC_ShouldGib(self))
	{
		self.npc_dead = 2;
		self.effects = EF_DIMLIGHT;
		sound(self, CHAN_VOICE, "player/udeath.wav", 1, ATTN_NORM);
		sound(self, CHAN_AUTO, "weapons/r_exp3.wav", 1, ATTN_NORM);
		ThrowGib("progs/gib1.mdl", -75);
		ThrowGib("progs/gib2.mdl", -85);
		ThrowGib("progs/gib3.mdl", -95);
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte(MSG_BROADCAST, TE_EXPLOSION);
		WriteCoord(MSG_BROADCAST, self.origin_x);
		WriteCoord(MSG_BROADCAST, self.origin_y);
		WriteCoord(MSG_BROADCAST, self.origin_z + 24);
		self.think = GreenSuit_DeathStep;
		self.nextthink = time + 0.07;
		return;
	}

	self.npc_dead = 1;
	self.effects = 0;
	self.alpha = 1;
	sound(self, CHAN_VOICE, "player/pain4.wav", 1, ATTN_NORM);
	self.think = GreenSuit_DeathStep;
	self.nextthink = time + 0.075;
};

void(entity attacker, float take) GreenSuit_Pain =
{
	if (self.health <= 0 || self.npc_dead)
		return;
	// Getting shot makes the harmless Wheelman hit Scream Turbo overdrive to zoom away!
	self.npc_state = 2;
	self.effects = EF_DIMLIGHT;
	self.npc_phase_end = time + 1.8;
	if (time > self.npc_next_voice)
	{
		sound(self, CHAN_AUTO, "weapons/lstart.wav", 0.75, ATTN_NORM);
		self.npc_next_voice = time + 1.2;
	}
};

void() GreenSuit_Think =
{
	local float want, diff, step_dist, roll_r;
	local vector flat_d;

	if (self.health <= 0)
	{
		GreenSuit_Die();
		return;
	}

	if (self.target != "" && self.goalentity == world)
		self.goalentity = find(world, targetname, self.target);

	// Cycle playful harmless stunts while driving around
	if (time >= self.npc_phase_end)
	{
		self.effects = 0;
		if (time >= self.npc_next_stunt)
		{
			roll_r = random();
			if (roll_r < 0.36)
			{
				self.npc_state = 2;		// Scream Turbo Overdrive!
				self.effects = EF_DIMLIGHT;
				self.npc_phase_end = time + 2.0;
			}
			else if (roll_r < 0.68)
			{
				self.npc_state = 4;		// Ab-Roller Plank Rollout!
				self.npc_phase_end = time + 1.8;
			}
			else
			{
				self.npc_state = 3;		// Brief Hero Crane Sky-Point pose!
				self.npc_phase_end = time + 1.25;
			}
			self.npc_next_stunt = time + 6.0 + random() * 4.0;
		}
		else
		{
			self.npc_state = 1;			// Classic Seated Wheel-Cruise!
			self.npc_phase_end = time + 2.8 + random() * 2.0;
		}
	}

	// Subtle rolling hum when a player is close
	if (time > self.npc_next_voice)
	{
		sound(self, CHAN_BODY, "vehicles/idle_coupe.wav", 0.28, 2.2);
		self.npc_next_voice = time + 3.5 + random() * 1.5;
	}

	// Stationary Crane Kick pose holds position briefly before rolling on
	if (self.npc_state == 3)
	{
		self.think = GreenSuit_Think;
		self.nextthink = time + 0.05;
		return;
	}

	if (self.goalentity != world)
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

	diff = want - self.angles_y;
	while (diff > 180)
		diff = diff - 360;
	while (diff < -180)
		diff = diff + 360;
	self.angles_y = self.angles_y + diff * 0.28;

	step_dist = 12.0;		// Smooth ~240 u/s wheel-cruise
	if (self.npc_state == 2)
		step_dist = 16.0;	// ~320 u/s Scream Turbo!
	else if (self.npc_state == 4)
		step_dist = 13.5;

	if (!walkmove(self.angles_y, step_dist))
	{
		// Steer cleanly around parked cars, curbs, or players without harming anyone
		if (!walkmove(self.angles_y + 42, step_dist * 0.85))
		{
			if (!walkmove(self.angles_y - 42, step_dist * 0.85))
			{
				self.angles_y = self.angles_y + 125 + random() * 70;
				while (self.angles_y >= 360)
					self.angles_y = self.angles_y - 360;
				walkmove(self.angles_y, step_dist * 0.75);
			}
			else
				self.angles_y = self.angles_y - 35;
		}
		else
			self.angles_y = self.angles_y + 35;
	}

	self.think = GreenSuit_Think;
	self.nextthink = time + 0.05;
};

void() npc_greensuit_wheelman =
{
	GreenSuit_Precache();
	self.classname = "npc_greensuit_wheelman";
	setmodel(self, "progs/greensuit_wheelman.spr32");
	self.scale = 0.36;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 135;
	self.max_health = 135;
	self.takedamage = DAMAGE_AIM;
	self.th_stand = GreenSuit_Think;
	self.th_walk = GreenSuit_Think;
	self.th_run = GreenSuit_Think;
	self.th_melee = GreenSuit_Think;
	self.th_missile = GreenSuit_Think;
	self.th_pain = GreenSuit_Pain;
	self.th_die = GreenSuit_Die;
	self.touch = SUB_Null;
	self.customizeentityforclient = GreenSuit_Customize;
	self.npc_state = 1;
	self.npc_phase_end = time + 3.0 + random() * 2.0;
	self.npc_next_stunt = time + 5.0 + random() * 3.0;
	self.npc_next_voice = time + 1.0 + random() * 2.0;
	if (self.npc_respawn <= 0)
		self.npc_respawn = 25;
	if (self.npc_radius <= 0)
		self.npc_radius = 680;
	self.flags = FL_MONSTER;
	setsize(self, '-18 -18 0', '18 18 54');
	droptofloor();
	self.npc_home = self.origin;
	self.think = GreenSuit_Think;
	self.nextthink = time + 0.1 + random() * 0.25;
};

void() GreenSuit_Summon =
{
	local vector flat_ang;
	local entity e, oself;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	e = spawn();
	e.origin = self.origin + v_forward * 136 + '0 0 20';
	e.angles_y = self.v_angle_y + 180;
	e.npc_respawn = 0;
	oself = self;
	self = e;
	npc_greensuit_wheelman();
	self = oself;
};


// ================================================================================================
// 2. THE FLAMINGO FIEND (`robeguy`, progs/robeguy.spr32)
//   0..7             8-dir Standing Idle keyposes
//   8 + d*6 + k      8-dir Barefoot Berserker Charge Run (k = 0..5)
//   56 + d*8 + k     8-dir Animated Unhinged Flamingo Whisperer Idle (k = 0..7)
//   120 + d*12 + k   8-dir Heart-Boxers Chest-Hair Laser comedic flash (k = 0..11, 0 damage!)
//   216 + d*12 + k   8-dir Dual Lawn-Flamingo & Hot-Coffee pose (k = 0..11, 0 damage!)
//   312..335         24-frame 4-Act Flamingo Feather & Gib Explosion!
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
		s = self.npc_dstep;
		if (s < 0)
			s = 0;
		if (s > 23)
			s = 23;
		self.frame = 312 + s;
		return TRUE;
	}
	if (self.npc_dead == 1)
	{
		s = self.npc_dstep;
		if (s < 0)
			s = 0;
		if (s > 5)
			s = 5;
		self.frame = 336 + d * 6 + s;
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
		// 8-frame Animated Flamingo Whisperer Idle
		k = floor(time * 10 + self.origin_y * 0.02);
		k = k - 8 * floor(k / 8);
		self.frame = 56 + d * 8 + k;
		return TRUE;
	}
	if (st == 3)
	{
		// 12-frame Heart-Boxers Chest-Hair Laser comedic flash
		k = floor(time * 12);
		k = k - 12 * floor(k / 12);
		self.frame = 120 + d * 12 + k;
		return TRUE;
	}
	// st == 4: 12-frame Dual Lawn-Flamingo & Hot-Coffee wave
	k = floor(time * 12);
	k = k - 12 * floor(k / 12);
	self.frame = 216 + d * 12 + k;
	return TRUE;
};

void() RobeGuy_Respawn =
{
	setorigin(self, self.npc_home + '0 0 12');
	setmodel(self, "progs/robeguy.spr32");
	self.scale = 0.28;
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
		sound(self, CHAN_VOICE, "robeguy/feather_gib_boom.wav", 1, ATTN_NORM);
		sound(self, CHAN_AUTO, "player/udeath.wav", 0.85, ATTN_NORM);
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
	if (time > self.npc_next_voice)
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
				sound(self, CHAN_VOICE, "robeguy/idle_honk_growl.wav", 0.55, 1.8);
			}
			else if (r < 0.68)
			{
				self.npc_state = 3;		// Comedic Heart-Boxers Chest-Hair Laser pose (0 dmg!)
				self.effects = 128;		// EF_RED warm magenta-red glow
				self.npc_phase_end = time + 1.05;
				sound(self, CHAN_VOICE, "robeguy/chest_laser_flash.wav", 0.55, 1.8);
			}
			else
			{
				self.npc_state = 4;		// Dual Lawn-Flamingo & Coffee wave (0 dmg!)
				self.npc_phase_end = time + 1.1;
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
	RobeGuy_Precache();
	self.classname = "npc_robeguy";
	setmodel(self, "progs/robeguy.spr32");
	self.scale = 0.28;
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
	if (self.npc_respawn <= 0)
		self.npc_respawn = 25;
	if (self.npc_radius <= 0)
		self.npc_radius = 480;
	self.flags = FL_MONSTER;
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
	e.npc_respawn = 0;
	oself = self;
	self = e;
	npc_robeguy();
	self = oself;
	sound(e, CHAN_VOICE, "robeguy/idle_honk_growl.wav", 1, ATTN_NORM);
};
