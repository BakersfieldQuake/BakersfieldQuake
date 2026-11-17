/*
showcase_movie.qc — BakersfieldQuake Cinematic Showcase Director (isolated build -> progs_showcase.dat)
Map: bakersfielddowntown.bsp

4-Scene Storyboard (~36.5s):
  1 ( 0.0s ..  7.6s) Historic Fox Theater: Rob Head, Wheelman & Green Man float out of the Clock Tower down to H St.
  2 ( 7.6s .. 17.5s) Mega Man Tank shoots down 20th St -> follow rocket -> banks onto Eye St -> slams Sandrini's & explodes!
  3 (17.5s .. 28.5s) John Bird cruises down 19th St -> goes down & shoots Eric Cannon at Chester Ave -> ICBM launch & nuke!
  4 (28.5s .. 36.5s) Suddenly 100 Green Men on their little carts drive all over Chester Ave & 19th St -> fade to black!
*/

.float	sc_tag;
.float	sc_kind;
.float	sc_born;
.float	sc_spd;
.float	sc_dur;
.float	sc_phase;
.float	sc_yaw;
.float	sc_turn;
.float	sc_stunt;
.float	sc_stunt_t;
.vector	sc_p0;
.vector	sc_p1;
.vector	sc_vel;
.entity	sc_sub;

entity	sc_dir;
entity	sc_cam;
entity	sc_bgm;
float	sc_t0;
float	sc_ev;
float	sc_bgm_on;
float	sc_cam_fixed;
float	sc_stopped;
float	sc_quitted;

vector	sc_cam_pos;
vector	sc_cam_ang;
float	sc_fade_alpha;

// Key actors
entity	sc_rob;
entity	sc_wheel;
entity	sc_green;
entity	sc_tank;
entity	sc_turret;
entity	sc_rocket;
entity	sc_bird;
entity	sc_ec_base;
entity	sc_ec_yoke;
entity	sc_ec_tube;
entity	sc_ec_shot;

// Particle effect IDs
float	sc_fx_fd_trail;
float	sc_fx_r_trail;
float	sc_fx_mm_trail;
float	sc_fx_mm_boom;
float	sc_fx_nuke_trail;
float	sc_fx_nuke_flash;
float	sc_fx_nuke_shock;
float	sc_fx_nuke_mush;
float	sc_fx_smoke;

float(float u) SC_Clamp01 =
{
	if (u < 0) return 0;
	if (u > 1) return 1;
	return u;
};

float(float u) SC_Smooth =
{
	u = SC_Clamp01 (u);
	return u * u * (3 - 2 * u);
};

float(float x) SC_Sin =
{
	local float r;
	r = sin (x);
	return r;
};

float(float x) SC_Cos =
{
	local float r;
	r = cos (x);
	return r;
};

vector(vector a, vector b, float u) SC_LerpVec =
{
	local float s;
	s = SC_Smooth (u);
	return a + (b - a) * s;
};

vector(vector a, vector b, float u) SC_LinVec =
{
	u = SC_Clamp01 (u);
	return a + (b - a) * u;
};

vector(vector p0, vector p1, vector p2, float u) SC_QuadBezier =
{
	local float inv;
	u = SC_Clamp01 (u);
	inv = 1 - u;
	return p0 * (inv * inv) + p1 * (2 * inv * u) + p2 * (u * u);
};

vector(vector from, vector to) SC_LookAngles =
{
	local vector a;
	local float px;

	a = vectoangles (to - from);
	px = a_x;
	if (px > 180)
		px = px - 360;
	a_x = 0 - px;
	a_z = 0;
	return a;
};

float(float a) SC_NormAng =
{
	while (a >= 360) a = a - 360;
	while (a < 0) a = a + 360;
	return a;
};

void(string samp, float vol) SC_Cue =
{
	local entity p;
	p = find (world, classname, "player");
	if (p)
		sound (p, CHAN_AUTO, samp, vol, ATTN_NONE);
};

void(vector org) SC_BoomTE =
{
	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, org_x);
	WriteCoord (MSG_BROADCAST, org_y);
	WriteCoord (MSG_BROADCAST, org_z);
};

// ---------------------------------------------------------------- Precache
void() Showcase_Precache =
{
	precache_model ("progs/spike.mdl");
	precache_model ("progs/missile.mdl");
	precache_model ("progs/s_explod.spr");
	precache_model ("progs/s_explodbig.spr");
	precache_model ("progs/ring_shockwave.mdl");

	// Scene 1: Rob Head, Wheelman & Green Man
	precache_model ("progs/floathead.mdl");
	precache_model ("progs/wheelman_3d_01_roller.md3");
	precache_model ("progs/wheelman.spr32");
	precache_model ("progs/greensuit_wheelman.spr32");

	// Scene 2: Mega Man Tank & Explosion
	precache_model ("progs/mm_tank_v1.md3");
	precache_model ("progs/mm_tank_turret_v1.md3");
	precache_model ("progs/mm_tank_bar.md3");
	precache_model ("progs/mm_explode.md3");
	precache_model ("progs/mm_tank_wheel_debris.md3");

	// Scene 3: John Bird & Eric Cannon
	precache_model ("progs/john_bird_head.md3");
	precache_model ("progs/john_bird_feather.md3");
	precache_model ("progs/eric_tripod.md3");
	precache_model ("progs/eric_yoke.md3");
	precache_model ("progs/eric_cannon.md3");

	// Music & FX
	precache_sound ("cdtracks/track013.ogg");
	precache_sound ("floathead/sight1.wav");
	precache_sound ("floathead/idle.wav");
	precache_sound ("funny/imfloating.wav");
	precache_sound ("funny/wewe.wav");
	precache_sound ("funny/heh.wav");
	precache_sound ("vehicles/tire_squeal.wav");
	precache_sound ("vehicles/horn.wav");
	precache_sound ("vehicles/idle_coupe.wav");
	precache_sound ("greenjar/mini_giggle1.wav");
	precache_sound ("greenjar/mini_giggle3.wav");
	precache_sound ("greenjar/mini_boing.wav");
	precache_sound ("friends/johnnnny.wav");
	precache_sound ("larry/octogood.wav");
	precache_sound ("mm_tank/pack1/engine.wav");
	precache_sound ("mm_tank/pack6/fire.wav");
	precache_sound ("mm_tank/pack10/boom.wav");
	precache_sound ("weapons/r_exp3.wav");
	precache_sound ("weapons/rocket1i.wav");
	precache_sound ("weapons/explodedist.wav");
	precache_sound ("afrit/body_explode.wav");
	precache_sound ("john_bird/jv_fly03.wav");
	precache_sound ("john_bird/flap1.wav");
	precache_sound ("john_bird/flap2.wav");
	precache_sound ("john_bird/flap3.wav");
	precache_sound ("john_bird/feather_hit.wav");
	precache_sound ("john_bird/shootdown.wav");
	precache_sound ("eric_cannon/windup.wav");
	precache_sound ("eric_cannon/canislupusfantasy2.wav");
	precache_sound ("eric_cannon/fire_boom.wav");
	precache_sound ("eric_cannon/dive_whistle.wav");
	precache_sound ("eric_cannon/doppler_scream.wav");
	precache_sound ("eric_cannon/nuke_boom.wav");
	precache_sound ("lan/pc_boom.wav");

	sc_fx_fd_trail = particleeffectnum ("fd_trail");
	sc_fx_r_trail = particleeffectnum ("rocket_trail");
	sc_fx_mm_trail = particleeffectnum ("mm_tank_bar_trail");
	sc_fx_mm_boom = particleeffectnum ("mm_tank_bar_boom");
	sc_fx_nuke_trail = particleeffectnum ("eric_nuke_trail");
	sc_fx_nuke_flash = particleeffectnum ("eric_nuke_flash");
	sc_fx_nuke_shock = particleeffectnum ("eric_nuke_shock");
	sc_fx_nuke_mush = particleeffectnum ("eric_nuke_mushroom");
	sc_fx_smoke = particleeffectnum ("TE_GUNSHOT");
};

