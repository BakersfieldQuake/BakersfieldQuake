//Decompiled code. Please respect the original copyright.

void() ghost_followers_pain =
{
	particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
	pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 2'), VEC_ORIGIN, 1);
	particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
	pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin - '0 0 2'), VEC_ORIGIN, 1);
};

void() ghost_followers_death =
{
	particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
	pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 4'), VEC_ORIGIN, 1);
	particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
	pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 2'), VEC_ORIGIN, 1);
	pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), self.origin, VEC_ORIGIN, 1);
	particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
	pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin - '0 0 2'), VEC_ORIGIN, 1);
	particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
	pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin - '0 0 4'), VEC_ORIGIN, 1);
	sound(self, CHAN_WEAPON, "reiver/ghost_follower_death.wav", 1, ATTN_NORM);
	remove(self);
};

void() ghost_follower_touch =
{
	if (other.takedamage)
	{
		if ((self.enemy.classname != "player"))
		{
			T_Damage(other, self, self.owner, autocvar_reiver_ranged_ghost_damage);
			sound(self, CHAN_WEAPON, "reiver/ghost_follower_death.wav", 1, ATTN_NORM);
			remove(self);
			return;
		}
		if ((other.classname != "player"))
		{
			return;
		}
		T_Damage(other, self, self.owner, autocvar_reiver_ranged_ghost_damage);
		sound(self.enemy, CHAN_ITEM, "lostsoul/idle2.wav", 1, ATTN_NORM);
		particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 3'), VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), self.origin, VEC_ORIGIN, 1);
		particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 -3'), VEC_ORIGIN, 1);
		if (autocvar_ghost_follower_psycho_effect)
		{
			ghost_follower_psycho = time + autocvar_ghost_follower_psycho_effect;
		}
		remove(self);
		return;
	}
	else
	{
		return;
	}
};

void() ghost_follower_think =
{
	local vector dir;
	local vector offang;
	local vector vec;
	local float zuffi;
	local float rndsnd;

	if ((self.enemy.health < 1))
	{
		sound(self, CHAN_WEAPON, "reiver/ghost_follower_death.wav", 1, ATTN_NORM);
		remove(self);
	}
	if ((self.maxlifetime < time))
	{
		sound(self, CHAN_WEAPON, "reiver/ghost_follower_death.wav", 1, ATTN_NORM);
		particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 4'), VEC_ORIGIN, 1);
		particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 2'), VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), self.origin, VEC_ORIGIN, 1);
		particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin - '0 0 2'), VEC_ORIGIN, 1);
		particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin - '0 0 4'), VEC_ORIGIN, 1);
		remove(self);
	}
	if ((self.origin == self.old_origin))
	{
		sound(self, CHAN_WEAPON, "reiver/ghost_follower_death.wav", 1, ATTN_NORM);
		particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 3'), VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), self.origin, VEC_ORIGIN, 1);
		particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
		pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 -3'), VEC_ORIGIN, 1);
		T_RadiusDamage(self, self.owner, (autocvar_reiver_ranged_ghost_damage + 15), self.owner);
		remove(self);
	}
	self.old_origin = self.origin;
	self.offsettt_x = (crandom() * 60);
	self.offsettt_y = (crandom() * 60);
	self.offsettt_z = (crandom() * 45);
	if ((vlen(((self.enemy.origin + '0 0 16') - self.origin)) <= 90))
	{
		dir = normalize(((self.enemy.origin + '0 0 16') - self.origin));
		offang = vectoangles(((self.enemy.origin + '0 0 12') - self.origin));
		traceline((self.enemy.origin + '0 0 16'), self.origin, FALSE, self);
		if ((trace_fraction == 1))
		{
			self.movetype = MOVETYPE_FLYMISSILE;
		}
		else
		{
			sound(self, CHAN_WEAPON, "reiver/ghost_follower_death.wav", 1, ATTN_NORM);
			particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
			pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 3'), VEC_ORIGIN, 1);
			pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), self.origin, VEC_ORIGIN, 1);
			particleeffectnum(/*26232i*/"double_shotgun_muzzleflash");
			pointparticles(particleeffectnum(/*26232i*/"double_shotgun_muzzleflash"), (self.origin + '0 0 -3'), VEC_ORIGIN, 1);
			T_Damage(self.enemy, self, self.owner, autocvar_reiver_ranged_ghost_damage);
			remove(self);
		}
	}
	else
	{
		dir = normalize(((self.enemy.origin + '0 0 16') - (self.origin + self.offsettt)));
		offang = vectoangles(((self.enemy.origin + '0 0 12') - (self.origin + self.offsettt)));
	}
	makevectors(offang);
	vec = normalize(v_forward);
	self.angles = vectoangles(vec);
	self.frame = (self.frame + 1);
	if ((self.frame >= 2))
	{
		self.frame = 0;
	}
	zuffi = random();
	if ((zuffi < 0.15))
	{
		self.frame = 2;
	}
	else
	{
		if ((zuffi < 0.3))
		{
			self.frame = 4;
		}
	}
	self.touch = ghost_follower_touch;
	if ((random() < 0.35))
	{
		rndsnd = random();
		if ((rndsnd < 0.3))
		{
			sound(self, CHAN_WEAPON, "lostsoul/idle1.wav", 0.7, ATTN_NORM);
		}
		else
		{
			if ((rndsnd < 0.9))
			{
				sound(self, CHAN_WEAPON, "lostsoul/idle2.wav", 0.7, ATTN_NORM);
			}
			else
			{
				sound(self, CHAN_WEAPON, "lostsoul/charge.wav", 0.7, ATTN_NORM);
			}
		}
	}
	self.velocity = (dir * 200);
	self.nextthink = (time + 0.25);
	self.think = ghost_follower_think;
};

void(vector spawn_pos, vector spawn_vel) launch_ghost_follower =
{
	newmis = spawn();
	newmis.owner = self;
	newmis.enemy = self.enemy;
	newmis.movetype = MOVETYPE_NOCLIP;
	newmis.solid = SOLID_BBOX;
	newmis.velocity = (spawn_vel * 100);
	newmis.velocity = (newmis.velocity * (1 + random()));
	newmis.angles = vectoangles(newmis.velocity);
	newmis.glow_color = 75;
	newmis.glow_size = 666;
	newmis.frame = 0;
	if ((random() < 0.5))
	{
		newmis.alpha = 0.95;
	}
	else
	{
		newmis.alpha = 0.8;
	}
	if ((random() < 0.5))
	{
		newmis.scale = 0.4;
	}
	else
	{
		newmis.scale = 0.51;
	}
	newmis.classname = "ghost_follower";
	newmis.think = ghost_follower_think;
	newmis.nextthink = (time + 0.2);
	newmis.maxlifetime = (time + 7);
	setmodel(newmis, "progs/ghost_follower.spr32");
	setsize(newmis, '-8 -8 -8', '8 8 8');
	newmis.offsettt_x = (crandom() * 10);
	newmis.offsettt_y = (crandom() * 10);
	newmis.offsettt_z = (random() * 3);
	spawn_pos_x = spawn_pos_x + newmis.offsettt_x;
	spawn_pos_y = spawn_pos_y + newmis.offsettt_y;
	spawn_pos_z = spawn_pos_z + newmis.offsettt_z;
	if ((autocvar_reiver_ranged_ghost_health < 1))
	{
		autocvar_reiver_ranged_ghost_health = 7;
	}
	newmis.health = autocvar_reiver_ranged_ghost_health;
	newmis.takedamage = DAMAGE_AIM;
	newmis.th_pain = ghost_followers_pain;
	newmis.th_die = ghost_followers_death;
	setorigin(newmis, spawn_pos);
};

