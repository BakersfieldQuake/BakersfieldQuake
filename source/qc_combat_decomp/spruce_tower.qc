#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
spruce_tower.qc — Destructible, Climbable, Flood-Triggering & Rebuildable Water Tower for `spruce`
Features:
  - Seamless 3D swimming physics & underwater tint inside the hollow tank AND during 14s neighborhood flood
  - Dynamic hit-cluster rocket breach tracking: >= 5 rockets in the same spot tears a hole with shrapnel + volumetric waterfall cascade
  - Total structural failure (~7 more rockets): multi-beat climbing explosions, 2.6s hinge topple onto compound yard, giant slam fireball
  - 3.5s radial 3D crashing tidal wave walls (`spruce_wave_n/s/e/w`) sweeping across Spruce ahead of a 76u (~6.3 ft) flood
  - 14-second flood followed by 2.5s drain + 22-second staged rebuild with lively worker NPCs
*/

float	WT_STATE_INTACT		= 0;
float	WT_STATE_TOPPLE		= 1;
float	WT_STATE_FLOODING	= 2;
float	WT_STATE_FLOODED	= 3;
float	WT_STATE_DRAINING	= 4;
float	WT_STATE_REBUILD	= 5;

float	WT_CENTER_X		= -1098.84;
float	WT_CENTER_Y		= 5800.20;
float	WT_TANK_Z_BOT	= 786;
float	WT_TANK_Z_SURF	= 1050;
float	WT_TANK_Z_TOP	= 1120;
float	WT_TANK_R_IN	= 244;
float	WT_FLOOD_DEPTH	= 76;		// ~6.3 ft: waist/swim height on streets while cars, fences & roofs stay clear

float	WT_POST_HITS_COLLAPSE	= 7;
float	WT_TOPPLE_CREAK_T		= 0.9;
float	WT_TOPPLE_FALL_T		= 1.7;
float	WT_TOPPLE_TOTAL_T		= 2.6;
float	WT_WAVE_DURATION		= 3.5;
float	WT_WAVE_SPEED			= 1250;
float	WT_WAVE_LIFT_Z			= 168;
float	WT_FLOOD_HOLD_T			= 14;
float	WT_DRAIN_DURATION		= 2.5;
float	WT_REBUILD_DURATION		= 22;

float	spruce_wt_state;
float	spruce_flood_z;
float	spruce_wt_phase_t0;
float	spruce_wt_breaches;
float	spruce_wt_post_hits;
float	spruce_wt_topple_beat;
float	spruce_wt_wave_dist;
float	spruce_wt_wave_snd_t;
float	spruce_wt_flood_warn;
float	spruce_wt_rebuild_snd_t;
float	spruce_tower_precached;
float	spruce_fx_waterjet;
float	spruce_fx_tidalfoam;
float	spruce_fx_vehexplode;

entity	spruce_wt_ctrl;
entity	spruce_wt_legs;
entity	spruce_wt_catwalk;
entity	spruce_wt_tank;
entity	spruce_wt_water;
entity	spruce_flood_ent;
entity	spruce_wave_n_ent;
entity	spruce_wave_s_ent;
entity	spruce_wave_e_ent;
entity	spruce_wave_w_ent;
entity	spruce_last_rocket;
float	spruce_last_rocket_t;

.float	wt_node_hits;
.float	wt_node_breached;
.vector	wt_node_out;
.float	wt_node_fx_t;
.float	wt_worker_slot;
.float	wt_worker_snd_t;
.float	wt_worker_panic_t;
.float	wt_worker_anim;
.float	spruce_in_water;
.float	spruce_cshift_on;
.float	spruce_swim_snd_t;
.float	spruce_wave_hit_t;
.float	spruce_swim_grav;

void() RandomNPCs_Precache;
void() Vehicles_Precache;
entity(string mdl, vector org, vector vel, vector ang, float life) Veh_SpawnDebris;

void() SpruceTower_Precache =
{
	if (spruce_tower_precached)
		return;
	spruce_tower_precached = TRUE;

	RandomNPCs_Precache ();
	Vehicles_Precache ();
	precache_model ("progs/veh_shrap1.md3");
	precache_model ("progs/veh_shrap2.md3");
	precache_model ("progs/veh_shrap3.md3");
	precache_model ("progs/veh_shrap4.md3");
	precache_sound ("misc/water1.wav");
	precache_sound ("misc/water2.wav");
	precache_sound ("player/inh2o.wav");
	precache_sound ("player/h2ojump.wav");
	precache_sound ("weapons/r_exp3.wav");
	spruce_fx_waterjet = particleeffectnum ("spruce_water_jet");
	spruce_fx_tidalfoam = particleeffectnum ("spruce_tidal_foam");
	spruce_fx_vehexplode = particleeffectnum ("veh_explode");
};

void(string msg) Spruce_CenterprintAll =
{
	local entity p;
	p = bm_player_head;
	while (p)
	{
		if (p.ishuman)
			centerprint (p, msg);
		p = p.bm_player_next;
	}
};

void(vector org, float radius, float kick) Spruce_ShockShake =
{
	local entity p;
	local float d, frac;
	local vector dir;

	p = bm_player_head;
	while (p)
	{
		if (p.health > 0)
		{
			d = vlen (p.origin - org);
			if (d < radius)
			{
				frac = 1 - (d / radius);
				if (p.ishuman)
				{
					p.punchangle_x = p.punchangle_x + (random () - 0.5) * 16 * frac;
					p.punchangle_z = p.punchangle_z + (random () - 0.5) * 12 * frac;
				}
				if (kick > 0)
				{
					dir = p.origin - org;
					dir_z = 0;
					if (vlen (dir) < 1)
						dir = '1 0 0';
					else
						dir = normalize (dir);
					p.velocity = p.velocity + dir * (kick * frac) + '0 0 1' * (180 * frac);
					p.flags = p.flags - (p.flags & FL_ONGROUND);
				}
			}
		}
		p = p.bm_player_next;
	}
};

