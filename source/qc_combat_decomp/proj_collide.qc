#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
PROJECTILE COLLISION & SKEET-SHOOTING INTERACTIVITY (proj_collide.qc)
================
*/

// ---------------------------------------------------------------- Geometry & Ownership Helpers

float(vector p0, vector p1, vector q) PC_SegDist2 =
{
	local vector ab, aq, closest;
	local float len2, t;

	ab = p1 - p0;
	aq = q - p0;
	len2 = ab * ab;
	if (len2 <= 0.0001)
		return aq * aq;
	t = (aq * ab) / len2;
	if (t < 0)
		t = 0;
	else if (t > 1)
		t = 1;
	closest = p0 + ab * t;
	closest = q - closest;
	return closest * closest;
};

vector(entity e) PC_Center =
{
	return e.origin + (e.mins + e.maxs) * 0.5;
};

entity(entity e) PC_GetOwner =
{
	if (!e || e == world)
		return world;
	if (e.classname == "milky")
		return e.milky_owner;
	if (e.classname == "misc_vehicle_johnbird")
	{
		if (e.jb_pilot != world)
			return e.jb_pilot;
		if (e.jb_ai && e.jb_summoner != world)
			return e.jb_summoner;
		return world;
	}
	return e.owner;
};

float(entity a, entity b) PC_IsAlly =
{
	if (!a || !b || a == world || b == world)
		return FALSE;
	if (a == b)
		return TRUE;
	if ((teamplay || CTF_ENABLED) && a.team > 0 && a.team == b.team)
		return TRUE;
	return FALSE;
};

string(entity e) PC_Label =
{
	if (e.classname == "dookie_shot")
		return "Flying Dookie";
	if (e.classname == "robdob")
		return "Rob Dob Drone";
	if (e.classname == "wc_shot")
		return "Wheelman";
	if (e.classname == "kyle_proj")
		return "Pocket Kyle";
	if (e.classname == "megaman")
		return "Mega Man";
	if (e.classname == "milky")
		return "Pink Lady";
	if (e.classname == "missile")
		return "Rocket";
	if (e.classname == "grenade")
		return "JohnWave Grenade";
	if (e.classname == "greenjar_proj")
		return "Jar o' Green Guys";
	if (e.classname == "greenguy_mini")
		return "Green Wheelman";
	if (e.classname == "pickle")
		return "Pickle Surprise";
	if (e.classname == "bigbanana")
		return "Big Banana";
	if (e.classname == "netsend_disk")
		return "LOL.BAT Disk";
	if (e.classname == "misc_vehicle_johnbird")
		return "Winged Breezy-Hair John";
	return "Projectile";
};

float(entity e) PC_IsAlive =
{
	if (!e || e == world || bm_wasfreed (e))
		return FALSE;
	if (e.pc_popped || e.pc_kind == PC_KIND_NONE)
		return FALSE;
	if (e.solid == SOLID_NOT)
		return FALSE;
	if (e.classname == "fh_dead" || e.classname == "mmdead")
		return FALSE;
	if (e.classname == "robdob" && (e.fd_boom || e.fd_blowing || e.health <= 0))
		return FALSE;
	if (e.classname == "dookie_shot" && e.dk_done)
		return FALSE;
	if (e.classname == "kyle_proj" && (e.ky_done || e.ky_mode == KY_MODE_DYING))
		return FALSE;
	if (e.classname == "milky" && e.milky_hp <= 0)
		return FALSE;
	if (e.classname == "misc_vehicle_johnbird" && (e.jb_dying || e.health <= 0))
		return FALSE;
	return TRUE;
};

// ---------------------------------------------------------------- Registration & Reset

void(entity e, float kind, float rad) PC_Register =
{
	if (!e || e == world)
		return;
	e.pc_kind = kind;
	e.pc_rad = rad;
	e.pc_born = time;
	e.pc_popped = FALSE;
	e.pc_pinata = FALSE;
	e.pc_killer = world;
	e.pc_clash_cd = 0;
	e.pc_prev_org = PC_Center (e);
	if (!e.pc_reg)
	{
		e.pc_reg = TRUE;
		e.pc_next = pc_head;
		pc_head = e;
	}
};

void(entity spk) PC_RegisterSpike =
{
	if (!spk || spk == world)
		return;
	spk.pc_prev_org = spk.origin;
	if (!spk.pc_spike_reg)
	{
		spk.pc_spike_reg = TRUE;
		spk.pc_spike_next = pc_spike_head;
		pc_spike_head = spk;
	}
};

