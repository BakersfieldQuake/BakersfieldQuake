#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
MAGAZINES AND RELOADING (Bakersfield LAN rules, Combat+ only)

Ammo never runs out, but every gun has a magazine:
	- empty magazine: the gun reloads by itself (no switching away)
	- R (impulse 41) reloads early
	- stop firing for bm_idle_reload seconds and a part-empty gun quietly tops itself up
	- only the gun in your hand reloads at full speed; holstered guns refill at bm_holster of that speed,
	  so swapping guns can't keep the rockets coming
	- firing with rounds left cancels a reload, switching guns drops it
	- any ammo or weapon pickup refills every magazine

The stock fire code still spends ammo_shells/nails/rockets/cells. Those four fields hold the HELD gun's
magazine (and, for the other ammo types, a representative gun's magazine so the HUD shows something
sensible). BM_Frame reads back what the fire code spent; BM_SwapIn saves and loads magazines on a
weapon change (it runs at the top of W_SetCurrentAmmo, which every weapon change goes through).
The Mega Man and fun guns keep their own ammo fields (mm_ammo, fg_ammoN) as their magazines; their
own always-on recharge is switched off while bm_reload is on (megaman.qc / funguns.qc).
================
*/

// ---------------------------------------------------------------- the table
float(float s) BM_IsFirearmSlot =
{
	return (s == BM_FG7 || s == BM_FG9);
};

// magazine size in ammo units
float(float s) BM_MagSize =
{
	local float n;

	if (s <= BM_MM)
	{
		if (s == BM_SG)			n = 8;
		else if (s == BM_SSG)	n = 8;		// DN3DooM Pump Shotgun: 8-shell tube magazine (1 shell a shot)
		else if (s == BM_NG)	n = 5;		// the Laptop Gun (took the nailgun slot): 5-packet mag for DDoS flood salvos
		else if (s == BM_SNG)	n = 2;		// the Milky Gun: two ladies
		else if (s == BM_GL)	n = 6;		// KTX Clan Arena: 6 grenades
		else if (s == BM_RL)	n = 5;
		else if (s == BM_LG)	n = 36;
		else if (s == BM_LASER)	n = 24;
		else if (s == BM_MM)	return MM_MAX_AMMO;
		else return 0;
		if (autocvar_bm_mag_scale != 1)
		{
			n = ceil (n * autocvar_bm_mag_scale);
			if (n < 1)
				n = 1;
		}
		return n;
	}
	if (s == BM_FG1)	return FunGun_Max (FG_DOB);
	if (s == BM_FG2)	return FunGun_Max (FG_PONG);
	if (s == BM_FG3)	return FunGun_Max (FG_PICKLE);
	if (s == BM_FG4)	return FunGun_Max (FG_NETSEND);
	if (s == BM_FG5)	return FunGun_Max (FG_DOOKIE);
	if (s == BM_FG6)	return FunGun_Max (FG_WCANNON);
	if (s == BM_FG7)	return FunGun_Max (FG_M4);
	if (s == BM_FG8)	return FunGun_Max (FG_KYLE);
	if (s == BM_FG9)	return FunGun_Max (FG_GARAND);
	if (s == BM_FG10)	return FunGun_Max (FG_CYRAX);
	return 0;
};

