//Decompiled code. Please respect the original copyright.

void() finish_particle =
{
	if ((self.classtype != CT_PARTICLE))
	{
		dprint("€–¡“‘…√Ã≈ﬂ“≈‘’“Œ› This is not a particle!?!\n");
	}
	else
	{
		if ((self.owner.pemit_tcount > 0))
		{
			self.owner.pemit_tcount = (self.owner.pemit_tcount - 1);
		}
		self.velocity = VEC_ORIGIN;
		self.avelocity = VEC_ORIGIN;
		self.origin = VEC_ORIGIN;
		self.part_active = 0;
		setmodel(self, "");
		self.owner = world;
		self.flags = 0;
		self.frame = 0;
		self.skin = 0;
		self.gravity = 1;
		if ((part_total > 1))
		{
			part_total = part_total - 1;
		}
		if ((part_free.classtype != CT_PARTICLE))
		{
			dprint("€–¡“‘…√Ã≈ﬂ“≈‘’“Œ› Current free particle is wrong classtype!!\n");
		}
		else
		{
			self.entchain = part_free.entchain;
			part_free.entchain = self;
			if ((part_debug == 2))
			{
				dprint("Return Free (");
				dprint(ftos(part_free.cnt));
				dprint(") Next (");
				dprint(ftos(part_free.entchain.cnt));
				dprint(")\n");
			}
		}
	}
};

entity() fetch_particle =
{
	local entity tpart_ret;

	tpart_ret = world;
	if ((part_control.count < PARTICLE_BUFFER))
	{
		return (tpart_ret);
	}
	if ((part_debug == 1))
	{
		sprint(client_ent, "CREATE Particle (");
		sprint(client_ent, ftos(part_total));
		sprint(client_ent, "/");
		sprint(client_ent, ftos(part_max));
		sprint(client_ent, ")\n");
	}
	if ((part_total >= (part_max - 1)))
	{
		if ((part_message < time))
		{
			dprint("€–¡“‘…√Ã≈› current limit (");
			dprint(ftos(part_max));
			dprint(") too low!\n");
			part_message = time + 3;
		}
	}
	else
	{
		if ((part_free.classtype != CT_PARTICLE))
		{
			dprint("€–¡“‘…√Ã≈ﬂ∆≈‘√»› Current free particle is wrong classtype!!\n");
		}
		else
		{
			if ((part_free.entchain.classtype != CT_PARTICLE))
			{
				dprint("€–¡“‘…√Ã≈ﬂ∆≈‘√»› Next free particle is wrong classtype!!\n");
				dprint("Free (");
				dprint(ftos(part_free.cnt));
				dprint(") Ctype (");
				dprint(ftos(part_free.classtype));
				dprint(") Next (");
				dprint(ftos(part_free.entchain.cnt));
				dprint(") Ctype (");
				dprint(ftos(part_free.entchain.classtype));
				dprint(")\n");
			}
			else
			{
				tpart_ret = part_free.entchain;
				part_free.entchain = tpart_ret.entchain;
				part_total = part_total + 1;
				tpart_ret.part_active = TRUE;
				if ((part_debug == 2))
				{
					dprint("Fetch Free (");
					dprint(ftos(part_free.cnt));
					dprint(") return (");
					dprint(ftos(tpart_ret.cnt));
					dprint(")\n");
				}
			}
		}
	}
	return (tpart_ret);
};

void() generate_particlechain =
{
	local entity part_prev;
	local entity part_first;
	local float pcount;

	part = world;
	part_prev = world;
	part_first = world;
	pcount = 0;
	if (((self.count + 1) < part_max))
	{
		dprint("€–√»¡…Œ› Part bank (");
		dprint(ftos(self.count));
		dprint(" / ");
		dprint(ftos(part_max));
		dprint(")\n");
		while ((pcount < PARTICLE_BANK))
		{
			part = spawn();
			part.solid = 0;
			part.owner = world;
			part.part_active = 0;
			part.classname = "particle";
			part.classtype = CT_PARTICLE;
			if ((engine == ENG_DPEXT))
			{
				part.effects = (part.effects + EF_NOSHADOW);
			}
			part.cnt = (self.count + pcount);
			pcount = pcount + 1;
			if ((part_prev.classtype != CT_PARTICLE))
			{
				part_first = part;
			}
			else
			{
				part_prev.entchain = part;
			}
			part_prev = part;
		}
		self.count = (self.count + PARTICLE_BANK);
		if ((part_start.classtype != CT_PARTICLE))
		{
			part.entchain = part_first;
			part_start = part_first;
			part_free = part_first.entchain;
			part_end = part;
		}
		else
		{
			part_end.entchain = part_first;
			part.entchain = part_start;
			part_end = part;
		}
	}
	if (((self.count + 1) < part_max))
	{
		self.think = generate_particlechain;
		self.nextthink = (time + 0.2);
	}
};

void() setup_particlechain =
{
	setup_particleprecache();
	if ((part_control.classtype != CT_PARTICLECONT))
	{
		part_control = spawn();
		part_control.solid = 0;
		part_control.classtype = CT_PARTICLECONT;
		dprint("€–√»¡…Œ› Creating controller\n");
		part_start = world;
		part_end = world;
		part_free = world;
		part_control.count = 0;
		part_total = 0;
	}
	part_control.think = generate_particlechain;
	part_control.nextthink = (time + 0.3);
};

void() setup_particleprecache =
{
	precache_model(PART_TORCH1);
	precache_model(PART_TORCH2);
	precache_model(PART_BOOKRUNE1);
	precache_model(PART_BOOKRUNE2);
	precache_model(PART_BUBBLE_BLUE);
	precache_model(PART_DOTMED_BLUE);
	precache_model(PART_DOTSML_BLUE);
	precache_model(PART_DOTMED_DBLUE);
	precache_model(PART_DOTSML_DBLUE);
	precache_model(PART_BUBBLE_YELLOW);
	precache_model(PART_DOTMED_YELLOW);
	precache_model(PART_DOTSML_YELLOW);
	precache_model(PART_DOTSML_GOLD);
	precache_model(PART_BUBBLE_RED);
	precache_model(PART_DOTMED_RED);
	precache_model(PART_DOTSML_RED);
	precache_model(PART_DOTMED_GREEN);
	precache_model(PART_DOTSML_GREEN);
	precache_model(PART_DOTMED_LGREEN);
	precache_model(PART_DOTSML_LGREEN);
	precache_model(PART_DOTSML_PURP);
	precache_model(PART_DOTMED_PURP);
	precache_model(PART_BUBBLE_WHITE);
	precache_model(PART_DOTSML_WHITE);
	precache_model(PART_DOTMED_GREY);
	precache_model(PART_DOTSML_GREY);
};
