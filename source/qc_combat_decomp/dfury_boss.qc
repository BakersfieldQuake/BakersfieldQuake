//Decompiled code. Please respect the original copyright.

void(float AttackNumber) dfury_boss_shot2 =
{
	local entity missile;
	local vector dir;
	local vector org;
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
	makevectors(self.angles);
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_FLYMISSILE;
	precache_model("progs/proj_fury1.mdl");
	setmodel(missile, "progs/proj_fury1.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	if ((AttackNumber == 1))
	{
		org = (self.origin + (v_forward * 20)) + (v_up * 12);
	}
	else
	{
		if ((AttackNumber == 2))
		{
			org = (self.origin + (v_forward * 18)) + (v_up * 10);
		}
		else
		{
			if ((AttackNumber == 3))
			{
				org = ((self.origin + (v_forward * 12)) + (v_up * 12)) + (v_right * 20);
			}
			else
			{
				if ((AttackNumber == 4))
				{
					org = (self.origin + (v_forward * 20)) + (v_up * 16);
				}
			}
		}
	}
	setorigin(missile, org);
	missile.velocity = (dir * 500);
	missile.avelocity = '300 300 300';
	missile.enemy = self.enemy;
	missile.touch = FuryBossMissileTouch;
	missile.nextthink = (time + 0.1);
	missile.think = FuryBossHome;
	sound(self, CHAN_WEAPON, "dfury/attack1.wav", 1, ATTN_NORM);
	self.attack_finished = (time + 2);
};

void(float offset) dfury_boss_shot =
{
	local vector offang;
	local vector org;
	local vector vec;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = ((self.origin + self.mins) + (self.size * 0.5)) + (v_forward * 20);
	vec = normalize(v_forward);
	launch_enemy_spike(org, vec);
	setmodel(newmis, "progs/k_spike.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	newmis.velocity = (vec * 700);
	sound(self, CHAN_WEAPON, "dfury/proj.wav", 1, ATTN_NORM);
};

void() dfury_boss_spawner =
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
	distancedelta = self.enemy.origin - self.origin;
	nozdistancedelta = distancedelta;
	missile.velocity = normalize(distancedelta);
	missile.velocity = ((missile.velocity * 100) + (v_right * random()));
	missile.velocity_z = ((missile.velocity_z + 350) + ((vlen(nozdistancedelta) * 0.22) * (1 + (0.3 * random()))));
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.nextthink = (time + 2.5);
	missile.think = FuryBossSpawnTouch;
	setmodel(missile, "progs/proj_summon.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.scale = 2;
	setorigin(missile, self.origin);
};

void() FuryBossHome =
{
	if ((self.enemy.health < 1))
	{
		remove(self);
		return;
	}
	if ((skill == 3))
	{
		ai_track(self.enemy, 420);
	}
	else
	{
		ai_track(self.enemy, 300);
	}
	self.nextthink = (time + 0.2);
	self.think = FuryBossHome;
};

void() FurySpawnerExplode =
{
	pointparticles(particleeffectnum(/*45799i*/"gibacid"), self.origin, VEC_ORIGIN, 1);
	self.velocity = VEC_ORIGIN;
	self.touch = SUB_Null;
	self.solid = 0;
	s_explode1();
};

void() FuryBossSpawnTouch =
{
	local entity afritspawn;
	local entity tmp;

	FurySpawnerExplode();
	afritspawn = spawn();
	sound(self, CHAN_WEAPON, "misc/summon.wav", 1, ATTN_NORM);
	afritspawn.classname = "monster_afrit";
	setorigin(afritspawn, self.origin);
	tmp = self;
	self = afritspawn;
	monster_afrit();
};

void() FuryBossMissileTouch =
{
	if ((other == self.owner))
	{
		remove(self);
		return;
	}
	if ((other.classname == "monster_zombie"))
	{
		T_Damage(other, self, self, 110);
	}
	T_RadiusDamage(self, self.owner, 20, world);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord(MSG_BROADCAST, self.origin_x);
	WriteCoord(MSG_BROADCAST, self.origin_y);
	WriteCoord(MSG_BROADCAST, self.origin_z);
	self.velocity = VEC_ORIGIN;
	self.touch = SUB_Null;
	setmodel(self, "progs/s_explod.spr");
	self.solid = 0;
	s_explode1();
};

void() FuryBossSpikeTouch =
{
	if ((other == self.owner))
	{
		remove(self);
		return;
	}
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_KNIGHTSPIKE);
	WriteCoord(MSG_BROADCAST, self.origin_x);
	WriteCoord(MSG_BROADCAST, self.origin_y);
	WriteCoord(MSG_BROADCAST, self.origin_z);
	self.velocity = VEC_ORIGIN;
	self.touch = SUB_Null;
	self.solid = 0;
	s_explode1();
	T_RadiusDamage(self, self.owner, 5, world);
};

void() CheckForCharge_boss =
{
	if (!enemy_vis)
	{
		return;
	}
	if ((time < self.attack_finished))
	{
		return;
	}
	if ((fabs((self.origin_z - self.enemy.origin_z)) > 20))
	{
		return;
	}
	if ((vlen((self.origin - self.enemy.origin)) < 80))
	{
		return;
	}
	SUB_AttackFinished(2);
	dfury_boss_char_a1();
};

void() CheckContinueCharge_boss =
{
	if ((time > self.attack_finished))
	{
		SUB_AttackFinished(3);
		dfury_boss_run1();
		return;
	}
	if ((random() > 0.5))
	{
		sound(self, CHAN_WEAPON, "knight/sword2.wav", 1, ATTN_NORM);
	}
	else
	{
		sound(self, CHAN_WEAPON, "knight/sword1.wav", 1, ATTN_NORM);
	}
};

void(float loudness) dfury_boss_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.33))
		{
			sound(self, CHAN_AUTO, "walk/dfuryboss1.wav", loudness, ATTN_IDLE);
		}
		else
		{
			if ((select <= 0.66))
			{
				sound(self, CHAN_AUTO, "walk/dfuryboss2.wav", loudness, ATTN_IDLE);
			}
			else
			{
				sound(self, CHAN_AUTO, "walk/dfuryboss3.wav", loudness, ATTN_IDLE);
			}
		}
	}
};

