#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE BONK HAMMER (see hammer_defs.qc for the rules and numbers)

A port of Bonk Jam's w_hammer.qc (default hammer). The swing (Hammer_Swing / Hammer_Hit) is Bonk's W_SwingHammer /
hithammer line for line; the animation chains are rebuilt as a timeline (Hammer_PlayerFrame) with the same frames
and timings, because Bonk ran them on the player's think with player.mdl frames Combat+ doesn't have.
Hooks (patch_hammer_combat.py): W_WeaponFrame runs Hammer_PlayerFrame every frame (it owns the fire button and
impulse 1 while the hammer is out) and skips W_Attack for IT_AXE; PutClientInServer runs Hammer_Spawn.
================
*/

// view-model frames of v_hammer.mdl, by tier (1 LOW, 2 MED, 3 HIGH)
float(float tier) Hammer_FrameRelease =	{ if (tier == 3) return 40; if (tier == 2) return 77; return 114; };
float(float tier) Hammer_FrameHit =		{ if (tier == 3) return 41; if (tier == 2) return 78; return 115; };
float(float tier) Hammer_FrameDash =	{ if (tier == 3) return 59; if (tier == 2) return 96; return 133; };
float(float tier) Hammer_FrameHop =		{ if (tier == 3) return 68; if (tier == 2) return 105; return 142; };
float(float tier) Hammer_FrameWhiff =	{ if (tier == 3) return 159; if (tier == 2) return 168; return 177; };
float(float tier) Hammer_Multi =		{ if (tier == 3) return HM_MULTI_HIGH; if (tier == 2) return HM_MULTI_MED; return HM_MULTI_LOW; };
float(float tier) Hammer_Damage =		{ if (tier == 3) return HM_DAMAGE_HIGH; if (tier == 2) return HM_DAMAGE_MED; return HM_DAMAGE_LOW; };

void() Hammer_Precache =
{
	precache_model ("progs/v_hammer.mdl");
	precache_model ("progs/spark_blue.mdl");
	precache_model ("progs/spark_yellow.mdl");
	precache_sound ("hammer/charge_med.wav");
	precache_sound ("hammer/charge_full.wav");
	precache_sound ("hammer/hammer_clang.wav");
	precache_sound ("hammer/hammer_clang2.wav");
	precache_sound ("hammer/slice1.wav");
	precache_sound ("hammer/slice2.wav");
	precache_sound ("hammer/slice3.wav");
	precache_sound ("hammer/frying_pan.wav");
	precache_sound ("hammer/axhit1.wav");
	precache_sound ("hammer/axhit2.wav");
	precache_sound ("weapons/ax1.wav");
};

void(string samp, float vol) Hammer_Snd =
{
	sound7 (self, CHAN_AUTO, samp, vol, ATTN_NORM, SNDSPD);
};

void() Hammer_HitSound =
{
	SuperDamageSound ();
	if (random () < 0.5)
		Hammer_Snd ("hammer/axhit1.wav", 0.65);
	else
		Hammer_Snd ("hammer/axhit2.wav", 0.65);
};

// ---------------------------------------------------------------- sparks (Spark_Activate, x_spark_01..07)

void() Hammer_SparkThink =
{
	self.cnt = self.cnt + 1;
	if (self.cnt >= 7)
	{
		remove (self);
		return;
	}
	self.frame = self.frame + 1;
	self.nextthink = time + 0.05;
};

