#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
David Ojeda & the 3 Running Pregnant Hispanic Women (david.qc).

Impulses:
  impulse 22  Summon David Ojeda + all 3 Running Pregnant Hispanic Women chasing him!
  impulse 23  Summon Solo Fast-Running David Ojeda
  impulse 24  Summon David Ojeda Playing on a Casino Slot Machine (360° Spin -> 777 Jackpot -> Bust)
  impulse 25  Summon the 3 Running Pregnant Hispanic Women (preg_1, preg_2, preg_3)

Full 360° 8-Direction Frame Layout on progs/david.spr32 (264 frames, 96x108, origin (-48, 98), scale 0.6935):
  0..7               8-direction Standing Idle (d = 0..7)
  8 + d*4 + k        8-direction Fast Running Cycle (d = 0..7, k = 0..3) [mbox.qc compatible]
  40 + d*4 + k       8-direction Turbo Speed-Burst Sprint (d = 0..7, k = 0..3)
  72 + d*4 + k       8-direction Holding & Flexing Bag of Money (d = 0..7, k = 0..3)
  104 + d*4 + k      8-direction Fast Heist Sprint Holding Bag of Money (d = 0..7, k = 0..3)
  136 + d*4 + k      8-direction Playing Slot Machine: Lever Pull & Reel Spin (d = 0..7, k = 0..3)
  168 + d*4 + k      8-direction Playing Slot Machine: 7-7-7 JACKPOT Cash Explosion (d = 0..7, k = 0..3)
  200 + d*4 + k      8-direction Playing Slot Machine: Near-Miss BUST & Tilt Shake (d = 0..7, k = 0..3)
  232 + d*4 + k      8-direction Falling Collapse Death (d = 0..7, k = 0..3)

Pregnant Runners on progs/preg_1.spr32, progs/preg_2.spr32, progs/preg_3.spr32 (88 frames each, 136x153, scale 0.4800):
  0..7               8-direction Standing Idle (d = 0..7)
  8 + d*6 + k        8-direction Running Cycle (d = 0..7, k = 0..5) [mbox.qc compatible]
  56 + d*4 + k       8-direction Falling Collapse Death (d = 0..7, k = 0..3)

Optional console cvars for inspection:
  dv_mode 0..8       0 = autonomous AI, 1 = Idle, 2 = Fast Run, 3 = Turbo Sprint,
                     4 = Holding Money Bag, 5 = Running w/ Money Bag,
                     6 = Slot Machine Spin, 7 = Slot Machine 777 Jackpot, 8 = Slot Machine Bust
  dv_stay 0/1        1 = hold position in place so players can walk 360° around freely
  dv_spin <deg>      turntable auto-spin yaw step when dv_stay 1
*/

float	DV_EF_GOLD	= 8;		// EF_DIMLIGHT warm casino gold glow
float	DV_EF_RED	= 128;		// DarkPlaces red dynamic light

.float	dv_state;		// 0=idle, 1=fast_run, 2=turbo, 3=money_hold, 4=money_run, 5=slot_spin, 6=slot_jackpot, 7=slot_bust
.float	dv_phase_end;
.float	dv_next_act;
.float	dv_next_voice;
.float	dv_next_touch;
.float	dv_scan_t;
.float	dv_slot_only;
.float	dv_alt;
.float	dv_harmless;
.float	dv_respawn;
.float	dv_runner_idx;
.vector	dv_home;
.entity	dv_chased;

void() David_Think;
void() David_Die;
void(entity attacker, float take) David_Pain;
void() PregRunner_Think;
void() PregRunner_Die;

void() David_Precache =
{
	if (david_precached)
		return;
	david_precached = TRUE;
	precache_model("progs/david.spr32");
	precache_model("progs/preg_1.spr32");
	precache_model("progs/preg_2.spr32");
	precache_model("progs/preg_3.spr32");
	precache_model("progs/gib1.mdl");
	precache_model("progs/gib2.mdl");
	precache_model("progs/gib3.mdl");
	precache_sound("david/shower_love.wav");
	precache_sound("david/sprint_rush.wav");
	precache_sound("david/money_bag.wav");
	precache_sound("david/slot_spin.wav");
	precache_sound("david/slot_jackpot.wav");
	precache_sound("david/slot_bust.wav");
	precache_sound("weapons/r_exp3.wav");
	precache_sound("player/udeath.wav");
	precache_sound("player/pain4.wav");
};

