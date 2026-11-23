//Decompiled code. Please respect the original copyright.

void() carniv_idle_sound =
{
	if ((random() < 0.2))
	{
		if ((random() < 0.5))
		{
			sound(self, CHAN_VOICE, "carnivean/idle1.wav", 1, ATTN_IDLE);
		}
		else
		{
			sound(self, CHAN_VOICE, "carnivean/idle2.wav", 1, ATTN_IDLE);
		}
	}
};

void(float loudness) carniv_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.5))
		{
			sound(self, CHAN_AUTO, "carnivean/step1.wav", loudness, ATTN_IDLE);
		}
		else
		{
			sound(self, CHAN_AUTO, "carnivean/step2.wav", loudness, ATTN_IDLE);
		}
	}
};

void() carniv_projectile_rock_touch =
{
	local vector dir;
	local vector vel;
	local vector detonate;

	detonate = self.origin;
	detonate = detonate - (10 * normalize(self.velocity));
	dir = self.enemy.origin - self.origin;
	dir = normalize(dir);
	if (other.takedamage)
	{
		spawn_touchblood(25);
		sound(self, CHAN_WEAPON, "ambience/coaled_monster_explode.wav", 0.6, ATTN_NORM);
		vel = dir * autocvar_carnivean_rock_projectile_pushback;
		if ((self.enemy.flags & FL_ONGROUND))
		{
			self.enemy.flags = (self.enemy.flags - FL_ONGROUND);
		}
		self.enemy.velocity = (self.enemy.velocity + vel);
		self.enemy.punchangle = (self.enemy.punchangle + (randomvec() * 17));
		T_Damage(self.enemy, self, self.owner, autocvar_carnivean_rock_projectile_impact_damage);
		pointparticles(particleeffectnum(/*52539i*/"canivean_rock_explode"), detonate, VEC_ORIGIN, 1);
	}
	else
	{
		pointparticles(particleeffectnum(/*52539i*/"canivean_rock_explode"), detonate, VEC_ORIGIN, 1);
		sound(self, CHAN_WEAPON, "ambience/coaled_monster_explode.wav", 0.8, ATTN_NORM);
	}
	remove(self);
};

void() carniv_projectile_rock_homing =
{
	local vector dir;
	local vector vtemp;

	if ((self.enemy.health < 1))
	{
		remove(self);
	}
	if ((self.maxlifetime < time))
	{
		remove(self);
		return;
	}
	if ((self.origin == self.old_origin))
	{
		sound(self, CHAN_WEAPON, "ambience/coaled_monster_explode.wav", 0.7, ATTN_NORM);
		T_RadiusDamage(self, self.owner, (autocvar_carnivean_rock_projectile_impact_damage + 5), self.owner);
		pointparticles(particleeffectnum(/*52539i*/"canivean_rock_explode"), self.origin, VEC_ORIGIN, 1);
		remove(self);
		return;
	}
	self.old_origin = self.origin;
	self.frame = (self.frame + 1);
	if ((self.frame >= 23))
	{
		self.frame = 0;
	}
	if ((time >= self.skypad_steer_t))
	{
		vtemp = self.enemy.origin + '0 0 10';
		dir = normalize((vtemp - self.origin));
		if ((skill == 3))
		{
			self.velocity = (dir * 350);
		}
		else
		{
			self.velocity = (dir * 300);
		}
	}
	self.nextthink = (time + 0.06);
	self.think = carniv_projectile_rock_homing;
};

void() carniv_projectile_rock_no_homing =
{
	self.frame = (self.frame + 1);
	if ((self.frame >= 23))
	{
		self.frame = 0;
	}
	self.nextthink = (time + 0.05);
	self.think = carniv_projectile_rock_no_homing;
};

