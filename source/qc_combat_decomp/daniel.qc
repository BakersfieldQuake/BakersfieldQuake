#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
Daniel ("4 AM Moving the Table" / "CCC!" / "SHAAAAAAAA!" / "Justin Berry's Webcam")
& Angry 4 AM Dad (daniel.qc).

Impulses (with sv_cheats 1):
  impulse 26  Summon 4 AM Daniel (dragging the oak table) + Angry 4 AM Dad chasing him + Framed Meme Poster!
  impulse 27  Summon Solo Autonomous Daniel (cycles 4 AM Table Ram, CCC! Yellow-C Barrage, SHAAA! Sonic Rage, & Webcam Toss)
  impulse 28  Summon 360° Bakersfield LAN Station Daniel (Oak Table + 19990 Quake CRT + RGB Keyboard + QuickCam)
  impulse 29  Summon Angry 4 AM Dad ("What the fuck! It's 4 in the morning, Daniel! What is this noise?!")

Full 360° 8-Direction Frame Layout on progs/daniel.spr32 (264 frames, 96x108, origin (-48, 98), scale 0.6935):
  0..7               8-direction Standing Squint Idle (d = 0..7)
  8 + d*4 + k        8-direction Fast Running Cycle (d = 0..7, k = 0..3) [mbox.qc compatible]
  40 + d*4 + k       8-direction 4 AM Moving the Wooden Table (d = 0..7, k = 0..3)
  72 + d*4 + k       8-direction "CCC! C-C-C-C!" Rapid-Chatter Grin Barrage (d = 0..7, k = 0..3)
  104 + d*4 + k      8-direction "SHAAAAAAAAAAAA!" Neon LAN Keyboard Rage Scream (d = 0..7, k = 0..3)
  136 + d*4 + k      8-direction "Justin Berry's Webcam!" Blind Squint Scan (d = 0..7, k = 0..3)
  168 + d*4 + k      8-direction Hands-Up "Sorry! I was just moving the table!" Panic Sprint (d = 0..7, k = 0..3)
  200 + d*4 + k      8-direction 360° Bakersfield LAN Station (d = 0..7, k = 0..3)
  232 + d*4 + k      8-direction Falling Collapse Death (d = 0..7, k = 0..3)

Angry 4 AM Dad on progs/daniel_dad.spr32 (88 frames, 128x154, origin (-64, 140), scale 0.5126):
  0..7               8-direction Furious 4 AM Yelling Idle (d = 0..7)
  8 + d*6 + k        8-direction Angry 4 AM Charge Run (d = 0..7, k = 0..5) [mbox.qc compatible]
  56 + d*4 + k       8-direction Falling Collapse Death (d = 0..7, k = 0..3)

Optional console cvars for inspection:
  dn_mode 0..8       0 = autonomous AI, 1 = Idle, 2 = Fast Run, 3 = 4 AM Table Move,
                     4 = CCC! Grin Barrage, 5 = SHAAA! LAN Rage, 6 = Justin's Webcam,
                     7 = Hands-Up Sorry Panic, 8 = 360° LAN Station
  dn_stay 0/1        1 = hold position in place so players can walk 360° around freely
  dn_spin <deg>      turntable auto-spin yaw step when dn_stay 1
*/

float	DN_EF_GLOW	= 8;		// EF_DIMLIGHT warm amber glow
float	DN_EF_BLUE	= 64;		// DarkPlaces blue/cyan neon LAN dynamic light
float	DN_EF_RED	= 128;		// DarkPlaces red 4AM rage light

float	daniel_poster_seq;

.float	dn_state;		// 0=idle, 1=fast_run, 2=table_move, 3=ccc_barrage, 4=shaaa_rage, 5=webcam_squint, 6=sorry_panic, 7=lan_station
.float	dn_phase_end;
.float	dn_next_act;
.float	dn_next_shot;
.float	dn_next_voice;
.float	dn_next_touch;
.float	dn_scan_t;
.float	dn_lan_only;
.float	dn_respawn;
.vector	dn_home;
.float	dn_act_seq;
.entity	dn_chased;

void() Daniel_Think;
void() Daniel_Die;
void(entity attacker, float take) Daniel_Pain;
void() Dad4AM_Think;
void() Dad4AM_Die;
void() exploderun;

