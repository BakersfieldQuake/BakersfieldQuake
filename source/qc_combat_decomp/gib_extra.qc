//Decompiled code. Please respect the original copyright.

float() blood_checkbounds =
{
	local vector t1start;
	local vector t1end;
	local vector t2start;
	local vector t2end;
	local vector FLRCHK;
	local vector fwd_bnds;
	local vector side_bnds;

	makevectors(self.angles);
	FLRCHK = '0 0 2';
	fwd_bnds = '23 0 0';
	side_bnds = '0 23 0';
	t1start = self.origin + fwd_bnds;
	t1end = t1start - FLRCHK;
	t2start = self.origin + side_bnds;
	t2end = t2start - FLRCHK;
	traceline(t1start, t1end, TRUE, self);
	if ((trace_fraction == 1))
	{
		return (0);
	}
	if ((trace_ent.solid != SOLID_BSP))
	{
		return (0);
	}
	t1start = self.origin + (VEC_ORIGIN - fwd_bnds);
	t1end = t1start - FLRCHK;
	traceline(t1start, t1end, TRUE, self);
	if ((trace_fraction == 1))
	{
		return (0);
	}
	if ((trace_ent.solid != SOLID_BSP))
	{
		return (0);
	}
	traceline(t2start, t2end, TRUE, self);
	if ((trace_fraction == 1))
	{
		return (0);
	}
	if ((trace_ent.solid != SOLID_BSP))
	{
		return (0);
	}
	t2start = self.origin + (VEC_ORIGIN - side_bnds);
	t2end = t2start - FLRCHK;
	traceline(t2start, t2end, TRUE, self);
	if ((trace_fraction == 1))
	{
		return (0);
	}
	if ((trace_ent.solid != SOLID_BSP))
	{
		return (0);
	}
	if (trace_inwater)
	{
		return (0);
	}
	return (TRUE);
};

void() bloodpool_remove =
{
	if ((BLOOD_POOL_CNT > 0))
	{
		BLOOD_POOL_CNT = BLOOD_POOL_CNT - 1;
	}
	remove(self);
};

void() bloodpool_grow =
{
	if ((self.flags & FL_ONGROUND))
	{
		self.alpha = 0.92;
	}
	else if ((self.frame > 20))
	{
		bloodpool_remove();
		return;
	}
	if (((self.frame < 69) && blood_checkbounds()))
	{
		self.frame = (self.frame + 1);
		self.think = bloodpool_grow;
		self.nextthink = (time + 0.1);
	}
	else
	{
		self.think = bloodpool_remove;
		self.nextthink = (time + 25);
	}
};

void() bloodpool =
{
	makevectors(self.owner.angles);
	setmodel(self, "progs/bloodpool.mdl");
	if (((self.owner.classname == "monster_shambler") || (self.owner.classname == "monster_yakman")))
	{
		self.scale = 1.1;
	}
	else
	{
		self.scale = 0.9;
	}
	self.think = bloodpool_grow;
	self.gravity = 5;
	self.solid = 0;
	self.frame = 0;
	self.angles_y = ((random() * 400) + -200);
	self.effects = EF_LOWPRECISION;
	setsize(self, VEC_ORIGIN, '1 0 0');
	self.movetype = MOVETYPE_TOSS;
	self.alpha = 0.000010;
	self.netname = "blood";
	BLOOD_POOL_CNT = BLOOD_POOL_CNT + 1;
	if ((self.owner.classname == "player"))
	{
		self.nextthink = (time + 1.8);
	}
	else
	{
		self.nextthink = (time + 1);
	}
};

void(float del) spawn_bloodpool =
{
	local entity bloodpl;

	if (((BLOOD_POOL_CNT > 4) && ((random() * 100) < 50)))
	{
		return;
	}
	if (((self.classname == "monster_afrit") && (self.grimrock_helper == 1)))
	{
		return;
	}
	bloodpl = spawn();
	bloodpl.origin = self.origin;
	bloodpl.owner = self;
	bloodpl.think = bloodpool;
	bloodpl.nextthink = (time + del);
};

