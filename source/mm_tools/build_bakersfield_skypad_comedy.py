#!/usr/bin/env python3
"""Record a real-time machinima comedy video on `bakersfielddowntown` showing
actual player models firing EVERY projectile into an info_skypad, following each
projectile in real time to a staged humorous payoff/kill/bounce, ending with
an ALL-PROJECTILES-AT-ONCE chaos finale, and send the MP4 to Telegram BAKOQUAKE.

Usage:
    python source/mm_tools/build_bakersfield_skypad_comedy.py --capture
    TG_BOT_TOKEN=... python source/mm_tools/build_bakersfield_skypad_comedy.py --telegram
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = HERE.parent.parent
ROOT = MOD.parent
SRC_QC = MOD / "source" / "qc_combat_decomp"

ZIRCON = ROOT / "engine" / "zircon_beta_gcc.exe"
FTEQCC = Path(r"D:\vibe\fteqw\2025-09-27-github\fteqcc64.exe")
if not FTEQCC.is_file():
    FTEQCC = Path(r"D:\vibe\quake1opensource\engines\win64\fteqcc64.exe")
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

OUT_ROOT = HERE / "out" / "skypad_comedy"
BUILD_DIR = OUT_ROOT / "build"
USERDIR = OUT_ROOT / "userdir"
OUT_MP4 = OUT_ROOT / "bakersfield_skypad_comedy.mp4"

TG_CHAT_ID = "-4993867752"

DIRECTOR_QC = r'''
// Staged Bakersfield Downtown comedy director (compiled ONLY into temp capture progs.dat)
entity sp_dir, sp_cam, sp_host, sp_b1, sp_b2, sp_b3, sp_b4, sp_mon;
entity sp_proj, sp_victim_bird, sp_jb, sp_tank, sp_pad;
float sp_stage, sp_next_t, sp_stage_t, sp_hit_t, sp_started, sp_done, sp_fired, sp_finale_burst;
vector sp_pad_org, sp_dst_org, sp_pad_vel, sp_pad_dir, sp_pad_right, sp_shoot_pos, sp_shoot_dir, sp_shoot_right, sp_cam_pos, sp_last_pos;
string sp_label;

void() SP_VidPrecache =
{
	precache_model ("progs/missile.mdl");
	precache_model ("progs/grenade.mdl");
	precache_model ("progs/proxbomb.mdl");
	precache_model ("progs/spike.mdl");
	precache_model ("progs/laser.mdl");
	precache_model ("progs/lasrspik.mdl");
	precache_model ("progs/bullettr.mdl");
	precache_model ("progs/w_spike.mdl");
	precache_model ("progs/k_spike.mdl");
	precache_model ("progs/v_spike.mdl");
	precache_model ("progs/face.mdl");
	precache_model ("progs/reiver_fireball.mdl");
	precache_model ("progs/ghost_follower.spr32");
	precache_model ("progs/carniv_rocks.mdl");
	precache_model ("progs/h_grenade2.mdl");
	precache_model ("progs/mon_jimrock.mdl");
	precache_model ("progs/mm_tank_bar.md3");
	precache_model ("progs/jb_spraying_can.md3");
	precache_model ("progs/jb_hairspray_can.md3");
	precache_model ("progs/banana.md3");
	precache_sound ("ccc/shoot.wav");
	precache_sound ("weapons/grenade.wav");
	precache_sound ("weapons/sgun1.wav");
	precache_sound ("weapons/bananafire.wav");
	precache_sound ("weapons/bananavoice.wav");
	precache_sound ("shalrath/attack2.wav");
	precache_sound ("wizard/wattack.wav");
	precache_sound ("warlord/homing_touch.wav");
	precache_sound ("reiver/reiver_fireball_shoot.wav");
	precache_sound ("lostsoul/idle1.wav");
	precache_sound ("lostsoul/idle2.wav");
	precache_sound ("lostsoul/charge.wav");
	precache_sound ("face/face.wav");
	precache_sound ("john_bird/jb_bottle_fire.wav");
	precache_sound ("vehicles/van_idle.wav");
};

vector(vector from, vector to) SP_Look =
{
	local vector a;
	local float px;
	a = vectoangles (to - from);
	px = a_x;
	if (px > 180) px = px - 360;
	a_x = 0 - px;
	a_z = 0;
	return a;
};

void(entity p, vector pos, vector target) SP_Face =
{
	local vector ang;
	setorigin (p, pos);
	p.velocity = '0 0 0';
	ang = SP_Look (pos + '0 0 18', target);
	p.v_angle = ang;
	p.angles = '0 1 0' * ang_y;
	p.fixangle = TRUE;
};

entity(string cls) SP_FindNewest =
{
	local entity e, best;
	best = world;
	e = find (world, classname, cls);
	while (e != world)
	{
		best = e;
		e = find (e, classname, cls);
	}
	return best;
};

void(entity p) SP_Stock =
{
	p.health = 999;
	p.takedamage = DAMAGE_AIM;
	p.deadflag = DEAD_NO;
	p.solid = SOLID_SLIDEBOX;
	p.movetype = MOVETYPE_WALK;
	p.ammo_rockets = 99;
	p.ammo_nails = 999;
	p.ammo_cells = 999;
	p.grenade_ammo = 99;
	p.mm_ammo = 9;
	p.bn_ammo = 9;
	FunGun_SetAmmo (p, FG_WCANNON, 9);
	FunGun_SetAmmo (p, FG_DOOKIE, 9);
	FunGun_SetAmmo (p, FG_DOB, 9);
	FunGun_SetAmmo (p, FG_PONG, 9);
	FunGun_SetAmmo (p, FG_PICKLE, 9);
	FunGun_SetAmmo (p, FG_NETSEND, 9);
	FunGun_SetAmmo (p, FG_KYLE, 9);
};

void(entity b, vector pos, float hp) SP_PlaceVictim =
{
	b.solid = SOLID_SLIDEBOX;
	b.movetype = MOVETYPE_NONE;
	b.takedamage = DAMAGE_AIM;
	b.deadflag = DEAD_NO;
	b.health = hp;
	b.max_health = hp;
	b.velocity = '0 0 0';
	b.items = b.items - (b.items & IT_INVULNERABILITY);
	b.bm_prot_t = 0;
	setorigin (b, pos);
	b.angles = SP_Look (pos, sp_pad_org);
	b.angles_x = 0;
	b.angles_z = 0;
};

vector(float t) SP_SkyRayPos =
{
	return sp_pad_org + sp_pad_vel * t;
};

vector(float t) SP_ArcPos =
{
	local vector p;
	p = sp_pad_org + sp_pad_vel * t;
	p_z = p_z - 400 * t * t;
	return p;
};

void() SP_ClearScene =
{
	local entity e, nx;
	local string c;

	e = nextent (world);
	while (e != world)
	{
		nx = nextent (e);
		c = e.classname;
		if (c == "missile" || c == "grenade" || c == "proximity_grenade" || c == "spike"
			|| c == "hiplaser" || c == "playershot" || c == "megaman" || c == "kyle_proj"
			|| c == "wc_shot" || c == "milky" || c == "robdob" || c == "dookie_shot"
			|| c == "dookie_glob" || c == "bigbanana" || c == "minibanana" || c == "pickle"
			|| c == "pkgib" || c == "greenjar_proj" || c == "greenguy_mini" || c == "netsend_disk"
			|| c == "netsend_pc" || c == "netsend_arc" || c == "netsend_screen"
			|| c == "ltg_head" || c == "ltg_aura" || c == "mm_tank_bar"
			|| c == "jb_bottle_proj" || c == "jb_aerosol_bomb" || c == "ShalrathMissile"
			|| c == "wizspike" || c == "hknight2_homing" || c == "Reiver_fireball"
			|| c == "ghost_follower" || c == "carniv_projectile" || c == "face"
			|| c == "gib" || c == "dookie_wall_splat" || c == "dookie_splat_fx")
		{
			remove (e);
		}
		e = nx;
	}
	if (sp_victim_bird && !bm_wasfreed (sp_victim_bird))
	{
		if (sp_victim_bird.jb_pilot)
			JB_Leave (sp_victim_bird, sp_dst_org, '0 0 0', FALSE);
		remove (sp_victim_bird);
		sp_victim_bird = world;
	}
	if (sp_b1)
	{
		if (sp_b1.fd_head) { remove (sp_b1.fd_head); sp_b1.fd_head = world; }
		if (sp_b1.fd_cam) { remove (sp_b1.fd_cam); sp_b1.fd_cam = world; }
		FD_Restore (sp_b1);
		sp_b1.fd_fade = 0;
		sp_b1.milky_active = world;
		if (sp_b1.ky_cam) KY_CamDetach (sp_b1);
	}
	sp_proj = world;
	sp_hit_t = 0;
};

void(float st) SP_SetupStage =
{
	local vector vpos;

	SP_ClearScene ();
	sp_stage_t = time;
	sp_fired = FALSE;
	sp_finale_burst = 0;

	SP_Stock (sp_b1);
	sp_b1.attack_finished = time + 999;

	// Shooter model stands visibly on ground level beside the SkyPad so muzzle Z (~48) hits dead-center of pad (Z 6..68)!
	SP_Face (sp_b1, sp_shoot_pos, sp_pad_org - '0 0 6');

	// Park extra bots far out of the way until placed as scene victims
	SP_PlaceVictim (sp_b2, sp_dst_org + '0 -240 16', 999);
	SP_PlaceVictim (sp_b3, sp_dst_org + '80 -240 16', 999);
	SP_PlaceVictim (sp_b4, sp_dst_org + '-80 -240 16', 999);

	// Camera starts 3/4 behind & beside sp_b1 in open street so you clearly see the full player model aim & shoot!
	sp_cam_pos = sp_shoot_pos - sp_shoot_dir * 95 + sp_shoot_right * 72 + '0 0 42';
	traceline (sp_shoot_pos + '0 0 24', sp_cam_pos, TRUE, sp_b1);
	if (trace_fraction < 1)
		sp_cam_pos = trace_endpos + trace_plane_normal * 12;
	sp_last_pos = sp_pad_org + '0 0 18';

	// Place funny scene-specific victims along each projectile's real trajectory or landing zone!
	if (st == 1)
	{
		sp_label = "1/17  ROCKET vs JETPACK CAMPER";
		SP_PlaceVictim (sp_b2, SP_SkyRayPos (0.85), 35);
		sp_b2.jp_fuel = 30;
		sp_b2.jp_on = TRUE;
		sp_next_t = time + 2.8;
	}
	else if (st == 2)
	{
		sp_label = "2/17  GRENADE AIRBURST vs WINGED JOHN BIRD";
		vpos = SP_ArcPos (2.45);
		sp_victim_bird = spawn ();
		setorigin (sp_victim_bird, vpos);
		JB_InitEntity (sp_victim_bird, TRUE);
		sp_victim_bird.movetype = MOVETYPE_NONE;
		SP_PlaceVictim (sp_b2, vpos, 40);
		JB_Enter (sp_b2, sp_victim_bird);
		sp_next_t = time + 3.8;
	}
	else if (st == 3)
	{
		sp_label = "3/17  PROXIMITY GRENADE -> FOX THEATER SQUAD";
		SP_PlaceVictim (sp_b2, sp_dst_org + '0 0 20', 40);
		SP_PlaceVictim (sp_b3, sp_dst_org + '42 -28 20', 40);
		sp_next_t = time + 6.4;
	}
	else if (st == 4)
	{
		sp_label = "4/17  NAILGUN STREAM vs FLOATING VICTIM";
		SP_PlaceVictim (sp_b2, SP_SkyRayPos (0.82), 18);
		sp_next_t = time + 2.7;
	}
	else if (st == 5)
	{
		sp_label = "5/17  LASER CANNON ANTI-AIR SNIPE";
		SP_PlaceVictim (sp_b2, SP_SkyRayPos (0.78), 20);
		sp_next_t = time + 2.6;
	}
	else if (st == 6)
	{
		sp_label = "6/17  MEGA MAN CROSS-CITY DELIVERY";
		SP_PlaceVictim (sp_b2, sp_dst_org + '32 0 20', 60);
		SP_PlaceVictim (sp_b3, sp_dst_org + '-32 32 20', 60);
		sp_next_t = time + 6.6;
	}
	else if (st == 7)
	{
		sp_label = "7/17  POCKET KYLE (0.75s FLING -> MID-AIR SCISSOR LATCH!)";
		SP_PlaceVictim (sp_b2, SP_SkyRayPos (1.10) + '120 90 -80', 80);
		sp_next_t = time + 4.4;
	}
	else if (st == 8)
	{
		sp_label = "8/17  WHEELMAN ROADKILL AT FOX THEATER";
		SP_PlaceVictim (sp_b2, sp_dst_org + '0 0 20', 50);
		SP_PlaceVictim (sp_b3, sp_dst_org + '36 36 20', 50);
		sp_next_t = time + 6.4;
	}
	else if (st == 9)
	{
		sp_label = "9/17  PINK LADY MILKY (0.75s FLING -> RE-HOME!)";
		SP_PlaceVictim (sp_b2, SP_SkyRayPos (1.05) + '-140 120 -60', 55);
		sp_next_t = time + 4.5;
	}
	else if (st == 10)
	{
		sp_label = "10/17  ROB DOB DRONE -> SKY AMBUSH";
		SP_PlaceVictim (sp_b2, SP_SkyRayPos (1.05), 40);
		sp_next_t = time + 3.5;
	}
	else if (st == 11)
	{
		sp_label = "11/17  FLYING DOOKIE -> POOP-SPLAT BIRD!";
		vpos = SP_SkyRayPos (0.92);
		sp_victim_bird = spawn ();
		setorigin (sp_victim_bird, vpos);
		JB_InitEntity (sp_victim_bird, TRUE);
		sp_victim_bird.movetype = MOVETYPE_NONE;
		SP_PlaceVictim (sp_b2, vpos, 60);
		JB_Enter (sp_b2, sp_victim_bird);
		sp_next_t = time + 3.2;
	}
	else if (st == 12)
	{
		sp_label = "12/17  BANANA CANNON -> MID-AIR BANANA SPLIT!";
		SP_PlaceVictim (sp_b2, SP_SkyRayPos (0.90), 35);
		sp_next_t = time + 3.0;
	}
	else if (st == 13)
	{
		sp_label = "13/17  PICKLE SURPRISE -> FOX THEATER TRIP!";
		SP_PlaceVictim (sp_b2, sp_dst_org + '0 0 20', 40);
		sp_next_t = time + 6.4;
	}
	else if (st == 14)
	{
		sp_label = "14/17  JAR O' GREEN GUYS -> 12-MAN SWARM!";
		SP_PlaceVictim (sp_b2, sp_dst_org + '24 0 20', 45);
		SP_PlaceVictim (sp_b3, sp_dst_org + '-28 24 20', 45);
		sp_next_t = time + 6.8;
	}
	else if (st == 15)
	{
		sp_label = "15/17  LOL.BAT DISK -> NET SEND ZAP!";
		SP_PlaceVictim (sp_b2, sp_dst_org + '0 0 20', 45);
		SP_PlaceVictim (sp_b3, sp_dst_org + '40 28 20', 45);
		sp_next_t = time + 6.6;
	}
	else if (st == 16)
	{
		sp_label = "16/17  CARGO VAN -> CLEAN GO-KART PAD FLIGHT";
		SP_PlaceVictim (sp_b2, sp_dst_org + '0 0 20', 40);
		sp_next_t = time + 6.0;
	}
	else if (st == 17)
	{
		sp_label = "FINALE: ALL PROJECTILES AT ONCE! CHAOS!!";
		SP_Face (sp_b1, sp_shoot_pos, sp_pad_org - '0 0 6');
		SP_Face (sp_b2, sp_shoot_pos + sp_shoot_right * 80, sp_pad_org - '0 0 6');
		SP_Face (sp_b3, sp_shoot_pos - sp_shoot_right * 80, sp_pad_org - '0 0 6');
		SP_Stock (sp_b2); SP_Stock (sp_b3);
		SP_PlaceVictim (sp_b4, SP_SkyRayPos (0.95), 999);
		sp_next_t = time + 8.5;
	}
};

void(float st) SP_FireStage =
{
	local entity oself, e;
	local vector org, dir;

	sp_fired = TRUE;
	oself = self;
	self = sp_b1;
	sp_b1.weapon = IT_ROCKET_LAUNCHER;
	makevectors (self.v_angle);
	dir = normalize ((sp_pad_org - '0 0 6') - (self.origin + '0 0 16'));
	org = self.origin + '0 0 16' + dir * 24;

	if (st == 1)
	{
		player_rocket1 ();
		W_FireRocket ();
		sp_proj = SP_FindNewest ("missile");
		if (sp_proj) { setorigin (sp_proj, org); sp_proj.velocity = dir * 1000; sp_proj.angles = vectoangles (sp_proj.velocity); }
	}
	else if (st == 2)
	{
		player_rocket1 ();
		W_FireGrenade ();
		sp_proj = SP_FindNewest ("grenade");
		if (sp_proj) sp_proj.velocity = normalize ((sp_pad_org + '0 0 12') - sp_proj.origin) * 650 + '0 0 80';
	}
	else if (st == 3)
	{
		player_rocket1 ();
		W_FireProximityGrenade ();
		sp_proj = SP_FindNewest ("proximity_grenade");
		if (sp_proj) sp_proj.velocity = normalize ((sp_pad_org + '0 0 12') - sp_proj.origin) * 650 + '0 0 80';
	}
	else if (st == 4)
	{
		player_nail1 ();
		self.weapon = IT_NAILGUN;
		self.button0 = TRUE;
		self.weapon = IT_NAILGUN;
		self.button0 = TRUE;
		W_FireSpikes (0);
		self.button0 = FALSE;
		self.weapon = IT_ROCKET_LAUNCHER;
		self.button0 = FALSE;
		self.weapon = IT_ROCKET_LAUNCHER;
		sp_proj = SP_FindNewest ("spike");
		if (sp_proj) { setorigin (sp_proj, sp_pad_org - dir * 36); sp_proj.velocity = dir * 1000; sp_proj.angles = vectoangles (sp_proj.velocity); }
	}
	else if (st == 5)
	{
		player_rocket1 ();
		HIP_LaunchLaser (org, dir, 0);
		sp_proj = SP_FindNewest ("hiplaser");
		if (sp_proj) { setorigin (sp_proj, sp_pad_org - dir * 36); sp_proj.velocity = dir * 1000; sp_proj.angles = vectoangles (sp_proj.velocity); }
	}
	else if (st == 6)
	{
		player_mm1 ();
		MegaMan_Launch ();
		sp_proj = SP_FindNewest ("megaman");
		if (sp_proj) sp_proj.velocity = normalize ((sp_pad_org + '0 0 12') - sp_proj.origin) * 620 + '0 0 90';
	}
	else if (st == 7)
	{
		player_mm1 ();
		KY_Launch (sp_b1, TRUE, sp_b2, 1.0);
		sp_proj = SP_FindNewest ("kyle_proj");
		if (sp_proj) { setorigin (sp_proj, sp_pad_org - dir * 18); sp_proj.velocity = dir * 680; sp_proj.angles = vectoangles (dir); }
	}
	else if (st == 8)
	{
		WC_Fire (0.85);
		sp_proj = SP_FindNewest ("wc_shot");
		if (sp_proj) { setorigin (sp_proj, sp_pad_org - dir * 18); sp_proj.wc_dir = normalize (dir); sp_proj.velocity = dir * 680; sp_proj.angles_y = vectoyaw (dir); }
	}
	else if (st == 9)
	{
		player_mm1 ();
		Milky_Launch ();
		sp_proj = SP_FindNewest ("milky");
	}
	else if (st == 10)
	{
		player_mm1 ();
		FD_Launch ();
		sp_proj = SP_FindNewest ("robdob");
		if (sp_proj) { setorigin (sp_proj, sp_pad_org - dir * 18); sp_proj.movedir = dir; sp_proj.velocity = dir * 720; sp_proj.angles = vectoangles (dir); }
	}
	else if (st == 11)
	{
		DK_Launch (0.90);
		sp_proj = SP_FindNewest ("dookie_shot");
		if (sp_proj) { sp_proj.velocity = dir * 900; sp_proj.angles = vectoangles (sp_proj.velocity); }
	}
	else if (st == 12)
	{
		Banana_Launch ();
		sp_proj = SP_FindNewest ("bigbanana");
		if (sp_proj) { sp_proj.velocity = dir * 900; sp_proj.angles = vectoangles (sp_proj.velocity); }
	}
	else if (st == 13)
	{
		Pk_Launch ();
		sp_proj = SP_FindNewest ("pickle");
		if (sp_proj) sp_proj.velocity = normalize ((sp_pad_org + '0 0 12') - sp_proj.origin) * 680 + '0 0 60';
	}
	else if (st == 14)
	{
		GJ_Launch ();
		sp_proj = SP_FindNewest ("greenjar_proj");
		if (sp_proj) sp_proj.velocity = normalize ((sp_pad_org + '0 0 12') - sp_proj.origin) * 680 + '0 0 60';
	}
	else if (st == 15)
	{
		NS_Throw ();
		sp_proj = SP_FindNewest ("netsend_disk");
		if (sp_proj) sp_proj.velocity = normalize ((sp_pad_org + '0 0 10') - sp_proj.origin) * 680 + '0 0 40';
	}
	else if (st == 16)
	{
		e = Veh_SpawnDynamic (VEH_VAN, sp_pad_org - sp_shoot_dir * 95 + '0 0 14', vectoyaw (sp_shoot_dir));
		if (e)
		{
			e.velocity = sp_shoot_dir * 650;
			e.veh_coast_until = time + 7.0;
			sp_proj = e;
		}
	}
	else if (st == 17)
	{
		// FINALE WAVE 1: EVERYONE SHOOTS EVERYTHING AT ONCE!
		sp_finale_burst = 1;
		player_rocket1 ();
		W_FireRocket ();
		W_FireGrenade ();
		W_FireProximityGrenade ();
		self.weapon = IT_NAILGUN;
		self.button0 = TRUE;
		W_FireSpikes (0);
		self.button0 = FALSE;
		self.weapon = IT_ROCKET_LAUNCHER;
		HIP_LaunchLaser (org, dir, 0);
		self.bulletspeed = 1600;
		launch_bullet (org, dir);
		MegaMan_Launch ();
		WC_Fire (0.9);
		DK_Launch (0.95);
		Banana_Launch ();
		Pk_Launch ();
		GJ_Launch ();
		NS_Throw ();
		LtGun_Launch (0, 1);

		self = sp_b2;
		makevectors (self.v_angle);
		dir = normalize ((sp_pad_org - '0 0 6') - (self.origin + '0 0 16'));
		org = self.origin + '0 0 16' + dir * 24;
		player_rocket1 ();
		W_FireRocket ();
		DK_Launch (0.95);
		Banana_Launch ();
		Milky_Launch ();
		KY_Launch (sp_b2, FALSE, world, 0.8);

		self = sp_b3;
		makevectors (self.v_angle);
		dir = normalize ((sp_pad_org - '0 0 6') - (self.origin + '0 0 16'));
		org = self.origin + '0 0 16' + dir * 24;
		player_rocket1 ();
		W_FireGrenade ();
		MegaMan_Launch ();
		WC_Fire (0.9);
		ShalMissile ();
		launch_homing_spikes (org, dir);
		launch_hknight2_homing (org, dir);
		newmis.solid = SOLID_BBOX; newmis.movetype = MOVETYPE_FLYMISSILE; newmis.velocity = dir * 650;
	}
	self = oself;
};

void() SP_VidThink =
{
	local entity e, pad, best_pad;
	local vector target, want_cam, vel_n, pull;
	local float is_launched, el, best_d, d;

	if (sp_done)
		return;

	if (!sp_started)
	{
		sp_host = find (world, classname, "player");
		while (sp_host && sp_host.ishuman != 1)
			sp_host = find (sp_host, classname, "player");
		if (sp_host == world) { self.nextthink = time + 0.05; return; }

		// Pick the Fox Theater SkyPad (-12429, 5519, 32) on bakersfielddowntown
		best_pad = world;
		best_d = 999999;
		pad = find (world, classname, "info_skypad");
		while (pad)
		{
			d = vlen (pad.origin - '-12429 5519 32');
			if (d < best_d) { best_d = d; best_pad = pad; }
			pad = find (pad, classname, "info_skypad");
		}
		if (best_pad == world) { self.nextthink = time + 0.05; return; }

		BotConnect (0, 0, 0);
		BotConnect (1, 0, 0);
		BotConnect (2, 0, 0);
		BotConnect (3, 0, 0);
		sp_b1 = world; sp_b2 = world; sp_b3 = world; sp_b4 = world;
		e = find (world, classname, "player");
		while (e)
		{
			if (e.ishuman != 1)
			{
				if (!sp_b1) sp_b1 = e;
				else if (!sp_b2) sp_b2 = e;
				else if (!sp_b3) sp_b3 = e;
				else if (!sp_b4) sp_b4 = e;
			}
			e = find (e, classname, "player");
		}
		if (!sp_b1 || !sp_b2 || !sp_b3 || !sp_b4) { self.nextthink = time + 0.05; return; }

		sp_pad = best_pad;
		sp_pad_org = best_pad.origin;
		sp_dst_org = best_pad.pos1;
		sp_pad_vel = SkyPad_CalcVel (sp_pad_org, sp_dst_org, best_pad.height);
		sp_pad_dir = sp_pad_vel;
		sp_pad_dir_z = 0;
		sp_pad_dir = normalize (sp_pad_dir);
		sp_pad_right_x = sp_pad_dir_y;
		sp_pad_right_y = 0 - sp_pad_dir_x;
		sp_pad_right_z = 0;

		// Pick an open street direction around sp_pad_org so shooter + camera are never inside a building!
		local float ang_i, ang_deg;
		local vector cand_dir, cand_pos, best_shoot;
		best_shoot = sp_pad_org + sp_pad_dir * 115 + '0 0 22';
		sp_shoot_dir = '0 0 0' - sp_pad_dir;
		ang_i = 0;
		while (ang_i < 8)
		{
			ang_deg = ang_i * 45;
			makevectors ('0 1 0' * ang_deg);
			cand_dir = v_forward;
			cand_pos = sp_pad_org - cand_dir * 115 + '0 0 4';
			tracebox (sp_pad_org + '0 0 16', '-24 -24 -12', '24 24 36', cand_pos + '0 0 16', TRUE, best_pad);
			if (trace_fraction == 1 && !trace_startsolid)
			{
				tracebox (cand_pos + '0 0 16', '-24 -24 -12', '24 24 36', cand_pos - cand_dir * 110 + '0 0 36', TRUE, best_pad);
				if (trace_fraction == 1 && !trace_startsolid)
				{
					best_shoot = cand_pos;
					sp_shoot_dir = cand_dir;
					break;
				}
			}
			ang_i = ang_i + 1;
		}
		sp_shoot_pos = best_shoot;
		sp_shoot_right_x = sp_shoot_dir_y;
		sp_shoot_right_y = 0 - sp_shoot_dir_x;
		sp_shoot_right_z = 0;

		sp_host.solid = SOLID_NOT;
		sp_host.movetype = MOVETYPE_NONE;
		sp_host.takedamage = DAMAGE_NO;
		sp_host.effects = sp_host.effects | EF_NODRAW;
		setorigin (sp_host, sp_shoot_pos + '0 0 40');

		sp_mon = spawn ();
		sp_mon.classname = "sp_vid_mon";

		sp_cam = spawn ();
		sp_cam.classname = "sp_vid_cam";
		sp_cam.movetype = MOVETYPE_NONE;
		sp_cam.solid = SOLID_NOT;
		setmodel (sp_cam, "progs/spike.mdl");
		sp_cam.alpha = 0.01;
		sp_cam.scale = 0.01;
		setsize (sp_cam, '0 0 0', '0 0 0');
		sp_cam_pos = sp_shoot_pos - sp_shoot_dir * 95 + sp_shoot_right * 72 + '0 0 42';
		setorigin (sp_cam, sp_cam_pos);
		sp_cam.angles = SP_Look (sp_cam_pos, sp_pad_org + '0 0 18');

		sp_host.angles = sp_cam.angles;
		sp_host.v_angle = sp_cam.angles;
		sp_host.fixangle = TRUE;
		sp_host.clientcamera = sp_cam;
		msg_entity = sp_host;
		WriteByte (MSG_ONE, 5);
		WriteEntity (MSG_ONE, sp_cam);

		sp_started = TRUE;
		sp_stage = 0;
		sp_next_t = time + 2.8;
		self.nextthink = time + 0.02;
		return;
	}

	if (sp_host)
	{
		sp_host.health = 999;
		sp_host.velocity = '0 0 0';
		sp_host.effects = sp_host.effects | EF_NODRAW;
	}
	if (sp_b1) { sp_b1.button0 = 0; sp_b1.movement = '0 0 0'; sp_b1.attack_finished = time + 999; }
	if (sp_b2) { sp_b2.button0 = 0; sp_b2.movement = '0 0 0'; sp_b2.attack_finished = time + 999; }
	if (sp_b3) { sp_b3.button0 = 0; sp_b3.movement = '0 0 0'; sp_b3.attack_finished = time + 999; }
	if (sp_b4) { sp_b4.button0 = 0; sp_b4.movement = '0 0 0'; sp_b4.attack_finished = time + 999; }

	// Advance stages (either on timeout, or 0.90s after projectile hits/explodes!)
	if (time >= sp_next_t || (sp_hit_t > 0 && time >= sp_hit_t + 0.90))
	{
		if (sp_stage >= 17)
		{
			sp_done = TRUE;
			localcmd ("cl_capturevideo 0\n");
			localcmd ("defer 0.5 quit\n");
			return;
		}
		sp_stage = sp_stage + 1;
		SP_SetupStage (sp_stage);
	}

	el = time - sp_stage_t;
	if (!sp_fired && el >= 0.45)
		SP_FireStage (sp_stage);

	// Finale extra chaos waves!
	if (sp_stage == 17 && sp_finale_burst == 1 && el >= 1.25)
	{
		sp_finale_burst = 2;
		local entity oself;
		oself = self; self = sp_b1;
		self.weapon = IT_NAILGUN;
		self.button0 = TRUE;
		W_FireSpikes (0);
		self.button0 = FALSE;
		self.weapon = IT_ROCKET_LAUNCHER; W_FireRocket (); WC_Fire (0.9); DK_Launch (0.95); GJ_Launch ();
		self = sp_b2;
		W_FireRocket (); Banana_Launch (); MegaMan_Launch (); FD_Launch ();
		self = sp_b3;
		W_FireGrenade (); Pk_Launch (); LtGun_Launch (0, 1);
		e = Veh_SpawnDynamic (VEH_VAN, sp_pad_org - sp_shoot_dir * 95 + '0 0 14', vectoyaw (sp_shoot_dir));
		if (e) { e.velocity = sp_shoot_dir * 720; e.veh_coast_until = time + 7.0; }
		self = oself;
	}
	if (sp_stage == 17 && sp_finale_burst == 2 && el >= 2.20)
	{
		sp_finale_burst = 3;
		local entity oself2;
		oself2 = self; self = sp_b1;
		W_FireRocket (); W_FireGrenade (); Banana_Launch (); DK_Launch (0.95);
		self = sp_b2;
		MegaMan_Launch (); GJ_Launch ();
		self = oself2;
	}

	// Keep drone/Milky pulled straight onto pad until launched
	if (sp_proj != world && !bm_wasfreed (sp_proj) && sp_proj.skypad_cool_t == 0)
	{
		if (sp_proj.classname == "robdob" || sp_proj.classname == "kyle_proj")
		{
			pull = normalize ((sp_pad_org + '0 0 12') - sp_proj.origin);
			sp_proj.velocity_x = pull_x * 680;
			sp_proj.velocity_y = pull_y * 680;
		}
		else if (sp_proj.classname == "milky" && sp_proj.milky_emerged)
		{
			sp_proj.velocity = normalize ((sp_pad_org + '0 0 12') - sp_proj.origin) * 680;
		}
	}

	// Detect projectile impact/pop to snap cleanly to next scene after 0.90s explosion hold
	if (sp_stage < 17 && sp_fired && sp_hit_t == 0)
	{
		if (sp_proj == world || bm_wasfreed (sp_proj) || sp_proj.solid == SOLID_NOT || sp_proj.pc_popped)
			sp_hit_t = time;
	}

	// Camera choreography
	if (sp_stage == 17)
	{
		// Dramatic wide chaos angle orbiting street/rooftop level so you see shooters, SkyPad eruption & sky storm!
		want_cam = sp_pad_org - sp_shoot_dir * 260 + sp_shoot_right * (160 - el * 24) + '0 0 140';
		target = sp_pad_org + sp_pad_dir * (80 + el * 65) + '0 0 160' + '0 0 1' * min (620, el * 95);
		traceline (sp_pad_org + '0 0 36', want_cam, TRUE, world);
		if (trace_fraction < 1)
			want_cam = trace_endpos + trace_plane_normal * 16;
		sp_cam_pos = sp_cam_pos + (want_cam - sp_cam_pos) * 0.16;
	}
	else if (!sp_fired || sp_proj == world || bm_wasfreed (sp_proj))
	{
		// Hold on player model shooting, or on explosion aftermath
		if (!sp_fired)
		{
			want_cam = sp_shoot_pos - sp_shoot_dir * 95 + sp_shoot_right * 72 + '0 0 42';
			target = sp_pad_org + '0 0 18';
		}
		else
		{
			want_cam = sp_cam_pos;
			target = sp_last_pos;
		}
		sp_cam_pos = sp_cam_pos + (want_cam - sp_cam_pos) * 0.25;
	}
	else
	{
		sp_last_pos = sp_proj.origin;
		is_launched = (sp_proj.skypad_cool_t > 0 || sp_proj.veh_pad_cool > 0);
		if (!is_launched)
		{
			// Watch player fire projectile into the glowing SkyPad!
			want_cam = sp_shoot_pos - sp_shoot_dir * 95 + sp_shoot_right * 72 + '0 0 42';
			target = sp_last_pos * 0.55 + sp_pad_org * 0.45;
			sp_cam_pos = sp_cam_pos + (want_cam - sp_cam_pos) * 0.25;
		}
		else
		{
			// Follow projectile in real time!
			vel_n = sp_proj.velocity;
			if (vlen (vel_n) > 20) vel_n = normalize (vel_n);
			else vel_n = sp_pad_dir;
			want_cam = sp_last_pos - vel_n * 110 + sp_pad_right * 44 + '0 0 28';
			if (sp_stage == 16 && sp_proj.classname == "misc_vehicle_van")
				want_cam = sp_last_pos - vel_n * 240 + sp_pad_right * 95 + '0 0 95';
			traceline (sp_last_pos, want_cam, TRUE, sp_proj);
			if (trace_fraction < 1)
				want_cam = trace_endpos + trace_plane_normal * 12;
			sp_cam_pos = sp_cam_pos + (want_cam - sp_cam_pos) * 0.34;
			target = sp_last_pos;
		}
	}

	setorigin (sp_cam, sp_cam_pos);
	sp_cam.angles = SP_Look (sp_cam_pos, target);
	if (sp_host)
	{
		sp_host.angles = sp_cam.angles;
		sp_host.v_angle = sp_cam.angles;
		sp_host.fixangle = TRUE;
		sp_host.clientcamera = sp_cam;
		msg_entity = sp_host;
		WriteByte (MSG_ONE, 5);
		WriteEntity (MSG_ONE, sp_cam);
		if (sp_label != "")
			centerprint (sp_host, sp_label);
	}

	self.nextthink = time + 0.02;
};

void() SP_VidStart =
{
	if (sp_dir)
		return;
	sp_dir = spawn ();
	sp_dir.classname = "sp_vid_director";
	sp_dir.think = SP_VidThink;
	sp_dir.nextthink = time + 0.25;
};
'''


def ensure_no_zircon(wait_s: float = 0.0) -> None:
    deadline = time.time() + wait_s
    while True:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process zircon* -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
            capture_output=True, text=True,
        )
        pids = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
        if not pids:
            return
        if time.time() >= deadline:
            sys.exit(f"ERROR: zircon already running (PIDs={pids})")
        time.sleep(0.5)


def compile_director() -> Path:
    print("[1/3] Compiling Bakersfield Downtown comedy director progs.dat...", flush=True)
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    qc_dir = BUILD_DIR / "qc"
    shutil.copytree(SRC_QC, qc_dir, ignore=shutil.ignore_patterns("*.dat", "*.log", "pre_tone_*"))
    (qc_dir / "sp_comedy_director.qc").write_text(DIRECTOR_QC, encoding="utf-8")

    wpath = qc_dir / "world.qc"
    wtxt = wpath.read_text(encoding="utf-8")
    wtxt = wtxt.replace("void() worldspawn =", "void() SP_VidPrecache;\nvoid() worldspawn =", 1)
    wtxt = wtxt.replace("void() StartFrame =", "void() SP_VidStart;\nvoid() StartFrame =", 1)
    wtxt = wtxt.replace("BotFrame();", "if (framecount == 5) SP_VidStart();\n\tBotFrame();", 1)
    wtxt = wtxt.replace('precache_model("progs/null.spr");', 'precache_model("progs/null.spr");\n\tSP_VidPrecache();', 1)
    wpath.write_text(wtxt, encoding="utf-8")

    ps_path = qc_dir / "progs.src"
    ps_path.write_text(ps_path.read_text(encoding="utf-8") + "\nsp_comedy_director.qc\n", encoding="utf-8")

    r = subprocess.run([str(FTEQCC), "-srcfile", "progs.src"], cwd=str(qc_dir), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        print(r.stdout.decode("utf-8", errors="replace")[-3000:])
        sys.exit("Director compile failed")
    out_dat = qc_dir / "progs.dat"
    assert out_dat.is_file()
    return out_dat


def capture_video() -> Path:
    ensure_no_zircon()
    progs_dat = compile_director()
    csprogs_dat = MOD / "csprogs.dat"

    shutil.rmtree(USERDIR, ignore_errors=True)
    ud_bk = USERDIR / "BakersfieldQuake"
    ud_bk.mkdir(parents=True, exist_ok=True)
    shutil.copy2(progs_dat, ud_bk / "progs.dat")
    shutil.copy2(csprogs_dat, ud_bk / "csprogs.dat")

    (ud_bk / "config.cfg").write_text(
        "unbindall\nvid_mouse 0\nm_pitch 0\nm_yaw 0\ncon_notify 0\n"
        "fov 95\nv_gamma 1.12\nr_hdr_scenebrightness 1.18\ncl_bob 0\ncrosshair 0\n"
        "r_drawviewmodel 0\nshowfps 0\nscr_centertime 2.5\n",
        encoding="ascii",
    )
    (ud_bk / "zz_cap.cfg").write_text(
        "developer 0\nseta menu_background 0\nseta bm_minimap 0\nbm_minimap 0\n"
        "con_notify 0\nset bm_botfill 0\nset crowd_on 0\nset bm_warmup 0\n"
        "deathmatch 1\ncoop 0\nsv_cheats 2\nviewsize 120\n"
        "crosshair 0\nr_drawviewmodel 0\nshowfps 0\n"
        "volume 0.85\nbgmvolume 0.12\n"
        "cl_capturevideo_ogg 0\ncl_capturevideo_fps 30\n"
        "cl_capturevideo_nameformat bako_skypad_comedy\n"
        "cl_capturevideo 1\n",
        encoding="ascii",
    )

    cmd = [
        str(ZIRCON), "-basedir", str(ROOT), "-userdir", str(USERDIR),
        "-port", "26098", "-window", "-width", "1280", "-height", "720",
        "-game", "quake15", "-game", "BakersfieldQuake",
        "-condebug", "+log_file", "zz_vid.log",
        "+vid_mouse", "0", "+m_pitch", "0", "+m_yaw", "0", "+bm_minimap", "0",
        "+sv_cheats", "2", "+deathmatch", "1", "+bm_botfill", "0", "+bm_warmup", "0",
        "+maxplayers", "6", "+stopdemo",
        "+map", "bakersfielddowntown",
        "+defer", "2.5", "exec zz_cap.cfg",
    ]
    print("[2/3] Launching Zircon on bakersfielddowntown to record AVI + audio...", flush=True)
    p = subprocess.Popen(cmd, cwd=str(ROOT))
    try:
        p.wait(timeout=360)
    except subprocess.TimeoutExpired:
        p.kill()
        sys.exit("Zircon timed out during capture")
    ensure_no_zircon(wait_s=15.0)

    vid_dir = ud_bk / "video"
    avis = sorted(vid_dir.glob("*.avi")) or sorted(ud_bk.glob("*.avi"))
    if not avis:
        logp = ud_bk / "zz_vid.log"
        tail = logp.read_text(errors="replace")[-2000:] if logp.is_file() else ""
        sys.exit(f"No captured AVI found!\n{tail}")
    avi = avis[0]
    dur = float(subprocess.check_output(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(avi)],
        text=True,
    ).strip())
    trim_start = 0.20
    keep_dur = max(5.0, dur - trim_start)
    fade_st = max(0.0, keep_dur - 0.7)
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    print(f"[3/3] Encoding {OUT_MP4} ({keep_dur:.1f}s)...", flush=True)
    subprocess.run([
        FFMPEG, "-y", "-ss", f"{trim_start:.2f}", "-i", str(avi),
        "-vf", f"fade=t=out:st={fade_st:.2f}:d=0.65,format=yuv420p",
        "-af", f"afade=t=out:st={fade_st:.2f}:d=0.65",
        "-c:v", "libx264", "-preset", "medium", "-crf", "24",
        "-maxrate", "3200k", "-bufsize", "4800k",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(OUT_MP4),
    ], check=True)
    sz = OUT_MP4.stat().st_size
    print(f"Encoded {OUT_MP4} ({sz/(1024*1024):.2f} MB, {keep_dur:.1f}s)")
    return OUT_MP4


def send_telegram(token: str) -> None:
    if not token:
        raise SystemExit("Missing TG_BOT_TOKEN")
    assert OUT_MP4.is_file(), f"Missing {OUT_MP4}"
    sz_mb = OUT_MP4.stat().st_size / (1024 * 1024)
    print(f"Sending {OUT_MP4.name} ({sz_mb:.2f} MB) to Telegram BAKOQUAKE...", flush=True)
    cap = (
        "Bakersfield Downtown SkyPad Projectile Comedy Showcase! "
        "Actual player models firing every projectile into the 21st & G SkyPad, "
        "real-time follow-cam to mid-air jetpack/John Bird ambushes & Fox Theater hits, "
        "plus an ALL-PROJECTILES-AT-ONCE chaos finale!"
    )
    proc = subprocess.run([
        "curl.exe", "-sS", "--max-time", "300",
        "-F", f"chat_id={TG_CHAT_ID}",
        "-F", f"caption={cap}",
        "-F", "supports_streaming=true",
        "-F", f"video=@{OUT_MP4};type=video/mp4",
        f"https://api.telegram.org/bot{token}/sendVideo",
    ], capture_output=True, text=True, check=True)
    res = json.loads(proc.stdout)
    print("sendVideo:", json.dumps({"ok": res.get("ok"), "message_id": res.get("result", {}).get("message_id")}))
    assert res.get("ok") is True, proc.stdout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", action="store_true")
    ap.add_argument("--telegram", action="store_true")
    ap.add_argument("--token", default=os.environ.get("TG_BOT_TOKEN", ""))
    args = ap.parse_args()
    if args.capture:
        capture_video()
    if args.telegram:
        send_telegram(args.token)


if __name__ == "__main__":
    main()
