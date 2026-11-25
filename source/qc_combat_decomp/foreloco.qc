#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
FORELOCO POWERUP - implementation (Combat+)
================
*/

float	fl_precached;

void() FL_Precache =
{
	if (fl_precached)
		return;
	fl_precached = TRUE;

	precache_model ("progs/foreloco_can.md3");
	precache_model ("progs/v_foreloco.md3");
	precache_model ("progs/foreloco_proj_can.md3");
	precache_model ("progs/foreloco_bedpan.md3");
	precache_model ("progs/crowd_c1.spr32");

	precache_sound ("foreloco/can_open.wav");
	precache_sound ("foreloco/drink_gulp.wav");
	precache_sound ("foreloco/vegas_baby.wav");
	precache_sound ("foreloco/party_loop.wav");
	precache_sound ("foreloco/bed_horn.wav");
	precache_sound ("foreloco/boing_hit.wav");
	precache_sound ("foreloco/bed_jump.wav");
	precache_sound ("foreloco/bed_boost.wav");

	Vehicles_Precache ();
	GK_Precache ();
	precache_model (Veh_IntactModel (VEH_FORELOCO));
	precache_model (Veh_WreckModel (VEH_FORELOCO));
	precache_model (Veh_WheelModel (VEH_FORELOCO));
	precache_model (Veh_HoodModel (VEH_FORELOCO));
	precache_model (Veh_DoorModel (VEH_FORELOCO));
	precache_model (Veh_ExtraModel (VEH_FORELOCO));
	precache_model (Veh_BumperModel (VEH_FORELOCO));
};

void(entity p) FL_Reset =
{
	p.fl_phase = 0;
	p.fl_t0 = 0;
	p.fl_end_t = 0;
	p.fl_invuln_t = 0;
	p.fl_hits = 0;
	p.fl_vm_frame = 0;
	p.fl_snd_flags = 0;
	p.fl_st_black = 0;
	p.fl_st_mode = 0;
	p.fl_st_rem = 0;
	p.fl_st_speed = 0;
	p.fl_st_flags = 0;
	p.fl_st_anim = 0;
};

// 8-direction viewer-facing animation for Eric on the hospital gurney (progs/crowd_c1.spr32)
// Layout: 0..7 idle, 8 + d*6 + k walk (6f), 56 + d*5 + k run (5f)
float() FL_BedCustomize =
{
	local vector view_org;
	local float rel, d, k, spd, fbase, fstep, fps;

	if (other.clientcamera != world && other.clientcamera != other)
		view_org = other.clientcamera.origin;
	else
		view_org = other.origin;

	rel = vectoyaw (view_org - self.origin) - self.angles_y;
	d = floor (rel / 45 + 0.5) & 7;

	spd = self.gk_speed;
	if (spd < 30 && !self.veh_air)
	{
		self.frame = d;
		return TRUE;
	}

	if (spd >= 420 || self.gk_boosting || self.veh_air)
	{
		fps = 10 + 10 * bound (0, spd / 1500, 1);
		k = floor (time * fps);
		k = k - 5 * floor (k / 5);
		fbase = 56 + k;
		fstep = 5;
	}
	else
	{
		fps = 6 + 6 * bound (0, spd / 420, 1);
		k = floor (time * fps);
		k = k - 6 * floor (k / 6);
		fbase = 8 + k;
		fstep = 6;
	}
	self.frame = fbase + d * fstep;
	return TRUE;
};

