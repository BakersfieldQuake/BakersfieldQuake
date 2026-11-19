#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
MEGA MAN TANK - Drivable Heavy Tank Implementation (Combat+)

  1. Map entity `misc_mm_tank` (snaps cleanly onto ground, Hull-safe, 600 HP default).
  2. Walk up within 165u -> "Press H to drive MEGA MAN TANK". Press H (impulse 86) to mount/exit.
  3. Driving & Camera:
     - W / S    : Drive forward (~190 u/s max) / reverse (~130 u/s) with heavy accel & braking.
     - A / D    : Rotate heavy hull yaw (tank skid-steer, works stationary or rolling).
     - Mouse    : Smoothly orbits 3rd-person chase cam & aims turret + silver bar yaw/pitch independently!
     - MOUSE1   : Launch rocket-boosted progs/mm_tank_bar.md3 (fire trail, 150 splash boom, wheel debris).
     - SPACE    : Horn blast & handbrake!
     - K (87)   : Toggle standard / wide 3rd-person chase camera.
  4. Wheelman Mechanic:
     - Little 8-direction 360° Wheelman sprite (progs/wheelman_dance.spr32) rides perched on front deck.
     - After firing, turret empties and Wheelman visibly lifts, spins, and re-installs a 3D silver bar
       over ~6 seconds with welding sparks & ratchet/hammer audio until locked back in!
  5. Live Prototype & Sound Pack Switching:
     - mm_tank_variant (1..4) / impulse 134 / cmd `tank_variant` : hot-swap V1..V4 models live.
     - mm_tank_soundpack (1..8) / impulse 135 / cmd `tank_sound` : hot-swap 8 loud sound packs live.
================
*/

void() MMT_Think;
void(entity tank, float forced) MMT_CatastrophicExplode;
void(entity p, entity tank) MMT_UpdateCameraAndAim;

// ---------------------------------------------------------------- Math Helpers

float(float deg) MMT_Sin =
{
	local float r, s;
	r = deg * 0.01745329;
	s = sin (r);
	return s;
};

float(float deg) MMT_Cos =
{
	local float r, c;
	r = deg * 0.01745329;
	c = cos (r);
	return c;
};

float(float a) MMT_NormAng =
{
	while (a > 180)
		a = a - 360;
	while (a < -180)
		a = a + 360;
	return a;
};

float(float a) MMT_NormYaw =
{
	while (a >= 360)
		a = a - 360;
	while (a < 0)
		a = a + 360;
	return a;
};

float(float to_ang, float from_ang) MMT_AngDelta =
{
	return MMT_NormAng (to_ang - from_ang);
};

float(float cur, float targ, float step) MMT_Approach =
{
	if (cur < targ)
	{
		cur = cur + step;
		if (cur > targ)
			cur = targ;
	}
	else
	{
		cur = cur - step;
		if (cur < targ)
			cur = targ;
	}
	return cur;
};

float(float rise, float run) MMT_RiseAngle =
{
	local vector d, a;
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

// ---------------------------------------------------------------- Variant & Sound Pack Tables

float(float v) MMT_ClampVariant =
{
	v = floor (v);
	if (v < 1 || v > 4)
		return 1;
	return v;
};

float(float p) MMT_ClampPack =
{
	p = floor (p);
	if (p < 0 || p > 11)
		return 0;
	return p;
};

string(float v) MMT_VariantName =
{
	if (v == 2) return "V2: Clean Machined Original";
	if (v == 3) return "V3: Tall-Wheel Slender-Bar Original";
	if (v == 4) return "V4: Fat-Tire Heavy-Bar Original";
	return "V1: Exact megaman1.glb 1:1 Giant";
};

string(float v) MMT_HullModel =
{
	if (v == 2) return "progs/mm_tank_v2.md3";
	if (v == 3) return "progs/mm_tank_v3.md3";
	if (v == 4) return "progs/mm_tank_v4.md3";
	return "progs/mm_tank_v1.md3";
};

string(float v) MMT_TurretModel =
{
	if (v == 2) return "progs/mm_tank_turret_v2.md3";
	if (v == 3) return "progs/mm_tank_turret_v3.md3";
	if (v == 4) return "progs/mm_tank_turret_v4.md3";
	return "progs/mm_tank_turret_v1.md3";
};

string(float p) MMT_PackName =
{
	if (p == 0) return "Pack 0: Official Voted Mix";
	if (p == 2) return "Pack 2: Mega Man Arcade Synth";
	if (p == 3) return "Pack 3: Wheelman Voice-Chaos";
	if (p == 4) return "Pack 4: Larry McCart LAN Tank";
	if (p == 5) return "Pack 5: Air-Raid Steamroller";
	if (p == 6) return "Pack 6: Cartoon Boing-Nuke";
	if (p == 7) return "Pack 7: Industrial Forge & Anvil";
	if (p == 8) return "Pack 8: Ear-Splitting Monster Truck";
	if (p == 9) return "Pack 9: Larry ChatExport Voice-Remix";
	if (p == 10) return "Pack 10: Velvet Sub-Bass & Tuba Comedy";
	if (p == 11) return "Pack 11: Deep-Warm Larry Lounge";
	return "Pack 1: Heavy Diesel Bass-Boost";
};

// kind: 0=engine, 1=move, 2=fire, 3=boom, 4=reload, 5=horn
string(float p, float kind) MMT_Snd =
{
	if (p == 0)
	{
		if (kind == 0) return "mm_tank/pack1/engine.wav";
		if (kind == 1) return "mm_tank/pack1/move.wav";
		if (kind == 2) return "mm_tank/pack6/fire.wav";
		if (kind == 3) return "mm_tank/pack10/boom.wav";
		if (kind == 4) return "mm_tank/pack10/reload.wav";
		return "mm_tank/pack11/horn.wav";
	}
	if (p == 1)
	{
		if (kind == 0) return "mm_tank/pack1/engine.wav";
		if (kind == 1) return "mm_tank/pack1/move.wav";
		if (kind == 2) return "mm_tank/pack1/fire.wav";
		if (kind == 3) return "mm_tank/pack1/boom.wav";
		if (kind == 4) return "mm_tank/pack1/reload.wav";
		return "mm_tank/pack1/horn.wav";
	}
	if (p == 2)
	{
		if (kind == 0) return "mm_tank/pack2/engine.wav";
		if (kind == 1) return "mm_tank/pack2/move.wav";
		if (kind == 2) return "mm_tank/pack2/fire.wav";
		if (kind == 3) return "mm_tank/pack2/boom.wav";
		if (kind == 4) return "mm_tank/pack2/reload.wav";
		return "mm_tank/pack2/horn.wav";
	}
	if (p == 3)
	{
		if (kind == 0) return "mm_tank/pack3/engine.wav";
		if (kind == 1) return "mm_tank/pack3/move.wav";
		if (kind == 2) return "mm_tank/pack3/fire.wav";
		if (kind == 3) return "mm_tank/pack3/boom.wav";
		if (kind == 4) return "mm_tank/pack3/reload.wav";
		return "mm_tank/pack3/horn.wav";
	}
	if (p == 4)
	{
		if (kind == 0) return "mm_tank/pack4/engine.wav";
		if (kind == 1) return "mm_tank/pack4/move.wav";
		if (kind == 2) return "mm_tank/pack4/fire.wav";
		if (kind == 3) return "mm_tank/pack4/boom.wav";
		if (kind == 4) return "mm_tank/pack4/reload.wav";
		return "mm_tank/pack4/horn.wav";
	}
	if (p == 5)
	{
		if (kind == 0) return "mm_tank/pack5/engine.wav";
		if (kind == 1) return "mm_tank/pack5/move.wav";
		if (kind == 2) return "mm_tank/pack5/fire.wav";
		if (kind == 3) return "mm_tank/pack5/boom.wav";
		if (kind == 4) return "mm_tank/pack5/reload.wav";
		return "mm_tank/pack5/horn.wav";
	}
	if (p == 6)
	{
		if (kind == 0) return "mm_tank/pack6/engine.wav";
		if (kind == 1) return "mm_tank/pack6/move.wav";
		if (kind == 2) return "mm_tank/pack6/fire.wav";
		if (kind == 3) return "mm_tank/pack6/boom.wav";
		if (kind == 4) return "mm_tank/pack6/reload.wav";
		return "mm_tank/pack6/horn.wav";
	}
	if (p == 7)
	{
		if (kind == 0) return "mm_tank/pack7/engine.wav";
		if (kind == 1) return "mm_tank/pack7/move.wav";
		if (kind == 2) return "mm_tank/pack7/fire.wav";
		if (kind == 3) return "mm_tank/pack7/boom.wav";
		if (kind == 4) return "mm_tank/pack7/reload.wav";
		return "mm_tank/pack7/horn.wav";
	}
	if (p == 8)
	{
		if (kind == 0) return "mm_tank/pack8/engine.wav";
		if (kind == 1) return "mm_tank/pack8/move.wav";
		if (kind == 2) return "mm_tank/pack8/fire.wav";
		if (kind == 3) return "mm_tank/pack8/boom.wav";
		if (kind == 4) return "mm_tank/pack8/reload.wav";
		return "mm_tank/pack8/horn.wav";
	}
	if (p == 9)
	{
		if (kind == 0) return "mm_tank/pack9/engine.wav";
		if (kind == 1) return "mm_tank/pack9/move.wav";
		if (kind == 2) return "mm_tank/pack9/fire.wav";
		if (kind == 3) return "mm_tank/pack9/boom.wav";
		if (kind == 4) return "mm_tank/pack9/reload.wav";
		return "mm_tank/pack9/horn.wav";
	}
	if (p == 10)
	{
		if (kind == 0) return "mm_tank/pack10/engine.wav";
		if (kind == 1) return "mm_tank/pack10/move.wav";
		if (kind == 2) return "mm_tank/pack10/fire.wav";
		if (kind == 3) return "mm_tank/pack10/boom.wav";
		if (kind == 4) return "mm_tank/pack10/reload.wav";
		return "mm_tank/pack10/horn.wav";
	}
	if (kind == 0) return "mm_tank/pack11/engine.wav";
	if (kind == 1) return "mm_tank/pack11/move.wav";
	if (kind == 2) return "mm_tank/pack11/fire.wav";
	if (kind == 3) return "mm_tank/pack11/boom.wav";
	if (kind == 4) return "mm_tank/pack11/reload.wav";
	return "mm_tank/pack11/horn.wav";
};

// ---------------------------------------------------------------- Precache

void() MMTank_Precache =
{
	local float p, k;

	if (mmt_precached)
		return;
	mmt_precached = TRUE;

	precache_model ("progs/mm_tank_v1.md3");
	precache_model ("progs/mm_tank_v2.md3");
	precache_model ("progs/mm_tank_v3.md3");
	precache_model ("progs/mm_tank_v4.md3");
	precache_model ("progs/mm_tank_turret_v1.md3");
	precache_model ("progs/mm_tank_turret_v2.md3");
	precache_model ("progs/mm_tank_turret_v3.md3");
	precache_model ("progs/mm_tank_turret_v4.md3");
	precache_model ("progs/mm_tank_bar.md3");
	precache_model ("progs/mm_tank_wheel_debris.md3");
	precache_model ("progs/mm_bar.md3");
	precache_model ("progs/mm_frag1.md3");
	precache_model ("progs/mm_frag2.md3");
	precache_model ("progs/mm_frag3.md3");
	precache_model ("progs/mm_frag4.md3");
	precache_model ("progs/wheelman_dance.spr32");
	precache_model ("progs/spike.mdl");
	precache_model ("progs/s_explodbig.spr");
	precache_model ("progs/ring_shockwave.mdl");

	p = 1;
	while (p <= 11)
	{
		k = 0;
		while (k <= 5)
		{
			precache_sound (MMT_Snd (p, k));
			k = k + 1;
		}
		p = p + 1;
	}

	precache_sound ("weapons/r_exp3.wav");
	precache_sound ("weapons/explodedist.wav");
	precache_sound ("weapons/tink1.wav");
	precache_sound ("weapons/ric1.wav");
	precache_sound ("weapons/ric2.wav");
	precache_sound ("vehicles/hit_metal1.wav");
	precache_sound ("vehicles/hit_metal2.wav");
	precache_sound ("vehicles/fire_burn.wav");
	precache_sound ("vehicles/clang2.wav");
	precache_sound ("megaman/tire1.wav");
	precache_sound ("megaman/tire2.wav");
	precache_sound ("megaman/tire3.wav");
	precache_sound ("items/itembk2.wav");
	precache_sound ("misc/null.wav");
	precache_sound ("ambience/windfly.wav");
	precache_sound ("skypad/launch.wav");

	mmt_fx_bar_trail = particleeffectnum ("mm_tank_bar_trail");
	mmt_fx_bar_boom = particleeffectnum ("mm_tank_bar_boom");
	mmt_fx_reload_sparks = particleeffectnum ("mm_tank_reload_sparks");
	mmt_fx_catastrophic = particleeffectnum ("mm_tank_catastrophic");
	mmt_fx_fire = particleeffectnum ("veh_fire");
	mmt_fx_smoke = particleeffectnum ("veh_smoke");
	mmt_fx_wreck = particleeffectnum ("veh_wreck_fire");
	mmt_fx_sparks = particleeffectnum ("veh_sparks");
};

float(entity p) MMTank_Driving =
{
	return (p.mmt_tank != world);
};

// ---------------------------------------------------------------- Live Variant & Sound Pack Switching

void(entity tank, float v) MMT_ApplyVariant =
{
	v = MMT_ClampVariant (v);
	tank.mmt_variant = v;
	if (tank.mmt_state == MMT_STATE_WRECK)
		return;
	setmodel (tank, MMT_HullModel (v));
	setsize (tank, '-104 -104 0', '104 104 132');
	setorigin (tank, tank.origin);
	if (tank.mmt_turret != world)
	{
		setmodel (tank.mmt_turret, MMT_TurretModel (v));
		setsize (tank.mmt_turret, '0 0 0', '0 0 0');
	}
};

void(float v) MMTank_SetVariant =
{
	local entity t;
	local string s;

	v = MMT_ClampVariant (v);
	s = ftos (v);
	cvar_set ("mm_tank_variant", s);
	mmt_last_variant = v;

	t = find (world, classname, "misc_mm_tank");
	while (t != world)
	{
		MMT_ApplyVariant (t, v);
		t = find (t, classname, "misc_mm_tank");
	}
};

void(float p) MMTank_SetSoundPack =
{
	p = MMT_ClampPack (p);
	cvar_set ("mm_tank_soundpack", ftos (p));
};

void(float mask) MMTank_SetBoomMask =
{
	mask = floor (mask);
	if (mask < 0)
		mask = 0;
	if (mask > 2047)
		mask = 2047;
	cvar_set ("mm_tank_boom_mask", ftos (mask));
};

string(float mask) MMT_BoomMaskSummary =
{
	local float p, bit;
	local string out;

	mask = floor (mask);
	if (mask <= 0)
		return "none (uses active mm_tank_soundpack)";
	out = "";
	p = 1;
	bit = 1;
	while (p <= 11)
	{
		if (mask & bit)
		{
			if (out == "")
				out = ftos (p);
			else
				out = strcat (out, strcat (", ", ftos (p)));
		}
		bit = bit * 2;
		p = p + 1;
	}
	if (out == "")
		return "none (uses active mm_tank_soundpack)";
	return out;
};

string(float cur_pack) MMT_PickBoomSound =
{
	local float mask, p, bit, cnt, pick, seen;

	mask = floor (autocvar_mm_tank_boom_mask);
	if (mask <= 0)
		return MMT_Snd (cur_pack, 3);

	cnt = 0;
	p = 1;
	bit = 1;
	while (p <= 11)
	{
		if (mask & bit)
			cnt = cnt + 1;
		bit = bit * 2;
		p = p + 1;
	}
	if (cnt <= 0)
		return MMT_Snd (cur_pack, 3);

	pick = floor (random () * cnt);
	if (pick >= cnt)
		pick = cnt - 1;

	seen = 0;
	p = 1;
	bit = 1;
	while (p <= 11)
	{
		if (mask & bit)
		{
			if (seen == pick)
				return MMT_Snd (p, 3);
			seen = seen + 1;
		}
		bit = bit * 2;
		p = p + 1;
	}
	return MMT_Snd (cur_pack, 3);
};

void() MMTank_StartFrame =
{
	local float v;
	local entity t;

	v = MMT_ClampVariant (autocvar_mm_tank_variant);
	if (!mmt_last_variant)
		mmt_last_variant = v;
	if (v != mmt_last_variant)
	{
		mmt_last_variant = v;
		t = find (world, classname, "misc_mm_tank");
		while (t != world)
		{
			MMT_ApplyVariant (t, v);
			t = find (t, classname, "misc_mm_tank");
		}
	}
};

// ---------------------------------------------------------------- Player Hide / Camera / Exit Helpers

void(entity p) MMT_HidePlayer =
{
	p.alpha = 0.01;
	p.effects = p.effects | EF_NODRAW;
	p.weaponmodel = "";
	if (!(p.flags & FL_NOTARGET))
	{
		p.flags = p.flags | FL_NOTARGET;
		p.mmt_notarget = TRUE;
	}
};

void(entity p) MMT_UnhidePlayer =
{
	p.alpha = 0;
	p.effects = p.effects - (p.effects & EF_NODRAW);
	if (p.mmt_notarget)
	{
		p.mmt_notarget = FALSE;
		if (p.flags & FL_NOTARGET)
			p.flags = p.flags - FL_NOTARGET;
	}
};

void(entity p, entity tank) MMT_RestoreViewAndBody =
{
	local entity oldself;

	p.mmt_st_active = 0;
	if (tank != world && tank.mmt_cam != world)
	{
		if (!bm_wasfreed (tank.mmt_cam) && tank.mmt_cam.classname == "mmt_cam")
			remove (tank.mmt_cam);
		tank.mmt_cam = world;
	}
	if (p.ishuman == 1)
	{
		p.clientcamera = p;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, p);
	}
	p.punchangle = '0 0 0';
	p.v_angle_z = 0;
	p.angles_z = 0;
	MMT_UnhidePlayer (p);
	if (p.health > 0)
	{
		p.movetype = p.mmt_oldmove;
		if (p.movetype == MOVETYPE_NONE || p.movetype == 0)
			p.movetype = MOVETYPE_WALK;
		p.solid = p.mmt_oldsolid;
		if (p.solid == SOLID_NOT || p.solid == 0)
			p.solid = SOLID_SLIDEBOX;
		oldself = self;
		self = p;
		W_SetCurrentAmmo ();
		self = oldself;
	}
};

