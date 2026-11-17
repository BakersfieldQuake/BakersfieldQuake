//Decompiled code. Please respect the original copyright.

void(float offset) hknight_shot =
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
	newmis.classname = "knightspike";
	setmodel(newmis, "progs/k_spike.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	if ((skill == 3))
	{
		newmis.velocity = (vec * 375);
	}
	else
	{
		newmis.velocity = (vec * 300);
	}
	sound7(self, CHAN_WEAPON, "hknight/attack1.wav", 1, ATTN_NORM, SNDSPD);
};

void() CheckForCharge =
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
	hknight_char_a1();
};

void() CheckContinueCharge =
{
	if ((time > self.attack_finished))
	{
		SUB_AttackFinished(3);
		hknight_run1();
		return;
	}
	if ((random() > 0.5))
	{
		sound7(self, CHAN_WEAPON, "knight/sword2.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_WEAPON, "knight/sword1.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void(float loudness) hknight_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.33))
		{
			sound7(self, CHAN_AUTO, "walk/hknight1.wav", loudness, ATTN_IDLE, SNDSPD);
		}
		else
		{
			if ((select <= 0.66))
			{
				sound7(self, CHAN_AUTO, "walk/hknight2.wav", loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_AUTO, "walk/hknight3.wav", loudness, ATTN_IDLE, SNDSPD);
			}
		}
	}
};

void() hknight_stand1 = [ 0, hknight_stand2 ]
{
	ai_stand();
	self.colormod = '1 1 1';
};

void() hknight_stand2 = [ 1, hknight_stand3 ]
{
	ai_stand();
};

void() hknight_stand3 = [ 2, hknight_stand4 ]
{
	ai_stand();
};

void() hknight_stand4 = [ 3, hknight_stand5 ]
{
	ai_stand();
};

void() hknight_stand5 = [ 4, hknight_stand6 ]
{
	ai_stand();
};

void() hknight_stand6 = [ 5, hknight_stand7 ]
{
	ai_stand();
};

void() hknight_stand7 = [ 6, hknight_stand8 ]
{
	ai_stand();
};

void() hknight_stand8 = [ 7, hknight_stand9 ]
{
	ai_stand();
};

void() hknight_stand9 = [ 8, hknight_stand1 ]
{
	ai_stand();
};

void() hknight_walk1 = [ 9, hknight_walk2 ]
{
	hk_idle_sound();
	ai_walk(2);
	self.colormod = '1 1 1';
	hknight_footsteps(0.8);
};

void() hknight_walk2 = [ 10, hknight_walk3 ]
{
	ai_walk(5);
};

void() hknight_walk3 = [ 11, hknight_walk4 ]
{
	ai_walk(5);
};

void() hknight_walk4 = [ 12, hknight_walk5 ]
{
	ai_walk(4);
};

void() hknight_walk5 = [ 13, hknight_walk6 ]
{
	ai_walk(4);
};

void() hknight_walk6 = [ 14, hknight_walk7 ]
{
	ai_walk(2);
};

void() hknight_walk7 = [ 15, hknight_walk8 ]
{
	ai_walk(2);
};

void() hknight_walk8 = [ 16, hknight_walk9 ]
{
	ai_walk(3);
};

void() hknight_walk9 = [ 17, hknight_walk10 ]
{
	ai_walk(3);
};

void() hknight_walk10 = [ 18, hknight_walk11 ]
{
	ai_walk(4);
};

void() hknight_walk11 = [ 19, hknight_walk12 ]
{
	ai_walk(3);
	hknight_footsteps(0.8);
};

void() hknight_walk12 = [ 20, hknight_walk13 ]
{
	ai_walk(4);
};

void() hknight_walk13 = [ 21, hknight_walk14 ]
{
	ai_walk(6);
};

void() hknight_walk14 = [ 22, hknight_walk1 ]
{
	ai_walk(2);
};

void() hknight_run1 = [ 23, hknight_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	hk_idle_sound();
	ai_run((20 + (skill * 0.35)));
	CheckForCharge();
	self.colormod = '1 1 1';
};

void() hknight_run2 = [ 24, hknight_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((25 + (skill * 0.35)));
	hknight_footsteps(1);
};

void() hknight_run3 = [ 25, hknight_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((18 + (skill * 0.35)));
};

void() hknight_run4 = [ 26, hknight_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((16 + (skill * 0.35)));
};

void() hknight_run5 = [ 27, hknight_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((14 + (skill * 0.35)));
};

void() hknight_run6 = [ 28, hknight_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((25 + (skill * 0.35)));
	hknight_footsteps(0.8);
};

void() hknight_run7 = [ 29, hknight_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((21 + (skill * 0.35)));
};

void() hknight_run8 = [ 30, hknight_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((13 + (skill * 0.35)));
};

void() hknight_pain1 = [ 31, hknight_pain2 ]
{
	sound7(self, CHAN_VOICE, "hknight/pain1.wav", 1, ATTN_NORM, SNDSPD);
	self.colormod = '1 1 1';
};

void() hknight_pain2 = [ 32, hknight_pain3 ]
{
};

void() hknight_pain3 = [ 33, hknight_pain4 ]
{
};

void() hknight_pain4 = [ 34, hknight_pain5 ]
{
};

void() hknight_pain5 = [ 35, hknight_run1 ]
{
};

void() hknight_dieburn1 = [ 48, hknight_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
};

void() hknight_dieburn2 = [ 49, hknight_dieburn3 ]
{
	self.burnz_origin = 10;
};

void() hknight_dieburn3 = [ 50, hknight_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
};

void() hknight_dieburn4 = [ 51, hknight_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() hknight_dieburn5 = [ 52, hknight_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() hknight_dieburn6 = [ 53, hknight_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() hknight_dieburn7 = [ 54, hknight_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() hknight_dieburn8 = [ 55, hknight_dieburn9 ]
{
	self.burnz_origin = -6;
};

void() hknight_dieburn9 = [ 56, hknight_dieburn9 ]
{
	self.burnz_origin = -8;
};

void() hknight_die1 = [ 36, hknight_die2 ]
{
	ai_forward(10);
	if ((self.colormod != '0.2 0.2 0.2'))
	{
		self.colormod = '1 1 1';
	}
};

void() hknight_die2 = [ 37, hknight_die3 ]
{
	ai_forward(8);
};

void() hknight_die3 = [ 38, hknight_die4 ]
{
	self.solid = 0;
	ai_forward(7);
};

void() hknight_die4 = [ 39, hknight_die5 ]
{
};

void() hknight_die5 = [ 40, hknight_die6 ]
{
};

void() hknight_die6 = [ 41, hknight_die7 ]
{
};

void() hknight_die7 = [ 42, hknight_die8 ]
{
};

void() hknight_die8 = [ 43, hknight_die9 ]
{
	ai_forward(10);
};

void() hknight_die9 = [ 44, hknight_die10 ]
{
	ai_forward(11);
	sound7(self, CHAN_AUTO, "hknight/fall.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_die10 = [ 45, hknight_die11 ]
{
};

void() hknight_die11 = [ 46, hknight_die12 ]
{
};

void() hknight_die12 = [ 47, hknight_die12 ]
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
	if ((autocvar_hknightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_hknightcorpsehealth, "progs/h_hellkn.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_hknightcorpsehealth, "progs/h_hellkn1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_hknightrandomness = autocvar_hknightrandomness * 0.01;
		if ((autocvar_hknight == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_hknightrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_hknight == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_hknightrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/hknight.mdl", 47, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/hknight1.mdl", 47, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_hknight == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_hknightrandomness))
					{
						vengeance_hknight("progs/hknight.mdl", 47);
					}
				}
				else
				{
					if ((autocvar_hknight == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_hknightrandomness))
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
										soul("progs/hknight.mdl", 47, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/hknight1.mdl", 47, zet);
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
			if ((zufall > 0.84))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.2))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/hknight.mdl", 47, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/hknight1.mdl", 47, zet);
						}
					}
				}
				else
				{
					vengeance_hknight("progs/hknight.mdl", 47);
				}
			}
		}
	}
};

