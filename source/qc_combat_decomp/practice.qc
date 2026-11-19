#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
PRACTICE RANGE - maps/practice.bsp

Clean, bloat-free shooting range & custom asset showcase (active in-game
custom assets only):
  - Auto-grants every gun & refills reserve ammo / fun-gun cooldowns quickly.
  - Passive respawning range targets (`info_practice_target`) for active
    in-game custom characters: never shoot back, respawn in 2.0 s.
  - Circling passive aerial targets above the Central Jump Pad (Winged John
    and Rob Dob head): respawn in 2.0 s.
  - Optional Live-Fire Pen (`trigger_practice_livefire`) in the West Wing.
================
*/

float PR_KIND_RANDGUY	= 11;
float PR_KIND_AFROGUY	= 12;
float PR_KIND_LADY		= 13;
float PR_KIND_FATGUY	= 14;
float PR_KIND_GREENSUIT	= 16;
float PR_KIND_BEERGUY	= 17;
float PR_KIND_ROBEGUY	= 18;
float PR_KIND_ROGERV	= 19;
float PR_KIND_BRYAN		= 20;
float PR_KIND_DAVID		= 21;
float PR_KIND_DANIEL	= 22;
float PR_KIND_REESE		= 23;
float PR_KIND_BEACH		= 24;
float PR_KIND_ALEX		= 25;
float PR_KIND_PINKLADY	= 26;

void() Practice_CtrlThink;
void() Practice_TargetThink;
void() Practice_LivePenThink;

void() Practice_Precache =
{
	if (mapname != "practice")
	{
		practice_active = FALSE;
		practice_live_fire = FALSE;
		return;
	}
	practice_active = TRUE;
	practice_live_fire = FALSE;
	practice_ctrl = world;
	practice_air_bird = world;
	practice_air_float = world;
	practice_air_bird_t = time + 0.6;
	practice_air_float_t = time + 0.8;
	practice_live_t = 0;

	JohnBird_Precache ();
	EricCannon_Precache ();
	MMTank_Precache ();
	Bikes_Precache ();

	// Active in-game custom character models & sprites
	precache_model ("progs/npc_randguy.md3");
	precache_model ("progs/npc_afroguy.md3");
	precache_model ("progs/npc_randlady.md3");
	precache_model ("progs/npc_fatguy.md3");
	precache_model ("progs/beach_uncle_a.md3");
	precache_model ("progs/alex_pattaya_a.md3");
	precache_model ("progs/pinklady.md3");

	precache_model ("progs/greensuit_wheelman.spr32");
	precache_model ("progs/beerguy.spr32");
	precache_model ("progs/robeguy.spr32");
	precache_model ("progs/rogerver.spr32");
	precache_model ("progs/bryan.spr32");
	precache_model ("progs/david.spr32");
	precache_model ("progs/daniel.spr32");
	precache_model ("progs/reeseice.spr32");
	precache_model ("progs/robhead_proj.spr32");

	precache_sound ("player/death1.wav");
	precache_sound ("player/pain1.wav");
	precache_sound ("weapons/shotgn2.wav");
	precache_sound ("buttons/switch04.wav");

	practice_ctrl = spawn ();
	practice_ctrl.classname = "practice_ctrl";
	practice_ctrl.think = Practice_CtrlThink;
	practice_ctrl.nextthink = time + 0.4;
};

void(entity p) Practice_GiveAll =
{
	local entity oself;

	p.items = p.items | IT_AXE | IT_SHOTGUN | IT_SUPER_SHOTGUN | IT_NAILGUN | IT_SUPER_NAILGUN | IT_GRENADE_LAUNCHER | IT_ROCKET_LAUNCHER | IT_LASER_CANNON | IT_LIGHTNING;
	p.ammo_shells = autocvar_shells_max_capacity;
	p.ammo_nails = autocvar_nails_max_capacity;
	p.ammo_rockets = autocvar_rockets_max_capacity;
	p.ammo_cells = autocvar_cells_max_capacity;
	if (p.ammo_shells < 100) p.ammo_shells = 100;
	if (p.ammo_nails < 200) p.ammo_nails = 200;
	if (p.ammo_rockets < 100) p.ammo_rockets = 100;
	if (p.ammo_cells < 200) p.ammo_cells = 200;
	p.grenade_ammo = 6;
	p.jp_fuel = autocvar_jp_fuel;

	MegaMan_Give (p);
	Banana_Give (p);
	FunGun_Give (p);

	oself = self;
	self = p;
	BM_FillAll ();
	W_SetCurrentAmmo ();
	self = oself;
};

