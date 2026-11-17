//Decompiled code. Please respect the original copyright.

void() trigger_reactivate =
{
	self.solid = SOLID_TRIGGER;
};

void() multi_wait =
{
	if (self.max_health)
	{
		self.health = self.max_health;
		self.takedamage = DAMAGE_YES;
		self.solid = SOLID_BBOX;
	}
};

void() multi_trigger =
{
	if ((self.nextthink > time))
	{
		return;
	}
	if ((self.classname == "trigger_secret"))
	{
		if ((self.enemy.classname != "player"))
		{
			return;
		}
		found_secrets = found_secrets + 1;
		WriteByte(MSG_ALL, SVC_FOUNDSECRET);
		if (((!coop && !deathmatch) && autocvar_auto_save))
		{
			stuffcmd(other, "Echo Checkpoint...\n");
			stuffcmd(other, "save autosaves/autosave\n");
		}
	}
	if (self.noise)
	{
		sound(self, CHAN_VOICE, self.noise, 1, ATTN_NORM);
	}
	self.takedamage = 0;
	activator = self.enemy;
	SUB_UseTargets();
	if ((self.wait > 0))
	{
		self.think = multi_wait;
		self.nextthink = (time + self.wait);
	}
	else
	{
		self.touch = SUB_Null;
		self.nextthink = (time + 0.1);
		self.think = SUB_Remove;
	}
};

void() multi_killed =
{
	self.enemy = damage_attacker;
	multi_trigger();
};

void() multi_use =
{
	self.enemy = activator;
	multi_trigger();
};

void() multi_touch =
{
	if ((other.classname != "player"))
	{
		return;
	}
	if ((self.movedir != VEC_ORIGIN))
	{
		makevectors(other.angles);
		if (((v_forward * self.movedir) < 0))
		{
			return;
		}
	}
	self.enemy = other;
	multi_trigger();
};

void() trigger_multiple =
{
	if ((self.sounds == 1))
	{
		precache_sound("misc/secret.wav");
		self.noise = "misc/secret.wav";
	}
	else
	{
		if ((self.sounds == 2))
		{
			precache_sound("misc/talk.wav");
			self.noise = "misc/talk.wav";
		}
		else
		{
			if ((self.sounds == 3))
			{
				precache_sound("misc/trigger1.wav");
				self.noise = "misc/trigger1.wav";
			}
		}
	}
	if (!self.wait)
	{
		self.wait = 0.2;
	}
	self.use = multi_use;
	InitTrigger();
	if (self.health)
	{
		if ((self.spawnflags & SPAWNFLAG_NOTOUCH))
		{
			objerror("health and notouch don't make sense\n");
		}
		self.max_health = self.health;
		self.th_die = multi_killed;
		self.takedamage = DAMAGE_YES;
		self.solid = SOLID_BBOX;
		setorigin(self, self.origin);
	}
	else
	{
		if (!(self.spawnflags & SPAWNFLAG_NOTOUCH))
		{
			self.touch = multi_touch;
		}
	}
};

void() trigger_once =
{
	self.wait = -1;
	trigger_multiple();
};

void() trigger_relay =
{
	self.use = SUB_UseTargets;
};

void() trigger_secret =
{
	total_secrets = total_secrets + 1;
	self.wait = -1;
	if (!self.message)
	{
		self.message = "You found a secret area!";
	}
	if (!self.sounds)
	{
		self.sounds = 1;
	}
	if ((self.sounds == 1))
	{
		precache_sound("misc/secret.wav");
		self.noise = "misc/secret.wav";
	}
	else
	{
		if ((self.sounds == 2))
		{
			precache_sound("misc/talk.wav");
			self.noise = "misc/talk.wav";
		}
	}
	trigger_multiple();
};

void() counter_use =
{
	self.count = (self.count - 1);
	if ((self.count < 0))
	{
		return;
	}
	if ((self.count != 0))
	{
		if (((activator.classname == "player") && ((self.spawnflags & SPAWNFLAG_NOMESSAGE) == 0)))
		{
			if ((self.count >= 4))
			{
				centerprint(activator, "There are more to go...");
			}
			else
			{
				if ((self.count == 3))
				{
					centerprint(activator, "Only 3 more to go...");
				}
				else
				{
					if ((self.count == 2))
					{
						centerprint(activator, "Only 2 more to go...");
					}
					else
					{
						centerprint(activator, "Only 1 more to go...");
					}
				}
			}
		}
		return;
	}
	if (((activator.classname == "player") && ((self.spawnflags & SPAWNFLAG_NOMESSAGE) == 0)))
	{
		centerprint(activator, "Sequence completed!");
	}
	self.enemy = activator;
	multi_trigger();
};

