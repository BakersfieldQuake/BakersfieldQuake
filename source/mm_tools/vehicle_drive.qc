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

float	VD_TOP			= 640;		// forward top speed, units/second
float	VD_BOOST_TOP	= 0.45;		// holding the throttle builds speed: up to this much extra top speed (640 -> 928) ...
float	VD_BOOST_ACC	= 0.6;		// ... and this much extra acceleration, after VD_BOOST_TIME seconds flat out
float	VD_BOOST_TIME	= 14;
float	VD_REV			= 190;		// reverse top speed
float	VD_ACCEL		= 205;		// acceleration from a standstill (falls off toward top speed)
float	VD_REV_ACCEL	= 150;
float	VD_BRAKE		= 640;		// footbrake deceleration
float	VD_COAST		= 55;		// rolling resistance with both pedals up (plus engine braking, below)
float	VD_GRIP			= 720;		// sideways acceleration the tyres hold
float	VD_GRIP_HB		= 170;		// ... with the handbrake on
float	VD_WHEELBASE	= 148;
float	VD_LOCK			= 34;		// degrees of front wheel lock at a standstill
float	VD_LOCK_HI		= 9;		// ... at top speed
float	VD_GRAVITY		= 800;
float	VD_HEIGHT		= 0.5;		// the van's origin sits this far above the road

float	VD_EYE_X		= 42;		// the driver's eye, van-local (the model's cockpit anchor)
float	VD_EYE_Y		= 19.8;
float	VD_EYE_Z		= 63.5;

float	VD_CAM_DIST		= 205;
float	VD_CAM_PITCH	= 12;
float	VD_CAM_UP		= 62;

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

// ---------------------------------------------------------------- the footprint: 20 hulls swept around the real body

// body-space (x forward, y left) spots round the van's edge where a 20 x 20 hull is swept, placed so the hull's outer
// edge lies on the body's outline (nose 112.5, tail -114, sides +-43): 4 across the nose, 4 across the tail, 6 down each side
vector(float i) Veh_ProbeOfs =
{
	local float k;

	if (i < 4)
	{
		k = i;
		return '102 0 0' + '0 1 0' * (-33 + 22 * k);
	}
	if (i < 8)
	{
		k = i - 4;
		return '-104 0 0' + '0 1 0' * (-33 + 22 * k);
	}
	if (i < 14)
	{
		k = i - 8;
		return '0 33 0' + '1 0 0' * (-80 + 32 * k);
	}
	k = i - 14;
	return '0 -33 0' + '1 0 0' * (-80 + 32 * k);
};

/*
Sweep every footprint hull from the van at (org0, yaw0) to the van at (org1, yaw1). TRUE if the way is clear;
otherwise vd_hitnorm (flat, unit), vd_hitpos and vd_hitent describe the first thing hit.
Hulls that start inside something are ignored (the van can always drive back out of a bad spot), and so are ramps:
a surface that faces up (normal z >= 0.7) is ground for the wheels to follow, not a wall.
*/
float(entity v, vector org0, float yaw0, vector org1, float yaw1) Veh_DriveSweep =
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
		o = Veh_ProbeOfs (i);
		p0 = org0;
		p0_x = org0_x + c0 * o_x - s0 * o_y;
		p0_y = org0_y + s0 * o_x + c0 * o_y;
		p0_z = org0_z + 20;
		p1 = org1;
		p1_x = org1_x + c1 * o_x - s1 * o_y;
		p1_y = org1_y + s1 * o_x + c1 * o_y;
		p1_z = org1_z + 20;
		tracebox (p0, '-10 -10 0', '10 10 76', p1, FALSE, v);
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

