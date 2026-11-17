//Decompiled code. Please respect the original copyright.

void(float loudness) knight_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.33))
		{
			sound(self, CHAN_AUTO, "walk/knight1.wav", loudness, ATTN_IDLE);
		}
		else
		{
			if ((select <= 0.66))
			{
				sound(self, CHAN_AUTO, "walk/knight2.wav", loudness, ATTN_IDLE);
			}
			else
			{
				sound(self, CHAN_AUTO, "walk/knight3.wav", loudness, ATTN_IDLE);
			}
		}
	}
};

void(float loudness) knight_statue_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.33))
		{
			sound(self, CHAN_AUTO, "walk/statue_knight1.wav", loudness, ATTN_IDLE);
		}
		else
		{
			if ((select <= 0.66))
			{
				sound(self, CHAN_AUTO, "walk/statue_knight2.wav", loudness, ATTN_IDLE);
			}
			else
			{
				sound(self, CHAN_AUTO, "walk/statue_knight3.wav", loudness, ATTN_IDLE);
			}
		}
	}
};

void() knight_still = [ 70, knight_still ]
{
	ai_stand();
};

void() knight_stand1 = [ 0, knight_stand2 ]
{
	ai_stand();
};

void() knight_stand2 = [ 1, knight_stand3 ]
{
	ai_stand();
};

void() knight_stand3 = [ 2, knight_stand4 ]
{
	ai_stand();
};

void() knight_stand4 = [ 3, knight_stand5 ]
{
	ai_stand();
};

void() knight_stand5 = [ 4, knight_stand6 ]
{
	ai_stand();
};

void() knight_stand6 = [ 5, knight_stand7 ]
{
	ai_stand();
};

void() knight_stand7 = [ 6, knight_stand8 ]
{
	ai_stand();
};

void() knight_stand8 = [ 7, knight_stand9 ]
{
	ai_stand();
};

void() knight_stand9 = [ 8, knight_stand1 ]
{
	ai_stand();
	if (((autocvar_knightpray == 1) && !(self.spawnflags & 2)))
	{
		if ((random() <= 0.06))
		{
			knight_pray1();
		}
	}
};

void() kn_idle_sound =
{
	if ((random() < 0.2))
	{
		if ((self.spawnflags & 2))
		{
			sound(self, CHAN_VOICE, "statue/idle.wav", 1, ATTN_IDLE);
		}
		else
		{
			sound(self, CHAN_VOICE, "knight/idle.wav", 1, ATTN_IDLE);
		}
	}
};

void() knight_walk1 = [ 52, knight_walk2 ]
{
	kn_idle_sound();
	ai_walk(3);
};

void() knight_walk2 = [ 53, knight_walk3 ]
{
	ai_walk(2);
};

void() knight_walk3 = [ 54, knight_walk4 ]
{
	ai_walk(3);
	knight_footsteps(0.7);
};

void() knight_walk4 = [ 55, knight_walk5 ]
{
	ai_walk(4);
};

void() knight_walk5 = [ 56, knight_walk6 ]
{
	ai_walk(3);
};

void() knight_walk6 = [ 57, knight_walk7 ]
{
	ai_walk(3);
};

void() knight_walk7 = [ 58, knight_walk8 ]
{
	ai_walk(3);
};

void() knight_walk8 = [ 59, knight_walk9 ]
{
	ai_walk(4);
};

void() knight_walk9 = [ 60, knight_walk10 ]
{
	ai_walk(3);
};

void() knight_walk10 = [ 61, knight_walk11 ]
{
	ai_walk(3);
	knight_footsteps(0.7);
};

void() knight_walk11 = [ 62, knight_walk12 ]
{
	ai_walk(2);
};

void() knight_walk12 = [ 63, knight_walk13 ]
{
	ai_walk(3);
};

void() knight_walk13 = [ 64, knight_walk14 ]
{
	ai_walk(4);
};

void() knight_walk14 = [ 65, knight_walk1 ]
{
	ai_walk(3);
	if (((autocvar_knightpray == 1) && !(self.spawnflags & 2)))
	{
		if ((random() <= 0.07))
		{
			knight_bow1();
		}
	}
};

void() knight_run1 = [ 9, knight_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((random() < 0.2))
	{
		sound(self, CHAN_VOICE, "knight/idle.wav", 1, ATTN_IDLE);
	}
	ai_run(16);
};

void() knight_run2 = [ 10, knight_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((skill == 3))
	{
		ai_run(22);
	}
	else
	{
		ai_run(20);
	}
	knight_footsteps(0.9);
};

void() knight_run3 = [ 11, knight_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((skill == 3))
	{
		ai_run(14);
	}
	else
	{
		ai_run(13);
	}
};

void() knight_run4 = [ 12, knight_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((skill == 3))
	{
		ai_run(8);
	}
	else
	{
		ai_run(7);
	}
};

void() knight_run5 = [ 13, knight_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((skill == 3))
	{
		ai_run(18);
	}
	else
	{
		ai_run(16);
	}
};

void() knight_run6 = [ 14, knight_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((skill == 3))
	{
		ai_run(22);
	}
	else
	{
		ai_run(20);
	}
	knight_footsteps(0.9);
};

void() knight_run7 = [ 15, knight_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((skill == 3))
	{
		ai_run(15);
	}
	else
	{
		ai_run(14);
	}
};

void() knight_run8 = [ 16, knight_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((skill == 3))
	{
		ai_run(7);
	}
	else
	{
		ai_run(6);
	}
};

void() knight_runatk1 = [ 17, knight_runatk2 ]
{
	self.nextthink = (time + 0.09);
	if ((random() > 0.5))
	{
		sound(self, CHAN_WEAPON, "knight/sword2.wav", 1, ATTN_NORM);
	}
	else
	{
		sound(self, CHAN_WEAPON, "knight/sword1.wav", 1, ATTN_NORM);
	}
	ai_charge(16);
};

void() knight_runatk2 = [ 18, knight_runatk3 ]
{
	self.nextthink = (time + 0.09);
	ai_charge_side();
};

void() knight_runatk3 = [ 19, knight_runatk4 ]
{
	self.nextthink = (time + 0.09);
	ai_charge_side();
	knight_footsteps(0.7);
};

void() knight_runatk4 = [ 20, knight_runatk5 ]
{
	self.nextthink = (time + 0.09);
	ai_charge_side();
};

void() knight_runatk5 = [ 21, knight_runatk6 ]
{
	self.nextthink = (time + 0.09);
	ai_charge(2);
};

void() knight_runatk6 = [ 22, knight_runatk7 ]
{
	self.nextthink = (time + 0.09);
	knight_footsteps(0.6);
};

void() knight_runatk7 = [ 23, knight_runatk8 ]
{
	self.nextthink = (time + 0.09);
	ai_melee_side_knight();
};

void() knight_runatk8 = [ 24, knight_runatk9 ]
{
	self.nextthink = (time + 0.09);
	ai_melee_side_knight();
};

void() knight_runatk9 = [ 25, knight_runatk10 ]
{
	self.nextthink = (time + 0.09);
	ai_melee_side_knight();
};

void() knight_runatk10 = [ 26, knight_runatk11 ]
{
	self.nextthink = (time + 0.09);
	ai_charge_side();
};

void() knight_runatk11 = [ 27, knight_run1 ]
{
	self.nextthink = (time + 0.09);
	ai_charge(10);
};

void() knight_atk1 = [ 42, knight_atk2 ]
{
	sound(self, CHAN_WEAPON, "knight/sword1.wav", 1, ATTN_NORM);
	ai_charge(0);
};

void() knight_atk2 = [ 43, knight_atk3 ]
{
	ai_charge(7);
};

void() knight_atk3 = [ 44, knight_atk4 ]
{
	ai_charge(4);
};

void() knight_atk4 = [ 45, knight_atk5 ]
{
	ai_charge(0);
	knight_footsteps(0.6);
};

