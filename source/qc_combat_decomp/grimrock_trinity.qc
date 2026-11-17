//Decompiled code. Please respect the original copyright.

void() zdisapear =
{
	self.frame = self.owner.frame;
	if ((self.alpha < 0))
	{
		remove(self);
	}
	else
	{
		if ((self.alpha < 0.1))
		{
			self.skin = 4;
		}
		self.alpha = (self.alpha - 0.01);
		self.nextthink = (time + 0.01);
	}
};

void() zbburn =
{
	if ((self.alpha > 1))
	{
		self.nextthink = (time + 0.01);
		self.think = zdisapear;
		self.frame = self.owner.frame;
	}
	else
	{
		makevectors(self.owner.angles);
		traceline(self.owner.origin, self.owner.origin, FALSE, self);
		setorigin(self, trace_endpos);
		self.nextthink = (time + 0.01);
		self.think = zbburn;
		self.frame = self.owner.frame;
		self.skin = 3;
		self.scale = 1;
		self.angles = self.owner.angles;
		self.owner.alpha = (self.owner.alpha - 0.03);
		self.alpha = (self.alpha + 0.03);
	}
};

void() zburna =
{
	local entity myburn;

	myburn = spawn();
	myburn.movetype = 0;
	myburn.solid = 0;
	setmodel(myburn, "progs/zombie.mdl");
	setsize(myburn, VEC_ORIGIN, VEC_ORIGIN);
	myburn.owner = self;
	self.burny = myburn;
	myburn.classname = "flash";
	makevectors(self.v_angle);
	traceline(self.origin, self.origin, FALSE, self);
	setorigin(myburn, trace_endpos);
	myburn.alpha = -0.01;
	myburn.think = zbburn;
	myburn.nextthink = (time + 0.005);
};

void() bburnb =
{
	if ((self.burn_origin < -10))
	{
		self.think = SUB_Remove;
		self.nextthink = (time + 0.02);
	}
	if ((self.burn_origin >= 10))
	{
		if ((self.burn_origin < -6))
		{
			self.owner.skin = 2;
		}
		pointparticles(particleeffectnum(/*51693i*/"burningzombie"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51693i*/"burningzombie"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51707i*/"grimrock_zombie"), self.origin, VEC_ORIGIN, 1);
		makevectors(self.owner.angles);
		traceline(self.owner.origin, self.owner.origin, FALSE, self);
		setorigin(self, (trace_endpos + (v_up * (-5 + self.owner.burnz_origin))));
		self.nextthink = (time + 0.02);
		self.burn_origin = (self.burn_origin - 0.4);
		self.think = bburnb;
	}
};

void() burnb =
{
	local entity myburn;

	myburn = spawn();
	myburn.movetype = 0;
	myburn.solid = 0;
	setsize(myburn, VEC_ORIGIN, VEC_ORIGIN);
	myburn.owner = self;
	self.burny = myburn;
	myburn.classname = "flash";
	makevectors(self.v_angle);
	traceline(self.origin, self.origin, FALSE, self);
	setorigin(myburn, trace_endpos);
	myburn.think = bburnb;
	myburn.nextthink = (time + 0.005);
};

void() bburnc =
{
	if ((self.burn_origin > 10))
	{
		self.think = SUB_Remove;
		self.nextthink = (time + 0.02);
	}
	if ((self.burn_origin <= 4))
	{
		if ((self.burn_color == 1))
		{
			pointparticles(particleeffectnum(/*51723i*/"grimrock_zombie_a"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*51741i*/"grimrock_zombie_b"), self.origin, VEC_ORIGIN, 1);
		}
		pointparticles(particleeffectnum(/*51759i*/"grimrock_zombie1"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51693i*/"burningzombie"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51693i*/"burningzombie"), self.origin, VEC_ORIGIN, 1);
		makevectors(self.owner.angles);
		traceline(self.owner.origin, self.owner.origin, FALSE, self);
		setorigin(self, (trace_endpos + (v_up * (-5 + (self.owner.burnz_origin + self.burn_origin)))));
		self.nextthink = (time + 0.02);
		self.think = bburnc;
		self.burn_origin = (self.burn_origin + 0.4);
	}
	if (((self.burn_origin <= 10) && (self.burn_origin > 4)))
	{
		if ((self.burn_origin > 6))
		{
			self.owner.skin = 2;
		}
		if ((self.burn_color == 1))
		{
			pointparticles(particleeffectnum(/*51723i*/"grimrock_zombie_a"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*51741i*/"grimrock_zombie_b"), self.origin, VEC_ORIGIN, 1);
		}
		pointparticles(particleeffectnum(/*51776i*/"grimrock_zombie2"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51693i*/"burningzombie"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51693i*/"burningzombie"), self.origin, VEC_ORIGIN, 1);
		makevectors(self.owner.angles);
		traceline(self.owner.origin, self.owner.origin, FALSE, self);
		setorigin(self, (trace_endpos + (v_up * (-5 + (self.owner.burnz_origin + self.burn_origin)))));
		self.nextthink = (time + 0.02);
		self.think = bburnc;
		self.burn_origin = (self.burn_origin + 0.4);
	}
};

