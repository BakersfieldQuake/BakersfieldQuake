//Decompiled code. Please respect the original copyright.

void() head_gib_faceplayer =
{
	self.ideal_yaw = (self.angles * '0 1 0');
	if (!self.yaw_speed)
	{
		self.yaw_speed = 20;
	}
	self.view_ofs = '0 0 25';
	ai_face();
	self.nextthink = (time + 0.05);
	self.think = head_gib_faceplayer;
};

void() gib_gravity_reset =
{
	if ((random() < 0.5))
	{
		self.gravity = 0.9;
	}
	else
	{
		self.gravity = 1.1;
	}
	if ((autocvar_gibsduration == 0))
	{
		return;
	}
	precache_sound("player/gibexplode.wav");
	self.think = gibsfade_blood;
	self.ltime = time;
	self.nextthink = ((time + autocvar_gibsduration) + (random() * 10));
};

void() gib_gravity_reset2 =
{
	if ((random() < 0.5))
	{
		self.gravity = 0.9;
	}
	else
	{
		self.gravity = 1.1;
	}
	if (autocvar_head_gibs_always_face_player)
	{
		self.nextthink = time;
		self.think = head_gib_faceplayer;
	}
};

void() gib_gravity_reset3 =
{
	if ((random() < 0.5))
	{
		self.gravity = 0.9;
	}
	else
	{
		self.gravity = 1.1;
	}
};