float(entity p, vector pos) MMT_SpotClear =
{
	tracebox (pos, VEC_HULL_MIN, VEC_HULL_MAX, pos, FALSE, p);
	if (trace_startsolid || trace_allsolid)
		return FALSE;
	return TRUE;
};

vector(entity tank, entity p) MMT_FindExitPos =
{
	local vector cand;

	makevectors ('0 1 0' * tank.angles_y);
	cand = tank.origin - v_right * 136 + '0 0 36';
	if (MMT_SpotClear (p, cand))
		return cand;
	cand = tank.origin + v_right * 136 + '0 0 36';
	if (MMT_SpotClear (p, cand))
		return cand;
	cand = tank.origin - v_forward * 140 + '0 0 36';
	if (MMT_SpotClear (p, cand))
		return cand;
	cand = tank.origin + v_forward * 140 + '0 0 36';
	if (MMT_SpotClear (p, cand))
		return cand;
	// all four sides blocked: the roof (checked too), then the rear corners, before the old unchecked roof spot
	cand = tank.origin + '0 0 157';
	if (MMT_SpotClear (p, cand))
		return cand;
	cand = tank.origin - v_forward * 140 - v_right * 136 + '0 0 36';
	if (MMT_SpotClear (p, cand))
		return cand;
	cand = tank.origin - v_forward * 140 + v_right * 136 + '0 0 36';
	if (MMT_SpotClear (p, cand))
		return cand;
	return tank.origin + '0 0 156';
};

// ---------------------------------------------------------------- Wheelman 360° Mechanic & Turret / Reload Sync

float() MMT_WheelmanCustomize =
{
	local entity tank;
	local vector eye, delta;
	local float rel, d, k, el;

	tank = self.mmt_base;
	if (tank == world || tank.mmt_state == MMT_STATE_WRECK || time >= tank.mmt_reload_end)
		return FALSE;

	if (other.clientcamera != world && other.clientcamera != other)
		eye = other.clientcamera.origin;
	else
		eye = other.origin + other.view_ofs;

	delta = eye - (self.origin + '0 0 30');
	rel = vectoyaw (delta) - self.angles_y;
	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 45 + 0.5);
	if (d >= 8)
		d = 0;

	el = time - tank.mmt_reload_start;
	if (el < 0.60)
	{
		k = floor (el * 16);
		k = k - 5 * floor (k / 5);
		self.frame = 128 + d * 5 + k;	// hands_up_kick (shot celebrate)
	}
	else if (el < 2.20)
	{
		k = floor ((el - 0.60) * 11);
		k = k - 6 * floor (k / 6);
		self.frame = 216 + d * 6 + k;	// weightlift (deadlift new silver bar)
	}
	else if (el < 4.00)
	{
		k = floor ((el - 2.20) * 14);
		k = k - 6 * floor (k / 6);
		self.frame = 168 + d * 6 + k;	// spin_bar (machining/spinning bar)
	}
	else if (el < 5.60)
	{
		k = floor ((el - 4.00) * 11);
		k = k - 6 * floor (k / 6);
		self.frame = 264 + d * 6 + k;	// throw_rig (hoisting bar into cradle)
	}
	else
	{
		k = floor ((el - 5.60) * 15);
		k = k - 6 * floor (k / 6);
		self.frame = 80 + d * 6 + k;	// dance (lock-in celebration)
	}
	return TRUE;
};

void(entity tank) MMT_SyncAttachments =
{
	local entity tur, wm, bp;
	local vector hull_fwd, hull_up, tur_pos, wm_pos, tur_aim, tur_fwd, bpos, p0, p1;
	local float el, u, pack, idx;

	if (tank.mmt_state == MMT_STATE_WRECK)
		return;

	makevectors ('0 1 0' * tank.angles_y);
	hull_fwd = v_forward;
	hull_up = '0 0 1';

	tur_pos = tank.origin + '0 0 63';
	wm_pos = tank.origin + hull_fwd * 46 + '0 0 4';

	// Aim vector along turret barrel
	tur_aim = '0 0 0';
	tur_aim_x = 0 - tank.mmt_turret_pitch;
	tur_aim_y = tank.mmt_turret_yaw;
	makevectors (tur_aim);
	tur_fwd = v_forward;

	// 1. Turret attachment
	tur = tank.mmt_turret;
	if (tur != world)
	{
		tur.effects = tur.effects - (tur.effects & EF_NODRAW);
		setorigin (tur, tur_pos);
		tur.angles_x = tank.mmt_turret_pitch;
		tur.angles_y = tank.mmt_turret_yaw;
		tur.angles_z = 0;

		if (time < tank.mmt_recoil_end)
		{
			el = 0.60 - (tank.mmt_recoil_end - time);
			idx = bound (0, floor ((el / 0.60) * 12), 11);
			tur.frame = 8 + idx;
		}
		else if (time < tank.mmt_reload_end)
		{
			if (tank.mmt_reload_end - time <= 0.40)
			{
				u = 1.0 - (tank.mmt_reload_end - time) / 0.40;
				tur.frame = 28 + bound (0, floor (u * 4), 3);
			}
			else
			{
				idx = floor (time * 10);
				idx = idx - 8 * floor (idx / 8);
				tur.frame = 20 + idx;
			}
		}
		else
		{
			idx = floor (time * 10);
			idx = idx - 8 * floor (idx / 8);
			tur.frame = idx;
		}
	}

	// 2. Front Wheelman sprite: ONLY visible while reloading (`time < tank.mmt_reload_end`)
	wm = tank.mmt_wheelman;
	if (wm != world)
	{
		if (time < tank.mmt_reload_end)
		{
			wm.effects = wm.effects - (wm.effects & EF_NODRAW);
			setorigin (wm, wm_pos);
			wm.angles_y = tank.angles_y;
		}
		else
			wm.effects = wm.effects | EF_NODRAW;
	}

	// 3. 3D Reloading Silver Bar prop + reload sounds/sparks
	bp = tank.mmt_bar_prop;
	pack = MMT_ClampPack (autocvar_mm_tank_soundpack);
	if (time < tank.mmt_reload_end)
	{
		el = time - tank.mmt_reload_start;
		if (el >= 0.60 && !tank.mmt_reload_snd1)
		{
			tank.mmt_reload_snd1 = TRUE;
			sound (tank, CHAN_VOICE, MMT_Snd (pack, 4), 1.0, 0.35);
		}
		if (el >= 3.10 && !tank.mmt_reload_snd2)
		{
			tank.mmt_reload_snd2 = TRUE;
			sound (tank, CHAN_VOICE, MMT_Snd (pack, 4), 1.0, 0.35);
		}
		if (el >= 0.65 && el < 5.55 && time >= tank.mmt_reload_spk_t)
		{
			tank.mmt_reload_spk_t = time + 0.28;
			if (mmt_fx_reload_sparks > 0)
				pointparticles (mmt_fx_reload_sparks, wm_pos + '0 0 38', '0 0 55', 1);
		}
		if (el >= 5.60 && !tank.mmt_reload_lock_snd)
		{
			tank.mmt_reload_lock_snd = TRUE;
			sound (tank, CHAN_AUTO, "weapons/tink1.wav", 1.0, 0.45);
			if (mmt_fx_reload_sparks > 0)
				pointparticles (mmt_fx_reload_sparks, tur_pos + tur_fwd * 18, '0 0 80', 1);
		}

		if (bp != world)
		{
			if (el >= 0.60 && el < 5.60)
			{
				bp.effects = bp.effects - (bp.effects & EF_NODRAW);
				if (el < 2.20)
				{
					u = (el - 0.60) / 1.60;
					bpos = wm_pos + '0 0 16' + '0 0 40' * u;
					bp.angles_x = MMT_Sin (u * 720) * 8;
					bp.angles_y = MMT_NormYaw (tank.angles_y + 90);
					bp.angles_z = 0;
				}
				else if (el < 4.00)
				{
					u = (el - 2.20) / 1.80;
					bpos = wm_pos + '0 0 56' + hull_up * (MMT_Sin (u * 1080) * 6);
					bp.angles_x = MMT_Sin (u * 1440) * 14;
					bp.angles_y = MMT_NormYaw (tank.angles_y + 90 + u * 1080);
					bp.angles_z = MMT_Cos (u * 1080) * 12;
				}
				else
				{
					u = (el - 4.00) / 1.60;
					p0 = wm_pos + '0 0 56';
					p1 = tur_pos + tur_fwd * 18;
					bpos = p0 + (p1 - p0) * u;
					bp.angles_x = tank.mmt_turret_pitch * u;
					bp.angles_y = MMT_NormYaw (tank.angles_y + 90 * (1 - u) + MMT_AngDelta (tank.mmt_turret_yaw, tank.angles_y) * u);
					bp.angles_z = 0;
				}
				setorigin (bp, bpos);
			}
			else
				bp.effects = bp.effects | EF_NODRAW;
		}
	}
	else if (bp != world)
		bp.effects = bp.effects | EF_NODRAW;
};