void() Daniel_Precache =
{
	if (daniel_precached)
		return;
	daniel_precached = TRUE;
	precache_model("progs/daniel.spr32");
	precache_model("progs/daniel_dad.spr32");
	precache_model("progs/daniel_table.md3");
	precache_model("progs/daniel_webcam.md3");
	precache_model("progs/daniel_poster.md3");
	precache_model("progs/ccc.md3");
	precache_model("progs/s_plasma.spr");
	precache_model("progs/gib1.mdl");
	precache_model("progs/gib2.mdl");
	precache_model("progs/gib3.mdl");
	precache_sound("daniel/dad_4am.wav");
	precache_sound("daniel/sorry_table.wav");
	precache_sound("daniel/table_drag.wav");
	precache_sound("daniel/shaaa_scream.wav");
	precache_sound("daniel/cant_see_webcam.wav");
	precache_sound("daniel/ccc_chant.wav");
	precache_sound("daniel/ccc_burst.wav");
	precache_sound("ccc/shoot.wav");
	precache_sound("floathead/boing.wav");
	precache_sound("weapons/r_exp3.wav");
	precache_sound("player/udeath.wav");
	precache_sound("player/pain6.wav");
};

// ---------------------------------------------------------------- Spinning Yellow 'C' Projectile (CCC! C-C-C-C!)
void() Daniel_CCCSpark =
{
	local entity sp;

	sp = spawn();
	setmodel(sp, "progs/s_plasma.spr");
	setorigin(sp, self.origin);
	sp.scale = 0.65;
	sp.colormod = '1 0.88 0.1';
	sp.effects = EF_ADDITIVE;
	sp.think = exploderun;
	sp.nextthink = time;
	remove(self);
};

void() Daniel_CCCTouch =
{
	if (other == self.owner)
		return;
	if (other.classname == "monster_daniel")
		return;
	if (pointcontents(self.origin) == CONTENT_SKY)
	{
		remove(self);
		return;
	}
	if (other.takedamage && other.health > 0)
	{
		if (bm_wasfreed(self.owner) || self.owner.classname != "monster_daniel")
			self.owner = world;		// Daniel was gibbed (removed) since: his edict may be someone else's by now
		T_Damage(other, self, self.owner, 9);
		Daniel_CCCSpark();
		return;
	}
	self.cnt = self.cnt + 1;
	if (self.cnt >= 3)
	{
		Daniel_CCCSpark();
		return;
	}
	sound(self, CHAN_AUTO, "floathead/boing.wav", 0.55, ATTN_NORM);
};

void(vector org, vector dir) Daniel_LaunchCCC =
{
	local entity c;

	c = spawn();
	c.owner = self;
	c.classname = "daniel_ccc";
	c.movetype = MOVETYPE_BOUNCE;
	c.solid = SOLID_BBOX;
	setmodel(c, "progs/ccc.md3");
	c.effects = EF_FULLBRIGHT;
	c.traileffectnum = particleeffectnum("ccc_trail");
	c.velocity = normalize(dir) * 860 + '0 0 95';
	c.angles = vectoangles(c.velocity);
	c.avelocity = '0 360 420';
	setsize(c, '0 0 0', '0 0 0');
	setorigin(c, org);
	c.touch = Daniel_CCCTouch;
	c.think = SUB_Remove;
	c.nextthink = time + 3.2;
};

// ---------------------------------------------------------------- Thrown 3D Props (4AM Wooden Table & Justin Berry's Webcam)
void() Daniel_PropTouch =
{
	local vector dir;

	if (other == self.owner || other.classname == "monster_daniel")
		return;
	if (other != world && other.takedamage && other.health > 0 && self.dmg > 0)
	{
		if (bm_wasfreed(self.owner) || self.owner.classname != "monster_daniel")
			self.owner = world;		// Daniel was gibbed (removed) since: his edict may be someone else's by now
		T_Damage(other, self, self.owner, self.dmg);
		dir = normalize((other.origin + '0 0 16') - self.origin);
		other.velocity = other.velocity + dir * 210 + '0 0 120';
		if (other.flags & FL_ONGROUND)
			other.flags = other.flags - FL_ONGROUND;
		self.dmg = 0;	// Deal impact damage once, then settle as a physics prop
	}
	if (vlen(self.velocity) < 55)
		self.avelocity = '0 0 0';
};

entity(string mdl, vector org, vector vel, float hit_dmg) Daniel_ThrowProp =
{
	local entity p;

	p = spawn();
	p.owner = self;
	p.classname = "daniel_prop";
	p.movetype = MOVETYPE_BOUNCE;
	p.solid = SOLID_BBOX;
	setmodel(p, mdl);
	p.velocity = vel;
	p.avelocity = '180 260 140';
	p.dmg = hit_dmg;
	setsize(p, '-12 -12 0', '12 12 20');
	setorigin(p, org);
	p.touch = Daniel_PropTouch;
	p.think = SUB_Remove;
	p.nextthink = time + 8.0;
	return p;
};

