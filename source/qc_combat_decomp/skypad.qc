#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
SKY LAUNCH PADS (skypad.qc)

High-arc cross-map launch pads (`info_skypad`) that throw players sky-high across downtown
from landmark to landmark along an exact ballistic parabola (`pos1` = landing player origin,
`height` = apex z in map units, `message` = destination name).

Raises `sv_maxvelocity` to 6500 so high cross-map velocities (~3800 u/s horizontal, ~2200 u/s
vertical) are never axis-clamped on either server or client prediction.
================
*/

// the launch needs a higher speed cap than stock; the value from before is kept in bm_maxvel_saved so that BM_Precache
// can put it back on the next map (it used to stay 6500 for the rest of the session, for every map)
void() SkyPad_RaiseMaxVel =
{
	if (cvar ("sv_maxvelocity") >= 6500)
		return;
	registercvar ("bm_maxvel_saved", "0");
	if (cvar ("bm_maxvel_saved") <= 0)
		cvar_set ("bm_maxvel_saved", cvar_string ("sv_maxvelocity"));
	cvar_set ("sv_maxvelocity", "6500");
};

void() SkyPad_Precache =
{
	if (skypad_precached)
		return;
	skypad_precached = TRUE;
	precache_model ("progs/turrbase.mdl");
	precache_model ("progs/ltg_aura.md3");
	precache_model ("progs/aura.md3");
	precache_model ("progs/laser.md3");
	precache_model ("progs/s_dotmed_yell.spr");
	precache_sound ("skypad/launch.wav");
	precache_sound ("weapons/turrset.wav");
};

vector(vector org, vector dst, float apex_z) SkyPad_CalcVel =
{
	local float g, top, vz, tf;
	local vector v;

	g = cvar ("sv_gravity");
	if (g <= 10)
		g = 800;
	top = apex_z;
	if (top < org_z + 256)
		top = org_z + 256;
	if (top < dst_z + 256)
		top = dst_z + 256;
	vz = sqrt (2 * g * (top - org_z));
	tf = (vz / g) + sqrt (2 * (top - dst_z) / g);
	if (tf < 0.2)
		tf = 0.2;
	v_x = (dst_x - org_x) / tf;
	v_y = (dst_y - org_y) / tf;
	v_z = vz;
	return v;
};

// Landing anti-camp shockwave when touching down from a cross-map SkyPad launch!
void() SkyPad_LandWave =
{
	local entity e;
	local vector d;

	pointparticles (particleeffectnum ("TE_TELEPORT"), self.origin - '0 0 18', '0 0 0', 1);
	e = findradius (self.origin, 175);
	while (e != world)
	{
		if (e != self && e.takedamage && e.health > 0 && e.solid == SOLID_SLIDEBOX)
		{
			d = e.origin - self.origin;
			d_z = 0;
			if (vlen (d) < 1)
				d = '1 0 0';
			else
				d = normalize (d);
			e.flags = e.flags - (e.flags & FL_ONGROUND);
			e.velocity = e.velocity + d * 380 + '0 0 220';
			T_Damage (e, self, self, 25);
		}
		e = e.chain;
	}
};

void(entity pad, entity jb) SkyPad_LaunchJohnBird =
{
	local entity pilot;
	local vector v;
	local float g, top, vz, tf;

	if (jb == world || jb.health <= 0 || jb.jb_dying)
		return;
	if (time < jb.skypad_cool_t)
		return;

	SkyPad_RaiseMaxVel ();
	pilot = jb.jb_pilot;
	if (pilot != world && pilot.ishuman == 1 && !pilot.skypad_vel_sent)
	{
		pilot.skypad_vel_sent = TRUE;
		stuffcmd (pilot, "sv_maxvelocity 6500\n");
	}

	jb.skypad_cool_t = time + 0.65;
	jb.flags = jb.flags - (jb.flags & FL_ONGROUND);
	setorigin (jb, jb.origin + '0 0 4');

	v = SkyPad_CalcVel (jb.origin, pad.pos1, pad.height);
	jb.velocity = v;

	g = cvar ("sv_gravity");
	if (g <= 10)
		g = 800;
	top = max (pad.height, max (jb.origin_z + 256, pad.pos1_z + 256));
	vz = sqrt (2 * g * (top - jb.origin_z));
	tf = (vz / g) + sqrt (2 * (top - pad.pos1_z) / g);
	jb.jb_skypad_until = time + bound (1.2, tf * 0.90, 3.8);
	jb.jb_swoop_until = time + 0.5;
	jb.jb_flap_t = time + 0.14;

	if (pilot != world)
		pilot.skypad_safe_t = time + 10.0;

	sound7 (jb, CHAN_AUTO, "skypad/launch.wav", 0.90, ATTN_NORM, SNDSPD * (0.96 + random () * 0.08));
	pointparticles (particleeffectnum ("TE_TELEPORT"), pad.origin + '0 0 12', '0 0 0', 1);
	JB_SpawnFeathers (jb.origin + '0 0 28', 10, 1.35);

	if (pad.message != "" && pilot != world && pilot.ishuman == 1)
		sprint (pilot, strcat ("Sky Pad -> ", pad.message, "\n"));
};

