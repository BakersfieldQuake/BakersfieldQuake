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

void() BM_Precache =
{
	precache_sound ("weapons/lock4.wav");
	precache_sound ("weapons/pkup.wav");
	precache_sound ("misc/talk.wav");
	precache_model ("progs/aura.md3");
	if (autocvar_bm_newbie > 0)
		precache_sound ("funny/newbie.wav");
	if (autocvar_bm_fun)
		BM_Fun_Precache ();
	David_Precache ();
	Daniel_Precache ();
	GreenSuit_Precache ();
	RobeGuy_Precache ();
	RandomNPCs_Precache ();
	JohnBird_Precache ();
};

// T_Damage, after Underdog_Damage: returns the damage to apply; bm_kb keeps the full push
float(entity targ, entity inflictor, entity attacker, float damage) BM_Damage =
{
	bm_kb = damage;
	bm_blocked = FALSE;
	if (targ.classname != "player")
		return damage;
	if (targ.bm_prot_t > time && damage < 1000)		// telefrags still go through
	{
		bm_blocked = TRUE;
		return 0;
	}
	if (attacker == targ)
	{
		damage = damage * autocvar_bm_selfdamage;
		if (inflictor.classname == "missile")		// your own rocket: a further cut on top
			damage = damage * autocvar_bm_rocketself;
	}
	return damage;
};