float() David_Customize =
{
	local float rel, d, k, st, m, fps;
	local vector delta;

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 28');
	rel = vectoyaw(delta) - self.angles_y;
	rel = rel - 360 * floor(rel / 360);
	d = floor(rel / 45 + 0.5);
	if (d >= 8)
		d = 0;

	if (self.npc_dead)
	{
		k = floor(self.npc_dstep * 0.67);
		if (k < 0)
			k = 0;
		if (k > 3)
			k = 3;
		self.frame = 232 + d * 4 + k;
		return TRUE;
	}

	st = self.dv_state;
	m = bm_cvar_dv_mode;
	if (m >= 1 && m <= 8)
		st = m - 1;

	if (st <= 0)
	{
		self.frame = d;
		return TRUE;
	}

	fps = 9.5;
	if (st == 1 || st == 2 || st == 4)
		fps = 12;	// Fast high-cadence sprinting!
	else if (st == 5)
		fps = 10.5;	// Rapid slot reel spin!

	k = floor(time * fps + self.origin_x * 0.02);
	k = k - 4 * floor(k / 4);

	if (st == 1)
		self.frame = 8 + d * 4 + k;
	else if (st == 2)
		self.frame = 40 + d * 4 + k;
	else if (st == 3)
		self.frame = 72 + d * 4 + k;
	else if (st == 4)
		self.frame = 104 + d * 4 + k;
	else if (st == 5)
		self.frame = 136 + d * 4 + k;
	else if (st == 6)
		self.frame = 168 + d * 4 + k;
	else
		self.frame = 200 + d * 4 + k;

	return TRUE;
};

void(float rad, float dmg) David_JackpotBlast =
{
	local entity e;
	local vector dir;

	if (self.dv_harmless)
		return;

	e = findradius(self.origin, rad);
	while (e)
	{
		if (e != self && e.takedamage && e.health > 0 && e.classname != "monster_david" && e.classname != "monster_preg_runner")
		{
			T_Damage(e, self, self, dmg);
			dir = normalize((e.origin + '0 0 16') - self.origin);
			e.velocity = e.velocity + dir * 240 + '0 0 135';
			if (e.flags & FL_ONGROUND)
				e.flags = e.flags - FL_ONGROUND;
		}
		e = e.chain;
	}
};

void(entity attacker, float take) David_Pain =
{
	if (self.health <= 0 || self.npc_dead)
		return;
	if (time < self.dv_phase_end)
		return;
	// Getting shot makes David clutch his money bag & turbo-bolt!
	self.dv_state = 4;
	self.dv_phase_end = time + 1.4;
	sound(self, CHAN_VOICE, "david/sprint_rush.wav", 1, ATTN_NORM);
};

void() David_Touch;
void() PregRunner_Touch;

void() David_Respawn =
{
	setorigin(self, self.dv_home + '0 0 12');
	setmodel(self, "progs/david.spr32");
	self.scale = 0.6935;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 180;
	self.max_health = 180;
	self.takedamage = DAMAGE_AIM;
	self.effects = 0;
	self.alpha = 1;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	self.dv_state = 4;
	self.dv_phase_end = time + 2.2;
	self.dv_next_act = time + 4.5;
	setsize(self, '-20 -20 0', '20 20 56');
	droptofloor();
	self.touch = David_Touch;		// Killed set SUB_Null
	self.think = David_Think;
	self.nextthink = time + 0.05;
};

void() David_Touch =
{
	local vector dir;

	if (self.dv_harmless || self.npc_dead || self.health <= 0)
		return;
	if (other == world || !other.takedamage || other.health <= 0)
		return;
	if (other.classname == "monster_david" || other.classname == "monster_preg_runner")
		return;
	if (time < self.dv_next_touch)
		return;
	self.dv_next_touch = time + 0.42;

	T_Damage(other, self, self, 15);
	dir = normalize((other.origin + '0 0 16') - self.origin);
	other.velocity = other.velocity + dir * 220 + '0 0 110';
	if (other.flags & FL_ONGROUND)
		other.flags = other.flags - FL_ONGROUND;
};

