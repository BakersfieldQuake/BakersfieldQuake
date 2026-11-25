//Decompiled code. Please respect the original copyright.

void(float loudness, float velo) zombie_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((velo == 1))
		{
			if ((select <= 0.5))
			{
				sound7(self, CHAN_AUTO, "walk/zombierun1.wav", loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_AUTO, "walk/zombierun2.wav", loudness, ATTN_IDLE, SNDSPD);
			}
		}
		else
		{
			if ((select <= 0.5))
			{
				sound7(self, CHAN_AUTO, "walk/zombiewalk1.wav", loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_AUTO, "walk/zombiewalk2.wav", loudness, ATTN_IDLE, SNDSPD);
			}
		}
	}
};

void() zombie_stand1 = [ 0, zombie_stand2 ]
{
	ai_stand();
};

void() zombie_stand2 = [ 1, zombie_stand3 ]
{
	ai_stand();
};

void() zombie_stand3 = [ 2, zombie_stand4 ]
{
	ai_stand();
};

void() zombie_stand4 = [ 3, zombie_stand5 ]
{
	ai_stand();
};

void() zombie_stand5 = [ 4, zombie_stand6 ]
{
	ai_stand();
};

void() zombie_stand6 = [ 5, zombie_stand7 ]
{
	ai_stand();
};

void() zombie_stand7 = [ 6, zombie_stand8 ]
{
	ai_stand();
};

void() zombie_stand8 = [ 7, zombie_stand9 ]
{
	ai_stand();
};

void() zombie_stand9 = [ 8, zombie_stand10 ]
{
	ai_stand();
};

void() zombie_stand10 = [ 9, zombie_stand11 ]
{
	ai_stand();
};

void() zombie_stand11 = [ 10, zombie_stand12 ]
{
	ai_stand();
};

void() zombie_stand12 = [ 11, zombie_stand13 ]
{
	ai_stand();
};

void() zombie_stand13 = [ 12, zombie_stand14 ]
{
	ai_stand();
};

void() zombie_stand14 = [ 13, zombie_stand15 ]
{
	ai_stand();
};

void() zombie_stand15 = [ 14, zombie_stand1 ]
{
	ai_stand();
};

void() zombie_cruc1 = [ 192, zombie_cruc2 ]
{
	if ((random() < 0.1))
	{
		sound7(self, CHAN_VOICE, "zombie/idle_w2.wav", 1, ATTN_STATIC);
	}
};

void() zombie_cruc2 = [ 193, zombie_cruc3 ]
{
	self.nextthink = ((time + 0.1) + (random() * 0.1));
};

void() zombie_cruc3 = [ 194, zombie_cruc4 ]
{
	self.nextthink = ((time + 0.1) + (random() * 0.1));
};

void() zombie_cruc4 = [ 195, zombie_cruc5 ]
{
	self.nextthink = ((time + 0.1) + (random() * 0.1));
};

void() zombie_cruc5 = [ 196, zombie_cruc6 ]
{
	self.nextthink = ((time + 0.1) + (random() * 0.1));
};

void() zombie_cruc6 = [ 197, zombie_cruc1 ]
{
	self.nextthink = ((time + 0.1) + (random() * 0.1));
};

void() zombie_walk1 = [ 15, zombie_walk2 ]
{
	ai_walk(0);
};

void() zombie_walk2 = [ 16, zombie_walk3 ]
{
	ai_walk(2);
	zombie_footsteps(0.6, 2);
};

void() zombie_walk3 = [ 17, zombie_walk4 ]
{
	ai_walk(3);
};

void() zombie_walk4 = [ 18, zombie_walk5 ]
{
	ai_walk(2);
};

void() zombie_walk5 = [ 19, zombie_walk6 ]
{
	ai_walk(1);
};

void() zombie_walk6 = [ 20, zombie_walk7 ]
{
	ai_walk(0);
};

void() zombie_walk7 = [ 21, zombie_walk8 ]
{
	ai_walk(0);
};

void() zombie_walk8 = [ 22, zombie_walk9 ]
{
	ai_walk(0);
};

void() zombie_walk9 = [ 23, zombie_walk10 ]
{
	ai_walk(0);
	if ((self.monstermodel == 2))
	{
		zombie_footsteps(0.6, 2);
	}
};

void() zombie_walk10 = [ 24, zombie_walk11 ]
{
	ai_walk(0);
};

void() zombie_walk11 = [ 25, zombie_walk12 ]
{
	ai_walk(2);
	if ((self.monstermodel < 2))
	{
		zombie_footsteps(0.6, 2);
	}
};

void() zombie_walk12 = [ 26, zombie_walk13 ]
{
	ai_walk(2);
};

void() zombie_walk13 = [ 27, zombie_walk14 ]
{
	ai_walk(1);
};

void() zombie_walk14 = [ 28, zombie_walk15 ]
{
	ai_walk(0);
};

void() zombie_walk15 = [ 29, zombie_walk16 ]
{
	ai_walk(0);
};

void() zombie_walk16 = [ 30, zombie_walk17 ]
{
	ai_walk(0);
};

void() zombie_walk17 = [ 31, zombie_walk18 ]
{
	ai_walk(0);
};

void() zombie_walk18 = [ 32, zombie_walk19 ]
{
	ai_walk(0);
};

void() zombie_walk19 = [ 33, zombie_walk1 ]
{
	ai_walk(0);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "zombie/z_idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
};

void() zombie_run1 = [ 34, zombie_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(1);
	self.inpain = 0;
};

void() zombie_run2 = [ 35, zombie_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(1);
};

void() zombie_run3 = [ 36, zombie_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(0);
};

void() zombie_run4 = [ 37, zombie_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(1);
};

void() zombie_run5 = [ 38, zombie_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(2);
};

void() zombie_run6 = [ 39, zombie_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(3);
};

void() zombie_run7 = [ 40, zombie_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(4);
};

void() zombie_run8 = [ 41, zombie_run9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(4);
};

void() zombie_run9 = [ 42, zombie_run10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(2);
	zombie_footsteps(1, 1);
};

void() zombie_run10 = [ 43, zombie_run11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(0);
};

void() zombie_run11 = [ 44, zombie_run12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(0);
};

void() zombie_run12 = [ 45, zombie_run13 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(0);
};

void() zombie_run13 = [ 46, zombie_run14 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(2);
};

void() zombie_run14 = [ 47, zombie_run15 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(4);
};

void() zombie_run15 = [ 48, zombie_run16 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(6);
};

void() zombie_run16 = [ 49, zombie_run17 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(7);
};

void() zombie_run17 = [ 50, zombie_run18 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(3);
	zombie_footsteps(1, 1);
};

void() zombie_run18 = [ 51, zombie_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "zombie/z_idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((random() > 0.8))
	{
		sound7(self, CHAN_VOICE, "zombie/z_idle1.wav", 1, ATTN_IDLE, SNDSPD);
	}
};

