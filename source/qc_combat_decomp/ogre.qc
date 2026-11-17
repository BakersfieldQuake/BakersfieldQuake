//Decompiled code. Please respect the original copyright.

void() OgreGrenadeExplode =
{

	if ((autocvar_ogre_size_influenced_attack == 1))
	{
		T_RadiusDamage(self, self.owner, (autocvar_ogre_grenade * self.owner.scale), world);
	}
	else
	{
		T_RadiusDamage(self, self.owner, autocvar_ogre_grenade, world);
	}
	if ((self.model == "progs/grenade.mdl"))
	{
		JG_Splash();	// JohnWave's head goes off as a water splash (jg_splash.qc)
		return;
	}
	if ((((pointcontents(self.origin) == CONTENT_WATER) || (pointcontents(self.origin) == CONTENT_SLIME)) || (pointcontents(self.origin) == CONTENT_LAVA)))
	{
		sound7(self, CHAN_WEAPON, "weapons/xpld_wat.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
	}
	if ((autocvar_explosiondebris == 0))
	{
		if ((autocvar_effects_classic_explosion == 1))
		{
			pointparticles(particleeffectnum(/*26347i*/"rocket_explo_classic"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			if (other.health)
			{
				pointparticles(particleeffectnum(/*52287i*/"multigrenade_explosion_nodebris"), self.origin, VEC_ORIGIN, 1);
			}
			else
			{
				pointparticles(particleeffectnum(/*26571i*/"grenade_explosion"), self.origin, VEC_ORIGIN, 1);
			}
		}
	}
	else
	{
		if ((autocvar_effects_classic_explosion == 1))
		{
			pointparticles(particleeffectnum(/*26347i*/"rocket_explo_classic"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*26571i*/"grenade_explosion"), self.origin, VEC_ORIGIN, 1);
		}
	}
	sparklers(2);
	self.velocity = VEC_ORIGIN;
	self.touch = SUB_Null;
	setmodel(self, "progs/s_explod.spr");
	self.solid = 0;
	BecomeExplosion();
};

void() OgreGrenadeTouch =
{
	if ((other == self.owner))
	{
		return;
	}
	if ((other.takedamage == DAMAGE_AIM))
	{
		OgreGrenadeExplode();
		return;
	}
	if ((self.model != "progs/skull.mdl"))
	{
		sound7(self, CHAN_VOICE, "weapons/bounce.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound(self, CHAN_WEAPON, "vengeance/skulltouch.wav", 1, ATTN_NORM);
	}
	if ((self.velocity == VEC_ORIGIN))
	{
		self.avelocity = VEC_ORIGIN;
	}
};

void() OgreFireGrenade =
{
	local vector distancedelta;
	local vector nozdistancedelta;
	local entity missile;

	self.effects = (self.effects | EF_MUZZLEFLASH);
	sound7(self, CHAN_WEAPON, "weapons/grenade.wav", 1, ATTN_NORM, SNDSPD);
	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	makevectors(self.angles);
	if (((autocvar_ogreaim == 0) || (skill < 2)))
	{
		missile.velocity = normalize((self.enemy.origin - self.origin));
		missile.velocity = (missile.velocity * 600);
		missile.velocity_z = 200;
	}
	else
	{
		distancedelta = self.enemy.origin - self.origin;
		nozdistancedelta = distancedelta;
		missile.velocity = normalize(distancedelta);
		missile.velocity = (missile.velocity * 600);
		missile.velocity_z = ((missile.velocity_z + 150) + ((vlen(nozdistancedelta) * 0.22) * (1 + (0.3 * random()))));
	}
	missile.avelocity = '300 300 300';
	missile.angles = vectoangles(missile.velocity);
	missile.touch = OgreGrenadeTouch;
	missile.nextthink = (time + 2.5);
	missile.think = OgreGrenadeExplode;
	if ((self.health <= 0))
	{
		setmodel(missile, "progs/skull.mdl");
		setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
		setorigin(missile, self.origin);
		missile.scale = 0.8;
		missile.traileffectnum = particleeffectnum(/*51651i*/"EF_STARDUST");
		missile.nextthink = (time + 3.5);
		missile.movetype = MOVETYPE_BOUNCEMISSILE;
		missile.velocity = normalize(distancedelta);
		missile.velocity = (missile.velocity * 600);
		missile.angles = vectoangles(missile.velocity);
	}
	else
	{
		setmodel(missile, "progs/grenade.mdl");
		setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
		setorigin(missile, self.origin);
	}
};

void(float side) chainsaw =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	if (!CanDamage(self.enemy, self))
	{
		return;
	}
	if ((skill == 3))
	{
		ai_charge(11);
	}
	else
	{
		ai_charge(10);
	}
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 100))
	{
		return;
	}
	if ((autocvar_ogre_size_influenced_attack == 1))
	{
		ldmg = (((random() + random()) + random()) * autocvar_ogre_chainsaw) * self.scale;
	}
	else
	{
		ldmg = ((random() + random()) + random()) * autocvar_ogre_chainsaw;
	}
	T_Damage(self.enemy, self, self, ldmg);
	if (side)
	{
		makevectors(self.angles);
		if ((side == 1))
		{
			SpawnMeatSpray((self.origin + (v_forward * 16)), ((crandom() * 100) * v_right));
		}
		else
		{
			SpawnMeatSpray((self.origin + (v_forward * 16)), (side * v_right));
		}
	}
};

void(float loudness) ogre_footsteps =
{
	local float select;

	if (((autocvar_monsterfootsteps == 1) && ((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl"))))
	{
		select = random();
		if ((select <= 0.25))
		{
			sound7(self, CHAN_AUTO, "walk/ogre1.wav", loudness, ATTN_IDLE, SNDSPD);
		}
		else
		{
			if ((select <= 0.5))
			{
				sound7(self, CHAN_AUTO, "walk/ogre2.wav", loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				if ((select <= 0.75))
				{
					sound7(self, CHAN_AUTO, "walk/ogre3.wav", loudness, ATTN_IDLE, SNDSPD);
				}
				else
				{
					sound7(self, CHAN_AUTO, "walk/ogre4.wav", loudness, ATTN_IDLE, SNDSPD);
				}
			}
		}
	}
};

void() ogre_pull1a = [ 136, ogre_pull2a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * -15)) + (v_forward * -19)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 19)) + (v_up * -5)) + (v_forward * -16)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull2a = [ 137, ogre_pull3a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 33)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 18)) + (v_up * -5)) + (v_forward * -11)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull3a = [ 138, ogre_pull4a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 33)) + (v_up * -10)) + (v_forward * 17)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 17)) + (v_up * -5)) + (v_forward * -5)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull4a = [ 139, ogre_pull5a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 14)) + (v_up * -4)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull5a = [ 140, ogre_pull6a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 11)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -2)) + (v_forward * 8)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull6a = [ 141, ogre_pull7a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 11)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 8)) + (v_up * -3)) + (v_forward * 8)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull7a = [ 142, ogre_pull8a ]
{
	ai_stand();
	sound7(self, CHAN_WEAPON, "ogre/ogdrag.wav", 1, ATTN_NORM, SNDSPD);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 16)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -3)) + (v_forward * 11)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull8a = [ 143, ogre_pull9a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 17)) + (v_up * 3)) + (v_forward * 15)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull9a = [ 144, ogre_pull10a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 23)) + (v_up * 9)) + (v_forward * 16)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull10a = [ 139, ogre_pull11a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 14)) + (v_up * -4)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull11a = [ 140, ogre_pull12a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 11)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -2)) + (v_forward * 8)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull12a = [ 141, ogre_pull13a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 11)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 8)) + (v_up * -3)) + (v_forward * 8)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull13a = [ 142, ogre_pull14a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 16)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -3)) + (v_forward * 11)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull14a = [ 143, ogre_pull15a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 17)) + (v_up * 3)) + (v_forward * 15)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull15a = [ 144, ogre_pull16a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 23)) + (v_up * 9)) + (v_forward * 16)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull16a = [ 138, ogre_pull17a ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 33)) + (v_up * -10)) + (v_forward * 17)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 17)) + (v_up * -5)) + (v_forward * -5)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull17a = [ 137, ogre_stand1 ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 33)) + (v_up * -10)) + (v_forward * 1)), VEC_ORIGIN, 1);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 33)) + (v_up * -10)) + (v_forward * 1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 18)) + (v_up * -5)) + (v_forward * -11)), VEC_ORIGIN, 1);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -5)) + (v_forward * -11)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull1 = [ 136, ogre_pull2 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * -15)) + (v_forward * -19)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 19)) + (v_up * -5)) + (v_forward * -16)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull2 = [ 137, ogre_pull3 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 33)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 18)) + (v_up * -5)) + (v_forward * -11)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull3 = [ 138, ogre_pull4 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 33)) + (v_up * -10)) + (v_forward * 17)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 17)) + (v_up * -5)) + (v_forward * -5)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull4 = [ 139, ogre_pull5 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 14)) + (v_up * -4)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull5 = [ 140, ogre_pull6 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 11)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -2)) + (v_forward * 8)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull6 = [ 141, ogre_pull7 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 11)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 8)) + (v_up * -3)) + (v_forward * 8)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull7 = [ 142, ogre_pull8 ]
{
	ai_walk(0);
	sound7(self, CHAN_WEAPON, "ogre/ogdrag.wav", 1, ATTN_NORM, SNDSPD);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 16)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -3)) + (v_forward * 11)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull8 = [ 143, ogre_pull9 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 17)) + (v_up * 3)) + (v_forward * 15)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull9 = [ 144, ogre_pull10 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 23)) + (v_up * 9)) + (v_forward * 16)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull10 = [ 139, ogre_pull11 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 14)) + (v_up * -4)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull11 = [ 140, ogre_pull12 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 11)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -2)) + (v_forward * 8)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull12 = [ 141, ogre_pull13 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 11)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 8)) + (v_up * -3)) + (v_forward * 8)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull13 = [ 142, ogre_pull14 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 16)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -3)) + (v_forward * 11)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull14 = [ 143, ogre_pull15 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * -15)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 17)) + (v_up * 3)) + (v_forward * 15)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull15 = [ 144, ogre_pull16 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * -10)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 23)) + (v_up * 9)) + (v_forward * 16)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull16 = [ 138, ogre_pull17 ]
{
	ai_walk(0);
	if ((self.has_fired >= 1))
	{
		self.has_fired = 0;
		ogre_smash1();
	}
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 33)) + (v_up * -10)) + (v_forward * 17)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 17)) + (v_up * -5)) + (v_forward * -5)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_pull17 = [ 137, ogre_stand1 ]
{
	ai_walk(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 33)) + (v_up * -10)) + (v_forward * 1)), VEC_ORIGIN, 1);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 33)) + (v_up * -10)) + (v_forward * 1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 18)) + (v_up * -5)) + (v_forward * -11)), VEC_ORIGIN, 1);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -5)) + (v_forward * -11)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_stand1 = [ 0, ogre_stand2 ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 26)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_stand2 = [ 1, ogre_stand3 ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 26)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -3)) + (v_forward * -14)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_stand3 = [ 2, ogre_stand4 ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 26)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -3)) + (v_forward * -13)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_stand4 = [ 3, ogre_stand5 ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 26)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -3)) + (v_forward * -12)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_stand5 = [ 4, ogre_stand6 ]
{
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "ogre/ogidle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 26)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -3)) + (v_forward * -13)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_stand6 = [ 5, ogre_stand7 ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 26)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -3)) + (v_forward * -14)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_stand7 = [ 6, ogre_stand8 ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 26)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_stand8 = [ 7, ogre_stand9 ]
{
	ai_stand();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 26)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -3)) + (v_forward * -16)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_stand9 = [ 8, ogre_stand1 ]
{
	ai_stand();
	if ((autocvar_ogrecheckchainsaw == 1))
	{
		if ((random() <= 0.06))
		{
			ogre_pull1a();
		}
	}
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 26)) + (v_up * -10)) + (v_forward * -10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 18)) + (v_up * -3)) + (v_forward * -16)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk1 = [ 9, ogre_walk2 ]
{
	ai_walk(3);
	ogre_footsteps(0.95);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk2 = [ 10, ogre_walk3 ]
{
	ai_walk(2);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk3 = [ 11, ogre_walk4 ]
{
	ai_walk(2);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "ogre/ogidle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk4 = [ 12, ogre_walk5 ]
{
	ai_walk(2);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk5 = [ 13, ogre_walk6 ]
{
	ai_walk(2);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk6 = [ 14, ogre_walk7 ]
{
	ai_walk(5);
	if ((random() < 0.1))
	{
		sound7(self, CHAN_VOICE, "ogre/ogdrag.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk7 = [ 15, ogre_walk8 ]
{
	ai_walk(3);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk8 = [ 16, ogre_walk9 ]
{
	ai_walk(2);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk9 = [ 17, ogre_walk10 ]
{
	ai_walk(3);
	ogre_footsteps(0.95);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk10 = [ 18, ogre_walk11 ]
{
	ai_walk(1);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk11 = [ 19, ogre_walk12 ]
{
	ai_walk(2);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk12 = [ 20, ogre_walk13 ]
{
	ai_walk(3);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk13 = [ 21, ogre_walk14 ]
{
	ai_walk(3);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk14 = [ 22, ogre_walk15 ]
{
	ai_walk(3);
	if ((autocvar_ogrecheckchainsaw == 1))
	{
		if ((random() <= 0.07))
		{
			ogre_pull1();
		}
	}
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk15 = [ 23, ogre_walk16 ]
{
	ai_walk(3);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_walk16 = [ 24, ogre_walk1 ]
{
	ai_walk(4);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
		pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 22)) + (v_up * -10)) + (v_forward * -11)), VEC_ORIGIN, 1);
		particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
		pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 20)) + (v_up * -21)) + (v_forward * -40)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52892i*/"ogre_chainsaw_walk");
			pointparticles(particleeffectnum(/*52892i*/"ogre_chainsaw_walk"), (((self.origin + (v_right * 15)) + (v_up * -3)) + (v_forward * -15)), VEC_ORIGIN, 1);
			particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching");
			pointparticles(particleeffectnum(/*52927i*/"ogre_chainsaw_walk_scratching"), (((self.origin + (v_right * 13)) + (v_up * -21)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_run1 = [ 25, ogre_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(9);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "ogre/ogidle2.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * 38)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_run2 = [ 26, ogre_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(12);
	ogre_footsteps(1);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 18)) + (v_up * 38)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_run3 = [ 27, ogre_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 19)) + (v_up * 38)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_run4 = [ 28, ogre_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(22);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 21)) + (v_up * 36)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_run5 = [ 29, ogre_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 21)) + (v_up * 35)) + (v_forward * -1)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_run6 = [ 30, ogre_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(4);
	ogre_footsteps(1);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 21)) + (v_up * 34)) + (v_forward * -4)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_run7 = [ 31, ogre_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(13);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 21)) + (v_up * 35)) + (v_forward * -8)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_run8 = [ 32, ogre_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(24);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 21)) + (v_up * 35)) + (v_forward * -12)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing1 = [ 33, ogre_swing2 ]
{
	ai_charge(11);
	sound7(self, CHAN_WEAPON, "ogre/ogsawatk.wav", 1, ATTN_NORM, SNDSPD);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -9)) + (v_forward * -19)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -7)) + (v_forward * -17)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing2 = [ 34, ogre_swing3 ]
{
	ai_charge(1);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 15)) + (v_up * -9)) + (v_forward * -17)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 15)) + (v_up * -6)) + (v_forward * -16)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing3 = [ 35, ogre_swing4 ]
{
	ai_charge(4);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * -8)) + (v_forward * -17)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 18)) + (v_up * -7)) + (v_forward * -14)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing4 = [ 36, ogre_swing5 ]
{
	ai_charge(13);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 30)) + (v_up * 1)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -1)) + (v_forward * 10)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing5 = [ 37, ogre_swing6 ]
{
	ai_charge(9);
	chainsaw(0);
	self.angles_y = (self.angles_y + (random() * 25));
	ogre_footsteps(0.75);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * 10)) + (v_forward * 27)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -1)) + (v_up * 9)) + (v_forward * 25)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing6 = [ 38, ogre_swing7 ]
{
	chainsaw(200);
	self.angles_y = (self.angles_y + (random() * 25));
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -33)) + (v_up * 12)) + (v_forward * 33)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -25)) + (v_up * 12)) + (v_forward * 27)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing7 = [ 39, ogre_swing8 ]
{
	chainsaw(0);
	self.angles_y = (self.angles_y + (random() * 25));
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -37)) + (v_up * 12)) + (v_forward * 15)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -27)) + (v_up * 14)) + (v_forward * 10)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing8 = [ 40, ogre_swing9 ]
{
	chainsaw(0);
	self.angles_y = (self.angles_y + (random() * 25));
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -30)) + (v_up * 12)) + (v_forward * 7)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -19)) + (v_up * 15)) + (v_forward * -7)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing9 = [ 41, ogre_swing10 ]
{
	chainsaw(0);
	self.angles_y = (self.angles_y + (random() * 25));
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -24)) + (v_up * 12)) + (v_forward * -7)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -14)) + (v_up * 15)) + (v_forward * -7)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing10 = [ 42, ogre_swing11 ]
{
	chainsaw(-200);
	self.angles_y = (self.angles_y + (random() * 25));
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -17)) + (v_up * 12)) + (v_forward * -1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -18)) + (v_up * 15)) + (v_forward * -7)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing11 = [ 43, ogre_swing12 ]
{
	chainsaw(0);
	self.angles_y = (self.angles_y + (random() * 25));
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -27)) + (v_up * 10)) + (v_forward * 7)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -20)) + (v_up * 14)) + (v_forward * 10)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing12 = [ 44, ogre_swing13 ]
{
	ai_charge(3);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -25)) + (v_up * 12)) + (v_forward * 30)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 2)) + (v_up * 15)) + (v_forward * 23)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing13 = [ 45, ogre_swing14 ]
{
	ai_charge(8);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -5)) + (v_up * 10)) + (v_forward * 22)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * -5)) + (v_up * 7)) + (v_forward * 15)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_swing14 = [ 46, ogre_run1 ]
{
	ai_charge(9);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 37)) + (v_up * 4)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * 1)) + (v_forward * -5)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash1 = [ 47, ogre_smash2 ]
{
	ai_charge(6);
	sound7(self, CHAN_WEAPON, "ogre/ogsawatk.wav", 1, ATTN_NORM, SNDSPD);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -9)) + (v_forward * -22)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -3)) + (v_forward * -22)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash2 = [ 48, ogre_smash3 ]
{
	ai_charge(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 7)) + (v_up * -9)) + (v_forward * -27)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 7)) + (v_up * -3)) + (v_forward * -27)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash3 = [ 49, ogre_smash4 ]
{
	ai_charge(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 7)) + (v_up * -4)) + (v_forward * -33)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * 1)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash4 = [ 50, ogre_smash5 ]
{
	ai_charge(1);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 7)) + (v_up * 10)) + (v_forward * -33)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 12)) + (v_up * 12)) + (v_forward * -33)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash5 = [ 51, ogre_smash6 ]
{
	ai_charge(4);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 11)) + (v_up * 22)) + (v_forward * -30)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 15)) + (v_up * 24)) + (v_forward * -30)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash6 = [ 52, ogre_smash7 ]
{
	ai_charge(4);
	chainsaw(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 17)) + (v_up * 37)) + (v_forward * -22)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * 35)) + (v_forward * -22)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash7 = [ 53, ogre_smash8 ]
{
	ai_charge(4);
	chainsaw(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * 53)) + (v_forward * -12)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 15)) + (v_up * 47)) + (v_forward * -5)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash8 = [ 54, ogre_smash9 ]
{
	ai_charge(10);
	chainsaw(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * 35)) + (v_forward * 12)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * 35)) + (v_forward * 7)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash9 = [ 55, ogre_smash10 ]
{
	ai_charge(13);
	chainsaw(0);
	ogre_footsteps(0.85);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * 10)) + (v_forward * 33)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 13)) + (v_up * 15)) + (v_forward * 30)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash10 = [ 56, ogre_smash11 ]
{
	chainsaw(1);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 10)) + (v_up * -5)) + (v_forward * 45)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 13)) + (v_up * -1)) + (v_forward * 38)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash11 = [ 57, ogre_smash12 ]
{
	ai_charge(2);
	chainsaw(0);
	self.nextthink = (self.nextthink + (random() * 0.2));
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 11)) + (v_up * -7)) + (v_forward * 45)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 17)) + (v_up * 4)) + (v_forward * 38)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash12 = [ 58, ogre_smash13 ]
{
	ai_charge(0);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * -5)) + (v_forward * 45)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * 10)) + (v_forward * 30)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash13 = [ 59, ogre_smash14 ]
{
	ai_charge(4);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 30)) + (v_up * 5)) + (v_forward * 25)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 30)) + (v_up * 20)) + (v_forward * 10)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_smash14 = [ 60, ogre_run1 ]
{
	ai_charge(12);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 37)) + (v_up * 5)) + (v_forward * -1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * 33)) + (v_forward * 2)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_nail1 = [ 61, ogre_nail2 ]
{
	self.nextthink = ((time + 0.1) + (self.has_fired * 0.35));
	ai_face();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 27)) + (v_up * 35)) + (v_forward * -1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 37)) + (v_forward * -4)), VEC_ORIGIN, 1);
		}
	}
	if ((self.has_fired > 0))
	{
		sound7(self, CHAN_VOICE, "ogre/ogwake.wav", 1, ATTN_NORM, (SNDSPD - 10));
	}
};

