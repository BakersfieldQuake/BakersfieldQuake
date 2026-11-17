//Decompiled code. Please respect the original copyright.

void() slimeboss_face =
{
	if (((self.enemy.health <= 0) || (random() < 0.02)))
	{
		self.enemy = find(self.enemy, classname, "player");
		if (!self.enemy)
		{
			self.enemy = find(self.enemy, classname, "player");
		}
	}
	ai_face();
};

void() slimeboss_rise1 = [ 0, slimeboss_rise2 ]
{
	sound(self, CHAN_WEAPON, "boss1/out1.wav", 1, ATTN_NORM);
};

void() slimeboss_rise2 = [ 1, slimeboss_rise3 ]
{
	sound(self, CHAN_VOICE, "boss1/sight1.wav", 1, ATTN_NORM);
};

void() slimeboss_rise3 = [ 2, slimeboss_rise4 ]
{
};

void() slimeboss_rise4 = [ 3, slimeboss_rise5 ]
{
	self.weapontimer = 0;
};

void() slimeboss_rise5 = [ 4, slimeboss_rise6 ]
{
};

void() slimeboss_rise6 = [ 5, slimeboss_rise7 ]
{
};

void() slimeboss_rise7 = [ 6, slimeboss_rise8 ]
{
};

void() slimeboss_rise8 = [ 7, slimeboss_rise9 ]
{
};

void() slimeboss_rise9 = [ 8, slimeboss_rise10 ]
{
};

void() slimeboss_rise10 = [ 9, slimeboss_rise11 ]
{
};

void() slimeboss_rise11 = [ 10, slimeboss_rise12 ]
{
};

void() slimeboss_rise12 = [ 11, slimeboss_rise13 ]
{
};

void() slimeboss_rise13 = [ 12, slimeboss_rise14 ]
{
};

void() slimeboss_rise14 = [ 13, slimeboss_rise15 ]
{
};

void() slimeboss_rise15 = [ 14, slimeboss_rise16 ]
{
};

void() slimeboss_rise16 = [ 15, slimeboss_rise17 ]
{
};

void() slimeboss_rise17 = [ 16, slimeboss_missile1 ]
{
};

void() slimeboss_idle1 = [ 17, slimeboss_idle2 ]
{
};

void() slimeboss_idle2 = [ 18, slimeboss_idle3 ]
{
	slimeboss_face();
};

void() slimeboss_idle3 = [ 19, slimeboss_idle4 ]
{
	slimeboss_face();
};

void() slimeboss_idle4 = [ 20, slimeboss_idle5 ]
{
	slimeboss_face();
};

void() slimeboss_idle5 = [ 21, slimeboss_idle6 ]
{
	slimeboss_face();
};

void() slimeboss_idle6 = [ 22, slimeboss_idle7 ]
{
	slimeboss_face();
};

void() slimeboss_idle7 = [ 23, slimeboss_idle8 ]
{
	slimeboss_face();
};

void() slimeboss_idle8 = [ 24, slimeboss_idle9 ]
{
	slimeboss_face();
};

void() slimeboss_idle9 = [ 25, slimeboss_idle10 ]
{
	slimeboss_face();
};

void() slimeboss_idle10 = [ 26, slimeboss_idle11 ]
{
	slimeboss_face();
};

void() slimeboss_idle11 = [ 27, slimeboss_idle12 ]
{
	slimeboss_face();
};

void() slimeboss_idle12 = [ 28, slimeboss_idle13 ]
{
	slimeboss_face();
};

void() slimeboss_idle13 = [ 29, slimeboss_idle14 ]
{
	slimeboss_face();
};

void() slimeboss_idle14 = [ 30, slimeboss_idle15 ]
{
	slimeboss_face();
};

void() slimeboss_idle15 = [ 31, slimeboss_idle16 ]
{
	slimeboss_face();
};

void() slimeboss_idle16 = [ 32, slimeboss_idle17 ]
{
	slimeboss_face();
	if (coop)
	{
		slimeboss_missile1();
	}
};

void() slimeboss_idle17 = [ 33, slimeboss_idle18 ]
{
	slimeboss_face();
};

void() slimeboss_idle18 = [ 34, slimeboss_idle19 ]
{
	slimeboss_face();
};

void() slimeboss_idle19 = [ 35, slimeboss_idle20 ]
{
	slimeboss_face();
};