entity(vector pos, float yaw_ang, float skin_num) Daniel_SpawnPoster =
{
	local entity p;

	Daniel_Precache();
	p = spawn();
	p.classname = "prop_daniel_poster";
	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	setmodel(p, "progs/daniel_poster.md3");
	p.skin = skin_num;
	p.angles_y = yaw_ang;
	setsize(p, '0 0 0', '0 0 0');
	setorigin(p, pos);
	p.think = SUB_Remove;
	p.nextthink = time + 45.0;
	return p;
};

// Map-placeable decorative entities
void() prop_daniel_poster =
{
	Daniel_Precache();
	setmodel(self, "progs/daniel_poster.md3");
	self.movetype = MOVETYPE_NONE;
	self.solid = SOLID_NOT;
};

void() prop_daniel_table =
{
	Daniel_Precache();
	setmodel(self, "progs/daniel_table.md3");
	self.movetype = MOVETYPE_TOSS;
	self.solid = SOLID_BBOX;
	setsize(self, '-16 -12 0', '16 12 28');
	droptofloor();
};

void() prop_daniel_webcam =
{
	Daniel_Precache();
	setmodel(self, "progs/daniel_webcam.md3");
	self.movetype = MOVETYPE_TOSS;
	self.solid = SOLID_BBOX;
	setsize(self, '-6 -6 0', '6 6 12');
	droptofloor();
};

// ---------------------------------------------------------------- Full 360° 8-Direction Customize & AI
float() Daniel_Customize =
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

	st = self.dn_state;
	m = bm_cvar_dn_mode;
	if (m >= 1 && m <= 8)
		st = m - 1;

	if (st <= 0)
	{
		self.frame = d;
		return TRUE;
	}

	fps = 9.5;
	if (st == 1 || st == 3 || st == 6)
		fps = 12;	// High-cadence sprinting & rapid CCC mouth chatter!
	else if (st == 4)
		fps = 10.5;	// SHAAA sonic vibration!

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

void(float rad, float dmg) Daniel_SonicBlast =
{
	local entity e;
	local vector dir;

	e = findradius(self.origin, rad);
	while (e)
	{
		if (e != self && e.takedamage && e.health > 0 && e.classname != "monster_daniel" && e.classname != "monster_dad4am")
		{
			T_Damage(e, self, self, dmg);
			dir = normalize((e.origin + '0 0 16') - self.origin);
			e.velocity = e.velocity + dir * 280 + '0 0 155';
			if (e.flags & FL_ONGROUND)
				e.flags = e.flags - FL_ONGROUND;
		}
		e = e.chain;
	}
};

void(entity attacker, float take) Daniel_Pain =
{
	local vector flat_ang;

	if (self.health <= 0 || self.npc_dead || self.dn_lan_only)
		return;
	if (time < self.dn_phase_end && self.dn_state == 6)
		return;
	// Getting hit makes Daniel throw both hands up ("Sorry! I was just moving the table!") and drop a table!
	self.dn_state = 6;
	self.effects = 0;
	self.dn_phase_end = time + 1.8;
	sound(self, CHAN_VOICE, "daniel/sorry_table.wav", 1, ATTN_NORM);
	flat_ang = '0 0 0';
	flat_ang_y = self.angles_y;
	makevectors(flat_ang);
	Daniel_ThrowProp("progs/daniel_table.md3", self.origin + v_forward * 20 + '0 0 22', v_forward * 190 + '0 0 165', 12);
};

void() Daniel_Touch;

void() Daniel_Respawn =
{
	setorigin(self, self.dn_home + '0 0 8');
	setmodel(self, "progs/daniel.spr32");
	self.scale = 0.6935;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 185;
	self.max_health = 185;
	self.takedamage = DAMAGE_AIM;
	self.effects = 0;
	self.alpha = 1;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	if (self.dn_lan_only)
		self.dn_state = 7;
	else
		self.dn_state = 2;
	self.dn_phase_end = time + 2.4;
	setsize(self, '-20 -20 0', '20 20 56');
	droptofloor();
	self.touch = Daniel_Touch;		// Killed set SUB_Null
	self.think = Daniel_Think;
	self.nextthink = time + 0.1;
};