void(entity pad, entity rr) SkyPad_LaunchRocketRider =
{
	local entity pilot;
	local vector v;
	local float g, top, vz, tf;

	if (rr == world || rr.health <= 0 || rr.rr_dying)
		return;
	if (time < rr.skypad_cool_t)
		return;

	SkyPad_RaiseMaxVel ();
	pilot = rr.rr_pilot;
	if (pilot != world && pilot.ishuman == 1 && !pilot.skypad_vel_sent)
	{
		pilot.skypad_vel_sent = TRUE;
		stuffcmd (pilot, "sv_maxvelocity 6500\n");
	}

	rr.skypad_cool_t = time + 0.65;
	rr.flags = rr.flags - (rr.flags & FL_ONGROUND);
	setorigin (rr, rr.origin + '0 0 4');

	v = SkyPad_CalcVel (rr.origin, pad.pos1, pad.height);
	rr.velocity = v;

	g = cvar ("sv_gravity");
	if (g <= 10)
		g = 800;
	top = max (pad.height, max (rr.origin_z + 256, pad.pos1_z + 256));
	vz = sqrt (2 * g * (top - rr.origin_z));
	tf = (vz / g) + sqrt (2 * (top - pad.pos1_z) / g);
	rr.rr_skypad_until = time + bound (1.8, tf * 0.90, 3.8);

	if (pilot != world)
		pilot.skypad_safe_t = time + 10.0;

	sound7 (rr, CHAN_AUTO, "skypad/launch.wav", 0.92, ATTN_NORM, SNDSPD * (0.96 + random () * 0.08));
	sound (rr, CHAN_WEAPON, "john_bird/jb_flame_roar.wav", 1, 0.45);
	if (rr_fx_teleport > 0)
		pointparticles (rr_fx_teleport, pad.origin + '0 0 12', '0 0 0', 1);
	if (rr_fx_hairfire > 0)
		pointparticles (rr_fx_hairfire, rr.origin + '0 0 24', '0 0 90', 3);

	if (pad.message != "" && pilot != world && pilot.ishuman == 1)
		sprint (pilot, strcat ("Sky Pad -> ", pad.message, "\n"));
};

