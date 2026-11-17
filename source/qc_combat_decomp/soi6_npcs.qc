#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
SOI 6 ENTERTAINERS (maps/soi6.bsp)

8 unique Thai nightlife entertainer NPCs (`soi6_ent1` .. `soi6_ent8`) with
8-direction 360-degree animated billboard MD3s (Atlas A: idle, dance, run,
scream; Atlas B: falling death, 2D palette-matched gib burst + 3D gibs).

Scale & Crowd Architecture:
  - Spawns 9-11 girls per bar across 69 bars on both sides of Soi 6 (~728 NPCs, 25% lighter than original 975)
  - Distributes bar crowds naturally from outer curb apron -> under awning -> inside bar floor
  - Performance-tuned for high density:
      * Caches living player entities once per frame in Soi6_Tick (zero per-NPC find() scans)
      * Adaptive think intervals (calm dancers sleep 0.35-0.65s; active chase/flee ticks @ 0.1s)
      * Distance visibility cull (>2400u along street) in Soi6_Customize
  - Cheat test impulses (sv_cheats 1), handled in bm_match.qc BM_TestImpulses. Moved from 61-66 on 2026-11-17:
    61-69 are the fun-gun select impulses (FG_IMPULSE), so the old numbers hijacked Rob Dob / NetSend / Wheelman picks.
      impulse 141 -> Soi6_Line ()        (line up all 12 characters in front of you)
      impulse 142 -> Soi6_Poke (25)      (make aimed entertainer scream & flee)
      impulse 143 -> Soi6_Poke (80)      (falling death test)
      impulse 144 -> Soi6_Poke (500)     (2D+3D gib burst test)
      impulse 145 -> Soi6_GotoStreet ()  (teleport to Soi 6 street)
      impulse 146 -> Soi6_GotoBarSide () (teleport near Ruby Club / Queen Vic)
      (Soi6_SummonAlex / Soi6_GotoAlex / Soi6_PokeAlex have no impulse wired up.)
================
*/

var float autocvar_bm_soi6_npcs = 1;
var float autocvar_bm_soi6_music = 0.16;
var float autocvar_bm_soi6_lights = 1;

.float soi6_id;         // 1..8 character index
.float soi6_state;      // 0 dance, 1 idle, 2 stroll, 3 chase_play, 4 return_bar, 5 scream_flee, 6 dead, 7 gib
.float soi6_anim_t;     // start time of current animation
.float soi6_state_t;    // time until next calm state change
.float soi6_yaw;        // true NPC facing yaw (degrees; self.angles_y is viewer billboard yaw)
.float soi6_home_yaw;   // resting facing yaw to restore on return/respawn
.float soi6_side;       // +1 North bar (facing -90 South), -1 South bar (facing +90 North)
.float soi6_tier;       // 0 = curb, 1 = awning apron, 2+ = inside bar
.float soi6_stationary; // 1 = stationary dancer/greeter (spawnflags & 1)
.float soi6_quiet;      // 1 = suppress voice/centerprint greetings (spawnflags & 2)
.vector soi6_apron;     // assigned home spot
.vector soi6_bar;       // inside-bar doorway retreat point
.string soi6_bar_name;  // bar name for centerprint banter
.string soi6_mdl_a;     // progs/soi6_ent{N}_a.md3
.string soi6_mdl_b;     // progs/soi6_ent{N}_b.md3
.float soi6_talk_t;     // next allowed voice greeting/scream time
.float soi6_chase_cd;   // next allowed playful chase time
.float soi6_chase_end;  // hard stop timestamp for short chase
.float soi6_respawn_t;  // respawn timestamp when dead/gibbed
.entity soi6_target;    // player currently chased, swarmed, or fled from
.float soi6_lineup;     // 1 = cheat lineup showcase dummy
.float soi6_swarm_atk;  // next allowed swarm slap time
.float soi6_yield_cd;   // cooldown before stepping aside again
.float soi6_pass_t;    // temporary SOLID_CORPSE expiry while yielding pass-through to player
.float alex_dir;        // Alex street patrol heading (0 East, 180 West)
.float alex_quote_id;   // active Alex quote index 1..12
.float alex_stuck;      // consecutive blocked walk ticks
.float alex_cp_t;       // player: next allowed Alex HP centerprint (one per hit flooded the reliable channel)
.float soi6_swarm_t;    // player: next allowed Soi6_TriggerSwarm from hitting Alex (a find over every bar girl)

float soi6_precached;
float soi6_spawned;
float soi6_total_count;
float soi6_chat_cd;
float soi6_voice_cd;
float soi6_scream_cd;
float soi6_chase_glob_cd;
float soi6_seed;
float soi6_bar_count;
entity alex_boss;

void() Alex_SpawnStreet;
void(float half_xy) Soi6_UpdatePassThrough;
void() Soi6_Touch;
void() Alex_Touch;

float SOI6_SF_STATIONARY = 1;
float SOI6_SF_QUIET = 2;

float SOI6_DANCE = 0;
float SOI6_IDLE = 1;
float SOI6_STROLL = 2;
float SOI6_CHASE_PLAY = 3;
float SOI6_RETURN = 4;
float SOI6_SCREAM = 5;
float SOI6_DEAD = 6;
float SOI6_GIB = 7;
float SOI6_SWARM = 8;
float SOI6_YIELD = 9;

float ALEX_MAX_HP = 1500;
float ALEX_IDLE = 0;
float ALEX_STRUT = 1;
float ALEX_WALK = 2;
float ALEX_TALK = 3;
float ALEX_DEAD = 4;
float ALEX_GIB = 5;

void() Soi6_PrecacheAssets =
{
	if (soi6_precached)
		return;
	soi6_precached = TRUE;

	precache_model ("progs/soi6_ent1_a.md3");
	precache_model ("progs/soi6_ent1_b.md3");
	precache_model ("progs/soi6_ent2_a.md3");
	precache_model ("progs/soi6_ent2_b.md3");
	precache_model ("progs/soi6_ent3_a.md3");
	precache_model ("progs/soi6_ent3_b.md3");
	precache_model ("progs/soi6_ent4_a.md3");
	precache_model ("progs/soi6_ent4_b.md3");
	precache_model ("progs/soi6_ent5_a.md3");
	precache_model ("progs/soi6_ent5_b.md3");
	precache_model ("progs/soi6_ent6_a.md3");
	precache_model ("progs/soi6_ent6_b.md3");
	precache_model ("progs/soi6_ent7_a.md3");
	precache_model ("progs/soi6_ent7_b.md3");
	precache_model ("progs/soi6_ent8_a.md3");
	precache_model ("progs/soi6_ent8_b.md3");
	precache_model ("progs/soi6_ent9_a.md3");
	precache_model ("progs/soi6_ent9_b.md3");
	precache_model ("progs/soi6_ent10_a.md3");
	precache_model ("progs/soi6_ent10_b.md3");
	precache_model ("progs/soi6_ent11_a.md3");
	precache_model ("progs/soi6_ent11_b.md3");
	precache_model ("progs/soi6_ent12_a.md3");
	precache_model ("progs/soi6_ent12_b.md3");

	precache_model ("progs/gib1.mdl");
	precache_model ("progs/gib2.mdl");
	precache_model ("progs/gib3.mdl");
	precache_model ("progs/gib_4.mdl");
	precache_model ("progs/gib_5.mdl");
	precache_model ("progs/gib_ribs.mdl");
	precache_model ("progs/gib_skull.mdl");
	precache_model ("progs/gib_soldfoot1.mdl");
	precache_model ("progs/gib_soldfoot2.mdl");
	precache_model ("progs/chop.mdl");
	precache_model ("progs/gibheart.mdl");
	precache_model ("progs/gib_splat.mdl");
	precache_sound ("player/udeath.wav");
	precache_sound ("player/udeath2.wav");
	precache_sound ("misc/corpsegib.wav");

	precache_sound ("soi6_ent/greet_1.ogg");
	precache_sound ("soi6_ent/greet_2.ogg");
	precache_sound ("soi6_ent/greet_3.ogg");
	precache_sound ("soi6_ent/greet_4.ogg");
	precache_sound ("soi6_ent/greet_5.ogg");
	precache_sound ("soi6_ent/greet_6.ogg");
	precache_sound ("soi6_ent/greet_7.ogg");
	precache_sound ("soi6_ent/greet_8.ogg");
	precache_sound ("soi6_ent/pain_1.ogg");
	precache_sound ("soi6_ent/pain_2.ogg");
	precache_sound ("soi6_ent/pain_3.ogg");
	precache_sound ("soi6_ent/pain_4.ogg");
	precache_sound ("soi6_ent/pain_5.ogg");
	precache_sound ("soi6_ent/pain_6.ogg");
	precache_sound ("soi6_ent/scream_1.ogg");
	precache_sound ("soi6_ent/scream_2.ogg");
	precache_sound ("soi6_ent/scream_3.ogg");
	precache_sound ("soi6_ent/scream_4.ogg");
	precache_sound ("soi6_ent/scream_5.ogg");
	precache_sound ("soi6_ent/scream_6.ogg");
	precache_sound ("soi6_ent/scream_7.ogg");
	precache_sound ("soi6_ent/scream_8.ogg");
	precache_sound ("soi6_ent/scream_9.ogg");
	precache_sound ("soi6_ent/scream_10.ogg");
	precache_sound ("soi6_ent/scream_11.ogg");
	precache_sound ("soi6_ent/scream_12.ogg");
	precache_sound ("soi6_ent/die_1.ogg");
	precache_sound ("soi6_ent/die_2.ogg");
	precache_sound ("soi6_ent/die_3.ogg");
	precache_sound ("soi6_ent/die_4.ogg");

	precache_model ("progs/null.spr");
	precache_sound ("soi6_music/mix_01.ogg");
	precache_sound ("soi6_music/mix_02.ogg");
	precache_sound ("soi6_music/mix_03.ogg");
	precache_sound ("soi6_music/mix_04.ogg");
	precache_sound ("soi6_music/mix_05.ogg");
	precache_sound ("soi6_music/mix_06.ogg");
	precache_sound ("soi6_music/mix_07.ogg");
	precache_sound ("soi6_music/mix_08.ogg");
	precache_sound ("soi6_music/mix_09.ogg");
	precache_sound ("soi6_music/mix_10.ogg");
	precache_sound ("soi6_music/mix_11.ogg");
	precache_sound ("soi6_music/mix_12.ogg");

	precache_model ("progs/alex_pattaya_a.md3");
	precache_model ("progs/alex_pattaya_b.md3");
	precache_sound ("alex_pattaya/talk_1.ogg");
	precache_sound ("alex_pattaya/talk_2.ogg");
	precache_sound ("alex_pattaya/talk_3.ogg");
	precache_sound ("alex_pattaya/talk_4.ogg");
	precache_sound ("alex_pattaya/talk_5.ogg");
	precache_sound ("alex_pattaya/talk_6.ogg");
	precache_sound ("alex_pattaya/talk_7.ogg");
	precache_sound ("alex_pattaya/talk_8.ogg");
	precache_sound ("alex_pattaya/talk_9.ogg");
	precache_sound ("alex_pattaya/talk_10.ogg");
	precache_sound ("alex_pattaya/talk_11.ogg");
	precache_sound ("alex_pattaya/talk_12.ogg");
};

