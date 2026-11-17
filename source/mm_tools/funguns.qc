void() FunGun_Precache =
{
	precache_model ("progs/v_pickle.md3");
	precache_sound ("fungun/fg_fork_hit.wav");
	precache_sound ("weapons/pkup.wav");
	precache_sound ("weapons/sgun1.wav");
	precache_sound ("weapons/r_exp3.wav");
	Pickle_Precache ();
	GreenJar_Precache ();
	Dookie_Precache ();
	RobHead_Precache ();
	NS_Precache ();
	WC_Precache ();
	M4_Precache ();
	Garand_Precache ();
	if (autocvar_bm_preload && deathmatch)
	{
		WC_PrecacheSprites ();
	}
};

// ---------------------------------------------------------------- tables

string(float g) FunGun_VModel =
{
	local entity p;

	if (g == FG_NETSEND)
		return "progs/v_netsend.md3";
	if (g == FG_WCANNON)
		return "progs/v_wewcannon.md3";
	if (g == FG_DOOKIE)
		return "progs/v_dookie.md3";
	if (g == FG_M4)
		return M4_VModel ();
	if (g == FG_GARAND)
		return Garand_VModel ();
	if (g == FG_PONG)
	{
		p = self;
		if (!(self.flags & FL_CLIENT) && self.owner)
			p = self.owner;
		if (FunGun_Ammo (p, FG_PONG) < 1 && !cvar ("gj_test") && p.gj_shaking <= 0 && p.gj_throw_at <= 0 && (!p.gj_threw_t || time >= p.gj_threw_t + GJ_FOLLOW_TIME))
			return "";
		return "progs/v_greenjar.md3";
	}
	if (g == FG_DOB)
	{
		p = self;
		if (!(self.flags & FL_CLIENT) && self.owner)
			p = self.owner;
		if (FunGun_Ammo (p, FG_DOB) < 1 && !(p.rh_charging > 0 && p.rh_charge_gun == FG_DOB) && !(p.rh_throw_at > 0 && p.rh_throw_gun == FG_DOB) && !(p.rh_threw_t > 0 && p.rh_throw_gun == FG_DOB && time < p.rh_threw_t + (RH_FOLLOW_TIME / RH_DRONE_ANIM_SPEED)))
			return "";
		return "progs/v_robhead_drone.md3";
	}
	// no pickle to throw: no hand (once any active throw + empty-claw follow-through has dropped off screen)
	p = self;
	if (!(self.flags & FL_CLIENT) && self.owner)
		p = self.owner;
	if (FunGun_Ammo (p, FG_PICKLE) < 1 && p.pk_throw_at <= 0 && (!p.pk_threw_t || time >= p.pk_threw_t + PK_FOLLOW_TIME))
		return "";
	return "progs/v_pickle.md3";
};

string(float g) FunGun_ShortName =
{
	if (g == FG_DOB)
		return "Rob Dob";
	if (g == FG_PONG)
		return "Jar o' Green Guys";
	if (g == FG_M4)
		return "M4A1";
	if (g == FG_GARAND)
		return "M1 Garand";
	if (g == FG_WCANNON)
		return "Wheelman Cannon";
	if (g == FG_DOOKIE)
		return "Dookie Bazooka";
	if (g == FG_NETSEND)
		return "NetSend";
	return "Pickle Surprise";
};

string(float g) FunGun_Name =
{
	if (g == FG_DOB)
		return "Rob Dob - steer head, fire to dash/detonate";
	if (g == FG_PONG)
		return "Jar o' Green Guys - hold fire to shake, release to swarm!";
	if (g == FG_M4)
		return "M4A1 - automatic rifle (R reloads)";
	if (g == FG_GARAND)
		return "M1 Garand - semi-auto rifle (R reloads)";
	if (g == FG_WCANNON)
		return "Wheelman Cannon - hold fire to charge";
	if (g == FG_DOOKIE)
		return "Dookie Bazooka - hold fire to wind up, release to blast!";
	if (g == FG_NETSEND)
		return "NetSend - throws a popup-spamming PC";
	return "Pickle Surprise - drop trap";
};