// kind 1 = dash (blue), 2 = hop (yellow); 7 frames per tier
void(float kind, float tier) Hammer_Spark =
{
	local entity spark;

	makevectors (self.v_angle);
	spark = spawn ();
	spark.owner = self;
	spark.movetype = MOVETYPE_NONE;
	spark.solid = SOLID_NOT;
	spark.angles = vectoangles (v_forward);
	if (kind == 1)
		setmodel (spark, "progs/spark_blue.mdl");
	else
		setmodel (spark, "progs/spark_yellow.mdl");
	setsize (spark, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (spark, self.origin + v_forward * 32 + '0 0 16');
	spark.frame = (tier - 1) * 7;
	spark.think = Hammer_SparkThink;
	spark.nextthink = time + 0.05;
};

// ---------------------------------------------------------------- the swing (W_SwingHammer / hithammer)

entity	hm_h1, hm_h2;
float	hm_d1, hm_d2;
vector	hm_p1, hm_p2, hm_src;

// one of the five traces: keep the nearest two different things
void() Hammer_Consider =
{
	local float d;

	if (trace_fraction >= 1)
		return;
	d = vlen (trace_endpos - hm_src);
	if (hm_d1 == 1000 || trace_ent == hm_h1)
	{
		if (d < hm_d1)
		{
			hm_d1 = d;
			hm_h1 = trace_ent;
			hm_p1 = trace_endpos;
		}
		return;
	}
	if (d < hm_d2)
	{
		hm_d2 = d;
		hm_h2 = trace_ent;
		hm_p2 = trace_endpos;
	}
};

void(entity hitent, vector org, vector dir, float tier, float hitfloor) Hammer_Hit =
{
	local vector toss;
	local float multi, dmg, height;

	makevectors (self.v_angle);
	multi = Hammer_Multi (tier);
	dmg = Hammer_Damage (tier);
	if (hitent.takedamage)
	{
		// a monster one hit from death takes double: it gibs (Bonk's overkill)
		if ((hitent.flags & FL_MONSTER) && hitent.health <= dmg)
		{
			SpawnBlood (org, dir, dmg * 2);
			T_Damage (hitent, self, self, dmg * 2);
			if (random () < 0.5)
				Hammer_Snd ("hammer/axhit1.wav", 0.65);
			else
				Hammer_Snd ("hammer/axhit2.wav", 0.65);
			if (tier == 1)
				Hammer_Snd ("hammer/frying_pan.wav", 0.25);
			else if (tier == 2)
				Hammer_Snd ("hammer/frying_pan.wav", 0.5);
			else
				Hammer_Snd ("hammer/frying_pan.wav", 1);
			self.hm_result = Hammer_FrameHit (tier);
			Hammer_HitSound ();
			return;
		}
		else if (hitent.classname == "player")
		{
			// the frying-pan clang on players too: Bonk only had it for monster overkills, so in deathmatch nobody ever heard it
			if (tier == 1)
				Hammer_Snd ("hammer/frying_pan.wav", 0.4);
			else if (tier == 2)
				Hammer_Snd ("hammer/frying_pan.wav", 0.7);
			else
				Hammer_Snd ("hammer/frying_pan.wav", 1);
		}
		// swat anything that walks and isn't huge, players included
		if ((hitent.movetype == MOVETYPE_STEP || hitent.movetype == MOVETYPE_WALK || (hitent.ishuman != 1 && hitent.classname == "player")) && hitent.maxs_x <= 32 && hitent.health > 0)
		{
			toss = v_forward;
			toss_z = 0;
			if (self.super_damage_finished > time)
			{
				toss = normalize (toss) * (multi * HM_KNOCKBACK_QUAD);
				toss_z = multi * HM_KNOCKBACK_QUAD_UP;
			}
			else
			{
				toss = normalize (toss) * (multi * HM_KNOCKBACK);
				toss_z = multi * HM_KNOCKBACK_UP;
			}
			setorigin (hitent, hitent.origin + '0 0 1');
			hitent.velocity = toss;
			hitent.flags = hitent.flags - (hitent.flags & FL_ONGROUND);
		}
		SpawnBlood (org, dir, dmg);
		T_Damage (hitent, self, self, dmg);
		self.hm_result = Hammer_FrameHit (tier);
		Hammer_HitSound ();
		return;
	}

	// the world (or anything that can't be hurt): the bonk hop
	if (tier == 1)
	{
		height = HM_HOP_LOW;
		Hammer_Snd ("hammer/hammer_clang2.wav", 0.3);
	}
	else if (tier == 2)
	{
		height = HM_HOP_MED;
		Hammer_Snd ("hammer/hammer_clang2.wav", 0.6);
	}
	else
	{
		height = HM_HOP_HIGH;
		Hammer_Snd ("hammer/hammer_clang.wav", 0.8);
	}
	self.hm_result = Hammer_FrameHop (tier);
	Hammer_Spark (2, tier);
	self.effects = self.effects | EF_MUZZLEFLASH;
	// how high off the floor are we? launch so the top of the hop is always the same height over it
	traceline (self.origin - '0 0 24', self.origin - '0 0 88', TRUE, self);
	self.velocity = self.velocity + v_forward * (multi * HM_HOP_BACKWARD);
	if (trace_fraction < 1 && hitfloor)
		self.velocity_z = sqrt (2 * ((height + 32) - (trace_fraction * 64)) * cvar ("sv_gravity"));
	self.flags = self.flags - (self.flags & FL_ONGROUND);
	sendParticle ("TE_GUNSHOT", org, VEC_ORIGIN, 1, 0);
};

void(float tier) Hammer_Swing =
{
	local float multi, hitfloor, d1, d2;
	local entity h1, h2;
	local vector p1, p2, dir;

	multi = Hammer_Multi (tier);
	makevectors (self.v_angle);
	hm_src = self.origin + self.view_ofs - v_up * 6;
	hm_h1 = world;
	hm_h2 = world;
	hm_d1 = 1000;
	hm_d2 = 1000;
	hitfloor = FALSE;

	traceline (hm_src, hm_src + v_forward * 64 - v_right * 16, FALSE, self);
	if (trace_fraction < 1)
	{
		hm_d1 = vlen (trace_endpos - hm_src);
		hm_h1 = trace_ent;
		hm_p1 = trace_endpos;
	}
	traceline (hm_src, hm_src + v_forward * 96 - v_right * 8, FALSE, self);
	Hammer_Consider ();
	traceline (hm_src, hm_src + v_forward * 128, FALSE, self);
	Hammer_Consider ();
	if (trace_fraction < 1 && trace_plane_normal_z > 0.71)
		hitfloor = TRUE;		// only the middle trace can make a hop
	traceline (hm_src, hm_src + v_forward * 96 + v_right * 8, FALSE, self);
	Hammer_Consider ();
	traceline (hm_src, hm_src + v_forward * 64 + v_right * 16, FALSE, self);
	Hammer_Consider ();

	if (hm_d1 == 1000 && hm_d2 == 1000)
	{
		if (!(self.flags & FL_ONGROUND))
		{
			// nothing there and we're in the air: dash
			self.hm_result = Hammer_FrameDash (tier);
			Hammer_Spark (1, tier);
			if (tier == 1)
				Hammer_Snd ("hammer/slice1.wav", 0.25);
			else if (tier == 2)
				Hammer_Snd ("hammer/slice2.wav", 0.5);
			else
				Hammer_Snd ("hammer/slice3.wav", 1);
			self.velocity = self.velocity + v_forward * (multi * HM_DASH_FORWARD);
			if (tier > 1 && self.velocity_z < HM_DASH_UPWARD)
				self.velocity_z = HM_DASH_UPWARD;
		}
		else
			self.hm_result = Hammer_FrameWhiff (tier);
		return;
	}

	self.show_hostile = time + 1;
	dir = v_right * 20 - v_up * 5;		// blood spray direction
	h1 = hm_h1;
	h2 = hm_h2;
	d1 = hm_d1;
	d2 = hm_d2;
	p1 = hm_p1 - v_forward * 4;
	p2 = hm_p2 - v_forward * 4;
	if (d1 < 1000)
		Hammer_Hit (h1, p1, dir, tier, hitfloor);
	if (d2 < 1000 && h1 != h2)
		Hammer_Hit (h2, p2, dir, tier, hitfloor);
};

// ---------------------------------------------------------------- the third-person swing (axe frames, no stock axe hit)

void() Hammer_Body2;
void() Hammer_Body3;
void() Hammer_Body4;
void() Hammer_Body1 = [ 119, Hammer_Body2 ] {};
void() Hammer_Body2 = [ 120, Hammer_Body3 ] {};
void() Hammer_Body3 = [ 121, Hammer_Body4 ] {};
void() Hammer_Body4 = [ 122, player_run ] {};

// ---------------------------------------------------------------- per frame

void() Hammer_StartCharge =
{
	self.hm_state = 1;
	self.hm_t0 = time;
	self.hm_tier = 1;
};

void() Hammer_Release =
{
	self.hm_state = 2;
	self.hm_t0 = time;
	self.hm_swung = FALSE;
	self.hm_result = Hammer_FrameWhiff (self.hm_tier);
	Hammer_Snd ("weapons/ax1.wav", 1);
	Hammer_Body1 ();
};

// top of W_WeaponFrame, every frame: charge, swing and spin while the hammer is in hand
void() Hammer_PlayerFrame =
{
	local float el, k, tier;

	if (self.weapon != IT_AXE || self.meleeing == 1 || self.throwing == 1)
	{
		self.hm_state = 0;		// put away, or Combat+'s kick / grenade throw took over the hands
		return;
	}
	if (self.health <= 0 || self.deadflag || intermission_running
		|| self.jb_vehicle != world || self.rr_vehicle != world || self.veh_van != world || self.mmt_tank != world || FD_Flying (self) || EricCannon_Active (self) || Binoc_On (self))
	{
		self.hm_state = 0;		// flying Winged John / Rob Dob, Eric Cannon, binoculars, or driving: fire belongs to the vehicle, no charge or swing
		return;
	}

	// R (BM_RELOAD_IMPULSE) with the hammer out: the spinny twirl (leaves key 1 free to toggle Bonk Hammer <-> Chainsaw!)
	if (self.impulse == BM_RELOAD_IMPULSE)
	{
		self.impulse = 0;
		if (self.hm_state == 0 || (self.hm_state == 2 && time >= self.hm_ready) || self.hm_state == 3)
		{
			self.hm_state = 3;
			self.hm_t0 = time;
			self.hm_ready = time + 0.4;
		}
	}

	// fire starts a charge once the last swing's cooldown is over (it cuts the follow-through short)
	if (self.button0 && self.hm_state != 1 && time >= self.hm_ready && time >= self.attack_finished)
		Hammer_StartCharge ();

	el = time - self.hm_t0;
	if (self.hm_state == 1)
	{
		// wind-up: frames 1-14 LOW, 15-27 MED, 28-29 HIGH, then 30-39 looping, 20 a second
		k = floor (el / 0.05);
		if (k < 29)
			self.weaponframe = k + 1;
		else
			self.weaponframe = 30 + (k - 29) - floor ((k - 29) / 10) * 10;
		tier = 1;
		if (k >= 21)
			tier = 3;
		else if (k >= 12)
			tier = 2;
		if (tier > self.hm_tier)
		{
			self.hm_tier = tier;
			if (tier == 2)
				Hammer_Snd ("hammer/charge_med.wav", 0.4);
			else
				Hammer_Snd ("hammer/charge_full.wav", 0.8);
		}
		if (!self.button0)
			Hammer_Release ();
		return;
	}
	if (self.hm_state == 2)
	{
		if (!self.hm_swung && el >= 0.025)
		{
			self.hm_swung = TRUE;
			Hammer_Swing (self.hm_tier);
			self.hm_ready = time + HM_COOLDOWN;
		}
		// release frame, the outcome, 8 frames of follow-through, then the cooldown frames 151-158
		if (el < 0.05)
			self.weaponframe = Hammer_FrameRelease (self.hm_tier);
		else if (el < 0.075)
			self.weaponframe = self.hm_result;
		else if (el < 0.1)
			self.weaponframe = self.hm_result + 1;
		else
		{
			k = floor ((el - 0.1) / 0.05);
			if (k <= 6)
				self.weaponframe = self.hm_result + 2 + k;
			else if (k <= 14)
				self.weaponframe = 151 + (k - 7);
			else
			{
				self.weaponframe = 0;
				self.hm_state = 0;
			}
		}
		return;
	}
	if (self.hm_state == 3)
	{
		// the spinny: frames 186-201, 20 a second
		k = floor (el / 0.05);
		if (k <= 15)
			self.weaponframe = 186 + k;
		else
		{
			self.weaponframe = 0;
			self.hm_state = 0;
		}
	}
};

// PutClientInServer
void() Hammer_Spawn =
{
	self.hm_state = 0;
	self.hm_ready = 0;
};
