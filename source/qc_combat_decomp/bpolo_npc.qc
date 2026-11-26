#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
==============================================================================
bpolo_npc.qc -- RogerVer 360-Degree Animated Sprite NPC (`progs/rogerver.spr32`)
8-direction VP_PARALLEL_UPRIGHT RGBA sprite (`npc_rogerver` / `npc_bpolo` / `impulse 67`).
Harmless ambient NPC (no FL_MONSTER): strolls casually around, pauses to relax,
sprints away if hurt, and bursts into chunky Quake 1 gibs before respawning.

32-frame-per-direction SPR32 layout (8 directions x 32 frames = 256 frames):
  0..11  (12f) Casual Walk
  12..21 (10f) Relaxed Idle
  22..25  (4f) Pain Flinch
  26..31  (6f) Gib Death
Stored per direction `d` (0..7, 45 deg step) at `d * 32 + fbase`.

Inspection cvars:
  bpolo_mode   0 = AI (default), 1 = force Walk, 2 = force Panic Run, 3 = force Idle, 4 = force Idle
  bpolo_stay   0 = normal movement (default), 1 = animate in-place
==============================================================================
*/

var float autocvar_bpolo_mode = 0;
var float autocvar_bpolo_stay = 0;
var float autocvar_bpolo_hp = 120;
var float autocvar_bpolo_speed = 72;
var float autocvar_bpolo_respawn = 12;

float ROGER_WALK_START = 0;
float ROGER_WALK_COUNT = 12;
float ROGER_IDLE_START = 12;
float ROGER_IDLE_COUNT = 10;
float ROGER_PAIN_START = 22;
float ROGER_PAIN_COUNT = 4;
float ROGER_GIB_START  = 26;
float ROGER_GIB_COUNT  = 6;
float ROGER_DIR_STRIDE = 32;

float BPOLO_ST_WALK  = 0;
float BPOLO_ST_EMOTE = 1;
float BPOLO_ST_IDLE  = 2;
float BPOLO_ST_PANIC = 3;
float BPOLO_ST_DEAD  = 4;

.float bpolo_state;
.float bpolo_state_end;
.float bpolo_steer_t;
.float bpolo_pain_end;
.float bpolo_step_t;
.float bpolo_voice_t;
.float bpolo_anim_f;
.float bpolo_base_f;

float bpolo_precached;

void() Bpolo_Think;
void(entity attacker, float take) Bpolo_Pain;
void() Bpolo_Die;
void(vector pos, float yaw_deg) Bpolo_Setup;

float(entity ent, entity viewer) Roger_Dir8 =
{
	local vector to_viewer;
	local float view_yaw, rel, d;

	to_viewer = viewer.origin - ent.origin;
	to_viewer_z = 0;
	if (vlen (to_viewer) < 1)
		return 0;
	view_yaw = vectoyaw (to_viewer);
	rel = anglemod (view_yaw - ent.angles_y);
	d = floor (anglemod (rel + 22.5) / 45);
	if (d >= 8)
		d = 0;
	return d;
};

float() Roger_Customize =
{
	local float d, fbase;

	if (!other || (other.flags & FL_CLIENT) == 0)
		return TRUE;

	d = Roger_Dir8 (self, other);
	fbase = self.bpolo_base_f;
	if (fbase < 0)
		fbase = 0;
	if (fbase >= ROGER_DIR_STRIDE)
		fbase = ROGER_DIR_STRIDE - 1;
	self.frame = d * ROGER_DIR_STRIDE + fbase;
	return TRUE;
};

void() Bpolo_Precache =
{
	if (bpolo_precached)
		return;
	bpolo_precached = TRUE;

	precache_model ("progs/rogerver.spr32");
	precache_model ("progs/gib1.mdl");
	precache_model ("progs/gib2.mdl");
	precache_model ("progs/gib3.mdl");

	precache_sound ("bpolo/greet.wav");
	precache_sound ("bpolo/pain.wav");
	precache_sound ("bpolo/death.wav");
	precache_sound ("bpolo/step.wav");
};

void() Roger_Precache =
{
	Bpolo_Precache ();
};

void(string snd, float vol, float attn) Bpolo_Say =
{
	if (time < self.bpolo_voice_t)
		return;
	self.bpolo_voice_t = time + 1.4;
	sound (self, CHAN_VOICE, snd, vol, attn);
};

void() Bpolo_PickWanderYaw =
{
	local vector to_home;
	local float d;

	to_home = self.npc_home - self.origin;
	to_home_z = 0;
	d = vlen (to_home);
	if (d > self.npc_radius)
		self.ideal_yaw = vectoyaw (to_home) + (random () - 0.5) * 35;
	else
		self.ideal_yaw = anglemod (self.angles_y + (random () - 0.5) * 110);
	self.bpolo_steer_t = time + 1.8 + random () * 2.4;
};

