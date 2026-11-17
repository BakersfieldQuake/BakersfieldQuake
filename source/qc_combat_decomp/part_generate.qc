//Decompiled code. Please respect the original copyright.

float() emit_checksource =
{
	if ((self.entno_unique != self.pemit_source.entno_unique))
	{
		self.part_style = 0;
	}
	if ((self.part_style == PARTICLE_STYLE_EMPTY))
	{
		self.state = STATE_OFF;
	}
	else
	{
		if ((self.part_style != PARTICLE_STYLE_RESPAWN))
		{
			if ((self.pemit_source.estate & ESTATE_BLOCK))
			{
				self.state = STATE_OFF;
			}
		}
	}
	if ((self.state == STATE_OFF))
	{
		self.estate = ESTATE_OFF;
		return (TRUE);
	}
	else
	{
		return (0);
	}
};

void() emitdpp_particle =
{

	if (emit_checksource())
	{
		return;
	}
	if (self.pemit_target)
	{
		self.dpp_vel = vectoangles((self.pemit_target.origin - self.pemit_source.origin));
		self.dpp_vel_z = 0;
		makevectors(self.dpp_vel);
		self.dpp_vel = normalize(v_forward);
	}
	if (!CheckZeroVector(self.part_vol))
	{
		if (self.pemit_source.bsporigin)
		{
			self.pos1 = (self.pemit_source.origin + bmodel_origin(self.pemit_source));
		}
		else
		{
			self.pos1 = self.pemit_source.origin;
		}
		random();
		self.pos1_x = (self.pos1_x + ((random() * (self.part_vol_x * 2)) - self.part_vol_x));
		random();
		self.pos1_y = (self.pos1_y + ((random() * (self.part_vol_y * 2)) - self.part_vol_y));
		random();
		self.pos1_z = (self.pos1_z + ((random() * (self.part_vol_z * 2)) - self.part_vol_z));
	}
	else
	{
		self.pos1 = self.pemit_source.origin;
	}
	particleeffectnum(self.dpp_name);
	pointparticles(particleeffectnum(self.dpp_name), self.pos1, self.dpp_vel, 1);
	self.think = emitdpp_particle;
	self.nextthink = ((time + self.dpp_wait) + (random() * self.dpp_rnd));
};

void() emitdpp_fcircle =
{
	local float loop_cnt;
	local vector circle_vec;
	local vector circle_org;

	if (emit_checksource())
	{
		return;
	}
	loop_cnt = 4;
	while ((loop_cnt > 0))
	{
		loop_cnt = loop_cnt - 1;
		circle_vec = VEC_ORIGIN;
		makevectors(circle_vec);
		circle_org = self.pemit_source.origin + (v_forward * self.part_vol_x);
		pointparticles(particleeffectnum(self.dpp_name), circle_org, self.dpp_vel, 1);
	}
	if ((self.part_vol_x == 56))
	{
		particleeffectnum(DPP_FCIRCLE_RING);
		pointparticles(particleeffectnum(DPP_FCIRCLE_RING), self.pemit_source.origin, VEC_ORIGIN, 1);
	}
	self.think = emitdpp_fcircle;
	self.nextthink = ((time + self.dpp_wait) + (random() * self.dpp_rnd));
};

void() pe_splash1 = [ 0, pe_splash2 ]
{
	self.nextthink = (time + 0.05);
};

void() pe_splash2 = [ 1, pe_splash3 ]
{
	self.nextthink = (time + 0.05);
};

void() pe_splash3 = [ 2, pe_splash4 ]
{
	self.nextthink = (time + 0.05);
};

void() pe_splash4 = [ 3, pe_splash5 ]
{
	self.nextthink = (time + 0.05);
};

void() pe_splash5 = [ 4, pe_splash6 ]
{
	self.nextthink = (time + 0.05);
};

void() pe_splash6 = [ 5, finish_particle ]
{
	self.nextthink = (time + 0.05);
};