void() Daniel_Touch =
{
	local vector dir;

	if (self.dn_lan_only || self.npc_dead || self.health <= 0)
		return;
	if (other == world || !other.takedamage || other.health <= 0)
		return;
	if (other.classname == "monster_daniel" || other.classname == "monster_dad4am")
		return;
	if (time < self.dn_next_touch)
		return;
	self.dn_next_touch = time + 0.45;

	// Dragging the 4AM table hits harder!
	if (self.dn_state == 2)
		T_Damage(other, self, self, 18);
	else
		T_Damage(other, self, self, 12);
	dir = normalize((other.origin + '0 0 16') - self.origin);
	other.velocity = other.velocity + dir * 230 + '0 0 115';
	if (other.flags & FL_ONGROUND)
		other.flags = other.flags - FL_ONGROUND;
};

void() Daniel_DeathStep =
{
	self.npc_dstep = self.npc_dstep + 1;
	if (self.npc_dstep <= 5)
	{
		self.think = Daniel_DeathStep;
		self.nextthink = time + 0.075;
		return;
	}
	if (self.npc_dstep == 6)
	{
		self.think = Daniel_DeathStep;
		self.nextthink = time + 2.2;
		return;
	}
	if (self.npc_dstep <= 13)
	{
		self.alpha = 1.0 - (self.npc_dstep - 6) * 0.13;
		self.think = Daniel_DeathStep;
		self.nextthink = time + 0.07;
		return;
	}
	self.alpha = 1;
	if (self.dn_respawn > 0)
	{
		setmodel(self, "");
		self.think = Daniel_Respawn;
		self.nextthink = time + self.dn_respawn;
		return;
	}
	remove(self);
};

void() Daniel_Die =
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
		sound(self, CHAN_AUTO, "daniel/shaaa_scream.wav", 1, ATTN_NORM);
		sound(self, CHAN_AUTO, "weapons/r_exp3.wav", 1, ATTN_NORM);
		Daniel_ThrowProp("progs/daniel_table.md3", self.origin + '0 0 24', '90 -110 240', 0);
		Daniel_ThrowProp("progs/daniel_webcam.md3", self.origin + '0 0 32', '-120 95 270', 0);
		BM_NPCGibBurst(-85, 5);
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte(MSG_BROADCAST, TE_EXPLOSION);
		WriteCoord(MSG_BROADCAST, self.origin_x);
		WriteCoord(MSG_BROADCAST, self.origin_y);
		WriteCoord(MSG_BROADCAST, self.origin_z + 24);
		if (self.dn_respawn > 0)
		{
			setmodel(self, "");
			self.think = Daniel_Respawn;
			self.nextthink = time + self.dn_respawn;
			return;
		}
		remove(self);
		return;
	}

	self.alpha = 1;
	sound(self, CHAN_VOICE, "daniel/sorry_table.wav", 1, ATTN_NORM);
	self.think = Daniel_DeathStep;
	self.nextthink = time + 0.075;
};