void(entity p) Practice_OnPlayerSpawn =
{
	if (!practice_active)
		return;
	Practice_GiveAll (p);
	p.pr_items_given = TRUE;
};

void() Practice_PlayerFrame =
{
	if (!practice_active || self.health <= 0)
		return;
	if (!self.pr_items_given)
		Practice_OnPlayerSpawn (self);

	// Only top up reserve ammo_* directly when bm_reload is OFF: when bm_reload is ON,
	// ammo_* holds the active magazine (2..36), so overwriting it to 100/200 trips BM_ReadFields
	// every single frame, cancelling reloads and resetting bm_ssgburst every tick.
	if (!autocvar_bm_reload)
	{
		if (self.ammo_shells < 40) self.ammo_shells = 100;
		if (self.ammo_nails < 60) self.ammo_nails = 200;
		if (self.ammo_rockets < 30) self.ammo_rockets = 100;
		if (self.ammo_cells < 60) self.ammo_cells = 200;
	}
	if ((self.flags & FL_ONGROUND) && self.jp_fuel < autocvar_jp_fuel)
		self.jp_fuel = autocvar_jp_fuel;

	// Fast cooldown cap for MegaMan / Banana / FunGuns (clamp regen timer instead of refilling every frame)
	if (self.mm_ammo < MM_MAX_AMMO && self.mm_regen_t > time + 1.5) self.mm_regen_t = time + 1.5;
	if (self.bn_ammo < BN_MAX_AMMO && self.bn_regen_t > time + 1.5) self.bn_regen_t = time + 1.5;
	if (self.fg_ammo1 < FG_DOB_MAX && self.fg_regen1 > time + 2.0) self.fg_regen1 = time + 2.0;
	if (self.fg_ammo2 < FG_PONG_MAX && self.fg_regen2 > time + 2.0) self.fg_regen2 = time + 2.0;
	if (self.fg_ammo3 < FG_PICKLE_MAX && self.fg_regen3 > time + 1.5) self.fg_regen3 = time + 1.5;
	if (self.fg_ammo4 < FG_NETSEND_MAX && self.fg_regen4 > time + 1.5) self.fg_regen4 = time + 1.5;
	if (self.fg_ammo5 < FG_DOOKIE_MAX && self.fg_regen5 > time + 1.0) self.fg_regen5 = time + 1.0;
	if (self.fg_ammo6 < FG_WCANNON_MAX && self.fg_regen6 > time + 2.0) self.fg_regen6 = time + 2.0;
	if (self.fg_ammo8 < FG_KYLE_MAX && self.fg_regen8 > time + 1.5) self.fg_regen8 = time + 1.5;
};

// ---------------------------------------------------------------- Passive Respawning Range Targets

float() Practice_TargetCustomize =
{
	local float rel, d, k;
	local vector delta;

	if (self.pr_dir_mode == 0)
		return TRUE;

	delta = (other.origin + other.view_ofs) - (self.origin + '0 0 26');
	rel = vectoyaw (delta) - self.angles_y;
	rel = rel - 360 * floor (rel / 360);

	if (self.pr_dir_mode == 3)
	{
		d = floor (rel / 22.5 + 0.5);
		if (d >= 16) d = 0;
		self.frame = 16 + d;
		return TRUE;
	}

	d = floor (rel / 45 + 0.5);
	if (d >= 8) d = 0;

	k = floor (time * self.pr_fps + self.origin_x * 0.02);
	k = k - self.pr_fcount * floor (k / self.pr_fcount);
	self.frame = d * self.pr_dir_stride + self.pr_f0 + k;
	return TRUE;
};