void() ghost_followers =
{
	local vector offang;
	local vector org;
	local vector vec;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = (self.origin + (v_forward * 20)) + (v_up * 2);
	vec = normalize(v_forward);
	launch_ghost_follower(org, vec);
};

void() reiver_fireball_death =
{
	pointparticles(particleeffectnum(/*26544i*/"grenade_explosion_nodebris"), self.origin, VEC_ORIGIN, 1);
	sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.85, ATTN_NORM);
	remove(self);
};

void() reiver_fireball_touch =
{
	if ((other == self.owner))
	{
		return;
	}
	if (((((other.model == "progs/spike.mdl") || (other.model == "progs/s_spike.mdl")) || (other.model == "progs/grenade.mdl")) || (other.model == "progs/missile.mdl")))
	{
		return;
	}
	if ((other.takedamage == DAMAGE_AIM))
	{
		spawn_touchblood(20);
		T_RadiusDamage(self, self.owner, 40, self);
		pointparticles(particleeffectnum(/*52421i*/"torment_hellrod_explosion"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
		sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, ATTN_NORM);
	}
	else
	{
		T_RadiusDamage(self, self.owner, 40, self);
		pointparticles(particleeffectnum(/*26544i*/"grenade_explosion_nodebris"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
		sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.8, ATTN_NORM);
	}
	remove(self);
};

void() reiver_fireball_homing =
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
		T_RadiusDamage(self, self.owner, (autocvar_reiver_ranged_fireball_damage + 10), self.owner);
		sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, ATTN_NORM);
		pointparticles(particleeffectnum(/*26544i*/"grenade_explosion_nodebris"), self.origin, VEC_ORIGIN, 1);
		remove(self);
		return;
	}
	self.old_origin = self.origin;
	dir = normalize((vtemp - self.origin));
	if ((skill == 3))
	{
		self.velocity = (dir * 380);
	}
	else
	{
		self.velocity = (dir * 320);
	}
	self.nextthink = (time + 0.35);
	self.think = reiver_fireball_homing;
};

void() reiver_fireball_no_homing =
{
	self.movetype = MOVETYPE_FLYMISSILE;
	if ((pointcontents(self.origin) == CONTENT_WATER))
	{
		self.traileffectnum = particleeffectnum(/*1i*/"");
	}
	if ((self.enemy.health < 1))
	{
		remove(self);
		return;
	}
	if ((self.maxlifetime < time))
	{
		T_RadiusDamage(self, self.owner, (autocvar_reiver_ranged_fireball_damage + 10), self.owner);
		sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, ATTN_NORM);
		pointparticles(particleeffectnum(/*26544i*/"grenade_explosion_nodebris"), self.origin, VEC_ORIGIN, 1);
		remove(self);
		return;
	}
	if ((self.origin == self.old_origin))
	{
		T_RadiusDamage(self, self.owner, (autocvar_reiver_ranged_fireball_damage + 10), self.owner);
		sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, ATTN_NORM);
		pointparticles(particleeffectnum(/*26544i*/"grenade_explosion_nodebris"), self.origin, VEC_ORIGIN, 1);
		remove(self);
		return;
	}
	self.old_origin = self.origin;
	self.nextthink = (time + 0.2);
	self.think = reiver_fireball_no_homing;
};

void() reiver_fireball =
{
	local entity missile;
	local vector dir;
	local vector org;

	dir = normalize(((self.enemy.origin + '0 0 10') - self.origin));
	sound(self, CHAN_WEAPON, "reiver/reiver_fireball_shoot.wav", 1, ATTN_NORM);
	missile = spawn();
	missile.owner = self;
	missile.enemy = self.enemy;
	missile.scale = 1;
	setmodel(missile, "progs/reiver_fireball.mdl");
	missile.solid = SOLID_BBOX;
	missile.classname = "Reiver_fireball";
	if ((autocvar_reiver_ranged_fireball_health > 0))
	{
		setsize(missile, '-5 -5 -5', '5 5 5');
		missile.movetype = MOVETYPE_NOCLIP;
		missile.health = autocvar_reiver_ranged_fireball_health;
		missile.takedamage = DAMAGE_AIM;
		missile.th_die = reiver_fireball_death;
		missile.nextthink = (time + 0.15);
	}
	else
	{
		if ((skill == 3))
		{
			missile.movetype = MOVETYPE_FLY;
		}
		else
		{
			missile.movetype = MOVETYPE_FLYMISSILE;
		}
		setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
		missile.nextthink = (time + 0.2);
	}
	makevectors(self.angles);
	org = (self.origin + (v_forward * 25)) + (v_up * -1);
	setorigin(missile, org);
	missile.velocity = (dir * 400);
	missile.avelocity = '300 300 300';
	missile.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
	missile.touch = reiver_fireball_touch;
	missile.velocity = (dir * 600);
	missile.maxlifetime = (time + 5);
	missile.think = reiver_fireball_no_homing;
};

void() reiver_look1 = [ 38, reiver_look2 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
	particleeffectnum(/*52689i*/"Reiver_idle");
	pointparticles(particleeffectnum(/*52689i*/"Reiver_idle"), self.origin, (self.velocity * 10), 1);
	sound(self, CHAN_VOICE, "reiver/raith3.wav", 1, ATTN_IDLE);
};

