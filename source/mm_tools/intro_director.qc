#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BAKERSFIELD QUAKE: UP-CLOSE SPRITE-ONLY FOX 360 -> 50-SWARM -> BURNING FOX + FLOATING CCCs, DAN & ROB (intro_director.qc)

Compiled ONLY into the isolated temporary build (source/mm_tools/out/qc_intro_build -> progs.dat)
by build_intro_demo.py to record BakersfieldQuake/intro.dem across maps/downtown.bsp (22.5s, cards 201..204):
  - Soundtrack: milky/song.ogg plays continuously from 0.0s to 22.45s!
  - Strictly Wheelman .spr32 sprites ONLY (zero 3D Wheelman, tire, axle, or shockwave MD3 models).
  201. (0.0-6.6s)   Fast Up-Close 360-Degree Orbit of the Historic Fox Theater with 3 Milky Milky Grenades +
                    3 Wheelman Sprites (~195u right in front of the camera lens)!
  202. (6.6-11.8s)  Sudden Up-Close 50 Milkys & Wheelman Sprites (25 + 25) spinning furiously around the Fox Clock Tower!
  203. (11.8-15.3s) ALL 50 EXPLODE UP CLOSE: 25 Milky Geysers + 25 360-Degree Escalating Wheelman Sprite Fireballs
                    erupt up the Clock Tower, splashing white milk drips onto the lens!
  204. (15.3-22.5s) FOX THEATER ON FIRE + FLOATING CCCCCCs + FLOATING DAN & ROB:
                    28 roaring fire & smoke columns engulf the Fox Marquee, FOX sign & Clock Tower while 24 yellow
                    Cs (progs/ccc.md3) float around levitating DAN (daniel.spr32) & ROB (fr_rob.spr32) with
                    "I'm floating" (jetpack/floating.wav) and "Ah, I can't see!" (ccc/shoot.wav)!

Never modifies BakersfieldQuake/progs.dat; intro.dem plays back under normal progs.dat + csprogs.dat.
================
*/

.float	intro_st_card;		// clientstat 69 -> CSQC BM_UpdateIntroCam & BM_DrawIntroHUD (201..204)
.float	intro_st_t0;		// clientstat 70 -> intro_t0 in milliseconds (constant clock anchor)
.float	intro_tag;			// 1 on temporary entities spawned by intro_director for clean scene transitions
.float	intro_phase;
.float	intro_spd;
.float	intro_rad;
.float	intro_gz;
.float	intro_lat;
.float	intro_born;
.float	intro_fkind;
.float	intro_slot;
.float	intro_ring;
.float	intro_boom_on;
.float	intro_boom_tier;
.float	intro_boom_step;

entity	intro_dir_ent;
entity	intro_cam;
entity	intro_bgm_ent;
float	intro_t0;
float	intro_t0_ms;
float	intro_ev;
float	intro_bgm_on;
float	intro_stopped;
float	intro_quitted;
float	intro_cam_fixed;
float	intro_milk_until;
float	intro_swarm_t0;

vector	intro_cam_pos;
vector	intro_cam_ang;
vector	intro_cam_look;
float	intro_cur_card;

vector	intro_b_pos;
vector	intro_b_fwd;
vector	intro_b_rgt;
vector	intro_b_up;

float	intro_fx_vfire;
float	intro_fx_vwreck;
float	intro_fx_vsmoke;
float	intro_fx_bigflame;
float	intro_fx_ccctrail;

void() Intro_Precache =
{
	precache_model ("progs/spike.mdl");
	precache_model ("progs/s_explod.spr");
	precache_model ("progs/s_explodbig.spr");
	precache_model ("progs/s_flame.spr");
	precache_model ("progs/torchflamebase.spr32");
	precache_model ("progs/torchflametop.spr32");

	// Wheelman Sprites ONLY (zero 3D Wheelman / tire / bar / dome models)
	precache_model ("progs/wheelman.spr32");
	precache_model ("progs/wheelman_historic.spr32");
	precache_model ("progs/greensuit_wheelman.spr32");
	precache_model ("progs/wheelman_dance.spr32");

	// Milky Milky Grenade + Floating CCCs + Floating DAN & ROB Sprites
	precache_model ("progs/pinklady.md3");
	precache_model ("progs/ccc.md3");
	precache_model ("progs/daniel.spr32");
	precache_model ("progs/fr_rob.spr32");

	// Non-Stop Milky Song + Action-Comedy Voice & Fire/Explosion Audio
	precache_sound ("milky/song.ogg");
	precache_sound ("milky/fire.wav");
	precache_sound ("afrit/body_explode.wav");
	precache_sound ("weapons/r_exp3.wav");
	precache_sound ("weapons/goosplat.wav");
	precache_sound ("weapons/goopop.wav");
	precache_sound ("weapons/megahorn.wav");
	precache_sound ("misc/h2ohit1.wav");
	precache_sound ("misc/null.wav");
	precache_sound ("wcannon/wc_shoot.wav");
	precache_sound ("wcannon/wc_scream.wav");
	precache_sound ("wcannon/wc_boom.wav");
	precache_sound ("wcannon/wc_lboom4.wav");
	precache_sound ("wcannon/wc_lrun02.wav");
	precache_sound ("wcannon/wc_lrun05.wav");
	precache_sound ("jetpack/floating.wav");
	precache_sound ("funny/imfloating.wav");
	precache_sound ("ccc/shoot.wav");
	precache_sound ("ccc/bounce.wav");
	precache_sound ("daniel/ccc_burst.wav");
	precache_sound ("daniel/ccc_chant.wav");
	precache_sound ("daniel/cant_see_webcam.wav");
	precache_sound ("daniel/shaaa_scream.wav");
	precache_sound ("friends/hello.wav");
	precache_sound ("friends/gowewd.wav");
	precache_sound ("bryan/noway.wav");
	precache_sound ("funny/wewe.wav");
	precache_sound ("player/inflame.wav");
	precache_sound ("vehicles/fire_burn.wav");

	wc_fx_spark = particleeffectnum ("wc_sparks");
	intro_fx_vfire = particleeffectnum ("veh_fire");
	intro_fx_vwreck = particleeffectnum ("veh_wreck_fire");
	intro_fx_vsmoke = particleeffectnum ("veh_smoke");
	intro_fx_bigflame = particleeffectnum ("particleflamebig");
	intro_fx_ccctrail = particleeffectnum ("ccc_trail");
};

void() Intro_Stats =
{
	clientstat (69, 2, intro_st_card);
	clientstat (70, 2, intro_st_t0);
};

float(float x) ISin =
{
	local float r;
	r = sin (x);
	return r;
};

float(float x) ICos =
{
	local float r;
	r = cos (x);
	return r;
};

float(float u) Intro_Smooth =
{
	if (u <= 0)
		return 0;
	if (u >= 1)
		return 1;
	return u * u * (3 - 2 * u);
};

vector(vector a, vector b, float u) Intro_LerpVec =
{
	local float s;
	s = Intro_Smooth (u);
	return a + (b - a) * s;
};

vector(vector from, vector to) Intro_LookAngles =
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

