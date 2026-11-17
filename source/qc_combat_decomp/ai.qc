//Decompiled code. Please respect the original copyright.

float(float v) anglemod =
{
	while ((v >= 360))
	{
		v = v - 360;
	}
	while ((v < 0))
	{
		v = v + 360;
	}
	return (v);
};

void() movetarget_f =
{
	if (!self.targetname)
	{
		objerror("monster_movetarget: no targetname");
	}
	self.solid = SOLID_TRIGGER;
	self.touch = t_movetarget;
	setsize(self, '-8 -8 -8', '8 8 8');
};

void() path_corner =
{
	movetarget_f();
};

void() t_movetarget =
{
	local entity temp;

	if ((other.movetarget != self))
	{
		return;
	}
	if (other.enemy)
	{
		return;
	}
	temp = self;
	self = other;
	other = temp;
	if ((self.classname == "monster_ogre"))
	{
		sound(self, CHAN_VOICE, "ogre/ogdrag.wav", 1, ATTN_IDLE);
	}
	self.movetarget = find(world, targetname, other.target);
	self.goalentity = find(world, targetname, other.target);
	self.ideal_yaw = vectoyaw((self.goalentity.origin - self.origin));
	if (!self.movetarget)
	{
		self.pausetime = (time + 999999);
		self.th_stand();
		return;
	}
};

float(entity targ) range =
{
	local vector spot1;
	local vector spot2;
	local float r;

	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	r = vlen((spot1 - spot2));
	if ((r < 120))
	{
		return (0);
	}
	if ((r < 500))
	{
		return (RANGE_NEAR);
	}
	if ((r < (1000 + (skill * 50))))
	{
		return (RANGE_MID);
	}
	return (RANGE_FAR);
};

float(entity targ) visible =
{
	local vector spot1;
	local vector spot2;

	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	traceline(spot1, spot2, TRUE, self);
	if ((trace_inopen && trace_inwater))
	{
		return (0);
	}
	if ((trace_fraction == 1))
	{
		return (TRUE);
	}
	return (0);
};

float(entity targ) infront =
{
	local vector vec;
	local float dot;

	makevectors(self.angles);
	vec = normalize((targ.origin - self.origin));
	dot = vec * v_forward;
	if ((dot > 0.3))
	{
		return (TRUE);
	}
	return (0);
};

void() HuntTarget =
{
	self.goalentity = self.enemy;
	self.think = self.th_run;
	self.ideal_yaw = vectoyaw((self.enemy.origin - self.origin));
	self.nextthink = (time + 0.1);
	SUB_AttackFinished(1);
};

