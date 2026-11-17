//Decompiled code. Please respect the original copyright.

void(float loudness, float attn, float side) yakman_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.5))
		{
			if ((attn == 1))
			{
				sound7(self, CHAN_AUTO, "yakman/step1.wav", loudness, ATTN_NORM, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_AUTO, "yakman/step1.wav", loudness, ATTN_IDLE, SNDSPD);
			}
		}
		else
		{
			if ((attn == 1))
			{
				sound7(self, CHAN_AUTO, "yakman/step2.wav", loudness, ATTN_NORM, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_AUTO, "yakman/step2.wav", loudness, ATTN_IDLE, SNDSPD);
			}
		}
		if ((side && (autocvar_yakman_walking_quake >= 2)))
		{
			makevectors(self.angles);
			if ((side == 1))
			{
				particleeffectnum(/*52589i*/"shambler_foot_dust");
				pointparticles(particleeffectnum(/*52589i*/"shambler_foot_dust"), ((((self.origin + self.view_ofs) + (v_up * -40)) + (v_forward * 7)) + (v_right * -15)), VEC_ORIGIN, 1);
			}
			else
			{
				particleeffectnum(/*52589i*/"shambler_foot_dust");
				pointparticles(particleeffectnum(/*52589i*/"shambler_foot_dust"), ((((self.origin + self.view_ofs) + (v_up * -40)) + (v_forward * 7)) + (v_right * 15)), VEC_ORIGIN, 1);
			}
		}
		if (((loudness > 0.8) && ((autocvar_yakman_walking_quake == 1) || (autocvar_yakman_walking_quake == 3))))
		{
			shambler_walking_quake();
		}
	}
};