void() David_DeathStep =
{
	self.npc_dstep = self.npc_dstep + 1;
	if (self.npc_dstep <= 5)
	{
		self.think = David_DeathStep;
		self.nextthink = time + 0.075;
		return;
	}
	if (self.npc_dstep == 6)
	{
		self.think = David_DeathStep;
		self.nextthink = time + 2.2;
		return;
	}
	if (self.npc_dstep <= 13)
	{
		self.alpha = 1.0 - (self.npc_dstep - 6) * 0.13;
		self.think = David_DeathStep;
		self.nextthink = time + 0.07;
		return;
	}
	self.alpha = 1;
	if (self.dv_respawn > 0)
	{
		setmodel(self, "");
		self.think = David_Respawn;
		self.nextthink = time + self.dv_respawn;
		return;
	}
	remove(self);
};

void() David_Die =
{
	if (self.npc_dead)
		return;
	self.npc_dead = TRUE;
	self.npc_dstep = 0;
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.effects = 0;

	if (NPC_ShouldGib(self))
	{
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
		if (self.dv_respawn > 0)
		{
			setmodel(self, "");
			self.think = David_Respawn;
			self.nextthink = time + self.dv_respawn;
			return;
		}
		remove(self);
		return;
	}

	self.alpha = 1;
	sound(self, CHAN_VOICE, "david/slot_bust.wav", 1, ATTN_NORM);
	self.think = David_DeathStep;
	self.nextthink = time + 0.075;
};

