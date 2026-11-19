#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
WINGED BREEZY-HAIR JOHN - FLYABLE VEHICLE & COMBAT DOGFIGHTER (john_bird.qc)

Model: progs/john_bird_head.md3 (100 frames: fly, soar, hover, swoop, perch, combat_fly, combat_whip)
Props: progs/jb_hairspray_can.md3, progs/jb_match.md3
SFX:   sound/john_bird/flap1..4.wav, jv_fly00..13.wav, jb_*.wav
FX:    effectinfo.txt jb_fx_*
================
*/

void() JB_IdleThink;
void(entity attacker, float take) JB_Pain;
void() JB_Die;
void() JB_BottleTouch;
void(entity targ, float dur) JB_ApplyStickySlow;
void(entity targ, entity attacker, float dur) JB_ApplyBurn;

.entity	jb_blast_pilot;		// JB_Die -> JB_DieBlast: the pilot just thrown out, who takes the blast

void() JohnBird_Precache =
{
	if (jb_precached)
		return;
	jb_precached = TRUE;

	precache_model ("progs/john_bird_head.md3");
	precache_model ("progs/john_bird_feather.md3");
	precache_model ("progs/spike.mdl");
	precache_model ("progs/jb_hairspray_can.md3");
	precache_model ("progs/jb_spraying_can.md3");
	precache_model ("progs/jb_match.md3");

	precache_sound ("john_bird/flap1.wav");
	precache_sound ("john_bird/flap2.wav");
	precache_sound ("john_bird/flap3.wav");
	precache_sound ("john_bird/flap4.wav");
	precache_sound ("john_bird/takeoff.wav");
	precache_sound ("john_bird/swoop.wav");
	precache_sound ("john_bird/feather_hit.wav");
	precache_sound ("john_bird/shootdown.wav");
	precache_sound ("john_bird/jv_hurt.wav");

	precache_sound ("john_bird/jb_spray_loop.wav");
	precache_sound ("john_bird/jb_match_light.wav");
	precache_sound ("john_bird/jb_flame_roar.wav");
	precache_sound ("john_bird/jb_bottle_fire.wav");
	precache_sound ("john_bird/jb_bottle_bonk.wav");
	precache_sound ("john_bird/jb_hair_whip.wav");
	precache_sound ("john_bird/jb_bomb_boom.wav");
	precache_sound ("john_bird/jb_ask_hairspray.wav");

	precache_sound ("john_bird/jv_fly00.wav");
	precache_sound ("john_bird/jv_fly01.wav");
	precache_sound ("john_bird/jv_fly02.wav");
	precache_sound ("john_bird/jv_fly03.wav");
	precache_sound ("john_bird/jv_fly04.wav");
	precache_sound ("john_bird/jv_fly05.wav");
	precache_sound ("john_bird/jv_fly06.wav");
	precache_sound ("john_bird/jv_fly07.wav");
	precache_sound ("john_bird/jv_fly08.wav");
	precache_sound ("john_bird/jv_fly09.wav");
	precache_sound ("john_bird/jv_fly10.wav");
	precache_sound ("john_bird/jv_fly11.wav");
	precache_sound ("john_bird/jv_fly12.wav");
	precache_sound ("john_bird/jv_fly13.wav");

	jb_fx_hairspray = particleeffectnum ("jb_fx_hairspray");
	jb_fx_hairfire = particleeffectnum ("jb_fx_hairfire");
	jb_fx_bottle_trail = particleeffectnum ("jb_fx_bottle_trail");
	jb_fx_sticky_foam = particleeffectnum ("jb_fx_sticky_foam");
	jb_fx_feather_boom = particleeffectnum ("jb_fx_feather_boom");
	jb_fx_mist_burst = particleeffectnum ("jb_fx_mist_burst");
	jb_fx_mist_cloud = particleeffectnum ("jb_fx_mist_cloud");
};

float(entity p) JohnBird_Flying =
{
	return p.jb_vehicle != world;
};

float(float a) JB_NormAngle =
{
	while (a > 180)
		a = a - 360;
	while (a < -180)
		a = a + 360;
	return a;
};

void(entity p) JohnBird_Reset =
{
	p.jb_slow_t = 0;
	p.jb_slow_fx_t = 0;
	p.jb_burn_t = 0;
	p.jb_burn_tick = 0;
	p.jb_burn_by = world;
	p.jb_st_active = 0;
	p.jb_st_combat = 0;
	p.jb_st_status = 0;
	p.jb_st_boost = 0;
	p.jb_st_hp = 0;
	p.jb_st_variant = 1;
	p.jb_st_ammo = 0;
	p.jb_st_ammoprog = 0;
	p.jb_st_speed = 0;
};

string(float idx) JB_VoiceSample =
{
	if (idx <= 0)  return "john_bird/jv_fly00.wav";
	if (idx == 1)  return "john_bird/jv_fly01.wav";
	if (idx == 2)  return "john_bird/jv_fly02.wav";
	if (idx == 3)  return "john_bird/jv_fly03.wav";
	if (idx == 4)  return "john_bird/jv_fly04.wav";
	if (idx == 5)  return "john_bird/jv_fly05.wav";
	if (idx == 6)  return "john_bird/jv_fly06.wav";
	if (idx == 7)  return "john_bird/jv_fly07.wav";
	if (idx == 8)  return "john_bird/jv_fly08.wav";
	if (idx == 9)  return "john_bird/jv_fly09.wav";
	if (idx == 10) return "john_bird/jv_fly10.wav";
	if (idx == 11) return "john_bird/jv_fly11.wav";
	if (idx == 12) return "john_bird/jv_fly12.wav";
	return "john_bird/jv_fly13.wav";
};

void(entity jb, float force_first) JB_PlayRandomVoice =
{
	local float pick, tries;
	local string wav;

	if (force_first)
		pick = 0;
	else
	{
		pick = floor (random () * JB_VOICE_COUNT);
		tries = 0;
		while ((pick == jb.jb_voice_last1 || pick == jb.jb_voice_last2) && tries < 8)
		{
			pick = floor (random () * JB_VOICE_COUNT);
			tries = tries + 1;
		}
	}
	if (pick >= JB_VOICE_COUNT)
		pick = JB_VOICE_COUNT - 1;

	jb.jb_voice_last2 = jb.jb_voice_last1;
	jb.jb_voice_last1 = pick;
	wav = JB_VoiceSample (pick);
	sound (jb, CHAN_VOICE, wav, 1, 0.55);
	jb.jb_voice_t = time + 4.2 + random () * 3.2;
};

void(entity jb, float vol, float pitch_pct) JB_PlayFlap =
{
	local string s;

	jb.jb_flap_idx = jb.jb_flap_idx + 1;
	if (jb.jb_flap_idx > 3)
		jb.jb_flap_idx = 0;

	if (jb.jb_flap_idx == 0)      s = "john_bird/flap1.wav";
	else if (jb.jb_flap_idx == 1) s = "john_bird/flap2.wav";
	else if (jb.jb_flap_idx == 2) s = "john_bird/flap3.wav";
	else                          s = "john_bird/flap4.wav";

	sound7 (jb, CHAN_BODY, s, vol, 0.65, pitch_pct);
};

// ---------------------------------------------------------------- 3D Fluttering Feather Debris

void() JB_FeatherThink =
{
	local float age;

	age = time - self.ltime;
	if (age >= self.wait)
	{
		remove (self);
		return;
	}
	makevectors ('0 1 0' * ((time * 360) + self.cnt));
	self.velocity_x = self.velocity_x * 0.90 + v_forward_x * 18;
	self.velocity_y = self.velocity_y * 0.90 + v_forward_y * 18;
	if (self.velocity_z < -78)
		self.velocity_z = -78;
	if (age > self.wait - 0.8)
		self.alpha = bound (0.05, (self.wait - age) / 0.8, 1);

	self.nextthink = time + 0.08;
};

void(vector org, float count, float boost) JB_SpawnFeathers =
{
	local float i;
	local entity f;

	i = 0;
	while (i < count)
	{
		f = spawn ();
		f.classname = "jb_feather";
		f.movetype = MOVETYPE_TOSS;
		f.solid = SOLID_NOT;
		setmodel (f, "progs/john_bird_feather.md3");
		setsize (f, '0 0 0', '0 0 0');
		setorigin (f, org + '1 0 0' * (crandom () * 24) + '0 1 0' * (crandom () * 28) + '0 0 1' * (crandom () * 16));
		f.velocity_x = crandom () * 220 * boost;
		f.velocity_y = crandom () * 220 * boost;
		f.velocity_z = (95 + random () * 185) * boost;
		f.avelocity_x = crandom () * 320;
		f.avelocity_y = crandom () * 360;
		f.avelocity_z = crandom () * 280;
		f.angles_x = random () * 360;
		f.angles_y = random () * 360;
		f.scale = 0.95 + random () * 0.55;
		f.alpha = 1;
		f.cnt = random () * 360;
		f.ltime = time;
		f.wait = 2.6 + random () * 1.4;
		f.think = JB_FeatherThink;
		f.nextthink = time + 0.08;
		i = i + 1;
	}
};

// ---------------------------------------------------------------- Local-Space & Prop Helpers

vector(entity jb, vector ofs) JB_LocalToWorld =
{
	local vector ang;

	// jb.angles_x uses entity pitch (+ up), whereas makevectors expects v_angle pitch (- up)
	ang_x = 0 - jb.angles_x;
	ang_y = jb.angles_y;
	ang_z = jb.angles_z;
	makevectors (ang);
	return jb.origin + v_forward * ofs_x - v_right * ofs_y + v_up * ofs_z;
};

void() JB_PropWatchdog =
{
	if (self.owner == world || bm_wasfreed (self.owner) || self.owner.classname != "misc_vehicle_johnbird" || self.owner.health <= 0 || self.owner.jb_dying)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.25;
};

void(entity jb) JB_CleanupProps =
{
	if (jb.jb_can_ent != world)
	{
		if (!bm_wasfreed (jb.jb_can_ent) && jb.jb_can_ent.owner == jb)
			remove (jb.jb_can_ent);
		jb.jb_can_ent = world;
	}
	if (jb.jb_match_ent != world)
	{
		if (!bm_wasfreed (jb.jb_match_ent) && jb.jb_match_ent.owner == jb)
			remove (jb.jb_match_ent);
		jb.jb_match_ent = world;
	}
};

entity(entity jb, string mdl) JB_EnsureProp =
{
	local entity e;

	e = spawn ();
	e.classname = "jb_prop";
	e.owner = jb;
	e.movetype = MOVETYPE_NONE;
	e.solid = SOLID_NOT;
	e.alpha = 1;
	e.scale = 1;
	setmodel (e, mdl);
	setsize (e, '0 0 0', '0 0 0');
	setattachment (e, jb, "");
	e.origin = '0 0 0';
	e.angles = '0 0 0';
	e.think = JB_PropWatchdog;
	e.nextthink = time + 0.25;
	return e;
};

