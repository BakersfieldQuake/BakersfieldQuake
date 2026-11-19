#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
PATTAYA BEACH UNCLES (maps/soi6.bsp)

Chubby shirtless Indian uncle NPC (`npc_beach_uncle`) wearing tricolor shorts:
  - Roams Pattaya Beach sand (X = -920..-440 u, Y = -1400..+1800 u)
  - Periodically walks East over the Promenade & Beach Road onto Soi 6
    (X = +240..+3600 u), then cycles back out to the beach
  - Continuous swarming black flies (`beach_uncle_flies`) buzzing around him
  - Bar girls (`npc_soi6`) nearby scream & run away when he approaches Soi 6
  - Zero red blood: hits spurt brown mud (`mud_hit`), death pops him into a
    mud explosion (`mud_boom` + 2D mud burst + 12 flying 3D `mud_glob.md3` chunks)
  - Cheat test impulses (sv_cheats 1):
      impulse 71 -> BeachUncle_Summon ()    (summon a Beach Uncle in front of you)
      impulse 72 -> BeachUncle_GotoBeach () (teleport to Pattaya Beach)
      impulse 73 -> BeachUncle_Poke (100)   (shoot/explode aimed Beach Uncle into mud)
      impulse 74 -> BeachUncle_SendToSoi6 () (redirect nearest uncle straight to Soi 6)
================
*/

float BU_WALK_BEACH = 0;
float BU_TO_SOI6    = 1;
float BU_WALK_SOI6  = 2;
float BU_TO_BEACH   = 3;
float BU_CHEER      = 4;
float BU_DEAD       = 5;
float BU_GIB        = 6;

float BEACH_UNCLE_HP    = 20;
float BEACH_UNCLE_COUNT = 10;

.float bu_slot;
.float bu_phase;       // pre-die mode remembered when cheering
.float bu_wp_stage;    // 0 = toward beach edge (-430,0), 1 = across road (+260,0)
.float bu_dir_x;       // +1 East down Soi 6, -1 West toward Beach
.float bu_steer_t;
.float bu_scare_t;
.float bu_stuck;
.float bu_home_y;
.vector bu_goal;

float bu_precached;
float bu_spawned;

void() BeachUncle_Respawn;
void() BeachUncle_Think;
void() BeachUncle_Touch;

string(float idx) BeachUncle_YellSound =
{
	if (idx <= 1) return "beach_uncle/yell_1.wav";
	if (idx == 2) return "beach_uncle/yell_2.wav";
	if (idx == 3) return "beach_uncle/yell_3.wav";
	return "beach_uncle/yell_4.wav";
};

void() BeachUncle_PrecacheAssets =
{
	if (bu_precached)
		return;
	bu_precached = TRUE;

	precache_model ("progs/beach_uncle_a.md3");
	precache_model ("progs/beach_uncle_b.md3");
	precache_model ("progs/mud_glob.md3");

	precache_sound ("beach_uncle/yell_1.wav");
	precache_sound ("beach_uncle/yell_2.wav");
	precache_sound ("beach_uncle/yell_3.wav");
	precache_sound ("beach_uncle/yell_4.wav");
	precache_sound ("beach_uncle/mud_hit.wav");
	precache_sound ("beach_uncle/mud_explode.wav");
};

void(entity ent, float st) BeachUncle_SetState =
{
	if (ent.soi6_state == st)
		return;
	ent.soi6_state = st;
	ent.soi6_anim_t = time;
	if (st == BU_DEAD || st == BU_GIB)
	{
		setmodel (ent, "progs/beach_uncle_b.md3");
	}
	else if (ent.model != "progs/beach_uncle_a.md3")
	{
		setmodel (ent, "progs/beach_uncle_a.md3");
		setsize (ent, '-15 -15 0', '15 15 68');
	}
};