// seconds to reload a completely empty magazine while holding the gun
float(float s) BM_ReloadTime =
{
	local float t;

	if (s == BM_SG)			t = 1.2;
	else if (s == BM_SSG)	t = 1.26;	// DN3DooM Pump Shotgun full tube reload
	else if (s == BM_NG)	t = 2.5;	// Laptop Gun
	else if (s == BM_SNG)	t = 5;		// Milky Gun
	else if (s == BM_GL)	t = 2.2;
	else if (s == BM_RL)	t = 2.4;
	else if (s == BM_LG)	t = 2.4;
	else if (s == BM_LASER)	t = 2.2;
	else if (s == BM_MM)	t = 9;		// 4.5 s a Mega Man (was 12: 6 s)
	else if (s == BM_FG1)	t = FG_DOB_REGEN;	// Rob Dob: one head (12 s)
	else if (s == BM_FG2)	t = FG_PONG_REGEN;	// Jar o' Green Guys: one jar
	else if (s == BM_FG3)	t = 8;		// Pickle Surprise: 8 s for full magazine of 3
	else if (s == BM_FG4)	t = FG_NETSEND_REGEN;		// NetSend: one LOL.BAT (5 s)
	else if (s == BM_FG5)	t = FG_DOOKIE_REGEN;		// Dookie Bazooka: 3 s full reload (5 canisters)
	else if (s == BM_FG7)	t = M4_RELOAD_TIME;		// the M4: the whole CS reload animation
	else if (s == BM_FG8)	t = FG_KYLE_REGEN;		// The Pocket Kyle: 5 s recharge
	else if (s == BM_FG9)	t = GAR_RELOAD_TIME;	// the M1 Garand: the whole DoD reload animation
	else if (s == BM_FG10)	t = FG_CYRAX_REGEN;		// Cyrax Net: 10 s recharge
	else if (s == BM_FG6)	t = FG_WCANNON_REGEN;		// Wheelman Cannon: 12 s for the next Wheelman
	else
		t = 2;
	if (s >= BM_FG1 && !BM_IsFirearmSlot (s))
		t = t * Underdog_AmmoRate (self);	// underdogs reload joke fun guns faster (firearms keep fixed animation timing)
	return t * autocvar_bm_reload_scale;
};

// ammo units one shot uses (for the HUD round count and the "can I fire" test)
float(float s) BM_PerShot =
{
	return 1;
};

// 1 shells, 2 nails, 3 rockets, 4 cells, 0 its own field
float(float s) BM_AmmoType =
{
	if (s == BM_SG || s == BM_SSG)
		return 1;
	if (s == BM_NG || s == BM_SNG)
		return 2;
	if (s == BM_GL || s == BM_RL)
		return 3;
	if (s == BM_LG || s == BM_LASER)
		return 4;
	return 0;
};

float(entity p) BM_SlotOf =
{
	local float w;

	w = p.weapon;
	if (w == IT_SHOTGUN)			return BM_SG;
	if (w == IT_SUPER_SHOTGUN)		return BM_SSG;
	if (w == IT_NAILGUN)			return BM_NG;
	if (w == IT_SUPER_NAILGUN)		return BM_SNG;
	if (w == IT_GRENADE_LAUNCHER)	return BM_GL;
	if (w == IT_ROCKET_LAUNCHER)	return BM_RL;
	if (w == IT_LIGHTNING)			return BM_LG;
	if (w == IT_LASER_CANNON)		return BM_LASER;
	if (w == IT_MEGAMAN)			return BM_MM;
	if (w == IT_FUNGUN)
	{
		if (p.fg_sel == FG_DOB)
			return BM_FG1;
		if (p.fg_sel == FG_PONG)
			return BM_FG2;
		if (p.fg_sel == FG_NETSEND)
			return BM_FG4;
		if (p.fg_sel == FG_DOOKIE)
			return BM_FG5;
		if (p.fg_sel == FG_WCANNON)
			return BM_FG6;
		if (p.fg_sel == FG_M4)
			return BM_FG7;
		if (p.fg_sel == FG_KYLE)
			return BM_FG8;
		if (p.fg_sel == FG_GARAND)
			return BM_FG9;
		if (p.fg_sel == FG_CYRAX)
			return BM_FG10;
		return BM_FG3;
	}
	return 0;
};

float() BM_CurSlot =
{
	if (!autocvar_bm_reload)
		return 0;
	return BM_SlotOf (self);
};

// ---------------------------------------------------------------- magazine storage
float(entity p, float s) BM_GetMag =
{
	if (s <= BM_MM)
	{
		if (s == BM_SG)		return p.bm_m1;
		if (s == BM_SSG)	return p.bm_m2;
		if (s == BM_NG)		return p.bm_m3;
		if (s == BM_SNG)	return p.bm_m4;
		if (s == BM_GL)		return p.bm_m5;
		if (s == BM_RL)		return p.bm_m6;
		if (s == BM_LG)		return p.bm_m7;
		if (s == BM_LASER)	return p.bm_m8;
		if (s == BM_MM)		return p.mm_ammo;
		return 0;
	}
	if (s == BM_FG1)	return p.fg_ammo1;
	if (s == BM_FG2)	return p.fg_ammo2;
	if (s == BM_FG3)	return p.fg_ammo3;
	if (s == BM_FG4)	return p.fg_ammo4;
	if (s == BM_FG5)	return p.fg_ammo5;
	if (s == BM_FG6)	return p.fg_ammo6;
	if (s == BM_FG7)	return p.fg_ammo7;
	if (s == BM_FG8)	return p.fg_ammo8;
	if (s == BM_FG9)	return p.fg_ammo9;
	if (s == BM_FG10)	return p.fg_ammo10;
	return 0;
};