// ---------------------------------------------------------------- Screen Shake & Radius Blast

void(vector boom_org, float max_rad, float max_punch) MMT_ShakePlayers =
{
	local entity plyr;
	local float dist, sh;

	if (autocvar_effects_explosion_shake == 0)
		return;

	plyr = find (world, classname, "player");
	while (plyr != world)
	{
		dist = vlen (boom_org - plyr.origin);
		if (dist < max_rad)
		{
			sh = max_punch * (1.0 - dist / max_rad);
			plyr.punchangle_x = plyr.punchangle_x + crandom () * sh;
			plyr.punchangle_y = plyr.punchangle_y + crandom () * (sh * 0.7);
			if (plyr.mmt_tank == world)
				plyr.punchangle_z = plyr.punchangle_z + crandom () * (sh * 0.9);
			else
				plyr.punchangle_z = 0;
		}
		plyr = find (plyr, classname, "player");
	}
};

// private link lists: Traffic_BlastExplode / T_Damage can run findradius and overwrite .chain
.entity	mmt_boom_next;
.entity	mmt_run_next;
.float	mmt_pad_scan_t;		// next jump/sky pad scan in MMT_CheckPads (entity-list walk throttled to 20 Hz)

void(entity inflictor, entity attacker, float peak_dmg, float blast_rad, entity ignore, entity reduced_self_tank) MMT_RadiusBlast =
{
	local entity head, explo, cars, nxt;
	local vector org, push_dir;
	local float dist, falloff, points;

	explo = Gyro_Force_Create ("explosion", inflictor.origin);
	Gyro_Force_ApplyFalloff_AreaQuadratic (explo, ('4 4 4' * blast_rad));
	Gyro_Force_ApplyAffector_Point (explo, '0 0 -24', '1 1 1', (peak_dmg * 11.0), FALSE);
	Gyro_Force_AddProperty_Instant (explo);
	Gyro_Force_AddProperty_AirOnly (explo);

	explo = Gyro_Force_Create ("explosion", inflictor.origin);
	Gyro_Force_ApplyFalloff_AreaLinear (explo, ('2 2 2' * blast_rad));
	Gyro_Force_ApplyAffector_Point (explo, '0 0 -24', '1 1 1', (peak_dmg * 5.5), FALSE);
	Gyro_Force_AddProperty_Instant (explo);
	Gyro_Force_AddProperty_WaterOnly (explo);

	cars = world;
	head = findradius (inflictor.origin, blast_rad);
	while (head)
	{
		if (head != ignore && mmt_inflicting == 1 && head.classname == "misc_traffic_car")
		{
			// explode after the loop: its T_RadiusDamage would overwrite .chain mid-walk
			head.mmt_boom_next = cars;
			cars = head;
		}
		else if (head != ignore && head.takedamage)
		{
			org = head.origin + ((head.mins + head.maxs) * 0.5);
			dist = vlen (inflictor.origin - org);
			falloff = 1.0 - (dist / blast_rad);
			if (falloff > 0)
			{
				points = peak_dmg * falloff;
				if (head == attacker)
					points = points * 0.15;
				else if (head == reduced_self_tank)
					points = points * 0.12;		// don't blow up your own tank from close ground shots
				else if (mmt_inflicting == 1 && (head.veh_kind > 0 || head.classname == "veh_van_clip"))
				{
					points = points * 3.0;
					if (falloff > 0.25 && points < 300)
						points = 300;
				}
				if (points > 0 && CanDamage (head, inflictor))
				{
					if (head.movetype != MOVETYPE_NONE && head.movetype != MOVETYPE_PUSH)
					{
						push_dir = org - inflictor.origin;
						if (push_dir_z < 0)
							push_dir_z = 0;
						push_dir_z = push_dir_z + 110;
						if (vlen (push_dir) < 1)
							push_dir = '0 0 1';
						else
							push_dir = normalize (push_dir);
						head.velocity = head.velocity + push_dir * (460 + 840 * falloff);
						head.flags = head.flags - (head.flags & FL_ONGROUND);
					}
					if (head.classname == "monster_shambler" || head.classname == "monster_hell_knight2")
						T_Damage (head, inflictor, attacker, (points * 0.65));
					else
						T_Damage (head, inflictor, attacker, points);
				}
			}
		}
		head = head.chain;
	}

	while (cars != world)
	{
		nxt = cars.mmt_boom_next;
		cars.mmt_boom_next = world;
		Traffic_BlastExplode (cars, attacker);
		cars = nxt;
	}
};

// ---------------------------------------------------------------- Spare Wheel & Shrapnel Debris

void() MMT_DebrisRemove =
{
	if (mmt_debris_count > 0)
		mmt_debris_count = mmt_debris_count - 1;
	remove (self);
};

void() MMT_PruneDebris =
{
	local entity e, oldest;

	if (mmt_debris_count < 36)
		return;
	oldest = world;
	e = find (world, classname, "mmt_debris");
	while (e != world)
	{
		if (oldest == world || e.mmt_born < oldest.mmt_born)
			oldest = e;
		e = find (e, classname, "mmt_debris");
	}
	if (oldest != world)
	{
		remove (oldest);
		if (mmt_debris_count > 0)
			mmt_debris_count = mmt_debris_count - 1;
	}
};

void(entity e, float spd) MMT_TireSound =
{
	local float k, vol;

	vol = bound (0.45, spd / 500, 1.0);
	k = floor (random () * 3);
	if (k == 0)
		sound7 (e, CHAN_AUTO, "megaman/tire1.wav", vol, 0.85, 88 + random () * 28);
	else if (k == 1)
		sound7 (e, CHAN_AUTO, "megaman/tire2.wav", vol, 0.85, 88 + random () * 28);
	else
		sound7 (e, CHAN_AUTO, "megaman/tire3.wav", vol, 0.85, 88 + random () * 28);
};

void() MMT_DebrisTouch =
{
	local float v;

	if (other.takedamage)
		return;
	v = vlen (self.velocity);
	if (time < self.mmt_bouncetime + 0.24 || v < 65)
		return;
	self.mmt_bouncetime = time;
	self.mmt_bounces = self.mmt_bounces + 1;
	if (self.mmt_roll_yaw >= 0)
		MMT_TireSound (self, v);
	else
	{
		if (mmt_fx_sparks > 0)
			pointparticles (mmt_fx_sparks, self.origin, '0 0 60', 1);
		if (random () < 0.5)
			sound7 (self, CHAN_AUTO, "weapons/tink1.wav", 0.75, 1.1, 88 + random () * 36);
		else
			sound7 (self, CHAN_AUTO, "weapons/ric2.wav", 0.65, 1.1, 96 + random () * 36);
	}
};

void() MMT_WheelDebrisThink =
{
	local float dt, age, rem, step, f, ndot;
	local vector fwd, next_xy, refl;

	dt = 0.04;
	self.nextthink = time + dt;
	age = time - self.mmt_born;
	if (age >= self.mmt_life || pointcontents (self.origin) == CONTENT_SKY)
	{
		MMT_DebrisRemove ();
		return;
	}
	rem = self.mmt_life - age;
	if (rem < 0.6)
		self.alpha = max (0.05, rem / 0.6);

	if (self.mmt_roll_state == 0)
	{
		self.angles_x = 0;
		self.mmt_wheel_dist = self.mmt_wheel_dist + 16;
		f = self.mmt_wheel_dist / 10.05;
		self.frame = floor (f - 16 * floor (f / 16));
		if (vlen (self.velocity) > 35)
			self.mmt_roll_yaw = vectoyaw (self.velocity);
		self.angles_y = self.mmt_roll_yaw;
		self.mmt_lean = bound (-42, self.mmt_lean + self.mmt_side * 50 * dt, 42);
		self.angles_z = self.mmt_lean;

		if ((self.flags & FL_ONGROUND) || (self.mmt_bounces >= 2 && fabs (self.velocity_z) < 90))
		{
			traceline (self.origin + '0 0 28', self.origin - '0 0 38', TRUE, self);
			if (trace_fraction < 1 && trace_plane_normal_z > 0.7)
			{
				self.mmt_roll_state = 1;
				self.movetype = MOVETYPE_NONE;
				self.avelocity = '0 0 0';
				self.mmt_roll_spd = bound (160, vlen (self.velocity - '0 0 1' * self.velocity_z), 340);
				self.velocity = '0 0 0';
				self.mmt_lean = self.mmt_side * (18 + random () * 14);
				setorigin (self, trace_endpos + '0 0 25.6');
			}
		}
		return;
	}

	if (self.mmt_roll_spd > 4)
	{
		step = self.mmt_roll_spd * dt;
		makevectors ('0 1 0' * self.mmt_roll_yaw);
		fwd = v_forward;

		traceline (self.origin + '0 0 6', self.origin + '0 0 6' + fwd * (step + 26), TRUE, self);
		if (trace_fraction < 1 && trace_plane_normal_z < 0.65)
		{
			ndot = fwd * trace_plane_normal;
			refl = fwd - trace_plane_normal * (2 * ndot);
			self.mmt_roll_yaw = vectoyaw (refl);
			self.mmt_roll_spd = self.mmt_roll_spd * 0.75;
			MMT_TireSound (self, self.mmt_roll_spd);
			makevectors ('0 1 0' * self.mmt_roll_yaw);
			fwd = v_forward;
			step = self.mmt_roll_spd * dt;
		}

		next_xy = self.origin + fwd * step;
		traceline (next_xy + '0 0 32', next_xy - '0 0 46', TRUE, self);
		if (trace_fraction == 1)
		{
			self.mmt_roll_state = 0;
			self.movetype = MOVETYPE_BOUNCE;
			self.flags = self.flags - (self.flags & FL_ONGROUND);
			self.mmt_bounces = 1;
			self.velocity = fwd * self.mmt_roll_spd + '0 0 -20';
			return;
		}
		setorigin (self, trace_endpos + '0 0 25.6');
		self.mmt_wheel_dist = self.mmt_wheel_dist + step;
		f = self.mmt_wheel_dist / 10.05;
		self.frame = floor (f - 16 * floor (f / 16));
		self.mmt_roll_yaw = MMT_NormYaw (self.mmt_roll_yaw - self.mmt_lean * 0.16);
		self.mmt_roll_spd = max (0, self.mmt_roll_spd * 0.968 - 2.0);
		self.angles_x = 0;
		self.angles_y = self.mmt_roll_yaw;
		self.angles_z = self.mmt_lean;
	}
	else
	{
		self.angles_z = MMT_Approach (self.angles_z, self.mmt_side * 86, 120 * dt);
		traceline (self.origin + '0 0 18', self.origin - '0 0 32', TRUE, self);
		if (trace_fraction < 1)
			setorigin (self, trace_endpos + '0 0 9');
	}
};