void(entity jb, entity pilot, float combat_on, float vmode, float match_lit) JB_UpdateProps =
{
	local vector can_ofs;
	local float cam_1p, sc, idx;

	if (!combat_on)
	{
		if (jb.jb_can_ent != world && !bm_wasfreed (jb.jb_can_ent))
			jb.jb_can_ent.effects = jb.jb_can_ent.effects | EF_NODRAW;
		if (jb.jb_match_ent != world && !bm_wasfreed (jb.jb_match_ent))
			jb.jb_match_ent.effects = jb.jb_match_ent.effects | EF_NODRAW;
		return;
	}

	cam_1p = (pilot != world && pilot.jb_cam_mode == 1);
	if (jb.jb_can_ent == world || bm_wasfreed (jb.jb_can_ent) || jb.jb_can_ent.owner != jb)
		jb.jb_can_ent = JB_EnsureProp (jb, "progs/jb_spraying_can.md3");

	jb.jb_can_ent.effects = jb.jb_can_ent.effects - (jb.jb_can_ent.effects & EF_NODRAW);

	// Big spraying hairspray can held in John's mouth while giant bangs wave wildly!
	if (cam_1p)
	{
		can_ofs = '66 0 40';
		sc = 0.85;
	}
	else
	{
		can_ofs = '22 0 36';
		sc = 1.25;
	}
	jb.jb_can_ent.origin = can_ofs;
	jb.jb_can_ent.scale = sc;
	jb.jb_can_ent.angles = '0 0 0';
	idx = floor (time * 24);
	jb.jb_can_ent.frame = idx - 12 * floor (idx / 12);
};

vector(entity jb, entity pilot, float vmode) JB_GetNozzleWorld =
{
	local vector can_ofs;
	local float cam_1p;

	cam_1p = (pilot != world && pilot.jb_cam_mode == 1);
	if (cam_1p)
		can_ofs = '75.5 0 40';
	else
		can_ofs = '36 0 36';
	return JB_LocalToWorld (jb, can_ofs);
};

vector(entity p, entity jb, vector muz_world) JB_GetAimDir =
{
	local vector cam_org, aim_pt;

	makevectors (p.v_angle);
	if (jb.jb_cam != world && !bm_wasfreed (jb.jb_cam))
		cam_org = jb.jb_cam.origin;
	else
		cam_org = jb.origin + '0 0 44';

	traceline (cam_org, cam_org + v_forward * 4096, FALSE, jb);
	aim_pt = trace_endpos;
	if (vlen (aim_pt - muz_world) < 64)
		aim_pt = cam_org + v_forward * 512;

	return normalize (aim_pt - muz_world);
};

// ---------------------------------------------------------------- Sticky Slow, Burning DoT & Foam Clouds

void() JB_DebuffThink =
{
	local entity targ, atk;
	local float slowed, burning;

	targ = self.owner;
	if (targ == world || bm_wasfreed (targ) || targ.health <= 0)
	{
		remove (self);
		return;
	}

	slowed = (time < targ.jb_slow_t);
	burning = (time < targ.jb_burn_t);
	if (!slowed && !burning)
	{
		remove (self);
		return;
	}

	if (slowed)
	{
		// Dampen ground/air monster movement gently
		targ.velocity_x = targ.velocity_x * 0.55;
		targ.velocity_y = targ.velocity_y * 0.55;
		if (jb_fx_sticky_foam > 0 && time >= targ.jb_slow_fx_t)
		{
			targ.jb_slow_fx_t = time + 0.22;
			pointparticles (jb_fx_sticky_foam, targ.origin + '0 0 24', '0 0 0', 1);
		}
	}

	if (burning)
	{
		if (targ.waterlevel >= 2)
		{
			targ.jb_burn_t = 0;
		}
		else
		{
			if (jb_fx_hairfire > 0)
				pointparticles (jb_fx_hairfire, targ.origin + '0 0 28', '0 0 48', 1);
			if (time >= targ.jb_burn_tick)
			{
				targ.jb_burn_tick = time + 0.40;
				atk = targ.jb_burn_by;
				if (atk != world && (bm_wasfreed (atk) || atk.health <= 0 && atk.classname != "player"))
					atk = world;
				jb_inflicting = 4;
				T_Damage (targ, self, (atk != world) ? atk : self, 6);
				jb_inflicting = 0;
			}
		}
	}

	self.nextthink = time + 0.12;
};

void(entity targ) JB_EnsureMonsterDebuff =
{
	local entity e;

	e = find (world, classname, "jb_debuff");
	while (e != world)
	{
		if (e.owner == targ)
			return;
		e = find (e, classname, "jb_debuff");
	}
	e = spawn ();
	e.classname = "jb_debuff";
	e.owner = targ;
	e.think = JB_DebuffThink;
	e.nextthink = time + 0.12;
};

void(entity targ, float dur) JB_ApplyStickySlow =
{
	if (targ == world || !targ.takedamage || targ.health <= 0)
		return;
	if (targ.jb_vehicle != world)
		targ = targ.jb_vehicle;

	targ.jb_slow_t = max (targ.jb_slow_t, time + dur);
	if (jb_fx_sticky_foam > 0 && time >= targ.jb_slow_fx_t)
	{
		targ.jb_slow_fx_t = time + 0.16;
		pointparticles (jb_fx_sticky_foam, targ.origin + '0 0 24', '0 0 0', 1);
	}
	if ((targ.flags & FL_MONSTER) && targ.classname != "player")
		JB_EnsureMonsterDebuff (targ);
};

void(entity targ, entity attacker, float dur) JB_ApplyBurn =
{
	if (targ == world || !targ.takedamage || targ.health <= 0)
		return;
	if (targ.jb_vehicle != world)
		targ = targ.jb_vehicle;
	if (targ.waterlevel >= 2)
		return;

	targ.jb_burn_t = max (targ.jb_burn_t, time + dur);
	if (attacker != world)
		targ.jb_burn_by = attacker;

	if (targ.classname == "misc_vehicle_johnbird")
	{
		targ.skin = 1;
		if (time >= targ.pain_finished)
		{
			sound (targ, CHAN_VOICE, "john_bird/jv_hurt.wav", 1, 0.55);
			targ.pain_finished = time + 1.1;
			JB_SpawnFeathers (targ.origin + '0 0 34', 3, 0.9);
		}
	}
	else if ((targ.flags & FL_MONSTER) && targ.classname != "player")
	{
		JB_EnsureMonsterDebuff (targ);
	}
};

// TRUE when e is the attacker himself or his own bird (either side of the pilot <-> bird link):
// splash/cloud/fireball loops skip these so a pilot never slows or burns his own bird
float(entity e, entity atk) JB_IsOwnSide =
{
	if (atk == world)
		return FALSE;
	if (e == atk || e.jb_pilot == atk)
		return TRUE;
	if (e.jb_vehicle != world && e.jb_vehicle.jb_pilot == atk)
		return TRUE;
	return FALSE;
};

void(entity jb) JB_UpdateBirdDebuffs =
{
	local entity atk;

	if (jb.health <= 0 || jb.jb_dying)
		return;

	if (time < jb.jb_slow_t && jb_fx_sticky_foam > 0 && time >= jb.jb_slow_fx_t)
	{
		jb.jb_slow_fx_t = time + 0.18;
		pointparticles (jb_fx_sticky_foam, jb.origin + '0 0 32', '0 0 0', 1);
	}

	if (time < jb.jb_burn_t)
	{
		if (jb_fx_hairfire > 0 && time >= jb.jb_smoke_t)
		{
			jb.jb_smoke_t = time + 0.11;
			pointparticles (jb_fx_hairfire, jb.origin + '0 0 34', '0 0 46', 1);
		}
		if (time >= jb.jb_burn_tick)
		{
			jb.jb_burn_tick = time + 0.40;
			atk = jb.jb_burn_by;
			if (atk != world && (bm_wasfreed (atk) || atk == jb.jb_pilot))
				atk = world;
			jb_inflicting = 4;
			T_Damage (jb, jb, (atk != world) ? atk : jb, 6);
			jb_inflicting = 0;
		}
	}
};

void() JohnBird_DebuffFrame =
{
	local vector v;
	local float z, sp, st;
	local entity atk;

	if (self.jb_vehicle != world)
		return;

	if (self.health > 0 && time < self.jb_slow_t)
	{
		v = self.velocity;
		z = v_z;
		v_z = 0;
		sp = vlen (v);
		if (sp > JB_SLOW_SPEED)
			v = normalize (v) * JB_SLOW_SPEED;
		v_z = z;
		self.velocity = v;
		if (jb_fx_sticky_foam > 0 && time >= self.jb_slow_fx_t)
		{
			self.jb_slow_fx_t = time + 0.22;
			pointparticles (jb_fx_sticky_foam, self.origin + '0 0 24', '0 0 0', 1);
		}
	}
	else if (time >= self.jb_slow_t)
	{
		self.jb_slow_t = 0;
	}

	if (self.health > 0 && time < self.jb_burn_t)
	{
		if (self.waterlevel >= 2)
		{
			self.jb_burn_t = 0;
		}
		else
		{
			if (jb_fx_hairfire > 0 && time >= self.jb_smoke_t)
			{
				self.jb_smoke_t = time + 0.14;
				pointparticles (jb_fx_hairfire, self.origin + '0 0 26', '0 0 42', 1);
			}
			if (time >= self.jb_burn_tick)
			{
				self.jb_burn_tick = time + 0.40;
				atk = self.jb_burn_by;
				if (atk != world && (bm_wasfreed (atk) || atk == self))
					atk = world;
				jb_inflicting = 4;
				T_Damage (self, (atk != world) ? atk : self, (atk != world) ? atk : self, 6);
				jb_inflicting = 0;
			}
		}
	}
	else if (time >= self.jb_burn_t)
	{
		self.jb_burn_t = 0;
	}

	if (self.ishuman == 1)
	{
		st = 0;
		if (time < self.jb_slow_t) st = st | 1;
		if (time < self.jb_burn_t) st = st | 2;
		self.jb_st_active = 0;
		self.jb_st_variant = 1;
		self.jb_st_combat = 0;
		self.jb_st_status = st;
		self.jb_st_boost = 0;
		self.jb_st_hp = 0;
		self.jb_st_ammo = 0;
		self.jb_st_ammoprog = 0;
		self.jb_st_speed = 0;
	}
};

// ---------------------------------------------------------------- Foam Cloud & Aerosol Combo Fireball

void(entity bomb_or_cloud, entity attacker) JB_DetonateFoamFireball =
{
	local vector org;
	local entity head, atk;

	if (bomb_or_cloud.jb_dying)
		return;
	bomb_or_cloud.jb_dying = TRUE;

	org = bomb_or_cloud.origin + '0 0 16';
	atk = attacker;
	if (atk == world)
		atk = bomb_or_cloud.jb_summoner;
	if (atk != world && bm_wasfreed (atk))
		atk = world;

	sound (bomb_or_cloud, CHAN_AUTO, "john_bird/jb_bomb_boom.wav", 1, 0.45);
	sound (bomb_or_cloud, CHAN_BODY, "weapons/r_exp3.wav", 1, 0.50);
	JB_SpawnFeathers (org, 18, 1.45);
	if (jb_fx_feather_boom > 0)
		pointparticles (jb_fx_feather_boom, org, '0 0 0', 1);
	if (jb_fx_hairfire > 0)
		pointparticles (jb_fx_hairfire, org, '0 0 90', 3);

	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, org_x);
	WriteCoord (MSG_BROADCAST, org_y);
	WriteCoord (MSG_BROADCAST, org_z);

	jb_inflicting = 7;
	head = findradius (org, 240);
	while (head != world)
	{
		if (head.takedamage && head.health > 0 && head != bomb_or_cloud)
		{
			if (!JB_IsOwnSide (head, atk))
			{
				JB_ApplyBurn (head, atk, 4.0);
				if (atk != world && atk.classname == "player")
					atk.jb_st_hit = atk.jb_st_hit + 1;
			}
		}
		head = head.chain;
	}
	T_RadiusDamage (bomb_or_cloud, (atk != world) ? atk : bomb_or_cloud, 110, world);
	jb_inflicting = 0;

	bomb_or_cloud.solid = SOLID_NOT;
	bomb_or_cloud.model = string_null;
	bomb_or_cloud.think = SUB_Remove;
	bomb_or_cloud.nextthink = time + 0.1;
};

