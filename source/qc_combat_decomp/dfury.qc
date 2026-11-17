//Decompiled code. Please respect the original copyright.

void(float offset) dfury_shot =
{
	local vector offang;
	local vector org;
	local vector vec;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = ((self.origin + self.mins) + (self.size * 0.5)) + (v_forward * 20);
	vec = normalize(v_forward);
	if ((autocvar_skill_adjusted_hellknight_projectile_homing && (skill != 0)))
	{
		launch_homing_spikes(org, vec);
	}
	else
	{
		launch_enemy_spike(org, vec);
	}
	newmis.classname = "furyspike";
	precache_model("progs/proj_fury1.mdl");
	setmodel(newmis, "progs/proj_fury1.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	newmis.velocity = (vec * 700);
	newmis.avelocity = '300 300 300';
	newmis.touch = FuryMissileTouch;
	sound(self, CHAN_WEAPON, "dfury/attack1.wav", 1, ATTN_NORM);
};

void() FuryMissileTouch =
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

void() CheckForCharge3 =
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
	dfury_char_a1();
};

void() CheckContinueCharge3 =
{
	if ((time > self.attack_finished))
	{
		SUB_AttackFinished(3);
		dfury_run1();
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

void(float loudness) dfury_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.33))
		{
			sound(self, CHAN_AUTO, "walk/dfury1.wav", loudness, ATTN_IDLE);
		}
		else
		{
			if ((select <= 0.66))
			{
				sound(self, CHAN_AUTO, "walk/dfury2.wav", loudness, ATTN_IDLE);
			}
			else
			{
				sound(self, CHAN_AUTO, "walk/dfury3.wav", loudness, ATTN_IDLE);
			}
		}
	}
};

void() dfury_stand1 = [ 0, dfury_stand2 ]
{
	ai_stand();
	self.colormod = '1 1 1';
};

void() dfury_stand2 = [ 1, dfury_stand3 ]
{
	ai_stand();
};

void() dfury_stand3 = [ 2, dfury_stand4 ]
{
	ai_stand();
};

void() dfury_stand4 = [ 3, dfury_stand5 ]
{
	ai_stand();
};

void() dfury_stand5 = [ 4, dfury_stand6 ]
{
	ai_stand();
};

void() dfury_stand6 = [ 5, dfury_stand7 ]
{
	ai_stand();
};

void() dfury_stand7 = [ 6, dfury_stand8 ]
{
	ai_stand();
};

void() dfury_stand8 = [ 7, dfury_stand9 ]
{
	ai_stand();
};

void() dfury_stand9 = [ 8, dfury_stand1 ]
{
	ai_stand();
};

void() dfury_walk1 = [ 9, dfury_walk2 ]
{
	df_idle_sound();
	ai_walk(2);
	self.colormod = '1 1 1';
	dfury_footsteps(0.8);
};

void() dfury_walk2 = [ 10, dfury_walk3 ]
{
	ai_walk(5);
};

void() dfury_walk3 = [ 11, dfury_walk4 ]
{
	ai_walk(5);
};

void() dfury_walk4 = [ 12, dfury_walk5 ]
{
	ai_walk(4);
};

void() dfury_walk5 = [ 13, dfury_walk6 ]
{
	ai_walk(4);
};

void() dfury_walk6 = [ 14, dfury_walk7 ]
{
	ai_walk(2);
};

void() dfury_walk7 = [ 15, dfury_walk8 ]
{
	ai_walk(2);
};

void() dfury_walk8 = [ 16, dfury_walk9 ]
{
	ai_walk(3);
};

void() dfury_walk9 = [ 17, dfury_walk10 ]
{
	ai_walk(3);
};

void() dfury_walk10 = [ 18, dfury_walk11 ]
{
	ai_walk(4);
};

void() dfury_walk11 = [ 19, dfury_walk12 ]
{
	ai_walk(3);
	dfury_footsteps(0.8);
};

void() dfury_walk12 = [ 20, dfury_walk13 ]
{
	ai_walk(4);
};

void() dfury_walk13 = [ 21, dfury_walk14 ]
{
	ai_walk(6);
};

void() dfury_walk14 = [ 22, dfury_walk1 ]
{
	ai_walk(2);
};

void() dfury_run1 = [ 23, dfury_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	df_idle_sound();
	ai_run(20);
	CheckForCharge3();
	self.colormod = '1 1 1';
};

void() dfury_run2 = [ 24, dfury_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(35);
	dfury_footsteps(1);
};

void() dfury_run3 = [ 25, dfury_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(28);
};

void() dfury_run4 = [ 26, dfury_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(26);
};

void() dfury_run5 = [ 27, dfury_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(24);
};

void() dfury_run6 = [ 28, dfury_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(23);
};

void() dfury_pain1 = [ 29, dfury_pain2 ]
{
	sound(self, CHAN_VOICE, "dfury/pain1.wav", 1, ATTN_NORM);
	self.colormod = '1 1 1';
};

void() dfury_pain2 = [ 30, dfury_pain3 ]
{
};

void() dfury_pain3 = [ 31, dfury_pain4 ]
{
};

void() dfury_pain4 = [ 32, dfury_pain5 ]
{
};

void() dfury_pain5 = [ 33, dfury_run1 ]
{
};

void() dfury_jump1 = [ 170, dfury_jump2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.tail_visible = 0;
};

void() dfury_jump2 = [ 171, dfury_jump3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() dfury_jump3 = [ 172, dfury_jump4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() dfury_jump4 = [ 173, dfury_jump5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.tail_visible = 1;
	self.touch = dfury_JumpTouch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 800) + '0 0 250');
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
};

