#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
MATCH RULES (Bakersfield LAN rules, Combat+ only)

	spawn protection	bm_spawnprot seconds after every deathmatch spawn: no damage (knockback still pushes
						you), see-through shimmer; firing ends it early
	self-damage			bm_selfdamage x (after knockback, so rocket and grenade jumps keep their push)
	kill command		just kills you; like every suicide, lava bath and fall it costs no frags (client.qc)
	map playlist		bm_maplist "e2m1 dm6 aerowalk ..."; the map after the current one, wrapping round
	intermission		moves on by itself after bm_intermission seconds
	bot fill			bm_botfill N keeps FrikBots joining until there are N players, and drops them again
						as people join
	HUD stats			addstat 52-61 for csprogs.dat (magazine, reload, protection, regen, leader)
================
*/

.float bm_st_menubg;
float bm_menubg_active;

float() BM_IsMenuBg =
{
	if (deathmatch || coop || CTF_ENABLED || max_clients > 1 || cvar ("maxplayers") > 1)
		return FALSE;
	return (cvar ("bm_menu_bg") > 0);
};

void() BM_Precache =
{
	local entity bgspot;

	registercvar ("bm_menu_bg", "0");
	registercvar ("bm_obs_key", "");
	registercvar ("bm_obs_qualify_sec", "15");
	bm_obs_qualify_t = 0;
	bm_obs_targ = world;
	bm_obs_cam_init = 0;
	bm_obs_frame_t = 0;
	bm_obs_switch_t = 0;
	bm_obs_force_t = 0;
	bm_obs_death_t = 0;
	if (cvar ("bm_menu_bg") > 0 && (deathmatch || coop || CTF_ENABLED || max_clients > 1 || cvar ("maxplayers") > 1))
		cvar_set ("bm_menu_bg", "0");
	bm_menubg_active = BM_IsMenuBg ();
	if (bm_menubg_active)
	{
		bgspot = spawn ();
		bgspot.classname = "info_player_start";
		setorigin (bgspot, '0 0 64');
	}
	precache_sound ("weapons/lock4.wav");
	precache_sound ("weapons/pkup.wav");
	precache_sound ("misc/talk.wav");
	precache_sound ("items/damage.wav");
	precache_sound ("jetpack/swoosh.wav");
	precache_model ("progs/aura.md3");
	precache_model ("progs/quaddama.mdl");
	// a map with sky pads raised sv_maxvelocity (SkyPad_RaiseMaxVel); the next map gets the value from before that back
	registercvar ("bm_maxvel_saved", "0");
	if (cvar ("bm_maxvel_saved") > 0)
	{
		cvar_set ("sv_maxvelocity", cvar_string ("bm_maxvel_saved"));
		cvar_set ("bm_maxvel_saved", "0");
	}
	// Unconditionally precache jetpack, newbie, and announcer clips in worldspawn so bots on maps without
	// item_jetpack/item_armor2 (e.g. terminal21, ooika_lawrenceville) and mid-map cvar toggles never precache post-spawn
	Jetpack_Precache ();
	precache_sound ("funny/newbie.wav");
	BM_Fun_Precache ();
	// Lazy sprite loading: David, Daniel, GreenSuit, RobeGuy and the crowd are about 1 GB of 32-bit sprites. Each of them
	// precaches itself where it is used (summon impulses, map entities, npc_crowd), so a map that never shows them no longer
	// loads them. Only the fox crowd is spawned by code after load, so fox still loads its crowd here.
	// The random NPCs, the Eric cannon (and its LAN props), the Mega Man tank and the sky pads are map-placed or summoned by
	// test impulses, and each of them precaches itself in its own init (RandomNPC_InitCommon, EC_InitMonument, Lan_InitProp,
	// MMT_InitTank, the sky pad spawn function). Loading all of them here cost every map about 70 models and 170 MB of
	// textures it never showed (2026-11-18 load audit), so a map that places none of them no longer loads them.
	if (world.model == "maps/fox.bsp")
		Crowd_Precache ();
	Soi6_Precache ();
	JohnBird_Precache ();
	RocketRider_Precache ();
	precache_sound ("items/r_item1.wav");	// skeet reward sound (proj_collide.qc); maps without health items never precached it
};

// T_Damage, after Underdog_Damage: returns the damage to apply; bm_kb keeps the full push
float(entity targ, entity inflictor, entity attacker, float damage) BM_Damage =
{
	bm_kb = damage;
	bm_blocked = FALSE;
	if (targ.classname != "player")
	{
		targ.bm_last_hit_dmg = damage;
		targ.bm_last_hit_explosive = FALSE;
		if (inflictor != world)
		{
			if (inflictor.classname == "missile" || inflictor.classname == "grenade"
				|| inflictor.classname == "proximity_grenade" || inflictor.classname == "misc_explobox"
				|| inflictor.classname == "jimrocket" || inflictor.classname == "resistexp"
				|| inflictor.deathtype == "exploding"
				|| inflictor.classname == "bigbanana" || inflictor.classname == "minibanana"
				|| inflictor.classname == "mmtire" || inflictor.classname == "mmrubber"
				|| inflictor.classname == "wc_dancer" || inflictor.classname == "wc_shot"
				|| inflictor.classname == "milky" || inflictor.classname == "jwwave"
				|| inflictor.classname == "veh_blast_inflictor" || inflictor.classname == "lan_blast_inflictor"
				|| inflictor.classname == "eric_cannon_blast"
				|| inflictor.classname == "mm_tank_bar" || inflictor.classname == "mm_tank_blast"
				|| (inflictor.classname == "building_sentrygun" && inflictor.health <= 0)
				|| inflictor.classname == "misc_vehicle_johnbird" || inflictor.classname == "misc_vehicle_rocketrider" || inflictor.veh_kind > 0)
			{
				targ.bm_last_hit_explosive = TRUE;
			}
		}
		return damage;
	}
	if (targ.bm_prot_t > time && damage < 1000)		// telefrags still go through
	{
		bm_blocked = TRUE;
		return 0;
	}
	if (attacker == targ && inflictor.classname != "eric_cannon_blast")
	{
		damage = damage * autocvar_bm_selfdamage;
		if (inflictor.classname == "missile")		// your own rocket: a further cut on top
			damage = damage * autocvar_bm_rocketself;
	}
	else if (attacker.classname == "player" && attacker.ishuman != 1 && autocvar_bm_bot_dmg > 0)
		damage = damage * autocvar_bm_bot_dmg;
	return damage;
};

// NPCs only gib when killed by rockets / explosions / vehicles or heavy high-damage hits (>= 75)
float(entity e) NPC_ShouldGib =
{
	if (e.bm_last_hit_explosive)
		return TRUE;
	if (e.bm_last_hit_dmg >= 75)
		return TRUE;
	return FALSE;
};

