/*
Wheelman. Impulse 18 summons one in front of you. It rolls at the nearest player on
progs/wheelman.spr32 (build_wheelman_sprite.py + wheelman_fx.py + wheelman_boom360.py + wheelman_stunts.py).

Compact 360° + Above/Below + 2x 360° Stunts Layout
(200 frames, 144x102 tight-cropped, origin (-72, 92), w.scale = 1.3333):
  0..7                         8-direction eye-level idle (d = 0..7)
  8 + d*6 + k                  8-direction eye-level driving/rolling (d = 0..7, k = 0..5)
  56 + d*4 + k                 8-direction eye-level screaming (d = 0..7, k = 0..3)
  88 + d*3 + k                 8-direction ABOVE HIM overhead rolling (d = 0..7, k = 0..2)
  112 + d*3 + k                8-direction BELOW HIM underneath rolling (d = 0..7, k = 0..2)
  136 + d*4 + k                Stunt 1: Fire-Wheels Hyper-Burnout (d = 0..7, k = 0..3)
  168 + d*4 + k                Stunt 2: Super-Long Metal Bar & Steamroller Wheels (d = 0..7, k = 0..3)
*/

float	wm_boom_seq;
.float	wm_run;
.float	wm_nextpain;
.float	wm_scream_until;
.float	wm_nextscream;
.float	wm_stunt;
.float	wm_stunt_until;
.float	wm_nextstunt;
.float	wm_dead;
.float	wm_tier;
.float	wm_dstep;

void() Wheelman_Die;
void() Wheelman_Think;
void(entity attacker, float take) Wheelman_Pain;

void() Wheelman_Precache =
{
	precache_model("progs/wheelman.spr32");
	precache_model("progs/gib1.mdl");
	precache_model("progs/gib2.mdl");
	precache_model("progs/gib3.mdl");
	precache_sound("weapons/r_exp3.wav");
	precache_sound("weapons/lstart.wav");
	precache_sound("weapons/lhit.wav");
	precache_sound("player/pain6.wav");
	precache_sound("player/udeath.wav");
	precache_sound("player/gibexplode.wav");
};

float() Wheelman_Customize =
{
	local float rel, d, k, dz, hdist;
	local vector delta;

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 28');
	rel = vectoyaw(delta) - self.angles_y;
	rel = rel - 360 * floor(rel / 360);
	d = floor(rel / 45 + 0.5);
	if (d >= 8)
		d = 0;

	if (self.wm_dead)
	{
		k = self.wm_dstep - 4 * floor(self.wm_dstep / 4);
		self.frame = 56 + d * 4 + k;
		return TRUE;
	}

	dz = delta_z;
	delta_z = 0;
	hdist = vlen(delta);

	// Steep overhead view (player above Wheelman looking down)
	if (dz > hdist * 0.62)
	{
		if (self.wm_run)
		{
			k = floor(time * 15);
			k = k - 3 * floor(k / 3);
		}
		else
			k = 0;
		self.frame = 88 + d * 3 + k;
		return TRUE;
	}

	// Steep underneath view (player below Wheelman looking up)
	if (dz < -hdist * 0.55)
	{
		if (self.wm_run)
		{
			k = floor(time * 15);
			k = k - 3 * floor(k / 3);
		}
		else
			k = 0;
		self.frame = 112 + d * 3 + k;
		return TRUE;
	}

	if (self.wm_stunt > 0 && time < self.wm_stunt_until)
	{
		k = floor(time * 12);
		k = k - 4 * floor(k / 4);
		if (self.wm_stunt == 1)
			self.frame = 136 + d * 4 + k;
		else
			self.frame = 168 + d * 4 + k;
		return TRUE;
	}
	if (time < self.wm_scream_until)
	{
		k = floor(time * 12);
		k = k - 4 * floor(k / 4);
		self.frame = 56 + d * 4 + k;
		return TRUE;
	}
	if (self.wm_run)
	{
		k = floor(time * 10 + self.origin_x * 0.025);
		k = k - 6 * floor(k / 6);
		self.frame = 8 + d * 6 + k;
	}
	else
		self.frame = d;
	return TRUE;
};