void() emitepp_weather =
{
	if (((self.attack_speed < time) && (self.speed > 0)))
	{
		self.attack_speed = ((time + self.speed) + (random() * self.speed));
		self.pos3_x = (crandom() * self.pos2_x);
		self.pos3_y = (crandom() * self.pos2_y);
	}
	self.t_width = (self.pos1_x + (random() * self.pos1_z));
	self.t_length = ((self.count * 0.75) + ((random() * 0.5) * self.count));
	self.pos3_z = ((self.pos2_z * 0.75) + ((random() * 0.5) * self.pos2_z));
	if ((self.spawnflags & PARTICLE_WEATHER_SNOW))
	{
		te_particlesnow(self.bbmins, self.bbmaxs, self.pos3, self.t_length, self.t_width);
	}
	else
	{
		te_particlerain(self.bbmins, self.bbmaxs, self.pos3, self.t_length, self.t_width);
	}
	self.think = emitepp_weather;
	self.nextthink = (time + 0.1);
};

void() emit_weather_think =
{
	if ((self.origin_z < (self.pos2_z + -4)))
	{
		self.movetype = 0;
		setorigin(self, (self.pos2 + '0 0 12'));
		setmodel(self, self.headmdl);
		self.velocity = VEC_ORIGIN;
		pe_splash1();
	}
	else
	{
		self.think = emit_weather_think;
		self.nextthink = (time + 0.1);
	}
};

void() emit_weather =
{
	if (emit_checksource())
	{
		return;
	}
	self.think = emit_weather;
	if (!self.enemy)
	{
		self.enemy = find(world, classname, "player");
	}
	if (!(self.enemy.flags & FL_CLIENT))
	{
		self.nextthink = (time + 0.1);
		return;
	}
	if ((range_distance(self.enemy, TRUE) < self.wakeup_dist))
	{
		self.nextthink = ((time + self.spawn_base) + (random() * self.spawn_rand));
		if ((self.pemit_tcount < self.part_limit))
		{
			part = fetch_particle();
			if ((part.classtype == CT_PARTICLE))
			{
				part.owner = self;
				self.pemit_tcount = (self.pemit_tcount + 1);
				part.movetype = self.part_movetype;
				setmodel(part, self.spr_name1);
				part.headmdl = self.spr_name2;
				setsize(part, VEC_ORIGIN, VEC_ORIGIN);
				part.velocity_x = (self.part_velrand_x * random());
				part.velocity_y = (self.part_velrand_y * random());
				part.velocity_z = (self.part_velrand_z * random());
				part.velocity = (part.velocity + self.part_vel);
				part.velocity_z = (0 - part.velocity_z);
				part.pos1_x = (self.pos1_x * random());
				part.pos1_y = (self.pos1_y * random());
				part.pos1_z = 0;
				part.pos1 = (part.pos1 + self.pos2);
				setorigin(part, part.pos1);
				traceline(part.pos1, (part.pos1 + '0 0 -4096'), TRUE, self);
				part.pos2 = trace_endpos;
				if (trace_inwater)
				{
					self.height = 8;
				}
				else
				{
					self.count = 0;
				}
				while ((self.height > 0))
				{
					if ((fabs((part.pos2_z - part.pos1_z)) < 8))
					{
						self.height = 0;
					}
					part.pos3 = part.pos1;
					part.pos3_z = (part.pos1_z + ((part.pos2_z - part.pos1_z) * 0.5));
					traceline(part.pos1, part.pos3, TRUE, self);
					if (trace_inwater)
					{
						part.pos2 = part.pos3;
					}
					else
					{
						part.pos1 = part.pos3;
					}
					self.height = (self.height - 1);
				}
				part.think = emit_weather_think;
				part.nextthink = (time + 0.1);
			}
		}
	}
	else
	{
		self.nextthink = ((time + self.wakeup_timer) + (random() * self.spawn_rand));
	}
};