void(entity bmodel_ent) Spruce_NudgePlayersClear =
{
	local entity p;
	local vector dir;

	if (!bmodel_ent)
		return;
	p = bm_player_head;
	while (p)
	{
		if (p.health > 0)
		{
			if (p.absmax_x > bmodel_ent.absmin_x - 24 && p.absmin_x < bmodel_ent.absmax_x + 24
				&& p.absmax_y > bmodel_ent.absmin_y - 24 && p.absmin_y < bmodel_ent.absmax_y + 24
				&& p.absmax_z > bmodel_ent.absmin_z - 16 && p.absmin_z < bmodel_ent.absmax_z + 16)
			{
				dir = p.origin - (WT_CENTER_X * '1 0 0' + WT_CENTER_Y * '0 1 0' + p.origin_z * '0 0 1');
				dir_z = 0;
				if (vlen (dir) < 4)
					dir = '1 0 0';
				else
					dir = normalize (dir);
				setorigin (p, p.origin + dir * 48 + '0 0 16');
				p.velocity = dir * 180 + '0 0 160';
				p.flags = p.flags - (p.flags & FL_ONGROUND);
			}
		}
		p = p.bm_player_next;
	}
};

string(float idx) Spruce_ShrapnelModel =
{
	local float k;
	k = idx - 4 * floor (idx / 4);
	if (k == 0)
		return "progs/veh_shrap1.md3";
	if (k == 1)
		return "progs/veh_shrap2.md3";
	if (k == 2)
		return "progs/veh_shrap3.md3";
	return "progs/veh_shrap4.md3";
};

void(vector org, vector out_dir, float count, float spd) Spruce_SpawnShrapnelBurst =
{
	local float i;
	local vector v, jorg;
	local entity d;

	for (i = 0; i < count; i = i + 1)
	{
		jorg_x = org_x + crandom () * 24;
		jorg_y = org_y + crandom () * 24;
		jorg_z = org_z + crandom () * 20;
		v = out_dir * (spd * (0.65 + random () * 0.7))
			+ ('1 0 0' * crandom () + '0 1 0' * crandom ()) * (spd * 0.65)
			+ '0 0 1' * (140 + random () * (spd * 0.65));
		d = Veh_SpawnDebris (Spruce_ShrapnelModel (i), jorg, v, '0 0 0', 5.0 + random () * 2.5);
		if (d)
		{
			if (random () < 0.5)
				d.colormod = '0.24 0.52 0.30';
			else
				d.colormod = '0.88 0.92 0.94';
		}
	}
};

// ============================================================================
// 1. VIRTUAL QUAKEC SWIMMING & FLOOD WATER INTERACTION
// ============================================================================

void(entity p) Spruce_PlayerWaterPreThink =
{
	local float lvl, dx, dy, r2, feet_z, eye_z, surf_z;
	local vector wish, fwd, rgt;

	if (p.classname != "player" || p.movetype == MOVETYPE_NOCLIP || p.movetype == MOVETYPE_NONE || Veh_Driving (p) || Veh_Riding (p) || intermission_running)
	{
		p.spruce_swim_grav = FALSE;
		if (p.spruce_in_water)
		{
			p.spruce_in_water = FALSE;
			if (p.gravity == 0.04)
				p.gravity = 1;
		}
		if (p.spruce_cshift_on)
		{
			p.spruce_cshift_on = FALSE;
			if (p.ishuman)
				stuffcmd (p, "v_cshift 0 0 0 0\n");
		}
		return;
	}

	feet_z = p.origin_z + p.mins_z;
	eye_z = p.origin_z + p.view_ofs_z;
	lvl = 0;
	surf_z = -9999;

	// Check intact Water Tower interior chamber (only when a map actually has a water tower controller)
	if (spruce_wt_ctrl != world && spruce_wt_state == WT_STATE_INTACT && p.origin_z >= WT_TANK_Z_BOT - 8 && p.origin_z <= WT_TANK_Z_TOP)
	{
		dx = p.origin_x - WT_CENTER_X;
		dy = p.origin_y - WT_CENTER_Y;
		r2 = dx * dx + dy * dy;
		if (r2 < WT_TANK_R_IN * WT_TANK_R_IN)
			surf_z = WT_TANK_Z_SURF;
	}

	// Check active neighborhood flood water
	if (spruce_flood_z > 8 && feet_z < spruce_flood_z)
	{
		if (spruce_flood_z > surf_z)
			surf_z = spruce_flood_z;
	}

	if (surf_z > -9000 && feet_z < surf_z)
	{
		if (eye_z < surf_z)
			lvl = 3;
		else if (p.origin_z + 2 < surf_z)
			lvl = 2;
		else
			lvl = 1;
	}

	if (lvl > 0)
	{
		if (lvl > p.waterlevel)
		{
			p.waterlevel = lvl;
			p.watertype = CONTENT_WATER;
		}
		if (!p.spruce_in_water)
		{
			p.spruce_in_water = TRUE;
			if (p.velocity_z < -120)
				sound (p, CHAN_BODY, "player/inh2o.wav", 0.9, ATTN_NORM);
			particle (p.origin, '0 0 60', 42, 18);
		}
	}
	else if (p.spruce_in_water)
	{
		p.spruce_in_water = FALSE;
		p.gravity = 1;
	}

	if (lvl >= 2 && p.health > 0)
	{
		// Buoyant low-gravity 3D swimming so both tank and flooded streets feel fluid
		p.spruce_swim_grav = TRUE;
		p.gravity = 0.04;
		if (p.flags & FL_ONGROUND)
		{
			if (p.button2 || p.v_angle_x < -12)
				p.flags = p.flags - FL_ONGROUND;
		}

		// Generous breath window inside tank / 14s flood while still drowning if submerged > 20s
		if (lvl < 3)
			p.air_finished = time + 18;

		makevectors (p.v_angle);
		fwd = v_forward;
		rgt = v_right;
		wish = '0 0 0';
		if (p.movement_x != 0 || p.movement_y != 0)
		{
			wish = fwd * p.movement_x + rgt * p.movement_y;
			if (vlen (wish) > 1)
				wish = normalize (wish) * 260;
		}
		if (p.button2)
			wish_z = wish_z + 210;

		p.velocity = p.velocity + (wish - p.velocity) * min (1, frametime * 4.5);
		// Gentle natural buoyancy lift near surface
		if (p.origin_z < surf_z - 14 && !p.button2 && fabs (p.movement_x) < 10)
			p.velocity_z = p.velocity_z + 40 * frametime;

		if ((p.button2 || vlen (wish) > 60) && time >= p.spruce_swim_snd_t)
		{
			p.spruce_swim_snd_t = time + 0.85;
			if (random () < 0.5)
				sound (p, CHAN_BODY, "misc/water1.wav", 0.65, ATTN_NORM);
			else
				sound (p, CHAN_BODY, "misc/water2.wav", 0.65, ATTN_NORM);
		}
	}
	else
	{
		p.spruce_swim_grav = FALSE;
		if (p.spruce_in_water == FALSE && p.gravity == 0.04)
			p.gravity = 1;
	}

	if (lvl >= 3 && p.health > 0)
	{
		if (!p.spruce_cshift_on)
		{
			p.spruce_cshift_on = TRUE;
			if (p.ishuman)
				stuffcmd (p, "v_cshift 18 92 132 108\n");
		}
	}
	else if (p.spruce_cshift_on)
	{
		p.spruce_cshift_on = FALSE;
		if (p.ishuman)
			stuffcmd (p, "v_cshift 0 0 0 0\n");
	}
};