float(float t) Intro_FoxOrbitDeg =
{
	local float u, u_orb;

	u = t / 6.6;
	if (u < 0)
		u = 0;
	if (u > 1)
		u = 1;
	u_orb = 0.72 * u + 0.28 * Intro_Smooth (u);
	return -48 + 360 * u_orb;
};

// Exact lockstep SSQC twin of BM_UpdateIntroCam() (card >= 201) in csqc/bm_hud.qc
void(float t) Intro_ComputeCamBasis =
{
	local float u, deg, rad;
	local vector cpos, look, fwd, rgt, upv;

	if (t < 0)
		t = 0;

	// 201. (0.0s .. 6.6s) FAST UP-CLOSE 360-DEGREE ORBIT OF THE HISTORIC FOX THEATER
	if (t < 6.6)
	{
		u = t / 6.6;
		if (u > 1)
			u = 1;
		deg = Intro_FoxOrbitDeg (t);
		rad = deg * 0.01745329;
		cpos_x = -9990 + ICos (rad) * 1420;
		cpos_y = 3440 + ISin (rad) * 2010;
		cpos_z = 450 + 150 * ISin (u * 3.1415927);
		look_x = -9990 + ICos (rad) * 140;
		look_y = 3440 + ISin (rad) * 200;
		look_z = 415;
	}
	// 202. (6.6s .. 11.8s) UP-CLOSE 50 MILKYS & WHEELMAN SPRITES SPINNING AROUND THE TOWER!
	else if (t < 11.8)
	{
		u = (t - 6.6) / 5.2;
		cpos = Intro_LerpVec ('-8860 2050 815', '-8920 2290 860', u);
		look = Intro_LerpVec ('-9565 2525 875', '-9565 2525 890', u);
	}
	// 203. (11.8s .. 15.3s) ALL 50 EXPLODE UP CLOSE!
	else if (t < 15.3)
	{
		u = (t - 11.8) / 3.5;
		cpos = Intro_LerpVec ('-8920 2290 860', '-8820 2090 835', u);
		look = Intro_LerpVec ('-9565 2525 890', '-9565 2525 885', u);
	}
	// 204. (15.3s .. 22.5s) FOX THEATER ON FIRE + FLOATING CCCCCCs + FLOATING DAN & ROB!
	else
	{
		u = (t - 15.3) / 7.2;
		cpos = Intro_LerpVec ('-8985 2285 285', '-9045 2345 300', u);
		look = Intro_LerpVec ('-9485 2545 375', '-9505 2565 410', u);
	}

	fwd = normalize (look - cpos);
	rgt = normalize (fwd_y * '1 0 0' - fwd_x * '0 1 0');
	upv_x = rgt_y * fwd_z - rgt_z * fwd_y;
	upv_y = rgt_z * fwd_x - rgt_x * fwd_z;
	upv_z = rgt_x * fwd_y - rgt_y * fwd_x;

	intro_b_pos = cpos;
	intro_b_fwd = fwd;
	intro_b_rgt = rgt;
	intro_b_up = upv;
	intro_cam_look = look;
};

void(float card, float t) Intro_EvalCam =
{
	if (card < 201)
		card = 201;
	Intro_ComputeCamBasis (t);
	intro_cam_pos = intro_b_pos;
	intro_cam_ang = Intro_LookAngles (intro_b_pos, intro_cam_look);
};

entity() Intro_GetPlayer =
{
	return find (world, classname, "player");
};

void(string samp, float vol) Intro_Cue =
{
	local entity p;
	p = Intro_GetPlayer ();
	if (p)
		sound (p, CHAN_AUTO, samp, vol, ATTN_NONE);
};

// Extra-punchy vocal cue (dual ATTN_NONE emit so key comedy lines cut straight through the music!)
void(string samp, float vol, float ch_cam) Intro_VocalHero =
{
	local entity p;
	p = Intro_GetPlayer ();
	if (p)
		sound (p, CHAN_AUTO, samp, vol, ATTN_NONE);
	if (intro_cam)
		sound (intro_cam, ch_cam, samp, vol, ATTN_NONE);
};

void(vector org) Intro_BoomFX =
{
	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, org_x);
	WriteCoord (MSG_BROADCAST, org_y);
	WriteCoord (MSG_BROADCAST, org_z);
};

void() Intro_SpriteBoomThink =
{
	self.frame = self.frame + 1;
	if (self.frame >= 6)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.06;
};

void(vector org, float sc) Intro_SpawnSpriteBoom =
{
	local entity b;

	b = spawn ();
	b.classname = "intro_sprboom";
	b.intro_tag = 1;
	b.movetype = MOVETYPE_NONE;
	b.solid = SOLID_NOT;
	setmodel (b, "progs/s_explodbig.spr");
	b.scale = sc;
	b.effects = EF_ADDITIVE | EF_FULLBRIGHT;
	b.frame = 0;
	setsize (b, '0 0 0', '0 0 0');
	setorigin (b, org);
	b.think = Intro_SpriteBoomThink;
	b.nextthink = time + 0.06;
};

void() Intro_ClearSpot =
{
	local entity e, nxt;

	milk_qhead = world;
	milk_qtail = world;
	milk_count = 0;
	milky_count = 0;

	if (intro_cam)
		sound (intro_cam, 6, "misc/null.wav", 1, ATTN_NONE);

	e = nextent (world);
	while (e)
	{
		nxt = nextent (e);
		if (e != intro_dir_ent && e != intro_cam && e != intro_bgm_ent && e.classname != "player" && e.solid != SOLID_BSP)
		{
			if (e.classname == "milky")
				sound (e, CHAN_VOICE, "misc/null.wav", 1, ATTN_NORM);
			if (e.intro_tag || (e.model != "" && e.classname != "misc_model" && e.classname != "bk_tv" && e.classname != "bk_trashcan" && e.classname != "skypad_fx") || e.classname == "milk_rain")
				remove (e);
		}
		e = nxt;
	}
};

// ================================================================
// 360-DEGREE SPRITE CUSTOMIZERS (WHEELMAN SPRITES + DAN + ROB)
// ================================================================

float(vector ref_org, float yaw_ang) Intro_SpriteDir8 =
{
	local float rel, d;

	rel = vectoyaw (intro_cam_pos - ref_org) - yaw_ang;
	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 45 + 0.5);
	if (d >= 8 || d < 0)
		d = 0;
	return d;
};

float() Intro_HistWheelCustomize =
{
	local float d, k, a;

	d = Intro_SpriteDir8 (self.origin + '0 0 38', self.angles_y);
	a = self.wc_anim;
	if (a < 0)
	{
		self.frame = d;
		return TRUE;
	}
	k = floor (time * self.intro_spd + self.intro_phase);
	k = k - 6 * floor (k / 6);
	self.frame = 8 + a * 48 + d * 6 + k;
	return TRUE;
};