void() Soi6_Precache =
{
	if (world.model != "maps/soi6.bsp" && world.model != "maps/soicowboy_bkk.bsp")
		return;
	Soi6_PrecacheAssets ();
};

string(float cid) Soi6_ModelA =
{
	if (cid == 1) return "progs/soi6_ent1_a.md3";
	if (cid == 2) return "progs/soi6_ent2_a.md3";
	if (cid == 3) return "progs/soi6_ent3_a.md3";
	if (cid == 4) return "progs/soi6_ent4_a.md3";
	if (cid == 5) return "progs/soi6_ent5_a.md3";
	if (cid == 6) return "progs/soi6_ent6_a.md3";
	if (cid == 7) return "progs/soi6_ent7_a.md3";
	if (cid == 8) return "progs/soi6_ent8_a.md3";
	if (cid == 9) return "progs/soi6_ent9_a.md3";
	if (cid == 10) return "progs/soi6_ent10_a.md3";
	if (cid == 11) return "progs/soi6_ent11_a.md3";
	return "progs/soi6_ent12_a.md3";
};

string(float cid) Soi6_ModelB =
{
	if (cid == 1) return "progs/soi6_ent1_b.md3";
	if (cid == 2) return "progs/soi6_ent2_b.md3";
	if (cid == 3) return "progs/soi6_ent3_b.md3";
	if (cid == 4) return "progs/soi6_ent4_b.md3";
	if (cid == 5) return "progs/soi6_ent5_b.md3";
	if (cid == 6) return "progs/soi6_ent6_b.md3";
	if (cid == 7) return "progs/soi6_ent7_b.md3";
	if (cid == 8) return "progs/soi6_ent8_b.md3";
	if (cid == 9) return "progs/soi6_ent9_b.md3";
	if (cid == 10) return "progs/soi6_ent10_b.md3";
	if (cid == 11) return "progs/soi6_ent11_b.md3";
	return "progs/soi6_ent12_b.md3";
};

void(entity ent, float chan, float vol) Soi6_PlayGreet =
{
	local float r;
	if (time < soi6_voice_cd)
		return;
	soi6_voice_cd = time + 0.65;
	r = floor(random() * 8);
	if (r == 0) sound (ent, chan, "soi6_ent/greet_1.ogg", vol, ATTN_NORM);
	else if (r == 1) sound (ent, chan, "soi6_ent/greet_2.ogg", vol, ATTN_NORM);
	else if (r == 2) sound (ent, chan, "soi6_ent/greet_3.ogg", vol, ATTN_NORM);
	else if (r == 3) sound (ent, chan, "soi6_ent/greet_4.ogg", vol, ATTN_NORM);
	else if (r == 4) sound (ent, chan, "soi6_ent/greet_5.ogg", vol, ATTN_NORM);
	else if (r == 5) sound (ent, chan, "soi6_ent/greet_6.ogg", vol, ATTN_NORM);
	else if (r == 6) sound (ent, chan, "soi6_ent/greet_7.ogg", vol, ATTN_NORM);
	else sound (ent, chan, "soi6_ent/greet_8.ogg", vol, ATTN_NORM);
};

void(entity ent, float chan, float vol) Soi6_PlayScream =
{
	local float r;
	if (time < soi6_scream_cd)
		return;
	soi6_scream_cd = time + 0.10;
	r = floor(random() * 12);
	if (r == 0) sound (ent, chan, "soi6_ent/scream_1.ogg", vol, ATTN_NORM);
	else if (r == 1) sound (ent, chan, "soi6_ent/scream_2.ogg", vol, ATTN_NORM);
	else if (r == 2) sound (ent, chan, "soi6_ent/scream_3.ogg", vol, ATTN_NORM);
	else if (r == 3) sound (ent, chan, "soi6_ent/scream_4.ogg", vol, ATTN_NORM);
	else if (r == 4) sound (ent, chan, "soi6_ent/scream_5.ogg", vol, ATTN_NORM);
	else if (r == 5) sound (ent, chan, "soi6_ent/scream_6.ogg", vol, ATTN_NORM);
	else if (r == 6) sound (ent, chan, "soi6_ent/scream_7.ogg", vol, ATTN_NORM);
	else if (r == 7) sound (ent, chan, "soi6_ent/scream_8.ogg", vol, ATTN_NORM);
	else if (r == 8) sound (ent, chan, "soi6_ent/scream_9.ogg", vol, ATTN_NORM);
	else if (r == 9) sound (ent, chan, "soi6_ent/scream_10.ogg", vol, ATTN_NORM);
	else if (r == 10) sound (ent, chan, "soi6_ent/scream_11.ogg", vol, ATTN_NORM);
	else sound (ent, chan, "soi6_ent/scream_12.ogg", vol, ATTN_NORM);
};

void(entity ent) Soi6_PlayPain =
{
	local float r;
	r = floor(random() * 6);
	if (r == 0) sound (ent, CHAN_VOICE, "soi6_ent/pain_1.ogg", 1, ATTN_NORM);
	else if (r == 1) sound (ent, CHAN_VOICE, "soi6_ent/pain_2.ogg", 1, ATTN_NORM);
	else if (r == 2) sound (ent, CHAN_VOICE, "soi6_ent/pain_3.ogg", 1, ATTN_NORM);
	else if (r == 3) sound (ent, CHAN_VOICE, "soi6_ent/pain_4.ogg", 1, ATTN_NORM);
	else if (r == 4) sound (ent, CHAN_VOICE, "soi6_ent/pain_5.ogg", 1, ATTN_NORM);
	else sound (ent, CHAN_VOICE, "soi6_ent/pain_6.ogg", 1, ATTN_NORM);
};

void(entity ent) Soi6_CenterBanter =
{
	local float r;
	if (!ent.soi6_target || !(ent.soi6_target.flags & FL_CLIENT))
		return;
	if (time < soi6_chat_cd)
		return;
	soi6_chat_cd = time + 1.8;

	r = floor(random() * 6);
	if (r == 0)
		centerprint (ent.soi6_target, strcat ("Hey handsome! Come inside ", ent.soi6_bar_name, "!"));
	else if (r == 1)
		centerprint (ent.soi6_target, strcat ("Cold Chang beer waiting for you at ", ent.soi6_bar_name, "!"));
	else if (r == 2)
		centerprint (ent.soi6_target, strcat ("Sawadee ka! Buy me a lady drink at ", ent.soi6_bar_name, "?"));
	else if (r == 3)
		centerprint (ent.soi6_target, strcat ("Where you going baby? Party at ", ent.soi6_bar_name, "!"));
	else if (r == 4)
		centerprint (ent.soi6_target, strcat ("Sexy dance inside ", ent.soi6_bar_name, " right now!"));
	else
		centerprint (ent.soi6_target, strcat ("One drink together, then back into ", ent.soi6_bar_name, "!"));
};

float() Soi6_Customize =
{
	local vector v;
	local float dx, dy, rel, d, elapsed, f;

	// Fast 2D XY distance cull keeps dense NPC crowds smooth over network & GPU
	dx = other.origin_x - self.origin_x;
	if (dx > 1050 || dx < -1050)
		return FALSE;
	dy = other.origin_y - self.origin_y;
	if (dy > 1050 || dy < -1050)
		return FALSE;
	if ((dx * dx + dy * dy) > 1102500)
		return FALSE;
	if (other.ishuman != 1)
		return FALSE;

	self.angles_y = other.v_angle_y;
	self.angles_x = 0;
	self.angles_z = 0;

	v = other.origin - self.origin;
	rel = vectoyaw (v) - self.soi6_yaw;
	if (rel < 0)
		rel = rel + 360;
	else if (rel >= 360)
		rel = rel - 360;
	if (rel < 0)
		rel = rel + 360;
	d = floor (rel / 45 + 0.5);
	if (d >= 8)
		d = d - 8;

	elapsed = time - self.soi6_anim_t;
	if (elapsed < 0)
		elapsed = 0;

	if (self.soi6_state == SOI6_DEAD)
	{
		f = floor (elapsed * 16);
		if (f > 5) f = 5;
		self.skin = f * 8 + d;
		return TRUE;
	}
	if (self.soi6_state == SOI6_GIB)
	{
		f = floor (elapsed * 18);
		if (f > 7) f = 7;
		self.skin = (6 + f) * 8 + d;
		return TRUE;
	}

	if (self.soi6_state == SOI6_IDLE)
		f = floor (elapsed * 16) % 6;
	else if (self.soi6_state == SOI6_DANCE)
		f = 6 + (floor (elapsed * 18) % 12);
	else if (self.soi6_state == SOI6_SCREAM)
	{
		// Alternates terror scream poses with frantic running strides while fleeing
		if (elapsed < 0.25 || ((floor (elapsed * 10) % 7) < 2))
			f = 26 + (floor (elapsed * 22) % 5);
		else
			f = 18 + (floor (elapsed * 22) % 8);
	}
	else if (self.soi6_state == SOI6_SWARM)
		f = 18 + (floor (elapsed * 22) % 8);
	else
		f = 18 + (floor (elapsed * 18) % 8);

	self.skin = f * 8 + d;
	return TRUE;
};

void(entity ent, float st) Soi6_SetState =
{
	if (ent.soi6_state == st)
		return;
	ent.soi6_state = st;
	ent.soi6_anim_t = time - random () * 0.25;
	if (st == SOI6_DEAD || st == SOI6_GIB)
	{
		ent.soi6_anim_t = time;
		setmodel (ent, ent.soi6_mdl_b);
	}
	else if (ent.model != ent.soi6_mdl_a)
	{
		setmodel (ent, ent.soi6_mdl_a);
		setsize (ent, '-12 -12 0', '12 12 54');
	}
};

void() Soi6_Respawn =
{
	self.health = 75;
	self.takedamage = DAMAGE_AIM;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.touch = Soi6_Touch;
	self.soi6_pass_t = 0;
	self.velocity = '0 0 0';
	self.soi6_target = world;
	self.soi6_lineup = 0;

	setmodel (self, self.soi6_mdl_a);
	setsize (self, '-12 -12 0', '12 12 54');
	setorigin (self, self.soi6_apron + '0 0 6');
	droptofloor ();
	Soi6_UpdatePassThrough (12);

	self.soi6_yaw = self.soi6_home_yaw;
	Soi6_SetState (self, SOI6_DANCE);
	self.soi6_state_t = time + 3 + random () * 5;
	self.nextthink = time + 0.35 + random () * 0.4;
};