void() carniv_projectile_flame_touch =
{
	local float zufal;

	if ((other == self.owner))
	{
		return;
	}
	if ((other.takedamage == DAMAGE_AIM))
	{
		spawn_touchblood(20);
		T_Damage(other, self, self.owner, autocvar_carnivean_explosive_projectile_impact_damage);
		pointparticles(particleeffectnum(/*52421i*/"torment_hellrod_explosion"), self.origin, VEC_ORIGIN, 1);
		sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, ATTN_NORM);
		if ((autocvar_carnivean_projectiles_inflame_chance && (self.projectile_type == 1)))
		{
			zufal = random() * 100;
			if ((zufal <= autocvar_carnivean_projectiles_inflame_chance))
			{
				other.inflamed = 1;
				other.inflametime = (time + autocvar_fire_projectiles_and_lava_inflame_time);
				other.inflamepause = (time + autocvar_fire_projectiles_and_lava_inflame_frequence);
				if (autocvar_fire_projectiles_and_lava_inflame_particles)
				{
					sound(other, CHAN_AUTO, "player/inflame.wav", 1, ATTN_NORM);
					sound(other, 120, "zombie/corpse_fire.wav", 1, ATTN_NORM);
				}
			}
		}
	}
	else
	{
		T_RadiusDamage(self, self.owner, autocvar_carnivean_explosive_projectile_radius_damage, other);
		pointparticles(particleeffectnum(/*26571i*/"grenade_explosion"), self.origin, VEC_ORIGIN, 1);
		sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, ATTN_NORM);
	}
	remove(self);
};

void() carniv_projectile =
{
	local entity missile;
	local float zufal;

	self.effects = (self.effects | EF_MUZZLEFLASH);
	missile = spawn();
	missile.owner = self;
	missile.enemy = self.enemy;
	missile.classname = "carniv_projectile";
	missile.movetype = MOVETYPE_FLYMISSILE;
	missile.solid = SOLID_BBOX;
	makevectors(self.angles);
	setorigin(missile, (((self.origin + (v_right * -12)) + (v_up * 8)) + (v_forward * 7)));
	zufal = autocvar_carnivean_projectile_type * 0.01;
	if ((random() <= zufal))
	{
		setmodel(missile, "progs/k_spike.mdl");
		missile.alpha = -1;
		missile.traileffectnum = particleeffectnum(/*52057i*/"TR_AFRITSPIKE_RED");
		missile.projectile_type = 1;
		sound(self, CHAN_WEAPON, "weapons/sgun1.wav", 1, ATTN_NORM);
		missile.velocity = normalize(((self.enemy.origin + '0 0 7') - missile.origin));
		missile.velocity = (missile.velocity * 666);
		missile.angles = vectoangles(missile.velocity);
		missile.touch = carniv_projectile_flame_touch;
		missile.nextthink = (time + 5);
		missile.think = SUB_Remove;
	}
	else
	{
		setmodel(missile, "progs/carniv_rocks.mdl");
		missile.scale = 0.4;
		missile.projectile_type = 2;
		sound(self, CHAN_WEAPON, "carnivean/rock_throw.wav", 1, ATTN_NORM);
		missile.velocity = normalize(((self.enemy.origin + '0 0 10') - missile.origin));
		if (autocvar_carnivean_rock_projectile_homing)
		{
			missile.velocity = (missile.velocity * 350);
		}
		else
		{
			missile.velocity = (missile.velocity * 400);
		}
		missile.angles = vectoangles(missile.velocity);
		missile.maxlifetime = (time + 7);
		missile.touch = carniv_projectile_rock_touch;
		if (autocvar_carnivean_rock_projectile_homing)
		{
			missile.nextthink = (time + 0.2);
			missile.think = carniv_projectile_rock_homing;
		}
		else
		{
			missile.nextthink = (time + 0.2);
			missile.think = carniv_projectile_rock_no_homing;
		}
	}
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
};

void() carniv_stand = [ 9, carniv_stand1 ]
{
	ai_stand();
	carniv_idle_sound();
};

void() carniv_stand1 = [ 10, carniv_stand2 ]
{
	ai_stand();
};

