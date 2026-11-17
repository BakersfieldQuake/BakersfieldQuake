//Decompiled code. Please respect the original copyright.

void() boss_face =
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

void() boss_rise1 = [ 0, boss_rise2 ]
{
	sound(self, CHAN_WEAPON, "boss1/out1.wav", 1, ATTN_NORM);
};

void() boss_rise2 = [ 1, boss_rise3 ]
{
	sound(self, CHAN_VOICE, "boss1/sight1.wav", 1, ATTN_NORM);
};

void() boss_rise3 = [ 2, boss_rise4 ]
{
};

void() boss_rise4 = [ 3, boss_rise5 ]
{
	self.weapontimer = 0;
};

void() boss_rise5 = [ 4, boss_rise6 ]
{
};

void() boss_rise6 = [ 5, boss_rise7 ]
{
};

void() boss_rise7 = [ 6, boss_rise8 ]
{
};

void() boss_rise8 = [ 7, boss_rise9 ]
{
};

void() boss_rise9 = [ 8, boss_rise10 ]
{
};

void() boss_rise10 = [ 9, boss_rise11 ]
{
};

void() boss_rise11 = [ 10, boss_rise12 ]
{
};

void() boss_rise12 = [ 11, boss_rise13 ]
{
};

void() boss_rise13 = [ 12, boss_rise14 ]
{
};

void() boss_rise14 = [ 13, boss_rise15 ]
{
};

void() boss_rise15 = [ 14, boss_rise16 ]
{
};

void() boss_rise16 = [ 15, boss_rise17 ]
{
};

void() boss_rise17 = [ 16, boss_missile1 ]
{
};

void() boss_idle1 = [ 17, boss_idle2 ]
{
};

void() boss_idle2 = [ 18, boss_idle3 ]
{
	boss_face();
};

void() boss_idle3 = [ 19, boss_idle4 ]
{
	boss_face();
};

void() boss_idle4 = [ 20, boss_idle5 ]
{
	boss_face();
};

void() boss_idle5 = [ 21, boss_idle6 ]
{
	boss_face();
};

void() boss_idle6 = [ 22, boss_idle7 ]
{
	boss_face();
};

void() boss_idle7 = [ 23, boss_idle8 ]
{
	boss_face();
};

void() boss_idle8 = [ 24, boss_idle9 ]
{
	boss_face();
};

void() boss_idle9 = [ 25, boss_idle10 ]
{
	boss_face();
};

void() boss_idle10 = [ 26, boss_idle11 ]
{
	boss_face();
};

void() boss_idle11 = [ 27, boss_idle12 ]
{
	boss_face();
};

void() boss_idle12 = [ 28, boss_idle13 ]
{
	boss_face();
};

void() boss_idle13 = [ 29, boss_idle14 ]
{
	boss_face();
};

void() boss_idle14 = [ 30, boss_idle15 ]
{
	boss_face();
};

void() boss_idle15 = [ 31, boss_idle16 ]
{
	boss_face();
};

void() boss_idle16 = [ 32, boss_idle17 ]
{
	boss_face();
	if (coop)
	{
		boss_missile1();
	}
};

void() boss_idle17 = [ 33, boss_idle18 ]
{
	boss_face();
};

void() boss_idle18 = [ 34, boss_idle19 ]
{
	boss_face();
};

void() boss_idle19 = [ 35, boss_idle20 ]
{
	boss_face();
};

void() boss_idle20 = [ 36, boss_idle21 ]
{
	boss_face();
};

void() boss_idle21 = [ 37, boss_idle22 ]
{
	boss_face();
};

void() boss_idle22 = [ 38, boss_idle23 ]
{
	boss_face();
};

void() boss_idle23 = [ 39, boss_idle24 ]
{
	boss_face();
};

void() boss_idle24 = [ 40, boss_idle25 ]
{
	boss_face();
};

void() boss_idle25 = [ 41, boss_idle26 ]
{
	boss_face();
};

void() boss_idle26 = [ 42, boss_idle27 ]
{
	boss_face();
};

void() boss_idle27 = [ 43, boss_idle28 ]
{
	boss_face();
};

void() boss_idle28 = [ 44, boss_idle29 ]
{
	boss_face();
};

void() boss_idle29 = [ 45, boss_idle30 ]
{
	boss_face();
};

void() boss_idle30 = [ 46, boss_idle31 ]
{
	boss_face();
};

void() boss_idle31 = [ 47, boss_idle1 ]
{
	boss_face();
};

void() boss_shake =
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