// obituary: victim + FunGun_Death1 + attacker + FunGun_Death2
string(float g) FunGun_Death1 =
{
	if (g == FG_DOB)
		return " got a big wet kiss from ";
	if (g == FG_PONG)
		return " was swarmed silly by ";
	if (g == FG_NETSEND)
		return " got a NET SEND from ";
	if (g == FG_DOOKIE)
		return " got splattered by ";
	if (g == FG_WCANNON)
		return " got rolled over by ";
	if (g == FG_M4)
		return " was lit up by ";
	if (g == FG_GARAND)
		return " was picked off by ";
	return " walked into ";
};

string(float g) FunGun_Death2 =
{
	if (g == FG_PICKLE)
		return "'s Pickle Surprise\n";
	if (g == FG_PONG)
		return "'s Jar o' Green Guys\n";
	if (g == FG_DOB)
		return "'s flying head\n";
	if (g == FG_NETSEND)
		return "'s NetSend PC\n";
	if (g == FG_DOOKIE)
		return "'s Dookie Bazooka\n";
	if (g == FG_WCANNON)
		return "'s Wheelman\n";
	if (g == FG_M4)
		return "'s M4\n";
	if (g == FG_GARAND)
		return "'s M1 Garand\n";
	return "\n";
};

float(float g) FunGun_Max =
{
	if (g == FG_DOB)
		return FG_DOB_MAX;
	if (g == FG_PONG)
		return FG_PONG_MAX;
	if (g == FG_NETSEND)
		return FG_NETSEND_MAX;
	if (g == FG_DOOKIE)
		return FG_DOOKIE_MAX;
	if (g == FG_WCANNON)
		return FG_WCANNON_MAX;
	if (g == FG_M4)
		return FG_M4_MAX;
	if (g == FG_TOMMY)
		return FG_TOMMY_MAX;
	if (g == FG_GARAND)
		return FG_GARAND_MAX;
	return FG_PICKLE_MAX;
};

float(float g) FunGun_RegenTime =
{
	if (g == FG_DOB)
		return FG_DOB_REGEN;
	if (g == FG_PONG)
		return FG_PONG_REGEN;
	if (g == FG_NETSEND)
		return FG_NETSEND_REGEN;
	if (g == FG_DOOKIE)
		return FG_DOOKIE_REGEN;
	if (g == FG_WCANNON)
		return FG_WCANNON_REGEN;
	if (g == FG_M4)
		return FG_M4_REGEN;
	if (g == FG_TOMMY)
		return FG_TOMMY_REGEN;
	if (g == FG_GARAND)
		return FG_GARAND_REGEN;
	return FG_PICKLE_REGEN;
};

float(entity p, float g) FunGun_Ammo =
{
	if (g == FG_DOB)
		return p.fg_ammo1;
	if (g == FG_PONG)
		return p.fg_ammo2;
	if (g == FG_NETSEND)
		return p.fg_ammo4;
	if (g == FG_DOOKIE)
		return p.fg_ammo5;
	if (g == FG_WCANNON)
		return p.fg_ammo6;
	if (g == FG_M4)
		return p.fg_ammo7;
	if (g == FG_TOMMY)
		return p.fg_ammo8;
	if (g == FG_GARAND)
		return p.fg_ammo9;
	return p.fg_ammo3;
};

void(entity p, float g, float v) FunGun_SetAmmo =
{
	if (g == FG_DOB)
		p.fg_ammo1 = v;
	else if (g == FG_PONG)
		p.fg_ammo2 = v;
	else if (g == FG_NETSEND)
		p.fg_ammo4 = v;
	else if (g == FG_DOOKIE)
		p.fg_ammo5 = v;
	else if (g == FG_WCANNON)
		p.fg_ammo6 = v;
	else if (g == FG_M4)
		p.fg_ammo7 = v;
	else if (g == FG_TOMMY)
		p.fg_ammo8 = v;
	else if (g == FG_GARAND)
		p.fg_ammo9 = v;
	else
		p.fg_ammo3 = v;
	if (p.weapon == IT_FUNGUN && p.fg_sel == g)
		p.currentammo = v;
};

float(entity p, float g) FunGun_RegenT =
{
	if (g == FG_DOB)
		return p.fg_regen1;
	if (g == FG_PONG)
		return p.fg_regen2;
	if (g == FG_NETSEND)
		return p.fg_regen4;
	if (g == FG_DOOKIE)
		return p.fg_regen5;
	if (g == FG_WCANNON)
		return p.fg_regen6;
	if (g == FG_M4)
		return p.fg_regen7;
	if (g == FG_TOMMY)
		return p.fg_regen8;
	if (g == FG_GARAND)
		return p.fg_regen9;
	return p.fg_regen3;
};

