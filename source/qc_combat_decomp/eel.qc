//Decompiled code. Please respect the original copyright.

void() eel_pitch_change =
{
	if ((pointcontents(self.origin) != CONTENT_WATER))
	{
		droptofloor();
		T_Damage(self, world, world, 6);
		return;
	}
	if ((time < self.delay))
	{
		return;
	}
	if ((self.weapon > 10))
	{
		self.weapon = -10;
	}
	if ((self.weapon < 0))
	{
		self.angles_x = (self.angles_x - 1.5);
	}
	else
	{
		if ((self.weapon > 0))
		{
			self.angles_x = (self.angles_x + 1.5);
		}
	}
	self.weapon = (self.weapon + 1);
};

void() eel_stand1 = [ 0, eel_stand2 ]
{
	ai_stand();
	eel_pitch_change();
};

void() eel_stand2 = [ 1, eel_stand3 ]
{
	ai_stand();
	eel_pitch_change();
};

void() eel_stand3 = [ 2, eel_stand4 ]
{
	ai_stand();
	eel_pitch_change();
};

void() eel_stand4 = [ 3, eel_stand5 ]
{
	ai_stand();
	eel_pitch_change();
};

void() eel_stand5 = [ 4, eel_stand6 ]
{
	ai_stand();
	eel_pitch_change();
};

void() eel_stand6 = [ 5, eel_stand1 ]
{
	ai_stand();
	eel_pitch_change();
};

void() eel_walk1 = [ 0, eel_walk2 ]
{
	if ((random() < 0.2))
	{
		sound(self, CHAN_VOICE, "eel/eactive1.wav", 1, ATTN_IDLE);
	}
	ai_walk(6);
	eel_pitch_change();
};

void() eel_walk2 = [ 1, eel_walk3 ]
{
	ai_walk(6);
	eel_pitch_change();
};

void() eel_walk3 = [ 2, eel_walk4 ]
{
	ai_walk(6);
	eel_pitch_change();
};

void() eel_walk4 = [ 3, eel_walk5 ]
{
	ai_walk(6);
	eel_pitch_change();
};

void() eel_walk5 = [ 4, eel_walk6 ]
{
	ai_walk(6);
	eel_pitch_change();
};

void() eel_walk6 = [ 5, eel_walk1 ]
{
	ai_walk(6);
	eel_pitch_change();
};

void() eel_run1 = [ 0, eel_run2 ]
{
	if ((random() < 0.4))
	{
		sound(self, CHAN_VOICE, "eel/eactive1.wav", 1, ATTN_IDLE);
	}
	ai_run(10);
	eel_pitch_change();
};

void() eel_run2 = [ 1, eel_run3 ]
{
	ai_run(10);
	eel_pitch_change();
};

void() eel_run3 = [ 2, eel_run4 ]
{
	ai_run(10);
	eel_pitch_change();
};

void() eel_run4 = [ 3, eel_run5 ]
{
	ai_run(10);
	eel_pitch_change();
};

void() eel_run5 = [ 4, eel_run6 ]
{
	ai_run(10);
	eel_pitch_change();
};

void() eel_run6 = [ 5, eel_run1 ]
{
	ai_run(10);
	eel_pitch_change();
};

void() eel_melee =
{
	local float attackOK;

	attackOK = 1;
	traceline(self.origin, self.enemy.origin, FALSE, self);
	if ((trace_ent != self.enemy))
	{
		attackOK = 0;
	}
	if ((trace_inopen && trace_inwater))
	{
		attackOK = 0;
	}
	if (attackOK)
	{
		T_EELZap(self, self, 45);
	}
	self.skin = 0;
	self.effects = 0;
};

void() eel_attack1 = [ 0, eel_attack2 ]
{
	ai_charge(8);
	eel_pitch_change();
};

void() eel_attack2 = [ 1, eel_attack3 ]
{
	ai_charge(8);
	eel_pitch_change();
};

void() eel_attack3 = [ 2, eel_attack4 ]
{
	ai_charge(8);
	eel_pitch_change();
};

void() eel_attack4 = [ 3, eel_attack5 ]
{
	ai_charge(8);
	eel_pitch_change();
};

void() eel_attack5 = [ 4, eel_attack6 ]
{
	ai_charge(8);
	eel_pitch_change();
};

void() eel_attack6 = [ 5, eel_attack7 ]
{
	ai_charge(8);
	eel_pitch_change();
};