void() Practice_TargetDie =
{
	sound (self, CHAN_VOICE, "player/death1.wav", 0.85, ATTN_NORM);
	pointparticles (particleeffectnum ("TE_BLOOD"), self.origin + '0 0 20', '0 0 80', 14);

	if (self.enemy && self.enemy.classname == "player" && self.enemy.ishuman == 1)
		sprint (self.enemy, strcat ("Target eliminated: ", self.netname, " (respawns in 2s)\n"));

	self.flags = self.flags - (self.flags & FL_MONSTER);
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.takedamage = DAMAGE_NO;
	self.deadflag = DEAD_DEAD;
	self.enemy = world;
	self.model = string_null;
	self.velocity = '0 0 0';
	self.pr_respawn_t = time + 2.0;
	self.think = Practice_TargetThink;
	self.nextthink = time + 0.1;
};

void(entity attacker, float damage) Practice_TargetPain =
{
	if (self.health <= 0)
		return;
	sound (self, CHAN_VOICE, "player/pain1.wav", 0.55, ATTN_NORM);
	self.enemy = world;
	self.think = Practice_TargetThink;
	self.nextthink = time + 0.05;
};

void() Practice_TargetRestore =
{
	self.pr_respawn_t = 0;
	self.deadflag = DEAD_NO;
	self.enemy = world;
	self.health = self.max_health;
	self.flags = FL_MONSTER;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.takedamage = DAMAGE_AIM;
	self.angles = '0 0 0';
	self.angles_y = self.pr_home_yaw;
	self.velocity = '0 0 0';
	self.pr_patrol_sign = 1;
	setmodel (self, self.mdl);
	setsize (self, self.bbmins, self.bbmaxs);
	setorigin (self, self.pr_home);
	droptofloor ();
	pointparticles (particleeffectnum ("TE_TELEPORT"), self.origin + '0 0 18', '0 0 0', 1);
};

void() Practice_TargetThink =
{
	local float f, step, move_yaw;
	local vector d;

	if (self.pr_respawn_t > 0)
	{
		if (time >= self.pr_respawn_t)
			Practice_TargetRestore ();
		self.nextthink = time + 0.1;
		return;
	}

	if (self.health <= 0)
		return;

	if (self.pr_patrol_dist > 0 && self.speed > 0)
	{
		d = self.origin - self.pr_home;
		d_z = 0;
		if ((d * self.pr_patrol_dir) > self.pr_patrol_dist)
			self.pr_patrol_sign = -1;
		else if ((d * self.pr_patrol_dir) < -self.pr_patrol_dist)
			self.pr_patrol_sign = 1;

		move_yaw = vectoyaw (self.pr_patrol_dir * self.pr_patrol_sign);
		self.angles_y = move_yaw;
		step = self.speed * 0.05;
		if (!walkmove (move_yaw, step))
			self.pr_patrol_sign = -self.pr_patrol_sign;
	}
	else
	{
		self.angles_y = self.pr_home_yaw;
	}

	if (self.pr_dir_mode == 0 && self.pr_fcount > 1)
	{
		f = floor (time * self.pr_fps);
		self.frame = self.pr_f0 + (f - self.pr_fcount * floor (f / self.pr_fcount));
	}
	self.nextthink = time + 0.05;
};

