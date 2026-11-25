//Decompiled code. Please respect the original copyright.

float(entity targ, entity inflictor) CanDamage =
{
	if ((targ.movetype == MOVETYPE_PUSH))
	{
		traceline(inflictor.origin, (0.5 * (targ.absmin + targ.absmax)), TRUE, self);
		if ((trace_fraction == 1))
		{
			return (TRUE);
		}
		if ((trace_ent == targ))
		{
			return (TRUE);
		}
		return (0);
	}
	traceline(inflictor.origin, targ.origin, TRUE, self);
	if ((trace_fraction == 1))
	{
		return (TRUE);
	}
	traceline(inflictor.origin, (targ.origin + '15 15 0'), TRUE, self);
	if ((trace_fraction == 1))
	{
		return (TRUE);
	}
	traceline(inflictor.origin, (targ.origin + '-15 -15 0'), TRUE, self);
	if ((trace_fraction == 1))
	{
		return (TRUE);
	}
	traceline(inflictor.origin, (targ.origin + '-15 15 0'), TRUE, self);
	if ((trace_fraction == 1))
	{
		return (TRUE);
	}
	traceline(inflictor.origin, (targ.origin + '15 -15 0'), TRUE, self);
	if ((trace_fraction == 1))
	{
		return (TRUE);
	}
	return (0);
};

void(entity targ, entity attacker) Killed =
{
	local entity oself;

	oself = self;
	self = targ;
	if ((self.health < -99))
	{
		self.health = -99;
	}
	if ((((self.movetype == MOVETYPE_PUSH) || (self.movetype == MOVETYPE_NONE)) && (self.classname != "player")))	// BM: a Rob Dob pilot / driver / rider is parked with MOVETYPE_NONE; this door shortcut skipped his obituary, so the killer got no frag
	{
		self.th_die();
		self = oself;
		return;
	}
	Underdog_Killed(targ, attacker);
	if (((targ.classname == "player") || (targ.flags & FL_MONSTER)))
		BM_Radar_Ping(targ, targ.origin, BM_RPK_KILL);
	self.enemy = attacker;
	if ((self.flags & FL_MONSTER))
	{
		killed_monsters = killed_monsters + 1;
		WriteByte(MSG_ALL, SVC_KILLEDMONSTER);
	}
	ClientObituary(self, attacker);
	self.takedamage = 0;
	self.touch = SUB_Null;
	monster_death_use();
	self.th_die();
	self = oself;
};