void() slimeboss_idle20 = [ 36, slimeboss_idle21 ]
{
	slimeboss_face();
};

void() slimeboss_idle21 = [ 37, slimeboss_idle22 ]
{
	slimeboss_face();
};

void() slimeboss_idle22 = [ 38, slimeboss_idle23 ]
{
	slimeboss_face();
};

void() slimeboss_idle23 = [ 39, slimeboss_idle24 ]
{
	slimeboss_face();
};

void() slimeboss_idle24 = [ 40, slimeboss_idle25 ]
{
	slimeboss_face();
};

void() slimeboss_idle25 = [ 41, slimeboss_idle26 ]
{
	slimeboss_face();
};

void() slimeboss_idle26 = [ 42, slimeboss_idle27 ]
{
	slimeboss_face();
};

void() slimeboss_idle27 = [ 43, slimeboss_idle28 ]
{
	slimeboss_face();
};

void() slimeboss_idle28 = [ 44, slimeboss_idle29 ]
{
	slimeboss_face();
};

void() slimeboss_idle29 = [ 45, slimeboss_idle30 ]
{
	slimeboss_face();
};

void() slimeboss_idle30 = [ 46, slimeboss_idle31 ]
{
	slimeboss_face();
};

void() slimeboss_idle31 = [ 47, slimeboss_idle1 ]
{
	slimeboss_face();
};

void() slimeboss_shake =
{
	local entity plyr;

	plyr = findradius(self.origin, 150);
	while (plyr)
	{
		if ((plyr.flags & FL_CLIENT))
		{
			random();
			plyr.punchangle_x = (-1 * (random() + ((0.025 * self.dmg) * 3)));
		}
	}
};

void() slimeboss_missile1 = [ 57, slimeboss_missile2 ]
{
	slimeboss_face();
};

void() slimeboss_missile2 = [ 58, slimeboss_missile3 ]
{
	slimeboss_face();
};

void() slimeboss_missile3 = [ 59, slimeboss_missile4 ]
{
	slimeboss_face();
};

void() slimeboss_missile4 = [ 60, slimeboss_missile5 ]
{
	slimeboss_face();
};

void() slimeboss_missile5 = [ 61, slimeboss_missile6 ]
{
	slimeboss_face();
};

void() slimeboss_missile6 = [ 62, slimeboss_missile7 ]
{
	slimeboss_face();
};

void() slimeboss_missile7 = [ 63, slimeboss_missile8 ]
{
	slimeboss_face();
};

void() slimeboss_missile8 = [ 64, slimeboss_missile9 ]
{
	slimeboss_face();
};

void() slimeboss_missile9 = [ 65, slimeboss_missile10 ]
{
	slimeboss_balls();
};

void() slimeboss_missile10 = [ 66, slimeboss_missile11 ]
{
	slimeboss_face();
};

void() slimeboss_missile11 = [ 67, slimeboss_missile12 ]
{
	slimeboss_face();
};

void() slimeboss_missile12 = [ 68, slimeboss_missile13 ]
{
	slimeboss_face();
};

void() slimeboss_missile13 = [ 69, slimeboss_missile14 ]
{
	slimeboss_face();
};

void() slimeboss_missile14 = [ 70, slimeboss_missile15 ]
{
	slimeboss_face();
};

void() slimeboss_missile15 = [ 71, slimeboss_missile16 ]
{
	slimeboss_face();
};

void() slimeboss_missile16 = [ 72, slimeboss_missile17 ]
{
	slimeboss_face();
};

void() slimeboss_missile17 = [ 73, slimeboss_missile18 ]
{
	slimeboss_face();
};

void() slimeboss_missile18 = [ 74, slimeboss_missile19 ]
{
	slimeboss_face();
};

void() slimeboss_missile19 = [ 75, slimeboss_missile20 ]
{
	slimeboss_face();
};

void() slimeboss_missile20 = [ 76, slimeboss_missile21 ]
{
	slimeboss_balls();
};

void() slimeboss_missile21 = [ 77, slimeboss_missile22 ]
{
	slimeboss_face();
};

void() slimeboss_missile22 = [ 78, slimeboss_missile23 ]
{
	slimeboss_face();
};

void() slimeboss_missile23 = [ 79, slimeboss_missile1 ]
{
	slimeboss_face();
};

