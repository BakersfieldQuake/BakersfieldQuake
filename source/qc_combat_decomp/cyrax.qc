#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
CYRAX NET LAUNCHER (Fun Gun Slot 10, FG_CYRAX = 10, BM_FG10 = 19, impulse 70, key L)
See cyrax_defs.qc for constants, fields, and state machine overview.
================
*/

void() Cyrax_Precache =
{
	precache_model ("progs/v_cyrax.md3");
	precache_model ("progs/cyrax_net.md3");
	precache_model ("progs/cyrax_wrap.md3");

	precache_sound ("cyrax/charge.wav");
	precache_sound ("cyrax/fire.wav");
	precache_sound ("cyrax/vent.wav");
	precache_sound ("cyrax/capture.wav");
	precache_sound ("cyrax/pull.wav");
	precache_sound ("cyrax/hold_beep.wav");
	precache_sound ("cyrax/bonk_launch.wav");

	cy_fx_charge_glow = particleeffectnum ("cyrax_charge_glow");
	cy_fx_muzzle_flash = particleeffectnum ("cyrax_muzzle_flash");
	cy_fx_muzzle_dust = particleeffectnum ("cyrax_muzzle_dust");
	cy_fx_net_trail = particleeffectnum ("cyrax_net_trail");
	cy_fx_net_capture = particleeffectnum ("cyrax_net_capture");
	cy_fx_bonk_launch = particleeffectnum ("cyrax_bonk_launch");
};

void(float fx, vector org, vector dir, float cnt) Cyrax_Fx =
{
	if (fx >= 0)
		pointparticles (fx, org, dir, cnt);
};

vector(entity p) Cyrax_MuzzlePos =
{
	local vector eye;

	makevectors (p.v_angle);
	eye = p.origin + p.view_ofs;
	traceline (eye, eye + v_forward * 26 + v_right * 6 - v_up * 5, TRUE, p);
	return trace_endpos - v_forward * 2;
};

vector(entity targ) Cyrax_TargetCenter =
{
	if (targ.classname == "misc_vehicle_johnbird")
		return targ.origin + '0 0 26';
	if (targ.classname == "milky")
		return targ.origin - '0 0 18';
	return targ.origin + '0 0 10';
};

float(entity p) Cyrax_TestOn =
{
	return (autocvar_cyrax_test != 0 || cvar ("cyrax_test") != 0);
};

// ---------------------------------------------------------------- target validation & cleanup

float(entity shooter, entity e) Cyrax_IsValidTarget =
{
	if (e == world || bm_wasfreed (e))
		return FALSE;

	// Redirect a flying Winged John pilot entity to the bird itself
	if (e.classname == "player" && e.jb_vehicle != world)
		e = e.jb_vehicle;

	if (e.classname == "player")
	{
		if (e.health <= 0 || e.deadflag || e.bm_obs || e.solid == SOLID_NOT || !e.takedamage)
			return FALSE;
		if (e.veh_van != world || e.veh_ride != world || e.mmt_tank != world || e.rr_vehicle != world || FD_Flying (e) || EricCannon_Active (e))
			return FALSE;
		if (e.cy_trapped_by != world && e.cy_trapped_by != shooter)
			return FALSE;
		if (e == shooter)
			return Cyrax_TestOn (shooter);
		if ((teamplay == 1 || CTF_ENABLED) && shooter != world && e.team > 0 && e.team == shooter.team)
			return FALSE;
		return TRUE;
	}

	if (e.classname == "misc_vehicle_johnbird")
	{
		if (e.health <= 0 || e.jb_dying)
			return FALSE;
		if (e.cy_trapped_by != world && e.cy_trapped_by != shooter)
			return FALSE;
		if (e.jb_pilot != world)
		{
			if (e.jb_pilot == shooter)
				return Cyrax_TestOn (shooter);
			if ((teamplay == 1 || CTF_ENABLED) && shooter != world && e.jb_pilot.team > 0 && e.jb_pilot.team == shooter.team)
				return FALSE;
		}
		return TRUE;
	}

	if (e.classname == "milky")
	{
		if (e.milky_hp <= 0 || !e.takedamage)
			return FALSE;
		if (!e.milky_emerged && e.milky_owner == shooter)
			return FALSE;
		if (e.cy_trapped_by != world && e.cy_trapped_by != shooter)
			return FALSE;
		if ((teamplay == 1 || CTF_ENABLED) && shooter != world && e.milky_owner != world && e.milky_owner != shooter && e.milky_owner.team > 0 && e.milky_owner.team == shooter.team)
			return FALSE;
		return TRUE;
	}

	return FALSE;
};

void(entity targ) Cyrax_RestoreVictimState =
{
	local entity oself;

	if (targ == world || bm_wasfreed (targ))
		return;

	targ.cy_trapped_by = world;
	targ.cy_trapped_end = 0;

	if (targ.classname == "player")
	{
		targ.cy_st_mode = 0;
		targ.cy_st_prog = 0;
		targ.cy_st_dist = 0;
		if (targ.health > 0 && !targ.deadflag && !targ.bm_obs)
		{
			if (targ.cy_old_movetype && targ.cy_old_movetype != MOVETYPE_NONE)
				targ.movetype = targ.cy_old_movetype;
			else
				targ.movetype = MOVETYPE_WALK;
			if (targ.cy_old_weapon && (targ.items & targ.cy_old_weapon))
			{
				targ.weapon = targ.cy_old_weapon;
				oself = self;
				self = targ;
				W_SetCurrentAmmo ();
				self = oself;
			}
		}
		targ.cy_old_movetype = 0;
		targ.cy_old_weapon = 0;
		return;
	}

	if (targ.classname == "misc_vehicle_johnbird")
	{
		if (targ.jb_pilot != world && !bm_wasfreed (targ.jb_pilot))
		{
			targ.jb_pilot.cy_trapped_by = world;
			targ.jb_pilot.cy_trapped_end = 0;
			targ.jb_pilot.cy_st_mode = 0;
			targ.jb_pilot.cy_st_prog = 0;
			targ.jb_pilot.cy_st_dist = 0;
		}
		if (targ.health > 0 && !targ.jb_dying)
		{
			if (targ.jb_pilot == world && !targ.jb_ai)
				targ.movetype = MOVETYPE_TOSS;
			else
				targ.movetype = MOVETYPE_NONE;
		}
		targ.cy_old_movetype = 0;
		return;
	}

	if (targ.classname == "milky")
	{
		if (targ.milky_hp > 0 && targ.takedamage)
		{
			if (targ.cy_old_movetype && targ.cy_old_movetype != MOVETYPE_NONE)
				targ.movetype = targ.cy_old_movetype;
			else
				targ.movetype = MOVETYPE_FLY;
		}
		targ.cy_old_movetype = 0;
	}
};