void() knight_atk5 = [ 46, knight_atk6 ]
{
	ai_charge(3);
};

void() knight_atk6 = [ 47, knight_atk7 ]
{
	ai_charge(4);
	ai_melee_knight();
};

void() knight_atk7 = [ 48, knight_atk8 ]
{
	ai_charge(1);
	ai_melee_knight();
};

void() knight_atk8 = [ 49, knight_atk9 ]
{
	ai_charge(3);
	ai_melee_knight();
};

void() knight_atk9 = [ 50, knight_atk10 ]
{
	ai_charge(1);
};

void() knight_atk10 = [ 51, knight_run1 ]
{
	ai_charge(5);
	if ((self.spawnflags & 2))
	{
		knight_statue_footsteps(0.7);
	}
	else
	{
		knight_footsteps(0.5);
	}
};

void() knight_pain1 = [ 28, knight_pain2 ]
{
};

void() knight_pain2 = [ 29, knight_pain3 ]
{
};

void() knight_pain3 = [ 30, knight_run1 ]
{
};

void() knight_painb1 = [ 31, knight_painb2 ]
{
	ai_painforward(0);
};

void() knight_painb2 = [ 32, knight_painb3 ]
{
	ai_painforward(3);
};

void() knight_painb3 = [ 33, knight_painb4 ]
{
};

void() knight_painb4 = [ 34, knight_painb5 ]
{
};

void() knight_painb5 = [ 35, knight_painb6 ]
{
	ai_painforward(2);
};

void() knight_painb6 = [ 36, knight_painb7 ]
{
	ai_painforward(4);
};

void() knight_painb7 = [ 37, knight_painb8 ]
{
	ai_painforward(2);
	if ((self.spawnflags & 2))
	{
		knight_statue_footsteps(0.7);
	}
	else
	{
		knight_footsteps(0.5);
	}
};

void() knight_painb8 = [ 38, knight_painb9 ]
{
	ai_painforward(5);
};

void() knight_painb9 = [ 39, knight_painb10 ]
{
	ai_painforward(5);
	if ((self.spawnflags & 2))
	{
		knight_statue_footsteps(0.6);
	}
	else
	{
		knight_footsteps(0.4);
	}
};

void() knight_painb10 = [ 40, knight_painb11 ]
{
	ai_painforward(0);
};

void() knight_painb11 = [ 41, knight_run1 ]
{
};

void(entity attacker, float damage) knight_pain =
{
	local float r;

	if ((self.model != "progs/knight_statue.mdl"))
	{
		random();
		if ((random() < (0.1 - (skill * 0.025))))
		{
			self.model = "progs/knight_pain.mdl";
			setmodel(self, "progs/knight_pain.mdl");
			knight_wounded1();
		}
	}
	if (((((self.model != "progs/knight_statue.mdl") && (self.health <= 26)) && (((self.enemy.weapon != IT_AXE) || (self.enemy.weapon != IT_ROCKET_LAUNCHER)) || (self.enemy.weapon != IT_GRENADE_LAUNCHER))) && (self.enemy.meleeing == 0)))
	{
		self.model = "progs/knight_pain.mdl";
		setmodel(self, "progs/knight_pain.mdl");
	}
	setsize(self, ARMY_MIN, ARMY_MAX);
	if ((self.pain_finished > time))
	{
		return;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_knight * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	r = random();
	if ((self.spawnflags & 2))
	{
		sound7(self, CHAN_VOICE, "statue/pain.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_VOICE, "knight/khurt.wav", 1, ATTN_NORM, SNDSPD);
	}
	if ((r < 0.85))
	{
		knight_pain1();
		self.pain_finished = (time + 1);
	}
	else
	{
		knight_painb1();
		self.pain_finished = (time + 1);
	}
};

void() knight_bow1 = [ 66, knight_bow2 ]
{
	ai_turn();
};

void() knight_bow2 = [ 67, knight_bow3 ]
{
	ai_turn();
	sound(self, CHAN_AUTO, "knight/pray.wav", 1, ATTN_IDLE);
};

void() knight_bow3 = [ 68, knight_bow4 ]
{
	ai_turn();
};

void() knight_bow4 = [ 69, knight_bow5 ]
{
	ai_turn();
};

void() knight_bow5 = [ 70, knight_bow5a ]
{
	ai_turn();
	self.nextthink = (time + 0.45);
};

void() knight_bow5a = [ 70, knight_bow5b ]
{
	ai_turn();
	self.nextthink = (time + 0.45);
};

void() knight_bow5b = [ 70, knight_bow5c ]
{
	ai_turn();
	self.nextthink = (time + 0.45);
};

void() knight_bow5c = [ 70, knight_bow5d ]
{
	ai_turn();
	self.nextthink = (time + 0.45);
};

void() knight_bow5d = [ 70, knight_bow6 ]
{
	ai_turn();
	self.nextthink = (time + 0.45);
};

void() knight_bow6 = [ 69, knight_bow7 ]
{
	ai_turn();
};

void() knight_bow7 = [ 68, knight_bow8 ]
{
	ai_turn();
};

void() knight_bow8 = [ 67, knight_bow9 ]
{
	ai_turn();
};

void() knight_bow9 = [ 66, knight_bow10 ]
{
	ai_turn();
};

void() knight_bow10 = [ 52, knight_walk1 ]
{
	ai_turn();
};

void() knight_pray1 = [ 66, knight_pray2 ]
{
	ai_stand();
};

void() knight_pray2 = [ 67, knight_pray3 ]
{
	ai_stand();
	sound(self, CHAN_AUTO, "knight/pray.wav", 1, ATTN_IDLE);
};

void() knight_pray3 = [ 68, knight_pray4 ]
{
	ai_stand();
};

void() knight_pray4 = [ 69, knight_pray5 ]
{
	ai_stand();
};

void() knight_pray5 = [ 70, knight_pray5a ]
{
	ai_stand();
	self.nextthink = (time + 0.45);
};

void() knight_pray5a = [ 70, knight_pray5b ]
{
	ai_stand();
	self.nextthink = (time + 0.45);
};

void() knight_pray5b = [ 70, knight_pray5c ]
{
	ai_stand();
	self.nextthink = (time + 0.45);
};

void() knight_pray5c = [ 70, knight_pray5d ]
{
	ai_stand();
	self.nextthink = (time + 0.45);
};

void() knight_pray5d = [ 70, knight_pray6 ]
{
	ai_stand();
	self.nextthink = (time + 0.45);
};

void() knight_pray6 = [ 69, knight_pray7 ]
{
	ai_stand();
};

void() knight_pray7 = [ 68, knight_pray8 ]
{
	ai_stand();
};

void() knight_pray8 = [ 67, knight_pray9 ]
{
	ai_stand();
};

void() knight_pray9 = [ 66, knight_pray10 ]
{
	ai_stand();
};

void() knight_pray10 = [ 0, knight_stand1 ]
{
	ai_stand();
};

void() knight_dieburn1 = [ 75, knight_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
};

void() knight_dieburn2 = [ 76, knight_dieburn3 ]
{
	self.burnz_origin = 11;
};

void() knight_dieburn3 = [ 77, knight_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
};

void() knight_dieburn4 = [ 78, knight_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() knight_dieburn5 = [ 79, knight_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() knight_dieburn6 = [ 80, knight_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() knight_dieburn7 = [ 81, knight_dieburn8 ]
{
	self.burnz_origin = -5;
};

void() knight_dieburn8 = [ 82, knight_dieburn9 ]
{
	self.burnz_origin = -7;
};

void() knight_dieburn9 = [ 83, knight_dieburn9 ]
{
	self.burnz_origin = -9;
};

void() knight_die1 = [ 75, knight_die2 ]
{
};

void() knight_die2 = [ 76, knight_die3 ]
{
	if ((self.model == "progs/knight_statue.mdl"))
	{
		pointparticles(particleeffectnum(/*54152i*/"statue_explode"), self.origin, VEC_ORIGIN, 1);
		ThrowGib("progs/gib_knarm_st.mdl", self.health);
		ThrowGib("progs/gib_s4.mdl", self.health);
		ThrowGib("progs/gib_s4.mdl", self.health);
		ThrowGib("progs/gib_knfoot_st.mdl", self.health);
		ThrowGib("progs/gib_knfoot_st.mdl", self.health);
		knight_die1();
		ThrowHead("progs/h_knight_st.mdl", self.health);
		sound(self, CHAN_VOICE, "ambience/coaled_monster_explode.wav", 1, ATTN_NORM);
		return;
	}
};

void() knight_die3 = [ 77, knight_die4 ]
{
	self.solid = 0;
};

void() knight_die4 = [ 78, knight_die5 ]
{
};

void() knight_die5 = [ 79, knight_die6 ]
{
};

void() knight_die6 = [ 80, knight_die7 ]
{
};

void() knight_die7 = [ 81, knight_die8 ]
{
	sound(self, CHAN_AUTO, "knight/fall_backwards.wav", 1, ATTN_IDLE);
};

void() knight_die8 = [ 82, knight_die9 ]
{
};

void() knight_die9 = [ 83, knight_die10 ]
{
};

void() knight_die10 = [ 83, knight_die11 ]
{
};

void() knight_die11 = [ 83, knight_die11 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 20;
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.spawnflags & 2))
	{
		CopyMonsterToBodyQue(autocvar_knightstatuecorpsehealth, "progs/gib_knarm_st.mdl");
	}
	else
	{
		if ((self.monstermodel == 0))
		{
			CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/h_knight.mdl");
		}
		if ((self.monstermodel == 1))
		{
			CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/h_knight1.mdl");
		}
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_knightrandomness = autocvar_knightrandomness * 0.01;
		if ((autocvar_knight == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_knightrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_knight == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_knightrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/knight.mdl", 92, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/knight1.mdl", 92, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_knight == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_knightrandomness))
					{
						vengeance_knight("progs/knight.mdl", 92);
					}
				}
				else
				{
					if ((autocvar_knight == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_knightrandomness))
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
										soul("progs/knight.mdl", 92, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/knight1.mdl", 92, zet);
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
			if ((zufall > 0.775))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.2))
				{
					if ((zufall < 0.004))
					{
						soul("progs/afrit.mdl", 64, 27.451);
					}
					else
					{
						if ((self.monstermodel == 0))
						{
							soul("progs/knight.mdl", 92, zet);
						}
						else
						{
							if ((self.monstermodel == 1))
							{
								soul("progs/knight1.mdl", 92, zet);
							}
						}
					}
				}
				else
				{
					vengeance_knight("progs/knight.mdl", 92);
				}
			}
		}
	}
};