void(entity p, float s, float v) BM_SetMag =
{
	if (s <= BM_MM)
	{
		if (s == BM_SG)			p.bm_m1 = v;
		else if (s == BM_SSG)	p.bm_m2 = v;
		else if (s == BM_NG)	p.bm_m3 = v;
		else if (s == BM_SNG)	p.bm_m4 = v;
		else if (s == BM_GL)	p.bm_m5 = v;
		else if (s == BM_RL)	p.bm_m6 = v;
		else if (s == BM_LG)	p.bm_m7 = v;
		else if (s == BM_LASER)	p.bm_m8 = v;
		else if (s == BM_MM)	p.mm_ammo = v;
		return;
	}
	if (s == BM_FG1)		p.fg_ammo1 = v;
	else if (s == BM_FG2)	p.fg_ammo2 = v;
	else if (s == BM_FG3)	p.fg_ammo3 = v;
	else if (s == BM_FG4)	p.fg_ammo4 = v;
	else if (s == BM_FG5)	p.fg_ammo5 = v;
	else if (s == BM_FG6)	p.fg_ammo6 = v;
	else if (s == BM_FG7)	p.fg_ammo7 = v;
	else if (s == BM_FG8)	p.fg_ammo8 = v;
	else if (s == BM_FG9)	p.fg_ammo9 = v;
	else if (s == BM_FG10)	p.fg_ammo10 = v;
};

float(entity p, float s) BM_GetAcc =
{
	if (s <= 9)
	{
		if (s == 1)		return p.bm_a1;
		if (s == 2)		return p.bm_a2;
		if (s == 3)		return p.bm_a3;
		if (s == 4)		return p.bm_a4;
		if (s == 5)		return p.bm_a5;
		if (s == 6)		return p.bm_a6;
		if (s == 7)		return p.bm_a7;
		if (s == 8)		return p.bm_a8;
		return p.bm_a9;
	}
	if (s == 10)	return p.bm_a10;
	if (s == 11)	return p.bm_a11;
	if (s == 12)	return p.bm_a12;
	if (s == 13)	return p.bm_a13;
	if (s == 14)	return p.bm_a14;
	if (s == 15)	return p.bm_a15;
	if (s == 16)	return p.bm_a16;
	if (s == 17)	return p.bm_a17;
	if (s == 18)	return p.bm_a18;
	return p.bm_a19;
};

void(entity p, float s, float v) BM_SetAcc =
{
	if (s <= 9)
	{
		if (s == 1)			p.bm_a1 = v;
		else if (s == 2)	p.bm_a2 = v;
		else if (s == 3)	p.bm_a3 = v;
		else if (s == 4)	p.bm_a4 = v;
		else if (s == 5)	p.bm_a5 = v;
		else if (s == 6)	p.bm_a6 = v;
		else if (s == 7)	p.bm_a7 = v;
		else if (s == 8)	p.bm_a8 = v;
		else				p.bm_a9 = v;
		return;
	}
	if (s == 10)		p.bm_a10 = v;
	else if (s == 11)	p.bm_a11 = v;
	else if (s == 12)	p.bm_a12 = v;
	else if (s == 13)	p.bm_a13 = v;
	else if (s == 14)	p.bm_a14 = v;
	else if (s == 15)	p.bm_a15 = v;
	else if (s == 16)	p.bm_a16 = v;
	else if (s == 17)	p.bm_a17 = v;
	else if (s == 18)	p.bm_a18 = v;
	else				p.bm_a19 = v;
};

float(float t) BM_GetField =
{
	if (t == 1)		return self.ammo_shells;
	if (t == 2)		return self.ammo_nails;
	if (t == 3)		return self.ammo_rockets;
	return self.ammo_cells;
};

float(float t) BM_GetShown =
{
	if (t == 1)		return self.bm_shown_s;
	if (t == 2)		return self.bm_shown_n;
	if (t == 3)		return self.bm_shown_r;
	return self.bm_shown_c;
};

