void() Banana_Precache =
{
};

// small banana goes off: little burst, no screen shake, no big sprite
void(entity hit) Banana_MiniExplode =
{
	bn_inflicting = TRUE;
	T_RadiusDamage (self, self.owner, BN_MINI_SPLASH, hit);
	bn_inflicting = FALSE;

	sendParticle ("grenade_explosion_nodebris", self.origin, VEC_ORIGIN, 1, 0);
	sound7 (self, CHAN_AUTO, "weapons/bananapop.wav", 0.8, ATTN_NORM, SNDSPD * (0.85 + random () * 0.3));
	remove (self);
};

void() Banana_MiniFuse =
{
	Banana_MiniExplode (world);
};

void() Banana_MiniTouch =
{
	if (other == self.owner)
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	if (other.takedamage)
	{
		bn_inflicting = TRUE;
		T_Damage (other, self, self.owner, BN_MINI_DAMAGE + random () * 6);
		bn_inflicting = FALSE;
		Banana_MiniExplode (other);
	}
};

// the big banana burst: BN_MINIS little ones fly out in all directions, mostly upward
void(vector org, entity who) Banana_Burst =
{
	local entity m;
	local float i, spd;
	local vector dir;

	i = 0;
	while (i < BN_MINIS)
	{
		dir_x = crandom ();
		dir_y = crandom ();
		dir_z = random () * 1.2 - 0.1;
		dir = normalize (dir);
		spd = 220 + random () * 260;

		m = spawn ();
		m.owner = who;
		m.classname = "minibanana";
		m.movetype = MOVETYPE_BOUNCE;
		m.solid = SOLID_TRIGGER;	// so the little ones do not block each other
		m.touch = Banana_MiniTouch;
		m.think = Banana_MiniFuse;
		m.nextthink = time + 1.2 + random () * 1.6;
		m.velocity = dir * spd;
		m.avelocity_x = crandom () * 500;
		m.avelocity_y = crandom () * 500;
		m.avelocity_z = crandom () * 500;
		m.angles_y = random () * 360;
		m.scale = 1.4;
		setmodel (m, "progs/banana.md3");
		setsize (m, VEC_ORIGIN, VEC_ORIGIN);	// point hull, like a grenade
		setorigin (m, org + dir * 6);
		i = i + 1;
	}
};

void() Banana_BigTouch =
{
	local vector org;

	if (other == self.owner)
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}

	org = self.origin;
	if (vlen (self.velocity) > 1)
		org = org - normalize (self.velocity) * 12;	// back off the wall so the little ones start in open air

	bn_inflicting = TRUE;
	if (other.takedamage)
		T_Damage (other, self, self.owner, BN_BIG_DAMAGE + random () * 20);
	T_RadiusDamage (self, self.owner, BN_BIG_SPLASH, other);
	bn_inflicting = FALSE;

	if (pointcontents (self.origin) == CONTENT_SLIME)
		sendParticle ("slimesplash", self.origin, VEC_ORIGIN, 1, 0);
	else
		sendParticle ("rocket_explosion", self.origin, VEC_ORIGIN, 1, 0);
	sound7 (self, CHAN_WEAPON, "weapons/bananasplat.wav", 1, ATTN_NORM, SNDSPD);
	sound7 (self, CHAN_AUTO, "weapons/r_exp3.wav", 0.7, ATTN_NORM, SNDSPD * 1.1);
	if (random () < 0.5)
		sound7 (self, CHAN_VOICE, "weapons/bananalaugh.wav", 1, ATTN_NORM, SNDSPD);

	Banana_Burst (org, self.owner);
	BecomeExplosion ();
};

void() Banana_BigGiveUp =
{
	remove (self);
};