void(entity attacker, float damage) Soi6_Pain =
{
	local vector away;
	local float was_screaming;

	if (self.health <= 0 || self.soi6_state == SOI6_DEAD || self.soi6_state == SOI6_GIB)
		return;

	was_screaming = (self.soi6_state == SOI6_SCREAM);
	self.soi6_target = attacker;
	if (attacker != world)
		self.enemy = attacker;

	// Any hit triggers immediate screaming + running away
	if (attacker && attacker != world)
	{
		away = self.origin - attacker.origin;
		away_z = 0;
		if (vlen (away) > 1)
			self.soi6_yaw = vectoyaw (away) + (random () - 0.5) * 32;
		else
			self.soi6_yaw = self.soi6_home_yaw;
	}

	Soi6_SetState (self, SOI6_SCREAM);
	self.soi6_state_t = time + 4.5 + random () * 1.5;
	self.nextthink = time + 0.05;

	// First shot always triggers an immediate panic scream; follow-up hits respect short talk cooldown
	if (!was_screaming || time >= self.soi6_talk_t)
	{
		if (random () < 0.80)
			Soi6_PlayScream (self, CHAN_VOICE, 1);
		else
			Soi6_PlayPain (self);
		self.soi6_talk_t = time + 1.0 + random () * 0.6;
	}
};

void() Soi6_SpawnPlayerGibs =
{
	local float gib_dm;
	local vector saved_org;

	gib_dm = self.health;
	if (gib_dm > -95)
		gib_dm = -95;

	if (!self.enemy && self.soi6_target)
		self.enemy = self.soi6_target;

	saved_org = self.origin;
	setsize (self, '-16 -16 -16', '16 16 32');
	setorigin (self, saved_org + '0 0 24');

	// Full player-model gib shower: guts, chops, limbs, ribs, skull, heart, sticky gibs & blood splats
	ThrowGib ("progs/gib_5.mdl", gib_dm);
	ThrowGib ("progs/gib_5.mdl", gib_dm);
	ThrowGib ("progs/gib_4.mdl", gib_dm);
	ThrowGib ("progs/gib_ribs.mdl", gib_dm);
	ThrowGib ("progs/gib_skull.mdl", gib_dm);
	ThrowGib ("progs/gib_soldfoot1.mdl", gib_dm);
	ThrowGib ("progs/gib_soldfoot2.mdl", gib_dm);
	ThrowGib ("progs/chop.mdl", gib_dm);
	ThrowGib ("progs/chop.mdl", gib_dm);
	ThrowGib ("progs/chop.mdl", gib_dm);
	ThrowGib ("progs/chop.mdl", gib_dm);
	ThrowGib ("progs/gib1.mdl", gib_dm);
	ThrowGib ("progs/gib2.mdl", gib_dm);
	ThrowGib ("progs/gib3.mdl", gib_dm);
	ThrowHeart ("progs/gibheart.mdl", gib_dm);
	CeilSplat ();
	CeilSplat ();
	CeilSplat ();
	CeilSplat ();
	CeilSplat ();
	play_gibsound ();
	gibdeath_effects ();

	setorigin (self, saved_org);
	setsize (self, '-12 -12 0', '12 12 54');
};

void() Soi6_Die =
{
	local float is_gib, r;

	if (self.soi6_state == SOI6_DEAD || self.soi6_state == SOI6_GIB)
		return;

	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';

	is_gib = (self.health < -20);
	if (is_gib)
	{
		Soi6_SetState (self, SOI6_GIB);
		Soi6_SpawnPlayerGibs ();
		self.soi6_respawn_t = time + 18;
	}
	else
	{
		Soi6_SetState (self, SOI6_DEAD);
		r = floor (random () * 4);
		if (r == 0) sound (self, CHAN_VOICE, "soi6_ent/die_1.ogg", 1, ATTN_NORM);
		else if (r == 1) sound (self, CHAN_VOICE, "soi6_ent/die_2.ogg", 1, ATTN_NORM);
		else if (r == 2) sound (self, CHAN_VOICE, "soi6_ent/die_3.ogg", 1, ATTN_NORM);
		else sound (self, CHAN_VOICE, "soi6_ent/die_4.ogg", 1, ATTN_NORM);
		self.soi6_respawn_t = time + 20;
	}
	self.nextthink = time + 0.48;
};

entity(entity ent, float maxd) Soi6_NearestPlayerFast =
{
	local entity p, best;
	local float bestd2, d2, dx, dy, dz;

	best = world;
	bestd2 = maxd * maxd;

	p = bm_player_head;
	while (p)
	{
		if (p.health > 0 && !(p.flags & FL_NOTARGET))
		{
			dx = p.origin_x - ent.origin_x;
			if (dx < maxd && dx > -maxd)
			{
				dy = p.origin_y - ent.origin_y;
				if (dy < maxd && dy > -maxd)
				{
					dz = p.origin_z - ent.origin_z;
					if (dz < 84 && dz > -84)
					{
						d2 = dx * dx + dy * dy;
						if (d2 < bestd2)
						{
							bestd2 = d2;
							best = p;
						}
					}
				}
			}
		}
		p = p.bm_player_next;
	}
	return best;
};

float(float move_yaw, float dist) Soi6_StepMove =
{
	self.angles_y = move_yaw;
	if (walkmove (move_yaw, dist))
		return TRUE;
	if (walkmove (move_yaw + 45, dist * 0.85))
	{
		self.soi6_yaw = move_yaw + 45;
		return TRUE;
	}
	if (walkmove (move_yaw - 45, dist * 0.85))
	{
		self.soi6_yaw = move_yaw - 45;
		return TRUE;
	}
	if (walkmove (move_yaw + 95, dist * 0.70))
	{
		self.soi6_yaw = move_yaw + 95;
		return TRUE;
	}
	if (walkmove (move_yaw - 95, dist * 0.70))
	{
		self.soi6_yaw = move_yaw - 95;
		return TRUE;
	}
	return FALSE;
};

float(entity p, float strict) Soi6_ShouldYield =
{
	local vector delta, pv;
	local float d;

	if (!p || p == world || p.health <= 0 || (p.flags & FL_NOTARGET))
		return FALSE;
	if (fabs (p.origin_z - self.origin_z) >= 64)
		return FALSE;

	delta = self.origin - p.origin;
	delta_z = 0;
	d = vlen (delta);
	if (d < 52)
		return TRUE;
	if (!strict && d < 84)
	{
		pv = p.velocity;
		pv_z = 0;
		if (vlen (pv) > 40 && (pv * delta) > 0)
			return TRUE;
	}
	return FALSE;
};

void(entity p) Soi6_StepAside =
{
	local vector away, pv, pdir, lat, step_dir;
	local float wy;

	away = self.origin - p.origin;
	away_z = 0;
	if (vlen (away) > 1)
		away = normalize (away);
	else
	{
		makevectors ('0 1 0' * self.soi6_home_yaw);
		away = -v_forward;
		away_z = 0;
		if (vlen (away) > 0.01)
			away = normalize (away);
		else
			away = '1 0 0';
	}

	pv = p.velocity;
	pv_z = 0;
	if (vlen (pv) > 30)
	{
		pdir = normalize (pv);
		lat_x = -pdir_y;
		lat_y = pdir_x;
		lat_z = 0;
		if ((away * lat) < 0 || ((away * lat) == 0 && (self.soi6_id & 1)))
			lat = -lat;
		step_dir = normalize (lat * 0.85 + away * 0.45);
	}
	else
		step_dir = away;

	wy = vectoyaw (step_dir);
	self.soi6_yaw = wy;
	if (!Soi6_StepMove (wy, 18))
	{
		if (!Soi6_StepMove (wy + 90, 14))
			Soi6_StepMove (wy - 90, 14);
	}
};

void(float half_xy) Soi6_UpdatePassThrough =
{
	local entity p;
	local float blocking, approaching, lim_b, lim_a, dx, dy, dz;
	local vector delta, pv;

	blocking = FALSE;
	approaching = FALSE;
	lim_b = half_xy + 18;
	lim_a = half_xy + 34;
	p = bm_player_head;
	while (p != world)
	{
		if (p.health > 0)
		{
			dz = self.origin_z - p.origin_z;
			if (dz < 62 && dz > -62)
			{
				dx = self.origin_x - p.origin_x;
				if (dx < lim_a && dx > -lim_a)
				{
					dy = self.origin_y - p.origin_y;
					if (dy < lim_a && dy > -lim_a)
					{
						// Keep SOLID_CORPSE until player clears bbox (+2u margin)
						if (dx < lim_b && dx > -lim_b && dy < lim_b && dy > -lim_b)
						{
							blocking = TRUE;
							break;
						}
						// Pre-emptively clear path when a moving player is approaching closely
						pv = p.velocity;
						pv_z = 0;
						delta = self.origin - p.origin;
						delta_z = 0;
						if (vlen (pv) > 75 && (pv * delta) > 0)
							approaching = TRUE;
					}
				}
			}
		}
		p = p.bm_player_next;
	}

	if (blocking || approaching)
	{
		self.solid = SOLID_CORPSE;
		if (time + 0.35 > self.soi6_pass_t)
			self.soi6_pass_t = time + 0.35;
	}
	else if (self.solid == SOLID_CORPSE && time >= self.soi6_pass_t)
		self.solid = SOLID_SLIDEBOX;
};

void() Soi6_Touch =
{
	if (!other || other.classname != "player" || other.health <= 0)
		return;
	if (self.soi6_state == SOI6_DEAD || self.soi6_state == SOI6_GIB)
		return;

	self.solid = SOLID_CORPSE;
	self.soi6_pass_t = time + 0.45;
	if (self.nextthink > time + 0.12)
		self.nextthink = time + 0.12;

	if (!self.soi6_lineup
		&& !self.soi6_stationary
		&& self.soi6_state != SOI6_SCREAM
		&& self.soi6_state != SOI6_SWARM
		&& self.soi6_state != SOI6_YIELD
		&& time >= self.soi6_yield_cd)
	{
		self.soi6_yield_cd = time + 0.9;
		Soi6_SetState (self, SOI6_YIELD);
		Soi6_StepAside (other);
	}
};