void() dfury_boss_stand1 = [ 0, dfury_boss_stand2 ]
{
	ai_stand();
	self.colormod = '1 1 1';
};

void() dfury_boss_stand2 = [ 1, dfury_boss_stand3 ]
{
	ai_stand();
};

void() dfury_boss_stand3 = [ 2, dfury_boss_stand4 ]
{
	ai_stand();
};

void() dfury_boss_stand4 = [ 3, dfury_boss_stand5 ]
{
	ai_stand();
};

void() dfury_boss_stand5 = [ 4, dfury_boss_stand6 ]
{
	ai_stand();
};

void() dfury_boss_stand6 = [ 5, dfury_boss_stand7 ]
{
	ai_stand();
};

void() dfury_boss_stand7 = [ 6, dfury_boss_stand8 ]
{
	ai_stand();
};

void() dfury_boss_stand8 = [ 7, dfury_boss_stand9 ]
{
	ai_stand();
};

void() dfury_boss_stand9 = [ 8, dfury_boss_stand1 ]
{
	ai_stand();
};

void() dfury_boss_walk1 = [ 9, dfury_boss_walk2 ]
{
	df_idle_sound();
	ai_walk(2);
	self.colormod = '1 1 1';
	dfury_boss_footsteps(0.8);
};

void() dfury_boss_walk2 = [ 10, dfury_boss_walk3 ]
{
	ai_walk(5);
};

void() dfury_boss_walk3 = [ 11, dfury_boss_walk4 ]
{
	ai_walk(5);
};

void() dfury_boss_walk4 = [ 12, dfury_boss_walk5 ]
{
	ai_walk(4);
};

void() dfury_boss_walk5 = [ 13, dfury_boss_walk6 ]
{
	ai_walk(4);
};

void() dfury_boss_walk6 = [ 14, dfury_boss_walk7 ]
{
	ai_walk(2);
};

void() dfury_boss_walk7 = [ 15, dfury_boss_walk8 ]
{
	ai_walk(2);
};

void() dfury_boss_walk8 = [ 16, dfury_boss_walk9 ]
{
	ai_walk(3);
};

void() dfury_boss_walk9 = [ 17, dfury_boss_walk10 ]
{
	ai_walk(3);
};

void() dfury_boss_walk10 = [ 18, dfury_boss_walk11 ]
{
	ai_walk(4);
};

void() dfury_boss_walk11 = [ 19, dfury_boss_walk12 ]
{
	ai_walk(3);
	dfury_boss_footsteps(1);
};

void() dfury_boss_walk12 = [ 20, dfury_boss_walk13 ]
{
	ai_walk(4);
};

void() dfury_boss_walk13 = [ 21, dfury_boss_walk14 ]
{
	ai_walk(6);
};

void() dfury_boss_walk14 = [ 22, dfury_boss_walk1 ]
{
	ai_walk(2);
};

void() dfury_boss_run1 = [ 23, dfury_boss_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	df_idle_sound();
	ai_run(60);
	CheckForCharge3();
	self.colormod = '1 1 1';
	shambler_walking_quake();
	dfury_boss_footsteps(1);
};

void() dfury_boss_run2 = [ 24, dfury_boss_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(65);
};

void() dfury_boss_run3 = [ 25, dfury_boss_run4 ]
{
	shambler_walking_quake();
	dfury_boss_footsteps(1);
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(48);
};

void() dfury_boss_run4 = [ 26, dfury_boss_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(66);
};

void() dfury_boss_run5 = [ 27, dfury_boss_run6 ]
{
	shambler_walking_quake();
	dfury_boss_footsteps(1);
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(44);
};

void() dfury_boss_run6 = [ 28, dfury_boss_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(63);
};

void() dfury_boss_pain1 = [ 29, dfury_boss_pain2 ]
{
	sound(self, CHAN_VOICE, "dfury/pain1.wav", 1, ATTN_NORM);
	self.colormod = '1 1 1';
};

void() dfury_boss_pain2 = [ 30, dfury_boss_pain3 ]
{
};

void() dfury_boss_pain3 = [ 31, dfury_boss_pain4 ]
{
};

void() dfury_boss_pain4 = [ 32, dfury_boss_pain5 ]
{
};

void() dfury_boss_pain5 = [ 33, dfury_boss_run1 ]
{
};

void() dfury_boss_jump1 = [ 170, dfury_boss_jump2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.01));
	ai_face();
	self.tail_visible = 0;
	shambler_walking_quake();
	dfury_boss_footsteps(1);
};

void() dfury_boss_jump2 = [ 171, dfury_boss_jump3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.01));
	ai_face();
	shambler_walking_quake();
	dfury_boss_footsteps(1);
};

void() dfury_boss_jump3 = [ 172, dfury_boss_jump4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.01));
	ai_face();
};

void() dfury_boss_jump4 = [ 173, dfury_boss_jump5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.tail_visible = 1;
	self.touch = dfury_boss_JumpTouch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 800) + '0 0 250');
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
};

void() dfury_boss_jump5 = [ 174, dfury_boss_jump6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.01));
};

void() dfury_boss_jump6 = [ 175, dfury_boss_jump7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.01));
};

void() dfury_boss_jump7 = [ 176, dfury_boss_jump8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.01));
};