/*
Trace the four wheel contact points (front pair x = 80, rear pair x = -68, track 77). Sets:
  vd_found   how many wheels found road
  vd_gh      the height the van's origin should have (mean of the four; a wheel with no road counts as hanging 24 low)
  vd_pitch   degrees the nose is up, from the front pair against the rear pair
  vd_slope_f / _l   sine of the road's slope along / across the van (+ = uphill ahead / to the left)
*/
void(entity v, vector org, float yaw) Veh_GroundSample =
{
	local float i, wx, wy, c, s, sum, have0, tf, tl, hf, hr, hl, hrt;
	local float h0, h1, h2, h3, hh, mask;
	local vector p, q;

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
			wx = 80;
		else
			wx = -68;
		if (i == 0 || i == 2)
			wy = 38.5;
		else
			wy = -38.5;
		p = org;
		p_x = org_x + c * wx - s * wy;
		p_y = org_y + s * wx + c * wy;
		p_z = org_z + 24;
		q = p;
		q_z = org_z - 48;
		traceline (p, q, 3, v);		// 3 = world only: parked vehicles' boxes and bodies are not road
		if (!trace_startsolid && trace_fraction < 1 && trace_plane_normal_z > 0.5)
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
	vd_pitch = Veh_RiseAngle (hf - hr, 148);
	tf = (hf - hr) / 148;
	tl = (hl - hrt) / 77;
	vd_slope_f = tf / vlen ('1 0 0' + '0 1 0' * tf);		// sine of the slope
	vd_slope_l = tl / vlen ('1 0 0' + '0 1 0' * tl);
};

// ---------------------------------------------------------------- solid box while driven / parked

// While driven the van is one box that fits INSIDE its real footprint at any heading (a box sticking out past the
// body would trap anyone standing beside it). It only has to take bullets: the van moves itself with the sweeps.
void(entity v) Veh_DriveBounds =
{
	local float c, s, hx, hy, a1, a2, k;
	local vector bmin, bmax;

	c = fabs (Veh_Cos (v.angles_y));
	s = fabs (Veh_Sin (v.angles_y));
	hx = c * 108 + s * 42;			// the box round the rotated 216 x 84 body...
	hy = s * 108 + c * 42;
	a1 = hx * c + hy * s;
	a2 = hx * s + hy * c;
	k = 1;
	if (108 / a1 < k)
		k = 108 / a1;
	if (42 / a2 < k)
		k = 42 / a2;				// ...shrunk until its corners sit inside the body
	bmin = '0 0 0';
	bmax = '0 0 0';
	bmin_x = 0 - hx * k;
	bmin_y = 0 - hy * k;
	bmax_x = hx * k;
	bmax_y = hy * k;
	bmax_z = 89;
	setsize (v, bmin, bmax);
};