void() JB_FoamCloudThink =
{
	local entity e, atk;
	local float d;

	if (self.jb_dying || time >= self.jb_foam_until)
	{
		remove (self);
		return;
	}

	if (jb_fx_mist_cloud > 0)
		pointparticles (jb_fx_mist_cloud, self.origin + '0 0 18', '0 0 18', 1);
	else if (jb_fx_sticky_foam > 0)
	{
		pointparticles (jb_fx_sticky_foam, self.origin + '0 0 18', '0 0 24', 2);
		pointparticles (jb_fx_sticky_foam, self.origin + '1 0 0' * (crandom () * 64) + '0 1 0' * (crandom () * 64) + '0 0 22', '0 0 16', 1);
	}

	atk = self.jb_summoner;
	if (atk != world && bm_wasfreed (atk))
		atk = world;

	e = findradius (self.origin, 185);
	while (e != world)
	{
		if (e != self && e.takedamage && e.health > 0)
		{
			// Burning player/bird/monster entering the aerosol cloud triggers fireball combo!
			if (time < e.jb_burn_t || e.inflamed == 1)
			{
				JB_DetonateFoamFireball (self, (e.jb_burn_by != world) ? e.jb_burn_by : atk);
				return;
			}
			d = vlen (e.origin - self.origin);
			if (d <= 185 && !JB_IsOwnSide (e, atk))
				JB_ApplyStickySlow (e, 1.5);
		}
		e = e.chain;
	}

	self.nextthink = time + 0.18;
};

entity(vector org, entity atk, float dur) JB_SpawnMistCloud =
{
	local entity e, oldest, cloud;
	local float n;

	// Refresh an overlapping mist cloud rather than stacking duplicates on the exact same spot
	n = 0;
	oldest = world;
	e = find (world, classname, "jb_foam_cloud");
	while (e != world)
	{
		if (!e.jb_dying)
		{
			if (vlen (e.origin - org) < 75)
			{
				e.jb_foam_until = max (e.jb_foam_until, time + dur);
				if (atk != world)
					e.jb_summoner = atk;
				if (jb_fx_mist_cloud > 0)
					pointparticles (jb_fx_mist_cloud, e.origin + '0 0 18', '0 0 24', 2);
				return e;
			}
			n = n + 1;
			if (oldest == world || e.jb_foam_until < oldest.jb_foam_until)
				oldest = e;
		}
		e = find (e, classname, "jb_foam_cloud");
	}
	if (n >= 8 && oldest != world)
		remove (oldest);

	cloud = spawn ();
	cloud.classname = "jb_foam_cloud";
	cloud.jb_summoner = atk;
	cloud.movetype = MOVETYPE_NONE;
	cloud.solid = SOLID_NOT;
	setsize (cloud, '0 0 0', '0 0 0');
	setorigin (cloud, org);
	cloud.jb_foam_until = time + dur;
	cloud.think = JB_FoamCloudThink;
	cloud.nextthink = time + 0.08;
	if (jb_fx_mist_cloud > 0)
		pointparticles (jb_fx_mist_cloud, org + '0 0 18', '0 0 22', 2);
	return cloud;
};

// ---------------------------------------------------------------- Variant Combat Weapons

void(entity jb, entity attacker, vector muz, vector dir, float is_fire, float is_ai) JB_FireSprayCone =
{
	local entity head, best_targ;
	local float max_range, cone_r, dmg, fx_id, dot_p, perp_d, best_d;
	local vector delta, proj_pt;

	max_range = is_fire ? 480 : 520;
	cone_r = is_fire ? 48 : 44;
	dmg = is_fire ? 12 : 6;
	if (is_ai)
		dmg = is_fire ? 6 : 4;

	fx_id = is_fire ? jb_fx_hairfire : jb_fx_hairspray;
	if (fx_id > 0)
		pointparticles (fx_id, muz, dir * (is_fire ? 520 : 450), 1);

	if (time >= jb.jb_spray_snd_t)
	{
		if (is_fire)
		{
			jb.jb_spray_snd_t = time + 0.52;
			sound (jb, CHAN_WEAPON, "john_bird/jb_flame_roar.wav", 0.95, 0.55);
		}
		else
		{
			jb.jb_spray_snd_t = time + 0.45;
			sound (jb, CHAN_WEAPON, "john_bird/jb_spray_loop.wav", 0.90, 0.60);
		}
	}

	if (time < jb.jb_fire_t)
		return;
	jb.jb_fire_t = time + 0.10;

	// Also launch a fast long-range hairspray / fire projectile every 0.28s so clicking fire hits anything at any range!
	if (!is_ai && time >= jb.jb_alt_t)
	{
		jb.jb_alt_t = time + 0.28;
		local entity g;
		g = spawn ();
		g.classname = "jb_spray_glob";
		g.owner = jb;
		g.jb_summoner = attacker;
		g.jb_match_on = is_fire;
		g.cnt = is_fire ? 42 : 28;
		g.movetype = MOVETYPE_FLYMISSILE;
		g.solid = SOLID_BBOX;
		setmodel (g, is_fire ? "progs/jb_match.md3" : "progs/jb_hairspray_can.md3");
		setsize (g, '-4 -4 -4', '4 4 4');
		setorigin (g, muz);
		g.velocity = dir * 1650;
		g.angles = vectoangles (dir);
		g.avelocity = '420 560 320';
		g.scale = is_fire ? 0.85 : 0.72;
		if (is_fire && jb_fx_hairfire > 0)
			g.traileffectnum = jb_fx_hairfire;
		else if (jb_fx_hairspray > 0)
			g.traileffectnum = jb_fx_hairspray;
		g.touch = JB_BottleTouch;
		g.think = SUB_Remove;
		g.nextthink = time + 2.6;
	}

	// Check aerosol bombs & foam clouds in flame cone for fireball combo!
	if (is_fire)
	{
		head = findradius (muz + dir * (max_range * 0.5), max_range * 0.65);
		while (head != world)
		{
			if ((head.classname == "jb_aerosol_bomb" || head.classname == "jb_foam_cloud") && !head.jb_dying)
			{
				delta = head.origin - muz;
				dot_p = delta * dir;
				if (dot_p > 0 && dot_p <= max_range + 80)
				{
					proj_pt = muz + dir * dot_p;
					if (vlen (head.origin - proj_pt) <= cone_r + 65)
					{
						JB_DetonateFoamFireball (head, attacker);
						head = world;
						break;
					}
				}
			}
			head = head.chain;
		}
	}

	best_targ = world;
	best_d = max_range;
	head = findradius (muz + dir * (max_range * 0.5), max_range * 0.60);
	while (head != world)
	{
		if (head != jb && head != attacker && head.takedamage && head.health > 0)
		{
			if (head.jb_pilot == world || head.jb_pilot != attacker)
			{
				delta = (head.absmin + head.absmax) * 0.5 - muz;
				dot_p = delta * dir;
				if (dot_p > 12 && dot_p < max_range)
				{
					proj_pt = muz + dir * dot_p;
					perp_d = vlen (((head.absmin + head.absmax) * 0.5) - proj_pt);
					if (perp_d <= cone_r + (head.maxs_x * 0.5))
					{
						traceline (muz, (head.absmin + head.absmax) * 0.5, TRUE, jb);
						if (trace_fraction >= 0.95)
						{
							jb_inflicting = is_fire ? 4 : 3;
							T_Damage (head, jb, (attacker != world) ? attacker : jb, dmg);
							jb_inflicting = 0;

							if (is_fire)
								JB_ApplyBurn (head, (attacker != world) ? attacker : jb, 4.0);
							else
								JB_ApplyStickySlow (head, is_ai ? 1.8 : 3.5);

							if (attacker != world && attacker.classname == "player")
								attacker.jb_st_hit = attacker.jb_st_hit + 1;

							if (dot_p < best_d)
							{
								best_d = dot_p;
								best_targ = head;
							}
						}
					}
				}
			}
		}
		head = head.chain;
	}
};

void() JB_BottleTouch =
{
	local vector org, push;
	local entity atk, head, cloud, snd_ent, own_bird;
	local float base_dmg, hit_dmg, sp_dmg, slow_dur, d, is_foot_player, is_bird, do_cloud;

	if (other == self.owner || (self.jb_summoner != world && other == self.jb_summoner))
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}

	if (vlen (self.velocity) > 1)
		org = self.origin - normalize (self.velocity) * 14 + '0 0 8';
	else
		org = self.origin + '0 0 8';
	atk = self.jb_summoner;
	if (atk != world && (bm_wasfreed (atk) || atk.classname != "player"))
		atk = world;
	if (atk == world)
		atk = self.owner;
	if (atk != world && bm_wasfreed (atk))
		atk = world;

	base_dmg = (self.cnt > 0) ? self.cnt : 28;
	slow_dur = 1.1;

	// Throttle mist-cloud & audio spam during rapid-fire stream while keeping direct hits crisp
	own_bird = self.owner;
	do_cloud = TRUE;
	if (own_bird != world && !bm_wasfreed (own_bird) && own_bird.classname == "misc_vehicle_johnbird")
	{
		if (time < own_bird.jb_cloud_cd)
			do_cloud = FALSE;
		else
			own_bird.jb_cloud_cd = time + 0.55;
	}

	if (do_cloud)
	{
		cloud = JB_SpawnMistCloud (org, atk, 1.8);
		snd_ent = (cloud != world) ? cloud : self;
		sound (snd_ent, CHAN_BODY, "john_bird/jb_spray_loop.wav", 0.72, 0.72);
		sound (snd_ent, CHAN_AUTO, "john_bird/jb_bottle_bonk.wav", 0.52, 0.70);
	}
	else if (other != world && other.takedamage)
	{
		sound (self, CHAN_AUTO, "john_bird/jb_bottle_bonk.wav", 0.45, 0.80);
	}

	// No feathers on hairspray crash — only bright aerosol mist particles (feathers spawn on bird-vs-bird hit below)
	if (jb_fx_mist_burst > 0)
		pointparticles (jb_fx_mist_burst, org, '0 0 0', 1);
	if (self.jb_match_on && jb_fx_hairfire > 0)
		pointparticles (jb_fx_hairfire, org, '0 0 42', 2);
	else if (do_cloud && jb_fx_sticky_foam > 0)
		pointparticles (jb_fx_sticky_foam, org, '0 0 32', 1);

	jb_inflicting = self.jb_match_on ? 4 : 5;
	if (other != world && other.takedamage && other.health > 0)
	{
		if (other.jb_pilot == world || other.jb_pilot != atk)
		{
			is_foot_player = (other.classname == "player" && other.jb_vehicle == world);
			is_bird = (other.classname == "misc_vehicle_johnbird");
			hit_dmg = is_foot_player ? 5 : base_dmg;
			if (other.movetype == MOVETYPE_WALK || other.movetype == MOVETYPE_STEP || other.movetype == MOVETYPE_TOSS)
			{
				push = normalize (self.velocity);
				push_z = max (0.25, push_z);
				other.flags = other.flags - (other.flags & FL_ONGROUND);
				other.velocity = other.velocity + normalize (push) * (is_foot_player ? 110 : 280) + '0 0 60';
			}
			T_Damage (other, self, (atk != world) ? atk : self, hit_dmg);
			if (is_bird)
				JB_SpawnFeathers (org, 4, 0.9);
			if (self.jb_match_on)
				JB_ApplyBurn (other, (atk != world) ? atk : self, 3.0);
			else
				JB_ApplyStickySlow (other, slow_dur);
			if (atk != world && atk.classname == "player")
				atk.jb_st_hit = atk.jb_st_hit + 1;
		}
	}

	// Anti-bird dogfight splash: tiny chip vs foot players so birds aren't air-to-ground gunships
	head = findradius (org, 110);
	while (head != world)
	{
		if (head != other && head != self.owner && head.takedamage && head.health > 0)
		{
			if (!JB_IsOwnSide (head, atk))
			{
				traceline (org, (head.absmin + head.absmax) * 0.5, TRUE, self);
				if (trace_fraction >= 0.90)
				{
					d = vlen (((head.absmin + head.absmax) * 0.5) - org);
					is_foot_player = (head.classname == "player" && head.jb_vehicle == world);
					sp_dmg = is_foot_player ? 3 : floor (base_dmg * 0.65);
					sp_dmg = floor (sp_dmg * bound (0.25, 1 - d / 110, 1));
					if (sp_dmg > 0)
						T_Damage (head, self, (atk != world) ? atk : self, sp_dmg);
					JB_ApplyStickySlow (head, slow_dur * 0.80);
					if (atk != world && atk.classname == "player")
						atk.jb_st_hit = atk.jb_st_hit + 1;
				}
			}
		}
		head = head.chain;
	}
	jb_inflicting = 0;

	remove (self);
};