void() dfury_boss_jump8 = [ 177, dfury_boss_jump9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.01));
	dfury_boss_footsteps(1);
};

void() dfury_boss_jump9 = [ 178, dfury_boss_jump10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.01));
	dfury_boss_footsteps(1);
};

void() dfury_boss_jump10 = [ 179, dfury_boss_jump1 ]
{
	self.nextthink = (time + 0.7);
};

void() dfury_boss_jump11 = [ 180, dfury_boss_jump12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.01));
	self.tail_visible = 0;
	shambler_walking_quake();
	dfury_boss_footsteps(1);
};

void() dfury_boss_jump12 = [ 181, dfury_boss_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.01));
	shambler_walking_quake();
	Monster_Animation_EarthQuake(20, 377);
	dfury_boss_footsteps(1);
};

void() dfury_boss_dieburn1 = [ 51, dfury_boss_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
};

void() dfury_boss_dieburn2 = [ 52, dfury_boss_dieburn3 ]
{
	self.burnz_origin = 10;
};

void() dfury_boss_dieburn3 = [ 53, dfury_boss_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
};

void() dfury_boss_dieburn4 = [ 54, dfury_boss_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() dfury_boss_dieburn5 = [ 55, dfury_boss_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() dfury_boss_dieburn6 = [ 56, dfury_boss_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() dfury_boss_dieburn7 = [ 57, dfury_boss_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() dfury_boss_dieburn8 = [ 58, dfury_boss_dieburn9 ]
{
	self.burnz_origin = -6;
};

void() dfury_boss_dieburn9 = [ 59, dfury_boss_dieburn9 ]
{
	self.burnz_origin = -8;
};

void() bossdeath_2 =
{
	local entity shake;

	sendParticle("BOSS_DEATH_FIN", self.origin, VEC_ORIGIN, 1);
	shake = spawn();
	setorigin(shake, (self.origin + '0 0 5'));
	shake.think = screenshake;
	shake.attack_finished = (time + 1);
	shake.nextthink = (time + 0.1);
	sound7(self.owner, CHAN_AUTO, "ambience/coaled_monster_explode.wav", 0.8, ATTN_NONE, SNDSPD);
	sound7(self.owner, CHAN_AUTO, "dfury/boss_explode.wav", 1, ATTN_NONE, SNDSPD);
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -100));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -100));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -50));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -100));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -50));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -100));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -100));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -50));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -100));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -50));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -50));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -100));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -100));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -50));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -100));
	ThrowBody("progs/gib_sBoss.mdl", (self.health + -50));
	remove(self.owner);
	remove(self);
};

void() dfury_boss_loop1 = [ 41, dfury_boss_loop2 ]
{
};

void() dfury_boss_loop2 = [ 42, dfury_boss_loop1 ]
{
};

void() bossdeath_ef =
{
	newmis = spawn();
	setmodel(newmis, "progs/spike.mdl");
	newmis.origin = self.origin;
	newmis.movetype = MOVETYPE_FLY;
	newmis.velocity = '0 0 10';
	newmis.traileffectnum = particleeffectnum(/*60921i*/"BOSS_DEATH");
	newmis.alpha = 0.000100;
	newmis.owner = self;
	sound(self, CHAN_AUTO, "dfury/boss_death1.wav", 1, ATTN_NONE);
	newmis.think = bossdeath_2;
	newmis.nextthink = (time + 7);
	self.skin = 0;
	self.think = dfury_boss_loop1;
	self.nextthink = time;
};

void() dfury_boss_die1 = [ 34, dfury_boss_die2 ]
{
	ai_forward(10);
	self.colormod = '1 1 1';
};

void() dfury_boss_die2 = [ 35, dfury_boss_die3 ]
{
	ai_forward(8);
};

void() dfury_boss_die3 = [ 36, dfury_boss_die4 ]
{
	self.solid = 0;
	ai_forward(7);
};

void() dfury_boss_die4 = [ 37, dfury_boss_die5 ]
{
};

void() dfury_boss_die5 = [ 38, dfury_boss_die6 ]
{
};

void() dfury_boss_die6 = [ 39, dfury_boss_die7 ]
{
};

void() dfury_boss_die7 = [ 40, dfury_boss_die8 ]
{
};

void() dfury_boss_die8 = [ 41, dfury_boss_die9 ]
{
	ai_forward(10);
};

void() dfury_boss_die9 = [ 42, dfury_boss_die10 ]
{
	ai_forward(11);
	self.think = bossdeath_ef;
	self.nextthink = time;
};

void() dfury_boss_die10 = [ 43, dfury_boss_die11 ]
{
};

void() dfury_boss_die11 = [ 44, dfury_boss_die12 ]
{
};

void() dfury_boss_die12 = [ 45, dfury_boss_die13 ]
{
};

void() dfury_boss_die13 = [ 46, dfury_boss_die14 ]
{
};

void() dfury_boss_die14 = [ 47, dfury_boss_die15 ]
{
	sound(self, CHAN_AUTO, "dfury/fall.wav", 1, ATTN_IDLE);
};

void() dfury_boss_die15 = [ 48, dfury_boss_die16 ]
{
};

void() dfury_boss_die16 = [ 49, dfury_boss_die17 ]
{
};

void() dfury_boss_die17 = [ 50, dfury_boss_die17 ]
{
	local float zet;

	zet = 21;
	self.delete_painskin = 1;
	if ((self.nodeathanim == 1))
	{
		return;
	}
};

void() dfury_boss_dieb1 = [ 51, dfury_boss_dieb2 ]
{
	self.colormod = '1 1 1';
};

void() dfury_boss_dieb2 = [ 52, dfury_boss_dieb3 ]
{
};

void() dfury_boss_dieb3 = [ 53, dfury_boss_dieb4 ]
{
	self.solid = 0;
};

