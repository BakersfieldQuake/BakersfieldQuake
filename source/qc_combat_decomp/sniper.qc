#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE SNIPER RIFLE (see sniper_defs.qc for the rules and numbers)

A port of Team Fortress 2.9's sniper rifle (SNIPER.QC, WEAPONS.QC W_FireSniperRifle / W_WeaponFrame), without
head shots. TF counted the charge and the zoom per frame; here they run per second at TF's 72-frame pace.
Hooks (patch_sniper_combat.py): W_WeaponFrame runs Sniper_PlayerFrame every frame and lets Sniper_Frame handle
the fire button for IT_NAILGUN (it charges while held and fires on release, so W_Attack never sees the rifle),
PutClientInServer runs Sniper_Spawn, and the obituary checks sn_inflicting.
================
*/

void() Sniper_Precache =
{
	precache_model ("progs/v_srifle.mdl");
	precache_model ("progs/g_srifle.mdl");
	precache_model ("progs/p_srifle.md3");
	precache_model ("progs/sight.spr");
	precache_sound ("weapons/sniper.wav");
};

// ---------------------------------------------------------------- zoom and the laser dot

// zoomed in past SN_FOV_SCOPE the held rifle is hidden: TF's view model fills a quarter of the screen at fov 30
float(entity p) Sniper_Scoped =
{
	return (p.weapon == IT_NAILGUN && p.sn_fov > 0 && p.sn_fov < SN_FOV_SCOPE && autocvar_sn_autozoom);
};

// TF_zoom, with DarkPlaces' viewzoom instead of stuffing "fov N" to the client
void() Sniper_Zoom =
{
	if (self.sn_fov >= 90 || !autocvar_sn_autozoom)
		self.viewzoom = 0;		// 0 = normal (an unset viewzoom)
	else
		self.viewzoom = self.sn_fov / 90;
	if (self.weapon != IT_NAILGUN || self.v_weapon_position_helper)
		return;		// the weapon-sway helper draws the gun itself and hides it with Sniper_Scoped (custom_effects.qc)
	if (Sniper_Scoped (self))
		self.weaponmodel = "";
	else if (self.weaponmodel == "")
		self.weaponmodel = "progs/v_srifle.mdl";
};

// SniperSight_Update: the dot goes where the rifle points (moved every frame here, TF moved it every 0.1 s)
void(entity p) Sniper_PlaceSight =
{
	local vector src;

	makevectors (p.v_angle);
	src = p.origin + v_forward * 10;
	src_z = p.absmin_z + p.size_z * 0.7;
	traceline (src, src + v_forward * SN_RANGE, FALSE, p);
	p.sn_sight.angles = vectoangles (v_forward);
	setorigin (p.sn_sight, trace_endpos - v_forward * 2);
};

void() Sniper_StopAiming =
{
	self.sn_aiming = FALSE;
	self.sn_heat = 0;
	if (self.sn_sight)
		remove (self.sn_sight);
	self.sn_sight = world;
};

// the dot cleans itself up if its owner died, left or put the rifle away without Sniper_Frame noticing
void() Sniper_SightThink =
{
	local entity o;

	o = self.owner;
	if (o.sn_sight != self || !o.sn_aiming || o.health <= 0 || o.weapon != IT_NAILGUN || o.classname != "player")
	{
		if (o.sn_sight == self)
		{
			o.sn_sight = world;
			o.sn_aiming = FALSE;
			o.sn_heat = 0;
		}
		remove (self);
		return;
	}
	self.nextthink = time + 0.1;
};

// SniperSight_Create + the start of aiming in W_WeaponFrame
void() Sniper_StartAiming =
{
	local entity dot;

	self.sn_aiming = TRUE;
	self.sn_heat = SN_HEAT_START;
	self.sn_fov = 90;
	dot = spawn ();
	dot.owner = self;
	dot.classname = "sn_sight";
	dot.movetype = MOVETYPE_NOCLIP;
	dot.solid = SOLID_NOT;
	setmodel (dot, "progs/sight.spr");
	dot.think = Sniper_SightThink;
	dot.nextthink = time + 0.1;
	self.sn_sight = dot;
	Sniper_PlaceSight (self);
};

// ---------------------------------------------------------------- the shot