// end of PutClientInServer
void() BM_PlayerSpawned =
{
	local entity dmspot;

	if (BM_IsMenuBg ())
	{
		self.bm_prot_t = 0;
		self.rg_hurt_t = 0;
		self.bm_st_menubg = 900;
		self.solid = SOLID_NOT;
		self.movetype = MOVETYPE_NONE;
		self.takedamage = DAMAGE_NO;
		self.modelindex = 0;
		self.weaponmodel = "";
		self.weaponframe = 0;
		self.items = 0;
		self.flags = self.flags | FL_NOTARGET;
		dmspot = find (world, classname, "info_player_deathmatch");
		if (dmspot)
			setorigin (self, dmspot.origin);
		if (self.ishuman == 1)
			stuffcmd (self, "v_glslgamma_2d 1\ncd stop\n");
		return;
	}
	self.bm_st_menubg = 0;
	if (deathmatch && autocvar_bm_spawnprot > 0)
		self.bm_prot_t = time + autocvar_bm_spawnprot;
	else
		self.bm_prot_t = 0;
	self.rg_hurt_t = 0;
	if (autocvar_bm_debug)
	{
		bprint ("ud spawn ", self.netname, " human ", ftos (self.ishuman == 1), " streak ", ftos (self.ud_streak), "/", ftos (self.ud_full));
		bprint (" k ", ftos (self.ud_kills), " d ", ftos (self.ud_deaths), " frags ", ftos (self.frags), " boost ", ftos (self.ud_boost));
		bprint (" hp ", ftos (self.health), " ar ", ftos (self.armorvalue), " at ", ftos (self.armortype));
		bprint (" quad ", ftos (max (0, self.super_damage_finished - time)), " pent ", ftos (max (0, self.invincible_finished - time)));
		bprint (" invis ", ftos (max (0, self.invisible_finished - time)), " shell ", ftos (self.ud_blueshell), "\n");
	}
	if (self.ishuman == 1)
	{
		stuffcmd (self, "alias vote \"cmd vote $*\"\nv_glslgamma_2d 1\n");	// map votes + apply GLSL gamma to 2D Quake HUD in windowed mode
		if (skypad_present && !self.skypad_vel_sent)		// only on maps with sky pads, once per connect (it went out on every spawn of every map: on a listen server that left the host's own sv_maxvelocity at 6500 for good)
		{
			self.skypad_vel_sent = TRUE;
			stuffcmd (self, "sv_maxvelocity 6500\n");
		}
	}
	else
		BM_BotSpawnLoadout ();
};

// Underdog_Spawn, first thing: every deathmatch life starts with green armor (bm_spawnarmor), before the
// catch-up code decides whether someone far behind gets yellow or red instead
void() BM_SpawnArmor =
{
	if (!deathmatch || autocvar_bm_spawnarmor <= 0)
		return;
	self.items = self.items - (self.items & (IT_ARMOR1 | IT_ARMOR2 | IT_ARMOR3));
	self.items = self.items | IT_ARMOR1;
	self.armortype = 0.3;
	self.armorvalue = autocvar_bm_spawnarmor;
};

// the bubble: follows its player (BM_LifeFrame moves it every frame), goes when the protection does or the player dies
void() BM_AuraThink =
{
	if (self.owner.bm_aura != self || self.owner.health <= 0 || !self.owner.bm_prot_t)
	{
		if (self.owner.bm_aura == self)
			self.owner.bm_aura = world;		// else BM_AuraFrame keeps writing to a freed (later reused) edict
		remove (self);
		return;
	}
	self.nextthink = time + 0.1;
};

void() BM_AuraFrame =
{
	local entity a;
	local float sn;

	a = self.bm_aura;
	if (a && (a.classname != "bm_aura" || a.owner != self))
		a = world;		// stale: the edict was freed (and maybe reused) behind our back
	if (!self.bm_prot_t || self.health <= 0)
	{
		if (a)
			remove (a);
		self.bm_aura = world;
		return;
	}
	if (!a)
	{
		a = spawn ();
		a.classname = "bm_aura";
		a.owner = self;
		a.movetype = MOVETYPE_NONE;
		a.solid = SOLID_NOT;
		a.exteriormodeltoclient = self;	// from the inside it is just a blinding wall: others (and your chase view) see it
		a.think = BM_AuraThink;
		a.nextthink = time + 0.1;
		setmodel (a, "progs/aura.md3");
		self.bm_aura = a;
	}
	sn = sin (time * 9);		// sin is a __variant in Combat+'s defs
	a.scale = 1 + 0.05 * sn;
	a.angles_y = time * 50;
	setorigin (a, self.origin);
};

// every frame, top of W_WeaponFrame, after BM_Frame
void() BM_LifeFrame =
{
	local float tmask;
	local vector gdir;

	if (self.bm_obs)
		return;
	if (BM_IsMenuBg ())
	{
		self.bm_st_menubg = 900;
		self.solid = SOLID_NOT;
		self.movetype = MOVETYPE_NONE;
		self.takedamage = DAMAGE_NO;
		self.modelindex = 0;
		self.weaponmodel = "";
		self.weaponframe = 0;
		self.flags = self.flags | FL_NOTARGET;
		return;
	}
	self.bm_st_menubg = 0;
	if (self.bm_prot_t)
	{
		if (time < self.bm_prot_t - autocvar_bm_spawnprot + autocvar_bm_spawnpause)
			self.button0 = 0;		// just spawned: a brief pause before the trigger works
		if (time >= self.bm_prot_t || (self.button0 && time > self.bm_prot_t - autocvar_bm_spawnprot + 0.3))
			self.bm_prot_t = 0;
	}
	if (world.model == "maps/morrorock.bsp" && self.movetype == MOVETYPE_WALK && self.health > 0
		&& (self.waterlevel >= 2 || self.origin_z < -10) && time >= self.mr_geyser_t)
	{
		self.mr_geyser_t = time + 2.5;
		self.skypad_safe_t = time + 7;
		gdir = '-2441 4331 0' - self.origin;
		gdir_z = 0;
		if (vlen (gdir) > 1)
			gdir = normalize (gdir);
		else
			gdir = '0 1 0';
		self.flags = self.flags - (self.flags & FL_ONGROUND);
		self.velocity = gdir * 980 + '0 0 860';
		sound (self, CHAN_AUTO, "jetpack/swoosh.wav", 1, ATTN_NORM);
		if (self.ishuman == 1)
			centerprint (self, "^5PACIFIC GEYSER BOOST!");
	}
	BM_AuraFrame ();
	Underdog_FxFrame ();

	if (self.ishuman != 1)
		return;
	if (self.bm_prot_t)
		self.bm_st_prot = ceil ((self.bm_prot_t - time) * 10);
	else
		self.bm_st_prot = 0;

	self.bm_st_regen = (self.health > 0 && self.health < self.max_health && time > self.rg_hurt_t + Underdog_RegenDelay ());
	self.bm_st_warmup = (autocvar_bm_warmup != 0);
	self.bm_st_heat = floor (self.ud_heat);
	self.bm_st_boost = floor (self.ud_boost * 100);
	if (ud_leader)
	{
		self.bm_st_leader = ud_leader.netname;
		self.bm_st_lheat = floor (ud_leader.ud_heat);
		self.bm_st_lshow = (ud_leader.ud_tier >= 3 && ud_leader != self && ud_leader.health > 0 && Underdog_PulseOn ());
		self.bm_st_lx = ud_leader.origin_x;
		self.bm_st_ly = ud_leader.origin_y;
		self.bm_st_lz = ud_leader.origin_z;
	}
	else
	{
		self.bm_st_leader = "";
		self.bm_st_lheat = 0;
		self.bm_st_lshow = 0;
	}

	self.bm_st_botmask = bm_botmask_cache;
	self.bm_st_playermask = bm_playermask_cache;
	self.bm_st_botcnt = bot_count;

	tmask = 0;
	if (self.fg_ammo1 >= 1 && self.bm_rl_slot != BM_FG1)		tmask = tmask | 1;
	if (self.fg_ammo2 >= 1 && self.bm_rl_slot != BM_FG2)		tmask = tmask | 2;
	if (self.fg_ammo3 >= 1 && self.bm_rl_slot != BM_FG3)		tmask = tmask | 4;
	if (self.fg_ammo4 >= 1 && self.bm_rl_slot != BM_FG4)		tmask = tmask | 8;
	if (self.fg_ammo5 >= 1 && self.bm_rl_slot != BM_FG5)		tmask = tmask | 16;
	if (self.fg_ammo6 >= 1 && self.bm_rl_slot != BM_FG6)		tmask = tmask | 32;
	if (time >= self.jb_cooldown_t)								tmask = tmask | 64;
	if (self.ud_blueshell)										tmask = tmask | 128;
	if (self.veh_van != world || self.veh_ride != world || RocketRider_Flying (self))		tmask = tmask | 256;
	if (Veh_Driving (self) || RocketRider_Flying (self))									tmask = tmask | 512;
	self.bm_st_toymask = tmask;
	self.bm_st_toycd = max (0, ceil (self.jb_cooldown_t - time));

	if (self.fd_head != world)
	{
		if (self.fd_head.fd_charging)
			self.fd_st_mode = 2;
		else
			self.fd_st_mode = 1;
		if (self.fd_head.fd_end > 0)
			self.fd_st_timer = max (0, ceil ((self.fd_head.fd_end - time) * 10));
		else
			self.fd_st_timer = 999;
		self.fd_st_speed = floor (vlen (self.fd_head.velocity));
		self.fd_st_arm = (time > self.fd_head.fd_arm);
	}
	else if (self.fd_fade > time)
	{
		self.fd_st_mode = 3;
		self.fd_st_timer = 0;
		self.fd_st_speed = 0;
		self.fd_st_arm = 0;
	}
	else
	{
		self.fd_st_mode = 0;
		self.fd_st_timer = 0;
		self.fd_st_speed = 0;
		self.fd_st_arm = 0;
	}
};

