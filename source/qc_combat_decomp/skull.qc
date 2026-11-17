//Decompiled code. Please respect the original copyright.

void() SkullTouch =
{
	T_RadiusDamage(self, self, 120, world);
	pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
	pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
	pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
	if (other.takedamage)
	{
	}
	else
	{
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte(MSG_BROADCAST, TE_KNIGHTSPIKE);
		WriteCoord(MSG_BROADCAST, self.origin_x);
		WriteCoord(MSG_BROADCAST, self.origin_y);
		WriteCoord(MSG_BROADCAST, self.origin_z);
		sound(self, CHAN_WEAPON, "vengeance/skulltouch.wav", 0.5, ATTN_NORM);
	}
	sound7(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
	remove(self);
};

void() SkullHoming =
{
	local vector dir;
	local vector vtemp;
	local vector faceplayer1;
	local vector faceplayer2;

	vtemp = self.enemy.origin + '0 0 16';
	dir = normalize((vtemp - self.origin));
	faceplayer1 = vectoangles((vtemp - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.frame = (self.frame + 1);
	if ((self.frame >= 8))
	{
		self.frame = 0;
	}
	self.glow_size = (self.glow_size - 1);
	if ((self.glow_size < 550))
	{
		SkullTouch();
		return;
	}
	self.velocity = (dir * 140);
	self.nextthink = (time + 0.3);
	self.think = SkullHoming;
};

void() vengeance_skull_main =
{
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
	self.glow_color = 75;
	self.glow_size = 600;
	sound(self, CHAN_WEAPON, "vengeance/skull.wav", 1, ATTN_NORM);
	self.velocity = (dir * 280);
	self.nextthink = (flytime + time);
	self.think = SkullHoming;
	self.touch = SkullTouch;
};

void(vector org) launch_vengeance_skull =
{
	local vector face1;
	local vector face2;

	newmis = spawn();
	newmis.owner = self;
	newmis.movetype = MOVETYPE_FLYMISSILE;
	newmis.solid = SOLID_BBOX;
	face1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(face1);
	face2 = normalize(v_forward);
	newmis.angles = vectoangles(face2);
	newmis.traileffectnum = particleeffectnum(/*51651i*/"EF_STARDUST");
	newmis.touch = SkullTouch;
	newmis.classname = "skull_fly";
	newmis.think = vengeance_skull_main;
	newmis.nextthink = (time + 0.01);
	setmodel(newmis, "progs/skull.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, org);
	newmis.glow_color = 75;
	newmis.glow_size = 600;
	newmis.enemy = self.enemy;
};
