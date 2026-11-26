#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
DOWNTOWN BOTS & FULL-ARSENAL DEATHMATCH AI (BakersfieldQuake)

- Instant F1 (add enemy bot, impulse 101) & F2 (kick bot, impulse 102) without sv_cheats,
  auto-upgrading singleplayer / small-slot local games to 16-player Deathmatch if needed.
- Clear [BOT] <Name> identity across scoreboard, obituaries, chat, and CSQC 3D overhead tags.
- Full knowledge of BakersfieldQuake weapons (Bonk Hammer, Shotgun, Super Shotgun,
  Laptop Gun, Milky Gun, Grenade Launcher, Rocket Launcher, Lightning Gun, CCC Laser Cannon,
  Mega Man Gun, Rob Dob flying head, Jar o' Green Guys, Pickle Surprise, NetSend PC, Dookie Bazooka,
  Wheelman Cannon, M4A1, M1 Garand), including charging, cocktail-shaking,
  semi-auto trigger resets, ballistic arcs, and magazine reloads.
- Aggressive yet forgiving ("pretty easy") combat pacing: smooth human aim spread, brief target
  reaction delay, burst firing, and scaled bot->player damage (bm_bot_dmg).
- Clever downtown navigation & verticality: automatic street/rooftop waypoint graph linking
  info_skypad launchers, trigger_teleport portals, vertical trigger_push ladders, ground jump pads,
  rooftop jump-offs, active jetpack flight, and rival hunting across the city grid.
================
*/

// downtown-only bot moves use fixed downtown coordinates: map check cached once per map (0 = not yet, 1 = no, 2 = yes)
float	bm_dt_map_cache;

// ---------------------------------------------------------------- helpers & notifications

void(string msg) BM_BotToastHumans =
{
	local entity p;

	p = find (world, classname, "player");
	while (p)
	{
		if (p.ishuman == 1)
			centerprint (p, msg);
		p = find (p, classname, "player");
	}
};

// Called inside BotConnect while `self` is the newly spawned bot and `caller` triggered it
void(entity caller) BM_BotConnected =
{
	local string msg;

	self.bm_bot_wep_t = 0;
	self.bm_bot_burst_t = 0;
	self.bm_bot_pause_t = 0;
	self.bm_bot_react_t = 0;
	self.bm_bot_lastfoe = world;
	self.bm_bot_wc_rel = 0;
	self.bm_bot_hm_rel = 0;
	self.bm_bot_jp_cd = time + 1.0;
	self.bm_bot_jp_end = 0;
	self.bm_bot_stuck_t = time + 1.2;
	self.bm_bot_stuck_org = self.origin;
	self.bm_bot_hunt_t = time + 0.8 + random () * 1.8;
	self.bm_bot_roof_t = 0;
	self.bm_bot_aim_t = 0;
	self.bm_bot_mm_cd = time + 6.0 + random () * 10.0;

	bprint ("^2+ Added ", self.netname, " (", ftos (bot_count), " bots active)\n");
	msg = strcat ("^2+ ", self.netname, "^7  (", ftos (bot_count), " bots active)\n^3F1^7: add bot   ^3F2^7: kick bot");
	if (caller != world && caller.classname == "player" && caller.ishuman == 1)
		centerprint (caller, msg);
	else
		BM_BotToastHumans (msg);
};

void(string kname) BM_BotNotifyKick =
{
	local string nm, msg;

	nm = kname;
	if (nm == "")
		nm = "[BOT]";
	bprint ("^1- Kicked ", nm, " (", ftos (bot_count), " bots left)\n");
	msg = strcat ("^1- Kicked ", nm, "^7  (", ftos (bot_count), " bots left)\n^3F1^7: add bot   ^3F2^7: kick bot");
	BM_BotToastHumans (msg);
};

void(float wid) BM_BotSelectWeaponID;
float() BM_BotCurWeaponID;

void() BM_BotReport =
{
	local entity p;
	local float wid;

	bprint ("=== BOT REPORT (bots=", ftos (bot_count), ", ways=", ftos (waypoints), ") ===\n");
	p = player_head;
	while (p)
	{
		if (p.ishuman != 1)
		{
			self = p;
			wid = BM_BotCurWeaponID ();
			bprint ("  ", p.netname, " org=", vtos (p.origin), " wep=", ftos (wid), " jp=", ftos (p.jp_on));
			bprint (" fuel=", ftos (floor (p.jp_fuel * 10)), " frags=", ftos (p.frags), " foe=", p.enemy.netname, "\n");
		}
		p = p._next;
	}
};

float() BM_CountHumans =
{
	local entity p;
	local float n;

	n = 0;
	p = find (world, classname, "player");
	while (p)
	{
		if (p.ishuman == 1)
			n = n + 1;
		p = find (p, classname, "player");
	}
	return n;
};

// Top of BotImpulses (frikbot.bot.qc): F1 = impulse 101 (addbotenemy), F2 = impulse 102 (removebot), impulse 100 (addbot)
float() BM_BotImpulses =
{
	local float want_n;
	local entity os;

	if (self.impulse == 109 && (!autocvar_bm_public_server || cvar ("sv_cheats")))
	{
		os = self;
		BM_BotReport ();
		self = os;
		return TRUE;
	}

	if (self.impulse < 100 || self.impulse > 102)
		return FALSE;

	// Public server (bm_public_server 1): any player may add/kick bots, no sv_cheats needed. Server owners switch it off with bm_bots_allowed 0.
	if (autocvar_bm_public_server && !autocvar_bm_bots_allowed)
	{
		sprint (self, "Bots are turned off on this server.\n");
		centerprint (self, "Bots are turned off on this server");
		return TRUE;
	}

	// bm_manual_bots (turns off auto bot fill for the map) is set only once a bot is really added or kicked:
	// a refused press must not switch off fill and the reserve kick for the rest of the map

	if (self.impulse == 100 || self.impulse == 101)
	{
		if (autocvar_bm_public_server)
		{
			// never restart a live public server because of a key press: just obey the cap, the free-slot reserve and a short cooldown
			if (time < bm_bot_add_t)
				return TRUE;
			if (bot_count >= autocvar_bm_bot_max)
			{
				sprint (self, strcat ("Bot limit reached (", ftos (bot_count), " bots). Press F2 to kick a bot.\n"));
				centerprint (self, strcat ("^3Bot limit reached^7 (", ftos (bot_count), ") - press ^3F2^7 to kick"));
				return TRUE;
			}
			if (max_clients - BM_CountHumans () - bm_obs_count - bot_count - 1 < autocvar_bm_bot_reserve)
			{
				sprint (self, strcat ("Keeping a slot open for players (", ftos (bot_count), " bots active). Press F2 to kick a bot.\n"));
				centerprint (self, strcat ("^3Slot kept free for players^7 (", ftos (bot_count), " bots)"));
				return TRUE;
			}
			bm_bot_add_t = time + autocvar_bm_bot_cooldown;
			bm_manual_bots = TRUE;
			BotConnect ((self.impulse == 101), 0, cvar ("skill"));
			return TRUE;
		}
		// Safety net: if player loaded a map in Singleplayer or with too few client slots, auto-restart in 16-slot DM
		if ((!deathmatch && !coop) || (ClientNextAvailable () == -1 && max_clients < 16))
		{
			registercvar ("bm_autobot", "0");
			want_n = bot_count + 1;
			if (want_n < 1)
				want_n = 1;
			cvar_set ("bm_autobot", ftos (want_n));
			sprint (self, "Switching to 16-player Deathmatch & adding [BOT]...\n");
			centerprint (self, "Switching to 16-player Deathmatch & adding [BOT]...");
			localcmd ("maxplayers 16\ndeathmatch 1\ncoop 0\nrestart\n");
			return TRUE;
		}
		if (ClientNextAvailable () == -1)
		{
			sprint (self, strcat ("Server is full (", ftos (bot_count), " bots active). Press F2 to kick a bot.\n"));
			centerprint (self, strcat ("^3Server full^7 (", ftos (bot_count), " bots) - press ^3F2^7 to kick"));
			return TRUE;
		}
		bm_manual_bots = TRUE;
		BotConnect ((self.impulse == 101), 0, cvar ("skill"));
		return TRUE;
	}

	if (self.impulse == 102)
	{
		if (bot_count <= 0)
		{
			sprint (self, "No bots left to kick (press F1 to add a bot).\n");
			centerprint (self, "No bots active - press ^3F1^7 to add a bot");
			return TRUE;
		}
		bm_manual_bots = TRUE;
		KickABot ();
		return TRUE;
	}

	return FALSE;
};

// ---------------------------------------------------------------- full 19-weapon arsenal

// Weapon range vector: x = sweet spot, y = min safe range, z = max effective range
vector(float wep) BM_BotWeaponRange =
{
	local float g;

	if (wep == IT_FUNGUN)
	{
		g = self.fg_sel;
		if (g == FG_DOB)		return '650 260 2500';
		if (g == FG_PONG)		return '420 90 1250';
		if (g == FG_PICKLE)		return '260 50 850';
		if (g == FG_NETSEND)	return '380 80 1100';
		if (g == FG_DOOKIE)		return '460 110 1750';
		if (g == FG_WCANNON)	return '550 180 2100';
		if (g == FG_M4)			return '520 35 2500';
		if (g == FG_GARAND)		return '680 70 2800';
		return '320 40 1000';
	}
	if (wep == IT_MEGAMAN)			return '520 90 2400';
	if (wep == IT_AXE)				return '55 0 150';
	if (wep == IT_SHOTGUN)			return '240 0 900';		// Shotgun
	if (wep == IT_SUPER_SHOTGUN)	return '160 0 650';
	if (wep == IT_NAILGUN)			return '560 90 2200';	// Laptop Gun
	if (wep == IT_SUPER_NAILGUN)	return '350 60 1200';	// Milky Gun
	if (wep == IT_GRENADE_LAUNCHER)	return '380 120 1050';
	if (wep == IT_ROCKET_LAUNCHER)	return '450 130 2200';
	if (wep == IT_LIGHTNING)		return '350 45 600';
	if (wep == IT_LASER_CANNON)		return '500 70 1850';	// CCC Laser Cannon
	return '350 0 1200';
};

