//Decompiled code. Please respect the original copyright.

void() lg_shock =
{
	sound7(self, CHAN_WEAPON, "weapons/lhit.wav", 0.7, ATTN_IDLE, SNDSPD);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING2);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, (self.origin_x + ((random() * 20) + -10)));
	WriteCoord(MSG_BROADCAST, (self.origin_y + ((random() * 20) + -10)));
	WriteCoord(MSG_BROADCAST, (self.origin_z + ((random() * 20) + -10)));
	WriteCoord(MSG_BROADCAST, (self.origin_x + ((random() * 20) + -10)));
	WriteCoord(MSG_BROADCAST, (self.origin_y + ((random() * 20) + -10)));
	WriteCoord(MSG_BROADCAST, (self.origin_z + ((random() * 20) + -10)));
};

void() lg_shock_player =
{
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING2);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, (self.origin_x + ((random() * 10) + -5)));
	WriteCoord(MSG_BROADCAST, (self.origin_y + ((random() * 10) + -5)));
	WriteCoord(MSG_BROADCAST, (self.origin_z + ((random() * 10) + -5)));
	WriteCoord(MSG_BROADCAST, (self.origin_x + ((random() * 10) + -5)));
	WriteCoord(MSG_BROADCAST, (self.origin_y + ((random() * 10) + -5)));
	WriteCoord(MSG_BROADCAST, (self.origin_z + ((random() * 10) + -5)));
};

void() shocked_explode =
{
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	sound7(self, CHAN_AUTO, "ambience/coaled_monster_explode.wav", 1, ATTN_NORM, SNDSPD);
	remove(self);
};

