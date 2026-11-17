//Decompiled code. Please respect the original copyright.

void() dog_bite =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	ai_charge(10);
	if (!CanDamage(self.enemy, self))
	{
		return;
	}
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 100))
	{
		return;
	}
	if ((autocvar_dog_size_influenced_attack == 1))
	{
		ldmg = (((random() + random()) + random()) * autocvar_dog_bite) * self.scale;
	}
	else
	{
		ldmg = ((random() + random()) + random()) * autocvar_dog_bite;
	}
	T_Damage(self.enemy, self, self, ldmg);
};

void() Dog_JumpTouch =
{
	local float ldmg;

	if (((self.health <= 0) || (self.attack_timer > 0)))
	{
		return;
	}
	if (other.takedamage)
	{
		if ((vlen(self.velocity) > 300))
		{
			if ((autocvar_dog_size_influenced_attack == 1))
			{
				ldmg = (autocvar_dog_jump * self.scale) + (10 * random());
			}
			else
			{
				ldmg = autocvar_dog_jump + (10 * random());
			}
			T_Damage(other, self, self, ldmg);
			if ((other.classname == "player"))
			{
				self.attack_timer = 1;
			}
		}
	}
	if (!checkbottom(self))
	{
		if ((self.flags & FL_ONGROUND))
		{
			self.touch = SUB_Null;
			self.think = dog_leap1;
			self.nextthink = (time + 0.1);
		}
		return;
	}
	self.touch = SUB_Null;
	self.think = dog_run1;
	self.nextthink = (time + 0.1);
};

void(float loudness) dog_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.33))
		{
			sound7(self, CHAN_AUTO, "walk/dog1.wav", loudness, ATTN_IDLE, SNDSPD);
		}
		else
		{
			if ((select <= 0.66))
			{
				sound7(self, CHAN_AUTO, "walk/dog2.wav", loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_AUTO, "walk/dog3.wav", loudness, ATTN_IDLE, SNDSPD);
			}
		}
	}
};