void() kick_touch =
{

	if (((self.velocity_x > VEC_ORIGIN_x) && (pointcontents(self.origin) == CONTENT_EMPTY)))
	{
		sound7(other, CHAN_ITEM, "gib/gibhit1.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() kick_touch2 =
{
	local vector v;
	local float zufall;

	if (!(deathmatch || coop))
	{
		if ((pointcontents(self.origin) == CONTENT_LAVA))
		{
			self.traileffectnum = particleeffectnum(/*45791i*/"gibburn");
			self.colormod = '0.4 0.1 0.1';
		}
		if ((pointcontents(self.origin) == CONTENT_SLIME))
		{
			self.traileffectnum = particleeffectnum(/*45799i*/"gibacid");
			self.colormod = '0.3 1.6 0.3';
		}
		if (((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)))
		{
			self.traileffectnum = particleeffectnum(/*25826i*/"gibnull");
		}
		if ((autocvar_gibflies == 1))
		{
			if ((((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)) && (pointcontents(self.origin) != CONTENT_WATER)))
			{
				self.traileffectnum = particleeffectnum(/*45807i*/"gibfliesblack");
			}
		}
		if ((autocvar_gibflies == 2))
		{
			if ((((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)) && (pointcontents(self.origin) != CONTENT_WATER)))
			{
				self.traileffectnum = particleeffectnum(/*45821i*/"gibfliesbrown");
			}
		}
	}
	if ((other.classname != "player"))
	{
		return;
	}
	if ((random() < 0.7))
	{
		sound(other, CHAN_ITEM, "kickgib/gib_hit.wav", 1, ATTN_NORM);
	}
	else
	{
		sound(other, CHAN_ITEM, "kickgib/gib_miss.wav", 1, ATTN_NORM);
	}
	if ((random() < 0.5))
	{
		v_x = other.velocity_x * 1.4;
	}
	else
	{
		v_x = other.velocity_x * 1.5;
	}
	if ((random() < 0.5))
	{
	}
	else
	{
	}
	if (((v_x & (other.velocity_y * 1.5)) == 0))
	{
	}
	else
	{
	}
	zufall = random();
	if ((zufall > 0.66))
	{
		self.gravity = 1.6;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.gravity = 1.7;
		}
		else
		{
			self.gravity = 1.5;
		}
	}
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	self.velocity = v;
	if ((((v_x & (other.velocity_y * 1.5)) & 250) == 0))
	{
		self.avelocity = VEC_ORIGIN;
	}
	else
	{
		self.avelocity = '0 300 0';
	}
	self.cansplash = 1;
	self.think = gib_gravity_reset2;
	self.nextthink = (time + 1.1);
};

void() kick_touch2_temp =
{
	self.origin = (self.origin + '0 0 7');
	droptofloor();
	setsize(self, '-8 -8 0', '8 8 24');
	self.touch = kick_touch2;
	self.think = kick_touch2;
	self.nextthink = (time + 0.5);
};

void() kick_touch3 =
{
	local float zufall;

	if (((time - self.delay) < 0.2))
	{
		return;
	}
	if ((self.velocity_x <= 50))
	{
		if (((self.angles_z >= 80) || (self.angles_z <= -80)))
		{
			self.angles_z = 0;
		}
		if (((self.angles_x >= 80) || (self.angles_x <= -80)))
		{
			self.angles_x = 0;
		}
	}
	if ((self.flags & FL_ONGROUND))
	{
		self.angles_x = 0;
	}
	if ((((other.classname == "player") || (other.classname == "gib")) || (other.flags & FL_MONSTER)))
	{
		return;
	}
	else
	{
		if (((((pointcontents(self.origin) == CONTENT_EMPTY) && (self.velocity_x <= 20)) && (other == world)) && (self.classname != "player")))
		{
			te_blood(self.origin, '0 80 1000', 7);
			if ((random() < 0.4))
			{
				sound7(self, CHAN_BODY, "gib/gibhit1.wav", 1, ATTN_NORM, SNDSPD);
			}
			else
			{
				if ((random() < 0.7))
				{
					sound7(self, CHAN_BODY, "gib/gibhit2.wav", 1, ATTN_NORM, SNDSPD);
				}
				else
				{
					if ((random() < 0.99))
					{
						sound7(self, CHAN_BODY, "gib/gibhit3.wav", 1, ATTN_NORM, SNDSPD);
					}
					else
					{
						sound7(self, CHAN_BODY, "gib/gibhit4.wav", 1, ATTN_NORM, SNDSPD);
					}
				}
			}
		}
	}
	if (!(deathmatch || coop))
	{
		if ((pointcontents(self.origin) == CONTENT_LAVA))
		{
			self.traileffectnum = particleeffectnum(/*45791i*/"gibburn");
			self.colormod = '0.4 0.1 0.1';
		}
		if ((pointcontents(self.origin) == CONTENT_SLIME))
		{
			self.traileffectnum = particleeffectnum(/*45799i*/"gibacid");
			self.colormod = '0.9 1.4 0.4';
		}
		if ((pointcontents(self.origin) == CONTENT_WATER))
		{
			self.traileffectnum = particleeffectnum(/*25826i*/"gibnull");
		}
		if ((((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)) && ((self.traileffectnum != particleeffectnum(/*45835i*/"burning_gib")) && ((self.traileffectnum != particleeffectnum(/*15029i*/"burning_gib_fade")) && ((self.traileffectnum != particleeffectnum(/*15169i*/"charred_gib")) && (self.traileffectnum != particleeffectnum(/*45847i*/"gib_lg")))))))
		{
			self.traileffectnum = particleeffectnum(/*25826i*/"gibnull");
		}
		if ((self.traileffectnum == particleeffectnum(/*45835i*/"burning_gib")))
		{
			self.think = burngib_init;
			self.nextthink = time;
		}
		if ((autocvar_gibflies == 1))
		{
			if ((((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)) && (pointcontents(self.origin) != CONTENT_WATER)))
			{
				self.traileffectnum = particleeffectnum(/*45807i*/"gibfliesblack");
			}
		}
		if ((autocvar_gibflies == 2))
		{
			if ((((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)) && (pointcontents(self.origin) != CONTENT_WATER)))
			{
				self.traileffectnum = particleeffectnum(/*45821i*/"gibfliesbrown");
			}
		}
	}
	zufall = random();
	if ((zufall > 0.66))
	{
		self.gravity = 1.1;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.gravity = 1;
		}
		else
		{
			self.gravity = 0.9;
		}
	}
	self.delay = time;
};

void() kick_touch3_temp =
{
	self.origin = (self.origin + '0 0 7');
	droptofloor();
	setsize(self, '-8 -8 0', '8 8 24');
	self.touch = kick_touch3;
	self.think = kick_touch3;
	self.nextthink = (time + 0.5);
};

void() kick_touch4 =
{
	local vector v;
	local float zufallsound;
	local float zufall;

	if ((other.classname != "player"))
	{
		return;
	}
	zufallsound = random();
	if ((zufallsound > 0.66))
	{
		sound(other, CHAN_ITEM, "kickgib/kick_debris1.wav", 1, ATTN_NORM);
	}
	else
	{
		if ((zufallsound < 0.34))
		{
			sound(other, CHAN_ITEM, "kickgib/kick_debris2.wav", 1, ATTN_NORM);
		}
		else
		{
			sound(other, CHAN_ITEM, "kickgib/kick_debris3.wav", 1, ATTN_NORM);
		}
	}
	if ((random() < 0.5))
	{
		v_x = other.velocity_x * 0.01;
	}
	else
	{
		v_x = other.velocity_x * 0.02;
	}
	if ((random() < 0.5))
	{
	}
	else
	{
	}
	if (((v_x & (other.velocity_y * 0.02)) == 0))
	{
	}
	else
	{
	}
	zufall = random();
	if ((zufall > 0.66))
	{
		self.gravity = 1.6;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.gravity = 1.7;
		}
		else
		{
			self.gravity = 1.5;
		}
	}
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	self.velocity = v;
	if ((((v_x & (other.velocity_y * 0.02)) & 250) == 0))
	{
		self.avelocity = VEC_ORIGIN;
	}
	else
	{
		self.avelocity = '0 300 0';
	}
	self.think = gib_gravity_reset3;
	self.nextthink = (time + 1.1);
};