// Check if bot currently owns and has ready rounds for weapon candidate `id`
// Candidate IDs:
//   1 = Bonk Hammer (IT_AXE), 2 = Shotgun (IT_SHOTGUN), 3 = SSG, 4 = Laptop Gun,
//   5 = Milky Gun, 6 = GL, 7 = RL, 8 = LG, 9 = CCC Laser, 10 = Chainsaw, 11 = Mega Man,
//   61 = Rob Dob, 63 = Pickle, 64 = NetSend, 65 = Mystery Box, 66 = Wheelman,
//   67 = M4A1, 68 = Thompson, 69 = M1 Garand
// NS_Count walks every entity; the weapon picker asks it several times a frame per bot. The 2-PC cap is only a preference,
// so a count up to half a second old is fine (the real 20-PC limit in netsend.qc still uses the exact NS_Count)
float() BM_BotNSCount =
{
	if (time >= self.bm_ns_t)
	{
		self.bm_ns_n = NS_Count (self);
		self.bm_ns_t = time + 0.5;
	}
	return self.bm_ns_n;
};

float(float id) BM_BotCanUseWeapon =
{
	local float g;

	if (id == 1)
		return ((self.items & IT_AXE) != 0);
	if (id == 10)
		return FALSE;		// Chainsaw removed
	if (id == 2)
	{
		if (!(self.items & IT_SHOTGUN)) return FALSE;
		if (autocvar_bm_reload) return (BM_GetMag (self, BM_SG) >= 1);
		return (self.ammo_shells >= 1);
	}
	if (id == 3)
	{
		if (!(self.items & IT_SUPER_SHOTGUN)) return FALSE;
		if (autocvar_bm_reload) return (BM_GetMag (self, BM_SSG) >= 1);
		return (self.ammo_shells >= 1);
	}
	if (id == 4)
	{
		if (!(self.items & IT_NAILGUN)) return FALSE;
		if (autocvar_bm_reload) return (BM_GetMag (self, BM_NG) >= 1);
		return (self.ammo_nails >= 1);
	}
	if (id == 5)
	{
		if (!(self.items & IT_SUPER_NAILGUN)) return FALSE;
		if (autocvar_bm_reload) return (BM_GetMag (self, BM_SNG) >= 1);
		return (self.ammo_nails >= 2);
	}
	if (id == 6)
	{
		if (!(self.items & IT_GRENADE_LAUNCHER)) return FALSE;
		if (autocvar_bm_reload) return (BM_GetMag (self, BM_GL) >= 1);
		return (self.ammo_rockets >= 1);
	}
	if (id == 7)
	{
		if (!(self.items & IT_ROCKET_LAUNCHER)) return FALSE;
		if (autocvar_bm_reload) return (BM_GetMag (self, BM_RL) >= 1);
		return (self.ammo_rockets >= 1);
	}
	if (id == 8)
	{
		if (self.waterlevel > 1) return FALSE;
		if (!(self.items & IT_LIGHTNING)) return FALSE;
		if (autocvar_bm_reload) return (BM_GetMag (self, BM_LG) >= 2);
		return (self.ammo_cells >= 2);
	}
	if (id == 9)
	{
		if (!(self.items & IT_LASER_CANNON)) return FALSE;
		if (autocvar_bm_reload) return (BM_GetMag (self, BM_LASER) >= 1);
		return (self.ammo_cells >= 1);
	}
	if (id == 11)
	{
		if (time < self.bm_bot_mm_cd)
			return FALSE;
		if (autocvar_bm_reload)
			return (BM_GetMag (self, BM_MM) >= MM_MAX_AMMO);
		return (self.mm_ammo >= MM_MAX_AMMO);
	}
	if (id >= 61 && id <= 69)
	{
		g = id - 60;
		if (!FunGun_Available (g))
			return FALSE;
		if (time < self.fg_lock_t && g != self.fg_lock_gun)
			return FALSE;
		if (g == FG_DOB && self.fd_head != world)
			return FALSE;
		if (g == FG_NETSEND && BM_BotNSCount () >= 2)
			return FALSE;
		return (FunGun_Ammo (self, g) >= 1);
	}
	return FALSE;
};

float() BM_BotCurWeaponID =
{
	if (self.weapon == IT_FUNGUN)
		return FunGun_Impulse (self.fg_sel);
	if (self.weapon == IT_MEGAMAN)			return 11;
	if (self.weapon == IT_LASER_CANNON)		return 9;
	if (self.weapon == IT_LIGHTNING)		return 8;
	if (self.weapon == IT_ROCKET_LAUNCHER)	return 7;
	if (self.weapon == IT_GRENADE_LAUNCHER)	return 6;
	if (self.weapon == IT_SUPER_NAILGUN)	return 5;
	if (self.weapon == IT_NAILGUN)			return 4;
	if (self.weapon == IT_SUPER_SHOTGUN)	return 3;
	if (self.weapon == IT_SHOTGUN)			return 2;
	return 1;
};

void(float id) BM_BotSelectWeaponID =
{
	local float cur;

	cur = BM_BotCurWeaponID ();
	if (cur == id)
		return;

	if (id >= 61 && id <= 69)
	{
		self.impulse = id;
		return;
	}
	if (id == 11)
	{
		self.impulse = MM_IMPULSE;
		return;
	}
	if (id == 9)
	{
		// Direct select when owning both LG and CCC Laser so impulse 8 doesn't land on LG first
		if (time >= self.attack_finished && !self.has_fired && (self.items & IT_LASER_CANNON))
		{
			self.weapon = IT_LASER_CANNON;
			self.idletimer = 1;
			self.switchtimer = -5;
			W_SetCurrentAmmo ();
		}
		else
			self.impulse = 8;
		return;
	}
	if (id == 8)
	{
		if (time >= self.attack_finished && !self.has_fired && (self.items & IT_LIGHTNING))
		{
			self.weapon = IT_LIGHTNING;
			self.idletimer = 1;
			self.switchtimer = -5;
			W_SetCurrentAmmo ();
		}
		else
			self.impulse = 8;
		return;
	}
	if (id == 1)
	{
		if (self.weapon != IT_AXE)
			self.impulse = 1;
		return;
	}
	// IDs 2..7 map directly to impulses 2..7
	self.impulse = id;
};