void() FL_ProjTouch =
{
	local entity head, atk;
	local vector dir;
	local float dmg;

	if (other == self.owner || (self.gk_kart != world && other == self.gk_kart))
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}

	atk = self.gk_shooter;
	if (atk == world || bm_wasfreed (atk))
		atk = self.owner;

	sound7 (self, CHAN_BODY, "foreloco/boing_hit.wav", 0.95, ATTN_NORM, 92 + random () * 24);
	if (veh_fx_sparks > 0)
		pointparticles (veh_fx_sparks, self.origin, '0 0 0', 2);
	if (veh_fx_drift > 0)
		pointparticles (veh_fx_drift, self.origin, '0 0 0', 1);

	head = findradius (self.origin, 115);
	while (head != world)
	{
		if (head.takedamage && head != atk && head != self.gk_kart && head.classname != "veh_van_clip")
		{
			dir = head.origin - self.origin;
			dir_z = 0;
			if (vlen (dir) > 2)
				dir = normalize (dir);
			else
				dir = normalize (self.velocity);
			dmg = (head == other) ? 55 : 32;
			if (head.flags & (FL_CLIENT | FL_MONSTER))
			{
				head.flags = head.flags - (head.flags & FL_ONGROUND);
				head.velocity = head.velocity + dir * 480 + '0 0 360';
				if (atk.classname == "player" && atk.fl_phase == 3)
					atk.fl_hits = atk.fl_hits + 1;
			}
			T_Damage (head, self, atk, dmg);
		}
		head = head.chain;
	}
	remove (self);
};

// Gently scatters nearby enemies clear of Eric's hospital bed at spawn without killing them
void(entity v) FL_SpawnShockwave =
{
	local entity head;
	local vector dir;

	if (veh_fx_sparks > 0)
		pointparticles (veh_fx_sparks, v.origin + '0 0 18', '0 0 0', 4);
	if (veh_fx_drift > 0)
		pointparticles (veh_fx_drift, v.origin + '0 0 18', '0 0 0', 4);

	head = findradius (v.origin, 150);
	while (head != world)
	{
		if (head != v && head != v.veh_driver && (head.flags & (FL_CLIENT | FL_MONSTER)) && head.health > 0)
		{
			dir = head.origin - v.origin;
			dir_z = 0;
			if (vlen (dir) > 2)
				dir = normalize (dir);
			else
				dir = Veh_Fwd (v.angles_y);
			head.flags = head.flags - (head.flags & FL_ONGROUND);
			head.velocity = head.velocity + dir * 320 + '0 0 240';
		}
		head = head.chain;
	}
};

void(entity p, entity v) FL_BedFire =
{
	local entity prj, cam;
	local vector aim_ang, launch_org, dir, aim_pt, cam_org;
	local float is_pan;

	cam = v.veh_cament;
	aim_ang = '0 0 0';
	aim_ang_x = p.veh_cam_pitch * 0.45;
	aim_ang_y = p.veh_cam_yaw;
	makevectors (aim_ang);

	launch_org = v.origin + v_forward * 34 + '0 0 42';
	dir = v_forward;
	if (cam != world)
	{
		cam_org = cam.origin;
		traceline (cam_org, cam_org + v_forward * 2400, FALSE, v);
		aim_pt = trace_endpos;
		if (vlen (aim_pt - launch_org) > 64)
			dir = normalize (aim_pt - launch_org);
	}
	dir = normalize (dir + '0 0 0.08');

	is_pan = (p.fl_proj_alt > 0);
	p.fl_proj_alt = 1 - p.fl_proj_alt;

	sound7 (v, CHAN_WEAPON, "weapons/sgun1.wav", 0.72, ATTN_NORM, is_pan ? 128 : 148);
	prj = spawn ();
	prj.classname = "foreloco_proj";
	prj.owner = v;
	prj.gk_kart = v;
	prj.gk_shooter = p;
	prj.movetype = MOVETYPE_BOUNCE;
	prj.solid = SOLID_BBOX;
	prj.takedamage = DAMAGE_NO;
	prj.velocity = dir * 1120 + '0 0 180';
	prj.avelocity = is_pan ? '280 720 190' : '640 420 510';
	prj.angles = vectoangles (dir);
	if (is_pan)
		setmodel (prj, "progs/foreloco_bedpan.md3");
	else
		setmodel (prj, "progs/foreloco_proj_can.md3");
	setsize (prj, '-6 -6 -6', '6 6 6');
	setorigin (prj, launch_org);
	prj.touch = FL_ProjTouch;
	prj.think = SUB_Remove;
	prj.nextthink = time + 3.5;
};

