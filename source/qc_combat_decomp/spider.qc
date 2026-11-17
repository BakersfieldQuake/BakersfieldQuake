//Decompiled code. Please respect the original copyright.

float() spider_checkroof =
{
	local vector end;
	local float contents;
	local float num;
	local float surfacenum;
	local string tex;

	end = self.origin + '0 0 1000';
	traceline(self.origin, end, TRUE, self);
	contents = pointcontents(trace_endpos);
	end = trace_endpos;
	num = 0 - self.origin_z;
	if ((num < (autocvar_spider_free_space_limit_for_jumping + 20)))
	{
		return (0);
	}
	if ((contents == CONTENT_SKY))
	{
		return (0);
	}
	surfacenum = getsurfacenearpoint(world, end);
	if ((surfacenum >= 0))
	{
		tex = getsurfacetexture(world, surfacenum);
		if (((tex == "sky1") || (tex == "sky4")))
		{
			return (0);
		}
	}
	if ((trace_fraction == 1))
	{
		return (0);
	}
	else
	{
		return (1);
	}
};

float() spider_clearance =
{
	local vector end;
	local vector end1;
	local vector end2;
	local float end_true;
	local float end1_true;
	local float end2_true;

	makevectors(self.angles);
	end = self.origin;
	end1 = self.origin + (v_forward * 30);
	end2 = self.origin + (v_forward * -30);
	traceline(self.origin, end, TRUE, self);
	if ((trace_fraction == 1))
	{
		end_true = 1;
	}
	traceline(self.origin, end1, TRUE, self);
	if ((trace_fraction == 1))
	{
		end1_true = 1;
	}
	traceline(self.origin, end2, TRUE, self);
	if ((trace_fraction == 1))
	{
		end2_true = 1;
	}
	if ((((end_true == 1) && (end1_true == 1)) && (end2_true == 1)))
	{
		return (1);
	}
	else
	{
		return (0);
	}
};

void() spider_flipdown2 =
{
	if ((self.angles_z <= 0))
	{
		if ((self.enemy != world))
		{
			self.angles_z = 0;
			spider_run1();
			return;
		}
		else
		{
			self.angles_z = 0;
			spider_look1();
			return;
		}
	}
	self.angles_z = (self.angles_z - 30);
	self.think = spider_flipdown2;
	self.nextthink = (time + 0.1);
};

void() spider_flipdown =
{
	self.spider_is_hanging_on_ceiling = 0;
	self.th_stand = spider_look1;
	self.th_walk = spider_walk1;
	self.th_run = spider_run1;
	self.th_melee = spider_melee_random;
	self.th_missile = spider_ranged;
	self.th_pain = spider_pain;
	self.th_die = spider_die;
	self.think = spider_flipdown2;
	self.nextthink = (time + 0.03);
};

float() spider_nosky =
{
	local vector end;
	local float surfacenum;
	local string tex;

	end = self.origin + '0 0 200';
	traceline(self.origin, end, TRUE, self);
	surfacenum = getsurfacenearpoint(world, trace_endpos);
	if ((surfacenum >= 0))
	{
		tex = getsurfacetexture(world, surfacenum);
		if (((tex == "sky1") || (tex == "sky4")))
		{
			return (1);
		}
	}
	if ((pointcontents(trace_endpos) == CONTENT_SKY))
	{
		return (1);
	}
	else
	{
		return (0);
	}
};

void() spider_jump_down1 = [ 255, spider_jump_down2 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
	self.velocity_x = 0;
	self.velocity_y = 0;
	self.velocity_z = 500;
};

void() spider_jump_down2 = [ 256, spider_jump_down3 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
	self.velocity_x = 0;
	self.velocity_y = 0;
	self.velocity_z = 500;
};

void() spider_jump_down3 = [ 257, spider_jump_down4 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
	sound(self, CHAN_VOICE, "spider/spider_jump.wav", 1, ATTN_NORM);
	self.velocity_x = 0;
	self.velocity_y = 0;
	self.velocity_z = 500;
};

void() spider_jump_down4 = [ 258, spider_jump_down5 ]
{
	local vector dir;

	ai_face();
	self.nextthink = (time + 0.06);
	self.angles_z = 150;
	self.touch = Spider_JumpTouch;
	dir = normalize(((self.enemy.origin + '0 0 16') - self.origin));
	self.velocity = ((dir * 600) + '0 0 200');
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
	self.th_stand = spider_look1;
	self.th_walk = spider_walk1;
	self.th_run = spider_run1;
	self.th_melee = spider_melee_random;
	self.th_missile = spider_ranged;
	self.th_pain = spider_pain;
	self.th_die = spider_die;
};

void() spider_jump_down5 = [ 259, spider_jump_down6 ]
{
	self.nextthink = (time + 0.06);
	self.angles_z = 120;
};

void() spider_jump_down6 = [ 260, spider_jump_down7 ]
{
	self.nextthink = (time + 0.06);
	self.angles_z = 90;
};

void() spider_jump_down7 = [ 261, spider_jump_down8 ]
{
	self.nextthink = (time + 0.06);
	self.angles_z = 60;
};

void() spider_jump_down8 = [ 262, spider_jump_down9 ]
{
	self.nextthink = (time + 0.06);
	self.angles_z = 30;
};

void() spider_jump_down9 = [ 263, spider_jump_down10 ]
{
	self.nextthink = (time + 0.06);
	self.angles_z = 0;
};

void() spider_jump_down10 = [ 264, spider_jump_down11 ]
{
	self.nextthink = (time + 0.06);
};