void() knight_wounded1 = [ 96, knight_wounded2 ]
{
};

void() knight_wounded2 = [ 97, knight_wounded3 ]
{
};

void() knight_wounded3 = [ 98, knight_wounded4 ]
{
	setsize(self, VEC_HULL_MIN, '16 16 14');
};

void() knight_wounded4 = [ 99, knight_wounded5 ]
{
	sendParticle("bleed", self.origin, VEC_ORIGIN, 1, 0);
};

void() knight_wounded5 = [ 100, knight_wounded6 ]
{
};

void() knight_wounded6 = [ 101, knight_wounded7 ]
{
};

void() knight_wounded7 = [ 102, knight_wounded8 ]
{
};

void() knight_wounded8 = [ 101, knight_wounded9 ]
{
};

void() knight_wounded9 = [ 100, knight_wounded4 ]
{
	if (((random() * 100) < 10))
	{
		sound7(self, CHAN_VOICE, "knight/khurt1.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() knight_dieb1 = [ 84, knight_dieb2 ]
{
};

void() knight_dieb2 = [ 85, knight_dieb3 ]
{
	if ((self.model == "progs/knight_statue.mdl"))
	{
		pointparticles(particleeffectnum(/*54152i*/"statue_explode"), self.origin, VEC_ORIGIN, 1);
		ThrowGib("progs/gib_knarm_st.mdl", self.health);
		ThrowGib("progs/gib_s4.mdl", self.health);
		ThrowGib("progs/gib_s4.mdl", self.health);
		ThrowGib("progs/gib_knfoot_st.mdl", self.health);
		ThrowGib("progs/gib_knfoot_st.mdl", self.health);
		knight_die1();
		ThrowHead("progs/h_knight_st.mdl", self.health);
		sound(self, CHAN_VOICE, "ambience/coaled_monster_explode.wav", 1, ATTN_NORM);
		return;
	}
};

void() knight_dieb3 = [ 86, knight_dieb4 ]
{
	self.solid = 0;
};

void() knight_dieb4 = [ 87, knight_dieb5 ]
{
};

void() knight_dieb5 = [ 88, knight_dieb6 ]
{
};

void() knight_dieb6 = [ 89, knight_dieb7 ]
{
};

void() knight_dieb7 = [ 90, knight_dieb8 ]
{
};

void() knight_dieb8 = [ 91, knight_dieb9 ]
{
};

void() knight_dieb9 = [ 92, knight_dieb10 ]
{
	sound(self, CHAN_AUTO, "knight/fall_forwards.wav", 1, ATTN_IDLE);
};

void() knight_dieb10 = [ 93, knight_dieb11 ]
{
};

void() knight_dieb11 = [ 94, knight_dieb12 ]
{
};

void() knight_dieb12 = [ 95, knight_dieb12 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 20;
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/h_knight.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/h_knight1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/h_knight.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_knightrandomness = autocvar_knightrandomness * 0.01;
		if ((autocvar_knight == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_knightrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_knight == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_knightrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/knight.mdl", 94, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/knight1.mdl", 94, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_knight == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_knightrandomness))
					{
						vengeance_knight("progs/knight.mdl", 94);
					}
				}
				else
				{
					if ((autocvar_knight == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_knightrandomness))
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
										soul("progs/knight.mdl", 94, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/knight1.mdl", 94, zet);
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
			if ((zufall > 0.775))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.26))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/knight.mdl", 94, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/knight1.mdl", 94, zet);
						}
					}
				}
				else
				{
					vengeance_knight("progs/knight.mdl", 94);
				}
			}
		}
	}
};

void(float maxgibs, float gibscounter) producegibs_knight =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/gib1.mdl", self.health);
		ThrowGib("progs/gib2.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib_knfoot_l.mdl", self.health);
		ThrowGib("progs/gib_knfoot_r.mdl", self.health);
		ThrowWeapon("progs/w_knightsword.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_knight(maxgibs, gibscounter);
};

void(float maxgibs, float gibscounter) producegibs_knightstatue =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/statgib1.mdl", self.health);
		ThrowGib("progs/statgib2.mdl", self.health);
		ThrowGib("progs/statgib3.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_knightstatue(maxgibs, gibscounter);
};

void() knight_lightning_death = [ 28, knight_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() knight_lightning_death1 = [ 28, knight_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(1, "progs/h_knight.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(1, "progs/h_knight1.mdl");
	}
};

void() knight_inflamed1 = [ 9, knight_inflamed2 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.09);
	if ((random() < 0.8))
	{
		sound(self, CHAN_VOICE, "knight/khurt1.wav", 1, ATTN_NORM);
	}
};

void() knight_inflamed2 = [ 10, knight_inflamed3 ]
{
	ai_run_inflamed(20);
	knight_footsteps(0.9);
	self.nextthink = (time + 0.09);
};

void() knight_inflamed3 = [ 11, knight_inflamed4 ]
{
	ai_run_inflamed(13);
	self.nextthink = (time + 0.09);
};

