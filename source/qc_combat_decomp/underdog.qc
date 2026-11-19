/*
================
UNDERDOG (Bakersfield LAN rules, deathmatch only)

Keeps scores close by scaling with the frag gap. Nothing here makes the leader weaker; it makes them
easy to find, and makes the people behind them tougher.

Recomputed twice a second (Underdog_Update, from StartFrame), over every player (bots too):
	heat    = your frags - the average of everyone else's
	deficit = the top score - your frags
Gaps of 0-1 do nothing.

LEADER (anyone 2+ frags ahead of the pack), stacking as heat grows:
	heat 2+		gold glow around them, bigger with every frag
	heat 4+		killing them is worth +1 bonus frag (bm_bounty)
	heat 6+		a beacon over their head that shows through walls, and a "hunt them" announcement
	heat 10+	their whole body shows through walls
UNDERDOG: frags alone miss a player being farmed, because their deaths are shared out among everyone else (7 deaths
with 0 kills is only 3-4 frags behind with 4 players). So boost is three signals, and any one can push it up:
	boost	= 1 - (1 - streak) (1 - kd) (1 - gap), 0..1
	streak	= (deaths in a row - 1) / (full - 1)	full = bm_ud_streak: +1 in a 1v1, -1 at 6+ players, -2 at 10+
	kd		= 0.6 * (1 - K/D) / 0.75				K/D = (kills + 4) / (deaths + 4); nothing until 2 deaths
	gap		= (frags behind - 1) / span				span = bm_ud_span * (1/3 + 2/3 / (players - 1)) + 0.15 * top score
A kill halves the streak rather than clearing it, so one lucky kill doesn't drop you back to nothing. Being ahead fades
the boost out: all of it at the pack's average, none at 2 frags above it or in first place. Bots stop at bm_ud_botcap.
	spawn health 100 -> 250 (max_health too, so regen fills it)
	spawn armor: everyone gets green 100 (bm_spawnarmor); boost bm_ud_yellow+ yellow 150, bm_ud_red+ red 200, 0.9+ red 250
	health regen starts 5 -> 1.5 s after a hit and runs 10 -> 50 per second; armor regen up to 4x
	giant slayer: up to +bm_giantslayer damage against anyone with more frags, up to -bm_ud_resist damage from them
	fun guns reload up to 50% faster
	boost 0.5+: a free power-up after a real death (Quad, invisibility or a pentagram, 5 s); 0.75+: Quad or pentagram, 8 s
	boost 0.7+: BLUE SHELL - your next Mega Man ignores everyone else and hunts the leader
	streak = full: LAST STAND - Quad and a pentagram together for 10 s, full health and armor, every spawn until you get a kill
Suicides, lava and falls never change anyone's score (client.qc) and don't count as deaths here, so nobody climbs this
by dying on purpose; a death to a player or monster is what earns the next spawn's power-up.

"set bm_handicap 0" switches all of it off. Compiled before combat.qc; hooked by patch_gameplay_combat.py
and patch_lan_combat.py.
================
*/

float() Underdog_On =
{
	return (deathmatch && autocvar_bm_handicap);
};

// the player with the most frags, other than 'not' (world if nobody else is playing)
entity(entity not) Underdog_Leader =
{
	local entity e, best;

	best = world;
	e = bm_player_head;
	while (e)
	{
		if (e != not && (!best || e.frags > best.frags))
			best = e;
		e = e.bm_player_next;
	}
	return best;
};

float(float heat) Underdog_Tier =
{
	if (heat >= 10)
		return 4;
	if (heat >= 6)
		return 3;
	if (heat >= 4)
		return 2;
	if (heat >= 2)
		return 1;
	return 0;
};

// T_Damage: giant slayer, and the same fight from the other end: hits from anyone with more frags hurt less
float(entity targ, entity attacker, float damage) Underdog_Damage =
{
	if (!Underdog_On () || attacker == targ)
		return damage;
	if (attacker.classname != "player" || targ.classname != "player")
		return damage;
	if (attacker.ud_boost > 0 && targ.frags > attacker.frags)
		damage = damage * (1 + autocvar_bm_giantslayer * attacker.ud_boost);
	if (targ.ud_boost > 0 && attacker.frags > targ.frags && damage < 1000)		// telefrags still go through
		damage = damage * (1 - autocvar_bm_ud_resist * targ.ud_boost);
	return damage;
};

