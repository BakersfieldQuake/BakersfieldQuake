//Decompiled code. Please respect the original copyright.

void() sword_stand1 = [ 0, sword_stand1 ]
{
	ai_stand();
};

void() sword_run1 = [ 1, sword_run2 ]
{
	self.effects = EF_DIMLIGHT;
	ai_run(14);
};

void() sword_run2 = [ 2, sword_run3 ]
{
	ai_run(14);
};

void() sword_run3 = [ 3, sword_run4 ]
{
	ai_run(14);
};

void() sword_run4 = [ 4, sword_run5 ]
{
	ai_run(14);
};

void() sword_run5 = [ 5, sword_run6 ]
{
	ai_run(14);
};

void() sword_run6 = [ 6, sword_run7 ]
{
	ai_run(14);
};

void() sword_run7 = [ 7, sword_run8 ]
{
	ai_run(14);
};

void() sword_run8 = [ 8, sword_run1 ]
{
	ai_run(14);
};

void() sword_atk1 = [ 9, sword_atk2 ]
{
	sound(self, 0, "knight/sword1.wav", 1, 1);
	ai_charge(14);
};

void() sword_atk2 = [ 10, sword_atk3 ]
{
	ai_charge(14);
};

void() sword_atk3 = [ 11, sword_atk4 ]
{
	ai_charge(14);
};

void() sword_atk4 = [ 12, sword_atk5 ]
{
	ai_charge(14);
};

void() sword_atk5 = [ 13, sword_atk6 ]
{
	ai_melee();
};

void() sword_atk6 = [ 14, sword_atk7 ]
{
	ai_melee();
};

void() sword_atk7 = [ 15, sword_atk8 ]
{
	ai_melee();
};

void() sword_atk8 = [ 16, sword_atk9 ]
{
	ai_charge(14);
};

void() sword_atk9 = [ 17, sword_atk10 ]
{
	ai_charge(14);
};

void() sword_atk10 = [ 18, sword_run1 ]
{
	ai_charge(14);
};

void() sword_die1 = [ 19, sword_die2 ]
{
};

void() sword_die2 = [ 20, sword_die3 ]
{
};

void() sword_die3 = [ 21, sword_die4 ]
{
	self.solid = 0;
};

void() sword_die4 = [ 22, sword_die5 ]
{
};

void() sword_die5 = [ 23, sword_die6 ]
{
};

void() sword_die6 = [ 24, sword_die7 ]
{
};

void() sword_die7 = [ 25, sword_die8 ]
{
	sound(self, 1, "player/axhit2.wav", 0.5, ATTN_NORM);
};

void() sword_die8 = [ 26, sword_die9 ]
{
};

void() sword_die9 = [ 27, sword_die10 ]
{
};

void() sword_die10 = [ 28, sword_die10 ]
{
};

void() sword_dieb1 = [ 29, sword_dieb2 ]
{
};

void() sword_dieb2 = [ 30, sword_dieb3 ]
{
};

void() sword_dieb3 = [ 31, sword_dieb4 ]
{
	self.solid = 0;
};

void() sword_dieb4 = [ 32, sword_dieb5 ]
{
};

void() sword_dieb5 = [ 33, sword_dieb6 ]
{
};

void() sword_dieb6 = [ 34, sword_dieb7 ]
{
};

void() sword_dieb7 = [ 35, sword_dieb8 ]
{
	sound(self, 1, "player/axhit2.wav", 0.5, ATTN_NORM);
};

void() sword_dieb8 = [ 36, sword_dieb9 ]
{
};

void() sword_dieb9 = [ 37, sword_dieb10 ]
{
};

void() sword_dieb10 = [ 38, sword_dieb11 ]
{
};

void() sword_dieb11 = [ 39, sword_dieb11 ]
{
};

void() sword_die =
{
	self.effects = 0;
	if ((random() < 0.5))
	{
		sword_die1();
	}
	else
	{
		sword_dieb1();
	}
};

void() sword_pause =
{
	self.th_run = sword_run1;
	self.think = sword_run1;
	self.nextthink = (time + self.delay);
	self.delay = 0;
};

void() sword_pain =
{
	self.th_run = sword_run1;
	self.think = sword_run1;
	self.nextthink = (time + 0.1);
	self.delay = 0;
	self.th_pain = SUB_Null;
};

void() monster_sword =
{
	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/sword.mdl");
	precache_sound("knight/sword1.wav");
	precache_sound("knight/ksight.wav");
	precache_sound("player/axhit2.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/sword.mdl");
	setsize(self, VEC_HULL_MIN, '16 16 40');
	self.health = 150;
	if (!self.delay)
	{
		self.delay = 10;
	}
	self.th_stand = sword_stand1;
	self.th_walk = sword_stand1;
	self.th_run = sword_pause;
	self.th_melee = sword_atk1;
	self.th_die = sword_die;
	self.th_pain = sword_pain;
	walkmonster_start();
};
