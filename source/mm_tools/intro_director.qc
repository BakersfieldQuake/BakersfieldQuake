#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BAKERSFIELD QUAKE STARTUP INTRO DIRECTOR (intro_director.qc)

Compiled ONLY into the isolated temporary build (source/mm_tools/out/qc_intro_build -> progs_intro.dat)
by build_intro_demo.py to record BakersfieldQuake/intro.dem across bklan5's Bakersfield landmarks:
  1-2. Bakersfield Sign (Sillect Ave): Calm White LAN Van opening -> All 19 characters pile out & make their sounds!
  3.   Fox Theater Marquee (20th & H St): Rob Dob Gun + "It's Not Pink!" Supercar + Podracer + Mini-Dobs
  4.   Fox Theater Eva's Lounge & Live TV: Pickle Surprise Gun ambushes Dennis & Paul watching TV
  5.   Fox Theater Auditorium & Sunburst Stage: Wheelman Cannon (+58 deg) + Stunt Dancer + Milky Opera & Screen Milk!
  6.   Padre Hotel (H & Wall St): 8-story sky float with Duke Nukem Jetpacks ("I'm floating!!")
  7.   Padre Hotel 96-ft Neon Rooftop: TF Spanner -> Level-2 Sentry Gun + TF Sniper Laser + CCC 'C' Bolts vs. Kyle
  8.   Larry's Warehouse (118/120 TV Hall): Bonk Hammer spinny + Frying-Pan SLAM vs. Mr. DIY & Orange Forklift
  9.   Larry's B-LAN 130A CRT Party Hall: NetSend LOL.BAT Floppy PC + 3D Laptop Gun zapping Friend Rob
  10.  Larry's 120A Mega Man Bedroom Shrine: Red-Shop-Rag Chrome Polish + Slingshot Fork + Headcrab Leap!
  11.  ORCOM Connect Banquet LAN Hall: Goo Gun expanding foam stack + Pong Balls vs. Giant 3D Big-Ears
  12.  Golden West Casino & Giant Horse: David Ojeda 777 Slot Jackpot, Money Bag Sprint & Pregnant Trio
  13.  Buck Owens' Crystal Palace & KUZZ Van: Mystery Box crystal ball -> Tinfoil-Hat Bryan, 3 Demons & Hell Portal
  14.  Amberton Park Picnic Shelter: JohnWave 3D Head Grenade tidal splash, Wheelie Riders & Rocket Trash Can
  15.  Full-Circle Finale Back Under the Bakersfield Sign: White LAN Van + Roof-Dancing Wheelman rolls out!

Never modifies BakersfieldQuake/progs.dat; intro.dem is a pure network packet recording that plays back
under the normal game progs.dat + csprogs.dat via quake.rc's `startdemos intro`.
Camera paths are lockstep-matched with BM_UpdateIntroCam() in csqc/bm_hud.qc for 150+ Hz zero-shake floating motion.
================
*/

.float	intro_st_card;		// clientstat 69 -> CSQC BM_UpdateIntroCam, BM_UpdateIntroVM & BM_DrawIntroHUD
.float	intro_st_t0;		// clientstat 70 -> intro_t0 in milliseconds (constant clock anchor)
.float	intro_tag;			// 1 on every temporary entity spawned by intro_director for instant scene cleanup
.float	intro_phase;
.float	intro_spd;
.float	intro_rad;
.float	intro_cx;
.float	intro_cy;
.float	intro_born;
.vector	intro_door;

entity	intro_dir_ent;
entity	intro_cam;
float	intro_t0;
float	intro_t0_ms;
float	intro_ev;
float	intro_stopped;
float	intro_quitted;
float	intro_cam_fixed;

vector	intro_cam_pos;
vector	intro_cam_ang;
float	intro_cur_card;

// Key actors across scenes
entity	ia_van;
entity	ia_vansurf;
entity	ia_pinkcar;
entity	ia_forklift;
entity	ia_pod1;
entity	ia_robdob;
entity	ia_pkbomb;
entity	ia_pickle;
entity	ia_wheelman;
entity	ia_dancer;
entity	ia_milky;
entity	ia_spot1;
entity	ia_spot2;
entity	ia_spot3;
entity	ia_spot4;
entity	ia_spot5;
entity	ia_jp1;
entity	ia_jp2;
entity	ia_turrbase;
entity	ia_turrgun;
entity	ia_sight;
entity	ia_nspc;
entity	ia_nsarc;
entity	ia_ltg_head;
entity	ia_ltg_aura;