// ---------------------------------------------------------------- Sprite Customize (8-dir Seated Low-Rider Cart)
float() SC_GreenCustomize =
{
	local float rel, d, k, base;
	local vector delta;

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 24');
	rel = vectoyaw (delta) - self.angles_y;
	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 45 + 0.5);
	if (d >= 8)
		d = 0;

	if (self.sc_stunt > 0 && time < self.sc_stunt_t)
	{
		// Wheelie burnout battle-cry (frames 144..175)
		k = floor (time * 10 + self.sc_phase);
		k = k - 4 * floor (k / 4);
		self.frame = 144 + d * 4 + k;
		return TRUE;
	}
	base = 0;
	if (self.sc_kind == 1)
		base = 32; // Ab-Roller Torpedo Charge!
	k = floor (time * 12 + self.sc_phase);
	k = k - 4 * floor (k / 4);
	self.frame = base + d * 4 + k;
	return TRUE;
};

float() SC_WheelCustomize =
{
	local float rel, d, k;
	local vector delta;

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 28');
	rel = vectoyaw (delta) - self.angles_y;
	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 45 + 0.5);
	if (d >= 8)
		d = 0;
	k = floor (time * 18 + self.sc_phase);
	k = k - 12 * floor (k / 12);
	self.frame = 8 + d * 12 + k;
	return TRUE;
};

// ---------------------------------------------------------------- Cleanup
void() SC_ClearStage =
{
	local entity e, nxt;

	sc_rob = world;
	sc_wheel = world;
	sc_green = world;
	sc_tank = world;
	sc_turret = world;
	sc_rocket = world;
	sc_bird = world;
	sc_ec_base = world;
	sc_ec_yoke = world;
	sc_ec_tube = world;
	sc_ec_shot = world;

	e = nextent (world);
	while (e)
	{
		nxt = nextent (e);
		if (e.sc_tag == 1)
			remove (e);
		e = nxt;
	}
};

// Suppress existing static ambient NPCs/vehicles near showcase hero zones so the frame reads ultra clean
void() SC_CleanWorldClutter =
{
	local entity e, nxt;
	e = nextent (world);
	while (e)
	{
		nxt = nextent (e);
		if (e != sc_dir && e != sc_cam && e != sc_bgm && e.classname != "player" && e.solid != SOLID_BSP)
		{
			if (e.classname == "misc_eric_cannon" || e.classname == "ec_yoke" || e.classname == "ec_tube"
			 || e.classname == "misc_vehicle_johnbird" || e.classname == "npc_crowd"
			 || e.classname == "npc_greensuit_wheelman" || e.classname == "npc_robeguy"
			 || e.classname == "misc_mm_tank" || substring (e.classname, 0, 12) == "misc_vehicle")
			{
				remove (e);
			}
		}
		e = nxt;
	}
};

// ---------------------------------------------------------------- Camera Lockstep
void(entity p) SC_EnsureCam =
{
	if (!sc_cam)
	{
		sc_cam = spawn ();
		sc_cam.classname = "sc_camera";
		sc_cam.movetype = MOVETYPE_NONE;
		sc_cam.solid = SOLID_NOT;
		setmodel (sc_cam, "progs/spike.mdl");
		sc_cam.scale = 0.01;
		sc_cam.alpha = 0.01;
		setsize (sc_cam, '0 0 0', '0 0 0');
		setorigin (sc_cam, sc_cam_pos);
	}
	if (!sc_bgm)
	{
		sc_bgm = spawn ();
		sc_bgm.classname = "sc_bgm";
		sc_bgm.movetype = MOVETYPE_NONE;
		sc_bgm.solid = SOLID_NOT;
		setmodel (sc_bgm, "progs/spike.mdl");
		sc_bgm.scale = 0.01;
		sc_bgm.alpha = 0.01;
		setsize (sc_bgm, '0 0 0', '0 0 0');
		setorigin (sc_bgm, sc_cam_pos);
	}
	if (p.clientcamera != sc_cam)
	{
		p.clientcamera = sc_cam;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);
		WriteEntity (MSG_ONE, sc_cam);
	}
};