void(entity p) Cyrax_ReleaseHold =
{
	local entity targ, wrap;

	if (p == world || bm_wasfreed (p))
		return;

	targ = p.cy_hold_targ;
	wrap = p.cy_hold_wrap;

	p.cy_hold_targ = world;
	p.cy_hold_wrap = world;
	p.cy_hold_kind = 0;
	p.cy_hold_end = 0;
	p.cy_hold_phase = 0;
	p.cy_pull_snd_t = 0;

	if (wrap != world && !bm_wasfreed (wrap) && wrap.classname == "cyrax_wrap")
		remove (wrap);

	if (targ != world && !bm_wasfreed (targ))
	{
		if (targ.cy_trapped_by == p)
			Cyrax_RestoreVictimState (targ);
	}

	if (p.classname == "player" && p.cy_charging <= 0 && p.cy_trapped_by == world)
	{
		p.cy_st_mode = 0;
		p.cy_st_prog = 0;
		p.cy_st_dist = 0;
	}
};

void(entity targ) Cyrax_ReleaseTargetEntity =
{
	local entity holder;

	if (targ == world || bm_wasfreed (targ))
		return;
	holder = targ.cy_trapped_by;
	if (holder != world && !bm_wasfreed (holder) && holder.cy_hold_targ == targ)
		Cyrax_ReleaseHold (holder);
	else
		Cyrax_RestoreVictimState (targ);
};