void() knight_inflamed4 = [ 12, knight_inflamed5 ]
{
	ai_run_inflamed(7);
	self.nextthink = (time + 0.09);
};

void() knight_inflamed5 = [ 13, knight_inflamed6 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.09);
};

void() knight_inflamed6 = [ 14, knight_inflamed7 ]
{
	ai_run_inflamed(20);
	knight_footsteps(0.9);
	self.nextthink = (time + 0.09);
};

void() knight_inflamed7 = [ 15, knight_inflamed8 ]
{
	local float r;

	ai_run_inflamed(14);
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		knight_die();
		return;
	}
	r = random();
	if ((r < 0.22))
	{
		knight_inflamed9();
	}
	else
	{
		if ((r < 0.47))
		{
			knight_inflamed12();
		}
	}
};

void() knight_inflamed8 = [ 16, knight_inflamed1 ]
{
	ai_run_inflamed(6);
	self.nextthink = (time + 0.09);
};

void() knight_inflamed9 = [ 28, knight_inflamed10 ]
{
	if ((random() < 0.6))
	{
		sound(self, CHAN_VOICE, "knight/khurt1.wav", 1, ATTN_NORM);
	}
};

void() knight_inflamed10 = [ 29, knight_inflamed11 ]
{
};

void() knight_inflamed11 = [ 30, knight_inflamed8 ]
{
	if ((self.inflametime < time))
	{
		knight_die();
		return;
	}
};

void() knight_inflamed12 = [ 31, knight_inflamed13 ]
{
	ai_painforward(0);
	self.nextthink = (time + 0.08);
	if ((random() < 0.8))
	{
		sound(self, CHAN_VOICE, "knight/khurt1.wav", 1, ATTN_NORM);
	}
};

void() knight_inflamed13 = [ 32, knight_inflamed14 ]
{
	ai_painforward(3);
	self.nextthink = (time + 0.08);
};

void() knight_inflamed14 = [ 33, knight_inflamed15 ]
{
	self.nextthink = (time + 0.08);
};

void() knight_inflamed15 = [ 34, knight_inflamed16 ]
{
	self.nextthink = (time + 0.08);
};

void() knight_inflamed16 = [ 35, knight_inflamed17 ]
{
	ai_painforward(2);
	self.nextthink = (time + 0.08);
};

void() knight_inflamed17 = [ 36, knight_inflamed18 ]
{
	ai_painforward(4);
	self.nextthink = (time + 0.08);
};

void() knight_inflamed18 = [ 37, knight_inflamed19 ]
{
	ai_painforward(2);
	knight_footsteps(0.5);
	self.nextthink = (time + 0.08);
};

void() knight_inflamed19 = [ 38, knight_inflamed20 ]
{
	ai_painforward(5);
	self.nextthink = (time + 0.08);
};

void() knight_inflamed20 = [ 39, knight_inflamed21 ]
{
	ai_painforward(5);
	knight_footsteps(0.4);
	self.nextthink = (time + 0.08);
};

void() knight_inflamed21 = [ 40, knight_inflamed22 ]
{
	ai_painforward(0);
	self.nextthink = (time + 0.08);
};

void() knight_inflamed22 = [ 41, knight_inflamed8 ]
{
	self.nextthink = (time + 0.08);
	if ((self.inflametime < time))
	{
		knight_die();
		return;
	}
};

void() knight_dierl1 = [ 103, knight_dierl2 ]
{
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
};

void() knight_dierl2 = [ 104, knight_dierl3 ]
{
	if ((random() < 0.4))
	{
		sound(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE);
	}
};

void() knight_dierl3 = [ 105, knight_dierl4 ]
{
	self.solid = 0;
};