void(entity e, float kind) Practice_ConfigureKind =
{
	e.pr_dir_mode = 0;
	e.pr_f0 = 0;
	e.pr_fcount = 1;
	e.pr_fps = 10;
	e.scale = 1;
	e.bbmins = VEC_HULL_MIN;
	e.bbmaxs = VEC_HULL_MAX;

	if (kind == PR_KIND_RANDGUY)
	{
		e.mdl = "progs/npc_randguy.md3";
		e.netname = "LAN Citizen";
		e.pr_f0 = 8; e.pr_fcount = 12;
		if (!e.max_health) e.max_health = 120;
	}
	else if (kind == PR_KIND_AFROGUY)
	{
		e.mdl = "progs/npc_afroguy.md3";
		e.netname = "Afro Citizen";
		e.pr_f0 = 8; e.pr_fcount = 12;
		if (!e.max_health) e.max_health = 120;
	}
	else if (kind == PR_KIND_LADY)
	{
		e.mdl = "progs/npc_randlady.md3";
		e.netname = "LAN Lady";
		e.pr_f0 = 8; e.pr_fcount = 12;
		if (!e.max_health) e.max_health = 120;
	}
	else if (kind == PR_KIND_FATGUY)
	{
		e.mdl = "progs/npc_fatguy.md3";
		e.netname = "Big LAN Guy";
		e.pr_f0 = 8; e.pr_fcount = 12;
		if (!e.max_health) e.max_health = 160;
	}
	else if (kind == PR_KIND_GREENSUIT)
	{
		e.mdl = "progs/greensuit_wheelman.spr32";
		e.netname = "Greensuit Wheelman";
		e.scale = 0.8036;
		e.bbmins = '-18 -18 0'; e.bbmaxs = '18 18 54';
		e.pr_dir_mode = 2; e.pr_dir_stride = 4; e.pr_f0 = 32; e.pr_fcount = 4; e.pr_fps = 10;
		if (!e.max_health) e.max_health = 165;
	}
	else if (kind == PR_KIND_BEERGUY)
	{
		e.mdl = "progs/beerguy.spr32";
		e.netname = "Beer Guy";
		e.scale = 0.483;
		e.bbmins = '-16 -16 0'; e.bbmaxs = '16 16 56';
		e.pr_dir_mode = 2; e.pr_dir_stride = 32; e.pr_f0 = 0; e.pr_fcount = 12; e.pr_fps = 14;
		if (!e.max_health) e.max_health = 140;
	}
	else if (kind == PR_KIND_ROBEGUY)
	{
		e.mdl = "progs/robeguy.spr32";
		e.netname = "Robe Guy";
		e.scale = 0.65;
		e.bbmins = '-18 -18 0'; e.bbmaxs = '18 18 56';
		e.pr_dir_mode = 2; e.pr_dir_stride = 4; e.pr_f0 = 32; e.pr_fcount = 4; e.pr_fps = 10;
		if (!e.max_health) e.max_health = 140;
	}
	else if (kind == PR_KIND_ROGERV)
	{
		e.mdl = "progs/rogerver.spr32";
		e.netname = "Roger Ver";
		e.scale = 0.48;
		e.bbmins = '-16 -16 0'; e.bbmaxs = '16 16 56';
		e.pr_dir_mode = 2; e.pr_dir_stride = 32; e.pr_f0 = 0; e.pr_fcount = 12; e.pr_fps = 14;
		if (!e.max_health) e.max_health = 140;
	}
	else if (kind == PR_KIND_BRYAN)
	{
		e.mdl = "progs/bryan.spr32";
		e.netname = "Tinfoil Bryan";
		e.scale = 0.65;
		e.bbmins = '-16 -16 0'; e.bbmaxs = '16 16 56';
		e.pr_dir_mode = 2; e.pr_dir_stride = 6; e.pr_f0 = 8; e.pr_fcount = 6; e.pr_fps = 11;
		if (!e.max_health) e.max_health = 160;
	}
	else if (kind == PR_KIND_DAVID)
	{
		e.mdl = "progs/david.spr32";
		e.netname = "David Ojeda";
		e.scale = 0.62;
		e.bbmins = '-16 -16 0'; e.bbmaxs = '16 16 56';
		e.pr_dir_mode = 2; e.pr_dir_stride = 4; e.pr_f0 = 8; e.pr_fcount = 4; e.pr_fps = 11;
		if (!e.max_health) e.max_health = 220;
	}
	else if (kind == PR_KIND_DANIEL)
	{
		e.mdl = "progs/daniel.spr32";
		e.netname = "4AM Daniel";
		e.scale = 0.66;
		e.bbmins = '-16 -16 0'; e.bbmaxs = '16 16 56';
		e.pr_dir_mode = 2; e.pr_dir_stride = 4; e.pr_f0 = 8; e.pr_fcount = 4; e.pr_fps = 11;
		if (!e.max_health) e.max_health = 320;
	}
	else if (kind == PR_KIND_REESE)
	{
		e.mdl = "progs/reeseice.spr32";
		e.netname = "ReeseIce";
		e.scale = 0.48;
		e.bbmins = '-16 -16 0'; e.bbmaxs = '16 16 56';
		e.pr_dir_mode = 2; e.pr_dir_stride = 44; e.pr_f0 = 0; e.pr_fcount = 12; e.pr_fps = 12;
		if (!e.max_health) e.max_health = 150;
	}
	else if (kind == PR_KIND_BEACH)
	{
		e.mdl = "progs/beach_uncle_a.md3";
		e.netname = "Beach Uncle";
		e.bbmins = '-16 -16 0'; e.bbmaxs = '16 16 64';
		if (!e.max_health) e.max_health = 150;
	}
	else if (kind == PR_KIND_ALEX)
	{
		e.mdl = "progs/alex_pattaya_a.md3";
		e.netname = "Alex Pattaya";
		e.bbmins = '-16 -16 0'; e.bbmaxs = '16 16 64';
		if (!e.max_health) e.max_health = 150;
	}
	else if (kind == PR_KIND_PINKLADY)
	{
		e.mdl = "progs/pinklady.md3";
		e.netname = "Pink Lady";
		e.bbmins = '-16 -16 0'; e.bbmaxs = '16 16 64';
		if (!e.max_health) e.max_health = 140;
	}
};

