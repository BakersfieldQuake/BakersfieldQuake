//Decompiled code. Please respect the original copyright.

void() smokemit_think =
{
	self.frame = (self.frame + 1);
	self.ltime = (self.ltime + 1);
	self.alpha = (self.alpha - 0.05);
	self.scale = (self.scale - 0.007);
	self.velocity_z = (self.velocity_z + 6);
	self.think = sprite_smoke_think;
	self.nextthink = (time + 0.07);
	if ((self.ltime > 61))
	{
		remove(self);
	}
};

void(entity e, string spritepath, float spscale, vector pos_mod, vector startvelocity, vector velocityrandom, float startalpha) Part_Emitter =
{
	newmis = spawn();
	newmis.movetype = MOVETYPE_NOCLIP;
	newmis.solid = 0;
	newmis.owner = e;
	newmis.classname = "particle";
	setmodel(newmis, spritepath);
	newmis.scale = spscale;
	newmis.scale = (newmis.scale + ((random() * 0.2) + -0.1));
	newmis.alpha = startalpha;
	newmis.velocity = startvelocity;
	newmis.velocity_x = (newmis.velocity_x + ((random() * (velocityrandom_x - (0 - velocityrandom_x))) + (0 - velocityrandom_x)));
	newmis.velocity_y = (newmis.velocity_y + ((random() * (velocityrandom_y - (0 - velocityrandom_y))) + (0 - velocityrandom_y)));
	newmis.velocity_z = (newmis.velocity_z + ((random() * (velocityrandom_z - (0 - velocityrandom_z))) + (0 - velocityrandom_z)));
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, e.origin);
	pos_mod_x = pos_mod_x + ((random() * 5) + -2);
	pos_mod_y = pos_mod_y + ((random() * 6) + -3);
	pos_mod_z = pos_mod_z + ((random() * 12) + -6);
	newmis.origin = (newmis.origin + pos_mod);
	newmis.think = smokemit_think;
	newmis.nextthink = (time + 0.01);
};