float() Intro_ClassicWheelCustomize =
{
	local float d, k;

	d = Intro_SpriteDir8 (self.origin + '0 0 36', self.angles_y);
	if (self.intro_boom_on > 0)
	{
		self.frame = 200 + self.intro_boom_tier * 112 + d * 14 + self.intro_boom_step;
		return TRUE;
	}
	if (self.wc_anim > 0)
	{
		k = floor (time * 20 + self.intro_phase);
		k = k - 6 * floor (k / 6);
		if (self.wc_anim == 1)
			self.frame = 648 + d * 6 + k;
		else if (self.wc_anim == 2)
			self.frame = 696 + d * 6 + k;
		else
			self.frame = 744 + d * 6 + k;
		return TRUE;
	}
	if (self.intro_fkind > 0)
	{
		k = floor (time * 20 + self.intro_phase);
		k = k - 6 * floor (k / 6);
		self.frame = 104 + d * 6 + k;
		return TRUE;
	}
	k = floor (time * 20 + self.intro_phase);
	k = k - 12 * floor (k / 12);
	self.frame = 8 + d * 12 + k;
	return TRUE;
};

// Floating DAN (progs/daniel.spr32): alternates Blind "I can't see!" Squint Scan (200) & "CCC!" Grin (104)!
float() Intro_FloatDanCustomize =
{
	local float d, k, cyc;

	d = Intro_SpriteDir8 (self.origin + '0 0 42', self.angles_y);
	k = floor (time * 16 + self.intro_phase);
	k = k - 6 * floor (k / 6);
	cyc = floor ((time - self.intro_born) * 0.85);
	cyc = cyc - 2 * floor (cyc / 2);
	if (cyc == 0)
		self.frame = 200 + d * 6 + k;	// Blind Squint Scan ("Ah, I can't see!")
	else
		self.frame = 104 + d * 6 + k;	// "CCC! C-C-C-C!" Rapid Grin
	return TRUE;
};

// Floating ROB (progs/fr_rob.spr32): zero-gravity mid-air leg-pedaling float!
float() Intro_FloatRobCustomize =
{
	local float d, k;

	d = Intro_SpriteDir8 (self.origin + '0 0 44', self.angles_y);
	k = floor (time * 13 + self.intro_phase);
	k = k - 6 * floor (k / 6);
	self.frame = 8 + d * 6 + k;
	return TRUE;
};

// ================================================================
// CARD 201 (0.0s .. 6.6s): UP-CLOSE 360 FOX ORBIT (3 MILKYS + 3 WHEELMAN SPRITES)
// ================================================================

vector(entity e, float t) Intro_Fox360FloaterPos =
{
	local float dst, lat, vof;
	local vector pos;

	Intro_ComputeCamBasis (t);
	dst = e.intro_rad + 6 * ICos (t * 2.3 + e.intro_slot * 0.9);
	lat = e.intro_lat + 9 * ISin (t * 2.6 + e.intro_slot * 1.1);
	vof = e.intro_gz + 11 * ISin (t * 3.1 + e.intro_slot * 1.4);
	pos = intro_b_pos + intro_b_fwd * dst + intro_b_rgt * lat + intro_b_up * vof;
	return pos;
};

void() Intro_Fox360FloaterThink =
{
	local float t;
	local vector pos, pos2;

	t = time - intro_t0;
	if (t < 0)
		t = 0;
	if (t >= 6.62)
	{
		remove (self);
		return;
	}

	pos = Intro_Fox360FloaterPos (self, t);
	pos2 = Intro_Fox360FloaterPos (self, t + 0.02);
	setorigin (self, pos);
	self.velocity = (pos2 - pos) * 50;

	if (self.classname == "milky")
	{
		// Face & wobble right toward the viewer so the close-up Milky grenade is clearly visible!
		self.milky_dir = normalize (intro_cam_pos - pos + intro_b_rgt * (ISin (t * 2.4 + self.intro_phase) * 95));
		if (time >= self.milky_drip)
		{
			pointparticles (particleeffectnum ("milk_drip"), pos - '0 0 28', '0 0 0', 1);
			self.milky_drip = time + 0.22 + random () * 0.14;
		}
	}
	else
	{
		// Spin each close-up Wheelman sprite smoothly so all 8 360-deg sprite angles shine!
		if (self.intro_slot == 5 && t >= 3.3)
			self.wc_anim = 2; // Switch Zen Lotus Guru -> Supersonic Pipe-Jet Afterburner halfway around!
		self.angles_y = vectoyaw (intro_cam_pos - pos) + t * 105 + self.intro_slot * 40;
		if (time >= self.cnt)
		{
			self.cnt = time + 0.16;
			pointparticles (wc_fx_spark, pos + '0 0 8', '0 0 28', 1);
		}
	}

	self.nextthink = time + 0.01;
};

void() Intro_SpawnFox360Floaters =
{
	local float idx, dst, lat, vof;
	local entity e;
	local vector p0;

	idx = 0;
	while (idx < 6)
	{
		if (idx == 0)      { lat = -138; dst = 215; vof = 18; }
		else if (idx == 1) { lat = -82;  dst = 196; vof = -34; }
		else if (idx == 2) { lat = -28;  dst = 208; vof = 24; }
		else if (idx == 3) { lat = 28;   dst = 194; vof = -36; }
		else if (idx == 4) { lat = 82;   dst = 210; vof = 16; }
		else               { lat = 138;  dst = 198; vof = -34; }

		e = spawn ();
		e.intro_tag = 1;
		e.movetype = MOVETYPE_NOCLIP;
		e.solid = SOLID_NOT;
		e.effects = EF_FULLBRIGHT;
		e.intro_slot = idx;
		e.intro_lat = lat;
		e.intro_rad = dst;
		e.intro_gz = vof;
		e.intro_phase = idx * 1.15;
		setsize (e, '0 0 0', '0 0 0');

		// Slots 0, 2, 4 = 3 Close-Up Floating Milky Milky Grenades!
		if (idx == 0 || idx == 2 || idx == 4)
		{
			e.classname = "milky";
			setmodel (e, "progs/pinklady.md3");
			if (idx == 2)
				e.scale = 4.0;
			else
				e.scale = 3.7;
			e.milky_owner = world;
			e.milky_born = time - 1.0;
			e.milky_dir = '1 0 0';
			e.milky_drip = time + 0.10 * idx;
			e.traileffectnum = particleeffectnum ("milky_trail");
			e.customizeentityforclient = Milky_Customize;
		}
		// Slot 1 = Close-Up Classic Wheelman Sprite #1 (Fire-Wheels Burnout!)
		else if (idx == 1)
		{
			e.classname = "intro_wheelman_360";
			setmodel (e, "progs/wheelman.spr32");
			e.scale = 0.54;
			e.colormod = '1.28 1.28 1.28';
			e.wc_anim = 1;
			e.customizeentityforclient = Intro_ClassicWheelCustomize;
			e.cnt = time + 0.08;
		}
		// Slot 3 = Close-Up Classic Wheelman Sprite #2 (Jetpack Hover + Spinning Tire Bar!)
		else if (idx == 3)
		{
			e.classname = "intro_wheelman_360";
			setmodel (e, "progs/wheelman.spr32");
			e.scale = 0.56;
			e.colormod = '1.28 1.28 1.28';
			e.wc_anim = 3;
			e.customizeentityforclient = Intro_ClassicWheelCustomize;
			e.cnt = time + 0.12;
		}
		// Slot 5 = Close-Up Historic Wheelman Sprite #3 (Zen Lotus Wheel-Guru -> Pipe-Jet!)
		else
		{
			e.classname = "intro_wheelman_360";
			setmodel (e, "progs/wheelman_historic.spr32");
			e.scale = 0.45;
			e.colormod = '1.30 1.30 1.30';
			e.wc_anim = 9;
			e.intro_spd = 16;
			e.customizeentityforclient = Intro_HistWheelCustomize;
			e.cnt = time + 0.16;
		}

		p0 = Intro_Fox360FloaterPos (e, 0);
		setorigin (e, p0);
		e.think = Intro_Fox360FloaterThink;
		e.nextthink = time + 0.01;

		idx = idx + 1;
	}
};