void() trigger_counter =
{
	self.wait = -1;
	if (!self.count)
	{
		self.count = 2;
	}
	self.use = counter_use;
};

void() play_teleport =
{
	local float v;
	local string tmpstr;

	v = random() * 5;
	if ((v < 1))
	{
		tmpstr = "misc/r_tele1.wav";
	}
	else
	{
		if ((v < 2))
		{
			tmpstr = "misc/r_tele2.wav";
		}
		else
		{
			if ((v < 3))
			{
				tmpstr = "misc/r_tele3.wav";
			}
			else
			{
				if ((v < 4))
				{
					tmpstr = "misc/r_tele4.wav";
				}
				else
				{
					tmpstr = "misc/r_tele5.wav";
				}
			}
		}
	}
	sound7(self, CHAN_VOICE, tmpstr, 0.72, ATTN_NORM, SNDSPD * (0.96 + random() * 0.08));
	remove(self);
};

void(vector org) spawn_tfog =
{
	s = spawn();
	s.origin = org;
	s.nextthink = (time + 0.2);
	s.think = play_teleport;
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_TELEPORT);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, org_y);
	WriteCoord(MSG_BROADCAST, org_z);
};

void() tdeath_touch =
{
	if ((other == self.owner))
	{
		return;
	}
	if ((other.classname == "player"))
	{
		if ((other.invincible_finished > time))
		{
			self.classname = "teledeath2";
		}
		if ((self.owner.classname != "player"))
		{
			T_Damage(self.owner, self, self, 50000);
			return;
		}
	}
	if (other.health)
	{
		if (((other.classname == "player") && (teamplay && coop)))
		{
			return;
		}
		else
		{
			T_Damage(other, self, self, 50000);
		}
	}
};

void(vector org, entity death_owner) spawn_tdeath =
{
	local entity death;

	death = spawn();
	death.classname = "teledeath";
	death.movetype = 0;
	death.solid = SOLID_TRIGGER;
	death.angles = VEC_ORIGIN;
	setsize(death, (death_owner.mins - '1 1 1'), (death_owner.maxs + '1 1 1'));
	setorigin(death, org);
	death.touch = tdeath_touch;
	death.nextthink = (time + 0.2);
	death.think = SUB_Remove;
	death.owner = death_owner;
	force_retouch = 2;
};

void() teleport_touch =
{
	local entity t;
	local vector org;

	if (self.targetname)
	{
		if ((self.nextthink < time))
		{
			return;
		}
	}
	if ((other.classname == "robdob"))
	{
		FD_Portal (other, self);	// a Rob Dob head flies through portals too (floathead.qc)
		return;
	}
	if ((self.spawnflags & PLAYER_ONLY))
	{
		if (((other.classname != "player") && (other.classname != "player_teleporter_entity")))
		{
			return;
		}
	}
	if (((other.health <= 0) || (other.solid != SOLID_SLIDEBOX)))
	{
		return;
	}
	SUB_UseTargets();
	spawn_tfog(other.origin);
	t = find(world, targetname, self.target);
	if (!t)
	{
		objerror("couldn't find target");
	}
	makevectors(t.mangle);
	org = t.origin + (32 * v_forward);
	spawn_tfog(org);
	spawn_tdeath(t.origin, other);
	if (!other.health)
	{
		other.origin = t.origin;
		other.velocity = ((v_forward * other.velocity_x) + (v_forward * other.velocity_y));
		return;
	}
	setorigin(other, t.origin);
	other.angles = t.mangle;
	if ((other.classname == "player"))
	{
		other.fixangle = 1;
		other.teleport_time = (time + 0.7);
		if ((other.flags & FL_ONGROUND))
		{
			other.flags = (other.flags - FL_ONGROUND);
		}
		other.velocity = (v_forward * 300);
	}
	other.flags = (other.flags - (other.flags & FL_ONGROUND));
	if ((((other.classname == "player") && autocvar_teleport_zoom_view) && (world.model != "maps/end.bsp")))
	{
		view_zoom_out = 1;
		other.viewzoom = 0.01;
	}
};

