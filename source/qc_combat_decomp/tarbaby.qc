//Decompiled code. Please respect the original copyright.

void() tbaby_stand1 = [ 0, tbaby_stand1 ]
{
	ai_stand();
};

void() tbaby_hang1 = [ 0, tbaby_hang1 ]
{
	ai_stand();
};

void() tbaby_walk1 = [ 0, tbaby_walk2 ]
{
	ai_turn();
};

void() tbaby_walk2 = [ 1, tbaby_walk3 ]
{
	ai_turn();
};

void() tbaby_walk3 = [ 2, tbaby_walk4 ]
{
	ai_turn();
};

void() tbaby_walk4 = [ 3, tbaby_walk5 ]
{
	ai_turn();
};

void() tbaby_walk5 = [ 4, tbaby_walk6 ]
{
	ai_turn();
};

void() tbaby_walk6 = [ 5, tbaby_walk7 ]
{
	ai_turn();
};

void() tbaby_walk7 = [ 6, tbaby_walk8 ]
{
	ai_turn();
};

void() tbaby_walk8 = [ 7, tbaby_walk9 ]
{
	ai_turn();
};

void() tbaby_walk9 = [ 8, tbaby_walk10 ]
{
	ai_turn();
};

void() tbaby_walk10 = [ 9, tbaby_walk11 ]
{
	ai_turn();
};

void() tbaby_walk11 = [ 10, tbaby_walk12 ]
{
	ai_walk(2);
};

void() tbaby_walk12 = [ 11, tbaby_walk13 ]
{
	ai_walk(2);
};

void() tbaby_walk13 = [ 12, tbaby_walk14 ]
{
	ai_walk(2);
};

void() tbaby_walk14 = [ 13, tbaby_walk15 ]
{
	ai_walk(2);
};

void() tbaby_walk15 = [ 14, tbaby_walk16 ]
{
	ai_walk(2);
};

void() tbaby_walk16 = [ 15, tbaby_walk17 ]
{
	ai_walk(2);
};

void() tbaby_walk17 = [ 16, tbaby_walk18 ]
{
	ai_walk(2);
};

void() tbaby_walk18 = [ 17, tbaby_walk19 ]
{
	ai_walk(2);
};

void() tbaby_walk19 = [ 18, tbaby_walk20 ]
{
	ai_walk(2);
};

void() tbaby_walk20 = [ 19, tbaby_walk21 ]
{
	ai_walk(2);
};

void() tbaby_walk21 = [ 20, tbaby_walk22 ]
{
	ai_walk(2);
};

void() tbaby_walk22 = [ 21, tbaby_walk23 ]
{
	ai_walk(2);
};

void() tbaby_walk23 = [ 22, tbaby_walk24 ]
{
	ai_walk(2);
};

void() tbaby_walk24 = [ 23, tbaby_walk25 ]
{
	ai_walk(2);
};

void() tbaby_walk25 = [ 24, tbaby_walk1 ]
{
	ai_walk(2);
};

void() tbaby_run1 = [ 25, tbaby_run2 ]
{
	ai_face();
};

void() tbaby_run2 = [ 26, tbaby_run3 ]
{
	ai_face();
};

void() tbaby_run3 = [ 27, tbaby_run4 ]
{
	ai_face();
};

void() tbaby_run4 = [ 28, tbaby_run5 ]
{
	ai_face();
};

void() tbaby_run5 = [ 29, tbaby_run6 ]
{
	ai_face();
};

void() tbaby_run6 = [ 30, tbaby_run7 ]
{
	ai_face();
};

void() tbaby_run7 = [ 31, tbaby_run8 ]
{
	ai_face();
};

void() tbaby_run8 = [ 32, tbaby_run9 ]
{
	ai_face();
};

void() tbaby_run9 = [ 33, tbaby_run10 ]
{
	ai_face();
};

void() tbaby_run10 = [ 34, tbaby_run11 ]
{
	ai_face();
};

void() tbaby_run11 = [ 35, tbaby_run12 ]
{
	ai_run(2);
};

void() tbaby_run12 = [ 36, tbaby_run13 ]
{
	ai_run(2);
};

void() tbaby_run13 = [ 37, tbaby_run14 ]
{
	ai_run(2);
};

void() tbaby_run14 = [ 38, tbaby_run15 ]
{
	ai_run(2);
};

void() tbaby_run15 = [ 39, tbaby_run16 ]
{
	ai_run(2);
};

void() tbaby_run16 = [ 40, tbaby_run17 ]
{
	ai_run(2);
};

void() tbaby_run17 = [ 41, tbaby_run18 ]
{
	ai_run(2);
};

void() tbaby_run18 = [ 42, tbaby_run19 ]
{
	ai_run(2);
};

void() tbaby_run19 = [ 43, tbaby_run20 ]
{
	ai_run(2);
};

void() tbaby_run20 = [ 44, tbaby_run21 ]
{
	ai_run(2);
};

