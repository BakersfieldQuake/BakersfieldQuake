//Decompiled code. Please respect the original copyright.

void(entity targ) ResetDebuffScreen =
{
	targ.cshift_upd = 0;
	targ.cshift_time = LARGE_TIMER;
	stuffcmd(targ, "v_cshift 0 0 0 0\n");
	targ.cshift_col = VEC_ORIGIN;
	targ.cshift_den = 0;
};

void(entity targ) ResetDebuffBurning =
{
	targ.burning_qty = 0;
	targ.burning = 0;
};

void(entity targ) ResetDebuffPoisoned =
{
	targ.poisoned_qty = 0;
	targ.poisoned = 0;
};

void(entity targ) ResetDebuffBleeding =
{
	targ.bleeding_qty = 0;
	targ.bleeding = 0;
};

void(entity targ) ResetDebuffSystem =
{
	ResetDebuffScreen(targ);
	ResetDebuffBurning(targ);
	ResetDebuffPoisoned(targ);
	ResetDebuffBleeding(targ);
};

void() ClientDeBuff =
{
	if (((intermission_running > 0) || (self.health < 1)))
	{
		ResetDebuffSystem(self);
		return;
	}
	if (self.burning)
	{
		if ((self.burning_time < time))
		{
			if ((self.burning_qty > 0))
			{
				self.burning_time = (time + 1);
				if ((!self.bleeding && !self.poisoned))
				{
					if ((self.debuff_sound < time))
					{
						self.debuff_sound = (time + 1);
					}
					self.cshift_upd = TRUE;
					self.cshift_time = -1;
					self.cshift_col = DEBUFF_BURN_COL;
					self.cshift_den = DEBUFF_BURN_DEN;
					self.cshift_step = DEBUFF_BURN_STEP;
				}
				self.debuff_qty = DEBUFF_BURN_DMG;
				if ((self.burning_qty < self.debuff_qty))
				{
					self.debuff_qty = self.burning_qty;
				}
				self.burning_qty = (self.burning_qty - self.debuff_qty);
				T_Damage(self, world, world, self.debuff_qty, NOARMOR);
			}
		}
		if (((self.waterlevel >= 2) || (self.burning_qty < 1)))
		{
			ResetDebuffBurning(self);
		}
	}
	if (self.poisoned)
	{
		if ((self.poisoned_time < time))
		{
			if ((self.poisoned_qty > 0))
			{
				self.poisoned_time = (time + 1);
				if (!self.bleeding)
				{
					if ((self.debuff_sound < time))
					{
						self.debuff_sound = (time + 1);
					}
					self.cshift_upd = TRUE;
					self.cshift_time = -1;
					self.cshift_col = DEBUFF_POISON_COL;
					self.cshift_den = DEBUFF_POISON_DEN;
					self.cshift_step = DEBUFF_POISON_STEP;
				}
				self.debuff_qty = DEBUFF_POISON_DMG;
				if ((self.poisoned_qty < self.debuff_qty))
				{
					self.debuff_qty = self.poisoned_qty;
				}
				self.poisoned_qty = (self.poisoned_qty - self.debuff_qty);
				T_Damage(self, world, world, self.debuff_qty, NOARMOR);
			}
		}
		if ((self.poisoned_qty < 1))
		{
			ResetDebuffPoisoned(self);
		}
	}
	if (self.bleeding)
	{
		if ((self.bleeding_time < time))
		{
			if ((self.bleeding_qty > 0))
			{
				self.bleeding_time = (time + 1);
				if ((self.debuff_sound < time))
				{
					self.debuff_sound = (time + 1);
				}
				self.cshift_upd = TRUE;
				self.cshift_time = -1;
				self.cshift_col = DEBUFF_BLEED_COL;
				self.cshift_den = DEBUFF_BLEED_DEN;
				self.cshift_step = DEBUFF_BLEED_STEP;
				self.debuff_qty = DEBUFF_BLEED_HEAL;
				if ((self.bleeding_qty < self.debuff_qty))
				{
					self.debuff_qty = self.bleeding_qty;
				}
				self.bleeding_qty = (self.bleeding_qty - self.debuff_qty);
				if (((self.health + self.debuff_qty) > self.max_health))
				{
					self.debuff_qty = (self.max_health - self.health);
				}
				self.health = (self.health + self.debuff_qty);
			}
		}
		if (((self.health >= self.max_health) || (self.bleeding_qty < 1)))
		{
			ResetDebuffBleeding(self);
		}
	}
	if (self.cshift_upd)
	{
		if ((self.debuff_sound > time))
		{
			self.debuff_sound = -1;
			if (((self.flags & FL_GODMODE) || (self.invincible_finished >= time)))
			{
				if ((self.invincible_sound < time))
				{
					self.invincible_sound = (time + 2);
				}
			}
			else
			{
				if (self.poisoned)
				{
					if ((random() < 0.5))
					{
						sound(self, CHAN_VOICE, "player/pain2.wav", 1, ATTN_IDLE);
					}
					else
					{
						sound(self, CHAN_VOICE, "player/pain3.wav", 1, ATTN_IDLE);
					}
				}
				else
				{
					if (self.burning)
					{
						if ((random() < 0.5))
						{
							sound(self, CHAN_VOICE, "player/pain1.wav", 1, ATTN_IDLE);
						}
						else
						{
							sound(self, CHAN_VOICE, "player/pain4.wav", 1, ATTN_IDLE);
						}
					}
				}
			}
		}
		if ((self.cshift_time < time))
		{
			self.cshift_den = (self.cshift_den - self.cshift_step);
			if ((self.cshift_den < 1))
			{
				ResetDebuffScreen(self);
			}
			else
			{
				self.cshift_time = (time + 0.1);
				if (((self.items & ALL_ITARTIFACTS) == 0))
				{
					stuffcmd(self, "v_cshift ");
					stuffcmd(self, ftos(rint(self.cshift_col_x)));
					stuffcmd(self, " ");
					stuffcmd(self, ftos(rint(self.cshift_col_y)));
					stuffcmd(self, " ");
					stuffcmd(self, ftos(rint(self.cshift_col_z)));
					stuffcmd(self, " ");
					stuffcmd(self, ftos(rint(self.cshift_den)));
					stuffcmd(self, "\n");
				}
			}
		}
	}
	else
	{
		if ((self.cshift_time < time))
		{
			ResetDebuffScreen(self);
		}
	}
};