// everyone (but the driver) standing inside the van's footprint gets thrown out the back
void(entity v, entity keep) Veh_EjectOthers =
{
	local entity e, nxt;
	local vector rel, fwd, lft, spot;
	local float lx, ly, lz, i;

	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	e = findradius (v.origin, 220);
	while (e != world)
	{
		nxt = e.chain;
		if (e != keep && e != v && e.health > 0 && (e.classname == "player" || (e.flags & FL_MONSTER)))
		{
			rel = e.origin - v.origin;
			lx = rel * fwd;
			ly = rel * lft;
			lz = rel_z;
			if (fabs (lx) < 126 && fabs (ly) < 52 && lz > -40 && lz < 110)
			{
				i = 0;
				while (i < 4)
				{
					if (i == 0)
						spot = v.origin - fwd * 160 + lft * (crandom () * 24);
					else if (i == 1)
						spot = v.origin + lft * 76 + fwd * (crandom () * 50);
					else if (i == 2)
						spot = v.origin - lft * 76 + fwd * (crandom () * 50);
					else
						spot = v.origin + fwd * 146;
					spot_z = v.origin_z + 26;
					if (Veh_FreeSpot (e, spot))
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

// the van has stopped being driven: square to the world it gets its walk-in interior back, otherwise it is a plain box
void(entity v) Veh_Park =
{
	local float snap, d;

	if (v.veh_air)
	{
		// parked in mid-air (he got out, died or dropped during a jump): put it down first, else it hung in the sky for
		// good, too high for anyone to get back in
		tracebox (v.origin, v.mins, v.maxs, v.origin - '0 0 4096', TRUE, v);
		if (!trace_startsolid && !trace_allsolid && trace_fraction < 1)
			setorigin (v, trace_endpos + '0 0 0.5');
	}
	v.velocity = '0 0 0';
	v.veh_steer = 0;
	v.veh_yawrate = 0;
	v.veh_rpm = 0;
	v.veh_air = FALSE;
	v.angles_x = 0;
	v.angles_z = 0;
	v.movetype = MOVETYPE_NONE;
	v.solid = SOLID_BBOX;
	snap = floor ((v.angles_y + 45) / 90) * 90;
	d = Veh_AngDelta (v.angles_y, snap);
	if (fabs (d) <= 7)
	{
		v.angles_y = Veh_NormYaw (snap);
		setorigin (v, v.origin);
		Veh_Van_InitCollision (v);
	}
	else
	{
		Veh_SetRotatedBounds (v, VEH_VAN, FALSE);
		setorigin (v, v.origin);
	}
	Veh_EjectOthers (v, world);
};

// ---------------------------------------------------------------- hitting things

// the van ran into something that can be hurt (a person, a monster, another vehicle's body)
void(entity v, entity hit, float imp) Veh_RamHit =
{
	local entity driver;
	local float dmg;
	local vector dir;

	if (imp < 90 || time < hit.veh_hit_t)
		return;
	driver = v.veh_driver;
	dir = v.velocity;
	dir_z = 0;
	dir = normalize (dir);
	dmg = (imp - 60) * 0.3;			// ~175 at top speed: kills most things on foot
	hit.veh_hit_t = time + 0.45;
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
	if ((hit.flags & FL_CLIENT) || (hit.flags & FL_MONSTER))
	{
		hit.velocity = hit.velocity + dir * (imp * 0.85) + '0 0 170';
		hit.flags = hit.flags - (hit.flags & FL_ONGROUND);
		sound7 (hit, CHAN_BODY, "vehicles/tire_thud1.wav", 1, ATTN_NORM, 70 + random () * 12);
	}
	veh_runover = TRUE;
	T_Damage (hit, v, driver, dmg);
	veh_runover = FALSE;
	if ((hit.flags & FL_CLIENT) && dmg > 20)
		T_Damage (v, world, world, dmg * 0.2);		// ramming people is not free: about 8 kills wrecks the van (280 hp)
};

// the van hit something that does not move: sparks, a clang, damage to the van, and a jolt for the driver
void(entity v, float imp, vector at) Veh_Crash =
{
	local entity driver;
	local float dmg;

	if (time < v.veh_crash_t)
		return;
	v.veh_crash_t = time + 0.3;
	if (autocvar_veh_debug)
	{
		dprint ("VEH crash imp=");
		dprint (ftos (floor (imp)));
		dprint (" van hp=");
		dprint (ftos (v.health));
		dprint ("\n");
	}
	pointparticles (veh_fx_sparks, at, '0 0 0', 1);
	if (random () < 0.5)
		sound7 (v, CHAN_BODY, "vehicles/clang1.wav", bound (0.5, imp / 500, 1), ATTN_NORM, 78 + random () * 16);
	else
		sound7 (v, CHAN_BODY, "vehicles/clang2.wav", bound (0.5, imp / 500, 1), ATTN_NORM, 78 + random () * 16);
	driver = v.veh_driver;
	if (imp > 420 && driver != world)
		T_Damage (driver, world, world, (imp - 420) * 0.12);		// head-on at top speed costs the driver ~26
	dmg = (imp - 210) * 0.16;										// ... and the van ~69 of its 280
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
	local float k;

	k = 0;
	if (self.veh_state == VEH_STATE_FIRE)
		k = 1;
	if (self.veh_state != VEH_STATE_WRECK && other.veh_van == self && other.veh_camera == 0)
		k = k + 2;
	self.skin = k;
	return TRUE;			// FALSE would mean: do not send the van to this client
};

// ---------------------------------------------------------------- the driver's eyes

void(entity p, entity v, float dt) Veh_DriveCamera =
{
	local entity cam;
	local vector fwd, lft, pos, tgt, ang;
	local float yaw, pitch, d, spd, lead;

	cam = v.veh_cament;
	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	spd = vlen (v.velocity);

	if (p.veh_camera == 0)
	{
		// cockpit: the driver's eye (42, 19.8, 63.5), looking a little into the turn
		pos = v.origin + fwd * VD_EYE_X + lft * VD_EYE_Y + '0 0 1' * VD_EYE_Z;
		lead = 0 - v.veh_steer * 9 * bound (0, spd / 220, 1);		// steering right (+) looks right (yaw falls)
		p.veh_cam_look = p.veh_cam_look + (lead - p.veh_cam_look) * min (1, dt * 5);
		yaw = Veh_NormYaw (v.angles_y + p.veh_cam_look);
		pitch = 0 - v.angles_x;
		p.veh_cam_yaw = v.angles_y;
	}
	else
	{
		// chase: behind and above, swinging round after the van rather than welded to it
		d = Veh_AngDelta (v.angles_y, p.veh_cam_yaw);
		p.veh_cam_yaw = Veh_NormYaw (p.veh_cam_yaw + d * min (1, dt * 5));
		yaw = p.veh_cam_yaw;
		pitch = VD_CAM_PITCH;
		tgt = v.origin + '0 0 1' * VD_CAM_UP;
		ang = '0 0 0';
		ang_x = pitch;
		ang_y = yaw;
		makevectors (ang);
		pos = tgt - v_forward * VD_CAM_DIST;
		traceline (tgt, pos, 3, v);
		pos = trace_endpos;
		if (trace_fraction < 1)
			pos = pos + trace_plane_normal * 8;
	}
	setorigin (cam, pos);
	cam.angles = '0 0 0';
	cam.angles_y = yaw;
	// the view itself is the server's: set absolutely every frame, so how long the round trip takes cannot slow it
	p.angles = '0 0 0';
	p.angles_x = pitch;
	p.angles_y = yaw;
	p.fixangle = TRUE;
};

// ---------------------------------------------------------------- sound

// the engine: overlapping windowed grains whose pitch follows the revs (see make_vehicle_drive_sounds.py)
void(entity v, float thr) Veh_EngineSound =
{
	local float pitch, vol;

	if (time < v.veh_eng_t)
		return;
	pitch = 62 + 150 * v.veh_rpm;
	if (time < v.veh_shift_t)
		pitch = pitch * 0.86;
	vol = 0.30 + 0.20 * thr;
	sound7 (v, VD_SOUND_CH, "vehicles/engine_grain.wav", vol, ATTN_NORM, pitch);
	if (v.veh_eng_t < time - 0.2)
		v.veh_eng_t = time;
	v.veh_eng_t = v.veh_eng_t + 16 / pitch;			// half a grain: 0.16 s at pitch 100
};

void(entity v, float slip) Veh_SkidSound =
{
	local vector rear;
	local float vol;

	if (time < v.veh_skid_t)
		return;
	vol = bound (0.3, (slip - 60) / 260, 1);
	sound7 (v, VD_SOUND_CH, "vehicles/tire_squeal.wav", vol * 0.8, ATTN_NORM, 92 + slip * 0.03);
	v.veh_skid_t = time + 0.3;
	if (time >= v.veh_smoke_t2)
	{
		v.veh_smoke_t2 = time + 0.1;
		rear = v.origin - Veh_Fwd (v.angles_y) * 68 + Veh_Lft (v.angles_y) * (crandom () * 38);
		rear_z = v.origin_z + 4;
		pointparticles (veh_fx_smoke, rear, '0 0 0', 1);
	}
};

// ---------------------------------------------------------------- getting out and in

// TRUE while p is at the wheel. The gun-drawing helper (custom_effects.qc) hides the gun on this, as it does while a Rob
// Dob head is being flown
float(entity p) Veh_Driving =
{
	return p.veh_van != world;
};

// give the player back to himself
void(entity p, vector pos, vector vel, float yaw) Veh_ReleasePlayer =
{
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
		if (p.veh_camera == 0)
			yaw = v.angles_y;
		Veh_ReleasePlayer (p, pos, vel, yaw);
	}
	if (v.veh_cament != world)
	{
		remove (v.veh_cament);
		v.veh_cament = world;
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

// the van is exploding (vehicles.qc): the driver goes out at the seat, with the van's speed, into the blast
void(entity v) Veh_DriverBail =
{
	local vector seat, vel;

	if (v.veh_driver == world)
		return;
	seat = v.origin + Veh_Fwd (v.angles_y) * 40 + Veh_Lft (v.angles_y) * 19.8;
	seat_z = v.origin_z + 40;
	if (Veh_ExitSpot (v, v.veh_driver))
		seat = vd_exit;		// the seat is inside the wreck's solid box: a survivor (armor, pent) was stuck in it
	vel = v.velocity * 0.6;
	vel_z = 160;
	Veh_Leave (v, seat, vel, TRUE);
};

// ClientDisconnect (client.qc), self = the leaving player: a driver who drops leaves the van parked, not "being driven"
void() Veh_ClientGone =
{
	local entity v;

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

// where can he get out? The driver's door, the passenger's, the back, the nose
float(entity v, entity p) Veh_ExitSpot =
{
	local float i, lx, ly;
	local vector pos, fwd, lft;

	fwd = Veh_Fwd (v.angles_y);
	lft = Veh_Lft (v.angles_y);
	i = 0;
	while (i < 4)
	{
		lx = 34;
		ly = 62;
		if (i == 1)
			ly = -62;
		if (i == 2)
		{
			lx = -154;
			ly = 0;
		}
		if (i == 3)
		{
			lx = 142;
			ly = 0;
		}
		pos = v.origin + fwd * lx + lft * ly;
		pos_z = v.origin_z + 26;
		traceline (pos, pos - '0 0 90', 3, v);
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

void(entity p, entity v) Veh_TryExit =
{
	local float spd, limit;
	local vector vel;

	spd = vlen (v.velocity);
	limit = 140;
	if (v.veh_state == VEH_STATE_FIRE)
		limit = 260;					// a burning van is worth jumping out of at a run
	if (spd > limit)
	{
		centerprint (p, "Too fast to get out!\nBrake first.\n");
		return;
	}
	if (!Veh_ExitSpot (v, p))
	{
		centerprint (p, "No room to open the door.\nPull away from the wall.\n");
		return;
	}
	vel = v.velocity * 0.7;
	vel_z = 0;
	Veh_Leave (v, vd_exit, vel, FALSE);
};

void(entity p, entity v) Veh_Enter =
{
	local entity cam, oldself;

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
	p.ltg_phase = 0;
	p.milky_wind = 0;
	p.pk_throw_at = 0;
	p.ns_throw_at = 0;
	p.mb_throw_at = 0;

	v.veh_driver = p;
	v.veh_drive_mode = TRUE;
	p.veh_van = v;
	p.veh_oldmove = p.movetype;
	p.veh_oldsolid = p.solid;

	// the van stops being a walk-in room and becomes one moving solid; anyone left in the back is thrown out
	Veh_FreeClips (v);
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
	v.veh_start_t = time + 1.0;
	v.veh_music_t = 0;
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
	p.veh_cam_look = 0;
	p.clientcamera = cam;
	msg_entity = p;
	WriteByte (MSG_ONE, 5);			// svc_setview
	WriteEntity (MSG_ONE, cam);
	Veh_DriveCamera (p, v, 0.02);

	sound (v, CHAN_VOICE, "vehicles/ignition.wav", 1, ATTN_NORM);
	if (!p.veh_hint_shown)
	{
		p.veh_hint_shown = TRUE;
		centerprint (p, "WASD drive | SPACE brake | FIRE horn | K cam | H exit");
	}
};

// the van this player can get into: first the one whose driver's seat he is standing in (the cab: x 30..72 forward of
// the van's centre, y -22..38, the floor at 19.5), else the nearest free van he is standing right beside (bklan3 review:
// "I don't know how to get into these vans": the walk-in cab was too hard to find), or world. Tested by position, not
// by the cockpit trigger's touch: a player standing still is not touched again every frame
entity(entity p) Veh_SeatOf =
{
	local entity e, best;
	local vector rel;
	local float lx, ly, d, bd;

	best = world;
	bd = 99999;
	e = findradius (p.origin, 260);
	while (e != world)
	{
		if (e.veh_kind == VEH_VAN && e.veh_state != VEH_STATE_WRECK)
		{
			rel = p.origin - e.origin;
			lx = rel * Veh_Fwd (e.angles_y);
			ly = rel * Veh_Lft (e.angles_y);
			if (lx > 30 && lx < 72 && ly > -22 && ly < 38 && rel_z > 20 && rel_z < 80)
				return e;
			if (e.veh_driver == world && lx > -190 && lx < 190 && ly > -120 && ly < 120 && rel_z > -30 && rel_z < 110)
			{
				d = vlen (rel);
				if (d < bd)
				{
					bd = d;
					best = e;
				}
			}
		}
		e = e.chain;
	}
	return best;
};

// a free van within reach of a player on foot: tell him how to get in, once per van
void() Veh_NearPrompt =
{
	local entity v;

	if (!veh_has_vans || self.ishuman != 1 || self.health <= 0 || self.veh_van != world || self.classname != "player")
		return;
	if (time < self.veh_prompt_scan_t)
		return;
	self.veh_prompt_scan_t = time + 0.1;
	v = Veh_SeatOf (self);
	if (v == world || v.veh_driver != world)
	{
		if (v == world && time > self.veh_prompt_t)
			self.veh_prompt_van = world;
		return;
	}
	if (self.veh_hint_shown || time < self.veh_prompt_t)
		return;
	if (self.veh_prompt_van == v)
	{
		self.veh_prompt_t = time + 35;
		return;
	}
	self.veh_prompt_van = v;
	self.veh_prompt_t = time + 35;
	centerprint (self, "Press H to drive ProMaster");
};

// H on foot (called from Vehicles_Impulse)
void() Veh_EnterKey =
{
	local entity v;
	local vector pos;

	if (self.health <= 0 || self.veh_van != world)
		return;
	v = Veh_SeatOf (self);
	if (v == world)
		return;
	if (v.veh_driver != world)
	{
		sprint (self, "Someone is already driving this van.\n");
		return;
	}
	if (self.fd_head != world || self.jp_on)
	{
		sprint (self, "Put the jetpack / Rob Dob away first.\n");
		return;
	}
	pos = v.origin + Veh_Fwd (v.angles_y) * 50 + Veh_Lft (v.angles_y) * 8;		// into the driver's seat, from wherever he stood
	pos_z = v.origin_z + 44;
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

	if (self.veh_van != world || self.health <= 0)
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
	local float started, living, ctop;
	local vector vel, org0, org1, org2, fwd, lft, n;

	v = self.veh_van;
	if (v == world)
		return FALSE;
	if (v.veh_driver != self || v.veh_state == VEH_STATE_WRECK || self.health <= 0)
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
	if (started && time >= v.veh_music_t)
	{
		v.veh_music_t = time + VD_MUSIC_LEN;
		sound (v, VD_MUSIC_CH, "vehicles/lanvan.wav", 0.5, ATTN_NORM);
		dprint ("lanvan: chant starts\n");
	}
	if (self.button0 && time >= v.veh_horn_t && started)
	{
		v.veh_horn_t = time + 1;
		sound (v, CHAN_WEAPON, "vehicles/horn.wav", 1, ATTN_NORM);
	}

	// the wheel eases toward the key: slow out from centre, quick to come back, quickest to counter-steer
	rate = 4.2;
	if (steer_in == 0)
		rate = 6.5;
	else if (steer_in * v.veh_steer < 0)
		rate = 8.5;
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

	// ---- the longer he keeps it floored the faster it will go: the boost builds while the throttle is open and the van is
	// really rolling forward, fades once he lifts, and the brake / handbrake / a crash take it away
	if (thr > 0 && brk == 0 && !hb && !v.veh_air && vf > 120)
		v.veh_boost = min (1, v.veh_boost + dt / VD_BOOST_TIME);
	else if (brk > 0 || hb)
		v.veh_boost = max (0, v.veh_boost - dt * 0.5);
	else if (thr == 0)
		v.veh_boost = max (0, v.veh_boost - dt / 25);
	ctop = VD_TOP * (1 + VD_BOOST_TOP * v.veh_boost);

	// ---- pedals. Forward key: drive, or brake if still rolling backward. Back key: brake, or reverse once stopped
	acc = 0;
	brake_a = 0;
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
			acc = thr * VD_ACCEL * (1 + VD_BOOST_ACC * v.veh_boost) * power * (1 - pow (k, 1.8));
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
		brake_a = brake_a + 260;

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
	grip = VD_GRIP;
	if (hb)
		grip = VD_GRIP_HB;
	grip = grip * (1 - 0.45 * bound (0, brake_a / VD_BRAKE, 1));
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
	yr_geo = 0 - vf * Veh_Tan (delta) / VD_WHEELBASE * 57.2958;
	yr_cap = grip / max (spd, 30) * 57.2958;
	yr = bound (0 - yr_cap, yr_geo, yr_cap);
	if (hb && spd > 140)
		yr = yr_geo * 1.5;				// locked rears: the tail comes round, and the grip limit no longer stops it
	if (v.veh_air)
		yr = v.veh_yawrate * 0.995;		// in the air nothing steers
	v.veh_yawrate = v.veh_yawrate + (yr - v.veh_yawrate) * min (1, dt * 7);
	yaw1 = Veh_NormYaw (yaw0 + v.veh_yawrate * dt);

	vel = fwd * vf + lft * vl;

	// ---- move: sweep the footprint; if it is blocked, slide along the wall, and what was lost is the crash
	org0 = v.origin;
	org1 = org0;
	org1_x = org0_x + vel_x * dt;
	org1_y = org0_y + vel_y * dt;
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
			v.veh_boost = v.veh_boost * (1 - bound (0, imp / 400, 1));		// a crash loses the build-up
			living = FALSE;
			if (vd_hitent != world && vd_hitent.takedamage)
			{
				if ((vd_hitent.flags & FL_CLIENT) || (vd_hitent.flags & FL_MONSTER))
					living = TRUE;
				Veh_RamHit (v, vd_hitent, imp);
			}
			if (!living && imp > 160)
				Veh_Crash (v, imp, vd_hitpos);
			if (self.veh_van != v)
				return TRUE;			// the crash blew the van up
			if (living)
				vel = vel * 0.9;
			else if (imp > 120)
				vel = vel - n * (vn * 1.15);		// off the wall with a little bounce
			else
				vel = vel - n * vn;
			vel = vel * (1 - 0.7 * dt);				// scraping
		}
		org2 = org0;
		org2_x = org0_x + vel_x * dt;
		org2_y = org0_y + vel_y * dt;
		if (Veh_DriveSweep (v, org0, yaw0, org2, yaw1))
			org1 = org2;
		else if (yaw1 != yaw0 && Veh_DriveSweep (v, org0, yaw0, org0, yaw1))
		{
			org1 = org0;
			vel = vel * 0.5;
		}
		else
		{
			org1 = org0;
			yaw1 = yaw0;
			vel = vel * 0.5;
			v.veh_yawrate = 0;
		}
	}

	// ---- up and down: ride the road, or fly
	Veh_GroundSample (v, org1, yaw1);
	z = org1_z;
	if (v.veh_air)
	{
		v.veh_vz = v.veh_vz - VD_GRAVITY * dt;
		z = z + v.veh_vz * dt;
		if (vd_found && v.veh_vz <= 0 && z <= vd_gh + 1)
		{
			imp = 0 - v.veh_vz;
			z = vd_gh;
			v.veh_vz = 0;
			v.veh_air = FALSE;
			if (imp > 300)
				Veh_Crash (v, imp * 0.8, org1);			// came down hard
			else if (imp > 120)
				sound7 (v, CHAN_BODY, "vehicles/tire_thud2.wav", 0.9, ATTN_NORM, 80 + random () * 10);
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
	if (vd_found)
		v.angles_x = v.angles_x + (vd_pitch - v.angles_x) * min (1, dt * 10);

	v.angles_y = yaw1;
	v.velocity = vel;
	if (v.veh_air)
		v.velocity_z = v.veh_vz;
	setorigin (v, org1);
	Veh_DriveBounds (v);

	// ---- engine revs: 5 gears picked by road speed; the revs fall at each upshift. Standing still the throttle revs it
	spd = fabs (vf);
	gear = 4;
	top = max (660, ctop * 1.03);
	lo = 560;
	if (spd < 150)
	{
		gear = 0;
		top = 150;
		lo = 0;
	}
	else if (spd < 290)
	{
		gear = 1;
		top = 290;
		lo = 150;
	}
	else if (spd < 430)
	{
		gear = 2;
		top = 430;
		lo = 290;
	}
	else if (spd < 560)
	{
		gear = 3;
		top = 560;
		lo = 430;
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
		rpm_t = 0.35 + 0.65 * thr;
	if (rpm_t > v.veh_rpm)
		v.veh_rpm = min (rpm_t, v.veh_rpm + 3.2 * dt);
	else
		v.veh_rpm = max (rpm_t, v.veh_rpm - 2.2 * dt);
	if (started)
		Veh_EngineSound (v, thr);

	// ---- tyre noise: sideways sliding, a hard stop from speed, or the handbrake at speed
	if (!v.veh_air)
	{
		if (brake_a > 450 && spd > 260)
			slip = max (slip, 150);
		if (hb && spd > 120)
			slip = max (slip, 190);
		if (slip > 90)
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

	// ---- the driver rides in the seat; the view is the camera
	setorigin (self, v.origin + fwd * 40 + lft * 19.8 + '0 0 44');
	Veh_DriveCamera (self, v, dt);
	return TRUE;
};