void(vector org, vector vel, float side_dir, float life) MMT_SpawnWheelDebris =
{
	local entity w;

	MMT_PruneDebris ();
	w = spawn ();
	w.classname = "mmt_debris";
	w.movetype = MOVETYPE_BOUNCE;
	w.solid = SOLID_TRIGGER;
	w.bouncefactor = 0.62;
	w.bouncestop = 0.08;
	w.alpha = 1;
	w.velocity = vel;
	w.mmt_roll_yaw = vectoyaw (vel);
	w.mmt_roll_state = 0;
	w.mmt_side = side_dir;
	w.mmt_lean = side_dir * 12;
	w.mmt_born = time;
	w.mmt_life = life;
	w.touch = MMT_DebrisTouch;
	w.think = MMT_WheelDebrisThink;
	w.nextthink = time + 0.04;
	setmodel (w, "progs/mm_tank_wheel_debris.md3");
	setsize (w, '-18 -18 -18', '18 18 18');
	setorigin (w, org);
	mmt_debris_count = mmt_debris_count + 1;
};

void() MMT_ShrapThink =
{
	local float age, rem;

	age = time - self.mmt_born;
	if (age >= self.mmt_life || pointcontents (self.origin) == CONTENT_SKY)
	{
		MMT_DebrisRemove ();
		return;
	}
	rem = self.mmt_life - age;
	if (rem < 0.5)
		self.alpha = max (0.05, rem / 0.5);
	if (self.flags & FL_ONGROUND)
		self.avelocity = '0 0 0';
	self.nextthink = time + 0.08;
};