void() carniv_stand2 = [ 11, carniv_stand3 ]
{
	ai_stand();
};

void() carniv_stand3 = [ 12, carniv_stand4 ]
{
	ai_stand();
};

void() carniv_stand4 = [ 13, carniv_stand5 ]
{
	ai_stand();
};

void() carniv_stand5 = [ 14, carniv_stand6 ]
{
	ai_stand();
};

void() carniv_stand6 = [ 15, carniv_stand7 ]
{
	ai_stand();
};

void() carniv_stand7 = [ 16, carniv_stand8 ]
{
	ai_stand();
};

void() carniv_stand8 = [ 17, carniv_stand9 ]
{
	ai_stand();
};

void() carniv_stand9 = [ 18, carniv_stand10 ]
{
	ai_stand();
};

void() carniv_stand10 = [ 19, carniv_stand11 ]
{
	ai_stand();
};

void() carniv_stand11 = [ 20, carniv_stand12 ]
{
	ai_stand();
};

void() carniv_stand12 = [ 21, carniv_stand13 ]
{
	ai_stand();
};

void() carniv_stand13 = [ 22, carniv_stand14 ]
{
	ai_stand();
};

void() carniv_stand14 = [ 23, carniv_stand15 ]
{
	ai_stand();
};

void() carniv_stand15 = [ 24, carniv_stand16 ]
{
	ai_stand();
};

void() carniv_stand16 = [ 25, carniv_stand17 ]
{
	ai_stand();
};

void() carniv_stand17 = [ 26, carniv_stand18 ]
{
	ai_stand();
};

void() carniv_stand18 = [ 27, carniv_stand19 ]
{
	ai_stand();
};

void() carniv_stand19 = [ 28, carniv_stand20 ]
{
	ai_stand();
};

void() carniv_stand20 = [ 29, carniv_stand21 ]
{
	ai_stand();
	carniv_idle_sound();
};

void() carniv_stand21 = [ 30, carniv_stand22 ]
{
	ai_stand();
};

void() carniv_stand22 = [ 31, carniv_stand23 ]
{
	ai_stand();
};

void() carniv_stand23 = [ 32, carniv_stand24 ]
{
	ai_stand();
};

void() carniv_stand24 = [ 33, carniv_stand25 ]
{
	ai_stand();
};

void() carniv_stand25 = [ 34, carniv_stand26 ]
{
	ai_stand();
};

void() carniv_stand26 = [ 35, carniv_stand27 ]
{
	ai_stand();
};

void() carniv_stand27 = [ 36, carniv_stand28 ]
{
	ai_stand();
};

void() carniv_stand28 = [ 37, carniv_stand29 ]
{
	ai_stand();
};

void() carniv_stand29 = [ 38, carniv_stand30 ]
{
	ai_stand();
};

void() carniv_stand30 = [ 39, carniv_stand31 ]
{
	ai_stand();
};

void() carniv_stand31 = [ 40, carniv_stand32 ]
{
	ai_stand();
};

void() carniv_stand32 = [ 41, carniv_stand33 ]
{
	ai_stand();
};

void() carniv_stand33 = [ 42, carniv_stand34 ]
{
	ai_stand();
};

void() carniv_stand34 = [ 43, carniv_stand35 ]
{
	ai_stand();
};

void() carniv_stand35 = [ 44, carniv_stand36 ]
{
	ai_stand();
};

void() carniv_stand36 = [ 45, carniv_stand37 ]
{
	ai_stand();
};

void() carniv_stand37 = [ 46, carniv_stand38 ]
{
	ai_stand();
};

void() carniv_stand38 = [ 47, carniv_stand ]
{
	ai_stand();
};

void() carniv_walk1 = [ 54, carniv_walk2 ]
{
	ai_walk(9);
	carniv_idle_sound();
};

void() carniv_walk2 = [ 55, carniv_walk3 ]
{
	ai_walk(2);
};

void() carniv_walk3 = [ 56, carniv_walk4 ]
{
	ai_walk(4);
};

