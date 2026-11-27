#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
CLASSIC QUAKE ROCKET RIDER - FLYABLE SKY-MOUNT (rocket_rider.qc)

2-MD3 V1 Classic Quake Munition:
  - progs/rocket_rider.md3       (rocket_body + flame_fx, grounded z_min == 0.00 on idle_ground 56..67)
  - progs/rocket_rider_rider.md3 (Quake 1 Ranger straddling U-hoop, spawned only while mounted)

Spawns 1 parked map Rocket Rider in the very Northwest corner of bakersfielddowntown
('-13910 6470 6', yaw = 315 facing Southeast over Fox Theater & Downtown Bakersfield)
via RocketRider_MapTick() without editing the BSP.
================
*/

void() RR_IdleThink;
void(entity attacker, float take) RR_Pain;
void() RR_Die;
void() RR_DieBlast;

// ---------------------------------------------------------------- Precache & Helpers

void() RocketRider_Precache =
{
	if (rr_precached)
		return;
	rr_precached = TRUE;

	precache_model ("progs/rocket_rider.md3");
	precache_model ("progs/rocket_rider_rider.md3");
	precache_model ("progs/spike.mdl");

	// Reuse existing precached sounds (0 new sound precache slots on bakersfielddowntown;
	// precaching here guarantees safe playback on maps without vehicles/skypads too)
	precache_sound ("john_bird/takeoff.wav");
	precache_sound ("john_bird/swoop.wav");
	precache_sound ("john_bird/jb_flame_roar.wav");
	precache_sound ("jetpack/swoosh.wav");
	precache_sound ("skypad/launch.wav");
	precache_sound ("ambience/windfly.wav");
	precache_sound ("vehicles/hit_metal1.wav");
	precache_sound ("vehicles/hit_metal2.wav");
	precache_sound ("vehicles/clang1.wav");
	precache_sound ("vehicles/car_boom1.wav");
	precache_sound ("weapons/r_exp3.wav");
	precache_sound ("weapons/rocket1i.wav");
	precache_sound ("items/itembk2.wav");
	precache_sound ("misc/null.wav");

	rr_fx_boost = particleeffectnum ("veh_boost");
	rr_fx_hairfire = particleeffectnum ("jb_fx_hairfire");
	rr_fx_smoke = particleeffectnum ("veh_smoke");
	rr_fx_explode = particleeffectnum ("veh_explode");
	rr_fx_sparks = particleeffectnum ("veh_sparks");
	rr_fx_teleport = particleeffectnum ("TE_TELEPORT");
};

float(entity p) RocketRider_Flying =
{
	return (p.rr_vehicle != world);
};

float(float a) RR_NormAngle =
{
	while (a > 180)
		a = a - 360;
	while (a < -180)
		a = a + 360;
	return a;
};

float(float a) RR_NormYaw360 =
{
	while (a >= 360)
		a = a - 360;
	while (a < 0)
		a = a + 360;
	return a;
};

// Transform rocket local offset (x forward, y port/left, z up) into world space.
// Note: rr.angles_x uses entity pitch (+ up), whereas makevectors expects v_angle pitch (- up).
vector(entity rr, vector ofs) RR_LocalToWorld =
{
	local vector ang;
	local float sc;

	sc = (rr.scale > 0) ? rr.scale : 1.0;
	ang_x = 0 - rr.angles_x;
	ang_y = rr.angles_y;
	ang_z = rr.angles_z;
	makevectors (ang);
	return rr.origin + v_forward * (ofs_x * sc) - v_right * (ofs_y * sc) + v_up * (ofs_z * sc);
};

// ---------------------------------------------------------------- Attached Quake 1 Ranger Entity (2-MD3 Sync)

void() RR_RiderWatchdog =
{
	if (self.owner == world || bm_wasfreed (self.owner) || self.owner.classname != "misc_vehicle_rocketrider"
		|| self.owner.health <= 0 || self.owner.rr_dying || self.owner.rr_pilot == world)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.25;
};

void(entity rr) RR_RemoveRiderEnt =
{
	if (rr.rr_riderent != world)
	{
		if (!bm_wasfreed (rr.rr_riderent) && rr.rr_riderent.owner == rr)
			remove (rr.rr_riderent);
		rr.rr_riderent = world;
	}
};

entity(entity rr) RR_EnsureRiderEnt =
{
	local entity de;

	de = spawn ();
	de.classname = "rr_rider";
	de.owner = rr;
	de.movetype = MOVETYPE_NONE;
	de.solid = SOLID_NOT;
	de.takedamage = DAMAGE_NO;
	de.effects = 0;
	de.alpha = 1;
	de.scale = (rr.scale > 0) ? rr.scale : 1.0;
	setmodel (de, "progs/rocket_rider_rider.md3");
	setsize (de, '0 0 0', '0 0 0');
	setorigin (de, rr.origin);
	de.angles = rr.angles;
	de.frame = rr.frame;
	de.think = RR_RiderWatchdog;
	de.nextthink = time + 0.25;
	rr.rr_riderent = de;
	return de;
};

void(entity rr) RR_SyncRiderEnt =
{
	local entity de;

	if (rr.rr_pilot == world || rr.rr_dying || rr.health <= 0)
	{
		RR_RemoveRiderEnt (rr);
		return;
	}
	de = rr.rr_riderent;
	if (de == world || bm_wasfreed (de) || de.owner != rr)
		de = RR_EnsureRiderEnt (rr);

	setorigin (de, rr.origin);
	de.angles = rr.angles;
	de.frame = rr.frame;
	de.scale = (rr.scale > 0) ? rr.scale : 1.0;
	if (rr.rr_pilot.rr_cam_mode == 1)
		de.nodrawtoclient = rr.rr_pilot;
	else
		de.nodrawtoclient = world;
	de.effects = 0;
};

// ---------------------------------------------------------------- Camera, HUD & Mount / Dismount

void(entity p, entity rr, float use_yaw_lock) RR_UpdateCamera =
{
	local entity cam;
	local vector view_ang, pivot, pos;

	cam = rr.rr_cam;
	if (cam == world || bm_wasfreed (cam))
		return;

	if (use_yaw_lock)
	{
		view_ang = '0 0 0';
		view_ang_y = rr.angles_y;
	}
	else
		view_ang = p.v_angle;

	makevectors (view_ang);
	pivot = rr.origin + '0 0 54';
	if (p.rr_cam_mode == 1)
	{
		// 1st-person nose view: clear look right over the hazard warhead & brass fuse
		pos = pivot + v_forward * 28;
		traceline (pivot, pos, TRUE, rr);
		pos = trace_endpos;
		if (trace_fraction < 1)
			pos = pos + trace_plane_normal * 6;
	}
	else
	{
		// 3rd-person chase cam with smooth boost pullback & wall pull-in
		pos = pivot - v_forward * (148 + rr.rr_cam_pull) + v_up * (28 + rr.rr_cam_pull * 0.16);
		traceline (pivot, pos, TRUE, rr);
		pos = trace_endpos;
		if (trace_fraction < 1)
			pos = pos + trace_plane_normal * 8;
	}
	setorigin (cam, pos);
	cam.angles = view_ang;
};