// a slot's numbers die with its player (ClientDisconnect): bots reuse their edict without clearing it
void(entity p) Underdog_Reset =
{
	local entity e;

	p.ud_streak = 0;
	p.ud_kills = 0;
	p.ud_deaths = 0;
	p.ud_earned = FALSE;
	// the computed boost / leader numbers too: a bot reusing the slot spawned with the old boost (and its gold glow)
	p.ud_boost = 0;
	p.ud_heat = 0;
	p.ud_tier = 0;
	p.ud_lead = 0;
	p.ud_deficit = 0;
	p.ud_blueshell = FALSE;
	// the kill-streak announcer's numbers too (bm_fun.qc), and nobody may take REVENGE on the next one in this slot
	p.bm_streak = 0;
	p.bm_streak_tier = 0;
	p.bm_multi_n = 0;
	p.bm_multi_t = 0;
	p.bm_killer = world;
	e = bm_player_head;
	while (e)
	{
		if (e.bm_killer == p)
			e.bm_killer = world;
		e = e.bm_player_next;
	}
};

// is 'p' in last place? Nobody else has fewer frags, and somebody has more (so a fresh 0-0 game has no loser)
float(entity p) Underdog_IsLast =
{
	local entity e;
	local float ahead;

	ahead = FALSE;
	e = bm_player_head;
	while (e)
	{
		if (e != p)
		{
			if (e.frags < p.frags)
				return FALSE;
			if (e.frags > p.frags)
				ahead = TRUE;
		}
		e = e.bm_player_next;
	}
	return ahead;
};

// Killed (before the obituary adds the normal frag): the bounty, and the newbie taunt for last place
void(entity p) Underdog_ClearFx;

void() Underdog_PinataTouch =
{
	local entity os;

	if (other.classname != "player" || other.health <= 0 || time < self.cnt)
		return;
	if (other.health < 220)
	{
		other.health = other.health + 75;
		if (other.health > 220)
			other.health = 220;
	}
	other.items = other.items | IT_QUAD;
	other.super_time = 1;
	if (other.super_damage_finished < time + 6)
		other.super_damage_finished = time + 6;
	os = self;
	self = other;
	BM_FillAll ();
	self = os;
	other.jb_cooldown_t = 0;
	sound (other, CHAN_ITEM, "items/damage.wav", 1, ATTN_NORM);
	particle (self.origin, '0 0 140', 192, 40);
	if (other.ishuman == 1)
		centerprint (other, "^3BOUNTY LOOT! +75 HP + 6s QUAD + FULL TOYS!");
	bprint ("^3", other.netname, " scooped up the BOUNTY PINATA LOOT!\n");
	remove (self);
};

void(vector org) Underdog_SpawnPinata =
{
	local entity orb;
	local vector rv;

	orb = spawn ();
	orb.classname = "ud_pinata";
	orb.movetype = MOVETYPE_TOSS;
	orb.solid = SOLID_TRIGGER;
	setmodel (orb, "progs/quaddama.mdl");
	setsize (orb, '-16 -16 -24', '16 16 32');
	setorigin (orb, org + '0 0 24');
	rv = randomvec ();
	rv_z = 0;
	orb.velocity = rv * 55 + '0 0 235';
	orb.avelocity = '0 160 0';
	orb.scale = 0.85;
	orb.effects = EF_FULLBRIGHT;
	orb.pflags = PFLAGS_FULLDYNAMIC | PFLAGS_NOSHADOW | PFLAGS_CORONA;
	orb.light_lev = 200;
	orb.color = '1.0 0.953 0.106';		// gold (palette 192), no shadow pass or double EF_DIMLIGHT
	orb.cnt = time + 0.35;
	orb.touch = Underdog_PinataTouch;
	orb.think = SUB_Remove;
	orb.nextthink = time + 15;
};

float() Underdog_PulseOn =
{
	local float cyc;

	cyc = time - 4.5 * floor (time / 4.5);
	return (cyc < 1.1);
};