// ============================================================================
// 2. BREACH LEAK STREAMS & LOCALIZED 5-ROCKET HOLE TRACKING
// ============================================================================

void() Spruce_ClearBreaches =
{
	local entity e, nxt;

	e = nextent (world);
	while (e != world)
	{
		nxt = nextent (e);
		if (e.classname == "spruce_breach_node")
			remove (e);
		e = nxt;
	}
	spruce_wt_breaches = 0;
	spruce_wt_post_hits = 0;
};

void() Spruce_BreachThink =
{
	local vector org, outv, v0, p1, p2, p3, p4, gpos;
	local float t1, t2, t3, t4;
	local entity p;

	if (spruce_wt_state != WT_STATE_INTACT)
	{
		remove (self);
		return;
	}

	self.nextthink = time + 0.06;
	org = self.origin;
	outv = self.wt_node_out;

	// Parabolic pressurized waterfall cascade pouring from breached hole down to compound splash pool
	v0 = outv * 255 + '0 0 36';
	t1 = 0.25;
	t2 = 0.52;
	t3 = 0.80;
	t4 = 1.08;

	p1 = org + v0 * t1 - '0 0 380' * (t1 * t1);
	p2 = org + v0 * t2 - '0 0 380' * (t2 * t2);
	p3 = org + v0 * t3 - '0 0 380' * (t3 * t3);
	p4 = org + v0 * t4 - '0 0 380' * (t4 * t4);
	p1_z = max (16, p1_z);
	p2_z = max (16, p2_z);
	p3_z = max (16, p3_z);
	p4_z = max (16, p4_z);

	pointparticles (spruce_fx_waterjet, org, v0, 2);
	pointparticles (spruce_fx_waterjet, p1, outv * 235 + '0 0 -180', 1);
	pointparticles (spruce_fx_waterjet, p2, outv * 210 + '0 0 -380', 1);
	pointparticles (spruce_fx_waterjet, p3, outv * 180 + '0 0 -560', 1);
	pointparticles (spruce_fx_waterjet, p4, outv * 140 + '0 0 -680', 1);
	particle (org, outv * 220, 42, 16);
	particle (org, '0 0 20', 0, 8);	// Dark jagged breach cavity smoke puff

	// Boiling whitewater splash pool on ground below the cascade
	gpos = org + outv * 270;
	gpos_z = 14;
	pointparticles (spruce_fx_tidalfoam, gpos, '0 0 125', 1);
	particle (gpos, '0 0 110', 42, 14);

	if (time >= self.wt_node_fx_t)
	{
		self.wt_node_fx_t = time + 0.5;
		if (random () < 0.5)
			sound (self, CHAN_VOICE, "misc/water1.wav", 0.85, ATTN_NORM);
		else
			sound (self, CHAN_VOICE, "misc/water2.wav", 0.85, ATTN_NORM);

		p = bm_player_head;
		while (p)
		{
			if (p.health > 0 && vlen (p.origin - gpos) < 130)
			{
				p.velocity = p.velocity + outv * 190 + '0 0 150';
				p.flags = p.flags - (p.flags & FL_ONGROUND);
			}
			p = p.bm_player_next;
		}
	}
};

void() Spruce_TriggerCollapse =
{
	local vector borg, ctr;
	local float i;

	if (spruce_wt_state != WT_STATE_INTACT)
		return;

	spruce_wt_state = WT_STATE_TOPPLE;
	spruce_wt_phase_t0 = time;
	spruce_wt_topple_beat = 0;
	Spruce_ClearBreaches ();

	if (spruce_wt_legs)
	{
		spruce_wt_legs.takedamage = DAMAGE_NO;
		spruce_wt_legs.solid = SOLID_NOT;
	}
	if (spruce_wt_catwalk)
	{
		spruce_wt_catwalk.takedamage = DAMAGE_NO;
		spruce_wt_catwalk.solid = SOLID_NOT;
	}
	if (spruce_wt_tank)
	{
		spruce_wt_tank.takedamage = DAMAGE_NO;
		spruce_wt_tank.solid = SOLID_NOT;
	}
	if (spruce_wt_water)
		spruce_wt_water.model = string_null;

	ctr = WT_CENTER_X * '1 0 0' + WT_CENTER_Y * '0 1 0';
	// Initial base demolition bursts + flying steel shrapnel
	for (i = 0; i < 3; i = i + 1)
	{
		borg = ctr;
		borg_x = borg_x + (random () - 0.5) * 320;
		borg_y = borg_y + (random () - 0.5) * 320;
		borg_z = 90 + random () * 160;
		te_explosion (borg);
		Spruce_SpawnShrapnelBurst (borg, normalize (borg - ctr + '0 0 80'), 3, 420);
	}
	sound (spruce_wt_ctrl, CHAN_VOICE, "vehicles/car_boom2.wav", 1, ATTN_NONE);
	sound (spruce_wt_ctrl, CHAN_BODY, "weapons/r_exp3.wav", 1, ATTN_NONE);
	Spruce_ShockShake (ctr + '0 0 360', 3400, 240);
	Spruce_CenterprintAll ("THE WATER TOWER IS GOING DOWN!");

	spruce_wt_ctrl.nextthink = time + 0.05;
};