void(entity p) PC_ResetPlayer =
{
	if (!p || p == world)
		return;
	p.pc_skeet_cnt = 0;
	p.pc_skeet_t = 0;
	p.pc_skeet_frame = 0;
	p.pc_refund_cooldown = FALSE;
	p.pc_poop_t = 0;
	p.pc_poop_fx_t = 0;
	if (p.pc_poop_cshift)
	{
		p.pc_poop_cshift = FALSE;
		if (p.ishuman == 1)
			stuffcmd (p, "v_cshift 0 0 0 0\n");
	}
};

// ---------------------------------------------------------------- Poop-Coating Debuff & Dookie Pinata

void(entity targ, float dur, float apply_cshift) PC_ApplyPoopCoat =
{
	local entity pilot;

	if (!targ || targ == world || bm_wasfreed (targ))
		return;

	if (targ.classname == "robdob")
	{
		pilot = targ.owner;
		if (pilot != world && pilot.classname == "player" && pilot.fd_head == targ)
		{
			pilot.pc_poop_t = max (pilot.pc_poop_t, time + min (dur, 1.6));
			if (apply_cshift && pilot.ishuman == 1)
			{
				pilot.pc_poop_cshift = TRUE;
				stuffcmd (pilot, "v_cshift 110 72 28 135\n");
				centerprint (pilot, "^3POOP-SPLAT ON YOUR DRONE LENS!\n");
			}
		}
		return;
	}

	targ.pc_poop_t = max (targ.pc_poop_t, time + dur);
	pointparticles (particleeffectnum ("dookie_drip"), PC_Center (targ), '0 0 0', 4);
	sound (targ, CHAN_AUTO, "dookie/dk_flies.wav", 0.9, ATTN_NORM);

	if (targ.classname == "player" && targ.health > 0)
	{
		if (apply_cshift && targ.ishuman == 1)
		{
			targ.pc_poop_cshift = TRUE;
			stuffcmd (targ, "v_cshift 110 72 28 110\n");
			centerprint (targ, "^3POOP-COATED! Ew! (-30% speed)\n");
		}
	}
	else if (targ.classname == "misc_vehicle_johnbird" && targ.health > 0 && !targ.jb_dying)
	{
		pilot = targ.jb_pilot;
		if (pilot != world && pilot.classname == "player" && pilot.ishuman == 1)
		{
			pilot.pc_poop_t = max (pilot.pc_poop_t, time + dur);
			if (apply_cshift)
			{
				pilot.pc_poop_cshift = TRUE;
				stuffcmd (pilot, "v_cshift 110 72 28 105\n");
				centerprint (pilot, "^3BIRD POOP-COATED! (-30% speed)\n");
			}
		}
	}
};

void(entity dookie, vector org, entity attacker) PC_DookiePinata =
{
	local entity e;
	local float d;

	sound (dookie, CHAN_AUTO, "dookie/dk_scream.wav", 1.0, 0.7);
	pointparticles (particleeffectnum ("dookie_boom"), org, '0 0 0', 2);

	// Coat nearby players, Rob Dob cameras, and John Birds in stink & slow
	e = findradius (org, PC_POOP_RADIUS);
	while (e)
	{
		if (e != dookie && !bm_wasfreed (e))
		{
			if (e.classname == "player" && e.health > 0 && e.jb_vehicle == world && e.rr_vehicle == world && e.fd_head == world)
			{
				if (CanDamage (e, dookie))
					PC_ApplyPoopCoat (e, PC_POOP_DUR, TRUE);
			}
			else if (e.classname == "misc_vehicle_johnbird" && e.health > 0 && !e.jb_dying)
			{
				d = vlen (PC_Center (e) - org);
				if (d <= PC_POOP_RADIUS)
					PC_ApplyPoopCoat (e, PC_POOP_DUR, TRUE);
			}
			else if (e.classname == "robdob" && !e.fd_boom)
			{
				if (CanDamage (e, dookie))
					PC_ApplyPoopCoat (e, 1.6, TRUE);
			}
		}
		e = e.chain;
	}
};