void() slimeboss_shocka1 = [ 80, slimeboss_shocka2 ]
{
};

void() slimeboss_shocka2 = [ 81, slimeboss_shocka3 ]
{
};

void() slimeboss_shocka3 = [ 82, slimeboss_shocka4 ]
{
};

void() slimeboss_shocka4 = [ 83, slimeboss_missile1 ]
{
};

void() slimeboss_pain =
{
	if ((random() < 0.2))
	{
		slimeboss_shocka1();
		sound(self, CHAN_VOICE, "boss1/pain.wav", 1, ATTN_NORM);
	}
};

void() slimeboss_shockb1 = [ 90, slimeboss_shockb2 ]
{
};

void() slimeboss_shockb2 = [ 91, slimeboss_shockb3 ]
{
};

void() slimeboss_shockb3 = [ 92, slimeboss_shockb4 ]
{
};

void() slimeboss_shockb4 = [ 93, slimeboss_shockb5 ]
{
};

void() slimeboss_shockb5 = [ 94, slimeboss_shockb6 ]
{
};

void() slimeboss_shockb6 = [ 95, slimeboss_shockb7 ]
{
};

void() slimeboss_shockb7 = [ 90, slimeboss_shockb8 ]
{
};

void() slimeboss_shockb8 = [ 91, slimeboss_shockb9 ]
{
};

void() slimeboss_shockb9 = [ 92, slimeboss_shockb10 ]
{
};

void() slimeboss_shockb10 = [ 93, slimeboss_missile1 ]
{
};

void() slimeboss_shockc1 = [ 96, slimeboss_shockc2 ]
{
};

void() slimeboss_shockc2 = [ 97, slimeboss_shockc3 ]
{
};

void() slimeboss_shockc3 = [ 98, slimeboss_shockc4 ]
{
};

void() slimeboss_shockc4 = [ 99, slimeboss_shockc5 ]
{
};

void() slimeboss_shockc5 = [ 100, slimeboss_shockc6 ]
{
};

void() slimeboss_shockc6 = [ 101, slimeboss_shockc7 ]
{
};

void() slimeboss_shockc7 = [ 102, slimeboss_shockc8 ]
{
};

void() slimeboss_shockc8 = [ 103, slimeboss_shockc9 ]
{
};

void() slimeboss_shockc9 = [ 104, slimeboss_shockc10 ]
{
};

void() slimeboss_shockc10 = [ 105, slimeboss_death1 ]
{
};

void() slimeboss_death1 = [ 48, slimeboss_death2 ]
{
	sound(self, CHAN_VOICE, "boss1/death.wav", 1, ATTN_NORM);
};

void() slimeboss_death2 = [ 49, slimeboss_death3 ]
{
};

void() slimeboss_death3 = [ 50, slimeboss_death4 ]
{
};

void() slimeboss_death4 = [ 51, slimeboss_death5 ]
{
};

void() slimeboss_death5 = [ 52, slimeboss_death6 ]
{
};

void() slimeboss_death6 = [ 53, slimeboss_death7 ]
{
};

void() slimeboss_death7 = [ 54, slimeboss_death8 ]
{
};

void() slimeboss_death8 = [ 55, slimeboss_death9 ]
{
};

void() slimeboss_death9 = [ 56, slimeboss_death10 ]
{
	sound(self, CHAN_BODY, "boss1/out1.wav", 1, ATTN_NORM);
	pointparticles(particleeffectnum(/*26394i*/"slimesplash"), self.origin, VEC_ORIGIN, 1);
};

void() slimeboss_death10 = [ 56, slimeboss_death10 ]
{
	killed_monsters = killed_monsters + 1;
	WriteByte(MSG_ALL, SVC_KILLEDMONSTER);
	remove(self);
};

