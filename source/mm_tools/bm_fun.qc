/*
================
KILL ANNOUNCER (Bakersfield LAN rules, Combat+ only)

The room hears every big moment, not just the weapons. Lines go to everyone (bprint, gold like the DOMINATING
line) and most come with a clip from sound/funny, played to everyone at full volume. One clip at a time: a clip
waits until bm_fun_gap seconds after the last one, so they never pile up over each other or the pickle's shout.

	FIRST BLOOD			the first player-on-player kill of the map
	KILLING SPREE		3 kills without dying; RAMPAGE at 5; GODLIKE at 8 (each said once per streak)
	ended X's spree		killing someone with a streak of 3+
	DOUBLE / TRIPLE /	kills within bm_fun_multi seconds of each other
	MULTI KILL x N
	REVENGE				killing the player who killed you last
	cheer				(clip only) the player in last place gets a kill, bm_fun_cheer of the time
	gib / big hit		(clip only) a gib, a HIGH-tier bonk, a 300+ sniper shot
	durr				(clip only) a suicide or a death by the map
Most clips can come from sound/larry instead (Larry McCart prank call), bm_fun_larry of the time.

Hooked from Underdog_Killed (combat.qc Killed runs it for every player death, before the obituary).
set bm_fun 0 switches the lines and the clips off. Streaks reset on death, everything resets with the map.
================
*/

// ---------------------------------------------------------------- the clips: change them here
string	BMF_FIRSTBLOOD	= "funny/wun.wav";
string	BMF_SPREE		= "funny/goooood.wav";
string	BMF_RAMPAGE		= "funny/quakeahh.wav";		// RAMPAGE and GODLIKE
string	BMF_ENDED		= "funny/huh.wav";
string	BMF_MULTI		= "funny/wewe.wav";
string	BMF_REVENGE		= "funny/heh.wav";
string	BMF_CHEER		= "funny/hearh.wav";
string	BMF_GIB			= "funny/quakeahh.wav";
string	BMF_BIGHIT1		= "funny/soleet1.wav";
string	BMF_BIGHIT2		= "funny/soleet2.wav";
string	BMF_SELFKILL	= "funny/durr.wav";

// Larry McCart prank-call clips (sound/larry, cut from the call in source/sound_bank): each stands in for a stock clip
// bm_fun_larry of the time
string	BMF_L_FIRSTBLOOD	= "larry/love_to_play_quake.wav";	// "I'd love to play Quake"
string	BMF_L_MULTI			= "larry/double_good.wav";			// "Double good"
string	BMF_L_MULTI4		= "larry/octogood.wav";				// "Octogood" (4+ kills)
string	BMF_L_ENDED			= "larry/interesting.wav";			// "Hmm, interesting."
string	BMF_L_REVENGE		= "larry/cigarettes.wav";			// "Cigarettes."
string	BMF_L_CHEER			= "larry/giggle_hacks.wav";			// "Giggle hacks!"
string	BMF_L_GIB			= "larry/play_with_knives.wav";		// "We get to play with knives"
string	BMF_L_BIGHIT		= "larry/banana_cannon.wav";		// "Banana cannon"
string	BMF_L_SELFKILL		= "larry/it_wont_boot.wav";			// "It won't boot."

void() BM_Fun_Precache =
{
	if (bm_fun_precached)
		return;
	bm_fun_precached = TRUE;
	precache_sound (BMF_FIRSTBLOOD);
	precache_sound (BMF_SPREE);
	precache_sound (BMF_RAMPAGE);
	precache_sound (BMF_ENDED);
	precache_sound (BMF_MULTI);
	precache_sound (BMF_REVENGE);
	precache_sound (BMF_CHEER);
	precache_sound (BMF_GIB);
	precache_sound (BMF_BIGHIT1);
	precache_sound (BMF_BIGHIT2);
	precache_sound (BMF_SELFKILL);
	precache_sound (BMF_L_FIRSTBLOOD);
	precache_sound (BMF_L_MULTI);
	precache_sound (BMF_L_MULTI4);
	precache_sound (BMF_L_ENDED);
	precache_sound (BMF_L_REVENGE);
	precache_sound (BMF_L_CHEER);
	precache_sound (BMF_L_GIB);
	precache_sound (BMF_L_BIGHIT);
	precache_sound (BMF_L_SELFKILL);
};