// Range-smart weighted reservoir pick across ALL 19 weapons so bots actively showcase the whole arsenal
float(float brange) BM_BotWeaponSwitch =
{
	local float cur, id, w, tot, pick;
	local vector rng;

	if (!deathmatch && !coop)
		return FALSE;

	// Never interrupt active charge/windup/flight states or Cyrax net stun
	if (self.cy_trapped_by != world || self.fd_head != world || self.wc_charging > 0 || self.dk_charging > 0 || self.gj_shaking > 0 || self.rh_charging > 0 || self.ky_locking > 0 || self.ltg_phase == 1)
		return TRUE;
	if (self.weapon == IT_AXE && self.hm_state == 1)
		return TRUE;
	if (self.pk_throw_at > 0 || self.ns_throw_at > 0 || self.gj_throw_at > 0 || self.rh_throw_at > 0 || self.ky_throw_at > 0)
		return TRUE;

	cur = BM_BotCurWeaponID ();
	rng = BM_BotWeaponRange (self.weapon);

	// Keep current gun until its hold window expires if it still has rounds and fits the current range
	if (time < self.bm_bot_wep_t && BM_BotCanUseWeapon (cur))
	{
		if (brange < 0 || (brange >= rng_y && brange <= rng_z))
			return TRUE;
	}
	// If currently reloading at safe mid/far range, let the reload finish half the time
	if (self.bm_rl_slot != 0 && (brange < 0 || brange > 380) && time < self.bm_bot_wep_t)
		return TRUE;

	if (brange < 0)
		brange = 480;

	pick = 0;
	tot = 0;

	// Evaluate every weapon candidate 1..20 with range-tuned weights
	id = 1;
	while (id <= 69)
	{
		if (id == 12)
			id = 61;

		w = 0;
		if (BM_BotCanUseWeapon (id))
		{
			if (brange < 135)
			{
				// Point-blank melee & close-quarters chaos
				if (id == 1)		w = 18;		// Bonk Hammer
				else if (id == 3)	w = 26;		// Super Shotgun
				else if (id == 2)	w = 15;		// Shotgun
				else if (id == 8)	w = 18;		// Lightning Gun
				else if (id == 9)	w = 14;		// CCC Laser
				else if (id == 5)	w = 15;		// Milky Gun
				else if (id == 67)	w = 14;		// M4A1
				else if (id == 63)	w = 10;		// Pickle Surprise
			}
			else if (brange < 420)
			{
				// Close-to-mid street brawls
				if (id == 3)		w = 19;		// Super Shotgun
				else if (id == 67)	w = 20;		// M4A1
				else if (id == 7)	w = 22;		// Rocket Launcher
				else if (id == 5)	w = 17;		// Milky Gun
				else if (id == 2)	w = 15;		// Shotgun
				else if (id == 8)	w = 17;		// Lightning Gun
				else if (id == 9)	w = 16;		// CCC Laser
				else if (id == 6)	w = 7;		// Grenade Launcher
				else if (id == 11)	w = 2;		// Mega Man Gun (rare)
				else if (id == 62)	w = 2;		// Jar o' Green Guys (reduced)
				else if (id == 63)	w = 3;		// Pickle Surprise
				else if (id == 64)	w = 5;		// NetSend PC
				else if (id == 65)	w = 8;		// Dookie Bazooka
				else if (id == 66)	w = 9;		// Wheelman Cannon
				else if (id == 4)	w = 10;		// Laptop Gun
				else if (id == 69)	w = 16;		// M1 Garand
			}
			else if (brange < 1050)
			{
				// Mid-range boulevard / rooftop-to-street firefights
				if (id == 7)		w = 24;		// Rocket Launcher
				else if (id == 67)	w = 22;		// M4A1
				else if (id == 69)	w = 20;		// M1 Garand
				else if (id == 9)	w = 17;		// CCC Laser
				else if (id == 4)	w = 12;		// Laptop Gun
				else if (id == 5)	w = 11;		// Milky Gun
				else if (id == 6)	w = 6;		// Grenade Launcher
				else if (id == 2)	w = 11;		// Shotgun
				else if (id == 11)	w = 1;		// Mega Man Gun (rare)
				else if (id == 62)	w = 2;		// Jar o' Green Guys (reduced)
				else if (id == 65)	w = 8;		// Dookie Bazooka
				else if (id == 66)	w = 11;		// Wheelman Cannon
				else if (id == 64)	w = 5;		// NetSend PC
				else if (id == 63)	w = 3;		// Pickle Surprise
				else if (id == 61)	w = 10;		// Rob Dob flying head
			}
			else
			{
				// Long-range cross-intersection & skyscraper duels
				if (id == 69)		w = 28;		// M1 Garand
				else if (id == 67)	w = 26;		// M4A1
				else if (id == 4)	w = 20;		// Laptop Gun (laser-guided homing)
				else if (id == 7)	w = 20;		// Rocket Launcher
				else if (id == 9)	w = 16;		// CCC Laser
				else if (id == 66)	w = 16;		// Wheelman Cannon
				else if (id == 11)	w = 1;		// Mega Man Gun (rare)
				else if (id == 61)	w = 14;		// Rob Dob flying head
			}
		}

		if (w > 0)
		{
			tot = tot + w;
			if (random () * tot < w)
				pick = id;
		}
		id = id + 1;
	}

	if (pick > 0)
	{
		BM_BotSelectWeaponID (pick);
		self.bm_bot_wep_t = time + 4.0 + random () * 4.5;
		return TRUE;
	}

	// Fallback if everything else is reloading: M4 / SSG / Bonk Hammer
	if (FunGun_Available (FG_M4))
		BM_BotSelectWeaponID (67);
	else
		BM_BotSelectWeaponID (1);
	self.bm_bot_wep_t = time + 2.0;
	return TRUE;
};

// Aim tuning (called at the end of bot_angle_set when self.enemy != world):
// 1. Ballistic pitch arcs for Grenade Launcher, Pickle Surprise, Jar o' Green Guys, Rob Fastball, Wheelman Cannon, and floor pitch for NetSend.
// 2. Smooth, human-like aim error when bm_bot_easy is on so 5-10 aggressive bots feel fun and fair.
void() BM_BotAimAdjust =
{
	local float dist, scale, g;

	if (!self.enemy)
		return;

	dist = vlen (realorigin (self.enemy) - self.origin);

	// Weapon-specific ballistic pitch adjustments (negative b_angle_x = pitch UP, positive = pitch DOWN)
	if (self.weapon == IT_GRENADE_LAUNCHER)
		self.b_angle_x = self.b_angle_x - bound (4, dist * 0.022, 24);
	else if (self.weapon == IT_FUNGUN)
	{
		g = self.fg_sel;
		if (g == FG_PICKLE)
			self.b_angle_x = self.b_angle_x - bound (3, dist * 0.016, 18);
		else if (g == FG_PONG)
			self.b_angle_x = self.b_angle_x - bound (2, dist * 0.014, 15);
		else if (g == FG_NETSEND)
			self.b_angle_x = bound (8, self.b_angle_x + 12, 22);		// toss LOL.BAT onto the street ahead
		else if (g == FG_WCANNON)
			self.b_angle_x = self.b_angle_x - bound (1, dist * 0.008, 10);
	}

	if (!autocvar_bm_bot_easy)
		return;

	if (time >= self.bm_bot_aim_t)
	{
		self.bm_bot_aim_t = time + 0.35 + random () * 0.35;
		self.bm_bot_aim_err_y = (random () - 0.5) * 22;		// +/- 11 deg yaw spread
		self.bm_bot_aim_err_x = (random () - 0.5) * 11;		// +/- 5.5 deg pitch spread
	}

	scale = 1;
	if (dist < 160)
		scale = 0.35;		// melee / point-blank still lands swings cleanly
	else if (dist > 1200)
		scale = 1.15;

	self.b_angle_y = frik_anglemod (self.b_angle_y + self.bm_bot_aim_err_y * scale);
	self.b_angle_x = bound (-70, self.b_angle_x + self.bm_bot_aim_err_x * scale, 80);
};

// Trigger control for all 19 weapons (called from bot_shoot when enemy is in sight & range)
void() BM_BotShoot =
{
	local float g, dist;

	if (!self.enemy || self.enemy.health <= 0 || self.cy_trapped_by != world)
		return;

	// If current gun ran dry (e.g. single-shot Rob Dob / Wheelman / NetSend / Pickle / Jar / Rob Head), swap smoothly
	if (!BM_BotCanUseWeapon (BM_BotCurWeaponID ()) && !self.wc_charging && !self.dk_charging && !self.gj_shaking && !self.rh_charging && !self.ky_locking && self.hm_state != 1 && self.ltg_phase != 1)
	{
		dist = vlen (realorigin (self.enemy) - self.origin);
		self.bm_bot_wep_t = 0;
		BM_BotWeaponSwitch (dist);
	}

	// Brief human reaction delay on acquiring a brand-new target in easy mode
	if (autocvar_bm_bot_easy)
	{
		if (self.enemy != self.bm_bot_lastfoe)
		{
			self.bm_bot_lastfoe = self.enemy;
			self.bm_bot_react_t = time + 0.22 + random () * 0.18;
		}
		if (time < self.bm_bot_react_t)
			return;
	}

	// Don't fire until roughly facing the target (within ~28 deg yaw) unless in melee range
	dist = vlen (realorigin (self.enemy) - self.origin);
	if (dist > 140 && fabs (angcomp (self.b_angle_y, self.v_angle_y)) > 28)
		return;

	// 1. Bonk Hammer (IT_AXE): hold fire to wind up, release fire to swing!
	if (self.weapon == IT_AXE)
	{
		if (self.hm_state == 0 && time >= self.hm_ready)
		{
			self.button0 = TRUE;
			self.bm_bot_hm_rel = time + 0.20 + random () * 0.45;
		}
		else if (self.hm_state == 1)
		{
			if (time < self.bm_bot_hm_rel && dist > 85)
				self.button0 = TRUE;
			else
				self.button0 = FALSE;		// let go -> Hammer_Release swings!
		}
		return;
	}

	// 1b. Laptop Gun (IT_NAILGUN): hold fire to queue DDoS packets, release to flood!
	if (self.weapon == IT_NAILGUN)
	{
		if (self.ltg_phase == 0)
		{
			if (time >= self.attack_finished)
			{
				self.button0 = TRUE;
				self.bm_bot_wc_rel = time + 0.15 + random () * 0.65;
			}
		}
		else if (self.ltg_phase == 1)
		{
			if (time < self.bm_bot_wc_rel && self.ltg_queue < self.ltg_qmax)
				self.button0 = TRUE;
			else
				self.button0 = FALSE;
		}
		else
			self.button0 = FALSE;
		return;
	}

	// 2. Fun Guns with special trigger mechanics
	if (self.weapon == IT_FUNGUN)
	{
		g = self.fg_sel;

		// Jar o' Green Guys: hold fire 0.25..0.65s to cocktail-shake, then release to hurl the swarm!
		if (g == FG_PONG)
		{
			if (self.gj_throw_at > 0)
			{
				self.button0 = FALSE;
				return;
			}
			if (self.gj_shaking <= 0)
			{
				if (time >= self.attack_finished)
				{
					self.button0 = TRUE;
					self.bm_bot_wc_rel = time + 0.25 + random () * 0.40;
				}
			}
			else if (time < self.bm_bot_wc_rel)
				self.button0 = TRUE;
			else
				self.button0 = FALSE;
			return;
		}

		// Rob Dob (DJI Drone): press button to launch steerable flying head
		if (g == FG_DOB)
		{
			if (self.rh_throw_at > 0)
			{
				self.button0 = FALSE;
				return;
			}
			if (self.rh_charging <= 0)
			{
				if (time >= self.attack_finished)
				{
					self.button0 = TRUE;
					self.bm_bot_wc_rel = time + 0.10 + random () * 0.15;
				}
			}
			else if (time < self.bm_bot_wc_rel)
				self.button0 = TRUE;
			else
				self.button0 = FALSE;
			return;
		}

		// Dookie Bazooka: hold fire to wind up tabla reactor 0.40..1.05s, then release!
		if (g == FG_DOOKIE)
		{
			if (!self.dk_charging)
			{
				if (time >= self.dk_cool)
				{
					self.button0 = TRUE;
					self.bm_bot_wc_rel = time + 0.40 + random () * 0.65;
				}
			}
			else if (time < self.bm_bot_wc_rel)
				self.button0 = TRUE;
			else
				self.button0 = FALSE;
			return;
		}

		// Wheelman Cannon: hold fire to charge 0.45..1.15s, then release to blast screaming Wheelman!
		if (g == FG_WCANNON)
		{
			if (!self.wc_charging)
			{
				if (time >= self.wc_cool)
				{
					self.button0 = TRUE;
					self.bm_bot_wc_rel = time + 0.45 + random () * 0.70;
				}
			}
			else if (time < self.bm_bot_wc_rel)
				self.button0 = TRUE;
			else
				self.button0 = FALSE;
			return;
		}

		// Pocket Kyle: hold fire briefly to wind up / lock, then release to throw!
		if (g == FG_KYLE)
		{
			if (self.ky_throw_at > 0)
			{
				self.button0 = FALSE;
				return;
			}
			if (!self.ky_locking)
			{
				if (time >= self.ky_cool)
				{
					self.button0 = TRUE;
					self.bm_bot_wc_rel = time + 0.30 + random () * 0.45;
				}
			}
			else if (time < self.bm_bot_wc_rel)
				self.button0 = TRUE;
			else
				self.button0 = FALSE;
			return;
		}

		// M1 Garand: semi-auto trigger reset (.gar_ready requires a button0 = 0 frame between shots)
		if (g == FG_GARAND)
		{
			if (!self.gar_ready)
				self.button0 = FALSE;
			else
				self.button0 = TRUE;
			return;
		}
	}

	// 2b. Mega Man Gun: fire at most one grenade per selection, then enforce cooldown & switch to regular weapons
	if (self.weapon == IT_MEGAMAN)
	{
		if (time < self.bm_bot_mm_cd || self.mm_pending)
		{
			self.button0 = FALSE;
			return;
		}
		if (time >= self.attack_finished && self.mm_ammo >= 1)
		{
			self.button0 = TRUE;
			self.bm_bot_mm_cd = time + 18.0 + random () * 14.0;
			self.bm_bot_wep_t = 0;
			return;
		}
		self.button0 = FALSE;
		return;
	}

	// 3. Easy-mode natural burst pacing on rapid/sustained guns so bots feel lively, not robotic
	if (autocvar_bm_bot_easy && self.ltg_phase != 1)
	{
		if (time < self.bm_bot_pause_t)
		{
			self.button0 = FALSE;
			return;
		}
		if (time >= self.bm_bot_burst_t)
		{
			if (self.bm_bot_burst_t > 0)
			{
				self.bm_bot_pause_t = time + 0.22 + random () * 0.28;
				self.bm_bot_burst_t = 0;
				self.button0 = FALSE;
				return;
			}
			self.bm_bot_burst_t = time + 0.95 + random () * 1.10;
		}
	}

	self.button0 = TRUE;
};

