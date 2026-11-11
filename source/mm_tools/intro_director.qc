#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BAKERSFIELD QUAKE: THE MOVIE — 8-ACT ESCALATING MOD SHOWCASE AT THE HISTORIC FOX THEATER (intro_director.qc)

Compiled ONLY into the isolated temporary build (source/mm_tools/out/qc_intro_build -> progs.dat)
by build_intro_demo.py to record BakersfieldQuake/intro.dem across maps/downtown.bsp (48.0s, cards 301..308):
  301. (0.0-5.5s)   ACT I   — Historic Fox Theater Crane-Down & White LAN Van Drift Arrival!
  302. (5.5-11.0s)  ACT II  — Barn Doors Blow Off! Hero Wheelman Stunt Trilogy (Fire-Wheels -> Headspin -> Pipe-Jet)!
  303. (11.0-17.0s) ACT III — Clown-Car Cast Pileout & Fun-Gun Arsenal (4AM Table Flip, Laptop Head, NetSend, Goo, Pickle Surprise, Bonk Clang)!
  304. (17.0-24.0s) ACT IV  — Rush Hour on H St: Supercar, School Bus, Bikes, M4/Tommy/Garand, Sentry, Mega Man, Mystery Box, JohnWave & Rocket Cans!
  305. (24.0-31.0s) ACT V   — Milky Invasion on H St (Milk-Puddle Spinouts!) -> Fast 360-Deg Fox Theater Aerial Orbit!
  306. (31.0-36.2s) ACT VI  — 50-Entity Category-5 Tornado Around the 74-Ft Fox Clock Tower!
  307. (36.2-40.5s) ACT VII — ALL 50 EXPLODE AT ONCE: Dairy Geysers, 4-Tier 360 Wheelman Fireballs, Flying Tires & Lens Milk Splat!
  308. (40.5-48.0s) ACT VIII— Blazing Fox Theater + Wrecked Van on Marquee + Floating DAN, Jetpack Wheelman, ROB & 24 Yellow CCCs!

Never modifies BakersfieldQuake/progs.dat; intro.dem plays back under normal progs.dat + csprogs.dat.
================
*/

.float	intro_st_card;		// clientstat 69 -> CSQC BM_UpdateIntroCam & BM_DrawIntroHUD (301..308)
.float	intro_st_t0;		// clientstat 70 -> intro_t0 in milliseconds (constant clock anchor)
.float	intro_tag;			// 1 on temporary entities spawned by intro_director for clean scene transitions
.float	intro_phase;
.float	intro_spd;
.float	intro_rad;
.float	intro_cx;
.float	intro_cy;
.float	intro_gz;
.float	intro_lat;
.float	intro_born;
.float	intro_fkind;
.float	intro_jrate;
.float	intro_jhigh;
.float	intro_slot;
.float	intro_ring;
.float	intro_boom_on;
.float	intro_boom_tier;
.float	intro_boom_step;
.vector	intro_p0;
.vector	intro_p1;
.entity	intro_wep;

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
float	intro_fx_ccctrail;

// Key Scene Actors & Props
entity	dm_p1;
entity	dm_p2;
entity	dm_p3;
entity	ia_van;
entity	ia_vansurf;
entity	ia_pinkcar;
entity	ia_bus;
entity	ia_forklift;
entity	ia_pickle;
entity	ia_wheelman;
entity	ia_wheel2;
entity	ia_dancer;
entity	ia_spot1;
entity	ia_spot2;
entity	ia_spot3;
entity	ia_spot4;
entity	ia_jp1;
entity	ia_m0;
entity	ia_m1;
entity	ia_m2;
entity	ia_m3;
entity	ia_m4;
entity	ia_m5;
entity	ia_m6;
entity	ia_m7;
entity	ia_m8;
entity	ia_m9;

