#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
GO-KART MARIO KART PHYSICS & MECHANICS (gokart.qc)

Dedicated arcade driving branch for VEH_GOKART_1..6 (progs/gokart_1..6.md3):
  - 64 MD3 frames: 0..11 idle, 12..27 fast drive, 28..43 super boost, 44..63 explode
  - Snappy arcade acceleration & ~1000 u/s cruise, zero sluggish understeer
  - SPACE (+button2): snappy hop on press; hold + steer locks into angled powerslide drift
    charging 3-tier Mini-Turbo sparks (Blue -> Orange -> Purple); release for burst + Nitro refill
  - SHIFT (+button4): rechargeable Nitro meter (0..100) for ~1560 u/s turbo surge, super frames,
    exhaust flames, boost sound, and camera pullback
  - Detects trigger_push jump pads & info_skypad launch pads (sv_maxvelocity 6500), mid-air pitch
    stabilization, and landing boost on touchdown
  - Massive knockback + speed-scaled damage (25-65 HP, lethal at full Shift boost) on players/bots,
    elastic ~75-85% speed bounce off walls/objects/vehicles, swept anti-stuck & curb-step climbing
================
*/

float	GK_TOP_CRUISE	= 1000;		// cruise top speed (~950-1050 u/s)
float	GK_TOP_NITRO	= 1560;		// Shift Nitro top speed (~1500+ u/s)
float	GK_REV_TOP		= 460;		// reverse top speed
float	GK_ACCEL		= 1280;		// snappy arcade acceleration
float	GK_REV_ACCEL	= 900;
float	GK_BRAKE		= 1850;
float	GK_COAST		= 240;
float	GK_TURN_MAX		= 155;		// deg/s at low/mid speed
float	GK_TURN_HI		= 132;		// deg/s at cruise/boost (crisp cornering at all speeds)
float	GK_GRIP			= 3400;		// lateral grip when not drifting
float	GK_GRAVITY		= 800;		// matches sv_gravity & SkyPad_CalcVel ballistic arcs

// Eric's hospital bed (4Loco): slower than before, but it turns hard and grips (playtest: not enough control)
float	FL_TOP_CRUISE	= 900;
float	FL_TOP_NITRO	= 1420;
float	FL_TURN_RATE	= 220;
float	FL_GRIP			= 6000;

float	GK_RKT_TAP_MAX		= 0.18;		// M1 tap <= 0.18s honks horn; holding longer opens rocket aim
float	GK_RKT_CHARGE_T		= 0.80;		// hold duration in aim mode to arm the rocket
float	GK_RKT_NITRO_COST	= 40;		// Nitro spent per rocket shot
float	GK_RKT_COOLDOWN		= 2.50;		// reload cooldown after firing

.float	gk_fx_side;		// tire FX alternate rear wheels (one particle message per tick instead of two)
.float	gk_ex_side;		// exhaust FX alternate the two pipes
.float	gk_hud_key;		// last centerprinted HUD state (resend only when it changes)
.float	gk_hud_keep;	// keep-alive resend so the centerprint never fades while unchanged
.float	gk_pad_scan_t;	// next jump/sky pad scan (entity-list walk throttled to 20 Hz)

void(entity v) GK_InitKart =
{
	v.gk_nitro = 100;
	v.gk_boosting = FALSE;
	v.gk_boost_t = 0;
	v.gk_boost_pwr = 0;
	v.gk_hop_prev = FALSE;
	v.gk_drift_dir = 0;
	v.gk_drift_charge = 0;
	v.gk_drift_tier = 0;
	v.gk_drift_fx_t = 0;
	v.gk_boost_snd_t = 0;
	v.gk_pad_cool = 0;
	v.gk_air_t = 0;
	v.gk_hud_t = 0;
	v.gk_speed = 0;
	v.gk_smoke_t = 0;
	v.gk_m1_prev = FALSE;
	v.gk_m1_hold_t = 0;
	v.gk_rkt_aim = FALSE;
	v.gk_aim_enter = FALSE;
	v.gk_rkt_charge = 0;
	v.gk_rkt_armed = FALSE;
	v.gk_rkt_cd = 0;
};

// Cockpit view: the driver sees his own arms and hands on the wheel, but not the inside of his head.
// gokart_driver.md3 skin 1 (zz_karts.pk3) draws the "head" surface with an invisible shader.
float() GK_DriverCustomize =
{
	local entity v;

	v = self.owner;
	if (v != world && other == v.veh_driver && other.veh_camera == 0)
		self.skin = 1;
	else
		self.skin = 0;
	return TRUE;
};

// Keep attached seated Quake Ranger driver entity synced to kart origin, angles & animation frame
void(entity v) GK_SyncDriverEnt =
{
	local entity de;

	de = v.veh_driverent;
	if (de == world)
		return;
	if (v.veh_driver == world || v.veh_state == VEH_STATE_WRECK)
	{
		remove (de);
		v.veh_driverent = world;
		return;
	}
	setorigin (de, v.origin);
	de.angles = v.angles;
	de.frame = v.frame;
	// drawn for everyone; in cockpit view the driver gets the headless skin (GK_DriverCustomize)
	de.owner = v;
	de.customizeentityforclient = GK_DriverCustomize;
	de.nodrawtoclient = world;
	de.effects = de.effects - (de.effects & EF_NODRAW);
};

// Frame ranges on gokart_1..6.md3: 0..11 idle, 12..27 fast drive, 28..43 super boost, 44..63 explode
// Keep rate <= 1.0 so MD3 vertex interpolation (r_lerpmodels) never skips frames and collapses spinning wheels.
void(entity v) GK_ThinkAnim =
{
	local float rate, spd, boosted;

	if (v.veh_state == VEH_STATE_WRECK || v.veh_kind == VEH_FORELOCO)
		return;

	if (v.veh_driver == world && v.veh_coast_until <= 0)
	{
		v.frame = 0;
		GK_SyncDriverEnt (v);
		return;
	}

	spd = v.gk_speed;
	boosted = (v.gk_boosting || time < v.gk_boost_t);
	if (v.veh_driver != world && boosted)
		rate = 1.0;
	else if ((v.veh_driver != world || v.veh_coast_until > 0) && spd > 35)
		rate = 0.45 + 0.55 * bound (0, spd / GK_TOP_CRUISE, 1);
	else
		rate = 0.55;

	v.veh_anim = v.veh_anim + rate;
	if (v.veh_driver != world && boosted)
	{
		v.veh_anim = v.veh_anim - 16 * floor (v.veh_anim / 16);
		v.frame = 28 + floor (v.veh_anim);
	}
	else if ((v.veh_driver != world || v.veh_coast_until > 0) && spd > 35)
	{
		v.veh_anim = v.veh_anim - 16 * floor (v.veh_anim / 16);
		v.frame = 12 + floor (v.veh_anim);
	}
	else
	{
		v.veh_anim = v.veh_anim - 12 * floor (v.veh_anim / 12);
		v.frame = floor (v.veh_anim);
	}

	GK_SyncDriverEnt (v);
};

// Emit thick rear tire smoke & optional rim sparks during peel-outs, burnouts, and high-speed skids
void(entity v, float slip_mag, float with_sparks) GK_PeelAndSkidFX =
{
	local vector fwd, lft, rw, smkvel;
	local float vol, pitch;

	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	smkvel = fwd * -48 + '0 0 28';

	// network: one message per effect per tick, alternating rear wheels, 3x count (was both wheels every 0.045 s)
	if (time >= v.gk_smoke_t)
	{
		v.gk_smoke_t = time + 0.065;
		v.gk_fx_side = 1 - v.gk_fx_side;
		if (v.gk_fx_side)
			rw = v.origin - fwd * 28 + lft * 26 + '0 0 4';
		else
			rw = v.origin - fwd * 28 - lft * 26 + '0 0 4';
		if (gk_fx_smoke > 0)
			pointparticles (gk_fx_smoke, rw, smkvel, 3);
		if (with_sparks && veh_fx_drift > 0)
			pointparticles (veh_fx_drift, rw, smkvel, 3);
		else if (gk_fx_smoke <= 0 && veh_fx_smoke > 0)
			pointparticles (veh_fx_smoke, rw, smkvel, 3);
	}

	if (time >= v.veh_skid_t)
	{
		vol = bound (0.38, slip_mag / 260, 0.92);
		pitch = bound (88, 96 + slip_mag * 0.08, 138);
		sound7 (v, VD_SOUND_CH, "vehicles/tire_squeal.wav", vol, ATTN_NORM, pitch);
		v.veh_skid_t = time + 0.24;
	}
};

// Emit Blue / Orange / Purple Mini-Turbo sparks + thick tire smoke from both rear tires while drifting
void(entity v, float tier) GK_DriftSparks =
{
	local vector fwd, lft, rw, spvel, side;
	local float col;

	// network: alternate rear wheels, one message per effect, 3x count (caller ticks every 0.08 s, was both wheels every 0.055 s)
	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	v.gk_fx_side = 1 - v.gk_fx_side;
	if (v.gk_fx_side)
		side = lft;
	else
		side = lft * -1;
	rw = v.origin - fwd * 30 + side * 26 + '0 0 4';
	spvel = fwd * -90 + '0 0 55';

	if (gk_fx_smoke > 0)
		pointparticles (gk_fx_smoke, rw, fwd * -45 + '0 0 24', 3);
	if (veh_fx_drift > 0)
		pointparticles (veh_fx_drift, rw, spvel, 3);
	if (tier == 1)
		col = 212;		// Blue sparks
	else if (tier == 2)
		col = 194;		// Orange sparks
	else if (tier >= 3)
		col = 149;		// Purple / Ultra sparks
	else
		col = 15;		// Neutral white/grey drift dust

	particle (rw, spvel + side * 40, col, (6 + tier * 4) * 3);	// <= 54, well under 255 (= explosion)
	if (tier >= 2 && veh_fx_boost > 0)
		pointparticles (veh_fx_boost, rw, spvel, 3);
};

// Emit twin rear exhaust flames & sparks during Shift Nitro or Mini-Turbo
void(entity v) GK_BoostExhaust =
{
	local vector fwd, lft, ex;

	if (veh_fx_boost <= 0)
		return;
	// network: alternate the two pipes with 3x count, one message per call (drive frame ticks every 0.05 s, was 2 per 0.035 s)
	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	v.gk_ex_side = 1 - v.gk_ex_side;
	if (v.gk_ex_side)
		ex = v.origin - fwd * 44 + lft * 11 + '0 0 14';
	else
		ex = v.origin - fwd * 44 - lft * 11 + '0 0 14';
	pointparticles (veh_fx_boost, ex, fwd * -150, 3);
	if (v.veh_kind == VEH_FORELOCO)
	{
		pointparticles (veh_fx_boost, v.origin - fwd * 36 + '0 0 18', fwd * -220, 4);
		if (veh_fx_sparks > 0)
			pointparticles (veh_fx_sparks, ex, fwd * -120 + '0 0 40', 2);
	}
};