void() kick_touch5 =
{
	local vector v;
	local float zufall;

	if ((pointcontents(self.origin) == CONTENT_LAVA))
	{
		self.traileffectnum = particleeffectnum(/*45791i*/"gibburn");
		self.colormod = '0.4 0.1 0.1';
	}
	if ((pointcontents(self.origin) == CONTENT_SLIME))
	{
		self.traileffectnum = particleeffectnum(/*45799i*/"gibacid");
		self.colormod = '0.3 1.6 0.3';
	}
	if (((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*25826i*/"gibnull");
	}
	if ((((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)) && (pointcontents(self.origin) != CONTENT_WATER)))
	{
		if (self.skin_type)
		{
			self.traileffectnum = particleeffectnum(/*45854i*/"Afrit_gib_grey");
		}
		else
		{
			self.traileffectnum = particleeffectnum(/*45869i*/"Afrit_gib_red");
		}
	}
	if ((other.classname != "player"))
	{
		return;
	}
	if ((random() < 0.7))
	{
		sound(other, CHAN_ITEM, "kickgib/gib_hit.wav", 1, ATTN_NORM);
	}
	else
	{
		sound(other, CHAN_ITEM, "kickgib/gib_miss.wav", 1, ATTN_NORM);
	}
	if ((random() < 0.5))
	{
		v_x = other.velocity_x * 1.4;
	}
	else
	{
		v_x = other.velocity_x * 1.5;
	}
	if ((random() < 0.5))
	{
	}
	else
	{
	}
	if (((v_x & (other.velocity_y * 1.5)) == 0))
	{
	}
	else
	{
	}
	zufall = random();
	if ((zufall > 0.66))
	{
		self.gravity = 1.6;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.gravity = 1.7;
		}
		else
		{
			self.gravity = 1.5;
		}
	}
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	self.velocity = v;
	if ((((v_x & (other.velocity_y * 1.5)) & 250) == 0))
	{
		self.avelocity = VEC_ORIGIN;
	}
	else
	{
		self.avelocity_x = (crandom() * 300);
		self.avelocity_y = (crandom() * 300);
		self.avelocity_z = (crandom() * 300);
	}
	setsize(self, '-12 -12 0', '12 12 48');
	self.touch = kick_touch5;
	self.cansplash = 1;
	self.think = gib_gravity_reset;
	self.nextthink = (time + 1.1);
};

void() kick_touch5temp =
{
	self.think = kick_touch5;
	self.nextthink = (time + 1);
	self.touch = kick_touch5;
};