// Give bots jetpack fuel & a rotating variety of map weapons each life so all 19 guns see action
void() BM_BotSpawnLoadout =
{
	local float r, k;

	if (!deathmatch)
		return;

	if (autocvar_bm_bot_jpfuel > 0 && self.jp_fuel < autocvar_bm_bot_jpfuel)
	{
		self.jp_fuel = autocvar_bm_bot_jpfuel;
		self.jp_low = FALSE;
	}

	// Grant 3 varied map weapons per life so bots use every stock + custom gun right away
	k = 0;
	while (k < 3)
	{
		r = floor (random () * 8);
		if (r == 0)			self.items = self.items | IT_SHOTGUN;			// Shotgun
		else if (r == 1)	self.items = self.items | IT_SUPER_SHOTGUN;
		else if (r == 2)	self.items = self.items | IT_NAILGUN;			// Laptop Gun
		else if (r == 3)	self.items = self.items | IT_SUPER_NAILGUN;		// Milky Gun
		else if (r == 4)	self.items = self.items | IT_GRENADE_LAUNCHER;
		else if (r == 5)	self.items = self.items | IT_ROCKET_LAUNCHER;
		else if (r == 6)	self.items = self.items | IT_LIGHTNING;
		else				self.items = self.items | IT_LASER_CANNON;		// CCC Laser Cannon
		k = k + 1;
	}

	if (self.ammo_shells < 40)	self.ammo_shells = 40;
	if (self.ammo_nails < 80)	self.ammo_nails = 80;
	if (self.ammo_rockets < 25)	self.ammo_rockets = 25;
	if (self.ammo_cells < 60)	self.ammo_cells = 60;

	if (autocvar_bm_reload)
		BM_FillAll ();

	if (time + 8.0 > self.bm_bot_mm_cd)
		self.bm_bot_mm_cd = time + 8.0 + random () * 10.0;
	self.bm_bot_free_t = 0;
	self.bm_bot_free_dir = '0 0 0';
	self.bm_bot_stuck_org = self.origin;
	self.bm_bot_stuck_t = time + 0.9;
	self.bm_bot_hunt_t = time + 1.2 + random () * 2.5;
	self.bm_bot_wep_t = 0;
	BM_BotWeaponSwitch (450);
};

// ---------------------------------------------------------------- downtown waypoint graph builder

// Windowed downtown crop (downtownsmall / bakersfielddowntown): D-feet (-340, -900)..(950, 275), SHIFT (835, -285)
// -> map units X [-14100, 1380], Y [-7380, 6720]. Guard out-of-window nodes so bots never path into the eastern void.
float(vector org) BM_DtWayInBounds =
{
	if (world.model == "maps/bakersfielddowntown.bsp" || world.model == "maps/bakersfieldish.bsp" || world.model == "maps/downtownsmall.bsp"
		|| mapname == "bakersfielddowntown" || mapname == "bakersfieldish" || mapname == "downtownsmall")
	{
		if (org_x < -14100 || org_x > 1380 || org_y < -7380 || org_y > 6720)
			return FALSE;
	}
	return TRUE;
};

// Find an existing waypoint within `rad` XY and 72 Z, or create a new one
entity(vector org, float rad) BM_EnsureWaypoint =
{
	local entity w;
	local vector d;

	if (!BM_DtWayInBounds (org))
		return world;

	w = way_head;
	while (w)
	{
		if (fabs (w.origin_z - org_z) < 72)
		{
			d = w.origin - org;
			d_z = 0;
			if (vlen (d) < rad)
				return w;
		}
		w = w._next;
	}
	return make_waypoint (org);
};

float(entity w) BM_WayFreeSlots =
{
	local float n;

	n = 0;
	if (w.target1 == world) n = n + 1;
	if (w.target2 == world) n = n + 1;
	if (w.target3 == world) n = n + 1;
	if (w.target4 == world) n = n + 1;
	return n;
};

void(string cname, float rad) BM_AddClassWaypoints =
{
	local entity e, w;

	e = find (world, classname, cname);
	while (e)
	{
		w = BM_EnsureWaypoint (e.origin + '0 0 24', rad);
		if (w != world && (e.flags & FL_ITEM))
			e.current_way = w;
		e = find (e, classname, cname);
	}
};

void(vector a_org, vector b_org, float rad) BM_LinkBiPair =
{
	local entity wa, wb;

	wa = BM_EnsureWaypoint (a_org, rad);
	wb = BM_EnsureWaypoint (b_org, rad);
	if (wa != world && wb != world)
	{
		LinkWays (wa, wb);
		LinkWays (wb, wa);
	}
};

void(vector a_org, vector b_org, float rad) BM_LinkOneWayPair =
{
	local entity wa, wb;

	wa = BM_EnsureWaypoint (a_org, rad);
	wb = BM_EnsureWaypoint (b_org, rad);
	if (wa != world && wb != world)
		LinkWays (wa, wb);
};