// Clean, compact Nitro & Drift HUD via centerprint toast. Network: a ~180 B reliable message, so it is only resent
// when what it shows changes (10% nitro steps, colour, tag; no live speed number), at most 2x a second by the caller,
// plus a 1.5 s keep-alive so the centerprint (scr_centertime 2) never fades while the text is unchanged.
void(entity p, entity v, float dirty) GK_UpdateHUD =
{
	local float pct, segs, i, cidx, tidx, key;
	local string bar, ncolor, tag, line1, line2;

	if (p.ishuman != 1)
		return;

	pct = floor (bound (0, v.gk_nitro, 100) + 0.5);
	segs = floor (pct / 10 + 0.49);
	if (segs > 10)
		segs = 10;
	if (segs < 0)
		segs = 0;

	if (v.gk_boosting)
		cidx = 0;
	else if (pct >= 60)
		cidx = 1;
	else if (pct >= 25)
		cidx = 2;
	else
		cidx = 3;

	if (v.gk_boosting)
		tidx = 1;
	else if (time < v.gk_boost_t)
		tidx = 2;
	else if (v.gk_drift_tier == 3)
		tidx = 3;
	else if (v.gk_drift_tier == 2)
		tidx = 4;
	else if (v.gk_drift_tier == 1)
		tidx = 5;
	else if (v.veh_air && v.gk_air_t > 0.25)
		tidx = 6;
	else
		tidx = 0;

	key = segs + 11 * cidx + 44 * tidx;
	if (!dirty && v.gk_hud_t > 0 && key == v.gk_hud_key && time < v.gk_hud_keep)
		return;		// gk_hud_t == 0: just entered (vehicle_drive.qc), always send
	v.gk_hud_key = key;
	v.gk_hud_keep = time + 1.5;
	v.gk_hud_t = time + 0.5;

	if (cidx == 0)
		ncolor = "^x0ff";
	else if (cidx == 1)
		ncolor = "^2";
	else if (cidx == 2)
		ncolor = "^3";
	else
		ncolor = "^1";

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
		tag = "  ^x0ff>> NITRO <<";
	else if (tidx == 2)
		tag = "  ^xfe4>> TURBO! <<";
	else if (tidx == 3)
		tag = "  ^xe4f[PURPLE MT]";
	else if (tidx == 4)
		tag = "  ^xfa0[ORANGE MT]";
	else if (tidx == 5)
		tag = "  ^4[BLUE MT]";
	else if (tidx == 6)
		tag = "  ^5[AIR +NITRO]";

	line1 = strcat ("^3NITRO ^7[", ncolor, bar, "^7] ", ncolor, ftos (segs * 10));
	line1 = strcat (line1, "%", tag);
	line2 = "^7WASD Drive  ^3SPACE^7 Drift  ^3SHIFT^7 Nitro  ^3M1^7 Horn / Hold Rocket  ^3K^7 Cam  ^3H^7 Exit";
	centerprint (p, strcat (line1, "\n", line2));
};

// Hull overlap test for trigger_push and info_skypad
float(vector bmin, vector bmax, entity pad) GK_OverlapPad =
{
	if (bmin_x > pad.absmax_x || bmax_x < pad.absmin_x)
		return FALSE;
	if (bmin_y > pad.absmax_y || bmax_y < pad.absmin_y)
		return FALSE;
	if (bmin_z > pad.absmax_z || bmax_z < pad.absmin_z)
		return FALSE;
	return TRUE;
};

float(entity v, entity driver) GK_CheckPads =
{
	local entity e;
	local vector bmin, bmax, vel, hvel;
	local float spd, maxv;

	if (time < v.gk_pad_cool)
		return FALSE;
	// two find() walks over every entity: 20 Hz is plenty (75 u at full nitro, shorter than the 104 u kart)
	if (time < v.gk_pad_scan_t)
		return FALSE;
	v.gk_pad_scan_t = time + 0.05;

	bmin = v.origin + '-52 -36 -4';
	bmax = v.origin + '52 36 44';

	if (skypad_present)
	{
		e = skypad_head;
		while (e != world)
		{
			if (!bm_wasfreed (e) && GK_OverlapPad (bmin, bmax, e))
			{
				SkyPad_RaiseMaxVel ();
				if (driver != world && driver.ishuman == 1 && !driver.skypad_vel_sent)
				{
					driver.skypad_vel_sent = TRUE;
					stuffcmd (driver, "sv_maxvelocity 6500\n");
				}
				vel = SkyPad_CalcVel (v.origin + '0 0 2', e.pos1, e.height);
				v.gk_pad_cool = time + 0.65;
				v.veh_air = TRUE;
				v.veh_vz = vel_z;
				v.velocity = vel;
				hvel = vel;
				hvel_z = 0;
				if (vlen (hvel) > 120)
					v.angles_y = vectoyaw (hvel);
				setorigin (v, v.origin + '0 0 4');
				sound7 (v, CHAN_AUTO, "skypad/launch.wav", 0.85, ATTN_NORM, SNDSPD * (0.96 + random () * 0.08));
				pointparticles (particleeffectnum ("TE_TELEPORT"), e.origin + '0 0 12', '0 0 0', 1);
				if (e.message != "" && driver != world && driver.ishuman == 1)
					sprint (driver, strcat ("Sky Pad -> ", e.message, "\n"));
				return TRUE;
			}
			e = e.skypad_next;
		}
	}

	e = bm_push_head;
	while (e != world)
	{
		if (!bm_wasfreed (e) && GK_OverlapPad (bmin, bmax, e))
		{
			spd = e.speed;
			if (!spd)
				spd = 1000;
			if (e.spawnflags & ADD_VEL)
				vel = v.velocity + spd * e.movedir * 5;
			else
				vel = spd * e.movedir * 10;
			if (vlen (vel) > 1800)
			{
				SkyPad_RaiseMaxVel ();
				if (driver != world && driver.ishuman == 1 && !driver.skypad_vel_sent)
				{
					driver.skypad_vel_sent = TRUE;
					stuffcmd (driver, "sv_maxvelocity 6500\n");
				}
			}
			maxv = cvar ("sv_maxvelocity");
			if (maxv <= 0)
				maxv = 2000;
			vel_x = bound (0 - maxv, vel_x, maxv);
			vel_y = bound (0 - maxv, vel_y, maxv);
			vel_z = bound (0 - maxv, vel_z, maxv);

			v.gk_pad_cool = time + 0.40;
			v.velocity = vel;
			if (vel_z > 10)
			{
				v.veh_air = TRUE;
				v.veh_vz = vel_z;
				setorigin (v, v.origin + '0 0 4');
			}
			hvel = vel;
			hvel_z = 0;
			if (vlen (hvel) > 200)
				v.angles_y = vectoyaw (hvel);
			v.gk_boost_t = max (v.gk_boost_t, time + 0.60);
			v.gk_boost_pwr = max (v.gk_boost_pwr, 1380);
			if (!(e.spawnflags & NO_SOUND))
				sound7 (v, CHAN_AUTO, "ambience/windfly.wav", 0.78, ATTN_NORM, SNDSPD * (0.95 + random () * 0.12));
			if (e.spawnflags & PUSH_ONCE)
				remove (e);
			return TRUE;
		}
		e = e.bm_push_next;
	}
	return FALSE;
};

vector	gk_slip_pos;	// resolved lateral corner-slip position from GK_TryCornerSlip

// Check if the kart's rotated hull overlaps solid BSP geometry (nomonsters=TRUE so bots/players never trigger warps)
float(entity v, vector org, float yaw) GK_IsEmbedded =
{
	local float i, c, s;
	local vector o, p;

	tracebox (org + '0 0 22', '-16 -16 0', '16 16 20', org + '0 0 22', TRUE, v);
	if (trace_startsolid || trace_allsolid)
		return TRUE;
	c = Veh_Cos (yaw);
	s = Veh_Sin (yaw);
	i = 0;
	while (i < 4)
	{
		if (i == 0) o = '26 14 0';
		else if (i == 1) o = '26 -14 0';
		else if (i == 2) o = '-26 14 0';
		else o = '-26 -14 0';
		p = org;
		p_x = org_x + c * o_x - s * o_y;
		p_y = org_y + s * o_x + c * o_y;
		p_z = org_z + 22;
		tracebox (p, '-8 -8 0', '8 8 20', p, TRUE, v);
		if (trace_startsolid || trace_allsolid)
			return TRUE;
		i = i + 1;
	}
	return FALSE;
};

// Automatic anti-stuck depenetration nudge
void(entity v) GK_Depenetrate =
{
	local float rad, ang, a;
	local vector cand;

	if (!GK_IsEmbedded (v, v.origin, v.angles_y))
		return;

	rad = 12;
	while (rad <= 36)
	{
		ang = 0;
		while (ang < 8)
		{
			a = ang * 45;
			cand = v.origin + Veh_Fwd (a) * rad;
			if (!GK_IsEmbedded (v, cand, v.angles_y))
			{
				setorigin (v, cand);
				return;
			}
			ang = ang + 1;
		}
		cand = v.origin + '0 0 1' * rad;
		if (!GK_IsEmbedded (v, cand, v.angles_y))
		{
			setorigin (v, cand);
			return;
		}
		rad = rad + 12;
	}
};

// Chamfered capsule-like 20-hull perimeter (~88u x 52u with rounded corners) so karts don't snag on street junk
vector(float i) GK_ProbeOfs =
{
	local float k;

	if (i == 0) return '26 -15 0';
	if (i == 1) return '34 -5 0';
	if (i == 2) return '34 5 0';
	if (i == 3) return '26 15 0';
	if (i == 4) return '-26 -15 0';
	if (i == 5) return '-34 -5 0';
	if (i == 6) return '-34 5 0';
	if (i == 7) return '-26 15 0';
	if (i < 14)
	{
		k = i - 8;
		return '0 16 0' + '1 0 0' * (-18 + 7.2 * k);
	}
	k = i - 14;
	return '0 -16 0' + '1 0 0' * (-18 + 7.2 * k);
};