void(entity p) Cyrax_StopCharge =
{
	if (p.cy_charging > 0)
	{
		p.cy_charging = 0;
		sound (p, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
	}
	if (p.cy_hold_targ == world && p.cy_trapped_by == world)
	{
		p.cy_st_mode = 0;
		p.cy_st_prog = 0;
		p.cy_st_dist = 0;
	}
};

void(entity p) Cyrax_ResetPlayer =
{
	if (p == world || bm_wasfreed (p))
		return;
	Cyrax_StopCharge (p);
	Cyrax_ReleaseHold (p);
	if (p.cy_trapped_by != world)
		Cyrax_ReleaseTargetEntity (p);
	p.cy_fire_t = 0;
	p.cy_vent_t = 0;
	p.cy_draw_t = 0;
	p.cy_catch_t = 0;
	p.cy_tether_t = 0;
	p.cy_empty = FALSE;
	p.cy_bonk_phase = 0;
	p.cy_bonk_t0 = 0;
	p.cy_bonk_hit_at = 0;
	p.cy_bonk_end = 0;
	p.cy_bonk_snd = FALSE;
	p.cy_click_ready = FALSE;
	p.cy_launch_until = 0;
	p.cy_st_mode = 0;
	p.cy_st_prog = 0;
	p.cy_st_dist = 0;
	if (p.cy_vm != world && !bm_wasfreed (p.cy_vm))
		p.cy_vm.alpha = -1;
};

void(entity p) Cyrax_ClientGone =
{
	local entity e, nx;

	Cyrax_ResetPlayer (p);
	if (p.cy_vm != world)
	{
		if (!bm_wasfreed (p.cy_vm) && p.cy_vm.owner == p)
			remove (p.cy_vm);
		p.cy_vm = world;
	}
	e = find (world, classname, "cyrax_net_proj");
	while (e)
	{
		nx = find (e, classname, "cyrax_net_proj");
		if (e.owner == p)
			remove (e);
		e = nx;
	}
	e = find (world, classname, "cyrax_wrap");
	while (e)
	{
		nx = find (e, classname, "cyrax_wrap");
		if (e.owner == p)
			remove (e);
		e = nx;
	}
};

// ---------------------------------------------------------------- viewmodel (progs/v_cyrax.md3, skins 0..67)

void(entity vm, entity p) Cyrax_UpdateVMVisual =
{
	local float hide, u, idx, ease, sw1, sw2, spd, dt_f;
	local vector vxy;

	hide = (p.classname != "player" || p.weapon != IT_FUNGUN || p.fg_sel != FG_CYRAX
		|| p.health <= 0 || p.deadflag || intermission_running || p.clientcamera != p
		|| p.meleeing == 1 || p.throwing == 1 || p.cy_trapped_by != world || p.cy_bonk_phase > 0
		|| (p.bm_rl_slot != 0 && !p.bm_rl_quiet)
		|| FD_Flying (p) || Veh_Driving (p) || JohnBird_Flying (p) || RocketRider_Flying (p)
		|| EricCannon_Active (p) || MMTank_Driving (p) || Binoc_On (p));

	if (hide)
	{
		if (p.cy_vm_was_on)
			p.cy_vm_was_on = FALSE;
		vm.alpha = -1;
		return;
	}

	p.weaponmodel = "";
	vm.frame = 0;
	vm.origin = '0 0 0';
	vm.angles = '0 0 0';

	if (!p.cy_vm_was_on)
	{
		p.cy_vm_was_on = TRUE;
		if (p.cy_charging <= 0 && (!p.cy_fire_t || time >= p.cy_fire_t + CY_FIRE_ANIM_TIME))
			p.cy_draw_t = time;
	}

	if (invisweapon && p.invisible_finished > time)
		vm.alpha = 0.3;
	else if (!invisweapon && p.invisible_finished > time)
		vm.alpha = -1;
	else
		vm.alpha = 1;

	if (p.super_damage_finished > time)
		vm.colormod = '0.5 0.7 1.5';
	else
		vm.colormod = '1 1 1';

	// 1. Charge buildup (skins 8..31)
	if (p.cy_charging > 0)
	{
		u = (time - p.cy_charging) / CY_CHARGE_TIME;
		if (u < 0) u = 0;
		if (u > 0.999) u = 0.999;
		idx = floor (u * CY_VM_CHARGE_COUNT);
		vm.skin = CY_VM_CHARGE_SKIN + idx;
		sw1 = sin (time * 54.0);
		sw2 = cos (time * 47.0);
		vm.origin_x = -0.8 * u + sw1 * (0.08 + 0.38 * u * u);
		vm.origin_y = sw2 * (0.08 + 0.34 * u * u);
		vm.origin_z = -0.5 * u + sw1 * (0.06 + 0.28 * u * u);
		vm.angles_z = sw2 * (0.4 + 1.8 * u * u);
		return;
	}

	// 2. Dopamine capture celebration (skins 56..67)
	if (p.cy_catch_t > 0 && time < p.cy_catch_t + CY_CATCH_ANIM_TIME)
	{
		u = (time - p.cy_catch_t) / CY_CATCH_ANIM_TIME;
		if (u < 0) u = 0;
		if (u > 0.999) u = 0.999;
		idx = floor (u * CY_VM_CATCH_COUNT);
		if (idx >= CY_VM_CATCH_COUNT)
			idx = CY_VM_CATCH_COUNT - 1;
		vm.skin = CY_VM_CATCH_SKIN + idx;
		sw1 = sin (u * 3.14159);
		sw2 = sin (u * 6.28318 * 2.0);
		vm.origin_x = 1.6 * sw1;
		vm.origin_y = 0.7 * sw1;
		vm.origin_z = 1.8 * sw1 + 0.35 * sw2 * (1 - u);
		vm.angles_x = -3.8 * sw1;
		vm.angles_z = 2.6 * sw2 * (1 - u);
		return;
	}

	// 3. Fire blast & recoil (skins 32..43: 32..36 muzzle flash, 37..43 recoil return)
	if (p.cy_fire_t > 0 && time < p.cy_fire_t + CY_FIRE_ANIM_TIME)
	{
		dt_f = time - p.cy_fire_t;
		if (dt_f < 0.14)
		{
			u = dt_f / 0.14;
			if (u > 0.999) u = 0.999;
			idx = floor (u * 5);
			vm.skin = CY_VM_FIRE_SKIN + idx;
			vm.origin_x = -3.4 * (1 - 0.3 * u);
			vm.origin_z = 0.8 * (1 - u);
			vm.angles_x = -4.2 * (1 - u);
		}
		else
		{
			u = (dt_f - 0.14) / (CY_FIRE_ANIM_TIME - 0.14);
			if (u > 0.999) u = 0.999;
			idx = 5 + floor (u * 7);
			if (idx >= CY_VM_FIRE_COUNT)
				idx = CY_VM_FIRE_COUNT - 1;
			vm.skin = CY_VM_FIRE_SKIN + idx;
			ease = 1 - (1 - u) * (1 - u);
			vm.origin_x = -2.4 * (1 - ease);
			vm.angles_x = -2.6 * (1 - ease);
		}
		return;
	}

	// 4. Early-abort vent / cooldown (skins 50..55)
	if (p.cy_vent_t > 0 && time < p.cy_vent_t + CY_VENT_ANIM_TIME)
	{
		u = (time - p.cy_vent_t) / CY_VENT_ANIM_TIME;
		if (u < 0) u = 0;
		if (u > 0.999) u = 0.999;
		idx = floor (u * CY_VM_VENT_COUNT);
		vm.skin = CY_VM_VENT_SKIN + idx;
		vm.origin_x = -0.9 * (1 - u);
		vm.origin_z = -0.8 * sin (u * 3.14159);
		vm.angles_x = 2.0 * sin (u * 3.14159);
		return;
	}

	// 5. Draw / raise pop-up (skins 44..49)
	if (p.cy_draw_t > 0 && time >= p.cy_draw_t && time < p.cy_draw_t + CY_DRAW_ANIM_TIME)
	{
		u = (time - p.cy_draw_t) / CY_DRAW_ANIM_TIME;
		if (u < 0) u = 0;
		if (u > 0.999) u = 0.999;
		idx = floor (u * CY_VM_DRAW_COUNT);
		vm.skin = CY_VM_DRAW_SKIN + idx;
		ease = 1 - (1 - u) * (1 - u);
		vm.origin_z = -16.0 * (1 - ease);
		return;
	}

	// 6. Idle (skins 0..7)
	idx = floor (time * 10);
	idx = idx - CY_VM_IDLE_COUNT * floor (idx / CY_VM_IDLE_COUNT);
	vm.skin = CY_VM_IDLE_SKIN + idx;

	vxy = p.velocity;
	vxy_z = 0;
	spd = vlen (vxy) / 320;
	if (spd > 1) spd = 1;
	sw1 = sin (time * 2.4);
	sw2 = cos (time * 4.8);
	vm.origin_y = 0.14 * sw1 + 0.35 * spd * sin (time * 8.0);
	vm.origin_z = 0.12 * sw2 - 0.28 * spd * fabs (sin (time * 8.0));
};

void() Cyrax_VMThink =
{
	local entity p;

	p = self.owner;
	if (p == world || bm_wasfreed (p) || p.classname != "player" || intermission_running)
	{
		if (p != world && !bm_wasfreed (p) && p.cy_vm == self)
			p.cy_vm = world;
		remove (self);
		return;
	}
	Cyrax_UpdateVMVisual (self, p);
	self.nextthink = time;
};

void(entity p) Cyrax_EnsureVM =
{
	local entity vm;

	if (p.ishuman != 1)
		return;
	vm = p.cy_vm;
	if (vm == world || bm_wasfreed (vm) || vm.owner != p)
	{
		if (p.weapon != IT_FUNGUN || p.fg_sel != FG_CYRAX)
			return;
		vm = spawn ();
		vm.classname = "cyrax_vm";
		vm.owner = p;
		vm.viewmodelforclient = p;
		vm.movetype = MOVETYPE_NONE;
		vm.solid = SOLID_NOT;
		vm.alpha = -1;
		setmodel (vm, "progs/v_cyrax.md3");
		setsize (vm, VEC_ORIGIN, VEC_ORIGIN);
		vm.think = Cyrax_VMThink;
		vm.nextthink = time;
		p.cy_vm = vm;
	}
	Cyrax_UpdateVMVisual (vm, p);
};

// ---------------------------------------------------------------- wrapped green net & capture

void(entity wrap, entity targ) Cyrax_PositionWrap =
{
	local vector ofs;
	local float f;

	if (targ.classname == "misc_vehicle_johnbird")
	{
		wrap.scale = 1.65;
		ofs = '0 0 18';
	}
	else if (targ.classname == "milky")
	{
		wrap.scale = 2.10;
		ofs = '0 0 -18';
	}
	else
	{
		wrap.scale = 1.05;
		ofs = '0 0 0';
	}
	setorigin (wrap, targ.origin + ofs);
	f = floor (time * 14);
	wrap.frame = f - 8 * floor (f / 8);
	wrap.angles_y = wrap.angles_y + 180 * frametime;
};

void() Cyrax_WrapThink =
{
	local entity p, targ;

	p = self.owner;
	targ = self.cy_targ;
	if (p == world || bm_wasfreed (p) || p.classname != "player" || p.health <= 0
		|| targ == world || bm_wasfreed (targ) || targ.cy_trapped_by != p
		|| p.cy_hold_targ != targ || time >= p.cy_hold_end)
	{
		remove (self);
		return;
	}
	Cyrax_PositionWrap (self, targ);
	self.nextthink = time + 0.03;
};

void(entity victim) Cyrax_ForceVictimAxe =
{
	local entity oself;

	if (victim.classname != "player")
		return;
	DK_ResetPlayer (victim);
	GJ_ResetPlayer (victim);
	KY_ResetPlayer (victim);
	RH_ResetPlayer (victim);
	victim.wc_charging = 0;
	victim.ltg_phase = 0;
	victim.milky_wind = 0;
	victim.pk_throw_at = 0;
	victim.ns_throw_at = 0;
	victim.hm_state = 0;
	victim.cy_charging = 0;
	if (victim.bn_on)
	{
		victim.bn_on = FALSE;
		victim.viewzoom = 0;
		centerprint (victim, "");
	}
	if (victim.jp_on)
	{
		oself = self;
		self = victim;
		Jetpack_Off ();
		self = oself;
	}
	if (victim.weapon != IT_AXE)
	{
		victim.weapon = IT_AXE;
		oself = self;
		self = victim;
		W_SetCurrentAmmo ();
		self = oself;
	}
	HeldVwep_Clear (victim);
};

void(entity shooter, entity targ, vector hit_org) Cyrax_Capture =
{
	local entity wrap;
	local float kind;
	local vector cpos;

	if (shooter == world || bm_wasfreed (shooter) || shooter.classname != "player" || shooter.health <= 0)
		return;
	if (!Cyrax_IsValidTarget (shooter, targ))
		return;

	if (targ.classname == "player" && targ.jb_vehicle != world)
		targ = targ.jb_vehicle;

	if (shooter.cy_hold_targ != world)
		Cyrax_ReleaseHold (shooter);

	if (targ.classname == "misc_vehicle_johnbird")
		kind = 1;
	else if (targ.classname == "milky")
		kind = 2;
	else
		kind = 0;

	cpos = Cyrax_TargetCenter (targ);
	Cyrax_Fx (cy_fx_net_capture, cpos, '0 0 0', 1);
	sound7 (targ, CHAN_AUTO, "cyrax/capture.wav", 1.0, ATTN_NORM, SNDSPD);
	if (shooter != targ)
		sound7 (shooter, CHAN_AUTO, "cyrax/capture.wav", 0.75, ATTN_NORM, SNDSPD);

	targ.cy_trapped_by = shooter;
	targ.cy_trapped_end = time + CY_HOLD_MAX;
	targ.cy_old_movetype = targ.movetype;
	targ.movetype = MOVETYPE_NONE;
	targ.velocity = '0 0 0';
	targ.flags = targ.flags - (targ.flags & FL_ONGROUND);

	if (kind == 0)
	{
		// Do not let a netted victim hold someone else or keep charging weapons
		if (targ != shooter && targ.cy_hold_targ != world)
			Cyrax_ReleaseHold (targ);
		if (targ != shooter)
		{
			targ.cy_old_weapon = targ.weapon;
			Cyrax_ForceVictimAxe (targ);
		}
		targ.disableclientprediction = 1;
	}
	else if (kind == 1)
	{
		if (targ.jb_pilot != world && !bm_wasfreed (targ.jb_pilot))
		{
			targ.jb_pilot.cy_trapped_by = shooter;
			targ.jb_pilot.cy_trapped_end = targ.cy_trapped_end;
		}
	}

	wrap = spawn ();
	wrap.classname = "cyrax_wrap";
	wrap.owner = shooter;
	wrap.cy_targ = targ;
	wrap.movetype = MOVETYPE_NONE;
	wrap.solid = SOLID_NOT;
	wrap.effects = EF_FULLBRIGHT;
	setmodel (wrap, "progs/cyrax_wrap.md3");
	setsize (wrap, VEC_ORIGIN, VEC_ORIGIN);
	Cyrax_PositionWrap (wrap, targ);
	wrap.think = Cyrax_WrapThink;
	wrap.nextthink = time + 0.03;

	shooter.cy_hold_targ = targ;
	shooter.cy_hold_wrap = wrap;
	shooter.cy_hold_kind = kind;
	shooter.cy_hold_end = time + CY_HOLD_MAX;
	shooter.cy_hold_phase = 1;
	shooter.cy_pull_snd_t = time + 0.05;
	shooter.cy_catch_t = time;
	shooter.cy_tether_t = 0;
	shooter.cy_click_ready = !shooter.button0;
	shooter.cy_st_flash = shooter.cy_st_flash + 1;
	shooter.cy_st_kind = kind;
	shooter.cy_st_dist = floor (vlen (targ.origin - shooter.origin));
};

// ---------------------------------------------------------------- flying net projectile

void() Cyrax_NetPop =
{
	local vector org;

	org = self.origin;
	Cyrax_Fx (cy_fx_muzzle_dust, org, '0 0 24', 1);
	sound7 (self, CHAN_AUTO, "cyrax/vent.wav", 0.55, ATTN_NORM, SNDSPD);
	remove (self);
};

void() Cyrax_NetTouch =
{
	local entity shooter, targ;

	if (other == self.owner)
		return;
	if (other.solid == SOLID_TRIGGER)
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}

	shooter = self.owner;
	targ = other;
	if (targ.classname == "player" && targ.jb_vehicle != world)
		targ = targ.jb_vehicle;

	if (Cyrax_IsValidTarget (shooter, targ))
	{
		Cyrax_Capture (shooter, targ, self.origin);
		remove (self);
		return;
	}

	// Ignore standard rockets, grenades, and other fun-gun projectiles in mid-flight
	if (other != world && other.solid != SOLID_BSP)
	{
		if (other.movetype == MOVETYPE_FLYMISSILE || other.movetype == MOVETYPE_BOUNCE
			|| other.movetype == MOVETYPE_TOSS || other.movetype == MOVETYPE_FLY)
		{
			self.velocity = self.cy_vel;
			if (vlen (self.cy_vel) > 1)
			{
				local vector fwd_step;
				fwd_step = normalize (self.cy_vel) * 14;
				traceline (self.origin, self.origin + fwd_step, TRUE, self);
				if (trace_fraction < 1)
				{
					Cyrax_NetPop ();
					return;
				}
				setorigin (self, self.origin + fwd_step);
			}
			return;
		}
	}

	Cyrax_NetPop ();
};

