#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
DRIVING THE PROMASTER VAN (Combat+)

Walk into the cab (the cockpit trigger in vehicles.qc), press H (impulse 86) and you are in the driver's seat.
Everything while driving runs from Veh_DriveFrame, which W_WeaponFrame calls for the driver every client frame:

  W / S    throttle / brake, then reverse once stopped (the "forward" and "back" keys)
  A / D    steer (the strafe keys). Eased toward the key like a keyboard racer, less lock the faster you go
  SPACE    handbrake: locks the rear tyres, the tail swings out (the jump key)
  FIRE     horn
  H        get out (stopped, or nearly)      K   cockpit view / chase view

Keeping the throttle open builds speed (veh_boost, VD_BOOST_*): top speed and acceleration grow over ~14 s flat out, up to
about 45% / 60% more; lifting off fades it slowly, braking or the handbrake fade it fast, a crash takes it away.

The model is one rigid MD3, so the body is moved by hand, like the Rob Dob head:
  - speed is kept as forward + sideways components of the van's own heading. Tyres can only take VD_GRIP of sideways
    acceleration: below that the van follows its nose, above it (hard cornering at speed, or the handbrake) it slides
  - the turn rate is the bicycle model, speed * tan(steer) / wheelbase, capped by what the tyres can hold, so too much
    speed into a corner is understeer, not magic
  - collision is 20 small hulls swept around the van's real, rotated footprint (an entity's own box is axis aligned
    and useless for a long thin van). A blocked hull slides the van along the wall, and the lost speed is the crash
  - ground is followed with four wheel traces (pitch from the front/rear pair, drops and jumps from the gap under them)
  - while driven the van is one solid box. Parked square to the world (within a few degrees) it gets its walk-in
    interior back; parked at an angle it stays a plain solid box.

The driver's body is hidden and parked at the seat; he sees through a camera entity (like the Rob Dob head).
The view is driven by the server, so the mouse is ignored while driving.
================
*/

// ---------------------------------------------------------------- tuning

float	VD_TOP			= 720;		// forward top speed, units/second (per-vehicle override in Veh_TopSpeed)
float	VD_BOOST_TOP	= 0.38;		// holding the throttle builds turbo boost: up to +38% top speed (van 900 -> 1242) ...
float	VD_BOOST_ACC	= 0.75;		// ... and +75% extra acceleration, spooling over VD_BOOST_TIME seconds
float	VD_BOOST_TIME	= 3.2;
float	VD_REV			= 360;		// reverse top speed
float	VD_ACCEL		= 310;		// acceleration from a standstill (falls off toward top speed)
float	VD_REV_ACCEL	= 380;
float	VD_BRAKE		= 960;		// footbrake deceleration
float	VD_COAST		= 65;		// rolling resistance with both pedals up (plus engine braking, below)
float	VD_GRIP			= 840;		// sideways acceleration the tyres hold
float	VD_GRIP_HB		= 270;		// ... with the handbrake on (controllable powerslide)
float	VD_WHEELBASE	= 148;
float	VD_LOCK			= 40;		// degrees of front wheel lock at a standstill
float	VD_LOCK_HI		= 14;		// ... at top speed
float	VD_GRAVITY		= 800;
float	VD_HEIGHT		= 0.5;		// the van's origin sits this far above the road

float	VD_EYE_X		= 42;		// the driver's eye, van-local (the model's cockpit anchor)
float	VD_EYE_Y		= 19.8;
float	VD_EYE_Z		= 63.5;

float	VD_CAM_DIST		= 253;
float	VD_CAM_PITCH	= 15;
float	VD_CAM_UP		= 118;

float	VD_MUSIC_CH		= 3;		// CHAN_ITEM: the "6 man LAN van" singalong (hacking.wmv), looped while he drives
float	VD_MUSIC_LEN	= 11.0;		// the clip's length
float	VD_SOUND_CH		= 0;		// CHAN_AUTO: engine and squeal grains overlap, they must not cut each other off

// ---------------------------------------------------------------- scratch results

vector	vd_hitnorm, vd_hitpos, vd_exit;
float	vd_dbg_t, vd_hit_dbg_t;
entity	vd_hitent;
float	vd_found, vd_gh, vd_pitch, vd_slope_f, vd_slope_l;

// ---------------------------------------------------------------- small helpers

// sin / cos / tan are untyped builtins that only compile cleanly into a float local: wrap them once, in degrees
float(float deg) Veh_Sin =
{
	local float r, s;

	r = deg * 0.0174533;
	s = sin (r);
	return s;
};

float(float deg) Veh_Cos =
{
	local float r, c;

	r = deg * 0.0174533;
	c = cos (r);
	return c;
};

float(float deg) Veh_Tan =
{
	local float c;

	c = Veh_Cos (deg);
	if (fabs (c) < 0.0001)
		c = 0.0001;
	return Veh_Sin (deg) / c;
};

// degrees the nose points up when it rises `rise` over `run` (vectoangles: up is +pitch, the way entity pitch is stored)
float(float rise, float run) Veh_RiseAngle =
{
	local vector a, d;
	local float p;

	d = '0 0 0';
	d_x = run;
	d_z = rise;
	a = vectoangles (d);
	p = a_x;
	if (p > 180)
		p = p - 360;
	return p;
};


// shortest signed turn from `from` to `to`, degrees
float(float to, float from) Veh_AngDelta =
{
	local float d;

	d = to - from;
	while (d > 180)
		d = d - 360;
	while (d < -180)
		d = d + 360;
	return d;
};

// move `cur` toward `target` by at most `step`
float(float cur, float target, float step) Veh_Approach =
{
	if (cur < target)
	{
		cur = cur + step;
		if (cur > target)
			cur = target;
	}
	else
	{
		cur = cur - step;
		if (cur < target)
			cur = target;
	}
	return cur;
};

// the van's world-space forward and left (xy) for a yaw
vector(float yaw) Veh_Fwd =
{
	local vector f;

	f = '0 0 0';
	f_x = Veh_Cos (yaw);
	f_y = Veh_Sin (yaw);
	return f;
};

vector(float yaw) Veh_Lft =
{
	local vector l;

	l = '0 0 0';
	l_x = 0 - Veh_Sin (yaw);
	l_y = Veh_Cos (yaw);
	return l;
};

void(entity v) Veh_FreeClips =
{
	local entity clp, nxt;

	clp = v.veh_clip_head;
	while (clp != world)
	{
		nxt = clp.enemy;
		remove (clp);
		clp = nxt;
	}
	v.veh_clip_head = world;
};

// can a standing player fit here?
float(entity e, vector org) Veh_FreeSpot =
{
	tracebox (org, '-16 -16 -24', '16 16 32', org, FALSE, e);
	if (trace_startsolid || trace_allsolid)
		return FALSE;
	return TRUE;
};

// ---------------------------------------------------------------- jump pads & SkyPad stunts

void(entity v) Veh_ResetPadStunt =
{
	v.veh_pad_spin = FALSE;
	v.veh_pad_launch_t = 0;
	v.veh_pad_horn_t = 0;
	v.veh_spin_yaw = 0;
	v.veh_spin_pitch = 0;
	v.veh_spin_roll = 0;
};

float(entity v, vector org, float dt) Veh_StepAirRise =
{
	local float grav;

	grav = cvar ("sv_gravity");
	if (grav <= 10)
		grav = VD_GRAVITY;
	v.veh_vz = v.veh_vz - grav * dt;
	if (v.veh_vz > 0)
	{
		tracebox (org + '0 0 8', '-24 -24 0', '24 24 0' + '0 0 1' * max (36, Veh_BodyHeight (v.veh_kind) - 8), org + '0 0 1' * (8 + v.veh_vz * dt + 4), TRUE, v);
		if (trace_fraction < 1 && trace_plane_normal_z < -0.5)
			v.veh_vz = 0;
	}
	return org_z + v.veh_vz * dt;
};

void(entity v, float pitch) Veh_PadHonk =
{
	if (v.veh_kind == VEH_TUKTUK)
		sound7 (v, CHAN_WEAPON, "vehicles/horn_tuktuk.wav", 1, ATTN_NORM, pitch);
	else
		sound7 (v, CHAN_WEAPON, "vehicles/horn.wav", 1, ATTN_NORM, pitch);
};

void(entity v) Veh_PadHornTick =
{
	if (!v.veh_pad_spin || !v.veh_air || time < v.veh_pad_horn_t)
		return;
	Veh_PadHonk (v, 76 + random () * 54);
	v.veh_pad_horn_t = time + 0.34 + random () * 0.30;
};

void(entity v) Veh_StartPadStunt =
{
	local float sy, sr;

	v.veh_pad_spin = TRUE;
	v.veh_pad_launch_t = time + 0.12;
	sy = (random () < 0.5) ? 1 : -1;
	sr = (random () < 0.5) ? 1 : -1;

	// Weight-based comedy spin: tiny carts spin like tops, midweights barrel-roll, buses/rigs flip end-over-end
	if (v.veh_kind == VEH_GOLFCART || v.veh_kind == VEH_TUKTUK)
	{
		v.veh_spin_yaw = sy * (700 + random () * 240);
		v.veh_spin_pitch = (random () - 0.5) * 110;
		v.veh_spin_roll = sr * (150 + random () * 120);
	}
	else if (v.veh_kind == VEH_SCHOOLBUS || v.veh_kind == VEH_HDTRUCK)
	{
		v.veh_spin_pitch = sy * (215 + random () * 95);
		v.veh_spin_roll = sr * (60 + random () * 60);
		v.veh_spin_yaw = sr * (75 + random () * 70);
	}
	else
	{
		v.veh_spin_roll = sy * (370 + random () * 170);
		v.veh_spin_yaw = sr * (210 + random () * 130);
		v.veh_spin_pitch = 45 + random () * 65;
	}

	Veh_PadHonk (v, 90 + random () * 34);
	v.veh_pad_horn_t = time + 0.38 + random () * 0.28;
};

void(entity v, float dt, float steer_in, float pitch_in) Veh_StepPadSpin =
{
	if (steer_in != 0)
	{
		v.veh_spin_yaw = bound (-1100, v.veh_spin_yaw - steer_in * 420 * dt, 1100);
		v.veh_spin_roll = bound (-720, v.veh_spin_roll + steer_in * 360 * dt, 720);
	}
	if (pitch_in != 0)
		v.veh_spin_pitch = bound (-520, v.veh_spin_pitch + pitch_in * 320 * dt, 520);

	v.angles_x = Veh_AngDelta (v.angles_x + v.veh_spin_pitch * dt, 0);
	v.angles_z = Veh_AngDelta (v.angles_z + v.veh_spin_roll * dt, 0);
	Veh_PadHornTick (v);
};

float(vector bmin, vector bmax, entity pad) Veh_OverlapPad =
{
	if (bmin_x > pad.absmax_x || bmax_x < pad.absmin_x)
		return FALSE;
	if (bmin_y > pad.absmax_y || bmax_y < pad.absmin_y)
		return FALSE;
	if (bmin_z > pad.absmax_z || bmax_z < pad.absmin_z)
		return FALSE;
	return TRUE;
};

