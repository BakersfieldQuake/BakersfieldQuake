//Decompiled code. Please respect the original copyright.

void() hip_powerup_touch =
{
	if ((other.classname != "player"))
	{
		return;
	}
	if ((other.health <= 0))
	{
		return;
	}
	sprint(other, "You got the ");
	sprint(other, self.netname);
	sprint(other, "\n");
	if (deathmatch)
	{
		self.mdl = self.model;
		self.nextthink = (time + 60);
		self.think = SUB_regen;
	}
	sound(other, CHAN_VOICE, self.noise, 1, ATTN_NORM);
	stuffcmd(other, "bf\n");
	self.solid = 0;
	other.items = (other.items | self.items);
	self.model = string_null;
	if (((self.classname == "item_artifact_envirosuit") && (self.dmg == 1)))
	{
		other.wetsuit_time = 1;
		other.wetsuit_finished = (time + 30);
	}
	activator = other;
	SUB_UseTargets();
};

void() item_artifact_wetsuit =
{
	self.dmg = 1;
	item_artifact_envirosuit();
};
