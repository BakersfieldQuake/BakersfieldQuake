#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
Tinfoil-Hat Bryan & His Demons (bryan.qc).
Impulse 19 summons Bryan in front of you on progs/bryan.spr32
(built by source/mm_tools/bryan/build_bryan_sprites.py).

Full 360° 8-Direction Frame Layout (200 frames, 120x108, origin (-60, 99), scale 0.8535):
  0..7               8-direction Solo Bryan standing idle keypose (d = 0..7, NO demons)
  8 + d*6 + k        8-direction Solo Bryan 360° Running Cycle (d = 0..7, k = 0..5, NO demons) [mbox.qc compatible]
  56 + d*4 + k       8-direction Solo Bryan Paranoid RGB Detector Scan (d = 0..7, k = 0..3, NO demons)
  88 + d*4 + k       8-direction "A DEMON! NO WAY!" 3D Giant-Swing Demon-Whirl Attack (d = 0..7, k = 0..3)
  120 + d*4 + k      8-direction 3-Demon Trio EMF Overload Surge (d = 0..7, k = 0..3)
  152..167           16-frame 4-Act Hell Portal Drag-Down Death -> Smoking Tinfoil Hat & Broken Detector!
  168 + d*4 + k      8-direction Falling Collapse Death (d = 0..7, k = 0..3)

Optional console cvars for inspection:
  br_mode 0..4       0 = autonomous AI (default), 1 = Scan, 2 = Sprint, 3 = Demon-Whirl, 4 = Demon-Trio Surge
  br_stay 0/1        1 = hold position in place so players can walk 360° around Bryan freely
*/

float	BR_EF_BLUE	= 64;		// DarkPlaces blue dynamic light
float	BR_EF_RED	= 128;		// DarkPlaces red dynamic light

.float	br_state;		// 0 = scan, 1 = sprint, 2 = demon-whirl, 3 = demon-trio surge
.float	br_special_end;
.float	br_next_special;
.float	br_next_voice;
.float	br_next_touch;
.float	br_dstep;
.float	br_alt;

.entity	br_target;		// the one he faces / goes for (Bryan_Think, rescanned every 0.25 s)
.float	br_scan_t;
void() Bryan_Die;
void() Bryan_Think;
void(entity attacker, float take) Bryan_Pain;

void() Bryan_Precache =
{
	if (bryan_precached)
		return;
	bryan_precached = TRUE;
	precache_model("progs/bryan.spr32");
	precache_model("progs/gib1.mdl");
	precache_model("progs/gib2.mdl");
	precache_model("progs/gib3.mdl");
	precache_sound("bryan/sense.wav");
	precache_sound("bryan/detector.wav");
	precache_sound("bryan/noway.wav");
	precache_sound("bryan/whirl.wav");
	precache_sound("bryan/slash.wav");
	precache_sound("bryan/portal_die.wav");
	precache_sound("weapons/r_exp3.wav");
	precache_sound("weapons/lstart.wav");
};

float() Bryan_Customize =
{
	local float rel, d, k, st, m;
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
		self.frame = 168 + d * 4 + k;
		return TRUE;
	}

	st = self.br_state;
	m = bm_cvar_br_mode;
	if (m >= 1 && m <= 4)
		st = m - 1;

	if (st == 3)
	{
		k = floor(time * 6 + self.origin_y * 0.015);
		k = k - 4 * floor(k / 4);
		self.frame = 120 + d * 4 + k;
		return TRUE;
	}
	if (st == 2)
	{
		k = floor(time * 7 + self.origin_x * 0.015);
		k = k - 4 * floor(k / 4);
		self.frame = 88 + d * 4 + k;
		return TRUE;
	}
	if (st == 1)
	{
		k = floor(time * 12 + self.origin_x * 0.04);
		k = k - 6 * floor(k / 6);
		self.frame = 8 + d * 6 + k;
		return TRUE;
	}

	k = floor(time * 5.5 + self.origin_y * 0.015);
	k = k - 4 * floor(k / 4);
	self.frame = 56 + d * 4 + k;
	return TRUE;
};

void(entity attacker, float take) Bryan_Pain =
{
	if (self.health <= 0 || self.npc_dead)
		return;
	if (time < self.br_special_end)
		return;
	self.br_state = 3;
	self.br_special_end = time + 1.15;
	self.effects = self.effects | BR_EF_BLUE;
	sound(self, CHAN_VOICE, "bryan/noway.wav", 1, ATTN_NORM);
	sound(self, CHAN_AUTO, "bryan/slash.wav", 0.85, ATTN_NORM);
};

void() Bryan_Touch =
{
	local vector dir;

	if (self.npc_dead || self.health <= 0)
		return;
	if (other == world || !other.takedamage || other.health <= 0)
		return;
	if (other.classname == "monster_bryan")
		return;
	if (time < self.br_next_touch)
		return;
	self.br_next_touch = time + 0.48;

	if (self.br_state == 2 || self.br_state == 3)
	{
		T_Damage(other, self, self, 22);
		dir = normalize((other.origin + '0 0 16') - self.origin);
		other.velocity = other.velocity + dir * 260 + '0 0 140';
		if (other.flags & FL_ONGROUND)
			other.flags = other.flags - FL_ONGROUND;
	}
	else
		T_Damage(other, self, self, 14);
};