void(entity targ, entity inflictor, entity attacker, float damage) T_Damage =
{
	local vector dir;
	local entity oldself;
	local float save;
	local float take;

	if (!targ.takedamage)
	{
		return;
	}
	if ((inflictor != world) && (inflictor.pc_blast_ignore == targ))
	{
		return;
	}
	if ((targ.jb_vehicle != world))
	{
		if (((inflictor != world) && (targ.jb_vehicle.jb_last_inflictor == inflictor)) && (targ.jb_vehicle.jb_last_inflictor_t == time))
		{
			return;
		}
		// the bird branch below records the inflictor (setting it here would make the bird skip this hit)
		T_Damage(targ.jb_vehicle, inflictor, attacker, damage);
		return;
	}
	if ((targ.rr_vehicle != world))
	{
		if (((inflictor != world) && (targ.rr_vehicle.rr_last_inflictor == inflictor)) && (targ.rr_vehicle.rr_last_inflictor_t == time))
		{
			return;
		}
		T_Damage(targ.rr_vehicle, inflictor, attacker, damage);
		return;
	}
	if (((targ.veh_van != world) && (targ.veh_van.veh_state != VEH_STATE_WRECK)))
	{
		// Vehicle cab shields the driver from hull-piercing splash: route external damage to the vehicle hull!
		if ((targ.veh_van.veh_driver == targ))
		{
			T_Damage(targ.veh_van, inflictor, attacker, damage);
			return;
		}
	}
	if (((targ.mmt_tank != world) && (targ.mmt_tank.mmt_state != MMT_STATE_WRECK) && (inflictor.classname != "mm_tank_blast")))
	{
		// Mega Man Tank hull absorbs external fire for its driver until destroyed
		if ((targ.mmt_tank.mmt_driver == targ))
		{
			T_Damage(targ.mmt_tank, inflictor, attacker, damage);
			return;
		}
	}
	if (((targ.classname == "misc_mm_tank") && (inflictor != world) && (inflictor != attacker)))
	{
		if (((targ.mmt_blast_infl == inflictor) && (targ.mmt_blast_t == time)))
		{
			return;
		}
		targ.mmt_blast_infl = inflictor;
		targ.mmt_blast_t = time;
	}
	if (((targ.classname == "player") && (time < targ.veh_bail_safe_t) && ((inflictor == targ.veh_last_van) || (inflictor.classname == "veh_blast_inflictor"))))
	{
		return;
	}
	if (((targ.veh_ride != world) && (targ.veh_ride.veh_state != VEH_STATE_WRECK)))
	{
		// Drive-by party passengers take half external damage while riding!
		if (((inflictor != world) && (attacker != targ)))
		{
			damage = (damage * 0.5);
		}
	}
	if (((targ.veh_kind > 0) && (attacker.classname == "player") && (attacker.veh_ride == targ)))
	{
		// Passengers firing out of a vehicle never damage their own ride's hull!
		return;
	}
	if ((targ.classname == "veh_van_clip"))
	{
		// a walk-in van's 12 solid clip boxes: the hit goes to the van itself (its armor, quad, pain and death rules)
		if (((targ.owner == world) || (targ.owner.veh_state == VEH_STATE_WRECK)))
		{
			return;
		}
		T_Damage(targ.owner, inflictor, attacker, damage);
		return;
	}
	if ((targ.veh_kind && (inflictor != world) && (inflictor != attacker)))
	{
		// one blast (or one ramming van) hits a vehicle once, not once per clip box inside the radius (6-10 times)
		if (((targ.veh_blast_infl == inflictor) && (targ.veh_blast_t == time)))
		{
			return;
		}
		targ.veh_blast_infl = inflictor;
		targ.veh_blast_t = time;
	}
	if (((targ.classname == "wt_part_tank") || (targ.classname == "wt_part_catwalk") || (targ.classname == "wt_part_legs")))
	{
		local vector _wt_hit;
		if ((inflictor != world))
		{
			_wt_hit = inflictor.origin;
		}
		else
		{
			_wt_hit = ((targ.absmin + targ.absmax) * 0.5);
		}
		Spruce_TowerHit(targ, _wt_hit, inflictor, attacker, damage);
		return;
	}
	if ((targ.bako_group > 0) || (targ.classname == "func_breakable"))
	{
		if ((inflictor.classname == "teledeath") || (inflictor.classname == "teledeath2")
			|| (attacker.classname == "teledeath") || (attacker.classname == "teledeath2")
			|| (damage >= 40000))
			return;
	}
	if ((targ.bako_group >= BAKO_GRP_FOX && targ.bako_group <= BAKO_GRP_SIGN))
	{
		local vector _bk_hit;
		if ((inflictor != world) && (inflictor != attacker))
			_bk_hit = inflictor.origin;
		else if ((trace_ent == targ))
			_bk_hit = trace_endpos;
		else
			_bk_hit = ((targ.absmin + targ.absmax) * 0.5);
		BakoDestruct_OnDamage(targ, _bk_hit, inflictor, attacker, damage);
		return;
	}
	if ((targ.classname == "misc_vehicle_johnbird"))
	{
		if (((attacker != world) && (attacker == targ.jb_pilot)))
		{
			return;
		}
		// one splash hits the bird once, whether findradius reaches it through the SOLID_NOT pilot or directly
		if ((((inflictor != world) && (inflictor != attacker)) && ((targ.jb_last_inflictor == inflictor) && (targ.jb_last_inflictor_t == time))))
		{
			return;
		}
		targ.jb_last_inflictor = inflictor;
		targ.jb_last_inflictor_t = time;
	}
	if ((targ.classname == "misc_vehicle_rocketrider"))
	{
		if (((attacker != world) && (attacker == targ.rr_pilot)))
		{
			return;
		}
		if ((((inflictor != world) && (inflictor != attacker)) && ((targ.rr_last_inflictor == inflictor) && (targ.rr_last_inflictor_t == time))))
		{
			return;
		}
		targ.rr_last_inflictor = inflictor;
		targ.rr_last_inflictor_t = time;
	}
	damage_attacker = attacker;
	if ((attacker.super_damage_finished > time))
	{
		damage = damage * 4;
	}
	damage = Underdog_Damage(targ, attacker, damage);
	damage = BM_Damage(targ, inflictor, attacker, damage);	// spawn protection, less self-damage
	damage = Milky_Damage(targ, inflictor, attacker, damage);	// the Pink Lady keeps her own hit points (milky.qc)
	if ((targ.veh_kind == VEH_FORELOCO))
	{
		damage = max(1, (damage * 0.25));
	}
	if ((targ.classname == "misc_vehicle_johnbird"))
	{
		if ((((inflictor.classname == "missile") || (inflictor.classname == "grenade")) && (damage >= 75)))
		{
			if ((attacker.super_damage_finished > time))
			{
				damage = 400;
			}
			else
			{
				damage = 100;	// exact 5-rocket shootdown (500 HP / 100 = 5 rockets)
			}
		}
	}
	save = ceil((targ.armortype * damage));
	if ((save >= targ.armorvalue))
	{
		save = targ.armorvalue;
		targ.armortype = 0;
		targ.items = (targ.items - (targ.items & 57344));
	}
	targ.armorvalue = (targ.armorvalue - save);
	take = ceil((damage - save));
	if ((targ.flags & FL_CLIENT))
	{
		targ.dmg_take = (targ.dmg_take + take);
		targ.dmg_save = (targ.dmg_save + save);
		targ.dmg_inflictor = inflictor;
	}
	if (((inflictor != world) && (targ.movetype == MOVETYPE_WALK)) && !(targ.veh_kind == VEH_FORELOCO && targ.invincible_finished >= time))
	{
		if (((fg_inflicting == FG_GARAND) && (bm_kb > 20)))
		{
			bm_kb = 20;
		}
		if (((attacker.classname == "player") && (attacker.weapon == IT_SHOTGUN) && (targ != attacker) && !(targ.flags & FL_ONGROUND)))
		{
			bm_kb = (bm_kb * 1.65);		// anti-air skeet-shooter knockback on airborne / jetpacking players
		}
		dir = targ.origin - ((inflictor.absmin + inflictor.absmax) * 0.5);
		dir = normalize(dir);
		targ.velocity = (targ.velocity + ((dir * bm_kb) * 8));	// full push, even when the damage was scaled down
	}
	if (bm_blocked)
	{
		return;	// spawn protection soaked it up
	}
	if ((targ.flags & FL_GODMODE))
	{
		return;
	}
	if ((targ.invincible_finished >= time))
	{
		if ((targ.invincible_sound < time))	// throttle per target, not per attacker
		{
			sound(targ, CHAN_ITEM, "items/protect3.wav", 1, ATTN_NORM);
			targ.invincible_sound = (time + 2);
		}
		return;
	}
	if (((((teamplay == 1) || CTF_ENABLED) && (targ.team > 0)) && (targ.team == attacker.team) && (targ != attacker)))
	{
		return;
	}
	if ((take > 0) && (targ.classname == "player"))
	{
		targ.rg_hurt_t = time;	// regenerating health waits for this
		if ((targ.fd_head != world) && (targ.ishuman == 1) && (time >= targ.fd_warn_t))
		{
			targ.fd_warn_t = (time + 1.0);
			sound(targ, CHAN_AUTO, "misc/talk.wav", 1, ATTN_NORM);
			centerprint(targ, "^1WARNING: YOUR BODY IS BEING SHOT! Press H to recall!\n");
		}
	}
	if (!targ.in_cocoon_shape)
	{
		targ.health = (targ.health - take);
		if ((targ.classname == "monster_zombie"))
		{
			targ.painskin_helper = 1;
		}
		HitSound_Play(targ, attacker, take);
	}
	if ((targ.health <= 0))
	{
		targ.grimrock_helper = -1;
		if (((autocvar_quadreplacer > 0) && (random() < 0.175)))
		{
			targ.grimrock_helper = 1;
			if (((random() < 0.1) && ((targ.classname == "monster_shalrath") || (targ.classname == "monster_afrit"))))
			{
				targ.grimrock_helper = -1;
			}
			else
			{
				if (((random() < 0.2) && (((targ.classname == "monster_knight") || (targ.classname == "monster_wizard")) || (targ.classname == "monster_shambler"))))
				{
					targ.grimrock_helper = -1;
				}
			}
			if ((attacker.meleeing && (random() < 0.35)))
			{
				targ.grimrock_helper = -1;
			}
		}
		Killed(targ, attacker);
		return;
	}
	oldself = self;
	self = targ;
	if (((self.classname == "monster_reiver") && (attacker != world)))
	{
		if (((self != attacker) && (attacker != self.enemy)))
		{
			if ((self.enemy.classname == "player"))
			{
				self.oldenemy = self.enemy;
			}
			if ((attacker.classname == "player"))
			{
				self.enemy = attacker;
				FoundTarget();
			}
		}
	}
	else
	{
		if (((self.flags & FL_MONSTER) && (attacker != world)))
		{
			if (((self != attacker) && (attacker != self.enemy)))
			{
				if ((((self.classname != attacker.classname) || (self.classname == "monster_army")) && (((attacker.classname != "monster_afrit") && (self.classname != "monster_afrit")) || ((attacker.classname == "player") && (self.classname == "monster_afrit")))))
				{
					if (((((self.classname != "monster_voreling") && (attacker.classname != "monster_shalrath")) || (self.classname != "monster_voreling")) && (attacker.classname != "monster_shalrath_boss")))
					{
						if ((((attacker.classname != "player") && (skill == 3)) && (random() < 0.75)))
						{
						}
						else
						{
							if ((((attacker.classname == "monster_hell_knight2") || ((self.classname == "monster_hell_knight2") && (attacker.classname != "player"))) && (random() < 0.95)))
							{
							}
							else
							{
								if ((self.enemy.classname == "player"))
								{
									self.oldenemy = self.enemy;
								}
								self.enemy = attacker;
								FoundTarget();
							}
						}
					}
				}
			}
		}
	}
	if (self.th_pain)
	{
		if (((random() > (autocvar_monster_skip_pain_animation_chance * 0.01)) || (self.classname == "player") || (self.classname == "npc_soi6")))
		{
			self.th_pain(attacker, take);
			if (((skill == 3) && (self.classname != "player")))
			{
				self.pain_finished = (time + 5);
			}
		}
	}
	self = oldself;
};