void() dfury_jump5 = [ 174, dfury_jump6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_jump6 = [ 175, dfury_jump7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_jump7 = [ 176, dfury_jump8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_jump8 = [ 177, dfury_jump9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_jump9 = [ 178, dfury_jump10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_jump10 = [ 179, dfury_jump1 ]
{
	self.nextthink = (time + 0.7);
};

void() dfury_jump11 = [ 180, dfury_jump12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	self.tail_visible = 0;
};

void() dfury_jump12 = [ 181, dfury_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_dieburn1 = [ 51, dfury_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
};

void() dfury_dieburn2 = [ 52, dfury_dieburn3 ]
{
	self.burnz_origin = 10;
};

void() dfury_dieburn3 = [ 53, dfury_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
};

void() dfury_dieburn4 = [ 54, dfury_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() dfury_dieburn5 = [ 55, dfury_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() dfury_dieburn6 = [ 56, dfury_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() dfury_dieburn7 = [ 57, dfury_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() dfury_dieburn8 = [ 58, dfury_dieburn9 ]
{
	self.burnz_origin = -6;
};

void() dfury_dieburn9 = [ 59, dfury_dieburn9 ]
{
	self.burnz_origin = -8;
};

void() dfury_die1 = [ 34, dfury_die2 ]
{
	ai_forward(10);
	self.colormod = '1 1 1';
};

void() dfury_die2 = [ 35, dfury_die3 ]
{
	ai_forward(8);
};

void() dfury_die3 = [ 36, dfury_die4 ]
{
	self.solid = 0;
	ai_forward(7);
};

void() dfury_die4 = [ 37, dfury_die5 ]
{
};

void() dfury_die5 = [ 38, dfury_die6 ]
{
};

void() dfury_die6 = [ 39, dfury_die7 ]
{
};

void() dfury_die7 = [ 40, dfury_die8 ]
{
};

void() dfury_die8 = [ 41, dfury_die9 ]
{
	ai_forward(10);
};

void() dfury_die9 = [ 42, dfury_die10 ]
{
	ai_forward(11);
};

void() dfury_die10 = [ 43, dfury_die11 ]
{
};

void() dfury_die11 = [ 44, dfury_die12 ]
{
};

void() dfury_die12 = [ 45, dfury_die13 ]
{
};

void() dfury_die13 = [ 46, dfury_die14 ]
{
};

void() dfury_die14 = [ 47, dfury_die15 ]
{
	sound(self, CHAN_AUTO, "hknight/fall.wav", 1, ATTN_IDLE);
};

void() dfury_die15 = [ 48, dfury_die16 ]
{
};

void() dfury_die16 = [ 49, dfury_die17 ]
{
};

void() dfury_die17 = [ 50, dfury_die17 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 21;
	if ((autocvar_dfurycorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_dfurycorpsehealth, "progs/h_hellkn.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_dfurycorpsehealth, "progs/h_hellkn1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_dfuryrandomness = autocvar_dfuryrandomness * 0.01;
		if ((autocvar_dfury == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_dfuryrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_dfury == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_dfuryrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/dfury.mdl", 45, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/dfury1.mdl", 45, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_dfury == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_dfuryrandomness))
					{
						vengeance_dfury("progs/dfury.mdl", 45);
					}
				}
				else
				{
					if ((autocvar_dfury == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_dfuryrandomness))
						{
							zufall = random();
							if ((zufall > 0.64))
							{
								ghost_die();
							}
							else
							{
								if ((zufall < 0.26))
								{
									if ((self.monstermodel == 0))
									{
										soul("progs/dfury.mdl", 45, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/dfury1.mdl", 45, zet);
										}
									}
								}
								else
								{
								}
							}
						}
					}
					else
					{
					}
				}
			}
		}
	}
	else
	{
		if ((self.grimrock_helper == 1))
		{
			zufall = random();
			if ((zufall > 0.64))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.26))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/dfury.mdl", 45, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/dfury1.mdl", 45, zet);
						}
					}
				}
			}
		}
	}
};

void() dfury_diessg1 = [ 185, dfury_diessg2 ]
{
};

void() dfury_diessg2 = [ 186, dfury_diessg3 ]
{
	sound(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE);
};

void() dfury_diessg3 = [ 187, dfury_diessg4 ]
{
	ai_forward(8);
};

void() dfury_diessg4 = [ 188, dfury_diessg5 ]
{
	sound(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE);
};