float(entity e) SkyPad_IsProjectile =
{
	local string c;

	if (!e || e == world || bm_wasfreed (e))
		return FALSE;
	c = e.classname;
	if (c == "ec_tube")
		return (e.ec_base != world && !bm_wasfreed (e.ec_base) && e.ec_base.ec_state == EC_STATE_FLYING);
	if (e.solid == SOLID_NOT)
		return FALSE;
	if (c == "fh_dead" || c == "mmdead")
		return FALSE;

	// Player / vehicle weapon projectiles
	if (c == "missile" || c == "grenade" || c == "spike" || c == "hiplaser" || c == "playershot" || c == "mm_tank_bar")
		return TRUE;
	if (c == "proximity_grenade")
		return (e.movetype != MOVETYPE_NONE && e.state == 0);
	if (c == "jb_bottle_proj" || c == "jb_aerosol_bomb" || c == "jb_whip_proj" || c == "jb_spray_glob")
		return TRUE;

	// Fun Guns & custom-steered projectiles / drones
	if (c == "megaman" || c == "wc_shot" || c == "netsend_disk" || c == "ltg_head")
		return TRUE;
	if (c == "kyle_proj")
		return (!e.ky_done && e.ky_mode != KY_MODE_DYING && e.ky_mode != KY_MODE_LATCHED);
	if (c == "milky")
		return (e.milky_hp > 0 && e.milky_emerged);
	if (c == "robdob")
		return (!e.fd_boom && !e.fd_blowing && e.health > 0);
	if (c == "dookie_shot")
		return (!e.dk_done);
	if (c == "dookie_glob" || c == "bigbanana" || c == "minibanana" || c == "greenjar_proj")
		return TRUE;
	if (c == "pickle")
		return (e.movetype != MOVETYPE_NONE);
	if (c == "greenguy_mini")
		return (e.gj_state != 4 && e.gj_state != 5 && e.health > 0);

	// Monster projectiles
	if (c == "wizspike" || c == "knightspike" || c == "knight2spike" || c == "gruntspike"
		|| c == "afritspike" || c == "furyspike" || c == "jimrocket" || c == "carniv_projectile"
		|| c == "slimeball" || c == "ShalrathMissile" || c == "Reiver_fireball"
		|| c == "ghost_follower" || c == "shamblerbeam" || c == "MiniGrenade"
		|| c == "hknight2_homing" || c == "yakman_projectile" || c == "skull"
		|| c == "skull_fly" || c == "face")
		return TRUE;

	return FALSE;
};

void(entity pad, entity e) SkyPad_LaunchProjectile =
{
	local vector v, hvel, ang;
	local string c;

	if (time < e.skypad_cool_t)
		return;

	SkyPad_RaiseMaxVel ();
	e.skypad_cool_t = time + 0.65;
	e.skypad_steer_t = time + 0.75;

	c = e.classname;
	if (c == "megaman" && e.mm_state != 0)
	{
		e.mm_state = 0;
		e.movetype = MOVETYPE_TOSS;
	}
	else if (c == "kyle_proj" && e.movetype == MOVETYPE_STEP)
	{
		e.movetype = MOVETYPE_TOSS;
		e.gravity = 0.48;
		e.ky_mode = KY_MODE_RUNNER;
	}

	if ((e.flags & FL_ONGROUND) || e.movetype == MOVETYPE_STEP || c == "wc_shot" || c == "greenguy_mini")
	{
		e.flags = e.flags - (e.flags & FL_ONGROUND);
		setorigin (e, e.origin + '0 0 4');
	}

	v = SkyPad_CalcVel (e.origin, pad.pos1, pad.height);
	e.velocity = v;
	hvel = v;
	hvel_z = 0;
	dprint (strcat ("skypad proj: ", c, " vel=", vtos (v), "\n"));

	if (c == "wc_shot")
	{
		if (vlen (hvel) > 20)
		{
			e.wc_dir = normalize (hvel);
			e.angles_y = vectoyaw (hvel);
		}
	}
	else if (c == "ec_tube")
	{
		if (vlen (hvel) > 20)
			e.ec_fly_yaw = vectoyaw (hvel);
		ang = vectoangles (v);
		if (ang_x > 180)
			ang_x = ang_x - 360;
		e.angles_x = bound (-82, ang_x, 76);
		e.angles_y = e.ec_fly_yaw;
	}
	else if (c == "milky")
	{
		e.milky_dir = normalize (v);
	}
	else if (c == "robdob")
	{
		e.movedir = normalize (v);
		e.angles = vectoangles (v);
	}
	else if (c == "megaman" || c == "dookie_shot" || c == "greenguy_mini" || (c == "kyle_proj" && e.ky_mode != KY_MODE_HOMING))
	{
		if (vlen (hvel) > 20)
			e.angles_y = vectoyaw (hvel);
	}
	else if ((c == "kyle_proj" && e.ky_mode == KY_MODE_HOMING) || c == "mm_tank_bar")
	{
		ang = vectoangles (v);
		if (ang_x > 180)
			ang_x = ang_x - 360;
		e.angles_x = bound (-45, ang_x, 45);
		e.angles_y = ang_y;
		e.angles_z = 0;
	}
	else if (c == "ltg_head")
	{
		e.angles = vectoangles (v);
		e.ltg_head = vectoyaw (v);
	}
	else if (e.avelocity == '0 0 0')
	{
		e.angles = vectoangles (v);
	}

	if (time >= pad.skypad_fx_t)
	{
		pad.skypad_fx_t = time + 0.15;
		sound7 (pad, CHAN_AUTO, "skypad/launch.wav", 0.68, ATTN_NORM, SNDSPD * (0.96 + random () * 0.08));
		pointparticles (particleeffectnum ("TE_TELEPORT"), pad.origin + '0 0 12', '0 0 0', 1);
	}
};

