#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
PRACTICE RANGE - maps/practice.bsp

Wide-open empty practice arena with a central jump-pad hole:
  - Auto-grants every gun & refills reserve ammo / fun-gun cooldowns quickly.
  - 1 walking, non-shooting enemy player model (`progs/player_id1.mdl`) that
    patrols around the central arena and respawns 2.5s after elimination.
  - Map entities place 1 Mega Man Tank, 1 Go-Kart, and 1 of each powerup.
================
*/

void() Practice_CtrlThink;
void() Practice_EnemyThink;

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
	practice_enemy = world;
	practice_enemy_t = time + 0.5;
	practice_live_t = 0;

	MMTank_Precache ();
	Vehicles_Precache ();

	precache_model ("progs/player_id1.mdl");
	precache_sound ("player/death1.wav");
	precache_sound ("player/pain1.wav");

	practice_ctrl = spawn ();
	practice_ctrl.classname = "practice_ctrl";
	practice_ctrl.think = Practice_CtrlThink;
	practice_ctrl.nextthink = time + 0.3;
};

void(entity p) Practice_GiveAll =
{
	local entity oself;

	p.items = p.items | IT_AXE | IT_SUPER_SHOTGUN | IT_SUPER_NAILGUN | IT_GRENADE_LAUNCHER | IT_ROCKET_LAUNCHER | IT_LASER_CANNON | IT_LIGHTNING;
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
	if (self.fg_ammo10 < FG_CYRAX_MAX && self.fg_regen10 > time + 2.0) self.fg_regen10 = time + 2.0;
};

// ---------------------------------------------------------------- Walking Non-Shooting Enemy Player Model

vector(float idx) Practice_EnemyWaypoint =
{
	local float a;

	// 8-point loop at radius 300 around the center hole (stays clear of pit, vehicles, and powerups)
	a = idx * 45 * 0.01745329;
	return ('1 0 0' * (cos (a) * 300)) + ('0 1 0' * (sin (a) * 300)) + '0 0 28';
};

void() Practice_EnemyDie =
{
	sound (self, CHAN_VOICE, "player/death1.wav", 0.9, ATTN_NORM);
	pointparticles (particleeffectnum ("TE_BLOOD"), self.origin + '0 0 20', '0 0 80', 18);

	if (self.enemy && self.enemy.classname == "player" && self.enemy.ishuman == 1)
		sprint (self.enemy, "Practice Enemy eliminated (respawns in 2.5s)\n");

	practice_enemy = world;
	practice_enemy_t = time + 2.5;
	remove (self);
};

void(entity attacker, float damage) Practice_EnemyPain =
{
	if (self.health <= 0)
		return;
	sound (self, CHAN_VOICE, "player/pain1.wav", 0.65, ATTN_NORM);
	self.enemy = world;
	self.think = Practice_EnemyThink;
	self.nextthink = time + 0.05;
};

void() Practice_EnemyThink =
{
	local vector wp, delta;
	local float f, yaw, moved;

	if (self.health <= 0)
		return;

	self.enemy = world;
	wp = Practice_EnemyWaypoint (self.pr_patrol_sign);
	delta = wp - self.origin;
	delta_z = 0;

	if (vlen (delta) < 48)
	{
		self.pr_patrol_sign = self.pr_patrol_sign + 1;
		if (self.pr_patrol_sign >= 8)
			self.pr_patrol_sign = 0;
		self.pr_stuck_t = 0;
		wp = Practice_EnemyWaypoint (self.pr_patrol_sign);
		delta = wp - self.origin;
		delta_z = 0;
	}

	yaw = vectoyaw (delta);
	self.angles = '0 0 0';
	self.angles_y = yaw;

	moved = walkmove (yaw, 10.5);
	if (!moved)
		moved = walkmove (yaw + 45, 10.5);
	if (!moved)
		moved = walkmove (yaw - 45, 10.5);
	if (!moved)
	{
		self.pr_stuck_t = self.pr_stuck_t + 0.05;
		if (self.pr_stuck_t > 0.6)
		{
			self.pr_stuck_t = 0;
			self.pr_patrol_sign = self.pr_patrol_sign + 1;
			if (self.pr_patrol_sign >= 8)
				self.pr_patrol_sign = 0;
		}
	}
	else
	{
		self.pr_stuck_t = 0;
	}

	// Standard Quake player run frames 6..11 (10 fps)
	f = floor (time * 10);
	self.frame = 6 + (f - 6 * floor (f / 6));
	self.nextthink = time + 0.05;
};

void() Practice_SpawnEnemy =
{
	local entity e, oself;

	e = spawn ();
	e.classname = "monster_practice_enemy";
	e.netname = "Practice Enemy";
	e.flags = FL_MONSTER;
	e.solid = SOLID_SLIDEBOX;
	e.movetype = MOVETYPE_STEP;
	e.takedamage = DAMAGE_AIM;
	e.health = 100;
	e.max_health = 100;
	e.pr_patrol_sign = 2;	// start at (0, 300) walking toward (-212, 212)
	e.pr_stuck_t = 0;
	e.th_stand = Practice_EnemyThink;
	e.th_walk = Practice_EnemyThink;
	e.th_run = Practice_EnemyThink;
	e.th_melee = SUB_Null;
	e.th_missile = SUB_Null;
	e.th_pain = Practice_EnemyPain;
	e.th_die = Practice_EnemyDie;
	e.angles = '0 180 0';

	setmodel (e, "progs/player_id1.mdl");
	setsize (e, VEC_HULL_MIN, VEC_HULL_MAX);
	setorigin (e, '0 300 28');

	oself = self;
	self = e;
	droptofloor ();
	self = oself;

	pointparticles (particleeffectnum ("TE_TELEPORT"), e.origin + '0 0 18', '0 0 0', 1);
	e.think = Practice_EnemyThink;
	e.nextthink = time + 0.05;
	practice_enemy = e;
};

// ---------------------------------------------------------------- Legacy Entity Stubs

void() info_practice_target =
{
	remove (self);
};

void() Practice_ToggleLiveFire =
{
	practice_live_fire = FALSE;
};

void() trigger_practice_livefire =
{
	remove (self);
};

// ---------------------------------------------------------------- Controller Tick

void() Practice_CtrlThink =
{
	if (mapname != "practice")
	{
		remove (self);
		return;
	}

	if (practice_enemy == world || bm_wasfreed (practice_enemy) || practice_enemy.health <= 0)
	{
		if (!practice_enemy_t)
			practice_enemy_t = time + 2.5;
		if (time >= practice_enemy_t)
		{
			practice_enemy_t = 0;
			Practice_SpawnEnemy ();
		}
	}

	self.nextthink = time + 0.25;
};