void() JB_BottleThink =
{
	local vector fdir;

	if (time >= self.jb_foam_until)
	{
		// Fizzle cleanly out of range
		if (jb_fx_mist_burst > 0)
			pointparticles (jb_fx_mist_burst, self.origin, '0 0 0', 1);
		remove (self);
		return;
	}
	self.frame = self.frame + 1;
	if (self.frame >= 12)
		self.frame = 0;

	// Light gravity arc for responsive air-to-air dogfighting
	self.velocity_z = self.velocity_z - 150 * 0.04;

	if (jb_fx_hairspray > 0 && vlen (self.velocity) > 10)
	{
		fdir = normalize (self.velocity);
		pointparticles (jb_fx_hairspray, self.origin + fdir * 20, fdir * 540, 1);
	}
	if (time >= self.jb_spray_snd_t)
	{
		self.jb_spray_snd_t = time + 0.48;
		sound7 (self, CHAN_BODY, "john_bird/jb_spray_loop.wav", 0.42, 0.95, 106 + crandom () * 6);
	}
	self.nextthink = time + 0.04;
};

void(entity jb, entity attacker, vector muz, vector dir, float spd, float direct_dmg) JB_LaunchBottle =
{
	local entity b;
	local float is_first;

	is_first = FALSE;
	if (!jb.jb_first_shot_said)
	{
		jb.jb_first_shot_said = TRUE;
		is_first = TRUE;
		jb.jb_voice_t = time + 4.2;
		sound (jb, CHAN_VOICE, "john_bird/jb_ask_hairspray.wav", 1, 0.35);
	}

	b = spawn ();
	b.classname = "jb_bottle_proj";
	b.owner = jb;
	b.jb_summoner = attacker;
	b.cnt = direct_dmg;
	b.movetype = MOVETYPE_FLYMISSILE;
	b.solid = SOLID_BBOX;
	setmodel (b, "progs/jb_spraying_can.md3");
	setsize (b, '-6 -6 -6', '6 6 6');
	setorigin (b, muz);
	b.velocity = dir * spd;
	b.angles = vectoangles (dir);
	b.avelocity = '0 0 360';
	b.scale = 1.25;
	b.skin = bound (0, floor (random () * 4), 3);
	b.frame = 0;
	b.jb_foam_until = time + 1.25;
	b.jb_spray_snd_t = time + 0.36;
	if (jb_fx_bottle_trail > 0)
		b.traileffectnum = jb_fx_bottle_trail;
	b.touch = JB_BottleTouch;
	b.think = JB_BottleThink;
	b.nextthink = time + 0.04;

	sound (jb, CHAN_WEAPON, "john_bird/jb_bottle_fire.wav", is_first ? 0.50 : 0.72, 0.65);
};

void() JB_BombExplode =
{
	local vector org;
	local entity atk, cloud, head;

	if (self.jb_dying)
		return;
	self.jb_dying = TRUE;

	org = self.origin + '0 0 10';
	atk = self.jb_summoner;
	if (atk != world && (bm_wasfreed (atk) || atk.classname != "player"))
		atk = world;
	if (atk == world)
		atk = self.owner;
	if (atk != world && bm_wasfreed (atk))
		atk = world;

	// If any burning entity is right here, detonate as huge fireball!
	head = findradius (org, 160);
	while (head != world)
	{
		if (head != self && (time < head.jb_burn_t || head.inflamed == 1))
		{
			self.jb_dying = FALSE;
			JB_DetonateFoamFireball (self, atk);
			return;
		}
		head = head.chain;
	}

	sound (self, CHAN_AUTO, "john_bird/jb_bomb_boom.wav", 1, 0.45);
	JB_SpawnFeathers (org, 16, 1.3);
	if (jb_fx_feather_boom > 0)
		pointparticles (jb_fx_feather_boom, org, '0 0 0', 1);
	if (jb_fx_sticky_foam > 0)
		pointparticles (jb_fx_sticky_foam, org, '0 0 40', 3);

	jb_inflicting = 7;
	head = findradius (org, 185);
	while (head != world)
	{
		if (head != self && head != self.owner && head.takedamage && head.health > 0)
		{
			if (!JB_IsOwnSide (head, atk))
			{
				JB_ApplyStickySlow (head, 3.8);
				if (atk != world && atk.classname == "player")
					atk.jb_st_hit = atk.jb_st_hit + 1;
			}
		}
		head = head.chain;
	}
	T_RadiusDamage (self, (atk != world) ? atk : self, 48, self.owner);
	jb_inflicting = 0;

	// Spawn lingering sticky-slow foam cloud
	cloud = spawn ();
	cloud.classname = "jb_foam_cloud";
	cloud.jb_summoner = atk;
	cloud.movetype = MOVETYPE_NONE;
	cloud.solid = SOLID_NOT;
	setsize (cloud, '0 0 0', '0 0 0');
	setorigin (cloud, org);
	cloud.jb_foam_until = time + 4.5;
	cloud.think = JB_FoamCloudThink;
	cloud.nextthink = time + 0.1;

	remove (self);
};

void() JB_BombTouch =
{
	if (other == self.owner || (self.jb_summoner != world && other == self.jb_summoner))
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	if (other != world && other.takedamage && other.health > 0)
	{
		if (time < other.jb_burn_t || other.inflamed == 1)
		{
			JB_DetonateFoamFireball (self, self.jb_summoner);
			return;
		}
		JB_BombExplode ();
		return;
	}
	sound (self, CHAN_AUTO, "john_bird/jb_bottle_bonk.wav", 0.55, ATTN_NORM);
};

void(entity jb, entity attacker, vector muz, vector dir) JB_LobAerosolBomb =
{
	local entity b;

	b = spawn ();
	b.classname = "jb_aerosol_bomb";
	b.owner = jb;
	b.jb_summoner = attacker;
	b.movetype = MOVETYPE_BOUNCE;
	b.solid = SOLID_BBOX;
	setmodel (b, "progs/jb_hairspray_can.md3");
	setsize (b, '-6 -6 -6', '6 6 6');
	setorigin (b, muz);
	b.velocity = dir * 920 + '0 0 180';
	b.angles = vectoangles (dir);
	b.avelocity = '440 620 280';
	b.scale = 1.45;
	if (jb_fx_bottle_trail > 0)
		b.traileffectnum = jb_fx_bottle_trail;
	b.touch = JB_BombTouch;
	b.think = JB_BombExplode;
	b.nextthink = time + 1.55;

	sound (jb, CHAN_WEAPON, "john_bird/jb_bottle_fire.wav", 1, 0.5);
};

void(entity jb, entity attacker, vector muz, vector dir) JB_PerformHairWhip =
{
	local entity head;
	local vector delta, push;
	local float dist, hit_any;

	jb.jb_whip_until = time + 0.50;
	jb.jb_fire_t = time + 0.55;
	sound (jb, CHAN_WEAPON, "john_bird/jb_hair_whip.wav", 1, 0.50);
	JB_SpawnFeathers (muz + dir * 24, 12, 1.25);

	hit_any = FALSE;
	head = findradius (muz + dir * 95, 165);
	while (head != world)
	{
		if (head.classname == "jb_aerosol_bomb" && !head.jb_dying)
		{
			// Pompadour-whip bats the aerosol bomb forward at high speed!
			head.velocity = dir * 1380 + '0 0 120';
			head.nextthink = time + 1.2;
			sound (head, CHAN_AUTO, "john_bird/jb_bottle_bonk.wav", 1, ATTN_NORM);
		}
		else if (head != jb && head != attacker && head.takedamage && head.health > 0)
		{
			if (head.jb_pilot == world || head.jb_pilot != attacker)
			{
				delta = ((head.absmin + head.absmax) * 0.5) - muz;
				dist = vlen (delta);
				if (dist <= 230 && (dist < 64 || (normalize (delta) * dir) > 0.28))
				{
					push = dir * 620 + '0 0 260';
					if (head.movetype == MOVETYPE_WALK || head.movetype == MOVETYPE_STEP || head.movetype == MOVETYPE_TOSS)
					{
						head.flags = head.flags - (head.flags & FL_ONGROUND);
						head.velocity = head.velocity + push;
					}
					else if (head.classname == "misc_vehicle_johnbird")
					{
						head.velocity = head.velocity + push * 0.85;
					}
					jb_inflicting = 6;
					T_Damage (head, jb, (attacker != world) ? attacker : jb, 65);
					jb_inflicting = 0;
					JB_SpawnFeathers ((head.absmin + head.absmax) * 0.5, 10, 1.2);
					if (attacker != world && attacker.classname == "player")
						attacker.jb_st_hit = attacker.jb_st_hit + 1;
					hit_any = TRUE;
				}
			}
		}
		head = head.chain;
	}
	if (hit_any)
		sound (jb, CHAN_AUTO, "john_bird/feather_hit.wav", 1, 0.55);

	// Also shoot a fast straight aerosol shockwave canister along aim dir so clicking Fire hits distant targets too!
	if (attacker != world && attacker.classname == "player")
	{
		local entity wb;
		wb = spawn ();
		wb.classname = "jb_whip_proj";
		wb.owner = jb;
		wb.jb_summoner = attacker;
		wb.cnt = 45;
		wb.movetype = MOVETYPE_FLYMISSILE;
		wb.solid = SOLID_BBOX;
		setmodel (wb, "progs/jb_hairspray_can.md3");
		setsize (wb, '-4 -4 -4', '4 4 4');
		setorigin (wb, muz);
		wb.velocity = dir * 1380;
		wb.angles = vectoangles (dir);
		wb.avelocity = '640 780 420';
		wb.scale = 1.10;
		if (jb_fx_bottle_trail > 0)
			wb.traileffectnum = jb_fx_bottle_trail;
		wb.touch = JB_BottleTouch;
		wb.think = SUB_Remove;
		wb.nextthink = time + 2.8;
	}
};

// ---------------------------------------------------------------- Pilot Camera & Mount / Dismount

void(entity p, entity jb) JB_UpdateCamera =
{
	local entity cam;
	local vector pivot, pos;

	cam = jb.jb_cam;
	if (cam == world)
		return;

	makevectors (p.v_angle);
	pivot = jb.origin + '0 0 54';
	if (p.jb_cam_mode == 1)
	{
		// First-person breezy-crown view (ahead of John's giant combat bangs so shooting never blocks sight)
		pos = jb.origin + '0 0 54' + v_forward * 52;
		traceline (pivot, pos, TRUE, jb);
		pos = trace_endpos;
		if (trace_fraction < 1)
			pos = pos + trace_plane_normal * 6;
	}
	else
	{
		// Centered close 3rd-person chase cam with subtle boost pullback for speed feel
		pos = pivot - v_forward * (104 + jb.jb_cam_pull) + v_up * (26 + jb.jb_cam_pull * 0.16);
		traceline (pivot, pos, TRUE, jb);
		pos = trace_endpos;
		if (trace_fraction < 1)
			pos = pos + trace_plane_normal * 8;
	}
	setorigin (cam, pos);
	cam.angles = p.v_angle;
};