// ================================================================
// CARDS 202..203 (6.6s .. 15.3s): UP-CLOSE 50 SPRITES & MILKYS ON CLOCK TOWER -> ALL 50 EXPLODE!
// ================================================================

void() Intro_WheelBoomStepThink =
{
	local float s;

	s = floor ((time - self.ltime) * 18);
	if (s >= 14)
	{
		remove (self);
		return;
	}
	if (s < 0)
		s = 0;
	self.intro_boom_step = s;
	self.velocity = '0 0 36';
	self.nextthink = time + 0.04;
};

vector(entity e, float dt) Intro_Swarm50Pos =
{
	local float spin, ang, rr;
	local vector pos;

	if (dt < 0)
		dt = 0;
	spin = dt * 138 + dt * dt * 22.0;
	ang = (e.intro_slot * 36 + e.intro_ring * 18 + spin * (1.0 + 0.07 * e.intro_ring)) * 0.01745329;
	rr = e.intro_rad + 14 * ISin ((intro_swarm_t0 + dt) * 2.8 + e.cnt * 0.7);
	pos_x = -9565 + ICos (ang) * rr;
	pos_y = 2525 + ISin (ang) * rr;
	pos_z = e.intro_gz + 14 * ISin ((intro_swarm_t0 + dt) * 3.3 + e.cnt * 0.9);
	return pos;
};

void() Intro_Swarm50Think =
{
	local float dt, idx, mod4, mod3, spin, ang;
	local vector pos, pos2;

	idx = self.cnt;

	// DETONATION TIME! All 50 Milkys & Wheelman Sprites explode up close (zero 3D debris models)!
	if (time >= self.dmgtime)
	{
		self.velocity = '0 0 0';

		if (self.classname == "milky")
		{
			pointparticles (particleeffectnum ("milky_boom"), self.origin, '0 0 0', 1);
			pointparticles (particleeffectnum ("milk_rain"), self.origin + '0 0 40', '0 0 0', 1);
			Intro_SpawnSpriteBoom (self.origin, 1.35);

			mod4 = idx - 4 * floor (idx / 4);
			if (mod4 == 0)
			{
				Intro_Cue ("afrit/body_explode.wav", 0.72);
				Intro_Cue ("weapons/goopop.wav", 0.78);
			}
			else if (mod4 == 2)
			{
				Intro_Cue ("misc/h2ohit1.wav", 0.76);
				Intro_Cue ("weapons/goosplat.wav", 0.76);
			}
			remove (self);
			return;
		}

		// Wheelman Sprite transforms in-place into progs/wheelman.spr32's 360-deg 14-frame Fireball Explosion!
		setmodel (self, "progs/wheelman.spr32");
		self.customizeentityforclient = Intro_ClassicWheelCustomize;
		self.scale = 0.88;
		self.colormod = '1.25 1.25 1.25';
		self.effects = EF_FULLBRIGHT;
		self.traileffectnum = 0;
		self.intro_boom_on = 1;
		self.intro_boom_tier = idx - 4 * floor (idx / 4);
		self.intro_boom_step = 0;
		self.ltime = time;

		mod3 = idx - 3 * floor (idx / 3);
		if (mod3 == 1)
		{
			Intro_BoomFX (self.origin);
			pointparticles (wc_fx_spark, self.origin, '0 0 90', 2);
			Intro_Cue ("wcannon/wc_boom.wav", 0.78);
		}
		else if (mod3 == 0)
		{
			Intro_SpawnSpriteBoom (self.origin + '0 0 24', 1.45);
			pointparticles (wc_fx_spark, self.origin, '0 0 70', 1);
			Intro_Cue ("weapons/r_exp3.wav", 0.70);
		}
		else
		{
			Intro_Cue ("wcannon/wc_lboom4.wav", 0.72);
		}

		// Spire-top finale blast (#49) splashes thick white milk drips onto the camera lens!
		if (idx == 49)
		{
			Intro_BoomFX ('-9565 2525 1065');
			Intro_SpawnSpriteBoom ('-9565 2525 920', 2.2);
			Intro_SpawnSpriteBoom ('-9565 2525 1060', 2.2);
			Intro_Cue ("weapons/megahorn.wav", 0.88);
			Intro_Cue ("afrit/body_explode.wav", 0.88);
			Intro_Cue ("weapons/goosplat.wav", 0.92);
			intro_milk_until = time + 2.55;
		}

		self.think = Intro_WheelBoomStepThink;
		self.nextthink = time + 0.04;
		return;
	}

	dt = time - intro_swarm_t0;
	if (dt < 0)
		dt = 0;

	pos = Intro_Swarm50Pos (self, dt);
	pos2 = Intro_Swarm50Pos (self, dt + 0.02);
	setorigin (self, pos);
	self.velocity = (pos2 - pos) * 50;

	spin = dt * 138 + dt * dt * 22.0;
	ang = (self.intro_slot * 36 + self.intro_ring * 18 + spin * (1.0 + 0.07 * self.intro_ring)) * 0.01745329;

	if (self.classname == "milky")
	{
		self.milky_dir_x = 0 - ISin (ang);
		self.milky_dir_y = ICos (ang);
		self.milky_dir_z = 0;
	}
	else
	{
		self.angles_y = ang * 57.29578 + 90;
	}

	self.nextthink = time + 0.01;
};

