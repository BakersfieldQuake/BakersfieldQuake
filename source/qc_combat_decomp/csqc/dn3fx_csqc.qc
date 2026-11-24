// dn3fx_csqc.qc — Client-side DN3DooM blood, gore, fire, smoke, and explosion FX.
// Zero server edicts retained: server emits transient ENT_DN3FX (9) events and
// CSQC spawns capped, smoothly-fading local entities in two ring buffers.

float ENT_DN3FX = 9;

float DN3FX_BLOOD_HIT   = 1;
float DN3FX_GIB_BURST   = 2;
float DN3FX_EXPLODE     = 3;
float DN3FX_FIRE_BURST  = 4;
float DN3FX_BULLET_PUFF = 5;

float DN3FX_EF_ADDITIVE   = 32;
float DN3FX_EF_FULLBRIGHT = 512;

float DN3FX_MAX_DECALS    = 64;
float DN3FX_MAX_TRANSIENT = 48;
float DN3FX_DECAL_LIFE    = 22.0;
float DN3FX_DECAL_FADE    = 5.0;

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
.float dn3fx_bounce;
.float dn3fx_splat_s;
.float dn3fx_is_decal;
.vector dn3fx_avel;
.entity dn3fx_qprev;
.entity dn3fx_qnext;

entity dn3fx_decal_head;
entity dn3fx_decal_tail;
float dn3fx_decal_count;

entity dn3fx_fx_head;
entity dn3fx_fx_tail;
float dn3fx_fx_count;

void() DN3FX_Precache =
{
	registercvar("bm_dn3fx", "1");

	precache_model("progs/dn3fx_bloodpuff.spr32");
	precache_model("progs/dn3fx_blooddrop.spr32");
	precache_model("progs/dn3fx_gore2d.spr32");
	precache_model("progs/dn3fx_explode.spr32");
	precache_model("progs/dn3fx_fireball.spr32");
	precache_model("progs/dn3fx_flame.spr32");
	precache_model("progs/dn3fx_smoke.spr32");
	precache_model("progs/dn3fx_shockwave.spr32");
	precache_model("progs/dn3fx_wallsplat.md3");
	precache_model("progs/dn3fx_pool.md3");
	precache_model("progs/dn3fx_flesh1.md3");

	dn3fx_decal_head = world;
	dn3fx_decal_tail = world;
	dn3fx_decal_count = 0;
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
	if (e.dn3fx_is_decal)
	{
		if (e.dn3fx_qprev)
			e.dn3fx_qprev.dn3fx_qnext = e.dn3fx_qnext;
		else if (dn3fx_decal_head == e)
			dn3fx_decal_head = e.dn3fx_qnext;
		if (e.dn3fx_qnext)
			e.dn3fx_qnext.dn3fx_qprev = e.dn3fx_qprev;
		else if (dn3fx_decal_tail == e)
			dn3fx_decal_tail = e.dn3fx_qprev;
		dn3fx_decal_count = dn3fx_decal_count - 1;
	}
	else
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
	}
	e.dn3fx_qprev = world;
	e.dn3fx_qnext = world;
	remove(e);
};

entity(float is_decal) DN3FX_Alloc =
{
	local entity e;

	if (is_decal)
	{
		while (dn3fx_decal_count >= DN3FX_MAX_DECALS && dn3fx_decal_head != world)
			DN3FX_QueueRemove(dn3fx_decal_head);
	}
	else
	{
		while (dn3fx_fx_count >= DN3FX_MAX_TRANSIENT && dn3fx_fx_head != world)
			DN3FX_QueueRemove(dn3fx_fx_head);
	}

	e = spawn();
	e.classname = "dn3fx_local";
	e.drawmask = MASK_ENGINE;
	e.dn3fx_born = time;
	e.dn3fx_is_decal = is_decal;
	e.alpha = 1.0;
	e.scale = 1.0;

	if (is_decal)
	{
		e.dn3fx_qprev = dn3fx_decal_tail;
		e.dn3fx_qnext = world;
		if (dn3fx_decal_tail)
			dn3fx_decal_tail.dn3fx_qnext = e;
		else
			dn3fx_decal_head = e;
		dn3fx_decal_tail = e;
		dn3fx_decal_count = dn3fx_decal_count + 1;
	}
	else
	{
		e.dn3fx_qprev = dn3fx_fx_tail;
		e.dn3fx_qnext = world;
		if (dn3fx_fx_tail)
			dn3fx_fx_tail.dn3fx_qnext = e;
		else
			dn3fx_fx_head = e;
		dn3fx_fx_tail = e;
		dn3fx_fx_count = dn3fx_fx_count + 1;
	}
	return e;
};