float(entity pad, vector pt) SkyPad_PointInPad =
{
	if (pt_x < pad.absmin_x || pt_x > pad.absmax_x)
		return FALSE;
	if (pt_y < pad.absmin_y || pt_y > pad.absmax_y)
		return FALSE;
	if (pt_z < pad.absmin_z || pt_z > pad.absmax_z)
		return FALSE;
	return TRUE;
};

float(entity pad, entity e) SkyPad_OverlapEnt =
{
	if (e.absmin_x > pad.absmax_x || e.absmax_x < pad.absmin_x)
		return FALSE;
	if (e.absmin_y > pad.absmax_y || e.absmax_y < pad.absmin_y)
		return FALSE;
	if (e.absmin_z > pad.absmax_z || e.absmax_z < pad.absmin_z)
		return FALSE;
	return TRUE;
};

void(entity pad, entity e, vector prev_org) SkyPad_TrySweep =
{
	local vector mid;

	if (time < e.skypad_cool_t || !SkyPad_IsProjectile (e))
		return;
	mid = (prev_org + e.origin) * 0.5;
	if (SkyPad_OverlapEnt (pad, e) || SkyPad_PointInPad (pad, e.origin) || SkyPad_PointInPad (pad, mid))
		SkyPad_LaunchProjectile (pad, e);
};

void(entity e) SkyPad_RegisterExtra =
{
	if (!e || e == world || e.skypad_extra_reg)
		return;
	e.skypad_extra_reg = TRUE;
	e.skypad_extra_next = skypad_extra_head;
	skypad_extra_head = e;
};

void() SkyPad_Frame =
{
	local entity e, pad, prev, nxt;

	if (!skypad_present || skypad_head == world)
		return;

	// Catch fast projectiles before they can tunnel past SV_TouchLinks, plus MOVETYPE_NONE/NOCLIP customs
	e = pc_head;
	while (e != world)
	{
		if (time >= e.skypad_cool_t && SkyPad_IsProjectile (e))
		{
			pad = skypad_head;
			while (pad != world)
			{
				SkyPad_TrySweep (pad, e, e.pc_prev_org);
				if (time < e.skypad_cool_t)
					break;
				pad = pad.skypad_next;
			}
		}
		e = e.pc_next;
	}

	e = pc_spike_head;
	while (e != world)
	{
		if (!bm_wasfreed (e) && e.solid != SOLID_NOT && time >= e.skypad_cool_t)
		{
			pad = skypad_head;
			while (pad != world)
			{
				SkyPad_TrySweep (pad, e, e.pc_prev_org);
				if (time < e.skypad_cool_t)
					break;
				pad = pad.skypad_next;
			}
		}
		e = e.pc_spike_next;
	}

	// Non-pc_head custom projectiles (ec_tube, ghost_follower, face) tracked in an intrusive list: O(active), 0 find() calls!
	prev = world;
	e = skypad_extra_head;
	while (e != world)
	{
		nxt = e.skypad_extra_next;
		if (bm_wasfreed (e) || !SkyPad_IsProjectile (e))
		{
			if (!bm_wasfreed (e))
			{
				e.skypad_extra_reg = FALSE;
				e.skypad_extra_next = world;
			}
			if (prev != world)
				prev.skypad_extra_next = nxt;
			else
				skypad_extra_head = nxt;
		}
		else
		{
			if (time >= e.skypad_cool_t)
			{
				pad = skypad_head;
				while (pad != world)
				{
					if (SkyPad_OverlapEnt (pad, e))
					{
						SkyPad_LaunchProjectile (pad, e);
						break;
					}
					pad = pad.skypad_next;
				}
			}
			prev = e;
		}
		e = nxt;
	}
};