void() lava_crack1 = [ 0, lava_crack2 ]
{
};

void() lava_crack2 = [ 1, lava_crack3 ]
{
};

void() lava_crack3 = [ 2, lava_crack4 ]
{
};

void() lava_crack4 = [ 3, lava_crack5 ]
{
};

void() lava_crack5 = [ 4, lava_crack6 ]
{
};

void() lava_crack6 = [ 5, lava_crack6 ]
{
	pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
	sound(self, CHAN_AUTO, "boss1/exp2.wav", 0.7, ATTN_NORM);
	self.think = boss_trap_fin;
	self.nextthink = (time + 0.1);
};

void() boss_missile1 = [ 57, boss_missile2 ]
{
	boss_face();
};

void() boss_missile2 = [ 58, boss_missile3 ]
{
	boss_face();
};

void() boss_missile3 = [ 59, boss_missile4 ]
{
	boss_face();
};

void() boss_missile4 = [ 60, boss_missile5 ]
{
	boss_face();
};

void() boss_missile5 = [ 61, boss_missile6 ]
{
	boss_face();
};

void() boss_missile6 = [ 62, boss_missile7 ]
{
	boss_face();
	self.weapontimer = (self.weapontimer + 1);
	if ((((random() < 0.3) && (self.health < 3)) && (self.weapontimer >= 3)))
	{
		boss_trap1();
	}
};

void() boss_missile7 = [ 63, boss_missile8 ]
{
	boss_face();
};

void() boss_missile8 = [ 64, boss_missile9 ]
{
	boss_face();
};

void() boss_missile9 = [ 65, boss_missile10 ]
{
	boss_missile('100 100 200');
};

void() boss_missile10 = [ 66, boss_missile11 ]
{
	boss_face();
};

void() boss_missile11 = [ 67, boss_missile12 ]
{
	boss_face();
};

void() boss_missile12 = [ 68, boss_missile13 ]
{
	boss_face();
};

void() boss_missile13 = [ 69, boss_missile14 ]
{
	boss_face();
};

void() boss_missile14 = [ 70, boss_missile15 ]
{
	boss_face();
};

void() boss_missile15 = [ 71, boss_missile16 ]
{
	boss_face();
};

void() boss_missile16 = [ 72, boss_missile17 ]
{
	boss_face();
};

void() boss_missile17 = [ 73, boss_missile18 ]
{
	boss_face();
};

void() boss_missile18 = [ 74, boss_missile19 ]
{
	boss_face();
};

void() boss_missile19 = [ 75, boss_missile20 ]
{
	boss_face();
};

void() boss_missile20 = [ 76, boss_missile21 ]
{
	boss_missile('100 -100 200');
};

void() boss_missile21 = [ 77, boss_missile22 ]
{
	boss_face();
};

void() boss_missile22 = [ 78, boss_missile23 ]
{
	boss_face();
};

void() boss_missile23 = [ 79, boss_missile1 ]
{
	boss_face();
	if ((((random() < 0.5) && (self.health < 4)) && (skill != 0)))
	{
		boss_magic1();
	}
};

void() boss_shocka1 = [ 80, boss_shocka2 ]
{
};

void() boss_shocka2 = [ 81, boss_shocka3 ]
{
};

void() boss_shocka3 = [ 82, boss_shocka4 ]
{
};

void() boss_shocka4 = [ 83, boss_shocka5 ]
{
};

void() boss_shocka5 = [ 84, boss_shocka6 ]
{
};

void() boss_shocka6 = [ 85, boss_shocka7 ]
{
};

void() boss_shocka7 = [ 86, boss_shocka8 ]
{
};

void() boss_shocka8 = [ 87, boss_shocka9 ]
{
};

void() boss_shocka9 = [ 88, boss_shocka10 ]
{
};

void() boss_shocka10 = [ 89, boss_missile1 ]
{
};

void() boss_shockb1 = [ 90, boss_shockb2 ]
{
};

void() boss_shockb2 = [ 91, boss_shockb3 ]
{
};

void() boss_shockb3 = [ 92, boss_shockb4 ]
{
};

void() boss_shockb4 = [ 93, boss_shockb5 ]
{
};

void() boss_shockb5 = [ 94, boss_shockb6 ]
{
};

void() boss_shockb6 = [ 95, boss_shockb7 ]
{
};

void() boss_shockb7 = [ 90, boss_shockb8 ]
{
};

void() boss_shockb8 = [ 91, boss_shockb9 ]
{
};

void() boss_shockb9 = [ 92, boss_shockb10 ]
{
};

