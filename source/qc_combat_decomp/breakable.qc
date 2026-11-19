//Decompiled code. Please respect the original copyright.

void() breakable_remove =
{
	self.think = model_fade;
	self.nextthink = (time + 0.1);
	self.ltime = self.nextthink;
};

void() breakable_particle =
{
	if (self.wait)
	{
		if ((self.waitmin < time))
		{
			self.nextthink = (time + 0.1);
		}
		else
		{
			self.nextthink = self.waitmin;
		}
		self.think = breakable_remove;
	}
	else
	{
		if ((random() < 0.5))
		{
			self.nextthink = (time + 0.01);
		}
		else
		{
			self.nextthink = (time + 0.02);
		}
		rint((self.pos1_x + (random() * self.pos1_y)));
		particle(self.origin, self.oldorigin, rint((self.pos1_x + (random() * self.pos1_y))), self.pos1_z);
		if ((self.waitmin < time))
		{
			self.think = breakable_remove;
		}
	}
};

void() breakable_touch =
{
	if (self.touchedvoid)
	{
		entity_remove(self, 0.1);
		return;
	}
	if (check_skycontent(self.origin))
	{
		remove(self);
		return;
	}
	if ((other.classtype == CT_FUNCBREAKOBJ))
	{
		return;
	}
	if ((other.solid == SOLID_TRIGGER))
	{
		return;
	}
	self.wait = TRUE;
	if ((self.count < 1))
	{
		self.touch = SUB_Null;
		self.solid = 0;
		self.avelocity = VEC_ORIGIN;
	}
	else
	{
		if ((self.owner.spawnflags & BREAK_DAMAGE))
		{
			if (other.takedamage)
			{
				if (((other.flags & FL_MONSTER) && (self.owner.spawnflags & BREAK_NOMONSTER)))
				{
				}
				else
				{
					T_Damage(other, self, self, self.owner.dmg, DAMARMOR);
				}
			}
		}
		self.count = (self.count - 1);
		if (!(self.owner.spawnflags & BREAK_NOSOUND))
		{
			random();
			self.lip = (random() * self.owner.brkimpqty);
			if ((self.lip < 1))
			{
				sound7(self, CHAN_VOICE, self.owner.noise1, 1, ATTN_BREAK, SNDSPD);
			}
			else
			{
				if ((self.lip < 2))
				{
					sound7(self, CHAN_VOICE, self.owner.noise2, 1, ATTN_BREAK, SNDSPD);
				}
				else
				{
					if ((self.lip < 3))
					{
						sound7(self, CHAN_VOICE, self.owner.noise3, 1, ATTN_BREAK, SNDSPD);
					}
					else
					{
						sound7(self, CHAN_VOICE, self.owner.noise4, 1, ATTN_BREAK, SNDSPD);
					}
				}
			}
		}
	}
};