void() SkyPad_Touch =
{
	local vector v;

	if (other.classname == "misc_vehicle_johnbird")
	{
		SkyPad_LaunchJohnBird (self, other);
		return;
	}
	if (other.classname == "player" && JohnBird_Flying (other))
	{
		SkyPad_LaunchJohnBird (self, other.jb_vehicle);
		return;
	}
	if (other.classname == "misc_vehicle_rocketrider")
	{
		SkyPad_LaunchRocketRider (self, other);
		return;
	}
	if (other.classname == "player" && RocketRider_Flying (other))
	{
		SkyPad_LaunchRocketRider (self, other.rr_vehicle);
		return;
	}
	if (SkyPad_IsProjectile (other))
	{
		SkyPad_LaunchProjectile (self, other);
		return;
	}

	if (other.classname != "player")
		return;
	if (other.health <= 0 || other.deadflag != 0)
		return;
	if ((other.movetype != MOVETYPE_WALK && (other.ishuman == 1 || other.movetype != MOVETYPE_NONE)) || Veh_Driving (other) || Veh_Riding (other))
		return;
	if (time < other.skypad_cool_t)
		return;

	SkyPad_RaiseMaxVel ();
	if (other.ishuman == 1 && !other.skypad_vel_sent)
	{
		other.skypad_vel_sent = TRUE;
		stuffcmd (other, "sv_maxvelocity 6500\n");
	}

	other.skypad_cool_t = time + 0.65;
	other.skypad_safe_t = time + 10.0;
	other.flags = other.flags - (other.flags & FL_ONGROUND);
	setorigin (other, other.origin + '0 0 2');

	v = SkyPad_CalcVel (other.origin, self.pos1, self.height);
	other.velocity = v;
	other.jump_flag = 0;

	sound7 (other, CHAN_AUTO, "skypad/launch.wav", 0.78, ATTN_NORM, SNDSPD * (0.96 + random () * 0.08));
	pointparticles (particleeffectnum ("TE_TELEPORT"), self.origin + '0 0 12', '0 0 0', 1);

	if (self.message != "" && other.ishuman == 1)
		sprint (other, strcat ("Sky Pad -> ", self.message, "\n"));
};

float() SkyPad_FxCustomize =
{
	local vector vorg;
	local float dx, dy;

	if (other.ishuman != 1)
		return FALSE;
	vorg = (other.clientcamera != world) ? other.clientcamera.origin : other.origin;
	dx = vorg_x - self.origin_x;
	if (dx > 2400 || dx < -2400)
		return FALSE;
	dy = vorg_y - self.origin_y;
	if (dy > 2400 || dy < -2400)
		return FALSE;
	return TRUE;
};

float() SkyPad_CoreCustomize =
{
	local vector vorg;
	local float dx, dy;

	if (other.ishuman != 1)
		return FALSE;
	vorg = (other.clientcamera != world) ? other.clientcamera.origin : other.origin;
	dx = vorg_x - self.origin_x;
	if (dx > 1600 || dx < -1600)
		return FALSE;
	dy = vorg_y - self.origin_y;
	if (dy > 1600 || dy < -1600)
		return FALSE;
	return TRUE;
};

