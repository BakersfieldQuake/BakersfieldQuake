//Decompiled code. Please respect the original copyright.

void(float offset) hknight2_shot =
{
	local vector offang;
	local vector org;
	local vector vec;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = (((self.origin + self.mins) + (self.size * 0.5)) + (v_up * 5)) + (v_forward * 20);
	vec = normalize(v_forward);
	launch_enemy_spike(org, vec);
	newmis.classname = "knight2spike";
	if (autocvar_warlord_spike_type)
	{
		setmodel(newmis, "progs/k_spike2.mdl");
	}
	else
	{
		setmodel(newmis, "progs/k_spike.mdl");
	}
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	newmis.traileffectnum = particleeffectnum(/*52258i*/"TR_WARLORDSPIKE");
	if ((skill == 3))
	{
		newmis.velocity = (vec * 375);
	}
	else
	{
		newmis.velocity = (vec * 300);
	}
	sound7(self, CHAN_WEAPON, "warlord/attack1.wav", 1, ATTN_NORM, SNDSPD);
};

void() CheckForCharge2 =
{

	if (!enemy_vis)
	{
		return;
	}
	if ((time < self.attack_finished))
	{
		return;
	}
	if ((fabs((self.origin_z - self.enemy.origin_z)) > 30))
	{
		return;
	}
	if (((vlen((self.origin - self.enemy.origin)) < 80) || (vlen((self.origin - self.enemy.origin)) > 170)))
	{
		return;
	}
	SUB_AttackFinished(2);
	hknight2_char_a1();
};