float() Showcase_PlayerHook =
{
	self.movetype = MOVETYPE_NONE;
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.flags = self.flags | FL_NOTARGET;
	self.health = 100;
	self.armorvalue = 0;
	self.items = 0;
	self.weapon = 0;
	self.model = "";
	self.modelindex = 0;
	self.weaponmodel = "";
	self.alpha = 0.01;
	self.effects = EF_NODRAW;
	self.velocity = '0 0 0';
	self.punchangle = '0 0 0';
	self.viewzoom = 1;
	setorigin (self, sc_cam_pos - self.view_ofs);
	self.angles = sc_cam_ang;
	self.v_angle = sc_cam_ang;
	return TRUE;
};

void(entity p) Showcase_SyncPlayer =
{
	if (!p)
		return;
	SC_EnsureCam (p);
	setorigin (sc_cam, sc_cam_pos);
	sc_cam.angles = sc_cam_ang;
	if (sc_bgm)
		setorigin (sc_bgm, sc_cam_pos);

	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.takedamage = DAMAGE_NO;
	p.flags = p.flags | FL_NOTARGET;
	p.model = "";
	p.modelindex = 0;
	p.weaponmodel = "";
	p.alpha = 0.01;
	p.effects = EF_NODRAW;
	setorigin (p, sc_cam_pos - p.view_ofs);
	p.angles = sc_cam_ang;
	p.v_angle = sc_cam_ang;
	if (!sc_cam_fixed)
	{
		sc_cam_fixed = TRUE;
		p.fixangle = TRUE;
	}
};

// ---------------------------------------------------------------- Scene FX & Helpers
void(vector org, float count, float boost) SC_DropFeathers =
{
	local float i;
	local entity f;
	i = 0;
	while (i < count)
	{
		f = spawn ();
		f.sc_tag = 1;
		f.classname = "sc_feather";
		f.movetype = MOVETYPE_TOSS;
		f.solid = SOLID_NOT;
		setmodel (f, "progs/john_bird_feather.md3");
		f.scale = 1.15 + random () * 0.45;
		f.gravity = 0.25;
		f.velocity_x = crandom () * 210 * boost;
		f.velocity_y = crandom () * 210 * boost;
		f.velocity_z = (80 + random () * 165) * boost;
		f.avelocity = '240 340 260';
		setsize (f, '0 0 0', '0 0 0');
		setorigin (f, org + '0 0 18');
		f.think = SUB_Remove;
		f.nextthink = time + 2.8;
		i = i + 1;
	}
};

void() SC_MMDomeThink =
{
	if (time >= self.ltime)
	{
		remove (self);
		return;
	}
	self.frame = floor ((1 - (self.ltime - time) / 1.05) * 15);
	if (self.frame > 15) self.frame = 15;
	self.scale = self.scale + 0.16;
	self.nextthink = time + 0.03;
};

void(vector org, float sc0) SC_SpawnMMDome =
{
	local entity d;
	d = spawn ();
	d.sc_tag = 1;
	d.movetype = MOVETYPE_NONE;
	d.solid = SOLID_NOT;
	setmodel (d, "progs/mm_explode.md3");
	d.scale = sc0;
	d.effects = EF_FULLBRIGHT;
	setsize (d, '0 0 0', '0 0 0');
	setorigin (d, org);
	d.ltime = time + 1.05;
	d.think = SC_MMDomeThink;
	d.nextthink = time + 0.03;
};

void() SC_NukeRingThink =
{
	local float el, u;
	el = time - self.sc_born;
	if (el > 1.6)
	{
		remove (self);
		return;
	}
	u = el / 1.6;
	self.scale = 1.6 + u * 26.0;
	self.alpha = 0.92 * (1 - u);
	self.nextthink = time + 0.02;
};

void() SC_NukeFireballThink =
{
	local float el;
	el = time - self.sc_born;
	if (el > 1.6)
	{
		remove (self);
		return;
	}
	self.frame = floor (el * 4.5);
	if (self.frame > 6) self.frame = 6;
	self.scale = 5.5 + el * 10.5;
	self.alpha = 0.95 * (1 - el / 1.6);
	self.nextthink = time + 0.03;
};

void() SC_NukeCloudThink =
{
	local float el;
	local vector p;
	el = time - self.sc_born;
	if (el > 2.4)
	{
		remove (self);
		return;
	}
	p = self.origin + '0 0 1' * (el * 260);
	if (sc_fx_nuke_mush > 0)
	{
		pointparticles (sc_fx_nuke_mush, p, '0 0 140', 2);
		pointparticles (sc_fx_nuke_mush, self.origin + '0 0 1' * (el * 120), '0 0 80', 1);
	}
	self.nextthink = time + 0.06;
};

void(vector org) SC_DetonateNuke =
{
	local entity ring, fb, cloud;

	SC_BoomTE (org + '0 0 24');
	if (sc_fx_nuke_flash > 0) pointparticles (sc_fx_nuke_flash, org + '0 0 36', '0 0 0', 2);
	if (sc_fx_nuke_shock > 0) pointparticles (sc_fx_nuke_shock, org + '0 0 18', '0 0 0', 2);
	if (sc_fx_nuke_mush > 0) pointparticles (sc_fx_nuke_mush, org + '0 0 42', '0 0 180', 3);

	ring = spawn ();
	ring.sc_tag = 1;
	ring.movetype = MOVETYPE_NONE;
	ring.solid = SOLID_NOT;
	ring.sc_born = time;
	setmodel (ring, "progs/ring_shockwave.mdl");
	ring.effects = EF_FULLBRIGHT;
	ring.scale = 1.6;
	setorigin (ring, org + '0 0 10');
	ring.think = SC_NukeRingThink;
	ring.nextthink = time + 0.02;

	fb = spawn ();
	fb.sc_tag = 1;
	fb.movetype = MOVETYPE_NONE;
	fb.solid = SOLID_NOT;
	fb.sc_born = time;
	setmodel (fb, "progs/s_explodbig.spr");
	fb.effects = EF_FULLBRIGHT;
	fb.scale = 5.5;
	setorigin (fb, org + '0 0 90');
	fb.think = SC_NukeFireballThink;
	fb.nextthink = time + 0.02;

	cloud = spawn ();
	cloud.sc_tag = 1;
	cloud.movetype = MOVETYPE_NONE;
	cloud.solid = SOLID_NOT;
	cloud.sc_born = time;
	setmodel (cloud, "progs/spike.mdl");
	cloud.scale = 0.01;
	cloud.alpha = 0.01;
	setorigin (cloud, org + '0 0 24');
	cloud.think = SC_NukeCloudThink;
	cloud.nextthink = time + 0.02;

	SC_Cue ("eric_cannon/nuke_boom.wav", 1.0);
	SC_Cue ("weapons/explodedist.wav", 0.90);
	SC_Cue ("lan/pc_boom.wav", 0.85);
};

