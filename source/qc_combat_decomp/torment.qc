//Decompiled code. Please respect the original copyright.

void(float loudness) torment_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.5))
		{
			sound(self, CHAN_AUTO, "walk/torment1.wav", loudness, ATTN_IDLE);
		}
		else
		{
			sound(self, CHAN_AUTO, "walk/torment2.wav", loudness, ATTN_IDLE);
		}
	}
};

void() TormentCheckForCharge =
{
	if (!enemy_vis)
	{
		return;
	}
	if ((time < self.attack_finished))
	{
		return;
	}
	if ((fabs((self.origin_z - self.enemy.origin_z)) > 20))
	{
		return;
	}
	if ((vlen((self.origin - self.enemy.origin)) < 80))
	{
		return;
	}
	SUB_AttackFinished(2);
	torment_char_a1();
};

void() TormentCheckContinueCharge =
{
	if ((time > self.attack_finished))
	{
		SUB_AttackFinished(3);
		torment_run1();
		return;
	}
	sound(self, CHAN_WEAPON, "torment/miss.wav", 1, ATTN_NORM);
};

void() HellStaffExplode =
{
	T_RadiusDamage(self, self.owner, autocvar_torment_rod_missile, world);
	pointparticles(particleeffectnum(/*52421i*/"torment_hellrod_explosion"), self.origin, VEC_ORIGIN, 1);
	sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, ATTN_NORM);
	remove(self);
};

void() HellStaffTouch =
{
	if ((other == self.owner))
	{
		return;
	}
	if ((other.takedamage == DAMAGE_AIM))
	{
		HellStaffExplode();
		return;
	}
	if ((self.magiccounter == 0))
	{
		self.magiccounter = 1;
		sound(self, CHAN_VOICE, "torment/firehit.wav", 0.8, ATTN_NORM);
		if ((self.velocity == VEC_ORIGIN))
		{
			self.avelocity = VEC_ORIGIN;
		}
	}
};

void() HellStaff =
{
	local entity missile;
	local float r;

	r = random();
	self.effects = (self.effects | EF_MUZZLEFLASH);
	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	makevectors(self.angles);
	missile.velocity = normalize((self.enemy.origin - self.origin));
	missile.velocity = (missile.velocity * 400);
	if ((vlen((self.enemy.origin - self.origin)) < 200))
	{
		missile.velocity_z = ((missile.velocity_z + 50) + (r * 100));
	}
	else
	{
		missile.velocity_z = ((missile.velocity_z + 200) + (r * 77));
	}
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.touch = HellStaffTouch;
	missile.nextthink = (time + 3);
	missile.think = HellStaffExplode;
	setmodel(missile, "progs/torm_lavaball.mdl");
	missile.scale = 0.3;
	missile.traileffectnum = particleeffectnum(/*52447i*/"torment_hellrod_projectile");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	r = random();
	if ((random() < 0.5))
	{
		if ((random() < 0.5))
		{
			setorigin(missile, (((self.origin + (v_right * (r * 20))) + (v_up * 25)) + (v_forward * 31)));
		}
		else
		{
			setorigin(missile, (((self.origin + (v_right * (r * 15))) + (v_up * 22)) + (v_forward * 35)));
		}
	}
	else
	{
		if ((random() < 0.5))
		{
			setorigin(missile, (((self.origin + (v_right * (r * 18))) + (v_up * 24)) + (v_forward * 30)));
		}
		else
		{
			setorigin(missile, (((self.origin + (v_right * (r * 16))) + (v_up * 22)) + (v_forward * 33)));
		}
	}
	sound(self, CHAN_WEAPON, "torment/hellstafffire.wav", 1, ATTN_NORM);
};

void() torment_stand1 = [ 0, torment_stand2 ]
{
	self.skin = 0;
	ai_stand();
};

void() torment_stand2 = [ 1, torment_stand3 ]
{
	ai_stand();
};

void() torment_stand3 = [ 2, torment_stand4 ]
{
	ai_stand();
};