void(float t, float v) BM_SetField =
{
	if (t == 1)			{ self.ammo_shells = v;		self.bm_shown_s = v; }
	else if (t == 2)	{ self.ammo_nails = v;		self.bm_shown_n = v; }
	else if (t == 3)	{ self.ammo_rockets = v;	self.bm_shown_r = v; }
	else				{ self.ammo_cells = v;		self.bm_shown_c = v; }
};

// ---------------------------------------------------------------- core
void() BM_FillAll =
{
	local float s;

	s = 1;
	while (s <= BM_SLOTS)
	{
		BM_SetMag (self, s, BM_MagSize (s));
		BM_SetAcc (self, s, 0);
		s = s + 1;
	}
	self.bm_ssgburst = 16;
	self.bm_rl_slot = 0;
	self.bm_rl_quiet = FALSE;
};

// regular ammo box / weapon pickup: refill combat guns & M4/Garand without instant-resetting joke superweapons (FG1..FG6)
void() BM_FillCombatOnly =
{
	local float s;

	s = 1;
	while (s <= BM_SLOTS)
	{
		if (s <= BM_MM || BM_IsFirearmSlot (s))
		{
			BM_SetMag (self, s, BM_MagSize (s));
			BM_SetAcc (self, s, 0);
		}
		s = s + 1;
	}
	self.bm_ssgburst = 16;
	if (self.bm_rl_slot <= BM_MM || BM_IsFirearmSlot (self.bm_rl_slot))
	{
		self.bm_rl_slot = 0;
		self.bm_rl_quiet = FALSE;
	}
};

// write the magazines into the four ammo fields (held gun's type gets the held gun's magazine)
void() BM_WriteFields =
{
	local float s, t, m, v;

	s = self.bm_slot;
	t = BM_AmmoType (s);
	if (s)
		m = BM_GetMag (self, s);
	else
		m = 0;
	if (t == 1) v = m; else v = self.bm_m2;
	self.ammo_shells = v;
	self.bm_shown_s = v;
	if (t == 2) v = m; else v = self.bm_m4;
	self.ammo_nails = v;
	self.bm_shown_n = v;
	if (t == 3) v = m; else v = self.bm_m6;
	self.ammo_rockets = v;
	self.bm_shown_r = v;
	if (t == 4) v = m; else v = self.bm_m7;
	self.ammo_cells = v;
	self.bm_shown_c = v;
	if (s)
		self.currentammo = m;
};

// read back what the fire code spent, and spot pickups (an ammo field went UP)
void() BM_ReadFields =
{
	local float s, t, f;

	s = self.bm_slot;
	t = BM_AmmoType (s);
	if (self.ammo_shells > self.bm_shown_s + 0.01 || self.ammo_nails > self.bm_shown_n + 0.01 || self.ammo_rockets > self.bm_shown_r + 0.01 || self.ammo_cells > self.bm_shown_c + 0.01)
	{
		if (self.bm_full_refill)
		{
			self.bm_full_refill = FALSE;
			BM_FillAll ();
		}
		else
			BM_FillCombatOnly ();
		return;
	}
	if (!t)
		return;
	if (t == 1)
	{
		f = self.ammo_shells;
		if (f >= self.bm_shown_s - 0.001) return;
	}
	else if (t == 2)
	{
		f = self.ammo_nails;
		if (f >= self.bm_shown_n - 0.001) return;
	}
	else if (t == 3)
	{
		f = self.ammo_rockets;
		if (f >= self.bm_shown_r - 0.001) return;
	}
	else
	{
		f = self.ammo_cells;
		if (f >= self.bm_shown_c - 0.001) return;
	}
	if (f < 0)
		f = 0;
	BM_SetMag (self, s, f);
	self.bm_lastshot = time;
};

void() BM_SwapIn =
{
	local float s;

	if (!autocvar_bm_reload || self.classname != "player")
		return;
	s = BM_SlotOf (self);
	if (s == self.bm_slot)
	{
		BM_ReadFields ();
		BM_WriteFields ();
		return;
	}
	BM_ReadFields ();				// bank whatever the old gun spent
	self.bm_rl_slot = 0;			// switching drops a reload
	self.bm_rl_quiet = FALSE;
	self.bm_slot = s;
	self.bm_lastshot = time;		// no instant idle top-up on the draw
	BM_WriteFields ();
};