void() teleport_touch_proj =
{
	local entity t;
	local vector org;

	if ((other.teleport_time > time))
	{
		return;
	}
	if ((other.classname == "robdob"))
	{
		FD_Portal (other, self);	// a Rob Dob head flies through portals too (floathead.qc)
		return;
	}
	if ((((((((((((((other.classname != "missile") && (other.classname != "grenade")) && (other.classname != "proximity_grenade")) && (other.classname != "player")) && (other.classname != "spike")) && (other.classname != "gib")) && (other.classname != "weapon_supershotgun")) && (other.classname != "weapon_grenadelauncher")) && (other.classname != "weapon_supernailgun")) && (other.classname != "weapon_nailgun")) && (other.classname != "weapon_lightning")) && (other.classname != "weapon_rocketlauncher")) && (other.classname != "")))
	{
		return;
	}
	if (self.targetname)
	{
		if ((self.nextthink < time))
		{
			return;
		}
	}
	if ((((other.classname == "player") && (other.solid != SOLID_SLIDEBOX)) || ((other.health <= 0) && (other.solid == SOLID_NOT))))
	{
		return;
	}
	if ((other.classname == "trigger_teleport"))
	{
		return;
	}
	SUB_UseTargets();
	if ((other.classname == "player"))
	{
		spawn_tfog(other.origin);
	}
	t = find(world, targetname, self.target);
	if (!t)
	{
		objerror("couldn't find target");
	}
	makevectors(t.mangle);
	org = t.origin + (32 * v_forward);
	if ((other.classname == "player"))
	{
		spawn_tfog(org);
		spawn_tdeath(t.origin, other);
	}
	if ((!other.health && (other.classname != "player")))
	{
		setorigin(other, org);
		other.velocity = (v_forward * vlen(other.velocity));
		other.angles = vectoangles(other.velocity);
		other.teleport_time = (time + 0.3);
		other.flags = (other.flags - (other.flags & FL_ONGROUND));
		return;
	}
	setorigin(other, t.origin);
	other.angles = t.mangle;
	if ((other.classname == "player"))
	{
		other.fixangle = 1;
		other.teleport_time = (time + 0.7);
		if ((other.flags & FL_ONGROUND))
		{
			other.flags = (other.flags - FL_ONGROUND);
		}
		other.velocity = (v_forward * 300);
	}
	other.flags = (other.flags - (other.flags & FL_ONGROUND));
};

void() info_teleport_destination =
{
	self.mangle = self.angles;
	self.angles = VEC_ORIGIN;
	self.model = "";
	self.origin = (self.origin + '0 0 27');
	if (!self.targetname)
	{
		objerror("no targetname");
	}
};

void() teleport_use =
{
	self.nextthink = (time + 0.2);
	force_retouch = 2;
	self.think = SUB_Null;
};

void() spawn_teleporter_particles =
{
	if ((world.model != "maps/e1m2.bsp"))
	{
		pointparticles(particleeffectnum(/*19532i*/"teleporter_particles"), self.origin, VEC_ORIGIN, 1);
	}
	self.nextthink = (time + 0.000650);
	self.think = spawn_teleporter_particles;
};