void() Cyrax_NetThink =
{
	local float f;
	local entity head, targ;
	local vector cpos;

	if (time >= self.fg_born + CY_NET_LIFE || pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}

	// Forgiving proximity capture for the huge non-spinning net (within 58u with clear LOS)
	head = findradius (self.origin, 58);
	while (head != world)
	{
		targ = head;
		if (targ.classname == "player" && targ.jb_vehicle != world)
			targ = targ.jb_vehicle;
		if (!(targ == self.owner && time < self.fg_born + 0.15) && Cyrax_IsValidTarget (self.owner, targ))
		{
			cpos = Cyrax_TargetCenter (targ);
			if (vlen (targ.origin - self.origin) <= 58 || vlen (cpos - self.origin) <= 58)
			{
				traceline (self.origin, cpos, TRUE, self);
				if (trace_fraction == 1)
				{
					Cyrax_Capture (self.owner, targ, self.origin);
					remove (self);
					return;
				}
			}
		}
		head = head.chain;
	}

	f = floor ((time - self.fg_born) * 18);
	self.frame = f - 8 * floor (f / 8);
	self.angles = vectoangles (self.cy_vel);
	self.angles_z = 0;
	self.nextthink = time + 0.02;
};

void(entity p) Cyrax_FireNet =
{
	local entity net;
	local vector muz, eye, aim_pt, dir;

	FunGun_SetAmmo (p, FG_CYRAX, 1);
	FunGun_Lock (FG_CYRAX);

	p.cy_charging = 0;
	p.cy_fire_t = time;
	p.fg_fire_t = time;
	p.bm_lastshot = time + 0.35;
	p.cy_click_ready = FALSE;

	makevectors (p.v_angle);
	muz = Cyrax_MuzzlePos (p);
	eye = p.origin + p.view_ofs;
	traceline (eye, eye + v_forward * 2048, FALSE, p);
	if (trace_fraction < 0.03)
		aim_pt = eye + v_forward * 256;
	else
		aim_pt = trace_endpos;
	dir = normalize (aim_pt - muz);
	if (dir == VEC_ORIGIN)
		dir = v_forward;

	// Slight player pushback recoil & muzzle FX
	p.velocity = p.velocity - v_forward * CY_RECOIL_PUSH;
	p.effects = p.effects | EF_MUZZLEFLASH;
	p.punchangle_x = -4.0;
	player_mm1 ();

	Cyrax_Fx (cy_fx_muzzle_flash, muz, dir * 200, 1);
	Cyrax_Fx (cy_fx_muzzle_dust, muz, dir * 120, 1);
	sound7 (p, CHAN_WEAPON, "cyrax/fire.wav", 1.0, ATTN_NORM, SNDSPD);

	net = spawn ();
	net.classname = "cyrax_net_proj";
	net.owner = p;
	net.fg_born = time;
	net.movetype = MOVETYPE_FLYMISSILE;
	net.solid = SOLID_BBOX;
	net.effects = EF_FULLBRIGHT;
	setmodel (net, "progs/cyrax_net.md3");
	setsize (net, '-32 -32 -40', '32 32 40');
	setorigin (net, muz);
	net.cy_vel = dir * CY_NET_SPEED;
	net.velocity = net.cy_vel;
	net.angles = vectoangles (dir);
	net.angles_z = 0;
	if (cy_fx_net_trail >= 0)
		net.traileffectnum = cy_fx_net_trail;
	net.touch = Cyrax_NetTouch;
	net.think = Cyrax_NetThink;
	net.nextthink = time + 0.02;

	p.attack_finished = time + 0.25;
};

