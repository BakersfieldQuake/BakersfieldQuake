// dn3fx_csqc.qc — Client-side DN3DooM fire, smoke, bullet puff, and explosion FX.
// Zero server edicts retained: server emits transient ENT_DN3FX (9) events and
// CSQC spawns capped, smoothly-fading local entities in a transient FX ring buffer.

float ENT_DN3FX = 9;

float DN3FX_EXPLODE     = 3;
float DN3FX_FIRE_BURST  = 4;
float DN3FX_BULLET_PUFF = 5;

float DN3FX_EF_ADDITIVE   = 32;
float DN3FX_EF_FULLBRIGHT = 512;

float DN3FX_MAX_TRANSIENT = 48;

.float dn3fx_kind;
.float dn3fx_born;
.float dn3fx_last;
.float dn3fx_life;
.float dn3fx_fade;
.float dn3fx_rate;
.float dn3fx_f0;
.float dn3fx_fcnt;
.float dn3fx_grav;
.float dn3fx_grow;
.entity dn3fx_qprev;
.entity dn3fx_qnext;

entity dn3fx_fx_head;
entity dn3fx_fx_tail;
float dn3fx_fx_count;

void() DN3FX_Precache =
{
	registercvar("bm_dn3fx", "1");

	precache_model("progs/dn3fx_explode.spr32");
	precache_model("progs/dn3fx_fireball.spr32");
	precache_model("progs/dn3fx_flame.spr32");
	precache_model("progs/dn3fx_smoke.spr32");
	precache_model("progs/dn3fx_shockwave.spr32");

	dn3fx_fx_head = world;
	dn3fx_fx_tail = world;
	dn3fx_fx_count = 0;
};

float() DN3FX_Enabled =
{
	return (cvar("bm_dn3fx") != 0);
};

float() DN3FX_CRand =
{
	return (random() * 2.0) - 1.0;
};

void(entity e) DN3FX_QueueRemove =
{
	if (e.dn3fx_qprev)
		e.dn3fx_qprev.dn3fx_qnext = e.dn3fx_qnext;
	else if (dn3fx_fx_head == e)
		dn3fx_fx_head = e.dn3fx_qnext;
	if (e.dn3fx_qnext)
		e.dn3fx_qnext.dn3fx_qprev = e.dn3fx_qprev;
	else if (dn3fx_fx_tail == e)
		dn3fx_fx_tail = e.dn3fx_qprev;
	dn3fx_fx_count = dn3fx_fx_count - 1;
	e.dn3fx_qprev = world;
	e.dn3fx_qnext = world;
	remove(e);
};

entity() DN3FX_Alloc =
{
	local entity e;

	while (dn3fx_fx_count >= DN3FX_MAX_TRANSIENT && dn3fx_fx_head != world)
		DN3FX_QueueRemove(dn3fx_fx_head);

	e = spawn();
	e.classname = "dn3fx_local";
	e.drawmask = MASK_ENGINE;
	e.dn3fx_born = time;
	e.alpha = 1.0;
	e.scale = 1.0;

	e.dn3fx_qprev = dn3fx_fx_tail;
	e.dn3fx_qnext = world;
	if (dn3fx_fx_tail)
		dn3fx_fx_tail.dn3fx_qnext = e;
	else
		dn3fx_fx_head = e;
	dn3fx_fx_tail = e;
	dn3fx_fx_count = dn3fx_fx_count + 1;
	return e;
};

