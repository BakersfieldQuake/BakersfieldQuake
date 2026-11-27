#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
DUAL WIELD POWERUP - implementation (Combat+)
================
*/

void() TW_Precache =
{
	if (tw_precached)
		return;
	tw_precached = TRUE;

	precache_model ("progs/triple_wheeled.md3");
	precache_model ("progs/muzzleflash1.spr");
	precache_sound ("triple_wheeled/pickup.wav");
	precache_sound ("triple_wheeled/wearoff.wav");
	precache_sound ("items/itembk2.wav");
	precache_sound ("weapons/sgun1.wav");
	precache_sound ("weapons/rocket2i.wav");
	precache_sound ("weapons/grenade.wav");
	precache_sound ("weapons/lhit.wav");
	precache_sound ("weapons/lstart.wav");
	precache_sound ("hipweap/laserg.wav");
};

float(float w) TW_IsPoolAvailable =
{
	if (w == TW_M4 && !m4_ok)
		return FALSE;
	if (w == 9)
		return FALSE;
	if (w == TW_LG)
	{
		// Only pick LG if v_light.mdl exists (extracted from pak0.pak)
		local float fh;
		fh = fopen ("progs/v_light.mdl", 0);
		if (fh < 0)
			return FALSE;
		fclose (fh);
	}
	return (w >= 1 && w <= TW_POOL_COUNT);
};

float() TW_PickRandomWeapon =
{
	local float tries, pick;

	tries = 0;
	while (tries < 32)
	{
		pick = 1 + floor (random () * TW_POOL_COUNT);
		if (pick > TW_POOL_COUNT)
			pick = TW_POOL_COUNT;
		if (TW_IsPoolAvailable (pick))
			return pick;
		tries = tries + 1;
	}
	return TW_RL;
};

float(entity p) TW_MainWepCode =
{
	local float w, g;

	w = p.weapon;
	if (w == IT_ROCKET_LAUNCHER)	return TW_RL;
	if (w == IT_GRENADE_LAUNCHER)	return TW_GL;
	if (w == IT_SUPER_SHOTGUN)		return TW_SSG;
	if (w == IT_LASER_CANNON)		return TW_LASER;
	if (w == IT_LIGHTNING)			return TW_LG;
	if (w == IT_MEGAMAN)			return TW_MEGAMAN;
	if (w == IT_SUPER_NAILGUN)		return TW_MILKY;
	if (w == IT_AXE)				return TW_AXE;
	if (w == IT_BANANA)				return TW_BANANA;
	if (w == IT_FUNGUN)
	{
		g = p.fg_sel;
		if (g == FG_M4)			return TW_M4;
		if (g == FG_WCANNON)	return TW_WCANNON;
		if (g == FG_DOOKIE)		return TW_DOOKIE;
		if (g == FG_PICKLE)		return TW_PICKLE;
		if (g == FG_PONG)		return TW_GREENJAR;
		if (g == FG_NETSEND)	return TW_NETSEND;
		if (g == FG_KYLE)		return TW_KYLE;
		if (g == FG_CYRAX)		return TW_CYRAX;
		if (g == FG_DOB)		return TW_DOB;
	}
	return TW_RL;
};

string(float tw) TW_WeaponName =
{
	if (tw == TW_RL)		return "Rocket Launcher";
	if (tw == TW_GL)		return "Grenade Launcher";
	if (tw == TW_SSG)		return "Pump Shotgun";
	if (tw == TW_LASER)		return "CCC Laser";
	if (tw == TW_LG)		return "Lightning Gun";
	if (tw == TW_MEGAMAN)	return "Mega Man";
	if (tw == TW_MILKY)		return "Milky Gun";
	if (tw == TW_M4)		return "M4A1";
	if (tw == TW_WCANNON)	return "Wheelman Cannon";
	if (tw == TW_DOOKIE)	return "Dookie Bazooka";
	if (tw == TW_PICKLE)	return "Pickle Surprise";
	if (tw == TW_GREENJAR)	return "Jar o' Green Guys";
	if (tw == TW_NETSEND)	return "NetSend";
	if (tw == TW_KYLE)		return "Pocket Kyle";
	if (tw == TW_CYRAX)		return "Cyrax Net";
	if (tw == TW_AXE)		return "Bonk Hammer";
	if (tw == TW_DOB)		return "Rob Dob";
	if (tw == TW_BANANA)	return "Banana";
	return "Mystery Gun";
};

string(float tw) TW_VModel =
{
	if (tw == TW_RL)		return "progs/v_rock2.mdl";
	if (tw == TW_GL)		return "progs/v_rock.mdl";
	if (tw == TW_SSG)		return "progs/v_shot2.mdl";
	if (tw == TW_LASER)		return "progs/v_laserg.mdl";
	if (tw == TW_LG)		return "progs/v_light.mdl";
	if (tw == TW_MEGAMAN)	return "progs/v_megaman.md3";
	if (tw == TW_MILKY)		return "progs/v_milky.md3";
	if (tw == TW_M4)		return "progs/v_m4.md3";
	if (tw == TW_WCANNON)	return "progs/v_wewcannon.md3";
	if (tw == TW_DOOKIE)	return "progs/v_dookie.md3";
	if (tw == TW_PICKLE)	return "progs/v_pickle.md3";
	if (tw == TW_GREENJAR)	return "progs/v_greenjar.md3";
	if (tw == TW_NETSEND)	return "progs/v_netsend.md3";
	if (tw == TW_KYLE)		return "progs/v_kyle.md3";
	if (tw == TW_CYRAX)		return "progs/v_cyrax.md3";
	return "progs/v_rock2.mdl";
};