void() tbaby_run21 = [ 45, tbaby_run22 ]
{
	ai_run(2);
};

void() tbaby_run22 = [ 46, tbaby_run23 ]
{
	ai_run(2);
};

void() tbaby_run23 = [ 47, tbaby_run24 ]
{
	ai_run(2);
};

void() tbaby_run24 = [ 48, tbaby_run25 ]
{
	ai_run(2);
};

void() tbaby_run25 = [ 49, tbaby_run1 ]
{
	ai_run(2);
};

void() Tar_JumpTouch =
{
	local float ldmg;

	if (((other.takedamage && (other.classname != self.classname)) && (self.attack_timer == 0)))
	{
		if ((vlen(self.velocity) > 400))
		{
			if ((autocvar_tarbaby_size_influenced_attack == 1))
			{
				ldmg = (autocvar_tarbaby_jump * self.scale) + (10 * random());
			}
			else
			{
				ldmg = autocvar_tarbaby_jump + (10 * random());
			}
			T_Damage(other, self, self, ldmg);
			sound(self, CHAN_WEAPON, "blob/hit1.wav", 1, ATTN_NORM);
			if ((other.classname == "player"))
			{
				self.attack_timer = 1;
			}
		}
	}
	else
	{
		sound(self, CHAN_WEAPON, "blob/land1.wav", 1, ATTN_NORM);
	}
	if (!checkbottom(self))
	{
		if ((self.flags & FL_ONGROUND))
		{
			self.touch = SUB_Null;
			self.think = tbaby_run1;
			self.movetype = MOVETYPE_STEP;
			self.nextthink = (time + 0.1);
		}
		if ((self.origin == self.old_origin))
		{
			self.touch = SUB_Null;
			self.flags = (self.flags & FL_ONGROUND);
			makevectors(self.angles);
			self.velocity = (((v_forward * (random() - 0.5)) * 500) + '0 0 200');
			self.think = tbaby_jump1;
			self.nextthink = (time + 0.2);
		}
		self.old_origin = self.origin;
		return;
	}
	self.touch = SUB_Null;
	self.think = tbaby_jump1;
	self.nextthink = (time + 0.1);
};

void() tbaby_fly1 = [ 56, tbaby_fly2 ]
{
};

void() tbaby_fly2 = [ 57, tbaby_fly3 ]
{
};

void() tbaby_fly3 = [ 58, tbaby_fly4 ]
{
};

void() tbaby_fly4 = [ 59, tbaby_fly1 ]
{
	self.cnt = (self.cnt + 1);
	if ((self.cnt == 4))
	{
		tbaby_jump5();
	}
};

void() tbaby_jump1 = [ 50, tbaby_jump2 ]
{
	ai_face();
	self.colormod = '1 1 1.3';
	self.attack_timer = 0;
};

void() tbaby_jump2 = [ 51, tbaby_jump3 ]
{
	ai_face();
	self.colormod = '1 1 1.6';
};

void() tbaby_jump3 = [ 52, tbaby_jump4 ]
{
	ai_face();
	self.colormod = '1 1 1.9';
};

void() tbaby_jump4 = [ 53, tbaby_jump5 ]
{
	ai_face();
	self.colormod = '1 1 2.1';
};

void() tbaby_jump5 = [ 54, tbaby_jump6 ]
{
	self.movetype = MOVETYPE_BOUNCE;
	self.touch = Tar_JumpTouch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 600) + '0 0 200');
	self.velocity_z = (self.velocity_z + (random() * 150));
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
	self.cnt = 0;
};

void() tbaby_jump6 = [ 55, tbaby_fly1 ]
{
	self.colormod = '1 1 2.5';
};

void() tbaby_die1 = [ 60, tbaby_die2 ]
{
	gibbed_monsters = gibbed_monsters + 1;
	self.takedamage = 0;
};

void() tbaby_die2 = [ 60, tbaby_run1 ]
{

	if ((autocvar_tarbaby_size_influenced_attack == 1))
	{
		T_RadiusDamage(self, self, (autocvar_tarbaby_explode * self.scale), world);
	}
	else
	{
		T_RadiusDamage(self, self, autocvar_tarbaby_explode, world);
	}
	sound(self, CHAN_VOICE, "blob/death1.wav", 1, ATTN_NORM);
	self.origin = (self.origin - (8 * normalize(self.velocity)));
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_TAREXPLOSION);
	WriteCoord(MSG_BROADCAST, self.origin_x);
	WriteCoord(MSG_BROADCAST, self.origin_y);
	WriteCoord(MSG_BROADCAST, self.origin_z);
	BecomeExplosion();
};

