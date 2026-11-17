#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE BONK HAMMER - definitions (Combat+ only; it replaces the axe)

Key 1 / IT_AXE is Bonk Jam's big bonker (Bonk Jam w_hammer.qc by Kebby and fairweather, bmFbr's melee traces),
the default hammer. Same numbers as Bonk Jam:
	- hold fire to charge: LOW under 0.7 s, MED to 1.35 s, HIGH after (the view model winds up 20 frames a second);
	  let go to swing (HM_COOLDOWN seconds before the next charge can start)
	- the swing traces 5 lines from just under the eye (64 / 96 / 128 / 96 / 64 units, fanned out) and hits the two
	  nearest things
	- hit something that takes damage: 30 / 80 / 200 and it is knocked along your view (135 / 25 up a tier unit,
	  250 / 50 with the Quad); a monster on its last legs takes double (it gibs, frying-pan clang)
	- hit the world: the bonk hop. A push back along your view (55 a tier unit) and, if the middle trace hit floor, a
	  launch that always tops out 64 / 128 / 192 units over the floor below you
	- hit nothing in the air: a dash, 125 a tier unit along your view (MED/HIGH also set your rise to 60)
	- tier units (Bonk's charge_multi): LOW 0.2, MED 2, HIGH 4
	- impulse 1 with the hammer out: the spinny twirl
Model: progs/v_hammer.mdl (Bonk Jam's v_hammer_default.mdl), spark_blue / spark_yellow.mdl; build_hammer.py copies them.
Bonk Jam drove all this from the player's think chain with its own player.mdl frames (119-254); Combat+'s player
models don't have those, so here a per-frame timeline sets the view-model frame and the body uses the axe swing frames.
================
*/

float	HM_DAMAGE_LOW		= 30;
float	HM_DAMAGE_MED		= 80;
float	HM_DAMAGE_HIGH		= 200;
float	HM_COOLDOWN			= 0.4;
float	HM_MULTI_LOW		= 0.2;
float	HM_MULTI_MED		= 2;
float	HM_MULTI_HIGH		= 4;
float	HM_KNOCKBACK		= 135;
float	HM_KNOCKBACK_UP		= 25;
float	HM_KNOCKBACK_QUAD	= 250;
float	HM_KNOCKBACK_QUAD_UP	= 50;
float	HM_DASH_FORWARD		= 125;
float	HM_DASH_UPWARD		= 60;
float	HM_HOP_BACKWARD		= -55;
float	HM_HOP_LOW			= 64;
float	HM_HOP_MED			= 128;
float	HM_HOP_HIGH			= 192;

.float	hm_state;			// player: 0 idle, 1 charging, 2 swinging (release, result, follow-through, cooldown), 3 spinning
.float	hm_t0;				// player: when the current state started
.float	hm_tier;			// player: charge tier reached (1 LOW, 2 MED, 3 HIGH)
.float	hm_swung;			// player: the swing's traces have run
.float	hm_result;			// player: first view-model frame of the swing's outcome (hit / dash / hop / whiff)
.float	hm_ready;			// player: next charge allowed (Bonk's attack_finished_hammer)

void() Hammer_Precache;
void() Hammer_Spawn;
void() Hammer_PlayerFrame;