void() David_Think =
{
	local entity e, best, chaser;
	local float bestd, d, want, diff, step_dist;

	if (self.health <= 0)
	{
		David_Die();
		return;
	}

	if (bm_cvar_dv_stay > 0 || self.dv_slot_only)
	{
		if (cvar("dv_spin") != 0)
		{
			self.angles_y = self.angles_y + cvar("dv_spin");
			while (self.angles_y >= 360)
				self.angles_y = self.angles_y - 360;
			while (self.angles_y < 0)
				self.angles_y = self.angles_y + 360;
		}
		if (self.dv_slot_only && time >= self.dv_phase_end)
		{
			if (self.dv_state == 5)
			{
				self.dv_alt = 1 - self.dv_alt;
				if (self.dv_alt)
				{
					self.dv_state = 6;	// 7-7-7 JACKPOT!
					self.effects = DV_EF_GOLD;
					sound(self, CHAN_AUTO, "david/slot_jackpot.wav", 1, ATTN_NORM);
				}
				else
				{
					self.dv_state = 7;	// BUST / TILT!
					self.effects = DV_EF_RED;
					sound(self, CHAN_AUTO, "david/slot_bust.wav", 1, ATTN_NORM);
				}
				self.dv_phase_end = time + 2.0;
			}
			else
			{
				self.effects = 0;
				self.dv_state = 5;		// Back to pulling lever & spinning reels!
				sound(self, CHAN_AUTO, "david/slot_spin.wav", 0.95, ATTN_NORM);
				self.dv_phase_end = time + 1.8;
			}
		}
		self.think = David_Think;
		self.nextthink = time + 0.05;
		return;
	}

	// Handle active Stationary Slot Machine / Money Bag Flex phase before resuming hyper-sprint!
	if (self.dv_state == 5 && time >= self.dv_phase_end)
	{
		self.dv_alt = 1 - self.dv_alt;
		if (self.dv_alt)
		{
			self.dv_state = 6;	// 7-7-7 JACKPOT!
			self.effects = DV_EF_GOLD;
			sound(self, CHAN_AUTO, "david/slot_jackpot.wav", 1, ATTN_NORM);
			David_JackpotBlast(165, 18);
		}
		else
		{
			self.dv_state = 7;	// BUST!
			self.effects = DV_EF_RED;
			sound(self, CHAN_AUTO, "david/slot_bust.wav", 1, ATTN_NORM);
		}
		self.dv_phase_end = time + 1.45;
		self.think = David_Think;
		self.nextthink = time + 0.05;
		return;
	}
	if ((self.dv_state == 6 || self.dv_state == 7 || self.dv_state == 3) && time >= self.dv_phase_end)
	{
		self.effects = 0;
		// Grab the bag of money and sprint fast!
		self.dv_state = 4;
		self.dv_phase_end = time + 2.4;
		sound(self, CHAN_VOICE, "david/money_bag.wav", 1, ATTN_NORM);
	}

	if (self.dv_state == 3 || self.dv_state == 5 || self.dv_state == 6 || self.dv_state == 7)
	{
		self.think = David_Think;
		self.nextthink = time + 0.05;
		return;
	}

	// Periodically trigger Slot Machine Spin or Money-Bag Flex!
	if (time > self.dv_next_act)
	{
		if (random() < 0.58)
		{
			self.dv_state = 5;	// Stop & play Slot Machine!
			self.dv_phase_end = time + 1.45;
			sound(self, CHAN_AUTO, "david/slot_spin.wav", 1, ATTN_NORM);
		}
		else
		{
			self.dv_state = 3;	// Hold & flex Bag of Money!
			self.dv_phase_end = time + 1.35;
			sound(self, CHAN_AUTO, "david/money_bag.wav", 1, ATTN_NORM);
		}
		self.dv_next_act = time + 6.5 + random() * 3.0;
		self.think = David_Think;
		self.nextthink = time + 0.05;
		return;
	}

	// Check if any Pregnant Runner is chasing David — if close, bolt away fast; else charge nearest player!
	chaser = self.dv_chased;
	if ((chaser == world || chaser.health <= 0 || chaser.classname != "monster_preg_runner") && time >= self.dv_scan_t)
	{
		self.dv_scan_t = time + 0.5;
		chaser = find(world, classname, "monster_preg_runner");
		self.dv_chased = chaser;
	}
	else if (chaser != world && (chaser.health <= 0 || chaser.classname != "monster_preg_runner"))
		chaser = world;
	best = world;
	bestd = 1600;
	e = bm_player_head;		// only players count: the frame's player list, not a 1600-unit findradius 20 times a second
	while (e)
	{
		if (e != self && e.health > 0 && e.takedamage && (e.flags & FL_CLIENT))
		{
			d = vlen(e.origin - self.origin);
			if (d < bestd)
			{
				bestd = d;
				best = e;
			}
		}
		e = e.bm_player_next;
	}

	if (self.dv_harmless)
	{
		if (self.dv_respawn > 0 && vlen(self.origin - self.dv_home) > 520)
			want = vectoyaw(self.dv_home - self.origin) + (random() - 0.5) * 42;
		else if (chaser != world && vlen(chaser.origin - self.origin) < 225)
			want = vectoyaw(self.origin - chaser.origin) + (random() - 0.5) * 55;
		else
			want = self.angles_y + (random() - 0.5) * 32;
	}
	else if (chaser != world && vlen(chaser.origin - self.origin) < 210)
	{
		// Evade chasing pregnant runners at hyper-speed!
		want = vectoyaw(self.origin - chaser.origin) + (random() - 0.5) * 50;
	}
	else if (best != world)
		want = vectoyaw(best.origin - self.origin);
	else
		want = self.angles_y + (random() - 0.5) * 28;

	diff = want - self.angles_y;
	while (diff > 180)
		diff = diff - 360;
	while (diff < -180)
		diff = diff + 360;
	self.angles_y = self.angles_y + diff * 0.32;

	if (time >= self.dv_phase_end)
	{
		if (random() < 0.45)
			self.dv_state = 2;	// Turbo Speed-Burst!
		else if (random() < 0.5)
			self.dv_state = 4;	// Running w/ Money Bag!
		else
			self.dv_state = 1;	// Fast Run!
		self.dv_phase_end = time + 1.6;
	}

	if (time > self.dv_next_voice)
	{
		if (random() < 0.45)
			sound(self, CHAN_VOICE, "david/shower_love.wav", 0.95, ATTN_NORM);
		else
			sound(self, CHAN_VOICE, "david/sprint_rush.wav", 0.90, ATTN_NORM);
		self.dv_next_voice = time + 5.5 + random() * 2.5;
	}

	// David Ojeda RUNS FAST (13.5 units per 0.05s = 270 u/s, nearly double standard monsters; bounces off walls cleanly!)
	step_dist = 13.5;
	if (self.dv_state == 2)
		step_dist = 15.5;
	if (!walkmove(self.angles_y, step_dist))
	{
		self.angles_y = self.angles_y + 115 + random() * 90;
		while (self.angles_y >= 360)
			self.angles_y = self.angles_y - 360;
		walkmove(self.angles_y, step_dist * 0.8);
	}

	self.think = David_Think;
	self.nextthink = time + 0.05;
};