void() lg_death1 =
{

	self.shocked = (self.shocked + 1);
	if ((self.shocked < 2))
	{
		self.colormod = '0.2 0.2 0.2';
		if ((self.classname != "monster_shambler"))
		{
			self.solid = 0;
		}
		if ((((random() < 0.275) && !(self.flags & FL_INWATER)) && (self.classname != "monster_shambler")))
		{
			self.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
		}
		else
		{
			random();
			if ((random() > (0.4 + (self.health_initial * 0.001))))
			{
				self.shocked = 20;
			}
			else
			{
				if ((((self.enemy.super_time > 0) && (random() < 0.8)) || (random() < 0.1)))
				{
					self.shocked = 28;
				}
				else
				{
					self.traileffectnum = particleeffectnum(/*12483i*/"corpse_charred");
				}
			}
		}
		if (((random() * 100) < 40))
		{
			lg_shock();
		}
	}
	if (((self.classname == "monster_afrit") && (self.colormod != '0.2 0.2 0.2')))
	{
		self.velocity = VEC_ORIGIN;
	}
	if (((self.classname == "monster_army") || (self.classname == "monster_afrit")))
	{
		self.frame = (self.frame + 1);
		if (((random() * 100) < 40))
		{
			lg_shock();
		}
		if ((self.frame <= 43))
		{
			if (((random() * 100) < 20))
			{
				Part_Emitter(self, "progs/s_smoke_muzz.spr", ((random() * 0.5) + 0.3), '5 5 -8', '0 0 10', VEC_ORIGIN, 0.8);
			}
			if (self.noise)
			{
				sound7(self, CHAN_VOICE, self.noise, 1, ATTN_NORM, SNDSPD);
			}
			lg_shock();
			self.frame = 43;
		}
		else
		{
			if ((self.frame >= 46))
			{
				if (((random() * 100) < 20))
				{
					Part_Emitter(self, "progs/s_smoke_muzz.spr", ((random() * 0.5) + 0.3), '5 5 -8', '0 0 10', VEC_ORIGIN, 0.8);
				}
				if (((random() * 100) > 50))
				{
					lg_shock();
					self.frame = 44;
				}
				else
				{
					self.frame = 43;
				}
				lg_shock();
			}
		}
	}
	else
	{
		if ((self.classname == "monster_ogre"))
		{
			self.frame = (self.frame + 1);
			if (((random() * 100) < 40))
			{
				lg_shock();
			}
			if ((self.frame <= 67))
			{
				if (((random() * 100) < 20))
				{
					Part_Emitter(self, "progs/s_smoke_muzz.spr", ((random() * 0.5) + 0.3), '5 5 -8', '0 0 10', VEC_ORIGIN, 0.8);
				}
				if (self.noise)
				{
					sound7(self, CHAN_VOICE, self.noise, 1, ATTN_NORM, SNDSPD);
				}
				lg_shock();
				self.frame = 67;
			}
			else
			{
				if ((self.frame >= 72))
				{
					if (((random() * 100) < 20))
					{
						Part_Emitter(self, "progs/s_smoke_muzz.spr", ((random() * 0.5) + 0.3), '5 5 -8', '0 0 10', VEC_ORIGIN, 0.8);
					}
					if (((random() * 100) > 50))
					{
						lg_shock();
						self.frame = 69;
					}
					else
					{
						self.frame = 67;
					}
					lg_shock();
				}
			}
		}
		else
		{
			if ((self.frame <= 1))
			{
				Part_Emitter(self, "progs/s_smoke_muzz.spr", ((random() * 0.5) + 0.3), '5 5 -8', '0 0 10', VEC_ORIGIN, 0.8);
				self.angles_y = (self.angles_y + 13);
				self.frame = ((random() * 1) + 8);
				lg_shock();
			}
			else
			{
				self.angles_y = (self.angles_y - 13);
				self.frame = ((random() * 1) + 0);
			}
		}
	}
	if (((self.shocked > 10) && (random() < 0.03)))
	{
		if ((self.flags & FL_FLY))
		{
			self.flags = (self.flags - FL_FLY);
		}
	}
	if ((self.shocked >= (20 + (random() * 8))))
	{
		if (((self.classname == "monster_zombie") || (self.classname == "monster_zombiek")))
		{
			if ((self.traileffectnum == particleeffectnum(/*23479i*/"burning_monster")))
			{
				self.health = -61;
			}
			else
			{
				if ((random() < 0.25))
				{
					self.health = -20;
				}
				else
				{
					self.health = -61;
				}
			}
		}
		else
		{
			if ((((self.traileffectnum == particleeffectnum(/*23479i*/"burning_monster")) || (random() < 0.3)) || (self.enemy.super_time && (random() < 0.5))))
			{
				self.health = (-41 - (self.health_initial * 0.15));
			}
			else
			{
				self.health = -20;
			}
		}
		if ((self.traileffectnum == particleeffectnum(/*23479i*/"burning_monster")))
		{
			self.shocked = 100;
		}
		self.frame = 0;
		self.think = self.th_die;
		if (((self.classname != "monster_tarbaby") && (self.classname != "Monster_Zombie")))
		{
			if (((self.health != -20) || (random() < 0.5)))
			{
				if ((self.health == -20))
				{
					sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_NORM, SNDSPD);
				}
				pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				sendParticle("blood_spurt", (self.origin - VEC_ORIGIN), VEC_ORIGIN, 1);
				sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
			}
			if (((random() < 0.1) && (self.health_initial < 450)))
			{
				pointparticles(particleeffectnum(/*46127i*/"shambler_ball"), self.origin, VEC_ORIGIN, 1);
				if ((self.classname != "monster_dog"))
				{
					particleeffectnum(/*46127i*/"shambler_ball");
					pointparticles(particleeffectnum(/*46127i*/"shambler_ball"), (self.origin + '0 0 12'), VEC_ORIGIN, 1);
					particleeffectnum(/*46127i*/"shambler_ball");
					pointparticles(particleeffectnum(/*46127i*/"shambler_ball"), (self.origin + '0 0 -12'), VEC_ORIGIN, 1);
				}
			}
		}
		self.nextthink = (time + (random() * 0.1));
	}
	else
	{
		self.think = lg_death1;
		if (((self.classname != "monster_army") && (self.classname != "monster_ogre")))
		{
			self.nextthink = (time + 0.07);
		}
		else
		{
			self.nextthink = (time + 0.055);
		}
	}
};