void(string mdl, vector org, vector vel, float life) MMT_SpawnShrap =
{
	local entity d;

	MMT_PruneDebris ();
	d = spawn ();
	d.classname = "mmt_debris";
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_TRIGGER;
	d.bouncefactor = 0.46;
	d.bouncestop = 0.08;
	d.alpha = 1;
	d.velocity = vel;
	d.avelocity_x = crandom () * 620;
	d.avelocity_y = crandom () * 620;
	d.avelocity_z = crandom () * 620;
	d.angles_y = random () * 360;
	d.mmt_roll_yaw = -1;
	d.mmt_born = time;
	d.mmt_life = life;
	d.touch = MMT_DebrisTouch;
	d.think = MMT_ShrapThink;
	d.nextthink = time + 0.06;
	setmodel (d, mdl);
	setsize (d, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (d, org);
	mmt_debris_count = mmt_debris_count + 1;
};

void() MMT_ShockRingThink =
{
	self.mmt_anim_t = self.mmt_anim_t + 1;
	if (self.mmt_anim_t >= 10)
	{
		remove (self);
		return;
	}
	self.frame = bound (0, floor (self.mmt_anim_t * 0.65), 6);
	self.scale = 2.4 + self.mmt_anim_t * 1.15;
	self.alpha = bound (0.05, 0.92 - self.mmt_anim_t * 0.09, 1.0);
	self.nextthink = time + 0.055;
};

void(vector org, float ring_sc, float spr_sc) MMT_SpawnBlastVisuals =
{
	local entity e, ring;

	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, org_x);
	WriteCoord (MSG_BROADCAST, org_y);
	WriteCoord (MSG_BROADCAST, org_z);

	e = spawn ();
	e.classname = "mmt_explod";
	e.movetype = MOVETYPE_NOCLIP;
	e.solid = SOLID_NOT;
	e.velocity = '0 0 85';
	e.scale = spr_sc;
	e.alpha = 0.95;
	e.frame = 0;
	setmodel (e, "progs/s_explodbig.spr");
	setsize (e, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (e, org + '0 0 16');
	e.think = exploderun;
	e.nextthink = time + 0.05;

	ring = spawn ();
	ring.classname = "mmt_ring";
	ring.movetype = MOVETYPE_NONE;
	ring.solid = SOLID_NOT;
	ring.scale = ring_sc;
	ring.alpha = 0.92;
	ring.frame = 0;
	ring.mmt_anim_t = 0;
	setmodel (ring, "progs/ring_shockwave.mdl");
	setsize (ring, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (ring, org + '0 0 10');
	ring.think = MMT_ShockRingThink;
	ring.nextthink = time + 0.05;
};

// ---------------------------------------------------------------- Silver Bar Projectile & Explosion

void(vector boom_org, entity bar_ent, entity hit) MMT_BarDetonate =
{
	local entity atk, tank, inf;
	local float i, ang, hspd, pack, ddmg;
	local vector v;

	tank = bar_ent.mmt_tank;
	atk = bar_ent.mmt_driver;
	if (atk == world)
		atk = tank;
	if (atk == world)
		atk = bar_ent;

	if (hit != world && hit != tank && hit != atk)
	{
		if (hit.classname == "misc_traffic_car")
			Traffic_BlastExplode (hit, atk);
		else if (hit.takedamage)
		{
			ddmg = MMT_BAR_DIRECT;
			if (hit.veh_kind > 0 || hit.classname == "veh_van_clip")
			{
				if (ddmg < 600)
					ddmg = 600;
			}
			mmt_inflicting = 1;
			T_Damage (hit, bar_ent, atk, ddmg);
			mmt_inflicting = 0;
		}
	}

	if (mmt_fx_bar_boom > 0)
		pointparticles (mmt_fx_bar_boom, boom_org, VEC_ORIGIN, 1);
	MMT_SpawnBlastVisuals (boom_org, 2.4, 2.2);

	pack = MMT_ClampPack (autocvar_mm_tank_soundpack);
	inf = spawn ();
	inf.classname = "mm_tank_bar";
	setorigin (inf, boom_org);
	sound (inf, CHAN_WEAPON, MMT_PickBoomSound (pack), 1.0, 0.20);
	sound (inf, CHAN_AUTO, "weapons/explodedist.wav", 0.90, 0.25);
	sound (inf, CHAN_VOICE, "weapons/r_exp3.wav", 0.85, 0.35);

	mmt_inflicting = 1;
	MMT_RadiusBlast (inf, atk, MMT_BAR_DMG, 320, hit, tank);
	mmt_inflicting = 0;
	remove (inf);

	MMT_ShakePlayers (boom_org, 900, 9.0);

	// Flying spare wheel wreckage + shrapnel
	i = 0;
	while (i < 3)
	{
		ang = random () * 360;
		hspd = 190 + random () * 210;
		v = '0 0 0';
		v_x = MMT_Cos (ang) * hspd;
		v_y = MMT_Sin (ang) * hspd;
		v_z = 260 + random () * 220;
		if (i & 1)
			MMT_SpawnWheelDebris (boom_org + '0 0 18', v, 1, 7.5 + random () * 2.0);
		else
			MMT_SpawnWheelDebris (boom_org + '0 0 18', v, -1, 7.5 + random () * 2.0);
		i = i + 1;
	}
	i = 0;
	while (i < 5)
	{
		ang = random () * 360;
		hspd = 220 + random () * 290;
		v = '0 0 0';
		v_x = MMT_Cos (ang) * hspd;
		v_y = MMT_Sin (ang) * hspd;
		v_z = 250 + random () * 260;
		if ((i & 3) == 0) MMT_SpawnShrap ("progs/mm_frag1.md3", boom_org + '0 0 14', v, 6.5);
		else if ((i & 3) == 1) MMT_SpawnShrap ("progs/mm_frag2.md3", boom_org + '0 0 14', v, 6.5);
		else if ((i & 3) == 2) MMT_SpawnShrap ("progs/mm_frag3.md3", boom_org + '0 0 14', v, 6.5);
		else MMT_SpawnShrap ("progs/mm_frag4.md3", boom_org + '0 0 14', v, 6.5);
		i = i + 1;
	}

	remove (bar_ent);
};

void() MMT_BarTouch =
{
	local vector org;

	if (other == self.owner || other == self.mmt_tank || (other.mmt_base != world && other.mmt_base == self.mmt_tank))
		return;
	if (other == self.mmt_driver && time < self.mmt_born + 0.25)
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}

	org = self.origin;
	if (vlen (self.velocity) > 1)
		org = org - normalize (self.velocity) * 10;
	MMT_BarDetonate (org, self, other);
};

void() MMT_BarThink =
{
	local vector da;
	local float idx;

	if (time >= self.mmt_born + 6.0 || pointcontents (self.origin) == CONTENT_SKY)
	{
		if (pointcontents (self.origin) == CONTENT_SKY)
			remove (self);
		else
			MMT_BarDetonate (self.origin, self, world);
		return;
	}
	if (vlen (self.velocity) > 10)
	{
		da = vectoangles (self.velocity);
		if (da_x > 180)
			da_x = da_x - 360;
		self.angles = da;
	}
	idx = floor ((time - self.mmt_born) * 20);
	idx = idx - 8 * floor (idx / 8);
	self.frame = idx;
	self.nextthink = time + 0.04;
};

// Trace the 3rd-person chase camera ray starting forward of the tank plane so walls/props
// behind the tank never hijack the aim; stores computed cam_des into vd_hitpos as well.
vector(entity p, entity tank) MMT_GetCrosshairTarget =
{
	local float dist_back, lift_up, start_dist, step;
	local vector look_ang, pivot, cam_des, p0, aim_end;

	look_ang = '0 0 0';
	look_ang_x = p.v_angle_x;
	look_ang_y = p.v_angle_y;
	makevectors (look_ang);

	pivot = tank.origin + '0 0 98';
	if (p.mmt_cam_mode)
	{
		dist_back = 385;
		lift_up = 58;
	}
	else
	{
		dist_back = 285;
		lift_up = 32;
	}
	cam_des = pivot - v_forward * dist_back + v_right * 24 + '0 0 1' * lift_up;
	traceline (pivot, cam_des, TRUE, tank);
	if (trace_fraction < 1)
		cam_des = trace_endpos + trace_plane_normal * 8;

	vd_hitpos = cam_des;

	start_dist = (pivot - cam_des) * v_forward;
	if (start_dist < 0)
		start_dist = 0;
	p0 = cam_des + v_forward * start_dist;
	aim_end = p0 + v_forward * 8192;
	step = 0;
	while (step < 4)
	{
		traceline (p0, aim_end, FALSE, tank);
		if (trace_startsolid)
			return p0;
		if (trace_fraction >= 1)
			return aim_end;
		if (trace_ent == tank || trace_ent == p || (trace_ent != world && trace_ent.mmt_base == tank))
		{
			p0 = trace_endpos + v_forward * 8;
			step = step + 1;
		}
		else
			return trace_endpos;
	}
	return aim_end;
};

// Shared exact aim & trajectory sweep used by both live aiming line and MMT_FireBar.
// Updates tank turret yaw/pitch directly and populates mmt_aim_muz, mmt_aim_dir, mmt_aim_end.
void(entity tank, entity driver) MMT_CalcAim =
{
	local vector aim_pt, muz_pivot, raw_fwd, shot_ang, aim_ang, fwd, step_pos;
	local float step;

	muz_pivot = tank.origin + '0 0 63';
	if (driver != world && driver.classname == "player")
	{
		aim_pt = MMT_GetCrosshairTarget (driver, tank);
		raw_fwd = aim_pt - muz_pivot;
		if (vlen (raw_fwd) < 1)
		{
			aim_ang = '0 0 0';
			aim_ang_x = driver.v_angle_x;
			aim_ang_y = driver.v_angle_y;
			makevectors (aim_ang);
			raw_fwd = v_forward;
		}
		else
			raw_fwd = normalize (raw_fwd);

		shot_ang = vectoangles (raw_fwd);
		if (shot_ang_x > 180)
			shot_ang_x = shot_ang_x - 360;
		tank.mmt_turret_yaw = MMT_NormYaw (shot_ang_y);
		tank.mmt_turret_pitch = bound (-82, shot_ang_x, 75);
	}

	aim_ang = '0 0 0';
	aim_ang_x = 0 - tank.mmt_turret_pitch;
	aim_ang_y = tank.mmt_turret_yaw;
	makevectors (aim_ang);
	fwd = v_forward;
	mmt_aim_dir = fwd;

	mmt_aim_instant = FALSE;
	mmt_aim_hit = world;

	// Sweep the projectile's actual 24x24x24 bbox out to the 88u muzzle tip
	tracebox (muz_pivot, '-12 -12 -12', '12 12 12', muz_pivot + fwd * 88, FALSE, tank);
	if (trace_fraction < 1 && trace_ent != driver && (trace_ent == world || trace_ent.mmt_base != tank))
	{
		if (trace_startsolid || trace_fraction * 88 < 28)
		{
			mmt_aim_instant = TRUE;
			mmt_aim_hit = trace_ent;
			if (trace_startsolid)
				mmt_aim_muz = muz_pivot + fwd * 24;
			else
				mmt_aim_muz = trace_endpos;
			mmt_aim_end = mmt_aim_muz;
			return;
		}
		mmt_aim_muz = trace_endpos - fwd * 2;
		mmt_aim_end = trace_endpos;
		return;
	}

	mmt_aim_muz = muz_pivot + fwd * 88;
	step_pos = mmt_aim_muz;
	step = 0;
	while (step < 4)
	{
		tracebox (step_pos, '-12 -12 -12', '12 12 12', mmt_aim_muz + fwd * 8192, FALSE, tank);
		if (trace_startsolid)
		{
			mmt_aim_end = step_pos;
			return;
		}
		if (trace_fraction >= 1)
		{
			mmt_aim_end = mmt_aim_muz + fwd * 8192;
			return;
		}
		if (trace_ent == tank || trace_ent == driver || (trace_ent != world && trace_ent.mmt_base == tank))
		{
			step_pos = trace_endpos + fwd * 8;
			step = step + 1;
		}
		else
		{
			mmt_aim_end = trace_endpos;
			return;
		}
	}
	mmt_aim_end = mmt_aim_muz + fwd * 8192;
};

void(entity tank, entity driver) MMT_FireBar =
{
	local vector muz, dir;
	local entity bar, hit_ent;
	local float pack, instant_boom;

	MMT_CalcAim (tank, driver);
	muz = mmt_aim_muz;
	dir = mmt_aim_dir;
	instant_boom = mmt_aim_instant;
	hit_ent = mmt_aim_hit;

	bar = spawn ();
	bar.classname = "mm_tank_bar";
	bar.owner = tank;
	bar.mmt_tank = tank;
	bar.mmt_driver = driver;
	bar.movetype = MOVETYPE_FLYMISSILE;
	bar.solid = SOLID_BBOX;
	bar.velocity = dir * MMT_BAR_SPEED;
	bar.angles = vectoangles (bar.velocity);
	if (bar.angles_x > 180)
		bar.angles_x = bar.angles_x - 360;
	bar.mmt_born = time;
	bar.traileffectnum = mmt_fx_bar_trail;
	bar.touch = MMT_BarTouch;
	bar.think = MMT_BarThink;
	bar.nextthink = time + 0.04;
	setmodel (bar, "progs/mm_tank_bar.md3");
	setsize (bar, '-12 -12 -12', '12 12 12');
	setorigin (bar, muz);

	tank.mmt_recoil_end = time + 0.60;
	tank.mmt_reload_start = time;
	tank.mmt_reload_end = time + MMT_RELOAD_TIME;
	tank.mmt_reload_snd1 = FALSE;
	tank.mmt_reload_snd2 = FALSE;
	tank.mmt_reload_lock_snd = FALSE;
	tank.mmt_reload_spk_t = time + 0.65;

	pack = MMT_ClampPack (autocvar_mm_tank_soundpack);
	sound (tank, CHAN_WEAPON, MMT_Snd (pack, 2), 1.0, 0.25);
	sound (tank, CHAN_AUTO, "weapons/r_exp3.wav", 0.72, 0.40);

	if (instant_boom)
		MMT_BarDetonate (muz, bar, hit_ent);
};

// ---------------------------------------------------------------- Driving Physics & Collision

float(entity tank, vector org0, vector org1) MMT_DriveSweep =
{
	local float i, ang, best;
	local vector ofs, p0, p1;

	best = 1;
	i = 0;
	while (i < 12)
	{
		ang = i * 30;
		ofs = '0 0 0';
		ofs_x = MMT_Cos (ang) * 82;
		ofs_y = MMT_Sin (ang) * 82;
		p0 = org0 + ofs + '0 0 26';
		p1 = org1 + ofs + '0 0 26';
		tracebox (p0, '-12 -12 0', '12 12 106', p1, FALSE, tank);
		if (!trace_startsolid && trace_fraction < best && trace_plane_normal_z < 0.7)
		{
			if (trace_ent == world || (trace_ent != tank.mmt_driver && trace_ent.mmt_base != tank))
			{
				best = trace_fraction;
				vd_hitnorm = trace_plane_normal;
				vd_hitpos = trace_endpos;
				vd_hitent = trace_ent;
			}
		}
		i = i + 1;
	}
	if (best >= 1)
		return TRUE;
	vd_hitnorm_z = 0;
	if (vlen (vd_hitnorm) < 0.01)
		vd_hitnorm = normalize (org0 - org1);
	vd_hitnorm = normalize (vd_hitnorm);
	return FALSE;
};

void(entity tank, vector org, float yaw) MMT_GroundSample =
{
	local float i, wx, wy, c, s, sum, mask, have0, h0, h1, h2, h3, hf, hr, hh;
	local vector p, q;

	c = MMT_Cos (yaw);
	s = MMT_Sin (yaw);
	vd_found = 0;
	sum = 0;
	mask = 0;
	h0 = 0; h1 = 0; h2 = 0; h3 = 0;
	i = 0;
	while (i < 4)
	{
		if (i < 2)
			wx = 52;
		else
			wx = -52;
		if (i == 0 || i == 2)
			wy = 76;
		else
			wy = -76;
		p = org;
		p_x = org_x + c * wx - s * wy;
		p_y = org_y + s * wx + c * wy;
		p_z = org_z + 32;
		q = p;
		q_z = org_z - 64;
		traceline (p, q, 3, tank);
		if (!trace_startsolid && trace_fraction < 1 && trace_plane_normal_z > 0.5)
		{
			hh = trace_endpos_z;
			vd_found = vd_found + 1;
			sum = sum + hh;
			if (i == 0) { h0 = hh; mask = mask + 1; }
			else if (i == 1) { h1 = hh; mask = mask + 2; }
			else if (i == 2) { h2 = hh; mask = mask + 4; }
			else { h3 = hh; mask = mask + 8; }
		}
		i = i + 1;
	}
	if (vd_found == 0)
		return;
	have0 = sum / vd_found - 32;
	if (!(mask & 1)) h0 = have0;
	if (!(mask & 2)) h1 = have0;
	if (!(mask & 4)) h2 = have0;
	if (!(mask & 8)) h3 = have0;
	hf = (h0 + h1) * 0.5;
	hr = (h2 + h3) * 0.5;
	vd_gh = (h0 + h1 + h2 + h3) * 0.25 + 0.5;
	vd_pitch = bound (-32, MMT_RiseAngle (hf - hr, 104), 32);
};

void(entity tank, entity hit, float spd, float runover) MMT_RamHit =
{
	local entity atk;
	local float dmg;
	local vector dir;

	if (spd < 35 || time < hit.mmt_hit_t)
		return;
	if (hit == tank.mmt_driver)
		return;
	atk = tank.mmt_driver;
	if (atk == world)
		atk = tank;
	dir = tank.velocity;
	dir_z = 0;
	if (vlen (dir) < 1)
	{
		makevectors ('0 1 0' * tank.angles_y);
		dir = v_forward;
	}
	else
		dir = normalize (dir);
	if (hit.veh_kind > 0 || hit.classname == "veh_van_clip")
		dmg = 220 + spd * 1.4;
	else if (runover)
		dmg = spd * 1.75;	// from 0, no floor: same ~330 as before at top speed (190)
	else
		dmg = 160 + spd * 0.90;
	hit.mmt_hit_t = time + 0.30;
	if ((hit.flags & FL_CLIENT) || (hit.flags & FL_MONSTER))
	{
		hit.velocity = hit.velocity + dir * (280 + spd * 1.4) + '0 0 240';
		hit.flags = hit.flags - (hit.flags & FL_ONGROUND);
		sound7 (hit, CHAN_BODY, "megaman/tire1.wav", 1.0, 0.7, 82 + random () * 14);
	}
	mmt_inflicting = 3;
	T_Damage (hit, tank, atk, dmg);
	mmt_inflicting = 0;
};

void(entity tank) MMT_CheckRunOver =
{
	local entity e, hits, nxt;
	local float spd;
	local vector bmin, bmax;

	// real forward/reverse speed only: turning in place or creeping must not crush roof riders / side huggers
	spd = fabs (tank.mmt_fwd_spd);
	if (spd <= 120)
		return;

	// strictly inside the '-104 -104 0'..'104 104 132' hull, so touching a side is not a run-over
	bmin = tank.origin + '-100 -100 0';
	bmax = tank.origin + '100 100 128';
	hits = world;
	e = findradius (tank.origin + '0 0 48', 160);
	while (e != world)
	{
		if (e != tank && e != tank.mmt_driver && e.takedamage && ((e.flags & FL_CLIENT) || (e.flags & FL_MONSTER)))
		{
			if (e.absmin_z < tank.absmax_z - 4)	// skip players riding on the roof
			if (bmin_x < e.absmax_x && bmax_x > e.absmin_x && bmin_y < e.absmax_y && bmax_y > e.absmin_y && bmin_z < e.absmax_z && bmax_z > e.absmin_z)
			{
				e.mmt_run_next = hits;
				hits = e;
			}
		}
		e = e.chain;
	}

	// damage after the walk: a death that runs findradius would overwrite .chain
	while (hits != world)
	{
		nxt = hits.mmt_run_next;
		hits.mmt_run_next = world;
		if (!bm_wasfreed (tank) && tank.mmt_state != MMT_STATE_WRECK)
			MMT_RamHit (tank, hits, spd, TRUE);
		hits = nxt;
	}
};

// ---------------------------------------------------------------- Enter / Exit / Camera

void(entity tank, entity p, float forced) MMT_Leave =
{
	local vector exit_p;
	local float yaw_out;

	if (tank.mmt_driver == p)
		tank.mmt_driver = world;
	tank.mmt_fwd_spd = tank.mmt_fwd_spd * 0.2;
	tank.mmt_yawrate = 0;

	sound (tank, CHAN_BODY, "misc/null.wav", 1, ATTN_NORM);
	sound (tank, CHAN_ITEM, "misc/null.wav", 1, ATTN_NORM);

	if (p != world && p.classname == "player")
	{
		yaw_out = p.v_angle_y;
		p.mmt_tank = world;
		MMT_RestoreViewAndBody (p, tank);
		if (!forced)
		{
			exit_p = MMT_FindExitPos (tank, p);
			setorigin (p, exit_p);
			p.velocity = '0 0 0';
			p.angles = '0 0 0';
			p.angles_y = yaw_out;
			p.fixangle = TRUE;
			sound (tank, CHAN_AUTO, "items/itembk2.wav", 0.85, ATTN_NORM);
		}
	}
	else if (tank.mmt_cam != world)
	{
		remove (tank.mmt_cam);
		tank.mmt_cam = world;
	}
};

void(entity p, entity tank) MMT_Enter =
{
	local entity cam, oldself;
	local float pack;

	if (p.health <= 0 || MMTank_Driving (p) || EricCannon_Active (p) || p.veh_van != world || p.veh_ride != world || p.jb_vehicle != world || p.fd_head != world)
		return;
	if (tank.mmt_state == MMT_STATE_WRECK || tank.mmt_driver != world)
		return;

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

	tank.mmt_driver = p;
	p.mmt_tank = tank;
	p.mmt_btn = TRUE;
	p.mmt_oldmove = p.movetype;
	p.mmt_oldsolid = p.solid;

	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.velocity = '0 0 0';
	MMT_HidePlayer (p);
	setorigin (p, tank.origin + '0 0 72');

	p.angles = '0 0 0';
	p.angles_x = 12;
	p.angles_y = tank.mmt_turret_yaw;
	p.angles_z = 0;
	p.v_angle = p.angles;
	p.v_angle_z = 0;
	p.punchangle = '0 0 0';
	p.fixangle = TRUE;

	if (p.ishuman == 1)
	{
		cam = spawn ();
		cam.classname = "mmt_cam";
		cam.movetype = MOVETYPE_NONE;
		cam.solid = SOLID_NOT;
		cam.alpha = 0.01;
		cam.scale = 0.01;
		setmodel (cam, "progs/spike.mdl");
		setsize (cam, '0 0 0', '0 0 0');
		setorigin (cam, tank.origin + '0 0 130');
		tank.mmt_cam = cam;

		p.clientcamera = cam;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, cam);
		MMT_UpdateCameraAndAim (p, tank);
	}

	pack = MMT_ClampPack (autocvar_mm_tank_soundpack);
	sound (tank, CHAN_VOICE, MMT_Snd (pack, 5), 1.0, 0.30);
	tank.mmt_eng_t = time + 0.05;
	if (!p.mmt_hint_shown)
	{
		p.mmt_hint_shown = TRUE;
		centerprint (p, "MEGA MAN TANK\nW/S: Drive  A/D: Turn Hull  Mouse: Aim Turret\nFIRE: Silver Bar  SPACE: Horn/Brake  K: Cam  H: Exit");
	}
};