void() PC_PlayerFrame =
{
	local vector v;
	local float z, sp, cap;

	if (self.pc_refund_cooldown)
	{
		self.pc_refund_cooldown = FALSE;
		self.attack_finished = time;
	}

	if (self.health <= 0 || self.deadflag || time >= self.pc_poop_t)
	{
		if (self.pc_poop_cshift)
		{
			self.pc_poop_cshift = FALSE;
			if (self.ishuman == 1)
				stuffcmd (self, "v_cshift 0 0 0 0\n");
		}
		if (time >= self.pc_poop_t)
			self.pc_poop_t = 0;
		return;
	}

	if (self.fd_head == world && self.jb_vehicle == world && self.rr_vehicle == world && self.veh_ride == world && self.mmt_tank == world)
	{
		cap = cvar ("sv_maxspeed");
		if (cap <= 0)
			cap = 320;
		cap = cap * PC_POOP_SLOW_MULT;
		v = self.velocity;
		z = v_z;
		v_z = 0;
		sp = vlen (v);
		if (sp > cap)
		{
			v = normalize (v) * cap;
			v_z = z;
			self.velocity = v;
		}
	}

	if (time >= self.pc_poop_fx_t)
	{
		self.pc_poop_fx_t = time + 0.25;
		if (self.fd_head != world)
			pointparticles (particleeffectnum ("dookie_drip"), self.fd_head.origin, '0 0 0', 2);
		else
			pointparticles (particleeffectnum ("dookie_drip"), self.origin + '0 0 24', '0 0 0', 2);
		sound (self, CHAN_BODY, "dookie/dk_flies.wav", 0.55, ATTN_NORM);
	}
};

// ---------------------------------------------------------------- Skeet-Shooting Rewards & Combo

void(entity p) PC_RefundWeaponAmmo =
{
	local entity oself;
	local float a, mx;

	if (!p || p.classname != "player")
		return;

	oself = self;
	self = p;

	if (self.weapon == IT_SHOTGUN)
	{
		self.ammo_shells = min (100, self.ammo_shells + 1);
		self.currentammo = self.ammo_shells;
	}
	else if (self.weapon == IT_SUPER_SHOTGUN)
	{
		self.ammo_shells = min (100, self.ammo_shells + 2);
		self.currentammo = self.ammo_shells;
	}
	else if (self.weapon == IT_NAILGUN || self.weapon == IT_SUPER_NAILGUN)
	{
		self.ammo_nails = min (200, self.ammo_nails + 4);
		self.currentammo = self.ammo_nails;
	}
	else if (self.weapon == IT_LIGHTNING)
	{
		self.ammo_cells = min (100, self.ammo_cells + 5);
		self.currentammo = self.ammo_cells;
	}
	else if (self.weapon == IT_FUNGUN)
	{
		if (self.fg_sel == FG_M4)
		{
			mx = FunGun_Max (FG_M4);
			a = FunGun_Ammo (self, FG_M4);
			FunGun_SetAmmo (self, FG_M4, min (mx, a + 5));
		}
		else if (self.fg_sel == FG_GARAND)
		{
			mx = FunGun_Max (FG_GARAND);
			a = FunGun_Ammo (self, FG_GARAND);
			FunGun_SetAmmo (self, FG_GARAND, min (mx, a + 2));
		}
	}

	if (self.bm_rl_slot && BM_IsFirearmSlot (self.bm_rl_slot))
		self.bm_rl_slot = 0;
	self.attack_finished = time;
	self.pc_refund_cooldown = TRUE;
	self = oself;
};

void(entity attacker, entity victim_proj) PC_AwardSkeet =
{
	local entity own;
	local string lbl;

	if (!attacker || attacker.classname != "player" || attacker.health <= 0)
		return;
	own = PC_GetOwner (victim_proj);
	if (own == attacker || PC_IsAlly (attacker, own))
		return;

	if (time > attacker.pc_skeet_t)
		attacker.pc_skeet_cnt = 0;
	attacker.pc_skeet_cnt = attacker.pc_skeet_cnt + 1;
	attacker.pc_skeet_t = time + PC_SKEET_WINDOW;
	lbl = PC_Label (victim_proj);

	if (attacker.pc_skeet_cnt == 1)
	{
		PC_RefundWeaponAmmo (attacker);
		if (attacker.ishuman == 1)
		{
			stuffcmd (attacker, "playvol misc/mmhit3.wav 0.65\n");
			sound (attacker, CHAN_AUTO, "weapons/pkup.wav", 0.7, ATTN_NORM);
			centerprint (attacker, strcat ("^3SKEET SHOT!^7 Popped ", lbl, "! (Ammo Refunded)\n"));
		}
	}
	else if (attacker.pc_skeet_cnt == 2)
	{
		PC_RefundWeaponAmmo (attacker);
		if (attacker.health < max (100, attacker.max_health))
			attacker.health = min (max (100, attacker.max_health), attacker.health + 25);
		if (attacker.armortype == 0)
		{
			attacker.armortype = 0.3;
			attacker.items = attacker.items | IT_ARMOR1;
		}
		attacker.armorvalue = min (150, attacker.armorvalue + 25);
		if (attacker.ishuman == 1)
		{
			stuffcmd (attacker, "playvol misc/mmhit3.wav 0.75\n");
			sound (attacker, CHAN_AUTO, "items/r_item1.wav", 0.85, ATTN_NORM);
			centerprint (attacker, strcat ("^2DOUBLE SKEET!^7 ", lbl, " denied! (+25 HP/AP)\n"));
		}
	}
	else
	{
		PC_RefundWeaponAmmo (attacker);
		attacker.items = attacker.items | IT_QUAD;
		attacker.super_damage_finished = max (attacker.super_damage_finished, time + 5.0);
		attacker.super_time = 1;
		sound (attacker, CHAN_ITEM, "items/damage.wav", 1.0, ATTN_NORM);
		if (attacker.ishuman == 1)
		{
			stuffcmd (attacker, "playvol misc/mmhit3.wav 0.85\n");
			centerprint (attacker, strcat ("^1SKEET GOD!^7 ", lbl, " sniped! (5s QUAD DAMAGE!)\n"));
		}
		bprint ("^3SKEET GOD! ^7", attacker.netname, " sniped a ", lbl, " out of the sky!\n");
	}
};