// Clean, change-throttled centerprint status bar (no John Bird HUD bleed, <= 2 Hz reliable traffic)
void(entity p, entity rr, float dirty) RR_UpdateHUD =
{
	local float hp, pct, segs, i, cidx, tidx, cam1p, key;
	local string hp_col, b_col, bar, tag, line1, line2;

	if (p.ishuman != 1)
		return;

	hp = max (0, ceil (rr.health));
	pct = floor (bound (0, rr.rr_boost_energy, 100) + 0.5);
	segs = floor (pct / 10 + 0.49);
	segs = bound (0, segs, 10);

	if (rr.rr_boosting)
		cidx = 0;
	else if (pct >= 60)
		cidx = 1;
	else if (pct >= 20)
		cidx = 2;
	else
		cidx = 3;

	if (time < rr.rr_skypad_until || vlen (rr.velocity) >= 1450)
		tidx = 1;
	else if (rr.rr_boosting)
		tidx = 2;
	else if (hp <= RR_LOW_HP)
		tidx = 3;
	else
		tidx = 0;

	cam1p = (p.rr_cam_mode == 1) ? 1 : 0;
	key = floor (hp / 10) + 20 * segs + 240 * cidx + 1000 * tidx + 4000 * cam1p;
	if (!dirty && rr.rr_hud_t > 0 && key == rr.rr_hud_key && time < rr.rr_hud_keep)
		return;

	rr.rr_hud_key = key;
	rr.rr_hud_keep = time + 1.5;
	rr.rr_hud_t = time + 0.45;

	if (hp <= RR_LOW_HP)
		hp_col = "^1";
	else if (hp <= 100)
		hp_col = "^3";
	else
		hp_col = "^2";

	if (cidx == 0)
		b_col = "^x0ff";
	else if (cidx == 1)
		b_col = "^5";
	else if (cidx == 2)
		b_col = "^3";
	else
		b_col = "^1";

	bar = "";
	i = 0;
	while (i < 10)
	{
		if (i < segs)
			bar = strcat (bar, "|");
		else
			bar = strcat (bar, "^8.");
		i = i + 1;
	}

	tag = "";
	if (tidx == 1)
		tag = "  ^xfe4>> SKYPAD HYPER! <<";
	else if (tidx == 2)
		tag = "  ^x0ff>> AFTERBURNER <<";
	else if (tidx == 3)
		tag = "  ^1! SMOKING !";

	line1 = strcat ("^3CLASSIC QUAKE ROCKET  ^7HP ", hp_col, ftos (hp));
	line1 = strcat (line1, "^7/150  ^3BOOST ^7[", b_col, bar);
	line1 = strcat (line1, "^7] ", b_col, ftos (segs * 10), "%", tag);
	line2 = strcat ("^7WASD+Mouse Fly  ^3SHIFT^7 Boost  ^3SPACE^7 Climb  ^3K^7 Cam(", cam1p ? "1P" : "3P", ")  ^3H^7 Bail");
	centerprint (p, strcat (line1, "\n", line2));
};

void(entity p, vector pos, vector vel, float yaw) RR_ReleasePlayer =
{
	p.rr_vehicle = world;
	if (p.ishuman == 1)
	{
		p.clientcamera = p;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, p);
		centerprint (p, "");
	}
	p.alpha = 0;					// 0 = default opaque in DarkPlaces
	p.effects = p.effects - (p.effects & EF_NODRAW);
	if (p.health > 0 && p.classname == "player")
	{
		p.movetype = p.rr_oldmove;
		if (p.movetype == MOVETYPE_NONE || p.movetype == 0)
			p.movetype = MOVETYPE_WALK;
		p.solid = p.rr_oldsolid;
		if (p.solid == SOLID_NOT || p.solid == 0)
			p.solid = SOLID_SLIDEBOX;
	}
	setorigin (p, pos);
	p.velocity = vel;
	p.flags = p.flags - (p.flags & FL_ONGROUND);
	p.angles = '0 0 0';
	p.angles_y = yaw;
	p.fixangle = TRUE;
};

void(entity rr) RR_Park =
{
	rr.rr_pilot = world;
	rr.rr_carve_spd = 0;
	rr.rr_boosting = FALSE;
	rr.rr_flail_until = 0;
	rr.rr_skypad_until = 0;
	rr.rr_enter_lock_t = 0;
	RR_RemoveRiderEnt (rr);

	rr.velocity = '0 0 0';
	rr.angles_x = 0;
	rr.angles_z = 0;
	rr.movetype = MOVETYPE_TOSS;
	rr.solid = SOLID_BBOX;
	rr.takedamage = DAMAGE_AIM;
	rr.effects = 0;
	// idle_ground frames (56..67) are grounded at exact z_min == 0.00 -> bmin_z = 0 sits flush!
	setsize (rr, '-32 -28 0', '32 28 56');
	setorigin (rr, rr.origin);
	rr.frame = 56;
	if (!rr.rr_temp && vlen (rr.origin - rr.rr_spawn_org) > 128)
		rr.rr_abandoned_t = time + RR_ABANDON_TIME;
	else
		rr.rr_abandoned_t = 0;
	rr.think = RR_IdleThink;
	rr.nextthink = time + 0.08;
};

void(entity rr, vector exit_pos, vector exit_vel, float exploding) RR_Leave =
{
	local entity p;
	local float yaw, was_locked;

	p = rr.rr_pilot;
	was_locked = (rr.rr_enter_lock_t > 0 && time < rr.rr_enter_lock_t);
	rr.rr_pilot = world;
	rr.rr_carve_spd = 0;
	rr.rr_boosting = FALSE;
	rr.rr_flail_until = 0;
	rr.rr_skypad_until = 0;
	rr.rr_enter_lock_t = 0;
	RR_RemoveRiderEnt (rr);

	if (rr.rr_cam != world)
	{
		if (!bm_wasfreed (rr.rr_cam))
			remove (rr.rr_cam);
		rr.rr_cam = world;
	}

	if (p != world && (p.classname == "player" || p.rr_vehicle == rr))
	{
		yaw = was_locked ? rr.angles_y : p.v_angle_y;
		RR_ReleasePlayer (p, exit_pos, exit_vel, yaw);
	}

	if (!exploding)
		RR_Park (rr);
};

float(entity p, vector pos) RR_SpotClear =
{
	tracebox (pos, VEC_HULL_MIN, VEC_HULL_MAX, pos, FALSE, p);
	if (trace_startsolid || trace_allsolid)
		return FALSE;
	return TRUE;
};

vector(entity rr, entity p) RR_FindExitPos =
{
	local vector cand;

	makevectors ('0 1 0' * rr.angles_y);
	cand = rr.origin + '0 0 32';
	if (RR_SpotClear (p, cand))
		return cand;
	cand = rr.origin + v_right * 58 + '0 0 28';
	if (RR_SpotClear (p, cand))
		return cand;
	cand = rr.origin - v_right * 58 + '0 0 28';
	if (RR_SpotClear (p, cand))
		return cand;
	cand = rr.origin - v_forward * 64 + '0 0 28';
	if (RR_SpotClear (p, cand))
		return cand;
	cand = rr.origin + v_forward * 64 + '0 0 28';
	if (RR_SpotClear (p, cand))
		return cand;
	cand = rr.origin + '0 0 84';
	if (RR_SpotClear (p, cand))
		return cand;
	return rr.origin + '0 0 28';
};