void(entity targ, entity attacker) Underdog_Killed =
{
	if (!deathmatch || targ.classname != "player")
		return;
	// a dead player's PostThink returns before BM_LifeFrame, so Underdog_FxFrame can't take the leader's glow, beacon and
	// x-ray copy down: they hung frozen where the leader died until the respawn
	if (targ.ud_aura)
		Underdog_ClearFx (targ);
	BM_Fun_Killed (targ, attacker);		// first blood, sprees, revenge... (bm_fun.qc)
	targ.ud_earned = FALSE;
	if (attacker != targ && (attacker.classname == "player" || (attacker.flags & FL_MONSTER)))
	{
		targ.ud_deaths = targ.ud_deaths + 1;
		targ.ud_streak = targ.ud_streak + 1;
		targ.ud_earned = TRUE;
	}
	if (attacker.classname != "player" || attacker == targ)
		return;
	attacker.ud_kills = attacker.ud_kills + 1;
	attacker.ud_streak = floor (attacker.ud_streak / 2);
	// Last Stand ends 2s after scoring a kill so it stays a comeback spark, not a multi-wipe godmode sweep
	if (attacker.invincible_finished > time + 2 && attacker.super_damage_finished > time + 2)
	{
		attacker.invincible_finished = time + 2;
		attacker.super_damage_finished = time + 2;
	}
	ud_next_t = 0;
	if (Underdog_IsLast (targ) && random () < autocvar_bm_newbie)
		BM_Fun_Say (attacker, "funny/newbie.wav");
	if (!Underdog_On ())
		return;
	if (autocvar_bm_bounty && targ.ud_heat >= 4)
	{
		attacker.frags = attacker.frags + 1;
		bprint ("^3", attacker.netname, " POPPED ", targ.netname, "'s BOUNTY PINATA! (+1 BONUS FRAG + LOOT ORB!)\n");
		if (attacker.ishuman == 1)
			centerprint (attacker, strcat ("^3BOUNTY PINATA! +1 BONUS FRAG!\n^2Took down ", targ.netname));
		sound (attacker, CHAN_AUTO, "misc/talk.wav", 1, ATTN_NONE);
		particle (targ.origin + '0 0 24', '0 0 180', 192, 64);
		particle (targ.origin + '0 0 32', '0 0 220', 41, 48);
		Underdog_SpawnPinata (targ.origin);
		ud_next_t = 0;
	}
};

// --------------------------------------------------------------- leader effects
// a free-standing entity (not attached: attached entities vanish with their parent when the parent is
// out of sight, and the whole point is seeing them through walls). BM_EF_NODEPTHTEST also skips the
// server's visibility culling, so these are sent to everyone.
entity(entity p, string m) Underdog_FxEnt =
{
	local entity e;

	e = spawn ();
	e.classname = "ud_fx";
	e.owner = p;
	e.movetype = MOVETYPE_NONE;
	e.solid = SOLID_NOT;
	setmodel (e, m);
	setsize (e, '0 0 0', '0 0 0');
	e.nodrawtoclient = p;		// the leader doesn't need to see their own beacon
	return e;
};

void(entity p) Underdog_ClearFx =
{
	if (p.ud_aura)
	{
		if (p.ud_aura.enemy)
			remove (p.ud_aura.enemy);
		remove (p.ud_aura);
		p.ud_aura = world;
	}
};