void() monster_tarbaby =
{
	local float zufall;
	local float zuffa;
	local float replacer;
	local vector check;
	local float replacez;
	local float replac;
	local float replacce;
	local float replace;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model2("progs/tarbaby.mdl");
	precache_sound2("blob/death1.wav");
	precache_sound2("blob/hit1.wav");
	precache_sound2("blob/land1.wav");
	precache_sound2("blob/sight1.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((autocvar_tarbabymultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/tarbaby.mdl");
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
		if ((autocvar_tarbabymultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/tarbaby1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/tarbaby.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/tarbaby1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_tarbabymultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/tarbaby1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/tarbaby.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/tarbaby.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/tarbaby1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_tarbabymultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/tarbaby1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/tarbaby.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/tarbaby.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/tarbaby1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/tarbaby1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/tarbaby.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_tarbaby_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.14;
			setsize(self, '-16 -16 -27', '16 16 37');
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.07;
				setsize(self, '-16 -16 -25', '16 16 39');
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
		if ((autocvar_tarbaby_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.21;
				setsize(self, '-16 -16 -29', '16 16 35');
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.14;
					setsize(self, '-16 -16 -27', '16 16 37');
				}
				else
				{
					if ((zuffa <= 0.75))
					{
						self.scale = 1.07;
						setsize(self, '-16 -16 -25', '16 16 39');
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
			if ((autocvar_tarbaby_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.28;
					setsize(self, '-16 -16 -31', '16 16 33');
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.21;
						setsize(self, '-16 -16 -29', '16 16 35');
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.14;
							setsize(self, '-16 -16 -27', '16 16 37');
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.07;
								setsize(self, '-16 -16 -25', '16 16 39');
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
				if ((autocvar_tarbaby_size == 4))
				{
					zuffa = random();
					if ((zuffa <= 0.17))
					{
						self.scale = 1.35;
						setsize(self, '-16 -16 -33', '16 16 31');
					}
					else
					{
						if ((zuffa <= 0.34))
						{
							self.scale = 1.28;
							setsize(self, '-16 -16 -31', '16 16 33');
						}
						else
						{
							if ((zuffa <= 0.5))
							{
								self.scale = 1.21;
								setsize(self, '-16 -16 -29', '16 16 35');
							}
							else
							{
								if ((zuffa <= 0.67))
								{
									self.scale = 1.14;
									setsize(self, '-16 -16 -27', '16 16 37');
								}
								else
								{
									if ((zuffa <= 0.84))
									{
										self.scale = 1.07;
										setsize(self, '-16 -16 -25', '16 16 39');
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
					if ((autocvar_tarbaby_size > 4))
					{
						if ((autocvar_tarbaby_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_tarbaby_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_tarbaby_size * 0.25);
						setsize(self, (VEC_HULL_MIN - self.sizefactor), ('16 16 40' - self.sizefactor));
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
	if ((autocvar_tarbaby_size_influenced_health == 1))
	{
		self.health = (autocvar_tarbaby_health + ((self.scale - 1) * 100));
	}
	else
	{
		self.health = autocvar_tarbaby_health;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_tarbaby_random_skin_colors))
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
	self.th_stand = tbaby_stand1;
	self.th_walk = tbaby_walk1;
	self.th_run = tbaby_run1;
	self.th_missile = tbaby_jump1;
	self.th_melee = tbaby_jump1;
	self.th_die = tbaby_die1;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_spider_replace_tarbaby)
	{
		replacer = autocvar_spider_replace_tarbaby * 0.01;
		if ((random() <= replacer))
		{
			check = (self.origin - '0 0 20') + '0 0 1';
			if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
			{
				self.skin = 3;
				self.health = autocvar_tarbaby_health;
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 40');
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_spider_start();
				return;
			}
		}
	}
	if (autocvar_reiver_replace_tarbaby)
	{
		replacez = autocvar_reiver_replace_tarbaby * 0.01;
		if ((random() <= replacez))
		{
			self.health = autocvar_tarbaby_health;
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_reiver_liftorigin_start();
			return;
		}
	}
	if (autocvar_afrit_replace_tarbaby)
	{
		replac = autocvar_afrit_replace_tarbaby * 0.01;
		if ((random() <= replac))
		{
			self.health = autocvar_tarbaby_health;
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_afrit_liftorigin_start();
			return;
		}
	}
	walkmonster_start();
	do_the_cloning();
	if (autocvar_reiver_supports_tarbaby)
	{
		if ((cvar("skill") == 3))
		{
			replacce = (autocvar_reiver_supports_tarbaby + 1) * 0.01;
		}
		else
		{
			replacce = autocvar_reiver_supports_tarbaby * 0.01;
		}
		if ((cvar("quadreplacer") > 0))
		{
			replacce = replacce + 0.01;
		}
		if ((random() <= replacce))
		{
			add_reiver_support_walk();
		}
	}
	if (autocvar_afrit_supports_tarbaby)
	{
		replace = autocvar_afrit_supports_tarbaby * 0.01;
		if (((cvar("skill") == 3) && (replace > 0)))
		{
			replace = replace + 0.01;
		}
		if ((cvar("quadreplacer") > 0))
		{
			replace = replace + 0.01;
		}
		if ((random() <= replace))
		{
			add_afrit_support_walk();
		}
	}
	MonsterPhysics(self, autocvar_tarbabymass);
};