void(entity p, entity tank) MMT_UpdateCameraAndAim =
{
	local entity cam;
	local vector cam_des, line_start;

	MMT_CalcAim (tank, p);
	cam_des = vd_hitpos;
	cam = tank.mmt_cam;

	if (cam != world)
	{
		setorigin (cam, cam_des);
		cam.angles = '0 0 0';
		cam.angles_x = p.v_angle_x;
		cam.angles_y = p.v_angle_y;
		cam.angles_z = 0;
	}

	if (time >= tank.mmt_reload_end)
		p.mmt_st_active = 1;
	else
		p.mmt_st_active = 2;

	// Start the visual aiming line at the silver bar nose tip (or mmt_aim_muz when blocked closer)
	if (mmt_aim_instant)
		line_start = mmt_aim_muz;
	else
		line_start = tank.origin + '0 0 63' + mmt_aim_dir * 84;
	if ((mmt_aim_end - line_start) * mmt_aim_dir < 0)
		line_start = mmt_aim_muz;

	p.mmt_st_sx = line_start_x;
	p.mmt_st_sy = line_start_y;
	p.mmt_st_sz = line_start_z;
	p.mmt_st_ex = mmt_aim_end_x;
	p.mmt_st_ey = mmt_aim_end_y;
	p.mmt_st_ez = mmt_aim_end_z;
};

// ---------------------------------------------------------------- Anti-Rollover, Jump/Launch Pads & Air Physics

// Keep tank pitch upright/bounded and zero out roll so the hull can never tip over or flip upside-down
void(entity tank, float dt, float grounded, float target_pitch) MMT_StabilizeAngles =
{
	local float px, rate;

	px = tank.angles_x;
	while (px > 180)
		px = px - 360;
	while (px < -180)
		px = px + 360;
	if (grounded)
	{
		target_pitch = bound (-32, target_pitch, 32);
		rate = min (1, dt * 8);
	}
	else
	{
		target_pitch = 0;
		rate = min (1, dt * 4);
	}
	px = px + (target_pitch - px) * rate;
	tank.angles_x = bound (-32, px, 32);
	tank.angles_z = 0;
};

float(vector bmin, vector bmax, entity pad) MMT_OverlapPad =
{
	if (bmin_x > pad.absmax_x || bmax_x < pad.absmin_x)
		return FALSE;
	if (bmin_y > pad.absmax_y || bmax_y < pad.absmin_y)
		return FALSE;
	if (bmin_z > pad.absmax_z || bmax_z < pad.absmin_z)
		return FALSE;
	return TRUE;
};

// Tank uses MOVETYPE_NONE + setorigin, so engine SOLID_TRIGGER touch never fires for it;
// detect trigger_push jump pads and info_skypad launch pads directly by hull overlap.
void(entity tank, entity driver) MMT_CheckPads =
{
	local entity e;
	local vector bmin, bmax, v;
	local float spd, maxv;

	if (time < tank.mmt_pad_cool)
		return;
	// two find() walks over every entity: 20 Hz is plenty at <= 190 u/s
	if (time < tank.mmt_pad_scan_t)
		return;
	tank.mmt_pad_scan_t = time + 0.05;

	bmin = tank.origin + '-104 -104 -4';
	bmax = tank.origin + '104 104 132';

	e = find (world, classname, "info_skypad");
	while (e != world)
	{
		if (MMT_OverlapPad (bmin, bmax, e))
		{
			SkyPad_RaiseMaxVel ();
			if (driver != world && driver.ishuman == 1 && !driver.skypad_vel_sent)
			{
				driver.skypad_vel_sent = TRUE;
				stuffcmd (driver, "sv_maxvelocity 6500\n");
			}
			v = SkyPad_CalcVel (tank.origin + '0 0 2', e.pos1, e.height);
			tank.mmt_pad_cool = time + 0.65;
			tank.mmt_air = TRUE;
			tank.mmt_vz = v_z;
			tank.mmt_air_vel = v;
			tank.mmt_air_vel_z = 0;
			tank.mmt_has_air_vel = TRUE;
			setorigin (tank, tank.origin + '0 0 4');
			sound7 (tank, CHAN_AUTO, "skypad/launch.wav", 0.85, ATTN_NORM, SNDSPD * (0.96 + random () * 0.08));
			pointparticles (particleeffectnum ("TE_TELEPORT"), e.origin + '0 0 12', '0 0 0', 1);
			if (e.message != "" && driver != world && driver.ishuman == 1)
				sprint (driver, strcat ("Sky Pad -> ", e.message, "\n"));
			return;
		}
		e = find (e, classname, "info_skypad");
	}

	e = find (world, classname, "trigger_push");
	while (e != world)
	{
		if (MMT_OverlapPad (bmin, bmax, e))
		{
			spd = e.speed;
			if (!spd)
				spd = 1000;
			v = spd * e.movedir * 10;
			maxv = cvar ("sv_maxvelocity");
			if (maxv <= 0)
				maxv = 2000;
			v_x = bound (0 - maxv, v_x, maxv);
			v_y = bound (0 - maxv, v_y, maxv);
			v_z = bound (0 - maxv, v_z, maxv);

			tank.mmt_pad_cool = time + 0.35;
			tank.mmt_air_vel = v;
			tank.mmt_air_vel_z = 0;
			tank.mmt_has_air_vel = TRUE;
			if (v_z > 0)
			{
				tank.mmt_air = TRUE;
				tank.mmt_vz = v_z;
				setorigin (tank, tank.origin + '0 0 4');
			}
			if (!(e.spawnflags & NO_SOUND))
				sound7 (tank, CHAN_AUTO, "ambience/windfly.wav", 0.72, ATTN_NORM, SNDSPD * (0.95 + random () * 0.12));
			if (e.spawnflags & PUSH_ONCE)
				remove (e);
			return;
		}
		e = find (e, classname, "trigger_push");
	}
};

vector(entity tank, vector org1, float yaw1, float dt, float is_driven) MMT_StepVerticalAndGround =
{
	local float grav, dz, z, d;

	grav = cvar ("sv_gravity");
	if (grav <= 10)
		grav = 800;

	z = org1_z;
	if (tank.mmt_air)
	{
		tank.mmt_vz = tank.mmt_vz - grav * dt;
		dz = tank.mmt_vz * dt;
		if (dz > 0)
		{
			tracebox (org1, '-84 -84 0', '84 84 132', org1 + '0 0 1' * dz, TRUE, tank);
			if (trace_fraction < 1 || trace_startsolid)
			{
				z = trace_endpos_z;
				tank.mmt_vz = 0;
			}
			else
				z = z + dz;
		}
		else
			z = z + dz;
		org1_z = z;
		MMT_GroundSample (tank, org1, yaw1);
		if (vd_found && tank.mmt_vz <= 0 && z <= vd_gh + 2)
		{
			z = vd_gh;
			tank.mmt_vz = 0;
			tank.mmt_air = FALSE;
			tank.mmt_has_air_vel = FALSE;
			tank.mmt_air_vel = '0 0 0';
			if (is_driven)
				sound7 (tank, CHAN_AUTO, "megaman/tire2.wav", 0.9, 0.6, 72);
		}
	}
	else
	{
		MMT_GroundSample (tank, org1, yaw1);
		if (!vd_found)
			tank.mmt_air = TRUE;
		else
		{
			d = vd_gh - z;
			if (d < -18)
				tank.mmt_air = TRUE;
			else if (d > 0)
				z = z + d * min (1, dt * 18);
			else
				z = vd_gh;
		}
	}
	org1_z = z;
	MMT_StabilizeAngles (tank, dt, (vd_found && !tank.mmt_air), vd_pitch);
	return org1;
};

// ---------------------------------------------------------------- Per-Frame Player Control (`MMTank_DriveFrame`)

float() MMTank_DriveFrame =
{
	local entity tank;
	local float dt, thr, steer_in, target_spd, acc, yawrate_t, yaw0, yaw1, spd;
	local float pack, f, moving, brake_on, power;
	local vector fwd, org0, org1, org2, vel, n;

	tank = self.mmt_tank;
	if (tank == world)
		return FALSE;
	if (bm_wasfreed (tank) || tank.classname != "misc_mm_tank" || tank.mmt_driver != self || tank.mmt_state == MMT_STATE_WRECK || self.health <= 0)
	{
		self.mmt_tank = world;
		if (tank != world && !bm_wasfreed (tank))
			MMT_RestoreViewAndBody (self, tank);
		else
			MMT_RestoreViewAndBody (self, world);
		return FALSE;
	}

	if (self.impulse == 86)
	{
		self.impulse = 0;
		MMT_Leave (tank, self, FALSE);
		return TRUE;
	}
	if (self.impulse == 87)
	{
		self.impulse = 0;
		self.mmt_cam_mode = 1 - self.mmt_cam_mode;
	}
	if (self.impulse == 134 || self.impulse == 135)
		MMTank_Impulse ();
	self.impulse = 0;

	dt = bound (0.001, frametime, 0.05);
	MMT_HidePlayer (self);
	self.v_angle_z = 0;
	self.angles_z = 0;
	self.punchangle_z = 0;
	self.velocity = '0 0 0';
	self.flags = self.flags - (self.flags & FL_ONGROUND);
	if (!self.button0)
		self.mmt_btn = FALSE;

	thr = bound (-1, self.movement_x / 160, 1);
	steer_in = bound (-1, self.movement_y / 160, 1);
	brake_on = self.button2;

	pack = MMT_ClampPack (autocvar_mm_tank_soundpack);
	if (brake_on && time >= tank.mmt_horn_t)
	{
		tank.mmt_horn_t = time + 1.15;
		sound (tank, CHAN_VOICE, MMT_Snd (pack, 5), 1.0, 0.22);
	}

	if (tank.mmt_state == MMT_STATE_FIRE)
		power = 0.78;
	else
		power = 1.0;

	// Heavy hull yaw rotation (left/right via A/D)
	yawrate_t = (0 - steer_in) * MMT_TURN_RATE * power;
	tank.mmt_yawrate = MMT_Approach (tank.mmt_yawrate, yawrate_t, MMT_TURN_ACCEL * dt);
	yaw0 = tank.angles_y;
	yaw1 = MMT_NormYaw (yaw0 + tank.mmt_yawrate * dt);

	// Forward / reverse throttle & heavy acceleration
	if (brake_on || tank.mmt_air)
		target_spd = 0;
	else if (thr > 0)
		target_spd = thr * MMT_TOP_FWD * power;
	else if (thr < 0)
		target_spd = thr * MMT_TOP_REV * power;
	else
		target_spd = 0;

	if (brake_on)
		acc = MMT_BRAKE;
	else if (fabs (target_spd) < fabs (tank.mmt_fwd_spd) || target_spd * tank.mmt_fwd_spd < 0)
	{
		if (thr == 0)
			acc = MMT_COAST;
		else
			acc = MMT_BRAKE;
	}
	else
		acc = MMT_ACCEL;
	tank.mmt_fwd_spd = MMT_Approach (tank.mmt_fwd_spd, target_spd, acc * dt);

	MMT_CheckPads (tank, self);
	if (!tank.mmt_air && tank.mmt_has_air_vel && time >= tank.mmt_pad_cool)
	{
		tank.mmt_has_air_vel = FALSE;
		tank.mmt_air_vel = '0 0 0';
	}

	makevectors ('0 1 0' * yaw1);
	fwd = v_forward;
	if (tank.mmt_has_air_vel)
		vel = tank.mmt_air_vel;
	else
		vel = fwd * tank.mmt_fwd_spd;

	// Sweep tank footprint; slide along walls & ram targets
	org0 = tank.origin;
	org1 = org0;
	org1_x = org0_x + vel_x * dt;
	org1_y = org0_y + vel_y * dt;
	if (!MMT_DriveSweep (tank, org0, org1))
	{
		n = vd_hitnorm;
		if (vd_hitent != world && vd_hitent.takedamage)
			MMT_RamHit (tank, vd_hitent, max (fabs (tank.mmt_fwd_spd), vlen (vel)), FALSE);
		if (tank.mmt_state == MMT_STATE_WRECK)
			return TRUE;
		if (vel * n < 0)
			vel = vel - n * (vel * n);
		org2 = org0;
		org2_x = org0_x + vel_x * dt;
		org2_y = org0_y + vel_y * dt;
		if (MMT_DriveSweep (tank, org0, org2))
		{
			org1 = org2;
			if (tank.mmt_has_air_vel)
				tank.mmt_air_vel = vel;
		}
		else
		{
			org1 = org0;
			tank.mmt_fwd_spd = tank.mmt_fwd_spd * 0.25;
			if (tank.mmt_has_air_vel)
				tank.mmt_air_vel = '0 0 0';
		}
	}

	// Ground height, jump/launch pad arcs & anti-rollover stabilization
	org1 = MMT_StepVerticalAndGround (tank, org1, yaw1, dt, TRUE);
	tank.angles_y = yaw1;
	tank.velocity = vel;
	if (tank.mmt_air)
		tank.velocity_z = tank.mmt_vz;
	setorigin (tank, org1);
	setsize (tank, '-104 -104 0', '104 104 132');
	MMT_CheckRunOver (tank);

	// Hull animation frames (0..15 idle, 16..31 wheel spin, 32..39 recoil, 40..47 flinch)
	spd = fabs (tank.mmt_fwd_spd);
	moving = (spd > 8 || fabs (tank.mmt_yawrate) > 8);
	if (time < tank.mmt_flinch_end)
	{
		f = floor ((0.36 - (tank.mmt_flinch_end - time)) * 22.0);
		tank.frame = 40 + bound (0, f, 7);
	}
	else if (time < tank.mmt_recoil_end)
	{
		f = floor ((0.60 - (tank.mmt_recoil_end - time)) * 13.3);
		tank.frame = 32 + bound (0, f, 7);
	}
	else if (moving)
	{
		tank.mmt_wheel_dist = tank.mmt_wheel_dist + (tank.mmt_fwd_spd * dt) + tank.mmt_yawrate * 0.35 * dt;
		f = floor (tank.mmt_wheel_dist / 24.74);
		f = f - 16 * floor (f / 16);
		tank.frame = 16 + f;
	}
	else
	{
		tank.mmt_anim_t = tank.mmt_anim_t + dt * 10;
		f = floor (tank.mmt_anim_t);
		tank.frame = f - 16 * floor (f / 16);
	}

	// Loud layered engine & heavy wheel rolling audio
	if (time >= tank.mmt_eng_t)
	{
		tank.mmt_eng_t = time + 1.15;
		sound7 (tank, CHAN_BODY, MMT_Snd (pack, 0), 0.90, 0.32, 95 + (spd / MMT_TOP_FWD) * 22);
	}
	if (moving && time >= tank.mmt_move_t)
	{
		tank.mmt_move_t = time + 1.12;
		sound7 (tank, CHAN_ITEM, MMT_Snd (pack, 1), bound (0.55, 0.55 + spd / MMT_TOP_FWD * 0.45, 1.0), 0.28, 90 + (spd / MMT_TOP_FWD) * 25);
	}

	// Independent aiming & 3rd-person chase camera
	MMT_UpdateCameraAndAim (self, tank);
	MMT_SyncAttachments (tank);
	setorigin (self, tank.origin + '0 0 72');

	// Fire silver bar on MOUSE1 when reload complete
	if (self.button0 && !self.mmt_btn && time >= tank.mmt_reload_end)
	{
		self.mmt_btn = TRUE;
		MMT_FireBar (tank, self);
	}
	return TRUE;
};