// Base viewmodel offset for slot (1=Bottom-Left upright, 2=Top-Right upside-down, 3=Top-Left upside-down).
// viewmodelforclient coordinates: +X = forward, +Y = left, -Y = right, +Z = up, -Z = down.
// Note: angles_z = 180 rolls (x, y, z) -> (x, -y, -z), flipping bottom-right into top-left automatically.
vector(float tw, float slot) TW_VModelBaseOrg =
{
	// 2D card MD3s (x=14, y=[-28..0], z=[-19..8])
	if (tw == TW_MILKY || tw == TW_DOOKIE || tw == TW_PICKLE || tw == TW_GREENJAR || tw == TW_KYLE || tw == TW_CYRAX || tw == TW_NETSEND)
	{
		if (slot == 1)	return '6 25 -3';
		if (slot == 2)	return '6 -25 4';
		return '6 2 4';
	}
	if (tw == TW_RL)
	{
		if (slot == 1)	return '0 23 -1';
		if (slot == 2)	return '0 -23 2';
		return '0 7 2';
	}
	if (tw == TW_GL)
	{
		if (slot == 1)	return '0 16 0';
		if (slot == 2)	return '0 -16 2';
		return '0 14 2';
	}
	if (tw == TW_SSG)
	{
		if (slot == 1)	return '0 18 1';
		if (slot == 2)	return '0 -18 1';
		return '0 12 1';
	}
	if (tw == TW_LASER)
	{
		if (slot == 1)	return '0 16 0';
		if (slot == 2)	return '0 -16 2';
		return '0 14 2';
	}
	if (tw == TW_LG)
	{
		if (slot == 1)	return '0 15 0';
		if (slot == 2)	return '0 -15 2';
		return '0 15 2';
	}
	if (tw == TW_MEGAMAN)
	{
		if (slot == 1)	return '2 19 -4';
		if (slot == 2)	return '2 -19 5';
		return '2 7 5';
	}
	if (tw == TW_M4)
	{
		if (slot == 1)	return '0 26 0';
		if (slot == 2)	return '0 -26 1';
		return '0 4 1';
	}
	if (tw == TW_WCANNON)
	{
		if (slot == 1)	return '0 23 -1';
		if (slot == 2)	return '0 -23 3';
		return '0 6 3';
	}
	if (slot == 1)	return '0 20 0';
	if (slot == 2)	return '0 -20 2';
	return '0 10 2';
};

// World muzzle flash position in viewmodelforclient coordinates for slot 1..3
vector(float slot) TW_FlashOrg =
{
	if (slot == 1)	return '36 14 -8';
	if (slot == 2)	return '36 -14 8';
	return '36 14 8';
};

float(entity p) TW_ViewHidden =
{
	if (!p || p.classname != "player" || p.health <= 0 || p.deadflag || p.bm_obs || intermission_running)
		return TRUE;
	if (FD_Flying (p) || Veh_Driving (p) || p.veh_ride != world)
		return TRUE;
	if (JohnBird_Flying (p) || RocketRider_Flying (p) || EricCannon_Active (p) || MMTank_Driving (p) || Binoc_On (p))
		return TRUE;
	if (p.cy_trapped_by != world)
		return TRUE;
	return FALSE;
};

void(entity p) TW_ClearStats =
{
	p.tw_st_rem = 0;
	p.tw_st_wep0 = 0;
	p.tw_st_wep1 = 0;
	p.tw_st_step = 0;
};

void(entity p) TW_RemoveEntities =
{
	if (p.tw_vm1 != world && !bm_wasfreed (p.tw_vm1))
		remove (p.tw_vm1);
	if (p.tw_halo != world && !bm_wasfreed (p.tw_halo))
		remove (p.tw_halo);
	p.tw_vm1 = world;
	p.tw_halo = world;
};

void(entity p) TW_Reset =
{
	if (p == world || bm_wasfreed (p))
		return;
	TW_RemoveEntities (p);
	p.tw_end_t = 0;
	p.tw_wep1 = 0;
	p.tw_seq_step = 0;
	p.tw_seq_next = 0;
	p.tw_fire_t0 = 0;
	p.tw_fire_t1 = 0;
	p.tw_warn_stage = 0;
	TW_ClearStats (p);
};

// Keep current held weapon loaded while Dual Wield is active so short chaos never stalls in a 2.5s reload
void(entity p) TW_TopUpHeldWeapon =
{
	local float s, m, g;

	if (p.bm_rl_slot)
	{
		p.bm_rl_slot = 0;
		p.bm_rl_quiet = FALSE;
	}
	if (p.bm_vm_hidden && p.bm_vm_str != "")
	{
		p.weaponmodel = p.bm_vm_str;
		p.bm_vm_hidden = 0;
	}

	if (autocvar_bm_reload)
	{
		s = BM_CurSlot ();
		if (s > 0)
		{
			m = BM_MagSize (s);
			if (m > 0 && BM_GetMag (p, s) < 1)
				BM_SetMag (p, s, m);
		}
	}

	if (p.weapon == IT_ROCKET_LAUNCHER || p.weapon == IT_GRENADE_LAUNCHER)
	{
		if (p.ammo_rockets < 1)
		{
			p.ammo_rockets = autocvar_bm_reload ? BM_MagSize (p.weapon == IT_ROCKET_LAUNCHER ? BM_RL : BM_GL) : 10;
			p.currentammo = p.ammo_rockets;
		}
	}
	else if (p.weapon == IT_SUPER_SHOTGUN)
	{
		if (p.ammo_shells < 1)
		{
			p.ammo_shells = autocvar_bm_reload ? BM_MagSize (BM_SSG) : 12;
			p.currentammo = p.ammo_shells;
		}
	}
	else if (p.weapon == IT_SUPER_NAILGUN)
	{
		if (p.ammo_nails < 2)
		{
			p.ammo_nails = autocvar_bm_reload ? BM_MagSize (BM_SNG) : 20;
			p.currentammo = p.ammo_nails;
		}
	}
	else if (p.weapon == IT_LIGHTNING || p.weapon == IT_LASER_CANNON)
	{
		if (p.ammo_cells < 1)
		{
			p.ammo_cells = autocvar_bm_reload ? BM_MagSize (p.weapon == IT_LIGHTNING ? BM_LG : BM_LASER) : 30;
			p.currentammo = p.ammo_cells;
		}
	}
	else if (p.weapon == IT_MEGAMAN)
	{
		if (p.mm_ammo < 1)
		{
			p.mm_ammo = MM_MAX_AMMO;
			p.currentammo = p.mm_ammo;
		}
	}
	else if (p.weapon == IT_FUNGUN)
	{
		g = p.fg_sel;
		if (FunGun_Ammo (p, g) < 1)
			FunGun_SetAmmo (p, g, FunGun_Max (g));
		p.fg_lock_t = 0;
	}
};