void() trigger_teleport =
{
	local vector o;
	local entity enFind;
	local entity particle_spawner;

	InitTrigger();
	if (((((autocvar_teleport_everything == 1) || deathmatch) && (autocvar_teleport_everything_dm == 1)) || (self.spawnflags & PROJECTILE)))
	{
		self.flags = (self.flags | FL_ITEM);
		self.touch = teleport_touch_proj;
	}
	else
	{
		self.touch = teleport_touch;
	}
	if (!self.target)
	{
		objerror("no target");
	}
	self.use = teleport_use;
	if (!(self.spawnflags & SILENT))
	{
		precache_sound("ambience/hum1.wav");
		o = (self.mins + self.maxs) * 0.5;
		ambientsound(o, "ambience/hum1.wav", 0.5, ATTN_STATIC);
		if (((autocvar_teleporter_particles == 1) || (autocvar_teleporter_particles == 2)))
		{
			if ((self.partname == "none"))
			{
				return;
			}
			enFind = findradius(o, 200);
			while (enFind)
			{
				if ((enFind.classname == "trigger_changelevel"))
				{
					return;
				}
				enFind = enFind.chain;
			}
			particle_spawner = spawn();
			if (((world.model == "maps/e1m3.bsp") && (self.mins == '1764 96 -132')))
			{
				particle_spawner.origin = '1796 128 -100';
			}
			else
			{
				if (((world.model == "maps/e2m3.bsp") && (self.mins == '1112 1768 -96')))
				{
					return;
				}
				else
				{
					if (((world.model == "maps/e2m7.bsp") && (self.mins == '1128 -1188 16')))
					{
						return;
					}
					else
					{
						if (((world.model == "maps/e3m2.bsp") && (self.mins == '224 -504 -256')))
						{
							return;
						}
						else
						{
							if (((world.model == "maps/e3m7.bsp") && (self.mins == '-1144 -312 -440')))
							{
								return;
							}
							else
							{
								if (((world.model == "maps/e3m7.bsp") && (self.mins == '-352 160 -184')))
								{
									return;
								}
								else
								{
									if (((world.model == "maps/e4m2.bsp") && (self.mins == '-568 408 368')))
									{
										particle_spawner.origin = '-544 425 405';
									}
									else
									{
										if (((world.model == "maps/e4m2.bsp") && (self.mins == '-1536 -304 144')))
										{
											particle_spawner.origin = '-1504 -295 200';
										}
										else
										{
											if (((world.model == "maps/e4m2.bsp") && (((self.mins == '-1128 -2112 384') || (self.mins == '-1128 -2248 384')) || (self.mins == '-1176 -2200 384'))))
											{
												return;
											}
											else
											{
												if (((world.model == "maps/e4m3.bsp") && (self.mins == '2776 784 -88')))
												{
													particle_spawner.origin = '2792 804 -70';
												}
												else
												{
													if (((world.model == "maps/e4m4.bsp") && (self.mins == '-1984 768 176')))
													{
														particle_spawner.origin = '-1964 788 155';
													}
													else
													{
														if (((world.model == "maps/e4m5.bsp") && (self.mins == '-2656 -2576 -256')))
														{
															particle_spawner.origin = '-2658 -2560 -228';
														}
														else
														{
															if (((world.model == "maps/e4m7.bsp") && (self.mins == '1000 -1888 40')))
															{
																particle_spawner.origin = '990 -1856 75';
															}
															else
															{
																if (((world.model == "maps/e4m7.bsp") && (self.mins == '-672 96 -288')))
																{
																	particle_spawner.origin = '-648 80 -256';
																}
																else
																{
																	if (((world.model == "maps/e4m7.bsp") && (self.mins == '-888 344 -288')))
																	{
																		particle_spawner.origin = '-864 365 -256';
																	}
																	else
																	{
																		if (((world.model == "maps/e4m7.bsp") && (self.mins == '-1016 -2480 -240')))
																		{
																			particle_spawner.origin = '-992 -2486 -200';
																		}
																		else
																		{
																			if (((world.model == "maps/e4m8.bsp") && (self.mins == '1936 -1072 104')))
																			{
																				particle_spawner.origin = '1952 -1064 140';
																			}
																			else
																			{
																				if (((world.model == "maps/e4m8.bsp") && (self.mins == '1456 -2352 24')))
																				{
																					particle_spawner.origin = '1472 -2344 60';
																				}
																				else
																				{
																					if (((world.model == "maps/e4m8.bsp") && (self.mins == '-456 808 32')))
																					{
																						return;
																					}
																					else
																					{
																						if (((world.model == "maps/end.bsp") && (self.mins == '-672 536 0')))
																						{
																							return;
																						}
																						else
																						{
																							if (((world.model == "maps/end.bsp") && (self.mins == '-1632 1248 0')))
																							{
																								return;
																							}
																							else
																							{
																								particle_spawner.origin = o;
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
			particle_spawner.velocity = VEC_ORIGIN;
			particle_spawner.movetype = 0;
			particle_spawner.solid = 0;
			setsize(particle_spawner, VEC_ORIGIN, VEC_ORIGIN);
			particle_spawner.touch = SUB_Null;
			particle_spawner.owner = self;
			particle_spawner.think = spawn_teleporter_particles;
			particle_spawner.nextthink = (time + 0.1);
		}
	}
};

void() trigger_skill_touch =
{
	if ((other.classname != "player"))
	{
		return;
	}
	cvar_set("skill", self.message);
};

void() trigger_setskill =
{
	InitTrigger();
	self.touch = trigger_skill_touch;
};

void() trigger_onlyregistered_touch =
{
	if ((other.classname != "player"))
	{
		return;
	}
	if ((self.attack_finished > time))
	{
		return;
	}
	self.attack_finished = (time + 2);
	if (cvar("registered"))
	{
		self.message = "";
		SUB_UseTargets();
		remove(self);
	}
	else
	{
		if ((self.message != ""))
		{
			centerprint(other, self.message);
			sound(other, CHAN_BODY, "misc/talk.wav", 1, ATTN_NORM);
		}
	}
};

void() trigger_onlyregistered =
{
	precache_sound("misc/talk.wav");
	InitTrigger();
	self.touch = trigger_onlyregistered_touch;
};

void() hurt_on =
{
	self.solid = SOLID_TRIGGER;
	self.nextthink = -1;
};

void() hurt_touch =
{
	if (other.takedamage)
	{
		if (self.noise)
		{
			sound7(other, CHAN_AUTO, self.noise, self.volume, ATTN_NORM, SNDSPD);
		}
		self.solid = 0;
		T_Damage(other, self, self, self.dmg);
		self.think = hurt_on;
		if (self.speed)
		{
			self.nextthink = (time + self.speed);
		}
		else
		{
			self.nextthink = (time + 1);
		}
	}
	return;
};

void() trigger_hurt =
{
	InitTrigger();
	if (self.noise)
	{
		precache_sound(self.noise);
	}
	if (!self.volume)
	{
		self.volume = 1;
	}
	self.touch = hurt_touch;
	if (!self.dmg)
	{
		self.dmg = 5;
	}
};

void() trigger_push_touch =
{
	if (other.movetype == MOVETYPE_PUSH)
		return;
	if (((other.classname == "grenade") || ((self.spawnflags & PUSH_ALL) && (other.classname != "missile"))))
	{
		if ((self.spawnflags & ADD_VEL))
		{
			if ((other.flags & FL_CLIENT))
			{
				other.velocity = (other.velocity + ((self.speed * self.movedir) * 1));
			}
			else
			{
				other.velocity = (other.velocity + ((self.speed * self.movedir) * 5));
			}
		}
		else
		{
			other.velocity = ((self.speed * self.movedir) * 10);
		}
	}
	else
	{
		if ((other.health > 0))
		{
			other.velocity = ((self.speed * self.movedir) * 10);
			if ((other.classname == "player"))
			{
				if ((other.fly_sound < time))
				{
					other.fly_sound = (time + 1.5);
					if (!(self.spawnflags & NO_SOUND))
					{
						sound7(other, CHAN_AUTO, "ambience/windfly.wav", 0.68, ATTN_NORM, SNDSPD * (0.95 + random() * 0.12));
					}
				}
			}
		}
	}
	if ((self.spawnflags & PUSH_ONCE))
	{
		remove(self);
	}
};

void() trigger_push =
{
	InitTrigger();
	precache_sound("ambience/windfly.wav");
	self.touch = trigger_push_touch;
	if (!self.speed)
	{
		self.speed = 1000;
	}
};

void() trigger_monsterjump_touch =
{
	if (((other.flags & 35) != FL_MONSTER))
	{
		return;
	}
	other.velocity_x = (self.movedir_x * self.speed);
	other.velocity_y = (self.movedir_y * self.speed);
	if (!(other.flags & FL_ONGROUND))
	{
		return;
	}
	other.flags = (other.flags - FL_ONGROUND);
	other.velocity_z = self.height;
};

void() trigger_monsterjump =
{
	if (!self.speed)
	{
		self.speed = 200;
	}
	if (!self.height)
	{
		self.height = 200;
	}
	if ((self.angles == VEC_ORIGIN))
	{
		self.angles = '0 360 0';
	}
	InitTrigger();
	self.touch = trigger_monsterjump_touch;
};

void() music_use =
{
	WriteByte(MSG_ALL, SVC_CDTRACK);
	WriteByte(MSG_ALL, self.track_start);
	WriteByte(MSG_ALL, self.track_end);
	self.touch = SUB_Null;
	self.nextthink = (time + 0.1);
	self.think = SUB_Remove;
};

void() trigger_music =
{
	if (!self.track_start)
	{
		self.track_start = 1;
	}
	if (!self.track_end)
	{
		self.track_end = 2;
	}
	if ((self.sounds == 1))
	{
		precache_sound("misc/secret.wav");
		self.noise = "misc/secret.wav";
	}
	else
	{
		if ((self.sounds == 2))
		{
			precache_sound("misc/talk.wav");
			self.noise = "misc/talk.wav";
		}
		else
		{
			if ((self.sounds == 3))
			{
				precache_sound("misc/trigger1.wav");
				self.noise = "misc/trigger1.wav";
			}
		}
	}
	if (!self.wait)
	{
		self.wait = 0.2;
	}
	self.use = music_use;
	InitTrigger();
	if (self.health)
	{
		if ((self.spawnflags & SPAWNFLAG_NOTOUCH))
		{
			objerror("health and notouch don't make sense\n");
		}
		self.max_health = self.health;
		self.th_die = multi_killed;
		self.takedamage = DAMAGE_YES;
		self.solid = SOLID_BBOX;
		setorigin(self, self.origin);
	}
	else
	{
		if (!(self.spawnflags & SPAWNFLAG_NOTOUCH))
		{
			self.touch = multi_touch;
		}
	}
};