void() Intro_Spawn50TowerSwarm =
{
	local float idx, ring, slot, rz, rr;
	local entity e;
	local vector p0;

	intro_swarm_t0 = time;

	idx = 0;
	while (idx < 50)
	{
		ring = floor (idx / 10);
		slot = idx - ring * 10;

		if (ring == 0)      { rz = 735;  rr = 286; }
		else if (ring == 1) { rz = 810;  rr = 268; }
		else if (ring == 2) { rz = 885;  rr = 250; }
		else if (ring == 3) { rz = 960;  rr = 234; }
		else                { rz = 1035; rr = 220; }

		e = spawn ();
		e.intro_tag = 1;
		e.movetype = MOVETYPE_NOCLIP;
		e.solid = SOLID_NOT;
		e.effects = EF_FULLBRIGHT;
		e.cnt = idx;
		e.intro_ring = ring;
		e.intro_slot = slot;
		e.intro_gz = rz;
		e.intro_rad = rr;
		e.intro_phase = idx * 0.65;
		// Rapid-fire bottom-to-top spiral chain detonation across all 50 entities (11.90s .. 14.11s)!
		e.dmgtime = intro_swarm_t0 + 5.30 + idx * 0.045;
		setsize (e, '0 0 0', '0 0 0');

		// Even slots (0, 2, 4, 6, 8 x 5 rings = 25 Milky Milky Grenades!)
		if (slot - 2 * floor (slot / 2) == 0)
		{
			e.classname = "milky";
			setmodel (e, "progs/pinklady.md3");
			e.scale = 5.8;
			e.milky_owner = world;
			e.milky_born = time - 1.0;
			e.milky_dir = '0 1 0';
			e.customizeentityforclient = Milky_Customize;
			if (slot == 0 || slot == 4)
				e.traileffectnum = particleeffectnum ("milky_trail");
		}
		// Odd slots (1, 3, 5, 7, 9 x 5 rings = 25 Pure .SPR32 Wheelman Sprites!)
		else
		{
			e.classname = "intro_wheelman_swarm";
			e.colormod = '1.26 1.26 1.26';
			if (slot == 1)
			{
				setmodel (e, "progs/wheelman.spr32");
				e.scale = 0.60;
				e.wc_anim = 1; // Fire-Wheels Burnout
				e.customizeentityforclient = Intro_ClassicWheelCustomize;
			}
			else if (slot == 3)
			{
				setmodel (e, "progs/wheelman_historic.spr32");
				e.scale = 0.52;
				if (ring - 2 * floor (ring / 2) == 0)
					e.wc_anim = 8; // Inverted B-Boy Headspin
				else
					e.wc_anim = 2; // Pipe-Jet Afterburner
				e.intro_spd = 20;
				e.customizeentityforclient = Intro_HistWheelCustomize;
			}
			else if (slot == 5)
			{
				setmodel (e, "progs/wheelman.spr32");
				e.scale = 0.60;
				e.wc_anim = 3; // Jetpack Hover + Spinning Bar
				e.customizeentityforclient = Intro_ClassicWheelCustomize;
			}
			else if (slot == 7)
			{
				if (ring - 2 * floor (ring / 2) == 0)
				{
					setmodel (e, "progs/greensuit_wheelman.spr32");
					e.scale = 0.50;
					e.npc_dead = 0;
					e.npc_state = 2;
					e.customizeentityforclient = GreenSuit_Customize;
				}
				else
				{
					setmodel (e, "progs/wheelman_dance.spr32");
					e.scale = 0.34;
					e.wc_anim = ring;
					e.wc_t0 = time;
					e.customizeentityforclient = WC_DancerCustomize;
				}
			}
			else
			{
				setmodel (e, "progs/wheelman.spr32");
				e.scale = 0.60;
				e.wc_anim = 0;
				e.intro_fkind = 1; // Screaming Wheelman
				e.customizeentityforclient = Intro_ClassicWheelCustomize;
			}
		}

		p0 = Intro_Swarm50Pos (e, 0);
		setorigin (e, p0);
		e.think = Intro_Swarm50Think;
		e.nextthink = time + 0.01;

		idx = idx + 1;
	}
};

// ================================================================
// CARD 204 (15.3s .. 22.5s): FOX THEATER ON FIRE + FLOATING CCCCCCs + FLOATING DAN & ROB!
// ================================================================

void() Intro_FoxFlameSpriteThink =
{
	local float f;

	f = floor (time * 16 + self.intro_phase);
	self.frame = f - 7 * floor (f / 7);
	if (time >= self.cnt)
	{
		self.cnt = time + 0.09 + random () * 0.05;
		pointparticles (intro_fx_vwreck, self.origin + '0 0 12', '0 0 45', 1);
		if (self.intro_slot == 1)
			pointparticles (intro_fx_vsmoke, self.origin + '0 0 34', '0 0 65', 1);
	}
	self.nextthink = time + 0.04;
};

void(vector org, float sc, float with_light, float with_smoke, float idx) Intro_SpawnFoxFireColumn =
{
	local entity fb, ft, fs;

	// 1. Bright additive torch-top roaring flame sprite
	ft = spawn ();
	ft.classname = "intro_foxfire";
	ft.intro_tag = 1;
	ft.movetype = MOVETYPE_NONE;
	ft.solid = SOLID_NOT;
	setmodel (ft, "progs/torchflametop.spr32");
	ft.scale = sc;
	ft.effects = EF_ADDITIVE | EF_FULLBRIGHT;
	if (with_light > 0)
		ft.effects = ft.effects | 128 | EF_DIMLIGHT;
	setsize (ft, '0 0 0', '0 0 0');
	setorigin (ft, org);

	// 2. Base ember glow sprite
	fb = spawn ();
	fb.classname = "intro_foxfire";
	fb.intro_tag = 1;
	fb.movetype = MOVETYPE_NONE;
	fb.solid = SOLID_NOT;
	setmodel (fb, "progs/torchflamebase.spr32");
	fb.scale = sc * 0.85;
	fb.effects = EF_ADDITIVE | EF_FULLBRIGHT;
	setsize (fb, '0 0 0', '0 0 0');
	setorigin (fb, org - '0 0 14');

	// 3. Animated 7-frame Quake fire tongue + continuous veh_wreck_fire & black smoke plumes!
	fs = spawn ();
	fs.classname = "intro_foxfire_emit";
	fs.intro_tag = 1;
	fs.movetype = MOVETYPE_NONE;
	fs.solid = SOLID_NOT;
	setmodel (fs, "progs/s_flame.spr");
	fs.scale = sc * 0.78;
	fs.effects = EF_ADDITIVE | EF_FULLBRIGHT;
	fs.intro_phase = idx * 0.9;
	fs.intro_slot = with_smoke;
	fs.cnt = time + (idx - 5 * floor (idx / 5)) * 0.02;
	setsize (fs, '0 0 0', '0 0 0');
	setorigin (fs, org + '0 0 18');
	fs.think = Intro_FoxFlameSpriteThink;
	fs.nextthink = time + 0.02;
};