void(entity p) FL_TransformToBed =
{
	local entity v, old_v;
	local vector pos, fwd;
	local float yaw;

	if (p.health <= 0 || p.deadflag)
	{
		FL_Reset (p);
		return;
	}

	pos = p.origin;
	yaw = Veh_NormYaw (p.v_angle_y);
	p.movetype = MOVETYPE_WALK;
	p.solid = SOLID_SLIDEBOX;

	v = Veh_SpawnDynamic (VEH_FORELOCO, pos, yaw);
	v.veh_temp = TRUE;
	v.max_health = 600;
	v.health = 600;
	v.customizeentityforclient = FL_BedCustomize;
	v.scale = 0.88;		// 1.2x normal 0.7328 NPC scale!

	// Nudge clear of walls if player blacked out pressed against a wall
	GK_Depenetrate (v);

	Veh_Enter (p, v);
	p.fl_phase = 3;
	p.fl_t0 = time;
	p.fl_end_t = time + FL_BED_DUR;
	p.fl_invuln_t = time + FL_INVULN_DUR;
	p.fl_hits = 0;
	p.fl_snd_flags = 0;
	p.invincible_finished = max (p.invincible_finished, p.fl_invuln_t);
	v.fl_invuln_t = p.fl_invuln_t;
	v.invincible_finished = max (v.invincible_finished, p.fl_invuln_t);
	v.effects = v.effects | EF_DIMLIGHT;
	p.fl_st_mode = 3;
	p.fl_st_black = 100;
	p.fl_st_rem = floor (FL_BED_DUR * 10);
	p.fl_st_flags = 3;		// invuln + 360 reveal active

	// Gentle forward roll while the 360 situation reveal orbits Eric, plus ER spawn scatter
	fwd = Veh_Fwd (yaw);
	v.velocity = fwd * 170;
	v.gk_nitro = 100;
	FL_SpawnShockwave (v);

	// Start full 3D-spatialized party loop + brief spawn shield chime on the bed
	sound (p, CHAN_ITEM, "misc/null.wav", 1, ATTN_NORM);
	sound (p, CHAN_BODY, "misc/null.wav", 1, ATTN_NORM);
	sound7 (v, CHAN_ITEM, "items/protect.wav", 0.72, ATTN_NORM, 112);
	sound7 (v, VD_MUSIC_CH, "foreloco/party_loop.wav", 0.95, ATTN_NORM, 100);
	v.veh_music_t = time + FL_PARTY_LEN;
	if (p.ishuman == 1)
		centerprint (p, "VEGAS BABY!! CHECK YOUR SURROUNDINGS (INVULNERABLE)!");
};