void() Soi6_Think =
{
	local entity p;
	local vector dir;
	local float d_p, d_apron, d_bar, wy;

	if (self.soi6_state == SOI6_DEAD || self.soi6_state == SOI6_GIB)
	{
		self.nextthink = time + 0.6;
		if (self.soi6_state == SOI6_GIB && time > self.soi6_anim_t + 0.45 && self.modelindex)
			setmodel (self, "");		// the engine draws by modelindex: clearing .model alone left the last gib frame up
		if (!self.soi6_lineup && time >= self.soi6_respawn_t)
			Soi6_Respawn ();
		return;
	}

	if (self.soi6_lineup || (self.soi6_state != SOI6_DANCE && self.soi6_state != SOI6_IDLE))
		Soi6_UpdatePassThrough (12);

	if (self.soi6_lineup && self.soi6_state != SOI6_SCREAM)
	{
		if (self.solid == SOLID_CORPSE)
			self.nextthink = time + 0.12;
		else
			self.nextthink = time + 0.5;
		return;
	}

	// Active states tick fast (10 Hz)
	if (self.soi6_state == SOI6_SWARM)
	{
		self.nextthink = time + 0.1;
		p = self.soi6_target;
		if (!p || p == world || p.health <= 0 || time >= self.soi6_state_t)
		{
			Soi6_SetState (self, SOI6_RETURN);
			self.soi6_state_t = time + 5.0;
			return;
		}
		if (time >= self.soi6_talk_t)
		{
			Soi6_PlayScream (self, CHAN_VOICE, 0.85);
			self.soi6_talk_t = time + 1.3 + random () * 0.9;
		}
		dir = p.origin - self.origin;
		dir_z = 0;
		d_p = vlen (dir);
		if (d_p > 2)
			wy = vectoyaw (dir);
		else
			wy = self.soi6_yaw;
		self.soi6_yaw = wy;
		if (d_p > 40)
			Soi6_StepMove (wy, 22);
		if (d_p <= 64 && fabs (p.origin_z - self.origin_z) < 64 && time >= self.soi6_swarm_atk)
		{
			self.soi6_swarm_atk = time + 0.90 + random () * 0.35;
			T_Damage (p, self, self, 3);
		}
		return;
	}

	if (self.soi6_state == SOI6_SCREAM)
	{
		self.nextthink = time + 0.1;
		if (time >= self.soi6_state_t)
		{
			if (self.soi6_stationary || self.soi6_lineup)
			{
				Soi6_SetState (self, SOI6_DANCE);
				self.soi6_yaw = self.soi6_home_yaw;
				self.soi6_state_t = time + 2.5 + random () * 4.0;
			}
			else
			{
				Soi6_SetState (self, SOI6_RETURN);
				self.soi6_state_t = time + 5.0;
			}
			return;
		}

		// Keep screaming periodically while sprinting away in panic
		if (time >= self.soi6_talk_t)
		{
			if (random () < 0.75)
				Soi6_PlayScream (self, CHAN_VOICE, 1);
			else
				Soi6_PlayPain (self);
			self.soi6_talk_t = time + 1.15 + random () * 0.70;
		}

		// Sprint directly away from shooter immediately (zero standstill delay)
		p = self.soi6_target;
		if (p && p != world && vlen (p.origin - self.origin) < 650)
			dir = self.origin - p.origin;
		else
			dir = self.soi6_bar - self.origin;
		dir_z = 0;
		if (vlen (dir) > 4)
			wy = vectoyaw (dir);
		else
			wy = self.soi6_yaw;
		self.soi6_yaw = wy;
		if (!Soi6_StepMove (wy, 28))
			Soi6_StepMove (wy + 180, 22);
		return;
	}

	if (self.soi6_state == SOI6_CHASE_PLAY)
	{
		self.nextthink = time + 0.1;
		p = self.soi6_target;
		d_apron = vlen ((self.origin - self.soi6_apron) - '0 0 1' * (self.origin_z - self.soi6_apron_z));
		if (!p || p.health <= 0 || time >= self.soi6_chase_end || d_apron > 135 || vlen (p.origin - self.origin) > 220)
		{
			Soi6_SetState (self, SOI6_RETURN);
			self.soi6_state_t = time + 5.0;
			self.soi6_chase_cd = time + 12 + random () * 6;
			return;
		}

		dir = p.origin - self.origin;
		dir_z = 0;
		wy = vectoyaw (dir);
		self.soi6_yaw = wy;
		if (vlen (dir) > 48)
			Soi6_StepMove (wy, 17);
		else if (!self.soi6_stationary && !self.soi6_lineup && vlen (dir) < 42 && time >= self.soi6_yield_cd)
		{
			self.soi6_target = p;
			self.soi6_state_t = time + 0.9;
			Soi6_SetState (self, SOI6_YIELD);
		}
		return;
	}

	if (self.soi6_state == SOI6_YIELD)
	{
		self.nextthink = time + 0.1;
		p = Soi6_NearestPlayerFast (self, 84);
		if (p != world && time < self.soi6_state_t && fabs (p.origin_z - self.origin_z) < 64)
		{
			dir = self.origin - p.origin;
			dir_z = 0;
			if (vlen (dir) < 68)
			{
				Soi6_StepAside (p);
				return;
			}
		}
		self.soi6_yield_cd = time + 0.9;
		Soi6_SetState (self, SOI6_STROLL);
		self.soi6_state_t = time + 4.0;
		return;
	}

	if (self.soi6_state == SOI6_RETURN)
	{
		self.nextthink = time + 0.1;
		if (!self.soi6_stationary && !self.soi6_lineup && time >= self.soi6_yield_cd)
		{
			p = Soi6_NearestPlayerFast (self, 84);
			if (Soi6_ShouldYield (p, FALSE))
			{
				self.soi6_target = p;
				self.soi6_state_t = time + 0.9;
				Soi6_SetState (self, SOI6_YIELD);
				return;
			}
		}
		dir = self.soi6_bar - self.origin;
		dir_z = 0;
		d_bar = vlen (dir);
		if (d_bar <= 24 || time >= self.soi6_state_t)
		{
			Soi6_SetState (self, SOI6_DANCE);
			self.soi6_yaw = self.soi6_home_yaw;
			self.soi6_state_t = time + 2.5 + random () * 4.0;
			return;
		}
		wy = vectoyaw (dir);
		self.soi6_yaw = wy;
		Soi6_StepMove (wy, 16);
		return;
	}

	if (self.soi6_state == SOI6_STROLL)
	{
		self.nextthink = time + 0.15;
		if (!self.soi6_stationary && !self.soi6_lineup && time >= self.soi6_yield_cd)
		{
			p = Soi6_NearestPlayerFast (self, 84);
			if (Soi6_ShouldYield (p, TRUE))
			{
				self.soi6_target = p;
				self.soi6_state_t = time + 0.9;
				Soi6_SetState (self, SOI6_YIELD);
				self.nextthink = time + 0.1;
				return;
			}
		}
		dir = self.soi6_apron - self.origin;
		dir_z = 0;
		if (vlen (dir) > 16)
		{
			wy = vectoyaw (dir);
			self.soi6_yaw = wy;
			Soi6_StepMove (wy, 12);
		}
		else
		{
			Soi6_SetState (self, SOI6_DANCE);
			self.soi6_yaw = self.soi6_home_yaw;
			self.soi6_state_t = time + 3 + random () * 5;
		}
		return;
	}

	// Calm dancing / idle girls do one spatial player check and sleep longer when far away
	p = Soi6_NearestPlayerFast (self, 360);
	if (p != world)
	{
		d_p = vlen (p.origin - self.origin);
		if (self.solid == SOLID_CORPSE || d_p <= 80)
			Soi6_UpdatePassThrough (12);
		if (d_p <= 165)
		{
			if (!self.soi6_quiet && d_p <= 112 && time >= self.soi6_talk_t)
			{
				self.soi6_target = p;
				self.soi6_talk_t = time + 8 + random () * 5;
				Soi6_PlayGreet (self, CHAN_VOICE, 1);
				Soi6_CenterBanter (self);
			}
			if (!self.soi6_stationary && !self.soi6_lineup && time >= self.soi6_yield_cd && Soi6_ShouldYield (p, FALSE))
			{
				self.soi6_target = p;
				self.soi6_state_t = time + 1.0;
				Soi6_SetState (self, SOI6_YIELD);
				self.nextthink = time + 0.1;
				return;
			}
			// Curb/awning girls step forward playfully to chase you a few feet, then go back inside
			if (!self.soi6_stationary && d_p <= 155 && self.soi6_tier <= 1 && time >= self.soi6_chase_cd && time >= soi6_chase_glob_cd)
			{
				soi6_chase_glob_cd = time + 0.45;
				self.soi6_target = p;
				self.soi6_chase_end = time + 1.15 + random () * 0.45;
				Soi6_SetState (self, SOI6_CHASE_PLAY);
				self.nextthink = time + 0.1;
				return;
			}
		}
		if (d_p <= 135)
			self.nextthink = time + 0.12;
		else if (d_p <= 220)
			self.nextthink = time + 0.25 + random () * 0.15;
		else
			self.nextthink = time + 0.45 + random () * 0.25;
	}
	else
	{
		if (self.solid == SOLID_CORPSE && time >= self.soi6_pass_t)
			self.solid = SOLID_SLIDEBOX;
		self.nextthink = time + 0.90 + random () * 0.60;
	}
	if (self.solid == SOLID_CORPSE && self.nextthink > time + 0.12)
		self.nextthink = time + 0.12;

	if (time >= self.soi6_state_t)
	{
		d_apron = vlen (self.origin - self.soi6_apron);
		if (!self.soi6_stationary && d_apron > 44)
		{
			Soi6_SetState (self, SOI6_STROLL);
			self.soi6_state_t = time + 4.0;
		}
		else if (self.soi6_state == SOI6_DANCE)
		{
			Soi6_SetState (self, SOI6_IDLE);
			self.soi6_state_t = time + 1.8 + random () * 3.0;
		}
		else
		{
			Soi6_SetState (self, SOI6_DANCE);
			self.soi6_state_t = time + 3.5 + random () * 6.0;
		}
	}
};

float(vector cand) Soi6_SpotClear =
{
	tracebox (cand + '0 0 18', '-12 -12 0', '12 12 54', cand - '0 0 28', FALSE, world);
	if (trace_startsolid || trace_allsolid || trace_fraction >= 1)
		return FALSE;
	// Ensure floor is street/bar ground (not rooftop, counter, stool, or pit)
	if (trace_endpos_z < -4 || trace_endpos_z > 12)
		return FALSE;
	return TRUE;
};

void(float cid, float x_u, float y_u, float mid_x_u, float side, float tier, string bname, float init_st) Soi6_SpawnSpot =
{
	local entity e;
	local float yaw_j;
	local vector base, cand;

	base_x = x_u;
	base_y = y_u;
	base_z = 4;

	cand = base;
	if (!Soi6_SpotClear (cand))
	{
		cand = base + '26 0 0';
		if (!Soi6_SpotClear (cand))
		{
			cand = base - '26 0 0';
			if (!Soi6_SpotClear (cand))
			{
				cand = base + side * '0 32 0';
				if (!Soi6_SpotClear (cand))
				{
					cand = base - side * '0 28 0';
					if (!Soi6_SpotClear (cand))
						cand = (mid_x_u + ((soi6_total_count % 3) - 1) * 28) * '1 0 0' + (side * (192 + (soi6_total_count % 2) * 28)) * '0 1 0' + '0 0 6';
				}
			}
		}
	}

	e = spawn ();
	e.classname = "npc_soi6";
	e.soi6_id = cid;
	e.soi6_side = side;
	e.soi6_tier = tier;
	e.soi6_apron = cand_x * '1 0 0' + cand_y * '0 1 0';
	// Retreat target aims through bar doorway center
	e.soi6_bar = mid_x_u * '1 0 0' + (side * 218) * '0 1 0';
	e.soi6_bar_name = bname;
	e.soi6_mdl_a = Soi6_ModelA (cid);
	e.soi6_mdl_b = Soi6_ModelB (cid);

	e.health = 75;
	e.takedamage = DAMAGE_AIM;
	e.solid = SOLID_SLIDEBOX;
	e.movetype = MOVETYPE_STEP;
	e.touch = Soi6_Touch;
	e.effects = EF_NOSHADOW;
	e.th_pain = Soi6_Pain;
	e.th_die = Soi6_Die;
	e.customizeentityforclient = Soi6_Customize;
	e.think = Soi6_Think;
	e.nextthink = time + 0.2 + random () * 0.8;

	yaw_j = (random () - 0.5) * 32;
	if (side > 0) e.soi6_home_yaw = -90; else e.soi6_home_yaw = 90;
	e.soi6_yaw = e.soi6_home_yaw + yaw_j;

	setmodel (e, e.soi6_mdl_a);
	setsize (e, '-12 -12 0', '12 12 54');
	setorigin (e, cand + '0 0 14');
	self = e;
	droptofloor ();

	e.soi6_state = -1;
	Soi6_SetState (e, init_st);
	e.soi6_state_t = time + 1.5 + random () * 6.0;
	e.soi6_chase_cd = time + 1.5 + random () * 5.0;
	soi6_total_count = soi6_total_count + 1;
};

