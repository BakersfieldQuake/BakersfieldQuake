//Decompiled code. Please respect the original copyright.

void(float loudness) soldier_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.4))
		{
			sound7(self, CHAN_AUTO, "walk/soldier1.wav", loudness, ATTN_IDLE, SNDSPD);
		}
		else
		{
			if ((select <= 0.7))
			{
				sound7(self, CHAN_AUTO, "walk/soldier2.wav", loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_AUTO, "walk/soldier3.wav", loudness, ATTN_IDLE, SNDSPD);
			}
		}
	}
};

void() soldier_reload1a = [ 113, soldier_reload2a ]
{
	ai_stand();
};

void() soldier_reload2a = [ 82, soldier_reload3a ]
{
	ai_stand();
};

void() soldier_reload3a = [ 83, soldier_reload4a ]
{
	ai_stand();
};

void() soldier_reload4a = [ 29, soldier_reload5a ]
{
	ai_stand();
};

void() soldier_reload5a = [ 30, soldier_reload6a ]
{
	ai_stand();
};

void() soldier_reload6a = [ 31, soldier_reload7a ]
{
	ai_stand();
};

void() soldier_reload7a = [ 32, soldier_reload8a ]
{
	ai_stand();
};

void() soldier_reload8a = [ 33, soldier_reload9a ]
{
	ai_stand();
};

void() soldier_reload9a = [ 34, soldier_reload10a ]
{
	ai_stand();
};

void() soldier_reload10a = [ 35, soldier_reload11a ]
{
	ai_stand();
};

void() soldier_reload11a = [ 36, soldier_reload12a ]
{
	ai_stand();
	sound7(self, CHAN_AUTO, "soldier/reload.wav", 0.75, ATTN_IDLE, SNDSPD);
};

void() soldier_reload12a = [ 37, soldier_reload13a ]
{
	ai_stand();
};

void() soldier_reload13a = [ 38, soldier_reload14a ]
{
	ai_stand();
};

void() soldier_reload14a = [ 39, soldier_reload15a ]
{
	ai_stand();
};

void() soldier_reload15a = [ 84, soldier_reload16a ]
{
	ai_stand();
};

void() soldier_reload16a = [ 83, soldier_reload17a ]
{
	ai_stand();
};

void() soldier_reload17a = [ 82, soldier_reload18a ]
{
	ai_stand();
};

void() soldier_reload18a = [ 113, army_stand1 ]
{
	ai_stand();
};

void() soldier_reload1 = [ 113, soldier_reload2 ]
{
	ai_walk(0);
	soldier_footsteps(0.9);
};

void() soldier_reload2 = [ 82, soldier_reload3 ]
{
	ai_walk(0);
};

void() soldier_reload3 = [ 83, soldier_reload4 ]
{
	ai_walk(0);
};

void() soldier_reload4 = [ 29, soldier_reload5 ]
{
	ai_walk(0);
};

void() soldier_reload5 = [ 30, soldier_reload6 ]
{
	ai_walk(0);
};

void() soldier_reload6 = [ 31, soldier_reload7 ]
{
	ai_walk(0);
};

void() soldier_reload7 = [ 32, soldier_reload8 ]
{
	ai_walk(0);
};

void() soldier_reload8 = [ 33, soldier_reload9 ]
{
	ai_walk(0);
};

void() soldier_reload9 = [ 34, soldier_reload10 ]
{
	ai_walk(0);
};

void() soldier_reload10 = [ 35, soldier_reload11 ]
{
	ai_walk(0);
};

void() soldier_reload11 = [ 36, soldier_reload12 ]
{
	ai_walk(0);
	sound7(self, CHAN_AUTO, "soldier/reload.wav", 0.75, ATTN_IDLE, SNDSPD);
};

void() soldier_reload12 = [ 37, soldier_reload13 ]
{
	ai_walk(0);
};

void() soldier_reload13 = [ 38, soldier_reload14 ]
{
	ai_walk(0);
};

void() soldier_reload14 = [ 39, soldier_reload15 ]
{
	ai_walk(0);
};

void() soldier_reload15 = [ 84, soldier_reload16 ]
{
	ai_walk(0);
};

void() soldier_reload16 = [ 83, soldier_reload17 ]
{
	ai_walk(0);
};

void() soldier_reload17 = [ 82, army_walk24 ]
{
	ai_walk(0);
};

void() army_stand1 = [ 0, army_stand2 ]
{
	ai_stand();
};

void() army_stand2 = [ 1, army_stand3 ]
{
	ai_stand();
};

void() army_stand3 = [ 2, army_stand4 ]
{
	ai_stand();
};

void() army_stand4 = [ 3, army_stand5 ]
{
	ai_stand();
};

void() army_stand5 = [ 4, army_stand6 ]
{
	ai_stand();
};

void() army_stand6 = [ 5, army_stand7 ]
{
	ai_stand();
};

void() army_stand7 = [ 6, army_stand8 ]
{
	ai_stand();
};

void() army_stand8 = [ 7, army_stand1 ]
{
	ai_stand();
	if ((autocvar_soldierreloadanim == 1))
	{
		if ((random() <= 0.06))
		{
			soldier_reload1a();
		}
	}
};

void() army_walk1 = [ 90, army_walk2 ]
{
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "soldier/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	ai_walk(1);
};

void() army_walk2 = [ 91, army_walk3 ]
{
	ai_walk(1);
};

void() army_walk3 = [ 92, army_walk4 ]
{
	ai_walk(1);
};

void() army_walk4 = [ 93, army_walk5 ]
{
	ai_walk(1);
};

void() army_walk5 = [ 94, army_walk6 ]
{
	ai_walk(2);
};

void() army_walk6 = [ 95, army_walk7 ]
{
	ai_walk(3);
};

void() army_walk7 = [ 96, army_walk8 ]
{
	ai_walk(4);
};

void() army_walk8 = [ 97, army_walk9 ]
{
	ai_walk(4);
};

void() army_walk9 = [ 98, army_walk10 ]
{
	ai_walk(2);
};

void() army_walk10 = [ 99, army_walk11 ]
{
	ai_walk(2);
};

void() army_walk11 = [ 100, army_walk12 ]
{
	ai_walk(2);
};

void() army_walk12 = [ 101, army_walk13 ]
{
	ai_walk(1);
	soldier_footsteps(0.9);
};

void() army_walk13 = [ 102, army_walk14 ]
{
	ai_walk(0);
};

void() army_walk14 = [ 103, army_walk15 ]
{
	ai_walk(1);
};

void() army_walk15 = [ 104, army_walk16 ]
{
	ai_walk(1);
};

void() army_walk16 = [ 105, army_walk17 ]
{
	ai_walk(1);
};

void() army_walk17 = [ 106, army_walk18 ]
{
	ai_walk(3);
};

void() army_walk18 = [ 107, army_walk19 ]
{
	ai_walk(3);
};

void() army_walk19 = [ 108, army_walk20 ]
{
	ai_walk(3);
};

void() army_walk20 = [ 109, army_walk21 ]
{
	ai_walk(3);
};

void() army_walk21 = [ 110, army_walk22 ]
{
	ai_walk(2);
};

void() army_walk22 = [ 111, army_walk23 ]
{
	ai_walk(1);
};

void() army_walk23 = [ 112, army_walk24 ]
{
	ai_walk(1);
	if ((autocvar_soldierreloadanim == 1))
	{
		if ((random() <= 0.08))
		{
			soldier_reload1();
		}
	}
};

void() army_walk24 = [ 113, army_walk1 ]
{
	ai_walk(1);
	soldier_footsteps(0.9);
};

void() army_run1 = [ 73, army_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "soldier/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	ai_run(11);
};

void() army_run2 = [ 74, army_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(15);
	soldier_footsteps(1);
};

void() army_run3 = [ 75, army_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(10);
};

void() army_run4 = [ 76, army_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(10);
};

void() army_run5 = [ 77, army_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
};

void() army_run6 = [ 78, army_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(15);
	soldier_footsteps(1);
};

void() army_run7 = [ 79, army_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(10);
};

void() army_run8 = [ 80, army_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
};