// Explicit WALK18 stair, lobby, balcony & suite exit chains so indoor/sub-grade/elevated spawns
// (especially Sandrini's basement, Fox lobby/mezz/stage, Padre lobby/suites/roof, Nile, Jerry's, Dagny's,
// NE alcove, and Padre Garage L4) connect 100% into the main street waypoint graph.
// All z values sit at resting player origin_z (floor_z + 26u) with step hops |dz| < 64u so FrikBot's
// 32u 3D capture sphere pops every stair node cleanly without triggering bot_lost().
void() BM_AddDowntownIndoorWaypoints =
{
	// 1. Sandrini's basement, booth (spawn #14), back room & staircase up to Eye St
	BM_LinkBiPair ('-3384 276 -106', '-3559 276 -106', 44);
	BM_LinkBiPair ('-3559 218 -60', '-3559 276 -106', 44);
	BM_LinkBiPair ('-3559 276 -106', '-3720 300 -106', 44);
	BM_LinkBiPair ('-3768 468 -106', '-3708 372 -106', 44);
	BM_LinkBiPair ('-3708 372 -106', '-3720 300 -106', 44);
	BM_LinkBiPair ('-3720 300 -106', '-3792 300 -76', 40);
	BM_LinkBiPair ('-3792 300 -76', '-3864 300 -37', 40);
	BM_LinkBiPair ('-3864 300 -37', '-3936 300 9', 40);
	BM_LinkBiPair ('-3936 300 9', '-4008 300 32', 40);
	BM_LinkBiPair ('-4008 300 32', '-4116 300 32', 44);
	BM_LinkBiPair ('-4116 300 32', '-4330 294 26', 44);

	// 2. Fox Theater lobby, mezzanine (spawn #02) & west stage exit (spawn #03)
	BM_LinkBiPair ('-9900 2568 32', '-10080 2472 32', 48);
	BM_LinkBiPair ('-10080 2472 32', '-10080 2304 32', 48);
	BM_LinkBiPair ('-10080 2304 32', '-10080 2076 26', 48);
	BM_LinkOneWayPair ('-10236 2736 276', '-9840 2736 276', 48);
	BM_LinkOneWayPair ('-9840 2736 276', '-9780 2592 232', 48);
	BM_LinkOneWayPair ('-9780 2592 232', '-9912 2496 172', 48);
	BM_LinkOneWayPair ('-9912 2496 172', '-10044 2472 172', 48);
	BM_LinkOneWayPair ('-10044 2472 172', '-10080 2304 32', 48);
	BM_LinkBiPair ('-9912 3456 74', '-10092 3996 72', 56);
	BM_LinkBiPair ('-10092 3996 72', '-10332 4116 72', 48);
	BM_LinkBiPair ('-10332 4116 72', '-10500 4248 72', 48);
	BM_LinkBiPair ('-10500 4248 72', '-10680 4248 26', 48);
	BM_LinkBiPair ('-10680 4248 26', '-10704 3684 31', 56);

	// 3. Padre Hotel lobby (spawns #04, #42), upper suites (#43..#45) & roof drops (#05)
	BM_LinkBiPair ('-9588 -5424 32', '-9390 -5366 32', 48);
	BM_LinkBiPair ('-9390 -5366 32', '-9156 -5652 32', 48);
	BM_LinkBiPair ('-9156 -5652 32', '-8916 -5652 26', 48);
	BM_LinkOneWayPair ('-9492 -4860 1256', '-9732 -4500 32', 64);
	BM_LinkOneWayPair ('-10184 -5824 1256', '-10356 -5824 26', 64);
	BM_LinkBiPair ('-10179 -5697 536', '-10179 -5504 536', 44);
	BM_LinkBiPair ('-10179 -5504 536', '-9576 -5504 536', 48);
	BM_LinkBiPair ('-9576 -5504 536', '-9576 -4862 536', 48);
	BM_LinkOneWayPair ('-9576 -4862 536', '-9616 -4862 536', 36);
	BM_LinkOneWayPair ('-9616 -4862 536', '-9696 -4862 35', 44);
	BM_LinkBiPair ('-10064 -5697 824', '-9984 -5688 824', 44);
	BM_LinkBiPair ('-9984 -5688 824', '-9984 -5568 824', 44);
	BM_LinkBiPair ('-9984 -5568 824', '-9624 -5568 824', 48);
	BM_LinkBiPair ('-9624 -5568 824', '-9624 -4862 824', 48);
	BM_LinkOneWayPair ('-9624 -4862 824', '-9696 -4862 35', 44);
	BM_LinkBiPair ('-9696 -4862 35', '-9624 -4848 35', 36);
	BM_LinkBiPair ('-9624 -4848 35', '-9624 -4776 35', 36);
	BM_LinkBiPair ('-9624 -4776 35', '-9816 -4776 35', 48);
	BM_LinkBiPair ('-9816 -4776 35', '-9816 -4440 26', 48);

	// 4. Nile Theater auditorium (spawn #06) & balcony drop (spawn #07)
	BM_LinkBiPair ('-11004 -3492 26', '-10704 -3252 32', 56);
	BM_LinkBiPair ('-10704 -3252 32', '-10774 -2814 32', 56);
	BM_LinkBiPair ('-10774 -2814 32', '-10764 -2508 26', 56);
	BM_LinkOneWayPair ('-10896 -3024 194', '-10740 -3096 194', 48);
	BM_LinkOneWayPair ('-10740 -3096 194', '-10884 -3096 32', 48);
	BM_LinkBiPair ('-10884 -3096 32', '-10774 -2814 32', 48);

	// 5. Jerry's Pizza interior -> Chester Ave
	BM_LinkBiPair ('-1140 -4032 32', '-876 -4092 32', 48);
	BM_LinkBiPair ('-876 -4092 32', '-636 -4140 32', 48);
	BM_LinkBiPair ('-636 -4140 32', '-444 -4140 26', 48);

	// 6. Dagny's Coffee interior -> Eye & 20th St
	BM_LinkBiPair ('-5616 2760 37', '-5820 2496 33', 48);
	BM_LinkBiPair ('-5820 2496 33', '-5820 2268 32', 48);
	BM_LinkBiPair ('-5820 2268 32', '-5988 1980 26', 48);

	// 7. NE 20th/Chester alcove & Padre Garage L4 -> street exits
	BM_LinkBiPair ('-1212 3780 33', '-1212 4044 26', 48);
	BM_LinkBiPair ('-1212 4044 26', '-1212 4140 32', 48);
	BM_LinkBiPair ('-1212 4140 32', '-444 4308 26', 48);
	BM_LinkOneWayPair ('-7092 -5472 417', '-6924 -5448 417', 48);
	BM_LinkOneWayPair ('-6924 -5448 417', '-6840 -5640 32', 48);
	BM_LinkBiPair ('-6840 -5640 32', '-6840 -6276 26', 56);
};

void() BM_BuildDowntownWaypoints =
{
	local entity e, dest, w1, w2, a, b, best1, best2, best3, best4, bestdrop;
	local vector mid, top, d;
	local float hgt, dist, d1, d2, d3, d4, ddrop;

	ClearAllWays ();

	// 1. SkyPads (8 rooftop ballistic launchers: origin -> pos1)
	// Linked via LinkWays (NOT TeleLinkWays, which makes FrikBot look for a trigger_teleport)
	e = find (world, classname, "info_skypad");
	while (e)
	{
		if (BM_DtWayInBounds (e.origin + '0 0 24') && BM_DtWayInBounds (e.pos1 + '0 0 24'))
		{
			w1 = BM_EnsureWaypoint (e.origin + '0 0 24', 96);
			w2 = BM_EnsureWaypoint (e.pos1 + '0 0 24', 128);
			if (w1 != world && w2 != world)
				LinkWays (w1, w2);
		}
		e = find (e, classname, "info_skypad");
	}

	// 2. Teleporters (6 portals across W / C / E districts)
	e = find (world, classname, "trigger_teleport");
	while (e)
	{
		if (e.target != "")
		{
			dest = find (world, targetname, e.target);
			if (dest)
			{
				mid = (e.absmin + e.absmax) * 0.5;
				mid_z = e.absmin_z + 28;
				if (BM_DtWayInBounds (mid) && BM_DtWayInBounds (dest.origin + '0 0 24'))
				{
					w1 = BM_EnsureWaypoint (mid, 96);
					w2 = BM_EnsureWaypoint (dest.origin + '0 0 24', 128);
					if (w1 != world && w2 != world)
						TeleLinkWays (w1, w2);
				}
			}
		}
		e = find (e, classname, "trigger_teleport");
	}

	// 3. Vertical trigger_push building ladders (29 in downtown)
	e = find (world, classname, "trigger_push");
	while (e)
	{
		hgt = e.absmax_z - e.absmin_z;
		mid = (e.absmin + e.absmax) * 0.5;
		if (hgt >= 140)
		{
			top = mid_x * '1 0 0' + mid_y * '0 1 0' + (e.absmax_z + 28) * '0 0 1';
			makevectors (e.angles);
			v_forward_z = 0;
			if (vlen (v_forward) > 0.01)
				top = top + normalize (v_forward) * 56;
			if (BM_DtWayInBounds (mid_x * '1 0 0' + mid_y * '0 1 0' + (e.absmin_z + 28) * '0 0 1') && BM_DtWayInBounds (top))
			{
				w1 = BM_EnsureWaypoint (mid_x * '1 0 0' + mid_y * '0 1 0' + (e.absmin_z + 28) * '0 0 1', 96);
				w2 = BM_EnsureWaypoint (top, 128);
				if (w1 != world && w2 != world)
					LinkWays (w1, w2);
			}
		}
		e = find (e, classname, "trigger_push");
	}

	// 3b. Explicit indoor stair, lobby, balcony & suite exit chains (seeded before class merges)
	BM_AddDowntownIndoorWaypoints ();

	// 4. Jetpacks, armor, ammo/health street pickups, and all street + rooftop DM spawns (guns removed from maps)
	BM_AddClassWaypoints ("item_jetpack", 180);
	BM_AddClassWaypoints ("item_armorInv", 180);
	BM_AddClassWaypoints ("item_armor2", 220);
	BM_AddClassWaypoints ("item_armor1", 220);
	BM_AddClassWaypoints ("item_rockets", 260);
	BM_AddClassWaypoints ("item_shells", 260);
	BM_AddClassWaypoints ("item_spikes", 260);
	BM_AddClassWaypoints ("item_cells", 260);
	BM_AddClassWaypoints ("item_health", 280);
	BM_AddClassWaypoints ("info_player_deathmatch", 280);

	// 5. Ground jump pads (5 low trigger_push pads): link upward to nearest elevated waypoint
	e = find (world, classname, "trigger_push");
	while (e)
	{
		hgt = e.absmax_z - e.absmin_z;
		if (hgt < 140)
		{
			mid = (e.absmin + e.absmax) * 0.5;
			mid_z = e.absmin_z + 28;
			w1 = BM_EnsureWaypoint (mid, 96);
			if (w1 != world)
			{
				best1 = world;
				d1 = 1600;
				b = way_head;
				while (b)
				{
					if (b.origin_z > w1.origin_z + 120)
					{
						d = b.origin - w1.origin;
						d_z = 0;
						dist = vlen (d);
						if (dist < d1)
						{
							d1 = dist;
							best1 = b;
						}
					}
					b = b._next;
				}
				if (best1 != world)
					LinkWays (w1, best1);
			}
		}
		e = find (e, classname, "trigger_push");
	}

	// 6. One-way rooftop-to-street jump-off links (fall damage is off, so bots leap off buildings!)
	a = way_head;
	while (a)
	{
		if (a.origin_z > 140 && BM_WayFreeSlots (a) >= 1)
		{
			bestdrop = world;
			ddrop = 1350;
			b = way_head;
			while (b)
			{
				if (b.origin_z < 95 && a.origin_z - b.origin_z > 90)
				{
					d = b.origin - a.origin;
					d_z = 0;
					dist = vlen (d);
					if (dist > 75 && dist < ddrop)
					{
						traceline (a.origin + '0 0 42', b.origin + '0 0 120', TRUE, a);
						if (trace_fraction == 1)
						{
							ddrop = dist;
							bestdrop = b;
						}
					}
				}
				b = b._next;
			}
			if (bestdrop != world)
				LinkWays (a, bestdrop);
		}
		a = a._next;
	}

	// 7. Connect same-tier streets & rooftops in all 4 compass quadrants (+X, -X, +Y, -Y)
	a = way_head;
	while (a)
	{
		if (BM_WayFreeSlots (a) > 0)
		{
			best1 = world; d1 = 6500;
			best2 = world; d2 = 6500;
			best3 = world; d3 = 6500;
			best4 = world; d4 = 6500;
			b = way_head;
			while (b)
			{
				if (b != a && fabs (b.origin_z - a.origin_z) <= 115)
				{
					d = b.origin - a.origin;
					dist = vlen (d);
					if (dist < 6500)
					{
						if (fabs (d_x) >= fabs (d_y))
						{
							if (d_x > 0 && dist < d1)
							{
								traceline (a.origin + '0 0 36', b.origin + '0 0 36', TRUE, a);
								if (trace_fraction == 1) { d1 = dist; best1 = b; }
							}
							else if (d_x <= 0 && dist < d2)
							{
								traceline (a.origin + '0 0 36', b.origin + '0 0 36', TRUE, a);
								if (trace_fraction == 1) { d2 = dist; best2 = b; }
							}
						}
						else
						{
							if (d_y > 0 && dist < d3)
							{
								traceline (a.origin + '0 0 36', b.origin + '0 0 36', TRUE, a);
								if (trace_fraction == 1) { d3 = dist; best3 = b; }
							}
							else if (d_y <= 0 && dist < d4)
							{
								traceline (a.origin + '0 0 36', b.origin + '0 0 36', TRUE, a);
								if (trace_fraction == 1) { d4 = dist; best4 = b; }
							}
						}
					}
				}
				b = b._next;
			}
			if (best1 != world) { LinkWays (a, best1); LinkWays (best1, a); }
			if (best2 != world) { LinkWays (a, best2); LinkWays (best2, a); }
			if (best3 != world) { LinkWays (a, best3); LinkWays (best3, a); }
			if (best4 != world) { LinkWays (a, best4); LinkWays (best4, a); }
		}
		a = a._next;
	}

	waypoint_mode = WM_LOADED;
	dprint ("downtown bot graph built: ", ftos (waypoints), " waypoints\n");
};