void() DN3FX_DecalThink =
{
	local float age, k;

	age = time - self.dn3fx_born;
	if (age < self.dn3fx_life)
	{
		self.nextthink = self.dn3fx_born + self.dn3fx_life;
		return;
	}
	k = 1.0 - (age - self.dn3fx_life) / self.dn3fx_fade;
	if (k <= 0.03)
	{
		DN3FX_QueueRemove(self);
		return;
	}
	self.alpha = k * 0.92;
	self.nextthink = time + 0.05;
};

void(vector pos, vector n, float sz) DN3FX_SpawnSurfaceBlood =
{
	local entity d;
	local float fidx;

	// Avoid duplicate stacking on the exact same spot
	d = dn3fx_decal_tail;
	if (d != world && vlen(d.origin - pos) < 6.0 && (time - d.dn3fx_born) < 0.25)
		return;

	d = DN3FX_Alloc(TRUE);
	d.dn3fx_life = DN3FX_DECAL_LIFE + random() * 6.0;
	d.dn3fx_fade = DN3FX_DECAL_FADE;
	d.alpha = 0.96;
	d.colormod = '1.35 1.15 1.15';

	if (n_z > 0.65)
	{
		setmodel(d, "progs/dn3fx_pool.md3");
		fidx = floor(random() * 5.0);
		if (fidx > 4)
			fidx = 4;
		d.frame = fidx;
		d.angles_x = 0;
		d.angles_y = random() * 360.0;
		d.angles_z = 0;
		d.scale = (0.75 + random() * 0.45) * sz;
		setorigin(d, pos + n * (0.35 + random() * 0.25));
	}
	else
	{
		setmodel(d, "progs/dn3fx_wallsplat.md3");
		fidx = floor(random() * 4.0);
		if (fidx > 3)
			fidx = 3;
		d.frame = fidx;
		d.angles = vectoangles(n);
		d.scale = (0.85 + random() * 0.45) * sz;
		setorigin(d, pos + n * (0.45 + random() * 0.30));
	}

	d.think = DN3FX_DecalThink;
	d.nextthink = d.dn3fx_born + d.dn3fx_life;
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

void() DN3FX_DropletThink =
{
	local float dt, age, f;
	local vector next_pos;

	dt = time - self.dn3fx_last;
	if (dt <= 0)
		dt = 0.025;
	self.dn3fx_last = time;
	age = time - self.dn3fx_born;

	// Splashed state on floor
	if (self.dn3fx_kind > 0)
	{
		if (age >= self.dn3fx_life)
		{
			DN3FX_QueueRemove(self);
			return;
		}
		f = floor((age - self.dn3fx_kind) * 18.0);
		if (f > 5)
			f = 5;
		self.frame = 2 + f;
		f = 1.0 - (age - self.dn3fx_kind) / 0.35;
		if (f < 0.05)
			f = 0.05;
		self.alpha = f;
		self.nextthink = time + 0.025;
		return;
	}

	if (age > 2.2)
	{
		DN3FX_QueueRemove(self);
		return;
	}

	self.velocity_z = self.velocity_z - 540.0 * dt;
	next_pos = self.origin + self.velocity * dt;
	traceline(self.origin, next_pos, TRUE, world);
	if (trace_fraction < 1.0)
	{
		if (trace_plane_normal_z > 0.65)
		{
			setorigin(self, trace_endpos + '0 0 2');
			self.velocity = '0 0 0';
			self.dn3fx_kind = age;
			self.dn3fx_life = age + 0.32;
			self.frame = 2;
			DN3FX_SpawnSurfaceBlood(trace_endpos, trace_plane_normal, self.dn3fx_splat_s);
			self.nextthink = time + 0.025;
			return;
		}
		if (trace_plane_normal_z > -0.65)
			DN3FX_SpawnSurfaceBlood(trace_endpos, trace_plane_normal, self.dn3fx_splat_s * 0.85);
		DN3FX_QueueRemove(self);
		return;
	}

	setorigin(self, next_pos);
	self.frame = (self.velocity_z > -60.0) ? 0 : 1;
	self.nextthink = time + 0.025;
};

void() DN3FX_GibThink =
{
	local float dt, age, f;
	local vector next_pos;
	local float vn;

	dt = time - self.dn3fx_last;
	if (dt <= 0)
		dt = 0.025;
	self.dn3fx_last = time;
	age = time - self.dn3fx_born;

	if (age >= self.dn3fx_life)
	{
		DN3FX_QueueRemove(self);
		return;
	}

	if (age > (self.dn3fx_life - self.dn3fx_fade))
	{
		f = (self.dn3fx_life - age) / self.dn3fx_fade;
		if (f < 0.03)
			f = 0.03;
		self.alpha = f;
	}

	if (self.dn3fx_bounce < 4)
	{
		self.velocity_z = self.velocity_z - 620.0 * dt;
		next_pos = self.origin + self.velocity * dt;
		traceline(self.origin, next_pos, TRUE, world);
		if (trace_fraction < 1.0)
		{
			if (trace_plane_normal_z > 0.65 && vlen(self.velocity) < 95.0)
			{
				setorigin(self, trace_endpos + '0 0 2');
				self.velocity = '0 0 0';
				self.dn3fx_bounce = 99;
				if (self.dn3fx_fcnt > 1)
					self.frame = self.dn3fx_f0 + 4;
				DN3FX_SpawnSurfaceBlood(trace_endpos, trace_plane_normal, 0.65 * self.dn3fx_splat_s);
			}
			else
			{
				vn = self.velocity * trace_plane_normal;
				self.velocity = (self.velocity - 1.55 * vn * trace_plane_normal) * 0.65;
				setorigin(self, trace_endpos + trace_plane_normal * 2.0);
				self.dn3fx_bounce = self.dn3fx_bounce + 1;
				if (self.dn3fx_bounce == 1)
					DN3FX_SpawnSurfaceBlood(trace_endpos, trace_plane_normal, 0.55 * self.dn3fx_splat_s);
			}
		}
		else
		{
			setorigin(self, next_pos);
			self.angles = self.angles + self.dn3fx_avel * dt;
		}
	}

	if (self.dn3fx_fcnt > 1 && self.dn3fx_bounce < 99)
	{
		f = floor(age * 10.0);
		f = f - floor(f / 4.0) * 4.0;
		self.frame = self.dn3fx_f0 + f;
	}

	self.nextthink = time + 0.025;
};

entity(string mdl, vector org, vector vel, float sc, float al, float eff, float life, float fade, float f0, float fcnt, float rate, float grav, float grow) DN3FX_SpawnSprite =
{
	local entity e;

	e = DN3FX_Alloc(FALSE);
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

void(vector org, vector dir, float s) DN3FX_RunBloodHit =
{
	local vector d, vel, jit;
	local float i, cnt;

	d = (vlen(dir) > 0.01) ? normalize(dir) : '0 0 1';

	// Crisp fullbright DN3DooM blood splashes (BLUDA0..D0)
	for (i = 0; i < 3; i = i + 1)
	{
		jit_x = DN3FX_CRand() * 9.0;
		jit_y = DN3FX_CRand() * 9.0;
		jit_z = DN3FX_CRand() * 9.0;
		DN3FX_SpawnSprite(
			"progs/dn3fx_bloodpuff.spr32",
			org + jit,
			d * (16.0 + i * 12.0) + '0 0 16',
			(1.50 + random() * 0.45) * s,
			1.0,
			DN3FX_EF_FULLBRIGHT,
			0.46,
			0.16,
			0, 4, 9.0, 0, 0.55 * s
		);
	}

	// Falling fullbright blood droplets (GIB6) that paint floor pools & wall splatters
	cnt = (s >= 1.05) ? 8 : 5;
	for (i = 0; i < cnt; i = i + 1)
	{
		local entity dr;
		dr = DN3FX_Alloc(FALSE);
		setmodel(dr, "progs/dn3fx_blooddrop.spr32");
		setorigin(dr, org);
		vel_x = d_x * (65.0 + random() * 90.0) + DN3FX_CRand() * 105.0;
		vel_y = d_y * (65.0 + random() * 90.0) + DN3FX_CRand() * 105.0;
		vel_z = d_z * 45.0 + 75.0 + random() * 110.0;
		dr.velocity = vel;
		dr.effects = DN3FX_EF_FULLBRIGHT;
		dr.scale = (0.95 + random() * 0.40) * s;
		dr.dn3fx_splat_s = s * 1.10;
		dr.dn3fx_kind = 0;
		dr.dn3fx_last = time;
		dr.think = DN3FX_DropletThink;
		dr.nextthink = time + 0.025;
	}

	// Trace behind/outward from hit for crisp wall/floor blood splat
	traceline(org, org - d * 140.0, TRUE, world);
	if (trace_fraction < 1.0)
		DN3FX_SpawnSurfaceBlood(trace_endpos, trace_plane_normal, s * 1.15);
	else
	{
		traceline(org, org + d * 140.0, TRUE, world);
		if (trace_fraction < 1.0)
			DN3FX_SpawnSurfaceBlood(trace_endpos, trace_plane_normal, s * 1.15);
	}
	traceline(org, org - '0 0 96', TRUE, world);
	if (trace_fraction < 1.0 && trace_plane_normal_z > 0.65)
		DN3FX_SpawnSurfaceBlood(trace_endpos, trace_plane_normal, s * 1.05);
};

void(vector org, float s) DN3FX_RunGibBurst =
{
	local float i, kind;
	local vector vel, p;
	local entity g;

	// Quad fullbright blood splashes (BLUDA0..D0)
	for (i = 0; i < 4; i = i + 1)
	{
		p = org;
		p_x = p_x + DN3FX_CRand() * 16.0;
		p_y = p_y + DN3FX_CRand() * 16.0;
		p_z = p_z + 6.0 + random() * 16.0;
		DN3FX_SpawnSprite(
			"progs/dn3fx_bloodpuff.spr32",
			p,
			'0 0 24',
			(1.85 + random() * 0.55) * s,
			1.0,
			DN3FX_EF_FULLBRIGHT,
			0.54,
			0.18,
			0, 4, 8.5, 0, 0.65 * s
		);
	}

	// 2D Duke gore chunks (GIB1..5)
	for (i = 0; i < 10; i = i + 1)
	{
		g = DN3FX_Alloc(FALSE);
		setmodel(g, "progs/dn3fx_gore2d.spr32");
		setorigin(g, org + '0 0 10');
		vel_x = DN3FX_CRand() * 230.0;
		vel_y = DN3FX_CRand() * 230.0;
		vel_z = 130.0 + random() * 195.0;
		g.velocity = vel;
		g.effects = DN3FX_EF_FULLBRIGHT;
		g.scale = (1.15 + random() * 0.50) * s;
		kind = floor(random() * 5.0);
		if (kind > 4) kind = 4;
		g.dn3fx_f0 = kind * 5;
		g.dn3fx_fcnt = 5;
		g.frame = g.dn3fx_f0;
		g.dn3fx_life = 7.5 + random() * 3.0;
		g.dn3fx_fade = 2.0;
		g.dn3fx_splat_s = s;
		g.dn3fx_last = time;
		g.think = DN3FX_GibThink;
		g.nextthink = time + 0.025;
	}

	// 3D tumbling flesh1.md3 chunks
	for (i = 0; i < 6; i = i + 1)
	{
		g = DN3FX_Alloc(FALSE);
		setmodel(g, "progs/dn3fx_flesh1.md3");
		setorigin(g, org + '0 0 12');
		vel_x = DN3FX_CRand() * 210.0;
		vel_y = DN3FX_CRand() * 210.0;
		vel_z = 150.0 + random() * 185.0;
		g.velocity = vel;
		g.angles_x = random() * 360.0;
		g.angles_y = random() * 360.0;
		g.dn3fx_avel_x = DN3FX_CRand() * 380.0;
		g.dn3fx_avel_y = DN3FX_CRand() * 380.0;
		g.dn3fx_avel_z = DN3FX_CRand() * 380.0;
		g.effects = DN3FX_EF_FULLBRIGHT;
		g.scale = (2.2 + random() * 1.1) * s;
		g.dn3fx_fcnt = 1;
		g.dn3fx_life = 8.5 + random() * 3.0;
		g.dn3fx_fade = 2.0;
		g.dn3fx_splat_s = s;
		g.dn3fx_last = time;
		g.think = DN3FX_GibThink;
		g.nextthink = time + 0.025;
	}

	// Extra fullbright blood droplets
	for (i = 0; i < 10; i = i + 1)
	{
		local entity dr;
		dr = DN3FX_Alloc(FALSE);
		setmodel(dr, "progs/dn3fx_blooddrop.spr32");
		setorigin(dr, org + '0 0 12');
		vel_x = DN3FX_CRand() * 200.0;
		vel_y = DN3FX_CRand() * 200.0;
		vel_z = 110.0 + random() * 180.0;
		dr.velocity = vel;
		dr.effects = DN3FX_EF_FULLBRIGHT;
		dr.scale = (1.0 + random() * 0.45) * s;
		dr.dn3fx_splat_s = s * 1.25;
		dr.dn3fx_kind = 0;
		dr.dn3fx_last = time;
		dr.think = DN3FX_DropletThink;
		dr.nextthink = time + 0.025;
	}

	// Immediate floor blood pool under gib origin + 4 wall traces
	traceline(org + '0 0 8', org - '0 0 96', TRUE, world);
	if (trace_fraction < 1.0)
		DN3FX_SpawnSurfaceBlood(trace_endpos, trace_plane_normal, s * 1.35);

	for (i = 0; i < 4; i = i + 1)
	{
		vel_x = DN3FX_CRand();
		vel_y = DN3FX_CRand();
		vel_z = DN3FX_CRand() * 0.25;
		if (vlen(vel) > 0.05)
		{
			vel = normalize(vel) * 140.0;
			traceline(org + '0 0 12', org + '0 0 12' + vel, TRUE, world);
			if (trace_fraction < 1.0)
				DN3FX_SpawnSurfaceBlood(trace_endpos, trace_plane_normal, s * 1.10);
		}
	}
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

	if (kind == DN3FX_BLOOD_HIT)
		DN3FX_RunBloodHit(org, dir, sc);
	else if (kind == DN3FX_GIB_BURST)
		DN3FX_RunGibBurst(org, sc);
	else if (kind == DN3FX_EXPLODE)
		DN3FX_RunExplode(org, sc);
	else if (kind == DN3FX_FIRE_BURST)
		DN3FX_RunFireBurst(org, dir, sc);
	else if (kind == DN3FX_BULLET_PUFF)
		DN3FX_RunBulletPuff(org, dir, sc);
};
