//Decompiled code. Please respect the original copyright.

void() knight_attack =
{
	local float len;

	len = vlen(((self.enemy.origin + self.enemy.view_ofs) - (self.origin + self.view_ofs)));
	if ((len < 80))
	{
		knight_atk1();
	}
	else
	{
		knight_runatk1();
	}
};

float() CheckAttack =
{
	local vector spot1;
	local vector spot2;
	local entity targ;
	local float chance;
	local float chance2;

	targ = self.enemy;
	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	traceline(spot1, spot2, FALSE, self);
	if ((trace_ent != targ))
	{
		return (0);
	}
	if ((trace_inopen && trace_inwater))
	{
		return (0);
	}
	if ((enemy_range == RANGE_MELEE))
	{
		if (self.th_melee)
		{
			if ((self.classname == "monster_knight"))
			{
				knight_attack();
			}
			else
			{
				self.th_melee();
				if ((self.classname == "monster_reiver"))
				{
					self.meleeing = 1;
				}
			}
			return (TRUE);
		}
	}
	if (!self.th_missile)
	{
		return (0);
	}
	if ((self.classname == "monster_reiver"))
	{
		self.meleeing = 0;
	}
	if ((time < self.attack_finished))
	{
		return (0);
	}
	if (((self.classname == "monster_hell_knight") || (self.classname == "monster_hell_knight2")))
	{
		if ((skill == 3))
		{
			chance2 = -0.05;
			if ((enemy_range == RANGE_NEAR))
			{
				chance2 = -0.15;
				if ((self.classname == "monster_hell_knight2"))
				{
					if ((vlen((self.enemy.origin - self.origin)) < 250))
					{
						chance2 = -0.39;
					}
				}
			}
		}
	}
	if ((enemy_range == RANGE_FAR))
	{
		return (0);
	}
	if ((enemy_range == RANGE_MELEE))
	{
		chance = 0.9;
		self.attack_finished = 0;
	}
	else
	{
		if ((enemy_range == RANGE_NEAR))
		{
			if (self.th_melee)
			{
				chance = 0.2;
			}
			else
			{
				chance = 0.4 + chance2;
			}
		}
		else
		{
			if ((enemy_range == RANGE_MID))
			{
				if (self.th_melee)
				{
					chance = 0.05;
				}
				else
				{
					chance = 0.1 + chance2;
				}
			}
			else
			{
				chance = 0;
			}
		}
	}
	if ((random() < chance))
	{
		self.th_missile();
		if (autocvar_skill_adjusted_monster_rangedattack_frequence)
		{
			if ((skill == 0))
			{
				SUB_AttackFinished((2 * random()));
			}
			else
			{
				if ((skill == 1))
				{
					SUB_AttackFinished((1.6 * random()));
				}
				else
				{
					if ((skill == 2))
					{
						SUB_AttackFinished((1.3 * random()));
					}
					else
					{
						SUB_AttackFinished(random());
					}
				}
			}
		}
		else
		{
			SUB_AttackFinished((2 * random()));
		}
		return (TRUE);
	}
	return (0);
};

void() ai_face =
{
	self.ideal_yaw = vectoyaw((self.enemy.origin - self.origin));
	ChangeYaw();
};

void(float d) ai_charge =
{
	ai_face();
	movetogoal(d);
};

void() ai_charge_side =
{
	local vector dtemp;
	local float heading;

	self.ideal_yaw = vectoyaw((self.enemy.origin - self.origin));
	ChangeYaw();
	makevectors(self.angles);
	dtemp = self.enemy.origin - (30 * v_right);
	heading = vectoyaw((dtemp - self.origin));
	walkmove(heading, 20);
};

void() ai_melee =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 60))
	{
		return;
	}
	ldmg = ((random() + random()) + random()) * 3;
	T_Damage(self.enemy, self, self, ldmg);
};