void(entity p, entity rr) RR_Enter =
{
	local entity cam, oldself;
	local float yaw;

	if (p.health <= 0 || p.rr_vehicle != world || p.jb_vehicle != world || p.veh_van != world || p.veh_ride != world
		|| FD_Flying (p) || EricCannon_Active (p) || MMTank_Driving (p))
		return;
	if (rr == world || rr.health <= 0 || rr.rr_dying || rr.rr_pilot != world)
		return;

	KY_CamDetach (p);
	DK_ResetPlayer (p);
	GJ_ResetPlayer (p);
	RH_ResetPlayer (p);
	p.mm_pending = FALSE;
	if (p.jp_on)
	{
		oldself = self;
		self = p;
		Jetpack_Off ();
		self = oldself;
	}
	if (p.wc_charging)
	{
		p.wc_charging = 0;
		sound (p, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
	}
	if (p.bn_on)
	{
		p.bn_on = FALSE;
		p.viewzoom = 0;
		centerprint (p, "");
	}
	p.milky_wind = 0;
	p.pk_throw_at = 0;
	p.ns_throw_at = 0;

	yaw = RR_NormYaw360 (rr.angles_y);
	rr.rr_pilot = p;
	rr.rr_carve_spd = 0;
	rr.rr_boost_energy = 100;
	rr.rr_boosting = FALSE;
	rr.rr_boost_snd_t = 0;
	rr.rr_cam_pull = 0;
	rr.rr_flail_until = 0;
	rr.rr_skypad_until = 0;
	rr.rr_pad_scan_t = 0;
	rr.rr_fx_t = 0;
	rr.rr_flare_cd = 0;
	rr.rr_abandoned_t = 0;
	rr.rr_hud_t = 0;
	rr.rr_hud_key = -1;
	rr.rr_enter_lock_t = time + 0.14;
	rr.think = RR_IdleThink;
	rr.nextthink = time + 0.1;

	p.rr_vehicle = rr;
	p.rr_oldmove = p.movetype;
	p.rr_oldsolid = p.solid;
	p.rr_cam_mode = 0;				// default 3rd-person chase view
	p.rr_prev_yaw = yaw;
	p.rr_prev_pitch = 0;

	rr.movetype = MOVETYPE_NONE;
	rr.solid = SOLID_BBOX;
	rr.takedamage = DAMAGE_AIM;
	rr.effects = 0;
	setsize (rr, '-28 -36 -4', '28 36 58');

	// Lift cleanly off the sidewalk so flying hull (-4u bottom) starts 100% clear
	tracebox (rr.origin + '0 0 8', '-28 -36 -4', '28 36 58', rr.origin + '0 0 12', FALSE, rr);
	if (!trace_startsolid && !trace_allsolid)
		setorigin (rr, trace_endpos);
	else
		setorigin (rr, rr.origin + '0 0 8');

	makevectors ('0 1 0' * yaw);
	rr.velocity = v_forward * 240 + '0 0 140';
	rr.angles_x = 0;
	rr.angles_y = yaw;
	rr.angles_z = 0;
	rr.frame = 0;

	// Hide player body & lock view onto the rocket's parked outward heading
	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.velocity = '0 0 0';
	p.alpha = 0.01;
	p.effects = p.effects | EF_NODRAW;
	setorigin (p, rr.origin + '0 0 20');
	p.angles = '0 0 0';
	p.angles_y = yaw;
	p.v_angle = '0 0 0';
	p.v_angle_y = yaw;
	p.fixangle = TRUE;

	// Spawn speck camera entity (exact john_bird / vehicle_drive pattern)
	cam = spawn ();
	cam.classname = "rr_cam";
	cam.movetype = MOVETYPE_NONE;
	cam.solid = SOLID_NOT;
	cam.alpha = 0.01;
	cam.scale = 0.01;
	setmodel (cam, "progs/spike.mdl");
	setsize (cam, '0 0 0', '0 0 0');
	setorigin (cam, rr.origin + '0 0 54');
	rr.rr_cam = cam;

	if (p.ishuman == 1)
	{
		p.clientcamera = cam;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, cam);
	}

	RR_SyncRiderEnt (rr);
	RR_UpdateCamera (p, rr, TRUE);
	RR_UpdateHUD (p, rr, TRUE);

	sound (rr, CHAN_ITEM, "john_bird/takeoff.wav", 1, 0.55);
	if (rr_fx_boost > 0)
	{
		local vector noz;
		noz = RR_LocalToWorld (rr, '-53.5 0 34');
		pointparticles (rr_fx_boost, noz, v_forward * -220, 3);
	}
};

// ---------------------------------------------------------------- SkyPad & Trigger_Push Scanner (20 Hz)

float(vector bmin, vector bmax, entity pad) RR_OverlapPad =
{
	if (bmin_x > pad.absmax_x || bmax_x < pad.absmin_x)
		return FALSE;
	if (bmin_y > pad.absmax_y || bmax_y < pad.absmin_y)
		return FALSE;
	if (bmin_z > pad.absmax_z || bmax_z < pad.absmin_z)
		return FALSE;
	return TRUE;
};

float(entity rr, entity pilot) RR_CheckPads =
{
	local entity e;
	local vector bmin, bmax, vel;
	local float spd, maxv;

	if (time < rr.skypad_cool_t || time < rr.rr_pad_scan_t)
		return FALSE;
	rr.rr_pad_scan_t = time + 0.05;

	bmin = rr.origin + '-36 -36 -8';
	bmax = rr.origin + '36 36 62';

	e = find (world, classname, "info_skypad");
	while (e != world)
	{
		if (RR_OverlapPad (bmin, bmax, e))
		{
			SkyPad_LaunchRocketRider (e, rr);
			return TRUE;
		}
		e = find (e, classname, "info_skypad");
	}

	e = find (world, classname, "trigger_push");
	while (e != world)
	{
		if (RR_OverlapPad (bmin, bmax, e))
		{
			spd = e.speed;
			if (!spd)
				spd = 1000;
			if (e.spawnflags & ADD_VEL)
				vel = rr.velocity + spd * e.movedir * 5;
			else
				vel = spd * e.movedir * 10;
			if (vlen (vel) > 1800)
			{
				SkyPad_RaiseMaxVel ();
				if (pilot != world && pilot.ishuman == 1 && !pilot.skypad_vel_sent)
				{
					pilot.skypad_vel_sent = TRUE;
					stuffcmd (pilot, "sv_maxvelocity 6500\n");
				}
			}
			maxv = cvar ("sv_maxvelocity");
			if (maxv <= 0)
				maxv = 2000;
			vel_x = bound (0 - maxv, vel_x, maxv);
			vel_y = bound (0 - maxv, vel_y, maxv);
			vel_z = bound (0 - maxv, vel_z, maxv);

			rr.skypad_cool_t = time + 0.45;
			rr.velocity = vel;
			if (vlen (vel) >= 1350)
				rr.rr_skypad_until = max (rr.rr_skypad_until, time + 1.8);
			if (!(e.spawnflags & NO_SOUND))
				sound7 (rr, CHAN_AUTO, "ambience/windfly.wav", 0.85, ATTN_NORM, SNDSPD * (0.95 + random () * 0.12));
			if (e.spawnflags & PUSH_ONCE)
				BM_PushRemove (e);
			return TRUE;
		}
		e = find (e, classname, "trigger_push");
	}
	return FALSE;
};

