/*
================
THE SENTRY GUN - definitions (Combat+ only)

Team Fortress's sentry gun (TF 2.9 SENTRY.QC / ENGINEER.QC), always level 2, the fourth fun gun (funguns.qc, FG_SENTRY):
	- key B (impulse 64), or the mouse wheel, takes out the spanner; fire builds a sentry 64 units in front of you
	  (on the ground, with room for it). It wakes up SG_BUILD_TIME seconds later
	- one sentry each: building a new one blows up the old one
	- the spanner then reloads for autocvar_sg_reload seconds (the HUD reload bar), held or not (bm_reload.qc)
	- TF level 2: SG_HEALTH health, SG_SHELLS shells, a 4-pellet x 3 damage shot every 0.1 s (120 a second; was x4 = 160, balance pass 2026-10-30)
	  at anyone it can see within SG_RANGE but its builder, after it has turned to within 10 degrees of them;
	  it sweeps 50 degrees each way while idle; out of shells it just sweeps
	- destroyed: it blows up (75 radius damage) into pieces. Knocked more than 15 units off its tripod, it
	  "malfunctions" and blows up too (TF's CheckSentry)
	- its kills are its builder's frags: "X is mown down by Y's sentry gun"
IT_SENTRY is no longer a weapon: the obituary still uses it as the kill's weapon number.
Models: progs/turrbase.mdl, turrgun.mdl, tgib1-3.mdl, v_span.mdl (TF's own); build_sentry.py copies them.
================
*/

float	IT_SENTRY		= 16384;
float	SG_HEALTH		= 180;		// TF level 2 (150 x 1.2)
float	SG_SHELLS		= 120;		// TF level 2 shell cap
float	SG_RANGE		= 400;		// TF had 480; shortened in the 2026-10-30 balance pass
float	SG_BUILD_TIME	= 2;

var float	autocvar_sg_reload	= 90;	// seconds before the spanner can build again (was 60)

float	sg_inflicting;		// TRUE while a sentry (or its blast) is dealing damage (obituary)

.entity	sg_sentry;			// player: their sentry gun (the swivelling head)
.float	sg_swing;			// player: when the spanner last swung (view-model frames 1-4)

.entity	sg_owner;			// sentry: who built it (not .owner, so its builder still bumps into it)
.entity	sg_base;			// sentry: its tripod
.float	sg_shells;			// sentry: shells left
.float	sg_sweep;			// sentry: idle sweep heading (0 to waitmin, 1 to waitmax)
.float	sg_waitmin, sg_waitmax;	// sentry: the idle sweep's ends (yaw)