void(float scratch_noise) ai_melee_carnivean =
{
	local vector delta;
	local float ldmg;
	local float richtung;

	if (!self.enemy)
	{
		return;
	}
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 100))
	{
		return;
	}
	ldmg = ((random() + random()) + random()) * autocvar_carnivean_scythe_damage;
	T_Damage(self.enemy, self, self, ldmg);
	makevectors(self.angles);
	particle(((self.origin + (v_forward * 50)) + (v_up * 2)), VEC_ORIGIN, 73, 17);
	if (scratch_noise)
	{
		sound(self, CHAN_AUTO, "demon/dhit2.wav", 0.5, ATTN_NORM);
		richtung = crandom() * 100;
		SpawnMeatSpray(((self.origin + (v_forward * 30)) + (v_up * -5)), (v_right * richtung));
	}
};

void() ai_melee_torment =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 77))
	{
		return;
	}
	ldmg = ((random() + random()) + random()) * autocvar_torment_rod_melee;
	T_Damage(self.enemy, self, self, ldmg);
};

void() ai_melee_hknight =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	delta = self.enemy.origin - (self.origin + '0 0 4');
	if ((vlen(delta) > 60))
	{
		return;
	}
	if ((autocvar_hknight_size_influenced_attack == 1))
	{
		ldmg = (((random() + random()) + random()) * autocvar_hellknight_sword) * self.scale;
	}
	else
	{
		ldmg = ((random() + random()) + random()) * autocvar_hellknight_sword;
	}
	T_Damage(self.enemy, self, self, ldmg);
};

void() ai_melee_dfury =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	delta = self.enemy.origin - (self.origin + '0 0 4');
	if ((vlen(delta) > 60))
	{
		return;
	}
	if ((autocvar_hknight_size_influenced_attack == 1))
	{
		ldmg = (((random() + random()) + random()) * autocvar_hellknight_sword) * self.scale;
	}
	else
	{
		ldmg = ((random() + random()) + random()) * autocvar_hellknight_sword;
	}
	T_Damage(self.enemy, self, self, ldmg);
};

void() ai_melee_dfury_boss =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 80))
	{
		return;
	}
	ldmg = ((random() + random()) + random()) * 6;
	T_Damage(self.enemy, self, self, ldmg);
};

void() ai_melee_knight =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	delta = self.enemy.origin - (self.origin + '0 0 4');
	if ((vlen(delta) > 60))
	{
		return;
	}
	if ((autocvar_knight_size_influenced_attack == 1))
	{
		ldmg = (((random() + random()) + random()) * autocvar_knight_sword) * self.scale;
	}
	else
	{
		ldmg = ((random() + random()) + random()) * autocvar_knight_sword;
	}
	T_Damage(self.enemy, self, self, ldmg);
};

void() ai_melee_side =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	ai_charge_side();
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 60))
	{
		return;
	}
	if (!CanDamage(self.enemy, self))
	{
		return;
	}
	ldmg = ((random() + random()) + random()) * 3;
	T_Damage(self.enemy, self, self, ldmg);
};

void() ai_melee_side_knight =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	ai_charge_side();
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 60))
	{
		return;
	}
	if (!CanDamage(self.enemy, self))
	{
		return;
	}
	if ((autocvar_knight_size_influenced_attack == 1))
	{
		ldmg = (((random() + random()) + random()) * autocvar_knight_sword) * self.scale;
	}
	else
	{
		ldmg = ((random() + random()) + random()) * autocvar_knight_sword;
	}
	T_Damage(self.enemy, self, self, ldmg);
};

float() SoldierCheckAttack =
{
	local vector spot1;
	local vector spot2;
	local entity targ;
	local float chance;

	targ = self.enemy;
	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	traceline(spot1, spot2, FALSE, self);
	if ((trace_inopen && trace_inwater))
	{
		return (0);
	}
	if ((trace_ent != targ))
	{
		return (0);
	}
	if ((time < self.attack_finished))
	{
		return (0);
	}
	if ((enemy_range == RANGE_FAR))
	{
		return (0);
	}
	if ((enemy_range == RANGE_MELEE))
	{
		chance = 0.9;
	}
	else
	{
		if ((enemy_range == RANGE_NEAR))
		{
			chance = 0.4 + (skill * 0.025);
		}
		else
		{
			if ((enemy_range == RANGE_MID))
			{
				chance = 0.05 + (skill * 0.025);
			}
			else
			{
				chance = 0;
			}
		}
	}
	if ((random() < chance))
	{
		self.th_missile();
		if (autocvar_skill_adjusted_monster_rangedattack_frequence)
		{
			if ((skill == 0))
			{
				SUB_AttackFinished((1 + random()));
			}
			else
			{
				if ((skill == 1))
				{
					SUB_AttackFinished((0.75 + random()));
				}
				else
				{
					if ((skill == 2))
					{
						SUB_AttackFinished((0.5 + random()));
					}
					else
					{
						SUB_AttackFinished((0.5 + random()));
					}
				}
			}
		}
		else
		{
			SUB_AttackFinished(((1 - (skill * 0.1)) + random()));
		}
		if ((random() < 0.3))
		{
			self.lefty = !self.lefty;
		}
		return (TRUE);
	}
	return (0);
};

