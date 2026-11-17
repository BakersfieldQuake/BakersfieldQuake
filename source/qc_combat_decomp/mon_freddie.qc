//Decompiled code. Please respect the original copyright.

void(float loudness, float side) freddie_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.33))
		{
			sound7(self, CHAN_AUTO, self.stepc1, loudness, ATTN_IDLE, SNDSPD);
		}
		else
		{
			if ((select <= 0.66))
			{
				sound7(self, CHAN_AUTO, self.stepc2, loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_AUTO, self.stepc3, loudness, ATTN_IDLE, SNDSPD);
			}
		}
		if (((loudness > 0.8) && ((autocvar_shambler_walking_quake == 1) || (autocvar_shambler_walking_quake == 3))))
		{
			shambler_walking_quake();
		}
	}
};

void() fred_stand1 = [ 149, fred_stand2 ]
{
	monster_idle_sound();
	ai_stand();
};

void() fred_stand2 = [ 150, fred_stand3 ]
{
	ai_stand();
};

void() fred_stand3 = [ 151, fred_stand4 ]
{
	ai_stand();
};

void() fred_stand4 = [ 152, fred_stand5 ]
{
	ai_stand();
};

void() fred_stand5 = [ 153, fred_stand6 ]
{
	ai_stand();
};

void() fred_stand6 = [ 154, fred_stand7 ]
{
	ai_stand();
};

void() fred_stand7 = [ 155, fred_stand8 ]
{
	ai_stand();
};

void() fred_stand8 = [ 156, fred_stand1 ]
{
	ai_stand();
};

void() fred_walk1 = [ 0, fred_walk2 ]
{
	monster_idle_sound();
	ai_walk(20);
};

void() fred_walk2 = [ 1, fred_walk3 ]
{
	freddie_footsteps(1, 1);
	ai_walk(16);
};

void() fred_walk3 = [ 2, fred_walk4 ]
{
	ai_walk(1);
};

void() fred_walk4 = [ 3, fred_walk5 ]
{
	ai_walk(2);
};

void() fred_walk5 = [ 4, fred_walk6 ]
{
	ai_walk(4);
};

void() fred_walk6 = [ 5, fred_walk7 ]
{
	ai_walk(8);
};

void() fred_walk7 = [ 6, fred_walk8 ]
{
	ai_walk(4);
};

void() fred_walk8 = [ 7, fred_walk9 ]
{
	ai_walk(16);
};

void() fred_walk9 = [ 8, fred_walk10 ]
{
	ai_walk(20);
};

void() fred_walk10 = [ 9, fred_walk11 ]
{
	freddie_footsteps(1, 1);
	ai_walk(16);
};

void() fred_walk11 = [ 10, fred_walk12 ]
{
	ai_walk(1);
};

void() fred_walk12 = [ 11, fred_walk13 ]
{
	ai_walk(2);
};

void() fred_walk13 = [ 12, fred_walk14 ]
{
	ai_walk(4);
};

void() fred_walk14 = [ 13, fred_walk15 ]
{
	ai_walk(8);
};

void() fred_walk15 = [ 14, fred_walk16 ]
{
	ai_walk(4);
};

void() fred_walk16 = [ 15, fred_walk1 ]
{
	ai_walk(16);
};

void(vector weapofs) fred_fireweapon =
{
	local vector org;
	local vector dir;
	local vector vec;

	if ((self.health < 1))
	{
		return;
	}
	self.effects = (self.effects | EF_MUZZLEFLASH);
	self.attack_speed = (500 + (skill * 150));
	makevectors(self.angles);
	org = self.origin + attack_vector(weapofs);
	vec = v_right * (crandom() * (20 + (random() * 60)));
	dir = normalize(((self.enemy.origin + vec) - org));
	if ((random() < 0.2))
	{
		dir = dir + '0 0 4';
	}
	else
	{
		if ((random() < 0.1))
		{
			dir = dir + '0 0 -3';
		}
	}
	if ((self.spawnflags & MON_FREDDIE_LASER))
	{
		sound7(self, CHAN_WEAPON, "enforcer/enfire.wav", 1, ATTN_NORM, SNDSPD);
		LaunchLaser(org, dir);
	}
	else
	{
		sound7(self, CHAN_WEAPON, "weapons/spike2.wav", 1, ATTN_NORM, SNDSPD);
		launch_enemy_spike(org, dir);
		newmis.classname = "gruntspike";
	}
};