float() BeachUncle_Customize =
{
	local vector v;
	local float dx, dy, rel, d, elapsed, f;

	dx = other.origin_x - self.origin_x;
	if (dx > 2200 || dx < -2200)
		return FALSE;
	dy = other.origin_y - self.origin_y;
	if (dy > 2200 || dy < -2200)
		return FALSE;
	if ((dx * dx + dy * dy) > 4840000)
		return FALSE;
	if (other.ishuman != 1)
		return FALSE;

	// Face the viewer's POSITION, in 3 degree steps. Facing his view angle (other.v_angle_y) changed this entity for him on
	// every frame he moved the mouse, so every NPC in range was re-sent to him each frame. Looking straight at the NPC the
	// two are the same angle.
	self.angles_y = floor ((vectoyaw (other.origin - self.origin) + 180) / 3 + 0.5) * 3;
	self.angles_x = 0;
	self.angles_z = 0;

	v = other.origin - self.origin;
	rel = vectoyaw (v) - self.soi6_yaw;
	while (rel < 0)
		rel = rel + 360;
	while (rel >= 360)
		rel = rel - 360;
	d = floor (rel / 45 + 0.5);
	if (d >= 8)
		d = d - 8;

	elapsed = time - self.soi6_anim_t;
	if (elapsed < 0)
		elapsed = 0;

	if (self.soi6_state == BU_DEAD)
	{
		f = floor (elapsed * 14);
		if (f > 5) f = 5;
		self.skin = f * 8 + d;
		return TRUE;
	}
	if (self.soi6_state == BU_GIB)
	{
		f = floor (elapsed * 18);
		if (f > 7) f = 7;
		self.skin = (6 + f) * 8 + d;
		return TRUE;
	}

	if (self.soi6_state == BU_CHEER)
		f = 26 + (floor (elapsed * 12) % 5);
	else
		f = 18 + (floor (elapsed * 15) % 8);

	self.skin = f * 8 + d;
	return TRUE;
};

void() BeachUncle_MudChunkThink =
{
	SUB_Remove ();
};

void(vector org, float count) BeachUncle_SpawnMudChunks =
{
	local float i, ang;
	local entity m;

	for (i = 0; i < count; i = i + 1)
	{
		m = spawn ();
		m.classname = "mud_chunk";
		m.solid = SOLID_NOT;
		m.movetype = MOVETYPE_BOUNCE;
		m.takedamage = DAMAGE_NO;
		m.owner = self;
		m.traileffectnum = particleeffectnum ("mud_trail");

		setmodel (m, "progs/mud_glob.md3");
		setsize (m, '0 0 0', '0 0 0');
		setorigin (m, org + randomvec () * 14 + '0 0 18');

		ang = (i / count) * 360 + random () * 28;
		makevectors ('0 1 0' * ang);
		m.velocity = v_forward * (120 + random () * 240) + '0 0 1' * (150 + random () * 230);
		m.avelocity = randomvec () * 420;
		m.angles_y = random () * 360;
		m.scale = 0.75 + random () * 0.85;

		m.think = BeachUncle_MudChunkThink;
		m.nextthink = time + 4.5 + random () * 2.5;
	}
};

void() BeachUncle_ScareGirls =
{
	local entity e;
	local float scared;

	scared = 0;
	e = findradius (self.origin, 300);
	while (e)
	{
		if (e.classname == "npc_soi6"
			&& e.health > 0
			&& !e.soi6_lineup
			&& e.soi6_state != SOI6_DEAD
			&& e.soi6_state != SOI6_GIB
			&& (!e.soi6_stationary || e.soi6_tier <= 1)
			&& fabs (e.origin_z - self.origin_z) < 96)
		{
			e.soi6_target = self;
			e.soi6_state_t = time + 5.5 + random () * 2.0;
			if (e.soi6_state != SOI6_SCREAM)
			{
				Soi6_SetState (e, SOI6_SCREAM);
				if (scared < 2 && time >= e.soi6_talk_t)
				{
					Soi6_PlayScream (e, CHAN_VOICE, 0.95);
					e.soi6_talk_t = time + 1.4 + random () * 0.8;
					scared = scared + 1;
				}
				e.nextthink = time + 0.05;
			}
		}
		e = e.chain;
	}
};

void(entity attacker, float damage) BeachUncle_Pain =
{
	if (self.health <= 0 || self.soi6_state == BU_DEAD || self.soi6_state == BU_GIB)
		return;

	pointparticles (particleeffectnum ("mud_hit"), self.origin + '0 0 32', '0 0 1' * 40, 1);
	sound (self, CHAN_VOICE, "beach_uncle/mud_hit.wav", 1, ATTN_NORM);
};