void() emit_particle =
{
	local float randno;
	local vector angle_vec;

	if (emit_checksource())
	{
		return;
	}
	self.think = emit_particle;
	if (!self.enemy)
	{
		self.enemy = find(world, classname, "player");
	}
	if (!(self.enemy.flags & FL_CLIENT))
	{
		self.nextthink = (time + 0.1);
		return;
	}
	if ((range_distance(self.enemy, TRUE) < self.wakeup_dist))
	{
		self.nextthink = ((time + self.spawn_base) + (random() * self.spawn_rand));
		if ((self.pemit_tcount < self.part_limit))
		{
			part = fetch_particle();
			if ((part.classtype == CT_PARTICLE))
			{
				part.owner = self;
				self.pemit_tcount = (self.pemit_tcount + 1);
				part.movetype = self.part_movetype;
				randno = random();
				if ((randno < 0.3))
				{
					setmodel(part, self.spr_name1);
				}
				else
				{
					if ((randno < 0.6))
					{
						setmodel(part, self.spr_name2);
					}
					else
					{
						setmodel(part, self.spr_name3);
					}
				}
				if ((self.spr_frame == 1))
				{
					part.frame = rint((random() * 1.4));
				}
				else
				{
					if ((self.spr_frame == 2))
					{
						part.frame = rint((random() * 2));
					}
					else
					{
						part.frame = rint((random() * 3.4));
					}
				}
				setsize(part, VEC_ORIGIN, VEC_ORIGIN);
				if ((self.part_veltype == PARTICLE_ORIGIN_CIRCLE))
				{
					angle_vec = VEC_ORIGIN;
					makevectors(angle_vec);
					part.origin = (self.origin + (v_forward * self.part_vol_x));
					setorigin(part, (part.origin + self.part_ofs));
					self.circular_angle = anglemod((self.circular_angle + self.part_vol_y));
				}
				else
				{
					if ((self.part_veltype == PARTICLE_ORIGIN_RANDCIRCLE))
					{
						angle_vec = VEC_ORIGIN;
						makevectors(angle_vec);
						part.origin = (self.origin + (v_forward * self.part_vol_x));
						setorigin(part, (part.origin + self.part_ofs));
					}
					else
					{
						if ((self.part_veltype == PARTICLE_ORIGIN_SPIRAL))
						{
							angle_vec = VEC_ORIGIN;
							makevectors(angle_vec);
							if ((self.lefty == 0))
							{
								self.lefty = 1;
							}
							self.part_vol_z = (self.part_vol_z + self.lefty);
							if ((self.part_vol_z == 0))
							{
								self.lefty = 1;
							}
							if ((self.part_vol_z == self.part_vol_x))
							{
								self.lefty = -1;
							}
							part.origin = (self.origin + (v_forward * self.part_vol_z));
							setorigin(part, (part.origin + self.part_ofs));
							self.circular_angle = anglemod((self.circular_angle + self.part_vol_y));
						}
						else
						{
							if ((self.part_veltype == PARTICLE_ORIGIN_CENTER))
							{
								part.origin = (self.pemit_source.origin + self.part_ofs);
								setorigin(part, part.origin);
							}
							else
							{
								if (self.pemit_source.bsporigin)
								{
									part.pos1 = (self.pemit_source.origin + bmodel_origin(self.pemit_source));
									part.origin = part.pos1;
									if (CheckZeroVector(self.part_vol))
									{
										self.part_vol = (self.pemit_source.size * 0.5);
									}
								}
								else
								{
									part.origin = (self.pemit_source.origin + self.part_ofs);
								}
								random();
								part.origin_x = (part.origin_x + ((random() * (self.part_vol_x * 2)) - self.part_vol_x));
								random();
								part.origin_y = (part.origin_y + ((random() * (self.part_vol_y * 2)) - self.part_vol_y));
								random();
								part.origin_z = (part.origin_z + ((random() * (self.part_vol_z * 2)) - self.part_vol_z));
								setorigin(part, part.origin);
							}
						}
					}
				}
				if (self.pemit_target)
				{
					if (self.pemit_target.bsporigin)
					{
						part.pos2 = (self.pemit_target.origin + bmodel_origin(self.pemit_target));
						angle_vec = part.pos2 - part.origin;
					}
					else
					{
						angle_vec = self.pemit_target.origin - part.origin;
					}
					angle_vec = normalize(angle_vec);
					part.velocity = (angle_vec * ((random() * self.part_vel_x) + self.part_vel_x));
					if ((((self.part_velrand_x > 0) || (self.part_velrand_y > 0)) || (self.part_velrand_z > 0)))
					{
						random();
						part.velocity_x = ((part.velocity_x + (random() * (self.part_velrand_x * 2))) - self.part_velrand_x);
						random();
						part.velocity_y = ((part.velocity_y + (random() * (self.part_velrand_y * 2))) - self.part_velrand_y);
						random();
						part.velocity_z = ((part.velocity_z + (random() * (self.part_velrand_z * 2))) - self.part_velrand_z);
					}
				}
				else
				{
					if ((self.part_veltype == PARTICLE_ORIGIN_CENTER))
					{
						part.velocity = VEC_ORIGIN;
						random();
						part.velocity_x = (self.part_vel_x - (random() * (self.part_vel_x * 2)));
						random();
						part.velocity_y = (self.part_vel_y - (random() * (self.part_vel_y * 2)));
						random();
						part.velocity_z = (self.part_vel_z - (random() * (self.part_vel_z * 2)));
						part.velocity = (part.velocity + self.part_velbase);
					}
					else
					{
						part.velocity = VEC_ORIGIN;
						part.velocity_x = ((random() * self.part_vel_x) + self.part_vel_x);
						part.velocity_y = ((random() * self.part_vel_y) + self.part_vel_y);
						part.velocity_z = ((random() * self.part_vel_z) + self.part_vel_z);
						part.velocity = (part.velocity + self.part_velbase);
						if ((((self.part_velrand_x > 0) || (self.part_velrand_y > 0)) || (self.part_velrand_z > 0)))
						{
							random();
							part.velocity_x = ((part.velocity_x + (random() * (self.part_velrand_x * 2))) - self.part_velrand_x);
							random();
							part.velocity_y = ((part.velocity_y + (random() * (self.part_velrand_y * 2))) - self.part_velrand_y);
							random();
							part.velocity_z = ((part.velocity_z + (random() * (self.part_velrand_z * 2))) - self.part_velrand_z);
						}
					}
				}
				if (self.part_velrot)
				{
					part.angles = self.enemy.angles;
					part.avelocity = VEC_ORIGIN;
					part.avelocity_y = (self.part_velrot + (random() * self.part_velrot));
				}
				part.nextthink = ((time + random()) + self.part_life);
				part.think = finish_particle;
			}
		}
	}
	else
	{
		self.nextthink = ((time + self.wakeup_timer) + (random() * self.spawn_rand));
	}
};