void() dfury_diessg5 = [ 189, dfury_diessg6 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessg6 = [ 190, dfury_diessg7 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessg7 = [ 191, dfury_diessg8 ]
{
	sound(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE);
};

void() dfury_diessg8 = [ 192, dfury_diessg9 ]
{
	ai_forward(8);
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessg9 = [ 193, dfury_diessg10 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessg10 = [ 194, dfury_diessg11 ]
{
};

void() dfury_diessg11 = [ 195, dfury_diessg12 ]
{
};

void() dfury_diessg12 = [ 196, dfury_diessg13 ]
{
	sound(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE);
};

void() dfury_diessg13 = [ 197, dfury_diessg14 ]
{
	ai_forward(8);
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessg14 = [ 198, dfury_diessg15 ]
{
};

void() dfury_diessg15 = [ 199, dfury_diessg16 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessg16 = [ 200, dfury_diessg17 ]
{
};

void() dfury_diessg17 = [ 201, dfury_diessg18 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessg18 = [ 202, dfury_diessg19 ]
{
};

void() dfury_diessg19 = [ 203, dfury_diessg20 ]
{
};

void() dfury_diessg20 = [ 204, dfury_diessg21 ]
{
};

void() dfury_diessg21 = [ 205, dfury_diessg22 ]
{
	self.solid = 0;
};

void() dfury_diessg22 = [ 206, dfury_diessg23 ]
{
};

void() dfury_diessg23 = [ 207, dfury_diessg24 ]
{
};

void() dfury_diessg24 = [ 208, dfury_diessg25 ]
{
	sound(self, CHAN_AUTO, "dfury/fall.wav", 1, ATTN_IDLE);
};

void() dfury_diessg25 = [ 209, dfury_diessg26 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessg26 = [ 210, dfury_diessg27 ]
{
};

void() dfury_diessg27 = [ 211, dfury_diessg28 ]
{
};

void() dfury_diessg28 = [ 212, dfury_diessg28 ]
{
};

void() dfury_diessgb1 = [ 213, dfury_diessgb2 ]
{
};

void() dfury_diessgb2 = [ 214, dfury_diessgb3 ]
{
	sound(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
	}
};

void() dfury_diessgb3 = [ 215, dfury_diessgb4 ]
{
};

void() dfury_diessgb4 = [ 216, dfury_diessgb5 ]
{
	self.solid = 0;
	sound(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE);
};

void() dfury_diessgb5 = [ 217, dfury_diessgb6 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessgb6 = [ 218, dfury_diessgb7 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessgb7 = [ 219, dfury_diessgb8 ]
{
	sound(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE);
};

void() dfury_diessgb8 = [ 220, dfury_diessgb9 ]
{
	ai_forward(8);
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessgb9 = [ 221, dfury_diessgb10 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() dfury_diessgb10 = [ 222, dfury_diessgb11 ]
{
};

void() dfury_diessgb11 = [ 223, dfury_diessgb12 ]
{
};

void() dfury_diessgb12 = [ 224, dfury_diessgb12 ]
{
};

void() dfury_dieb1 = [ 51, dfury_dieb2 ]
{
	self.colormod = '1 1 1';
};

void() dfury_dieb2 = [ 52, dfury_dieb3 ]
{
};

void() dfury_dieb3 = [ 53, dfury_dieb4 ]
{
	self.solid = 0;
};

void() dfury_dieb4 = [ 54, dfury_dieb5 ]
{
};

void() dfury_dieb5 = [ 55, dfury_dieb6 ]
{
};

void() dfury_dieb6 = [ 56, dfury_dieb7 ]
{
	sound(self, CHAN_AUTO, "dfury/fall.wav", 1, ATTN_IDLE);
};

void() dfury_dieb7 = [ 57, dfury_dieb8 ]
{
};

void() dfury_dieb8 = [ 58, dfury_dieb9 ]
{
};

void() dfury_dieb9 = [ 59, dfury_dieb10 ]
{
};

void() dfury_dieb10 = [ 60, dfury_dieb11 ]
{
};

void() dfury_dieb11 = [ 61, dfury_dieb12 ]
{
};

void() dfury_dieb12 = [ 62, dfury_dieb13 ]
{
};

void() dfury_dieb13 = [ 63, dfury_dieb14 ]
{
};

void() dfury_dieb14 = [ 64, dfury_dieb14 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 21;
	if ((autocvar_dfurycorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_dfurycorpsehealth, "progs/h_hellkn.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_dfurycorpsehealth, "progs/h_hellkn1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_dfuryrandomness = autocvar_dfuryrandomness * 0.01;
		if ((autocvar_dfury == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_dfuryrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_dfury == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_dfuryrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/dfury.mdl", 59, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/dfury1.mdl", 59, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_dfury == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_dfuryrandomness))
					{
						vengeance_dfury("progs/dfury.mdl", 59);
					}
				}
				else
				{
					if ((autocvar_dfury == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_dfuryrandomness))
						{
							zufall = random();
							if ((zufall > 0.64))
							{
								ghost_die();
							}
							else
							{
								if ((zufall < 0.26))
								{
									if ((self.monstermodel == 0))
									{
										soul("progs/dfury.mdl", 59, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/dfury1.mdl", 59, zet);
										}
									}
								}
								else
								{
								}
							}
						}
					}
					else
					{
					}
				}
			}
		}
	}
	else
	{
		if ((self.grimrock_helper == 1))
		{
			zufall = random();
			if ((zufall > 0.64))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.26))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/dfury.mdl", 59, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/dfury1.mdl", 59, zet);
						}
					}
				}
			}
		}
	}
};

void(float maxgibs, float gibscounter) producegibs_dfury =
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

void() dfury_lightning_death = [ 34, dfury_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() dfury_lightning_death1 = [ 34, dfury_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(1, "progs/h_hellkn.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(1, "progs/h_hellkn1.mdl");
	}
};

void() dfury_inflamed1 = [ 23, dfury_inflamed2 ]
{
	local float r;

	ai_run_inflamed(20);
	self.nextthink = (time + 0.09);
	r = random();
	if ((r < 0.3))
	{
		sound(self, CHAN_VOICE, "dfury/grunt.wav", 1, ATTN_NORM);
	}
	else
	{
		if ((r < 0.82))
		{
			sound(self, CHAN_VOICE, "dfury/pain2.wav", 1, ATTN_NORM);
		}
	}
};

void() dfury_inflamed2 = [ 24, dfury_inflamed3 ]
{
	ai_run_inflamed(25);
	dfury_footsteps(1);
	self.nextthink = (time + 0.09);
};

void() dfury_inflamed3 = [ 25, dfury_inflamed4 ]
{
	ai_run_inflamed(18);
	self.nextthink = (time + 0.09);
};

void() dfury_inflamed4 = [ 26, dfury_inflamed5 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.09);
};

void() dfury_inflamed5 = [ 27, dfury_inflamed6 ]
{
	ai_run_inflamed(14);
	self.nextthink = (time + 0.09);
};

void() dfury_inflamed6 = [ 28, dfury_inflamed7 ]
{
	ai_run_inflamed(25);
	dfury_footsteps(0.8);
	self.nextthink = (time + 0.09);
};

void() dfury_inflamed7 = [ 29, dfury_inflamed8 ]
{
	ai_run_inflamed(21);
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		dfury_die();
		return;
	}
	if ((random() < 0.5))
	{
		dfury_inflamed9();
	}
};

void() dfury_inflamed8 = [ 30, dfury_inflamed1 ]
{
	ai_run_inflamed(13);
	self.nextthink = (time + 0.09);
};

void() dfury_inflamed9 = [ 29, dfury_inflamed10 ]
{
	local float r;

	self.nextthink = (time + 0.09);
	r = random();
	if ((r < 0.3))
	{
		sound(self, CHAN_VOICE, "dfury/grunt.wav", 1, ATTN_NORM);
	}
	else
	{
		if ((r < 0.82))
		{
			sound(self, CHAN_VOICE, "dfury/pain2.wav", 1, ATTN_NORM);
		}
	}
};

void() dfury_inflamed10 = [ 30, dfury_inflamed11 ]
{
	self.nextthink = (time + 0.09);
};

void() dfury_inflamed11 = [ 31, dfury_inflamed12 ]
{
	self.nextthink = (time + 0.09);
};

void() dfury_inflamed12 = [ 32, dfury_inflamed13 ]
{
	self.nextthink = (time + 0.09);
};

void() dfury_inflamed13 = [ 33, dfury_inflamed8 ]
{
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		dfury_die();
		return;
	}
};