// ---------------------------------------------------------------- Collision, SlideMove & Aerial Ram

void(entity rr, entity pilot, entity hit) RR_CheckRam =
{
	local vector push;
	local float spd;

	if (hit == world || hit == pilot || hit == rr)
		return;
	if (!hit.takedamage || hit.health <= 0)
		return;
	if (time < rr.rr_ram_cd)
		return;
	spd = vlen (rr.velocity);
	if (spd < 820)
		return;
	if (!rr.rr_boosting && time >= rr.rr_skypad_until && spd < 1050)
		return;

	rr.rr_ram_cd = time + 1.0;
	sound (rr, CHAN_AUTO, "vehicles/clang1.wav", 0.9, ATTN_NORM);
	if (rr_fx_sparks > 0)
		pointparticles (rr_fx_sparks, rr.origin + '0 0 32', '0 0 0', 1);

	push = normalize (rr.velocity);
	push_z = max (0.35, push_z);
	push = normalize (push);
	if (hit.movetype == MOVETYPE_WALK || hit.movetype == MOVETYPE_STEP || hit.movetype == MOVETYPE_TOSS)
	{
		hit.flags = hit.flags - (hit.flags & FL_ONGROUND);
		hit.velocity = hit.velocity + push * 420 + '0 0 200';
	}
	rr_inflicting = 2;
	if (pilot != world)
		T_Damage (hit, rr, pilot, (hit.classname == "player" && hit.rr_vehicle == world) ? 40 : 75);
	else
		T_Damage (hit, rr, rr, 50);
	rr_inflicting = 0;
};

void(entity rr, entity pilot, float dt) RR_SlideMove =
{
	local vector start, dest, rem, n1;
	local float vn;

	if (vlen (rr.velocity) < 0.5)
		return;

	start = rr.origin;
	dest = start + rr.velocity * dt;
	if (pointcontents (dest + '0 0 56') == CONTENT_SKY)
	{
		dest_z = min (dest_z, start_z);
		if (rr.velocity_z > 0)
			rr.velocity_z = 0;
	}
	tracebox (start, rr.mins, rr.maxs, dest, FALSE, rr);
	if (trace_allsolid || trace_startsolid)
	{
		tracebox (start + '0 0 8', rr.mins, rr.maxs, start + '0 0 8', TRUE, rr);
		if (!trace_startsolid && !trace_allsolid)
			setorigin (rr, start + '0 0 8');
		return;
	}
	setorigin (rr, trace_endpos);
	if (trace_fraction >= 1)
		return;

	if (trace_ent != world)
		RR_CheckRam (rr, pilot, trace_ent);

	n1 = trace_plane_normal;
	vn = rr.velocity * n1;
	if (vn < 0)
		rr.velocity = rr.velocity - n1 * vn;

	rem = rr.velocity * (dt * (1 - trace_fraction));
	if (vlen (rem) > 0.25)
	{
		tracebox (rr.origin, rr.mins, rr.maxs, rr.origin + rem, FALSE, rr);
		if (!trace_allsolid && !trace_startsolid)
		{
			setorigin (rr, trace_endpos);
			if (trace_fraction < 1)
			{
				vn = rr.velocity * trace_plane_normal;
				if (vn < 0)
					rr.velocity = rr.velocity - trace_plane_normal * vn;
			}
		}
	}
};

// ---------------------------------------------------------------- Animation, Nozzle Particles & Audio

void(entity rr, float dt, float up_in) RR_UpdateAnimAndFX =
{
	local float spd, clip_start, clip_len, fps, idx, is_hyper, is_boost;
	local vector noz, ex_vel;

	spd = vlen (rr.velocity);
	is_hyper = (time < rr.rr_skypad_until || spd >= 1450);
	is_boost = (rr.rr_boosting || rr.rr_carve_spd >= 60 || spd >= 950);

	if (time < rr.rr_flail_until)
	{
		// Clip 6: hit_flail (frames 68..83, 16f @ 26fps)
		clip_start = 68;
		clip_len = 16;
		fps = 26;
	}
	else if (is_hyper)
	{
		// Clip 7: skypad_hyper (frames 84..99, 16f @ 30fps)
		clip_start = 84;
		clip_len = 16;
		fps = 30;
	}
	else if (is_boost)
	{
		// Clip 2: fly_boost (frames 16..31, 16f @ 22fps)
		clip_start = 16;
		clip_len = 16;
		fps = 22;
	}
	else if (rr.velocity_z < -420)
	{
		// Clip 4: swoop_dive (frames 44..55, 12f @ 16fps)
		clip_start = 44;
		clip_len = 12;
		fps = 16;
	}
	else if (up_in > 0.2 || spd < 230)
	{
		// Clip 3: fly_hover (frames 32..43, 12f @ 12fps)
		clip_start = 32;
		clip_len = 12;
		fps = 12;
	}
	else
	{
		// Clip 1: fly_cruise (frames 0..15, 16f @ 14..20fps)
		clip_start = 0;
		clip_len = 16;
		fps = 14 + bound (0, spd / 150, 6);
	}

	rr.rr_anim_clock = rr.rr_anim_clock + dt * fps;
	idx = floor (rr.rr_anim_clock);
	idx = idx - clip_len * floor (idx / clip_len);
	rr.frame = clip_start + idx;

	// Nozzle-accurate DarkPlaces particles (~18 Hz)
	if (time >= rr.rr_fx_t)
	{
		rr.rr_fx_t = time + 0.055;
		noz = RR_LocalToWorld (rr, '-53.5 0 34');
		ex_vel = v_forward * -160;
		if (is_hyper)
		{
			if (rr_fx_hairfire > 0)
				pointparticles (rr_fx_hairfire, noz, ex_vel * 1.4, 2);
			if (rr_fx_boost > 0)
				pointparticles (rr_fx_boost, noz, ex_vel * 1.2, 2);
		}
		else if (is_boost)
		{
			if (rr_fx_boost > 0)
				pointparticles (rr_fx_boost, noz, ex_vel, 2);
		}
		else if (spd > 180)
		{
			if (rr_fx_boost > 0)
				pointparticles (rr_fx_boost, noz, ex_vel * 0.65, 1);
		}
	}

	if (rr.health <= RR_LOW_HP && rr_fx_smoke > 0 && time >= rr.rr_smoke_t)
	{
		rr.rr_smoke_t = time + 0.09;
		pointparticles (rr_fx_smoke, rr.origin + '0 0 34', '0 0 28', 1);
	}
};

// ---------------------------------------------------------------- Per-Frame Player Flight Loop