void() carniv_walk4 = [ 57, carniv_walk5 ]
{
	ai_walk(6);
};

void() carniv_walk5 = [ 58, carniv_walk6 ]
{
	ai_walk(9);
	carniv_footsteps(0.9);
};

void() carniv_walk6 = [ 59, carniv_walk7 ]
{
	ai_walk(9);
};

void() carniv_walk7 = [ 60, carniv_walk8 ]
{
	ai_walk(12);
};

void() carniv_walk8 = [ 61, carniv_walk9 ]
{
	ai_walk(11);
};

void() carniv_walk9 = [ 62, carniv_walk10 ]
{
	ai_walk(4);
};

void() carniv_walk10 = [ 63, carniv_walk11 ]
{
	ai_walk(3);
};

void() carniv_walk11 = [ 64, carniv_walk12 ]
{
	ai_walk(10);
	carniv_footsteps(0.9);
};

void() carniv_walk12 = [ 65, carniv_walk1 ]
{
	ai_walk(14);
};

void() carniv_run1 = [ 54, carniv_run2 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(10);
	carniv_idle_sound();
};

void() carniv_run2 = [ 55, carniv_run3 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(3);
};

void() carniv_run3 = [ 56, carniv_run4 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(5);
};

void() carniv_run4 = [ 57, carniv_run5 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(7);
};

void() carniv_run5 = [ 58, carniv_run6 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(10);
	carniv_footsteps(1);
};

void() carniv_run6 = [ 59, carniv_run7 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(10);
};

void() carniv_run7 = [ 60, carniv_run8 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(13);
};

void() carniv_run8 = [ 61, carniv_run9 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(12);
};

void() carniv_run9 = [ 62, carniv_run10 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(5);
};

void() carniv_run10 = [ 63, carniv_run11 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(4);
};

void() carniv_run11 = [ 64, carniv_run12 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(11);
	carniv_footsteps(1);
};