// end of PutClientInServer
void() BM_PlayerSpawned =
{
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
		stuffcmd (self, "alias vote \"cmd vote $*\"\nv_glslgamma 1\nv_glslgamma_2d 1\n");	// map votes + apply GLSL gamma to 2D Quake HUD in windowed mode
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
	if (self.bm_prot_t)
	{
		if (time < self.bm_prot_t - autocvar_bm_spawnprot + autocvar_bm_spawnpause)
			self.button0 = 0;		// just spawned: a brief pause before the trigger works
		if (time >= self.bm_prot_t || (self.button0 && time > self.bm_prot_t - autocvar_bm_spawnprot + 0.3))
			self.bm_prot_t = 0;
	}
	BM_AuraFrame ();
	if (self.bm_prot_t)
		self.bm_st_prot = ceil ((self.bm_prot_t - time) * 10);
	else
		self.bm_st_prot = 0;

	Underdog_FxFrame ();

	self.bm_st_regen = (self.health > 0 && self.health < self.max_health && time > self.rg_hurt_t + Underdog_RegenDelay ());
	self.bm_st_warmup = (autocvar_bm_warmup != 0);
	self.bm_st_heat = floor (self.ud_heat);
	self.bm_st_boost = floor (self.ud_boost * 100);
	if (ud_leader)
	{
		self.bm_st_leader = ud_leader.netname;
		self.bm_st_lheat = floor (ud_leader.ud_heat);
		self.bm_st_lshow = (ud_leader.ud_tier >= 3 && ud_leader != self && ud_leader.health > 0);
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
};

// SelectSpawnPoint (client.qc) asks first. bklan4 is about 28000 x 20000 units with 52 spawns scattered over it, and
// the stock round robin hands out the next free spawn in map order, so a handful of players start in different
// corners and never meet. This picks the free spawn closest to a living rival that is not nearer than bm_spawnnear
// units and not in sight of them (a little random, so it is not always the same one). Nobody else alive: a random
// free spawn. world = use the stock choice.
entity() BM_PickSpawn =
{
	local entity spot, p, best;
	local float dmin, d, score, bestscore, seen;

	if (!deathmatch || autocvar_bm_spawnnear <= 0)
		return world;
	best = world;
	bestscore = 1000000;
	spot = find (world, classname, "info_player_deathmatch");
	while (spot)
	{
		p = findradius (spot.origin, 32);
		while (p && p.classname != "player")
			p = p.chain;
		if (!p)
		{
			dmin = 99999;
			seen = 0;
			p = find (world, classname, "player");
			while (p)
			{
				if (p != self && p.health > 0)
				{
					d = vlen (p.origin - spot.origin);
					if (d < dmin)
						dmin = d;
					if (d < 2500 && !seen)
					{
						traceline (spot.origin + '0 0 24', p.origin + '0 0 24', TRUE, spot);
						if (trace_fraction == 1)
							seen = 1;
					}
				}
				p = find (p, classname, "player");
			}
			if (dmin == 99999)
				score = random () * 1000;
			else if (dmin < autocvar_bm_spawnnear)
				score = 20000 + (autocvar_bm_spawnnear - dmin);
			else
				score = dmin + seen * 4000 + random () * 1500;
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

// NextLevel: TRUE = handled (the playlist picked the next map)
float() BM_NextLevel =
{
	local float n, i, found;
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
	i = found + 1;
	if (i >= n)
		i = 0;
	pick = argv (i);
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
	clientstat (61, 1, bm_st_leader);
	clientstat (62, 2, bm_st_lx);
	clientstat (63, 2, bm_st_ly);
	clientstat (64, 2, bm_st_lz);
	clientstat (65, 2, bm_st_lshow);
	clientstat (66, 2, jp_st_fuel);		// the jetpack's glass fuel tank (jetpack.qc, csqc/bm_hud.qc)
	clientstat (67, 2, jp_st_max);
	clientstat (68, 2, milk_st);		// milk on the screen after a Pink Lady burst (milky.qc, csqc/bm_hud.qc)
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

	if (!BM_DummyMap ())
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
			centerprint (e, strcat ("VOTE: change the map to ", bm_vote_map, "\n\nF5 = YES     F6 = NO\n(or type  vote yes / vote no)\n\nyes ", ftos (bm_v_yes), "   no ", ftos (bm_v_no), "   ", ftos (ceil (bm_vote_end - time)), "s left"));
		e = find (e, classname, "player");
	}
};

// the maps a vote may pick, e.g. "fox bklan4"
string() BM_VoteMapList =
{
	return cvar_string ("bm_votemaps");
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
		{
			stuffcmd (p, "bind F5 \"cmd vote yes\"\nbind F6 \"cmd vote no\"\n");
			sprint (p, "\n");
		}
		p = find (p, classname, "player");
	}
	e.bm_voted = 1;
	bprint (e.netname, " called a vote: change the map to ", pick, "\n");
	bprint ("Vote with F5 (yes) / F6 (no), or type: vote yes / vote no\n");
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

	n = tokenize (s);
	if (autocvar_bm_vote && n >= 1)
	{
		chat = FALSE;
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
	clientcommand (self, s);
};

// StartFrame
void() BM_StartFrame =
{
	local float n, want;
	local entity p, tail;

	// Refresh hot cvars once per server tick instead of per-entity / per-customizeentityforclient
	bm_cvar_grav = cvar ("sv_gravity");
	bm_cvar_maxvel = cvar ("sv_maxvelocity");
	bm_cvar_ltg_video = cvar ("ltg_video");
	bm_cvar_br_mode = cvar ("br_mode");
	bm_cvar_dv_mode = cvar ("dv_mode");
	bm_cvar_dv_stay = cvar ("dv_stay");
	bm_cvar_dn_mode = cvar ("dn_mode");
	bm_cvar_dn_stay = cvar ("dn_stay");
	bm_cvar_rnpc_mode = autocvar_rnpc_mode;
	bm_cvar_rnpc_stay = autocvar_rnpc_stay;
	bm_cvar_pk_ofs = cvar ("pk_viewoffset");
	bm_cvar_dev = cvar ("developer");

	// Rebuild active player list once per server tick
	bm_player_head = world;
	tail = world;
	p = find (world, classname, "player");
	while (p)
	{
		p.bm_player_next = world;
		if (!bm_player_head)
			bm_player_head = p;
		else
			tail.bm_player_next = p;
		tail = p;
		p = find (p, classname, "player");
	}

	Underdog_Update ();
	BM_VoteTick ();
	if (autocvar_bm_debug && time >= bm_debug_t)
	{
		bm_debug_t = time + 2;
		BM_DebugPrint ();
	}

	if (!deathmatch || intermission_running || time < bm_botfill_t)
		return;
	bm_botfill_t = time + 2;
	want = autocvar_bm_botfill;
	if (BM_DummyMap () && want < 4)
		want = 4;
	if (want <= 0)
		return;
	n = BM_CountPlayers ();
	if (n < 1 && !autocvar_bm_botfill_empty)
		return;		// nobody here yet: don't fill an empty server
	if (n < want)
		BotConnect (0, 0, cvar ("skill"));
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

	if (!cvar ("sv_cheats"))
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
};

// every frame from W_WeaponFrame: while the server overrides your speed the client's own movement guess is wrong by a whole ping
// and each correction snaps you back, so it stops guessing (bm_nopredict 0 puts it back)
void() BM_PredictFrame =
{
	if (autocvar_bm_nopredict && (self.jp_on || time < self.goo_slow || self.ltg_shock > 0 || time < self.milk_freeze || self.milk_slip))
		self.disableclientprediction = 1;
	else
		self.disableclientprediction = 0;
};