void() ogre_nail2 = [ 62, ogre_nail3 ]
{
	self.nextthink = ((time + 0.1) + (self.has_fired * 0.25));
	ai_face();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 27)) + (v_up * 35)) + (v_forward * -1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * 37)) + (v_forward * -6)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_nail3 = [ 62, ogre_nail4 ]
{
	self.nextthink = (time + 0.1);
	ai_face();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 27)) + (v_up * 35)) + (v_forward * -1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * 37)) + (v_forward * -6)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_nail4 = [ 63, ogre_nail5 ]
{
	self.nextthink = (time + 0.1);
	ai_face();
	OgreFireGrenade();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 27)) + (v_up * 35)) + (v_forward * -1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * 37)) + (v_forward * -6)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_nail5 = [ 64, ogre_nail6 ]
{
	self.nextthink = (time + 0.1);
	ai_face();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 27)) + (v_up * 35)) + (v_forward * -1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 25)) + (v_up * 37)) + (v_forward * -5)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_nail6 = [ 65, ogre_nail7 ]
{
	self.nextthink = (time + 0.1);
	ai_face();
	if (((((skill >= 2) && (self.has_fired < 5)) && (self.has_fired >= 1)) && (enemy_range != RANGE_MELEE)))
	{
		self.has_fired = (self.has_fired + 1);
		ogre_nail3();
	}
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 27)) + (v_up * 35)) + (v_forward * -1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 27)) + (v_up * 33)) + (v_forward * -5)), VEC_ORIGIN, 1);
		}
	}
	if (((skill >= 2) && (self.has_fired >= 5)))
	{
		if (((random() < 0.4) && (enemy_range == RANGE_NEAR)))
		{
			ogre_pull1();
		}
	}
};