void(entity wtpart, vector hit_org, entity inflictor, entity attacker, float damage) Spruce_TowerHit =
{
	local vector rad, cl_org;
	local entity e, match;
	local float best_d, d, r_surf;

	if (spruce_wt_state != WT_STATE_INTACT)
		return;
	if (!wtpart)
		return;

	wtpart.health = 99999;

	// Only heavy explosive rockets count toward structural breaching
	if (inflictor == world)
		return;
	if (inflictor.classname != "missile" && inflictor.classname != "jimrocket" && damage < 65)
	{
		if (time >= wtpart.wt_node_fx_t)
		{
			wtpart.wt_node_fx_t = time + 0.12;
			te_spark (hit_org, '0 0 40', 8);
			sound (wtpart, CHAN_BODY, "vehicles/hit_metal1.wav", 0.7, ATTN_NORM);
		}
		return;
	}

	// Deduplicate single rocket touching + splashing in the same frame
	if (inflictor == spruce_last_rocket && spruce_last_rocket_t == time)
		return;
	spruce_last_rocket = inflictor;
	spruce_last_rocket_t = time;

	te_spark (hit_org, '0 0 80', 18);
	sound (wtpart, CHAN_BODY, "vehicles/clang1.wav", 0.85, ATTN_NORM);

	// Stage 2: Once at least one breach is leaking, continued rocket hits trigger full collapse
	if (spruce_wt_breaches >= 1)
	{
		spruce_wt_post_hits = spruce_wt_post_hits + 1;
		if (spruce_wt_post_hits == 3)
			Spruce_CenterprintAll ("Water tower legs buckling! Keep shooting!");
		else if (spruce_wt_post_hits == 5)
			Spruce_CenterprintAll ("Water tower about to collapse!");
		if (spruce_wt_post_hits >= WT_POST_HITS_COLLAPSE)
		{
			Spruce_TriggerCollapse ();
			return;
		}
	}

	// Track localized rocket clusters on the tank (or upper catwalk rim right around tank)
	if (wtpart != spruce_wt_tank && !(wtpart == spruce_wt_catwalk && hit_org_z >= 720))
		return;

	rad = hit_org - (WT_CENTER_X * '1 0 0' + WT_CENTER_Y * '0 1 0' + hit_org_z * '0 0 1');
	rad_z = 0;
	if (vlen (rad) < 8)
		rad = '1 0 0';
	else
		rad = normalize (rad);

	cl_org = hit_org;
	cl_org_z = max (760, min (1200, hit_org_z));

	match = world;
	best_d = 96;
	e = nextent (world);
	while (e != world)
	{
		if (e.classname == "spruce_breach_node")
		{
			d = vlen (e.origin - cl_org);
			if (d < best_d)
			{
				best_d = d;
				match = e;
			}
		}
		e = nextent (e);
	}

	if (match == world)
	{
		r_surf = 266;
		if (cl_org_z < 864)
			r_surf = 252;
		match = spawn ();
		match.classname = "spruce_breach_node";
		match.movetype = MOVETYPE_NONE;
		match.solid = SOLID_NOT;
		setorigin (match, WT_CENTER_X * '1 0 0' + WT_CENTER_Y * '0 1 0' + cl_org_z * '0 0 1' + rad * r_surf);
		match.wt_node_out = rad;
		match.wt_node_hits = 1;
		match.wt_node_breached = FALSE;
	}
	else
	{
		match.wt_node_hits = match.wt_node_hits + 1;
	}

	if (!match.wt_node_breached)
	{
		if (match.wt_node_hits == 3 && spruce_wt_breaches == 0)
			Spruce_CenterprintAll ("Tank hull cracking at that spot (3/5 rockets)...");
		if (match.wt_node_hits >= 5)
		{
			match.wt_node_breached = TRUE;
			spruce_wt_breaches = spruce_wt_breaches + 1;
			te_explosion (match.origin);
			pointparticles (spruce_fx_tidalfoam, match.origin, match.wt_node_out * 280, 2);
			particle (match.origin, match.wt_node_out * 240, 42, 56);
			sound (match, CHAN_VOICE, "vehicles/car_boom1.wav", 0.95, ATTN_NORM);
			sound (match, CHAN_AUTO, "vehicles/clang2.wav", 1, ATTN_NORM);
			Spruce_SpawnShrapnelBurst (match.origin, match.wt_node_out, 6, 360);
			match.think = Spruce_BreachThink;
			match.nextthink = time + 0.05;
			Spruce_CenterprintAll ("HULL BREACHED! Keep shooting to bring the tower down!");
		}
	}
};

// Explicit proximity catch from T_MissileTouch so rockets hitting catwalk clips,
// non-solid lower bowl, central riser, or skimming within ~32-40u reliably count!
void(entity inflictor, entity attacker, float damage, entity direct_other) Spruce_CheckRocketSplash =
{
	local float dx, dy, r, z;
	local entity wtpart;

	if (spruce_wt_state != WT_STATE_INTACT || inflictor == world)
		return;
	if (inflictor == spruce_last_rocket && spruce_last_rocket_t == time)
		return;

	dx = inflictor.origin_x - WT_CENTER_X;
	dy = inflictor.origin_y - WT_CENTER_Y;
	r = sqrt (dx * dx + dy * dy);
	z = inflictor.origin_z;

	wtpart = world;
	if (direct_other == spruce_wt_tank || direct_other == spruce_wt_catwalk || direct_other == spruce_wt_legs)
	{
		wtpart = direct_other;
	}
	else if (z >= 720 && z <= 1280 && r <= 365)
	{
		if (r <= 300 || z >= 918)
			wtpart = spruce_wt_tank;
		else
			wtpart = spruce_wt_catwalk;
	}
	else if (z >= 20 && z < 720 && r <= 385)
	{
		// Match central riser pipe (r <= 68) or battered leg lattice cone (r ~ 342 -> 246)
		if (r <= 68 || fabs (r - (342 - (z / 864) * 96)) <= 48)
			wtpart = spruce_wt_legs;
	}

	if (wtpart != world)
		Spruce_TowerHit (wtpart, inflictor.origin, inflictor, attacker, damage);
};

// ============================================================================
// 3. LIVELY COMEDIC CONSTRUCTION WORKER CREW DURING 22s REBUILD
// ============================================================================

void() Spruce_SpawnWorkerCrew;

void(entity attacker, float damage) Spruce_WorkerPain =
{
	self.wt_worker_panic_t = time + 3.0;
	if (random () < 0.5)
		sound (self, CHAN_VOICE, "random_npcs/randguy_panic.wav", 0.9, ATTN_NORM);
	else
		sound (self, CHAN_VOICE, "random_npcs/afroguy_panic.wav", 0.9, ATTN_NORM);
};