void() boss_shockb10 = [ 93, boss_missile1 ]
{
};

void() boss_shockc1 = [ 96, boss_shockc2 ]
{
};

void() boss_shockc2 = [ 97, boss_shockc3 ]
{
};

void() boss_shockc3 = [ 98, boss_shockc4 ]
{
};

void() boss_shockc4 = [ 99, boss_shockc5 ]
{
};

void() boss_shockc5 = [ 100, boss_shockc6 ]
{
};

void() boss_shockc6 = [ 101, boss_shockc7 ]
{
};

void() boss_shockc7 = [ 102, boss_shockc8 ]
{
};

void() boss_shockc8 = [ 103, boss_shockc9 ]
{
};

void() boss_shockc9 = [ 104, boss_shockc10 ]
{
};

void() boss_shockc10 = [ 105, boss_death1 ]
{
};

void() boss_magic1 = [ 57, boss_magic2 ]
{
	sound(self, CHAN_VOICE, "boss1/sight1.wav", 0.6, ATTN_NONE);
};

void() boss_magic2 = [ 58, boss_magic3 ]
{
};

void() boss_magic3 = [ 59, boss_magic4 ]
{
};

void() boss_magic4 = [ 48, boss_magic5 ]
{
};

void() boss_magic5 = [ 50, boss_magic6 ]
{
};

void() boss_magic6 = [ 49, boss_magic7 ]
{

	if (((self.health < 3) && FacingIdeal()))
	{
		boss_flamewave();
	}
};

void() boss_magic7 = [ 50, boss_magic8 ]
{
	if (FacingIdeal())
	{
		boss_flamewave();
	}
};

void() boss_magic8 = [ 49, boss_magic9 ]
{

	if (((self.health < 3) && FacingIdeal()))
	{
		boss_flamewave();
	}
};

void() boss_magic9 = [ 48, boss_missile1 ]
{
	boss_flamewave();
};

void() boss_trap1 = [ 10, boss_trap2 ]
{
	sound(self, CHAN_VOICE, "boss1/atk2.wav", 1, ATTN_NORM);
};

void() boss_trap2 = [ 11, boss_trap3 ]
{
};

void() boss_trap3 = [ 12, boss_trap4 ]
{
};

void() boss_trap4 = [ 13, boss_trap5 ]
{
};

void() boss_trap5 = [ 14, boss_trap6 ]
{
};

void() boss_trap6 = [ 15, boss_trap7 ]
{
};

void() boss_trap7 = [ 16, boss_trap8 ]
{
	boss_lavamagic();
};

void() boss_trap8 = [ 12, boss_trap9 ]
{
};

void() boss_trap9 = [ 11, boss_trap10 ]
{
};

void() boss_trap10 = [ 10, boss_missile1 ]
{
};

void() boss_death1 = [ 48, boss_death2 ]
{
	sound(self, CHAN_VOICE, "boss1/death.wav", 1, ATTN_NORM);
};

void() boss_death2 = [ 49, boss_death3 ]
{
};

void() boss_death3 = [ 50, boss_death4 ]
{
};

void() boss_death4 = [ 51, boss_death5 ]
{
};

void() boss_death5 = [ 52, boss_death6 ]
{
};

void() boss_death6 = [ 53, boss_death7 ]
{
};

void() boss_death7 = [ 54, boss_death8 ]
{
};

void() boss_death8 = [ 55, boss_death9 ]
{
};

void() boss_death9 = [ 56, boss_death10 ]
{
	sound(self, CHAN_BODY, "boss1/out1.wav", 1, ATTN_NORM);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LAVASPLASH);
	WriteCoord(MSG_BROADCAST, self.origin_x);
	WriteCoord(MSG_BROADCAST, self.origin_y);
	WriteCoord(MSG_BROADCAST, self.origin_z);
};

void() boss_death10 = [ 56, boss_death10 ]
{
	killed_monsters = killed_monsters + 1;
	WriteByte(MSG_ALL, SVC_KILLEDMONSTER);
	SUB_UseTargets();
	remove(self);
};

