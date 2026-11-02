/*
random_npcs.qc — 4 Photorealistic + Comedic 3D Humanoid Roaming NPCs (Player-Sized MD3s):
  1) npc_random_guy    (progs/npc_randguy.md3   — 6 random comedy shirts _0.._5 + 64oz Mega Gulp)
  2) npc_afro_guy      (progs/npc_afroguy.md3   — Giant 70s Afro, Gold Pick, Funk Polo & Boombox)
  3) npc_random_lady   (progs/npc_randlady.md3  — High Bun, 3 tops _0.._2, Quilted Purse & Phone)
  4) npc_fat_guy       (progs/npc_fatguy.md3    — Really Big Fat Guy, Stained Tee, Bare Belly & XXL Burrito)
  5) npc_random_person (spawns one of the 4 randomly)

All 4 use the exact Quake player hull ('-16 -16 -24' to '16 16 32', ~54u standing height),
roam peacefully (walk, run, idle, signature funny emotes), startle & sprint away from gunfire,
and can be shot/gibbed.

Cheat test impulses (with sv_cheats 1):
  impulse 51  Summon Random Guy (cycles/randomizes comedy shirts)
  impulse 52  Summon Black Guy with Afro
  impulse 53  Summon Random Lady (cycles/randomizes tops)
  impulse 54  Summon Really Big Fat Guy
  impulse 55  Summon all 4 side-by-side in front of the player

Inspection cvars:
  rnpc_mode   0 = AI (default), 1 = force Walk, 2 = force Run, 3 = force Funny, 4 = force Idle
  rnpc_stay   0 = normal movement (default), 1 = animate in-place (for lineup inspection)
*/

.float	rnpc_kind;
.float	rnpc_anim_i;
float	rnpc_shirt_seq;
float	rnpc_lady_seq;

float	RNPC_RANDGUY	= 1;
float	RNPC_AFROGUY	= 2;
float	RNPC_LADY		= 3;
float	RNPC_FATGUY		= 4;

// 50-frame shared MD3 animation layout:
//   0..7   (8f)  Idle
//   8..19  (12f) Walk
//   20..29 (10f) Run / Panic Sprint
//   30..39 (10f) Signature Funny Emote
//   40..43 (4f)  Pain Flinch
//   44..49 (6f)  Comedic Collapse Death

void() RandomNPC_Think;
void() RandomNPC_Die;
void(entity attacker, float take) RandomNPC_Pain;

void() RandomNPCs_Precache =
{
	if (random_npcs_precached)
		return;
	random_npcs_precached = TRUE;

	precache_model("progs/npc_randguy.md3");
	precache_model("progs/npc_afroguy.md3");
	precache_model("progs/npc_randlady.md3");
	precache_model("progs/npc_fatguy.md3");

	precache_model("progs/gib1.mdl");
	precache_model("progs/gib2.mdl");
	precache_model("progs/gib3.mdl");
	precache_sound("player/udeath.wav");

	precache_sound("random_npcs/randguy_idle.wav");
	precache_sound("random_npcs/randguy_funny.wav");
	precache_sound("random_npcs/randguy_panic.wav");

	precache_sound("random_npcs/afroguy_idle.wav");
	precache_sound("random_npcs/afroguy_funny.wav");
	precache_sound("random_npcs/afroguy_panic.wav");

	precache_sound("random_npcs/lady_idle.wav");
	precache_sound("random_npcs/lady_funny.wav");
	precache_sound("random_npcs/lady_panic.wav");

	precache_sound("random_npcs/fatguy_idle.wav");
	precache_sound("random_npcs/fatguy_funny.wav");
	precache_sound("random_npcs/fatguy_panic.wav");
};

void(entity e, float slot) RandomNPC_PlayVoice =
{
	local float k;
	local string snd;

	k = e.rnpc_kind;
	snd = "random_npcs/randguy_idle.wav";
	if (k == RNPC_RANDGUY)
	{
		if (slot == 1)
			snd = "random_npcs/randguy_funny.wav";
		else if (slot == 2)
			snd = "random_npcs/randguy_panic.wav";
		else
			snd = "random_npcs/randguy_idle.wav";
	}
	else if (k == RNPC_AFROGUY)
	{
		if (slot == 1)
			snd = "random_npcs/afroguy_funny.wav";
		else if (slot == 2)
			snd = "random_npcs/afroguy_panic.wav";
		else
			snd = "random_npcs/afroguy_idle.wav";
	}
	else if (k == RNPC_LADY)
	{
		if (slot == 1)
			snd = "random_npcs/lady_funny.wav";
		else if (slot == 2)
			snd = "random_npcs/lady_panic.wav";
		else
			snd = "random_npcs/lady_idle.wav";
	}
	else
	{
		if (slot == 1)
			snd = "random_npcs/fatguy_funny.wav";
		else if (slot == 2)
			snd = "random_npcs/fatguy_panic.wav";
		else
			snd = "random_npcs/fatguy_idle.wav";
	}
	sound(e, CHAN_VOICE, snd, 0.92, ATTN_NORM);
};