float() BM_IsDowntownMap =
{
	return (mapname == "downtown" || mapname == "downtownsmall" || mapname == "bakersfielddowntown" || mapname == "bakersfieldish"
		|| world.model == "maps/downtown.bsp" || world.model == "maps/downtownsmall.bsp" || world.model == "maps/bakersfielddowntown.bsp" || world.model == "maps/bakersfieldish.bsp");
};

// BM_IsDowntownMap, cached (BM_BotPostAI runs it per bot per frame)
float() BM_BotDowntown =
{
	if (!bm_dt_map_cache)
	{
		if (BM_IsDowntownMap ())
			bm_dt_map_cache = 2;
		else
			bm_dt_map_cache = 1;
	}
	return (bm_dt_map_cache == 2);
};

void() BM_MapLoad =
{
	bm_dt_way_done = FALSE;
	bm_route_lock_t = 0;
	if (BM_IsDowntownMap ())
		bm_dt_way_t = time + 0.75;		// right after Jetpack_Place (0.5s) spawns the 11 jetpacks
	else
		bm_dt_way_t = 0;
};

void() BM_BotStartFrame =
{
	local float auto_n, hn;

	if (BM_IsDowntownMap () && !bm_dt_way_done && bm_dt_way_t > 0 && time >= bm_dt_way_t)
	{
		bm_dt_way_done = TRUE;
		if (max_clients > 1)
			BM_BuildDowntownWaypoints ();
	}

	// Watchdog: FrikBot can leave route_table locked if bot_look_for_crap(TRUE) finds nothing or a bot dies mid-route
	if (route_table != world)
	{
		if (bm_wasfreed (route_table) || route_table.classname != "player" || route_table.health <= 0)
		{
			ClearRouteTable ();		// items -1: pending WaypointThinks stop (no busy_waypoints < 0, no finish with self = world)
			route_table = world;
			busy_waypoints = 0;
			direct_route = 0;
			bm_route_lock_t = 0;
		}
		else if (!bm_route_lock_t)
			bm_route_lock_t = time + 0.75;
		else if (time >= bm_route_lock_t && (busy_waypoints <= 0 || time >= bm_route_lock_t + 2.25))
		{
			// a route still being computed (busy_waypoints > 0) gets up to 3 s before it is dropped
			ClearRouteTable ();
			route_table = world;
			busy_waypoints = 0;
			direct_route = 0;
			bm_route_lock_t = 0;
		}
	}
	else
		bm_route_lock_t = 0;

	// Public server housekeeping (2 ticks per second): bots give up a slot when humans have filled the server,
	// and the whole crew leaves once nobody human has been connected for bm_bot_idle seconds (no 14 bots fighting on an empty VPS)
	if (autocvar_bm_public_server && bot_count > 0 && time >= bm_bot_slot_t)
	{
		bm_bot_slot_t = time + 0.5;
		hn = BM_CountHumans ();
		if (hn > 0)
		{
			bm_bot_idle_t = time + autocvar_bm_bot_idle;
			if (max_clients - hn - bm_obs_count - bot_count < autocvar_bm_bot_reserve)
				KickABot ();
		}
		else
		{
			if (bm_bot_idle_t == 0)
				bm_bot_idle_t = time + autocvar_bm_bot_idle;
			if (autocvar_bm_bot_idle > 0 && time >= bm_bot_idle_t)
				KickABot ();
		}
	}

	// Complete auto-restart F1 bot spawn if triggered from Singleplayer / low-slot server
	if (time > 1.2 && time >= bm_autobot_check_t)
	{
		bm_autobot_check_t = time + 0.5;
		registercvar ("bm_autobot", "0");
		auto_n = floor (cvar ("bm_autobot"));
		if (auto_n > 0 && deathmatch && max_clients > 1)
		{
			cvar_set ("bm_autobot", "0");
			bm_manual_bots = TRUE;
			while (bot_count < auto_n && ClientNextAvailable () != -1)
				BotConnect (1, 0, cvar ("skill"));
		}
	}
};

// ---------------------------------------------------------------- item priority, spawning, patrol & hunting

float(entity thing) BM_BotItemPriority =
{
	if (thing.classname == "item_jetpack")
	{
		// Only prioritize nearby jetpacks so bots across the map don't all march to Padre Hotel's jetpack
		if (thing.solid == SOLID_TRIGGER && thing.model != string_null && self.jp_fuel < autocvar_jp_fuel * 0.65
			&& vlen (thing.origin - self.origin) < 1400)
			return 68;
	}
	return 0;
};

// Spread bot spawns across all DM districts instead of clustering around Padre Hotel / combat centroid
entity() BM_BotPickSpawn =
{
	local entity spot, p, best;
	local float dmin, d, near_cnt, seen, score, bestscore, n;

	if (!deathmatch)
		return world;

	n = 0;
	p = player_head;
	while (p)
	{
		if (p != self && p.health > 0 && !p.bm_obs)		// observers: health 100, nowhere on the map
			n = n + 1;
		p = p._next;
	}

	best = world;
	bestscore = 1000000;
	spot = find (world, classname, "info_player_deathmatch");
	while (spot)
	{
		p = findradius (spot.origin, 48);
		while (p && p.classname != "player")
			p = p.chain;
		if (!p)
		{
			if (n == 0)
				score = random () * 1000;
			else
			{
				dmin = 99999;
				near_cnt = 0;
				seen = 0;
				p = player_head;
				while (p)
				{
					if (p != self && p.health > 0 && !p.bm_obs)
					{
						d = vlen (p.origin - spot.origin);
						if (d < dmin)
							dmin = d;
						if (d < 1700)
							near_cnt = near_cnt + 1;
						if (d < 3400 && !seen)
						{
							traceline (spot.origin + '0 0 28', p.origin + '0 0 28', TRUE, spot);
							if (trace_fraction == 1)
								seen = 1;
						}
					}
					p = p._next;
				}
				score = near_cnt * 2400 + seen * 3600 + random () * 1500;
				if (dmin < 1000)
					score = score + (1000 - dmin) * 5.0;
				if (dmin > 6000)
					score = score + (dmin - 6000) * 0.25;
			}
			if (score < bestscore)
			{
				bestscore = score;
				best = spot;
			}
		}
		spot = find (spot, classname, "info_player_deathmatch");
	}
	return best;
};