void(entity part_ent, float part_style) particle_style =
{
	local float ring_rand;

	ring_rand = random();
	if ((ring_rand < 0.4))
	{
		if ((part_style & PARTICLE_BURST_YELLOW))
		{
			setmodel(part_ent, PART_DOTSML_GOLD);
		}
		else
		{
			if ((part_style & PARTICLE_BURST_GREEN))
			{
				setmodel(part_ent, PART_DOTSML_LGREEN);
			}
			else
			{
				if ((part_style & PARTICLE_BURST_RED))
				{
					setmodel(part_ent, PART_DOTSML_GREY);
				}
				else
				{
					if ((part_style & PARTICLE_BURST_BLUE))
					{
						setmodel(part_ent, PART_DOTSML_BLUE);
					}
					else
					{
						if ((part_style & PARTICLE_BURST_PURPLE))
						{
							setmodel(part_ent, PART_DOTSML_PURP);
						}
						else
						{
							if ((part_style & PARTICLE_BURST_FIRE))
							{
								setmodel(part_ent, PART_TORCH1);
							}
							else
							{
								setmodel(part_ent, PART_DOTSML_WHITE);
							}
						}
					}
				}
			}
		}
	}
	else
	{
		if ((ring_rand < 0.8))
		{
			if ((part_style & PARTICLE_BURST_YELLOW))
			{
				setmodel(part_ent, PART_DOTSML_YELLOW);
			}
			else
			{
				if ((part_style & PARTICLE_BURST_GREEN))
				{
					setmodel(part_ent, PART_DOTSML_GREEN);
				}
				else
				{
					if ((part_style & PARTICLE_BURST_RED))
					{
						setmodel(part_ent, PART_DOTSML_RED);
					}
					else
					{
						if ((part_style & PARTICLE_BURST_BLUE))
						{
							setmodel(part_ent, PART_DOTSML_GREY);
						}
						else
						{
							if ((part_style & PARTICLE_BURST_PURPLE))
							{
								setmodel(part_ent, PART_DOTSML_GREY);
							}
							else
							{
								if ((part_style & PARTICLE_BURST_FIRE))
								{
									setmodel(part_ent, PART_DOTSML_GOLD);
								}
								else
								{
									setmodel(part_ent, PART_DOTSML_GREY);
								}
							}
						}
					}
				}
			}
		}
		else
		{
			if ((part_style & PARTICLE_BURST_YELLOW))
			{
				setmodel(part_ent, PART_DOTMED_YELLOW);
			}
			else
			{
				if ((part_style & PARTICLE_BURST_GREEN))
				{
					setmodel(part_ent, PART_DOTMED_GREEN);
				}
				else
				{
					if ((part_style & PARTICLE_BURST_RED))
					{
						setmodel(part_ent, PART_DOTMED_RED);
					}
					else
					{
						if ((part_style & PARTICLE_BURST_BLUE))
						{
							setmodel(part_ent, PART_DOTMED_BLUE);
						}
						else
						{
							if ((part_style & PARTICLE_BURST_PURPLE))
							{
								setmodel(part_ent, PART_DOTMED_PURP);
							}
							else
							{
								if ((part_style & PARTICLE_BURST_FIRE))
								{
									setmodel(part_ent, PART_DOTMED_GREY);
								}
								else
								{
									setmodel(part_ent, PART_DOTMED_GREY);
								}
							}
						}
					}
				}
			}
		}
	}
	part.frame = rint((random() * 3));
};