float() RocketRider_Frame =
{
	local entity rr, oldself;
	local float dt, fwd_in, str_in, up_in, slow_mult, max_spd, yaw_delta, pitch_delta;
	local float yaw_rate, ang_rate, prev_carve, carve_bonus, target_roll, target_pitch, k, pull_tgt, grav, pc, locked;
	local vector wish, dir_ang, view_ang, noz;

	rr = self.rr_vehicle;
	if (rr == world)
		return FALSE;
	if (bm_wasfreed (rr) || rr.rr_pilot != self || rr.health <= 0 || self.health <= 0)
	{
		RR_ReleasePlayer (self, self.origin, '0 0 0', self.v_angle_y);
		return FALSE;
	}

	dt = frametime;
	if (dt < 0.001)
		dt = 0.001;
	if (dt > 0.05)
		dt = 0.05;

	// Dismount (H = 86), Camera Toggle (K = 87), Cheat Impulses (139, 140)
	if (self.impulse == 86)
	{
		self.impulse = 0;
		RR_Leave (rr, RR_FindExitPos (rr, self), rr.velocity * 0.35, FALSE);
		return TRUE;
	}
	else if (self.impulse == 87)
	{
		self.rr_cam_mode = 1 - self.rr_cam_mode;
		if (self.rr_cam_mode == 1)
			sprint (self, "Classic Quake Rocket camera: 1st-Person Nose View\n");
		else
			sprint (self, "Classic Quake Rocket camera: 3rd-Person Chase View\n");
		self.impulse = 0;
		RR_UpdateHUD (self, rr, TRUE);
	}
	else if ((self.impulse == 139 || self.impulse == 140) && autocvar_sv_cheats)
	{
		RocketRider_Impulse ();
	}
	self.impulse = 0;

	self.flags = self.flags - (self.flags & FL_ONGROUND);
	self.velocity = '0 0 0';

	// Post-mount heading lock: wait ~140ms for client to acknowledge parked yaw before mouse steering takes over
	locked = (rr.rr_enter_lock_t > 0 && time < rr.rr_enter_lock_t);
	if (locked)
	{
		view_ang = '0 0 0';
		view_ang_y = rr.angles_y;
		self.angles = view_ang;
		self.fixangle = TRUE;
		yaw_delta = 0;
		pitch_delta = 0;
	}
	else
	{
		if (rr.rr_enter_lock_t > 0)
		{
			rr.rr_enter_lock_t = 0;
			self.rr_prev_yaw = self.v_angle_y;
			self.rr_prev_pitch = self.v_angle_x;
		}
		view_ang = self.v_angle;
		yaw_delta = RR_NormAngle (view_ang_y - self.rr_prev_yaw);
		pitch_delta = RR_NormAngle (view_ang_x - self.rr_prev_pitch);
		self.rr_prev_yaw = view_ang_y;
		self.rr_prev_pitch = view_ang_x;
	}

	makevectors (view_ang);
	fwd_in = bound (-1, self.movement_x / 200, 1);
	str_in = bound (-1, self.movement_y / 200, 1);
	up_in = 0;
	if (self.button2 || self.movement_z > 40)
		up_in = 1;
	else if (self.movement_z < -40)
		up_in = -1;

	// Water / Lava / Slime hazard checks
	pc = pointcontents (rr.origin + '0 0 18');
	if (pc == CONTENT_LAVA || pc == CONTENT_SLIME)
	{
		damage_attacker = world;
		oldself = self;
		self = rr;
		RR_Die ();
		self = oldself;
		return TRUE;
	}
	slow_mult = 1.0;
	if (pc == CONTENT_WATER)
	{
		slow_mult = 0.55;
		if (rr_fx_smoke > 0 && time >= rr.rr_smoke_t)
		{
			rr.rr_smoke_t = time + 0.14;
			pointparticles (rr_fx_smoke, rr.origin + '0 0 24', '0 0 36', 1);
		}
	}

	// Mouse-carve airspeed bonus (sweeping turns pump up rocket speed)
	yaw_rate = yaw_delta / dt;
	ang_rate = (fabs (yaw_delta) + fabs (pitch_delta)) / dt;
	prev_carve = rr.rr_carve_spd;
	if (ang_rate > 25 && fwd_in >= -0.2)
		rr.rr_carve_spd = min (100, rr.rr_carve_spd + bound (0, (ang_rate - 25) * 0.48, 160) * dt);
	rr.rr_carve_spd = max (0, rr.rr_carve_spd - dt * 26);
	if (prev_carve < 65 && rr.rr_carve_spd >= 65 && time >= rr.rr_carve_snd_t)
	{
		rr.rr_carve_snd_t = time + 1.1;
		sound (rr, CHAN_ITEM, "john_bird/swoop.wav", 0.75, 0.70);
	}

	// SHIFT (+button4): Rechargeable Afterburner Boost (1280 u/s)
	if (self.button4)
	{
		if (rr.rr_boosting)
		{
			if (rr.rr_boost_energy <= 0)
				rr.rr_boosting = FALSE;
		}
		else if (rr.rr_boost_energy >= 15)
		{
			rr.rr_boosting = TRUE;
			if (time >= rr.rr_boost_snd_t)
			{
				rr.rr_boost_snd_t = time + 0.65;
				sound (rr, CHAN_WEAPON, "john_bird/jb_flame_roar.wav", 0.95, 0.55);
				sound (rr, CHAN_ITEM, "john_bird/takeoff.wav", 0.75, 0.65);
			}
		}
	}
	else
	{
		rr.rr_boosting = FALSE;
	}

	if (rr.rr_boosting)
	{
		rr.rr_boost_energy = max (0, rr.rr_boost_energy - dt * 36);
		if (rr.rr_boost_energy <= 0)
			rr.rr_boosting = FALSE;
		else if (time >= rr.rr_boost_snd_t)
		{
			rr.rr_boost_snd_t = time + 0.55;
			sound (rr, CHAN_WEAPON, "john_bird/jb_flame_roar.wav", 0.85, 0.58);
		}
	}
	else
	{
		rr.rr_boost_energy = min (100, rr.rr_boost_energy + dt * 28);
	}

	// M1 (Fire): tactile rocket exhaust whistle / flare burst
	if (self.button0 && time >= rr.rr_flare_cd)
	{
		rr.rr_flare_cd = time + 1.1;
		sound7 (rr, CHAN_AUTO, "weapons/rocket1i.wav", 0.85, 0.60, 108 + crandom () * 8);
		noz = RR_LocalToWorld (rr, '-53.5 0 34');
		if (rr_fx_hairfire > 0)
			pointparticles (rr_fx_hairfire, noz, v_forward * -260, 3);
		makevectors (view_ang);
	}

	// SkyPad & trigger_push detection (20 Hz)
	RR_CheckPads (rr, self);

	carve_bonus = (rr.rr_carve_spd / 100) * RR_SPEED_CARVE_MAX;
	if (time < rr.rr_skypad_until)
	{
		// Supersonic SkyPad ballistic arc: keep full launch velocity without clamping to cruise cap!
		grav = cvar ("sv_gravity");
		if (grav <= 10)
			grav = 800;
		rr.velocity_z = rr.velocity_z - grav * dt;
		wish = v_forward * (fwd_in * 420) + v_right * (str_in * 360);
		if (up_in > 0)
			wish_z = wish_z + 240;
		rr.velocity = rr.velocity + wish * (dt * 1.35);
	}
	else
	{
		wish = '0 0 0';
		if (rr.rr_boosting)
		{
			wish = v_forward * (RR_SPEED_BOOST * slow_mult) + v_right * (str_in * RR_SPEED_STRAFE * 0.72 * slow_mult);
			if (up_in > 0)
				wish_z = wish_z + RR_SPEED_CLIMB * 0.55 * slow_mult;
			else if (up_in < 0)
				wish_z = wish_z - RR_SPEED_CLIMB * 0.55 * slow_mult;
			max_spd = max (RR_SPEED_BOOST, RR_SPEED_CRUISE + 140 + carve_bonus) * slow_mult;
		}
		else
		{
			if (fwd_in > 0)
				wish = wish + v_forward * (fwd_in * (RR_SPEED_CRUISE + carve_bonus) * slow_mult);
			else if (fwd_in < 0)
				wish = wish + v_forward * (fwd_in * 300 * slow_mult);
			else if (rr.rr_carve_spd > 15)
				wish = wish + v_forward * (carve_bonus * 0.65 * slow_mult);

			wish = wish + v_right * (str_in * RR_SPEED_STRAFE * slow_mult);
			if (up_in > 0)
				wish_z = wish_z + RR_SPEED_CLIMB * slow_mult;
			else if (up_in < 0)
				wish_z = wish_z - RR_SPEED_CLIMB * slow_mult;
			max_spd = (RR_SPEED_CRUISE + 140 + carve_bonus) * slow_mult;
		}

		if (fwd_in < -0.2 && !rr.rr_boosting)
		{
			k = bound (0, dt * 8.0, 1);
			rr.velocity = rr.velocity + (wish - rr.velocity) * k;
		}
		else if (vlen (wish) > 10)
		{
			k = bound (0, dt * ((rr.rr_boosting || rr.rr_carve_spd >= 60) ? 8.0 : 6.2), 1);
			rr.velocity = rr.velocity + (wish - rr.velocity) * k;
		}
		else
		{
			// Hover buoyancy: gentle drag + mild settle
			rr.velocity_x = rr.velocity_x * bound (0, 1 - dt * 2.2, 1);
			rr.velocity_y = rr.velocity_y * bound (0, 1 - dt * 2.2, 1);
			rr.velocity_z = rr.velocity_z * bound (0, 1 - dt * 2.8, 1) - 24 * dt;
		}

		if (vlen (rr.velocity) > max_spd)
			rr.velocity = normalize (rr.velocity) * max_spd;
	}

	RR_SlideMove (rr, self, dt);

	// Smooth rocket attitude: pitch tracks flight velocity/look, banking roll into turns up to +-42 deg!
	if (fabs (yaw_rate) < 12 && fabs (str_in) < 0.05)
		target_roll = 0;
	else
		target_roll = bound (-42, (0 - yaw_rate * 0.16) + str_in * 24, 42);

	if (vlen (rr.velocity) > 140)
	{
		dir_ang = vectoangles (rr.velocity);
		target_pitch = bound (-38, RR_NormAngle (dir_ang_x), 38);
	}
	else
	{
		target_pitch = bound (-30, 0 - view_ang_x * 0.50, 30);
	}
	rr.angles_x = rr.angles_x + (target_pitch - rr.angles_x) * bound (0, dt * 10.0, 1);
	rr.angles_y = view_ang_y;
	rr.angles_z = rr.angles_z + (target_roll - rr.angles_z) * bound (0, dt * 8.5, 1);

	// Camera pullback on boost / supersonic SkyPad
	pull_tgt = (time < rr.rr_skypad_until) ? 28 : (rr.rr_boosting ? 20 : (rr.rr_carve_spd / 100 * 14));
	rr.rr_cam_pull = rr.rr_cam_pull + (pull_tgt - rr.rr_cam_pull) * bound (0, dt * 6.0, 1);

	setorigin (self, rr.origin + '0 0 20');
	RR_UpdateAnimAndFX (rr, dt, up_in);
	RR_SyncRiderEnt (rr);
	RR_UpdateCamera (self, rr, locked);

	if (time >= rr.rr_hud_t)
		RR_UpdateHUD (self, rr, FALSE);

	return TRUE;
};