string(float tid) Soi6_MusicTrack =
{
	if (tid == 1)  return "soi6_music/mix_01.ogg";
	if (tid == 2)  return "soi6_music/mix_02.ogg";
	if (tid == 3)  return "soi6_music/mix_03.ogg";
	if (tid == 4)  return "soi6_music/mix_04.ogg";
	if (tid == 5)  return "soi6_music/mix_05.ogg";
	if (tid == 6)  return "soi6_music/mix_06.ogg";
	if (tid == 7)  return "soi6_music/mix_07.ogg";
	if (tid == 8)  return "soi6_music/mix_08.ogg";
	if (tid == 9)  return "soi6_music/mix_09.ogg";
	if (tid == 10) return "soi6_music/mix_10.ogg";
	if (tid == 11) return "soi6_music/mix_11.ogg";
	return "soi6_music/mix_12.ogg";
};

float(float tid) Soi6_TrackBPM =
{
	if (tid == 1)  return 132;
	if (tid == 2)  return 134;
	if (tid == 3)  return 130;
	if (tid == 4)  return 136;
	if (tid == 5)  return 128;
	if (tid == 6)  return 138;
	if (tid == 7)  return 132;
	if (tid == 8)  return 128;
	if (tid == 9)  return 135;
	if (tid == 10) return 140;
	if (tid == 11) return 130;
	return 134;
};

vector(float tid) Soi6_BarColorA =
{
	if (tid == 1)  return '1.45 0.12 0.85'; // Hot Pink
	if (tid == 2)  return '0.95 0.15 1.55'; // Club Violet
	if (tid == 3)  return '1.55 0.82 0.12'; // 3-Cha Amber Gold
	if (tid == 4)  return '0.25 1.50 0.30'; // Neon Rave Lime
	if (tid == 5)  return '1.55 0.15 0.28'; // Sexy Crimson
	if (tid == 6)  return '0.15 1.25 1.55'; // Afterhours Cyan
	if (tid == 7)  return '1.55 0.48 0.10'; // Sunset Orange
	if (tid == 8)  return '0.15 1.40 1.35'; // Tropical Aqua
	if (tid == 9)  return '0.35 1.60 0.18'; // Laser Acid Green
	if (tid == 10) return '1.55 0.12 1.25'; // Turbo Magenta
	if (tid == 11) return '1.45 0.45 0.85'; // Disco Peach
	return '1.60 0.14 0.22';                // Bass Cannon Red
};

vector(float tid) Soi6_BarColorB =
{
	if (tid == 1)  return '0.12 1.05 1.55'; // Electric Cyan
	if (tid == 2)  return '0.15 0.55 1.65'; // Laser Blue
	if (tid == 3)  return '1.45 0.12 0.78'; // Magenta
	if (tid == 4)  return '0.95 0.15 1.60'; // Ultraviolet
	if (tid == 5)  return '1.45 0.35 1.15'; // Rose Pink
	if (tid == 6)  return '1.20 1.25 1.60'; // Cool White Strobe
	if (tid == 7)  return '0.14 1.32 1.15'; // Peacock Teal
	if (tid == 8)  return '1.50 0.55 0.42'; // Warm Coral
	if (tid == 9)  return '0.42 0.22 1.65'; // Electric Indigo
	if (tid == 10) return '1.50 1.02 0.16'; // Bright Gold
	if (tid == 11) return '0.72 0.22 1.55'; // Deep Violet
	return '0.20 1.12 1.60';                // Ice Blue
};

void() Soi6_PartyLightThink =
{
	local entity p;
	local float near, bphase, bstep, bfrac, punch, fade, dx, dy;
	local vector ca, cb, mixc;

	if (!autocvar_bm_soi6_lights)
	{
		self.pflags = 0;
		self.light_lev = 0;
		self.nextthink = time + 0.65;
		return;
	}

	near = 0;
	p = bm_player_head;
	while (p)
	{
		if (p.ishuman == 1)
		{
			dx = p.origin_x - self.origin_x;
			if (dx < 420 && dx > -420)
			{
				dy = p.origin_y - self.origin_y;
				if (dy < 420 && dy > -420)
				{
					near = 1;
					break;
				}
			}
		}
		p = p.bm_player_next;
	}

	if (!near)
	{
		self.pflags = 0;
		self.light_lev = 0;
		self.nextthink = time + 0.55;
		return;
	}

	// EDM kick-synced bounce envelope + alternating club color wash
	bphase = time * (self.speed / 60) + self.soi6_anim_t;
	bstep = floor (bphase);
	bfrac = bphase - bstep;
	punch = 1.0 - bfrac * 2.1;
	if (punch < 0) punch = 0;

	ca = Soi6_BarColorA (self.cnt);
	cb = Soi6_BarColorB (self.cnt);
	// Alternate smoothly across beats (odd bars crossfade smoothly, even flip crisply)
	if ((bstep % 2) == 0)
		mixc = ca;
	else
		mixc = cb;
	if ((bstep % 4) == 3 && bfrac > 0.5)
	{
		fade = (bfrac - 0.5) * 2.0;
		mixc = cb * (1.0 - fade) + ca * fade;
	}

	self.pflags = PFLAGS_FULLDYNAMIC | PFLAGS_CORONA | PFLAGS_NOSHADOW;
	self.color = mixc;
	self.light_lev = 175 + 140 * punch;
	self.nextthink = time + 0.11;
};

void(float lx, float ly, float tid, float phase_ofs) Soi6_SpawnBarLight =
{
	local entity l;
	local vector p0, p1;

	p0_x = lx;
	p0_y = ly;
	p0_z = 64;
	p1 = p0 + '0 0 66';
	traceline (p0, p1, TRUE, world);
	if (trace_fraction < 1.0)
		p0_z = trace_endpos_z - 12;
	else
		p0_z = 102;
	if (p0_z < 84) p0_z = 84;
	if (p0_z > 106) p0_z = 106;

	l = spawn ();
	l.classname = "soi6_bar_light";
	l.solid = 0;
	l.movetype = 0;
	setmodel (l, "progs/null.spr");
	setsize (l, '-4 -4 -4', '4 4 4');
	setorigin (l, p0);
	l.cnt = tid;
	l.speed = Soi6_TrackBPM (tid);
	l.soi6_anim_t = phase_ofs;
	l.think = Soi6_PartyLightThink;
	l.nextthink = time + 0.1 + random () * 0.25;
};

void(float x1_m, float x2_m, float side, float count, string bname) Soi6_SpawnBar =
{
	local float U_M, i, tier, col, cols, frac_x, x_u, y_u, cid, st;
	local float min_x, max_x, mid_x_u, y_base, stagger, tid, half_w, ph;
	local vector mus_org;

	U_M = 39.37007874;
	// Keep 0.95m inset inside bay edges to clear structural columns & side bar counters
	min_x = x1_m + 0.95;
	max_x = x2_m - 0.95;
	if (max_x <= min_x)
	{
		min_x = x1_m + 0.5;
		max_x = x2_m - 0.5;
	}
	mid_x_u = 0.5 * (x1_m + x2_m) * U_M;
	half_w = 0.5 * (x2_m - x1_m) * U_M;

	// Assign unique Thai remix / EDM bounce music + club party lights per bar
	soi6_bar_count = soi6_bar_count + 1;
	tid = soi6_bar_count;
	if (side < 0)
		tid = tid + 5;
	tid = 1 + (tid % 12);

	if (autocvar_bm_soi6_music > 0)
	{
		mus_org_x = mid_x_u;
		mus_org_y = side * 196;
		mus_org_z = 74;
		ambientsound (mus_org, Soi6_MusicTrack (tid), autocvar_bm_soi6_music, ATTN_STATIC);
	}

	ph = (soi6_bar_count * 0.37) % 2.0;
	if ((x2_m - x1_m) >= 9.5)
	{
		Soi6_SpawnBarLight (mid_x_u - half_w * 0.36, side * 204, tid, ph);
		Soi6_SpawnBarLight (mid_x_u + half_w * 0.36, side * 246, tid, ph + 1.0);
	}
	else
	{
		Soi6_SpawnBarLight (mid_x_u, side * 206, tid, ph);
	}

	cols = 3;

	for (i = 0; i < count; i = i + 1)
	{
		tier = floor (i / cols);
		col = i % cols;
		stagger = (tier % 2) * 0.08 - 0.04;
		frac_x = (col + 0.5) / cols + stagger;
		if (frac_x < 0.08) frac_x = 0.08;
		if (frac_x > 0.92) frac_x = 0.92;

		x_u = (min_x + frac_x * (max_x - min_x)) * U_M;

		// 5 clear depth zones avoiding Y_FACADE = +-167.3u wall plane & sidewalk stools (150u):
		// sidewalk curb (116u), sidewalk front (132u), inside front (200u), mid bar (238u), deep bar (278u)
		if (tier == 0) y_base = 116;
		else if (tier == 1) y_base = 132;
		else if (tier == 2) y_base = 200;
		else if (tier == 3) y_base = 238;
		else y_base = 278;
		y_u = side * (y_base + (random () - 0.5) * 10);

		soi6_seed = soi6_seed + 1;
		cid = 1 + (floor (soi6_seed + random () * 4) % 12);
		if (cid >= 9)
		{
			if (random () < 0.88) st = SOI6_DANCE; else st = SOI6_IDLE;
		}
		else
		{
			if (random () < 0.74) st = SOI6_DANCE; else st = SOI6_IDLE;
		}

		Soi6_SpawnSpot (cid, x_u, y_u, mid_x_u, side, tier, bname, st);
	}
};