void() Daniel_Think =
{
	local entity e, best, dad;
	local float bestd, d, want, diff, step_dist;
	local vector flat_ang;

	if (self.health <= 0)
	{
		Daniel_Die();
		return;
	}

	// Stationary 360° LAN Station mode or dn_stay inspection mode
	if (bm_cvar_dn_stay > 0 || self.dn_lan_only)
	{
		if (cvar("dn_spin") != 0)
		{
			self.angles_y = self.angles_y + cvar("dn_spin");
			while (self.angles_y >= 360)
				self.angles_y = self.angles_y - 360;
			while (self.angles_y < 0)
				self.angles_y = self.angles_y + 360;
		}
		if (self.dn_lan_only && time >= self.dn_phase_end)
		{
			self.dn_act_seq = self.dn_act_seq + 1;
			if (self.dn_act_seq > 3)
				self.dn_act_seq = 0;
			if (self.dn_act_seq == 1)
			{
				self.dn_state = 3;	// CCC! C-C-C-C!
				self.effects = DN_EF_GLOW;
				sound(self, CHAN_VOICE, "daniel/ccc_burst.wav", 0.95, ATTN_NORM);
				self.dn_phase_end = time + 1.8;
			}
			else if (self.dn_act_seq == 2)
			{
				self.dn_state = 4;	// SHAAAAAAAA!
				self.effects = DN_EF_BLUE;
				sound(self, CHAN_VOICE, "daniel/shaaa_scream.wav", 0.95, ATTN_NORM);
				self.dn_phase_end = time + 2.4;
			}
			else if (self.dn_act_seq == 3)
			{
				self.dn_state = 5;	// Justin Berry's Webcam!
				self.effects = 0;
				sound(self, CHAN_VOICE, "daniel/cant_see_webcam.wav", 0.95, ATTN_NORM);
				self.dn_phase_end = time + 3.2;
			}
			else
			{
				self.dn_state = 7;	// Back at 360° LAN Station CRT desk!
				self.effects = 0;
				self.dn_phase_end = time + 2.8;
			}
		}
		self.think = Daniel_Think;
		self.nextthink = time + 0.05;
		return;
	}

	// Find nearest player target & check if Angry 4 AM Dad is closing in!
	dad = self.dn_chased;
	if ((dad == world || dad.health <= 0 || dad.classname != "monster_dad4am") && time >= self.dn_scan_t)
	{
		self.dn_scan_t = time + 0.5;
		dad = find(world, classname, "monster_dad4am");
		self.dn_chased = dad;
	}
	else if (dad != world && (dad.health <= 0 || dad.classname != "monster_dad4am"))
		dad = world;
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

	// Active special signature attacks (3 = CCC Barrage, 4 = SHAAA Sonic Rage, 5 = Justin's Webcam)
	if (self.dn_state == 3 || self.dn_state == 4 || self.dn_state == 5)
	{
		if (best != world)
			self.angles_y = vectoyaw(best.origin - self.origin);

		if (self.dn_state == 3 && time >= self.dn_next_shot)
		{
			flat_ang = '0 0 0';
			flat_ang_y = self.angles_y + (random() - 0.5) * 26;
			makevectors(flat_ang);
			sound(self, CHAN_WEAPON, "ccc/shoot.wav", 0.75, ATTN_NORM);
			Daniel_LaunchCCC(self.origin + v_forward * 22 + '0 0 32', v_forward);
			self.dn_next_shot = time + 0.22;
		}
		else if (self.dn_state == 4 && time >= self.dn_next_shot)
		{
			Daniel_SonicBlast(185, 10);
			self.dn_next_shot = time + 0.45;
		}

		if (time >= self.dn_phase_end)
		{
			flat_ang = '0 0 0';
			flat_ang_y = self.angles_y;
			makevectors(flat_ang);
			if (self.dn_state == 5)
			{
				// Tosses Justin Berry's eyeball webcam at the end of his squint scan!
				Daniel_ThrowProp("progs/daniel_webcam.md3", self.origin + v_forward * 20 + '0 0 34', v_forward * 380 + '0 0 180', 14);
			}
			self.effects = 0;
			self.dn_state = 2;	// Resume dragging the 4 AM oak table!
			sound(self, CHAN_AUTO, "daniel/table_drag.wav", 0.90, ATTN_NORM);
			self.dn_phase_end = time + 2.2;
		}
		else
		{
			self.think = Daniel_Think;
			self.nextthink = time + 0.05;
			return;
		}
	}

	// Trigger rotating meme signature action every few seconds!
	if (time >= self.dn_next_act && self.dn_state != 6)
	{
		self.dn_act_seq = self.dn_act_seq + 1;
		if (self.dn_act_seq > 3)
			self.dn_act_seq = 1;

		if (self.dn_act_seq == 1)
		{
			// "CCC! C-C-C-C-C!" Yellow-C Barrage!
			self.dn_state = 3;
			self.effects = DN_EF_GLOW;
			if (random() < 0.5)
				sound(self, CHAN_VOICE, "daniel/ccc_chant.wav", 1, ATTN_NORM);
			else
				sound(self, CHAN_VOICE, "daniel/ccc_burst.wav", 1, ATTN_NORM);
			self.dn_phase_end = time + 1.85;
			self.dn_next_shot = time + 0.10;
		}
		else if (self.dn_act_seq == 2)
		{
			// "SHAAAAAAAAAAAA!" Neon LAN Keyboard Sonic Scream!
			self.dn_state = 4;
			self.effects = DN_EF_BLUE + DN_EF_GLOW;
			sound(self, CHAN_VOICE, "daniel/shaaa_scream.wav", 1, ATTN_NORM);
			self.dn_phase_end = time + 2.10;
			self.dn_next_shot = time + 0.15;
		}
		else
		{
			// "When is Justin Berry coming? I wanna borrow his webcam!"
			self.dn_state = 5;
			self.effects = 0;
			sound(self, CHAN_VOICE, "daniel/cant_see_webcam.wav", 1, ATTN_NORM);
			self.dn_phase_end = time + 2.30;
		}
		self.dn_next_act = time + 5.8 + random() * 2.5;
		self.think = Daniel_Think;
		self.nextthink = time + 0.05;
		return;
	}

	// If Angry 4 AM Dad gets close, panic with BOTH HANDS UP ("Sorry! I was just moving the table!") and bolt!
	if (dad != world && dad.health > 0 && vlen(dad.origin - self.origin) < 220)
	{
		want = vectoyaw(self.origin - dad.origin) + (random() - 0.5) * 45;
		if (self.dn_state != 6)
		{
			self.dn_state = 6;
			self.dn_phase_end = time + 1.8;
			if (time >= self.dn_next_voice)
			{
				sound(self, CHAN_VOICE, "daniel/sorry_table.wav", 1, ATTN_NORM);
				self.dn_next_voice = time + 3.2;
			}
		}
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
	self.angles_y = self.angles_y + diff * 0.30;

	if (time >= self.dn_phase_end)
	{
		if (self.dn_state == 2)
		{
			// Fling the wooden 4 AM table forward at the end of a drag sprint!
			flat_ang = '0 0 0';
			flat_ang_y = self.angles_y;
			makevectors(flat_ang);
			Daniel_ThrowProp("progs/daniel_table.md3", self.origin + v_forward * 26 + '0 0 20', v_forward * 320 + '0 0 150', 15);
			self.dn_state = 1;
		}
		else
		{
			self.dn_state = 2;	// Drag the 4 AM wooden table!
			sound(self, CHAN_AUTO, "daniel/table_drag.wav", 0.90, ATTN_NORM);
		}
		self.dn_phase_end = time + 2.0;
	}

	step_dist = 12.2;
	if (self.dn_state == 6)
		step_dist = 15.2;	// Hands-up panic sprint!
	else if (self.dn_state == 2)
		step_dist = 10.8;	// Heavy wooden table drag!

	if (!walkmove(self.angles_y, step_dist))
	{
		self.angles_y = self.angles_y + 110 + random() * 90;
		while (self.angles_y >= 360)
			self.angles_y = self.angles_y - 360;
		walkmove(self.angles_y, step_dist * 0.8);
	}

	self.think = Daniel_Think;
	self.nextthink = time + 0.05;
};

// ---------------------------------------------------------------- Angry 4 AM Dad ("It's 4 in the morning, Daniel!")
float() Dad4AM_Customize =
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

	if (bm_cvar_dn_stay > 0)
	{
		self.frame = d;
		return TRUE;
	}

	k = floor(time * 16 + self.origin_x * 0.04 + self.origin_y * 0.03);
	k = k - 6 * floor(k / 6);
	self.frame = 8 + d * 6 + k;
	return TRUE;
};