void() BeachUncle_Die =
{
	if (self.soi6_state == BU_DEAD || self.soi6_state == BU_GIB)
		return;

	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';

	// Always pop into muddy smithereens when shot dead
	BeachUncle_SetState (self, BU_GIB);
	sound (self, CHAN_VOICE, "beach_uncle/mud_explode.wav", 1, ATTN_NORM);
	pointparticles (particleeffectnum ("mud_boom"), self.origin + '0 0 28', '0 0 0', 1);
	BeachUncle_SpawnMudChunks (self.origin, 12);

	self.soi6_respawn_t = time + 12 + random () * 4;
	self.nextthink = time + 0.45;
};

void() BeachUncle_Touch =
{
	if (!other || other == world)
		return;
	if (self.soi6_state == BU_DEAD || self.soi6_state == BU_GIB)
		return;
	if (other.classname == "player" || other.classname == "npc_beach_uncle" || other.classname == "npc_soi6")
	{
		self.solid = SOLID_CORPSE;
		self.soi6_pass_t = time + 0.45;
	}
};

vector(float slot) BeachUncle_PickBeachSpot =
{
	local vector v;
	local float rx, ry;

	// Avoid ocean surf (X < -940) and Taksin Shrine (-531, -1378)
	rx = -890 + random () * 410;
	if (slot <= 3)
		ry = -500 + random () * 1000;
	else
		ry = -1100 + random () * 2400;

	if (ry < -1180 && ry > -1560 && rx > -660 && rx < -420)
		rx = -780;

	v_x = rx;
	v_y = ry;
	v_z = 24;
	return v;
};

void(entity ent) BeachUncle_PickNewBeachGoal =
{
	ent.bu_goal = BeachUncle_PickBeachSpot (ent.bu_slot);
	ent.bu_steer_t = time + 4.0 + random () * 4.0;
};

float(float yaw, float stepd) BeachUncle_WalkStep =
{
	local float ok, ny;

	self.angles_y = yaw;
	ok = walkmove (yaw, stepd);
	if (ok)
	{
		self.soi6_yaw = yaw;
		self.bu_stuck = 0;
		return TRUE;
	}

	if (walkmove (yaw + 42, stepd * 0.85))
	{
		self.soi6_yaw = yaw + 42;
		self.bu_stuck = 0;
		return TRUE;
	}
	if (walkmove (yaw - 42, stepd * 0.85))
	{
		self.soi6_yaw = yaw - 42;
		self.bu_stuck = 0;
		return TRUE;
	}
	if (walkmove (yaw + 95, stepd * 0.70))
	{
		self.soi6_yaw = yaw + 95;
		self.bu_stuck = 0;
		return TRUE;
	}
	if (walkmove (yaw - 95, stepd * 0.70))
	{
		self.soi6_yaw = yaw - 95;
		self.bu_stuck = 0;
		return TRUE;
	}

	self.bu_stuck = self.bu_stuck + 1;
	ny = yaw + 135;
	if (random () < 0.5)
		ny = yaw - 135;
	self.soi6_yaw = ny;
	walkmove (ny, stepd * 0.6);
	return FALSE;
};

void() BeachUncle_BeginSoi6Trip =
{
	self.bu_wp_stage = 0;
	BeachUncle_SetState (self, BU_TO_SOI6);
	self.bu_phase = BU_TO_SOI6;
	self.soi6_state_t = time + 35;
	self.bu_stuck = 0;
};

