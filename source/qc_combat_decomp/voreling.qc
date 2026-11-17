//Decompiled code. Please respect the original copyright.

void() voreling_idle1 = [ 0, voreling_idle2 ]
{
	monster_idle_sound();
	ai_stand();
};

void() voreling_idle2 = [ 1, voreling_idle3 ]
{
	ai_stand();
};

void() voreling_idle3 = [ 2, voreling_idle4 ]
{
	ai_stand();
};

void() voreling_idle4 = [ 3, voreling_idle5 ]
{
	ai_stand();
};

void() voreling_idle5 = [ 4, voreling_idle6 ]
{
	ai_stand();
};

void() voreling_idle6 = [ 5, voreling_idle7 ]
{
	ai_stand();
};

void() voreling_idle7 = [ 6, voreling_idle8 ]
{
	ai_stand();
};

void() voreling_idle8 = [ 7, voreling_idle9 ]
{
	ai_stand();
};

void() voreling_idle9 = [ 8, voreling_idle10 ]
{
	ai_stand();
};

void() voreling_idle10 = [ 9, voreling_idle11 ]
{
	ai_stand();
};

void() voreling_idle11 = [ 10, voreling_idle12 ]
{
	ai_stand();
};

void() voreling_idle12 = [ 11, voreling_idle13 ]
{
	ai_stand();
};

void() voreling_idle13 = [ 12, voreling_idle1 ]
{
	ai_stand();
};

void() voreling_dangle1 = [ 13, voreling_dangle2 ]
{
	self.velocity_z = 10000;
	monster_idle_sound();
	ai_stand();
};

void() voreling_dangle2 = [ 14, voreling_dangle3 ]
{
	self.velocity_z = 10000;
	ai_stand();
};

void() voreling_dangle3 = [ 15, voreling_dangle4 ]
{
	self.velocity_z = 10000;
	ai_stand();
};

void() voreling_dangle4 = [ 16, voreling_dangle5 ]
{
	self.velocity_z = 10000;
	ai_stand();
};

void() voreling_dangle5 = [ 17, voreling_dangle6 ]
{
	self.velocity_z = 10000;
	ai_stand();
};

void() voreling_dangle6 = [ 18, voreling_dangle1 ]
{
	self.velocity_z = 10000;
	self.movetype = 0;
	ai_stand();
};

void() voreling_walk1 = [ 34, voreling_walk2 ]
{
	monster_idle_sound();
	ai_walk(4);
};

void() voreling_walk2 = [ 35, voreling_walk3 ]
{
	ai_walk(3);
};

void() voreling_walk3 = [ 36, voreling_walk4 ]
{
	ai_walk(4);
};

void() voreling_walk4 = [ 37, voreling_walk5 ]
{
	ai_walk(5);
};

void() voreling_walk5 = [ 38, voreling_walk1 ]
{
	ai_walk(5);
};

void() voreling_run1 = [ 39, voreling_run2 ]
{
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "voreling/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	ai_run(20);
};

void() voreling_run2 = [ 40, voreling_run3 ]
{
	if ((self.spawnflags & VORE_CEIL))
	{
		self.movetype = MOVETYPE_STEP;
		self.velocity_z = 0;
	}
	ai_run(25);
};

void() voreling_run3 = [ 41, voreling_run4 ]
{
	ai_run(22);
};

void() voreling_run4 = [ 42, voreling_run5 ]
{
	ai_run(18);
};

void() voreling_run5 = [ 58, voreling_run6 ]
{
	ai_run(25);
};

void() voreling_run6 = [ 59, voreling_run7 ]
{
	ai_run(21);
};

void() voreling_run7 = [ 59, voreling_run8 ]
{
	ai_run(24);
};

void() voreling_run8 = [ 59, voreling_run1 ]
{
	ai_run(27);
};

void() voreling_jump1 = [ 43, voreling_jump2 ]
{
	ai_face();
};

void() voreling_jump2 = [ 44, voreling_jump3 ]
{
	ai_face();
};

void() voreling_jump3 = [ 45, voreling_jump4 ]
{
	ai_face();
};