// ---------------------------------------------------------------- pull, hold & geometry-safe movement

vector(entity p, entity targ) Cyrax_CalcHoldPoint =
{
	local vector eye, want, bmin, bmax, ofs;

	makevectors (p.v_angle);
	eye = p.origin + p.view_ofs;
	if (targ.classname == "misc_vehicle_johnbird")
		ofs = '0 0 -18';
	else if (targ.classname == "milky")
		ofs = '0 0 10';
	else
		ofs = '0 0 -10';

	traceline (eye, eye + v_forward * CY_HOLD_DIST, TRUE, p);
	want = trace_endpos;
	if (trace_fraction < 1)
		want = want + trace_plane_normal * 20;
	want = want + ofs;

	bmin = targ.mins;
	bmax = targ.maxs;
	if (bmin == VEC_ORIGIN && bmax == VEC_ORIGIN)
	{
		bmin = '-16 -16 -24';
		bmax = '16 16 32';
	}
	tracebox (eye + ofs, bmin, bmax, want, TRUE, targ);
	if (!trace_startsolid)
		return trace_endpos;

	traceline (targ.origin, want, TRUE, targ);
	if (trace_fraction < 1)
		return trace_endpos + trace_plane_normal * 18;
	return want;
};

void(entity targ, vector want_pos, float max_step) Cyrax_MoveToward =
{
	local vector delta, step, bmin, bmax, next_pos;
	local float d;

	delta = want_pos - targ.origin;
	d = vlen (delta);
	if (d < 0.5)
		return;
	if (d > max_step)
		step = normalize (delta) * max_step;
	else
		step = delta;

	bmin = targ.mins;
	bmax = targ.maxs;
	if (bmin == VEC_ORIGIN && bmax == VEC_ORIGIN)
	{
		bmin = '-16 -16 -24';
		bmax = '16 16 32';
	}

	// First check line-of-sight world geometry so target is never pulled inside solid walls
	traceline (targ.origin, targ.origin + step, TRUE, targ);
	if (trace_fraction < 1)
	{
		step = step * trace_fraction;
		if (trace_plane_normal_z > -0.4 && trace_plane_normal_z < 0.4)
		{
			// Gentle step-up assist over low ledges/curbs
			tracebox (targ.origin + '0 0 18', bmin, bmax, targ.origin + '0 0 18' + normalize (delta) * min (d, max_step), TRUE, targ);
			if (!trace_startsolid && trace_fraction > 0.25)
			{
				setorigin (targ, trace_endpos);
				return;
			}
		}
	}

	next_pos = targ.origin + step;
	tracebox (targ.origin, bmin, bmax, next_pos, TRUE, targ);
	if (!trace_startsolid && !trace_allsolid)
	{
		setorigin (targ, trace_endpos);
		return;
	}

	// If wedged near floor/wall, lift gently by 6u to free hull
	tracebox (targ.origin + '0 0 6', bmin, bmax, next_pos + '0 0 6', TRUE, targ);
	if (!trace_startsolid && !trace_allsolid)
		setorigin (targ, trace_endpos);
};

