//Decompiled code. Please respect the original copyright.

void() spriteThink =
{
	local vector v;

	if ((self.frame < 7))
	{
		self.frame = (self.frame + 0.06);
	}
	v = self.origin + (self.velocity * frametime);
	self.lifetime = (self.lifetime + 1);
	if ((pointcontents(self.origin) != CONTENT_SOLID))
	{
		setorigin(self, v);
		if ((self.velocity_x > 0))
		{
			self.velocity_x = (self.velocity_x - (0.5 * csqc_slowmo));
		}
		if ((self.velocity_y > 0))
		{
			self.velocity_y = (self.velocity_y - (0.5 * csqc_slowmo));
		}
		self.velocity_z = (self.velocity_z + (0.6 * csqc_slowmo));
		self.angles_x = (self.angles_x + (2 * csqc_slowmo));
		self.angles_y = (self.angles_y + (2 * csqc_slowmo));
		self.oldorigin = self.origin;
	}
	self.think = spriteThink;
	self.nextthink = time;
	self.alpha = (self.alpha - 0.007);
	self.scale = (self.scale + 0.001);
	if ((self.lifetime > 100))
	{
		remove(self);
	}
};

void() spritegen =
{
	local entity sprite;

	sprite = spawn();
	self.lifetime = (self.lifetime + 1);
	sprite.effecttype = self.effecttype;
	if ((sprite.effecttype == EFF_SMOKE))
	{
		setmodel(sprite, "progs/s_smoke_muzz.spr");
		sprite.alpha = 0.8;
		sprite.scale = 0.3;
	}
	setorigin(sprite, self.origin);
	sprite.drawmask = MASK_ENGINE;
	sprite.velocity = self.velocity;
	sprite.velocity_old = self.velocity;
	sprite.velocity_old_z = (sprite.velocity_old_z + 10);
	if ((self.lifetime > 45))
	{
		remove(self);
	}
	sprite.think = spriteThink;
	sprite.nextthink = time;
	self.think = spritegen;
	self.nextthink = (time + 0.5);
};

