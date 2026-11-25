//Decompiled code. Please respect the original copyright.

void(vector spot, vector splashsize) Splash =
{
	pointsound(spot, /*25990i*/"player/watersplash.wav", 0.8, ATTN_IDLE);
	pointparticles(particleeffectnum(/*25978i*/"watersplash"), spot, VEC_ORIGIN, 1);
};

void(vector spot, vector splashsize) Splash_big =
{
	pointsound(spot, /*25990i*/"player/watersplash.wav", 0.9, ATTN_IDLE);
	pointparticles(particleeffectnum(/*39480i*/"watersplashbig"), spot, VEC_ORIGIN, 1);
};

void(vector spot, vector splashsize) Splash_Lava =
{
	pointsound(spot, /*39495i*/"ambience/lavasplash.wav", 0.9, ATTN_IDLE);
	pointparticles(particleeffectnum(/*26013i*/"lavasplash"), spot, VEC_ORIGIN, 1);
};

void(vector spot, vector splashsize) Splash_Lava_big =
{
	pointsound(spot, /*39495i*/"ambience/lavasplash.wav", 0.9, ATTN_IDLE);
	pointparticles(particleeffectnum(/*39519i*/"lavasplashbig"), spot, VEC_ORIGIN, 1);
};

void(entity e) Splash_Register =
{
	if (!e || e == world || e.splash_reg)
		return;
	e.splash_reg = TRUE;
	e.splash_next = splash_head;
	splash_head = e;
};

void() CheckSplash =
{
	local entity checker, prev, nxt;
	local float check;

	if (!splash_head || (time < splash_next_t))
		return;
	splash_next_t = (time + 0.05);
	prev = world;
	checker = splash_head;
	while (checker)
	{
		nxt = checker.splash_next;
		if (bm_wasfreed(checker) || checker.cansplash != 1)
		{
			if (!bm_wasfreed(checker))
			{
				checker.splash_reg = FALSE;
				checker.splash_next = world;
			}
			if (prev)
				prev.splash_next = nxt;
			else
				splash_head = nxt;
			checker = nxt;
			continue;
		}
		prev = checker;
		check = pointcontents(checker.origin);
		if ((((check == CONTENT_WATER) || (check == CONTENT_SLIME)) && (checker.splashy == 1)))
		{
			checker.splashy = 0;
			if (((checker.model == "progs/grenade.mdl") || (checker.model == "progs/missile.mdl")))
			{
				Splash_big(checker.origin, checker.velocity);
			}
			else
			{
				Splash(checker.origin, checker.velocity);
				checker.cansplash = 0;
			}
		}
		if (((check == CONTENT_LAVA) && (checker.splashy == 1)))
		{
			checker.splashy = 0;
			if (((checker.model == "progs/grenade.mdl") || (checker.model == "progs/missile.mdl")))
			{
				Splash_Lava_big(checker.origin, checker.velocity);
			}
			else
			{
				Splash_Lava(checker.origin, checker.velocity);
				checker.cansplash = 0;
			}
		}
		if ((check == CONTENT_EMPTY))
		{
			checker.splashy = 1;
		}
		checker = nxt;
	}
};