// ---------------------------------------------------------------- Tank Damage, Fire State, Catastrophic Boom & Respawn

void(entity tank, entity attacker) MMT_StartFire =
{
	if (tank.mmt_state != MMT_STATE_IDLE)
		return;
	tank.mmt_state = MMT_STATE_FIRE;
	tank.skin = 1;
	tank.mmt_fx_t = time;
	tank.mmt_smoke_t = time;
	tank.mmt_fire_snd_t = time;
	if (attacker != world && attacker.classname == "player")
		tank.mmt_igniter = attacker;
	sound (tank, CHAN_AUTO, "vehicles/clang2.wav", 0.95, 0.45);
};

void(entity tank, entity atk) MMT_EjectOrKillDriver =
{
	local entity p, inf;
	local vector out_vel;

	p = tank.mmt_driver;
	if (p == world)
		return;
	MMT_Leave (tank, p, TRUE);
	if (p.classname != "player")
		return;

	setorigin (p, tank.origin + '0 0 64');
	out_vel = '0 0 260' + ('1 0 0' * crandom () + '0 1 0' * crandom ()) * 240;
	p.velocity = out_vel;
	p.flags = p.flags - (p.flags & FL_ONGROUND);

	if (p.health > 0 && !(p.flags & FL_GODMODE) && p.invincible_finished < time)
	{
		inf = spawn ();
		inf.classname = "mm_tank_blast";
		setorigin (inf, tank.origin + '0 0 32');
		mmt_inflicting = 2;
		if (atk != world)
			T_Damage (p, inf, atk, 50000);
		else
			T_Damage (p, inf, inf, 50000);
		mmt_inflicting = 0;
		remove (inf);
	}
};

void(entity tank, float forced) MMT_CatastrophicExplode =
{
	local entity atk, inf;
	local float i, ang, hspd, pack;
	local vector org, v;

	if (tank.mmt_state == MMT_STATE_WRECK)
		return;
	tank.mmt_state = MMT_STATE_WRECK;
	tank.takedamage = DAMAGE_NO;
	tank.solid = SOLID_NOT;
	tank.skin = 1;
	tank.frame = 0;
	tank.velocity = '0 0 0';

	atk = tank.mmt_igniter;
	if (atk == world)
		atk = tank;

	MMT_EjectOrKillDriver (tank, atk);

	if (tank.mmt_turret != world)
		tank.mmt_turret.effects = tank.mmt_turret.effects | EF_NODRAW;
	if (tank.mmt_wheelman != world)
		tank.mmt_wheelman.effects = tank.mmt_wheelman.effects | EF_NODRAW;
	if (tank.mmt_bar_prop != world)
		tank.mmt_bar_prop.effects = tank.mmt_bar_prop.effects | EF_NODRAW;

	org = tank.origin + '0 0 34';
	if (mmt_fx_catastrophic > 0)
		pointparticles (mmt_fx_catastrophic, org, VEC_ORIGIN, 1);
	MMT_SpawnBlastVisuals (org, 3.2, 2.8);

	pack = MMT_ClampPack (autocvar_mm_tank_soundpack);
	sound (tank, CHAN_WEAPON, MMT_PickBoomSound (pack), 1.0, 0.15);
	sound (tank, CHAN_AUTO, "weapons/explodedist.wav", 1.0, 0.20);
	sound (tank, CHAN_VOICE, "weapons/r_exp3.wav", 0.90, 0.30);

	inf = spawn ();
	inf.classname = "mm_tank_blast";
	setorigin (inf, org);
	mmt_inflicting = 2;
	MMT_RadiusBlast (inf, atk, 220, 340, tank, world);
	mmt_inflicting = 0;
	remove (inf);

	MMT_ShakePlayers (org, 1300, 14.0);

	// Flying tank bar + shrapnel (no tank wheels in explosion)
	MMT_SpawnShrap ("progs/mm_tank_bar.md3", org + '0 0 24', '0 0 480' + ('1 0 0' * crandom () + '0 1 0' * crandom ()) * 240, 8.5);
	i = 0;
	while (i < 8)
	{
		ang = random () * 360;
		hspd = 240 + random () * 340;
		v = '0 0 0';
		v_x = MMT_Cos (ang) * hspd;
		v_y = MMT_Sin (ang) * hspd;
		v_z = 290 + random () * 290;
		if ((i & 3) == 0) MMT_SpawnShrap ("progs/mm_frag1.md3", org, v, 8.0);
		else if ((i & 3) == 1) MMT_SpawnShrap ("progs/mm_frag2.md3", org, v, 8.0);
		else if ((i & 3) == 2) MMT_SpawnShrap ("progs/mm_frag3.md3", org, v, 8.0);
		else MMT_SpawnShrap ("progs/mm_frag4.md3", org, v, 8.0);
		i = i + 1;
	}

	tank.mmt_wreck_t = time + 12.0;
	tank.mmt_respawn_t = time + max (10, autocvar_mm_tank_respawn);
	tank.mmt_fx_t = time + 0.5;
	tank.think = MMT_Think;
	tank.nextthink = time + 0.2;
};

void(entity attacker, float take) MMT_Pain =
{
	if (self.mmt_state == MMT_STATE_WRECK)
		return;
	if (attacker != world && attacker.classname == "player")
		self.mmt_igniter = attacker;
	self.mmt_flinch_end = time + 0.36;
	if (time >= self.mmt_pain_snd_t)
	{
		self.mmt_pain_snd_t = time + 0.14;
		if (mmt_fx_sparks > 0)
			pointparticles (mmt_fx_sparks, self.origin + '0 0 42', '0 0 50', 1);
		if (random () < 0.5)
			sound7 (self, CHAN_AUTO, "vehicles/hit_metal1.wav", 0.90, 0.65, 92 + random () * 18);
		else
			sound7 (self, CHAN_AUTO, "vehicles/hit_metal2.wav", 0.90, 0.65, 92 + random () * 18);
	}
	if (self.mmt_state == MMT_STATE_IDLE && self.health <= self.max_health * 0.40)
		MMT_StartFire (self, attacker);
};

void() MMT_Die =
{
	if (self.mmt_state == MMT_STATE_WRECK)
		return;
	if (damage_attacker != world && damage_attacker.classname == "player")
		self.mmt_igniter = damage_attacker;
	// Defer detonation by 1 frame so we never mutate findradius .chain during T_RadiusDamage
	self.health = 1;
	self.takedamage = DAMAGE_NO;
	self.mmt_cook_t = -1;
	self.think = MMT_Think;
	self.nextthink = time;
};

// ---------------------------------------------------------------- Main Tank Think & Respawn

void(entity tank, float is_temp) MMT_InitTank =
{
	local entity tur, wm, bp;
	local float v, hp;

	MMTank_Precache ();
	mmt_has_tanks = TRUE;

	v = MMT_ClampVariant (autocvar_mm_tank_variant);
	hp = autocvar_mm_tank_hp;
	if (hp < 100)
		hp = 600;

	tank.classname = "misc_mm_tank";
	tank.netname = "Mega Man Tank";
	tank.mmt_temp = is_temp;
	tank.mmt_state = MMT_STATE_IDLE;
	tank.mmt_variant = v;
	tank.mmt_fwd_spd = 0;
	tank.mmt_yawrate = 0;
	tank.mmt_vz = 0;
	tank.mmt_air = FALSE;
	tank.mmt_air_vel = '0 0 0';
	tank.mmt_has_air_vel = FALSE;
	tank.mmt_pad_cool = 0;
	tank.angles_x = 0;
	tank.angles_z = 0;
	tank.mmt_turret_yaw = tank.angles_y;
	tank.mmt_turret_pitch = 6;
	tank.mmt_flinch_end = 0;
	tank.mmt_recoil_end = 0;
	tank.mmt_reload_start = 0;
	tank.mmt_reload_end = 0;
	tank.mmt_cook_t = 0;
	tank.mmt_igniter = world;
	tank.mmt_driver = world;
	tank.skin = 0;
	tank.frame = 0;
	tank.scale = 1;

	tank.movetype = MOVETYPE_NONE;
	tank.solid = SOLID_BBOX;
	tank.takedamage = DAMAGE_AIM;
	tank.max_health = hp;
	tank.health = hp;
	tank.th_pain = MMT_Pain;
	tank.th_die = MMT_Die;

	setmodel (tank, MMT_HullModel (v));
	setsize (tank, '-104 -104 0', '104 104 132');

	// Snap cleanly onto floor
	traceline (tank.origin + '0 0 36', tank.origin - '0 0 256', TRUE, tank);
	if (trace_fraction < 1 && !trace_startsolid)
		setorigin (tank, trace_endpos + '0 0 0.5');
	else
		setorigin (tank, tank.origin);

	if (!is_temp)
	{
		tank.mmt_spawn_org = tank.origin;
		tank.mmt_spawn_ang = tank.angles;
	}

	if (tank.mmt_turret == world)
	{
		tur = spawn ();
		tur.classname = "mmt_turret";
		tur.mmt_base = tank;
		tur.movetype = MOVETYPE_NONE;
		tur.solid = SOLID_NOT;
		tank.mmt_turret = tur;
	}
	setmodel (tank.mmt_turret, MMT_TurretModel (v));
	setsize (tank.mmt_turret, '0 0 0', '0 0 0');
	tank.mmt_turret.effects = tank.mmt_turret.effects - (tank.mmt_turret.effects & EF_NODRAW);

	if (tank.mmt_wheelman == world)
	{
		wm = spawn ();
		wm.classname = "mmt_wheelman";
		wm.mmt_base = tank;
		wm.movetype = MOVETYPE_NONE;
		wm.solid = SOLID_NOT;
		wm.scale = 0.72;
		setmodel (wm, "progs/wheelman_dance.spr32");
		setsize (wm, '0 0 0', '0 0 0');
		wm.customizeentityforclient = MMT_WheelmanCustomize;
		tank.mmt_wheelman = wm;
	}
	tank.mmt_wheelman.scale = 0.72;
	tank.mmt_wheelman.effects = tank.mmt_wheelman.effects | EF_NODRAW;

	if (tank.mmt_bar_prop == world)
	{
		bp = spawn ();
		bp.classname = "mmt_bar_prop";
		bp.mmt_base = tank;
		bp.movetype = MOVETYPE_NONE;
		bp.solid = SOLID_NOT;
		bp.scale = 2.54;
		setmodel (bp, "progs/mm_bar.md3");
		setsize (bp, '0 0 0', '0 0 0');
		bp.effects = bp.effects | EF_NODRAW;
		tank.mmt_bar_prop = bp;
	}
	tank.mmt_bar_prop.scale = 2.54;
	tank.mmt_bar_prop.effects = tank.mmt_bar_prop.effects | EF_NODRAW;

	MMT_SyncAttachments (tank);
	tank.think = MMT_Think;
	tank.nextthink = time + 0.08;
};