void(float s) BM_StartReload =
{
	local float size, mag;

	if (!s || self.bm_rl_slot == s)
		return;
	size = BM_MagSize (s);
	mag = BM_GetMag (self, s);
	if (mag >= size)
	{
		self.bm_rl_quiet = FALSE;
		return;
	}
	if (s == BM_SSG)
	{
		DN3SG_StartReload ();
		return;
	}
	self.bm_rl_slot = s;
	self.bm_rl_start = time;
	self.bm_rl_end = time + max (0.4, BM_ReloadTime (s) * (size - mag) / size);
	if (BM_IsFirearmSlot (s))
	{
		self.bm_rl_quiet = FALSE;
		self.bm_rl_end = time + BM_ReloadTime (s);		// M4 / Garand always play their full reload animation & sounds
	}
	else if (!self.bm_rl_quiet)
		sound7 (self, CHAN_ITEM, "weapons/lock4.wav", 0.6, ATTN_NORM, SNDSPD);
};

// replaces "switch to the best weapon" when a gun runs dry mid-burst (nailgun, LG, ...)
void() BM_OutOfAmmo =
{
	local float s;

	s = BM_CurSlot ();
	if (!s)
	{
		self.weapon = W_BestWeapon ();
		W_SetCurrentAmmo ();
		return;
	}
	BM_ReadFields ();
	self.bm_rl_quiet = FALSE;
	BM_StartReload (s);
	player_run ();
	self.weaponframe = 0;
};

// W_CheckNoAmmo: TRUE = the gun can fire
float() BM_CheckNoAmmo =
{
	local float s;

	s = BM_CurSlot ();
	if (s >= BM_MM)
		return TRUE;		// the Mega Man and fun guns click when empty on their own
	if (BM_GetMag (self, s) >= BM_PerShot (s))
		return TRUE;
	self.bm_rl_quiet = FALSE;
	BM_StartReload (s);
	return FALSE;
};

// PutClientInServer, before W_SetCurrentAmmo: every life starts with full magazines
void() BM_Spawn =
{
	self.bm_full_refill = FALSE;
	if (!autocvar_bm_reload)
		return;
	BM_FillAll ();
	self.bm_slot = 0;
	self.bm_shown_s = 0;
	self.bm_shown_n = 0;
	self.bm_shown_r = 0;
	self.bm_shown_c = 0;
	self.bm_lastframe = time;
	self.bm_lastshot = time;
	self.bm_vm_hidden = 0;
	if (self.grenade_ammo > 2)
		self.grenade_ammo = 2;		// prox grenades used to pile up one per spawn, forever
};

// the gun is put away while it reloads, and comes back when the magazine is full (or the reload is dropped)
void() BM_ViewModel =
{
	local string old;

	if (self.bm_rl_slot && !self.bm_rl_quiet && self.health > 0 && !(M4_ShowsReload (self) || Garand_ShowsReload (self)))
	{
		if (!self.bm_vm_hidden && self.weaponmodel != "")
		{
			old = self.bm_vm_str;
			self.bm_vm_str = strzone (self.weaponmodel);
			self.weaponmodel = "";
			if (old)
				strunzone (old);		// only after weaponmodel no longer points into it
			self.bm_vm_hidden = self.bm_rl_slot;
		}
		return;
	}
	if (self.bm_vm_hidden)
	{
		// still empty = nobody switched guns meanwhile (a switch sets the new gun's own model)
		// and the same gun is still in the hand: some guns (the banana, the fallback) set "" on purpose
		if (self.weaponmodel == "" && self.bm_vm_str && BM_SlotOf (self) == self.bm_vm_hidden)
			self.weaponmodel = self.bm_vm_str;
		self.bm_vm_hidden = 0;
	}
};