void(entity inflictor, entity attacker, float damage) T_EELZap =
{
	local float points;
	local entity head;
	local vector org;

	head = findradius(inflictor.origin, (damage + 40));
	while (head)
	{
		if (head.takedamage)
		{
			org = head.origin + ((head.mins + head.maxs) * 0.5);
			points = 0.5 * vlen((inflictor.origin - org));
			if ((points < 0))
			{
				points = 0;
			}
			points = damage - points;
			if ((head == attacker))
			{
				points = points * 0.5;
			}
			if ((points > 0))
			{
				if (CanDamage(head, inflictor))
				{
					if (((head.classname != "monster_eel") && (head.flags & FL_INWATER)))
					{
						T_Damage(head, inflictor, attacker, points);
					}
				}
			}
		}
		head = head.chain;
	}
};

void(entity inflictor, entity attacker, float damage, entity ignore) T_RadiusDamage =
{
	local float points;
	local float radboost;
	local entity head;
	local vector org;
	local entity explo;

	if (damage >= 25)
		BM_Radar_Ping(attacker, inflictor.origin, BM_RPK_BLAST);

	explo = Gyro_Force_Create("explosion", inflictor.origin);
	Gyro_Force_ApplyFalloff_AreaQuadratic(explo, ('4 4 4' * damage));
	Gyro_Force_ApplyAffector_Point(explo, '0 0 -24', '1 1 1', (damage * 6.25), FALSE);
	Gyro_Force_AddProperty_Instant(explo);
	Gyro_Force_AddProperty_AirOnly(explo);
	explo = Gyro_Force_Create("explosion", inflictor.origin);
	Gyro_Force_ApplyFalloff_AreaLinear(explo, ('2 2 2' * damage));
	Gyro_Force_ApplyAffector_Point(explo, '0 0 -24', '1 1 1', (damage * 3), FALSE);
	Gyro_Force_AddProperty_Instant(explo);
	Gyro_Force_AddProperty_WaterOnly(explo);
	if ((damage < 50))
	{
		radboost = damage * 0.65;
		if ((attacker.classname == "monster_reiver"))
		{
			radboost = radboost + 10;
		}
		if ((autocvar_quadreplacer > 0))
		{
			radboost = radboost + 20;
		}
	}
	head = findradius(inflictor.origin, ((damage + 40) + radboost));
	while (head)
	{
		if ((head != ignore))
		{
			if (head.takedamage && (head.bako_group == 0))
			{
				if ((inflictor.deathtype == "exploding"))
				{
					head.sticky = 1;
				}
				org = head.origin + ((head.mins + head.maxs) * 0.5);
				if ((damage < 50))
				{
					points = 0.25 * vlen((inflictor.origin - org));
				}
				else
				{
					points = 0.5 * vlen((inflictor.origin - org));
				}
				if ((points < 0))
				{
					points = 0;
				}
				points = damage - points;
				if ((head == attacker))
				{
					points = points * 0.5;
				}
				if ((points > 0))
				{
					if ((self.owner.classname == "monster_oldone_tentacle"))
					{
						if ((head.classname == "monster_oldone_tentacle"))
						{
							return;
						}
					}
					if (CanDamage(head, inflictor))
					{
						if (((head.classname == "monster_shambler") || (head.classname == "monster_hell_knight2")))
						{
							T_Damage(head, inflictor, attacker, (points * 0.65));
						}
						else
						{
							T_Damage(head, inflictor, attacker, points);
						}
					}
				}
			}
		}
		head = head.chain;
	}
	BakoDestruct_RadiusSplash(inflictor.origin, ((damage + 40) + radboost), damage, inflictor, attacker, FALSE);
};