// ---------------------------------------------------------------- Bonk-Launch strike (auto-equips IT_AXE)

void(entity p) Cyrax_ExecuteBonkLaunch =
{
	local entity targ, old_own;
	local float kind;
	local vector aim_dir, launch_vel, cpos;

	targ = p.cy_hold_targ;
	kind = p.cy_hold_kind;
	if (targ == world || bm_wasfreed (targ))
	{
		Cyrax_ReleaseHold (p);
		return;
	}

	makevectors (p.v_angle);
	aim_dir = normalize (v_forward);
	launch_vel = aim_dir * CY_BONK_SPEED + '0 0 1' * CY_BONK_UP;
	cpos = Cyrax_TargetCenter (targ);

	// Release net trap/wrap before applying launch physics and damage
	Cyrax_ReleaseHold (p);

	Cyrax_Fx (cy_fx_bonk_launch, cpos, aim_dir * 260, 1);
	sound7 (p, CHAN_AUTO, "cyrax/bonk_launch.wav", 1.0, ATTN_NORM, SNDSPD);
	sound7 (p, CHAN_WEAPON, "hammer/frying_pan.wav", 1.0, ATTN_NORM, SNDSPD);
	p.effects = p.effects | EF_MUZZLEFLASH;
	p.punchangle_x = -6.0;
	Hammer_Body1 ();

	if (kind == 0)
	{
		if (targ.health > 0 && !targ.deadflag)
		{
			targ.movetype = MOVETYPE_WALK;
			targ.flags = targ.flags - (targ.flags & FL_ONGROUND);
			tracebox (targ.origin, VEC_HULL_MIN, VEC_HULL_MAX, targ.origin + '0 0 4', TRUE, targ);
			if (!trace_startsolid)
				setorigin (targ, trace_endpos);
			targ.velocity = launch_vel;
			targ.cy_launch_until = time + 0.55;
			targ.disableclientprediction = 1;
			fg_inflicting = FG_CYRAX;
			T_Damage (targ, p, p, CY_BONK_DMG);
			fg_inflicting = 0;
		}
	}
	else if (kind == 1)
	{
		if (targ.health > 0 && !targ.jb_dying)
		{
			if (targ.jb_pilot == world && !targ.jb_ai)
				targ.movetype = MOVETYPE_TOSS;
			targ.flags = targ.flags - (targ.flags & FL_ONGROUND);
			targ.velocity = launch_vel;
			targ.cy_launch_until = time + 0.75;
			fg_inflicting = FG_CYRAX;
			T_Damage (targ, p, p, CY_BONK_DMG);
			fg_inflicting = 0;
		}
	}
	else if (kind == 2)
	{
		if (targ.milky_hp > 0 && targ.takedamage)
		{
			old_own = targ.milky_owner;
			if (old_own != world && !bm_wasfreed (old_own) && old_own.milky_active == targ)
				old_own.milky_active = world;
			targ.milky_owner = p;
			p.milky_active = targ;
			targ.owner = world;
			targ.milky_target = world;
			if (!targ.milky_emerged)
			{
				targ.scale = MILKY_SCALE;
				setsize (targ, MILKY_MIN, MILKY_MAX);
				targ.traileffectnum = particleeffectnum ("milky_trail");
			}
			targ.milky_emerged = TRUE;
			targ.milky_born = time;
			targ.milky_seen = time;
			targ.milky_scan = time + 0.1;
			targ.milky_dir = aim_dir;
			targ.movetype = MOVETYPE_FLY;
			targ.velocity = launch_vel;
			targ.cy_launch_until = time + 0.45;
		}
	}
};

void(entity p) Cyrax_StartBonkWindup =
{
	local entity oself;

	if (p.cy_hold_targ == world || p.cy_bonk_phase > 0)
		return;
	Cyrax_StopCharge (p);
	p.bm_rl_slot = 0;
	p.bm_rl_quiet = FALSE;

	if (p.weapon != IT_AXE)
	{
		p.weapon = IT_AXE;
		oself = self;
		self = p;
		W_SetCurrentAmmo ();
		self = oself;
	}
	p.hm_state = 0;
	p.hm_tier = 3;
	p.hm_ready = time + CY_BONK_WIND_TIME + CY_BONK_FOLLOW_TIME;
	p.attack_finished = time + CY_BONK_WIND_TIME + CY_BONK_FOLLOW_TIME;
	p.cy_bonk_phase = 1;
	p.cy_bonk_t0 = time;
	p.cy_bonk_hit_at = time + CY_BONK_WIND_TIME;
	p.cy_bonk_end = p.cy_bonk_hit_at + CY_BONK_FOLLOW_TIME;
	p.cy_bonk_snd = FALSE;
	sound7 (p, CHAN_AUTO, "hammer/charge_med.wav", 0.55, ATTN_NORM, SNDSPD);
};