void() fire_burn_out =
{
	local float pc;

	pc = pointcontents(self.origin);
	if ((cvar("gl_flashblend") == 1))
	{
		self.pflags = 3;
	}
	else
	{
		self.pflags = (((self.pflags | PFLAGS_FULLDYNAMIC) | PFLAGS_CORONA) | PFLAGS_NOSHADOW);
	}
	self.spintimer = (self.spintimer + 1);
	self.think = fire_burn_out;
	self.nextthink = (time + 0.1);
	if ((self.spintimer < 240) && (time >= self.dn3fx_fire_t) && (pc != CONTENT_WATER) && (pc != CONTENT_SLIME))
	{
		self.dn3fx_fire_t = time + 0.95;
		DN3FX_OnFire(self.origin, '0 0 18', 0.85, FALSE);
	}
	if (((pc == CONTENT_WATER) || (pc == CONTENT_SLIME) || (pc == CONTENT_LAVA)))
	{
		self.pflags = 3;
	}
	if ((self.light_lev > 20))
	{
		self.light_lev = (self.light_lev - 0.3);
	}
	if ((self.spintimer > 100))
	{
		self.traileffectnum = particleeffectnum(/*14995i*/"rocket_burn_die");
	}
	if ((self.spintimer > 145))
	{
		self.traileffectnum = particleeffectnum(/*15011i*/"rocket_burn_faint");
	}
	if ((self.spintimer > 255))
	{
		self.traileffectnum = particleeffectnum(/*15029i*/"burning_gib_fade");
	}
	if ((self.spintimer > 380))
	{
		sound(self, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
		remove(self);
	}
};

void() spawn_fire =
{
	local entity fire;

	if (bako_present)
	{
		return;
	}
	if ((coop && ((random() * 100) > 15)))
	{
		return;
	}
	if ((deathmatch && ((random() * 100) > 5)))
	{
		return;
	}
	if (((!coop || !deathmatch) && ((random() * 100) > 25)))
	{
		return;
	}
	fire = spawn();
	fire.owner = self;
	setorigin(fire, (self.origin + '0 0 2'));
	if ((pointcontents(self.origin) == CONTENT_SOLID))
	{
		setorigin(fire, (self.origin - '0 0 2'));
	}
	setmodel(fire, "progs/gib3.mdl");
	fire.movetype = MOVETYPE_TOSS;
	fire.solid = SOLID_TRIGGER;
	fire.effects = EF_LOWPRECISION;
	fire.light_lev = 140;
	fire.color = '11 3 0.2';
	fire.style = 6;
	fire.pflags = (((fire.pflags | PFLAGS_FULLDYNAMIC) | PFLAGS_CORONA) | PFLAGS_NOSHADOW);
	setsize(fire, '0 0 -2', VEC_ORIGIN);
	sound7(fire, CHAN_WEAPON, "zombie/corpse_fire.wav", 1, ATTN_NORM);
	fire.velocity = VEC_ORIGIN;
	fire.alpha = 0.01;
	fire.traileffectnum = particleeffectnum(/*15061i*/"rocket_burn");
	if ((((pointcontents(fire.origin) == CONTENT_WATER) || (pointcontents(fire.origin) == CONTENT_SLIME)) || (pointcontents(fire.origin) == CONTENT_LAVA)))
	{
		fire.traileffectnum = 0;
		fire.spintimer = 379;
	}
	else
	{
		DN3FX_OnFire(fire.origin, '0 0 24', 1.1, TRUE);
	}
	fire.think = fire_burn_out;
	fire.nextthink = time;
};

void() gibdeath_effects =
{
	if ((((self.enemy.weapon == IT_LASER_CANNON) || (self.enemy.classname == "monster_enforcer")) || (self.enemy.classname == "monster_jim")))
	{
		if (((random() * 100) > 50))
		{
			sound7(other, CHAN_VOICE, "hipweap/hipmelt2.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(other, CHAN_VOICE, "hipweap/hipmelt.wav", 1, ATTN_NORM, SNDSPD);
		}
		sendParticle("hiplas_death", self.origin, VEC_ORIGIN, 1);
	}
	else
	{
		if ((self.shocked > 0))
		{
			sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			if ((autocvar_bloodextension == 1))
			{
				sendParticle("blood_monster_gib", self.origin, VEC_ORIGIN, 1);
			}
		}
	}
};

void() burngib_end_think =
{
	self.traileffectnum = particleeffectnum(/*15169i*/"charred_gib");
	self.pflags = 3;
	if (self.light_lev > 0)
	{
		self.light_lev = 0;
		if (LIGHT_COUNT > 0)
			LIGHT_COUNT = LIGHT_COUNT - 1;
	}
	self.colormod = '0.15 0.2 0.2';
};

void() burngib_think =
{
	if ((LIGHT_COUNT < 6))
	{
		self.light_lev = 40;
		self.style = 1;
		self.color = '3 1.1 0.5';
		if ((cvar("gl_flashblend") == 1))
		{
			self.pflags = 3;
		}
		else
		{
			self.pflags = (((self.pflags | PFLAGS_FULLDYNAMIC) | PFLAGS_CORONA) | PFLAGS_NOSHADOW);
		}
	}
	self.traileffectnum = particleeffectnum(/*15029i*/"burning_gib_fade");
	self.think = burngib_end_think;
	self.nextthink = (time + 6);
	self.colormod = '0.35 0.4 0.4';
};

// Deathmatch burning gibs (audit 2026-11-26): the single-player burn-out (burngib_init) only runs outside deathmatch,
// so in deathmatch a burning gib kept its ~184 particles/s flame trail and light for its whole 30-40 s life.
// Burn for 6 s, die down for 4 s, then smoulder until the gib's normal fade, which is kept.
void() BM_DMBurnGib_Out =
{
	self.traileffectnum = particleeffectnum("charred_gib");
	self.colormod = '0.15 0.2 0.2';
	self.think = self.bm_gib_fade_fn;
	if (self.bm_gib_fade_at < 0)
		self.nextthink = -1;
	else if (self.bm_gib_fade_at > time + 0.1)
		self.nextthink = self.bm_gib_fade_at;
	else
		self.nextthink = time + 0.1;
};

void() BM_DMBurnGib_Fade =
{
	self.traileffectnum = particleeffectnum("burning_gib_fade");
	self.colormod = '0.35 0.4 0.4';
	self.think = BM_DMBurnGib_Out;
	self.nextthink = time + 4;
};

void(entity g) BM_DMBurnGib =
{
	if (!deathmatch && !coop)
		return;
	if (g.traileffectnum != particleeffectnum("burning_gib"))
		return;
	g.bm_gib_fade_fn = g.think;
	g.bm_gib_fade_at = g.nextthink;
	g.think = BM_DMBurnGib_Fade;
	g.nextthink = time + 6;
};

void() burngib_init =
{
	if ((LIGHT_COUNT < 6))
	{
		self.light_lev = 60;
		self.style = 6;
		self.color = '3.5 1.3 0.7';
		LIGHT_COUNT = LIGHT_COUNT + 1;
		if ((cvar("gl_flashblend") == 1))
		{
			self.pflags = 3;
		}
		else
		{
			self.pflags = (((self.pflags | PFLAGS_FULLDYNAMIC) | PFLAGS_CORONA) | PFLAGS_NOSHADOW);
		}
	}
	self.think = burngib_think;
	self.nextthink = (time + 14);
	self.colormod = '0.75 0.8 0.8';
	DN3FX_OnFire(self.origin, '0 0 14', 0.65, FALSE);
};

void() play_gibsound =
{
	if (coop)
	{
		spawn_stickygibs(((random() * 3) + 4));
	}
	else
	{
		spawn_stickygibs(((random() * 2) + 2));
	}
	if (((random() * 100) < 25))
	{
		sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((((random() * 100) < 50) && ((random() * 100) < 75)))
		{
			sound7(self, CHAN_VOICE, "player/udeath2.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "player/udeath.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

float(entity to, float sendFlags) sprite_sendtocsqc =
{
	WriteByte(MSG_ENTITY, ENT_SPRITE_EMITTER);
	WriteByte(MSG_ENTITY, sendFlags);
	if ((sendFlags & 1))
	{
		WriteCoord(MSG_ENTITY, self.origin_x);
		WriteCoord(MSG_ENTITY, self.origin_y);
		WriteCoord(MSG_ENTITY, self.origin_z);
		WriteCoord(MSG_ENTITY, self.velocity_x);
		WriteCoord(MSG_ENTITY, self.velocity_y);
		WriteCoord(MSG_ENTITY, self.velocity_z);
		WriteCoord(MSG_ENTITY, self.effecttype);
	}
	return (TRUE);
};

void() sprite_smoke_think =
{
	self.frame = (self.frame + 1);
	self.ltime = (self.ltime + 1);
	self.alpha = (self.alpha - 0.03);
	self.scale = (self.scale + 0.004);
	if ((self.velocity_z < 20))
	{
		self.velocity_z = (self.velocity_z + 1);
	}
	self.think = sprite_smoke_think;
	self.nextthink = (time + 0.07);
	if ((self.ltime > 61))
	{
		remove(self);
	}
};

void() clientsmoke_spawner =
{
	local entity smoke;

	smoke = spawn();
	setorigin(smoke, self.origin);
	setmodel(smoke, "progs/s_smoke_muzz.spr");
	smoke.alpha = 0.000100;
	smoke.effecttype = EFF_SMOKE;
	smoke.SendEntity = sprite_sendtocsqc;
	smoke.SendFlags = (smoke.SendFlags | 1);
	smoke.think = SUB_Remove;
	smoke.nextthink = (time + 0.1);
	self.weapontimer = 43;
	self.think = chargib_think;
	self.nextthink = (time + 0.1);
};

void() chargib_think =
{
	local entity emit;

	if (((coop || deathmatch) && !self.weapontimer))
	{
		self.think = clientsmoke_spawner;
		self.nextthink = (time + 1.4);
		return;
	}
	emit = spawn();
	emit.movetype = MOVETYPE_NOCLIP;
	emit.solid = 0;
	self.weapontimer = (self.weapontimer + 1);
	emit.velocity = (self.velocity * 0.25);
	if ((self.ltime <= 5))
	{
		self.velocity = (self.velocity * 0.2);
	}
	setmodel(emit, "progs/s_smoke_muzz.spr");
	emit.scale = 0.3;
	emit.alpha = 0.8;
	emit.origin = self.origin;
	emit.frame = ((random() * 2) + 0);
	emit.velocity_x = (emit.velocity_x + ((random() * 0) + -5));
	emit.velocity_y = (emit.velocity_y + ((random() * 10) + -5));
	emit.velocity_z = (emit.velocity_z + ((random() * 10) + -5));
	emit.think = sprite_smoke_think;
	emit.nextthink = (time + 0.1);
	if ((self.weapontimer > 43))
	{
		if ((autocvar_gibsduration == 0))
		{
			self.think = chargib_think;
			self.nextthink = -1;
		}
		else
		{
			self.think = chargib_think;
			self.nextthink = (time + autocvar_gibsduration);
		}
	}
	else
	{
		self.think = chargib_think;
		self.nextthink = (time + ((random() * 0.5) + 0.2));
	}
};

void() gibs_rest =
{
	self.touch = SUB_Null;
	self.think = SUB_Remove;
	self.nextthink = ((time + 15) + (random() * 5));
};

void() gibs_think =
{
	self.velocity = VEC_ORIGIN;
	self.movetype = MOVETYPE_BOUNCE;
	self.think = gibs_rest;
	self.nextthink = (time + 8);
};

void() gibs_touch =
{
	if ((pointcontents((self.origin + '0 0 3')) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	if ((other.solid != SOLID_BSP))
	{
		return;
	}
	if ((self.waitmin > time))
	{
		return;
	}
	self.waitmin = ((time + 0.1) + (random() * 1));
	if ((self.velocity_x < 100))
	{
		if (((random() * 100) > 50))
		{
			sound(self, CHAN_ITEM, "gib/gibhit1.wav", 1, ATTN_NORM);
		}
		else
		{
			sound(self, CHAN_ITEM, "gib/gibhit6.wav", 1, ATTN_NORM);
		}
	}
	SpawnBlood(self.origin, '-10 -10 20', 5);
	if ((self.movetype == MOVETYPE_TOSS))
	{
		sendParticle("hldecal", self.origin, '0 0 100', 2);
		self.movetype = 0;
		self.cnt = 0;
	}
	if ((self.movetype == MOVETYPE_BOUNCE))
	{
		self.cnt = (self.cnt + 1);
	}
};

void() GibSticky =
{
	local entity dripper;
	local vector throwdir;

	throwdir_x = (((random() * 260) + -130) * (0 - self.health)) / 25;
	dripper = spawn();
	setorigin(dripper, self.origin);
	setmodel(dripper, "progs/gib_4.mdl");
	setsize(dripper, VEC_ORIGIN, VEC_ORIGIN);
	dripper.velocity = throwdir;
	dripper.avelocity_x = ((random() * 800) + -400);
	dripper.avelocity_y = ((random() * 800) + -400);
	dripper.avelocity_z = ((random() * 800) + -400);
	if (((random() * 100) < 60))
	{
		dripper.movetype = MOVETYPE_TOSS;
	}
	else
	{
		dripper.movetype = MOVETYPE_BOUNCE;
	}
	dripper.solid = SOLID_TRIGGER;
	dripper.touch = gibs_touch;
	dripper.think = gibs_think;
	dripper.nextthink = (time + ((random() * 3) + 2));
	dripper.netname = "stickygib";
};

void(float amount) spawn_stickygibs =
{
	if ((self.cnt < 0))
	{
		self.cnt = 0;
	}
	while ((self.cnt <= amount))
	{
		GibSticky();
		self.cnt = (self.cnt + 1);
	}
};