void(entity e) RandomNPC_AssignSkinAndModel =
{
	local float sk;

	if (e.rnpc_kind == RNPC_AFROGUY)
	{
		setmodel(e, "progs/npc_afroguy.md3");
		e.skin = 0;
	}
	else if (e.rnpc_kind == RNPC_LADY)
	{
		setmodel(e, "progs/npc_randlady.md3");
		if (e.cnt >= 1 && e.cnt <= 3)
			sk = e.cnt - 1;
		else
		{
			sk = floor(random() * 3);
			if (sk > 2)
				sk = 2;
		}
		e.skin = sk;
	}
	else if (e.rnpc_kind == RNPC_FATGUY)
	{
		setmodel(e, "progs/npc_fatguy.md3");
		e.skin = 0;
	}
	else
	{
		e.rnpc_kind = RNPC_RANDGUY;
		setmodel(e, "progs/npc_randguy.md3");
		if (e.cnt >= 1 && e.cnt <= 6)
			sk = e.cnt - 1;
		else
		{
			sk = floor(random() * 6);
			if (sk > 5)
				sk = 5;
		}
		e.skin = sk;
	}
};

void() RandomNPC_Respawn =
{
	setorigin(self, self.npc_home + '0 0 8');
	RandomNPC_AssignSkinAndModel(self);
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if (self.rnpc_kind == RNPC_FATGUY)
		self.health = 165;
	else
		self.health = 115;
	self.max_health = self.health;
	self.takedamage = DAMAGE_AIM;
	self.effects = 0;
	self.alpha = 1;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	self.npc_state = 1;
	self.rnpc_anim_i = floor(random() * 12);
	self.frame = 8 + self.rnpc_anim_i;
	self.npc_phase_end = time + 2.5 + random() * 2.5;
	self.npc_next_stunt = time + 5.0 + random() * 4.0;
	if (self.target != "")
		self.goalentity = find(world, targetname, self.target);
	setsize(self, '-16 -16 -24', '16 16 32');
	droptofloor();
	self.think = RandomNPC_Think;
	self.nextthink = time + 0.08;
};

void() RandomNPC_CorpseCleanup =
{
	if (self.npc_respawn > 0)
	{
		setmodel(self, "");
		self.think = RandomNPC_Respawn;
		self.nextthink = time + self.npc_respawn;
		return;
	}
	remove(self);
};

void() RandomNPC_DeathStep =
{
	self.npc_dstep = self.npc_dstep + 1;
	if (self.npc_dstep <= 5)
	{
		self.frame = 44 + self.npc_dstep;
		self.think = RandomNPC_DeathStep;
		self.nextthink = time + 0.08;
		return;
	}
	self.frame = 49;
	self.think = RandomNPC_CorpseCleanup;
	self.nextthink = time + 4.0;
};

