/*
==============================================================================
REESEICE — HD High-FPS Screaming Ice-Bath NPC (`npc_reeseice`)

144x144px HDR-calibrated DarkPlaces `.spr32` (8 compass angles x 44 frames @ 24 FPS)
Animations (dir-major frame layout: d * 44 + anim_offset):
  - scream     (0..11, 12f @ 24 FPS)  : Intense cold-shock open-mouth roar + frost breath
  - shiver_hop (12..21, 10f @ 24 FPS) : Frantic ice-tub bounce & teeth-chattering panic
  - ice_erupt  (22..33, 12f @ 24 FPS) : Skyward brain-freeze roar erupting ice cubes
  - pain       (34..37, 4f @ 20 FPS)  : Knockback tub-tilt blood recoil
  - gib_death  (38..43, 6f @ 16 FPS)  : 3D Quake meat & ice-cube shatter explosion

Console / cheat controls (`sv_cheats 1`):
  impulse 49    : Summon ReeseIce in front of player (facing player)
  reese_stay 1  : Anchor ReeseIce in place for angle turnaround inspection
  reese_mode 1  : Precache at map start
==============================================================================
*/

float REESE_FRAMES_PER_DIR = 44;
float REESE_SCALE = 0.4912;

float REESE_SCREAM = 0;
float REESE_SHIVER = 1;
float REESE_ERUPT  = 2;
float REESE_PAIN   = 3;
float REESE_DEAD   = 4;

var float autocvar_reese_stay = 0;

float reeseice_precached;

.float reese_anim_t;

void() ReeseIce_Think;
void() ReeseIce_Die;
void(entity attacker, float take) ReeseIce_Pain;

void() ReeseIce_Precache =
{
	if (reeseice_precached)
		return;
	reeseice_precached = 1;
	precache_model("progs/reeseice.spr32");
	precache_model("progs/gib1.mdl");
	precache_model("progs/gib2.mdl");
	precache_model("progs/gib3.mdl");
	precache_sound("reeseice/scream1.wav");
	precache_sound("reeseice/scream2.wav");
	precache_sound("reeseice/shiver_yell.wav");
	precache_sound("reeseice/ice_explode.wav");
};

float() ReeseIce_Dir8 =
{
	local vector delta;
	local float rel, d;

	delta = other.origin - self.origin;
	rel = anglemod(vectoyaw(delta) - self.angles_y);
	d = rint(rel / 45);
	if (d >= 8)
		d = 0;
	if (d < 0)
		d = 0;
	return d;
};

float(float val, float modulus) ReeseIce_Mod =
{
	return val - modulus * floor(val / modulus);
};

float() ReeseIce_Customize =
{
	local float d, k, elapsed;

	d = ReeseIce_Dir8();
	elapsed = max(0, time - self.reese_anim_t);

	if (self.npc_state == REESE_DEAD)
	{
		k = floor(elapsed * 16);
		if (k > 5)
			k = 5;
		self.frame = d * REESE_FRAMES_PER_DIR + 38 + k;
		return TRUE;
	}
	if (self.npc_state == REESE_PAIN)
	{
		k = floor(elapsed * 20);
		if (k > 3)
			k = 3;
		self.frame = d * REESE_FRAMES_PER_DIR + 34 + k;
		return TRUE;
	}
	if (self.npc_state == REESE_ERUPT)
	{
		k = ReeseIce_Mod(floor(elapsed * 24), 12);
		self.frame = d * REESE_FRAMES_PER_DIR + 22 + k;
		return TRUE;
	}
	if (self.npc_state == REESE_SHIVER)
	{
		k = ReeseIce_Mod(floor(elapsed * 24), 10);
		self.frame = d * REESE_FRAMES_PER_DIR + 12 + k;
		return TRUE;
	}

	// Default continuous 24 FPS high-frame-rate screaming loop
	k = ReeseIce_Mod(floor(elapsed * 24), 12);
	self.frame = d * REESE_FRAMES_PER_DIR + k;
	return TRUE;
};

void(string wav) ReeseIce_PlayScream =
{
	if (NPC_IsVoiceMuted(self))
		return;
	sound(self, CHAN_VOICE, wav, 1, ATTN_NORM);
};

void() ReeseIce_Respawn =
{
	self.solid = SOLID_BBOX;
	self.movetype = MOVETYPE_STEP;
	self.takedamage = DAMAGE_AIM;
	self.health = 180;
	self.deadflag = DEAD_NO;
	self.npc_state = REESE_SCREAM;
	self.reese_anim_t = time;
	self.npc_phase_end = time + 1.8;
	setmodel(self, "progs/reeseice.spr32");
	self.scale = REESE_SCALE;
	setsize(self, '-20 -20 0', '20 20 56');
	setorigin(self, self.npc_home);
	droptofloor();
	self.customizeentityforclient = ReeseIce_Customize;
	ReeseIce_PlayScream("reeseice/scream1.wav");
	self.think = ReeseIce_Think;
	self.nextthink = time + 0.1;
};

void() ReeseIce_DeathStep =
{
	if (time >= self.npc_respawn)
	{
		ReeseIce_Respawn();
		return;
	}
	self.think = ReeseIce_DeathStep;
	self.nextthink = time + 0.25;
};

void() ReeseIce_Die =
{
	if (self.npc_state == REESE_DEAD)
		return;
	self.npc_state = REESE_DEAD;
	self.reese_anim_t = time;
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.deadflag = DEAD_DEAD;
	self.npc_respawn = time + 8;

	sound(self, CHAN_VOICE, "reeseice/ice_explode.wav", 1, ATTN_NORM);
	particle(self.origin + '0 0 32', '0 0 90', 216, 48);
	ThrowGib("progs/gib1.mdl", -85);
	ThrowGib("progs/gib2.mdl", -95);
	ThrowGib("progs/gib3.mdl", -105);

	self.think = ReeseIce_DeathStep;
	self.nextthink = time + 0.45;
};