void() torment_stand4 = [ 3, torment_stand5 ]
{
	ai_stand();
	sound(self, CHAN_AUTO, "torment/scratch.wav", 1, ATTN_IDLE);
};

void() torment_stand5 = [ 4, torment_stand6 ]
{
	ai_stand();
};

void() torment_stand6 = [ 5, torment_stand7 ]
{
	ai_stand();
	makevectors(self.angles);
	particleeffectnum(/*52474i*/"torment_rod_scratching_start");
	pointparticles(particleeffectnum(/*52474i*/"torment_rod_scratching_start"), (((self.origin + (v_right * 10)) + (v_up * -24)) + (v_forward * 18)), VEC_ORIGIN, 1);
};

void() torment_stand7 = [ 26, torment_stand8 ]
{
	ai_stand();
	makevectors(self.angles);
	particleeffectnum(/*52503i*/"torment_rod_scratching");
	pointparticles(particleeffectnum(/*52503i*/"torment_rod_scratching"), (((self.origin + (v_right * 10)) + (v_up * -24)) + (v_forward * 15)), VEC_ORIGIN, 1);
};

void() torment_stand8 = [ 27, torment_stand9 ]
{
	ai_stand();
	makevectors(self.angles);
	particleeffectnum(/*52503i*/"torment_rod_scratching");
	pointparticles(particleeffectnum(/*52503i*/"torment_rod_scratching"), (((self.origin + (v_right * 12)) + (v_up * -24)) + (v_forward * 9)), VEC_ORIGIN, 1);
};

void() torment_stand9 = [ 28, torment_stand10 ]
{
	ai_stand();
	makevectors(self.angles);
	particleeffectnum(/*52503i*/"torment_rod_scratching");
	pointparticles(particleeffectnum(/*52503i*/"torment_rod_scratching"), (((self.origin + (v_right * 14)) + (v_up * -24)) + (v_forward * 3)), VEC_ORIGIN, 1);
};

void() torment_stand10 = [ 29, torment_stand11 ]
{
	ai_stand();
	makevectors(self.angles);
	particleeffectnum(/*52503i*/"torment_rod_scratching");
	pointparticles(particleeffectnum(/*52503i*/"torment_rod_scratching"), (((self.origin + (v_right * 16)) + (v_up * -24)) + (v_forward * -4)), VEC_ORIGIN, 1);
};

void() torment_stand11 = [ 30, torment_stand12 ]
{
	ai_stand();
	makevectors(self.angles);
	particleeffectnum(/*52503i*/"torment_rod_scratching");
	pointparticles(particleeffectnum(/*52503i*/"torment_rod_scratching"), (((self.origin + (v_right * 18)) + (v_up * -24)) + (v_forward * -11)), VEC_ORIGIN, 1);
};

void() torment_stand12 = [ 31, torment_stand13 ]
{
	ai_stand();
	makevectors(self.angles);
	particleeffectnum(/*52503i*/"torment_rod_scratching");
	pointparticles(particleeffectnum(/*52503i*/"torment_rod_scratching"), (((self.origin + (v_right * 20)) + (v_up * -24)) + (v_forward * -18)), VEC_ORIGIN, 1);
	if ((random() < 0.2))
	{
		sound(self, CHAN_AUTO, "torment/idle.wav", 1, ATTN_IDLE);
	}
};

void() torment_stand13 = [ 32, torment_stand1 ]
{
	ai_stand();
	makevectors(self.angles);
	particleeffectnum(/*52503i*/"torment_rod_scratching");
	pointparticles(particleeffectnum(/*52503i*/"torment_rod_scratching"), (((self.origin + (v_right * 20)) + (v_up * -24)) + (v_forward * -25)), VEC_ORIGIN, 1);
};

void() torment_walk1 = [ 41, torment_walk2 ]
{
	self.skin = 0;
	ai_walk(5);
	if ((random() < 0.2))
	{
		sound(self, CHAN_AUTO, "torment/idle.wav", 1, ATTN_NORM);
	}
};