// ---------------------------------------------------------------- Green Man 100-Cart Swarm Thinker
void() SC_CartSwarmThink =
{
	local float dt, turn_amt;
	local vector dir, nxt, p_snap;

	dt = 0.04;
	self.sc_yaw = self.sc_yaw + (self.sc_turn + SC_Sin (time * 3.1 + self.sc_phase) * 72) * dt;
	self.sc_yaw = SC_NormAng (self.sc_yaw);
	makevectors ('0 1 0' * self.sc_yaw);
	dir = v_forward;

	nxt = self.origin + dir * (self.sc_spd * dt);

	// Keep inside wide open Chester Ave (-520..+240 x -2960..-1100) + 19th St cross-arm (-1100..+500 x -2480..-2200)
	if (nxt_y < -2500 || nxt_y > -2180)
	{
		if (nxt_x < -465 || nxt_x > 195)
		{
			self.sc_yaw = SC_NormAng (self.sc_yaw + 145 + random () * 60);
			nxt = self.origin;
		}
	}
	if (nxt_x < -1050 || nxt_x > 460 || nxt_y < -2940 || nxt_y > -1150)
	{
		self.sc_yaw = SC_NormAng (self.sc_yaw + 145 + random () * 60);
		nxt = self.origin;
	}

	// Solid building/curb wall bounce check
	traceline (self.origin + '0 0 26', nxt + '0 0 26' + dir * 24, TRUE, self);
	if (trace_fraction < 1 && trace_plane_normal_z < 0.7)
	{
		self.sc_yaw = SC_NormAng (vectoyaw (trace_plane_normal) + crandom () * 35);
		nxt = self.origin;
	}

	// Snap cleanly onto asphalt/sidewalk surface so carts never float or sink
	traceline (nxt + '0 0 56', nxt - '0 0 96', TRUE, self);
	if (trace_fraction < 1 && !trace_startsolid)
		nxt_z = trace_endpos_z + 2;

	self.angles = '0 1 0' * self.sc_yaw;
	setorigin (self, nxt);

	// Occasional joyful wheelie hop!
	if (random () < 0.03 && time > self.sc_stunt_t + 0.8)
	{
		self.sc_stunt = 1;
		self.sc_stunt_t = time + 0.55;
	}
	self.nextthink = time + dt;
};

void(float idx) SC_SpawnCartGreenMan =
{
	local entity g;
	local float rx, ry, ang;
	local vector pos;

	g = spawn ();
	g.sc_tag = 1;
	g.classname = "sc_greensuit";
	g.movetype = MOVETYPE_NONE;
	g.solid = SOLID_NOT;
	setmodel (g, "progs/greensuit_wheelman.spr32");
	g.scale = 0.52;
	g.effects = EF_FULLBRIGHT;
	g.sc_kind = (idx - 3 * floor (idx / 3) == 0) ? 1 : 0; // Mix Low-Rider Cruise + Ab-Roller Torpedo Charge!
	g.sc_phase = random () * 12;
	g.sc_spd = 250 + random () * 210;
	g.sc_turn = crandom () * 48;
	g.customizeentityforclient = SC_GreenCustomize;
	setsize (g, '0 0 0', '0 0 0');

	// Distribute cleanly across Chester Ave dual roadways & 19th St cross-intersection
	if (idx < 75)
	{
		rx = -445 + random () * 620;
		ry = -2860 + random () * 1650;
		ang = (random () < 0.5 ? 90 : 270) + crandom () * 45;
	}
	else
	{
		rx = -980 + random () * 1380;
		ry = -2440 + random () * 200;
		ang = (random () < 0.5 ? 0 : 180) + crandom () * 35;
	}
	g.sc_yaw = SC_NormAng (ang);
	g.angles = '0 1 0' * g.sc_yaw;

	pos_x = rx;
	pos_y = ry;
	pos_z = 36;
	traceline (pos + '0 0 48', pos - '0 0 96', TRUE, g);
	if (trace_fraction < 1 && !trace_startsolid)
		pos_z = trace_endpos_z + 2;
	else
		pos_z = 2;
	setorigin (g, pos);

	g.think = SC_CartSwarmThink;
	g.nextthink = time + 0.02 + random () * 0.05;
};

// ---------------------------------------------------------------- Helper: Tank Rocket Curve Position
// Smooth continuous 3-leg street path:
//   20th & H St (-8625, 1800, 92) -> 20th & Eye (-4464, 1800, 155) -> Eye & Sandrini approach (-4464, 130, 88) -> Sandrini's (-4050, 115, 76)
vector(float rfrac) SC_TankRocketPos =
{
	local float k;
	if (rfrac < 0.62)
	{
		k = rfrac / 0.62;
		return SC_LinVec ('-8625 1800 84', '-4620 1800 158', k);
	}
	else if (rfrac < 0.72)
	{
		// Smooth banked 90-deg turn around 20th & Eye corner
		k = (rfrac - 0.62) / 0.10;
		return SC_QuadBezier ('-4620 1800 158', '-4464 1800 152', '-4464 1620 144', k);
	}
	else if (rfrac < 0.90)
	{
		k = (rfrac - 0.72) / 0.18;
		return SC_LinVec ('-4464 1620 144', '-4464 150 96', k);
	}
	else
	{
		k = (rfrac - 0.90) / 0.10;
		return SC_QuadBezier ('-4464 150 96', '-4320 115 86', '-4050 115 74', k);
	}
};

// ---------------------------------------------------------------- Helper: Eric Cannon ICBM Flight Position
vector(float efrac) SC_EricFlyPos =
{
	// Launches from (-180, -2340, 74) -> climbs skyward to (-180, -1720, 960) -> terminal dive to (-180, -1100, 28)
	return SC_QuadBezier ('-180 -2340 74', '-180 -1720 1880', '-180 -1100 28', efrac);
};