// every frame for living players (BM_LifeFrame): keep the effects glued to the leader.
// The glow sits on the follower entity, not the player, so the leader's own screen doesn't turn gold
// (nodrawtoclient also hides its light from them).
void() Underdog_FxFrame =
{
	local entity b, x;
	local float sn;

	if (!Underdog_On () || self.ud_tier < 1 || self.health <= 0)
	{
		if (self.ud_aura)
			Underdog_ClearFx (self);
		return;
	}

	if (!self.ud_aura)
	{
		self.ud_aura = Underdog_FxEnt (self, "progs/s_dotmed_yell.spr");
		self.ud_fx_t = 0;
	}
	if (time < self.ud_fx_t)
		return;
	self.ud_fx_t = time + 0.05;
	b = self.ud_aura;
	b.pflags = PFLAGS_FULLDYNAMIC | PFLAGS_NOSHADOW | PFLAGS_CORONA;
	b.color = '1.0 0.953 0.106';		// gold (palette 192), no shadow cubemap pass
	b.light_lev = min (80 + 25 * self.ud_heat, 400);
	if (self.ud_tier >= 3)
	{
		// periodic radar beacon: pulses through walls for 1.1s every 4.5s so ambushes stay alive!
		if (Underdog_PulseOn ())
			b.effects = BM_EF_NODEPTHTEST | EF_FULLBRIGHT | EF_ADDITIVE;
		else
			b.effects = EF_FULLBRIGHT | EF_ADDITIVE;
		sn = sin (time * 6);		// sin is a __variant in Combat+'s defs
		b.scale = 4 + sn;
		b.alpha = 1;
		setorigin (b, self.origin + '0 0 52');
	}
	else
	{
		// just the light
		b.effects = 0;
		b.scale = 0.1;
		b.alpha = 0.01;
		setorigin (b, self.origin + '0 0 16');
	}

	if (self.ud_tier >= 4)
	{
		if (!b.enemy)
		{
			b.enemy = Underdog_FxEnt (self, "progs/player_id1.mdl");
			b.enemy.colormod = '2 1.5 0.3';
		}
		x = b.enemy;
		if (Underdog_PulseOn ())
		{
			x.effects = BM_EF_NODEPTHTEST | EF_FULLBRIGHT | EF_ADDITIVE;
			x.alpha = 0.45;
		}
		else
		{
			x.effects = EF_FULLBRIGHT | EF_ADDITIVE;
			x.alpha = 0.22;
		}
		x.modelindex = self.modelindex;
		x.frame = self.frame;
		x.skin = self.skin;
		x.angles = self.angles;
		setorigin (x, self.origin);
	}
	else if (b.enemy)
	{
		remove (b.enemy);
		b.enemy = world;
	}
};

// how far this player's game has gone wrong, 0..1 (the header has the sums). n = players, top = the top score;
// e.ud_heat, e.ud_deficit and e.ud_lead are already fresh.
float(entity e, float n, float top) Underdog_Boost =
{
	local float a, k, g, b;

	e.ud_full = autocvar_bm_ud_streak;
	if (n <= 2)
		e.ud_full = e.ud_full + 1;
	if (n >= 6)
		e.ud_full = e.ud_full - 1;
	if (n >= 10)
		e.ud_full = e.ud_full - 1;
	e.ud_full = max (2, e.ud_full);

	if (e.ud_lead)
		return 0;
	a = bound (0, (e.ud_streak - 1) / (e.ud_full - 1), 1);
	k = 0;
	if (e.ud_deaths >= 2)
		k = 0.6 * bound (0, (1 - (e.ud_kills + 4) / (e.ud_deaths + 4)) / 0.75, 1);
	g = bound (0, (e.ud_deficit - 1) / (autocvar_bm_ud_span * (1 / 3 + (2 / 3) / (n - 1)) + 0.15 * max (0, top)), 1);
	b = 1 - (1 - a) * (1 - k) * (1 - g);
	if (e.ud_heat > 0)
		b = b * bound (0, 1 - e.ud_heat / 2, 1);		// a good player on a bad run is not an underdog
	if (e.ishuman != 1)
		b = min (b, autocvar_bm_ud_botcap);
	return bound (0, b, 1);
};

// twice a second, from StartFrame
void() Underdog_Update =
{
	local entity e;
	local float n, sum, top, low, t, besth;

	if (time < ud_next_t)
		return;
	ud_next_t = time + 0.5;

	n = 0;
	sum = 0;
	top = -99999;
	low = 99999;
	e = bm_player_head;
	while (e)
	{
		n = n + 1;
		sum = sum + e.frags;
		if (e.frags > top)
			top = e.frags;
		if (e.frags < low)
			low = e.frags;
		e = e.bm_player_next;
	}

	ud_leader = world;
	besth = 0;
	e = bm_player_head;
	while (e)
	{
		e.ud_lead = (n >= 2 && e.frags >= top && top > low);		// first place, with somebody behind
		if (!Underdog_On () || n < 2)
		{
			e.ud_heat = 0;
			e.ud_deficit = 0;
			e.ud_boost = 0;
		}
		else
		{
			e.ud_heat = e.frags - (sum - e.frags) / (n - 1);
			e.ud_deficit = top - e.frags;
			e.ud_boost = Underdog_Boost (e, n, top);
		}
		t = Underdog_Tier (e.ud_heat);
		if (t >= 4 && e.ud_tier < 4)
			bprint ("^3", e.netname, " is UNSTOPPABLE - radar sweeps locking onto them!\n");
		else if (t >= 3 && e.ud_tier < 3)
			bprint ("^3", e.netname, " is DOMINATING - radar pings active, hunt the Pinata!\n");
		e.ud_tier = t;
		if (e.ud_heat >= 2 && e.ud_heat > besth)
		{
			besth = e.ud_heat;
			ud_leader = e;
		}
		e = e.bm_player_next;
	}
};