void() dog_howl_newmodel1 = [ 140, dog_howl_newmodel2 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_howl_newmodel2 = [ 141, dog_howl_newmodel3 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_howl_newmodel3 = [ 142, dog_howl_newmodel4 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_howl_newmodel4 = [ 143, dog_howl_newmodel5 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_howl_newmodel5 = [ 144, dog_howl_newmodel6 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_howl_newmodel6 = [ 145, dog_howl_newmodel7 ]
{
	ai_stand();
	sound7(self, CHAN_VOICE, "dog/howl.wav", 1, ATTN_IDLE, SNDSPD);
};

void() dog_howl_newmodel7 = [ 146, dog_howl_newmodel8 ]
{
	ai_stand();
};

void() dog_howl_newmodel8 = [ 147, dog_howl_newmodel9 ]
{
	ai_stand();
};

void() dog_howl_newmodel9 = [ 148, dog_howl_newmodel10 ]
{
	ai_stand();
};

void() dog_howl_newmodel10 = [ 149, dog_howl_newmodel11 ]
{
	ai_stand();
};

void() dog_howl_newmodel11 = [ 150, dog_howl_newmodel12 ]
{
	ai_stand();
};

void() dog_howl_newmodel12 = [ 151, dog_howl_newmodel13 ]
{
	ai_stand();
};

void() dog_howl_newmodel13 = [ 152, dog_howl_newmodel14 ]
{
	ai_stand();
};

void() dog_howl_newmodel14 = [ 153, dog_howl_newmodel15 ]
{
	ai_stand();
};

void() dog_howl_newmodel15 = [ 154, dog_howl_newmodel16 ]
{
	ai_stand();
};

void() dog_howl_newmodel16 = [ 155, dog_howl_newmodel17 ]
{
	ai_stand();
};

void() dog_howl_newmodel17 = [ 156, dog_howl_newmodel18 ]
{
	ai_stand();
};

void() dog_howl_newmodel18 = [ 157, dog_howl_newmodel19 ]
{
	ai_stand();
};

void() dog_howl_newmodel19 = [ 158, dog_howl_newmodel20 ]
{
	ai_stand();
};

void() dog_howl_newmodel20 = [ 159, dog_howl_newmodel21 ]
{
	ai_stand();
};

void() dog_howl_newmodel21 = [ 160, dog_howl_newmodel22 ]
{
	ai_stand();
};

void() dog_howl_newmodel22 = [ 161, dog_howl_newmodel23 ]
{
	ai_stand();
};

void() dog_howl_newmodel23 = [ 162, dog_howl_newmodel24 ]
{
	ai_stand();
};

void() dog_howl_newmodel24 = [ 163, dog_howl_newmodel25 ]
{
	ai_stand();
};

void() dog_howl_newmodel25 = [ 164, dog_howl_newmodel26 ]
{
	ai_stand();
};

void() dog_howl_newmodel26 = [ 165, dog_howl_newmodel27 ]
{
	ai_stand();
};

void() dog_howl_newmodel27 = [ 166, dog_howl_newmodel28 ]
{
	ai_stand();
};

void() dog_howl_newmodel28 = [ 167, dog_howl_newmodel29 ]
{
	ai_stand();
};

void() dog_howl_newmodel29 = [ 167, dog_howl_newmodel30 ]
{
	ai_stand();
};

void() dog_howl_newmodel30 = [ 169, dog_howl_newmodel31 ]
{
	ai_stand();
};

void() dog_howl_newmodel31 = [ 170, dog_howl_newmodel32 ]
{
	ai_stand();
};

void() dog_howl_newmodel32 = [ 171, dog_howl_newmodel33 ]
{
	ai_stand();
};

void() dog_howl_newmodel33 = [ 172, dog_howl_newmodel34 ]
{
	ai_stand();
};

void() dog_howl_newmodel34 = [ 173, dog_howl_newmodel35 ]
{
	ai_stand();
};

void() dog_howl_newmodel35 = [ 174, dog_howl_newmodel36 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel36 = [ 175, dog_howl_newmodel37 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel37 = [ 176, dog_howl_newmodel38 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel38 = [ 177, dog_howl_newmodel39 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel39 = [ 178, dog_howl_newmodel40 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel40 = [ 179, dog_howl_newmodel41 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel41 = [ 180, dog_howl_newmodel42 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel42 = [ 181, dog_stand_newmodel40 ]
{
	ai_stand();
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel1a = [ 140, dog_howl_newmodel2a ]
{
	ai_walk(0);
	self.nextthink = (time + 0.06);
};

void() dog_howl_newmodel2a = [ 141, dog_howl_newmodel3a ]
{
	ai_walk(0);
	self.nextthink = (time + 0.06);
};

void() dog_howl_newmodel3a = [ 142, dog_howl_newmodel4a ]
{
	ai_walk(0);
	self.nextthink = (time + 0.06);
};

void() dog_howl_newmodel4a = [ 143, dog_howl_newmodel5a ]
{
	ai_walk(0);
	self.nextthink = (time + 0.06);
};

void() dog_howl_newmodel5a = [ 144, dog_howl_newmodel6a ]
{
	ai_walk(0);
	self.nextthink = (time + 0.06);
};

void() dog_howl_newmodel6a = [ 145, dog_howl_newmodel7a ]
{
	ai_walk(0);
	sound7(self, CHAN_VOICE, "dog/howl.wav", 1, ATTN_IDLE, SNDSPD);
};

void() dog_howl_newmodel7a = [ 146, dog_howl_newmodel8a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel8a = [ 147, dog_howl_newmodel9a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel9a = [ 148, dog_howl_newmodel10a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel10a = [ 149, dog_howl_newmodel11a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel11a = [ 150, dog_howl_newmodel12a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel12a = [ 151, dog_howl_newmodel13a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel13a = [ 152, dog_howl_newmodel14a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel14a = [ 153, dog_howl_newmodel15a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel15a = [ 154, dog_howl_newmodel16a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel16a = [ 155, dog_howl_newmodel17a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel17a = [ 156, dog_howl_newmodel18a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel18a = [ 157, dog_howl_newmodel19a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel19a = [ 158, dog_howl_newmodel20a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel20a = [ 159, dog_howl_newmodel21a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel21a = [ 160, dog_howl_newmodel22a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel22a = [ 161, dog_howl_newmodel23a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel23a = [ 162, dog_howl_newmodel24a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel24a = [ 163, dog_howl_newmodel25a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel25a = [ 164, dog_howl_newmodel26a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel26a = [ 165, dog_howl_newmodel27a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel27a = [ 166, dog_howl_newmodel28a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel28a = [ 167, dog_howl_newmodel29a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel29a = [ 167, dog_howl_newmodel30a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel30a = [ 169, dog_howl_newmodel31a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel31a = [ 170, dog_howl_newmodel32a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel32a = [ 171, dog_howl_newmodel33a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel33a = [ 172, dog_howl_newmodel34a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel34a = [ 173, dog_howl_newmodel35a ]
{
	ai_walk(0);
};

void() dog_howl_newmodel35a = [ 174, dog_howl_newmodel36a ]
{
	ai_walk(0);
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel36a = [ 175, dog_howl_newmodel37a ]
{
	ai_walk(0);
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel37a = [ 176, dog_howl_newmodel38a ]
{
	ai_walk(0);
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel38a = [ 177, dog_howl_newmodel39a ]
{
	ai_walk(0);
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel39a = [ 178, dog_howl_newmodel40a ]
{
	ai_walk(0);
	self.nextthink = (time + 0.05);
};

void() dog_howl_newmodel40a = [ 179, dog_walk7 ]
{
	ai_walk(0);
	self.nextthink = (time + 0.05);
};

void() dog_bark_newmodel1 = [ 182, dog_bark_newmodel2 ]
{
	ai_stand();
};

void() dog_bark_newmodel2 = [ 183, dog_bark_newmodel3 ]
{
	ai_stand();
};

void() dog_bark_newmodel3 = [ 184, dog_bark_newmodel4 ]
{
	ai_stand();
	sound7(self, CHAN_AUTO, "dog/bark.wav", 1, ATTN_IDLE, SNDSPD);
};

void() dog_bark_newmodel4 = [ 185, dog_bark_newmodel5 ]
{
	ai_stand();
};

void() dog_bark_newmodel5 = [ 186, dog_bark_newmodel6 ]
{
	ai_stand();
};

void() dog_bark_newmodel6 = [ 187, dog_bark_newmodel7 ]
{
	ai_stand();
};

void() dog_bark_newmodel7 = [ 188, dog_bark_newmodel8 ]
{
	ai_stand();
	sound7(self, CHAN_AUTO, "dog/bark.wav", 1, ATTN_IDLE, SNDSPD);
};

void() dog_bark_newmodel8 = [ 189, dog_bark_newmodel9 ]
{
	ai_stand();
};

void() dog_bark_newmodel9 = [ 190, dog_bark_newmodel10 ]
{
	ai_stand();
};

void() dog_bark_newmodel10 = [ 191, dog_bark_newmodel11 ]
{
	ai_stand();
};

void() dog_bark_newmodel11 = [ 192, dog_stand_newmodel40 ]
{
	ai_stand();
};

void() dog_bark_newmodel1a = [ 182, dog_bark_newmodel2a ]
{
	ai_walk(0);
};

void() dog_bark_newmodel2a = [ 183, dog_bark_newmodel3a ]
{
	ai_walk(0);
};

void() dog_bark_newmodel3a = [ 184, dog_bark_newmodel4a ]
{
	ai_walk(0);
	sound7(self, CHAN_AUTO, "dog/bark.wav", 1, ATTN_IDLE, SNDSPD);
};

void() dog_bark_newmodel4a = [ 185, dog_bark_newmodel5a ]
{
	ai_walk(0);
};

void() dog_bark_newmodel5a = [ 186, dog_bark_newmodel6a ]
{
	ai_walk(0);
};

void() dog_bark_newmodel6a = [ 187, dog_bark_newmodel7a ]
{
	ai_walk(0);
};

void() dog_bark_newmodel7a = [ 188, dog_bark_newmodel8a ]
{
	ai_walk(0);
	sound7(self, CHAN_AUTO, "dog/bark.wav", 1, ATTN_IDLE, SNDSPD);
};

void() dog_bark_newmodel8a = [ 189, dog_bark_newmodel9a ]
{
	ai_walk(0);
};

void() dog_bark_newmodel9a = [ 190, dog_bark_newmodel10a ]
{
	ai_walk(0);
};

void() dog_bark_newmodel10a = [ 191, dog_bark_newmodel11a ]
{
	ai_walk(0);
};

void() dog_bark_newmodel11a = [ 192, dog_walk7 ]
{
	ai_walk(0);
};

void() dog_stand_newmodel1 = [ 100, dog_stand_newmodel2 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel2 = [ 101, dog_stand_newmodel3 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel3 = [ 102, dog_stand_newmodel4 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel4 = [ 103, dog_stand_newmodel5 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel5 = [ 104, dog_stand_newmodel6 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
	if ((random() <= 0.27))
	{
		if ((random() <= 0.5))
		{
			sound7(self, CHAN_VOICE, "dog/growla.wav", 1, ATTN_IDLE, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "dog/growlb.wav", 1, ATTN_IDLE, SNDSPD);
		}
	}
};

void() dog_stand_newmodel6 = [ 105, dog_stand_newmodel7 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel7 = [ 106, dog_stand_newmodel8 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel8 = [ 107, dog_stand_newmodel9 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel9 = [ 108, dog_stand_newmodel10 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel10 = [ 109, dog_stand_newmodel11 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel11 = [ 110, dog_stand_newmodel12 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel12 = [ 111, dog_stand_newmodel13 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel13 = [ 112, dog_stand_newmodel14 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel14 = [ 113, dog_stand_newmodel15 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel15 = [ 114, dog_stand_newmodel16 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel16 = [ 115, dog_stand_newmodel17 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel17 = [ 116, dog_stand_newmodel18 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel18 = [ 117, dog_stand_newmodel19 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel19 = [ 118, dog_stand_newmodel20 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel20 = [ 119, dog_stand_newmodel21 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel21 = [ 120, dog_stand_newmodel22 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel22 = [ 121, dog_stand_newmodel23 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel23 = [ 122, dog_stand_newmodel24 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel24 = [ 123, dog_stand_newmodel25 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel25 = [ 124, dog_stand_newmodel26 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel26 = [ 125, dog_stand_newmodel27 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel27 = [ 126, dog_stand_newmodel28 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel28 = [ 127, dog_stand_newmodel29 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel29 = [ 128, dog_stand_newmodel30 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel30 = [ 129, dog_stand_newmodel31 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel31 = [ 130, dog_stand_newmodel32 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel32 = [ 131, dog_stand_newmodel33 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel33 = [ 132, dog_stand_newmodel34 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel34 = [ 133, dog_stand_newmodel35 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel35 = [ 134, dog_stand_newmodel36 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel36 = [ 135, dog_stand_newmodel37 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel37 = [ 136, dog_stand_newmodel38 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel38 = [ 137, dog_stand_newmodel39 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand_newmodel39 = [ 138, dog_stand_newmodel40 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
	if ((random() <= 0.1))
	{
		if ((random() <= 0.666))
		{
			dog_bark_newmodel1();
		}
		else
		{
			dog_howl_newmodel1();
		}
	}
};

void() dog_stand_newmodel40 = [ 139, dog_stand_newmodel1 ]
{
	ai_stand();
	self.nextthink = (time + 0.06);
};

void() dog_stand1 = [ 69, dog_stand2 ]
{
	ai_stand();
	self.nextthink = (time + 0.15);
};

void() dog_stand2 = [ 70, dog_stand3 ]
{
	ai_stand();
	self.nextthink = (time + 0.15);
};

void() dog_stand3 = [ 71, dog_stand4 ]
{
	ai_stand();
	self.nextthink = (time + 0.15);
};

void() dog_stand4 = [ 72, dog_stand5 ]
{
	ai_stand();
	self.nextthink = (time + 0.15);
	if ((random() <= 0.2))
	{
		if ((random() <= 0.5))
		{
			sound7(self, CHAN_VOICE, "dog/growla.wav", 1, ATTN_IDLE, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "dog/growlb.wav", 1, ATTN_IDLE, SNDSPD);
		}
	}
};

void() dog_stand5 = [ 73, dog_stand6 ]
{
	ai_stand();
	self.nextthink = (time + 0.15);
};

void() dog_stand6 = [ 74, dog_stand7 ]
{
	ai_stand();
	self.nextthink = (time + 0.15);
};

void() dog_stand7 = [ 75, dog_stand8 ]
{
	ai_stand();
	self.nextthink = (time + 0.15);
};

void() dog_stand8 = [ 76, dog_stand9 ]
{
	ai_stand();
	self.nextthink = (time + 0.15);
};

void() dog_stand9 = [ 77, dog_stand1 ]
{
	ai_stand();
	self.nextthink = (time + 0.15);
};

void() dog_walk1 = [ 78, dog_walk2 ]
{
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "dog/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	ai_walk(8);
	dog_footsteps(0.5);
};

void() dog_walk2 = [ 79, dog_walk3 ]
{
	ai_walk(8);
};

void() dog_walk3 = [ 80, dog_walk4 ]
{
	ai_walk(8);
	dog_footsteps(0.5);
	if ((self.monstermodel == 2))
	{
		if ((random() <= 0.05))
		{
			if ((random() <= 0.666))
			{
				dog_bark_newmodel1a();
			}
			else
			{
				dog_howl_newmodel1a();
			}
		}
	}
};

void() dog_walk4 = [ 81, dog_walk5 ]
{
	ai_walk(8);
};

void() dog_walk5 = [ 82, dog_walk6 ]
{
	ai_walk(8);
	dog_footsteps(0.5);
};

void() dog_walk6 = [ 83, dog_walk7 ]
{
	ai_walk(8);
};

void() dog_walk7 = [ 84, dog_walk8 ]
{
	ai_walk(8);
	dog_footsteps(0.5);
};

void() dog_walk8 = [ 85, dog_walk1 ]
{
	ai_walk(8);
};

void() dog_run1 = [ 48, dog_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "dog/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	ai_run(16);
};

void() dog_run2 = [ 49, dog_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(32);
	dog_footsteps(0.8);
};

void() dog_run3 = [ 50, dog_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(32);
};

void() dog_run4 = [ 51, dog_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(20);
};

void() dog_run5 = [ 52, dog_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(64);
	dog_footsteps(0.9);
};

void() dog_run6 = [ 53, dog_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(32);
};

void() dog_run7 = [ 54, dog_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() dog_run8 = [ 55, dog_run9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(32);
	dog_footsteps(0.7);
};

void() dog_run9 = [ 56, dog_run10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(32);
};

void() dog_run10 = [ 57, dog_run11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(20);
};

void() dog_run11 = [ 58, dog_run12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(64);
	dog_footsteps(0.8);
};

void() dog_run12 = [ 59, dog_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(32);
};

void() dog_atta1 = [ 0, dog_atta2 ]
{
	ai_charge(10);
};

void() dog_atta2 = [ 1, dog_atta3 ]
{
	ai_charge(10);
};

void() dog_atta3 = [ 2, dog_atta4 ]
{
	ai_charge(10);
};

void() dog_atta4 = [ 3, dog_atta5 ]
{
	sound7(self, CHAN_VOICE, "dog/dattack1.wav", 1, ATTN_NORM, SNDSPD);
	dog_bite();
};

void() dog_atta5 = [ 4, dog_atta6 ]
{
	ai_charge(10);
};

void() dog_atta6 = [ 5, dog_atta7 ]
{
	ai_charge(10);
};

void() dog_atta7 = [ 6, dog_atta8 ]
{
	ai_charge(10);
	dog_footsteps(0.6);
};

void() dog_atta8 = [ 7, dog_run1 ]
{
	ai_charge(10);
};

void() dog_leap1 = [ 60, dog_leap2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() dog_leap2 = [ 61, dog_leap3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	self.attack_timer = 0;
	self.touch = Dog_JumpTouch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 300) + '0 0 200');
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
};

void() dog_leap3 = [ 62, dog_leap4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dog_leap4 = [ 63, dog_leap5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dog_leap5 = [ 64, dog_leap6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dog_leap6 = [ 65, dog_leap7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dog_leap7 = [ 66, dog_leap8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dog_leap8 = [ 67, dog_leap9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	dog_footsteps(1);
};

void() dog_leap9 = [ 68, dog_leap9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
};

void() dog_pain1 = [ 26, dog_pain2 ]
{
};

void() dog_pain2 = [ 27, dog_pain3 ]
{
};

void() dog_pain3 = [ 28, dog_pain4 ]
{
};

void() dog_pain4 = [ 29, dog_pain5 ]
{
};

void() dog_pain5 = [ 30, dog_pain6 ]
{
};

void() dog_pain6 = [ 31, dog_run1 ]
{
	dog_footsteps(0.6);
};

void() dog_painb1 = [ 32, dog_painb2 ]
{
};

void() dog_painb2 = [ 33, dog_painb3 ]
{
};

void() dog_painb3 = [ 34, dog_painb4 ]
{
	ai_pain(4);
};

void() dog_painb4 = [ 35, dog_painb5 ]
{
	ai_pain(12);
};

void() dog_painb5 = [ 36, dog_painb6 ]
{
	ai_pain(12);
};

void() dog_painb6 = [ 37, dog_painb7 ]
{
	ai_pain(2);
};

void() dog_painb7 = [ 38, dog_painb8 ]
{
};

void() dog_painb8 = [ 39, dog_painb9 ]
{
	ai_pain(4);
};

void() dog_painb9 = [ 40, dog_painb10 ]
{
};

void() dog_painb10 = [ 41, dog_painb11 ]
{
	ai_pain(10);
};

void() dog_painb11 = [ 42, dog_painb12 ]
{
};

void() dog_painb12 = [ 43, dog_painb13 ]
{
};

void() dog_painb13 = [ 44, dog_painb14 ]
{
	dog_footsteps(0.6);
};

void() dog_painb14 = [ 45, dog_painb15 ]
{
};

void() dog_painb15 = [ 46, dog_painb16 ]
{
};

void() dog_painb16 = [ 47, dog_run1 ]
{
};

void() dog_pain =
{
	sound7(self, CHAN_VOICE, "dog/dpain1.wav", 1, ATTN_NORM, SNDSPD);
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_dog * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	if ((random() > 0.5))
	{
		dog_pain1();
	}
	else
	{
		dog_painb1();
	}
};

void() dog_dieburn1 = [ 8, dog_dieburn2 ]
{
	self.burnz_origin = 10;
	burn_toggle_allround();
};

void() dog_dieburn2 = [ 9, dog_dieburn3 ]
{
	self.burnz_origin = 8;
};

void() dog_dieburn3 = [ 10, dog_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
};

void() dog_dieburn4 = [ 11, dog_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() dog_dieburn5 = [ 12, dog_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() dog_dieburn6 = [ 13, dog_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() dog_dieburn7 = [ 14, dog_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() dog_dieburn8 = [ 15, dog_dieburn9 ]
{
	self.burnz_origin = -6;
};

void() dog_dieburn9 = [ 16, dog_dieburn9 ]
{
	self.burnz_origin = -9;
};

void() dog_dieax1 = [ 86, dog_dieax2 ]
{
	makevectors(self.angles);
	self.fangle = v_forward;
	self.rangle = v_right;
};

void() dog_dieax2 = [ 87, dog_dieax3 ]
{
	sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", (self.origin + ((self.fangle * 18) + (self.rangle * 18))), VEC_ORIGIN, 1);
	}
};

void() dog_dieax3 = [ 88, dog_dieax4 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", (self.origin + ((self.fangle * 18) + (self.rangle * 18))), VEC_ORIGIN, 1);
	}
};

void() dog_dieax4 = [ 89, dog_dieax5 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", (self.origin + ((self.fangle * 18) + (self.rangle * 18))), VEC_ORIGIN, 1);
	}
};

void() dog_dieax5 = [ 90, dog_dieax6 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() dog_dieax6 = [ 91, dog_dieax7 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", (self.origin + ((self.fangle * 18) + (self.rangle * 18))), VEC_ORIGIN, 1);
	}
};

void() dog_dieax7 = [ 92, dog_dieax8 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", (self.origin + ((self.fangle * 18) + (self.rangle * 18))), VEC_ORIGIN, 1);
	}
};

void() dog_dieax8 = [ 93, dog_dieax9 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", (self.origin + ((self.fangle * 18) + (self.rangle * 18))), VEC_ORIGIN, 1);
	}
};

void() dog_dieax9 = [ 94, dog_dieax10 ]
{
};

void() dog_dieax10 = [ 95, dog_dieax11 ]
{
};

void() dog_dieax11 = [ 96, dog_dieax12 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", (self.origin + ((self.fangle * 18) + (self.rangle * 18))), VEC_ORIGIN, 1);
	}
};

void() dog_dieax12 = [ 97, dog_dieax13 ]
{
};

void() dog_dieax13 = [ 98, dog_dieax14 ]
{
	if ((autocvar_dogcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	CopyMonsterToBodyQue(autocvar_dogcorpsehealth, "progs/h_dog.mdl");
};

void() dog_dieax14 = [ 99, dog_dieax14 ]
{
};

void() dog_die1 = [ 8, dog_die2 ]
{
};

void() dog_die2 = [ 9, dog_die3 ]
{
};

void() dog_die3 = [ 10, dog_die4 ]
{
};

void() dog_die4 = [ 11, dog_die5 ]
{
};

void() dog_die5 = [ 12, dog_die6 ]
{
};

void() dog_die6 = [ 13, dog_die7 ]
{
};

void() dog_die7 = [ 14, dog_die8 ]
{
};

void() dog_die8 = [ 15, dog_die9 ]
{
};

void() dog_die9 = [ 16, dog_die9 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 20;
	if ((autocvar_dogcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_dogcorpsehealth, "progs/h_dog.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_dogcorpsehealth, "progs/h_dog1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_dogcorpsehealth, "progs/h_dog_extended.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_dograndomness = autocvar_dograndomness * 0.01;
		if ((autocvar_dog == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_dograndomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_dog == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_dograndomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/dog.mdl", 16, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/dog1.mdl", 16, zet);
						}
						else
						{
							if ((self.monstermodel == 2))
							{
								soul("progs/dog_extended.mdl", 16, zet);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_dog == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_dograndomness))
					{
						vengeance_dog("progs/dog.mdl", 16);
					}
				}
				else
				{
					if ((autocvar_dog == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_dograndomness))
						{
							zufall = random();
							if ((zufall > 0.64))
							{
								ghost_die();
							}
							else
							{
								if ((zufall < 0.26))
								{
									if ((self.monstermodel == 0))
									{
										soul("progs/dog.mdl", 16, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/dog1.mdl", 16, zet);
										}
										else
										{
											if ((self.monstermodel == 2))
											{
												soul("progs/dog_extended.mdl", 16, zet);
											}
										}
									}
								}
								else
								{
								}
							}
						}
					}
					else
					{
					}
				}
			}
		}
	}
};

void() dog_dieb1 = [ 17, dog_dieb2 ]
{
};

void() dog_dieb2 = [ 18, dog_dieb3 ]
{
};

void() dog_dieb3 = [ 19, dog_dieb4 ]
{
};

void() dog_dieb4 = [ 20, dog_dieb5 ]
{
};

void() dog_dieb5 = [ 21, dog_dieb6 ]
{
};

void() dog_dieb6 = [ 22, dog_dieb7 ]
{
};

void() dog_dieb7 = [ 23, dog_dieb8 ]
{
};

void() dog_dieb8 = [ 24, dog_dieb9 ]
{
};

void() dog_dieb9 = [ 25, dog_dieb9 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 20;
	if ((autocvar_dogcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_dogcorpsehealth, "progs/h_dog.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_dogcorpsehealth, "progs/h_dog1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(autocvar_dogcorpsehealth, "progs/h_dog_extended.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_dograndomness = autocvar_dograndomness * 0.01;
		if ((autocvar_dog == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_dograndomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_dog == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_dograndomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/dog.mdl", 25, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/dog1.mdl", 25, zet);
						}
						else
						{
							if ((self.monstermodel == 2))
							{
								soul("progs/dog_extended.mdl", 25, zet);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_dog == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_dograndomness))
					{
						vengeance_dog("progs/dog.mdl", 25);
					}
				}
				else
				{
					if ((autocvar_dog == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_dograndomness))
						{
							zufall = random();
							if ((zufall > 0.64))
							{
								ghost_die();
							}
							else
							{
								if ((zufall < 0.26))
								{
									if ((self.monstermodel == 0))
									{
										soul("progs/dog.mdl", 25, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/dog1.mdl", 25, zet);
										}
										else
										{
											if ((self.monstermodel == 2))
											{
												soul("progs/dog_extended.mdl", 25, zet);
											}
										}
									}
								}
								else
								{
								}
							}
						}
					}
					else
					{
					}
				}
			}
		}
	}
};

void(float maxgibs, float gibscounter) producegibs_dog =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/gib_4.mdl", self.health);
		ThrowGib("progs/gib_5.mdl", self.health);
		ThrowGib("progs/gib_4.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_dog(maxgibs, gibscounter);
};

void() dog_lightning_death = [ 6, dog_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() dog_lightning_death1 = [ 6, dog_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(1, "progs/h_dog.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(1, "progs/h_dog1.mdl");
	}
	if ((self.monstermodel == 2))
	{
		CopyMonsterToBodyQue(1, "progs/h_dog_extended.mdl");
	}
};

void() dog_inflamed1 = [ 48, dog_inflamed2 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.09);
	if ((random() < 0.75))
	{
		sound7(self, CHAN_VOICE, "dog/dpain1.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() dog_inflamed2 = [ 49, dog_inflamed3 ]
{
	ai_run_inflamed(32);
	dog_footsteps(0.8);
	self.nextthink = (time + 0.09);
};

void() dog_inflamed3 = [ 50, dog_inflamed4 ]
{
	ai_run_inflamed(32);
	self.nextthink = (time + 0.09);
};

void() dog_inflamed4 = [ 51, dog_inflamed5 ]
{
	ai_run_inflamed(20);
	self.nextthink = (time + 0.09);
};

void() dog_inflamed5 = [ 52, dog_inflamed6 ]
{
	ai_run_inflamed(64);
	dog_footsteps(0.9);
	self.nextthink = (time + 0.09);
};

void() dog_inflamed6 = [ 53, dog_inflamed7 ]
{
	ai_run_inflamed(32);
	self.nextthink = (time + 0.09);
};

void() dog_inflamed7 = [ 54, dog_inflamed8 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.09);
	if ((random() < 0.5))
	{
		dog_inflamed13();
	}
};

void() dog_inflamed8 = [ 55, dog_inflamed9 ]
{
	ai_run_inflamed(32);
	dog_footsteps(0.7);
	self.nextthink = (time + 0.09);
};

void() dog_inflamed9 = [ 56, dog_inflamed10 ]
{
	ai_run_inflamed(32);
	self.nextthink = (time + 0.09);
};

void() dog_inflamed10 = [ 57, dog_inflamed11 ]
{
	ai_run_inflamed(20);
	self.nextthink = (time + 0.09);
};

void() dog_inflamed11 = [ 58, dog_inflamed12 ]
{
	ai_run_inflamed(64);
	dog_footsteps(0.8);
	self.nextthink = (time + 0.09);
};

void() dog_inflamed12 = [ 59, dog_inflamed1 ]
{
	ai_run_inflamed(32);
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		dog_die();
		return;
	}
};

void() dog_inflamed13 = [ 26, dog_inflamed14 ]
{
	self.nextthink = (time + 0.09);
};

void() dog_inflamed14 = [ 27, dog_inflamed15 ]
{
	self.nextthink = (time + 0.09);
};

void() dog_inflamed15 = [ 28, dog_inflamed16 ]
{
	self.nextthink = (time + 0.09);
	if ((random() < 0.8))
	{
		sound7(self, CHAN_VOICE, "dog/dpain1.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() dog_inflamed16 = [ 29, dog_inflamed17 ]
{
	self.nextthink = (time + 0.09);
};

void() dog_inflamed17 = [ 30, dog_inflamed18 ]
{
	self.nextthink = (time + 0.09);
};

void() dog_inflamed18 = [ 31, dog_inflamed8 ]
{
	dog_footsteps(0.6);
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		dog_die();
		return;
	}
};

void() dog_die =
{
	local float maxgibs;
	local float gibscounter;
	local float zufa;
	local float zufall;
	local float randomness;

	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			dog_lightning_death();
			return;
		}
	}
	else
	{
		if ((((!self.shocked && (self.enemy.weapon == IT_LIGHTNING)) && (self.sticky != 1)) && (self.enemy.meleeing == 0)))
		{
			lg_death1();
			return;
		}
	}
	if (((self.health < -35) || (self.enemy.weapon == IT_CHAINSAW)))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_dog * 0.01)))
			{
				the_matrix = 1;
				SNDSPD = 70;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		play_gibsound();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		if ((autocvar_gibsmultiplier == 1))
		{
			if ((self.monstermodel == 0))
			{
				ThrowHead("progs/h_dog.mdl", self.health);
			}
			else
			{
				if ((self.monstermodel == 1))
				{
					ThrowHead("progs/h_dog1.mdl", self.health);
				}
				else
				{
					if ((self.monstermodel == 2))
					{
						ThrowHead("progs/h_dog_extended.mdl", self.health);
					}
				}
			}
			ThrowGib("progs/gib3.mdl", self.health);
			ThrowGib("progs/gib_dogleg.mdl", self.health);
			ThrowGib("progs/gib_dogleg.mdl", self.health);
			if ((autocvar_heartgib >= 1))
			{
				ThrowHeart("progs/gibheart.mdl", self.health);
			}
			gibdeath_effects();
			return;
		}
		else
		{
			if ((self.monstermodel == 0))
			{
				ThrowHead("progs/h_dog.mdl", self.health);
			}
			else
			{
				if ((self.monstermodel == 1))
				{
					ThrowHead("progs/h_dog1.mdl", self.health);
				}
				else
				{
					if ((self.monstermodel == 2))
					{
						ThrowHead("progs/h_dog_extended.mdl", self.health);
					}
				}
			}
			if ((autocvar_heartgib >= 1))
			{
				ThrowHeart("progs/gibheart.mdl", self.health);
			}
			maxgibs = autocvar_gibsmultiplier;
			gibscounter = 0;
			if ((autocvar_bloodextension == 1))
			{
				pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
			}
			producegibs_dog(maxgibs, gibscounter);
			return;
		}
	}
	if (autocvar_burning_monsters_death_animation)
	{
		if ((self.inflamed == 0))
		{
			zufa = random() * 100;
			if ((((((self.enemy.weapon == IT_GRENADE_LAUNCHER) || (self.enemy.weapon == IT_ROCKET_LAUNCHER)) && (zufa <= autocvar_burning_monsters_death_animation)) && (self.watertype != CONTENT_WATER)) && (self.enemy.meleeing == 0)))
			{
				self.delete_painskin = 1;
				self.inflamed = 1;
				self.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
				self.inflametime = ((time + autocvar_burning_monsters_death_animation_time) + random());
				dog_inflamed1();
				return;
			}
		}
		else
		{
			sound7(self, CHAN_VOICE, "dog/ddeath.wav", 1, ATTN_NORM, SNDSPD);
			self.solid = 0;
			if ((random() > 0.5))
			{
				dog_die1();
			}
			else
			{
				dog_dieb1();
			}
			return;
		}
	}
	autocvar_dograndomness = autocvar_dograndomness * 0.01;
	if ((autocvar_dog == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_dograndomness))
		{
			self.delete_painskin = 1;
			dog_dieburn1();
			return;
		}
	}
	if ((autocvar_dog == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_dograndomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				dog_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_dog * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "dog/ddeath.wav", 1, ATTN_NORM, SNDSPD);
	self.solid = 0;
	if ((random() > 0.5))
	{
		dog_die1();
	}
	else
	{
		dog_dieb1();
	}
	if ((self.enemy.meleeing == 0))
	{
		if ((self.enemy.weapon == IT_AXE))
		{
			if (((random() < 0.5) && (random() < 0.9)))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				self.model = "progs/dogaxe.mdl";
				setmodel(self, "progs/dogaxe.mdl");
				dog_dieax1();
				ThrowGib("progs/chop.mdl", self.health);
			}
		}
	}
};

float() CheckDogMelee =
{
	if ((enemy_range == RANGE_MELEE))
	{
		self.attack_state = AS_MELEE;
		return (TRUE);
	}
	return (0);
};

float() CheckDogJump =
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
	if ((d < 80))
	{
		return (0);
	}
	if ((d > 150))
	{
		return (0);
	}
	return (TRUE);
};

float() DogCheckAttack =
{
	if (CheckDogMelee())
	{
		self.attack_state = AS_MELEE;
		return (TRUE);
	}
	if (CheckDogJump())
	{
		self.attack_state = AS_MISSILE;
		return (TRUE);
	}
	return (0);
};

void() monster_dog =
{
	local float zufall;
	local float new_dog;
	local float zuffa;
	local float replacer;
	local vector check;
	local float replacez;
	local float replac;
	local entity pain_skin_entity;
	local float replacce;
	local float replace;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/h_dog.mdl");
	precache_model("progs/dog.mdl");
	precache_model("progs/gib_dogleg.mdl");
	precache_model("progs/dogaxe.mdl");
	precache_sound("dog/dattack1.wav");
	precache_sound("dog/ddeath.wav");
	precache_sound("dog/dpain1.wav");
	precache_sound("dog/dsight.wav");
	precache_sound("dog/idle.wav");
	precache_sound("dog/bark.wav");
	precache_sound("dog/howl.wav");
	precache_sound("dog/growla.wav");
	precache_sound("dog/growlb.wav");
	precache_sound("walk/dog1.wav");
	precache_sound("walk/dog2.wav");
	precache_sound("walk/dog3.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.netname = "monster_dog";
	if ((autocvar_dogmultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/dog.mdl");
		zufall = random();
		if ((zufall >= 0.5))
		{
			self.skin = 0;
			self.monsterskin = 0;
			self.monstermodel = 0;
		}
		else
		{
			self.skin = 1;
			self.monsterskin = 1;
			self.monstermodel = 0;
		}
	}
	else
	{
		if ((autocvar_dogmultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/dog1.mdl");
			precache_model("progs/h_dog1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/dog.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/dog1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_dogmultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/dog1.mdl");
				precache_model("progs/h_dog1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/dog.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/dog.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/dog1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_dogmultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/dog1.mdl");
					precache_model("progs/h_dog1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/dog.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/dog.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/dog1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/dog1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/dog.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if (autocvar_dog_extended_newmodel)
	{
		new_dog = autocvar_dog_extended_newmodel * 0.01;
		if ((random() < new_dog))
		{
			precache_model("progs/dog_extended.mdl");
			precache_model("progs/h_dog_extended.mdl");
			setmodel(self, "progs/dog_extended.mdl");
			zufall = random();
			if ((zufall > 0.5))
			{
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 2;
			}
			else
			{
				self.skin = 1;
				self.monsterskin = 1;
				self.monstermodel = 2;
			}
		}
	}
	if ((autocvar_dog_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.14;
			self.sizediff = '0 0 3';
			setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.07;
				self.sizediff = '0 0 1';
				setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
			}
			else
			{
				self.scale = 1;
				setsize(self, DOG_MIN, DOG_MAX);
			}
		}
	}
	else
	{
		if ((autocvar_dog_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.21;
				self.sizediff = '0 0 5';
				setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.14;
					self.sizediff = '0 0 3';
					setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.75))
					{
						self.scale = 1.07;
						self.sizediff = '0 0 1';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, DOG_MIN, DOG_MAX);
					}
				}
			}
		}
		else
		{
			if ((autocvar_dog_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.28;
					self.sizediff = '0 0 7';
					setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.21;
						self.sizediff = '0 0 5';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.14;
							self.sizediff = '0 0 3';
							setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.07;
								self.sizediff = '0 0 1';
								setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
							}
							else
							{
								self.scale = 1;
								setsize(self, DOG_MIN, DOG_MAX);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_dog_size == 4))
				{
					zuffa = random();
					if ((zuffa <= 0.17))
					{
						self.scale = 1.35;
						self.sizediff = '0 0 9';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.34))
						{
							self.scale = 1.28;
							self.sizediff = '0 0 7';
							setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.5))
							{
								self.scale = 1.21;
								self.sizediff = '0 0 5';
								setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
							}
							else
							{
								if ((zuffa <= 0.67))
								{
									self.scale = 1.14;
									self.sizediff = '0 0 3';
									setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
								}
								else
								{
									if ((zuffa <= 0.84))
									{
										self.scale = 1.07;
										self.sizediff = '0 0 1';
										setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
									}
									else
									{
										self.scale = 1;
										setsize(self, DOG_MIN, DOG_MAX);
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_dog_size > 4))
					{
						if ((autocvar_dog_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_dog_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_dog_size * 0.25);
						self.sizediff = self.sizefactor;
						setsize(self, (VEC_HULL2_MIN - self.sizediff), ('32 32 40' - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, DOG_MIN, DOG_MAX);
					}
				}
			}
		}
	}
	if ((autocvar_dog_size_influenced_health == 1))
	{
		self.health = (autocvar_dog_health + ((self.scale - 1) * 100));
	}
	else
	{
		self.health = autocvar_dog_health;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_dog_random_skin_colors))
	{
		self.colormod_x = random();
		if ((self.colormod_x < 0.5))
		{
			self.colormod_x = (self.colormod_x + 0.5);
		}
		if ((autocvar_monster_random_skin_color_alteration == 1))
		{
			if ((self.colormod_x < 0.75))
			{
				self.colormod_x = (self.colormod_x + 0.25);
			}
		}
		else
		{
			if ((autocvar_monster_random_skin_color_alteration == 2))
			{
				if ((self.colormod_x < 0.65))
				{
					self.colormod_x = (self.colormod_x + 0.25);
				}
			}
			else
			{
				if ((self.colormod_x < 0.55))
				{
					self.colormod_x = (self.colormod_x + 0.25);
				}
			}
		}
		self.colormod_y = random();
		if ((self.colormod_y < 0.5))
		{
			self.colormod_y = (self.colormod_y + 0.5);
		}
		if ((autocvar_monster_random_skin_color_alteration == 1))
		{
			if ((self.colormod_y < 0.75))
			{
				self.colormod_y = (self.colormod_y + 0.25);
			}
		}
		else
		{
			if ((autocvar_monster_random_skin_color_alteration == 2))
			{
				if ((self.colormod_y < 0.65))
				{
					self.colormod_y = (self.colormod_y + 0.25);
				}
			}
			else
			{
				if ((self.colormod_y < 0.55))
				{
					self.colormod_y = (self.colormod_y + 0.25);
				}
			}
		}
		self.colormod_z = random();
		if ((self.colormod_z < 0.5))
		{
			self.colormod_z = (self.colormod_z + 0.5);
		}
		if ((autocvar_monster_random_skin_color_alteration == 1))
		{
			if ((self.colormod_z < 0.75))
			{
				self.colormod_z = (self.colormod_z + 0.25);
			}
		}
		else
		{
			if ((autocvar_monster_random_skin_color_alteration == 2))
			{
				if ((self.colormod_z < 0.65))
				{
					self.colormod_z = (self.colormod_z + 0.25);
				}
			}
			else
			{
				if ((self.colormod_z < 0.55))
				{
					self.colormod_z = (self.colormod_z + 0.25);
				}
			}
		}
	}
	if ((self.monstermodel == 2))
	{
		self.th_stand = dog_stand_newmodel1;
	}
	else
	{
		self.th_stand = dog_stand1;
	}
	self.th_walk = dog_walk1;
	self.th_run = dog_run1;
	self.th_pain = dog_pain;
	self.th_die = dog_die;
	self.th_melee = dog_atta1;
	self.th_missile = dog_leap1;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_spider_replace_dog)
	{
		replacer = autocvar_spider_replace_dog * 0.01;
		if ((random() <= replacer))
		{
			check = (self.origin - '0 0 20') + '0 0 1';
			if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
			{
				self.skin = 7;
				self.health = autocvar_dog_health;
				self.scale = 1;
				setsize(self, VEC_HULL2_MIN, '32 32 40');
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_spider_start();
				return;
			}
		}
	}
	if (autocvar_reiver_replace_dog)
	{
		replacez = autocvar_reiver_replace_dog * 0.01;
		if ((random() <= replacez))
		{
			self.health = (autocvar_dog_health + 25);
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, '32 32 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_reiver_liftorigin_start();
			return;
		}
	}
	if (autocvar_afrit_replace_dog)
	{
		replac = autocvar_afrit_replace_dog * 0.01;
		if ((random() <= replac))
		{
			self.health = autocvar_dog_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, '32 32 40');
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_afrit_liftorigin_start();
			return;
		}
	}
	if (autocvar_painskin_transparency)
	{
		pain_skin_entity = spawn();
		pain_skin_entity.solid = 0;
		pain_skin_entity.movetype = MOVETYPE_NOCLIP;
		pain_skin_entity.owner = self;
		setmodel(pain_skin_entity, self.model);
		setsize(pain_skin_entity, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		setorigin(pain_skin_entity, VEC_ORIGIN);
		pain_skin_entity.skin = self.skin;
		pain_skin_entity.colormod_x = self.colormod_x;
		pain_skin_entity.colormod_y = self.colormod_y;
		pain_skin_entity.colormod_z = self.colormod_z;
		pain_skin_entity.monstermodel = self.monstermodel;
		pain_skin_entity.frame = self.frame;
		pain_skin_entity.alpha = autocvar_painskin_transparency;
		pain_skin_entity.think = pain_skin_entity_think;
		pain_skin_entity.nextthink = time;
		setattachment(pain_skin_entity, self, /*37325i*/"test");
	}
	walkmonster_start();
	do_the_cloning();
	if (autocvar_reiver_supports_dog)
	{
		replacce = autocvar_reiver_supports_dog * 0.01;
		if ((random() <= replacce))
		{
			add_reiver_support_walk();
		}
	}
	if (autocvar_afrit_supports_dog)
	{
		replace = autocvar_afrit_supports_dog * 0.01;
		if ((random() <= replace))
		{
			add_afrit_support_walk();
		}
	}
	MonsterPhysics(self, autocvar_dogmass);
};

void() vengeance_dog_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_dog_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_dog_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog_run1 = [ 48, vengeance_dog_run2 ]
{
	ai_face();
	movetogoal(24);
	self.touch = vengeance_dog_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog_run2 = [ 49, vengeance_dog_run3 ]
{
	ai_face();
	movetogoal(40);
	self.touch = vengeance_dog_touch;
	self.alpha = 0.34;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog_run3 = [ 50, vengeance_dog_jump1 ]
{
	ai_face();
	movetogoal(40);
	self.touch = vengeance_dog_touch;
	self.alpha = 0.28;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog_jump1 = [ 60, vengeance_dog_jump2 ]
{
	ai_face();
	movetogoal(24);
	self.touch = vengeance_dog_touch;
	self.alpha = 0.22;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog_jump2 = [ 61, vengeance_dog_jump3 ]
{
	ai_face();
	movetogoal(32);
	self.touch = vengeance_dog_touch;
	sound7(self, CHAN_VOICE, "dog/dattack1.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.17;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog_jump3 = [ 62, vengeance_dog_jump4 ]
{
	ai_face();
	movetogoal(32);
	self.touch = vengeance_dog_touch;
	self.alpha = 0.12;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog_jump4 = [ 63, vengeance_dog_end1 ]
{
	ai_face();
	self.touch = vengeance_dog_touch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 210) + '0 0 70');
	self.alpha = 0.07;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog11 = [ 15, vengeance_dog12 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog12 = [ 14, vengeance_dog13 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog13 = [ 13, vengeance_dog14 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog14 = [ 12, vengeance_dog15 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog15 = [ 11, vengeance_dog16 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog16 = [ 10, vengeance_dog17 ]
{
	sound7(self, CHAN_WEAPON, "dog/dsight.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog17 = [ 9, vengeance_dog18 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog18 = [ 8, vengeance_dog_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog21 = [ 24, vengeance_dog22 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog22 = [ 23, vengeance_dog23 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog23 = [ 22, vengeance_dog24 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog24 = [ 21, vengeance_dog25 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog25 = [ 20, vengeance_dog26 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog26 = [ 19, vengeance_dog27 ]
{
	sound7(self, CHAN_WEAPON, "dog/dsight.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog27 = [ 18, vengeance_dog28 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog28 = [ 17, vengeance_dog_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_dog_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	if ((self.frame == 16))
	{
		self.think = vengeance_dog11;
	}
	else
	{
		self.think = vengeance_dog21;
	}
};

void() vengeance_dog_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_dog_bright05;
};

void() vengeance_dog_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_dog_bright04;
};

void() vengeance_dog_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_dog_bright03;
};

void() vengeance_dog_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_dog_bright02;
};

void() vengeance_dog_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_dog_bright01;
};

void(string modelname, float modelframe) vengeance_dog =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_FLY;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/dog.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/dog1.mdl");
		}
		else
		{
			if ((self.monstermodel == 2))
			{
				setmodel(self, "progs/dog_extended.mdl");
			}
		}
	}
	setsize(self, VEC_HULL2_MIN, '32 32 40');
	self.frame = modelframe;
	self.solid = 0;
	vengeance_dog_bright00();
};