void() ZombieGrenadeTouch =
{
	if ((other == self.owner))
	{
		return;
	}
	if (other.takedamage)
	{
		if ((autocvar_zombie_size_influenced_attack == 1))
		{
			T_Damage(other, self, self.owner, (autocvar_zombie_flesh * self.owner.scale));
		}
		else
		{
			T_Damage(other, self, self.owner, autocvar_zombie_flesh);
		}
		sound7(self, CHAN_WEAPON, "zombie/z_hit.wav", 1, ATTN_NORM);
		remove(self);
		return;
	}
	sound7(self, CHAN_WEAPON, "zombie/z_miss.wav", 1, ATTN_NORM, SNDSPD);
	self.velocity = VEC_ORIGIN;
	self.avelocity = VEC_ORIGIN;
	self.touch = SUB_Remove;
};

void(vector st) ZombieFireGrenade =
{
	local vector distancedelta;
	local vector nozdistancedelta;
	local entity missile;
	local vector org;

	sound7(self, CHAN_WEAPON, "zombie/z_shot1.wav", 1, ATTN_NORM, SNDSPD);
	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	org = ((self.origin + (st_x * v_forward)) + (st_y * v_right)) + ((st_z - 24) * v_up);
	makevectors(self.angles);
	if ((autocvar_zombieaim == 0))
	{
		missile.velocity = normalize((self.enemy.origin - org));
		missile.velocity = (missile.velocity * 600);
		missile.velocity_z = 200;
	}
	else
	{
		distancedelta = self.enemy.origin - org;
		nozdistancedelta = distancedelta;
		missile.velocity = normalize(distancedelta);
		missile.velocity = (missile.velocity * 600);
		missile.velocity_z = ((missile.velocity_z + 175) + (50 * random()));
	}
	missile.avelocity = '3000 1000 2000';
	missile.touch = ZombieGrenadeTouch;
	missile.scale = (missile.scale + 0.1);
	missile.nextthink = (time + 2.5);
	missile.think = SUB_Remove;
	if ((autocvar_zombienewmodelprojectile == 1))
	{
		if ((self.monstermodel == 2))
		{
			setmodel(missile, "progs/zombie_new_projectile.mdl");
			missile.traileffectnum = particleeffectnum(/*56087i*/"zombie_new_projectile");
			missile.scale = 2.5;
			missile.avelocity = '1000 1000 1000';
		}
		else
		{
			setmodel(missile, "progs/zom_gib.mdl");
		}
	}
	else
	{
		setmodel(missile, "progs/zom_gib.mdl");
	}
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(missile, org);
};