void() SightSound =
{
	local float rsnd;

	if ((self.classname == "monster_ogre"))
	{
		sound7(self, CHAN_VOICE, "ogre/ogwake.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((self.classname == "monster_knight"))
		{
			if (((skill == 3) && (random() < 0.6)))
			{
			}
			else
			{
				sound7(self, CHAN_VOICE, "knight/ksight.wav", 1, ATTN_NORM, SNDSPD);
			}
		}
		else
		{
			if ((self.classname == "monster_shambler"))
			{
				sound7(self, CHAN_VOICE, "shambler/ssight.wav", 1, ATTN_NORM, SNDSPD);
			}
			else
			{
				if ((self.classname == "monster_demon1"))
				{
					if ((self.monstermodel == 2))
					{
						sound7(self, CHAN_VOICE, "teneb/sight.wav", 1, ATTN_NORM, SNDSPD);
					}
					else
					{
						if (((self.alpha < 0.2) && (self.demon_on_fire == 1)))
						{
							sound7(self, CHAN_VOICE, "shalrath/growl.wav", 1, ATTN_NORM, SNDSPD);
						}
						else
						{
							sound7(self, CHAN_VOICE, "demon/sight2.wav", 1, ATTN_NORM, SNDSPD);
						}
					}
				}
				else
				{
					if ((self.classname == "monster_voreling"))
					{
						sound7(self, CHAN_VOICE, "voreling/sight.wav", 1, ATTN_NORM, SNDSPD);
					}
					else
					{
						if ((self.classname == "monster_wizard"))
						{
							sound7(self, CHAN_VOICE, "wizard/wsight.wav", 1, ATTN_NORM, SNDSPD);
						}
						else
						{
							if ((self.classname == "monster_zombie"))
							{
								sound7(self, CHAN_VOICE, "zombie/z_idle.wav", 1, ATTN_NORM, SNDSPD);
							}
							else
							{
								if ((self.classname == "monster_dog"))
								{
									if (((skill == 3) && (random() < 0.6)))
									{
									}
									else
									{
										sound7(self, CHAN_VOICE, "dog/dsight.wav", 1, ATTN_NORM, SNDSPD);
									}
								}
								else
								{
									if ((self.classname == "monster_hell_knight"))
									{
										sound7(self, CHAN_VOICE, "hknight/sight1.wav", 1, ATTN_NORM, SNDSPD);
									}
									else
									{
										if ((self.classname == "monster_hell_knight2"))
										{
											sound7(self, CHAN_VOICE, "warlord/sight1.wav", 1, ATTN_NORM, SNDSPD);
										}
										else
										{
											if ((self.classname == "monster_dfury"))
											{
												sound7(self, CHAN_VOICE, "dfury/sight1.wav", 1, ATTN_NORM, SNDSPD);
											}
											else
											{
												if ((self.classname == "monster_dfury_boss"))
												{
													sound7(self, CHAN_AUTO, "dfury/sight1.wav", 1, ATTN_NONE);
												}
												else
												{
													if ((self.classname == "monster_tarbaby"))
													{
														sound7(self, CHAN_VOICE, "blob/sight1.wav", 1, ATTN_NORM, SNDSPD);
													}
													else
													{
														if ((self.classname == "monster_vomit"))
														{
															sound7(self, CHAN_VOICE, "vomitus/v_sight1.wav", 1, ATTN_NORM, SNDSPD);
														}
														else
														{
															if ((self.classname == "monster_jim"))
															{
																sound7(self, CHAN_VOICE, "jim/sight1.wav", 1, ATTN_NORM, SNDSPD);
															}
															else
															{
																if ((self.classname == "monster_freddie"))
																{
																	sound7(self, CHAN_VOICE, "freddie/sight.wav", 1, ATTN_NORM, SNDSPD);
																}
																else
																{
																	if ((self.classname == "monster_enforcer"))
																	{
																		rsnd = rint((random() * 3));
																		if ((self.skin == 1))
																		{
																			sound7(self, CHAN_VOICE, "enforcer/def_sight1.wav", 1, ATTN_NORM, SNDSPD);
																		}
																		else
																		{
																			if ((rsnd == 1))
																			{
																				sound7(self, CHAN_VOICE, "enforcer/sight1.wav", 1, ATTN_NORM, SNDSPD);
																			}
																			else
																			{
																				if ((rsnd == 2))
																				{
																					sound7(self, CHAN_VOICE, "enforcer/sight2.wav", 1, ATTN_NORM, SNDSPD);
																				}
																				else
																				{
																					if ((rsnd == 0))
																					{
																						sound7(self, CHAN_VOICE, "enforcer/sight3.wav", 1, ATTN_NORM, SNDSPD);
																					}
																					else
																					{
																						sound7(self, CHAN_VOICE, "enforcer/sight4.wav", 1, ATTN_NORM, SNDSPD);
																					}
																				}
																			}
																		}
																		random();
																		if (((random() < (0.05 + (skill * 0.05))) && (enemy_range == RANGE_NEAR)))
																		{
																			self.has_fired = 1;
																		}
																	}
																	else
																	{
																		if ((self.classname == "monster_army"))
																		{
																			sound7(self, CHAN_VOICE, "soldier/sight1.wav", 1, ATTN_NORM, SNDSPD);
																			random();
																			if (((random() < (0.05 + (skill * 0.05))) && (enemy_range == RANGE_NEAR)))
																			{
																				self.has_fired = 1;
																			}
																		}
																		else
																		{
																			if ((self.classname == "monster_scourge"))
																			{
																				sound7(self, CHAN_VOICE, "scourge/sight.wav", 1, ATTN_NORM, SNDSPD);
																			}
																			else
																			{
																				if ((self.classname == "monster_shalrath"))
																				{
																					sound7(self, CHAN_VOICE, "shalrath/sight.wav", 1, ATTN_NORM, SNDSPD);
																				}
																				else
																				{
																					if ((self.classname == "monster_shalrath_boss"))
																					{
																						sound7(self, CHAN_VOICE, "shalrath/bosssight.wav", 1, ATTN_NORM, SNDSPD);
																					}
																					else
																					{
																						if (((self.classname == "monster_spider") && !self.spider_jumped_ceiling_at_map_start))
																						{
																							sound7(self, CHAN_VOICE, "spider/spider_sight.wav", 1, ATTN_NORM, SNDSPD);
																						}
																						else
																						{
																							if (((self.classname == "monster_afrit") && !self.in_cocoon_shape))
																							{
																								sound7(self, CHAN_AUTO, "afrit/sight.wav", 1, ATTN_NORM, SNDSPD);
																							}
																							else
																							{
																								if ((self.classname == "monster_torment"))
																								{
																									sound7(self, CHAN_VOICE, "torment/alert.wav", 1, ATTN_NORM, SNDSPD);
																								}
																								else
																								{
																									if ((self.classname == "monster_carnivean"))
																									{
																										sound7(self, CHAN_VOICE, "carnivean/scream.wav", 1, ATTN_NORM, SNDSPD);
																									}
																									else
																									{
																										if ((self.classname == "monster_yakman"))
																										{
																											if ((random() < 0.5))
																											{
																												sound7(self, CHAN_VOICE, "yakman/big1.wav", 1, ATTN_NORM, SNDSPD);
																											}
																											else
																											{
																												sound7(self, CHAN_VOICE, "yakman/big3.wav", 1, ATTN_NORM, SNDSPD);
																											}
																										}
																										else
																										{
																											if ((self.classname == "monster_reiver"))
																											{
																												sound7(self, CHAN_VOICE, "reiver/sight.wav", 1, ATTN_NORM, SNDSPD);
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
};

void() FoundTarget =
{
	if (((self.classname == "monster_voreling") && (self.enemy.classname == "monster_shalrath")))
	{
		return;
	}
	if ((self.enemy.classname == "player"))
	{
		sight_entity = self;
		sight_entity_time = time;
	}
	self.show_hostile = (time + 1);
	SightSound();
	HuntTarget();
};

float() FindTarget =
{
	local entity client;
	local float r;

	if (((sight_entity_time >= (time - 0.1)) && !(self.spawnflags & 3)))
	{
		client = sight_entity;
		if ((client.enemy == self.enemy))
		{
			return;
		}
	}
	else
	{
		client = checkclient();
		if (!client)
		{
			return (0);
		}
	}
	if ((client == self.enemy))
	{
		return (0);
	}
	if ((client.flags & FL_NOTARGET))
	{
		return (0);
	}
	if ((client.items & IT_INVISIBILITY))
	{
		return (0);
	}
	r = range(client);
	if ((r == RANGE_FAR))
	{
		return (0);
	}
	if (!visible(client))
	{
		return (0);
	}
	if ((r == RANGE_NEAR))
	{
		if (((client.show_hostile < time) && !infront(client)))
		{
			return (0);
		}
	}
	else
	{
		if ((r == RANGE_MID))
		{
			if (!infront(client))
			{
				return (0);
			}
		}
	}
	self.enemy = client;
	if ((self.enemy.classname != "player"))
	{
		self.enemy = self.enemy.enemy;
		if ((self.enemy.classname != "player"))
		{
			self.enemy = world;
			return (0);
		}
	}
	FoundTarget();
	return (TRUE);
};

void(float dist) ai_forward =
{
	walkmove(self.angles_y, dist);
};

void(float dist) ai_back =
{
	walkmove((self.angles_y + 180), dist);
};

void(float dist) ai_pain =
{
	ai_back(dist);
	if ((self.hitbox_pos == HEAD_SHOT))
	{
		self.hitbox_pos = 0;
	}
};

void(float dist) ai_painforward =
{
	if ((self.hitbox_pos == HEAD_SHOT))
	{
		self.hitbox_pos = 0;
	}
	walkmove(self.ideal_yaw, dist);
};

void(float dist) ai_walk =
{
	movedist = dist;
	if ((self.classname == "monster_dragon"))
	{
		movetogoal(dist);
		return;
	}
	if (FindTarget())
	{
		return;
	}
	movetogoal(dist);
};

void() ai_stand =
{
	if (FindTarget())
	{
		return;
	}
	if ((time > self.pausetime))
	{
		self.th_walk();
		return;
	}
};

void() ai_turn =
{
	if (FindTarget())
	{
		return;
	}
	ChangeYaw();
};

void(vector dest3) ChooseTurn =
{
	local vector dir;
	local vector newdir;

	dir = self.origin - dest3;
	newdir_x = 0;
	if (((dir * newdir) > 0))
	{
		dir_x = 0 - 0;
	}
	else
	{
		dir_x = 0;
	}
	self.ideal_yaw = vectoyaw(dir);
};

float() FacingIdeal =
{
	local float delta;

	delta = anglemod((self.angles_y - self.ideal_yaw));
	if (((delta > 25) && (delta < 335)))
	{
		return (0);
	}
	return (TRUE);
};

float() CheckAnyAttack =
{
	if (!enemy_vis)
	{
		return;
	}
	if ((self.classname == "monster_army"))
	{
		return (SoldierCheckAttack());
	}
	if ((self.classname == "monster_ogre"))
	{
		return (OgreCheckAttack());
	}
	if ((self.classname == "monster_shambler"))
	{
		return (ShamCheckAttack());
	}
	if ((self.classname == "monster_demon1"))
	{
		return (DemonCheckAttack());
	}
	if ((self.classname == "monster_dog"))
	{
		return (DogCheckAttack());
	}
	if ((self.classname == "monster_wizard"))
	{
		return (WizardCheckAttack());
	}
	if ((self.classname == "monster_spider"))
	{
		return (SpiderCheckAttack());
	}
	if ((self.classname == "monster_afrit"))
	{
		return (AfritCheckAttack());
	}
	return (CheckAttack());
};

void() ai_run_melee =
{
	self.ideal_yaw = enemy_yaw;
	ChangeYaw();
	if (FacingIdeal())
	{
		self.th_melee();
		self.attack_state = AS_STRAIGHT;
	}
};

void() ai_run_missile =
{
	self.ideal_yaw = enemy_yaw;
	ChangeYaw();
	if (FacingIdeal())
	{
		self.th_missile();
		self.attack_state = AS_STRAIGHT;
	}
};

void() ai_run_slide =
{
	local float ofs;

	self.ideal_yaw = enemy_yaw;
	ChangeYaw();
	if (self.lefty)
	{
		ofs = 90;
	}
	else
	{
		ofs = -90;
	}
	if (walkmove((self.ideal_yaw + ofs), movedist))
	{
		return;
	}
	self.lefty = (1 - self.lefty);
	walkmove((self.ideal_yaw - ofs), movedist);
};

void(float dist) ai_run =
{
	local vector check;
	local vector dir;
	local vector vtemp;

	check = (self.origin - '0 0 20') + '0 0 1';
	if ((the_matrix == 1))
	{
		SNDSPD = 60;
	}
	if ((self.hitbox_pos == HEAD_SHOT))
	{
		self.hitbox_pos = 0;
	}
	if ((self.classname == "monster_reiver"))
	{
		if ((self.attack_chance > 0))
		{
			self.attack_chance = (self.attack_chance + 0.1);
			if (((pointcontents(self.origin) == CONTENT_SOLID) && (self.bodyphased == 0)))
			{
				self.bodyphased = 1;
				sound(self, CHAN_BODY, "reiver/ghost_flying.wav", 0.8, ATTN_NORM, (SNDSPD + 10));
			}
			if ((self.bodyphased > 0))
			{
				self.traileffectnum = particleeffectnum(/*19532i*/"teleporter_particles");
				self.colormod = '0.1 0.1 0.1';
				self.alpha = 0.6;
				self.glow_color = 1;
				self.glow_size = 104;
				self.attack_finished = (time + 0.6);
				if ((self.attack_chance > 5))
				{
					vtemp = self.enemy.origin + '0 0 10';
					dir = normalize((vtemp - self.origin));
					self.velocity = (dir * 150);
					return;
				}
			}
		}
	}
	if ((autocvar_monsterlavaslime == 1))
	{
		if ((pointcontents(check) == CONTENT_LAVA))
		{
			self.traileffectnum = particleeffectnum(/*19553i*/"monsterburn");
			self.colormod = '0.4 0.1 0.1';
			self.nodeathanim = 1;
		}
		if ((pointcontents(check) == CONTENT_SLIME))
		{
			self.traileffectnum = particleeffectnum(/*19565i*/"monsteracid");
			self.colormod = '0.3 1.6 0.3';
			self.nodeathanim = 1;
		}
		if ((self.monstdamag > 0))
		{
			if (((pointcontents(check) != CONTENT_SLIME) && (pointcontents(check) != CONTENT_LAVA)))
			{
				self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
			}
		}
	}
	else
	{
		if ((autocvar_monsterlavaslime == 2))
		{
			if ((pointcontents(check) == CONTENT_LAVA))
			{
				self.traileffectnum = particleeffectnum(/*19553i*/"monsterburn");
				self.colormod = '0.4 0.1 0.1';
				self.nodeathanim = 1;
				self.monstdamag = 0.1;
				if ((self.classname != "monster_zombie"))
				{
					if ((self.monstdamag < time))
					{
						T_Damage(self, world, world, 14);
						if ((self.health <= 0))
						{
							self.th_die();
							return;
						}
						self.monstdamag = (time + 0.5);
					}
				}
			}
			if ((pointcontents(check) == CONTENT_SLIME))
			{
				self.traileffectnum = particleeffectnum(/*19565i*/"monsteracid");
				self.colormod = '0.9 1.4 0.4';
				self.nodeathanim = 1;
				self.monstdamag = 0.1;
				if ((self.classname != "monster_zombie"))
				{
					if ((self.monstdamag < time))
					{
						T_Damage(self, world, world, 7);
						if ((self.health <= 0))
						{
							self.th_die();
							return;
						}
						self.monstdamag = (time + 1);
					}
				}
			}
			if ((self.monstdamag > 0))
			{
				if (((pointcontents(check) != CONTENT_SLIME) && (pointcontents(check) != CONTENT_LAVA)))
				{
					self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
				}
			}
		}
	}
	if ((self.classname == "monster_zombie"))
	{
		if ((((autocvar_zombieflies == 1) && (pointcontents(check) != CONTENT_SLIME)) && (pointcontents(check) != CONTENT_LAVA)))
		{
			self.traileffectnum = particleeffectnum(/*19589i*/"zombiefliesblack");
		}
		else
		{
			if ((((autocvar_zombieflies == 2) && (pointcontents(check) != CONTENT_SLIME)) && (pointcontents(check) != CONTENT_LAVA)))
			{
				self.traileffectnum = particleeffectnum(/*19606i*/"zombiefliesbrown");
			}
		}
	}
	movedist = dist;
	if ((self.enemy.health <= 0))
	{
		self.enemy = world;
		if ((self.oldenemy.health > 0))
		{
			self.enemy = self.oldenemy;
			HuntTarget();
		}
		else
		{
			if (self.movetarget)
			{
				self.th_walk();
			}
			else
			{
				self.th_stand();
			}
			return;
		}
	}
	self.show_hostile = (time + 1);
	enemy_vis = visible(self.enemy);
	if (enemy_vis)
	{
		self.search_time = (time + 5);
	}
	if ((coop && (self.search_time < time)))
	{
		if (FindTarget())
		{
			return;
		}
	}
	enemy_infront = infront(self.enemy);
	enemy_range = range(self.enemy);
	enemy_yaw = vectoyaw((self.enemy.origin - self.origin));
	if ((((self.classname == "monster_army") || (self.classname == "monster_enforcer")) || (self.classname == "monster_reiver")))
	{
		if ((((self.has_fired > 0) && (self.has_fired < 6)) || (self.has_fired > 100)))
		{
			if ((self.has_fired > 100))
			{
				if ((self.has_fired > 101))
				{
					movetogoal(dist);
					return;
				}
				else
				{
					ai_run_slide();
					return;
				}
			}
			ai_run_slide();
			if (((self.has_fired < 90) && (self.has_fired >= 1)))
			{
				if ((random() < 0.8))
				{
					self.has_fired = (self.has_fired + 1);
				}
				if ((((self.classname == "monster_reiver") && (random() < 0.25)) && (self.has_fired > 1)))
				{
					self.has_fired = (self.has_fired + -1);
				}
			}
			return;
		}
		else
		{
			if ((((self.classname == "monster_reiver") && (self.has_fired == -1)) && (self.attack_chance == 0)))
			{
				ai_back(40);
				return;
			}
		}
		self.has_fired = 0;
	}
	if ((self.attack_state == AS_MISSILE))
	{
		ai_run_missile();
		return;
	}
	if ((self.attack_state == AS_MELEE))
	{
		ai_run_melee();
		return;
	}
	if (CheckAnyAttack())
	{
		return;
	}
	if ((self.attack_state == AS_SLIDING))
	{
		ai_run_slide();
		return;
	}
	movetogoal(dist);
};

void() ai_turn_in_place =
{
	local float delta;

	self.nextthink = (time + 0.1);
	enemy_yaw = vectoyaw((self.enemy.origin - self.origin));
	delta = fabs((self.angles_y - enemy_yaw));
	if ((delta > MIN_ANGLE_DELTA))
	{
		self.ideal_yaw = enemy_yaw;
		ChangeYaw();
	}
	else
	{
		self.think = self.th_run;
	}
};

void(float dist) ai_run_inflamed =
{
	self.colormod = '0.35 0.26 0.26';
	movedist = dist;
	self.enemy = world;
	self.show_hostile = (time + 1);
	movetogoal(dist);
};