void(vector ring_org, vector ring_dir, vector ring_rdir, float ring_rad, float ring_qty, float ring_time, float ring_style) particle_ring =
{
	local vector circle_vec;
	local vector circle_org;
	local float ring_loop;
	local float ring_angle;
	local string dpp_string;

	if ((query_configflag(SVR_PARTICLES) != SVR_PARTICLES))
	{
		return;
	}
	if (ext_dppart)
	{
		if ((ring_style & PARTICLE_BURST_YELLOW))
		{
			dpp_string = DPP_RINGPARTY;
		}
		else
		{
			if ((ring_style & PARTICLE_BURST_GREEN))
			{
				dpp_string = DPP_RINGPARTG;
			}
			else
			{
				if ((ring_style & PARTICLE_BURST_RED))
				{
					dpp_string = DPP_RINGPARTR;
				}
				else
				{
					if ((ring_style & PARTICLE_BURST_BLUE))
					{
						dpp_string = DPP_RINGPARTB;
					}
					else
					{
						if ((ring_style & PARTICLE_BURST_PURPLE))
						{
							dpp_string = DPP_RINGPARTP;
						}
						else
						{
							dpp_string = DPP_RINGPARTW;
						}
					}
				}
			}
		}
	}
	else
	{
		if (((part_total + ring_qty) >= (part_max - 1)))
		{
			return;
		}
	}
	ring_loop = 0;
	ring_angle = 360 / ring_qty;
	while ((ring_loop < ring_qty))
	{
		if (ext_dppart)
		{
			circle_vec = VEC_ORIGIN;
			makevectors(circle_vec);
			circle_org = ring_org + (v_forward * ring_rad);
			pointparticles(particleeffectnum(dpp_string), circle_org, VEC_ORIGIN, 1);
		}
		else
		{
			part = fetch_particle();
			if ((part.classtype == CT_PARTICLE))
			{
				part.owner = self;
				part.movetype = MOVETYPE_NOCLIP;
				particle_style(part, ring_style);
				circle_vec = VEC_ORIGIN;
				makevectors(circle_vec);
				part.origin = (ring_org + (v_forward * ring_rad));
				setorigin(part, part.origin);
				setsize(part, VEC_ORIGIN, VEC_ORIGIN);
				part.velocity_x = (ring_dir_x + ((random() * (ring_rdir_x * 2)) - ring_rdir_x));
				part.velocity_y = (ring_dir_y + ((random() * (ring_rdir_y * 2)) - ring_rdir_y));
				part.velocity_z = (ring_dir_z + (random() * ring_rdir_z));
				part.nextthink = ((time + (random() * ring_time)) + ring_time);
				part.think = finish_particle;
			}
		}
		ring_loop = ring_loop + 1;
	}
};