void() BeachUncle_Think =
{
	local vector dir, target_pt;
	local float wy, d, idx;

	if (self.soi6_state == BU_DEAD || self.soi6_state == BU_GIB)
	{
		self.nextthink = time + 0.45;
		if (time > self.soi6_anim_t + 0.40 && self.modelindex)
			setmodel (self, "");
		if (time >= self.soi6_respawn_t)
			BeachUncle_Respawn ();
		return;
	}

	self.nextthink = time + 0.1;
	self.velocity = '0 0 0';
	Soi6_UpdatePassThrough (15);

	// Flies persistently swarm around every Beach Uncle
	pointparticles (particleeffectnum ("beach_uncle_flies"), self.origin, '0 0 0', 1);

	// Scare Soi 6 girls whenever approaching or inside Soi 6
	if (self.origin_x > 40 && time >= self.bu_scare_t)
	{
		self.bu_scare_t = time + 0.25;
		BeachUncle_ScareGirls ();
	}

	// Cheer pause (raises hands & plays yell_1..4.wav from the 2nd video)
	if (self.soi6_state == BU_CHEER)
	{
		if (time >= self.soi6_state_t)
		{
			if (self.bu_phase == BU_WALK_BEACH && random () < 0.35)
			{
				BeachUncle_BeginSoi6Trip ();
			}
			else
			{
				BeachUncle_SetState (self, self.bu_phase);
				if (self.bu_phase == BU_WALK_BEACH)
				{
					BeachUncle_PickNewBeachGoal (self);
					self.soi6_state_t = time + 9.0 + random () * 8.0;
				}
				else if (self.bu_phase == BU_WALK_SOI6)
				{
					self.soi6_state_t = time + 14.0 + random () * 10.0;
				}
				else
				{
					self.soi6_state_t = time + 30.0;
				}
			}
		}
		return;
	}

	// State 0: Walking around Pattaya Beach sand
	if (self.soi6_state == BU_WALK_BEACH)
	{
		if (time >= self.soi6_state_t)
		{
			if (random () < 0.45)
			{
				BeachUncle_BeginSoi6Trip ();
				return;
			}
			self.bu_phase = BU_WALK_BEACH;
			BeachUncle_SetState (self, BU_CHEER);
			self.soi6_state_t = time + 2.4 + random () * 1.4;
			idx = 1 + floor (random () * 4);
			if (time >= self.soi6_talk_t)
			{
				sound (self, CHAN_VOICE, BeachUncle_YellSound (idx), 0.9, ATTN_NORM);
				self.soi6_talk_t = time + 3.0;
			}
			return;
		}

		dir = self.bu_goal - self.origin;
		dir_z = 0;
		d = vlen (dir);
		if (d < 48 || time >= self.bu_steer_t || self.bu_stuck >= 6)
			BeachUncle_PickNewBeachGoal (self);

		dir = self.bu_goal - self.origin;
		dir_z = 0;
		wy = self.soi6_yaw;
		if (vlen (dir) > 4)
			wy = vectoyaw (dir);
		BeachUncle_WalkStep (wy, 8.5);
		return;
	}

	// State 1: Walking from Beach over Promenade + Beach Rd into Soi 6 entrance
	if (self.soi6_state == BU_TO_SOI6)
	{
		if (self.bu_wp_stage == 0)
		{
			target_pt = '-400 0 8';
			if (self.origin_x >= -420 && fabs (self.origin_y) < 120)
				self.bu_wp_stage = 1;
		}
		else
		{
			target_pt = '320 0 8';
			if (self.origin_x >= 260)
			{
				self.bu_phase = BU_WALK_SOI6;
				BeachUncle_SetState (self, BU_WALK_SOI6);
				self.soi6_state_t = time + 18.0 + random () * 14.0;
				self.bu_dir_x = 1;
				return;
			}
		}

		dir = target_pt - self.origin;
		dir_z = 0;
		wy = vectoyaw (dir);
		BeachUncle_WalkStep (wy, 10.5);
		return;
	}

	// State 2: Walking down Soi 6 causing bar girls to run away
	if (self.soi6_state == BU_WALK_SOI6)
	{
		if (self.origin_x > 3400 || time >= self.soi6_state_t)
		{
			self.bu_phase = BU_TO_BEACH;
			BeachUncle_SetState (self, BU_TO_BEACH);
			self.soi6_state_t = time + 40;
			return;
		}

		if (time >= self.soi6_talk_t && random () < 0.04)
		{
			idx = 1 + floor (random () * 4);
			sound (self, CHAN_VOICE, BeachUncle_YellSound (idx), 0.95, ATTN_NORM);
			self.soi6_talk_t = time + 4.5 + random () * 3.0;
		}

		// Gently weave toward left/right bar fronts while progressing East down Soi 6
		makevectors ('0 1 0' * ((time * 32 + self.bu_slot * 75) % 360));
		target_pt_x = self.origin_x + 180;
		target_pt_y = v_forward_y * 78;
		target_pt_z = self.origin_z;
		if (self.origin_x < 260)
			target_pt_y = 0;

		dir = target_pt - self.origin;
		dir_z = 0;
		wy = vectoyaw (dir);
		BeachUncle_WalkStep (wy, 10.0);
		return;
	}

	// State 3: Strolling back West from Soi 6 onto Pattaya Beach
	if (self.soi6_state == BU_TO_BEACH)
	{
		if (self.origin_x > 260)
			target_pt = '180 0 8';
		else if (self.origin_x > -420)
			target_pt = '-460 0 8';
		else
		{
			self.bu_phase = BU_WALK_BEACH;
			BeachUncle_SetState (self, BU_WALK_BEACH);
			BeachUncle_PickNewBeachGoal (self);
			self.soi6_state_t = time + 12.0 + random () * 10.0;
			return;
		}

		dir = target_pt - self.origin;
		dir_z = 0;
		wy = vectoyaw (dir);
		BeachUncle_WalkStep (wy, 10.5);
	}
};