// SelectSpawnPoint (client.qc) asks first. Keeps 4-8 friends clustered around the active combat centroid
// in the 1,200-3,600u sweet spot while avoiding line-of-sight out to 4,200u and never exiling anyone to empty corners.
entity() BM_PickSpawn =
{
	local entity spot, p, best;
	local float dmin, d, dcen, score, bestscore, seen, n;
	local vector cen;

	if (!deathmatch)
		return world;
	if (self.ishuman != 1)
		return BM_BotPickSpawn ();
	if (autocvar_bm_spawnnear <= 0)
		return world;

	cen = '0 0 0';
	n = 0;
	p = bm_player_head;
	while (p)
	{
		if (p != self && p.health > 0)
		{
			cen = cen + p.origin;
			n = n + 1;
		}
		p = p.bm_player_next;
	}
	if (n > 0)
		cen = cen * (1 / n);

	best = world;
	bestscore = 1000000;
	spot = find (world, classname, "info_player_deathmatch");
	while (spot)
	{
		p = findradius (spot.origin, 36);
		while (p && p.classname != "player")
			p = p.chain;
		if (!p)
		{
			dmin = 99999;
			seen = 0;
			p = bm_player_head;
			while (p)
			{
				if (p != self && p.health > 0)
				{
					d = vlen (p.origin - spot.origin);
					if (d < dmin)
						dmin = d;
					if (d < 4200 && !seen)
					{
						traceline (spot.origin + '0 0 28', p.origin + '0 0 28', TRUE, spot);
						if (trace_fraction == 1)
							seen = 1;
					}
				}
				p = p.bm_player_next;
			}
			if (n == 0 || dmin == 99999)
				score = random () * 1000;
			else
			{
				dcen = vlen (spot.origin - cen);
				if (dmin < autocvar_bm_spawnnear)
					score = 4500 + seen * 5000 + (autocvar_bm_spawnnear - dmin) * 6 + random () * 400;
				else
				{
					score = fabs (dcen - 2100) * 0.65 + seen * 5500 + random () * 950;
					if (dmin > 3400)
						score = score + (dmin - 3400) * 1.4;
					if (dcen > 3800)
						score = score + (dcen - 3800) * 1.8;
				}
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

// TRUE when maps/<m>.bsp can be opened (loose or in a pk3)
float(string m) BM_MapExists =
{
	local float fh;

	if (m == "")
		return FALSE;
	fh = fopen (strcat ("maps/", m, ".bsp"), 0);
	if (fh < 0)
		return FALSE;
	fclose (fh);
	return TRUE;
};

// NextLevel: TRUE = handled (the playlist picked the next map)
float() BM_NextLevel =
{
	local float n, i, found, tries;
	local string s, pick;
	local entity o;

	if (!deathmatch)
		return FALSE;
	s = cvar_string ("bm_maplist");
	if (s == "")
		return FALSE;
	n = tokenize (s);
	if (n < 1)
		return FALSE;
	found = -1;
	i = 0;
	while (i < n)
	{
		if (argv (i) == mapname)
			found = i;
		i = i + 1;
	}
	// skip playlist entries that are not shipped (changelevel to a missing map stalls at intermission);
	// if none of them exists, replay the current map
	pick = mapname;
	tries = 0;
	i = found;
	while (tries < n)
	{
		i = i + 1;
		if (i >= n)
			i = 0;
		if (BM_MapExists (argv (i)))
		{
			pick = argv (i);
			break;
		}
		dprint ("bm_maplist: skipping missing map ", argv (i), "\n");
		tries = tries + 1;
	}
	if (bm_nextmap)
		strunzone (bm_nextmap);
	bm_nextmap = strzone (pick);

	o = spawn ();
	o.map = bm_nextmap;
	nextmap = bm_nextmap;
	gameover = TRUE;
	o.think = execute_changelevel;
	o.nextthink = time + 0.1;
	bprint ("Next map: ", bm_nextmap, "\n");
	return TRUE;
};

// IntermissionThink: TRUE = moved on
float() BM_IntermissionThink =
{
	if (!deathmatch || autocvar_bm_intermission <= 0)
		return FALSE;
	if (!bm_inter_t)
		bm_inter_t = time + autocvar_bm_intermission;
	if (time < bm_inter_t)
		return FALSE;
	ExitIntermission ();
	return TRUE;
};

// worldspawn, after the stock clientstat list
void() BM_Stats =
{
	clientstat (52, 2, bm_st_mag);
	clientstat (53, 2, bm_st_magmax);
	clientstat (54, 2, bm_st_reload);
	clientstat (55, 2, bm_st_prot);
	clientstat (56, 2, bm_st_heat);
	clientstat (57, 2, bm_st_boost);
	clientstat (58, 2, bm_st_regen);
	clientstat (59, 2, bm_st_warmup);
	clientstat (60, 2, bm_st_lheat);
	clientstat (72, 1, bm_st_leader);		// a string stat takes 4 slots (72-75): on 61 it ran into the coordinates on 62-64
	clientstat (62, 2, bm_st_lx);
	clientstat (63, 2, bm_st_ly);
	clientstat (64, 2, bm_st_lz);
	clientstat (65, 2, bm_st_lshow);
	clientstat (66, 2, jp_st_fuel);		// the jetpack's glass fuel tank (jetpack.qc, csqc/bm_hud.qc)
	clientstat (67, 2, jp_st_max);
	clientstat (68, 2, milk_st);		// milk on the screen after a Pink Lady burst (milky.qc, csqc/bm_hud.qc)
	clientstat (71, 2, bm_st_slot);		// held weapon slot (16 = M4A1, csqc/bm_hud.qc)
	clientstat (76, 2, bm_st_botmask);	// bitmask of live bot slots 0..15 (csqc/bm_hud.qc)
	clientstat (77, 2, bm_st_botcnt);	// active bot count (csqc/bm_hud.qc)
	clientstat (78, 2, bm_st_toymask);	// bitmask of ready fun-gun superweapons & Winged John (csqc/bm_hud.qc)
	clientstat (79, 2, bm_st_toycd);	// Winged John cooldown seconds remaining (csqc/bm_hud.qc)
	clientstat (80, 2, bm_st_playermask);	// bitmask of live visible human slots 0..15 (csqc/bm_hud.qc)
	clientstat (69, 2, bm_st_menubg);	// 900 during silent menu-background map (csqc/bm_hud.qc)
	clientstat (81, 2, fd_st_mode);		// Rob Dob X-Ray HUD mode (csqc/robhead_xray.qc)
	clientstat (82, 2, fd_st_timer);		// Rob Dob flight timer tenths (csqc/robhead_xray.qc)
	clientstat (83, 2, fd_st_speed);		// Rob Dob speed u/s (csqc/robhead_xray.qc)
	clientstat (84, 2, fd_st_arm);		// Rob Dob dash armed (csqc/robhead_xray.qc)
	clientstat (85, 2, fd_st_seq);		// Rob Dob terminal sequence 1..14 (csqc/robhead_xray.qc)
	clientstat (86, 2, mmt_st_active);	// Mega Man Tank aiming line active (0=off, 1=ready, 2=reloading)
	clientstat (87, 2, mmt_st_sx);
	clientstat (88, 2, mmt_st_sy);
	clientstat (89, 2, mmt_st_sz);
	clientstat (90, 2, mmt_st_ex);
	clientstat (91, 2, mmt_st_ey);
	clientstat (92, 2, mmt_st_ez);
	clientstat (93, 2, jb_st_active);		// Winged John: 0=off, 1=3rd-person, 2=1st-person
	clientstat (94, 2, jb_st_variant);		// Winged John combat variant 1..3
	clientstat (95, 2, jb_st_combat);		// Winged John combat flags (1=combat, 2=M1, 4=M3/R, 16=Shift boost)
	clientstat (96, 2, jb_st_status);		// Winged John / player status (1=slowed, 2=burning, 4=low HP <=200)
	clientstat (97, 2, jb_st_boost);		// Winged John boost gauge 0..100
	clientstat (98, 2, jb_st_hp);			// Winged John HP 0..500
	clientstat (99, 2, jb_st_hit);			// Winged John hit-confirm counter
	clientstat (100, 2, jb_st_ammo);		// Winged John hairspray cans remaining 0..JB_MAX_AMMO
	clientstat (101, 2, jb_st_ammoprog);	// Winged John next-can restock progress 0..100
	clientstat (102, 2, jb_st_speed);		// Winged John airspeed u/s
	clientstat (103, 2, ky_st_mode);		// Pocket Kyle HUD: 0=off, 1=windup, 2=locking bird, 3=locked, 4=bird too far
	clientstat (104, 2, ky_st_prog);		// Pocket Kyle HUD: 0..100 charge or lock progress
	clientstat (105, 2, ky_st_dist);		// Pocket Kyle HUD: distance to bird/sky vehicle in units
	clientstat (106, 2, ky_st_tx);			// Pocket Kyle HUD: targeted bird world X
	clientstat (107, 2, ky_st_ty);			// Pocket Kyle HUD: targeted bird world Y
	clientstat (108, 2, ky_st_tz);			// Pocket Kyle HUD: targeted bird world Z
	clientstat (109, 2, gk_st_mode);		// Go-Kart rocket HUD: 0=off, 1=charging, 2=armed, 3=low nitro, 4=reloading
	clientstat (110, 2, gk_st_prog);		// Go-Kart rocket HUD: 0..100 progress
	clientstat (111, 2, gk_st_nitro);		// Go-Kart rocket HUD: 0..100 current nitro
	clientstat (112, 2, dn3_st_frame);		// DN3DooM Pump Shotgun CSQC 2D sprite frame + flags
	clientstat (113, 2, dn3_st_speed);		// DN3DooM Pump Shotgun horizontal speed for walk bob
	clientstat (114, 2, fl_st_black);		// ForeLoco screen blackout alpha 0..100
	clientstat (115, 2, fl_st_mode);		// ForeLoco phase: 0=off, 1=drinking, 2=blackout, 3=hospital bed
	clientstat (116, 2, fl_st_rem);			// ForeLoco remaining time in tenths of a second
	clientstat (117, 2, fl_st_speed);		// ForeLoco hospital bed speed u/s
	clientstat (118, 2, fl_st_flags);		// ForeLoco invuln/orbit/boost flags + ram KO count
	clientstat (119, 2, fl_st_anim);		// ForeLoco 2D sprite viewmodel frame (1..16)
};

float() BM_CountPlayers =
{
	local entity e;
	local float n;

	n = 0;
	e = bm_player_head;
	while (e)
	{
		n = n + 1;
		e = e.bm_player_next;
	}
	return n;
};

// bm_debug 1: one line per player every 2 s on the server console
void() BM_DebugPrint =
{
	local entity e, os;
	local float s;

	os = self;
	e = find (world, classname, "player");
	while (e)
	{
		self = e;
		s = BM_SlotOf (e);
		bprint (etos (e), " ", e.netname, ": slot ", ftos (s));
		bprint (" mag ", ftos (BM_GetMag (e, s)), "/", ftos (BM_MagSize (s)));
		bprint (" rl ", ftos (e.bm_rl_slot), " hp ", ftos (e.health), "/", ftos (e.max_health), " ar ", ftos (e.armorvalue));
		bprint (" frags ", ftos (e.frags), " heat ", ftos (e.ud_heat), " boost ", ftos (e.ud_boost), " tier ", ftos (e.ud_tier));
		bprint (" streak ", ftos (e.ud_streak), "/", ftos (e.ud_full), " k ", ftos (e.ud_kills), " d ", ftos (e.ud_deaths));
		bprint (" glow ", ftos (e.ud_aura.glow_size), " prot ", ftos (e.bm_prot_t > time), "\n");
		e = find (e, classname, "player");
	}
	self = os;
};

// The Test Box map (maps/testbox.bsp) is for trying guns on bots: there every bot is a target dummy. It walks round and round
// in a small circle (forward + turning, half of them one way, half the other), never looks at anybody and never fires, so
// it can not hurt you or anybody else. And at least 4 players are kept in the match, bots filling up.
float() BM_DummyMap =
{
	return world.model == "maps/testbox.bsp";
};

// BotAI (frikbot.bot_ai.qc) asks first; self = a living bot. TRUE = it has been steered, skip the real AI
float() BM_DummyBot =
{
	local float dir, k;

	if (!BM_DummyMap () && !(practice_active && !practice_live_fire))
		return FALSE;
	self.button0 = 0;
	self.button2 = 0;
	self.enemy = world;
	self.b_aiflags = 0;
	dir = 1;
	k = num_for_edict (self);
	if (k - 2 * floor (k / 2) == 1)			// odd bots turn the other way
		dir = -1;
	if (self.b_skill == 2)
	{
		self.b_angle_y = self.v_angle_y + 45 * dir;		// the mouse-emulating bots chase this angle
		self.b_angle_x = 0;
		self.keys = KEY_MOVEFORWARD;
	}
	else if (dir > 0)
		self.keys = KEY_MOVEFORWARD | KEY_LOOKLEFT;
	else
		self.keys = KEY_MOVEFORWARD | KEY_LOOKRIGHT;
	return TRUE;
};

// ---------------------------------------------------------------- map votes
// "vote map fox" (in chat or the console) opens a vote for a map listed in bm_votemaps; everybody then
// answers "vote yes" / "vote no" (console) or the F5 / F6 keys that the server binds when a vote starts.
// Passes when more than half of the humans say yes, fails when half say no, at the timeout yes beats no.

void() BM_VoteCount =
{
	local entity e;

	bm_v_n = 0;
	bm_v_yes = 0;
	bm_v_no = 0;
	e = find (world, classname, "player");
	while (e)
	{
		if (e.ishuman == 1)
		{
			bm_v_n = bm_v_n + 1;
			if (e.bm_voted == 1)
				bm_v_yes = bm_v_yes + 1;
			else if (e.bm_voted == 2)
				bm_v_no = bm_v_no + 1;
		}
		e = find (e, classname, "player");
	}
};

void(float pass) BM_VoteEnd =
{
	bm_vote_on = FALSE;
	if (pass)
	{
		bprint ("Vote passed (", ftos (bm_v_yes), " yes, ", ftos (bm_v_no), " no): changing map to ", bm_vote_map, "\n");
		bm_vote_go_t = time + 3;
	}
	else
		bprint ("Vote failed (", ftos (bm_v_yes), " yes, ", ftos (bm_v_no), " no)\n");
};

void() BM_VoteCheck =
{
	BM_VoteCount ();
	if (bm_v_n < 1)
		bm_vote_on = FALSE;			// everybody left
	else if (bm_v_yes * 2 > bm_v_n)
		BM_VoteEnd (TRUE);
	else if (bm_v_no * 2 >= bm_v_n)
		BM_VoteEnd (FALSE);
	else if (time >= bm_vote_end)
		BM_VoteEnd (bm_v_yes > bm_v_no);
};

// StartFrame
void() BM_VoteTick =
{
	local entity e;

	if (bm_vote_go_t && time >= bm_vote_go_t)
	{
		bm_vote_go_t = 0;
		localcmd (strcat ("changelevel ", bm_vote_map, "\n"));
		return;
	}
	if (!bm_vote_on)
		return;
	if (intermission_running)
	{
		bm_vote_on = FALSE;
		return;
	}
	if (time < bm_vote_tick_t)
		return;
	bm_vote_tick_t = time + 0.5;
	BM_VoteCheck ();
	if (!bm_vote_on || time < bm_vote_prompt_t)
		return;
	bm_vote_prompt_t = time + 1;
	e = find (world, classname, "player");
	while (e)
	{
		if (e.ishuman == 1 && !e.bm_voted)
			centerprint (e, strcat ("VOTE: change the map to ", bm_vote_map, "\nSay  vote yes  or  vote no  in chat\nyes ", ftos (bm_v_yes), "   no ", ftos (bm_v_no), strcat ("   ", ftos (ceil (bm_vote_end - time)), "s left")));
		e = find (e, classname, "player");
	}
};

// the maps a vote may pick, e.g. "fox bklan6" (when bm_votemaps is unset locally, default to installed DM maps)
string() BM_VoteMapList =
{
	local string s;

	s = cvar_string ("bm_votemaps");
	if (s != "")
		return s;
	return "soi6 soicowboy_bkk bakersfielddowntown terminal21 little_st_james slo_bike_kitchen ooika_lawrenceville goldenwest morrorock fox bklan6 aerowalk dm6";
};

void(entity e, string m) BM_VoteStart =
{
	local float n, i;
	local string pick;
	local entity p;

	if (intermission_running)
		return;
	if (bm_vote_on || bm_vote_go_t)
	{
		sprint (e, "A vote is already running.\n");
		return;
	}
	if (time < e.bm_vote_cool)
	{
		sprint (e, strcat ("Wait ", ftos (ceil (e.bm_vote_cool - time)), " seconds before calling another vote.\n"));
		return;
	}
	pick = "";
	n = tokenize (BM_VoteMapList ());
	i = 0;
	while (i < n)
	{
		if (argv (i) == m)
			pick = argv (i);
		i = i + 1;
	}
	if (pick == "")
	{
		sprint (e, strcat ("You can vote for these maps: ", BM_VoteMapList (), "\n"));
		return;
	}
	if (pick == mapname)
	{
		sprint (e, strcat ("We are already on ", pick, ".\n"));
		return;
	}
	if (bm_vote_map)
		strunzone (bm_vote_map);
	bm_vote_map = strzone (pick);
	e.bm_vote_cool = time + autocvar_bm_votecool;
	bm_vote_on = TRUE;
	bm_vote_end = time + autocvar_bm_votetime;
	bm_vote_tick_t = time + 0.5;
	bm_vote_prompt_t = time + 1;
	p = find (world, classname, "player");
	while (p)
	{
		p.bm_voted = 0;
		if (p.ishuman == 1)
			sprint (p, "\n");
		p = find (p, classname, "player");
	}
	e.bm_voted = 1;
	bprint (e.netname, " called a vote: change the map to ", pick, "\n");
	bprint ("Say  vote yes  or  vote no  in chat (or console)\n");
	BM_VoteCheck ();
};

void(entity e, float v) BM_VoteCast =
{
	if (!bm_vote_on)
	{
		sprint (e, strcat ("No vote is running. Say  vote map <name>  to start one (", BM_VoteMapList (), ").\n"));
		return;
	}
	e.bm_voted = v;
	if (v == 1)
		sprint (e, "You voted YES.\n");
	else
		sprint (e, "You voted NO.\n");
	BM_VoteCheck ();
};

// a "vote ..." line from chat or the console; n tokens are in argv
void(float n, float chat) BM_VoteCommand =
{
	local string a, b;

	a = "";
	b = "";
	if (n >= 2)
		a = strtolower (argv (1));
	if (n >= 3)
		b = strtolower (argv (2));
	if (self.ishuman != 1)
		return;
	if (a == "yes" || a == "y")
		BM_VoteCast (self, 1);
	else if (a == "no" || a == "n")
		BM_VoteCast (self, 2);
	else if (a == "map" && b != "")
		BM_VoteStart (self, b);
	else if (!chat)
		sprint (self, strcat ("Usage: vote map <name>  |  vote yes  |  vote no   (maps: ", BM_VoteMapList (), ")\n"));
};

// the engine hands every client command to the progs first; anything not ours goes back to the engine
void(string s) SV_ParseClientCommand =
{
	local float n, i, chat;
	local string t;

	chat = FALSE;
	n = tokenize (s);
	if (autocvar_bm_vote && n >= 1)
	{
		if (argv (0) == "say" || argv (0) == "say_team")
		{
			chat = TRUE;
			t = "";
			i = 1;
			while (i < n)
			{
				t = strcat (t, " ", argv (i));
				i = i + 1;
			}
			n = tokenize (t);
		}
		if (n >= 1 && strtolower (argv (0)) == "vote")
		{
			BM_VoteCommand (n, chat);
			if (!chat)
				return;
		}
	}
	// the tank switches below set server-wide mm_tank_* cvars: never from chat words, and only with sv_cheats 1
	if (chat)
	{
		clientcommand (self, s);
		return;
	}
	if (n >= 1 && strtolower (argv (0)) == "observe")
	{
		local string okey;
		okey = cvar_string ("bm_obs_key");
		if (okey != "" && n >= 2 && argv (1) == okey)
		{
			BM_ObsActivate (self);
			return;
		}
		sprint (self, "Observer mode requires a valid bm_obs_key.\n");
		return;
	}
	if (n >= 1 && !autocvar_sv_cheats)
	{
		t = strtolower (argv (0));
		if (t == "tank_variant" || t == "mm_tank_variant" || t == "tank_sound" || t == "mm_tank_soundpack" || t == "tank_boom_pool")
		{
			sprint (self, "Mega Man Tank switches need sv_cheats 1\n");
			return;
		}
	}
	if (n >= 1 && (strtolower (argv (0)) == "tank_variant" || strtolower (argv (0)) == "mm_tank_variant"))
	{
		if (n >= 2)
			MMTank_SetVariant (stof (argv (1)));
		else if (autocvar_mm_tank_variant >= 4)
			MMTank_SetVariant (1);
		else
			MMTank_SetVariant (autocvar_mm_tank_variant + 1);
		sprint (self, strcat ("Mega Man Tank prototype set to ", ftos (floor (autocvar_mm_tank_variant)), "\n"));
		return;
	}
	if (n >= 1 && (strtolower (argv (0)) == "tank_sound" || strtolower (argv (0)) == "mm_tank_soundpack"))
	{
		if (n >= 2)
			MMTank_SetSoundPack (stof (argv (1)));
		else if (autocvar_mm_tank_soundpack >= 11)
			MMTank_SetSoundPack (0);
		else
			MMTank_SetSoundPack (autocvar_mm_tank_soundpack + 1);
		sprint (self, strcat ("Mega Man Tank sound pack set to ", ftos (floor (autocvar_mm_tank_soundpack)), "\n"));
		return;
	}
	if (n >= 1 && strtolower (argv (0)) == "tank_boom_pool")
	{
		if (n >= 2)
			MMTank_SetBoomMask (stof (argv (1)));
		sprint (self, strcat ("Mega Man Tank boom pool mask=", ftos (floor (autocvar_mm_tank_boom_mask)), " (packs: ", MMT_BoomMaskSummary (autocvar_mm_tank_boom_mask), ")\n"));
		return;
	}
	clientcommand (self, s);
};

// StartFrame
void() BM_StartFrame =
{
	local float n, want, cno, lim, bmask, pmask, bit, obs_n;
	local entity p, tail;

	// Refresh hot cvars once per server tick from engine-synced autocvars
	bm_cvar_grav = autocvar_sv_gravity;
	bm_cvar_maxvel = autocvar_sv_maxvelocity;
	bm_cvar_ltg_video = autocvar_ltg_video;
	bm_cvar_br_mode = autocvar_br_mode;
	bm_cvar_dv_mode = autocvar_dv_mode;
	bm_cvar_dv_stay = autocvar_dv_stay;
	bm_cvar_dn_mode = autocvar_dn_mode;
	bm_cvar_dn_stay = autocvar_dn_stay;
	bm_cvar_rnpc_mode = autocvar_rnpc_mode;
	bm_cvar_rnpc_stay = autocvar_rnpc_stay;
	bm_cvar_pk_ofs = autocvar_pk_viewoffset;
	bm_cvar_dev = autocvar_developer;
	bm_menubg_active = BM_IsMenuBg ();

	// Rebuild active player list and HUD bot/human bitmasks in a single 1..max_clients pass
	bm_player_head = world;
	tail = world;
	bmask = 0;
	pmask = 0;
	obs_n = 0;
	bit = 1;
	cno = 0;
	lim = max_clients;
	if (lim <= 0)
		lim = 16;
	p = nextent (world);
	while (cno < lim && p != world)
	{
		if (p.bm_obs)
			obs_n = obs_n + 1;
		else if (p.classname == "player")
		{
			p.bm_player_next = world;
			if (!bm_player_head)
				bm_player_head = p;
			else
				tail.bm_player_next = p;
			tail = p;
		}
		if (cno < 16)
		{
			if ((active_clients & bit) && !p.bm_obs && p.health > 0 && p.modelindex != 0 && !(p.flags & FL_NOTARGET))
			{
				if (p.ishuman != 1)
					bmask = bmask | bit;
				else if (!(p.items & IT_INVISIBILITY) && !(p.effects & EF_NODRAW))
					pmask = pmask | bit;
			}
			bit = bit * 2;
		}
		cno = cno + 1;
		p = nextent (p);
	}
	bm_obs_count = obs_n;
	bm_botmask_cache = bmask;
	bm_playermask_cache = pmask;

	Underdog_Update ();
	Crowd_Tick ();
	Soi6_Tick ();
	RocketRider_MapTick ();
	MMTank_StartFrame ();
	BM_VoteTick ();
	BM_BotStartFrame ();
	BM_ObsCheckDiscard ();
	BM_Radar_Tick ();
	if (autocvar_bm_debug && time >= bm_debug_t)
	{
		bm_debug_t = time + 2;
		BM_DebugPrint ();
	}

	if (bm_menubg_active || !deathmatch || intermission_running || bm_manual_bots || time < bm_botfill_t)
		return;
	bm_botfill_t = time + 2;
	want = autocvar_bm_botfill;
	if (BM_DummyMap () && want < 4)
		want = 4;
	if (want <= 0)
		return;
	// leave bm_bot_reserve slots open (LAN too): a joining human otherwise lands in a bot's slot,
	// and on a public server the reserve rule would kick every bot this adds
	// observers hold a slot but are not in BM_CountPlayers: subtract them too, or the public
	// reserve kick (which does) removes each bot this adds, forever
	if (want > max_clients - autocvar_bm_bot_reserve - bm_obs_count)
		want = max_clients - autocvar_bm_bot_reserve - bm_obs_count;
	n = BM_CountPlayers ();
	if (n < 1 && !autocvar_bm_botfill_empty)
		return;		// nobody here yet: don't fill an empty server
	if (n < want)
	{
		if (ClientNextAvailable () != -1 && bot_count < autocvar_bm_bot_max)		// no free slot: BotConnect would bprint "server is full" to everybody every 2 s
			BotConnect (0, 0, autocvar_skill);
	}
	else if (n > want && bot_count > 0)
		KickABot ();
};

// cheat-only test helpers: impulse 42 gives you 2 frags (try the leader effects), impulse 43 gives every bot 2,
// impulse 44 the first living bot kills you, impulse 45 you kill the first living bot (the announcer, obituaries),
// impulse 48 you and the first living bot each take a 100 damage hit from the other and the log says what landed (the underdog damage scaling)
void() BM_TestImpulses =
{
	local entity e;
	local float h0, a0;

	if (!self.impulse || !autocvar_sv_cheats)
		return;
	if (self.impulse == 48)
	{
		e = find (world, classname, "player");
		while (e && (e.ishuman == 1 || e.health <= 0))
			e = find (e, classname, "player");
		if (e)
		{
			self.bm_prot_t = 0;
			self.invincible_finished = 0;
			self.super_damage_finished = 0;
			e.bm_prot_t = 0;
			e.invincible_finished = 0;
			e.super_damage_finished = 0;
			h0 = self.health;
			a0 = self.armorvalue;
			T_Damage (self, e, e, 100);
			bprint ("ud hit you: boost ", ftos (self.ud_boost), " your frags ", ftos (self.frags), " theirs ", ftos (e.frags), " lost ", ftos (h0 + a0 - self.health - self.armorvalue), "\n");
			h0 = e.health;
			a0 = e.armorvalue;
			T_Damage (e, self, self, 100);
			bprint ("ud hit bot: boost ", ftos (self.ud_boost), " bot lost ", ftos (h0 + a0 - e.health - e.armorvalue), "\n");
		}
		self.impulse = 0;
		return;
	}
	if (self.impulse == 44 || self.impulse == 45)
	{
		e = find (world, classname, "player");
		while (e && (e.ishuman == 1 || e.health <= 0))
			e = find (e, classname, "player");
		if (e)
		{
			if (self.impulse == 44)
			{
				self.invincible_finished = 0;		// a boosted spawn's pentagram would stop the test kill
				T_Damage (self, e, e, 1000);
			}
			else
				T_Damage (e, self, self, 1000);
		}
		self.impulse = 0;
		return;
	}
	if (self.impulse == 42)
	{
		self.frags = self.frags + 2;
		self.impulse = 0;
		ud_next_t = 0;
	}
	else if (self.impulse == 43)
	{
		e = find (world, classname, "player");
		while (e)
		{
			if (e.ishuman != 1)
				e.frags = e.frags + 2;
			e = find (e, classname, "player");
		}
		self.impulse = 0;
		ud_next_t = 0;
	}
	else if (self.impulse == 46)
	{
		GreenSuit_Summon ();
		self.impulse = 0;
	}
	else if (self.impulse == 47)
	{
		RobeGuy_Summon ();
		self.impulse = 0;
	}
	else if (self.impulse >= 51 && self.impulse <= 54)
	{
		RandomNPC_Summon (self.impulse - 50);
		self.impulse = 0;
	}
	else if (self.impulse == 55)
	{
		RandomNPC_SummonAll4 ();
		self.impulse = 0;
	}
	else if (self.impulse == 56)
	{
		Crowd_Report ();
		self.impulse = 0;
	}
	else if (self.impulse == 59)
	{
		Crowd_Line ();
		self.impulse = 0;
	}
	else if (self.impulse == 60)
	{
		SkyPad_Report ();
		self.impulse = 0;
	}
	else if (self.impulse == 57 || self.impulse == 58)
	{
		if (self.impulse == 57)
			Crowd_Poke (25);
		else
			Crowd_Poke (500);
		self.impulse = 0;
	}
	// Soi 6 test impulses live at 141-146: they were 61-66, the fun-gun select impulses (FG_IMPULSE 61..69), so with
	// sv_cheats on a bot or player picking the Rob Dob / NetSend / Wheelman Cannon got a lineup, gib test or teleport
	else if (self.impulse == 141)
	{
		Soi6_Line ();
		self.impulse = 0;
	}
	else if (self.impulse == 142)
	{
		Soi6_Poke (25);
		self.impulse = 0;
	}
	else if (self.impulse == 143)
	{
		Soi6_Poke (80);
		self.impulse = 0;
	}
	else if (self.impulse == 144)
	{
		Soi6_Poke (500);
		self.impulse = 0;
	}
	else if (self.impulse == 145)
	{
		Soi6_GotoStreet ();
		self.impulse = 0;
	}
	else if (self.impulse == 146)
	{
		Soi6_GotoBarSide ();
		self.impulse = 0;
	}
};

// every frame from W_WeaponFrame: while the server overrides your speed the client's own movement guess is wrong by a whole ping
// and each correction snaps you back, so it stops guessing (bm_nopredict 0 puts it back)
void() BM_PredictFrame =
{
	if (autocvar_bm_nopredict && (self.jp_on || self.veh_ride != world || self.mmt_tank != world || self.ltg_shock > 0 || time < self.milk_freeze || self.milk_slip || time < self.jb_slow_t || time < self.pc_poop_t))
		self.disableclientprediction = 1;
	else
		self.disableclientprediction = 0;
};

// ClientDisconnect: what a leaver left in the map goes with them (NetSend PCs, armed pickles, Mega Men on the loose)
void(entity p) BM_ClientGone =
{
	local entity e, nx, me;

	NS_ClientGone (p);
	KY_CleanupOwner (p);
	FD_Reset (p);
	me = self;
	e = find (world, classname, "pickle");
	while (e)
	{
		nx = find (e, classname, "pickle");
		if (e.owner == p)
		{
			self = e;
			Pk_Fizzle ();
		}
		e = nx;
	}
	e = find (world, classname, "megaman");
	while (e)
	{
		nx = find (e, classname, "megaman");
		if (e.owner == p)
		{
			self = e;
			MegaMan_Dud ();
		}
		e = nx;
	}
	// Green Men pop harmlessly (gj_attack_end 0: no confetti damage in a reused slot's name)
	e = find (world, classname, "greenguy_mini");
	while (e)
	{
		nx = find (e, classname, "greenguy_mini");
		if (e.owner == p && e.gj_state != 5)
		{
			e.gj_attack_end = 0;
			GJ_StartBalloonPop (e, TRUE);
		}
		e = nx;
	}
	e = find (world, classname, "greenjar_proj");
	while (e)
	{
		nx = find (e, classname, "greenjar_proj");
		if (e.owner == p)
			remove (e);
		e = nx;
	}
	e = find (world, classname, "wc_shot");
	while (e)
	{
		nx = find (e, classname, "wc_shot");
		if (e.owner == p)
		{
			self = e;
			WC_Fizzle ();
		}
		e = nx;
	}
	// Pink Ladies (milky.qc) and in-flight Dookie canisters (dookie.qc) leave with their owner
	e = find (world, classname, "milky");
	while (e)
	{
		nx = find (e, classname, "milky");
		if (e.milky_owner == p)
		{
			sound (e, CHAN_BODY, "misc/null.wav", 0, ATTN_NONE);
			remove (e);
		}
		e = nx;
	}
	p.milky_active = world;
	e = find (world, classname, "dookie_shot");
	while (e)
	{
		nx = find (e, classname, "dookie_shot");
		if (e.owner == p)
		{
			sound (e, CHAN_BODY, "misc/null.wav", 0, ATTN_NONE);
			remove (e);
		}
		e = nx;
	}
	// a laptop shock from the leaver stops (the zap damage would otherwise go to whoever reuses the slot)
	e = find (world, classname, "player");
	while (e)
	{
		if (e.ltg_by == p)
		{
			e.ltg_shock = 0;
			e.ltg_by = world;
		}
		e = find (e, classname, "player");
	}
	self = me;
};

// ---------------------------------------------------------------- server observer / auto-director camera
var float autocvar_bm_obs_qualify_sec = 15;			// >= 2 humans for this long before an observer demo is kept
float autocvar_sv_autodemo_perclient_discardable;		// engine cvar

void(entity e) BM_ObsActivate =
{
	local entity me;

	me = self;
	self = e;
	if (!e.bm_obs)
	{
		// out of any van / bird / cannon / tank first (self = e, classname still "player" so the
		// leave code releases him): else the vehicle keeps a driver ref and the HUD stats stay set
		Veh_ClientGone ();
		JohnBird_ClientGone ();
		RocketRider_ClientGone ();
		EricCannon_ClientGone ();
		MMTank_ClientGone ();
		Underdog_ClearFx (e);
		Underdog_Reset (e);
		FD_Reset (e);
		BM_ClientGone (e);
		BM_Radar_ClientGone (e);
	}
	if (e.bm_aura)
	{
		if (!bm_wasfreed (e.bm_aura) && e.bm_aura.classname == "bm_aura" && e.bm_aura.owner == e)
			remove (e.bm_aura);
		e.bm_aura = world;
	}
	e.bm_obs = 1;
	e.classname = "observer";
	e.ishuman = 3;
	e.solid = SOLID_NOT;
	e.movetype = MOVETYPE_NONE;
	e.takedamage = DAMAGE_NO;
	e.flags = FL_CLIENT | FL_NOTARGET;
	e.deadflag = DEAD_NO;
	e.health = 100;
	e.max_health = 100;
	e.armorvalue = 0;
	e.armortype = 0;
	e.items = 0;
	e.weapon = 0;
	e.modelindex = 0;
	e.model = "";
	e.weaponmodel = "";
	e.weaponframe = 0;
	e.view_ofs = '0 0 0';
	e.velocity = '0 0 0';
	e.clientcamera = e;
	e.bm_prot_t = 0;
	e.bm_st_menubg = 0;
	e.v_weapon_position_helper = 0;
	e.quad_v_weapon_position_helper = 0;
	if (bm_obs_qualify_t < max (1, autocvar_bm_obs_qualify_sec))
		e.discardabledemo = 1;
	else
		e.discardabledemo = 0;
	self = me;
};

float(float a, float b) BM_ObsAngleDiff =
{
	local float d;

	d = a - b;
	while (d > 180)
		d = d - 360;
	while (d < -180)
		d = d + 360;
	return d;
};

vector(vector from, vector to) BM_ObsLookAngles =
{
	local vector a;
	local float px;

	a = vectoangles (to - from);
	px = a_x;
	if (px > 180)
		px = px - 360;
	a_x = 0 - px;
	a_z = 0;
	return a;
};

entity(entity cur) BM_ObsPickTarget =
{
	local entity p, q, best;
	local float has_human, score, bestscore, near;

	has_human = FALSE;
	p = bm_player_head;
	while (p)
	{
		if (!p.bm_obs && p.health > 0 && !p.deadflag && p.ishuman == 1)
		{
			has_human = TRUE;
			break;
		}
		p = p.bm_player_next;
	}

	best = world;
	bestscore = -99999;
	p = bm_player_head;
	while (p)
	{
		if (!p.bm_obs && p.health > 0 && !p.deadflag && (!has_human || p.ishuman == 1))
		{
			score = random () * 8;
			if (p != cur)
				score = score + 30;
			if (p.frags > p.bm_obs_frags_last)
				score = score + 25;
			if (p.show_hostile > time)
				score = score + 15;
			if (vlen (p.velocity) > 250 || p.jp_on || p.veh_ride != world || p.mmt_tank != world)
				score = score + 10;
			near = FALSE;
			q = bm_player_head;
			while (q)
			{
				if (q != p && !q.bm_obs && q.health > 0 && vlen (q.origin - p.origin) < 900)
				{
					near = TRUE;
					break;
				}
				q = q.bm_player_next;
			}
			if (near)
				score = score + 20;
			if (score > bestscore)
			{
				bestscore = score;
				best = p;
			}
		}
		p.bm_obs_frags_last = p.frags;
		p = p.bm_player_next;
	}
	return best;
};

void() BM_ObsCheckDiscard =
{
	local float dt, hn, cno, lim, need_sec, keep;
	local entity p;

	if (bm_obs_frame_t <= 0)
		dt = 0;
	else
		dt = bound (0, time - bm_obs_frame_t, 0.1);
	bm_obs_frame_t = time;
	// no observer: nothing to qualify, and humans already got discardabledemo 1 in ClientConnect
	if (bm_obs_count <= 0)
		return;

	hn = 0;
	p = bm_player_head;
	while (p)
	{
		if (!p.bm_obs && p.ishuman == 1)
			hn = hn + 1;
		p = p.bm_player_next;
	}

	if (hn >= 2 && bm_obs_count > 0 && !intermission_running)
		bm_obs_qualify_t = bm_obs_qualify_t + dt;

	if (autocvar_sv_autodemo_perclient_discardable <= 0)
		return;

	need_sec = max (1, autocvar_bm_obs_qualify_sec);
	keep = (bm_obs_qualify_t >= need_sec);

	cno = 0;
	lim = max_clients;
	if (lim <= 0)
		lim = 16;
	p = nextent (world);
	while (cno < lim && p != world)
	{
		if (p.bm_obs)
			p.discardabledemo = keep ? 0 : 1;
		else if (p.ishuman == 1)
			p.discardabledemo = 1;
		cno = cno + 1;
		p = nextent (p);
	}
};

void() BM_ObsFrame =
{
	local entity p, spot, prev_targ;
	local vector focus, want_ang, want_org, aim_ang;
	local float dist, up, dt, s_ang, s_pos, switched;

	self.classname = "observer";
	self.ishuman = 3;
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.takedamage = DAMAGE_NO;
	self.flags = FL_CLIENT | FL_NOTARGET;
	self.deadflag = DEAD_NO;
	self.health = 100;
	self.max_health = 100;
	self.armorvalue = 0;
	self.armortype = 0;
	self.items = 0;
	self.weapon = 0;
	self.modelindex = 0;
	self.model = "";
	self.weaponmodel = "";
	self.weaponframe = 0;
	self.view_ofs = '0 0 0';
	self.velocity = '0 0 0';
	self.clientcamera = self;
	self.bm_st_mag = 0;
	self.bm_st_magmax = 0;
	self.bm_st_reload = 0;
	self.bm_st_slot = 0;
	self.bm_st_prot = 0;
	self.bm_st_heat = 0;
	self.bm_st_boost = 0;
	self.bm_st_regen = 0;
	self.bm_st_warmup = 0;
	self.bm_st_lheat = 0;
	self.bm_st_lshow = 0;
	self.bm_st_leader = "";
	self.bm_st_toymask = 0;
	self.bm_st_toycd = 0;
	self.jp_st_fuel = 0;
	self.jp_st_max = 0;
	self.milk_st = 0;
	self.fd_st_mode = 0;
	self.mmt_st_active = 0;
	self.jb_st_active = 0;
	self.ky_st_mode = 0;
	self.gk_st_mode = 0;
	self.gk_st_prog = 0;
	self.gk_st_nitro = 0;
	self.bm_st_menubg = 0;
	self.bm_st_botmask = bm_botmask_cache;
	self.bm_st_playermask = bm_playermask_cache;
	self.bm_st_botcnt = bot_count;

	if (intermission_running)
	{
		if (bm_obs_cam_init)
		{
			setorigin (self, bm_obs_cam_org);
			self.v_angle = bm_obs_cam_ang;
			self.angles = bm_obs_cam_ang;
			self.fixangle = TRUE;
		}
		return;
	}

	prev_targ = bm_obs_targ;
	switched = FALSE;

	if (!bm_obs_targ || bm_wasfreed (bm_obs_targ) || bm_obs_targ.classname != "player" || bm_obs_targ.bm_obs)
	{
		bm_obs_death_t = 0;
		bm_obs_targ = BM_ObsPickTarget (world);
		bm_obs_switch_t = time + 5;
		bm_obs_force_t = time + 13;
		switched = (bm_obs_targ != prev_targ);
	}
	else if (bm_obs_targ.health <= 0 || bm_obs_targ.deadflag)
	{
		if (!bm_obs_death_t)
			bm_obs_death_t = time + 1.5;
		if (time >= bm_obs_death_t)
		{
			bm_obs_death_t = 0;
			bm_obs_targ = BM_ObsPickTarget (bm_obs_targ);
			bm_obs_switch_t = time + 5;
			bm_obs_force_t = time + 13;
			switched = (bm_obs_targ != prev_targ);
		}
	}
	else
	{
		bm_obs_death_t = 0;
		if (time >= bm_obs_force_t)
		{
			bm_obs_targ = BM_ObsPickTarget (bm_obs_targ);
			bm_obs_switch_t = time + 5;
			bm_obs_force_t = time + 13;
			switched = (bm_obs_targ != prev_targ);
		}
		else if (time >= bm_obs_switch_t)
		{
			p = bm_player_head;
			while (p)
			{
				if (p != bm_obs_targ && !p.bm_obs && p.ishuman == 1 && p.health > 0 && p.frags > p.bm_obs_frags_last)
				{
					bm_obs_targ = p;
					bm_obs_switch_t = time + 5;
					bm_obs_force_t = time + 13;
					switched = TRUE;
					break;
				}
				p = p.bm_player_next;
			}
			p = bm_player_head;
			while (p)
			{
				p.bm_obs_frags_last = p.frags;
				p = p.bm_player_next;
			}
		}
	}

	if (!bm_obs_targ)
	{
		if (!bm_obs_cam_init)
		{
			spot = find (world, classname, "info_player_deathmatch");
			if (spot)
			{
				bm_obs_cam_org = spot.origin + '0 0 48';
				bm_obs_cam_ang = spot.angles;
				bm_obs_cam_ang_x = 10;
			}
			else
			{
				bm_obs_cam_org = '0 0 96';
				bm_obs_cam_ang = '10 0 0';
			}
			bm_obs_cam_init = 1;
		}
		setorigin (self, bm_obs_cam_org);
		self.v_angle = bm_obs_cam_ang;
		self.angles = bm_obs_cam_ang;
		self.fixangle = TRUE;
		return;
	}

	if (bm_obs_targ.fd_head != world)
	{
		focus = bm_obs_targ.fd_head.origin;
		dist = 90;
		up = 22;
	}
	else if (bm_obs_targ.mmt_tank != world)
	{
		focus = bm_obs_targ.mmt_tank.origin + '0 0 36';
		dist = 165;
		up = 52;
	}
	else if (bm_obs_targ.veh_ride != world)
	{
		focus = bm_obs_targ.veh_ride.origin + '0 0 32';
		dist = 155;
		up = 46;
	}
	else
	{
		focus = bm_obs_targ.origin + '0 0 28';
		dist = 110;
		up = 28;
	}

	want_ang_x = bound (-30, bm_obs_targ.v_angle_x * 0.55 + 10, 35);
	want_ang_y = bm_obs_targ.v_angle_y;
	want_ang_z = 0;

	dt = bound (0.001, frametime, 0.1);
	if (!bm_obs_cam_init || switched || vlen (focus - bm_obs_cam_org) > 700)
	{
		bm_obs_cam_ang = want_ang;
	}
	else
	{
		s_ang = min (1, dt * 6);
		bm_obs_cam_ang_x = bm_obs_cam_ang_x + (want_ang_x - bm_obs_cam_ang_x) * s_ang;
		bm_obs_cam_ang_y = bm_obs_cam_ang_y + BM_ObsAngleDiff (want_ang_y, bm_obs_cam_ang_y) * s_ang;
		bm_obs_cam_ang_z = 0;
	}

	makevectors (bm_obs_cam_ang);
	want_org = focus - v_forward * dist + v_up * up + v_right * 12;
	traceline (focus, want_org, TRUE, bm_obs_targ);
	if (trace_fraction < 1)
		want_org = focus + (want_org - focus) * max (0.18, trace_fraction - 0.08);

	if (!bm_obs_cam_init || switched || vlen (want_org - bm_obs_cam_org) > 700)
		bm_obs_cam_org = want_org;
	else
	{
		s_pos = min (1, dt * 14);
		bm_obs_cam_org = bm_obs_cam_org + (want_org - bm_obs_cam_org) * s_pos;
	}
	bm_obs_cam_init = 1;

	aim_ang = BM_ObsLookAngles (bm_obs_cam_org, focus - '0 0 6');
	setorigin (self, bm_obs_cam_org);
	self.v_angle = aim_ang;
	self.angles = aim_ang;
	self.fixangle = TRUE;
};