void() reiver_look2 = [ 39, reiver_look3 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look3 = [ 40, reiver_look4 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look4 = [ 41, reiver_look5 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look5 = [ 42, reiver_look6 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look6 = [ 43, reiver_look7 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look7 = [ 44, reiver_look8 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look8 = [ 45, reiver_look9 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look9 = [ 46, reiver_look10 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look10 = [ 47, reiver_look11 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look11 = [ 48, reiver_look12 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look12 = [ 49, reiver_look13 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look13 = [ 50, reiver_look14 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_look14 = [ 51, reiver_idle1 ]
{
	ai_stand();
	self.nextthink = (time + 0.11);
};

void() reiver_idle1 = [ 25, reiver_idle2 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	self.th_stand = reiver_idle1;
};

void() reiver_idle2 = [ 26, reiver_idle3 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle3 = [ 27, reiver_idle4 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle4 = [ 28, reiver_idle5 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle5 = [ 29, reiver_idle6 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle6 = [ 30, reiver_idle7 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle7 = [ 31, reiver_idle8 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle8 = [ 32, reiver_idle9 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle9 = [ 33, reiver_idle10 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle10 = [ 34, reiver_idle11 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle11 = [ 35, reiver_idle12 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle12 = [ 36, reiver_idle13 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
};

void() reiver_idle13 = [ 37, reiver_idle1 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((random() < 0.25))
	{
		reiver_look1();
	}
};

void() reiver_underground1 = [ 1, reiver_underground2 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
	sound(self, CHAN_VOICE, "misc/null.wav", 1, ATTN_NORM);
	sound(self, CHAN_WEAPON, "player/inflame.wav", 1, ATTN_NORM);
	self.alpha = (autocvar_monstertransparency * 0.01);
};

void() reiver_underground2 = [ 2, reiver_underground3 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
};

void() reiver_underground3 = [ 3, reiver_underground4 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
	traceline(self.origin, (self.origin - '0 0 66'), TRUE, self);
	pointparticles(particleeffectnum(/*52701i*/"reiver_outbreak_decal"), trace_endpos, VEC_ORIGIN, 1);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground4 = [ 4, reiver_underground5 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
	self.takedamage = DAMAGE_AIM;
	self.solid = SOLID_SLIDEBOX;
};

void() reiver_underground5 = [ 5, reiver_underground6 ]
{
	ai_stand();
	self.nextthink = (time + 0.09);
	sound(self, CHAN_VOICE, "reiver/sight.wav", 1, ATTN_NORM);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground6 = [ 6, reiver_underground7 ]
{
	ai_stand();
	self.nextthink = (time + 0.09);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground7 = [ 7, reiver_underground8 ]
{
	ai_stand();
	self.nextthink = (time + 0.09);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground8 = [ 8, reiver_underground9 ]
{
	ai_stand();
	self.nextthink = (time + 0.09);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground9 = [ 9, reiver_underground10 ]
{
	ai_stand();
	self.nextthink = (time + 0.09);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground10 = [ 10, reiver_underground11 ]
{
	ai_stand();
	self.nextthink = (time + 0.09);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground11 = [ 11, reiver_underground12 ]
{
	ai_stand();
	self.nextthink = (time + 0.09);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground12 = [ 12, reiver_underground13 ]
{
	ai_stand();
	self.nextthink = (time + 0.09);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground13 = [ 13, reiver_underground14 ]
{
	ai_stand();
	self.nextthink = (time + 0.09);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground14 = [ 14, reiver_underground15 ]
{
	ai_stand();
	self.nextthink = (time + 0.09);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground15 = [ 15, reiver_underground16 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
	pointparticles(particleeffectnum(/*52723i*/"reiver_outbreak"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_underground16 = [ 16, reiver_underground17 ]
{
	ai_stand();
	self.nextthink = (time + 0.08);
};

void() reiver_underground17 = [ 17, reiver_underground18 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	self.origin = (self.origin + '0 0 2');
};

void() reiver_underground18 = [ 18, reiver_underground19 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	self.origin = (self.origin + '0 0 2');
};

void() reiver_underground19 = [ 19, reiver_underground20 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	self.origin = (self.origin + '0 0 2');
};

void() reiver_underground20 = [ 20, reiver_underground21 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	self.origin = (self.origin + '0 0 2');
};

void() reiver_underground21 = [ 21, reiver_underground22 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	self.origin = (self.origin + '0 0 2');
};

void() reiver_underground22 = [ 22, reiver_underground23 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	self.origin = (self.origin + '0 0 2');
};

void() reiver_underground23 = [ 23, reiver_underground24 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() reiver_underground24 = [ 24, reiver_run1 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
	self.meleeing = 0;
	self.th_run = reiver_run1;
	self.th_stand = reiver_idle1;
};

void() reiver_wait_underground = [ 1, reiver_wait_underground ]
{
	ai_stand();
	self.takedamage = 0;
	self.solid = 0;
	self.alpha = -1;
	self.meleeing = 1;
	self.th_run = reiver_underground1;
};

void() reiver_idle_random =
{
	local float hidechance;

	hidechance = autocvar_reiver_hide_underground * 0.01;
	if ((random() < hidechance))
	{
		traceline(self.origin, (self.origin - '0 0 77'), TRUE, self);
		self.origin_z = (0 + 34);
		reiver_wait_underground();
	}
	else
	{
		reiver_idle1();
	}
};

void() reiver_fly1 = [ 25, reiver_fly2 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
	self.th_stand = reiver_idle1;
};

void() reiver_fly2 = [ 26, reiver_fly3 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly3 = [ 27, reiver_fly4 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly4 = [ 28, reiver_fly5 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly5 = [ 29, reiver_fly6 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly6 = [ 30, reiver_fly7 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly7 = [ 31, reiver_fly8 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly8 = [ 32, reiver_fly9 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly9 = [ 33, reiver_fly10 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly10 = [ 34, reiver_fly11 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly11 = [ 35, reiver_fly12 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly12 = [ 36, reiver_fly13 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	particleeffectnum(/*52739i*/"Reiver_fly");
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, (self.velocity * 10), 1);
};

void() reiver_fly13 = [ 37, reiver_fly1 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
	if ((random() < 0.2))
	{
		sound(self, CHAN_VOICE, "reiver/raith3.wav", 1, ATTN_IDLE);
	}
};

void() reiver_run1 = [ 25, reiver_run2 ]
{

	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
	if ((((((self.attack_chance == 0) && !visible(self.enemy)) && (random() < 0.05)) || (self.attack_chance == -1)) || ((pointcontents(self.origin) == CONTENT_SOLID) && (self.attack_chance == 0))))
	{
		if (((self.attack_chance == 0) || (pointcontents(self.origin) != CONTENT_SOLID)))
		{
			self.movetype = MOVETYPE_NOCLIP;
		}
		self.attack_chance = 1;
	}
	else
	{
		if ((((self.attack_chance > 2) && (pointcontents(self.origin) != CONTENT_SKY)) && (pointcontents(self.origin) != CONTENT_SOLID)))
		{
			self.attack_chance = 0;
			self.movetype = MOVETYPE_STEP;
			if (self.bodyphased)
			{
				self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
				self.colormod = '1 1 1';
				self.alpha = 1;
				self.glow_color = 0;
				self.glow_size = 0;
				self.bodyphased = 0;
				sound(self, CHAN_BODY, "misc/null.wav", 1, ATTN_NORM);
				sound(self, CHAN_WEAPON, "reiver/death.wav", 1, ATTN_NORM, SNDSPD);
				particleeffectnum(/*52177i*/"hydra_toxic_player");
				pointparticles(particleeffectnum(/*52177i*/"hydra_toxic_player"), (self.origin + '0 0 -8'), VEC_ORIGIN, 1);
			}
		}
	}
};

void() reiver_run2 = [ 26, reiver_run3 ]
{
	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_run3 = [ 27, reiver_run4 ]
{
	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_run4 = [ 28, reiver_run5 ]
{
	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_run5 = [ 29, reiver_run6 ]
{

	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
	if ((((((self.attack_chance == 0) && !visible(self.enemy)) && (random() < 0.08)) || (self.attack_chance == -1)) || ((pointcontents(self.origin) == CONTENT_SOLID) && (self.attack_chance == 0))))
	{
		if (((self.attack_chance == 0) || (pointcontents(self.origin) != CONTENT_SOLID)))
		{
			self.movetype = MOVETYPE_NOCLIP;
		}
		self.attack_chance = 1;
	}
	else
	{
		if ((((self.attack_chance > 2) && (pointcontents(self.origin) != CONTENT_SKY)) && (pointcontents(self.origin) != CONTENT_SOLID)))
		{
			self.attack_chance = 0;
			self.movetype = MOVETYPE_STEP;
			if (self.bodyphased)
			{
				self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
				self.colormod = '1 1 1';
				self.alpha = 1;
				self.glow_color = 0;
				self.glow_size = 0;
				self.bodyphased = 0;
				sound(self, CHAN_BODY, "misc/null.wav", 1, ATTN_NORM);
				sound(self, CHAN_WEAPON, "reiver/death.wav", 1, ATTN_NORM, SNDSPD);
				particleeffectnum(/*52177i*/"hydra_toxic_player");
				pointparticles(particleeffectnum(/*52177i*/"hydra_toxic_player"), (self.origin + '0 0 -8'), VEC_ORIGIN, 1);
			}
		}
	}
};

void() reiver_run6 = [ 30, reiver_run7 ]
{
	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_run7 = [ 31, reiver_run8 ]
{
	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_run8 = [ 32, reiver_run9 ]
{
	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_run9 = [ 33, reiver_run10 ]
{

	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
	if ((((((self.attack_chance == 0) && !visible(self.enemy)) && (random() < 0.05)) || (self.attack_chance == -1)) || ((pointcontents(self.origin) == CONTENT_SOLID) && (self.attack_chance == 0))))
	{
		if (((self.attack_chance == 0) || (pointcontents(self.origin) != CONTENT_SOLID)))
		{
			self.movetype = MOVETYPE_NOCLIP;
		}
		self.attack_chance = 1;
	}
	else
	{
		if ((((self.attack_chance > 2) && (pointcontents(self.origin) != CONTENT_SKY)) && (pointcontents(self.origin) != CONTENT_SOLID)))
		{
			self.attack_chance = 0;
			self.movetype = MOVETYPE_STEP;
			if (self.bodyphased)
			{
				self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
				self.colormod = '1 1 1';
				self.alpha = 1;
				self.glow_color = 0;
				self.glow_size = 0;
				self.bodyphased = 0;
				sound(self, CHAN_BODY, "misc/null.wav", 1, ATTN_NORM);
				sound(self, CHAN_WEAPON, "reiver/death.wav", 1, ATTN_NORM, SNDSPD);
				particleeffectnum(/*52177i*/"hydra_toxic_player");
				pointparticles(particleeffectnum(/*52177i*/"hydra_toxic_player"), (self.origin + '0 0 -8'), VEC_ORIGIN, 1);
			}
		}
	}
};

void() reiver_run10 = [ 34, reiver_run11 ]
{
	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_run11 = [ 35, reiver_run12 ]
{
	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_run12 = [ 36, reiver_run13 ]
{
	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
};

void() reiver_run13 = [ 37, reiver_run1 ]
{
	ai_run(((skill * 0.5) + 5.5));
	self.nextthink = (time + 0.07);
	pointparticles(particleeffectnum(/*52739i*/"Reiver_fly"), self.origin, VEC_ORIGIN, 1);
	if ((random() < 0.25))
	{
		sound(self, CHAN_VOICE, "reiver/run.wav", 1, ATTN_IDLE);
	}
};

void(float scratch_noise) reiver_melee_scratch =
{
	local vector delta;
	local float ldmg;
	local float richtung;

	if (!self.enemy)
	{
		return;
	}
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 77))
	{
		return;
	}
	ldmg = ((random() + random()) + random()) * autocvar_reiver_melee_scratch_damage;
	T_Damage(self.enemy, self, self, ldmg);
	makevectors(self.angles);
	particle(((self.origin + (v_forward * 45)) + (v_up * -10)), VEC_ORIGIN, 73, 17);
	if (scratch_noise)
	{
		sound(self, CHAN_AUTO, "demon/dhit2.wav", 0.6, ATTN_NORM);
		richtung = crandom() * 100;
		SpawnMeatSpray(((self.origin + (v_forward * 27)) + (v_up * -22)), (v_right * richtung));
	}
};

void() reiver_melee_left1 = [ 69, reiver_melee_left2 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_left2 = [ 70, reiver_melee_left3 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_left3 = [ 71, reiver_melee_left4 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_left4 = [ 72, reiver_melee_left5 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_left5 = [ 73, reiver_melee_left6 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
	reiver_melee_scratch(1);
};

void() reiver_melee_left6 = [ 74, reiver_melee_left7 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
	reiver_melee_scratch(0);
};

void() reiver_melee_left7 = [ 75, reiver_melee_left8 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
	reiver_melee_scratch(0);
};

void() reiver_melee_left8 = [ 76, reiver_melee_left9 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
	reiver_melee_scratch(0);
};

void() reiver_melee_left9 = [ 77, reiver_melee_left10 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_left10 = [ 78, reiver_melee_left11 ]
{

	ai_charge(10);
	self.nextthink = (time + 0.07);
	if ((((self.attack_chance > 2) && (pointcontents(self.origin) != CONTENT_SKY)) && (pointcontents(self.origin) != CONTENT_SOLID)))
	{
		self.attack_chance = 0;
		self.movetype = MOVETYPE_STEP;
		if (self.bodyphased)
		{
			self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
			self.colormod = '1 1 1';
			self.alpha = 1;
			self.glow_color = 0;
			self.glow_size = 0;
			self.bodyphased = 0;
			sound(self, CHAN_BODY, "misc/null.wav", 1, ATTN_NORM);
			sound(self, CHAN_WEAPON, "reiver/death.wav", 1, ATTN_NORM, SNDSPD);
			particleeffectnum(/*52177i*/"hydra_toxic_player");
			pointparticles(particleeffectnum(/*52177i*/"hydra_toxic_player"), (self.origin + '0 0 -8'), VEC_ORIGIN, 1);
		}
	}
};

void() reiver_melee_left11 = [ 79, reiver_melee_left12 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_left12 = [ 80, reiver_melee_left13 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_left13 = [ 81, reiver_melee_left14 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_left14 = [ 82, reiver_melee_left15 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_left15 = [ 83, reiver_melee_left16 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_left16 = [ 84, reiver_run1 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_right1 = [ 85, reiver_melee_right2 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_right2 = [ 86, reiver_melee_right3 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_right3 = [ 87, reiver_melee_right4 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_right4 = [ 88, reiver_melee_right5 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_right5 = [ 89, reiver_melee_right6 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_right6 = [ 90, reiver_melee_right7 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_right7 = [ 91, reiver_melee_right8 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
	reiver_melee_scratch(1);
};

void() reiver_melee_right8 = [ 92, reiver_melee_right9 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
	reiver_melee_scratch(0);
};

void() reiver_melee_right9 = [ 93, reiver_melee_right10 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
	reiver_melee_scratch(0);
};

void() reiver_melee_right10 = [ 94, reiver_melee_right11 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
	reiver_melee_scratch(0);
};

void() reiver_melee_right11 = [ 95, reiver_melee_right12 ]
{

	ai_charge(10);
	self.nextthink = (time + 0.07);
	if ((((self.attack_chance > 2) && (pointcontents(self.origin) != CONTENT_SKY)) && (pointcontents(self.origin) != CONTENT_SOLID)))
	{
		self.attack_chance = 0;
		self.movetype = MOVETYPE_STEP;
		if (self.bodyphased)
		{
			self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
			self.colormod = '1 1 1';
			self.alpha = 1;
			self.glow_color = 0;
			self.glow_size = 0;
			self.bodyphased = 0;
			sound(self, CHAN_BODY, "misc/null.wav", 1, ATTN_NORM);
			sound(self, CHAN_WEAPON, "reiver/death.wav", 1, ATTN_NORM, SNDSPD);
			particleeffectnum(/*52177i*/"hydra_toxic_player");
			pointparticles(particleeffectnum(/*52177i*/"hydra_toxic_player"), (self.origin + '0 0 -8'), VEC_ORIGIN, 1);
		}
	}
};

void() reiver_melee_right12 = [ 96, reiver_melee_right13 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_right13 = [ 97, reiver_melee_right14 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_right14 = [ 98, reiver_melee_right15 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee_right15 = [ 99, reiver_run1 ]
{
	ai_charge(10);
	self.nextthink = (time + 0.07);
};

void() reiver_melee =
{
	if ((self.dodge_finished > time))
	{
		self.dodge_finished = time;
	}
	if ((random() < 0.5))
	{
		reiver_melee_left1();
	}
	else
	{
		reiver_melee_right1();
	}
};

void(vector ofs, float scal) reiver_hand1 =
{
	local vector org;

	makevectors(self.angles);
	org = ((self.origin + (v_forward * ofs_x)) + (v_right * ofs_y)) + (v_up * ofs_z);
	setorigin(self.owner, org);
	self.owner.scale = scal;
};

void(vector ofs, float scal) reiver_hand2 =
{
	local vector org;

	makevectors(self.angles);
	org = ((self.origin + (v_forward * ofs_x)) + (v_right * ofs_y)) + (v_up * ofs_z);
	setorigin(self.owner2, org);
	self.owner2.scale = scal;
};

void() life_drain_effect =
{
	local vector dir;

	makevectors(self.enemy.angles);
	dir = normalize((self.origin - self.enemy.origin));
	if (autocvar_reiver_vampire_life_drain_particle_effect)
	{
		if ((autocvar_reiver_vampire_life_drain_particle_effect == 1))
		{
			particleeffectnum(/*52750i*/"reiver_vampire_drain1");
			pointparticles(particleeffectnum(/*52750i*/"reiver_vampire_drain1"), (((self.enemy.origin + self.enemy.view_ofs) + (v_up * -8)) + (v_forward * 10)), (dir * 10), 1);
		}
		else
		{
			particleeffectnum(/*52772i*/"reiver_vampire_drain2");
			pointparticles(particleeffectnum(/*52772i*/"reiver_vampire_drain2"), (((self.enemy.origin + self.enemy.view_ofs) + (v_up * -8)) + (v_forward * 10)), (dir * 10), 1);
		}
	}
};

void() life_drain =
{
	local vector spot1;
	local vector spot2;

	spot1 = self.origin + '0 0 12';
	spot2 = self.enemy.origin + self.enemy.view_ofs;
	traceline(spot1, spot2, FALSE, self);
	if ((trace_ent != self.enemy))
	{
		return;
	}
	life_drain_effect();
	if ((autocvar_reiver_vampire_life_drain < (1 + skill)))
	{
		autocvar_reiver_vampire_life_drain = 1 + skill;
	}
	T_Damage(self.enemy, self, self, autocvar_reiver_vampire_life_drain);
	self.health = (self.health + autocvar_reiver_vampire_life_drain);
	if ((self.health > self.health_initial))
	{
		self.health = self.health_initial;
	}
};

void() reiver_vampire1 = [ 116, reiver_vampire2 ]
{
	ai_face();
	self.nextthink = (time + 0.13);
	self.has_fired = 0;
	reiver_hand1('32 23 1', 0.35);
	reiver_hand2('37 -20 2', 0.35);
	sound(self, CHAN_AUTO, "reiver/vampire.wav", 1, ATTN_NORM);
};

void() reiver_vampire2 = [ 117, reiver_vampire3 ]
{
	ai_face();
	self.nextthink = (time + 0.13);
	reiver_hand1('34 23 5', 0.5);
	reiver_hand2('37 -23 5', 0.5);
};

void() reiver_vampire3 = [ 118, reiver_vampire4 ]
{
	ai_face();
	self.has_fired = -1;
	ai_run(1);
	self.nextthink = (time + 0.12);
	life_drain();
	reiver_hand1('42 27 9', 0.75);
	reiver_hand2('42 -27 9', 0.75);
};

void() reiver_vampire4 = [ 119, reiver_vampire5 ]
{
	ai_face();
	ai_run(1);
	self.nextthink = (time + 0.14);
	life_drain();
	reiver_hand1('47 31 12', 1);
	reiver_hand2('47 -30 11', 1);
	sound(self, CHAN_AUTO, "reiver/vampire.wav", 1, ATTN_NORM);
};

void() reiver_vampire5 = [ 120, reiver_vampire6 ]
{
	ai_face();
	ai_run(1);
	self.nextthink = (time + 0.14);
	life_drain();
	reiver_hand1('45 30 11', 1);
	reiver_hand2('45 -29 10', 1);
};

void() reiver_vampire6 = [ 121, reiver_vampire7 ]
{
	ai_face();
	ai_run(1);
	self.nextthink = (time + 0.15);
	reiver_hand1('42 25 9', 0.85);
	reiver_hand2('42 -24 9', 0.85);
	life_drain();
	if ((skill == 3))
	{
		self.attack_finished = ((time + 0.6) + random());
	}
	else
	{
		if ((skill > 1))
		{
			self.attack_finished = ((time + 0.8) + random());
		}
		else
		{
			self.attack_finished = ((time + 1.3) + random());
		}
	}
};

void() reiver_vampire7 = [ 122, reiver_run1 ]
{
	ai_face();
	ai_run(1);
	self.nextthink = (time + 0.2);
	reiver_hand1('40 20 2', 0.7);
	reiver_hand2('37 -21 5', 0.7);
	if ((random() < 0.3))
	{
		self.has_fired = 1;
	}
	else
	{
		self.has_fired = 0;
	}
};

void() reiver_shoot1 = [ 52, reiver_shoot2 ]
{
	if (((random() < 0.05) || ((self.has_fired == 1) && (random() < 0.3))))
	{
		self.has_fired = 101;
	}
	else
	{
		self.has_fired = 102;
	}
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.06);
	if ((self.projectile_type == 0))
	{
		reiver_hand1('32 24 2', 0.35);
		reiver_hand2('37 -20 2', 0.35);
	}
};

void() reiver_shoot2 = [ 53, reiver_shoot3 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.06);
	if ((self.projectile_type == 0))
	{
		reiver_hand1('28 24 5', 0.5);
		reiver_hand2('33 -21 5', 0.5);
	}
};

void() reiver_shoot3 = [ 54, reiver_shoot4 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.06);
	if ((self.projectile_type == 0))
	{
		reiver_hand1('24 24 8', 0.6);
		reiver_hand2('29 -21 8', 0.6);
	}
};

void() reiver_shoot4 = [ 55, reiver_shoot5 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.06);
	if ((self.projectile_type == 0))
	{
		reiver_hand1('20 24 14', 0.7);
		reiver_hand2('25 -21 14', 0.7);
	}
};

void() reiver_shoot5 = [ 56, reiver_shoot6 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.06);
	if ((self.projectile_type == 0))
	{
		reiver_hand1('13 26 20', 0.8);
		reiver_hand2('17 -23 20', 0.8);
	}
};

void() reiver_shoot6 = [ 57, reiver_shoot7 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.07);
	if ((self.projectile_type == 0))
	{
		reiver_hand1('9 28 22', 0.8);
		reiver_hand2('13 -27 22', 0.8);
	}
};

void() reiver_shoot7 = [ 58, reiver_shoot8 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.07);
	if ((self.projectile_type == 0))
	{
		reiver_hand1('14 23 22', 0.8);
		reiver_hand2('18 -23 22', 0.8);
	}
};

void() reiver_shoot8 = [ 59, reiver_shoot9 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.07);
	if ((self.projectile_type == 0))
	{
		reiver_hand1('23 19 14', 0.8);
		reiver_hand2('26 -19 14', 0.8);
	}
};

void() reiver_shoot9 = [ 60, reiver_shoot10 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.07);
	if ((self.projectile_type == 0))
	{
		reiver_hand1('36 11 5', 0.8);
		reiver_hand2('36 -11 5', 0.8);
	}
};

void() reiver_shoot10 = [ 61, reiver_shoot11 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.1);
	if ((self.projectile_type == 0))
	{
		reiver_hand1('46 8 -1', 0.8);
		reiver_hand2('46 -8 -1', 0.8);
		if ((pointcontents(self.origin) != CONTENT_SOLID))
		{
			reiver_fireball();
		}
	}
	else
	{
		ghost_followers();
		ghost_followers();
		ghost_followers();
	}
};

void() reiver_shoot11 = [ 62, reiver_shoot12 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.12);
	if ((skill == 3))
	{
		self.attack_finished = (((time + 0.5) + random()) + (self.projectile_type * 0.5));
	}
	else
	{
		if ((skill > 0))
		{
			self.attack_finished = (((time + 1) + random()) + (self.projectile_type * 0.5));
		}
		else
		{
			self.attack_finished = (((time + 1.5) + random()) + (self.projectile_type * 0.5));
		}
	}
};

void() reiver_shoot12 = [ 63, reiver_shoot13 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.07);
};

void() reiver_shoot13 = [ 64, reiver_shoot14 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.07);
};

void() reiver_shoot14 = [ 65, reiver_shoot15 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.07);
};

void() reiver_shoot15 = [ 66, reiver_shoot16 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.07);
};

void() reiver_shoot16 = [ 67, reiver_shoot17 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.07);
};

void() reiver_shoot17 = [ 68, reiver_run1 ]
{
	ai_run(((skill * 0.5) + 5.5));
	ai_face();
	self.nextthink = (time + 0.07);
	if (((random() < 0.4) && (self.has_fired == 101)))
	{
		self.has_fired = 1;
	}
	else
	{
		self.has_fired = 0;
	}
};

void() reiver_missile =
{
	local vector spot1;
	local vector spot2;
	local vector org;
	local vector porg;
	local float r;
	local float zufall;
	local entity o;
	local entity p;

	if (((pointcontents(self.origin) == CONTENT_SOLID) || (self.attack_chance > 0)))
	{
		return;
	}
	spot1 = self.origin + '0 0 15';
	spot2 = self.enemy.origin + '0 0 15';
	r = vlen((spot1 - spot2));
	if (((((r < 200) && (self.movetype != MOVETYPE_NOCLIP)) && (pointcontents(self.origin) != CONTENT_SKY)) && (pointcontents(self.origin) != CONTENT_SOLID)))
	{
		if (!FacingIdeal())
		{
			ai_face();
			return;
		}
		makevectors(self.angles);
		self.owner = spawn();
		o = self.owner;
		o.nextthink = (time + 0.85);
		o.think = SUB_Remove;
		o.effects = 40;
		o.scale = 0.25;
		o.alpha = 0.725;
		o.colormod = '0.3 1.3 0.3';
		setmodel(o, "progs/reiverhands.spr");
		org = ((self.origin + (v_forward * 32)) + (v_right * 23)) + (v_up * 1);
		setorigin(o, org);
		self.owner2 = spawn();
		p = self.owner2;
		p.nextthink = (time + 0.85);
		p.think = SUB_Remove;
		p.effects = 40;
		p.scale = 0.25;
		p.alpha = 0.725;
		p.colormod = '0.3 1.3 0.3';
		setmodel(p, "progs/reiverhands.spr");
		porg = ((self.origin + (v_forward * 36)) + (v_right * -20)) + (v_up * 1);
		setorigin(p, org);
		reiver_vampire1();
	}
	else
	{
		zufall = autocvar_reiver_projectile_type * 0.01;
		if ((random() < 0.925))
		{
			self.projectile_type = 0;
			makevectors(self.angles);
			self.owner = spawn();
			o = self.owner;
			o.nextthink = (time + 0.75);
			o.think = SUB_Remove;
			o.effects = 40;
			o.scale = 0.25;
			o.alpha = 0.666;
			setmodel(o, "progs/reiverhands.spr");
			org = ((self.origin + (v_forward * 32)) + (v_right * 23)) + (v_up * 1);
			setorigin(o, org);
			self.owner2 = spawn();
			p = self.owner2;
			p.nextthink = (time + 0.75);
			p.think = SUB_Remove;
			p.effects = 40;
			p.scale = 0.25;
			p.alpha = 0.666;
			setmodel(p, "progs/reiverhands.spr");
			porg = ((self.origin + (v_forward * 36)) + (v_right * -20)) + (v_up * 1);
			setorigin(p, org);
			sound(self, CHAN_AUTO, "reiver/ranged_attack.wav", 1, ATTN_NORM);
		}
		else
		{
			self.projectile_type = 1;
			sound(self, CHAN_AUTO, "reiver/ranged_attack2.wav", 1, ATTN_NORM);
		}
		reiver_shoot1();
	}
};

void() reiver_paina1 = [ 100, reiver_paina2 ]
{
	self.has_fired = 0;
	ai_face();
	self.nextthink = (time + 0.08);
};

void() reiver_paina2 = [ 101, reiver_paina3 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
};

void() reiver_paina3 = [ 102, reiver_paina4 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
};

void() reiver_paina4 = [ 103, reiver_paina5 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
};

void() reiver_paina5 = [ 104, reiver_paina6 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
};

void() reiver_paina6 = [ 105, reiver_paina7 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
};

void() reiver_paina7 = [ 106, reiver_paina8 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
};

void() reiver_paina8 = [ 107, reiver_paina9 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() reiver_paina9 = [ 108, reiver_paina10 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() reiver_paina10 = [ 109, reiver_paina11 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() reiver_paina11 = [ 110, reiver_paina12 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() reiver_paina12 = [ 111, reiver_paina13 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() reiver_paina13 = [ 112, reiver_paina14 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() reiver_paina14 = [ 113, reiver_paina15 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() reiver_paina15 = [ 114, reiver_paina16 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() reiver_paina16 = [ 115, reiver_run1 ]
{
	ai_face();
	self.nextthink = (time + 0.06);
};

void() reiver_painb1 = [ 123, reiver_painb2 ]
{
	self.has_fired = 0;
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb2 = [ 124, reiver_painb3 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb3 = [ 125, reiver_painb4 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb4 = [ 126, reiver_painb5 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb5 = [ 127, reiver_painb6 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb6 = [ 128, reiver_painb7 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb7 = [ 129, reiver_painb8 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb8 = [ 130, reiver_painb9 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb9 = [ 131, reiver_painb10 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb10 = [ 132, reiver_painb11 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb11 = [ 133, reiver_painb12 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void() reiver_painb12 = [ 134, reiver_run1 ]
{
	ai_face();
	self.nextthink = (time + 0.075);
};

void(entity attacker, float damage) reiver_pain =
{
	if ((self.dodge_finished > time))
	{
		return;
	}
	if ((self.pain_finished > time))
	{
		return;
	}
	if (((random() * 60) > damage))
	{
		return;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_reiver * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	if ((random() > 0.5))
	{
		self.pain_finished = (time + 1.7);
		sound(self, CHAN_VOICE, "reiver/pain2.wav", 1, ATTN_NORM);
		reiver_paina1();
	}
	else
	{
		self.pain_finished = (time + 1.5);
		sound(self, CHAN_VOICE, "reiver/pain1.wav", 1, ATTN_NORM);
		reiver_painb1();
	}
};

void() reiver_death_touch =
{
	if (((self.flags & FL_ONGROUND) || (self.attack_chance == 100)))
	{
		self.solid = 0;
		T_RadiusDamage(self, self, autocvar_reiver_death_explosion_radius_damage, world);
		pointparticles(particleeffectnum(/*26406i*/"rocket_explosion"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
		sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, ATTN_NORM);
		self.delete_painskin = 1;
		remove(self);
		return;
	}
	else
	{
		if ((self.velocity == VEC_ORIGIN))
		{
			self.solid = 0;
			T_RadiusDamage(self, self, autocvar_reiver_death_explosion_radius_damage, world);
			pointparticles(particleeffectnum(/*26406i*/"rocket_explosion"), self.origin, VEC_ORIGIN, 1);
			pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
			pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
			sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, ATTN_NORM);
			self.delete_painskin = 1;
			remove(self);
			return;
		}
	}
	if ((self.origin == self.old_origin))
	{
		self.solid = 0;
		T_RadiusDamage(self, self, autocvar_reiver_death_explosion_radius_damage, world);
		pointparticles(particleeffectnum(/*26406i*/"rocket_explosion"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
		sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, ATTN_NORM);
		self.delete_painskin = 1;
		remove(self);
		return;
	}
	self.old_origin = self.origin;
	self.think = reiver_death_touch;
	self.nextthink = (time + 0.001);
};

void() reiver_death1 = [ 142, reiver_death2 ]
{
	self.nextthink = (time + 0.1);
	self.flags = (self.flags - FL_ONGROUND);
	self.flags = (self.flags | FL_FLY);
};

void() reiver_death2 = [ 143, reiver_death3 ]
{
	self.nextthink = (time + 0.1);
	self.solid = 0;
};

void() reiver_death3 = [ 144, reiver_death4 ]
{
	self.nextthink = (time + 0.1);
	if (((random() < 0.7) && (enemy_range != RANGE_MELEE)))
	{
		self.attack_chance = 100;
		reiver_death_touch();
	}
	self.flags = (self.flags - FL_FLY);
	self.velocity_x = (-200 + (400 * random()));
	self.velocity_y = (-200 + (400 * random()));
	self.velocity_z = (100 + (100 * random()));
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
};

void() reiver_death4 = [ 145, reiver_death5 ]
{
	self.nextthink = (time + 0.1);
};

void() reiver_death5 = [ 146, reiver_death6 ]
{
	self.nextthink = (time + 0.1);
};

void() reiver_death6 = [ 147, reiver_death7 ]
{
	self.nextthink = (time + 0.1);
};

void() reiver_death7 = [ 148, reiver_death8 ]
{
	self.nextthink = (time + 0.1);
};

void() reiver_death8 = [ 149, reiver_death9 ]
{
	self.nextthink = (time + 0.1);
	reiver_death_touch();
};

void() reiver_death9 = [ 150, reiver_death10 ]
{
	self.nextthink = (time + 0.1);
};

void() reiver_death10 = [ 151, reiver_death11 ]
{
	self.nextthink = (time + 0.1);
};

void() reiver_death11 = [ 152, reiver_death12 ]
{
	self.nextthink = (time + 0.1);
};

void() reiver_death12 = [ 153, reiver_death13 ]
{
	self.nextthink = (time + 0.1);
};

void() reiver_death13 = [ 154, reiver_death14 ]
{
	self.nextthink = (time + 0.1);
};

void() reiver_death14 = [ 155, reiver_death15 ]
{
	self.nextthink = (time + 0.1);
};

void() reiver_death15 = [ 156, reiver_death15 ]
{
	self.nextthink = (time + 0.1);
	self.attack_chance = 100;
};

void() reiver_die =
{
	self.dodge_finished = (time - 1);
	sound7(self, CHAN_VOICE, "reiver/death.wav", 1, ATTN_NORM);
	reiver_death1();
};

void() animate_shield =
{
	self.reiver_shield_animation = (time + 0.07);
	self.frame = (self.frame + 1);
	if ((self.frame >= 20))
	{
		self.frame = 0;
	}
};

void() reiver_shield_think =
{
	if ((autocvar_reiver_multi_shield_chance == 0))
	{
		remove(self);
		return;
	}
	if ((self.reiver_shield_animation < time))
	{
		animate_shield();
	}
	self.scale = 0.9;
	if (((self.owner.dodge_finished > time) && !self.owner.meleeing))
	{
		self.alpha = 1;
		self.protective_shield_spawned = 1;
		self.owner.takedamage = DAMAGE_YES;
	}
	else
	{
		self.alpha = -1;
		self.protective_shield_spawned = 0;
		self.owner.takedamage = DAMAGE_AIM;
	}
	if ((((self.owner.enemy != world) && (self.protective_shield_spawned == 0)) && !self.owner.meleeing))
	{
		if ((random() < 0.000900))
		{
			self.owner.dodge_finished = ((time + autocvar_reiver_multi_shield_lifetime) + random());
		}
	}
	if ((self.owner.health < 0))
	{
		remove(self);
		return;
	}
	setorigin(self, '0 0 -9');
	self.think = reiver_shield_think;
	self.nextthink = (time + 0.01);
};

void() monster_reiver =
{
	local entity reiver_shield;
	local entity pain_skin_entity;

	self.classname = "monster_reiver";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.origin_z = (self.origin_z + 20);
	setmodel(self, "progs/reiver.mdl");
	self.skin = 0;
	self.monstermodel = 0;
	setsize(self, '-20 -20 -24', '20 20 24');
	self.health = autocvar_reiver_health;
	if ((cvar("skill") == 3))
	{
		self.health = 370;
	}
	self.health_initial = self.health;
	self.colormod = '1 1 1';
	self.scale = 1;
	self.th_stand = reiver_idle1;
	self.th_walk = reiver_fly1;
	self.th_run = reiver_run1;
	self.th_missile = reiver_missile;
	self.th_melee = reiver_melee;
	self.th_pain = reiver_pain;
	self.th_die = reiver_die;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_reiver_multi_shield_chance)
	{
		reiver_shield = spawn();
		reiver_shield.solid = 0;
		reiver_shield.movetype = MOVETYPE_NOCLIP;
		setmodel(reiver_shield, "progs/reiver_shield.mdl");
		setsize(reiver_shield, VEC_HULL_MIN, VEC_HULL_MAX);
		setorigin(reiver_shield, '0 0 -9');
		reiver_shield.owner = self;
		reiver_shield.avelocity = '0 77 0';
		reiver_shield.frame = 0;
		reiver_shield.think = reiver_shield_think;
		reiver_shield.nextthink = time;
		setattachment(reiver_shield, self, /*37325i*/"test");
	}
	if (autocvar_painskin_transparency)
	{
		pain_skin_entity = spawn();
		pain_skin_entity.solid = 0;
		pain_skin_entity.movetype = MOVETYPE_NOCLIP;
		pain_skin_entity.owner = self;
		setmodel(pain_skin_entity, self.model);
		setsize(pain_skin_entity, '-20 -20 -24', '20 20 24');
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
	flymonster_start();
	if ((pointcontents(self.origin) == CONTENT_SOLID))
	{
		self.attack_chance = -1;
		self.traileffectnum = particleeffectnum(/*19532i*/"teleporter_particles");
		self.colormod = '0.1 0.1 0.1';
		self.alpha = 0.6;
		self.glow_color = 1;
		self.glow_size = 104;
	}
	MonsterPhysics(self, autocvar_reivermass);
};

void() monster_reiver_liftorigin =
{
	local entity reiver_shield;
	local entity pain_skin_entity;

	self.classname = "monster_reiver";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.origin_z = (self.origin_z + 25);
	setmodel(self, "progs/reiver.mdl");
	self.skin = 0;
	self.monstermodel = 0;
	setsize(self, '-20 -20 -24', '20 20 24');
	self.health = autocvar_reiver_health;
	if ((cvar("skill") == 3))
	{
		self.health = 370;
	}
	self.health_initial = self.health;
	self.colormod = '1 1 1';
	self.scale = 1;
	self.th_stand = reiver_idle_random;
	self.th_walk = reiver_fly1;
	self.th_run = reiver_run1;
	self.th_missile = reiver_missile;
	self.th_melee = reiver_melee;
	self.th_pain = reiver_pain;
	self.th_die = reiver_die;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_reiver_multi_shield_chance)
	{
		reiver_shield = spawn();
		reiver_shield.solid = 0;
		reiver_shield.movetype = MOVETYPE_NOCLIP;
		setmodel(reiver_shield, "progs/reiver_shield.mdl");
		setsize(reiver_shield, VEC_HULL_MIN, VEC_HULL_MAX);
		setorigin(reiver_shield, '0 0 -9');
		reiver_shield.owner = self;
		reiver_shield.avelocity = '0 77 0';
		reiver_shield.frame = 0;
		reiver_shield.think = reiver_shield_think;
		reiver_shield.nextthink = time;
		setattachment(reiver_shield, self, /*37325i*/"test");
	}
	if (autocvar_painskin_transparency)
	{
		pain_skin_entity = spawn();
		pain_skin_entity.solid = 0;
		pain_skin_entity.movetype = MOVETYPE_NOCLIP;
		pain_skin_entity.owner = self;
		setmodel(pain_skin_entity, self.model);
		setsize(pain_skin_entity, '-20 -20 -24', '20 20 24');
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
	flymonster_start();
	MonsterPhysics(self, autocvar_reivermass);
};

void() monster_reiver_start =
{
	local entity clone;

	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_reiver;
	clone.nextthink = (time + 0.000100);
};

void() monster_reiver_liftorigin_start =
{
	local entity clone;

	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_reiver_liftorigin;
	clone.nextthink = (time + 0.000100);
};

void() add_reiver_support_fly =
{
	local entity clone;
	local entity head;
	local float done;
	local float c;
	local float proceed;
	local vector ang;
	local vector pos;

	done = 0;
	c = 0;
	ang = self.angles;
	while ((done == 0))
	{
		makevectors(ang);
		pos = ((self.origin + (60 * v_forward)) + ((crandom() * 33) * v_right)) + ((crandom() * 48) * v_up);
		head = findradius(pos, 35);
		proceed = 1;
		while (head)
		{
			if (((head.health > 0) && (head.flags & 40)))
			{
				proceed = 0;
			}
			head = head.chain;
		}
		traceline(self.origin, pos, FALSE, self);
		if (((trace_fraction == 1) && (proceed == 1)))
		{
			traceline(self.origin, (pos - '40 40 0'), FALSE, self);
			if ((trace_fraction == 1))
			{
				traceline(self.origin, (pos + '40 40 0'), FALSE, self);
				if ((trace_fraction == 1))
				{
					done = 1;
				}
			}
		}
		if ((done == 0))
		{
			c = c + 1;
			if ((c == 10))
			{
				return;
			}
		}
	}
	if (((0 - self.origin_z) < 12))
	{
		return;
	}
	clone = spawn();
	copyentity(self, clone);
	setorigin(clone, pos);
	clone.think = monster_reiver;
	clone.nextthink = (time + 0.000100);
};

void() add_reiver_support_walk =
{
	local entity clone;
	local entity head;
	local float done;
	local float c;
	local float proceed;
	local vector ang;
	local vector pos;

	done = 0;
	c = 0;
	ang = self.angles;
	while ((done == 0))
	{
		makevectors(ang);
		if ((pointcontents(self.origin) == CONTENT_WATER))
		{
			pos = ((self.origin + (48 * v_forward)) + ((crandom() * 33) * v_right)) + (2 * v_up);
		}
		else
		{
			pos = ((self.origin + (60 * v_forward)) + ((crandom() * 33) * v_right)) + (35 * v_up);
		}
		head = findradius(pos, 35);
		proceed = 1;
		while (head)
		{
			if (((head.health > 0) && (head.flags & 40)))
			{
				proceed = 0;
			}
			head = head.chain;
		}
		traceline(self.origin, pos, FALSE, self);
		if (((trace_fraction == 1) && (proceed == 1)))
		{
			traceline(self.origin, (pos - '40 40 0'), FALSE, self);
			if ((trace_fraction == 1))
			{
				traceline(self.origin, (pos + '40 40 0'), FALSE, self);
				if ((trace_fraction == 1))
				{
					traceline(self.origin, (pos + '0 0 40'), FALSE, self);
					if ((trace_fraction == 1))
					{
						traceline(self.origin, (pos - '0 0 80'), FALSE, self);
						if ((trace_fraction != 1))
						{
							done = 1;
						}
					}
				}
			}
		}
		if ((done == 0))
		{
			c = c + 1;
			if ((c == 10))
			{
				return;
			}
		}
	}
	if ((pointcontents(pos) != CONTENT_WATER))
	{
		traceline(pos, (pos + '0 0 250'), FALSE, self);
		if ((vlen((trace_endpos - pos)) > 72))
		{
			pos = trace_endpos - '0 0 53';
		}
		else
		{
			return;
		}
	}
	clone = spawn();
	copyentity(self, clone);
	setorigin(clone, pos);
	clone.think = monster_reiver;
	clone.nextthink = (time + 0.000100);
};