void() Spruce_WorkerDie =
{
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	sound (self, CHAN_VOICE, "player/udeath.wav", 1, ATTN_NORM);
	ThrowHead ("progs/gib1.mdl", self.health);
	ThrowGib ("progs/gib2.mdl", self.health);
	ThrowGib ("progs/gib3.mdl", self.health);
	// Rebuild NEVER stalls: mark removed so backup worker spawns if needed
	remove (self);
};

void() Spruce_WorkerThink =
{
	local vector target_pos, d;
	local float ang, f;

	if (spruce_wt_state != WT_STATE_REBUILD)
	{
		remove (self);
		return;
	}

	self.nextthink = time + 0.1;
	ang = 195 + self.wt_worker_slot * 45;
	makevectors ('0 1 0' * ang);
	target_pos = (WT_CENTER_X * '1 0 0' + WT_CENTER_Y * '0 1 0') + v_forward * 338 + '0 0 28';

	// Panic sprint temporarily when shot near/hit
	if (time < self.wt_worker_panic_t)
	{
		self.angles_y = self.angles_y + 25;
		makevectors ('0 1 0' * self.angles_y);
		walkmove (self.angles_y, 22);
		self.wt_worker_anim = self.wt_worker_anim + 1;
		f = self.wt_worker_anim - 10 * floor (self.wt_worker_anim / 10);
		self.frame = 20 + f;
		return;
	}

	d = target_pos - self.origin;
	d_z = 0;
	if (vlen (d) > 36)
	{
		self.angles_y = vectoyaw (d);
		if (!walkmove (self.angles_y, 18))
			walkmove (self.angles_y + 50, 18);
		self.wt_worker_anim = self.wt_worker_anim + 1;
		f = self.wt_worker_anim - 10 * floor (self.wt_worker_anim / 10);
		self.frame = 20 + f;
	}
	else
	{
		// Face tower center and hammer/weld with sparks!
		self.angles_y = vectoyaw ((WT_CENTER_X * '1 0 0' + WT_CENTER_Y * '0 1 0') - self.origin);
		makevectors ('0 1 0' * self.angles_y);
		self.wt_worker_anim = self.wt_worker_anim + 1;
		f = self.wt_worker_anim - 10 * floor (self.wt_worker_anim / 10);
		self.frame = 30 + f;
		if (time >= self.wt_worker_snd_t)
		{
			self.wt_worker_snd_t = time + 0.8 + random () * 0.8;
			te_spark (self.origin + v_forward * 28 + '0 0 24', '0 0 60', 14);
			if (random () < 0.5)
				sound (self, CHAN_BODY, "vehicles/clang1.wav", 0.75, ATTN_NORM);
			else
				sound (self, CHAN_BODY, "vehicles/clang2.wav", 0.75, ATTN_NORM);
		}
	}
};

void(float slot) Spruce_SpawnOneWorker =
{
	local entity w;
	local vector start_pos;
	local float k;

	w = spawn ();
	w.classname = "npc_spruce_worker";
	w.wt_worker_slot = slot;
	k = slot - 3 * floor (slot / 3);
	if (k == 0)
	{
		setmodel (w, "progs/npc_randguy.md3");
		w.colormod = '1.8 0.92 0.22';
	}
	else if (k == 1)
	{
		setmodel (w, "progs/npc_afroguy.md3");
		w.colormod = '1.7 1.4 0.25';
	}
	else
	{
		setmodel (w, "progs/npc_fatguy.md3");
		w.colormod = '1.85 0.78 0.18';
	}
	w.solid = SOLID_BBOX;
	w.movetype = MOVETYPE_STEP;
	setsize (w, '-16 -16 -24', '16 16 32');
	w.health = 75;
	w.takedamage = DAMAGE_AIM;
	w.th_pain = Spruce_WorkerPain;
	w.th_die = Spruce_WorkerDie;

	// Enter on clear gravel apron south-southwest of tower legs
	start_pos_x = -1520 + slot * 110;
	start_pos_y = 5100 + random () * 50;
	start_pos_z = 32;
	setorigin (w, start_pos);
	local entity oldself;
	oldself = self;
	self = w;
	droptofloor ();
	self = oldself;
	w.think = Spruce_WorkerThink;
	w.nextthink = time + 0.1 + slot * 0.12;
};

void() Spruce_SpawnWorkerCrew =
{
	local float i;
	for (i = 0; i < 4; i = i + 1)
		Spruce_SpawnOneWorker (i);
};

// ============================================================================
// 4. TIDAL WAVE WALLS & MASTER STATE MACHINE: TOPPLE -> WAVE -> FLOOD -> DRAIN -> REBUILD
// ============================================================================

void(entity w) Spruce_HideWave =
{
	if (!w)
		return;
	w.model = string_null;
	setorigin (w, w.pos1);
};

void(entity w, vector offset) Spruce_MoveWave =
{
	if (!w)
		return;
	if (w.model == string_null)
		setmodel (w, w.mdl);
	setorigin (w, w.pos1 + '0 0 1' * WT_WAVE_LIFT_Z + offset);
};