void(entity attacker, float take) Wheelman_Pain =
{
	if (self.health <= 0)
		return;
	if (time < self.wm_scream_until)
		return;
	self.wm_scream_until = time + 0.65;
	sound(self, CHAN_VOICE, "player/pain6.wav", 1, ATTN_NORM);
};

void() Wheelman_Touch =
{
	if (other == world || !other.takedamage || other.health <= 0)
		return;
	if (other.classname == "monster_wheelman")
		return;
	if (time < self.wm_nextpain)
		return;
	self.wm_nextpain = time + 0.50;
	T_Damage(other, self, self, 16);
};

void(vector org, float te_type) Wheelman_NetBlast =
{
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, te_type);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, org_y);
	WriteCoord(MSG_BROADCAST, org_z);
};

void() Wheelman_DieLoop =
{
	local float gcount, gi;
	local vector boff;

	self.wm_dstep = self.wm_dstep + 1;
	if (self.wm_dstep >= 14)
	{
		self.wm_dstep = 13;
		self.frame = 57;
		self.think = SUB_Remove;
		self.nextthink = time + 4.5;
		return;
	}
	self.frame = 56 + (self.wm_dstep - 4 * floor(self.wm_dstep / 4));

	// Act 2: Critical overload whine / Tesla charge
	if (self.wm_dstep == 3)
		sound(self, CHAN_ITEM, "weapons/lstart.wav", 1, ATTN_NORM);

	// Act 3: Primary Core Detonation — escalates massively across Tiers 0..3!
	if (self.wm_dstep == 5)
	{
		sound(self, CHAN_BODY, "weapons/r_exp3.wav", 1, ATTN_NORM);
		sound(self, CHAN_VOICE, "player/udeath.wav", 1, ATTN_NORM);

		gcount = 3 + self.wm_tier * 4;
		gi = 0;
		while (gi < gcount)
		{
			ThrowGib("progs/gib1.mdl", -70 - self.wm_tier * 25);
			ThrowGib("progs/gib2.mdl", -85 - self.wm_tier * 30);
			if (gi < 4)
				ThrowGib("progs/gib3.mdl", -95 - self.wm_tier * 35);
			gi = gi + 2;
		}
		if (self.wm_tier == 2)
			Wheelman_NetBlast(self.origin + '0 0 36', TE_TAREXPLOSION);
		else if (self.wm_tier == 3)
			Wheelman_NetBlast(self.origin + '0 0 24', TE_LAVASPLASH);
	}

	// Act 4: Escalating Secondary / Tornado / Carpet-Bomb Blasts!
	if (self.wm_dstep == 8 || (self.wm_tier >= 1 && self.wm_dstep == 10))
	{
		sound(self, CHAN_AUTO, "player/gibexplode.wav", 1, ATTN_NORM);
		if (self.wm_tier >= 1)
		{
			boff_x = (random() - 0.5) * (90 + self.wm_tier * 50);
			boff_y = (random() - 0.5) * (90 + self.wm_tier * 50);
			boff_z = 24 + random() * 48;
			Wheelman_NetBlast(self.origin + boff, TE_EXPLOSION);
		}
		if (self.wm_tier == 2 && self.wm_dstep == 10)
		{
			sound(self, CHAN_WEAPON, "weapons/lhit.wav", 1, ATTN_NORM);
			WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
			WriteByte(MSG_BROADCAST, TE_LIGHTNING2);
			WriteEntity(MSG_BROADCAST, self);
			WriteCoord(MSG_BROADCAST, self.origin_x);
			WriteCoord(MSG_BROADCAST, self.origin_y);
			WriteCoord(MSG_BROADCAST, self.origin_z + 256);
			WriteCoord(MSG_BROADCAST, self.origin_x);
			WriteCoord(MSG_BROADCAST, self.origin_y);
			WriteCoord(MSG_BROADCAST, self.origin_z);
		}
	}

	self.think = Wheelman_DieLoop;
	// Slower step cadence on bigger tiers so Tier 4 nuclear cataclysm lasts ~3.4s in-game!
	self.nextthink = time + (0.14 + self.wm_tier * 0.035);
};