void(entity p, vector pos, vector vel, float yaw) JB_ReleasePlayer =
{
	p.jb_vehicle = world;
	if (p.ishuman == 1)
	{
		p.clientcamera = p;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, p);
		p.jb_st_active = 0;
		p.jb_st_combat = 0;
		p.jb_st_hp = 0;
		p.jb_st_boost = 0;
		p.jb_st_ammo = 0;
		p.jb_st_ammoprog = 0;
		p.jb_st_speed = 0;
	}
	p.alpha = 0;					// 0 = default opaque in DarkPlaces
	p.effects = p.effects - (p.effects & EF_NODRAW);
	if (p.health > 0 && p.classname == "player")	// an observer keeps his own noclip movetype / SOLID_NOT
	{
		p.movetype = p.jb_oldmove;
		if (p.movetype == MOVETYPE_NONE || p.movetype == 0)
			p.movetype = MOVETYPE_WALK;
		p.solid = p.jb_oldsolid;
		if (p.solid == SOLID_NOT || p.solid == 0)
			p.solid = SOLID_SLIDEBOX;
	}
	setorigin (p, pos);
	p.velocity = vel;
	p.flags = p.flags - (p.flags & FL_ONGROUND);
	p.angles = '0 0 0';
	p.angles_y = yaw;
	p.fixangle = TRUE;
};

void(entity jb) JB_Park =
{
	jb.jb_pilot = world;
	jb.jb_ai = FALSE;
	jb.jb_carve_spd = 0;
	jb.jb_match_on = FALSE;
	jb.jb_whip_until = 0;
	JB_CleanupProps (jb);
	jb.velocity = '0 0 0';
	jb.angles_x = 0;
	jb.angles_z = 0;
	jb.movetype = MOVETYPE_TOSS;
	jb.solid = SOLID_BBOX;
	jb.takedamage = DAMAGE_AIM;
	setsize (jb, '-30 -38 -6', '30 38 56');
	setorigin (jb, jb.origin);
	jb.frame = 60;
	jb.think = JB_IdleThink;
	jb.nextthink = time + 0.08;
};

void(entity jb, vector exit_pos, vector exit_vel, float exploding) JB_Leave =
{
	local entity p;
	local float yaw;

	p = jb.jb_pilot;
	jb.jb_pilot = world;
	jb.jb_carve_spd = 0;
	jb.jb_match_on = FALSE;
	jb.jb_whip_until = 0;
	JB_CleanupProps (jb);
	if (jb.jb_cam != world)
	{
		remove (jb.jb_cam);
		jb.jb_cam = world;
	}
	// release on the vehicle link, not the classname: an `observe` or disconnect can rename him first,
	// and then jb_vehicle would point at a freed bird with the John HUD stats left on
	if (p != world && (p.classname == "player" || p.jb_vehicle == jb))
	{
		if (!exploding && jb.jb_temp && jb.jb_summoner == p)
		{
			if (p.ud_boost >= 0.5)
				p.jb_cooldown_t = max (p.jb_cooldown_t, time + 4.0);
			else
				p.jb_cooldown_t = max (p.jb_cooldown_t, time + 6.0);
		}
		yaw = p.v_angle_y;
		JB_ReleasePlayer (p, exit_pos, exit_vel, yaw);
	}
	if (!exploding)
	{
		if (jb.jb_temp && jb.jb_summoner != world)
		{
			jb.jb_pilot = world;
			jb.solid = SOLID_NOT;
			jb.takedamage = DAMAGE_NO;
			jb.movetype = MOVETYPE_NONE;
			setmodel (jb, "");	// model = string_null alone keeps the modelindex: the frozen bird stayed drawn
			jb.jb_dying = TRUE;
			jb.health = 0;
			jb.think = SUB_Remove;
			jb.nextthink = time + 0.2;
		}
		else
			JB_Park (jb);
	}
};

float(entity p, vector pos) JB_SpotClear =
{
	tracebox (pos, VEC_HULL_MIN, VEC_HULL_MAX, pos, FALSE, p);
	if (trace_startsolid || trace_allsolid)
		return FALSE;
	return TRUE;
};

vector(entity jb, entity p) JB_FindExitPos =
{
	local vector cand;

	makevectors ('0 1 0' * jb.angles_y);
	cand = jb.origin + '0 0 28';
	if (JB_SpotClear (p, cand))
		return cand;
	cand = jb.origin - v_forward * 54 + '0 0 26';
	if (JB_SpotClear (p, cand))
		return cand;
	cand = jb.origin + v_right * 56 + '0 0 26';
	if (JB_SpotClear (p, cand))
		return cand;
	cand = jb.origin - v_right * 56 + '0 0 26';
	if (JB_SpotClear (p, cand))
		return cand;
	cand = jb.origin + v_forward * 60 + '0 0 26';
	if (JB_SpotClear (p, cand))
		return cand;
	cand = jb.origin + '0 0 84';
	if (JB_SpotClear (p, cand))
		return cand;
	return jb.origin + '0 0 24';
};

void(entity p, entity jb) JB_Enter =
{
	local entity cam, oldself;

	if (p.health <= 0 || p.jb_vehicle != world || p.veh_van != world || p.veh_ride != world || p.fd_head != world)
		return;
	if (p.jp_on)
	{
		oldself = self;
		self = p;
		Jetpack_Off ();
		self = oldself;
	}
	if (p.wc_charging)
	{
		p.wc_charging = 0;
		sound (p, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
	}
	if (p.bn_on)
	{
		p.bn_on = FALSE;
		p.viewzoom = 0;
		centerprint (p, "");
	}
	p.ltg_phase = 0;
	p.milky_wind = 0;
	p.pk_throw_at = 0;
	p.ns_throw_at = 0;
	p.jb_variant = 1;

	jb.jb_pilot = p;
	jb.jb_ai = FALSE;
	jb.jb_carve_spd = 0;
	jb.jb_cam_pull = 0;
	jb.jb_match_on = FALSE;
	jb.jb_dry_snd_t = 0;
	jb.jb_whip_until = 0;
	jb.think = JB_IdleThink;
	jb.nextthink = time + 0.1;
	p.jb_vehicle = jb;
	p.jb_oldmove = p.movetype;
	p.jb_oldsolid = p.solid;
	p.jb_prev_yaw = p.v_angle_y;
	p.jb_prev_pitch = p.v_angle_x;

	jb.movetype = MOVETYPE_NONE;
	jb.solid = SOLID_BBOX;
	jb.takedamage = DAMAGE_AIM;
	setsize (jb, '-28 -36 -4', '28 36 58');
	setorigin (jb, jb.origin + '0 0 14');
	jb.velocity = '0 0 160';
	jb.angles_x = 0;
	jb.angles_y = p.v_angle_y;
	jb.angles_z = 0;
	jb.jb_flap_t = time + 0.12;
	jb.jb_voice_t = time + 0.24;
	jb.jb_swoop_until = 0;

	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.velocity = '0 0 0';
	p.alpha = 0.01;
	p.effects = p.effects | EF_NODRAW;
	setorigin (p, jb.origin + '0 0 20');

	cam = spawn ();
	cam.classname = "jb_cam";
	cam.movetype = MOVETYPE_NONE;
	cam.solid = SOLID_NOT;
	cam.alpha = 0.01;
	cam.scale = 0.01;
	setmodel (cam, "progs/spike.mdl");
	setsize (cam, '0 0 0', '0 0 0');
	setorigin (cam, jb.origin + '0 0 48');
	jb.jb_cam = cam;

	if (p.ishuman == 1)
	{
		p.clientcamera = cam;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, cam);
	}
	JB_UpdateCamera (p, jb);

	sound (jb, CHAN_ITEM, "john_bird/takeoff.wav", 1, 0.6);
	JB_SpawnFeathers (jb.origin + '0 0 28', 4, 0.7);
	p.jb_hint_shown = TRUE;
};

// ---------------------------------------------------------------- Collision & Dive-Ram

void(entity jb, entity pilot, entity hit) JB_CheckSwoopRam =
{
	local vector push;

	if (hit == world || hit == pilot || hit == jb)
		return;
	if (!hit.takedamage || hit.health <= 0)
		return;
	if (time < jb.jb_ram_cd)
		return;
	if (vlen (jb.velocity) < 720)
		return;
	if (time >= jb.jb_swoop_until && jb.velocity_z > -420)
		return;

	jb.jb_ram_cd = time + 1.15;
	jb.jb_ammo = min (JB_MAX_AMMO, jb.jb_ammo + 3);
	sound (jb, CHAN_AUTO, "john_bird/feather_hit.wav", 1, ATTN_NORM);
	sound (jb, CHAN_VOICE, "john_bird/swoop.wav", 0.75, 0.75);
	JB_SpawnFeathers (jb.origin + '0 0 32', 8, 1.25);

	push = normalize (jb.velocity);
	push_z = 0.42;
	push = normalize (push);
	if (hit.movetype == MOVETYPE_WALK || hit.movetype == MOVETYPE_STEP || hit.movetype == MOVETYPE_TOSS)
	{
		hit.flags = hit.flags - (hit.flags & FL_ONGROUND);
		hit.velocity = hit.velocity + push * 360 + '0 0 180';
	}
	jb_inflicting = 2;
	if (pilot != world)
	{
		T_Damage (hit, jb, pilot, (hit.classname == "player" && hit.jb_vehicle == world) ? 35 : 65);
		if (pilot.classname == "player")
			pilot.jb_st_hit = pilot.jb_st_hit + 1;
	}
	else
		T_Damage (hit, jb, jb, 45);
	jb_inflicting = 0;
};

void(entity jb, entity pilot, float dt) JB_SlideMove =
{
	local vector start, dest, rem, n1;
	local float vn;

	if (vlen (jb.velocity) < 0.5)
		return;

	start = jb.origin;
	dest = start + jb.velocity * dt;
	if (pointcontents (dest + '0 0 52') == CONTENT_SKY)
	{
		dest_z = min (dest_z, start_z);
		if (jb.velocity_z > 0)
			jb.velocity_z = 0;
	}
	tracebox (start, jb.mins, jb.maxs, dest, FALSE, jb);
	if (trace_allsolid || trace_startsolid)
	{
		tracebox (start + '0 0 8', jb.mins, jb.maxs, start + '0 0 8', TRUE, jb);
		if (!trace_startsolid)
			setorigin (jb, start + '0 0 8');
		return;
	}
	setorigin (jb, trace_endpos);
	if (trace_fraction >= 1)
		return;

	if (trace_ent != world)
		JB_CheckSwoopRam (jb, pilot, trace_ent);

	n1 = trace_plane_normal;
	vn = jb.velocity * n1;
	if (vn < 0)
		jb.velocity = jb.velocity - n1 * vn;

	rem = jb.velocity * (dt * (1 - trace_fraction));
	if (vlen (rem) > 0.25)
	{
		tracebox (jb.origin, jb.mins, jb.maxs, jb.origin + rem, FALSE, jb);
		if (!trace_allsolid && !trace_startsolid)
		{
			setorigin (jb, trace_endpos);
			if (trace_fraction < 1)
			{
				vn = jb.velocity * trace_plane_normal;
				if (vn < 0)
					jb.velocity = jb.velocity - trace_plane_normal * vn;
			}
		}
	}
};

// ---------------------------------------------------------------- Animation & Audio Driver