void() CheckContinueCharge2 =
{
	if ((time > self.attack_finished))
	{
		SUB_AttackFinished(2);
		hknight2_run1();
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

void(float loudness) hknight2_footsteps =
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

void() hknight2_stand1 = [ 0, hknight2_stand2 ]
{
	ai_stand();
	self.colormod = '1 1 1';
	self.nextthink = (time + 0.06);
};

void() hknight2_stand2 = [ 1, hknight2_stand3 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand3 = [ 2, hknight2_stand4 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand4 = [ 3, hknight2_stand5 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand5 = [ 4, hknight2_stand6 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "warlord/growl.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() hknight2_stand6 = [ 5, hknight2_stand7 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand7 = [ 6, hknight2_stand8 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand8 = [ 7, hknight2_stand9 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand9 = [ 8, hknight2_stand10 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand10 = [ 9, hknight2_stand11 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand11 = [ 10, hknight2_stand12 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand12 = [ 11, hknight2_stand13 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand13 = [ 12, hknight2_stand14 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand14 = [ 13, hknight2_stand15 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand15 = [ 14, hknight2_stand16 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand16 = [ 15, hknight2_stand17 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand17 = [ 16, hknight2_stand18 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand18 = [ 17, hknight2_stand19 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand19 = [ 18, hknight2_stand20 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand20 = [ 19, hknight2_stand21 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand21 = [ 20, hknight2_stand22 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand22 = [ 21, hknight2_stand23 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand23 = [ 22, hknight2_stand24 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand24 = [ 23, hknight2_stand25 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand25 = [ 24, hknight2_stand26 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand26 = [ 25, hknight2_stand27 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand27 = [ 26, hknight2_stand28 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand28 = [ 27, hknight2_stand29 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand29 = [ 28, hknight2_stand30 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand30 = [ 29, hknight2_stand31 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand31 = [ 30, hknight2_stand32 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand32 = [ 31, hknight2_stand33 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand33 = [ 32, hknight2_stand34 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand34 = [ 33, hknight2_stand35 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand35 = [ 34, hknight2_stand36 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand36 = [ 35, hknight2_stand37 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand37 = [ 36, hknight2_stand38 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand38 = [ 37, hknight2_stand39 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand39 = [ 38, hknight2_stand40 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand40 = [ 39, hknight2_stand41 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand41 = [ 40, hknight2_stand42 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_stand42 = [ 41, hknight2_stand1 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() hknight2_walk1 = [ 42, hknight2_walk2 ]
{
	if ((random() < 0.11))
	{
		sound7(self, CHAN_VOICE, "warlord/growl.wav", 1, ATTN_NORM, SNDSPD);
	}
	ai_walk(2);
	self.colormod = '1 1 1';
};

void() hknight2_walk2 = [ 43, hknight2_walk3 ]
{
	ai_walk(4);
};

void() hknight2_walk3 = [ 44, hknight2_walk4 ]
{
	ai_walk(5);
};

void() hknight2_walk4 = [ 45, hknight2_walk5 ]
{
	ai_walk(4);
	hknight2_footsteps(0.8);
};

void() hknight2_walk5 = [ 46, hknight2_walk6 ]
{
	ai_walk(4);
};

void() hknight2_walk6 = [ 47, hknight2_walk7 ]
{
	ai_walk(5);
};

void() hknight2_walk7 = [ 48, hknight2_walk8 ]
{
	ai_walk(5);
};

void() hknight2_walk8 = [ 49, hknight2_walk9 ]
{
	ai_walk(4);
};

void() hknight2_walk9 = [ 50, hknight2_walk10 ]
{
	ai_walk(5);
};

void() hknight2_walk10 = [ 51, hknight2_walk11 ]
{
	ai_walk(4);
	hknight2_footsteps(0.8);
};

void() hknight2_walk11 = [ 52, hknight2_walk12 ]
{
	ai_walk(5);
};

void() hknight2_walk12 = [ 53, hknight2_walk1 ]
{
	ai_walk(4);
};

void() hknight2_run1 = [ 54, hknight2_run2 ]
{
	self.nextthink = (time + 0.075);
	self.tail_visible = 1;
	if ((random() < 0.025))
	{
		sound7(self, CHAN_VOICE, "warlord/idle.wav", 1, ATTN_NORM, SNDSPD);
	}
	ai_run(20);
	if ((random() < 0.6))
	{
		CheckForCharge2();
	}
	self.colormod = '1 1 1';
};

void() hknight2_run2 = [ 55, hknight2_run3 ]
{
	self.nextthink = (time + 0.075);
	ai_run((24 + skill));
	hknight2_footsteps(1);
};

void() hknight2_run3 = [ 56, hknight2_run4 ]
{
	self.nextthink = (time + 0.075);
	ai_run((18 + skill));
};

void() hknight2_run4 = [ 57, hknight2_run5 ]
{
	self.nextthink = (time + 0.075);
	ai_run((16 + skill));
};

void() hknight2_run5 = [ 58, hknight2_run6 ]
{
	self.nextthink = (time + 0.075);
	ai_run((18 + skill));
};

void() hknight2_run6 = [ 59, hknight2_run7 ]
{
	self.nextthink = (time + 0.075);
	ai_run((25 + skill));
	hknight2_footsteps(1);
};

void() hknight2_run7 = [ 60, hknight2_run8 ]
{
	self.nextthink = (time + 0.075);
	ai_run((18 + skill));
};

void() hknight2_run8 = [ 61, hknight2_run1 ]
{
	self.nextthink = (time + 0.075);
	ai_run((13 + skill));
};

void() hknight2_pain1 = [ 62, hknight2_pain2 ]
{
	sound7(self, CHAN_VOICE, "warlord/pain2.wav", 1, ATTN_NORM, SNDSPD);
	self.colormod = '1 1 1';
};

void() hknight2_pain2 = [ 63, hknight2_pain3 ]
{
};

void() hknight2_pain3 = [ 64, hknight2_pain4 ]
{
};

void() hknight2_pain4 = [ 65, hknight2_pain5 ]
{
};

void() hknight2_pain5 = [ 66, hknight2_run1 ]
{
};

void() hknight2_painb1 = [ 67, hknight2_painb2 ]
{
	sound7(self, CHAN_VOICE, "warlord/pain1.wav", 1, ATTN_NORM, SNDSPD);
	self.colormod = '1 1 1';
};

void() hknight2_painb2 = [ 68, hknight2_painb3 ]
{
};

void() hknight2_painb3 = [ 69, hknight2_painb4 ]
{
};

void() hknight2_painb4 = [ 70, hknight2_run1 ]
{
};

void() hknight2_dieburn1 = [ 84, hknight2_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
};

void() hknight2_dieburn2 = [ 85, hknight2_dieburn3 ]
{
	self.burnz_origin = 10;
};

void() hknight2_dieburn3 = [ 86, hknight2_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
};

void() hknight2_dieburn4 = [ 87, hknight2_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() hknight2_dieburn5 = [ 88, hknight2_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() hknight2_dieburn6 = [ 89, hknight2_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() hknight2_dieburn7 = [ 90, hknight2_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() hknight2_dieburn8 = [ 91, hknight2_dieburn9 ]
{
	self.burnz_origin = -6;
};

void() hknight2_dieburn9 = [ 92, hknight2_dieburn9 ]
{
	self.burnz_origin = -8;
};

void() hknight2_ssgdie1 = [ 246, hknight2_ssgdie2 ]
{
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight2_ssgdie2 = [ 247, hknight2_ssgdie3 ]
{
};

void() hknight2_ssgdie3 = [ 248, hknight2_ssgdie4 ]
{
	self.solid = 0;
};

void() hknight2_ssgdie4 = [ 249, hknight2_ssgdie5 ]
{
};

void() hknight2_ssgdie5 = [ 250, hknight2_ssgdie6 ]
{
	sound7(self, CHAN_VOICE, "warlord/shielddrop.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight2_ssgdie6 = [ 251, hknight2_ssgdie7 ]
{
	ai_back(1);
};

void() hknight2_ssgdie7 = [ 252, hknight2_ssgdie8 ]
{
};

void() hknight2_ssgdie8 = [ 253, hknight2_ssgdie9 ]
{
};

void() hknight2_ssgdie9 = [ 254, hknight2_ssgdie10 ]
{
};

void() hknight2_ssgdie10 = [ 255, hknight2_ssgdie11 ]
{
};

void() hknight2_ssgdie11 = [ 256, hknight2_ssgdie12 ]
{
	sound7(self, CHAN_AUTO, "warlord/fall.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight2_ssgdie12 = [ 257, hknight2_ssgdie12 ]
{
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	if ((autocvar_warlordcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_warlordcorpsehealth, "progs/gib_warleg.mdl");
};

void() hknight2_naildie1 = [ 258, hknight2_naildie2 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight2_naildie2 = [ 259, hknight2_naildie3 ]
{
};

void() hknight2_naildie3 = [ 260, hknight2_naildie4 ]
{
	self.solid = 0;
};

void() hknight2_naildie4 = [ 261, hknight2_naildie5 ]
{
};

void() hknight2_naildie5 = [ 262, hknight2_naildie6 ]
{
};

void() hknight2_naildie6 = [ 263, hknight2_naildie7 ]
{
	ai_back(1);
};

void() hknight2_naildie7 = [ 264, hknight2_naildie8 ]
{
	sound7(self, CHAN_VOICE, "warlord/shielddrop.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight2_naildie8 = [ 265, hknight2_naildie9 ]
{
};

void() hknight2_naildie9 = [ 266, hknight2_naildie10 ]
{
};

void() hknight2_naildie10 = [ 267, hknight2_naildie11 ]
{
};

void() hknight2_naildie11 = [ 268, hknight2_naildie12 ]
{
};

void() hknight2_naildie12 = [ 269, hknight2_naildie13 ]
{
};

void() hknight2_naildie13 = [ 270, hknight2_naildie14 ]
{
	self.solid = 0;
};

void() hknight2_naildie14 = [ 271, hknight2_naildie15 ]
{
};

void() hknight2_naildie15 = [ 272, hknight2_naildie16 ]
{
};

void() hknight2_naildie16 = [ 273, hknight2_naildie17 ]
{
	ai_back(1);
};

void() hknight2_naildie17 = [ 274, hknight2_naildie18 ]
{
};

void() hknight2_naildie18 = [ 275, hknight2_naildie19 ]
{
	sound7(self, CHAN_AUTO, "warlord/fall.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
	}
};

void() hknight2_naildie19 = [ 276, hknight2_naildie19 ]
{
	if ((autocvar_warlordcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_warlordcorpsehealth, "progs/gib_warnail_t.mdl");
};

void() hknight2_sngdie1 = [ 258, hknight2_sngdie2 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight2_sngdie2 = [ 259, hknight2_sngdie3 ]
{
	sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight2_sngdie3 = [ 260, hknight2_sngdie4 ]
{
	self.solid = 0;
};

void() hknight2_sngdie4 = [ 261, hknight2_sngdie5 ]
{
};

void() hknight2_sngdie5 = [ 262, hknight2_sngdie6 ]
{
};

void() hknight2_sngdie6 = [ 263, hknight2_sngdie7 ]
{
	ai_back(1);
};

void() hknight2_sngdie7 = [ 264, hknight2_sngdie8 ]
{
	sound7(self, CHAN_AUTO, "warlord/shielddrop.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight2_sngdie8 = [ 265, hknight2_sngdie9 ]
{
};

void() hknight2_sngdie9 = [ 266, hknight2_sngdie10 ]
{
};

void() hknight2_sngdie10 = [ 267, hknight2_sngdie11 ]
{
};

void() hknight2_sngdie11 = [ 268, hknight2_sngdie12 ]
{
};

void() hknight2_sngdie12 = [ 269, hknight2_sngdie13 ]
{
};

void() hknight2_sngdie13 = [ 270, hknight2_sngdie14 ]
{
	self.solid = 0;
};

void() hknight2_sngdie14 = [ 271, hknight2_sngdie15 ]
{
};

void() hknight2_sngdie15 = [ 272, hknight2_sngdie16 ]
{
};

void() hknight2_sngdie16 = [ 273, hknight2_sngdie17 ]
{
	ai_back(1);
};

void() hknight2_sngdie17 = [ 274, hknight2_sngdie18 ]
{
};

void() hknight2_sngdie18 = [ 275, hknight2_sngdie19 ]
{
	sound7(self, CHAN_AUTO, "warlord/fall.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
	}
};

void() hknight2_sngdie19 = [ 276, hknight2_sngdie19 ]
{
	if ((autocvar_warlordcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_warlordcorpsehealth, "progs/gib_warleg1.mdl");
};

void() hknight2_die1 = [ 71, hknight2_die2 ]
{
	self.colormod = '1 1 1';
	self.nextthink = (time + 0.12);
};

void() hknight2_die2 = [ 72, hknight2_die3 ]
{
	self.nextthink = (time + 0.13);
};

void() hknight2_die3 = [ 73, hknight2_die4 ]
{
	self.solid = 0;
	ai_back(3);
};

void() hknight2_die4 = [ 74, hknight2_die5 ]
{
	ai_back(4);
};

void() hknight2_die5 = [ 75, hknight2_die6 ]
{
	ai_back(5);
};

void() hknight2_die6 = [ 76, hknight2_die7 ]
{
	ai_back(1);
	sound7(self, CHAN_AUTO, "warlord/fall.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight2_die7 = [ 77, hknight2_die8 ]
{
};

void() hknight2_die8 = [ 78, hknight2_die9 ]
{
};

void() hknight2_die9 = [ 79, hknight2_die10 ]
{
};

void() hknight2_die10 = [ 80, hknight2_die11 ]
{
};

void() hknight2_die11 = [ 81, hknight2_die12 ]
{
};

void() hknight2_die12 = [ 82, hknight2_die13 ]
{
	self.nextthink = (time + 0.03);
};

void() hknight2_die13 = [ 83, hknight2_die13 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	zet = 21;
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	if ((autocvar_warlordcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_warlordcorpsehealth, "progs/h_warlord.mdl");
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_warlordrandomness = autocvar_warlordrandomness * 0.01;
		if ((autocvar_warlord == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_warlordrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_warlord == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_warlordrandomness))
				{
					soul("progs/warlord.mdl", 83, zet);
				}
			}
			else
			{
				if ((autocvar_warlord == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_warlordrandomness))
					{
						vengeance_hknight2("progs/warlord.mdl", 83);
					}
				}
				else
				{
					if ((autocvar_warlord == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_warlordrandomness))
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
									soul("progs/warlord.mdl", 83, zet);
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
			if ((zufall > 0.9))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.1))
				{
					soul("progs/warlord.mdl", 83, zet);
				}
				else
				{
					vengeance_hknight2("progs/warlord.mdl", 83);
				}
			}
		}
	}
};

void() hknight2_dieb1 = [ 84, hknight2_dieb2 ]
{
	ai_back(5);
	self.colormod = '1 1 1';
};

void() hknight2_dieb2 = [ 85, hknight2_dieb3 ]
{
	ai_back(5);
};

void() hknight2_dieb3 = [ 86, hknight2_dieb4 ]
{
	ai_back(5);
	self.solid = 0;
};

void() hknight2_dieb4 = [ 87, hknight2_dieb5 ]
{
	ai_back(3);
};

void() hknight2_dieb5 = [ 88, hknight2_dieb6 ]
{
	sound7(self, CHAN_AUTO, "warlord/fall.wav", 1, ATTN_IDLE, SNDSPD);
};

void() hknight2_dieb6 = [ 89, hknight2_dieb7 ]
{
};

void() hknight2_dieb7 = [ 90, hknight2_dieb8 ]
{
};

void() hknight2_dieb8 = [ 91, hknight2_dieb9 ]
{
};

void() hknight2_dieb9 = [ 92, hknight2_dieb9 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	zet = 21;
	if ((autocvar_warlordcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_warlordcorpsehealth, "progs/h_warlord.mdl");
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_warlordrandomness = autocvar_warlordrandomness * 0.01;
		if ((autocvar_warlord == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_warlordrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_warlord == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_warlordrandomness))
				{
					soul("progs/warlord.mdl", 92, zet);
				}
			}
			else
			{
				if ((autocvar_warlord == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_warlordrandomness))
					{
						vengeance_hknight2("progs/warlord.mdl", 92);
					}
				}
				else
				{
					if ((autocvar_warlord == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_warlordrandomness))
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
									soul("progs/warlord.mdl", 92, zet);
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
			if ((zufall > 0.9))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.1))
				{
					if ((zufall < 0.004))
					{
						soul("progs/afrit.mdl", 64, 27.451);
					}
					else
					{
						soul("progs/warlord.mdl", 92, zet);
					}
				}
				else
				{
					vengeance_hknight2("progs/warlord.mdl", 92);
				}
			}
		}
	}
};

void(float maxgibs, float gibscounter) producegibs_hknight2 =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/w_wshield.mdl", self.health);
		ThrowGib("progs/gib_warleg.mdl", self.health);
		ThrowGib("progs/gib_warleg.mdl", self.health);
		ThrowGib("progs/gib_wararm.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_hknight2(maxgibs, gibscounter);
};

void() hknight2_lightning_death = [ 71, hknight2_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() hknight2_lightning_death1 = [ 71, hknight2_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	CopyMonsterToBodyQue(1, "progs/h_warlord.mdl");
};

void() hknight2_die =
{
	local entity item;
	local float maxgibs;
	local float gibscounter;
	local float zufall;
	local float randomness;

	self.touch = SUB_Null;
	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			hknight2_lightning_death();
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
	self.tail_visible = 0;
	if (((self.has_fired == 1) && (autocvar_slowmotion > 0)))
	{
		item = spawn();
		item.origin = (self.origin - '0 0 8');
		item.flags = FL_ITEM;
		item.solid = SOLID_TRIGGER;
		item.movetype = MOVETYPE_TOSS;
		item.think = item_artifact_timerune;
		item.nextthink = 0.000100;
		item.has_fired = 1;
		self.has_fired = 0;
	}
	else
	{
		if ((self.has_fired == 2))
		{
			item = spawn();
			item.origin = (self.origin - '0 0 8');
			item.flags = FL_ITEM;
			item.solid = SOLID_TRIGGER;
			item.movetype = MOVETYPE_TOSS;
			item.think = item_artifact_invulnerability2;
			item.nextthink = 0.000100;
			item.has_fired = 1;
			self.has_fired = 0;
		}
		else
		{
			if ((self.has_fired == 3))
			{
				item = spawn();
				item.origin = (self.origin - '0 0 8');
				item.flags = FL_ITEM;
				item.solid = SOLID_TRIGGER;
				item.movetype = MOVETYPE_TOSS;
				item.classname = "item_artifact_invisibility";
				item.think = item_artifact_invisibility;
				item.nextthink = 0.000100;
				item.has_fired = 1;
				self.has_fired = 0;
			}
		}
	}
	if ((self.health < -45))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_warlord * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		play_gibsound();
		ThrowHead("progs/h_warlord.mdl", self.health);
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		gibdeath_effects();
		producegibs_hknight2(maxgibs, gibscounter);
		return;
	}
	autocvar_warlordrandomness = autocvar_warlordrandomness * 0.01;
	if ((autocvar_warlord == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_warlordrandomness))
		{
			self.delete_painskin = 1;
			hknight2_dieburn1();
			return;
		}
	}
	if ((autocvar_warlord == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_warlordrandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				hknight2_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_warlord * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "warlord/death1.wav", 1, ATTN_NORM, SNDSPD);
	if ((random() > 0.5))
	{
		hknight2_die1();
	}
	else
	{
		hknight2_dieb1();
	}
	if ((self.enemy.meleeing == 0))
	{
		if (((self.enemy.weapon == IT_SUPER_SHOTGUN) || (self.enemy.weapon == IT_SHOTGUN)))
		{
			if ((((random() < 0.7) && (self.enemy.weapon == IT_SUPER_SHOTGUN)) || ((random() < 0.4) && (self.enemy.weapon == IT_SHOTGUN))))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/warlordblast.mdl";
					setmodel(self, "progs/warlordblast.mdl");
					self.skin = 0;
					ThrowGib("progs/h_warlordblast.mdl", self.health);
					ThrowGib("progs/gib_wararm.mdl", self.health);
				}
				else
				{
					self.model = "progs/warlordblast.mdl";
					setmodel(self, "progs/warlordblast.mdl");
					ThrowGib("progs/h_warlordblast1.mdl", self.health);
					ThrowGib("progs/gib_wararm.mdl", self.health);
					self.skin = 1;
				}
				hknight2_ssgdie1();
			}
		}
		if ((self.enemy.weapon == IT_NAILGUN))
		{
			if ((random() < 0.7))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/warlordnail.mdl";
					setmodel(self, "progs/warlordnail.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/warlordnail.mdl";
					setmodel(self, "progs/warlordnail.mdl");
					self.skin = 1;
				}
				hknight2_naildie1();
			}
		}
		if ((self.enemy.weapon == IT_SUPER_NAILGUN))
		{
			if ((random() < 0.7))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				StickGib("progs/gib_warnail_t.mdl");
				ThrowGib("progs/gib_warleg.mdl", self.health);
				ThrowGib("progs/w_wshield.mdl", self.health);
				ThrowWeapon("progs/w_wsword.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/warlord_supernail.mdl";
					setmodel(self, "progs/warlord_supernail.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/warlord_supernail.mdl";
					setmodel(self, "progs/warlord_supernail.mdl");
					self.skin = 1;
				}
				hknight2_sngdie1();
			}
		}
		setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	}
};

void() hknight2_minigrenade_explode =
{
	T_RadiusDamage(self, self.owner, autocvar_warlord_spike_grenade, self.owner);
	if ((autocvar_explosiondebris == 0))
	{
		if (other.health)
		{
			pointparticles(particleeffectnum(/*52287i*/"multigrenade_explosion_nodebris"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52319i*/"multigrenade_explosion"), self.origin, VEC_ORIGIN, 1);
		}
	}
	else
	{
		pointparticles(particleeffectnum(/*52319i*/"multigrenade_explosion"), self.origin, VEC_ORIGIN, 1);
	}
	sound7(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
	BecomeExplosion();
};

void(float offsetAngle) hknight2_minigrenade_launch =
{
	local entity missile;
	local float tempRand;

	missile = spawn();
	missile.owner = self.owner;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	missile.classname = "MiniGrenade";
	missile.v_angle = self.v_angle;
	missile.v_angle_y = (missile.v_angle_y + offsetAngle);
	makevectors(missile.v_angle);
	missile.velocity = ((v_forward * 100) + (v_up * 400));
	tempRand = (crandom() * 60) - 30;
	missile.velocity = (missile.velocity + (tempRand * v_forward));
	tempRand = (crandom() * 40) - 20;
	missile.velocity = (missile.velocity + (tempRand * v_right));
	tempRand = (crandom() * 60) - 30;
	missile.velocity = (missile.velocity + (tempRand * v_up));
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.touch = hknight2_multigrenade_touch;
	setmodel(missile, "progs/h_grenade2.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(missile, self.origin);
	missile.scale = 0.8;
	missile.nextthink = ((time + 1) + (crandom() * 0.5));
	missile.think = hknight2_minigrenade_explode;
};

void() hknight2_multigrenade_explode =
{
	hknight2_minigrenade_launch(0);
	hknight2_minigrenade_launch(72);
	hknight2_minigrenade_launch(144);
	hknight2_minigrenade_launch(216);
	hknight2_minigrenade_launch(288);
	remove(self);
};

void() hknight2_multigrenade_touch =
{
	if ((other == self.owner))
	{
		return;
	}
	if ((other.takedamage == DAMAGE_AIM))
	{
		hknight2_minigrenade_explode();
		return;
	}
	sound7(self, CHAN_WEAPON, "weapons/bounce.wav", 1, ATTN_NORM, SNDSPD);
	if ((self.velocity == VEC_ORIGIN))
	{
		self.avelocity = VEC_ORIGIN;
	}
};

void() hknight2_grenade_explode =
{
	T_RadiusDamage(self, self.owner, autocvar_warlord_grenade, world);
	sound7(self, CHAN_VOICE, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
	if ((autocvar_explosiondebris == 0))
	{
		if (other.health)
		{
			pointparticles(particleeffectnum(/*52287i*/"multigrenade_explosion_nodebris"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*26571i*/"grenade_explosion"), self.origin, VEC_ORIGIN, 1);
		}
	}
	else
	{
		pointparticles(particleeffectnum(/*26571i*/"grenade_explosion"), self.origin, VEC_ORIGIN, 1);
	}
	self.velocity = VEC_ORIGIN;
	self.touch = SUB_Null;
	setmodel(self, "progs/s_explod.spr");
	self.solid = 0;
	s_explode1();
};

void() hknight2_grenade_touch =
{
	if ((other == self.owner))
	{
		return;
	}
	if ((other.takedamage == DAMAGE_AIM))
	{
		hknight2_grenade_explode();
		return;
	}
	sound7(self, CHAN_VOICE, "weapons/bounce.wav", 1, ATTN_NORM, SNDSPD);
	if ((self.velocity == VEC_ORIGIN))
	{
		self.avelocity = VEC_ORIGIN;
	}
};

void() hknight2_throw =
{
	local vector distancedelta;
	local vector nozdistancedelta;
	local vector org;
	local vector follow;
	local entity missile;

	sound7(self, CHAN_WEAPON, "warlord/throw.wav", 1, ATTN_NORM, SNDSPD);
	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	makevectors(self.angles);
	org = ((self.origin + (v_right * 12)) + (v_up * 11)) + (v_forward * 20);
	follow = self.enemy.velocity * 0.2;
	distancedelta = (self.enemy.origin + follow) - org;
	nozdistancedelta = distancedelta;
	missile.velocity = normalize(distancedelta);
	missile.velocity = (missile.velocity * (400 + (random() * 200)));
	missile.velocity_z = ((missile.velocity_z + 150) + ((vlen(nozdistancedelta) * 0.22) * (1 + (0.3 * random()))));
	if (((vlen((self.enemy.origin - self.origin)) < 380) && (random() < 0.65)))
	{
		missile.velocity = (missile.velocity * 0.75);
	}
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.effects = 40;
	if ((autocvar_warlord_grenade_type == 2))
	{
		missile.touch = hknight2_multigrenade_touch;
		missile.nextthink = (time + 2.5);
		missile.think = hknight2_multigrenade_explode;
		setmodel(missile, "progs/h_grenade2.mdl");
	}
	else
	{
		missile.touch = hknight2_grenade_touch;
		missile.nextthink = (time + 2);
		missile.think = hknight2_grenade_explode;
		setmodel(missile, "progs/h_grenade1.mdl");
	}
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(missile, org);
	missile.scale = 1.2;
};

void() hknight2_throwgrenade1 = [ 196, hknight2_throwgrenade2 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
	self.colormod = '1 1 1';
};

void() hknight2_throwgrenade2 = [ 197, hknight2_throwgrenade3 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade3 = [ 198, hknight2_throwgrenade4 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade4 = [ 199, hknight2_throwgrenade5 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade5 = [ 200, hknight2_throwgrenade6 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade6 = [ 201, hknight2_throwgrenade7 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade7 = [ 202, hknight2_throwgrenade8 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade8 = [ 203, hknight2_throwgrenade9 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade9 = [ 204, hknight2_throwgrenade10 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade10 = [ 205, hknight2_throwgrenade11 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade11 = [ 206, hknight2_throwgrenade12 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade12 = [ 207, hknight2_throwgrenade13 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade13 = [ 208, hknight2_throwgrenade14 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade14 = [ 209, hknight2_throwgrenade15 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade15 = [ 210, hknight2_throwgrenade16 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade16 = [ 211, hknight2_throwgrenade17 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade17 = [ 212, hknight2_throwgrenade18 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade18 = [ 213, hknight2_throwgrenade19 ]
{
	ai_face();
	self.nextthink = (time + 0.03);
};

void() hknight2_throwgrenade19 = [ 214, hknight2_throwgrenade20 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade20 = [ 215, hknight2_throwgrenade21 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
	hknight2_throw();
	hknight2_footsteps(0.7);
	random();
	if ((random() < (0.1 + (skill * 0.1))))
	{
		hknight2_throwgrenade8();
	}
};

void() hknight2_throwgrenade21 = [ 216, hknight2_throwgrenade22 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade22 = [ 217, hknight2_throwgrenade23 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade23 = [ 218, hknight2_throwgrenade24 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade24 = [ 219, hknight2_throwgrenade25 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade25 = [ 220, hknight2_throwgrenade26 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade26 = [ 221, hknight2_throwgrenade27 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade27 = [ 222, hknight2_throwgrenade28 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade28 = [ 223, hknight2_throwgrenade29 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade29 = [ 224, hknight2_throwgrenade30 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade30 = [ 225, hknight2_throwgrenade31 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade31 = [ 226, hknight2_throwgrenade32 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade32 = [ 227, hknight2_throwgrenade33 ]
{
	ai_face();
	self.nextthink = (time + 0.04);
};

void() hknight2_throwgrenade33 = [ 228, hknight2_run1 ]
{
	ai_face();
};

float() hknight2_throwdistance =
{
	local vector spot1;
	local vector spot2;
	local float r;

	spot1 = self.origin + self.view_ofs;
	spot2 = self.enemy.origin + self.enemy.view_ofs;
	r = vlen((spot1 - spot2));
	if (((r > 190) && (r < 666)))
	{
		return (TRUE);
	}
	else
	{
		return (0);
	}
};

void() hknight2_homing_teleport =
{
	local vector spot;
	local vector vec;

	spot = self.origin + (randomvec() * 55);
	vec = normalize((spot - self.origin));
	traceline(self.origin, spot, TRUE, self);
	spot = trace_endpos - (vec * 13);
	if (PM_InWall(self, spot))
	{
		return;
	}
	if (!PM_TraceCheck(self, spot))
	{
		return;
	}
	traceline(spot, self.enemy.origin, FALSE, self);
	if ((trace_fraction < 1))
	{
		if ((trace_ent != self.enemy))
		{
			return;
		}
	}
	setorigin(self, spot);
	self.angles_y = vectoyaw((self.enemy.origin - spot));
};

void() hknight2_homing_pain =
{
	if ((self.pain_finished > time))
	{
		return;
	}
	self.pain_finished = (time + 0.5);
	sound7(self, CHAN_VOICE, "warlord/homing_pain.wav", 1, ATTN_NORM, SNDSPD);
	hknight2_homing_teleport();
};

void() hknight2_homing_death =
{
	pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
	sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
	sound7(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
	remove(self);
};

void() hknight2_homing_touch =
{
	if (other.takedamage)
	{
		if ((other.classname != "player"))
		{
			hknight2_homing_teleport();
		}
		pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
		sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
		sound(self, CHAN_BODY, "player/gibsplit.wav", 1, ATTN_NORM, SNDSPD);
		T_Damage(other, self, self.owner, autocvar_warlord_homing_missile);
		sound7(self, CHAN_WEAPON, "warlord/homing_touch.wav", 1, ATTN_NORM, SNDSPD);
		remove(self);
	}
	if ((autocvar_warlord_homing_behaviour == 0))
	{
		if (!((((other.model == "progs/spike.mdl") || (other.model == "progs/s_spike.mdl")) || (other.model == "progs/grenade.mdl")) || (other.model == "progs/missile.mdl")))
		{
			pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
			sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
			sound(self, CHAN_BODY, "player/gibsplit.wav", 1, ATTN_NORM, SNDSPD);
			sound7(self, CHAN_WEAPON, "warlord/homing_touch.wav", 1, ATTN_NORM, SNDSPD);
			remove(self);
		}
	}
};

void() hknight2_homing_think =
{
	local vector dir;
	local vector offang;
	local vector vec;

	if ((self.enemy.health < 1))
	{
		remove(self);
	}
	self.has_fired = (self.has_fired + 1);
	if ((self.has_fired == 2))
	{
		self.solid = SOLID_BBOX;
		self.movetype = MOVETYPE_FLYMISSILE;
	}
	if ((self.origin == self.old_origin))
	{
		sound7(self, CHAN_WEAPON, "warlord/homing_touch.wav", 1, ATTN_NORM, SNDSPD);
		remove(self);
	}
	self.old_origin = self.origin;
	dir = normalize(((self.enemy.origin + '0 0 16') - self.origin));
	offang = vectoangles(((self.enemy.origin + '0 0 12') - self.origin));
	makevectors(offang);
	vec = normalize(v_forward);
	self.angles = vectoangles(vec);
	self.frame = (self.frame + 1);
	if ((self.frame >= 19))
	{
		self.frame = 0;
	}
	self.touch = hknight2_homing_touch;
	if (((self.has_fired < 30) && (time >= self.skypad_steer_t)))
	{
		self.velocity = (self.velocity * 0.75);
		self.velocity = (self.velocity + (dir * 100));
	}
	else if ((time < self.skypad_steer_t))
	{
		self.angles = vectoangles(self.velocity);
	}
	self.nextthink = (time + 0.1);
	self.think = hknight2_homing_think;
};

void(vector face_spawn_pos, vector face_spawn_vel) launch_hknight2_homing =
{
	newmis = spawn();
	newmis.owner = self;
	newmis.enemy = self.enemy;
	newmis.movetype = MOVETYPE_NOCLIP;
	newmis.solid = 0;
	newmis.velocity = (face_spawn_vel * 110);
	newmis.angles = vectoangles(newmis.velocity);
	newmis.colormod = '0.5 0.5 0.5';
	newmis.scale = 0.7;
	newmis.glow_color = 22;
	newmis.glow_size = 333;
	newmis.frame = 0;
	newmis.classname = "hknight2_homing";
	newmis.think = hknight2_homing_think;
	newmis.nextthink = (time + 0.4);
	setmodel(newmis, "progs/face.mdl");
	setsize(newmis, '1 1 1', '1 1 1');
	newmis.traileffectnum = particleeffectnum(/*52370i*/"TR_WARLORDHOMING");
	newmis.health = 4;
	newmis.takedamage = DAMAGE_AIM;
	setorigin(newmis, (face_spawn_pos + '0 0 8'));
	newmis.th_pain = hknight2_homing_pain;
	newmis.th_die = hknight2_homing_death;
};

void() hknight2_homing_shot =
{
	local vector offang;
	local vector org;
	local vector vec;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = ((self.origin + (v_right * 9)) + (v_up * 12)) + (v_forward * 17);
	vec = normalize(v_forward);
	launch_hknight2_homing(org, vec);
};

void() hknight2_magica1 = [ 109, hknight2_magica2 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	self.colormod = '1 1 1';
};

void() hknight2_magica2 = [ 110, hknight2_magica3 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() hknight2_magica3 = [ 111, hknight2_magica4 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() hknight2_magica4 = [ 112, hknight2_magica5 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() hknight2_magica5 = [ 113, hknight2_magica6 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() hknight2_magica6 = [ 114, hknight2_magica7 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	hknight2_footsteps(0.7);
};

void() hknight2_magica7 = [ 115, hknight2_magica8 ]
{
	self.nextthink = (time + 0.075);
	hknight2_shot(-2);
};

void() hknight2_magica8 = [ 116, hknight2_magica9 ]
{
	self.nextthink = (time + 0.075);
	hknight2_shot(-1);
};

void() hknight2_magica9 = [ 117, hknight2_magica10 ]
{
	self.nextthink = (time + 0.075);
	hknight2_shot(0);
};

void() hknight2_magica10 = [ 118, hknight2_magica11 ]
{
	self.nextthink = (time + 0.075);
	hknight2_shot(1);
};

void() hknight2_magica11 = [ 119, hknight2_magica12 ]
{
	self.nextthink = (time + 0.075);
	hknight2_shot(2);
};

void() hknight2_magica12 = [ 120, hknight2_magica13 ]
{
	self.nextthink = (time + 0.075);
	hknight2_shot(3);
};

void() hknight2_magica13 = [ 121, hknight2_magica14 ]
{
	self.nextthink = (time + 0.075);
	ai_face();
};

void() hknight2_magica14 = [ 122, hknight2_run1 ]
{
	self.nextthink = (time + 0.075);
	ai_face();
};

void() hknight2_magicb1 = [ 123, hknight2_magicb2 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	self.colormod = '1.4 1 1';
};

void() hknight2_magicb2 = [ 124, hknight2_magicb3 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	self.colormod = '1.8 1 1';
};

void() hknight2_magicb3 = [ 125, hknight2_magicb4 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	self.colormod = '2.2 1 1';
};

void() hknight2_magicb4 = [ 126, hknight2_magicb5 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	self.colormod = '2.6 1 1';
};

void() hknight2_magicb5 = [ 127, hknight2_magicb6 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	self.colormod = '3 1 1';
};

void() hknight2_magicb6 = [ 128, hknight2_magicb7 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	self.colormod = '3.5 1 1';
	hknight2_footsteps(0.7);
};

void() hknight2_magicb7 = [ 129, hknight2_magicb8 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	sound7(self, CHAN_WEAPON, "warlord/homing_shot.wav", 1, ATTN_NORM, SNDSPD);
};

void() hknight2_magicb8 = [ 130, hknight2_magicb9 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() hknight2_magicb9 = [ 131, hknight2_magicb10 ]
{
	self.nextthink = (time + 0.075);
	hknight2_homing_shot();
};

void() hknight2_magicb10 = [ 132, hknight2_magicb11 ]
{
	self.nextthink = (time + 0.075);
};

void() hknight2_magicb11 = [ 133, hknight2_magicb12 ]
{
	self.nextthink = (time + 0.075);
};

void() hknight2_magicb12 = [ 134, hknight2_magicb13 ]
{
	self.nextthink = (time + 0.075);
	self.colormod = '2 1 1';
};

void() hknight2_magicb13 = [ 135, hknight2_run1 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	self.colormod = '1 1 1';
};

void() ram_scan =
{
	local vector dir;
	local vector spot1;
	local vector spot2;
	local float r;
	local float ldmg;

	spot1 = self.origin + self.view_ofs;
	spot2 = self.enemy.origin + self.enemy.view_ofs;
	r = vlen((spot1 - spot2));
	if ((r < 60))
	{
		sound7(self, CHAN_AUTO, "warlord/fall.wav", 1, ATTN_IDLE, SNDSPD);
		ldmg = rint((autocvar_warlord_ram_attack + (5 * random())));
		T_Damage(self.enemy, self, self, ldmg);
		dir = (self.origin - '0 0 7') - self.enemy.origin;
		dir = normalize(dir);
		self.enemy.rammed = 1;
		ramdirection = dir;
	}
};

void() hknight2_char_a1 = [ 93, hknight2_char_a2 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
	self.colormod = '1 1 1';
};

void() hknight2_char_a2 = [ 94, hknight2_char_a3 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((4 + (skill * 0.5)));
};

void() hknight2_char_a3 = [ 95, hknight2_char_a4 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((6 + (skill * 0.5)));
};

void() hknight2_char_a4 = [ 96, hknight2_char_a5 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((16 + (skill * 0.5)));
	ai_melee();
	hknight2_footsteps(0.9);
};

void() hknight2_char_a5 = [ 97, hknight2_char_a6 ]
{
	ai_charge((18 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_char_a6 = [ 98, hknight2_char_a7 ]
{
	ai_charge((21 + (skill * 0.5)));
	ai_melee();
	sound7(self, CHAN_AUTO, "warlord/ram.wav", 1, ATTN_NORM, SNDSPD);
};

void() hknight2_char_a7 = [ 99, hknight2_char_a8 ]
{
	ai_charge((23 + (skill * 0.5)));
	ai_melee();
	hknight2_footsteps(0.9);
};

void() hknight2_char_a8 = [ 100, hknight2_char_a9 ]
{
	ai_charge((23 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_char_a9 = [ 101, hknight2_char_a10 ]
{
	ai_charge((23 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_char_a10 = [ 102, hknight2_char_a11 ]
{
	ai_charge((23 + (skill * 0.5)));
	ai_melee();
	ram_scan();
};

void() hknight2_char_a11 = [ 103, hknight2_char_a12 ]
{
	ai_charge((19 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_char_a12 = [ 104, hknight2_char_a13 ]
{
	ai_charge((16 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_char_a13 = [ 105, hknight2_char_a14 ]
{
	ai_charge((6 + (skill * 0.5)));
	hknight2_footsteps(0.8);
};

void() hknight2_char_a14 = [ 106, hknight2_char_a15 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_char_a15 = [ 107, hknight2_char_a16 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_char_a16 = [ 108, hknight2_run1 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_char_b1 = [ 136, hknight2_char_b2 ]
{
	CheckContinueCharge2();
	ai_charge((2 + (skill * 0.5)));
	self.colormod = '1 1 1';
};

void() hknight2_char_b2 = [ 137, hknight2_char_b3 ]
{
	ai_charge((12 + (skill * 0.5)));
};

void() hknight2_char_b3 = [ 138, hknight2_char_b4 ]
{
	ai_charge((17 + (skill * 0.5)));
	ai_melee();
	hknight2_footsteps(0.7);
};

void() hknight2_char_b4 = [ 139, hknight2_char_b5 ]
{
	ai_charge((23 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_char_b5 = [ 140, hknight2_char_b6 ]
{
	ai_charge((19 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_char_b6 = [ 141, hknight2_char_b1 ]
{
	ai_charge((14 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_slice1 = [ 142, hknight2_slice2 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
	self.colormod = '1 1 1';
};

void() hknight2_slice2 = [ 143, hknight2_slice3 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_slice3 = [ 144, hknight2_slice4 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((5 + (skill * 0.5)));
};

void() hknight2_slice4 = [ 145, hknight2_slice5 ]
{
	ai_charge((9 + (skill * 0.5)));
	if ((random() < 0.5))
	{
		sound7(self, CHAN_AUTO, "warlord/attack2.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() hknight2_slice5 = [ 146, hknight2_slice6 ]
{
	ai_charge((15 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_slice6 = [ 147, hknight2_slice7 ]
{
	ai_charge((20 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_slice7 = [ 148, hknight2_slice8 ]
{
	ai_charge((25 + (skill * 0.5)));
	ai_melee();
	hknight2_footsteps(0.8);
};

void() hknight2_slice8 = [ 149, hknight2_slice9 ]
{
	ai_charge((18 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_slice9 = [ 150, hknight2_slice10 ]
{
	ai_charge((10 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_slice10 = [ 151, hknight2_run1 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((3 + (skill * 0.5)));
};

void() hknight2_smash1 = [ 152, hknight2_smash2 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
	self.colormod = '1 1 1';
};

void() hknight2_smash2 = [ 153, hknight2_smash3 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_smash3 = [ 154, hknight2_smash4 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((5 + (skill * 0.5)));
};

void() hknight2_smash4 = [ 155, hknight2_smash5 ]
{
	ai_charge((9 + (skill * 0.5)));
	if ((random() < 0.5))
	{
		sound7(self, CHAN_AUTO, "warlord/attack2.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() hknight2_smash5 = [ 156, hknight2_smash6 ]
{
	ai_charge((15 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_smash6 = [ 157, hknight2_smash7 ]
{
	ai_charge((20 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_smash7 = [ 158, hknight2_smash8 ]
{
	ai_charge((17 + (skill * 0.5)));
	ai_melee();
	hknight2_footsteps(0.8);
};

void() hknight2_smash8 = [ 159, hknight2_smash9 ]
{
	ai_charge((15 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_smash9 = [ 160, hknight2_smash10 ]
{
	ai_charge((10 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_smash10 = [ 161, hknight2_smash11 ]
{
	ai_charge((5 + (skill * 0.5)));
	hknight2_footsteps(0.8);
};

void() hknight2_smash11 = [ 162, hknight2_run1 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_watk1 = [ 163, hknight2_watk2 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
	self.colormod = '1 1 1';
};

void() hknight2_watk2 = [ 164, hknight2_watk3 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((6 + (skill * 0.5)));
	if ((random() < 0.5))
	{
		sound7(self, CHAN_AUTO, "warlord/attack3.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() hknight2_watk3 = [ 165, hknight2_watk4 ]
{
	ai_charge((10 + (skill * 0.5)));
	ai_melee();
	hknight2_footsteps(0.7);
};

void() hknight2_watk4 = [ 166, hknight2_watk5 ]
{
	ai_charge((8 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_watk5 = [ 167, hknight2_watk6 ]
{
	ai_charge((8 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_watk6 = [ 168, hknight2_watk7 ]
{
	ai_charge((8 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_watk7 = [ 169, hknight2_watk8 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_watk8 = [ 170, hknight2_watk9 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_watk9 = [ 171, hknight2_watk10 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_watk10 = [ 172, hknight2_watk11 ]
{
	ai_charge((6 + (skill * 0.5)));
};

void() hknight2_watk11 = [ 173, hknight2_watk12 ]
{
	ai_charge((10 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_watk12 = [ 174, hknight2_watk13 ]
{
	ai_charge((15 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_watk13 = [ 175, hknight2_watk14 ]
{
	ai_charge((10 + (skill * 0.5)));
	ai_melee();
	hknight2_footsteps(0.7);
};

void() hknight2_watk14 = [ 176, hknight2_watk15 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((1 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_watk15 = [ 177, hknight2_watk16 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((1 + (skill * 0.5)));
};

void() hknight2_watk16 = [ 178, hknight2_watk17 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
	hknight2_footsteps(0.7);
};

void() hknight2_watk17 = [ 179, hknight2_watk18 ]
{
	self.nextthink = (time + 0.075);
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_watk18 = [ 180, hknight2_watk19 ]
{
	ai_charge((2 + (skill * 0.5)));
};

void() hknight2_watk19 = [ 181, hknight2_watk20 ]
{
	ai_charge((6 + (skill * 0.5)));
	ai_melee();
	hknight2_footsteps(0.7);
};

void() hknight2_watk20 = [ 182, hknight2_watk21 ]
{
	ai_charge((12 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_watk21 = [ 183, hknight2_watk22 ]
{
	ai_charge((12 + (skill * 0.5)));
	ai_melee();
};

void() hknight2_watk22 = [ 184, hknight2_run1 ]
{
	ai_charge((3 + (skill * 0.5)));
};

void() hknight2_duck1 = [ 240, hknight2_duck2 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() hknight2_duck2 = [ 241, hknight2_duck3 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() hknight2_duck3 = [ 242, hknight2_duck4 ]
{
	ai_face();
	self.nextthink = (time + 0.2);
};

void() hknight2_duck4 = [ 243, hknight2_duck5 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
};

void() hknight2_duck5 = [ 244, hknight2_duck6 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
};

void() hknight2_duck6 = [ 245, hknight2_run1 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
	self.takedamage = DAMAGE_AIM;
};

void() hknight2_dodge1 = [ 235, hknight2_dodge2 ]
{
	ai_face();
	ai_back(18);
	self.nextthink = (time + 0.03);
};

void() hknight2_dodge2 = [ 236, hknight2_dodge3 ]
{
	ai_face();
	ai_back(28);
	self.nextthink = (time + 0.03);
};

void() hknight2_dodge3 = [ 237, hknight2_dodge4 ]
{
	ai_face();
	ai_back(35);
	self.nextthink = (time + 0.04);
};

void() hknight2_dodge4 = [ 238, hknight2_dodge5 ]
{
	ai_face();
	ai_back(28);
	self.nextthink = (time + 0.04);
};

void() hknight2_dodge5 = [ 239, hknight2_run1 ]
{
	ai_face();
	ai_back(14);
	self.nextthink = (time + 0.04);
	self.takedamage = DAMAGE_AIM;
};

void() hknight2_block1 = [ 229, hknight2_block2 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
};

void() hknight2_block2 = [ 230, hknight2_block3 ]
{
	ai_face();
	self.nextthink = (time + 0.1);
};

void() hknight2_block3 = [ 231, hknight2_block4 ]
{
	ai_face();
	self.nextthink = (time + 0.2);
};

void() hknight2_block4 = [ 232, hknight2_block5 ]
{
	ai_face();
	self.nextthink = (time + 0.1);
};

void() hknight2_block5 = [ 233, hknight2_block6 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
};

void() hknight2_block6 = [ 234, hknight2_run1 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
	self.takedamage = DAMAGE_AIM;
};

void() hknight2_dodge =
{
	local float zufall;

	self.takedamage = DAMAGE_YES;
	zufall = random();
	if ((zufall < 0.2))
	{
		hknight2_duck1();
	}
	else
	{
		if ((zufall < 0.4))
		{
			hknight2_block1();
		}
		else
		{
			hknight2_dodge1();
		}
	}
};

void() hknight2_random_ranged_attack =
{
	local float grenade_distance;
	local float zufall;

	grenade_distance = 0;
	grenade_distance = grenade_distance + hknight2_throwdistance();
	zufall = random();
	if (grenade_distance)
	{
		if ((zufall < 0.45))
		{
			hknight2_throwgrenade1();
		}
		else
		{
			if ((zufall < 0.7))
			{
				hknight2_magica1();
			}
			else
			{
				if ((random() < 0.15))
				{
					hknight2_magicb1();
				}
				else
				{
					hknight2_magica1();
				}
			}
		}
	}
	else
	{
		if ((zufall < 0.8))
		{
			hknight2_magica1();
		}
		else
		{
			hknight2_magicb1();
		}
	}
};

void(entity attacker, float damage) hknight2_pain =
{
	self.colormod = '1 1 1';
	self.touch = SUB_Null;
	if ((random() < (damage * 0.005)))
	{
		if ((self.th_missile == SUB_Null))
		{
			self.th_missile = hknight2_random_ranged_attack;
		}
		self.dodging = 0;
		hknight2_dodge();
		return;
	}
	if ((self.dodge_finished > time))
	{
		return;
	}
	if ((self.pain_finished > time))
	{
		return;
	}
	if (((time - self.pain_finished) > 5))
	{
		if ((autocvar_slowmotion >= 4))
		{
			if ((random() <= (autocvar_slowmotion_randomness_warlord * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		if ((random() < 0.5))
		{
			hknight2_pain1();
		}
		else
		{
			hknight2_painb1();
		}
		self.pain_finished = (time + 1.5);
		return;
	}
	if (((random() * 30) > damage))
	{
		return;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_warlord * 0.01)))
		{
			the_matrix = 1;
			SNDSPD = 70;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	self.pain_finished = (time + 1.5);
	if ((random() < 0.5))
	{
		hknight2_pain1();
	}
	else
	{
		hknight2_painb1();
	}
};

void() hknight2_melee =
{
	hknight2_type = hknight2_type + 1;
	if ((random() < 0.2))
	{
		self.th_missile = SUB_Null;
	}
	sound7(self, CHAN_WEAPON, "warlord/slash1.wav", 1, ATTN_NORM, SNDSPD);
	if ((hknight2_type == 1))
	{
		hknight2_slice1();
	}
	else
	{
		if ((hknight2_type == 2))
		{
			hknight2_smash1();
		}
		else
		{
			if ((hknight2_type == 3))
			{
				hknight2_watk1();
				hknight2_type = 0;
				if (((random() < 0.4) && (self.th_missile == SUB_Null)))
				{
					self.th_missile = hknight2_random_ranged_attack;
				}
			}
		}
	}
};

void() monster_hell_knight2 =
{
	local float zufal;
	local entity motion_blur_entity;
	local entity motion_blur_entity1;
	local entity motion_blur_entity2;
	local entity motion_blur_entity3;
	local entity motion_blur_entity4;
	local entity motion_blur_entity5;
	local entity pain_skin_entity;

	self.classname = "monster_hell_knight2";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	precachegibs_warlord();
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/warlord.mdl");
	zufal = autocvar_warlordmultiskin * 0.01;
	if ((random() <= zufal))
	{
		self.skin = 1;
	}
	else
	{
		self.skin = 0;
	}
	self.monstermodel = 0;
	setsize(self, VEC_HULL_MIN, '16 16 40');
	self.health = autocvar_warlord_health;
	if ((cvar("skill") == 3))
	{
		self.health = 400;
	}
	else
	{
		self.health = 320;
	}
	if ((random() < 0.09))
	{
		self.has_fired = 1;
	}
	else
	{
		if ((random() < 0.1))
		{
			self.has_fired = 2;
		}
		else
		{
			if ((random() < 0.04))
			{
				self.has_fired = 3;
			}
		}
	}
	self.health_initial = self.health;
	self.colormod = '1 1 1';
	self.th_stand = hknight2_stand1;
	self.th_walk = hknight2_walk1;
	self.th_run = hknight2_run1;
	self.th_melee = hknight2_melee;
	self.th_missile = hknight2_random_ranged_attack;
	self.th_pain = hknight2_pain;
	self.th_die = hknight2_die;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_demon_jump_motion_blur)
	{
		motion_blur_entity = spawn();
		motion_blur_entity.solid = 0;
		motion_blur_entity.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity.owner = self;
		setmodel(motion_blur_entity, self.model);
		setsize(motion_blur_entity, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity, VEC_ORIGIN);
		motion_blur_entity.skin = self.skin;
		motion_blur_entity.colormod_x = self.colormod_x;
		motion_blur_entity.colormod_y = self.colormod_y;
		motion_blur_entity.colormod_z = self.colormod_z;
		motion_blur_entity.frame = self.frame;
		motion_blur_entity.think = motion_blur_entity_think;
		motion_blur_entity.nextthink = (time + 0.05);
		setattachment(motion_blur_entity, self, /*37325i*/"test");
		motion_blur_entity1 = spawn();
		motion_blur_entity1.solid = 0;
		motion_blur_entity1.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity1.owner = self;
		setmodel(motion_blur_entity1, self.model);
		setsize(motion_blur_entity1, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity1, VEC_ORIGIN);
		motion_blur_entity1.skin = self.skin;
		motion_blur_entity1.colormod_x = self.colormod_x;
		motion_blur_entity1.colormod_y = self.colormod_y;
		motion_blur_entity1.colormod_z = self.colormod_z;
		motion_blur_entity1.frame = self.frame;
		motion_blur_entity1.think = motion_blur_entity1_think;
		motion_blur_entity1.nextthink = (time + 0.05);
		setattachment(motion_blur_entity1, self, /*37325i*/"test");
		motion_blur_entity2 = spawn();
		motion_blur_entity2.solid = 0;
		motion_blur_entity2.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity2.owner = self;
		setmodel(motion_blur_entity2, self.model);
		setsize(motion_blur_entity2, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity2, VEC_ORIGIN);
		motion_blur_entity2.skin = self.skin;
		motion_blur_entity2.colormod_x = self.colormod_x;
		motion_blur_entity2.colormod_y = self.colormod_y;
		motion_blur_entity2.colormod_z = self.colormod_z;
		motion_blur_entity2.frame = self.frame;
		motion_blur_entity2.think = motion_blur_entity2_think;
		motion_blur_entity2.nextthink = (time + 0.05);
		setattachment(motion_blur_entity2, self, /*37325i*/"test");
		motion_blur_entity3 = spawn();
		motion_blur_entity3.solid = 0;
		motion_blur_entity3.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity3.owner = self;
		setmodel(motion_blur_entity3, self.model);
		setsize(motion_blur_entity3, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity3, VEC_ORIGIN);
		motion_blur_entity3.skin = self.skin;
		motion_blur_entity3.colormod_x = self.colormod_x;
		motion_blur_entity3.colormod_y = self.colormod_y;
		motion_blur_entity3.colormod_z = self.colormod_z;
		motion_blur_entity3.frame = self.frame;
		motion_blur_entity3.think = motion_blur_entity3_think;
		motion_blur_entity3.nextthink = (time + 0.05);
		setattachment(motion_blur_entity3, self, /*37325i*/"test");
		motion_blur_entity4 = spawn();
		motion_blur_entity4.solid = 0;
		motion_blur_entity4.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity4.owner = self;
		setmodel(motion_blur_entity4, self.model);
		setsize(motion_blur_entity4, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity4, VEC_ORIGIN);
		motion_blur_entity4.skin = self.skin;
		motion_blur_entity4.colormod_x = self.colormod_x;
		motion_blur_entity4.colormod_y = self.colormod_y;
		motion_blur_entity4.colormod_z = self.colormod_z;
		motion_blur_entity4.frame = self.frame;
		motion_blur_entity4.think = motion_blur_entity4_think;
		motion_blur_entity4.nextthink = (time + 0.05);
		setattachment(motion_blur_entity4, self, /*37325i*/"test");
		motion_blur_entity5 = spawn();
		motion_blur_entity5.solid = 0;
		motion_blur_entity5.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity5.owner = self;
		setmodel(motion_blur_entity5, self.model);
		setsize(motion_blur_entity5, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity5, VEC_ORIGIN);
		motion_blur_entity5.skin = self.skin;
		motion_blur_entity5.colormod_x = self.colormod_x;
		motion_blur_entity5.colormod_y = self.colormod_y;
		motion_blur_entity5.colormod_z = self.colormod_z;
		motion_blur_entity5.frame = self.frame;
		motion_blur_entity5.think = motion_blur_entity5_think;
		motion_blur_entity5.nextthink = (time + 0.05);
		setattachment(motion_blur_entity5, self, /*37325i*/"test");
	}
	if (autocvar_painskin_transparency)
	{
		pain_skin_entity = spawn();
		pain_skin_entity.solid = 0;
		pain_skin_entity.movetype = MOVETYPE_NOCLIP;
		pain_skin_entity.owner = self;
		setmodel(pain_skin_entity, self.model);
		setsize(pain_skin_entity, VEC_HULL2_MIN, VEC_HULL2_MAX);
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
	MonsterPhysics(self, autocvar_warlordmass);
};

void() monster_hell_knight2_start =
{
	local entity clone;

	self.scale = 1;
	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_hell_knight2;
	clone.nextthink = (time + 0.000100);
};

void() vengeance_hknight2_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_hknight2_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_hknight2_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_skull =
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

void() vengeance_hknight2_run1 = [ 54, vengeance_hknight2_run2 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_run2 = [ 55, vengeance_hknight2_run3 ]
{
	ai_face();
	movetogoal(24);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.37;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_run3 = [ 56, vengeance_hknight2_run4 ]
{
	ai_face();
	movetogoal(17);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.34;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_run4 = [ 57, vengeance_hknight2_run5 ]
{
	ai_face();
	movetogoal(15);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.31;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_run5 = [ 58, vengeance_hknight2_run6 ]
{
	ai_face();
	movetogoal(13);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.28;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_run6 = [ 59, vengeance_hknight2_run7 ]
{
	ai_face();
	movetogoal(24);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.25;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_run7 = [ 60, vengeance_hknight2_random ]
{
	ai_face();
	movetogoal(20);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.22;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() trap_flame_touch2 =
{
	ApplyFireDmg(other, 0.000100, 0.000100);
	self.touch = SUB_Null;
};

void() boss_trap_fin2 =
{
	local entity flame;

	flame = spawn();
	flame.owner = self;
	if ((self.has_fired == 0))
	{
		if ((((pointcontents(self.origin) == CONTENT_WATER) || (pointcontents(self.origin) == CONTENT_SOLID)) || (pointcontents(self.origin) == CONTENT_SLIME)))
		{
			remove(self);
		}
		self.alpha = 1;
		self.has_fired = 1;
		self.angles_y = ((random() * 720) + -360);
		pointparticles(particleeffectnum(/*12736i*/"lava_eruption_large"), self.origin, VEC_ORIGIN, 1);
	}
	setmodel(flame, "progs/s_flame.spr");
	setorigin(flame, (self.origin + '0 0 1'));
	setsize(flame, VEC_ORIGIN, '14 14 1');
	flame.velocity = '0 0 180';
	flame.alpha = -1;
	if ((random() < 0.01))
	{
		if ((random() < 0.7))
		{
			pointparticles(particleeffectnum(/*12681i*/"lava_eruption_medium"), self.origin, VEC_ORIGIN, 1);
			if ((random() < 0.8))
			{
				sound(self, CHAN_BODY, "ambience/rumblefade.wav", 1, ATTN_NORM);
			}
		}
		else
		{
			pointparticles(particleeffectnum(/*12628i*/"lava_eruption_small"), self.origin, VEC_ORIGIN, 1);
		}
	}
	flame.velocity_x = ((random() * 40) + -20);
	flame.velocity_y = ((random() * 40) + -20);
	flame.movetype = MOVETYPE_FLY;
	flame.solid = SOLID_TRIGGER;
	if ((random() < 0.85))
	{
		flame.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
	}
	flame.nextthink = ((time + 0.05) + (random() * 0.05));
	flame.think = trap_gasshooter_think;
	flame.touch = trap_flame_touch2;
	sound(self, CHAN_WEAPON, "traps/steam_loop.wav", 0.9, ATTN_STATIC);
	self.think = boss_trap_fin2;
	self.nextthink = (time + (0.35 - (random() * 0.1)));
};

void() vengeance_hknight2_chara1 = [ 96, vengeance_hknight2_chara2 ]
{
	ai_face();
	movetogoal(13);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	sound(self, CHAN_VOICE, "boss1/atk2.wav", 1, ATTN_NORM);
};

void() vengeance_hknight2_chara2 = [ 97, vengeance_hknight2_chara3 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.17;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_chara3 = [ 98, vengeance_hknight2_chara4 ]
{
	ai_face();
	movetogoal(20);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.14;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_chara4 = [ 99, vengeance_hknight2_chara5 ]
{
	ai_face();
	movetogoal(20);
	self.touch = SUB_Null;
	self.alpha = 0.11;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_chara5 = [ 100, vengeance_hknight2_chara6 ]
{
	ai_face();
	movetogoal(20);
	self.alpha = 0.08;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_chara6 = [ 101, vengeance_hknight2_end1 ]
{
	local entity missile;

	ai_face();
	self.alpha = 0.05;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	if ((self.weapontimer == 3))
	{
		self.weapontimer = 0;
	}
	sound(self, CHAN_AUTO, "boss1/quake.wav", 1, ATTN_NONE);
	sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 0.9, ATTN_NORM, SNDSPD);
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_TOSS;
	setmodel(missile, "progs/lavacrack.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.origin = (self.origin + '-110 -10 35');
	missile.nextthink = (time + 0.1);
	missile.scale = (missile.scale * (3 + random()));
	missile.angles_y = ((random() * 720) + -360);
	missile.think = boss_trap_fin2;
	missile.frame = 4;
	missile.alpha = -1;
	pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
	pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
	pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
	T_RadiusDamage(self, self, 90, world);
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_TOSS;
	setmodel(missile, "progs/lavacrack.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.origin = (self.origin + '50 90 32');
	missile.nextthink = (time + 0.1);
	missile.scale = (missile.scale * (3 + random()));
	missile.frame = 5;
	missile.alpha = -1;
	missile.angles_y = ((random() * 720) + -360);
	missile.think = boss_trap_fin2;
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_TOSS;
	setmodel(missile, "progs/lavacrack.mdl");
	setsize(missile, '0 0 -1', VEC_ORIGIN);
	missile.origin = (self.origin + '-28 34 32');
	missile.nextthink = (time + 0.1);
	missile.scale = (missile.scale * (3 + random()));
	missile.frame = 5;
	missile.alpha = -1;
	missile.angles_y = ((random() * 720) + -360);
	missile.think = boss_trap_fin2;
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_TOSS;
	setmodel(missile, "progs/lavacrack.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.origin = (self.origin + '32 -50 32');
	missile.nextthink = (time + 0.1);
	missile.scale = (missile.scale * (3 + random()));
	missile.frame = 5;
	missile.alpha = -1;
	missile.angles_y = ((random() * 720) + -360);
	missile.think = boss_trap_fin2;
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_TOSS;
	setmodel(missile, "progs/lavacrack.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.origin = (self.origin + '90 35 32');
	missile.nextthink = (time + 0.1);
	missile.scale = (missile.scale * (3 + random()));
	missile.frame = 5;
	missile.alpha = -1;
	missile.angles_y = ((random() * 720) + -360);
	missile.think = boss_trap_fin2;
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_TOSS;
	setmodel(missile, "progs/lavacrack.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.origin = (self.origin + '2 120 42');
	missile.nextthink = (time + 0.1);
	missile.scale = (missile.scale * (3 + random()));
	missile.angles_y = ((random() * 720) + -360);
	missile.frame = 5;
	missile.alpha = -1;
	missile.think = boss_trap_fin2;
};

void() vengeance_hknight2_skull1 = [ 110, vengeance_hknight2_skull2 ]
{
	ai_face();
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_skull2 = [ 111, vengeance_hknight2_skull3 ]
{
	sound7(self, CHAN_VOICE, "vengeance/hknightmag.wav", 0.8, ATTN_NORM, SNDSPD);
	ai_face();
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_skull3 = [ 112, vengeance_hknight2_skull4 ]
{
	ai_face();
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_skull4 = [ 113, vengeance_hknight2_skull5 ]
{
	ai_face();
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_skull5 = [ 114, vengeance_hknight2_skull6 ]
{
	ai_face();
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_skull6 = [ 115, vengeance_hknight2_skull7 ]
{
	ai_face();
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_skull7 = [ 116, vengeance_hknight2_skull8 ]
{
	ai_face();
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.15;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight2_skull8 = [ 116, vengeance_hknight2_end1 ]
{
	ai_face();
	movetogoal(2);
	self.touch = vengeance_hknight2_touch;
	self.alpha = 0.1;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	vengeance_hknight2_skull();
};

void() vengeance_hknight2_random =
{
	self.alpha = 0.22;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.01);
	ai_face();
	self.think = vengeance_hknight2_chara1;
};

void() vengeance_hknight211 = [ 81, vengeance_hknight212 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	sound7(self, CHAN_WEAPON, "warlord/sight1.wav", 1, ATTN_NORM, 70);
	self.nextthink = (time + 1.13);
};

void() vengeance_hknight212 = [ 80, vengeance_hknight213 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.13);
};

void() vengeance_hknight213 = [ 79, vengeance_hknight214 ]
{
	walkmove((self.angles_y + 180), 11);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_hknight214 = [ 78, vengeance_hknight215 ]
{
	walkmove((self.angles_y + 180), 10);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_hknight215 = [ 77, vengeance_hknight216 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_hknight216 = [ 76, vengeance_hknight217 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
	sound(self, CHAN_AUTO, "ambience/rumblefade.wav", 1, ATTN_NORM);
};

void() vengeance_hknight217 = [ 75, vengeance_hknight218 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_hknight218 = [ 74, vengeance_hknight219 ]
{
	local entity shake;

	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
	shake = spawn();
	setorigin(shake, (self.origin + '0 0 5'));
	shake.think = screenshake;
	shake.attack_finished = (time + 3.5);
	shake.nextthink = (time + 0.1);
};

void() vengeance_hknight219 = [ 73, vengeance_hknight2110 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_hknight2110 = [ 72, vengeance_hknight2111 ]
{
	walkmove((self.angles_y + 180), 8);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
	sound(self, CHAN_BODY, "boss1/quake.wav", 1, ATTN_NONE);
};

void() vengeance_hknight2111 = [ 71, vengeance_hknight2_stand1 ]
{
	walkmove((self.angles_y + 180), 10);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_hknight2_stand1 = [ 47, vengeance_hknight2_run1 ]
{
	self.alpha = 0.4;
	ai_face();
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_hknight221 = [ 91, vengeance_hknight222 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	sound7(self, CHAN_WEAPON, "warlord/sight1.wav", 1, ATTN_NORM, 70);
	self.nextthink = (time + 1);
};

void() vengeance_hknight222 = [ 90, vengeance_hknight223 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.13);
};

void() vengeance_hknight223 = [ 89, vengeance_hknight224 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.13);
};

void() vengeance_hknight224 = [ 88, vengeance_hknight225 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.13);
};

void() vengeance_hknight225 = [ 87, vengeance_hknight226 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
	sound(self, CHAN_AUTO, "ambience/rumblefade.wav", 1, ATTN_NORM);
};

void() vengeance_hknight226 = [ 86, vengeance_hknight227 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_hknight227 = [ 85, vengeance_hknight228 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_hknight228 = [ 84, vengeance_hknight2_stand2 ]
{
	local entity shake;

	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
	shake = spawn();
	setorigin(shake, (self.origin + '0 0 5'));
	shake.think = screenshake;
	shake.attack_finished = (time + 3.5);
	shake.nextthink = (time + 0.1);
};

void() vengeance_hknight2_stand2 = [ 94, vengeance_hknight2_stand21 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
	sound(self, CHAN_BODY, "boss1/quake.wav", 1, ATTN_NONE);
};

void() vengeance_hknight2_stand21 = [ 93, vengeance_hknight2_run1 ]
{
	ai_face();
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_hknight2_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	if ((self.frame == 83))
	{
		self.think = vengeance_hknight211;
	}
	else
	{
		self.think = vengeance_hknight221;
	}
};

void() vengeance_hknight2_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_hknight2_bright05;
};

void() vengeance_hknight2_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_hknight2_bright04;
};

void() vengeance_hknight2_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_hknight2_bright03;
};

void() vengeance_hknight2_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_hknight2_bright02;
};

void() vengeance_hknight2_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_hknight2_bright01;
};

void(string modelname, float modelframe) vengeance_hknight2 =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/warlord.mdl");
	setsize(self, VEC_HULL_MIN, '16 16 40');
	self.frame = modelframe;
	self.solid = 0;
	MonsterPhysics(self, autocvar_warlordmass);
	vengeance_hknight2_bright00();
};
