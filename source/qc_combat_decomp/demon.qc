//Decompiled code. Please respect the original copyright.

void(float loudness) demon_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((self.monstermodel == 2))
		{
			if ((select <= 0.33))
			{
				sound7(self, CHAN_AUTO, "teneb/step1.wav", loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				if ((select <= 0.66))
				{
					sound7(self, CHAN_AUTO, "teneb/step2.wav", loudness, ATTN_IDLE, SNDSPD);
				}
				else
				{
					sound7(self, CHAN_AUTO, "teneb/step3.wav", loudness, ATTN_IDLE, SNDSPD);
				}
			}
		}
		else
		{
			if ((select <= 0.2))
			{
				sound7(self, CHAN_AUTO, "walk/demon1.wav", loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				if ((select <= 0.4))
				{
					sound7(self, CHAN_AUTO, "walk/demon2.wav", loudness, ATTN_IDLE, SNDSPD);
				}
				else
				{
					if ((select <= 0.6))
					{
						sound7(self, CHAN_AUTO, "walk/demon3.wav", loudness, ATTN_IDLE, SNDSPD);
					}
					else
					{
						if ((select <= 0.8))
						{
							sound7(self, CHAN_AUTO, "walk/demon4.wav", loudness, ATTN_IDLE, SNDSPD);
						}
						else
						{
							sound7(self, CHAN_AUTO, "walk/demon5.wav", loudness, ATTN_IDLE, SNDSPD);
						}
					}
				}
			}
		}
	}
};

void(vector org) spawn_demon_fog =
{
	s = spawn();
	s.origin = org;
	s.nextthink = (time + 0.2);
	s.think = play_teleport;
	pointparticles(particleeffectnum(/*53356i*/"demon_fog"), org, VEC_ORIGIN, 1);
};

float(entity beacon, float attack) PM_DemTeleport =
{
	local vector spot;
	local vector vec;

	if ((self.health <= 0))
	{
		return (0);
	}
	spot_x = beacon.origin_x + ((random() * 800) - 400);
	vec = normalize((spot - beacon.origin));
	traceline(beacon.origin, spot, TRUE, beacon);
	spot = trace_endpos - (vec * 50);
	if ((vlen((spot - self.origin)) < 80))
	{
		return (0);
	}
	traceline(spot, (spot - '0 0 88'), FALSE, self);
	if ((trace_endpos == (spot - '0 0 88')))
	{
		return (0);
	}
	if ((vlen((spot - self.enemy.origin)) < 320))
	{
		return (0);
	}
	if (PM_InWall(self, spot))
	{
		return (0);
	}
	if (!PM_TraceCheck(self, spot))
	{
		return (0);
	}
	if (attack)
	{
		traceline(spot, self.enemy.origin, FALSE, self);
		if ((trace_fraction < 1))
		{
			if ((trace_ent != self.enemy))
			{
				return (0);
			}
		}
	}
	setorigin(self, spot);
	self.angles_y = vectoyaw((self.enemy.origin - spot));
	self.fixangle = TRUE;
	self.velocity = (self.velocity * 0.3);
	return (TRUE);
};

void(entity beacon, float attack) PM_DemBlink =
{
	local vector org;

	org = self.origin;
	if (PM_DemTeleport(beacon, attack))
	{
		spawn_demon_fog(org);
		spawn_demon_fog(self.origin);
	}
	else
	{
		if (PM_DemTeleport(beacon, attack))
		{
			spawn_demon_fog(org);
			spawn_demon_fog(self.origin);
		}
		else
		{
			if (PM_DemTeleport(beacon, attack))
			{
				spawn_demon_fog(org);
				spawn_demon_fog(self.origin);
			}
			else
			{
				if (PM_DemTeleport(beacon, attack))
				{
					spawn_demon_fog(org);
					spawn_demon_fog(self.origin);
				}
				else
				{
					if (PM_DemTeleport(beacon, attack))
					{
						spawn_demon_fog(org);
						spawn_demon_fog(self.origin);
					}
					else
					{
						if (PM_DemTeleport(beacon, attack))
						{
							spawn_demon_fog(org);
							spawn_demon_fog(self.origin);
						}
						else
						{
							if (PM_DemTeleport(beacon, attack))
							{
								spawn_demon_fog(org);
								spawn_demon_fog(self.origin);
							}
						}
					}
				}
			}
		}
	}
};

void() PM_DemMultiBlink =
{
	local vector org;
	local float success;

	org = self.origin;
	success = 0;
	success = success + PM_DemTeleport(self, FALSE);
	if (success)
	{
		spawn_demon_fog(org);
		spawn_demon_fog(self.origin);
	}
	else
	{
		success = success + PM_DemTeleport(self, FALSE);
		if (success)
		{
			spawn_demon_fog(org);
			spawn_demon_fog(self.origin);
		}
		else
		{
			success = success + PM_DemTeleport(self, FALSE);
			if (success)
			{
				spawn_demon_fog(org);
				spawn_demon_fog(self.origin);
			}
		}
	}
};

