#!/usr/bin/env python3
"""Capture a real-time follow-camera video in Zircon Engine demonstrating EVERY
projectile type hitting an info_skypad (plus Cargo Van go-kart flight), encode MP4,
and send it to Telegram BAKOQUAKE (-4993867752).

Usage:
    python source/mm_tools/build_skypad_demo_video.py --capture
    TG_BOT_TOKEN=... python source/mm_tools/build_skypad_demo_video.py --telegram
    TG_BOT_TOKEN=... python source/mm_tools/build_skypad_demo_video.py --all
"""
from __future__ import annotations

import argparse
import glob
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

OUT_ROOT = HERE / "out" / "skypad_video"
BUILD_DIR = OUT_ROOT / "build"
USERDIR = OUT_ROOT / "userdir"
OUT_MP4 = OUT_ROOT / "skypad_all_projectiles.mp4"

TG_CHAT_ID = "-4993867752"

DIRECTOR_QC = r'''
// Temporary choreographed real-time follow-cam director for SkyPad projectile video.
// Compiled ONLY into an isolated scratch progs.dat.
entity sp_vid_dir, sp_vid_cam, sp_vid_host, sp_vid_b1, sp_vid_b2, sp_vid_mon;
entity sp_vid_proj, sp_vid_jb, sp_vid_tank, sp_vid_ec;
float sp_vid_stage, sp_vid_next_t, sp_vid_stage_t, sp_vid_started, sp_vid_done;
vector sp_vid_pad, sp_vid_shoot, sp_vid_cam_pos, sp_vid_last_pos;
string sp_vid_label;

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

vector(vector from, vector to) SP_VidLook =
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

void(entity p, vector pos, vector target) SP_VidFace =
{
	local vector ang;
	setorigin (p, pos);
	p.velocity = '0 0 0';
	ang = SP_VidLook (pos + '0 0 18', target);
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

void() SP_ClearLeftovers =
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
			|| c == "greenjar_proj" || c == "greenguy_mini" || c == "netsend_disk"
			|| c == "netsend_pc" || c == "ltg_head" || c == "mm_tank_bar"
			|| c == "jb_bottle_proj" || c == "jb_aerosol_bomb" || c == "ShalrathMissile"
			|| c == "wizspike" || c == "hknight2_homing" || c == "Reiver_fireball"
			|| c == "ghost_follower" || c == "carniv_projectile" || c == "face"
			|| c == "jimrocket")
		{
			remove (e);
		}
		e = nx;
	}
	if (sp_vid_b1)
	{
		if (sp_vid_b1.fd_head) { remove (sp_vid_b1.fd_head); sp_vid_b1.fd_head = world; }
		if (sp_vid_b1.fd_cam) { remove (sp_vid_b1.fd_cam); sp_vid_b1.fd_cam = world; }
		FD_Restore (sp_vid_b1);
		sp_vid_b1.fd_fade = 0;
		sp_vid_b1.milky_active = world;
		if (sp_vid_b1.ky_cam) KY_CamDetach (sp_vid_b1);
		if (sp_vid_b1.ec_cannon_ent)
		{
			EC_RestoreViewAndBody (sp_vid_b1);
			sp_vid_b1.ec_cannon_ent = world;
		}
	}
	sp_vid_proj = world;
};

void(float st) SP_RunStage =
{
	local entity oself, m, e;
	local vector org, dir;

	SP_ClearLeftovers ();
	sp_vid_stage_t = time;
	sp_vid_cam_pos = sp_vid_pad + '-135 -125 85';

	// Keep shooter bot stocked & ready
	SP_VidFace (sp_vid_b1, sp_vid_shoot, sp_vid_pad + '0 0 12');
	sp_vid_b1.health = 999;
	sp_vid_b1.ammo_rockets = 99;
	sp_vid_b1.ammo_nails = 999;
	sp_vid_b1.ammo_cells = 999;
	sp_vid_b1.grenade_ammo = 99;
	sp_vid_b1.mm_ammo = 9;
	sp_vid_b1.bn_ammo = 9;
	FunGun_SetAmmo (sp_vid_b1, FG_WCANNON, 9);
	FunGun_SetAmmo (sp_vid_b1, FG_DOOKIE, 9);
	FunGun_SetAmmo (sp_vid_b1, FG_DOB, 9);
	FunGun_SetAmmo (sp_vid_b1, FG_PONG, 9);
	FunGun_SetAmmo (sp_vid_b1, FG_PICKLE, 9);
	FunGun_SetAmmo (sp_vid_b1, FG_NETSEND, 9);

	// Position target bot out along the open SE flight path for homing projectiles
	SP_VidFace (sp_vid_b2, sp_vid_pad + '560 -560 80', sp_vid_pad);
	sp_vid_b2.movetype = MOVETYPE_NONE;
	sp_vid_b2.health = 999;

	oself = self;
	self = sp_vid_b1;
	makevectors (self.v_angle);
	dir = normalize ((sp_vid_pad + '0 0 8') - (self.origin + '0 0 16'));
	org = self.origin + '0 0 16' + dir * 24;

	if (st == 1)
	{
		sp_vid_label = "1 / 25  ROCKET (missile)";
		W_FireRocket ();
		sp_vid_proj = SP_FindNewest ("missile");
		sp_vid_next_t = time + 2.2;
	}
	else if (st == 2)
	{
		sp_vid_label = "2 / 25  GRENADE (grenade)";
		SP_VidFace (sp_vid_b1, sp_vid_pad + '-115 0 24', sp_vid_pad + '0 0 28');
		W_FireGrenade ();
		sp_vid_proj = SP_FindNewest ("grenade");
		sp_vid_next_t = time + 2.6;
	}
	else if (st == 3)
	{
		sp_vid_label = "3 / 25  PROXIMITY GRENADE";
		SP_VidFace (sp_vid_b1, sp_vid_pad + '-115 0 24', sp_vid_pad + '0 0 28');
		W_FireProximityGrenade ();
		sp_vid_proj = SP_FindNewest ("proximity_grenade");
		sp_vid_next_t = time + 2.6;
	}
	else if (st == 4)
	{
		sp_vid_label = "4 / 25  NAILGUN SPIKE (spike)";
		W_FireSpikes (0);
		sp_vid_proj = SP_FindNewest ("spike");
		sp_vid_next_t = time + 2.0;
	}
	else if (st == 5)
	{
		sp_vid_label = "5 / 25  HIP LASER (hiplaser)";
		HIP_LaunchLaser (org, dir, 0);
		sp_vid_proj = SP_FindNewest ("hiplaser");
		sp_vid_next_t = time + 2.0;
	}
	else if (st == 6)
	{
		sp_vid_label = "6 / 25  ENFORCER SHOT (playershot)";
		self.bulletspeed = 1600;
		launch_bullet (org, dir);
		sp_vid_proj = SP_FindNewest ("playershot");
		sp_vid_next_t = time + 2.0;
	}
	else if (st == 7)
	{
		sp_vid_label = "7 / 25  MEGA MAN (megaman)";
		SP_VidFace (sp_vid_b1, sp_vid_pad + '-115 0 24', sp_vid_pad + '0 0 24');
		MegaMan_Launch ();
		sp_vid_proj = SP_FindNewest ("megaman");
		sp_vid_next_t = time + 2.8;
	}
	else if (st == 8)
	{
		sp_vid_label = "8 / 25  POCKET KYLE HOMING (0.75s fling!)";
		SP_VidFace (sp_vid_b1, sp_vid_pad + '-115 0 26', sp_vid_pad + '0 0 20');
		KY_Launch (sp_vid_b1, TRUE, sp_vid_b2, 1.0);
		sp_vid_proj = SP_FindNewest ("kyle_proj");
		if (sp_vid_proj) sp_vid_proj.velocity = normalize ((sp_vid_pad + '0 0 20') - sp_vid_proj.origin) * 650;
		sp_vid_next_t = time + 2.9;
	}
	else if (st == 9)
	{
		sp_vid_label = "9 / 25  WHEELMAN CANNON (wc_shot)";
		SP_VidFace (sp_vid_b1, sp_vid_pad + '-120 0 24', sp_vid_pad + '0 0 10');
		WC_Fire (0.85);
		sp_vid_proj = SP_FindNewest ("wc_shot");
		sp_vid_next_t = time + 2.8;
	}
	else if (st == 10)
	{
		sp_vid_label = "10 / 25  PINK LADY MILKY (0.75s fling!)";
		SP_VidFace (sp_vid_b1, sp_vid_pad + '-115 0 24', sp_vid_pad + '0 0 24');
		Milky_Launch ();
		sp_vid_proj = SP_FindNewest ("milky");
		sp_vid_next_t = time + 3.0;
	}
	else if (st == 11)
	{
		sp_vid_label = "11 / 25  ROB DOB DRONE (robdob)";
		SP_VidFace (sp_vid_b1, sp_vid_pad + '-115 0 24', sp_vid_pad + '0 0 18');
		FD_Launch ();
		sp_vid_proj = SP_FindNewest ("robdob");
		if (sp_vid_proj) sp_vid_proj.velocity = normalize ((sp_vid_pad + '0 0 18') - sp_vid_proj.origin) * 720;
		sp_vid_next_t = time + 2.8;
	}
	else if (st == 12)
	{
		sp_vid_label = "12 / 25  FLYING DOOKIE (dookie_shot)";
		DK_Launch (0.85);
		sp_vid_proj = SP_FindNewest ("dookie_shot");
		sp_vid_next_t = time + 2.3;
	}
	else if (st == 13)
	{
		sp_vid_label = "13 / 25  BANANA CANNON (bigbanana)";
		Banana_Launch ();
		sp_vid_proj = SP_FindNewest ("bigbanana");
		sp_vid_next_t = time + 2.3;
	}
	else if (st == 14)
	{
		sp_vid_label = "14 / 25  PICKLE SURPRISE (pickle)";
		SP_VidFace (sp_vid_b1, sp_vid_pad + '-115 0 24', sp_vid_pad + '0 0 24');
		Pk_Launch ();
		sp_vid_proj = SP_FindNewest ("pickle");
		sp_vid_next_t = time + 2.7;
	}
	else if (st == 15)
	{
		sp_vid_label = "15 / 25  JAR O' GREEN GUYS (greenjar_proj)";
		SP_VidFace (sp_vid_b1, sp_vid_pad + '-115 0 24', sp_vid_pad + '0 0 24');
		GJ_Launch ();
		sp_vid_proj = SP_FindNewest ("greenjar_proj");
		sp_vid_next_t = time + 2.7;
	}
	else if (st == 16)
	{
		sp_vid_label = "16 / 25  GREEN MINI GUY (greenguy_mini)";
		GJ_SpawnMini (sp_vid_pad + '-55 0 18', sp_vid_b1, 0);
		sp_vid_proj = SP_FindNewest ("greenguy_mini");
		if (sp_vid_proj)
		{
			sp_vid_proj.enemy = sp_vid_b2;
			sp_vid_proj.velocity = '420 0 140';
		}
		sp_vid_next_t = time + 2.8;
	}
	else if (st == 17)
	{
		sp_vid_label = "17 / 25  LOL.BAT DISK (netsend_disk)";
		SP_VidFace (sp_vid_b1, sp_vid_pad + '-115 0 24', sp_vid_pad + '0 0 24');
		NS_Throw ();
		sp_vid_proj = SP_FindNewest ("netsend_disk");
		sp_vid_next_t = time + 2.7;
	}
	else if (st == 18)
	{
		sp_vid_label = "18 / 25  LT GUN HEAD (ltg_head)";
		LtGun_Launch (0, 1);
		sp_vid_proj = SP_FindNewest ("ltg_head");
		sp_vid_next_t = time + 2.4;
	}
	else if (st == 19)
	{
		sp_vid_label = "19 / 25  TANK BAR SHELL (mm_tank_bar)";
		if (!sp_vid_tank)
		{
			sp_vid_tank = spawn ();
			setorigin (sp_vid_tank, sp_vid_shoot + '90 0 0');
			sp_vid_tank.angles_y = 180;
		}
		e = spawn ();
		e.classname = "mm_tank_bar";
		e.owner = sp_vid_tank;
		e.mmt_tank = sp_vid_tank;
		e.mmt_driver = sp_vid_b1;
		e.movetype = MOVETYPE_FLYMISSILE;
		e.solid = SOLID_BBOX;
		e.velocity = dir * 1650;
		e.angles = vectoangles (e.velocity);
		e.mmt_born = time;
		e.traileffectnum = mmt_fx_bar_trail;
		e.touch = MMT_BarTouch;
		e.think = MMT_BarThink;
		e.nextthink = time + 0.04;
		setmodel (e, "progs/mm_tank_bar.md3");
		setsize (e, '-12 -12 -12', '12 12 12');
		setorigin (e, org);
		sp_vid_proj = e;
		sp_vid_next_t = time + 2.2;
	}
	else if (st == 20)
	{
		sp_vid_label = "20 / 25  JOHN BIRD AEROSOL BOMB";
		if (!sp_vid_jb)
		{
			sp_vid_jb = spawn ();
			setorigin (sp_vid_jb, sp_vid_shoot + '0 0 24');
		}
		JB_LobAerosolBomb (sp_vid_jb, sp_vid_b1, org, dir);
		sp_vid_proj = SP_FindNewest ("jb_aerosol_bomb");
		sp_vid_next_t = time + 2.6;
	}
	else if (st == 21)
	{
		sp_vid_label = "21 / 25  SHALRATH HOMING POD";
		self = sp_vid_mon;
		setorigin (sp_vid_mon, sp_vid_shoot + '0 0 18');
		sp_vid_mon.enemy = sp_vid_b2;
		ShalMissile ();
		sp_vid_proj = SP_FindNewest ("ShalrathMissile");
		if (sp_vid_proj) sp_vid_proj.velocity = dir * 520;
		sp_vid_next_t = time + 2.5;
	}
	else if (st == 22)
	{
		sp_vid_label = "22 / 25  WIZARD HOMING SPIKE (wizspike)";
		self = sp_vid_mon;
		setorigin (sp_vid_mon, sp_vid_shoot + '0 0 18');
		sp_vid_mon.enemy = sp_vid_b2;
		launch_homing_spikes (org, dir);
		newmis.classname = "wizspike";
		setmodel (newmis, "progs/w_spike.mdl");
		newmis.velocity = dir * 650;
		sp_vid_proj = newmis;
		sp_vid_next_t = time + 2.3;
	}
	else if (st == 23)
	{
		sp_vid_label = "23 / 25  WARLORD HOMING FACE (hknight2_homing)";
		self = sp_vid_mon;
		setorigin (sp_vid_mon, sp_vid_shoot + '0 0 18');
		sp_vid_mon.enemy = sp_vid_b2;
		launch_hknight2_homing (org, dir);
		newmis.solid = SOLID_BBOX;
		newmis.movetype = MOVETYPE_FLYMISSILE;
		newmis.velocity = dir * 600;
		sp_vid_proj = newmis;
		sp_vid_next_t = time + 2.4;
	}
	else if (st == 24)
	{
		sp_vid_label = "24 / 25  REIVER FIREBALL & GHOST FOLLOWER";
		self = sp_vid_mon;
		setorigin (sp_vid_mon, sp_vid_shoot + '0 0 18');
		sp_vid_mon.enemy = sp_vid_b2;
		launch_ghost_follower (org, dir);
		newmis.velocity = dir * 580;
		sp_vid_proj = newmis;
		sp_vid_next_t = time + 2.4;
	}
	else if (st == 25)
	{
		sp_vid_label = "25 / 25  CARGO VAN (GO-KART PAD FLIGHT)";
		self = oself;
		e = Veh_SpawnDynamic (VEH_VAN, sp_vid_pad + '-95 0 20', 0);
		if (e)
		{
			e.velocity = '650 0 0';
			e.veh_coast_until = time + 6.0;
			sp_vid_proj = e;
		}
		sp_vid_next_t = time + 3.6;
		return;
	}
	self = oself;
};

void() SP_VidThink =
{
	local entity e, pad;
	local vector target, want_cam, vel_xy;
	local float is_launched;

	if (sp_vid_done)
		return;

	if (!sp_vid_started)
	{
		sp_vid_host = find (world, classname, "player");
		while (sp_vid_host && sp_vid_host.ishuman != 1)
			sp_vid_host = find (sp_vid_host, classname, "player");
		if (sp_vid_host == world)
		{
			self.nextthink = time + 0.05;
			return;
		}
		pad = find (world, classname, "info_skypad");
		if (find (pad, classname, "info_skypad") != world)
			pad = find (pad, classname, "info_skypad");
		if (pad == world)
		{
			self.nextthink = time + 0.05;
			return;
		}
		sp_vid_pad = pad.origin;
		sp_vid_shoot = sp_vid_pad + '-125 0 22';
		sp_vid_last_pos = sp_vid_pad + '0 0 18';

		BotConnect (0, 0, 0);
		BotConnect (1, 0, 0);
		sp_vid_b1 = world;
		sp_vid_b2 = world;
		e = find (world, classname, "player");
		while (e)
		{
			if (e.ishuman != 1)
			{
				if (!sp_vid_b1) sp_vid_b1 = e;
				else if (!sp_vid_b2) sp_vid_b2 = e;
			}
			e = find (e, classname, "player");
		}
		if (!sp_vid_b1 || !sp_vid_b2)
		{
			self.nextthink = time + 0.05;
			return;
		}

		sp_vid_host.solid = SOLID_NOT;
		sp_vid_host.movetype = MOVETYPE_NONE;
		sp_vid_host.takedamage = DAMAGE_NO;
		sp_vid_host.effects = sp_vid_host.effects | EF_NODRAW;
		setorigin (sp_vid_host, sp_vid_pad + '-135 -125 85');

		sp_vid_mon = spawn ();
		sp_vid_mon.classname = "sp_vid_mon";

		sp_vid_cam = spawn ();
		sp_vid_cam.classname = "sp_vid_cam";
		sp_vid_cam.movetype = MOVETYPE_NONE;
		sp_vid_cam.solid = SOLID_NOT;
		setmodel (sp_vid_cam, "progs/spike.mdl");
		sp_vid_cam.alpha = 0.01;
		sp_vid_cam.scale = 0.01;
		setsize (sp_vid_cam, '0 0 0', '0 0 0');
		sp_vid_cam_pos = sp_vid_pad + '-135 -125 85';
		setorigin (sp_vid_cam, sp_vid_cam_pos);
		sp_vid_cam.angles = SP_VidLook (sp_vid_cam_pos, sp_vid_pad + '0 0 18');

		sp_vid_host.angles = sp_vid_cam.angles;
		sp_vid_host.v_angle = sp_vid_cam.angles;
		sp_vid_host.fixangle = TRUE;
		sp_vid_host.clientcamera = sp_vid_cam;
		msg_entity = sp_vid_host;
		WriteByte (MSG_ONE, 5);
		WriteEntity (MSG_ONE, sp_vid_cam);

		sp_vid_started = TRUE;
		sp_vid_stage = 0;
		sp_vid_next_t = time + 2.85;
		self.nextthink = time + 0.02;
		return;
	}

	if (sp_vid_host)
	{
		sp_vid_host.health = 999;
		sp_vid_host.velocity = '0 0 0';
		sp_vid_host.effects = sp_vid_host.effects | EF_NODRAW;
	}
	if (sp_vid_b1)
	{
		sp_vid_b1.health = 999;
		sp_vid_b1.button0 = 0;
		sp_vid_b1.button2 = 0;
		sp_vid_b1.movement = '0 0 0';
		sp_vid_b1.attack_finished = time + 999;
	}
	if (sp_vid_b2)
	{
		sp_vid_b2.health = 999;
		sp_vid_b2.button0 = 0;
		sp_vid_b2.button2 = 0;
		sp_vid_b2.movement = '0 0 0';
		sp_vid_b2.attack_finished = time + 999;
		SP_VidFace (sp_vid_b2, sp_vid_pad + '560 -560 80', sp_vid_pad);
	}

	if (time >= sp_vid_next_t)
	{
		if (sp_vid_stage >= 25)
		{
			sp_vid_done = TRUE;
			localcmd ("cl_capturevideo 0\n");
			localcmd ("defer 0.5 quit\n");
			return;
		}
		sp_vid_stage = sp_vid_stage + 1;
		SP_RunStage (sp_vid_stage);
	}

	// Keep Rob Dob & Milky steering toward the SkyPad until launched
	if (sp_vid_proj != world && !bm_wasfreed (sp_vid_proj) && sp_vid_proj.skypad_cool_t == 0)
	{
		if (sp_vid_proj.classname == "robdob" || sp_vid_proj.classname == "kyle_proj" || sp_vid_proj.classname == "greenguy_mini")
		{
			local vector pull;
			pull = normalize ((sp_vid_pad + '0 0 12') - sp_vid_proj.origin);
			sp_vid_proj.velocity_x = pull_x * 680;
			sp_vid_proj.velocity_y = pull_y * 680;
		}
		else if (sp_vid_proj.classname == "milky" && sp_vid_proj.milky_emerged)
		{
			sp_vid_proj.velocity = normalize ((sp_vid_pad + '0 0 12') - sp_vid_proj.origin) * 680;
		}
	}

	// Real-time follow camera!
	if (sp_vid_proj != world && !bm_wasfreed (sp_vid_proj))
	{
		sp_vid_last_pos = sp_vid_proj.origin;
		is_launched = (sp_vid_proj.skypad_cool_t > 0 || sp_vid_proj.veh_pad_cool > 0);
		if (is_launched)
		{
			vel_xy = sp_vid_proj.velocity;
			if (vlen (vel_xy) > 20)
				vel_xy = normalize (vel_xy);
			else
				vel_xy = '0.5 -0.5 0.7';
			want_cam = sp_vid_last_pos - vel_xy * 115 + '-48 -48 34';
			if (sp_vid_stage == 25)
				want_cam = sp_vid_last_pos - vel_xy * 210 + '-65 -65 68';
			traceline (sp_vid_last_pos, want_cam, TRUE, sp_vid_proj);
			if (trace_fraction < 1)
				want_cam = trace_endpos + trace_plane_normal * 12;
			sp_vid_cam_pos = sp_vid_cam_pos + (want_cam - sp_vid_cam_pos) * 0.35;
		}
		else
		{
			want_cam = sp_vid_pad + '-135 -125 85';
			sp_vid_cam_pos = sp_vid_cam_pos + (want_cam - sp_vid_cam_pos) * 0.30;
		}
		target = sp_vid_last_pos;
	}
	else
	{
		target = sp_vid_last_pos;
	}

	setorigin (sp_vid_cam, sp_vid_cam_pos);
	sp_vid_cam.angles = SP_VidLook (sp_vid_cam_pos, target);
	if (sp_vid_host)
	{
		sp_vid_host.angles = sp_vid_cam.angles;
		sp_vid_host.v_angle = sp_vid_cam.angles;
		sp_vid_host.fixangle = TRUE;
		sp_vid_host.clientcamera = sp_vid_cam;
		msg_entity = sp_vid_host;
		WriteByte (MSG_ONE, 5);
		WriteEntity (MSG_ONE, sp_vid_cam);
		if (sp_vid_label != "")
			centerprint (sp_vid_host, sp_vid_label);
	}

	self.nextthink = time + 0.02;
};

void() SP_VidStart =
{
	if (sp_vid_dir)
		return;
	sp_vid_dir = spawn ();
	sp_vid_dir.classname = "sp_vid_director";
	sp_vid_dir.think = SP_VidThink;
	sp_vid_dir.nextthink = time + 0.25;
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
    print("[1/3] Compiling isolated SkyPad video director progs.dat...", flush=True)
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    qc_dir = BUILD_DIR / "qc"
    shutil.copytree(SRC_QC, qc_dir, ignore=shutil.ignore_patterns("*.dat", "*.log", "pre_tone_*"))
    (qc_dir / "sp_vid_director.qc").write_text(DIRECTOR_QC, encoding="utf-8")

    wpath = qc_dir / "world.qc"
    wtxt = wpath.read_text(encoding="utf-8")
    wtxt = wtxt.replace("void() worldspawn =", "void() SP_VidPrecache;\nvoid() worldspawn =", 1)
    wtxt = wtxt.replace("void() StartFrame =", "void() SP_VidStart;\nvoid() StartFrame =", 1)
    wtxt = wtxt.replace("BotFrame();", "if (framecount == 5) SP_VidStart();\n\tBotFrame();", 1)
    wtxt = wtxt.replace('precache_model("progs/null.spr");', 'precache_model("progs/null.spr");\n\tSP_VidPrecache();', 1)
    wpath.write_text(wtxt, encoding="utf-8")

    ps_path = qc_dir / "progs.src"
    ps_path.write_text(ps_path.read_text(encoding="utf-8") + "\nsp_vid_director.qc\n", encoding="utf-8")

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
        "unbindall\nvid_mouse 0\nm_pitch 0\nm_yaw 0\ncon_notify 4\ncon_notifytime 3\n"
        "fov 95\nv_gamma 1.12\nr_hdr_scenebrightness 1.18\ncl_bob 0\ncrosshair 0\n"
        "r_drawviewmodel 0\nshowfps 0\nscr_centertime 2.5\n",
        encoding="ascii",
    )
    (ud_bk / "zz_cap.cfg").write_text(
        "developer 0\nseta menu_background 0\nseta bm_minimap 0\nbm_minimap 0\n"
        "con_notify 0\n"
        "set bm_botfill 0\nset crowd_on 0\nset bm_warmup 0\n"
        "deathmatch 1\ncoop 0\nsv_cheats 2\nviewsize 120\n"
        "crosshair 0\nr_drawviewmodel 0\nshowfps 0\n"
        "volume 0.85\nbgmvolume 0.12\n"
        "cl_capturevideo_ogg 0\ncl_capturevideo_fps 30\n"
        "cl_capturevideo_nameformat skypad_all_proj\n"
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
        "+maxplayers", "4", "+stopdemo",
        "+map", "soicowboy_bkk",
        "+defer", "2.5", "exec zz_cap.cfg",
    ]
    print("[2/3] Launching Zircon to record real-time follow-cam AVI + audio...", flush=True)
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
        "Real-time follow-cam demo of EVERY projectile hitting the info_skypad "
        "(Rocket, Grenade, Proximity, Nail, Laser, Enforcer, Mega Man, Kyle Homing, "
        "Wheelman, Milky, Rob Dob, Dookie, Banana, Pickle, Green Jar, Green Mini, "
        "LOL.BAT Disk, LT Gun, Tank Bar, John Bird Bomb, Monster Projectiles, plus Cargo Van go-kart flight)."
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
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--token", default=os.environ.get("TG_BOT_TOKEN", ""))
    args = ap.parse_args()
    if args.all or args.capture:
        capture_video()
    if args.all or args.telegram:
        send_telegram(args.token)


if __name__ == "__main__":
    main()