void() Soi6_PopulateStreet =
{
	local entity saved_self;
	saved_self = self;
	soi6_total_count = 0;
	soi6_seed = 0;
	soi6_bar_count = 0;

	// --- NORTH SIDE BARS (+1, Y = +130..+300u) â€” 39 bars x 13-15 girls ---
	Soi6_SpawnBar (8.0,   18.0,  1, 11, "Tanyada");
	Soi6_SpawnBar (18.0,  24.0,  1, 9,  "Soi 6 Mini Bar");
	Soi6_SpawnBar (24.0,  28.4,  1, 10, "N03 Corner");
	Soi6_SpawnBar (28.4,  32.8,  1, 10, "Red Point");
	Soi6_SpawnBar (32.8,  37.2,  1, 10, "Maggie's");
	Soi6_SpawnBar (37.2,  41.6,  1, 10, "Secret Bar");
	Soi6_SpawnBar (41.6,  46.0,  1, 10, "Bamboo Bar");
	Soi6_SpawnBar (46.0,  50.0,  1, 10, "Boofie's");
	Soi6_SpawnBar (50.0,  54.0,  1, 10, "Soi 6 Salon");
	Soi6_SpawnBar (54.0,  60.0,  1, 11, "Toy Box");
	Soi6_SpawnBar (60.0,  66.0,  1, 10, "Sweet Bar");
	Soi6_SpawnBar (66.0,  71.0,  1, 10, "Repent");
	Soi6_SpawnBar (71.0,  76.0,  1, 10, "Smoke Bar");
	Soi6_SpawnBar (76.0,  81.0,  1, 11, "Wicked");
	Soi6_SpawnBar (81.0,  86.0,  1, 10, "Flirt");
	Soi6_SpawnBar (86.0,  96.0,  1, 11, "The Pussy Club");
	Soi6_SpawnBar (96.0,  102.0, 1, 11, "Horny Bar");
	Soi6_SpawnBar (102.0, 108.0, 1, 10, "Lollipop");
	Soi6_SpawnBar (108.0, 114.0, 1, 10, "Thai Baht Bar");
	Soi6_SpawnBar (114.0, 120.0, 1, 10, "Liquid");
	Soi6_SpawnBar (120.0, 126.0, 1, 10, "Chili Bar");
	Soi6_SpawnBar (126.0, 132.0, 1, 10, "Kawaii Bar");
	Soi6_SpawnBar (132.0, 137.0, 1, 10, "Butterfly");
	Soi6_SpawnBar (137.0, 142.5, 1, 10, "Lust");
	Soi6_SpawnBar (142.5, 148.0, 1, 11, "Ruby Club");
	Soi6_SpawnBar (148.0, 164.0, 1, 11, "Hero Bar");
	Soi6_SpawnBar (164.0, 170.0, 1, 10, "Desire");
	Soi6_SpawnBar (170.0, 176.0, 1, 11, "Candy Shop");
	Soi6_SpawnBar (176.0, 180.0, 1, 10, "Sugar Club");
	Soi6_SpawnBar (180.0, 186.0, 1, 10, "Poison");
	Soi6_SpawnBar (186.0, 192.0, 1, 11, "Playgirls");
	Soi6_SpawnBar (192.0, 198.0, 1, 10, "Foxy");
	Soi6_SpawnBar (198.0, 204.0, 1, 10, "Roxy");
	Soi6_SpawnBar (204.0, 212.0, 1, 11, "Sexy Bar");
	Soi6_SpawnBar (212.0, 220.0, 1, 11, "SoHo");
	Soi6_SpawnBar (248.0, 254.0, 1, 10, "Perry's");
	Soi6_SpawnBar (254.0, 261.0, 1, 11, "Love Miss");
	Soi6_SpawnBar (261.0, 268.0, 1, 11, "Mods");
	Soi6_SpawnBar (268.0, 276.0, 1, 11, "Three Angels");
	Soi6_SpawnBar (276.0, 290.0, 1, 11, "Night Lounge");
	Soi6_SpawnBar (290.0, 304.0, 1, 11, "Nikki Bar");

	// --- SOUTH SIDE BARS (-1, Y = -130..-300u) â€” 29 bars x 13-15 girls ---
	Soi6_SpawnBar (18.0,  28.0,  -1, 11, "Soi 6 Lounge");
	Soi6_SpawnBar (28.0,  38.0,  -1, 11, "Coconut Bar");
	Soi6_SpawnBar (38.0,  46.0,  -1, 10, "Bangkok Club");
	Soi6_SpawnBar (46.0,  58.0,  -1, 11, "Sandcastle");
	Soi6_SpawnBar (60.0,  68.0,  -1, 10, "Weed Lounge");
	Soi6_SpawnBar (68.0,  78.0,  -1, 11, "Panda Bar");
	Soi6_SpawnBar (78.0,  84.0,  -1, 10, "Helicopter");
	Soi6_SpawnBar (84.0,  94.0,  -1, 11, "Benders");
	Soi6_SpawnBar (94.0,  108.0, -1, 11, "Slotz Bar");
	Soi6_SpawnBar (118.0, 126.0, -1, 11, "Project Life");
	Soi6_SpawnBar (126.0, 133.8, -1, 11, "Spider Girl");
	Soi6_SpawnBar (136.0, 140.0, -1, 10, "Bandits");
	Soi6_SpawnBar (140.0, 156.0, -1, 11, "Queen Victoria");
	Soi6_SpawnBar (156.0, 160.0, -1, 10, "6/1 Lounge");
	Soi6_SpawnBar (160.0, 172.0, -1, 11, "VIP Bar");
	Soi6_SpawnBar (172.0, 182.0, -1, 11, "Exotica");
	Soi6_SpawnBar (182.0, 190.0, -1, 11, "Smoke & Mirrors");
	Soi6_SpawnBar (190.0, 204.0, -1, 11, "Amnesia");
	Soi6_SpawnBar (204.0, 212.0, -1, 11, "Green Bay");
	Soi6_SpawnBar (212.0, 220.0, -1, 11, "My Friend You");
	Soi6_SpawnBar (220.0, 238.0, -1, 11, "Hollywood");
	Soi6_SpawnBar (240.0, 250.0, -1, 11, "Direction Bar");
	Soi6_SpawnBar (250.0, 260.0, -1, 11, "Lucky Six");
	Soi6_SpawnBar (260.0, 274.0, -1, 11, "Diamond Bar");
	Soi6_SpawnBar (274.0, 286.0, -1, 11, "Passion Bar");
	Soi6_SpawnBar (286.0, 298.0, -1, 11, "Moonlight");
	Soi6_SpawnBar (298.0, 310.0, -1, 11, "Flirt South");
	Soi6_SpawnBar (310.0, 322.0, -1, 11, "Fire Bar");

	self = saved_self;
	print ("Soi6_PopulateStreet: spawned ", ftos (soi6_total_count), " entertainers across Soi 6 bars.\n");
	Alex_SpawnStreet ();
};

/*
Map-placeable Soi 6 / Soi Cowboy entertainer NPC (`npc_soi6`).
Keys:
  origin     - world position (feet/player origin; dropped to floor cleanly)
  angle      - facing yaw in degrees
  cnt        - character 1..8 (random/cycled if omitted or out of range)
  message    - bar name shown in centerprint banter (defaults to "the bar")
  pos1       - optional retreat point (defaults to settled spawn origin)
  spawnflags - 1: stationary dancer/greeter (never chases/wanders off spot)
               2: quiet (suppresses greeting voice & centerprint banter)
*/
void() npc_soi6 =
{
	local float cid, init_st;

	if (!autocvar_bm_soi6_npcs)
	{
		remove (self);
		return;
	}

	Soi6_PrecacheAssets ();

	if (self.cnt >= 1 && self.cnt <= 12)
		cid = floor (self.cnt);
	else
	{
		soi6_seed = soi6_seed + 1;
		cid = 1 + (floor (soi6_seed + random () * 4) % 12);
	}

	self.classname = "npc_soi6";
	self.soi6_id = cid;
	self.soi6_stationary = ((self.spawnflags & SOI6_SF_STATIONARY) != 0);
	self.soi6_quiet = ((self.spawnflags & SOI6_SF_QUIET) != 0);
	if (self.soi6_stationary)
		self.soi6_tier = 2;
	else
		self.soi6_tier = 0;

	if (self.message != "")
		self.soi6_bar_name = self.message;
	else
		self.soi6_bar_name = "the bar";

	self.soi6_mdl_a = Soi6_ModelA (cid);
	self.soi6_mdl_b = Soi6_ModelB (cid);

	self.health = 75;
	self.takedamage = DAMAGE_AIM;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.touch = Soi6_Touch;
	self.effects = EF_NOSHADOW;
	self.th_pain = Soi6_Pain;
	self.th_die = Soi6_Die;
	self.customizeentityforclient = Soi6_Customize;
	self.think = Soi6_Think;
	self.nextthink = time + 0.2 + random () * 0.8;

	self.soi6_home_yaw = self.angles_y;
	self.soi6_yaw = self.soi6_home_yaw;

	setmodel (self, self.soi6_mdl_a);
	setsize (self, '-12 -12 0', '12 12 54');
	setorigin (self, self.origin + '0 0 4');
	if (!droptofloor ())
	{
		setorigin (self, self.origin + '0 0 16');
		droptofloor ();
	}

	self.soi6_apron = self.origin;
	if (self.pos1 != '0 0 0')
		self.soi6_bar = self.pos1;
	else
		self.soi6_bar = self.soi6_apron;

	if (random () < 0.72) init_st = SOI6_DANCE; else init_st = SOI6_IDLE;
	self.soi6_state = -1;
	Soi6_SetState (self, init_st);
	self.soi6_state_t = time + 1.5 + random () * 6.0;
	self.soi6_chase_cd = time + 1.5 + random () * 5.0;
	self.soi6_talk_t = time + random () * 2.0;
	soi6_total_count = soi6_total_count + 1;
};

void() Soi6_Tick =
{
	if (!autocvar_bm_soi6_npcs)
		return;
	if (world.model != "maps/soi6.bsp" && world.model != "maps/soicowboy_bkk.bsp")
		return;

	if (world.model == "maps/soi6.bsp" && !soi6_spawned && time >= 0.8)
	{
		soi6_spawned = 1;
		Soi6_PopulateStreet ();
	}
};

void() Soi6_GotoStreet =
{
	setorigin (self, '3200 0 42');
	self.velocity = '0 0 0';
	self.angles = '0 0 0';
	self.v_angle = '0 0 0';
	self.fixangle = TRUE;
};

void() Soi6_GotoBarSide =
{
	setorigin (self, '5680 -20 42');
	self.velocity = '0 0 0';
	self.angles = '0 28 0';
	self.v_angle = '0 28 0';
	self.fixangle = TRUE;
};