void(vector org, vector v_nom) SkyPad_SpawnVisuals =
{
	local entity base, ring, dome, beam, core;
	local float flz;
	local vector dir, p;

	flz = org_z - 26;		// org is resting player origin + 2u (floor + 26u)
	dir = normalize (v_nom);
	p_x = org_x;
	p_y = org_y;

	// 1. Metallic emitter ring base on the sidewalk
	base = spawn ();
	base.classname = "skypad_fx";
	base.movetype = MOVETYPE_NONE;
	base.solid = SOLID_NOT;
	setmodel (base, "progs/turrbase.mdl");
	setsize (base, '0 0 0', '0 0 0');
	base.scale = 1.65;
	base.angles_y = vectoyaw (dir);
	base.effects = EF_FULLBRIGHT;
	base.colormod = '1.25 1.32 1.45';
	p_z = flz + 0.5;
	setorigin (base, p);
	base.customizeentityforclient = SkyPad_FxCustomize;

	// 2. Animated electric energy ring flush on the pavement
	ring = spawn ();
	ring.classname = "skypad_fx";
	ring.movetype = MOVETYPE_NONE;
	ring.solid = SOLID_NOT;
	setmodel (ring, "progs/ltg_aura.md3");
	setsize (ring, '0 0 0', '0 0 0');
	ring.angles = vectoangles ('0 0 1');
	ring.scale = 1.45;
	ring.effects = EF_FULLBRIGHT | EF_ADDITIVE;
	ring.colormod = '0.30 0.95 1.00';
	ring.alpha = 0.92;
	p_z = flz + 3;
	setorigin (ring, p);
	ring.customizeentityforclient = SkyPad_FxCustomize;

	// 3. Spinning translucent energy vortex dome
	dome = spawn ();
	dome.classname = "skypad_fx";
	dome.movetype = MOVETYPE_NOCLIP;
	dome.solid = SOLID_NOT;
	setmodel (dome, "progs/aura.md3");
	setsize (dome, '0 0 0', '0 0 0');
	dome.scale = 1.15;
	dome.effects = EF_FULLBRIGHT | EF_ADDITIVE;
	dome.colormod = '0.25 0.85 1.00';
	dome.alpha = 0.48;
	dome.avelocity = '0 105 0';
	p_z = flz + 24;
	setorigin (dome, p);
	dome.customizeentityforclient = SkyPad_FxCustomize;

	// 4. Directional trajectory beam pointing along the launch arc
	beam = spawn ();
	beam.classname = "skypad_fx";
	beam.movetype = MOVETYPE_NONE;
	beam.solid = SOLID_NOT;
	setmodel (beam, "progs/laser.md3");
	setsize (beam, '0 0 0', '0 0 0');
	beam.angles = vectoangles (dir);
	beam.scale = 0.85;
	beam.effects = EF_FULLBRIGHT | EF_ADDITIVE;
	beam.colormod = '1.00 0.82 0.25';
	beam.alpha = 0.85;
	p_z = flz + 18;
	setorigin (beam, p);
	beam.customizeentityforclient = SkyPad_FxCustomize;

	// 5. Glowing core sprite casting warm-gold street glow without lightmap rebake
	core = spawn ();
	core.classname = "skypad_fx";
	core.movetype = MOVETYPE_NONE;
	core.solid = SOLID_NOT;
	setmodel (core, "progs/s_dotmed_yell.spr");
	setsize (core, '0 0 0', '0 0 0');
	core.effects = EF_FULLBRIGHT | EF_ADDITIVE;
	core.scale = 1.8;
	core.alpha = 0.85;
	core.pflags = PFLAGS_FULLDYNAMIC | PFLAGS_NOSHADOW | PFLAGS_CORONA;
	core.light_lev = 180;
	core.color = '1 0 0';		// matches palette 251 glow_color without shadow cubemap pass
	p_z = flz + 18;
	setorigin (core, p);
	core.customizeentityforclient = SkyPad_CoreCustomize;
};

void() info_skypad =
{
	local vector v_nom;

	SkyPad_Precache ();
	skypad_present = TRUE;
	SkyPad_RaiseMaxVel ();

	if (!self.height)
		self.height = 2900;

	self.solid = SOLID_TRIGGER;
	self.movetype = MOVETYPE_NONE;
	setorigin (self, self.origin);
	setsize (self, '-40 -40 -26', '40 40 36');
	self.touch = SkyPad_Touch;
	self.skypad_next = skypad_head;
	skypad_head = self;

	v_nom = SkyPad_CalcVel (self.origin, self.pos1, self.height);
	SkyPad_SpawnVisuals (self.origin, v_nom);
};

void() SkyPad_Report =
{
	local entity e;
	local float n;
	local vector v;

	n = 0;
	e = find (world, classname, "info_skypad");
	while (e)
	{
		n = n + 1;
		v = SkyPad_CalcVel (e.origin, e.pos1, e.height);
		bprint ("skypad #", ftos (n), " -> ", e.message, " org=", vtos (e.origin));
		bprint (" dst=", vtos (e.pos1), " apex=", ftos (e.height), " vel=", vtos (v), "\n");
		e = find (e, classname, "info_skypad");
	}
	bprint ("skypad total=", ftos (n), " sv_maxvelocity=", ftos (cvar ("sv_maxvelocity")), "\n");
};