void() Dad4AM_Touch =
{
	local vector dir;

	if (self.npc_dead || self.health <= 0)
		return;
	if (other == world || !other.takedamage || other.health <= 0)
		return;
	if (other.classname == "monster_dad4am")
		return;
	if (time < self.dn_next_touch)
		return;
	self.dn_next_touch = time + 0.50;

	if (other.classname == "monster_daniel")
	{
		// Catching Daniel makes Dad roar and Daniel throw both hands up yelling "Sorry! I was just moving the table!"
		other.dn_state = 6;
		other.effects = 0;
		other.dn_phase_end = time + 2.0;
		sound(other, CHAN_VOICE, "daniel/sorry_table.wav", 1, ATTN_NORM);
		dir = normalize(other.origin - self.origin);
		other.angles_y = vectoyaw(dir);
		return;
	}

	T_Damage(other, self, self, 15);
	dir = normalize((other.origin + '0 0 16') - self.origin);
	other.velocity = other.velocity + dir * 240 + '0 0 120';
	if (other.flags & FL_ONGROUND)
		other.flags = other.flags - FL_ONGROUND;
};

void() Dad4AM_DeathStep =
{
	self.npc_dstep = self.npc_dstep + 1;
	if (self.npc_dstep <= 5)
	{
		self.think = Dad4AM_DeathStep;
		self.nextthink = time + 0.075;
		return;
	}
	if (self.npc_dstep == 6)
	{
		self.think = Dad4AM_DeathStep;
		self.nextthink = time + 2.2;
		return;
	}
	if (self.npc_dstep <= 13)
	{
		self.alpha = 1.0 - (self.npc_dstep - 6) * 0.13;
		self.think = Dad4AM_DeathStep;
		self.nextthink = time + 0.07;
		return;
	}
	remove(self);
};

void() Dad4AM_Die =
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
		BM_NPCGibBurst(-80, 4);
		remove(self);
		return;
	}

	self.alpha = 1;
	sound(self, CHAN_VOICE, "player/pain6.wav", 1, ATTN_NORM);
	self.think = Dad4AM_DeathStep;
	self.nextthink = time + 0.075;
};

