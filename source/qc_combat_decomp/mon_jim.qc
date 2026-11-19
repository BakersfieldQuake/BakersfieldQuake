//Decompiled code. Please respect the original copyright.

void(float fstate) jim_update =
{
	if ((self.health < 1))
	{
		return;
	}
	if ((self.t_width < time))
	{
		self.t_width = (time + 0.9);
		sound(self, CHAN_AUTO, "jim/gunidle2.wav", 0.3, ATTN_NORM);
	}
	if ((self.idletimer < time))
	{
		monster_idle_sound();
	}
	if ((self.t_length < time))
	{
		self.t_length = (time + 0.2);
		self.exactskin = (self.exactskin + 1);
		if ((self.exactskin > 2))
		{
			self.exactskin = 0;
		}
		self.skin = self.exactskin;
	}
	if (self.enemy)
	{
		self.idlebusy = 0;
		if ((fstate == JS_IDLE))
		{
			if ((self.origin_z > self.oldorigin_z))
			{
				fstate = JS_UP;
			}
			else
			{
				if ((self.origin_z < self.oldorigin_z))
				{
					fstate = JS_DOWN;
				}
			}
		}
	}
	else
	{
		if (((self.count == 0) && self.idlereverse))
		{
			if (((self.idlebusy == JS_TURNLEFT) || (self.idlebusy == JS_TURNRIGHT)))
			{
				self.idlebusy = 0;
				self.idlereverse = 0;
				self.waitmin = ((time + 2) + (random() * 4));
			}
		}
		else
		{
			if (((self.count == 5) && !self.idlereverse))
			{
				if (((self.idlebusy == JS_IDLE) && (self.waitmin < time)))
				{
					if (((self.velocity_x == 0) && (self.velocity_y == 0)))
					{
						if ((self.idletimer < time))
						{
							monster_idle_sound();
						}
						self.lip = random();
						if ((self.lip < 0.3))
						{
							self.idlebusy = JS_TURNLEFT;
						}
						else
						{
							if ((self.lip < 0.6))
							{
								self.idlebusy = JS_TURNRIGHT;
							}
							else
							{
								if ((self.lip < 0.8))
								{
									self.idlebusy = JS_IDLE2;
								}
								else
								{
									self.idlebusy = JS_IDLE3;
								}
							}
						}
					}
				}
				else
				{
					if (((self.idlebusy == JS_IDLE2) || (self.idlebusy == JS_IDLE3)))
					{
						self.idlebusy = 0;
						self.waitmin = ((time + 2) + (random() * 4));
					}
					else
					{
						if ((self.idlebusy == JS_TURNLEFT))
						{
							self.idlebusy = JS_IDLELEFT;
							self.waitmin = ((time + 2) + (random() * 4));
						}
						else
						{
							if ((self.idlebusy == JS_TURNRIGHT))
							{
								self.idlebusy = JS_IDLERIGHT;
								self.waitmin = ((time + 2) + (random() * 4));
							}
							else
							{
								if ((self.idlebusy == JS_IDLELEFT))
								{
									if (((self.waitmin < time) && (random() < 0.5)))
									{
										self.idlebusy = JS_TURNLEFT;
										self.idlereverse = TRUE;
									}
								}
								else
								{
									if ((self.idlebusy == JS_IDLERIGHT))
									{
										if (((self.waitmin < time) && (random() < 0.5)))
										{
											self.idlebusy = JS_TURNRIGHT;
											self.idlereverse = TRUE;
										}
									}
								}
							}
						}
					}
				}
			}
		}
		if (((self.velocity_x == 0) && (self.velocity_y == 0)))
		{
			if ((self.attack_timer < time))
			{
				self.attack_timer = (time + 1);
				if ((self.lip < 1))
				{
					self.lip = 1;
				}
				else
				{
					self.lip = -1;
				}
				self.velocity_z = (2 * self.lip);
			}
		}
	}
	if (self.idlereverse)
	{
		self.count = (self.count - 1);
	}
	else
	{
		self.count = (self.count + 1);
	}
	if ((self.count >= JS_ANIMBLOCK))
	{
		self.count = 0;
	}
	if ((self.count < 0))
	{
		self.count = 5;
	}
	if ((self.idlebusy > 0))
	{
		fstate = self.idlebusy;
	}
	self.frame = ((fstate * JS_ANIMBLOCK) + self.count);
	self.oldorigin = self.origin;
};