// ---------------------------------------------------------------- Parked Idle, Respawn, Damage & Explosion

void() RR_Respawn =
{
	tracebox (self.rr_spawn_org, '-32 -28 0', '32 28 56', self.rr_spawn_org, FALSE, self);
	if (trace_ent != world)
	{
		self.nextthink = time + 1.0;
		return;
	}
	self.rr_dying = FALSE;
	self.enemy = world;
	self.health = RR_MAX_HP;
	self.max_health = RR_MAX_HP;
	self.skin = 0;
	self.alpha = 1;
	self.scale = 1.0;
	self.effects = 0;
	setmodel (self, "progs/rocket_rider.md3");
	setorigin (self, self.rr_spawn_org);
	self.angles = '0 0 0';
	self.angles_y = self.rr_spawn_yaw;
	RR_Park (self);
	sound (self, CHAN_ITEM, "items/itembk2.wav", 1, ATTN_NORM);
};

void() RR_IdleThink =
{
	local entity p;
	local float idx, pc;

	if (self.health <= 0 || self.rr_dying)
		return;

	p = self.rr_pilot;
	if (p != world)
	{
		if (p.classname != "player" || p.health <= 0 || p.rr_vehicle != self)
			RR_Leave (self, self.origin + '0 0 32', '0 0 0', FALSE);
		self.nextthink = time + 0.1;
		return;
	}

	// Ensure rider entity is never left orphaned on an unmanned rocket
	RR_RemoveRiderEnt (self);

	// Check lava/slime/water while parked unmanned
	pc = pointcontents (self.origin + '0 0 18');
	if (pc == CONTENT_LAVA || pc == CONTENT_SLIME)
	{
		damage_attacker = world;
		RR_Die ();
		return;
	}
	if (pc == CONTENT_WATER && !self.rr_temp && self.rr_abandoned_t == 0)
		self.rr_abandoned_t = time + 12;

	// Return abandoned unmanned map rocket cleanly to its home spawn pad
	if (!self.rr_temp && self.rr_abandoned_t > 0 && time >= self.rr_abandoned_t)
	{
		tracebox (self.rr_spawn_org, '-32 -28 0', '32 28 56', self.rr_spawn_org, FALSE, self);
		if (trace_ent == world)
		{
			RR_Respawn ();
			return;
		}
		self.rr_abandoned_t = time + 2.0;
	}

	// Clip 5: idle_ground (frames 56..67, 12f @ 8fps, z_min == 0.00 flush on skids)
	idx = floor (time * 8.0);
	idx = idx - 12 * floor (idx / 12);
	self.frame = 56 + idx;

	if (self.health <= RR_LOW_HP && rr_fx_smoke > 0 && time >= self.rr_smoke_t)
	{
		self.rr_smoke_t = time + 0.16;
		pointparticles (rr_fx_smoke, self.origin + '0 0 28', '0 0 20', 1);
	}
	self.nextthink = time + 0.1;
};

