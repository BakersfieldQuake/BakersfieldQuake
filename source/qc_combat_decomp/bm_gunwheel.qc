// ================================================================= Gun Wheel: what the HUD needs to know
// The wheel itself is client side (csqc/gunwheel.qc). Magazines and fun gun ammo live on the server, so each of the
// 18 slots is sent as one stat, in the wheel's order:
//   0 = not owned / not installed, 1 = owned but out of ammo and not selectable (bm_reload 0),
//   2 = usable, no counter, 10 + n = usable with n rounds (0 rounds reloads when drawn)
// Stat 151: 0 = the wheel may not open now, 1..18 = it may, holding that slot, 19 = it may, holding something else.

.float bm_gw0, bm_gw1, bm_gw2, bm_gw3, bm_gw4, bm_gw5, bm_gw6, bm_gw7, bm_gw8;
.float bm_gw9, bm_gw10, bm_gw11, bm_gw12, bm_gw13, bm_gw14, bm_gw15, bm_gw16, bm_gw17;
.float bm_gw_held;

// worldspawn, with the other clientstats
void() BM_WheelStatsInit =
{
	clientstat (133, 2, bm_gw0);
	clientstat (134, 2, bm_gw1);
	clientstat (135, 2, bm_gw2);
	clientstat (136, 2, bm_gw3);
	clientstat (137, 2, bm_gw4);
	clientstat (138, 2, bm_gw5);
	clientstat (139, 2, bm_gw6);
	clientstat (140, 2, bm_gw7);
	clientstat (141, 2, bm_gw8);
	clientstat (142, 2, bm_gw9);
	clientstat (143, 2, bm_gw10);
	clientstat (144, 2, bm_gw11);
	clientstat (145, 2, bm_gw12);
	clientstat (146, 2, bm_gw13);
	clientstat (147, 2, bm_gw14);
	clientstat (148, 2, bm_gw15);
	clientstat (149, 2, bm_gw16);
	clientstat (150, 2, bm_gw17);
	clientstat (151, 2, bm_gw_held);
};

// a stock gun (items bit): its magazine with bm_reload, else the shared pool (need = rounds one shot takes)
float(float owned, float slot, float pool, float need) BM_WheelGun =
{
	if (!(self.items & owned))
		return 0;
	if (autocvar_bm_reload)
		return 10 + floor (BM_GetMag (self, slot));
	if (pool < need)
		return 1;
	return 10 + floor (pool);
};

float(float g, float slot) BM_WheelFun =
{
	if (!FunGun_Available (g))
		return 0;
	if (autocvar_bm_reload && slot)
		return 10 + floor (BM_GetMag (self, slot));
	return 10 + floor (FunGun_Ammo (self, g));
};

float() BM_WheelHeld =
{
	local float w, g;

	w = self.weapon;
	if (w == IT_AXE)				return 1;
	if (w == IT_SUPER_SHOTGUN)		return 2;
	if (w == IT_SUPER_NAILGUN)		return 3;
	if (w == IT_GRENADE_LAUNCHER)	return 4;
	if (w == IT_ROCKET_LAUNCHER)	return 5;
	if (w == IT_LIGHTNING)			return 6;
	if (w == IT_LASER_CANNON)		return 7;
	if (w == IT_MEGAMAN)			return 8;
	if (w != IT_FUNGUN)				return 19;
	g = self.fg_sel;
	if (g == FG_M4)					return 9;
	if (g == FG_GARAND)				return 10;
	if (g == FG_DOB)				return 11;
	if (g == FG_PONG)				return 12;
	if (g == FG_PICKLE)				return 13;
	if (g == FG_NETSEND)			return 14;
	if (g == FG_DOOKIE)				return 15;
	if (g == FG_WCANNON)			return 16;
	if (g == FG_KYLE)				return 17;
	if (g == FG_CYRAX)				return 18;
	return 19;
};

// no switching while dead, watching, driving, flying, trapped, drinking or looking through the binoculars
float() BM_WheelAllowed =
{
	if (self.bm_obs || self.health <= 0 || self.deadflag || intermission_running)
		return FALSE;
	if (FD_Flying (self) || Veh_Driving (self) || JohnBird_Flying (self) || RocketRider_Flying (self))
		return FALSE;
	if (EricCannon_Active (self) || MMTank_Driving (self))
		return FALSE;
	if (self.cy_trapped_by != world || self.fl_st_mode > 0 || Binoc_On (self))
		return FALSE;
	return TRUE;
};

// every frame, for people only (PlayerPostThink)
void() BM_WheelFrame =
{
	if (self.ishuman != 1)
	{
		self.bm_gw_held = 0;	// observers (ishuman 3) and bots: stat 151 at 0 keeps the wheel shut for them
		return;
	}
	if (!BM_WheelAllowed ())
	{
		self.bm_gw_held = 0;
		return;
	}
	self.bm_gw_held = BM_WheelHeld ();

	if (self.items & IT_AXE)
		self.bm_gw0 = 2;
	else
		self.bm_gw0 = 0;
	self.bm_gw1 = BM_WheelGun (IT_SUPER_SHOTGUN, BM_SSG, self.ammo_shells, 1);
	self.bm_gw2 = BM_WheelGun (IT_SUPER_NAILGUN, BM_SNG, self.ammo_nails, 2);
	self.bm_gw3 = BM_WheelGun (IT_GRENADE_LAUNCHER, BM_GL, self.ammo_rockets, 1);
	self.bm_gw4 = BM_WheelGun (IT_ROCKET_LAUNCHER, BM_RL, self.ammo_rockets, 1);
	self.bm_gw5 = BM_WheelGun (IT_LIGHTNING, BM_LG, self.ammo_cells, 1);
	self.bm_gw6 = BM_WheelGun (IT_LASER_CANNON, BM_LASER, self.ammo_cells, 1);
	if (self.items & IT_MEGAMAN)
		self.bm_gw7 = 10 + floor (self.mm_ammo);
	else
		self.bm_gw7 = 0;
	self.bm_gw8 = BM_WheelFun (FG_M4, BM_FG7);
	self.bm_gw9 = BM_WheelFun (FG_GARAND, BM_FG9);
	self.bm_gw10 = BM_WheelFun (FG_DOB, BM_FG1);
	self.bm_gw11 = BM_WheelFun (FG_PONG, BM_FG2);
	self.bm_gw12 = BM_WheelFun (FG_PICKLE, BM_FG3);
	self.bm_gw13 = BM_WheelFun (FG_NETSEND, BM_FG4);
	self.bm_gw14 = BM_WheelFun (FG_DOOKIE, BM_FG5);
	self.bm_gw15 = BM_WheelFun (FG_WCANNON, BM_FG6);
	self.bm_gw16 = BM_WheelFun (FG_KYLE, BM_FG8);
	self.bm_gw17 = BM_WheelFun (FG_CYRAX, 0);
};