void() Intro_SpawnBurningFoxTheater =
{
	// 8 roaring fire columns along the iconic Fox Marquee Canopy & H-Street Entrance!
	Intro_SpawnFoxFireColumn ('-9290 2375 185', 4.6, 1, 1, 0);
	Intro_SpawnFoxFireColumn ('-9290 2465 235', 5.2, 0, 1, 1);
	Intro_SpawnFoxFireColumn ('-9290 2555 190', 4.8, 1, 1, 2);
	Intro_SpawnFoxFireColumn ('-9290 2645 238', 5.4, 0, 1, 3);
	Intro_SpawnFoxFireColumn ('-9290 2735 195', 4.6, 1, 1, 4);
	Intro_SpawnFoxFireColumn ('-9290 2825 236', 5.0, 0, 1, 5);
	Intro_SpawnFoxFireColumn ('-9345 2430 115', 4.0, 0, 0, 6);
	Intro_SpawnFoxFireColumn ('-9345 2610 118', 4.2, 0, 0, 7);

	// 6 fire columns wrapping the South 20th-Street Facade!
	Intro_SpawnFoxFireColumn ('-9440 2305 195', 4.6, 1, 1, 8);
	Intro_SpawnFoxFireColumn ('-9565 2355 215', 4.8, 0, 1, 9);
	Intro_SpawnFoxFireColumn ('-9695 2355 205', 4.5, 0, 1, 10);
	Intro_SpawnFoxFireColumn ('-9825 2355 225', 4.6, 0, 0, 11);
	Intro_SpawnFoxFireColumn ('-9575 2385 385', 5.2, 0, 1, 12);
	Intro_SpawnFoxFireColumn ('-9730 2425 410', 5.0, 0, 1, 13);

	// 8 huge fire columns up the Fox Upper Facade & Vertical 'FOX' Sign!
	Intro_SpawnFoxFireColumn ('-9420 2495 345', 5.4, 1, 1, 14);
	Intro_SpawnFoxFireColumn ('-9420 2585 455', 5.8, 0, 1, 15);
	Intro_SpawnFoxFireColumn ('-9420 2515 565', 5.6, 0, 1, 16);
	Intro_SpawnFoxFireColumn ('-9420 2635 570', 5.4, 0, 1, 17);
	Intro_SpawnFoxFireColumn ('-9550 2735 370', 5.0, 0, 1, 18);
	Intro_SpawnFoxFireColumn ('-9550 2845 480', 5.2, 0, 1, 19);
	Intro_SpawnFoxFireColumn ('-9550 2765 575', 5.4, 0, 1, 20);
	Intro_SpawnFoxFireColumn ('-9550 2895 575', 5.0, 0, 0, 21);

	// 6 towering inferno columns blazing on the 74-Ft Fox Clock Tower & Belfry!
	Intro_SpawnFoxFireColumn ('-9430 2505 705', 6.0, 1, 1, 22);
	Intro_SpawnFoxFireColumn ('-9430 2610 720', 5.8, 0, 1, 23);
	Intro_SpawnFoxFireColumn ('-9435 2525 845', 6.4, 1, 1, 24);
	Intro_SpawnFoxFireColumn ('-9435 2615 860', 6.0, 0, 1, 25);
	Intro_SpawnFoxFireColumn ('-9460 2555 975', 6.5, 0, 1, 26);
	Intro_SpawnFoxFireColumn ('-9545 2475 835', 5.8, 0, 1, 27);
};

vector(entity e, float t) Intro_FloatHeroPos =
{
	local float dt, dst, lat, vof;

	dt = t - 15.3;
	if (dt < 0)
		dt = 0;
	Intro_ComputeCamBasis (t);
	dst = e.intro_rad + 7 * ISin (dt * 2.1 + e.intro_phase);
	lat = e.intro_lat + 11 * ISin (dt * 1.8 + e.intro_phase * 1.3);
	vof = e.intro_gz + 15 * ISin (dt * 2.6 + e.intro_phase);
	return intro_b_pos + intro_b_fwd * dst + intro_b_rgt * lat + intro_b_up * vof;
};

void() Intro_FloatHeroThink =
{
	local float t;
	local vector pos, pos2;

	t = time - intro_t0;
	if (t < 15.3)
		t = 15.3;

	pos = Intro_FloatHeroPos (self, t);
	pos2 = Intro_FloatHeroPos (self, t + 0.02);
	setorigin (self, pos);
	self.velocity = (pos2 - pos) * 50;

	// Keep DAN and ROB facing the camera while swaying gently in zero-gravity!
	self.angles_y = vectoyaw (intro_cam_pos - pos) + 34 * ISin (t * 2.2 + self.intro_phase);

	if (time >= self.cnt)
	{
		self.cnt = time + 0.22;
		pointparticles (wc_fx_spark, pos + '0 0 10', '0 0 24', 1);
	}
	self.nextthink = time + 0.01;
};

vector(entity e, float t) Intro_FloatCCCPos =
{
	local float dt, ang, dst, lat, vof;

	dt = t - 15.3;
	if (dt < 0)
		dt = 0;
	Intro_ComputeCamBasis (t);
	ang = e.intro_phase + dt * e.intro_spd;
	lat = e.intro_lat + ICos (ang) * 26;
	vof = e.intro_gz + ISin (ang * 1.3) * 20;
	dst = e.intro_rad + ISin (ang * 0.9) * 16;
	return intro_b_pos + intro_b_fwd * dst + intro_b_rgt * lat + intro_b_up * vof;
};

void() Intro_FloatCCCThink =
{
	local float t;
	local vector pos, pos2;

	t = time - intro_t0;
	if (t < 15.3)
		t = 15.3;

	pos = Intro_FloatCCCPos (self, t);
	pos2 = Intro_FloatCCCPos (self, t + 0.02);
	setorigin (self, pos);
	self.velocity = (pos2 - pos) * 50;
	self.nextthink = time + 0.01;
};

void() Intro_SpawnFloatingCCCsDanRob =
{
	local entity dan, rob, c;
	local float i, ring, slot, ang0, rx, ry, dst, sc;
	local vector p0;

	// 1. Floating DAN (progs/daniel.spr32) up close on left-center!
	dan = spawn ();
	dan.classname = "intro_float_dan";
	dan.intro_tag = 1;
	dan.movetype = MOVETYPE_NOCLIP;
	dan.solid = SOLID_NOT;
	setmodel (dan, "progs/daniel.spr32");
	dan.scale = 0.24;
	dan.colormod = '1.35 1.35 1.35';
	dan.effects = EF_FULLBRIGHT;
	dan.intro_rad = 154;
	dan.intro_lat = -48;
	dan.intro_gz = -46;
	dan.intro_phase = 0.2;
	dan.intro_born = time;
	dan.cnt = time + 0.10;
	dan.customizeentityforclient = Intro_FloatDanCustomize;
	setsize (dan, '0 0 0', '0 0 0');
	p0 = Intro_FloatHeroPos (dan, 15.3);
	setorigin (dan, p0);
	dan.think = Intro_FloatHeroThink;
	dan.nextthink = time + 0.01;

	// 2. Floating ROB (progs/fr_rob.spr32) up close on right-center!
	rob = spawn ();
	rob.classname = "intro_float_rob";
	rob.intro_tag = 1;
	rob.movetype = MOVETYPE_NOCLIP;
	rob.solid = SOLID_NOT;
	setmodel (rob, "progs/fr_rob.spr32");
	rob.scale = 0.96;
	rob.colormod = '1.35 1.35 1.35';
	rob.effects = EF_FULLBRIGHT;
	rob.intro_rad = 156;
	rob.intro_lat = 48;
	rob.intro_gz = -46;
	rob.intro_phase = 2.1;
	rob.intro_born = time;
	rob.cnt = time + 0.18;
	rob.customizeentityforclient = Intro_FloatRobCustomize;
	setsize (rob, '0 0 0', '0 0 0');
	p0 = Intro_FloatHeroPos (rob, 15.3);
	setorigin (rob, p0);
	rob.think = Intro_FloatHeroThink;
	rob.nextthink = time + 0.01;

	// 3. 24 Bright Yellow Spinning 'C's (progs/ccc.md3) floating & orbiting all around DAN & ROB!
	i = 0;
	while (i < 24)
	{
		ring = floor (i / 12);
		slot = i - ring * 12;
		ang0 = (slot * 30 + ring * 15) * 0.01745329;

		if (ring == 0)
		{
			// Inner close-up halo framing DAN & ROB without blocking their faces!
			rx = 148;
			ry = 68;
			dst = 156 + 18 * ISin (i * 1.7);
			sc = 1.65;
		}
		else
		{
			// Wide outer cloud of floating yellow CCCCCCs across the burning Fox Theater!
			rx = 215;
			ry = 92;
			dst = 228 + 24 * ICos (i * 1.3);
			sc = 2.05;
		}

		c = spawn ();
		c.classname = "intro_float_ccc";
		c.intro_tag = 1;
		c.movetype = MOVETYPE_NOCLIP;
		c.solid = SOLID_NOT;
		setmodel (c, "progs/ccc.md3");
		c.scale = sc;
		c.effects = EF_FULLBRIGHT;
		if (i - 2 * floor (i / 2) == 0)
			c.traileffectnum = intro_fx_ccctrail;
		c.intro_lat = ICos (ang0) * rx;
		c.intro_gz = ISin (ang0) * ry + 4;
		c.intro_rad = dst;
		c.intro_phase = i * 0.85;
		c.intro_spd = 2.2 + (i - 4 * floor (i / 4)) * 0.35;
		c.angles_x = (i * 29) - 360 * floor ((i * 29) / 360);
		c.angles_y = (i * 67) - 360 * floor ((i * 67) / 360);
		c.avelocity_x = 150 + (i - 3 * floor (i / 3)) * 55;
		c.avelocity_y = 320 + (i - 5 * floor (i / 5)) * 45;
		c.avelocity_z = 260;
		setsize (c, '0 0 0', '0 0 0');
		p0 = Intro_FloatCCCPos (c, 15.3);
		setorigin (c, p0);
		c.think = Intro_FloatCCCThink;
		c.nextthink = time + 0.01;

		i = i + 1;
	}
};