void(float dist) Spruce_UpdateWaveSweep =
{
	local float k, off;
	local vector pos;
	local entity p;
	local vector push;

	Spruce_MoveWave (spruce_wave_n_ent, '0 1 0' * dist);
	Spruce_MoveWave (spruce_wave_s_ent, '0 -1 0' * dist);
	Spruce_MoveWave (spruce_wave_e_ent, '1 0 0' * dist);
	Spruce_MoveWave (spruce_wave_w_ent, '-1 0 0' * dist);

	// Emit foaming breaker crests along all 4 advancing wave fronts
	for (k = -2; k <= 2; k = k + 1)
	{
		off = k * 900;
		pos_z = 48;

		// North (+Y)
		pos_x = WT_CENTER_X + off;
		pos_y = WT_CENTER_Y + dist + 200;
		pointparticles (spruce_fx_tidalfoam, pos, '0 320 140', 1);

		// South (-Y)
		pos_y = WT_CENTER_Y - dist - 200;
		pointparticles (spruce_fx_tidalfoam, pos, '0 -320 140', 1);

		// East (+X)
		pos_x = WT_CENTER_X + dist + 200;
		pos_y = WT_CENTER_Y + off;
		pointparticles (spruce_fx_tidalfoam, pos, '320 0 140', 1);

		// West (-X)
		pos_x = WT_CENTER_X - dist - 200;
		pointparticles (spruce_fx_tidalfoam, pos, '-320 0 140', 1);
	}

	if (time >= spruce_wt_wave_snd_t)
	{
		spruce_wt_wave_snd_t = time + 0.45;
		if (random () < 0.5)
			sound (spruce_wt_ctrl, CHAN_VOICE, "misc/water1.wav", 1, ATTN_NONE);
		else
			sound (spruce_wt_ctrl, CHAN_AUTO, "misc/water2.wav", 1, ATTN_NONE);
	}

	// Push & splash players struck by an advancing tidal wave wall
	p = bm_player_head;
	while (p)
	{
		if (p.health > 0 && p.movetype != MOVETYPE_NOCLIP && p.origin_z < 175 && time >= p.spruce_wave_hit_t)
		{
			push = '0 0 0';
			if (fabs (p.origin_y - (WT_CENTER_Y + dist + 140)) < 170 && fabs (p.origin_x - WT_CENTER_X) < 5000)
				push = '0 380 210';
			else if (fabs (p.origin_y - (WT_CENTER_Y - dist - 140)) < 170 && fabs (p.origin_x - WT_CENTER_X) < 5000)
				push = '0 -380 210';
			else if (fabs (p.origin_x - (WT_CENTER_X + dist + 140)) < 170 && p.origin_y > WT_CENTER_Y - 5700 && p.origin_y < WT_CENTER_Y + 3800)
				push = '380 0 210';
			else if (fabs (p.origin_x - (WT_CENTER_X - dist - 140)) < 170 && p.origin_y > WT_CENTER_Y - 5700 && p.origin_y < WT_CENTER_Y + 3800)
				push = '-380 0 210';

			if (vlen (push) > 10)
			{
				p.spruce_wave_hit_t = time + 1.5;
				p.velocity = p.velocity + push;
				p.flags = p.flags - (p.flags & FL_ONGROUND);
				sound (p, CHAN_BODY, "player/h2ojump.wav", 1, ATTN_NORM);
				particle (p.origin, '0 0 90', 42, 24);
				pointparticles (spruce_fx_tidalfoam, p.origin, push * 0.6, 1);
				if (p.ishuman)
				{
					p.punchangle_x = p.punchangle_x + (random () - 0.5) * 14;
					p.punchangle_z = p.punchangle_z + (random () - 0.5) * 12;
				}
			}
		}
		p = p.bm_player_next;
	}
};

void() Spruce_ResetTowerIntact =
{
	spruce_wt_state = WT_STATE_INTACT;
	spruce_wt_breaches = 0;
	spruce_wt_post_hits = 0;
	spruce_flood_z = 0;

	if (spruce_flood_ent)
		setorigin (spruce_flood_ent, spruce_flood_ent.pos1);

	Spruce_HideWave (spruce_wave_n_ent);
	Spruce_HideWave (spruce_wave_s_ent);
	Spruce_HideWave (spruce_wave_e_ent);
	Spruce_HideWave (spruce_wave_w_ent);

	if (spruce_wt_legs)
	{
		spruce_wt_legs.angles = '0 0 0';
		setorigin (spruce_wt_legs, spruce_wt_legs.pos1);
		spruce_wt_legs.solid = SOLID_BSP;
		spruce_wt_legs.takedamage = DAMAGE_AIM;
		spruce_wt_legs.health = 99999;
		Spruce_NudgePlayersClear (spruce_wt_legs);
	}
	if (spruce_wt_catwalk)
	{
		spruce_wt_catwalk.angles = '0 0 0';
		setorigin (spruce_wt_catwalk, spruce_wt_catwalk.pos1);
		spruce_wt_catwalk.solid = SOLID_BSP;
		spruce_wt_catwalk.takedamage = DAMAGE_AIM;
		spruce_wt_catwalk.health = 99999;
		Spruce_NudgePlayersClear (spruce_wt_catwalk);
	}
	if (spruce_wt_tank)
	{
		spruce_wt_tank.angles = '0 0 0';
		setorigin (spruce_wt_tank, spruce_wt_tank.pos1);
		spruce_wt_tank.solid = SOLID_BSP;
		spruce_wt_tank.takedamage = DAMAGE_AIM;
		spruce_wt_tank.health = 99999;
		Spruce_NudgePlayersClear (spruce_wt_tank);
	}
	if (spruce_wt_water)
	{
		setmodel (spruce_wt_water, spruce_wt_water.mdl);
		setorigin (spruce_wt_water, spruce_wt_water.pos1);
		spruce_wt_water.angles = '0 0 0';
	}
};