void() info_practice_target =
{
	local float k;

	k = self.count;
	if (!k) k = PR_KIND_GREENSUIT;
	self.pr_kind = k;
	if (self.health > 0)
		self.max_health = self.health;
	Practice_ConfigureKind (self, k);

	self.classname = "info_practice_target";
	self.pr_home = self.origin;
	self.pr_home_yaw = self.angles_y;
	if (vlen (self.pos1) > 1)
	{
		self.pr_patrol_dist = vlen (self.pos1);
		self.pr_patrol_dir = normalize (self.pos1);
	}
	else
	{
		self.pr_patrol_dist = 0;
		self.pr_patrol_dir = '1 0 0';
	}

	self.th_stand = Practice_TargetThink;
	self.th_walk = Practice_TargetThink;
	self.th_run = Practice_TargetThink;
	self.th_melee = SUB_Null;
	self.th_missile = SUB_Null;
	self.th_pain = Practice_TargetPain;
	self.th_die = Practice_TargetDie;
	self.customizeentityforclient = Practice_TargetCustomize;

	Practice_TargetRestore ();
	self.think = Practice_TargetThink;
	self.nextthink = time + 0.1 + random () * 0.2;
};

// ---------------------------------------------------------------- Circling Aerial Targets

void() Practice_AirFloatDie =
{
	sound (self, CHAN_VOICE, "weapons/r_exp3.wav", 0.85, ATTN_NORM);
	pointparticles (particleeffectnum ("TE_EXPLOSION"), self.origin, '0 0 0', 1);
	practice_air_float = world;
	practice_air_float_t = time + 2.0;
	remove (self);
};

void(entity attacker, float damage) Practice_AirFloatPain =
{
	sound (self, CHAN_VOICE, "player/pain1.wav", 0.6, ATTN_NORM);
	self.enemy = world;
};

void() Practice_AirOrbitThink =
{
	local float ang, rad, z0, spd, c, s, s2;
	local vector nxt;

	if (self.health <= 0)
		return;
	rad = 560; z0 = 540; spd = 0.65;
	ang = time * spd + self.pr_home_yaw;
	c = cos (ang);
	s = sin (ang);
	s2 = sin (ang * 2);
	nxt_x = c * rad;
	nxt_y = s * rad;
	nxt_z = z0 + s2 * 56;
	self.angles_y = (ang * 57.29578) + 90;
	setorigin (self, nxt);
	self.nextthink = time + 0.05;
};