// the banana leaves the tube
void() Banana_Launch =
{
	local entity b;
	local vector dir;

	self.bn_ammo = self.bn_ammo - 1;
	if (self.weapon == IT_BANANA)
		self.currentammo = self.bn_ammo;
	if (self.bn_ammo < BN_MAX_AMMO && self.bn_regen_t < time)
		self.bn_regen_t = time + BN_REGEN_TIME;

	sound7 (self, CHAN_WEAPON, "weapons/bananafire.wav", 1, ATTN_NORM, SNDSPD);
	if (random () < 0.6)
		sound7 (self, CHAN_VOICE, "weapons/bananavoice.wav", 1, ATTN_NORM, SNDSPD);	// "do you like my banana cannon"
	self.punchangle_x = -4;

	makevectors (self.v_angle);
	dir = aim (self, 1000);

	b = spawn ();
	b.owner = self;
	b.classname = "bigbanana";
	b.movetype = MOVETYPE_FLYMISSILE;
	b.solid = SOLID_BBOX;
	b.velocity = dir * BN_SPEED;
	b.angles = vectoangles (dir);
	b.avelocity = '0 0 540';
	b.scale = BN_SCALE;
	b.touch = Banana_BigTouch;
	b.think = Banana_BigGiveUp;
	b.nextthink = time + 8;
	setmodel (b, "progs/banana.md3");
	setsize (b, VEC_ORIGIN, VEC_ORIGIN);	// a point, like a rocket: any bigger box uses the player hull and sticks in corridors

	// start in front of the muzzle, but not inside a wall
	traceline (self.origin + '0 0 16', self.origin + '0 0 16' + v_forward * 30, TRUE, self);
	setorigin (b, trace_endpos);
};

// fire pressed with the banana gun out (called from W_Attack)
void() Banana_Attack =
{
	if (self.bn_ammo < 1)
	{
		sound7 (self, CHAN_WEAPON, "weapons/pkup.wav", 0.4, ATTN_NORM, SNDSPD);
		self.attack_finished = time + 0.3;
		return;
	}
	player_mm1 ();		// the rocket firing pose
	self.bn_fire_t = time;
	self.bn_launch_t = time + 0.1;
	self.bn_pending = TRUE;
	self.attack_finished = time + 1.1;
};

// impulse BN_IMPULSE
// REMOVED: the banana gun is switched off (original in BakersfieldQuake/source/mm_tools/out/removed_guns_src). impulse 15 does nothing.
void() Banana_Select =
{
	self.impulse = 0;
};

// gives a player the gun (spawn, impulse 9)
void(entity p) Banana_Give =
{
};

// the little banana other players see in your hand (hidden from you unless you are in third person)
void() Banana_VwepThink =
{
	local entity p;
	local float s;

	p = self.owner;
	if (p.bn_vwep != self || p.classname != "player" || p.health <= 0)
	{
		if (p.bn_vwep == self)
			p.bn_vwep = world;
		remove (self);
		return;
	}
	self.nextthink = time + 0.1;
	s = sin (time * 5);
	self.origin_z = s * 1.2;
};

void() Banana_UpdateVwep =
{
	local entity e;
	local float show;

	show = (self.weapon == IT_BANANA && self.health > 0 && !(self.items & IT_INVISIBILITY));
	if (!show)
	{
		if (self.bn_vwep)
		{
			remove (self.bn_vwep);
			self.bn_vwep = world;
		}
		return;
	}

	e = self.bn_vwep;
	if (!e)
	{
		e = spawn ();
		e.classname = "bn_vwep";
		e.owner = self;
		e.exteriormodeltoclient = self;
		e.scale = 1.2;
		setattachment (e, self, "");
		e.origin = '12 -18 0';
		e.angles = '0 0 80';
		e.think = Banana_VwepThink;
		e.nextthink = time + 0.1;
		self.bn_vwep = e;
		setmodel (e, "progs/banana.md3");
	}
};

// called every frame from W_WeaponFrame: recharge, shot timing, the view model's animation
// (v_banana.md3: 0-7 idle bob, 8-15 recoil)
void() Banana_ViewFrame =
{
	local float t;
	local float f;

	if (self.bn_ammo < BN_MAX_AMMO)
	{
		if (!self.bn_regen_t)
			self.bn_regen_t = time + BN_REGEN_TIME;
		else if (time >= self.bn_regen_t)
		{
			self.bn_ammo = self.bn_ammo + 1;
			self.bn_regen_t = 0;
			if (self.weapon == IT_BANANA)
				self.currentammo = self.bn_ammo;
		}
	}

	if (self.bn_pending && time >= self.bn_launch_t)
	{
		self.bn_pending = FALSE;
		if (time - self.bn_launch_t < 0.3 && self.health > 0)
			Banana_Launch ();
	}

	Banana_UpdateVwep ();

	if (self.weapon != IT_BANANA)
		return;
	t = time - self.bn_fire_t;
	if (self.bn_fire_t && t < 0.5)
	{
		f = 8 + floor (t * 16);
		if (f > 15)
			f = 15;
	}
	else
	{
		f = floor (time * 10);
		f = f - 8 * floor (f / 8);
	}
	self.weaponframe = f;
};