void() voreling_jump4 = [ 46, voreling_jump5 ]
{
	ai_face();
	self.attack_timer = 0;
	self.touch = voreling_JumpTouch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 400) + '0 0 200');
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
};

void() voreling_jump5 = [ 47, voreling_jump6 ]
{
};

void() voreling_jump6 = [ 48, voreling_jump7 ]
{
};

void() voreling_jump7 = [ 115, voreling_jump8 ]
{
};

void() voreling_jump8 = [ 116, voreling_jump9 ]
{
};

void() voreling_jump9 = [ 117, voreling_run1 ]
{
};

void() voreling_bite1 = [ 49, voreling_bite2 ]
{
	ai_face();
};

void() voreling_bite2 = [ 50, voreling_bite3 ]
{
	ai_face();
};

void() voreling_bite3 = [ 51, voreling_bite4 ]
{
	ai_face();
};

void() voreling_bite4 = [ 52, voreling_bite5 ]
{
	voreling_melee(10);
};

void() voreling_bite5 = [ 53, voreling_bite6 ]
{
};

void() voreling_bite6 = [ 54, voreling_bite7 ]
{
};

void() voreling_bite7 = [ 55, voreling_run1 ]
{
};

void() voreling_pain1 = [ 56, voreling_pain2 ]
{
};

void() voreling_pain2 = [ 57, voreling_run1 ]
{
};

void(entity attacker, float damage) voreling_pain =
{
	if ((self.touch == voreling_JumpTouch))
	{
		return;
	}
	if ((self.pain_finished > time))
	{
		return;
	}
	self.pain_finished = (time + 1);
	sound7(self, CHAN_VOICE, "voreling/pain.wav", 1, ATTN_NORM, SNDSPD);
	if (((random() * 50) > damage))
	{
		return;
	}
	voreling_pain1();
};

void() voreling_die1 = [ 58, voreling_die2 ]
{
};

void() voreling_die2 = [ 59, voreling_die3 ]
{
	sound7(self, CHAN_VOICE, "voreling/death.wav", 1, ATTN_NORM, SNDSPD);
};

void() voreling_die3 = [ 60, voreling_die4 ]
{
	self.solid = 0;
};

void() voreling_die4 = [ 61, voreling_die5 ]
{
};

void() voreling_die5 = [ 62, voreling_die6 ]
{
};

void() voreling_die6 = [ 63, voreling_die7 ]
{
};

void() voreling_die7 = [ 64, voreling_die7 ]
{
	CopyMonsterToBodyQue(8, "progs/gib_voreleg.mdl");
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
};

void() voreling_dieB1 = [ 65, voreling_dieB2 ]
{
};

void() voreling_dieB2 = [ 66, voreling_dieB3 ]
{
	sound7(self, CHAN_VOICE, "voreling/death.wav", 1, ATTN_NORM, SNDSPD);
};

void() voreling_dieB3 = [ 67, voreling_dieB4 ]
{
	self.solid = 0;
};

void() voreling_dieB4 = [ 68, voreling_dieB5 ]
{
};

void() voreling_dieB5 = [ 69, voreling_dieB6 ]
{
};

void() voreling_dieB6 = [ 70, voreling_dieB7 ]
{
};

void() voreling_dieB7 = [ 71, voreling_dieB8 ]
{
};

void() voreling_dieB8 = [ 72, voreling_dieB8 ]
{
	CopyMonsterToBodyQue(8, "progs/gib_voreleg.mdl");
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
};

void() voreling_die =
{
	bodyCheck();
	if (((!self.shocked && (self.enemy.weapon == IT_LIGHTNING)) && (self.sticky != 1)))
	{
		lg_death1();
		return;
	}
	if ((((self.health < -15) || (self.enemy.weapon == IT_CHAINSAW)) || (self.enemy.meleeing && (random() < 0.4))))
	{
		sound7(self, CHAN_VOICE, "player/gibexplode.wav", 1, ATTN_NORM, SNDSPD);
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		ThrowHead("progs/gib_voreleg.mdl", self.health);
		ThrowGib("progs/gib_voreleg.mdl", self.health);
		ThrowGib("progs/gib_voreleg.mdl", self.health);
		return;
	}
	if ((random() < 0.5))
	{
		voreling_die1();
	}
	else
	{
		voreling_dieB1();
	}
};

