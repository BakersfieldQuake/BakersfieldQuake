//Decompiled code. Please respect the original copyright.

void() Laser_Touch =
{
	local vector org;

	if ((other == self.owner))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	sound7(self, CHAN_WEAPON, "enforcer/enfstop.wav", 1, ATTN_STATIC);
	org = self.origin - (8 * normalize(self.velocity));
	if (other.health)
	{
		SpawnBlood(org, (self.velocity * 0.2), 15);
		if ((other.health < 25))
		{
			T_Damage(other, self, self.owner, (autocvar_enforcer_laser * 15));
		}
		if ((autocvar_enforcer_size_influenced_attack == 1))
		{
			T_Damage(other, self, self.owner, (autocvar_enforcer_laser * self.owner.scale));
		}
		else
		{
			T_Damage(other, self, self.owner, autocvar_enforcer_laser);
		}
	}
	else
	{
		if ((self.model == "progs/lasrspik.mdl"))
		{
			sendParticle("hiplaser_impact", org, VEC_ORIGIN, 1);
		}
		else
		{
			sendParticle("laser_impact", org, VEC_ORIGIN, 1);
		}
	}
	laserdie();
	remove(self);
};

void() Laser_Touch2 =
{
	local vector org;

	if ((other == self.owner))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	sound7(self, CHAN_WEAPON, "enforcer/enfstop.wav", 1, ATTN_STATIC);
	org = self.origin - (8 * normalize(self.velocity));
	if (other.health)
	{
		SpawnBlood(org, (self.velocity * 0.2), 15);
		T_Damage(other, self, self.owner, 14);
	}
	else
	{
		pointparticles(particleeffectnum(/*57867i*/"laser_impact2"), org, VEC_ORIGIN, 1);
	}
	remove(self);
};