// Swept footprint around the kart at z+22..z+42 so <=22u pipes/curbs pass underneath cleanly
float(entity v, vector org0, float yaw0, vector org1, float yaw1, float zbase) GK_Sweep =
{
	local float i, best, c0, s0, c1, s1;
	local vector o, p0, p1;

	c0 = Veh_Cos (yaw0);
	s0 = Veh_Sin (yaw0);
	c1 = Veh_Cos (yaw1);
	s1 = Veh_Sin (yaw1);
	best = 1;
	vd_hitent = world;
	vd_hitnorm = '0 0 0';
	i = 0;
	while (i < 20)
	{
		o = GK_ProbeOfs (i);
		p0 = org0;
		p0_x = org0_x + c0 * o_x - s0 * o_y;
		p0_y = org0_y + s0 * o_x + c0 * o_y;
		p0_z = org0_z + zbase;
		p1 = org1;
		p1_x = org1_x + c1 * o_x - s1 * o_y;
		p1_y = org1_y + s1 * o_x + c1 * o_y;
		p1_z = org1_z + zbase;
		tracebox (p0, '-10 -10 0', '10 10 20', p1, FALSE, v);
		if (!trace_startsolid && trace_fraction < best && trace_plane_normal_z < 0.7)
		{
			best = trace_fraction;
			vd_hitnorm = trace_plane_normal;
			vd_hitpos = trace_endpos;
			vd_hitent = trace_ent;
		}
		i = i + 1;
	}
	if (best >= 1)
		return TRUE;
	vd_hitnorm_z = 0;
	if (vlen (vd_hitnorm) < 0.01)
		vd_hitnorm = Veh_Fwd (yaw0) * -1;
	vd_hitnorm = normalize (vd_hitnorm);
	return FALSE;
};

// Try a subtle sideways slip around a narrow pole, pipe, or wall-corner snag without changing heading/camera
float(entity v, vector org0, float yaw0, vector org1, float yaw1, vector lft, vector hitpos) GK_TryCornerSlip =
{
	local float side_dot, try_idx, nudge;
	local vector dir, step0, cand;

	side_dot = (hitpos - org0) * lft;
	if (side_dot >= 0)
		dir = lft * -1;
	else
		dir = lft;

	try_idx = 0;
	while (try_idx < 2)
	{
		nudge = 10;
		while (nudge <= 18)
		{
			step0 = org0 + dir * nudge;
			if (GK_Sweep (v, org0, yaw0, step0, yaw0, 22))
			{
				cand = org1 + dir * nudge;
				if (GK_Sweep (v, step0, yaw0, cand, yaw1, 22))
				{
					gk_slip_pos = cand;
					return TRUE;
				}
			}
			nudge = nudge + 8;
		}
		// Only try the other side if the snag was nearly dead-center on the nose
		if (fabs (side_dot) > 6)
			break;
		dir = dir * -1;
		try_idx = try_idx + 1;
	}
	return FALSE;
};

entity(entity v) GK_DamageAttacker =
{
	if (v.veh_driver != world)
		return v.veh_driver;
	if (v.veh_igniter != world)
		return v.veh_igniter;
	return v;
};

// Small breakable street/room props the kart should plow straight through (excludes explosive barrels & structural map pieces)
float(entity e) GK_IsSmashableProp =
{
	if (e == world || !e.takedamage)
		return FALSE;
	if (e.veh_kind > 0 || e.classname == "veh_van_clip")
		return FALSE;
	if (e.lan_kind > 0)
		return TRUE;
	if (e.classname == "misc_bicycle" || e.classname == "misc_bike_cruiser" || e.classname == "misc_bike_bmx" || e.classname == "misc_bike_road")
		return TRUE;
	if (e.classname == "bk_trashcan")
		return TRUE;
	return FALSE;
};

// Kart hits a player, bot, or monster: massive launch knockback + 25-65 HP (lethal at full Shift boost)
float(entity v, entity hit, float spd) GK_RamLiving =
{
	local entity driver;
	local float dmg;
	local vector dir;

	if (time < hit.veh_hit_t || hit.veh_ride == v || (hit.veh_last_van == v && time < hit.veh_bail_safe_t))
		return FALSE;
	if (spd < (v.veh_kind == VEH_FORELOCO ? 90 : 150))
		return FALSE;

	driver = GK_DamageAttacker (v);

	dir = v.velocity;
	dir_z = 0;
	if (vlen (dir) > 10)
		dir = normalize (dir);
	else
		dir = Veh_Fwd (v.angles_y);

	if (v.veh_kind == VEH_FORELOCO)
	{
		dmg = bound (50, 50 + (spd - 100) * 0.09, 150);
		if (v.gk_boosting)
			dmg = max (dmg, 125);
		hit.veh_hit_t = time + 0.35;
		hit.flags = hit.flags - (hit.flags & FL_ONGROUND);
		setorigin (hit, hit.origin + '0 0 6');
		hit.velocity = dir * (760 + spd * 0.72) + '0 0 1' * (520 + spd * 0.34);
		if (driver.classname == "player" && driver.fl_phase == 3)
		{
			driver.fl_hits = driver.fl_hits + 1;
			v.health = min (v.max_health, v.health + 15);
		}
		sound7 (hit, CHAN_BODY, "foreloco/boing_hit.wav", 1, ATTN_NORM, 92 + random () * 20);
		if (veh_fx_sparks > 0)
			pointparticles (veh_fx_sparks, hit.origin + '0 0 24', '0 0 0', 2);
		if (veh_fx_drift > 0)
			pointparticles (veh_fx_drift, hit.origin + '0 0 24', '0 0 0', 2);
	}
	else
	{
		if (v.gk_boosting && spd >= 1150)
			dmg = 125;		// lethal only at full Shift boost
		else
			dmg = bound (25, 25 + (spd - 200) * (40 / 850), 65);

		hit.veh_hit_t = time + 0.45;
		hit.flags = hit.flags - (hit.flags & FL_ONGROUND);
		setorigin (hit, hit.origin + '0 0 4');
		hit.velocity = dir * (560 + spd * 0.55) + '0 0 1' * (380 + spd * 0.25);

		sound7 (hit, CHAN_BODY, "vehicles/tire_thud1.wav", 1, ATTN_NORM, 78 + random () * 18);
		if (veh_fx_sparks > 0)
			pointparticles (veh_fx_sparks, hit.origin + '0 0 24', '0 0 0', 1);
	}

	veh_runover = TRUE;
	T_Damage (hit, v, driver, dmg);
	veh_runover = FALSE;
	if ((hit.flags & FL_MONSTER) && hit.health <= 0)
		hit.solid = SOLID_NOT;
	return TRUE;
};

// Kart smashes cleanly through breakable street/room props (bikes, LAN gear, rocket trashcans)
float(entity v, entity hit, float spd) GK_SmashProp =
{
	local entity driver;
	local float dmg;

	if (spd < 110)
		return FALSE;
	driver = GK_DamageAttacker (v);
	dmg = max (160, hit.health + 60);
	sound7 (hit, CHAN_BODY, "vehicles/tire_thud1.wav", 0.85, ATTN_NORM, 92 + random () * 16);
	if (veh_fx_sparks > 0)
		pointparticles (veh_fx_sparks, hit.origin + '0 0 16', '0 0 0', 1);
	veh_runover = TRUE;
	T_Damage (hit, v, driver, dmg);
	veh_runover = FALSE;
	return TRUE;
};

// Kart bumps another vehicle/kart: deal bump damage without hurting our own kart
void(entity v, entity hit, float imp) GK_RamVehicle =
{
	local entity driver;
	local float dmg;

	if (imp < 140 || time < hit.veh_hit_t)
		return;
	driver = GK_DamageAttacker (v);
	hit.veh_hit_t = time + 0.35;
	dmg = bound (12, (imp - 100) * 0.08, 55);
	if (v.gk_boosting)
		dmg = dmg * 1.5;
	if (v.veh_kind == VEH_FORELOCO)
	{
		dmg = dmg * 1.6;
		v.veh_air = TRUE;
		v.veh_vz = max (v.veh_vz, 310);
		setorigin (v, v.origin + '0 0 8');
		sound7 (v, CHAN_BODY, "foreloco/boing_hit.wav", 0.95, ATTN_NORM, 108 + random () * 14);
	}
	if (veh_fx_sparks > 0)
		pointparticles (veh_fx_sparks, vd_hitpos, '0 0 0', 1);
	veh_runover = TRUE;
	T_Damage (hit, v, driver, dmg);
	veh_runover = FALSE;
};

void() GK_RocketSeek;

void() GK_RocketThink =
{
	local float rem;

	// Wait up to 0.28s total if still right on top of the firing kart (e.g. cruising downward shots),
	// then hand ownership back to the driver so frag credit and high-speed Nitro rear-ends work cleanly.
	if (self.gk_kart != world && !bm_wasfreed (self.gk_kart))
	{
		if (time < self.gk_safe_t + 0.14 && vlen (self.origin - self.gk_kart.origin) < 58)
		{
			self.nextthink = time + 0.04;
			return;
		}
	}
	if (self.gk_shooter != world && !bm_wasfreed (self.gk_shooter))
		self.owner = self.gk_shooter;
	if (self.gk_seek != world)
	{
		self.think = GK_RocketSeek;		// heat seeker
		self.nextthink = time;
		return;
	}
	rem = max (0.10, (self.gk_safe_t + 4.86) - time);
	self.think = SUB_Remove;
	self.nextthink = time + rem;
};

void() GK_RocketTouch =
{
	if (other != world && self.gk_shooter != world && other == self.gk_shooter)
		return;
	if (other != world && self.gk_kart != world && !bm_wasfreed (self.gk_kart) && other == self.gk_kart.veh_driverent)
		return;
	if (other == self.gk_kart && time < self.gk_safe_t)
		return;
	if (self.gk_shooter != world && !bm_wasfreed (self.gk_shooter))
		self.owner = self.gk_shooter;
	T_MissileTouch ();
};

// ---------------------------------------------------------------- heat-seeking rockets
// While the rocket crosshair is up, another player near it (on foot, in a vehicle or in a tank) is locked on, and the
// rocket fired then follows him.

float	GK_LOCK_RANGE	= 3500;
float	GK_LOCK_CONE	= 0.93;		// cos of the angle from the crosshair to get a lock (about 21 degrees)
float	GK_LOCK_KEEP	= 0.82;		// ...and to keep it
float	GK_SEEK_SPEED	= 1150;
float	GK_SEEK_TURN	= 7;		// how fast the rocket turns onto its target (fraction of the gap per second)