void() Practice_SpawnAirBird =
{
	local entity jb;

	jb = spawn ();
	jb.angles = '0 0 0';
	setorigin (jb, '0 440 620');
	JB_InitEntity (jb, TRUE);
	jb.movetype = MOVETYPE_NONE;
	setsize (jb, '-28 -36 -4', '28 36 58');
	jb.jb_spawn_org = '0 440 620';
	jb.jb_ai = TRUE;
	jb.jb_ai_strafe = 1;
	jb.jb_ai_mode = 0;
	jb.jb_ai_mode_t = time + 999;
	jb.jb_ai_fire_t = time + 99999;
	jb.jb_flap_t = time + 0.1;
	jb.jb_voice_t = time + 9999;
	jb.think = JB_AutopilotThink;
	jb.nextthink = time + 0.05;
	practice_air_bird = jb;
};

void() Practice_SpawnAirFloat =
{
	local entity e;

	e = spawn ();
	e.classname = "practice_air_float";
	e.netname = "Aerial Rob Dob";
	e.flags = FL_MONSTER;
	e.solid = SOLID_SLIDEBOX;
	e.movetype = MOVETYPE_NONE;
	e.takedamage = DAMAGE_AIM;
	e.health = 160;
	e.max_health = 160;
	e.pr_home_yaw = 1.2;
	e.pr_dir_mode = 3;
	e.scale = FD_PROJ_SCALE;
	e.th_pain = Practice_AirFloatPain;
	e.th_die = Practice_AirFloatDie;
	e.customizeentityforclient = Practice_TargetCustomize;
	setmodel (e, "progs/robhead_proj.spr32");
	setsize (e, '-24 -24 -24', '24 24 24');
	setorigin (e, '560 0 540');
	e.think = Practice_AirOrbitThink;
	e.nextthink = time + 0.05;
	practice_air_float = e;
};

// ---------------------------------------------------------------- Live-Fire Pen

void() Practice_LivePenDie =
{
	sound (self, CHAN_VOICE, "player/death1.wav", 0.9, ATTN_NORM);
	pointparticles (particleeffectnum ("TE_BLOOD"), self.origin + '0 0 20', '0 0 80', 18);
	remove (self);
};

void(entity attacker, float dmg) Practice_LivePenPain =
{
	if (self.health <= 0)
		return;
	sound (self, CHAN_VOICE, "player/pain1.wav", 0.7, ATTN_NORM);
	if (attacker.classname == "player")
		self.enemy = attacker;
};

void() Practice_LivePenThink =
{
	local entity p, best;
	local float d, bd;
	local vector dir;

	if (!practice_live_fire || self.health <= 0)
	{
		remove (self);
		return;
	}

	best = world;
	bd = 1000;
	p = find (world, classname, "player");
	while (p)
	{
		if (p.health > 0 && p.deadflag == 0)
		{
			d = vlen (p.origin - self.origin);
			if (d < bd)
			{
				bd = d;
				best = p;
			}
		}
		p = find (p, classname, "player");
	}

	if (best != world)
	{
		dir = best.origin - self.origin;
		self.angles_y = vectoyaw (dir);
		if (bd > 160)
		{
			if (self.origin_x < -2180 && dir_x < 0) self.angles_y = 0;
			else if (self.origin_x > -1620 && dir_x > 0) self.angles_y = 180;
			walkmove (self.angles_y, 7.5);
		}
		if (time >= self.attack_finished && visible (best))
		{
			local vector src, aim_ang, pellet_dir;
			local float shots;

			self.attack_finished = time + 1.35 + random () * 0.8;
			sound (self, CHAN_WEAPON, "weapons/shotgn2.wav", 0.8, ATTN_NORM);
			src = self.origin + '0 0 24';
			dir = normalize ((best.origin + '0 0 18') - src);
			aim_ang = vectoangles (dir);
			aim_ang_x = 0 - aim_ang_x;
			makevectors (aim_ang);
			ClearMultiDamage ();
			shots = 3;
			while (shots > 0)
			{
				pellet_dir = normalize (dir + crandom () * 0.06 * v_right + crandom () * 0.06 * v_up);
				traceline (src, src + pellet_dir * 2048, FALSE, self);
				if (trace_fraction != 1)
					TraceAttack (5, pellet_dir);
				shots = shots - 1;
			}
			ApplyMultiDamage ();
		}
	}
	self.nextthink = time + 0.05;
};

