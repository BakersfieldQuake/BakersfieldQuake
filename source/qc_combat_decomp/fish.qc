//Decompiled code. Please respect the original copyright.

void() f_stand1 = [ 39, f_stand2 ]
{
	ai_stand();
};

void() f_stand2 = [ 40, f_stand3 ]
{
	ai_stand();
};

void() f_stand3 = [ 41, f_stand4 ]
{
	ai_stand();
};

void() f_stand4 = [ 42, f_stand5 ]
{
	ai_stand();
};

void() f_stand5 = [ 43, f_stand6 ]
{
	ai_stand();
};

void() f_stand6 = [ 44, f_stand7 ]
{
	ai_stand();
};

void() f_stand7 = [ 45, f_stand8 ]
{
	ai_stand();
};

void() f_stand8 = [ 46, f_stand9 ]
{
	ai_stand();
};

void() f_stand9 = [ 47, f_stand10 ]
{
	ai_stand();
};

void() f_stand10 = [ 48, f_stand11 ]
{
	ai_stand();
};

void() f_stand11 = [ 49, f_stand12 ]
{
	ai_stand();
};

void() f_stand12 = [ 50, f_stand13 ]
{
	ai_stand();
};

void() f_stand13 = [ 51, f_stand14 ]
{
	ai_stand();
};

void() f_stand14 = [ 52, f_stand15 ]
{
	ai_stand();
};

void() f_stand15 = [ 53, f_stand16 ]
{
	ai_stand();
};

void() f_stand16 = [ 54, f_stand17 ]
{
	ai_stand();
};

void() f_stand17 = [ 55, f_stand18 ]
{
	ai_stand();
};

void() f_stand18 = [ 56, f_stand1 ]
{
	ai_stand();
};

void() f_walk1 = [ 39, f_walk2 ]
{
	ai_walk(8);
};

void() f_walk2 = [ 40, f_walk3 ]
{
	ai_walk(8);
};

void() f_walk3 = [ 41, f_walk4 ]
{
	ai_walk(8);
};

void() f_walk4 = [ 42, f_walk5 ]
{
	ai_walk(8);
};

void() f_walk5 = [ 43, f_walk6 ]
{
	ai_walk(8);
};

void() f_walk6 = [ 44, f_walk7 ]
{
	ai_walk(8);
};

void() f_walk7 = [ 45, f_walk8 ]
{
	ai_walk(8);
};

void() f_walk8 = [ 46, f_walk9 ]
{
	ai_walk(8);
};

void() f_walk9 = [ 47, f_walk10 ]
{
	ai_walk(8);
};

void() f_walk10 = [ 48, f_walk11 ]
{
	ai_walk(8);
};

void() f_walk11 = [ 49, f_walk12 ]
{
	ai_walk(8);
};

void() f_walk12 = [ 50, f_walk13 ]
{
	ai_walk(8);
};

void() f_walk13 = [ 51, f_walk14 ]
{
	ai_walk(8);
};

void() f_walk14 = [ 52, f_walk15 ]
{
	ai_walk(8);
};

void() f_walk15 = [ 53, f_walk16 ]
{
	ai_walk(8);
};

void() f_walk16 = [ 54, f_walk17 ]
{
	ai_walk(8);
};

void() f_walk17 = [ 55, f_walk18 ]
{
	ai_walk(8);
};

void() f_walk18 = [ 56, f_walk1 ]
{
	ai_walk(8);
};

void() f_run1 = [ 39, f_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((11 + skill));
	if ((random() < 0.5))
	{
		sound(self, CHAN_VOICE, "fish/idle.wav", 1, ATTN_NORM);
	}
};

void() f_run2 = [ 41, f_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((11 + skill));
};

void() f_run3 = [ 43, f_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((11 + skill));
};

void() f_run4 = [ 45, f_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((11 + skill));
};

void() f_run5 = [ 47, f_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((11 + skill));
};

void() f_run6 = [ 49, f_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((11 + skill));
};

void() f_run7 = [ 51, f_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((11 + skill));
};

void() f_run8 = [ 53, f_run9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((11 + skill));
};

void() f_run9 = [ 55, f_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run((11 + skill));
};

void() fish_melee =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 60))
	{
		return;
	}
	sound(self, CHAN_VOICE, "fish/bite.wav", 1, ATTN_NORM);
	if ((autocvar_fish_size_influenced_attack == 1))
	{
		ldmg = ((random() + random()) * autocvar_fish_bite) * self.scale;
	}
	else
	{
		ldmg = (random() + random()) * autocvar_fish_bite;
	}
	T_Damage(self.enemy, self, self, ldmg);
};