void(vector org, vector vec) LaunchLaser =
{
	if (((self.classname == "monster_freddie") || (((self.classname == "monster_enforcer") && (self.skin == 1)) && (autocvar_enforcer_defender == 1))))
	{
		sound7(self, CHAN_WEAPON, "hipweap/laserg.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((self.classname == "monster_enforcer"))
		{
			sound7(self, CHAN_WEAPON, "enforcer/enfire.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
	vec = normalize(vec);
	newmis = spawn();
	newmis.owner = self;
	newmis.movetype = MOVETYPE_FLY;
	newmis.solid = SOLID_BBOX;
	if ((((self.classname == "monster_jim") || (self.classname == "monster_freddie")) || ((self.skin == 1) && (autocvar_enforcer_defender == 1))))
	{
		newmis.traileffectnum = particleeffectnum(/*25495i*/"hiplaser_trail");
		setmodel(newmis, "progs/lasrspik.mdl");
	}
	else
	{
		newmis.traileffectnum = particleeffectnum(/*25498i*/"laser_trail");
		setmodel(newmis, "progs/laser.mdl");
	}
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, org);
	newmis.velocity = (vec * 600);
	newmis.angles = vectoangles(newmis.velocity);
	newmis.nextthink = (time + 5);
	newmis.think = SUB_Remove;
	newmis.touch = Laser_Touch;
};

void(vector org, vector vec) LaunchLaser2 =
{
	if ((self.classname == "monster_enforcer"))
	{
		sound7(self, CHAN_WEAPON, "enforcer/enfire.wav", 1, ATTN_NORM, SNDSPD);
	}
	vec = normalize(vec);
	newmis = spawn();
	newmis.owner = self;
	newmis.movetype = MOVETYPE_FLY;
	newmis.solid = SOLID_BBOX;
	newmis.traileffectnum = particleeffectnum(/*57881i*/"laser_trail2");
	setmodel(newmis, "progs/laser.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, org);
	newmis.velocity = (vec * 600);
	newmis.angles = vectoangles(newmis.velocity);
	newmis.nextthink = (time + 5);
	newmis.think = SUB_Remove;
	newmis.touch = Laser_Touch2;
};

void() def_FireGrenade =
{
	local vector distancedelta;
	local vector nozdistancedelta;
	local entity missile;

	self.effects = (self.effects | EF_MUZZLEFLASH);
	sound7(self, CHAN_WEAPON, "weapons/grenade.wav", 1, ATTN_NORM, SNDSPD);
	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	makevectors(self.angles);
	if (((autocvar_ogreaim == 0) || (skill < 2)))
	{
		missile.velocity = normalize((self.enemy.origin - self.origin));
		missile.velocity = (missile.velocity * 600);
		missile.velocity_z = 180;
	}
	else
	{
		distancedelta = self.enemy.origin - self.origin;
		nozdistancedelta = distancedelta;
		missile.velocity = normalize(distancedelta);
		missile.velocity = (missile.velocity * (500 + (random() * 100)));
		missile.velocity_z = ((missile.velocity_z + 150) + ((vlen(nozdistancedelta) * 0.22) * (1 + (0.3 * random()))));
	}
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.classname = "proximity_grenade";
	missile.touch = ProximityGrenadeTouch;
	missile.health = 5;
	missile.state = 0;
	missile.scale = 0.9;
	missile.nextthink = (time + 2);
	missile.delay = ((time + 15) + (10 * random()));
	missile.think = ProximityBomb;
	missile.th_die = ProximityGrenadeExplode;
	setmodel(missile, "progs/proxbomb.mdl");
	missile.traileffectnum = particleeffectnum("monsternull");	// no smoke trail
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(missile, self.origin);
};

void() enforcer_fire =
{
	local vector org;

	self.effects = (self.effects | EF_MUZZLEFLASH);
	makevectors(self.angles);
	org = ((self.origin + (v_forward * 30)) + (v_right * 8.5)) + '0 0 16';
	LaunchLaser(org, (self.enemy.origin - self.origin));
};

void(float loudness) enforcer_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.25))
		{
			sound7(self, CHAN_AUTO, "walk/enforcer1.wav", loudness, ATTN_IDLE, SNDSPD);
		}
		else
		{
			if ((select <= 0.5))
			{
				sound7(self, CHAN_AUTO, "walk/enforcer2.wav", loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				if ((select <= 0.75))
				{
					sound7(self, CHAN_AUTO, "walk/enforcer3.wav", loudness, ATTN_IDLE, SNDSPD);
				}
				else
				{
					sound7(self, CHAN_AUTO, "walk/enforcer4.wav", loudness, ATTN_IDLE, SNDSPD);
				}
			}
		}
	}
};

void() enf_stand1 = [ 0, enf_stand2 ]
{
	ai_stand();
};

void() enf_stand2 = [ 1, enf_stand3 ]
{
	ai_stand();
};

void() enf_stand3 = [ 2, enf_stand4 ]
{
	ai_stand();
};

void() enf_stand4 = [ 3, enf_stand5 ]
{
	ai_stand();
};

void() enf_stand5 = [ 4, enf_stand6 ]
{
	ai_stand();
};

void() enf_stand6 = [ 5, enf_stand7 ]
{
	ai_stand();
};

void() enf_stand7 = [ 6, enf_stand1 ]
{
	ai_stand();
};

void() enf_walk1 = [ 7, enf_walk2 ]
{
	if ((random() < 0.2))
	{
		if ((self.skin == 1))
		{
			sound7(self, CHAN_VOICE, "enforcer/def_idle1.wav", 1, ATTN_IDLE, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "enforcer/idle1.wav", 1, ATTN_IDLE, SNDSPD);
		}
	}
	ai_walk(2);
	enforcer_footsteps(0.95);
};

void() enf_walk2 = [ 8, enf_walk3 ]
{
	ai_walk(4);
};

void() enf_walk3 = [ 9, enf_walk4 ]
{
	ai_walk(4);
};

void() enf_walk4 = [ 10, enf_walk5 ]
{
	ai_walk(3);
};

void() enf_walk5 = [ 11, enf_walk6 ]
{
	ai_walk(1);
};

void() enf_walk6 = [ 12, enf_walk7 ]
{
	ai_walk(2);
};

void() enf_walk7 = [ 13, enf_walk8 ]
{
	ai_walk(2);
};

void() enf_walk8 = [ 14, enf_walk9 ]
{
	ai_walk(1);
};

void() enf_walk9 = [ 15, enf_walk10 ]
{
	ai_walk(2);
};

void() enf_walk10 = [ 16, enf_walk11 ]
{
	ai_walk(4);
	enforcer_footsteps(0.95);
};

void() enf_walk11 = [ 17, enf_walk12 ]
{
	ai_walk(4);
};

void() enf_walk12 = [ 18, enf_walk13 ]
{
	ai_walk(1);
};

void() enf_walk13 = [ 19, enf_walk14 ]
{
	ai_walk(2);
};

void() enf_walk14 = [ 20, enf_walk15 ]
{
	ai_walk(3);
};

void() enf_walk15 = [ 21, enf_walk16 ]
{
	ai_walk(4);
};

void() enf_walk16 = [ 22, enf_walk1 ]
{
	ai_walk(2);
};

void() enf_run1 = [ 23, enf_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((random() < 0.2))
	{
		if ((self.skin == 1))
		{
			sound7(self, CHAN_VOICE, "enforcer/def_idle1.wav", 1, ATTN_IDLE, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "enforcer/idle1.wav", 1, ATTN_IDLE, SNDSPD);
		}
	}
	ai_run(18);
};

void() enf_run2 = [ 24, enf_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(14);
};

void() enf_run3 = [ 25, enf_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(7);
	enforcer_footsteps(1);
};

void() enf_run4 = [ 26, enf_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(12);
};

void() enf_run5 = [ 27, enf_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(14);
};

void() enf_run6 = [ 28, enf_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(14);
};

void() enf_run7 = [ 29, enf_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(7);
	enforcer_footsteps(1);
};

void() enf_run8 = [ 30, enf_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(11);
};

void() enf_prox1 = [ 31, enf_prox2 ]
{
	self.nextthink = ((time + 0.14) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	sound7(self, CHAN_WEAPON, "weapons/weapon6.wav", 1, ATTN_NORM, SNDSPD);
};

void() enf_prox2 = [ 32, enf_prox3 ]
{
	self.nextthink = ((time + 0.14) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_prox3 = [ 33, enf_prox4 ]
{
	self.nextthink = ((time + 0.14) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_prox4 = [ 34, enf_prox5 ]
{
	self.nextthink = ((time + 0.15) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_prox5 = [ 35, enf_prox6 ]
{
	self.nextthink = ((time + 0.15) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_prox6 = [ 36, enf_prox7 ]
{
	self.nextthink = ((time + 0.15) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	if ((visible(self.enemy) || (random() < 0.4)))
	{
		def_FireGrenade();
	}
};

void() enf_prox7 = [ 37, enf_prox8 ]
{
	self.nextthink = ((time + 0.13) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_prox8 = [ 38, enf_prox9 ]
{
	self.nextthink = ((time + 0.12) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_prox9 = [ 39, enf_prox10 ]
{
	self.nextthink = ((time + 0.11) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_prox10 = [ 40, enf_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk1 = [ 31, enf_atk2 ]
{

	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((((random() < 0.05) && (self.skin == 1)) && (vlen((self.enemy.origin - self.origin)) > 300)))
	{
		enf_prox1();
	}
};

void() enf_atk2 = [ 32, enf_atk3 ]
{
	self.nextthink = (((time + 0.11) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk3 = [ 33, enf_atk4 ]
{
	self.nextthink = (((time + 0.11) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk4 = [ 34, enf_atk5 ]
{
	self.nextthink = (((time + 0.11) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk5 = [ 35, enf_atk6 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk6 = [ 36, enf_atk7 ]
{
	self.nextthink = (((time + 0.11) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	enforcer_fire();
};

void() enf_atk7 = [ 37, enf_atk8 ]
{
	self.nextthink = (((time + 0.11) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk8 = [ 38, enf_atk9 ]
{
	self.nextthink = (((time + 0.11) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk9 = [ 35, enf_atk10 ]
{
	self.nextthink = (((time + 0.11) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk10 = [ 36, enf_atk11 ]
{
	local vector spot1;
	local vector spot2;
	local entity targ;

	self.nextthink = (((time + 0.11) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	enforcer_fire();
	targ = self.enemy;
	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	traceline(spot1, spot2, FALSE, self);
	if (((trace_ent != targ) || (trace_inopen && trace_inwater)))
	{
	}
	else
	{
		random();
		if (((random() < (0.1 + (skill * 0.1))) && (self.skin == 1)))
		{
			enf_atk7();
		}
	}
};

void() enf_atk11 = [ 37, enf_atk12 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk12 = [ 38, enf_atk13 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk13 = [ 39, enf_atk14 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_atk14 = [ 40, enf_run1 ]
{
	self.nextthink = (((time + 0.1) - (skill * 0.01)) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	SUB_CheckRefire(enf_atk1);
	random();
	if ((random() < (0.05 + (skill * 0.05))))
	{
		self.has_fired = 1;
	}
};

void() enf_altfir1 = [ 31, enf_altfir2 ]
{
	self.nextthink = ((time + 0.12) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	sound7(self, CHAN_WEAPON, "enforcer/def_ssg_load.wav", 1, ATTN_NORM, SNDSPD);
};

void() enf_altfir2 = [ 32, enf_altfir3 ]
{
	self.nextthink = ((time + 0.12) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_altfir3 = [ 33, enf_altfir4 ]
{
	self.nextthink = ((time + 0.11) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_altfir4 = [ 34, enf_altfir5 ]
{
	self.nextthink = ((time + 0.11) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_altfir5 = [ 35, enf_altfir6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_altfir6 = [ 36, enf_altfir7 ]
{
	local vector org;

	makevectors(self.angles);
	org = ((self.origin + (v_up * 17)) + (v_right * 7)) + (v_forward * 17);
	pointparticles(particleeffectnum(/*54914i*/"soldier_muzzleflash"), org, VEC_ORIGIN, 1);
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	army_fire();
};

void() enf_altfir7 = [ 37, enf_altfir8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_altfir8 = [ 38, enf_altfir9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	casing(1);
	casing(1);
};

void() enf_altfir9 = [ 39, enf_altfir10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_altfir10 = [ 40, enf_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() enf_paina1 = [ 66, enf_paina2 ]
{
};

void() enf_paina2 = [ 67, enf_paina3 ]
{
};

void() enf_paina3 = [ 68, enf_paina4 ]
{
};

void() enf_paina4 = [ 69, enf_run1 ]
{
};

void() enf_painb1 = [ 70, enf_painb2 ]
{
};

void() enf_painb2 = [ 71, enf_painb3 ]
{
};

void() enf_painb3 = [ 72, enf_painb4 ]
{
};

void() enf_painb4 = [ 73, enf_painb5 ]
{
};

void() enf_painb5 = [ 74, enf_run1 ]
{
};

void() enf_painc1 = [ 75, enf_painc2 ]
{
};

void() enf_painc2 = [ 76, enf_painc3 ]
{
};

void() enf_painc3 = [ 77, enf_painc4 ]
{
};

void() enf_painc4 = [ 78, enf_painc5 ]
{
};

void() enf_painc5 = [ 79, enf_painc6 ]
{
};

void() enf_painc6 = [ 80, enf_painc7 ]
{
};

void() enf_painc7 = [ 81, enf_painc8 ]
{
};

void() enf_painc8 = [ 82, enf_run1 ]
{
};

void() enf_wounded1 = [ 102, enf_wounded2 ]
{
};

void() enf_wounded2 = [ 103, enf_wounded3 ]
{
};

void() enf_wounded3 = [ 104, enf_wounded4 ]
{
};

void() enf_wounded4 = [ 105, enf_wounded5 ]
{
	sendParticle("bleed", self.origin, VEC_ORIGIN, 1, 0);
};

void() enf_wounded5 = [ 106, enf_wounded6 ]
{
};

void() enf_wounded6 = [ 107, enf_wounded7 ]
{
};

void() enf_wounded7 = [ 108, enf_wounded8 ]
{
};

void() enf_wounded8 = [ 107, enf_wounded9 ]
{
};

void() enf_wounded9 = [ 106, enf_wounded4 ]
{
	if (((random() * 100) < 10))
	{
		sound7(self, CHAN_VOICE, "enforcer/pain2.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if (((random() * 100) < 5))
		{
			sound7(self, CHAN_VOICE, "enforcer/pain1.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() enf_paind1 = [ 83, enf_paind2 ]
{
};

void() enf_paind2 = [ 84, enf_paind3 ]
{
};

void() enf_paind3 = [ 85, enf_paind4 ]
{
};

void() enf_paind4 = [ 86, enf_paind5 ]
{
	ai_painforward(2);
};

void() enf_paind5 = [ 87, enf_paind6 ]
{
	ai_painforward(1);
};

void() enf_paind6 = [ 88, enf_paind7 ]
{
};

void() enf_paind7 = [ 89, enf_paind8 ]
{
};

void() enf_paind8 = [ 90, enf_paind9 ]
{
};

void() enf_paind9 = [ 91, enf_paind10 ]
{
};

void() enf_paind10 = [ 92, enf_paind11 ]
{
};

void() enf_paind11 = [ 93, enf_paind12 ]
{
	ai_painforward(1);
};

void() enf_paind12 = [ 94, enf_paind13 ]
{
	ai_painforward(1);
};

void() enf_paind13 = [ 95, enf_paind14 ]
{
	ai_painforward(1);
	enforcer_footsteps(0.9);
};

void() enf_paind14 = [ 96, enf_paind15 ]
{
};

void() enf_paind15 = [ 97, enf_paind16 ]
{
};

void() enf_paind16 = [ 98, enf_paind17 ]
{
	ai_pain(1);
};

void() enf_paind17 = [ 99, enf_paind18 ]
{
	ai_pain(1);
};

void() enf_paind18 = [ 100, enf_paind19 ]
{
};

void() enf_paind19 = [ 101, enf_run1 ]
{
};

void(entity attacker, float damage) enf_pain =
{
	local float r;
	local entity ball;

	r = random();
	setsize(self, ARMY_MIN, ARMY_MAX);
	if ((((random() * 100) < (8 - skill)) && (self.health < (45 - (skill * 4)))))
	{
		self.model = "progs/enforcernail.mdl";
		setmodel(self, "progs/enforcernail.mdl");
		setsize(self, VEC_HULL_MIN, '16 16 14');
		enf_wounded1();
	}
	if ((((self.enemy.meleeing == 0) && (((self.enemy.weapon != IT_AXE) || (self.enemy.weapon != IT_GRENADE_LAUNCHER)) || (self.enemy.weapon != IT_ROCKET_LAUNCHER))) && (self.health < 60)))
	{
		self.model = "progs/enforcernail.mdl";
		setmodel(self, "progs/enforcernail.mdl");
		setsize(self, ARMY_MIN, ARMY_MAX);
	}
	random();
	if ((random() < (0.15 + (skill * 0.05))))
	{
		self.has_fired = 1;
	}
	if ((self.skin == 1))
	{
		if ((self.health > 60))
		{
			pointparticles(particleeffectnum(/*46127i*/"shambler_ball"), self.origin, VEC_ORIGIN, 1);
			sound7(self, CHAN_VOICE, "enforcer/enfstop.wav", 1, ATTN_NORM, (SNDSPD * 1.1));
			ball = spawn();
			setmodel(ball, "progs/plasma.mdl");
			ball.solid = SOLID_BBOX;
			ball.movetype = MOVETYPE_FLY;
			setsize(ball, VEC_ORIGIN, VEC_ORIGIN);
			setorigin(ball, self.origin);
			ball.scale = 4.6;
			ball.alpha = 0.3;
			ball.avelocity = '700 600 900';
			ball.glow_color = 200;
			ball.glow_size = 230;
			self.glow_size = (self.glow_size - damage);
			ball.nextthink = (time + 0.2);
			ball.think = SUB_Remove;
			if ((r < 0.25))
			{
				return;
			}
		}
		else
		{
			if ((self.glow_size > 0))
			{
				self.glow_size = 0;
				pointparticles(particleeffectnum(/*58042i*/"vore_shockwave"), self.origin, VEC_ORIGIN, 1);
				particle_explode(self.origin, (10 + (random() * 10)), (0.5 + random()), PARTICLE_BURST_BLUE, 0);
				sound7(self, CHAN_VOICE, "break/glass_i2.wav", 1, ATTN_NORM, (SNDSPD * 1.1));
				self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
			}
		}
	}
	if ((self.dodge_finished > time))
	{
		return;
	}
	if ((self.pain_finished > time))
	{
		return;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_enforcer * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	if ((r < 0.5))
	{
		sound7(self, CHAN_VOICE, "enforcer/pain1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_VOICE, "enforcer/pain2.wav", 1, ATTN_NORM, SNDSPD);
	}
	if ((r < 0.2))
	{
		self.pain_finished = (time + 1);
		enf_paina1();
	}
	else
	{
		if ((r < 0.4))
		{
			self.pain_finished = (time + 1);
			enf_painb1();
		}
		else
		{
			if ((r < 0.7))
			{
				self.pain_finished = (time + 1);
				enf_painc1();
			}
			else
			{
				self.pain_finished = (time + 2);
				enf_paind1();
			}
		}
	}
};

void() enf_dieHS1 = [ 102, enf_dieHS2 ]
{
};

void() enf_dieHS2 = [ 103, enf_dieHS3 ]
{
	sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieHS3 = [ 104, enf_dieHS4 ]
{
	self.solid = 0;
	self.ammo_cells = autocvar_backpack_enforcer_cells;
	self.backpack_thrower = 2;
	DropBackpack();
};

void() enf_dieHS4 = [ 105, enf_dieHS5 ]
{
	ai_forward(14);
};

void() enf_dieHS5 = [ 106, enf_dieHS6 ]
{
	ai_forward(2);
};

void() enf_dieHS6 = [ 107, enf_dieHS7 ]
{
};

void() enf_dieHS7 = [ 108, enf_dieHS8 ]
{
};

void() enf_dieHS8 = [ 109, enf_dieHS9 ]
{
};

void() enf_dieHS9 = [ 110, enf_dieHS10 ]
{
	ai_forward(3);
};

void() enf_dieHS10 = [ 111, enf_dieHS11 ]
{
	ai_forward(5);
};

void() enf_dieHS11 = [ 112, enf_dieHS12 ]
{
	ai_forward(5);
};

void() enf_dieHS12 = [ 113, enf_dieHS13 ]
{
	ai_forward(5);
};

void() enf_dieHS13 = [ 114, enf_dieHS14 ]
{
	sound7(self, CHAN_AUTO, "enforcer/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieHS14 = [ 115, enf_dieHS15 ]
{
};

void() enf_dieHS15 = [ 116, enf_dieHS16 ]
{
	if ((autocvar_bloodextension == 1))
	{
		particleeffectnum(/*15139i*/"blood_spurt");
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), (self.origin - '0 0 10'), VEC_ORIGIN, 1);
	}
};

void() enf_dieHS16 = [ 117, enf_dieHS16 ]
{
	if ((autocvar_enforcercorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	CopyMonsterToBodyQue(autocvar_enforcercorpsehealth, "progs/gib_enforcer_rarm.mdl");
};

void() enf_diessg1 = [ 102, enf_diessg2 ]
{
};

void() enf_diessg2 = [ 103, enf_diessg3 ]
{
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_diessg3 = [ 104, enf_diessg4 ]
{
	self.solid = 0;
	self.ammo_cells = autocvar_backpack_enforcer_cells;
	self.backpack_thrower = 2;
	DropBackpack();
};

void() enf_diessg4 = [ 105, enf_diessg5 ]
{
	ai_forward(14);
};

void() enf_diessg5 = [ 106, enf_diessg6 ]
{
	ai_forward(2);
};

void() enf_diessg6 = [ 107, enf_diessg7 ]
{
};

void() enf_diessg7 = [ 108, enf_diessg8 ]
{
};

void() enf_diessg8 = [ 109, enf_diessg9 ]
{
};

void() enf_diessg9 = [ 110, enf_diessg10 ]
{
	ai_forward(3);
};

void() enf_diessg10 = [ 111, enf_diessg11 ]
{
	ai_forward(5);
};

void() enf_diessg11 = [ 112, enf_diessg12 ]
{
	ai_forward(5);
};

void() enf_diessg12 = [ 113, enf_diessg13 ]
{
	ai_forward(5);
};

void() enf_diessg13 = [ 114, enf_diessg14 ]
{
	sound7(self, CHAN_AUTO, "enforcer/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_diessg14 = [ 115, enf_diessg15 ]
{
};

void() enf_diessg15 = [ 116, enf_diessg16 ]
{
	if ((autocvar_bloodextension == 1))
	{
		particleeffectnum(/*15139i*/"blood_spurt");
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), (self.origin - '0 0 10'), VEC_ORIGIN, 1);
	}
};

void() enf_diessg16 = [ 117, enf_diessg16 ]
{
	if ((autocvar_enforcercorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	CopyMonsterToBodyQue(autocvar_enforcercorpsehealth, "progs/gib_enforcer_rarm.mdl");
};

void() enf_dieng1 = [ 118, enf_dieng2 ]
{
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
};

void() enf_dieng2 = [ 119, enf_dieng3 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieng3 = [ 120, enf_dieng4 ]
{
	self.solid = 0;
	self.ammo_cells = autocvar_backpack_enforcer_cells;
	self.backpack_thrower = 2;
	DropBackpack();
};

void() enf_dieng4 = [ 121, enf_dieng5 ]
{
};

void() enf_dieng5 = [ 122, enf_dieng6 ]
{
};

void() enf_dieng6 = [ 123, enf_dieng7 ]
{
};

void() enf_dieng7 = [ 124, enf_dieng8 ]
{
	sound7(self, CHAN_AUTO, "misc/gundrop.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieng8 = [ 125, enf_dieng9 ]
{
};

void() enf_dieng9 = [ 126, enf_dieng10 ]
{
};

void() enf_dieng10 = [ 127, enf_dieng11 ]
{
};

void() enf_dieng11 = [ 128, enf_dieng12 ]
{
};

void() enf_dieng12 = [ 129, enf_dieng13 ]
{
};

void() enf_dieng13 = [ 130, enf_dieng14 ]
{
};

void() enf_dieng14 = [ 131, enf_dieng15 ]
{
};

void() enf_dieng15 = [ 132, enf_dieng16 ]
{
	sound7(self, CHAN_AUTO, "enforcer/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
	}
};

void() enf_dieng16 = [ 133, enf_dieng17 ]
{
};

void() enf_dieng17 = [ 134, enf_dieng18 ]
{
};

void() enf_dieng18 = [ 135, enf_dieng19 ]
{
};

void() enf_dieng19 = [ 136, enf_dieng20 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieng20 = [ 137, enf_dieng21 ]
{
	sound7(self, CHAN_AUTO, "enforcer/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieng21 = [ 138, enf_dieng21 ]
{
	if ((autocvar_enforcercorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_enforcercorpsehealth, "progs/gib_enforcer_larm.mdl");
};

void() enf_dieax1 = [ 139, enf_dieax2 ]
{
};

void() enf_dieax2 = [ 140, enf_dieax3 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() enf_dieax3 = [ 141, enf_dieax4 ]
{
	self.solid = 0;
	self.ammo_cells = autocvar_backpack_enforcer_cells;
	self.backpack_thrower = 2;
	DropBackpack();
};

void() enf_dieax4 = [ 142, enf_dieax5 ]
{
	sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieax5 = [ 143, enf_dieax6 ]
{
	self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
};

void() enf_dieax6 = [ 144, enf_dieax7 ]
{
};

void() enf_dieax7 = [ 145, enf_dieax8 ]
{
};

void() enf_dieax8 = [ 146, enf_dieax9 ]
{
};

void() enf_dieax9 = [ 147, enf_dieax10 ]
{
};

void() enf_dieax10 = [ 148, enf_dieax11 ]
{
};

void() enf_dieax11 = [ 149, enf_dieax12 ]
{
};

void() enf_dieax12 = [ 150, enf_dieax13 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieax13 = [ 151, enf_dieax14 ]
{
};

void() enf_dieax14 = [ 152, enf_dieax15 ]
{
};

void() enf_dieax15 = [ 153, enf_dieax16 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
	self.traileffectnum = particleeffectnum(/*1i*/"");
};

void() enf_dieax16 = [ 154, enf_dieax17 ]
{
};

void() enf_dieax17 = [ 155, enf_dieax18 ]
{
};

void() enf_dieax18 = [ 156, enf_dieax19 ]
{
};

void() enf_dieax19 = [ 157, enf_dieax20 ]
{
	sound7(self, CHAN_AUTO, "misc/gundrop.wav", 1, ATTN_IDLE, SNDSPD);
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieax20 = [ 158, enf_dieax21 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
	}
	sound7(self, CHAN_AUTO, "enforcer/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieax21 = [ 159, enf_dieax21 ]
{
	if ((autocvar_knightcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	CopyMonsterToBodyQue(autocvar_enforcercorpsehealth, "progs/gib_enforcer_head.mdl");
};

void() enf_dieaxb1 = [ 160, enf_dieaxb2 ]
{
};

void() enf_dieaxb2 = [ 161, enf_dieaxb3 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
	self.traileffectnum = particleeffectnum(/*55026i*/"blood_spurt_trail");
};

void() enf_dieaxb3 = [ 162, enf_dieaxb4 ]
{
	self.solid = 0;
	self.ammo_cells = autocvar_backpack_enforcer_cells;
	self.backpack_thrower = 2;
	DropBackpack();
};

void() enf_dieaxb4 = [ 163, enf_dieaxb5 ]
{
	sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieaxb5 = [ 164, enf_dieaxb6 ]
{
};

void() enf_dieaxb6 = [ 165, enf_dieaxb7 ]
{
};

void() enf_dieaxb7 = [ 166, enf_dieaxb8 ]
{
	sound7(self, CHAN_AUTO, "misc/gundrop.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieaxb8 = [ 167, enf_dieaxb9 ]
{
};

void() enf_dieaxb9 = [ 168, enf_dieaxb10 ]
{
};

void() enf_dieaxb10 = [ 169, enf_dieaxb11 ]
{
};

void() enf_dieaxb11 = [ 170, enf_dieaxb12 ]
{
};

void() enf_dieaxb12 = [ 171, enf_dieaxb13 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieaxb13 = [ 172, enf_dieaxb14 ]
{
	sound7(self, CHAN_AUTO, "enforcer/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieaxb14 = [ 173, enf_dieaxb15 ]
{
};

void() enf_dieaxb15 = [ 174, enf_dieaxb16 ]
{
	self.traileffectnum = particleeffectnum(/*1i*/"");
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_dieaxb16 = [ 175, enf_dieaxb16 ]
{
	if ((autocvar_enforcercorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	CopyMonsterToBodyQue(autocvar_enforcercorpsehealth, "progs/w_enforcergun.mdl");
};

void() enf_dieburn1 = [ 41, enf_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
};

void() enf_dieburn2 = [ 42, enf_dieburn3 ]
{
	self.burnz_origin = 11;
};

void() enf_dieburn3 = [ 43, enf_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
	self.ammo_cells = autocvar_backpack_enforcer_cells;
	self.backpack_thrower = 2;
	DropBackpack();
};

void() enf_dieburn4 = [ 44, enf_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() enf_dieburn5 = [ 45, enf_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() enf_dieburn6 = [ 46, enf_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() enf_dieburn7 = [ 47, enf_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() enf_dieburn8 = [ 48, enf_dieburn9 ]
{
	self.burnz_origin = -6;
};

void() enf_dieburn9 = [ 49, enf_dieburn10 ]
{
	self.burnz_origin = -8;
};

void() enf_dieburn10 = [ 50, enf_dieburn10 ]
{
	self.burnz_origin = -10;
};

void() enf_die1 = [ 41, enf_die2 ]
{
};

void() enf_die2 = [ 42, enf_die3 ]
{
};

void() enf_die3 = [ 43, enf_die4 ]
{
	self.solid = 0;
	self.ammo_cells = autocvar_backpack_enforcer_cells;
	self.backpack_thrower = 2;
	DropBackpack();
};

void() enf_die4 = [ 44, enf_die5 ]
{
	ai_forward(14);
};

void() enf_die5 = [ 45, enf_die6 ]
{
	ai_forward(2);
};

void() enf_die6 = [ 46, enf_die7 ]
{
};

void() enf_die7 = [ 47, enf_die8 ]
{
};

void() enf_die8 = [ 48, enf_die9 ]
{
};

void() enf_die9 = [ 49, enf_die10 ]
{
	ai_forward(3);
};

void() enf_die10 = [ 50, enf_die11 ]
{
	ai_forward(5);
	sound7(self, CHAN_AUTO, "enforcer/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_die11 = [ 51, enf_die12 ]
{
	ai_forward(5);
};

void() enf_die12 = [ 52, enf_die13 ]
{
	ai_forward(5);
};

void() enf_die13 = [ 53, enf_die14 ]
{
};

void() enf_die14 = [ 54, enf_die14 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 25;
	if ((autocvar_enforcercorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_enforcercorpsehealth, "progs/h_mega.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_enforcercorpsehealth, "progs/h_mega1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_enforcerrandomness = autocvar_enforcerrandomness * 0.01;
		if ((autocvar_enforcer == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_enforcerrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_enforcer == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_enforcerrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/enforcer.mdl", 54, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/enforcer1.mdl", 54, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_enforcer == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_enforcerrandomness))
					{
						vengeance_enforcer("progs/enforcer.mdl", 54);
					}
				}
				else
				{
					if ((autocvar_enforcer == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_enforcerrandomness))
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
										soul("progs/enforcer.mdl", 54, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/enforcer1.mdl", 54, zet);
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

void() enf_fdie1 = [ 55, enf_fdie2 ]
{
};

void() enf_fdie2 = [ 56, enf_fdie3 ]
{
};

void() enf_fdie3 = [ 57, enf_fdie4 ]
{
	self.solid = 0;
	self.ammo_cells = autocvar_backpack_enforcer_cells;
	self.backpack_thrower = 2;
	DropBackpack();
};

void() enf_fdie4 = [ 58, enf_fdie5 ]
{
};

void() enf_fdie5 = [ 59, enf_fdie6 ]
{
};

void() enf_fdie6 = [ 60, enf_fdie7 ]
{
};

void() enf_fdie7 = [ 61, enf_fdie8 ]
{
};

void() enf_fdie8 = [ 62, enf_fdie9 ]
{
};

void() enf_fdie9 = [ 63, enf_fdie10 ]
{
	sound7(self, CHAN_AUTO, "enforcer/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() enf_fdie10 = [ 64, enf_fdie11 ]
{
};

void() enf_fdie11 = [ 65, enf_fdie11 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 25;
	if ((autocvar_enforcercorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_enforcercorpsehealth, "progs/h_mega.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_enforcercorpsehealth, "progs/h_mega1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_enforcerrandomness = autocvar_enforcerrandomness * 0.01;
		if ((autocvar_enforcer == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_enforcerrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_enforcer == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_enforcerrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/enforcer.mdl", 65, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/enforcer1.mdl", 65, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_enforcer == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_enforcerrandomness))
					{
						vengeance_enforcer("progs/enforcer.mdl", 65);
					}
				}
				else
				{
					if ((autocvar_enforcer == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_enforcerrandomness))
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
										soul("progs/enforcer.mdl", 65, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/enforcer1.mdl", 65, zet);
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

void(float maxgibs, float gibscounter) producegibs_enforcer =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/gib1.mdl", self.health);
		ThrowGib("progs/gib2.mdl", self.health);
		ThrowGib("progs/gib_soldfoot1.mdl", self.health);
		ThrowGib("progs/gib_soldfoot2.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowWeapon("progs/w_enforcergun.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_enforcer(maxgibs, gibscounter);
};

void() enf_pack =
{
	self.ammo_cells = autocvar_backpack_enforcer_cells;
	self.backpack_thrower = 2;
	DropBackpack();
};

void() enforcer_lightning_death = [ 73, enforcer_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() enforcer_lightning_death1 = [ 73, enforcer_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(1, "progs/h_mega.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(1, "progs/h_mega1.mdl");
	}
};

void() enf_inflamed1 = [ 23, enf_inflamed2 ]
{
	local float r;

	ai_run_inflamed(18);
	self.nextthink = (time + 0.07);
	r = random();
	if ((r < 0.4))
	{
		sound7(self, CHAN_VOICE, "enforcer/enfburn1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.8))
		{
			sound7(self, CHAN_VOICE, "enforcer/enfburn2.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "enforcer/enfburn3.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() enf_inflamed2 = [ 24, enf_inflamed3 ]
{
	ai_run_inflamed(14);
	self.nextthink = (time + 0.07);
};

void() enf_inflamed3 = [ 25, enf_inflamed4 ]
{
	ai_run_inflamed(7);
	enforcer_footsteps(1);
	self.nextthink = (time + 0.07);
};

void() enf_inflamed4 = [ 26, enf_inflamed5 ]
{
	ai_run_inflamed(12);
	self.nextthink = (time + 0.07);
};

void() enf_inflamed5 = [ 27, enf_inflamed6 ]
{
	ai_run_inflamed(14);
	self.nextthink = (time + 0.07);
};

void() enf_inflamed6 = [ 28, enf_inflamed7 ]
{
	ai_run_inflamed(14);
	self.nextthink = (time + 0.07);
};

void() enf_inflamed7 = [ 29, enf_inflamed8 ]
{
	ai_run_inflamed(7);
	enforcer_footsteps(1);
	self.nextthink = (time + 0.07);
};

void() enf_inflamed8 = [ 30, enf_inflamed1 ]
{
	local float r;

	ai_run_inflamed(11);
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		enf_die();
		return;
	}
	r = random();
	if ((r < 0.22))
	{
		enf_inflamed9();
	}
	else
	{
		if ((r < 0.45))
		{
			enf_inflamed15();
		}
	}
};

void() enf_inflamed9 = [ 70, enf_inflamed10 ]
{
	local float r;

	self.nextthink = (time + 0.07);
	r = random();
	if ((r < 0.4))
	{
		sound7(self, CHAN_VOICE, "enforcer/enfburn1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.8))
		{
			sound7(self, CHAN_VOICE, "enforcer/enfburn2.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "enforcer/enfburn3.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() enf_inflamed10 = [ 71, enf_inflamed11 ]
{
	self.nextthink = (time + 0.07);
};

void() enf_inflamed11 = [ 72, enf_inflamed12 ]
{
	self.nextthink = (time + 0.07);
};

void() enf_inflamed12 = [ 73, enf_inflamed13 ]
{
	self.nextthink = (time + 0.07);
};

void() enf_inflamed13 = [ 74, enf_inflamed14 ]
{
	self.nextthink = (time + 0.07);
};

void() enf_inflamed14 = [ 30, enf_inflamed1 ]
{
	ai_run_inflamed(6);
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		enf_die();
		return;
	}
};

void() enf_inflamed15 = [ 83, enf_inflamed16 ]
{
	self.nextthink = (time + 0.07);
};

void() enf_inflamed16 = [ 84, enf_inflamed17 ]
{
	local float r;

	self.nextthink = (time + 0.07);
	r = random();
	if ((r < 0.4))
	{
		sound7(self, CHAN_VOICE, "enforcer/enfburn1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.8))
		{
			sound7(self, CHAN_VOICE, "enforcer/enfburn2.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "enforcer/enfburn3.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() enf_inflamed17 = [ 85, enf_inflamed18 ]
{
	self.nextthink = (time + 0.07);
};

void() enf_inflamed18 = [ 86, enf_inflamed19 ]
{
	ai_painforward(2);
	self.nextthink = (time + 0.07);
};

void() enf_inflamed19 = [ 87, enf_inflamed20 ]
{
	ai_painforward(1);
	self.nextthink = (time + 0.07);
};

void() enf_inflamed20 = [ 88, enf_inflamed21 ]
{
	self.nextthink = (time + 0.07);
};

void() enf_inflamed21 = [ 89, enf_inflamed22 ]
{
	self.nextthink = (time + 0.06);
};

void() enf_inflamed22 = [ 90, enf_inflamed23 ]
{
	self.nextthink = (time + 0.06);
};

void() enf_inflamed23 = [ 91, enf_inflamed24 ]
{
	self.nextthink = (time + 0.06);
};

void() enf_inflamed24 = [ 92, enf_inflamed25 ]
{
	self.nextthink = (time + 0.06);
};

void() enf_inflamed25 = [ 93, enf_inflamed26 ]
{
	ai_painforward(1);
	self.nextthink = (time + 0.06);
};

void() enf_inflamed26 = [ 94, enf_inflamed27 ]
{
	ai_painforward(1);
	self.nextthink = (time + 0.06);
};

void() enf_inflamed27 = [ 95, enf_inflamed28 ]
{
	ai_painforward(1);
	enforcer_footsteps(0.9);
	self.nextthink = (time + 0.06);
};

void() enf_inflamed28 = [ 96, enf_inflamed29 ]
{
	self.nextthink = (time + 0.06);
};

void() enf_inflamed29 = [ 97, enf_inflamed30 ]
{
	self.nextthink = (time + 0.07);
};

void() enf_inflamed30 = [ 98, enf_inflamed31 ]
{
	ai_pain(1);
	self.nextthink = (time + 0.07);
};

void() enf_inflamed31 = [ 99, enf_inflamed32 ]
{
	ai_pain(1);
	self.nextthink = (time + 0.07);
};

void() enf_inflamed32 = [ 100, enf_inflamed33 ]
{
	self.nextthink = (time + 0.07);
};

void() enf_inflamed33 = [ 101, enf_inflamed1 ]
{
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		enf_die();
		return;
	}
};

void() enf_die =
{
	local float maxgibs;
	local float gibscounter;
	local float zufa;
	local float zufall;
	local float randomness;

	self.glow_size = 0;
	self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			enf_pack();
			enforcer_lightning_death();
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
	if (((self.attack_timer > 0) && (self.skin == 1)))
	{
		prox_spawn(1);
		self.attack_timer = 0;
	}
	if ((((!self.shocked && (self.enemy.meleeing || self.axhitme)) && (autocvar_berserkmode > 0)) && (random() < 0.3)))
	{
		self.health = -10;
	}
	if (((self.health < -40) || ((self.enemy.weapon == IT_CHAINSAW) && (random() < 0.3))))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_enforcer * 0.01)))
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
		ThrowHead("progs/h_mega.mdl", self.health);
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		gibdeath_effects();
		producegibs_enforcer(maxgibs, gibscounter);
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
				enf_inflamed1();
				return;
			}
		}
		else
		{
			sound7(self, CHAN_VOICE, "enforcer/death1.wav", 1, ATTN_NORM, SNDSPD);
			if ((random() > 0.5))
			{
				enf_die1();
			}
			else
			{
				enf_fdie1();
			}
			return;
		}
	}
	autocvar_enforcerrandomness = autocvar_enforcerrandomness * 0.01;
	if ((autocvar_enforcer == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_enforcerrandomness))
		{
			self.delete_painskin = 1;
			enf_dieburn1();
			return;
		}
	}
	if ((autocvar_enforcer == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_enforcerrandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				enf_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_enforcer * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "enforcer/death1.wav", 1, ATTN_NORM, SNDSPD);
	if ((random() > 0.5))
	{
		enf_die1();
	}
	else
	{
		enf_fdie1();
	}
	if ((self.enemy.meleeing == 0))
	{
		if ((self.enemy.weapon == IT_SHOTGUN))
		{
			self.model = "progs/enforcernail.mdl";
			setmodel(self, "progs/enforcernail.mdl");
		}
		if (((self.enemy.weapon == IT_SUPER_SHOTGUN) && (random() < 0.9)))
		{
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			if ((random() <= 0.5))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/gib_skull.mdl", self.health);
				self.delete_painskin = 1;
				self.model = "progs/enforcerblast.mdl";
				setmodel(self, "progs/enforcerblast.mdl");
				enf_diessg1();
				return;
			}
			else
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				enf_die1();
				sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 1, ATTN_IDLE, SNDSPD);
				ThrowHead("progs/gib_enforcer_torso.mdl", self.health);
				ThrowGib("progs/gib_enforcer_head.mdl", self.health);
				ThrowGib("progs/gib_enforcer_rarm.mdl", self.health);
				ThrowGib("progs/gib_enforcer_larm.mdl", self.health);
				ThrowGib("progs/gib_enforcer_pack.mdl", self.health);
				ThrowGib("progs/gib_enforcer_legs.mdl", self.health);
				return;
			}
		}
		if ((self.enemy.weapon == IT_NAILGUN))
		{
			if ((random() <= 0.5))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				self.model = "progs/enforcernail.mdl";
				setmodel(self, "progs/enforcernail.mdl");
				enf_dieng1();
				return;
			}
		}
		if (((self.enemy.weapon == IT_AXE) || (self.enemy.weapon == IT_CHAINSAW)))
		{
			if ((random() < 0.5))
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
					self.model = "progs/enforceraxe.mdl";
					setmodel(self, "progs/enforceraxe.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/enforceraxe.mdl";
					setmodel(self, "progs/enforceraxe.mdl");
					self.skin = 1;
				}
				enf_dieax1();
				ThrowGib("progs/chop.mdl", self.health);
				return;
			}
			else
			{
				if ((self.hitbox_pos == HEAD_SHOT))
				{
					if ((autocvar_bloodextension == 1))
					{
						pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/gib_enforcer_head.mdl", self.health);
					self.delete_painskin = 1;
					self.model = "progs/enforcerblast.mdl";
					setmodel(self, "progs/enforcerblast.mdl");
					enf_dieHS1();
					return;
				}
				else
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
						self.model = "progs/enforceraxe2.mdl";
						setmodel(self, "progs/enforceraxe2.mdl");
						self.skin = 0;
					}
					else
					{
						self.model = "progs/enforceraxe2.mdl";
						setmodel(self, "progs/enforceraxe2.mdl");
						self.skin = 1;
					}
					enf_dieaxb1();
					ThrowGib("progs/chop.mdl", self.health);
					return;
				}
			}
		}
		if ((((self.enemy.weapon == IT_ROCKET_LAUNCHER) || (self.enemy.weapon == IT_GRENADE_LAUNCHER)) || ((self.enemy.weapon == IT_CHAINSAW) && (random() > 0.5))))
		{
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			if ((random() <= 0.7))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				enf_die1();
				sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE, SNDSPD);
				ThrowHead("progs/gib_enforcer_torso.mdl", self.health);
				ThrowGib("progs/gib_enforcer_head.mdl", self.health);
				ThrowGib("progs/gib_enforcer_rarm.mdl", self.health);
				ThrowGib("progs/gib_enforcer_larm.mdl", self.health);
				ThrowGib("progs/gib_enforcer_pack.mdl", self.health);
				ThrowGib("progs/gib_enforcer_legs.mdl", self.health);
			}
		}
		if ((self.enemy.weapon == IT_SUPER_NAILGUN))
		{
			if ((self.hitbox_pos == HEAD_SHOT))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				StickGib("progs/gib_enforcer_head.mdl", self.health);
				self.delete_painskin = 1;
				self.model = "progs/enforcerblast.mdl";
				setmodel(self, "progs/enforcerblast.mdl");
				enf_dieHS1();
				return;
			}
			else
			{
				CeilSplat();
				CeilSplat();
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				enf_die1();
				sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE, SNDSPD);
				ThrowHead("progs/gib_enforcer_larm.mdl", self.health);
				StickGib("progs/gib_enforcer_torso_sng2.mdl");
				ThrowGib("progs/gib_enforcer_legs.mdl", self.health);
			}
		}
	}
};

void() precachegibs_enf =
{
	precache_model("progs/enforcerblast.mdl");
	precache_model("progs/enforcernail.mdl");
	precache_model("progs/enforceraxe.mdl");
	precache_model("progs/enforceraxe2.mdl");
	precache_model("progs/gib_enforcer_torso.mdl");
	precache_model("progs/gib_enforcer_torso_sng2.mdl");
	precache_model("progs/gib_enforcer_head.mdl");
	precache_model("progs/gib_enforcer_rarm.mdl");
	precache_model("progs/gib_enforcer_larm.mdl");
	precache_model("progs/gib_enforcer_pack.mdl");
	precache_model("progs/gib_enforcer_legs.mdl");
	precache_model("progs/plasma.mdl");
};

void() monster_enforcer =
{
	local float zufall;
	local float zuffa;
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
	precache_model2("progs/enforcer.mdl");
	precache_model2("progs/h_mega.mdl");
	precache_model2("progs/laser.mdl");
	precache_model("progs/enforcer_sphere.mdl");
	precachegibs_enf();
	precache_sound2("enforcer/death1.wav");
	precache_sound2("enforcer/enfire.wav");
	precache_sound2("enforcer/enfstop.wav");
	precache_sound2("enforcer/idle1.wav");
	precache_sound2("enforcer/pain1.wav");
	precache_sound2("enforcer/pain2.wav");
	precache_sound2("enforcer/sight1.wav");
	precache_sound2("enforcer/sight2.wav");
	precache_sound2("enforcer/sight3.wav");
	precache_sound2("enforcer/sight4.wav");
	precache_sound2("enforcer/def_ssg_fire.wav");
	precache_sound2("enforcer/def_ssg_load.wav");
	precache_sound2("enforcer/def_idle1.wav");
	precache_sound2("enforcer/def_idle2.wav");
	precache_sound2("enforcer/def_sight1.wav");
	precache_sound("enforcer/fall_backwards.wav");
	precache_sound("enforcer/fall_forwards.wav");
	precache_sound("enforcer/enfburn1.wav");
	precache_sound("enforcer/enfburn2.wav");
	precache_sound("enforcer/enfburn3.wav");
	precache_sound("walk/enforcer1.wav");
	precache_sound("walk/enforcer2.wav");
	precache_sound("walk/enforcer3.wav");
	precache_sound("walk/enforcer4.wav");
	precache_sound("break/glass_i2.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.noise = "enforcer/pain1.wav";
	if ((autocvar_enforcermultiskin == 1))
	{
		self.multiskin = 1;
		precache_model("progs/enforcer1.mdl");
		precache_model("progs/h_mega1.mdl");
		setmodel(self, "progs/enforcer.mdl");
		zufall = random();
		if (((self.spawnflags & 2) || ((zufall >= 0.1) && (self.skin != 1))))
		{
			self.skin = 0;
			self.monsterskin = 0;
			self.monstermodel = 0;
		}
		else
		{
			setmodel(self, "progs/enforcer1.mdl");
			self.skin = 1;
			self.monsterskin = 1;
			self.monstermodel = 1;
			self.traileffectnum = particleeffectnum(/*22812i*/"silver_key");
			self.glow_color = 112;
			self.glow_size = 190;
		}
	}
	else
	{
		if ((autocvar_enforcermultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/enforcer1.mdl");
			precache_model("progs/h_mega1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/enforcer.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/enforcer1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_enforcermultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/enforcer1.mdl");
				precache_model("progs/h_mega1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/enforcer.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/enforcer.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/enforcer1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_enforcermultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/enforcer1.mdl");
					precache_model("progs/h_mega1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/enforcer.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/enforcer.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/enforcer1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/enforcer1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/enforcer.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_enforcer_size == 1))
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
				setsize(self, ARMY_MIN, ARMY_MAX);
			}
		}
	}
	else
	{
		if ((autocvar_enforcer_size == 2))
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
						setsize(self, ARMY_MIN, ARMY_MAX);
					}
				}
			}
		}
		else
		{
			if ((autocvar_enforcer_size == 3))
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
								setsize(self, ARMY_MIN, ARMY_MAX);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_enforcer_size == 4))
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
										setsize(self, ARMY_MIN, ARMY_MAX);
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_enforcer_size > 4))
					{
						if ((autocvar_enforcer_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_enforcer_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_enforcer_size * 0.25);
						self.sizediff = self.sizefactor;
						setsize(self, (VEC_HULL_MIN - self.sizediff), ('16 16 40' - self.sizediff));
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
	if ((autocvar_enforcer_size_influenced_health == 1))
	{
		self.health = (autocvar_enforcer_health + ((self.scale - 1) * 100));
	}
	else
	{
		self.health = autocvar_enforcer_health;
	}
	if ((((self.classname == "monster_enforcer") && (self.skin == 1)) && (self.health < 100)))
	{
		self.health = (self.health + 100);
	}
	self.health_initial = self.health;
	if ((random() < 0.65))
	{
		self.attack_timer = 1;
	}
	if ((autocvar_monster_random_skin_color_alteration && autocvar_enforcer_random_skin_colors))
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
	if (((self.skin == 1) && (autocvar_enforcer_defender == 1)))
	{
		self.th_melee = enf_altfir1;
	}
	self.th_stand = enf_stand1;
	self.th_walk = enf_walk1;
	self.th_run = enf_run1;
	self.th_pain = enf_pain;
	self.th_die = enf_die;
	self.th_missile = enf_atk1;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_spider_replace_enforcer)
	{
		replacer = autocvar_spider_replace_enforcer * 0.01;
		if ((random() <= replacer))
		{
			check = (self.origin - '0 0 20') + '0 0 1';
			if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
			{
				self.skin = 1;
				self.health = autocvar_enforcer_health;
				self.scale = 1;
				setsize(self, VEC_HULL_MIN, '16 16 40');
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_spider_start();
				return;
			}
		}
	}
	if (autocvar_reiver_replace_enforcer)
	{
		replacez = autocvar_reiver_replace_enforcer * 0.01;
		if ((random() <= replacez))
		{
			self.health = autocvar_enforcer_health;
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_reiver_liftorigin_start();
			return;
		}
	}
	if (autocvar_afrit_replace_enforcer)
	{
		replac = autocvar_afrit_replace_enforcer * 0.01;
		if ((random() <= replac))
		{
			self.health = autocvar_enforcer_health;
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
	if (autocvar_reiver_supports_enforcer)
	{
		replacce = autocvar_reiver_supports_enforcer * 0.01;
		if ((random() <= replacce))
		{
			add_reiver_support_walk();
		}
	}
	if (((cvar("skill") == 3) && (self.skin != 1)))
	{
		replace = 0.005;
	}
	if ((random() < ((cvar("skill") * 0.01) + replace)))
	{
		traceline(self.origin, (self.origin + '0 0 76'), FALSE, self);
		if ((trace_fraction != 1))
		{
			return;
		}
		setsize(self, '-18 -18 -24', '18 18 52');
		add_freddie_support_walk();
		return;
	}
	MonsterPhysics(self, autocvar_enforcermass);
};

void() monster_defender =
{
	self.skin = 1;
	self.classname = "monster_enforcer";
	monster_enforcer();
};

void() vengeance_enforcer_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_enforcer_shoot =
{
	local float shootdmg;

	shootdmg = 1;
	T_Damage(self.enemy, self, self, shootdmg);
	self.touch = SUB_Null;
};

void() vengeance_enforcer_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_enforcer_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_run1 = [ 23, vengeance_enforcer_run2 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_run2 = [ 25, vengeance_enforcer_run3 ]
{
	ai_face();
	movetogoal(12);
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.36;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_run3 = [ 26, vengeance_enforcer_run4 ]
{
	ai_face();
	movetogoal(17);
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.32;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_run4 = [ 27, vengeance_enforcer_run5 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.29;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_run5 = [ 28, vengeance_enforcer_run6 ]
{
	ai_face();
	movetogoal(19);
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.26;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_run6 = [ 29, vengeance_enforcer_run7 ]
{
	ai_face();
	movetogoal(12);
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.23;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_run7 = [ 30, vengeance_enforcer_shoot1 ]
{
	ai_face();
	movetogoal(16);
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_shoot1 = [ 31, vengeance_enforcer_shoot2 ]
{
	ai_face();
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.18;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_shoot2 = [ 32, vengeance_enforcer_shoot3 ]
{
	ai_face();
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.16;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_shoot3 = [ 33, vengeance_enforcer_shoot4 ]
{
	ai_face();
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.14;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_shoot4 = [ 34, vengeance_enforcer_shoot5 ]
{
	ai_face();
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.12;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_shoot5 = [ 35, vengeance_enforcer_shoot6 ]
{
	ai_face();
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.09;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_shoot6 = [ 36, vengeance_enforcer_end1 ]
{
	ai_face();
	self.touch = vengeance_enforcer_touch;
	self.alpha = 0.06;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	sound7(self, CHAN_WEAPON, "enforcer/enfire.wav", 1, ATTN_NORM, SNDSPD);
	vengeance_enforcer_shoot();
};

void() vengeance_enforcer11 = [ 53, vengeance_enforcer12 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer12 = [ 52, vengeance_enforcer13 ]
{
	walkmove((self.angles_y + 180), 5);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer13 = [ 51, vengeance_enforcer14 ]
{
	walkmove((self.angles_y + 180), 5);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer14 = [ 50, vengeance_enforcer15 ]
{
	walkmove((self.angles_y + 180), 5);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer15 = [ 49, vengeance_enforcer16 ]
{
	walkmove((self.angles_y + 180), 3);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer16 = [ 48, vengeance_enforcer17 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer17 = [ 47, vengeance_enforcer18 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer18 = [ 46, vengeance_enforcer19 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer19 = [ 45, vengeance_enforcer110 ]
{
	walkmove((self.angles_y + 180), 2);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer110 = [ 44, vengeance_enforcer111 ]
{
	walkmove((self.angles_y + 180), 14);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer111 = [ 43, vengeance_enforcer112 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer112 = [ 42, vengeance_enforcer113 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer113 = [ 41, vengeance_enforcer_stand1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_stand1 = [ 0, vengeance_enforcer_run1 ]
{
	local float zufall;

	zufall = random();
	if ((zufall <= 0.25))
	{
		sound7(self, CHAN_VOICE, "enforcer/sight1.wav", 1, 4, SNDSPD);
	}
	else
	{
		if (((zufall > 0.25) && (zufall <= 0.5)))
		{
			sound7(self, CHAN_VOICE, "enforcer/sight2.wav", 1, 4, SNDSPD);
		}
		else
		{
			if (((zufall > 0.5) && (zufall <= 0.75)))
			{
				sound7(self, CHAN_VOICE, "enforcer/sight3.wav", 1, 4, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_VOICE, "enforcer/sight4.wav", 1, 4, SNDSPD);
			}
		}
	}
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer21 = [ 64, vengeance_enforcer22 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer22 = [ 63, vengeance_enforcer23 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer23 = [ 62, vengeance_enforcer24 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer24 = [ 61, vengeance_enforcer25 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer25 = [ 60, vengeance_enforcer26 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer26 = [ 59, vengeance_enforcer27 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer27 = [ 58, vengeance_enforcer28 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer28 = [ 57, vengeance_enforcer29 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer29 = [ 56, vengeance_enforcer210 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer210 = [ 55, vengeance_enforcer_stand2 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_stand2 = [ 0, vengeance_enforcer_run1 ]
{
	local float zufall;

	zufall = random();
	if ((zufall <= 0.25))
	{
		sound7(self, CHAN_VOICE, "enforcer/sight1.wav", 1, 4, SNDSPD);
	}
	else
	{
		if (((zufall > 0.25) && (zufall <= 0.5)))
		{
			sound7(self, CHAN_VOICE, "enforcer/sight2.wav", 1, 4, SNDSPD);
		}
		else
		{
			if (((zufall > 0.5) && (zufall <= 0.75)))
			{
				sound7(self, CHAN_VOICE, "enforcer/sight3.wav", 1, 4, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_VOICE, "enforcer/sight4.wav", 1, 4, SNDSPD);
			}
		}
	}
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_enforcer_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	if ((self.frame == 54))
	{
		self.think = vengeance_enforcer11;
	}
	else
	{
		self.think = vengeance_enforcer21;
	}
};

void() vengeance_enforcer_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_enforcer_bright05;
};

void() vengeance_enforcer_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_enforcer_bright04;
};

void() vengeance_enforcer_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_enforcer_bright03;
};

void() vengeance_enforcer_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_enforcer_bright02;
};

void() vengeance_enforcer_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_enforcer_bright01;
};

void(string modelname, float modelframe) vengeance_enforcer =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_FLY;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/enforcer.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/enforcer1.mdl");
		}
	}
	setsize(self, VEC_HULL_MIN, '16 16 40');
	self.frame = modelframe;
	self.solid = 0;
	vengeance_enforcer_bright00();
};
