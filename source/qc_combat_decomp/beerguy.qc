#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
==============================================================================
beerguy.qc — BeerGuy (Hawaiian shirt + khaki shorts + sandals + cold beer)
HD 8-direction SPR32 wandering NPC (`npc_beerguy` / `monster_beerguy` / `impulse 50`).
Casually strolls around holding his beer, pauses periodically to take a sip,
and splashes foam / smashes bottle if shot. Harmless ambient NPC (no FL_MONSTER).
==============================================================================
*/

var float autocvar_beer_mode = 0;
var float autocvar_beer_stay = 0;
var float autocvar_beer_hp = 120;
var float autocvar_beer_speed = 68;
var float autocvar_beer_respawn = 10;

// Frame layout in progs/beerguy.spr32 (8 compass dirs x 32 frames/dir = 256 frames)
float BEER_WALK_START  = 0;
float BEER_WALK_COUNT  = 12;
float BEER_SIP_START   = 12;
float BEER_SIP_COUNT   = 10;
float BEER_PAIN_START  = 22;
float BEER_PAIN_COUNT  = 4;
float BEER_GIB_START   = 26;
float BEER_GIB_COUNT   = 6;
float BEER_DIR_STRIDE  = 32;

.float beer_state;      // 0 = walk, 1 = sip pause, 2 = pain hurry, 3 = dead/gib
.float beer_state_end;
.float beer_steer_t;
.float beer_pain_end;
.float beer_step_t;
.float beer_voice_t;
.float beer_phase;
.float beer_fbase;
.float beer_ftime;
.float beer_soi6;
.float beer_dir;
.float beer_stuck;

entity tim_soi6;

void() Beerguy_Think;
void(entity attacker, float take) Beerguy_Pain;
void() Beerguy_Die;
void() Beerguy_Respawn;

float beer_precached;

void() Beerguy_Precache =
{
	if (beer_precached)
		return;
	beer_precached = TRUE;
	precache_model ("progs/beerguy.spr32");
	precache_model ("progs/gib1.mdl");
	precache_model ("progs/gib2.mdl");
	precache_model ("progs/gib3.mdl");
	precache_sound ("beerguy/sip_ahh.wav");
	precache_sound ("beerguy/chill_burp.wav");
	precache_sound ("beerguy/pain_beer.wav");
	precache_sound ("beerguy/bottle_smash.wav");
	precache_sound ("beerguy/footstep_sandal.wav");
};

// Maps viewer angle around self into 8 sprite compass buckets (0=front, 2=left, 4=back, 6=right)
float(entity viewer) Beerguy_Dir8 =
{
	local vector v;
	local float rel, d;
	v = viewer.origin - self.origin;
	v_z = 0;
	rel = vectoyaw (v) - self.angles_y;
	while (rel < 0)
		rel = rel + 360;
	while (rel >= 360)
		rel = rel - 360;
	d = floor ((rel + 22.5) / 45);
	if (d >= 8)
		d = 0;
	return d;
};

float() Beerguy_Customize =
{
	local float k, d;

	if (self.beer_ftime != time)
	{
		self.beer_ftime = time;
		if (self.npc_dead)
		{
			k = floor (self.npc_dstep);
			if (k < 0)
				k = 0;
			if (k >= BEER_GIB_COUNT)
				k = BEER_GIB_COUNT - 1;
			self.beer_fbase = BEER_GIB_START + k;
		}
		else if (time < self.beer_pain_end)
		{
			k = floor ((time - (self.beer_pain_end - 0.35)) * 12);
			if (k < 0)
				k = 0;
			if (k >= BEER_PAIN_COUNT)
				k = BEER_PAIN_COUNT - 1;
			self.beer_fbase = BEER_PAIN_START + k;
		}
		else if (self.beer_state == 1 || autocvar_beer_stay > 0)
		{
			k = floor ((time + self.beer_phase) * 11);
			k = k - BEER_SIP_COUNT * floor (k / BEER_SIP_COUNT);
			self.beer_fbase = BEER_SIP_START + k;
		}
		else
		{
			if (self.beer_state == 2)
				k = floor ((time + self.beer_phase) * 26);
			else
				k = floor ((time + self.beer_phase) * 15);
			k = k - BEER_WALK_COUNT * floor (k / BEER_WALK_COUNT);
			self.beer_fbase = BEER_WALK_START + k;
		}
	}

	d = Beerguy_Dir8 (other);
	self.frame = d * BEER_DIR_STRIDE + self.beer_fbase;
	return TRUE;
};

void(string snd, float vol, float attn) Beerguy_Say =
{
	if (time < self.beer_voice_t)
		return;
	self.beer_voice_t = time + 1.2;
	sound (self, CHAN_VOICE, snd, vol, attn);
};