void(entity attacker, float take) ReeseIce_Pain =
{
	if (self.npc_state == REESE_DEAD)
		return;
	self.npc_state = REESE_PAIN;
	self.reese_anim_t = time;
	self.npc_phase_end = time + 0.28;
	if (time > self.npc_next_voice)
	{
		self.npc_next_voice = time + 0.65;
		ReeseIce_PlayScream("reeseice/scream2.wav");
	}
	self.think = ReeseIce_Think;
	self.nextthink = time + 0.05;
};

void() ReeseIce_Think =
{
	local entity head, best;
	local float dist, best_d, r;

	if (self.npc_state == REESE_DEAD)
		return;

	if (time >= self.npc_phase_end)
	{
		r = random();
		if (r < 0.36)
		{
			self.npc_state = REESE_SHIVER;
			self.reese_anim_t = time;
			self.npc_phase_end = time + 1.4 + random() * 0.8;
			if (time > self.npc_next_voice)
			{
				self.npc_next_voice = time + 1.1;
				ReeseIce_PlayScream("reeseice/shiver_yell.wav");
			}
		}
		else if (r < 0.72)
		{
			self.npc_state = REESE_ERUPT;
			self.reese_anim_t = time;
			self.npc_phase_end = time + 1.5 + random() * 0.9;
			particle(self.origin + '0 0 36', '0 0 65', 212, 18);
			if (time > self.npc_next_voice)
			{
				self.npc_next_voice = time + 1.1;
				ReeseIce_PlayScream("reeseice/scream2.wav");
			}
		}
		else
		{
			self.npc_state = REESE_SCREAM;
			self.reese_anim_t = time;
			self.npc_phase_end = time + 1.6 + random() * 1.0;
			if (time > self.npc_next_voice)
			{
				self.npc_next_voice = time + 1.1;
				ReeseIce_PlayScream("reeseice/scream1.wav");
			}
		}
	}

	// Keep shivering ice-tub anchored if `reese_stay 1`, else face nearest player and shiver-hop around home
	if (!autocvar_reese_stay && !(self.spawnflags & 1))
	{
		best = world;
		best_d = 900;
		head = find(world, classname, "player");
		while (head != world)
		{
			if (head.health > 0)
			{
				dist = vlen(head.origin - self.origin);
				if (dist < best_d)
				{
					best_d = dist;
					best = head;
				}
			}
			head = find(head, classname, "player");
		}
		if (best != world)
		{
			self.ideal_yaw = vectoyaw(best.origin - self.origin);
			ChangeYaw();
		}
	}

	if (self.npc_state == REESE_ERUPT && random() < 0.45)
		particle(self.origin + '0 0 38', '0 0 55', 216, 6);

	self.think = ReeseIce_Think;
	self.nextthink = time + 0.1;
};

void() npc_reeseice =
{
	ReeseIce_Precache();
	self.classname = "npc_reeseice";
	self.solid = SOLID_BBOX;
	self.movetype = MOVETYPE_STEP;
	self.takedamage = DAMAGE_AIM;
	self.health = 180;
	self.yaw_speed = 18;
	self.npc_home = self.origin;
	self.npc_state = REESE_SCREAM;
	self.reese_anim_t = time;
	self.npc_phase_end = time + 1.5;
	setmodel(self, "progs/reeseice.spr32");
	self.scale = REESE_SCALE;
	setsize(self, '-20 -20 0', '20 20 56');
	droptofloor();
	self.npc_home = self.origin;
	self.th_pain = ReeseIce_Pain;
	self.th_die = ReeseIce_Die;
	self.customizeentityforclient = ReeseIce_Customize;
	self.think = ReeseIce_Think;
	self.nextthink = time + 0.1;
};

void() monster_reeseice =
{
	npc_reeseice();
};

void() ReeseIce_Summon =
{
	local entity e;
	local vector spot, oself_ang;

	local vector flat_ang;
	ReeseIce_Precache();
	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	spot = self.origin + v_forward * 112 + '0 0 24';
	traceline(self.origin + '0 0 24', spot, FALSE, self);
	if (trace_fraction < 1.0)
		spot = trace_endpos - v_forward * 28;
	traceline(spot, spot - '0 0 128', TRUE, self);
	if (trace_fraction < 1.0)
		spot = trace_endpos + '0 0 2';

	oself_ang = self.origin - spot;
	e = spawn();
	e.classname = "npc_reeseice";
	e.origin = spot;
	e.angles_y = vectoyaw(oself_ang);
	e.ideal_yaw = e.angles_y;
	e.solid = SOLID_BBOX;
	e.movetype = MOVETYPE_STEP;
	e.takedamage = DAMAGE_AIM;
	e.health = 180;
	e.yaw_speed = 18;
	e.npc_home = spot;
	e.npc_state = REESE_SCREAM;
	e.reese_anim_t = time;
	e.npc_phase_end = time + 1.5;
	setmodel(e, "progs/reeseice.spr32");
	e.scale = REESE_SCALE;
	setsize(e, '-20 -20 0', '20 20 56');
	e.th_pain = ReeseIce_Pain;
	e.th_die = ReeseIce_Die;
	e.customizeentityforclient = ReeseIce_Customize;
	e.think = ReeseIce_Think;
	e.nextthink = time + 0.05;

	sound(e, CHAN_VOICE, "reeseice/scream1.wav", 1, ATTN_NORM);
	sprint(self, "Spawned ReeseIce (screaming in the ice bath!)\n");
};