void(entity p, entity v, float dt) FL_BedDriveTick =
{
	local float rem, age, fl_flags, is_invuln, in_orbit, is_boosted;

	if (p.fl_phase != 3)
		return;

	age = time - p.fl_t0;
	if (age < FL_BLACK_FADE)
		p.fl_st_black = floor (bound (0, (1 - age / FL_BLACK_FADE) * 100, 100));
	else
		p.fl_st_black = 0;

	is_invuln = (time < p.fl_invuln_t);
	in_orbit = (age < FL_INTRO_DUR);
	is_boosted = (v.gk_boosting || time < v.gk_boost_t);

	if (!is_invuln && (v.effects & EF_DIMLIGHT))
		v.effects = v.effects - (v.effects & EF_DIMLIGHT);

	// Trigger celebratory Nurse-Call Turbo surge the moment the 360 reveal completes
	if (!in_orbit && !(p.fl_snd_flags & 8))
	{
		p.fl_snd_flags = p.fl_snd_flags | 8;
		v.velocity = v.velocity + Veh_Fwd (v.angles_y) * 540;
		v.gk_nitro = 100;
		v.gk_boost_t = time + 0.75;
		v.gk_boost_pwr = 1320;
		sound7 (v, CHAN_AUTO, "foreloco/bed_boost.wav", 0.90, ATTN_NORM, 106);
		sound7 (v, CHAN_BODY, "foreloco/bed_horn.wav", 0.92, ATTN_NORM, 112);
		if (p.ishuman == 1)
			centerprint (p, "ERIC HOSPITAL BED!! SHIFT=TURBO | SPACE=JUMP | M1=BEDPANS/HORN");
	}

	fl_flags = 0;
	if (is_invuln)
		fl_flags = fl_flags | 1;
	if (in_orbit)
		fl_flags = fl_flags | 2;
	if (is_boosted)
		fl_flags = fl_flags | 4;
	fl_flags = fl_flags + floor (min (255, p.fl_hits)) * 16;

	rem = max (0, p.fl_end_t - time);
	p.fl_st_mode = 3;
	p.fl_st_rem = floor (rem * 10 + 0.5);
	p.fl_st_speed = floor (v.gk_speed + 0.5);
	p.fl_st_flags = fl_flags;

	// Loop 3D-spatialized party music from the rolling bed
	if (time >= v.veh_music_t)
	{
		sound7 (v, VD_MUSIC_CH, "foreloco/party_loop.wav", 0.95, ATTN_NORM, 100);
		v.veh_music_t = time + FL_PARTY_LEN;
	}

	// Trailing party sparkles & caster sparks under the bed
	if (time >= p.fl_fx_t)
	{
		p.fl_fx_t = time + (v.gk_boosting ? 0.05 : 0.12);
		if (veh_fx_drift > 0)
			pointparticles (veh_fx_drift, v.origin + '0 0 12', '0 0 0', 1);
		if (v.gk_speed > 380 && veh_fx_sparks > 0)
			pointparticles (veh_fx_sparks, v.origin + '0 0 4', '0 0 0', 1);
	}

	if (time >= p.fl_end_t)
	{
		// Time up: eject player cleanly back to normal
		local vector exit_p;
		if (Veh_ExitSpot (v, p))
			exit_p = vd_exit;
		else
			exit_p = v.origin + '0 0 24';
		FL_Reset (p);
		Veh_Leave (v, exit_p, v.velocity * 0.25 + '0 0 120', TRUE);
		if (veh_fx_drift > 0)
			pointparticles (veh_fx_drift, exit_p + '0 0 16', '0 0 0', 3);
		if (p.ishuman == 1)
			centerprint (p, "ForeLoco wore off! You survived Vegas!");
	}
};

void(entity p) FL_StartDrink =
{
	if (p.classname != "player" || p.ishuman != 1 || p.health <= 0 || p.deadflag)
		return;
	if (p.fl_phase > 0 || Veh_Driving (p) || p.veh_ride != world || MMTank_Driving (p) || JohnBird_Flying (p) || RocketRider_Flying (p) || EricCannon_Active (p) || FD_Flying (p))
		return;

	if (time <= 1.1)
		FL_Precache ();
	p.fl_phase = 1;
	p.fl_t0 = time;
	p.fl_vm_frame = 0;
	p.fl_snd_flags = 0;
	p.fl_saved_wep = p.weapon;
	p.weaponmodel = "";
	p.weaponframe = 0;
	p.fl_st_mode = 1;
	p.fl_st_black = 0;
	p.fl_st_rem = floor (FL_DRINK_DUR * 10);
	p.fl_st_speed = 0;
	p.fl_st_flags = 0;
	p.fl_st_anim = 1;
	p.attack_finished = time + FL_DRINK_DUR + FL_BLACK_HOLD + 0.2;
};