void() Beerguy_PickWanderYaw =
{
	local vector to_home;
	local float dist, drift;

	if (self.beer_soi6)
	{
		if (self.origin_x >= 11800)
			self.beer_dir = 180;
		else if (self.origin_x <= 480)
			self.beer_dir = 0;

		drift = (random () - 0.5) * 32;
		if (self.origin_y > 70)
			drift = -18 - random () * 14;
		else if (self.origin_y < -70)
			drift = 18 + random () * 14;

		if (self.beer_dir == 0)
			self.ideal_yaw = anglemod (drift);
		else
			self.ideal_yaw = anglemod (180 - drift);
		self.beer_steer_t = time + 1.8 + random () * 2.2;
		return;
	}

	to_home = self.npc_home - self.origin;
	to_home_z = 0;
	dist = vlen (to_home);

	if (dist > self.npc_radius * 0.78)
	{
		self.ideal_yaw = vectoyaw (to_home) + (random () - 0.5) * 45;
	}
	else
	{
		self.ideal_yaw = anglemod (self.angles_y + (random () - 0.5) * 130);
	}
	self.beer_steer_t = time + 2.2 + random () * 3.0;
};

void() Beerguy_Think =
{
	local float spd, step_d, ok;

	self.nextthink = time + 0.05;

	if (self.npc_dead)
	{
		self.npc_dstep = self.npc_dstep + 0.65;
		if (time >= self.beer_state_end)
		{
			Beerguy_Respawn ();
			return;
		}
		if (self.npc_dstep >= BEER_GIB_COUNT)
		{
			// Freeze final smashed bottle & gib puddle until respawn
			self.npc_dstep = BEER_GIB_COUNT - 1;
			self.alpha = 0.01;
		}
		return;
	}

	// Inspection freeze toggle (`beer_stay 1`)
	if (autocvar_beer_stay > 0)
	{
		ChangeYaw ();
		return;
	}

	// Periodic sip pause
	if (self.beer_state == 1)
	{
		if (time >= self.beer_state_end)
		{
			self.beer_state = 0;
			self.beer_state_end = time + 5.5 + random () * 5.0;
			Beerguy_PickWanderYaw ();
		}
		return;
	}

	// Pause to take a casual sip every few seconds (unless hurrying after pain)
	if (self.beer_state == 0 && time >= self.beer_state_end)
	{
		self.beer_state = 1;
		self.beer_state_end = time + 2.2 + random () * 0.8;
		if (random () < 0.25)
			Beerguy_Say ("beerguy/chill_burp.wav", 0.85, ATTN_NORM);
		else
			Beerguy_Say ("beerguy/sip_ahh.wav", 0.85, ATTN_NORM);
		return;
	}

	if (self.beer_state == 2 && time >= self.beer_state_end)
	{
		self.beer_state = 0;
		self.beer_state_end = time + 4.0 + random () * 4.0;
	}

	if (time >= self.beer_steer_t)
		Beerguy_PickWanderYaw ();

	self.yaw_speed = 9;
	ChangeYaw ();

	spd = autocvar_beer_speed;
	if (spd <= 0)
		spd = 68;
	if (self.beer_state == 2)
		spd = spd * 1.75;

	step_d = spd * 0.05;
	ok = walkmove (self.ideal_yaw, step_d);
	if (!ok)
	{
		if (self.beer_soi6)
		{
			if (walkmove (anglemod (self.ideal_yaw + 35), step_d))
				self.beer_stuck = 0;
			else if (walkmove (anglemod (self.ideal_yaw - 35), step_d))
				self.beer_stuck = 0;
			else
			{
				self.beer_stuck = self.beer_stuck + 1;
				if (self.beer_stuck >= 8)
				{
					self.beer_stuck = 0;
					if (self.beer_dir == 0)
						self.beer_dir = 180;
					else
						self.beer_dir = 0;
					self.ideal_yaw = self.beer_dir;
					self.angles_y = self.beer_dir;
				}
			}
		}
		else
		{
			// Steer cleanly around obstacles without getting stuck
			self.ideal_yaw = anglemod (self.ideal_yaw + 105 + (random () - 0.5) * 70);
			self.angles_y = self.ideal_yaw;
			self.beer_steer_t = time + 1.4;
			walkmove (self.ideal_yaw, step_d * 0.6);
		}
	}
	else
	{
		self.beer_stuck = 0;
		if (time >= self.beer_step_t)
		{
			self.beer_step_t = time + 0.42;
			sound (self, CHAN_BODY, "beerguy/footstep_sandal.wav", 0.32, ATTN_IDLE);
		}
	}
};

void(entity attacker, float take) Beerguy_Pain =
{
	if (self.npc_dead)
		return;
	self.beer_pain_end = time + 0.35;
	self.beer_state = 2;
	self.beer_state_end = time + 2.8;
	self.ideal_yaw = vectoyaw (self.origin - attacker.origin) + (random () - 0.5) * 50;
	Beerguy_Say ("beerguy/pain_beer.wav", 0.95, ATTN_NORM);
};