void() Soi6_Line =
{
	local float i;
	local vector fwd, right, org;
	local entity e, saved_self;

	makevectors (self.v_angle);
	fwd = v_forward;
	fwd_z = 0;
	fwd = normalize (fwd);
	right = v_right;
	right_z = 0;
	right = normalize (right);

	saved_self = self;
	for (i = 1; i <= 12; i = i + 1)
	{
		org = saved_self.origin + fwd * 225 + right * ((i - 6.5) * 20) + '0 0 24';
		e = spawn ();
		e.classname = "npc_soi6";
		e.soi6_id = i;
		e.soi6_lineup = 1;
		e.soi6_apron = org;
		e.soi6_bar = org;
		e.soi6_bar_name = "Soi 6";
		e.soi6_mdl_a = Soi6_ModelA (i);
		e.soi6_mdl_b = Soi6_ModelB (i);
		e.health = 75;
		e.takedamage = DAMAGE_AIM;
		e.solid = SOLID_SLIDEBOX;
		e.movetype = MOVETYPE_STEP;
		e.touch = Soi6_Touch;
		e.effects = EF_NOSHADOW;
		e.th_pain = Soi6_Pain;
		e.th_die = Soi6_Die;
		e.customizeentityforclient = Soi6_Customize;
		e.think = Soi6_Think;
		e.nextthink = time + 0.25;
		e.soi6_yaw = vectoyaw (-fwd);
		e.soi6_home_yaw = e.soi6_yaw;
		setmodel (e, e.soi6_mdl_a);
		setsize (e, '-12 -12 0', '12 12 54');
		setorigin (e, org);
		self = e;
		droptofloor ();
		e.soi6_state = -1;
		Soi6_SetState (e, SOI6_DANCE);
	}
	self = saved_self;
	sprint (self, "Soi6_Line: spawned all 12 entertainers in front of you.\n");
};

void(float dmg) Soi6_Poke =
{
	local entity e, best;
	local float bestd, d;
	local vector aim_pt;

	makevectors (self.v_angle);
	aim_pt = self.origin + v_forward * 195;

	best = world;
	bestd = 99999;
	e = find (world, classname, "npc_soi6");
	while (e)
	{
		if (e.health > 0)
		{
			d = vlen (e.origin - aim_pt);
			if (d < bestd)
			{
				bestd = d;
				best = e;
			}
		}
		e = find (e, classname, "npc_soi6");
	}
	if (!best)
	{
		sprint (self, "Soi6_Poke: no living entertainer found.\n");
		return;
	}
	T_Damage (best, self, self, dmg);
};

/*
================
ALEX PATTAYA GUY (npc_alex_pattaya)

Tanky Soi 6 street NPC:
  - Patrols up and down Soi 6 (x = 650..12200, y near 0) with swagger flex pauses
  - Talks shit (12 real voice clips + centerprint quotes) when approached or shot
  - 1500 HP, knockback-immune (MOVETYPE_STEP + velocity zeroed)
  - When shot, rallies up to 35 nearby non-stationary bar girls to swarm the shooter
  - Respawns 20s after death back onto Soi 6
================
*/

string(float idx) Alex_ClipSound =
{
	if (idx == 1) return "alex_pattaya/talk_1.ogg";
	if (idx == 2) return "alex_pattaya/talk_2.ogg";
	if (idx == 3) return "alex_pattaya/talk_3.ogg";
	if (idx == 4) return "alex_pattaya/talk_4.ogg";
	if (idx == 5) return "alex_pattaya/talk_5.ogg";
	if (idx == 6) return "alex_pattaya/talk_6.ogg";
	if (idx == 7) return "alex_pattaya/talk_7.ogg";
	if (idx == 8) return "alex_pattaya/talk_8.ogg";
	if (idx == 9) return "alex_pattaya/talk_9.ogg";
	if (idx == 10) return "alex_pattaya/talk_10.ogg";
	if (idx == 11) return "alex_pattaya/talk_11.ogg";
	return "alex_pattaya/talk_12.ogg";
};

string(float idx) Alex_ClipQuote =
{
	if (idx == 1) return "\"All you on the damn David Bond group!\"";
	if (idx == 2) return "\"Get off your lazy asses and be doing what I'm doing!\"";
	if (idx == 3) return "\"I'm always stocked with the alcohol at any given time!\"";
	if (idx == 4) return "\"Does David Bond have bling like this? Gold like this?\"";
	if (idx == 5) return "\"Just trying to chill, enjoy my life, even though I don't work!\"";
	if (idx == 6) return "\"And you know why? Because I fucking can, goddamn it!\"";
	if (idx == 7) return "\"Because I fucking like cameras! I do whatever I want to do!\"";
	if (idx == 8) return "\"Come on, I'll show you guys the beast real quick!\"";
	if (idx == 9) return "\"Got a fucking porno studio! You guys have a porno studio?\"";
	if (idx == 10) return "\"Is that a window looking into my pool? Goddamn straight it is!\"";
	if (idx == 11) return "\"Look, I'm just sick and tired of it!\"";
	return "\"I got a day one to pay double the price, motherfuckers!\"";
};

void(entity ent, float st) Alex_SetState =
{
	if (ent.soi6_state == st)
		return;
	ent.soi6_state = st;
	ent.soi6_anim_t = time;
	if (st == ALEX_DEAD || st == ALEX_GIB)
		setmodel (ent, "progs/alex_pattaya_b.md3");
	else if (ent.model != "progs/alex_pattaya_a.md3")
	{
		setmodel (ent, "progs/alex_pattaya_a.md3");
		setsize (ent, '-14 -14 0', '14 14 58');
	}
};

void(entity ent, entity target_pl, float is_shot) Alex_Talk =
{
	local float idx, hp;
	local string q;

	if (!ent.alex_quote_id)
		ent.alex_quote_id = 1;

	if (time >= ent.soi6_talk_t)
	{
		idx = 1 + floor (random () * 12);
		if (idx == ent.alex_quote_id)
			idx = 1 + (idx % 12);
		ent.alex_quote_id = idx;
		sound (ent, CHAN_VOICE, Alex_ClipSound (idx), 1, ATTN_NORM);
		dprint ("Alex_Talk: clip ", ftos (idx), " -> ", Alex_ClipSound (idx), "\n");
		if (is_shot)
			ent.soi6_talk_t = time + 2.2;
		else
			ent.soi6_talk_t = time + 3.4 + random () * 1.4;
	}

	if (target_pl && (target_pl.flags & FL_CLIENT) && (!is_shot || time >= target_pl.alex_cp_t))
	{
		if (is_shot)
			target_pl.alex_cp_t = time + 1;		// a nailgun / lightning gun hits ~10 times a second
		q = Alex_ClipQuote (ent.alex_quote_id);
		hp = ceil (ent.health);
		if (hp < 0)
			hp = 0;
		if (is_shot)
			centerprint (target_pl, strcat ("ALEX PATTAYA [HP: ", ftos (hp), " / ", ftos (ALEX_MAX_HP), "]\n", q));
		else
			centerprint (target_pl, strcat ("ALEX PATTAYA\n", q));
	}
};

float(entity alex, entity attacker) Soi6_TriggerSwarm =
{
	local entity e;
	local float n, d_alex, d_att;

	if (!attacker || !(attacker.flags & FL_CLIENT) || attacker.health <= 0)
		return 0;

	n = 0;
	e = find (world, classname, "npc_soi6");
	while (e && n < 35)
	{
		if (e.health > 0 && !e.soi6_stationary && !e.soi6_lineup && e.soi6_state != SOI6_DEAD && e.soi6_state != SOI6_GIB)
		{
			d_alex = vlen (e.origin - alex.origin);
			d_att = vlen (e.origin - attacker.origin);
			if (d_alex <= 720 || d_att <= 560)
			{
				e.soi6_target = attacker;
				e.enemy = attacker;
				e.soi6_state_t = time + 8.0;
				if (e.soi6_state != SOI6_SWARM)
				{
					Soi6_SetState (e, SOI6_SWARM);
					e.soi6_swarm_atk = time + 0.35 + random () * 0.45;
					e.nextthink = time + 0.05;
				}
				n = n + 1;
			}
		}
		e = find (e, classname, "npc_soi6");
	}
	if (n > 0)
		dprint ("Soi6_TriggerSwarm: ", ftos (n), " bar girls swarming!\n");
	return n;
};

float() Alex_Customize =
{
	local vector v;
	local float dx, dy, rel, d, elapsed, f;

	dx = other.origin_x - self.origin_x;
	if (dx > 2200 || dx < -2200)
		return FALSE;
	dy = other.origin_y - self.origin_y;
	if (dy > 2200 || dy < -2200)
		return FALSE;
	if ((dx * dx + dy * dy) > 4840000)
		return FALSE;
	if (other.ishuman != 1)
		return FALSE;

	self.angles_y = other.v_angle_y;
	self.angles_x = 0;
	self.angles_z = 0;

	v = other.origin - self.origin;
	rel = vectoyaw (v) - self.soi6_yaw;
	if (rel < 0)
		rel = rel + 360;
	else if (rel >= 360)
		rel = rel - 360;
	if (rel < 0)
		rel = rel + 360;
	d = floor (rel / 45 + 0.5);
	if (d >= 8)
		d = d - 8;

	elapsed = time - self.soi6_anim_t;
	if (elapsed < 0)
		elapsed = 0;

	if (self.soi6_state == ALEX_DEAD)
	{
		f = floor (elapsed * 14);
		if (f > 5) f = 5;
		self.skin = f * 8 + d;
		return TRUE;
	}
	if (self.soi6_state == ALEX_GIB)
	{
		f = floor (elapsed * 18);
		if (f > 7) f = 7;
		self.skin = (6 + f) * 8 + d;
		return TRUE;
	}

	if (self.soi6_state == ALEX_IDLE)
		f = floor (elapsed * 12) % 6;
	else if (self.soi6_state == ALEX_STRUT)
		f = 6 + (floor (elapsed * 14) % 12);
	else if (self.soi6_state == ALEX_TALK)
		f = 26 + (floor (elapsed * 14) % 5);
	else
		f = 18 + (floor (elapsed * 16) % 8);

	self.skin = f * 8 + d;
	return TRUE;
};

void() Alex_Respawn =
{
	local float rx;
	local vector cand;

	rx = 1600 + random () * 8800;
	cand_x = rx;
	cand_y = (random () - 0.5) * 48;
	cand_z = 8;
	if (!Soi6_SpotClear (cand))
		cand = '3350 0 8';

	self.health = ALEX_MAX_HP;
	self.max_health = ALEX_MAX_HP;
	self.takedamage = DAMAGE_AIM;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.touch = Alex_Touch;
	self.soi6_pass_t = 0;
	self.velocity = '0 0 0';
	self.soi6_target = world;
	self.enemy = world;
	self.alex_stuck = 0;

	setmodel (self, "progs/alex_pattaya_a.md3");
	setsize (self, '-14 -14 0', '14 14 58');
	setorigin (self, cand + '0 0 6');
	droptofloor ();
	Soi6_UpdatePassThrough (14);

	if (random () < 0.5)
		self.alex_dir = 0;
	else
		self.alex_dir = 180;
	self.soi6_yaw = self.alex_dir;
	Alex_SetState (self, ALEX_WALK);
	self.soi6_state_t = time + 6 + random () * 5;
	self.soi6_talk_t = time + 0.5;
	self.nextthink = time + 0.1;

	bprint ("Alex Pattaya Guy is back strutting down Soi 6!\n");
	sound (self, CHAN_VOICE, Alex_ClipSound (6), 1, ATTN_NORM);
};