float(entity v, entity driver) Veh_CheckPads =
{
	local entity e;
	local vector bmin, bmax, vel, hvel;
	local float c, s, hl, hw, hx, hy, ht, spd, maxv;

	if (time < v.veh_pad_cool)
		return FALSE;
	if (time < v.veh_pad_scan_t)
		return FALSE;
	v.veh_pad_scan_t = time + 0.05;

	c = fabs (Veh_Cos (v.angles_y));
	s = fabs (Veh_Sin (v.angles_y));
	hl = Veh_HalfLen (v.veh_kind);
	hw = Veh_HalfWid (v.veh_kind);
	ht = Veh_BodyHeight (v.veh_kind);
	hx = c * hl + s * hw;
	hy = s * hl + c * hw;
	bmin = v.origin;
	bmin_x = bmin_x - hx;
	bmin_y = bmin_y - hy;
	bmin_z = bmin_z - 4;
	bmax = v.origin;
	bmax_x = bmax_x + hx;
	bmax_y = bmax_y + hy;
	bmax_z = bmax_z + ht;

	if (skypad_present)
	{
		e = skypad_head;
		while (e != world)
		{
			if (!bm_wasfreed (e) && Veh_OverlapPad (bmin, bmax, e))
			{
				SkyPad_RaiseMaxVel ();
				if (driver != world && driver.ishuman == 1 && !driver.skypad_vel_sent)
				{
					driver.skypad_vel_sent = TRUE;
					stuffcmd (driver, "sv_maxvelocity 6500\n");
				}
				vel = SkyPad_CalcVel (v.origin + '0 0 2', e.pos1, e.height);
				v.veh_pad_cool = time + 0.65;
				v.veh_air = TRUE;
				v.veh_vz = vel_z;
				v.velocity = vel;
				Veh_ResetPadStunt (v);
				hvel = vel;
				hvel_z = 0;
				if (vlen (hvel) > 120)
					v.angles_y = vectoyaw (hvel);
				v.veh_yawrate = 0;
				dprint (strcat ("veh skypad: kind=", ftos (v.veh_kind), " pad_spin=", ftos (v.veh_pad_spin), " yaw=", ftos (v.angles_y), " vel=", vtos (v.velocity), "\n"));
				setorigin (v, v.origin + '0 0 12');
				sound7 (v, CHAN_AUTO, "skypad/launch.wav", 0.90, ATTN_NORM, SNDSPD * (0.96 + random () * 0.08));
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
		if (!bm_wasfreed (e) && Veh_OverlapPad (bmin, bmax, e))
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

			v.veh_pad_cool = time + 0.40;
			v.velocity = vel;
			if (vel_z > 10)
			{
				v.veh_air = TRUE;
				v.veh_vz = vel_z;
				Veh_ResetPadStunt (v);
				hvel = vel;
				hvel_z = 0;
				if (vlen (hvel) > 200)
					v.angles_y = vectoyaw (hvel);
				v.veh_yawrate = 0;
				setorigin (v, v.origin + '0 0 12');
			}
			if (!(e.spawnflags & NO_SOUND))
				sound7 (v, CHAN_AUTO, "ambience/windfly.wav", 0.80, ATTN_NORM, SNDSPD * (0.95 + random () * 0.12));
			if (e.spawnflags & PUSH_ONCE)
				BM_PushRemove (e);
			return TRUE;
		}
		e = e.bm_push_next;
	}
	return FALSE;
};

// ---------------------------------------------------------------- per-vehicle driving characteristics

float(float kind) Veh_TopSpeed =
{
	if (kind == VEH_VAN)       return 900;
	if (kind == VEH_TUKTUK)    return 855;
	if (kind == VEH_GTCAR)     return 830;
	if (kind == VEH_COUPE)     return 780;
	if (kind == VEH_SEDAN)     return 720;
	if (kind == VEH_TRUCK)     return 670;
	if (kind == VEH_HDTRUCK)   return 620;
	if (kind == VEH_SCHOOLBUS) return 600;
	if (kind == VEH_GOLFCART)  return 610;
	return VD_TOP;
};

float(float kind) Veh_BaseAccel =
{
	if (kind == VEH_VAN)       return 480;
	if (kind == VEH_TUKTUK)    return 365;
	if (kind == VEH_GTCAR)     return 320;
	if (kind == VEH_GOLFCART)  return 290;
	if (kind == VEH_COUPE)     return 285;
	if (kind == VEH_SEDAN)     return 250;
	if (kind == VEH_TRUCK)     return 225;
	if (kind == VEH_HDTRUCK)   return 200;
	if (kind == VEH_SCHOOLBUS) return 185;
	return VD_ACCEL;
};

float(float kind) Veh_BaseGrip =
{
	if (kind == VEH_VAN)       return 1180;
	if (kind == VEH_GOLFCART)  return 820;
	if (kind == VEH_COUPE)     return 810;
	if (kind == VEH_TUKTUK)    return 790;
	if (kind == VEH_SEDAN)     return 760;
	if (kind == VEH_GTCAR)     return 740;
	if (kind == VEH_TRUCK)     return 730;
	if (kind == VEH_HDTRUCK)   return 690;
	if (kind == VEH_SCHOOLBUS) return 660;
	return VD_GRIP;
};

float(float kind) Veh_Wheelbase =
{
	if (kind == VEH_SCHOOLBUS) return 198;
	if (kind == VEH_HDTRUCK)   return 156;
	if (kind == VEH_VAN)       return 148;
	if (kind == VEH_TRUCK)     return 142;
	if (kind == VEH_SEDAN)     return 116;
	if (kind == VEH_GTCAR)     return 114;
	if (kind == VEH_COUPE)     return 108;
	if (kind == VEH_TUKTUK)    return 77;
	if (kind == VEH_GOLFCART)  return 72;
	return VD_WHEELBASE;
};

float(float kind) Veh_MaxPass =
{
	if (Veh_IsKart (kind))
		return 0;
	if (kind == VEH_VAN || kind == VEH_SCHOOLBUS)
		return 5;
	if (kind == VEH_TRUCK || kind == VEH_HDTRUCK)
		return 4;
	if (kind == VEH_SEDAN || kind == VEH_GOLFCART || kind == VEH_TUKTUK)
		return 3;
	return 2;
};

// ---------------------------------------------------------------- the footprint: 20 hulls swept around the real body

// body-space (x forward, y left) spots round the vehicle's edge where a 20 x 20 hull is swept, scaled to each vehicle's real footprint
vector(float kind, float i) Veh_ProbeOfs =
{
	local float k, hl, hw, sx;

	hl = max (24, Veh_HalfLen (kind) - 10);
	hw = max (14, Veh_HalfWid (kind) - 10);
	if (i < 4)
	{
		k = i;
		return '1 0 0' * hl + '0 1 0' * ((0 - hw) + (2 * hw / 3.0) * k);
	}
	if (i < 8)
	{
		k = i - 4;
		return '-1 0 0' * hl + '0 1 0' * ((0 - hw) + (2 * hw / 3.0) * k);
	}
	sx = hl * 0.78;
	if (i < 14)
	{
		k = i - 8;
		return '0 1 0' * hw + '1 0 0' * ((0 - sx) + (2 * sx / 5.0) * k);
	}
	k = i - 14;
	return '0 -1 0' * hw + '1 0 0' * ((0 - sx) + (2 * sx / 5.0) * k);
};

/*
Sweep every footprint hull from the van at (org0, yaw0) to the van at (org1, yaw1). TRUE if the way is clear;
otherwise vd_hitnorm (flat, unit), vd_hitpos and vd_hitent describe the first thing hit.
Hulls that start inside something are ignored (the van can always drive back out of a bad spot), and so are ramps:
a surface that faces up (normal z >= 0.7) is ground for the wheels to follow, not a wall.
*/
float(entity v, vector org0, float yaw0, vector org1, float yaw1) Veh_DriveSweep =
{
	local float i, best, c0, s0, c1, s1, hz;
	local vector o, p0, p1;

	c0 = Veh_Cos (yaw0);
	s0 = Veh_Sin (yaw0);
	c1 = Veh_Cos (yaw1);
	s1 = Veh_Sin (yaw1);
	hz = max (36, Veh_BodyHeight (v.veh_kind) - 20);
	best = 1;
	vd_hitent = world;
	vd_hitnorm = '0 0 0';
	i = 0;
	while (i < 20)
	{
		o = Veh_ProbeOfs (v.veh_kind, i);
		p0 = org0;
		p0_x = org0_x + c0 * o_x - s0 * o_y;
		p0_y = org0_y + s0 * o_x + c0 * o_y;
		p0_z = org0_z + 20;
		p1 = org1;
		p1_x = org1_x + c1 * o_x - s1 * o_y;
		p1_y = org1_y + s1 * o_x + c1 * o_y;
		p1_z = org1_z + 20;
		tracebox (p0, '-10 -10 0', '10 10 0' + '0 0 1' * hz, p1, FALSE, v);
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

// ---------------------------------------------------------------- the road under the wheels

void(entity v, vector org, float yaw) Veh_GroundSample =
{
	local float i, wx, wy, wxf, wxr, wyt, wb, c, s, sum, have0, tf, tl, hf, hr, hl, hrt;
	local float h0, h1, h2, h3, hh, mask;
	local vector p, q;

	wxf = Veh_HalfLen (v.veh_kind) * 0.72;
	wxr = 0 - Veh_HalfLen (v.veh_kind) * 0.62;
	wyt = Veh_HalfWid (v.veh_kind) * 0.85;
	wb = max (60, wxf - wxr);

	c = Veh_Cos (yaw);
	s = Veh_Sin (yaw);
	vd_found = 0;
	sum = 0;
	mask = 0;
	h0 = 0;
	h1 = 0;
	h2 = 0;
	h3 = 0;
	i = 0;
	while (i < 4)
	{
		if (i < 2)
			wx = wxf;
		else
			wx = wxr;
		if (i == 0 || i == 2)
			wy = wyt;
		else
			wy = 0 - wyt;
		p = org;
		p_x = org_x + c * wx - s * wy;
		p_y = org_y + s * wx + c * wy;
		p_z = org_z + 24;
		q = p;
		q_z = org_z - 48;
		tracebox (p, '-2 -2 0', '2 2 2', q, 1, v);		// MOVE_NOMONSTERS + Hull 1: hits worldspawn & SOLID_BSP ramps/rubble/roofs (incl. clip ramps), skips parked BBOX vehicles
		if (!trace_startsolid && trace_fraction < 1 && trace_plane_normal_z > 0.5 && (trace_ent == world || trace_ent.solid == SOLID_BSP))
		{
			hh = trace_endpos_z;
			vd_found = vd_found + 1;
			sum = sum + hh;
			if (i == 0)
			{
				h0 = hh;
				mask = mask + 1;
			}
			else if (i == 1)
			{
				h1 = hh;
				mask = mask + 2;
			}
			else if (i == 2)
			{
				h2 = hh;
				mask = mask + 4;
			}
			else
			{
				h3 = hh;
				mask = mask + 8;
			}
		}
		i = i + 1;
	}
	if (vd_found == 0)
		return;
	have0 = sum / vd_found - 24;	// a hanging wheel
	if (!(mask & 1))
		h0 = have0;
	if (!(mask & 2))
		h1 = have0;
	if (!(mask & 4))
		h2 = have0;
	if (!(mask & 8))
		h3 = have0;
	hf = (h0 + h1) * 0.5;
	hr = (h2 + h3) * 0.5;
	hl = (h0 + h2) * 0.5;
	hrt = (h1 + h3) * 0.5;
	vd_gh = (h0 + h1 + h2 + h3) * 0.25 + VD_HEIGHT;
	vd_pitch = Veh_RiseAngle (hf - hr, wb);
	tf = (hf - hr) / wb;
	tl = (hl - hrt) / max (36, wyt * 2);
	vd_slope_f = tf / vlen ('1 0 0' + '0 1 0' * tf);		// sine of the slope
	vd_slope_l = tl / vlen ('1 0 0' + '0 1 0' * tl);
};

// ---------------------------------------------------------------- solid box while driven / parked

float(float kind) Veh_DrivenTopZ =
{
	if (Veh_IsKart (kind))
		return 34;
	if (kind == VEH_SCHOOLBUS)
		return 62;
	if (kind == VEH_VAN || kind == VEH_TRUCK || kind == VEH_HDTRUCK)
		return 52;
	return 46;
};

// While driven the vehicle is one box that fits INSIDE its real footprint at any heading; bmax_z stays at beltline
// height so enemies easily hit the body while riding gunners fire cleanly 360 degrees above the roof/windows!
void(entity v) Veh_DriveBounds =
{
	local float c, s, hl, hw, hx, hy, a1, a2, k;
	local vector bmin, bmax;

	hl = Veh_HalfLen (v.veh_kind) * 0.86;
	hw = Veh_HalfWid (v.veh_kind) * 0.86;
	c = fabs (Veh_Cos (v.angles_y));
	s = fabs (Veh_Sin (v.angles_y));
	hx = c * hl + s * hw;
	hy = s * hl + c * hw;
	a1 = hx * c + hy * s;
	a2 = hx * s + hy * c;
	k = 1;
	if (hl / a1 < k)
		k = hl / a1;
	if (hw / a2 < k)
		k = hw / a2;
	bmin = '0 0 0';
	bmax = '0 0 0';
	bmin_x = 0 - hx * k;
	bmin_y = 0 - hy * k;
	bmax_x = hx * k;
	bmax_y = hy * k;
	bmax_z = Veh_DrivenTopZ (v.veh_kind);
	setsize (v, bmin, bmax);
};

// everyone (but the driver) standing inside the van's footprint gets thrown out the back
void(entity v, entity keep) Veh_EjectOthers =
{
	local entity e, nxt;
	local vector rel, fwd, lft, spot;
	local float lx, ly, lz, i, hl, hw, inbox, found;

	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	// sized per kind (these were van numbers: a bus is ~165 long), and the radius reaches a bus's corners
	hl = Veh_HalfLen (v.veh_kind);
	hw = Veh_HalfWid (v.veh_kind);
	e = findradius (v.origin, hl + hw + 60);
	while (e != world)
	{
		nxt = e.chain;
		if (e != keep && e != v && e.health > 0 && e.veh_ride == world && e.veh_van == world && (e.classname == "player" || (e.flags & FL_MONSTER)))	// seated riders / drivers stay put: the friends just auto-seated from the cargo bay were thrown out and told they fell
		{
			rel = e.origin - v.origin;
			lx = rel * fwd;
			ly = rel * lft;
			lz = rel_z;
			// an angled parked vehicle's solid is its rotated AABB, which reaches past the footprint: overlap with that too
			inbox = FALSE;
			if (v.solid != SOLID_NOT && e.origin_x + e.mins_x < v.origin_x + v.maxs_x && e.origin_x + e.maxs_x > v.origin_x + v.mins_x && e.origin_y + e.mins_y < v.origin_y + v.maxs_y && e.origin_y + e.maxs_y > v.origin_y + v.mins_y)
				inbox = TRUE;
			if ((inbox || (fabs (lx) < hl + 16 && fabs (ly) < hw + 8)) && lz > -40 && lz < 110)
			{
				spot = v.origin;
				i = 0;
				while (i < 5)
				{
					if (i == 0)
						spot = v.origin - fwd * (hl + 50) + lft * (crandom () * 24);
					else if (i == 1)
						spot = v.origin + lft * (hw + 32) + fwd * (crandom () * 50);
					else if (i == 2)
						spot = v.origin - lft * (hw + 32) + fwd * (crandom () * 50);
					else if (i == 3)
						spot = v.origin + fwd * (hl + 36);
					spot_z = v.origin_z + 26;
					found = FALSE;
					if (i == 4)
					{
						// all four sides blocked (angled box, walls): any door spot or the roof
						if (Veh_ExitSpot (v, e))
						{
							spot = vd_exit;
							found = TRUE;
						}
					}
					else if (Veh_FreeSpot (e, spot))
						found = TRUE;
					if (found)
					{
						setorigin (e, spot);
						e.velocity = '0 0 140' - fwd * 90;
						e.flags = e.flags - (e.flags & FL_ONGROUND);
						if (e.classname == "player")
							sprint (e, "The van pulls away and you tumble out!\n");
						i = 99;
					}
					i = i + 1;
				}
			}
		}
		e = nxt;
	}
};

// the vehicle has stopped being driven: square to the world (within 22 deg) a van gets its walk-in interior back
void(entity v) Veh_Park =
{
	local float snap, d;

	v.veh_coast_until = 0;
	Veh_AllPassengersBail (v, FALSE);
	if (v.veh_air)
	{
		tracebox (v.origin, v.mins, v.maxs, v.origin - '0 0 4096', TRUE, v);
		if (!trace_startsolid && !trace_allsolid && trace_fraction < 1)
			setorigin (v, trace_endpos + '0 0 0.5');
	}
	v.velocity = '0 0 0';
	v.veh_steer = 0;
	v.veh_yawrate = 0;
	v.veh_rpm = 0;
	v.veh_boost = 0;
	v.veh_land_dip = 0;
	v.veh_drift_t = 0;
	v.veh_air = FALSE;
	Veh_ResetPadStunt (v);
	v.gk_boosting = FALSE;
	v.gk_boost_t = 0;
	v.gk_boost_pwr = 0;
	v.gk_drift_dir = 0;
	v.gk_drift_charge = 0;
	v.gk_drift_tier = 0;
	v.gk_air_t = 0;
	v.gk_speed = 0;
	v.angles_x = 0;
	v.angles_z = 0;
	v.movetype = MOVETYPE_NONE;
	v.solid = SOLID_BBOX;
	snap = floor ((v.angles_y + 45) / 90) * 90;
	d = Veh_AngDelta (v.angles_y, snap);
	if (v.veh_kind == VEH_VAN && fabs (d) <= 22)
	{
		v.angles_y = Veh_NormYaw (snap);
		setorigin (v, v.origin);
		Veh_Van_InitCollision (v);
	}
	else
	{
		Veh_SetRotatedBounds (v, v.veh_kind, FALSE);
		setorigin (v, v.origin);
	}
	Veh_EjectOthers (v, world);
};

// ---------------------------------------------------------------- hitting things

// the vehicle ran into something that can be hurt (a person, a monster, another vehicle's body)
void(entity v, entity hit, float imp) Veh_RamHit =
{
	local entity driver;
	local float dmg, is_veh, is_live;
	local vector dir;

	if (imp < 75 || time < hit.veh_hit_t)
		return;
	if (hit.veh_ride == v || (hit.veh_last_van == v && time < hit.veh_bail_safe_t))
		return;
	driver = v.veh_driver;
	if (driver == world)
		driver = v.veh_igniter;
	if (driver == world)
		driver = v;
	dir = v.velocity;
	dir_z = 0;
	if (vlen (dir) > 0.1)
		dir = normalize (dir);
	else
		dir = Veh_Fwd (v.angles_y);
	is_live = ((hit.flags & FL_CLIENT) || (hit.flags & FL_MONSTER));
	is_veh = (hit.veh_kind > 0 || hit.classname == "veh_van_clip");
	dmg = (imp - 45) * 0.45;		// ~250+ at cruise, ~500+ boosted: flattens monsters & enemies cleanly
	if (v.veh_kind == VEH_VAN && is_veh)
		dmg = dmg * 1.35;
	hit.veh_hit_t = time + 0.35;
	if (autocvar_veh_debug)
	{
		dprint ("VEH ram ");
		dprint (hit.classname);
		dprint (" imp=");
		dprint (ftos (floor (imp)));
		dprint (" dmg=");
		dprint (ftos (floor (dmg)));
		dprint ("\n");
	}
	if (is_live)
	{
		hit.velocity = hit.velocity + dir * (imp * 1.15) + '0 0 220';
		hit.flags = hit.flags - (hit.flags & FL_ONGROUND);
		sound7 (hit, CHAN_BODY, "vehicles/tire_thud1.wav", 1, ATTN_NORM, 70 + random () * 15);
		if (veh_fx_sparks > 0 && imp > 220)
			pointparticles (veh_fx_sparks, hit.origin + '0 0 24', '0 0 0', 1);
	}
	else if (is_veh && veh_fx_sparks > 0)
		pointparticles (veh_fx_sparks, vd_hitpos, '0 0 0', 1);
	if (v.veh_driver != world && imp > 140)
		Veh_AddShake (v.veh_driver, bound (1.5, imp / 190, 6.0), bound (0.14, imp / 1800, 0.30));
	veh_runover = TRUE;
	T_Damage (hit, v, driver, dmg);
	veh_runover = FALSE;
	if ((hit.flags & FL_MONSTER) && hit.health <= 0)
		hit.solid = SOLID_NOT;		// let the van plow cleanly over flattened monster corpses
	if (is_live && imp > 200)
		v.veh_boost = min (1, v.veh_boost + 0.25);		// ramming momentum keeps turbo spooled!
	if ((hit.flags & FL_CLIENT) && dmg > 20)
	{
		if (v.veh_kind == VEH_VAN)
		{
			if (v.veh_boost <= 0.5)
				T_Damage (v, world, world, min (6, dmg * 0.03));
		}
		else
			T_Damage (v, world, world, dmg * 0.2);
	}
};

// T_Damage (combat.qc) hands a driver's damage to his van; the crash jolt is meant for him, so he is unhooked for the hit
void(entity v, entity p, float dmg) Veh_JoltDriver =
{
	p.veh_van = world;
	T_Damage (p, world, world, dmg);
	if (p.veh_van == world)
		p.veh_van = v;		// if the jolt killed him, Veh_DriveFrame / Veh_DriveWatch let him go as usual
};

// the van hit something that does not move: sparks, a clang, damage to the van, and a jolt for the driver
void(entity v, float imp, vector at) Veh_Crash =
{
	local entity driver;
	local float dmg;

	if (time < v.veh_crash_t)
		return;
	v.veh_crash_t = time + 0.28;
	if (autocvar_veh_debug)
	{
		dprint ("VEH crash imp=");
		dprint (ftos (floor (imp)));
		dprint (" van hp=");
		dprint (ftos (v.health));
		dprint ("\n");
	}
	if (veh_fx_sparks > 0)
	{
		pointparticles (veh_fx_sparks, at, '0 0 0', 1);
		if (imp > 450)
			pointparticles (veh_fx_sparks, at + '0 0 18', '0 0 0', 1);
	}
	if (imp > 450 && veh_fx_smoke > 0)
		pointparticles (veh_fx_smoke, at + '0 0 14', '0 0 0', 1);
	if (random () < 0.5)
		sound7 (v, CHAN_BODY, "vehicles/clang1.wav", bound (0.55, imp / 420, 1), ATTN_NORM, 78 + random () * 16);
	else
		sound7 (v, CHAN_BODY, "vehicles/clang2.wav", bound (0.55, imp / 420, 1), ATTN_NORM, 78 + random () * 16);
	if (imp > 450)
		sound7 (v, CHAN_AUTO, "vehicles/hit_metal2.wav", bound (0.55, imp / 550, 1), ATTN_NORM, 74 + random () * 14);
	driver = v.veh_driver;
	if (driver != world)
		Veh_AddShake (driver, bound (2.2, imp / 145, 9.5), bound (0.20, imp / 1200, 0.52));
	if (v.veh_kind == VEH_VAN)
	{
		if (imp > 650 && driver != world)
			Veh_JoltDriver (v, driver, min (45, (imp - 650) * 0.055));
		dmg = (imp - 300) * 0.10;
	}
	else
	{
		if (imp > 420 && driver != world)
			Veh_JoltDriver (v, driver, min (45, (imp - 420) * 0.09));
		dmg = (imp - 210) * 0.16;
	}
	if (dmg > 0)
		T_Damage (v, world, world, dmg);
};

// ---------------------------------------------------------------- what the driver sees of the van

/*
Called by the engine for each client the van is about to be sent to (self = the van, other = that client); it must set
everything it varies every time, and return TRUE. From inside the cab body_a (the outer shell) paints the whole view flat grey, so the
driver, in the cockpit view only, is sent the van with skin 2 / 3 (body_a left out; scripts/vehicles.shader
progs/veh_van_nodraw). Everyone else, and the driver in the chase view, get the normal skin: 0 intact, 1 scorched.
*/
float() Veh_VanCustomize =
{
	local float k, cam_inside;
	local vector rel;
	local float lx, ly;

	k = 0;
	if (self.veh_state == VEH_STATE_FIRE)
		k = 1;
	cam_inside = FALSE;
	if (other.veh_van == self && other.veh_camera == 0 && !self.veh_pad_spin)
		cam_inside = TRUE;
	else if (other.veh_van == self && self.veh_cament != world)
	{
		// If a tight wall crash forced the 3rd-person camera inside the white van shell, hide body_a so it never flashes white
		rel = self.veh_cament.origin - self.origin;
		lx = rel * Veh_Fwd (self.angles_y);
		ly = rel * Veh_Lft (self.angles_y);
		if (fabs (lx) < 120 && fabs (ly) < 52 && rel_z > -10 && rel_z < 102)
			cam_inside = TRUE;
	}
	if (self.veh_state != VEH_STATE_WRECK && cam_inside)
		k = k + 2;
	self.skin = k;
	return TRUE;			// FALSE would mean: do not send the van to this client
};

// ---------------------------------------------------------------- the driver's eyes

void(entity p, entity v, float dt) Veh_DriveCamera =
{
	local entity cam;
	local vector fwd, lft, pos, tgt, ang;
	local float yaw, pitch, d, spd, lead, hl, ht, cdist, cup;
	local float want_dist, spd_frac, vf_cam, look_fwd, tgt_yaw, vel_d, want_pitch;

	if (Veh_IsKart (v.veh_kind))
	{
		GK_DriveCamera (p, v, dt);
		return;
	}

	cam = v.veh_cament;
	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	spd = vlen (v.velocity);
	hl = Veh_HalfLen (v.veh_kind);
	ht = Veh_BodyHeight (v.veh_kind);

	if (p.veh_camera == 0 && !v.veh_pad_spin)
	{
		if (v.veh_kind == VEH_VAN)
			pos = v.origin + fwd * VD_EYE_X + lft * VD_EYE_Y + '0 0 1' * VD_EYE_Z;
		else if (v.veh_kind == VEH_TUKTUK)
			pos = v.origin + fwd * 14 + '0 0 52';
		else
			pos = v.origin + fwd * (hl * 0.28) + '0 0 1' * (ht + 6);
		lead = 0 - v.veh_steer * 9 * bound (0, spd / 220, 1);		// steering right (+) looks right (yaw falls)
		p.veh_cam_look = p.veh_cam_look + (lead - p.veh_cam_look) * min (1, dt * 5);
		yaw = Veh_NormYaw (v.angles_y + p.veh_cam_look);
		pitch = 0 - v.angles_x;
		p.veh_cam_yaw = v.angles_y;
		p.veh_cam_pitch = pitch;
	}
	else
	{
		// 3rd-person chase: elevated cleanly above the tall L2H2 roof with speed pullback, look-ahead, and drift yaw lag
		cdist = max (180, hl * 2.30);
		if (v.veh_kind == VEH_VAN)
			cup = VD_CAM_UP;
		else
			cup = max (62, ht + 22);
		spd_frac = bound (0, spd / 1100, 1);
		want_dist = cdist + 56 * spd_frac + 28 * v.veh_boost;
		if (p.veh_cam_dist < 100)
			p.veh_cam_dist = want_dist;
		p.veh_cam_dist = p.veh_cam_dist + (want_dist - p.veh_cam_dist) * min (1, dt * 4.5);

		if (v.veh_pad_spin)
		{
			local vector vel_xy;
			vel_xy = v.velocity;
			vel_xy_z = 0;
			tgt_yaw = p.veh_cam_yaw;
			if (vlen (vel_xy) > 60)
				tgt_yaw = vectoyaw (vel_xy);
			d = Veh_AngDelta (tgt_yaw, p.veh_cam_yaw);
			p.veh_cam_yaw = Veh_NormYaw (p.veh_cam_yaw + d * min (1, dt * 6.0));
			yaw = p.veh_cam_yaw;

			want_pitch = VD_CAM_PITCH + bound (-18, 0 - v.veh_vz * 0.015, 18);
			p.veh_cam_pitch = p.veh_cam_pitch + (want_pitch - p.veh_cam_pitch) * min (1, dt * 6);
			pitch = p.veh_cam_pitch;

			look_fwd = 18 + 24 * bound (0, vlen (vel_xy) / 900, 1);
			tgt = v.origin + Veh_Fwd (yaw) * look_fwd + '0 0 1' * cup;
		}
		else
		{
			vf_cam = v.velocity * fwd;
			look_fwd = 18 + 24 * bound (0, vf_cam / 900, 1);
			tgt_yaw = v.angles_y;
			if (spd > 180 && vf_cam > 80)
			{
				vel_d = Veh_AngDelta (vectoyaw (v.velocity), v.angles_y);
				tgt_yaw = Veh_NormYaw (v.angles_y + bound (-26, vel_d * 0.35, 26));
			}
			d = Veh_AngDelta (tgt_yaw, p.veh_cam_yaw);
			p.veh_cam_yaw = Veh_NormYaw (p.veh_cam_yaw + d * min (1, dt * 5.2));
			yaw = p.veh_cam_yaw;

			want_pitch = VD_CAM_PITCH - v.angles_x * 0.35;
			p.veh_cam_pitch = p.veh_cam_pitch + (want_pitch - p.veh_cam_pitch) * min (1, dt * 6);
			pitch = p.veh_cam_pitch;

			tgt = v.origin + fwd * look_fwd + '0 0 1' * cup;
		}
		traceline (v.origin + '0 0 36', tgt, 3, v);
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
		{
			pos = pos + trace_plane_normal * 10;
			if (v.veh_kind == VEH_VAN && pos_z < v.origin_z + 115)
			{
				traceline (pos, pos + '0 0 24', 3, v);
				if (trace_fraction >= 1)
					pos_z = v.origin_z + 115;
			}
		}
		traceline (pos, pos + '0 0 12', 3, v);
		if (trace_fraction < 1)
			pos_z = trace_endpos_z - 12;
	}
	setorigin (cam, pos);
	cam.angles = '0 0 0';
	cam.angles_x = pitch;
	cam.angles_y = yaw;
	p.angles = '0 0 0';
	p.angles_x = pitch;
	p.angles_y = yaw;
	p.fixangle = TRUE;
	Veh_ApplyCamShake (p, cam, v);
};

// ---------------------------------------------------------------- sound

// the engine: overlapping windowed grains whose pitch follows the revs (see make_vehicle_drive_sounds.py)
void(entity v, float thr) Veh_EngineSound =
{
	local float pitch, vol;

	if (time < v.veh_eng_t)
		return;
	if (Veh_IsKart (v.veh_kind))
	{
		pitch = 78 + 165 * v.veh_rpm;
		if (v.gk_boosting || time < v.gk_boost_t)
			pitch = pitch * 1.15;
		vol = 0.28 + 0.18 * thr;
		sound7 (v, VD_SOUND_CH, "vehicles/engine_grain_tuktuk.wav", vol, ATTN_NORM, min (245, pitch * 1.08));
		if (v.veh_eng_t < time - 0.2)
			v.veh_eng_t = time;
		v.veh_eng_t = v.veh_eng_t + 16 / max (60, pitch);
		return;
	}
	pitch = 62 + 150 * v.veh_rpm;
	if (time < v.veh_shift_t)
		pitch = pitch * 0.86;
	vol = 0.30 + 0.20 * thr;
	if (v.veh_kind == VEH_TUKTUK)
		sound7 (v, VD_SOUND_CH, "vehicles/engine_grain_tuktuk.wav", vol, ATTN_NORM, pitch * 1.12);
	else
		sound7 (v, VD_SOUND_CH, "vehicles/engine_grain.wav", vol, ATTN_NORM, pitch);
	if (v.veh_eng_t < time - 0.2)
		v.veh_eng_t = time;
	v.veh_eng_t = v.veh_eng_t + 16 / pitch;			// half a grain: 0.16 s at pitch 100
};

void(entity v, float slip) Veh_SkidSound =
{
	local vector rear_l, rear_r, fwd, lft;
	local float vol, fx, rx, wy;

	if (time >= v.veh_skid_t)
	{
		vol = bound (0.3, (slip - 60) / 260, 1);
		sound7 (v, VD_SOUND_CH, "vehicles/tire_squeal.wav", vol * 0.8, ATTN_NORM, 92 + slip * 0.03);
		v.veh_skid_t = time + 0.3;
	}
	if (time >= v.veh_smoke_t2)
	{
		v.veh_smoke_t2 = time + 0.06;
		fx = veh_fx_drift;
		if (fx <= 0)
			fx = veh_fx_smoke;
		fwd = Veh_Fwd (v.angles_y);
		lft = Veh_Lft (v.angles_y);
		rx = Veh_HalfLen (v.veh_kind) * 0.62;
		wy = Veh_HalfWid (v.veh_kind) * 0.84;
		rear_l = v.origin - fwd * rx + lft * wy + '0 0 6';
		rear_r = v.origin - fwd * rx - lft * wy + '0 0 6';
		pointparticles (fx, rear_l, '0 0 0', 1);
		pointparticles (fx, rear_r, '0 0 0', 1);
	}
};

// ---------------------------------------------------------------- getting out and in

// TRUE while p is at the wheel. The gun-drawing helper (custom_effects.qc) hides the gun on this, as it does while a Rob
// Dob head is being flown
float(entity p) Veh_Driving =
{
	return p.veh_van != world;
};

float(entity p) Veh_Riding =
{
	return p.veh_ride != world;
};

void(entity v, vector pos, vector vel, float forced) Veh_Leave;

void() Veh_SpawnReset =
{
	local entity v;

	v = self.veh_van;
	if (v != world && !bm_wasfreed (v) && v.veh_driver == self)
		Veh_Leave (v, v.origin + '0 0 40', '0 0 0', (v.veh_state == VEH_STATE_WRECK));
	else if (v != world || self.clientcamera != self)
	{
		self.clientcamera = self;
		if (self.ishuman == 1)
		{
			msg_entity = self;
			WriteByte (MSG_ONE, 5);		// svc_setview
			WriteEntity (MSG_ONE, self);
		}
		self.alpha = 0;
		self.effects = self.effects - (self.effects & EF_NODRAW);
	}
	self.veh_van = world;
	self.veh_ride = world;
	self.veh_seat = 0;
	self.veh_bail_safe_t = 0;
};

// World-space drive-by seat offset for passenger `seat` (1..5): sits around the perimeter/bed/roof above Veh_DrivenTopZ
// so passengers have 360-degree unobstructed weapon fire with all rockets & Fun Guns!
vector(entity v, float seat) Veh_PassengerOfs =
{
	local vector fwd, lft;
	local float hl, hw, ztop, lx, ly, lz;

	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	hl = Veh_HalfLen (v.veh_kind);
	hw = Veh_HalfWid (v.veh_kind);
	ztop = Veh_DrivenTopZ (v.veh_kind) + 18;

	if (seat <= 1)
	{
		// Seat 1: Shotgun / Front-Right window gunner
		lx = hl * 0.28;
		ly = 0 - hw * 0.72;
		lz = ztop;
	}
	else if (seat == 2)
	{
		// Seat 2: Rear-Left bed / cargo-window gunner
		lx = 0 - hl * 0.44;
		ly = hw * 0.72;
		lz = ztop;
	}
	else if (seat == 3)
	{
		// Seat 3: Rear-Right bed / cargo-window gunner
		lx = 0 - hl * 0.44;
		ly = 0 - hw * 0.72;
		lz = ztop;
	}
	else if (seat == 4)
	{
		// Seat 4: Open Tailgate / Rear Barn-Door gunner
		lx = 0 - hl * 0.80;
		ly = 0;
		lz = ztop;
	}
	else
	{
		// Seat 5: Roof-Deck Center Turret gunner
		lx = 0 - hl * 0.08;
		ly = 0;
		lz = ztop + 8;
	}
	return v.origin + fwd * lx + lft * ly + '0 0 1' * lz;
};

float(entity v) Veh_FindFreeSeat =
{
	local float mx, s, taken;
	local entity e;

	mx = Veh_MaxPass (v.veh_kind);
	s = 1;
	while (s <= mx)
	{
		taken = FALSE;
		// the per-frame player list (BM_StartFrame), not a pass over every edict per seat: this runs 10 times a
		// second for each player standing beside a driven van or bus (Veh_NearPrompt)
		if (bm_player_head != world)
		{
			e = bm_player_head;
			while (e != world)
			{
				if (e.health > 0 && e.veh_ride == v && e.veh_seat == s)
					taken = TRUE;
				e = e.bm_player_next;
			}
		}
		else
		{
			e = find (world, classname, "player");
			while (e != world)
			{
				if (e.health > 0 && e.veh_ride == v && e.veh_seat == s)
					taken = TRUE;
				e = find (e, classname, "player");
			}
		}
		if (!taken)
			return s;
		s = s + 1;
	}
	return 0;
};

void(entity p, float forced) Veh_LeavePassenger =
{
	local entity v;
	local vector pos, vel, outd;

	v = p.veh_ride;
	p.veh_ride = world;
	p.veh_seat = 0;
	if (p.health > 0)
	{
		p.movetype = MOVETYPE_WALK;
		p.solid = SOLID_SLIDEBOX;
	}
	if (v == world)
		return;

	p.veh_last_van = v;
	if (!forced)
		p.veh_bail_safe_t = time + 1.25;
	pos = p.origin + '0 0 18';
	if (Veh_ExitSpot (v, p))
		pos = vd_exit;
	else if (!Veh_FreeSpot (p, pos))
	{
		// Veh_ExitSpot already found the roof blocked: the seat itself (outside the body box) before that last resort
		if (Veh_FreeSpot (p, p.origin))
			pos = p.origin;
		else
			pos = v.origin + '0 0 1' * (Veh_BodyHeight (v.veh_kind) + 28);
	}

	outd = pos - v.origin;
	outd_z = 0;
	if (vlen (outd) > 1)
		outd = normalize (outd);
	else
		outd = Veh_Lft (v.angles_y);

	if (forced)
		vel = v.velocity * 0.55 + outd * 210 + '0 0 210';
	else
		vel = v.velocity * 0.45 + outd * 150 + '0 0 165';

	setorigin (p, pos);
	p.velocity = vel;
	p.flags = p.flags - (p.flags & FL_ONGROUND);
};

void(entity v, float exploding) Veh_AllPassengersBail =
{
	local entity e;

	e = find (world, classname, "player");
	while (e != world)
	{
		if (e.veh_ride == v)
			Veh_LeavePassenger (e, exploding);
		e = find (e, classname, "player");
	}
};

void(entity v) Veh_SyncPassengers =
{
	local entity e;

	e = bm_player_head;
	if (e == world)
		e = find (world, classname, "player");
	while (e != world)
	{
		if (e.veh_ride == v)
		{
			if (e.health <= 0 || e.deadflag != 0)
			{
				e.veh_ride = world;
				e.veh_seat = 0;
			}
			else
			{
				setorigin (e, Veh_PassengerOfs (v, e.veh_seat));
				e.velocity = '0 0 0';
				e.flags = e.flags - (e.flags & FL_ONGROUND);
			}
		}
		if (bm_player_head != world)
			e = e.bm_player_next;
		else
			e = find (e, classname, "player");
	}
};

float(entity p, entity v) Veh_EnterPassenger =
{
	local float s;
	local entity oldself;

	if (p.health <= 0 || p.veh_van != world || p.veh_ride != world || p.jb_vehicle != world || p.rr_vehicle != world || p.fd_head != world || p.mmt_tank != world)
		return FALSE;
	if (EricCannon_Active (p))
		return FALSE;		// cannon riders are not seated (audit 2026-11-26)
	s = Veh_FindFreeSeat (v);
	if (s <= 0)
	{
		if (p.ishuman == 1)
			sprint (p, "All passenger seats are full!\n");
		return FALSE;
	}
	if (p.ky_cam != world)
		KY_CamDetach (p);
	RH_ResetPlayer (p);
	DK_ResetPlayer (p);
	GJ_ResetPlayer (p);
	if (p.jp_on)
	{
		oldself = self;
		self = p;
		Jetpack_Off ();
		self = oldself;
	}
	p.veh_ride = v;
	p.veh_seat = s;
	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.velocity = '0 0 0';
	p.flags = p.flags - (p.flags & FL_ONGROUND);
	setorigin (p, Veh_PassengerOfs (v, s));
	sound (v, CHAN_AUTO, "items/armor1.wav", 0.85, ATTN_NORM);
	if (p.ishuman == 1)
		centerprint (p, strcat ("Riding in ", Veh_DisplayName (v.veh_kind), "!\nAim & shoot freely | Press H to bail"));
	if (v.veh_driver != world && v.veh_driver.ishuman == 1)
		sprint (v.veh_driver, strcat (p.netname, " hopped aboard your ", Veh_DisplayName (v.veh_kind), "!\n"));
	return TRUE;
};

// Called from W_WeaponFrame right after Veh_DriveFrame (does NOT return early: passenger retains full aiming & arsenal!)
void() Veh_PassengerFrame =
{
	local entity v;

	v = self.veh_ride;
	if (v == world)
		return;
	if (bm_wasfreed (v) || v.veh_state == VEH_STATE_WRECK || self.health <= 0 || (v.veh_driver == world && time >= v.veh_coast_until))
	{
		Veh_LeavePassenger (self, FALSE);
		return;
	}
	if (self.impulse == 86)
	{
		self.impulse = 0;
		Veh_LeavePassenger (self, FALSE);
		return;
	}
	setorigin (self, Veh_PassengerOfs (v, self.veh_seat));
	self.velocity = '0 0 0';
	self.flags = self.flags - (self.flags & FL_ONGROUND);
};

// give the player back to himself
void(entity p, vector pos, vector vel, float yaw) Veh_ReleasePlayer =
{
	if (p.veh_van != world && Veh_IsKart (p.veh_van.veh_kind))
	{
		p.veh_van.gk_m1_prev = FALSE;
		p.veh_van.gk_m1_hold_t = 0;
		p.veh_van.gk_rkt_aim = FALSE;
		p.veh_van.gk_aim_enter = FALSE;
		p.veh_van.gk_rkt_charge = 0;
		p.veh_van.gk_rkt_armed = FALSE;
		if (p.ishuman == 1)
			centerprint (p, "");
	}
	p.gk_st_mode = 0;
	p.gk_st_prog = 0;
	p.gk_st_nitro = 0;
	p.gk_st_lock = 0;
	p.veh_van = world;
	p.clientcamera = p;
	msg_entity = p;
	WriteByte (MSG_ONE, 5);			// svc_setview
	WriteEntity (MSG_ONE, p);
	p.alpha = 0;					// 0 = opaque
	p.effects = p.effects - (p.effects & EF_NODRAW);
	if (p.health > 0)
	{
		p.movetype = p.veh_oldmove;
		if (p.movetype == MOVETYPE_NONE || p.movetype == 0)
			p.movetype = MOVETYPE_WALK;
		p.solid = p.veh_oldsolid;
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

// the driver is out: engine off, camera gone, the van is parked. forced = it is blowing up (nothing to park)
void(entity v, vector pos, vector vel, float forced) Veh_Leave =
{
	local entity p;
	local float yaw;

	p = v.veh_driver;
	v.veh_driver = world;
	v.veh_drive_mode = FALSE;
	dprint ("lanvan: chant stops\n");
	sound (v, VD_MUSIC_CH, "misc/null.wav", 1, ATTN_NORM);		// the chant stops with the engine
	if (p != world && p.classname == "player")
	{
		yaw = p.veh_cam_yaw;
		if (p.veh_camera == 0 && !v.veh_pad_spin)
			yaw = v.angles_y;
		Veh_ReleasePlayer (p, pos, vel, yaw);
	}
	if (v.veh_cament != world)
	{
		remove (v.veh_cament);
		v.veh_cament = world;
	}
	if (v.veh_driverent != world)
	{
		remove (v.veh_driverent);
		v.veh_driverent = world;
	}
	v.angles_x = 0;
	v.angles_z = 0;
	if (!forced)
	{
		Veh_Park (v);
		if (p != world && p.classname == "player")
			Veh_EjectOthers (v, world);		// the driver too, if parking boxed him in
	}
};

// the van is exploding (vehicles.qc): the driver is thrown clear into the air so he sees the fireball & shake
void(entity v) Veh_DriverBail =
{
	local vector seat, vel, out_dir;

	if (v.veh_driver == world)
		return;
	seat = v.origin + Veh_Fwd (v.angles_y) * 40 + Veh_Lft (v.angles_y) * 19.8;
	seat_z = v.origin_z + 40;
	if (Veh_ExitSpot (v, v.veh_driver))
		seat = vd_exit;		// clear side/rear/roof exit spot outside the wreck
	out_dir = seat - v.origin;
	out_dir_z = 0;
	if (vlen (out_dir) > 1)
		out_dir = normalize (out_dir);
	else
		out_dir = Veh_Lft (v.angles_y);
	vel = v.velocity * 0.35 + out_dir * 190;
	vel_z = max (260, v.velocity_z * 0.25 + 260);
	Veh_Leave (v, seat, vel, TRUE);
};

// ClientDisconnect (client.qc), self = the leaving player: a driver who drops leaves the van parked, not "being driven"
void() Veh_ClientGone =
{
	local entity v;

	if (self.veh_ride != world)
	{
		self.veh_ride = world;
		self.veh_seat = 0;
	}
	v = self.veh_van;
	if (v != world && v.veh_driver == self)
		Veh_Leave (v, v.origin + '0 0 40', '0 0 0', FALSE);
	self.veh_van = world;
};

// the van's own think (vehicles.qc): the driver died, dropped or was replaced without going through the door
void(entity v) Veh_DriveWatch =
{
	local entity p;

	p = v.veh_driver;
	if (p == world)
		return;
	if (p.classname != "player" || p.health <= 0 || p.veh_van != v)
		Veh_Leave (v, p.origin, '0 0 0', v.veh_state == VEH_STATE_WRECK);		// he stays where he fell (or is gone); the van is parked
};

// where can he get out? The driver's door, the passenger's, the back, the nose, or roof
float(entity v, entity p) Veh_ExitSpot =
{
	local float i, lx, ly, hl, hw;
	local vector pos, fwd, lft;

	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	hl = Veh_HalfLen (v.veh_kind);
	hw = Veh_HalfWid (v.veh_kind);
	i = 0;
	while (i < 5)
	{
		lx = hl * 0.25;
		ly = hw + 22;
		if (i == 1)
			ly = 0 - (hw + 22);
		if (i == 2)
		{
			lx = 0 - (hl + 38);
			ly = 0;
		}
		if (i == 3)
		{
			lx = hl + 34;
			ly = 0;
		}
		if (i == 4)
		{
			pos = v.origin + '0 0 1' * (Veh_BodyHeight (v.veh_kind) + 28);
			if (Veh_FreeSpot (p, pos))
			{
				vd_exit = pos;
				return TRUE;
			}
			return FALSE;
		}
		pos = v.origin + fwd * lx + lft * ly;
		pos_z = v.origin_z + 28;
		traceline (pos, pos - '0 0 96', 3, v);
		if (trace_fraction < 1 && !trace_startsolid)
		{
			pos_z = trace_endpos_z + 25;
			if (Veh_FreeSpot (p, pos))
			{
				vd_exit = pos;
				return TRUE;
			}
		}
		i = i + 1;
	}
	return FALSE;
};

// Coasting runaway step when a driver performs a high-speed Hollywood Dive-Bail!
void(entity v, float dt) Veh_CoastStep =
{
	local vector org0, org1, n, vel;
	local float yaw0, yaw1, vn, imp, living, z, d, grav, air_rising;

	if (v.veh_driver != world || v.veh_state == VEH_STATE_WRECK)
	{
		v.veh_coast_until = 0;
		return;
	}
	if (!Veh_IsKart (v.veh_kind) && Veh_CheckPads (v, world))
		v.veh_coast_until = max (v.veh_coast_until, time + 5.0);
	vel = v.velocity;
	vel_z = 0;
	if (!v.veh_air && (time >= v.veh_coast_until || vlen (vel) < 35))
	{
		Veh_Park (v);
		return;
	}
	if (v.veh_air)
		v.veh_coast_until = max (v.veh_coast_until, time + 0.5);
	yaw0 = v.angles_y;
	yaw1 = yaw0;
	if (v.veh_air && v.veh_pad_spin)
		yaw1 = Veh_NormYaw (yaw0 + v.veh_spin_yaw * dt);
	org0 = v.origin;
	org1 = org0 + vel * dt;
	air_rising = (!Veh_IsKart (v.veh_kind) && v.veh_air && v.veh_vz > 0);
	if (air_rising)
		org1_z = Veh_StepAirRise (v, org0, dt);
	if (Veh_IsKart (v.veh_kind))
	{
		GK_CheckPads (v, world);
		v.gk_speed = vlen (vel);
		if (!Veh_DriveSweep (v, org0, yaw0, org1, yaw0))
		{
			n = vd_hitnorm;
			vn = vel * n;
			if (vn < 0)
			{
				imp = 0 - vn;
				living = FALSE;
				if (vd_hitent != world && vd_hitent.takedamage && ((vd_hitent.flags & FL_CLIENT) || (vd_hitent.flags & FL_MONSTER)))
				{
					living = TRUE;
					Veh_RamHit (v, vd_hitent, imp);
					vel = vel * 0.95;
				}
				else
				{
					vel = (vel - n * (vn * 1.65)) * 0.80;
					sound7 (v, CHAN_BODY, "bikes/tire_bounce.wav", bound (0.35, imp / 450, 0.9), ATTN_NORM, 96 + random () * 16);
				}
				org1 = org0 + vel * dt;
				if (!Veh_DriveSweep (v, org0, yaw0, org1, yaw0))
					org1 = org0;
			}
			else
				org1 = org0;
		}
	}
	else if (!Veh_DriveSweep (v, org0, yaw0, org1, yaw1))
	{
		n = vd_hitnorm;
		vn = vel * n;
		if (vn < 0)
		{
			imp = 0 - vn;
			living = FALSE;
			if (vd_hitent != world && vd_hitent.takedamage)
			{
				if ((vd_hitent.flags & FL_CLIENT) || (vd_hitent.flags & FL_MONSTER))
					living = TRUE;
				Veh_RamHit (v, vd_hitent, imp);
			}
			if (!living && (imp >= 340 || (imp >= 175 && v.veh_state == VEH_STATE_FIRE)))
			{
				// Hollywood runaway crash fireball!
				Veh_Crash (v, imp, vd_hitpos);
				if (v.veh_state != VEH_STATE_WRECK)
				{
					local entity oldself;
					oldself = self;
					self = v;
					Veh_ExplodeNow ();
					self = oldself;
				}
				return;
			}
			if (!living)
			{
				Veh_Crash (v, imp, vd_hitpos);
				if (v.veh_state == VEH_STATE_WRECK)
					return;
				vel = (vel - n * (vn * 1.1)) * 0.45;
			}
			else
				vel = vel * 0.85;
			org1 = org0 + vel * dt;
			if (air_rising)
				org1_z = org0_z + v.veh_vz * dt;
			if (!Veh_DriveSweep (v, org0, yaw0, org1, yaw1))
			{
				if (v.veh_air && Veh_DriveSweep (v, org0, yaw0, org1, yaw0))
					yaw1 = yaw0;
				else if (v.veh_air)
				{
					org1 = org0;
					if (air_rising)
						org1_z = org0_z + v.veh_vz * dt;
				}
				else
				{
					Veh_Park (v);
					return;
				}
			}
		}
		else if (v.veh_pad_spin && Veh_DriveSweep (v, org0, yaw0, org1, yaw0))
			yaw1 = yaw0;
	}
	Veh_GroundSample (v, org1, yaw1);
	z = org1_z;
	if (v.veh_air)
	{
		if (!air_rising)
		{
			grav = cvar ("sv_gravity");
			if (grav <= 10)
				grav = VD_GRAVITY;
			v.veh_vz = v.veh_vz - grav * dt;
			z = z + v.veh_vz * dt;
		}
		if (vd_found && v.veh_vz <= 0 && z <= vd_gh + 1 && time >= v.veh_pad_launch_t)
		{
			imp = 0 - v.veh_vz;
			z = vd_gh;
			v.veh_vz = 0;
			v.veh_air = FALSE;
			if (v.veh_pad_spin)
			{
				Veh_ResetPadStunt (v);
				v.angles_x = 0;
				v.angles_z = 0;
			}
			if (imp > 580)
			{
				Veh_Crash (v, imp * 0.65, org1);
				if (v.veh_state == VEH_STATE_WRECK)
					return;
			}
			else if (imp > 110)
			{
				sound7 (v, CHAN_BODY, "vehicles/tire_thud2.wav", 0.95, ATTN_NORM, 78 + random () * 14);
				if (veh_fx_smoke > 0)
					pointparticles (veh_fx_smoke, org1 + '0 0 6', '0 0 0', 1);
			}
		}
	}
	else if (!vd_found)
		v.veh_air = TRUE;
	else
	{
		d = vd_gh - z;
		if (d < -12)
			v.veh_air = TRUE;
		else
			z = vd_gh;
	}
	if (v.veh_air)
	{
		if (v.veh_pad_spin)
			Veh_StepPadSpin (v, dt, 0, 0);
		else
		{
			local float coast_pitch;
			coast_pitch = bound (-22, v.veh_vz * 0.03, 22);
			v.angles_x = v.angles_x + Veh_AngDelta (coast_pitch, v.angles_x) * min (1, dt * 4);
			v.angles_z = v.angles_z + Veh_AngDelta (0, v.angles_z) * min (1, dt * 3);
		}
	}
	v.angles_y = yaw1;
	org1_z = z;
	if (v.veh_air)
	{
		v.velocity = vel;
		v.velocity_z = v.veh_vz;
	}
	else
		v.velocity = vel * 0.96;
	setorigin (v, org1);
	Veh_DriveBounds (v);
	Veh_SyncPassengers (v);
};

void(entity p, entity v) Veh_TryExit =
{
	local float spd, yaw;
	local vector vel, outd;
	local entity r;

	spd = vlen (v.velocity);
	if (!Veh_ExitSpot (v, p))
	{
		centerprint (p, "No room to open the door.\nPull away from the wall.\n");
		return;
	}
	if (spd > 165 && !Veh_IsKart (v.veh_kind))
	{
		// Hollywood Dive-Bail! Fling driver clear while the unmanned vehicle coasts forward into walls/enemies!
		outd = vd_exit - v.origin;
		outd_z = 0;
		if (vlen (outd) > 1)
			outd = normalize (outd);
		else
			outd = Veh_Lft (v.angles_y);

		p.veh_last_van = v;
		p.veh_bail_safe_t = time + 1.5;
		v.veh_igniter = p;
		vel = v.velocity * 0.45 + outd * 220 + '0 0 215';

		v.veh_driver = world;
		v.veh_drive_mode = FALSE;
		sound (v, VD_MUSIC_CH, "misc/null.wav", 1, ATTN_NORM);
		if (v.veh_cament != world)
		{
			remove (v.veh_cament);
			v.veh_cament = world;
		}
		yaw = p.veh_cam_yaw;
		if (p.veh_camera == 0 && !v.veh_pad_spin)
			yaw = v.angles_y;
		Veh_ReleasePlayer (p, vd_exit, vel, yaw);
		v.veh_coast_until = time + 2.2;
		v.nextthink = time + 0.04;
		if (p.ishuman == 1)
			centerprint (p, strcat ("DIVE BAIL! Ghost-riding the ", Veh_DisplayName (v.veh_kind), "!"));
		r = find (world, classname, "player");
		while (r != world)
		{
			if (r.veh_ride == v && r.ishuman == 1)
				centerprint (r, "DRIVER BAILED!! Press H to jump clear!");
			r = find (r, classname, "player");
		}
		return;
	}
	vel = v.velocity * 0.7;
	vel_z = 0;
	Veh_Leave (v, vd_exit, vel, FALSE);
};

// Automatically seat friends standing inside a parked walk-in Van's cargo bay when the driver takes off!
void(entity v, entity drv) Veh_BoardCargoRiders =
{
	local entity e, nxt;
	local vector rel, fwd, lft;
	local float lx, ly, lz;

	if (v.veh_kind != VEH_VAN)
		return;
	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	e = findradius (v.origin, 180);
	while (e != world)
	{
		nxt = e.chain;
		if (e != drv && e.classname == "player" && e.health > 0 && e.veh_van == world && e.veh_ride == world)
		{
			rel = e.origin - v.origin;
			lx = rel * fwd;
			ly = rel * lft;
			lz = rel_z;
			if (fabs (lx) < 118 && fabs (ly) < 46 && lz > -20 && lz < 105)
				Veh_EnterPassenger (e, v);
		}
		e = nxt;
	}
};

void(entity p, entity v) Veh_Enter =
{
	local entity cam, oldself, de;

	if (p.ky_cam != world)
		KY_CamDetach (p);
	RH_ResetPlayer (p);
	DK_ResetPlayer (p);
	GJ_ResetPlayer (p);
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
	p.milky_wind = 0;
	p.pk_throw_at = 0;
	p.ns_throw_at = 0;

	v.veh_driver = p;
	v.veh_drive_mode = TRUE;
	v.veh_coast_until = 0;
	v.gk_idle_t = 0;		// a spawn kart's idle clock starts again when it is left (Veh_SpawnKartExpired)
	p.veh_van = v;
	p.veh_oldmove = p.movetype;
	p.veh_oldsolid = p.solid;
	p.veh_camera = 1;		// 3rd-person chase view by default on all vehicles (K / impulse 87 toggles cockpit)

	// the van stops being a walk-in room and becomes one moving solid; cargo-bay friends snap into passenger seats!
	Veh_FreeClips (v);
	Veh_BoardCargoRiders (v, p);
	v.velocity = '0 0 0';
	v.veh_steer = 0;
	v.veh_yawrate = 0;
	v.veh_rpm = 0;
	v.veh_boost = 0;
	v.veh_gear = 1;
	v.veh_vz = 0;
	v.veh_air = FALSE;
	v.veh_eng_t = 0;
	v.veh_skid_t = 0;
	v.veh_horn_t = 0;
	v.veh_start_t = time + 0.18;
	v.veh_music_t = 0;
	v.veh_fx_boost_t = 0;
	v.veh_land_dip = 0;
	v.veh_drift_t = 0;
	Veh_ResetPadStunt (v);
	v.gk_nitro = 100;
	v.gk_boosting = FALSE;
	v.gk_boost_t = 0;
	v.gk_boost_pwr = 0;
	v.gk_drift_dir = 0;
	v.gk_drift_charge = 0;
	v.gk_drift_tier = 0;
	v.gk_air_t = 0;
	v.gk_speed = 0;
	v.gk_hud_t = 0;
	v.gk_smoke_t = 0;
	v.gk_hop_prev = TRUE;
	v.gk_m1_prev = FALSE;
	v.gk_m1_hold_t = (p.button0 != 0) ? -1 : 0;
	v.gk_rkt_aim = FALSE;
	v.gk_aim_enter = FALSE;
	v.gk_rkt_charge = 0;
	v.gk_rkt_armed = FALSE;
	p.gk_st_mode = 0;
	p.gk_st_prog = 0;
	p.gk_st_nitro = 0;
	v.movetype = MOVETYPE_NONE;
	v.solid = SOLID_BBOX;
	v.takedamage = DAMAGE_AIM;
	Veh_DriveBounds (v);
	setorigin (v, v.origin);
	Veh_EjectOthers (v, p);

	// the driver: no body, no collision, parked in the seat, seeing through the camera
	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.velocity = '0 0 0';
	p.alpha = 0.01;
	p.effects = p.effects | EF_NODRAW;		// his body is not drawn at all: the camera sits inside his head
	cam = spawn ();
	cam.classname = "veh_cam";
	cam.movetype = MOVETYPE_NONE;
	cam.solid = SOLID_NOT;
	// The engine only sends (and so only lets a client look through) an entity that has a model, so it has one. It must not
	// be a sprite (a camera-facing quad AT the eye: it ignores .scale and washes the whole view with its own colour; the
	// bubble sprite gave a green haze) nor EF_NODRAW (then the entity is not sent and the client looks out from the map
	// origin). An alias model honours .scale, so it is the nail, shrunk to a speck.
	cam.alpha = 0.01;
	cam.scale = 0.01;
	setmodel (cam, "progs/spike.mdl");
	setsize (cam, '0 0 0', '0 0 0');
	setorigin (cam, v.origin + '0 0 63');
	v.veh_cament = cam;
	p.veh_cam_yaw = v.angles_y;
	p.veh_cam_pitch = VD_CAM_PITCH;
	p.veh_cam_dist = max (180, Veh_HalfLen (v.veh_kind) * 2.30);
	if (v.veh_driverent != world)
	{
		remove (v.veh_driverent);
		v.veh_driverent = world;
	}
	if (Veh_IsKart (v.veh_kind))
	{
		de = spawn ();
		de.classname = "gokart_driver";
		de.movetype = MOVETYPE_NONE;
		de.solid = SOLID_NOT;
		de.takedamage = DAMAGE_NO;
		de.angles = v.angles;
		de.frame = v.frame;
		setmodel (de, "progs/gokart_driver.md3");
		setsize (de, '0 0 0', '0 0 0');
		setorigin (de, v.origin);
		v.veh_driverent = de;
		p.veh_cam_pitch = 12;
		p.veh_cam_dist = 142;
	}
	p.veh_cam_look = 0;
	p.clientcamera = cam;
	msg_entity = p;
	WriteByte (MSG_ONE, 5);			// svc_setview
	WriteEntity (MSG_ONE, cam);
	Veh_DriveCamera (p, v, 0.02);

	sound (v, CHAN_VOICE, "vehicles/ignition.wav", 1, ATTN_NORM);
	if (!p.veh_hint_shown && !Veh_IsKart (v.veh_kind))
	{
		p.veh_hint_shown = TRUE;
		centerprint (p, "WASD drive | SPACE drift/brake | FIRE horn | K cam | H exit");
	}
};

// Nearest drivable or rideable vehicle within reach (all 8 vehicle types supported!)
entity(entity p) Veh_SeatOf =
{
	local entity e, best;
	local vector rel;
	local float lx, ly, hl, hw, d, bd;

	best = world;
	bd = 99999;
	e = findradius (p.origin, 280);
	while (e != world)
	{
		// the Spruce school bus drives itself on .ltime waypoints and removes itself at the route end: not enterable
		if (e.veh_kind >= 1 && e.veh_kind <= VEH_GOKART_6 && e.veh_state != VEH_STATE_WRECK && e.classname != "spruce_schoolbus")
		{
			rel = p.origin - e.origin;
			lx = rel * Veh_Fwd (e.angles_y);
			ly = rel * Veh_Lft (e.angles_y);
			if (e.veh_kind == VEH_VAN && e.veh_driver == world && lx > 30 && lx < 72 && ly > -22 && ly < 38 && rel_z > 20 && rel_z < 80)
				return e;
			hl = Veh_HalfLen (e.veh_kind) + 82;
			hw = Veh_HalfWid (e.veh_kind) + 78;
			if (fabs (lx) < hl && fabs (ly) < hw && rel_z > -36 && rel_z < 118)
			{
				if (e.veh_driver == world || Veh_FindFreeSeat (e) > 0)
				{
					d = vlen (rel);
					if (d < bd)
					{
						bd = d;
						best = e;
					}
				}
			}
		}
		e = e.chain;
	}
	return best;
};

// Show contextual prompt beside any drivable or rideable vehicle
void() Veh_NearPrompt =
{
	local entity v;

	if (!veh_has_vans || self.ishuman != 1 || self.health <= 0 || self.veh_van != world || self.veh_ride != world || self.rr_vehicle != world || self.classname != "player")
		return;
	if (time < self.veh_prompt_scan_t)
		return;
	self.veh_prompt_scan_t = time + 0.1;
	v = Veh_SeatOf (self);
	if (v == world)
	{
		if (time > self.veh_prompt_t)
			self.veh_prompt_van = world;
		return;
	}
	if (self.veh_prompt_van == v && time < self.veh_prompt_t)
		return;
	self.veh_prompt_van = v;
	self.veh_prompt_t = time + 12;
	if (v.veh_driver != world)
		centerprint (self, strcat ("Press H to ride & shoot in ", Veh_DisplayName (v.veh_kind)));
	else if (!self.veh_hint_shown)
		centerprint (self, strcat ("Press H to drive ", Veh_DisplayName (v.veh_kind)));
};

// H on foot (called from Vehicles_Impulse): drives if free, or hops into a drive-by passenger seat!
void() Veh_EnterKey =
{
	local entity v;
	local vector pos;

	if (self.health <= 0 || self.veh_van != world || self.veh_ride != world || self.rr_vehicle != world)
		return;
	v = Veh_SeatOf (self);
	if (v == world)
		return;
	if (self.fd_head != world)
	{
		sprint (self, "Recall Rob Dob first (H).\n");
		return;
	}
	if (v.veh_driver != world)
	{
		Veh_EnterPassenger (self, v);
		return;
	}
	if (self.jp_on)
		Jetpack_Off ();
	pos = v.origin + Veh_Fwd (v.angles_y) * (Veh_HalfLen (v.veh_kind) * 0.35) + Veh_Lft (v.angles_y) * 8;
	pos_z = v.origin_z + 40;
	setorigin (self, pos);
	self.velocity = '0 0 0';
	Veh_Enter (self, v);
};

// impulse 89 (sv_cheats test aid): stand in the cab of the nearest van that has no driver, as if you had walked in
void() Veh_TestSeat =
{
	local entity e, best;
	local float d, bd;
	local vector pos;

	if (!cvar ("sv_cheats") || self.veh_van != world)
		return;
	best = world;
	bd = 99999;
	e = findradius (self.origin, 1500);
	while (e != world)
	{
		if (e.veh_kind == VEH_VAN && e.veh_state != VEH_STATE_WRECK && e.veh_driver == world)
		{
			d = vlen (e.origin - self.origin);
			if (d < bd)
			{
				bd = d;
				best = e;
			}
		}
		e = e.chain;
	}
	if (best == world)
	{
		sprint (self, "No free van within reach\n");
		return;
	}
	pos = best.origin + Veh_Fwd (best.angles_y) * 50 + Veh_Lft (best.angles_y) * 8;
	pos_z = best.origin_z + 44;
	setorigin (self, pos);
	self.velocity = '0 0 0';
};

// impulse 90 (sv_cheats test aid): a sedan 700 units ahead (of the van if you are driving, else of you), to ram
void() Veh_TestTarget =
{
	local vector org, fwd;
	local float yaw;

	if (!cvar ("sv_cheats"))
		return;
	if (self.veh_van != world)
	{
		yaw = self.veh_van.angles_y;
		org = self.veh_van.origin;
	}
	else
	{
		yaw = self.v_angle_y;
		org = self.origin;
	}
	fwd = Veh_Fwd (yaw);
	Veh_SpawnDynamic (VEH_SEDAN, org + fwd * 700 + '0 0 8', yaw + 90);
};

// impulse 88: a van right here, already running, nose the way you are facing
void() Veh_SpawnAndEnter =
{
	local entity v;
	local vector fwd;

	if (self.veh_van != world || self.veh_ride != world || self.fd_head != world || self.jb_vehicle != world || self.rr_vehicle != world || self.mmt_tank != world || self.health <= 0)
		return;
	fwd = Veh_Fwd (self.v_angle_y);
	v = Veh_SpawnDynamic (VEH_VAN, self.origin + fwd * 150 + '0 0 8', self.v_angle_y);
	Veh_Enter (self, v);
};

// ---------------------------------------------------------------- the frame

// from W_WeaponFrame, self = the player: TRUE while he drives, which stops him doing anything else
float() Veh_DriveFrame =
{
	local entity v;
	local float dt, thr, brk, steer_in, hb, vf, vl, spd, acc, brake_a, grip, lock, delta, yr, yr_geo, yr_cap;
	local float yaw0, yaw1, imp, vn, power, k, rate, slip, rpm_t, top, lo, gear, z, d;
	local float started, living, ctop, launch, pitch_tgt, roll_tgt, brk_fac, grav, air_pitch_in, air_rising;
	local vector vel, org0, org1, org2, fwd, lft, n, ex_pos;

	v = self.veh_van;
	if (v == world)
		return FALSE;
	// bm_wasfreed: the van was removed under him (its edict may already be reused)
	if (bm_wasfreed (v) || v.veh_driver != self || v.veh_state == VEH_STATE_WRECK || self.health <= 0)
	{
		// the van let go of him without telling him (the watch in the van's think normally catches this first)
		Veh_ReleasePlayer (self, self.origin, '0 0 0', self.angles_y);
		return FALSE;
	}

	dt = frametime;
	if (dt < 0.001)
		dt = 0.001;
	if (dt > 0.05)
		dt = 0.05;

	// ---- keys that are not the pedals
	if (self.impulse == 86)
	{
		self.impulse = 0;
		Veh_TryExit (self, v);
		return TRUE;
	}
	if (self.impulse == 87)
		self.veh_camera = 1 - self.veh_camera;
	if (self.impulse == 90)
		Veh_TestTarget ();		// sv_cheats test aid
	self.impulse = 0;
	self.velocity = '0 0 0';
	self.flags = self.flags - (self.flags & FL_ONGROUND);		// so the jump key (the handbrake) is not a jump

	if (Veh_IsKart (v.veh_kind))
		return GK_DriveFrame (self, v, dt);

	// ---- the driver's controls
	started = (time >= v.veh_start_t);
	thr = bound (0, self.movement_x / 160, 1);
	brk = bound (0, 0 - self.movement_x / 160, 1);
	steer_in = bound (-1, self.movement_y / 160, 1);			// + = D = right
	hb = FALSE;
	if (self.button2)
		hb = TRUE;
	if (!started)
	{
		thr = 0;
		brk = 0;
	}
	if (started && (v.veh_kind == VEH_VAN || v.veh_kind == VEH_SCHOOLBUS) && time >= v.veh_music_t)
	{
		v.veh_music_t = time + VD_MUSIC_LEN;
		sound (v, VD_MUSIC_CH, "vehicles/lanvan.wav", 0.5, ATTN_NORM);
		dprint ("lanvan: chant starts\n");
	}
	if (self.button0 && time >= v.veh_horn_t && started)
	{
		v.veh_horn_t = time + 1;
		if (v.veh_kind == VEH_TUKTUK)
			sound (v, CHAN_WEAPON, "vehicles/horn_tuktuk.wav", 1, ATTN_NORM);
		else
			sound (v, CHAN_WEAPON, "vehicles/horn.wav", 1, ATTN_NORM);
	}

	// the wheel eases toward the key: snappy turn-in, quick self-centering, fastest counter-steer
	rate = 6.8;
	if (steer_in == 0)
		rate = 10.5;
	else if (steer_in * v.veh_steer < 0)
		rate = 14.0;
	v.veh_steer = Veh_Approach (v.veh_steer, steer_in, rate * dt);

	// ---- the van's own frame
	yaw0 = v.angles_y;
	fwd = Veh_Fwd (yaw0);
	lft = Veh_Lft (yaw0);
	vel = v.velocity;
	vel_z = 0;
	vf = vel * fwd;
	vl = vel * lft;
	spd = fabs (vf);
	slip = fabs (vl);

	if (Veh_CheckPads (v, self))
	{
		yaw0 = v.angles_y;
		fwd = Veh_Fwd (yaw0);
		lft = Veh_Lft (yaw0);
		vel = v.velocity;
		vel_z = 0;
		vf = vel * fwd;
		vl = vel * lft;
		spd = fabs (vf);
		slip = fabs (vl);
	}

	Veh_GroundSample (v, v.origin, yaw0);

	power = 1;
	if (v.veh_state == VEH_STATE_FIRE)
		power = 0.7;						// burning: it still goes, badly
	if (pointcontents (v.origin + '0 0 24') <= CONTENT_WATER)
	{
		power = power * 0.5;
		vf = vf * (1 - 1.6 * dt);
		vl = vl * (1 - 1.6 * dt);
	}

	// ---- turbo spool & drift-exit mini-turbo: holding W builds speed fast; powersliding holds boost & kicks on exit
	if (thr > 0 && brk == 0 && !hb && !v.veh_air && vf > 60)
		v.veh_boost = min (1, v.veh_boost + dt / VD_BOOST_TIME);
	else if (hb && thr > 0 && !v.veh_air)
	{
		if (slip > 70 || spd > 180)
			v.veh_drift_t = min (2.0, v.veh_drift_t + dt);
	}
	else if (brk > 0 || hb)
		v.veh_boost = max (0, v.veh_boost - dt * 0.6);
	else if (thr == 0)
		v.veh_boost = max (0, v.veh_boost - dt / 18);

	if (!hb && v.veh_drift_t > 0)
	{
		if (!v.veh_air && v.veh_drift_t > 0.25 && vf > 120)
		{
			v.veh_boost = min (1, v.veh_boost + 0.35 * v.veh_drift_t);
			vf = vf + min (140, slip * 0.25);
			if (veh_fx_boost > 0)
			{
				ex_pos = v.origin - fwd * (Veh_HalfLen (v.veh_kind) - 2) + lft * (Veh_HalfWid (v.veh_kind) * 0.62) + '0 0 10';
				pointparticles (veh_fx_boost, ex_pos, fwd * -120, 1);
			}
		}
		v.veh_drift_t = 0;
	}
	else if (v.veh_air)
		v.veh_drift_t = 0;

	ctop = Veh_TopSpeed (v.veh_kind) * (1 + VD_BOOST_TOP * v.veh_boost);

	// ---- pedals. Forward key: drive, or brake if still rolling backward. Back key: brake, or reverse once stopped
	acc = 0;
	brake_a = 0;
	air_pitch_in = thr - brk;
	if (v.veh_air)
	{
		thr = 0;
		brk = 0;
	}
	if (thr > 0 && brk > 0)
	{
		if (spd > 12)
			brake_a = VD_BRAKE;
	}
	else if (thr > 0)
	{
		if (vf < -12)
			brake_a = VD_BRAKE * thr;
		else
		{
			k = bound (0, vf / ctop, 1);
			launch = 1 + 0.45 * (1 - min (1, spd / 260));
			acc = thr * Veh_BaseAccel (v.veh_kind) * launch * (1 + VD_BOOST_ACC * v.veh_boost) * power * (1 - pow (k, 2.3));
		}
	}
	else if (brk > 0)
	{
		if (vf > 12)
			brake_a = VD_BRAKE * brk;
		else
		{
			k = bound (0, 0 - vf / VD_REV, 1);
			acc = 0 - brk * VD_REV_ACCEL * power * (1 - pow (k, 1.5));
		}
	}
	else if (!v.veh_air)
		brake_a = VD_COAST + spd * 0.09;		// both pedals up: rolling resistance + engine braking
	if (hb && !v.veh_air)
	{
		if (thr > 0)
			brake_a = brake_a + 110;			// throttle + SPACE = powerslide (keeps momentum!)
		else
			brake_a = brake_a + 360;			// SPACE alone = handbrake stop
	}

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
		vf = vf - 400 * vd_slope_f * dt;		// uphill slows, downhill speeds up
		vl = vl - 400 * vd_slope_l * dt;
	}

	// ---- tyres: they take out sideways speed, up to what they can hold (less while braking hard, or with the rears locked)
	grip = Veh_BaseGrip (v.veh_kind);
	if (hb)
		grip = VD_GRIP_HB;
	grip = grip * (1 - 0.40 * bound (0, brake_a / VD_BRAKE, 1));
	slip = fabs (vl);
	if (!v.veh_air)
	{
		k = grip * dt;
		vl = vl + bound (0 - k, 0 - vl, k);
	}

	// ---- steering: front wheel angle (less lock the faster you go) -> bicycle-model turn rate, capped by the tyres
	spd = fabs (vf);
	lock = VD_LOCK - (VD_LOCK - VD_LOCK_HI) * bound (0, spd / ctop, 1);
	delta = v.veh_steer * lock;
	yr_geo = 0 - vf * Veh_Tan (delta) / Veh_Wheelbase (v.veh_kind) * 57.2958;
	yr_cap = grip / max (spd, 30) * 57.2958;
	yr = bound (0 - yr_cap, yr_geo, yr_cap);
	if (hb && spd > 130)
	{
		yr = bound (-165, yr_geo * 1.55, 165);	// controllable oversteer powerslide without spinning out
		if (fabs (vl) > spd * 0.72 && yr * vl < 0)
			yr = yr * 0.45;
	}
	if (v.veh_air)
	{
		if (v.veh_pad_spin)
			yr = v.veh_spin_yaw;
		else
			yr = v.veh_yawrate * 0.992;		// in the air nothing steers
	}
	if (v.veh_air && v.veh_pad_spin)
	{
		v.veh_yawrate = v.veh_spin_yaw;
		yaw1 = Veh_NormYaw (yaw0 + v.veh_spin_yaw * dt);
	}
	else
	{
		v.veh_yawrate = v.veh_yawrate + (yr - v.veh_yawrate) * min (1, dt * 8);
		yaw1 = Veh_NormYaw (yaw0 + v.veh_yawrate * dt);
	}

	vel = fwd * vf + lft * vl;

	// ---- move: sweep the footprint; if it is blocked, slide along the wall, and what was lost is the crash
	org0 = v.origin;
	org1 = org0;
	org1_x = org0_x + vel_x * dt;
	org1_y = org0_y + vel_y * dt;
	air_rising = (v.veh_air && v.veh_vz > 0);
	if (air_rising)
		org1_z = Veh_StepAirRise (v, org0, dt);
	if (!Veh_DriveSweep (v, org0, yaw0, org1, yaw1))
	{
		n = vd_hitnorm;
		vn = vel * n;
		if (autocvar_veh_debug && time >= vd_hit_dbg_t)
		{
			vd_hit_dbg_t = time + 0.5;
			dprint ("VEH blocked by ");
			dprint (vd_hitent.classname);
			dprint (" at ");
			dprint (vtos (vd_hitpos));
			dprint (" normal ");
			dprint (vtos (n));
			dprint (" ent mins/maxs ");
			dprint (vtos (vd_hitent.absmin));
			dprint (vtos (vd_hitent.absmax));
			dprint ("\n");
		}
		if (vn < 0)
		{
			imp = 0 - vn;
			living = FALSE;
			if (vd_hitent != world && vd_hitent.takedamage)
			{
				if ((vd_hitent.flags & FL_CLIENT) || (vd_hitent.flags & FL_MONSTER))
					living = TRUE;
				Veh_RamHit (v, vd_hitent, imp);
			}
			if (!living && (imp >= 1150 || (imp >= 520 && v.veh_state == VEH_STATE_FIRE)))
			{
				// Catastrophic high-speed wall crash fireball!
				Veh_Crash (v, imp, vd_hitpos);
				if (v.veh_state != VEH_STATE_WRECK)
				{
					local entity oldself;
					v.veh_igniter = self;
					oldself = self;
					self = v;
					Veh_ExplodeNow ();
					self = oldself;
				}
				return TRUE;
			}
			if (!living && imp > 180)
				Veh_Crash (v, imp, vd_hitpos);
			if (self.veh_van != v)
				return TRUE;			// the crash blew the van up
			if (living)
				vel = vel * 0.94;
			else if (imp >= 200)
			{
				v.veh_boost = v.veh_boost * (1 - bound (0, (imp - 160) / 450, 1));
				vel = vel - n * (vn * 1.15);		// off the wall with a little bounce
				vel = vel * (1 - 0.5 * dt);
			}
			else
			{
				v.veh_boost = v.veh_boost * (1 - bound (0, (imp - 120) / 400, 0.45));
				vel = vel - n * vn;					// glancing curb/wall scrape slides cleanly
				vel = vel * (1 - 0.2 * dt);
			}
		}
		org2 = org0;
		org2_x = org0_x + vel_x * dt;
		org2_y = org0_y + vel_y * dt;
		org2_z = org1_z;
		if (Veh_DriveSweep (v, org0, yaw0, org2, yaw1))
			org1 = org2;
		else if (v.veh_pad_spin && Veh_DriveSweep (v, org0, yaw0, org2, yaw0))
		{
			org1 = org2;
			yaw1 = yaw0;
		}
		else if (yaw1 != yaw0 && Veh_DriveSweep (v, org0, yaw0, org0_x * '1 0 0' + org0_y * '0 1 0' + org1_z * '0 0 1', yaw1))
		{
			org1 = org0_x * '1 0 0' + org0_y * '0 1 0' + org1_z * '0 0 1';
			vel = vel * 0.7;
		}
		else
		{
			local float jam_spd;
			jam_spd = vlen (vel);
			if (jam_spd > 280)
			{
				Veh_Crash (v, jam_spd * 0.85, v.origin + '0 0 28');
				if (self.veh_van != v)
					return TRUE;
				if (jam_spd >= 1000 || (jam_spd >= 480 && v.veh_state == VEH_STATE_FIRE))
				{
					local entity oldself3;
					v.veh_igniter = self;
					oldself3 = self;
					self = v;
					Veh_ExplodeNow ();
					self = oldself3;
					return TRUE;
				}
			}
			org1 = org0_x * '1 0 0' + org0_y * '0 1 0' + org1_z * '0 0 1';
			yaw1 = yaw0;
			vel = vel * 0.65;
			if (!v.veh_pad_spin)
				v.veh_yawrate = 0;
		}
	}

	// ---- up and down: ride the road, or fly
	Veh_GroundSample (v, org1, yaw1);
	z = org1_z;
	if (v.veh_air)
	{
		if (!air_rising)
		{
			grav = cvar ("sv_gravity");
			if (grav <= 10)
				grav = VD_GRAVITY;
			v.veh_vz = v.veh_vz - grav * dt;
			z = z + v.veh_vz * dt;
		}
		if (vd_found && v.veh_vz <= 0 && z <= vd_gh + 1 && time >= v.veh_pad_launch_t)
		{
			imp = 0 - v.veh_vz;
			z = vd_gh;
			v.veh_vz = 0;
			v.veh_air = FALSE;
			if (v.veh_pad_spin)
			{
				Veh_ResetPadStunt (v);
				v.angles_x = Veh_AngDelta (v.angles_x, 0) * 0.35;
				v.angles_z = Veh_AngDelta (v.angles_z, 0) * 0.35;
				v.veh_yawrate = 0;
			}
			if (imp > 580)
			{
				Veh_Crash (v, imp * 0.65, org1);		// only massive drops hurt
				if (v.veh_state != VEH_STATE_WRECK && (imp > 1550 || (imp > 850 && v.veh_state == VEH_STATE_FIRE)))
				{
					local entity oldself2;
					v.veh_igniter = self;
					oldself2 = self;
					self = v;
					Veh_ExplodeNow ();
					self = oldself2;
					return TRUE;
				}
			}
			else if (imp > 110)
			{
				sound7 (v, CHAN_BODY, "vehicles/tire_thud2.wav", 0.95, ATTN_NORM, 78 + random () * 14);
				v.veh_land_dip = 0 - min (7, imp * 0.016);
				if (veh_fx_smoke > 0)
					pointparticles (veh_fx_smoke, org1 + '0 0 6', '0 0 0', 1);
			}
			if (self.veh_van != v)
				return TRUE;
		}
	}
	else if (!vd_found)
	{
		v.veh_air = TRUE;
	}
	else
	{
		d = vd_gh - z;
		if (d < -12)
			v.veh_air = TRUE;					// drove off an edge: launch with the road's last rise rate
		else
		{
			if (d > 0)
				z = z + d * min (1, dt * 20);	// steps and kerbs are climbed, not teleported over
			else
				z = vd_gh;
			v.veh_vz = bound (-300, v.veh_vz * 0.6 + ((z - org1_z) / dt) * 0.4, 400);
		}
	}
	org1_z = z;
	v.veh_land_dip = Veh_Approach (v.veh_land_dip, 0, dt * 18);
	if (v.veh_air)
	{
		if (v.veh_pad_spin)
			Veh_StepPadSpin (v, dt, steer_in, air_pitch_in);
		else
		{
			pitch_tgt = bound (-22, v.veh_vz * 0.03, 22);
			v.angles_x = v.angles_x + Veh_AngDelta (pitch_tgt, v.angles_x) * min (1, dt * 4);
			v.angles_z = v.angles_z + Veh_AngDelta (0, v.angles_z) * min (1, dt * 3);
		}
	}
	else if (vd_found)
	{
		brk_fac = 0;
		if (vf > 20)
			brk_fac = bound (0, brake_a / VD_BRAKE, 1);
		pitch_tgt = vd_pitch + 3.5 * thr * (1 + 0.6 * v.veh_boost) * (1 - bound (0, vf / ctop, 1) * 0.4) - 4.5 * brk_fac + v.veh_land_dip;
		v.angles_x = v.angles_x + Veh_AngDelta (pitch_tgt, v.angles_x) * min (1, dt * 12);
		roll_tgt = bound (-8, v.veh_yawrate * bound (0, spd / 500, 1) * 0.065 + vd_slope_l * 35, 8);
		v.angles_z = v.angles_z + Veh_AngDelta (roll_tgt, v.angles_z) * min (1, dt * 12);
	}

	v.angles_y = yaw1;
	v.velocity = vel;
	if (v.veh_air)
		v.velocity_z = v.veh_vz;
	setorigin (v, org1);
	Veh_DriveBounds (v);

	// Out of the world: setorigin movement never touches trigger_hurt/teleporters, so blow it up cleanly if launched into sky/void
	if (v.veh_chain_t == 0 && ((world.maxs_z > world.mins_z && v.origin_z < world.mins_z - 64) || pointcontents (v.origin + '0 0 8') == CONTENT_SKY || pointcontents (v.origin - '0 0 4') == CONTENT_SKY))
	{
		v.health = 1;
		v.takedamage = DAMAGE_NO;
		v.veh_chain_t = time;
		v.think = Veh_Think;
		v.nextthink = time;
	}

	// ---- engine revs: 5 gears picked by road speed; the revs fall at each upshift. Standing still the throttle revs it
	spd = fabs (vf);
	gear = 4;
	top = max (860, ctop * 1.03);
	lo = 840;
	if (spd < 180)
	{
		gear = 0;
		top = 180;
		lo = 0;
	}
	else if (spd < 380)
	{
		gear = 1;
		top = 380;
		lo = 180;
	}
	else if (spd < 600)
	{
		gear = 2;
		top = 600;
		lo = 380;
	}
	else if (spd < 840)
	{
		gear = 3;
		top = 840;
		lo = 600;
	}
	if (gear + 1 > v.veh_gear)
		v.veh_shift_t = time + 0.22;				// upshift: the revs dip
	v.veh_gear = gear + 1;
	rpm_t = 0.22 + 0.78 * bound (0, (spd - lo * 0.62) / (top - lo * 0.62), 1);
	if (vf < -5)
		rpm_t = 0.2 + 0.4 * bound (0, spd / VD_REV, 1);
	if (spd < 60)
		rpm_t = max (0.12 + 0.7 * max (thr, brk), 0.12);		// clutch slipping: revs follow the pedal
	if (!started)
		rpm_t = 0;
	if (v.veh_air)
	{
		if (v.veh_pad_spin)
			rpm_t = 0.86 + 0.14 * random ();
		else
			rpm_t = 0.35 + 0.65 * thr;
	}
	if (rpm_t > v.veh_rpm)
		v.veh_rpm = min (rpm_t, v.veh_rpm + 3.2 * dt);
	else
		v.veh_rpm = max (rpm_t, v.veh_rpm - 2.2 * dt);
	if (started)
		Veh_EngineSound (v, (v.veh_air && v.veh_pad_spin) ? 1 : thr);

	// ---- turbo exhaust flames / sparks during hard launch & boost
	if (started && thr > 0 && !v.veh_air && veh_fx_boost > 0 && (v.veh_boost > 0.35 || (vf < 240 && thr > 0.8)) && time >= v.veh_fx_boost_t)
	{
		v.veh_fx_boost_t = time + 0.04;
		ex_pos = v.origin - fwd * (Veh_HalfLen (v.veh_kind) - 2) + lft * (Veh_HalfWid (v.veh_kind) * 0.62) + '0 0 10';
		pointparticles (veh_fx_boost, ex_pos, fwd * -90, 1);
	}

	// ---- tyre noise & drift smoke: sideways sliding, a hard stop from speed, or the handbrake at speed
	if (!v.veh_air)
	{
		if (brake_a > 500 && spd > 280)
			slip = max (slip, 150);
		if (hb && spd > 120)
			slip = max (slip, 190);
		if (slip > 85)
			Veh_SkidSound (v, slip);
	}

	if (autocvar_veh_debug && time >= vd_dbg_t)
	{
		vd_dbg_t = time + 0.25;
		dprint ("VEH t=");
		dprint (ftos (floor (time * 100) / 100));
		dprint (" pos=");
		dprint (vtos (v.origin));
		dprint (" yaw=");
		dprint (ftos (floor (v.angles_y)));
		dprint (" pitch=");
		dprint (ftos (floor (v.angles_x)));
		dprint (" fwd=");
		dprint (ftos (floor (vf)));
		dprint (" lat=");
		dprint (ftos (floor (vl)));
		dprint (" steer=");
		dprint (ftos (floor (v.veh_steer * 100)));
		dprint (" rpm=");
		dprint (ftos (floor (v.veh_rpm * 100)));
		dprint (" gear=");
		dprint (ftos (v.veh_gear));
		dprint (" air=");
		dprint (ftos (v.veh_air));
		dprint (" cam=");
		dprint (ftos (self.veh_camera));
		dprint (" view=");
		dprint (vtos (self.v_angle));
		dprint (" camorg=");
		dprint (vtos (v.veh_cament.origin));
		dprint (" p.org=");
		dprint (vtos (self.origin));
		dprint ("\n");
	}

	// ---- the driver rides in the seat; lockstep-sync any party passengers; the view is the camera
	setorigin (self, v.origin + fwd * (Veh_HalfLen (v.veh_kind) * 0.30) + lft * 14 + '0 0 40');
	Veh_SyncPassengers (v);
	Veh_DriveCamera (self, v, dt);
	return TRUE;
};