// Called from W_WeaponFrame right after Hammer_PlayerFrame
void() Cyrax_BonkFrame =
{
	local float el, k;

	if (self.cy_bonk_phase <= 0)
		return;
	if (self.weapon != IT_AXE || self.health <= 0 || self.deadflag || intermission_running)
	{
		self.cy_bonk_phase = 0;
		return;
	}

	self.hm_state = 0;
	self.hm_ready = time + 0.35;
	self.attack_finished = time + 0.35;

	if (self.cy_bonk_phase == 1)
	{
		if (!self.cy_bonk_snd && time >= self.cy_bonk_t0 + 0.14)
		{
			self.cy_bonk_snd = TRUE;
			sound7 (self, CHAN_AUTO, "hammer/charge_full.wav", 0.85, ATTN_NORM, SNDSPD);
		}
		el = (time - self.cy_bonk_t0) / CY_BONK_WIND_TIME;
		if (el < 0) el = 0;
		if (el > 1) el = 1;
		self.weaponframe = 1 + floor (el * 28);
		if (time >= self.cy_bonk_hit_at)
		{
			self.cy_bonk_phase = 2;
			self.cy_bonk_t0 = time;
			self.cy_bonk_end = time + CY_BONK_FOLLOW_TIME;
			self.weaponframe = 40;
			Cyrax_ExecuteBonkLaunch (self);
		}
		return;
	}

	// Phase 2: Tier-3 hit & follow-through frames (40 -> 41..48 -> 151..158)
	el = time - self.cy_bonk_t0;
	if (el < 0.04)
		self.weaponframe = 40;
	else
	{
		k = floor ((el - 0.04) / 0.03);
		if (k <= 7)
			self.weaponframe = 41 + k;
		else if (k <= 15)
			self.weaponframe = 151 + (k - 8);
		else
		{
			self.weaponframe = 0;
			self.cy_bonk_phase = 0;
			self.hm_ready = time + 0.12;
			self.attack_finished = time + 0.12;
		}
	}
};

// ---------------------------------------------------------------- per-frame player & victim ticks

void(entity p) Cyrax_HoldTick =
{
	local entity targ;
	local vector hold_pt;
	local float d, rem_tenths, dt;

	targ = p.cy_hold_targ;
	if (targ == world)
		return;

	if (bm_wasfreed (targ) || p.health <= 0 || p.deadflag || intermission_running
		|| time >= p.cy_hold_end || p.jb_vehicle != world || p.veh_van != world || p.mmt_tank != world || p.rr_vehicle != world || FD_Flying (p) || EricCannon_Active (p))
	{
		Cyrax_ReleaseHold (p);
		return;
	}

	if (p.cy_hold_kind == 0)
	{
		if (targ.classname != "player" || targ.health <= 0 || targ.deadflag || targ.bm_obs)
		{
			Cyrax_ReleaseHold (p);
			return;
		}
		if (targ != p && targ.weapon != IT_AXE)
			Cyrax_ForceVictimAxe (targ);
	}
	else if (p.cy_hold_kind == 1)
	{
		if (targ.classname != "misc_vehicle_johnbird" || targ.health <= 0 || targ.jb_dying)
		{
			Cyrax_ReleaseHold (p);
			return;
		}
	}
	else
	{
		if (targ.classname != "milky" || targ.milky_hp <= 0 || !targ.takedamage)
		{
			Cyrax_ReleaseHold (p);
			return;
		}
	}

	dt = frametime;
	if (dt < 0.001) dt = 0.001;
	if (dt > 0.05) dt = 0.05;

	hold_pt = Cyrax_CalcHoldPoint (p, targ);
	if (p.cy_hold_kind == 0 && targ != p)
	{
		local vector hsep;
		hsep = hold_pt - p.origin;
		hsep_z = 0;
		if (vlen (hsep) < 38 && fabs (hold_pt_z - p.origin_z) < 56)
		{
			tracebox (targ.origin, VEC_HULL_MIN, VEC_HULL_MAX, p.origin + '0 0 58', TRUE, targ);
			if (!trace_startsolid && !trace_allsolid && trace_fraction > 0.5)
				hold_pt = trace_endpos;
			else
				hold_pt = targ.origin;
		}
	}
	d = vlen (hold_pt - targ.origin);

	if (p.cy_hold_phase == 1)
	{
		Cyrax_MoveToward (targ, hold_pt, CY_PULL_SPEED * dt);
		d = vlen (hold_pt - targ.origin);
		if (d <= CY_HOLD_ENTER_DIST)
		{
			p.cy_hold_phase = 2;
			sound7 (p, CHAN_AUTO, "cyrax/hold_beep.wav", 0.90, ATTN_NORM, SNDSPD);
		}
		else if (time >= p.cy_pull_snd_t)
		{
			p.cy_pull_snd_t = time + 0.78;
			sound7 (p, CHAN_AUTO, "cyrax/pull.wav", 0.72, ATTN_NORM, SNDSPD);
		}
	}
	else
	{
		Cyrax_MoveToward (targ, hold_pt, min (d, max (360 * dt, d * 12 * dt)));
	}

	if (p.cy_hold_wrap != world && !bm_wasfreed (p.cy_hold_wrap))
		Cyrax_PositionWrap (p.cy_hold_wrap, targ);

	if (!p.button0)
		p.cy_click_ready = TRUE;

	rem_tenths = bound (0, ceil ((p.cy_hold_end - time) * 10), 300);
	p.cy_st_mode = (p.cy_hold_phase == 1) ? 2 : 3;
	p.cy_st_prog = rem_tenths;
	p.cy_st_kind = p.cy_hold_kind;
	p.cy_st_dist = floor (vlen (targ.origin - p.origin));

	if (p.cy_hold_kind == 0 && targ != p)
	{
		targ.cy_st_mode = 4;
		targ.cy_st_prog = rem_tenths;
		targ.cy_st_kind = 0;
		targ.cy_st_dist = p.cy_st_dist;
	}
	else if (p.cy_hold_kind == 1 && targ.jb_pilot != world && !bm_wasfreed (targ.jb_pilot))
	{
		targ.jb_pilot.cy_st_mode = 4;
		targ.jb_pilot.cy_st_prog = rem_tenths;
		targ.jb_pilot.cy_st_kind = 1;
		targ.jb_pilot.cy_st_dist = p.cy_st_dist;
	}
};