void() hknight_diessg1 = [ 160, hknight_diessg2 ]
{
	ai_forward(5);
	self.health = -1;
	self.takedamage = DAMAGE_YES;
};

void() hknight_diessg2 = [ 161, hknight_diessg3 ]
{
	ai_forward(5);
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_diessg3 = [ 162, hknight_diessg4 ]
{
	ai_forward(5);
};

void() hknight_diessg4 = [ 163, hknight_diessg5 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_diessg5 = [ 164, hknight_diessg6 ]
{
	self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
};

void() hknight_diessg6 = [ 165, hknight_diessg7 ]
{
	ai_melee_hknight();
};

void() hknight_diessg7 = [ 166, hknight_diessg8 ]
{
	ai_melee_hknight();
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_diessg8 = [ 167, hknight_diessg9 ]
{
	ai_melee_hknight();
};

void() hknight_diessg9 = [ 168, hknight_diessg10 ]
{
	self.traileffectnum = particleeffectnum(/*1i*/"");
};

void() hknight_diessg10 = [ 169, hknight_diessg11 ]
{
};

void() hknight_diessg11 = [ 170, hknight_diessg12 ]
{
	ai_forward(8);
};

void() hknight_diessg12 = [ 171, hknight_diessg13 ]
{
	ai_forward(8);
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_diessg13 = [ 172, hknight_diessg14 ]
{
	ai_forward(8);
	self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
};

void() hknight_diessg14 = [ 173, hknight_diessg15 ]
{
	ai_forward(5);
};

void() hknight_diessg15 = [ 174, hknight_diessg16 ]
{
	ai_melee_hknight();
	ai_forward(3);
};

void() hknight_diessg16 = [ 175, hknight_diessg17 ]
{
	ai_melee_hknight();
};

void() hknight_diessg17 = [ 176, hknight_diessg18 ]
{
	ai_melee_hknight();
	self.traileffectnum = particleeffectnum(/*1i*/"");
};

void() hknight_diessg18 = [ 177, hknight_diessg19 ]
{
	ai_melee_hknight();
};

void() hknight_diessg19 = [ 178, hknight_diessg20 ]
{
};

void() hknight_diessg20 = [ 179, hknight_diessg21 ]
{
};

void() hknight_diessg21 = [ 180, hknight_diessg22 ]
{
	self.takedamage = 0;
	self.touch = SUB_Null;
	self.solid = 0;
};

void() hknight_diessg22 = [ 181, hknight_diessg23 ]
{
};

void() hknight_diessg23 = [ 182, hknight_diessg24 ]
{
};

void() hknight_diessg24 = [ 183, hknight_diessg25 ]
{
};

void() hknight_diessg25 = [ 184, hknight_diessg26 ]
{
};

void() hknight_diessg26 = [ 185, hknight_diessg27 ]
{
};

void() hknight_diessg27 = [ 186, hknight_diessg28 ]
{
};

void() hknight_diessg28 = [ 188, hknight_diessg28 ]
{
	sound7(self, CHAN_AUTO, "hknight/fall.wav", 1, ATTN_IDLE, SNDSPD);
	sendParticle("blood_spurt", (self.origin - '0 0 6'), VEC_ORIGIN, 1);
	if ((autocvar_hknightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	CopyMonsterToBodyQue(autocvar_hknightcorpsehealth, "progs/gib_hknight_larm.mdl");
};

void() hknight_diessgb1 = [ 188, hknight_diessgb2 ]
{
};

void() hknight_diessgb2 = [ 189, hknight_diessgb3 ]
{
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_blast", self.origin, VEC_ORIGIN, 1);
	}
};

void() hknight_diessgb3 = [ 190, hknight_diessgb4 ]
{
};

void() hknight_diessgb4 = [ 191, hknight_diessgb5 ]
{
	self.solid = 0;
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
	self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
};

void() hknight_diessgb5 = [ 192, hknight_diessgb6 ]
{
};

void() hknight_diessgb6 = [ 193, hknight_diessgb7 ]
{
};

void() hknight_diessgb7 = [ 194, hknight_diessgb8 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_diessgb8 = [ 195, hknight_diessgb9 ]
{
	ai_forward(8);
};

void() hknight_diessgb9 = [ 196, hknight_diessgb10 ]
{
	self.traileffectnum = particleeffectnum(/*1i*/"");
};

void() hknight_diessgb10 = [ 197, hknight_diessgb11 ]
{
};

void() hknight_diessgb11 = [ 198, hknight_diessgb12 ]
{
};

void() hknight_diessgb12 = [ 199, hknight_diessgb12 ]
{
	if ((autocvar_hknightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	CopyMonsterToBodyQue(autocvar_hknightcorpsehealth, "progs/gib_hknight_head.mdl");
};

void() hknight_diesnga1 = [ 188, hknight_diesnga2 ]
{
};

void() hknight_diesnga2 = [ 189, hknight_diesnga3 ]
{
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_blast", self.origin, VEC_ORIGIN, 1);
	}
};

void() hknight_diesnga3 = [ 190, hknight_diesnga4 ]
{
};

void() hknight_diesnga4 = [ 191, hknight_diesnga5 ]
{
	self.solid = 0;
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_diesnga5 = [ 192, hknight_diesnga6 ]
{
	self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
};

void() hknight_diesnga6 = [ 193, hknight_diesnga7 ]
{
};

void() hknight_diesnga7 = [ 194, hknight_diesnga8 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_diesnga8 = [ 195, hknight_diesnga9 ]
{
	ai_forward(8);
};

void() hknight_diesnga9 = [ 196, hknight_diesnga10 ]
{
	self.traileffectnum = particleeffectnum(/*1i*/"");
};

void() hknight_diesnga10 = [ 197, hknight_diesnga11 ]
{
};

void() hknight_diesnga11 = [ 198, hknight_diesnga12 ]
{
};

void() hknight_diesnga12 = [ 199, hknight_diesnga12 ]
{
	if ((autocvar_hknightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	CopyMonsterToBodyQue(autocvar_hknightcorpsehealth, "progs/gib3.mdl");
};

void() hknight_make_corpse =
{
	if ((autocvar_hknightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	CopyMonsterToBodyQue(autocvar_hknightcorpsehealth, "progs/gib_hknight_larm.mdl");
};

void() hknight_axdeth0 = [ 0, hknight_axdeth1 ]
{
};

void() hknight_axdeth1 = [ 1, hknight_axdeth2 ]
{
	self.solid = 0;
};

void() hknight_axdeth2 = [ 2, hknight_axdeth3 ]
{
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_axdeth3 = [ 3, hknight_axdeth4 ]
{
};

void() hknight_axdeth4 = [ 4, hknight_axdeth5 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_axdeth5 = [ 5, hknight_axdeth6 ]
{
	self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
};

void() hknight_axdeth6 = [ 6, hknight_axdeth7 ]
{
};

void() hknight_axdeth7 = [ 7, hknight_axdeth8 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_axdeth8 = [ 8, hknight_axdeth9 ]
{
};

void() hknight_axdeth9 = [ 9, hknight_axdeth10 ]
{
};

void() hknight_axdeth10 = [ 10, hknight_axdeth11 ]
{
};

void() hknight_axdeth11 = [ 11, hknight_axdeth12 ]
{
};

void() hknight_axdeth12 = [ 12, hknight_axdeth13 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_axdeth13 = [ 13, hknight_axdeth14 ]
{
};

void() hknight_axdeth14 = [ 14, hknight_axdeth15 ]
{
	self.traileffectnum = particleeffectnum(/*1i*/"");
};

void() hknight_axdeth15 = [ 15, hknight_axdeth16 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() hknight_axdeth16 = [ 16, hknight_axdeth17 ]
{
};

void() hknight_axdeth17 = [ 17, hknight_axdeth18 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() hknight_axdeth18 = [ 18, hknight_axdeth19 ]
{
};

void() hknight_axdeth19 = [ 19, hknight_axdeth20 ]
{
};

void() hknight_axdeth20 = [ 20, hknight_axdeth21 ]
{
	sound7(self, CHAN_AUTO, "hknight/fall.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_axdeth21 = [ 21, hknight_axdeth22 ]
{
};

void() hknight_axdeth22 = [ 22, hknight_axdeth23 ]
{
};

void() hknight_axdeth23 = [ 23, hknight_axdeth23 ]
{
	hknight_make_corpse();
};

void() hknight_dieb1 = [ 48, hknight_dieb2 ]
{
};

void() hknight_dieb2 = [ 49, hknight_dieb3 ]
{
};

void() hknight_dieb3 = [ 50, hknight_dieb4 ]
{
	self.solid = 0;
};

void() hknight_dieb4 = [ 51, hknight_dieb5 ]
{
};

void() hknight_dieb5 = [ 52, hknight_dieb6 ]
{
};

void() hknight_dieb6 = [ 53, hknight_dieb7 ]
{
	sound7(self, CHAN_AUTO, "hknight/fall.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight_dieb7 = [ 54, hknight_dieb8 ]
{
};

void() hknight_dieb8 = [ 55, hknight_dieb9 ]
{
};

void() hknight_dieb9 = [ 56, hknight_dieb9 ]
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
	if ((autocvar_hknightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_hknightcorpsehealth, "progs/h_hellkn.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_hknightcorpsehealth, "progs/h_hellkn1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_hknightrandomness = autocvar_hknightrandomness * 0.01;
		if ((autocvar_hknight == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_hknightrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_hknight == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_hknightrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/hknight.mdl", 56, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/hknight1.mdl", 56, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_hknight == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_hknightrandomness))
					{
						vengeance_hknight("progs/hknight.mdl", 56);
					}
				}
				else
				{
					if ((autocvar_hknight == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_hknightrandomness))
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
										soul("progs/hknight.mdl", 56, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/hknight1.mdl", 56, zet);
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
			if ((zufall > 0.8))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.26))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/hknight.mdl", 56, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/hknight1.mdl", 56, zet);
						}
					}
				}
				else
				{
					vengeance_hknight("progs/hknight.mdl", 56);
				}
			}
		}
	}
};

void(float maxgibs, float gibscounter) producegibs_hknight =
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
	producegibs_hknight(maxgibs, gibscounter);
};

void() hknight_lightning_death = [ 36, hknight_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() hknight_lightning_death1 = [ 36, hknight_lightning_death1 ]
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

void() hknight_inflamed1 = [ 23, hknight_inflamed2 ]
{
	local float r;

	ai_run_inflamed(20);
	self.nextthink = (time + 0.09);
	r = random();
	if ((r < 0.3))
	{
		sound7(self, CHAN_VOICE, "hknight/grunt.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.82))
		{
			sound7(self, CHAN_VOICE, "hknight/pain2.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() hknight_inflamed2 = [ 24, hknight_inflamed3 ]
{
	ai_run_inflamed(25);
	hknight_footsteps(1);
	self.nextthink = (time + 0.09);
};

void() hknight_inflamed3 = [ 25, hknight_inflamed4 ]
{
	ai_run_inflamed(18);
	self.nextthink = (time + 0.09);
};

void() hknight_inflamed4 = [ 26, hknight_inflamed5 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.09);
};

void() hknight_inflamed5 = [ 27, hknight_inflamed6 ]
{
	ai_run_inflamed(14);
	self.nextthink = (time + 0.09);
};

void() hknight_inflamed6 = [ 28, hknight_inflamed7 ]
{
	ai_run_inflamed(25);
	hknight_footsteps(0.8);
	self.nextthink = (time + 0.09);
};

void() hknight_inflamed7 = [ 29, hknight_inflamed8 ]
{
	ai_run_inflamed(21);
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		hknight_die();
		return;
	}
	if ((random() < 0.5))
	{
		hknight_inflamed9();
	}
};

void() hknight_inflamed8 = [ 30, hknight_inflamed1 ]
{
	ai_run_inflamed(13);
	self.nextthink = (time + 0.09);
};

void() hknight_inflamed9 = [ 31, hknight_inflamed10 ]
{
	local float r;

	self.nextthink = (time + 0.09);
	r = random();
	if ((r < 0.3))
	{
		sound7(self, CHAN_VOICE, "hknight/grunt.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.82))
		{
			sound7(self, CHAN_VOICE, "hknight/pain2.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() hknight_inflamed10 = [ 32, hknight_inflamed11 ]
{
	self.nextthink = (time + 0.09);
};

void() hknight_inflamed11 = [ 33, hknight_inflamed12 ]
{
	self.nextthink = (time + 0.09);
};

void() hknight_inflamed12 = [ 34, hknight_inflamed13 ]
{
	self.nextthink = (time + 0.09);
};

void() hknight_inflamed13 = [ 35, hknight_inflamed8 ]
{
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		hknight_die();
		return;
	}
};

void() hknight_die =
{
	local float maxgibs;
	local float gibscounter;
	local float cranf;
	local float zufa;
	local float zufall;
	local float randomness;

	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			hknight_lightning_death();
			return;
		}
	}
	else
	{
		if ((((!self.shocked && (self.enemy.weapon == IT_LIGHTNING)) && (self.enemy.meleeing == 0)) && (self.sticky != 1)))
		{
			lg_death1();
			return;
		}
	}
	if ((self.colormod != '0.2 0.2 0.2'))
	{
		self.colormod = '1 1 1';
	}
	if (((self.model == "progs/hknight_half.mdl") && (((self.health < -40) || ((random() < 0.15) && (self.health < -15))) || (self.enemy.weapon == IT_CHAINSAW))))
	{
		sendParticle("blood_saw", self.origin, VEC_ORIGIN, 1);
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 1, ATTN_NORM, SNDSPD);
		gibdeath_effects();
		ThrowGib("progs/gib_hknight_head.mdl", (self.health / 2));
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib2.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
		ThrowGib("progs/gib2.mdl", self.health);
		ThrowHeart("progs/gibheart.mdl", self.health);
		remove(self);
		return;
	}
	else
	{
		if ((self.model == "progs/hknight_half.mdl"))
		{
			cranf = random() * 0.1;
			sendParticle("blood_saw", self.origin, VEC_ORIGIN, 1);
			sound7(self, CHAN_VOICE, "hknight/death.wav", 1, ATTN_NORM, SNDSPD);
			ThrowBody("progs/gib_hknight_half.mdl", (self.health * cranf));
			remove(self);
			return;
		}
	}
	if ((self.health < -45))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_hknight * 0.01)))
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
		gibdeath_effects();
		producegibs_hknight(maxgibs, gibscounter);
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
				hknight_inflamed1();
				return;
			}
		}
		else
		{
			sound7(self, CHAN_VOICE, "hknight/death2.wav", 1, ATTN_NORM, SNDSPD);
			if ((random() > 0.5))
			{
				hknight_die1();
			}
			else
			{
				hknight_dieb1();
			}
			return;
		}
	}
	autocvar_hknightrandomness = autocvar_hknightrandomness * 0.01;
	if ((autocvar_hknight == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_hknightrandomness))
		{
			self.delete_painskin = 1;
			hknight_dieburn1();
			return;
		}
	}
	if ((autocvar_hknight == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_hknightrandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				hknight_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_hknight * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "hknight/death1.wav", 1, ATTN_NORM, SNDSPD);
	if ((random() > 0.5))
	{
		hknight_die1();
	}
	else
	{
		hknight_dieb1();
	}
	if ((self.enemy.meleeing == 0))
	{
		if ((random() < 0.05))
		{
			self.grimrock_helper = 1;
		}
		if (((self.enemy.weapon == IT_AXE) || (self.enemy.weapon == IT_CHAINSAW)))
		{
			if ((random() < 0.5))
			{
				if ((autocvar_bloodextension == 1))
				{
					sendParticle("blood_blast", self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/hknight_axe.mdl";
					setmodel(self, "progs/hknight_axe.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/hknight_axe.mdl";
					setmodel(self, "progs/hknight_axe.mdl");
					self.skin = 1;
				}
				hknight_axdeth0();
				ThrowGib("progs/chop.mdl", self.health);
			}
		}
		if (((((self.enemy.weapon == IT_SUPER_SHOTGUN) && (random() < 0.8)) || ((self.enemy.weapon == IT_SHOTGUN) && (random() < 0.5))) || ((self.enemy.weapon == IT_NAILGUN) && (random() < 0.6))))
		{
			if (((self.hitbox_pos == HEAD_SHOT) && (self.has_fired == 0)))
			{
				if ((autocvar_bloodextension == 1))
				{
					sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/hknightssg.mdl";
					setmodel(self, "progs/hknightssg.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/hknightssg.mdl";
					setmodel(self, "progs/hknightssg.mdl");
					self.skin = 1;
				}
				setsize(self, VEC_HULL_MIN, '16 16 40');
				hknight_diessg1();
				self.has_fired = 1;
				ThrowGib("progs/chop.mdl", self.health);
			}
			else
			{
				if ((((random() >= 0.4) && (random() <= 0.7)) && (self.enemy.weapon != IT_NAILGUN)))
				{
					if ((autocvar_bloodextension == 1))
					{
						sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					self.delete_painskin = 1;
					if ((self.skin == 0))
					{
						self.model = "progs/hknightssgb.mdl";
						setmodel(self, "progs/hknightssgb.mdl");
						self.skin = 0;
					}
					else
					{
						self.model = "progs/hknightssgb.mdl";
						setmodel(self, "progs/hknightssgb.mdl");
						self.skin = 1;
					}
					hknight_diessgb1();
					ThrowGib("progs/chop.mdl", self.health);
				}
				else
				{
					if ((self.enemy.weapon == IT_NAILGUN))
					{
					}
					else
					{
						if ((autocvar_bloodextension == 1))
						{
							sendParticle("blood_monster_gibsm", self.origin, VEC_ORIGIN, 1);
						}
						self.delete_painskin = 1;
						if ((self.skin == 0))
						{
							self.model = "progs/hknightblast.mdl";
							setmodel(self, "progs/hknightblast.mdl");
							self.skin = 0;
						}
						else
						{
							self.model = "progs/hknightblast.mdl";
							setmodel(self, "progs/hknightblast.mdl");
							self.skin = 1;
						}
						hknight_die1();
						ThrowHead("progs/gib_hknight_torso.mdl", self.health);
						ThrowGib("progs/gib_hknight_head.mdl", self.health);
						ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
						ThrowGib("progs/gib_hknight_larm.mdl", self.health);
						ThrowGib("progs/gib_knfoot_r.mdl", self.health);
						ThrowGib("progs/gib_knfoot_l.mdl", self.health);
						sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 1, ATTN_IDLE, SNDSPD);
						ThrowGib("progs/chop.mdl", self.health);
					}
				}
			}
		}
		if (((random() < 0.85) && ((self.enemy.weapon == IT_GRENADE_LAUNCHER) || (self.enemy.weapon == IT_ROCKET_LAUNCHER))))
		{
			if ((autocvar_bloodextension == 1))
			{
				sendParticle("blood_monster_gibsm", self.origin, VEC_ORIGIN, 1);
			}
			hknight_die1();
			ThrowHead("progs/gib_hknight_torso.mdl", self.health);
			ThrowGib("progs/gib_hknight_head.mdl", self.health);
			ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
			if ((random() < 0.5))
			{
				ThrowGib("progs/gib_hknight_larm.mdl", self.health);
			}
			else
			{
				ThrowWeapon("progs/w_dknightsword.mdl", self.health);
				ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
			}
			ThrowGib("progs/gib_knfoot_r.mdl", self.health);
			ThrowGib("progs/gib_knfoot_l.mdl", self.health);
			sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 1, ATTN_NORM, SNDSPD);
			ThrowGib("progs/chop.mdl", self.health);
			ThrowGib("progs/chop.mdl", self.health);
		}
		if (((self.enemy.weapon == IT_SUPER_NAILGUN) && (random() < 0.9)))
		{
			if ((((self.hitbox_pos == HEAD_SHOT) && (self.has_fired == 0)) && (random() < 0.9)))
			{
				if ((autocvar_bloodextension == 1))
				{
					sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/hknightssg.mdl";
					setmodel(self, "progs/hknightssg.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/hknightssg.mdl";
					setmodel(self, "progs/hknightssg.mdl");
					self.skin = 1;
				}
				setsize(self, VEC_HULL_MIN, '16 16 40');
				hknight_diessg1();
				self.has_fired = 1;
				ThrowGib("progs/chop.mdl", self.health);
			}
			else
			{
				if ((random() <= 0.6))
				{
					if ((autocvar_bloodextension == 1))
					{
						sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					if (((random() > 0.5) || (self.hitbox_pos == HEAD_SHOT)))
					{
						StickGib("progs/gib_hknight_headSNG.mdl", self.health);
						ThrowGib("progs/gib_hknight_torsoSNG.mdl", self.health);
					}
					else
					{
						ThrowGib("progs/gib_hknight_headSNG.mdl", self.health);
						StickGib("progs/gib_hknight_torsoSNG.mdl", self.health);
					}
					ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					self.delete_painskin = 1;
					if ((self.skin == 0))
					{
						self.model = "progs/hknightSNG.mdl";
						setmodel(self, "progs/hknightSNG.mdl");
						self.skin = 0;
					}
					else
					{
						self.model = "progs/hknightSNG.mdl";
						setmodel(self, "progs/hknightSNG.mdl");
						self.skin = 1;
					}
					hknight_diesnga1();
					sound7(self, CHAN_AUTO, "knight/dropsword.wav", 1, ATTN_IDLE, SNDSPD);
					ThrowWeapon("progs/w_dknightsword.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
				}
				else
				{
					if ((autocvar_bloodextension == 1))
					{
						sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					if ((random() > 0.5))
					{
						StickGib("progs/gib_hknight_torso_SNGb.mdl", self.health);
					}
					else
					{
						ThrowGib("progs/gib_hknight_torso_SNGb.mdl", self.health);
					}
					StickGib("progs/gib_hknight_headSNG.mdl");
					if ((random() > 0.5))
					{
						StickGib("progs/gib_hknight_rarm.mdl");
					}
					else
					{
						ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
					}
					ThrowGib("progs/chop.mdl", self.health);
					self.delete_painskin = 1;
					if ((self.skin == 0))
					{
						self.model = "progs/hknightSNG.mdl";
						setmodel(self, "progs/hknightSNG.mdl");
						self.skin = 0;
					}
					else
					{
						self.model = "progs/hknightSNG.mdl";
						setmodel(self, "progs/hknightSNG.mdl");
						self.skin = 1;
					}
					hknight_diesnga1();
					sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 1, ATTN_IDLE, SNDSPD);
					sound7(self, CHAN_AUTO, "knight/dropsword.wav", 1, ATTN_IDLE, SNDSPD);
					ThrowGib("progs/chop.mdl", self.health);
				}
			}
		}
	}
};

void() hknight_magica1 = [ 73, hknight_magica2 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1.5 1 1';
};

void() hknight_magica2 = [ 74, hknight_magica3 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() hknight_magica3 = [ 75, hknight_magica4 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2.5 1 1';
};

void() hknight_magica4 = [ 76, hknight_magica5 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3 1 1';
};

void() hknight_magica5 = [ 77, hknight_magica6 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3.5 1 1';
};

void() hknight_magica6 = [ 78, hknight_magica7 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() hknight_magica7 = [ 79, hknight_magica8 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(-2);
};

void() hknight_magica8 = [ 80, hknight_magica9 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(-1);
};

void() hknight_magica9 = [ 81, hknight_magica10 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(0);
};

void() hknight_magica10 = [ 82, hknight_magica11 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(1);
};

void() hknight_magica11 = [ 83, hknight_magica12 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(2);
};

void() hknight_magica12 = [ 84, hknight_magica13 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(3);
	self.colormod = '3 1 1';
};

void() hknight_magica13 = [ 85, hknight_magica14 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() hknight_magica14 = [ 86, hknight_run1 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1 1 1';
	hknight_random_magic();
};

void() hknight_magicb1 = [ 87, hknight_magicb2 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1.5 1 1';
};

void() hknight_magicb2 = [ 88, hknight_magicb3 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() hknight_magicb3 = [ 89, hknight_magicb4 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2.5 1 1';
};

void() hknight_magicb4 = [ 90, hknight_magicb5 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3 1 1';
};

void() hknight_magicb5 = [ 91, hknight_magicb6 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3.5 1 1';
};

void() hknight_magicb6 = [ 92, hknight_magicb7 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() hknight_magicb7 = [ 93, hknight_magicb8 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(-2);
};

void() hknight_magicb8 = [ 94, hknight_magicb9 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(-1);
};

void() hknight_magicb9 = [ 95, hknight_magicb10 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(0);
};

void() hknight_magicb10 = [ 96, hknight_magicb11 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(1);
};

void() hknight_magicb11 = [ 97, hknight_magicb12 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(2);
};

void() hknight_magicb12 = [ 98, hknight_magicb13 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(3);
	self.colormod = '2 1 1';
};

void() hknight_magicb13 = [ 99, hknight_run1 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1 1 1';
	hknight_random_magic();
};

void() hknight_magicc1 = [ 149, hknight_magicc2 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '1.5 1 1';
};

void() hknight_magicc2 = [ 150, hknight_magicc3 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2 1 1';
};

void() hknight_magicc3 = [ 151, hknight_magicc4 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '2.5 1 1';
};

void() hknight_magicc4 = [ 152, hknight_magicc5 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3 1 1';
};

void() hknight_magicc5 = [ 153, hknight_magicc6 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.colormod = '3.5 1 1';
};

void() hknight_magicc6 = [ 154, hknight_magicc7 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(-2);
};

void() hknight_magicc7 = [ 155, hknight_magicc8 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(-1);
};

void() hknight_magicc8 = [ 156, hknight_magicc9 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(0);
};

void() hknight_magicc9 = [ 157, hknight_magicc10 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(1);
};

void() hknight_magicc10 = [ 158, hknight_magicc11 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(2);
	self.colormod = '2 1 1';
};

void() hknight_magicc11 = [ 159, hknight_run1 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	hknight_shot(3);
	self.colormod = '1 1 1';
	hknight_random_magic();
};

void() hknight_char_a1 = [ 57, hknight_char_a2 ]
{
	ai_charge((20 + (skill * 0.35)));
	self.colormod = '1 1 1';
};

void() hknight_char_a2 = [ 58, hknight_char_a3 ]
{
	ai_charge((25 + (skill * 0.35)));
	hknight_footsteps(0.9);
};

void() hknight_char_a3 = [ 59, hknight_char_a4 ]
{
	ai_charge((18 + (skill * 0.35)));
};

void() hknight_char_a4 = [ 60, hknight_char_a5 ]
{
	ai_charge((16 + (skill * 0.35)));
};

void() hknight_char_a5 = [ 61, hknight_char_a6 ]
{
	ai_charge((14 + (skill * 0.35)));
};

void() hknight_char_a6 = [ 62, hknight_char_a7 ]
{
	ai_charge((20 + (skill * 0.35)));
	ai_melee_hknight();
	hknight_footsteps(0.9);
};

void() hknight_char_a7 = [ 63, hknight_char_a8 ]
{
	ai_charge((21 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_char_a8 = [ 64, hknight_char_a9 ]
{
	ai_charge((13 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_char_a9 = [ 65, hknight_char_a10 ]
{
	ai_charge((20 + (skill * 0.35)));
	ai_melee_hknight();
	hknight_footsteps(0.9);
};

void() hknight_char_a10 = [ 66, hknight_char_a11 ]
{
	ai_charge((20 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_char_a11 = [ 67, hknight_char_a12 ]
{
	ai_charge((18 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_char_a12 = [ 68, hknight_char_a13 ]
{
	ai_charge((16 + (skill * 0.35)));
};

void() hknight_char_a13 = [ 69, hknight_char_a14 ]
{
	ai_charge((14 + (skill * 0.35)));
	hknight_footsteps(0.9);
};

void() hknight_char_a14 = [ 70, hknight_char_a15 ]
{
	ai_charge((25 + (skill * 0.35)));
};

void() hknight_char_a15 = [ 71, hknight_char_a16 ]
{
	ai_charge((21 + (skill * 0.35)));
};

void() hknight_char_a16 = [ 72, hknight_run1 ]
{
	ai_charge((13 + (skill * 0.35)));
};

void() hknight_char_b1 = [ 100, hknight_char_b2 ]
{
	CheckContinueCharge();
	ai_charge(23);
	ai_melee_hknight();
	self.colormod = '1 1 1';
};

void() hknight_char_b2 = [ 101, hknight_char_b3 ]
{
	ai_charge((17 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_char_b3 = [ 102, hknight_char_b4 ]
{
	ai_charge((12 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_char_b4 = [ 103, hknight_char_b5 ]
{
	ai_charge((22 + (skill * 0.35)));
	ai_melee_hknight();
	hknight_footsteps(0.9);
};

void() hknight_char_b5 = [ 104, hknight_char_b6 ]
{
	ai_charge((18 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_char_b6 = [ 105, hknight_char_b1 ]
{
	ai_charge((8 + (skill * 0.2)));
	ai_melee_hknight();
};

void() hknight_slice1 = [ 106, hknight_slice2 ]
{
	ai_charge((9 + (skill * 0.2)));
	self.colormod = '1 1 1';
};

void() hknight_slice2 = [ 107, hknight_slice3 ]
{
	ai_charge((6 + (skill * 0.2)));
};

void() hknight_slice3 = [ 108, hknight_slice4 ]
{
	ai_charge((13 + (skill * 0.35)));
	hknight_footsteps(0.8);
};

void() hknight_slice4 = [ 109, hknight_slice5 ]
{
	ai_charge((4 + (skill * 0.2)));
};

void() hknight_slice5 = [ 110, hknight_slice6 ]
{
	ai_charge((7 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_slice6 = [ 111, hknight_slice7 ]
{
	ai_charge((15 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_slice7 = [ 112, hknight_slice8 ]
{
	ai_charge((8 + (skill * 0.3)));
	ai_melee_hknight();
	hknight_footsteps(0.8);
};

void() hknight_slice8 = [ 113, hknight_slice9 ]
{
	ai_charge((2 + (skill * 0.2)));
	ai_melee_hknight();
};

void() hknight_slice9 = [ 114, hknight_slice10 ]
{
	ai_melee_hknight();
};

void() hknight_slice10 = [ 115, hknight_run1 ]
{
	ai_charge((3 + (skill * 0.2)));
};

void() hknight_smash1 = [ 116, hknight_smash2 ]
{
	ai_charge((1 + (skill * 0.2)));
	self.colormod = '1 1 1';
};

void() hknight_smash2 = [ 117, hknight_smash3 ]
{
	ai_charge((13 + (skill * 0.35)));
};

void() hknight_smash3 = [ 118, hknight_smash4 ]
{
	ai_charge((9 + (skill * 0.3)));
};

void() hknight_smash4 = [ 119, hknight_smash5 ]
{
	ai_charge((11 + (skill * 0.35)));
	hknight_footsteps(0.8);
};

void() hknight_smash5 = [ 120, hknight_smash6 ]
{
	ai_charge((10 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_smash6 = [ 121, hknight_smash7 ]
{
	ai_charge((7 + (skill * 0.3)));
	ai_melee_hknight();
};

void() hknight_smash7 = [ 122, hknight_smash8 ]
{
	ai_charge((12 + (skill * 0.35)));
	ai_melee_hknight();
};

void() hknight_smash8 = [ 123, hknight_smash9 ]
{
	ai_charge((2 + (skill * 0.25)));
	ai_melee_hknight();
};

void() hknight_smash9 = [ 124, hknight_smash10 ]
{
	ai_charge((3 + (skill * 0.25)));
	ai_melee_hknight();
	hknight_footsteps(0.8);
};

void() hknight_smash10 = [ 125, hknight_smash11 ]
{
	ai_charge(0);
};

void() hknight_smash11 = [ 126, hknight_run1 ]
{
	ai_charge(0);
};

void() hknight_watk1 = [ 127, hknight_watk2 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(2);
	self.colormod = '1 1 1';
};

void() hknight_watk2 = [ 128, hknight_watk3 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(0);
};

void() hknight_watk3 = [ 129, hknight_watk4 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(0);
};

void() hknight_watk4 = [ 130, hknight_watk5 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_melee_hknight();
};

void() hknight_watk5 = [ 131, hknight_watk6 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_melee_hknight();
};

void() hknight_watk6 = [ 132, hknight_watk7 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_melee_hknight();
};

void() hknight_watk7 = [ 133, hknight_watk8 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(1);
};

void() hknight_watk8 = [ 134, hknight_watk9 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(4);
};

void() hknight_watk9 = [ 135, hknight_watk10 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(5);
};

void() hknight_watk10 = [ 136, hknight_watk11 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(3);
	ai_melee_hknight();
};

void() hknight_watk11 = [ 137, hknight_watk12 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(2);
	ai_melee_hknight();
	hknight_footsteps(0.8);
};

void() hknight_watk12 = [ 138, hknight_watk13 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(2);
	ai_melee_hknight();
};

void() hknight_watk13 = [ 139, hknight_watk14 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(0);
};

void() hknight_watk14 = [ 140, hknight_watk15 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(0);
};

void() hknight_watk15 = [ 141, hknight_watk16 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(0);
};

void() hknight_watk16 = [ 142, hknight_watk17 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(1);
};

void() hknight_watk17 = [ 143, hknight_watk18 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(1);
	ai_melee_hknight();
};

void() hknight_watk18 = [ 144, hknight_watk19 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(3);
	ai_melee_hknight();
};

void() hknight_watk19 = [ 145, hknight_watk20 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(4);
	ai_melee_hknight();
};

void() hknight_watk20 = [ 146, hknight_watk21 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(6);
};

void() hknight_watk21 = [ 147, hknight_watk22 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(7);
};

void() hknight_watk22 = [ 148, hknight_run1 ]
{
	self.nextthink = ((time + 0.1) - (skill * 0.01));
	ai_charge(3);
	hknight_footsteps(0.8);
};

void() hknight_crawl1 = [ 0, hknight_crawl2 ]
{
	ThrowBloodSplat('0 0 -10', (self.origin + '0 0 -20'), self);
	ai_walk(1);
	self.health = (self.health - 0.5);
	if ((self.health <= 0))
	{
		hknight_die();
		if ((self.target || self.killtarget))
		{
			activator = self.enemy;
			SUB_UseTargets();
		}
	}
};

void() hknight_crawl2 = [ 1, hknight_crawl3 ]
{
	ThrowBloodSplat('1 1 -10', (self.origin + '0 0 -20'), self);
	ai_walk(1);
};

void() hknight_crawl3 = [ 2, hknight_crawl4 ]
{
	ThrowBloodSplat('-1 -1 -10', (self.origin + '0 0 -20'), self);
	ai_walk(1);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "hknight/pain2.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() hknight_crawl4 = [ 3, hknight_crawl5 ]
{
	ai_walk(3);
};

void() hknight_crawl5 = [ 4, hknight_crawl6 ]
{
	ThrowBloodSplat('0 0 -10', (self.origin + '0 0 -20'), self);
	ai_walk(4);
};

void() hknight_crawl6 = [ 5, hknight_crawl7 ]
{
	ThrowBloodSplat('1 1 -10', (self.origin + '0 0 -20'), self);
	ai_walk(4);
};

void() hknight_crawl7 = [ 6, hknight_crawl8 ]
{
	ThrowBloodSplat('-1.5 -1.5 -10', (self.origin + '0 0 -20'), self);
	ai_walk(4);
};

void() hknight_crawl8 = [ 7, hknight_crawl1 ]
{
	ThrowBloodSplat('2 2 -10', (self.origin + '0 0 -20'), self);
	ai_walk(3);
};

void() hk_idle_sound =
{
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "hknight/idle.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void(entity attacker, float damage) hknight_pain =
{
	if ((((((attacker.meleeing == 0) && (((attacker.weapon == IT_ROCKET_LAUNCHER) || (attacker.weapon == IT_GRENADE_LAUNCHER)) || (attacker.weapon == IT_SUPER_SHOTGUN))) && ((random() * 100) < 14)) && (self.health <= 59)) && (damage > 40)))
	{
		self.colormod = '1 1 1';
		setmodel(self, "progs/hknight_half.mdl");
		setsize(self, ZOMB_MIN, '12 12 -7');
		sendParticle("blood_saw", self.origin, VEC_ORIGIN, 1);
		sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
		self.velocity = ('0 0 30' + (v_forward * 8));
		ThrowGib("progs/gib_knfoot_l.mdl", self.health);
		ThrowGib("progs/gib_knfoot_r.mdl", self.health);
		ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
		if ((random() < 0.4))
		{
			sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "player/udeath2.wav", 1, ATTN_NORM, SNDSPD);
		}
		ThrowWeapon("progs/w_dknightsword.mdl", self.health);
		self.traileffectnum = particleeffectnum(/*53029i*/"med_bloodtrail_TR");
		self.th_stand = hknight_crawl1;
		self.th_run = SUB_Null;
		self.th_melee = SUB_Null;
		self.th_pain = SUB_Null;
		self.th_missile = SUB_Null;
		self.health = 15;
		self.goalentity = world;
		self.th_stand();
		return;
	}
	if ((self.pain_finished > time))
	{
		return;
	}
	sound7(self, CHAN_VOICE, "hknight/pain1.wav", 1, ATTN_NORM, SNDSPD);
	if (((time - self.pain_finished) > 5))
	{
		if ((autocvar_slowmotion >= 4))
		{
			if ((random() <= (autocvar_slowmotion_randomness_hknight * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		hknight_pain1();
		self.pain_finished = (time + 1);
		return;
	}
	if (((random() * 30) > damage))
	{
		return;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_hknight * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	self.pain_finished = (time + 1);
	hknight_pain1();
};

void() hknight_melee =
{
	hknight_type = hknight_type + 1;
	sound7(self, CHAN_WEAPON, "hknight/slash1.wav", 1, ATTN_NORM, SNDSPD);
	if ((hknight_type == 1))
	{
		hknight_slice1();
	}
	else
	{
		if ((hknight_type == 2))
		{
			hknight_smash1();
		}
		else
		{
			if ((hknight_type == 3))
			{
				hknight_watk1();
				hknight_type = 0;
			}
		}
	}
};

void() hknight_random_magic =
{
	local float zufall;

	zufall = random();
	if ((zufall > 0.66))
	{
		self.th_missile = hknight_magica1;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.th_missile = hknight_magicb1;
		}
		else
		{
			self.th_missile = hknight_magicc1;
		}
	}
};

void() monster_hell_knight =
{
	local float zufall;
	local float zuffa;
	local float replacerr;
	local float replacerrrrr;
	local float replacerrr;
	local float replacerrrr;
	local float replacer;
	local vector check;
	local float replacez;
	local float replac;
	local entity pain_skin_entity;
	local float replacce;
	local float replace;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model2("progs/hknight.mdl");
	precache_model2("progs/hknight_half.mdl");
	precache_model2("progs/gib_hknight_half.mdl");
	precache_model2("progs/k_spike.mdl");
	precache_model2("progs/h_hellkn.mdl");
	precachegibs_knights();
	precache_sound2("hknight/attack1.wav");
	precache_sound2("hknight/death.wav");
	precache_sound2("hknight/death1.wav");
	precache_sound2("hknight/pain1.wav");
	precache_sound("hknight/death2.wav");
	precache_sound("hknight/pain2.wav");
	precache_sound2("hknight/sight1.wav");
	precache_sound("hknight/hit.wav");
	precache_sound2("hknight/slash1.wav");
	precache_sound2("hknight/idle.wav");
	precache_sound2("hknight/grunt.wav");
	precache_sound("hknight/fall.wav");
	precache_sound("walk/hknight1.wav");
	precache_sound("walk/hknight2.wav");
	precache_sound("walk/hknight3.wav");
	precache_sound("knight/dropsword.wav");
	precache_sound("knight/sword1.wav");
	precache_sound("knight/sword2.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((autocvar_hknightmultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/hknight.mdl");
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
		if ((autocvar_hknightmultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/hknight1.mdl");
			precache_model("progs/h_hellkn1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/hknight.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/hknight1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_hknightmultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/hknight1.mdl");
				precache_model("progs/h_hellkn1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/hknight.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/hknight.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/hknight1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_hknightmultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/hknight1.mdl");
					precache_model("progs/h_hellkn1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/hknight.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/hknight.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/hknight1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/hknight1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/hknight.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_hknight_size == 1))
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
		if ((autocvar_hknight_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.21;
				self.sizediff = '0 0 5';
				setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.14;
					self.sizediff = '0 0 3';
					setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.75))
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
		else
		{
			if ((autocvar_hknight_size == 3))
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
				if ((autocvar_hknight_size == 4))
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
					if ((autocvar_hknight_size > 4))
					{
						if ((autocvar_hknight_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_hknight_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_hknight_size * 0.25);
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
	if ((autocvar_hknight_size_influenced_health == 1))
	{
		self.health = (autocvar_hellknight_health * self.scale);
	}
	else
	{
		self.health = autocvar_hellknight_health;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_hknight_random_skin_colors))
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
	self.th_stand = hknight_stand1;
	self.th_walk = hknight_walk1;
	self.th_run = hknight_run1;
	self.th_melee = hknight_melee;
	self.th_missile = hknight_random_magic;
	self.th_pain = hknight_pain;
	self.th_die = hknight_die;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_warlord_replace_hknight)
	{
		replacerr = autocvar_warlord_replace_hknight * 0.01;
		if ((cvar("skill") == 3))
		{
			replacerr = replacerr + 0.01;
		}
		if ((cvar("quadreplacer") > 0))
		{
			replacerr = replacerr + 0.01;
		}
		if ((random() <= replacerr))
		{
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_hell_knight2_start();
			return;
		}
	}
	if (autocvar_carnivean_replace_hellknight)
	{
		replacerrrrr = autocvar_carnivean_replace_hellknight * 0.01;
		if ((random() <= replacerrrrr))
		{
			self.health = (autocvar_knight_health + 50);
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_carnivean_start();
			return;
		}
	}
	if (autocvar_torment_replace_hknight)
	{
		replacerrr = autocvar_torment_replace_hknight * 0.01;
		if ((random() <= replacerrr))
		{
			self.health = autocvar_hellknight_health;
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_torment_start();
			return;
		}
	}
	if (autocvar_yakman_replace_hellknight)
	{
		replacerrrr = autocvar_yakman_replace_hellknight * 0.01;
		if ((random() <= replacerrrr))
		{
			self.health = (autocvar_hellknight_health + 50);
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_yakman_start();
			return;
		}
	}
	if (autocvar_spider_replace_hknight)
	{
		replacer = autocvar_spider_replace_hknight * 0.01;
		if ((random() <= replacer))
		{
			check = (self.origin - '0 0 20') + '0 0 1';
			if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
			{
				self.skin = 5;
				self.health = autocvar_hellknight_health;
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 40');
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_spider_start();
				return;
			}
		}
	}
	if (autocvar_reiver_replace_hknight)
	{
		replacez = autocvar_reiver_replace_hknight * 0.01;
		if ((random() <= replacez))
		{
			self.health = autocvar_hellknight_health;
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_reiver_liftorigin_start();
			return;
		}
	}
	if (autocvar_afrit_replace_hknight)
	{
		replac = autocvar_afrit_replace_hknight * 0.01;
		if ((random() <= replac))
		{
			self.health = autocvar_hellknight_health;
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_afrit_liftorigin_start();
			return;
		}
	}
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
	if (autocvar_reiver_supports_hknight)
	{
		replacce = autocvar_reiver_supports_hknight * 0.01;
		if ((random() <= replacce))
		{
			add_reiver_support_walk();
		}
	}
	if (autocvar_afrit_supports_hknight)
	{
		replace = autocvar_afrit_supports_hknight * 0.01;
		if ((random() <= replace))
		{
			add_afrit_support_walk();
		}
	}
	MonsterPhysics(self, autocvar_hknightmass);
};

void() vengeance_hknight_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_hknight_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_hknight_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_skull =
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

void() vengeance_hknight_run1 = [ 23, vengeance_hknight_run2 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_run2 = [ 24, vengeance_hknight_run3 ]
{
	ai_face();
	movetogoal(27);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.37;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_run3 = [ 25, vengeance_hknight_run4 ]
{
	ai_face();
	movetogoal(22);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.34;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_run4 = [ 26, vengeance_hknight_run5 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.31;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_run5 = [ 27, vengeance_hknight_run6 ]
{
	ai_face();
	movetogoal(17);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.28;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_run6 = [ 28, vengeance_hknight_run7 ]
{
	ai_face();
	movetogoal(26);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.25;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_run7 = [ 29, vengeance_hknight_random ]
{
	ai_face();
	movetogoal(24);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.22;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_chara1 = [ 57, vengeance_hknight_chara2 ]
{
	ai_charge((17 + (skill * 0.35)));
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_hknight_chara2 = [ 58, vengeance_hknight_chara3 ]
{
	ai_charge((18 + (skill * 0.35)));
	if ((autocvar_quadreplacer > 0))
	{
		ai_melee_hknight();
	}
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.17;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_hknight_chara3 = [ 59, vengeance_hknight_chara4 ]
{
	ai_charge((11 + (skill * 0.35)));
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.14;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_hknight_chara4 = [ 60, vengeance_hknight_chara5 ]
{
	ai_charge((15 + (skill * 0.35)));
	if ((autocvar_quadreplacer > 0))
	{
		ai_melee_hknight();
	}
	self.touch = vengeance_hknight_touch;
	sound7(self, CHAN_VOICE, "hknight/slash1.wav", 1, 4);
	self.alpha = 0.11;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_hknight_chara5 = [ 61, vengeance_hknight_chara6 ]
{
	ai_charge((21 + (skill * 0.35)));
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.08;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_hknight_chara6 = [ 62, vengeance_hknight_end1 ]
{
	ai_charge((18 + (skill * 0.35)));
	if ((autocvar_quadreplacer > 0))
	{
		ai_melee_hknight();
	}
	self.touch = vengeance_hknight_touch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 130) + '0 0 10');
	self.alpha = 0.05;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_skull1 = [ 74, vengeance_hknight_skull2 ]
{
	ai_face();
	movetogoal(3);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.05);
};

void() vengeance_hknight_skull2 = [ 75, vengeance_hknight_skull3 ]
{
	sound7(self, CHAN_VOICE, "vengeance/hknightmag.wav", 0.8, ATTN_NORM, SNDSPD);
	ai_face();
	movetogoal(4);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.05);
};

void() vengeance_hknight_skull3 = [ 76, vengeance_hknight_skull4 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.05);
};

void() vengeance_hknight_skull4 = [ 77, vengeance_hknight_skull5 ]
{
	ai_face();
	movetogoal(13);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.05);
};

void() vengeance_hknight_skull5 = [ 78, vengeance_hknight_skull6 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.05);
};

void() vengeance_hknight_skull6 = [ 77, vengeance_hknight_skull7 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.05);
};

void() vengeance_hknight_skull7 = [ 80, vengeance_hknight_skull8 ]
{
	ai_face();
	movetogoal(15);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.15;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.05);
};

void() vengeance_hknight_skull8 = [ 80, vengeance_hknight_end1 ]
{
	ai_face();
	movetogoal(2);
	self.touch = vengeance_hknight_touch;
	self.alpha = 0.1;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.05);
	vengeance_hknight_skull();
};

void() vengeance_hknight_random =
{
	self.alpha = 0.22;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.01);
	self.think = vengeance_hknight_chara1;
};

void() vengeance_hknight11 = [ 46, vengeance_hknight12 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight12 = [ 45, vengeance_hknight13 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight13 = [ 44, vengeance_hknight14 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight14 = [ 43, vengeance_hknight15 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight15 = [ 42, vengeance_hknight16 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight16 = [ 41, vengeance_hknight17 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight17 = [ 40, vengeance_hknight18 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight18 = [ 39, vengeance_hknight19 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight19 = [ 38, vengeance_hknight110 ]
{
	sound7(self, CHAN_WEAPON, "hknight/sight1.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight110 = [ 37, vengeance_hknight111 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight111 = [ 36, vengeance_hknight_stand1 ]
{
	self.alpha = 0.4;
	ai_face();
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_stand1 = [ 30, vengeance_hknight_run1 ]
{
	self.alpha = 0.4;
	ai_face();
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	if ((vlen((self.enemy.origin - self.origin)) < 160))
	{
		self.think = vengeance_hknight_chara1;
	}
};

void() vengeance_hknight21 = [ 55, vengeance_hknight22 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight22 = [ 54, vengeance_hknight23 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight23 = [ 53, vengeance_hknight24 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight24 = [ 52, vengeance_hknight25 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight25 = [ 51, vengeance_hknight26 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight26 = [ 50, vengeance_hknight27 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight27 = [ 49, vengeance_hknight28 ]
{
	sound7(self, CHAN_WEAPON, "hknight/sight1.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight28 = [ 48, vengeance_hknight_stand2 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_stand2 = [ 0, vengeance_hknight_stand21 ]
{
	self.alpha = 0.4;
	ai_face();
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight_stand21 = [ 30, vengeance_hknight_run1 ]
{
	self.alpha = 0.4;
	ai_face();
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	if ((vlen((self.enemy.origin - self.origin)) < 150))
	{
		self.think = vengeance_hknight_chara1;
	}
};

void() vengeance_hknight_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	if ((self.frame == 47))
	{
		self.think = vengeance_hknight11;
	}
	else
	{
		self.think = vengeance_hknight21;
	}
};

void() vengeance_hknight_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_hknight_bright05;
};

void() vengeance_hknight_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_hknight_bright04;
};

void() vengeance_hknight_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_hknight_bright03;
};

void() vengeance_hknight_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_hknight_bright02;
};

void() vengeance_hknight_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_hknight_bright01;
};

void(string modelname, float modelframe) vengeance_hknight =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_STEP;
	self.inflamed = 0;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/hknight.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/hknight1.mdl");
		}
	}
	setsize(self, VEC_HULL_MIN, '16 16 40');
	self.frame = modelframe;
	self.solid = 0;
	MonsterPhysics(self, autocvar_hknightmass);
	vengeance_hknight_bright00();
};