void(entity p, float force_all_rl) TW_Activate =
{
	local float dur;

	if (p == world || p.classname != "player" || p.health <= 0 || p.deadflag)
		return;
	if (!tw_precached)
		TW_Precache ();

	dur = bound (4, autocvar_bm_triple_dur, 60);
	p.tw_end_t = time + dur;
	p.tw_seq_step = 0;
	p.tw_seq_next = 0;
	p.tw_fire_t0 = 0;
	p.tw_fire_t1 = 0;
	p.tw_warn_stage = 0;

	if (force_all_rl)
	{
		p.items = p.items | IT_ROCKET_LAUNCHER;
		if (p.ammo_rockets < 5)
			p.ammo_rockets = 5;
		p.weapon = IT_ROCKET_LAUNCHER;
		W_SetCurrentAmmo ();
		p.tw_wep1 = TW_RL;
	}
	else
	{
		p.tw_wep1 = TW_PickRandomWeapon ();
	}

	TW_TopUpHeldWeapon (p);
	sound7 (p, CHAN_VOICE, "triple_wheeled/pickup.wav", 1, ATTN_NORM, SNDSPD);
	if (p.ishuman == 1)
	{
		stuffcmd (p, "bf\n");
		centerprint (p, strcat (
			"^3DUAL WIELD!!\n^7MAIN: ^2", TW_WeaponName (TW_MainWepCode (p)),
			"  ^7LEFT: ^6", TW_WeaponName (p.tw_wep1)
		));
	}
};

// -----------------------------------------------------------------------------
// 1st-Person Viewmodel (Left upright)
// -----------------------------------------------------------------------------

void(entity vm, float tw, float slot, float fire_t) TW_UpdateSingleVM =
{
	local entity p;
	local vector org, ang;
	local float dt, kick, sw_y, sw_z, fr;

	p = vm.owner;
	if (TW_ViewHidden (p) || time >= p.tw_end_t)
	{
		vm.alpha = -1;
		return;
	}

	if (vm.model != TW_VModel (tw))
		setmodel (vm, TW_VModel (tw));

	vm.alpha = 1.0;
	vm.skin = 0;
	vm.frame = 0;

	org = TW_VModelBaseOrg (tw, slot);
	if (slot == 1)
		ang = '0 -3 0';
	else if (slot == 2)
		ang = '0 3 180';
	else
		ang = '0 -3 180';

	// Subtle independent bob per corner so all 4 guns feel hilariously alive
	sw_y = sin (time * 3.1 + slot * 1.7);
	sw_z = cos (time * 4.2 + slot * 2.1);
	org_y = org_y + sw_y * 0.28;
	org_z = org_z + sw_z * 0.25;

	// Fire kickback & model frames when this corner fires
	if (fire_t > 0)
	{
		dt = time - fire_t;
		if (dt >= 0 && dt < 0.28)
		{
			kick = 1.0 - (dt / 0.28);
			kick = kick * kick;
			org_x = org_x - 4.2 * kick;
			if (slot == 1)
				ang_x = ang_x - 6.5 * kick;
			else
				ang_x = ang_x + 6.5 * kick;	// upside down: positive pitch kicks muzzle upward on screen

			if (tw == TW_M4)
			{
				fr = M4_FIRE_FIRST + min (M4_FIRE_COUNT - 1, floor (dt * M4_FIRE_FPS));
				vm.frame = fr;
			}
			else if (tw == TW_MEGAMAN)
			{
				vm.frame = min (35, 16 + floor (dt * 30));
			}
			else if (tw == TW_WCANNON)
			{
				vm.frame = min (47, 26 + floor (dt * 36));
			}
			else if (tw == TW_RL || tw == TW_GL || tw == TW_SSG || tw == TW_LASER || tw == TW_LG)
			{
				vm.frame = 1 + min (4, floor (dt * 18));
			}
		}
	}

	vm.origin = org;
	vm.angles = ang;
};

void() TW_VMThink =
{
	local entity p;

	p = self.owner;
	if (p == world || bm_wasfreed (p) || p.classname != "player" || time >= p.tw_end_t || intermission_running)
	{
		if (p != world && !bm_wasfreed (p))
		{
			if (p.tw_vm1 == self) p.tw_vm1 = world;
		}
		remove (self);
		return;
	}
	TW_UpdateSingleVM (self, p.tw_wep1, 1, p.tw_fire_t1);
	self.nextthink = time;
};

entity(entity p, float tw, float slot) TW_SpawnVM =
{
	local entity vm;

	vm = spawn ();
	vm.classname = "tw_vm";
	vm.owner = p;
	vm.viewmodelforclient = p;
	vm.movetype = MOVETYPE_NONE;
	vm.solid = SOLID_NOT;
	setmodel (vm, TW_VModel (tw));
	setsize (vm, VEC_ORIGIN, VEC_ORIGIN);
	vm.think = TW_VMThink;
	vm.nextthink = time;
	TW_UpdateSingleVM (vm, tw, slot, 0);
	return vm;
};

void() TW_HaloThink =
{
	local entity p;
	local float s_roll;

	p = self.owner;
	if (p == world || bm_wasfreed (p) || p.classname != "player" || p.health <= 0 || p.deadflag || p.bm_obs || time >= p.tw_end_t || intermission_running)
	{
		if (p != world && !bm_wasfreed (p) && p.tw_halo == self)
			p.tw_halo = world;
		remove (self);
		return;
	}
	self.angles_y = anglemod (time * 260);
	s_roll = sin (time * 4.5);
	self.angles_z = s_roll * 12;
	self.frame = floor (time * 16) - 16 * floor (floor (time * 16) / 16);
	setorigin (self, p.origin + '0 0 42');
	self.nextthink = time + 0.02;
};

void(entity p) TW_EnsureVisuals =
{
	if (p.ishuman == 1)
	{
		if (p.tw_vm1 == world || bm_wasfreed (p.tw_vm1) || p.tw_vm1.owner != p)
			p.tw_vm1 = TW_SpawnVM (p, p.tw_wep1, 1);
	}
	if ((p.tw_halo == world || bm_wasfreed (p.tw_halo) || p.tw_halo.owner != p) && p.health > 0)
	{
		local entity h;
		h = spawn ();
		h.classname = "tw_halo";
		h.owner = p;
		h.exteriormodeltoclient = p;
		h.movetype = MOVETYPE_NONE;
		h.solid = SOLID_NOT;
		h.scale = 0.48;
		h.effects = EF_FULLBRIGHT;
		setmodel (h, "progs/triple_wheeled.md3");
		setsize (h, VEC_ORIGIN, VEC_ORIGIN);
		setorigin (h, p.origin + '0 0 42');
		h.think = TW_HaloThink;
		h.nextthink = time + 0.02;
		p.tw_halo = h;
	}
};

// -----------------------------------------------------------------------------
// Sequential Firing of the 3 Extra Weapons from Their Screen Corners
// -----------------------------------------------------------------------------