void(entity jb, float dt, float thr_in, float climb_in, float swooping, float combat_on) JB_UpdateAnimAndAudio =
{
	local float hspd, clip_start, clip_len, fps, flap_gap, flap_vol, flap_pitch, idx;

	hspd = vlen (jb.velocity);
	if (time < jb.jb_whip_until)
	{
		// Clip 7: Mega-Bangs Pompadour Whip (frames 88..99)
		idx = floor ((1 - (jb.jb_whip_until - time) / 0.50) * 12);
		idx = bound (0, idx, 11);
		jb.frame = 88 + idx;
		flap_gap = 0.24;
		flap_vol = 0.85;
		flap_pitch = 112;
	}
	else
	{
		if (combat_on)
		{
			// Clip 6: Giant Waving Bangs Combat Flight (frames 72..87)
			clip_start = 72;
			clip_len = 16;
			fps = 18;
			flap_gap = 0.24;
			flap_vol = 0.85;
			flap_pitch = 108;
		}
		else if (swooping || jb.velocity_z < -420)
		{
			// Clip 4: Peregrine Swoop / Dive (frames 48..59)
			clip_start = 48;
			clip_len = 12;
			fps = 16;
			flap_gap = 0.52;
			flap_vol = 0.55;
			flap_pitch = 114;
		}
		else if (climb_in > 0.2 || hspd < 230)
		{
			// Clip 3: Rapid Hover Flutter / Vigorous Climb (frames 32..47)
			clip_start = 32;
			clip_len = 16;
			fps = 19;
			flap_gap = 0.22;
			flap_vol = 0.90;
			flap_pitch = 108;
		}
		else if (thr_in <= 0.05 && climb_in <= 0 && hspd > 340)
		{
			// Clip 2: Windy Thermal Soar / Outstretched Glide (frames 16..31)
			clip_start = 16;
			clip_len = 16;
			fps = 11;
			flap_gap = 1.05;
			flap_vol = 0.38;
			flap_pitch = 92;
		}
		else
		{
			// Clip 1: Fast Cruising Wingbeat & Breezy Hair (frames 0..15)
			clip_start = 0;
			clip_len = 16;
			fps = 14 + bound (0, hspd / 130, 8);
			flap_gap = bound (0.23, 0.36 - hspd * 0.00010, 0.35);
			flap_vol = 0.85;
			flap_pitch = 96 + bound (0, hspd * 0.012, 14);
		}

		jb.jb_anim_clock = jb.jb_anim_clock + dt * fps;
		idx = floor (jb.jb_anim_clock);
		idx = idx - clip_len * floor (idx / clip_len);
		jb.frame = clip_start + idx;
	}

	if (time >= jb.jb_flap_t)
	{
		JB_PlayFlap (jb, flap_vol, flap_pitch + crandom () * 4);
		jb.jb_flap_t = time + flap_gap;
	}

	if (time >= jb.jb_voice_t)
		JB_PlayRandomVoice (jb, (jb.jb_voice_last1 < 0));

	if (jb.health <= JB_LOW_HP && veh_fx_smoke > 0 && time >= jb.jb_smoke_t)
	{
		jb.jb_smoke_t = time + 0.09;
		pointparticles (veh_fx_smoke, jb.origin + '0 0 34', '0 0 24', 1);
	}
};

// ---------------------------------------------------------------- Per-Frame Player Flight Loop

float() JohnBird_Frame =
{
	local entity jb, head, best_ram;
	local float dt, fwd_in, str_in, up_in, swooping, max_spd, yaw_rate, target_roll, k, shot_spd, best_d, d;
	local float yaw_delta, pitch_delta, ang_rate, carve_bonus, prev_carve;
	local float slow_mult, combat_on, c_flags, s_flags;
	local vector wish, dir_ang, muz, aim_dir;

	jb = self.jb_vehicle;
	if (jb == world)
		return FALSE;
	if (bm_wasfreed (jb) || jb.jb_pilot != self || jb.health <= 0 || self.health <= 0)
	{
		JB_ReleasePlayer (self, self.origin, '0 0 0', self.v_angle_y);
		return FALSE;
	}

	dt = frametime;
	if (dt < 0.001)
		dt = 0.001;
	if (dt > 0.05)
		dt = 0.05;

	// Handle dismount (H = 86, P = 98), camera toggle (K = 87), V (20), cheats (97, 99)
	if (self.impulse == 86 || self.impulse == 98)
	{
		self.impulse = 0;
		JB_Leave (jb, JB_FindExitPos (jb, self), jb.velocity * 0.35, FALSE);
		return TRUE;
	}
	else if (self.impulse == 87)
	{
		self.jb_cam_mode = 1 - self.jb_cam_mode;
		if (self.jb_cam_mode == 1)
			sprint (self, "Winged John camera: First-Person Breezy-Crown View\n");
		else
			sprint (self, "Winged John camera: Third-Person Avian Chase View\n");
		self.impulse = 0;
	}
	else if (self.impulse == 20 && time >= jb.jb_voice_t - 6.0)
	{
		JB_PlayRandomVoice (jb, FALSE);
		self.impulse = 0;
	}
	else if ((self.impulse == 97 || self.impulse == 99) && autocvar_sv_cheats)
	{
		JohnBird_Impulse ();
	}
	self.impulse = 0;

	self.flags = self.flags - (self.flags & FL_ONGROUND);
	self.velocity = '0 0 0';

	// Read 3D flight inputs
	makevectors (self.v_angle);
	fwd_in = bound (-1, self.movement_x / 200, 1);
	str_in = bound (-1, self.movement_y / 200, 1);
	up_in = 0;
	if (self.button2 || self.movement_z > 40)
		up_in = 1;
	else if (self.movement_z < -40)
		up_in = -1;

	// Mouse carve / flap speed: moving mouse L/R/U/D pumps up airspeed smoothly
	yaw_delta = JB_NormAngle (self.v_angle_y - self.jb_prev_yaw);
	pitch_delta = JB_NormAngle (self.v_angle_x - self.jb_prev_pitch);
	self.jb_prev_yaw = self.v_angle_y;
	self.jb_prev_pitch = self.v_angle_x;
	yaw_rate = yaw_delta / dt;
	ang_rate = (fabs (yaw_delta) + fabs (pitch_delta)) / dt;

	prev_carve = jb.jb_carve_spd;
	if (ang_rate > 25 && fwd_in >= -0.2)
		jb.jb_carve_spd = min (100, jb.jb_carve_spd + bound (0, (ang_rate - 25) * 0.48, 160) * dt);
	jb.jb_carve_spd = max (0, jb.jb_carve_spd - dt * 26);

	if (prev_carve < 65 && jb.jb_carve_spd >= 65 && time >= jb.jb_carve_snd_t)
	{
		jb.jb_carve_snd_t = time + 1.1;
		sound (jb, CHAN_ITEM, "john_bird/swoop.wav", 0.70, 0.75);
	}

	carve_bonus = (jb.jb_carve_spd / 100) * JB_SPEED_CARVE_MAX;
	swooping = (jb.jb_carve_spd >= 60 || vlen (jb.velocity) >= 1020);
	if (swooping)
		jb.jb_swoop_until = time + 0.15;

	slow_mult = (time < jb.jb_slow_t) ? JB_BIRD_SLOW_MULT : 1.0;

	wish = '0 0 0';
	if (fwd_in > 0)
		wish = wish + v_forward * (fwd_in * (JB_SPEED_CRUISE + carve_bonus) * slow_mult);
	else if (fwd_in < 0)
		wish = wish + v_forward * (fwd_in * 300 * slow_mult);
	else if (jb.jb_carve_spd > 15)
		wish = wish + v_forward * (carve_bonus * 0.65 * slow_mult);

	wish = wish + v_right * (str_in * JB_SPEED_STRAFE * slow_mult);
	if (up_in > 0)
		wish_z = wish_z + JB_SPEED_CLIMB * slow_mult;
	else if (up_in < 0)
		wish_z = wish_z - 460 * slow_mult;
	max_spd = (JB_SPEED_CRUISE + 140 + carve_bonus) * slow_mult;

	if (fwd_in < -0.2)
	{
		k = bound (0, dt * 8.0, 1);
		jb.velocity = jb.velocity + (wish - jb.velocity) * k;
	}
	else if (vlen (wish) > 10)
	{
		k = bound (0, dt * (swooping ? 8.2 : 6.2), 1);
		jb.velocity = jb.velocity + (wish - jb.velocity) * k;
	}
	else
	{
		jb.velocity_x = jb.velocity_x * bound (0, 1 - dt * 2.1, 1);
		jb.velocity_y = jb.velocity_y * bound (0, 1 - dt * 2.1, 1);
		jb.velocity_z = jb.velocity_z * bound (0, 1 - dt * 2.8, 1) - 38 * dt;
	}

	if (vlen (jb.velocity) > max_spd)
		jb.velocity = normalize (jb.velocity) * max_spd;

	JB_SlideMove (jb, self, dt);

	// Forgiving swoop dive-ram hitbox when carving fast or diving
	if (time >= jb.jb_ram_cd && vlen (jb.velocity) >= 720 && (time < jb.jb_swoop_until || jb.velocity_z < -420))
	{
		best_ram = world;
		best_d = 78;
		head = findradius (jb.origin + '0 0 26', 78);
		while (head != world)
		{
			if (head != jb && head != self && head.takedamage && head.health > 0)
			{
				if (head.jb_pilot != self)
				{
					d = vlen (((head.absmin + head.absmax) * 0.5) - (jb.origin + '0 0 26'));
					if (d < best_d)
					{
						best_d = d;
						best_ram = head;
					}
				}
			}
			head = head.chain;
		}
		if (best_ram != world)
			JB_CheckSwoopRam (jb, self, best_ram);
	}

	if (fabs (yaw_rate) < 15 && fabs (str_in) < 0.05)
		target_roll = 0;
	else
		target_roll = bound (-20, (0 - yaw_rate * 0.08) + str_in * 14, 20);

	if (vlen (jb.velocity) > 140)
	{
		dir_ang = vectoangles (jb.velocity);
		jb.angles_x = bound (-28, JB_NormAngle (dir_ang_x), 28);
	}
	else
	{
		jb.angles_x = bound (-26, 0 - self.v_angle_x * 0.45, 26);
	}
	jb.angles_y = self.v_angle_y;
	jb.angles_z = jb.angles_z + (target_roll - jb.angles_z) * bound (0, dt * 11.0, 1);

	jb.jb_cam_pull = jb.jb_cam_pull + ((jb.jb_carve_spd / 100 * 16) - jb.jb_cam_pull) * bound (0, dt * 6.0, 1);
	setorigin (self, jb.origin + '0 0 20');
	JB_UpdateCamera (self, jb);

	// Finite hairspray can rack: passive slow restock when below JB_MAX_AMMO
	local float ammo_prog;
	ammo_prog = 0;
	if (jb.jb_ammo < JB_MAX_AMMO)
	{
		if (jb.jb_ammo_regen_t <= 0)
			jb.jb_ammo_regen_t = time + JB_AMMO_RECHARGE_TIME;
		if (time >= jb.jb_ammo_regen_t)
		{
			jb.jb_ammo = min (JB_MAX_AMMO, jb.jb_ammo + 1);
			sound7 (jb, CHAN_ITEM, "weapons/pkup.wav", 0.45, 0.8, 125);
			if (jb.jb_ammo < JB_MAX_AMMO)
				jb.jb_ammo_regen_t = time + JB_AMMO_RECHARGE_TIME;
			else
				jb.jb_ammo_regen_t = 0;
		}
		if (jb.jb_ammo < JB_MAX_AMMO && jb.jb_ammo_regen_t > time)
			ammo_prog = bound (0, floor ((1 - (jb.jb_ammo_regen_t - time) / JB_AMMO_RECHARGE_TIME) * 100), 99);
	}
	else
	{
		jb.jb_ammo_regen_t = 0;
	}

	// Finite Combat: CLICK (button0) shoots hairspray can when ammo > 0; dry-clicks when empty
	combat_on = (self.button0 && jb.jb_ammo > 0);
	JB_UpdateProps (jb, self, combat_on, 1, FALSE);

	if (self.button0)
	{
		if (jb.jb_ammo > 0)
		{
			muz = JB_GetNozzleWorld (jb, self, 1);
			aim_dir = JB_GetAimDir (self, jb, muz);
			if (time >= jb.jb_fire_t)
			{
				jb.jb_fire_t = time + 0.22;
				jb.jb_ammo = max (0, jb.jb_ammo - 1);
				jb.jb_ammo_regen_t = time + JB_AMMO_RECHARGE_DELAY + JB_AMMO_RECHARGE_TIME;
				shot_spd = max (1550, (jb.velocity * aim_dir) + 950);
				JB_LaunchBottle (jb, self, muz, aim_dir, shot_spd, 28);
			}
		}
		else if (time >= jb.jb_dry_snd_t)
		{
			jb.jb_dry_snd_t = time + 0.50;
			sound (jb, CHAN_WEAPON, "weapons/lock4.wav", 0.75, 0.7);
		}
	}

	JB_UpdateBirdDebuffs (jb);
	JB_UpdateAnimAndAudio (jb, dt, (fwd_in > 0 ? fwd_in : 0), up_in, swooping, combat_on);

	// Sync CSQC HUD stats (93..102)
	if (self.ishuman == 1)
	{
		c_flags = 0;
		if (combat_on) c_flags = c_flags | 3;
		if (vlen (jb.velocity) >= 980) c_flags = c_flags | 16;

		s_flags = 0;
		if (time < jb.jb_slow_t) s_flags = s_flags | 1;
		if (time < jb.jb_burn_t) s_flags = s_flags | 2;
		if (jb.health <= JB_LOW_HP) s_flags = s_flags | 4;

		self.jb_st_active = (self.jb_cam_mode == 1) ? 2 : 1;
		self.jb_st_variant = 1;
		self.jb_st_combat = c_flags;
		self.jb_st_status = s_flags;
		self.jb_st_boost = 0;
		self.jb_st_hp = max (0, ceil (jb.health));
		self.jb_st_ammo = bound (0, jb.jb_ammo, JB_MAX_AMMO);
		self.jb_st_ammoprog = ammo_prog;
		self.jb_st_speed = floor (vlen (jb.velocity));
	}

	return TRUE;
};