void(entity attacker, float take) RR_Pain =
{
	local string msg;

	// Trigger 0.65s hit_flail animation + tactile roll jolt while flying!
	if (self.rr_pilot != world)
	{
		self.rr_flail_until = time + 0.65;
		self.angles_z = bound (-42, self.angles_z + ((random () < 0.5) ? 14 : -14), 42);
		// no forced HUD redraw here: a reliable centerprint per hit flooded the pilot under fire. The 0.45 s refresh
		// in the flight frame sees the new health in its key and redraws then.

	}

	if (time < self.rr_pain_t)
		return;
	self.rr_pain_t = time + 0.18;

	if (random () < 0.5)
		sound7 (self, CHAN_AUTO, "vehicles/hit_metal1.wav", 0.95, 0.55, 94 + random () * 14);
	else
		sound7 (self, CHAN_AUTO, "vehicles/hit_metal2.wav", 0.95, 0.55, 94 + random () * 14);

	if (rr_fx_sparks > 0)
		pointparticles (rr_fx_sparks, self.origin + '0 0 32', '0 0 0', 1);

	msg = strcat ("Classic Quake Rocket hit! [", ftos (max (0, ceil (self.health))), "/150 HP]\n");
	if (attacker != world && attacker.classname == "player" && attacker.ishuman == 1)
		sprint (attacker, msg);
	if (self.rr_pilot != world && self.rr_pilot != attacker && self.rr_pilot.ishuman == 1)
		sprint (self.rr_pilot, msg);
};

void() RR_Die =
{
	local entity pilot, killer;
	local vector eject_vel;

	if (self.rr_dying)
		return;
	self.rr_dying = TRUE;
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.touch = SUB_Null;
	RR_RemoveRiderEnt (self);

	killer = damage_attacker;
	if (killer == world)
		killer = self.enemy;
	self.enemy = killer;

	pilot = self.rr_pilot;
	self.rr_blast_pilot = pilot;
	if (pilot != world)
	{
		eject_vel = self.velocity * 0.45 + '0 0 240';
		RR_Leave (self, RR_FindExitPos (self, pilot), eject_vel, TRUE);
	}

	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.think = RR_DieBlast;
	self.nextthink = time;		// deferred 1 tick: avoids T_Damage recursion
};

void() RR_DieBlast =
{
	local entity pilot, killer;
	local vector boom_org;

	killer = self.enemy;
	pilot = self.rr_blast_pilot;
	self.rr_blast_pilot = world;
	boom_org = self.origin + '0 0 32';

	sound (self, CHAN_VOICE, "vehicles/car_boom1.wav", 1, 0.45);
	sound (self, CHAN_AUTO, "weapons/r_exp3.wav", 1, 0.45);

	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, boom_org_x);
	WriteCoord (MSG_BROADCAST, boom_org_y);
	WriteCoord (MSG_BROADCAST, boom_org_z);
	if (rr_fx_explode > 0)
		pointparticles (rr_fx_explode, boom_org, '0 0 0', 1);
	if (rr_fx_hairfire > 0)
		pointparticles (rr_fx_hairfire, boom_org, '0 0 80', 2);

	if (killer != world && killer.classname == "player" && killer.ishuman == 1)
		sprint (killer, "BOOM! Destroyed Classic Quake Rocket!\n");

	rr_inflicting = 1;
	if (pilot != world && pilot.classname == "player" && pilot.health > 0)
	{
		if (killer != world && killer != pilot)
			T_Damage (pilot, self, killer, 45);
		else
			T_Damage (pilot, self, self, 35);
	}
	if (killer != world)
		T_RadiusDamage (self, killer, 120, pilot);
	else
		T_RadiusDamage (self, self, 120, pilot);
	rr_inflicting = 0;

	if (self.rr_temp)
	{
		self.solid = SOLID_NOT;
		self.takedamage = DAMAGE_NO;
		self.movetype = MOVETYPE_NONE;
		setmodel (self, "");
		self.think = SUB_Remove;
		self.nextthink = time + 1.5;
	}
	else
	{
		self.solid = SOLID_NOT;
		self.takedamage = DAMAGE_NO;
		self.movetype = MOVETYPE_NONE;
		self.effects = self.effects | EF_NODRAW;
		self.velocity = '0 0 0';
		self.think = RR_Respawn;
		self.nextthink = time + RR_RESPAWN_TIME;
	}
};

// ---------------------------------------------------------------- Spawn, Prompts, Cleanup & Impulses

entity(vector org, float yaw, float is_temp) RR_SpawnParked =
{
	local entity rr;

	RocketRider_Precache ();
	rr_has_rockets = TRUE;

	rr = spawn ();
	rr.classname = "misc_vehicle_rocketrider";
	rr.netname = "Classic Quake Rocket";
	rr.rr_temp = is_temp;
	rr.rr_pilot = world;
	rr.rr_cam = world;
	rr.rr_riderent = world;
	rr.rr_summoner = world;
	rr.rr_dying = FALSE;
	rr.rr_carve_spd = 0;
	rr.rr_boost_energy = 100;
	rr.rr_boosting = FALSE;
	rr.rr_boost_snd_t = 0;
	rr.rr_cam_pull = 0;
	rr.rr_flail_until = 0;
	rr.rr_skypad_until = 0;
	rr.rr_pad_scan_t = 0;
	rr.rr_fx_t = 0;
	rr.rr_smoke_t = 0;
	rr.rr_pain_t = 0;
	rr.rr_ram_cd = 0;
	rr.rr_flare_cd = 0;
	rr.rr_abandoned_t = 0;
	rr.rr_enter_lock_t = 0;
	rr.health = RR_MAX_HP;
	rr.max_health = RR_MAX_HP;
	rr.skin = 0;
	rr.alpha = 1;
	rr.scale = 1.0;
	rr.effects = 0;
	rr.th_pain = RR_Pain;
	rr.th_die = RR_Die;

	setmodel (rr, "progs/rocket_rider.md3");
	rr.angles = '0 0 0';
	rr.angles_y = RR_NormYaw360 (yaw);
	setorigin (rr, org);
	rr.rr_spawn_org = org;
	rr.rr_spawn_yaw = rr.angles_y;
	RR_Park (rr);
	return rr;
};

void() misc_vehicle_rocketrider =
{
	RocketRider_Precache ();
	rr_has_rockets = TRUE;

	self.classname = "misc_vehicle_rocketrider";
	self.netname = "Classic Quake Rocket";
	self.rr_temp = FALSE;
	self.rr_pilot = world;
	self.rr_cam = world;
	self.rr_riderent = world;
	self.rr_summoner = world;
	self.rr_dying = FALSE;
	self.rr_boost_energy = 100;
	self.health = RR_MAX_HP;
	self.max_health = RR_MAX_HP;
	self.skin = 0;
	self.alpha = 1;
	self.scale = 1.0;
	self.effects = 0;
	self.th_pain = RR_Pain;
	self.th_die = RR_Die;

	setmodel (self, "progs/rocket_rider.md3");
	self.angles_x = 0;
	self.angles_y = RR_NormYaw360 (self.angles_y);
	self.angles_z = 0;
	self.rr_spawn_org = self.origin;
	self.rr_spawn_yaw = self.angles_y;
	RR_Park (self);
};

