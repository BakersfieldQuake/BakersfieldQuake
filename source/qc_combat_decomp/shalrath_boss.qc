//Decompiled code. Please respect the original copyright.

void() ring_grow1 = [ 0, ring_grow2 ]
{
};

void() ring_grow2 = [ 1, ring_grow3 ]
{
};

void() ring_grow3 = [ 2, ring_grow4 ]
{
};

void() ring_grow4 = [ 3, ring_grow5 ]
{
};

void() ring_grow5 = [ 4, ring_grow6 ]
{
};

void() ring_grow6 = [ 5, ring_grow7 ]
{
};

void() ring_grow7 = [ 6, SUB_Remove ]
{
};

void() shal_boss_stand = [ 23, shal_boss_stand ]
{
	ai_stand();
};

void() shal_boss_walk1 = [ 24, shal_boss_walk2 ]
{
	if ((random() < 0.2))
	{
		sound(self, CHAN_VOICE, "shalrath/idle.wav", 1, ATTN_IDLE);
	}
	ai_walk(6);
};

void() shal_boss_walk2 = [ 25, shal_boss_walk3 ]
{
	ai_walk(4);
};

void() shal_boss_walk3 = [ 26, shal_boss_walk4 ]
{
	ai_walk(0);
};

void() shal_boss_walk4 = [ 27, shal_boss_walk5 ]
{
	ai_walk(0);
};

void() shal_boss_walk5 = [ 28, shal_boss_walk6 ]
{
	ai_walk(0);
};

void() shal_boss_walk6 = [ 29, shal_boss_walk7 ]
{
	ai_walk(0);
};

void() shal_boss_walk7 = [ 30, shal_boss_walk8 ]
{
	ai_walk(5);
};

void() shal_boss_walk8 = [ 31, shal_boss_walk9 ]
{
	ai_walk(6);
};

void() shal_boss_walk9 = [ 32, shal_boss_walk10 ]
{
	ai_walk(5);
};

void() shal_boss_walk10 = [ 33, shal_boss_walk11 ]
{
	ai_walk(0);
};

void() shal_boss_walk11 = [ 34, shal_boss_walk12 ]
{
	ai_walk(4);
};

void() shal_boss_walk12 = [ 23, shal_boss_walk1 ]
{
	ai_walk(5);
};

void() shal_boss_run1 = [ 24, shal_boss_run2 ]
{
	if ((random() < 0.2))
	{
		sound(self, CHAN_VOICE, "shalrath/idle.wav", 1, ATTN_IDLE);
	}
	ai_run(6);
};

void() shal_boss_run2 = [ 25, shal_boss_run3 ]
{
	ai_run(14);
};

void() shal_boss_run3 = [ 26, shal_boss_run4 ]
{
	ai_run(0);
	shambler_walking_quake();
};

void() shal_boss_run4 = [ 27, shal_boss_run5 ]
{
	ai_run(0);
};

void() shal_boss_run5 = [ 28, shal_boss_run6 ]
{
	ai_run(0);
};

void() shal_boss_run6 = [ 29, shal_boss_run7 ]
{
	ai_run(0);
	shambler_walking_quake();
};

void() shal_boss_run7 = [ 30, shal_boss_run8 ]
{
	ai_run(15);
	if (((self.health < 1800) && (random() < 0.4)))
	{
		shal_boss_attack1();
	}
};

void() shal_boss_run8 = [ 31, shal_boss_run9 ]
{
	ai_run(16);
};

void() shal_boss_run9 = [ 32, shal_boss_run10 ]
{
	ai_run(15);
	shambler_walking_quake();
};

void() shal_boss_run10 = [ 33, shal_boss_run11 ]
{
	ai_run(0);
};

void() shal_boss_run11 = [ 34, shal_boss_run12 ]
{
	ai_run(14);
};

void() shal_boss_run12 = [ 23, shal_boss_run1 ]
{
	ai_run(15);
};

void() shal_boss_jump1 = [ 10, shal_boss_jump2 ]
{
	ai_face();
};

void() shal_boss_jump2 = [ 9, shal_boss_jump3 ]
{
	ai_face();
	shambler_walking_quake();
};

void() shal_boss_jump3 = [ 8, shal_boss_jump4 ]
{
	ai_face();
};

void() shal_boss_jump4 = [ 3, shal_boss_jump5 ]
{
	ai_face();
	sound(self, CHAN_VOICE, "shalrath/death.wav", 1, ATTN_NORM);
};

void() shal_boss_jump5 = [ 2, shal_boss_jump6 ]
{
	ai_face();
	self.enemy.punchangle_x = -2;
	self.velocity = '0 0 500';
};