void() carniv_run12 = [ 65, carniv_run1 ]
{
	self.nextthink = ((time + 0.08) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(15);
};

void() carniv_swing1 = [ 74, carniv_swing2 ]
{
	ai_charge(10);
};

void() carniv_swing2 = [ 75, carniv_swing3 ]
{
	ai_charge(5);
};

void() carniv_swing3 = [ 76, carniv_swing4 ]
{
	ai_charge(4);
};

void() carniv_swing4 = [ 77, carniv_swing5 ]
{
	ai_charge(9);
	sound(self, CHAN_WEAPON, "carnivean/swing.wav", 1, ATTN_NORM);
	ai_melee_carnivean(0);
};

void() carniv_swing5 = [ 78, carniv_swing6 ]
{
	ai_charge(12);
	carniv_footsteps(0.8);
	ai_melee_carnivean(1);
};

void() carniv_swing6 = [ 79, carniv_swing7 ]
{
	ai_charge(7);
	ai_melee_carnivean(0);
};

void() carniv_swing7 = [ 80, carniv_swing8 ]
{
	ai_charge(6);
	ai_melee_carnivean(0);
};

void() carniv_swing8 = [ 81, carniv_swing9 ]
{
	ai_charge(13);
};

void() carniv_swing9 = [ 82, carniv_swing10 ]
{
	ai_charge(5);
};

void() carniv_swing10 = [ 83, carniv_swing11 ]
{
	ai_charge(10);
};

void() carniv_swing11 = [ 84, carniv_run1 ]
{
	ai_charge(9);
};

void() carniv_fire1 = [ 66, carniv_fire2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() carniv_fire2 = [ 67, carniv_fire3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() carniv_fire3 = [ 68, carniv_fire4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() carniv_fire4 = [ 69, carniv_fire5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	carniv_projectile();
	if ((skill >= 2))
	{
		self.attack_finished = ((time + 1) + random());
	}
	else
	{
		self.attack_finished = ((time + 1.5) + random());
	}
};

void() carniv_fire5 = [ 70, carniv_fire6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() carniv_fire6 = [ 71, carniv_fire7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() carniv_fire7 = [ 72, carniv_fire8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() carniv_fire8 = [ 73, carniv_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() carniv_missile =
{
	if ((random() <= 0.77))
	{
		sound(self, CHAN_AUTO, "carnivean/scream.wav", 1, ATTN_NORM);
		carniv_fire1();
	}
};

void() carniv_pain1 = [ 85, carniv_pain2 ]
{
};

void() carniv_pain2 = [ 86, carniv_pain3 ]
{
};

void() carniv_pain3 = [ 87, carniv_pain4 ]
{
};

void() carniv_pain4 = [ 88, carniv_pain5 ]
{
};

void() carniv_pain5 = [ 89, carniv_pain6 ]
{
};

void() carniv_pain6 = [ 90, carniv_run1 ]
{
};

void() carniv_painb1 = [ 91, carniv_painb2 ]
{
};

void() carniv_painb2 = [ 92, carniv_painb3 ]
{
};

void() carniv_painb3 = [ 93, carniv_painb4 ]
{
};

void() carniv_painb4 = [ 94, carniv_painb5 ]
{
};

void() carniv_painb5 = [ 95, carniv_run1 ]
{
};

void() carniv_painc1 = [ 96, carniv_painc2 ]
{
};

void() carniv_painc2 = [ 97, carniv_painc3 ]
{
	carniv_footsteps(0.8);
};

void() carniv_painc3 = [ 98, carniv_painc4 ]
{
};

void() carniv_painc4 = [ 99, carniv_painc5 ]
{
};

void() carniv_painc5 = [ 100, carniv_painc6 ]
{
};

void() carniv_painc6 = [ 101, carniv_painc7 ]
{
};

void() carniv_painc7 = [ 102, carniv_painc8 ]
{
};

void() carniv_painc8 = [ 103, carniv_painc9 ]
{
};

void() carniv_painc9 = [ 104, carniv_painc10 ]
{
};

void() carniv_painc10 = [ 105, carniv_painc11 ]
{
	carniv_footsteps(0.7);
};

void() carniv_painc11 = [ 106, carniv_run1 ]
{
};

void(entity attacker, float damage) carniv_pain =
{
	local float r;

	if ((self.pain_finished > time))
	{
		return;
	}
	if (((random() * 70) > damage))
	{
		return;
	}
	r = random();
	if ((r < 0.33))
	{
		sound(self, CHAN_VOICE, "carnivean/pain2.wav", 1, ATTN_NORM);
		carniv_pain1();
		self.pain_finished = (time + 1.2);
	}
	else
	{
		if ((r < 0.66))
		{
			sound(self, CHAN_VOICE, "carnivean/pain2.wav", 1, ATTN_NORM);
			carniv_painb1();
			self.pain_finished = (time + 1.2);
		}
		else
		{
			sound(self, CHAN_VOICE, "carnivean/pain1.wav", 1, ATTN_NORM);
			carniv_painc1();
			self.pain_finished = (time + 1.7);
		}
	}
};

void() carniv_die1 = [ 107, carniv_die2 ]
{
	ai_back(10);
};

void() carniv_die2 = [ 108, carniv_die3 ]
{
	ai_back(6);
};

void() carniv_die3 = [ 109, carniv_die4 ]
{
	ai_back(5);
	self.solid = 0;
};

void() carniv_die4 = [ 110, carniv_die5 ]
{
	ai_back(4);
};

void() carniv_die5 = [ 111, carniv_die6 ]
{
	sound(self, CHAN_AUTO, "demon/fall_backwards.wav", 1, ATTN_NORM);
};

void() carniv_die6 = [ 112, carniv_die7 ]
{
};

void() carniv_die7 = [ 113, carniv_die8 ]
{
};

void() carniv_die8 = [ 114, carniv_die9 ]
{
};

void() carniv_die9 = [ 115, carniv_die10 ]
{
	sound(self, CHAN_AUTO, "demon/fall_backwards.wav", 0.7, ATTN_NORM);
};

void() carniv_die10 = [ 116, carniv_die11 ]
{
};

void() carniv_die11 = [ 117, carniv_die12 ]
{
};

void() carniv_die12 = [ 118, carniv_die13 ]
{
};

void() carniv_die13 = [ 119, carniv_die14 ]
{
	ai_back(1);
};

void() carniv_die14 = [ 120, carniv_die15 ]
{
	ai_back(1);
};

void() carniv_die15 = [ 121, carniv_die16 ]
{
	ai_back(1);
};

void() carniv_die16 = [ 122, carniv_die17 ]
{
	ai_back(1);
};

void() carniv_die17 = [ 123, carniv_die18 ]
{
};

void() carniv_die18 = [ 124, carniv_die19 ]
{
};

void() carniv_die19 = [ 125, carniv_die20 ]
{
};

void() carniv_die20 = [ 126, carniv_die21 ]
{
};

void() carniv_die21 = [ 127, carniv_die22 ]
{
};

void() carniv_die22 = [ 128, carniv_die23 ]
{
};

void() carniv_die23 = [ 129, carniv_die24 ]
{
};

void() carniv_die24 = [ 130, carniv_die25 ]
{
};

void() carniv_die25 = [ 131, carniv_die26 ]
{
};

void() carniv_die26 = [ 132, carniv_die27 ]
{
};

void() carniv_die27 = [ 133, carniv_die28 ]
{
};

void() carniv_die28 = [ 134, carniv_die29 ]
{
};

void() carniv_die29 = [ 135, carniv_die30 ]
{
};

void() carniv_die30 = [ 136, carniv_die31 ]
{
};

void() carniv_die31 = [ 137, carniv_die31 ]
{
	if ((autocvar_carniveancorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_carniveancorpsehealth, "progs/h_carnivean.mdl");
};

void() carniv_bdie1 = [ 138, carniv_bdie2 ]
{
	ai_back(3);
};

void() carniv_bdie2 = [ 139, carniv_bdie3 ]
{
	ai_back(3);
};

void() carniv_bdie3 = [ 140, carniv_bdie4 ]
{
	ai_back(3);
	self.solid = 0;
};

void() carniv_bdie4 = [ 141, carniv_bdie5 ]
{
	ai_back(2);
	carniv_footsteps(0.8);
};

void() carniv_bdie5 = [ 142, carniv_bdie6 ]
{
	ai_back(2);
};

void() carniv_bdie6 = [ 143, carniv_bdie7 ]
{
	ai_back(2);
};

void() carniv_bdie7 = [ 144, carniv_bdie8 ]
{
	ai_back(2);
};

void() carniv_bdie8 = [ 145, carniv_bdie9 ]
{
	ai_back(2);
};

void() carniv_bdie9 = [ 146, carniv_bdie10 ]
{
};

void() carniv_bdie10 = [ 147, carniv_bdie11 ]
{
};

void() carniv_bdie11 = [ 148, carniv_bdie12 ]
{
};

void() carniv_bdie12 = [ 149, carniv_bdie13 ]
{
	ai_back(1);
};

void() carniv_bdie13 = [ 150, carniv_bdie14 ]
{
	ai_back(3);
};

void() carniv_bdie14 = [ 151, carniv_bdie15 ]
{
	ai_back(3);
};

void() carniv_bdie15 = [ 152, carniv_bdie16 ]
{
	ai_back(3);
};

void() carniv_bdie16 = [ 153, carniv_bdie17 ]
{
	sound(self, CHAN_AUTO, "demon/fall_backwards.wav", 1, ATTN_NORM);
};

void() carniv_bdie17 = [ 154, carniv_bdie18 ]
{
};

void() carniv_bdie18 = [ 155, carniv_bdie19 ]
{
};

void() carniv_bdie19 = [ 156, carniv_bdie20 ]
{
};

void() carniv_bdie20 = [ 157, carniv_bdie21 ]
{
};

void() carniv_bdie21 = [ 158, carniv_bdie22 ]
{
};

void() carniv_bdie22 = [ 159, carniv_bdie23 ]
{
};

void() carniv_bdie23 = [ 160, carniv_bdie24 ]
{
};

void() carniv_bdie24 = [ 161, carniv_bdie25 ]
{
};

void() carniv_bdie25 = [ 162, carniv_bdie26 ]
{
};

void() carniv_bdie26 = [ 163, carniv_bdie27 ]
{
};

void() carniv_bdie27 = [ 164, carniv_bdie28 ]
{
};

void() carniv_bdie28 = [ 165, carniv_bdie29 ]
{
};

void() carniv_bdie29 = [ 166, carniv_bdie30 ]
{
};

void() carniv_bdie30 = [ 167, carniv_bdie31 ]
{
};

void() carniv_bdie31 = [ 168, carniv_bdie32 ]
{
};

void() carniv_bdie32 = [ 169, carniv_bdie33 ]
{
};

void() carniv_bdie33 = [ 170, carniv_bdie34 ]
{
};

void() carniv_bdie34 = [ 171, carniv_bdie35 ]
{
};

void() carniv_bdie35 = [ 172, carniv_bdie36 ]
{
};

void() carniv_bdie36 = [ 173, carniv_bdie37 ]
{
};

void() carniv_bdie37 = [ 174, carniv_bdie38 ]
{
};

void() carniv_bdie38 = [ 175, carniv_bdie39 ]
{
};

void() carniv_bdie39 = [ 176, carniv_bdie40 ]
{
};

void() carniv_bdie40 = [ 177, carniv_bdie40 ]
{
	if ((autocvar_carniveancorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_carniveancorpsehealth, "progs/h_carnivean.mdl");
};

void() carnivean_lightning_death = [ 85, carnivean_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() carnivean_lightning_death1 = [ 85, carnivean_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	CopyMonsterToBodyQue(1, "progs/h_carnivean.mdl");
};

void() carniv_die =
{
	if (autocvar_lightninggun_death_animation)
	{
		if ((self.enemy.weapon == IT_LIGHTNING))
		{
			carnivean_lightning_death();
			return;
		}
	}
	if ((self.health < -60))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_carnivean * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		sound(self, CHAN_VOICE, "player/udeath.wav", 1, ATTN_NORM);
		ThrowHead("progs/h_carnivean.mdl", self.health);
		ThrowGib("progs/gib1.mdl", self.health);
		ThrowGib("progs/gib2.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		if ((autocvar_bloodextension == 1))
		{
			pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
		}
		return;
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_carnivean * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	if ((random() < 0.5))
	{
		sound(self, CHAN_VOICE, "carnivean/death1.wav", 1, ATTN_NORM);
		carniv_die1();
	}
	else
	{
		sound(self, CHAN_VOICE, "carnivean/death2.wav", 1, ATTN_NORM);
		carniv_bdie1();
	}
};

void() monster_carnivean =
{
	local entity pain_skin_entity;

	self.classname = "monster_carnivean";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/carnivean.mdl");
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	if (!self.health)
	{
		self.health = autocvar_carnivean_health;
	}
	self.health_initial = self.health;
	self.colormod = '1 1 1';
	self.scale = 1;
	self.alpha = 1;
	self.th_stand = carniv_stand;
	self.th_walk = carniv_walk1;
	self.th_run = carniv_run1;
	self.th_die = carniv_die;
	self.th_melee = carniv_swing1;
	self.th_missile = carniv_missile;
	self.th_pain = carniv_pain;
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
	MonsterPhysics(self, autocvar_carniveanmass);
};

void() monster_carnivean_start =
{
	local entity clone;

	self.scale = 1;
	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_carnivean;
	clone.nextthink = (time + 0.000100);
};