void() torment_walk2 = [ 42, torment_walk3 ]
{
	ai_walk(5);
};

void() torment_walk3 = [ 43, torment_walk4 ]
{
	ai_walk(5);
};

void() torment_walk4 = [ 44, torment_walk5 ]
{
	ai_walk(4);
	torment_footsteps(1);
};

void() torment_walk5 = [ 45, torment_walk6 ]
{
	ai_walk(4);
};

void() torment_walk6 = [ 46, torment_walk7 ]
{
	ai_walk(5);
};

void() torment_walk7 = [ 47, torment_walk8 ]
{
	ai_walk(5);
};

void() torment_walk8 = [ 48, torment_walk9 ]
{
	ai_walk(4);
};

void() torment_walk9 = [ 49, torment_walk10 ]
{
	ai_walk(3);
};

void() torment_walk10 = [ 50, torment_walk11 ]
{
	ai_walk(4);
	torment_footsteps(1);
};

void() torment_walk11 = [ 51, torment_walk12 ]
{
	ai_walk(3);
};

void() torment_walk12 = [ 52, torment_walk1 ]
{
	ai_walk(5);
};

void() torment_run1 = [ 33, torment_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	self.skin = 0;
	ai_run(20);
	TormentCheckForCharge();
};

void() torment_run2 = [ 34, torment_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(25);
	torment_footsteps(1);
};

void() torment_run3 = [ 35, torment_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(18);
};