void(entity targ) BurnDeBuff =
{
	local float debuffqty;

	if ((targ.burning_qty > DEBUFF_BURN_MAX))
	{
		return;
	}
	if (((targ.flags & FL_CLIENT) == FALSE))
	{
		return;
	}
	if ((targ.waterlevel >= 3))
	{
		return;
	}
	if ((targ.items & 3145728))
	{
		return;
	}
	if (!targ.burning)
	{
		targ.burning = TRUE;
		targ.burning_time = -1;
	}
	debuffqty = rint((((5 * skill) + 3) + (2 * random())));
	targ.burning_qty = (targ.burning_qty + debuffqty);
	if ((targ.burning_qty > DEBUFF_BURN_MAX))
	{
		targ.burning_qty = DEBUFF_BURN_MAX;
	}
	targ.cshift_upd = TRUE;
	targ.cshift_time = -1;
	targ.cshift_col = DEBUFF_BURN_COL;
	targ.cshift_den = DEBUFF_BURN_DEN;
	targ.cshift_step = DEBUFF_BURN_STEP;
};

void(entity targ) PoisonDeBuff =
{
	local float debuffqty;

	if (((targ.flags & FL_CLIENT) == FALSE))
	{
		return;
	}
	if ((targ.items & 3145728))
	{
		return;
	}
	if (targ.poisoned)
	{
		return;
	}
	targ.poisoned = TRUE;
	targ.poisoned_time = -1;
	debuffqty = rint(((skill + 3) + (2 * random())));
	targ.poisoned_qty = (targ.poisoned_qty + debuffqty);
	targ.cshift_upd = TRUE;
	targ.cshift_time = -1;
	targ.cshift_col = DEBUFF_POISON_COL;
	targ.cshift_den = DEBUFF_POISON_DEN;
	targ.cshift_step = DEBUFF_POISON_STEP;
};

void(entity targ, float playdmg, float mondmg) ApplyFireDmg =
{
	local float reduction;
	local float firedamage;

	reduction = 0.2 + (skill * 0.1);
	if ((targ.flags & FL_MONSTER))
	{
		firedamage = mondmg;
	}
	else
	{
		if ((targ.items & IT_SUIT))
		{
			firedamage = rint((playdmg * reduction));
		}
		else
		{
			firedamage = playdmg;
		}
	}
	T_Damage(targ, self, self.owner, firedamage, NOARMOR);
	BurnDeBuff(targ);
};