// no-op: the bounty lives in Underdog_Update / Underdog_Killed now (kept for the existing hook)
void() Underdog_UpdateBounty =
{
};

// health regen tuning (client.qc regen block)
float() Underdog_RegenDelay =
{
	return autocvar_bm_regen_delay - (autocvar_bm_regen_delay - 1.5) * self.ud_boost;
};

float() Underdog_RegenRate =
{
	return autocvar_bm_regen_rate + (50 - autocvar_bm_regen_rate) * self.ud_boost;
};

// armor regeneration (client.qc PlayerPostThink, same wait after a hit as health): slow, quicker the bigger your boost,
// and none at all while you are in first place. It tops armor back up to what the armor's colour holds (green 100,
// yellow 150, red 200); with none left it brings back green.
void(float dt) Underdog_ArmorRegen =
{
	local float cap, rate, ar;

	if (!deathmatch || !autocvar_bm_armor_regen || self.health <= 0 || self.deadflag || self.ud_lead)
	{
		self.bm_ar_frac = 0;
		return;
	}
	if (self.items & IT_ARMOR3)
		cap = 200;
	else if (self.items & IT_ARMOR2)
		cap = 150;
	else
		cap = max (100, autocvar_bm_spawnarmor);
	if (self.armorvalue >= cap || time <= self.rg_hurt_t + Underdog_RegenDelay ())
	{
		self.bm_ar_frac = 0;
		return;
	}
	rate = autocvar_bm_armor_rate * (1 + 3 * self.ud_boost);
	self.bm_ar_frac = self.bm_ar_frac + rate * dt;
	if (self.bm_ar_frac < 1)
		return;
	ar = floor (self.bm_ar_frac);
	self.bm_ar_frac = self.bm_ar_frac - ar;
	if (!(self.items & (IT_ARMOR1 | IT_ARMOR2 | IT_ARMOR3)))
	{
		self.items = self.items | IT_ARMOR1;
		self.armortype = 0.3;
	}
	self.armorvalue = min (cap, self.armorvalue + ar);
};

// fun-gun reload time multiplier
float(entity p) Underdog_AmmoRate =
{
	return 1 - 0.5 * p.ud_boost;
};

void() Underdog_GiveQuad =
{
	self.items = self.items | IT_QUAD;
	self.super_time = 1;
};

void() Underdog_GivePent =
{
	self.items = self.items | IT_INVULNERABILITY;		// set it the way the pentagram pickup does
	self.invincible_time = 1;
};

