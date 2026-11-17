//Decompiled code. Please respect the original copyright.

void() storm_reset =
{
	lightstyle(self.style, "a");
	if ((self.cnt == 2))
	{
		self.count = 0;
	}
	IS_FLASHING = 0;
	if ((!(self.spawnflags & NO_SOUND) && (self.cnt >= 3)))
	{
		if (((random() * 100) > 90))
		{
			sound7(self, CHAN_ITEM, "ambience/thunder3.wav", 1, ATTN_NONE, SNDSPD);
		}
		else
		{
			if (((random() * 100) > 65))
			{
				sound7(self, CHAN_ITEM, "ambience/thunder2.wav", 1, ATTN_NONE, SNDSPD);
			}
			else
			{
				if (((random() * 100) > 35))
				{
					sound7(self, CHAN_ITEM, "ambience/thunder1.wav", 1, ATTN_NONE, SNDSPD);
				}
			}
		}
	}
	self.think = storm_start;
	self.nextthink = (time + ((random() * 14) + 17));
};

void() storm_start =
{
	if ((self.cnt >= 1))
	{
		lightstyle(self.style, "nbn");
		IS_FLASHING = 1;
	}
	self.cnt = (self.cnt + 1);
	self.think = storm_reset;
	self.nextthink = (time + 0.7);
};

void() light_storm =
{
	precache_sound("ambience/thunder1.wav");
	precache_sound("ambience/thunder2.wav");
	precache_sound("ambience/thunder3.wav");
	IS_FLASHING = 0;
	self.count = 2;
	self.think = storm_start;
	lightstyle(self.style, "a");
	self.nextthink = (time + 6);
};

void() trigger_stormflash =
{
	remove(self);
};