// ---------------------------------------------------------------- 3 Running Pregnant Hispanic Women
float() PregRunner_Customize =
{
	local float rel, d, k;
	local vector delta;

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 28');
	rel = vectoyaw(delta) - self.angles_y;
	rel = rel - 360 * floor(rel / 360);
	d = floor(rel / 45 + 0.5);
	if (d >= 8)
		d = 0;

	if (self.npc_dead)
	{
		k = floor(self.npc_dstep * 0.67);
		if (k < 0)
			k = 0;
		if (k > 3)
			k = 3;
		self.frame = 56 + d * 4 + k;
		return TRUE;
	}

	if (bm_cvar_dv_stay > 0)
	{
		self.frame = d;
		return TRUE;
	}

	k = floor(time * 15 + self.origin_x * 0.04 + self.origin_y * 0.03);
	k = k - 6 * floor(k / 6);
	self.frame = 8 + d * 6 + k;
	return TRUE;
};

void() PregRunner_Respawn =
{
	setorigin(self, self.dv_home + '0 0 12');
	if (self.dv_runner_idx == 1)
		setmodel(self, "progs/preg_1.spr32");
	else if (self.dv_runner_idx == 2)
		setmodel(self, "progs/preg_2.spr32");
	else
		setmodel(self, "progs/preg_3.spr32");
	self.scale = 0.4800;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 120;
	self.max_health = 120;
	self.takedamage = DAMAGE_AIM;
	self.alpha = 1;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	setsize(self, '-18 -18 0', '18 18 56');
	droptofloor();
	self.touch = PregRunner_Touch;	// Killed set SUB_Null: a respawned runner who caught David no longer made him bolt
	self.think = PregRunner_Think;
	self.nextthink = time + 0.05;
};

void(entity attacker, float take) PregRunner_Pain =
{
};

void() PregRunner_Touch =
{
	if (self.npc_dead || self.health <= 0)
		return;
	if (other == world || !other.takedamage || other.health <= 0)
		return;
	if (other.classname == "monster_preg_runner")
		return;
	if (time < self.dv_next_touch)
		return;
	self.dv_next_touch = time + 0.50;
	if (other.classname == "monster_david")
	{
		// Force David to bolt when caught!
		other.dv_state = 2;
		other.dv_phase_end = time + 1.5;
		return;
	}
	if (self.dv_harmless)
		return;
	T_Damage(other, self, self, 12);
};

void() PregRunner_DeathStep =
{
	self.npc_dstep = self.npc_dstep + 1;
	if (self.npc_dstep <= 5)
	{
		self.think = PregRunner_DeathStep;
		self.nextthink = time + 0.075;
		return;
	}
	if (self.npc_dstep == 6)
	{
		self.think = PregRunner_DeathStep;
		self.nextthink = time + 2.2;
		return;
	}
	if (self.npc_dstep <= 13)
	{
		self.alpha = 1.0 - (self.npc_dstep - 6) * 0.13;
		self.think = PregRunner_DeathStep;
		self.nextthink = time + 0.07;
		return;
	}
	self.alpha = 1;
	if (self.dv_respawn > 0)
	{
		setmodel(self, "");
		self.think = PregRunner_Respawn;
		self.nextthink = time + self.dv_respawn;
		return;
	}
	remove(self);
};

void() PregRunner_Die =
{
	if (self.npc_dead)
		return;
	self.npc_dead = TRUE;
	self.npc_dstep = 0;
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.effects = 0;

	if (NPC_ShouldGib(self))
	{
		sound(self, CHAN_VOICE, "player/udeath.wav", 1, ATTN_NORM);
		ThrowGib("progs/gib1.mdl", -70);
		ThrowGib("progs/gib2.mdl", -80);
		ThrowGib("progs/gib3.mdl", -85);
		if (self.dv_respawn > 0)
		{
			setmodel(self, "");
			self.think = PregRunner_Respawn;
			self.nextthink = time + self.dv_respawn;
			return;
		}
		remove(self);
		return;
	}

	self.alpha = 1;
	sound(self, CHAN_VOICE, "player/pain4.wav", 1, ATTN_NORM);
	self.think = PregRunner_DeathStep;
	self.nextthink = time + 0.075;
};