void(entity attacker, float damage) T_BeamDamage =
{
	local float points;
	local entity head;

	head = findradius(attacker.origin, (damage + 40));
	while (head)
	{
		if (head.takedamage)
		{
			points = 0.5 * vlen((attacker.origin - head.origin));
			if ((points < 0))
			{
				points = 0;
			}
			points = damage - points;
			if ((head == attacker))
			{
				points = points * 0.5;
			}
			if ((points > 0))
			{
				if (CanDamage(head, attacker))
				{
					if (((head.classname == "monster_shambler") || (head.classname == "monster_hell_knight2")))
					{
						T_Damage(head, attacker, attacker, (points * 0.7));
					}
					else
					{
						T_Damage(head, attacker, attacker, points);
					}
				}
			}
		}
		head = head.chain;
	}
};

void(entity org) Bleeding1 =
{
	if ((org.velocity == '0 1 1'))
	{
		return;
	}
	particleeffectnum(/*19698i*/"TE_BLEED1");
	pointparticles(particleeffectnum(/*19698i*/"TE_BLEED1"), ((org.origin + org.view_ofs) + (v_up * -20)), (org.velocity * 0.7), 1);
};

void(entity org) Bleeding2 =
{
	if ((org.velocity == '0 1 1'))
	{
		return;
	}
	particleeffectnum(/*19708i*/"TE_BLEED2");
	pointparticles(particleeffectnum(/*19708i*/"TE_BLEED2"), ((org.origin + org.view_ofs) + (v_up * -20)), (org.velocity * 0.7), 1);
};

void(entity org) Bleedingnull =
{
	pointparticles(particleeffectnum(/*19718i*/"TE_BLEEDNULL"), org.origin, VEC_ORIGIN, 1);
};
