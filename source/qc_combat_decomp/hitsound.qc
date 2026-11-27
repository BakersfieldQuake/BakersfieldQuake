#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
HIT SOUNDS (Combat+)

When your shot lands on another player or a monster you hear a short tick, only you. Small hits tick high,
big ones lower. Pellets and splash landing in the same moment only tick once. Called from T_Damage
(patch_gameplay_combat.py) after the damage has been taken off, so teammates under teamplay 1 never tick.
================
*/

float	HS_GAP		= 0.12;		// shortest time between two ticks for the same attacker

.float	hs_time;			// player: when they may hear the next tick

void() HitSound_Precache =
{
	precache_sound ("misc/mmhit1.wav");
	precache_sound ("misc/mmhit2.wav");
	precache_sound ("misc/mmhit3.wav");
};

void(entity attacker, float tier) HitSound_Emit =
{
	local float seq;

	if (!attacker || attacker.ishuman != 1)
		return;
	seq = attacker.bm_hs_seq + 1;
	if (seq > 63)
		seq = 1;
	attacker.bm_hs_seq = seq;
	attacker.bm_st_hitsnd = seq * 8 + bound (1, floor (tier), 7);
};

void(entity targ, entity attacker, float take) HitSound_Play =
{
	if (take <= 0 || targ == attacker || attacker.ishuman != 1)
		return;
	if (!(targ.flags & (FL_CLIENT | FL_MONSTER)))
		return;		// doors, Mega Men, Robs and other shootable things don't count
	if (time < attacker.hs_time)
		return;
	attacker.hs_time = time + HS_GAP;
	dprint ("hit tick: ", attacker.netname, " hit ", targ.netname, targ.classname, " for ", ftos (take), "\n");

	// Unreliable CSQC stat 158 (bm_st_hitsnd): zero reliable stuffcmd channel pressure at high RTT
	if (take < 25)
		HitSound_Emit (attacker, 1);
	else if (take < 60)
		HitSound_Emit (attacker, 2);
	else
		HitSound_Emit (attacker, 3);
};