// ---------------------------------------------------------------- Deferred Safe Detonations

void() PC_RocketExplodeThink =
{
	other = world;
	T_MissileTouch ();
};

void() PC_GreenJarBurstThink =
{
	GJ_ShatterJar (self.origin, self.owner);
	remove (self);
};

void() PC_BananaBurstThink =
{
	other = world;
	Banana_BigTouch ();
};

void() PC_DiskPopThink =
{
	sendParticle ("TE_GUNSHOT", self.origin, VEC_ORIGIN, 1, 0);
	sound (self, CHAN_AUTO, "robhead/key_beep.wav", 0.85, ATTN_NORM);
	remove (self);
};

void(entity e, entity attacker, float by_shot) PC_PopProjectile =
{
	local entity oself, own;

	if (!e || e == world || e.pc_popped)
		return;
	e.pc_popped = TRUE;
	own = PC_GetOwner (e);

	if (attacker != world && attacker.classname == "player" && attacker != own && !PC_IsAlly (attacker, own))
	{
		if (by_shot)
			PC_AwardSkeet (attacker, e);
		e.pc_killer = attacker;
		if (e.classname != "robdob" && e.classname != "milky" && e.classname != "misc_vehicle_johnbird")
			e.owner = attacker;
	}

	oself = self;
	self = e;

	if (e.classname == "dookie_shot")
	{
		e.pc_pinata = TRUE;
		DK_ProjDie ();
	}
	else if (e.classname == "robdob")
	{
		FD_Die ();
	}
	else if (e.classname == "wc_shot")
	{
		WC_Die ();
	}
	else if (e.classname == "kyle_proj")
	{
		KY_ProjDie ();
	}
	else if (e.classname == "megaman")
	{
		MegaMan_Shot ();
	}
	else if (e.classname == "milky")
	{
		e.milky_hp = 0;
		e.enemy = attacker;
		e.takedamage = DAMAGE_NO;
		e.think = Milky_Burst;
		e.nextthink = time;
	}
	else if (e.classname == "missile")
	{
		e.takedamage = DAMAGE_NO;
		e.touch = SUB_Null;
		e.velocity = '0 0 0';
		e.think = PC_RocketExplodeThink;
		e.nextthink = time;
	}
	else if (e.classname == "grenade")
	{
		e.takedamage = DAMAGE_NO;
		e.touch = SUB_Null;
		e.velocity = '0 0 0';
		e.think = GrenadeExplode;
		e.nextthink = time;
	}
	else if (e.classname == "greenjar_proj")
	{
		e.takedamage = DAMAGE_NO;
		e.touch = SUB_Null;
		e.velocity = '0 0 0';
		e.think = PC_GreenJarBurstThink;
		e.nextthink = time;
	}
	else if (e.classname == "greenguy_mini")
	{
		GJ_StartBalloonPop (e, TRUE);
	}
	else if (e.classname == "pickle")
	{
		e.takedamage = DAMAGE_NO;
		e.touch = SUB_Null;
		e.velocity = '0 0 0';
		e.think = Pk_Explode;
		e.nextthink = time;
	}
	else if (e.classname == "bigbanana")
	{
		e.takedamage = DAMAGE_NO;
		e.touch = SUB_Null;
		e.velocity = '0 0 0';
		e.think = PC_BananaBurstThink;
		e.nextthink = time;
	}
	else if (e.classname == "netsend_disk")
	{
		e.takedamage = DAMAGE_NO;
		e.touch = SUB_Null;
		e.velocity = '0 0 0';
		e.think = PC_DiskPopThink;
		e.nextthink = time;
	}

	self = oself;
};