void() DN3FX_SpriteThink =
{
	local float age, dt, f;

	dt = time - self.dn3fx_last;
	if (dt <= 0)
		dt = 0.02;
	self.dn3fx_last = time;

	age = time - self.dn3fx_born;
	if (age >= self.dn3fx_life)
	{
		DN3FX_QueueRemove(self);
		return;
	}

	if (vlen(self.velocity) > 0.1 || self.dn3fx_grav != 0)
	{
		self.velocity_z = self.velocity_z - self.dn3fx_grav * dt;
		setorigin(self, self.origin + self.velocity * dt);
	}

	if (self.dn3fx_grow != 0)
	{
		self.scale = self.scale + self.dn3fx_grow * dt;
		if (self.scale < 0.05)
			self.scale = 0.05;
	}

	if (self.dn3fx_rate > 0 && self.dn3fx_fcnt > 1)
	{
		f = floor(age * self.dn3fx_rate);
		if (self.dn3fx_kind == DN3FX_FIRE_BURST)
			f = f - floor(f / self.dn3fx_fcnt) * self.dn3fx_fcnt;
		else if (f >= self.dn3fx_fcnt)
			f = self.dn3fx_fcnt - 1;
		self.frame = self.dn3fx_f0 + f;
	}

	if (self.dn3fx_fade > 0 && age > (self.dn3fx_life - self.dn3fx_fade))
	{
		f = self.count * (1.0 - (age - (self.dn3fx_life - self.dn3fx_fade)) / self.dn3fx_fade);
		if (f < 0.02)
			f = 0.02;
		self.alpha = f;
	}

	self.nextthink = time + 0.025;
};

entity(string mdl, vector org, vector vel, float sc, float al, float eff, float life, float fade, float f0, float fcnt, float rate, float grav, float grow) DN3FX_SpawnSprite =
{
	local entity e;

	e = DN3FX_Alloc();
	setmodel(e, mdl);
	setorigin(e, org);
	e.velocity = vel;
	e.scale = sc;
	e.alpha = al;
	e.count = al;
	e.effects = eff;
	e.dn3fx_life = life;
	e.dn3fx_fade = fade;
	e.dn3fx_f0 = f0;
	e.dn3fx_fcnt = fcnt;
	e.dn3fx_rate = rate;
	e.dn3fx_grav = grav;
	e.dn3fx_grow = grow;
	e.frame = f0;
	e.dn3fx_last = time;
	e.think = DN3FX_SpriteThink;
	e.nextthink = time + 0.02;
	return e;
};

void(vector org, float s) DN3FX_RunExplode =
{
	local float i, eff_glow;
	local vector p, vel, fl_pos;
	local entity fl;

	eff_glow = DN3FX_EF_FULLBRIGHT | DN3FX_EF_ADDITIVE;

	// Core Duke RPG explosion fireball (21 frames)
	DN3FX_SpawnSprite(
		"progs/dn3fx_explode.spr32",
		org + '0 0 6',
		'0 0 14',
		1.15 * s,
		0.98,
		eff_glow,
		0.70,
		0.18,
		0, 21, 30.0, 0, 0.25 * s
	);

	// Expanding shockwave ring (9 frames)
	DN3FX_SpawnSprite(
		"progs/dn3fx_shockwave.spr32",
		org,
		'0 0 0',
		0.45 * s,
		0.85,
		eff_glow,
		0.36,
		0.22,
		0, 9, 25.0, 0, 1.85 * s
	);

	// Secondary fireball burst (FRB1 14 frames)
	p = org;
	p_x = p_x + DN3FX_CRand() * 10.0;
	p_y = p_y + DN3FX_CRand() * 10.0;
	p_z = p_z + random() * 10.0;
	DN3FX_SpawnSprite(
		"progs/dn3fx_fireball.spr32",
		p,
		'0 0 24',
		0.75 * s,
		0.90,
		eff_glow,
		0.52,
		0.20,
		0, 14, 27.0, 0, 0.25 * s
	);

	// Rising smoke puffs
	for (i = 0; i < 3; i = i + 1)
	{
		p = org;
		p_x = p_x + DN3FX_CRand() * 16.0;
		p_y = p_y + DN3FX_CRand() * 16.0;
		p_z = p_z + 6.0 + random() * 12.0;
		vel_x = DN3FX_CRand() * 22.0;
		vel_y = DN3FX_CRand() * 22.0;
		vel_z = 44.0 + random() * 34.0;
		DN3FX_SpawnSprite(
			"progs/dn3fx_smoke.spr32",
			p,
			vel,
			(0.65 + random() * 0.35) * s,
			0.72,
			0,
			0.95 + random() * 0.30,
			0.45,
			0, 16, 17.0, -8.0, 0.40 * s
		);
	}

	// Lingering ground flames
	traceline(org + '0 0 8', org - '0 0 72', TRUE, world);
	fl_pos = (trace_fraction < 1.0) ? (trace_endpos + '0 0 2') : org;
	for (i = 0; i < 2; i = i + 1)
	{
		p = fl_pos;
		p_x = p_x + DN3FX_CRand() * 18.0 * s;
		p_y = p_y + DN3FX_CRand() * 18.0 * s;
		fl = DN3FX_SpawnSprite(
			"progs/dn3fx_flame.spr32",
			p,
			'0 0 8',
			(0.85 + random() * 0.40) * s,
			0.92,
			eff_glow,
			1.25 + random() * 0.65,
			0.50,
			(random() < 0.5) ? 0 : 16, 16, 22.0, 0, -0.25 * s
		);
		fl.dn3fx_kind = DN3FX_FIRE_BURST;
	}
};