// W_FireSniperRifle
void() Sniper_Fire =
{
	local vector src, f, g, h;
	local float dmg, zdif;
	local entity victim;

	makevectors (self.v_angle);
	sound7 (self, CHAN_WEAPON, "weapons/sniper.wav", 0.4, ATTN_NORM, SNDSPD);	// was 1: the clip is at full scale and was far louder than every other gun
	self.punchangle_x = -4;		// TF's big kick
	self.ammo_nails = self.ammo_nails - 1;		// the LAN magazine reads this back (bm_reload.qc)
	self.currentammo = self.ammo_nails;
	self.show_hostile = time + 1;
	player_shot1 ();			// the kick on v_srifle.mdl (weaponframe 1-6) and the player's shoot frames

	src = self.origin + v_forward * 10;
	src_z = self.absmin_z + self.size_z * 0.7;
	traceline (src, src + v_forward * SN_RANGE, FALSE, self);
	if (PC_TraceIntercept (self, src, trace_endpos, self.sn_heat))
		return;
	if (trace_fraction == 1)
		return;

	dmg = self.sn_heat;
	sn_inflicting = 1;
	victim = world;
	if (trace_ent.classname == "player" && trace_ent.takedamage)
	{
		// carry the bullet on to the victim's middle (their origin's x/y) and see how high it is there
		f = trace_endpos - src;
		g = trace_endpos;
		g_z = 0;
		h = trace_ent.origin;
		h_z = 0;
		f = normalize (f) * vlen (g - h) + trace_endpos;
		zdif = f_z - trace_ent.origin_z;
		if (zdif < 0)
		{
			dmg = dmg * 0.5;
			sn_inflicting = 2;
			victim = trace_ent;
			victim.sn_leg = min (victim.sn_leg + 1, SN_LEG_MAX);
		}
		// (TF: zdif > 20 is a head shot, x2. Not here.)
	}
	ClearMultiDamage ();
	TraceAttack (dmg, v_forward);		// blood or a wall puff, as the other guns do
	ApplyMultiDamage ();
	sn_inflicting = 0;

	if (victim && victim.health > 0)
	{
		sprint (victim, "Leg injury!\n");
		sprint (self, "Leg shot - that'll slow them down!\n");
	}
};

// ---------------------------------------------------------------- per frame

// top of W_WeaponFrame, every frame: zoom back out, move the dot, mend legs, cap speed
void() Sniper_PlayerFrame =
{
	local vector v;
	local float cap, z;

	if (self.sn_aiming && (self.weapon != IT_NAILGUN || self.health <= 0))
		Sniper_StopAiming ();

	// TF T_Heal: healing mends the legs (all of them once health is over 95)
	if (self.sn_leg && self.health > self.sn_hp)
	{
		if (self.health > 95)
			self.sn_leg = 0;
		else if (self.health > self.sn_hp + 1)		// a pickup, not one point of regeneration
			self.sn_leg = max (0, self.sn_leg - ceil (self.health / 20));
	}
	self.sn_hp = self.health;

	if (!self.sn_aiming && self.sn_fov > 29 && self.sn_fov < 90)
	{
		self.sn_fov = min (90, self.sn_fov + SN_FOV_RATE_OUT * frametime);
		Sniper_Zoom ();
	}
	if (self.sn_aiming && self.sn_sight)
		Sniper_PlaceSight (self);

	// TeamFortress_SetSpeed: aiming walks at SN_AIM_SPEED, every leg shot takes 10% off.
	// TF capped the client's move speeds; this caps ground speed after the move (bots too), so knockback still flies.
	if ((self.sn_aiming || self.sn_leg) && (self.flags & FL_ONGROUND))
	{
		cap = cvar ("sv_maxspeed");
		if (self.sn_aiming)
			cap = SN_AIM_SPEED;
		cap = cap * (10 - self.sn_leg) / 10;
		v = self.velocity;
		z = v_z;
		v_z = 0;
		if (vlen (v) > cap)
		{
			v = normalize (v) * cap;
			v_z = z;
			self.velocity = v;
		}
	}
};

// W_WeaponFrame, once attack_finished has passed: TRUE = the rifle is in hand and took care of the fire button
float() Sniper_Frame =
{
	local vector v;

	if (self.weapon != IT_NAILGUN)
	{
		if (self.sn_aiming)
			Sniper_StopAiming ();
		return FALSE;
	}
	if (self.button0)
	{
		if (self.sn_aiming)
		{
			self.sn_heat = min (SN_HEAT_MAX, self.sn_heat + SN_HEAT_RATE * frametime);
			if (self.sn_fov > SN_FOV_MIN)
			{
				self.sn_fov = max (SN_FOV_MIN, self.sn_fov - SN_FOV_RATE_IN * frametime);
				Sniper_Zoom ();
			}
		}
		else if (self.meleeing != 1 && self.throwing != 1)
		{
			v = self.velocity;
			v_z = 0;
			if (vlen (v) <= SN_START_SPEED && W_CheckNoAmmo ())
				Sniper_StartAiming ();
		}
	}
	else if (self.sn_aiming)
	{
		// let go: fire, but only standing on something (in the air the charge is just lost)
		if (self.flags & FL_ONGROUND)
		{
			SuperDamageSound ();
			Sniper_Fire ();
			self.attack_timer = 1;
			self.attack_finished = time + SN_REFIRE;
		}
		Sniper_StopAiming ();
	}
	return TRUE;
};

// PutClientInServer: a fresh life has steady legs and no zoom
void() Sniper_Spawn =
{
	Sniper_StopAiming ();
	self.sn_leg = 0;
	self.sn_hp = self.health;
	if (self.sn_fov > 0 && self.sn_fov < 90)
		self.viewzoom = 0;
	self.sn_fov = 90;
};

// obituary text (TF's DMSG_SNIPERRIFLE / DMSG_SNIPERLEGSHOT)
string() Sniper_Death =
{
	if (sn_inflicting == 2)
	{
		if (random () < 0.5)
			return " is made legless by ";
		return " gets their legs blown off by ";
	}
	if (random () < 0.3)
		return " takes a bullet in the chest from ";
	return " succumbs to sniperfire from ";
};