void(entity part_ent, vector part_org, float expl_style) explosion_style =
{
	local vector org_volume;
	local vector expl_vel;

	if ((expl_style & PARTICLE_BURST_SHOCKWAVE))
	{
		org_volume = VEC_ORIGIN;
		org_volume_x = crandom() * 16;
		part_ent.origin = (part_org + org_volume);
		setorigin(part_ent, part_ent.origin);
		if ((random() < 0.3))
		{
			part_ent.velocity = VEC_ORIGIN;
			if ((random() < 0.5))
			{
				setmodel(part_ent, PART_DOTSML_GREY);
			}
			else
			{
				setmodel(part_ent, PART_DOTMED_GREY);
			}
			part_ent.frame = rint((random() * 3));
		}
		else
		{
			expl_vel_x = crandom() * 75;
			part_ent.velocity = expl_vel;
			part_ent.avelocity = vecrand(100, 200, FALSE);
			part_ent.movetype = MOVETYPE_TOSS;
			part_ent.gravity = 0.75;
			part_ent.flags = 0;
		}
	}
	else
	{
		if ((expl_style & PARTICLE_BURST_SKULLUP))
		{
			part_ent.origin_x = (part_org_x + (crandom() * 8));
			part_ent.origin_y = (part_org_y + (crandom() * 8));
			if ((self.health < 0))
			{
				part_ent.origin_z = (part_org_z - MON_VIEWOFS);
			}
			else
			{
				part_ent.origin_z = (part_org_z - (crandom() * MON_VIEWOFS));
			}
			setorigin(part_ent, part_ent.origin);
			part_ent.velocity_x = (crandom() * 8);
			part_ent.velocity_y = (crandom() * 8);
			part_ent.velocity_z = (random() * 25);
			part_ent.avelocity = vecrand(100, 200, FALSE);
			part_ent.movetype = MOVETYPE_FLY;
			part_ent.flags = 0;
		}
		else
		{
			if ((expl_style & PARTICLE_BURST_LOSTUP))
			{
				part_ent.origin_x = (part_org_x + (crandom() * 4));
				part_ent.origin_y = (part_org_y + (crandom() * 4));
				part_ent.origin_z = part_org_z;
				setorigin(part_ent, part_ent.origin);
				part_ent.velocity_x = (crandom() * 4);
				part_ent.velocity_y = (crandom() * 4);
				part_ent.velocity_z = (random() * 10);
				part_ent.avelocity = vecrand(100, 200, FALSE);
				part_ent.movetype = MOVETYPE_FLY;
				part_ent.flags = 0;
			}
			else
			{
				if ((expl_style & PARTICLE_BURST_MINOTAUR))
				{
					part_ent.origin_x = (part_org_x + (crandom() * 8));
					part_ent.origin_y = (part_org_y + (crandom() * 8));
					part_ent.origin_z = (part_org_z - (crandom() * MON_VIEWOFS));
					setorigin(part_ent, part_ent.origin);
					part_ent.velocity_x = (crandom() * 8);
					part_ent.velocity_y = (crandom() * 8);
					part_ent.velocity_z = (random() * 35);
					part_ent.avelocity = vecrand(100, 200, FALSE);
					part_ent.movetype = MOVETYPE_FLY;
					part_ent.flags = 0;
				}
				else
				{
					if ((expl_style & PARTICLE_BURST_UPWARD))
					{
						part_ent.origin_x = (part_org_x + (crandom() * 24));
						part_ent.origin_y = (part_org_y + (crandom() * 24));
						part_ent.origin_z = (part_org_z + (random() * 64));
						setorigin(part_ent, part_ent.origin);
						part_ent.velocity_x = (crandom() * 16);
						part_ent.velocity_y = (crandom() * 16);
						part_ent.velocity_z = (8 + (random() * 16));
						part_ent.movetype = MOVETYPE_FLY;
						part_ent.flags = 0;
					}
					else
					{
						part_ent.origin = part_org;
						setorigin(part_ent, part_ent.origin);
						part_ent.velocity = vecrand(0, 16, TRUE);
						part_ent.avelocity = vecrand(100, 200, FALSE);
						part_ent.movetype = MOVETYPE_FLY;
						part_ent.flags = 0;
					}
				}
			}
		}
	}
};