void(entity p, float g, float v) FunGun_SetRegenT =
{
	if (g == FG_DOB)
		p.fg_regen1 = v;
	else if (g == FG_PONG)
		p.fg_regen2 = v;
	else if (g == FG_NETSEND)
		p.fg_regen4 = v;
	else if (g == FG_DOOKIE)
		p.fg_regen5 = v;
	else if (g == FG_WCANNON)
		p.fg_regen6 = v;
	else if (g == FG_M4)
		p.fg_regen7 = v;
	else if (g == FG_TOMMY)
		p.fg_regen8 = v;
	else if (g == FG_GARAND)
		p.fg_regen9 = v;
	else
		p.fg_regen3 = v;
};

// pitch is a multiplier (1 = normal); Combat+ scales it with its slow-motion
void(entity e, float chan, string samp, float vol, float pitch) FG_Snd =
{
	sound7 (e, chan, samp, vol, ATTN_NORM, SNDSPD * pitch);
};

// a spot just in front of the player's eye, pulled back if that is inside a wall
vector(float dist) FG_Muzzle =
{
	traceline (self.origin + '0 0 16', self.origin + '0 0 16' + v_forward * dist - v_up * 4, TRUE, self);
	return trace_endpos - v_forward * 2;
};

// ---------------------------------------------------------------- the player side

// fire pressed with a fun gun out (called from W_Attack)
// a fun gun fired: the other fun guns wait, so one life can't dump every hazard at once (the gun itself keeps its own magazine)
void(float g) FunGun_Lock =
{
	self.fg_lock_gun = g;
	self.fg_lock_t = time + autocvar_bm_fg_lock;
	dprint (strcat ("fungun: fired ", ftos (g), " at ", ftos (time), "\n"));
};

void() FunGun_Attack =
{
	local float g, a, ct;

	g = self.fg_sel;
	if (g == FG_M4)
	{
		if (self.bm_rl_slot != BM_FG7 && FunGun_Ammo (self, FG_M4) < 1)
		{
			if (self.fg_dry_held)
			{
				self.attack_finished = time + 0.3;
				return;
			}
			self.fg_dry_held = TRUE;
		}
		else
			self.fg_dry_held = FALSE;
		M4_Press ();		// stand-alone automatic rifle: exempt from bm_fg_lock (m4.qc)
		return;
	}
	if (g == FG_GARAND)
	{
		Garand_Press ();	// stand-alone M1 Garand rifle: exempt from bm_fg_lock (garand.qc)
		return;
	}
	if (time < self.fg_lock_t && g != self.fg_lock_gun)
	{
		if (!self.fg_dry_held && time >= self.fg_lock_msg)
		{
			self.fg_lock_msg = time + 3;
			dprint (strcat ("fungun: locked ", ftos (g), " at ", ftos (time), "\n"));
			centerprint (self, strcat ("Fun guns locked: ", ftos (ceil (self.fg_lock_t - time)), " s\n"));
			sound7 (self, CHAN_WEAPON, "weapons/pkup.wav", 0.4, ATTN_NORM, SNDSPD);
		}
		self.fg_dry_held = TRUE;
		self.attack_finished = time + 0.3;
		return;
	}
	a = FunGun_Ammo (self, g);
	if (g == FG_PONG && a < 1 && cvar ("gj_test"))
		a = 1;		// gj_test: Jar o' Green Guys never runs dry during testing
	if (a < 1)
	{
		if (!self.fg_dry_held)
		{
			self.fg_dry_held = TRUE;
			if (g == FG_PONG)
				centerprint (self, "The jar is still recharging\n");
			if (g == FG_NETSEND)
				centerprint (self, "The disk is still reloading\n");
			if (g == FG_DOOKIE)
				centerprint (self, "The reactor is still refilling\n");
			if (g == FG_WCANNON)
				centerprint (self, "The cannon is still reloading\n");
			if (g == FG_DOB)
				centerprint (self, "The Rob Drone is still recharging\n");
			sound7 (self, CHAN_WEAPON, "weapons/pkup.wav", 0.4, ATTN_NORM, SNDSPD);
		}
		self.attack_finished = time + 0.3;
		return;
	}
	self.fg_dry_held = FALSE;
	if (g == FG_PONG)
	{
		GJ_Press ();		// holds fire to cocktail-shake; GJ_Frame hurls it on release (greenjar.qc)
		return;
	}
	if (g == FG_DOB)
	{
		RH_DronePress ();	// DJI remote launches steerable flying Rob head drone (robhead.qc / floathead.qc)
		return;
	}
	if (g == FG_DOOKIE)
	{
		DK_Press ();		// holds fire to wind up tabla reactor; DK_Frame launches on release (dookie.qc)
		return;
	}
	if (g == FG_WCANNON)
	{
		WC_Press ();		// holds fire to charge, WC_Frame launches it (wcannon.qc)
		return;
	}
	if (g == FG_NETSEND)
	{
		if (NS_Count (self) >= NS_MAX_PCS)		// FIFO cap: pop the oldest active PC to make room (netsend.qc)
			NS_MakeRoom (self);
		FunGun_SetAmmo (self, g, a - 1);
		FunGun_Lock (g);
		self.fg_fire_t = time;
		self.ns_fire_t = time;
		self.ns_throw_at = time + NS_THROW_DELAY;		// the hand lets go at frame 44 (FunGun_ViewFrame)
		FG_Snd (self, CHAN_VOICE, "netsend/wheres_disk.wav", 1, 1);		// "David! Where's the disk?"
		player_mm1 ();
		self.attack_finished = time + 1;
		return;
	}
	FunGun_SetAmmo (self, g, a - 1);
	FunGun_Lock (g);
	self.fg_fire_t = time;
	self.bm_lastshot = time + 0.7;		// keep bm_idle_reload from putting the gun away mid-throw (bm_reload.qc)
	player_mm1 ();		// the rocket firing pose
	self.pk_fire_t = time;
	self.pk_throw_at = time + PK_THROW_DELAY;		// brutal choke-windup + forward whip; Pk_Launch() fires as the claw snaps open
	self.punchangle_x = -2.8;				// upward head cock during brutal windup
	self.punchangle_z = 2.0;
	FG_Snd (self, CHAN_VOICE, "pickle/throw.wav", 1, 1);
	self.attack_finished = time + PK_THROW_DELAY + PK_FOLLOW_TIME + PK_RAISE_TIME;
};