void() torment_run4 = [ 36, torment_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() torment_run5 = [ 37, torment_run6 ]
{
	ai_run(14);
};

void() torment_run6 = [ 38, torment_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(13);
	torment_footsteps(1);
};

void() torment_run7 = [ 39, torment_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(14);
};

void() torment_run8 = [ 40, torment_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(13);
	if ((random() < 0.2))
	{
		sound(self, CHAN_AUTO, "torment/idle.wav", 1, ATTN_IDLE);
	}
};

void() torment_paina1 = [ 70, torment_paina2 ]
{
	self.skin = 0;
};

void() torment_paina2 = [ 71, torment_paina3 ]
{
};

void() torment_paina3 = [ 72, torment_paina4 ]
{
};

void() torment_paina4 = [ 73, torment_run1 ]
{
};

void() torment_painb1 = [ 74, torment_painb2 ]
{
	self.skin = 0;
};

void() torment_painb2 = [ 75, torment_painb3 ]
{
};

void() torment_painb3 = [ 76, torment_painb4 ]
{
};

void() torment_painb4 = [ 77, torment_painb5 ]
{
};

void() torment_painb5 = [ 78, torment_painb6 ]
{
};

void() torment_painb6 = [ 79, torment_run1 ]
{
};

void() torment_painc1 = [ 80, torment_painc2 ]
{
	self.skin = 0;
};

void() torment_painc2 = [ 81, torment_painc3 ]
{
};

void() torment_painc3 = [ 82, torment_painc4 ]
{
};

void() torment_painc4 = [ 83, torment_painc5 ]
{
};

void() torment_painc5 = [ 84, torment_run1 ]
{
};

void(entity attacker, float damage) torment_pain =
{
	local float r;

	r = random();
	if ((self.pain_finished > time))
	{
		return;
	}
	if ((r <= 0.35))
	{
		sound(self, CHAN_VOICE, "torment/pain1.wav", 1, ATTN_NORM);
	}
	else
	{
		if ((r <= 0.65))
		{
			sound(self, CHAN_VOICE, "torment/pain2.wav", 1, ATTN_NORM);
		}
		else
		{
			sound(self, CHAN_VOICE, "torment/pain3.wav", 1, ATTN_NORM);
		}
	}
	if (((random() * 30) > damage))
	{
		return;
	}
	if (((time - self.pain_finished) > 5))
	{
		torment_painc1();
		self.pain_finished = (time + 1);
		return;
	}
	self.pain_finished = (time + 1);
	if ((r <= 0.35))
	{
		torment_paina1();
	}
	else
	{
		if ((r <= 0.65))
		{
			torment_painb1();
		}
		else
		{
			torment_painc1();
		}
	}
};

void() torment_die1 = [ 85, torment_die2 ]
{
	self.skin = 0;
	ai_back(5);
	self.nextthink = (time + 0.12);
};

void() torment_die2 = [ 86, torment_die3 ]
{
	ai_back(8);
	self.nextthink = (time + 0.12);
};

void() torment_die3 = [ 87, torment_die4 ]
{
	ai_back(7);
	self.solid = 0;
	self.nextthink = (time + 0.12);
};

void() torment_die4 = [ 88, torment_die5 ]
{
	self.nextthink = (time + 0.12);
};

void() torment_die5 = [ 89, torment_die6 ]
{
	sound(self, CHAN_AUTO, "torment/fall.wav", 1, ATTN_IDLE);
};

void() torment_die6 = [ 90, torment_die7 ]
{
};

void() torment_die7 = [ 91, torment_die7 ]
{
	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	if ((autocvar_tormentcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_tormentcorpsehealth, "progs/h_torment.mdl");
};

void() torment_lightning_death = [ 70, torment_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() torment_lightning_death1 = [ 70, torment_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	CopyMonsterToBodyQue(1, "progs/h_torment.mdl");
};

void() torment_inflamed1 = [ 33, torment_inflamed2 ]
{
	local float r;

	ai_run_inflamed(20);
	self.nextthink = (time + 0.085);
	r = random();
	if ((r <= 0.2))
	{
		sound(self, CHAN_VOICE, "torment/pain1.wav", 1, ATTN_NORM);
	}
	else
	{
		if ((r <= 0.5))
		{
			sound(self, CHAN_VOICE, "torment/pain2.wav", 1, ATTN_NORM);
		}
		else
		{
			if ((r <= 0.77))
			{
				sound(self, CHAN_VOICE, "torment/pain3.wav", 1, ATTN_NORM);
			}
		}
	}
};

void() torment_inflamed2 = [ 34, torment_inflamed3 ]
{
	ai_run_inflamed(25);
	self.nextthink = (time + 0.085);
};

void() torment_inflamed3 = [ 35, torment_inflamed4 ]
{
	ai_run_inflamed(18);
	self.nextthink = (time + 0.085);
};

void() torment_inflamed4 = [ 36, torment_inflamed5 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.085);
};

void() torment_inflamed5 = [ 37, torment_inflamed6 ]
{
	ai_run_inflamed(14);
	self.nextthink = (time + 0.085);
};

void() torment_inflamed6 = [ 38, torment_inflamed7 ]
{
	ai_run_inflamed(13);
	self.nextthink = (time + 0.085);
};

void() torment_inflamed7 = [ 39, torment_inflamed8 ]
{
	ai_run_inflamed(14);
	self.nextthink = (time + 0.085);
};

void() torment_inflamed8 = [ 40, torment_inflamed1 ]
{
	local float r;

	ai_run_inflamed(13);
	self.nextthink = (time + 0.085);
	if ((self.inflametime < time))
	{
		torment_die();
		return;
	}
	r = random();
	if ((r < 0.22))
	{
		torment_inflamed9();
	}
	else
	{
		if ((r < 0.45))
		{
			torment_inflamed13();
		}
	}
};

void() torment_inflamed9 = [ 70, torment_inflamed10 ]
{
	local float r;

	self.nextthink = (time + 0.09);
	r = random();
	if ((r <= 0.2))
	{
		sound(self, CHAN_VOICE, "torment/pain1.wav", 1, ATTN_NORM);
	}
	else
	{
		if ((r <= 0.5))
		{
			sound(self, CHAN_VOICE, "torment/pain2.wav", 1, ATTN_NORM);
		}
		else
		{
			if ((r <= 0.77))
			{
				sound(self, CHAN_VOICE, "torment/pain3.wav", 1, ATTN_NORM);
			}
		}
	}
};

void() torment_inflamed10 = [ 71, torment_inflamed11 ]
{
	self.nextthink = (time + 0.09);
};

void() torment_inflamed11 = [ 72, torment_inflamed12 ]
{
	self.nextthink = (time + 0.09);
};

void() torment_inflamed12 = [ 73, torment_inflamed1 ]
{
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		torment_die();
		return;
	}
};

void() torment_inflamed13 = [ 80, torment_inflamed14 ]
{
	local float r;

	self.nextthink = (time + 0.09);
	r = random();
	if ((r <= 0.2))
	{
		sound(self, CHAN_VOICE, "torment/pain1.wav", 1, ATTN_NORM);
	}
	else
	{
		if ((r <= 0.5))
		{
			sound(self, CHAN_VOICE, "torment/pain2.wav", 1, ATTN_NORM);
		}
		else
		{
			if ((r <= 0.77))
			{
				sound(self, CHAN_VOICE, "torment/pain3.wav", 1, ATTN_NORM);
			}
		}
	}
};

void() torment_inflamed14 = [ 81, torment_inflamed15 ]
{
	self.nextthink = (time + 0.09);
};

void() torment_inflamed15 = [ 82, torment_inflamed16 ]
{
	self.nextthink = (time + 0.09);
};

void() torment_inflamed16 = [ 83, torment_inflamed17 ]
{
	self.nextthink = (time + 0.09);
};

void() torment_inflamed17 = [ 84, torment_inflamed1 ]
{
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		torment_die();
		return;
	}
};