void() Dad4AM_Think =
{
	local entity targ, p;
	local float want, diff;

	if (self.health <= 0)
	{
		Dad4AM_Die();
		return;
	}

	if (bm_cvar_dn_stay > 0)
	{
		if (cvar("dn_spin") != 0)
			self.angles_y = self.angles_y + cvar("dn_spin");
		self.think = Dad4AM_Think;
		self.nextthink = time + 0.05;
		return;
	}

	if (time >= self.dn_next_voice)
	{
		sound(self, CHAN_VOICE, "daniel/dad_4am.wav", 1, ATTN_NORM);
		self.dn_next_voice = time + 5.8 + random() * 2.5;
	}

	targ = self.dn_chased;
	if (targ == world || targ.health <= 0 || targ.classname != "monster_daniel" || targ.dn_lan_only)
	{
		if (time >= self.dn_scan_t)
		{
			self.dn_scan_t = time + 0.5;
			targ = find(world, classname, "monster_daniel");
			self.dn_chased = targ;
		}
		else
			targ = world;
	}
	if (targ == world || targ.dn_lan_only)
	{
		targ = world;
		p = bm_player_head;
		while (p)
		{
			if (p != self && p.health > 0 && p.takedamage && (targ == world || vlen(p.origin - self.origin) < vlen(targ.origin - self.origin)))
				targ = p;
			p = p.bm_player_next;
		}
	}

	if (targ != world)
	{
		want = vectoyaw(targ.origin - self.origin);
		diff = want - self.angles_y;
		while (diff > 180)
			diff = diff - 360;
		while (diff < -180)
			diff = diff + 360;
		self.angles_y = self.angles_y + diff * 0.30;
	}

	if (!walkmove(self.angles_y, 12.6))
	{
		self.angles_y = self.angles_y + 100 + random() * 80;
		walkmove(self.angles_y, 9.5);
	}

	self.think = Dad4AM_Think;
	self.nextthink = time + 0.05;
};

// ---------------------------------------------------------------- Spawners & Impulse Entry Points
entity(vector pos, float yaw_ang, float lan_mode) Daniel_SpawnOne =
{
	local entity old, b;

	Daniel_Precache();
	old = self;
	b = spawn();
	b.classname = "monster_daniel";
	b.origin = pos;
	setmodel(b, "progs/daniel.spr32");
	b.scale = 0.6935;
	b.solid = SOLID_SLIDEBOX;
	b.movetype = MOVETYPE_STEP;
	b.health = 185;
	b.max_health = 185;
	b.takedamage = DAMAGE_AIM;
	b.th_stand = Daniel_Think;
	b.th_walk = Daniel_Think;
	b.th_run = Daniel_Think;
	b.th_melee = Daniel_Think;
	b.th_missile = Daniel_Think;
	b.th_pain = Daniel_Pain;
	b.th_die = Daniel_Die;
	b.touch = Daniel_Touch;
	b.customizeentityforclient = Daniel_Customize;
	b.dn_lan_only = lan_mode;
	if (lan_mode)
	{
		b.dn_state = 7;		// Full 360° Bakersfield LAN Station!
		b.dn_phase_end = time + 2.8;
	}
	else
	{
		b.dn_state = 2;		// Starts dragging the 4 AM wooden table!
		b.dn_phase_end = time + 2.4;
		b.dn_next_act = time + 3.6;
	}
	b.dn_next_voice = time + 2.0;
	b.flags = FL_MONSTER;
	b.angles_y = yaw_ang;
	while (b.angles_y >= 360)
		b.angles_y = b.angles_y - 360;
	setsize(b, '-20 -20 0', '20 20 56');
	self = b;
	droptofloor();
	self = old;
	b.think = Daniel_Think;
	b.nextthink = time + 0.05;
	return b;
};

entity(vector pos, float yaw_ang, entity target_dn) Dad4AM_SpawnOne =
{
	local entity old, d;

	Daniel_Precache();
	old = self;
	d = spawn();
	d.classname = "monster_dad4am";
	d.origin = pos;
	setmodel(d, "progs/daniel_dad.spr32");
	d.scale = 0.5126;
	d.solid = SOLID_SLIDEBOX;
	d.movetype = MOVETYPE_STEP;
	d.health = 150;
	d.max_health = 150;
	d.takedamage = DAMAGE_AIM;
	d.th_stand = Dad4AM_Think;
	d.th_walk = Dad4AM_Think;
	d.th_run = Dad4AM_Think;
	d.th_die = Dad4AM_Die;
	d.touch = Dad4AM_Touch;
	d.customizeentityforclient = Dad4AM_Customize;
	d.dn_chased = target_dn;
	d.dn_next_voice = time + 4.2;
	d.flags = FL_MONSTER;
	d.angles_y = yaw_ang;
	while (d.angles_y >= 360)
		d.angles_y = d.angles_y - 360;
	setsize(d, '-18 -18 0', '18 18 56');
	self = d;
	droptofloor();
	self = old;
	d.think = Dad4AM_Think;
	d.nextthink = time + 0.05;
	return d;
};