void() f_attack1 = [ 0, f_attack2 ]
{
	ai_charge((10 + skill));
};

void() f_attack2 = [ 1, f_attack3 ]
{
	ai_charge((10 + skill));
};

void() f_attack3 = [ 2, f_attack4 ]
{
	fish_melee();
};

void() f_attack4 = [ 3, f_attack5 ]
{
	ai_charge((10 + skill));
};

void() f_attack5 = [ 4, f_attack6 ]
{
	ai_charge((10 + skill));
};

void() f_attack6 = [ 5, f_attack7 ]
{
	ai_charge((10 + skill));
};

void() f_attack7 = [ 6, f_attack8 ]
{
	ai_charge((10 + skill));
};

void() f_attack8 = [ 7, f_attack9 ]
{
	ai_charge((10 + skill));
};

void() f_attack9 = [ 8, f_attack10 ]
{
	fish_melee();
};

void() f_attack10 = [ 9, f_attack11 ]
{
	ai_charge((10 + skill));
};

void() f_attack11 = [ 10, f_attack12 ]
{
	ai_charge((10 + skill));
};

void() f_attack12 = [ 11, f_attack13 ]
{
	ai_charge((10 + skill));
};

void() f_attack13 = [ 12, f_attack14 ]
{
	ai_charge((10 + skill));
};

void() f_attack14 = [ 13, f_attack15 ]
{
	ai_charge((10 + skill));
};

void() f_attack15 = [ 14, f_attack16 ]
{
	fish_melee();
};

void() f_attack16 = [ 15, f_attack17 ]
{
	ai_charge((10 + skill));
};

void() f_attack17 = [ 16, f_attack18 ]
{
	ai_charge((10 + skill));
};

void() f_attack18 = [ 17, f_run1 ]
{
	ai_charge((10 + skill));
};

void() f_death1 = [ 18, f_death2 ]
{
	if ((((self.health < -18) || ((self.enemy.weapon == IT_CHAINSAW) || (self.enemy.weapon == IT_SHOTGUN))) || (self.enemy.weapon == IT_SUPER_SHOTGUN)))
	{
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		sendParticle("blood_monster_gib", self.origin, VEC_ORIGIN, 1, 0);
		ThrowHead("progs/h_fish.mdl", self.health);
		CeilSplat();
		CeilSplat();
		CeilSplat();
		sound(self, CHAN_VOICE, "misc/paste.wav", 1, ATTN_NORM);
		return;
	}
	sound(self, CHAN_VOICE, "fish/death.wav", 1, ATTN_NORM);
};

void() f_death2 = [ 19, f_death3 ]
{
};

void() f_death3 = [ 20, f_death4 ]
{
};

void() f_death4 = [ 21, f_death5 ]
{
};

void() f_death5 = [ 22, f_death6 ]
{
};

void() f_death6 = [ 23, f_death7 ]
{
};

void() f_death7 = [ 24, f_death8 ]
{
};

void() f_death8 = [ 25, f_death9 ]
{
};

void() f_death9 = [ 26, f_death10 ]
{
};

void() f_death10 = [ 27, f_death11 ]
{
};

void() f_death11 = [ 28, f_death12 ]
{
};

void() f_death12 = [ 29, f_death13 ]
{
};

void() f_death13 = [ 30, f_death14 ]
{
};

void() f_death14 = [ 31, f_death15 ]
{
};

void() f_death15 = [ 32, f_death16 ]
{
};

void() f_death16 = [ 33, f_death17 ]
{
};

void() f_death17 = [ 34, f_death18 ]
{
};

void() f_death18 = [ 35, f_death19 ]
{
};

void() f_death19 = [ 36, f_death20 ]
{
};

void() f_death20 = [ 37, f_death21 ]
{
};

void() f_death21 = [ 38, f_death21 ]
{
	self.solid = 0;
};

void() f_pain1 = [ 57, f_pain2 ]
{
};

void() f_pain2 = [ 58, f_pain3 ]
{
	ai_pain(6);
};

void() f_pain3 = [ 59, f_pain4 ]
{
	ai_pain(6);
};

void() f_pain4 = [ 60, f_pain5 ]
{
	ai_pain(6);
};

void() f_pain5 = [ 61, f_pain6 ]
{
	ai_pain(6);
};