// ---------------------------------------------------------------- Master Director Tick (30..60 Hz)
void() Showcase_DirectorTick =
{
	local entity p;
	local float t, u, k, idx;
	local vector cpos, look, pos, pos2, dir;

	self.nextthink = time + 0.02;

	p = find (world, classname, "player");
	if (!p)
		return;

	if (sc_t0 == 0)
	{
		sc_t0 = time;
		SC_CleanWorldClutter ();
	}
	t = time - sc_t0;

	if (!sc_bgm_on)
	{
		sc_bgm_on = TRUE;
		SC_EnsureCam (p);
		sound (sc_bgm, 1, "cdtracks/track013.ogg", 0.36, ATTN_NONE);
	}

	// =========================================================================
	// SCENE 1 (0.0s .. 7.6s): FOX THEATER & CLOCK TOWER DROP
	// Rob Head, Wheelman & Green Man float out of Clock Tower down to H Street!
	// =========================================================================
	if (t < 7.6)
	{
		if (sc_ev < 1)
		{
			sc_ev = 1;
			SC_ClearStage ();

			// 1) Rob Head (floathead.mdl)
			sc_rob = spawn ();
			sc_rob.sc_tag = 1;
			sc_rob.movetype = MOVETYPE_NONE;
			sc_rob.solid = SOLID_NOT;
			setmodel (sc_rob, "progs/floathead.mdl");
			sc_rob.scale = 1.65;
			sc_rob.effects = EF_FULLBRIGHT;
			if (sc_fx_fd_trail > 0) sc_rob.traileffectnum = sc_fx_fd_trail;
			setsize (sc_rob, '0 0 0', '0 0 0');
			setorigin (sc_rob, '-9400 2525 910');

			// 2) Wheelman (classic 8-dir roller sprite — clean silhouette from every angle!)
			sc_wheel = spawn ();
			sc_wheel.sc_tag = 1;
			sc_wheel.movetype = MOVETYPE_NONE;
			sc_wheel.solid = SOLID_NOT;
			setmodel (sc_wheel, "progs/wheelman.spr32");
			sc_wheel.scale = 0.64;
			sc_wheel.effects = EF_FULLBRIGHT;
			sc_wheel.sc_phase = 0.8;
			sc_wheel.customizeentityforclient = SC_WheelCustomize;
			if (sc_fx_r_trail > 0) sc_wheel.traileffectnum = sc_fx_r_trail;
			setsize (sc_wheel, '0 0 0', '0 0 0');
			setorigin (sc_wheel, '-9400 2525 910');

			// 3) Green Man on cart (greensuit_wheelman.spr32)
			sc_green = spawn ();
			sc_green.sc_tag = 1;
			sc_green.movetype = MOVETYPE_NONE;
			sc_green.solid = SOLID_NOT;
			setmodel (sc_green, "progs/greensuit_wheelman.spr32");
			sc_green.scale = 0.64;
			sc_green.effects = EF_FULLBRIGHT;
			sc_green.sc_kind = 0;
			sc_green.sc_phase = 1.5;
			sc_green.customizeentityforclient = SC_GreenCustomize;
			setsize (sc_green, '0 0 0', '0 0 0');
			setorigin (sc_green, '-9400 2525 910');

			SC_Cue ("funny/imfloating.wav", 0.92);
		}
		if (t >= 2.2 && sc_ev < 2) { sc_ev = 2; SC_Cue ("floathead/sight1.wav", 0.90); }
		if (t >= 4.2 && sc_ev < 3) { sc_ev = 3; SC_Cue ("funny/wewe.wav", 0.90); }
		if (t >= 5.8 && sc_ev < 4) { sc_ev = 4; SC_Cue ("greenjar/mini_giggle1.wav", 0.88); }

		// Float progression:
		//   0.0..1.8s: Emerge right out of the open Clock Tower east dial (-9380 -> -9040, Z~860)
		//   1.8..6.3s: Glide smoothly downward onto clear H St crosswalk/sidewalk (-8785, 2500, 26)
		//   6.3..7.6s: Settle & bob in full view outside Fox marquee
		if (t < 1.8)
		{
			u = SC_Smooth (t / 1.8);
			pos = SC_LinVec ('-9380 2525 912', '-9040 2525 855', u);
			k = 0.15 + 0.55 * u;
		}
		else if (t < 6.3)
		{
			u = SC_Smooth ((t - 1.8) / 4.5);
			pos = SC_QuadBezier ('-9040 2525 855', '-8860 2510 470', '-8785 2500 26', u);
			k = 0.70 + 0.30 * u;
		}
		else
		{
			pos = '-8785 2500 26';
			k = 1.0;
		}

		// Fan the 3 trio characters side-by-side perpendicular (SW vs Center vs NE) to SE->NW camera view so NONE overlap!
		if (sc_rob)
		{
			pos2 = pos + ('-85 -98 46' * k) + '0 0 1' * (SC_Sin (time * 4.5) * 8);
			setorigin (sc_rob, pos2);
			sc_rob.angles_y = vectoyaw (sc_cam_pos - pos2);
			sc_rob.frame = floor (time * 14) - 6 * floor (floor (time * 14) / 6) + 8;
		}
		if (sc_wheel)
		{
			pos2 = pos + ('0 0 24' * k) + '0 0 1' * (SC_Sin (time * 4.5 + 1.8) * 6);
			setorigin (sc_wheel, pos2);
			sc_wheel.angles_y = vectoyaw (sc_cam_pos - pos2);
		}
		if (sc_green)
		{
			pos2 = pos + ('85 98 4' * k) + '0 0 1' * (SC_Sin (time * 4.5 + 3.6) * 6);
			setorigin (sc_green, pos2);
			sc_green.angles_y = vectoyaw (sc_cam_pos - pos2);
		}

		// Camera stays clear WEST/SOUTH of the 20th/H overhead traffic signal pole!
		if (t < 6.3)
		{
			u = t / 6.3;
			cpos = SC_LerpVec ('-8310 1910 220', '-8460 2190 88', u);
			look = SC_LerpVec ('-9160 2490 680', '-8820 2480 68', u);
		}
		else
		{
			u = (t - 6.3) / 1.3;
			cpos = SC_LerpVec ('-8460 2190 88', '-8490 2240 82', u);
			look = SC_LerpVec ('-8820 2480 68', '-8800 2490 54', u);
		}
	}

	// =========================================================================
	// SCENE 2 (7.6s .. 17.5s): MEGA MAN TANK -> FOLLOW ROCKET -> SANDRINI BOOM!
	// =========================================================================
	else if (t < 17.5)
	{
		if (sc_ev < 10)
		{
			sc_ev = 10;
			SC_ClearStage ();

			// Mega Man Tank chassis on 20th & H St facing due East down 20th St!
			sc_tank = spawn ();
			sc_tank.sc_tag = 1;
			sc_tank.movetype = MOVETYPE_NONE;
			sc_tank.solid = SOLID_NOT;
			setmodel (sc_tank, "progs/mm_tank_v1.md3");
			sc_tank.effects = EF_FULLBRIGHT;
			sc_tank.angles = '0 0 0';
			setsize (sc_tank, '0 0 0', '0 0 0');
			setorigin (sc_tank, '-8750 1800 2');

			sc_turret = spawn ();
			sc_turret.sc_tag = 1;
			sc_turret.movetype = MOVETYPE_NONE;
			sc_turret.solid = SOLID_NOT;
			setmodel (sc_turret, "progs/mm_tank_turret_v1.md3");
			sc_turret.effects = EF_FULLBRIGHT;
			sc_turret.angles = '12 0 0';
			setsize (sc_turret, '0 0 0', '0 0 0');
			setorigin (sc_turret, '-8750 1800 65');

			SC_Cue ("mm_tank/pack1/engine.wav", 0.90);
		}

		// 7.6s .. 9.85s: Tank rolls out & elevates cannon
		if (t < 9.85)
		{
			u = SC_Smooth ((t - 7.6) / 2.25);
			pos = SC_LinVec ('-8750 1800 2', '-8685 1800 2', u);
			if (sc_tank)
			{
				setorigin (sc_tank, pos);
				sc_tank.frame = floor (time * 16) - 16 * floor (floor (time * 16) / 16);
			}
			if (sc_turret)
			{
				setorigin (sc_turret, pos + '0 0 63');
				sc_turret.angles_x = 12 * SC_Smooth ((t - 8.2) / 1.2);
				sc_turret.frame = floor (time * 10) - 8 * floor (floor (time * 10) / 8);
			}
			cpos = SC_LerpVec ('-8450 1560 78', '-8520 1620 82', u);
			look = pos + '40 0 58';
		}
		// 9.85s .. 15.60s: Fire! Chase rocket all the way down 20th St -> Eye St -> Sandrini's!
		else if (t < 15.60)
		{
			if (sc_ev < 11)
			{
				sc_ev = 11;
				SC_Cue ("mm_tank/pack6/fire.wav", 1.0);
				SC_Cue ("weapons/r_exp3.wav", 0.80);

				sc_rocket = spawn ();
				sc_rocket.sc_tag = 1;
				sc_rocket.movetype = MOVETYPE_NONE;
				sc_rocket.solid = SOLID_NOT;
				setmodel (sc_rocket, "progs/mm_tank_bar.md3");
				sc_rocket.scale = 1.65;
				sc_rocket.effects = EF_FULLBRIGHT;
				if (sc_fx_mm_trail > 0) sc_rocket.traileffectnum = sc_fx_mm_trail;
				else if (sc_fx_r_trail > 0) sc_rocket.traileffectnum = sc_fx_r_trail;
				setsize (sc_rocket, '0 0 0', '0 0 0');
				setorigin (sc_rocket, '-8615 1800 84');
			}

			u = (t - 9.85) / 5.75; // 0..1 flight to Sandrini's
			pos = SC_TankRocketPos (u);
			pos2 = SC_TankRocketPos (u + 0.02);
			dir = normalize (pos2 - pos);

			if (sc_rocket)
			{
				setorigin (sc_rocket, pos);
				sc_rocket.angles = vectoangles (dir);
				sc_rocket.angles_z = time * 420;
				if (sc_fx_r_trail > 0)
					pointparticles (sc_fx_r_trail, pos - dir * 18, '0 0 0', 1);
			}
			if (sc_turret && t < 10.6)
			{
				k = floor (((t - 9.85) / 0.6) * 12);
				if (k > 11) k = 11;
				sc_turret.frame = 8 + k;
			}

			// Dynamic chase camera locked behind rocket shoulder (stays cleanly inside street corridors!)
			cpos = pos - dir * 165 + '0 0 42';
			if (u < 0.06)
				cpos = SC_LerpVec ('-8520 1620 82', cpos, u / 0.06);
			look = pos + dir * 180 + '0 0 -10';
		}
		// 15.60s .. 17.50s: Rocket slams Sandrini's -> HUGE EXPLOSION!
		else
		{
			if (sc_ev < 12)
			{
				sc_ev = 12;
				if (sc_rocket)
				{
					remove (sc_rocket);
					sc_rocket = world;
				}
				SC_BoomTE ('-4050 115 74');
				SC_SpawnMMDome ('-4050 115 56', 1.9);
				if (sc_fx_mm_boom > 0)
					pointparticles (sc_fx_mm_boom, '-4050 115 74', '0 0 0', 2);
				SC_Cue ("mm_tank/pack10/boom.wav", 1.0);
				SC_Cue ("weapons/explodedist.wav", 0.90);
				SC_Cue ("afrit/body_explode.wav", 0.90);
			}
			u = (t - 15.60) / 1.90;
			cpos = SC_LerpVec ('-4410 -40 94', '-4450 -130 112', u);
			look = SC_LerpVec ('-4050 115 74', '-4050 115 95', u);
		}
	}

	// =========================================================================
	// SCENE 3 (17.5s .. 28.5s): JOHN BIRD CRUISE -> GOES DOWN & SHOOTS ERIC CANNON -> NUKE!
	// =========================================================================
	else if (t < 28.5)
	{
		if (sc_ev < 20)
		{
			sc_ev = 20;
			SC_ClearStage ();

			// Winged Breezy-Hair John cruising East down 19th St toward Chester Ave
			sc_bird = spawn ();
			sc_bird.sc_tag = 1;
			sc_bird.movetype = MOVETYPE_NONE;
			sc_bird.solid = SOLID_NOT;
			setmodel (sc_bird, "progs/john_bird_head.md3");
			sc_bird.scale = 1.38;
			sc_bird.effects = EF_FULLBRIGHT;
			setsize (sc_bird, '0 0 0', '0 0 0');
			setorigin (sc_bird, '-1480 -2340 105');

			// Eric Cannon Monument planted right on 19th & Chester Ave intersection!
			sc_ec_base = spawn ();
			sc_ec_base.sc_tag = 1;
			sc_ec_base.movetype = MOVETYPE_NONE;
			sc_ec_base.solid = SOLID_NOT;
			setmodel (sc_ec_base, "progs/eric_tripod.md3");
			sc_ec_base.effects = EF_FULLBRIGHT;
			sc_ec_base.angles = '0 90 0'; // Facing north up Chester Ave
			setsize (sc_ec_base, '0 0 0', '0 0 0');
			setorigin (sc_ec_base, '-180 -2340 2');

			sc_ec_yoke = spawn ();
			sc_ec_yoke.sc_tag = 1;
			sc_ec_yoke.movetype = MOVETYPE_NONE;
			sc_ec_yoke.solid = SOLID_NOT;
			setmodel (sc_ec_yoke, "progs/eric_yoke.md3");
			sc_ec_yoke.effects = EF_FULLBRIGHT;
			sc_ec_yoke.angles = '0 90 0';
			setorigin (sc_ec_yoke, '-180 -2340 2');

			sc_ec_tube = spawn ();
			sc_ec_tube.sc_tag = 1;
			sc_ec_tube.movetype = MOVETYPE_NONE;
			sc_ec_tube.solid = SOLID_NOT;
			setmodel (sc_ec_tube, "progs/eric_cannon.md3");
			sc_ec_tube.effects = EF_FULLBRIGHT;
			sc_ec_tube.angles = '28 90 0';
			setorigin (sc_ec_tube, '-180 -2340 52');

			SC_Cue ("john_bird/jv_fly03.wav", 0.95);
		}

		// 17.50s .. 20.60s: John Bird cruising/driving East down 19th St, camera tracking right alongside/behind
		if (t < 20.60)
		{
			u = (t - 17.50) / 3.10;
			pos = SC_LinVec ('-1480 -2340 105', '-650 -2340 92', u);
			pos_z = pos_z + SC_Sin (time * 7.5) * 9;
			if (sc_bird)
			{
				setorigin (sc_bird, pos);
				sc_bird.angles = '0 0 0';
				sc_bird.angles_z = SC_Sin (time * 5.0) * 14;
				idx = floor (time * 18);
				sc_bird.frame = idx - 16 * floor (idx / 16);
			}
			if (t >= 18.6 && sc_ev < 21) { sc_ev = 21; SC_Cue ("john_bird/flap1.wav", 0.85); }
			if (t >= 19.4 && sc_ev < 22) { sc_ev = 22; SC_Cue ("john_bird/flap2.wav", 0.85); }
			cpos = pos + '-185 -115 36';
			look = pos + '120 10 -8';
		}
		// 20.60s .. 22.15s: John Bird gets rocked -> goes down onto street -> fires rocket into Eric Cannon!
		else if (t < 22.15)
		{
			if (sc_ev < 23)
			{
				sc_ev = 23;
				if (sc_bird) sc_bird.skin = 1;
				SC_DropFeathers ('-650 -2340 92', 24, 1.35);
				SC_Cue ("john_bird/feather_hit.wav", 0.95);
				SC_Cue ("john_bird/shootdown.wav", 0.95);
			}
			// Goes down from (-650, -2340, 92) -> crashes to (-470, -2340, 18) over 0.9s
			u = SC_Clamp01 ((t - 20.60) / 0.90);
			pos = SC_LerpVec ('-650 -2340 92', '-470 -2340 18', u);
			if (sc_bird)
			{
				setorigin (sc_bird, pos);
				sc_bird.angles_x = 18 * (1 - u);
				sc_bird.angles_y = 0;
				sc_bird.angles_z = 26 * u; // Tilted hard on the asphalt
				sc_bird.frame = 60; // stunned perch
				if (sc_fx_smoke > 0 && random () < 0.35)
					pointparticles (sc_fx_smoke, pos + '0 0 28', '0 0 32', 1);
			}

			// Fires glowing rocket from downed John Bird -> Eric Cannon!
			if (t >= 21.50 && sc_ev < 24)
			{
				sc_ev = 24;
				SC_Cue ("weapons/rocket1i.wav", 0.95);
				sc_ec_shot = spawn ();
				sc_ec_shot.sc_tag = 1;
				sc_ec_shot.movetype = MOVETYPE_NONE;
				sc_ec_shot.solid = SOLID_NOT;
				setmodel (sc_ec_shot, "progs/missile.mdl");
				sc_ec_shot.scale = 1.6;
				sc_ec_shot.effects = EF_FULLBRIGHT;
				if (sc_fx_r_trail > 0) sc_ec_shot.traileffectnum = sc_fx_r_trail;
				sc_ec_shot.angles = '0 0 0';
				setorigin (sc_ec_shot, '-430 -2340 42');
			}
			if (sc_ec_shot && t >= 21.50)
			{
				k = SC_Clamp01 ((t - 21.50) / 0.62);
				setorigin (sc_ec_shot, SC_LinVec ('-430 -2340 42', '-180 -2340 54', k));
			}

			cpos = SC_LerpVec ('-620 -2630 105', '-450 -2660 112', (t - 20.60) / 1.55);
			look = '-300 -2340 52';
		}
		// 22.15s .. 23.05s: Rocket hits Eric Cannon -> rubber wind-up & supersonic liftoff ignition!
		else if (t < 23.05)
		{
			if (sc_ev < 25)
			{
				sc_ev = 25;
				if (sc_ec_shot) { remove (sc_ec_shot); sc_ec_shot = world; }
				SC_BoomTE ('-180 -2340 56');
				SC_Cue ("weapons/r_exp3.wav", 0.90);
				SC_Cue ("eric_cannon/windup.wav", 0.95);
				SC_Cue ("eric_cannon/canislupusfantasy2.wav", 0.65);
			}
			if (t >= 22.75 && sc_ev < 26)
			{
				sc_ev = 26;
				SC_Cue ("eric_cannon/fire_boom.wav", 1.0);
				if (sc_fx_smoke > 0)
					pointparticles (sc_fx_smoke, '-180 -2340 68', '0 0 40', 4);
			}
			u = (t - 22.15) / 0.90;
			if (sc_ec_tube)
			{
				if (u < 0.65)
					sc_ec_tube.frame = 17 + floor ((u / 0.65) * 8);
				else
					sc_ec_tube.frame = 26 + floor (((u - 0.65) / 0.35) * 3);
			}
			cpos = SC_LerpVec ('-450 -2660 112', '-390 -2560 96', u);
			look = '-180 -2340 72';
		}
		// 23.05s .. 26.25s: ERIC CANNON FLIES SKY-HIGH ACROSS CHESTER AVE & NOSES INTO TERMINAL DIVE!
		else if (t < 26.25)
		{
			if (sc_ev < 27)
			{
				sc_ev = 27;
				SC_Cue ("eric_cannon/dive_whistle.wav", 0.85);
			}
			if (t >= 24.75 && sc_ev < 28)
			{
				sc_ev = 28;
				SC_Cue ("eric_cannon/doppler_scream.wav", 0.92);
			}
			u = (t - 23.05) / 3.20;
			pos = SC_EricFlyPos (u);
			pos2 = SC_EricFlyPos (u + 0.025);
			dir = normalize (pos2 - pos);

			if (sc_ec_tube)
			{
				setorigin (sc_ec_tube, pos);
				sc_ec_tube.angles = vectoangles (dir);
				if (sc_ec_tube.angles_x > 180) sc_ec_tube.angles_x = sc_ec_tube.angles_x - 360;
				sc_ec_tube.angles_z = time * 120;
				if (u < 0.5)
					sc_ec_tube.frame = 33 + floor (time * 16) - 12 * floor (floor (time * 16) / 12);
				else
					sc_ec_tube.frame = 61 + floor (time * 16) - 8 * floor (floor (time * 16) / 8);
				if (sc_fx_nuke_trail > 0)
					pointparticles (sc_fx_nuke_trail, pos - dir * 48, '0 0 0', 1);
			}
			// Dramatic chasing orbit tracking the flying Eric Cannon up & over into terminal dive!
			cpos = pos + '-230 -240 48';
			if (u > 0.65)
				cpos = SC_LerpVec (pos + '-230 -240 48', '-460 -1520 185', (u - 0.65) / 0.35);
			look = pos;
		}
		// 26.25s .. 28.50s: ERIC CANNON NUCLEAR DETONATION ON CHESTER AVE!
		else
		{
			if (sc_ev < 29)
			{
				sc_ev = 29;
				if (sc_ec_tube) { remove (sc_ec_tube); sc_ec_tube = world; }
				SC_DetonateNuke ('-180 -1100 18');
			}
			u = (t - 26.25) / 2.25;
			cpos = SC_LerpVec ('-460 -1520 185', '-520 -1780 220', u);
			look = SC_LerpVec ('-180 -1100 140', '-180 -1100 320', u);
		}
	}

	// =========================================================================
	// SCENE 4 (28.5s .. 36.5s): 100 GREEN MEN ON CARTS EVERYWHERE + FADE TO BLACK!
	// =========================================================================
	else if (t < 36.5)
	{
		if (sc_ev < 40)
		{
			sc_ev = 40;
			SC_ClearStage ();

			// Spawn 100 Green Men on their little motorized carts driving EVERYWHERE!
			k = 0;
			while (k < 100)
			{
				SC_SpawnCartGreenMan (k);
				k = k + 1;
			}
			SC_Cue ("vehicles/idle_coupe.wav", 0.85);
			SC_Cue ("greenjar/mini_giggle3.wav", 0.95);
			SC_Cue ("vehicles/horn.wav", 0.88);
		}
		if (t >= 30.2 && sc_ev < 41) { sc_ev = 41; SC_Cue ("friends/johnnnny.wav", 0.92); }
		if (t >= 31.8 && sc_ev < 42) { sc_ev = 42; SC_Cue ("greenjar/mini_boing.wav", 0.88); }
		if (t >= 33.4 && sc_ev < 43) { sc_ev = 43; SC_Cue ("larry/octogood.wav", 0.92); }

		u = SC_Smooth ((t - 28.5) / 6.2);
		cpos = SC_LerpVec ('-460 -2660 118', '140 -1550 245', u);
		look = SC_LerpVec ('-120 -2050 28', '-200 -2150 32', u);

		// Smooth hardware screen fade-to-black during final 2.0s (plus ffmpeg fade polish!)
		if (t >= 34.5)
		{
			sc_fade_alpha = floor (SC_Clamp01 ((t - 34.5) / 1.8) * 255);
			stuffcmd (p, strcat ("v_cshift 0 0 0 ", ftos (sc_fade_alpha), "\n"));
		}
	}
	else
	{
		if (!sc_stopped)
		{
			sc_stopped = TRUE;
			if (sc_bgm)
				sound (sc_bgm, 1, "misc/null.wav", 1, ATTN_NONE);
			stuffcmd (p, "v_cshift 0 0 0 255\n");
			localcmd ("stop\n");
		}
		if (t >= 37.0 && !sc_quitted)
		{
			sc_quitted = TRUE;
			if (cvar ("intro_autoquit") > 0)
				localcmd ("quit\n");
		}
		cpos = sc_cam_pos;
		look = sc_cam_pos + '1 0 0';
	}

	if (t < 36.5)
	{
		sc_cam_pos = cpos;
		sc_cam_ang = SC_LookAngles (cpos, look);
	}
	Showcase_SyncPlayer (p);
};

void() Showcase_StartDirector =
{
	sc_t0 = 0;
	sc_ev = 0;
	sc_bgm_on = FALSE;
	sc_cam_fixed = FALSE;
	sc_stopped = FALSE;
	sc_quitted = FALSE;
	sc_cam_pos = '-8220 1760 210';
	sc_cam_ang = SC_LookAngles ('-8220 1760 210', '-9160 2480 680');

	sc_dir = spawn ();
	sc_dir.classname = "showcase_director";
	sc_dir.think = Showcase_DirectorTick;
	sc_dir.nextthink = time + 0.02;
};