// Called from BM_StartFrame(): spawns 1 Classic Quake Rocket in the NW corner of bakersfielddowntown
void() RocketRider_MapTick =
{
	if (rr_map_spawned || time < 0.8)
		return;
	rr_map_spawned = TRUE;

	if (world.model == "maps/bakersfielddowntown.bsp" || mapname == "bakersfielddowntown")
		RR_SpawnParked ('-13910 6470 6', 315, FALSE);
};

entity(entity p) RocketRider_NearParked =
{
	local entity e, best;
	local float d, bd;

	if (!rr_has_rockets)
		return world;
	best = world;
	bd = 170;
	e = findradius (p.origin, 170);
	while (e != world)
	{
		if (e.classname == "misc_vehicle_rocketrider" && e.health > 0 && !e.rr_dying && e.rr_pilot == world)
		{
			d = vlen (e.origin - p.origin);
			if (d < bd)
			{
				bd = d;
				best = e;
			}
		}
		e = e.chain;
	}
	return best;
};

void() RocketRider_NearPrompt =
{
	local entity rr;

	if (!rr_has_rockets || self.ishuman != 1 || self.health <= 0 || self.rr_vehicle != world
		|| self.jb_vehicle != world || self.veh_van != world || self.veh_ride != world
		|| EricCannon_Active (self) || MMTank_Driving (self) || self.classname != "player")
		return;
	if (time < self.rr_prompt_scan_t)
		return;
	self.rr_prompt_scan_t = time + 0.12;

	rr = RocketRider_NearParked (self);
	if (rr == world)
	{
		if (time > self.rr_prompt_t)
			self.rr_prompt_ent = world;
		return;
	}
	if (self.rr_prompt_ent == rr && time < self.rr_prompt_t)
		return;
	self.rr_prompt_ent = rr;
	self.rr_prompt_t = time + 6.0;
	centerprint (self, "Press H to fly Classic Quake Rocket");
};

float() RocketRider_TryEnterKey =
{
	local entity rr, ec, t, jb, van;
	local float dr;

	if (self.health <= 0 || self.rr_vehicle != world || self.jb_vehicle != world || self.veh_van != world
		|| self.veh_ride != world || EricCannon_Active (self) || MMTank_Driving (self) || FD_Flying (self))
		return FALSE;

	rr = RocketRider_NearParked (self);
	if (rr == world)
		return FALSE;

	dr = vlen (rr.origin - self.origin);
	ec = EricCannon_NearIdle (self);
	if (ec != world && vlen (ec.origin - self.origin) < dr)
		return FALSE;
	t = MMTank_NearFree (self);
	if (t != world && vlen (t.origin - self.origin) < dr)
		return FALSE;
	jb = JohnBird_NearPerched (self);
	if (jb != world && vlen (jb.origin - self.origin) < dr)
		return FALSE;
	van = Veh_SeatOf (self);
	if (van != world && vlen (van.origin - self.origin) < dr)
		return FALSE;

	RR_Enter (self, rr);
	return TRUE;
};

void(entity p) RocketRider_Reset =
{
	local entity rr;

	rr = p.rr_vehicle;
	if (rr != world && !bm_wasfreed (rr) && rr.classname == "misc_vehicle_rocketrider" && rr.rr_pilot == p)
		RR_Leave (rr, rr.origin + '0 0 32', '0 0 0', rr.rr_dying);
	else if (rr != world)
		RR_ReleasePlayer (p, p.origin, '0 0 0', p.v_angle_y);
	p.rr_vehicle = world;
};

entity(entity p) RR_MyTemp =
{
	local entity e;

	e = p.rr_my_temp;
	if (e != world && (bm_wasfreed (e) || e.classname != "misc_vehicle_rocketrider" || !e.rr_temp || e.rr_summoner != p))
	{
		p.rr_my_temp = world;
		e = world;
	}
	return e;
};

void() RocketRider_ClientGone =
{
	local entity rr;

	rr = self.rr_vehicle;
	if (rr != world && !bm_wasfreed (rr) && rr.rr_pilot == self)
		RR_Leave (rr, rr.origin + '0 0 32', '0 0 0', FALSE);
	self.rr_vehicle = world;

	rr = RR_MyTemp (self);
	if (rr != world && rr.rr_pilot == world)
	{
		RR_RemoveRiderEnt (rr);
		if (rr.rr_cam != world && !bm_wasfreed (rr.rr_cam))
			remove (rr.rr_cam);
		remove (rr);
	}
	self.rr_my_temp = world;
};

void() RR_PruneTempRockets =
{
	local entity e, oldest;
	local float n;

	n = 0;
	oldest = world;
	e = find (world, classname, "misc_vehicle_rocketrider");
	while (e != world)
	{
		if (e.rr_temp && e.rr_pilot == world && e.health > 0)
		{
			n = n + 1;
			if (oldest == world)
				oldest = e;
		}
		e = find (e, classname, "misc_vehicle_rocketrider");
	}
	if (n > 5 && oldest != world)
	{
		RR_RemoveRiderEnt (oldest);
		if (oldest.rr_cam != world && !bm_wasfreed (oldest.rr_cam))
			remove (oldest.rr_cam);
		remove (oldest);
	}
};

void() RocketRider_Impulse =
{
	local entity rr;
	local vector org;

	RocketRider_NearPrompt ();
	if (self.impulse != 139 && self.impulse != 140)
		return;
	if (!autocvar_sv_cheats)
		return;

	if (self.impulse == 139)
	{
		self.impulse = 0;
		RR_PruneTempRockets ();
		makevectors ('0 1 0' * self.v_angle_y);
		org = self.origin + v_forward * 170 + '0 0 8';
		traceline (org + '0 0 24', org - '0 0 128', TRUE, self);
		if (trace_fraction < 1 && !trace_startsolid)
			org_z = trace_endpos_z;
		rr = RR_SpawnParked (org, self.v_angle_y, TRUE);
		rr.rr_summoner = self;
		sprint (self, "Spawned parked Classic Quake Rocket ahead! (150 HP - Press H to fly!)\n");
		return;
	}

	if (self.impulse == 140)
	{
		self.impulse = 0;
		if (self.health <= 0 || self.rr_vehicle != world || self.jb_vehicle != world || self.veh_van != world
			|| self.veh_ride != world || FD_Flying (self) || EricCannon_Active (self) || MMTank_Driving (self))
			return;
		tracebox (self.origin + '0 0 14', '-28 -36 -4', '28 36 58', self.origin + '0 0 26', FALSE, self);
		if (trace_startsolid || trace_allsolid || trace_fraction < 1)
		{
			sprint (self, "Need open headroom to summon Classic Quake Rocket!\n");
			return;
		}
		rr = RR_MyTemp (self);
		if (rr != world && rr.rr_pilot == world && rr.health > 0)
		{
			RR_RemoveRiderEnt (rr);
			if (rr.rr_cam != world && !bm_wasfreed (rr.rr_cam))
				remove (rr.rr_cam);
			remove (rr);
			self.rr_my_temp = world;
		}
		rr = RR_SpawnParked (self.origin + '0 0 6', self.v_angle_y, TRUE);
		rr.rr_summoner = self;
		self.rr_my_temp = rr;
		RR_Enter (self, rr);
		return;
	}
};