void() spider_jump_down11 = [ 265, spider_jump_down12 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_jump_down12 = [ 266, spider_jump_down13 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_jump_down13 = [ 267, spider_jump_down14 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_jump_down14 = [ 268, spider_jump_down15 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_jump_down15 = [ 269, spider_jump_down16 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_jump_down16 = [ 270, spider_jump_down17 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_jump_down17 = [ 271, spider_jump_down18 ]
{
	self.nextthink = (time + 0.05);
	spider_footsteps(1);
};

void() spider_jump_down18 = [ 272, spider_jump_down19 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_jump_down19 = [ 273, spider_jump_down20 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_jump_down20 = [ 274, spider_jump_down21 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_jump_down21 = [ 275, spider_jump_down22 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_jump_down22 = [ 276, spider_jump_down23 ]
{
	self.nextthink = (time + 0.05);
	spider_footsteps(1);
};

void() spider_jump_down23 = [ 277, spider_run1 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_upidle =
{
	if ((self.enemy && (self.pausetime_ceiling < time)))
	{
		if (visible(self.enemy))
		{
			spider_web_up();
			return;
		}
	}
	else
	{
		ai_stand();
	}
	if (spider_nosky())
	{
		spider_flipdown();
		return;
	}
	self.frame = 356;
	self.think = spider_upidle;
	self.nextthink = (time + 0.02);
	if ((self.flags & FL_ONGROUND))
	{
		self.origin_z = (self.origin_z + 1);
		self.flags = (self.flags - FL_ONGROUND);
	}
	self.velocity_x = 0;
	self.velocity_y = 0;
	self.velocity_z = 250;
	if ((self.th_stand != spider_flipdown))
	{
		self.th_stand = spider_flipdown;
		self.th_walk = spider_flipdown;
	}
};

void() spider_web_up =
{
	local vector a;
	local vector b;
	local vector delta;

	self.gravity = 0;
	self.velocity_z = 5;
	self.spider_is_hanging_on_ceiling = 1;
	a = self.enemy.origin;
	b = self.origin;
	delta = a - b;
	if ((vlen(delta) < 350))
	{
		self.spider_is_hanging_on_ceiling = 0;
		spider_jump_down1();
		return;
	}
	self.speed_reducer = (self.speed_reducer + 1);
	if (((self.walkframe >= 27) && (self.speed_reducer == 2)))
	{
		self.walkframe = 0;
		if ((random() < 0.5))
		{
			self.pausetime_ceiling = (time + random());
			spider_upidle();
			return;
		}
	}
	if (((self.enemy.health < 1) && (self.speed_reducer == 2)))
	{
		self.enemy = world;
		self.th_stand();
		return;
	}
	if ((!visible(self.enemy) && (self.speed_reducer == 2)))
	{
		self.frame = 356;
		spider_upidle();
		return;
	}
	spider_nosky();
	if ((spider_nosky() && (self.speed_reducer == 2)))
	{
		self.spider_is_hanging_on_ceiling = 0;
		spider_flipdown();
		return;
	}
	self.think = spider_web_up;
	self.nextthink = (time + 0.02);
	if ((self.speed_reducer == 2))
	{
		self.frame = (117 + self.walkframe);
		self.walkframe = (self.walkframe + 1);
		ai_face();
	}
	if (((self.enemy == world) && (self.speed_reducer >= 2)))
	{
		self.spider_is_hanging_on_ceiling = 0;
		spider_flipdown();
		return;
	}
	visible(self.enemy);
	if ((visible(self.enemy) && (self.speed_reducer == 2)))
	{
		if ((self.walkframe == 17))
		{
			spider_webshot();
		}
	}
	if ((self.speed_reducer > 2))
	{
		self.speed_reducer = 0;
	}
};

void() spider_stand_ceiling_map_start = [ 356, spider_stand_ceiling_map_start ]
{
	ai_stand();
	self.nextthink = (time + 0.02);
	if (spider_nosky())
	{
		spider_flipdown();
		return;
	}
	if ((self.flags & FL_ONGROUND))
	{
		self.origin_z = (self.origin_z + 1);
		self.flags = (self.flags - FL_ONGROUND);
	}
	self.velocity_x = 0;
	self.velocity_y = 0;
	self.velocity_z = 500;
};

void() spider_updie1 = [ 382, spider_updie2 ]
{
	self.movetype = MOVETYPE_STEP;
	self.angles_z = 150;
	sound(self, CHAN_VOICE, "spider/spider_death.wav", 1, ATTN_NORM);
	self.solid = 0;
};

void() spider_updie2 = [ 383, spider_updie3 ]
{
	self.angles_z = 120;
};

void() spider_updie3 = [ 384, spider_updie4 ]
{
	self.angles_z = 90;
};

void() spider_updie4 = [ 385, spider_updie5 ]
{
	self.angles_z = 60;
};

void() spider_updie5 = [ 386, spider_updie6 ]
{
	self.angles_z = 30;
};

void() spider_updie6 = [ 387, spider_updie7 ]
{
	self.angles_z = 0;
};

void() spider_updie7 = [ 388, spider_updie8 ]
{
};

void() spider_updie8 = [ 389, spider_updie9 ]
{
};

void() spider_updie9 = [ 390, spider_updie10 ]
{
};

void() spider_updie10 = [ 391, spider_updie11 ]
{
};

void() spider_updie11 = [ 392, spider_updie12 ]
{
};

void() spider_updie12 = [ 393, spider_updie13 ]
{
};

void() spider_updie13 = [ 394, spider_updie14 ]
{
};

void() spider_updie14 = [ 395, spider_updie15 ]
{
};

void() spider_updie15 = [ 396, spider_updie16 ]
{
};

void() spider_updie16 = [ 397, spider_updie17 ]
{
};

void() spider_updie17 = [ 398, spider_updie18 ]
{
};

void() spider_updie18 = [ 399, spider_updie19 ]
{
};

void() spider_updie19 = [ 400, spider_updie19 ]
{
	spider_die19();
	return;
};

void() spider_uppain =
{
	if ((self.pain_finished > time))
	{
		return;
	}
	spider_flipdown();
	sound(self, CHAN_VOICE, "spider/spider_pain.wav", 1, ATTN_NORM);
	self.pain_finished = (time + 1.7);
};

void() spider_reaching_map_start =
{
	if ((self.nojump == -1))
	{
		self.th_stand = spider_stand_ceiling_map_start;
		self.th_walk = spider_flipdown;
		self.th_pain = spider_uppain;
		self.th_run = spider_web_up;
		self.th_melee = SUB_Null;
		self.th_missile = spider_web_up;
		self.th_die = spider_updie1;
		spider_stand_ceiling_map_start();
		return;
	}
	if ((self.velocity_z < 100))
	{
		spider_flipdown();
		return;
	}
	self.think = spider_reaching_map_start;
	self.nextthink = (time + 0.1);
};

void() spider_flipup_map_start =
{
	if ((self.angles_z >= 180))
	{
		self.angles_z = 180;
		spider_reaching_map_start();
		return;
	}
	self.think = spider_flipup_map_start;
	self.nextthink = (time + 0.1);
	self.angles_z = (self.angles_z + 30);
	self.velocity_z = 666;
};

void() spider_grabroof =
{
	if ((other.takedamage || other.health))
	{
		return;
	}
	self.nojump = -1;
	self.touch = SUB_Null;
	self.velocity = VEC_ORIGIN;
};

void(float loudness) spider_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.5))
		{
			sound(self, CHAN_AUTO, "spider/spider_walk1.wav", loudness, ATTN_IDLE);
		}
		else
		{
			sound(self, CHAN_AUTO, "spider/spider_walk2.wav", loudness, ATTN_IDLE);
		}
	}
};

void(float hitpoints) spider_damage =
{
	local vector delta;
	local float ldmg;
	local float directio;

	if (!self.enemy)
	{
		return;
	}
	ai_charge(2);
	if (!CanDamage(self.enemy, self))
	{
		return;
	}
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 85))
	{
		return;
	}
	if (self.spider_is_shambler)
	{
		ldmg = (((random() + random()) + random()) * hitpoints) * 2;
	}
	else
	{
		ldmg = ((random() + random()) + random()) * hitpoints;
	}
	T_Damage(self.enemy, self, self, ldmg);
	makevectors(self.angles);
	directio = crandom() * 200;
	particle(((self.origin + (v_forward * 66)) + (v_up * 15)), (directio * v_right), 73, (ldmg * 1.5));
};

float() CheckSpiderMelee =
{
	local vector delta;

	delta = self.enemy.origin - self.origin;
	if (self.spider_is_shambler)
	{
		if ((vlen(delta) < 100))
		{
			return (TRUE);
		}
	}
	else
	{
		if ((vlen(delta) < 77))
		{
			return (TRUE);
		}
	}
	return (0);
};

float() CheckSpiderJump =
{
	local vector dist;
	local vector spot1;
	local vector spot2;
	local float d;
	local entity targ;

	targ = self.enemy;
	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	traceline(spot1, spot2, FALSE, self);
	if ((trace_ent != targ))
	{
		return (0);
	}
	if (!autocvar_spider_improved_jump_behaviour)
	{
		if (((self.origin_z + self.mins_z) > ((self.enemy.origin_z + self.enemy.mins_z) + (0.75 * self.enemy.size_z))))
		{
			return (0);
		}
		if (((self.origin_z + self.maxs_z) < ((self.enemy.origin_z + self.enemy.mins_z) + (0.25 * self.enemy.size_z))))
		{
			return (0);
		}
	}
	else
	{
		if (((self.origin_z + self.mins_z) > ((self.enemy.origin_z + self.enemy.mins_z) + (0.75 * self.enemy.size_z))))
		{
			self.enemy_is_higher = 0;
		}
		else
		{
			if (((self.origin_z + self.maxs_z) < ((self.enemy.origin_z + self.enemy.mins_z) + (0.25 * self.enemy.size_z))))
			{
				self.enemy_is_higher = 2;
			}
			else
			{
				self.enemy_is_higher = 1;
			}
		}
	}
	dist = self.enemy.origin - self.origin;
	d = vlen(dist);
	if ((d < 130))
	{
		return (0);
	}
	else
	{
		if ((d < 400))
		{
			if ((random() < 0.05))
			{
				return (TRUE);
			}
		}
		else
		{
			if ((d < 700))
			{
				if ((random() < 0.01))
				{
					return (TRUE);
				}
			}
			else
			{
				return (0);
			}
		}
	}
};

float() CheckSpiderRanged =
{
	local vector spot1;
	local vector spot2;
	local entity targ;

	targ = self.enemy;
	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	traceline(spot1, spot2, FALSE, self);
	if ((trace_ent != targ))
	{
		return (0);
	}
	if ((time < self.attack_finished))
	{
		return (0);
	}
	if ((enemy_range == RANGE_FAR))
	{
		return (0);
	}
	if ((enemy_range == RANGE_MELEE))
	{
		return (0);
	}
	if ((random() < 0.05))
	{
		SUB_AttackFinished((2 + random()));
		return (TRUE);
	}
	return (0);
};

float() SpiderCheckAttack =
{
	if (CheckSpiderMelee())
	{
		self.attack_state = AS_MELEE;
		return (TRUE);
	}
	if (CheckSpiderJump())
	{
		self.attack_state = AS_MISSILE;
		return (TRUE);
	}
	if (CheckSpiderRanged())
	{
		self.attack_state = AS_MISSILE;
		self.webshot = 1;
		return (TRUE);
	}
	return (0);
};

void() spider_jump1 = [ 81, spider_jump2 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
};

void() spider_jump2 = [ 82, spider_jump3 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
};

void() spider_jump3 = [ 83, spider_jump4 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
};

void() spider_jump4 = [ 84, spider_jump5 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
};

void() spider_jump5 = [ 85, spider_jump6 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
};

void() spider_jump6 = [ 86, spider_jump7 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
};

void() spider_jump7 = [ 87, spider_jump8 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
};

void() spider_jump8 = [ 88, spider_jump9 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() spider_jump9 = [ 89, spider_jump10 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() spider_jump10 = [ 90, spider_jump11 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() spider_jump11 = [ 91, spider_jump12 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() spider_jump12 = [ 92, spider_jump13 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() spider_jump13 = [ 93, spider_jump14 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() spider_jump14 = [ 94, spider_jump15 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() spider_jump15 = [ 95, spider_jump16 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	spider_footsteps(1);
};

void() spider_jump16 = [ 96, spider_jump17 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	spider_footsteps(1);
};

void() spider_jump17 = [ 97, spider_jump18 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_jump18 = [ 98, spider_jump1 ]
{
	local float zufall;

	ai_stand();
	self.nextthink = (time + 0.07);
	zufall = random();
	if ((zufall > 0.75))
	{
		spider_idle1();
	}
	else
	{
		if ((zufall < 0.55))
		{
			spider_look1();
		}
	}
};

void() spider_idle1 = [ 334, spider_idle2 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle2 = [ 335, spider_idle3 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle3 = [ 336, spider_idle4 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle4 = [ 337, spider_idle5 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle5 = [ 338, spider_idle6 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle6 = [ 339, spider_idle7 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle7 = [ 340, spider_idle8 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle8 = [ 341, spider_idle9 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle9 = [ 342, spider_idle10 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle10 = [ 343, spider_idle11 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle11 = [ 344, spider_idle12 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle12 = [ 345, spider_idle13 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle13 = [ 346, spider_idle14 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((random() < 0.35))
	{
		sound(self, CHAN_VOICE, "spider/spider_idle.wav", 1, ATTN_IDLE);
	}
};

void() spider_idle14 = [ 347, spider_idle15 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle15 = [ 348, spider_idle16 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle16 = [ 349, spider_idle17 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle17 = [ 350, spider_idle18 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle18 = [ 351, spider_idle19 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle19 = [ 352, spider_idle20 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle20 = [ 353, spider_idle21 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle21 = [ 354, spider_idle22 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle22 = [ 355, spider_idle23 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle23 = [ 356, spider_idle24 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle24 = [ 357, spider_idle25 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle25 = [ 358, spider_idle26 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle26 = [ 359, spider_idle27 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle27 = [ 360, spider_idle28 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle28 = [ 361, spider_idle29 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle29 = [ 362, spider_idle30 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle30 = [ 363, spider_idle31 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle31 = [ 364, spider_idle32 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle32 = [ 365, spider_idle33 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle33 = [ 366, spider_idle34 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle34 = [ 367, spider_idle35 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle35 = [ 368, spider_idle36 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle36 = [ 369, spider_idle37 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle37 = [ 370, spider_idle38 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle38 = [ 371, spider_idle39 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle39 = [ 372, spider_idle40 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle40 = [ 373, spider_idle41 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle41 = [ 374, spider_idle42 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle42 = [ 375, spider_idle43 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle43 = [ 376, spider_idle44 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle44 = [ 377, spider_idle45 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle45 = [ 378, spider_idle46 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle46 = [ 379, spider_idle47 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle47 = [ 380, spider_idle48 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_idle48 = [ 381, spider_idle1 ]
{
	local float zufall;

	ai_stand();
	self.nextthink = (time + 0.07);
	zufall = random();
	if ((zufall > 0.5))
	{
		spider_look1();
	}
	else
	{
		if ((zufall < 0.22))
		{
			spider_jump1();
		}
	}
};

void() spider_look1 = [ 294, spider_look2 ]
{
	local float spider_map_start_ceiling;

	ai_stand();
	self.nextthink = (time + 0.07);
	spider_map_start_ceiling = autocvar_spider_hanging_on_ceiling_on_map_start_chance * 0.01;
	if (((((!self.spider_is_shambler && !self.spider_checked_ceiling_at_map_start) && (self.spider_jumped_ceiling_at_map_start == 0)) && (random() < spider_map_start_ceiling)) || (self.spawnflags & SPAWN_CEILING)))
	{
		if (spider_clearance())
		{
			if (spider_checkroof())
			{
				if ((self.flags & FL_ONGROUND))
				{
					self.flags = (self.flags - FL_ONGROUND);
					self.origin_z = (self.origin_z + 1);
					self.velocity_z = 666;
				}
				self.spider_jumped_ceiling_at_map_start = 1;
				self.frame = 382;
				self.touch = spider_grabroof;
				self.origin_z = (self.origin_z + 1);
				self.angles_z = 0;
				spider_flipup_map_start();
				return;
			}
		}
	}
	self.spider_checked_ceiling_at_map_start = 1;
	self.th_stand = spider_look1;
};

void() spider_look2 = [ 295, spider_look3 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look3 = [ 296, spider_look4 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look4 = [ 297, spider_look5 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look5 = [ 298, spider_look6 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look6 = [ 299, spider_look7 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look7 = [ 300, spider_look8 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look8 = [ 301, spider_look9 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look9 = [ 302, spider_look10 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look10 = [ 303, spider_look11 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look11 = [ 304, spider_look12 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look12 = [ 305, spider_look13 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look13 = [ 306, spider_look14 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look14 = [ 307, spider_look15 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look15 = [ 308, spider_look16 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look16 = [ 309, spider_look17 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look17 = [ 310, spider_look18 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look18 = [ 311, spider_look19 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look19 = [ 312, spider_look20 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look20 = [ 313, spider_look21 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look21 = [ 314, spider_look22 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look22 = [ 315, spider_look23 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look23 = [ 316, spider_look24 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look24 = [ 317, spider_look25 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look25 = [ 318, spider_look26 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look26 = [ 319, spider_look27 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look27 = [ 320, spider_look28 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look28 = [ 321, spider_look29 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look29 = [ 322, spider_look30 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look30 = [ 323, spider_look31 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((random() < 0.35))
	{
		sound(self, CHAN_VOICE, "spider/spider_idle.wav", 1, ATTN_IDLE);
	}
};

void() spider_look31 = [ 324, spider_look32 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look32 = [ 325, spider_look33 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look33 = [ 326, spider_look34 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look34 = [ 327, spider_look35 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look35 = [ 328, spider_look36 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look36 = [ 329, spider_look37 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look37 = [ 330, spider_look38 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look38 = [ 331, spider_look39 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look39 = [ 332, spider_look40 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() spider_look40 = [ 333, spider_look1 ]
{
	local float zufall;

	ai_stand();
	self.nextthink = (time + 0.07);
	zufall = random();
	if ((zufall > 0.72))
	{
		spider_idle1();
	}
	else
	{
		if ((zufall < 0.22))
		{
			spider_jump1();
		}
	}
};

void() spider_underground1 = [ 36, spider_underground2 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	self.alpha = 1;
};

void() spider_underground2 = [ 37, spider_underground3 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() spider_underground3 = [ 38, spider_underground4 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() spider_underground4 = [ 39, spider_underground5 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() spider_underground5 = [ 40, spider_underground6 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground6 = [ 41, spider_underground7 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground7 = [ 42, spider_underground8 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground8 = [ 43, spider_underground9 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground9 = [ 44, spider_underground10 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground10 = [ 45, spider_underground11 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground11 = [ 46, spider_underground12 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground12 = [ 47, spider_underground13 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground13 = [ 48, spider_underground14 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground14 = [ 49, spider_underground15 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground15 = [ 50, spider_underground16 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground16 = [ 51, spider_underground17 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground17 = [ 52, spider_underground18 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground18 = [ 53, spider_underground19 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground19 = [ 54, spider_underground20 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground20 = [ 55, spider_underground21 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground21 = [ 56, spider_underground22 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground22 = [ 57, spider_underground23 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground23 = [ 58, spider_underground24 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground24 = [ 59, spider_underground25 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground25 = [ 60, spider_underground26 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground26 = [ 61, spider_underground27 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground27 = [ 62, spider_underground28 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground28 = [ 63, spider_underground29 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground29 = [ 64, spider_underground30 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	pointparticles(particleeffectnum(/*51893i*/"spider_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() spider_underground30 = [ 65, spider_underground31 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground31 = [ 66, spider_underground32 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground32 = [ 67, spider_underground33 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground33 = [ 68, spider_underground34 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground34 = [ 69, spider_underground35 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground35 = [ 70, spider_underground36 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground36 = [ 71, spider_underground37 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground37 = [ 72, spider_underground38 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground38 = [ 73, spider_underground39 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground39 = [ 74, spider_underground40 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground40 = [ 75, spider_underground41 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
	self.takedamage = DAMAGE_AIM;
	self.solid = SOLID_SLIDEBOX;
};

void() spider_underground41 = [ 76, spider_underground42 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground42 = [ 77, spider_underground43 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground43 = [ 78, spider_underground44 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground44 = [ 79, spider_underground45 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
};

void() spider_underground45 = [ 80, spider_run1 ]
{
	ai_stand();
	self.nextthink = (time + 0.04);
	self.th_run = spider_run1;
	self.th_stand = spider_look1;
};

void() spider_wait_underground = [ 36, spider_wait_underground ]
{
	ai_stand();
	self.takedamage = 0;
	self.solid = 0;
	self.alpha = -1;
	self.th_run = spider_underground1;
};

void() spider_stand_random =
{
	local float hidechance;

	hidechance = autocvar_spider_hide_underground * 0.01;
	if ((random() < hidechance))
	{
		spider_wait_underground();
	}
	else
	{
		spider_look1();
	}
};

void() spider_jump_walk1 = [ 81, spider_jump_walk2 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.08);
};

void() spider_jump_walk2 = [ 82, spider_jump_walk3 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.08);
};

void() spider_jump_walk3 = [ 83, spider_jump_walk4 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.08);
};

void() spider_jump_walk4 = [ 84, spider_jump_walk5 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.08);
};

void() spider_jump_walk5 = [ 85, spider_jump_walk6 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.08);
};

void() spider_jump_walk6 = [ 86, spider_jump_walk7 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.08);
};

void() spider_jump_walk7 = [ 87, spider_jump_walk8 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.08);
};

void() spider_jump_walk8 = [ 88, spider_jump_walk9 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.05);
};

void() spider_jump_walk9 = [ 89, spider_jump_walk10 ]
{
	ai_walk(3);
	self.nextthink = (time + 0.05);
};

void() spider_jump_walk10 = [ 90, spider_jump_walk11 ]
{
	ai_walk(3);
	self.nextthink = (time + 0.05);
};

void() spider_jump_walk11 = [ 91, spider_jump_walk12 ]
{
	ai_walk(2);
	self.nextthink = (time + 0.05);
};

void() spider_jump_walk12 = [ 92, spider_jump_walk13 ]
{
	ai_walk(2);
	self.nextthink = (time + 0.05);
};

void() spider_jump_walk13 = [ 93, spider_jump_walk14 ]
{
	ai_walk(2);
	self.nextthink = (time + 0.05);
};

void() spider_jump_walk14 = [ 94, spider_jump_walk15 ]
{
	ai_walk(2);
	self.nextthink = (time + 0.05);
};

void() spider_jump_walk15 = [ 95, spider_jump_walk16 ]
{
	ai_walk(2);
	self.nextthink = (time + 0.05);
	spider_footsteps(1);
};

void() spider_jump_walk16 = [ 96, spider_jump_walk17 ]
{
	ai_walk(1);
	self.nextthink = (time + 0.05);
	spider_footsteps(1);
};

void() spider_jump_walk17 = [ 97, spider_jump_walk18 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() spider_jump_walk18 = [ 98, spider_walk9 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.07);
};

void() spider_walk1 = [ 0, spider_walk2 ]
{
	if ((random() < 0.3))
	{
		sound(self, CHAN_VOICE, "spider/spider_idle.wav", 1, ATTN_IDLE);
	}
	ai_walk(2);
	spider_footsteps(1);
	self.th_stand = spider_look1;
};

void() spider_walk2 = [ 1, spider_walk3 ]
{
	ai_walk(2);
};

void() spider_walk3 = [ 2, spider_walk4 ]
{
	ai_walk(2);
};

void() spider_walk4 = [ 3, spider_walk5 ]
{
	ai_walk(2);
};

void() spider_walk5 = [ 4, spider_walk6 ]
{
	ai_walk(2);
};

void() spider_walk6 = [ 5, spider_walk7 ]
{
	ai_walk(2);
};

void() spider_walk7 = [ 6, spider_walk8 ]
{
	ai_walk(2);
};

void() spider_walk8 = [ 7, spider_walk9 ]
{
	ai_walk(2);
	if ((random() < 0.2))
	{
		spider_jump_walk1();
	}
};

void() spider_walk9 = [ 8, spider_walk10 ]
{
	ai_walk(2);
};

void() spider_walk10 = [ 9, spider_walk11 ]
{
	ai_walk(2);
};

void() spider_walk11 = [ 10, spider_walk12 ]
{
	ai_walk(2);
};

void() spider_walk12 = [ 11, spider_walk13 ]
{
	ai_walk(2);
};

void() spider_walk13 = [ 12, spider_walk14 ]
{
	ai_walk(2);
	spider_footsteps(1);
};

void() spider_walk14 = [ 13, spider_walk15 ]
{
	ai_walk(2);
};

void() spider_walk15 = [ 14, spider_walk16 ]
{
	ai_walk(2);
};

void() spider_walk16 = [ 15, spider_walk17 ]
{
	ai_walk(2);
};

void() spider_walk17 = [ 16, spider_walk18 ]
{
	ai_walk(2);
};

void() spider_walk18 = [ 17, spider_walk19 ]
{
	ai_walk(2);
};

void() spider_walk19 = [ 18, spider_walk20 ]
{
	ai_walk(2);
};

void() spider_walk20 = [ 19, spider_walk21 ]
{
	ai_walk(2);
};

void() spider_walk21 = [ 20, spider_walk22 ]
{
	ai_walk(2);
};

void() spider_walk22 = [ 21, spider_walk23 ]
{
	ai_walk(2);
};

void() spider_walk23 = [ 22, spider_walk24 ]
{
	ai_walk(2);
};

void() spider_walk24 = [ 23, spider_walk1 ]
{
	ai_walk(2);
};

void() spider_run1 = [ 24, spider_run2 ]
{
	if ((random() < 0.3))
	{
		sound(self, CHAN_VOICE, "spider/spider_idle.wav", 1, ATTN_IDLE);
	}
	ai_run(9);
	self.nextthink = (time + 0.04);
	spider_footsteps(1);
};

void() spider_run2 = [ 25, spider_run3 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
};

void() spider_run3 = [ 26, spider_run4 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
};

void() spider_run4 = [ 27, spider_run5 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
};

void() spider_run5 = [ 28, spider_run6 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
};

void() spider_run6 = [ 29, spider_run7 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
};

void() spider_run7 = [ 30, spider_run8 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
	spider_footsteps(1);
};

void() spider_run8 = [ 31, spider_run9 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
};

void() spider_run9 = [ 32, spider_run10 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
};

void() spider_run10 = [ 33, spider_run11 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
};

void() spider_run11 = [ 34, spider_run12 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
};

void() spider_run12 = [ 35, spider_run1 ]
{
	ai_run(9);
	self.nextthink = (time + 0.04);
};

void() spider_bitea1 = [ 186, spider_bitea2 ]
{
	sound(self, CHAN_WEAPON, "spider/spider_bite.wav", 1, ATTN_NORM);
	ai_charge(0);
	self.nextthink = (time + 0.08);
};

void() spider_bitea2 = [ 187, spider_bitea3 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.08);
};

void() spider_bitea3 = [ 188, spider_bitea4 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.08);
};

void() spider_bitea4 = [ 189, spider_bitea5 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.08);
};

void() spider_bitea5 = [ 190, spider_bitea6 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.08);
};

void() spider_bitea6 = [ 191, spider_bitea7 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.08);
};

void() spider_bitea7 = [ 192, spider_bitea8 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.08);
};

void() spider_bitea8 = [ 193, spider_bitea9 ]
{
	ai_charge(3);
	self.nextthink = (time + 0.08);
};

void() spider_bitea9 = [ 194, spider_bitea10 ]
{
	ai_charge(5);
	spider_damage(autocvar_spider_melee);
	self.nextthink = (time + 0.08);
};

void() spider_bitea10 = [ 195, spider_bitea11 ]
{
	ai_charge(3);
	self.nextthink = (time + 0.08);
};

void() spider_bitea11 = [ 196, spider_bitea12 ]
{
	ai_charge(2);
	self.nextthink = (time + 0.08);
};

void() spider_bitea12 = [ 197, spider_bitea13 ]
{
	ai_charge(1);
	self.nextthink = (time + 0.08);
};

void() spider_bitea13 = [ 198, spider_run1 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.08);
};

void() spider_headbang1 = [ 173, spider_headbang2 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.09);
};

void() spider_headbang2 = [ 174, spider_headbang3 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.09);
};

void() spider_headbang3 = [ 175, spider_headbang4 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.09);
};

void() spider_headbang4 = [ 176, spider_headbang5 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.09);
};

void() spider_headbang5 = [ 177, spider_headbang6 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.09);
};

void() spider_headbang6 = [ 178, spider_headbang7 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.08);
	sound(self, CHAN_WEAPON, "spider/spider_headbang.wav", 1, ATTN_NORM);
};

void() spider_headbang7 = [ 179, spider_headbang8 ]
{
	ai_charge(1);
	self.nextthink = (time + 0.07);
};

void() spider_headbang8 = [ 180, spider_headbang9 ]
{
	ai_charge(2);
	self.nextthink = (time + 0.07);
};

void() spider_headbang9 = [ 181, spider_headbang10 ]
{
	ai_charge(2);
	spider_damage((autocvar_spider_melee - 1));
	self.nextthink = (time + 0.07);
};

void() spider_headbang10 = [ 182, spider_headbang11 ]
{
	ai_charge(1);
	self.nextthink = (time + 0.07);
};

void() spider_headbang11 = [ 183, spider_headbang12 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.07);
};

void() spider_headbang12 = [ 184, spider_headbang13 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.09);
};

void() spider_headbang13 = [ 185, spider_run1 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.09);
};

void() spider_legattack1 = [ 255, spider_legattack2 ]
{
	sound(self, CHAN_WEAPON, "spider/spider_legattack.wav", 1, ATTN_NORM);
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack2 = [ 256, spider_legattack3 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack3 = [ 257, spider_legattack4 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack4 = [ 258, spider_legattack5 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack5 = [ 259, spider_legattack6 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack6 = [ 260, spider_legattack7 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack7 = [ 261, spider_legattack8 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack8 = [ 262, spider_legattack9 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack9 = [ 263, spider_legattack10 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack10 = [ 264, spider_legattack11 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack11 = [ 265, spider_legattack12 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.05);
};

void() spider_legattack12 = [ 266, spider_legattack13 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.05);
};

void() spider_legattack13 = [ 267, spider_legattack14 ]
{
	ai_charge(2);
	self.nextthink = (time + 0.05);
};

void() spider_legattack14 = [ 268, spider_legattack15 ]
{
	ai_charge(2);
	spider_damage((autocvar_spider_melee - 1));
	self.nextthink = (time + 0.05);
};

void() spider_legattack15 = [ 269, spider_legattack16 ]
{
	ai_charge(2);
	self.nextthink = (time + 0.05);
};

void() spider_legattack16 = [ 270, spider_legattack17 ]
{
	ai_charge(2);
	self.nextthink = (time + 0.05);
};

void() spider_legattack17 = [ 271, spider_legattack18 ]
{
	ai_charge(1);
	self.nextthink = (time + 0.05);
};

void() spider_legattack18 = [ 272, spider_legattack19 ]
{
	ai_charge(1);
	self.nextthink = (time + 0.06);
};

void() spider_legattack19 = [ 273, spider_legattack20 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
	spider_footsteps(1);
};

void() spider_legattack20 = [ 274, spider_legattack21 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack21 = [ 275, spider_legattack22 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_legattack22 = [ 276, spider_legattack23 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
	spider_footsteps(1);
};

void() spider_legattack23 = [ 277, spider_run1 ]
{
	ai_charge(0);
	self.nextthink = (time + 0.06);
};

void() spider_melee_random =
{
	local float zufall;

	zufall = random();
	if ((zufall > 0.6))
	{
		spider_bitea1();
	}
	else
	{
		if ((zufall < 0.3))
		{
			spider_headbang1();
		}
		else
		{
			spider_legattack1();
		}
	}
};

void() spider_leap1 = [ 255, spider_leap2 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() spider_leap2 = [ 256, spider_leap3 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() spider_leap3 = [ 257, spider_leap4 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
	sound(self, CHAN_VOICE, "spider/spider_jump.wav", 1, ATTN_NORM);
};

void() spider_leap4 = [ 258, spider_leap5 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
	self.touch = Spider_JumpTouch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	if (autocvar_spider_improved_jump_behaviour)
	{
		if ((self.enemy_is_higher == 2))
		{
			self.velocity = ((v_forward * 400) + '0 0 375');
		}
		else
		{
			if ((self.enemy_is_higher == 1))
			{
				self.velocity = ((v_forward * 600) + '0 0 250');
			}
			else
			{
				self.velocity = ((v_forward * 400) + '0 0 150');
			}
		}
	}
	else
	{
		self.velocity = ((v_forward * 600) + '0 0 250');
	}
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
};

void() spider_leap5 = [ 259, spider_leap6 ]
{
	self.nextthink = (time + 0.06);
};

void() spider_leap6 = [ 260, spider_leap7 ]
{
	self.nextthink = (time + 0.06);
};

void() spider_leap7 = [ 261, spider_leap8 ]
{
	self.nextthink = (time + 0.06);
};

void() spider_leap8 = [ 262, spider_leap9 ]
{
	self.nextthink = (time + 0.06);
};

void() spider_leap9 = [ 263, spider_leap10 ]
{
	self.nextthink = (time + 0.06);
};

void() spider_leap10 = [ 264, spider_leap11 ]
{
	self.nextthink = (time + 0.06);
};

void() spider_leap11 = [ 265, spider_leap12 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_leap12 = [ 266, spider_leap13 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_leap13 = [ 267, spider_leap14 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_leap14 = [ 268, spider_leap15 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_leap15 = [ 269, spider_leap16 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_leap16 = [ 270, spider_leap17 ]
{
	self.nextthink = (time + 0.05);
	if (!autocvar_spider_improved_jump_behaviour)
	{
		self.nextthink = (time + 1);
	}
	else
	{
		self.nextthink = (time + 0.5);
	}
};

void() spider_leap17 = [ 271, spider_leap18 ]
{
	self.nextthink = (time + 0.05);
	spider_footsteps(1);
};

void() spider_leap18 = [ 272, spider_leap19 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_leap19 = [ 273, spider_leap20 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_leap20 = [ 274, spider_leap21 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_leap21 = [ 275, spider_leap22 ]
{
	self.nextthink = (time + 0.05);
};

void() spider_leap22 = [ 276, spider_leap23 ]
{
	self.nextthink = (time + 0.05);
	spider_footsteps(1);
};

void() spider_leap23 = [ 277, spider_run1 ]
{
	self.nextthink = (time + 0.05);
};

void() Spider_JumpTouch =
{
	local float ldmg;

	self.angles_z = 0;
	if ((self.health <= 0))
	{
		return;
	}
	if (other.takedamage)
	{
		if ((vlen(self.velocity) > 300))
		{
			ldmg = autocvar_spider_jump + (5 * random());
			if ((other.classname == "player"))
			{
				T_Damage(other, self, self, ldmg);
			}
		}
	}
	if (!checkbottom(self))
	{
		if ((self.flags & FL_ONGROUND))
		{
			self.touch = SUB_Null;
			self.think = spider_leap1;
			self.nextthink = (time + 0.1);
		}
		return;
	}
	self.touch = SUB_Null;
	self.think = spider_leap18;
	self.nextthink = (time + 0.1);
};

void() spider_web_touch =
{
	if ((other == self.owner))
	{
		return;
	}
	if ((other.solid == SOLID_TRIGGER))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	if (other.takedamage)
	{
		if ((other.classname == "player"))
		{
			T_Damage(other, self, self.owner, autocvar_spider_web);
			sound(self, CHAN_WEAPON, "spider/spider_impact.wav", 1, ATTN_NORM);
			if (((skill == 3) && (random() < 0.8)))
			{
				other.poisoned = 1;
				other.poisontime = (time + autocvar_wizard_projectiles_and_slime_poison_time);
				other.poisonpause = (time + autocvar_wizard_projectiles_and_slime_poison_frequence);
				stuffcmd(other, "v_cshift 1 0 1 0\n");
			}
			if ((autocvar_spider_paralyze_effect == 2))
			{
				pointparticles(particleeffectnum(/*51909i*/"spider_paralyze_player2"), other.origin, VEC_ORIGIN, 1);
			}
			else
			{
				pointparticles(particleeffectnum(/*51933i*/"spider_paralyze_player1"), other.origin, VEC_ORIGIN, 1);
			}
		}
	}
	else
	{
		pointparticles(particleeffectnum(/*51957i*/"web_touch"), self.origin, VEC_ORIGIN, 1);
		sound(self, CHAN_WEAPON, "spider/spider_impact.wav", 1, ATTN_NORM);
	}
	remove(self);
};

void() spider_webshot =
{
	local vector offang;
	local vector org;
	local vector vec;
	local entity web;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	if (self.spider_is_shambler)
	{
		org = (self.origin + (v_up * 3)) + (v_forward * 12);
	}
	else
	{
		if ((self.spider_is_hanging_on_ceiling == 1))
		{
			org = (self.origin + (v_up * 9)) + (v_forward * 7);
		}
		else
		{
			org = (self.origin + (v_up * -9)) + (v_forward * 7);
		}
	}
	web = spawn();
	web.classname = "web";
	setorigin(web, org);
	setmodel(web, "progs/web.mdl");
	web.scale = 0.7;
	setsize(web, VEC_ORIGIN, VEC_ORIGIN);
	web.movetype = MOVETYPE_FLYMISSILE;
	web.solid = SOLID_BBOX;
	vec = normalize(((self.enemy.origin + '0 0 15') - org));
	web.velocity = (vec * 500);
	web.angles = vectoangles(vec);
	web.traileffectnum = particleeffectnum(/*51971i*/"web_trail");
	web.owner = self;
	web.enemy = self.enemy;
	web.touch = spider_web_touch;
	web.think = SUB_Remove;
	web.nextthink = (time + 5);
	sound(self, CHAN_WEAPON, "spider/spider_spit.wav", 1, ATTN_NORM);
};

void() spider_web1 = [ 117, spider_web2 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web2 = [ 118, spider_web3 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web3 = [ 119, spider_web4 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web4 = [ 120, spider_web5 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web5 = [ 121, spider_web6 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web6 = [ 122, spider_web7 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web7 = [ 123, spider_web8 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web8 = [ 124, spider_web9 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web9 = [ 125, spider_web10 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web10 = [ 126, spider_web11 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web11 = [ 127, spider_web12 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web12 = [ 128, spider_web13 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web13 = [ 129, spider_web14 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web14 = [ 130, spider_web15 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web15 = [ 131, spider_web16 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web16 = [ 132, spider_web17 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web17 = [ 133, spider_web18 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
	spider_webshot();
};

void() spider_web18 = [ 134, spider_web19 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web19 = [ 135, spider_web20 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web20 = [ 136, spider_web21 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web21 = [ 137, spider_web22 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web22 = [ 138, spider_web23 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web23 = [ 139, spider_web24 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web24 = [ 140, spider_web25 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web25 = [ 141, spider_web26 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web26 = [ 142, spider_web27 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web27 = [ 143, spider_web28 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_web28 = [ 144, spider_run1 ]
{
	ai_face();
	self.nextthink = (time + 0.05);
};

void() spider_ranged =
{
	if ((self.webshot == 1))
	{
		spider_web1();
		self.webshot = 0;
	}
	else
	{
		spider_leap1();
	}
};

void() spider_pain1 = [ 278, spider_pain2 ]
{
	ai_back(3);
	self.nextthink = (time + 0.07);
};

void() spider_pain2 = [ 279, spider_pain3 ]
{
	ai_back(3);
	self.nextthink = (time + 0.07);
};

void() spider_pain3 = [ 280, spider_pain4 ]
{
	ai_back(2);
	self.nextthink = (time + 0.07);
};

void() spider_pain4 = [ 281, spider_pain5 ]
{
	ai_back(1);
	self.nextthink = (time + 0.07);
};

void() spider_pain5 = [ 282, spider_pain6 ]
{
	ai_back(1);
	self.nextthink = (time + 0.07);
};

void() spider_pain6 = [ 283, spider_pain7 ]
{
	self.nextthink = (time + 0.07);
};

void() spider_pain7 = [ 284, spider_pain8 ]
{
	self.nextthink = (time + 0.07);
};

void() spider_pain8 = [ 285, spider_pain9 ]
{
	self.nextthink = (time + 0.07);
};

void() spider_pain9 = [ 286, spider_pain10 ]
{
	self.nextthink = (time + 0.07);
};

void() spider_pain10 = [ 287, spider_pain11 ]
{
	self.nextthink = (time + 0.07);
	spider_footsteps(0.8);
};

void() spider_pain11 = [ 288, spider_run1 ]
{
	ai_forward(3);
	self.nextthink = (time + 0.07);
};

void(entity attacker, float damage) spider_pain =
{
	if ((self.touch == Spider_JumpTouch))
	{
		return;
	}
	if ((self.pain_finished > time))
	{
		return;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_spider * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound(self, CHAN_VOICE, "spider/spider_pain.wav", 1, ATTN_NORM);
	spider_pain1();
	self.pain_finished = (time + 2);
};

void() spider_dieburn1 = [ 382, spider_dieburn2 ]
{
	self.burnz_origin = 10;
	burn_toggle_allround();
};

void() spider_dieburn2 = [ 383, spider_dieburn3 ]
{
	self.burnz_origin = 8;
};

void() spider_dieburn3 = [ 384, spider_dieburn4 ]
{
	self.burnz_origin = 5;
	self.solid = 0;
};

void() spider_dieburn4 = [ 385, spider_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() spider_dieburn5 = [ 386, spider_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() spider_dieburn6 = [ 387, spider_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() spider_dieburn7 = [ 388, spider_dieburn8 ]
{
	self.burnz_origin = -5;
};

void() spider_dieburn8 = [ 389, spider_dieburn9 ]
{
	self.burnz_origin = -7;
};

void() spider_dieburn9 = [ 390, spider_dieburn9 ]
{
	self.burnz_origin = -9;
};

void() spider_die1 = [ 382, spider_die2 ]
{
	self.angles_z = 0;
};

void() spider_die2 = [ 383, spider_die3 ]
{
	sound(self, CHAN_VOICE, "spider/spider_death.wav", 1, ATTN_NORM);
};

void() spider_die3 = [ 384, spider_die4 ]
{
	self.solid = 0;
};

void() spider_die4 = [ 385, spider_die5 ]
{
};

void() spider_die5 = [ 386, spider_die6 ]
{
};

void() spider_die6 = [ 387, spider_die7 ]
{
};

void() spider_die7 = [ 388, spider_die8 ]
{
};

void() spider_die8 = [ 389, spider_die9 ]
{
};

void() spider_die9 = [ 390, spider_die10 ]
{
};

void() spider_die10 = [ 391, spider_die11 ]
{
};

void() spider_die11 = [ 392, spider_die12 ]
{
};

void() spider_die12 = [ 393, spider_die13 ]
{
};

void() spider_die13 = [ 394, spider_die14 ]
{
};

void() spider_die14 = [ 395, spider_die15 ]
{
};

void() spider_die15 = [ 396, spider_die16 ]
{
};

void() spider_die16 = [ 397, spider_die17 ]
{
};

void() spider_die17 = [ 398, spider_die18 ]
{
};

void() spider_die18 = [ 399, spider_die19 ]
{
};

void() spider_die19 = [ 400, spider_die19 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	zet = 19;
	if ((autocvar_spidercorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if (self.spider_is_shambler)
	{
		CopyMonsterToBodyQue(autocvar_spidercorpsehealth, "progs/h_spidbodyshamb.mdl");
	}
	else
	{
		CopyMonsterToBodyQue(autocvar_spidercorpsehealth, "progs/h_spidbody.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_spiderrandomness = autocvar_spiderrandomness * 0.01;
		if ((autocvar_spider == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_spiderrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_spider == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_spiderrandomness))
				{
					if (self.spider_is_shambler)
					{
						soul("progs/spider_shambler.mdl", 400, zet);
					}
					else
					{
						soul("progs/spider.mdl", 400, zet);
					}
				}
			}
			else
			{
				if ((autocvar_spider == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_spiderrandomness))
					{
						vengeance_spider("progs/spider.mdl", 400);
					}
				}
				else
				{
					if ((autocvar_spider == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_spiderrandomness))
						{
							zufall = random();
							if ((zufall > 0.8))
							{
								ghost_die();
							}
							else
							{
								if ((zufall < 0.2))
								{
									if (self.spider_is_shambler)
									{
										soul("progs/spider_shambler.mdl", 400, zet);
									}
									else
									{
										soul("progs/spider.mdl", 400, zet);
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
		if (((self.grimrock_helper == 1) && (self.velocity == VEC_ORIGIN)))
		{
			zufall = random();
			if ((zufall > 0.8))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.125))
				{
					if ((zufall < 0.004))
					{
						soul("progs/afrit.mdl", 385, 27.451);
					}
					else
					{
						if (self.spider_is_shambler)
						{
							soul("progs/spider_shambler.mdl", 400, zet);
						}
						else
						{
							soul("progs/spider.mdl", 400, zet);
						}
					}
				}
				else
				{
					vengeance_spider("progs/spider.mdl", 400);
				}
			}
		}
	}
};

void(float maxgibs, float gibscounter) producegibs_spider =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		if (self.spider_is_shambler)
		{
			ThrowGibSpider("progs/gib_spidlegshamb.mdl", self.health);
			ThrowGibSpider("progs/gib_spidlegshamb.mdl", self.health);
		}
		else
		{
			ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
			ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
			ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
			ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
		}
	}
	gibscounter = gibscounter + 1;
	producegibs_spider(maxgibs, gibscounter);
};

void() spider_lightning_death = [ 282, spider_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() spider_lightning_death1 = [ 282, spider_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.3 0.25 0.25';
	if (self.spider_is_shambler)
	{
		CopyMonsterToBodyQue(1, "progs/h_spidbodyshamb.mdl");
	}
	else
	{
		CopyMonsterToBodyQue(1, "progs/h_spidbody.mdl");
	}
};

void() spider_die =
{
	local float maxgibs;
	local float gibscounter;
	local float zufall;
	local float randomness;

	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			spider_lightning_death();
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
	if (((self.health < -35) || (self.enemy.weapon == IT_CHAINSAW)))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_spider * 0.01)))
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
		if ((autocvar_gibsmultiplier == 1))
		{
			if (self.spider_is_shambler)
			{
				ThrowHead("progs/h_spidbodyshamb.mdl", self.health);
				ThrowGibSpider("progs/gib_spidlegshamb.mdl", self.health);
				ThrowGibSpider("progs/gib_spidlegshamb.mdl", self.health);
			}
			else
			{
				ThrowHead("progs/h_spidbody.mdl", self.health);
				ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
				ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
				ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
				ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
			}
			if ((autocvar_bloodextension == 1))
			{
				pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
			}
			return;
		}
		else
		{
			if (self.spider_is_shambler)
			{
				ThrowHead("progs/h_spidbodyshamb.mdl", self.health);
			}
			else
			{
				ThrowHead("progs/h_spidbody.mdl", self.health);
			}
			maxgibs = autocvar_gibsmultiplier;
			gibscounter = 0;
			gibdeath_effects();
			producegibs_spider(maxgibs, gibscounter);
			return;
		}
	}
	autocvar_spiderrandomness = autocvar_spiderrandomness * 0.01;
	if ((autocvar_spider == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_spiderrandomness))
		{
			self.delete_painskin = 1;
			spider_dieburn1();
			return;
		}
	}
	if ((autocvar_spider == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_spiderrandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				spider_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_spider * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	spider_die1();
};

void() monster_spider =
{
	local float rand;
	local entity pain_skin_entity;

	self.classname = "monster_spider";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/spider.mdl");
	precache_model("progs/h_spidbody.mdl");
	precache_model("progs/web.mdl");
	precache_model("progs/gib_spidlegshamb.mdl");
	precache_model("progs/gib_spidlegb.mdl");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/spider.mdl");
	if (!self.skin)
	{
		self.skin = 0;
	}
	self.monstermodel = 0;
	if (autocvar_spider_random_skin_selection)
	{
		rand = random();
		if ((rand < 0.125))
		{
			self.skin = 0;
		}
		else
		{
			if ((rand < 0.25))
			{
				self.skin = 1;
			}
			else
			{
				if ((rand < 0.375))
				{
					self.skin = 2;
				}
				else
				{
					if ((rand < 0.5))
					{
						self.skin = 3;
					}
					else
					{
						if ((rand < 0.625))
						{
							self.skin = 4;
						}
						else
						{
							if ((rand < 0.75))
							{
								self.skin = 5;
							}
							else
							{
								if ((rand < 0.875))
								{
									self.skin = 6;
								}
								else
								{
									self.skin = 7;
								}
							}
						}
					}
				}
			}
		}
	}
	setsize(self, VEC_HULL_MIN, '16 16 16');
	if (!self.health)
	{
		self.health = autocvar_spider_health;
	}
	self.health_initial = self.health;
	self.colormod = '1 1 1';
	self.painskin_helper = 2;
	self.th_stand = spider_stand_random;
	self.th_walk = spider_walk1;
	self.th_run = spider_run1;
	self.th_melee = spider_melee_random;
	self.th_missile = spider_ranged;
	self.th_pain = spider_pain;
	self.th_die = spider_die;
	self.alpha = (autocvar_monstertransparency * 0.01);
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
	MonsterPhysics(self, autocvar_spidermass);
};

void() monster_spider_shambler =
{
	local float rand;
	local entity pain_skin_entity;

	self.classname = "monster_spider";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/spider_shambler.mdl");
	self.skin = 0;
	self.monstermodel = 0;
	if (autocvar_spider_random_skin_selection)
	{
		rand = random();
		if ((rand < 0.125))
		{
			self.skin = 0;
		}
		else
		{
			if ((rand < 0.25))
			{
				self.skin = 1;
			}
			else
			{
				if ((rand < 0.375))
				{
					self.skin = 2;
				}
				else
				{
					if ((rand < 0.5))
					{
						self.skin = 3;
					}
					else
					{
						if ((rand < 0.625))
						{
							self.skin = 4;
						}
						else
						{
							if ((rand < 0.75))
							{
								self.skin = 5;
							}
							else
							{
								if ((rand < 0.875))
								{
									self.skin = 6;
								}
								else
								{
									self.skin = 7;
								}
							}
						}
					}
				}
			}
		}
	}
	setsize(self, '-36 -36 -32', '36 36 40');
	self.health = autocvar_shambler_health;
	self.health_initial = self.health;
	self.spider_is_shambler = 1;
	self.colormod = '1 1 1';
	self.th_stand = spider_stand_random;
	self.th_walk = spider_walk1;
	self.th_run = spider_run1;
	self.th_melee = spider_melee_random;
	self.th_missile = spider_ranged;
	self.th_pain = spider_pain;
	self.th_die = spider_die;
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
	self.alpha = (autocvar_monstertransparency * 0.01);
	walkmonster_start();
	do_the_cloning();
	MonsterPhysics(self, 3000);
};

void() monster_spider_start =
{
	local entity clone;

	self.scale = 1;
	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_spider;
	clone.nextthink = (time + 0.000100);
};

void() monster_spider_shambler_start =
{
	local entity clone;

	self.scale = 1;
	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_spider_shambler;
	clone.nextthink = (time + 0.000100);
};

void() vengeance_spider_end1 =
{
	self.alpha = -1;
	self.touch = SUB_Null;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_spider_touch =
{
	local float ldmg;

	ldmg = rint((1.5 + (3 * random())));
	if ((((self.alpha > 0.1) && (vlen((self.enemy.origin - self.origin)) < 75)) && (autocvar_quadreplacer > 0)))
	{
		T_Damage(other, self, self, ldmg);
	}
	self.touch = SUB_Null;
	self.think = vengeance_spider_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_spider_run1 = [ 24, vengeance_spider_run2 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.4;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run2 = [ 25, vengeance_spider_run3 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.39;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run3 = [ 26, vengeance_spider_run4 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.38;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run4 = [ 27, vengeance_spider_run5 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.37;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run5 = [ 28, vengeance_spider_run6 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.36;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run6 = [ 29, vengeance_spider_run7 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.35;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run7 = [ 30, vengeance_spider_run8 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.34;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run8 = [ 31, vengeance_spider_run9 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.33;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run9 = [ 32, vengeance_spider_run10 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.32;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run10 = [ 33, vengeance_spider_run11 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.31;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run11 = [ 34, vengeance_spider_run12 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.3;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_run12 = [ 35, vengeance_spider_jump1 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.28;
	self.nextthink = (time + 0.04);
};

void() vengeance_spider_jump1 = [ 256, vengeance_spider_jump2 ]
{
	ai_face();
	self.touch = vengeance_spider_touch;
	self.alpha = 0.24;
	self.nextthink = (time + 0.09);
};

void() vengeance_spider_jump2 = [ 258, vengeance_spider_jump3 ]
{
	sound(self, CHAN_VOICE, "spider/spider_jump.wav", 1, ATTN_NORM);
	ai_face();
	movetogoal(8);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.21;
	self.nextthink = (time + 0.09);
};

void() vengeance_spider_jump3 = [ 260, vengeance_spider_jump4 ]
{
	ai_face();
	movetogoal(12);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.18;
	self.nextthink = (time + 0.09);
};

void() vengeance_spider_jump4 = [ 262, vengeance_spider_jump5 ]
{
	ai_face();
	movetogoal(20);
	self.touch = vengeance_spider_touch;
	self.alpha = 0.15;
	self.nextthink = (time + 0.09);
};

void() vengeance_spider_jump5 = [ 264, vengeance_spider_jump6 ]
{
	ai_face();
	self.touch = vengeance_spider_touch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 2);
	self.velocity = ((v_forward * 650) + '0 0 225');
	if (((self.enemy.origin_z - self.origin_z) > 48))
	{
		self.velocity_z = (self.velocity_z + 50);
	}
	else
	{
		if (((self.enemy.origin_z - self.origin_z) < -48))
		{
			self.velocity_z = (self.velocity_z - 50);
		}
	}
	self.alpha = 0.13;
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
	self.nextthink = (time + 0.7);
};

void() vengeance_spider_jump6 = [ 265, vengeance_spider_end1 ]
{
	self.touch = SUB_Null;
	self.alpha = 0.1;
	self.nextthink = (time + 0.09);
};

void() vengeance_spider1 = [ 399, vengeance_spider2 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.05);
};

void() vengeance_spider2 = [ 398, vengeance_spider3 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider3 = [ 397, vengeance_spider4 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider4 = [ 396, vengeance_spider5 ]
{
	sound(self, CHAN_WEAPON, "spider/spider_sight.wav", 1, ATTN_NORM);
	self.nextthink = (time + 0.05);
};

void() vengeance_spider5 = [ 395, vengeance_spider6 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider6 = [ 394, vengeance_spider7 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider7 = [ 393, vengeance_spider8 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider8 = [ 392, vengeance_spider9 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider9 = [ 391, vengeance_spider10 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider10 = [ 390, vengeance_spider11 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider11 = [ 389, vengeance_spider12 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider12 = [ 388, vengeance_spider13 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider13 = [ 387, vengeance_spider14 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider14 = [ 386, vengeance_spider15 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider15 = [ 385, vengeance_spider16 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider16 = [ 384, vengeance_spider17 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider17 = [ 383, vengeance_spider18 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider18 = [ 382, vengeance_spider_run1 ]
{
	self.nextthink = (time + 0.05);
};

void() vengeance_spider_bright05 =
{
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	self.think = vengeance_spider1;
};

void() vengeance_spider_bright04 =
{
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_spider_bright05;
};

void() vengeance_spider_bright03 =
{
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_spider_bright04;
};

void() vengeance_spider_bright02 =
{
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_spider_bright03;
};

void() vengeance_spider_bright01 =
{
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_spider_bright02;
};

void() vengeance_spider_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_spider_bright01;
};

void(string modelname, float modelframe) vengeance_spider =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_STEP;
	if (self.spider_is_shambler)
	{
		setmodel(self, "progs/spider_shambler.mdl");
		setsize(self, '-32 -32 -32', '32 32 40');
	}
	else
	{
		setmodel(self, "progs/spider.mdl");
		setsize(self, VEC_HULL_MIN, '16 16 16');
	}
	self.frame = modelframe;
	self.solid = 0;
	MonsterPhysics(self, autocvar_spidermass);
	vengeance_spider_bright00();
};