void(entity e, entity attacker) PC_NoteKilled =
{
	if (!e || e == world || e.pc_popped || !e.pc_reg)
		return;
	e.pc_popped = TRUE;
	if (attacker != world && attacker.classname == "player")
		PC_AwardSkeet (attacker, e);
};

// ---------------------------------------------------------------- Weapon Shooting Interception

float(entity proj, entity attacker) PC_CanShootProj =
{
	local entity own;

	if (!PC_IsAlive (proj))
		return FALSE;
	if (proj.pc_kind == PC_KIND_BIRD)
		return FALSE;
	own = PC_GetOwner (proj);
	if (own == attacker)
		return (time >= proj.pc_born + PC_SELF_GRACE);
	if (PC_IsAlly (attacker, own))
		return FALSE;
	return TRUE;
};

void(entity proj, entity attacker, float dmg, vector hit_pos) PC_HitProjectile =
{
	local float dead_now;

	sendParticle ("TE_GUNSHOT", hit_pos, VEC_ORIGIN, 1, 0);
	sound (proj, CHAN_AUTO, "weapons/tink1.wav", 0.75, ATTN_NORM);

	if (proj.pc_kind == PC_KIND_LIGHT || proj.pc_kind == PC_KIND_DOOKIE)
	{
		PC_PopProjectile (proj, attacker, TRUE);
		return;
	}

	// Character / heavy projectiles take weapon damage and award Skeet on kill
	if (proj.takedamage == DAMAGE_NO && time >= proj.pc_born + 0.10)
		proj.takedamage = DAMAGE_AIM;
	if (proj.takedamage != DAMAGE_NO)
		T_Damage (proj, attacker, attacker, dmg);
	else
		proj.health = proj.health - dmg;

	dead_now = FALSE;
	if (proj.classname == "milky")
		dead_now = (proj.milky_hp <= 0);
	else
		dead_now = (proj.health <= 0);

	if (dead_now)
	{
		if (proj.takedamage == DAMAGE_NO)
			PC_PopProjectile (proj, attacker, TRUE);
		else
			PC_NoteKilled (proj, attacker);
	}
};

float(entity attacker, vector src, vector end, float dmg) PC_TraceIntercept =
{
	local entity e, best;
	local float best_d2, d2, r2;
	local vector c;

	if (!autocvar_bm_proj_collide || !attacker || attacker.classname != "player")
		return FALSE;

	best = world;
	best_d2 = 99999999;

	// If physical trace already hit a John Bird directly, let weapon's normal TraceAttack handle it
	if (trace_ent != world && trace_ent.classname == "misc_vehicle_johnbird")
		return FALSE;

	e = pc_head;
	while (e)
	{
		if (PC_CanShootProj (e, attacker))
		{
			c = PC_Center (e);
			r2 = e.pc_rad * e.pc_rad;
			if (trace_ent == e || PC_SegDist2 (src, end, c) <= r2)
			{
				d2 = (c - src) * (c - src);
				if (d2 < best_d2)
				{
					best_d2 = d2;
					best = e;
				}
			}
		}
		e = e.pc_next;
	}

	if (best == world)
		return FALSE;

	PC_HitProjectile (best, attacker, dmg, PC_Center (best));
	return TRUE;
};

// ---------------------------------------------------------------- Mid-Air Projectile Collisions

void(entity bird, vector from_org, float feather_n, float dmg, entity inflictor, entity attacker) PC_KnockBird =
{
	local vector side, push;
	local entity pilot;

	side = PC_Center (bird) - from_org;
	side_z = 0;
	if (vlen (side) < 2)
		side = randomvec ();
	side_z = 0;
	side = normalize (side);
	push = side * 420 + '0 0 160';
	bird.flags = bird.flags - (bird.flags & FL_ONGROUND);
	bird.velocity = bird.velocity + push;
	bird.angles_z = bound (-45, bird.angles_z + ((random () < 0.5) ? -32 : 32), 45);
	JB_SpawnFeathers (PC_Center (bird), feather_n, 1.35);
	sound (bird, CHAN_AUTO, "john_bird/feather_hit.wav", 1.0, ATTN_NORM);

	if (dmg > 0 && bird.takedamage)
	{
		jb_inflicting = 1;
		T_Damage (bird, inflictor, attacker, dmg);
		jb_inflicting = 0;
	}
	pilot = bird.jb_pilot;
	if (pilot != world && pilot.classname == "player" && pilot.ishuman == 1 && time >= bird.pc_clash_cd)
	{
		bird.pc_clash_cd = time + 0.6;
		centerprint (pilot, "^3MID-AIR FENDER-BENDER!\n");
	}
};