entity() BM_BotPickHuntTarget =
{
	local entity p, b, best;
	local float d, crowd, score, bestscore;

	best = world;
	bestscore = 999999;
	p = player_head;
	while (p)
	{
		if (p != self && p.health > 0 && p.modelindex != 0 && !(p.flags & FL_NOTARGET) && !p.bm_obs)
		{
			if (!((teamplay || CTF_ENABLED) && p.team > 0 && p.team == self.team))
			{
				// Count other bots already swarming this player so bots don't all pile into one street fight
				crowd = 0;
				b = player_head;
				while (b)
				{
					if (b != self && b != p && b.ishuman != 1 && b.health > 0 && !b.bm_obs)		// an observer (ishuman 3) is no bot
					{
						if (b.enemy == p || b.target1 == p || vlen (b.origin - p.origin) < 950)
							crowd = crowd + 1;
					}
					b = b._next;
				}
				d = vlen (p.origin - self.origin);
				score = d + crowd * 1800 + random () * 2800;
				if (p.ishuman == 1 && d < 4200)
					score = score * 0.85;
				if (score < bestscore)
				{
					bestscore = score;
					best = p;
				}
			}
		}
		p = p._next;
	}
	return best;
};

entity() BM_BotPickPatrolWay =
{
	local entity w, p, best;
	local float d, crowd, score, bestscore;

	if (way_head == world)
		return world;

	best = world;
	bestscore = 999999;
	w = way_head;
	while (w)
	{
		if (w != self.current_way && w != self.last_way)
		{
			d = vlen (w.origin - self.origin);
			if (d >= 600 && d <= 8500)
			{
				crowd = 0;
				p = player_head;
				while (p)
				{
					if (p != self && p.health > 0 && !p.bm_obs && vlen (p.origin - w.origin) < 1500)
						crowd = crowd + 1;
					p = p._next;
				}
				score = crowd * 2600 + random () * 3200;
				if (d < 1200)
					score = score + (1200 - d) * 1.2;
				if (score < bestscore)
				{
					bestscore = score;
					best = w;
				}
			}
		}
		w = w._next;
	}
	return best;
};

// Shared 12-ray open-direction picker for both unstuck recovery and continuous non-idle patrolling
vector(float avoid_last, float curve_bias, entity steer_toward) BM_BotPickOpenDir =
{
	local vector open_dir, want_dir, probe;
	local float best_frac, yaw, s, fl, fr, turn_side, want_yaw, cont;

	turn_side = num_for_edict (self);
	if (turn_side - 2 * floor (turn_side / 2) == 1)
		turn_side = 1;
	else
		turn_side = -1;
	want_yaw = self.v_angle_y + turn_side * 28;
	makevectors ('0 1 0' * want_yaw);
	want_dir = v_forward;

	best_frac = -9;
	open_dir = want_dir;
	yaw = 0;
	while (yaw < 360)
	{
		makevectors ('0 1 0' * yaw);
		traceline (self.origin + '0 0 18', self.origin + '0 0 18' + v_forward * 320, TRUE, self);
		s = trace_fraction;
		traceline (self.origin + '0 0 18' + v_right * 20, self.origin + '0 0 18' + v_right * 20 + v_forward * 320, TRUE, self);
		fl = trace_fraction;
		traceline (self.origin + '0 0 18' - v_right * 20, self.origin + '0 0 18' - v_right * 20 + v_forward * 320, TRUE, self);
		fr = trace_fraction;
		if (fl < s) s = fl;
		if (fr < s) s = fr;

		// Avoid walking blindly into lava or slime
		probe = self.origin + v_forward * min (160, 300 * s);
		traceline (probe + '0 0 16', probe - '0 0 96', TRUE, self);
		cont = pointcontents (trace_endpos + '0 0 4');
		if (cont == CONTENT_LAVA || cont == CONTENT_SLIME)
			s = s - 1.5;

		if (avoid_last && vlen (self.bm_bot_free_dir) > 0.5 && (v_forward * self.bm_bot_free_dir) > 0.65)
			s = s - 0.55;
		if (steer_toward != world && s > 0.45)
			s = s + 0.18 * (v_forward * normalize (steer_toward.origin - self.origin));
		if (curve_bias)
			s = s + 0.25 * (v_forward * want_dir) + random () * 0.12;

		if (s > best_frac)
		{
			best_frac = s;
			open_dir = v_forward;
		}
		yaw = yaw + 30;
	}
	return open_dir;
};

.float bm_bot_repick_t;		// roam re-pick throttle: the 12-ray scan at most every 0.25 s per bot

// the flat roam probe hit something: is it stairs / a ramp / a curb he can walk up?
// floor 42 ahead at most 48 above his feet, and a line 42 over that slope clear for the full 84
float(vector dir) BM_BotSlopeOpen =
{
	local vector ahead, from;

	ahead = self.origin + dir * 42;
	traceline (ahead + '0 0 60', ahead - '0 0 64', TRUE, self);
	if (trace_startsolid || trace_fraction == 1)
		return FALSE;
	if (trace_endpos_z - (self.origin_z + self.mins_z) > 48)
		return FALSE;
	from = self.origin + '0 0 18';
	traceline (from, from + (trace_endpos + '0 0 42' - from) * 2, TRUE, self);
	return (trace_fraction >= 0.85);
};