void() kick_touch6 =
{
	local float zufall;
	local float gibsfadetime;

	if ((pointcontents(self.origin) == CONTENT_LAVA))
	{
		self.traileffectnum = particleeffectnum(/*45791i*/"gibburn");
		self.colormod = '0.4 0.1 0.1';
	}
	if ((pointcontents(self.origin) == CONTENT_SLIME))
	{
		self.traileffectnum = particleeffectnum(/*45799i*/"gibacid");
		self.colormod = '0.3 1.6 0.3';
	}
	if (((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*25826i*/"gibnull");
	}
	if ((((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)) && (pointcontents(self.origin) != CONTENT_WATER)))
	{
		if (self.skin_type)
		{
			self.traileffectnum = particleeffectnum(/*45854i*/"Afrit_gib_grey");
		}
		else
		{
			self.traileffectnum = particleeffectnum(/*45869i*/"Afrit_gib_red");
		}
	}
	zufall = random();
	if ((zufall > 0.66))
	{
		self.gravity = 1.1;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.gravity = 1;
		}
		else
		{
			self.gravity = 0.9;
		}
	}
	setsize(self, '-12 -12 0', '12 12 48');
	self.touch = kick_touch6;
	if ((autocvar_gibsduration == 0))
	{
		self.nextthink = -1;
	}
	else
	{
		gibsfadetime = autocvar_gibsduration;
		self.think = gibsfade_noblood;
		self.ltime = time;
		self.nextthink = ((time + gibsfadetime) + (random() * 10));
	}
};

void() kick_touch6temp =
{
	self.think = kick_touch6;
	self.nextthink = (time + 1);
};

void() heart_dies =
{
	precache_sound("player/gibexplode.wav");
	self.scale = 1;
	self.gravity = 1;
	self.think = gib_heart_stop_beating;
	self.nextthink = (time + 0.1);
};

void() kick_touch_heart1 =
{
	local vector v;
	local float zufall;

	if ((pointcontents(self.origin) == CONTENT_WATER))
	{
		self.traileffectnum = particleeffectnum(/*45883i*/"gib_heart_nobeating");
		self.think = heart_dies;
		self.nextthink = (time + 0.1);
	}
	if ((pointcontents(self.origin) == CONTENT_LAVA))
	{
		self.traileffectnum = particleeffectnum(/*45791i*/"gibburn");
		self.colormod = '0.4 0.1 0.1';
		self.think = heart_dies;
		self.nextthink = (time + 0.1);
	}
	if ((pointcontents(self.origin) == CONTENT_SLIME))
	{
		self.traileffectnum = particleeffectnum(/*45799i*/"gibacid");
		self.colormod = '0.3 1.6 0.3';
		self.think = heart_dies;
		self.nextthink = (time + 0.1);
	}
	if (((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*45903i*/"gib_heart");
	}
	if ((other.classname != "player"))
	{
		return;
	}
	if ((random() < 0.7))
	{
		sound(other, CHAN_ITEM, "kickgib/gib_hit.wav", 1, ATTN_NORM);
	}
	else
	{
		sound(other, CHAN_ITEM, "kickgib/gib_miss.wav", 1, ATTN_NORM);
	}
	if ((random() < 0.5))
	{
		v_x = other.velocity_x * 1.4;
	}
	else
	{
		v_x = other.velocity_x * 1.5;
	}
	if ((random() < 0.5))
	{
	}
	else
	{
	}
	if (((v_x & (other.velocity_y * 1.5)) == 0))
	{
	}
	else
	{
	}
	zufall = random();
	if ((zufall > 0.66))
	{
		self.gravity = 1.6;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.gravity = 1.7;
		}
		else
		{
			self.gravity = 1.5;
		}
	}
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	self.velocity = v;
	if ((((v_x & (other.velocity_y * 1.5)) & 250) == 0))
	{
		self.avelocity = VEC_ORIGIN;
	}
	else
	{
		self.avelocity = '0 300 0';
	}
};