// the stock clip, or the Larry one bm_fun_larry of the time
string(string stock, string larry) BM_Fun_Pick =
{
	if (random () < autocvar_bm_fun_larry)
		return larry;
	return stock;
};

// a clip for everyone, from e, if the last one was bm_fun_gap seconds ago (newbie.wav goes through here too)
void(entity e, string clip) BM_Fun_Say =
{
	if (time < bm_fun_say_t)
		return;
	bm_fun_say_t = time + autocvar_bm_fun_gap;
	if (clip == "funny/newbie.wav")
		precache_sound ("funny/newbie.wav");
	else
		BM_Fun_Precache ();
	if (bm_cvar_dev)
		dprint ("announcer: ", clip, " (", e.netname, ")\n");
	sound (e, CHAN_AUTO, clip, 1, ATTN_NONE);
};

// Underdog_Killed: every deathmatch player death, before the frag and the obituary
void(entity targ, entity attacker) BM_Fun_Killed =
{
	local float n, tier, bigshot;
	local string splash;

	if (!deathmatch || !autocvar_bm_fun || targ.classname != "player")
		return;
	splash = "";

	// the victim's streak is over
	if (attacker.classname == "player" && attacker != targ && targ.bm_streak >= 3)
	{
		bprint ("^3", attacker.netname, " ended ", targ.netname, "'s ", ftos (targ.bm_streak), "-kill spree\n");
		splash = strcat ("^3BUZZKILL! Ended ", targ.netname, "'s spree!");
		BM_Fun_Say (attacker, BM_Fun_Pick (BMF_ENDED, BMF_L_ENDED));
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
		BM_Fun_Say (targ, BM_Fun_Pick (BMF_SELFKILL, BMF_L_SELFKILL));		// suicides, lava, falls: the room is told
		return;
	}

	// first blood
	if (!bm_fun_first)
	{
		bm_fun_first = TRUE;
		bprint ("^3", attacker.netname, " drew FIRST BLOOD\n");
		splash = "^1FIRST BLOOD!";
		BM_Fun_Say (attacker, BM_Fun_Pick (BMF_FIRSTBLOOD, BMF_L_FIRSTBLOOD));
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
	if (n >= 4)
		BM_Fun_Say (attacker, BM_Fun_Pick (BMF_MULTI, BMF_L_MULTI4));
	else if (n >= 2)
		BM_Fun_Say (attacker, BM_Fun_Pick (BMF_MULTI, BMF_L_MULTI));

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
		if (tier == 1)
			BM_Fun_Say (attacker, BMF_SPREE);
		else
			BM_Fun_Say (attacker, BMF_RAMPAGE);
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
		BM_Fun_Say (attacker, BM_Fun_Pick (BMF_REVENGE, BMF_L_REVENGE));
	}

	if (splash != "" && attacker.ishuman == 1 && (!autocvar_bm_bounty || targ.ud_heat < 4))
		centerprint (attacker, splash);

	// the room cheers for last place (checked before this frag is added, so "last" means last)
	if (Underdog_IsLast (attacker) && random () < autocvar_bm_fun_cheer)
		BM_Fun_Say (attacker, BM_Fun_Pick (BMF_CHEER, BMF_L_CHEER));

	// a gib, a HIGH bonk, a big sniper shot
	bigshot = FALSE;
	if (sn_inflicting && attacker.sn_heat >= 300)
		bigshot = TRUE;
	if (attacker.weapon == IT_AXE && attacker.hm_tier == 3 && !fg_inflicting && !mm_inflicting && !bn_inflicting && !sg_inflicting && !sn_inflicting)
		bigshot = TRUE;
	if (targ.health < -40)
		BM_Fun_Say (attacker, BM_Fun_Pick (BMF_GIB, BMF_L_GIB));
	else if (bigshot)
	{
		if (random () < 0.5)
			BM_Fun_Say (attacker, BM_Fun_Pick (BMF_BIGHIT1, BMF_L_BIGHIT));
		else
			BM_Fun_Say (attacker, BMF_BIGHIT2);
	}
};