void() Intro_Precache =
{
	precache_model ("progs/spike.mdl");
	precache_model ("progs/missile.mdl");
	precache_model ("progs/grenade.mdl");
	precache_model ("progs/s_explod.spr");
	precache_model ("progs/s_explodbig.spr");
	precache_model ("progs/s_flame.spr");
	precache_model ("progs/torchflamebase.spr32");
	precache_model ("progs/torchflametop.spr32");
	precache_model ("progs/player_shot.mdl");

	// 3rd-person world weapons
	precache_model ("progs/g_wewcannon.md3");
	precache_model ("progs/p_m4.md3");
	precache_model ("progs/p_tommy.md3");
	precache_model ("progs/p_garand.md3");
	precache_model ("progs/g_rock2.mdl");
	precache_model ("progs/w_blueflail.mdl");

	// Vehicles, Bicycles & LAN Props
	precache_model ("progs/veh_van.md3");
	precache_model ("progs/van_walkin.md3");
	precache_model ("progs/veh_van_door.md3");
	precache_model ("progs/veh_van_wreck.md3");
	precache_model ("progs/veh_schoolbus.md3");
	precache_model ("progs/pink_supercar.md3");
	precache_model ("progs/skyveh_v3.md3");
	precache_model ("progs/bklan/sr_vehicle_forklift_orange_a01.md3");
	precache_model ("progs/bklan/trashcan.md3");
	precache_model ("progs/bklan/lan_mon1.md3");
	precache_model ("progs/bklan/lan_chair1.md3");
	precache_model ("progs/bike_cruiser.md3");
	precache_model ("progs/bike_bmx.md3");
	precache_model ("progs/bike_road.md3");

	// Wheelman Sprites & 3D Wheelman Monuments
	precache_model ("progs/wheelman.spr32");
	precache_model ("progs/wheelman_historic.spr32");
	precache_model ("progs/wheelman_dance.spr32");
	precache_model ("progs/greensuit_wheelman.spr32");
	precache_model ("progs/wheelman_3d_01_roller.md3");
	precache_model ("progs/wheelman_3d_02_standing.md3");
	precache_model ("progs/wheelman_3d_03_titan.md3");
	precache_model ("progs/wheelman_3d_04_thinker.md3");
	precache_model ("progs/wc_bar.md3");
	precache_model ("progs/mm_wheel.md3");

	// Custom Projectiles, Deployables & Gadgets
	precache_model ("progs/pinklady.md3");
	precache_model ("progs/milksplat.md3");
	precache_model ("progs/ccc.md3");
	precache_model ("progs/ltg_head.md3");
	precache_model ("progs/ltg_laser.md3");
	precache_model ("progs/netsend_disk.md3");
	precache_model ("progs/netsend_pc.md3");
	precache_model ("progs/netsend_scr.md3");
	precache_model ("progs/pickle.md3");
	precache_model ("progs/pickle_bomb.md3");
	precache_model ("progs/floathead.mdl");
	precache_model ("progs/turrbase.mdl");
	precache_model ("progs/turrgun.mdl");
	precache_model ("progs/proj_mysterybox.md3");
	precache_model ("progs/megaman.md3");
	precache_model ("progs/mm_explode.md3");
	precache_model ("progs/mm_suit_rider.md3");
	precache_model ("progs/mm_squat_rider.md3");
	precache_model ("progs/gw_horse.md3");
	precache_model ("progs/bigears.md3");
	precache_model ("progs/jw_splash.spr32");
	precache_model ("progs/jw_ripple.spr32");
	precache_model ("progs/jw_wave.md3");
	precache_model ("progs/goo.md3");
	precache_model ("progs/spark_blue.mdl");
	precache_model ("progs/spark_yellow.mdl");
	precache_model ("progs/jetpack.md3");
	precache_model ("progs/john_bird_head.md3");
	precache_model ("progs/john_bird_feather.md3");

	// Bakersfield Legends, Friends, Crowd Sprites & 3D Citizens
	precache_model ("progs/robeguy.spr32");
	precache_model ("progs/daniel.spr32");
	precache_model ("progs/daniel_dad.spr32");
	precache_model ("progs/daniel_table.md3");
	precache_model ("progs/david.spr32");
	precache_model ("progs/preg_1.spr32");
	precache_model ("progs/bryan.spr32");
	precache_model ("progs/jesskart.spr32");
	precache_model ("progs/fr_dennis.spr32");
	precache_model ("progs/fr_paul.spr32");
	precache_model ("progs/fr_mrdiy.spr32");
	precache_model ("progs/fr_scissors.spr32");
	precache_model ("progs/fr_rob.spr32");
	precache_model ("progs/fr_quakeguy.spr32");
	precache_model ("progs/fr_finger.spr32");
	precache_model ("progs/crowd_c1.spr32");
	precache_model ("progs/crowd_c2.spr32");
	precache_model ("progs/crowd_c4.spr32");
	precache_model ("progs/crowd_c6.spr32");
	precache_model ("progs/npc_randguy.md3");
	precache_model ("progs/npc_afroguy.md3");
	precache_model ("progs/npc_randlady.md3");
	precache_model ("progs/npc_fatguy.md3");

	// Soundtracks, Voices & Signature SFX
	precache_sound ("cdtracks/track013.ogg");
	precache_sound ("milky/song.ogg");
	precache_sound ("milky/fire.wav");
	precache_sound ("vehicles/idle_van.wav");
	precache_sound ("vehicles/lanvan.wav");
	precache_sound ("vehicles/horn.wav");
	precache_sound ("vehicles/tire_squeal.wav");
	precache_sound ("vehicles/fire_burn.wav");
	precache_sound ("bklan/notpink.wav");
	precache_sound ("bikes/bell_ring.wav");
	precache_sound ("larry/love_to_play_quake.wav");
	precache_sound ("larry/double_good.wav");
	precache_sound ("friends/hello.wav");
	precache_sound ("friends/gowewd.wav");
	precache_sound ("wcannon/wc_shoot.wav");
	precache_sound ("wcannon/wc_scream.wav");
	precache_sound ("wcannon/wc_boom.wav");
	precache_sound ("wcannon/wc_lboom4.wav");
	precache_sound ("wcannon/wc_lrun02.wav");
	precache_sound ("wcannon/wc_lrun05.wav");
	precache_sound ("pickle/surprise.wav");
	precache_sound ("afrit/body_explode.wav");
	precache_sound ("weapons/r_exp3.wav");
	precache_sound ("weapons/sgun1.wav");
	precache_sound ("weapons/rocket1i.wav");
	precache_sound ("weapons/goosplat.wav");
	precache_sound ("weapons/goopop.wav");
	precache_sound ("weapons/megahorn.wav");
	precache_sound ("megaman/mm_fire.wav");
	precache_sound ("ltgun/type.wav");
	precache_sound ("ltgun/canis.wav");
	precache_sound ("netsend/wheres_disk.wav");
	precache_sound ("hammer/frying_pan.wav");
	precache_sound ("cs16/m4a1_unsil-1.wav");
	precache_sound ("dod/thompson_shoot.wav");
	precache_sound ("dod/garand_shoot.wav");
	precache_sound ("dod/garand_reload_clipding.wav");
	precache_sound ("floathead/calc/c2.wav");
	precache_sound ("funny/heh.wav");
	precache_sound ("funny/quakeahh.wav");
	precache_sound ("funny/wewe.wav");
	precache_sound ("funny/imfloating.wav");
	precache_sound ("jetpack/floating.wav");
	precache_sound ("jetpack/swoosh.wav");
	precache_sound ("ccc/shoot.wav");
	precache_sound ("ccc/bounce.wav");
	precache_sound ("daniel/dad_4am.wav");
	precache_sound ("daniel/shaaa_scream.wav");
	precache_sound ("daniel/ccc_burst.wav");
	precache_sound ("david/slot_jackpot.wav");
	precache_sound ("bryan/noway.wav");
	precache_sound ("mbox/drv_boing_hop.wav");
	precache_sound ("john_bird/jv_fly03.wav");
	precache_sound ("player/pain3.wav");
	precache_sound ("player/inflame.wav");
	precache_sound ("misc/h2ohit1.wav");
	precache_sound ("misc/r_tele5.wav");
	precache_sound ("misc/null.wav");

	wc_fx_spark = particleeffectnum ("wc_sparks");
	intro_fx_vfire = particleeffectnum ("veh_fire");
	intro_fx_vwreck = particleeffectnum ("veh_wreck_fire");
	intro_fx_vsmoke = particleeffectnum ("veh_smoke");
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

// Exact lockstep SSQC twin of BM_UpdateIntroCam() (card >= 301, 0.0s .. 48.0s) in csqc/bm_hud.qc
void(float t) Intro_ComputeCamBasis =
{
	local float u, u_orb, deg, rad;
	local vector cpos, look, fwd, rgt, upv;

	if (t < 0)
		t = 0;

	if (t < 2.2)
	{
		u = t / 2.2;
		cpos = Intro_LerpVec ('-8590 2115 128', '-8695 2182 64', u);
		look = Intro_LerpVec ('-9340 2485 310', '-9030 2435 88', u);
	}
	else if (t < 5.5)
	{
		u = (t - 2.2) / 3.3;
		cpos = Intro_LerpVec ('-8695 2182 64', '-8752 2224 55', u);
		look = Intro_LerpVec ('-9030 2435 88', '-8990 2382 62', u);
	}
	else if (t < 11.0)
	{
		u = (t - 5.5) / 5.5;
		cpos = Intro_LerpVec ('-8720 2205 50', '-8758 2235 56', u);
		look = Intro_LerpVec ('-8890 2320 48', '-8875 2310 56', u);
	}
	else if (t < 17.0)
	{
		u = (t - 11.0) / 6.0;
		cpos = Intro_LerpVec ('-8645 2152 68', '-8595 2118 88', u);
		look = Intro_LerpVec ('-8925 2345 58', '-8910 2335 72', u);
	}
	else if (t < 24.0)
	{
		u = (t - 17.0) / 7.0;
		cpos = Intro_LerpVec ('-8565 2095 76', '-8465 2025 162', u);
		look = Intro_LerpVec ('-9060 2375 96', '-9240 2420 205', u);
	}
	else if (t < 27.4)
	{
		u = (t - 24.0) / 3.4;
		cpos = Intro_LerpVec ('-8635 2145 78', '-8725 2210 92', u);
		look = Intro_LerpVec ('-8975 2375 96', '-9045 2415 112', u);
	}
	else if (t < 31.0)
	{
		u = (t - 27.4) / 3.6;
		if (u < 0)
			u = 0;
		if (u > 1)
			u = 1;
		u_orb = 0.72 * u + 0.28 * Intro_Smooth (u);
		deg = -48 + 360 * u_orb;
		rad = deg * 0.01745329;
		cpos_x = -9990 + ICos (rad) * 1420;
		cpos_y = 3440 + ISin (rad) * 2010;
		cpos_z = 450 + 150 * ISin (u * 3.1415927);
		look_x = -9990 + ICos (rad) * 140;
		look_y = 3440 + ISin (rad) * 200;
		look_z = 415;
	}
	else if (t < 36.2)
	{
		u = (t - 31.0) / 5.2;
		cpos = Intro_LerpVec ('-8860 2050 815', '-8920 2290 860', u);
		look = Intro_LerpVec ('-9565 2525 875', '-9565 2525 890', u);
	}
	else if (t < 40.5)
	{
		u = (t - 36.2) / 4.3;
		cpos = Intro_LerpVec ('-8920 2290 860', '-8820 2090 835', u);
		look = Intro_LerpVec ('-9565 2525 890', '-9565 2525 885', u);
	}
	else
	{
		u = (t - 40.5) / 7.5;
		cpos = Intro_LerpVec ('-8985 2285 285', '-9050 2348 302', u);
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
	if (card < 301)
		card = 301;
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

void(entity v) Intro_FreeCarClips =
{
	local entity clp, nxt_clp;
	if (!v)
		return;
	clp = v.veh_clip_head;
	while (clp != world)
	{
		nxt_clp = clp.enemy;
		remove (clp);
		clp = nxt_clp;
	}
	v.veh_clip_head = world;
};

void() Intro_ClearSpot =
{
	local entity e, nxt;

	dm_p1 = world;
	dm_p2 = world;
	dm_p3 = world;
	ia_van = world;
	ia_vansurf = world;
	ia_pinkcar = world;
	ia_bus = world;
	ia_forklift = world;
	ia_pickle = world;
	ia_wheelman = world;
	ia_wheel2 = world;
	ia_dancer = world;
	ia_spot1 = world;
	ia_spot2 = world;
	ia_spot3 = world;
	ia_spot4 = world;
	ia_jp1 = world;
	ia_m0 = world;
	ia_m1 = world;
	ia_m2 = world;
	ia_m3 = world;
	ia_m4 = world;
	ia_m5 = world;
	ia_m6 = world;
	ia_m7 = world;
	ia_m8 = world;
	ia_m9 = world;

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
			{
				Intro_FreeCarClips (e);
				remove (e);
			}
		}
		e = nxt;
	}
};

// ================================================================
// WHEELMAN, CHARACTER, SPRITE, WEAPON & PROP CHOREOGRAPHY HELPERS
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

	d = Intro_SpriteDir8 (self.origin + '0 0 34', self.angles_y);
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

	d = Intro_SpriteDir8 (self.origin + '0 0 32', self.angles_y);
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

float() Intro_FloatDanCustomize =
{
	local float d, k, cyc;

	d = Intro_SpriteDir8 (self.origin + '0 0 42', self.angles_y);
	k = floor (time * 16 + self.intro_phase);
	k = k - 6 * floor (k / 6);
	cyc = floor ((time - self.intro_born) * 0.85);
	cyc = cyc - 2 * floor (cyc / 2);
	if (cyc == 0)
		self.frame = 200 + d * 6 + k;
	else
		self.frame = 104 + d * 6 + k;
	return TRUE;
};

float() Intro_FloatRobCustomize =
{
	local float d, k;

	d = Intro_SpriteDir8 (self.origin + '0 0 44', self.angles_y);
	k = floor (time * 13 + self.intro_phase);
	k = k - 6 * floor (k / 6);
	self.frame = 8 + d * 6 + k;
	return TRUE;
};

entity(float anim_id, float fps, float sc, vector org) Intro_MakeHistWheel =
{
	local entity w;

	w = spawn ();
	w.classname = "intro_wheelman_hist";
	w.intro_tag = 1;
	w.movetype = MOVETYPE_NONE;
	w.solid = SOLID_NOT;
	setmodel (w, "progs/wheelman_historic.spr32");
	w.scale = sc;
	w.effects = EF_FULLBRIGHT;
	w.colormod = '1.22 1.22 1.22';
	w.wc_anim = anim_id;
	w.intro_spd = fps;
	w.intro_phase = random () * 6;
	w.customizeentityforclient = Intro_HistWheelCustomize;
	w.angles = '0 1 0' * vectoyaw (intro_cam_pos - org);
	setsize (w, '0 0 0', '0 0 0');
	setorigin (w, org);
	return w;
};

entity(float kind, float sc, vector org, float yaw) Intro_MakeWheel3D =
{
	local entity w;

	w = spawn ();
	w.classname = "intro_wheelman_3d";
	w.intro_tag = 1;
	w.movetype = MOVETYPE_NONE;
	w.solid = SOLID_NOT;
	if (kind == 1)
		setmodel (w, "progs/wheelman_3d_01_roller.md3");
	else if (kind == 2)
		setmodel (w, "progs/wheelman_3d_02_standing.md3");
	else if (kind == 3)
		setmodel (w, "progs/wheelman_3d_03_titan.md3");
	else
		setmodel (w, "progs/wheelman_3d_04_thinker.md3");
	w.scale = sc;
	w.effects = EF_FULLBRIGHT;
	w.colormod = '1.08 1.08 1.08';
	w.angles = '0 1 0' * yaw;
	setsize (w, '0 0 0', '0 0 0');
	setorigin (w, org);
	return w;
};

entity(float stunt_id, float scream_on, float sc, vector org) Intro_MakeClassicWheel =
{
	local entity w;

	w = spawn ();
	w.classname = "intro_wheelman_classic";
	w.intro_tag = 1;
	w.movetype = MOVETYPE_NONE;
	w.solid = SOLID_NOT;
	setmodel (w, "progs/wheelman.spr32");
	w.scale = sc;
	w.effects = EF_FULLBRIGHT;
	w.colormod = '1.18 1.18 1.18';
	w.wc_anim = stunt_id;
	w.intro_fkind = scream_on;
	w.intro_phase = random () * 6;
	w.customizeentityforclient = Intro_ClassicWheelCustomize;
	w.angles = '0 1 0' * vectoyaw (intro_cam_pos - org);
	setsize (w, '0 0 0', '0 0 0');
	setorigin (w, org);
	return w;
};

entity(float anim_id, float sc, vector org) Intro_MakeWheelDancer =
{
	local entity d;

	d = spawn ();
	d.classname = "intro_wheelman_dancer";
	d.intro_tag = 1;
	d.movetype = MOVETYPE_NONE;
	d.solid = SOLID_NOT;
	setmodel (d, "progs/wheelman_dance.spr32");
	d.scale = sc;
	d.effects = EF_FULLBRIGHT;
	d.wc_anim = anim_id;
	d.wc_t0 = time;
	d.customizeentityforclient = WC_DancerCustomize;
	d.angles = '0 1 0' * vectoyaw (intro_cam_pos - org);
	setsize (d, '0 0 0', '0 0 0');
	setorigin (d, org);
	return d;
};

entity(float mtype, float sc_mul, vector org) Intro_MakeActor =
{
	local entity m;
	local string mdl;

	mdl = MB_TypeModel (mtype);
	if (mdl == "")
		return world;

	m = spawn ();
	m.classname = "intro_spot";
	m.intro_tag = 1;
	m.movetype = MOVETYPE_NONE;
	m.solid = SOLID_NOT;
	m.mb_type = mtype;
	m.mb_run = TRUE;
	m.mb_born = time;
	MB_Setup (m, mtype);
	m.scale = m.scale * sc_mul;
	setmodel (m, mdl);
	setsize (m, '0 0 0', '0 0 0');
	if (MB_IsSprite (mtype))
		m.customizeentityforclient = MB_Customize;
	m.angles = '0 1 0' * (vectoyaw (intro_cam_pos - org) + m.mb_yaw0);
	setorigin (m, org);
	return m;
};

entity(float ckind, float mv, float sc_mul, vector org) Intro_MakeCrowd =
{
	local entity m;

	m = spawn ();
	m.classname = "intro_spot";
	m.intro_tag = 1;
	m.movetype = MOVETYPE_NONE;
	m.solid = SOLID_NOT;
	m.cn_kind = ckind;
	m.cn_move = mv;
	m.cn_phase = random () * 6;
	m.npc_dead = FALSE;
	m.npc_dstep = 0;
	setmodel (m, CN_Model (ckind));
	if (ckind < 19)
	{
		m.scale = CN_Scale (ckind) * sc_mul;
		m.customizeentityforclient = CN_Customize;
	}
	else
	{
		m.scale = sc_mul;
		if (ckind == 19)
			m.skin = 2;
		else if (ckind == 21)
			m.skin = 1;
		m.frame = 8;
	}
	setsize (m, '0 0 0', '0 0 0');
	m.angles = '0 1 0' * vectoyaw (intro_cam_pos - org);
	setorigin (m, org);
	return m;
};

entity(float st, float sc_mul, vector org) Intro_MakeGreenSuit =
{
	local entity m;

	m = spawn ();
	m.classname = "intro_spot";
	m.intro_tag = 1;
	m.movetype = MOVETYPE_NONE;
	m.solid = SOLID_NOT;
	setmodel (m, "progs/greensuit_wheelman.spr32");
	m.scale = 0.38 * sc_mul;
	m.effects = EF_FULLBRIGHT;
	m.npc_dead = 0;
	m.npc_dstep = 0;
	m.npc_state = st;
	m.customizeentityforclient = GreenSuit_Customize;
	setsize (m, '0 0 0', '0 0 0');
	m.angles = '0 1 0' * vectoyaw (intro_cam_pos - org);
	setorigin (m, org);
	return m;
};

entity(float st, float sc_mul, vector org) Intro_MakeRobeGuy =
{
	local entity m;

	m = spawn ();
	m.classname = "intro_spot";
	m.intro_tag = 1;
	m.movetype = MOVETYPE_NONE;
	m.solid = SOLID_NOT;
	setmodel (m, "progs/robeguy.spr32");
	m.scale = 0.31 * sc_mul;
	m.effects = EF_FULLBRIGHT;
	m.npc_dead = 0;
	m.npc_dstep = 0;
	m.npc_state = st;
	m.customizeentityforclient = RobeGuy_Customize;
	setsize (m, '0 0 0', '0 0 0');
	m.angles = '0 1 0' * vectoyaw (intro_cam_pos - org);
	setorigin (m, org);
	return m;
};

void() Intro_GrooveThink =
{
	local float f;
	local vector p;

	if (time >= self.ltime)
	{
		remove (self);
		return;
	}
	p = self.intro_p0;
	p_z = p_z + fabs (ISin (time * self.intro_jrate + self.intro_phase)) * self.intro_jhigh;
	setorigin (self, p);
	if (self.intro_spd != 0)
		self.angles_y = self.angles_y + self.intro_spd * 0.02;
	if (self.cn_kind >= 19)
	{
		f = floor (time * 14 + self.intro_phase);
		self.frame = 20 + (f - 10 * floor (f / 10));
	}
	else if (self.mb_fn > 0)
	{
		f = floor (time * self.mb_fps + self.intro_phase);
		self.frame = self.mb_f0 + f - self.mb_fn * floor (f / self.mb_fn);
	}
	self.nextthink = time + 0.02;
};

void(entity e, float jrate, float jhigh, float yaw_spd, float dur) Intro_AttachGroove =
{
	if (!e)
		return;
	e.intro_p0 = e.origin;
	e.intro_jrate = jrate;
	e.intro_jhigh = jhigh;
	e.intro_spd = yaw_spd;
	e.intro_phase = random () * 6;
	e.ltime = time + dur;
	e.think = Intro_GrooveThink;
	e.nextthink = time + 0.02;
};

void() Intro_MoverThink =
{
	local float u, f;
	local vector pos, dir;

	if (time >= self.ltime)
	{
		remove (self);
		return;
	}
	u = (time - self.intro_born) / self.intro_spd;
	if (u < 0) u = 0;
	if (u > 1) u = 1;

	pos = self.intro_p0 + (self.intro_p1 - self.intro_p0) * u;
	pos_z = pos_z + fabs (ISin (time * 9.5 + self.intro_phase)) * self.intro_jhigh;
	setorigin (self, pos);

	dir = self.intro_p1 - self.intro_p0;
	if (vlen (dir) > 1 && self.intro_fkind != 9)
		self.angles_y = vectoyaw (dir) + self.mb_yaw0;

	if (self.cn_kind >= 19)
	{
		f = floor (time * 13 + self.intro_phase);
		self.frame = 20 + (f - 10 * floor (f / 10));
	}
	else if (self.mb_fn > 0)
	{
		f = floor (time * self.mb_fps + self.intro_phase);
		self.frame = self.mb_f0 + f - self.mb_fn * floor (f / self.mb_fn);
	}
	self.nextthink = time + 0.02;
};

void(entity e, vector p0, vector p1, float dur, float hop_h, float keep_yaw) Intro_AttachMover =
{
	if (!e)
		return;
	setorigin (e, p0);
	e.intro_p0 = p0;
	e.intro_p1 = p1;
	e.intro_born = time;
	e.intro_spd = dur;
	e.intro_jhigh = hop_h;
	e.intro_fkind = keep_yaw;
	e.intro_phase = random () * 6;
	e.ltime = time + dur + 0.3;
	e.think = Intro_MoverThink;
	e.nextthink = time + 0.02;
};

// ================================================================
// DEATHMATCH FIGHTERS, CUSTOM FUN GUNS, BIKES, BIRDS & FX HELPERS
// ================================================================

void() Intro_DMThink =
{
	local float a, nx, ny, f, aim_yaw;
	local vector np, dir, wpos;

	if (time > self.ltime)
	{
		if (self.intro_wep)
			remove (self.intro_wep);
		remove (self);
		return;
	}

	if (self.movetype == MOVETYPE_TOSS || self.movetype == MOVETYPE_BOUNCE)
	{
		f = floor ((time - self.dmgtime) * 14);
		if (f < 0) f = 0;
		if (f > 10) f = 10;
		self.frame = 50 + f;
		if (self.intro_wep)
		{
			setorigin (self.intro_wep, self.origin + '0 0 12');
			self.intro_wep.angles = self.angles;
		}
		self.nextthink = time + 0.02;
		return;
	}

	a = time * self.intro_spd + self.intro_phase;
	nx = self.intro_cx + ICos (a * 0.0174533) * self.intro_rad;
	ny = self.intro_cy + ISin (a * 0.0174533 * 1.35) * (self.intro_rad * 0.72);
	np_x = nx;
	np_y = ny;
	np_z = self.intro_gz + 24 + fabs (ISin (time * self.intro_jrate + self.intro_phase)) * self.intro_jhigh;
	setorigin (self, np);

	if (self.enemy)
		dir = self.enemy.origin - np;
	else
		dir = intro_cam_pos - np;
	aim_yaw = vectoyaw (dir);
	self.angles = '0 1 0' * aim_yaw;

	if (time < self.pain_finished)
	{
		f = floor ((self.pain_finished - time) * 16);
		f = 5 - (f - 6 * floor (f / 6));
		if (f < 0) f = 0;
		if (f > 5) f = 5;
		if (self.cnt == 2)
			self.frame = 119 + f;
		else
			self.frame = 107 + f;
	}
	else
	{
		self.effects = self.effects - (self.effects & EF_MUZZLEFLASH);
		f = floor (time * 14 + self.intro_phase);
		self.frame = 6 + (f - 6 * floor (f / 6));
	}

	if (self.intro_wep)
	{
		self.intro_wep.effects = self.effects & EF_MUZZLEFLASH;
		makevectors (self.angles);
		wpos = np + v_forward * 15 + v_right * 8 + '0 0 8';
		setorigin (self.intro_wep, wpos);
		self.intro_wep.angles = vectoangles (dir);
		self.intro_wep.angles_x = 0 - self.intro_wep.angles_x;
	}

	self.nextthink = time + 0.01;
};

entity(float slot, vector center, float gz, float rad, float spd, float ph, string wmdl, float wsc, float dur) Intro_SpawnDMFighter =
{
	local entity p, w;

	p = spawn ();
	p.classname = "intro_dm_player";
	p.intro_tag = 1;
	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	setmodel (p, "progs/player_shot.mdl");
	p.scale = 1.24;
	if (slot == 1)
		p.colormod = '1.85 0.42 0.38';
	else if (slot == 2)
		p.colormod = '0.38 1.32 1.95';
	else
		p.colormod = '1.90 1.48 0.34';
	setsize (p, '0 0 0', '0 0 0');
	p.intro_cx = center_x;
	p.intro_cy = center_y;
	p.intro_gz = gz;
	p.intro_rad = rad;
	p.intro_spd = spd;
	p.intro_phase = ph;
	p.intro_jrate = 6.4 + slot * 0.5;
	p.intro_jhigh = 20;
	p.ltime = time + dur;
	setorigin (p, center + '0 0 24');

	if (wmdl != "")
	{
		w = spawn ();
		w.classname = "intro_dm_weapon";
		w.intro_tag = 1;
		w.movetype = MOVETYPE_NONE;
		w.solid = SOLID_NOT;
		setmodel (w, wmdl);
		w.scale = wsc;
		w.colormod = '1.15 1.15 1.15';
		setsize (w, '0 0 0', '0 0 0');
		setorigin (w, center + '0 0 32');
		p.intro_wep = w;
	}

	p.think = Intro_DMThink;
	p.nextthink = time + 0.01;
	return p;
};

void(entity fighter, vector vel) Intro_LaunchRagdoll =
{
	if (!fighter)
		return;
	fighter.movetype = MOVETYPE_TOSS;
	fighter.dmgtime = time;
	fighter.velocity = vel;
	fighter.avelocity = '180 340 120';
};

void(string mdl, vector org, vector vel, float sc, float life) Intro_TossProp =
{
	local entity d;

	d = spawn ();
	d.classname = "intro_prop";
	d.intro_tag = 1;
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_BBOX;
	setmodel (d, mdl);
	d.scale = sc;
	d.bouncefactor = 0.68;
	d.velocity = vel;
	d.avelocity = '240 380 190';
	setsize (d, '0 0 0', '0 0 0');
	setorigin (d, org);
	d.think = SUB_Remove;
	d.nextthink = time + life;
};

void(vector org, float play_pan) Intro_BonkSparks =
{
	local float i;
	local entity s;

	if (play_pan > 0)
		Intro_Cue ("hammer/frying_pan.wav", 0.94);
	i = 0;
	while (i < 12)
	{
		s = spawn ();
		s.classname = "intro_prop";
		s.intro_tag = 1;
		s.movetype = MOVETYPE_BOUNCE;
		s.solid = SOLID_NOT;
		if (i - 2 * floor (i / 2) == 0)
			setmodel (s, "progs/spark_yellow.mdl");
		else
			setmodel (s, "progs/spark_blue.mdl");
		s.scale = 1.65;
		s.effects = EF_FULLBRIGHT;
		setsize (s, '0 0 0', '0 0 0');
		setorigin (s, org + '0 0 32');
		s.velocity_x = crandom () * 185;
		s.velocity_y = crandom () * 185;
		s.velocity_z = 190 + random () * 190;
		s.avelocity = '400 500 300';
		s.think = SUB_Remove;
		s.nextthink = time + 1.6;
		i = i + 1;
	}
};

void() Intro_GooBlobSwell =
{
	self.cnt = self.cnt + 1;
	if (self.cnt <= 4)
	{
		self.frame = self.cnt + 1;
		self.scale = self.scale + 0.12;
		self.nextthink = time + 0.12;
		return;
	}
	self.frame = 0;
	self.think = SUB_Remove;
	self.nextthink = time + 3.6;
};

void(vector target_org) Intro_StickGooFoam =
{
	local entity g;

	g = spawn ();
	g.classname = "intro_prop";
	g.intro_tag = 1;
	g.movetype = MOVETYPE_NONE;
	g.solid = SOLID_NOT;
	setmodel (g, "progs/goo.md3");
	g.frame = 1;
	g.scale = 0.36;
	g.effects = EF_FULLBRIGHT;
	g.angles = '0 1 0' * (random () * 360);
	setsize (g, '0 0 0', '0 0 0');
	setorigin (g, target_org);
	g.cnt = 0;
	g.think = Intro_GooBlobSwell;
	g.nextthink = time + 0.10;
	Intro_Cue ("weapons/goosplat.wav", 0.80);
};

// Laptop Gun 24-angle wobbling flying head + red targeting beam!
void() Intro_LtHeadThink =
{
	local float u;
	local vector pos;

	if (time >= self.ltime)
	{
		Intro_BoomFX (self.origin);
		if (self.intro_wep)
			remove (self.intro_wep);
		remove (self);
		return;
	}
	u = (time - self.intro_born) / self.intro_spd;
	if (u < 0) u = 0;
	if (u > 1) u = 1;
	pos = self.intro_p0 + (self.intro_p1 - self.intro_p0) * u;
	pos_z = pos_z + ISin (time * 8.0) * 8;
	setorigin (self, pos);
	if (self.intro_wep)
	{
		setorigin (self.intro_wep, pos);
		self.intro_wep.angles = vectoangles (self.intro_p1 - pos);
		self.intro_wep.angles_x = 0 - self.intro_wep.angles_x;
	}
	self.nextthink = time + 0.02;
};

void(vector p0, vector p1, float dur) Intro_SpawnLaptopHead =
{
	local entity h, beam;

	h = spawn ();
	h.classname = "intro_ltg_head";
	h.intro_tag = 1;
	h.movetype = MOVETYPE_NONE;
	h.solid = SOLID_NOT;
	setmodel (h, "progs/ltg_head.md3");
	h.scale = 1.65;
	h.effects = EF_FULLBRIGHT;
	h.traileffectnum = particleeffectnum ("ltg_trail");
	h.ltg_head = vectoyaw (p1 - p0);
	h.ltg_wob = random () * 6;
	h.customizeentityforclient = LtGun_HeadCustomize;
	h.intro_p0 = p0;
	h.intro_p1 = p1;
	h.intro_born = time;
	h.intro_spd = dur;
	h.ltime = time + dur;
	setsize (h, '0 0 0', '0 0 0');
	setorigin (h, p0);

	beam = spawn ();
	beam.classname = "intro_ltg_beam";
	beam.intro_tag = 1;
	beam.movetype = MOVETYPE_NONE;
	beam.solid = SOLID_NOT;
	setmodel (beam, "progs/ltg_laser.md3");
	beam.scale = 0.55;
	beam.effects = EF_ADDITIVE | EF_FULLBRIGHT;
	setsize (beam, '0 0 0', '0 0 0');
	setorigin (beam, p0);
	h.intro_wep = beam;

	h.think = Intro_LtHeadThink;
	h.nextthink = time + 0.02;
};

// NetSend CRT PC Turret + Animated Screen!
void() Intro_NetSendPCThink =
{
	local float f;

	if (time >= self.ltime)
	{
		if (self.intro_wep)
			remove (self.intro_wep);
		remove (self);
		return;
	}
	f = floor ((time - self.intro_born) * 14);
	self.frame = f - 8 * floor (f / 8);
	if (self.intro_wep)
	{
		self.intro_wep.frame = 24 + (f - 16 * floor (f / 16));
		self.intro_wep.skin = f - 6 * floor (f / 6);
	}
	if (time >= self.cnt)
	{
		self.cnt = time + 0.28;
		pointparticles (particleeffectnum ("netsend_zap"), self.origin + '0 0 38', '0 0 25', 1);
	}
	self.nextthink = time + 0.04;
};

void(vector org, float yaw, float dur) Intro_SpawnNetSendPC =
{
	local entity pc, scr;

	pc = spawn ();
	pc.classname = "intro_netsend_pc";
	pc.intro_tag = 1;
	pc.movetype = MOVETYPE_NONE;
	pc.solid = SOLID_NOT;
	setmodel (pc, "progs/netsend_pc.md3");
	pc.scale = 1.35;
	pc.effects = EF_FULLBRIGHT;
	pc.angles = '0 1 0' * yaw;
	pc.intro_born = time;
	pc.cnt = time + 0.10;
	pc.ltime = time + dur;
	setsize (pc, '0 0 0', '0 0 0');
	setorigin (pc, org);

	scr = spawn ();
	scr.classname = "intro_netsend_scr";
	scr.intro_tag = 1;
	scr.movetype = MOVETYPE_NONE;
	scr.solid = SOLID_NOT;
	setmodel (scr, "progs/netsend_scr.md3");
	scr.scale = 1.35;
	scr.effects = EF_FULLBRIGHT;
	scr.angles = pc.angles;
	setsize (scr, '0 0 0', '0 0 0');
	setorigin (scr, org);
	pc.intro_wep = scr;

	pc.think = Intro_NetSendPCThink;
	pc.nextthink = time + 0.04;
};

// Giant Inflating 64-Skin 360-Deg Pickle Surprise Diva!
void() Intro_PickleDivaThink =
{
	local float dt, f;

	if (time >= self.ltime)
	{
		pointparticles (particleeffectnum ("pk_boom"), self.origin + '0 0 42', '0 0 0', 1);
		Intro_Cue ("weapons/goopop.wav", 0.86);
		if (self.intro_wep)
			remove (self.intro_wep);
		remove (self);
		return;
	}
	dt = time - self.intro_born;
	if (dt < 0.35)
		self.scale = 1.2 + (dt / 0.35) * 4.1;
	else
		self.scale = 5.3 + ISin (dt * 9.0) * 0.25;
	f = floor (dt * 18);
	self.frame = f - 12 * floor (f / 12);
	self.pk_front = vectoyaw (intro_cam_pos - self.origin);
	self.nextthink = time + 0.03;
};

entity(vector org, float dur) Intro_SpawnPickleDiva =
{
	local entity pk, base;

	base = spawn ();
	base.classname = "intro_pickle_base";
	base.intro_tag = 1;
	base.movetype = MOVETYPE_NONE;
	base.solid = SOLID_NOT;
	setmodel (base, "progs/pickle_bomb.md3");
	base.scale = 1.85;
	base.effects = EF_FULLBRIGHT;
	base.frame = 18;
	setsize (base, '0 0 0', '0 0 0');
	setorigin (base, org + '0 0 2');

	pk = spawn ();
	pk.classname = "intro_pickle_diva";
	pk.intro_tag = 1;
	pk.movetype = MOVETYPE_NONE;
	pk.solid = SOLID_NOT;
	setmodel (pk, "progs/pickle.md3");
	pk.scale = 1.2;
	pk.effects = EF_FULLBRIGHT;
	pk.pk_state = 4;
	pk.pk_front = vectoyaw (intro_cam_pos - org);
	pk.pk_t0 = time;
	pk.pk_t = time + dur;
	pk.intro_born = time;
	pk.ltime = time + dur;
	pk.intro_wep = base;
	pk.customizeentityforclient = Pk_Customize;
	setsize (pk, '0 0 0', '0 0 0');
	setorigin (pk, org);
	pk.think = Intro_PickleDivaThink;
	pk.nextthink = time + 0.02;
	return pk;
};

// Shootable 3D Bicycle spinning HitSpin frames!
void() Intro_BikeSpinThink =
{
	local float f;

	if (time >= self.ltime)
	{
		remove (self);
		return;
	}
	f = floor ((time - self.intro_born) * 20 + self.intro_phase);
	self.frame = 12 + (f - 16 * floor (f / 16));
	self.nextthink = time + 0.03;
};

void(string mdl, vector org, float yaw, float dur) Intro_SpawnSpinBike =
{
	local entity b;

	b = spawn ();
	b.classname = "intro_bike";
	b.intro_tag = 1;
	b.movetype = MOVETYPE_NONE;
	b.solid = SOLID_NOT;
	setmodel (b, mdl);
	b.scale = 1.22;
	b.effects = EF_FULLBRIGHT;
	b.angles = '0 1 0' * yaw;
	b.intro_born = time;
	b.intro_phase = random () * 10;
	b.ltime = time + dur;
	setsize (b, '0 0 0', '0 0 0');
	setorigin (b, org);
	b.think = Intro_BikeSpinThink;
	b.nextthink = time + 0.03;
};

// TF Level-2 Sentry Gun tracking targets!
void() Intro_SentryThink =
{
	if (time >= self.ltime)
	{
		if (self.intro_wep)
			remove (self.intro_wep);
		remove (self);
		return;
	}
	if (self.intro_wep)
		self.intro_wep.angles_y = self.angles_y + ISin (time * 4.5) * 48;
	self.nextthink = time + 0.03;
};

void(vector org, float yaw, float dur) Intro_SpawnSentry =
{
	local entity tb, tg;

	tb = spawn ();
	tb.classname = "intro_sentry";
	tb.intro_tag = 1;
	tb.movetype = MOVETYPE_NONE;
	tb.solid = SOLID_NOT;
	setmodel (tb, "progs/turrbase.mdl");
	tb.scale = 1.25;
	tb.angles = '0 1 0' * yaw;
	tb.ltime = time + dur;
	setsize (tb, '0 0 0', '0 0 0');
	setorigin (tb, org);

	tg = spawn ();
	tg.classname = "intro_sentry_gun";
	tg.intro_tag = 1;
	tg.movetype = MOVETYPE_NONE;
	tg.solid = SOLID_NOT;
	setmodel (tg, "progs/turrgun.mdl");
	tg.scale = 1.25;
	tg.skin = 1;
	tg.frame = 3;
	tg.angles = tb.angles;
	setsize (tg, '0 0 0', '0 0 0');
	setorigin (tg, org + '0 0 10');
	tb.intro_wep = tg;

	tb.think = Intro_SentryThink;
	tb.nextthink = time + 0.03;
};

// Steerable Rob Dob Flying Head!
void() Intro_RobDobThink =
{
	local float u, f;
	local vector pos, dir;

	if (time >= self.ltime)
	{
		Intro_BoomFX (self.origin);
		Intro_Cue ("funny/heh.wav", 0.85);
		remove (self);
		return;
	}
	u = (time - self.intro_born) / self.intro_spd;
	if (u < 0) u = 0;
	if (u > 1) u = 1;
	pos = Intro_LerpVec (self.intro_p0, self.intro_p1, u);
	pos_z = pos_z + ISin (time * 7.2 + self.intro_phase) * 14;
	dir = self.intro_p1 - self.intro_p0;
	self.angles = vectoangles (dir);
	f = floor (time * 16 + self.intro_phase);
	self.frame = 8 + (f - 6 * floor (f / 6));
	if (u > 0.72)
		self.skin = 1;
	setorigin (self, pos);
	self.nextthink = time + 0.02;
};

void(vector p0, vector p1, float dur, float sc) Intro_SpawnRobDob =
{
	local entity r;

	r = spawn ();
	r.classname = "intro_robdob";
	r.intro_tag = 1;
	r.movetype = MOVETYPE_NONE;
	r.solid = SOLID_NOT;
	setmodel (r, "progs/floathead.mdl");
	r.scale = sc;
	r.effects = EF_FULLBRIGHT;
	r.traileffectnum = particleeffectnum ("fd_trail");
	r.intro_p0 = p0;
	r.intro_p1 = p1;
	r.intro_born = time;
	r.intro_spd = dur;
	r.intro_phase = random () * 6;
	r.ltime = time + dur;
	setsize (r, '0 0 0', '0 0 0');
	setorigin (r, p0);
	r.think = Intro_RobDobThink;
	r.nextthink = time + 0.02;
};

void(vector org) Intro_DropFeather =
{
	local entity f;

	f = spawn ();
	f.classname = "intro_prop";
	f.intro_tag = 1;
	f.movetype = MOVETYPE_TOSS;
	f.solid = SOLID_NOT;
	setmodel (f, "progs/john_bird_feather.md3");
	f.scale = 1.25;
	f.gravity = 0.22;
	f.velocity_x = crandom () * 65;
	f.velocity_y = crandom () * 65;
	f.velocity_z = 35 + random () * 45;
	f.avelocity = '180 340 220';
	setsize (f, '0 0 0', '0 0 0');
	setorigin (f, org);
	f.think = SUB_Remove;
	f.nextthink = time + 2.2;
};

void() Intro_JohnBirdThink =
{
	local float u, k;
	local vector pos, dir;

	if (time >= self.ltime)
	{
		remove (self);
		return;
	}
	u = (time - self.intro_born) / self.intro_spd;
	if (u < 0) u = 0;
	if (u > 1) u = 1;
	pos = Intro_LerpVec (self.intro_p0, self.intro_p1, u);
	pos_z = pos_z + ISin (time * 6.5) * 8;
	dir = self.intro_p1 - self.intro_p0;
	self.angles = vectoangles (dir);
	self.angles_x = 0 - self.angles_x * 0.35;
	self.angles_z = ISin (time * 5.0) * 9;
	k = floor (time * 22);
	self.frame = k - 16 * floor (k / 16);
	setorigin (self, pos);

	if (time >= self.cnt)
	{
		self.cnt = time + 0.34;
		Intro_DropFeather (pos + '0 0 12');
	}
	self.nextthink = time + 0.01;
};

entity(vector p0, vector p1, float dur, float sc) Intro_SpawnJohnBird =
{
	local entity b;

	b = spawn ();
	b.classname = "intro_bird";
	b.intro_tag = 1;
	b.movetype = MOVETYPE_NONE;
	b.solid = SOLID_NOT;
	setmodel (b, "progs/john_bird_head.md3");
	b.scale = sc;
	b.effects = EF_FULLBRIGHT;
	b.intro_p0 = p0;
	b.intro_p1 = p1;
	b.intro_born = time;
	b.intro_spd = dur;
	b.ltime = time + dur + 0.2;
	b.cnt = time + 0.18;
	setsize (b, '0 0 0', '0 0 0');
	setorigin (b, p0);
	b.think = Intro_JohnBirdThink;
	b.nextthink = time + 0.01;
	return b;
};

void() Intro_WaveRingThink =
{
	if (time >= self.ltime)
	{
		remove (self);
		return;
	}
	self.scale = self.scale + 0.18;
	self.alpha = 0.88 * ((self.ltime - time) / 1.8);
	self.angles_y = self.angles_y + 8;
	self.nextthink = time + 0.03;
};

void(vector org) Intro_SpawnJohnWave =
{
	local entity s, w, oldself;

	s = spawn ();
	s.classname = "grenade";
	s.intro_tag = 1;
	s.movetype = MOVETYPE_NONE;
	s.solid = SOLID_NOT;
	setmodel (s, "progs/jw_splash.spr32");
	s.scale = 1.25;
	setsize (s, '0 0 0', '0 0 0');
	setorigin (s, org);
	oldself = self;
	self = s;
	JG_Splash ();
	self = oldself;

	w = spawn ();
	w.classname = "intro_prop";
	w.intro_tag = 1;
	w.movetype = MOVETYPE_NONE;
	w.solid = SOLID_NOT;
	setmodel (w, "progs/jw_wave.md3");
	w.scale = 0.65;
	w.alpha = 0.88;
	w.effects = EF_FULLBRIGHT;
	setsize (w, '0 0 0', '0 0 0');
	setorigin (w, org + '0 0 4');
	w.ltime = time + 1.8;
	w.think = Intro_WaveRingThink;
	w.nextthink = time + 0.03;
};

void() Intro_MMDomeThink =
{
	if (time >= self.ltime)
	{
		remove (self);
		return;
	}
	self.frame = floor (((1 - (self.ltime - time) / 0.85)) * 15);
	if (self.frame > 15)
		self.frame = 15;
	self.scale = self.scale + 0.10;
	self.nextthink = time + 0.04;
};

void(vector org, float sc0) Intro_SpawnMMDome =
{
	local entity d;

	d = spawn ();
	d.classname = "intro_prop";
	d.intro_tag = 1;
	d.movetype = MOVETYPE_NONE;
	d.solid = SOLID_NOT;
	setmodel (d, "progs/mm_explode.md3");
	d.scale = sc0;
	d.effects = EF_FULLBRIGHT;
	setsize (d, '0 0 0', '0 0 0');
	setorigin (d, org);
	d.ltime = time + 0.85;
	d.think = Intro_MMDomeThink;
	d.nextthink = time + 0.03;
};

void() Intro_RocketCanThink =
{
	pointparticles (particleeffectnum ("rocket_trail"), self.origin, '0 0 -1', 1);
	if (time > self.ltime)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.03;
};

void(vector org, vector vel) Intro_LaunchTrashcan =
{
	local entity c;

	c = spawn ();
	c.classname = "intro_prop";
	c.intro_tag = 1;
	c.movetype = MOVETYPE_FLY;
	c.solid = SOLID_NOT;
	setmodel (c, "progs/bklan/trashcan.md3");
	c.scale = 1.38;
	c.effects = EF_FULLBRIGHT;
	setsize (c, '0 0 0', '0 0 0');
	setorigin (c, org);
	c.velocity = vel;
	c.avelocity = '90 360 70';
	c.ltime = time + 3.4;
	c.think = Intro_RocketCanThink;
	c.nextthink = time + 0.02;

	Intro_BoomFX (org + '0 0 16');
	Intro_Cue ("weapons/rocket1i.wav", 0.86);
};

// ================================================================
// ACT V..VIII: MILKY INVASION, 360 ORBIT, 50-SWARM TORNADO & BURNING FOX FINALE
// ================================================================

void() Intro_MilkyFloatThink =
{
	local float u, sw_x, sw_z, bank;
	local vector pos, look_dir;

	if (time >= self.ltime)
	{
		sound (self, CHAN_VOICE, "misc/null.wav", 1, ATTN_NORM);
		remove (self);
		return;
	}

	u = (time - self.intro_born) / self.intro_spd;
	if (u < 0) u = 0;
	if (u > 1) u = 1;

	sw_x = ISin (time * 1.85 + self.intro_phase) * self.intro_rad;
	sw_z = ISin (time * 2.75 + self.intro_phase * 1.3) * 14;

	pos = self.intro_p0 + (self.intro_p1 - self.intro_p0) * u;
	pos_x = pos_x + sw_x;
	pos_z = pos_z + sw_z;
	setorigin (self, pos);

	look_dir = intro_cam_pos - pos;
	look_dir_z = 0;
	if (vlen (look_dir) < 10)
		look_dir = '0 -1 0';
	bank = ISin (time * 1.5 + self.intro_phase) * 42;
	makevectors ('0 1 0' * (vectoyaw (look_dir) + bank));
	self.milky_dir = v_forward;

	if (time >= self.milky_drip)
	{
		pointparticles (particleeffectnum ("milk_drip"), pos - '0 0 40' + v_right * (crandom () * 16), '0 0 0', 1);
		self.milky_drip = time + 0.22 + random () * 0.16;
	}
	if (time >= self.milky_ptrail)
	{
		Milk_SpawnFlightDrop (self, pos - '0 0 48', '0 0 -30');
		self.milky_ptrail = time + 0.75 + random () * 0.45;
	}

	self.nextthink = time + 0.02;
};

entity(vector p0, vector p1, float dur, float sc, float sway_r, float ph) Intro_SpawnMilkyUnit =
{
	local entity m;

	m = spawn ();
	m.classname = "milky";
	m.intro_tag = 1;
	m.movetype = MOVETYPE_NONE;
	m.solid = SOLID_NOT;
	m.effects = EF_FULLBRIGHT;
	setmodel (m, "progs/pinklady.md3");
	m.scale = sc;
	m.milky_owner = world;
	m.milky_born = time - 1.0;
	m.milky_dir = '0 -1 0';
	m.milky_drip = time + random () * 0.20;
	m.milky_ptrail = time + 0.20 + random () * 0.40;
	m.traileffectnum = particleeffectnum ("milky_trail");
	m.customizeentityforclient = Milky_Customize;
	m.intro_p0 = p0;
	m.intro_p1 = p1;
	m.intro_born = time;
	m.intro_spd = dur;
	m.intro_rad = sway_r;
	m.intro_phase = ph;
	m.ltime = time + dur + 0.2;
	setsize (m, '0 0 0', '0 0 0');
	setorigin (m, p0);
	m.think = Intro_MilkyFloatThink;
	m.nextthink = time + 0.02;
	return m;
};

void(entity m, float splash_lens) Intro_BurstMilky =
{
	local vector org;

	if (!m)
		return;
	org = m.origin;
	sound (m, CHAN_VOICE, "misc/null.wav", 1, ATTN_NORM);
	pointparticles (particleeffectnum ("milky_boom"), org, '0 0 0', 1);
	Milk_Splatter (org);
	Milk_Rain (org);

	Intro_Cue ("afrit/body_explode.wav", 0.78);
	Intro_Cue ("misc/h2ohit1.wav", 0.85);
	Intro_Cue ("weapons/goopop.wav", 0.82);
	Intro_Cue ("weapons/goosplat.wav", 0.88);

	if (splash_lens > 0)
		intro_milk_until = time + 1.4;

	remove (m);
};

void() Intro_MilkSkidderThink =
{
	local float u, f;
	local vector pos;

	if (time >= self.ltime)
	{
		remove (self);
		return;
	}
	u = (time - self.intro_born) / self.intro_spd;
	if (u < 0) u = 0;
	if (u > 1) u = 1;

	pos = self.intro_p0 + (self.intro_p1 - self.intro_p0) * u;
	pos_x = pos_x + ISin (time * 4.5 + self.intro_phase) * self.intro_rad;
	setorigin (self, pos);
	self.angles_y = self.angles_y + 13;

	if (time >= self.cnt)
	{
		self.cnt = time + 0.14;
		pointparticles (particleeffectnum ("milk_skid"), pos + '0 0 4', '0 0 35', 1);
	}
	if (self.mb_fn > 0)
	{
		f = floor (time * self.mb_fps + self.intro_phase);
		self.frame = self.mb_f0 + f - self.mb_fn * floor (f / self.mb_fn);
	}
	self.nextthink = time + 0.02;
};

void(entity e, vector p0, vector p1, float dur, float sway_r, float ph) Intro_AttachMilkSkid =
{
	if (!e)
		return;
	e.intro_p0 = p0;
	e.intro_p1 = p1;
	e.intro_born = time;
	e.intro_spd = dur;
	e.intro_rad = sway_r;
	e.intro_phase = ph;
	e.cnt = time + 0.05;
	e.ltime = time + dur + 0.2;
	e.think = Intro_MilkSkidderThink;
	e.nextthink = time + 0.02;
};

void(float dur) Intro_SpawnHStMilkies =
{
	local float i;
	local vector pspot;

	i = 0;
	while (i < 16)
	{
		pspot_x = -8795 - (i - 4 * floor (i / 4)) * 68 + crandom () * 16;
		pspot_y = 2245 + floor (i / 4) * 58 + crandom () * 14;
		pspot_z = 2;
		Milk_Splat (pspot, '0 0 1', 2.0 + random () * 1.1);
		i = i + 1;
	}

	ia_m0 = Intro_SpawnMilkyUnit ('-8835 2255 110', '-8895 2295 118', dur, 8.8, 20, 0.0);
	ia_m1 = Intro_SpawnMilkyUnit ('-8885 2345 138', '-8945 2385 146', dur, 9.6, 18, 1.1);
	ia_m2 = Intro_SpawnMilkyUnit ('-8815 2365 112', '-8875 2405 120', dur, 8.8, 20, 2.2);
	ia_m3 = Intro_SpawnMilkyUnit ('-8925 2285 116', '-8985 2325 124', dur, 9.4, 22, 0.6);
	ia_m4 = Intro_SpawnMilkyUnit ('-8965 2375 154', '-9025 2415 162', dur, 10.0, 18, 1.8);
	ia_m5 = Intro_SpawnMilkyUnit ('-8895 2425 148', '-8955 2465 156', dur, 9.8, 20, 2.9);
	ia_m6 = Intro_SpawnMilkyUnit ('-9010 2325 128', '-9070 2365 136', dur, 9.6, 22, 3.7);
	ia_m7 = Intro_SpawnMilkyUnit ('-9045 2415 172', '-9105 2455 180', dur, 10.4, 20, 4.4);
	ia_m8 = Intro_SpawnMilkyUnit ('-8985 2475 182', '-9045 2515 190', dur, 10.6, 18, 5.1);
	ia_m9 = Intro_SpawnMilkyUnit ('-9085 2365 168', '-9145 2405 176', dur, 10.2, 22, 5.8);
};

// Fast 360-Deg Fox Orbit Floaters (27.4s .. 31.0s)
vector(entity e, float t) Intro_Fox360FloaterPos =
{
	local float dst, lat, vof;

	Intro_ComputeCamBasis (t);
	dst = e.intro_rad + 6 * ICos (t * 2.5 + e.intro_slot * 0.9);
	lat = e.intro_lat + 9 * ISin (t * 2.8 + e.intro_slot * 1.1);
	vof = e.intro_gz + 11 * ISin (t * 3.3 + e.intro_slot * 1.4);
	return intro_b_pos + intro_b_fwd * dst + intro_b_rgt * lat + intro_b_up * vof;
};

void() Intro_Fox360FloaterThink =
{
	local float t;
	local vector pos, pos2;

	t = time - intro_t0;
	if (t < 27.4)
		t = 27.4;
	if (t >= 31.02)
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
		self.milky_dir = normalize (intro_cam_pos - pos + intro_b_rgt * (ISin (t * 2.6 + self.intro_phase) * 95));
		if (time >= self.milky_drip)
		{
			pointparticles (particleeffectnum ("milk_drip"), pos - '0 0 28', '0 0 0', 1);
			self.milky_drip = time + 0.22 + random () * 0.14;
		}
	}
	else
	{
		if (self.intro_slot == 5 && t >= 29.2)
			self.wc_anim = 2; // Zen Lotus Guru -> Supersonic Pipe-Jet Afterburner halfway around!
		self.angles_y = vectoyaw (intro_cam_pos - pos) + (t - 27.4) * 145 + self.intro_slot * 40;
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

		p0 = Intro_Fox360FloaterPos (e, 27.4);
		setorigin (e, p0);
		e.think = Intro_Fox360FloaterThink;
		e.nextthink = time + 0.01;

		idx = idx + 1;
	}
};