void() dfury_boss_dieb4 = [ 54, dfury_boss_dieb5 ]
{
};

void() dfury_boss_dieb5 = [ 55, dfury_boss_dieb6 ]
{
};

void() dfury_boss_dieb6 = [ 56, dfury_boss_dieb7 ]
{
	sound(self, CHAN_AUTO, "dfury/fall.wav", 1, ATTN_IDLE);
};

void() dfury_boss_dieb7 = [ 57, dfury_boss_dieb8 ]
{
};

void() dfury_boss_dieb8 = [ 58, dfury_boss_dieb9 ]
{
	Monster_Animation_EarthQuake(20, 377);
};

void() dfury_boss_dieb9 = [ 59, dfury_boss_dieb10 ]
{
};

void() dfury_boss_dieb10 = [ 60, dfury_boss_dieb11 ]
{
};

void() dfury_boss_dieb11 = [ 61, dfury_boss_dieb12 ]
{
};

void() dfury_boss_dieb12 = [ 62, dfury_boss_dieb13 ]
{
};

void() dfury_boss_dieb13 = [ 63, dfury_boss_dieb14 ]
{
};

void() dfury_boss_dieb14 = [ 64, dfury_boss_dieb14 ]
{
	local float zet;

	zet = 21;
	self.delete_painskin = 1;
	if ((self.nodeathanim == 1))
	{
		return;
	}
};

void(float maxgibs, float gibscounter) producegibs_dfury_boss =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/gib1.mdl", self.health);
		ThrowGib("progs/gib_4.mdl", self.health);
		ThrowGib("progs/gib_5.mdl", self.health);
		ThrowGib("progs/gib_knfoot_l.mdl", self.health);
		ThrowGib("progs/gib_knfoot_r.mdl", self.health);
		ThrowWeapon("progs/w_dknightsword.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_dfury(maxgibs, gibscounter);
};

void() dfury_boss_die =
{
	autocvar_dfuryrandomness = autocvar_dfuryrandomness * 0.01;
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_dfury * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound(self, CHAN_VOICE, "dfury/death1.wav", 1, ATTN_NORM);
	dfury_boss_die1();
};

void() dfury_boss_magica1 = [ 81, dfury_boss_magica2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1.5 1 1';
};

