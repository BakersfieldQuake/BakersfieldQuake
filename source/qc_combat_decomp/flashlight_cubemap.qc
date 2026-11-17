//Decompiled code. Please respect the original copyright.

void() flash_update_cubemap =
{
	if ((autocvar_flashlight_type == 1))
	{
		remove(self);
		return;
	}
	if (((self.owner.deadflag != DEAD_NO) || intermission_running))
	{
		remove(self);
		return;
	}
	makevectors(self.owner.v_angle);
	traceline(self.owner.origin, (self.owner.origin + (v_forward * 10)), FALSE, self);
	setorigin(self, ((trace_endpos + '0 0 22') + (v_forward * 7)));
	self.angles_x = (self.owner.v_angle_x - 180);
	self.angles_y = self.owner.v_angle_y;
	self.angles_z = self.owner.angles_z;
	self.pflags = PFLAGS_FULLDYNAMIC;
	self.light_lev = 760;
	self.color_x = (1.8 * (autocvar_berserkmode * 0.8));
	self.color_y = 1.7;
	self.color_z = 1.7;
	self.skin = 238;
	self.nextthink = (time + 0.01);
};

void() flash_on_cubemap =
{
	local entity myflash;

	myflash = spawn();
	myflash.movetype = 0;
	myflash.solid = 0;
	setmodel(myflash, "progs/null.spr");
	setsize(myflash, VEC_ORIGIN, VEC_ORIGIN);
	myflash.owner = self;
	self.flash = myflash;
	myflash.classname = "flash_cubemap";
	makevectors(self.v_angle);
	traceline(self.origin, (self.origin + (v_forward * 10)), FALSE, self);
	setorigin(myflash, trace_endpos);
	myflash.think = flash_update_cubemap;
	myflash.nextthink = (time + 0.01);
};

void() flash_toggle_cubemap =
{
	if ((self.flash_flag == FALSE))
	{
		sound(self, CHAN_AUTO, "player/click.wav", 0.5, ATTN_NORM);
		sprint(self, "Flashlight: ON\n");
		self.flash_flag = TRUE;
		flash_on_cubemap();
	}
	else
	{
		sound(self, CHAN_AUTO, "player/click.wav", 0.5, ATTN_NORM);
		sprint(self, "Flashlight: OFF\n");
		self.flash_flag = 0;
		self.flash.think = SUB_Remove;
		self.flash.nextthink = (time + 0.1);
	}
};