void() knight_dierl4 = [ 106, knight_dierl5 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dierl5 = [ 107, knight_dierl6 ]
{
};

void() knight_dierl6 = [ 108, knight_dierl7 ]
{
	sound(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dierl7 = [ 109, knight_dierl8 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dierl8 = [ 110, knight_dierl9 ]
{
};

void() knight_dierl9 = [ 111, knight_dierl10 ]
{
	sound(self, CHAN_AUTO, "knight/dropsword.wav", 1, ATTN_IDLE);
};

void() knight_dierl10 = [ 112, knight_dierl11 ]
{
};

void() knight_dierl11 = [ 113, knight_dierl12 ]
{
};

void() knight_dierl12 = [ 114, knight_dierl12 ]
{
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_l.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_r.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_l.mdl");
	}
};

void() knight_diessg1 = [ 103, knight_diessg2 ]
{
};

void() knight_diessg2 = [ 104, knight_diessg3 ]
{
	sound(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE);
};

void() knight_diessg3 = [ 105, knight_diessg4 ]
{
	self.solid = 0;
};

void() knight_diessg4 = [ 106, knight_diessg5 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_diessg5 = [ 107, knight_diessg6 ]
{
};

void() knight_diessg6 = [ 108, knight_diessg7 ]
{
	sound(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_diessg7 = [ 109, knight_diessg8 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_diessg8 = [ 110, knight_diessg9 ]
{
};

void() knight_diessg9 = [ 111, knight_diessg10 ]
{
	sound(self, CHAN_AUTO, "knight/dropsword.wav", 1, ATTN_IDLE);
};

void() knight_diessg10 = [ 112, knight_diessg11 ]
{
};

void() knight_diessg11 = [ 113, knight_diessg12 ]
{
};

void() knight_diessg12 = [ 114, knight_diessg13 ]
{
};

void() knight_diessg13 = [ 115, knight_diessg14 ]
{
};

void() knight_diessg14 = [ 116, knight_diessg15 ]
{
};

void() knight_diessg15 = [ 117, knight_diessg16 ]
{
};

void() knight_diessg16 = [ 118, knight_diessg17 ]
{
};

void() knight_diessg17 = [ 119, knight_diessg17 ]
{
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_l.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_r.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_l.mdl");
	}
};

void() knight_dieHSstart = [ 84, knight_dieHS0 ]
{
	ai_back(1);
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() knight_dieHS0 = [ 84, knight_dieHS1 ]
{
	sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() knight_dieHS1 = [ 84, knight_dieHS2 ]
{
};

void() knight_dieHS2 = [ 85, knight_dieHS3 ]
{
	if ((self.model == "progs/knight_statue.mdl"))
	{
		pointparticles(particleeffectnum(/*54152i*/"statue_explode"), self.origin, VEC_ORIGIN, 1);
		ThrowGib("progs/gib_knarm_st.mdl", self.health);
		ThrowGib("progs/gib_s4.mdl", self.health);
		ThrowGib("progs/gib_s4.mdl", self.health);
		ThrowGib("progs/gib_knfoot_st.mdl", self.health);
		ThrowGib("progs/gib_knfoot_st.mdl", self.health);
		knight_die1();
		ThrowHead("progs/h_knight_st.mdl", self.health);
		sound(self, CHAN_VOICE, "ambience/coaled_monster_explode.wav", 1, ATTN_NORM);
		return;
	}
};

void() knight_dieHS3 = [ 86, knight_dieHS4 ]
{
	self.solid = 0;
};

void() knight_dieHS4 = [ 87, knight_dieHS5 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() knight_dieHS5 = [ 88, knight_dieHS6 ]
{
};

void() knight_dieHS6 = [ 89, knight_dieHS7 ]
{
};

void() knight_dieHS7 = [ 90, knight_dieHS8 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() knight_dieHS8 = [ 91, knight_dieHS9 ]
{
};

void() knight_dieHS9 = [ 92, knight_dieHS10 ]
{
	sound7(self, CHAN_AUTO, "knight/fall_forwards.wav", 1, ATTN_IDLE);
};

void() knight_dieHS10 = [ 93, knight_dieHS11 ]
{
};

void() knight_dieHS11 = [ 94, knight_dieHS12 ]
{
};

void() knight_dieHS12 = [ 95, knight_dieHS12 ]
{
};

void() knight_dieng1 = [ 120, knight_dieng2 ]
{
};

void() knight_dieng2 = [ 121, knight_dieng3 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieng3 = [ 122, knight_dieng4 ]
{
	self.solid = 0;
};

void() knight_dieng4 = [ 123, knight_dieng5 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieng5 = [ 124, knight_dieng6 ]
{
};

void() knight_dieng6 = [ 125, knight_dieng7 ]
{
};

void() knight_dieng7 = [ 126, knight_dieng8 ]
{
};

void() knight_dieng8 = [ 127, knight_dieng9 ]
{
};

void() knight_dieng9 = [ 128, knight_dieng10 ]
{
};

void() knight_dieng10 = [ 129, knight_dieng11 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieng11 = [ 130, knight_dieng12 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieng12 = [ 131, knight_dieng13 ]
{
};

void() knight_dieng13 = [ 132, knight_dieng14 ]
{
};

void() knight_dieng14 = [ 133, knight_dieng15 ]
{
};

void() knight_dieng15 = [ 134, knight_dieng16 ]
{
};

void() knight_dieng16 = [ 135, knight_dieng17 ]
{
};

void() knight_dieng17 = [ 136, knight_dieng18 ]
{
};

void() knight_dieng18 = [ 137, knight_dieng19 ]
{
};

void() knight_dieng19 = [ 138, knight_dieng20 ]
{
};

void() knight_dieng20 = [ 139, knight_dieng21 ]
{
	sound7(self, CHAN_VOICE, "knight/fall_forwards.wav", 1, ATTN_IDLE);
};

void() knight_dieng21 = [ 140, knight_dieng22 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieng22 = [ 141, knight_dieng23 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieng23 = [ 142, knight_dieng24 ]
{
};

void() knight_dieng24 = [ 143, knight_dieng24 ]
{
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_kntorso_n.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_kntorso_b_n.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_kntorso_n.mdl");
	}
};

void() knight_diesng1 = [ 120, knight_diesng2 ]
{
};

void() knight_diesng2 = [ 121, knight_diesng3 ]
{
	sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
	ThrowGib("progs/gib_knarm_n.mdl", self.health);
};

void() knight_diesng3 = [ 122, knight_diesng4 ]
{
	self.solid = 0;
};

void() knight_diesng4 = [ 123, knight_diesng5 ]
{
	ThrowGib("progs/w_knightsword.mdl", self.health);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_diesng5 = [ 124, knight_diesng6 ]
{
};

void() knight_diesng6 = [ 125, knight_diesng7 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_diesng7 = [ 126, knight_diesng8 ]
{
	ThrowGib("progs/gib3.mdl", self.health);
};

void() knight_diesng8 = [ 127, knight_diesng9 ]
{
	sound7(self, CHAN_AUTO, "misc/swordbounce.wav", 1, ATTN_IDLE);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_diesng9 = [ 128, knight_diesng10 ]
{
};

void() knight_diesng10 = [ 129, knight_diesng11 ]
{
	ThrowGib("progs/chop.mdl", self.health);
	sound(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_diesng11 = [ 130, knight_diesng12 ]
{
};

void() knight_diesng12 = [ 131, knight_diesng13 ]
{
};

void() knight_diesng13 = [ 132, knight_diesng14 ]
{
};

void() knight_diesng14 = [ 133, knight_diesng15 ]
{
};

void() knight_diesng15 = [ 134, knight_diesng16 ]
{
};

void() knight_diesng16 = [ 135, knight_diesng17 ]
{
};

void() knight_diesng17 = [ 136, knight_diesng18 ]
{
};

void() knight_diesng18 = [ 137, knight_diesng19 ]
{
};

void() knight_diesng19 = [ 138, knight_diesng20 ]
{
};

void() knight_diesng20 = [ 139, knight_diesng21 ]
{
	sound7(self, CHAN_VOICE, "knight/fall_forwards.wav", 1, ATTN_IDLE);
};

void() knight_diesng21 = [ 140, knight_diesng22 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_diesng22 = [ 141, knight_diesng23 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_diesng23 = [ 142, knight_diesng24 ]
{
};

void() knight_diesng24 = [ 143, knight_diesng24 ]
{
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_l.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_r.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_l.mdl");
	}
};

void() knight_dieax1 = [ 145, knight_dieax2 ]
{
};

void() knight_dieax2 = [ 146, knight_dieax3 ]
{
	sound(self, CHAN_AUTO, "player/axeflesh3.wav", 1, ATTN_IDLE);
	sound(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE);
};

void() knight_dieax3 = [ 147, knight_dieax4 ]
{
	self.solid = 0;
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieax4 = [ 148, knight_dieax5 ]
{
	sound(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieax5 = [ 149, knight_dieax6 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieax6 = [ 150, knight_dieax7 ]
{
	sound(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieax7 = [ 151, knight_dieax8 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieax8 = [ 152, knight_dieax9 ]
{
};

void() knight_dieax9 = [ 153, knight_dieax10 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieax10 = [ 154, knight_dieax11 ]
{
	sound(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieax11 = [ 155, knight_dieax12 ]
{
	sound(self, CHAN_AUTO, "knight/dropsword.wav", 1, ATTN_IDLE);
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieax12 = [ 156, knight_dieax13 ]
{
};

void() knight_dieax13 = [ 157, knight_dieax14 ]
{
};

void() knight_dieax14 = [ 158, knight_dieax15 ]
{
};

void() knight_dieax15 = [ 159, knight_dieax16 ]
{
};

void() knight_dieax16 = [ 160, knight_dieax17 ]
{
};

void() knight_dieax17 = [ 161, knight_dieax18 ]
{
};

void() knight_dieax18 = [ 162, knight_dieax19 ]
{
};

void() knight_dieax19 = [ 163, knight_dieax20 ]
{
};

void() knight_dieax20 = [ 164, knight_dieax21 ]
{
	sound(self, CHAN_VOICE, "knight/fall_forwards.wav", 1, ATTN_IDLE);
};

void() knight_dieax21 = [ 165, knight_dieax22 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", (self.origin - '0 0 14'), VEC_ORIGIN, 1);
	}
};

void() knight_dieax22 = [ 166, knight_dieax23 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", (self.origin - '0 0 14'), VEC_ORIGIN, 1);
	}
};

void() knight_dieax23 = [ 167, knight_dieax24 ]
{
	sound(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieax24 = [ 168, knight_dieax24 ]
{
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_r.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_r.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_knfoot_r.mdl");
	}
};

void() knight_dieaxb1 = [ 145, knight_dieaxb2 ]
{
};

void() knight_dieaxb2 = [ 146, knight_dieaxb3 ]
{
	sound(self, CHAN_AUTO, "player/axeflesh3.wav", 1, ATTN_IDLE);
	sound(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE);
};

void() knight_dieaxb3 = [ 147, knight_dieaxb4 ]
{
	self.solid = 0;
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieaxb4 = [ 148, knight_dieaxb5 ]
{
	sound(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieaxb5 = [ 149, knight_dieaxb6 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieaxb6 = [ 150, knight_dieaxb7 ]
{
	sound(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieaxb7 = [ 151, knight_dieaxb8 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieaxb8 = [ 152, knight_dieaxb9 ]
{
};

void() knight_dieaxb9 = [ 153, knight_dieaxb10 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieaxb10 = [ 154, knight_dieaxb11 ]
{
	sound(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieaxb11 = [ 155, knight_dieaxb12 ]
{
	sound(self, CHAN_AUTO, "knight/fall_forwards.wav", 1, ATTN_IDLE);
	sound(self, CHAN_AUTO, "knight/dropsword.wav", 1, ATTN_IDLE);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieaxb12 = [ 156, knight_dieaxb13 ]
{
};

void() knight_dieaxb13 = [ 157, knight_dieaxb14 ]
{
};

void() knight_dieaxb14 = [ 158, knight_dieaxb15 ]
{
};

void() knight_dieaxb15 = [ 159, knight_dieaxb16 ]
{
};

void() knight_dieaxb16 = [ 160, knight_dieaxb17 ]
{
};

void() knight_dieaxb17 = [ 161, knight_dieaxb18 ]
{
};

void() knight_dieaxb18 = [ 162, knight_dieaxb19 ]
{
};

void() knight_dieaxb19 = [ 163, knight_dieaxb20 ]
{
};

void() knight_dieaxb20 = [ 164, knight_dieaxb21 ]
{
	sound(self, CHAN_VOICE, "knight/fall_forwards.wav", 1, ATTN_IDLE);
};

void() knight_dieaxb21 = [ 165, knight_dieaxb22 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*53047i*/"blood_spurt_corpse"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieaxb22 = [ 166, knight_dieaxb23 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*53047i*/"blood_spurt_corpse"), self.origin, VEC_ORIGIN, 1);
	}
};

void() knight_dieaxb23 = [ 167, knight_dieaxb24 ]
{
	sound(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE);
};

void() knight_dieaxb24 = [ 168, knight_dieaxb24 ]
{
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/h_knight.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/h_knight1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/h_knight.mdl");
	}
};

void() knight_die =
{
	local float maxgibs;
	local float gibscounter;
	local float zufa;
	local float zufall;
	local float randomness;

	if ((self.target || self.killtarget))
	{
		activator = self.enemy;
		SUB_UseTargets();
	}
	if (autocvar_lightninggun_death_animation)
	{
		if ((((self.enemy.weapon == IT_LIGHTNING) && (self.model != "progs/knight_statue.mdl")) && (self.enemy.meleeing == 0)))
		{
			knight_lightning_death();
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
	if ((((!self.shocked && (self.enemy.meleeing || self.axhitme)) && (autocvar_berserkmode > 0)) && (random() < 0.25)))
	{
		self.health = -10;
	}
	if ((((self.health < -40) || ((self.enemy.weapon == IT_CHAINSAW) && (random() < 0.5))) && (self.model != "progs/knight_statue.mdl")))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_knight * 0.01)))
			{
				the_matrix = 1;
				SNDSPD = 70;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		play_gibsound();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		if ((self.monstermodel == 0))
		{
			ThrowHead("progs/h_knight.mdl", self.health);
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				ThrowHead("progs/h_knight1.mdl", self.health);
			}
		}
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		gibdeath_effects();
		producegibs_knight(maxgibs, gibscounter);
		return;
	}
	if (autocvar_burning_monsters_death_animation)
	{
		if (((self.inflamed == 0) && (self.model != "progs/knight_statue.mdl")))
		{
			zufa = random() * 100;
			if ((((((self.enemy.weapon == IT_GRENADE_LAUNCHER) || (self.enemy.weapon == IT_ROCKET_LAUNCHER)) && (zufa <= autocvar_burning_monsters_death_animation)) && (self.watertype != CONTENT_WATER)) && (self.enemy.meleeing == 0)))
			{
				self.delete_painskin = 1;
				self.inflamed = 1;
				self.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
				self.inflametime = ((time + autocvar_burning_monsters_death_animation_time) + random());
				knight_inflamed1();
				return;
			}
		}
		else
		{
			sound(self, CHAN_VOICE, "knight/kdeath1.wav", 1, ATTN_NORM);
			if ((random() < 0.5))
			{
				knight_die1();
			}
			else
			{
				knight_dieb1();
			}
			return;
		}
	}
	autocvar_knightrandomness = autocvar_knightrandomness * 0.01;
	if ((autocvar_knight == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_knightrandomness))
		{
			self.delete_painskin = 1;
			knight_dieburn1();
			return;
		}
	}
	if ((autocvar_knight == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_knightrandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				knight_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_knight * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound(self, CHAN_VOICE, "knight/kdeath.wav", 1, ATTN_NORM);
	if ((random() < 0.5))
	{
		knight_die1();
	}
	else
	{
		knight_dieb1();
	}
	if (((self.enemy.meleeing == 0) && (self.model != "progs/knight_statue.mdl")))
	{
		if ((self.hitbox_pos == HEAD_SHOT))
		{
			if ((random() < 0.1))
			{
			}
			else
			{
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/gib_knhead.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/knight_headshot.mdl";
					setmodel(self, "progs/knight_headshot.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/knight_headshot.mdl";
					setmodel(self, "progs/knight_headshot.mdl");
					self.skin = 1;
				}
				knight_dieHSstart();
				return;
			}
		}
		if ((self.enemy.weapon == IT_SUPER_SHOTGUN))
		{
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			if (((random() > 0.5) && (random() < 0.9)))
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
					self.model = "progs/knightblast.mdl";
					setmodel(self, "progs/knightblast.mdl");
					self.skin = 0;
					ThrowGib("progs/h_knightblast.mdl", self.health);
				}
				else
				{
					self.model = "progs/knightblast.mdl";
					setmodel(self, "progs/knightblast.mdl");
					ThrowGib("progs/h_knightblast1.mdl", self.health);
					self.skin = 1;
				}
				knight_diessg1();
			}
		}
		else
		{
			if ((self.enemy.weapon == IT_ROCKET_LAUNCHER))
			{
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/gib3.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/knightgib.mdl";
					setmodel(self, "progs/knightgib.mdl");
					self.skin = 0;
					ThrowGib("progs/h_knightblast.mdl", self.health);
				}
				else
				{
					self.model = "progs/knightgib.mdl";
					setmodel(self, "progs/knightgib.mdl");
					ThrowGib("progs/h_knightblast1.mdl", self.health);
					self.skin = 1;
				}
				knight_dierl1();
			}
			else
			{
				if ((self.enemy.weapon == IT_NAILGUN))
				{
					if ((random() < 0.5))
					{
						ThrowGib("progs/chop.mdl", self.health);
						self.delete_painskin = 1;
						if ((self.skin == 0))
						{
							self.model = "progs/knightnail.mdl";
							setmodel(self, "progs/knightnail.mdl");
							self.skin = 0;
						}
						else
						{
							self.model = "progs/knightnail.mdl";
							setmodel(self, "progs/knightnail.mdl");
							self.skin = 1;
						}
						knight_dieng1();
					}
				}
				else
				{
					if (((self.enemy.weapon == IT_SUPER_NAILGUN) && (random() < 0.9)))
					{
						CeilSplat();
						CeilSplat();
						if (((random() > 0.4) || (self.hitbox_pos == HEAD_SHOT)))
						{
							ThrowGib("progs/gib3.mdl", self.health);
							ThrowGib("progs/chop.mdl", self.health);
							StickGib("progs/gib_knhead_n.mdl");
							self.delete_painskin = 1;
							if ((self.skin == 0))
							{
								self.model = "progs/knightsng.mdl";
								setmodel(self, "progs/knightsng.mdl");
								self.skin = 0;
							}
							else
							{
								self.model = "progs/knightsng.mdl";
								setmodel(self, "progs/knightsng.mdl");
								self.skin = 1;
							}
							knight_diesng1();
						}
						else
						{
							ThrowGib("progs/gib3.mdl", self.health);
							ThrowGib("progs/chop.mdl", self.health);
							if ((self.hitbox_pos == HEAD_SHOT))
							{
								StickGib("progs/gib_knhead_n.mdl");
							}
							else
							{
								ThrowGib("progs/gib_knhead_n.mdl", self.health);
							}
							self.delete_painskin = 1;
							if ((self.skin == 0))
							{
								self.model = "progs/knightsng2.mdl";
								setmodel(self, "progs/knightsng2.mdl");
								self.skin = 0;
								if ((random() > 0.5))
								{
									ThrowGib("progs/gib_kntorso_n.mdl", self.health);
								}
								else
								{
									StickGib("progs/gib_kntorso_n.mdl");
								}
							}
							else
							{
								self.model = "progs/knightsng2.mdl";
								setmodel(self, "progs/knightsng2.mdl");
								self.skin = 1;
								if ((random() > 0.5))
								{
									ThrowGib("progs/gib_kntorso_b_n.mdl", self.health);
								}
								else
								{
									StickGib("progs/gib_kntorso_b_n.mdl");
								}
							}
							knight_diesng1();
						}
					}
				}
			}
		}
		if (((self.enemy.weapon == IT_AXE) || (self.enemy.weapon == IT_CHAINSAW)))
		{
			if ((((random() > 0.5) && (random() < 0.9)) && (self.enemy.weapon == IT_CHAINSAW)))
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
					self.model = "progs/knightblast.mdl";
					setmodel(self, "progs/knightblast.mdl");
					self.skin = 0;
					ThrowGib("progs/h_knightblast.mdl", self.health);
				}
				else
				{
					self.model = "progs/knightblast.mdl";
					setmodel(self, "progs/knightblast.mdl");
					ThrowGib("progs/h_knightblast1.mdl", self.health);
					self.skin = 1;
				}
				knight_diessg1();
			}
			if ((random() <= 0.5))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/knightaxe2.mdl";
					setmodel(self, "progs/knightaxe2.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/knightaxe2.mdl";
					setmodel(self, "progs/knightaxe2.mdl");
					self.skin = 1;
				}
				knight_dieaxb1();
				ThrowGib("progs/chop.mdl", self.health);
			}
			else
			{
				if ((self.hitbox_pos == HEAD_SHOT))
				{
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/gib_knhead.mdl", self.health);
					self.delete_painskin = 1;
					if ((self.skin == 0))
					{
						self.model = "progs/knight_headshot.mdl";
						setmodel(self, "progs/knight_headshot.mdl");
						self.skin = 0;
					}
					else
					{
						self.model = "progs/knight_headshot.mdl";
						setmodel(self, "progs/knight_headshot.mdl");
						self.skin = 1;
					}
					knight_dieHSstart();
				}
				else
				{
					if ((autocvar_bloodextension == 1))
					{
						pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					self.delete_painskin = 1;
					if ((self.skin == 0))
					{
						self.model = "progs/knightaxe.mdl";
						setmodel(self, "progs/knightaxe.mdl");
						self.skin = 0;
					}
					else
					{
						self.model = "progs/knightaxe.mdl";
						setmodel(self, "progs/knightaxe.mdl");
						self.skin = 1;
					}
					knight_dieax1();
					ThrowGib("progs/chop.mdl", self.health);
				}
			}
		}
	}
};

void() knight_random_stand =
{
	if ((random() < 0.8))
	{
		self.th_stand = knight_stand1;
	}
	else
	{
		self.th_stand = knight_still;
	}
};

void() knight_pause =
{
	precache_sound("statue/see.wav");
	sound(self, CHAN_VOICE, "statue/see.wav", 1, ATTN_NORM);
	self.takedamage = DAMAGE_AIM;
	self.th_stand = knight_stand1;
	self.th_walk = knight_walk1;
	self.th_run = knight_run1;
	self.th_melee = knight_atk1;
	self.th_pain = knight_pain;
	self.th_die = knight_die;
	self.use = SUB_Null;
	self.think = knight_run1;
	self.enemy = activator;
	self.nextthink = (time + 0.1);
	self.think = FoundTarget;
	self.delay = 0;
	MonsterPhysics(self, autocvar_knightmass);
};

void() knight_pause1 =
{
	self.takedamage = 0;
	self.use = knight_pause;
	self.think = knight_pause1;
	self.nextthink = (time + 0.1);
};

void() monster_knight =
{
	local float zufall;
	local float zuffa;
	local float replacerrrrr;
	local float replacerrrr;
	local float replacerrr;
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
	precache_model("progs/knight.mdl");
	precache_model("progs/h_knight.mdl");
	precache_model("progs/knight_pain.mdl");
	precachegibs_knights();
	precache_model("progs/knight_headshot.mdl");
	precache_model("progs/knightblast.mdl");
	precache_model("progs/knightgib.mdl");
	precache_model("progs/h_knightblast.mdl");
	precache_model("progs/h_knightblast1.mdl");
	precache_model("progs/knightnail.mdl");
	precache_model("progs/knightsng.mdl");
	precache_model("progs/knightsng2.mdl");
	precache_model("progs/knightaxe.mdl");
	precache_model("progs/knightaxe2.mdl");
	precache_model("progs/gib_kntorso_n.mdl");
	precache_model("progs/gib_kntorso_b_n.mdl");
	precache_model("progs/gib_knhead_n.mdl");
	precache_model("progs/gib_knhead.mdl");
	precache_sound("knight/kdeath.wav");
	precache_sound("knight/khurt.wav");
	precache_sound("knight/kdeath1.wav");
	precache_sound("knight/khurt1.wav");
	precache_sound("knight/ksight.wav");
	precache_sound("knight/sword1.wav");
	precache_sound("knight/sword2.wav");
	precache_sound("knight/idle.wav");
	precache_sound("knight/fall_backwards.wav");
	precache_sound("knight/fall_forwards.wav");
	precache_sound("knight/pray.wav");
	precache_sound("walk/knight1.wav");
	precache_sound("walk/knight2.wav");
	precache_sound("walk/knight3.wav");
	precache_sound("walk/statue_knight1.wav");
	precache_sound("walk/statue_knight2.wav");
	precache_sound("walk/statue_knight3.wav");
	precache_sound("knight/dropsword.wav");
	precache_sound("statue/pain.wav");
	precache_sound("statue/idle.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((autocvar_knightmultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/knight.mdl");
		zufall = random();
		if ((self.spawnflags & 2))
		{
			self.skin = 2;
			self.monsterskin = 2;
			self.monstermodel = 0;
		}
		else
		{
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
	}
	else
	{
		if ((autocvar_knightmultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/knight1.mdl");
			precache_model("progs/h_knight1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/knight.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/knight1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_knightmultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/knight1.mdl");
				precache_model("progs/h_knight1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/knight.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/knight.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/knight1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_knightmultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/knight1.mdl");
					precache_model("progs/h_knight1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/knight.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/knight.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/knight1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/knight1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/knight.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_knight_size == 1))
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
				setsize(self, KNIGHT_MIN, KNIGHT_MAX);
			}
		}
	}
	else
	{
		if ((autocvar_knight_size == 2))
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
						setsize(self, KNIGHT_MIN, KNIGHT_MAX);
					}
				}
			}
		}
		else
		{
			if ((autocvar_knight_size == 3))
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
								setsize(self, KNIGHT_MIN, KNIGHT_MAX);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_knight_size == 4))
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
										setsize(self, KNIGHT_MIN, KNIGHT_MAX);
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_knight_size > 4))
					{
						if ((autocvar_knight_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_knight_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_knight_size * 0.25);
						self.sizediff = self.sizefactor;
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, KNIGHT_MIN, KNIGHT_MAX);
					}
				}
			}
		}
	}
	if ((autocvar_knight_size_influenced_health == 1))
	{
		self.health = (autocvar_knight_health + ((self.scale - 1) * 100));
	}
	else
	{
		self.health = autocvar_knight_health;
	}
	if ((cvar("skill") == 3))
	{
		self.health = (self.health * 1.16);
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_knight_random_skin_colors))
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
			self.frame = 49;
		}
		precache_model("progs/knight_statue.mdl");
		precache_model("progs/h_knight_st.mdl");
		precache_model("progs/gib_knfoot_st.mdl");
		precache_model("progs/gib_s4.mdl");
		precache_model("progs/gib_knarm_st.mdl");
		setmodel(self, "progs/knight_statue.mdl");
		setsize(self, VEC_HULL_MIN, '16 16 40');
		if (!self.targetname)
		{
			dprint("statue not targeted\n");
			dprint(self.classname);
			dprint(" at ");
			dprint(vtos(self.origin));
			dprint("\n");
			return;
		}
		self.use = knight_pause;
		self.th_stand = knight_pause1;
		self.th_walk = knight_pause1;
		self.th_run = knight_pause1;
		walkmonster_start();
	}
	else
	{
		if ((autocvar_knightpray == 1))
		{
			self.th_stand = knight_random_stand;
		}
		else
		{
			self.th_stand = knight_stand1;
		}
		self.th_walk = knight_walk1;
		self.th_run = knight_run1;
		self.th_melee = knight_atk1;
		self.th_pain = knight_pain;
		self.th_die = knight_die;
		self.alpha = (autocvar_monstertransparency * 0.01);
		if (autocvar_yakman_replace_knight)
		{
			replacerrrrr = autocvar_yakman_replace_knight * 0.01;
			if ((random() <= replacerrrrr))
			{
				self.health = (autocvar_knight_health + 50);
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 40');
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_yakman_start();
				return;
			}
		}
		if (autocvar_carnivean_replace_knight)
		{
			replacerrrr = autocvar_carnivean_replace_knight * 0.01;
			if ((random() <= replacerrrr))
			{
				self.health = autocvar_knight_health;
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 40');
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_carnivean_start();
				return;
			}
		}
		if (autocvar_torment_replace_knight)
		{
			replacerrr = autocvar_torment_replace_knight * 0.01;
			if ((random() <= replacerrr))
			{
				self.health = autocvar_knight_health;
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 40');
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_torment_start();
				return;
			}
		}
		if (autocvar_spider_replace_knight)
		{
			replacer = autocvar_spider_replace_knight * 0.01;
			if ((cvar("quadreplacer") > 0))
			{
				replacer = replacer + 0.03;
			}
			if ((random() <= replacer))
			{
				check = (self.origin - '0 0 20') + '0 0 1';
				if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
				{
					self.skin = 0;
					self.health = autocvar_knight_health;
					self.scale = 1;
					setsize(self, VEC_HULL_MIN, '16 16 40');
					self.nextthink = (time + 0.3);
					self.think = SUB_Remove;
					monster_spider_start();
					return;
				}
			}
		}
		if (autocvar_reiver_replace_knight)
		{
			replacez = autocvar_reiver_replace_knight * 0.01;
			if ((random() <= replacez))
			{
				self.health = (autocvar_knight_health + 25);
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 40');
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_reiver_liftorigin_start();
				return;
			}
		}
		if (autocvar_afrit_replace_knight)
		{
			replac = autocvar_afrit_replace_knight * 0.01;
			if ((random() <= replac))
			{
				self.health = autocvar_knight_health;
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
		if (autocvar_reiver_supports_knight)
		{
			replacce = autocvar_reiver_supports_knight * 0.01;
			if ((random() <= replacce))
			{
				add_reiver_support_walk();
			}
		}
		if (autocvar_afrit_supports_knight)
		{
			replace = autocvar_afrit_supports_knight * 0.01;
			if ((cvar("quadreplacer") > 0))
			{
				replace = replace + 0.01;
			}
			if ((random() <= replace))
			{
				add_afrit_support_walk();
			}
		}
		MonsterPhysics(self, autocvar_knightmass);
	}
};

void() vengeance_knight_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_knight_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_knight_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_run1 = [ 9, vengeance_knight_run2 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_knight_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_run2 = [ 10, vengeance_knight_run3 ]
{
	ai_face();
	movetogoal(26);
	self.touch = vengeance_knight_touch;
	self.alpha = 0.36;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_run3 = [ 11, vengeance_knight_run4 ]
{
	ai_face();
	movetogoal(20);
	self.touch = vengeance_knight_touch;
	self.alpha = 0.32;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_run4 = [ 12, vengeance_knight_run5 ]
{
	ai_face();
	movetogoal(14);
	self.touch = vengeance_knight_touch;
	self.alpha = 0.28;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_run5 = [ 13, vengeance_knight_runattack1 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_knight_touch;
	self.alpha = 0.24;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_runattack1 = [ 17, vengeance_knight_runattack2 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_knight_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_runattack2 = [ 18, vengeance_knight_runattack3 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_knight_touch;
	self.alpha = 0.18;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_runattack3 = [ 19, vengeance_knight_runattack4 ]
{
	ai_face();
	movetogoal(23);
	sound(self, CHAN_WEAPON, "knight/sword1.wav", 1, ATTN_NORM);
	self.touch = vengeance_knight_touch;
	self.alpha = 0.17;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_runattack4 = [ 20, vengeance_knight_runattack5 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_knight_touch;
	self.alpha = 0.16;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_runattack5 = [ 21, vengeance_knight_runattack6 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_knight_touch;
	self.alpha = 0.14;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_runattack6 = [ 22, vengeance_knight_runattack7 ]
{
	ai_face();
	movetogoal(23);
	if ((autocvar_quadreplacer > 0))
	{
		ai_melee_side_knight();
	}
	self.touch = vengeance_knight_touch;
	self.alpha = 0.12;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_runattack7 = [ 23, vengeance_knight_end1 ]
{
	ai_face();
	movetogoal(23);
	ai_melee_side_knight();
	self.touch = vengeance_knight_touch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 100) + '0 0 10');
	self.alpha = 0.1;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight11 = [ 83, vengeance_knight12 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight12 = [ 82, vengeance_knight13 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight13 = [ 81, vengeance_knight14 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight14 = [ 80, vengeance_knight15 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight15 = [ 79, vengeance_knight16 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight16 = [ 78, vengeance_knight17 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight17 = [ 77, vengeance_knight18 ]
{
	sound(self, CHAN_VOICE, "knight/ksight.wav", 1, ATTN_NORM);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight18 = [ 76, vengeance_knight19 ]
{
	self.alpha = 0.4;
	ai_face();
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight19 = [ 75, vengeance_knight_walk16 ]
{
	self.alpha = 0.4;
	ai_face();
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_walk16 = [ 57, vengeance_knight_run1 ]
{
	self.alpha = 0.4;
	ai_face();
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight21 = [ 93, vengeance_knight22 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight22 = [ 92, vengeance_knight23 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight23 = [ 91, vengeance_knight24 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight24 = [ 90, vengeance_knight25 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight25 = [ 89, vengeance_knight26 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight26 = [ 88, vengeance_knight27 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight27 = [ 87, vengeance_knight28 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight28 = [ 86, vengeance_knight29 ]
{
	sound(self, CHAN_VOICE, "knight/ksight.wav", 1, ATTN_NORM);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight29 = [ 85, vengeance_knight210 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight210 = [ 84, vengeance_knight_walk26 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_walk26 = [ 57, vengeance_knight_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_knight_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	if ((self.frame == 92))
	{
		self.think = vengeance_knight11;
	}
	else
	{
		self.think = vengeance_knight21;
	}
};

void() vengeance_knight_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_knight_bright05;
};

void() vengeance_knight_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_knight_bright04;
};

void() vengeance_knight_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_knight_bright03;
};

void() vengeance_knight_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_knight_bright02;
};

void() vengeance_knight_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_knight_bright01;
};

void(string modelname, float modelframe) vengeance_knight =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_STEP;
	self.inflamed = 0;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/knight.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/knight1.mdl");
		}
	}
	setsize(self, VEC_HULL_MIN, '16 16 40');
	self.frame = modelframe;
	self.solid = 0;
	MonsterPhysics(self, (autocvar_knightmass - 300));
	vengeance_knight_bright00();
};