// PutClientInServer: the spawn boosts
void() Underdog_Spawn =
{
	local float b, hp, ar, r, earned, last, n, sum, top, low, listed;
	local entity best, e;

	earned = self.ud_earned;
	self.ud_earned = FALSE;
	self.ud_level = 0;
	self.ud_blueshell = FALSE;
	self.max_health = 100;
	Underdog_ClearFx (self);
	BM_SpawnArmor ();		// green 100 for everyone (bm_match.qc)
	if (!Underdog_On ())
		return;
	ud_next_t = 0;
	Underdog_Update ();		// fresh numbers for this spawn
	// a player who just connected (a new bot) is not in bm_player_head yet: StartFrame built it before the classname
	// was set, so Underdog_Update skipped it. Work its numbers out here, counting it in.
	listed = FALSE;
	n = 1;
	sum = self.frags;
	top = self.frags;
	low = self.frags;
	e = bm_player_head;
	while (e)
	{
		if (e == self)
			listed = TRUE;		// Underdog_Update already did it
		n = n + 1;
		sum = sum + e.frags;
		if (e.frags > top)
			top = e.frags;
		if (e.frags < low)
			low = e.frags;
		e = e.bm_player_next;
	}
	if (!listed)
	{
		self.ud_lead = (n >= 2 && self.frags >= top && top > low);
		self.ud_heat = 0;
		self.ud_deficit = 0;
		self.ud_boost = 0;
		if (n >= 2)
		{
			self.ud_heat = self.frags - (sum - self.frags) / (n - 1);
			self.ud_deficit = top - self.frags;
			self.ud_boost = Underdog_Boost (self, n, top);
		}
		self.ud_tier = Underdog_Tier (self.ud_heat);
	}
	b = self.ud_boost;
	if (b <= 0)
		return;
	last = (earned && self.ishuman == 1 && self.ud_streak >= self.ud_full);
	if (last)
		b = 1;		// the guarantee: it can't be diluted by a leader fade or anything else on this spawn

	hp = 100 + floor (80 * b);
	self.max_health = hp;
	if (self.health < hp)
		self.health = hp;
	// armor by boost: capped at 150 Yellow Armor so underdogs are offensive chaos engines, not 1,000-EHP bullet sponges
	ar = 0;
	if (b >= autocvar_bm_ud_yellow)
	{
		ar = 125;
		if (b >= autocvar_bm_ud_red)
			ar = 150;
		self.items = self.items - (self.items & (IT_ARMOR1 | IT_ARMOR2 | IT_ARMOR3));
		self.items = self.items | IT_ARMOR2;
		self.armortype = 0.6;
	}
	if (ar > self.armorvalue)
		self.armorvalue = ar;
	self.ud_level = 1 + floor (b * 4);
	if (earned && b >= 0.60)
	{
		BM_FillAll ();
		self.jb_cooldown_t = 0;
	}

	// power-ups only after a real death, so `kill` can't re-roll them
	if (last)
	{
		Underdog_GiveQuad ();
		self.super_damage_finished = time + 7;
		Underdog_GivePent ();
		self.invincible_finished = time + 7;
	}
	else if (earned && b >= 0.75)
	{
		if (random () < 0.5)
		{
			Underdog_GiveQuad ();
			self.super_damage_finished = time + 8;
		}
		else
		{
			Underdog_GivePent ();
			self.invincible_finished = time + 8;
		}
	}
	else if (earned && b >= 0.5)
	{
		r = random () * 3;
		if (r < 1)
		{
			Underdog_GiveQuad ();
			self.super_damage_finished = time + 5;
		}
		else if (r < 2)
		{
			self.items = self.items | IT_INVISIBILITY;
			self.invisible_time = 1;
			self.invisible_finished = time + 5;
		}
		else
		{
			Underdog_GivePent ();
			self.invincible_finished = time + 5;
		}
	}
	if (b >= 0.7)
		self.ud_blueshell = TRUE;

	if (last)
	{
		bprint ("^3", self.netname, " is on LAST STAND - ", ftos (self.ud_streak), " deaths in a row, Quad and pentagram for 7 seconds!\n");
		sound (self, CHAN_AUTO, "misc/talk.wav", 1, ATTN_NONE);
		centerprint (self, "^3LAST STAND: Quad + Pentagram (7s)");
		return;
	}
	best = Underdog_Leader (self);
	if (self.ud_blueshell && best)
		centerprint (self, strcat ("^5Blue Shell ready - Mega Man hunts ", best.netname));
};

// Mega Man launch: spend a 3D Flying Blue Shell on this one!
void(entity m) Underdog_BlueShell =
{
	local entity t;

	if (!self.ud_blueshell)
		return;
	t = Underdog_Leader (self);
	if (!t || t.frags <= self.frags)
		return;
	self.ud_blueshell = FALSE;
	m.ud_hunt = t;
	m.ud_shell_stage = 1;
	m.ud_shell_t = time + 18;
	m.movetype = MOVETYPE_NOCLIP;
	m.solid = SOLID_NOT;
	m.takedamage = DAMAGE_NO;
	m.scale = 1.35;
	m.effects = m.effects | 64 | 8 | 512;		// EF_BLUE + EF_DIMLIGHT + EF_FULLBRIGHT
	sound (t, CHAN_AUTO, "weapons/megahorn.wav", 1, ATTN_NORM);
	centerprint (self, strcat ("^5FLYING BLUE SHELL airborne -> ", t.netname, "!"));
	centerprint (t, "^1INCOMING BLUE SHELL! LISTEN FOR THE HORN!");
	bprint ("^5", self.netname, " launched a FLYING BLUE SHELL at ", t.netname, "!\n");
};