void() Bpolo_Think =
{
	local float spd, step_d, ok, mode, fbase, fcount, frate, anim_st, local_f;

	self.nextthink = time + 0.05;

	if (self.npc_dead)
	{
		if (self.npc_dstep < ROGER_GIB_COUNT - 1)
		{
			self.npc_dstep = self.npc_dstep + 0.42;
			if (self.npc_dstep >= ROGER_GIB_COUNT - 1)
				self.npc_dstep = ROGER_GIB_COUNT - 1;
		}
		self.bpolo_base_f = ROGER_GIB_START + floor (self.npc_dstep);
		self.frame = self.bpolo_base_f;
		if (time >= self.bpolo_state_end)
		{
			if (self.npc_respawn < 0)
			{
				remove (self);
				return;
			}
			Bpolo_Setup (self.npc_home, self.angles_y);
		}
		return;
	}

	mode = autocvar_bpolo_mode;
	if (mode == 1)
		anim_st = BPOLO_ST_WALK;
	else if (mode == 2)
		anim_st = BPOLO_ST_PANIC;
	else if (mode == 3)
		anim_st = BPOLO_ST_EMOTE;
	else if (mode == 4)
		anim_st = BPOLO_ST_IDLE;
	else
	{
		if (time >= self.bpolo_state_end)
		{
			if (self.bpolo_state == BPOLO_ST_PANIC)
			{
				self.bpolo_state = BPOLO_ST_WALK;
				self.bpolo_state_end = time + 5.5 + random () * 4.5;
				Bpolo_PickWanderYaw ();
			}
			else if (self.bpolo_state == BPOLO_ST_EMOTE || self.bpolo_state == BPOLO_ST_IDLE)
			{
				self.bpolo_state = BPOLO_ST_WALK;
				self.bpolo_state_end = time + 6.0 + random () * 5.0;
				Bpolo_PickWanderYaw ();
			}
			else
			{
				if (random () < 0.5)
				{
					self.bpolo_state = BPOLO_ST_EMOTE;
					self.bpolo_state_end = time + 2.0 + random () * 0.9;
					Bpolo_Say ("bpolo/greet.wav", 0.9, ATTN_NORM);
				}
				else
				{
					self.bpolo_state = BPOLO_ST_IDLE;
					self.bpolo_state_end = time + 1.8 + random () * 1.2;
				}
			}
		}
		anim_st = self.bpolo_state;
	}

	if (time < self.bpolo_pain_end)
	{
		local float pk;
		pk = floor ((time - (self.bpolo_pain_end - 0.35)) * 12);
		if (pk < 0)
			pk = 0;
		if (pk >= ROGER_PAIN_COUNT)
			pk = ROGER_PAIN_COUNT - 1;
		local_f = ROGER_PAIN_START + pk;
	}
	else
	{
		if (anim_st == BPOLO_ST_PANIC)
		{
			fbase = ROGER_WALK_START;
			fcount = ROGER_WALK_COUNT;
			frate = 0.86;
		}
		else if (anim_st == BPOLO_ST_EMOTE || anim_st == BPOLO_ST_IDLE)
		{
			fbase = ROGER_IDLE_START;
			fcount = ROGER_IDLE_COUNT;
			frate = 0.45;
		}
		else
		{
			fbase = ROGER_WALK_START;
			fcount = ROGER_WALK_COUNT;
			frate = 0.60;
		}
		self.bpolo_anim_f = self.bpolo_anim_f + frate;
		if (self.bpolo_anim_f >= fcount)
			self.bpolo_anim_f = self.bpolo_anim_f - fcount * floor (self.bpolo_anim_f / fcount);
		local_f = fbase + floor (self.bpolo_anim_f);
	}

	self.bpolo_base_f = local_f;
	self.frame = local_f;

	if (autocvar_bpolo_stay)
		return;
	if (anim_st == BPOLO_ST_EMOTE || anim_st == BPOLO_ST_IDLE)
		return;

	if (time >= self.bpolo_steer_t)
		Bpolo_PickWanderYaw ();

	self.yaw_speed = 9;
	ChangeYaw ();

	spd = autocvar_bpolo_speed;
	if (spd <= 0)
		spd = 72;
	if (anim_st == BPOLO_ST_PANIC)
		spd = spd * 1.85;

	step_d = spd * 0.05;
	ok = walkmove (self.ideal_yaw, step_d);
	if (!ok)
	{
		self.ideal_yaw = anglemod (self.ideal_yaw + 105 + (random () - 0.5) * 70);
		self.angles_y = self.ideal_yaw;
		self.bpolo_steer_t = time + 1.4;
		walkmove (self.ideal_yaw, step_d * 0.6);
	}
	else if (time >= self.bpolo_step_t)
	{
		if (anim_st == BPOLO_ST_PANIC)
			self.bpolo_step_t = time + 0.28;
		else
			self.bpolo_step_t = time + 0.44;
		sound (self, CHAN_BODY, "bpolo/step.wav", 0.35, ATTN_IDLE);
	}
};