void(float slot) TW_SpawnCornerFlash =
{
	local entity fl;

	if (self.ishuman != 1 || self.waterlevel >= 3)
		return;
	fl = spawn ();
	fl.movetype = 0;
	fl.solid = 0;
	fl.viewmodelforclient = self;
	fl.owner = self;
	fl.classname = "tw_flash";
	fl.effects = EF_ADDITIVE;
	setmodel (fl, "progs/muzzleflash1.spr");
	fl.scale = 0.38;
	fl.alpha = 0.85;
	setsize (fl, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (fl, TW_FlashOrg (slot));
	fl.think = SUB_Remove;
	fl.nextthink = time + 0.05;
};

void(float tw, float slot) TW_FireSlot =
{
	local vector eye, want, muz, aim_pt, dir;
	local entity e;
	local float i, dmg, dist, spd;

	if (TW_ViewHidden (self))
		return;

	makevectors (self.v_angle);
	eye = self.origin + self.view_ofs;
	traceline (eye, eye + v_forward * 2048, FALSE, self);
	if (trace_fraction * 2048 < 96)
		aim_pt = eye + v_forward * 256;
	else
		aim_pt = trace_endpos;

	if (slot == 1)
		want = eye + v_forward * 14 - v_right * 12 - v_up * 6;
	else if (slot == 2)
		want = eye + v_forward * 14 + v_right * 12 + v_up * 7;
	else
		want = eye + v_forward * 14 - v_right * 12 + v_up * 7;

	tracebox (eye, '-4 -4 -4', '4 4 4', want, TRUE, self);
	muz = trace_endpos;
	dir = normalize (aim_pt - muz);
	if (dir == VEC_ORIGIN)
		dir = v_forward;

	self.effects = self.effects | EF_MUZZLEFLASH;
	self.show_hostile = time + 1;
	TW_SpawnCornerFlash (slot);

	self.tw_fire_t1 = time;

	if (tw == TW_RL)
	{
		sound7 (self, CHAN_AUTO, "weapons/sgun1.wav", 0.9, ATTN_NORM, self.PLR_SNDSPD);
		sound7 (self, CHAN_AUTO, "weapons/rocket2i.wav", 0.75, ATTN_NORM, self.PLR_SNDSPD);
		self.punchangle_x = self.punchangle_x - 1.6;
		e = spawn ();
		e.cansplash = TRUE;
		e.owner = self;
		e.movetype = MOVETYPE_FLYMISSILE;
		e.solid = SOLID_BBOX;
		e.classname = "missile";
		e.velocity = dir * 1000;
		e.angles = vectoangles (e.velocity);
		e.touch = T_MissileTouch;
		e.nextthink = time + 5;
		e.think = SUB_Remove;
		setmodel (e, "progs/missile.mdl");
		setsize (e, VEC_ORIGIN, VEC_ORIGIN);
		setorigin (e, muz);
		PC_Register (e, PC_KIND_LIGHT, 20);
		return;
	}

	if (tw == TW_GL)
	{
		sound7 (self, CHAN_AUTO, "weapons/grenade.wav", 0.9, ATTN_NORM, self.PLR_SNDSPD);
		self.punchangle_x = self.punchangle_x - 1.4;
		e = spawn ();
		e.cansplash = TRUE;
		e.owner = self;
		e.movetype = MOVETYPE_BOUNCE;
		e.solid = SOLID_BBOX;
		e.classname = "grenade";
		e.nextthink = time + 2.5;
		e.think = GrenadeExplode;
		e.velocity = dir * 600 + v_up * 200;
		e.avelocity = '300 300 300';
		e.angles = vectoangles (e.velocity);
		e.touch = GrenadeTouch;
		setmodel (e, "progs/grenade.mdl");
		setsize (e, VEC_ORIGIN, VEC_ORIGIN);
		setorigin (e, muz);
		PC_Register (e, PC_KIND_LIGHT, 20);
		return;
	}

	if (tw == TW_SSG)
	{
		sound7 (self, CHAN_AUTO, "dn3sg/fire.wav", 0.9, ATTN_NORM, self.PLR_SNDSPD);
		self.punchangle_x = self.punchangle_x - 1.5;
		ClearMultiDamage ();
		i = 0;
		while (i < DN3SG_PELLETS)
		{
			local vector sdir;
			sdir = normalize (dir + (crandom () * 0.063 * v_right) + (crandom () * 0.063 * v_up));
			traceline (muz, muz + sdir * 2048, FALSE, self);
			if (i < 4 && dn3sg_fx_tracer >= 0 && trace_fraction > 0.02)
				trailparticles (self, dn3sg_fx_tracer, muz, trace_endpos);
			if (!PC_TraceIntercept (self, muz, trace_endpos, DN3SG_PELLET_DMG) && trace_fraction != 1)
			{
				if (trace_ent.takedamage || trace_ent.inflamed == 1)
					TraceAttack (DN3SG_PELLET_DMG, sdir);
				else
					DN3SG_WallImpact (sdir);
			}
			i = i + 1;
		}
		W_BulletSplash (dir);
		ApplyMultiDamage ();
		return;
	}

	if (tw == TW_LASER)
	{
		sound7 (self, CHAN_AUTO, "hipweap/laserg.wav", 0.85, ATTN_NORM, self.PLR_SNDSPD);
		self.punchangle_x = self.punchangle_x - 0.8;
		HIP_LaunchLaser (muz + v_right * 3, dir, 0);
		HIP_LaunchLaser (muz - v_right * 3, dir, 0);
		return;
	}

	if (tw == TW_LG)
	{
		sound7 (self, CHAN_AUTO, "weapons/lhit.wav", 0.85, ATTN_NORM, self.PLR_SNDSPD);
		self.punchangle_x = self.punchangle_x - 0.9;
		traceline (muz, muz + dir * 600, TRUE, self);
		WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte (MSG_BROADCAST, TE_LIGHTNING2);
		WriteEntity (MSG_BROADCAST, self);
		WriteCoord (MSG_BROADCAST, muz_x);
		WriteCoord (MSG_BROADCAST, muz_y);
		WriteCoord (MSG_BROADCAST, muz_z);
		WriteCoord (MSG_BROADCAST, trace_endpos_x);
		WriteCoord (MSG_BROADCAST, trace_endpos_y);
		WriteCoord (MSG_BROADCAST, trace_endpos_z);
		LightningDamage (muz, trace_endpos + dir * 4, self, autocvar_player_lightninggun * 1.5);
		return;
	}

	if (tw == TW_MEGAMAN)
	{
		sound7 (self, CHAN_AUTO, "weapons/grenade.wav", 0.85, ATTN_NORM, SNDSPD);
		MegaMan_Larry ();
		self.punchangle_x = self.punchangle_x - 1.5;
		e = spawn ();
		e.owner = self;
		e.classname = "megaman";
		e.movetype = MOVETYPE_TOSS;
		e.solid = SOLID_BBOX;
		e.mm_state = 0;
		e.mm_born = time;
		e.mm_leap_t = time + 0.6;
		e.mm_side = (random () < 0.5) ? -1 : 1;
		e.velocity = dir * 620 + '0 0 120';
		e.angles = '0 0 0';
		e.angles_y = vectoyaw (dir);
		e.effects = 0;
		e.takedamage = DAMAGE_YES;
		e.health = MM_HEALTH;
		e.th_die = MegaMan_Shot;
		e.touch = MegaMan_Touch;
		e.think = MegaMan_Think;
		e.nextthink = time + 0.05;
		setmodel (e, "progs/megaman.md3");
		setsize (e, '-16 -16 0', '16 16 24');
		tracebox (eye, '-16 -16 0', '16 16 24', muz, TRUE, self);
		setorigin (e, trace_endpos);
		PC_Register (e, PC_KIND_HEAVY, 28);
		return;
	}

	if (tw == TW_MILKY)
	{
		if (!Milky_Room ())
			return;
		Milky_Snd (self, CHAN_AUTO, "milky/fire.wav", 0.75, ATTN_NORM);
		self.punchangle_x = self.punchangle_x - 1.4;
		e = spawn ();
		e.classname = "milky";
		e.milky_owner = self;
		e.owner = self;
		e.movetype = MOVETYPE_NOCLIP;
		e.solid = SOLID_BBOX;
		e.effects = EF_FULLBRIGHT;
		e.takedamage = DAMAGE_AIM;
		e.health = MILKY_HEALTH;
		e.max_health = MILKY_HEALTH;
		e.milky_hp = MILKY_HEALTH;
		e.dodge_finished = time + 999999;
		e.milky_dir = dir;
		e.milky_born = time;
		e.milky_seen = time;
		e.milky_scan = time + 0.2;
		e.milky_from = muz;
		e.milky_to = muz + dir * 88;
		e.milky_emerged = FALSE;
		e.milky_last = e.milky_to;
		e.milky_lastt = time;
		e.milky_phase = random () * 6.28;
		e.milky_drip = time + 0.08;
		e.milky_ptrail = time + 0.28;
		e.scale = 2.1;
		e.customizeentityforclient = Milky_Customize;
		e.touch = Milky_Touch;
		e.think = Milky_Think;
		e.nextthink = time + 0.02;
		setmodel (e, "progs/pinklady.md3");
		setsize (e, '-14 -14 -24', '14 14 20');
		setorigin (e, muz);
		e.velocity = (e.milky_to - muz) * (1.375 / MILKY_EMERGE);
		Milky_Snd (e, CHAN_VOICE, "milky/song.ogg", MILKY_SONG_VOL, MILKY_SONG_ATTN);
		milky_count = milky_count + 1;
		PC_Register (e, PC_KIND_HEAVY, 36);
		return;
	}

	if (tw == TW_M4)
	{
		sound7 (self, CHAN_AUTO, (random () < 0.5) ? m4_snd_fire1 : m4_snd_fire2, 0.9, ATTN_NORM, SNDSPD);
		self.punchangle_x = self.punchangle_x - 0.9;
		ClearMultiDamage ();
		traceline (muz, muz + dir * M4_RANGE, FALSE, self);
		dist = trace_fraction * M4_RANGE;
		dmg = M4_DAMAGE * 1.4;
		if (!PC_TraceIntercept (self, muz, trace_endpos, dmg) && trace_fraction != 1)
		{
			if (trace_ent.takedamage || trace_ent.inflamed == 1)
				TraceAttack (dmg, dir);
			else
				M4_WallImpact (dir);
		}
		W_BulletSplash (dir);
		fg_inflicting = FG_M4;
		ApplyMultiDamage ();
		fg_inflicting = 0;
		return;
	}

	if (tw == TW_WCANNON)
	{
		WC_PrecacheSprites ();
		spd = WC_SPEED_MIN + (WC_SPEED_MAX - WC_SPEED_MIN) * 0.75;
		e = spawn ();
		e.classname = "wc_shot";
		e.owner = self;
		e.movetype = MOVETYPE_NONE;
		e.solid = SOLID_BBOX;
		e.takedamage = DAMAGE_NO;
		e.health = WC_HEALTH;
		e.th_die = WC_Die;
		e.fg_born = time;
		e.wc_t = time;
		e.wc_tier = 2;
		e.wc_speed = spd;
		e.wc_dir = normalize ('1 0 0' * dir_x + '0 1 0' * dir_y);
		if (e.wc_dir == VEC_ORIGIN)
			e.wc_dir = v_forward;
		e.angles_y = vectoyaw (dir);
		setmodel (e, "progs/wheelman.spr32");
		e.scale = WC_SCALE;
		setsize (e, '-14 -14 0', '14 14 48');
		tracebox (eye, '-14 -14 0', '14 14 48', muz, TRUE, self);
		setorigin (e, trace_endpos);
		e.velocity = dir * spd;
		e.customizeentityforclient = WC_ShotCustomize;
		e.touch = WC_Touch;
		e.think = WC_Think;
		e.nextthink = time + 0.02;
		e.wc_snd = time + WC_SCREAM_GAP;
		PC_Register (e, PC_KIND_HEAVY, 32);
		sound (e, CHAN_VOICE, WC_ScreamClip (), WC_SCREAM_VOL, ATTN_NORM);
		sound7 (self, CHAN_AUTO, "wcannon/wc_shoot.wav", 0.75, ATTN_NORM, SNDSPD);
		self.punchangle_x = self.punchangle_x - 2.2;
		return;
	}

	if (tw == TW_DOOKIE)
	{
		spd = DK_SPEED_MIN + (DK_SPEED_MAX - DK_SPEED_MIN) * 0.75;
		e = spawn ();
		e.classname = "dookie_shot";
		e.owner = self;
		e.movetype = MOVETYPE_FLYMISSILE;
		e.solid = SOLID_BBOX;
		e.takedamage = DAMAGE_NO;
		e.health = DK_HEALTH;
		e.th_die = DK_ProjDie;
		e.fg_born = time;
		e.dk_charge = 0.75;
		e.dk_done = FALSE;
		e.angles_y = vectoyaw (dir);
		setmodel (e, "progs/dookie_proj.spr32");
		e.scale = DK_SCALE;
		setsize (e, VEC_ORIGIN, VEC_ORIGIN);
		setorigin (e, muz);
		e.velocity = dir * spd;
		e.traileffectnum = particleeffectnum ("dookie_glob");
		e.customizeentityforclient = DK_ProjCustomize;
		e.touch = DK_ProjTouch;
		e.think = DK_ProjThink;
		e.nextthink = time + 0.05;
		e.dk_yell_t = time + 1.35;
		PC_Register (e, PC_KIND_DOOKIE, 32);
		sound7 (self, CHAN_AUTO, "dookie/dk_fire.wav", 0.9, ATTN_NORM, SNDSPD);
		DK_PlayFlightYell (e);
		self.punchangle_x = self.punchangle_x - 2.0;
		return;
	}

	if (tw == TW_PICKLE)
	{
		Pk_MakeRoom (self);
		e = spawn ();
		e.owner = self;
		e.classname = "pickle";
		e.movetype = MOVETYPE_TOSS;
		e.solid = SOLID_BBOX;
		e.fg_born = time;
		e.pk_state = 1;
		e.velocity = dir * PK_THROW + v_up * 36;
		e.angles_y = vectoyaw (dir);
		e.scale = 1.92;
		e.takedamage = DAMAGE_YES;
		e.health = PK_HEALTH;
		e.th_die = Pk_Shot;
		e.touch = Pk_Touch;
		e.think = Pk_Think;
		e.nextthink = time + 0.02;
		e.customizeentityforclient = Pk_Customize;
		setmodel (e, "progs/pickle_throw.md3");
		e.traileffectnum = particleeffectnum ("pk_throw_trail");
		setsize (e, '-5 -5 -5', '5 5 5');
		tracebox (eye, '-5 -5 -5', '5 5 5', muz, TRUE, self);
		setorigin (e, trace_endpos);
		PC_Register (e, PC_KIND_LIGHT, 20);
		sound7 (self, CHAN_AUTO, "pickle/throw.wav", 0.85, ATTN_NORM, SNDSPD);
		return;
	}

	if (tw == TW_GREENJAR)
	{
		e = spawn ();
		e.classname = "greenjar_proj";
		e.owner = self;
		e.fg_born = time;
		e.movetype = MOVETYPE_TOSS;
		e.solid = SOLID_BBOX;
		e.effects = EF_DIMLIGHT;
		e.velocity = dir * 920 + v_up * 200;
		setmodel (e, "progs/greenjar_proj.spr32");
		e.scale = 0.52;
		e.frame = 0;
		setsize (e, '-4 -4 -4', '4 4 4');
		tracebox (eye, '-4 -4 -4', '4 4 4', muz, TRUE, self);
		setorigin (e, trace_endpos);
		e.touch = GJ_ProjTouch;
		e.think = GJ_ProjThink;
		e.nextthink = time + 0.035;
		PC_Register (e, PC_KIND_LIGHT, 20);
		sound7 (self, CHAN_AUTO, "greenjar/jar_throw.wav", 0.85, ATTN_NORM, SNDSPD);
		return;
	}

	if (tw == TW_NETSEND)
	{
		e = spawn ();
		e.owner = self;
		e.classname = "netsend_disk";
		e.movetype = MOVETYPE_BOUNCE;
		e.solid = SOLID_BBOX;
		e.fg_born = time;
		e.velocity = dir * NS_THROW + v_up * 60;
		e.avelocity_y = 900;
		e.bouncefactor = 0.35;
		e.bouncestop = 0.1;
		e.touch = NS_DiskTouch;
		e.think = NS_DiskThink;
		e.nextthink = time + 0.1;
		setmodel (e, "progs/netsend_sentry_floppy.md3");
		setsize (e, '-5 -5 -1', '5 5 1');
		tracebox (eye, '-5 -5 -1', '5 5 1', muz, TRUE, self);
		setorigin (e, trace_endpos);
		PC_Register (e, PC_KIND_LIGHT, 20);
		sound7 (self, CHAN_AUTO, "netsend/disk_throw.wav", 0.9, ATTN_NORM, SNDSPD);
		return;
	}

	if (tw == TW_KYLE)
	{
		KY_Launch (self, FALSE, world, 0.85);
		return;
	}

	if (tw == TW_CYRAX)
	{
		Cyrax_FireNet (self, FALSE);
		return;
	}
};

void() TW_TriggerSequence =
{
	local float delay;

	if (self.tw_end_t <= time)
		return;
	self.tw_fire_t0 = time;
	// If a 1->2->3 cascade is already running, let it finish before starting the next burst
	if (self.tw_seq_step > 0)
		return;
	delay = bound (0.15, autocvar_bm_triple_delay, 1.0);
	self.tw_seq_step = 1;
	self.tw_seq_next = time + delay;
};

void() TW_Frame =
{
	local float rem, fl, w0;

	if (self.tw_end_t <= 0)
		return;

	if (self.health <= 0 || self.deadflag || self.bm_obs || intermission_running)
	{
		TW_Reset (self);
		return;
	}

	if (time >= self.tw_end_t)
	{
		sound7 (self, CHAN_AUTO, "triple_wheeled/wearoff.wav", 0.85, ATTN_NORM, SNDSPD);
		if (self.ishuman == 1)
			centerprint (self, "^3Dual Wield ^7wore off!");
		TW_Reset (self);
		return;
	}

	TW_TopUpHeldWeapon (self);
	TW_EnsureVisuals (self);

	// Expiration warnings in last 3 seconds
	rem = self.tw_end_t - time;
	if (rem < 3.0 && self.tw_warn_stage < 1)
	{
		self.tw_warn_stage = 1;
		if (self.ishuman == 1)
			sprint (self, "Dual Wield is wearing off...\n");
	}

	// Sequential firing tick (slot 1 left weapon)
	if (self.tw_seq_step > 0 && time >= self.tw_seq_next)
	{
		TW_FireSlot (self.tw_wep1, 1);
		self.tw_seq_step = 0;
		self.tw_seq_next = 0;
	}

	// Update CSQC HUD stats
	if (self.ishuman == 1)
	{
		w0 = TW_MainWepCode (self);
		fl = self.tw_seq_step * 16;
		if (self.tw_fire_t0 > 0 && time - self.tw_fire_t0 < 0.22) fl = fl | 1;
		if (self.tw_fire_t1 > 0 && time - self.tw_fire_t1 < 0.22) fl = fl | 2;

		self.tw_st_rem = ceil (rem * 10);
		self.tw_st_wep0 = w0;
		self.tw_st_wep1 = self.tw_wep1;
		self.tw_st_step = fl;
	}
};

// -----------------------------------------------------------------------------
// Spinning & Glowing 2-Rocket-Launcher Powerup Entity: item_powerup_triple_wheeled
// -----------------------------------------------------------------------------

void() TW_ItemThink;

void() TW_ItemRespawn =
{
	self.model = self.mdl;
	self.solid = SOLID_TRIGGER;
	self.nextthink = time + 0.05;
	self.think = TW_ItemThink;
	sound (self, CHAN_VOICE, "items/itembk2.wav", 1, ATTN_NORM);
	setorigin (self, self.tw_spawn_org);
};

void() TW_ItemThink =
{
	local float bob;

	if (self.solid == SOLID_TRIGGER)
	{
		local float s_tilt, s_bob;

		self.angles_y = anglemod (self.angles_y + 220 * 0.05);
		s_tilt = sin (time * 2.6);
		self.angles_z = s_tilt * 10;
		self.frame = floor (time * 16) - 16 * floor (floor (time * 16) / 16);
		s_bob = sin (time * 3.4);
		bob = s_bob * 4.5;
		setorigin (self, self.tw_spawn_org + '0 0 1' * bob);
		if (time >= self.tw_fx_t)
		{
			self.tw_fx_t = time + 0.16;
			if (veh_fx_drift > 0)
				pointparticles (veh_fx_drift, self.origin, '0 0 0', 1);
		}
	}
	self.nextthink = time + 0.05;
};

void() TW_ItemTouch =
{
	if (other.classname != "player" || other.health <= 0 || other.deadflag || other.bm_obs)
		return;
	if (Veh_Driving (other) || other.veh_ride != world || MMTank_Driving (other) || JohnBird_Flying (other) || RocketRider_Flying (other) || EricCannon_Active (other) || FD_Flying (other))
		return;

	if (deathmatch)
	{
		self.solid = SOLID_NOT;
		self.model = "";
		self.think = TW_ItemRespawn;
		self.nextthink = time + 45;
	}
	else
	{
		self.solid = SOLID_NOT;
		self.model = "";
		self.think = SUB_Remove;
		self.nextthink = time + 0.1;
	}

	TW_Activate (other, FALSE);
};

void() TW_ItemDrop =
{
	self.flags = FL_ITEM;
	self.solid = SOLID_TRIGGER;
	self.movetype = MOVETYPE_TOSS;
	self.velocity = '0 0 0';
	self.origin_z = self.origin_z + 6;
	droptofloor ();
	self.movetype = MOVETYPE_NONE;
	setorigin (self, self.origin + '0 0 28');
	self.tw_spawn_org = self.origin;
	self.think = TW_ItemThink;
	self.nextthink = time + 0.05;
};

void() item_powerup_triple_wheeled =
{
	TW_Precache ();
	self.classname = "item_powerup_triple_wheeled";
	self.touch = TW_ItemTouch;
	setmodel (self, "progs/triple_wheeled.md3");
	self.mdl = self.model;
	self.traileffectnum = particleeffectnum ("quad");
	self.effects = self.effects | EF_DIMLIGHT | EF_FULLBRIGHT;
	self.netname = "Dual Wield";
	setsize (self, '-18 -18 -24', '18 18 32');
	BM_Radar_RegisterPowerup (self, BM_RPU_TRIPLE);
	self.think = TW_ItemDrop;
	self.nextthink = time + 0.15;
};

// Spawn helper for maps that don't yet place item_powerup_triple_wheeled
void(vector org) TW_SpawnAt =
{
	local entity e, oldself;

	e = spawn ();
	e.origin = org;
	e.angles = '0 0 0';
	oldself = self;
	self = e;
	item_powerup_triple_wheeled ();
	self = oldself;
};

void() TW_MapSpawn =
{
	local entity spot, pick1, pick2;
	local float cnt, idx;

	if (tw_map_spawned)
		return;
	tw_map_spawned = TRUE;

	if (!autocvar_bm_triple_spawn || BM_IsMenuBg ())
		return;
	if (find (world, classname, "item_powerup_triple_wheeled") != world)
		return;

	if (mapname == "bakersfielddowntown" || world.model == "maps/bakersfielddowntown.bsp")
	{
		// Sandrini's Public House (ground + basement rooms)
		TW_SpawnAt ('-3990 428 48');
		TW_SpawnAt ('-3640 460 48');
		TW_SpawnAt ('-3640 180 48');
		TW_SpawnAt ('-3880 180 -80');
		TW_SpawnAt ('-3851 545 -80');
		TW_SpawnAt ('-3525 308 -80');
		TW_SpawnAt ('-3240 270 -80');
		TW_SpawnAt ('-3240 500 -80');

		// Dagny's Coffee + Upstairs LAN Loft + Room 13
		TW_SpawnAt ('-5900 2576 48');
		TW_SpawnAt ('-5500 2660 210');
		TW_SpawnAt ('-6050 2760 210');

		// Historic Fox Theater (auditorium, stage, mezzanine)
		TW_SpawnAt ('-9980 3390 88');
		TW_SpawnAt ('-10092 3996 88');
		TW_SpawnAt ('-10152 2724 290');

		// Padre Hotel (lobby, mid suite, rooftop)
		TW_SpawnAt ('-9528 -5424 48');
		TW_SpawnAt ('-9800 -5504 550');
		TW_SpawnAt ('-9492 -5160 1270');

		// Nile Theater, Jerry's Pizza, Guthrie's Alley Cat, Parking Garage
		TW_SpawnAt ('-11078 -2572 48');
		TW_SpawnAt ('-10994 -3024 200');
		TW_SpawnAt ('-1080 -4032 48');
		TW_SpawnAt ('-3224 -4756 48');
		TW_SpawnAt ('-7172 -5551 430');

		// Far edges & outer corners of the map
		TW_SpawnAt ('-12740 5936 48');
		TW_SpawnAt ('-12982 -6634 48');
		TW_SpawnAt ('84 5910 48');
		TW_SpawnAt ('672 -6348 48');
		TW_SpawnAt ('-13220 -1500 48');
		TW_SpawnAt ('600 1960 48');
		TW_SpawnAt ('-8300 6200 48');
		TW_SpawnAt ('-5424 -6700 48');
		return;
	}
	if (mapname == "bakersfieldish" || world.model == "maps/bakersfieldish.bsp")
	{
		// Sandrini's Public House (ground + basement rooms)
		TW_SpawnAt ('-3990 428 48');
		TW_SpawnAt ('-3640 460 48');
		TW_SpawnAt ('-3640 180 48');
		TW_SpawnAt ('-3880 180 -80');
		TW_SpawnAt ('-3851 545 -80');
		TW_SpawnAt ('-3525 308 -80');
		TW_SpawnAt ('-3240 270 -80');
		TW_SpawnAt ('-3240 500 -80');

		// Golden West Casino (poker pit, blackjack rotunda, buddha alcove)
		TW_SpawnAt ('-2920 4236 48');
		TW_SpawnAt ('-2100 4176 48');
		TW_SpawnAt ('-2540 3550 48');

		// The Great Castle (dining hall, kitchen/BOH, watchtower)
		TW_SpawnAt ('-5840 460 48');
		TW_SpawnAt ('-6228 480 48');
		TW_SpawnAt ('-5868 396 200');

		// Larry's Warehouse & Unit 130A B-LAN (warehouse hall, bedroom, B-LAN hall)
		TW_SpawnAt ('-7380 4400 48');
		TW_SpawnAt ('-7600 3600 48');
		TW_SpawnAt ('-5820 5100 48');

		// Dagny's Coffee + Upstairs LAN Loft + Room 13
		TW_SpawnAt ('-5900 2576 48');
		TW_SpawnAt ('-5500 2660 210');
		TW_SpawnAt ('-6050 2760 210');

		// Fox, Padre, Nile, Jerry's, Guthrie's, Parking Garage
		TW_SpawnAt ('-9920 3450 64');
		TW_SpawnAt ('-9528 -5424 48');
		TW_SpawnAt ('-10994 -3024 200');
		TW_SpawnAt ('-1080 -4032 48');
		TW_SpawnAt ('-3224 -4756 48');
		TW_SpawnAt ('-6998 -5561 690');

		// Far edges & outer corners of the map
		TW_SpawnAt ('-12836 5812 48');
		TW_SpawnAt ('-12980 -6420 48');
		TW_SpawnAt ('-200 5880 48');
		TW_SpawnAt ('-220 -6360 48');
		TW_SpawnAt ('-13220 -1500 48');
		TW_SpawnAt ('-396 1884 48');
		TW_SpawnAt ('-8732 5800 48');
		TW_SpawnAt ('-6600 -6420 48');
		return;
	}
	if (mapname == "spruce" || world.model == "maps/spruce.bsp")
	{
		TW_SpawnAt ('-1224 -2920 56');
		TW_SpawnAt ('1104 -340 56');
		TW_SpawnAt ('1944 500 56');
		TW_SpawnAt ('-6750 -120 56');
		return;
	}
	if (mapname == "soi6" || world.model == "maps/soi6.bsp")
	{
		TW_SpawnAt ('-200 472 60');
		TW_SpawnAt ('1780 0 56');
		TW_SpawnAt ('6063 200 60');
		TW_SpawnAt ('10236 1750 56');
		return;
	}
	if (mapname == "bklan6" || world.model == "maps/bklan6.bsp")
	{
		TW_SpawnAt ('11580 -2736 56');
		TW_SpawnAt ('-4200 -10380 56');
		TW_SpawnAt ('5304 -15228 58');
		TW_SpawnAt ('564 -571 56');
		return;
	}
	if (mapname == "soicowboy_bkk" || world.model == "maps/soicowboy_bkk.bsp")
	{
		TW_SpawnAt ('118 -1141 56');
		TW_SpawnAt ('4252 -1417 56');
		TW_SpawnAt ('7716 -1417 56');
		TW_SpawnAt ('10098 -1417 60');
		return;
	}
	if (mapname == "morrorock" || world.model == "maps/morrorock.bsp")
	{
		TW_SpawnAt ('-1102 3020 140');
		TW_SpawnAt ('-787 -8300 140');
		TW_SpawnAt ('-3600 3980 130');
		TW_SpawnAt ('-5500 -11480 130');
		return;
	}
	if (!deathmatch)
		return;

	cnt = 0;
	spot = find (world, classname, "info_player_deathmatch");
	while (spot)
	{
		cnt = cnt + 1;
		spot = find (spot, classname, "info_player_deathmatch");
	}
	if (cnt < 1)
		return;

	pick1 = world;
	pick2 = world;
	idx = 0;
	spot = find (world, classname, "info_player_deathmatch");
	while (spot)
	{
		if (idx == 0)
			pick1 = spot;
		if (idx == floor (cnt * 0.5) && spot != pick1)
			pick2 = spot;
		idx = idx + 1;
		spot = find (spot, classname, "info_player_deathmatch");
	}
	if (pick1)
	{
		makevectors (pick1.angles);
		traceline (pick1.origin + '0 0 16', pick1.origin + '0 0 16' + v_forward * 96, TRUE, pick1);
		TW_SpawnAt (trace_endpos);
	}
	if (pick2 && vlen (pick2.origin - pick1.origin) > 400)
	{
		makevectors (pick2.angles);
		traceline (pick2.origin + '0 0 16', pick2.origin + '0 0 16' + v_forward * 96, TRUE, pick2);
		TW_SpawnAt (trace_endpos);
	}
};

void() TW_Impulse =
{
	local vector fwd;

	if (!autocvar_sv_cheats)
		return;
	if (self.impulse == 158)
	{
		self.impulse = 0;
		makevectors ('0 1 0' * self.v_angle_y);
		fwd = v_forward;
		traceline (self.origin + '0 0 16', self.origin + '0 0 16' + fwd * 120, TRUE, self);
		TW_SpawnAt (trace_endpos - fwd * 16);
		sprint (self, "Spawned Dual Wield!\n");
		return;
	}
	if (self.impulse == 159)
	{
		self.impulse = 0;
		TW_Activate (self, FALSE);
		return;
	}
	if (self.impulse == 160)
	{
		self.impulse = 0;
		TW_Activate (self, TRUE);
		return;
	}
};