// what stands for player e in the world right now (his vehicle or tank while he is in one)
entity(entity e) GK_LockBody =
{
	if (e.veh_van != world && e.veh_van.veh_driver == e)
		return e.veh_van;
	if (e.mmt_tank != world && e.mmt_tank.mmt_driver == e)
		return e.mmt_tank;
	return e;
};

vector(entity e) GK_LockPoint =
{
	local entity b;

	b = GK_LockBody (e);
	if (b.classname == "misc_mm_tank")
		return b.origin + '0 0 63';
	if (b != e)
		return b.origin + '0 0 24';
	return e.origin + '0 0 4';
};

float(entity p, entity e) GK_Lockable =
{
	if (e == world || e == p || bm_wasfreed (e) || e.classname != "player" || e.health <= 0)
		return FALSE;
	if ((e.items & IT_INVISIBILITY) || ((e.flags & FL_NOTARGET) && e.mmt_tank == world))
		return FALSE;
	if (teamplay && p.team > 0 && e.team == p.team)
		return FALSE;
	return TRUE;
};

// how well e sits under the crosshair: the cosine, or -1 if out of range or hidden
float(entity v, entity e, vector from, vector dir) GK_LockScore =
{
	local vector to;
	local float c;

	to = GK_LockPoint (e) - from;
	if (vlen (to) > GK_LOCK_RANGE)
		return -1;
	c = normalize (to) * dir;
	traceline (v.origin + '0 0 44', GK_LockPoint (e), TRUE, v);
	if (trace_fraction < 0.98 && trace_ent != GK_LockBody (e))
		return -1;
	return c;
};

void(entity p, entity v) GK_UpdateLock =
{
	local entity e, best, cam;
	local vector from, dir, ang, pt;
	local float c, bc;

	best = world;
	if (v.gk_rkt_aim)
	{
		cam = v.veh_cament;
		from = (cam != world) ? cam.origin : v.origin + '0 0 44';
		ang = '0 0 0';
		ang_x = p.veh_cam_pitch;
		ang_y = p.veh_cam_yaw;
		makevectors (ang);
		dir = v_forward;
		if (GK_Lockable (p, v.gk_lock_ent) && GK_LockScore (v, v.gk_lock_ent, from, dir) > GK_LOCK_KEEP)
			best = v.gk_lock_ent;
		else
		{
			bc = GK_LOCK_CONE;
			e = bm_player_head;
			while (e)
			{
				if (GK_Lockable (p, e))
				{
					c = GK_LockScore (v, e, from, dir);
					if (c > bc)
					{
						best = e;
						bc = c;
					}
				}
				e = e.bm_player_next;
			}
		}
	}
	if (best != world && best != v.gk_lock_ent && p.ishuman == 1)
		FG_Snd (p, CHAN_AUTO, "bikes/spoke_ping.wav", 1, 1.6);
	v.gk_lock_ent = best;
	if (p.ishuman == 1)
	{
		p.gk_st_lock = (best != world);
		if (best != world)
		{
			pt = GK_LockPoint (best);
			p.gk_st_tx = floor (pt_x);
			p.gk_st_ty = floor (pt_y);
			p.gk_st_tz = floor (pt_z);
		}
	}
};

void() GK_RocketSeek =
{
	local vector want, dir, pt;
	local entity body, oth;
	local float d;

	if (time >= self.gk_safe_t + 4.86)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.03;
	if (time < self.skypad_steer_t)
		return;
	if (!GK_Lockable (self.gk_shooter, self.gk_seek))
		return;			// target gone: fly straight on
	body = GK_LockBody (self.gk_seek);
	pt = GK_LockPoint (self.gk_seek);
	d = vlen (pt - self.origin);
	// proximity fuse: a near miss still counts, or it would circle its target and plough into the road
	if (d < ((body == self.gk_seek) ? 56 : 90))
	{
		oth = other;
		other = body;
		GK_RocketTouch ();
		other = oth;
		return;
	}
	want = normalize (pt + body.velocity * min (0.4, d / GK_SEEK_SPEED) - self.origin);		// lead a moving target
	dir = normalize (self.velocity);
	dir = normalize (dir + (want - dir) * min (1, GK_SEEK_TURN * 0.03 * 1.5));
	self.velocity = dir * GK_SEEK_SPEED;
	self.angles = vectoangles (self.velocity);
};