void() teneb_stand1 = [ 84, teneb_stand2 ]
{
	ai_stand();
	self.tail_visible = 0;
	if ((random() < 0.37))
	{
		sound7(self, CHAN_VOICE, "teneb/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand2 = [ 85, teneb_stand3 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand3 = [ 86, teneb_stand4 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand4 = [ 87, teneb_stand5 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand5 = [ 88, teneb_stand6 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand6 = [ 89, teneb_stand7 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand7 = [ 90, teneb_stand8 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand8 = [ 91, teneb_stand9 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand9 = [ 92, teneb_stand10 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand10 = [ 93, teneb_stand11 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand11 = [ 94, teneb_stand12 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand12 = [ 95, teneb_stand13 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand13 = [ 96, teneb_stand14 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand14 = [ 97, teneb_stand15 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand15 = [ 98, teneb_stand16 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand16 = [ 99, teneb_stand17 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand17 = [ 100, teneb_stand18 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand18 = [ 101, teneb_stand19 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand19 = [ 102, teneb_stand20 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand20 = [ 103, teneb_stand21 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand21 = [ 104, teneb_stand22 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand22 = [ 105, teneb_stand23 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand23 = [ 106, teneb_stand24 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand24 = [ 107, teneb_stand25 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand25 = [ 108, teneb_stand26 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand26 = [ 109, teneb_stand27 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand27 = [ 110, teneb_stand28 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand28 = [ 111, teneb_stand29 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand29 = [ 112, teneb_stand30 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand30 = [ 113, teneb_stand31 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand31 = [ 114, teneb_stand32 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand32 = [ 115, teneb_stand33 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand33 = [ 116, teneb_stand34 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand34 = [ 117, teneb_stand35 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand35 = [ 118, teneb_stand36 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand36 = [ 119, teneb_stand37 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand37 = [ 120, teneb_stand38 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand38 = [ 121, teneb_stand39 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand39 = [ 122, teneb_stand40 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_stand40 = [ 123, teneb_stand1 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand1 = [ 0, demon1_stand2 ]
{
	ai_stand();
	self.tail_visible = 0;
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "demon/idle1.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand2 = [ 1, demon1_stand3 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand3 = [ 2, demon1_stand4 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand4 = [ 3, demon1_stand5 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand5 = [ 4, demon1_stand6 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand6 = [ 5, demon1_stand7 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand7 = [ 6, demon1_stand8 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand8 = [ 7, demon1_stand9 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand9 = [ 8, demon1_stand10 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand10 = [ 9, demon1_stand11 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand11 = [ 10, demon1_stand12 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand12 = [ 11, demon1_stand13 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_stand13 = [ 12, demon1_stand1 ]
{
	ai_stand();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_walk1 = [ 124, teneb_walk2 ]
{
	self.tail_visible = 0;
	ai_walk(8);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "teneb/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_walk2 = [ 125, teneb_walk3 ]
{
	ai_walk(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_walk3 = [ 126, teneb_walk4 ]
{
	ai_walk(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_walk4 = [ 127, teneb_walk5 ]
{
	ai_walk(7);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_walk5 = [ 128, teneb_walk6 ]
{
	ai_walk(4);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
	demon_footsteps(0.7);
};

void() teneb_walk6 = [ 129, teneb_walk7 ]
{
	ai_walk(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_walk7 = [ 130, teneb_walk8 ]
{
	ai_walk(8);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_walk8 = [ 131, teneb_walk9 ]
{
	ai_walk(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_walk9 = [ 132, teneb_walk10 ]
{
	ai_walk(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_walk10 = [ 133, teneb_walk11 ]
{
	ai_walk(7);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_walk11 = [ 134, teneb_walk12 ]
{
	ai_walk(4);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
	demon_footsteps(0.7);
};

void() teneb_walk12 = [ 135, teneb_walk1 ]
{
	ai_walk(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_walk1 = [ 13, demon1_walk2 ]
{
	self.tail_visible = 0;
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "demon/idle1.wav", 1, ATTN_IDLE, SNDSPD);
	}
	ai_walk(8);
	demon_footsteps(0.7);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_walk2 = [ 14, demon1_walk3 ]
{
	ai_walk(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_walk3 = [ 15, demon1_walk4 ]
{
	ai_walk(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_walk4 = [ 16, demon1_walk5 ]
{
	ai_walk(7);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_walk5 = [ 17, demon1_walk6 ]
{
	ai_walk(4);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
	demon_footsteps(0.7);
};

void() demon1_walk6 = [ 18, demon1_walk7 ]
{
	ai_walk(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_walk7 = [ 19, demon1_walk8 ]
{
	ai_walk(10);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_walk8 = [ 20, demon1_walk1 ]
{
	ai_walk(10);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_run1 = [ 21, demon1_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	self.tail_visible = 0;
	if ((random() < 0.2))
	{
		if ((self.monstermodel == 2))
		{
			sound7(self, CHAN_VOICE, "teneb/idle.wav", 1, ATTN_IDLE, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "demon/idle1.wav", 1, ATTN_IDLE, SNDSPD);
		}
	}
	ai_run(20);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_run2 = [ 22, demon1_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(15);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
	demon_footsteps(0.85);
};

void() demon1_run3 = [ 23, demon1_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(36);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
	if ((((skill == 3) && self.demon_on_fire) && (random() < 0.35)))
	{
		sound7(self, CHAN_VOICE, "teneb/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
};

void() demon1_run4 = [ 24, demon1_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(20);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_run5 = [ 25, demon1_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(15);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
	demon_footsteps(0.85);
	if ((random() < (skill * 0.01)))
	{
		if ((vlen((self.enemy.origin - self.origin)) > 300))
		{
			PM_DemBlink(self, TRUE);
		}
	}
};

void() demon1_run6 = [ 26, demon1_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(36);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53409i*/"demon_walk"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_jump1 = [ 136, teneb_jump2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.tail_visible = 0;
	sound7(self, CHAN_VOICE, "teneb/jump.wav", 1, ATTN_NORM, SNDSPD);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_jump2 = [ 137, teneb_jump3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_jump3 = [ 138, teneb_jump31 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.tail_visible = 1;
	self.touch = Demon_JumpTouch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 600) + '0 0 250');
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
};

void() teneb_jump31 = [ 138, teneb_jump32 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() teneb_jump32 = [ 138, teneb_jump33 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() teneb_jump33 = [ 138, teneb_jump4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() teneb_jump4 = [ 139, teneb_jump5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() teneb_jump5 = [ 140, teneb_jump6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() teneb_jump6 = [ 141, teneb_jump1 ]
{
	self.nextthink = (time + 0.7);
};

void() teneb_jump7 = [ 142, teneb_jump8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	self.tail_visible = 0;
};

void() teneb_jump8 = [ 142, demon1_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() demon1_jump1 = [ 27, demon1_jump2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.tail_visible = 0;
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_jump2 = [ 28, demon1_jump3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_jump3 = [ 29, demon1_jump4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_jump4 = [ 30, demon1_jump5 ]
{
	self.nextthink = ((time + 0.1) - 0.03);
	ai_face();
	self.tail_visible = 1;
	self.attack_timer = 0;
	self.touch = Demon_JumpTouch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 2);
	if (((self.origin_z - self.enemy.origin_z) > 48))
	{
		self.velocity = ((v_forward * (590 + (random() * 60))) + '0 0 230');
	}
	else
	{
		if (((self.enemy.origin_z - self.origin_z) > (32 + (random() * 2))))
		{
			self.velocity = ((v_forward * (390 + (random() * 60))) + '0 0 330');
		}
		else
		{
			if ((skill > 1))
			{
				self.velocity = ((v_forward * (600 + (random() * 100))) + '0 0 240');
			}
			else
			{
				self.velocity = ((v_forward * (600 + (random() * 30))) + '0 0 240');
			}
		}
	}
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
	autocvar_DemonLoc = self.origin_x;
	autocvar_DemonLoc2 = self.origin_y;
};

void() demon1_jump5 = [ 31, demon1_jump6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	if (((autocvar_DemonLoc == self.origin_x) && (autocvar_DemonLoc2 == self.origin_y)))
	{
		autocvar_DemonLoc = 0;
		autocvar_DemonLoc2 = 0;
		PM_DemBlink(self, TRUE);
	}
	else
	{
		autocvar_DemonLoc = 0;
		autocvar_DemonLoc2 = 0;
	}
};

void() demon1_jump6 = [ 32, demon1_jump7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() demon1_jump7 = [ 33, demon1_jump8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() demon1_jump8 = [ 34, demon1_jump9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() demon1_jump9 = [ 35, demon1_jump10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() demon1_jump10 = [ 36, demon1_jump1 ]
{
	self.nextthink = (time + 0.7);
	if ((((skill == 3) && self.demon_on_fire) && (random() < 0.4)))
	{
		sound7(self, CHAN_VOICE, "teneb/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
};

void() demon1_jump11 = [ 37, demon1_jump12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	self.tail_visible = 0;
};

void() demon1_jump12 = [ 38, demon1_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() teneb_atta1 = [ 143, teneb_atta2 ]
{
	ai_charge(4);
	self.tail_visible = 0;
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_atta2 = [ 144, teneb_atta3 ]
{
	ai_charge(0);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_atta3 = [ 145, teneb_atta4 ]
{
	ai_charge(0);
	Demon_Melee(200);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_atta4 = [ 146, teneb_atta5 ]
{
	ai_charge(1);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_atta5 = [ 147, teneb_atta6 ]
{
	ai_charge(2);
	Demon_Melee(-200);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_atta6 = [ 148, teneb_atta7 ]
{
	ai_charge(1);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_atta7 = [ 149, teneb_atta8 ]
{
	ai_charge(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_atta8 = [ 150, teneb_atta9 ]
{
	ai_charge(8);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() teneb_atta9 = [ 151, demon1_run1 ]
{
	ai_charge(4);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta1 = [ 54, demon1_atta2 ]
{
	ai_charge(4);
	self.tail_visible = 0;
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta2 = [ 55, demon1_atta3 ]
{
	ai_charge(0);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta3 = [ 56, demon1_atta4 ]
{
	ai_charge(0);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta4 = [ 57, demon1_atta5 ]
{
	ai_charge(1);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta5 = [ 58, demon1_atta6 ]
{
	ai_charge(2);
	Demon_Melee(200);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta6 = [ 59, demon1_atta7 ]
{
	ai_charge(1);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta7 = [ 60, demon1_atta8 ]
{
	ai_charge(6);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta8 = [ 61, demon1_atta9 ]
{
	ai_charge(8);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta9 = [ 62, demon1_atta10 ]
{
	ai_charge(4);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta10 = [ 63, demon1_atta11 ]
{
	ai_charge(2);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta11 = [ 64, demon1_atta12 ]
{
	Demon_Melee(-200);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
	demon_footsteps(0.85);
};

void() demon1_atta12 = [ 65, demon1_atta13 ]
{
	ai_charge(5);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta13 = [ 66, demon1_atta14 ]
{
	ai_charge(8);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta14 = [ 67, demon1_atta15 ]
{
	ai_charge(4);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_atta15 = [ 68, demon1_run1 ]
{
	ai_charge(4);
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_pain1 = [ 39, demon1_pain2 ]
{
	self.tail_visible = 0;
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_pain2 = [ 40, demon1_pain3 ]
{
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_pain3 = [ 41, demon1_pain4 ]
{
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_pain4 = [ 42, demon1_pain5 ]
{
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_pain5 = [ 43, demon1_pain6 ]
{
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_pain6 = [ 44, demon1_run1 ]
{
	if ((self.demon_on_fire == 1))
	{
		pointparticles(particleeffectnum(/*53381i*/"demon_stand"), self.origin, VEC_ORIGIN, 1);
	}
};

void(entity attacker, float damage) demon1_pain =
{
	if ((self.touch == Demon_JumpTouch))
	{
		return;
	}
	if ((random() <= 0.01))
	{
		PM_DemMultiBlink();
	}
	if ((self.pain_finished > time))
	{
		return;
	}
	if ((((self.health <= 200) && (((self.enemy.weapon != IT_AXE) || (self.enemy.weapon != IT_ROCKET_LAUNCHER)) || (self.enemy.weapon != IT_GRENADE_LAUNCHER))) && (self.enemy.meleeing == 0)))
	{
		self.skin = 1;
	}
	self.pain_finished = (time + 1);
	if ((self.monstermodel == 2))
	{
		sound7(self, CHAN_VOICE, "teneb/pain1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_VOICE, "demon/dpain1.wav", 1, ATTN_NORM, SNDSPD);
	}
	if ((self.monstermodel == 2))
	{
		if (((random() * 90) > damage))
		{
			return;
		}
	}
	else
	{
		if (((random() * 200) > damage))
		{
			return;
		}
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_demon * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	demon1_pain1();
};

void() demon_dieburn1 = [ 45, demon_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
};

void() demon_dieburn2 = [ 46, demon_dieburn3 ]
{
	self.burnz_origin = 11;
};

void() demon_dieburn3 = [ 47, demon_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
};

void() demon_dieburn4 = [ 48, demon_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() demon_dieburn5 = [ 49, demon_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() demon_dieburn6 = [ 50, demon_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() demon_dieburn7 = [ 51, demon_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() demon_dieburn8 = [ 52, demon_dieburn9 ]
{
	self.burnz_origin = -6;
};

void() demon_dieburn9 = [ 53, demon_dieburn9 ]
{
	self.burnz_origin = -8;
};

void() demon1_rldie1 = [ 45, demon1_expdie2 ]
{
	sound7(self, CHAN_VOICE, "player/udeath.wav", 1, ATTN_NORM, SNDSPD);
};

void() demon1_rldie2 = [ 45, demon1_expdie2 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_expdie1 = [ 69, demon1_expdie2 ]
{
};

void() demon1_expdie2 = [ 70, demon1_expdie3 ]
{
};

void() demon1_expdie3 = [ 71, demon1_expdie4 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_expdie4 = [ 72, demon1_expdie5 ]
{
	ai_back(5);
};

void() demon1_expdie5 = [ 73, demon1_expdie6 ]
{
	ai_back(5);
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_NORM, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_NORM, SNDSPD);
};

void() demon1_expdie6 = [ 74, demon1_expdie7 ]
{
	self.solid = 0;
};

void() demon1_expdie7 = [ 75, demon1_expdie8 ]
{
	sound7(self, CHAN_AUTO, "demon/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
	ai_back(5);
	sound7(self, CHAN_AUTO, "misc/megagib.wav", 1, ATTN_NORM, SNDSPD);
};

void() demon1_expdie8 = [ 76, demon1_expdie9 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_expdie9 = [ 77, demon1_expdie10 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_expdie10 = [ 78, demon1_expdie11 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	}
};

void() demon1_expdie11 = [ 79, demon1_expdie12 ]
{
};

void() demon1_expdie12 = [ 80, demon1_expdie13 ]
{
};

void() demon1_expdie13 = [ 81, demon1_expdie13 ]
{
	if ((autocvar_demoncorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_demoncorpsehealth, "progs/gib_dmclaw1.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_demoncorpsehealth, "progs/gib_dmclaw1.mdl");
	}
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
};

void() demon1_die1 = [ 45, demon1_die2 ]
{
	ai_back(3);
	if ((self.monstermodel == 2))
	{
		sound7(self, CHAN_VOICE, "teneb/death.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_VOICE, "demon/ddeath.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() demon1_die2 = [ 46, demon1_die3 ]
{
	ai_back(5);
};

void() demon1_die3 = [ 47, demon1_die4 ]
{
	ai_back(5);
};

void() demon1_die4 = [ 48, demon1_die5 ]
{
	ai_back(5);
};

void() demon1_die5 = [ 49, demon1_die6 ]
{
	ai_back(4);
};

void() demon1_die6 = [ 50, demon1_die7 ]
{
	self.solid = 0;
};

void() demon1_die7 = [ 51, demon1_die8 ]
{
	sound7(self, CHAN_AUTO, "demon/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() demon1_die8 = [ 52, demon1_die9 ]
{
};

void() demon1_die9 = [ 53, demon1_die9 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	zet = 27;
	if ((autocvar_demoncorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_demoncorpsehealth, "progs/h_demon.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_demoncorpsehealth, "progs/h_demon1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_demoncorpsehealth, "progs/h_teneb.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_demonrandomness = autocvar_demonrandomness * 0.01;
		if ((autocvar_demon == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_demonrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_demon == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_demonrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/demon.mdl", 53, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/demon1.mdl", 53, zet);
						}
						else
						{
							if ((self.monstermodel == 2))
							{
								soul("progs/teneb.mdl", 53, zet);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_demon == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_demonrandomness))
					{
						vengeance_demon("progs/demon.mdl", 53);
					}
				}
				else
				{
					if ((autocvar_demon == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_demonrandomness))
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
									if ((self.monstermodel == 0))
									{
										soul("progs/demon.mdl", 53, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/demon1.mdl", 53, zet);
										}
										else
										{
											if ((self.monstermodel == 2))
											{
												soul("progs/teneb.mdl", 53, zet);
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
			if ((zufall > 0.825))
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
						if ((self.monstermodel == 0))
						{
							soul("progs/demon.mdl", 53, zet);
						}
						else
						{
							if ((self.monstermodel == 1))
							{
								soul("progs/demon1.mdl", 53, zet);
							}
							else
							{
								if ((self.monstermodel == 2))
								{
									soul("progs/teneb.mdl", 53, zet);
								}
							}
						}
					}
				}
				else
				{
					vengeance_demon("progs/demon.mdl", 53);
				}
			}
		}
	}
};

void(float maxgibs, float gibscounter) producegibs_demon =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/gib1.mdl", self.health);
		ThrowGib("progs/gib_dmleg1.mdl", self.health);
		ThrowGib("progs/gib_dmleg2.mdl", self.health);
		ThrowGib("progs/gib_dmtail.mdl", self.health);
		ThrowGib("progs/gib_dmclaw1.mdl", self.health);
		ThrowGib("progs/gib_dmclaw2.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_demon(maxgibs, gibscounter);
};

void() demon_lightning_death = [ 41, demon_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() demon_lightning_death1 = [ 41, demon_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(1, "progs/h_demon.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(1, "progs/h_demon1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(1, "progs/h_teneb.mdl");
	}
};

void() demon_die =
{
	local float maxgibs;
	local float gibscounter;
	local float zufall;
	local float randomness;

	self.tail_visible = 0;
	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			demon_lightning_death();
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
	if ((self.health < -65))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_demon * 0.01)))
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
			ThrowHead("progs/h_demon.mdl", self.health);
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				ThrowHead("progs/h_demon1.mdl", self.health);
			}
			else
			{
				if ((self.monstermodel == 2))
				{
					ThrowHead("progs/h_teneb.mdl", self.health);
				}
			}
		}
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		gibdeath_effects();
		producegibs_demon(maxgibs, gibscounter);
		return;
	}
	autocvar_demonrandomness = autocvar_demonrandomness * 0.01;
	if ((autocvar_demon == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_demonrandomness))
		{
			self.delete_painskin = 1;
			demon_dieburn1();
			return;
		}
	}
	if ((autocvar_demon == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_demonrandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				demon_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_demon * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	demon1_die1();
	if ((self.enemy.meleeing == 0))
	{
		if (((self.enemy.weapon == IT_SUPER_SHOTGUN) && (random() < 0.05)))
		{
			self.grimrock_helper = 1;
		}
		if (((self.enemy.weapon == IT_SUPER_SHOTGUN) && (random() < 0.9)))
		{
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			if ((autocvar_bloodextension == 1))
			{
				pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
			}
			ThrowGib("progs/chop.mdl", self.health);
			ThrowGib("progs/chop.mdl", self.health);
			ThrowGib("progs/gib2.mdl", self.health);
			ThrowGib("progs/gib_dmclaw1.mdl", self.health);
			ThrowGib("progs/gib_dmclaw2.mdl", self.health);
			self.delete_painskin = 1;
			if ((self.model == "progs/demon.mdl"))
			{
				self.model = "progs/demonblast.mdl";
				setmodel(self, "progs/demonblast.mdl");
				self.skin = 0;
			}
			else
			{
				self.model = "progs/demonblast.mdl";
				setmodel(self, "progs/demonblast.mdl");
				self.skin = 1;
			}
			demon1_expdie1();
		}
		if ((((self.enemy.weapon == IT_ROCKET_LAUNCHER) || (self.enemy.weapon == IT_GRENADE_LAUNCHER)) && (random() < 0.9)))
		{
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			if ((random() < 0.5))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/gib2.mdl", self.health);
				ThrowGib("progs/gib_dmclaw1.mdl", self.health);
				ThrowGib("progs/gib_dmclaw2.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.model == "progs/demon.mdl"))
				{
					self.model = "progs/demonblast.mdl";
					setmodel(self, "progs/demonblast.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/demonblast.mdl";
					setmodel(self, "progs/demonblast.mdl");
					self.skin = 1;
				}
				demon1_expdie1();
			}
			else
			{
				ThrowGib("progs/gib_dmtail.mdl", self.health);
				ThrowGib("progs/gib_dmclaw1.mdl", self.health);
				ThrowGib("progs/gib_dmclaw2.mdl", self.health);
				ThrowGib("progs/gib_dmleg1.mdl", self.health);
				ThrowGib("progs/gib_dmleg2.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.model == "progs/demon.mdl"))
				{
					ThrowGib("progs/h_demon.mdl", self.health);
					self.model = "progs/demonrl.mdl";
					setmodel(self, "progs/demonrl.mdl");
					self.skin = 0;
				}
				else
				{
					ThrowGib("progs/h_demon1.mdl", self.health);
					self.model = "progs/demonrl.mdl";
					setmodel(self, "progs/demonrl.mdl");
					self.skin = 0;
				}
				demon1_rldie1();
			}
		}
		setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	}
};

void() Demon_MeleeAttack =
{
	if ((self.monstermodel == 2))
	{
		teneb_atta1();
	}
	else
	{
		demon1_atta1();
	}
};

void() monster_demon1 =
{
	local float zufall;
	local float teneb;
	local float zuffa;
	local float zufal;
	local float replacer;
	local vector check;
	local float replacerrr;
	local float replacez;
	local float replac;
	local entity motion_blur_entity;
	local entity motion_blur_entity1;
	local entity motion_blur_entity2;
	local entity motion_blur_entity3;
	local entity motion_blur_entity4;
	local entity motion_blur_entity5;
	local entity pain_skin_entity;
	local float replacce;
	local float replace;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/demon.mdl");
	precache_model("progs/h_demon.mdl");
	precachegibs_dem();
	precache_sound("demon/ddeath.wav");
	precache_sound("demon/dhit2.wav");
	precache_sound("demon/djump.wav");
	precache_sound("demon/dpain1.wav");
	precache_sound("demon/idle1.wav");
	precache_sound("demon/sight2.wav");
	precache_sound("demon/fall_backwards.wav");
	precache_sound("walk/demon1.wav");
	precache_sound("walk/demon2.wav");
	precache_sound("walk/demon3.wav");
	precache_sound("walk/demon4.wav");
	precache_sound("walk/demon5.wav");
	precache_sound("teneb/sight.wav");
	precache_sound("teneb/jump.wav");
	precache_sound("teneb/idle.wav");
	precache_sound("teneb/pain1.wav");
	precache_sound("teneb/death.wav");
	precache_sound("teneb/step1.wav");
	precache_sound("teneb/step2.wav");
	precache_sound("teneb/step3.wav");
	precache_sound("shalrath/growl.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.netname = "monster_demon1";
	if ((autocvar_demonmultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/demon.mdl");
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
		if ((autocvar_demonmultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/demon1.mdl");
			precache_model("progs/h_demon1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/demon.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/demon1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_demonmultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/demon1.mdl");
				precache_model("progs/h_demon1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/demon.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/demon.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/demon1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_demonmultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/demon1.mdl");
					precache_model("progs/h_demon1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/demon.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/demon.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/demon1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/demon1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/demon.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if (autocvar_teneb_replace_demon)
	{
		teneb = autocvar_teneb_replace_demon * 0.01;
		if ((random() < teneb))
		{
			precache_model("progs/teneb.mdl");
			precache_model("progs/h_teneb.mdl");
			setmodel(self, "progs/teneb.mdl");
			self.skin = 0;
			self.monsterskin = 0;
			self.monstermodel = 2;
		}
	}
	if ((autocvar_demon_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.14;
			self.sizediff = '0 0 3';
			setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.07;
				self.sizediff = '0 0 1';
				setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
			}
			else
			{
				self.scale = 1;
				setsize(self, DEM_MIN, DEM_MAX);
			}
		}
	}
	else
	{
		if ((autocvar_demon_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.21;
				self.sizediff = '0 0 5';
				setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.14;
					self.sizediff = '0 0 3';
					setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.75))
					{
						self.scale = 1.07;
						self.sizediff = '0 0 1';
						setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, DEM_MIN, DEM_MAX);
					}
				}
			}
		}
		else
		{
			if ((autocvar_demon_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.28;
					self.sizediff = '0 0 7';
					setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.21;
						self.sizediff = '0 0 5';
						setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.14;
							self.sizediff = '0 0 3';
							setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.07;
								self.sizediff = '0 0 1';
								setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
							}
							else
							{
								self.scale = 1;
								setsize(self, DEM_MIN, DEM_MAX);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_demon_size == 4))
				{
					zuffa = random();
					if ((zuffa <= 0.17))
					{
						self.scale = 1.35;
						self.sizediff = '0 0 9';
						setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.34))
						{
							self.scale = 1.28;
							self.sizediff = '0 0 7';
							setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.5))
							{
								self.scale = 1.21;
								self.sizediff = '0 0 5';
								setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
							}
							else
							{
								if ((zuffa <= 0.67))
								{
									self.scale = 1.14;
									self.sizediff = '0 0 3';
									setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
								}
								else
								{
									if ((zuffa <= 0.84))
									{
										self.scale = 1.07;
										self.sizediff = '0 0 1';
										setsize(self, (DEM_MIN - self.sizediff), (DEM_MAX - self.sizediff));
									}
									else
									{
										self.scale = 1;
										setsize(self, DEM_MIN, DEM_MAX);
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_demon_size > 4))
					{
						if ((autocvar_demon_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_demon_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_demon_size * 0.25);
						self.sizediff = self.sizefactor;
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, DEM_MIN, DEM_MAX);
					}
				}
			}
		}
	}
	if ((autocvar_demon_size_influenced_health == 1))
	{
		self.health = (autocvar_demon_health * self.scale);
	}
	else
	{
		self.health = autocvar_demon_health;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_demon_random_skin_colors))
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
	if ((self.monstermodel == 2))
	{
		self.th_stand = teneb_stand1;
		self.th_walk = teneb_walk1;
		self.th_missile = teneb_jump1;
	}
	else
	{
		self.th_stand = demon1_stand1;
		self.th_walk = demon1_walk1;
		self.th_missile = demon1_jump1;
	}
	self.th_run = demon1_run1;
	self.th_die = demon_die;
	self.th_melee = Demon_MeleeAttack;
	self.th_pain = demon1_pain;
	autocvar_helldemon = autocvar_helldemon * 0.01;
	zufal = random();
	if (((zufal <= autocvar_helldemon) && (cvar("skill") != 3)))
	{
		self.demon_on_fire = 1;
	}
	else
	{
		if (((cvar("skill") == 3) && (random() <= (0.05 + (cvar("quadreplacer") * 0.01)))))
		{
			self.demon_on_fire = 1;
			self.alpha = 0.135;
			self.glow_color = 75;
			self.glow_size = 40;
		}
	}
	if (autocvar_spider_replace_demon)
	{
		replacer = autocvar_spider_replace_demon * 0.01;
		if ((random() <= replacer))
		{
			check = (self.origin - '0 0 20') + '0 0 1';
			if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
			{
				self.skin = 4;
				self.health = autocvar_demon_health;
				self.scale = 1;
				setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_spider_start();
				return;
			}
		}
	}
	if (autocvar_torment_replace_demon)
	{
		replacerrr = autocvar_torment_replace_demon * 0.01;
		if ((random() <= replacerrr))
		{
			self.health = autocvar_demon_health;
			self.scale = 1;
			setsize(self, VEC_HULL_MIN, '16 16 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_torment_start();
			return;
		}
	}
	if (autocvar_reiver_replace_demon)
	{
		replacez = autocvar_reiver_replace_demon * 0.01;
		if ((random() <= replacez))
		{
			self.health = autocvar_demon_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_reiver_liftorigin_start();
			return;
		}
	}
	if (autocvar_afrit_replace_demon)
	{
		replac = autocvar_afrit_replace_demon * 0.01;
		if ((random() <= replac))
		{
			self.health = autocvar_demon_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_afrit_liftorigin_start();
			return;
		}
	}
	if (autocvar_demon_jump_motion_blur)
	{
		motion_blur_entity = spawn();
		motion_blur_entity.solid = 0;
		motion_blur_entity.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity.owner = self;
		setmodel(motion_blur_entity, self.model);
		setsize(motion_blur_entity, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity, VEC_ORIGIN);
		motion_blur_entity.skin = self.skin;
		motion_blur_entity.colormod_x = self.colormod_x;
		motion_blur_entity.colormod_y = self.colormod_y;
		motion_blur_entity.colormod_z = self.colormod_z;
		motion_blur_entity.frame = self.frame;
		motion_blur_entity.think = motion_blur_entity_think;
		motion_blur_entity.nextthink = (time + 0.05);
		setattachment(motion_blur_entity, self, /*37325i*/"test");
		motion_blur_entity1 = spawn();
		motion_blur_entity1.solid = 0;
		motion_blur_entity1.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity1.owner = self;
		setmodel(motion_blur_entity1, self.model);
		setsize(motion_blur_entity1, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity1, VEC_ORIGIN);
		motion_blur_entity1.skin = self.skin;
		motion_blur_entity1.colormod_x = self.colormod_x;
		motion_blur_entity1.colormod_y = self.colormod_y;
		motion_blur_entity1.colormod_z = self.colormod_z;
		motion_blur_entity1.frame = self.frame;
		motion_blur_entity1.think = motion_blur_entity1_think;
		motion_blur_entity1.nextthink = (time + 0.05);
		setattachment(motion_blur_entity1, self, /*37325i*/"test");
		motion_blur_entity2 = spawn();
		motion_blur_entity2.solid = 0;
		motion_blur_entity2.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity2.owner = self;
		setmodel(motion_blur_entity2, self.model);
		setsize(motion_blur_entity2, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity2, VEC_ORIGIN);
		motion_blur_entity2.skin = self.skin;
		motion_blur_entity2.colormod_x = self.colormod_x;
		motion_blur_entity2.colormod_y = self.colormod_y;
		motion_blur_entity2.colormod_z = self.colormod_z;
		motion_blur_entity2.frame = self.frame;
		motion_blur_entity2.think = motion_blur_entity2_think;
		motion_blur_entity2.nextthink = (time + 0.05);
		setattachment(motion_blur_entity2, self, /*37325i*/"test");
		motion_blur_entity3 = spawn();
		motion_blur_entity3.solid = 0;
		motion_blur_entity3.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity3.owner = self;
		setmodel(motion_blur_entity3, self.model);
		setsize(motion_blur_entity3, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity3, VEC_ORIGIN);
		motion_blur_entity3.skin = self.skin;
		motion_blur_entity3.colormod_x = self.colormod_x;
		motion_blur_entity3.colormod_y = self.colormod_y;
		motion_blur_entity3.colormod_z = self.colormod_z;
		motion_blur_entity3.frame = self.frame;
		motion_blur_entity3.think = motion_blur_entity3_think;
		motion_blur_entity3.nextthink = (time + 0.05);
		setattachment(motion_blur_entity3, self, /*37325i*/"test");
		motion_blur_entity4 = spawn();
		motion_blur_entity4.solid = 0;
		motion_blur_entity4.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity4.owner = self;
		setmodel(motion_blur_entity4, self.model);
		setsize(motion_blur_entity4, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity4, VEC_ORIGIN);
		motion_blur_entity4.skin = self.skin;
		motion_blur_entity4.colormod_x = self.colormod_x;
		motion_blur_entity4.colormod_y = self.colormod_y;
		motion_blur_entity4.colormod_z = self.colormod_z;
		motion_blur_entity4.frame = self.frame;
		motion_blur_entity4.think = motion_blur_entity4_think;
		motion_blur_entity4.nextthink = (time + 0.05);
		setattachment(motion_blur_entity4, self, /*37325i*/"test");
		motion_blur_entity5 = spawn();
		motion_blur_entity5.solid = 0;
		motion_blur_entity5.movetype = MOVETYPE_NOCLIP;
		motion_blur_entity5.owner = self;
		setmodel(motion_blur_entity5, self.model);
		setsize(motion_blur_entity5, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(motion_blur_entity5, VEC_ORIGIN);
		motion_blur_entity5.skin = self.skin;
		motion_blur_entity5.colormod_x = self.colormod_x;
		motion_blur_entity5.colormod_y = self.colormod_y;
		motion_blur_entity5.colormod_z = self.colormod_z;
		motion_blur_entity5.frame = self.frame;
		motion_blur_entity5.think = motion_blur_entity5_think;
		motion_blur_entity5.nextthink = (time + 0.05);
		setattachment(motion_blur_entity5, self, /*37325i*/"test");
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
	if (autocvar_reiver_supports_demon)
	{
		replacce = autocvar_reiver_supports_demon * 0.01;
		if ((cvar("quadreplacer") > 0))
		{
			replacce = replacce + 0.01;
		}
		if ((random() <= replacce))
		{
			add_reiver_support_walk();
		}
	}
	if (autocvar_afrit_supports_demon)
	{
		replace = autocvar_afrit_supports_demon * 0.01;
		if ((random() <= replace))
		{
			add_afrit_support_walk();
		}
	}
	MonsterPhysics(self, autocvar_demonmass);
};

float() CheckDemonMelee =
{
	if ((enemy_range == RANGE_MELEE))
	{
		self.attack_state = AS_MELEE;
		return (TRUE);
	}
	return (0);
};

float() CheckDemonJump =
{
	local vector dist;
	local float d;

	if (((self.enemy.origin_z - self.origin_z) > 54))
	{
		return (0);
	}
	else
	{
		if ((((self.enemy.origin_z - self.origin_z) > 24) && (random() < 0.7)))
		{
			return (0);
		}
	}
	if (((self.origin_z + self.mins_z) > ((self.enemy.origin_z + self.enemy.mins_z) + (2.5 * self.enemy.size_z))))
	{
		return (0);
	}
	if (((self.origin_z + self.maxs_z) < ((self.enemy.origin_z + self.enemy.mins_z) + (0.25 * self.enemy.size_z))))
	{
		return (0);
	}
	dist = self.enemy.origin - self.origin;
	d = vlen(dist);
	if ((d < 100))
	{
		return (0);
	}
	if ((d > 200))
	{
		if (autocvar_skill_adjusted_monster_rangedattack_frequence)
		{
			if ((skill == 0))
			{
				if ((random() < 0.9))
				{
					return (0);
				}
			}
			else
			{
				if ((skill == 1))
				{
					if ((random() < 0.85))
					{
						return (0);
					}
				}
				else
				{
					if ((skill == 2))
					{
						if ((random() < 0.8))
						{
							return (0);
						}
					}
					else
					{
						if ((random() < 0.75))
						{
							return (0);
						}
					}
				}
			}
		}
		else
		{
			if ((random() < 0.9))
			{
				return (0);
			}
		}
	}
	return (TRUE);
};

float() DemonCheckAttack =
{
	if (CheckDemonMelee())
	{
		self.attack_state = AS_MELEE;
		return (TRUE);
	}
	if (CheckDemonJump())
	{
		self.attack_state = AS_MISSILE;
		if ((self.monstermodel != 2))
		{
			sound7(self, CHAN_VOICE, "demon/djump.wav", 1, ATTN_NORM, SNDSPD);
		}
		return (TRUE);
	}
	return (0);
};

void(float side) Demon_Melee =
{
	local float ldmg;
	local vector delta;

	ai_face();
	walkmove(self.ideal_yaw, 12);
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 100))
	{
		return;
	}
	if (!CanDamage(self.enemy, self))
	{
		return;
	}
	sound7(self, CHAN_WEAPON, "demon/dhit2.wav", 1, ATTN_NORM, SNDSPD);
	if ((autocvar_demon_size_influenced_attack == 1))
	{
		ldmg = (autocvar_demon_claws * self.scale) + (5 * random());
	}
	else
	{
		ldmg = autocvar_demon_claws + (5 * random());
	}
	T_Damage(self.enemy, self, self, ldmg);
	makevectors(self.angles);
	SpawnMeatSpray((self.origin + (v_forward * 16)), (side * v_right));
};

void() Demon_JumpTouch =
{
	local float ldmg;

	if (((self.health <= 0) || (self.attack_timer > 0)))
	{
		return;
	}
	if (other.takedamage)
	{
		if ((vlen(self.velocity) > 400))
		{
			if ((autocvar_demon_size_influenced_attack == 1))
			{
				ldmg = (autocvar_demon_jump * self.scale) + (10 * random());
			}
			else
			{
				ldmg = autocvar_demon_jump + (10 * random());
			}
			T_Damage(other, self, self, ldmg);
			if ((other.classname == "player"))
			{
				self.attack_timer = 1;
			}
		}
	}
	if (!checkbottom(self))
	{
		self.tail_visible = 0;
		if ((self.flags & FL_ONGROUND))
		{
			self.touch = SUB_Null;
			if ((self.monstermodel == 2))
			{
				self.think = teneb_jump1;
			}
			else
			{
				self.think = demon1_jump1;
			}
			self.nextthink = (time + 0.1);
		}
		return;
	}
	self.touch = SUB_Null;
	if ((self.monstermodel == 2))
	{
		self.think = teneb_jump7;
	}
	else
	{
		self.think = demon1_jump11;
	}
	self.nextthink = (time + 0.1);
};

void() vengeance_demon_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_demon_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_demon_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon_run1 = [ 21, vengeance_demon_run2 ]
{
	ai_face();
	movetogoal(15);
	self.touch = vengeance_demon_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon_run2 = [ 22, vengeance_demon_run3 ]
{
	ai_face();
	movetogoal(15);
	self.touch = vengeance_demon_touch;
	self.alpha = 0.35;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon_run3 = [ 23, vengeance_demon_run4 ]
{
	ai_face();
	movetogoal(18);
	self.touch = vengeance_demon_touch;
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon_run4 = [ 24, vengeance_demon_run5 ]
{
	ai_face();
	movetogoal(15);
	self.touch = vengeance_demon_touch;
	self.alpha = 0.25;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon_run5 = [ 25, vengeance_demon_jump1 ]
{
	ai_face();
	movetogoal(15);
	self.touch = vengeance_demon_touch;
	self.alpha = 0.225;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() jumpmelee =
{
	ai_melee();
	self.alpha = (self.alpha - 0.0055);
	if ((self.alpha < 0.1))
	{
		self.think = vengeance_demon_end1;
		self.nextthink = (time + 0.1);
		return;
	}
	self.think = jumpmelee;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon_jump1 = [ 27, vengeance_demon_jump2 ]
{
	ai_face();
	movetogoal(26);
	self.touch = vengeance_demon_touch;
	self.alpha = 0.21;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_demon_jump2 = [ 28, vengeance_demon_jump3 ]
{
	if ((self.monstermodel == 2))
	{
		sound7(self, CHAN_VOICE, "teneb/jump.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_VOICE, "demon/djump.wav", 1, ATTN_NORM, SNDSPD);
	}
	ai_face();
	self.touch = vengeance_demon_touch;
	movetogoal(16);
	self.alpha = 0.19;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_demon_jump3 = [ 29, vengeance_demon_jump4 ]
{
	ai_face();
	self.touch = vengeance_demon_touch;
	self.alpha = 0.17;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_demon_jump4 = [ 30, vengeance_demon_jump5 ]
{
	ai_face();
	self.touch = vengeance_demon_touch;
	self.alpha = 0.16;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.07);
};

void() vengeance_demon_jump5 = [ 31, vengeance_demon_end1 ]
{
	local vector vec;

	ai_face();
	self.touch = vengeance_demon_touch;
	self.origin_z = (self.origin_z + 1);
	makevectors(self.enemy.angles);
	vec = normalize((self.enemy.origin - self.origin));
	self.velocity = (vec * 740);
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
	self.alpha = 0.15;
	self.glow_color = 75;
	self.glow_size = 600;
	self.movetype = MOVETYPE_NOCLIP;
	self.solid = SOLID_SLIDEBOX;
	self.nextthink = (time + 0.1);
	self.think = jumpmelee;
};

void() vengeance_demon1 = [ 52, vengeance_demon2 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon2 = [ 51, vengeance_demon3 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon3 = [ 50, vengeance_demon4 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon4 = [ 49, vengeance_demon5 ]
{
	if ((self.monstermodel == 2))
	{
		sound7(self, CHAN_VOICE, "teneb/sight.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_WEAPON, "demon/sight2.wav", 1, ATTN_NORM, SNDSPD);
	}
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon5 = [ 48, vengeance_demon6 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon6 = [ 47, vengeance_demon7 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon7 = [ 46, vengeance_demon8 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon8 = [ 45, vengeance_demon_stand1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon_stand1 = [ 54, vengeance_demon_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_demon_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	self.think = vengeance_demon1;
};

void() vengeance_demon_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_demon_bright05;
};

void() vengeance_demon_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_demon_bright04;
};

void() vengeance_demon_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_demon_bright03;
};

void() vengeance_demon_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_demon_bright02;
};

void() vengeance_demon_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_demon_bright01;
};

void(string modelname, float modelframe) vengeance_demon =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_STEP;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/demon.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/demon1.mdl");
		}
		else
		{
			if ((self.monstermodel == 2))
			{
				setmodel(self, "progs/teneb.mdl");
			}
		}
	}
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	self.frame = modelframe;
	self.solid = 0;
	MonsterPhysics(self, autocvar_demonmass);
	vengeance_demon_bright00();
};