void(vector e_org, float e_qty, float e_speed, float e_dist, float p_style) particle_implode =
{
	local float e_loop;
	local float e_len;
	local float e_traveltime;
	local vector e_dir;
	local vector e_vdestdelta;
	local vector e_finaldest;
	local string dpp_string;

	if ((query_configflag(SVR_PARTICLES) != SVR_PARTICLES))
	{
		return;
	}
	if (((part_total + e_qty) >= (part_max - 1)))
	{
		return;
	}
	if (ext_dppart)
	{
		if ((p_style & PARTICLE_BURST_YELLOW))
		{
			dpp_string = DPP_BURSTPARTY;
		}
		else
		{
			if ((p_style & PARTICLE_BURST_GREEN))
			{
				dpp_string = DPP_BURSTPARTG;
			}
			else
			{
				if ((p_style & PARTICLE_BURST_RED))
				{
					dpp_string = DPP_BURSTPARTR;
				}
				else
				{
					if ((p_style & PARTICLE_BURST_BLUE))
					{
						dpp_string = DPP_BURSTPARTB;
					}
					else
					{
						if ((p_style & PARTICLE_BURST_PURPLE))
						{
							dpp_string = DPP_BURSTPARTP;
						}
						else
						{
							dpp_string = DPP_BURSTPARTW;
						}
					}
				}
			}
		}
	}
	e_loop = 0;
	while ((e_loop < e_qty))
	{
		e_loop = e_loop + 1;
		part = fetch_particle();
		if ((part.classtype == CT_PARTICLE))
		{
			part.owner = self;
			particle_style(part, p_style);
			e_dir = normalize(vecrand(0, 50, TRUE));
			e_finaldest = e_org + (e_dir * (e_dist + (random() * 50)));
			e_vdestdelta = e_org - e_finaldest;
			e_len = vlen(e_vdestdelta);
			e_traveltime = e_len / (e_speed + (random() * 50));
			setorigin(part, e_finaldest);
			setsize(part, VEC_ORIGIN, VEC_ORIGIN);
			part.movetype = MOVETYPE_NOCLIP;
			part.velocity = (e_vdestdelta * (1 / e_traveltime));
			part.nextthink = (time + e_traveltime);
			part.think = finish_particle;
		}
	}
};

void(vector e_org, float e_qty, float e_time, float p_style, float e_style) particle_explode =
{
	local float e_loop;
	local string dpp_string;

	if ((query_configflag(SVR_PARTICLES) != SVR_PARTICLES))
	{
		return;
	}
	e_qty = rint(e_qty);
	if (ext_dppart)
	{
		if ((e_style & PARTICLE_BURST_SHOCKWAVE))
		{
			if ((e_style & 1))
			{
				pointparticles(particleeffectnum(DPP_BURSTSHOCKWAVE1), e_org, VEC_ORIGIN, 1);
			}
			else
			{
				pointparticles(particleeffectnum(DPP_BURSTSHOCKWAVE1), e_org, VEC_ORIGIN, 1);
			}
		}
		else
		{
			if ((p_style & PARTICLE_BURST_YELLOW))
			{
				dpp_string = DPP_BURSTPARTY;
			}
			else
			{
				if ((p_style & PARTICLE_BURST_GREEN))
				{
					dpp_string = DPP_BURSTPARTG;
				}
				else
				{
					if ((p_style & PARTICLE_BURST_RED))
					{
						dpp_string = DPP_BURSTPARTR;
					}
					else
					{
						if ((p_style & PARTICLE_BURST_BLUE))
						{
							dpp_string = DPP_BURSTPARTB;
						}
						else
						{
							if ((p_style & PARTICLE_BURST_PURPLE))
							{
								dpp_string = DPP_BURSTPARTP;
							}
							else
							{
								dpp_string = DPP_BURSTPARTW;
							}
						}
					}
				}
			}
			pointparticles(particleeffectnum(dpp_string), e_org, VEC_ORIGIN, e_qty);
		}
	}
	else
	{
		if (((part_total + e_qty) >= (part_max - 1)))
		{
			return;
		}
		e_loop = 0;
		while ((e_loop < e_qty))
		{
			e_loop = e_loop + 1;
			part = fetch_particle();
			if ((part.classtype == CT_PARTICLE))
			{
				part.owner = self;
				particle_style(part, p_style);
				explosion_style(part, e_org, e_style);
				setsize(part, VEC_ORIGIN, VEC_ORIGIN);
				part.nextthink = ((time + (random() * e_time)) + e_time);
				part.think = finish_particle;
			}
		}
	}
};