void() fred_sfire1 = [ 32, fred_sfire2 ]
{
	self.nextthink = (time + 0.07);
	ai_face();
	self.pain_finished = ((time + 0.5) + (skill * 0.5));
	sound7(self, CHAN_WEAPON, "freddie/stfire.wav", 1, ATTN_NORM, SNDSPD);
};

void() fred_sfire2 = [ 33, fred_sfire3 ]
{
	self.nextthink = (time + 0.08);
	ai_face();
};

void() fred_sfire3 = [ 34, fred_sfire4 ]
{
	self.nextthink = (time + 0.08);
	ai_face();
};

void() fred_sfire4 = [ 35, fred_sfire5 ]
{
	self.nextthink = (time + 0.08);
	ai_face();
};

void() fred_sfire5 = [ 36, fred_sfire6 ]
{
	self.nextthink = (time + 0.08);
	ai_face();
	freddie_footsteps(1, 1);
};

void() fred_sfire6 = [ 37, fred_sfire7 ]
{
	self.nextthink = (time + 0.08);
	ai_face();
};

void() fred_sfire7 = [ 38, fred_sfire8 ]
{
	self.nextthink = (time + 0.08);
	ai_face();
};

void() fred_sfire8 = [ 39, fred_sfire9 ]
{
	self.nextthink = (time + 0.08);
	ai_face();
	self.cnt = 0;
	self.attack_chance = (5 + (skill * 2));
	if ((random() < 0.1))
	{
		self.attack_chance = (self.attack_chance + 10);
	}
	else
	{
		if (((random() < 0.1) && (skill > 0)))
		{
			self.attack_chance = (self.attack_chance - skill);
		}
	}
};

void(vector weapofs) fred_standfire =
{
	if ((self.health < 1))
	{
		return;
	}
	ai_face();
	if ((!self.enemy || (self.enemy.health < 1)))
	{
		self.cnt = 100;
	}
	else
	{
		if (visxray(self.enemy, weapofs, VEC_ORIGIN, FALSE))
		{
			self.cnt = (self.cnt + 1);
		}
		else
		{
			self.cnt = 0;
		}
	}
	if ((self.cnt > self.attack_chance))
	{
		self.think = self.th_charge;
	}
	else
	{
		fred_fireweapon(weapofs);
	}
};

void() fred_sfire9 = [ 40, fred_sfire10 ]
{
	fred_standfire('45 -10 20');
};

void() fred_sfire10 = [ 41, fred_sfire11 ]
{
	fred_standfire('45 -10 20');
};

void() fred_sfire11 = [ 42, fred_sfire12 ]
{
	fred_standfire('45 -10 22');
};

void() fred_sfire12 = [ 43, fred_sfire13 ]
{
	fred_standfire('45 -10 22');
};

void() fred_sfire13 = [ 44, fred_sfire14 ]
{
	fred_standfire('45 -12 23');
};

void() fred_sfire14 = [ 45, fred_sfire15 ]
{
	fred_standfire('42 -12 25');
};

void() fred_sfire15 = [ 46, fred_sfire16 ]
{
	fred_standfire('42 -14 23');
	if (((self.health > 0) && (skill == 0)))
	{
		self.think = self.th_charge;
	}
};

void() fred_sfire16 = [ 47, fred_sfire17 ]
{
	fred_standfire('38 -14 27');
};

void() fred_sfire17 = [ 48, fred_sfire18 ]
{
	fred_standfire('38 -17 26');
};

void() fred_sfire18 = [ 49, fred_sfire19 ]
{
	fred_standfire('36 -17 28');
};

void() fred_sfire19 = [ 50, fred_sfire20 ]
{
	fred_standfire('36 -17 26');
	if (((self.health > 0) && (skill == 1)))
	{
		self.think = self.th_charge;
	}
};

void() fred_sfire20 = [ 51, fred_sfire21 ]
{
	fred_standfire('30 -17 28');
};

void() fred_sfire21 = [ 52, fred_sfire22 ]
{
	fred_standfire('30 -18 25');
};

void() fred_sfire22 = [ 53, fred_sfire23 ]
{
	fred_standfire('25 -18 27');
};