void() Bryan_TestCamLock =
{
	local entity p;
	local vector aim;

	if (cvar("br_camlock") <= 0)
		return;
	p = find(world, classname, "player");
	if (p != world)
	{
		aim = vectoangles((self.origin + '0 0 26') - (p.origin + p.view_ofs));
		aim_x = -aim_x;
		aim_z = 0;
		p.angles = aim;
		p.v_angle = aim;
		p.fixangle = TRUE;
	}
};

void() Bryan_DieLoop =
{
	Bryan_TestCamLock();
	self.br_dstep = self.br_dstep + 1;
	if (self.br_dstep >= 32)
	{
		self.effects = 0;
		self.frame = 167;	// Smoking silver tinfoil hat & broken Demon Detector on floor!
		self.think = SUB_Remove;
		self.nextthink = time + 5.0;
		return;
	}
	self.frame = 152 + floor(self.br_dstep * 0.5);

	// Act 2: Demon Trio erupts from molten pentagram portal!
	if (self.br_dstep == 8)
	{
		self.effects = BR_EF_RED;
		sound(self, CHAN_ITEM, "weapons/lstart.wav", 1, ATTN_NORM);
	}

	// Act 3: Dragged down into roaring hellfire!
	if (self.br_dstep == 16)
		sound(self, CHAN_AUTO, "bryan/noway.wav", 1, ATTN_NORM);

	// Act 4: Hellfire shockwave detonation + Quake 3D gibs!
	if (self.br_dstep == 24)
	{
		self.effects = 0;
		sound(self, CHAN_BODY, "weapons/r_exp3.wav", 1, ATTN_NORM);
		ThrowGib("progs/gib1.mdl", -70);
		ThrowGib("progs/gib2.mdl", -85);
		ThrowGib("progs/gib3.mdl", -95);
	}

	self.think = Bryan_DieLoop;
	self.nextthink = time + 0.065;
};

void() Bryan_FallStep =
{
	Bryan_TestCamLock();
	self.npc_dstep = self.npc_dstep + 1;
	if (self.npc_dstep <= 5)
	{
		self.think = Bryan_FallStep;
		self.nextthink = time + 0.075;
		return;
	}
	if (self.npc_dstep == 6)
	{
		self.think = Bryan_FallStep;
		self.nextthink = time + 2.2;
		return;
	}
	if (self.npc_dstep <= 13)
	{
		self.alpha = 1.0 - (self.npc_dstep - 6) * 0.13;
		self.think = Bryan_FallStep;
		self.nextthink = time + 0.07;
		return;
	}
	remove(self);
};

float() Bryan_ShowAll =
{
	return TRUE;
};

void() Bryan_Die =
{
	if (self.npc_dead)
		return;
	self.npc_dead = TRUE;
	self.npc_dstep = 0;
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.br_state = 0;

	if (NPC_ShouldGib(self))
	{
		self.customizeentityforclient = Bryan_ShowAll;		// was SUB_Null: a void customize function returns 0 (= not sent), so nobody saw the portal death
		self.br_dstep = 0;
		self.frame = 152;
		self.effects = BR_EF_BLUE;
		sound(self, CHAN_VOICE, "bryan/portal_die.wav", 1, ATTN_NORM);
		self.think = Bryan_DieLoop;
		self.nextthink = time + 0.065;
		return;
	}

	self.effects = 0;
	self.alpha = 1;
	sound(self, CHAN_VOICE, "bryan/noway.wav", 1, ATTN_NORM);
	self.think = Bryan_FallStep;
	self.nextthink = time + 0.075;
};

void(float rad, float dmg) Bryan_DemonPulse =
{
	local entity e;
	local vector dir;

	e = findradius(self.origin, rad);
	while (e)
	{
		if (e != self && e.takedamage && e.health > 0 && e.classname != "monster_bryan")
		{
			T_Damage(e, self, self, dmg);
			dir = normalize((e.origin + '0 0 16') - self.origin);
			e.velocity = e.velocity + dir * 210 + '0 0 110';
			if (e.flags & FL_ONGROUND)
				e.flags = e.flags - FL_ONGROUND;
		}
		e = e.chain;
	}
};