void() shal_boss_jump6 = [ 1, shal_boss_jump7 ]
{
	ai_face();
};

void() shal_boss_jump7 = [ 0, shal_boss_jump8 ]
{
	ai_face();
};

void() shal_boss_jump8 = [ 52, shal_boss_jump9 ]
{
	ai_face();
};

void() shal_boss_jump9 = [ 51, shal_boss_jump10 ]
{
	ai_face();
};

void() shal_boss_jump10 = [ 52, shal_boss_jump11 ]
{
	ai_face();
};

void() shal_boss_jump11 = [ 51, shal_boss_jump12 ]
{
	ai_face();
};

void() shal_boss_jump12 = [ 52, shal_boss_jump13 ]
{
	ai_face();
};

void() shal_boss_jump13 = [ 51, shal_boss_jump14 ]
{
	ai_face();
};

void() shal_boss_jump14 = [ 52, shal_boss_jump15 ]
{
	ai_face();
};

void() shal_boss_jump15 = [ 51, shal_boss_jump16 ]
{
	ai_face();
	ShalBossNova();
};

void() shal_boss_jump16 = [ 52, shal_boss_run1 ]
{
	ai_face();
	self.enemy.punchangle_y = -8;
};

void() shal_boss_attack1 = [ 0, shal_boss_attack2 ]
{
	if ((((self.health < (2000 + (skill * 200))) && (random() < 0.1)) && (enemy_range == RANGE_NEAR)))
	{
		shal_boss_jump1();
	}
	sound(self, CHAN_VOICE, "shalrath/bossattack.wav", 1, ATTN_NORM);
	ai_face();
};

void() shal_boss_attack2 = [ 1, shal_boss_attack3 ]
{
	ai_face();
};

void() shal_boss_attack3 = [ 2, shal_boss_attack4 ]
{
	ai_face();
};

void() shal_boss_attack4 = [ 3, shal_boss_attack5 ]
{
	ai_face();
};

void() shal_boss_attack5 = [ 4, shal_boss_attack6 ]
{
	ai_face();
};

void() shal_boss_attack6 = [ 5, shal_boss_attack7 ]
{
	ai_face();
	if ((random() < 0.4))
	{
		ShalBossGrenade();
	}
};

void() shal_boss_attack7 = [ 6, shal_boss_attack8 ]
{
	ai_face();
	if ((self.health < 2500))
	{
		ShalBossGrenade();
	}
};

void() shal_boss_attack8 = [ 7, shal_boss_attack9 ]
{
	ai_face();
	if ((self.health < 1000))
	{
		ShalBossGrenade();
	}
	shal_boss_spawner();
};

void() shal_boss_attack9 = [ 8, shal_boss_attack10 ]
{
	if ((random() < 0.2))
	{
		ShalBossMissile();
	}
	else
	{
		if (((random() > 0.2) && (random() < 0.4)))
		{
			shal_boss_spawner();
		}
		else
		{
			ShalBossGrenade();
			ShalBossGrenade();
			ShalBossGrenade();
		}
	}
};

void() shal_boss_attack10 = [ 9, shal_boss_attack11 ]
{
	ai_face();
	if ((self.health < 1900))
	{
		ShalBossGrenade();
	}
};

void() shal_boss_attack11 = [ 10, shal_boss_run1 ]
{
};

void() shal_boss_pain1 = [ 11, shal_boss_pain2 ]
{
};

void() shal_boss_pain2 = [ 12, shal_boss_pain3 ]
{
};

void() shal_boss_pain3 = [ 13, shal_boss_pain4 ]
{
};

void() shal_boss_pain4 = [ 14, shal_boss_pain5 ]
{
};

void() shal_boss_pain5 = [ 15, shal_boss_run1 ]
{
};

void() Shal_Gib =
{
	ThrowGib("progs/gib_shalclawb.mdl", (self.health * 3));
	ThrowGib("progs/gib_shalclawb.mdl", (self.health * 3));
	ThrowGib("progs/h_shalboss.mdl", (self.health * 3));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib1.mdl", (self.health * 7));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib1.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 7));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib1.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 7));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib1.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 7));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib3.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 7));
	ThrowGib("progs/gib2.mdl", (self.health * 4));
	ThrowGib("progs/gib3.mdl", (self.health * 4));
	ThrowGib("progs/gib3.mdl", (self.health * 4));
	ThrowGib("progs/gib3.mdl", (self.health * 4));
	ThrowGib("progs/gib2.mdl", (self.health * 10));
	ThrowGib("progs/gib2.mdl", (self.health * 10));
	ThrowGib("progs/gib2.mdl", (self.health * 4));
	sendParticle("blood_monster_gib", self.origin, VEC_ORIGIN, 1);
	play_gibsound();
};