void(entity attacker, float take) Bpolo_Pain =
{
	if (self.npc_dead)
		return;
	self.bpolo_pain_end = time + 0.35;
	self.bpolo_state = BPOLO_ST_PANIC;
	self.bpolo_state_end = time + 3.0;
	self.ideal_yaw = vectoyaw (self.origin - attacker.origin) + (random () - 0.5) * 50;
	Bpolo_Say ("bpolo/pain.wav", 0.95, ATTN_NORM);
};

void() Bpolo_Die =
{
	if (self.npc_dead)
		return;
	self.npc_dead = TRUE;
	self.npc_dstep = 0;
	self.bpolo_base_f = ROGER_GIB_START;
	self.frame = ROGER_GIB_START;
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.bpolo_state = BPOLO_ST_DEAD;
	self.bpolo_state_end = time + autocvar_bpolo_respawn;

	sound (self, CHAN_VOICE, "bpolo/death.wav", 1, ATTN_NORM);
	if (self.health < -45)
	{
		ThrowGib ("progs/gib1.mdl", -45);
		ThrowGib ("progs/gib2.mdl", -55);
	}
};

void(vector pos, float yaw_deg) Bpolo_Setup =
{
	setmodel (self, "progs/rogerver.spr32");
	self.classname = "npc_rogerver";
	self.netname = "RogerVer";
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.takedamage = DAMAGE_AIM;
	self.health = autocvar_bpolo_hp;
	self.max_health = self.health;
	self.scale = 0.4912;
	self.colormod = '1 1 1';
	self.alpha = 1;
	self.effects = 0;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	self.bpolo_state = BPOLO_ST_WALK;
	self.bpolo_anim_f = 0;
	self.bpolo_base_f = ROGER_WALK_START;
	self.frame = ROGER_WALK_START;
	self.bpolo_state_end = time + 5.5 + random () * 4.5;
	self.bpolo_steer_t = time + 1.5;
	self.bpolo_pain_end = 0;
	self.angles = '0 0 0';
	self.angles_y = yaw_deg;
	self.ideal_yaw = yaw_deg;
	self.yaw_speed = 9;
	setsize (self, '-16 -16 0', '16 16 56');
	setorigin (self, pos);
	droptofloor ();

	self.customizeentityforclient = Roger_Customize;
	self.th_pain = Bpolo_Pain;
	self.th_die = Bpolo_Die;
	self.think = Bpolo_Think;
	self.nextthink = time + 0.05;
};

void() npc_rogerver =
{
	if (BM_NoMapNPC ())		// no map NPCs unless bm_npcs 1 (2026-11-26)
	{
		remove (self);
		return;
	}
	if (!bpolo_precached)
		Bpolo_Precache ();
	self.npc_home = self.origin;
	if (!self.npc_radius)
		self.npc_radius = 320;
	Bpolo_Setup (self.origin, self.angles_y);
};

void() monster_rogerver =
{
	npc_rogerver ();
};

void() npc_bpolo =
{
	if (BM_NoMapNPC ())		// no map NPCs unless bm_npcs 1 (2026-11-26)
	{
		remove (self);
		return;
	}
	npc_rogerver ();
};

void() monster_bpolo =
{
	npc_rogerver ();
};

void() Bpolo_Summon =
{
	local entity e, oself;
	local vector flat_ang, org;

	if (!bpolo_precached)
	{
		bprint ("RogerVer sprite not precached yet -- start map with +sv_cheats 1 or +bpolo_mode 1\n");
		return;
	}

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors (flat_ang);
	org = self.origin + v_forward * 116 + '0 0 8';

	e = spawn ();
	e.npc_home = org;
	e.npc_radius = 320;
	e.npc_respawn = -1;
	oself = self;
	self = e;
	Bpolo_Setup (org, anglemod (oself.v_angle_y + 180));
	self = oself;
	sound (e, CHAN_VOICE, "bpolo/greet.wav", 0.9, ATTN_NORM);
	bprint ("RogerVer (360 sprite) summoned (impulse 67)! Use bpolo_stay 1 / bpolo_mode 1..4 to inspect.\n");
};

void() Roger_Summon =
{
	Bpolo_Summon ();
};