void() funcbreakable_use =
{
	local vector dirvec;
	local vector rorg;
	local vector gvel;
	local vector dirorg;
	local float content_loop;
	local float content_flag;

	if (self.waitmin)
	{
		return;
	}
	if (!(self.spawnflags & BREAK_SILENT))
	{
		sound7(self.attachment, CHAN_BODY, self.noise, 1, ATTN_NORM, SNDSPD);
	}
	if ((self.noise == SOUND_BRK_GLASS))
	{
		particleeffectnum(/*18343i*/"glass_break");
		pointparticles(particleeffectnum(/*18343i*/"glass_break"), self.attachment.origin, VEC_ORIGIN, 1);
	}
	if ((self.classtype == CT_FUNCBREAK))
	{
		self.waitmin = TRUE;
		self.use = SUB_Null;
		self.takedamage = 0;
		self.model = "";
		self.solid = 0;
		self.movetype = 0;
		self.oldorigin = (self.attachment.origin - (self.size * 0.5));
	}
	else
	{
		if ((self.classtype == CT_FUNCBREAKMDL))
		{
			self.waitmin = TRUE;
			self.use = SUB_Null;
			self.takedamage = 0;
			self.model = "";
			self.solid = 0;
			self.movetype = 0;
		}
		else
		{
			self.oldorigin = self.origin;
		}
	}
	if ((self.target != ""))
	{
		if ((self.activate.flags & FL_CLIENT))
		{
			activator = self.activate;
		}
		SUB_UseTargets();
	}
	clear_trigstrs(self);
	if ((self.spawnflags & BREAK_MOVEDIR))
	{
		dirvec = self.movedir;
	}
	else
	{
		if (!self.activate)
		{
			dirvec = '0 0 1';
		}
		else
		{
			if (self.activate.bsporigin)
			{
				dirorg = bmodel_origin(self.activate);
			}
			else
			{
				dirorg = self.activate.origin;
			}
			dirvec = vectoangles((self.attachment.origin - dirorg));
		}
	}
	while (((self.count > 0) && (self.brkobjqty > 0)))
	{
		content_loop = 4;
		while ((content_loop > 0))
		{
			if ((self.classtype == CT_FUNCBREAK))
			{
				rorg_x = self.oldorigin_x + (random() * self.size_x);
				rorg_y = self.oldorigin_y + (random() * self.size_y);
				rorg_z = self.oldorigin_z + (random() * self.size_z);
			}
			else
			{
				rorg_x = self.origin_x + (crandom() * self.brkvol_x);
				rorg_y = self.origin_y + (crandom() * self.brkvol_y);
				rorg_z = self.origin_z + (crandom() * self.brkvol_z);
			}
			content_flag = pointcontents(rorg);
			if (((content_flag != CONTENT_SOLID) && (content_flag != CONTENT_SKY)))
			{
				content_loop = -1;
			}
			else
			{
				content_loop = content_loop - 1;
			}
		}
		if ((content_loop < 0))
		{
			newmis = spawn();
			newmis.classname = "rubble";
			newmis.classtype = CT_FUNCBREAKOBJ;
			newmis.classgroup = CG_TEMPENT;
			newmis.owner = self;
			newmis.effects = EF_LOWPRECISION;
			self.lip = (random() * self.brkobjqty);
			if ((self.lip < 1))
			{
				setmodel(newmis, self.brkobj1);
			}
			else
			{
				if ((self.lip < 2))
				{
					setmodel(newmis, self.brkobj2);
				}
				else
				{
					if ((self.lip < 3))
					{
						setmodel(newmis, self.brkobj3);
					}
					else
					{
						setmodel(newmis, self.brkobj4);
					}
				}
			}
			setorigin(newmis, rorg);
			setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
			newmis.movetype = MOVETYPE_BOUNCE;
			newmis.solid = SOLID_BBOX;
			if (!(self.spawnflags & BREAK_NOROTATE))
			{
				newmis.angles_y = (random() * 360);
			}
			newmis.avelocity = vecrand(0, self.brkavel, TRUE);
			if (((self.spawnflags & BREAK_MOVEDIR) && (self.movedir_y < 0)))
			{
				crandom();
				newmis.velocity_x = (crandom() * (self.brkveladd_x / 2));
				crandom();
				newmis.velocity_y = (crandom() * (self.brkveladd_y / 2));
				if ((self.movedir_y == -2))
				{
					newmis.velocity_z = (0 - (random() * 50));
				}
				else
				{
					newmis.velocity_z = (self.brkvelbase_z + (random() * self.brkveladd_z));
				}
			}
			else
			{
				makevectors(dirvec);
				gvel = v_forward * (self.brkvelbase_x + (random() * self.brkveladd_x));
				gvel = gvel + (v_right * (crandom() * self.brkveladd_y));
				gvel = gvel + (v_up * (self.brkvelbase_z + (random() * self.brkveladd_z)));
				newmis.velocity = gvel;
			}
			if ((random() < 0.2))
			{
				newmis.count = 2;
			}
			else
			{
				newmis.count = 1;
			}
			newmis.touch = breakable_touch;
			newmis.waitmin = ((time + self.brkfade) + (random() * self.brkfade));
			newmis.nextthink = (time + 0.01);
			newmis.think = breakable_particle;
			newmis.pos1 = self.pos1;
			gvel = vectoangles(newmis.velocity);
			makevectors(gvel);
			newmis.oldorigin = v_forward;
			if (self.brkgravity)
			{
				newmis.gravity = self.brkgravity;
			}
		}
		self.count = (self.count - 1);
	}
	if (self.dmg)
	{
		T_RadiusDamage(self.attachment, self.attachment, self.dmg, self.attachment, DAMAGEALL);
	}
	if ((self.wait != -1))
	{
		self.count = self.height;
	}
	else
	{
		setsize(self, VEC_ORIGIN, VEC_ORIGIN);
		if ((self.spawnflags & BREAK_EXPLOSION))
		{
			if ((self.spawnflags & BREAK_SLIME))
			{
				self.attachment.netname = "slimeball";
				sendParticle("slimesplash_small", self.attachment.origin, VEC_ORIGIN, 1);
			}
			else
			{
				WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
				WriteByte(MSG_BROADCAST, TE_EXPLOSION);
				WriteCoord(MSG_BROADCAST, self.attachment.origin_x);
				WriteCoord(MSG_BROADCAST, self.attachment.origin_y);
				WriteCoord(MSG_BROADCAST, self.attachment.origin_z);
			}
			sound7(self, CHAN_AUTO, "weapons/explodedist.wav", 0.4, 0.4, SNDSPD);
			self.attachment.think = BecomeExplosion;
			self.attachment.nextthink = time;
			entity_hide(self);
		}
	}
};

void() funcbreakable_touch =
{
	if (!(other.flags & FL_MONSTER))
	{
		return;
	}
	if ((other.flags & FL_ONGROUND))
	{
		return;
	}
	if (!self.brktrigjump)
	{
		return;
	}
	self.touch = SUB_Null;
	self.use();
};

void(entity attacker, float damage) funcbreakable_th_pain =
{
	local float loop_count;
	local vector vel, porg;

	if ((damage <= 0))
	{
		return;
	}
	if ((self.classtype == CT_FUNCBREAK))
	{
		porg = bmodel_origin(self);
	}
	else
	{
		porg = self.origin;
	}
	vel = '0 0 -2';
	while ((loop_count < 4))
	{
		particle(porg, (vel * 0.1), (self.bleedcolour + rint((random() * 7))), bound(1, damage, 32));
		loop_count = loop_count + 1;
	}
};

void(entity inflictor, entity attacker, float damage) funcbreakable_pain =
{
	funcbreakable_th_pain(attacker, damage);
};

void() funcbreakable_death =
{
	if ((self.spawnflags & BREAK_NOSHOOT))
	{
		return;
	}
	else
	{
		funcbreakable_use();
	}
};