void(float kind, vector org) Practice_SpawnPenFighter =
{
	local entity e;

	e = spawn ();
	e.classname = "practice_live_pen";
	e.pr_live_pen = TRUE;
	e.pr_kind = kind;
	Practice_ConfigureKind (e, kind);
	e.health = e.max_health;
	e.flags = FL_MONSTER;
	e.solid = SOLID_SLIDEBOX;
	e.movetype = MOVETYPE_STEP;
	e.takedamage = DAMAGE_AIM;
	e.attack_finished = time + 1.0 + random ();
	e.th_pain = Practice_LivePenPain;
	e.th_die = Practice_LivePenDie;
	e.customizeentityforclient = Practice_TargetCustomize;
	setmodel (e, e.mdl);
	setsize (e, e.bbmins, e.bbmaxs);
	setorigin (e, org);
	droptofloor ();
	e.think = Practice_LivePenThink;
	e.nextthink = time + 0.1;
};

void() Practice_EnsurePenFighters =
{
	local entity e;
	local float cnt;

	cnt = 0;
	e = find (world, classname, "practice_live_pen");
	while (e)
	{
		if (e.health > 0)
			cnt = cnt + 1;
		e = find (e, classname, "practice_live_pen");
	}
	if (cnt < 3)
	{
		if (cnt == 0) Practice_SpawnPenFighter (PR_KIND_GREENSUIT, '-2040 -160 32');
		else if (cnt == 1) Practice_SpawnPenFighter (PR_KIND_BRYAN, '-2040 160 32');
		else Practice_SpawnPenFighter (PR_KIND_DAVID, '-1820 0 32');
	}
};

void() Practice_ClearPenFighters =
{
	local entity e, nxt;

	e = find (world, classname, "practice_live_pen");
	while (e)
	{
		nxt = find (e, classname, "practice_live_pen");
		remove (e);
		e = nxt;
	}
};

void() Practice_ToggleLiveFire =
{
	practice_live_fire = !practice_live_fire;
	sound (self, CHAN_AUTO, "buttons/switch04.wav", 1.0, ATTN_NONE);
	if (practice_live_fire)
	{
		bprint ("Practice Range: LIVE-FIRE PEN ON (arena fighters & bots now fight back!)\n");
		Practice_EnsurePenFighters ();
	}
	else
	{
		bprint ("Practice Range: PEACEFUL MODE (all targets & bots passive)\n");
		Practice_ClearPenFighters ();
	}
};

void() trigger_practice_livefire =
{
	self.use = Practice_ToggleLiveFire;
};

// ---------------------------------------------------------------- Controller Tick

void() Practice_CtrlThink =
{
	if (mapname != "practice")
	{
		remove (self);
		return;
	}

	if (practice_air_bird == world || bm_wasfreed (practice_air_bird) || practice_air_bird.health <= 0 || practice_air_bird.jb_dying)
	{
		if (!practice_air_bird_t) practice_air_bird_t = time + 2.0;
		if (time >= practice_air_bird_t)
		{
			practice_air_bird_t = 0;
			Practice_SpawnAirBird ();
		}
	}
	else
	{
		practice_air_bird.jb_ai_fire_t = time + 99999;
	}

	if (practice_air_float == world || bm_wasfreed (practice_air_float) || practice_air_float.health <= 0)
	{
		if (!practice_air_float_t) practice_air_float_t = time + 2.0;
		if (time >= practice_air_float_t)
		{
			practice_air_float_t = 0;
			Practice_SpawnAirFloat ();
		}
	}

	if (practice_live_fire && time >= practice_live_t)
	{
		practice_live_t = time + 2.5;
		Practice_EnsurePenFighters ();
	}

	self.nextthink = time + 0.4;
};