void() T_BossTouch_chton =
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
	damg = autocvar_chton_lavaballs + (random() * 20);
	if ((autocvar_explosiondebris == 0))
	{
		if (other.health)
		{
			if ((other.classname == "monster_shambler"))
			{
				damg = damg * 0.65;
			}
			T_Damage(other, self, self.owner, damg);
			detonate = self.origin;
			detonate = detonate - (8 * normalize(self.velocity));
			pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), detonate, VEC_ORIGIN, 1);
		}
		else
		{
			detonate = self.origin;
			detonate = detonate - (8 * normalize(self.velocity));
			pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), detonate, VEC_ORIGIN, 1);
		}
	}
	else
	{
		if (other.health)
		{
			if (((other.classname == "monster_shambler") || (self.classname == "monster_hell_knight2")))
			{
				damg = damg * 0.65;
			}
			T_Damage(other, self, self.owner, damg);
		}
		detonate = self.origin;
		detonate = detonate - (8 * normalize(self.velocity));
		pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), detonate, VEC_ORIGIN, 1);
	}
	T_RadiusDamage(self, self.owner, 80, other);
	sound(self, CHAN_WEAPON, "boss1/exphuge.wav", 1, ATTN_NORM);
	BecomeExplosion();
};

void() boss_flamewave =
{
	local entity missile;
	local vector dir;
	local vector follow;
	local float dist;

	follow = self.enemy.velocity * 1.3;
	if ((skill >= 3))
	{
		dir = normalize((((self.enemy.origin + '0 0 -200') + (follow * 0.4)) - self.origin));
	}
	else
	{
		dir = normalize(((self.enemy.origin + '0 0 -200') - self.origin));
	}
	dist = vlen((self.enemy.origin - self.origin));
	self.effects = (self.effects | EF_MUZZLEFLASH);
	sound(self, CHAN_WEAPON, "boss1/launch.wav", 1, ATTN_NONE);
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_FLYMISSILE;
	setmodel(missile, "progs/bossball.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.origin = (self.origin + '0 0 200');
	missile.velocity = (dir * 950);
	missile.avelocity = '0 0 300';
	missile.nextthink = (time + 12);
	missile.angles = vectoangles(missile.velocity);
	missile.think = T_BossTouch_chton;
	missile.touch = T_BossTouch_chton;
};

void() trap_flame_touch =
{
	ApplyFireDmg(other, 0.1, 0.1);
	self.touch = SUB_Null;
};

void() boss_trap_fin =
{
	local entity flame;

	flame = spawn();
	flame.owner = self;
	setmodel(flame, "progs/s_flame.spr");
	setorigin(flame, self.origin);
	setsize(flame, VEC_ORIGIN, VEC_ORIGIN);
	flame.velocity = '0 0 120';
	flame.velocity_x = ((random() * 40) + -20);
	flame.velocity_y = ((random() * 40) + -20);
	flame.movetype = MOVETYPE_FLY;
	flame.solid = SOLID_TRIGGER;
	flame.nextthink = ((time + 0.1) + (random() * 0.05));
	flame.think = trap_gasshooter_think;
	flame.touch = trap_flame_touch;
	self.think = boss_trap_fin;
	self.nextthink = (time + 0.2);
};

void() boss_trap = [ 0, lava_crack1 ]
{
};

void() boss_lavamagic =
{
	local entity missile;

	if ((self.weapontimer == 3))
	{
		self.weapontimer = 0;
	}
	sound(self, CHAN_AUTO, "boss1/quake.wav", 1, ATTN_NONE);
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_TOSS;
	setmodel(missile, "progs/lavacrack.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.origin = (self.enemy.origin + '0 0 -15');
	missile.nextthink = (time + 0.1);
	missile.angles_y = ((random() * 720) + -360);
	missile.think = boss_trap;
};

void(vector p) boss_missile =
{
	local vector offang;
	local vector org;
	local vector vec;
	local vector d;
	local float t;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = ((self.origin + (p_x * v_forward)) + (p_y * v_right)) + (p_z * '0 0 1');
	if (((skill > 1) && (random() < 0.9)))
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
		boss_idle1();
	}
};

void() boss_awake =
{
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.takedamage = 0;
	setmodel(self, "progs/boss.mdl");
	setsize(self, '-128 -128 -24', '128 128 256');
	self.traileffectnum = particleeffectnum(/*56526i*/"chton_on_fire");
	self.alpha = (autocvar_monstertransparency * 0.01);
	if ((world.model == "maps/e1m7.bsp"))
	{
		if ((skill == 0))
		{
			self.health = 1;
		}
		else
		{
			if ((skill == 1))
			{
				self.health = 4;
			}
			else
			{
				self.health = 5;
			}
		}
	}
	else
	{
		if ((skill == 0))
		{
			self.health = 1;
		}
		else
		{
			if ((skill == 1))
			{
				self.health = 2;
			}
			else
			{
				self.health = 3;
			}
		}
	}
	self.enemy = activator;
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LAVASPLASH);
	WriteCoord(MSG_BROADCAST, self.origin_x);
	WriteCoord(MSG_BROADCAST, self.origin_y);
	WriteCoord(MSG_BROADCAST, self.origin_z);
	self.yaw_speed = 20;
	boss_rise1();
};