void() Intro_Precache =
{
	precache_model ("progs/spike.mdl");
	precache_model ("progs/wheelman.spr32");
	precache_model ("progs/wheelman_dance.spr32");
	precache_model ("progs/mm_wheel.md3");
	precache_model ("progs/pinklady.md3");
	precache_model ("progs/milksplat.md3");
	precache_model ("progs/floathead.mdl");
	precache_model ("progs/pickle.md3");
	precache_model ("progs/pickle_bomb.md3");
	precache_model ("progs/pickle_gib.md3");
	precache_model ("progs/david.spr32");
	precache_model ("progs/preg_1.spr32");
	precache_model ("progs/preg_2.spr32");
	precache_model ("progs/preg_3.spr32");
	precache_model ("progs/bryan.spr32");
	precache_model ("progs/proj_mysterybox.md3");
	precache_model ("progs/jesskart.spr32");
	precache_model ("progs/fr_dennis.spr32");
	precache_model ("progs/fr_paul.spr32");
	precache_model ("progs/fr_mrdiy.spr32");
	precache_model ("progs/fr_scissors.spr32");
	precache_model ("progs/fr_rob.spr32");
	precache_model ("progs/fr_quakeguy.spr32");
	precache_model ("progs/fr_finger.spr32");
	precache_model ("progs/player_shot.mdl");
	precache_model ("progs/megaman.md3");
	precache_model ("progs/mm_explode.md3");
	precache_model ("progs/mm_suit_rider.md3");
	precache_model ("progs/mm_squat_rider.md3");
	precache_model ("progs/gw_horse.md3");
	precache_model ("progs/bigears.md3");
	precache_model ("progs/johnhead3d.md3");
	precache_model ("progs/netsend_disk.md3");
	precache_model ("progs/netsend_pc.md3");
	precache_model ("progs/netsend_arc.md3");
	precache_model ("progs/netsend_laser.md3");
	precache_model ("progs/ltg_head.md3");
	precache_model ("progs/ltg_aura.md3");
	precache_model ("progs/ltg_laser.md3");
	precache_model ("progs/grenade.mdl");
	precache_model ("progs/jw_splash.spr32");
	precache_model ("progs/jw_ripple.spr32");
	precache_model ("progs/jw_wave.md3");
	precache_model ("progs/goo.md3");
	precache_model ("progs/ccc.md3");
	precache_model ("progs/fg_pongball.md3");
	precache_model ("progs/spark_blue.mdl");
	precache_model ("progs/spark_yellow.mdl");
	precache_model ("progs/pink_supercar.md3");
	precache_model ("progs/skyveh_v3.md3");
	precache_model ("progs/veh_van.md3");
	precache_model ("progs/bklan/trashcan.md3");
	precache_model ("progs/bklan/sr_vehicle_forklift_orange_a01.md3");
	precache_model ("progs/jetpack.md3");
	precache_model ("progs/turrbase.mdl");
	precache_model ("progs/turrgun.mdl");
	precache_model ("progs/g_srifle.mdl");
	precache_model ("progs/sight.spr");

	precache_sound ("vehicles/idle_van.wav");
	precache_sound ("vehicles/lanvan.wav");
	precache_sound ("vehicles/horn.wav");
	precache_sound ("vehicles/tire_squeal.wav");
	precache_sound ("bklan/pinkcar.wav");
	precache_sound ("bklan/notpink.wav");
	precache_sound ("larry/love_to_play_quake.wav");
	precache_sound ("larry/double_good.wav");
	precache_sound ("larry/play_with_knives.wav");
	precache_sound ("larry/it_wont_boot.wav");
	precache_sound ("friends/hello.wav");
	precache_sound ("friends/gowewd.wav");
	precache_sound ("friends/no.wav");
	precache_sound ("friends/interesting.wav");
	precache_sound ("friends/megamayan.wav");
	precache_sound ("wcannon/wc_charge.wav");
	precache_sound ("wcannon/wc_shoot.wav");
	precache_sound ("wcannon/wc_scream.wav");
	precache_sound ("wcannon/wc_boom.wav");
	precache_sound ("pickle/throw.wav");
	precache_sound ("pickle/surprise.wav");
	precache_sound ("milky/song.ogg");
	precache_sound ("milky/fire.wav");
	precache_sound ("afrit/body_explode.wav");
	precache_sound ("weapons/goofire.wav");
	precache_sound ("weapons/goosplat.wav");
	precache_sound ("weapons/tink1.wav");
	precache_sound ("weapons/megamotor.wav");
	precache_sound ("weapons/megahorn.wav");
	precache_sound ("weapons/rocket1i.wav");
	precache_sound ("weapons/lhit.wav");
	precache_sound ("weapons/lstart.wav");
	precache_sound ("weapons/turrset.wav");
	precache_sound ("weapons/turrspot.wav");
	precache_sound ("weapons/sniper.wav");
	precache_sound ("hackmon/hm_launch.wav");
	precache_sound ("floathead/sight1.wav");
	precache_sound ("floathead/charge.wav");
	precache_sound ("floathead/boing.wav");
	precache_sound ("funny/heh.wav");
	precache_sound ("funny/fart2.wav");
	precache_sound ("funny/quakeahh.wav");
	precache_sound ("funny/wewe.wav");
	precache_sound ("funny/durr.wav");
	precache_sound ("david/shower_love.wav");
	precache_sound ("david/money_bag.wav");
	precache_sound ("david/slot_jackpot.wav");
	precache_sound ("bryan/detector.wav");
	precache_sound ("bryan/noway.wav");
	precache_sound ("bryan/whirl.wav");
	precache_sound ("bryan/portal_die.wav");
	precache_sound ("mrdiy/mrdiy_jingle.wav");
	precache_sound ("mbox/drv_boing_hop.wav");
	precache_sound ("john/jv15.wav");
	precache_sound ("john/jv11.wav");
	precache_sound ("megaman/mm_fire.wav");
	precache_sound ("netsend/wheres_disk.wav");
	precache_sound ("netsend/ns_beep.wav");
	precache_sound ("ltgun/type.wav");
	precache_sound ("ltgun/canis.wav");
	precache_sound ("ltgun/zap.wav");
	precache_sound ("hammer/charge_full.wav");
	precache_sound ("hammer/frying_pan.wav");
	precache_sound ("hammer/slice1.wav");
	precache_sound ("fungun/fg_bonk_hit.wav");
	precache_sound ("grenade/bounce_08_rubber_ball.wav");
	precache_sound ("grenade/boom_03_scream_launch.wav");
	precache_sound ("grenade/boom_04_mega_fart.wav");
	precache_sound ("jetpack/floating.wav");
	precache_sound ("jetpack/swoosh.wav");
	precache_sound ("ccc/shoot.wav");
	precache_sound ("misc/r_tele5.wav");
	precache_sound ("misc/null.wav");
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

// Exact lockstep SSQC twin of BM_UpdateIntroCam() in csqc/bm_hud.qc across all 15 bklan5 scenes (0.0s .. 78.0s)
void(float card, float t) Intro_EvalCam =
{
	local float u;
	local vector cpos, look;

	if (card == 1)
	{
		u = t / 4.4;
		cpos = Intro_LerpVec ('11520 -2736 98', '11700 -2736 62', u);
		look = Intro_LerpVec ('12180 -2736 86', '12160 -2736 68', u);
	}
	else if (card == 2)
	{
		u = (t - 4.4) / 7.0;
		cpos = Intro_LerpVec ('11700 -2736 62', '11540 -2736 128', u);
		look = Intro_LerpVec ('12160 -2736 68', '12160 -2736 88', u);
	}
	else if (card == 3)
	{
		u = (t - 11.4) / 5.0;
		cpos = Intro_LerpVec ('1340 -11560 84', '1120 -11340 62', u);
		look = Intro_LerpVec ('780 -11040 138', '780 -11040 125', u);
	}
	else if (card == 4)
	{
		u = (t - 16.4) / 5.0;
		cpos = Intro_LerpVec ('618 -10268 46', '618 -10198 43', u);
		look = Intro_LerpVec ('610 -10065 56', '610 -10055 64', u);
	}
	else if (card == 5)
	{
		u = (t - 21.4) / 5.6;
		cpos = Intro_LerpVec ('48 -9520 94', '48 -9250 78', u);
		look = Intro_LerpVec ('48 -9030 84', '48 -9020 78', u);
	}
	else if (card == 6)
	{
		u = (t - 27.0) / 5.0;
		cpos = Intro_LerpVec ('860 -17220 560', '780 -17300 1185', u);
		look = Intro_LerpVec ('520 -17510 760', '280 -17555 1235', u);
	}
	else if (card == 7)
	{
		u = (t - 32.0) / 5.0;
		cpos = Intro_LerpVec ('-240 -18120 1212', '-110 -17980 1206', u);
		look = Intro_LerpVec ('60 -17660 1208', '90 -17640 1208', u);
	}
	else if (card == 8)
	{
		u = (t - 37.0) / 5.0;
		cpos = Intro_LerpVec ('-744 -755 36', '-744 -675 32', u);
		look = Intro_LerpVec ('-744 -565 48', '-744 -565 52', u);
	}
	else if (card == 9)
	{
		u = (t - 42.0) / 5.4;
		cpos = Intro_LerpVec ('436 -758 30', '472 -758 27', u);
		look = '548 -758 38';
	}
	else if (card == 10)
	{
		u = (t - 47.4) / 5.4;
		cpos = Intro_LerpVec ('-1050 -2195 29', '-1098 -2195 26', u);
		look = Intro_LerpVec ('-1215 -2190 40', '-1225 -2188 40', u);
	}
	else if (card == 11)
	{
		u = (t - 52.8) / 5.0;
		cpos = Intro_LerpVec ('6300 1134 34', '6235 1134 30', u);
		look = '6125 1134 38';
	}
	else if (card == 12)
	{
		u = (t - 57.8) / 5.0;
		cpos = Intro_LerpVec ('-6397 -12145 34', '-6397 -12085 29', u);
		look = '-6397 -11990 48';
	}
	else if (card == 13)
	{
		u = (t - 62.8) / 5.0;
		cpos = Intro_LerpVec ('11730 -3745 34', '11730 -3792 29', u);
		look = '11730 -3870 44';
	}
	else if (card == 14)
	{
		u = (t - 67.8) / 5.0;
		cpos = Intro_LerpVec ('14575 -14090 34', '14625 -14090 29', u);
		look = Intro_LerpVec ('14755 -14090 48', '14755 -14090 54', u);
	}
	else
	{
		u = (t - 72.8) / 5.2;
		cpos = Intro_LerpVec ('11710 -2736 68', '11520 -2736 126', u);
		look = Intro_LerpVec ('12190 -2736 92', '12280 -2736 155', u);
	}

	intro_cam_pos = cpos;
	intro_cam_ang = Intro_LookAngles (cpos, look);
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

void(vector org) Intro_TelePop =
{
	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_TELEPORT);
	WriteCoord (MSG_BROADCAST, org_x);
	WriteCoord (MSG_BROADCAST, org_y);
	WriteCoord (MSG_BROADCAST, org_z);
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

	ia_van = world;
	ia_vansurf = world;
	ia_pinkcar = world;
	ia_forklift = world;
	ia_pod1 = world;
	ia_robdob = world;
	ia_pkbomb = world;
	ia_pickle = world;
	ia_wheelman = world;
	ia_dancer = world;
	ia_milky = world;
	ia_spot1 = world;
	ia_spot2 = world;
	ia_spot3 = world;
	ia_spot4 = world;
	ia_spot5 = world;
	ia_jp1 = world;
	ia_jp2 = world;
	ia_turrbase = world;
	ia_turrgun = world;
	ia_sight = world;
	ia_nspc = world;
	ia_nsarc = world;
	ia_ltg_head = world;
	ia_ltg_aura = world;

	if (intro_cam)
		sound (intro_cam, 6, "misc/null.wav", 1, ATTN_NONE);

	e = nextent (world);
	while (e)
	{
		nxt = nextent (e);
		if (e != intro_dir_ent && e != intro_cam && e.classname != "player" && e.solid != SOLID_BSP)
		{
			if (e.intro_tag || (e.model != "" && e.classname != "misc_model" && e.classname != "bk_tv" && e.classname != "bk_trashcan"))
			{
				Intro_FreeCarClips (e);
				remove (e);
			}
		}
		e = nxt;
	}
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

void(entity p) Intro_PurgePlayerAttachments =
{
	local entity e, nxt;

	if (!p)
		return;
	e = nextent (world);
	while (e)
	{
		nxt = nextent (e);
		if (e != p && e != intro_cam && e != intro_dir_ent && e.solid != SOLID_BSP)
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
	if (p.clientcamera != intro_cam)
	{
		p.clientcamera = intro_cam;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
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
	if (!p)
		return;

	Intro_EnsureCam (p);
	setorigin (intro_cam, intro_cam_pos);
	intro_cam.angles = intro_cam_ang;

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

	e = nextent (world);
	while (e)
	{
		nxt = nextent (e);
		if (e.classname != "player" && e != intro_dir_ent && e != intro_cam && e.solid != SOLID_BSP)
		{
			// Strip roaming cruisers/flyers, map-spawned drivable vehicles, and floating weapon/item/jetpack pickups,
			// while preserving all map misc_model props (CRTs, sodas, pallet racks, Mega Man bed shrine, Casino horse, KUZZ van) & live bk_tv!
			if (e.classname == "bk_cruiser" || e.classname == "bk_flyer" || e.veh_kind > 0 || e.classname == "veh_part")
			{
				Intro_FreeCarClips (e);
				remove (e);
			}
			else if (e.classname == "misc_vehicle_van" || e.classname == "misc_vehicle_sedan" || e.classname == "misc_vehicle_coupe" || e.classname == "misc_vehicle_truck")
			{
				Intro_FreeCarClips (e);
				remove (e);
			}
			else if (e.model == "progs/veh_van.md3" && e.origin_x > 11800 && e.origin_y > -3000 && e.origin_y < -2500)
				remove (e);
			else if ((e.flags & FL_ITEM) || e.model == "progs/jetpack.md3" || e.think == Jetpack_Place)
				remove (e);
		}
		e = nxt;
	}
};

// ---------------------------------------------------------------- Reusable Comedy Props & Actors

// Runner that emerges smoothly out of the White Van side door over 0.85s, then trots along a spacious oval path!
void() Intro_RunnerThink =
{
	local float a, nx, ny, f, blend;
	local vector target_p, np, dir;

	if (time > self.ltime)
	{
		remove (self);
		return;
	}
	a = time * self.intro_spd + self.intro_phase;
	nx = self.intro_cx + ICos (a * 0.0174533) * self.intro_rad;
	ny = self.intro_cy + ISin (a * 0.0174533 * 1.25) * (self.intro_rad * 0.68);
	target_p_x = nx;
	target_p_y = ny;
	target_p_z = 2;
	if (self.mb_type == 6)
		target_p_z = 9;
	else if (self.mb_type == 7)
		target_p_z = 28;
	else if (self.mb_type == 22)
		target_p_z = 2 + fabs (ISin (time * 9 + self.intro_phase)) * 22;

	blend = Intro_Smooth ((time - self.intro_born) / 0.85);
	np = self.intro_door + (target_p - self.intro_door) * blend;

	dir = np - self.origin;
	dir_z = 0;
	if (vlen (dir) > 0.05)
		self.angles_y = vectoyaw (dir) + self.mb_yaw0;
	setorigin (self, np);

	if (self.mb_fn > 0)
	{
		f = floor (time * self.mb_fps + self.intro_phase);
		self.frame = self.mb_f0 + f - self.mb_fn * floor (f / self.mb_fn);
	}
	self.nextthink = time + 0.001;
};

entity(float mtype, vector door_org, float cx, float cy, float rad, float spd, float ph, float dur, float sc_mul) Intro_SpawnVanRunner =
{
	local entity m;

	m = Intro_MakeActor (mtype, sc_mul, door_org);
	if (!m)
		return world;
	m.classname = "intro_runner";
	m.intro_door = door_org;
	m.intro_born = time;
	m.intro_cx = cx;
	m.intro_cy = cy;
	m.intro_rad = rad;
	m.intro_spd = spd;
	m.intro_phase = ph;
	m.ltime = time + dur;
	m.think = Intro_RunnerThink;
	m.nextthink = time + 0.001;
	return m;
};

void(float dur) Intro_SpawnVanPileOut =
{
	local vector door_l, door_r;
	door_l = '12145 -2705 2';
	door_r = '12145 -2768 2';

	// Spacious, readable rings around the White Van under the Bakersfield Sign!
	Intro_SpawnVanRunner (19, door_l, 11925, -2670, 95,  96,  0,   dur, 1.22);	// Paul ("Hello!")
	Intro_SpawnVanRunner (18, door_r, 11935, -2805, 95, -94,  45,  dur, 1.22);	// Dennis
	Intro_SpawnVanRunner (22, door_l, 11885, -2736, 85,  108, 90,  dur, 1.26);	// Rubber Finger (hopping!)
	Intro_SpawnVanRunner (21, door_r, 11985, -2620, 110, 98,  135, dur, 1.22);	// Mr. DIY
	Intro_SpawnVanRunner (11, door_l, 11995, -2845, 110,-106, 180, dur, 1.22);	// Kyle (Scissors!)
	Intro_SpawnVanRunner (17, door_r, 11910, -2855, 95,  92,  225, dur, 1.20);	// Tinfoil-Hat Bryan
	Intro_SpawnVanRunner (14, door_l, 11915, -2610, 95, -92,  270, dur, 1.20);	// Friend Rob
	Intro_SpawnVanRunner (20, door_r, 12035, -2785, 105, 95,  315, dur, 1.20);	// QuakeGuy
	Intro_SpawnVanRunner (23, door_l, 12040, -2685, 105,-102, 25,  dur, 1.24);	// David Ojeda
	Intro_SpawnVanRunner (24, door_r, 12075, -2850, 110, 96,  70,  dur, 1.18);	// Pregnant Runner 1
	Intro_SpawnVanRunner (25, door_l, 12085, -2625, 110,-96,  115, dur, 1.18);	// Pregnant Runner 2
	Intro_SpawnVanRunner (26, door_r, 12115, -2740, 115, 92,  160, dur, 1.18);	// Pregnant Runner 3
	Intro_SpawnVanRunner (10, door_l, 11970, -2736, 155,-122, 205, dur, 1.22);	// JessKart
	Intro_SpawnVanRunner (1,  door_r, 11895, -2795, 90,  104, 250, dur, 1.55);	// Mega Man
	Intro_SpawnVanRunner (2,  door_l, 12055, -2900, 115,-104, 295, dur, 1.18);	// Suit Rider
	Intro_SpawnVanRunner (4,  door_r, 12055, -2575, 115, 104, 340, dur, 1.18);	// Squat Rider
	Intro_SpawnVanRunner (7,  door_l, 11955, -2880, 90,  88,  55,  dur, 0.94);	// Giant 3D Big-Ears
	Intro_SpawnVanRunner (6,  door_r, 12215, -2845, 115,-92,  150, dur, 0.95);	// Golden Casino Horse
	Intro_SpawnVanRunner (9,  door_l, 11875, -2675, 95,  116, 100, dur, 1.22);	// Wheelman
};

void(vector start, vector vel, float life) Intro_TossWheel =
{
	local entity w;

	w = spawn ();
	w.classname = "intro_prop";
	w.intro_tag = 1;
	w.movetype = MOVETYPE_BOUNCE;
	w.solid = SOLID_BBOX;
	setmodel (w, "progs/mm_wheel.md3");
	w.scale = 1.55;
	setsize (w, '0 0 0', '0 0 0');
	setorigin (w, start);
	w.velocity = vel;
	w.avelocity = '360 220 420';
	w.bouncefactor = 0.82;
	w.think = SUB_Remove;
	w.nextthink = time + life;
};

void(vector start, vector vel, float life) Intro_TossMiniDob =
{
	local entity m;

	m = spawn ();
	m.classname = "fh_mini";
	m.intro_tag = 1;
	m.movetype = MOVETYPE_BOUNCE;
	m.solid = SOLID_BBOX;
	setmodel (m, "progs/floathead.mdl");
	m.scale = 0.72;
	m.effects = EF_FULLBRIGHT;
	setsize (m, '0 0 0', '0 0 0');
	setorigin (m, start);
	m.velocity = vel;
	m.avelocity = '0 320 0';
	m.bouncefactor = 0.88;
	m.think = SUB_Remove;
	m.nextthink = time + life;
};

void(vector org) Intro_BonkSparks =
{
	local float i;
	local entity s;

	sound (intro_cam, CHAN_AUTO, "hammer/frying_pan.wav", 0.98, ATTN_NONE);
	i = 0;
	while (i < 14)
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
		s.scale = 1.70;
		s.effects = EF_FULLBRIGHT;
		setsize (s, '0 0 0', '0 0 0');
		setorigin (s, org + '0 0 36');
		s.velocity_x = crandom () * 210;
		s.velocity_y = crandom () * 210;
		s.velocity_z = 210 + random () * 210;
		s.avelocity = '400 500 300';
		s.think = SUB_Remove;
		s.nextthink = time + 1.8;
		i = i + 1;
	}
};

void(vector start, vector vel, string mdl, float sc, float life) Intro_FlyBolt =
{
	local entity b;

	b = spawn ();
	b.classname = "intro_prop";
	b.intro_tag = 1;
	b.movetype = MOVETYPE_FLY;
	b.solid = SOLID_NOT;
	setmodel (b, mdl);
	b.scale = sc;
	setsize (b, '0 0 0', '0 0 0');
	setorigin (b, start);
	b.velocity = vel;
	b.angles = vectoangles (vel);
	b.avelocity = '0 0 540';
	b.effects = EF_FULLBRIGHT;
	b.think = SUB_Remove;
	b.nextthink = time + life;
};

void() Intro_GooBlobSwell =
{
	self.cnt = self.cnt + 1;
	if (self.cnt <= 4)
	{
		self.frame = self.cnt + 1;		// frames 1 -> 2 -> 3 -> 4 -> 5 swelling foam blob!
		self.scale = self.scale + 0.09;
		self.nextthink = time + 0.14;
		return;
	}
	self.frame = 0;
	self.think = SUB_Remove;
	self.nextthink = time + 2.8;
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
	g.scale = 0.26;
	g.angles = '0 1 0' * (random () * 360);
	setsize (g, '0 0 0', '0 0 0');
	setorigin (g, target_org);
	g.cnt = 0;
	g.think = Intro_GooBlobSwell;
	g.nextthink = time + 0.12;
	sound (g, CHAN_AUTO, "weapons/goosplat.wav", 0.85, ATTN_NORM);
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
	local entity s, w;

	s = spawn ();
	s.classname = "grenade";
	s.intro_tag = 1;
	s.movetype = MOVETYPE_NONE;
	s.solid = SOLID_NOT;
	setmodel (s, "progs/jw_splash.spr32");
	s.scale = 1.25;
	setsize (s, '0 0 0', '0 0 0');
	setorigin (s, org);
	// JG_Splash converts self into the animated splash + floor ripples
	{
		local entity oldself;
		oldself = self;
		self = s;
		JG_Splash ();
		self = oldself;
	}

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
	self.scale = self.scale + 0.09;
	self.nextthink = time + 0.04;
};

void(vector org) Intro_SpawnMMDome =
{
	local entity d;

	d = spawn ();
	d.classname = "intro_prop";
	d.intro_tag = 1;
	d.movetype = MOVETYPE_NONE;
	d.solid = SOLID_NOT;
	setmodel (d, "progs/mm_explode.md3");
	d.scale = 1.35;
	d.effects = EF_FULLBRIGHT;
	setsize (d, '0 0 0', '0 0 0');
	setorigin (d, org);
	d.ltime = time + 0.85;
	d.think = Intro_MMDomeThink;
	d.nextthink = time + 0.03;
	Intro_TossWheel (org + '0 10 14', '95 140 240', 2.0);
	Intro_TossWheel (org + '0 -10 14', '95 -140 250', 2.0);
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

void(vector org) Intro_LaunchTrashcan =
{
	local entity c;

	c = spawn ();
	c.classname = "intro_prop";
	c.intro_tag = 1;
	c.movetype = MOVETYPE_FLY;
	c.solid = SOLID_NOT;
	setmodel (c, "progs/bklan/trashcan.md3");
	c.scale = 1.28;
	setsize (c, '0 0 0', '0 0 0');
	setorigin (c, org);
	c.velocity = '15 0 420';
	c.avelocity = '90 360 70';
	c.ltime = time + 3.5;
	c.think = Intro_RocketCanThink;
	c.nextthink = time + 0.02;

	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, org_x);
	WriteCoord (MSG_BROADCAST, org_y);
	WriteCoord (MSG_BROADCAST, org_z + 16);
	sound (c, CHAN_WEAPON, "weapons/rocket1i.wav", 0.92, ATTN_NONE);
};

void(entity a, vector start_pos, vector mark_pos, float u, float keep_running) Intro_Spin360 =
{
	local vector pos;
	local float front, s, f;

	if (!a)
		return;
	if (u < 0.22)
		pos = Intro_LerpVec (start_pos, mark_pos, u / 0.22);
	else
		pos = mark_pos;

	front = vectoyaw (intro_cam_pos - pos);
	if (u < 0.78)
	{
		s = Intro_Smooth (u / 0.78);
		a.mb_run = TRUE;
		a.angles_y = (front + a.mb_yaw0) + s * 360;
	}
	else
	{
		a.mb_run = keep_running;
		a.angles_y = (front + a.mb_yaw0) + ISin ((u - 0.78) * 14.0) * 18;
	}
	if (a.mb_fn > 0)
	{
		f = floor (time * a.mb_fps);
		a.frame = a.mb_f0 + f - a.mb_fn * floor (f / a.mb_fn);
	}
	setorigin (a, pos);
};

// ---------------------------------------------------------------- Main 100Hz bklan5 Comedy Tour Sequencer

void() Intro_Tick =
{
	local entity p, oldself;
	local float t, u, f, front;
	local vector pos, pos2;

	self.nextthink = time + 0.001;

	p = Intro_GetPlayer ();
	if (!p)
		return;

	if (!intro_t0)
	{
		intro_t0 = time;
		intro_t0_ms = rint (intro_t0 * 1000);
		Intro_CleanStage ();
		cvar_set ("sv_gravity", "800");
	}

	t = time - intro_t0;
	if (t < 2.0)
		Intro_PurgePlayerAttachments (p);

	// ================================================================
	// CARD 1 (0.0s .. 4.4s): BAKERSFIELD SIGN — JUST THE WHITE LAN VAN!
	// ================================================================
	if (t < 4.4)
	{
		intro_cur_card = 1;
		if (intro_ev < 1)
		{
			intro_ev = 1;
			sound (intro_cam, 6, "vehicles/idle_van.wav", 0.85, ATTN_NONE);

			ia_van = spawn ();
			ia_van.intro_tag = 1;
			ia_van.movetype = MOVETYPE_NONE;
			ia_van.solid = SOLID_NOT;
			setmodel (ia_van, "progs/veh_van.md3");
			setsize (ia_van, '0 0 0', '0 0 0');
			ia_van.angles = '0 162 0';
			setorigin (ia_van, '12170 -2736 2');
		}
		if (t >= 1.70 && intro_ev < 2)
		{
			intro_ev = 2;
			Intro_Cue ("vehicles/horn.wav", 0.95);
		}
		if (t >= 3.35 && intro_ev < 3)
		{
			intro_ev = 3;
			Intro_Cue ("vehicles/horn.wav", 0.90);
		}
		if (ia_van)
		{
			// Funny subtle suspension rocking — like 19 people are crammed inside arguing!
			pos = '12170 -2736 2';
			pos_z = 2 + fabs (ISin (t * 8.5)) * 1.4;
			if ((t >= 1.70 && t < 2.05) || (t >= 3.35 && t < 3.65))
				pos_z = pos_z + 3.0;
			ia_van.angles_z = ISin (t * 8.5) * 2.2;
			setorigin (ia_van, pos);
		}
	}

	// ================================================================
	// CARD 2 (4.4s .. 11.4s): BAKERSFIELD SIGN — ALL 19 CHARACTERS PILE OUT & MAKE THEIR SOUNDS!
	// ================================================================
	else if (t < 11.4)
	{
		intro_cur_card = 2;
		if (intro_ev < 4)
		{
			intro_ev = 4;
			Intro_TelePop ('12135 -2720 28');
			Intro_TelePop ('12135 -2752 28');
			Intro_Cue ("larry/love_to_play_quake.wav", 1.0);
			Intro_SpawnVanPileOut (7.3);

			// Stunt-dancer Wheelman pops onto the roof of the White Van!
			ia_vansurf = spawn ();
			ia_vansurf.intro_tag = 1;
			ia_vansurf.movetype = MOVETYPE_NONE;
			ia_vansurf.solid = SOLID_NOT;
			setmodel (ia_vansurf, "progs/wheelman_dance.spr32");
			ia_vansurf.scale = 0.42;
			ia_vansurf.wc_anim = 2;
			ia_vansurf.wc_t0 = time;
			ia_vansurf.customizeentityforclient = WC_DancerCustomize;
			setsize (ia_vansurf, '0 0 0', '0 0 0');
			setorigin (ia_vansurf, '12170 -2736 92');
		}
		// Cleanly staggered voice callouts (~0.74s apart) so EVERY character's funny sound is clearly heard!
		if (t >= 5.25 && intro_ev < 5)  { intro_ev = 5;  Intro_Cue ("friends/hello.wav", 1.0); }
		if (t >= 6.00 && intro_ev < 6)  { intro_ev = 6;  Intro_Cue ("friends/gowewd.wav", 1.0); if (ia_vansurf) ia_vansurf.wc_anim = 4; }
		if (t >= 6.72 && intro_ev < 7)  { intro_ev = 7;  Intro_Cue ("mbox/drv_boing_hop.wav", 0.95); }
		if (t >= 7.45 && intro_ev < 8)  { intro_ev = 8;  Intro_Cue ("mrdiy/mrdiy_jingle.wav", 0.92); }
		if (t >= 8.20 && intro_ev < 9)  { intro_ev = 9;  Intro_Cue ("larry/play_with_knives.wav", 1.0); if (ia_vansurf) ia_vansurf.wc_anim = 7; }
		if (t >= 8.95 && intro_ev < 10) { intro_ev = 10; Intro_Cue ("bryan/noway.wav", 1.0); }
		if (t >= 9.68 && intro_ev < 11) { intro_ev = 11; Intro_Cue ("john/jv15.wav", 0.95); }
		if (t >= 10.42 && intro_ev < 12){ intro_ev = 12; Intro_Cue ("david/shower_love.wav", 1.0); }

		if (ia_vansurf)
			ia_vansurf.angles_y = 180 + ((t - 4.4) / 7.0) * 720;
	}

	// ================================================================
	// CARD 3 (11.4s .. 16.4s): FOX THEATER MARQUEE (20TH & H ST)
	//        Rob Dob Gun + "It's Not Pink!" Supercar + Podracer + Mini-Dobs!
	// ================================================================
	else if (t < 16.4)
	{
		intro_cur_card = 3;
		if (intro_ev < 13)
		{
			intro_ev = 13;
			Intro_ClearSpot ();
			Intro_EvalCam (3, t);
			Intro_Cue ("bklan/notpink.wav", 1.0);
			sound (intro_cam, 6, "bklan/pinkcar.wav", 0.72, ATTN_NONE);

			// "It's Not Pink!" Supercar parked right in front of the Fox Marquee!
			ia_pinkcar = spawn ();
			ia_pinkcar.intro_tag = 1;
			ia_pinkcar.movetype = MOVETYPE_NONE;
			ia_pinkcar.solid = SOLID_NOT;
			setmodel (ia_pinkcar, "progs/pink_supercar.md3");
			ia_pinkcar.scale = 0.95;
			setsize (ia_pinkcar, '0 0 0', '0 0 0');
			ia_pinkcar.angles = '0 305 0';
			setorigin (ia_pinkcar, '940 -11155 2');

			// Podracer banking past the Fox Clock Tower!
			ia_pod1 = spawn ();
			ia_pod1.intro_tag = 1;
			ia_pod1.movetype = MOVETYPE_FLY;
			ia_pod1.solid = SOLID_NOT;
			setmodel (ia_pod1, "progs/skyveh_v3.md3");
			ia_pod1.scale = 0.92;
			setsize (ia_pod1, '0 0 0', '0 0 0');
			setorigin (ia_pod1, '1180 -10890 218');
			ia_pod1.velocity = '-115 -85 6';
			ia_pod1.angles = '0 216 -14';
		}

		u = (t - 11.4) / 5.0;
		if (ia_pinkcar)
		{
			f = floor (u * 24);
			if (f > 15)
				f = 15;
			ia_pinkcar.frame = 32 + f;		// Lambo scissor doors open!
			ia_pinkcar.angles_y = 305 + Intro_Smooth (u) * 180;
		}

		// 12.60s: Foreground v_robdob.mdl launches Rob Dob's Floating Head!
		if (t >= 12.60 && intro_ev < 14)
		{
			intro_ev = 14;
			Intro_Cue ("hackmon/hm_launch.wav", 1.0);
			Intro_Cue ("floathead/sight1.wav", 1.0);

			ia_robdob = spawn ();
			ia_robdob.classname = "intro_robdob";
			ia_robdob.intro_tag = 1;
			ia_robdob.movetype = MOVETYPE_NONE;
			ia_robdob.solid = SOLID_NOT;
			setmodel (ia_robdob, "progs/floathead.mdl");
			ia_robdob.scale = 2.05;
			ia_robdob.effects = EF_FULLBRIGHT;
			ia_robdob.traileffectnum = particleeffectnum ("fd_trail");
			setsize (ia_robdob, '0 0 0', '0 0 0');
			setorigin (ia_robdob, '1140 -11360 66');
		}

		if (ia_robdob)
		{
			if (t < 15.15)
			{
				f = (t - 12.60) / 0.85;
				pos = Intro_LerpVec ('1140 -11360 66', '990 -11215 80', f);
				pos_z = pos_z + ISin ((t - 12.60) * 5.0) * 4;
				setorigin (ia_robdob, pos);
				front = vectoyaw (intro_cam_pos - pos);
				if (t < 14.15)
				{
					ia_robdob.angles_y = front + Intro_Smooth ((t - 12.60) / 1.55) * 360;
					ia_robdob.skin = 0;
					f = floor (time * 10);
					ia_robdob.frame = f - 8 * floor (f / 8);
				}
				else
				{
					if (intro_ev < 15)
					{
						intro_ev = 15;
						Intro_Cue ("floathead/charge.wav", 1.0);
					}
					ia_robdob.angles_y = front;
					ia_robdob.skin = 1;
					f = floor (time * 14);
					ia_robdob.frame = 12 + (f - 4 * floor (f / 4));
				}
			}
			else if (intro_ev < 16)
			{
				intro_ev = 16;
				Intro_Cue ("weapons/lhit.wav", 0.95);
				Intro_Cue ("funny/heh.wav", 1.0);
				Intro_Cue ("floathead/boing.wav", 0.95);
				FD_Shock (ia_robdob, TRUE);
				Intro_TossMiniDob (ia_robdob.origin, '85 -95 230', 1.6);
				Intro_TossMiniDob (ia_robdob.origin, '-95 85 240', 1.6);
				Intro_TossMiniDob (ia_robdob.origin, '110 65 215', 1.6);
				Intro_TossMiniDob (ia_robdob.origin, '-75 -105 225', 1.6);
				remove (ia_robdob);
				ia_robdob = world;
			}
		}
	}

	// ================================================================
	// CARD 4 (16.4s .. 21.4s): FOX THEATER EVA'S LOUNGE & LIVE SECURITY TV
	//        Pickle Surprise Gun ambushes Dennis & Paul watching Fox's TV!
	// ================================================================
	else if (t < 21.4)
	{
		intro_cur_card = 4;
		if (intro_ev < 17)
		{
			intro_ev = 17;
			Intro_ClearSpot ();
			Intro_EvalCam (4, t);
			Intro_Cue ("friends/interesting.wav", 1.0);

			ia_spot1 = Intro_MakeActor (18, 1.15, '582 -10078 25');	// Dennis on Eva's Lounge stage
			ia_spot2 = Intro_MakeActor (19, 1.15, '638 -10078 25');	// Paul watching the live wall TV
			{
				local entity tv;
				tv = find (world, classname, "bk_tv");
				while (tv)
				{
					if (vlen (tv.origin - '610 -10027 91') < 180)
					{
						oldself = self;
						self = tv;
						self.tv_vid = 0;
						self.tv_chunk = 0;
						BKTV_Think ();
						self = oldself;
					}
					tv = find (tv, classname, "bk_tv");
				}
			}
		}
		if (t >= 17.55 && intro_ev < 18)
		{
			intro_ev = 18;
			Intro_Cue ("pickle/throw.wav", 0.95);
			ia_pkbomb = spawn ();
			ia_pkbomb.intro_tag = 1;
			ia_pkbomb.movetype = MOVETYPE_NONE;
			ia_pkbomb.solid = SOLID_NOT;
			setmodel (ia_pkbomb, "progs/pickle_bomb.md3");
			ia_pkbomb.scale = 1.85;
			setsize (ia_pkbomb, '0 0 0', '0 0 0');
			ia_pkbomb.avelocity = '0 220 0';
			setorigin (ia_pkbomb, '611 -10095 26');
		}
		if (t >= 17.85 && intro_ev < 19)
		{
			intro_ev = 19;
			if (ia_pkbomb) { remove (ia_pkbomb); ia_pkbomb = world; }
			Intro_Cue ("pickle/surprise.wav", 1.0);
			Intro_Cue ("friends/no.wav", 1.0);

			ia_pickle = spawn ();
			ia_pickle.classname = "pickle";
			ia_pickle.intro_tag = 1;
			ia_pickle.movetype = MOVETYPE_NONE;
			ia_pickle.solid = SOLID_NOT;
			ia_pickle.pk_state = 4;
			ia_pickle.pk_t0 = time;
			ia_pickle.pk_t = time + 2.85;
			ia_pickle.pk_front = 270;
			ia_pickle.scale = 1.65;
			setmodel (ia_pickle, "progs/pickle.md3");
			setsize (ia_pickle, '0 0 0', '0 0 0');
			ia_pickle.customizeentityforclient = Pk_Customize;
			setorigin (ia_pickle, '611 -10096 26');
		}

		if (t < 20.70)
		{
			u = (t - 16.4) / 4.3;
			Intro_Spin360 (ia_spot1, '582 -10078 25', '580 -10084 25', u, TRUE);
			Intro_Spin360 (ia_spot2, '638 -10078 25', '640 -10084 25', u, TRUE);
			if (ia_pickle)
			{
				f = (t - 17.85) / 2.85;
				ia_pickle.pk_front = 270 + Intro_Smooth (f) * 360;
				if (f < 0.68)
				{
					ia_pickle.scale = 1.65 + f * 1.45;
					ia_pickle.frame = floor ((time * 18) - 24 * floor ((time * 18) / 24));
				}
				else
				{
					ia_pickle.scale = 2.64 + ((f - 0.68) / 0.32) * 1.65;
					ia_pickle.frame = 24 + floor (((f - 0.68) / 0.32) * 11);
				}
			}
		}
		else if (intro_ev < 20)
		{
			intro_ev = 20;
			Intro_Cue ("afrit/body_explode.wav", 0.95);
			if (ia_pickle)
			{
				oldself = self;
				self = ia_pickle;
				sendParticle ("pk_boom", '611 -10094 48', '0 0 0', 1, 0);
				f = 0;
				while (f < 12)
				{
					Pk_Gib ('611 -10094 52');
					f = f + 1;
				}
				self = oldself;
				remove (ia_pickle);
				ia_pickle = world;
			}
			// Pop Dennis & Paul comically upward!
			if (ia_spot1) { ia_spot1.movetype = MOVETYPE_TOSS; ia_spot1.velocity = '-45 -30 220'; }
			if (ia_spot2) { ia_spot2.movetype = MOVETYPE_TOSS; ia_spot2.velocity = '45 -30 230'; }
		}
	}

	// ================================================================
	// CARD 5 (21.4s .. 27.0s): FOX THEATER AUDITORIUM & SUNBURST STAGE
	//        Wheelman Cannon (+58 deg) -> Stunt Dancer + Milky Opera & Screen Milk!
	// ================================================================
	else if (t < 27.0)
	{
		intro_cur_card = 5;
		if (intro_ev < 21)
		{
			intro_ev = 21;
			Intro_ClearSpot ();
			Intro_EvalCam (5, t);
			Intro_Cue ("wcannon/wc_charge.wav", 0.95);
		}
		if (t >= 22.55 && intro_ev < 22)
		{
			intro_ev = 22;
			Intro_Cue ("wcannon/wc_shoot.wav", 1.0);
			Intro_Cue ("wcannon/wc_scream.wav", 1.0);

			ia_wheelman = spawn ();
			ia_wheelman.intro_tag = 1;
			ia_wheelman.movetype = MOVETYPE_NONE;
			ia_wheelman.solid = SOLID_NOT;
			setmodel (ia_wheelman, "progs/wheelman.spr32");
			ia_wheelman.scale = 0.44;
			ia_wheelman.wc_anim = 2;
			ia_wheelman.angles = '0 90 0';
			ia_wheelman.customizeentityforclient = WC_ShotCustomize;
			setsize (ia_wheelman, '0 0 0', '0 0 0');
			setorigin (ia_wheelman, '48 -9310 68');
		}
		if (ia_wheelman && t < 23.15)
		{
			f = (t - 22.55) / 0.60;
			pos = Intro_LerpVec ('48 -9310 68', '24 -9045 48', f);
			pos_z = pos_z + ISin (f * 3.14159) * 34;
			setorigin (ia_wheelman, pos);
			pointparticles (wc_fx_spark, pos + '0 0 12', '0 0 60', 1);
		}
		if (t >= 23.15 && intro_ev < 23)
		{
			intro_ev = 23;
			if (ia_wheelman) { remove (ia_wheelman); ia_wheelman = world; }
			Intro_Cue ("wcannon/wc_boom.wav", 0.90);
			Intro_Cue ("friends/gowewd.wav", 1.0);
			Intro_TossWheel ('24 -9045 64', '-95 -60 220', 2.2);
			Intro_TossWheel ('24 -9045 64', '95 -60 230', 2.2);

			// Stunt dancer Wheelman takes Fox Center Stage!
			ia_dancer = spawn ();
			ia_dancer.intro_tag = 1;
			ia_dancer.movetype = MOVETYPE_NONE;
			ia_dancer.solid = SOLID_NOT;
			setmodel (ia_dancer, "progs/wheelman_dance.spr32");
			ia_dancer.scale = 0.46;
			ia_dancer.wc_anim = 2;
			ia_dancer.wc_t0 = time;
			ia_dancer.customizeentityforclient = WC_DancerCustomize;
			setsize (ia_dancer, '0 0 0', '0 0 0');
			setorigin (ia_dancer, '16 -9045 48');
		}
		if (ia_dancer)
		{
			if (t >= 24.4 && t < 25.4)
				ia_dancer.wc_anim = 4;		// Spin-bar stunt!
			else if (t >= 25.4)
				ia_dancer.wc_anim = 7;		// Robot stunt!
			ia_dancer.angles_y = 270 + ((t - 23.15) / 3.85) * 720;
		}
		// Beat 5B: Milky joins Wheelman on stage, sings opera, & splashes the camera!
		if (t >= 24.85 && intro_ev < 24)
		{
			intro_ev = 24;
			Intro_Cue ("milky/fire.wav", 0.95);
			sound (intro_cam, 6, "milky/song.ogg", 0.95, ATTN_NONE);

			ia_milky = spawn ();
			ia_milky.classname = "milky_lady";
			ia_milky.intro_tag = 1;
			ia_milky.movetype = MOVETYPE_NONE;
			ia_milky.solid = SOLID_NOT;
			ia_milky.milky_born = time - 2;
			ia_milky.milky_dir = '0 -1 0';
			ia_milky.scale = 2.45;
			ia_milky.colormod = '1 1 1';
			ia_milky.effects = EF_FULLBRIGHT;
			setmodel (ia_milky, "progs/pinklady.md3");
			setsize (ia_milky, '-16 -16 -24', '16 16 24');
			ia_milky.customizeentityforclient = Milky_Customize;
			setorigin (ia_milky, '76 -9045 80');
		}
		if (ia_milky && t < 26.05)
		{
			f = (t - 24.85) / 1.20;
			pos = Intro_LerpVec ('76 -9045 80', '48 -9195 76', f);
			pos_x = pos_x + ISin (f * 6.28318) * 14;
			setorigin (ia_milky, pos);
			u = (270 + Intro_Smooth (f) * 360) * 0.0174533;
			ia_milky.milky_dir_x = ICos (u);
			ia_milky.milky_dir_y = ISin (u);
			ia_milky.milky_dir_z = 0;
		}
		if (t >= 26.05 && intro_ev < 25)
		{
			intro_ev = 25;
			sound (intro_cam, 6, "misc/null.wav", 1, ATTN_NONE);
			Intro_Cue ("weapons/goosplat.wav", 1.0);
			if (ia_milky)
			{
				Milk_Splatter (ia_milky.origin);
				Milk_Rain ('48 -9210 82');
				remove (ia_milky);
				ia_milky = world;
			}
			p.milk_scr = time - 1.55;
		}
	}

	// ================================================================
	// CARD 6 (27.0s .. 32.0s): PADRE HOTEL (H & WALL ST) 8-STORY SKY FLOAT
	//        Duke Nukem Jetpacks ("I'm floating!!") ascending to the red neon sign!
	// ================================================================
	else if (t < 32.0)
	{
		intro_cur_card = 6;
		if (intro_ev < 26)
		{
			intro_ev = 26;
			Intro_ClearSpot ();
			Intro_EvalCam (6, t);
			Intro_Cue ("jetpack/floating.wav", 1.0);
			sound (intro_cam, 6, "jetpack/swoosh.wav", 0.85, ATTN_NONE);

			// Flyer 1: QuakeGuy with strapped-on Jetpack!
			ia_spot1 = Intro_MakeActor (20, 1.30, '660 -17430 535');
			ia_jp1 = spawn ();
			ia_jp1.intro_tag = 1;
			ia_jp1.movetype = MOVETYPE_NONE;
			ia_jp1.solid = SOLID_NOT;
			setmodel (ia_jp1, "progs/jetpack.md3");
			ia_jp1.scale = 1.95;
			setsize (ia_jp1, '0 0 0', '0 0 0');
			setorigin (ia_jp1, '660 -17430 562');

			// Flyer 2: 3D Quake Ranger (player_shot.mdl) with strapped-on Jetpack!
			ia_spot2 = spawn ();
			ia_spot2.intro_tag = 1;
			ia_spot2.movetype = MOVETYPE_NONE;
			ia_spot2.solid = SOLID_NOT;
			setmodel (ia_spot2, "progs/player_shot.mdl");
			ia_spot2.scale = 1.35;
			setsize (ia_spot2, '0 0 0', '0 0 0');
			setorigin (ia_spot2, '555 -17385 505');

			ia_jp2 = spawn ();
			ia_jp2.intro_tag = 1;
			ia_jp2.movetype = MOVETYPE_NONE;
			ia_jp2.solid = SOLID_NOT;
			setmodel (ia_jp2, "progs/jetpack.md3");
			ia_jp2.scale = 1.95;
			setsize (ia_jp2, '0 0 0', '0 0 0');
			setorigin (ia_jp2, '555 -17385 512');
		}
		if (t >= 29.60 && intro_ev < 27)
		{
			intro_ev = 27;
			Intro_Cue ("larry/double_good.wav", 1.0);
		}

		u = (t - 27.0) / 5.0;
		f = floor (time * 16);
		f = f - 8 * floor (f / 8);		// Jetpack thrust frames 0..7!

		if (ia_spot1 && ia_jp1)
		{
			pos = Intro_LerpVec ('660 -17430 535', '585 -17455 1192', u);
			pos_x = pos_x + ISin (u * 6.28318) * 18;
			front = vectoyaw (intro_cam_pos - pos) + u * 720;
			ia_spot1.angles_y = front + ia_spot1.mb_yaw0;
			setorigin (ia_spot1, pos);
			makevectors ('0 1 0' * front);
			setorigin (ia_jp1, pos - v_forward * 10 + '0 0 28');
			ia_jp1.angles_y = front;
			ia_jp1.frame = f;
			pointparticles (particleeffectnum ("jp_fire"), ia_jp1.origin - '0 0 12', '0 0 -120', 1);
		}
		if (ia_spot2 && ia_jp2)
		{
			pos2 = Intro_LerpVec ('555 -17385 505', '445 -17450 1180', u);
			pos2_y = pos2_y + ICos (u * 6.28318) * 16;
			front = vectoyaw (intro_cam_pos - pos2) - u * 720;
			ia_spot2.angles_y = front;
			ia_spot2.frame = 6 + (f - 6 * floor (f / 6));
			setorigin (ia_spot2, pos2);
			makevectors ('0 1 0' * front);
			setorigin (ia_jp2, pos2 - v_forward * 10 + '0 0 6');
			ia_jp2.angles_y = front;
			ia_jp2.frame = f;
			pointparticles (particleeffectnum ("jp_fire"), ia_jp2.origin - '0 0 12', '0 0 -120', 1);
		}
	}

	// ================================================================
	// CARD 7 (32.0s .. 37.0s): PADRE HOTEL 96-FT SKYLINE ROOFTOP
	//        TF Spanner -> Level-2 Sentry Gun + Sniper Laser + CCC 'C' Bolts vs. Kyle!
	// ================================================================
	else if (t < 37.0)
	{
		intro_cur_card = 7;
		if (intro_ev < 28)
		{
			intro_ev = 28;
			Intro_ClearSpot ();
			Intro_EvalCam (7, t);
			Intro_Cue ("weapons/turrset.wav", 0.95);
			Intro_Cue ("larry/play_with_knives.wav", 1.0);

			// TF Level-2 Sentry Gun tripod + twin chaingun head on the Padre Hotel roof!
			ia_turrbase = spawn ();
			ia_turrbase.intro_tag = 1;
			ia_turrbase.movetype = MOVETYPE_NONE;
			ia_turrbase.solid = SOLID_NOT;
			setmodel (ia_turrbase, "progs/turrbase.mdl");
			ia_turrbase.scale = 1.25;
			setsize (ia_turrbase, '0 0 0', '0 0 0');
			setorigin (ia_turrbase, '-70 -17915 1162');

			ia_turrgun = spawn ();
			ia_turrgun.intro_tag = 1;
			ia_turrgun.movetype = MOVETYPE_NONE;
			ia_turrgun.solid = SOLID_NOT;
			setmodel (ia_turrgun, "progs/turrgun.mdl");
			ia_turrgun.scale = 1.25;
			ia_turrgun.skin = 1;			// TF Level-2 Sentry skin!
			ia_turrgun.frame = 3;			// TF Level-2 Twin Chainguns!
			setsize (ia_turrgun, '0 0 0', '0 0 0');
			setorigin (ia_turrgun, '-70 -17915 1162');

			// Rotating TF Sniper Rifle world model display beside the Sentry!
			ia_spot2 = spawn ();
			ia_spot2.intro_tag = 1;
			ia_spot2.movetype = MOVETYPE_FLY;
			ia_spot2.solid = SOLID_NOT;
			setmodel (ia_spot2, "progs/g_srifle.mdl");
			ia_spot2.scale = 1.35;
			ia_spot2.avelocity = '0 160 0';
			setsize (ia_spot2, '0 0 0', '0 0 0');
			setorigin (ia_spot2, '8 -17885 1188');

			// Kyle (Running With Scissors) sprinting right in front of the glowing red neon PADRE HOTEL sign!
			ia_spot1 = Intro_MakeActor (11, 1.25, '-20 -17685 1164');

			// Red Sniper Laser Dot!
			ia_sight = spawn ();
			ia_sight.intro_tag = 1;
			ia_sight.movetype = MOVETYPE_NONE;
			ia_sight.solid = SOLID_NOT;
			setmodel (ia_sight, "progs/sight.spr");
			ia_sight.scale = 1.65;
			ia_sight.effects = EF_FULLBRIGHT;
			setsize (ia_sight, '0 0 0', '0 0 0');
			setorigin (ia_sight, '-20 -17695 1196');
		}
		if (t >= 33.15 && intro_ev < 29)
		{
			intro_ev = 29;
			Intro_Cue ("weapons/turrspot.wav", 0.95);
			Intro_Cue ("ccc/shoot.wav", 0.95);
			Intro_FlyBolt ('-70 -17915 1195', '55 190 4', "progs/ccc.md3", 1.65, 1.3);
			Intro_FlyBolt ('-70 -17915 1195', '85 185 8', "progs/ccc.md3", 1.65, 1.3);
		}
		if (t >= 35.40 && intro_ev < 30)
		{
			intro_ev = 30;
			Intro_Cue ("weapons/sniper.wav", 0.95);
			Intro_FlyBolt ('-70 -17915 1195', '95 190 6', "progs/ccc.md3", 1.65, 1.2);
		}

		u = (t - 32.0) / 5.0;
		if (ia_spot1)
		{
			pos_x = 65 + ISin (u * 9.42477) * 85;
			pos_y = -17685;
			pos_z = 1164 + fabs (ISin (u * 18.0)) * 12;
			ia_spot1.mb_run = TRUE;
			f = floor (time * ia_spot1.mb_fps);
			ia_spot1.frame = ia_spot1.mb_f0 + f - ia_spot1.mb_fn * floor (f / ia_spot1.mb_fn);
			ia_spot1.angles_y = vectoyaw (intro_cam_pos - pos) + ia_spot1.mb_yaw0;
			setorigin (ia_spot1, pos);

			if (ia_turrgun)
			{
				ia_turrgun.angles_y = vectoyaw (pos - ia_turrgun.origin);
				if (t >= 33.15)
					ia_turrgun.frame = 3 + (floor (time * 16) - 2 * floor ((time * 16) / 2));
			}
			if (ia_sight)
				setorigin (ia_sight, pos + '0 -10 34');
		}
	}

	// ================================================================
	// CARD 8 (37.0s .. 42.0s): LARRY'S WAREHOUSE (118/120 PALLET & LIVE TV HALL)
	//        Bonk Hammer Spinny + HIGH Charge FRYING-PAN SLAM vs. Mr. DIY & Forklift!
	// ================================================================
	else if (t < 42.0)
	{
		intro_cur_card = 8;
		if (intro_ev < 31)
		{
			intro_ev = 31;
			Intro_ClearSpot ();
			Intro_EvalCam (8, t);
			sound (intro_cam, 6, "mrdiy/mrdiy_jingle.wav", 0.92, ATTN_NONE);
			Intro_Cue ("hammer/slice1.wav", 0.90);

			ia_spot1 = Intro_MakeActor (21, 1.24, '-744 -596 2');	// Mr. DIY center-stage under Larry's live TV
			ia_forklift = Intro_MakeActor (8, 1.00, '-790 -578 2');	// Orange Warehouse Forklift
		}
		if (t >= 38.55 && intro_ev < 32)
		{
			intro_ev = 32;
			Intro_Cue ("hammer/charge_full.wav", 0.90);
		}
		if (t < 39.42)
		{
			u = (t - 37.0) / 2.42;
			Intro_Spin360 (ia_spot1, '-744 -585 2', '-744 -598 2', u, TRUE);
			if (ia_forklift)
				ia_forklift.angles_y = 315 + ISin ((t - 37.0) * 3.0) * 18;
		}
		else if (intro_ev < 33)
		{
			intro_ev = 33;
			sound (intro_cam, 6, "misc/null.wav", 1, ATTN_NONE);
			Intro_BonkSparks ('-744 -598 4');
			Intro_Cue ("funny/wewe.wav", 1.0);
			if (ia_spot1)
			{
				ia_spot1.movetype = MOVETYPE_TOSS;
				ia_spot1.velocity = '32 95 290';
				ia_spot1.avelocity = '0 540 0';
			}
		}
	}

	// ================================================================
	// CARD 9 (42.0s .. 47.4s): LARRY'S B-LAN 130A CRT PARTY HALL
	//        NetSend 3.5" Floppy PC (LOL.BAT) + 3D Laptop Gun zapping Friend Rob!
	// ================================================================
	else if (t < 47.4)
	{
		intro_cur_card = 9;
		if (intro_ev < 34)
		{
			intro_ev = 34;
			Intro_ClearSpot ();
			Intro_EvalCam (9, t);
			Intro_Cue ("netsend/wheres_disk.wav", 1.0);

			ia_spot1 = Intro_MakeActor (14, 1.18, '548 -748 2');	// Friend Rob among the LAN CRTs
		}
		// 43.15s: Floppy disk sticks & boots the killer Windows 98 CRT PC!
		if (t >= 43.15 && intro_ev < 35)
		{
			intro_ev = 35;
			Intro_Cue ("netsend/ns_beep.wav", 0.95);
			Intro_Cue ("larry/it_wont_boot.wav", 1.0);

			ia_nspc = spawn ();
			ia_nspc.intro_tag = 1;
			ia_nspc.movetype = MOVETYPE_NONE;
			ia_nspc.solid = SOLID_NOT;
			setmodel (ia_nspc, "progs/netsend_pc.md3");
			ia_nspc.scale = 1.30;
			setsize (ia_nspc, '0 0 0', '0 0 0');
			setorigin (ia_nspc, '542 -782 2');

			ia_nsarc = spawn ();
			ia_nsarc.intro_tag = 1;
			ia_nsarc.movetype = MOVETYPE_NONE;
			ia_nsarc.solid = SOLID_NOT;
			setmodel (ia_nsarc, "progs/netsend_arc.md3");
			ia_nsarc.scale = 1.30;
			ia_nsarc.effects = EF_FULLBRIGHT;
			setsize (ia_nsarc, '0 0 0', '0 0 0');
			setorigin (ia_nsarc, '542 -782 2');

			Intro_FlyBolt ('542 -782 26', '-115 45 8', "progs/netsend_disk.md3", 1.85, 1.2);
			Intro_FlyBolt ('542 -782 24', '-120 25 12', "progs/netsend_laser.md3", 1.55, 1.2);
		}
		// 44.75s: Foreground swaps to 3D Laptop Gun typing & zapping Friend Rob!
		if (t >= 44.75 && intro_ev < 36)
		{
			intro_ev = 36;
			Intro_Cue ("ltgun/type.wav", 0.95);
			Intro_Cue ("ltgun/canis.wav", 1.0);

			ia_ltg_head = spawn ();
			ia_ltg_head.intro_tag = 1;
			ia_ltg_head.movetype = MOVETYPE_NONE;
			ia_ltg_head.solid = SOLID_NOT;
			setmodel (ia_ltg_head, "progs/ltg_head.md3");
			ia_ltg_head.scale = 1.85;
			ia_ltg_head.colormod = '1.35 1.35 1.35';
			ia_ltg_head.effects = EF_FULLBRIGHT;
			setsize (ia_ltg_head, '-6 -6 -6', '6 6 6');
			ia_ltg_head.customizeentityforclient = LtGun_HeadCustomize;
			setorigin (ia_ltg_head, '540 -726 36');

			ia_ltg_aura = spawn ();
			ia_ltg_aura.intro_tag = 1;
			ia_ltg_aura.movetype = MOVETYPE_NONE;
			ia_ltg_aura.solid = SOLID_NOT;
			setmodel (ia_ltg_aura, "progs/ltg_aura.md3");
			ia_ltg_aura.scale = 1.85;
			ia_ltg_aura.effects = EF_FULLBRIGHT;
			setsize (ia_ltg_aura, '0 0 0', '0 0 0');
			ia_ltg_aura.customizeentityforclient = LtGun_AuraCustomize;
			setorigin (ia_ltg_aura, '540 -726 36');
		}
		if (t >= 45.65 && intro_ev < 37)
		{
			intro_ev = 37;
			Intro_Cue ("ltgun/zap.wav", 0.95);
			Intro_FlyBolt ('540 -726 36', '10 -28 -10', "progs/ltg_laser.md3", 1.65, 1.0);
			Intro_FlyBolt ('540 -726 36', '-115 -35 6', "progs/ltg_laser.md3", 1.55, 1.2);
		}

		u = (t - 42.0) / 5.4;
		if (ia_spot1)
		{
			Intro_Spin360 (ia_spot1, '555 -748 2', '544 -750 2', u, TRUE);
			if (t >= 45.65)
			{
				pos = ia_spot1.origin;
				pos_z = 2 + fabs (ISin ((t - 45.65) * 16.0)) * 14;
				setorigin (ia_spot1, pos);
			}
		}
		if (ia_nspc)
		{
			f = floor ((t - 43.15) * 10);
			if (f > 39)
				f = 20 + (f - 20 * floor (f / 20));
			ia_nspc.frame = f;
			ia_nspc.skin = NS_Skin (f);
			ia_nspc.angles_y = vectoyaw (intro_cam_pos - ia_nspc.origin);
			if (ia_nsarc)
			{
				ia_nsarc.frame = floor (time * 16) - 8 * floor ((time * 16) / 8);
				ia_nsarc.angles_y = ia_nspc.angles_y;
			}
		}
		if (ia_ltg_head)
		{
			pos = '540 -726 36' + '0 0 1' * (ISin (t * 5.0) * 3.5);
			ia_ltg_head.ltg_head = vectoyaw (intro_cam_pos - pos) + (t - 44.75) * 180;
			setorigin (ia_ltg_head, pos);
			if (ia_ltg_aura)
				setorigin (ia_ltg_aura, pos);
		}
	}

	// ================================================================
	// CARD 10 (47.4s .. 52.8s): LARRY'S 120A MEGA MAN BEDROOM SHRINE
	//         Red-Shop-Rag Chrome Polish (*DING!*) + Slingshot + Driving Mega Man!
	// ================================================================
	else if (t < 52.8)
	{
		intro_cur_card = 10;
		if (intro_ev < 38)
		{
			intro_ev = 38;
			Intro_ClearSpot ();
			Intro_EvalCam (10, t);
		}
		// 48.95s: Chrome sparkle *DING!* at frame 82 of v_mm_cannon.md3's red-shop-rag polish!
		if (t >= 48.95 && intro_ev < 39)
		{
			intro_ev = 39;
			Intro_Cue ("weapons/tink1.wav", 1.0);
		}
		// 49.45s: Cannon fires wheel-driving 3D Mega Man right beside his own Bed Shrine!
		if (t >= 49.45 && intro_ev < 40)
		{
			intro_ev = 40;
			Intro_Cue ("friends/megamayan.wav", 1.0);
			Intro_Cue ("megaman/mm_fire.wav", 0.95);
			Intro_Cue ("weapons/megahorn.wav", 0.95);
			sound (intro_cam, 6, "weapons/megamotor.wav", 0.78, ATTN_NONE);

			ia_spot1 = Intro_MakeActor (1, 1.78, '-1140 -2185 4');
		}
		if (ia_spot1 && t < 51.65)
		{
			u = (t - 49.45) / 2.20;
			if (u < 0.72)
				Intro_Spin360 (ia_spot1, '-1140 -2185 4', '-1192 -2170 4', u / 0.72 * 0.78, TRUE);
			else
			{
				// Headcrab leap arc over his Mega Man bed!
				f = (u - 0.72) / 0.28;
				pos = Intro_LerpVec ('-1192 -2170 4', '-1222 -2205 26', f);
				pos_z = pos_z + ISin (f * 3.14159) * 34;
				ia_spot1.angles_y = vectoyaw (intro_cam_pos - pos);
				setorigin (ia_spot1, pos);
			}
		}
		if (t >= 51.65 && intro_ev < 41)
		{
			intro_ev = 41;
			sound (intro_cam, 6, "misc/null.wav", 1, ATTN_NONE);
			Intro_Cue ("grenade/boom_04_mega_fart.wav", 1.0);
			if (ia_spot1)
			{
				Intro_SpawnMMDome (ia_spot1.origin + '0 0 12');
				remove (ia_spot1);
				ia_spot1 = world;
			}
		}
	}

	// ================================================================
	// CARD 11 (52.8s .. 57.8s): ORCOM CONNECT BANQUET LAN HALL
	//         Goo Gun Expanding Foam Stack + Pong Balls vs. Big-Ears & Rubber Finger!
	// ================================================================
	else if (t < 57.8)
	{
		intro_cur_card = 11;
		if (intro_ev < 42)
		{
			intro_ev = 42;
			Intro_ClearSpot ();
			Intro_EvalCam (11, t);
			Intro_Cue ("mbox/drv_boing_hop.wav", 0.95);

			ia_spot1 = Intro_MakeActor (7,  1.15, '6142 1122 30');	// Giant 3D Big-Ears
			ia_spot2 = Intro_MakeActor (22, 1.28, '6150 1152 2');	// Rubber Finger
		}
		if (t >= 53.45 && intro_ev < 43)
		{
			intro_ev = 43;
			Intro_Cue ("weapons/goofire.wav", 0.95);
			Intro_StickGooFoam ('6158 1096 8');
			Intro_FlyBolt ('6215 1120 34', '-150 22 10', "progs/fg_pongball.md3", 2.1, 1.6);
		}
		if (t >= 54.15 && intro_ev < 44)
		{
			intro_ev = 44;
			Intro_Cue ("weapons/goofire.wav", 0.95);
			Intro_Cue ("fungun/fg_bonk_hit.wav", 0.95);
			Intro_StickGooFoam ('6158 1170 8');
			Intro_FlyBolt ('6215 1148 34', '-150 -24 14', "progs/fg_pongball.md3", 2.1, 1.6);
		}
		if (t >= 54.85 && intro_ev < 45)
		{
			intro_ev = 45;
			Intro_Cue ("weapons/goofire.wav", 0.95);
			Intro_Cue ("funny/durr.wav", 1.0);
			Intro_StickGooFoam ('6172 1092 22');
			Goo_Chunks ('6158 1134 28');
		}

		u = (t - 52.8) / 5.0;
		if (ia_spot1)
		{
			pos = '6142 1120 28';
			pos_z = 28 + ISin ((t - 52.8) * 5.0) * 5;
			ia_spot1.angles_y = vectoyaw (intro_cam_pos - pos) + Intro_Smooth (u / 0.85) * 360;
			setorigin (ia_spot1, pos);
		}
		if (ia_spot2)
		{
			pos = '6150 1152 2';
			pos_z = 2 + fabs (ISin ((t - 52.8) * 9.5)) * 20;
			ia_spot2.angles_y = vectoyaw (intro_cam_pos - pos) + Intro_Smooth (u / 0.85) * 360;
			setorigin (ia_spot2, pos);
		}
	}

	// ================================================================
	// CARD 12 (57.8s .. 62.8s): GOLDEN WEST CASINO & GIANT HORSE PLAZA
	//         David Ojeda 777 Slot Jackpot, Money Bag Sprint & Pregnant Trio!
	// ================================================================
	else if (t < 62.8)
	{
		intro_cur_card = 12;
		if (intro_ev < 46)
		{
			intro_ev = 46;
			Intro_ClearSpot ();
			Intro_EvalCam (12, t);
			Intro_Cue ("david/slot_jackpot.wav", 0.98);
			Intro_Cue ("david/shower_love.wav", 1.0);

			ia_spot1 = spawn ();
			ia_spot1.intro_tag = 1;
			ia_spot1.movetype = MOVETYPE_NONE;
			ia_spot1.solid = SOLID_NOT;
			setmodel (ia_spot1, "progs/david.spr32");
			ia_spot1.scale = 0.31;
			setsize (ia_spot1, '0 0 0', '0 0 0');
			ia_spot1.dv_state = 6;		// 777 Slot Machine Jackpot!
			ia_spot1.angles = '0 270 0';
			ia_spot1.customizeentityforclient = David_Customize;
			setorigin (ia_spot1, '-6397 -11998 2');

			// Placed cleanly on the flagstone plaza (y < -11985, clear of the stone flowerbed!)
			ia_spot2 = Intro_MakeActor (24, 1.16, '-6438 -12006 2');	// Pregnant Runner 1
			ia_spot3 = Intro_MakeActor (25, 1.16, '-6356 -12006 2');	// Pregnant Runner 2
			ia_spot4 = Intro_MakeActor (26, 1.16, '-6420 -12020 2');	// Pregnant Runner 3
			ia_spot5 = Intro_MakeActor (6,  0.95, '-6362 -12022 9');	// Prancing Golden Casino Horse
		}

		u = (t - 57.8) / 5.0;
		if (ia_spot1)
		{
			front = vectoyaw (intro_cam_pos - ia_spot1.origin);
			if (t < 59.30)
			{
				ia_spot1.dv_state = 6;
				setorigin (ia_spot1, '-6397 -11998 2');
				ia_spot1.angles_y = front + ISin ((t - 57.8) * 5.5) * 18;
			}
			else if (t < 60.65)
			{
				ia_spot1.dv_state = 3;
				setorigin (ia_spot1, '-6397 -11998 2');
				ia_spot1.angles_y = front + Intro_Smooth ((t - 59.30) / 1.35) * 360;
			}
			else
			{
				if (intro_ev < 47)
				{
					intro_ev = 47;
					Intro_Cue ("david/money_bag.wav", 1.0);
				}
				ia_spot1.dv_state = 4;		// Money Bag getaway sprint!
				f = (t - 60.65) / 2.15;
				pos = Intro_LerpVec ('-6397 -11998 2', '-6342 -12014 2', f);
				ia_spot1.angles_y = front + 24;
				setorigin (ia_spot1, pos);
			}
		}
		Intro_Spin360 (ia_spot2, '-6444 -12002 2', '-6434 -12008 2', u, TRUE);
		Intro_Spin360 (ia_spot3, '-6350 -12002 2', '-6360 -12008 2', u, TRUE);
		Intro_Spin360 (ia_spot4, '-6424 -12018 2', '-6416 -12022 2', u, TRUE);
		if (ia_spot5)
		{
			pos = '-6362 -12022 9';
			pos_z = 9 + fabs (ISin ((t - 57.8) * 8.5)) * 10;
			ia_spot5.angles_y = vectoyaw (intro_cam_pos - pos) + Intro_Smooth (u / 0.85) * 360;
			setorigin (ia_spot5, pos);
		}
	}

	// ================================================================
	// CARD 13 (62.8s .. 67.8s): BUCK OWENS' CRYSTAL PALACE & KUZZ RADIO VAN
	//         Mystery Box Throw -> Tinfoil-Hat Bryan, 3 Red Demons & Hell Portal!
	// ================================================================
	else if (t < 67.8)
	{
		intro_cur_card = 13;
		if (intro_ev < 48)
		{
			intro_ev = 48;
			Intro_ClearSpot ();
			Intro_EvalCam (13, t);
		}
		if (t >= 63.65 && intro_ev < 49)
		{
			intro_ev = 49;
			Intro_Cue ("weapons/lstart.wav", 0.90);
			ia_spot2 = spawn ();
			ia_spot2.intro_tag = 1;
			ia_spot2.movetype = MOVETYPE_TOSS;
			ia_spot2.solid = SOLID_NOT;
			setmodel (ia_spot2, "progs/proj_mysterybox.md3");
			ia_spot2.scale = 1.55;
			ia_spot2.avelocity = '180 360 120';
			setsize (ia_spot2, '0 0 0', '0 0 0');
			setorigin (ia_spot2, '11730 -3815 44');
			ia_spot2.velocity = '0 -95 90';
		}
		if (t >= 64.15 && intro_ev < 50)
		{
			intro_ev = 50;
			if (ia_spot2) { remove (ia_spot2); ia_spot2 = world; }
			Intro_TelePop ('11730 -3862 22');
			Intro_Cue ("misc/r_tele5.wav", 0.85);
			Intro_Cue ("bryan/detector.wav", 0.95);

			ia_spot1 = spawn ();
			ia_spot1.intro_tag = 1;
			ia_spot1.movetype = MOVETYPE_NONE;
			ia_spot1.solid = SOLID_NOT;
			setmodel (ia_spot1, "progs/bryan.spr32");
			ia_spot1.scale = 0.37;
			setsize (ia_spot1, '0 0 0', '0 0 0');
			ia_spot1.br_state = 0;
			ia_spot1.angles = '0 90 0';
			ia_spot1.customizeentityforclient = Bryan_Customize;
			setorigin (ia_spot1, '11730 -3862 5');
		}
		if (ia_spot1)
		{
			front = vectoyaw (intro_cam_pos - ia_spot1.origin);
			if (t < 64.95)
			{
				ia_spot1.br_state = 0;
				ia_spot1.angles_y = front + ISin ((t - 64.15) * 6.0) * 28;
			}
			else if (t < 66.15)
			{
				if (intro_ev < 51)
				{
					intro_ev = 51;
					Intro_Cue ("bryan/noway.wav", 1.0);
					Intro_Cue ("bryan/whirl.wav", 0.92);
				}
				ia_spot1.br_state = 3;		// 3 Red Demons orbiting Bryan!
				ia_spot1.effects = 64;
				ia_spot1.angles_y = front + Intro_Smooth ((t - 64.95) / 1.20) * 360;
			}
			else if (t < 66.75)
			{
				ia_spot1.br_state = 2;		// Giant Demon Tornado!
				ia_spot1.angles_y = front + ((t - 66.15) / 0.60) * 360;
			}
			else
			{
				if (intro_ev < 52)
				{
					intro_ev = 52;
					Intro_Cue ("bryan/portal_die.wav", 1.0);
					ia_spot1.customizeentityforclient = SUB_Null;
					ia_spot1.effects = 128;
				}
				f = floor (((t - 66.75) / 1.00) * 31);
				if (f > 31)
				{
					f = 31;
					ia_spot1.effects = 0;
				}
				ia_spot1.frame = 232 + f;
			}
		}
	}

	// ================================================================
	// CARD 14 (67.8s .. 72.8s): AMBERTON PARK PICNIC SHELTER
	//         JohnWave 3D Head Grenade, Wheelie Riders & Rocket Park Trash Can!
	// ================================================================
	else if (t < 72.8)
	{
		intro_cur_card = 14;
		if (intro_ev < 53)
		{
			intro_ev = 53;
			Intro_ClearSpot ();
			Intro_EvalCam (14, t);
			Intro_Cue ("john/jv15.wav", 1.0);
			Intro_Cue ("grenade/bounce_08_rubber_ball.wav", 0.95);

			ia_spot1 = Intro_MakeActor (2, 1.22, '14738 -14114 4');	// Suit Rider
			ia_spot2 = Intro_MakeActor (4, 1.22, '14738 -14066 4');	// Squat Rider

			// Standing Park Trash Can ready for rocket liftoff!
			ia_spot3 = spawn ();
			ia_spot3.intro_tag = 1;
			ia_spot3.movetype = MOVETYPE_NONE;
			ia_spot3.solid = SOLID_NOT;
			setmodel (ia_spot3, "progs/bklan/trashcan.md3");
			ia_spot3.scale = 1.28;
			setsize (ia_spot3, '0 0 0', '0 0 0');
			setorigin (ia_spot3, '14696 -14122 2');

			// Giant bouncing 3D John Head Grenade!
			ia_spot4 = spawn ();
			ia_spot4.intro_tag = 1;
			ia_spot4.movetype = MOVETYPE_BOUNCE;
			ia_spot4.solid = SOLID_BBOX;
			setmodel (ia_spot4, "progs/johnhead3d.md3");
			ia_spot4.scale = 1.85;
			ia_spot4.bouncefactor = 0.86;
			ia_spot4.avelocity = '180 340 120';
			setsize (ia_spot4, '0 0 0', '0 0 0');
			setorigin (ia_spot4, '14712 -14090 58');
			ia_spot4.velocity = '12 0 185';
		}
		if (t >= 69.35 && intro_ev < 54)
		{
			intro_ev = 54;
			Intro_Cue ("grenade/boom_03_scream_launch.wav", 0.95);
			Intro_Cue ("funny/fart2.wav", 1.0);
			if (ia_spot4)
			{
				Intro_SpawnJohnWave ('14716 -14090 4');
				remove (ia_spot4);
				ia_spot4 = world;
			}
		}
		if (t >= 70.60 && intro_ev < 55)
		{
			intro_ev = 55;
			Intro_Cue ("john/jv11.wav", 0.95);
			if (ia_spot3) { remove (ia_spot3); ia_spot3 = world; }
			Intro_LaunchTrashcan ('14696 -14122 2');
		}

		u = (t - 67.8) / 5.0;
		if (ia_spot1 && ia_spot2)
		{
			if (u < 0.58)
			{
				Intro_Spin360 (ia_spot1, '14752 -14116 4', '14736 -14114 4', u / 0.58 * 0.78, TRUE);
				Intro_Spin360 (ia_spot2, '14752 -14064 4', '14736 -14066 4', u / 0.58 * 0.78, TRUE);
			}
			else
			{
				f = floor (((u - 0.58) / 0.42) * 18);
				f = f - 8 * floor (f / 8);
				ia_spot1.frame = 52 + f;		// Synchronized wheelie slam!
				ia_spot2.frame = 52 + f;
				ia_spot1.angles_y = vectoyaw (intro_cam_pos - ia_spot1.origin) - 12;
				ia_spot2.angles_y = vectoyaw (intro_cam_pos - ia_spot2.origin) + 12;
			}
		}
	}

	// ================================================================
	// CARD 15 (72.8s .. 78.0s): FULL-CIRCLE FINALE BACK UNDER THE BAKERSFIELD SIGN!
	//         White LAN Van + Roof-Dancing Wheelman + Convoy rolls out under the Sign!
	// ================================================================
	else
	{
		intro_cur_card = 15;
		if (intro_ev < 56)
		{
			intro_ev = 56;
			Intro_ClearSpot ();
			Intro_EvalCam (15, t);
			Intro_Cue ("vehicles/horn.wav", 0.95);
			Intro_Cue ("funny/quakeahh.wav", 1.0);
			sound (intro_cam, 6, "vehicles/lanvan.wav", 0.82, ATTN_NONE);

			ia_van = spawn ();
			ia_van.intro_tag = 1;
			ia_van.movetype = MOVETYPE_NONE;
			ia_van.solid = SOLID_NOT;
			setmodel (ia_van, "progs/veh_van.md3");
			setsize (ia_van, '0 0 0', '0 0 0');
			ia_van.angles = '0 0 0';
			setorigin (ia_van, '11890 -2736 2');

			ia_vansurf = spawn ();
			ia_vansurf.intro_tag = 1;
			ia_vansurf.movetype = MOVETYPE_NONE;
			ia_vansurf.solid = SOLID_NOT;
			setmodel (ia_vansurf, "progs/wheelman_dance.spr32");
			ia_vansurf.scale = 0.44;
			ia_vansurf.wc_anim = 4;
			ia_vansurf.wc_t0 = time;
			ia_vansurf.customizeentityforclient = WC_DancerCustomize;
			setsize (ia_vansurf, '0 0 0', '0 0 0');
			setorigin (ia_vansurf, '11890 -2736 92');

			ia_pinkcar = spawn ();
			ia_pinkcar.intro_tag = 1;
			ia_pinkcar.movetype = MOVETYPE_NONE;
			ia_pinkcar.solid = SOLID_NOT;
			setmodel (ia_pinkcar, "progs/pink_supercar.md3");
			ia_pinkcar.frame = 47;
			ia_pinkcar.angles = '0 0 0';
			setsize (ia_pinkcar, '0 0 0', '0 0 0');
			setorigin (ia_pinkcar, '11840 -2565 2');

			ia_spot1 = Intro_MakeActor (10, 1.24, '11850 -2895 2');	// JessKart escort!
			ia_forklift = Intro_MakeActor (8, 0.95, '11790 -2960 2');	// Orange Forklift!

			// Cheerful wave-off runners along the sidewalks!
			Intro_SpawnVanRunner (19, '12020 -2590 2', 12060, -2585, 65, 95, 0,   5.5, 1.20);
			Intro_SpawnVanRunner (21, '12020 -2885 2', 12060, -2885, 65,-95, 90,  5.5, 1.20);
			Intro_SpawnVanRunner (22, '12140 -2605 2', 12160, -2600, 60, 110,180, 5.5, 1.24);
			Intro_SpawnVanRunner (23, '12140 -2870 2', 12160, -2875, 60,-105,270, 5.5, 1.22);
		}
		if (t >= 75.0 && intro_ev < 57)
		{
			intro_ev = 57;
			Intro_Cue ("vehicles/horn.wav", 0.88);
		}

		u = (t - 72.8) / 5.0;
		if (u > 1)
			u = 1;
		if (ia_van)
		{
			pos = Intro_LerpVec ('11890 -2736 2', '12430 -2736 2', u);
			f = floor (time * 18);
			ia_van.frame = f - 16 * floor (f / 16);
			setorigin (ia_van, pos);
			if (ia_vansurf)
			{
				setorigin (ia_vansurf, pos + '0 0 92');
				ia_vansurf.angles_y = 180 + u * 720;
			}
		}
		if (ia_pinkcar)
			setorigin (ia_pinkcar, Intro_LerpVec ('11840 -2565 2', '12380 -2565 2', u));
		if (ia_spot1)
		{
			pos2 = Intro_LerpVec ('11850 -2895 2', '12390 -2895 2', u);
			ia_spot1.angles_y = 0;
			setorigin (ia_spot1, pos2);
		}
		if (ia_forklift)
		{
			pos2 = Intro_LerpVec ('11790 -2960 2', '12260 -2960 2', u);
			ia_forklift.angles_y = 270;
			setorigin (ia_forklift, pos2);
		}

		if (t >= 77.30 && !intro_stopped)
		{
			intro_stopped = TRUE;
			sound (intro_cam, 6, "misc/null.wav", 1, ATTN_NONE);
			localcmd ("stop\n");
		}
		if (t >= 77.80 && !intro_quitted)
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
	intro_stopped = FALSE;
	intro_quitted = FALSE;
	intro_cam_fixed = FALSE;
	intro_cur_card = 1;
	intro_cam_pos = '11520 -2736 98';
	intro_cam_ang = Intro_LookAngles ('11520 -2736 98', '12180 -2736 86');

	intro_dir_ent = spawn ();
	intro_dir_ent.classname = "intro_director";
	intro_dir_ent.think = Intro_Tick;
	intro_dir_ent.nextthink = time + 0.02;
};