void() fred_sfire23 = [ 54, fred_sfire24 ]
{
	fred_standfire('25 -18 27');
};

void() fred_sfire24 = [ 55, fred_sfire25 ]
{
};

void() fred_sfire25 = [ 56, fred_sfire26 ]
{
};

void() fred_sfire26 = [ 57, fred_sfire27 ]
{
};

void() fred_sfire27 = [ 58, fred_run ]
{

	if (((random() < 0.8) && (vlen((self.enemy.origin - self.origin)) < 350)))
	{
		self.has_fired = 1;
	}
};

void() fred_runframe =
{

	if ((self.health < 1))
	{
		return;
	}
	if ((!self.enemy || (self.enemy.health < 1)))
	{
		self.attack_timer = 0;
	}
	if (self.attack_timer)
	{
		self.frame = (16 + self.walkframe);
	}
	else
	{
		self.frame = self.walkframe;
	}
	if ((self.walkframe == 0))
	{
		monster_idle_sound();
	}
	else
	{
		if ((self.walkframe == 1))
		{
			freddie_footsteps(1, 1);
		}
		else
		{
			if ((self.walkframe == 9))
			{
				freddie_footsteps(1, 1);
			}
		}
	}
	if ((self.walkframe == 0))
	{
		self.distance = 8;
		self.attack_offset = '50 -20 32';
	}
	else
	{
		if ((self.walkframe == 1))
		{
			self.distance = 18;
			self.attack_offset = '43 -18 33';
		}
		else
		{
			if ((self.walkframe == 2))
			{
				self.distance = 18;
				self.attack_offset = '53 -20 27';
			}
			else
			{
				if ((self.walkframe == 3))
				{
					self.distance = 8;
					self.attack_offset = '47 -19 31';
				}
				else
				{
					if ((self.walkframe == 4))
					{
						self.distance = 5;
						self.attack_offset = '54 -17 29';
					}
					else
					{
						if ((self.walkframe == 5))
						{
							self.distance = 2;
							self.attack_offset = '47 -17 35';
						}
						else
						{
							if ((self.walkframe == 6))
							{
								self.distance = 5;
								self.attack_offset = '53 -15 32';
							}
							else
							{
								if ((self.walkframe == 7))
								{
									self.distance = 8;
									self.attack_offset = '47 -15 36';
								}
								else
								{
									if ((self.walkframe == 8))
									{
										self.distance = 18;
										self.attack_offset = '50 -13 32';
									}
									else
									{
										if ((self.walkframe == 9))
										{
											self.distance = 18;
											self.attack_offset = '46 -15 33';
										}
										else
										{
											if ((self.walkframe == 10))
											{
												self.distance = 18;
												self.attack_offset = '51 -14 33';
											}
											else
											{
												if ((self.walkframe == 11))
												{
													self.distance = 8;
													self.attack_offset = '47 -14 32';
												}
												else
												{
													if ((self.walkframe == 12))
													{
														self.distance = 5;
														self.attack_offset = '52 -14 33';
													}
													else
													{
														if ((self.walkframe == 13))
														{
															self.distance = 2;
															self.attack_offset = '47 -14 36';
														}
														else
														{
															if ((self.walkframe == 14))
															{
																self.distance = 5;
																self.attack_offset = '49 -14 35';
															}
															else
															{
																if ((self.walkframe == 15))
																{
																	if ((random() < 0.4))
																	{
																		self.has_fired = 0;
																	}
																	self.distance = 8;
																	self.attack_offset = '45 -15 34';
																}
															}
														}
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	if ((self.attack_timer > 0))
	{
		ai_face();
		self.cnt = (self.cnt + 1);
		if ((self.cnt > 8))
		{
			self.attack_timer = 0;
		}
		else
		{
			fred_fireweapon(self.attack_offset);
		}
	}
	self.walkframe = (self.walkframe + 1);
	if ((self.walkframe > 15))
	{
		self.walkframe = 0;
	}
	if ((self.has_fired > 0))
	{
		self.nextthink = (time + 0.07);
	}
	else
	{
		self.nextthink = (time + 0.1);
	}
	self.think = fred_runframe;
	if ((self.has_fired && (vlen((self.enemy.origin - self.origin)) > 80)))
	{
		ai_charge((self.distance + (skill * 2.5)));
	}
	else
	{
		ai_run((self.distance + skill));
	}
};

void() fred_run =
{
	self.walkframe = 0;
	fred_runframe();
};

void(float side) fred_blade =
{
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	if ((self.health < 1))
	{
		return;
	}
	if (!ai_checkmelee(self.meleerange))
	{
		return;
	}
	if (!CanDamage(self.enemy, self))
	{
		return;
	}
	if (self.poisonous)
	{
		PoisonDeBuff(self.enemy);
	}
	sound7(self, CHAN_WEAPON, "freddie/mangle.wav", 1, ATTN_NORM, SNDSPD);
	ldmg = ((random() + random()) + random()) * 12;
	if ((ldmg < 1))
	{
		ldmg = 1;
	}
	T_Damage(self.enemy, self, self, ldmg, DAMARMOR);
	SpawnMeatSpray((self.origin + (v_forward * 16)), (side * v_right));
	SpawnMeatSpray((self.origin + (v_forward * 16)), (side * v_right));
};

void() fred_bswing1 = [ 98, fred_bswing2 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
	sound7(self, CHAN_WEAPON, "freddie/sawstart.wav", 1, ATTN_NORM, SNDSPD);
};

void() fred_bswing2 = [ 99, fred_bswing3 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_bswing3 = [ 100, fred_bswing4 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_bswing4 = [ 101, fred_bswing5 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
	freddie_footsteps(1, 1);
};

void() fred_bswing5 = [ 102, fred_bswing6 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
	fred_blade(200);
};

void() fred_bswing6 = [ 103, fred_bswing7 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_bswing7 = [ 104, fred_bswing8 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_bswing8 = [ 105, fred_bswing9 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_bswing9 = [ 106, fred_bswing10 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
	freddie_footsteps(1, 1);
};

void() fred_bswing10 = [ 107, fred_bswing11 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_bswing11 = [ 108, fred_bswing12 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_bswing12 = [ 109, fred_bswing13 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_bswing13 = [ 110, fred_bswing14 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_bswing14 = [ 111, fred_run ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswing1 = [ 77, fred_fswing2 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
	sound7(self, CHAN_WEAPON, "freddie/sawstart.wav", 1, ATTN_NORM, SNDSPD);
};

void() fred_fswing2 = [ 78, fred_fswing3 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
	freddie_footsteps(1, 1);
};

void() fred_fswing3 = [ 79, fred_fswing4 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() fred_fswing4 = [ 80, fred_fswing5 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
	freddie_footsteps(1, 1);
};

void() fred_fswing5 = [ 81, fred_fswing6 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() fred_fswing6 = [ 82, fred_fswing7 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() fred_fswing7 = [ 83, fred_fswing8 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() fred_fswing8 = [ 84, fred_fswing9 ]
{
	ai_face();
	fred_blade(-200);
	if ((random() < 0.7))
	{
		self.has_fired = 0;
	}
	self.nextthink = (time + 0.05);
};

void() fred_fswing9 = [ 85, fred_fswing10 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswing10 = [ 86, fred_fswing11 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswing11 = [ 87, fred_fswinge1 ]
{
	self.nextthink = (time + 0.05);
	if (((self.enemy && (self.enemy.health > 1)) && (self.health > 0)))
	{
		if (ai_checkmelee(self.meleerange))
		{
			self.think = fred_bswing1;
		}
	}
};

void() fred_fswinge1 = [ 88, fred_fswinge2 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswinge2 = [ 89, fred_fswinge3 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswinge3 = [ 90, fred_fswinge4 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswinge4 = [ 91, fred_fswinge5 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswinge5 = [ 92, fred_fswinge6 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswinge6 = [ 93, fred_fswinge7 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswinge7 = [ 94, fred_fswinge8 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswinge8 = [ 95, fred_fswinge9 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswinge9 = [ 96, fred_fswinge10 ]
{
	self.nextthink = (time + 0.05);
	ai_face();
};

void() fred_fswinge10 = [ 97, fred_run ]
{
	ai_face();
	freddie_footsteps(1, 1);
};

void() fred_pain1 = [ 60, fred_pain2 ]
{
	self.has_fired = 0;
};

void() fred_pain2 = [ 61, fred_pain3 ]
{
	ai_pain(10);
};

void() fred_pain3 = [ 62, fred_pain4 ]
{
	ai_pain(9);
};

void() fred_pain4 = [ 63, fred_pain5 ]
{
	ai_pain(4);
};

void() fred_pain5 = [ 64, fred_pain6 ]
{
};

void() fred_pain6 = [ 65, fred_pain7 ]
{
};

void() fred_pain7 = [ 66, fred_pain8 ]
{
};

void() fred_pain8 = [ 67, fred_pain9 ]
{
};

void() fred_pain9 = [ 68, fred_pain10 ]
{
};

void() fred_pain10 = [ 69, fred_pain11 ]
{
};

void() fred_pain11 = [ 70, fred_pain12 ]
{
};

void() fred_pain12 = [ 71, fred_run ]
{
};

void() fred_painb1 = [ 72, fred_painb2 ]
{
};

void() fred_painb2 = [ 73, fred_painb3 ]
{
};

void() fred_painb3 = [ 74, fred_painb4 ]
{
};

void() fred_painb4 = [ 75, fred_painb5 ]
{
};

void() fred_painb5 = [ 76, fred_run ]
{
};

void(entity inflictor, entity attacker, float damage) fred_pain =
{
	monster_pain_check(attacker, damage);
	if (((self.pain_check > 0) && (random() < 0.1)))
	{
		if ((random() < 0.2))
		{
			sound7(self, CHAN_VOICE, self.pain_sound, 1, ATTN_NORM, SNDSPD);
			self.pain_finished = ((time + 3) + (random() * 2));
			fred_pain1();
		}
		else
		{
			sound7(self, CHAN_VOICE, self.pain_sound2, 1, ATTN_NORM, SNDSPD);
			self.pain_finished = ((time + 2) + (random() * 2));
			fred_painb1();
		}
	}
};

void() fred_death1 = [ 112, fred_death2 ]
{
};

void() fred_death2 = [ 113, fred_death3 ]
{
};

void() fred_death3 = [ 114, fred_death4 ]
{
	self.solid = 0;
};

void() fred_death4 = [ 115, fred_death5 ]
{
};

void() fred_death5 = [ 116, fred_death6 ]
{
};

void() fred_death6 = [ 117, fred_death7 ]
{
};

void() fred_death7 = [ 118, fred_death8 ]
{
};

void() fred_death8 = [ 119, fred_death9 ]
{
};

void() fred_death9 = [ 120, fred_death10 ]
{
};

void() fred_death10 = [ 121, fred_death11 ]
{
};

void() fred_death11 = [ 122, fred_death12 ]
{
};

void() fred_death12 = [ 123, fred_death13 ]
{
};

void() fred_death13 = [ 124, fred_death14 ]
{
};

void() fred_death14 = [ 125, fred_death15 ]
{
};

void() fred_death15 = [ 126, fred_death16 ]
{
};

void() fred_death16 = [ 127, fred_death17 ]
{
};

void() fred_death17 = [ 128, fred_death18 ]
{
};

void() fred_death18 = [ 129, fred_death19 ]
{
};

void() fred_death19 = [ 130, fred_death20 ]
{
	Monster_Animation_EarthQuake(15, 377);
};

void() fred_death20 = [ 131, fred_death21 ]
{
};

void() fred_death21 = [ 132, fred_death22 ]
{
};

void() fred_death22 = [ 133, fred_death23 ]
{
};

void() fred_death23 = [ 134, fred_death24 ]
{
};

void() fred_death24 = [ 135, fred_death25 ]
{
};

void() fred_death25 = [ 136, fred_death26 ]
{
};

void() fred_death26 = [ 137, fred_death27 ]
{
};

void() fred_death27 = [ 138, fred_death28 ]
{
};

void() fred_death28 = [ 139, fred_death29 ]
{
};

void() fred_death29 = [ 140, fred_death30 ]
{
};

void() fred_death30 = [ 141, fred_death31 ]
{
};

void() fred_death31 = [ 142, fred_death32 ]
{
};

void() fred_death32 = [ 143, fred_death33 ]
{
	CopyMonsterToBodyQue(60, "progs/gib_ogre_h.mdl");
};

void() fred_death33 = [ 144, fred_death34 ]
{
};

void() fred_death34 = [ 145, fred_death35 ]
{
};

void() fred_death35 = [ 146, fred_death35 ]
{
};

void() fred_explode =
{
	entity_hide(self);
	self.max_health = 300;
	self.health = -100;
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord(MSG_BROADCAST, self.origin_x);
	WriteCoord(MSG_BROADCAST, self.origin_y);
	WriteCoord(MSG_BROADCAST, self.origin_z);
	T_RadiusDamage(self, self, self.death_dmg, world, DAMAGEALL);
	SpawnExplosion(EXPLODE_BIG, self.origin, self.death_sound);
	SpawnProjectileSmoke(self.origin, 200, 250, 100);
	SpawnProjectileSmoke(self.origin, 200, 250, 100);
	ThrowGib("progs/chop.mdl", self.health);
	ThrowGib("progs/chop.mdl", self.health);
	ThrowGib("progs/chop.mdl", self.health);
	ThrowGib("progs/gib_freddie_arm_sng.mdl", self.health);
	ThrowGib("progs/gib_freddie_arm_saw.mdl", self.health);
	ThrowHead("progs/gib_ogre_h.mdl", self.health);
	ThrowWeapon("progs/gib_freddie_leg.mdl", self.health);
	ThrowWeapon("progs/gib_freddie_leg.mdl", self.health);
	pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
};

void() fred_die =
{
	local entity dropitem;

	if (((!self.shocked && (self.enemy.weapon == IT_LIGHTNING)) && (self.sticky != 1)))
	{
		lg_death1();
		return;
	}
	if ((world.model != "maps/e2m1.bsp"))
	{
		dropitem = spawn();
		dropitem.origin = (self.origin + '0 0 -12');
		dropitem.movetype = MOVETYPE_TOSS;
		dropitem.health = 1;
		dropitem.think = item_spikes;
		dropitem.nextthink = (time + 0.1);
	}
	if (((self.health < -80) || (random() < 0.5)))
	{
		fred_explode();
		return;
	}
	if (!self.gibbed)
	{
		sound7(self, CHAN_VOICE, "freddie/death.wav", 1, ATTN_NORM, SNDSPD);
		fred_death1();
	}
};

void() monster_freddie =
{
	if (deathmatch)
	{
		remove(self);
		return;
	}
	self.mdl = "progs/mon_freddie.mdl";
	self.headmdl = "progs/h_ogre.mdl";
	precachegibs_freddie();
	self.classname = "monster_freddie";
	self.idle_sound = "freddie/idle1.wav";
	self.pain_sound = "freddie/pain.wav";
	self.pain_sound2 = "freddie/painshrt.wav";
	self.sight_sound = "freddie/sight.wav";
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.health = (300 + (cvar("skill") * 50));
	self.glow_size = 0;
	self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
	self.health_initial = self.health;
	self.gibhealth = -80;
	self.gibbed = 0;
	self.pain_flinch = 200;
	self.pain_longanim = 0;
	if (!self.infightextra)
	{
		self.infightextra = 2;
	}
	self.meleerange = 100;
	if ((self.death_dmg < 1))
	{
		self.death_dmg = 40;
	}
	self.pain_timeout = 2;
	self.blockudeath = TRUE;
	self.attack_offset = VEC_ORIGIN;
	self.poisonous = 0;
	self.stepc1 = "freddie/step.wav";
	self.stepc2 = "freddie/step2.wav";
	self.stepc3 = "freddie/step.wav";
	self.stepc4 = "freddie/step2.wav";
	self.stepc5 = "freddie/step3.wav";
	self.th_stand = fred_stand1;
	self.th_walk = fred_walk1;
	self.th_run = fred_run;
	self.th_melee = fred_fswing1;
	self.th_missile = fred_sfire1;
	self.th_charge = fred_sfire24;
	self.th_pain = fred_pain;
	self.th_die = fred_die;
	self.classtype = CT_MONFREDDIE;
	self.classmove = MON_MOVEWALK;
	monster_start();
	setsize(self, '-20 -20 -24', '20 20 56');
};

void() add_freddie_support_walk =
{
	local entity clone;
	local vector pos;

	pos = self.origin + '0 0 40';
	if (PM_InWall(self, pos))
	{
		return;
	}
	clone = spawn();
	copyentity(self, clone);
	setorigin(clone, pos);
	clone.think = monster_freddie;
	clone.nextthink = (time + 0.000100);
	remove(self);
};

void() monster_edie =
{
	monster_freddie();
};