// Runs every AI frame at the end of BotAI (frikbot.bot_ai.qc)
void() BM_BotPostAI =
{
	local entity goal, prey;
	local vector d, open_dir;
	local float dz, xydist, s, fl;

	if (self.health <= 0 || self.cy_trapped_by != world)
		return;

	// Safety: release charged Bonk Hammer or Wheelman Cannon if target died or charge finished
	if (self.weapon == IT_AXE && self.hm_state == 1)
	{
		if (!self.enemy || time >= self.bm_bot_hm_rel)
			self.button0 = FALSE;
		else
			self.button0 = TRUE;
	}
	if (self.weapon == IT_FUNGUN && ((self.fg_sel == FG_WCANNON && self.wc_charging > 0) || (self.fg_sel == FG_DOOKIE && self.dk_charging > 0) || (self.fg_sel == FG_KYLE && self.ky_locking > 0)))
	{
		if (!self.enemy || time >= self.bm_bot_wc_rel)
			self.button0 = FALSE;
		else
			self.button0 = TRUE;
	}

	// Out-of-combat tactical magazine top-up for firearms (M4 / Garand)
	if (!self.enemy && autocvar_bm_reload && !self.bm_rl_slot && time > self.bm_lastshot + 2.0)
	{
		s = BM_SlotOf (self);
		if (BM_IsFirearmSlot (s))
		{
			if (BM_GetMag (self, s) < BM_MagSize (s) * 0.35)
				self.impulse = BM_RELOAD_IMPULSE;
		}
	}

	// Trickle-recharge a small reserve of jetpack fuel while grounded so bots keep flying around downtown
	if (!self.jp_on && (self.flags & FL_ONGROUND) && self.jp_fuel < 1.8 && autocvar_bm_bot_jpfuel > 0)
		self.jp_fuel = min (1.8, self.jp_fuel + frametime * 0.22);

	// ---------------- 1. JETPACK AI ----------------
	goal = self.enemy;
	if (!goal)
		goal = self.target1;

	if (self.jb_vehicle == world && self.rr_vehicle == world && self.veh_van == world && self.fd_head == world && self.waterlevel < 2)
	{
		if (self.jp_on)
		{
			// Steer & climb while jetpack is burning
			dz = 80;
			if (goal != world)
			{
				d = realorigin (goal) - self.origin;
				dz = d_z;
				if (!self.enemy)
					self.keys = (self.keys & 960) | frik_KeysForDir (d);
			}
			if (dz > -10 && time < self.bm_bot_jp_end)
			{
				self.button2 = TRUE;
				self.keys = self.keys | KEY_MOVEUP;
			}
			else if (dz < -120)
				self.button2 = FALSE;

			// Shut off jetpack once high above goal, out of burst time, or roofed under a ceiling
			traceline (self.origin, self.origin + '0 0 72', TRUE, self);
			if (time >= self.bm_bot_jp_end || self.jp_fuel < 0.15 || (dz < -60 && self.origin_z > 120) || trace_fraction < 0.5)
			{
				Jetpack_Off ();
				self.bm_bot_jp_cd = time + 1.8 + random () * 2.0;
			}
		}
		else if (self.jp_fuel >= 0.7 && time >= self.bm_bot_jp_cd)
		{
			// Case A: Cushion a huge skyscraper leap or boost horizontal distance mid-drop
			if (!(self.flags & FL_ONGROUND) && self.velocity_z < -420 && self.jp_fuel >= 0.5)
			{
				Jetpack_On ();
				self.button2 = TRUE;
				self.bm_bot_jp_end = time + 0.65;
			}
			// Case B: Fly up onto buildings/rooftops to reach an elevated enemy or waypoint!
			else if (goal != world)
			{
				d = realorigin (goal) - self.origin;
				dz = d_z;
				d_z = 0;
				xydist = vlen (d);
				if (dz > 95 && xydist < 1800)
				{
					traceline (self.origin, self.origin + '0 0 220', TRUE, self);
					if (trace_fraction > 0.75)
					{
						if (self.flags & FL_ONGROUND)
							bot_jump ();
						Jetpack_On ();
						self.button2 = TRUE;
						self.keys = (self.keys & 960) | frik_KeysForDir (d) | KEY_MOVEUP;
						self.bm_bot_jp_end = time + bound (0.9, dz / 210 + 0.5, 3.2);
					}
				}
				// Case C: Occasional aggressive jetpack aerial strafe during open-sky firefights!
				else if (self.enemy != world && xydist > 220 && xydist < 1400 && random () < 0.018)
				{
					traceline (self.origin, self.origin + '0 0 260', TRUE, self);
					if (trace_fraction == 1)
					{
						if (self.flags & FL_ONGROUND)
							bot_jump ();
						Jetpack_On ();
						self.button2 = TRUE;
						self.bm_bot_jp_end = time + 0.9 + random () * 1.1;
					}
				}
			}
		}
	}

	// ---------------- 2. ROOFTOP LEAP-OFF AI ----------------
	// Fall damage is off (bm_falldamage 0): if on a building/rooftop and enemy is down on the street, charge & jump off!
	// (downtown only: z > 130 is a rooftop there, on other maps it can be any upper floor or ledge)
	if ((self.flags & FL_ONGROUND) && self.origin_z > 130 && !autocvar_bm_falldamage && BM_BotDowntown ())
	{
		if (self.enemy != world && self.origin_z - self.enemy.origin_z > 80)
		{
			d = realorigin (self.enemy) - self.origin;
			d_z = 0;
			if (vlen (d) > 32)
			{
				self.keys = (self.keys & 960) | frik_KeysForDir (d);
				d = normalize (d);
				traceline (self.origin + '0 0 18', self.origin + '0 0 18' + d * 64, TRUE, self);
				fl = trace_fraction;
				traceline (self.origin + '0 0 78', self.origin + '0 0 78' + d * 64, TRUE, self);
				if (fl < 1 && trace_fraction == 1)
				{
					// Vault over 48-56u rooftop brick parapet (e.g. Padre Garage L6)
					if (!self.jp_on && self.jp_fuel >= 0.35)
					{
						Jetpack_On ();
						self.button2 = TRUE;
						self.bm_bot_jp_end = time + 0.55;
					}
					else
					{
						self.flags = self.flags - (self.flags & FL_ONGROUND);
						self.velocity = d * 280 + '0 0 340';
					}
				}
				else
				{
					traceline (self.origin + d * 44, self.origin + d * 44 - '0 0 96', TRUE, self);
					if (trace_fraction == 1)
						bot_jump ();
				}
			}
		}
		else if (!self.enemy)
		{
			if (!self.bm_bot_roof_t)
				self.bm_bot_roof_t = time + 2.8;
			else if (time >= self.bm_bot_roof_t)
			{
				// Don't camp empty rooftops: vault any parapet and jump down toward the nearest rival!
				self.bm_bot_roof_t = time + 2.2;
				prey = BM_BotPickHuntTarget ();
				if (prey != world && prey.origin_z + 70 < self.origin_z)
				{
					d = prey.origin - self.origin;
					d_z = 0;
					self.keys = (self.keys & 960) | frik_KeysForDir (d);
					d = normalize (d);
					traceline (self.origin + '0 0 18', self.origin + '0 0 18' + d * 64, TRUE, self);
					fl = trace_fraction;
					traceline (self.origin + '0 0 78', self.origin + '0 0 78' + d * 64, TRUE, self);
					if (fl < 1 && trace_fraction == 1)
					{
						if (!self.jp_on && self.jp_fuel >= 0.35)
						{
							Jetpack_On ();
							self.button2 = TRUE;
							self.bm_bot_jp_end = time + 0.55;
						}
						else
						{
							self.flags = self.flags - (self.flags & FL_ONGROUND);
							self.velocity = d * 280 + '0 0 340';
						}
					}
					else
						bot_jump ();
				}
			}
		}
	}
	else
		self.bm_bot_roof_t = 0;

	// Padre upper-suite west courtyard window sill hop (20u sill at x=-9636, y=-4862)
	if (BM_BotDowntown () && (self.flags & FL_ONGROUND) && self.origin_x >= -9655 && self.origin_x <= -9560
		&& self.origin_y >= -4950 && self.origin_y <= -4800 && self.origin_z > 480 && self.origin_z < 880)
	{
		bot_jump ();
	}

	// ---------------- 3. DOWNTOWN RIVAL HUNTING, PATROL & SUB-GRADE EXIT ----------------
	// Never let FrikBot's AI_WAIT or chat pause freeze a bot in place
	if (route_table != self && (self.b_aiflags & AI_WAIT))
		self.b_aiflags = self.b_aiflags - (self.b_aiflags & AI_WAIT);
	if (self.b_skill < 2 && self.b_chattime > time)
		self.b_chattime = time;

	// Suppress perpendicular wall-dodge inside Sandrini's narrow basement stairwell so bots walk straight up the steps
	if (BM_BotDowntown () && self.origin_x >= -4040 && self.origin_x <= -3660 && self.origin_y >= 240 && self.origin_y <= 360 && self.origin_z < 40)
		self.b_aiflags = self.b_aiflags - (self.b_aiflags & AI_OBSTRUCTED);

	// Alternate between patrolling spread-out waypoints and hunting non-crowded rivals so bots roam the whole map
	if (!self.enemy && (time >= self.bm_bot_hunt_t || (self.origin_z < -36 && self.target1 == world)))
	{
		self.bm_bot_hunt_t = time + 4.5 + random () * 3.5;
		if (self.target1 == world || (self.target1.classname != "item_jetpack" && random () < 0.55))
		{
			prey = world;
			if (self.origin_z >= -36 && random () < 0.45 && way_head != world)
				prey = BM_BotPickPatrolWay ();
			if (prey == world)
				prey = BM_BotPickHuntTarget ();
			if (prey == world && way_head != world)
				prey = BM_BotPickPatrolWay ();
			if (prey != world && !target_onstack (prey))
			{
				target_add (prey);
				bot_get_path (prey, TRUE);
			}
		}
	}

	// ---------------- 4. NEVER-IDLE CONTINUOUS ROAM & CURB / CAR / ALLEY UNSTUCK ----------------
	if (!self.enemy && !self.fd_head && !self.wc_charging && !self.dk_charging && self.ltg_phase != 1)
	{
		if (time < self.bm_bot_free_t || self.target1 == world || !(self.keys & 63))
		{
			if (time >= self.bm_bot_free_t || vlen (self.bm_bot_free_dir) < 0.5)
			{
				self.bm_bot_free_dir = BM_BotPickOpenDir (FALSE, TRUE, world);
				self.bm_bot_free_t = time + 0.95 + random () * 0.85;
				self.bm_bot_repick_t = time + 0.25;
			}
			else if (time >= self.bm_bot_repick_t)
			{
				self.bm_bot_repick_t = time + 0.25;
				// stairs / ramps / curbs blocked this flat probe every frame: re-scan only if the slope check fails too
				traceline (self.origin + '0 0 18', self.origin + '0 0 18' + self.bm_bot_free_dir * 84, TRUE, self);
				if (trace_fraction < 0.85 && !BM_BotSlopeOpen (self.bm_bot_free_dir))
				{
					self.bm_bot_free_dir = BM_BotPickOpenDir (TRUE, TRUE, world);
					self.bm_bot_free_t = time + 0.90 + random () * 0.70;
				}
			}
			self.b_angle_y = vectoyaw (self.bm_bot_free_dir);
			self.v_angle_y = self.b_angle_y;
			self.keys = (self.keys & 960) | frik_KeysForDir (self.bm_bot_free_dir);
		}
	}
	if (time >= self.bm_bot_stuck_t)
	{
		d = self.origin - self.bm_bot_stuck_org;
		d_z = 0;
		self.bm_bot_stuck_org = self.origin;
		self.bm_bot_stuck_t = time + 0.85;

		if (route_table != self
			&& !self.fd_head && !self.wc_charging && !self.dk_charging && self.ltg_phase != 1 && ((self.keys & 63) || !self.enemy) && vlen (d) < 28)
		{
			// Sub-grade basement failsafe: steer directly to Sandrini's stair foot / Eye St exit instead of wall rays
			if (BM_BotDowntown () && self.origin_z < -20 && self.origin_x >= -4080 && self.origin_x <= -3280
				&& self.origin_y >= 160 && self.origin_y <= 540)
			{
				if (self.origin_x > -3695 || self.origin_y < 262 || self.origin_y > 338)
					open_dir = '-3720 300 -106' - self.origin;
				else
					open_dir = '-4116 300 32' - self.origin;
				open_dir_z = 0;
				open_dir = normalize (open_dir);
			}
			else
			{
				prey = BM_BotPickHuntTarget ();
				open_dir = BM_BotPickOpenDir (TRUE, FALSE, prey);
			}
			self.target1 = world;
			self.target2 = world;
			self.target3 = world;
			self.target4 = world;
			self.current_way = world;
			self.b_aiflags = 0;
			self.bm_bot_hunt_t = time + 1.5;
			self.bm_bot_free_dir = open_dir;
			self.bm_bot_free_t = time + 1.30;
			if (!self.enemy)
			{
				self.b_angle_y = vectoyaw (open_dir);
				self.v_angle_y = self.b_angle_y;
			}
			self.keys = frik_KeysForDir (open_dir);
			if (self.flags & FL_ONGROUND)
			{
				if (self.origin_z >= -20)
					bot_jump ();
			}
			else if (!self.jp_on && self.jp_fuel >= 0.6 && self.origin_z >= -20)
			{
				Jetpack_On ();
				self.button2 = TRUE;
				self.bm_bot_jp_end = time + 0.7;
			}
		}
	}
};