// impulse FG_IMPULSE + g - 1
float(float g) FunGun_Bit =
{
	if (g == 1) return 1;
	if (g == 2) return 2;
	if (g == 3) return 4;
	if (g == 4) return 8;
	if (g == 5) return 16;
	if (g == 6) return 32;
	if (g == 7) return 64;
	if (g == 8) return 128;
	return 256;
};

float(float g) FunGun_Impulse =
{
	return FG_IMPULSE + g - 1;
};

float(float g) FunGun_Available =
{
	if (g == FG_TOMMY)
		return FALSE;		// slot 8 was the Thompson, removed 2026-11-16
	if (g == FG_M4)
		return m4_ok;
	if (g == FG_GARAND)
		return garand_ok;
	return (g >= 1 && g <= FG_COUNT);
};

void(float g) FunGun_Select =
{
	local float bit;

	self.impulse = 0;
	if (!FunGun_Available (g))
		return;
	if (self.has_fired == 1)
		return;
	if (self.weapon == IT_FUNGUN && self.fg_sel == g)
		return;
	self.idletimer = 1;		// weapon raise animation
	self.switchtimer = -5;
	self.weapon = IT_FUNGUN;
	self.fg_sel = g;
	W_SetCurrentAmmo ();
	bit = FunGun_Bit (g);
	if (!(self.fg_seen_mask & bit))
	{
		self.fg_seen_mask = self.fg_seen_mask | bit;
		centerprint (self, FunGun_Name (g));
	}
	else
		centerprint (self, FunGun_ShortName (g));
};