void() Spruce_TowerThink =
{
	local float dt, frac, u, deg, wcnt, beat_t, i;
	local vector tilt, spark_org, borg, ctr, slam_org;
	local entity e;

	self.nextthink = time + 0.05;

	if (spruce_wt_state == WT_STATE_INTACT)
	{
		self.nextthink = time + 0.25;
		return;
	}

	dt = time - spruce_wt_phase_t0;
	ctr = WT_CENTER_X * '1 0 0' + WT_CENTER_Y * '0 1 0';

	// PHASE 1: 2.6s Multi-Beat Cinematic Collapse (0..0.9s climbing explosions + creak, 0.9..2.6s accelerating topple)
	if (spruce_wt_state == WT_STATE_TOPPLE)
	{
		if (dt < WT_TOPPLE_CREAK_T)
		{
			u = dt / WT_TOPPLE_CREAK_T;
			deg = 14 * (u * u);

			// Sequential base/leg explosions climbing up the steel lattice
			beat_t = 0.20 + spruce_wt_topple_beat * 0.22;
			if (spruce_wt_topple_beat < 4 && dt >= beat_t)
			{
				spruce_wt_topple_beat = spruce_wt_topple_beat + 1;
				borg = ctr;
				borg_x = borg_x + (random () - 0.5) * 280;
				borg_y = borg_y + (random () - 0.5) * 280;
				borg_z = 140 + spruce_wt_topple_beat * 155;
				te_explosion (borg);
				pointparticles (spruce_fx_vehexplode, borg, '0 0 0', 1);
				Spruce_SpawnShrapnelBurst (borg, normalize (borg - ctr + '0 0 60'), 3, 460);
				if (random () < 0.5)
					sound (self, CHAN_VOICE, "vehicles/car_boom1.wav", 1, ATTN_NONE);
				else
					sound (self, CHAN_VOICE, "vehicles/car_boom2.wav", 1, ATTN_NONE);
				sound (self, CHAN_AUTO, "weapons/r_exp3.wav", 0.9, ATTN_NONE);
				Spruce_ShockShake (borg, 3000, 150);
			}
		}
		else
		{
			u = min (1, (dt - WT_TOPPLE_CREAK_T) / WT_TOPPLE_FALL_T);
			deg = 14 + 72 * (u * u);
		}

		tilt = '0 0 0';
		tilt_x = deg;
		tilt_z = (deg / 86) * 12;

		if (spruce_wt_legs) spruce_wt_legs.angles = tilt;
		if (spruce_wt_catwalk) spruce_wt_catwalk.angles = tilt;
		if (spruce_wt_tank) spruce_wt_tank.angles = tilt;

		// Trailing water & steam bursts spraying out the falling tank & open hatch
		if (dt >= WT_TOPPLE_CREAK_T)
		{
			makevectors (tilt);
			slam_org = ctr + v_up * 960;
			slam_org_z = max (80, slam_org_z);
			pointparticles (spruce_fx_waterjet, slam_org, v_up * 180 + '0 0 -120', 1);
			pointparticles (spruce_fx_tidalfoam, slam_org, '0 0 90', 1);
			particle (slam_org, '0 0 100', 42, 18);
		}

		if (dt >= WT_TOPPLE_TOTAL_T)
		{
			// Slam Impact: giant fireball shockwave + launch 3D radial tidal waves!
			makevectors (tilt);
			slam_org = ctr + v_up * 720;
			slam_org_z = 64;

			for (i = 0; i < 5; i = i + 1)
			{
				borg = slam_org;
				borg_x = borg_x + (random () - 0.5) * 520;
				borg_y = borg_y + (random () - 0.5) * 520;
				borg_z = 48 + random () * 110;
				te_explosion (borg);
				pointparticles (spruce_fx_vehexplode, borg, '0 0 0', 1);
			}
			Spruce_SpawnShrapnelBurst (slam_org, '0 0 1', 10, 560);

			spruce_wt_state = WT_STATE_FLOODING;
			spruce_wt_phase_t0 = time;
			spruce_wt_wave_dist = 0;
			spruce_wt_wave_snd_t = 0;
			spruce_wt_flood_warn = 0;
			Spruce_UpdateWaveSweep (0);
			Spruce_ShockShake (slam_org, 6500, 420);
			sound (self, CHAN_VOICE, "weapons/r_exp3.wav", 1, ATTN_NONE);
			sound (self, CHAN_AUTO, "vehicles/car_boom2.wav", 1, ATTN_NONE);
			sound (self, CHAN_BODY, "player/inh2o.wav", 1, ATTN_NONE);
			Spruce_CenterprintAll ("TIDAL WAVE! Neighborhood flooding for 14 seconds!");
		}
		return;
	}

	// PHASE 2: 3.5s Sweeping 3D Tidal Wave Walls (`1250 u/s`) + Rising Flood Water Behind Wave (`0 -> 76u`)
	if (spruce_wt_state == WT_STATE_FLOODING)
	{
		frac = min (1, dt / WT_WAVE_DURATION);
		spruce_wt_wave_dist = dt * WT_WAVE_SPEED;
		Spruce_UpdateWaveSweep (spruce_wt_wave_dist);

		spruce_flood_z = WT_FLOOD_DEPTH * frac;
		if (spruce_flood_ent)
			setorigin (spruce_flood_ent, spruce_flood_ent.pos1 + '0 0 1' * (spruce_flood_z + 5));

		if (frac >= 1)
		{
			Spruce_HideWave (spruce_wave_n_ent);
			Spruce_HideWave (spruce_wave_s_ent);
			Spruce_HideWave (spruce_wave_e_ent);
			Spruce_HideWave (spruce_wave_w_ent);
			spruce_wt_state = WT_STATE_FLOODED;
			spruce_wt_phase_t0 = time;
			spruce_flood_z = WT_FLOOD_DEPTH;
		}
		return;
	}

	// PHASE 3: 14 Seconds Flooded (~6.3 ft deep)
	if (spruce_wt_state == WT_STATE_FLOODED)
	{
		spruce_flood_z = WT_FLOOD_DEPTH;
		if (dt >= WT_FLOOD_HOLD_T)
		{
			spruce_wt_state = WT_STATE_DRAINING;
			spruce_wt_phase_t0 = time;
			Spruce_CenterprintAll ("Floodwaters draining... Construction crew inbound!");
		}
		else if (spruce_wt_flood_warn == 0 && (WT_FLOOD_HOLD_T - dt) <= 5)
		{
			spruce_wt_flood_warn = 1;
			Spruce_CenterprintAll ("Flood draining in 5s...");
		}
		return;
	}

	// PHASE 4: 2.5s Drain + Reset Parts Underground for Growing Rebuild
	if (spruce_wt_state == WT_STATE_DRAINING)
	{
		frac = min (1, dt / WT_DRAIN_DURATION);
		spruce_flood_z = WT_FLOOD_DEPTH * (1 - frac);
		if (spruce_flood_ent)
			setorigin (spruce_flood_ent, spruce_flood_ent.pos1 + '0 0 1' * max (0, spruce_flood_z + 5));
		if (frac >= 1)
		{
			spruce_flood_z = 0;
			if (spruce_flood_ent)
				setorigin (spruce_flood_ent, spruce_flood_ent.pos1);
			spruce_wt_state = WT_STATE_REBUILD;
			spruce_wt_phase_t0 = time;

			// Tuck tower stages underground upright relative to pos1 so they smoothly grow upward!
			if (spruce_wt_legs)
			{
				spruce_wt_legs.angles = '0 0 0';
				setorigin (spruce_wt_legs, spruce_wt_legs.pos1 + '0 0 -900');
			}
			if (spruce_wt_catwalk)
			{
				spruce_wt_catwalk.angles = '0 0 0';
				setorigin (spruce_wt_catwalk, spruce_wt_catwalk.pos1 + '0 0 -1000');
			}
			if (spruce_wt_tank)
			{
				spruce_wt_tank.angles = '0 0 0';
				setorigin (spruce_wt_tank, spruce_wt_tank.pos1 + '0 0 -1360');
			}
			Spruce_SpawnWorkerCrew ();
			Spruce_CenterprintAll ("Construction crew rebuilding Water Tower...");
		}
		return;
	}

	// PHASE 5: 22s Visible Staged Growth + Welding Sparks + Backup Worker Check
	if (spruce_wt_state == WT_STATE_REBUILD)
	{
		// Tier 1 (0..8s): 8 steel legs & riser grow up from concrete footings
		if (dt <= 8)
		{
			frac = min (1, dt / 8);
			if (spruce_wt_legs)
				setorigin (spruce_wt_legs, spruce_wt_legs.pos1 + '0 0 -900' * (1 - frac));
		}
		else if (spruce_wt_legs && spruce_wt_legs.origin_z < spruce_wt_legs.pos1_z)
		{
			setorigin (spruce_wt_legs, spruce_wt_legs.pos1);
			spruce_wt_legs.solid = SOLID_BSP;
			Spruce_NudgePlayersClear (spruce_wt_legs);
		}

		// Tier 2 (7.5..15s): Bowl, catwalk & X-braced safety rails rise into lock
		if (dt >= 7.5 && dt <= 15)
		{
			frac = min (1, (dt - 7.5) / 7.5);
			if (spruce_wt_catwalk)
				setorigin (spruce_wt_catwalk, spruce_wt_catwalk.pos1 + '0 0 -1000' * (1 - frac));
		}
		else if (dt > 15 && spruce_wt_catwalk && spruce_wt_catwalk.origin_z < spruce_wt_catwalk.pos1_z)
		{
			setorigin (spruce_wt_catwalk, spruce_wt_catwalk.pos1);
			spruce_wt_catwalk.solid = SOLID_BSP;
			Spruce_NudgePlayersClear (spruce_wt_catwalk);
		}

		// Tier 3 (14..21.5s): White steel tank belly, dome crown & finial rise + fill!
		if (dt >= 14 && dt <= 21.5)
		{
			frac = min (1, (dt - 14) / 7.5);
			if (spruce_wt_tank)
				setorigin (spruce_wt_tank, spruce_wt_tank.pos1 + '0 0 -1360' * (1 - frac));
		}

		// Welding spark cascades on rising structure + backup worker check if crew got gibbed
		if (time >= spruce_wt_rebuild_snd_t)
		{
			spruce_wt_rebuild_snd_t = time + 0.5;
			spark_org_x = WT_CENTER_X + (random () - 0.5) * 420;
			spark_org_y = WT_CENTER_Y + (random () - 0.5) * 420;
			spark_org_z = 80 + min (1, dt / 21.5) * 950;
			te_spark (spark_org, '0 0 90', 18);

			wcnt = 0;
			e = nextent (world);
			while (e != world)
			{
				if (e.classname == "npc_spruce_worker")
					wcnt = wcnt + 1;
				e = nextent (e);
			}
			if (wcnt < 2 && dt < 19)
				Spruce_SpawnOneWorker (floor (random () * 4));
		}

		if (dt >= WT_REBUILD_DURATION)
		{
			Spruce_ResetTowerIntact ();
			sound (self, CHAN_VOICE, "vehicles/horn.wav", 1, ATTN_NONE);
			Spruce_CenterprintAll ("WATER TOWER RESTORED! Climb up or blow it down!");
		}
	}
};