void(entity attacker, float damage) Alex_Pain =
{
	local vector dvec;
	local float swarmed;

	if (self.health <= 0 || self.soi6_state == ALEX_DEAD || self.soi6_state == ALEX_GIB)
		return;

	self.velocity = '0 0 0';
	self.soi6_target = attacker;
	if (attacker && attacker != world)
	{
		self.enemy = attacker;
		dvec = attacker.origin - self.origin;
		dvec_z = 0;
		if (vlen (dvec) > 2)
			self.soi6_yaw = vectoyaw (dvec);
	}

	Alex_SetState (self, ALEX_TALK);
	self.soi6_state_t = time + 2.2;
	self.nextthink = time + 0.1;

	Alex_Talk (self, attacker, TRUE);
	swarmed = 0;
	if (attacker != world && time >= attacker.soi6_swarm_t)		// the swarm lasts 8 s: re-arming it on every hit only cost a find() per hit
	{
		attacker.soi6_swarm_t = time + 0.75;
		swarmed = Soi6_TriggerSwarm (self, attacker);
	}
	if (swarmed > 0 && attacker && (attacker.flags & FL_CLIENT) && time >= soi6_chat_cd)
	{
		soi6_chat_cd = time + 2.5;
		sprint (attacker, "Soi 6 girls are swarming you for shooting Alex!\n");
	}
};

void() Alex_Die =
{
	local entity att;

	if (self.soi6_state == ALEX_DEAD || self.soi6_state == ALEX_GIB)
		return;

	att = self.enemy;
	if (!att || !(att.flags & FL_CLIENT))
		att = self.soi6_target;
	if (att && (att.flags & FL_CLIENT))
		Soi6_TriggerSwarm (self, att);

	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';

	if (self.health < -40)
	{
		Alex_SetState (self, ALEX_GIB);
		Soi6_SpawnPlayerGibs ();
	}
	else
	{
		Alex_SetState (self, ALEX_DEAD);
	}

	sound (self, CHAN_VOICE, Alex_ClipSound (11), 1, ATTN_NORM);
	if (att && (att.flags & FL_CLIENT))
		centerprint (att, "ALEX PATTAYA IS DOWN!\nHe respawns on Soi 6 in 20s...");
	bprint ("Someone finally dropped Alex Pattaya Guy! Respawn in 20s.\n");

	self.soi6_respawn_t = time + 20;
	self.nextthink = time + 0.5;
};

void() Alex_Touch =
{
	if (!other || other.classname != "player" || other.health <= 0)
		return;
	if (self.soi6_state == ALEX_DEAD || self.soi6_state == ALEX_GIB)
		return;

	self.solid = SOLID_CORPSE;
	self.soi6_pass_t = time + 0.45;
};

void() Alex_Think =
{
	local entity p;
	local vector dir;
	local float wy, d_p;

	if (self.soi6_state == ALEX_DEAD || self.soi6_state == ALEX_GIB)
	{
		self.nextthink = time + 0.5;
		if (self.soi6_state == ALEX_GIB && time > self.soi6_anim_t + 0.45 && self.modelindex)
			setmodel (self, "");		// the engine draws by modelindex: clearing .model alone left the last gib frame up
		if (time >= self.soi6_respawn_t)
			Alex_Respawn ();
		return;
	}

	Soi6_UpdatePassThrough (14);

	self.nextthink = time + 0.1;
	self.velocity = '0 0 0';

	p = Soi6_NearestPlayerFast (self, 215);
	if (p != world)
	{
		d_p = vlen (p.origin - self.origin);
		if (d_p <= 215 && time >= self.soi6_talk_t)
		{
			self.soi6_target = p;
			dir = p.origin - self.origin;
			dir_z = 0;
			if (vlen (dir) > 2)
				self.soi6_yaw = vectoyaw (dir);
			Alex_SetState (self, ALEX_TALK);
			self.soi6_state_t = time + 2.2;
			Alex_Talk (self, p, FALSE);
			return;
		}
	}

	if (self.soi6_state == ALEX_TALK)
	{
		p = self.soi6_target;
		if (p && p != world && p.health > 0 && vlen (p.origin - self.origin) < 480)
		{
			dir = p.origin - self.origin;
			dir_z = 0;
			if (vlen (dir) > 2)
				self.soi6_yaw = vectoyaw (dir);
		}
		if (time >= self.soi6_state_t)
		{
			Alex_SetState (self, ALEX_WALK);
			self.soi6_state_t = time + 6 + random () * 5;
			self.soi6_yaw = self.alex_dir;
		}
		return;
	}

	if (self.soi6_state == ALEX_STRUT)
	{
		if (time >= self.soi6_state_t)
		{
			Alex_SetState (self, ALEX_WALK);
			self.soi6_state_t = time + 7 + random () * 6;
			self.soi6_yaw = self.alex_dir;
		}
		return;
	}

	// Patrol up and down the middle of Soi 6 (Beach Rd x~650 <-> Second Rd x~12200)
	if (self.origin_x >= 12200)
		self.alex_dir = 180;
	else if (self.origin_x <= 650)
		self.alex_dir = 0;

	wy = self.alex_dir;
	if (self.origin_y > 42)
	{
		if (wy == 0) wy = 345;
		else wy = 195;
	}
	else if (self.origin_y < -42)
	{
		if (wy == 0) wy = 15;
		else wy = 165;
	}

	self.soi6_yaw = wy;
	self.angles_y = wy;
	if (walkmove (wy, 13.5))
		self.alex_stuck = 0;
	else if (walkmove (wy + 35, 12.5))
	{
		self.soi6_yaw = wy + 35;
		self.alex_stuck = 0;
	}
	else if (walkmove (wy - 35, 12.5))
	{
		self.soi6_yaw = wy - 35;
		self.alex_stuck = 0;
	}
	else if (walkmove (wy + 75, 11))
	{
		self.soi6_yaw = wy + 75;
		self.alex_stuck = 0;
	}
	else if (walkmove (wy - 75, 11))
	{
		self.soi6_yaw = wy - 75;
		self.alex_stuck = 0;
	}
	else
	{
		self.alex_stuck = self.alex_stuck + 1;
		if (self.alex_stuck >= 8)
		{
			self.alex_stuck = 0;
			if (self.alex_dir == 0)
				self.alex_dir = 180;
			else
				self.alex_dir = 0;
			self.soi6_yaw = self.alex_dir;
		}
	}

	if (time >= self.soi6_state_t)
	{
		Alex_SetState (self, ALEX_STRUT);
		self.soi6_state_t = time + 2.2 + random () * 1.4;
	}
};

entity(vector org, float heading) Alex_SpawnAt =
{
	local entity e, saved;

	Soi6_PrecacheAssets ();
	e = spawn ();
	e.classname = "npc_alex_pattaya";
	e.health = ALEX_MAX_HP;
	e.max_health = ALEX_MAX_HP;
	e.takedamage = DAMAGE_AIM;
	e.solid = SOLID_SLIDEBOX;
	e.movetype = MOVETYPE_STEP;
	e.touch = Alex_Touch;
	e.effects = EF_NOSHADOW;
	e.th_pain = Alex_Pain;
	e.th_die = Alex_Die;
	e.customizeentityforclient = Alex_Customize;
	e.think = Alex_Think;
	e.nextthink = time + 0.15;

	e.alex_dir = heading;
	e.soi6_yaw = heading;
	e.soi6_home_yaw = heading;
	setmodel (e, "progs/alex_pattaya_a.md3");
	setsize (e, '-14 -14 0', '14 14 58');
	setorigin (e, org + '0 0 8');
	e.soi6_state = -1;
	Alex_SetState (e, ALEX_WALK);
	e.soi6_state_t = time + 6;
	e.soi6_talk_t = time + 0.4;

	saved = self;
	self = e;
	droptofloor ();
	self = saved;

	alex_boss = e;
	return e;
};

void() Alex_SpawnStreet =
{
	if (alex_boss && alex_boss != world && alex_boss.classname == "npc_alex_pattaya")
		return;
	Alex_SpawnAt ('3350 0 8', 0);
	print ("Alex_SpawnStreet: Alex Pattaya Guy spawned on Soi 6 (1500 HP).\n");
};

void() Soi6_SummonAlex =
{
	local vector fwd, dst;
	local entity saved;

	makevectors (self.v_angle);
	fwd = v_forward;
	fwd_z = 0;
	if (vlen (fwd) < 0.01)
		fwd = '1 0 0';
	fwd = normalize (fwd);
	dst = self.origin + fwd * 180 + '0 0 8';

	if (!alex_boss || alex_boss == world || alex_boss.classname != "npc_alex_pattaya")
		Alex_SpawnAt (dst, vectoyaw (-fwd));
	else
	{
		alex_boss.health = ALEX_MAX_HP;
		alex_boss.takedamage = DAMAGE_AIM;
		alex_boss.solid = SOLID_SLIDEBOX;
		alex_boss.movetype = MOVETYPE_STEP;
		alex_boss.touch = Alex_Touch;
		alex_boss.velocity = '0 0 0';
		setmodel (alex_boss, "progs/alex_pattaya_a.md3");
		setsize (alex_boss, '-14 -14 0', '14 14 58');
		setorigin (alex_boss, dst);
		alex_boss.soi6_yaw = vectoyaw (-fwd);
		alex_boss.alex_dir = alex_boss.soi6_yaw;
		Alex_SetState (alex_boss, ALEX_STRUT);
		alex_boss.soi6_state_t = time + 3.0;
		alex_boss.nextthink = time + 0.1;

		saved = self;
		self = alex_boss;
		droptofloor ();
		self = saved;
	}
	sprint (self, "Soi6_SummonAlex: Alex Pattaya Guy summoned in front of you.\n");
};

void() Soi6_GotoAlex =
{
	local vector dvec, spot;

	if (!alex_boss || alex_boss == world || alex_boss.classname != "npc_alex_pattaya")
		Alex_SpawnStreet ();

	if (!alex_boss || alex_boss == world)
		return;

	spot = alex_boss.origin + '-185 0 18';
	setorigin (self, spot);
	self.velocity = '0 0 0';
	dvec = alex_boss.origin - self.origin;
	dvec_z = 0;
	self.angles = '0 0 0';
	self.angles_y = vectoyaw (dvec);
	self.v_angle = self.angles;
	self.fixangle = TRUE;
	sprint (self, "Soi6_GotoAlex: teleported facing Alex Pattaya Guy.\n");
};

void(float dmg) Soi6_PokeAlex =
{
	if (!alex_boss || alex_boss == world || alex_boss.classname != "npc_alex_pattaya")
	{
		sprint (self, "Soi6_PokeAlex: Alex not spawned.\n");
		return;
	}
	if (alex_boss.health <= 0)
	{
		sprint (self, "Soi6_PokeAlex: Alex is already down waiting to respawn.\n");
		return;
	}
	T_Damage (alex_boss, self, self, dmg);
};