void() dfury_boss_magica2 = [ 82, dfury_boss_magica3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() dfury_boss_magica3 = [ 83, dfury_boss_magica4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2.5 1 1';
};

void() dfury_boss_magica4 = [ 84, dfury_boss_magica5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3 1 1';
};

void() dfury_boss_magica5 = [ 85, dfury_boss_magica6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3.5 1 1';
};

void() dfury_boss_magica6 = [ 86, dfury_boss_magica7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() dfury_boss_magica7 = [ 87, dfury_boss_magica8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot2(-2);
};

void() dfury_boss_magica8 = [ 88, dfury_boss_magica9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_boss_magica9 = [ 89, dfury_boss_magica10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot2(0);
};

void() dfury_boss_magica10 = [ 90, dfury_boss_magica11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot2(1);
};

void() dfury_boss_magica11 = [ 91, dfury_boss_magica12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_boss_magica12 = [ 92, dfury_boss_magica13 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot2(3);
	self.colormod = '3 1 1';
};

void() dfury_boss_magica13 = [ 93, dfury_boss_magica14 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() dfury_boss_magica14 = [ 94, dfury_boss_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1 1 1';
	dfury_boss_random_magic();
};

void() dfury_boss_magicb1 = [ 95, dfury_boss_magicb2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1.5 1 1';
};

void() dfury_boss_magicb2 = [ 96, dfury_boss_magicb3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() dfury_boss_magicb3 = [ 97, dfury_boss_magicb4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2.5 1 1';
};

void() dfury_boss_magicb4 = [ 98, dfury_boss_magicb5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3 1 1';
};

void() dfury_boss_magicb5 = [ 99, dfury_boss_magicb6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3.5 1 1';
};

void() dfury_boss_magicb6 = [ 100, dfury_boss_magicb7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() dfury_boss_magicb7 = [ 101, dfury_boss_magicb8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(-2);
};

void() dfury_boss_magicb8 = [ 102, dfury_boss_magicb9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(-1);
};

void() dfury_boss_magicb9 = [ 103, dfury_boss_magicb10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(0);
};

void() dfury_boss_magicb10 = [ 104, dfury_boss_magicb11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(1);
};

void() dfury_boss_magicb11 = [ 105, dfury_boss_magicb12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(2);
};

void() dfury_boss_magicb12 = [ 106, dfury_boss_magicb13 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(3);
	self.colormod = '2 1 1';
};

void() dfury_boss_magicb13 = [ 107, dfury_boss_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1 1 1';
	dfury_boss_random_magic();
};

void() dfury_boss_magicc1 = [ 159, dfury_boss_magicc2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1.5 1 1';
};

void() dfury_boss_magicc2 = [ 160, dfury_boss_magicc3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() dfury_boss_magicc3 = [ 161, dfury_boss_magicc4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2.5 1 1';
};

void() dfury_boss_magicc4 = [ 162, dfury_boss_magicc5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3 1 1';
};

void() dfury_boss_magicc5 = [ 163, dfury_boss_magicc6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3.5 1 1';
};

void() dfury_boss_magicc6 = [ 164, dfury_boss_magicc7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(-3);
};

void() dfury_boss_magicc7 = [ 165, dfury_boss_magicc8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(-1);
};

void() dfury_boss_magicc8 = [ 166, dfury_boss_magicc9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(0);
};

void() dfury_boss_magicc9 = [ 167, dfury_boss_magicc10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(1);
};

void() dfury_boss_magicc10 = [ 168, dfury_boss_magicc11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(3);
	self.colormod = '2 1 1';
};

void() dfury_boss_magicc11 = [ 169, dfury_boss_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_shot(4);
	self.colormod = '1 1 1';
	dfury_boss_random_magic();
};

void() dfury_boss_spawn1 = [ 95, dfury_boss_spawn2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1.5 1 1';
};

void() dfury_boss_spawn2 = [ 96, dfury_boss_spawn3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() dfury_boss_spawn3 = [ 97, dfury_boss_spawn4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2.5 1 1';
};

void() dfury_boss_spawn4 = [ 98, dfury_boss_spawn5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3 1 1';
};

void() dfury_boss_spawn5 = [ 99, dfury_boss_spawn6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3.5 1 1';
};

void() dfury_boss_spawn6 = [ 100, dfury_boss_spawn7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() dfury_boss_spawn7 = [ 101, dfury_boss_spawn8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_boss_spawn8 = [ 102, dfury_boss_spawn9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_boss_spawn9 = [ 103, dfury_boss_spawn10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_boss_spawn10 = [ 104, dfury_boss_spawn11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_spawner();
};

void() dfury_boss_spawn11 = [ 105, dfury_boss_spawn12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_boss_spawn12 = [ 106, dfury_boss_spawn13 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_boss_spawner();
	self.colormod = '2 1 1';
};

void() dfury_boss_spawn13 = [ 107, dfury_boss_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1 1 1';
	dfury_boss_random_magic();
};

void() dfury_boss_char_a1 = [ 65, dfury_boss_char_a2 ]
{
	ai_charge(76);
	self.colormod = '1 1 1';
	dfury_boss_footsteps(1);
};

void() dfury_boss_char_a2 = [ 66, dfury_boss_char_a3 ]
{
	ai_charge(70);
	dfury_boss_footsteps(0.9);
	dfury_boss_footsteps(1);
};

void() dfury_boss_char_a3 = [ 67, dfury_boss_char_a4 ]
{
	dfury_boss_footsteps(1);
	ai_charge(78);
	if ((random() > 0.3))
	{
		dfury_boss_jump1();
	}
};

void() dfury_boss_char_a4 = [ 68, dfury_boss_char_a5 ]
{
	ai_charge(76);
	dfury_boss_footsteps(1);
};

void() dfury_boss_char_a5 = [ 69, dfury_boss_char_a6 ]
{
	ai_charge(74);
	dfury_boss_footsteps(1);
};

void() dfury_boss_char_a6 = [ 70, dfury_boss_char_a7 ]
{
	dfury_boss_footsteps(1);
	ai_charge(70);
	ai_melee_dfury_boss();
};

void() dfury_boss_char_a7 = [ 71, dfury_boss_char_a8 ]
{
	dfury_boss_footsteps(1);
	ai_charge(71);
	ai_melee_dfury_boss();
};

void() dfury_boss_char_a8 = [ 72, dfury_boss_char_a9 ]
{
	dfury_boss_footsteps(1);
	ai_charge(73);
	ai_melee_dfury_boss();
};

void() dfury_boss_char_a9 = [ 73, dfury_boss_char_a10 ]
{
	dfury_boss_footsteps(1);
	ai_charge(70);
	ai_melee_dfury_boss();
};

void() dfury_boss_char_a10 = [ 74, dfury_boss_char_a11 ]
{
	dfury_boss_footsteps(1);
	ai_charge(70);
	ai_melee_dfury_boss();
};

void() dfury_boss_char_a11 = [ 75, dfury_boss_char_a12 ]
{
	dfury_boss_footsteps(1);
	ai_charge(78);
	ai_melee_dfury_boss();
};

void() dfury_boss_char_a12 = [ 76, dfury_boss_char_a13 ]
{
	dfury_boss_footsteps(1);
	ai_charge(76);
};

void() dfury_boss_char_a13 = [ 77, dfury_boss_char_a14 ]
{
	ai_charge(74);
	dfury_boss_footsteps(0.9);
};

void() dfury_boss_char_a14 = [ 78, dfury_boss_char_a15 ]
{
	dfury_boss_footsteps(1);
	ai_charge(75);
};

void() dfury_boss_char_a15 = [ 79, dfury_boss_char_a16 ]
{
	dfury_boss_footsteps(1);
	ai_charge(71);
};

void() dfury_boss_char_a16 = [ 80, dfury_boss_run1 ]
{
	dfury_boss_footsteps(1);
	ai_charge(73);
};

void() dfury_boss_char_b1 = [ 108, dfury_boss_char_b2 ]
{
	CheckContinueCharge3();
	ai_charge(23);
	ai_melee_dfury_boss();
	self.colormod = '1 1 1';
};

void() dfury_boss_char_b2 = [ 109, dfury_boss_char_b3 ]
{
	ai_charge(72);
	ai_melee_dfury_boss();
	dfury_boss_footsteps(1);
};

void() dfury_boss_char_b3 = [ 110, dfury_boss_char_b4 ]
{
	ai_charge(72);
	ai_melee_dfury_boss();
	dfury_boss_footsteps(1);
};

void() dfury_boss_char_b4 = [ 111, dfury_boss_char_b5 ]
{
	ai_charge(72);
	ai_melee_dfury_boss();
	dfury_boss_footsteps(0.9);
};

void() dfury_boss_char_b5 = [ 112, dfury_boss_char_b6 ]
{
	ai_charge(78);
	ai_melee_dfury_boss();
	dfury_boss_footsteps(1);
};

void() dfury_boss_char_b6 = [ 113, dfury_boss_char_b1 ]
{
	ai_charge(78);
	ai_melee_dfury_boss();
	dfury_boss_footsteps(1);
};

void() dfury_boss_slice1 = [ 114, dfury_boss_slice2 ]
{
	ai_charge(79);
	self.colormod = '1 1 1';
};

void() dfury_boss_slice2 = [ 115, dfury_boss_slice3 ]
{
	ai_charge(76);
};

void() dfury_boss_slice3 = [ 116, dfury_boss_slice4 ]
{
	ai_charge(73);
	dfury_boss_footsteps(0.8);
};

void() dfury_boss_slice4 = [ 117, dfury_boss_slice5 ]
{
	ai_charge(74);
};

void() dfury_boss_slice5 = [ 118, dfury_boss_slice6 ]
{
	ai_charge(77);
	ai_melee_dfury_boss();
};

void() dfury_boss_slice6 = [ 119, dfury_boss_slice7 ]
{
	ai_charge(75);
	ai_melee_dfury_boss();
};

void() dfury_boss_slice7 = [ 120, dfury_boss_slice8 ]
{
	ai_charge(78);
	ai_melee_dfury_boss();
	dfury_boss_footsteps(0.8);
};

void() dfury_boss_slice8 = [ 121, dfury_boss_slice9 ]
{
	ai_charge(72);
	ai_melee_dfury_boss();
};

void() dfury_boss_slice9 = [ 122, dfury_boss_slice10 ]
{
	ai_melee_dfury_boss();
};

void() dfury_boss_slice10 = [ 123, dfury_boss_slice11 ]
{
	ai_charge(64);
	ai_melee_dfury_boss();
	dfury_boss_footsteps(1);
};

void() dfury_boss_slice11 = [ 124, dfury_boss_slice12 ]
{
	ai_charge(64);
	ai_melee_dfury_boss();
};

void() dfury_boss_slice12 = [ 125, dfury_boss_slice13 ]
{
	ai_charge(64);
	ai_melee_dfury_boss();
};

void() dfury_boss_slice13 = [ 126, dfury_boss_slice14 ]
{
	ai_charge(64);
	ai_melee_dfury_boss();
	dfury_boss_footsteps(1);
};

void() dfury_boss_slice14 = [ 127, dfury_boss_run1 ]
{
	ai_charge(53);
};

void() dfury_boss_smash1 = [ 128, dfury_boss_smash2 ]
{
	ai_charge(1);
	self.colormod = '1 1 1';
};

void() dfury_boss_smash2 = [ 129, dfury_boss_smash3 ]
{
	ai_charge(48);
};

void() dfury_boss_smash3 = [ 130, dfury_boss_smash4 ]
{
	ai_charge(9);
};

void() dfury_boss_smash4 = [ 131, dfury_boss_smash5 ]
{
	ai_charge(51);
	dfury_boss_footsteps(0.8);
};

void() dfury_boss_smash5 = [ 132, dfury_boss_smash6 ]
{
	ai_charge(40);
	ai_melee_dfury_boss();
};

void() dfury_boss_smash6 = [ 133, dfury_boss_smash7 ]
{
	ai_charge(7);
	ai_melee_dfury_boss();
};

void() dfury_boss_smash7 = [ 134, dfury_boss_smash8 ]
{
	ai_charge(42);
	ai_melee_dfury_boss();
};

void() dfury_boss_smash8 = [ 135, dfury_boss_smash9 ]
{
	ai_charge(42);
	ai_melee_dfury_boss();
	Monster_Animation_EarthQuake(20, 377);
	dfury_boss_footsteps(1);
};

void() dfury_boss_smash9 = [ 136, dfury_boss_smash10 ]
{
	ai_charge(3);
	ai_melee_dfury_boss();
	Monster_Animation_EarthQuake(20, 377);
};

void() dfury_boss_smash10 = [ 137, dfury_boss_smash11 ]
{
	ai_charge(0);
	Monster_Animation_EarthQuake(20, 377);
};

void() dfury_boss_smash11 = [ 138, dfury_boss_smash12 ]
{
	ai_charge(0);
};

void() dfury_boss_smash12 = [ 139, dfury_boss_smash13 ]
{
	ai_charge(0);
};

void() dfury_boss_smash13 = [ 140, dfury_boss_smash14 ]
{
	ai_charge(0);
};

void() dfury_boss_smash14 = [ 141, dfury_boss_smash15 ]
{
	ai_charge(0);
	dfury_boss_footsteps(1);
};

void() dfury_boss_smash15 = [ 142, dfury_boss_run1 ]
{
	ai_charge(0);
};

void() dfury_boss_watk1 = [ 143, dfury_boss_watk2 ]
{
	ai_charge(8);
	self.colormod = '1 1 1';
};

void() dfury_boss_watk2 = [ 144, dfury_boss_watk3 ]
{
	ai_charge(0);
};

void() dfury_boss_watk3 = [ 145, dfury_boss_watk4 ]
{
	ai_charge(0);
};

void() dfury_boss_watk4 = [ 146, dfury_boss_watk5 ]
{
	ai_melee_dfury_boss();
};

void() dfury_boss_watk5 = [ 147, dfury_boss_watk6 ]
{
	ai_melee_dfury_boss();
};

void() dfury_boss_watk6 = [ 148, dfury_boss_watk7 ]
{
	ai_melee_dfury_boss();
};

void() dfury_boss_watk7 = [ 149, dfury_boss_watk8 ]
{
	ai_charge(24);
	ai_melee_dfury_boss();
};

void() dfury_boss_watk8 = [ 150, dfury_boss_watk9 ]
{
	ai_charge(30);
	ai_melee_dfury_boss();
};

void() dfury_boss_watk9 = [ 151, dfury_boss_watk10 ]
{
	ai_charge(32);
};

void() dfury_boss_watk10 = [ 152, dfury_boss_watk11 ]
{
	ai_charge(16);
	ai_melee_dfury_boss();
};

void() dfury_boss_watk11 = [ 153, dfury_boss_watk12 ]
{
	ai_charge(15);
	ai_melee_dfury_boss();
	dfury_boss_footsteps(0.8);
};

void() dfury_boss_watk12 = [ 154, dfury_boss_watk13 ]
{
	ai_charge(15);
	ai_melee_dfury_boss();
};

void() dfury_boss_watk13 = [ 155, dfury_boss_watk14 ]
{
	ai_charge(0);
};

void() dfury_boss_watk14 = [ 156, dfury_boss_watk15 ]
{
	ai_charge(0);
	ai_melee_dfury_boss();
};

void() dfury_boss_watk15 = [ 157, dfury_boss_watk16 ]
{
	ai_charge(0);
	ai_melee_dfury_boss();
};

void() dfury_boss_watk16 = [ 158, dfury_boss_run1 ]
{
	ai_charge(13);
	dfury_boss_footsteps(0.8);
};

void() dfury_boss_idle_sound =
{
	if ((random() < 0.2))
	{
		sound(self, CHAN_VOICE, "dfury/idle.wav", 1, ATTN_NORM);
	}
};

void(entity attacker, float damage) dfury_boss_pain =
{
	if ((self.pain_finished > time))
	{
		return;
	}
	sound(self, CHAN_VOICE, "dfury/pain1.wav", 1, ATTN_NORM);
	if (((time - self.pain_finished) > 5))
	{
		if ((autocvar_slowmotion >= 4))
		{
			if ((random() <= (autocvar_slowmotion_randomness_dfury * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		dfury_boss_pain1();
		self.pain_finished = (time + 1);
		return;
	}
	if (((random() * 30) > damage))
	{
		return;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_dfury * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	self.pain_finished = (time + 1);
	dfury_boss_pain1();
};

void() dfury_boss_melee =
{
	dfury_boss_type = dfury_boss_type + 1;
	sound(self, CHAN_WEAPON, "dfury/slash1.wav", 1, ATTN_NORM);
	if ((dfury_boss_type == 1))
	{
		dfury_boss_slice1();
	}
	else
	{
		if ((dfury_boss_type == 2))
		{
			dfury_boss_smash1();
		}
		else
		{
			if ((dfury_boss_type == 3))
			{
				dfury_boss_watk1();
				dfury_boss_type = 0;
			}
		}
	}
};

void() dfury_boss_random_magic =
{
	local float zufall;

	zufall = random();
	if (((zufall > 0.56) && (zufall < 0.62)))
	{
		self.th_missile = dfury_boss_magica1;
	}
	else
	{
		if ((zufall > 0.61))
		{
			self.th_missile = dfury_boss_spawn1;
		}
		else
		{
			if ((zufall < 0.34))
			{
				self.th_missile = dfury_boss_magicb1;
			}
			else
			{
				self.th_missile = dfury_boss_magicc1;
			}
		}
	}
};

void() dfury_boss_JumpTouch =
{
	local float ldmg;

	if ((self.health <= 0))
	{
		return;
	}
	if (other.takedamage)
	{
		if ((vlen(self.velocity) > 100))
		{
			ldmg = 50 + (10 * random());
			if ((other.classname == "player"))
			{
				T_Damage(other, self, self, 40);
			}
		}
	}
	if (!checkbottom(self))
	{
		self.tail_visible = 0;
		if ((self.flags & FL_ONGROUND))
		{
			self.touch = SUB_Null;
			self.think = dfury_boss_jump1;
			self.nextthink = (time + 0.1);
		}
		return;
	}
	self.touch = SUB_Null;
	self.think = dfury_boss_jump11;
	self.nextthink = (time + 0.1);
};

void() dfury_boss_pause =
{
	precache_sound("misc/wallbrk.wav");
	sound(self, CHAN_AUTO, "misc/wallbrk.wav", 1, ATTN_NONE);
	self.skin = 1;
	self.takedamage = DAMAGE_AIM;
	self.th_stand = dfury_boss_stand1;
	self.th_walk = dfury_boss_walk1;
	self.th_run = dfury_boss_run1;
	self.th_melee = dfury_boss_melee;
	self.th_missile = dfury_boss_random_magic;
	self.th_pain = dfury_boss_pain;
	self.th_die = dfury_boss_die;
	self.use = SUB_Null;
	self.think = dfury_boss_run1;
	self.enemy = activator;
	self.nextthink = (time + 0.1);
	self.think = FoundTarget;
	self.delay = 0;
};

void() dfury_boss_pause1 =
{
	self.takedamage = 0;
	self.use = dfury_boss_pause;
	self.think = dfury_boss_pause1;
	self.nextthink = (time + 0.1);
	self.skin = 0;
};

void() monster_dfury_boss =
{
	local float zufall;
	local entity pain_skin_entity;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model2("progs/dfury_boss.mdl");
	precache_model2("progs/k_spike.mdl");
	precache_model("progs/proj_summon.mdl");
	precache_model("progs/gib_sBoss.mdl");
	precache_sound2("dfury/boss_explode.wav");
	precache_sound2("dfury/boss_death1.wav");
	precache_sound2("dfury/attack1.wav");
	precache_sound2("dfury/death1.wav");
	precache_sound2("dfury/pain1.wav");
	precache_sound("dfury/death2.wav");
	precache_sound("dfury/pain2.wav");
	precache_sound2("dfury/sight1.wav");
	precache_sound("dfury/hit.wav");
	precache_sound2("dfury/slash1.wav");
	precache_sound2("dfury/idle.wav");
	precache_sound2("dfury/grunt.wav");
	precache_sound2("dfury/proj.wav");
	precache_sound("dfury/fall.wav");
	precache_sound("walk/dfury1.wav");
	precache_sound("walk/dfury2.wav");
	precache_sound("walk/dfury3.wav");
	precache_sound("walk/dfuryboss1.wav");
	precache_sound("walk/dfuryboss2.wav");
	precache_sound("walk/dfuryboss3.wav");
	precache_sound("misc/summon.wav");
	precache_sound("knight/dropsword.wav");
	precache_sound("knight/sword1.wav");
	precache_sound("knight/sword2.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((autocvar_dfurymultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/dfury_boss.mdl");
		zufall = random();
		if ((zufall >= 0.5))
		{
			self.skin = 0;
			self.monsterskin = 0;
			self.monstermodel = 0;
		}
		else
		{
			self.skin = 1;
			self.monsterskin = 1;
			self.monstermodel = 0;
		}
	}
	else
	{
		if ((autocvar_dfurymultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/dfury1.mdl");
			precache_model("progs/h_hellkn1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_dfurymultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/dfury1.mdl");
				precache_model("progs/h_hellkn1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/dfury_boss.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/dfury_boss.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/dfury1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_dfurymultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/dfury1.mdl");
					precache_model("progs/h_hellkn1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/dfury_boss.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/dfury_boss.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/dfury1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/dfury1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/dfury_boss.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	self.scale = 1;
	setsize(self, '-26 -30 -24', '26 30 100');
	if (((cvar("skill") == 3) || coop))
	{
		self.health = 6700;
	}
	else
	{
		if ((cvar("skill") == 2))
		{
			self.health = 5000;
		}
		else
		{
			self.health = 3500;
		}
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_dfury_boss_random_skin_colors))
	{
		self.colormod_x = random();
		if ((self.colormod_x < 0.5))
		{
			self.colormod_x = (self.colormod_x + 0.5);
		}
		if ((autocvar_monster_random_skin_color_alteration == 1))
		{
			if ((self.colormod_x < 0.75))
			{
				self.colormod_x = (self.colormod_x + 0.25);
			}
		}
		else
		{
			if ((autocvar_monster_random_skin_color_alteration == 2))
			{
				if ((self.colormod_x < 0.65))
				{
					self.colormod_x = (self.colormod_x + 0.25);
				}
			}
			else
			{
				if ((self.colormod_x < 0.55))
				{
					self.colormod_x = (self.colormod_x + 0.25);
				}
			}
		}
		self.colormod_y = random();
		if ((self.colormod_y < 0.5))
		{
			self.colormod_y = (self.colormod_y + 0.5);
		}
		if ((autocvar_monster_random_skin_color_alteration == 1))
		{
			if ((self.colormod_y < 0.75))
			{
				self.colormod_y = (self.colormod_y + 0.25);
			}
		}
		else
		{
			if ((autocvar_monster_random_skin_color_alteration == 2))
			{
				if ((self.colormod_y < 0.65))
				{
					self.colormod_y = (self.colormod_y + 0.25);
				}
			}
			else
			{
				if ((self.colormod_y < 0.55))
				{
					self.colormod_y = (self.colormod_y + 0.25);
				}
			}
		}
		self.colormod_z = random();
		if ((self.colormod_z < 0.5))
		{
			self.colormod_z = (self.colormod_z + 0.5);
		}
		if ((autocvar_monster_random_skin_color_alteration == 1))
		{
			if ((self.colormod_z < 0.75))
			{
				self.colormod_z = (self.colormod_z + 0.25);
			}
		}
		else
		{
			if ((autocvar_monster_random_skin_color_alteration == 2))
			{
				if ((self.colormod_z < 0.65))
				{
					self.colormod_z = (self.colormod_z + 0.25);
				}
			}
			else
			{
				if ((self.colormod_z < 0.55))
				{
					self.colormod_z = (self.colormod_z + 0.25);
				}
			}
		}
	}
	if ((self.spawnflags & 2))
	{
		if ((self.frame == 0))
		{
			self.frame = 10;
		}
		if (!self.targetname)
		{
			dprint("statue not targeted\n");
			dprint(self.classname);
			dprint(" at ");
			dprint(vtos(self.origin));
			dprint("\n");
			return;
		}
		self.use = dfury_boss_pause;
		self.th_stand = dfury_boss_pause1;
		self.th_walk = dfury_boss_pause1;
		self.th_run = dfury_boss_pause1;
		walkmonster_start();
	}
	else
	{
		self.th_stand = dfury_boss_stand1;
		self.th_walk = dfury_boss_walk1;
		self.th_run = dfury_boss_run1;
		self.th_melee = dfury_boss_melee;
		self.th_missile = dfury_boss_random_magic;
		self.th_pain = dfury_boss_pain;
		self.th_die = dfury_boss_die;
		self.alpha = (autocvar_monstertransparency * 0.01);
		if (autocvar_painskin_transparency)
		{
			pain_skin_entity = spawn();
			pain_skin_entity.solid = 0;
			pain_skin_entity.movetype = MOVETYPE_NOCLIP;
			pain_skin_entity.owner = self;
			setmodel(pain_skin_entity, self.model);
			setsize(pain_skin_entity, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
			setorigin(pain_skin_entity, VEC_ORIGIN);
			pain_skin_entity.skin = self.skin;
			pain_skin_entity.colormod_x = self.colormod_x;
			pain_skin_entity.colormod_y = self.colormod_y;
			pain_skin_entity.colormod_z = self.colormod_z;
			pain_skin_entity.monstermodel = self.monstermodel;
			pain_skin_entity.frame = self.frame;
			pain_skin_entity.alpha = autocvar_painskin_transparency;
			pain_skin_entity.think = pain_skin_entity_think;
			pain_skin_entity.nextthink = time;
			setattachment(pain_skin_entity, self, /*37325i*/"test");
		}
		walkmonster_start();
	}
	MonsterPhysics(self, autocvar_dfurymass);
};