void() eel_attack7 = [ 0, eel_attack8 ]
{
	ai_charge(8);
	eel_pitch_change();
};

void() eel_attack8 = [ 1, eel_attack9 ]
{
	self.effects = EF_DIMLIGHT;
	self.skin = 1;
	ai_charge(8);
	eel_pitch_change();
	sound(self, CHAN_WEAPON, "eel/eatt1.wav", 1, ATTN_NORM);
};

void() eel_attack9 = [ 2, eel_attack10 ]
{
	self.skin = 2;
	ai_charge(8);
	eel_pitch_change();
};

void() eel_attack10 = [ 3, eel_attack11 ]
{
	self.skin = 3;
	ai_charge(8);
	eel_pitch_change();
};

void() eel_attack11 = [ 4, eel_attack12 ]
{
	self.effects = EF_BRIGHTLIGHT;
	self.skin = 4;
	ai_charge(8);
	eel_pitch_change();
};

void() eel_attack12 = [ 5, eel_run1 ]
{
	self.skin = 5;
	eel_melee();
};

void() eel_death1 = [ 6, eel_death2 ]
{
	self.skin = 0;
	self.effects = 0;
	sound(self, CHAN_VOICE, "eel/edie3r.wav", 1, ATTN_NORM);
};

void() eel_death2 = [ 7, eel_death3 ]
{
};

void() eel_death3 = [ 8, eel_death4 ]
{
};

void() eel_death4 = [ 9, eel_death5 ]
{
};

void() eel_death5 = [ 8, eel_death6 ]
{
};

void() eel_death6 = [ 7, eel_death7 ]
{
};

void() eel_death7 = [ 6, eel_death8 ]
{
};

void() eel_death8 = [ 7, eel_death9 ]
{
};

void() eel_death9 = [ 8, eel_death10 ]
{
};

void() eel_death10 = [ 9, eel_death11 ]
{
};

void() eel_death11 = [ 10, eel_death12 ]
{
	self.flags = (self.flags - FL_SWIM);
};

void() eel_death12 = [ 11, eel_death13 ]
{
};

void() eel_death13 = [ 12, eel_death14 ]
{
};

void() eel_death14 = [ 13, eel_death15 ]
{
};

void() eel_death15 = [ 14, eel_death16 ]
{
	droptofloor();
};

void() eel_death16 = [ 15, eel_death16 ]
{
	self.solid = 0;
};

void() eel_death =
{
	self.flags = (self.flags + FL_SWIM);
	setsize(self, VEC_ORIGIN, VEC_ORIGIN);
	if ((self.health < -12))
	{
		self.skin = 0;
		self.effects = 0;
		ThrowHead("progs/eelgib.mdl", self.health);
		ThrowGib("progs/gib1.mdl", self.health);
		ThrowGib("progs/gib1.mdl", self.health);
		ThrowGib("progs/gib1.mdl", self.health);
		return;
	}
	else
	{
		eel_death1();
	}
};

void() eel_pain1 = [ 6, eel_pain2 ]
{
	if ((self.pain_finished > time))
	{
		return;
	}
	self.pain_finished = (time + 1);
	sound(self, CHAN_VOICE, "eel/epain3.wav", 1, ATTN_NORM);
	self.skin = 0;
};

void() eel_pain2 = [ 7, eel_pain3 ]
{
};

void() eel_pain3 = [ 8, eel_pain4 ]
{
};

void() eel_pain4 = [ 9, eel_pain5 ]
{
};

void() eel_pain5 = [ 8, eel_pain6 ]
{
};

void() eel_pain6 = [ 7, eel_pain7 ]
{
};

void() eel_pain7 = [ 6, eel_run1 ]
{
};

void() monster_eel =
{
	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/eel2.mdl");
	precache_model("progs/eelgib.mdl");
	precache_model("progs/gib1.mdl");
	precache_sound("eel/edie3r.wav");
	precache_sound("eel/epain3.wav");
	precache_sound("eel/eactive1.wav");
	precache_sound("eel/eatt1.wav");
	precache_sound("eel/eelc5.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/eel2.mdl");
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	self.health = 60;
	self.th_stand = eel_stand1;
	self.th_walk = eel_walk1;
	self.th_run = eel_run1;
	self.th_die = eel_death;
	self.th_pain = eel_pain1;
	self.th_melee = eel_attack1;
	self.delay = (time + (random() * 6));
	self.weapon = 0;
	swimmonster_start();
};