float() FL_Frame =
{
	local float el, frac, hspd, b_el;
	local vector hv;

	if (self.fl_phase <= 0)
		return FALSE;

	// If already in the hospital bed, Veh_DriveFrame handles driving & FL_BedDriveTick
	if (self.fl_phase == 3)
		return FALSE;

	if (self.health <= 0 || self.deadflag)
	{
		FL_Reset (self);
		return FALSE;
	}

	if (self.fl_phase == 1)
	{
		el = time - self.fl_t0;
		frac = bound (0, el / FL_DRINK_DUR, 1);
		self.fl_vm_frame = bound (1, 1 + floor (frac * (FL_VM_FRAMES - 0.001)), FL_VM_FRAMES);
		self.fl_st_anim = self.fl_vm_frame;
		self.weaponframe = self.fl_vm_frame;
		self.fl_st_mode = 1;
		self.fl_st_black = 0;
		self.fl_st_rem = floor (max (0, FL_DRINK_DUR - el) * 10);

		// Slow player movement while drinking + beat-synced camera sway
		hv = self.velocity;
		hv_z = 0;
		hspd = vlen (hv);
		if (hspd > 155)
		{
			hv = normalize (hv) * 155;
			self.velocity_x = hv_x;
			self.velocity_y = hv_y;
		}
		local float pop_p, pop_s, sway, sw_s, sw_c, chug_env, gulp_s, cr_env, cr_s, yeet_env, yeet_s;
		pop_s = 0;
		if (el >= 0.70 && el < 0.92)
		{
			pop_p = (el - 0.70) / 0.22;
			pop_s = sin (pop_p * 3.14159);
		}
		sway = bound (0, (el - 0.96) / 1.85, 1);
		sw_s = sin (time * 7.6);
		sw_c = cos (time * 5.4);

		chug_env = bound (0, (el - 0.98) / 0.30, 1) * (1 - bound (0, (el - 2.12) / 0.20, 1));
		if (chug_env > 0.001 && el >= 1.24)
			gulp_s = sin ((el - 1.24) * 19.2);
		else
			gulp_s = 0;

		cr_env = bound (0, (el - 2.20) / 0.10, 1) * (1 - bound (0, (el - 2.48) / 0.12, 1));
		cr_s = sin (time * 38.0);

		yeet_env = 0;
		yeet_s = 0;
		if (el >= 2.54)
		{
			yeet_env = bound (0, (el - 2.54) / 0.31, 1);
			yeet_s = sin (yeet_env * 3.14159);
		}

		self.punchangle_z = 1.2 * pop_s + sw_s * 6.0 * sway + cr_s * 1.6 * cr_env - 5.5 * yeet_s;
		self.punchangle_x = -1.5 * pop_s + (-2.6 + gulp_s * 1.4) * chug_env + sw_c * 2.4 * sway + 1.2 * cr_env + 3.2 * yeet_s;

		// Timed sound cues matching the 36-frame 2D sprite animation:
		// frame 10 (~0.72s): tab snap + fizz; frame 16 (~1.24s): 3-gulp chug; 2.20s: cut gulp; 2.22s: VEGAS BABY!
		if (!(self.fl_snd_flags & 1) && el >= 0.72)
		{
			self.fl_snd_flags = self.fl_snd_flags | 1;
			sound7 (self, CHAN_WEAPON, "foreloco/can_open.wav", 1, ATTN_NORM, 100);
		}
		if (!(self.fl_snd_flags & 2) && el >= 1.24)
		{
			self.fl_snd_flags = self.fl_snd_flags | 2;
			sound7 (self, CHAN_BODY, "foreloco/drink_gulp.wav", 1, ATTN_NORM, 100);
		}
		if (!(self.fl_snd_flags & 16) && el >= 2.20)
		{
			self.fl_snd_flags = self.fl_snd_flags | 16;
			sound (self, CHAN_BODY, "misc/null.wav", 1, ATTN_NORM);
		}
		if (!(self.fl_snd_flags & 4) && el >= 2.22)
		{
			self.fl_snd_flags = self.fl_snd_flags | 4;
			sound7 (self, CHAN_VOICE, "foreloco/vegas_baby.wav", 1, ATTN_NONE, 100);
			sound7 (self, CHAN_ITEM, "foreloco/party_loop.wav", 0.65, ATTN_NORM, 100);
			centerprint (self, "VEGAS BABY!!");
		}

		if (el >= FL_DRINK_DUR)
		{
			self.fl_phase = 2;
			self.fl_t0 = time;
			self.fl_st_mode = 2;
			self.velocity = '0 0 0';
			self.movetype = MOVETYPE_NONE;
		}
		return TRUE;
	}

	if (self.fl_phase == 2)
	{
		b_el = time - self.fl_t0;
		self.velocity = '0 0 0';
		self.fl_st_mode = 2;
		self.fl_st_black = floor (bound (0, (b_el / 0.25) * 100, 100));
		if (b_el >= FL_BLACK_HOLD)
			FL_TransformToBed (self);
		return TRUE;
	}

	return FALSE;
};