void() Wheelman_Die =
{
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.wm_run = 0;
	self.wm_dead = 1;
	self.wm_tier = wm_boom_seq;
	wm_boom_seq = wm_boom_seq + 1;
	if (wm_boom_seq >= 4)
		wm_boom_seq = 0;
	self.wm_dstep = 0;
	self.frame = 56;
	sound(self, CHAN_VOICE, "player/pain6.wav", 1, ATTN_NORM);
	self.think = Wheelman_DieLoop;
	self.nextthink = time + 0.14;
};

void() Wheelman_Think =
{
	local entity e, best;
	local float bestd, d, want, diff;

	if (self.health <= 0)
	{
		Wheelman_Die();
		return;
	}
	best = world;
	bestd = 1400;
	e = findradius(self.origin, 1400);
	while (e)
	{
		if ((e.flags & FL_CLIENT) && e.health > 0 && e != self)
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
	if (best != world)
	{
		if (!self.wm_run && time > self.wm_nextscream)
		{
			self.wm_scream_until = time + 0.65;
			self.wm_nextscream = time + 4.0;
			sound(self, CHAN_VOICE, "player/pain6.wav", 1, ATTN_NORM);
		}
		else if (time > self.wm_nextscream)
		{
			self.wm_scream_until = time + 0.55;
			self.wm_nextscream = time + 5.5;
			sound(self, CHAN_VOICE, "player/pain6.wav", 0.85, ATTN_NORM);
		}
		want = vectoyaw(best.origin - self.origin);
		diff = want - self.angles_y;
		while (diff > 180)
			diff = diff - 360;
		while (diff < -180)
			diff = diff + 360;
		self.angles_y = self.angles_y + diff * 0.25;
		self.wm_run = 1;

		// Cycle dynamically through Fire-Wheels Turbo (1), Super-Long Bar Sweep (2), & Jetpack Hover Flight (3)!
		if (time > self.wm_nextstunt)
		{
			if (best.origin_z > self.origin_z + 42)
				self.wm_stunt = 3;
			else if (bestd < 160)
				self.wm_stunt = 2;
			else if (random() < 0.36)
				self.wm_stunt = 3;
			else
				self.wm_stunt = 1;
			self.wm_stunt_until = time + 2.2;
			self.wm_nextstunt = time + 4.4;
			if (self.wm_stunt == 3)
			{
				self.flags = self.flags - (self.flags & FL_ONGROUND);
				self.velocity_z = 240;
			}
		}

		if (time >= self.wm_stunt_until)
			self.wm_stunt = 0;

		if (self.wm_stunt == 1)
			walkmove(self.angles_y, 13.0);
		else if (self.wm_stunt == 3)
		{
			makevectors('0 1 0' * self.angles_y);
			self.velocity_x = v_forward_x * 210;
			self.velocity_y = v_forward_y * 210;
			if (self.origin_z < best.origin_z + 32)
				self.velocity_z = 95;
		}
		else
			walkmove(self.angles_y, 7.5);
	}
	else
		self.wm_run = 0;
	self.think = Wheelman_Think;
	self.nextthink = time + 0.05;
};

void() Wheelman_Summon =
{
	local entity old, w;

	old = self;
	makevectors(self.v_angle);
	w = spawn();
	w.classname = "monster_wheelman";
	w.origin = old.origin + v_forward * 112 + '0 0 24';
	setmodel(w, "progs/wheelman.spr32");
	w.scale = 1.3333;
	w.solid = SOLID_SLIDEBOX;
	w.movetype = MOVETYPE_STEP;
	w.health = 140;
	w.max_health = 140;
	w.takedamage = DAMAGE_AIM;
	w.th_pain = Wheelman_Pain;
	w.th_die = Wheelman_Die;
	w.touch = Wheelman_Touch;
	w.customizeentityforclient = Wheelman_Customize;
	w.think = Wheelman_Think;
	w.nextthink = time + 0.1;
	w.flags = FL_MONSTER;
	w.angles_y = old.angles_y;
	setsize(w, '-20 -20 0', '20 20 56');
	droptofloor();
};