void(entity p, entity v) GK_FireRocket =
{
	local entity missile, cam;
	local vector cam_org, aim_ang, launch_org, dir, aim_pt;
	local float cam_dist;

	cam = v.veh_cament;
	aim_ang = '0 0 0';
	aim_ang_x = p.veh_cam_pitch;
	aim_ang_y = p.veh_cam_yaw;
	makevectors (aim_ang);

	if (cam != world)
		cam_org = cam.origin;
	else
		cam_org = v.origin + '0 0 44';

	// Launch cleanly above the 34u kart hull and stop before nearby walls
	launch_org = v.origin + '0 0 44';
	if (v_forward_z > -0.15)
	{
		traceline (launch_org, launch_org + v_forward * 24, FALSE, v);
		if (trace_fraction > 0.25)
			launch_org = trace_endpos - v_forward * 4;
	}

	// 3rd-person crosshair convergence: trace from chase camera onto target/wall
	dir = v_forward;
	if (p.veh_camera != 0)
	{
		traceline (cam_org, cam_org + v_forward * 4096, FALSE, v);
		aim_pt = trace_endpos;
		cam_dist = vlen (aim_pt - cam_org);
		if (cam_dist > max (80, p.veh_cam_dist + 24) && vlen (aim_pt - launch_org) > 24)
			dir = normalize (aim_pt - launch_org);
	}

	sound7 (v, CHAN_WEAPON, "weapons/sgun1.wav", 1, ATTN_NORM, SNDSPD);
	sound7 (v, CHAN_AUTO, "weapons/rocket2i.wav", 0.9, ATTN_NORM, SNDSPD);

	missile = spawn ();
	missile.cansplash = TRUE;
	// Own to the kart briefly so engine physics pass cleanly through the kart hull,
	// then GK_RocketThink / GK_RocketTouch switches .owner to the driver p for frag credit & self-collision.
	missile.owner = v;
	missile.gk_shooter = p;
	missile.gk_kart = v;
	missile.gk_safe_t = time + 0.14;
	missile.movetype = MOVETYPE_FLYMISSILE;
	missile.solid = SOLID_BBOX;
	missile.classname = "missile";
	missile.velocity = dir * 1000;
	missile.angles = vectoangles (missile.velocity);
	missile.touch = GK_RocketTouch;
	missile.nextthink = time + 0.14;
	missile.think = GK_RocketThink;
	if (GK_Lockable (p, v.gk_lock_ent))
		missile.gk_seek = v.gk_lock_ent;
	setmodel (missile, "progs/missile.mdl");
	setsize (missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (missile, launch_org);
};

float	GK_COCKPIT_TILT		= 32;		// degrees the cockpit view looks down, to show the wheel and hands
float	GK_COCKPIT_X		= -8;		// cockpit eye in kart space (driver head: x -9.5..0, z 34.5..45; shoulders z <= 38)
float	GK_COCKPIT_Z		= 40;

void(entity p, entity v, float dt) GK_DriveCamera =
{
	local entity cam;
	local vector fwd, pos, tgt, ang, vel_xy;
	local float yaw, pitch, d, spd, lead, cdist, cup, lock_view;
	local float want_dist, spd_frac, vf_cam, look_fwd, tgt_yaw, vel_d, want_pitch, boosted;

	cam = v.veh_cament;
	fwd = Veh_Fwd (v.angles_y);
	vel_xy = v.velocity;
	vel_xy_z = 0;
	spd = vlen (vel_xy);
	boosted = (v.gk_boosting || time < v.gk_boost_t);
	lock_view = (!v.gk_rkt_aim || v.gk_aim_enter);

	if (p.veh_camera == 0)
	{
		// eye where the driver's eyes are (his head is hidden from him: GK_DriverCustomize), above the shoulders,
		// so the wheel and his hands are in front of you (playtest 1.76); the view tilts down (GK_COCKPIT_TILT)
		pos = v.origin + fwd * GK_COCKPIT_X + '0 0 1' * GK_COCKPIT_Z;
		if (v.gk_rkt_aim)
		{
			if (v.gk_aim_enter)
			{
				v.gk_aim_enter = FALSE;
				yaw = p.veh_cam_yaw;
				pitch = p.veh_cam_pitch;
			}
			else
			{
				yaw = Veh_NormYaw (p.v_angle_y);
				pitch = bound (-70, p.v_angle_x, 75);
				p.veh_cam_yaw = yaw;
				p.veh_cam_pitch = pitch;
			}
		}
		else
		{
			lead = 0 - v.veh_steer * 10 * bound (0, spd / 240, 1);
			p.veh_cam_look = p.veh_cam_look + (lead - p.veh_cam_look) * min (1, dt * 6);
			yaw = Veh_NormYaw (v.angles_y + p.veh_cam_look);
			pitch = GK_COCKPIT_TILT - v.angles_x;
			p.veh_cam_yaw = yaw;
			p.veh_cam_pitch = pitch;
		}
	}
	else
	{
		cdist = 136;
		cup = 48;
		spd_frac = bound (0, spd / GK_TOP_CRUISE, 1);
		want_dist = cdist + 30 * spd_frac;
		if (boosted)
			want_dist = want_dist + 36;
		if (p.veh_cam_dist < 80)
			p.veh_cam_dist = want_dist;
		p.veh_cam_dist = p.veh_cam_dist + (want_dist - p.veh_cam_dist) * min (1, dt * 6.0);

		if (v.veh_kind == VEH_FORELOCO && p.fl_phase == 3 && (time - p.fl_t0) < FL_INTRO_DUR)
		{
			// Smooth 360-degree situation reveal orbit around Eric in the hospital bed
			local float fl_u, fl_s;
			fl_u = bound (0, (time - p.fl_t0) / FL_INTRO_DUR, 1);
			fl_s = fl_u * fl_u * (3 - 2 * fl_u);
			cdist = 166 - 24 * fl_s;
			cup = 46;
			p.veh_cam_dist = cdist;
			yaw = Veh_NormYaw (v.angles_y + 360 * (1 - fl_s));
			pitch = 16 - 4 * fl_s;
			p.veh_cam_yaw = yaw;
			p.veh_cam_pitch = pitch;
			tgt = v.origin + '0 0 1' * cup;
		}
		else if (v.gk_rkt_aim)
		{
			if (v.gk_aim_enter)
			{
				v.gk_aim_enter = FALSE;
				yaw = p.veh_cam_yaw;
				pitch = p.veh_cam_pitch;
			}
			else
			{
				yaw = Veh_NormYaw (p.v_angle_y);
				pitch = bound (-70, p.v_angle_x, 75);
				p.veh_cam_yaw = yaw;
				p.veh_cam_pitch = pitch;
			}
			tgt = v.origin + '0 0 1' * cup;
		}
		else if (v.veh_kind == VEH_FORELOCO && p.movement_y == 0)
		{
			// free mouse look: the bed follows the view (GK_DriveFrame), so never force the angles here
			lock_view = FALSE;
			yaw = Veh_NormYaw (p.v_angle_y);
			pitch = bound (-35, p.v_angle_x, 55);
			p.veh_cam_yaw = yaw;
			p.veh_cam_pitch = pitch;
			tgt = v.origin + '0 0 1' * cup;
		}
		else if (v.veh_kind == VEH_FORELOCO)
		{
			// A/D turn the bed and the view stays locked behind it
			yaw = v.angles_y;
			p.veh_cam_yaw = yaw;
			pitch = bound (-35, p.veh_cam_pitch, 55);
			tgt = v.origin + '0 0 1' * cup;
		}
		else
		{
			vf_cam = vel_xy * fwd;
			look_fwd = 14 + 18 * bound (0, vf_cam / GK_TOP_CRUISE, 1);
			tgt_yaw = v.angles_y;
			if (spd > 180 && vf_cam > 80)
			{
				vel_d = Veh_AngDelta (vectoyaw (vel_xy), v.angles_y);
				tgt_yaw = Veh_NormYaw (v.angles_y + bound (-22, vel_d * 0.45, 22));
			}
			d = Veh_AngDelta (tgt_yaw, p.veh_cam_yaw);
			p.veh_cam_yaw = Veh_NormYaw (p.veh_cam_yaw + d * min (1, dt * 7.2));
			yaw = p.veh_cam_yaw;

			want_pitch = 12 - v.angles_x * 0.35;
			p.veh_cam_pitch = p.veh_cam_pitch + (want_pitch - p.veh_cam_pitch) * min (1, dt * 7.0);
			pitch = p.veh_cam_pitch;

			tgt = v.origin + fwd * look_fwd + '0 0 1' * cup;
		}
		traceline (v.origin + '0 0 24', tgt, 3, v);
		if (trace_fraction < 1)
			tgt = trace_endpos + trace_plane_normal * 6;

		ang = '0 0 0';
		ang_x = pitch;
		ang_y = yaw;
		makevectors (ang);
		pos = tgt - v_forward * p.veh_cam_dist;
		traceline (tgt, pos, 3, v);
		pos = trace_endpos;
		if (trace_fraction < 1)
			pos = pos + trace_plane_normal * 10;
		traceline (pos, pos + '0 0 10', 3, v);
		if (trace_fraction < 1)
			pos_z = trace_endpos_z - 10;
	}
	setorigin (cam, pos);
	cam.angles = '0 0 0';
	cam.angles_x = pitch;
	cam.angles_y = yaw;
	p.angles = '0 0 0';
	p.angles_x = pitch;
	p.angles_y = yaw;
	if (lock_view)
		p.fixangle = TRUE;
	Veh_ApplyCamShake (p, cam, v);
};

float(entity p, entity v, float dt) GK_DriveFrame =
{
	local float thr, brk, steer_in, spc, spc_edge, started;
	local float yaw0, yaw1, vf, vl, spd, acc, brake_a, turn_rate, yr, yr_in;
	local float ctop, k, launch, power, d, z, imp, vn, new_tier, mt_dur, mt_pwr, mt_nitro, grav;
	local float pitch_tgt, roll_tgt, hud_dirty, pass, old_solid, climbed, is_boosted;
	local float lat_grip, vf1, vl1, peeling, skidding, slip_mag, m1, rkt_ready, is_fl;
	local vector fwd, lft, fwd1, lft1, vel, vel_world, org0, org1, org2, n, tang;
	local entity hit, restore1, restore2, restore3, restore4;
	local float rsol1, rsol2, rsol3, rsol4, rcnt, gone, is_living, is_prop, is_veh;

	is_fl = (v.veh_kind == VEH_FORELOCO);
	if (is_fl)
	{
		FL_BedDriveTick (p, v, dt);
		if (p.fl_phase != 3)
			return TRUE;
	}
	hud_dirty = FALSE;
	started = (time >= v.veh_start_t);
	thr = bound (0, p.movement_x / 160, 1);
	brk = bound (0, 0 - p.movement_x / 160, 1);
	steer_in = bound (-1, p.movement_y / 160, 1);		// + = D = right
	spc = (p.button2 != 0);
	spc_edge = (spc && !v.gk_hop_prev);
	v.gk_hop_prev = spc;

	if (!started)
	{
		thr = 0;
		brk = 0;
	}

	// Snappy arcade steering input easing
	if (steer_in == 0)
		v.veh_steer = Veh_Approach (v.veh_steer, 0, 18.0 * dt);
	else if (steer_in * v.veh_steer < 0)
		v.veh_steer = Veh_Approach (v.veh_steer, steer_in, 24.0 * dt);
	else
		v.veh_steer = Veh_Approach (v.veh_steer, steer_in, 15.0 * dt);

	yaw0 = v.angles_y;
	fwd = Veh_Fwd (yaw0);
	lft = Veh_Lft (yaw0);
	vel = v.velocity;
	vel_z = 0;
	vf = vel * fwd;
	vl = vel * lft;
	spd = vlen (vel);
	v.gk_speed = spd;

	if (GK_CheckPads (v, p))
	{
		// Pad just launched/pushed us this frame: re-read velocity & facing
		fwd = Veh_Fwd (v.angles_y);
		lft = Veh_Lft (v.angles_y);
		yaw0 = v.angles_y;
		vel = v.velocity;
		vel_z = 0;
		vf = vel * fwd;
		vl = vel * lft;
		spd = vlen (vel);
	}

	Veh_GroundSample (v, v.origin, yaw0);

	power = 1;
	if (v.veh_state == VEH_STATE_FIRE)
		power = 0.85;
	if (pointcontents (v.origin + '0 0 18') <= CONTENT_WATER)
	{
		power = power * 0.72;
		vf = vf * (1 - 1.2 * dt);
		vl = vl * (1 - 1.2 * dt);
	}

	// ---- SHIFT (+button4): Nitro Boost
	if (started && p.button4)
	{
		if (v.gk_boosting)
		{
			if (v.gk_nitro <= 0)
			{
				v.gk_boosting = FALSE;
				hud_dirty = TRUE;
			}
		}
		else if (v.gk_nitro >= 10)
		{
			v.gk_boosting = TRUE;
			hud_dirty = TRUE;
			if (vf < (is_fl ? 1100 : 1200))
				vf = max (vf + 260, is_fl ? 1100 : 1180);
			if (time >= v.gk_boost_snd_t)
			{
				v.gk_boost_snd_t = time + 0.65;
				sound7 (v, CHAN_AUTO, is_fl ? "foreloco/bed_boost.wav" : "john_bird/swoop.wav", 0.85, ATTN_NORM, 112 + random () * 8);
			}
		}
	}
	else
	{
		if (v.gk_boosting)
			hud_dirty = TRUE;
		v.gk_boosting = FALSE;
	}

	if (v.gk_boosting)
	{
		v.gk_nitro = max (0, v.gk_nitro - (is_fl ? 18 : 32) * dt);
		if (v.gk_nitro <= 0)
		{
			v.gk_boosting = FALSE;
			hud_dirty = TRUE;
		}
		if (time >= v.gk_boost_snd_t)
		{
			v.gk_boost_snd_t = time + 0.65;
			sound7 (v, CHAN_AUTO, is_fl ? "foreloco/bed_boost.wav" : "john_bird/swoop.wav", 0.72, ATTN_NORM, 118 + random () * 8);
		}
	}
	else
	{
		v.gk_nitro = min (100, v.gk_nitro + (is_fl ? 32 : 14) * dt);
		if (v.veh_air && v.gk_air_t > 0.60)
			v.gk_nitro = min (100, v.gk_nitro + 22 * dt);
	}

	// ---- SPACE (+button2): Hop & Mario Kart 3-Tier Drift
	if (started && spc_edge && !v.veh_air)
	{
		v.veh_air = TRUE;
		v.veh_vz = is_fl ? 435 : 235;
		v.gk_air_t = 0;
		setorigin (v, v.origin + '0 0 3');
		sound7 (v, CHAN_BODY, is_fl ? "foreloco/bed_jump.wav" : "bikes/tire_bounce.wav", 0.82, ATTN_NORM, is_fl ? (100 + random () * 12) : (138 + random () * 10));
		if (!is_fl && fabs (steer_in) > 0.15 && vf > 200)
			v.gk_drift_dir = (steer_in > 0) ? 1 : -1;
	}
	else if (!is_fl && started && spc && v.gk_drift_dir == 0 && fabs (steer_in) > 0.25 && vf > 220)
	{
		// Also allow locking drift as soon as steering starts while holding SPACE
		v.gk_drift_dir = (steer_in > 0) ? 1 : -1;
	}

	if (spc && v.gk_drift_dir != 0)
	{
		if (!v.veh_air && vf > 200)
		{
			// Steering into the drift charges Mini-Turbo 1.45x faster!
			k = 1.0;
			if (steer_in * v.gk_drift_dir > 0.2)
				k = 1.45;
			else if (steer_in * v.gk_drift_dir < -0.2)
				k = 0.65;
			v.gk_drift_charge = v.gk_drift_charge + dt * k;

			new_tier = 0;
			if (v.gk_drift_charge >= 2.00)
				new_tier = 3;
			else if (v.gk_drift_charge >= 1.15)
				new_tier = 2;
			else if (v.gk_drift_charge >= 0.45)
				new_tier = 1;

			if (new_tier > v.gk_drift_tier)
			{
				v.gk_drift_tier = new_tier;
				hud_dirty = TRUE;
				sound7 (v, CHAN_AUTO, "bikes/spoke_ping.wav", 0.78, ATTN_NORM, 105 + new_tier * 22);
			}
			if (time >= v.gk_drift_fx_t)
			{
				v.gk_drift_fx_t = time + 0.08;		// one wheel per tick, 3x count (GK_DriftSparks)
				GK_DriftSparks (v, v.gk_drift_tier);
				if (time >= v.veh_skid_t)
				{
					v.veh_skid_t = time + 0.28;
					sound7 (v, VD_SOUND_CH, "vehicles/tire_squeal.wav", 0.55, ATTN_NORM, 108 + v.gk_drift_tier * 8);
				}
			}
		}
		else if (vf <= 140)
		{
			v.gk_drift_dir = 0;
			v.gk_drift_charge = 0;
			v.gk_drift_tier = 0;
		}
	}
	else if (!spc && v.gk_drift_dir != 0)
	{
		// Released SPACE: trigger Mini-Turbo if charged!
		if (v.gk_drift_tier >= 1 && vf > 160)
		{
			if (v.gk_drift_tier == 1)
			{
				mt_dur = 0.75;
				mt_pwr = 1320;
				mt_nitro = 20;
			}
			else if (v.gk_drift_tier == 2)
			{
				mt_dur = 1.25;
				mt_pwr = 1450;
				mt_nitro = 38;
			}
			else
			{
				mt_dur = 1.85;
				mt_pwr = 1580;
				mt_nitro = 60;
			}
			v.gk_boost_t = max (v.gk_boost_t, time + mt_dur);
			v.gk_boost_pwr = max (v.gk_boost_pwr, mt_pwr);
			v.gk_nitro = min (100, v.gk_nitro + mt_nitro);
			vf = max (vf, mt_pwr * 0.90);
			GK_BoostExhaust (v);
			sound7 (v, CHAN_AUTO, "john_bird/swoop.wav", 0.9, ATTN_NORM, 112 + v.gk_drift_tier * 12);
			hud_dirty = TRUE;
		}
		v.gk_drift_dir = 0;
		v.gk_drift_charge = 0;
		v.gk_drift_tier = 0;
	}

	// ---- M1 (+button0): Tap (<0.18s) = Horn | Hold (>=0.18s) = Rocket Crosshair & Free-Aim (or ForeLoco Bedpan/Can Barrage!)
	m1 = (started && p.button0 != 0);
	if (is_fl)
	{
		if (v.gk_m1_hold_t < 0)
		{
			if (!m1)
				v.gk_m1_hold_t = 0;
			v.gk_m1_prev = FALSE;
		}
		else if (m1)
		{
			if (!v.gk_m1_prev)
			{
				v.gk_m1_hold_t = 0;
				v.gk_rkt_aim = FALSE;
			}
			else
			{
				v.gk_m1_hold_t = v.gk_m1_hold_t + dt;
				if (v.gk_m1_hold_t >= GK_RKT_TAP_MAX && time >= v.gk_rkt_cd)
				{
					v.gk_rkt_cd = time + 0.26;
					v.gk_rkt_armed = TRUE;	// reuse flag locally to suppress tap-horn after firing
					FL_BedFire (p, v);
				}
			}
			v.gk_m1_prev = TRUE;
		}
		else if (v.gk_m1_prev)
		{
			if (!v.gk_rkt_armed && started && time >= v.veh_horn_t)
			{
				v.veh_horn_t = time + 0.55;
				sound7 (v, CHAN_WEAPON, "foreloco/bed_horn.wav", 0.95, ATTN_NORM, 96 + random () * 10);
			}
			v.gk_m1_hold_t = 0;
			v.gk_rkt_aim = FALSE;
			v.gk_rkt_armed = FALSE;
			v.gk_m1_prev = FALSE;
		}
		if (p.ishuman == 1 && !is_fl)
		{
			p.gk_st_mode = 0;
			p.gk_st_prog = 0;
			p.gk_st_nitro = 0;
		}
	}
	else if (v.gk_m1_hold_t < 0)
	{
		// Entered the kart while M1 was already held: ignore until released once
		if (!m1)
			v.gk_m1_hold_t = 0;
		v.gk_m1_prev = FALSE;
	}
	else if (m1)
	{
		if (!v.gk_m1_prev)
		{
			v.gk_m1_hold_t = 0;
			v.gk_rkt_aim = FALSE;
			v.gk_aim_enter = FALSE;
			v.gk_rkt_charge = 0;
			v.gk_rkt_armed = FALSE;
		}
		else
		{
			v.gk_m1_hold_t = v.gk_m1_hold_t + dt;
			if (!v.gk_rkt_aim && v.gk_m1_hold_t >= GK_RKT_TAP_MAX)
			{
				v.gk_rkt_aim = TRUE;
				v.gk_aim_enter = TRUE;
				v.gk_rkt_charge = 0;
				v.gk_rkt_armed = FALSE;
				if (v.gk_nitro >= GK_RKT_NITRO_COST && time >= v.gk_rkt_cd)
					sound7 (v, CHAN_AUTO, "weapons/rockload.wav", 0.65, ATTN_NORM, 118);
				else
					sound7 (v, CHAN_AUTO, "weapons/guncock.wav", 0.50, ATTN_NORM, 92);
			}
			if (v.gk_rkt_aim)
			{
				rkt_ready = (v.gk_nitro >= GK_RKT_NITRO_COST && time >= v.gk_rkt_cd);
				if (rkt_ready)
				{
					if (!v.gk_rkt_armed)
					{
						v.gk_rkt_charge = min (GK_RKT_CHARGE_T, v.gk_rkt_charge + dt);
						if (v.gk_rkt_charge >= GK_RKT_CHARGE_T)
						{
							v.gk_rkt_armed = TRUE;
							sound7 (v, CHAN_AUTO, "bikes/spoke_ping.wav", 0.78, ATTN_NORM, 148);
						}
					}
				}
				else
				{
					v.gk_rkt_armed = FALSE;
					v.gk_rkt_charge = 0;
				}
			}
		}
		v.gk_m1_prev = TRUE;
	}
	else if (v.gk_m1_prev)
	{
		if (!v.gk_rkt_aim)
		{
			if (started && time >= v.veh_horn_t)
			{
				v.veh_horn_t = time + 0.55;
				sound7 (v, CHAN_WEAPON, "vehicles/horn.wav", 0.9, ATTN_NORM, 125 + random () * 8);
			}
		}
		else
		{
			if (v.gk_rkt_armed && v.gk_nitro >= GK_RKT_NITRO_COST && time >= v.gk_rkt_cd)
			{
				v.gk_nitro = max (0, v.gk_nitro - GK_RKT_NITRO_COST);
				if (v.gk_nitro <= 0)
					v.gk_boosting = FALSE;
				v.gk_rkt_cd = time + GK_RKT_COOLDOWN;
				hud_dirty = TRUE;
				GK_FireRocket (p, v);
			}
			else if (v.gk_nitro < GK_RKT_NITRO_COST || time < v.gk_rkt_cd)
			{
				sound7 (v, CHAN_AUTO, "weapons/guncock.wav", 0.45, ATTN_NORM, 85);
			}
		}
		v.gk_m1_hold_t = 0;
		v.gk_rkt_aim = FALSE;
		v.gk_aim_enter = FALSE;
		v.gk_rkt_charge = 0;
		v.gk_rkt_armed = FALSE;
		v.gk_m1_prev = FALSE;
	}

	if (!is_fl)
		GK_UpdateLock (p, v);

	if (p.ishuman == 1 && !is_fl)
	{
		if (v.gk_rkt_aim)
		{
			if (time < v.gk_rkt_cd)
			{
				p.gk_st_mode = 4;
				p.gk_st_prog = floor (bound (0, ((v.gk_rkt_cd - time) / GK_RKT_COOLDOWN) * 100, 100) + 0.5);
			}
			else if (v.gk_nitro < GK_RKT_NITRO_COST)
			{
				p.gk_st_mode = 3;
				p.gk_st_prog = floor (bound (0, v.gk_nitro, 100) + 0.5);
			}
			else if (v.gk_rkt_armed)
			{
				p.gk_st_mode = 2;
				p.gk_st_prog = 100;
			}
			else
			{
				p.gk_st_mode = 1;
				p.gk_st_prog = floor (bound (0, (v.gk_rkt_charge / GK_RKT_CHARGE_T) * 100, 100) + 0.5);
			}
			p.gk_st_nitro = floor (bound (0, v.gk_nitro, 100) + 0.5);
		}
		else
		{
			p.gk_st_mode = 0;
			p.gk_st_prog = 0;
			p.gk_st_nitro = 0;
		}
	}

	is_boosted = (v.gk_boosting || time < v.gk_boost_t);
	ctop = is_fl ? FL_TOP_CRUISE : GK_TOP_CRUISE;
	if (v.gk_boosting)
		ctop = max (ctop, is_fl ? FL_TOP_NITRO : GK_TOP_NITRO);
	if (time < v.gk_boost_t)
		ctop = max (ctop, v.gk_boost_pwr);
	ctop = ctop * power;

	// ---- Acceleration & Braking
	acc = 0;
	brake_a = 0;
	if (v.gk_boosting && started)
	{
		// Shift nitro drives hard on ground and adds gentle forward thrust in mid-air
		if (v.veh_air)
		{
			if (vf < ctop)
				vf = min (ctop, vf + 520 * dt);
		}
		else
		{
			k = bound (0, vf / ctop, 1);
			acc = GK_ACCEL * 2.05 * power * (1 - pow (k, 2.6));
		}
	}
	else if (time < v.gk_boost_t && !v.veh_air && !(is_fl && brk > 0))
	{
		k = bound (0, vf / ctop, 1);
		acc = GK_ACCEL * 1.85 * power * (1 - pow (k, 2.4));
	}
	else if (!v.veh_air)
	{
		if (thr > 0 && brk > 0)
		{
			if (spd > 16)
				brake_a = GK_BRAKE;
		}
		else if (thr > 0)
		{
			if (vf < -16)
				brake_a = GK_BRAKE * thr;
			else
			{
				k = bound (0, vf / ctop, 1);
				launch = 1 + 0.55 * (1 - min (1, spd / 320));
				acc = thr * GK_ACCEL * launch * power * (1 - pow (k, 2.2));
			}
		}
		else if (brk > 0)
		{
			if (vf > 16)
				brake_a = GK_BRAKE * brk;
			else
			{
				k = bound (0, 0 - vf / GK_REV_TOP, 1);
				acc = 0 - brk * GK_REV_ACCEL * power * (1 - pow (k, 1.5));
			}
		}
		else
			brake_a = GK_COAST + spd * 0.14;
	}

	// Stationary SPACE acts as crisp handbrake
	if (spc && v.gk_drift_dir == 0 && !v.veh_air && thr == 0)
		brake_a = brake_a + 650;

	if (!v.veh_air)
	{
		vf = vf + acc * dt;
		if (brake_a > 0)
		{
			if (vf > 0)
				vf = max (0, vf - brake_a * dt);
			else
				vf = min (0, vf + brake_a * dt);
		}
		vf = vf - 260 * vd_slope_f * dt;
		vl = vl - 260 * vd_slope_l * dt;
	}

	// ---- Snappy Arcade Steering + Natural High-Speed Oversteer & Skid
	turn_rate = GK_TURN_MAX - (GK_TURN_MAX - GK_TURN_HI) * bound (0, spd / GK_TOP_CRUISE, 1);
	if (is_fl && steer_in == 0 && started && (time - p.fl_t0) >= FL_INTRO_DUR)
	{
		// the hospital bed steers with the mouse: it swings to face where you look (casters: even standing still)
		k = Veh_AngDelta (p.v_angle_y, yaw0);
		yr = bound (0 - FL_TURN_RATE, k * 7, FL_TURN_RATE);
		if (v.veh_air)
			yr = bound (-110, yr, 110);
	}
	else if (is_fl)
	{
		yr = 0 - v.veh_steer * (v.veh_air ? 110 : FL_TURN_RATE);
		if (vf < -18)
			yr = 0 - yr;
	}
	else if (v.veh_air)
	{
		// Gentle air steering so player can line up landings
		yr = 0 - v.veh_steer * 32;
	}
	else if (v.gk_drift_dir != 0)
	{
		// Drifting: base curve in drift_dir; steer into drift tightens, counter-steer widens
		yr_in = 0 - v.gk_drift_dir * 108;
		if (v.veh_steer * v.gk_drift_dir > 0)
			yr_in = yr_in - v.veh_steer * 68;
		else
			yr_in = yr_in - v.veh_steer * 56;
		yr = yr_in;
	}
	else if (fabs (vf) < 18)
	{
		yr = 0;
	}
	else if (vf < 0)
	{
		yr = v.veh_steer * (turn_rate * 0.72) * bound (0, fabs (vf) / 140, 1);
	}
	else
	{
		yr = 0 - v.veh_steer * turn_rate * bound (0, vf / 110, 1);
	}
	v.veh_yawrate = v.veh_yawrate + (yr - v.veh_yawrate) * min (1, dt * 16);
	yaw1 = Veh_NormYaw (yaw0 + v.veh_yawrate * dt);

	// Reconstruct world XY velocity before heading step, then resolve tire slip against new heading!
	vel_world = fwd * vf + lft * vl;
	fwd1 = Veh_Fwd (yaw1);
	lft1 = Veh_Lft (yaw1);
	if (!v.veh_air)
	{
		vf1 = vel_world * fwd1;
		vl1 = vel_world * lft1;
		if (v.gk_drift_dir != 0)
		{
			// Locked SPACE powerslide: pronounced tail-out angle without losing forward drive
			k = 215 * v.gk_drift_dir;
			vl1 = Veh_Approach (vl1, k, 1450 * dt);
		}
		else
		{
			// Natural high-speed skidding & trail-brake slides!
			lat_grip = 2900;
			if (brk > 0.15 && fabs (v.veh_steer) > 0.22 && spd > 220)
			{
				// Slamming brake + steer kicks the rear end out into a fast slide
				lat_grip = 460;
			}
			else if (spd > 520 && fabs (v.veh_steer) > 0.38)
			{
				// Going really fast into a corner naturally breaks rear traction!
				lat_grip = bound (620, 2250 - (spd - 520) * 1.45 * fabs (v.veh_steer), 2250);
				if (is_boosted)
					lat_grip = lat_grip * 0.72;
			}
			if (is_fl && lat_grip > 460)
				lat_grip = FL_GRIP;		// the bed goes where it points; only brake+steer slides it
			vl1 = Veh_Approach (vl1, 0, lat_grip * dt);
		}
		vel = fwd1 * vf1 + lft1 * vl1;
	}
	else
	{
		vl1 = vl;
		vel = vel_world;
	}

	// ---- Peel-Outs & High-Speed Tire Smoke / Squeal
	peeling = (!v.veh_air && ((thr > 0.65 && fabs (vf) < 440) || (thr > 0.35 && brk > 0.35) || (is_boosted && spd < 1260)));
	skidding = (!v.veh_air && (fabs (vl1) > 85 || (brk > 0.25 && spd > 320 && fabs (v.veh_steer) > 0.28) || (spd > 760 && fabs (v.veh_steer) > 0.62)));
	if ((peeling || skidding) && v.gk_drift_dir == 0)
	{
		slip_mag = fabs (vl1);
		if (peeling && slip_mag < 240)
			slip_mag = 240;
		GK_PeelAndSkidFX (v, slip_mag, skidding);
	}

	// ---- Swept Move + Living Launch + Curb Climb + Elastic Wall Bounce + Depenetration
	org0 = v.origin;
	org1 = org0;
	org1_x = org0_x + vel_x * dt;
	org1_y = org0_y + vel_y * dt;

	rcnt = 0;
	gone = FALSE;
	restore1 = world;
	restore2 = world;
	restore3 = world;
	restore4 = world;
	rsol1 = rsol2 = rsol3 = rsol4 = SOLID_NOT;
	pass = 0;
	while (pass < 4)
	{
		if (GK_Sweep (v, org0, yaw0, org1, yaw1, 22))
			break;

		// Living target or breakable street/room prop: plow cleanly through at 95% speed (only when actually launched/smashed!)
		is_living = (vd_hitent != world && vd_hitent.takedamage && ((vd_hitent.flags & FL_CLIENT) || (vd_hitent.flags & FL_MONSTER)));
		is_prop = (!is_living && GK_IsSmashableProp (vd_hitent));
		if (is_living || is_prop)
		{
			local float plowed;
			hit = vd_hitent;
			old_solid = hit.solid;
			if (is_living)
				plowed = GK_RamLiving (v, hit, spd);
			else
				plowed = GK_SmashProp (v, hit, spd);
			// the ram's frag may have released the driver (match end / intermission): stop driving him
			if (p.veh_van != v || bm_wasfreed (v))
			{
				gone = TRUE;
				break;
			}
			if (plowed)
			{
				vel = vel * 0.95;
				org1 = org0;
				org1_x = org0_x + vel_x * dt;
				org1_y = org0_y + vel_y * dt;
				hit.solid = SOLID_NOT;
				// one restore slot per pass (4), so no rammed body is left SOLID_NOT for good
				if (rcnt == 0) { restore1 = hit; rsol1 = old_solid; }
				else if (rcnt == 1) { restore2 = hit; rsol2 = old_solid; }
				else if (rcnt == 2) { restore3 = hit; rsol3 = old_solid; }
				else { restore4 = hit; rsol4 = old_solid; }
				rcnt = rcnt + 1;
				pass = pass + 1;
				continue;
			}
		}

		// Try curb-step / low-pipe / BSP ramp climbing (+24u step-up) on world and SOLID_BSP geometry, preserving hit globals on failure!
		climbed = FALSE;
		if (vd_hitent == world || vd_hitent.solid == SOLID_BSP)
		{
			local vector saved_norm, saved_pos;
			local entity saved_ent;
			saved_norm = vd_hitnorm;
			saved_pos = vd_hitpos;
			saved_ent = vd_hitent;
			if (GK_Sweep (v, org0, yaw0, org1, yaw1, 36))
			{
				Veh_GroundSample (v, org1, yaw1);
				if (vd_found && vd_gh <= org0_z + 24 && vd_gh >= org0_z - 12)
					climbed = TRUE;
			}
			if (!climbed)
			{
				vd_hitnorm = saved_norm;
				vd_hitpos = saved_pos;
				vd_hitent = saved_ent;
			}
		}
		if (climbed)
			break;

		// Non-living obstacle (wall, object, vehicle/kart): corner slip-around / smooth wall slide / head-on bounce
		n = vd_hitnorm;
		vn = vel * n;
		is_veh = (vd_hitent != world && (vd_hitent.veh_kind > 0 || vd_hitent.classname == "veh_van_clip"));
		if (vn < 0)
		{
			imp = 0 - vn;
			if (is_veh)
			{
				GK_RamVehicle (v, vd_hitent, imp);
				if (p.veh_van != v || bm_wasfreed (v))
				{
					gone = TRUE;
					break;
				}
			}

			// Narrow pole/pipe/corner snag: slip subtly sideways around it without jerking heading or camera
			if (!is_veh && fabs (vn) >= max (160, spd * 0.85) && GK_TryCornerSlip (v, org0, yaw0, org1, yaw1, lft, vd_hitpos))
			{
				org1 = gk_slip_pos;
				vel = vel * 0.92;
				break;
			}

			if (fabs (vn) < max (160, spd * 0.85))
			{
				// Smooth wall/obstacle slide up to ~58 deg: keep ~92% tangential speed
				vel = (vel - n * (1.06 * vn)) * 0.92;
				if (imp > 280 && time >= v.veh_crash_t)
				{
					v.veh_crash_t = time + 0.18;
					sound7 (v, CHAN_BODY, "bikes/tire_bounce.wav", bound (0.25, imp / 650, 0.60), ATTN_NORM, 102 + random () * 16);
				}
			}
			else
			{
				// Near-head-on impact against flat wall or vehicle: controlled rebound + shake
				vel = (vel - n * (1.45 * vn)) * 0.72;
				if (time >= v.veh_crash_t)
				{
					v.veh_crash_t = time + 0.16;
					Veh_AddShake (p, bound (1.5, imp / 210, 6.5), bound (0.14, imp / 1500, 0.36));
					sound7 (v, CHAN_BODY, "bikes/tire_bounce.wav", bound (0.4, imp / 450, 0.95), ATTN_NORM, 92 + random () * 18);
					if (veh_fx_sparks > 0)
						pointparticles (veh_fx_sparks, vd_hitpos, '0 0 0', 1);
				}
			}
		}

		org2 = org0;
		org2_x = org0_x + vel_x * dt;
		org2_y = org0_y + vel_y * dt;
		if (GK_Sweep (v, org0, yaw0, org2, yaw1, 22))
		{
			org1 = org2;
		}
		else
		{
			// Corner bevel fallback: slide pure tangent along wall normal
			tang = vel - n * (vel * n);
			org2 = org0 + tang * (dt * 0.90) + n * 1.5;
			if (GK_Sweep (v, org0, yaw0, org2, yaw1, 22))
			{
				org1 = org2;
				vel = tang * 0.90;
			}
			else if (yaw1 != yaw0 && GK_Sweep (v, org0, yaw0, org0, yaw1, 22))
			{
				org1 = org0;
				vel = vel * 0.85;
			}
			else
			{
				org1 = org0;
				yaw1 = yaw0;
				vel = vel * 0.80;
				v.veh_yawrate = 0;
			}
		}
		break;
	}

	if (gone)
	{
		// driver was let go during the ram: put back the bodies we made SOLID_NOT and leave the kart alone
		if (restore1 != world && !bm_wasfreed (restore1) && restore1.health > 0 && restore1.takedamage != DAMAGE_NO) restore1.solid = rsol1;
		if (restore2 != world && !bm_wasfreed (restore2) && restore2.health > 0 && restore2.takedamage != DAMAGE_NO) restore2.solid = rsol2;
		if (restore3 != world && !bm_wasfreed (restore3) && restore3.health > 0 && restore3.takedamage != DAMAGE_NO) restore3.solid = rsol3;
		if (restore4 != world && !bm_wasfreed (restore4) && restore4.health > 0 && restore4.takedamage != DAMAGE_NO) restore4.solid = rsol4;
		return TRUE;
	}

	// ---- Vertical Ground Follow, Airtime & Landing Boost
	Veh_GroundSample (v, org1, yaw1);
	z = org1_z;
	if (v.veh_air)
	{
		grav = cvar ("sv_gravity");
		if (grav <= 10)
			grav = GK_GRAVITY;
		v.gk_air_t = v.gk_air_t + dt;
		v.veh_vz = v.veh_vz - grav * dt;
		// Ceiling guard so high SkyPad / jump-pad launches never embed into arches
		if (v.veh_vz > 0)
		{
			tracebox (org1 + '0 0 8', '-24 -24 0', '24 24 34', org1 + '0 0 1' * (8 + v.veh_vz * dt + 4), TRUE, v);
			if (trace_fraction < 1 && trace_plane_normal_z < -0.5)
				v.veh_vz = 0;
		}
		z = z + v.veh_vz * dt;
		if (vd_found && v.veh_vz <= 0 && z <= vd_gh + 2)
		{
			imp = 0 - v.veh_vz;
			z = vd_gh;
			v.veh_vz = 0;
			v.veh_air = FALSE;
			if (v.gk_air_t >= (v.veh_kind == VEH_FORELOCO ? 1.35 : 0.68))
			{
				// Landing boost on touchdown from real airtime (ramps/drops/jump pads)!
				v.gk_boost_t = max (v.gk_boost_t, time + 0.85);
				v.gk_boost_pwr = max (v.gk_boost_pwr, 1380);
				v.gk_nitro = min (100, v.gk_nitro + 20);
				vel = vel + Veh_Fwd (yaw1) * 220;
				GK_BoostExhaust (v);
				sound7 (v, CHAN_BODY, "vehicles/tire_thud2.wav", 0.95, ATTN_NORM, 108 + random () * 12);
				sound7 (v, CHAN_AUTO, "john_bird/swoop.wav", 0.72, ATTN_NORM, 128);
				hud_dirty = TRUE;
			}
			else if (imp > 110)
			{
				sound7 (v, CHAN_BODY, "vehicles/tire_thud2.wav", 0.75, ATTN_NORM, 92 + random () * 12);
			}
			v.gk_air_t = 0;
			v.veh_land_dip = 0 - min (6, imp * 0.014);
		}
	}
	else if (!vd_found)
	{
		v.veh_air = TRUE;
		v.gk_air_t = 0;
	}
	else
	{
		d = vd_gh - z;
		if (d < -14)
		{
			v.veh_air = TRUE;
			v.gk_air_t = 0;
		}
		else
		{
			if (d > 0.5)
				z = z + d * min (1, dt * 28);
			else
				z = vd_gh;
			v.veh_vz = bound (-280, v.veh_vz * 0.5 + ((z - org1_z) / dt) * 0.5, 420);
		}
	}
	org1_z = z;

	// ---- Pitch & Roll Attitude (smooth mid-air pitch stabilization + snappy drift/turn lean)
	v.veh_land_dip = Veh_Approach (v.veh_land_dip, 0, dt * 20);
	if (v.veh_air)
	{
		pitch_tgt = bound (-26, v.veh_vz * 0.025, 26);
		v.angles_x = v.angles_x + (pitch_tgt - v.angles_x) * min (1, dt * 5.0);
		v.angles_z = v.angles_z + (0 - v.angles_z) * min (1, dt * 5.0);
	}
	else if (vd_found)
	{
		pitch_tgt = vd_pitch + (is_boosted ? 4.0 : 2.0 * thr) + v.veh_land_dip;
		v.angles_x = v.angles_x + (pitch_tgt - v.angles_x) * min (1, dt * 12);
		roll_tgt = bound (-10, v.veh_yawrate * bound (0, spd / 400, 1) * 0.055 + vd_slope_l * 28, 10);
		v.angles_z = v.angles_z + (roll_tgt - v.angles_z) * min (1, dt * 12);
	}

	v.angles_y = yaw1;
	v.velocity = vel;
	if (v.veh_air)
		v.velocity_z = v.veh_vz;
	setorigin (v, org1);
	GK_Depenetrate (v);
	// Restore solids on launched living entities / un-broken props after depenetration
	if (restore1 != world && !bm_wasfreed (restore1) && restore1.health > 0 && restore1.takedamage != DAMAGE_NO) restore1.solid = rsol1;
	if (restore2 != world && !bm_wasfreed (restore2) && restore2.health > 0 && restore2.takedamage != DAMAGE_NO) restore2.solid = rsol2;
	if (restore3 != world && !bm_wasfreed (restore3) && restore3.health > 0 && restore3.takedamage != DAMAGE_NO) restore3.solid = rsol3;
	if (restore4 != world && !bm_wasfreed (restore4) && restore4.health > 0 && restore4.takedamage != DAMAGE_NO) restore4.solid = rsol4;
	Veh_DriveBounds (v);

	// Out of the world: setorigin movement never touches trigger_hurt/teleporters, so a kart that drops below the map
	// or into sky would fall forever and a map kart would never respawn. Blow it up the deferred way (on its own think).
	if (v.veh_chain_t == 0 && ((world.maxs_z > world.mins_z && v.origin_z < world.mins_z - 64) || pointcontents (v.origin + '0 0 8') == CONTENT_SKY || pointcontents (v.origin - '0 0 4') == CONTENT_SKY))
	{
		v.health = 1;
		v.takedamage = DAMAGE_NO;
		v.veh_chain_t = time;
		v.think = Veh_Think;
		v.nextthink = time;
	}

	// ---- Engine Revs, Boost Exhaust & Animation Frame Sync
	spd = vlen (vel);
	v.gk_speed = spd;
	v.veh_rpm = bound (0.14, 0.16 + 0.84 * (spd / GK_TOP_CRUISE), 1.0);
	if (is_boosted)
		v.veh_rpm = 1.0;
	if (started && !is_fl)
		Veh_EngineSound (v, max (thr, is_boosted));

	if (is_boosted && time >= v.veh_fx_boost_t)
	{
		v.veh_fx_boost_t = time + 0.05;		// one pipe per tick, 3x count (GK_BoostExhaust)
		GK_BoostExhaust (v);
	}

	// Keep MD3 super-boost / drive frames locked responsively every client frame while preserving wheel phase
	if (!is_fl)
	{
		if (is_boosted && (v.frame < 28 || v.frame > 43))
		{
			if (v.frame >= 12 && v.frame <= 27)
				v.veh_anim = floor ((v.frame - 12) * 0.5);
			else
				v.veh_anim = 0;
			v.frame = 28 + v.veh_anim;
		}
		else if (!is_boosted && spd > 35 && (v.frame < 12 || v.frame > 27))
		{
			if (v.frame >= 28 && v.frame <= 43)
			{
				local float kf;
				kf = (v.frame - 28) * 2;
				v.veh_anim = kf - 16 * floor (kf / 16);
			}
			else
				v.veh_anim = 0;
			v.frame = 12 + v.veh_anim;
		}
	}

	// ---- Nitro / Drift HUD: at most 2 Hz, and only when its text changes (GK_UpdateHUD sets gk_hud_t)
	if (!is_fl && time >= v.gk_hud_t)
		GK_UpdateHUD (p, v, hud_dirty);

	// ---- Seat Driver & Update Mario Kart Chase Camera
	setorigin (p, v.origin - Veh_Fwd (yaw1) * 9 + '0 0 18');
	if (!is_fl)
		GK_SyncDriverEnt (v);
	GK_DriveCamera (p, v, dt);
	return TRUE;
};

// ---------------------------------------------------------------- sv_cheats Test Impulses (136..138)

void() GK_SpawnAndEnter =
{
	local entity v;
	local vector fwd;
	local float k;

	if (self.veh_van != world || self.veh_ride != world || self.fd_head != world || self.jb_vehicle != world || self.rr_vehicle != world || self.mmt_tank != world || self.health <= 0)
		return;
	k = floor (cvar ("gokart_variant"));
	if (k < 1 || k > 6)
	{
		gokart_spawn_cycle = gokart_spawn_cycle + 1;
		if (gokart_spawn_cycle > 6)
			gokart_spawn_cycle = 1;
		k = gokart_spawn_cycle;
	}
	fwd = Veh_Fwd (self.v_angle_y);
	v = Veh_SpawnDynamic (VEH_GOKART_1 + k - 1, self.origin + fwd * 120 + '0 0 8', self.v_angle_y);
	Veh_Enter (self, v);
};

void() GK_SpawnNext =
{
	local vector fwd;
	local float k;

	gokart_spawn_cycle = gokart_spawn_cycle + 1;
	if (gokart_spawn_cycle > 6)
		gokart_spawn_cycle = 1;
	k = gokart_spawn_cycle;
	fwd = Veh_Fwd (self.v_angle_y);
	Veh_SpawnDynamic (VEH_GOKART_1 + k - 1, self.origin + fwd * 140 + '0 0 8', Veh_NormYaw (self.v_angle_y + 90));
	sprint (self, strcat ("Spawned ", Veh_DisplayName (VEH_GOKART_1 + k - 1), "\n"));
};

void() GK_SpawnAll6 =
{
	local vector fwd, rgt, base;
	local float i, row, col;

	makevectors ('0 1 0' * self.v_angle_y);
	fwd = v_forward;
	rgt = v_right;
	base = self.origin + fwd * 220 + '0 0 16';
	i = 0;
	while (i < 6)
	{
		row = floor (i / 3);
		col = i - row * 3 - 1;
		Veh_SpawnDynamic (VEH_GOKART_1 + i, base + fwd * (row * 145) + rgt * (col * 125), self.v_angle_y + 180);
		i = i + 1;
	}
	sprint (self, "Spawned all 6 Go-Karts!\n");
};