// every frame, top of W_WeaponFrame (alive players and bots)
void() BM_Frame =
{
	local float s, i, size, mag, dt, acc, rate, prev;

	if (!autocvar_bm_reload)
	{
		self.bm_st_reload = 0;
		self.bm_st_magmax = 0;
		self.bm_st_slot = BM_SlotOf (self);
		return;
	}
	dt = time - self.bm_lastframe;
	self.bm_lastframe = time;
	if (dt > 0.25)
		dt = 0.25;
	if (dt < 0)
		dt = 0;

	s = BM_SlotOf (self);
	if (s != self.bm_slot)
		BM_SwapIn ();
	else
	{
		prev = BM_GetMag (self, s);
		BM_ReadFields ();
		if (BM_AmmoType (s) == 0 && BM_GetMag (self, s) < prev)
			self.bm_lastshot = time;			// a Mega Man or fun gun went
	}

	// R: reload now (impulses wait for attack_finished, this one doesn't)
	// Only consume BM_RELOAD_IMPULSE when the held weapon has a magazine slot (s != 0),
	// so melee/non-magazine weapons like Bonk Hammer (IT_AXE) still receive R to spin!
	if (self.impulse == BM_RELOAD_IMPULSE && s)
	{
		self.impulse = 0;
		self.bm_rl_quiet = FALSE;
		BM_StartReload (s);
	}

	if (s)
	{
		size = BM_MagSize (s);
		mag = BM_GetMag (self, s);
		if (self.bm_rl_slot == s)
		{
			if (s == BM_SSG && self.dn3_sg_rl_phase > 0)
			{
				// DN3SG_Frame drives shell-by-shell tilt reload and +attack cancellation
			}
			else if (time >= self.bm_rl_end)
			{
				BM_SetMag (self, s, size);
				BM_SetAcc (self, s, 0);
				if (s == BM_SSG)
					self.bm_ssgburst = 16;
				self.bm_rl_slot = 0;
				if (!BM_IsFirearmSlot (s) && !self.bm_rl_quiet)
					sound7 (self, CHAN_ITEM, "weapons/pkup.wav", 0.35, ATTN_NORM, SNDSPD);
				self.bm_rl_quiet = FALSE;
				if (s == BM_MM)
					self.mm_fire_t = time - 0.5;	// the Mega Man pops back up into the hand
				if (s == BM_FG2)
					self.gj_reload_t = time;		// fresh Jar o' Green Guys whips up from the belt
				if (s == BM_FG3)
					self.pk_reload_t = time;		// fresh Pickle Surprise whips up into the hand
				if (s == BM_FG5)
					self.dk_reload_t = time;		// fresh Dookie Bazooka canister raises up
				if (s == BM_FG1)
					self.rh_reload_t = time;		// fresh Rob Head drone remote raises up
				if (s == BM_FG8)
					self.ky_draw_t = time;			// fresh Pocket Kyle pops up into the hand
				if (s == BM_FG10)
					self.cy_draw_t = time;			// fresh Cyrax Net Launcher raises up
			}
			else if (self.button0 && mag >= BM_PerShot (s) && (self.bm_rl_quiet || time > self.bm_rl_start + 0.15) && !BM_IsFirearmSlot (s))
			{
				self.bm_rl_slot = 0;				// fire what's left instead
				self.bm_rl_quiet = FALSE;
			}
		}
		else if (s == BM_SSG && self.dn3_sg_fire_t > 0 && time < self.dn3_sg_fire_t + DN3SG_REFIRE)
		{
			// let the DN3DooM Pump Shotgun finish its fire + pump cycle before auto-reloading
		}
		else if (s == BM_NG && self.ltg_phase > 0)
		{
			// let the Laptop Gun finish queuing/unleashing its DDoS salvo before starting reload
		}
		else if (s == BM_FG2 && (self.gj_shaking > 0 || self.gj_throw_at > 0 || (self.gj_threw_t > 0 && time < self.gj_threw_t + GJ_FOLLOW_TIME)))
		{
			// let the Jar o' Green Guys cocktail-shake, whip-throw & open-claw follow-through finish before starting reload
		}
		else if (s == BM_FG3 && (self.pk_throw_at > 0 || (self.pk_threw_t > 0 && time < self.pk_threw_t + PK_FOLLOW_TIME)))
		{
			// let the Pickle Surprise throw & open-gauntlet follow-through finish before starting reload
		}
		else if (s == BM_FG5 && (self.dk_charging > 0 || (self.dk_fire_t > 0 && time < self.dk_fire_t + DK_FOLLOW_TIME)))
		{
			// let the Dookie Bazooka windup & blast recoil finish before starting reload
		}
		else if (s == BM_FG6 && self.fg_fire_t > 0 && time < self.fg_fire_t + WC_COOLDOWN)
		{
			// let the WEW Cannon blast, long-stroke barrel recoil & breech cycle finish before starting reload
		}
		else if (s == BM_FG9 && self.gar_empty_t > 0 && time < self.gar_empty_t + GAR_SHOOT_EMPTY_TIME)
		{
			// let the M1 Garand 8th-round en-bloc clip ejection + PING finish before starting reload
		}
		else if (s == BM_FG1 && (self.rh_charging > 0 || self.rh_throw_at > 0 || (self.rh_threw_t > 0 && time < self.rh_threw_t + (RH_FOLLOW_TIME / RH_DRONE_ANIM_SPEED))))
		{
			// let the Rob Head windup, throw/launch & follow-through finish before starting reload
		}
		else if (s == BM_FG8 && (self.ky_locking > 0 || self.ky_throw_at > 0 || (self.ky_fire_t > 0 && time < self.ky_fire_t + KY_THROW_DELAY + KY_FOLLOW_TIME)))
		{
			// let The Pocket Kyle lock-on, throw & open-palm follow-through finish before starting reload
		}
		else if (s == BM_FG4 && (self.ns_throw_at > 0 || (self.ns_fire_t > 0 && time < self.ns_fire_t + NDVM_THROW_COUNT / NDVM_THROW_FPS + NDVM_DROP)))
		{
			// let the NetSend throw, the release & the empty hand dropping away finish before starting reload (netsend.qc)
		}
		else if (s == BM_FG10 && (self.cy_charging > 0 || (self.cy_fire_t > 0 && time < self.cy_fire_t + CY_FIRE_ANIM_TIME) || (self.cy_vent_t > 0 && time < self.cy_vent_t + CY_VENT_ANIM_TIME)))
		{
			// let Cyrax Net charge, fire recoil & vent finish before starting reload (cyrax.qc)
		}
		else if (mag < BM_PerShot (s))
		{
			self.bm_rl_quiet = FALSE;
			BM_StartReload (s);
		}
		else if (!BM_IsFirearmSlot (s) && mag < size && !self.button0 && time > self.bm_lastshot + autocvar_bm_idle_reload)
		{
			self.bm_rl_quiet = TRUE;
			BM_StartReload (s);
		}
	}

	// holstered guns trickle back. 10 times a second with the time gathered meanwhile: 17 slots of if-chains for every
	// player on every frame was the costliest thing here, mostly for magazines that were already full
	self.bm_holster_dt = self.bm_holster_dt + dt;
	if (self.bm_holster_dt >= 0.1)
	{
		dt = self.bm_holster_dt;
		self.bm_holster_dt = 0;
		i = 1;
	}
	else
		i = BM_SLOTS + 1;
	while (i <= BM_SLOTS)
	{
		if (i != s)
		{
			size = BM_MagSize (i);
			mag = BM_GetMag (self, i);
			if (mag < size)
			{
				rate = size / BM_ReloadTime (i) * autocvar_bm_holster;
				if (i == BM_MM || (i >= BM_FG1 && i <= BM_FG6) || i == BM_FG8 || i == BM_FG10)
					rate = size / BM_ReloadTime (i);		// Mega Man & recharging fun-gun cooldowns (incl. Pocket Kyle & Cyrax) tick at 1.0x speed in pocket
				acc = BM_GetAcc (self, i) + rate * dt;
				if (acc >= 1)
				{
					mag = min (size, mag + floor (acc));
					acc = acc - floor (acc);
					BM_SetMag (self, i, mag);
				}
				BM_SetAcc (self, i, acc);
			}
			else
				BM_SetAcc (self, i, 0);
		}
		i = i + 1;
	}

	BM_WriteFields ();

	// HUD
	if (self.ishuman == 1)
	{
		self.bm_st_slot = s;
		if (s)
		{
			rate = BM_PerShot (s);
			self.bm_st_mag = floor (BM_GetMag (self, s) / rate + 0.001);
			self.bm_st_magmax = floor (BM_MagSize (s) / rate + 0.001);
		}
		else
			self.bm_st_magmax = 0;
		if (self.bm_rl_slot && !self.fd_head && !self.fd_fade)
			self.bm_st_reload = 1 + floor (99 * (time - self.bm_rl_start) / (self.bm_rl_end - self.bm_rl_start));
		else
			self.bm_st_reload = 0;
	}
	BM_ViewModel ();
};

// QC super shotgun burst state, per player
void() BM_FiredSSG =
{
	if (self.bm_ssgburst == 15)
	{
		self.attack_finished = (time + 0.95);
		self.bm_ssgburst = 16;
	}
	else
	{
		self.attack_finished = (time + 0.15);
		self.bm_ssgburst = 15;
	}
};
