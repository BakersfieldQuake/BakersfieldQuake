//Decompiled code. Please respect the original copyright.

void() shal_spawner =
{
	local vector distancedelta;
	local vector nozdistancedelta;
	local entity missile;

	self.effects = (self.effects | EF_MUZZLEFLASH);
	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	makevectors(self.angles);
	sound7(self, CHAN_WEAPON, "shalrath/firesum.wav", 1, ATTN_NORM, SNDSPD);
	distancedelta = self.enemy.origin - self.origin;
	nozdistancedelta = distancedelta;
	missile.velocity = normalize(distancedelta);
	missile.velocity = ((missile.velocity * 150) + (v_right * (random() * 90)));
	missile.velocity_z = ((missile.velocity_z + 50) + ((vlen(nozdistancedelta) * 0.22) * (1 + (0.3 * random()))));
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.nextthink = (time + 2.5);
	missile.think = ShalBossSpawnTouch;
	setmodel(missile, "progs/proj_shalshell.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.scale = 3;
	setorigin(missile, self.origin);
};

float() shal_checkroof =
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
	if ((num < (autocvar_shalrath_free_space_limit_for_jumping + 20)))
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

float() shal_clearance =
{
	local vector end;
	local vector end1;
	local vector end2;
	local float end_true;
	local float end1_true;
	local float end2_true;

	makevectors(self.angles);
	end = self.origin;
	end1 = self.origin + (v_forward * 33);
	end2 = self.origin + (v_forward * -33);
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

float() shal_nosky =
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

void() shal_updie = [ 16, shal_updie2 ]
{
	self.movetype = MOVETYPE_STEP;
	if ((self.health < -90))
	{
		shalrath_die();
		return;
	}
	self.angles_z = 150;
	sound7(self, CHAN_VOICE, "shalrath/death.wav", 1, ATTN_NORM, SNDSPD);
	self.solid = 0;
};

void() shal_updie2 = [ 17, shal_updie3 ]
{
	ai_face();
	self.angles_z = 120;
};

void() shal_updie3 = [ 18, shal_updie4 ]
{
	ai_face();
	self.angles_z = 90;
};

void() shal_updie4 = [ 19, shal_updie5 ]
{
	ai_face();
	self.angles_z = 60;
};

void() shal_updie5 = [ 20, shal_updie6 ]
{
	ai_face();
	self.angles_z = 30;
};

void() shal_updie6 = [ 21, shal_updie7 ]
{
	ai_face();
	self.angles_z = 0;
};

void() shal_updie7 = [ 22, shal_updie7 ]
{
	self.angles_z = 0;
	shal_death7();
	return;
};

void() shal_uppain =
{
	if ((self.pain_finished > time))
	{
		return;
	}
	if (autocvar_shalrath_pain_drop_down_from_ceiling)
	{
		if ((((self.enemy.weapon == IT_GRENADE_LAUNCHER) || (self.enemy.weapon == IT_ROCKET_LAUNCHER)) || (self.enemy.weapon == IT_LIGHTNING)))
		{
			shal_flipdown();
		}
	}
	else
	{
		shal_flipdown();
	}
	sound7(self, CHAN_VOICE, "shalrath/pain.wav", 1, ATTN_NORM, SNDSPD);
	self.pain_finished = (time + 1.5);
};

void() shal_reaching =
{
	if ((self.nojump == -1))
	{
		self.th_stand = shal_flipdown;
		self.th_walk = shal_flipdown;
		self.th_pain = shal_uppain;
		self.th_run = shal_upatt;
		if ((self.th_missile != shal_spawn1))
		{
			self.th_missile = shal_upatt;
		}
		self.th_die = shal_updie;
		shal_upatt();
		return;
	}
	if ((self.velocity_z < 100))
	{
		shal_flipdown();
		return;
	}
	self.think = shal_reaching;
	self.nextthink = (time + 0.1);
	ai_face();
};

void() shal_reaching_map_start =
{
	if ((self.nojump == -1))
	{
		self.th_stand = shal_stand_ceiling_map_start;
		self.th_walk = shal_flipdown;
		self.th_pain = shal_uppain;
		self.th_run = shal_upatt;
		if ((self.th_missile != shal_spawn1))
		{
			self.th_missile = shal_upatt;
		}
		self.th_die = shal_updie;
		shal_stand_ceiling_map_start();
		return;
	}
	if ((self.velocity_z < 100))
	{
		shal_flipdown();
		return;
	}
	self.think = shal_reaching_map_start;
	self.nextthink = (time + 0.1);
};

void() shal_flipdown2 =
{
	if ((self.angles_z <= 0))
	{
		if ((self.enemy != world))
		{
			self.angles_z = 0;
			shal_run1();
			return;
		}
		else
		{
			self.angles_z = 0;
			shal_stand();
			return;
		}
	}
	self.angles_z = (self.angles_z - 30);
	self.think = shal_flipdown2;
	self.nextthink = (time + 0.1);
};

void() shal_flipdown =
{
	self.shalrath_just_jumped_or_dropped = ((time + 3) + (random() * 2));
	self.th_stand = shal_stand;
	self.th_walk = shal_walk1;
	self.th_run = shal_run1;
	self.th_die = shalrath_die;
	self.th_pain = shalrath_pain;
	if ((self.th_missile != shal_spawn1))
	{
		self.th_missile = shal_attack1;
	}
	self.think = shal_flipdown2;
	self.nextthink = (time + 0.03);
};

void() shal_flipup =
{
	if ((self.angles_z >= 180))
	{
		self.angles_z = 180;
		shal_reaching();
		return;
	}
	self.think = shal_flipup;
	self.nextthink = (time + 0.1);
	self.angles_z = (self.angles_z + 30);
	ai_face();
	self.velocity_z = 666;
	if ((self.angles_z == 90))
	{
		sound7(self, CHAN_VOICE, "shalrath/attack.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() shal_flipup_map_start =
{
	if ((self.angles_z >= 180))
	{
		self.angles_z = 180;
		shal_reaching_map_start();
		return;
	}
	self.think = shal_flipup_map_start;
	self.nextthink = (time + 0.1);
	self.angles_z = (self.angles_z + 30);
	self.velocity_z = 666;
};

void() shal_grabroof =
{
	if ((other.takedamage || other.health))
	{
		return;
	}
	self.nojump = -1;
	self.touch = SUB_Null;
	self.velocity = VEC_ORIGIN;
};

void() shal_upidle =
{
	if ((((self.shalrath_residence_time < time) || (random() < 0.01)) && (self.shalrath_residence == 1)))
	{
		self.shalrath_residence = 0;
		shal_flipdown();
		return;
	}
	if (self.enemy)
	{
		if (visible(self.enemy))
		{
			self.shalrath_residence = 0;
			shal_upatt();
			return;
		}
		else
		{
			if ((self.shalrath_residence == 0))
			{
				self.shalrath_residence_time = (time + autocvar_shalrath_hanging_no_enemy_in_sight_time);
				self.shalrath_residence = 1;
			}
		}
	}
	else
	{
		ai_stand();
	}
	if (shal_nosky())
	{
		self.shalrath_residence = 0;
		shal_flipdown();
		return;
	}
	self.frame = 23;
	self.think = shal_upidle;
	self.nextthink = (time + 0.02);
	if ((self.flags & FL_ONGROUND))
	{
		self.origin_z = (self.origin_z + 1);
		self.flags = (self.flags - FL_ONGROUND);
	}
	self.velocity_x = 0;
	self.velocity_y = 0;
	self.velocity_z = 500;
	if ((self.th_stand != shal_flipdown))
	{
		self.th_stand = shal_flipdown;
		self.th_walk = shal_flipdown;
	}
};

void() shal_stand_ceiling_map_start = [ 23, shal_stand_ceiling_map_start ]
{
	ai_stand();
	self.nextthink = (time + 0.02);
	if (shal_nosky())
	{
		shal_flipdown();
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

void() shal_upatt =
{
	self.speed_reducer = (self.speed_reducer + 1);
	if (((self.walkframe >= 10) && (self.speed_reducer == 4)))
	{
		self.walkframe = 0;
	}
	if (((self.enemy.health < 1) && (self.speed_reducer == 4)))
	{
		self.enemy = world;
		self.th_stand();
		return;
	}
	if ((!visible(self.enemy) && (self.speed_reducer == 4)))
	{
		self.frame = 23;
		shal_upidle();
		return;
	}
	shal_nosky();
	if ((shal_nosky() && (self.speed_reducer == 4)))
	{
		shal_flipdown();
		return;
	}
	self.think = shal_upatt;
	self.nextthink = (time + 0.02);
	if ((self.speed_reducer == 4))
	{
		self.frame = self.walkframe;
		self.walkframe = (self.walkframe + 1);
		ai_face();
	}
	self.velocity_x = 0;
	self.velocity_y = 0;
	self.velocity_z = 500;
	if (((self.enemy == world) && (self.speed_reducer >= 4)))
	{
		shal_flipdown();
		return;
	}
	visible(self.enemy);
	if ((visible(self.enemy) && (self.speed_reducer == 4)))
	{
		if ((self.walkframe == 4))
		{
			sound7(self, CHAN_VOICE, "shalrath/attack.wav", 1, ATTN_NORM, SNDSPD);
		}
		if ((self.walkframe == 8))
		{
			ShalMissile();
		}
	}
	if ((self.speed_reducer > 4))
	{
		self.speed_reducer = 0;
	}
};

void() shal_jump =
{
	if ((self.walkframe >= 10))
	{
		self.walkframe = 0;
		if (visible(self.enemy))
		{
			shal_attack1();
			return;
		}
		shal_run1();
		return;
	}
	self.think = shal_jump;
	self.nextthink = (time + 0.1);
	self.frame = self.walkframe;
	self.walkframe = (self.walkframe + 1);
	ai_face();
	if ((self.walkframe == 4))
	{
		sound7(self, CHAN_VOICE, "shalrath/attack.wav", 1, ATTN_NORM, SNDSPD);
	}
	if ((self.walkframe == 8))
	{
		ShalMissile();
	}
};

void() shal_bounce = [ 9, shal_bounce1 ]
{
	ai_face();
};

void() shal_bounce1 = [ 9, shal_bounce2 ]
{
	ai_face();
};

void() shal_bounce2 = [ 10, shal_bounce3 ]
{
	ai_face();
};

void() shal_bounce3 = [ 15, shal_bounce4 ]
{
	ai_face();
};

void() shal_bounce4 = [ 14, shal_jump ]
{
	local float shalrath_hanging;

	ai_face();
	self.walkframe = 0;
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
		self.origin_z = (self.origin_z + 1);
		self.velocity_z = 666;
	}
	shalrath_hanging = autocvar_shalrath_hanging_on_ceiling_chance * 0.01;
	if (((random() < shalrath_hanging) && (skill >= 2)))
	{
		if (shal_checkroof())
		{
			self.frame = 16;
			self.touch = shal_grabroof;
			self.origin_z = (self.origin_z + 1);
			self.angles_z = 0;
			shal_flipup();
			return;
		}
	}
};

void(float loudness) shalrath_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.5))
		{
			sound7(self, CHAN_AUTO, "walk/shalrath1.wav", loudness, ATTN_IDLE, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_AUTO, "walk/shalrath2.wav", loudness, ATTN_IDLE, SNDSPD);
		}
	}
};

void() shal_stand = [ 23, shal_stand ]
{
	local float shalrath_map_start_ceiling;

	ai_stand();
	shalrath_map_start_ceiling = autocvar_shalrath_hanging_on_ceiling_on_map_start_chance * 0.01;
	if ((((((!self.shalrath_checked_ceiling_at_map_start && !self.afrit_supports_me) && (self.shalrath_jumped_ceiling_at_map_start == 0)) && autocvar_shalrath_hanging_on_ceiling_chance) && (random() < shalrath_map_start_ceiling)) || (self.spawnflags & SPAWN_CEILING_SHAL)))
	{
		if (shal_clearance())
		{
			if (shal_checkroof())
			{
				if ((self.flags & FL_ONGROUND))
				{
					self.flags = (self.flags - FL_ONGROUND);
					self.origin_z = (self.origin_z + 2);
					self.velocity_z = 666;
				}
				self.shalrath_jumped_ceiling_at_map_start = 1;
				self.frame = 16;
				self.touch = shal_grabroof;
				self.origin_z = (self.origin_z + 1);
				self.angles_z = 0;
				shal_flipup_map_start();
				return;
			}
		}
	}
	self.shalrath_checked_ceiling_at_map_start = 1;
};

void() shal_walk1 = [ 24, shal_walk2 ]
{
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "shalrath/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	ai_walk(6);
};

void() shal_walk2 = [ 25, shal_walk3 ]
{
	ai_walk(4);
};

void() shal_walk3 = [ 26, shal_walk4 ]
{
	ai_walk(0);
	shalrath_footsteps(1);
};

void() shal_walk4 = [ 27, shal_walk5 ]
{
	ai_walk(0);
};

void() shal_walk5 = [ 28, shal_walk6 ]
{
	ai_walk(0);
};

void() shal_walk6 = [ 29, shal_walk7 ]
{
	ai_walk(0);
};

void() shal_walk7 = [ 30, shal_walk8 ]
{
	ai_walk(5);
};

void() shal_walk8 = [ 31, shal_walk9 ]
{
	ai_walk(6);
};

void() shal_walk9 = [ 32, shal_walk10 ]
{
	ai_walk(5);
	shalrath_footsteps(1);
};

void() shal_walk10 = [ 33, shal_walk11 ]
{
	ai_walk(0);
};

void() shal_walk11 = [ 34, shal_walk12 ]
{
	ai_walk(4);
};

void() shal_walk12 = [ 23, shal_walk1 ]
{
	ai_walk(5);
};

void() shal_run1 = [ 24, shal_run2 ]
{
	local float shalrath_jumping;

	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	self.angles_z = 0;
	shalrath_jumping = autocvar_shalrath_jumping_chance * 0.01;
	if (((visible(self.enemy) && (random() < shalrath_jumping)) && (self.shalrath_just_jumped_or_dropped < time)))
	{
		self.shalrath_just_jumped_or_dropped = ((time + 2) + random());
		if ((self.nojump < 1))
		{
			if (shal_clearance())
			{
				shal_bounce();
				return;
			}
		}
	}
	ai_run(6);
};

void() shal_run2 = [ 25, shal_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "shalrath/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	ai_run(4);
};

void() shal_run3 = [ 26, shal_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(0);
	shalrath_footsteps(1);
};

void() shal_run4 = [ 27, shal_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(0);
};

void() shal_run5 = [ 28, shal_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(0);
};

void() shal_run6 = [ 29, shal_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(0);
};

void() shal_run7 = [ 30, shal_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(5);
};

void() shal_run8 = [ 31, shal_run9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(6);
};

void() shal_run9 = [ 32, shal_run10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(5);
	shalrath_footsteps(1);
};

void() shal_run10 = [ 33, shal_run11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(0);
};

void() shal_run11 = [ 34, shal_run12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(4);
};

void() shal_run12 = [ 23, shal_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(5);
};

void() shal_run_frantically1 = [ 24, shal_run_frantically2 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((8 + (skill * 0.2)));
};

void() shal_run_frantically2 = [ 25, shal_run_frantically3 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((6 + (skill * 0.2)));
};

void() shal_run_frantically3 = [ 26, shal_run_frantically4 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((2 + (skill * 0.1)));
	shalrath_footsteps(1);
};

void() shal_run_frantically4 = [ 27, shal_run_frantically5 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((1 + (skill * 0.1)));
	if (((self.cnt == 0) || (self.cnt == 3)))
	{
		sound7(self, CHAN_VOICE, "shalrath/pain.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() shal_run_frantically5 = [ 28, shal_run_frantically6 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((1 + (skill * 0.1)));
};

void() shal_run_frantically6 = [ 29, shal_run_frantically7 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((2 + (skill * 0.1)));
};

void() shal_run_frantically7 = [ 30, shal_run_frantically8 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((7 + (skill * 0.2)));
};

void() shal_run_frantically8 = [ 31, shal_run_frantically9 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((8 + (skill * 0.2)));
};

void() shal_run_frantically9 = [ 32, shal_run_frantically10 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((7 + (skill * 0.2)));
	shalrath_footsteps(1);
};

void() shal_run_frantically10 = [ 33, shal_run_frantically11 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((2 + (skill * 0.1)));
};

void() shal_run_frantically11 = [ 34, shal_run_frantically12 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((6 + (skill * 0.2)));
};

void() shal_run_frantically12 = [ 23, shal_run_frantically1 ]
{
	self.nextthink = (time + 0.03);
	movetogoal((7 + (skill * 0.2)));
	self.cnt = (self.cnt + 1);
	if (((vlen((self.origin - self.enemy.origin)) < 300) || (self.cnt >= 5)))
	{
		self.cnt = 0;
		shal_run1();
		return;
	}
};

void() shal_attack1 = [ 0, shal_attack2 ]
{
	local float shalrath_running_frantically;

	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	shalrath_running_frantically = autocvar_shalrath_runs_frantically_towards_player * 0.01;
	if (((random() < shalrath_running_frantically) && (vlen((self.origin - self.enemy.origin)) > 377)))
	{
		shal_run_frantically1();
		return;
	}
	sound7(self, CHAN_VOICE, "shalrath/attack.wav", 1, ATTN_NORM, SNDSPD);
	ai_face();
};

void() shal_attack2 = [ 1, shal_attack3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_attack3 = [ 2, shal_attack4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_attack4 = [ 3, shal_attack5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_attack5 = [ 4, shal_attack6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_attack6 = [ 5, shal_attack7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_attack7 = [ 6, shal_attack8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_attack8 = [ 7, shal_attack9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_attack9 = [ 8, shal_attack10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ShalMissile();
};

void() shal_attack10 = [ 9, shal_attack11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_attack11 = [ 10, shal_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() shal_spawn1 = [ 0, shal_spawn2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_spawn2 = [ 1, shal_spawn3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_spawn3 = [ 2, shal_spawn4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_spawn4 = [ 3, shal_spawn5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_spawn5 = [ 4, shal_spawn6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_spawn6 = [ 5, shal_spawn7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_spawn7 = [ 6, shal_spawn8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_spawn8 = [ 7, shal_spawn9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_spawn9 = [ 8, shal_spawn10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	shal_spawner();
};

void() shal_spawn10 = [ 9, shal_spawn11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() shal_spawn11 = [ 10, shal_run1 ]
{
	self.nextthink = ((time + 0.3) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() shal_pain1 = [ 11, shal_pain2 ]
{
};

void() shal_pain2 = [ 12, shal_pain3 ]
{
};

void() shal_pain3 = [ 13, shal_pain4 ]
{
};

void() shal_pain4 = [ 14, shal_pain5 ]
{
};

void() shal_pain5 = [ 15, shal_run1 ]
{
};

void() shal_dieburn1 = [ 16, shal_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
};

void() shal_dieburn2 = [ 17, shal_dieburn3 ]
{
	self.burnz_origin = 10;
};

void() shal_dieburn3 = [ 18, shal_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
};

void() shal_dieburn4 = [ 19, shal_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() shal_dieburn5 = [ 20, shal_dieburn6 ]
{
	self.burnz_origin = -1;
};

void() shal_dieburn6 = [ 21, shal_dieburn7 ]
{
	self.burnz_origin = -3;
};

void() shal_dieburn7 = [ 22, shal_dieburn7 ]
{
	self.burnz_origin = -7;
};

void() shal_death1 = [ 16, shal_death2 ]
{
	self.angles_z = 0;
};

void() shal_death2 = [ 17, shal_death3 ]
{
};

void() shal_death3 = [ 18, shal_death4 ]
{
};

void() shal_death4 = [ 19, shal_death5 ]
{
};

void() shal_death5 = [ 20, shal_death6 ]
{
};

void() shal_death6 = [ 21, shal_death7 ]
{
};

void() shal_death7 = [ 22, shal_death7 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 30;
	if ((autocvar_shalrathcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_shalrathcorpsehealth, "progs/h_shal.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_shalrathcorpsehealth, "progs/h_shal1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_shalrathrandomness = autocvar_shalrathrandomness * 0.01;
		if ((autocvar_shalrath == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_shalrathrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_shalrath == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_shalrathrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/shalrath.mdl", 22, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/shalrath1.mdl", 22, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_shalrath == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_shalrathrandomness))
					{
						vengeance_shalrath("progs/shalrath.mdl", 22);
					}
				}
				else
				{
					if ((autocvar_shalrath == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_shalrathrandomness))
						{
							zufall = random();
							if ((zufall > 0.85))
							{
								self.think = ghost_die;
								self.nextthink = (time + 0.8);
							}
							else
							{
								if ((zufall < 0.2))
								{
									if ((self.monstermodel == 0))
									{
										soul("progs/shalrath.mdl", 22, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/shalrath1.mdl", 22, zet);
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
			if ((self.velocity != VEC_ORIGIN))
			{
				return;
			}
			zufall = random();
			if ((zufall > 0.85))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.15))
				{
					if ((zufall < 0.005))
					{
						soul("progs/afrit.mdl", 64, 27.451);
					}
					else
					{
						if ((self.monstermodel == 0))
						{
							soul("progs/shalrath.mdl", 22, zet);
						}
						else
						{
							if ((self.monstermodel == 1))
							{
								soul("progs/shalrath1.mdl", 22, zet);
							}
						}
					}
				}
				else
				{
					vengeance_shalrath("progs/shalrath.mdl", 22);
				}
			}
		}
	}
};

void() shalrath_pain =
{
	if ((self.pain_finished > time))
	{
		return;
	}
	if ((((self.health <= 180) && (((self.enemy.weapon != IT_AXE) || (self.enemy.weapon != IT_ROCKET_LAUNCHER)) || (self.enemy.weapon != IT_GRENADE_LAUNCHER))) && (self.enemy.meleeing == 0)))
	{
		self.skin = 1;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_shalrath * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "shalrath/pain.wav", 1, ATTN_NORM, SNDSPD);
	shal_pain1();
	self.pain_finished = (time + 3);
};

void(float maxgibs, float gibscounter) producegibs_shalrath =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/gib_shalleg.mdl", self.health);
		ThrowGib("progs/gib_shalleg.mdl", self.health);
		ThrowGib("progs/gib_shalleg.mdl", self.health);
		ThrowGib("progs/gib_shalclaw.mdl", self.health);
		ThrowGib("progs/gib_shalclaw.mdl", self.health);
		ThrowGib("progs/gib_4.mdl", self.health);
		ThrowGib("progs/gib_5.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_shalrath(maxgibs, gibscounter);
};

void() shalrath_lightning_death = [ 7, shalrath_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() shalrath_lightning_death1 = [ 7, shalrath_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(1, "progs/h_shal.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(1, "progs/h_shal1.mdl");
	}
};

void() shal_inflamed1 = [ 24, shal_inflamed2 ]
{
	ai_run_inflamed(8);
	self.nextthink = (time + 0.06);
	if ((random() < 0.75))
	{
		sound7(self, CHAN_VOICE, "shalrath/pain.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() shal_inflamed2 = [ 25, shal_inflamed3 ]
{
	ai_run_inflamed(6);
	self.nextthink = (time + 0.06);
};

void() shal_inflamed3 = [ 26, shal_inflamed4 ]
{
	ai_run_inflamed(1);
	shalrath_footsteps(1);
	self.nextthink = (time + 0.06);
};

void() shal_inflamed4 = [ 27, shal_inflamed5 ]
{
	ai_run_inflamed(1);
	self.nextthink = (time + 0.06);
};

void() shal_inflamed5 = [ 28, shal_inflamed6 ]
{
	ai_run_inflamed(1);
	self.nextthink = (time + 0.06);
};

void() shal_inflamed6 = [ 29, shal_inflamed7 ]
{
	ai_run_inflamed(1);
	self.nextthink = (time + 0.06);
};

void() shal_inflamed7 = [ 30, shal_inflamed8 ]
{
	ai_run_inflamed(7);
	self.nextthink = (time + 0.06);
};

void() shal_inflamed8 = [ 31, shal_inflamed9 ]
{
	ai_run_inflamed(8);
	self.nextthink = (time + 0.06);
};

void() shal_inflamed9 = [ 32, shal_inflamed10 ]
{
	ai_run_inflamed(7);
	shalrath_footsteps(1);
	self.nextthink = (time + 0.06);
};

void() shal_inflamed10 = [ 33, shal_inflamed11 ]
{
	ai_run_inflamed(1);
	self.nextthink = (time + 0.06);
};

void() shal_inflamed11 = [ 34, shal_inflamed12 ]
{
	ai_run_inflamed(6);
	self.nextthink = (time + 0.06);
	if ((self.inflametime < time))
	{
		shalrath_die();
		return;
	}
	if ((random() < 0.65))
	{
		shal_inflamed13();
	}
};

void() shal_inflamed12 = [ 23, shal_inflamed1 ]
{
	ai_run_inflamed(5);
	self.nextthink = (time + 0.06);
};

void() shal_inflamed13 = [ 11, shal_inflamed14 ]
{
	self.nextthink = (time + 0.09);
	if ((random() < 0.8))
	{
		sound7(self, CHAN_VOICE, "shalrath/pain.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() shal_inflamed14 = [ 12, shal_inflamed15 ]
{
	self.nextthink = (time + 0.09);
};

void() shal_inflamed15 = [ 13, shal_inflamed16 ]
{
	self.nextthink = (time + 0.09);
};

void() shal_inflamed16 = [ 14, shal_inflamed17 ]
{
	self.nextthink = (time + 0.09);
};

void() shal_inflamed17 = [ 15, shal_inflamed12 ]
{
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		shalrath_die();
		return;
	}
};

void() shalrath_die =
{
	local float maxgibs;
	local float gibscounter;
	local float zufa;
	local float zufall;
	local float randomness;

	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			shalrath_lightning_death();
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
	if ((self.health < -70))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_shalrath * 0.01)))
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
		self.angles_z = 0;
		if ((self.monstermodel == 0))
		{
			ThrowHead("progs/h_shal.mdl", self.health);
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				ThrowHead("progs/h_shal1.mdl", self.health);
			}
		}
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		if ((autocvar_bloodextension == 1))
		{
			pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
		}
		producegibs_shalrath(maxgibs, gibscounter);
		return;
	}
	if (autocvar_burning_monsters_death_animation)
	{
		if ((self.inflamed == 0))
		{
			zufa = random() * 100;
			if ((((((self.enemy.weapon == IT_GRENADE_LAUNCHER) || (self.enemy.weapon == IT_ROCKET_LAUNCHER)) && (zufa <= autocvar_burning_monsters_death_animation)) && (self.watertype != CONTENT_WATER)) && (self.enemy.meleeing == 0)))
			{
				self.delete_painskin = 1;
				self.inflamed = 1;
				self.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
				self.inflametime = ((time + autocvar_burning_monsters_death_animation_time) + random());
				shal_inflamed1();
				return;
			}
		}
		else
		{
			sound7(self, CHAN_VOICE, "shalrath/death.wav", 1, ATTN_NORM, SNDSPD);
			shal_death1();
			self.solid = 0;
			return;
		}
	}
	autocvar_shalrathrandomness = autocvar_shalrathrandomness * 0.01;
	if ((autocvar_shalrath == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_shalrathrandomness))
		{
			self.delete_painskin = 1;
			shal_dieburn1();
			return;
		}
	}
	if ((autocvar_shalrath == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_shalrathrandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				shal_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_shalrath * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "shalrath/death.wav", 1, ATTN_NORM, SNDSPD);
	shal_death1();
	self.solid = 0;
	if ((self.enemy.meleeing == 0))
	{
		if ((self.enemy.weapon == IT_SUPER_SHOTGUN))
		{
			if ((random() < 0.4))
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
					self.model = "progs/shalrath_dmg.mdl";
					setmodel(self, "progs/shalrath_dmg.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/shalrath_dmg.mdl";
					setmodel(self, "progs/shalrath_dmg.mdl");
					self.skin = 1;
				}
				shal_death1();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
			}
			else
			{
				if ((((random() < 0.65) && (self.health < -33)) && (vlen((self.enemy.origin - self.origin)) < 320)))
				{
					self.health = -71;
					shalrath_die();
				}
			}
		}
		if ((self.enemy.weapon == IT_SUPER_NAILGUN))
		{
			if ((random() < 0.4))
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
					self.model = "progs/shalrath_dmg.mdl";
					setmodel(self, "progs/shalrath_dmg.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/shalrath_dmg.mdl";
					setmodel(self, "progs/shalrath_dmg.mdl");
					self.skin = 1;
				}
				shal_death1();
				sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_NORM, SNDSPD);
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
			}
			else
			{
				if ((random() < 0.5))
				{
					self.health = -71;
					shalrath_die();
				}
			}
		}
	}
};

void() shalrath_homing_teleport =
{
	local vector spot;
	local vector vec;

	spot = self.origin + (randomvec() * autocvar_shalrath_shootable_missile_teleporting);
	vec = normalize((spot - self.origin));
	traceline(self.origin, spot, TRUE, self);
	spot = trace_endpos - (vec * 13);
	if (PM_InWall(self, spot))
	{
		return;
	}
	if (!PM_TraceCheck(self, spot))
	{
		return;
	}
	traceline(spot, self.enemy.origin, FALSE, self);
	if ((trace_fraction < 1))
	{
		if ((trace_ent != self.enemy))
		{
			return;
		}
	}
	setorigin(self, spot);
};

void() shalrath_homing_pain =
{
	if ((self.pain_finished > time))
	{
		return;
	}
	self.pain_finished = (time + 0.5);
	sound7(self, CHAN_VOICE, "warlord/homing_pain.wav", 1, ATTN_NORM, SNDSPD);
	if (autocvar_shalrath_shootable_missile_teleporting)
	{
		shalrath_homing_teleport();
	}
};

void() shalrath_homing_death =
{
	pointparticles(particleeffectnum(/*57797i*/"voreball_explosion"), self.origin, VEC_ORIGIN, 1);
	sound7(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
	remove(self);
};

void() ShalMissile =
{
	local entity missile;
	local vector dir;
	local float dist;
	local float flytime;

	dir = normalize(((self.enemy.origin + '0 0 10') - self.origin));
	dist = vlen((self.enemy.origin - self.origin));
	flytime = dist * 0.002;
	if ((flytime < 0.1))
	{
		flytime = 0.1;
	}
	self.effects = (self.effects | EF_MUZZLEFLASH);
	sound7(self, CHAN_WEAPON, "shalrath/attack2.wav", 1, ATTN_NORM, SNDSPD);
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	setmodel(missile, "progs/v_spike.mdl");
	if (autocvar_shalrath_shootable_missile)
	{
		setsize(missile, '-8 -8 -8', '8 8 8');
		missile.movetype = MOVETYPE_NOCLIP;
		missile.classname = "ShalrathMissile";
		missile.health = autocvar_shalrath_shootable_missile_health;
		missile.takedamage = DAMAGE_AIM;
		missile.th_pain = shalrath_homing_pain;
		missile.th_die = shalrath_homing_death;
		missile.nextthink = (time + 0.3);
	}
	else
	{
		missile.movetype = MOVETYPE_FLYMISSILE;
		setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
		missile.nextthink = (flytime + time);
	}
	missile.origin = (self.origin + '0 0 10');
	missile.velocity = (dir * 400);
	missile.avelocity = '300 300 300';
	missile.think = ShalHome;
	missile.enemy = self.enemy;
	missile.touch = ShalMissileTouch;
};

void() ShalHome =
{
	local vector dir;
	local vector vtemp;

	vtemp = self.enemy.origin + '0 0 10';
	self.movetype = MOVETYPE_FLYMISSILE;
	if ((self.enemy.health < 1))
	{
		remove(self);
		return;
	}
	if ((self.origin == self.old_origin))
	{
		sound7(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
		pointparticles(particleeffectnum(/*57797i*/"voreball_explosion"), self.origin, VEC_ORIGIN, 1);
		remove(self);
		return;
	}
	self.old_origin = self.origin;
	dir = normalize((vtemp - self.origin));
	if ((skill == 3))
	{
		self.velocity = (dir * 300);
	}
	else
	{
		self.velocity = (dir * 250);
	}
	self.nextthink = (time + 0.2);
	self.think = ShalHome;
};

void() ShalMissileTouch =
{
	if (((other == self.owner) || (other.classname == "monster_voreling")))
	{
		return;
	}
	if (((((other.model == "progs/spike.mdl") || (other.model == "progs/s_spike.mdl")) || (other.model == "progs/grenade.mdl")) || (other.model == "progs/missile.mdl")))
	{
		return;
	}
	if ((other.classname == "monster_zombie"))
	{
		T_Damage(other, self, self, 110);
	}
	if (autocvar_shalrath_shootable_missile)
	{
		if ((autocvar_shalrath_size_influenced_attack == 1))
		{
			T_Damage(other, self, self.owner, ((autocvar_shalrath_missile + -7) * self.owner.scale));
		}
		else
		{
			T_Damage(other, self, self.owner, (autocvar_shalrath_missile + -7));
		}
	}
	else
	{
		if ((autocvar_shalrath_size_influenced_attack == 1))
		{
			T_RadiusDamage(self, self.owner, (autocvar_shalrath_missile * self.owner.scale), world);
		}
		else
		{
			T_RadiusDamage(self, self.owner, autocvar_shalrath_missile, world);
		}
	}
	sound7(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
	pointparticles(particleeffectnum(/*57797i*/"voreball_explosion"), self.origin, VEC_ORIGIN, 1);
	remove(self);
};

void() monster_shalrath =
{
	local float zufall;
	local float zuffa;
	local float replacerr;
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
	precache_model2("progs/shalrath.mdl");
	precache_model2("progs/h_shal.mdl");
	precache_model2("progs/v_spike.mdl");
	precache_model2("progs/proj_shalshell.mdl");
	precachegibs_shal();
	precache_sound2("shalrath/attack.wav");
	precache_sound2("shalrath/attack2.wav");
	precache_sound2("shalrath/death.wav");
	precache_sound2("shalrath/idle.wav");
	precache_sound2("shalrath/pain.wav");
	precache_sound2("shalrath/sight.wav");
	precache_sound("walk/shalrath1.wav");
	precache_sound("walk/shalrath2.wav");
	precache_sound("warlord/homing_pain.wav");
	precache_sound2("shalrath/firesum.wav");
	precache_sound2("misc/summon.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.netname = "monster_shalrath";
	if ((autocvar_shalrathmultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/shalrath.mdl");
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
		if ((autocvar_shalrathmultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/shalrath1.mdl");
			precache_model("progs/h_shal1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/shalrath.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/shalrath1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_shalrathmultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/shalrath1.mdl");
				precache_model("progs/h_shal1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/shalrath.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/shalrath.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/shalrath1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_shalrathmultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/shalrath1.mdl");
					precache_model("progs/h_shal1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/shalrath.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/shalrath.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/shalrath1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/shalrath1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/shalrath.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_shalrath_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.14;
			self.sizediff = '0 0 3';
			setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.07;
				self.sizediff = '0 0 1';
				setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
			}
			else
			{
				self.scale = 1;
				setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			}
		}
	}
	else
	{
		if ((autocvar_shalrath_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.21;
				self.sizediff = '0 0 5';
				setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.14;
					self.sizediff = '0 0 3';
					setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.75))
					{
						self.scale = 1.07;
						self.sizediff = '0 0 1';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
					}
				}
			}
		}
		else
		{
			if ((autocvar_shalrath_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.28;
					self.sizediff = '0 0 7';
					setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.21;
						self.sizediff = '0 0 5';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.14;
							self.sizediff = '0 0 3';
							setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.07;
								self.sizediff = '0 0 1';
								setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
							}
							else
							{
								self.scale = 1;
								setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_shalrath_size == 4))
				{
					zuffa = random();
					if ((zuffa <= 0.17))
					{
						self.scale = 1.35;
						self.sizediff = '0 0 9';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.34))
						{
							self.scale = 1.28;
							self.sizediff = '0 0 7';
							setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.5))
							{
								self.scale = 1.21;
								self.sizediff = '0 0 5';
								setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
							}
							else
							{
								if ((zuffa <= 0.67))
								{
									self.scale = 1.14;
									self.sizediff = '0 0 3';
									setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
								}
								else
								{
									if ((zuffa <= 0.84))
									{
										self.scale = 1.07;
										self.sizediff = '0 0 1';
										setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
									}
									else
									{
										self.scale = 1;
										setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_shalrath_size > 4))
					{
						if ((autocvar_shalrath_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_shalrath_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_shalrath_size * 0.25);
						self.sizediff = self.sizefactor;
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
					}
				}
			}
		}
	}
	if ((autocvar_shalrath_size_influenced_health == 1))
	{
		self.health = (autocvar_shalrath_health * self.scale);
	}
	else
	{
		self.health = autocvar_shalrath_health;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_shalrath_random_skin_colors))
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
	self.th_stand = shal_stand;
	self.th_walk = shal_walk1;
	self.th_run = shal_run1;
	self.th_die = shalrath_die;
	self.th_pain = shalrath_pain;
	if ((((random() > 0.8) && (autocvar_shalrath_mother == 1)) || (self.spawnflags & MINIONS)))
	{
		self.th_missile = shal_spawn1;
	}
	else
	{
		self.th_missile = shal_attack1;
	}
	if ((((autocvar_shalrath_mother == 1) && (self.th_missile == shal_spawn1)) || (self.spawnflags & MINIONS)))
	{
		self.colormod = '1.3 1.7 1';
	}
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_carnivean_replace_shalrath)
	{
		replacerr = autocvar_carnivean_replace_shalrath * 0.01;
		if ((random() <= replacerr))
		{
			self.health = autocvar_shalrath_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_carnivean_start();
			return;
		}
	}
	if (autocvar_yakman_replace_shalrath)
	{
		replacerrr = autocvar_yakman_replace_shalrath * 0.01;
		if ((random() <= replacerrr))
		{
			traceline(self.origin, (self.origin + '0 0 76'), FALSE, self);
			if ((trace_fraction != 1))
			{
			}
			else
			{
				self.health = autocvar_shalrath_health;
				self.scale = 1;
				setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_yakman_start();
				return;
			}
		}
	}
	if (autocvar_spider_replace_shalrath)
	{
		replacer = autocvar_spider_replace_shalrath * 0.01;
		if ((random() <= replacer))
		{
			check = (self.origin - '0 0 20') + '0 0 1';
			if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
			{
				self.skin = 2;
				self.health = autocvar_shalrath_health;
				self.scale = 1;
				setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_spider_start();
				return;
			}
		}
	}
	if (autocvar_reiver_replace_shalrath)
	{
		replacez = autocvar_reiver_replace_shalrath * 0.01;
		if ((random() <= replacez))
		{
			self.health = autocvar_shalrath_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_reiver_liftorigin_start();
			return;
		}
	}
	if (autocvar_afrit_replace_shalrath)
	{
		replac = autocvar_afrit_replace_shalrath * 0.01;
		if ((random() <= replac))
		{
			self.health = autocvar_shalrath_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_afrit_liftorigin_start();
			return;
		}
	}
	if (autocvar_shalrath_hanging_on_ceiling_chance)
	{
		if ((self.sizediff_z == 0))
		{
			setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 35' - self.sizediff));
		}
		if ((self.sizediff_z < 2))
		{
			setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 38' - self.sizediff));
		}
		else
		{
			if ((self.sizediff_z < 4))
			{
				setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 42' - self.sizediff));
			}
			else
			{
				if ((self.sizediff_z < 6))
				{
					setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 46' - self.sizediff));
				}
				else
				{
					if ((self.sizediff_z < 8))
					{
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 50' - self.sizediff));
					}
					else
					{
						if ((self.sizediff_z < 10))
						{
							setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 54' - self.sizediff));
						}
						else
						{
							setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
						}
					}
				}
			}
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
	self.think = walkmonster_start;
	self.nextthink = ((time + 0.1) + (random() * 0.1));
	do_the_cloning();
	if (autocvar_reiver_supports_shalrath)
	{
		replacce = autocvar_reiver_supports_shalrath * 0.01;
		if ((random() <= replacce))
		{
			add_reiver_support_walk();
		}
	}
	if (autocvar_afrit_supports_shalrath)
	{
		replace = autocvar_afrit_supports_shalrath * 0.01;
		if (((cvar("skill") == 3) && (replace > 0)))
		{
			replace = replace + 0.01;
		}
		if (((cvar("quadreplacer") > 0) && (replace > 0)))
		{
			replace = replace + 0.01;
		}
		if ((random() <= replace))
		{
			self.afrit_supports_me = 1;
			add_afrit_support_walk();
		}
	}
	MonsterPhysics(self, autocvar_shalrathmass);
};

void() vengeance_shalrath_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_shalrath_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_shalrath_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath_skull =
{
	local vector offang;
	local vector org;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = ((self.origin + self.mins) + (self.size * 0.5)) + (v_forward * 20);
	launch_vengeance_skull(org);
	newmis.classname = "skull";
	setmodel(newmis, "progs/skull.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	newmis.scale = 0.9;
	precache_sound("vengeance/skull.wav");
	precache_sound("vengeance/skulltouch.wav");
};

void() ShalBossGrenadeExplode2 =
{
	sound7(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
	pointparticles(particleeffectnum(/*57797i*/"voreball_explosion"), self.origin, VEC_ORIGIN, 1);
	T_RadiusDamage(self, self.owner, 39, world);
	self.touch = SUB_Null;
	setmodel(self, "progs/s_explod.spr");
	self.solid = 0;
	s_explode1();
};

void() ShalBossGrenadeTouch2 =
{
	if ((other == self.owner))
	{
		return;
	}
	self.velocity = (self.velocity * 1.3);
	if ((other.classname == "monster_zombie"))
	{
		T_Damage(other, self, self, 110);
	}
	else
	{
		if ((other.takedamage == DAMAGE_AIM))
		{
			ShalBossGrenadeExplode2();
			return;
		}
	}
};

void() shalbossgrenade2 =
{
	local vector distancedelta;
	local vector nozdistancedelta;
	local vector vec;
	local vector dst;
	local vector follow;
	local entity missile;

	makevectors(self.enemy.angles);
	follow = VEC_ORIGIN;
	dst = (self.enemy.origin + follow) - (13 * self.movedir);
	vec = normalize((dst - self.origin));
	self.effects = (self.effects | EF_MUZZLEFLASH);
	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	makevectors(self.angles);
	distancedelta = self.enemy.origin - self.origin;
	nozdistancedelta = distancedelta;
	missile.velocity = normalize(distancedelta);
	missile.velocity = ((vec * 350) + (v_right * (random() * 100)));
	if ((random() < 0.5))
	{
		missile.velocity_x = (missile.velocity_x + (random() * 100));
	}
	else
	{
		missile.velocity_x = (missile.velocity_x - (random() * 100));
	}
	if ((random() < 0.5))
	{
		missile.velocity_y = (missile.velocity_y + (random() * 100));
	}
	else
	{
		missile.velocity_y = (missile.velocity_y - (random() * 100));
	}
	if ((random() < 0.5))
	{
		missile.velocity = (missile.velocity * (0.3 + (random() * 0.35)));
		missile.nextthink = ((time + 2.5) + (random() * 2));
	}
	else
	{
		missile.nextthink = ((time + 2.5) + (random() * 1.5));
	}
	missile.velocity_z = ((vec_x + 220) + ((vlen(nozdistancedelta) * 0.22) * (1 + (0.3 * random()))));
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.touch = ShalBossGrenadeTouch2;
	missile.think = ShalBossGrenadeExplode2;
	setmodel(missile, "progs/v_spike.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.scale = 1.2;
	setorigin(missile, (self.origin + '0 0 60'));
};

void() vengeance_shalrath_blast1 = [ 11, vengeance_shalrath_blast2 ]
{
	ai_face();
	sound7(self, CHAN_WEAPON, "shalrath/attack.wav", 1, ATTN_NORM, (SNDSPD + -10));
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_shalrath_blast2 = [ 12, vengeance_shalrath_blast3 ]
{
	ai_face();
	self.alpha = 0.25;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_shalrath_blast3 = [ 13, vengeance_shalrath_blast4 ]
{
	ai_face();
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_shalrath_blast4 = [ 14, vengeance_shalrath_blast5 ]
{
	ai_face();
	self.alpha = 0.175;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
};

void() vengeance_shalrath_blast5 = [ 15, vengeance_shalrath_end1 ]
{
	ai_face();
	self.alpha = 0.15;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.12);
	self.effects = (self.effects | EF_MUZZLEFLASH);
	sound7(self, CHAN_WEAPON, "shalrath/attack2.wav", 1, ATTN_NORM, SNDSPD);
	shalbossgrenade2();
	shalbossgrenade2();
	shalbossgrenade2();
	shalbossgrenade2();
	shalbossgrenade2();
	shalbossgrenade2();
	shalbossgrenade2();
	shalbossgrenade2();
};

void() vengeance_shalrath_run1 = [ 23, vengeance_shalrath_run2 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_shalrath_run2 = [ 24, vengeance_shalrath_run3 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.35;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_shalrath_run3 = [ 25, vengeance_shalrath_run4 ]
{
	ai_face();
	if ((random() < 0.6))
	{
		self.alpha = 0.35;
		self.glow_color = 75;
		self.glow_size = 600;
		vengeance_shalrath_blast1();
		return;
	}
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_shalrath_run4 = [ 26, vengeance_shalrath_run5 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.25;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_shalrath_run5 = [ 27, vengeance_shalrath_attack1 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_shalrath_attack1 = [ 0, vengeance_shalrath_attack2 ]
{
	sound7(self, CHAN_VOICE, "vengeance/shalthrow.wav", 1, ATTN_NORM, SNDSPD);
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath_attack2 = [ 1, vengeance_shalrath_attack3 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath_attack3 = [ 2, vengeance_shalrath_attack4 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath_attack4 = [ 3, vengeance_shalrath_attack5 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath_attack5 = [ 4, vengeance_shalrath_attack6 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath_attack6 = [ 5, vengeance_shalrath_attack7 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath_attack7 = [ 6, vengeance_shalrath_attack8 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath_attack8 = [ 7, vengeance_shalrath_end1 ]
{
	ai_face();
	self.touch = vengeance_shalrath_touch;
	self.alpha = 0.15;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	vengeance_shalrath_skull();
};

void() vengeance_shalrath1 = [ 21, vengeance_shalrath2 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath2 = [ 20, vengeance_shalrath3 ]
{
	sound7(self, CHAN_WEAPON, "shalrath/sight.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath3 = [ 19, vengeance_shalrath4 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath4 = [ 18, vengeance_shalrath5 ]
{
	ai_face();
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath5 = [ 17, vengeance_shalrath6 ]
{
	ai_face();
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath6 = [ 16, vengeance_shalrath_run1 ]
{
	ai_face();
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shalrath_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	self.think = vengeance_shalrath1;
};

void() vengeance_shalrath_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_shalrath_bright05;
};

void() vengeance_shalrath_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_shalrath_bright04;
};

void() vengeance_shalrath_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_shalrath_bright03;
};

void() vengeance_shalrath_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_shalrath_bright02;
};

void() vengeance_shalrath_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_shalrath_bright01;
};

void(string modelname, float modelframe) vengeance_shalrath =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_STEP;
	self.inflamed = 0;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/shalrath.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/shalrath1.mdl");
		}
	}
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	self.frame = modelframe;
	self.solid = 0;
	vengeance_shalrath_bright00();
};