void() BeachUncle_Respawn =
{
	local vector cand;

	cand = BeachUncle_PickBeachSpot (self.bu_slot);
	self.health = BEACH_UNCLE_HP;
	self.max_health = BEACH_UNCLE_HP;
	self.takedamage = DAMAGE_AIM;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.touch = BeachUncle_Touch;
	self.soi6_pass_t = 0;
	self.velocity = '0 0 0';
	self.bu_stuck = 0;
	self.traileffectnum = 0;

	setmodel (self, "progs/beach_uncle_a.md3");
	setsize (self, '-15 -15 0', '15 15 68');
	setorigin (self, cand);
	droptofloor ();
	Soi6_UpdatePassThrough (15);

	self.soi6_yaw = random () * 360;
	self.angles_y = self.soi6_yaw;
	self.bu_phase = BU_WALK_BEACH;
	BeachUncle_SetState (self, BU_WALK_BEACH);
	BeachUncle_PickNewBeachGoal (self);
	self.soi6_state_t = time + 6.0 + random () * 10.0;
	self.nextthink = time + 0.2 + random () * 0.5;
};

entity(float slot, float start_mode, vector org) BeachUncle_SpawnOne =
{
	local entity u;

	u = spawn ();
	u.classname = "npc_beach_uncle";
	u.bu_slot = slot;
	u.health = BEACH_UNCLE_HP;
	u.max_health = BEACH_UNCLE_HP;
	u.takedamage = DAMAGE_AIM;
	u.solid = SOLID_SLIDEBOX;
	u.movetype = MOVETYPE_STEP;
	u.flags = FL_MONSTER;
	u.yaw_speed = 24;
	u.th_stand = BeachUncle_Think;
	u.th_walk = BeachUncle_Think;
	u.th_run = BeachUncle_Think;
	u.th_pain = BeachUncle_Pain;
	u.th_die = BeachUncle_Die;
	u.touch = BeachUncle_Touch;
	u.customizeentityforclient = BeachUncle_Customize;

	setmodel (u, "progs/beach_uncle_a.md3");
	setsize (u, '-15 -15 0', '15 15 68');
	setorigin (u, org);
	local entity saved_self;
	saved_self = self;
	self = u;
	droptofloor ();
	self = saved_self;

	u.soi6_yaw = random () * 360;
	u.angles_y = u.soi6_yaw;
	u.bu_phase = start_mode;
	u.soi6_state = -1;
	BeachUncle_SetState (u, start_mode);
	if (start_mode == BU_WALK_BEACH)
	{
		BeachUncle_PickNewBeachGoal (u);
		u.soi6_state_t = time + 5.0 + random () * 10.0;
	}
	else if (start_mode == BU_TO_SOI6)
	{
		u.bu_wp_stage = 0;
		if (u.origin_x >= -420)
			u.bu_wp_stage = 1;
		u.soi6_state_t = time + 35;
	}
	else
	{
		u.soi6_state_t = time + 22 + random () * 12;
	}

	u.think = BeachUncle_Think;
	u.nextthink = time + 0.1 + slot * 0.05;
	return u;
};

