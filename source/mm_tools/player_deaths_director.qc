/*
player_deaths_director.qc — Downtown Bakersfield 3rd-person 360 Death Showcase
Runs on maps/bakersfielddowntown.bsp (~26.5s) around H St & 20th St (Fox Theater):
  Six fast-paced multiplayer duels between classic Quake Rangers (progs/player_id1.mdl),
  each ending in one of the 6 new smooth death animations + classic gibs + map slide,
  while the 3rd-person camera sweeps 360+ degrees around the street action.
*/

entity	pdv_dir;
entity	pdv_cam;
entity	pdv_bgm;
entity	pdv_hero;
entity	pdv_foe;
entity	pdv_proj;

float	pdv_t0;
float	pdv_stage;
float	pdv_sub;
float	pdv_cam_fixed;
float	pdv_stopped;
float	pdv_quitted;
float	pdv_floor_z;
float	pdv_death_t;
float	pdv_gib_mask;
vector	pdv_slide_vel;
vector	pdv_cam_pos;
vector	pdv_cam_ang;
vector	pdv_focus_pos;

float(float u) PDV_Clamp01 = { if (u < 0) return 0; if (u > 1) return 1; return u; };
float(float u) PDV_Smooth = { u = PDV_Clamp01(u); return u * u * (3 - 2 * u); };
float(float x) PDV_Sin = { local float r; r = sin(x); return r; };
float(float x) PDV_Cos = { local float r; r = cos(x); return r; };

vector(vector from, vector to) PDV_Look =
{
	local vector a;
	local float px;
	a = vectoangles(to - from);
	px = a_x;
	if (px > 180) px = px - 360;
	a_x = 0 - px;
	a_z = 0;
	return a;
};

float(vector xy) PDV_FloorZ =
{
	local vector p0, p1;
	p0 = xy; p0_z = 96;
	p1 = xy; p1_z = -96;
	traceline(p0, p1, TRUE, world);
	if (trace_fraction < 1)
		return trace_endpos_z;
	return 2;
};

void(float t) PDV_EvalCam =
{
	local float ang, rad, cz, fz;
	local vector look, cpos;

	fz = pdv_floor_z;
	// Continuous sweeping 360+ degree 3rd-person orbital camera around the street fight
	// 0..20s: full 360 deg orbit tracking the active duel/victim center
	// 20..26.2s: tighter 360 deg hero-and-carnage victory orbit
	if (t < 20.0)
	{
		ang = (40.0 + (t / 20.0) * 360.0) * 0.0174533;
		rad = 84.0;
		cz = fz + 44.0 + PDV_Sin(t * 0.8) * 5.0;
	}
	else
	{
		ang = (40.0 + ((t - 20.0) / 6.2) * 360.0) * 0.0174533;
		rad = 74.0;
		cz = fz + 38.0;
	}

	look = pdv_focus_pos;
	cpos_x = look_x + PDV_Cos(ang) * rad;
	cpos_y = look_y + PDV_Sin(ang) * rad;
	cpos_z = cz;

	pdv_cam_pos = cpos;
	pdv_cam_ang = PDV_Look(cpos, look + '0 0 8');
};

void() PDV_Precache =
{
	precache_model("progs/player_id1.mdl");
	precache_model("progs/h_player_id1.mdl");
	precache_model("progs/gib_id1_arm_l.mdl");
	precache_model("progs/gib_id1_arm_r.mdl");
	precache_model("progs/gib_id1_leg_l.mdl");
	precache_model("progs/gib_id1_leg_r.mdl");
	precache_model("progs/missile.mdl");
	precache_model("progs/spike.mdl");
	precache_sound("weapons/sgun1.wav");
	precache_sound("weapons/rocket1i.wav");
	precache_sound("weapons/r_exp3.wav");
	precache_sound("weapons/lhit.wav");
	precache_sound("player/death1.wav");
	precache_sound("player/death2.wav");
	precache_sound("player/death3.wav");
	precache_sound("player/death4.wav");
	precache_sound("player/death5.wav");
	precache_sound("player/gib.wav");
	precache_sound("misc/corpsegib.wav");
};

void() PDV_CleanStage =
{
	local entity e, nxt;
	e = nextent(world);
	while (e)
	{
		nxt = nextent(e);
		if (e != pdv_dir && e != pdv_cam && e != pdv_bgm && e != pdv_hero && e != pdv_foe
		 && e.classname != "player" && e.solid != SOLID_BSP)
		{
			if (e.classname == "npc_crowd" || substring(e.classname, 0, 12) == "misc_vehicle"
			 || e.classname == "misc_gokart" || (e.flags & FL_ITEM))
				remove(e);
		}
		e = nxt;
	}
};