// ================================================================
// CAMERA & PLAYER LOCKSTEP SYNC
// ================================================================

void(entity p) Intro_PurgePlayerAttachments =
{
	local entity e, nxt;

	if (!p)
		return;
	e = nextent (world);
	while (e)
	{
		nxt = nextent (e);
		if (e != p && e != intro_cam && e != intro_bgm_ent && e != intro_dir_ent && e.solid != SOLID_BSP)
		{
			if (e.owner == p || e.tag_entity == p || e.viewmodelforclient == p)
				remove (e);
		}
		e = nxt;
	}
};

void(entity p) Intro_EnsureCam =
{
	if (!intro_cam)
	{
		intro_cam = spawn ();
		intro_cam.classname = "intro_camera";
		intro_cam.movetype = MOVETYPE_NONE;
		intro_cam.solid = SOLID_NOT;
		setmodel (intro_cam, "progs/spike.mdl");
		intro_cam.scale = 0.01;
		intro_cam.alpha = 0.01;
		setsize (intro_cam, '0 0 0', '0 0 0');
		setorigin (intro_cam, intro_cam_pos);
	}
	if (!intro_bgm_ent)
	{
		intro_bgm_ent = spawn ();
		intro_bgm_ent.classname = "intro_bgm";
		intro_bgm_ent.movetype = MOVETYPE_NONE;
		intro_bgm_ent.solid = SOLID_NOT;
		setmodel (intro_bgm_ent, "progs/spike.mdl");
		intro_bgm_ent.scale = 0.01;
		intro_bgm_ent.alpha = 0.01;
		setsize (intro_bgm_ent, '0 0 0', '0 0 0');
		setorigin (intro_bgm_ent, intro_cam_pos);
	}
	if (p.clientcamera != intro_cam)
	{
		p.clientcamera = intro_cam;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);
		WriteEntity (MSG_ONE, intro_cam);
	}
};

float() Intro_PlayerHook =
{
	self.movetype = MOVETYPE_NONE;
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.flags = self.flags | FL_NOTARGET;
	self.health = 100;
	self.armorvalue = 0;
	self.items = 0;
	self.weapon = 0;
	self.currentammo = 0;
	self.weaponframe = 0;
	self.model = "";
	self.modelindex = 0;
	self.weaponmodel = "";
	self.alpha = 0.01;
	self.effects = EF_NODRAW;
	self.velocity = '0 0 0';
	self.punchangle = '0 0 0';
	self.viewzoom = 1;
	setorigin (self, intro_cam_pos - self.view_ofs);
	self.angles = intro_cam_ang;
	self.v_angle = intro_cam_ang;
	return TRUE;
};

void(entity p) Intro_SyncPlayer =
{
	local float mst;

	if (!p)
		return;

	Intro_EnsureCam (p);
	setorigin (intro_cam, intro_cam_pos);
	intro_cam.angles = intro_cam_ang;
	if (intro_bgm_ent)
		setorigin (intro_bgm_ent, intro_cam_pos);

	mst = 0;
	if (intro_milk_until > time)
	{
		mst = ceil ((intro_milk_until - time) * 22);
		if (mst > 55)
			mst = 55;
	}

	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.takedamage = DAMAGE_NO;
	p.flags = p.flags | FL_NOTARGET;
	p.health = 100;
	p.armorvalue = 0;
	p.items = 0;
	p.weapon = 0;
	p.currentammo = 0;
	p.weaponframe = 0;
	p.model = "";
	p.modelindex = 0;
	p.alpha = 0.01;
	p.effects = EF_NODRAW;
	p.weaponmodel = "";
	p.punchangle = '0 0 0';
	p.viewzoom = 1;
	p.milk_st = mst;
	p.intro_st_card = intro_cur_card;
	p.intro_st_t0 = intro_t0_ms;
	p.velocity = '0 0 0';
	setorigin (p, intro_cam_pos - p.view_ofs);
	p.angles = intro_cam_ang;
	p.v_angle = intro_cam_ang;
	if (!intro_cam_fixed)
	{
		intro_cam_fixed = TRUE;
		p.fixangle = TRUE;
		Intro_PurgePlayerAttachments (p);
	}
};

void() Intro_CleanStage =
{
	local entity e, nxt;

	cvar_set ("bm_botfill", "0");
	cvar_set ("crowd_on", "0");

	e = nextent (world);
	while (e)
	{
		nxt = nextent (e);
		if (e != intro_dir_ent && e != intro_cam && e != intro_bgm_ent && e.classname != "player" && e.solid != SOLID_BSP)
		{
			if (e.classname == "crowd_spawner" || e.classname == "crowd_npc" || e.classname == "floathead_spawner" || e.classname == "floathead")
				remove (e);
			else if (e.classname == "bklan_greensuit" || e.classname == "bklan_robeguy" || e.classname == "bklan_daniel" || e.classname == "bklan_bryan" || e.classname == "bklan_david")
				remove (e);
			else if (e.classname == "bk_car" || e.classname == "bk_bicycle" || (e.flags & FL_ITEM))
				remove (e);
		}
		e = nxt;
	}
};