void() voreling_MeleeAtk =
{
	voreling_bite1();
};

void() monster_voreling =
{
	if (deathmatch)
	{
		remove(self);
		return;
	}
	precachegibs_shal();
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.netname = "monster_voreling";
	setmodel(self, "progs/voreling.mdl");
	setsize(self, ZOMB_MIN, '12 12 5');
	self.health = 40;
	if ((self.spawnflags & VORE_CEIL))
	{
		self.th_stand = voreling_dangle1;
	}
	else
	{
		self.th_stand = voreling_idle1;
	}
	self.th_walk = voreling_walk1;
	self.th_run = voreling_run1;
	self.th_die = voreling_die;
	self.th_melee = voreling_MeleeAtk;
	self.th_missile = voreling_jump1;
	self.th_pain = voreling_pain;
	walkmonster_start();
};

void() monster_shalrathminion =
{
	self.classname = "monster_voreling";
	monster_voreling();
};

float() CheckVorelingMelee =
{
	if ((enemy_range == RANGE_MELEE))
	{
		if (((self.enemy.origin - self.origin)[0] <= 48))
		{
			self.attack_state = AS_MELEE;
			return (TRUE);
		}
	}
	return (0);
};

float() CheckVorelingJump =
{
	local vector dist;
	local float d;

	if (((self.origin_z + self.mins_z) > ((self.enemy.origin_z + self.enemy.mins_z) + (0.75 * self.enemy.size_z))))
	{
		return (0);
	}
	if (((self.origin_z + self.maxs_z) < ((self.enemy.origin_z + self.enemy.mins_z) + (0.25 * self.enemy.size_z))))
	{
		return (0);
	}
	dist = self.enemy.origin - self.origin;
	d = vlen(dist);
	if ((d < 112))
	{
		return (0);
	}
	else
	{
		if ((random() < 0.95))
		{
			return (0);
		}
	}
	return (TRUE);
};

float() VorelingCheckAttack =
{
	if (CheckVorelingMelee())
	{
		self.attack_state = AS_MELEE;
		return (TRUE);
	}
	if (CheckVorelingJump())
	{
		self.attack_state = AS_MISSILE;
		return (TRUE);
	}
	return (0);
};

void(float side) voreling_melee =
{
	local float ldmg;
	local vector delta;

	ai_face();
	walkmove(self.ideal_yaw, 12);
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 64))
	{
		return;
	}
	if (!CanDamage(self.enemy, self))
	{
		return;
	}
	sound7(self, CHAN_WEAPON, "voreling/attackmunch.wav", 1, ATTN_NORM, SNDSPD);
	ldmg = 3 * random();
	if ((other.classname == "monster_shalrath_boss"))
	{
		sound7(self, CHAN_WEAPON, "voreling/attacktear.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		T_Damage(self.enemy, self, self, ldmg);
	}
	makevectors(self.angles);
	SpawnMeatSpray((self.origin + (v_forward * 16)), (side * v_right));
};

void() voreling_JumpTouch =
{
	local float ldmg;

	if ((self.health <= 0))
	{
		return;
	}
	if (other.takedamage)
	{
		if ((vlen(self.velocity) > 400))
		{
			ldmg = 8;
			if (((other.classname == "monster_shalrath_boss") || (other.classname == "monster_voreling")))
			{
				sound7(self, CHAN_WEAPON, "voreling/attacktear.wav", 1, ATTN_NORM, SNDSPD);
			}
			else
			{
				if ((self.attack_timer == 0))
				{
					T_Damage(other, self, self, ldmg);
					self.attack_timer = 1;
				}
				sound7(self, CHAN_WEAPON, "voreling/attacktear.wav", 1, ATTN_NORM, SNDSPD);
			}
		}
	}
	if (!checkbottom(self))
	{
		if ((self.flags & FL_ONGROUND))
		{
			self.touch = SUB_Null;
			self.think = voreling_jump1;
			self.nextthink = (time + 0.1);
		}
		return;
	}
	self.touch = SUB_Null;
	self.think = voreling_jump9;
	self.nextthink = (time + 0.1);
};