void() torment_die =
{
	local float zufa;

	if (autocvar_lightninggun_death_animation)
	{
		if ((self.enemy.weapon == IT_LIGHTNING))
		{
			torment_lightning_death();
			return;
		}
	}
	if ((self.health < -40))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_torment * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		sound(self, CHAN_VOICE, "player/udeath.wav", 1, ATTN_NORM);
		ThrowHead("progs/h_torment.mdl", self.health);
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
	if (autocvar_burning_monsters_death_animation)
	{
		if ((self.inflamed == 0))
		{
			zufa = random() * 100;
			if (((((self.enemy.weapon == IT_GRENADE_LAUNCHER) || (self.enemy.weapon == IT_ROCKET_LAUNCHER)) && (zufa <= autocvar_burning_monsters_death_animation)) && (self.watertype != CONTENT_WATER)))
			{
				self.delete_painskin = 1;
				self.inflamed = 1;
				self.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
				self.inflametime = ((time + autocvar_burning_monsters_death_animation_time) + random());
				torment_inflamed1();
				return;
			}
		}
		else
		{
			sound(self, CHAN_VOICE, "torment/death1.wav", 1, ATTN_NORM);
			torment_die1();
			return;
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_torment * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound(self, CHAN_VOICE, "torment/death1.wav", 1, ATTN_NORM);
	torment_die1();
};

void() torment_char_a1 = [ 33, torment_char_a2 ]
{
	self.skin = 0;
	ai_charge(20);
};

void() torment_char_a2 = [ 34, torment_char_a3 ]
{
	ai_charge(20);
};

void() torment_char_a3 = [ 35, torment_char_a4 ]
{
	ai_charge(21);
};

void() torment_char_a4 = [ 36, torment_char_a5 ]
{
	ai_charge(13);
};

void() torment_char_a5 = [ 37, torment_char_a6 ]
{
	ai_charge(20);
};

void() torment_char_a6 = [ 38, torment_char_a7 ]
{
	ai_charge(13);
};

void() torment_char_a7 = [ 39, torment_char_a8 ]
{
	ai_charge(20);
};

void() torment_char_a8 = [ 40, torment_run1 ]
{
	ai_charge(13);
};

void() torment_char_b1 = [ 33, torment_char_b2 ]
{
	self.skin = 0;
	TormentCheckContinueCharge();
	ai_charge(23);
};

void() torment_char_b2 = [ 34, torment_char_b3 ]
{
	ai_charge(17);
};

void() torment_char_b3 = [ 35, torment_char_b4 ]
{
	ai_charge(12);
};

void() torment_char_b4 = [ 36, torment_char_b5 ]
{
	ai_charge(22);
};

void() torment_char_b5 = [ 37, torment_char_b6 ]
{
	ai_charge(18);
};

void() torment_char_b6 = [ 38, torment_char_b7 ]
{
	ai_charge(22);
};

void() torment_char_b7 = [ 39, torment_char_b8 ]
{
	ai_charge(18);
};

void() torment_char_b8 = [ 40, torment_char_b1 ]
{
	ai_charge(8);
};

void() torment_watk1 = [ 53, torment_watk2 ]
{
	self.skin = 0;
	ai_charge(9);
};

void() torment_watk2 = [ 54, torment_watk3 ]
{
	self.skin = 1;
	ai_charge(7);
};

void() torment_watk3 = [ 55, torment_watk4 ]
{
	self.skin = 1;
	if ((random() < 0.4))
	{
		sound(self, CHAN_WEAPON, "torment/hellstaff_swing1.wav", 1, ATTN_NORM);
	}
	else
	{
		sound(self, CHAN_WEAPON, "torment/hellstaff_swing2.wav", 1, ATTN_NORM);
	}
	ai_charge(15);
	ai_melee_torment();
};

void() torment_watk4 = [ 56, torment_watk5 ]
{
	ai_charge(8);
	ai_melee_torment();
};

void() torment_watk5 = [ 57, torment_watk6 ]
{
	torment_footsteps(0.9);
	ai_charge(2);
	ai_melee_torment();
};

void() torment_watk6 = [ 58, torment_watk7 ]
{
	ai_face();
	ai_melee_torment();
};

void() torment_watk7 = [ 59, torment_watk8 ]
{
	ai_face();
};

void() torment_watk8 = [ 60, torment_watk9 ]
{
	self.skin = 0;
	ai_face();
};

void() torment_watk9 = [ 61, torment_run1 ]
{
	ai_face();
};

void() torment_hellstaff1 = [ 62, torment_hellstaff2 ]
{
	self.nextthink = ((time + 0.12) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.skin = 1;
};

void() torment_hellstaff2 = [ 63, torment_hellstaff3 ]
{
	self.nextthink = ((time + 0.12) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() torment_hellstaff3 = [ 64, torment_hellstaff4 ]
{
	self.nextthink = ((time + 0.12) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((skill > 0))
	{
		HellStaff();
	}
};

void() torment_hellstaff4 = [ 65, torment_hellstaff5 ]
{
	self.nextthink = ((time + 0.12) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	HellStaff();
};

void() torment_hellstaff5 = [ 66, torment_hellstaff6 ]
{
	self.nextthink = ((time + 0.12) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	HellStaff();
};

void() torment_hellstaff6 = [ 67, torment_hellstaff7 ]
{
	self.nextthink = ((time + 0.12) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((skill > 1))
	{
		HellStaff();
	}
};

void() torment_hellstaff7 = [ 68, torment_hellstaff8 ]
{
	self.nextthink = ((time + 0.12) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() torment_hellstaff8 = [ 69, torment_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.skin = 0;
};

void() monster_torment =
{
	local entity pain_skin_entity;

	self.classname = "monster_torment";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/torment.mdl");
	setsize(self, VEC_HULL_MIN, '16 16 40');
	if (!self.health)
	{
		self.health = autocvar_torment_health;
	}
	self.health_initial = self.health;
	self.scale = 1;
	self.th_stand = torment_stand1;
	self.th_walk = torment_walk1;
	self.th_run = torment_run1;
	self.th_melee = torment_watk1;
	self.th_missile = torment_hellstaff1;
	self.th_pain = torment_pain;
	self.th_die = torment_die;
	self.classname = "monster_torment";
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
	MonsterPhysics(self, autocvar_tormentmass);
};

void() monster_torment_start =
{
	local entity clone;

	self.scale = 1;
	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_torment;
	clone.nextthink = (time + 0.000100);
};