void() yakman_howl_walk1 = [ 73, yakman_howl_walk2 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk2 = [ 74, yakman_howl_walk3 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk3 = [ 75, yakman_howl_walk4 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk4 = [ 76, yakman_howl_walk5 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
	sound7(self, CHAN_VOICE, "yakman/big3.wav", 1, ATTN_IDLE, SNDSPD);
};

void() yakman_howl_walk5 = [ 77, yakman_howl_walk6 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk6 = [ 78, yakman_howl_walk7 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk7 = [ 79, yakman_howl_walk8 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk8 = [ 80, yakman_howl_walk9 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk9 = [ 81, yakman_howl_walk10 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk10 = [ 82, yakman_howl_walk11 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk11 = [ 83, yakman_howl_walk12 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk12 = [ 84, yakman_howl_walk13 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk13 = [ 85, yakman_howl_walk14 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk14 = [ 86, yakman_howl_walk15 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk15 = [ 87, yakman_howl_walk16 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk16 = [ 88, yakman_howl_walk17 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk17 = [ 89, yakman_howl_walk18 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk18 = [ 90, yakman_howl_walk19 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk19 = [ 91, yakman_howl_walk20 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk20 = [ 92, yakman_howl_walk21 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk21 = [ 93, yakman_howl_walk22 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk22 = [ 94, yakman_howl_walk23 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk23 = [ 95, yakman_howl_walk24 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk24 = [ 96, yakman_howl_walk25 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk25 = [ 97, yakman_howl_walk26 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk26 = [ 98, yakman_howl_walk27 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk27 = [ 99, yakman_howl_walk28 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk28 = [ 100, yakman_howl_walk29 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk29 = [ 101, yakman_howl_walk30 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk30 = [ 102, yakman_howl_walk31 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk31 = [ 103, yakman_howl_walk32 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk32 = [ 104, yakman_howl_walk33 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk33 = [ 105, yakman_howl_walk34 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk34 = [ 106, yakman_howl_walk35 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk35 = [ 107, yakman_howl_walk36 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() yakman_howl_walk36 = [ 108, yakman_walk1 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void(float fr, float fadd, float fmax) WalkFrame_Add =
{
	if (((self.walkframe < 0) || (self.walkframe > fmax)))
	{
		self.walkframe = 0;
	}
	self.frame = (fr + self.walkframe);
	self.walkframe = (self.walkframe + fadd);
};

void(float mad) yakman_anim =
{
	local float move;

	if ((self.walkframe == 24))
	{
		if ((random() < 0.22))
		{
			if (mad)
			{
				sound7(self, CHAN_VOICE, "yakman/snort1.wav", 1, ATTN_NORM, SNDSPD);
			}
			else
			{
				if ((random() < 0.5))
				{
					sound7(self, CHAN_VOICE, "yakman/grunt.wav", 1, ATTN_IDLE, SNDSPD);
				}
				else
				{
					sound7(self, CHAN_VOICE, "yakman/snort2.wav", 1, ATTN_IDLE, SNDSPD);
				}
			}
		}
		else
		{
			if (((random() < 0.11) && !mad))
			{
				yakman_howl_walk1();
				return;
			}
		}
	}
	WalkFrame_Add(227, 2, 22);
	if (((((self.frame == 227) || (self.frame == 229)) || (self.frame == 239)) || (self.frame == 241)))
	{
		move = 12;
	}
	else
	{
		if ((self.frame == 233))
		{
			move = 5;
			if (mad)
			{
				yakman_footsteps(1, 1, 1);
			}
			else
			{
				yakman_footsteps(1, 0, 1);
			}
		}
		else
		{
			if ((self.frame == 245))
			{
				move = 5;
				if (mad)
				{
					yakman_footsteps(1, 1, 2);
				}
				else
				{
					yakman_footsteps(1, 0, 2);
				}
			}
			else
			{
				if (((self.frame == 235) || (self.frame == 247)))
				{
					move = 4;
				}
				else
				{
					move = 9;
				}
			}
		}
	}
	if (mad)
	{
		ai_run(move);
	}
	else
	{
		ai_walk(move);
	}
};

void() yakman_reset =
{
	if (((self.frame < 227) || (self.frame > 250)))
	{
		self.walkframe = 0;
	}
};

void() yakman_walk2 = [ 227, yakman_walk2 ]
{
	yakman_anim(FALSE);
	self.nextthink = (time + 0.1);
};

void() yakman_walk1 =
{
	yakman_reset();
	yakman_walk2();
};

void() yakman_run2 = [ 227, yakman_run2 ]
{
	yakman_anim(TRUE);
	self.nextthink = (time + 0.08);
};

void() yakman_run1 =
{
	yakman_reset();
	yakman_run2();
};

void() yakman_stop1 = [ 61, yakman_stop2 ]
{
	movetogoal(40);
};

void() yakman_stop2 = [ 63, yakman_stop3 ]
{
	movetogoal(30);
};

void() yakman_stop3 = [ 65, yakman_stop4 ]
{
	movetogoal(40);
	yakman_footsteps(1, 1, 1);
};

void() yakman_stop4 = [ 67, yakman_stop5 ]
{
	movetogoal(40);
};

void() yakman_stop5 = [ 69, yakman_stop6 ]
{
	movetogoal(30);
};

void() yakman_stop6 = [ 71, yakman_run1 ]
{
	self.waitmax = (time + 6);
	movetogoal(40);
	yakman_footsteps(1, 1, 2);
};

float(float dist) QC_CloseEnough =
{
	if ((self.enemy.absmin_x > (self.absmax_x + dist)))
	{
		return (0);
	}
	if ((self.enemy.absmax_x < (self.absmin_x - dist)))
	{
		return (0);
	}
	if ((self.enemy.absmin_y > (self.absmax_y + dist)))
	{
		return (0);
	}
	if ((self.enemy.absmax_y < (self.absmin_y - dist)))
	{
		return (0);
	}
	if ((self.enemy.absmin_z > (self.absmax_z + dist)))
	{
		return (0);
	}
	if ((self.enemy.absmax_z < (self.absmin_z - dist)))
	{
		return (0);
	}
	return (TRUE);
};

void(float d) yak_run =
{
	local entity targ;
	local vector dir;
	local vector org;
	local vector vel;
	local float ldmg;

	targ = self.enemy;
	if (targ)
	{
		if (QC_CloseEnough(d))
		{
			if (infront(targ))
			{
				if (CanDamage(targ, self))
				{
					d = d / 2;
					if (!QC_CloseEnough(d))
					{
						walkmove(self.angles_y, d);
						ai_face();
					}
					makevectors(self.angles);
					dir = v_forward;
					sound7(self, CHAN_WEAPON, "yakman/crash.wav", 1, ATTN_NORM, SNDSPD);
					vel = dir * autocvar_yakman_ram_velocity;
					if ((targ.flags & FL_ONGROUND))
					{
						targ.flags = (targ.flags - FL_ONGROUND);
					}
					targ.velocity = (targ.velocity + vel);
					ldmg = ((random() + random()) + random()) * autocvar_yakman_ram_damage;
					if ((self.health <= 0))
					{
						ldmg = 10;
					}
					T_Damage(self.enemy, self, self, ldmg);
					org = self.origin + (v_forward * 16);
					dir = (v_forward * 100) + (v_right * (random() * 200));
					SpawnMeatSpray(org, dir);
					dir = (v_forward * 100) + ((random() * -200) * v_right);
					SpawnMeatSpray(org, dir);
					if ((self.health > 0))
					{
						if ((self.frame == 24))
						{
							self.think = yakman_stop2;
						}
						else
						{
							if ((self.frame == 26))
							{
								self.think = yakman_stop3;
							}
							else
							{
								if ((self.frame == 28))
								{
									self.think = yakman_stop4;
								}
								else
								{
									if ((self.frame == 30))
									{
										self.think = yakman_stop5;
									}
									else
									{
										if ((self.frame == 32))
										{
											self.think = yakman_stop6;
										}
										else
										{
											self.think = yakman_stop1;
										}
									}
								}
							}
						}
					}
					else
					{
						if (((self.health <= 0) && (self.alpha < 1)))
						{
							self.alpha = -1;
							te_customflash(self.origin, 500, 0.7, '1 0 0');
							self.nextthink = (time + 0.2);
							self.think = SUB_Remove;
						}
					}
					return;
				}
			}
			ai_face();
			return;
		}
	}
	if (walkmove(self.angles_y, d))
	{
		ai_face();
	}
	else
	{
		movetogoal((d / 2));
	}
};

void() vengeance_yak_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() yakman_charge1 = [ 24, yakman_charge2 ]
{
	yak_run(25);
};

void() yakman_charge2 = [ 26, yakman_charge3 ]
{
	yak_run(30);
};

void() yakman_charge3 = [ 28, yakman_charge4 ]
{
	yak_run(40);
	yakman_footsteps(1, 1, 1);
};

void() yakman_charge4 = [ 30, yakman_charge5 ]
{
	yak_run(40);
};

void() yakman_charge5 = [ 32, yakman_charge6 ]
{
	yak_run(30);
};

void() yakman_charge6 = [ 34, yakman_charge1 ]
{
	yak_run(40);
	yakman_footsteps(1, 1, 2);
	if ((time > self.waitmax))
	{
		self.waitmax = (time + 5);
		if (((self.health <= 0) && (self.alpha < 1)))
		{
			self.think = vengeance_yak_end1;
		}
		else
		{
			self.think = self.th_run;
		}
	}
};

void(float side) yakman_slam =
{
	local float dist;
	local float ldmg;
	local vector org;
	local vector vel;

	self.encore = 1;
	sound7(self, CHAN_WEAPON, "yakman/woosh.wav", 1, ATTN_NORM, SNDSPD);
	if (!self.enemy)
	{
		return;
	}
	if (!CanDamage(self.enemy, self))
	{
		return;
	}
	dist = vlen((self.enemy.origin - self.origin));
	if ((dist > 100))
	{
		return;
	}
	ldmg = ((random() + random()) + random()) * autocvar_yakman_melee_damage;
	T_Damage(self.enemy, self, self, ldmg);
	sound7(self, CHAN_WEAPON, "yakman/slam.wav", 1, ATTN_NORM, SNDSPD);
	makevectors(self.angles);
	self.enemy.flags = (self.enemy.flags - (self.enemy.flags & FL_ONGROUND));
	self.enemy.velocity = (((v_forward * 50) + (v_right * (100 * side))) + '0 0 300');
	self.enemy.velocity = (self.enemy.velocity * 0.5);
	org = (self.origin + (v_forward * 16)) + '0 0 12';
	vel = (v_right * side) * (random() * 200);
	SpawnMeatSpray(org, vel);
};

void() yakman_left1 = [ 18, yakman_left2 ]
{
	ai_charge(5);
	yakman_footsteps(0.8, 1, 1);
};

void() yakman_left2 = [ 20, yakman_left3 ]
{
	ai_charge(4);
};

void() yakman_left3 = [ 22, yakman_left4 ]
{
	ai_charge(9);
};

void() yakman_left4 = [ 0, yakman_left5 ]
{
	ai_charge(12);
	yakman_slam(-1);
};

void() yakman_left5 = [ 2, yakman_left6 ]
{
	ai_charge(12);
};

void() yakman_left6 = [ 4, yakman_left7 ]
{
	ai_charge(9);
	if ((skill >= 2))
	{
		if (!self.cnt)
		{
			self.think = yakman_run2;
			self.walkframe = 6;
		}
		self.cnt = !self.cnt;
	}
};

void() yakman_left7 = [ 6, yakman_run2 ]
{
	ai_charge(5);
	yakman_footsteps(0.8, 1, 2);
	self.walkframe = 8;
};

void() yakman_right1 = [ 6, yakman_right2 ]
{
	ai_charge(5);
	yakman_footsteps(0.8, 1, 1);
};

void() yakman_right2 = [ 8, yakman_right3 ]
{
	ai_charge(4);
};

void() yakman_right3 = [ 10, yakman_right4 ]
{
	ai_charge(9);
};

void() yakman_right4 = [ 12, yakman_right5 ]
{
	ai_charge(12);
	yakman_slam(1);
};

void() yakman_right5 = [ 14, yakman_right6 ]
{
	ai_charge(12);
};

void() yakman_right6 = [ 16, yakman_right7 ]
{
	ai_charge(9);
	if ((skill >= 2))
	{
		if (!self.cnt)
		{
			self.think = yakman_run2;
			self.walkframe = 18;
		}
		self.cnt = !self.cnt;
	}
};

void() yakman_right7 = [ 18, yakman_run2 ]
{
	ai_charge(5);
	yakman_footsteps(0.8, 1, 2);
	self.walkframe = 20;
};

void() yakman_melee =
{
	if ((self.frame == 233))
	{
		yakman_right1();
	}
	else
	{
		if ((self.frame == 245))
		{
			yakman_left1();
		}
		else
		{
			if ((self.encore && (random() < 0.1)))
			{
				self.th_missile();
			}
			else
			{
				ai_charge(9);
			}
		}
	}
};

void() s_explode_think =
{
	if ((self.frame >= self.cnt))
	{
		SUB_Remove();
		return;
	}
	self.frame = (self.frame + 1);
	self.nextthink = (time + self.wait);
	if ((self.frame == self.cnt))
	{
		self.think = SUB_Remove;
	}
};

void(float base, float add, float fps, string text) BecomeFpsExplosion =
{
	if (!add)
	{
		add = 6;
	}
	if (!fps)
	{
		fps = 10;
	}
	self.movetype = 0;
	self.velocity = VEC_ORIGIN;
	self.touch = SUB_Null;
	setmodel(self, text);
	self.solid = 0;
	self.frame = base;
	self.cnt = ((base + add) - 1);
	self.wait = (1 / fps);
	self.nextthink = (time + self.wait);
	self.think = s_explode_think;
};

void() YakStar_Touch =
{

	self.touch = SUB_Null;
	T_Damage(other, self, self.owner, autocvar_yakman_projectile_damage);
	self.origin = (self.origin - (8 * normalize(self.velocity)));
	sound(self, CHAN_WEAPON, "vengeance/skulltouch.wav", 1, ATTN_NORM);
	BecomeFpsExplosion((self.cnt + 6), 5, 20, "progs/s_kinn.spr");
	if (((((other.classname == "player") && (skill == 3)) && (random() < 0.2)) || ((other.flags & FL_MONSTER) && (other.health <= 10))))
	{
		if ((other.inflamed == 0))
		{
			sound(other, CHAN_AUTO, "player/inflame.wav", 1, ATTN_NORM);
			other.inflamed = 1;
			other.inflametime = (time + 10);
			other.inflamepause = (time + 1);
			if ((other.classname == "player"))
			{
				stuffcmd(other, "bf\n");
			}
		}
	}
};

void(vector start, vector end, float color1, float color2, float density, float full) Particle_Beam =
{
	local vector delta;
	local float points;
	local float dist;
	local vector next;

	delta = end - start;
	dist = vlen(delta);
	if (full)
	{
		points = dist / 24;
		points = ceil(points);
		dist = -24;
	}
	else
	{
		if ((deathmatch || coop))
		{
			points = 2;
		}
		else
		{
			points = 3;
		}
		dist = dist / points;
		dist = 0 - dist;
	}
	delta = normalize(delta);
	next = delta * dist;
	full = color1;
	while ((points > 0))
	{
		particle(end, delta, full, density);
		end = end + next;
		points = points - 1;
		if ((full == color1))
		{
			full = color2;
		}
		else
		{
			full = color1;
		}
	}
};

void(float rgb, float density, float full) Meteor_Trail =
{
	Particle_Beam(self.oldorigin, self.origin, rgb, rgb, density, full);
	self.oldorigin = self.origin;
};

void() YakStar_Think =
{
	if ((pointcontents(self.origin) == CONTENT_WATER))
	{
		self.traileffectnum = particleeffectnum(/*1i*/"");
	}
	if ((self.frame < 11))
	{
		Meteor_Trail(41, 2, TRUE);
	}
	else
	{
		if ((self.frame < 22))
		{
			Meteor_Trail(105, 2, TRUE);
		}
		else
		{
			Meteor_Trail(233, 2, TRUE);
		}
	}
	if ((self.delay <= time))
	{
		remove(self);
		return;
	}
	self.walkframe = (self.walkframe + 1);
	if ((self.walkframe > 5))
	{
		self.walkframe = 0;
	}
	self.frame = (self.cnt + self.walkframe);
	self.nextthink = (time + 0.05);
};

void(vector start, vector end, float sped) YakStar_Launch =
{
	local vector dir;

	newmis = spawn();
	newmis.owner = self;
	newmis.movetype = MOVETYPE_FLYMISSILE;
	newmis.solid = SOLID_BBOX;
	newmis.classname = "yakman_projectile";
	setmodel(newmis, "progs/s_kinn.spr");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, start);
	dir = normalize((end - start));
	newmis.velocity = (dir * sped);
	newmis.angles = vectoangles(newmis.velocity);
	newmis.touch = YakStar_Touch;
	newmis.delay = (time + 5);
	newmis.nextthink = 0.01;
	newmis.think = YakStar_Think;
	newmis.colormod = '1.1 0.6 0.6';
	newmis.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
	newmis.frame = (self.yakman_particles * 11);
	newmis.cnt = (self.yakman_particles * 11);
	newmis.walkframe = 0;
	newmis.oldorigin = start;
};

void(vector left, vector right) yak_magic =
{
	local vector spot_right;
	local vector spot_left;
	local float sped;
	local float zufall_right;
	local float zufall_left;

	zufall_right = 8 + (crandom() * 7);
	zufall_left = -8 + (crandom() * 7);
	sped = 1000 + (skill * 150);
	makevectors(self.enemy.v_angle);
	if (self.has_fired)
	{
		zufall_right = 108 + (crandom() * 7);
		zufall_left = -108 + (crandom() * 7);
		spot_right = ((self.enemy.origin + self.enemy.view_ofs) + (v_right * zufall_right)) + (v_up * (-48 + (random() * 80)));
		spot_left = ((self.enemy.origin + self.enemy.view_ofs) + (v_right * zufall_left)) + (v_up * (-48 + (random() * 80)));
	}
	else
	{
		spot_right = ((self.enemy.origin + self.enemy.view_ofs) + ((crandom() * v_right) * zufall_right)) + (v_up * (-27 + (random() * 50)));
		spot_left = ((self.enemy.origin + self.enemy.view_ofs) + ((crandom() * v_right) * zufall_left)) + (v_up * (-27 + (random() * 50)));
	}
	makevectors(self.angles);
	left = ((self.origin + (v_forward * left_x)) + (v_right * left_y)) + (v_up * left_z);
	right = ((self.origin + (v_forward * right_x)) + (v_right * right_y)) + (v_up * right_z);
	YakStar_Launch(left, spot_right, sped);
	YakStar_Launch(right, spot_left, sped);
};

void(vector left, vector right) yak_glitter =
{
	local vector up;

	up = '0 0 2';
	makevectors(self.angles);
	left = ((self.origin + (v_forward * left_x)) + (v_right * left_y)) + (v_up * left_z);
	right = ((self.origin + (v_forward * right_x)) + (v_right * right_y)) + (v_up * right_z);
	if ((self.yakman_particles == 2))
	{
		particle(left, up, 233, 10);
		particle(right, up, 233, 10);
	}
	else
	{
		if ((self.yakman_particles == 1))
		{
			particle(left, up, 105, 10);
			particle(right, up, 105, 10);
		}
		else
		{
			particle(left, up, 41, 5);
			particle(right, up, 41, 5);
			particle(left, up, 209, 5);
			particle(right, up, 209, 5);
		}
	}
};

void() yakman_shard1 = [ 161, yakman_shard2 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	sound7(self, CHAN_VOICE, "yakman/snort2.wav", 1, ATTN_NORM, SNDSPD);
	if (self.has_fired)
	{
		self.glow_size = 300;
		self.glow_color = 33;
		self.glow_trail = 1;
		self.traileffectnum = particleeffectnum(/*19565i*/"monsteracid");
		self.colormod = '0.6 1.2 0.6';
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard2 = [ 163, yakman_shard3 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	if (self.has_fired)
	{
		self.glow_size = 330;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard3 = [ 165, yakman_shard4 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	if (self.has_fired)
	{
		self.glow_size = 370;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard4 = [ 167, yakman_shard5 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	yak_glitter('6 -20 88', '-14 50 53');
	if (self.has_fired)
	{
		self.glow_size = 410;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard5 = [ 169, yakman_shard6 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	yak_glitter('-6 -41 78', '-18 48 70');
	if (self.has_fired)
	{
		self.glow_size = 450;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard6 = [ 171, yakman_shard7 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	yak_glitter('8 -38 64', '-20 41 77');
	if (self.has_fired)
	{
		self.glow_size = 480;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard7 = [ 173, yakman_shard8 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	yak_glitter('26 -22 52', '18 33 70');
	if (self.has_fired)
	{
		self.glow_size = 500;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard8 = [ 175, yakman_shard9 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	yak_glitter('38 -9 48', '36 9 42');
	if (self.has_fired)
	{
		self.glow_size = 500;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard9 = [ 177, yakman_shard10 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	self.shots_left = 3;
	self.shots_max = 3;
	sound7(self, CHAN_AUTO, "yakman/expsmall.wav", 1, ATTN_NORM, SNDSPD);
	yak_magic('26 -5 50', '26 8 42');
	if (self.has_fired)
	{
		self.glow_size = 500;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard10 = [ 179, yakman_shard11 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	yak_magic('14 -1 54', '15 11 45');
	if (self.has_fired)
	{
		self.glow_size = 440;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard11 = [ 181, yakman_shard12 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	yak_magic('26 -5 54', '26 10 45');
	if (self.has_fired)
	{
		self.glow_size = 360;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard12 = [ 183, yakman_shard13 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	if ((skill >= 2))
	{
		yak_magic('38 -9 48', '36 9 42');
	}
	if (self.has_fired)
	{
		self.glow_size = 260;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard13 = [ 185, yakman_shard14 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	if ((skill >= 2))
	{
		self.attack_finished = (((time + 0.9) + random()) - (skill * 0.25));
	}
	else
	{
		self.attack_finished = ((time + 1.5) + random());
	}
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.think = vengeance_yak_end1;
	}
	if (self.has_fired)
	{
		self.glow_size = 160;
		self.glow_trail = 1;
		self.nextthink = (time + 0.1);
	}
};

void() yakman_shard14 = [ 187, yakman_shard15 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() yakman_shard15 = [ 189, yakman_shard16 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() yakman_shard16 = [ 191, yakman_run1 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
	if (self.has_fired)
	{
		self.glow_size = 0;
		self.glow_color = 0;
		self.glow_trail = 0;
		self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
		self.colormod = '1 1 1';
	}
	if ((random() < 0.5))
	{
		SUB_CheckRefire(yakman_shard1);
	}
};

void() yakman_missile =
{
	self.encore = 0;
	if ((time > self.waitmax))
	{
		if ((fabs((self.enemy.origin_z - self.origin_z)) < 48))
		{
			if ((vlen((self.enemy.origin - self.origin)) > 120))
			{
				if ((random() < 0.2))
				{
					self.waitmax = ((time + 5) + random());
					yakman_charge1();
					return;
				}
			}
		}
	}
	self.has_fired = 0;
	yakman_shard1();
};

void() yakman_howl1 = [ 73, yakman_howl2 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = 0.05;
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl2 = [ 74, yakman_howl3 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl3 = [ 75, yakman_howl4 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl4 = [ 76, yakman_howl5 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
	sound7(self, CHAN_VOICE, "yakman/big3.wav", 1, ATTN_IDLE, SNDSPD);
};

void() yakman_howl5 = [ 77, yakman_howl6 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl6 = [ 78, yakman_howl7 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl7 = [ 79, yakman_howl8 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl8 = [ 80, yakman_howl9 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl9 = [ 81, yakman_howl10 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl10 = [ 82, yakman_howl11 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl11 = [ 83, yakman_howl12 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl12 = [ 84, yakman_howl13 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl13 = [ 85, yakman_howl14 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl14 = [ 86, yakman_howl15 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl15 = [ 87, yakman_howl16 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl16 = [ 88, yakman_howl17 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl17 = [ 89, yakman_howl18 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl18 = [ 90, yakman_howl19 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl19 = [ 91, yakman_howl20 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl20 = [ 92, yakman_howl21 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl21 = [ 93, yakman_howl22 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.alpha = (self.alpha + 0.01);
	}
};

void() yakman_howl22 = [ 94, yakman_howl23 ]
{
	self.nextthink = (time + 0.07);
};

void() yakman_howl23 = [ 95, yakman_howl24 ]
{
	self.nextthink = (time + 0.07);
};

void() yakman_howl24 = [ 96, yakman_howl25 ]
{
	self.nextthink = (time + 0.07);
};

void() yakman_howl25 = [ 97, yakman_howl26 ]
{
	self.nextthink = (time + 0.07);
};

void() yakman_howl26 = [ 98, yakman_howl27 ]
{
	self.nextthink = (time + 0.07);
};

void() yakman_howl27 = [ 99, yakman_howl28 ]
{
	self.nextthink = (time + 0.07);
};

void() yakman_howl28 = [ 100, yakman_howl29 ]
{
	self.nextthink = (time + 0.07);
};

void() yakman_howl29 = [ 101, yakman_howl30 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() yakman_howl30 = [ 102, yakman_howl31 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() yakman_howl31 = [ 103, yakman_howl32 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() yakman_howl32 = [ 104, yakman_howl33 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() yakman_howl33 = [ 105, yakman_howl34 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() yakman_howl34 = [ 106, yakman_howl35 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() yakman_howl35 = [ 107, yakman_howl36 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() yakman_howl36 = [ 108, yakman_stand1 ]
{
	self.nextthink = (time + 0.07);
	if (((self.health <= 0) && (self.alpha < 1)))
	{
		self.waitmax = ((time + 4) + random());
		if (((fabs((self.enemy.origin_z - self.origin_z)) < 48) && (random() < 0.2)))
		{
			if ((vlen((self.enemy.origin - self.origin)) > 120))
			{
				yakman_charge1();
			}
			else
			{
				yakman_shard1();
			}
		}
		else
		{
			yakman_shard1();
		}
	}
};

void() yakman_stand_anim =
{
	if ((self.walkframe == 24))
	{
		if ((random() < 0.2))
		{
			if ((random() < 0.5))
			{
				sound7(self, CHAN_VOICE, "yakman/grunt.wav", 1, ATTN_IDLE, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_VOICE, "yakman/snort2.wav", 1, ATTN_IDLE, SNDSPD);
			}
		}
		else
		{
			if ((random() < 0.11))
			{
				yakman_howl1();
				return;
			}
		}
	}
	WalkFrame_Add(203, 1, 23);
	ai_stand();
};

void() yakman_stand2 = [ 203, yakman_stand2 ]
{
	yakman_stand_anim();
	self.nextthink = (time + 0.06);
};

void() yakman_stand1 =
{
	if (((self.frame < 203) || (self.frame > 226)))
	{
		self.walkframe = 0;
	}
	yakman_stand2();
};

void() yakman_pain1 = [ 133, yakman_pain2 ]
{
	self.nextthink = (time + 0.08);
};

void() yakman_pain2 = [ 134, yakman_pain3 ]
{
	self.nextthink = (time + 0.08);
};

void() yakman_pain3 = [ 135, yakman_pain4 ]
{
	self.nextthink = (time + 0.08);
};

void() yakman_pain4 = [ 136, yakman_pain5 ]
{
	self.nextthink = (time + 0.08);
};

void() yakman_pain5 = [ 137, yakman_pain6 ]
{
	self.nextthink = (time + 0.1);
};

void() yakman_pain6 = [ 138, yakman_pain7 ]
{
	self.nextthink = (time + 0.08);
};

void() yakman_pain7 = [ 139, yakman_pain8 ]
{
	self.nextthink = (time + 0.08);
};

void() yakman_pain8 = [ 140, yakman_run1 ]
{
	self.nextthink = (time + 0.08);
};

void() yakman_shake1 = [ 141, yakman_shake2 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake2 = [ 142, yakman_shake3 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake3 = [ 143, yakman_shake4 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake4 = [ 144, yakman_shake5 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake5 = [ 145, yakman_shake6 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake6 = [ 146, yakman_shake7 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake7 = [ 147, yakman_shake8 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake8 = [ 148, yakman_shake9 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake9 = [ 149, yakman_shake10 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake10 = [ 150, yakman_shake11 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake11 = [ 151, yakman_shake12 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake12 = [ 152, yakman_shake13 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake13 = [ 153, yakman_shake14 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake14 = [ 154, yakman_shake15 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake15 = [ 155, yakman_shake16 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake16 = [ 156, yakman_shake17 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake17 = [ 157, yakman_shake18 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake18 = [ 158, yakman_shake19 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake19 = [ 159, yakman_shake20 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_shake20 = [ 160, yakman_run1 ]
{
	self.nextthink = (time + 0.06);
};

void(entity attacker, float damage) yakman_pain =
{
	if ((self.pain_finished > time))
	{
		return;
	}
	if (((random() * 200) > damage))
	{
		return;
	}
	self.walkframe = 0;
	if ((random() < 0.5))
	{
		self.pain_finished = (time + 2);
		sound7(self, CHAN_VOICE, "yakman/pain.wav", 1, ATTN_NORM, SNDSPD);
		yakman_pain1();
	}
	else
	{
		self.pain_finished = (time + 3);
		sound7(self, CHAN_VOICE, "yakman/big1.wav", 1, ATTN_NORM, SNDSPD);
		yakman_shake1();
	}
};

void() vengeance_yak_bright05 =
{
	self.alpha = 0.01;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	self.think = yakman_howl1;
};

void() vengeance_yak_bright04 =
{
	self.alpha = 0.01;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_yak_bright05;
};

void() vengeance_yak_bright03 =
{
	self.alpha = 0.01;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_yak_bright04;
};

void() vengeance_yak_bright02 =
{
	self.alpha = 0.01;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_yak_bright03;
};

void() vengeance_yak_bright01 =
{
	self.alpha = -1;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_yak_bright02;
};

void() vengeance_yak_bright00 =
{
	self.alpha = -1;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.1);
	self.think = vengeance_yak_bright01;
};

void(string modelname, float modelframe) vengeance_yakman =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, modelname);
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	self.frame = modelframe;
	self.solid = 0;
	MonsterPhysics(self, 3200);
	vengeance_yak_bright00();
};

void() yakman_die1 = [ 36, yakman_die2 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die2 = [ 37, yakman_die3 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die3 = [ 38, yakman_die4 ]
{
	self.nextthink = (time + 0.06);
	ai_forward(2);
};

void() yakman_die4 = [ 39, yakman_die5 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die5 = [ 40, yakman_die6 ]
{
	self.nextthink = (time + 0.06);
	ai_forward(4);
	self.solid = 0;
};

void() yakman_die6 = [ 41, yakman_die7 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die7 = [ 42, yakman_die8 ]
{
	self.nextthink = (time + 0.06);
	ai_forward(8);
};

void() yakman_die8 = [ 43, yakman_die9 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die9 = [ 44, yakman_die10 ]
{
	self.nextthink = (time + 0.06);
	ai_forward(10);
};

void() yakman_die10 = [ 45, yakman_die11 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die11 = [ 46, yakman_die12 ]
{
	self.nextthink = (time + 0.06);
	ai_forward(12);
};

void() yakman_die12 = [ 47, yakman_die13 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die13 = [ 48, yakman_die14 ]
{
	self.nextthink = (time + 0.06);
	ai_forward(11);
};

void() yakman_die14 = [ 49, yakman_die15 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die15 = [ 50, yakman_die16 ]
{
	self.nextthink = (time + 0.06);
	ai_forward(10);
};

void() yakman_die16 = [ 51, yakman_die17 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die17 = [ 52, yakman_die18 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die18 = [ 53, yakman_die19 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die19 = [ 54, yakman_die20 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die20 = [ 55, yakman_die21 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die21 = [ 56, yakman_die22 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die22 = [ 57, yakman_die23 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die23 = [ 58, yakman_die24 ]
{
	self.nextthink = (time + 0.06);
	pointparticles(particleeffectnum(/*52626i*/"shambler_falling_dust"), self.origin, VEC_ORIGIN, 1);
	Monster_Animation_EarthQuake(20, 377);
	sound7(self, CHAN_AUTO, "shambler/fall.wav", 1, ATTN_NORM, SNDSPD);
};

void() yakman_die24 = [ 59, yakman_die25 ]
{
	self.nextthink = (time + 0.06);
};

void() yakman_die25 = [ 60, yakman_die25 ]
{
	local float zufall;
	local float zet;

	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_yakmancorpsehealth, "progs/h_yak.mdl");
	if ((random() < 0.05))
	{
		self.grimrock_helper = 1;
	}
	if ((self.grimrock_helper == 1))
	{
		zet = 27;
		zufall = random();
		if ((zufall > 0.8))
		{
			ghost_die();
		}
		else
		{
			if ((zufall < 0.175))
			{
				if ((zufall < 0.004))
				{
					soul("progs/afrit.mdl", 64, 27.451);
				}
				else
				{
					soul("progs/yakman.mdl", 60, zet);
				}
			}
			else
			{
				vengeance_yakman("progs/yakman.mdl", 60);
			}
		}
	}
};

void() yakman_lightning_death = [ 137, yakman_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() yakman_lightning_death1 = [ 137, yakman_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	CopyMonsterToBodyQue(1, "progs/h_yak.mdl");
};

void() yakman_die =
{
	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			yakman_lightning_death();
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
	if (((self.health < -70) || ((((self.shocked > 0) || (self.enemy.weapon == IT_GRENADE_LAUNCHER)) || (self.enemy.weapon == IT_ROCKET_LAUNCHER)) && (random() < 0.15))))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_yakman * 0.01)))
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
		CeilSplat();
		CeilSplat();
		ThrowHead("progs/h_yak.mdl", self.health);
		ThrowGib("progs/gib_minoclaw1.mdl", self.health);
		ThrowGib("progs/gib_minoleg1.mdl", self.health);
		ThrowGib("progs/gib_minoclaw2.mdl", self.health);
		ThrowGib("progs/gib_minoleg2.mdl", self.health);
		ThrowGib("progs/gib_4.mdl", self.health);
		ThrowGib("progs/gib_4.mdl", self.health);
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		gibdeath_effects();
		return;
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_yakman * 0.01)))
		{
			the_matrix = 1;
			SNDSPD = 70;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	if ((random() < 0.3))
	{
		sound7(self, CHAN_VOICE, "yakman/death.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_VOICE, "yakman/die.wav", 1, ATTN_NORM, SNDSPD);
	}
	yakman_die1();
};

void() monster_yakman =
{
	local float skinner;
	local entity pain_skin_entity;

	self.classname = "monster_yakman";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/yakman.mdl");
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	self.health = autocvar_yakman_health;
	self.health_initial = self.health;
	self.scale = 1;
	self.alpha = 1;
	self.colormod = '1 1 1';
	self.painskin_helper = 3;
	self.netname = "monster_yakman";
	if ((autocvar_yakman_skin_selection == 1))
	{
		self.skin = 0;
		self.yakman_particles = 0;
	}
	else
	{
		if ((autocvar_yakman_skin_selection == 2))
		{
			self.skin = 1;
			self.yakman_particles = 1;
		}
		else
		{
			if ((autocvar_yakman_skin_selection == 3))
			{
				self.skin = 2;
				self.yakman_particles = 2;
			}
			else
			{
				if ((autocvar_yakman_skin_selection == 4))
				{
					self.skin = 3;
					self.yakman_particles = 1;
				}
				else
				{
					if ((autocvar_yakman_skin_selection == 5))
					{
						self.skin = 4;
						self.yakman_particles = 0;
					}
					else
					{
						skinner = random();
						if ((skinner < 0.2))
						{
							self.skin = 0;
							self.yakman_particles = 0;
						}
						else
						{
							if ((skinner < 0.4))
							{
								self.skin = 1;
								self.yakman_particles = 1;
							}
							else
							{
								if ((skinner < 0.6))
								{
									self.skin = 2;
									self.yakman_particles = 2;
								}
								else
								{
									if ((skinner < 0.8))
									{
										self.skin = 3;
										self.yakman_particles = 1;
									}
									else
									{
										self.skin = 4;
										self.yakman_particles = 0;
									}
								}
							}
						}
					}
				}
			}
		}
	}
	self.th_stand = yakman_stand1;
	self.th_walk = yakman_walk1;
	self.th_run = yakman_run1;
	self.th_melee = yakman_melee;
	self.th_missile = yakman_missile;
	self.th_pain = yakman_pain;
	self.th_die = yakman_die;
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
	MonsterPhysics(self, autocvar_yakmanmass);
};

void() monster_minotaur =
{
	self.classname = "monster_yakman";
	monster_yakman();
};

void() monster_yakman_start =
{
	local entity clone;

	self.scale = 1;
	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_yakman;
	clone.nextthink = (time + 0.000100);
};