float(entity a, entity b) PC_CanCollidePair =
{
	local entity oa, ob;

	if (!autocvar_bm_proj_collide)
		return FALSE;
	if (!PC_IsAlive (a) || !PC_IsAlive (b) || a == b)
		return FALSE;

	// Two parked/flying John Birds don't trigger projectile clash logic against each other
	if (a.pc_kind == PC_KIND_BIRD && b.pc_kind == PC_KIND_BIRD)
		return FALSE;

	// A parked idle bird only gets struck by Rob Dob or Dookie, not stray resting contacts
	if (a.pc_kind == PC_KIND_BIRD && a.jb_pilot == world && !a.jb_ai && vlen (a.velocity) < 40)
	{
		if (b.pc_kind != PC_KIND_ROB && b.pc_kind != PC_KIND_DOOKIE)
			return FALSE;
	}
	if (b.pc_kind == PC_KIND_BIRD && b.jb_pilot == world && !b.jb_ai && vlen (b.velocity) < 40)
	{
		if (a.pc_kind != PC_KIND_ROB && a.pc_kind != PC_KIND_DOOKIE)
			return FALSE;
	}

	oa = PC_GetOwner (a);
	ob = PC_GetOwner (b);
	if (oa != world && oa == ob)
		return FALSE;
	if (PC_IsAlly (oa, ob))
		return FALSE;

	return TRUE;
};

void(entity rob1, entity rob2) PC_RobVsRob =
{
	local vector mid;
	local entity p1, p2, oself;
	local string n1, n2;

	mid = (PC_Center (rob1) + PC_Center (rob2)) * 0.5;
	p1 = rob1.owner;
	p2 = rob2.owner;

	PC_PopProjectile (rob1, p2, FALSE);
	PC_PopProjectile (rob2, p1, FALSE);

	// Double bouncing mini-heads + extra electric arcs!
	oself = self;
	self = rob1;
	FD_Minis ();
	FD_Shock (rob1, TRUE);
	FD_ImpactFX (mid);
	self = rob2;
	FD_Minis ();
	FD_Shock (rob2, TRUE);
	self = oself;

	sound (rob1, CHAN_AUTO, "robhead/pop.wav", 1.0, ATTN_NONE);
	n1 = (p1 != world && p1.netname != "") ? p1.netname : "Someone";
	n2 = (p2 != world && p2.netname != "") ? p2.netname : "Someone";
	bprint ("^3ROB COLLISION! ^7", n1, " & ", n2, "'s drones crashed head-on in mid-air!\n");
};

void(entity rob, entity bird) PC_RobVsBird =
{
	local entity rp, bp;
	local string rn;

	rp = rob.owner;
	bp = bird.jb_pilot;
	rob.enemy = bird;
	PC_PopProjectile (rob, bp, FALSE);

	// Feather-Fender-Bender: knocks bird spinning sideways & sheds a massive feather cloud
	PC_KnockBird (bird, PC_Center (rob), 26, 0, rob, rp);

	rn = (rp != world && rp.netname != "") ? rp.netname : "A Rob Dob";
	if (bp != world && bp.netname != "")
		bprint ("^3FEATHER-FENDER-BENDER! ^7", rn, "'s drone slammed into ", bp.netname, "'s John Bird!\n");
	else
		bprint ("^3FEATHER-FENDER-BENDER! ^7", rn, "'s drone slammed into a John Bird!\n");
};