void(vector org, vector dir, float s) DN3FX_RunFireBurst =
{
	local float eff_glow;
	local vector vel;
	local entity fl;

	eff_glow = DN3FX_EF_FULLBRIGHT | DN3FX_EF_ADDITIVE;
	vel = dir * 0.25;
	vel_x = vel_x + DN3FX_CRand() * 16.0;
	vel_y = vel_y + DN3FX_CRand() * 16.0;
	vel_z = vel_z + 18.0 + random() * 24.0;

	fl = DN3FX_SpawnSprite(
		"progs/dn3fx_flame.spr32",
		org,
		vel,
		(0.75 + random() * 0.40) * s,
		0.92,
		eff_glow,
		0.75 + random() * 0.45,
		0.32,
		(random() < 0.5) ? 0 : 16, 16, 22.0, -10.0, -0.20 * s
	);
	fl.dn3fx_kind = DN3FX_FIRE_BURST;

	if (random() < 0.35)
	{
		DN3FX_SpawnSprite(
			"progs/dn3fx_smoke.spr32",
			org + '0 0 10',
			'0 0 42',
			0.45 * s,
			0.50,
			0,
			0.65,
			0.35,
			0, 16, 22.0, -6.0, 0.25 * s
		);
	}
};

void(vector org, vector dir, float s) DN3FX_RunBulletPuff =
{
	local vector d, vel;

	d = (vlen(dir) > 0.01) ? normalize(dir) : '0 0 1';
	vel = d * 24.0 + '0 0 20';
	DN3FX_SpawnSprite(
		"progs/dn3fx_smoke.spr32",
		org + d * 2.0,
		vel,
		(0.26 + random() * 0.12) * s,
		0.55,
		0,
		0.40,
		0.22,
		0, 16, 36.0, 0, 0.20 * s
	);
};

void(float isnew) DN3FX_EntUpdate =
{
	local float flags, kind, sc;
	local vector org, dir;

	flags = ReadByte();
	if (!(flags & 1))
		return;

	kind = ReadByte();
	org_x = ReadCoord();
	org_y = ReadCoord();
	org_z = ReadCoord();
	dir_x = ReadCoord();
	dir_y = ReadCoord();
	dir_z = ReadCoord();
	sc = ReadByte() / 32.0;
	if (sc <= 0.05)
		sc = 1.0;

	if (!isnew || !DN3FX_Enabled())
		return;

	if (kind == DN3FX_EXPLODE)
		DN3FX_RunExplode(org, sc);
	else if (kind == DN3FX_FIRE_BURST)
		DN3FX_RunFireBurst(org, dir, sc);
	else if (kind == DN3FX_BULLET_PUFF)
		DN3FX_RunBulletPuff(org, dir, sc);
};