void() burnc =
{
	local entity myburn;
	local float zufall;

	myburn = spawn();
	myburn.movetype = 0;
	myburn.solid = 0;
	setsize(myburn, VEC_ORIGIN, VEC_ORIGIN);
	myburn.owner = self;
	self.burny = myburn;
	myburn.classname = "flash";
	self.alpha = 1;
	makevectors(self.v_angle);
	traceline(self.origin, self.origin, FALSE, self);
	setorigin(myburn, trace_endpos);
	zufall = random();
	if ((zufall > 0.37))
	{
		myburn.burn_color = 1;
	}
	else
	{
		myburn.burn_color = 2;
	}
	myburn.think = bburnc;
	myburn.nextthink = (time + 0.005);
};

void() burn_toggle =
{
	if ((self.burn_flag == FALSE))
	{
		self.burn_flag = TRUE;
		burnb();
		burnc();
		zburna();
	}
};

void() zdisapeard =
{
	self.frame = self.owner.frame;
	if ((self.alpha < 0))
	{
		remove(self);
	}
	else
	{
		self.alpha = (self.alpha - 0.01);
		self.nextthink = (time + 0.01);
	}
};

void() zbburnd =
{
	if ((self.alpha > 1))
	{
		self.nextthink = (time + 0.01);
		self.think = zdisapeard;
		self.frame = self.owner.frame;
	}
	else
	{
		makevectors(self.owner.angles);
		traceline(self.owner.origin, self.owner.origin, FALSE, self);
		setorigin(self, trace_endpos);
		self.nextthink = (time + 0.01);
		self.think = zbburnd;
		self.frame = self.owner.frame;
		self.scale = 1;
		self.angles = self.owner.angles;
		self.owner.alpha = (self.owner.alpha - 0.025);
		self.alpha = (self.alpha + 0.025);
	}
};

void() zburnd =
{
	local entity myburn;

	myburn = spawn();
	myburn.movetype = 0;
	myburn.solid = 0;
	setsize(myburn, VEC_ORIGIN, VEC_ORIGIN);
	myburn.owner = self;
	self.burny = myburn;
	myburn.classname = "flash";
	makevectors(self.v_angle);
	traceline(self.origin, self.origin, FALSE, self);
	setorigin(myburn, trace_endpos);
	myburn.alpha = -0.01;
	myburn.think = zbburnd;
	myburn.nextthink = (time + 0.005);
};