void() RandomNPC_Die =
{
	if (self.npc_dead)
		return;
	self.npc_dead = TRUE;
	self.npc_dstep = 0;
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.movetype = MOVETYPE_NONE;

	// Heavy overkill (rockets / close SSG) splatters classic Quake gibs!
	if (self.health < -35)
	{
		sound(self, CHAN_VOICE, "player/udeath.wav", 1, ATTN_NORM);
		ThrowGib("progs/gib1.mdl", self.health);
		ThrowGib("progs/gib2.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		if (self.npc_respawn > 0)
		{
			setmodel(self, "");
			self.think = RandomNPC_Respawn;
			self.nextthink = time + self.npc_respawn;
			return;
		}
		remove(self);
		return;
	}

	RandomNPC_PlayVoice(self, 2);
	self.frame = 44;
	self.think = RandomNPC_DeathStep;
	self.nextthink = time + 0.08;
};

void(entity attacker, float take) RandomNPC_Pain =
{
	if (self.health <= 0 || self.npc_dead)
		return;

	// Turn away from whoever shot us, yelp in panic, play quick 4-frame flinch, then SPRINT!
	if (attacker != world && attacker != self)
		self.angles_y = vectoyaw(self.origin - attacker.origin) + (random() - 0.5) * 35;

	if (time > self.npc_next_voice)
	{
		RandomNPC_PlayVoice(self, 2);
		self.npc_next_voice = time + 1.4;
	}

	self.npc_state = 4;
	self.rnpc_anim_i = 0;
	self.frame = 40;
	self.npc_phase_end = time + 0.30;
};

entity(entity npc, float max_d) RandomNPC_FindGunfirePlayer =
{
	local entity p;
	local float d;

	p = bm_player_head;
	while (p)
	{
		if (p.health > 0 && p.attack_finished > time)
		{
			d = vlen(p.origin - npc.origin);
			if (d < max_d)
				return p;
		}
		p = p.bm_player_next;
	}
	return world;
};

entity(entity npc, float max_d) RandomNPC_FindNearPlayer =
{
	local entity p, best;
	local float d, best_d;

	best = world;
	best_d = max_d;
	p = bm_player_head;
	while (p)
	{
		if (p.health > 0)
		{
			d = vlen(p.origin - npc.origin);
			if (d < best_d)
			{
				best_d = d;
				best = p;
			}
		}
		p = p.bm_player_next;
	}
	return best;
};

void() RandomNPC_Think =
{
	local float forced, st, step_dist, dt, want, diff, roll_r;
	local entity shooter, near_p;
	local vector flat_d;

	if (self.health <= 0)
	{
		RandomNPC_Die();
		return;
	}

	if (self.target != "" && self.goalentity == world)
		self.goalentity = find(world, targetname, self.target);

	forced = bm_cvar_rnpc_mode;
	if (forced >= 1 && forced <= 4)
	{
		if (forced == 1)
			self.npc_state = 1;		// Walk
		else if (forced == 2)
			self.npc_state = 2;		// Run
		else if (forced == 3)
			self.npc_state = 3;		// Funny emote
		else
			self.npc_state = 0;		// Idle
	}
	else
	{
		// Startle into comedic panic sprint when nearby gunfire erupts!
		if (self.npc_state != 2 && self.npc_state != 4)
		{
			shooter = RandomNPC_FindGunfirePlayer(self, 440);
			if (shooter != world)
			{
				self.npc_state = 2;
				self.rnpc_anim_i = 0;
				self.npc_phase_end = time + 2.4 + random() * 1.4;
				self.angles_y = vectoyaw(self.origin - shooter.origin) + (random() - 0.5) * 40;
				if (time > self.npc_next_voice)
				{
					RandomNPC_PlayVoice(self, 2);
					self.npc_next_voice = time + 2.2;
				}
			}
		}

		// State transitions when current phase finishes
		if (time >= self.npc_phase_end)
		{
			if (self.npc_state == 4)
			{
				// After pain flinch -> bolt into panicked sprint!
				self.npc_state = 2;
				self.rnpc_anim_i = 0;
				self.npc_phase_end = time + 2.6 + random() * 1.2;
			}
			else if (time >= self.npc_next_stunt)
			{
				roll_r = random();
				if (roll_r < 0.52)
				{
					// Signature funny emote! Face nearby player if one is watching
					self.npc_state = 3;
					self.rnpc_anim_i = 0;
					self.npc_phase_end = time + 0.95;
					near_p = RandomNPC_FindNearPlayer(self, 360);
					if (near_p != world)
						self.angles_y = vectoyaw(near_p.origin - self.origin);
					if (time > self.npc_next_voice)
					{
						RandomNPC_PlayVoice(self, 1);
						self.npc_next_voice = time + 2.5;
					}
				}
				else if (roll_r < 0.80)
				{
					// Spontaneous comedic hustle / jog!
					self.npc_state = 2;
					self.rnpc_anim_i = 0;
					self.npc_phase_end = time + 1.9 + random() * 1.4;
				}
				else
				{
					// Casual neighborhood pause & look-around
					self.npc_state = 0;
					self.rnpc_anim_i = 0;
					self.npc_phase_end = time + 1.4 + random() * 1.2;
					if (time > self.npc_next_voice)
					{
						RandomNPC_PlayVoice(self, 0);
						self.npc_next_voice = time + 3.5 + random() * 2.5;
					}
				}
				self.npc_next_stunt = time + 4.8 + random() * 3.8;
			}
			else
			{
				// Default: stroll down the street!
				self.npc_state = 1;
				self.rnpc_anim_i = 0;
				self.npc_phase_end = time + 3.0 + random() * 2.5;
				if (time > self.npc_next_voice && random() < 0.35)
				{
					RandomNPC_PlayVoice(self, 0);
					self.npc_next_voice = time + 4.5 + random() * 3.0;
				}
			}
		}
	}

	// Advance MD3 animation frame for current state
	st = self.npc_state;
	dt = 0.09;
	step_dist = 0;

	if (st == 0)
	{
		// Idle: 0..7
		self.rnpc_anim_i = self.rnpc_anim_i + 1;
		if (self.rnpc_anim_i >= 8)
			self.rnpc_anim_i = 0;
		self.frame = self.rnpc_anim_i;
		dt = 0.10;
	}
	else if (st == 1)
	{
		// Walk: 8..19
		self.rnpc_anim_i = self.rnpc_anim_i + 1;
		if (self.rnpc_anim_i >= 12)
			self.rnpc_anim_i = 0;
		self.frame = 8 + self.rnpc_anim_i;
		dt = 0.085;
		if (self.rnpc_kind == RNPC_FATGUY)
			step_dist = 5.5;
		else
			step_dist = 7.2;
	}
	else if (st == 2)
	{
		// Run / Panic Sprint: 20..29
		self.rnpc_anim_i = self.rnpc_anim_i + 1;
		if (self.rnpc_anim_i >= 10)
			self.rnpc_anim_i = 0;
		self.frame = 20 + self.rnpc_anim_i;
		dt = 0.068;
		if (self.rnpc_kind == RNPC_FATGUY)
			step_dist = 10.5;
		else
			step_dist = 13.8;
	}
	else if (st == 3)
	{
		// Signature Funny Emote: 30..39
		self.rnpc_anim_i = self.rnpc_anim_i + 1;
		if (self.rnpc_anim_i >= 10)
			self.rnpc_anim_i = 0;
		self.frame = 30 + self.rnpc_anim_i;
		dt = 0.095;
	}
	else
	{
		// Pain Flinch: 40..43
		if (self.rnpc_anim_i < 3)
			self.rnpc_anim_i = self.rnpc_anim_i + 1;
		self.frame = 40 + self.rnpc_anim_i;
		dt = 0.075;
	}

	// Roaming steering + walkmove (skipped when stationary or rnpc_stay == 1)
	if (step_dist > 0 && !bm_cvar_rnpc_stay)
	{
		if (self.goalentity != world)
		{
			flat_d = self.goalentity.origin - self.origin;
			flat_d_z = 0;
			if (vlen(flat_d) < 56 && self.goalentity.target != "")
				self.goalentity = find(world, targetname, self.goalentity.target);
			want = vectoyaw(flat_d);
		}
		else if (self.npc_radius > 0 && vlen(self.origin - self.npc_home) > self.npc_radius)
			want = vectoyaw(self.npc_home - self.origin) + (random() - 0.5) * 36;
		else
			want = self.angles_y + (random() - 0.5) * 22;

		diff = want - self.angles_y;
		while (diff > 180)
			diff = diff - 360;
		while (diff < -180)
			diff = diff + 360;
		self.angles_y = self.angles_y + diff * 0.30;

		if (!walkmove(self.angles_y, step_dist))
		{
			// Smoothly steer around walls, curbs, or furniture
			if (!walkmove(self.angles_y + 45, step_dist * 0.8))
			{
				if (!walkmove(self.angles_y - 45, step_dist * 0.8))
				{
					self.angles_y = self.angles_y + 115 + random() * 90;
					while (self.angles_y >= 360)
						self.angles_y = self.angles_y - 360;
					walkmove(self.angles_y, step_dist * 0.7);
				}
				else
					self.angles_y = self.angles_y - 35;
			}
			else
				self.angles_y = self.angles_y + 35;
		}
	}

	self.think = RandomNPC_Think;
	self.nextthink = time + dt;
};

void(float kind) RandomNPC_InitCommon =
{
	RandomNPCs_Precache();
	self.rnpc_kind = kind;
	RandomNPC_AssignSkinAndModel(self);
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if (kind == RNPC_FATGUY)
		self.health = 165;
	else
		self.health = 115;
	self.max_health = self.health;
	self.takedamage = DAMAGE_AIM;
	self.th_stand = RandomNPC_Think;
	self.th_walk = RandomNPC_Think;
	self.th_run = RandomNPC_Think;
	self.th_melee = RandomNPC_Think;
	self.th_missile = RandomNPC_Think;
	self.th_pain = RandomNPC_Pain;
	self.th_die = RandomNPC_Die;
	self.touch = SUB_Null;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	self.npc_state = 1;
	self.rnpc_anim_i = floor(random() * 12);
	self.frame = 8 + self.rnpc_anim_i;
	self.npc_phase_end = time + 2.2 + random() * 2.4;
	self.npc_next_stunt = time + 3.8 + random() * 3.5;
	if (self.npc_respawn == 0)
		self.npc_respawn = 25;
	if (self.npc_radius <= 0)
		self.npc_radius = 460;
	self.flags = FL_MONSTER;
	// Exact Quake player bounding box ('-16 -16 -24' to '16 16 32')!
	setsize(self, '-16 -16 -24', '16 16 32');
	droptofloor();
	self.npc_home = self.origin;
	self.think = RandomNPC_Think;
	self.nextthink = time + 0.08 + random() * 0.15;
};

void() npc_random_guy =
{
	self.classname = "npc_random_guy";
	RandomNPC_InitCommon(RNPC_RANDGUY);
};

void() npc_afro_guy =
{
	self.classname = "npc_afro_guy";
	RandomNPC_InitCommon(RNPC_AFROGUY);
};

void() npc_random_lady =
{
	self.classname = "npc_random_lady";
	RandomNPC_InitCommon(RNPC_LADY);
};

void() npc_fat_guy =
{
	self.classname = "npc_fat_guy";
	RandomNPC_InitCommon(RNPC_FATGUY);
};

void() npc_random_person =
{
	local float r;

	r = random();
	if (r < 0.25)
		npc_random_guy();
	else if (r < 0.50)
		npc_afro_guy();
	else if (r < 0.75)
		npc_random_lady();
	else
		npc_fat_guy();
};

entity(float kind, vector spawn_org, float yaw) RandomNPC_SpawnOneAt =
{
	local entity e, oself;

	e = spawn();
	e.origin = spawn_org;
	e.angles = '0 0 0';
	e.angles_y = yaw;
	e.npc_respawn = -1;		// Summoned test NPCs clean up after dying

	// Cycle shirts on summon so repeated summons immediately show off every shirt variant!
	if (kind == RNPC_RANDGUY)
	{
		e.cnt = 1 + (rnpc_shirt_seq - 6 * floor(rnpc_shirt_seq / 6));
		rnpc_shirt_seq = rnpc_shirt_seq + 1;
	}
	else if (kind == RNPC_LADY)
	{
		e.cnt = 1 + (rnpc_lady_seq - 3 * floor(rnpc_lady_seq / 3));
		rnpc_lady_seq = rnpc_lady_seq + 1;
	}

	oself = self;
	self = e;
	if (kind == RNPC_AFROGUY)
		npc_afro_guy();
	else if (kind == RNPC_LADY)
		npc_random_lady();
	else if (kind == RNPC_FATGUY)
		npc_fat_guy();
	else
		npc_random_guy();
	self = oself;
	return e;
};

void(float kind) RandomNPC_Summon =
{
	local vector flat_ang, pos;
	local entity e;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	pos = self.origin + v_forward * 124 + '0 0 18';
	e = RandomNPC_SpawnOneAt(kind, pos, self.v_angle_y + 180);
	RandomNPC_PlayVoice(e, 1);
};

void() RandomNPC_SummonAll4 =
{
	local vector flat_ang, base_p;
	local entity e1, e2, e3, e4;
	local float face_yaw;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	base_p = self.origin + v_forward * 148 + '0 0 18';
	face_yaw = self.v_angle_y + 180;

	e1 = RandomNPC_SpawnOneAt(RNPC_RANDGUY, base_p - v_right * 66, face_yaw);
	e2 = RandomNPC_SpawnOneAt(RNPC_AFROGUY, base_p - v_right * 22, face_yaw);
	e3 = RandomNPC_SpawnOneAt(RNPC_LADY,    base_p + v_right * 22, face_yaw);
	e4 = RandomNPC_SpawnOneAt(RNPC_FATGUY,  base_p + v_right * 68, face_yaw);
	RandomNPC_PlayVoice(e2, 1);
};