void(vector debuff_center, float debuff_volsize, float debuff_qty, float debuff_style) particle_debuff =
{
	local float debuff_loop;
	local float debuff_time;
	local vector debuff_org;
	local vector debuff_vol;
	local string dpp_string;

	if ((query_configflag(SVR_PARTICLES) != SVR_PARTICLES))
	{
		return;
	}
	if (ext_dppart)
	{
		if ((debuff_style & PARTICLE_BURST_YELLOW))
		{
			dpp_string = DPP_RINGPARTY;
		}
		else
		{
			if ((debuff_style & PARTICLE_BURST_GREEN))
			{
				dpp_string = DPP_RINGPARTG;
			}
			else
			{
				if ((debuff_style & PARTICLE_BURST_RED))
				{
					dpp_string = DPP_RINGPARTR;
				}
				else
				{
					if ((debuff_style & PARTICLE_BURST_BLUE))
					{
						dpp_string = DPP_RINGPARTB;
					}
					else
					{
						if ((debuff_style & PARTICLE_BURST_PURPLE))
						{
							dpp_string = DPP_RINGPARTP;
						}
						else
						{
							dpp_string = DPP_RINGPARTW;
						}
					}
				}
			}
		}
	}
	else
	{
		if (((part_total + debuff_qty) >= (part_max - 1)))
		{
			return;
		}
	}
	debuff_loop = 0;
	debuff_time = 2;
	while ((debuff_loop < debuff_qty))
	{
		debuff_vol = vecrand(0, debuff_volsize, TRUE);
		debuff_org = debuff_center + debuff_vol;
		if (ext_dppart)
		{
			pointparticles(particleeffectnum(dpp_string), debuff_org, VEC_ORIGIN, 1);
		}
		else
		{
			part = fetch_particle();
			if ((part.classtype == CT_PARTICLE))
			{
				part.owner = self;
				part.movetype = MOVETYPE_NOCLIP;
				particle_style(part, debuff_style);
				setorigin(part, debuff_org);
				setsize(part, VEC_ORIGIN, VEC_ORIGIN);
				part.velocity = vecrand(0, 2, TRUE);
				part.velocity_z = (8 + (random() * 24));
				part.nextthink = ((time + (random() * debuff_time)) + debuff_time);
				part.think = finish_particle;
			}
		}
		debuff_loop = debuff_loop + 1;
	}
};

void(vector dust_center, float dust_qty, float dust_style) particle_dust =
{
	local float dust_loop;
	local float dust_volsize;
	local float dust_time;
	local vector dust_org;
	local vector dust_vol;
	local string dpp_string;

	if ((query_configflag(SVR_PARTICLES) != SVR_PARTICLES))
	{
		return;
	}
	if (ext_dppart)
	{
		if ((dust_style & PARTICLE_BURST_YELLOW))
		{
			dpp_string = DPP_RINGPARTY;
		}
		else
		{
			if ((dust_style & PARTICLE_BURST_GREEN))
			{
				dpp_string = DPP_RINGPARTG;
			}
			else
			{
				if ((dust_style & PARTICLE_BURST_RED))
				{
					dpp_string = DPP_RINGPARTR;
				}
				else
				{
					if ((dust_style & PARTICLE_BURST_BLUE))
					{
						dpp_string = DPP_RINGPARTB;
					}
					else
					{
						if ((dust_style & PARTICLE_BURST_PURPLE))
						{
							dpp_string = DPP_RINGPARTP;
						}
						else
						{
							dpp_string = DPP_RINGPARTW;
						}
					}
				}
			}
		}
	}
	else
	{
		if (((part_total + dust_qty) >= (part_max - 1)))
		{
			return;
		}
	}
	dust_loop = 0;
	dust_time = 1;
	dust_volsize = 16;
	while ((dust_loop < dust_qty))
	{
		dust_vol = vecrand(0, dust_volsize, TRUE);
		dust_org = dust_center + dust_vol;
		if (ext_dppart)
		{
			pointparticles(particleeffectnum(dpp_string), dust_org, VEC_ORIGIN, 1);
		}
		else
		{
			part = fetch_particle();
			if ((part.classtype == CT_PARTICLE))
			{
				part.owner = self;
				part.movetype = MOVETYPE_NOCLIP;
				part.solid = 0;
				particle_style(part, dust_style);
				setorigin(part, dust_org);
				setsize(part, VEC_ORIGIN, VEC_ORIGIN);
				part.velocity = vecrand(0, 35, TRUE);
				part.velocity_z = (-100 - (random() * 100));
				part.avelocity = '300 300 300';
				part.nextthink = ((time + (random() * dust_time)) + dust_time);
				part.think = finish_particle;
			}
		}
		dust_loop = dust_loop + 1;
	}
};
