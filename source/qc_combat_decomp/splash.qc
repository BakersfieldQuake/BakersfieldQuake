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

void() CheckSplash =
{
	local entity checker;
	local float check;

	if ((time < splash_next_t))
		return;
	splash_next_t = (time + 0.05);
	checker = findfloat(world, cansplash, 1);
	while (checker)
	{
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
			}
		}
		if ((check == CONTENT_EMPTY))
		{
			checker.splashy = 1;
		}
		checker = findfloat(checker, cansplash, 1);
	}
};