void() ogre_nail7 = [ 66, ogre_run1 ]
{
	self.nextthink = (time + 0.1);
	ai_face();
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 27)) + (v_up * 35)) + (v_forward * -1)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 27)) + (v_up * 20)) + (v_forward * -2)), VEC_ORIGIN, 1);
		}
	}
	if (((random() < 0.175) && (self.has_fired == 0)))
	{
		SUB_CheckRefire(ogre_nail1);
	}
	self.has_fired = 0;
	random();
	if ((random() < (0.04 + (skill * 0.01))))
	{
		self.has_fired = 1;
	}
};

void() ogre_crawl1 = [ 25, ogre_crawl2 ]
{
	ThrowBloodSplat('0 0 -10', (self.origin + '0 0 -20'), self);
	ai_walk(1);
	self.health = (self.health - 0.5);
	if ((self.health <= 0))
	{
		if ((self.target || self.killtarget))
		{
			activator = self.enemy;
			SUB_UseTargets();
		}
		ogre_die();
	}
};

void() ogre_crawl2 = [ 26, ogre_crawl3 ]
{
	ThrowBloodSplat('1 1 -10', (self.origin + '0 0 -20'), self);
	ai_walk(1);
};

void() ogre_crawl3 = [ 27, ogre_crawl4 ]
{
	ThrowBloodSplat('2 2 -10', (self.origin + '0 0 -20'), self);
	ai_walk(2);
	if ((random() < 0.3))
	{
		sound7(self, CHAN_VOICE, "ogre/ogpain1.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() ogre_crawl4 = [ 28, ogre_crawl5 ]
{
	ThrowBloodSplat('0 0 -10', (self.origin + '0 0 -20'), self);
	ai_walk(2);
};

void() ogre_crawl5 = [ 29, ogre_crawl6 ]
{
	ThrowBloodSplat('-1 -1 -10', (self.origin + '0 0 -20'), self);
	ai_walk(2);
};

void() ogre_crawl6 = [ 30, ogre_crawl7 ]
{
	ThrowBloodSplat('1 1 -10', (self.origin + '0 0 -20'), self);
	ai_walk(1);
};

void() ogre_crawl7 = [ 31, ogre_crawl8 ]
{
	ThrowBloodSplat('-1.5 -1 -10', (self.origin + '0 0 -20'), self);
	ai_walk(1);
};

void() ogre_crawl8 = [ 32, ogre_crawl1 ]
{
	ThrowBloodSplat('1 2 -10', (self.origin + '0 0 -20'), self);
	ai_walk(1);
};

void() ogre_pain1 = [ 67, ogre_pain2 ]
{
};

void() ogre_pain2 = [ 68, ogre_pain3 ]
{
};

void() ogre_pain3 = [ 69, ogre_pain4 ]
{
};

void() ogre_pain4 = [ 70, ogre_pain5 ]
{
};

void() ogre_pain5 = [ 71, ogre_run1 ]
{
};

void() ogre_painb1 = [ 72, ogre_painb2 ]
{
};

void() ogre_painb2 = [ 73, ogre_painb3 ]
{
};

void() ogre_painb3 = [ 74, ogre_run1 ]
{
};

void() ogre_painc1 = [ 75, ogre_painc2 ]
{
};

void() ogre_painc2 = [ 76, ogre_painc3 ]
{
};

void() ogre_painc3 = [ 77, ogre_painc4 ]
{
	ogre_footsteps(0.7);
};

void() ogre_painc4 = [ 78, ogre_painc5 ]
{
};

void() ogre_painc5 = [ 79, ogre_painc6 ]
{
};

void() ogre_painc6 = [ 80, ogre_run1 ]
{
};

void() ogre_paind1 = [ 81, ogre_paind2 ]
{
};

void() ogre_paind2 = [ 82, ogre_paind3 ]
{
	ai_pain(10);
};

void() ogre_paind3 = [ 83, ogre_paind4 ]
{
	ai_pain(9);
};

void() ogre_paind4 = [ 84, ogre_paind5 ]
{
	ai_pain(4);
};

void() ogre_paind5 = [ 85, ogre_paind6 ]
{
};

void() ogre_paind6 = [ 86, ogre_paind7 ]
{
};

void() ogre_paind7 = [ 87, ogre_paind8 ]
{
};

void() ogre_paind8 = [ 88, ogre_paind9 ]
{
};

void() ogre_paind9 = [ 89, ogre_paind10 ]
{
};

void() ogre_paind10 = [ 90, ogre_paind11 ]
{
};

void() ogre_paind11 = [ 91, ogre_paind12 ]
{
};

void() ogre_paind12 = [ 92, ogre_paind13 ]
{
};

void() ogre_paind13 = [ 93, ogre_paind14 ]
{
};

void() ogre_paind14 = [ 94, ogre_paind15 ]
{
};

void() ogre_paind15 = [ 95, ogre_paind16 ]
{
};

void() ogre_paind16 = [ 96, ogre_run1 ]
{
};

void() ogre_paine1 = [ 97, ogre_paine2 ]
{
};

void() ogre_paine2 = [ 98, ogre_paine3 ]
{
	ai_pain(10);
};

void() ogre_paine3 = [ 99, ogre_paine4 ]
{
	ai_pain(9);
};

void() ogre_paine4 = [ 100, ogre_paine5 ]
{
	ai_pain(4);
};

void() ogre_paine5 = [ 101, ogre_paine6 ]
{
};

void() ogre_paine6 = [ 102, ogre_paine7 ]
{
};

void() ogre_paine7 = [ 103, ogre_paine8 ]
{
};

void() ogre_paine8 = [ 104, ogre_paine9 ]
{
};

void() ogre_paine9 = [ 105, ogre_paine10 ]
{
};

void() ogre_paine10 = [ 106, ogre_paine11 ]
{
};

void() ogre_paine11 = [ 107, ogre_paine12 ]
{
};

void() ogre_paine12 = [ 108, ogre_paine13 ]
{
};

void() ogre_paine13 = [ 109, ogre_paine14 ]
{
};

void() ogre_paine14 = [ 110, ogre_paine15 ]
{
};

void() ogre_paine15 = [ 111, ogre_run1 ]
{
};

void() ogre_pack =
{
	self.ammo_rockets = autocvar_backpack_ogre_grenades;
	self.backpack_thrower = 3;
	DropBackpack();
};

void(entity attacker, float damage) ogre_pain =
{
	local float r;

	if ((((((attacker.meleeing == 0) && (((attacker.weapon == IT_ROCKET_LAUNCHER) || (attacker.weapon == IT_GRENADE_LAUNCHER)) || (attacker.weapon == IT_SUPER_SHOTGUN))) && ((random() * 100) < 15)) && (self.health <= 59)) && (damage > 40)))
	{
		setmodel(self, "progs/ogre_half.mdl");
		setsize(self, ZOMB_MIN, '12 12 -7');
		pointparticles(particleeffectnum(/*25865i*/"blood_saw"), self.origin, VEC_ORIGIN, 1);
		sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
		self.velocity = ('0 0 15' + (v_forward * 25));
		ThrowGib("progs/gib_ogfoot1.mdl", self.health);
		ThrowGib("progs/gib_ogfoot2.mdl", self.health);
		if ((random() < 0.5))
		{
			sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "player/udeath2.wav", 1, ATTN_NORM, SNDSPD);
		}
		if ((attacker.weapon == IT_SUPER_SHOTGUN))
		{
			ogre_pack();
		}
		ThrowWeapon("progs/w_chainsaw.mdl", self.health);
		self.traileffectnum = particleeffectnum(/*53029i*/"med_bloodtrail_TR");
		self.th_stand = ogre_crawl1;
		self.th_run = SUB_Null;
		self.th_melee = SUB_Null;
		self.th_pain = SUB_Null;
		self.th_missile = SUB_Null;
		self.goalentity = world;
		self.health = 15;
		self.th_stand();
		return;
	}
	if ((self.pain_finished > time))
	{
		return;
	}
	random();
	if (((self.has_fired > 0) && (random() < (0.95 - (damage * 0.005)))))
	{
		return;
	}
	if ((random() < 0.7))
	{
		self.has_fired = 0;
	}
	if ((((self.health <= 120) && (((self.enemy.weapon != IT_AXE) || (self.enemy.weapon != IT_ROCKET_LAUNCHER)) || (self.enemy.weapon != IT_GRENADE_LAUNCHER))) && (self.enemy.meleeing == 0)))
	{
		if ((self.skin == 1))
		{
			setmodel(self, "progs/ogre_pain.mdl");
			self.skin = 1;
		}
		else
		{
			setmodel(self, "progs/ogre_pain.mdl");
		}
		setsize(self, '-22 -22 -24', '22 22 41');
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_ogre * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "ogre/ogpain1.wav", 1, ATTN_NORM, SNDSPD);
	r = random();
	if ((r < 0.25))
	{
		ogre_pain1();
		self.pain_finished = (time + 1);
	}
	else
	{
		if ((r < 0.5))
		{
			ogre_painb1();
			self.pain_finished = (time + 1);
		}
		else
		{
			if ((r < 0.75))
			{
				ogre_painc1();
				self.pain_finished = (time + 1);
			}
			else
			{
				if ((r < 0.88))
				{
					ogre_paind1();
					self.pain_finished = (time + 2);
				}
				else
				{
					ogre_paine1();
					self.pain_finished = (time + 2);
				}
			}
		}
	}
};

void() ogre_dieburn1 = [ 112, ogre_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
};

void() ogre_dieburn2 = [ 113, ogre_dieburn3 ]
{
	self.burnz_origin = 11;
};

void() ogre_dieburn3 = [ 114, ogre_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
	self.ammo_rockets = autocvar_backpack_ogre_grenades;
	self.backpack_thrower = 3;
	DropBackpack();
};

void() ogre_dieburn4 = [ 115, ogre_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() ogre_dieburn5 = [ 116, ogre_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() ogre_dieburn6 = [ 117, ogre_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() ogre_dieburn7 = [ 118, ogre_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() ogre_dieburn8 = [ 119, ogre_dieburn9 ]
{
	self.burnz_origin = -6;
};

void() ogre_dieburn9 = [ 120, ogre_dieburn10 ]
{
	self.burnz_origin = -8;
};

void() ogre_dieburn10 = [ 121, ogre_dieburn10 ]
{
	self.burnz_origin = -10;
};

void() ogre_dierl1 = [ 0, ogre_dierl2 ]
{
	sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_dierl2 = [ 1, ogre_dierl3 ]
{
	self.solid = 0;
	self.ammo_rockets = autocvar_backpack_ogre_grenades;
	self.backpack_thrower = 3;
	DropBackpack();
};

void() ogre_dierl3 = [ 1, ogre_dierl3 ]
{
	if ((self.flags & FL_ONGROUND))
	{
		self.movetype = 0;
	}
};

void() ogre_diessg1 = [ 147, ogre_diessg2 ]
{
	makevectors(self.angles);
	self.fangle = v_forward;
	ai_back(4);
};

void() ogre_diessg2 = [ 148, ogre_diessg3 ]
{
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt_corpse", self.origin, VEC_ORIGIN, 1);
	}
};

void() ogre_diessg3 = [ 149, ogre_diessg4 ]
{
	self.solid = 0;
	self.ammo_rockets = autocvar_backpack_ogre_grenades;
	self.backpack_thrower = 3;
	DropBackpack();
};

void() ogre_diessg4 = [ 150, ogre_diessg5 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	}
	sound7(self, CHAN_AUTO, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_diessg5 = [ 151, ogre_diessg6 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	}
};

void() ogre_diessg6 = [ 152, ogre_diessg7 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	}
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_diessg7 = [ 153, ogre_diessg8 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt", self.origin, VEC_ORIGIN, 1);
	}
};

void() ogre_diessg8 = [ 154, ogre_diessg9 ]
{
};

void() ogre_diessg9 = [ 155, ogre_diessg10 ]
{
};

void() ogre_diessg10 = [ 156, ogre_diessg11 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_blast", self.origin, VEC_ORIGIN, 1);
	}
};

void() ogre_diessg11 = [ 157, ogre_diessg12 ]
{
};

void() ogre_diessg12 = [ 158, ogre_diessg13 ]
{
	sound7(self, CHAN_AUTO, "ogre/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_diessg13 = [ 159, ogre_diessg14 ]
{
};

void() ogre_diessg14 = [ 160, ogre_diessg15 ]
{
};

void() ogre_diessg15 = [ 161, ogre_diessg16 ]
{
};

void() ogre_diessg16 = [ 162, ogre_diessg17 ]
{
};

void() ogre_diessg17 = [ 163, ogre_diessg18 ]
{
};

void() ogre_diessg18 = [ 164, ogre_diessg19 ]
{
};

void() ogre_diessg19 = [ 165, ogre_diessg20 ]
{
	sound7(self, CHAN_AUTO, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_diessg20 = [ 166, ogre_diessg21 ]
{
	if ((autocvar_bloodextension == 1))
	{
		sendParticle("blood_spurt_ogre", ((self.origin + (self.fangle * -30)) - '0 0 10'), VEC_ORIGIN, 1);
	}
};

void() ogre_diessg21 = [ 167, ogre_diessg22 ]
{
};

void() ogre_diessg22 = [ 167, ogre_diessg23 ]
{
};

void() ogre_diessg23 = [ 167, ogre_diessg24 ]
{
};

void() ogre_diessg24 = [ 167, ogre_diessg25 ]
{
};

void() ogre_diessg25 = [ 167, ogre_diessg26 ]
{
};

void() ogre_diessg26 = [ 168, ogre_diessg26 ]
{
	if ((autocvar_ogrecorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_ogrecorpsehealth, "progs/gib_ogfoot1.mdl");
	sendParticle("blood_spurt_ogre", ((self.origin + (self.fangle * -30)) - '0 0 10'), VEC_ORIGIN, 1);
};

void() ogre_dieng1 = [ 169, ogre_dieng2 ]
{
};

void() ogre_dieng2 = [ 170, ogre_dieng3 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
	}
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_dieng3 = [ 171, ogre_dieng4 ]
{
	self.solid = 0;
	self.ammo_rockets = autocvar_backpack_ogre_grenades;
	self.backpack_thrower = 3;
	DropBackpack();
};

void() ogre_dieng4 = [ 172, ogre_dieng5 ]
{
};

void() ogre_dieng5 = [ 173, ogre_dieng6 ]
{
};

void() ogre_dieng6 = [ 174, ogre_dieng7 ]
{
};

void() ogre_dieng7 = [ 175, ogre_dieng8 ]
{
};

void() ogre_dieng8 = [ 176, ogre_dieng9 ]
{
};

void() ogre_dieng9 = [ 177, ogre_dieng10 ]
{
};

void() ogre_dieng10 = [ 178, ogre_dieng11 ]
{
};

void() ogre_dieng11 = [ 179, ogre_dieng12 ]
{
};

void() ogre_dieng12 = [ 180, ogre_dieng13 ]
{
};

void() ogre_dieng13 = [ 181, ogre_dieng14 ]
{
};

void() ogre_dieng14 = [ 182, ogre_dieng15 ]
{
};

void() ogre_dieng15 = [ 183, ogre_dieng16 ]
{
};

void() ogre_dieng16 = [ 184, ogre_dieng17 ]
{
};

void() ogre_dieng17 = [ 185, ogre_dieng18 ]
{
};

void() ogre_dieng18 = [ 186, ogre_dieng19 ]
{
};

void() ogre_dieng19 = [ 187, ogre_dieng20 ]
{
};

void() ogre_dieng20 = [ 188, ogre_dieng21 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
	}
};

void() ogre_dieng21 = [ 189, ogre_dieng22 ]
{
};

void() ogre_dieng22 = [ 190, ogre_dieng23 ]
{
	sound7(self, CHAN_AUTO, "misc/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_dieng23 = [ 191, ogre_dieng24 ]
{
};

void() ogre_dieng24 = [ 192, ogre_dieng25 ]
{
};

void() ogre_dieng25 = [ 193, ogre_dieng26 ]
{
};

void() ogre_dieng26 = [ 194, ogre_dieng27 ]
{
};

void() ogre_dieng27 = [ 195, ogre_dieng28 ]
{
};

void() ogre_dieng28 = [ 196, ogre_dieng29 ]
{
};

void() ogre_dieng29 = [ 197, ogre_dieng30 ]
{
};

void() ogre_dieng30 = [ 198, ogre_dieng31 ]
{
	sound7(self, CHAN_AUTO, "ogre/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_dieng31 = [ 199, ogre_dieng31 ]
{
	if ((autocvar_ogrecorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_ogrecorpsehealth, "progs/gib_ogfoot1.mdl");
};

void() ogre_dieaxe1 = [ 0, ogre_dieaxe2 ]
{
};

void() ogre_dieaxe2 = [ 1, ogre_dieaxe3 ]
{
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
	}
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_dieaxe3 = [ 2, ogre_dieaxe4 ]
{
	self.solid = 0;
	self.ammo_rockets = autocvar_backpack_ogre_grenades;
	self.backpack_thrower = 3;
	DropBackpack();
};

void() ogre_dieaxe4 = [ 3, ogre_dieaxe5 ]
{
	sound7(self, CHAN_AUTO, "misc/megagib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_dieaxe5 = [ 4, ogre_dieaxe6 ]
{
	ai_forward(10);
};

void() ogre_dieaxe6 = [ 5, ogre_dieaxe7 ]
{
};

void() ogre_dieaxe7 = [ 6, ogre_dieaxe8 ]
{
};

void() ogre_dieaxe8 = [ 7, ogre_dieaxe9 ]
{
	ai_forward(6);
};

void() ogre_dieaxe9 = [ 8, ogre_dieaxe10 ]
{
	ai_forward(6);
};

void() ogre_dieaxe10 = [ 9, ogre_dieaxe11 ]
{
};

void() ogre_dieaxe11 = [ 10, ogre_dieaxe12 ]
{
};

void() ogre_dieaxe12 = [ 11, ogre_dieaxe13 ]
{
};

void() ogre_dieaxe13 = [ 12, ogre_dieaxe14 ]
{
};

void() ogre_dieaxe14 = [ 13, ogre_dieaxe15 ]
{
};

void() ogre_dieaxe15 = [ 14, ogre_dieaxe16 ]
{
};

void() ogre_dieaxe16 = [ 15, ogre_dieaxe17 ]
{
};

void() ogre_dieaxe17 = [ 16, ogre_dieaxe18 ]
{
};

void() ogre_dieaxe18 = [ 17, ogre_dieaxe19 ]
{
};

void() ogre_dieaxe19 = [ 18, ogre_dieaxe20 ]
{
};

void() ogre_dieaxe20 = [ 19, ogre_dieaxe21 ]
{
	ai_forward(6);
	sound7(self, CHAN_AUTO, "misc/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
	if ((autocvar_bloodextension == 1))
	{
		pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
	}
};

void() ogre_dieaxe21 = [ 20, ogre_dieaxe22 ]
{
	ai_forward(7);
};

void() ogre_dieaxe22 = [ 21, ogre_dieaxe22 ]
{
	ai_forward(10);
	if ((autocvar_ogrecorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_ogrecorpsehealth, "progs/gib_ogfoot2.mdl");
};

void() ogre_die1 = [ 112, ogre_die2 ]
{
};

void() ogre_die2 = [ 113, ogre_die3 ]
{
};

void() ogre_die3 = [ 114, ogre_die4 ]
{
	self.solid = 0;
	self.ammo_rockets = autocvar_backpack_ogre_grenades;
	self.backpack_thrower = 3;
	DropBackpack();
};

void() ogre_die4 = [ 115, ogre_die5 ]
{
};

void() ogre_die5 = [ 116, ogre_die6 ]
{
};

void() ogre_die6 = [ 117, ogre_die7 ]
{
};

void() ogre_die7 = [ 118, ogre_die8 ]
{
};

void() ogre_die8 = [ 119, ogre_die9 ]
{
};

void() ogre_die9 = [ 120, ogre_die10 ]
{
};

void() ogre_die10 = [ 121, ogre_die11 ]
{
};

void() ogre_die11 = [ 122, ogre_die12 ]
{
};

void() ogre_die12 = [ 123, ogre_die13 ]
{
	sound7(self, CHAN_AUTO, "ogre/fall_backwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_die13 = [ 124, ogre_die14 ]
{
};

void() ogre_die14 = [ 125, ogre_die14 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 22;
	if ((autocvar_ogrecorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_ogrecorpsehealth, "progs/h_ogre.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_ogrecorpsehealth, "progs/h_ogre1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_ogrerandomness = autocvar_ogrerandomness * 0.01;
		if ((autocvar_ogre == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_ogrerandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_ogre == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_ogrerandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/ogre.mdl", 125, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/ogre1.mdl", 125, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_ogre == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_ogrerandomness))
					{
						vengeance_ogre("progs/ogre.mdl", 125);
					}
				}
				else
				{
					if ((autocvar_ogre == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_ogrerandomness))
						{
							zufall = random();
							if ((zufall > 0.8))
							{
								ghost_die();
							}
							else
							{
								if ((zufall < 0.25))
								{
									if ((self.monstermodel == 0))
									{
										soul("progs/ogre.mdl", 125, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/ogre1.mdl", 125, zet);
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
	else
	{
		if ((self.grimrock_helper == 1))
		{
			zufall = random();
			if ((zufall > 0.825))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.175))
				{
					if ((zufall < 0.004))
					{
						soul("progs/afrit.mdl", 64, 27.451);
					}
					else
					{
						if ((self.monstermodel == 0))
						{
							soul("progs/ogre.mdl", 125, zet);
						}
						else
						{
							if ((self.monstermodel == 1))
							{
								soul("progs/ogre1.mdl", 125, zet);
							}
						}
					}
				}
				else
				{
					vengeance_ogre("progs/ogre.mdl", 125);
				}
			}
		}
	}
};

void() ogre_bdie1 = [ 126, ogre_bdie2 ]
{
};

void() ogre_bdie2 = [ 127, ogre_bdie3 ]
{
	ai_forward(5);
};

void() ogre_bdie3 = [ 128, ogre_bdie4 ]
{
	self.solid = 0;
	self.ammo_rockets = autocvar_backpack_ogre_grenades;
	self.backpack_thrower = 3;
	DropBackpack();
};

void() ogre_bdie4 = [ 129, ogre_bdie5 ]
{
	ai_forward(1);
};

void() ogre_bdie5 = [ 130, ogre_bdie6 ]
{
	ai_forward(3);
};

void() ogre_bdie6 = [ 131, ogre_bdie7 ]
{
	ai_forward(7);
};

void() ogre_bdie7 = [ 132, ogre_bdie8 ]
{
	ai_forward(25);
	sound7(self, CHAN_AUTO, "ogre/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() ogre_bdie8 = [ 133, ogre_bdie9 ]
{
};

void() ogre_bdie9 = [ 134, ogre_bdie10 ]
{
};

void() ogre_bdie10 = [ 135, ogre_bdie10 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	zet = 22;
	if ((autocvar_ogrecorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_ogrecorpsehealth, "progs/h_ogre.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_ogrecorpsehealth, "progs/h_ogre1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_ogrerandomness = autocvar_ogrerandomness * 0.01;
		if ((autocvar_ogre == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_ogrerandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_ogre == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_ogrerandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/ogre.mdl", 135, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/ogre1.mdl", 135, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_ogre == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_ogrerandomness))
					{
						vengeance_ogre("progs/ogre.mdl", 135);
					}
				}
				else
				{
					if ((autocvar_ogre == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_ogrerandomness))
						{
							zufall = random();
							if ((zufall > 0.8))
							{
								ghost_die();
							}
							else
							{
								if ((zufall < 0.2))
								{
									if ((self.monstermodel == 0))
									{
										soul("progs/ogre.mdl", 135, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/ogre1.mdl", 135, zet);
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
	else
	{
		if ((self.grimrock_helper == 1))
		{
			zufall = random();
			if ((zufall > 0.825))
			{
				ghost_die();
			}
			else
			{
				if ((zufall < 0.25))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/ogre.mdl", 135, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/ogre1.mdl", 135, zet);
						}
					}
				}
				else
				{
					vengeance_ogre("progs/ogre.mdl", 135);
				}
			}
		}
	}
};

void(float maxgibs, float gibscounter) producegibs_ogre =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/gib1.mdl", self.health);
		ThrowGib("progs/gib2.mdl", self.health);
		ThrowWeapon("progs/w_ogregl.mdl", self.health);
		ThrowGib("progs/gib_ogfoot1.mdl", self.health);
		ThrowGib("progs/gib_ogfoot2.mdl", self.health);
		ThrowWeapon("progs/w_chainsaw.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_ogre(maxgibs, gibscounter);
};

void() ogre_lightning_death = [ 69, ogre_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() ogre_lightning_death1 = [ 69, ogre_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(1, "progs/h_ogre.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(1, "progs/h_ogre1.mdl");
	}
};

void() ogre_inflamed1 = [ 25, ogre_inflamed2 ]
{
	ai_run_inflamed(9);
	if ((random() < 0.8))
	{
		sound7(self, CHAN_VOICE, "ogre/ogpain1.wav", 1, ATTN_NORM, SNDSPD);
	}
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 20)) + (v_up * 38)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_inflamed2 = [ 26, ogre_inflamed3 ]
{
	ai_run_inflamed(12);
	ogre_footsteps(1);
	self.nextthink = (time + 0.07);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 18)) + (v_up * 38)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_inflamed3 = [ 27, ogre_inflamed4 ]
{
	ai_run_inflamed(8);
	self.nextthink = (time + 0.07);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 19)) + (v_up * 38)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_inflamed4 = [ 28, ogre_inflamed5 ]
{
	ai_run_inflamed(22);
	self.nextthink = (time + 0.07);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 21)) + (v_up * 36)) + (v_forward * 3)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_inflamed5 = [ 29, ogre_inflamed6 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.07);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 21)) + (v_up * 35)) + (v_forward * -1)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_inflamed6 = [ 30, ogre_inflamed7 ]
{
	ai_run_inflamed(4);
	ogre_footsteps(1);
	self.nextthink = (time + 0.07);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 21)) + (v_up * 34)) + (v_forward * -4)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_inflamed7 = [ 31, ogre_inflamed8 ]
{
	ai_run_inflamed(13);
	self.nextthink = (time + 0.07);
	if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 1)))
	{
		makevectors(self.angles);
		particleeffectnum(/*52874i*/"ogre_chainsaw_run");
		pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 22)) + (v_up * 42)) + (v_forward * 10)), VEC_ORIGIN, 1);
	}
	else
	{
		if ((((self.model == "progs/ogre.mdl") || (self.model == "progs/ogre1.mdl")) && (self.chainsaw_particles_original_model == 2)))
		{
			makevectors(self.angles);
			particleeffectnum(/*52874i*/"ogre_chainsaw_run");
			pointparticles(particleeffectnum(/*52874i*/"ogre_chainsaw_run"), (((self.origin + (v_right * 21)) + (v_up * 35)) + (v_forward * -8)), VEC_ORIGIN, 1);
		}
	}
};

void() ogre_inflamed8 = [ 32, ogre_inflamed1 ]
{
	local float r;

	ai_run_inflamed(24);
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		ogre_die();
		return;
	}
	r = random();
	if ((r < 0.25))
	{
		ogre_inflamed9();
	}
	else
	{
		if ((r < 0.45))
		{
			ogre_inflamed15();
		}
	}
};

void() ogre_inflamed9 = [ 75, ogre_inflamed10 ]
{
	self.nextthink = (time + 0.07);
	if ((random() < 0.8))
	{
		sound7(self, CHAN_VOICE, "ogre/ogpain1.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() ogre_inflamed10 = [ 76, ogre_inflamed11 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed11 = [ 77, ogre_inflamed12 ]
{
	ogre_footsteps(0.7);
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed12 = [ 78, ogre_inflamed13 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed13 = [ 79, ogre_inflamed14 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed14 = [ 80, ogre_inflamed2 ]
{
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		ogre_die();
		return;
	}
};

void() ogre_inflamed15 = [ 76, ogre_inflamed16 ]
{
	self.nextthink = (time + 0.07);
	if ((random() < 0.8))
	{
		sound7(self, CHAN_VOICE, "ogre/ogpain1.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() ogre_inflamed16 = [ 97, ogre_inflamed17 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed17 = [ 98, ogre_inflamed18 ]
{
	ai_pain(10);
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed18 = [ 99, ogre_inflamed19 ]
{
	ai_pain(9);
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed19 = [ 100, ogre_inflamed20 ]
{
	ai_pain(4);
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed20 = [ 101, ogre_inflamed21 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed21 = [ 102, ogre_inflamed22 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed22 = [ 103, ogre_inflamed23 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed23 = [ 104, ogre_inflamed24 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed24 = [ 105, ogre_inflamed25 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed25 = [ 106, ogre_inflamed26 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed26 = [ 107, ogre_inflamed27 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed27 = [ 108, ogre_inflamed28 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed28 = [ 109, ogre_inflamed29 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed29 = [ 110, ogre_inflamed30 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed30 = [ 111, ogre_inflamed31 ]
{
	self.nextthink = (time + 0.07);
};

void() ogre_inflamed31 = [ 72, ogre_inflamed1 ]
{
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		ogre_die();
		return;
	}
};

void() ogre_die =
{
	local float maxgibs;
	local float gibscounter;
	local float cranf;
	local float zufa;
	local float zufall;
	local float randomness;

	bodyCheck();
	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			ogre_pack();
			ogre_lightning_death();
			return;
		}
	}
	else
	{
		if ((((!self.shocked && (self.enemy.weapon == IT_LIGHTNING)) && (self.enemy.meleeing == 0)) && (self.sticky != 1)))
		{
			lg_death1();
			return;
		}
	}
	if (((self.model == "progs/ogre_half.mdl") && (((self.health < -40) || ((random() < 0.15) && (self.health < -15))) || (self.enemy.weapon == IT_CHAINSAW))))
	{
		pointparticles(particleeffectnum(/*25865i*/"blood_saw"), self.origin, VEC_ORIGIN, 1);
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 1, ATTN_NORM, SNDSPD);
		if ((self.skin == 0))
		{
			ThrowGib("progs/gib_ogre_h.mdl", (self.health / 2));
		}
		else
		{
			ThrowGib("progs/gib_ogre_h1.mdl", (self.health / 2));
		}
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib2.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib2.mdl", self.health);
		ThrowHeart("progs/gibheart.mdl", self.health);
		ThrowWeapon("progs/w_ogregl.mdl", self.health);
		remove(self);
		return;
	}
	else
	{
		if ((self.model == "progs/ogre_half.mdl"))
		{
			pointparticles(particleeffectnum(/*25865i*/"blood_saw"), self.origin, VEC_ORIGIN, 1);
			sound7(self, CHAN_VOICE, "ogre/ogdth.wav", 1, ATTN_NORM, SNDSPD);
			cranf = random() * 0.1;
			if ((self.skin == 0))
			{
				ThrowBody("progs/gib_ogre_half.mdl", (self.health * cranf));
			}
			else
			{
				ThrowBody("progs/gib_ogre_half1.mdl", (self.health * cranf));
			}
			ThrowWeapon("progs/w_ogregl.mdl", (self.health * cranf));
			remove(self);
			return;
		}
	}
	if (((self.health < -45) || ((self.enemy.weapon == IT_CHAINSAW) && (random() < 0.5))))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_ogre * 0.01)))
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
		if ((self.monstermodel == 0))
		{
			ThrowHead("progs/h_ogre.mdl", (self.health * 0.5));
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				ThrowHead("progs/h_ogre1.mdl", (self.health * 0.5));
			}
		}
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", (self.health * 0.5));
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		gibdeath_effects();
		producegibs_ogre(maxgibs, gibscounter);
		return;
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
				ogre_inflamed1();
				return;
			}
		}
		else
		{
			sound7(self, CHAN_VOICE, "ogre/ogdth.wav", 1, ATTN_NORM, SNDSPD);
			if ((random() < 0.5))
			{
				ogre_die1();
			}
			else
			{
				ogre_bdie1();
			}
			return;
		}
	}
	autocvar_ogrerandomness = autocvar_ogrerandomness * 0.01;
	if ((autocvar_ogre == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_ogrerandomness))
		{
			self.delete_painskin = 1;
			ogre_dieburn1();
			return;
		}
	}
	if ((autocvar_ogre == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_ogrerandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				ogre_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_ogre * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "ogre/ogdth.wav", 1, ATTN_NORM, SNDSPD);
	if ((random() < 0.5))
	{
		ogre_die1();
	}
	else
	{
		ogre_bdie1();
	}
	if ((self.enemy.meleeing == 0))
	{
		if ((((self.enemy.weapon == IT_SUPER_SHOTGUN) && (random() < 0.8)) || ((self.enemy.weapon == IT_SHOTGUN) && (random() < 0.5))))
		{
			if (((random() < 0.1) || (self.hitbox_pos == HEAD_SHOT)))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					ThrowGib("progs/gib_ogre_h.mdl", self.health);
					self.model = "progs/ogreblast.mdl";
					setmodel(self, "progs/ogreblast.mdl");
					self.skin = 0;
				}
				else
				{
					ThrowGib("progs/gib_ogre_h1.mdl", self.health);
					self.model = "progs/ogreblast.mdl";
					setmodel(self, "progs/ogreblast.mdl");
					self.skin = 1;
				}
				ogre_diessg1();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
			}
		}
		if ((((self.enemy.weapon == IT_ROCKET_LAUNCHER) || (self.enemy.weapon == IT_GRENADE_LAUNCHER)) && (random() < 0.5)))
		{
			if ((autocvar_bloodextension == 1))
			{
				pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
			}
			ThrowGib("progs/gib3.mdl", self.health);
			ThrowGib("progs/gib3.mdl", self.health);
			ThrowGib("progs/gib3.mdl", self.health);
			ThrowWeapon("progs/w_ogregl.mdl", self.health);
			ThrowWeapon("progs/w_chainsaw.mdl", self.health);
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			ThrowGib("progs/chop.mdl", self.health);
			self.delete_painskin = 1;
			if ((self.skin == 0))
			{
				ThrowGib("progs/h_ogregib.mdl", self.health);
			}
			else
			{
				ThrowGib("progs/h_ogregib1.mdl", self.health);
			}
			self.model = "progs/ogregib.mdl";
			setmodel(self, "progs/ogregib.mdl");
			ogre_dierl1();
		}
		if ((self.enemy.weapon == IT_NAILGUN))
		{
			if (((random() < 0.9) && (self.hitbox_pos == HEAD_SHOT)))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					ThrowGib("progs/gib_ogre_h.mdl", self.health);
					self.model = "progs/ogreblast.mdl";
					setmodel(self, "progs/ogreblast.mdl");
					self.skin = 0;
				}
				else
				{
					ThrowGib("progs/gib_ogre_h1.mdl", self.health);
					self.model = "progs/ogreblast.mdl";
					setmodel(self, "progs/ogreblast.mdl");
					self.skin = 1;
				}
				ogre_diessg1();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
				CeilSplat();
			}
			else
			{
				if ((random() < 0.5))
				{
					if ((autocvar_bloodextension == 1))
					{
						pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					self.delete_painskin = 1;
					if ((self.skin == 0))
					{
						self.model = "progs/ogrenail.mdl";
						setmodel(self, "progs/ogrenail.mdl");
						self.skin = 0;
					}
					else
					{
						self.model = "progs/ogrenail.mdl";
						setmodel(self, "progs/ogrenail.mdl");
						self.skin = 1;
					}
					ogre_dieng1();
				}
				else
				{
					sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
					self.model = "progs/ogre_dmg.mdl";
					setmodel(self, "progs/ogre_dmg.mdl");
				}
			}
		}
		if ((self.enemy.weapon == IT_SUPER_NAILGUN))
		{
			if ((self.hitbox_pos != HEAD_SHOT))
			{
				if ((random() < 0.1))
				{
					self.health = -46;
					ogre_die();
					return;
				}
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/ogrenail.mdl";
					setmodel(self, "progs/ogrenail.mdl");
					self.skin = 0;
				}
				else
				{
					self.model = "progs/ogrenail.mdl";
					setmodel(self, "progs/ogrenail.mdl");
					self.skin = 1;
				}
				if ((random() < 0.6))
				{
					ogre_dieng1();
				}
				else
				{
					self.model = "progs/ogre_dmg.mdl";
					setmodel(self, "progs/ogre_dmg.mdl");
				}
			}
			else
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*52274i*/"blood_facepl"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/ogre_sng.mdl";
					setmodel(self, "progs/ogre_sng.mdl");
					StickGib("progs/gib_ogre_h.mdl", self.health);
					self.skin = 0;
				}
				else
				{
					self.model = "progs/ogre_sng.mdl";
					setmodel(self, "progs/ogre_sng.mdl");
					StickGib("progs/gib_ogre_h1.mdl", self.health);
					self.skin = 1;
				}
				ogre_dieng1();
			}
		}
		if (((self.enemy.weapon == IT_AXE) || (self.enemy.weapon == IT_CHAINSAW)))
		{
			if (((random() < 0.2) || (self.hitbox_pos == HEAD_SHOT)))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				if ((self.skin == 0))
				{
					self.model = "progs/ogreblast.mdl";
					setmodel(self, "progs/ogreblast.mdl");
					self.skin = 0;
					ThrowGib("progs/gib_ogre_h.mdl", self.health);
				}
				else
				{
					self.model = "progs/ogreblast.mdl";
					setmodel(self, "progs/ogreblast.mdl");
					self.skin = 1;
					ThrowGib("progs/gib_ogre_h1.mdl", self.health);
				}
				ogre_diessg1();
			}
			else
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				if ((self.skin == 0))
				{
					self.model = "progs/ogre_axe.mdl";
					setmodel(self, "progs/ogre_axe.mdl");
					self.skin = 0;
					ThrowGib("progs/gib_ogarm.mdl", self.health);
				}
				else
				{
					self.model = "progs/ogre_axe.mdl";
					setmodel(self, "progs/ogre_axe.mdl");
					self.skin = 1;
					ThrowGib("progs/gib_ogarm.mdl", self.health);
				}
				ogre_dieaxe1();
			}
		}
		setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	}
};

void() ogre_melee =
{
	if ((random() > 0.5))
	{
		ogre_smash1();
	}
	else
	{
		ogre_swing1();
	}
};

void() monster_ogre =
{
	local float zufall;
	local float zuffa;
	local float replacerrr;
	local float replacerrrrr;
	local float replacerr;
	local float replacerrrr;
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
	precache_model("progs/ogre.mdl");
	precache_model("progs/ogre_half.mdl");
	precache_model("progs/h_ogre.mdl");
	precache_model("progs/grenade.mdl");
	precache_model("progs/gib_ogre_half.mdl");
	precache_model("progs/gib_ogre_half1.mdl");
	precachegibs_ogre();
	precache_sound("ogre/ogdrag.wav");
	precache_sound("ogre/ogdth.wav");
	precache_sound("ogre/ogidle.wav");
	precache_sound("ogre/ogidle2.wav");
	precache_sound("ogre/ogpain1.wav");
	precache_sound("ogre/ogsawatk.wav");
	precache_sound("ogre/ogwake.wav");
	precache_sound("ogre/fall_backwards.wav");
	precache_sound("ogre/fall_forwards.wav");
	precache_sound("walk/ogre1.wav");
	precache_sound("walk/ogre2.wav");
	precache_sound("walk/ogre3.wav");
	precache_sound("walk/ogre4.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((autocvar_ogremultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/ogre.mdl");
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
		if ((autocvar_ogremultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/ogre1.mdl");
			precache_model("progs/h_ogre1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/ogre.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/ogre1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_ogremultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/ogre1.mdl");
				precache_model("progs/h_ogre1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/ogre.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/ogre.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/ogre1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_ogremultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/ogre1.mdl");
					precache_model("progs/h_ogre1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/ogre.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/ogre.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/ogre1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/ogre1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/ogre.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_ogre_additional_particle_effects == 1))
	{
		self.chainsaw_particles_original_model = 1;
	}
	else
	{
		if ((autocvar_ogre_additional_particle_effects == 2))
		{
			self.chainsaw_particles_original_model = 2;
		}
		else
		{
			if ((autocvar_ogre_additional_particle_effects == 3))
			{
				if ((self.monstermodel == 0))
				{
					self.chainsaw_particles_original_model = 1;
				}
				else
				{
					self.chainsaw_particles_original_model = 2;
				}
			}
			else
			{
				if ((autocvar_ogre_additional_particle_effects == 4))
				{
					if ((self.monstermodel == 0))
					{
						self.chainsaw_particles_original_model = 2;
					}
					else
					{
						self.chainsaw_particles_original_model = 1;
					}
				}
			}
		}
	}
	if ((autocvar_ogre_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.14;
			self.sizediff = '0 0 3';
			setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.07;
				self.sizediff = '0 0 1';
				setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
			}
			else
			{
				self.scale = 1;
				setsize(self, '-22 -22 -24', '22 22 41');
			}
		}
	}
	else
	{
		if ((autocvar_ogre_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.21;
				self.sizediff = '0 0 5';
				setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.14;
					self.sizediff = '0 0 3';
					setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.75))
					{
						self.scale = 1.07;
						self.sizediff = '0 0 1';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, '-22 -22 -24', '22 22 41');
					}
				}
			}
		}
		else
		{
			if ((autocvar_ogre_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.28;
					self.sizediff = '0 0 7';
					setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.21;
						self.sizediff = '0 0 5';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.14;
							self.sizediff = '0 0 3';
							setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.07;
								self.sizediff = '0 0 1';
								setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
							}
							else
							{
								self.scale = 1;
								setsize(self, '-22 -22 -24', '22 22 41');
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_ogre_size == 4))
				{
					zuffa = random();
					if ((zuffa <= 0.17))
					{
						self.scale = 1.35;
						self.sizediff = '0 0 9';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.34))
						{
							self.scale = 1.28;
							self.sizediff = '0 0 7';
							setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
						}
						else
						{
							if ((zuffa <= 0.5))
							{
								self.scale = 1.21;
								self.sizediff = '0 0 5';
								setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
							}
							else
							{
								if ((zuffa <= 0.67))
								{
									self.scale = 1.14;
									self.sizediff = '0 0 3';
									setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
								}
								else
								{
									if ((zuffa <= 0.84))
									{
										self.scale = 1.07;
										self.sizediff = '0 0 1';
										setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
									}
									else
									{
										self.scale = 1;
										setsize(self, '-22 -22 -24', '22 22 41');
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_ogre_size > 4))
					{
						if ((autocvar_ogre_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_ogre_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_ogre_size * 0.25);
						self.sizediff = self.sizefactor;
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, '-22 -22 -24', '22 22 41');
					}
				}
			}
		}
	}
	if ((autocvar_ogre_size_influenced_health == 1))
	{
		self.health = (autocvar_ogre_health * self.scale);
	}
	else
	{
		self.health = autocvar_ogre_health;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_ogre_random_skin_colors))
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
	self.th_stand = ogre_stand1;
	self.th_walk = ogre_walk1;
	self.th_run = ogre_run1;
	self.th_die = ogre_die;
	self.th_melee = ogre_melee;
	self.th_missile = ogre_nail1;
	self.th_pain = ogre_pain;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_torment_replace_ogre)
	{
		replacerrr = autocvar_torment_replace_ogre * 0.01;
		if ((random() <= replacerrr))
		{
			self.health = autocvar_ogre_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_torment_start();
			return;
		}
	}
	if (autocvar_carnivean_replace_ogre)
	{
		replacerrrrr = autocvar_carnivean_replace_ogre * 0.01;
		if ((random() <= replacerrrrr))
		{
			self.health = autocvar_ogre_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_carnivean_start();
			return;
		}
	}
	if (autocvar_warlord_replace_ogre)
	{
		replacerr = autocvar_warlord_replace_ogre * 0.01;
		if (((cvar("skill") == 3) && (replacerr > 0)))
		{
			replacerr = replacerr + 0.01;
		}
		if ((cvar("quadreplacer") > 0))
		{
			replacerr = replacerr + 0.01;
		}
		if ((random() <= replacerr))
		{
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_hell_knight2_start();
			return;
		}
	}
	if ((autocvar_yakman_replace_ogre || (cvar("quadreplacer") > 0)))
	{
		replacerrrr = autocvar_yakman_replace_ogre * 0.01;
		if ((cvar("quadreplacer") > 0))
		{
			replacerrrr = replacerrrr + 0.01;
		}
		if ((random() <= replacerrrr))
		{
			traceline(self.origin, (self.origin + '0 0 76'), FALSE, self);
			if ((trace_fraction != 1))
			{
			}
			else
			{
				self.scale = 1;
				setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_yakman_start();
				return;
			}
		}
	}
	if (autocvar_spider_replace_ogre)
	{
		replacer = autocvar_spider_replace_ogre * 0.01;
		if ((random() <= replacer))
		{
			check = (self.origin - '0 0 20') + '0 0 1';
			if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
			{
				self.skin = 7;
				self.health = autocvar_ogre_health;
				self.scale = 1;
				setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
				self.nextthink = (time + 0.3);
				self.think = SUB_Remove;
				monster_spider_start();
				return;
			}
		}
	}
	if (autocvar_reiver_replace_ogre)
	{
		replacez = autocvar_reiver_replace_ogre * 0.01;
		if ((random() <= replacez))
		{
			self.health = autocvar_ogre_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_reiver_liftorigin_start();
			return;
		}
	}
	if (autocvar_afrit_replace_ogre)
	{
		replac = autocvar_afrit_replace_ogre * 0.01;
		if ((random() <= replac))
		{
			self.health = autocvar_ogre_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
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
	if (autocvar_reiver_supports_ogre)
	{
		replacce = autocvar_reiver_supports_ogre * 0.01;
		if (((cvar("skill") == 3) && (replacce > 0)))
		{
			replacce = replacce + 0.01;
		}
		if (((cvar("quadreplacer") > 0) && (replacce > 0)))
		{
			replacce = replacce + 0.01;
		}
		if ((random() <= replacce))
		{
			add_reiver_support_walk();
		}
	}
	if (autocvar_afrit_supports_ogre)
	{
		replace = autocvar_afrit_supports_ogre * 0.01;
		if (((cvar("skill") == 3) && (replace > 0)))
		{
			replace = replace + 0.01;
		}
		if (((cvar("quadreplacer") > 0) && (replace > 0)))
		{
			replace = replace + 0.01;
		}
		if ((random() <= replace))
		{
			add_afrit_support_walk();
		}
	}
	MonsterPhysics(self, autocvar_ogremass);
};

void() monster_ogre_marksman =
{
	monster_ogre();
};

void() vengeance_ogre_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_ogre_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_ogre_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_skull =
{
	local vector offang;
	local vector org;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = ((self.origin + self.mins) + (self.size * 0.5)) + (v_forward * 20);
	precache_sound("vengeance/skull.wav");
	precache_sound("vengeance/skulltouch.wav");
	OgreFireGrenade();
};

void() vengeance_ogre_skull1 = [ 61, vengeance_ogre_skull2 ]
{
	ai_face();
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_skull2 = [ 62, vengeance_ogre_skull3 ]
{
	ai_face();
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_skull3 = [ 62, vengeance_ogre_skull4 ]
{
	ai_face();
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_skull4 = [ 63, vengeance_ogre_skull5 ]
{
	ai_face();
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_skull5 = [ 63, vengeance_ogre_skull6 ]
{
	ai_face();
	self.touch = vengeance_ogre_touch;
	sound7(self, CHAN_VOICE, "hknight/attack1.wav", 1, 4);
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_skull6 = [ 64, vengeance_ogre_end1 ]
{
	ai_face();
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.15;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	if ((autocvar_quadreplacer > 0))
	{
		vengeance_ogre_skull();
	}
};

void() vengeance_ogre_run1 = [ 25, vengeance_ogre_run2 ]
{
	ai_face();
	movetogoal(14);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_run2 = [ 26, vengeance_ogre_run3 ]
{
	ai_face();
	movetogoal(16);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.37;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_run3 = [ 27, vengeance_ogre_run4 ]
{
	ai_face();
	movetogoal(12);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.34;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_run4 = [ 28, vengeance_ogre_run5 ]
{
	ai_face();
	movetogoal(26);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.31;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	if (((random() < 0.4) && (autocvar_quadreplacer > 0)))
	{
		vengeance_ogre_skull1();
	}
};

void() vengeance_ogre_run5 = [ 29, vengeance_ogre_run6 ]
{
	ai_face();
	movetogoal(20);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.28;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_run6 = [ 30, vengeance_ogre_run7 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.25;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_run7 = [ 31, vengeance_ogre_run8 ]
{
	ai_face();
	movetogoal(17);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.22;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_run8 = [ 32, vengeance_ogre_random ]
{
	ai_face();
	movetogoal(28);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_swing1 = [ 33, vengeance_ogre_swing2 ]
{
	ai_face();
	movetogoal(5);
	sound7(self, CHAN_VOICE, "ogre/ogsawatk.wav", 1, ATTN_NORM, SNDSPD);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.17;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_swing2 = [ 34, vengeance_ogre_swing3 ]
{
	ai_face();
	movetogoal(6);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.14;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_swing3 = [ 35, vengeance_ogre_swing4 ]
{
	ai_face();
	chainsaw(0);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.11;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_swing4 = [ 36, vengeance_ogre_swing5 ]
{
	ai_face();
	chainsaw(0);
	self.touch = vengeance_ogre_touch;
	self.alpha = 0.08;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_swing5 = [ 37, vengeance_ogre_end1 ]
{
	ai_face();
	chainsaw(0);
	self.touch = vengeance_ogre_touch;
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 200) + '0 0 10');
	self.alpha = 0.06;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_random =
{

	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.01);
	if (((random() > 0.5) && (vlen((self.enemy.origin - self.origin)) < 300)))
	{
		self.think = vengeance_ogre_swing1;
	}
	else
	{
		self.think = vengeance_ogre_skull1;
	}
};

void() vengeance_ogre11 = [ 124, vengeance_ogre12 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre12 = [ 123, vengeance_ogre13 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre13 = [ 122, vengeance_ogre14 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre14 = [ 121, vengeance_ogre15 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre15 = [ 120, vengeance_ogre16 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre16 = [ 119, vengeance_ogre17 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre17 = [ 118, vengeance_ogre18 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre18 = [ 117, vengeance_ogre19 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre19 = [ 116, vengeance_ogre120 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre120 = [ 115, vengeance_ogre121 ]
{
	sound7(self, CHAN_WEAPON, "ogre/ogwake.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre121 = [ 114, vengeance_ogre122 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre122 = [ 113, vengeance_ogre123 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre123 = [ 112, vengeance_ogre_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre21 = [ 134, vengeance_ogre22 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre22 = [ 133, vengeance_ogre23 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre23 = [ 132, vengeance_ogre24 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre24 = [ 131, vengeance_ogre25 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre25 = [ 130, vengeance_ogre26 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre26 = [ 129, vengeance_ogre27 ]
{
	sound7(self, CHAN_WEAPON, "ogre/ogwake.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre27 = [ 128, vengeance_ogre28 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre28 = [ 127, vengeance_ogre29 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre29 = [ 126, vengeance_ogre_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_ogre_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	if ((self.frame == 125))
	{
		self.think = vengeance_ogre11;
	}
	else
	{
		self.think = vengeance_ogre21;
	}
};

void() vengeance_ogre_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_ogre_bright05;
};

void() vengeance_ogre_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_ogre_bright04;
};

void() vengeance_ogre_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_ogre_bright03;
};

void() vengeance_ogre_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_ogre_bright02;
};

void() vengeance_ogre_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_ogre_bright01;
};

void(string modelname, float modelframe) vengeance_ogre =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_STEP;
	self.inflamed = 0;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/ogre.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/ogre1.mdl");
		}
	}
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	self.frame = modelframe;
	self.solid = 0;
	MonsterPhysics(self, autocvar_ogremass);
	vengeance_ogre_bright00();
};