// gives a player every fun gun, full (spawn, impulse 9) and clears leftover shrinking
void(entity p) FunGun_Give =
{
	local float g, ct;

	g = 1;
	while (g <= FG_COUNT)
	{
		if (FunGun_Available (g) && FunGun_Ammo (p, g) < FunGun_Max (g))
			FunGun_SetAmmo (p, g, FunGun_Max (g));
		FunGun_SetRegenT (p, g, 0);
		g = g + 1;
	}
	p.fg_lock_t = 0;
	p.milk_freeze = 0;
	p.milk_slip = FALSE;
	p.ltg_shock = 0;
	p.disableclientprediction = 0;
	p.ns_throw_at = 0;		// a throw wound up in the last life must not fire in this one
	p.milky_wind = 0;
	if (p.fg_sel < 1 || p.fg_sel > FG_COUNT)
		p.fg_sel = 1 + floor (random () * FG_COUNT);
	if (p.fg_sel > FG_COUNT)
		p.fg_sel = FG_COUNT;
	// sprites must never be see-through: with r_lerpsprites on, the engine cross-fades sprite frames (the Wheelman looked ghostly)
	ct = clienttype (p);
	if (!FunGun_Available (p.fg_sel))
		p.fg_sel = FG_PICKLE;
	if (ct == FD_CLIENTTYPE_REAL)
	{
		stuffcmd (p, "r_lerpsprites 0\n");
		if (!p.bm_fx_sent)
		{
			p.bm_fx_sent = TRUE;
			stuffcmd (p, "exec zz_tone_fx.cfg\n");		// in zz_tone1.pk3: reloads the lighter effects over an older loose effectinfo.txt. No pack = \"couldn't exec\", no harm
		}
		stuffcmd (p, "cl_movement_track_canjump 0\n");		// hold-to-jump rebounds on the server: predict it, or every landing snaps online
	}
	p.scale = 1;
	p.wc_charging = 0;
	p.wc_cool = 0;
	p.pk_throw_at = 0;
	p.pk_threw_t = 0;
	p.pk_reload_t = 0;
	p.pk_empty = FALSE;
	GJ_ResetPlayer (p);
	DK_ResetPlayer (p);
	RH_ResetPlayer (p);
	p.m4_bloom = 0;
	p.m4_bloom_t = 0;
	p.m4_shot_n = 0;
	p.gar_ready = 1;
	p.gar_shootanim = 0;
	p.gar_empty_t = 0;
	FD_Reset (p);		// a new life starts with no head out
};

// bots (bot_weapon_switch): in deathmatch they spend most of their time with a random fun gun,
// so they are fun to be killed by. TRUE = keep this choice, skip the normal weapon pick.
float() FunGun_BotPick =
{
	if (!deathmatch)
		return FALSE;
	if (time >= self.fg_bot_until)
	{
		if (random () < 0.65)
		{
			self.fg_bot_fun = TRUE;
			self.fg_bot_until = time + 8 + random () * 10;
			self.impulse = FG_IMPULSE + 2;		// the pickle: not the Rob Dob
			return TRUE;
		}
		self.fg_bot_fun = FALSE;
		self.fg_bot_until = time + 5 + random () * 6;
		return FALSE;
	}
	if (self.fg_bot_fun)
	{
		if (self.fg_sel == FG_DOB)
			self.fg_sel = FG_PICKLE;
		if (self.weapon != IT_FUNGUN)
			self.impulse = FunGun_Impulse (self.fg_sel);
		return TRUE;
	}
	return FALSE;
};

// first fun gun visited when scrolling forward off the Banana (skips joke slots 1..6 unless bm_scroll_fun 1)
float() FunGun_First =
{
	local float n;

	n = FG_M4;
	if (autocvar_bm_scroll_fun)
		n = 1;
	while (n <= FG_COUNT)
	{
		if (FunGun_Available (n))
			return n;
		n = n + 1;
	}
	return 0;
};

// weapon cycling inside the fun-gun block; FALSE when it ran off the end
float() FunGun_CycleNext =
{
	local float n, min_g;

	min_g = FG_M4;
	if (autocvar_bm_scroll_fun)
		min_g = 1;
	n = self.fg_sel + 1;
	if (n < min_g)
		n = min_g;
	while (n <= FG_COUNT)
	{
		if (FunGun_Available (n))
		{
			self.fg_sel = n;
			return TRUE;
		}
		n = n + 1;
	}
	return FALSE;
};

// the last fun gun that can be selected (backwards cycling from the axe lands on it)
float() FunGun_Last =
{
	local float n, min_g;

	min_g = FG_M4;
	if (autocvar_bm_scroll_fun)
		min_g = 1;
	n = FG_COUNT;
	while (n >= min_g)
	{
		if (FunGun_Available (n))
			return n;
		n = n - 1;
	}
	return 0;
};