// ---------------------------------------------------------------- Perched Idle, AI Dogfighter & Respawn

void() JB_Respawn =
{
	tracebox (self.jb_spawn_org, '-30 -38 -6', '30 38 56', self.jb_spawn_org, FALSE, self);
	if (trace_ent != world)
	{
		self.nextthink = time + 1.0;
		return;
	}
	self.jb_dying = FALSE;
	self.jb_slow_t = 0;
	self.jb_burn_t = 0;
	self.jb_burn_by = world;
	self.enemy = world;
	self.health = JB_MAX_HP;
	self.max_health = JB_MAX_HP;
	self.jb_ammo = JB_MAX_AMMO;
	self.jb_ammo_regen_t = 0;
	self.jb_dry_snd_t = 0;
	self.skin = 0;
	self.alpha = 1;
	self.effects = self.effects - (self.effects & EF_NODRAW);
	setmodel (self, "progs/john_bird_head.md3");
	setorigin (self, self.jb_spawn_org);
	self.angles = '0 0 0';
	self.angles_y = self.jb_spawn_yaw;
	JB_Park (self);
	sound (self, CHAN_ITEM, "items/itembk2.wav", 1, ATTN_NORM);
};

entity(entity jb) JB_AIPickTarget =
{
	local entity e, best, cand;
	local float bd, d;

	best = world;
	bd = 2400;
	e = find (world, classname, "player");
	while (e != world)
	{
		if (e.health > 0 && !e.bm_obs && !(e.flags & FL_NOTARGET))
		{
			cand = (e.jb_vehicle != world) ? e.jb_vehicle : e;
			d = vlen (cand.origin - jb.origin);
			if (cand.jb_vehicle == world && e.jb_vehicle != world)
				d = d * 0.75;		// prioritize dogfighting flying Winged Johns!
			if (d < bd)
			{
				bd = d;
				best = cand;
			}
		}
		e = find (e, classname, "player");
	}
	return best;
};

void() JB_AutopilotThink =
{
	local float dt, ang, rad, spd, slow_mult, combat_on, dist, sn;
	local vector center, target_pos, delta, dir_ang, aim_dir, muz;
	local entity targ;

	if (self.health <= 0 || self.jb_dying)
		return;
	if (!self.jb_ai || self.jb_pilot != world)
	{
		self.think = JB_IdleThink;
		self.nextthink = time + 0.08;
		return;
	}

	dt = 0.05;
	if (time >= self.jb_ai_scan_t)
	{
		self.jb_ai_scan_t = time + 0.45;
		self.enemy = JB_AIPickTarget (self);
	}

	targ = self.enemy;
	if (targ != world && (bm_wasfreed (targ) || targ.health <= 0 || targ.jb_dying))
	{
		targ = world;
		self.enemy = world;
	}

	if (time >= self.jb_ai_mode_t)
	{
		self.jb_ai_mode_t = time + 3.2 + random () * 2.0;
		self.jb_ai_mode = 1 - self.jb_ai_mode;
		self.jb_ai_strafe = (random () < 0.5) ? 1 : -1;
		if (self.jb_ai_strafe == 0)
			self.jb_ai_strafe = 1;
	}

	self.jb_ai_phase = self.jb_ai_phase + dt * 92 * ((self.jb_ai_strafe != 0) ? self.jb_ai_strafe : 1);
	if (self.jb_ai_phase >= 360)
		self.jb_ai_phase = self.jb_ai_phase - 360;
	if (self.jb_ai_phase < 0)
		self.jb_ai_phase = self.jb_ai_phase + 360;

	ang = self.jb_ai_phase;
	if (targ != world)
	{
		center = targ.origin + '0 0 110';
		sn = sin (ang * 1.5);
		rad = 380 + 140 * sn;
	}
	else
	{
		center = self.jb_spawn_org;
		rad = 320;
	}

	// Evasive 3D figure-8 dogfight orbit
	makevectors ('0 1 0' * ang);
	target_pos_x = center_x + v_forward_x * rad;
	target_pos_y = center_y + v_forward_y * rad * 0.85;
	makevectors ('0 1 0' * (ang * 2));
	target_pos_z = center_z + v_forward_y * 85;

	// Floor & wall avoidance whiskers
	traceline (self.origin, self.origin - '0 0 110', TRUE, self);
	if (trace_fraction < 1.0)
		target_pos_z = max (target_pos_z, self.origin_z + 90);
	traceline (self.origin, self.origin + normalize (self.velocity) * 140, TRUE, self);
	if (trace_fraction < 0.9)
		target_pos = target_pos + trace_plane_normal * 220;

	slow_mult = (time < self.jb_slow_t) ? JB_BIRD_SLOW_MULT : 1.0;
	delta = target_pos - self.origin;
	spd = 820 * slow_mult;
	if (vlen (delta) > 8)
		self.velocity = self.velocity + (normalize (delta) * spd - self.velocity) * bound (0, dt * 4.5, 1);

	JB_SlideMove (self, world, dt);

	// Engage target if in range & visible!
	combat_on = FALSE;
	if (targ != world)
	{
		dist = vlen (targ.origin - self.origin);
		if (dist < 1050)
		{
			traceline (self.origin + '0 0 36', targ.origin + '0 0 28', TRUE, self);
			if (trace_fraction >= 0.95)
			{
				combat_on = TRUE;
				self.jb_ai_combat_t = time + 0.6;
				aim_dir = normalize ((targ.origin + '0 0 28') - (self.origin + '0 0 36'));
				dir_ang = vectoangles (aim_dir);
				self.angles_x = bound (-42, JB_NormAngle (dir_ang_x), 42);
				self.angles_y = dir_ang_y;
				self.angles_z = (self.jb_ai_strafe >= 0) ? -22 : 22;

				muz = JB_GetNozzleWorld (self, world, 1);
				// Fair dodgeable aim spread
				aim_dir = normalize (aim_dir + '1 0 0' * (crandom () * 0.06) + '0 1 0' * (crandom () * 0.06) + '0 0 1' * (crandom () * 0.04));

				if (time >= self.jb_ai_fire_t)
				{
					self.jb_ai_fire_t = time + 1.40 + random () * 0.45;
					JB_LaunchBottle (self, self, muz, aim_dir, 900, 22);
				}
			}
		}
	}

	if (!combat_on && vlen (self.velocity) > 40)
	{
		dir_ang = vectoangles (self.velocity);
		self.angles_x = bound (-35, JB_NormAngle (dir_ang_x), 35);
		self.angles_y = dir_ang_y;
		self.angles_z = (self.jb_ai_strafe >= 0) ? -24 : 24;
	}

	if (time < self.jb_ai_combat_t)
		combat_on = TRUE;

	JB_UpdateProps (self, world, combat_on, 1, FALSE);
	JB_UpdateBirdDebuffs (self);
	JB_UpdateAnimAndAudio (self, dt, 1.0, 0, FALSE, combat_on);
	self.nextthink = time + dt;
};

void() JB_IdleThink =
{
	local entity p;
	local float idx;

	if (self.health <= 0)
		return;

	p = self.jb_pilot;
	if (p != world)
	{
		if (p.classname != "player" || p.health <= 0 || p.jb_vehicle != self)
			JB_Leave (self, self.origin + '0 0 28', '0 0 0', FALSE);
		self.nextthink = time + 0.1;
		return;
	}

	if (self.jb_ai)
	{
		self.think = JB_AutopilotThink;
		self.nextthink = time + 0.05;
		return;
	}

	idx = floor (time * 9.0);
	idx = idx - 12 * floor (idx / 12);
	self.frame = 60 + idx;

	if (self.health <= JB_LOW_HP && veh_fx_smoke > 0 && time >= self.jb_smoke_t)
	{
		self.jb_smoke_t = time + 0.16;
		pointparticles (veh_fx_smoke, self.origin + '0 0 32', '0 0 18', 1);
	}
	self.nextthink = time + 0.1;
};

// ---------------------------------------------------------------- Rocket Damage & Shootdown

void(entity attacker, float take) JB_Pain =
{
	local float r_left, throttled;
	local string msg;

	throttled = FALSE;
	if (time < self.jb_feather_t)
	{
		if (self.health > JB_LOW_HP)
			return;
		throttled = TRUE;	// low HP: skin, sound and hit marker still react to every hit, the feathers and reliable sprints don't
	}
	else
	{
		self.jb_feather_t = time + 0.2;
		JB_SpawnFeathers (self.origin + '0 0 34', 8, 1.0);
	}
	sound (self, CHAN_AUTO, "john_bird/feather_hit.wav", 1, 0.55);

	if (self.health <= JB_LOW_HP)
		self.skin = 1;

	if (random () < 0.45 && time >= self.pain_finished)
	{
		sound (self, CHAN_VOICE, "john_bird/jv_hurt.wav", 1, 0.55);
		self.pain_finished = time + 0.9;
		self.jb_voice_t = time + 3.2;
	}

	if (attacker != world && attacker.classname == "player" && attacker.ishuman == 1)
		attacker.jb_st_hit = attacker.jb_st_hit + 1;
	if (throttled)
		return;

	r_left = ceil (self.health / JB_ROCKET_DMG);
	if (r_left < 1)
		r_left = 1;

	msg = strcat ("Winged John hit! [", ftos (ceil (self.health)), "/140 HP — ", ftos (r_left));
	if (r_left == 1)
		msg = strcat (msg, " rocket left!]\n");
	else
		msg = strcat (msg, " rockets left]\n");

	if (attacker != world && attacker.classname == "player" && attacker.ishuman == 1)
		sprint (attacker, msg);
	if (self.jb_pilot != world && self.jb_pilot != attacker && self.jb_pilot.ishuman == 1)
		sprint (self.jb_pilot, msg);
};