void() PregRunner_Think =
{
	local entity targ, p;
	local float want, diff;

	if (self.health <= 0)
	{
		PregRunner_Die();
		return;
	}

	if (bm_cvar_dv_stay > 0)
	{
		if (cvar("dv_spin") != 0)
			self.angles_y = self.angles_y + cvar("dv_spin");
		self.think = PregRunner_Think;
		self.nextthink = time + 0.05;
		return;
	}

	targ = self.dv_chased;
	if (targ == world || targ.health <= 0 || targ.classname != "monster_david")
	{
		if (time >= self.dv_scan_t)
		{
			self.dv_scan_t = time + 0.5;
			targ = find(world, classname, "monster_david");
			self.dv_chased = targ;
		}
		else
			targ = world;
	}
	if (targ == world && !self.dv_harmless)
	{
		p = bm_player_head;
		while (p)
		{
			if (p != self && p.health > 0 && p.takedamage && (targ == world || vlen(p.origin - self.origin) < vlen(targ.origin - self.origin)))
				targ = p;
			p = p.bm_player_next;
		}
	}

	if (targ != world && targ.health > 0)
	{
		want = vectoyaw(targ.origin - self.origin);
		diff = want - self.angles_y;
		while (diff > 180)
			diff = diff - 360;
		while (diff < -180)
			diff = diff + 360;
		self.angles_y = self.angles_y + diff * 0.28;
	}
	else if (self.dv_harmless && self.dv_respawn > 0 && vlen(self.origin - self.dv_home) > 220)
	{
		want = vectoyaw(self.dv_home - self.origin);
		diff = want - self.angles_y;
		while (diff > 180)
			diff = diff - 360;
		while (diff < -180)
			diff = diff + 360;
		self.angles_y = self.angles_y + diff * 0.22;
	}

	if (!walkmove(self.angles_y, 11.2))
	{
		self.angles_y = self.angles_y + 95 + random() * 80;
		walkmove(self.angles_y, 9.0);
	}

	self.think = PregRunner_Think;
	self.nextthink = time + 0.05;
};

entity(vector pos, float yaw_ang, float slot_mode) David_SpawnOne =
{
	local entity old, b;

	David_Precache();
	old = self;
	b = spawn();
	b.classname = "monster_david";
	b.origin = pos;
	setmodel(b, "progs/david.spr32");
	b.scale = 0.6935;
	b.solid = SOLID_SLIDEBOX;
	b.movetype = MOVETYPE_STEP;
	b.health = 180;
	b.max_health = 180;
	b.takedamage = DAMAGE_AIM;
	b.th_stand = David_Think;
	b.th_walk = David_Think;
	b.th_run = David_Think;
	b.th_melee = David_Think;
	b.th_missile = David_Think;
	b.th_pain = David_Pain;
	b.th_die = David_Die;
	b.touch = David_Touch;
	b.customizeentityforclient = David_Customize;
	b.dv_slot_only = slot_mode;
	if (slot_mode)
	{
		b.dv_state = 5;
		b.dv_phase_end = time + 1.8;
	}
	else
	{
		b.dv_state = 4;		// Starts sprinting fast holding his bag of money!
		b.dv_phase_end = time + 2.2;
		b.dv_next_act = time + 4.2;
	}
	b.dv_next_voice = time + 3.0;
	b.flags = FL_MONSTER;
	b.angles_y = yaw_ang;
	while (b.angles_y >= 360)
		b.angles_y = b.angles_y - 360;
	setsize(b, '-20 -20 0', '20 20 56');
	self = b;
	droptofloor();
	self = old;
	b.think = David_Think;
	b.nextthink = time + 0.05;
	return b;
};

entity(float idx, vector pos, float yaw_ang, entity target_dv) PregRunner_SpawnOne =
{
	local entity old, w;

	David_Precache();
	old = self;
	w = spawn();
	w.classname = "monster_preg_runner";
	w.origin = pos;
	if (idx == 1)
		setmodel(w, "progs/preg_1.spr32");
	else if (idx == 2)
		setmodel(w, "progs/preg_2.spr32");
	else
		setmodel(w, "progs/preg_3.spr32");
	w.scale = 0.4800;
	w.dv_runner_idx = idx;
	w.solid = SOLID_SLIDEBOX;
	w.movetype = MOVETYPE_STEP;
	w.health = 120;
	w.max_health = 120;
	w.takedamage = DAMAGE_AIM;
	w.th_stand = PregRunner_Think;
	w.th_walk = PregRunner_Think;
	w.th_run = PregRunner_Think;
	w.th_melee = PregRunner_Think;
	w.th_missile = PregRunner_Think;
	w.th_pain = PregRunner_Pain;
	w.th_die = PregRunner_Die;
	w.touch = PregRunner_Touch;
	w.customizeentityforclient = PregRunner_Customize;
	w.dv_chased = target_dv;
	w.flags = FL_MONSTER;
	w.angles_y = yaw_ang;
	while (w.angles_y >= 360)
		w.angles_y = w.angles_y - 360;
	setsize(w, '-18 -18 0', '18 18 56');
	self = w;
	droptofloor();
	self = old;
	w.think = PregRunner_Think;
	w.nextthink = time + 0.05;
	return w;
};