float() FunGun_CyclePrev =
{
	local float n, min_g;

	min_g = FG_M4;
	if (autocvar_bm_scroll_fun)
		min_g = 1;
	n = self.fg_sel - 1;
	while (n >= min_g)
	{
		if (FunGun_Available (n))
		{
			self.fg_sel = n;
			return TRUE;
		}
		n = n - 1;
	}
	return FALSE;
};

void(float g) FunGun_Regen =
{
	local float a, m, r, rt;

	a = FunGun_Ammo (self, g);
	m = FunGun_Max (g);
	r = FunGun_RegenT (self, g);
	if (a >= m)
	{
		if (r)
			FunGun_SetRegenT (self, g, 0);
		return;
	}
	rt = FunGun_RegenTime (g) * Underdog_AmmoRate (self);	// underdogs recharge faster
	if (!r)
	{
		FunGun_SetRegenT (self, g, time + rt);
		return;
	}
	if (time < r)
		return;
	while (time >= r && a < m)
	{
		a = a + 1;
		r = r + rt;
	}
	if (a >= m)
		r = 0;
	FunGun_SetAmmo (self, g, a);
	FunGun_SetRegenT (self, g, r);
};

// ---------------------------------------------------------------- the binoculars

float(entity p) Binoc_On =
{
	return p.bn_on;
};

// every frame from W_WeaponFrame: hold +button3 to look through the binoculars. The gun is put away (custom_effects.qc), you
// cannot shoot, the view zooms with DarkPlaces' viewzoom, the mouse wheel changes the magnification, and the range to whatever
// is under the cross-hairs is printed
void() Binoc_Frame =
{
	local vector eye;
	local string s;

	if (self.health <= 0 || !self.button3 || self.classname != "player")
	{
		if (self.bn_on)
		{
			self.bn_on = FALSE;
			self.viewzoom = 0;
			centerprint (self, "");
		}
		return;
	}
	if (!self.bn_on)
	{
		self.bn_on = TRUE;
		self.bn_zoom = BN_ZOOM_START;
		self.bn_msg = 0;
		sound7 (self, CHAN_ITEM, "weapons/pkup.wav", 0.5, ATTN_NORM, SNDSPD);
	}
	if (self.impulse == 10)		// wheel up: zoom in
	{
		self.impulse = 0;
		self.bn_zoom = self.bn_zoom * 1.35;
	}
	if (self.impulse == 12)		// wheel down: zoom out
	{
		self.impulse = 0;
		self.bn_zoom = self.bn_zoom / 1.35;
	}
	if (self.bn_zoom > BN_ZOOM_MAX)
		self.bn_zoom = BN_ZOOM_MAX;
	if (self.bn_zoom < BN_ZOOM_MIN)
		self.bn_zoom = BN_ZOOM_MIN;
	self.viewzoom = 1 / self.bn_zoom;
	if (self.attack_finished < time + 0.15)
		self.attack_finished = time + 0.15;		// both hands are on the binoculars
	if (time >= self.bn_msg)
	{
		self.bn_msg = time + 0.3;		// a centerprint is reliable traffic: 8 a second lagged slow connections
		makevectors (self.v_angle);
		eye = self.origin + self.view_ofs;
		traceline (eye, eye + v_forward * 8000, FALSE, self);
		s = strcat ("BINOCULARS x", ftos (floor (self.bn_zoom * 10 + 0.5) / 10));
		if (trace_fraction < 1)
			s = strcat (s, strcat ("\nRANGE ", ftos (floor (trace_fraction * 8000))));
		else
			s = strcat (s, "\nRANGE ---");
		if (trace_ent.classname == "player" || (trace_ent.flags & FL_MONSTER))
			s = strcat (s, strcat ("\n", trace_ent.netname));
		centerprint (self, s);
	}
};