void() JB_DieBlast;

void() JB_Die =
{
	local entity pilot, killer;
	local vector eject_vel;

	if (self.jb_dying)
		return;
	self.jb_dying = TRUE;
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.touch = SUB_Null;
	JB_CleanupProps (self);

	killer = damage_attacker;
	if (killer == world)
		killer = self.enemy;
	self.enemy = killer;

	pilot = self.jb_pilot;
	self.jb_blast_pilot = pilot;

	if (pilot != world)
	{
		if (self.jb_temp)
		{
			if (pilot.ud_boost >= 0.5)
				pilot.jb_cooldown_t = time + 12.0;
			else
				pilot.jb_cooldown_t = time + 25.0;
		}
		else
			pilot.jb_cooldown_t = time + 6.0;
		eject_vel = self.velocity * 0.45 + '0 0 240';
		JB_Leave (self, JB_FindExitPos (self, pilot), eject_vel, TRUE);
	}

	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.think = JB_DieBlast;
	self.nextthink = time;
};

void() JB_DieBlast =
{
	local entity pilot, killer;
	local vector boom_org;

	killer = self.enemy;
	pilot = self.jb_blast_pilot;
	self.jb_blast_pilot = world;
	boom_org = self.origin + '0 0 32';

	sound (self, CHAN_VOICE, "john_bird/shootdown.wav", 1, 0.45);
	sound (self, CHAN_AUTO, "weapons/r_exp3.wav", 1, 0.50);
	JB_SpawnFeathers (boom_org, 28, 1.45);

	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, boom_org_x);
	WriteCoord (MSG_BROADCAST, boom_org_y);
	WriteCoord (MSG_BROADCAST, boom_org_z);
	if (veh_fx_explode > 0)
		pointparticles (veh_fx_explode, boom_org, '0 0 0', 1);

	if (killer != world && killer.classname == "player" && killer.ishuman == 1)
		sprint (killer, "BOOM! Shot down Winged Breezy-Hair John!\n");

	jb_inflicting = 1;
	if (pilot != world && pilot.classname == "player" && pilot.health > 0)
	{
		if (killer != world && killer != pilot)
			T_Damage (pilot, self, killer, 50);
		else
			T_Damage (pilot, self, self, 35);
	}
	if (killer != world)
		T_RadiusDamage (self, killer, 120, pilot);
	else
		T_RadiusDamage (self, self, 120, pilot);
	jb_inflicting = 0;

	if (self.jb_temp)
	{
		self.solid = SOLID_NOT;
		self.takedamage = DAMAGE_NO;
		self.movetype = MOVETYPE_NONE;
		setmodel (self, "");	// clears modelindex too, so the shot-down bird does not hang visible for 1.5 s
		self.think = SUB_Remove;
		self.nextthink = time + 1.5;
	}
	else
	{
		self.solid = SOLID_NOT;
		self.takedamage = DAMAGE_NO;
		self.movetype = MOVETYPE_NONE;
		self.effects = self.effects | EF_NODRAW;
		self.velocity = '0 0 0';
		self.think = JB_Respawn;
		self.nextthink = time + 22;
	}
};

// ---------------------------------------------------------------- Entity Spawn, Prompts & Impulses

void(entity jb, float is_temp) JB_InitEntity =
{
	JohnBird_Precache ();
	jb_has_birds = TRUE;

	jb.classname = "misc_vehicle_johnbird";
	jb.netname = "Winged Breezy-Hair John";
	jb.jb_temp = is_temp;
	jb.jb_pilot = world;
	jb.jb_cam = world;
	jb.jb_can_ent = world;
	jb.jb_match_ent = world;
	jb.enemy = world;
	jb.jb_voice_last1 = -1;
	jb.jb_voice_last2 = -1;
	jb.jb_carve_spd = 0;
	jb.jb_cam_pull = 0;
	jb.jb_match_on = FALSE;
	jb.jb_ammo = JB_MAX_AMMO;
	jb.jb_ammo_regen_t = 0;
	jb.jb_first_shot_said = FALSE;
	jb.jb_dry_snd_t = 0;
	jb.jb_slow_t = 0;
	jb.jb_burn_t = 0;
	jb.jb_burn_by = world;
	jb.health = JB_MAX_HP;
	jb.max_health = JB_MAX_HP;
	jb.skin = 0;
	jb.th_pain = JB_Pain;
	jb.th_die = JB_Die;

	setmodel (jb, "progs/john_bird_head.md3");
	jb.jb_spawn_org = jb.origin;
	jb.jb_spawn_yaw = jb.angles_y;
	JB_Park (jb);
};

void() misc_vehicle_johnbird =
{
	remove (self);
};

entity(entity p) JohnBird_NearPerched =
{
	local entity e, best;
	local float d, bd;

	if (!jb_has_birds)
		return world;
	best = world;
	bd = 170;
	e = findradius (p.origin, 170);
	while (e != world)
	{
		if (e.classname == "misc_vehicle_johnbird" && e.health > 0 && e.jb_pilot == world && !e.jb_ai)
		{
			d = vlen (e.origin - p.origin);
			if (d < bd)
			{
				bd = d;
				best = e;
			}
		}
		e = e.chain;
	}
	return best;
};

void() JohnBird_NearPrompt =
{
	local entity jb;

	if (!jb_has_birds || self.ishuman != 1 || self.health <= 0 || self.jb_vehicle != world || self.veh_van != world || self.veh_ride != world || self.classname != "player")
		return;
	if (time < self.jb_prompt_scan_t)
		return;
	self.jb_prompt_scan_t = time + 0.12;
	jb = JohnBird_NearPerched (self);
	if (jb == world)
	{
		if (time > self.jb_prompt_t)
			self.jb_prompt_ent = world;
		return;
	}
	if (self.jb_hint_shown || time < self.jb_prompt_t)
		return;
	if (self.jb_prompt_ent == jb)
	{
		self.jb_prompt_t = time + 35;
		return;
	}
	self.jb_prompt_ent = jb;
	self.jb_prompt_t = time + 35;
	centerprint (self, "Press H to fly Winged John");
};

float() JohnBird_TryEnterKey =
{
	local entity jb, van;

	if (self.health <= 0 || self.jb_vehicle != world || self.veh_van != world || self.veh_ride != world)
		return FALSE;
	jb = JohnBird_NearPerched (self);
	if (jb == world)
		return FALSE;

	van = Veh_SeatOf (self);
	if (van != world && vlen (van.origin - self.origin) < vlen (jb.origin - self.origin))
		return FALSE;

	JB_Enter (self, jb);
	return TRUE;
};

entity(entity p) JB_MyTemp =
{
	local entity e;

	e = p.jb_my_temp;
	if (e != world && (bm_wasfreed (e) || e.classname != "misc_vehicle_johnbird" || !e.jb_temp || e.jb_summoner != p))
	{
		p.jb_my_temp = world;
		e = world;
	}
	return e;
};

void() JohnBird_ClientGone =
{
	local entity jb;

	jb = self.jb_vehicle;
	if (jb != world && jb.jb_pilot == self)
		JB_Leave (jb, jb.origin + '0 0 28', '0 0 0', FALSE);
	self.jb_vehicle = world;
	jb = JB_MyTemp (self);
	if (jb != world && jb.jb_pilot == world)
		remove (jb);
	self.jb_my_temp = world;
};

void() JB_PruneTempBirds =
{
	local entity e, oldest;
	local float n;

	n = 0;
	oldest = world;
	e = find (world, classname, "misc_vehicle_johnbird");
	while (e != world)
	{
		if (e.jb_temp && e.jb_pilot == world && e.health > 0)
		{
			n = n + 1;
			if (oldest == world)
				oldest = e;
		}
		e = find (e, classname, "misc_vehicle_johnbird");
	}
	if (n > 5 && oldest != world)
	{
		JB_CleanupProps (oldest);
		remove (oldest);
	}
};

void() JohnBird_Impulse =
{
	local entity jb;
	local vector org;

	JohnBird_NearPrompt ();
	if (self.impulse < 97 || self.impulse > 99)
		return;

	if (self.impulse == 98)
	{
		self.impulse = 0;
		if (self.health <= 0 || self.veh_van != world || self.veh_ride != world || self.fd_head != world)
			return;
		if (time < self.jb_cooldown_t)
		{
			sprint (self, strcat ("Winged John recovering feathers (", ftos (ceil (self.jb_cooldown_t - time)), "s)...\n"));
			return;
		}
		tracebox (self.origin + '0 0 14', '-28 -36 -4', '28 36 58', self.origin + '0 0 28', FALSE, self);
		if (trace_startsolid || trace_allsolid || trace_fraction < 1)
		{
			sprint (self, "Need open headroom to summon Winged John!\n");
			return;
		}
		jb = JB_MyTemp (self);
		if (jb != world && jb.jb_pilot == world && jb.health > 0)
		{
			JB_CleanupProps (jb);
			remove (jb);
			self.jb_my_temp = world;
		}
		jb = spawn ();
		jb.angles = '0 0 0';
		jb.angles_y = self.v_angle_y;
		setorigin (jb, self.origin + '0 0 12');
		JB_InitEntity (jb, TRUE);
		jb.jb_summoner = self;
		self.jb_my_temp = jb;
		JB_Enter (self, jb);
		return;
	}

	if (!autocvar_sv_cheats)
		return;

	if (self.impulse == 97)
	{
		self.impulse = 0;
		JB_PruneTempBirds ();
		makevectors ('0 1 0' * self.v_angle_y);
		org = self.origin + v_forward * 180 + '0 0 18';
		jb = spawn ();
		jb.angles = '0 0 0';
		jb.angles_y = JB_NormAngle (self.v_angle_y + 180);
		setorigin (jb, org);
		JB_InitEntity (jb, TRUE);
		sprint (self, "Spawned perched Winged Breezy-Hair John (140 HP — Press H to fly, or 1-2 rockets to shoot down!)\n");
		return;
	}

	if (self.impulse == 99)
	{
		self.impulse = 0;
		JB_PruneTempBirds ();
		makevectors ('0 1 0' * self.v_angle_y);
		org = self.origin + v_forward * 340 + '0 0 200';
		jb = spawn ();
		jb.angles = '0 0 0';
		jb.angles_y = self.v_angle_y;
		setorigin (jb, org);
		JB_InitEntity (jb, TRUE);
		jb.movetype = MOVETYPE_NONE;
		setsize (jb, '-28 -36 -4', '28 36 58');
		jb.jb_spawn_org = org;
		jb.jb_ai = TRUE;
		jb.jb_ai_strafe = 1;
		jb.jb_ai_mode = 0;
		jb.jb_ai_mode_t = time + 3.0;
		jb.jb_ai_fire_t = time + 1.0;
		jb.jb_flap_t = time + 0.1;
		jb.jb_voice_t = time + 0.35;
		jb.think = JB_AutopilotThink;
		jb.nextthink = time + 0.05;
		sprint (self, "Launched AI Dogfighter Winged John overhead! (Fights back with hairspray & bottles!)\n");
		return;
	}
};