// Act VI & VII: 50-Entity Tower Tornado (31.0s .. 36.2s) -> All 50 Explode (36.2s .. 40.5s)!
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
	spin = dt * 140 + dt * dt * 23.0;
	ang = (e.intro_slot * 36 + e.intro_ring * 18 + spin * (1.0 + 0.07 * e.intro_ring)) * 0.01745329;
	rr = e.intro_rad + 14 * ISin ((intro_swarm_t0 + dt) * 2.8 + e.cnt * 0.7);
	pos_x = -9565 + ICos (ang) * rr;
	pos_y = 2525 + ISin (ang) * rr;
	pos_z = e.intro_gz + 14 * ISin ((intro_swarm_t0 + dt) * 3.3 + e.cnt * 0.9);
	return pos;
};

void() Intro_Swarm50Think =
{
	local float dt, idx, mod4, mod3, spin, ang, f;
	local vector pos, pos2, tvel;

	idx = self.cnt;

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

		if (self.classname == "intro_chaos_swarm")
		{
			Intro_SpawnMMDome (self.origin, 1.65);
			pointparticles (particleeffectnum ("mb_confetti"), self.origin, '0 0 60', 2);
			tvel_x = crandom () * 280;
			tvel_y = crandom () * 280;
			tvel_z = 220 + random () * 180;
			Intro_TossProp ("progs/mm_wheel.md3", self.origin, tvel, 1.55, 2.6);
			if (idx - 2 * floor (idx / 2) == 0)
				Intro_Cue ("weapons/megahorn.wav", 0.72);
			else
				Intro_Cue ("funny/heh.wav", 0.74);
			remove (self);
			return;
		}

		// Wheelman Sprite transforms in-place into 4-tier 360-deg 14-frame Fireball Explosion + flings axle/tires!
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
			tvel_x = crandom () * 260;
			tvel_y = crandom () * 260;
			tvel_z = 200 + random () * 180;
			Intro_TossProp ("progs/wc_bar.md3", self.origin, tvel, 1.35, 2.5);
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

		// Spire-top finale blast (#49) splashes thick white milk drips right onto the camera lens!
		if (idx == 49)
		{
			Intro_BoomFX ('-9565 2525 1065');
			Intro_SpawnSpriteBoom ('-9565 2525 920', 2.2);
			Intro_SpawnSpriteBoom ('-9565 2525 1060', 2.2);
			Intro_Cue ("weapons/megahorn.wav", 0.88);
			Intro_Cue ("afrit/body_explode.wav", 0.88);
			Intro_Cue ("weapons/goosplat.wav", 0.92);
			intro_milk_until = time + 2.75;
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

	spin = dt * 140 + dt * dt * 23.0;
	ang = (self.intro_slot * 36 + self.intro_ring * 18 + spin * (1.0 + 0.07 * self.intro_ring)) * 0.01745329;

	if (self.classname == "milky")
	{
		self.milky_dir_x = 0 - ISin (ang);
		self.milky_dir_y = ICos (ang);
		self.milky_dir_z = 0;
	}
	else if (self.classname == "intro_chaos_swarm")
	{
		self.angles_y = ang * 57.29578 + 90;
		if (self.pk_state == 4)
		{
			self.pk_front = vectoyaw (intro_cam_pos - pos);
			f = floor (time * 16 + self.intro_phase);
			self.frame = f - 12 * floor (f / 12);
		}
		else
		{
			f = floor (time * 18 + self.intro_phase);
			self.frame = f - 16 * floor (f / 16);
		}
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
		e.dmgtime = intro_swarm_t0 + 5.25 + idx * 0.044;
		setsize (e, '0 0 0', '0 0 0');

		// Slots 0, 2, 4, 6 (x5 = 20 Milky Milky Grenades!)
		if (slot == 0 || slot == 2 || slot == 4 || slot == 6)
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
		// Slot 8 (x5 = Giant Pickle Surprises & Spinning Mystery Boxes!)
		else if (slot == 8)
		{
			e.classname = "intro_chaos_swarm";
			if (ring - 2 * floor (ring / 2) == 0)
			{
				setmodel (e, "progs/pickle.md3");
				e.scale = 4.5;
				e.pk_state = 4;
				e.pk_t0 = time;
				e.pk_t = e.dmgtime;
				e.customizeentityforclient = Pk_Customize;
			}
			else
			{
				setmodel (e, "progs/proj_mysterybox.md3");
				e.scale = 2.8;
				e.traileffectnum = particleeffectnum ("mb_trail");
			}
		}
		// Slot 9 (x5 = Wheeled Mega Men & Angry Red Rob Dob Heads, except #49 = Spire Finale Wheelman!)
		else if (slot == 9 && idx < 49)
		{
			e.classname = "intro_chaos_swarm";
			if (ring - 2 * floor (ring / 2) == 0)
			{
				setmodel (e, "progs/megaman.md3");
				e.scale = 2.5;
			}
			else
			{
				setmodel (e, "progs/floathead.mdl");
				e.skin = 1;
				e.scale = 2.2;
			}
		}
		// Slots 1, 3, 5, 7 + #49 (21 Stunt Wheelman Sprites!)
		else
		{
			e.classname = "intro_wheelman_swarm";
			e.colormod = '1.26 1.26 1.26';
			if (slot == 1)
			{
				setmodel (e, "progs/wheelman.spr32");
				e.scale = 0.60;
				e.wc_anim = 1;
				e.customizeentityforclient = Intro_ClassicWheelCustomize;
			}
			else if (slot == 3)
			{
				setmodel (e, "progs/wheelman_historic.spr32");
				e.scale = 0.52;
				if (ring - 2 * floor (ring / 2) == 0)
					e.wc_anim = 8;
				else
					e.wc_anim = 2;
				e.intro_spd = 20;
				e.customizeentityforclient = Intro_HistWheelCustomize;
			}
			else if (slot == 5)
			{
				setmodel (e, "progs/wheelman.spr32");
				e.scale = 0.60;
				e.wc_anim = 3;
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
				e.scale = 0.62;
				e.wc_anim = 0;
				e.intro_fkind = 1;
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

// Act VIII: Blazing Fox Theater + Wrecked Van on Marquee + Floating DAN, Jetpack Wheelman, ROB & 24 CCCs!
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
	local entity wvan;

	Intro_SpawnFoxFireColumn ('-9290 2375 185', 4.6, 1, 1, 0);
	Intro_SpawnFoxFireColumn ('-9290 2465 235', 5.2, 0, 1, 1);
	Intro_SpawnFoxFireColumn ('-9290 2555 190', 4.8, 1, 1, 2);
	Intro_SpawnFoxFireColumn ('-9290 2645 238', 5.4, 0, 1, 3);
	Intro_SpawnFoxFireColumn ('-9290 2735 195', 4.6, 1, 1, 4);
	Intro_SpawnFoxFireColumn ('-9290 2825 236', 5.0, 0, 1, 5);
	Intro_SpawnFoxFireColumn ('-9345 2430 115', 4.0, 0, 0, 6);
	Intro_SpawnFoxFireColumn ('-9345 2610 118', 4.2, 0, 0, 7);

	Intro_SpawnFoxFireColumn ('-9440 2305 195', 4.6, 1, 1, 8);
	Intro_SpawnFoxFireColumn ('-9565 2355 215', 4.8, 0, 1, 9);
	Intro_SpawnFoxFireColumn ('-9695 2355 205', 4.5, 0, 1, 10);
	Intro_SpawnFoxFireColumn ('-9825 2355 225', 4.6, 0, 0, 11);
	Intro_SpawnFoxFireColumn ('-9575 2385 385', 5.2, 0, 1, 12);
	Intro_SpawnFoxFireColumn ('-9730 2425 410', 5.0, 0, 1, 13);

	Intro_SpawnFoxFireColumn ('-9420 2495 345', 5.4, 1, 1, 14);
	Intro_SpawnFoxFireColumn ('-9420 2585 455', 5.8, 0, 1, 15);
	Intro_SpawnFoxFireColumn ('-9420 2515 565', 5.6, 0, 1, 16);
	Intro_SpawnFoxFireColumn ('-9420 2635 570', 5.4, 0, 1, 17);
	Intro_SpawnFoxFireColumn ('-9550 2735 370', 5.0, 0, 1, 18);
	Intro_SpawnFoxFireColumn ('-9550 2845 480', 5.2, 0, 1, 19);
	Intro_SpawnFoxFireColumn ('-9550 2765 575', 5.4, 0, 1, 20);
	Intro_SpawnFoxFireColumn ('-9550 2895 575', 5.0, 0, 0, 21);

	Intro_SpawnFoxFireColumn ('-9430 2505 705', 6.0, 1, 1, 22);
	Intro_SpawnFoxFireColumn ('-9430 2610 720', 5.8, 0, 1, 23);
	Intro_SpawnFoxFireColumn ('-9435 2525 845', 6.4, 1, 1, 24);
	Intro_SpawnFoxFireColumn ('-9435 2615 860', 6.0, 0, 1, 25);
	Intro_SpawnFoxFireColumn ('-9460 2555 975', 6.5, 0, 1, 26);
	Intro_SpawnFoxFireColumn ('-9545 2475 835', 5.8, 0, 1, 27);

	// Comedy Callback: Smoldering Wrecked White Van blown right onto top of the blazing Fox Marquee canopy!
	wvan = spawn ();
	wvan.classname = "intro_van_wreck";
	wvan.intro_tag = 1;
	wvan.movetype = MOVETYPE_NONE;
	wvan.solid = SOLID_NOT;
	setmodel (wvan, "progs/veh_van_wreck.md3");
	wvan.frame = 19;
	wvan.scale = 1.15;
	wvan.effects = EF_FULLBRIGHT;
	wvan.angles = '14 148 -20';
	setsize (wvan, '0 0 0', '0 0 0');
	setorigin (wvan, '-9305 2480 206');

	Intro_MakeWheelDancer (2, 0.28, '-9290 2395 192');
	Intro_MakeWheelDancer (4, 0.28, '-9290 2575 192');
};

vector(entity e, float t) Intro_FloatHeroPos =
{
	local float dt, dst, lat, vof;

	dt = t - 40.5;
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
	if (t < 40.5)
		t = 40.5;

	pos = Intro_FloatHeroPos (self, t);
	pos2 = Intro_FloatHeroPos (self, t + 0.02);
	setorigin (self, pos);
	self.velocity = (pos2 - pos) * 50;
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

	dt = t - 40.5;
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
	if (t < 40.5)
		t = 40.5;

	pos = Intro_FloatCCCPos (self, t);
	pos2 = Intro_FloatCCCPos (self, t + 0.02);
	setorigin (self, pos);
	self.velocity = (pos2 - pos) * 50;
	self.nextthink = time + 0.01;
};

void() Intro_SpawnFloatingFinale =
{
	local entity dan, rob, jpw, c;
	local float i, ring, slot, ang0, rx, ry, dst, sc;
	local vector p0;

	// 1. Floating DAN (left-center)
	dan = spawn ();
	dan.classname = "intro_float_dan";
	dan.intro_tag = 1;
	dan.movetype = MOVETYPE_NOCLIP;
	dan.solid = SOLID_NOT;
	setmodel (dan, "progs/daniel.spr32");
	dan.scale = 0.24;
	dan.colormod = '1.35 1.35 1.35';
	dan.effects = EF_FULLBRIGHT;
	dan.intro_rad = 156;
	dan.intro_lat = -50;
	dan.intro_gz = -46;
	dan.intro_phase = 0.2;
	dan.intro_born = time;
	dan.cnt = time + 0.10;
	dan.customizeentityforclient = Intro_FloatDanCustomize;
	setsize (dan, '0 0 0', '0 0 0');
	p0 = Intro_FloatHeroPos (dan, 40.5);
	setorigin (dan, p0);
	dan.think = Intro_FloatHeroThink;
	dan.nextthink = time + 0.01;

	// 2. Floating ROB (right-center)
	rob = spawn ();
	rob.classname = "intro_float_rob";
	rob.intro_tag = 1;
	rob.movetype = MOVETYPE_NOCLIP;
	rob.solid = SOLID_NOT;
	setmodel (rob, "progs/fr_rob.spr32");
	rob.scale = 0.96;
	rob.colormod = '1.35 1.35 1.35';
	rob.effects = EF_FULLBRIGHT;
	rob.intro_rad = 158;
	rob.intro_lat = 50;
	rob.intro_gz = -46;
	rob.intro_phase = 2.1;
	rob.intro_born = time;
	rob.cnt = time + 0.18;
	rob.customizeentityforclient = Intro_FloatRobCustomize;
	setsize (rob, '0 0 0', '0 0 0');
	p0 = Intro_FloatHeroPos (rob, 40.5);
	setorigin (rob, p0);
	rob.think = Intro_FloatHeroThink;
	rob.nextthink = time + 0.01;

	// 3. Floating Jetpack Wheelman (center-top between DAN & ROB!)
	jpw = spawn ();
	jpw.classname = "intro_float_wheel";
	jpw.intro_tag = 1;
	jpw.movetype = MOVETYPE_NOCLIP;
	jpw.solid = SOLID_NOT;
	setmodel (jpw, "progs/wheelman.spr32");
	jpw.scale = 0.56;
	jpw.colormod = '1.32 1.32 1.32';
	jpw.effects = EF_FULLBRIGHT;
	jpw.wc_anim = 3;
	jpw.intro_rad = 188;
	jpw.intro_lat = 0;
	jpw.intro_gz = 32;
	jpw.intro_phase = 1.1;
	jpw.intro_born = time;
	jpw.cnt = time + 0.14;
	jpw.customizeentityforclient = Intro_ClassicWheelCustomize;
	setsize (jpw, '0 0 0', '0 0 0');
	p0 = Intro_FloatHeroPos (jpw, 40.5);
	setorigin (jpw, p0);
	jpw.think = Intro_FloatHeroThink;
	jpw.nextthink = time + 0.01;

	// 4. 24 Bright Yellow Spinning 'C's (progs/ccc.md3)
	i = 0;
	while (i < 24)
	{
		ring = floor (i / 12);
		slot = i - ring * 12;
		ang0 = (slot * 30 + ring * 15) * 0.01745329;

		if (ring == 0)
		{
			rx = 148;
			ry = 68;
			dst = 158 + 18 * ISin (i * 1.7);
			sc = 1.65;
		}
		else
		{
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
		p0 = Intro_FloatCCCPos (c, 40.5);
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
		if (e.classname != "player" && e != intro_dir_ent && e != intro_cam && e != intro_bgm_ent && e.solid != SOLID_BSP)
		{
			if (e.classname == "bk_cruiser" || e.classname == "bk_flyer" || e.veh_kind > 0 || e.classname == "veh_part" || e.classname == "bk_car" || e.classname == "bk_bicycle")
			{
				Intro_FreeCarClips (e);
				remove (e);
			}
			else if (e.classname == "crowd_spawner" || e.classname == "crowd_npc" || e.classname == "npc_crowd" || e.classname == "floathead_spawner" || e.classname == "floathead")
				remove (e);
			else if (e.classname == "npc_greensuit_wheelman" || e.classname == "npc_robeguy" || e.classname == "monster_daniel" || e.classname == "monster_daniel_dad")
				remove (e);
			else if (e.classname == "misc_vehicle_van" || e.classname == "misc_vehicle_sedan" || e.classname == "misc_vehicle_coupe" || e.classname == "misc_vehicle_truck")
			{
				Intro_FreeCarClips (e);
				remove (e);
			}
			else if ((e.flags & FL_ITEM) || e.model == "progs/jetpack.md3" || e.think == Jetpack_Place)
				remove (e);
		}
		e = nxt;
	}
};

// ================================================================
// MAIN 100HZ 8-ACT ESCALATING MOVIE SEQUENCER (0.0s .. 48.0s, CARDS 301..308)
// ================================================================

void() Intro_Tick =
{
	local entity p, e;
	local float t, u, f;
	local vector pos;

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
		cvar_set ("sv_gravity", "800");
		cvar_set ("sv_maxvelocity", "6500");
	}

	t = time - intro_t0;
	if (t < 0)
		t = 0;
	if (t < 2.0)
		Intro_PurgePlayerAttachments (p);

	// ================================================================
	// ACT I — CARD 301 (0.0s .. 5.5s): FOX THEATER CRANE-DOWN & WHITE VAN DRIFT ARRIVAL!
	// ================================================================
	if (t < 5.5)
	{
		intro_cur_card = 301;
		if (intro_ev < 1)
		{
			intro_ev = 1;
			Intro_ClearSpot ();
			Intro_EvalCam (301, t);

			sound (intro_bgm_ent, 1, "cdtracks/track013.ogg", 0.44, ATTN_NONE);

			// Peaceful Fox sidewalk before the White Van arrives: Cruiser Bike, Paul, Afro Boombox Guy & Selfie Lady
			Intro_SpawnSpinBike ("progs/bike_cruiser.md3", '-9014 2472 16', 320, 5.6);
			ia_spot1 = Intro_MakeActor (19, 1.24, '-9030 2442 6');
			Intro_AttachGroove (ia_spot1, 6.2, 7, 0, 5.6);
			ia_spot2 = Intro_MakeCrowd (20, 2, 1.22, '-9062 2410 30');
			Intro_AttachGroove (ia_spot2, 7.0, 5, 0, 5.6);
			ia_spot3 = Intro_MakeCrowd (21, 2, 1.18, '-8998 2502 30');
			Intro_AttachGroove (ia_spot3, 6.6, 5, 0, 5.6);

			Intro_Cue ("friends/hello.wav", 0.85);
		}
		// 1.85s: Enter the White ProMaster LAN Van ("6-Man LAN Van!") + Green-Suit Wheelman escort!
		if (t >= 1.85 && intro_ev < 2)
		{
			intro_ev = 2;
			sound (intro_cam, 6, "vehicles/lanvan.wav", 0.92, ATTN_NONE);

			ia_van = spawn ();
			ia_van.intro_tag = 1;
			setmodel (ia_van, "progs/veh_van.md3");
			ia_van.effects = EF_FULLBRIGHT;
			ia_van.colormod = '0.98 0.98 0.96';
			ia_van.angles = '0 268 0';
			setorigin (ia_van, '-8920 2830 2');

			ia_wheel2 = Intro_MakeGreenSuit (2, 1.26, '-8890 2690 2');
			Intro_AttachMover (ia_wheel2, '-8890 2690 2', '-8845 2290 2', 3.4, 4, 0);
		}
		// 3.70s: Handbrake J-Turn Tire Screech!
		if (t >= 3.70 && intro_ev < 3)
		{
			intro_ev = 3;
			Intro_Cue ("vehicles/tire_squeal.wav", 0.96);
		}
		// 4.65s: Van slams curbside & blasts horn!
		if (t >= 4.65 && intro_ev < 4)
		{
			intro_ev = 4;
			Intro_Cue ("vehicles/horn.wav", 0.96);
			sound (intro_cam, 6, "vehicles/idle_van.wav", 0.78, ATTN_NONE);
		}

		if (ia_van && t >= 1.85)
		{
			f = floor (time * 24);
			f = f - 16 * floor (f / 16);
			ia_van.frame = f;
			if (t < 3.75)
			{
				u = (t - 1.85) / 1.90;
				pos = '-8920 2830 2' + ('-8950 2470 2' - '-8920 2830 2') * u;
				ia_van.angles = '0 268 0';
				ia_van.angles_z = ISin (t * 11.0) * 2.2;
				setorigin (ia_van, pos);
			}
			else
			{
				u = (t - 3.75) / 1.55;
				if (u > 1) u = 1;
				pos = Intro_LerpVec ('-8950 2470 2', '-8995 2385 2', u);
				ia_van.angles_y = 268 - Intro_Smooth (u) * 123;
				ia_van.angles_z = ISin (u * 3.14159) * 9.5;
				setorigin (ia_van, pos);
				if (u < 0.85)
					pointparticles (intro_fx_vsmoke, pos - '0 35 -8', '0 0 32', 1);
			}
		}
	}

	// ================================================================
	// ACT II — CARD 302 (5.5s .. 11.0s): BARN DOORS BLOW OFF & WHEELMAN STUNT TRILOGY!
	// ================================================================
	else if (t < 11.0)
	{
		intro_cur_card = 302;
		if (intro_ev < 10)
		{
			intro_ev = 10;
			Intro_ClearSpot ();
			Intro_EvalCam (302, t);

			// Open-back White Van parked right behind Hero Wheelman!
			ia_van = spawn ();
			ia_van.intro_tag = 1;
			setmodel (ia_van, "progs/van_walkin.md3");
			ia_van.effects = EF_FULLBRIGHT;
			ia_van.colormod = '0.98 0.98 0.96';
			ia_van.angles = '0 145 0';
			setorigin (ia_van, '-8995 2385 2');

			// Rear barn doors blow clean off into the air!
			Intro_BoomFX ('-8882 2308 38');
			Intro_TossProp ("progs/veh_van_door.md3", '-8888 2322 42', '125 85 255',  1.05, 4.8);
			Intro_TossProp ("progs/veh_van_door.md3", '-8872 2292 42', '115 -95 265', 1.05, 4.8);

			// Hero Wheelman bursts out with Classic Fire-Wheels Burnout!
			ia_wheelman = Intro_MakeClassicWheel (1, 0, 0.72, '-8882 2310 2');

			// 3D Standing Wheelman Sculpture posing on the White Van roof!
			ia_vansurf = Intro_MakeWheel3D (2, 1.28, '-8965 2362 124', 325);

			// Green-Suit Wheelman carving wheelies + Daniel & Paul reacting!
			ia_wheel2 = Intro_MakeGreenSuit (2, 1.18, '-8818 2338 2');
			ia_spot1 = Intro_MakeActor (27, 1.22, '-8892 2252 2');
			Intro_AttachGroove (ia_spot1, 7.5, 14, 0, 5.6);
			ia_spot2 = Intro_MakeActor (19, 1.22, '-8828 2372 2');
			Intro_AttachGroove (ia_spot2, 6.8, 12, 0, 5.6);

			Intro_Cue ("wcannon/wc_boom.wav", 0.92);
			Intro_Cue ("larry/love_to_play_quake.wav", 1.0);
		}
		// 7.30s: Hero Wheelman flips upside-down into Inverted B-Boy Helicopter Headspin!
		if (t >= 7.30 && intro_ev < 11)
		{
			intro_ev = 11;
			if (ia_wheelman)
				remove (ia_wheelman);
			ia_wheelman = Intro_MakeHistWheel (8, 18, 0.45, '-8845 2288 2');
			Intro_BonkSparks ('-8845 2288 8', 0);
			Intro_Cue ("friends/gowewd.wav", 1.0);
		}
		// 8.60s: WEW Cannon Fighter charges out of the open White Van!
		if (t >= 8.60 && intro_ev < 12)
		{
			intro_ev = 12;
			dm_p3 = Intro_SpawnDMFighter (3, '-8915 2335 2', 2, 18, 110, 0, "progs/g_wewcannon.md3", 1.28, 2.5);
			Intro_Cue ("wcannon/wc_shoot.wav", 0.88);
		}
		// 9.20s: Hero Wheelman ignites Supersonic Pipe-Jet Afterburner right across the lens!
		if (t >= 9.20 && intro_ev < 13)
		{
			intro_ev = 13;
			if (ia_wheelman)
				remove (ia_wheelman);
			ia_wheelman = Intro_MakeHistWheel (2, 20, 0.46, '-8878 2262 24');
			ia_wheelman.traileffectnum = particleeffectnum ("rocket_trail");
			Intro_Cue ("wcannon/wc_lrun02.wav", 1.0);
			Intro_Cue ("jetpack/swoosh.wav", 0.92);
		}

		if (ia_wheelman)
		{
			if (t < 7.30)
			{
				u = (t - 5.5) / 1.80;
				pos = Intro_LerpVec ('-8882 2310 2', '-8845 2288 2', u);
				setorigin (ia_wheelman, pos);
				ia_wheelman.angles_y = vectoyaw (intro_cam_pos - pos) + ISin (t * 9.0) * 28;
			}
			else if (t < 9.20)
			{
				pos = '-8845 2288 2';
				pos_z = 2 + fabs (ISin (t * 8.0)) * 8;
				setorigin (ia_wheelman, pos);
				ia_wheelman.angles_y = vectoyaw (intro_cam_pos - pos) + (t - 7.30) * 220;
			}
			else
			{
				u = (t - 9.20) / 1.80;
				pos = Intro_LerpVec ('-8878 2262 24', '-8808 2338 48', u);
				setorigin (ia_wheelman, pos);
				ia_wheelman.angles_y = vectoyaw ('-8808 2338 48' - '-8878 2262 24');
			}
		}
		if (ia_vansurf)
			ia_vansurf.angles_y = 325 + (t - 5.5) * 140;
		if (ia_wheel2)
		{
			pos_x = -8818 + ICos (t * 4.5) * 24;
			pos_y = 2338 + ISin (t * 4.5) * 24;
			pos_z = 2;
			setorigin (ia_wheel2, pos);
			ia_wheel2.angles_y = vectoyaw (intro_cam_pos - pos);
		}
	}

	// ================================================================
	// ACT III — CARD 303 (11.0s .. 17.0s): CLOWN-CAR CAST PILEOUT & CUSTOM FUN-GUN ARSENAL!
	// ================================================================
	else if (t < 17.0)
	{
		intro_cur_card = 303;
		if (intro_ev < 20)
		{
			intro_ev = 20;
			Intro_ClearSpot ();
			Intro_EvalCam (303, t);

			// Keep the open White Van parked as an infinite clown car + 3D Thinker Wheelman on its roof!
			ia_van = spawn ();
			ia_van.intro_tag = 1;
			setmodel (ia_van, "progs/van_walkin.md3");
			ia_van.effects = EF_FULLBRIGHT;
			ia_van.colormod = '0.98 0.98 0.96';
			ia_van.angles = '0 145 0';
			setorigin (ia_van, '-8995 2385 2');

			ia_vansurf = Intro_MakeWheel3D (4, 1.32, '-8965 2362 124', 325);
			Intro_AttachGroove (ia_vansurf, 2.5, 0, 75, 6.2);

			// Wave 1 out of the van: 4 AM Daniel + Angry 4 AM Dad + Flying Oak Table, CRT Monitor & LAN Chair!
			ia_spot1 = Intro_MakeActor (27, 1.28, '-8935 2345 2');
			Intro_AttachMover (ia_spot1, '-8935 2345 2', '-8785 2225 2', 3.4, 8, 0);
			ia_spot2 = Intro_MakeActor (28, 1.26, '-8955 2360 2');
			Intro_AttachMover (ia_spot2, '-8955 2360 2', '-8820 2250 2', 3.6, 6, 0);

			Intro_TossProp ("progs/daniel_table.md3", '-8915 2330 36', '135 -110 265', 1.15, 5.5);
			Intro_TossProp ("progs/bklan/lan_mon1.md3", '-8905 2320 42', '155 -75 245', 1.25, 5.5);
			Intro_TossProp ("progs/bklan/lan_chair1.md3", '-8922 2340 38', '115 -140 250', 1.20, 5.5);

			// Matrix Cyber-Desk Wheelman + Laptop Gun Flying Head ("Canis Lupus!")
			ia_wheelman = Intro_MakeHistWheel (4, 18, 0.45, '-8840 2358 2');
			Intro_SpawnLaptopHead ('-8835 2352 44', '-8695 2195 62', 3.2);

			Intro_Cue ("daniel/dad_4am.wav", 0.95);
			Intro_Cue ("ltgun/type.wav", 0.88);
			Intro_Cue ("ltgun/canis.wav", 0.92);
		}
		// 12.5s: Wave 2 pours out of the White Van + NetSend CRT PC + Goo Foam + 777 Jackpot!
		if (t >= 12.50 && intro_ev < 21)
		{
			intro_ev = 21;
			e = Intro_MakeActor (23, 1.26, '-8935 2345 2');
			Intro_AttachMover (e, '-8935 2345 2', '-8815 2385 2', 4.0, 9, 0);
			e = Intro_MakeActor (24, 1.22, '-8945 2352 2');
			Intro_AttachMover (e, '-8945 2352 2', '-8775 2345 2', 4.0, 7, 0);
			e = Intro_MakeActor (17, 1.26, '-8935 2345 2');
			Intro_AttachMover (e, '-8935 2345 2', '-8895 2245 2', 4.0, 8, 0);
			e = Intro_MakeRobeGuy (2, 1.22, '-8935 2345 2');
			Intro_AttachMover (e, '-8935 2345 2', '-8865 2405 2', 4.0, 8, 0);
			e = Intro_MakeActor (21, 1.24, '-8935 2345 2');
			Intro_AttachMover (e, '-8935 2345 2', '-8935 2275 2', 4.0, 7, 0);

			Intro_TossProp ("progs/netsend_disk.md3", '-8885 2310 38', '110 -80 180', 1.5, 1.8);
			Intro_SpawnNetSendPC ('-8812 2282 2', 320, 4.4);
			Intro_StickGooFoam ('-8778 2258 4');
			Intro_StickGooFoam ('-8802 2322 4');
			Intro_StickGooFoam ('-8852 2242 4');

			Intro_Cue ("netsend/wheres_disk.wav", 0.92);
			Intro_Cue ("david/slot_jackpot.wav", 0.88);
		}
		// 14.0s: Wave 3 — Shaolin Wheel-Fu + Giant 64-Skin Inflating Pickle Surprise Diva!
		if (t >= 14.00 && intro_ev < 22)
		{
			intro_ev = 22;
			ia_wheel2 = Intro_MakeHistWheel (3, 18, 0.45, '-8890 2302 2');
			Intro_AttachGroove (ia_wheel2, 8.0, 10, 0, 3.0);
			ia_pickle = Intro_SpawnPickleDiva ('-8848 2308 2', 2.9);

			dm_p1 = Intro_SpawnDMFighter (1, '-8785 2252 2', 2, 16, 95,  0,   "progs/w_blueflail.mdl", 1.38, 3.0);
			dm_p3 = Intro_SpawnDMFighter (3, '-8815 2268 2', 2, 16, -95, 180, "progs/g_wewcannon.md3", 1.25, 3.0);
			dm_p1.enemy = dm_p3;
			dm_p3.enemy = dm_p1;

			Intro_Cue ("pickle/surprise.wav", 1.0);
		}
		// 15.45s: Wave 4 — BONK HAMMER FRYING-PAN *CLANG!* Ragdoll Sky-Launch!
		if (t >= 15.45 && intro_ev < 23)
		{
			intro_ev = 23;
			if (dm_p1)
			{
				dm_p1.cnt = 2;
				dm_p1.pain_finished = time + 0.45;
			}
			if (dm_p3)
			{
				Intro_BonkSparks (dm_p3.origin, 1);
				Intro_LaunchRagdoll (dm_p3, '-95 175 450');
			}
			Intro_Cue ("daniel/shaaa_scream.wav", 0.86);
		}
	}

	// ================================================================
	// ACT IV — CARD 304 (17.0s .. 24.0s): RUSH HOUR ON H STREET — EVERY GUN, VEHICLE & FLYER!
	// ================================================================
	else if (t < 24.0)
	{
		intro_cur_card = 304;
		if (intro_ev < 30)
		{
			intro_ev = 30;
			Intro_ClearSpot ();
			Intro_EvalCam (304, t);

			// Overheated White Van on curb + 3D Overhead Axle Titan Wheelman flexing on roof!
			ia_van = spawn ();
			ia_van.intro_tag = 1;
			setmodel (ia_van, "progs/veh_van.md3");
			ia_van.skin = 1;
			ia_van.frame = 24;
			ia_van.effects = EF_FULLBRIGHT;
			ia_van.angles = '0 145 0';
			setorigin (ia_van, '-9045 2425 2');
			ia_vansurf = Intro_MakeWheel3D (3, 1.38, '-9045 2425 124', 325);
			Intro_AttachGroove (ia_vansurf, 4.5, 4, 65, 7.1);

			// "It's Not Pink!" Exotic Supercar drag-racing 3D Seated Roller Wheelman, JessKart & Kyle!
			ia_pinkcar = spawn ();
			ia_pinkcar.intro_tag = 1;
			setmodel (ia_pinkcar, "progs/pink_supercar.md3");
			ia_pinkcar.scale = 1.08;
			ia_pinkcar.effects = EF_FULLBRIGHT;
			ia_pinkcar.frame = 36;
			Intro_AttachMover (ia_pinkcar, '-8815 2135 2', '-8965 2620 2', 4.6, 0, 0);

			ia_wheelman = Intro_MakeWheel3D (1, 1.42, '-8775 2165 34', 108);
			Intro_AttachMover (ia_wheelman, '-8775 2165 34', '-8925 2640 34', 4.6, 3, 0);

			e = Intro_MakeActor (10, 1.34, '-8745 2190 2');
			Intro_AttachMover (e, '-8745 2190 2', '-8895 2655 2', 4.6, 7, 0);
			e = Intro_MakeActor (11, 1.30, '-8855 2195 2');
			Intro_AttachMover (e, '-8855 2195 2', '-8995 2585 2', 4.6, 7, 0);

			// Chrome Yellow School Bus & Orange Forklift rumbling down the far lane!
			ia_bus = spawn ();
			ia_bus.intro_tag = 1;
			setmodel (ia_bus, "progs/veh_schoolbus.md3");
			ia_bus.effects = EF_FULLBRIGHT;
			Intro_AttachMover (ia_bus, '-9135 2720 2', '-9080 2230 2', 5.4, 0, 0);

			ia_forklift = Intro_MakeActor (8, 1.18, '-9085 2620 2');
			Intro_AttachMover (ia_forklift, '-9085 2620 2', '-9035 2260 2', 5.4, 0, 0);

			// 3 Shootable 3D Bicycles spinning tires + TF Level-2 Sentry + M4, Tommy & Garand Fighters!
			Intro_SpawnSpinBike ("progs/bike_cruiser.md3", '-8730 2235 16', 135, 7.0);
			Intro_SpawnSpinBike ("progs/bike_bmx.md3",     '-8762 2275 14', 145, 7.0);
			Intro_SpawnSpinBike ("progs/bike_road.md3",    '-8794 2315 16', 155, 7.0);
			Intro_SpawnSentry ('-8742 2182 2', 135, 7.0);

			dm_p1 = Intro_SpawnDMFighter (1, '-8785 2215 2', 2, 22, 115, 0,   "progs/p_m4.md3",     1.28, 7.0);
			dm_p2 = Intro_SpawnDMFighter (2, '-8835 2265 2', 2, 24, -115, 90, "progs/p_tommy.md3",  1.28, 7.0);
			dm_p3 = Intro_SpawnDMFighter (3, '-8885 2315 2', 2, 22, 110, 180, "progs/p_garand.md3", 1.28, 7.0);

			// Sky Chaos: 2 Winged John-Birds, Podracer Sky-Chariot, Jetpack Fighter & 2 Rob Dob Heads!
			Intro_SpawnJohnBird ('-8740 2120 148', '-9160 2560 215', 5.2, 1.25);
			Intro_SpawnJohnBird ('-9140 2580 185', '-8720 2160 162', 5.2, 1.20);
			Intro_SpawnRobDob   ('-8710 2185 118', '-9040 2450 155', 3.4, 1.65);
			Intro_SpawnRobDob   ('-9060 2490 142', '-8750 2220 128', 3.8, 1.65);

			e = spawn ();
			e.intro_tag = 1;
			setmodel (e, "progs/skyveh_v3.md3");
			e.scale = 1.05;
			e.effects = EF_FULLBRIGHT;
			Intro_AttachMover (e, '-9180 2640 245', '-8690 2140 225', 5.2, 4, 0);

			ia_jp1 = spawn ();
			ia_jp1.intro_tag = 1;
			setmodel (ia_jp1, "progs/jetpack.md3");
			ia_jp1.scale = 1.65;
			ia_jp1.effects = EF_FULLBRIGHT;
			ia_jp1.traileffectnum = particleeffectnum ("jp_fire");
			Intro_AttachMover (ia_jp1, '-8820 2210 95', '-9090 2490 250', 5.0, 6, 0);

			Intro_Cue ("bklan/notpink.wav", 0.96);
			Intro_Cue ("bikes/bell_ring.wav", 0.88);
			Intro_Cue ("cs16/m4a1_unsil-1.wav", 0.78);
			Intro_Cue ("dod/thompson_shoot.wav", 0.78);
			Intro_Cue ("floathead/calc/c2.wav", 0.82);
		}
		// 18.25s: M1 Garand 8th-round shot + iconic en-bloc *PING!* + John-Bird cry!
		if (t >= 18.25 && intro_ev < 31)
		{
			intro_ev = 31;
			Intro_Cue ("dod/garand_shoot.wav", 0.86);
			Intro_Cue ("dod/garand_reload_clipding.wav", 0.98);
			Intro_Cue ("john_bird/jv_fly03.wav", 0.88);
		}
		// 19.35s: Mega Man Chariot + 3D Riders + Shatter Dome + Mystery Box Confetti Explosion!
		if (t >= 19.35 && intro_ev < 32)
		{
			intro_ev = 32;
			e = Intro_MakeActor (1, 1.75, '-8880 2325 14');
			Intro_AttachGroove (e, 8.0, 12, 0, 4.5);
			e = Intro_MakeActor (2, 1.30, '-8925 2365 14');
			Intro_AttachGroove (e, 7.5, 10, 0, 4.5);
			e = Intro_MakeActor (4, 1.30, '-8845 2285 14');
			Intro_AttachGroove (e, 7.8, 10, 0, 4.5);

			Intro_SpawnMMDome ('-8880 2325 36', 1.75);
			Intro_TossProp ("progs/mm_wheel.md3", '-8880 2325 32', '155 -125 275', 1.55, 4.2);
			Intro_TossProp ("progs/mm_wheel.md3", '-8880 2325 32', '-145 135 285', 1.55, 4.2);

			// Mystery Box bursts into confetti & Bakersfield roster monsters!
			Intro_TossProp ("progs/proj_mysterybox.md3", '-8945 2380 48', '45 -45 235', 1.85, 4.2);
			pointparticles (particleeffectnum ("mb_confetti"), '-8945 2380 48', '0 0 80', 3);
			e = Intro_MakeActor (22, 1.38, '-8915 2415 2');
			Intro_AttachGroove (e, 9.0, 26, 0, 4.5);
			e = Intro_MakeActor (6,  1.05, '-8975 2345 12');
			Intro_AttachGroove (e, 6.8, 10, 0, 4.5);
			e = Intro_MakeActor (7,  1.12, '-8955 2445 18');
			Intro_AttachGroove (e, 6.5, 8,  0, 4.5);
			e = Intro_MakeCrowd (12, 2, 1.24, '-8865 2395 2');
			Intro_AttachGroove (e, 7.4, 10, 0, 4.5);
			e = Intro_MakeCrowd (22, 2, 1.24, '-8995 2395 28');
			Intro_AttachGroove (e, 7.0, 6,  0, 4.5);

			Intro_Cue ("megaman/mm_fire.wav", 0.94);
			Intro_Cue ("weapons/megahorn.wav", 0.90);
			Intro_Cue ("misc/r_tele5.wav", 0.85);
			Intro_Cue ("mbox/drv_boing_hop.wav", 0.88);
		}
		// 21.50s: JohnWave Tidal Ring + Triple NASA Rocket Trash Can Liftoff!
		if (t >= 21.50 && intro_ev < 33)
		{
			intro_ev = 33;
			Intro_TossProp ("progs/grenade.mdl", '-8875 2320 38', '35 -25 190', 1.85, 2.2);
			Intro_SpawnJohnWave ('-8875 2320 6');

			Intro_LaunchTrashcan ('-8825 2275 4', '-35 45 580');
			Intro_LaunchTrashcan ('-8935 2365 4', '25 -30 620');
			Intro_LaunchTrashcan ('-9020 2445 6', '-20 35 600');

			Intro_Cue ("funny/quakeahh.wav", 0.94);
			Intro_Cue ("larry/double_good.wav", 0.92);
		}
	}

	// ================================================================
	// ACT V — CARD 305 (24.0s .. 31.0s): MILKY INVASION ON H ST -> FAST 360 FOX ORBIT!
	// ================================================================
	else if (t < 31.0)
	{
		intro_cur_card = 305;
		// Part A (24.0s .. 27.4s): 10 Singing Milkys + Slippery Milk Puddle Spinouts on H St!
		if (intro_ev < 50)
		{
			intro_ev = 50;
			Intro_ClearSpot ();
			Intro_EvalCam (305, t);

			// Drop the non-stop Milky Milky Song for the rest of the movie (24.0s -> 47.95s)!
			intro_bgm_on = TRUE;
			sound (intro_bgm_ent, 1, "milky/song.ogg", 0.96, ATTN_NONE);

			Intro_SpawnHStMilkies (3.35);

			ia_wheelman = Intro_MakeClassicWheel (0, 1, 0.72, '-8815 2275 2');
			Intro_AttachMilkSkid (ia_wheelman, '-8815 2275 2', '-8935 2355 2', 3.3, 38, 0.0);

			ia_wheel2 = Intro_MakeHistWheel (8, 20, 0.44, '-8865 2325 2');
			Intro_AttachMilkSkid (ia_wheel2, '-8865 2325 2', '-8985 2405 2', 3.3, 36, 2.1);

			ia_dancer = Intro_MakeWheelDancer (3, 0.24, '-8835 2355 2');
			Intro_AttachMilkSkid (ia_dancer, '-8835 2355 2', '-8955 2435 2', 3.3, 34, 3.6);

			ia_spot1 = Intro_MakeActor (27, 1.26, '-8885 2295 2');
			Intro_AttachMilkSkid (ia_spot1, '-8885 2295 2', '-9005 2375 2', 3.3, 42, 4.4);

			dm_p2 = Intro_SpawnDMFighter (2, '-8845 2305 2', 2, 32, 135, 0,   "progs/g_rock2.mdl", 1.25, 3.35);
			dm_p1 = Intro_SpawnDMFighter (1, '-8915 2355 2', 2, 32, -135, 160, "progs/p_m4.md3",    1.25, 3.35);

			Intro_Cue ("milky/fire.wav", 0.94);
			Intro_Cue ("wcannon/wc_scream.wav", 0.80);
		}
		if (t >= 26.05 && intro_ev < 51)
		{
			intro_ev = 51;
			Intro_BurstMilky (ia_m3, 1);
			ia_m3 = world;
			Intro_LaunchRagdoll (dm_p2, '95 75 340');
			Intro_Cue ("player/pain3.wav", 0.90);
		}
		if (t >= 26.75 && intro_ev < 52)
		{
			intro_ev = 52;
			Intro_BurstMilky (ia_m5, 0);
			ia_m5 = world;
			Intro_LaunchRagdoll (dm_p1, '-105 65 350');
			Intro_Cue ("wcannon/wc_lrun05.wav", 0.88);
		}
		// Part B (27.4s .. 31.0s): Whiplash 360-Deg Aerial Orbit Around the Historic Fox Theater!
		if (t >= 27.40 && intro_ev < 55)
		{
			intro_ev = 55;
			intro_milk_until = 0;
			Intro_ClearSpot ();
			Intro_EvalCam (305, t);
			Intro_SpawnFox360Floaters ();
			Intro_Cue ("funny/wewe.wav", 0.85);
			Intro_Cue ("friends/gowewd.wav", 0.86);
		}
	}

	// ================================================================
	// ACT VI — CARD 306 (31.0s .. 36.2s): 50-ENTITY TOWER TORNADO!!
	// ================================================================
	else if (t < 36.2)
	{
		intro_cur_card = 306;
		if (intro_ev < 60)
		{
			intro_ev = 60;
			Intro_ClearSpot ();
			Intro_EvalCam (306, t);
			Intro_Spawn50TowerSwarm ();

			Intro_Cue ("bryan/noway.wav", 0.96);
			Intro_Cue ("milky/fire.wav", 0.84);
		}
		if (t >= 33.60 && intro_ev < 61)
		{
			intro_ev = 61;
			Intro_Cue ("wcannon/wc_scream.wav", 0.84);
			Intro_Cue ("pickle/surprise.wav", 0.86);
		}
	}

	// ================================================================
	// ACT VII — CARD 307 (36.2s .. 40.5s): ALL 50 EXPLODE AT ONCE + LENS MILK SPLAT!!
	// ================================================================
	else if (t < 40.5)
	{
		intro_cur_card = 307;
		if (intro_ev < 70)
		{
			intro_ev = 70;
			Intro_Cue ("wcannon/wc_shoot.wav", 0.88);
			Intro_Cue ("daniel/shaaa_scream.wav", 0.86);
		}
	}

	// ================================================================
	// ACT VIII — CARD 308 (40.5s .. 48.0s): FOX ON FIRE + WRECKED VAN + FLOATING DAN, WHEELMAN, ROB & 24 CCCs!
	// ================================================================
	else
	{
		intro_cur_card = 308;
		if (intro_ev < 80)
		{
			intro_ev = 80;
			Intro_ClearSpot ();
			Intro_EvalCam (308, t);
			Intro_SpawnBurningFoxTheater ();
			Intro_SpawnFloatingFinale ();

			Intro_Cue ("player/inflame.wav", 0.80);
			Intro_Cue ("vehicles/fire_burn.wav", 0.60);
			Intro_Cue ("ccc/bounce.wav", 0.78);
		}
		// 40.80s: "I'm floating!"
		if (t >= 40.80 && intro_ev < 81)
		{
			intro_ev = 81;
			Intro_VocalHero ("jetpack/floating.wav", 1.0, 4);
			Intro_Cue ("funny/imfloating.wav", 0.95);
		}
		// 42.20s: "Ah, I can't see!"
		if (t >= 42.20 && intro_ev < 82)
		{
			intro_ev = 82;
			Intro_VocalHero ("ccc/shoot.wav", 1.0, 5);
		}
		// 43.45s: "CCC! C-C-C-C!" + ricochet boing
		if (t >= 43.45 && intro_ev < 83)
		{
			intro_ev = 83;
			Intro_Cue ("daniel/ccc_burst.wav", 0.90);
			Intro_Cue ("ccc/bounce.wav", 0.74);
			Intro_Cue ("vehicles/fire_burn.wav", 0.54);
		}
		// 45.05s: Second "I'm floating!" beat
		if (t >= 45.05 && intro_ev < 84)
		{
			intro_ev = 84;
			Intro_VocalHero ("jetpack/floating.wav", 1.0, 4);
			Intro_Cue ("funny/imfloating.wav", 0.92);
		}
		// 46.45s: Final punchline "Ah, I can't see!" right before fadeout!
		if (t >= 46.45 && intro_ev < 85)
		{
			intro_ev = 85;
			Intro_VocalHero ("ccc/shoot.wav", 1.0, 5);
			Intro_Cue ("ccc/bounce.wav", 0.70);
		}

		if (t >= 47.95 && !intro_stopped)
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
		if (t >= 48.45 && !intro_quitted)
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
	intro_cur_card = 301;
	intro_cam_pos = '-8590 2115 128';
	intro_cam_ang = Intro_LookAngles ('-8590 2115 128', '-9340 2485 310');

	intro_dir_ent = spawn ();
	intro_dir_ent.classname = "intro_director";
	intro_dir_ent.think = Intro_Tick;
	intro_dir_ent.nextthink = time + 0.02;
};