void() Bryan_Think =
{
	local entity e, best;
	local float bestd, d, want, diff;

	if (self.health <= 0)
	{
		Bryan_Die();
		return;
	}
	Bryan_TestCamLock();

	if (time >= self.br_special_end)
		self.effects = 0;

	if (cvar("br_stay") > 0)
	{
		if (cvar("br_spin") != 0)
		{
			self.angles_y = self.angles_y + cvar("br_spin");
			while (self.angles_y >= 360)
				self.angles_y = self.angles_y - 360;
			while (self.angles_y < 0)
				self.angles_y = self.angles_y + 360;
		}
		if (time >= self.br_special_end)
			self.br_state = 0;
		if (time > self.br_next_voice)
		{
			sound(self, CHAN_VOICE, "bryan/detector.wav", 0.9, ATTN_NORM);
			self.br_next_voice = time + 6.5;
		}
		self.think = Bryan_Think;
		self.nextthink = time + 0.05;
		return;
	}

	// the nearest player or monster: a 1400-unit findradius 4 times a second, not 20 (kept in br_target in between;
	// the distance is taken fresh every think)
	best = self.br_target;
	if (best != world && (best.health <= 0 || !best.takedamage))
		best = world;
	bestd = 1400;
	if (best != world)
	{
		bestd = vlen(best.origin - self.origin);
		if (bestd >= 1400)
		{
			best = world;
			bestd = 1400;
		}
	}
	e = world;
	if (time >= self.br_scan_t)
	{
		self.br_scan_t = time + 0.25;
		best = world;
		bestd = 1400;
		e = findradius(self.origin, 1400);
	}
	while (e)
	{
		if (e != self && e.health > 0 && e.takedamage &&
		    ((e.flags & FL_CLIENT) || ((e.flags & FL_MONSTER) && e.classname != "monster_bryan")))
		{
			d = vlen(e.origin - self.origin);
			if (d < bestd)
			{
				bestd = d;
				best = e;
			}
		}
		e = e.chain;
	}
	self.br_target = best;

	if (best != world)
	{
		want = vectoyaw(best.origin - self.origin);
		diff = want - self.angles_y;
		while (diff > 180)
			diff = diff - 360;
		while (diff < -180)
			diff = diff + 360;
		self.angles_y = self.angles_y + diff * 0.25;

		// Close-quarters Demon-Whirl or Mid-range Demon-Trio EMF Surge!
		if (bestd < 135 && time > self.br_next_special)
		{
			self.br_alt = 1 - self.br_alt;
			if (self.br_alt)
			{
				self.br_state = 2;	// 360° "A DEMON! NO WAY!" Giant-Swing Demon-Whirl!
				self.br_special_end = time + 1.45;
				self.br_next_special = time + 3.2;
				self.effects = BR_EF_RED;
				sound(self, CHAN_VOICE, "bryan/whirl.wav", 1, ATTN_NORM);
				Bryan_DemonPulse(145, 18);
			}
			else
			{
				self.br_state = 3;	// 360° 3-Demon Trio EMF Overload Surge!
				self.br_special_end = time + 1.35;
				self.br_next_special = time + 3.4;
				self.effects = BR_EF_BLUE;
				sound(self, CHAN_VOICE, "bryan/slash.wav", 1, ATTN_NORM);
				Bryan_DemonPulse(160, 16);
			}
		}
		else if (time >= self.br_special_end)
		{
			if (self.br_state == 0 && time > self.br_next_voice)
			{
				sound(self, CHAN_VOICE, "bryan/noway.wav", 1, ATTN_NORM);
				self.br_next_voice = time + 4.8;
			}
			else if (time > self.br_next_voice)
			{
				if (random() < 0.5)
					sound(self, CHAN_VOICE, "bryan/detector.wav", 0.9, ATTN_NORM);
				else
					sound(self, CHAN_VOICE, "bryan/noway.wav", 0.9, ATTN_NORM);
				self.br_next_voice = time + 6.0;
			}
			self.br_state = 1;
		}

		walkmove(self.angles_y, 7.2);
	}
	else
	{
		if (time >= self.br_special_end)
			self.br_state = 0;
	}

	self.think = Bryan_Think;
	self.nextthink = time + 0.05;
};

void() Bryan_Summon =
{
	local entity old, b;
	local vector flat_ang;

	Bryan_Precache();
	old = self;
	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	b = spawn();
	b.classname = "monster_bryan";
	b.origin = old.origin + v_forward * 124 + '0 0 24';
	setmodel(b, "progs/bryan.spr32");
	b.scale = 0.8535;
	b.solid = SOLID_SLIDEBOX;
	b.movetype = MOVETYPE_STEP;
	b.health = 160;
	b.max_health = 160;
	b.takedamage = DAMAGE_AIM;
	b.th_stand = Bryan_Think;
	b.th_walk = Bryan_Think;
	b.th_run = Bryan_Think;
	b.th_melee = Bryan_Think;
	b.th_missile = Bryan_Think;
	b.th_pain = Bryan_Pain;
	b.th_die = Bryan_Die;
	b.touch = Bryan_Touch;
	b.customizeentityforclient = Bryan_Customize;
	b.think = Bryan_Think;
	b.nextthink = time + 0.1;
	b.br_next_voice = time + 3.4;
	b.br_next_special = time + 1.2;
	b.flags = FL_MONSTER;
	b.angles_y = old.v_angle_y + 180;
	while (b.angles_y >= 360)
		b.angles_y = b.angles_y - 360;
	setsize(b, '-24 -24 0', '24 24 58');
	self = b;
	droptofloor();
	self = old;
	sound(b, CHAN_VOICE, "bryan/sense.wav", 1, ATTN_NORM);
};