void() shal_boss_death1 = [ 35, shal_boss_death2 ]
{
	sound(self, CHAN_VOICE, "shalrath/pain.wav", 1, ATTN_NORM);
};

void() shal_boss_death2 = [ 36, shal_boss_death3 ]
{
};

void() shal_boss_death3 = [ 37, shal_boss_death4 ]
{
};

void() shal_boss_death4 = [ 38, shal_boss_death5 ]
{
};

void() shal_boss_death5 = [ 39, shal_boss_death6 ]
{
	sound(self, CHAN_VOICE, "shalrath/death.wav", 1, ATTN_NORM);
};

void() shal_boss_death6 = [ 40, shal_boss_death7 ]
{
};

void() shal_boss_death7 = [ 41, shal_boss_death8 ]
{
};

void() shal_boss_death8 = [ 42, shal_boss_death9 ]
{
	sound(self, CHAN_VOICE, "shalrath/death.wav", 1, ATTN_NORM);
};

void() shal_boss_death9 = [ 43, shal_boss_death10 ]
{
};

void() shal_boss_death10 = [ 44, shal_boss_death11 ]
{
};

void() shal_boss_death11 = [ 45, shal_boss_death12 ]
{
	sound(self, CHAN_VOICE, "shalrath/pain.wav", 1, ATTN_NORM);
};

void() shal_boss_death12 = [ 46, shal_boss_death13 ]
{
};

void() shal_boss_death13 = [ 47, shal_boss_death14 ]
{
	sound(self, CHAN_VOICE, "shalrath/death.wav", 1, ATTN_NORM);
};

void() shal_boss_death14 = [ 48, shal_boss_death15 ]
{
};

void() shal_boss_death15 = [ 49, shal_boss_death16 ]
{
};

void() shal_boss_death16 = [ 50, shal_boss_death17 ]
{
	Shal_Gib();
	setmodel(self, "progs/shalrath_death.mdl");
	setsize(self, '-46 -40 -24', '46 40 100');
};

void() shal_boss_death17 = [ 16, shal_boss_death18 ]
{
};

void() shal_boss_death18 = [ 17, shal_boss_death19 ]
{
};

void() shal_boss_death19 = [ 18, shal_boss_death20 ]
{
};

void() shal_boss_death20 = [ 19, shal_boss_death21 ]
{
};

void() shal_boss_death21 = [ 20, shal_boss_death22 ]
{
};

void() shal_boss_death22 = [ 21, shal_boss_death23 ]
{
};

void() shal_boss_death23 = [ 22, shal_boss_death23 ]
{
	CopyMonsterToBodyQue(8, "progs/gib_shalleg_b.mdl");
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
};

void() shalrath_boss_pain =
{
	if ((self.pain_finished > time))
	{
		return;
	}
	sound(self, CHAN_VOICE, "shalrath/pain.wav", 1, ATTN_NORM);
	if (((random() < 0.1) && (enemy_range == RANGE_MID)))
	{
		shal_boss_jump1();
	}
	else
	{
		shal_boss_pain1();
	}
	self.pain_finished = (time + 3);
};

void() shalrath_boss_die =
{
	sound(self, CHAN_VOICE, "shalrath/death.wav", 1, ATTN_NORM);
	shal_boss_death1();
	self.solid = 0;
};