void() f_pain6 = [ 62, f_pain7 ]
{
	ai_pain(6);
};

void() f_pain7 = [ 63, f_pain8 ]
{
	ai_pain(6);
};

void() f_pain8 = [ 64, f_pain9 ]
{
	ai_pain(6);
};

void() f_pain9 = [ 65, f_run1 ]
{
	ai_pain(6);
};

void(entity attacker, float damage) fish_pain =
{
	f_pain1();
};

void() monster_fish =
{
	local float zufall;
	local float zuffa;
	local float replac;
	local float replacce;
	local entity pain_skin_entity;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model2("progs/fish.mdl");
	precache_model2("progs/h_fish.mdl");
	precache_sound2("fish/death.wav");
	precache_sound2("fish/bite.wav");
	precache_sound2("fish/idle.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((autocvar_fishmultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/fish.mdl");
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
		if ((autocvar_fishmultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/fish1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/fish.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/fish1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_fishmultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/fish1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/fish.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/fish.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/fish1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_fishmultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/fish1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/fish.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/fish.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/fish1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/fish1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/fish.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_fish_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.28;
			self.sizediff = '0 0 3';
			setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.14;
				self.sizediff = '0 0 1';
				setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
			}
			else
			{
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 24');
			}
		}
	}
	else
	{
		if ((autocvar_fish_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.42;
				self.sizediff = '0 0 5';
				setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.28;
					self.sizediff = '0 0 3';
					setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.75))
					{
						self.scale = 1.14;
						self.sizediff = '0 0 1';
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, VEC_HULL_MIN, '16 16 24');
					}
				}
			}
		}
		else
		{
			if ((autocvar_fish_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.56;
					self.sizediff = '0 0 7';
					setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.42;
						self.sizediff = '0 0 5';
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.28;
							self.sizediff = '0 0 3';
							setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.14;
								self.sizediff = '0 0 1';
								setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
							}
							else
							{
								self.scale = 1;
								setsize(self, VEC_HULL_MIN, '16 16 24');
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_fish_size == 4))
				{
					zuffa = random();
					if ((zuffa <= 0.17))
					{
						self.scale = 1.7;
						self.sizediff = '0 0 9';
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.34))
						{
							self.scale = 1.56;
							self.sizediff = '0 0 7';
							setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.5))
							{
								self.scale = 1.42;
								self.sizediff = '0 0 5';
								setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
							}
							else
							{
								if ((zuffa <= 0.67))
								{
									self.scale = 1.28;
									self.sizediff = '0 0 3';
									setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
								}
								else
								{
									if ((zuffa <= 0.84))
									{
										self.scale = 1.14;
										self.sizediff = '0 0 1';
										setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
									}
									else
									{
										self.scale = 1;
										setsize(self, VEC_HULL_MIN, '16 16 24');
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_fish_size > 4))
					{
						if ((autocvar_fish_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_fish_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_fish_size * 0.25);
						self.sizediff = self.sizefactor;
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 24' - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, VEC_HULL_MIN, '16 16 24');
					}
				}
			}
		}
	}
	if ((autocvar_fish_size_influenced_health == 1))
	{
		self.health = (autocvar_fish_health + ((self.scale - 1) * 100));
	}
	else
	{
		self.health = autocvar_fish_health;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_fish_random_skin_colors))
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
	self.th_stand = f_stand1;
	self.th_walk = f_walk1;
	self.th_run = f_run1;
	self.th_die = f_death1;
	self.th_pain = fish_pain;
	self.th_melee = f_attack1;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_hydra_replace_fish)
	{
		replac = autocvar_hydra_replace_fish * 0.01;
		replac = replac + ((cvar("skill") * 0.01) + (cvar("quadreplacer") * 0.03));
		if ((random() <= replac))
		{
			self.health = autocvar_hydra_health;
			if (((cvar("skill") == 3) && (self.health < 100)))
			{
				self.health = 100;
			}
			self.health_initial = self.health;
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 24');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_hydra_start();
			return;
		}
	}
	if ((cvar("skill") > 0))
	{
		replacce = 0.02;
		if ((cvar("skill") == 3))
		{
			replacce = replacce + 0.015;
		}
		if ((cvar("quadreplacer") > 0))
		{
			replacce = replacce + 0.015;
		}
		if ((random() <= replacce))
		{
			add_reiver_support_walk();
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
	swimmonster_start();
	do_the_cloning__fly_swim();
	MonsterPhysics(self, autocvar_fishmass);
};