void() David_Summon =
{
	local vector flat_ang;
	local entity dv;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	dv = David_SpawnOne(self.origin + v_forward * 132 + '0 0 24', self.v_angle_y + 180, FALSE);
	sound(dv, CHAN_VOICE, "david/shower_love.wav", 1, ATTN_NORM);
};

void() David_SummonSlot =
{
	local vector flat_ang;
	local entity dv;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	dv = David_SpawnOne(self.origin + v_forward * 138 + '0 0 24', self.v_angle_y + 180, TRUE);
	sound(dv, CHAN_VOICE, "david/slot_spin.wav", 1, ATTN_NORM);
};

void() PregRunners_Summon =
{
	local vector flat_ang;
	local entity dv;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	dv = find(world, classname, "monster_david");
	PregRunner_SpawnOne(1, self.origin + v_forward * 138 - v_right * 56 + '0 0 24', self.v_angle_y + 180, dv);
	PregRunner_SpawnOne(2, self.origin + v_forward * 154 + '0 0 24', self.v_angle_y + 180, dv);
	PregRunner_SpawnOne(3, self.origin + v_forward * 138 + v_right * 56 + '0 0 24', self.v_angle_y + 180, dv);
};

void() David_SummonSquad =
{
	local vector flat_ang;
	local entity dv;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	dv = David_SpawnOne(self.origin + v_forward * 118 + '0 0 24', self.v_angle_y + 180, FALSE);
	PregRunner_SpawnOne(1, self.origin + v_forward * 195 - v_right * 62 + '0 0 24', self.v_angle_y + 180, dv);
	PregRunner_SpawnOne(2, self.origin + v_forward * 212 + '0 0 24', self.v_angle_y + 180, dv);
	PregRunner_SpawnOne(3, self.origin + v_forward * 195 + v_right * 62 + '0 0 24', self.v_angle_y + 180, dv);
	sound(dv, CHAN_VOICE, "david/shower_love.wav", 1, ATTN_NORM);
};

// Map-placeable harmless & shootable squad: David Ojeda fleeing all 3 Running Pregnant Women!
void() npc_david_squad =
{
	local vector flat_ang;
	local entity dv, w1, w2, w3;
	if (BM_NoMapNPC ())		// no map NPCs unless bm_npcs 1 (2026-11-26)
	{
		remove (self);
		return;
	}

	David_Precache();
	flat_ang = '0 0 0';
	flat_ang_y = self.angles_y;
	makevectors(flat_ang);

	dv = David_SpawnOne(self.origin + '0 0 16', self.angles_y, FALSE);
	dv.flags = dv.flags - (dv.flags & FL_MONSTER);
	dv.dv_harmless = TRUE;
	dv.dv_respawn = 25;
	dv.dv_home = dv.origin;

	w1 = PregRunner_SpawnOne(1, self.origin - v_forward * 78 - v_right * 48 + '0 0 16', self.angles_y, dv);
	w1.flags = w1.flags - (w1.flags & FL_MONSTER);
	w1.dv_harmless = TRUE;
	w1.dv_respawn = 25;
	w1.dv_home = w1.origin;

	w2 = PregRunner_SpawnOne(2, self.origin - v_forward * 96 + '0 0 16', self.angles_y, dv);
	w2.flags = w2.flags - (w2.flags & FL_MONSTER);
	w2.dv_harmless = TRUE;
	w2.dv_respawn = 25;
	w2.dv_home = w2.origin;

	w3 = PregRunner_SpawnOne(3, self.origin - v_forward * 78 + v_right * 48 + '0 0 16', self.angles_y, dv);
	w3.flags = w3.flags - (w3.flags & FL_MONSTER);
	w3.dv_harmless = TRUE;
	w3.dv_respawn = 25;
	w3.dv_home = w3.origin;

	remove(self);
};