void() monster_daniel =
{
	if (BM_NoMapNPC ())		// no map NPCs unless bm_npcs 1 (2026-11-26)
	{
		remove (self);
		return;
	}
	Daniel_Precache();
	self.dn_home = self.origin;
	setmodel(self, "progs/daniel.spr32");
	self.scale = 0.6935;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 185;
	self.max_health = 185;
	self.takedamage = DAMAGE_AIM;
	self.th_stand = Daniel_Think;
	self.th_walk = Daniel_Think;
	self.th_run = Daniel_Think;
	self.th_melee = Daniel_Think;
	self.th_missile = Daniel_Think;
	self.th_pain = Daniel_Pain;
	self.th_die = Daniel_Die;
	self.touch = Daniel_Touch;
	self.customizeentityforclient = Daniel_Customize;
	if (self.spawnflags & 1)
	{
		self.dn_lan_only = TRUE;
		self.dn_state = 7;
		self.dn_respawn = 25;
	}
	else
		self.dn_state = 2;
	self.dn_phase_end = time + 2.4;
	self.dn_next_act = time + 4.0;
	self.flags = FL_MONSTER;
	setsize(self, '-20 -20 0', '20 20 56');
	droptofloor();
	self.dn_home = self.origin;
	self.think = Daniel_Think;
	self.nextthink = time + 0.1 + random() * 0.2;
};

void() monster_dad4am =
{
	Daniel_Precache();
	setmodel(self, "progs/daniel_dad.spr32");
	self.scale = 0.5126;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = 150;
	self.max_health = 150;
	self.takedamage = DAMAGE_AIM;
	self.th_stand = Dad4AM_Think;
	self.th_walk = Dad4AM_Think;
	self.th_run = Dad4AM_Think;
	self.th_die = Dad4AM_Die;
	self.touch = Dad4AM_Touch;
	self.customizeentityforclient = Dad4AM_Customize;
	self.dn_next_voice = time + 1.0;
	self.flags = FL_MONSTER;
	setsize(self, '-18 -18 0', '18 18 56');
	droptofloor();
	self.think = Dad4AM_Think;
	self.nextthink = time + 0.1 + random() * 0.2;
};

void() Daniel_Summon4AM =
{
	local vector flat_ang;
	local entity dn, dad;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);

	dn = Daniel_SpawnOne(self.origin + v_forward * 124 + '0 0 24', self.v_angle_y + 180, FALSE);
	dad = Dad4AM_SpawnOne(self.origin + v_forward * 212 + v_right * 28 + '0 0 24', self.v_angle_y + 180, dn);
	Daniel_SpawnPoster(self.origin + v_forward * 156 - v_right * 68 + '0 0 42', self.v_angle_y + 180, daniel_poster_seq);
	daniel_poster_seq = daniel_poster_seq + 1;
	if (daniel_poster_seq >= 4)
		daniel_poster_seq = 0;

	sound(dn, CHAN_AUTO, "daniel/table_drag.wav", 1, ATTN_NORM);
	sound(dad, CHAN_VOICE, "daniel/dad_4am.wav", 1, ATTN_NORM);
};

void() Daniel_Summon =
{
	local vector flat_ang;
	local entity dn;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	dn = Daniel_SpawnOne(self.origin + v_forward * 132 + '0 0 24', self.v_angle_y + 180, FALSE);
	sound(dn, CHAN_VOICE, "daniel/ccc_chant.wav", 1, ATTN_NORM);
};

void() Daniel_SummonLAN =
{
	local vector flat_ang;
	local entity dn;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	dn = Daniel_SpawnOne(self.origin + v_forward * 142 + '0 0 24', self.v_angle_y + 180, TRUE);
	sound(dn, CHAN_VOICE, "daniel/cant_see_webcam.wav", 1, ATTN_NORM);
};

void() Dad4AM_Summon =
{
	local vector flat_ang;
	local entity dn, dad;

	flat_ang = '0 0 0';
	flat_ang_y = self.v_angle_y;
	makevectors(flat_ang);
	dn = find(world, classname, "monster_daniel");
	dad = Dad4AM_SpawnOne(self.origin + v_forward * 138 + '0 0 24', self.v_angle_y + 180, dn);
	sound(dad, CHAN_VOICE, "daniel/dad_4am.wav", 1, ATTN_NORM);
};