// Called from FunGun_Attack when self.weapon == IT_FUNGUN && self.fg_sel == FG_CYRAX
void() Cyrax_Press =
{
	if (self.cy_hold_targ != world || self.cy_bonk_phase > 0)
		return;
	if (self.cy_charging > 0)
		return;
	if (self.cy_fire_t > 0 && time < self.cy_fire_t + 0.25)
		return;

	self.cy_charging = time;
	self.cy_vent_t = 0;
	self.cy_charge_fx_t = time + 0.04;
	self.bm_lastshot = time + 1.5;
	self.attack_finished = time + 0.12;
	if (time >= self.cy_charge_snd_t)
	{
		self.cy_charge_snd_t = time + 0.25;
		sound7 (self, CHAN_WEAPON, "cyrax/charge.wav", 0.90, ATTN_NORM, SNDSPD);
	}
};

// Called every frame from FunGun_ViewFrame (before Hammer_PlayerFrame & W_Attack)
void() Cyrax_Frame =
{
	local float busy, held, prog;
	local vector muz;

	if (self.cy_hold_targ != world)
	{
		Cyrax_HoldTick (self);
		if (self.cy_hold_targ != world && self.cy_bonk_phase == 0 && self.cy_click_ready && self.button0)
		{
			if (self.health > 0 && !self.deadflag && !intermission_running
				&& !self.meleeing && !self.throwing && self.cy_trapped_by == world
				&& !FD_Flying (self) && !Veh_Driving (self) && !JohnBird_Flying (self)
				&& !RocketRider_Flying (self) && !EricCannon_Active (self) && !MMTank_Driving (self) && !Binoc_On (self))
			{
				Cyrax_StartBonkWindup (self);
			}
		}
	}

	if (self.cy_charging > 0)
	{
		busy = (self.health <= 0 || self.deadflag || intermission_running
			|| self.weapon != IT_FUNGUN || self.fg_sel != FG_CYRAX
			|| self.bm_rl_slot != 0 || self.meleeing == 1 || self.throwing == 1
			|| self.cy_trapped_by != world
			|| FD_Flying (self) || Veh_Driving (self) || JohnBird_Flying (self) || RocketRider_Flying (self)
			|| EricCannon_Active (self) || MMTank_Driving (self) || Binoc_On (self));

		if (busy)
		{
			Cyrax_StopCharge (self);
		}
		else
		{
			held = time - self.cy_charging;
			prog = held / CY_CHARGE_TIME;
			if (prog < 0) prog = 0;
			if (prog > 1) prog = 1;
			self.bm_lastshot = time + 1.0;

			if (!self.button0)
			{
				// Early release (< 1.1s): abort charge, vent steam/dust, spend NO ammo
				self.cy_charging = 0;
				self.cy_vent_t = time;
				sound7 (self, CHAN_WEAPON, "cyrax/vent.wav", 0.85, ATTN_NORM, SNDSPD);
				makevectors (self.v_angle);
				muz = Cyrax_MuzzlePos (self);
				Cyrax_Fx (cy_fx_muzzle_dust, muz, v_forward * 95, 1);
				self.attack_finished = time + 0.25;
			}
			else if (held >= CY_CHARGE_TIME)
			{
				Cyrax_FireNet (self);
			}
			else
			{
				// Still charging: subtle escalating punchangle shake + muzzle glow particles + HUD %
				self.attack_finished = time + 0.12;
				self.punchangle_x = self.punchangle_x + crandom () * (0.18 + 0.42 * prog);
				self.punchangle_z = self.punchangle_z + crandom () * (0.18 + 0.42 * prog);
				if (time >= self.cy_charge_fx_t)
				{
					self.cy_charge_fx_t = time + 0.08;
					makevectors (self.v_angle);
					muz = Cyrax_MuzzlePos (self);
					Cyrax_Fx (cy_fx_charge_glow, muz, v_forward * 40, 1);
				}
				if (self.cy_hold_targ == world && self.cy_trapped_by == world)
				{
					self.cy_st_mode = 1;
					self.cy_st_prog = bound (0, floor (prog * 100), 100);
					self.cy_st_dist = 0;
				}
			}
		}
	}

	if (self.cy_charging <= 0 && self.cy_hold_targ == world && self.cy_trapped_by == world)
	{
		self.cy_st_mode = 0;
		self.cy_st_prog = 0;
		self.cy_st_dist = 0;
	}

	Cyrax_EnsureVM (self);
};

// ---------------------------------------------------------------- trapped victim enforcement

void() Cyrax_VictimPreThink =
{
	local entity holder;

	holder = self.cy_trapped_by;
	if (holder == world)
		return;
	if (bm_wasfreed (holder) || holder.classname != "player" || holder.health <= 0
		|| (holder.cy_hold_targ != self && (self.jb_vehicle == world || holder.cy_hold_targ != self.jb_vehicle))
		|| time >= self.cy_trapped_end || self.health <= 0 || self.deadflag)
	{
		Cyrax_ReleaseTargetEntity ((self.jb_vehicle != world) ? self.jb_vehicle : self);
		return;
	}
	if (holder == self)
		return;
	self.velocity = '0 0 0';
	self.movement = '0 0 0';
	self.button0 = 0;
	self.button2 = 0;
	self.impulse = 0;
	self.flags = self.flags - (self.flags & FL_ONGROUND);
};

float() Cyrax_VictimWeaponFrame =
{
	local entity holder;

	holder = self.cy_trapped_by;
	if (holder == world)
		return FALSE;
	if (bm_wasfreed (holder) || holder.classname != "player" || holder.health <= 0
		|| (holder.cy_hold_targ != self && (self.jb_vehicle == world || holder.cy_hold_targ != self.jb_vehicle))
		|| time >= self.cy_trapped_end || self.health <= 0 || self.deadflag)
	{
		Cyrax_ReleaseTargetEntity ((self.jb_vehicle != world) ? self.jb_vehicle : self);
		return FALSE;
	}
	if (holder == self)
		return FALSE;
	if (self.jb_vehicle == world && self.weapon != IT_AXE)
		Cyrax_ForceVictimAxe (self);
	self.hm_state = 0;
	self.weaponframe = 0;
	self.meleeing = 0;
	self.throwing = 0;
	self.button0 = 0;
	self.button2 = 0;
	self.impulse = 0;
	self.velocity = '0 0 0';
	return TRUE;
};