void() jim_stand1 = [ 0, jim_stand1 ]
{
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_FLY;
	jim_update(JS_IDLE);
	ai_stand();
};

void() jim_walk1 = [ 0, jim_walk1 ]
{
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	jim_update(JS_IDLE);
	ai_walk(8);
};

void() jim_run1 = [ 0, jim_run1 ]
{
	if ((pointcontents(self.origin) == CONTENT_SOLID))
	{
		setorigin(self, (self.oldorigin + '0 0 -1'));
		ai_run(-10);
	}
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	ai_face();
	traceline((self.origin + '0 0 1'), (self.enemy.origin + '0 0 1'), FALSE, self);
	if (((trace_ent != self.enemy) && (self.attack_chance < 6)))
	{
		if ((pointcontents(self.origin) != CONTENT_SOLID))
			self.oldorigin = self.origin;
		self.attack_chance = (self.attack_chance + 1);
		ai_run(-60);
	}
	else
	{
		jim_update(JS_IDLE);
		ai_run((10 + skill));
	}
};

void(vector org, vector dir, float proj_speed) LaunchRocket =
{
	newmis = spawn();
	newmis.owner = self;
	newmis.movetype = MOVETYPE_FLYMISSILE;
	newmis.solid = SOLID_BBOX;
	newmis.angles = vectoangles(dir);
	newmis.touch = T_MissileTouch;
	newmis.classname = "jimrocket";
	newmis.think = SUB_Remove;
	newmis.nextthink = (time + 6);
	setmodel(newmis, "progs/missile.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, org);
	newmis.velocity = (dir * proj_speed);
};

void() jim_laser =
{
	local vector org;
	local vector dir;
	local vector vec;
	local vector follow;

	follow = self.enemy.velocity * 0.8;
	if (!self.enemy)
	{
		return;
	}
	if ((self.health < 1))
	{
		return;
	}
	if (!visxray(SUB_entEnemyTarget(), self.attack_offset, '0 0 12', FALSE))
	{
		return;
	}
	self.effects = (self.effects | EF_MUZZLEFLASH);
	sound7(self, CHAN_WEAPON, "hipweap/laserg.wav", 1, ATTN_NORM, SNDSPD);
	makevectors(self.angles);
	org = self.origin + attack_vector(self.attack_offset);
	dir = SUB_orgEnemyTarget() + '0 0 12';
	if ((skill < 2))
	{
		vec = normalize((dir - org));
	}
	else
	{
		vec = normalize(((dir + (follow * 0.4)) - org));
	}
	self.attack_speed = (SPEED_JIMPROJ + ((skill * 0.7) * SPEED_JIMPROJSKILL));
	LaunchLaser(org, vec);
};

void() jim_rocket =
{
	local vector org;
	local vector dir;
	local vector vec;

	if (!self.enemy)
	{
		return;
	}
	if ((self.health < 1))
	{
		return;
	}
	if (!visxray(SUB_entEnemyTarget(), self.attack_offset, '0 0 -12', FALSE))
	{
		return;
	}
	self.effects = (self.effects | EF_MUZZLEFLASH);
	sound(self, CHAN_WEAPON, "jim/rocket_fire.wav", 1, ATTN_NORM);
	makevectors(self.angles);
	org = self.origin + attack_vector(self.attack_offset);
	dir = SUB_orgEnemyTarget() - '0 0 12';
	vec = normalize((dir - org));
	self.attack_speed = (SPEED_JIMPROJ + (skill * SPEED_JIMPROJSKILL));
	LaunchRocket(org, vec, (self.attack_speed * 0.9));
};

void(float vspeed) jim_vel =
{
	ai_face();
	if ((self.movespeed == 0))
	{
		self.velocity = (self.attack_track * vspeed);
	}
};

void() jim_attack =
{
	self.solid = SOLID_SLIDEBOX;
	if ((self.movespeed == 0))
	{
		self.movetype = MOVETYPE_FLY;
	}
	makevectors(self.angles);
	self.attack_chance = 0;
	if ((random() < 0.4))
	{
		self.pos1 = v_up;
	}
	else
	{
		self.pos1 = (v_up * (50 + (random() * 100)));
	}
	self.pos2 = (v_right * (crandom() * 100));
	self.pos3 = (v_forward * (random() * 100));
	self.attack_track = ((self.pos1 + self.pos2) + self.pos3);
	traceline(self.origin, (self.origin + self.attack_track), FALSE, self);
};

void() jim_fire1 = [ 0, jim_fire2 ]
{

	jim_update(JS_IDLE);
	if (((((random() < 0.15) || self.has_fired) && (skill > 1)) && (vlen((self.enemy.origin - self.origin)) > 400)))
	{
		self.has_fired = 1;
		sound(self, CHAN_WEAPON, "jim/rocket_load.wav", 1, ATTN_NORM);
	}
	else
	{
		self.has_fired = 0;
		sound(self, CHAN_WEAPON, "jim/laser_load.wav", 1, ATTN_NORM);
	}
};

void() jim_fire2 = [ 0, jim_fire3 ]
{
	jim_update(JS_IDLE);
	jim_attack();
	if ((skill < 2))
	{
		jim_vel(0.4);
	}
	else
	{
		jim_vel(1.5);
	}
};

void() jim_fire3 = [ 0, jim_fire4 ]
{
	jim_update(JS_IDLE);
	if ((skill < 2))
	{
		jim_vel(0.6);
	}
};

void() jim_fire4 = [ 0, jim_fire5 ]
{
	jim_update(JS_IDLE);
	if ((skill < 2))
	{
		jim_vel(0.8);
	}
};

void() jim_fire5 = [ 0, jim_fire6 ]
{
	jim_update(JS_IDLE);
	jim_vel(1);
};

void() jim_fire6 = [ 0, jim_fire7 ]
{
	jim_update(JS_IDLE);
	if ((skill < 2))
	{
		jim_vel(1.2);
	}
	if ((self.has_fired == 1))
	{
		jim_rocket();
	}
	else
	{
		jim_laser();
	}
};

void() jim_fire7 = [ 0, jim_fire8 ]
{
	jim_update(JS_IDLE);
	if ((skill < 2))
	{
		jim_vel(1.4);
	}
	if ((self.has_fired == 0))
	{
		jim_laser();
	}
};

void() jim_fire8 = [ 0, jim_fire9 ]
{
	jim_update(JS_IDLE);
	if ((skill < 2))
	{
		jim_vel(1.3);
	}
	if (((self.has_fired == 0) && (skill >= 1)))
	{
		jim_laser();
	}
};

void() jim_fire9 = [ 0, jim_fire10 ]
{
	jim_update(JS_IDLE);
	if ((skill < 2))
	{
		jim_vel(1.1);
	}
	if (((self.has_fired == 0) && (skill > 2)))
	{
		jim_laser();
	}
};

void() jim_fire10 = [ 0, jim_fire11 ]
{
	jim_update(JS_IDLE);
	jim_vel(0.5);
};

void() jim_fire11 = [ 0, jim_run1 ]
{
	jim_update(JS_IDLE);
	self.has_fired = 0;
	if ((random() < 0.8))
	{
		SUB_AttackFinished((0.5 + random()));
	}
	else
	{
		SUB_AttackFinished((0.5 + (random() * 0.5)));
	}
};

void() jim_inpain =
{
	self.think = jim_inpain;
	self.nextthink = (time + 0.1);
	if ((self.inpain == 0))
	{
		particle_dust(self.origin, (10 + (random() * 10)), PARTICLE_BURST_YELLOW);
		self.pos1 = VEC_ORIGIN;
		self.pos1_x = (random() * self.lefty);
		self.pos1_z = (crandom() * -10);
	}
	else
	{
		if ((self.inpain >= 5))
		{
			self.angles_z = 0;
			self.angles_x = 0;
			self.think = self.th_run;
		}
		else
		{
			self.pos1 = (self.pos1 * 1.2);
			self.angles = (self.angles + self.pos1);
		}
	}
	jim_update(JS_PAIN);
	self.inpain = (self.inpain + 1);
};

void(entity attacker, float damage) jim_pain =
{
	monster_pain_check(attacker, damage);
	self.velocity = VEC_ORIGIN;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((random() < 0.5))
	{
		sound(self, CHAN_VOICE, self.pain_sound, 1, ATTN_NORM);
	}
	else
	{
		sound(self, CHAN_VOICE, self.pain_sound2, 1, ATTN_NORM);
	}
	self.inpain = 0;
	if (infront(attacker))
	{
		self.lefty = 10;
	}
	else
	{
		self.lefty = -10;
	}
	if ((random() > 0.6))
	{
		jim_inpain();
	}
};

void() jim_dying1 =
{
	self.frame = (JS_DYING + self.cnt);
	self.cnt = (self.cnt + 1);
	makevectors(self.angles);
	self.velocity = ((v_forward * 300) + (v_up * -30));
	if ((self.lefty == 1))
	{
		self.angles_y = (self.angles_y + 10);
	}
	else
	{
		self.angles_y = (self.angles_y - 10);
	}
	if ((random() < 0.3))
	{
		SpawnProjectileSmoke(self.origin, 150, 50, 150);
	}
	self.think = jim_dying1;
	self.nextthink = (time + 0.1);
	if ((self.cnt > 3))
	{
		self.think = jim_dying2;
		self.waitmin = (time + 1);
		self.cnt = 0;
	}
};

void() jim_dying2 =
{
	self.frame = (JS_DYING + self.cnt);
	self.cnt = (self.cnt + 1);
	if ((self.cnt > 5))
	{
		self.cnt = 0;
	}
	if ((random() > 0.7))
	{
		SpawnExplosion(EXPLODE_MED, self.origin, "jim/explode_minor.wav");
	}
	else
	{
		if ((random() < 0.3))
		{
			SpawnProjectileSmoke(self.origin, 150, 50, 150);
		}
	}
	makevectors(self.angles);
	self.solid = SOLID_BBOX;
	self.velocity = ((self.velocity * 0.2) + ((v_forward * 100) * 0.8));
	self.velocity = (normalize(self.velocity) * 300);
	self.velocity_z = (self.velocity_z - 200);
	if ((self.lefty == 1))
	{
		self.angles_y = (self.angles_y + 10);
	}
	else
	{
		self.angles_y = (self.angles_y - 10);
	}
	self.nextthink = (time + 0.1);
	if ((self.waitmin < time))
	{
		self.think = jim_is_dead;
	}
	else
	{
		self.think = jim_dying2;
	}
};

void() jim_is_dead =
{
	self.touch = SUB_Null;
	self.think = SUB_Null;
	particle_dust(self.origin, (10 + (random() * 10)), PARTICLE_BURST_YELLOW);
	sendParticle("rocket_explo_classic", self.origin, VEC_ORIGIN, 1);
	SpawnProjectileSmoke(self.origin, 150, 50, 150);
	SpawnProjectileSmoke(self.origin, 150, 50, 150);
	SpawnExplosion(EXPLODE_BIG, self.origin, "jim/explode_major.wav");
	sparklers();
	sparklers();
	entity_remove(self, 0.1);
};

void() jim_die =
{
	sound(self, CHAN_WEAPON, SOUND_EMPTY, 1, ATTN_NORM);
	sound(self, CHAN_VOICE, SOUND_EMPTY, 1, ATTN_NORM);
	sound(self, CHAN_ITEM, SOUND_EMPTY, 1, ATTN_NORM);
	sound(self, CHAN_AUTO, SOUND_EMPTY, 1, ATTN_NORM);
	sound(self, CHAN_AUTO, SOUND_EMPTY, 1, ATTN_NORM);
	sound(self, CHAN_AUTO, SOUND_EMPTY, 1, ATTN_NORM);
	sendParticle("rocket_explo_classic", self.origin, VEC_ORIGIN, 1);
	sparklers();
	sound(self, CHAN_VOICE, "jim/death1.wav", 1, ATTN_NORM);
	self.solid = 0;
	self.movetype = MOVETYPE_FLY;
	self.touch = jim_is_dead;
	self.cnt = 0;
	self.movespeed = 0;
	self.avelocity_x = ((random() * 50) - 100);
	self.avelocity_y = ((random() * 50) - 100);
	self.avelocity_z = ((random() * 50) - 100);
	if ((random() < 0.5))
	{
		self.lefty = 1;
	}
	else
	{
		self.lefty = 0;
	}
	particle_dust(self.origin, (10 + (random() * 10)), PARTICLE_BURST_YELLOW);
	SpawnExplosion(EXPLODE_BIG, self.origin, "jim/explode_minor.wav");
	SpawnProjectileSmoke(self.origin, 150, 50, 150);
	if (((((((!(self.spawnflags & MON_JIM_ROCKET) && (world.model != "maps/e1m1.bsp")) && (world.model != "maps/e3m1.bsp")) && (world.model != "maps/e2m1.bsp")) && (world.model != "maps/e3m9.bsp")) && (world.model != "maps/e2m9.bsp")) && ((random() * 100) < 50)))
	{
		hiplas_spawn();
	}
	if ((random() < 0.86))
	{
		jim_is_dead();
	}
	else
	{
		jim_dying1();
	}
};

void() monster_jim =
{
	if (deathmatch)
	{
		remove(self);
		return;
	}
	setmodel(self, "progs/mon_jimrock.mdl");
	setsize(self, '-16 -16 -24', '16 16 16');
	self.solid = SOLID_SLIDEBOX;
	self.movetype = 0;
	if ((self.bboxtype < 1))
	{
		self.bboxtype = BBOX_SHORT;
	}
	self.gibhealth = -300;
	self.gibbed = 0;
	self.pain_flinch = 30;
	self.pain_longanim = 0;
	self.blockudeath = TRUE;
	self.colormod = '0.6 0.6 0.6';
	if ((self.height == 0))
	{
		self.height = 64;
	}
	self.oldorigin = self.origin;
	self.idlebusy = 0;
	self.idlereverse = 0;
	self.attack_offset = '20 0 -10';
	self.th_stand = jim_stand1;
	self.th_walk = jim_walk1;
	self.th_run = jim_run1;
	self.th_pain = jim_pain;
	self.th_die = jim_die;
	self.th_missile = jim_fire1;
	self.classname = "monster_jim";
	self.classtype = 385;
	if ((self.health < 1))
	{
		self.health = 60;
	}
	self.idle_sound = "jim/idle1.wav";
	self.idle_sound2 = "jim/idle1r.wav";
	self.pain_sound = "jim/pain1.wav";
	self.pain_sound2 = "jim/pain2.wav";
	flymonster_start();
};

void() add_jim_support_walk =
{
	local entity clone;
	local vector pos;

	pos = self.origin;
	traceline(pos, (pos + '0 0 250'), FALSE, self);
	if ((vlen((trace_endpos - self.origin)) < 128))
	{
		return;
	}
	if ((trace_fraction == 1))
	{
		traceline(pos, (pos + '0 0 180'), FALSE, self);
		pos = trace_endpos - '0 0 40';
	}
	else
	{
		pos = trace_endpos - '0 0 40';
	}
	if (PM_InWall(self, pos))
	{
		return;
	}
	clone = spawn();
	copyentity(self, clone);
	clone.health = 0;
	clone.target = string_null;
	clone.killtarget = string_null;
	clone.spawnflags = 0;
	setorigin(clone, pos);
	clone.think = monster_jim;
	clone.nextthink = (time + 0.000100);
};

void() monster_bob =
{
	self.classname = "monster_jim";
	monster_jim();
};