float(entity heavy, entity light) PC_HeavyVsLight =
{
	local entity ho, lo;
	local float dmg;
	local vector mid;

	ho = PC_GetOwner (heavy);
	lo = PC_GetOwner (light);
	mid = PC_Center (light);

	sendParticle ("TE_GUNSHOT", mid, VEC_ORIGIN, 1, 0);
	if (heavy.pc_kind != PC_KIND_BIRD)
		light.pc_blast_ignore = heavy;
	PC_PopProjectile (light, ho, FALSE);

	if (heavy.pc_kind == PC_KIND_BIRD)
	{
		dmg = 0;
		if (light.classname == "missile" || light.classname == "grenade")
			dmg = 100;	// preserve John Bird 5-rocket shootdown balance
		PC_KnockBird (heavy, mid, 10, dmg, light, lo);
	}
	else
	{
		sound (heavy, CHAN_AUTO, "weapons/tink1.wav", 0.9, ATTN_NORM);
	}

	if (ho != world && ho.classname == "player" && ho.ishuman == 1 && time >= heavy.pc_clash_cd)
	{
		heavy.pc_clash_cd = time + 0.5;
		centerprint (ho, strcat ("^3MID-AIR INTERCEPTION!^7 Swatted ", PC_Label (light), "!\n"));
	}
	return FALSE;	// heavy plows right through!
};

float(entity a, entity b) PC_HandlePair =
{
	local vector mid;
	local entity oa, ob;

	if (!PC_CanCollidePair (a, b))
		return FALSE;

	// 1. Rob vs Rob
	if (a.pc_kind == PC_KIND_ROB && b.pc_kind == PC_KIND_ROB)
	{
		PC_RobVsRob (a, b);
		return TRUE;
	}

	// 2. Rob vs John Bird (Feather-Fender-Bender)
	if (a.pc_kind == PC_KIND_ROB && b.pc_kind == PC_KIND_BIRD)
	{
		PC_RobVsBird (a, b);
		return TRUE;
	}
	if (b.pc_kind == PC_KIND_ROB && a.pc_kind == PC_KIND_BIRD)
	{
		PC_RobVsBird (b, a);
		return FALSE;
	}

	oa = PC_GetOwner (a);
	ob = PC_GetOwner (b);
	mid = (PC_Center (a) + PC_Center (b)) * 0.5;

	// 3. Dookie (Super-Splat Pinata + Poop-Coating) vs anything
	if (a.pc_kind == PC_KIND_DOOKIE || b.pc_kind == PC_KIND_DOOKIE)
	{
		local entity dk, oth;
		if (a.pc_kind == PC_KIND_DOOKIE)
		{
			dk = a;
			oth = b;
		}
		else
		{
			dk = b;
			oth = a;
		}
		PC_PopProjectile (dk, PC_GetOwner (oth), FALSE);
		if (oth.pc_kind == PC_KIND_BIRD)
		{
			PC_KnockBird (oth, mid, 16, 45, dk, PC_GetOwner (dk));
			PC_ApplyPoopCoat (oth, PC_POOP_DUR, TRUE);
		}
		else
		{
			if (oth.pc_kind == PC_KIND_ROB)
				PC_ApplyPoopCoat (oth, 1.6, TRUE);
			PC_PopProjectile (oth, PC_GetOwner (dk), FALSE);
			if (oth.pc_kind == PC_KIND_HEAVY || oth.pc_kind == PC_KIND_ROB)
				bprint ("^3MID-AIR POOP INTERCEPTION! ^7", PC_Label (oth), " collided with a Flying Dookie!\n");
		}
		return (a != oth || a.pc_popped);
	}

	// 4. Heavy / Bird vs Light (Heavy plows through & swats Light aside)
	if ((a.pc_kind == PC_KIND_HEAVY || a.pc_kind == PC_KIND_BIRD) && b.pc_kind == PC_KIND_LIGHT)
		return PC_HeavyVsLight (a, b);
	if ((b.pc_kind == PC_KIND_HEAVY || b.pc_kind == PC_KIND_BIRD) && a.pc_kind == PC_KIND_LIGHT)
	{
		PC_HeavyVsLight (b, a);
		return TRUE;	// a (light) was destroyed
	}

	// 5. Heavy / Rob / Bird vs Heavy / Rob
	if (a.pc_kind == PC_KIND_BIRD)
	{
		PC_PopProjectile (b, oa, FALSE);
		PC_KnockBird (a, mid, 16, 65, b, ob);
		return FALSE;
	}
	if (b.pc_kind == PC_KIND_BIRD)
	{
		PC_PopProjectile (a, ob, FALSE);
		PC_KnockBird (b, mid, 16, 65, a, oa);
		return TRUE;
	}
	if (a.pc_kind >= PC_KIND_ROB && b.pc_kind >= PC_KIND_ROB)
	{
		sendParticle ("TE_GUNSHOT", mid, VEC_ORIGIN, 1, 0);
		sound (a, CHAN_AUTO, "weapons/r_exp3.wav", 0.85, ATTN_NORM);
		PC_PopProjectile (a, ob, FALSE);
		PC_PopProjectile (b, oa, FALSE);
		bprint ("^3MID-AIR INTERCEPTION! ^7", PC_Label (a), " & ", PC_Label (b), " clashed in mid-air!\n");
		return TRUE;
	}

	// 6. Light vs Light
	sendParticle ("TE_GUNSHOT", mid, VEC_ORIGIN, 1, 0);
	sound (a, CHAN_AUTO, "weapons/tink1.wav", 0.85, ATTN_NORM);
	PC_PopProjectile (a, ob, FALSE);
	PC_PopProjectile (b, oa, FALSE);
	return TRUE;
};