// called every frame from W_WeaponFrame: recharge, dizzy stars, the view model's frame
// (v_<gun>.md3: 0-15 idle bob, 16-18 kick, 19 gone, 20-21 coming back up)
void() FunGun_ViewFrame =
{
	local float g, t, f, nt;

	if (self.ns_throw_at && time >= self.ns_throw_at)		// the NetSend disk leaves the hand (netsend.qc)
	{
		self.ns_throw_at = 0;
		NS_Throw ();
	}
	if (self.health <= 0)
		self.pk_throw_at = 0;
	if (self.pk_throw_at && time >= self.pk_throw_at)		// the Pickle Surprise rockets out of the open gauntlet (pickle.qc)
	{
		self.pk_throw_at = 0;
		self.pk_threw_t = time;
		Pk_Launch ();
	}
	Binoc_Frame ();		// hold the key: look through the binoculars
	WC_Frame ();		// the Wheelman Cannon charges and launches (wcannon.qc)
	GJ_Frame ();		// the Jar o' Green Guys cocktail-shakes and launches (greenjar.qc)
	DK_Frame ();		// the Dookie Bazooka winds up and blasts (dookie.qc)
	RH_Frame ();		// the Rob Head winds up and throws (robhead.qc)
	if (!self.button0)
		self.gar_ready = 1;		// semi-auto M1 Garand trigger reset
	g = 1;
	while (g <= FG_COUNT && !autocvar_bm_reload)	// with the LAN magazines on, bm_reload.qc reloads them
	{
		FunGun_Regen (g);
		g = g + 1;
	}

	if (self.weapon != IT_FUNGUN || self.meleeing == 1 || self.throwing == 1)
		return;
	g = self.fg_sel;
	t = time - self.fg_fire_t;
	f = floor (time * 10);
	f = f - 16 * floor (f / 16);		// idle
	if (g == FG_PICKLE || g == FG_PONG || g == FG_DOOKIE || g == FG_DOB)
	{
		f = 0;			// 1-frame card MD3s: their animation frames come from .skin shaders
		if (self.weaponmodel != FunGun_VModel (g))		// the hand goes when the last charge is thrown, and comes back with the next
			self.weaponmodel = FunGun_VModel (g);
	}
	else if (g == FG_NETSEND)
	{
		// v_netsend.md3: 0-39 the idle loop; 40-47 the throw (the disk leaves at 44); 48-53 follow-through, then the
		// empty hand while the disk is written again; 54-59 the new disk slides in
		if (FunGun_Ammo (self, g) < 1)
			self.ns_empty = TRUE;
		else if (self.ns_empty)
		{
			self.ns_empty = FALSE;
			self.ns_rl_t = time;
		}
		f = floor (time * 10);
		f = f - 40 * floor (f / 40);
		nt = time - self.ns_fire_t;
		if (nt < 1)
			f = min (53, 40 + floor (nt * 14));
		else if (FunGun_Ammo (self, g) < 1)
			f = 53;
		else if (time - self.ns_rl_t < 0.6)
			f = 54 + floor ((time - self.ns_rl_t) * 10);
	}
	else if (g == FG_M4)
	{
		f = M4_Anim ();		// v_m4.md3: CS idle / fire / reload / draw (m4.qc)
	}
	else if (g == FG_GARAND)
	{
		f = Garand_Anim ();	// v_garand.md3: DoD idle / shoot / shoote / reload / draw (garand.qc)
	}
	else if (g == FG_WCANNON)
	{
		// v_wewcannon.md3: 0-15 military idle sway; 16-25 sear cocking & +5.5 deg steel overpressure flex;
		// 26-29 side-brake jets & -6.3u barrel recoil; 30-39 hydropneumatic return-to-battery; 40-47 breech lock-in
		if (self.wc_charging)
		{
			nt = (time - self.wc_charging) / WC_CHARGE_TIME;
			if (nt > 1)
				nt = 1;
			f = min (25, 16 + floor (nt * 10));
		}
		else if (self.fg_fire_t && t < WC_COOLDOWN)
			f = min (47, 26 + floor ((t / WC_COOLDOWN) * 22));
	}
	else if (self.fg_fire_t && t < 0.15)
		f = 16 + floor (t * 20);
	self.weaponframe = f;
};

// PlayerDie: the frame hooks don't run once you are dead, so anything still playing or set stops here
void() FunGun_PlayerDie =
{
	DK_ResetPlayer (self);
	RH_ResetPlayer (self);
	if (self.wc_charging)
	{
		self.wc_charging = 0;
		sound (self, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);		// the charge whine
	}
	Jetpack_Off ();		// cuts the swoosh
	self.disableclientprediction = 0;
	if (self.bn_on)
	{
		// Binoc_Frame no longer runs while dead: the death cam stayed zoomed in with the BINOCULARS text up
		self.bn_on = FALSE;
		self.viewzoom = 0;
		centerprint (self, "");
	}
};