// ================================================================
// MAIN DIRECTOR TIMELINE (0.0s .. 22.5s, CARDS 201..204)
// ================================================================

void() Intro_Tick =
{
	local entity p;
	local float t;

	self.nextthink = time + 0.01;

	p = Intro_GetPlayer ();
	if (!p)
		return;

	if (intro_t0 == 0)
	{
		if (time < 0.25)
			return;
		intro_t0 = time;
		intro_t0_ms = floor (intro_t0 * 1000 + 0.5);
		Intro_CleanStage ();
		Intro_EnsureCam (p);
	}

	t = time - intro_t0;
	if (t < 0)
		t = 0;

	// ================================================================
	// CARD 201 (0.0s .. 6.6s): UP-CLOSE 360 FOX ORBIT (3 MILKYS + 3 WHEELMAN SPRITES)
	// ================================================================
	if (t < 6.6)
	{
		intro_cur_card = 201;
		if (intro_ev < 1)
		{
			intro_ev = 1;
			Intro_ClearSpot ();
			Intro_EvalCam (201, t);
			Intro_SpawnFox360Floaters ();

			// Play the Milky song the WHOLE time (0.0s -> 22.5s uninterrupted)!
			if (!intro_bgm_on && intro_bgm_ent)
			{
				intro_bgm_on = TRUE;
				sound (intro_bgm_ent, 1, "milky/song.ogg", 0.96, ATTN_NONE);
			}
			Intro_Cue ("milky/fire.wav", 0.78);
			Intro_Cue ("wcannon/wc_lrun02.wav", 0.72);
		}
		if (t >= 3.2 && intro_ev < 2)
		{
			intro_ev = 2;
			Intro_Cue ("friends/hello.wav", 0.80);
			Intro_Cue ("funny/wewe.wav", 0.76);
		}
	}

	// ================================================================
	// CARD 202 (6.6s .. 11.8s): SUDDEN UP-CLOSE 50 MILKYS & WHEELMAN SPRITES ON THE TOWER!
	// ================================================================
	else if (t < 11.8)
	{
		intro_cur_card = 202;
		if (intro_ev < 10)
		{
			intro_ev = 10;
			Intro_ClearSpot ();
			Intro_EvalCam (202, t);
			Intro_Spawn50TowerSwarm ();

			Intro_Cue ("bryan/noway.wav", 0.92);
			Intro_Cue ("milky/fire.wav", 0.82);
		}
		if (t >= 9.0 && intro_ev < 11)
		{
			intro_ev = 11;
			Intro_Cue ("wcannon/wc_scream.wav", 0.82);
			Intro_Cue ("friends/gowewd.wav", 0.84);
		}
	}

	// ================================================================
	// CARD 203 (11.8s .. 15.3s): ALL 50 EXPLODE UP CLOSE!!
	// ================================================================
	else if (t < 15.3)
	{
		intro_cur_card = 203;
		if (intro_ev < 20)
		{
			intro_ev = 20;
			Intro_Cue ("wcannon/wc_shoot.wav", 0.85);
			Intro_Cue ("daniel/shaaa_scream.wav", 0.82);
		}
	}

	// ================================================================
	// CARD 204 (15.3s .. 22.5s): FOX THEATER ON FIRE + FLOATING CCCs + DAN & ROB!
	// ================================================================
	else
	{
		intro_cur_card = 204;
		if (intro_ev < 30)
		{
			intro_ev = 30;
			Intro_ClearSpot ();
			Intro_EvalCam (204, t);
			Intro_SpawnBurningFoxTheater ();
			Intro_SpawnFloatingCCCsDanRob ();

			Intro_Cue ("player/inflame.wav", 0.78);
			Intro_Cue ("vehicles/fire_burn.wav", 0.58);
			Intro_Cue ("ccc/bounce.wav", 0.76);
		}
		// 15.55s: "I'm floating!" (clear & prominent right as floating DAN, ROB & CCCs fill the screen!)
		if (t >= 15.55 && intro_ev < 31)
		{
			intro_ev = 31;
			Intro_VocalHero ("jetpack/floating.wav", 1.0, 4);
			Intro_Cue ("funny/imfloating.wav", 0.95);
		}
		// 16.95s: "Ah, I can't see!" (native 0.80s CCC clip right after "I'm floating" finishes!)
		if (t >= 16.95 && intro_ev < 32)
		{
			intro_ev = 32;
			Intro_VocalHero ("ccc/shoot.wav", 1.0, 5);
		}
		// 18.05s: "CCC! C-C-C-C!" + ricochet boing + fire crackle
		if (t >= 18.05 && intro_ev < 33)
		{
			intro_ev = 33;
			Intro_Cue ("daniel/ccc_burst.wav", 0.88);
			Intro_Cue ("ccc/bounce.wav", 0.72);
			Intro_Cue ("vehicles/fire_burn.wav", 0.52);
		}
		// 19.80s: Second "I'm floating!" beat
		if (t >= 19.80 && intro_ev < 34)
		{
			intro_ev = 34;
			Intro_VocalHero ("jetpack/floating.wav", 1.0, 4);
			Intro_Cue ("funny/imfloating.wav", 0.90);
		}
		// 21.15s: Final punchline "Ah, I can't see!" right before fadeout!
		if (t >= 21.15 && intro_ev < 35)
		{
			intro_ev = 35;
			Intro_VocalHero ("ccc/shoot.wav", 1.0, 5);
			Intro_Cue ("ccc/bounce.wav", 0.68);
		}

		if (t >= 22.45 && !intro_stopped)
		{
			intro_stopped = TRUE;
			if (intro_bgm_ent)
				sound (intro_bgm_ent, 1, "misc/null.wav", 1, ATTN_NONE);
			if (intro_cam)
			{
				sound (intro_cam, 4, "misc/null.wav", 1, ATTN_NONE);
				sound (intro_cam, 5, "misc/null.wav", 1, ATTN_NONE);
				sound (intro_cam, 6, "misc/null.wav", 1, ATTN_NONE);
			}
			localcmd ("stop\n");
		}
		if (t >= 22.90 && !intro_quitted)
		{
			intro_quitted = TRUE;
			if (cvar ("intro_autoquit") > 0)
				localcmd ("quit\n");
		}
	}

	Intro_EvalCam (intro_cur_card, t);
	Intro_SyncPlayer (p);
};

void() Intro_StartDirector =
{
	intro_t0 = 0;
	intro_t0_ms = 0;
	intro_ev = 0;
	intro_bgm_on = FALSE;
	intro_stopped = FALSE;
	intro_quitted = FALSE;
	intro_cam_fixed = FALSE;
	intro_milk_until = 0;
	intro_swarm_t0 = 0;
	intro_cur_card = 201;
	intro_cam_pos = '-9040 1946 450';
	intro_cam_ang = Intro_LookAngles ('-9040 1946 450', '-9896 3291 415');

	intro_dir_ent = spawn ();
	intro_dir_ent.classname = "intro_director";
	intro_dir_ent.think = Intro_Tick;
	intro_dir_ent.nextthink = time + 0.02;
};
