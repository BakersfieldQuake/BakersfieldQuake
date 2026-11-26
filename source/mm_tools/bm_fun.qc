/*
================
KILL ANNOUNCER (Bakersfield LAN rules, Combat+ only)

The room reads every big moment (text only: the voice clips were removed 2026-11-26, they sounded like random
noises). Lines go to everyone (bprint, gold like the DOMINATING line).

	FIRST BLOOD			the first player-on-player kill of the map
	KILLING SPREE		3 kills without dying; RAMPAGE at 5; GODLIKE at 8 (each said once per streak)
	ended X's spree		killing someone with a streak of 3+
	DOUBLE / TRIPLE /	kills within bm_fun_multi seconds of each other
	MULTI KILL x N
	REVENGE				killing the player who killed you last

Hooked from Underdog_Killed (combat.qc Killed runs it for every player death, before the obituary).
set bm_fun 0 switches the lines off. Streaks reset on death, everything resets with the map.
================
*/

// Underdog_Killed: every deathmatch player death, before the frag and the obituary
void(entity targ, entity attacker) BM_Fun_Killed =
{
	local float n, tier;
	local string splash;

	if (!deathmatch || !autocvar_bm_fun || targ.classname != "player")
		return;
	splash = "";

	// the victim's streak is over
	if (attacker.classname == "player" && attacker != targ && targ.bm_streak >= 3)
	{
		bprint ("^3", attacker.netname, " ended ", targ.netname, "'s ", ftos (targ.bm_streak), "-kill spree\n");
		splash = strcat ("^3BUZZKILL! Ended ", targ.netname, "'s spree!");
	}
	targ.bm_streak = 0;
	targ.bm_streak_tier = 0;
	targ.bm_multi_n = 0;
	if (attacker.classname == "player" && attacker != targ)
		targ.bm_killer = attacker;
	else
		targ.bm_killer = world;

	if (attacker.classname != "player" || attacker == targ)
	{
		return;
	}

	// first blood
	if (!bm_fun_first)
	{
		bm_fun_first = TRUE;
		bprint ("^3", attacker.netname, " drew FIRST BLOOD\n");
		splash = "^1FIRST BLOOD!";
	}

	// kills in a burst
	if (time - attacker.bm_multi_t < autocvar_bm_fun_multi)
		attacker.bm_multi_n = attacker.bm_multi_n + 1;
	else
		attacker.bm_multi_n = 1;
	attacker.bm_multi_t = time;
	n = attacker.bm_multi_n;
	if (n == 2)
	{
		bprint ("^3", attacker.netname, ": DOUBLE KILL\n");
		splash = "^xfb2DOUBLE KILL!";
	}
	else if (n == 3)
	{
		bprint ("^3", attacker.netname, ": TRIPLE KILL\n");
		splash = "^xf91TRIPLE KILL!";
	}
	else if (n >= 4)
	{
		bprint ("^3", attacker.netname, ": MULTI KILL x", ftos (n), "\n");
		splash = strcat ("^1MULTI KILL x", ftos (n), "!");
	}

	// the streak
	attacker.bm_streak = attacker.bm_streak + 1;
	tier = 0;
	if (attacker.bm_streak >= 8)
		tier = 3;
	else if (attacker.bm_streak >= 5)
		tier = 2;
	else if (attacker.bm_streak >= 3)
		tier = 1;
	if (tier > attacker.bm_streak_tier)
	{
		attacker.bm_streak_tier = tier;
		if (tier == 3)
		{
			bprint ("^3", attacker.netname, " is GODLIKE (", ftos (attacker.bm_streak), " kills)\n");
			if (splash != "")
				splash = strcat (splash, "\n^1GODLIKE! (", ftos (attacker.bm_streak), " KILLS)");
			else
				splash = strcat ("^1GODLIKE! (", ftos (attacker.bm_streak), " KILLS)");
		}
		else if (tier == 2)
		{
			bprint ("^3", attacker.netname, " is on a RAMPAGE (", ftos (attacker.bm_streak), " kills)\n");
			if (splash != "")
				splash = strcat (splash, "\n^xf80RAMPAGE! (", ftos (attacker.bm_streak), " KILLS)");
			else
				splash = strcat ("^xf80RAMPAGE! (", ftos (attacker.bm_streak), " KILLS)");
		}
		else
		{
			bprint ("^3", attacker.netname, " is on a KILLING SPREE\n");
			if (splash != "")
				splash = strcat (splash, "\n^3KILLING SPREE! (3)");
			else
				splash = "^3KILLING SPREE! (3)";
		}
	}

	// revenge
	if (attacker.bm_killer == targ)
	{
		attacker.bm_killer = world;
		bprint ("^3", attacker.netname, " got REVENGE on ", targ.netname, "\n");
		if (splash != "")
			splash = strcat (splash, "\n^2REVENGE on ", targ.netname, "!");
		else
			splash = strcat ("^2REVENGE on ", targ.netname, "!");
	}

	if (splash != "" && attacker.ishuman == 1 && (!autocvar_bm_bounty || targ.ud_heat < 4))
	{
		centerprint (attacker, splash);
		attacker.bm_fun_cp_t = time;
	}
};