void() T_slimebossTouch =
{
	local float damg;
	local vector detonate;
	local float surfacenum;
	local string tex;

	if ((other == self.owner))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	surfacenum = getsurfacenearpoint(world, self.origin);
	if ((surfacenum >= 0))
	{
		tex = getsurfacetexture(world, surfacenum);
		if (((tex == "sky1") || (tex == "sky4")))
		{
			remove(self);
			return;
		}
	}
	damg = 10;
	if ((autocvar_explosiondebris == 0))
	{
		if (other.health)
		{
			if (((other.classname == "monster_shambler") || (other.classname == "monster_hell_knight2")))
			{
				damg = damg * 0.65;
			}
			T_Damage(other, self, self.owner, damg);
			detonate = self.origin;
			detonate = detonate - (8 * normalize(self.velocity));
		}
		else
		{
			detonate = self.origin;
			detonate = detonate - (8 * normalize(self.velocity));
		}
	}
	else
	{
		if (other.health)
		{
			if ((other.classname == "monster_shambler"))
			{
				damg = damg * 0.65;
			}
			T_Damage(other, self, self.owner, damg);
		}
		detonate = self.origin;
		detonate = detonate - (8 * normalize(self.velocity));
	}
	T_RadiusDamage(self, self.owner, 50, other);
	sound(self, CHAN_WEAPON, "boss1/expslime.wav", 1, ATTN_NORM);
	sendParticle("slimesplash_small", detonate, VEC_ORIGIN, 1);
	BecomeExplosion();
};

void() slimeboss_balls =
{
	local vector distancedelta;
	local vector nozdistancedelta;
	local entity missile;

	sound(self, CHAN_WEAPON, "boss1/throw.wav", 1, ATTN_NONE);
	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	setorigin(missile, self.origin);
	missile.origin = (self.origin + '0 0 30');
	makevectors(self.angles);
	distancedelta = self.enemy.origin - self.origin;
	nozdistancedelta = distancedelta;
	missile.velocity = normalize(distancedelta);
	missile.velocity = (missile.velocity * 700);
	missile.velocity_z = ((missile.velocity_z + 100) + ((vlen(nozdistancedelta) * 0.22) * (1 + (0.3 * random()))));
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.touch = T_slimebossTouch;
	missile.nextthink = (time + 2.5);
	missile.think = T_slimebossTouch;
	setmodel(missile, "progs/slimeball.mdl");
	missile.classname = "slimeball";
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
};

void(vector p) slimeboss_missile =
{
	local vector offang;
	local vector org;
	local vector vec;
	local vector d;
	local float t;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = ((self.origin + (p_x * v_forward)) + (p_y * v_right)) + (p_z * '0 0 1');
	if ((skill > 1))
	{
		t = vlen((self.enemy.origin - org)) / 300;
		vec = self.enemy.velocity;
		d = self.enemy.origin + (t * vec);
	}
	else
	{
		d = self.enemy.origin;
	}
	vec = normalize((d - org));
	launch_enemy_spike(org, vec);
	setmodel(newmis, "progs/lavaball.mdl");
	newmis.avelocity = '200 100 300';
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	newmis.velocity = (vec * 300);
	newmis.touch = T_MissileTouch_chton;
	sound(self, CHAN_WEAPON, "boss1/throw.wav", 1, ATTN_NORM);
	if ((self.enemy.health <= 0))
	{
		slimeboss_idle1();
	}
};

void() slimeboss_awake =
{
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.takedamage = DAMAGE_YES;
	setmodel(self, "progs/slimeboss.mdl");
	self.th_die = slimeboss_death1;
	self.th_pain = slimeboss_pain;
	setsize(self, VEC_HULL2_MIN, '32 32 79');
	self.alpha = (autocvar_monstertransparency * 0.01);
	if ((skill == 0))
	{
		self.health = 500;
	}
	else
	{
		self.health = 650;
	}
	self.enemy = activator;
	pointparticles(particleeffectnum(/*26394i*/"slimesplash"), self.origin, VEC_ORIGIN, 1);
	self.yaw_speed = 20;
	slimeboss_rise1();
};

void() monster_slimeboss =
{
	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/slimeboss.mdl");
	precache_model("progs/slimeball.mdl");
	precache_sound("weapons/rocket1i.wav");
	precache_sound("boss1/out1.wav");
	precache_sound("boss1/sight1.wav");
	precache_sound("misc/power.wav");
	precache_sound("boss1/throw.wav");
	precache_sound("boss1/pain.wav");
	precache_sound("boss1/death.wav");
	precache_sound("boss1/fireball.wav");
	precache_sound("boss1/launch.wav");
	precache_sound("boss1/expslime.wav");
	precache_sound("boss1/quake.wav");
	precache_sound("boss1/exp2.wav");
	precache_sound("boss1/atk2.wav");
	total_monsters = total_monsters + 1;
	self.use = slimeboss_awake;
};