void(entity p) PDV_EnsureCam =
{
	if (!pdv_cam)
	{
		pdv_cam = spawn();
		pdv_cam.classname = "pdv_camera";
		pdv_cam.movetype = MOVETYPE_NONE;
		pdv_cam.solid = SOLID_NOT;
		setmodel(pdv_cam, "progs/spike.mdl");
		pdv_cam.scale = 0.01;
		pdv_cam.alpha = 0.01;
		setsize(pdv_cam, '0 0 0', '0 0 0');
		setorigin(pdv_cam, pdv_cam_pos);
	}
	if (!pdv_bgm)
	{
		pdv_bgm = spawn();
		pdv_bgm.classname = "pdv_bgm";
		pdv_bgm.movetype = MOVETYPE_NONE;
		pdv_bgm.solid = SOLID_NOT;
		setmodel(pdv_bgm, "progs/spike.mdl");
		pdv_bgm.scale = 0.01;
		pdv_bgm.alpha = 0.01;
		setsize(pdv_bgm, '0 0 0', '0 0 0');
		setorigin(pdv_bgm, pdv_cam_pos);
	}
	if (p.clientcamera != pdv_cam)
	{
		p.clientcamera = pdv_cam;
		msg_entity = p;
		WriteByte(MSG_ONE, 5);
		WriteEntity(MSG_ONE, pdv_cam);
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
	setorigin(self, pdv_cam_pos - self.view_ofs);
	self.angles = pdv_cam_ang;
	self.v_angle = pdv_cam_ang;
	return TRUE;
};

void(entity p) Showcase_SyncPlayer =
{
	if (!p) return;
	PDV_EnsureCam(p);
	setorigin(pdv_cam, pdv_cam_pos);
	pdv_cam.angles = pdv_cam_ang;
	if (pdv_bgm) setorigin(pdv_bgm, pdv_cam_pos);
	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.takedamage = DAMAGE_NO;
	p.flags = p.flags | FL_NOTARGET;
	p.model = "";
	p.modelindex = 0;
	p.weaponmodel = "";
	p.alpha = 0.01;
	p.effects = EF_NODRAW;
	setorigin(p, pdv_cam_pos - p.view_ofs);
	p.angles = pdv_cam_ang;
	p.v_angle = pdv_cam_ang;
	if (!pdv_cam_fixed) { pdv_cam_fixed = TRUE; p.fixangle = TRUE; }
};

void() PDV_GibFade = { remove(self); };

void(entity src, string mdl, vector lofs, vector lvel) PDV_SpawnGib =
{
	local entity g;
	makevectors(src.angles);
	g = spawn();
	g.origin = src.origin + (v_forward * lofs_x) + (v_right * (-lofs_y)) + ('0 0 1' * lofs_z);
	setmodel(g, mdl);
	setsize(g, '-6 -6 -6', '6 6 6');
	g.movetype = MOVETYPE_BOUNCE;
	g.solid = SOLID_NOT;
	g.velocity = (v_forward * lvel_x) + (v_right * (-lvel_y)) + ('0 0 1' * lvel_z);
	g.avelocity = crandom() * '480 480 480';
	g.colormap = src.colormap;
	g.traileffectnum = particleeffectnum("TR_BLOOD");
	g.think = PDV_GibFade;
	g.nextthink = time + 4.5;
};

void(float cmap, vector pos, float yaw_deg) PDV_SpawnFoe =
{
	if (pdv_foe && pdv_foe != world)
	{
		// Leave previous dead body frozen on the street for carnage!
		pdv_foe.movetype = MOVETYPE_NONE;
		pdv_foe.think = SUB_Null;
	}
	pdv_foe = spawn();
	pdv_foe.classname = "pdv_foe";
	pdv_foe.movetype = MOVETYPE_STEP;
	pdv_foe.solid = SOLID_NOT;
	setmodel(pdv_foe, "progs/player_id1.mdl");
	setsize(pdv_foe, VEC_HULL_MIN, VEC_HULL_MAX);
	pos_z = PDV_FloorZ(pos) + 25;
	setorigin(pdv_foe, pos);
	pdv_foe.angles = '0 0 0';
	pdv_foe.angles_y = yaw_deg;
	pdv_foe.colormap = cmap;
	pdv_foe.colormod = '1.22 1.22 1.22';
	pdv_foe.frame = 6;
};

void(float death_idx) PDV_TriggerDeath =
{
	local vector dir;
	pdv_death_t = time;
	pdv_gib_mask = 0;
	pdv_slide_vel = '0 0 0';

	dir = pdv_foe.origin - pdv_hero.origin;
	dir_z = 0;
	if (vlen(dir) < 1) dir = '0 -1 0';
	dir = normalize(dir);
	pdv_foe.angles_y = vectoyaw(-dir);
	pdv_foe.movetype = MOVETYPE_TOSS;
	pdv_foe.flags = pdv_foe.flags - (pdv_foe.flags & FL_ONGROUND);

	// Explosion / impact VFX + death sound
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord(MSG_BROADCAST, pdv_foe.origin_x);
	WriteCoord(MSG_BROADCAST, pdv_foe.origin_y);
	WriteCoord(MSG_BROADCAST, pdv_foe.origin_z + 10);

	if (death_idx == 1)
	{
		sound(pdv_foe, CHAN_VOICE, "player/death1.wav", 1, ATTN_NORM);
		pdv_foe.velocity = dir * 185 + '0 0 265';
		pdv_foe.frame = PD_KO_SPIN_START;
	}
	else if (death_idx == 2)
	{
		sound(pdv_foe, CHAN_VOICE, "player/death2.wav", 1, ATTN_NORM);
		pdv_slide_vel = dir * 560;
		pdv_foe.velocity = dir * 560 + '0 0 185';
		pdv_foe.frame = PD_GUT_SLIDE_START;
	}
	else if (death_idx == 3)
	{
		sound(pdv_foe, CHAN_VOICE, "player/death3.wav", 1, ATTN_NORM);
		pdv_gib_mask = 3;
		pdv_foe.velocity = dir * 50 + '0 0 105';
		pdv_foe.frame = PD_LIMBS_OFF_START;
	}
	else if (death_idx == 4)
	{
		sound(pdv_foe, CHAN_VOICE, "player/death4.wav", 1, ATTN_NORM);
		pdv_gib_mask = 4;
		pdv_foe.velocity = dir * 35 + '0 0 55';
		pdv_foe.frame = PD_HEAD_OFF_START;
	}
	else if (death_idx == 5)
	{
		sound(pdv_foe, CHAN_VOICE, "player/death5.wav", 1, ATTN_NORM);
		pdv_foe.velocity = dir * 215 + '0 0 315';
		pdv_foe.frame = PD_BACKFLIP_START;
	}
	else
	{
		sound(pdv_foe, CHAN_VOICE, "player/death2.wav", 1, ATTN_NORM);
		pdv_foe.velocity = dir * 20;
		pdv_foe.frame = PD_SPASM_START;
	}
};

void(float death_idx, float dt) PDV_StepDeath =
{
	local float f0, f1, fr;

	if (death_idx == 1) { f0 = PD_KO_SPIN_START; f1 = PD_KO_SPIN_END; }
	else if (death_idx == 2) { f0 = PD_GUT_SLIDE_START; f1 = PD_GUT_SLIDE_END; }
	else if (death_idx == 3) { f0 = PD_LIMBS_OFF_START; f1 = PD_LIMBS_OFF_END; }
	else if (death_idx == 4) { f0 = PD_HEAD_OFF_START; f1 = PD_HEAD_OFF_END; }
	else if (death_idx == 5) { f0 = PD_BACKFLIP_START; f1 = PD_BACKFLIP_END; }
	else { f0 = PD_SPASM_START; f1 = PD_SPASM_END; }

	fr = f0 + floor(dt * 20.0);
	if (fr > f1) fr = f1;
	pdv_foe.frame = fr;

	if (death_idx == 3)
	{
		if ((pdv_gib_mask & 1) && fr >= PD_LIMBS_OFF_GIB_ARM_F)
		{
			pdv_gib_mask = pdv_gib_mask - 1;
			PDV_SpawnGib(pdv_foe, "progs/gib_id1_arm_l.mdl", '-2 9 12', '45 140 210');
			PDV_SpawnGib(pdv_foe, "progs/gib_id1_arm_r.mdl", '-2 -9 12', '-35 -145 220');
			sound(pdv_foe, CHAN_AUTO, "misc/corpsegib.wav", 1, ATTN_NORM);
		}
		if ((pdv_gib_mask & 2) && fr >= PD_LIMBS_OFF_GIB_LEG_F)
		{
			pdv_gib_mask = pdv_gib_mask - 2;
			PDV_SpawnGib(pdv_foe, "progs/gib_id1_leg_l.mdl", '2 5 -10', '115 90 175');
			PDV_SpawnGib(pdv_foe, "progs/gib_id1_leg_r.mdl", '-2 -5 -10', '-110 -85 185');
			sound(pdv_foe, CHAN_AUTO, "player/gib.wav", 1, ATTN_NORM);
		}
	}
	else if (death_idx == 4)
	{
		if ((pdv_gib_mask & 4) && fr >= (PD_HEAD_OFF_START + 1))
		{
			pdv_gib_mask = pdv_gib_mask - 4;
			PDV_SpawnGib(pdv_foe, "progs/h_player_id1.mdl", '0 0 22', '35 20 275');
			pointparticles(particleeffectnum("blood_spurt"), pdv_foe.origin + '0 0 22', '0 0 120', 1);
			sound(pdv_foe, CHAN_AUTO, "misc/corpsegib.wav", 1, ATTN_NORM);
		}
	}
	else if (death_idx == 2)
	{
		if (dt >= 0.45 && vlen(pdv_slide_vel) > 25)
		{
			pdv_foe.flags = pdv_foe.flags - (pdv_foe.flags & FL_ONGROUND);
			pdv_foe.velocity_x = pdv_slide_vel_x;
			pdv_foe.velocity_y = pdv_slide_vel_y;
			if (pdv_foe.velocity_z < -35) pdv_foe.velocity_z = -35;
			pdv_slide_vel = pdv_slide_vel * 0.94;
		}
	}
};

void() PDV_DirectorTick =
{
	local entity p;
	local float t, st, local_t, fr, fa;
	local vector hpos, fpos, dir;

	self.nextthink = time + 0.02;
	p = find(world, classname, "player");
	if (!p) return;

	if (pdv_t0 == 0)
	{
		pdv_t0 = time;
		PDV_CleanStage();
		pdv_floor_z = PDV_FloorZ('-8855 2320 0');
		pdv_hero = spawn();
		pdv_hero.classname = "pdv_hero";
		pdv_hero.movetype = MOVETYPE_NONE;
		pdv_hero.solid = SOLID_NOT;
		setmodel(pdv_hero, "progs/player_id1.mdl");
		setsize(pdv_hero, VEC_HULL_MIN, VEC_HULL_MAX);
		pdv_hero.colormap = 5; // Classic Red/Brown Hero
		pdv_hero.colormod = '1.25 1.25 1.25';
		setorigin(pdv_hero, '-8855 2360 26');
		pdv_focus_pos = pdv_hero.origin;
	}

	t = time - pdv_t0;

	// Determine active stage 1..6 (3.8s..4.2s each -> 0..23s, then 23..26.2s victory orbit)
	if (t < 3.6)      { st = 1; local_t = t; }
	else if (t < 7.8) { st = 2; local_t = t - 3.6; }
	else if (t < 11.4){ st = 3; local_t = t - 7.8; }
	else if (t < 15.0){ st = 4; local_t = t - 11.4; }
	else if (t < 18.8){ st = 5; local_t = t - 15.0; }
	else if (t < 23.0){ st = 6; local_t = t - 18.8; }
	else              { st = 7; local_t = t - 23.0; }

	if (st != pdv_stage)
	{
		pdv_stage = st;
		pdv_sub = 0;
		if (st == 1)      PDV_SpawnFoe(14, '-8840 2410 0', 270);
		else if (st == 2) PDV_SpawnFoe(4,  '-8855 2420 0', 270);
		else if (st == 3) PDV_SpawnFoe(12, '-8815 2360 0', 180);
		else if (st == 4) PDV_SpawnFoe(10, '-8895 2340 0', 0);
		else if (st == 5) PDV_SpawnFoe(8,  '-8845 2415 0', 270);
		else if (st == 6) PDV_SpawnFoe(7,  '-8885 2405 0', 300);
	}

	// Hero circles/strafes slightly around Fox Theater intersection (-8855, 2340)
	hpos_x = -8855 + PDV_Sin(t * 1.4) * 18;
	hpos_y = 2350 + PDV_Cos(t * 1.1) * 14;
	hpos_z = PDV_FloorZ(hpos) + 25;
	setorigin(pdv_hero, hpos);

	if (st <= 6)
	{
		if (local_t < 1.1)
		{
			// Active fight phase: both Rangers strafe and trade shots!
			fpos = pdv_foe.origin;
			if (st == 2) fpos_x = -8855 + PDV_Sin(t * 4.0) * 12;
			else         fpos_x = fpos_x + PDV_Sin(t * 5.0) * 1.2;
			fpos_z = PDV_FloorZ(fpos) + 25;
			setorigin(pdv_foe, fpos);

			dir = pdv_foe.origin - pdv_hero.origin;
			pdv_hero.angles_y = vectoyaw(dir);
			pdv_foe.angles_y = vectoyaw(-dir);

			fr = floor(t * 12.0);
			pdv_hero.frame = 6 + (fr - 6 * floor(fr / 6));
			pdv_foe.frame = 6 + (fr - 6 * floor(fr / 6));

			if (local_t >= 0.45 && pdv_sub < 1)
			{
				pdv_sub = 1;
				pdv_foe.frame = 113; // shotatt1
				sound(pdv_foe, CHAN_WEAPON, "weapons/sgun1.wav", 0.8, ATTN_NORM);
			}
			if (local_t >= 0.95 && pdv_sub < 2)
			{
				pdv_sub = 2;
				pdv_hero.frame = 107; // rockatt1
				pdv_hero.effects = EF_MUZZLEFLASH;
				if (st == 6) sound(pdv_hero, CHAN_WEAPON, "weapons/lhit.wav", 1, ATTN_NORM);
				else         sound(pdv_hero, CHAN_WEAPON, "weapons/rocket1i.wav", 1, ATTN_NORM);
			}
			pdv_focus_pos = (pdv_hero.origin + pdv_foe.origin) * 0.5;
		}
		else
		{
			// Killing blow + death animation showcase!
			if (pdv_sub < 3)
			{
				pdv_sub = 3;
				PDV_TriggerDeath(st);
			}
			if (st == 6 && local_t < 2.2)
			{
				// Lightning arc during spasm
				WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
				WriteByte(MSG_BROADCAST, TE_LIGHTNING2);
				WriteEntity(MSG_BROADCAST, pdv_hero);
				WriteCoord(MSG_BROADCAST, pdv_hero.origin_x);
				WriteCoord(MSG_BROADCAST, pdv_hero.origin_y);
				WriteCoord(MSG_BROADCAST, pdv_hero.origin_z + 12);
				WriteCoord(MSG_BROADCAST, pdv_foe.origin_x);
				WriteCoord(MSG_BROADCAST, pdv_foe.origin_y);
				WriteCoord(MSG_BROADCAST, pdv_foe.origin_z + 10);
			}
			PDV_StepDeath(st, local_t - 1.1);
			pdv_hero.frame = 12; // stand1 admiring the KO
			pdv_focus_pos = pdv_foe.origin;
		}
	}
	else
	{
		// Finale: hero taunts/stands victorious while camera finishes 360 around Fox Theater street
		pdv_hero.frame = 12;
		pdv_focus_pos = pdv_hero.origin;
	}

	PDV_EvalCam(t);
	print("[PDV_CAM] ", ftos(t), " ", ftos(pdv_cam_ang_x), " ", ftos(pdv_cam_ang_y), "\n");

	if (t >= 25.4 && t < 26.4)
	{
		fa = floor(PDV_Clamp01((t - 25.4) / 0.95) * 255);
		stuffcmd(p, strcat("v_cshift 0 0 0 ", ftos(fa), "\n"));
	}
	else if (t >= 26.4)
	{
		if (!pdv_stopped)
		{
			pdv_stopped = TRUE;
			stuffcmd(p, "v_cshift 0 0 0 255\n");
			localcmd("stop\n");
		}
		if (t >= 26.8 && !pdv_quitted)
		{
			pdv_quitted = TRUE;
			if (cvar("intro_autoquit") > 0) localcmd("quit\n");
		}
	}

	Showcase_SyncPlayer(p);
};

void() Showcase_Precache = { PDV_Precache(); };
void() Showcase_StartDirector =
{
	pdv_t0 = 0; pdv_stage = 0; pdv_sub = 0; pdv_cam_fixed = FALSE;
	pdv_stopped = FALSE; pdv_quitted = FALSE;
	pdv_floor_z = 2;
	pdv_focus_pos = '-8855 2320 26';
	PDV_EvalCam(0);
	pdv_dir = spawn();
	pdv_dir.classname = "pdv_director";
	pdv_dir.think = PDV_DirectorTick;
	pdv_dir.nextthink = time + 0.02;
};