// -----------------------------------------------------------------------------
// Floating 3D Powerup Entity: item_powerup_foreloco
// -----------------------------------------------------------------------------
void() FL_CanThink;

void() FL_CanRespawn =
{
	self.model = self.mdl;
	self.solid = SOLID_TRIGGER;
	self.nextthink = time + 0.05;
	self.think = FL_CanThink;
	sound (self, CHAN_VOICE, "items/itembk2.wav", 1, ATTN_NORM);
	setorigin (self, self.origin);
};

void() FL_CanThink =
{
	local float bob, s_bob;
	if (self.solid == SOLID_TRIGGER)
	{
		self.angles_y = anglemod (self.angles_y + 115 * 0.05);
		s_bob = sin (time * 3.2);
		bob = s_bob * 3.5;
		setorigin (self, self.veh_spawn_org + '0 0 1' * bob);
		if (time >= self.fl_fx_t)
		{
			self.fl_fx_t = time + 0.18;
			if (veh_fx_drift > 0)
				pointparticles (veh_fx_drift, self.origin + '0 0 8', '0 0 0', 1);
		}
	}
	self.nextthink = time + 0.05;
};

void() FL_CanTouch =
{
	if (other.classname != "player" || other.ishuman != 1 || other.health <= 0 || other.deadflag)
		return;
	if (other.fl_phase > 0 || Veh_Driving (other) || other.veh_ride != world || MMTank_Driving (other) || JohnBird_Flying (other) || RocketRider_Flying (other) || EricCannon_Active (other) || FD_Flying (other))
		return;

	if (deathmatch)
	{
		self.solid = SOLID_NOT;
		self.model = "";
		self.think = FL_CanRespawn;
		self.nextthink = time + 60;
	}
	else
	{
		self.solid = SOLID_NOT;
		self.model = "";
		self.think = SUB_Remove;
		self.nextthink = time + 0.1;
	}

	FL_StartDrink (other);
};

void() FL_CanDrop =
{
	self.flags = FL_ITEM;
	self.solid = SOLID_TRIGGER;
	self.movetype = MOVETYPE_TOSS;
	self.velocity = '0 0 0';
	self.origin_z = self.origin_z + 6;
	droptofloor ();
	self.movetype = MOVETYPE_NONE;
	setorigin (self, self.origin + '0 0 28');
	self.veh_spawn_org = self.origin;
	self.think = FL_CanThink;
	self.nextthink = time + 0.05;
};

void() item_powerup_foreloco =
{
	FL_Precache ();
	self.classname = "item_powerup_foreloco";
	self.touch = FL_CanTouch;
	setmodel (self, "progs/foreloco_can.md3");
	self.mdl = self.model;
	self.traileffectnum = particleeffectnum ("quad");
	self.effects = self.effects | EF_DIMLIGHT | EF_FULLBRIGHT;
	self.netname = "Watermelon ForeLoco";
	setsize (self, '-16 -16 -24', '16 16 32');
	self.think = FL_CanDrop;
	self.nextthink = time + 0.15;
};

void() FL_Impulse =
{
	local entity e;
	local vector fwd;

	if (!autocvar_sv_cheats)
		return;
	if (self.impulse == 156)
	{
		self.impulse = 0;
		makevectors ('0 1 0' * self.v_angle_y);
		fwd = v_forward;
		e = spawn ();
		e.origin = self.origin + fwd * 120 + '0 0 16';
		e.angles = '0 0 0';
		local entity oldself;
		oldself = self;
		self = e;
		item_powerup_foreloco ();
		self = oldself;
		sprint (self, "Spawned Watermelon ForeLoco!\n");
		return;
	}
	if (self.impulse == 157)
	{
		self.impulse = 0;
		FL_StartDrink (self);
		return;
	}
};