void() monster_boss =
{
	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/boss.mdl");
	precache_model("progs/lavaball.mdl");
	precache_model("progs/bossball.mdl");
	precache_model("progs/lavacrack.mdl");
	precache_model("progs/s_flame.spr");
	precache_sound("weapons/rocket1i.wav");
	precache_sound("boss1/out1.wav");
	precache_sound("boss1/sight1.wav");
	precache_sound("misc/power.wav");
	precache_sound("boss1/throw.wav");
	precache_sound("boss1/pain.wav");
	precache_sound("boss1/death.wav");
	precache_sound("boss1/fireball.wav");
	precache_sound("boss1/launch.wav");
	precache_sound("boss1/exphuge.wav");
	precache_sound("boss1/quake.wav");
	precache_sound("boss1/exp2.wav");
	precache_sound("boss1/atk2.wav");
	total_monsters = total_monsters + 1;
	self.use = boss_awake;
};

void() lightning_fire =
{
	local vector p1;
	local vector p2;

	if ((time >= lightning_end))
	{
		self = le1;
		door_go_down();
		self = le2;
		door_go_down();
		return;
	}
	p1 = (le1.mins + le1.maxs) * 0.5;
	p2 = (le2.mins + le2.maxs) * 0.5;
	p2 = p2 - (normalize((p2 - p1)) * 100);
	self.nextthink = (time + 0.1);
	self.think = lightning_fire;
	WriteByte(MSG_ALL, SVC_TEMPENTITY);
	WriteByte(MSG_ALL, TE_LIGHTNING3);
	WriteEntity(MSG_ALL, world);
	WriteCoord(MSG_ALL, p1_x);
	WriteCoord(MSG_ALL, 0);
	WriteCoord(MSG_ALL, (le1.absmin_z - 16));
	WriteCoord(MSG_ALL, p2_x);
	WriteCoord(MSG_ALL, 0);
	WriteCoord(MSG_ALL, (le2.absmin_z - 16));
};

void() lightning_use =
{
	if ((lightning_end >= (time + 1)))
	{
		return;
	}
	le1 = find(world, target, "lightning");
	le2 = find(le1, target, "lightning");
	if ((!le1 || !le2))
	{
		dprint("missing lightning targets\n");
		return;
	}
	if (((((le1.state != STATE_TOP) && (le1.state != STATE_BOTTOM)) || ((le2.state != STATE_TOP) && (le2.state != STATE_BOTTOM))) || (le1.state != le2.state)))
	{
		return;
	}
	le1.nextthink = -1;
	le2.nextthink = -1;
	lightning_end = time + 1;
	sound(self, CHAN_VOICE, "misc/power.wav", 1, ATTN_NORM);
	lightning_fire();
	self = find(world, classname, "monster_boss");
	if (!self)
	{
		return;
	}
	self.enemy = activator;
	if (((le1.state == STATE_TOP) && (self.health > 0)))
	{
		sound(self, CHAN_VOICE, "boss1/pain.wav", 1, ATTN_NORM);
		self.health = (self.health - 1);
		if ((self.health >= 2))
		{
			boss_shocka1();
		}
		else
		{
			if ((self.health == 1))
			{
				boss_shockb1();
			}
			else
			{
				if ((self.health == 0))
				{
					boss_shockc1();
				}
			}
		}
		if ((self.health == 4))
		{
			if (((!coop && !deathmatch) && autocvar_auto_save))
			{
				stuffcmd(self.enemy, "Echo Checkpoint...\n");
				stuffcmd(self.enemy, "save autosaves/autosave\n");
			}
		}
		else
		{
			if ((self.health == 3))
			{
				self.colormod = '0.6 0.6 0.6';
			}
			else
			{
				if ((self.health == 2))
				{
					self.colormod = '0.4 0.4 0.4';
					if (((!coop && !deathmatch) && autocvar_auto_save))
					{
						stuffcmd(self.enemy, "Echo Checkpoint...\n");
						stuffcmd(self.enemy, "save autosaves/autosave\n");
					}
				}
				else
				{
					if ((self.health == 1))
					{
						self.colormod = '0.2 0.2 0.2';
					}
				}
			}
		}
	}
};

void() event_lightning =
{
	self.use = lightning_use;
};