void() army_atk1 = [ 81, army_atk2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() army_atk2 = [ 82, army_atk3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() army_atk3 = [ 83, army_atk4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() army_atk4 = [ 84, army_atk5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() army_atk5 = [ 85, army_atk6 ]
{
	local vector org;

	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	army_fire();
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if ((autocvar_soldiermuzzleflash == 1))
	{
		makevectors(self.angles);
		org = ((self.origin + (v_up * 17)) + (v_right * 7)) + (v_forward * 17);
		sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
	}
	else
	{
		if ((autocvar_soldiermuzzleflash == 2))
		{
			makevectors(self.angles);
			org = ((self.origin + (v_up * 17)) + (v_right * 5)) + (v_forward * 21);
			sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
		}
		else
		{
			if ((autocvar_soldiermuzzleflash == 3))
			{
				if ((self.model == "progs/soldier.mdl"))
				{
					makevectors(self.angles);
					org = ((self.origin + (v_up * 17)) + (v_right * 7)) + (v_forward * 17);
					sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
				}
				else
				{
					if ((self.model == "progs/soldier1.mdl"))
					{
						makevectors(self.angles);
						org = ((self.origin + (v_up * 17)) + (v_right * 5)) + (v_forward * 21);
						sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
					}
				}
			}
		}
	}
};

void() army_atk6 = [ 86, army_atk7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() army_atk7 = [ 87, army_atk8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	SUB_CheckRefire(army_atk1);
};

void() army_atk8 = [ 88, army_atk9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((autocvar_gruntcasing == 1))
	{
		casing(1);
	}
};

void() army_atk9 = [ 89, army_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	random();
	if ((random() < (0.1 + (skill * 0.05))))
	{
		self.has_fired = 1;
	}
};

void() army_nail1 = [ 81, army_nail2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() army_nail2 = [ 82, army_nail3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() army_nail3 = [ 83, army_nail4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() army_nail4 = [ 84, army_nail5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() army_nail5 = [ 85, army_nail6 ]
{
	local vector org;

	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	army_nailfire();
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if ((autocvar_soldiermuzzleflash == 1))
	{
		makevectors(self.angles);
		org = ((self.origin + (v_up * 12)) + (v_right * 5)) + (v_forward * 19);
		sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
	}
	else
	{
		if ((autocvar_soldiermuzzleflash == 2))
		{
			makevectors(self.angles);
			org = ((self.origin + (v_up * 12)) + (v_right * 5)) + (v_forward * 19);
			sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
		}
		else
		{
			if ((autocvar_soldiermuzzleflash == 3))
			{
				if ((self.model == "progs/soldier.mdl"))
				{
					makevectors(self.angles);
					org = ((self.origin + (v_up * 17)) + (v_right * 7)) + (v_forward * 17);
					sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
				}
				else
				{
					if ((self.model == "progs/soldier1.mdl"))
					{
						makevectors(self.angles);
						org = ((self.origin + (v_up * 17)) + (v_right * 5)) + (v_forward * 21);
						sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
					}
				}
			}
		}
	}
};

void() army_nail6 = [ 87, army_nail7 ]
{
	nailcasing(1);
};

void() army_nail7 = [ 85, army_nail8 ]
{
	local vector org;

	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	army_nailfire();
	random();
	if ((random() < (0.1 + (skill * 0.05))))
	{
		army_nail6();
	}
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if ((autocvar_soldiermuzzleflash == 1))
	{
		makevectors(self.angles);
		org = ((self.origin + (v_up * 12)) + (v_right * 5)) + (v_forward * 19);
		sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
	}
	else
	{
		if ((autocvar_soldiermuzzleflash == 2))
		{
			makevectors(self.angles);
			org = ((self.origin + (v_up * 12)) + (v_right * 5)) + (v_forward * 19);
			sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
		}
		else
		{
			if ((autocvar_soldiermuzzleflash == 3))
			{
				if ((self.model == "progs/soldier.mdl"))
				{
					makevectors(self.angles);
					org = ((self.origin + (v_up * 17)) + (v_right * 7)) + (v_forward * 17);
					sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
				}
				else
				{
					if ((self.model == "progs/soldier1.mdl"))
					{
						makevectors(self.angles);
						org = ((self.origin + (v_up * 17)) + (v_right * 5)) + (v_forward * 21);
						sendParticle("soldier_muzzleflash", org, VEC_ORIGIN, 1);
					}
				}
			}
		}
	}
};

void() army_nail8 = [ 87, army_nail9 ]
{
	if ((autocvar_gruntcasing == 1))
	{
		nailcasing(1);
	}
};

void() army_nail9 = [ 88, army_nail10 ]
{
};

void() army_nail10 = [ 89, army_run1 ]
{
	random();
	if ((random() < (0.1 + (skill * 0.05))))
	{
		self.has_fired = 1;
	}
};

void() army_pain1 = [ 40, army_pain2 ]
{
};

void() army_pain2 = [ 41, army_pain3 ]
{
};

void() army_pain3 = [ 42, army_pain4 ]
{
};

void() army_pain4 = [ 43, army_pain5 ]
{
};

void() army_pain5 = [ 44, army_pain6 ]
{
};

void() army_pain6 = [ 45, army_run1 ]
{
	ai_pain(1);
};

void() army_wounded1 = [ 52, army_wounded2 ]
{
	sendParticle("bleed", self.origin, VEC_ORIGIN, 1, 0);
};

void() army_wounded2 = [ 53, army_wounded3 ]
{
};

void() army_wounded3 = [ 52, army_wounded4 ]
{
};

void() army_wounded4 = [ 53, army_wounded5 ]
{
};

void() army_wounded5 = [ 52, army_wounded6 ]
{
};

void() army_wounded6 = [ 53, army_wounded7 ]
{
	if (((random() * 100) < 30))
	{
		if (((random() * 100) < 40))
		{
			sound7(self, CHAN_VOICE, "soldier/pain2.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "soldier/pain1.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() army_wounded7 = [ 52, army_wounded8 ]
{
};

void() army_wounded8 = [ 53, army_wounded1 ]
{
	if (((random() * 100) < (2 + (skill * 2))))
	{
		army_painb9();
	}
};

void() army_painb1 = [ 46, army_painb2 ]
{
};

void() army_painb2 = [ 47, army_painb3 ]
{
	ai_painforward(13);
};

void() army_painb3 = [ 48, army_painb4 ]
{
	ai_painforward(9);
};

void() army_painb4 = [ 49, army_painb5 ]
{
};

void() army_painb5 = [ 50, army_painb6 ]
{
};

void() army_painb6 = [ 51, army_painb7 ]
{
};

void() army_painb7 = [ 52, army_painb8 ]
{
	if (((random() * 100) > 60))
	{
		setsize(self, VEC_HULL_MIN, '16 16 5');
		army_wounded1();
	}
};

void() army_painb8 = [ 53, army_painb9 ]
{
};

void() army_painb9 = [ 54, army_painb10 ]
{
	setsize(self, ARMY_MIN, ARMY_MAX);
};

void() army_painb10 = [ 55, army_painb11 ]
{
};

void() army_painb11 = [ 56, army_painb12 ]
{
	soldier_footsteps(0.85);
};

void() army_painb12 = [ 57, army_painb13 ]
{
	ai_pain(2);
};

void() army_painb13 = [ 58, army_painb14 ]
{
};

void() army_painb14 = [ 59, army_run1 ]
{
};

void() army_painc1 = [ 60, army_painc2 ]
{
};

void() army_painc2 = [ 61, army_painc3 ]
{
	ai_pain(1);
};

void() army_painc3 = [ 62, army_painc4 ]
{
};

void() army_painc4 = [ 63, army_painc5 ]
{
};

void() army_painc5 = [ 64, army_painc6 ]
{
	ai_painforward(1);
};

void() army_painc6 = [ 65, army_painc7 ]
{
	ai_painforward(1);
};

void() army_painc7 = [ 66, army_painc8 ]
{
};

void() army_painc8 = [ 67, army_painc9 ]
{
	ai_pain(1);
};

void() army_painc9 = [ 68, army_painc10 ]
{
	ai_painforward(4);
};

void() army_painc10 = [ 69, army_painc11 ]
{
	ai_painforward(3);
	soldier_footsteps(0.85);
};

void() army_painc11 = [ 70, army_painc12 ]
{
	ai_painforward(6);
};

void() army_painc12 = [ 71, army_painc13 ]
{
	ai_painforward(8);
};

void() army_painc13 = [ 72, army_run1 ]
{
	soldier_footsteps(0.85);
};

void() army_sdie1 = [ 0, army_sdie1 ]
{
	ThrowHead("progs/gib3.mdl", self.health);
};

void(entity attacker, float damage) army_pain =
{
	local float r;

	if ((((self.health <= 16) && (((self.enemy.weapon != IT_AXE) || (self.enemy.weapon != IT_ROCKET_LAUNCHER)) || (self.enemy.weapon != IT_GRENADE_LAUNCHER))) && (self.enemy.meleeing == 0)))
	{
		if ((self.netname == "nailgrunt"))
		{
			self.model = "progs/soldier1_pain.mdl";
			setmodel(self, "progs/soldier1_pain.mdl");
		}
		else
		{
			self.model = "progs/soldier_pain.mdl";
			setmodel(self, "progs/soldier_pain.mdl");
		}
		setsize(self, ARMY_MIN, ARMY_MAX);
	}
	random();
	if (((skill > 1) && (random() < (0.1 + (skill * 0.05)))))
	{
		self.has_fired = 1;
	}
	if ((self.pain_finished > time))
	{
		return;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_soldier * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	r = random();
	if ((r < 0.2))
	{
		self.pain_finished = (time + 0.6);
		army_pain1();
		sound7(self, CHAN_VOICE, "soldier/pain1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.6))
		{
			self.pain_finished = (time + 1.1);
			army_painb1();
			sound7(self, CHAN_VOICE, "soldier/pain2.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			self.pain_finished = (time + 1.1);
			army_painc1();
			sound7(self, CHAN_VOICE, "soldier/pain2.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() army_fire =
{
	local vector dir;
	local entity en;

	ai_face();
	en = self.enemy;
	if (autocvar_skill_adjusted_soldier_aiming)
	{
		if ((skill == 0))
		{
			dir = en.origin - (en.velocity * 0.2);
		}
		else
		{
			if ((skill == 1))
			{
				dir = en.origin - (en.velocity * 0.15);
			}
			else
			{
				if ((skill == 2))
				{
					dir = en.origin - (en.velocity * 0.1);
				}
				else
				{
					dir = en.origin - (en.velocity * 0.05);
				}
			}
		}
	}
	else
	{
		dir = en.origin - (en.velocity * 0.2);
	}
	dir = normalize((dir - self.origin));
	if ((self.classname == "monster_enforcer"))
	{
		FireBullets_soldier(6, dir, '0.3 0.3 0');
		sound7(self, CHAN_WEAPON, "enforcer/def_ssg_fire.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_WEAPON, "soldier/sattck1.wav", 1, ATTN_NORM, SNDSPD);
		FireBullets_soldier(4, dir, '0.1 0.1 0');
	}
};

void() army_nailfire =
{
	local vector dir;
	local vector org;
	local entity en;

	ai_face();
	en = self.enemy;
	makevectors(self.angles);
	if (autocvar_skill_adjusted_soldier_aiming)
	{
		if ((skill == 0))
		{
			dir = en.origin - (en.velocity * 0.2);
		}
		else
		{
			if ((skill == 1))
			{
				dir = en.origin - (en.velocity * 0.15);
			}
			else
			{
				if ((skill == 2))
				{
					dir = en.origin - (en.velocity * 0.1);
				}
				else
				{
					dir = en.origin - (en.velocity * 0.05);
				}
			}
		}
	}
	else
	{
		dir = en.origin - (en.velocity * 0.2);
	}
	org = ((self.origin + (v_up * 12)) - (v_right * -12)) + (v_forward * 19);
	dir = normalize((dir - org));
	sound7(self, CHAN_WEAPON, "weapons/rocket1i.wav", 1, ATTN_NORM, SNDSPD);
	launch_enemy_spike(org, dir);
	newmis.classname = "gruntspike";
};

void() army_diessg1 = [ 114, army_diessg2 ]
{
};

void() army_diessg2 = [ 115, army_diessg3 ]
{
	sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE, SNDSPD);
	sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
};

void() army_diessg3 = [ 116, army_diessg4 ]
{
	sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	self.solid = 0;
	if ((self.netname == "nailgrunt"))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_diessg4 = [ 117, army_diessg5 ]
{
};

void() army_diessg5 = [ 118, army_diessg6 ]
{
	sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
};

void() army_diessg6 = [ 119, army_diessg7 ]
{
};

void() army_diessg7 = [ 120, army_diessg8 ]
{
	sendParticle("blood_spurt", (self.origin - '0 0 5'), VEC_ORIGIN, 1);
};

void() army_diessg8 = [ 121, army_diessg9 ]
{
};

void() army_diessg9 = [ 122, army_diessg10 ]
{
};

void() army_diessg10 = [ 123, army_diessg11 ]
{
};

void() army_diessg11 = [ 124, army_diessg12 ]
{
};

void() army_diessg12 = [ 125, army_diessg13 ]
{
};

void() army_diessg13 = [ 126, army_diessg14 ]
{
	sendParticle("blood_spurt", (self.origin - '0 0 14'), VEC_ORIGIN, 1);
};

void() army_diessg14 = [ 127, army_diessg14 ]
{
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
};

void() army_shrink1 = [ 40, army_shrink2 ]
{
	self.scale = 0.9;
};

void() army_shrink2 = [ 40, army_shrink3 ]
{
	self.scale = 0.8;
};

void() army_shrink3 = [ 40, army_shrink4 ]
{
	self.scale = 0.7;
};

void() army_shrink4 = [ 41, army_shrink5 ]
{
	self.scale = 0.6;
};

void() army_shrink5 = [ 41, army_shrink6 ]
{
	self.scale = 0.5;
};

void() army_shrink6 = [ 41, army_shrink7 ]
{
	self.scale = 0.4;
};

void() army_shrink7 = [ 41, army_shrink8 ]
{
	self.scale = 0.3;
	self.th_melee = army_sdie1;
	self.th_die = army_sdie1;
	self.health = 1;
};

void() army_shrink8 = [ 42, army_run1 ]
{
	self.scale = 0.2;
	setsize(self, '-6 -6 -10', '6 6 6');
};

void() army_diessgb1 = [ 141, army_diessgb2 ]
{
};

void() army_diessgb2 = [ 142, army_diessgb3 ]
{
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_diessgb3 = [ 143, army_diessgb4 ]
{
	sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	self.solid = 0;
	if ((self.netname == "nailgrunt"))
	{
		self.ammo_nails = 4;
		self.backpack_thrower = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_diessgb4 = [ 144, army_diessgb5 ]
{
	sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
};

void() army_diessgb5 = [ 145, army_diessgb6 ]
{
	sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
};

void() army_diessgb6 = [ 146, army_diessgb7 ]
{
};

void() army_diessgb7 = [ 147, army_diessgb8 ]
{
};

void() army_diessgb8 = [ 148, army_diessgb9 ]
{
};

void() army_diessgb9 = [ 149, army_diessgb10 ]
{
};

void() army_diessgb10 = [ 150, army_diessgb11 ]
{
};

void() army_diessgb11 = [ 151, army_diessgb12 ]
{
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_diessgb12 = [ 152, army_diessgb13 ]
{
	sendParticle("blood_spurt", (self.origin - '0 0 14'), VEC_ORIGIN, 1);
};

void() army_diessgb13 = [ 153, army_diessgb13 ]
{
	sendParticle("blood_spurt_ogre", (self.origin - '0 0 14'), VEC_ORIGIN, 1);
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
};

void() army_dieHS1 = [ 128, army_dieHS2 ]
{
};

void() army_dieHS2 = [ 129, army_dieHS3 ]
{
	sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dieHS3 = [ 130, army_dieHS4 ]
{
	self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
	self.solid = 0;
	if ((self.netname == "nailgrunt"))
	{
		self.ammo_nails = 4;
		self.backpack_thrower = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_dieHS4 = [ 131, army_dieHS5 ]
{
};

void() army_dieHS5 = [ 132, army_dieHS6 ]
{
};

void() army_dieHS6 = [ 133, army_dieHS7 ]
{
};

void() army_dieHS7 = [ 134, army_dieHS8 ]
{
	self.traileffectnum = particleeffectnum(/*1i*/"");
};

void() army_dieHS8 = [ 135, army_dieHS9 ]
{
};

void() army_dieHS9 = [ 136, army_dieHS10 ]
{
};

void() army_dieHS10 = [ 137, army_dieHS11 ]
{
};

void() army_dieHS11 = [ 138, army_dieHS12 ]
{
};

void() army_dieHS12 = [ 139, army_dieHS13 ]
{
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_facepl", self.origin, VEC_ORIGIN, 1);
	}
};

void() army_dieHS13 = [ 140, army_dieHS13 ]
{
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
};

void() army_dieng1 = [ 128, army_dieng2 ]
{
};

void() army_dieng2 = [ 129, army_dieng3 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dieng3 = [ 130, army_dieng4 ]
{
	self.solid = 0;
	if ((self.netname == "nailgrunt"))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_dieng4 = [ 131, army_dieng5 ]
{
};

void() army_dieng5 = [ 132, army_dieng6 ]
{
};

void() army_dieng6 = [ 133, army_dieng7 ]
{
};

void() army_dieng7 = [ 134, army_dieng8 ]
{
};

void() army_dieng8 = [ 135, army_dieng9 ]
{
};

void() army_dieng9 = [ 136, army_dieng10 ]
{
};

void() army_dieng10 = [ 137, army_dieng11 ]
{
};

void() army_dieng11 = [ 138, army_dieng12 ]
{
};

void() army_dieng12 = [ 139, army_dieng13 ]
{
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_facepl", self.origin, VEC_ORIGIN, 1);
	}
};

void() army_dieng13 = [ 140, army_dieng13 ]
{
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
};

void() army_dien1 = [ 8, army_dien2 ]
{
};

void() army_dien2 = [ 9, army_dien3 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dien3 = [ 10, army_dien4 ]
{
	self.solid = 0;
	if ((self.netname == "nailgrunt"))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_dien4 = [ 11, army_dien5 ]
{
};

void() army_dien5 = [ 12, army_dien6 ]
{
};

void() army_dien6 = [ 13, army_dien7 ]
{
};

void() army_dien7 = [ 14, army_dien8 ]
{
	sound7(self, CHAN_AUTO, "soldier/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dien8 = [ 15, army_dien9 ]
{
};

void() army_dien9 = [ 16, army_dien10 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_facepl", self.origin, VEC_ORIGIN, 1);
	}
};

void() army_dien10 = [ 17, army_dien10 ]
{
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
};

void() army_diesng1 = [ 128, army_diesng2 ]
{
};

void() army_diesng2 = [ 129, army_diesng3 ]
{
	sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_diesng3 = [ 130, army_diesng4 ]
{
	self.solid = 0;
	if ((self.netname == "nailgrunt"))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_diesng4 = [ 131, army_diesng5 ]
{
	self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
};

void() army_diesng5 = [ 132, army_diesng6 ]
{
};

void() army_diesng6 = [ 133, army_diesng7 ]
{
};

void() army_diesng7 = [ 134, army_diesng8 ]
{
};

void() army_diesng8 = [ 135, army_diesng9 ]
{
	self.traileffectnum = particleeffectnum(/*1i*/"");
};

void() army_diesng9 = [ 136, army_diesng10 ]
{
};

void() army_diesng10 = [ 137, army_diesng11 ]
{
};

void() army_diesng11 = [ 138, army_diesng12 ]
{
};

void() army_diesng12 = [ 139, army_diesng13 ]
{
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", (self.origin - '0 0 14'), VEC_ORIGIN, 1);
	}
};

void() army_diesng13 = [ 140, army_diesng13 ]
{
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/w_soldiergun.mdl");
};

void() army_dierl1 = [ 154, army_dierl2 ]
{
};

void() army_dierl2 = [ 155, army_dierl3 ]
{
	sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dierl3 = [ 156, army_dierl4 ]
{
	self.solid = 0;
	if (((self.model == "progs/soldier1.mdl") || (self.model == "progs/soldier1_pain.mdl")))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_dierl4 = [ 157, army_dierl5 ]
{
};

void() army_dierl5 = [ 158, army_dierl6 ]
{
};

void() army_dierl6 = [ 159, army_dierl7 ]
{
};

void() army_dierl7 = [ 160, army_dierl8 ]
{
};

void() army_dierl8 = [ 161, army_dierl9 ]
{
};

void() army_dierl9 = [ 162, army_dierl10 ]
{
};

void() army_dierl10 = [ 163, army_dierl11 ]
{
};

void() army_dierl11 = [ 164, army_dierl12 ]
{
};

void() army_dierl12 = [ 165, army_dierl13 ]
{
};

void() army_dierl13 = [ 166, army_dierl14 ]
{
};

void() army_dierl14 = [ 167, army_dierl14 ]
{
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
};

void() army_dieax1 = [ 168, army_dieax2 ]
{
};

void() army_dieax2 = [ 169, army_dieax3 ]
{
	sound7(self, CHAN_AUTO, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dieax3 = [ 170, army_dieax4 ]
{
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
	self.solid = 0;
	if (((self.model == "progs/soldier1.mdl") || (self.model == "progs/soldier1_pain.mdl")))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_dieax4 = [ 171, army_dieax5 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dieax5 = [ 172, army_dieax6 ]
{
	if ((autocvar_bloodextension == 1))
	{
		self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
	}
};

void() army_dieax6 = [ 173, army_dieax7 ]
{
};

void() army_dieax7 = [ 174, army_dieax8 ]
{
};

void() army_dieax8 = [ 175, army_dieax9 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dieax9 = [ 176, army_dieax10 ]
{
};

void() army_dieax10 = [ 177, army_dieax11 ]
{
};

void() army_dieax11 = [ 178, army_dieax12 ]
{
};

void() army_dieax12 = [ 179, army_dieax13 ]
{
};

void() army_dieax13 = [ 180, army_dieax14 ]
{
	self.traileffectnum = particleeffectnum(/*1i*/"");
};

void() army_dieax14 = [ 181, army_dieax15 ]
{
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dieax15 = [ 182, army_dieax16 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dieax16 = [ 183, army_dieax17 ]
{
};

void() army_dieax17 = [ 184, army_dieax18 ]
{
};

void() army_dieax18 = [ 185, army_dieax18 ]
{
	if ((autocvar_soldiercorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_soldiercorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_soldiercorpsehealth, "progs/gib_soldfoot1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_soldiercorpsehealth, "progs/gib_soldfoot2.mdl");
	}
};

void() army_dieaxb1 = [ 187, army_dieaxb2 ]
{
};

void() army_dieaxb2 = [ 188, army_dieaxb3 ]
{
	sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dieaxb3 = [ 189, army_dieaxb4 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
	self.solid = 0;
	if (((self.model == "progs/soldier1.mdl") || (self.model == "progs/soldier1_pain.mdl")))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_dieaxb4 = [ 190, army_dieaxb5 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dieaxb5 = [ 191, army_dieaxb6 ]
{
	if ((autocvar_bloodextension == 1))
	{
		CeilSplat();
	}
	self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
};

void() army_dieaxb6 = [ 192, army_dieaxb7 ]
{
	if ((autocvar_bloodextension == 1))
	{
		CeilSplat();
	}
};

void() army_dieaxb7 = [ 193, army_dieaxb8 ]
{
	if ((autocvar_bloodextension == 1))
	{
		CeilSplat();
	}
};

void() army_dieaxb8 = [ 194, army_dieaxb9 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		CeilSplat();
	}
};

void() army_dieaxb9 = [ 195, army_dieaxb10 ]
{
};

void() army_dieaxb10 = [ 196, army_dieaxb11 ]
{
	self.traileffectnum = particleeffectnum(/*1i*/"");
};

void() army_dieaxb11 = [ 197, army_dieaxb12 ]
{
};

void() army_dieaxb12 = [ 198, army_dieaxb13 ]
{
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_dieaxb13 = [ 199, army_dieaxb13 ]
{
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_knightcorpsehealth, "progs/gib_soldfoot2.mdl");
	}
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
};

void() army_dieburn1 = [ 8, army_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
};

void() army_dieburn2 = [ 9, army_dieburn3 ]
{
	self.burnz_origin = 11;
};

void() army_dieburn3 = [ 10, army_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
	if ((self.netname == "nailgrunt"))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_dieburn4 = [ 11, army_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() army_dieburn5 = [ 12, army_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() army_dieburn6 = [ 13, army_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() army_dieburn7 = [ 14, army_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() army_dieburn8 = [ 15, army_dieburn9 ]
{
	self.burnz_origin = -6;
};

void() army_dieburn9 = [ 16, army_dieburn10 ]
{
	self.burnz_origin = -8;
};

void() army_dieburn10 = [ 17, army_dieburn10 ]
{
	self.burnz_origin = -10;
};

void() army_die1 = [ 8, army_die2 ]
{
};

void() army_die2 = [ 9, army_die3 ]
{
	if ((self.model == "progs/soldier.mdl"))
	{
		ThrowGib("progs/gib_soldarm.mdl", self.health);
	}
};

void() army_die3 = [ 10, army_die4 ]
{
	ai_back(5);
	self.solid = 0;
	if ((self.netname == "nailgrunt"))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
	ai_back(5);
};

void() army_die4 = [ 11, army_die5 ]
{
	ai_back(5);
	if (((self.enemy.weapon == IT_SUPER_SHOTGUN) || (self.enemy.weapon == IT_SHOTGUN)))
	{
		ai_face();
	}
};

void() army_die5 = [ 12, army_die6 ]
{
};

void() army_die6 = [ 13, army_die7 ]
{
};

void() army_die7 = [ 14, army_die8 ]
{
	sound7(self, CHAN_AUTO, "soldier/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_die8 = [ 15, army_die9 ]
{
};

void() army_die9 = [ 16, army_die10 ]
{
};

void() army_die10 = [ 17, army_die10 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 20;
	if ((autocvar_soldiercorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_soldiercorpsehealth, "progs/h_guard.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_soldiercorpsehealth, "progs/h_guard1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_soldierrandomness = autocvar_soldierrandomness * 0.01;
		if ((autocvar_soldier == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_soldierrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_soldier == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_soldierrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/soldier.mdl", 17, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/soldier1.mdl", 17, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_soldier == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_soldierrandomness))
					{
						vengeance_soldier("progs/soldier.mdl", 17);
					}
				}
				else
				{
					if ((autocvar_soldier == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_soldierrandomness))
						{
							zufall = random();
							if ((zufall > 0.64))
							{
								ghost_die();
							}
							else
							{
								if ((zufall < 0.26))
								{
									if ((self.monstermodel == 0))
									{
										soul("progs/soldier.mdl", 17, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/soldier1.mdl", 17, zet);
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
};

void() army_cdie1 = [ 18, army_cdie2 ]
{
	if (((self.enemy.weapon == IT_SUPER_SHOTGUN) || (self.enemy.weapon == IT_SHOTGUN)))
	{
		ai_face();
	}
};

void() army_cdie2 = [ 19, army_cdie3 ]
{
	ai_back(5);
};

void() army_cdie3 = [ 20, army_cdie4 ]
{
	self.solid = 0;
	if ((self.netname == "nailgrunt"))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
	ai_back(4);
};

void() army_cdie4 = [ 21, army_cdie5 ]
{
	ai_back(13);
};

void() army_cdie5 = [ 22, army_cdie6 ]
{
	ai_back(3);
};

void() army_cdie6 = [ 23, army_cdie7 ]
{
	ai_back(4);
};

void() army_cdie7 = [ 24, army_cdie8 ]
{
};

void() army_cdie8 = [ 25, army_cdie9 ]
{
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() army_cdie9 = [ 26, army_cdie10 ]
{
};

void() army_cdie10 = [ 27, army_cdie11 ]
{
};

void() army_cdie11 = [ 28, army_cdie11 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 20;
	if ((autocvar_soldiercorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_soldiercorpsehealth, "progs/h_guard.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_soldiercorpsehealth, "progs/h_guard1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_soldierrandomness = autocvar_soldierrandomness * 0.01;
		if ((autocvar_soldier == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_soldierrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_soldier == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_soldierrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/soldier.mdl", 28, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/soldier1.mdl", 28, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_soldier == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_soldierrandomness))
					{
						vengeance_soldier("progs/soldier.mdl", 28);
					}
				}
				else
				{
					if ((autocvar_soldier == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_soldierrandomness))
						{
							zufall = random();
							if ((zufall > 0.64))
							{
								ghost_die();
							}
							else
							{
								if ((zufall < 0.26))
								{
									if ((self.monstermodel == 0))
									{
										soul("progs/soldier.mdl", 28, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/soldier1.mdl", 28, zet);
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
};

void(float maxgibs, float gibscounter) producegibs_grunt =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/gib_4.mdl", self.health);
		ThrowGib("progs/gib_5.mdl", self.health);
		ThrowGib("progs/gib_soldfoot1.mdl", self.health);
		ThrowGib("progs/gib_soldfoot2.mdl", self.health);
		ThrowGib("progs/gib_soldarm.mdl", self.health);
		ThrowWeapon("progs/w_soldiergun.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_grunt(maxgibs, gibscounter);
};

void() army_pack =
{
	if ((self.netname == "nailgrunt"))
	{
		self.ammo_nails = 4;
		if ((self.attack_chance > 0))
		{
			self.ammo_nails = 6;
		}
		self.backpack_thrower = 4;
	}
	else
	{
		self.ammo_shells = autocvar_backpack_soldier_shells;
		self.backpack_thrower = 1;
	}
	DropBackpack();
};

void() army_lightning_death = [ 46, army_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() army_lightning_death1 = [ 46, army_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(1, "progs/h_guard.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(1, "progs/h_guard1.mdl");
	}
};

void() army_inflamed1 = [ 73, army_inflamed2 ]
{
	local float r;

	ai_run_inflamed(11);
	self.nextthink = (time + 0.07);
	r = random();
	if ((r < 0.3))
	{
		sound7(self, CHAN_VOICE, "misc/burn1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.82))
		{
			sound7(self, CHAN_VOICE, "misc/burn2.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() army_inflamed2 = [ 74, army_inflamed3 ]
{
	ai_run_inflamed(15);
	soldier_footsteps(1);
	self.nextthink = (time + 0.07);
};

void() army_inflamed3 = [ 75, army_inflamed4 ]
{
	ai_run_inflamed(10);
	self.nextthink = (time + 0.07);
};

void() army_inflamed4 = [ 76, army_inflamed5 ]
{
	ai_run_inflamed(10);
	self.nextthink = (time + 0.07);
};

void() army_inflamed5 = [ 77, army_inflamed6 ]
{
	ai_run_inflamed(8);
	self.nextthink = (time + 0.07);
};

void() army_inflamed6 = [ 78, army_inflamed7 ]
{
	ai_run_inflamed(15);
	soldier_footsteps(1);
	self.nextthink = (time + 0.07);
};

void() army_inflamed7 = [ 79, army_inflamed8 ]
{
	ai_run_inflamed(10);
	self.nextthink = (time + 0.07);
};

void() army_inflamed8 = [ 80, army_inflamed1 ]
{
	local float r;

	ai_run_inflamed(8);
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		army_die();
		return;
	}
	r = random();
	if ((r < 0.27))
	{
		army_inflamed9();
	}
	else
	{
		if ((r < 0.44))
		{
			army_inflamed18();
		}
	}
};

void() army_inflamed9 = [ 60, army_inflamed10 ]
{
	local float r;

	self.nextthink = (time + 0.07);
	r = random();
	if ((r < 0.3))
	{
		sound7(self, CHAN_VOICE, "misc/burn1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.82))
		{
			sound7(self, CHAN_VOICE, "misc/burn2.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() army_inflamed10 = [ 61, army_inflamed11 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed11 = [ 62, army_inflamed12 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed12 = [ 63, army_inflamed13 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed13 = [ 64, army_inflamed14 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed14 = [ 65, army_inflamed15 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed15 = [ 64, army_inflamed16 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed16 = [ 63, army_inflamed17 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed17 = [ 60, army_inflamed1 ]
{
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		army_die();
		return;
	}
};

void() army_inflamed18 = [ 60, army_inflamed19 ]
{
	local float r;

	self.nextthink = (time + 0.07);
	r = random();
	if ((r < 0.3))
	{
		sound7(self, CHAN_VOICE, "misc/burn1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.82))
		{
			sound7(self, CHAN_VOICE, "misc/burn2.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() army_inflamed19 = [ 46, army_inflamed20 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed20 = [ 47, army_inflamed21 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed21 = [ 48, army_inflamed22 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed22 = [ 49, army_inflamed23 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed23 = [ 50, army_inflamed24 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed24 = [ 57, army_inflamed25 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed25 = [ 58, army_inflamed26 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed26 = [ 59, army_inflamed27 ]
{
	self.nextthink = (time + 0.07);
};

void() army_inflamed27 = [ 60, army_inflamed1 ]
{
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		army_die();
		return;
	}
};

void() army_die =
{
	local float maxgibs;
	local float gibscounter;
	local float zufa;
	local float zufall;
	local float randomness;

	bodyCheck();
	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			army_pack();
			army_lightning_death();
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
	if ((((!self.shocked && (self.enemy.meleeing || self.axhitme)) && (autocvar_berserkmode > 0)) && (random() < 0.3)))
	{
		self.health = -10;
	}
	if (((self.health < -40) || ((self.enemy.weapon == IT_CHAINSAW) && (random() < 0.35))))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_soldier * 0.01)))
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
		if ((self.monstermodel == 0))
		{
			ThrowHead("progs/h_guard.mdl", self.health);
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				ThrowHead("progs/h_guard1.mdl", self.health);
			}
		}
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		gibdeath_effects();
		producegibs_grunt(maxgibs, gibscounter);
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
				army_inflamed1();
				return;
			}
		}
		else
		{
			sound7(self, CHAN_VOICE, "soldier/death1.wav", 1, ATTN_NORM, SNDSPD);
			if ((random() < 0.5))
			{
				army_die1();
			}
			else
			{
				army_cdie1();
			}
			return;
		}
	}
	autocvar_soldierrandomness = autocvar_soldierrandomness * 0.01;
	if ((autocvar_soldier == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_soldierrandomness))
		{
			self.delete_painskin = 1;
			army_dieburn1();
			return;
		}
	}
	if ((autocvar_soldier == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_soldierrandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				army_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_soldier * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "soldier/death1.wav", 1, ATTN_NORM, SNDSPD);
	if ((random() < 0.5))
	{
		army_die1();
	}
	else
	{
		army_cdie1();
	}
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	if ((self.enemy.meleeing == 0))
	{
		if (((((random() * 100) < 70) && (self.hitbox_pos == HEAD_SHOT)) && (self.enemy.weapon != IT_SUPER_NAILGUN)))
		{
			ThrowGib("progs/gib_splat.mdl", self.health);
			ThrowGib("progs/gib_splat.mdl", self.health);
			if ((random() < 0.2))
			{
				ThrowGib("progs/gib_skull.mdl", self.health);
			}
			else
			{
				ThrowGib("progs/gib_soldhead.mdl", self.health);
			}
			self.delete_painskin = 1;
			if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
			{
				self.model = "progs/soldier_headshot.mdl";
				setmodel(self, "progs/soldier_headshot.mdl");
				self.skin = 1;
			}
			else
			{
				self.model = "progs/soldier_headshot.mdl";
				setmodel(self, "progs/soldier_headshot.mdl");
				self.skin = 0;
			}
			setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
			army_dieHS1();
			sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
			return;
		}
		if ((self.enemy.weapon == IT_SHOTGUN))
		{
			if ((random() > 0.5))
			{
				self.delete_painskin = 1;
				if (((self.model == "progs/soldier_pain.mdl") || (self.model == "progs/soldier.mdl")))
				{
					self.model = "progs/soldier_sg.mdl";
					setmodel(self, "progs/soldier_sg.mdl");
				}
				else
				{
					self.model = "progs/soldier1_sg.mdl";
					setmodel(self, "progs/soldier1_sg.mdl");
				}
			}
		}
		if ((self.enemy.weapon == IT_SUPER_SHOTGUN))
		{
			self.delete_painskin = 1;
			if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
			{
				self.model = "progs/soldier_sg.mdl";
				setmodel(self, "progs/soldier_sg.mdl");
				ssgpower = 120;
			}
			else
			{
				ssgpower = 120;
				self.model = "progs/soldier1_sg.mdl";
				setmodel(self, "progs/soldier1_sg.mdl");
			}
			if (((random() > 0.4) && (random() < 0.7)))
			{
				if ((autocvar_bloodextension == 1))
				{
					sendParticle("blood_blast", self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ssgpower = 0;
				self.delete_painskin = 1;
				if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
				{
					self.model = "progs/soldierblast.mdl";
					setmodel(self, "progs/soldierblast.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/soldierblast.mdl";
					setmodel(self, "progs/soldierblast.mdl");
					self.skin = 1;
				}
				army_diessgb1();
			}
			else
			{
				if ((random() <= 0.4))
				{
					if ((autocvar_bloodextension == 1))
					{
						sendParticle("blood_monster_gib", self.origin, VEC_ORIGIN, 1);
					}
					ThrowWeapon("progs/w_soldiergun.mdl", self.health);
					CeilSplat();
					CeilSplat();
					CeilSplat();
					CeilSplat();
					CeilSplat();
					ssgpower = 0;
					if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
					{
						ThrowGib("progs/h_guardbl.mdl", self.health);
					}
					else
					{
						ThrowGib("progs/gib_soldarm.mdl", self.health);
						ThrowGib("progs/h_guard1bl.mdl", self.health);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					self.delete_painskin = 1;
					self.model = "progs/soldierblown.mdl";
					setmodel(self, "progs/soldierblown.mdl");
					army_diessg1();
				}
				else
				{
					if ((random() > 0.8))
					{
						if ((autocvar_bloodextension == 1))
						{
							sendParticle("blood_blast", self.origin, VEC_ORIGIN, 1);
						}
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/gib_skull.mdl", self.health);
						ThrowGib("progs/gib_ribs.mdl", self.health);
						ssgpower = 0;
						self.delete_painskin = 1;
						if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
						{
							self.model = "progs/soldiersplat.mdl";
							setmodel(self, "progs/soldiersplat.mdl");
							self.skin = 0;
						}
						else
						{
							self.model = "progs/soldiersplat.mdl";
							setmodel(self, "progs/soldiersplat.mdl");
							self.skin = 1;
						}
						army_diessgb1();
					}
				}
			}
		}
		if ((self.enemy.weapon == IT_NAILGUN))
		{
			if ((random() < 0.5))
			{
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
				{
					self.model = "progs/soldiernail.mdl";
					setmodel(self, "progs/soldiernail.mdl");
					self.skin = 1;
				}
				else
				{
					self.model = "progs/soldiernail.mdl";
					setmodel(self, "progs/soldiernail.mdl");
					self.skin = 0;
				}
				army_dieng1();
			}
			else
			{
				if (((random() > 0.5) && (random() < 0.9)))
				{
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					self.delete_painskin = 1;
					if ((self.model == "progs/soldier.mdl"))
					{
						self.model = "progs/soldiernail.mdl";
						setmodel(self, "progs/soldiernail.mdl");
						self.skin = 1;
					}
					else
					{
						self.model = "progs/soldiernail.mdl";
						setmodel(self, "progs/soldiernail.mdl");
						self.skin = 0;
					}
					army_dien1();
				}
			}
			setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
			return;
		}
		if ((self.enemy.weapon == IT_SUPER_NAILGUN))
		{
			if ((self.hitbox_pos == HEAD_SHOT))
			{
				if ((autocvar_bloodextension == 1))
				{
					sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
				{
					self.model = "progs/soldier_headshot.mdl";
					setmodel(self, "progs/soldier_headshot.mdl");
					self.skin = 1;
					StickGib("progs/gib_soldhead.mdl", 1);
				}
				else
				{
					self.model = "progs/soldier_headshot.mdl";
					setmodel(self, "progs/soldier_headshot.mdl");
					self.skin = 0;
					StickGib("progs/gib_soldhead.mdl", 1);
				}
				army_dieHS1();
				return;
			}
			else
			{
				if ((random() > 0.5))
				{
					if ((autocvar_bloodextension == 1))
					{
						sendParticle("blood_blast", self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					self.delete_painskin = 1;
					if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
					{
						self.model = "progs/soldier_supernail.mdl";
						setmodel(self, "progs/soldier_supernail.mdl");
						self.skin = 1;
						if ((random() < 0.3))
						{
							StickGib("progs/gib_soldnail_b.mdl", 1);
						}
						else
						{
							StickGib("progs/gib_soldnail.mdl", 1);
						}
					}
					else
					{
						self.model = "progs/soldier_supernail.mdl";
						setmodel(self, "progs/soldier_supernail.mdl");
						self.skin = 0;
						if ((random() < 0.3))
						{
							StickGib("progs/gib_soldnail_b.mdl", 1);
						}
						else
						{
							StickGib("progs/gib_soldnail.mdl", 0);
						}
					}
				}
				else
				{
					if ((autocvar_bloodextension == 1))
					{
						sendParticle("blood_blast", self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					self.delete_painskin = 1;
					if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
					{
						self.model = "progs/soldier_supernail.mdl";
						setmodel(self, "progs/soldier_supernail.mdl");
						if ((random() < 0.3))
						{
							StickGib("progs/gib_soldnail_b.mdl", 1);
						}
						else
						{
							if ((random() < 0.7))
							{
								ThrowGib("progs/gib_soldnail_b.mdl", (self.health * 3));
								StickGib("progs/gib_soldarm_nail.mdl", 0);
							}
							else
							{
								StickGib("progs/gib_soldnail2.mdl", 1);
							}
						}
						self.skin = 1;
					}
					else
					{
						if ((random() < 0.3))
						{
							StickGib("progs/gib_soldnail_b.mdl", 1);
						}
						else
						{
							if ((random() < 0.7))
							{
								ThrowGib("progs/gib_soldnail_b.mdl", (self.health * 3));
								StickGib("progs/gib_soldarm_nail.mdl", 0);
							}
							else
							{
								StickGib("progs/gib_soldnail2.mdl", 0);
							}
						}
						self.model = "progs/soldier_supernail.mdl";
						setmodel(self, "progs/soldier_supernail.mdl");
						self.skin = 0;
					}
				}
			}
			army_diesng1();
		}
		if ((self.enemy.weapon == IT_ROCKET_LAUNCHER))
		{
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			if ((autocvar_bloodextension == 1))
			{
				sendParticle("blood_monster_gib", self.origin, VEC_ORIGIN, 1);
			}
			ThrowGib("progs/chop.mdl", self.health);
			ThrowGib("progs/chop.mdl", self.health);
			ThrowGib("progs/chop.mdl", self.health);
			ThrowGib("progs/gib2.mdl", self.health);
			ThrowGib("progs/gib_soldarm.mdl", self.health);
			ThrowGib("progs/gib_soldfoot1.mdl", self.health);
			ThrowWeapon("progs/w_soldiergun.mdl", self.health);
			self.delete_painskin = 1;
			if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
			{
				self.model = "progs/soldiergib.mdl";
				setmodel(self, "progs/soldiergib.mdl");
				self.skin = 0;
			}
			else
			{
				self.model = "progs/soldiergib.mdl";
				setmodel(self, "progs/soldiergib.mdl");
				self.skin = 1;
			}
			army_dierl1();
		}
		if (((self.enemy.weapon == IT_AXE) || (self.enemy.weapon == IT_CHAINSAW)))
		{
			if ((self.hitbox_pos == HEAD_SHOT))
			{
				ThrowGib("progs/gib_splat.mdl", self.health);
				ThrowGib("progs/gib_splat.mdl", self.health);
				if ((random() < 0.2))
				{
					ThrowGib("progs/gib_skull.mdl", self.health);
				}
				else
				{
					ThrowGib("progs/gib_soldhead.mdl", self.health);
				}
				sendParticle("blood_spurt", (self.origin + '0 0 8'), VEC_ORIGIN, 2);
				self.delete_painskin = 1;
				if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
				{
					self.model = "progs/soldier_headshot.mdl";
					setmodel(self, "progs/soldier_headshot.mdl");
					self.skin = 1;
				}
				else
				{
					self.model = "progs/soldier_headshot.mdl";
					setmodel(self, "progs/soldier_headshot.mdl");
					self.skin = 0;
				}
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				army_dieHS1();
				sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
				return;
			}
			else
			{
				if ((random() > 0.8))
				{
					if ((autocvar_bloodextension == 1))
					{
						sendParticle("blood_spurt_corpse", self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					ThrowWeapon("progs/w_soldiergun.mdl", self.health);
					self.delete_painskin = 1;
					if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
					{
						self.model = "progs/soldieraxe2.mdl";
						setmodel(self, "progs/soldieraxe2.mdl");
						self.skin = 0;
					}
					else
					{
						self.model = "progs/soldieraxe2.mdl";
						setmodel(self, "progs/soldieraxe2.mdl");
						self.skin = 1;
					}
					army_dieaxb1();
					ThrowGib("progs/chop.mdl", self.health);
				}
				else
				{
					if (((random() > 0.4) && (random() < 0.8)))
					{
						if ((autocvar_bloodextension == 1))
						{
							sendParticle("blood_blast", self.origin, VEC_ORIGIN, 1);
						}
						ThrowWeapon("progs/w_soldiergun.mdl", self.health);
						if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
						{
							ThrowGib("progs/h_guardbl.mdl", self.health);
						}
						else
						{
							ThrowGib("progs/gib_soldarm.mdl", self.health);
							ThrowGib("progs/h_guard1bl.mdl", self.health);
						}
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/chop.mdl", self.health);
						self.delete_painskin = 1;
						army_diessg1();
						self.model = "progs/soldierblown.mdl";
						setmodel(self, "progs/soldierblown.mdl");
					}
					else
					{
						if ((autocvar_bloodextension == 1))
						{
							sendParticle("blood_blast", self.origin, VEC_ORIGIN, 1);
						}
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/chop.mdl", self.health);
						self.delete_painskin = 1;
						if (((self.model == "progs/soldier.mdl") || (self.model == "progs/soldier_pain.mdl")))
						{
							self.model = "progs/soldieraxe.mdl";
							setmodel(self, "progs/soldieraxe.mdl");
							self.skin = 0;
						}
						else
						{
							self.model = "progs/soldieraxe.mdl";
							setmodel(self, "progs/soldieraxe.mdl");
							self.skin = 1;
						}
						army_dieax1();
						ThrowGib("progs/chop.mdl", self.health);
					}
				}
			}
		}
		setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	}
};

void() monster_army =
{
	local float zufall;
	local float zuffa;
	local float replacer;
	local vector check;
	local float replacez;
	local float replac;
	local entity pain_skin_entity;
	local float repla;
	local float replace;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/soldier.mdl");
	precache_model("progs/h_guard.mdl");
	precache_model("progs/gib1.mdl");
	precache_model("progs/gib2.mdl");
	precache_model("progs/gib3.mdl");
	precache_model("progs/gib_soldfoot1.mdl");
	precache_model("progs/gib_soldfoot2.mdl");
	precache_model("progs/gib_soldnail.mdl");
	precache_model("progs/gib_soldnail2.mdl");
	precache_model("progs/gib_soldnail_b.mdl");
	precache_model("progs/gib_soldarm.mdl");
	precache_model("progs/gib_soldarm_nail.mdl");
	precache_model("progs/gib_soldhead.mdl");
	precache_model("progs/soldier_headshot.mdl");
	precache_model("progs/soldierblown.mdl");
	precache_model("progs/soldierblast.mdl");
	precache_model("progs/soldieraxe.mdl");
	precache_model("progs/soldieraxe2.mdl");
	precache_model("progs/soldiergib.mdl");
	precache_model("progs/h_guardbl.mdl");
	precache_model("progs/h_guard1bl.mdl");
	precache_model("progs/soldiernail.mdl");
	precache_model("progs/soldier_supernail.mdl");
	precache_model("progs/soldiersplat.mdl");
	precache_sound("soldier/death1.wav");
	precache_sound("soldier/idle.wav");
	precache_sound("soldier/pain1.wav");
	precache_sound("soldier/pain2.wav");
	precache_sound("soldier/sattck1.wav");
	precache_sound("soldier/sight1.wav");
	precache_sound("soldier/fall_backwards.wav");
	precache_sound("soldier/fall_forwards.wav");
	precache_sound("soldier/reload.wav");
	precache_sound("walk/soldier1.wav");
	precache_sound("walk/soldier2.wav");
	precache_sound("walk/soldier3.wav");
	precache_sound("player/udeath.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.noise = "soldier/pain1.wav";
	self.netname = "monster_army";
	if ((autocvar_soldiermultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/soldier.mdl");
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
		if ((autocvar_soldiermultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/soldier1.mdl");
			precache_model("progs/h_guard1.mdl");
			zufall = random();
			if (((self.spawnflags & 2) || ((zufall >= 0.5) && ((self.classname != "monster_army_rocket") && (self.classname != "monster_army_spike")))))
			{
				setmodel(self, "progs/soldier.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				if (((self.classname == "monster_army_rocket") || (self.classname == "monster_army_spike")))
				{
					self.classname = "monster_army";
				}
				setmodel(self, "progs/soldier1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
				self.netname = "nailgrunt";
			}
		}
		else
		{
			if ((autocvar_soldiermultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/soldier1.mdl");
				precache_model("progs/h_guard1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/soldier.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/soldier.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/soldier1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
						self.netname = "nailgrunt";
					}
				}
			}
			else
			{
				if ((autocvar_soldiermultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/soldier1.mdl");
					precache_model("progs/h_guard1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/soldier.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/soldier.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/soldier1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
								self.netname = "nailgrunt";
							}
							else
							{
								setmodel(self, "progs/soldier1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
								self.netname = "nailgrunt";
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/soldier.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_soldier_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.14;
			self.sizediff = '0 0 3';
			setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.07;
				self.sizediff = '0 0 1';
				setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
			}
			else
			{
				self.scale = 1;
				setsize(self, ARMY_MIN, ARMY_MAX);
			}
		}
	}
	else
	{
		if ((autocvar_soldier_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.21;
				self.sizediff = '0 0 5';
				setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.14;
					self.sizediff = '0 0 3';
					setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.75))
					{
						self.scale = 1.07;
						self.sizediff = '0 0 1';
						setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, ARMY_MIN, ARMY_MAX);
					}
				}
			}
		}
		else
		{
			if ((autocvar_soldier_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.28;
					self.sizediff = '0 0 7';
					setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.21;
						self.sizediff = '0 0 5';
						setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.14;
							self.sizediff = '0 0 3';
							setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.07;
								self.sizediff = '0 0 1';
								setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
							}
							else
							{
								self.scale = 1;
								setsize(self, ARMY_MIN, ARMY_MAX);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_soldier_size == 4))
				{
					zuffa = random();
					if ((zuffa <= 0.17))
					{
						self.scale = 1.35;
						self.sizediff = '0 0 9';
						setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.34))
						{
							self.scale = 1.28;
							self.sizediff = '0 0 7';
							setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.5))
							{
								self.scale = 1.21;
								self.sizediff = '0 0 5';
								setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
							}
							else
							{
								if ((zuffa <= 0.67))
								{
									self.scale = 1.14;
									self.sizediff = '0 0 3';
									setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
								}
								else
								{
									if ((zuffa <= 0.84))
									{
										self.scale = 1.07;
										self.sizediff = '0 0 1';
										setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
									}
									else
									{
										self.scale = 1;
										setsize(self, ARMY_MIN, ARMY_MAX);
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_soldier_size > 4))
					{
						if ((autocvar_soldier_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_soldier_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_soldier_size * 0.25);
						self.sizediff = self.sizefactor;
						setsize(self, (ARMY_MIN - self.sizediff), (ARMY_MAX - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, ARMY_MIN, ARMY_MAX);
					}
				}
			}
		}
	}
	if ((autocvar_soldier_size_influenced_health == 1))
	{
		self.health = (autocvar_soldier_health + ((self.scale - 1) * 100));
	}
	else
	{
		self.health = autocvar_soldier_health;
	}
	if ((cvar("skill") == 3))
	{
		self.health = 45;
	}
	else
	{
		self.health = 35;
	}
	if ((random() < 0.35))
	{
		self.attack_chance = 0.5;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_soldier_random_skin_colors))
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
	self.th_stand = army_stand1;
	self.th_walk = army_walk1;
	self.th_run = army_run1;
	if ((self.netname == "nailgrunt"))
	{
		self.th_missile = army_nail1;
	}
	else
	{
		self.th_missile = army_atk1;
	}
	self.th_pain = army_pain;
	self.th_die = army_die;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_spider_replace_soldier)
	{
		replacer = autocvar_spider_replace_soldier * 0.01;
		if ((random() <= replacer))
		{
			check = (self.origin - '0 0 20') + '0 0 1';
			if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
			{
				self.skin = 0;
				self.health = 40;
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 40');
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_spider_start();
				return;
			}
		}
	}
	if (autocvar_reiver_replace_soldier)
	{
		replacez = autocvar_reiver_replace_soldier * 0.01;
		if ((random() <= replacez))
		{
			self.health = 50;
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_reiver_liftorigin_start();
			return;
		}
	}
	if (autocvar_afrit_replace_soldier)
	{
		replac = autocvar_afrit_replace_soldier * 0.01;
		if ((random() <= replac))
		{
			self.health = 50;
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_afrit_liftorigin_start();
			return;
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
	walkmonster_start();
	do_the_cloning();
	if (autocvar_reiver_supports_soldier)
	{
		repla = autocvar_reiver_supports_soldier * 0.01;
		if ((random() <= repla))
		{
			add_reiver_support_walk();
		}
	}
	if (autocvar_afrit_supports_soldier)
	{
		replace = autocvar_afrit_supports_soldier * 0.01;
		if ((random() <= replace))
		{
			add_afrit_support_walk();
		}
	}
	if (((random() < ((0.02 + (cvar("skill") * 0.01)) + (cvar("quadreplacer") * 0.015))) && (self.classname != "monster_enforcer")))
	{
		add_jim_support_walk();
	}
	MonsterPhysics(self, autocvar_soldiermass);
};

void() monster_army_rocket =
{
	monster_army();
};

void() monster_army_spike =
{
	monster_army();
};

void() vengeance_soldier_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_soldier_shoot =
{
	local float shootdmg;

	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		shootdmg = 1;
		T_Damage(self.enemy, self, self, shootdmg);
	}
	self.touch = SUB_Null;
};

void() vengeance_soldier_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_soldier_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_run1 = [ 73, vengeance_soldier_run2 ]
{
	ai_face();
	movetogoal(15);
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_run2 = [ 74, vengeance_soldier_run3 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.36;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_run3 = [ 75, vengeance_soldier_run4 ]
{
	ai_face();
	movetogoal(14);
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.33;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_run4 = [ 76, vengeance_soldier_run5 ]
{
	ai_face();
	movetogoal(17);
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_run5 = [ 77, vengeance_soldier_run6 ]
{
	ai_face();
	movetogoal(12);
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.27;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_run6 = [ 78, vengeance_soldier_run7 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.24;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_run7 = [ 79, vengeance_soldier_run8 ]
{
	ai_face();
	movetogoal(14);
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.21;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_run8 = [ 80, vengeance_soldier_shoot1 ]
{
	ai_face();
	movetogoal(12);
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_shoot1 = [ 81, vengeance_soldier_shoot2 ]
{
	ai_face();
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.17;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_shoot2 = [ 82, vengeance_soldier_shoot3 ]
{
	ai_face();
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.14;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_shoot3 = [ 83, vengeance_soldier_shoot4 ]
{
	ai_face();
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.11;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_shoot4 = [ 84, vengeance_soldier_shoot5 ]
{
	ai_face();
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.08;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_shoot5 = [ 85, vengeance_soldier_end1 ]
{
	ai_face();
	self.touch = vengeance_soldier_touch;
	self.alpha = 0.06;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	sound7(self, CHAN_WEAPON, "soldier/sattck1.wav", 1, ATTN_NORM, SNDSPD);
	vengeance_soldier_shoot();
};

void() vengeance_soldier11 = [ 16, vengeance_soldier12 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier12 = [ 15, vengeance_soldier13 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier13 = [ 14, vengeance_soldier14 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier14 = [ 13, vengeance_soldier15 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier15 = [ 12, vengeance_soldier16 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier16 = [ 11, vengeance_soldier17 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier17 = [ 10, vengeance_soldier18 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier18 = [ 9, vengeance_soldier19 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier19 = [ 8, vengeance_soldier_stand1 ]
{
	sound7(self, CHAN_VOICE, "soldier/sight1.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_stand1 = [ 81, vengeance_soldier_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier21 = [ 27, vengeance_soldier22 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier22 = [ 26, vengeance_soldier23 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier23 = [ 25, vengeance_soldier24 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier24 = [ 24, vengeance_soldier25 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier25 = [ 23, vengeance_soldier26 ]
{
	walkmove(self.angles_y, 4);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier26 = [ 22, vengeance_soldier27 ]
{
	walkmove(self.angles_y, 3);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier27 = [ 21, vengeance_soldier28 ]
{
	walkmove(self.angles_y, 13);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier28 = [ 20, vengeance_soldier29 ]
{
	walkmove(self.angles_y, 4);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier29 = [ 19, vengeance_soldier210 ]
{
	walkmove(self.angles_y, 5);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier210 = [ 18, vengeance_soldier_stand2 ]
{
	sound7(self, CHAN_VOICE, "soldier/sight1.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_stand2 = [ 8, vengeance_soldier_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_soldier_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	if ((self.frame == 17))
	{
		self.think = vengeance_soldier11;
	}
	else
	{
		self.think = vengeance_soldier21;
	}
};

void() vengeance_soldier_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_soldier_bright05;
};

void() vengeance_soldier_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_soldier_bright04;
};

void() vengeance_soldier_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_soldier_bright03;
};

void() vengeance_soldier_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_soldier_bright02;
};

void() vengeance_soldier_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_soldier_bright01;
};

void(string modelname, float modelframe) vengeance_soldier =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_FLY;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/soldier.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/soldier1.mdl");
		}
	}
	setsize(self, VEC_HULL_MIN, '16 16 40');
	self.frame = modelframe;
	if ((autocvar_quadreplacer == 0))
	{
		self.solid = 0;
	}
	else
	{
		self.solid = SOLID_SLIDEBOX;
	}
	vengeance_soldier_bright00();
};