void() bburnd =
{
	if ((self.burn_origin > 10))
	{
		self.think = SUB_Remove;
		self.nextthink = (time + 0.02);
	}
	if ((self.burn_origin <= 4))
	{
		if ((self.burn_color == 1))
		{
			pointparticles(particleeffectnum(/*51723i*/"grimrock_zombie_a"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			if ((self.burn_color == 2))
			{
				pointparticles(particleeffectnum(/*51741i*/"grimrock_zombie_b"), self.origin, VEC_ORIGIN, 1);
			}
			else
			{
				pointparticles(particleeffectnum(/*51793i*/"grimrock_zombie_c"), self.origin, VEC_ORIGIN, 1);
			}
		}
		pointparticles(particleeffectnum(/*51759i*/"grimrock_zombie1"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51693i*/"burningzombie"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51693i*/"burningzombie"), self.origin, VEC_ORIGIN, 1);
		makevectors(self.owner.angles);
		traceline(self.owner.origin, self.owner.origin, FALSE, self);
		setorigin(self, (trace_endpos + (v_up * (-5 + (self.owner.burnz_origin + self.burn_origin)))));
		self.nextthink = (time + 0.02);
		self.think = bburnd;
		self.burn_origin = (self.burn_origin + 0.4);
	}
	if (((self.burn_origin <= 10) && (self.burn_origin > 4)))
	{
		if ((self.burn_color == 1))
		{
			pointparticles(particleeffectnum(/*51723i*/"grimrock_zombie_a"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			if ((self.burn_color == 2))
			{
				pointparticles(particleeffectnum(/*51741i*/"grimrock_zombie_b"), self.origin, VEC_ORIGIN, 1);
			}
			else
			{
				pointparticles(particleeffectnum(/*51793i*/"grimrock_zombie_c"), self.origin, VEC_ORIGIN, 1);
			}
		}
		pointparticles(particleeffectnum(/*51776i*/"grimrock_zombie2"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51693i*/"burningzombie"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51693i*/"burningzombie"), self.origin, VEC_ORIGIN, 1);
		makevectors(self.owner.angles);
		traceline(self.owner.origin, self.owner.origin, FALSE, self);
		setorigin(self, (trace_endpos + (v_up * (-5 + (self.owner.burnz_origin + self.burn_origin)))));
		self.nextthink = (time + 0.02);
		self.think = bburnd;
		self.burn_origin = (self.burn_origin + 0.4);
	}
};

void() burnd =
{
	local entity myburn;
	local float zufall;

	myburn = spawn();
	myburn.movetype = 0;
	myburn.solid = 0;
	setsize(myburn, VEC_ORIGIN, VEC_ORIGIN);
	myburn.owner = self;
	self.burny = myburn;
	myburn.classname = "flash";
	self.alpha = 1;
	makevectors(self.v_angle);
	traceline(self.origin, self.origin, FALSE, self);
	setorigin(myburn, trace_endpos);
	zufall = random();
	if ((zufall > 0.61))
	{
		myburn.burn_color = 1;
	}
	else
	{
		if ((zufall < 0.39))
		{
			myburn.burn_color = 2;
		}
		else
		{
			myburn.burn_color = 3;
		}
	}
	myburn.think = bburnd;
	myburn.nextthink = (time + 0.005);
};

void() burn_toggle_allround =
{
	if ((self.burn_flag == FALSE))
	{
		self.burn_flag = TRUE;
		burnd();
		zburnd();
	}
};

void() zdisapeare =
{
	self.frame = self.owner.frame;
	if ((self.alpha < 0))
	{
		remove(self);
	}
	else
	{
		self.alpha = (self.alpha - 0.01);
		self.nextthink = (time + 0.01);
	}
};

void() zbburne =
{
	if ((self.alpha > 1))
	{
		self.nextthink = (time + 0.01);
		self.think = zdisapeare;
		self.frame = self.owner.frame;
	}
	else
	{
		makevectors(self.owner.angles);
		traceline(self.owner.origin, self.owner.origin, FALSE, self);
		setorigin(self, trace_endpos);
		self.nextthink = (time + 0.01);
		self.think = zbburne;
		self.frame = self.owner.frame;
		self.scale = 1;
		self.angles = self.owner.angles;
		self.owner.alpha = (self.owner.alpha - 0.025);
		self.alpha = (self.alpha + 0.025);
	}
};

void() zburne =
{
	local entity myburn;

	myburn = spawn();
	myburn.movetype = 0;
	myburn.solid = 0;
	setsize(myburn, VEC_ORIGIN, VEC_ORIGIN);
	myburn.owner = self;
	self.burny = myburn;
	myburn.classname = "flash";
	makevectors(self.v_angle);
	traceline(self.origin, self.origin, FALSE, self);
	setorigin(myburn, trace_endpos);
	myburn.alpha = -0.01;
	myburn.think = zbburne;
	myburn.nextthink = (time + 0.005);
};

void() bburne =
{
	if ((self.burn_origin > 10))
	{
		self.think = SUB_Remove;
		self.nextthink = (time + 0.02);
	}
	if ((self.burn_origin <= 4))
	{
		pointparticles(particleeffectnum(/*51811i*/"grimrock_shambler"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51829i*/"grimrock_shambler1"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51848i*/"burningshambler"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51848i*/"burningshambler"), self.origin, VEC_ORIGIN, 1);
		makevectors(self.owner.angles);
		traceline(self.owner.origin, self.owner.origin, FALSE, self);
		setorigin(self, (trace_endpos + (v_up * (-5 + (self.owner.burnz_origin + self.burn_origin)))));
		self.nextthink = (time + 0.02);
		self.think = bburne;
		self.burn_origin = (self.burn_origin + 0.4);
	}
	if (((self.burn_origin <= 10) && (self.burn_origin > 4)))
	{
		pointparticles(particleeffectnum(/*51811i*/"grimrock_shambler"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51864i*/"grimrock_shambler2"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51848i*/"burningshambler"), self.origin, VEC_ORIGIN, 1);
		pointparticles(particleeffectnum(/*51848i*/"burningshambler"), self.origin, VEC_ORIGIN, 1);
		makevectors(self.owner.angles);
		traceline(self.owner.origin, self.owner.origin, FALSE, self);
		setorigin(self, (trace_endpos + (v_up * (-5 + (self.owner.burnz_origin + self.burn_origin)))));
		self.nextthink = (time + 0.02);
		self.think = bburne;
		self.burn_origin = (self.burn_origin + 0.4);
	}
};

void() burne =
{
	local entity myburn;

	myburn = spawn();
	myburn.movetype = 0;
	myburn.solid = 0;
	setsize(myburn, VEC_ORIGIN, VEC_ORIGIN);
	myburn.owner = self;
	self.burny = myburn;
	myburn.classname = "flash";
	self.alpha = 1;
	makevectors(self.v_angle);
	traceline(self.origin, self.origin, FALSE, self);
	setorigin(myburn, trace_endpos);
	myburn.think = bburne;
	myburn.nextthink = (time + 0.005);
};

void() burn_toggle_shambler =
{
	if ((self.burn_flag == FALSE))
	{
		self.burn_flag = TRUE;
		burne();
		zburne();
	}
};