void() zombie_atta1 = [ 52, zombie_atta2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta2 = [ 53, zombie_atta3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta3 = [ 54, zombie_atta4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta4 = [ 55, zombie_atta5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta5 = [ 56, zombie_atta6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((self.monstermodel == 2))
	{
		ZombieFireGrenade('-2 -8 32');
	}
};

void() zombie_atta6 = [ 57, zombie_atta7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta7 = [ 58, zombie_atta8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta8 = [ 59, zombie_atta9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta9 = [ 60, zombie_atta10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta10 = [ 61, zombie_atta11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta11 = [ 62, zombie_atta12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta12 = [ 63, zombie_atta13 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_atta13 = [ 64, zombie_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((self.monstermodel < 2))
	{
		ZombieFireGrenade('-10 -22 30');
	}
};

void() zombie_attb1 = [ 65, zombie_attb2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb2 = [ 66, zombie_attb3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb3 = [ 67, zombie_attb4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb4 = [ 68, zombie_attb5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb5 = [ 69, zombie_attb6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((self.monstermodel == 2))
	{
		ZombieFireGrenade('-7 -11 25');
	}
};

void() zombie_attb6 = [ 70, zombie_attb7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb7 = [ 71, zombie_attb8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb8 = [ 72, zombie_attb9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb9 = [ 73, zombie_attb10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb10 = [ 74, zombie_attb11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb11 = [ 75, zombie_attb12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb12 = [ 76, zombie_attb13 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb13 = [ 77, zombie_attb14 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attb14 = [ 77, zombie_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((self.monstermodel < 2))
	{
		ZombieFireGrenade('-10 9 30');
	}
};

void() zombie_attc1 = [ 79, zombie_attc2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attc2 = [ 80, zombie_attc3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attc3 = [ 81, zombie_attc4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attc4 = [ 82, zombie_attc5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attc5 = [ 83, zombie_attc6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((self.monstermodel == 2))
	{
		ZombieFireGrenade('-2 -8 32');
	}
};

void() zombie_attc6 = [ 84, zombie_attc7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attc7 = [ 85, zombie_attc8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attc8 = [ 86, zombie_attc9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attc9 = [ 87, zombie_attc10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attc10 = [ 88, zombie_attc11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attc11 = [ 89, zombie_attc12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() zombie_attc12 = [ 90, zombie_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((self.monstermodel < 2))
	{
		ZombieFireGrenade('-12 -19 29');
	}
};

void() zombie_missile =
{
	local float r;

	r = random();
	if ((self.monstermodel == 2))
	{
		if ((r < 0.3))
		{
			zombie_atta1();
		}
		else
		{
			if ((r < 0.77))
			{
				zombie_attb1();
			}
			else
			{
				zombie_attc1();
			}
		}
	}
	else
	{
		if (((self.model != "progs/zombie_noarms.mdl") && (self.model != "progs/zombie1_noarms.mdl")))
		{
			if ((r < 0.3))
			{
				zombie_atta1();
			}
			else
			{
				if ((r < 0.6))
				{
					zombie_attb1();
				}
				else
				{
					zombie_attc1();
				}
			}
		}
	}
};

void() zombie_paina1 = [ 91, zombie_paina2 ]
{
	sound7(self, CHAN_VOICE, "zombie/z_pain.wav", 1, ATTN_NORM, SNDSPD);
};

void() zombie_paina2 = [ 92, zombie_paina3 ]
{
	ai_painforward(3);
};

void() zombie_paina3 = [ 93, zombie_paina4 ]
{
	ai_painforward(1);
};

void() zombie_paina4 = [ 94, zombie_paina5 ]
{
	ai_pain(1);
};

void() zombie_paina5 = [ 95, zombie_paina6 ]
{
	ai_pain(3);
};

void() zombie_paina6 = [ 96, zombie_paina7 ]
{
	ai_pain(1);
};

void() zombie_paina7 = [ 97, zombie_paina8 ]
{
};

void() zombie_paina8 = [ 98, zombie_paina9 ]
{
};

void() zombie_paina9 = [ 99, zombie_paina10 ]
{
};

void() zombie_paina10 = [ 100, zombie_paina11 ]
{
};

void() zombie_paina11 = [ 101, zombie_paina12 ]
{
};

void() zombie_paina12 = [ 102, zombie_run1 ]
{
};

void() zombie_painb1 = [ 103, zombie_painb2 ]
{
	sound7(self, CHAN_VOICE, "zombie/z_pain1.wav", 1, ATTN_NORM, SNDSPD);
};

void() zombie_painb2 = [ 104, zombie_painb3 ]
{
	local vector check;

	ai_pain(2);
	check = (self.origin - '0 0 20') + '0 0 1';
	if (((((autocvar_zombieflies == 1) && (pointcontents(check) != CONTENT_WATER)) && (pointcontents(check) != CONTENT_SLIME)) && (pointcontents(check) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*56146i*/"zombiedownfliesblack");
	}
	if (((((autocvar_zombieflies == 2) && (pointcontents(check) != CONTENT_WATER)) && (pointcontents(check) != CONTENT_SLIME)) && (pointcontents(check) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*56167i*/"zombiedownfliesbrown");
	}
};

void() zombie_painb3 = [ 105, zombie_painb4 ]
{
	ai_pain(8);
};

void() zombie_painb4 = [ 106, zombie_painb5 ]
{
	ai_pain(6);
};

void() zombie_painb5 = [ 107, zombie_painb6 ]
{
	ai_pain(2);
};

void() zombie_painb6 = [ 108, zombie_painb7 ]
{
};

void() zombie_painb7 = [ 109, zombie_painb8 ]
{
};

void() zombie_painb8 = [ 110, zombie_painb9 ]
{
};

void() zombie_painb9 = [ 111, zombie_painb10 ]
{
	if ((random() < 0.7))
	{
		sound7(self, CHAN_BODY, "zombie/z_fall.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() zombie_painb10 = [ 112, zombie_painb11 ]
{
};

void() zombie_painb11 = [ 113, zombie_painb12 ]
{
};

void() zombie_painb12 = [ 114, zombie_painb13 ]
{
};

void() zombie_painb13 = [ 115, zombie_painb14 ]
{
};

void() zombie_painb14 = [ 116, zombie_painb15 ]
{
};

void() zombie_painb15 = [ 117, zombie_painb16 ]
{
};

void() zombie_painb16 = [ 118, zombie_painb17 ]
{
};

void() zombie_painb17 = [ 119, zombie_painb18 ]
{
};

void() zombie_painb18 = [ 120, zombie_painb19 ]
{
};

void() zombie_painb19 = [ 121, zombie_painb20 ]
{
};

void() zombie_painb20 = [ 122, zombie_painb21 ]
{
};

void() zombie_painb21 = [ 123, zombie_painb22 ]
{
};

void() zombie_painb22 = [ 124, zombie_painb23 ]
{
};

void() zombie_painb23 = [ 125, zombie_painb24 ]
{
};

void() zombie_painb24 = [ 126, zombie_painb25 ]
{
};

void() zombie_painb25 = [ 127, zombie_painb26 ]
{
	ai_painforward(1);
};

void() zombie_painb26 = [ 128, zombie_painb27 ]
{
};

void() zombie_painb27 = [ 129, zombie_painb28 ]
{
};

void() zombie_painb28 = [ 130, zombie_run1 ]
{
};

void() zombie_painc1 = [ 131, zombie_painc2 ]
{
	sound7(self, CHAN_VOICE, "zombie/z_pain1.wav", 1, ATTN_NORM, SNDSPD);
};

void() zombie_painc2 = [ 132, zombie_painc3 ]
{
};

void() zombie_painc3 = [ 133, zombie_painc4 ]
{
	ai_pain(3);
};

void() zombie_painc4 = [ 134, zombie_painc5 ]
{
	ai_pain(1);
};

void() zombie_painc5 = [ 135, zombie_painc6 ]
{
};

void() zombie_painc6 = [ 136, zombie_painc7 ]
{
};

void() zombie_painc7 = [ 137, zombie_painc8 ]
{
};

void() zombie_painc8 = [ 138, zombie_painc9 ]
{
};

void() zombie_painc9 = [ 139, zombie_painc10 ]
{
};

void() zombie_painc10 = [ 140, zombie_painc11 ]
{
};

void() zombie_painc11 = [ 141, zombie_painc12 ]
{
	ai_painforward(1);
};

void() zombie_painc12 = [ 142, zombie_painc13 ]
{
	ai_painforward(1);
};

void() zombie_painc13 = [ 143, zombie_painc14 ]
{
};

void() zombie_painc14 = [ 144, zombie_painc15 ]
{
};

void() zombie_painc15 = [ 145, zombie_painc16 ]
{
};

void() zombie_painc16 = [ 146, zombie_painc17 ]
{
};

void() zombie_painc17 = [ 147, zombie_painc18 ]
{
};

void() zombie_painc18 = [ 148, zombie_run1 ]
{
};

void() zombie_paind1 = [ 149, zombie_paind2 ]
{
	sound7(self, CHAN_VOICE, "zombie/z_pain.wav", 1, ATTN_NORM, SNDSPD);
};

void() zombie_paind2 = [ 150, zombie_paind3 ]
{
};

void() zombie_paind3 = [ 151, zombie_paind4 ]
{
};

void() zombie_paind4 = [ 152, zombie_paind5 ]
{
};

void() zombie_paind5 = [ 153, zombie_paind6 ]
{
};

void() zombie_paind6 = [ 154, zombie_paind7 ]
{
};

void() zombie_paind7 = [ 155, zombie_paind8 ]
{
};

void() zombie_paind8 = [ 156, zombie_paind9 ]
{
};

void() zombie_paind9 = [ 157, zombie_paind10 ]
{
	ai_pain(1);
};

void() zombie_paind10 = [ 158, zombie_paind11 ]
{
};

void() zombie_paind11 = [ 159, zombie_paind12 ]
{
};

void() zombie_paind12 = [ 160, zombie_paind13 ]
{
};

void() zombie_paind13 = [ 161, zombie_run1 ]
{
};

void() zombie_paine1 = [ 162, zombie_paine2 ]
{
	sound7(self, CHAN_VOICE, "zombie/z_pain.wav", 1, ATTN_NORM, SNDSPD);
	if ((autocvar_zombienewmodelproperties >= 2))
	{
		if ((self.monstermodel == 2))
		{
			self.health = 490;
		}
		else
		{
			self.health = 60;
		}
	}
	else
	{
		self.health = 60;
	}
};

void() zombie_paine2 = [ 163, zombie_paine3 ]
{
	ai_pain(8);
};

void() zombie_paine3 = [ 164, zombie_paine4 ]
{
	local vector check;

	ai_pain(5);
	check = (self.origin - '0 0 20') + '0 0 1';
	if (((((autocvar_zombieflies == 1) && (pointcontents(check) != CONTENT_WATER)) && (pointcontents(check) != CONTENT_SLIME)) && (pointcontents(check) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*56146i*/"zombiedownfliesblack");
	}
	if (((((autocvar_zombieflies == 2) && (pointcontents(check) != CONTENT_WATER)) && (pointcontents(check) != CONTENT_SLIME)) && (pointcontents(check) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*56167i*/"zombiedownfliesbrown");
	}
};

void() zombie_paine4 = [ 165, zombie_paine5 ]
{
	ai_pain(3);
};

void() zombie_paine5 = [ 166, zombie_paine6 ]
{
	ai_pain(1);
};

void() zombie_paine6 = [ 167, zombie_paine7 ]
{
	ai_pain(2);
};

void() zombie_paine7 = [ 168, zombie_paine8 ]
{
	ai_pain(1);
};

void() zombie_paine8 = [ 169, zombie_paine9 ]
{
	ai_pain(1);
};

void() zombie_paine9 = [ 170, zombie_paine10 ]
{
	ai_pain(2);
};

void() zombie_paine10 = [ 171, zombie_paine11 ]
{
	if ((random() < 0.7))
	{
		sound7(self, CHAN_BODY, "zombie/z_fall.wav", 1, ATTN_NORM, SNDSPD);
	}
	self.solid = 0;
};

void() zombie_paine11 = [ 172, zombie_paine12 ]
{
	self.nextthink = (self.nextthink + 5);
	if ((autocvar_zombienewmodelproperties >= 2))
	{
		if ((self.monstermodel == 2))
		{
			self.health = 490;
		}
		else
		{
			self.health = 60;
		}
	}
	else
	{
		self.health = 60;
	}
};

void() zombie_paine12 = [ 173, zombie_paine13 ]
{
	if ((autocvar_zombienewmodelproperties >= 2))
	{
		if ((self.monstermodel == 2))
		{
			self.health = 490;
		}
		else
		{
			self.health = 60;
		}
	}
	else
	{
		self.health = 60;
	}
	sound7(self, CHAN_VOICE, "zombie/z_idle.wav", 1, ATTN_IDLE, SNDSPD);
	self.solid = SOLID_SLIDEBOX;
	if (!walkmove(0, 0))
	{
		self.think = zombie_paine11;
		self.solid = 0;
		return;
	}
};

void() zombie_paine13 = [ 174, zombie_paine14 ]
{
};

void() zombie_paine14 = [ 175, zombie_paine15 ]
{
};

void() zombie_paine15 = [ 176, zombie_paine16 ]
{
};

void() zombie_paine16 = [ 177, zombie_paine17 ]
{
};

void() zombie_paine17 = [ 178, zombie_paine18 ]
{
};

void() zombie_paine18 = [ 179, zombie_paine19 ]
{
};

void() zombie_paine19 = [ 180, zombie_paine20 ]
{
};

void() zombie_paine20 = [ 181, zombie_paine21 ]
{
};

void() zombie_paine21 = [ 182, zombie_paine22 ]
{
};

void() zombie_paine22 = [ 183, zombie_paine23 ]
{
};

void() zombie_paine23 = [ 184, zombie_paine24 ]
{
};

void() zombie_paine24 = [ 185, zombie_paine25 ]
{
};

void() zombie_paine25 = [ 186, zombie_paine26 ]
{
	ai_painforward(5);
};

void() zombie_paine26 = [ 187, zombie_paine27 ]
{
	ai_painforward(3);
};

void() zombie_paine27 = [ 188, zombie_paine28 ]
{
	ai_painforward(1);
};

void() zombie_paine28 = [ 189, zombie_paine29 ]
{
	ai_pain(1);
};

void() zombie_paine29 = [ 190, zombie_paine30 ]
{
};

void() zombie_paine30 = [ 191, zombie_run1 ]
{
};

void() zombie_head_anim =
{
	self.frame = (self.frame + 1);
	if ((self.frame >= 10))
	{
		if ((autocvar_kickgibs == 1))
		{
			kick_touch2_temp();
		}
		else
		{
			kick_touch3_temp();
		}
		return;
	}
	self.nextthink = (time + 0.1);
	self.think = zombie_head_anim;
};

void() zombie_head =
{
	local entity zombiehead;
	local vector face1;
	local vector face2;
	local vector org;

	zombiehead = spawn();
	face1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(face1);
	face2 = normalize(v_forward);
	zombiehead.angles = vectoangles(face2);
	org = ((self.origin + (v_right * 2)) + (v_up * 20)) + (v_forward * -10);
	setorigin(zombiehead, org);
	setmodel(zombiehead, "progs/h_zombie_new.mdl");
	setsize(zombiehead, VEC_ORIGIN, VEC_ORIGIN);
	zombiehead.skin = self.skin;
	zombiehead.scale = 1.07;
	zombiehead.movetype = MOVETYPE_BOUNCE;
	zombiehead.solid = SOLID_TRIGGER;
	zombiehead.takedamage = 0;
	zombiehead.velocity_x = (83 * crandom());
	zombiehead.velocity_y = (83 * crandom());
	zombiehead.velocity_z = 222;
	zombiehead.enemy = self.enemy;
	zombiehead.nextthink = (time + 0.15);
	zombiehead.think = zombie_head_anim;
	Gyro_Object_ClearPhysics(zombiehead);
	GibPhysics(zombiehead);
};

void() zombie_dieburn1 = [ 162, zombie_dieburn2 ]
{
	self.burnz_origin = 12;
	if ((self.zombie_mix_anim == 1))
	{
		burn_toggle_allround();
	}
	else
	{
		burn_toggle();
	}
};

void() zombie_dieburn2 = [ 163, zombie_dieburn3 ]
{
	ai_pain(8);
	self.burnz_origin = 11;
};

void() zombie_dieburn3 = [ 164, zombie_dieburn4 ]
{
	ai_pain(5);
	self.burnz_origin = 6;
};

void() zombie_dieburn4 = [ 165, zombie_dieburn5 ]
{
	ai_pain(3);
	self.burnz_origin = 3;
};

void() zombie_dieburn5 = [ 166, zombie_dieburn6 ]
{
	ai_pain(1);
	self.burnz_origin = 0;
};

void() zombie_dieburn6 = [ 167, zombie_dieburn7 ]
{
	ai_pain(2);
	self.burnz_origin = -2;
};

void() zombie_dieburn7 = [ 168, zombie_dieburn8 ]
{
	ai_pain(1);
	self.burnz_origin = -4;
};

void() zombie_dieburn8 = [ 169, zombie_dieburn9 ]
{
	ai_pain(1);
	self.burnz_origin = -6;
};

void() zombie_dieburn9 = [ 170, zombie_dieburn10 ]
{
	self.burnz_origin = -8;
};

void() zombie_dieburn10 = [ 171, zombie_dieburn11 ]
{
	self.solid = 0;
	self.burnz_origin = -10;
};

void() zombie_dieburn11 = [ 172, zombie_dieburn12 ]
{
	self.burnz_origin = -10;
};

void() zombie_dieburn12 = [ 173, zombie_dieburn12 ]
{
	self.burnz_origin = -10;
	self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
};

void() zombie_die_newmodel_deatha1 = [ 198, zombie_die_newmodel_deatha2 ]
{
	local vector face1;
	local vector org;

	sound7(self, CHAN_VOICE, "zombie/cut_head.wav", 1, ATTN_NORM, SNDSPD);
	setmodel(self, "progs/zombie_new_headless.mdl");
	setsize(self, VEC_HULL_MIN, '16 16 40');
	zombie_head();
	ai_forward(2);
	face1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(face1);
	org = ((self.origin + (v_right * 1)) + (v_up * 22)) + (v_forward * -10);
	pointparticles(particleeffectnum(/*56226i*/"zombieheadcut"), org, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.14);
};

void() zombie_die_newmodel_deatha2 = [ 199, zombie_die_newmodel_deatha3 ]
{
	ai_forward(2);
	self.nextthink = (time + 0.14);
};

void() zombie_die_newmodel_deatha3 = [ 200, zombie_die_newmodel_deatha4 ]
{
	local vector check;

	ai_forward(2);
	self.nextthink = (time + 0.14);
	check = (self.origin - '0 0 20') + '0 0 1';
	if ((((pointcontents(check) != CONTENT_WATER) && (pointcontents(check) != CONTENT_SLIME)) && (pointcontents(check) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*56146i*/"zombiedownfliesblack");
	}
};

void() zombie_die_newmodel_deatha4 = [ 201, zombie_die_newmodel_deatha5 ]
{
	ai_forward(7);
	self.nextthink = (time + 0.14);
};

void() zombie_die_newmodel_deatha5 = [ 202, zombie_die_newmodel_deatha6 ]
{
	self.nextthink = (time + 0.13);
};

void() zombie_die_newmodel_deatha6 = [ 203, zombie_die_newmodel_deatha7 ]
{
	self.nextthink = (time + 0.13);
};

void() zombie_die_newmodel_deatha7 = [ 204, zombie_die_newmodel_deatha8 ]
{
	self.nextthink = (time + 0.13);
};

void() zombie_die_newmodel_deatha8 = [ 205, zombie_die_newmodel_deatha9 ]
{
	self.nextthink = (time + 0.13);
};

void() zombie_die_newmodel_deatha9 = [ 206, zombie_die_newmodel_deatha10 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha10 = [ 207, zombie_die_newmodel_deatha11 ]
{
	self.solid = 0;
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha11 = [ 208, zombie_die_newmodel_deatha12 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha12 = [ 209, zombie_die_newmodel_deatha13 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha13 = [ 210, zombie_die_newmodel_deatha14 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha14 = [ 211, zombie_die_newmodel_deatha15 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha15 = [ 212, zombie_die_newmodel_deatha16 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha16 = [ 213, zombie_die_newmodel_deatha17 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha17 = [ 214, zombie_die_newmodel_deatha18 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha18 = [ 215, zombie_die_newmodel_deatha19 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha19 = [ 216, zombie_die_newmodel_deatha20 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha20 = [ 217, zombie_die_newmodel_deatha21 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha21 = [ 218, zombie_die_newmodel_deatha22 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha22 = [ 219, zombie_die_newmodel_deatha23 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha23 = [ 220, zombie_die_newmodel_deatha24 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha24 = [ 221, zombie_die_newmodel_deatha25 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha25 = [ 222, zombie_die_newmodel_deatha26 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deatha26 = [ 223, zombie_die_newmodel_deatha26 ]
{
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_newzombiecorpsehealth, "newzombieheadless");
};

void() zombie_die_newmodel_deathb1 = [ 224, zombie_die_newmodel_deathb2 ]
{
	sound7(self, CHAN_VOICE, "zombie/zombie_die.wav", 1, ATTN_NORM, SNDSPD);
	ai_forward(-7);
	self.nextthink = (time + 0.14);
};

void() zombie_die_newmodel_deathb2 = [ 225, zombie_die_newmodel_deathb3 ]
{
	ai_forward(-7);
	self.nextthink = (time + 0.14);
};

void() zombie_die_newmodel_deathb3 = [ 226, zombie_die_newmodel_deathb4 ]
{
	local vector check;

	ai_forward(-7);
	self.nextthink = (time + 0.14);
	check = (self.origin - '0 0 20') + '0 0 1';
	if ((((pointcontents(check) != CONTENT_WATER) && (pointcontents(check) != CONTENT_SLIME)) && (pointcontents(check) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*56146i*/"zombiedownfliesblack");
	}
};

void() zombie_die_newmodel_deathb4 = [ 227, zombie_die_newmodel_deathb5 ]
{
	ai_forward(-7);
	self.nextthink = (time + 0.14);
};

void() zombie_die_newmodel_deathb5 = [ 228, zombie_die_newmodel_deathb6 ]
{
	self.nextthink = (time + 0.13);
};

void() zombie_die_newmodel_deathb6 = [ 229, zombie_die_newmodel_deathb7 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb7 = [ 230, zombie_die_newmodel_deathb8 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb8 = [ 231, zombie_die_newmodel_deathb9 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb9 = [ 232, zombie_die_newmodel_deathb10 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb10 = [ 233, zombie_die_newmodel_deathb11 ]
{
	self.solid = 0;
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb11 = [ 234, zombie_die_newmodel_deathb12 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb12 = [ 235, zombie_die_newmodel_deathb13 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb13 = [ 236, zombie_die_newmodel_deathb14 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb14 = [ 237, zombie_die_newmodel_deathb15 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb15 = [ 238, zombie_die_newmodel_deathb16 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb16 = [ 239, zombie_die_newmodel_deathb17 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb17 = [ 240, zombie_die_newmodel_deathb18 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb18 = [ 241, zombie_die_newmodel_deathb19 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb19 = [ 242, zombie_die_newmodel_deathb20 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb20 = [ 243, zombie_die_newmodel_deathb21 ]
{
	self.nextthink = (time + 0.12);
};

void() zombie_die_newmodel_deathb21 = [ 244, zombie_die_newmodel_deathb21 ]
{
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_newzombiecorpsehealth, "newzombie");
};

void(float maxgibs, float gibscounter) producegibs_zombie =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/gib_zarm.mdl", self.health);
		ThrowGib("progs/gib_zarm.mdl", self.health);
		ThrowGib("progs/gib_zleg.mdl", self.health);
		ThrowGib("progs/gib_zleg.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_zombie(maxgibs, gibscounter);
};

void() zombie_die =
{
	local float zufall;
	local float randomness;
	local float maxgibs;
	local float gibscounter;

	if ((((!self.shocked && (self.enemy.meleeing == 0)) && (self.enemy.weapon == IT_LIGHTNING)) && (self.sticky != 1)))
	{
		self.sticky = 0;
		lg_death1();
		if ((self.target || self.killtarget))
		{
			activator = self.enemy;
			SUB_UseTargets();
		}
		return;
	}
	if ((autocvar_zombienewmodelproperties >= 1))
	{
		if (((self.monstermodel == 2) && (world.model != "maps/e1m7.bsp")))
		{
			if ((autocvar_slowmotion >= 3))
			{
				if ((random() <= (autocvar_slowmotion_randomness_zombie * 0.01)))
				{
					the_matrix = 1;
					matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
				}
			}
			if ((self.enemy.axeequipped == 1))
			{
				zombie_die_newmodel_deatha1();
			}
			else
			{
				zombie_die_newmodel_deathb1();
			}
			return;
		}
	}
	gibbed_monsters = gibbed_monsters + 1;
	autocvar_zombierandomness = autocvar_zombierandomness * 0.01;
	if ((((autocvar_zombie == 2) && (world.model != "maps/e1m7.bsp")) && !(self.spawnflags & SPAWN_CRUCIFIED)))
	{
		randomness = random();
		if ((randomness <= autocvar_zombierandomness))
		{
			if ((random() < 0.3))
			{
				sound7(self, CHAN_VOICE, "zombie/z_gib.wav", 1, ATTN_NORM, SNDSPD);
			}
			else
			{
				if ((random() < 0.5))
				{
					sound7(self, CHAN_VOICE, "zombie/cut_head.wav", 1, ATTN_NORM, SNDSPD);
				}
			}
			sound7(self, CHAN_VOICE, "player/udeath2.wav", 0.6, ATTN_NORM, SNDSPD);
			Gyro_Object_ClearPhysics(self);
			self.delete_painskin = 1;
			zombie_dieburn1();
			return;
		}
	}
	if ((((autocvar_zombie == 3) && (world.model != "maps/e1m7.bsp")) && !(self.spawnflags & SPAWN_CRUCIFIED)))
	{
		randomness = random();
		if ((randomness <= autocvar_zombierandomness))
		{
			if ((random() < 0.3))
			{
				sound7(self, CHAN_VOICE, "zombie/z_gib.wav", 1, ATTN_NORM, SNDSPD);
			}
			else
			{
				if ((random() < 0.5))
				{
					sound7(self, CHAN_VOICE, "zombie/cut_head.wav", 1, ATTN_NORM, SNDSPD);
				}
			}
			self.delete_painskin = 1;
			self.zombie_mix_anim = 1;
			zombie_dieburn1();
			if ((self.nodeathanim == 0))
			{
				ghost_die();
			}
			return;
		}
	}
	if (((autocvar_zombie == 4) && (world.model != "maps/e1m7.bsp")))
	{
		randomness = random();
		if ((randomness <= autocvar_zombierandomness))
		{
			zufall = random();
			if ((zufall > 0.67))
			{
				self.grimrock_helper = 1;
			}
			else
			{
				if (((zufall < 0.33) && !(self.spawnflags & SPAWN_CRUCIFIED)))
				{
					if ((random() < 0.3))
					{
						sound7(self, CHAN_VOICE, "zombie/z_gib.wav", 1, ATTN_NORM, SNDSPD);
					}
					else
					{
						if ((random() < 0.5))
						{
							sound7(self, CHAN_VOICE, "zombie/cut_head.wav", 1, ATTN_NORM, SNDSPD);
						}
					}
					Gyro_Object_ClearPhysics(self);
					self.delete_painskin = 1;
					zombie_dieburn1();
					return;
				}
				else
				{
					if (!(self.spawnflags & SPAWN_CRUCIFIED))
					{
						if ((random() < 0.3))
						{
							sound7(self, CHAN_VOICE, "zombie/z_gib.wav", 1, ATTN_NORM, SNDSPD);
						}
						else
						{
							if ((random() < 0.5))
							{
								sound7(self, CHAN_VOICE, "zombie/cut_head.wav", 1, ATTN_NORM, SNDSPD);
							}
						}
						self.delete_painskin = 1;
						self.zombie_mix_anim = 1;
						zombie_dieburn1();
						if ((self.nodeathanim == 0))
						{
							ghost_die();
						}
						return;
					}
				}
			}
		}
	}
	self.delete_painskin = 1;
	if ((autocvar_slowmotion >= 1))
	{
		if ((random() <= (autocvar_slowmotion_randomness_zombie * 0.01)))
		{
			the_matrix = 1;
			SNDSPD = 70;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	if ((self.spawnflags & SPAWN_CRUCIFIED))
	{
		makevectors(self.angles);
		self.origin = (self.origin + (v_forward * 15));
	}
	CeilSplat();
	CeilSplat();
	CeilSplat();
	CeilSplat();
	CeilSplat();
	if ((autocvar_gibsmultiplier == 1))
	{
		if ((self.monstermodel == 0))
		{
			ThrowHead("progs/h_zombie.mdl", self.health);
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				ThrowHead("progs/h_zombie1.mdl", self.health);
			}
			else
			{
				self.scale = 1.4;
				ThrowHead("progs/h_zombie_new.mdl", self.health);
			}
		}
		if ((((self.model == "progs/zombie1.mdl") || (self.model == "progs/zombie.mdl")) || (self.model == "progs/zombie_new.mdl")))
		{
			ThrowGib("progs/gib_zarm.mdl", self.health);
			ThrowGib("progs/gib_zarm.mdl", self.health);
		}
		ThrowGib("progs/gib_zleg.mdl", self.health);
		ThrowGib("progs/gib_zleg.mdl", self.health);
		if ((autocvar_bloodextension == 1))
		{
			pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
		}
	}
	else
	{
		if ((self.monstermodel == 0))
		{
			ThrowHead("progs/h_zombie.mdl", self.health);
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				ThrowHead("progs/h_zombie1.mdl", self.health);
			}
			else
			{
				self.scale = 1.4;
				ThrowHead("progs/h_zombie_new.mdl", self.health);
			}
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		gibdeath_effects();
		producegibs_zombie(maxgibs, gibscounter);
	}
	if ((autocvar_zombie == 1))
	{
		if ((self.nodeathanim == 0))
		{
			randomness = random();
			if ((randomness <= autocvar_zombierandomness))
			{
				ghost_die();
			}
		}
	}
	if ((self.grimrock_helper == 1))
	{
		if (((self.nodeathanim == 0) && !(self.spawnflags & SPAWN_CRUCIFIED)))
		{
			if ((random() < 0.006))
			{
				soul("progs/afrit.mdl", 64, 27.451);
			}
			else
			{
				ghost_die();
			}
		}
	}
};

void(entity attacker, float take) zombie_pain =
{
	local float r;

	if ((autocvar_wallzombie == 2))
	{
		if (!(self.spawnflags & SPAWN_CRUCIFIED))
		{
			self.health = 60;
		}
	}
	else
	{
		self.health = 60;
	}
	if ((take >= 10))
	{
		if (((attacker.weapon == IT_AXE) || (attacker.weapon == IT_CHAINSAW)))
		{
			if ((self.model == "progs/zombie.mdl"))
			{
				ThrowGib("progs/gib_zarm.mdl", self.health);
				self.model = "progs/zombie_onearm.mdl";
				setmodel(self, "progs/zombie_onearm.mdl");
				setsize(self, ZOMB_MIN, ZOMB_MAX);
			}
			else
			{
				if ((self.model == "progs/zombie_onearm.mdl"))
				{
					ThrowGib("progs/gib_zarm.mdl", self.health);
					self.model = "progs/zombie_noarms.mdl";
					setmodel(self, "progs/zombie_noarms.mdl");
					self.goalentity = world;
					setsize(self, ZOMB_MIN, ZOMB_MAX);
				}
			}
			if ((self.model == "progs/zombie1.mdl"))
			{
				ThrowGib("progs/gib_zarm.mdl", self.health);
				self.model = "progs/zombie1_onearm.mdl";
				setmodel(self, "progs/zombie1_onearm.mdl");
				setsize(self, ZOMB_MIN, ZOMB_MAX);
			}
			else
			{
				if ((self.model == "progs/zombie1_onearm.mdl"))
				{
					ThrowGib("progs/gib_zarm.mdl", self.health);
					self.model = "progs/zombie1_noarms.mdl";
					setmodel(self, "progs/zombie1_noarms.mdl");
					self.goalentity = world;
					setsize(self, ZOMB_MIN, ZOMB_MAX);
				}
			}
		}
	}
	if ((take < 9))
	{
		return;
	}
	if ((self.inpain == 2))
	{
		return;
	}
	if ((take >= 25))
	{
		if ((autocvar_slowmotion >= 4))
		{
			if ((random() <= (autocvar_slowmotion_randomness_zombie * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		if ((((!self.shocked && (self.enemy.weapon == IT_LIGHTNING)) && (take >= 30)) && (random() < 0.8)))
		{
			self.sticky = 0;
			zombie_die();
			return;
		}
		self.inpain = 2;
		zombie_paine1();
		return;
	}
	if (self.inpain)
	{
		self.pain_finished = (time + 3);
		return;
	}
	if ((self.pain_finished > time))
	{
		if ((autocvar_slowmotion >= 4))
		{
			if ((random() <= (autocvar_slowmotion_randomness_zombie * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		self.inpain = 2;
		zombie_paine1();
		return;
	}
	self.inpain = 1;
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_zombie * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	r = random();
	if ((r < 0.25))
	{
		zombie_paina1();
	}
	else
	{
		if ((r < 0.5))
		{
			zombie_painb1();
		}
		else
		{
			if ((r < 0.75))
			{
				zombie_painc1();
			}
			else
			{
				zombie_paind1();
			}
		}
	}
};

void() zombie_lay12 = [ 173, zombie_paine13 ]
{
	self.solid = SOLID_SLIDEBOX;
	if (self.targetname)
	{
		self.use = SUB_Null;
	}
	self.th_pain = zombie_pain;
};

void() zombie_lay = [ 172, zombie_lay ]
{
	self.th_stand = zombie_stand1;
	self.th_pain = zombie_lay12;
	self.nextthink = (self.nextthink + 0.1);
	self.health = 60;
	if (!self.targetname)
	{
		if (FindTarget())
		{
			zombie_lay12();
			return;
		}
	}
	else
	{
		self.solid = 0;
		self.use = zombie_lay12;
	}
};

void(entity attacker, float take) zombie_pain_newmodel =
{
	local float r;

	self.health = 60;
	if ((attacker.weapon == IT_AXE))
	{
		self.axehitcount = (self.axehitcount + 1);
	}
	if ((take < 9))
	{
		return;
	}
	if ((self.inpain == 2))
	{
		return;
	}
	if ((attacker.weapon != IT_AXE))
	{
		if ((take >= 25))
		{
			if ((autocvar_slowmotion >= 4))
			{
				if ((random() <= (autocvar_slowmotion_randomness_zombie * 0.01)))
				{
					the_matrix = 1;
					matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
				}
			}
			self.inpain = 2;
			zombie_paine1();
			return;
		}
	}
	if (self.inpain)
	{
		self.pain_finished = (time + 3);
		return;
	}
	if ((attacker.weapon != IT_AXE))
	{
		if ((self.pain_finished > time))
		{
			if ((autocvar_slowmotion >= 4))
			{
				if ((random() <= (autocvar_slowmotion_randomness_zombie * 0.01)))
				{
					the_matrix = 1;
					matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
				}
			}
			self.inpain = 2;
			zombie_paine1();
			return;
		}
	}
	self.inpain = 1;
	if ((attacker.weapon != IT_AXE))
	{
		if ((autocvar_slowmotion >= 4))
		{
			if ((random() <= (autocvar_slowmotion_randomness_zombie * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		r = random();
		if ((r < 0.25))
		{
			zombie_paina1();
		}
		else
		{
			if ((r < 0.5))
			{
				zombie_painb1();
			}
			else
			{
				if ((r < 0.75))
				{
					zombie_painc1();
				}
				else
				{
					zombie_paind1();
				}
			}
		}
	}
	else
	{
		if ((autocvar_slowmotion >= 4))
		{
			if ((random() <= (autocvar_slowmotion_randomness_zombie * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		r = random();
		if ((r < 0.5))
		{
			zombie_paina1();
		}
		else
		{
			zombie_paind1();
		}
	}
};

void() monster_zombie =
{
	local float zufall;
	local float new_zombie;
	local float zuffa;
	local entity pain_skin_entity;
	local float replacer;
	local vector check;
	local float replacez;
	local float replac;
	local float replacce;
	local float replace;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/zombie.mdl");
	precache_model("progs/h_zombie.mdl");
	precache_model("progs/zom_gib.mdl");
	precachegibs_zom();
	precache_model("progs/zombie_new_projectile.mdl");
	precache_sound("zombie/z_idle.wav");
	precache_sound("zombie/z_idle1.wav");
	precache_sound("zombie/z_shot1.wav");
	precache_sound("zombie/z_gib.wav");
	precache_sound("zombie/z_pain.wav");
	precache_sound("zombie/z_pain1.wav");
	precache_sound("zombie/z_fall.wav");
	precache_sound("zombie/z_miss.wav");
	precache_sound("zombie/z_hit.wav");
	precache_sound("zombie/idle_w2.wav");
	precache_sound("walk/zombierun1.wav");
	precache_sound("walk/zombierun2.wav");
	precache_sound("walk/zombiewalk1.wav");
	precache_sound("walk/zombiewalk2.wav");
	precache_sound("zombie/cut_head.wav");
	precache_sound("zombie/zombie_die.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.netname = "monster_zombie";
	if ((autocvar_zombiemultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/zombie.mdl");
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
		if ((autocvar_zombiemultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/zombie1.mdl");
			precache_model("progs/h_zombie1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/zombie.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/zombie1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_zombiemultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/zombie1.mdl");
				precache_model("progs/h_zombie1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/zombie.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/zombie.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/zombie1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_zombiemultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/zombie1.mdl");
					precache_model("progs/h_zombie1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/zombie.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/zombie.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/zombie1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/zombie1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/zombie.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_zombie_use_newmodel && (world.model != "maps/start.bsp")))
	{
		new_zombie = autocvar_zombie_use_newmodel * 0.01;
		if ((random() < new_zombie))
		{
			precache_model("progs/zombie_new.mdl");
			precache_model("progs/zombie_new_headless.mdl");
			precache_model("progs/h_zombie_new.mdl");
			setmodel(self, "progs/zombie_new.mdl");
			zufall = random();
			if ((zufall > 0.5))
			{
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 2;
			}
			else
			{
				self.skin = 1;
				self.monsterskin = 1;
				self.monstermodel = 2;
			}
		}
	}
	if ((autocvar_zombie_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.14;
			self.sizediff = '0 0 3';
			setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.07;
				self.sizediff = '0 0 1';
				setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
			}
			else
			{
				self.scale = 1;
				setsize(self, ZOMB_MIN, ZOMB_MAX);
			}
		}
	}
	else
	{
		if ((autocvar_zombie_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.21;
				self.sizediff = '0 0 5';
				setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.14;
					self.sizediff = '0 0 3';
					setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.75))
					{
						self.scale = 1.07;
						self.sizediff = '0 0 1';
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, ZOMB_MIN, ZOMB_MAX);
					}
				}
			}
		}
		else
		{
			if ((autocvar_zombie_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.28;
					self.sizediff = '0 0 7';
					setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.21;
						self.sizediff = '0 0 5';
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.14;
							self.sizediff = '0 0 3';
							setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.07;
								self.sizediff = '0 0 1';
								setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
							}
							else
							{
								self.scale = 1;
								setsize(self, ZOMB_MIN, ZOMB_MAX);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_zombie_size == 4))
				{
					zuffa = random();
					if ((zuffa <= 0.17))
					{
						self.scale = 1.35;
						self.sizediff = '0 0 9';
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.34))
						{
							self.scale = 1.28;
							self.sizediff = '0 0 7';
							setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.5))
							{
								self.scale = 1.21;
								self.sizediff = '0 0 5';
								setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
							}
							else
							{
								if ((zuffa <= 0.67))
								{
									self.scale = 1.14;
									self.sizediff = '0 0 3';
									setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
								}
								else
								{
									if ((zuffa <= 0.84))
									{
										self.scale = 1.07;
										self.sizediff = '0 0 1';
										setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
									}
									else
									{
										self.scale = 1;
										setsize(self, ZOMB_MIN, ZOMB_MAX);
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_zombie_size > 3))
					{
						if ((autocvar_zombie_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_zombie_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_zombie_size * 0.25);
						self.sizediff = self.sizefactor;
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, ZOMB_MIN, ZOMB_MAX);
					}
				}
			}
		}
	}
	self.health = 60;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_zombie_random_skin_colors))
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
	self.th_stand = zombie_stand1;
	self.th_walk = zombie_walk1;
	self.th_run = zombie_run1;
	if ((autocvar_zombienewmodelproperties == 1))
	{
		if ((self.monstermodel == 2))
		{
			self.th_pain = zombie_pain_newmodel;
		}
		else
		{
			self.th_pain = zombie_pain;
		}
	}
	else
	{
		if ((autocvar_zombienewmodelproperties >= 2))
		{
			if ((self.monstermodel == 2))
			{
				self.th_pain = zombie_pain_newmodel;
				self.health = 490;
			}
			else
			{
				self.th_pain = zombie_pain;
			}
		}
		else
		{
			self.th_pain = zombie_pain;
		}
	}
	self.th_die = zombie_die;
	self.th_missile = zombie_missile;
	if ((self.spawnflags & SPAWN_CRUCIFIED))
	{
		if ((autocvar_wallzombie >= 1))
		{
			self.takedamage = DAMAGE_AIM;
			self.inpain = 2;
		}
		self.movetype = 0;
		if ((autocvar_zombiecrucifiedflies == 1))
		{
			self.traileffectnum = particleeffectnum(/*56318i*/"zombiefliescrucifiedblack");
		}
		if ((autocvar_zombiecrucifiedflies == 2))
		{
			self.traileffectnum = particleeffectnum(/*56344i*/"zombiefliescrucifiedbrown");
		}
		if ((self.monstermodel == 2))
		{
			setmodel(self, "progs/zombie.mdl");
			self.th_pain = zombie_pain;
			self.health = 60;
			if ((autocvar_zombiemultiskin >= 2))
			{
				zufall = random();
				if ((zufall >= 0.5))
				{
					self.monstermodel = 0;
				}
				else
				{
					self.monstermodel = 1;
				}
			}
			else
			{
				self.monstermodel = 0;
			}
		}
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
		zombie_cruc1();
	}
	else
	{
		if (((autocvar_zombieflies == 1) && (pointcontents(self.origin) != CONTENT_WATER)))
		{
			self.traileffectnum = particleeffectnum(/*19589i*/"zombiefliesblack");
		}
		if (((autocvar_zombieflies == 2) && (pointcontents(self.origin) != CONTENT_WATER)))
		{
			self.traileffectnum = particleeffectnum(/*19606i*/"zombiefliesbrown");
		}
		self.alpha = (autocvar_monstertransparency * 0.01);
		if ((autocvar_spider_replace_zombie && !(self.spawnflags & SPAWN_CRUCIFIED)))
		{
			replacer = autocvar_spider_replace_zombie * 0.01;
			if (((cvar("quadreplacer") > 0) && (replacer > 0)))
			{
				replacer = replacer + 0.02;
			}
			if ((random() <= replacer))
			{
				check = (self.origin - '0 0 20') + '0 0 1';
				if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
				{
					self.skin = 6;
					self.health = 70;
					self.scale = 1;
					setsize(self, VEC_HULL_MIN, '16 16 40');
					self.nextthink = (time + 0.3);
					self.think = SUB_Remove;
					monster_spider_start();
					return;
				}
			}
		}
		if ((autocvar_reiver_replace_zombie && !(self.spawnflags & SPAWN_CRUCIFIED)))
		{
			replacez = autocvar_reiver_replace_zombie * 0.01;
			if ((random() <= replacez))
			{
				self.health = 70;
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 40');
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_reiver_liftorigin_start();
				return;
			}
		}
		if ((autocvar_afrit_replace_zombie && !(self.spawnflags & SPAWN_CRUCIFIED)))
		{
			replac = autocvar_afrit_replace_zombie * 0.01;
			if ((random() <= replac))
			{
				self.health = 70;
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
		if ((self.spawnflags & SPAWN_LYINGDOWN))
		{
			self.th_stand = zombie_lay;
		}
		if (autocvar_reiver_supports_zombie)
		{
			replacce = autocvar_reiver_supports_zombie * 0.01;
			if ((cvar("quadreplacer") > 0))
			{
				replacce = replacce + 0.01;
			}
			if ((random() <= replacce))
			{
				add_reiver_support_walk();
			}
		}
		if (autocvar_afrit_supports_zombie)
		{
			replace = autocvar_afrit_supports_zombie * 0.01;
			if ((random() <= replace))
			{
				add_afrit_support_walk();
			}
		}
		do_the_cloning();
	}
	MonsterPhysics(self, autocvar_zombiemass);
};