// ---------------------------------------------------------------- Per-Frame Swept Physics Loop

void() PC_PruneLists =
{
	local entity e, prev, nxt;

	prev = world;
	e = pc_head;
	while (e)
	{
		nxt = e.pc_next;
		if (!PC_IsAlive (e))
		{
			if (!bm_wasfreed (e))
			{
				e.pc_reg = FALSE;
				e.pc_next = world;
			}
			if (prev)
				prev.pc_next = nxt;
			else
				pc_head = nxt;
		}
		else
			prev = e;
		e = nxt;
	}

	prev = world;
	e = pc_spike_head;
	while (e)
	{
		nxt = e.pc_spike_next;
		if (bm_wasfreed (e) || e.classname != "spike" || e.solid == SOLID_NOT)
		{
			if (!bm_wasfreed (e))
			{
				e.pc_spike_reg = FALSE;
				e.pc_spike_next = world;
			}
			if (prev)
				prev.pc_spike_next = nxt;
			else
				pc_spike_head = nxt;
		}
		else
			prev = e;
		e = nxt;
	}
};

void() PC_SweepSpikes =
{
	local entity spk, nxt, e;
	local float r2;

	spk = pc_spike_head;
	while (spk)
	{
		nxt = spk.pc_spike_next;
		if (spk.owner != world && spk.owner.classname == "player" && spk.solid != SOLID_NOT)
		{
			e = pc_head;
			while (e)
			{
				if (PC_CanShootProj (e, spk.owner))
				{
					r2 = e.pc_rad * e.pc_rad;
					if (PC_SegDist2 (spk.pc_prev_org, spk.origin, PC_Center (e)) <= r2)
					{
						PC_HitProjectile (e, spk.owner, autocvar_player_nailgun, spk.origin);
						spk.solid = SOLID_NOT;
						remove (spk);
						break;
					}
				}
				e = e.pc_next;
			}
		}
		spk = nxt;
	}
};

void() PC_SweepPairs =
{
	local entity a, b;
	local vector d0, d1;
	local float r;

	a = pc_head;
	while (a)
	{
		if (PC_IsAlive (a))
		{
			if (a.pc_kind == PC_KIND_BIRD && time < a.pc_poop_t && time >= a.pc_poop_fx_t)
			{
				a.pc_poop_fx_t = time + 0.25;
				pointparticles (particleeffectnum ("dookie_drip"), PC_Center (a), '0 0 0', 3);
				sound (a, CHAN_BODY, "dookie/dk_flies.wav", 0.6, ATTN_NORM);
			}

			b = a.pc_next;
			while (b)
			{
				if (PC_CanCollidePair (a, b))
				{
					d0 = a.pc_prev_org - b.pc_prev_org;
					d1 = PC_Center (a) - PC_Center (b);
					r = a.pc_rad + b.pc_rad;
					if (PC_SegDist2 (d0, d1, '0 0 0') <= r * r)
					{
						PC_HandlePair (a, b);
						if (!PC_IsAlive (a))
							break;
					}
				}
				b = b.pc_next;
			}
		}
		a = a.pc_next;
	}
};

void() PC_Frame =
{
	local entity e;

	// Prune even while collisions are off: freed edicts are reused after 0.5 s, and re-registering one that an older
	// node still points at would close a loop that hangs the walks below once the cvar is back on (audit SC-06).
	PC_PruneLists ();
	if (!autocvar_bm_proj_collide)
		return;

	PC_SweepSpikes ();
	PC_SweepPairs ();

	e = pc_head;
	while (e)
	{
		if (PC_IsAlive (e))
			e.pc_prev_org = PC_Center (e);
		e = e.pc_next;
	}

	e = pc_spike_head;
	while (e)
	{
		if (!bm_wasfreed (e) && e.solid != SOLID_NOT)
			e.pc_prev_org = e.origin;
		e = e.pc_spike_next;
	}
};
