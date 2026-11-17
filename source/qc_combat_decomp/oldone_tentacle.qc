//Decompiled code. Please respect the original copyright.

void() oldone_stand1 = [ 0, oldone_stand2 ]
{
	ai_stand();
};

void() oldone_stand2 = [ 1, oldone_stand3 ]
{
	ai_stand();
};

void() oldone_stand3 = [ 2, oldone_stand4 ]
{
	ai_stand();
};

void() oldone_stand4 = [ 3, oldone_stand5 ]
{
	ai_stand();
};

void() oldone_stand5 = [ 4, oldone_stand6 ]
{
	ai_stand();
};

void() oldone_stand6 = [ 5, oldone_stand1 ]
{
	ai_stand();
};

void() oldone_aim1 = [ 0, oldone_aim2 ]
{
	if ((random() < 0.4))
	{
		oldone_atta1();
	}
};

void() oldone_aim2 = [ 1, oldone_aim3 ]
{
};

void() oldone_aim3 = [ 2, oldone_aim4 ]
{
};

void() oldone_aim4 = [ 3, oldone_aim5 ]
{
};

void() oldone_aim5 = [ 4, oldone_aim6 ]
{
};

void() oldone_aim6 = [ 5, oldone_aim1 ]
{
};

void() groundSmash =
{
	local entity shake;

	shake = spawn();
	setorigin(shake, (self.origin + '0 0 15'));
	shake.think = screenshake;
	shake.attack_finished = (time + 0.3);
	shake.nextthink = (time + 0.2);
	sound(self, CHAN_AUTO, "shambler/fall.wav", 1, ATTN_NORM);
	T_RadiusDamage(self, self.owner, 50, self.owner);
	remove(self);
};

void(vector org, vector vec) oldone_attack =
{
	vec = normalize(vec);
	newmis = spawn();
	newmis.owner = self;
	newmis.movetype = MOVETYPE_FLY;
	newmis.solid = SOLID_BBOX;
	setorigin(newmis, org);
	newmis.velocity = (vec * 3600);
	newmis.angles = vectoangles(newmis.velocity);
	newmis.velocity_z = 0;
	newmis.nextthink = (time + 0.05);
	newmis.think = groundSmash;
	newmis.touch = groundSmash;
};

void() oldone_atta1 = [ 6, oldone_atta2 ]
{
	ai_face();
};

void() oldone_atta2 = [ 7, oldone_atta3 ]
{
	ai_face();
};

void() oldone_atta3 = [ 8, oldone_atta4 ]
{
	ai_face();
};

void() oldone_atta4 = [ 9, oldone_atta5 ]
{
	ai_face();
};

void() oldone_atta5 = [ 10, oldone_atta6 ]
{
	ai_face();
};

void() oldone_atta6 = [ 11, oldone_atta7 ]
{
	ai_face();
};

void() oldone_atta7 = [ 12, oldone_atta8 ]
{
	ai_face();
};

void() oldone_atta8 = [ 13, oldone_atta9 ]
{
	ai_face();
};

void() oldone_atta9 = [ 14, oldone_atta10 ]
{
	ai_face();
};

void() oldone_atta10 = [ 15, oldone_atta11 ]
{
	ai_face();
};

void() oldone_atta11 = [ 16, oldone_atta12 ]
{
	ai_face();
};

void() oldone_atta12 = [ 17, oldone_atta13 ]
{
	ai_face();
};

void() oldone_atta13 = [ 18, oldone_atta14 ]
{
	ai_face();
};

void() oldone_atta14 = [ 19, oldone_atta15 ]
{
	ai_face();
};

void() oldone_atta15 = [ 20, oldone_atta16 ]
{
	self.solid = 0;
};

void() oldone_atta16 = [ 21, oldone_atta17 ]
{
	oldone_attack(self.origin, (self.enemy.origin - self.origin));
};

void() oldone_atta17 = [ 22, oldone_atta18 ]
{
};

void() oldone_atta18 = [ 23, oldone_atta19 ]
{
	ai_face();
};

void() oldone_atta19 = [ 24, oldone_atta20 ]
{
	ai_face();
};

void() oldone_atta20 = [ 25, oldone_atta21 ]
{
	ai_face();
	self.solid = SOLID_BBOX;
};

void() oldone_atta21 = [ 26, oldone_aim1 ]
{
	ai_face();
};

void() oldone_die1 = [ 27, oldone_die2 ]
{
};

void() oldone_die2 = [ 28, oldone_die3 ]
{
};

void() oldone_die3 = [ 29, oldone_die4 ]
{
};

void() oldone_die4 = [ 30, oldone_die5 ]
{
};

void() oldone_die5 = [ 31, oldone_die6 ]
{
};

void() oldone_die6 = [ 32, oldone_die7 ]
{
};

void() oldone_die7 = [ 33, oldone_die8 ]
{
};

void() oldone_die8 = [ 34, oldone_die9 ]
{
};

void() oldone_die9 = [ 35, oldone_die10 ]
{
};

void() oldone_die10 = [ 36, oldone_die11 ]
{
};

void() oldone_die11 = [ 37, oldone_die12 ]
{
};

void() oldone_die12 = [ 38, oldone_die13 ]
{
};

void() oldone_die13 = [ 39, oldone_die14 ]
{
};

void() oldone_die14 = [ 40, oldone_die15 ]
{
};

void() oldone_die15 = [ 41, oldone_die16 ]
{
};

void() oldone_die16 = [ 42, oldone_die17 ]
{
};

void() oldone_die17 = [ 43, oldone_die17 ]
{
};

void() oldone_pain =
{
	sound(self, CHAN_VOICE, "boss1/pain.wav", 1, ATTN_NORM);
};

void() oldone_die =
{
	if ((self.health < -135))
	{
		play_gibsound();
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		return;
	}
	sound(self, CHAN_VOICE, "boss1/death.wav", 1, ATTN_NORM);
	self.solid = 0;
	oldone_die1();
};

float() CheckoldoneMelee =
{
	if ((enemy_range == RANGE_MELEE))
	{
		self.attack_state = AS_MELEE;
		return (TRUE);
	}
	return (0);
};

void() oldone_rise1 = [ 43, oldone_rise2 ]
{
	self.solid = SOLID_BBOX;
};

void() oldone_rise2 = [ 42, oldone_rise3 ]
{
};

void() oldone_rise3 = [ 41, oldone_rise4 ]
{
};

void() oldone_rise4 = [ 40, oldone_rise5 ]
{
};

void() oldone_rise5 = [ 39, oldone_rise6 ]
{
};

void() oldone_rise6 = [ 38, oldone_aim1 ]
{
	walkmonster_start();
};

void() oldone_hide =
{
};

void() monster_oldone_tentacle =
{
	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/oldone_tent.mdl");
	precache_sound("oldone/dattack1.wav");
	precache_sound("boss1/pain.wav");
	precache_sound("boss1/death.wav");
	self.solid = SOLID_BBOX;
	self.movetype = 0;
	setmodel(self, "progs/oldone_tent.mdl");
	setsize(self, ZOMB_MIN, '12 12 60');
	self.health = 135;
	self.scale = 0.5;
	self.th_run = oldone_aim1;
	self.th_pain = oldone_pain;
	self.th_die = oldone_die;
	self.th_melee = oldone_atta1;
	if (!self.targetname)
	{
		self.th_stand = oldone_stand1;
		walkmonster_start();
	}
	else
	{
		self.solid = 0;
		self.th_stand = oldone_stand1;
		self.frame = 43;
		self.use = oldone_rise1;
	}
};