void() dfury_die =
{
	local float maxgibs;
	local float gibscounter;
	local float zufa;
	local float zufall;
	local float randomness;

	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			dfury_lightning_death();
			return;
		}
	}
	if ((self.health < -40))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		self.colormod = '1 1 1';
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_dfury * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		play_gibsound();
		if ((self.monstermodel == 0))
		{
			ThrowHead("progs/h_hellkn.mdl", self.health);
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				ThrowHead("progs/h_hellkn1.mdl", self.health);
			}
		}
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		if ((autocvar_bloodextension == 1))
		{
			pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
		}
		producegibs_dfury(maxgibs, gibscounter);
		return;
	}
	if (autocvar_burning_monsters_death_animation)
	{
		if ((self.inflamed == 0))
		{
			zufa = random() * 100;
			if ((((((self.enemy.weapon == IT_GRENADE_LAUNCHER) || (self.enemy.weapon == IT_ROCKET_LAUNCHER)) && (zufa <= autocvar_burning_monsters_death_animation)) && (self.watertype != CONTENT_WATER)) && (self.enemy.meleeing == 0)))
			{
				self.delete_painskin = 1;
				self.inflamed = 1;
				self.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
				self.inflametime = ((time + autocvar_burning_monsters_death_animation_time) + random());
				dfury_inflamed1();
				return;
			}
		}
		else
		{
			sound(self, CHAN_VOICE, "dfury/death2.wav", 1, ATTN_NORM);
			if ((random() > 0.5))
			{
				dfury_die1();
			}
			else
			{
				dfury_dieb1();
			}
			return;
		}
	}
	autocvar_dfuryrandomness = autocvar_dfuryrandomness * 0.01;
	if ((autocvar_dfury == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_dfuryrandomness))
		{
			self.delete_painskin = 1;
			dfury_dieburn1();
			return;
		}
	}
	if ((autocvar_dfury == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_dfuryrandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				dfury_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_dfury * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound(self, CHAN_VOICE, "dfury/death1.wav", 1, ATTN_NORM);
	if ((random() > 0.5))
	{
		dfury_die1();
	}
	else
	{
		dfury_dieb1();
	}
};

void() dfury_magica1 = [ 81, dfury_magica2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1.5 1 1';
};

void() dfury_magica2 = [ 82, dfury_magica3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() dfury_magica3 = [ 83, dfury_magica4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2.5 1 1';
};

void() dfury_magica4 = [ 84, dfury_magica5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3 1 1';
};

void() dfury_magica5 = [ 85, dfury_magica6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3.5 1 1';
};

void() dfury_magica6 = [ 86, dfury_magica7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() dfury_magica7 = [ 87, dfury_magica8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magica8 = [ 88, dfury_magica9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magica9 = [ 89, dfury_magica10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_shot(-2);
	dfury_shot(0);
	dfury_shot(2);
};

void() dfury_magica10 = [ 90, dfury_magica11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magica11 = [ 91, dfury_magica12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magica12 = [ 92, dfury_magica13 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	self.colormod = '3 1 1';
};

void() dfury_magica13 = [ 93, dfury_magica14 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() dfury_magica14 = [ 94, dfury_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1 1 1';
	dfury_random_magic();
};

void() dfury_magicb1 = [ 95, dfury_magicb2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1.5 1 1';
};

void() dfury_magicb2 = [ 96, dfury_magicb3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() dfury_magicb3 = [ 97, dfury_magicb4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2.5 1 1';
};

void() dfury_magicb4 = [ 98, dfury_magicb5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3 1 1';
};

void() dfury_magicb5 = [ 99, dfury_magicb6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3.5 1 1';
};

void() dfury_magicb6 = [ 100, dfury_magicb7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() dfury_magicb7 = [ 101, dfury_magicb8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magicb8 = [ 102, dfury_magicb9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magicb9 = [ 103, dfury_magicb10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_shot(-1);
	dfury_shot(0);
	dfury_shot(1);
};

void() dfury_magicb10 = [ 104, dfury_magicb11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magicb11 = [ 105, dfury_magicb12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magicb12 = [ 106, dfury_magicb13 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	self.colormod = '2 1 1';
};

void() dfury_magicb13 = [ 107, dfury_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1 1 1';
	dfury_random_magic();
};

void() dfury_magicc1 = [ 159, dfury_magicc2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1.5 1 1';
};

void() dfury_magicc2 = [ 160, dfury_magicc3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() dfury_magicc3 = [ 161, dfury_magicc4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2.5 1 1';
};

void() dfury_magicc4 = [ 162, dfury_magicc5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3 1 1';
};

void() dfury_magicc5 = [ 163, dfury_magicc6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3.5 1 1';
};

void() dfury_magicc6 = [ 164, dfury_magicc7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magicc7 = [ 165, dfury_magicc8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magicc8 = [ 166, dfury_magicc9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dfury_shot(-3);
	dfury_shot(-1);
	dfury_shot(1);
	dfury_shot(3);
};

void() dfury_magicc9 = [ 167, dfury_magicc10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dfury_magicc10 = [ 168, dfury_magicc11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	self.colormod = '2 1 1';
};

void() dfury_magicc11 = [ 169, dfury_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	self.colormod = '1 1 1';
	dfury_random_magic();
};

void() dfury_char_a1 = [ 65, dfury_char_a2 ]
{
	ai_charge(30);
	self.colormod = '1 1 1';
};

void() dfury_char_a2 = [ 66, dfury_char_a3 ]
{
	ai_charge(35);
	dfury_footsteps(0.9);
};

void() dfury_char_a3 = [ 67, dfury_char_a4 ]
{
	ai_charge(28);
	if ((random() > 0.3))
	{
		dfury_jump1();
	}
};

void() dfury_char_a4 = [ 68, dfury_char_a5 ]
{
	ai_charge(26);
};

void() dfury_char_a5 = [ 69, dfury_char_a6 ]
{
	ai_charge(24);
};

void() dfury_char_a6 = [ 70, dfury_char_a7 ]
{
	ai_charge(30);
	ai_melee_dfury();
	dfury_footsteps(0.9);
};

void() dfury_char_a7 = [ 71, dfury_char_a8 ]
{
	ai_charge(31);
	ai_melee_dfury();
};

void() dfury_char_a8 = [ 72, dfury_char_a9 ]
{
	ai_charge(33);
	ai_melee_dfury();
};

void() dfury_char_a9 = [ 73, dfury_char_a10 ]
{
	ai_charge(30);
	ai_melee_dfury();
	dfury_footsteps(0.9);
};

void() dfury_char_a10 = [ 74, dfury_char_a11 ]
{
	ai_charge(30);
	ai_melee_dfury();
};

void() dfury_char_a11 = [ 75, dfury_char_a12 ]
{
	ai_charge(28);
	ai_melee_dfury();
};

void() dfury_char_a12 = [ 76, dfury_char_a13 ]
{
	ai_charge(26);
};

void() dfury_char_a13 = [ 77, dfury_char_a14 ]
{
	ai_charge(24);
	dfury_footsteps(0.9);
};

void() dfury_char_a14 = [ 78, dfury_char_a15 ]
{
	ai_charge(35);
};

void() dfury_char_a15 = [ 79, dfury_char_a16 ]
{
	ai_charge(31);
};

void() dfury_char_a16 = [ 80, dfury_run1 ]
{
	ai_charge(23);
};

void() dfury_char_b1 = [ 108, dfury_char_b2 ]
{
	CheckContinueCharge3();
	ai_charge(23);
	ai_melee_dfury();
	self.colormod = '1 1 1';
};

void() dfury_char_b2 = [ 109, dfury_char_b3 ]
{
	ai_charge(27);
	ai_melee_dfury();
};

void() dfury_char_b3 = [ 110, dfury_char_b4 ]
{
	ai_charge(22);
	ai_melee_dfury();
};

void() dfury_char_b4 = [ 111, dfury_char_b5 ]
{
	ai_charge(32);
	ai_melee_dfury();
	dfury_footsteps(0.9);
};

void() dfury_char_b5 = [ 112, dfury_char_b6 ]
{
	ai_charge(28);
	ai_melee_dfury();
};

void() dfury_char_b6 = [ 113, dfury_char_b1 ]
{
	ai_charge(8);
	ai_melee_dfury();
};

void() dfury_slice1 = [ 114, dfury_slice2 ]
{
	ai_charge(19);
	self.colormod = '1 1 1';
};

void() dfury_slice2 = [ 115, dfury_slice3 ]
{
	ai_charge(16);
};

void() dfury_slice3 = [ 116, dfury_slice4 ]
{
	ai_charge(23);
	dfury_footsteps(0.8);
};

void() dfury_slice4 = [ 117, dfury_slice5 ]
{
	ai_charge(14);
};

void() dfury_slice5 = [ 118, dfury_slice6 ]
{
	ai_charge(17);
	ai_melee_dfury();
};

void() dfury_slice6 = [ 119, dfury_slice7 ]
{
	ai_charge(25);
	ai_melee_dfury();
};

void() dfury_slice7 = [ 120, dfury_slice8 ]
{
	ai_charge(18);
	ai_melee_dfury();
	dfury_footsteps(0.8);
};

void() dfury_slice8 = [ 121, dfury_slice9 ]
{
	ai_charge(12);
	ai_melee_dfury();
};

void() dfury_slice9 = [ 122, dfury_slice10 ]
{
	ai_melee_dfury();
};

void() dfury_slice10 = [ 123, dfury_slice11 ]
{
	ai_charge(14);
	ai_melee_dfury();
};

void() dfury_slice11 = [ 124, dfury_slice12 ]
{
	ai_charge(14);
	ai_melee_dfury();
};

void() dfury_slice12 = [ 125, dfury_slice13 ]
{
	ai_charge(14);
	ai_melee_dfury();
};

void() dfury_slice13 = [ 126, dfury_slice14 ]
{
	ai_charge(14);
	ai_melee_dfury();
};

void() dfury_slice14 = [ 127, dfury_run1 ]
{
	ai_charge(13);
};

void() dfury_smash1 = [ 128, dfury_smash2 ]
{
	ai_charge(1);
	self.colormod = '1 1 1';
};

void() dfury_smash2 = [ 129, dfury_smash3 ]
{
	ai_charge(23);
};

void() dfury_smash3 = [ 130, dfury_smash4 ]
{
	ai_charge(9);
};

void() dfury_smash4 = [ 131, dfury_smash5 ]
{
	ai_charge(21);
	dfury_footsteps(0.8);
};

void() dfury_smash5 = [ 132, dfury_smash6 ]
{
	ai_charge(20);
	ai_melee_dfury();
};

void() dfury_smash6 = [ 133, dfury_smash7 ]
{
	ai_charge(7);
	ai_melee_dfury();
};

void() dfury_smash7 = [ 134, dfury_smash8 ]
{
	ai_charge(22);
	ai_melee_dfury();
};

void() dfury_smash8 = [ 135, dfury_smash9 ]
{
	ai_charge(2);
	ai_melee_dfury();
};

void() dfury_smash9 = [ 136, dfury_smash10 ]
{
	ai_charge(3);
	ai_melee_dfury();
	dfury_footsteps(0.8);
};

void() dfury_smash10 = [ 137, dfury_smash11 ]
{
	ai_charge(0);
};

void() dfury_smash11 = [ 138, dfury_smash12 ]
{
	ai_charge(0);
};

void() dfury_smash12 = [ 139, dfury_smash13 ]
{
	ai_charge(0);
};

void() dfury_smash13 = [ 140, dfury_smash14 ]
{
	ai_charge(0);
};

void() dfury_smash14 = [ 141, dfury_smash15 ]
{
	ai_charge(0);
};

void() dfury_smash15 = [ 142, dfury_run1 ]
{
	ai_charge(0);
};

void() dfury_watk1 = [ 143, dfury_watk2 ]
{
	ai_charge(2);
	self.colormod = '1 1 1';
};

void() dfury_watk2 = [ 144, dfury_watk3 ]
{
	ai_charge(0);
};

void() dfury_watk3 = [ 145, dfury_watk4 ]
{
	ai_charge(0);
};

void() dfury_watk4 = [ 146, dfury_watk5 ]
{
	ai_melee_dfury();
};

void() dfury_watk5 = [ 147, dfury_watk6 ]
{
	ai_melee_dfury();
};

void() dfury_watk6 = [ 148, dfury_watk7 ]
{
	ai_melee_dfury();
};

void() dfury_watk7 = [ 149, dfury_watk8 ]
{
	ai_charge(1);
	ai_melee_dfury();
};

void() dfury_watk8 = [ 150, dfury_watk9 ]
{
	ai_charge(4);
	ai_melee_dfury();
};

void() dfury_watk9 = [ 151, dfury_watk10 ]
{
	ai_charge(5);
};

void() dfury_watk10 = [ 152, dfury_watk11 ]
{
	ai_charge(3);
	ai_melee_dfury();
};

void() dfury_watk11 = [ 153, dfury_watk12 ]
{
	ai_charge(2);
	ai_melee_dfury();
	dfury_footsteps(0.8);
};

void() dfury_watk12 = [ 154, dfury_watk13 ]
{
	ai_charge(2);
	ai_melee_dfury();
};

void() dfury_watk13 = [ 155, dfury_watk14 ]
{
	ai_charge(0);
};

void() dfury_watk14 = [ 156, dfury_watk15 ]
{
	ai_charge(0);
	ai_melee_dfury();
};

void() dfury_watk15 = [ 157, dfury_watk16 ]
{
	ai_charge(0);
	ai_melee_dfury();
};

void() dfury_watk16 = [ 158, dfury_run1 ]
{
	ai_charge(3);
	dfury_footsteps(0.8);
};

void() df_idle_sound =
{
	if ((random() < 0.2))
	{
		sound(self, CHAN_VOICE, "dfury/idle.wav", 1, ATTN_NORM);
	}
};

void(entity attacker, float damage) dfury_pain =
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
		dfury_pain1();
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
	dfury_pain1();
};

void() dfury_melee =
{
	dfury_type = dfury_type + 1;
	sound(self, CHAN_WEAPON, "dfury/slash1.wav", 1, ATTN_NORM);
	if ((dfury_type == 1))
	{
		dfury_slice1();
	}
	else
	{
		if ((dfury_type == 2))
		{
			dfury_smash1();
		}
		else
		{
			if ((dfury_type == 3))
			{
				dfury_watk1();
				dfury_type = 0;
			}
		}
	}
};

void() dfury_random_magic =
{
	local float zufall;

	zufall = random();
	if ((zufall > 0.66))
	{
		self.th_missile = dfury_magica1;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.th_missile = dfury_magicb1;
		}
		else
		{
			self.th_missile = dfury_magicc1;
		}
	}
};

void() dfury_JumpTouch =
{
	local float ldmg;

	if ((self.health <= 0))
	{
		return;
	}
	if (other.takedamage)
	{
		if ((vlen(self.velocity) > 400))
		{
			if ((autocvar_dfury_size_influenced_attack == 1))
			{
				ldmg = (autocvar_dfury_jump * self.scale) + (10 * random());
			}
			else
			{
				ldmg = autocvar_dfury_jump + (10 * random());
			}
			if ((self.enemy.classname == "monster_knight"))
			{
				T_Damage(other, self, self, ldmg);
			}
		}
	}
	if (!checkbottom(self))
	{
		self.tail_visible = 0;
		if ((self.flags & FL_ONGROUND))
		{
			self.touch = SUB_Null;
			if ((self.monstermodel == 2))
			{
				self.think = teneb_jump1;
			}
			else
			{
				self.think = dfury_jump1;
			}
			self.nextthink = (time + 0.1);
		}
		return;
	}
	self.touch = SUB_Null;
	if ((self.monstermodel == 2))
	{
		self.think = teneb_jump7;
	}
	else
	{
		self.think = dfury_jump11;
	}
	self.nextthink = (time + 0.1);
};

void() monster_dfury =
{
	local float zufall;
	local float zuffa;
	local entity pain_skin_entity;
	local float replace;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model2("progs/dfury.mdl");
	precache_model2("progs/k_spike.mdl");
	precache_model2("progs/h_hellkn.mdl");
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
	precache_sound("dfury/fall.wav");
	precache_sound("walk/dfury1.wav");
	precache_sound("walk/dfury2.wav");
	precache_sound("walk/dfury3.wav");
	precache_sound("knight/dropsword.wav");
	precache_sound("knight/sword1.wav");
	precache_sound("knight/sword2.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((autocvar_dfurymultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/dfury.mdl");
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
					setmodel(self, "progs/dfury.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/dfury.mdl");
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
						setmodel(self, "progs/dfury.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/dfury.mdl");
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
					setmodel(self, "progs/dfury.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_dfury_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.14;
			self.sizediff = '0 0 3';
			setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.07;
				self.sizediff = '0 0 1';
				setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
			}
			else
			{
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 40');
			}
		}
	}
	else
	{
		if ((autocvar_dfury_size == 2))
		{
			self.scale = 1;
			setsize(self, '-26 -26 -24', '26 26 70');
		}
		else
		{
			if ((autocvar_dfury_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.28;
					self.sizediff = '0 0 7';
					setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.21;
						self.sizediff = '0 0 5';
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.14;
							self.sizediff = '0 0 3';
							setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.07;
								self.sizediff = '0 0 1';
								setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
							}
							else
							{
								self.scale = 1;
								setsize(self, VEC_HULL_MIN, '16 16 40');
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_dfury_size == 4))
				{
					zuffa = random();
					if ((zuffa <= 0.17))
					{
						self.scale = 1.35;
						self.sizediff = '0 0 9';
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.34))
						{
							self.scale = 1.28;
							self.sizediff = '0 0 7';
							setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.5))
							{
								self.scale = 1.21;
								self.sizediff = '0 0 5';
								setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
							}
							else
							{
								if ((zuffa <= 0.67))
								{
									self.scale = 1.14;
									self.sizediff = '0 0 3';
									setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
								}
								else
								{
									if ((zuffa <= 0.84))
									{
										self.scale = 1.07;
										self.sizediff = '0 0 1';
										setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
									}
									else
									{
										self.scale = 1;
										setsize(self, VEC_HULL_MIN, '16 16 40');
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_dfury_size > 4))
					{
						if ((autocvar_dfury_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_dfury_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_dfury_size * 0.25);
						self.sizediff = self.sizefactor;
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, VEC_HULL_MIN, '16 16 40');
					}
				}
			}
		}
	}
	if ((autocvar_dfury_size_influenced_health == 1))
	{
		self.health = (autocvar_dfury_health * self.scale);
	}
	else
	{
		self.health = autocvar_dfury_health;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_dfury_random_skin_colors))
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
	self.th_stand = dfury_stand1;
	self.th_walk = dfury_walk1;
	self.th_run = dfury_run1;
	self.th_melee = dfury_melee;
	self.th_missile = dfury_random_magic;
	self.th_pain = dfury_pain;
	self.th_die = dfury_die;
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
	do_the_cloning();
	if (autocvar_afrit_supports_dfury)
	{
		replace = autocvar_afrit_supports_dfury * 0.01;
		if ((random() <= replace))
		{
			add_afrit_support_walk();
		}
	}
	MonsterPhysics(self, autocvar_dfurymass);
};

void() vengeance_dfury_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_dfury_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_dfury_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_skull =
{
	local vector offang;
	local vector org;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = ((self.origin + self.mins) + (self.size * 0.5)) + (v_forward * 20);
	launch_vengeance_skull(org);
	newmis.classname = "skull";
	setmodel(newmis, "progs/skull.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	newmis.scale = 0.9;
	precache_sound("vengeance/skull.wav");
	precache_sound("vengeance/skulltouch.wav");
};

void() vengeance_dfury_run1 = [ 23, vengeance_dfury_run2 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_run2 = [ 24, vengeance_dfury_run3 ]
{
	ai_face();
	movetogoal(24);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.37;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_run3 = [ 25, vengeance_dfury_run4 ]
{
	ai_face();
	movetogoal(17);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.34;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_run4 = [ 26, vengeance_dfury_run5 ]
{
	ai_face();
	movetogoal(15);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.31;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_run5 = [ 27, vengeance_dfury_run6 ]
{
	ai_face();
	movetogoal(13);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.28;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_run6 = [ 28, vengeance_dfury_run7 ]
{
	ai_face();
	movetogoal(24);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.25;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_run7 = [ 29, vengeance_dfury_random ]
{
	ai_face();
	movetogoal(20);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.22;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_chara1 = [ 65, vengeance_dfury_chara2 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_chara2 = [ 66, vengeance_dfury_chara3 ]
{
	ai_face();
	movetogoal(24);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.17;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_chara3 = [ 67, vengeance_dfury_chara4 ]
{
	ai_face();
	movetogoal(17);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.14;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_chara4 = [ 68, vengeance_dfury_chara5 ]
{
	ai_face();
	movetogoal(15);
	self.touch = vengeance_dfury_touch;
	sound(self, CHAN_VOICE, "dfury/slash1.wav", 1, 4);
	self.alpha = 0.11;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_chara5 = [ 69, vengeance_dfury_chara6 ]
{
	ai_face();
	movetogoal(13);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.08;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_chara6 = [ 70, vengeance_dfury_end1 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_dfury_touch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 130) + '0 0 10');
	self.alpha = 0.05;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_skull1 = [ 82, vengeance_dfury_skull2 ]
{
	ai_face();
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_skull2 = [ 83, vengeance_dfury_skull3 ]
{
	sound(self, CHAN_VOICE, "vengeance/dfurymag.wav", 0.8, ATTN_NORM);
	ai_face();
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_skull3 = [ 84, vengeance_dfury_skull4 ]
{
	ai_face();
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_skull4 = [ 85, vengeance_dfury_skull5 ]
{
	ai_face();
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_skull5 = [ 86, vengeance_dfury_skull6 ]
{
	ai_face();
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_skull6 = [ 85, vengeance_dfury_skull7 ]
{
	ai_face();
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_skull7 = [ 88, vengeance_dfury_skull8 ]
{
	ai_face();
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.15;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_skull8 = [ 88, vengeance_dfury_end1 ]
{
	ai_face();
	movetogoal(2);
	self.touch = vengeance_dfury_touch;
	self.alpha = 0.1;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	vengeance_dfury_skull();
};

void() vengeance_dfury_random =
{
	self.alpha = 0.22;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.01);
	if ((random() > 0.45))
	{
		self.think = vengeance_dfury_chara1;
	}
	else
	{
		self.think = vengeance_dfury_skull1;
	}
};

void() vengeance_dfury11 = [ 44, vengeance_dfury12 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury12 = [ 43, vengeance_dfury13 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury13 = [ 42, vengeance_dfury14 ]
{
	walkmove((self.angles_y + 180), 11);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury14 = [ 41, vengeance_dfury15 ]
{
	walkmove((self.angles_y + 180), 10);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury15 = [ 40, vengeance_dfury16 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury16 = [ 39, vengeance_dfury17 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury17 = [ 38, vengeance_dfury18 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury18 = [ 37, vengeance_dfury19 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury19 = [ 36, vengeance_dfury110 ]
{
	sound(self, CHAN_WEAPON, "dfury/sight1.wav", 1, ATTN_NORM);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury110 = [ 35, vengeance_dfury111 ]
{
	walkmove((self.angles_y + 180), 8);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury111 = [ 34, vengeance_dfury_stand1 ]
{
	walkmove((self.angles_y + 180), 10);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_stand1 = [ 30, vengeance_dfury_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury21 = [ 58, vengeance_dfury22 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury22 = [ 57, vengeance_dfury23 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury23 = [ 56, vengeance_dfury24 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury24 = [ 55, vengeance_dfury25 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury25 = [ 54, vengeance_dfury26 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury26 = [ 53, vengeance_dfury27 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury27 = [ 52, vengeance_dfury28 ]
{
	sound(self, CHAN_WEAPON, "dfury/sight1.wav", 1, ATTN_NORM);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury28 = [ 51, vengeance_dfury_stand2 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_stand2 = [ 0, vengeance_dfury_stand21 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_stand21 = [ 30, vengeance_dfury_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dfury_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	if ((self.frame == 45))
	{
		self.think = vengeance_dfury11;
	}
	else
	{
		self.think = vengeance_dfury21;
	}
};

void() vengeance_dfury_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_dfury_bright05;
};

void() vengeance_dfury_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_dfury_bright04;
};

void() vengeance_dfury_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_dfury_bright03;
};

void() vengeance_dfury_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_dfury_bright02;
};

void() vengeance_dfury_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_dfury_bright01;
};

void(string modelname, float modelframe) vengeance_dfury =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_FLY;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/dfury.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/dfury1.mdl");
		}
	}
	setsize(self, VEC_HULL_MIN, '16 16 40');
	self.frame = modelframe;
	self.solid = 0;
	vengeance_dfury_bright00();
};