void(entity tank) MMT_FreeChildren =
{
	if (tank.mmt_turret != world) { remove (tank.mmt_turret); tank.mmt_turret = world; }
	if (tank.mmt_wheelman != world) { remove (tank.mmt_wheelman); tank.mmt_wheelman = world; }
	if (tank.mmt_bar_prop != world) { remove (tank.mmt_bar_prop); tank.mmt_bar_prop = world; }
	if (tank.mmt_cam != world) { remove (tank.mmt_cam); tank.mmt_cam = world; }
};

void() MMT_Think =
{
	local float f, pack;
	local vector fpos, org0, org1, vel;

	if (self.mmt_cook_t < 0)
	{
		self.mmt_cook_t = 0;
		MMT_CatastrophicExplode (self, TRUE);
		return;
	}

	if (self.mmt_state == MMT_STATE_WRECK)
	{
		if (time < self.mmt_wreck_t)
		{
			if (time >= self.mmt_fx_t && mmt_fx_wreck > 0)
			{
				self.mmt_fx_t = time + 0.22;
				pointparticles (mmt_fx_wreck, self.origin + '0 0 22', '0 0 0', 1);
			}
			self.nextthink = time + 0.22;
			return;
		}
		if (!self.mmt_temp && autocvar_mm_tank_respawn > 0)
		{
			if (time < self.mmt_respawn_t)
			{
				self.effects = self.effects | EF_NODRAW;
				self.nextthink = time + 1.0;
				return;
			}
			tracebox (self.mmt_spawn_org + '0 0 4', '-104 -104 0', '104 104 132', self.mmt_spawn_org + '0 0 4', FALSE, self);
			if (trace_startsolid || trace_allsolid || trace_ent != world)
			{
				self.nextthink = time + 2.0;
				return;
			}
			self.effects = self.effects - (self.effects & EF_NODRAW);
			setorigin (self, self.mmt_spawn_org);
			self.angles = self.mmt_spawn_ang;
			MMT_InitTank (self, FALSE);
			sound (self, CHAN_AUTO, "items/itembk2.wav", 0.9, ATTN_NORM);
			return;
		}
		self.nextthink = -1;
		return;
	}

	// Safety: verify driver still alive and connected
	if (self.mmt_driver != world)
	{
		if (self.mmt_driver.health <= 0 || self.mmt_driver.deadflag != 0 || self.mmt_driver.mmt_tank != self)
			MMT_Leave (self, self.mmt_driver, FALSE);
	}

	// Fire state below 40% HP
	if (self.mmt_state == MMT_STATE_IDLE && self.health <= self.max_health * 0.40)
		MMT_StartFire (self, world);

	if (self.mmt_state == MMT_STATE_FIRE)
	{
		fpos = self.origin + '0 0 44';
		if (time >= self.mmt_fx_t && mmt_fx_fire > 0)
		{
			self.mmt_fx_t = time + 0.08;
			pointparticles (mmt_fx_fire, fpos, '0 0 0', 1);
		}
		if (time >= self.mmt_smoke_t && mmt_fx_smoke > 0)
		{
			self.mmt_smoke_t = time + 0.14;
			pointparticles (mmt_fx_smoke, fpos + '0 0 8', '0 0 0', 1);
		}
		if (time >= self.mmt_fire_snd_t)
		{
			self.mmt_fire_snd_t = time + 0.98;
			sound7 (self, CHAN_AUTO, "vehicles/fire_burn.wav", 0.85, 0.55, 98 + random () * 6);
		}
		if (time >= self.mmt_cook_t)
		{
			self.mmt_cook_t = time + 0.35;
			self.health = self.health - 5;
			if (self.health <= 0)
			{
				MMT_CatastrophicExplode (self, FALSE);
				return;
			}
		}
	}

	// Idle animation, airborne settle, & attachments when unoccupied
	if (self.mmt_driver == world)
	{
		if (self.mmt_air)
		{
			org0 = self.origin;
			vel = '0 0 0';
			if (self.mmt_has_air_vel)
				vel = self.mmt_air_vel;
			org1 = org0;
			org1_x = org0_x + vel_x * 0.08;
			org1_y = org0_y + vel_y * 0.08;
			if (!MMT_DriveSweep (self, org0, org1))
			{
				org1 = org0;
				self.mmt_air_vel = '0 0 0';
			}
			org1 = MMT_StepVerticalAndGround (self, org1, self.angles_y, 0.08, FALSE);
			setorigin (self, org1);
			setsize (self, '-104 -104 0', '104 104 132');
		}
		else
			MMT_StabilizeAngles (self, 0.08, TRUE, 0);
		if (time < self.mmt_flinch_end)
		{
			f = floor ((0.36 - (self.mmt_flinch_end - time)) * 22.0);
			self.frame = 40 + bound (0, f, 7);
		}
		else
		{
			self.mmt_anim_t = self.mmt_anim_t + 0.8;
			f = floor (self.mmt_anim_t);
			self.frame = f - 16 * floor (f / 16);
		}
		if (time >= self.mmt_eng_t)
		{
			self.mmt_eng_t = time + 1.18;
			pack = MMT_ClampPack (autocvar_mm_tank_soundpack);
			sound7 (self, CHAN_BODY, MMT_Snd (pack, 0), 0.42, ATTN_STATIC, 100);
		}
		MMT_SyncAttachments (self);
	}

	self.nextthink = time + 0.08;
};

// ---------------------------------------------------------------- Spawn, Proximity Prompt, H-Key & Impulses

void() misc_mm_tank =
{
	MMT_InitTank (self, FALSE);
};

entity(entity p) MMTank_NearFree =
{
	local entity e, best;
	local float d, bd;

	if (!mmt_has_tanks)
		return world;
	best = world;
	bd = 235;
	e = find (world, classname, "misc_mm_tank");
	while (e != world)
	{
		if (e.mmt_state != MMT_STATE_WRECK && e.mmt_driver == world)
		{
			d = vlen ((e.origin + '0 0 63') - (p.origin + '0 0 22'));
			if (d < bd)
			{
				bd = d;
				best = e;
			}
		}
		e = find (e, classname, "misc_mm_tank");
	}
	return best;
};

void() MMTank_NearPrompt =
{
	local entity t;

	if (!mmt_has_tanks || self.ishuman != 1 || self.health <= 0 || MMTank_Driving (self) || EricCannon_Active (self) || self.veh_van != world || self.veh_ride != world || self.jb_vehicle != world || self.classname != "player")
		return;
	if (time < self.mmt_prompt_scan_t)
		return;
	self.mmt_prompt_scan_t = time + 0.12;

	t = MMTank_NearFree (self);
	if (t == world)
	{
		if (time > self.mmt_prompt_t)
			self.mmt_prompt_ent = world;
		return;
	}
	if (self.mmt_prompt_ent == t && time < self.mmt_prompt_t)
		return;
	self.mmt_prompt_ent = t;
	self.mmt_prompt_t = time + 6.0;
	centerprint (self, "Press H to drive MEGA MAN TANK");
};

float() MMTank_TryEnterKey =
{
	local entity t, ec, jb, van;
	local float dt;

	if (self.health <= 0 || MMTank_Driving (self) || EricCannon_Active (self) || self.veh_van != world || self.veh_ride != world || self.jb_vehicle != world)
		return FALSE;
	t = MMTank_NearFree (self);
	if (t == world)
		return FALSE;

	dt = vlen (t.origin - self.origin);
	ec = EricCannon_NearIdle (self);
	if (ec != world && vlen (ec.origin - self.origin) < dt)
		return FALSE;
	jb = JohnBird_NearPerched (self);
	if (jb != world && vlen (jb.origin - self.origin) < dt)
		return FALSE;
	van = Veh_SeatOf (self);
	if (van != world && vlen (van.origin - self.origin) < dt)
		return FALSE;

	MMT_Enter (self, t);
	return TRUE;
};

void(entity p) MMTank_Reset =
{
	local entity tank;
	local float ct;

	tank = p.mmt_tank;
	if (tank != world && !bm_wasfreed (tank) && tank.classname == "misc_mm_tank" && tank.mmt_driver == p)
		MMT_Leave (tank, p, TRUE);
	else
		MMT_UnhidePlayer (p);
	p.mmt_tank = world;
	p.mmt_btn = FALSE;
	p.mmt_st_active = 0;
	ct = clienttype (p);
	if (!p.mmt_alias_sent && ct == FD_CLIENTTYPE_REAL)
	{
		p.mmt_alias_sent = TRUE;
		stuffcmd (p, "alias tank_variant \"cmd tank_variant $*\"\nalias tank_sound \"cmd tank_sound $*\"\nalias tank_boom_pool \"cmd tank_boom_pool $*\"\n");
	}
};

void() MMTank_ClientGone =
{
	local entity tmp;

	self.mmt_alias_sent = FALSE;
	MMTank_Reset (self);
	tmp = self.mmt_my_temp;
	if (tmp != world && !bm_wasfreed (tmp) && tmp.classname == "misc_mm_tank" && tmp.mmt_temp && tmp.mmt_summoner == self && tmp.mmt_driver == world)
	{
		MMT_FreeChildren (tmp);
		remove (tmp);
	}
	self.mmt_my_temp = world;
};

entity(entity summoner, vector org, float yaw) MMT_SpawnTemp =
{
	local entity old, t;

	old = summoner.mmt_my_temp;
	if (old != world && !bm_wasfreed (old) && old.classname == "misc_mm_tank" && old.mmt_temp && old.mmt_driver == world)
	{
		MMT_FreeChildren (old);
		remove (old);
		summoner.mmt_my_temp = world;
	}

	t = spawn ();
	t.angles = '0 1 0' * MMT_NormYaw (yaw);
	setorigin (t, org);
	MMT_InitTank (t, TRUE);
	t.mmt_summoner = summoner;
	summoner.mmt_my_temp = t;
	return t;
};

void() MMTank_Impulse =
{
	local float v, p;
	local vector org;
	local entity t;

	MMTank_NearPrompt ();
	// 134/135 cvar_set server-wide mm_tank_* (they outlive the map): a test aid like 132/133, not for any client
	if ((self.impulse == 134 || self.impulse == 135) && !autocvar_sv_cheats)
	{
		self.impulse = 0;
		return;
	}
	if (self.impulse == 134)
	{
		self.impulse = 0;
		v = MMT_ClampVariant (autocvar_mm_tank_variant) + 1;
		if (v > 4)
			v = 1;
		MMTank_SetVariant (v);
		sprint (self, strcat ("Mega Man Tank prototype: ", MMT_VariantName (v), "\n"));
		centerprint (self, MMT_VariantName (v));
		return;
	}
	if (self.impulse == 135)
	{
		self.impulse = 0;
		p = MMT_ClampPack (autocvar_mm_tank_soundpack) + 1;
		if (p > 11)
			p = 0;
		MMTank_SetSoundPack (p);
		sprint (self, strcat ("Mega Man Tank sound pack: ", MMT_PackName (p), "\n"));
		centerprint (self, MMT_PackName (p));
		sound (self, CHAN_AUTO, MMT_Snd (p, 5), 1.0, 0.35);
		return;
	}
	if (self.impulse != 132 && self.impulse != 133)
		return;
	if (!autocvar_sv_cheats)
		return;

	if (self.impulse == 132)
	{
		self.impulse = 0;
		makevectors ('0 1 0' * self.v_angle_y);
		org = self.origin + v_forward * 220 + '0 0 24';
		t = MMT_SpawnTemp (self, org, self.v_angle_y);
		sprint (self, "Spawned Mega Man Tank ahead! Walk up and press H to drive!\n");
		return;
	}
	if (self.impulse == 133)
	{
		self.impulse = 0;
		if (self.health <= 0 || MMTank_Driving (self) || EricCannon_Active (self) || self.veh_van != world || self.veh_ride != world || self.jb_vehicle != world)
			return;
		makevectors ('0 1 0' * self.v_angle_y);
		org = self.origin + v_forward * 140 + '0 0 24';
		t = MMT_SpawnTemp (self, org, self.v_angle_y);
		MMT_Enter (self, t);
		return;
	}
};