void() Beerguy_Die =
{
	if (self.npc_dead)
		return;
	self.npc_dead = TRUE;
	self.npc_dstep = 0;
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.beer_state = 3;
	self.beer_state_end = time + autocvar_beer_respawn;

	sound (self, CHAN_VOICE, "beerguy/bottle_smash.wav", 1, ATTN_NORM);
	ThrowGib ("progs/gib1.mdl", -45);
	ThrowGib ("progs/gib2.mdl", -60);
	ThrowGib ("progs/gib3.mdl", -55);
};

void(vector pos, float yaw_deg) Beerguy_Setup =
{
	setmodel (self, "progs/beerguy.spr32");
	self.classname = "npc_tim";
	self.netname = "TimBlackburn";
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.takedamage = DAMAGE_AIM;
	self.health = autocvar_beer_hp;
	self.max_health = self.health;
	self.scale = 0.4912;
	self.colormod = '1 1 1';
	self.alpha = 1;
	self.effects = 0;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	self.beer_state = 0;
	self.beer_phase = random () * 5;
	self.beer_state_end = time + 4.5 + random () * 4.5;
	self.beer_steer_t = time + 1.5;
	self.beer_pain_end = 0;
	self.angles = '0 0 0';
	self.angles_y = yaw_deg;
	self.ideal_yaw = yaw_deg;
	self.yaw_speed = 9;
	setsize (self, '-16 -16 0', '16 16 56');
	setorigin (self, pos);
	droptofloor ();

	self.th_pain = Beerguy_Pain;
	self.th_die = Beerguy_Die;
	self.customizeentityforclient = Beerguy_Customize;
	self.think = Beerguy_Think;
	self.nextthink = time + 0.05;
};

void() Beerguy_Respawn =
{
	local vector pos;
	local float yaw_deg;

	if (self.beer_soi6)
	{
		pos = '3420 22 8';
		pos_x = 600 + random () * 8200;
		pos_y = (random () - 0.5) * 90;
		yaw_deg = self.beer_dir;
		Beerguy_Setup (pos, yaw_deg);
		return;
	}
	Beerguy_Setup (self.npc_home, self.angles_y);
};

void() npc_beerguy =
{
	if (BM_NoMapNPC ())		// no map NPCs unless bm_npcs 1 (2026-11-26)
	{
		remove (self);
		return;
	}
	if (!beer_precached)
		Beerguy_Precache ();
	self.npc_home = self.origin;
	if (!self.npc_radius)
		self.npc_radius = 320;
	Beerguy_Setup (self.origin, self.angles_y);
};

void() monster_beerguy =
{
	npc_beerguy ();
};

void() npc_tim =
{
	if (BM_NoMapNPC ())		// no map NPCs unless bm_npcs 1 (2026-11-26)
	{
		remove (self);
		return;
	}
	npc_beerguy ();
};

void() monster_tim =
{
	npc_beerguy ();
};

void() npc_timblackburn =
{
	if (BM_NoMapNPC ())		// no map NPCs unless bm_npcs 1 (2026-11-26)
	{
		remove (self);
		return;
	}
	npc_beerguy ();
};

void() monster_timblackburn =
{
	npc_beerguy ();
};

void() Tim_CineStart;

void() Tim_SpawnSoi6 =
{
	local entity e, oself;
	local vector org;

	if (tim_soi6 && tim_soi6 != world && (tim_soi6.classname == "npc_tim" || tim_soi6.classname == "npc_beerguy"))
		return;

	if (!beer_precached)
		Beerguy_Precache ();

	org = '3420 22 8';
	e = spawn ();
	e.npc_home = org;
	e.npc_radius = 6500;
	e.beer_soi6 = 1;
	e.beer_dir = 180;
	e.beer_stuck = 0;
	oself = self;
	self = e;
	Beerguy_Setup (org, 180);
	self = oself;
	tim_soi6 = e;
	print ("Tim_SpawnSoi6: TimBlackburn spawned walking on Soi 6.\n");
	Tim_CineStart ();
};

void() Beerguy_Summon =
{
	local entity e;
	local vector org;

	if (!beer_precached)
	{
		bprint ("TimBlackburn not precached yet -- start map with +sv_cheats 1 or +beer_mode 1\n");
		return;
	}

	makevectors (self.v_angle);
	v_forward_z = 0;
	v_forward = normalize (v_forward);
	org = self.origin + v_forward * 112 - '0 0 22';

	e = spawn ();
	e.npc_home = org;
	e.npc_radius = 320;
	e.angles_y = anglemod (self.v_angle_y + 180);
	{
		local entity oself;
		oself = self;
		self = e;
		Beerguy_Setup (org, e.angles_y);
		self = oself;
	}
	bprint ("TimBlackburn summoned (impulse 50) -- strolling with a cold one! Use beer_stay 1 to inspect.\n");
};