void() ShalBossMissile =
{
	local entity missile;
	local vector dir;
	local float dist;
	local float flytime;

	dir = normalize(((self.enemy.origin + '0 0 10') - self.origin));
	dist = vlen((self.enemy.origin - self.origin));
	flytime = dist * 0.002;
	if ((flytime < 0.1))
	{
		flytime = 0.1;
	}
	self.effects = (self.effects | EF_MUZZLEFLASH);
	sound(self, CHAN_WEAPON, "shalrath/bossattack2.wav", 1, ATTN_NORM);
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_FLYMISSILE;
	setmodel(missile, "progs/v_spike.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.origin = (self.origin + '0 0 60');
	missile.velocity = (dir * 400);
	missile.avelocity = '300 300 300';
	missile.nextthink = (flytime + time);
	missile.think = ShalBossHome;
	missile.enemy = self.enemy;
	missile.touch = ShalBossMissileTouch;
};

void() ShalBossStomp =
{
	shal_boss_jump1();
};

void() ShalBossGrenade =
{
	local vector distancedelta;
	local vector nozdistancedelta;
	local vector vec;
	local vector dst;
	local vector follow;
	local entity missile;

	makevectors(self.enemy.angles);
	follow = self.enemy.velocity * 3.3;
	dst = (self.enemy.origin + follow) - (13 * self.movedir);
	vec = normalize((dst - self.origin));
	self.effects = (self.effects | EF_MUZZLEFLASH);
	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	makevectors(self.angles);
	sound(self, CHAN_WEAPON, "shalrath/voregren.wav", 1, ATTN_NORM);
	sound(self, CHAN_ITEM, "shalrath/voretick.wav", 1, ATTN_NORM);
	distancedelta = self.enemy.origin - self.origin;
	nozdistancedelta = distancedelta;
	missile.velocity = normalize(distancedelta);
	missile.velocity = ((vec * 350) + (v_right * (random() * 100)));
	if ((random() < 0.5))
	{
		missile.velocity = (missile.velocity * (0.2 + (random() * 0.35)));
		missile.nextthink = ((time + 2.2) + random());
	}
	else
	{
		missile.nextthink = ((time + 1.4) + random());
	}
	missile.velocity_z = ((vec_x + 220) + ((vlen(nozdistancedelta) * 0.22) * (1 + (0.3 * random()))));
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.touch = ShalBossGrenadeTouch;
	missile.think = ShalBossGrenadeExplode;
	setmodel(missile, "progs/v_spike.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.scale = 1.2;
	setorigin(missile, (self.origin + '0 0 60'));
};

void() ShalBossNova =
{
	local entity missile;

	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_FLY;
	missile.solid = SOLID_BBOX;
	missile.nextthink = (time + 0.2);
	missile.think = ShalBossNovaTouch;
	setorigin(missile, (self.origin + '0 0 -117'));
};

void() ShalBossHome =
{
	local vector dir;
	local vector vtemp;

	vtemp = self.enemy.origin + '0 0 10';
	if ((self.enemy.health < 1))
	{
		remove(self);
		return;
	}
	dir = normalize((vtemp - self.origin));
	if ((skill == 3))
	{
		self.velocity = (dir * 350);
	}
	else
	{
		self.velocity = (dir * 250);
	}
	self.nextthink = (time + 0.2);
	self.think = ShalBossHome;
};

void() ShalBossMissileTouch =
{
	if ((other == self.owner))
	{
		return;
	}
	if ((other.classname == "monster_zombie"))
	{
		T_Damage(other, self, self, 110);
	}
	if ((other.classname == "monster_voreling"))
	{
		precache_sound2("voreling/miss.wav");
		sound(self, CHAN_WEAPON, "voreling/miss.wav", 1, ATTN_NORM);
	}
	else
	{
		T_Damage(other, self, self, 25);
		sound(self, CHAN_WEAPON, "shalrath/voreball.wav", 1, ATTN_NORM);
		pointparticles(particleeffectnum(/*57797i*/"voreball_explosion"), self.origin, VEC_ORIGIN, 1);
	}
	self.velocity = VEC_ORIGIN;
	self.touch = SUB_Null;
	setmodel(self, "progs/s_explod.spr");
	self.solid = 0;
	s_explode1();
};

void() ShalBossGrenadeTouch =
{
	if ((other == self.owner))
	{
		return;
	}
	self.velocity = (self.velocity * 1.4);
	if ((other.classname == "monster_zombie"))
	{
		T_Damage(other, self, self, 110);
	}
	if ((other.classname == "monster_voreling"))
	{
		precache_sound2("voreling/miss.wav");
		sound(self, CHAN_WEAPON, "voreling/miss.wav", 1, ATTN_NORM);
	}
	else
	{
		if ((other.takedamage == DAMAGE_AIM))
		{
			ShalBossGrenadeExplode();
			return;
		}
	}
};

void() ShalBossGrenadeExplode =
{
	sound(self, CHAN_WEAPON, "shalrath/voreexp.wav", 1, ATTN_NORM);
	pointparticles(particleeffectnum(/*57797i*/"voreball_explosion"), self.origin, VEC_ORIGIN, 1);
	T_RadiusDamage(self, self.owner, 39, world);
	self.touch = SUB_Null;
	setmodel(self, "progs/s_explod.spr");
	self.solid = 0;
	s_explode1();
};

void() ShalBossNovaTouch =
{
	local entity shockwavefind;

	shockwavefind = findradius(self.owner.origin, 300);
	while (shockwavefind)
	{
		if (shockwavefind.takedamage)
		{
			if ((shockwavefind != self.owner))
			{
				if ((shockwavefind.classname == "monster_voreling"))
				{
					T_Damage(shockwavefind, self, self.owner, 40);
				}
				else
				{
					T_Damage(shockwavefind, self, self.owner, 20);
				}
			}
		}
		shockwavefind = shockwavefind.chain;
	}
	sound(self, CHAN_AUTO, "shalrath/earthshake.wav", 1, ATTN_NONE);
	pointparticles(particleeffectnum(/*58042i*/"vore_shockwave"), self.origin, VEC_ORIGIN, 1);
	if ((shockwavefind.classname == "player"))
	{
		self.owner.enemy.punchangle_x = -7;
	}
	self.velocity = VEC_ORIGIN;
	self.touch = SUB_Null;
	setmodel(self, "progs/ring_shockwave.mdl");
	self.scale = 6;
	self.solid = 0;
	ring_grow1();
};

void() shal_boss_spawner =
{
	local vector distancedelta;
	local vector nozdistancedelta;
	local entity missile;

	self.effects = (self.effects | EF_MUZZLEFLASH);
	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	makevectors(self.angles);
	sound(self, CHAN_WEAPON, "shalrath/firesum.wav", 1, ATTN_NORM);
	distancedelta = self.enemy.origin - self.origin;
	nozdistancedelta = distancedelta;
	missile.velocity = normalize(distancedelta);
	missile.velocity = ((missile.velocity * 150) + (v_right * (random() * 90)));
	missile.velocity_z = ((missile.velocity_z + 350) + ((vlen(nozdistancedelta) * 0.22) * (1 + (0.3 * random()))));
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.nextthink = (time + 2.5);
	missile.think = ShalBossSpawnTouch;
	setmodel(missile, "progs/proj_shalshell.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.scale = 3;
	setorigin(missile, self.origin);
};

void() ShalSpawnerExplode =
{
	pointparticles(particleeffectnum(/*45799i*/"gibacid"), self.origin, VEC_ORIGIN, 1);
	self.velocity = VEC_ORIGIN;
	self.touch = SUB_Null;
	self.scale = 5;
	self.solid = 0;
	s_explode1();
};

void() ShalBossSpawnTouch =
{
	local entity vorespawn;
	local entity tmp;

	ShalSpawnerExplode();
	vorespawn = spawn();
	sound(self, CHAN_WEAPON, "misc/summon.wav", 1, ATTN_NORM);
	vorespawn.classname = "monster_voreling";
	setorigin(vorespawn, (self.origin + '0 0 30'));
	tmp = self;
	self = vorespawn;
	monster_voreling();
};

void() monster_shalrath_boss =
{
	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model2("progs/shalrath_boss.mdl");
	precache_model2("progs/shalrath_death.mdl");
	precache_model2("progs/gib_shalclawb.mdl");
	precache_model2("progs/gib_shalleg_b.mdl");
	precache_model2("progs/h_shalboss.mdl");
	precache_model2("progs/v_spike.mdl");
	precache_model2("progs/proj_shalshell.mdl");
	precache_model2("progs/ring_shockwave.mdl");
	precache_sound2("shalrath/bossattack.wav");
	precache_sound2("shalrath/bossattack2.wav");
	precache_sound2("shalrath/death.wav");
	precache_sound2("shalrath/idle.wav");
	precache_sound2("shalrath/pain.wav");
	precache_sound2("shalrath/bosssight.wav");
	precache_sound2("shalrath/firesum.wav");
	precache_sound2("misc/summon.wav");
	precache_sound2("shalrath/voreexp.wav");
	precache_sound2("shalrath/voretick.wav");
	precache_sound2("shalrath/voreball.wav");
	precache_sound2("shalrath/voregren.wav");
	precache_sound2("shalrath/earthshake.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/shalrath_boss.mdl");
	if (((cvar("skill") == 3) || coop))
	{
		self.health = 6000;
	}
	else
	{
		if ((cvar("skill") == 2))
		{
			self.health = 4500;
		}
		else
		{
			self.health = 3000;
		}
	}
	self.classname = "monster_shalrath_boss";
	self.th_stand = shal_boss_stand;
	self.th_walk = shal_boss_walk1;
	self.th_run = shal_boss_run1;
	self.th_die = shalrath_boss_die;
	self.th_pain = shalrath_boss_pain;
	self.th_missile = shal_boss_attack1;
	self.th_melee = shal_boss_jump1;
	setsize(self, '-46 -40 -24', '46 40 100');
	walkmonster_start();
	self.nextthink = ((time + 0.1) + (random() * 0.1));
};