float() ShamCheckAttack =
{
	local vector spot1;
	local vector spot2;
	local entity targ;

	if ((enemy_range == RANGE_MELEE))
	{
		if (CanDamage(self.enemy, self))
		{
			self.attack_state = AS_MELEE;
			return (TRUE);
		}
	}
	if ((time < self.attack_finished))
	{
		return (0);
	}
	if (!enemy_vis)
	{
		return (0);
	}
	targ = self.enemy;
	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	if ((vlen((spot1 - spot2)) > 600))
	{
		return (0);
	}
	traceline(spot1, spot2, FALSE, self);
	if ((trace_inopen && trace_inwater))
	{
		return (0);
	}
	if ((trace_ent != targ))
	{
		return (0);
	}
	if ((enemy_range == RANGE_FAR))
	{
		return (0);
	}
	self.attack_state = AS_MISSILE;
	if (autocvar_skill_adjusted_monster_rangedattack_frequence)
	{
		if ((skill == 0))
		{
			SUB_AttackFinished((2 + (2 * random())));
		}
		else
		{
			if ((skill == 1))
			{
				SUB_AttackFinished((1.4 + (2 * random())));
			}
			else
			{
				if ((skill == 2))
				{
					SUB_AttackFinished((0.8 + (2 * random())));
				}
				else
				{
					SUB_AttackFinished((2 + (2 * random())));
				}
			}
		}
	}
	else
	{
		SUB_AttackFinished((2 + (2 * random())));
	}
	return (TRUE);
};

float() OgreCheckAttack =
{
	local vector spot1;
	local vector spot2;
	local entity targ;
	local float chance;

	if ((enemy_range == RANGE_MELEE))
	{
		if (CanDamage(self.enemy, self))
		{
			self.attack_state = AS_MELEE;
			return (TRUE);
		}
	}
	if ((time < self.attack_finished))
	{
		return (0);
	}
	if (!enemy_vis)
	{
		return (0);
	}
	if (((skill == 3) && (random() < 0.88)))
	{
		return (0);
	}
	targ = self.enemy;
	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	traceline(spot1, spot2, FALSE, self);
	if ((trace_inopen && trace_inwater))
	{
		return (0);
	}
	if ((trace_ent != targ))
	{
		return (0);
	}
	if ((time < self.attack_finished))
	{
		return (0);
	}
	if ((enemy_range == RANGE_FAR))
	{
		return (0);
	}
	else
	{
		if ((enemy_range == RANGE_NEAR))
		{
			chance = 0.1;
		}
		else
		{
			if ((enemy_range == RANGE_MID))
			{
				chance = 0.05;
			}
			else
			{
				chance = 0;
			}
		}
	}
	self.attack_state = AS_MISSILE;
	if (autocvar_skill_adjusted_monster_rangedattack_frequence)
	{
		if ((skill == 0))
		{
			SUB_AttackFinished((1 + (2 * random())));
		}
		else
		{
			if ((skill == 1))
			{
				SUB_AttackFinished((0.75 + (2 * random())));
			}
			else
			{
				if ((skill == 2))
				{
					SUB_AttackFinished((0.5 + (2 * random())));
				}
				else
				{
					SUB_AttackFinished((1 + (2 * random())));
				}
			}
		}
	}
	else
	{
		SUB_AttackFinished((1 + (2 * random())));
	}
	return (TRUE);
};
