//Decompiled code. Please respect the original copyright.

void() flash_update =
{
	local entity y;
	local vector middle;

	// The light goes away by itself when its owner dies, leaves, or the flashlight type changes. The owner's
	// flash_flag has to go off with it: otherwise the next press takes the "off" branch and sets think = SUB_Remove
	// on a freed edict, which by then can be another entity (a rocket, an item) and removes that instead.
	if ((autocvar_flashlight_type == 2) || (self.owner.deadflag != DEAD_NO) || intermission_running
		|| (self.owner.classname != "player") || ((self.owner.flash != self) && (self.owner.flash2 != self)))
	{
		if ((self.owner.flash == self) || (self.owner.flash2 == self))
		{
			self.owner.flash_flag = 0;
			if (self.owner.flash == self)
				self.owner.flash = world;
			if (self.owner.flash2 == self)
				self.owner.flash2 = world;
		}
		remove(self);
		return;
	}
	else
	{
		self.pflags = PFLAGS_FULLDYNAMIC;
		self.light_lev = autocvar_flashlight_radius;
		self.color_x = autocvar_flashlight_color_brightness_red;
		self.color_y = autocvar_flashlight_color_brightness_green;
		self.color_z = autocvar_flashlight_color_brightness_blue;
	}
	makevectors(self.owner.v_angle);
	traceline(self.owner.origin, (self.owner.origin + (v_forward * 384)), FALSE, self);
	middle = ((self.owner.origin + trace_endpos) + '0 0 22') * 0.5;
	if ((self.classname == "flash"))
	{
		setorigin(self, ((trace_endpos + '0 0 22') + (v_forward * -5)));
		y = find(world, flashtarg, "yes");
		while (y)
		{
			if (((y.flags & FL_ITEM) && (y.model != string_null)))
			{
				if ((y.solid != SOLID_BBOX))
				{
					y.solid = SOLID_BBOX;
					setmodel(y, y.model);
				}
			}
			y = find(y, flashtarg, "yes");
		}
		y = find(world, flashtarg, "yes");
		while (y)
		{
			if (((y.flags & FL_ITEM) && (y.model != string_null)))
			{
				if ((y.solid != SOLID_TRIGGER))
				{
					y.solid = SOLID_TRIGGER;
					setmodel(y, y.model);
				}
			}
			y = find(y, flashtarg, "yes");
		}
	}
	else
	{
		if ((self.classname == "flash2"))
		{
			setorigin(self, middle);
		}
	}
	self.nextthink = (time + 0.01);
};

void() flash_on =
{
	local entity myflash;
	local entity myflash2;
	local vector middle;

	makevectors(self.v_angle);
	myflash = spawn();
	myflash.movetype = 0;
	myflash.solid = 0;
	setmodel(myflash, "progs/null.spr");
	setsize(myflash, VEC_ORIGIN, VEC_ORIGIN);
	myflash.owner = self;
	self.flash = myflash;
	myflash.classname = "flash";
	myflash.think = flash_update;
	myflash.nextthink = (time + 0.01);
	middle = (self.owner.origin + trace_endpos) * 0.5;
	myflash2 = spawn();
	myflash2.movetype = 0;
	myflash2.solid = 0;
	setmodel(myflash2, "progs/null.spr");
	setsize(myflash2, VEC_ORIGIN, VEC_ORIGIN);
	myflash2.owner = self;
	self.flash2 = myflash2;
	myflash2.classname = "flash2";
	setorigin(myflash2, middle);
	myflash2.think = flash_update;
	myflash2.nextthink = (time + 0.01);
};

void() flash_toggle =
{
	if ((self.flash_flag == FALSE))
	{
		sound(self, CHAN_AUTO, "player/click.wav", 0.5, ATTN_NORM);
		sprint(self, "Flashlight: ON\n");
		self.flash_flag = TRUE;
		flash_on();
	}
	else
	{
		sound(self, CHAN_AUTO, "player/click.wav", 0.5, ATTN_NORM);
		sprint(self, "Flashlight: OFF\n");
		self.flash_flag = 0;
		if (self.flash && (self.flash.owner == self) && (self.flash.classname == "flash"))
			remove(self.flash);
		if (self.flash2 && (self.flash2.owner == self) && (self.flash2.classname == "flash2"))
			remove(self.flash2);
		self.flash = world;
		self.flash2 = world;
	}
};