void() breakable_cache =
{
	if (((self.style > 0) && (self.style < BTYPE_CUSTOM)))
	{
		if (!self.brksound)
		{
			self.brksound = self.style;
		}
		if (!self.brkimpsound)
		{
			self.brkimpsound = self.style;
		}
		if (!self.brkobjects)
		{
			self.brkobjects = (self.style * 10);
		}
	}
	else
	{
		return;
	}
	if (((self.brksound < BTYPE_ROCK) || (self.brksound > BTYPE_CUSTOM)))
	{
		self.brksound = BTYPE_ROCK;
	}
	if (((self.brksound == BTYPE_ROCK) || (self.brksound == BTYPE_BRICK)))
	{
		self.noise = SOUND_BRK_ROCK;
		if (!self.brkvelbase)
		{
			self.brkvelbase = '0 0 50';
		}
		if (!self.brkveladd)
		{
			self.brkveladd = '100 100 100';
		}
	}
	else
	{
		if ((self.brksound == BTYPE_WOOD))
		{
			self.noise = SOUND_BRK_WOOD;
			if (!self.brkvelbase)
			{
				self.brkvelbase = '50 50 50';
			}
			if (!self.brkveladd)
			{
				self.brkveladd = '100 100 50';
			}
		}
		else
		{
			if ((self.brksound == BTYPE_GLASS))
			{
				self.noise = SOUND_BRK_GLASS;
				if (!self.brkvelbase)
				{
					self.brkvelbase = '50 50 50';
				}
				if (!self.brkveladd)
				{
					self.brkveladd = '100 100 150';
				}
			}
			else
			{
				if ((self.brksound == BTYPE_METAL))
				{
					self.noise = SOUND_BRK_METAL;
					if (!self.brkvelbase)
					{
						self.brkvelbase = '50 50 100';
					}
					if (!self.brkveladd)
					{
						self.brkveladd = '100 100 150';
					}
				}
				else
				{
					if ((self.brksound == BTYPE_CERAMIC))
					{
						self.noise = SOUND_BRK_CERAMIC;
						if (!self.brkvelbase)
						{
							self.brkvelbase = '50 50 50';
						}
						if (!self.brkveladd)
						{
							self.brkveladd = '100 100 150';
						}
					}
					else
					{
						if ((self.noise == ""))
						{
							self.noise = SOUND_EMPTY;
							if (!self.brkvelbase)
							{
								self.brkvelbase = '50 50 50';
							}
							if (!self.brkveladd)
							{
								self.brkveladd = '100 100 150';
							}
						}
					}
				}
			}
		}
	}
	precache_sound(self.noise);
	if (((self.brkimpsound < BTYPE_ROCK) || (self.brkimpsound > BTYPE_CUSTOM)))
	{
		self.brkimpsound = BTYPE_ROCK;
	}
	self.brkimpqty = 4;
	if (((self.brkimpsound == BTYPE_ROCK) || (self.brkimpsound == BTYPE_BRICK)))
	{
		if ((self.noise1 == ""))
		{
			self.noise1 = SOUND_IMP_ROCK1;
		}
		if ((self.noise2 == ""))
		{
			self.noise2 = SOUND_IMP_ROCK2;
		}
		if ((self.noise3 == ""))
		{
			self.noise3 = SOUND_IMP_ROCK3;
		}
		if ((self.noise4 == ""))
		{
			self.noise4 = SOUND_IMP_ROCK4;
		}
	}
	else
	{
		if ((self.brkimpsound == BTYPE_WOOD))
		{
			if ((self.noise1 == ""))
			{
				self.noise1 = SOUND_IMP_WOOD1;
			}
			if ((self.noise2 == ""))
			{
				self.noise2 = SOUND_IMP_WOOD2;
			}
			if ((self.noise3 == ""))
			{
				self.noise3 = SOUND_IMP_WOOD3;
			}
			if ((self.noise4 == ""))
			{
				self.noise4 = SOUND_IMP_WOOD4;
			}
		}
		else
		{
			if ((self.brkimpsound == BTYPE_GLASS))
			{
				if ((self.noise1 == ""))
				{
					self.noise1 = SOUND_IMP_GLASS1;
				}
				if ((self.noise2 == ""))
				{
					self.noise2 = SOUND_IMP_GLASS2;
				}
				if ((self.noise3 == ""))
				{
					self.noise3 = SOUND_IMP_GLASS3;
				}
				if ((self.noise4 == ""))
				{
					self.noise4 = SOUND_IMP_GLASS4;
				}
			}
			else
			{
				if ((self.brkimpsound == BTYPE_METAL))
				{
					if ((self.noise1 == ""))
					{
						self.noise1 = SOUND_IMP_METAL1;
					}
					if ((self.noise2 == ""))
					{
						self.noise2 = SOUND_IMP_METAL2;
					}
					if ((self.noise3 == ""))
					{
						self.noise3 = SOUND_IMP_METAL3;
					}
					if ((self.noise4 == ""))
					{
						self.noise4 = SOUND_IMP_METAL4;
					}
				}
				else
				{
					if ((self.brkimpsound == BTYPE_CERAMIC))
					{
						if ((self.noise1 == ""))
						{
							self.noise1 = SOUND_IMP_CERAMIC1;
						}
						if ((self.noise2 == ""))
						{
							self.noise2 = SOUND_IMP_CERAMIC2;
						}
						if ((self.noise3 == ""))
						{
							self.noise3 = SOUND_IMP_CERAMIC3;
						}
						if ((self.noise4 == ""))
						{
							self.noise4 = SOUND_IMP_CERAMIC4;
						}
					}
					else
					{
						if ((self.noise2 != ""))
						{
							if ((self.noise3 != ""))
							{
								if ((self.noise4 != ""))
								{
									self.brkimpqty = 4;
								}
								else
								{
									self.brkimpqty = 3;
								}
							}
							else
							{
								self.brkimpqty = 2;
							}
						}
						else
						{
							self.brkimpqty = 1;
						}
						if (((self.pos1_x + self.pos1_y) == 0))
						{
							self.pos1 = '80 8 1';
						}
						if ((self.noise1 == ""))
						{
							self.noise1 = SOUND_IMP_ROCK1;
						}
						if ((self.noise2 == ""))
						{
							self.noise2 = SOUND_EMPTY;
						}
						if ((self.noise3 == ""))
						{
							self.noise3 = SOUND_EMPTY;
						}
						if ((self.noise4 == ""))
						{
							self.noise4 = SOUND_EMPTY;
						}
					}
				}
			}
		}
	}
	precache_sound(self.noise1);
	precache_sound(self.noise2);
	precache_sound(self.noise3);
	precache_sound(self.noise4);
	if ((self.brkobjects < BMODTYPE_SELF))
	{
		self.brkobjects = BMODTYPE_ROCK1;
	}
	if ((self.brkobj1 == ""))
	{
		self.brkobjqty = 4;
	}
	else
	{
		if ((self.brkobj2 != ""))
		{
			if ((self.brkobj3 != ""))
			{
				if ((self.brkobj4 != ""))
				{
					self.brkobjqty = 4;
				}
				else
				{
					self.brkobjqty = 3;
				}
			}
			else
			{
				self.brkobjqty = 2;
			}
		}
		else
		{
			self.brkobjqty = 1;
		}
	}
	if ((self.brkobjects == BMODTYPE_ROCK1))
	{
		if (((self.pos1_x + self.pos1_y) == 0))
		{
			self.pos1 = '80 8 1';
		}
		if ((self.brkobj1 == ""))
		{
			self.brkobj1 = MODEL_BRK_ROCK1A;
		}
		if ((self.brkobj2 == ""))
		{
			self.brkobj2 = MODEL_BRK_ROCK1B;
		}
		if ((self.brkobj3 == ""))
		{
			self.brkobj3 = MODEL_BRK_ROCK1C;
		}
		if ((self.brkobj4 == ""))
		{
			self.brkobj4 = MODEL_BRK_ROCK1D;
		}
	}
	else
	{
		if ((self.brkobjects == BMODTYPE_ROCK2))
		{
			if (((self.pos1_x + self.pos1_y) == 0))
			{
				self.pos1 = '48 8 1';
			}
			if ((self.brkobj1 == ""))
			{
				self.brkobj1 = MODEL_BRK_ROCK2A;
			}
			if ((self.brkobj2 == ""))
			{
				self.brkobj2 = MODEL_BRK_ROCK2B;
			}
			if ((self.brkobj3 == ""))
			{
				self.brkobj3 = MODEL_BRK_ROCK2C;
			}
			if ((self.brkobj4 == ""))
			{
				self.brkobj4 = MODEL_BRK_ROCK2D;
			}
		}
		else
		{
			if ((self.brkobjects == BMODTYPE_ROCK3))
			{
				if (((self.pos1_x + self.pos1_y) == 0))
				{
					self.pos1 = '20 8 1';
				}
				if ((self.brkobj1 == ""))
				{
					self.brkobj1 = MODEL_BRK_ROCK3A;
				}
				if ((self.brkobj2 == ""))
				{
					self.brkobj2 = MODEL_BRK_ROCK3B;
				}
				if ((self.brkobj3 == ""))
				{
					self.brkobj3 = MODEL_BRK_ROCK3C;
				}
				if ((self.brkobj4 == ""))
				{
					self.brkobj4 = MODEL_BRK_ROCK3D;
				}
			}
			else
			{
				if ((self.brkobjects == BMODTYPE_ROCK4))
				{
					if (((self.pos1_x + self.pos1_y) == 0))
					{
						self.pos1 = '168 8 1';
					}
					if ((self.brkobj1 == ""))
					{
						self.brkobj1 = MODEL_BRK_ROCK4A;
					}
					if ((self.brkobj2 == ""))
					{
						self.brkobj2 = MODEL_BRK_ROCK4B;
					}
					if ((self.brkobj3 == ""))
					{
						self.brkobj3 = MODEL_BRK_ROCK4C;
					}
					if ((self.brkobj4 == ""))
					{
						self.brkobj4 = MODEL_BRK_ROCK4D;
					}
				}
				else
				{
					if ((self.brkobjects == BMODTYPE_ROCK5))
					{
						if (((self.pos1_x + self.pos1_y) == 0))
						{
							self.pos1 = '32 8 1';
						}
						if ((self.brkobj1 == ""))
						{
							self.brkobj1 = MODEL_BRK_ROCK5A;
						}
						if ((self.brkobj2 == ""))
						{
							self.brkobj2 = MODEL_BRK_ROCK5B;
						}
						if ((self.brkobj3 == ""))
						{
							self.brkobj3 = MODEL_BRK_ROCK5C;
						}
						if ((self.brkobj4 == ""))
						{
							self.brkobj4 = MODEL_BRK_ROCK5D;
						}
					}
					else
					{
						if ((self.brkobjects == BMODTYPE_ROCK6))
						{
							if (((self.pos1_x + self.pos1_y) == 0))
							{
								self.pos1 = '1 8 1';
							}
							if ((self.brkobj1 == ""))
							{
								self.brkobj1 = MODEL_BRK_ROCK6A;
							}
							if ((self.brkobj2 == ""))
							{
								self.brkobj2 = MODEL_BRK_ROCK6B;
							}
							if ((self.brkobj3 == ""))
							{
								self.brkobj3 = MODEL_BRK_ROCK6C;
							}
							if ((self.brkobj4 == ""))
							{
								self.brkobj4 = MODEL_BRK_ROCK6D;
							}
						}
						else
						{
							if ((self.brkobjects == BMODTYPE_WOOD1))
							{
								if (((self.pos1_x + self.pos1_y) == 0))
								{
									self.pos1 = '16 8 1';
								}
								if ((self.brkobj1 == ""))
								{
									self.brkobj1 = MODEL_BRK_WOOD1A;
								}
								if ((self.brkobj2 == ""))
								{
									self.brkobj2 = MODEL_BRK_WOOD1B;
								}
								if ((self.brkobj3 == ""))
								{
									self.brkobj3 = MODEL_BRK_WOOD1C;
								}
								if ((self.brkobj4 == ""))
								{
									self.brkobj4 = MODEL_BRK_WOOD1D;
								}
							}
							else
							{
								if ((self.brkobjects == BMODTYPE_WOOD2))
								{
									if (((self.pos1_x + self.pos1_y) == 0))
									{
										self.pos1 = '112 8 1';
									}
									if ((self.brkobj1 == ""))
									{
										self.brkobj1 = MODEL_BRK_WOOD2A;
									}
									if ((self.brkobj2 == ""))
									{
										self.brkobj2 = MODEL_BRK_WOOD2B;
									}
									if ((self.brkobj3 == ""))
									{
										self.brkobj3 = MODEL_BRK_WOOD2C;
									}
									if ((self.brkobj4 == ""))
									{
										self.brkobj4 = MODEL_BRK_WOOD2D;
									}
								}
								else
								{
									if ((self.brkobjects == BMODTYPE_WOOD3))
									{
										if (((self.pos1_x + self.pos1_y) == 0))
										{
											self.pos1 = '80 8 1';
										}
										if ((self.brkobj1 == ""))
										{
											self.brkobj1 = MODEL_BRK_WOOD3A;
										}
										if ((self.brkobj2 == ""))
										{
											self.brkobj2 = MODEL_BRK_WOOD3B;
										}
										if ((self.brkobj3 == ""))
										{
											self.brkobj3 = MODEL_BRK_WOOD3C;
										}
										if ((self.brkobj4 == ""))
										{
											self.brkobj4 = MODEL_BRK_WOOD3D;
										}
									}
									else
									{
										if ((self.brkobjects == BMODTYPE_GLASS1))
										{
											if (((self.pos1_x + self.pos1_y) == 0))
											{
												self.pos1 = '32 8 1';
											}
											if ((self.brkobj1 == ""))
											{
												self.brkobj1 = MODEL_BRK_GLASS1A;
											}
											if ((self.brkobj2 == ""))
											{
												self.brkobj2 = MODEL_BRK_GLASS1B;
											}
											if ((self.brkobj3 == ""))
											{
												self.brkobj3 = MODEL_BRK_GLASS1C;
											}
											if ((self.brkobj4 == ""))
											{
												self.brkobj4 = MODEL_BRK_GLASS1D;
											}
										}
										else
										{
											if ((self.brkobjects == BMODTYPE_GLASS2))
											{
												if (((self.pos1_x + self.pos1_y) == 0))
												{
													self.pos1 = '64 8 1';
												}
												if ((self.brkobj1 == ""))
												{
													self.brkobj1 = MODEL_BRK_GLASS2A;
												}
												if ((self.brkobj2 == ""))
												{
													self.brkobj2 = MODEL_BRK_GLASS2B;
												}
												if ((self.brkobj3 == ""))
												{
													self.brkobj3 = MODEL_BRK_GLASS2C;
												}
												if ((self.brkobj4 == ""))
												{
													self.brkobj4 = MODEL_BRK_GLASS2D;
												}
											}
											else
											{
												if ((self.brkobjects == BMODTYPE_GLASS3))
												{
													if (((self.pos1_x + self.pos1_y) == 0))
													{
														self.pos1 = '96 8 1';
													}
													if ((self.brkobj1 == ""))
													{
														self.brkobj1 = MODEL_BRK_GLASS3A;
													}
													if ((self.brkobj2 == ""))
													{
														self.brkobj2 = MODEL_BRK_GLASS3B;
													}
													if ((self.brkobj3 == ""))
													{
														self.brkobj3 = MODEL_BRK_GLASS3C;
													}
													if ((self.brkobj4 == ""))
													{
														self.brkobj4 = MODEL_BRK_GLASS3D;
													}
												}
												else
												{
													if ((self.brkobjects == BMODTYPE_METAL1))
													{
														if (((self.pos1_x + self.pos1_y) == 0))
														{
															self.pos1 = '16 8 1';
														}
														if ((self.brkobj1 == ""))
														{
															self.brkobj1 = MODEL_BRK_METAL1A;
														}
														if ((self.brkobj2 == ""))
														{
															self.brkobj2 = MODEL_BRK_METAL1B;
														}
														if ((self.brkobj3 == ""))
														{
															self.brkobj3 = MODEL_BRK_METAL1C;
														}
														if ((self.brkobj4 == ""))
														{
															self.brkobj4 = MODEL_BRK_METAL1D;
														}
													}
													else
													{
														if ((self.brkobjects == BMODTYPE_METAL2))
														{
															if (((self.pos1_x + self.pos1_y) == 0))
															{
																self.pos1 = '80 8 1';
															}
															if ((self.brkobj1 == ""))
															{
																self.brkobj1 = MODEL_BRK_METAL2A;
															}
															if ((self.brkobj2 == ""))
															{
																self.brkobj2 = MODEL_BRK_METAL2B;
															}
															if ((self.brkobj3 == ""))
															{
																self.brkobj3 = MODEL_BRK_METAL2C;
															}
															if ((self.brkobj4 == ""))
															{
																self.brkobj4 = MODEL_BRK_METAL2D;
															}
														}
														else
														{
															if ((self.brkobjects == BMODTYPE_METAL3))
															{
																if (((self.pos1_x + self.pos1_y) == 0))
																{
																	self.pos1 = '48 8 1';
																}
																if ((self.brkobj1 == ""))
																{
																	self.brkobj1 = MODEL_BRK_METAL3A;
																}
																if ((self.brkobj2 == ""))
																{
																	self.brkobj2 = MODEL_BRK_METAL3B;
																}
																if ((self.brkobj3 == ""))
																{
																	self.brkobj3 = MODEL_BRK_METAL3C;
																}
																if ((self.brkobj4 == ""))
																{
																	self.brkobj4 = MODEL_BRK_METAL3D;
																}
															}
															else
															{
																if ((self.brkobjects == BMODTYPE_METAL4))
																{
																	if (((self.pos1_x + self.pos1_y) == 0))
																	{
																		self.pos1 = '48 8 1';
																	}
																	if ((self.brkobj1 == ""))
																	{
																		self.brkobj1 = MODEL_BRK_METAL4A;
																	}
																	if ((self.brkobj2 == ""))
																	{
																		self.brkobj2 = MODEL_BRK_METAL4B;
																	}
																	if ((self.brkobj3 == ""))
																	{
																		self.brkobj3 = MODEL_BRK_METAL4C;
																	}
																	if ((self.brkobj4 == ""))
																	{
																		self.brkobj4 = MODEL_BRK_METAL4D;
																	}
																}
																else
																{
																	if ((self.brkobjects == BMODTYPE_METAL5))
																	{
																		if (((self.pos1_x + self.pos1_y) == 0))
																		{
																			self.pos1 = '32 8 1';
																		}
																		if ((self.brkobj1 == ""))
																		{
																			self.brkobj1 = MODEL_BRK_METAL5A;
																		}
																		if ((self.brkobj2 == ""))
																		{
																			self.brkobj2 = MODEL_BRK_METAL5B;
																		}
																		if ((self.brkobj3 == ""))
																		{
																			self.brkobj3 = MODEL_BRK_METAL5C;
																		}
																		if ((self.brkobj4 == ""))
																		{
																			self.brkobj4 = MODEL_BRK_METAL5D;
																		}
																	}
																	else
																	{
																		if ((self.brkobjects == BMODTYPE_BRICK1))
																		{
																			if (((self.pos1_x + self.pos1_y) == 0))
																			{
																				self.pos1 = '16 8 1';
																			}
																			if ((self.brkobj1 == ""))
																			{
																				self.brkobj1 = MODEL_BRK_BRICK1A;
																			}
																			if ((self.brkobj2 == ""))
																			{
																				self.brkobj2 = MODEL_BRK_BRICK1B;
																			}
																			if ((self.brkobj3 == ""))
																			{
																				self.brkobj3 = MODEL_BRK_BRICK1C;
																			}
																			if ((self.brkobj4 == ""))
																			{
																				self.brkobj4 = MODEL_BRK_BRICK1D;
																			}
																		}
																		else
																		{
																			if ((self.brkobjects == BMODTYPE_BRICK2))
																			{
																				if (((self.pos1_x + self.pos1_y) == 0))
																				{
																					self.pos1 = '80 8 1';
																				}
																				if ((self.brkobj1 == ""))
																				{
																					self.brkobj1 = MODEL_BRK_BRICK2A;
																				}
																				if ((self.brkobj2 == ""))
																				{
																					self.brkobj2 = MODEL_BRK_BRICK2B;
																				}
																				if ((self.brkobj3 == ""))
																				{
																					self.brkobj3 = MODEL_BRK_BRICK2C;
																				}
																				if ((self.brkobj4 == ""))
																				{
																					self.brkobj4 = MODEL_BRK_BRICK2D;
																				}
																			}
																			else
																			{
																				if ((self.brkobjects == BMODTYPE_BRICK3))
																				{
																					if (((self.pos1_x + self.pos1_y) == 0))
																					{
																						self.pos1 = '48 8 1';
																					}
																					if ((self.brkobj1 == ""))
																					{
																						self.brkobj1 = MODEL_BRK_BRICK3A;
																					}
																					if ((self.brkobj2 == ""))
																					{
																						self.brkobj2 = MODEL_BRK_BRICK3B;
																					}
																					if ((self.brkobj3 == ""))
																					{
																						self.brkobj3 = MODEL_BRK_BRICK3C;
																					}
																					if ((self.brkobj4 == ""))
																					{
																						self.brkobj4 = MODEL_BRK_BRICK3D;
																					}
																				}
																				else
																				{
																					if ((self.brkobjects == BMODTYPE_BRICK4))
																					{
																						if (((self.pos1_x + self.pos1_y) == 0))
																						{
																							self.pos1 = '0 8 1';
																						}
																						if ((self.brkobj1 == ""))
																						{
																							self.brkobj1 = MODEL_BRK_BRICK4A;
																						}
																						if ((self.brkobj2 == ""))
																						{
																							self.brkobj2 = MODEL_BRK_BRICK4B;
																						}
																						if ((self.brkobj3 == ""))
																						{
																							self.brkobj3 = MODEL_BRK_BRICK4C;
																						}
																						if ((self.brkobj4 == ""))
																						{
																							self.brkobj4 = MODEL_BRK_BRICK4D;
																						}
																					}
																					else
																					{
																						if ((self.brkobjects == BMODTYPE_BRICK5))
																						{
																							if (((self.pos1_x + self.pos1_y) == 0))
																							{
																								self.pos1 = '16 8 1';
																							}
																							if ((self.brkobj1 == ""))
																							{
																								self.brkobj1 = MODEL_BRK_BRICK5A;
																							}
																							if ((self.brkobj2 == ""))
																							{
																								self.brkobj2 = MODEL_BRK_BRICK5B;
																							}
																							if ((self.brkobj3 == ""))
																							{
																								self.brkobj3 = MODEL_BRK_BRICK5C;
																							}
																							if ((self.brkobj4 == ""))
																							{
																								self.brkobj4 = MODEL_BRK_BRICK5D;
																							}
																						}
																						else
																						{
																							if ((self.brkobjects == BMODTYPE_CERAMIC1))
																							{
																								if (((self.pos1_x + self.pos1_y) == 0))
																								{
																									self.pos1 = '96 8 1';
																								}
																								if ((self.brkobj1 == ""))
																								{
																									self.brkobj1 = MODEL_BRK_GLASS3A;
																								}
																								if ((self.brkobj2 == ""))
																								{
																									self.brkobj2 = MODEL_BRK_GLASS3B;
																								}
																								if ((self.brkobj3 == ""))
																								{
																									self.brkobj3 = MODEL_BRK_GLASS3C;
																								}
																								if ((self.brkobj4 == ""))
																								{
																									self.brkobj4 = MODEL_BRK_GLASS3D;
																								}
																							}
																							else
																							{
																								if ((self.brkobj1 == ""))
																								{
																									self.brkobj1 = MODEL_BRK_ROCK1A;
																								}
																								if ((self.brkobj2 == ""))
																								{
																									self.brkobj2 = MODEL_EMPTY;
																								}
																								if ((self.brkobj3 == ""))
																								{
																									self.brkobj3 = MODEL_EMPTY;
																								}
																								if ((self.brkobj4 == ""))
																								{
																									self.brkobj4 = MODEL_EMPTY;
																								}
																							}
																						}
																					}
																				}
																			}
																		}
																	}
																}
															}
														}
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	precache_model(self.brkobj1);
	precache_model(self.brkobj2);
	precache_model(self.brkobj3);
	precache_model(self.brkobj4);
};

void() breakable_defaults =
{

	if ((self.count <= 0))
	{
		self.count = 4;
	}
	if ((self.cnt == 0))
	{
		self.cnt = 4;
	}
	if ((self.cnt < 0))
	{
		self.height = self.count;
	}
	else
	{
		self.height = (self.count + rint((random() * self.cnt)));
	}
	if ((coop && (((self.count == 3) || (self.count == 5)) || (self.count == 7))))
	{
		self.count = 2;
	}
	else
	{
		if ((coop && (self.count <= 1)))
		{
			self.count = self.count;
		}
		else
		{
			if (coop)
			{
				self.count = (self.count / 2);
			}
		}
	}
	self.count = self.height;
	if ((((self.brktrigjump < 0) || (self.brktrigmissile < 0)) || (self.health < 0)))
	{
		self.spawnflags = (self.spawnflags | BREAK_NOSHOOT);
	}
	if ((self.health == 0))
	{
		self.health = 1;
	}
	if ((self.spawnflags & BREAK_DAMAGE))
	{
		if ((self.dmg <= 0))
		{
			self.dmg = 2;
		}
	}
	else
	{
		if ((self.spawnflags & BREAK_EXPLOSION))
		{
			if ((self.dmg <= 0))
			{
				self.dmg = DAMAGE_MONROCKET;
			}
		}
	}
	if (!self.brkvelbase)
	{
		self.brkvelbase = '50 50 100';
	}
	if (!self.brkveladd)
	{
		self.brkveladd = '100 100 150';
	}
	if ((self.brkavel <= 0))
	{
		self.brkavel = 200;
	}
	if ((self.brkfade <= 0))
	{
		self.brkfade = 4;
	}
	if (self.angles_y)
	{
		self.movedir_y = self.angles_y;
		self.spawnflags = (self.spawnflags | BREAK_MOVEDIR);
	}
	self.angles = VEC_ORIGIN;
	self.mangle = VEC_ORIGIN;
	self.avelocity = VEC_ORIGIN;
	self.velocity = VEC_ORIGIN;
	self.delay = 0;
};

void() breakable_on =
{

	self.use = SUB_Null;
	if (self.bsporigin)
	{
		self.solid = SOLID_BSP;
		self.movetype = MOVETYPE_PUSH;
		setmodel(self, self.model);
		setorigin(self, self.origin);
		setsize(self, self.mins, self.maxs);
		self.attachment = spawn();
		self.attachment.origin = bmodel_origin(self);
		setorigin(self.attachment, self.attachment.origin);
	}
	else
	{
		self.solid = SOLID_BBOX;
		self.movetype = 0;
		setmodel(self, self.mdl);
		setorigin(self, self.origin);
		setsize(self, self.bbmins, self.bbmaxs);
		self.angles = self.pos2;
		self.attachment = self;
	}
	if ((self.spawnflags & BREAK_NOSHOOT))
	{
		self.takedamage = 0;
		self.th_pain = SUB_Null_pain;
		self.th_die = SUB_Null;
	}
	else
	{
		self.takedamage = DAMAGE_YES;
		self.th_pain = funcbreakable_th_pain;
		self.th_die = funcbreakable_death;
		self.bleedcolour = self.pos1_x;
		if (self.bsporigin)
		{
			self.oldorigin = bmodel_origin(self);
		}
		else
		{
			self.oldorigin = self.origin;
		}
	}
	self.use = funcbreakable_use;
	if (self.brktrigjump)
	{
		self.touch = funcbreakable_touch;
	}
};

void() func_breakable =
{
	if (((self.style < BTYPE_ROCK) || (self.style > BTYPE_MAX)))
	{
		self.style = BTYPE_ROCK;
	}
	breakable_cache();
	breakable_defaults();
	if (((self.targetname == "") && (self.spawnflags & BREAK_NOSHOOT)))
	{
		dprint("€¬“ÀÕƒÃ› Cannot be triggered or shoot, removed\n");
		setmodel(self, self.model);
		setorigin(self, self.origin);
		setsize(self, self.mins, self.maxs);
		spawn_marker(bmodel_origin(self));
		remove(self);
		return;
	}
	self.classtype = CT_FUNCBREAK;
	self.classgroup = CG_BREAKABLE;
	self.bsporigin = TRUE;
	self.wait = -1;
	if ((self.spawnflags & BREAK_STARTOFF))
	{
		self.use = breakable_on;
	}
	else
	{
		breakable_on();
	}
};

void() func_breakable_spawner =
{
	if (((self.style < BTYPE_ROCK) || (self.style > BTYPE_MAX)))
	{
		self.style = BTYPE_ROCK;
	}
	breakable_cache();
	breakable_defaults();
	if ((self.targetname == ""))
	{
		dprint("€¬“À‘“…«› Missing targetname\n");
		spawn_marker(self.origin);
		remove(self);
		return;
	}
	self.classtype = CT_FUNCBREAKSPN;
	self.classgroup = CG_BREAKABLE;
	self.solid = 0;
	self.movetype = 0;
	if ((self.brkvol_x < 8))
	{
		self.brkvol_x = 8;
	}
	if ((self.brkvol_y < 8))
	{
		self.brkvol_y = 8;
	}
	if ((self.brkvol_z < 8))
	{
		self.brkvol_z = 8;
	}
	self.attachment = self;
	self.use = funcbreakable_use;
};

void() breakable_wall_state =
{
	if ((self.state == STATE_ENABLED))
	{
		if ((self.spawnflags & BREAKWALL_SOLID))
		{
			self.solid = SOLID_BSP;
			self.movetype = MOVETYPE_PUSH;
		}
		else
		{
			self.solid = 0;
			self.movetype = 0;
		}
		setmodel(self, self.mdl);
	}
	else
	{
		self.solid = 0;
		self.movetype = 0;
		self.model = "";
	}
};

void() breakable_wall_use =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	if ((self.attack_finished > time))
	{
		return;
	}
	if ((self.wait < 0))
	{
		self.attack_finished = LARGE_TIMER;
	}
	if ((self.state == STATE_ENABLED))
	{
		self.state = STATE_DISABLED;
	}
	else
	{
		self.state = STATE_ENABLED;
	}
	breakable_wall_state();
	if (((self.spawnflags & BREAKWALL_FADEOUT) && (self.state == STATE_ENABLED)))
	{
		self.nextthink = ((time + self.waitmin) + (random() * self.waitmin));
		self.think = breakable_remove;
		self.movetype = 0;
		self.solid = SOLID_BBOX;
	}
};

void() func_breakable_wall =
{
	self.classtype = CT_FUNCBREAKWALL;
	self.classgroup = CG_BREAKABLE;
	self.bsporigin = TRUE;
	self.angles = VEC_ORIGIN;
	self.mdl = self.model;
	self.solid = SOLID_BSP;
	self.movetype = MOVETYPE_PUSH;
	setmodel(self, self.mdl);
	if ((self.spawnflags & BREAKWALL_FADEOUT))
	{
		self.wait = -1;
	}
	if (!self.waitmin)
	{
		self.waitmin = 4;
	}
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_use = breakable_wall_use;
	self.estate = ESTATE_ON;
	if ((self.spawnflags & BREAKWALL_START_ON))
	{
		self.state = STATE_ENABLED;
	}
	else
	{
		self.state = STATE_DISABLED;
	}
	breakable_wall_state();
};

void() trig_monbreak_delay =
{
	self.owner = find(world, targetname, self.target);
	if ((self.owner.classtype == CT_FUNCBREAK))
	{
		self.owner.activate = self;
		self = self.owner;
		self.use();
	}
};

void() trig_monbreak_use =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	if ((self.attack_finished > time))
	{
		return;
	}
	self.attack_finished = LARGE_TIMER;
	if ((self.enemy.flags & FL_MONSTER))
	{
		if ((self.spawnflags & MONTRIG_WAKEUPANIM))
		{
			self.enemy.wakeuptrigger = TRUE;
		}
		trigger_ent(self.enemy, other);
	}
	if ((self.spawnflags & MONTRIG_NODELAY))
	{
		trig_monbreak_delay();
	}
	else
	{
		self.nextthink = (time + self.wait);
		self.think = trig_monbreak_delay;
	}
};

void() trigger_monsterbreak =
{
	self.classtype = CT_TRIGMONBREAK;
	self.classgroup = CG_BREAKABLE;
	if ((self.wait <= 0))
	{
		self.wait = 0.2;
	}
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_use = trig_monbreak_use;
	self.estate = ESTATE_ON;
};

void() trig_explode_fire =
{
	if ((self.dmg > 0))
	{
		T_RadiusDamage(self, self, self.dmg, self, DAMAGEALL);
	}
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord(MSG_BROADCAST, self.origin_x);
	WriteCoord(MSG_BROADCAST, self.origin_y);
	WriteCoord(MSG_BROADCAST, self.origin_z);
	sound7(self, CHAN_WEAPON, SOUND_REXP3, 1, ATTN_NORM, SNDSPD);
	BecomeExplosion();
};

void() trig_explode_use =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	if ((self.attack_finished > time))
	{
		return;
	}
	self.attack_finished = LARGE_TIMER;
	if (self.delay)
	{
		self.nextthink = (time + self.delay);
		self.think = trig_explode_fire;
	}
	else
	{
		trig_explode_fire();
	}
};

void() trigger_explode =
{
	self.classtype = CT_TRIGEXPLODE;
	if ((self.dmg <= 0))
	{
		self.dmg = DAMAGE_MONROCKET;
	}
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_use = trig_explode_use;
	self.estate = ESTATE_ON;
};

void() misc_breakable_pot1 =
{
	self.classtype = CT_FUNCBREAKMDL;
	self.classgroup = CG_BREAKABLE;
	self.bbmins = VEC_HULL_MIN;
	self.bbmaxs = '16 16 24';
	self.brkvol = '32 32 48';
	self.mdl = "progs/misc_pot1.mdl";
	precache_model(self.mdl);
	self.skin = self.exactskin;
	self.style = BTYPE_CERAMIC;
	self.brkobjects = BMODTYPE_CUSTOM;
	self.brkobj1 = "progs/misc_potshard1.mdl";
	self.brkobj2 = "progs/misc_potshard2.mdl";
	self.brkobj3 = "progs/misc_potshard3.mdl";
	self.brkobj4 = "progs/misc_potshard4.mdl";
	self.pos1 = '16 8 1';
	self.wait = -1;
	self.pos2 = VEC_ORIGIN;
	if ((self.mangle != VEC_ORIGIN))
	{
		self.pos2 = self.mangle;
	}
	else
	{
		if ((query_configflag(SVR_ITEMROTATE) == FALSE))
		{
			self.pos2_y = rint((random() * 359));
		}
	}
	breakable_cache();
	breakable_defaults();
	if ((self.spawnflags & BREAK_STARTOFF))
	{
		self.use = breakable_on;
	}
	else
	{
		breakable_on();
	}
};