// ============================================================================
// 5. MAP ENTITY SPAWN FUNCTIONS
// ============================================================================

void(entity attacker, float damage) wt_part_pain =
{
	self.health = 99999;
};

void() wt_part_die =
{
	self.health = 99999;
};

void() wt_part_legs =
{
	SpruceTower_Precache ();
	self.solid = SOLID_BSP;
	self.movetype = MOVETYPE_PUSH;
	setmodel (self, self.model);
	self.mdl = self.model;
	self.pos1 = self.origin;
	setorigin (self, self.pos1);
	self.takedamage = DAMAGE_AIM;
	self.health = 99999;
	self.th_pain = wt_part_pain;
	self.th_die = wt_part_die;
	spruce_wt_legs = self;
};

void() wt_part_catwalk =
{
	SpruceTower_Precache ();
	self.solid = SOLID_BSP;
	self.movetype = MOVETYPE_PUSH;
	setmodel (self, self.model);
	self.mdl = self.model;
	self.pos1 = self.origin;
	setorigin (self, self.pos1);
	self.takedamage = DAMAGE_AIM;
	self.health = 99999;
	self.th_pain = wt_part_pain;
	self.th_die = wt_part_die;
	spruce_wt_catwalk = self;
};

void() wt_part_tank =
{
	SpruceTower_Precache ();
	self.solid = SOLID_BSP;
	self.movetype = MOVETYPE_PUSH;
	setmodel (self, self.model);
	self.mdl = self.model;
	self.pos1 = self.origin;
	setorigin (self, self.pos1);
	self.takedamage = DAMAGE_AIM;
	self.health = 99999;
	self.th_pain = wt_part_pain;
	self.th_die = wt_part_die;
	spruce_wt_tank = self;
};

void() wt_tank_water =
{
	SpruceTower_Precache ();
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NOCLIP;
	setmodel (self, self.model);
	self.mdl = self.model;
	self.pos1 = self.origin;
	setorigin (self, self.pos1);
	self.alpha = 0.62;
	spruce_wt_water = self;
};

void() spruce_flood_water =
{
	SpruceTower_Precache ();
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NOCLIP;
	setmodel (self, self.model);
	self.mdl = self.model;
	self.pos1 = self.origin;
	setorigin (self, self.pos1);
	self.alpha = 0.58;
	spruce_flood_ent = self;
};

void() Spruce_WaveSpawnInit =
{
	SpruceTower_Precache ();
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NOCLIP;
	setmodel (self, self.model);
	self.mdl = self.model;
	self.pos1 = self.origin;
	setorigin (self, self.pos1);
	self.alpha = 0.78;
	self.model = string_null;
};

void() spruce_wave_n =
{
	Spruce_WaveSpawnInit ();
	spruce_wave_n_ent = self;
};

void() spruce_wave_s =
{
	Spruce_WaveSpawnInit ();
	spruce_wave_s_ent = self;
};

void() spruce_wave_e =
{
	Spruce_WaveSpawnInit ();
	spruce_wave_e_ent = self;
};

void() spruce_wave_w =
{
	Spruce_WaveSpawnInit ();
	spruce_wave_w_ent = self;
};

void() misc_wt_controller =
{
	SpruceTower_Precache ();
	spruce_wt_ctrl = self;
	spruce_wt_state = WT_STATE_INTACT;
	spruce_flood_z = 0;
	spruce_wt_breaches = 0;
	spruce_wt_post_hits = 0;
	self.think = Spruce_TowerThink;
	self.nextthink = time + 0.5;
};