void() casingSound =
{
	if ((self.casetype == CASING_SHELL))
	{
		if ((random() <= 0.4))
		{
			sound7(self, CHAN_WEAPON, "weapons/casings1.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
		}
		else
		{
			if ((random() >= 0.6))
			{
				sound7(self, CHAN_WEAPON, "weapons/casings2.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_WEAPON, "weapons/casings3.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
			}
		}
	}
	else
	{
		if ((self.casetype == CASING_NAIL))
		{
			if ((random() <= 0.4))
			{
				sound7(self, CHAN_WEAPON, "weapons/nailcase1.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
			}
			else
			{
				if ((random() >= 0.6))
				{
					sound7(self, CHAN_WEAPON, "weapons/nailcase2.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
				}
				else
				{
					sound7(self, CHAN_WEAPON, "weapons/nailcase3.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
				}
			}
		}
		else
		{
			if ((self.casetype == CASING_ROCKET))
			{
				if ((random() <= 0.6))
				{
					sound7(self, CHAN_WEAPON, "weapons/rockcase.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
				}
				else
				{
					sound7(self, CHAN_WEAPON, "weapons/rockcase1.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
				}
			}
		}
	}
};

#define MAX_CSQC_CASINGS 32
entity casing_q_head;
entity casing_q_tail;
float casing_q_count;

void(entity e) casing_unlink_and_remove =
{
	local entity p;
	local entity n;

	if ((e == world))
	{
		return;
	}
	p = e.enemy;
	n = e.chain;
	if ((p != world))
	{
		p.chain = n;
	}
	else
	{
		if ((casing_q_head == e))
		{
			casing_q_head = n;
		}
	}
	if ((n != world))
	{
		n.enemy = p;
	}
	else
	{
		if ((casing_q_tail == e))
		{
			casing_q_tail = p;
		}
	}
	e.enemy = world;
	e.chain = world;
	if ((casing_q_count > 0))
	{
		casing_q_count = (casing_q_count - 1);
	}
	remove(e);
};

void() casing_remove =
{
	casing_unlink_and_remove(self);
};

void() runphysics_casing_gravity =
{
	local vector v;
	local vector modelsize;
	local float dt;
	local float step_scale;

	dt = 0.025;
	step_scale = (1.8 * csqc_slowmo);
	if ((step_scale <= 0))
	{
		step_scale = 1.8;
	}
	v = self.origin + (self.velocity * dt);
	if ((self.casetype == CASING_SHELL))
	{
		modelsize = '0 0 2';
	}
	else
	{
		if ((self.casetype == CASING_NAIL))
		{
			modelsize = '0 0 1';
		}
		else
		{
			if ((self.casetype == CASING_ROCKET))
			{
				modelsize = '0 0 2';
			}
		}
	}
	if ((pointcontents((self.origin - modelsize)) != CONTENT_SOLID))
	{
		setorigin(self, v);
		if ((self.velocity_x > 0))
		{
			self.velocity_x = (self.velocity_x - (0.5 * step_scale));
		}
		if ((self.velocity_y > 0))
		{
			self.velocity_y = (self.velocity_y - (0.5 * step_scale));
		}
		self.velocity_z = (self.velocity_z - (6 * step_scale));
		self.angles_x = (self.angles_x + (2 * step_scale));
		self.angles_y = (self.angles_y + (2 * step_scale));
		self.oldorigin = self.origin;
	}
	else
	{
		if ((pointcontents(self.origin) == CONTENT_SOLID))
		{
			if ((self.casetype == CASING_SHELL))
			{
				if ((pointcontents((self.origin - '0 0 2')) == CONTENT_SOLID))
				{
					setorigin(self, (self.origin + '0 0 1'));
				}
			}
			else
			{
				if ((self.casetype == CASING_NAIL))
				{
					if ((pointcontents((self.origin - '0 0 3')) == CONTENT_SOLID))
					{
						setorigin(self, (self.origin + '0 0 1'));
					}
					else
					{
						if ((pointcontents((self.origin - '0 0 1')) == CONTENT_SOLID))
						{
							setorigin(self, (self.origin + '0 0 0.5'));
							self.velocity = VEC_0;
						}
					}
				}
				else
				{
					if ((self.casetype == CASING_ROCKET))
					{
						if ((pointcontents((self.origin - '0 0 2')) == CONTENT_SOLID))
						{
							setorigin(self, (self.origin + '0 0 2'));
						}
					}
				}
			}
			if ((pointcontents((self.origin - '0 3 0')) == CONTENT_SOLID))
			{
				setorigin(self, (self.origin + '0 3 0'));
				self.velocity_y = (0 - self.velocity_y);
				self.velocity_old_y = (0 - self.velocity_old_y);
			}
			if ((pointcontents((self.origin + '0 3 0')) == CONTENT_SOLID))
			{
				setorigin(self, (self.origin - '0 3 0'));
				self.velocity_y = (0 - self.velocity_y);
				self.velocity_old_y = (0 - self.velocity_old_y);
			}
			if ((pointcontents((self.origin - '3 0 0')) == CONTENT_SOLID))
			{
				setorigin(self, (self.origin + '3 0 0'));
				self.velocity_x = (0 - self.velocity_x);
				self.velocity_old_x = (0 - self.velocity_old_x);
			}
			if ((pointcontents((self.origin + '3 0 0')) == CONTENT_SOLID))
			{
				setorigin(self, (self.origin - '3 0 0'));
				self.velocity_x = (0 - self.velocity_x);
				self.velocity_old_x = (0 - self.velocity_old_x);
			}
		}
		else
		{
			if ((self.velocity_z < -9))
			{
				self.velocity_old_z = (self.velocity_old_z / 1.01);
			}
			else
			{
				self.velocity_old_z = (self.velocity_old_z / 1.4);
			}
			if ((self.velocity_old_y < -2))
			{
				self.velocity_old_x = (self.velocity_old_x / 1.04);
			}
			else
			{
				self.velocity_old_x = (self.velocity_old_x / 1.4);
			}
			if ((self.velocity_old_y < -2))
			{
				self.velocity_old_y = (self.velocity_old_y / 1.04);
			}
			else
			{
				self.velocity_old_y = (self.velocity_old_y / 1.4);
			}
			self.velocity = (self.velocity_old * 2);
			self.velocity_z = (self.velocity_old_z * 1.65);
			if ((self.velocity_z > 0))
			{
				v = self.origin + (self.velocity * dt);
			}
			setorigin(self, v);
			if ((self.angles_x != 0))
			{
				casingSound();
			}
			self.angles_x = 0;
		}
	}
};

void() casing_placement =
{
	runphysics_casing_gravity();
	if ((((time - self.casing_born) > 2.5) || ((pointcontents((self.origin - '0 0 4')) == CONTENT_SOLID) && ((self.velocity_z < 1) && (self.velocity_z > -1)))))
	{
		self.velocity = VEC_0;
		self.nextthink = (time + 8);
		self.think = casing_remove;
		return;
	}
	self.nextthink = (time + 0.025);
};

void() casing =
{
	local entity casing;

	while (((casing_q_count >= MAX_CSQC_CASINGS) && (casing_q_head != world)))
	{
		casing_unlink_and_remove(casing_q_head);
	}
	casing = spawn();
	casing.enemy = casing_q_tail;
	casing.chain = world;
	if ((casing_q_tail != world))
	{
		casing_q_tail.chain = casing;
	}
	else
	{
		casing_q_head = casing;
	}
	casing_q_tail = casing;
	casing_q_count = (casing_q_count + 1);
	casing.casing_born = time;
	casing.angles = view_angles;
	casing.angles_x = (casing.angles_x * -1);
	casing.casetype = self.casetype;
	if ((casing.casetype == CASING_SHELL))
	{
		setmodel(casing, "progs/casing.mdl");
		setsize(casing, '-1 -1 -2', '1 1 2');
	}
	else
	{
		if ((casing.casetype == CASING_NAIL))
		{
			setmodel(casing, "progs/nailcasing.mdl");
			setsize(casing, '-1 -1 -2', '1 1 2');
		}
		else
		{
			if ((casing.casetype == CASING_ROCKET))
			{
				setmodel(casing, "progs/missilecasing.mdl");
				setsize(casing, '-1 -1 1', VEC_1);
			}
		}
	}
	setorigin(casing, self.origin);
	casing.scale = 0.9;
	casing.alpha = 1;
	casing.movetype = MOVETYPE_BOUNCE;
	casing.solid = SOLID_TRIGGER;
	casing.drawmask = MASK_ENGINE;
	casing.velocity = self.velocity;
	casing.velocity_old = self.velocity;
	casing.velocity_old_z = (casing.velocity_old_z + 10);
	casing.think = casing_placement;
	casing.nextthink = time;
	casing.cansplash = TRUE;
	casing.count = 0;
};

void() Particle_Emitter_Think =
{
	pointparticles(self.fx, self.origin, self.velocity, self.count);
	if ((self.wait > 0))
	{
		self.think = SUB_Remove;
		self.nextthink = (time + self.wait);
		return;
	}
	remove(self);
};

void(float isnew) Sprite_Spawner =
{
	self.origin_x = ReadCoord();
	self.origin_y = ReadCoord();
	self.origin_z = ReadCoord();
	self.velocity_x = ReadCoord();
	self.velocity_y = ReadCoord();
	self.velocity_z = ReadCoord();
	self.effecttype = ReadCoord();
	setorigin(self, self.origin);
	self.think = spritegen;
	self.nextthink = time;
	self.classname = "sprite";
};

void(float isnew) Casing_Spawner =
{
	self.origin_x = ReadCoord();
	self.origin_y = ReadCoord();
	self.origin_z = ReadCoord();
	self.velocity_x = ReadCoord();
	self.velocity_y = ReadCoord();
	self.velocity_z = ReadCoord();
	self.casetype = ReadCoord();
	setorigin(self, self.origin);
	self.think = casing;
	self.nextthink = time;
};

void(float isnew) Particle_Emitter =
{
	local string temp_fxname;

	self.origin_x = ReadCoord();
	self.origin_y = ReadCoord();
	self.origin_z = ReadCoord();
	self.velocity_x = ReadCoord();
	self.velocity_y = ReadCoord();
	self.velocity_z = ReadCoord();
	self.count = ReadCoord();
	self.wait = ReadCoord();
	temp_fxname = strzone(ReadString());
	self.fx = particleeffectnum(temp_fxname);
	setorigin(self, self.origin);
	if ((self.fx == -1))
	{
		print(/*11145i*/"no effectinfo for ", temp_fxname, /*48i*/"\n");
		strunzone(temp_fxname);
		remove(self);
		return;
	}
	strunzone(temp_fxname);
	self.think = Particle_Emitter_Think;
	self.nextthink = time;
};