void() BeachUncle_SpawnBeachPack =
{
	local float i, mode;
	local vector org;

	if (world.model != "maps/soi6.bsp")
		return;
	if (bu_spawned || autocvar_bm_soi6_npcs == 0)
		return;
	bu_spawned = TRUE;

	BeachUncle_PrecacheAssets ();

	for (i = 0; i < BEACH_UNCLE_COUNT; i = i + 1)
	{
		if (i < 6)
		{
			// Walkers spread along Pattaya Beach sand
			mode = BU_WALK_BEACH;
			if (i == 0) org = '-560 -220 20';
			else if (i == 1) org = '-740 -80 20';
			else if (i == 2) org = '-610 180 20';
			else if (i == 3) org = '-840 -480 20';
			else if (i == 4) org = '-520 640 20';
			else org = '-790 420 20';
		}
		else if (i < 8)
		{
			// Actively walking across Beach Rd toward Soi 6
			mode = BU_TO_SOI6;
			if (i == 6) org = '-350 -10 20';
			else org = '-40 20 20';
		}
		else
		{
			// Already entering / strolling along Soi 6 making girls flee
			mode = BU_WALK_SOI6;
			if (i == 8) org = '420 -10 20';
			else org = '1050 20 20';
		}
		BeachUncle_SpawnOne (i, mode, org);
	}
	dprint (strcat ("BeachUncle_SpawnBeachPack: spawned ", ftos (BEACH_UNCLE_COUNT), " beach uncles.\n"));
};

// ---- Cheat impulses 71..74 for rapid testing ----

void() BeachUncle_Summon =
{
	local vector org;
	local entity u;

	BeachUncle_PrecacheAssets ();
	makevectors ('0 1 0' * self.v_angle_y);
	org = self.origin + v_forward * 140 + '0 0 24';
	traceline (self.origin + '0 0 24', org, TRUE, self);
	org = trace_endpos - v_forward * 24;
	u = BeachUncle_SpawnOne (99, BU_WALK_BEACH, org);
	u.soi6_yaw = anglemod (self.v_angle_y + 180);
	u.angles_y = u.soi6_yaw;
	sprint (self, "Spawned a Beach Uncle in front of you.\n");
};

void() BeachUncle_GotoBeach =
{
	setorigin (self, '-340 -140 42');
	self.angles = '10 180 0';
	self.v_angle = '10 180 0';
	self.fixangle = TRUE;
	self.velocity = '0 0 0';
	sprint (self, "Teleported to Pattaya Beach promenade looking at beach uncles.\n");
};

void(float dmg) BeachUncle_Poke =
{
	local entity e, best;
	local float best_d, d;

	best = world;
	best_d = 900;
	e = find (world, classname, "npc_beach_uncle");
	while (e)
	{
		if (e.health > 0)
		{
			d = vlen (e.origin - self.origin);
			if (d < best_d)
			{
				best_d = d;
				best = e;
			}
		}
		e = find (e, classname, "npc_beach_uncle");
	}
	if (best == world)
	{
		sprint (self, "No living Beach Uncle nearby.\n");
		return;
	}
	pointparticles (particleeffectnum ("mud_hit"), best.origin + '0 0 32', '0 0 60', 1);
	T_Damage (best, self, self, dmg);
	sprint (self, strcat ("Hit Beach Uncle for ", ftos (dmg), " damage!\n"));
};

void() BeachUncle_SendToSoi6 =
{
	local entity e, best;
	local float best_d, d;

	best = world;
	best_d = 2000;
	e = find (world, classname, "npc_beach_uncle");
	while (e)
	{
		if (e.health > 0)
		{
			d = vlen (e.origin - self.origin);
			if (d < best_d)
			{
				best_d = d;
				best = e;
			}
		}
		e = find (e, classname, "npc_beach_uncle");
	}
	if (best == world)
		return;
	best.bu_wp_stage = 0;
	BeachUncle_SetState (best, BU_TO_SOI6);
	best.bu_phase = BU_TO_SOI6;
	best.soi6_state_t = time + 35;
	sprint (self, "Beach Uncle is walking to Soi 6!\n");
};