void() kick_touch_heart2 =
{
	local float zufall;

	if ((pointcontents(self.origin) == CONTENT_WATER))
	{
		self.traileffectnum = particleeffectnum(/*45883i*/"gib_heart_nobeating");
		self.think = heart_dies;
		self.nextthink = (time + 0.1);
	}
	if ((pointcontents(self.origin) == CONTENT_LAVA))
	{
		self.traileffectnum = particleeffectnum(/*45791i*/"gibburn");
		self.colormod = '0.4 0.1 0.1';
		self.think = heart_dies;
		self.nextthink = (time + 0.1);
	}
	if ((pointcontents(self.origin) == CONTENT_SLIME))
	{
		self.traileffectnum = particleeffectnum(/*45799i*/"gibacid");
		self.colormod = '0.3 1.6 0.3';
		self.think = heart_dies;
		self.nextthink = (time + 0.1);
	}
	if (((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*45903i*/"gib_heart");
	}
	zufall = random();
	if ((zufall > 0.66))
	{
		self.gravity = 1.1;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.gravity = 1;
		}
		else
		{
			self.gravity = 0.9;
		}
	}
};

void() kick_touch_heart1_nobeating =
{
	local vector v;
	local float zufall;

	if ((pointcontents(self.origin) == CONTENT_WATER))
	{
		self.traileffectnum = particleeffectnum(/*45883i*/"gib_heart_nobeating");
		heart_dies();
	}
	if ((pointcontents(self.origin) == CONTENT_LAVA))
	{
		self.traileffectnum = particleeffectnum(/*45791i*/"gibburn");
		self.colormod = '0.4 0.1 0.1';
		heart_dies();
	}
	if ((pointcontents(self.origin) == CONTENT_SLIME))
	{
		self.traileffectnum = particleeffectnum(/*45799i*/"gibacid");
		self.colormod = '0.3 1.6 0.3';
		heart_dies();
	}
	if (((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*45883i*/"gib_heart_nobeating");
	}
	if ((other.classname != "player"))
	{
		return;
	}
	if ((random() < 0.7))
	{
		sound(other, CHAN_ITEM, "kickgib/gib_hit.wav", 1, ATTN_NORM);
	}
	else
	{
		sound(other, CHAN_ITEM, "kickgib/gib_miss.wav", 1, ATTN_NORM);
	}
	if ((random() < 0.5))
	{
		v_x = other.velocity_x * 1.4;
	}
	else
	{
		v_x = other.velocity_x * 1.5;
	}
	if ((random() < 0.5))
	{
	}
	else
	{
	}
	if (((v_x & (other.velocity_y * 1.5)) == 0))
	{
	}
	else
	{
	}
	zufall = random();
	if ((zufall > 0.66))
	{
		self.gravity = 1.6;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.gravity = 1.7;
		}
		else
		{
			self.gravity = 1.5;
		}
	}
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	self.velocity = v;
	if ((((v_x & (other.velocity_y * 1.5)) & 250) == 0))
	{
		self.avelocity = VEC_ORIGIN;
	}
	else
	{
		self.avelocity = '0 300 0';
	}
};

void() kick_touch_heart2_nobeating =
{
	local float zufall;

	if ((pointcontents(self.origin) == CONTENT_WATER))
	{
		self.traileffectnum = particleeffectnum(/*45883i*/"gib_heart_nobeating");
		heart_dies();
	}
	if ((pointcontents(self.origin) == CONTENT_LAVA))
	{
		self.traileffectnum = particleeffectnum(/*45791i*/"gibburn");
		self.colormod = '0.4 0.1 0.1';
		heart_dies();
	}
	if ((pointcontents(self.origin) == CONTENT_SLIME))
	{
		self.traileffectnum = particleeffectnum(/*45799i*/"gibacid");
		self.colormod = '0.3 1.6 0.3';
		heart_dies();
	}
	if (((pointcontents(self.origin) != CONTENT_SLIME) && (pointcontents(self.origin) != CONTENT_LAVA)))
	{
		self.traileffectnum = particleeffectnum(/*45883i*/"gib_heart_nobeating");
	}
	zufall = random();
	if ((zufall > 0.66))
	{
		self.gravity = 1.1;
	}
	else
	{
		if ((zufall < 0.34))
		{
			self.gravity = 1;
		}
		else
		{
			self.gravity = 0.9;
		}
	}
};
