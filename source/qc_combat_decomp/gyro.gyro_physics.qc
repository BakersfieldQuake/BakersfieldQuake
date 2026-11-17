//Decompiled code. Please respect the original copyright.

void(entity e, float mass) Gyro_Object_Activate =
{
	local float reactive;

	Gyro_ObjectList_Add(e);
	if ((e.gyro_object_mass == 0))
	{
		e.gyro_object_mass = mass;
		e.gyro_object_channels = 1;
		reactive = 0;
	}
	else
	{
		reactive = TRUE;
	}
	if ((e.gyro_object_mass <= 0))
	{
		if ((GYRO_OBJECTDEBUG > 0))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Warning: Entity physics not activated for \"");
			bprint(e.classname);
			bprint("\"\nMass cannot be set to zero or below\n");
		}
	}
	e.gyro_velocityeffect = VEC_ORIGIN;
	e.gyro_avelocityeffect = VEC_ORIGIN;
	e.gyro_dampeningeffect = '1 1 1';
	e.gyro_adampeningeffect = '1 1 1';
	e.gyro_antigravityeffect = 0;
	if ((GYRO_OBJECTDEBUG > 0))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity physics activated for \"");
		bprint(e.classname);
		bprint("\"\nMass: ");
		bprint(ftos(e.gyro_object_mass));
		if ((reactive == TRUE))
		{
			bprint(", inactive settings have been restored");
		}
		bprint("\n");
	}
};

void(entity e) Gyro_Object_Deactivate =
{
	Gyro_ObjectList_Remove(e);
	if ((GYRO_OBJECTDEBUG > 0))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity physics deactivated for \"");
		bprint(e.classname);
		bprint("\"\nPhysics settings preserved but inactive\n");
	}
};

void(entity e) Gyro_Object_ClearPhysics =
{
	e.gyro_object_mass = 0;
	e.gyro_object_bouyancy_air = 0;
	e.gyro_object_bouyancy_water = 0;
	e.gyro_object_bouyancy_slime = 0;
	e.gyro_object_bouyancy_lava = 0;
	e.gyro_object_resistance_air = 1;
	e.gyro_object_resistance_water = 1;
	e.gyro_object_resistance_slime = 1;
	e.gyro_object_resistance_lava = 1;
	e.gyro_object_turbulence_air = 0;
	e.gyro_object_turbulence_water = 0;
	e.gyro_object_turbulence_slime = 0;
	e.gyro_object_turbulence_lava = 0;
	e.gyro_object_turbulence_smooth = 0;
	e.gyro_object_turbulence_velocity = VEC_ORIGIN;
	e.gyro_object_globalturb_air = 0;
	e.gyro_object_globalturb_water = 0;
	e.gyro_object_globalturb_slime = 0;
	e.gyro_object_globalturb_lava = 0;
	e.gyro_object_globalturb_smooth = 0;
	e.gyro_object_globalturb_velocity = VEC_ORIGIN;
	e.gyro_object_hover_tap = 0;
	e.gyro_object_hover_dist = 0;
	e.gyro_object_hover_power = 0;
	e.gyro_object_aerodynamics = 0;
	e.gyro_object_angleturb = 0;
	e.gyro_object_thrust = 0;
	e.gyro_object_flags = 0;
	e.gyro_feedback = Gyro_Null;
	Gyro_ObjectList_Remove(e);
	if ((GYRO_OBJECTDEBUG > 0))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity physics cleared for \"");
		bprint(e.classname);
		bprint("\"\nAll physics settings removed\n");
	}
};

void(entity e, float channels) Gyro_Object_SetChannels =
{
	e.gyro_object_channels = channels;
};

void(entity e, float channels) Gyro_Object_AddChannels =
{
	e.gyro_object_channels = (e.gyro_object_channels | channels);
};

void(entity e, float channels) Gyro_Object_RemoveChannels =
{
	e.gyro_object_channels = (e.gyro_object_channels - (e.gyro_object_channels & channels));
};

void(entity e) Gyro_Object_CallFeedback =
{
	local entity oldself;

	if (e.gyro_feedback)
	{
		oldself = self;
		self = e;
		self.gyro_feedback();
		self = oldself;
	}
};

void() Gyro_Object_FeedbackDebug =
{
	bprint("Feedback function called for \"");
	bprint(self.classname);
	bprint("\"\nCalled by: ");
	bprint(gyro_feedback_name);
	bprint(", Power: ");
	bprint(ftos(gyro_feedback_power));
	bprint(", Channels: ");
	bprint(ftos(gyro_feedback_channels));
	bprint("\n");
};

void(entity e) Gyro_RunPhysics_Bouyancy =
{
	local float org_content;
	local float bouypower;
	local float inwater;
	local float top_content;
	local float top_bouyancy;
	local float mid_bouyancy;
	local float mid_content;

	if (!(e.gyro_object_flags & GYRO_OBJECTFLAG_BOUYANCY))
	{
		return;
	}
	org_content = e.gyro_object_pointcontent;
	if ((org_content == -3))
	{
		bouypower = e.gyro_object_bouyancy_water;
		inwater = TRUE;
	}
	else
	{
		if ((org_content == -4))
		{
			bouypower = e.gyro_object_bouyancy_slime;
			inwater = TRUE;
		}
		else
		{
			if ((org_content == -5))
			{
				bouypower = e.gyro_object_bouyancy_lava;
				inwater = TRUE;
			}
			else
			{
				bouypower = e.gyro_object_bouyancy_air;
			}
		}
	}
	e.gyro_object_flags = (e.gyro_object_flags - (e.gyro_object_flags & GYRO_OBJECTFLAG_FLOATING));
	if (((e.gyro_velocityeffect_z < 60) && (e.gyro_velocityeffect_z > -60)))
	{
		top_content = pointcontents((e.origin + '0 0 2.4'));
		if ((top_content != org_content))
		{
			if ((top_content == -3))
			{
				top_bouyancy = e.gyro_object_bouyancy_water;
			}
			else
			{
				if ((top_content == -4))
				{
					top_bouyancy = e.gyro_object_bouyancy_slime;
				}
				else
				{
					if ((top_content == -5))
					{
						top_bouyancy = e.gyro_object_bouyancy_lava;
					}
					else
					{
						top_bouyancy = e.gyro_object_bouyancy_air;
					}
				}
			}
			mid_content = pointcontents((e.origin + '0 0 1.2'));
			if ((mid_content == top_content))
			{
				mid_bouyancy = top_bouyancy;
			}
			else
			{
				mid_bouyancy = bouypower;
			}
			bouypower = ((bouypower + top_bouyancy) + mid_bouyancy) / 3;
			e.gyro_dampeningeffect_z = (e.gyro_dampeningeffect_z * Gyro_PowerEstimation(0.2, GYRO_TICKRATE));
			e.gyro_object_flags = (e.gyro_object_flags | GYRO_OBJECTFLAG_FLOATING);
		}
	}
	if (e.gyro_feedback)
	{
		if (inwater)
		{
			gyro_feedback_channels = 0;
			gyro_feedback_power = bouypower * e.gyro_object_mass;
			if ((org_content == -3))
			{
				gyro_feedback_name = "water";
			}
			else
			{
				if ((org_content == -4))
				{
					gyro_feedback_name = "slime";
				}
				else
				{
					if ((org_content == -5))
					{
						gyro_feedback_name = "lava";
					}
				}
			}
			Gyro_Object_CallFeedback(e);
		}
	}
	e.gyro_velocityeffect_z = (e.gyro_velocityeffect_z + ((bouypower * gyro_framegrav) * GYRO_TICKRATE));
};

void(entity e) Gyro_Object_RemoveBouyancy =
{
	e.gyro_object_bouyancy_air = 0;
	e.gyro_object_bouyancy_water = 0;
	e.gyro_object_bouyancy_slime = 0;
	e.gyro_object_bouyancy_lava = 0;
	e.gyro_object_flags = (e.gyro_object_flags - (e.gyro_object_flags & GYRO_OBJECTFLAG_BOUYANCY));
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity bouyancy removed from \"");
		bprint(e.classname);
		bprint("\"\n");
	}
};

void(entity e, float bouyforce, float mod_air, float mod_water, float mod_slime, float mod_lava) Gyro_Object_SetBouyancyMod =
{
	local float bouypower;

	if ((bouyforce == 0))
	{
		return (Gyro_Object_RemoveBouyancy(e));
	}
	bouypower = bouyforce / e.gyro_object_mass;
	e.gyro_object_bouyancy_air = (bouypower * mod_air);
	e.gyro_object_bouyancy_water = (bouypower * mod_water);
	e.gyro_object_bouyancy_slime = (bouypower * mod_slime);
	e.gyro_object_bouyancy_lava = (bouypower * mod_lava);
	e.gyro_object_flags = (e.gyro_object_flags | GYRO_OBJECTFLAG_BOUYANCY);
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity bouyancy activated for \"");
		bprint(e.classname);
		bprint("\"\nMass: ");
		bprint(ftos(e.gyro_object_mass));
		bprint(", Bouyancy: ");
		bprint(ftos(bouyforce));
		bprint("\n");
	}
};

void(entity e, float bouyforce) Gyro_Object_SetBouyancy =
{
	Gyro_Object_SetBouyancyMod(e, bouyforce, GYRO_BOUYANCYMOD_AIR, GYRO_BOUYANCYMOD_WATER, GYRO_BOUYANCYMOD_SLIME, GYRO_BOUYANCYMOD_LAVA);
};

void(entity e) Gyro_RunPhysics_Resistance =
{
	local float resistpower;

	if (!(e.gyro_object_flags & GYRO_OBJECTFLAG_RESISTANCE))
	{
		return;
	}
	if ((e.gyro_object_pointcontent == -3))
	{
		resistpower = e.gyro_object_resistance_water;
	}
	else
	{
		if ((e.gyro_object_pointcontent == -4))
		{
			resistpower = e.gyro_object_resistance_slime;
		}
		else
		{
			if ((e.gyro_object_pointcontent == -5))
			{
				resistpower = e.gyro_object_resistance_lava;
			}
			else
			{
				resistpower = e.gyro_object_resistance_air;
			}
		}
	}
	resistpower = Gyro_PowerEstimation(resistpower, GYRO_TICKRATE);
	e.gyro_dampeningeffect = (e.gyro_dampeningeffect * resistpower);
	e.gyro_adampeningeffect = (e.gyro_adampeningeffect * resistpower);
};

void(entity e) Gyro_Object_RemoveResistance =
{
	e.gyro_object_resistance_air = 1;
	e.gyro_object_resistance_water = 1;
	e.gyro_object_resistance_slime = 1;
	e.gyro_object_resistance_lava = 1;
	e.gyro_object_flags = (e.gyro_object_flags - (e.gyro_object_flags & GYRO_OBJECTFLAG_RESISTANCE));
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity motion resistance removed from \"");
		bprint(e.classname);
		bprint("\"\n");
	}
};

void(entity e, float resforce, float mod_air, float mod_water, float mod_slime, float mod_lava) Gyro_Object_SetResistanceMod =
{
	if ((resforce == 0))
	{
		return (Gyro_Object_RemoveResistance(e));
	}
	e.gyro_object_resistance_air = (1 / ((((resforce * mod_air) * 10) / e.gyro_object_mass) + 1));
	e.gyro_object_resistance_water = (1 / ((((resforce * mod_water) * 10) / e.gyro_object_mass) + 1));
	e.gyro_object_resistance_slime = (1 / ((((resforce * mod_slime) * 10) / e.gyro_object_mass) + 1));
	e.gyro_object_resistance_lava = (1 / ((((resforce * mod_lava) * 10) / e.gyro_object_mass) + 1));
	e.gyro_object_flags = (e.gyro_object_flags | GYRO_OBJECTFLAG_RESISTANCE);
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity motion resistance activated for \"");
		bprint(e.classname);
		bprint("\"\nMass: ");
		bprint(ftos(e.gyro_object_mass));
		bprint(", Resistance: ");
		bprint(ftos(resforce));
		bprint("\n");
	}
};

void(entity e, float resforce) Gyro_Object_SetResistance =
{
	Gyro_Object_SetResistanceMod(e, resforce, GYRO_RESISTANCEMOD_AIR, GYRO_RESISTANCEMOD_WATER, GYRO_RESISTANCEMOD_SLIME, GYRO_RESISTANCEMOD_LAVA);
};

void(entity e) Gyro_RunPhysics_Aerodynamics =
{
	local float movespeed;
	local float aeropower;
	local float avelmult;
	local float adampmult;
	local vector moveangle;
	local vector turnangle;

	if ((e.gyro_object_aerodynamics == 0))
	{
		return;
	}
	if ((e.velocity == VEC_ORIGIN))
	{
		return;
	}
	movespeed = vlen(e.velocity);
	if ((e.gyro_object_aerodynamics > 0))
	{
		aeropower = e.gyro_object_aerodynamics * 0.01;
		moveangle = vectoangles(e.velocity);
	}
	else
	{
		aeropower = e.gyro_object_aerodynamics * -0.01;
		moveangle = vectoangles((VEC_ORIGIN - e.velocity));
	}
	if ((e.gyro_object_flags & GYRO_OBJECTFLAG_FLOATING))
	{
		moveangle_x = 0;
		movespeed = movespeed + 200;
	}
	avelmult = movespeed * aeropower;
	adampmult = 1 / (((movespeed * aeropower) * 0.2) + 1);
	turnangle = moveangle - e.angles;
	while ((turnangle_x > 180))
	{
		turnangle_x = turnangle_x - 360;
	}
	while ((turnangle_x < -180))
	{
		turnangle_x = turnangle_x + 360;
	}
	while ((0 > 180))
	{
	}
	while (((0 - 360) < -180))
	{
	}
	while ((0 > 180))
	{
	}
	while (((0 - 360) < -180))
	{
	}
	e.gyro_avelocityeffect = (e.gyro_avelocityeffect + ((turnangle * avelmult) * GYRO_TICKRATE));
	e.gyro_adampeningeffect = (e.gyro_adampeningeffect * Gyro_PowerEstimation(adampmult, GYRO_TICKRATE));
};

void(entity e) Gyro_Object_RemoveAerodynamics =
{
	e.gyro_object_aerodynamics = 0;
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity aerodynamics removed from \"");
		bprint(e.classname);
		bprint("\"\n");
	}
};

void(entity e, float aeroforce) Gyro_Object_SetAerodynamics =
{
	if ((aeroforce == 0))
	{
		return (Gyro_Object_RemoveAerodynamics(e));
	}
	e.gyro_object_aerodynamics = (aeroforce / e.gyro_object_mass);
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity aerodynamics activated for \"");
		bprint(e.classname);
		bprint("\"\nMass: ");
		bprint(ftos(e.gyro_object_mass));
		bprint(", Aerodynamics: ");
		bprint(ftos(aeroforce));
		bprint("\n");
	}
};

void(entity e) Gyro_RunPhysics_Thrust =
{
	local vector gyrothrust;

	if ((e.gyro_object_thrust == 0))
	{
		return;
	}
	makevectors(e.angles);
	gyrothrust = v_forward;
	e.gyro_velocityeffect = (e.gyro_velocityeffect + (((gyrothrust * e.gyro_object_thrust) * GYRO_TICKRATE) * GYRO_POWERCONSTANT));
};

void(entity e) Gyro_Object_RemoveThrust =
{
	e.gyro_object_thrust = 0;
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity thrust removed from \"");
		bprint(e.classname);
		bprint("\"\n");
	}
};

void(entity e, float thrustforce) Gyro_Object_SetThrust =
{
	if ((thrustforce == 0))
	{
		return (Gyro_Object_RemoveThrust(e));
	}
	e.gyro_object_thrust = (thrustforce / e.gyro_object_mass);
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity thrust activated for \"");
		bprint(e.classname);
		bprint("\"\nMass: ");
		bprint(ftos(e.gyro_object_mass));
		bprint(", Thrust: ");
		bprint(ftos(thrustforce));
		bprint("\n");
	}
};

vector(vector taporigin, vector tapdir, float tapdist) Gyro_RunHoverTap =
{
	traceline(taporigin, (taporigin - (tapdir * tapdist)), TRUE, world);
	return ((tapdir * (1 - trace_fraction)));
};

void(entity e) Gyro_RunPhysics_Hover =
{
	local vector totalpush;
	local float tapsleft;
	local vector tapoffset;
	local float z_dampen;

	if ((e.gyro_object_hover_tap <= 0))
	{
		return;
	}
	if ((e.gyro_object_hover_dist <= 0))
	{
		return;
	}
	if ((e.gyro_object_hover_power <= 0))
	{
		return;
	}
	tapsleft = ceil(e.gyro_object_hover_tap);
	while (tapsleft)
	{
		if ((tapsleft > 1))
		{
			tapoffset_x = random() - 0.5;
			totalpush = totalpush + Gyro_RunHoverTap(e.origin, ('0 0 1' + tapoffset), e.gyro_object_hover_dist);
			totalpush = totalpush + Gyro_RunHoverTap(e.origin, ('0 0 1' - tapoffset), e.gyro_object_hover_dist);
			tapsleft = tapsleft - 2;
		}
		else
		{
			totalpush = totalpush + Gyro_RunHoverTap(e.origin, '0 0 1', e.gyro_object_hover_dist);
			tapsleft = tapsleft - 1;
		}
	}
	totalpush = totalpush * (1 / ceil(e.gyro_object_hover_tap));
	z_dampen = Gyro_PowerEstimation((1 - (vlen(totalpush) * 0.7)), GYRO_TICKRATE);
	e.gyro_velocityeffect = (e.gyro_velocityeffect + (((totalpush * e.gyro_object_hover_power) * gyro_framegrav) * GYRO_TICKRATE));
	e.gyro_dampeningeffect_z = (e.gyro_dampeningeffect_z * z_dampen);
};

void(entity e) Gyro_Object_RemoveHover =
{
	e.gyro_object_hover_tap = 0;
	e.gyro_object_hover_dist = 0;
	e.gyro_object_hover_power = 0;
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity hover removed from \"");
		bprint(e.classname);
		bprint("\"\n");
	}
};

void(entity e, float hoverforce, float hoverdist, float hovertap) Gyro_Object_SetHover =
{
	if ((hoverforce <= 0))
	{
		return (Gyro_Object_RemoveThrust(e));
	}
	if ((hoverdist <= 0))
	{
		return (Gyro_Object_RemoveThrust(e));
	}
	if ((hovertap <= 0))
	{
		return (Gyro_Object_RemoveThrust(e));
	}
	hovertap = ceil(hovertap);
	e.gyro_object_hover_tap = hovertap;
	e.gyro_object_hover_dist = hoverdist;
	e.gyro_object_hover_power = (hoverforce / e.gyro_object_mass);
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity thrust activated for \"");
		bprint(e.classname);
		bprint("\"\nMass: ");
		bprint(ftos(e.gyro_object_mass));
		bprint(", Strength: ");
		bprint(ftos(hoverforce));
		bprint(", Tap: ");
		bprint(ftos(hovertap));
		bprint("\n");
	}
};

void(entity e) Gyro_RunPhysics_Turbulence =
{
	local float turbpower;
	local vector extravel;

	if (!(e.gyro_object_flags & GYRO_OBJECTFLAG_TURBULENCE))
	{
		return;
	}
	if ((e.gyro_object_pointcontent == -3))
	{
		turbpower = e.gyro_object_turbulence_water;
	}
	else
	{
		if ((e.gyro_object_pointcontent == -4))
		{
			turbpower = e.gyro_object_turbulence_slime;
		}
		else
		{
			if ((e.gyro_object_pointcontent == -5))
			{
				turbpower = e.gyro_object_turbulence_lava;
			}
			else
			{
				turbpower = e.gyro_object_turbulence_air;
			}
		}
	}
	turbpower = (turbpower * GYRO_POWERCONSTANT) * GYRO_TICKRATE;
	if ((turbpower <= 0))
	{
		return;
	}
	if ((e.gyro_object_turbulence_smooth <= 0))
	{
		e.gyro_object_turbulence_velocity_x = ((random() - 0.5) * turbpower);
		e.gyro_object_turbulence_velocity_y = ((random() - 0.5) * turbpower);
		e.gyro_object_turbulence_velocity_z = ((random() - 0.5) * turbpower);
	}
	else
	{
		if ((e.gyro_object_turbulence_smooth < 1))
		{
			extravel_x = (random() - 0.5) * turbpower;
			e.gyro_object_turbulence_velocity = ((e.gyro_object_turbulence_velocity * e.gyro_object_turbulence_smooth) + (extravel * (1 - e.gyro_object_turbulence_smooth)));
		}
	}
	if ((pointcontents((e.origin + e.gyro_object_turbulence_velocity)) != -2))
	{
		if ((e.gyro_object_flags & GYRO_OBJECTFLAG_FLOATING))
		{
			e.gyro_object_turbulence_velocity_z = 0;
		}
		e.gyro_velocityeffect = (e.gyro_velocityeffect + e.gyro_object_turbulence_velocity);
	}
};

void(entity e) Gyro_Object_RemoveTurbulence =
{
	e.gyro_object_turbulence_air = 0;
	e.gyro_object_turbulence_water = 0;
	e.gyro_object_turbulence_slime = 0;
	e.gyro_object_turbulence_lava = 0;
	e.gyro_object_turbulence_smooth = 0;
	e.gyro_object_turbulence_velocity = VEC_ORIGIN;
	e.gyro_object_flags = (e.gyro_object_flags - (e.gyro_object_flags & GYRO_OBJECTFLAG_TURBULENCE));
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity turbulence removed from \"");
		bprint(e.classname);
		bprint("\"\n");
	}
};

void(entity e, float turbforce, float smoothness, float airmod, float watermod, float slimemod, float lavamod) Gyro_Object_SetTurbulenceMod =
{
	if ((turbforce <= 0))
	{
		return (Gyro_Object_RemoveTurbulence(e));
	}
	turbforce = turbforce / e.gyro_object_mass;
	e.gyro_object_turbulence_air = (turbforce * airmod);
	e.gyro_object_turbulence_water = (turbforce * watermod);
	e.gyro_object_turbulence_slime = (turbforce * slimemod);
	e.gyro_object_turbulence_lava = (turbforce * lavamod);
	e.gyro_object_flags = (e.gyro_object_flags | GYRO_OBJECTFLAG_TURBULENCE);
	e.gyro_object_turbulence_smooth = smoothness;
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity turbulence activated for \"");
		bprint(e.classname);
		bprint("\"\nMass: ");
		bprint(ftos(e.gyro_object_mass));
		bprint(", Turbulence: ");
		bprint(ftos(turbforce));
		bprint(", Smoothness: ");
		bprint(ftos((smoothness * 100)));
		bprint("%\n");
	}
};

void(entity e, float turbforce, float smoothness) Gyro_Object_SetTurbulence =
{
	Gyro_Object_SetTurbulenceMod(e, turbforce, smoothness, GYRO_TURBULENCEMOD_AIR, GYRO_TURBULENCEMOD_WATER, GYRO_TURBULENCEMOD_SLIME, GYRO_TURBULENCEMOD_LAVA);
};

void(entity e) Gyro_RunPhysics_GlobalTurb =
{
	local float turbpower;

	if (!(e.gyro_object_flags & GYRO_OBJECTFLAG_GLOBALTURB))
	{
		return;
	}
	if ((e.gyro_object_pointcontent == -3))
	{
		turbpower = e.gyro_object_globalturb_water;
	}
	else
	{
		if ((e.gyro_object_pointcontent == -4))
		{
			turbpower = e.gyro_object_globalturb_slime;
		}
		else
		{
			if ((e.gyro_object_pointcontent == -5))
			{
				turbpower = e.gyro_object_globalturb_lava;
			}
			else
			{
				turbpower = e.gyro_object_globalturb_air;
			}
		}
	}
	turbpower = (turbpower * GYRO_POWERCONSTANT) * GYRO_TICKRATE;
	if ((turbpower <= 0))
	{
		return;
	}
	if ((e.gyro_object_globalturb_smooth <= 0))
	{
		e.gyro_object_globalturb_velocity = (gyro_globalturbulence * turbpower);
	}
	else
	{
		if ((e.gyro_object_globalturb_smooth < 1))
		{
			e.gyro_object_globalturb_velocity = ((e.gyro_object_globalturb_velocity * e.gyro_object_globalturb_smooth) + ((turbpower * gyro_globalturbulence) * (1 - e.gyro_object_globalturb_smooth)));
		}
	}
	if ((pointcontents((e.origin + e.gyro_object_globalturb_velocity)) != -2))
	{
		if ((e.gyro_object_flags & GYRO_OBJECTFLAG_FLOATING))
		{
			e.gyro_object_globalturb_velocity_z = 0;
		}
		e.gyro_velocityeffect = (e.gyro_velocityeffect + e.gyro_object_globalturb_velocity);
	}
};

void(entity e) Gyro_Object_RemoveGlobalTurb =
{
	e.gyro_object_globalturb_air = 0;
	e.gyro_object_globalturb_water = 0;
	e.gyro_object_globalturb_slime = 0;
	e.gyro_object_globalturb_lava = 0;
	e.gyro_object_globalturb_smooth = 0;
	e.gyro_object_globalturb_velocity = VEC_ORIGIN;
	e.gyro_object_flags = (e.gyro_object_flags - (e.gyro_object_flags & GYRO_OBJECTFLAG_GLOBALTURB));
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity global-turbulence removed from \"");
		bprint(e.classname);
		bprint("\"\n");
	}
};

void(entity e, float turbforce, float smoothness, float airmod, float watermod, float slimemod, float lavamod) Gyro_Object_SetGlobalTurbMod =
{
	if ((turbforce <= 0))
	{
		return (Gyro_Object_RemoveGlobalTurb(e));
	}
	turbforce = turbforce / e.gyro_object_mass;
	e.gyro_object_globalturb_air = (turbforce * airmod);
	e.gyro_object_globalturb_water = (turbforce * watermod);
	e.gyro_object_globalturb_slime = (turbforce * slimemod);
	e.gyro_object_globalturb_lava = (turbforce * lavamod);
	e.gyro_object_globalturb_smooth = smoothness;
	e.gyro_object_flags = (e.gyro_object_flags | GYRO_OBJECTFLAG_GLOBALTURB);
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity global-turbulence activated for \"");
		bprint(e.classname);
		bprint("\"\nMass: ");
		bprint(ftos(e.gyro_object_mass));
		bprint(", Turbulence: ");
		bprint(ftos(turbforce));
		bprint("\n");
	}
};

void(entity e, float turbforce, float smoothness) Gyro_Object_SetGlobalTurb =
{
	Gyro_Object_SetGlobalTurbMod(e, turbforce, smoothness, GYRO_TURBULENCEMOD_AIR, GYRO_TURBULENCEMOD_WATER, GYRO_TURBULENCEMOD_SLIME, GYRO_TURBULENCEMOD_LAVA);
};

void(entity e) Gyro_RunPhysics_AngleTurb =
{
	local float turbeffect;

	if ((e.gyro_object_angleturb == 0))
	{
		return;
	}
	turbeffect = (e.gyro_object_angleturb * GYRO_TICKRATE) * 360;
	e.gyro_avelocityeffect_x = (e.gyro_avelocityeffect_x + ((random() - 0.5) * turbeffect));
	e.gyro_avelocityeffect_y = (e.gyro_avelocityeffect_y + ((random() - 0.5) * turbeffect));
	e.gyro_avelocityeffect_z = (e.gyro_avelocityeffect_z + ((random() - 0.5) * turbeffect));
};

void(entity e) Gyro_Object_RemoveAngleTurb =
{
	e.gyro_object_angleturb = 0;
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity angular-turbulence removed from \"");
		bprint(e.classname);
		bprint("\"\n");
	}
};

void(entity e, float turbforce) Gyro_Object_SetAngleTurb =
{
	if ((turbforce <= 0))
	{
		return (Gyro_Object_RemoveAngleTurb(e));
	}
	e.gyro_object_angleturb = (turbforce / e.gyro_object_mass);
	if ((GYRO_OBJECTDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Entity angular-turbulence activated for \"");
		bprint(e.classname);
		bprint("\"\nMass: ");
		bprint(ftos(e.gyro_object_mass));
		bprint(", Turbulence: ");
		bprint(ftos(turbforce));
		bprint("\n");
	}
};

void() Gyro_RunPhysics =
{
	local entity gyrohead;
	local float gyroheadcount;
	local float movespeed;

	gyro_globalturbulence_x = random() - 0.5;
	gyrohead = gyro_objectlist_head;
	while (gyrohead)
	{
		gyrohead.gyro_object_pointcontent = pointcontents(gyrohead.origin);
		Gyro_RunPhysics_Bouyancy(gyrohead);
		Gyro_RunPhysics_Resistance(gyrohead);
		Gyro_RunPhysics_Aerodynamics(gyrohead);
		Gyro_RunPhysics_Thrust(gyrohead);
		Gyro_RunPhysics_Hover(gyrohead);
		Gyro_RunPhysics_Turbulence(gyrohead);
		Gyro_RunPhysics_AngleTurb(gyrohead);
		Gyro_RunPhysics_GlobalTurb(gyrohead);
		if (((gyrohead.flags & FL_ONGROUND) && (gyrohead.movetype != 3)))
		{
			gyrohead.velocity = VEC_ORIGIN;
			gyrohead.avelocity = VEC_ORIGIN;
		}
		gyrohead.velocity_x = (gyrohead.velocity_x * gyrohead.gyro_dampeningeffect_x);
		gyrohead.velocity_y = (gyrohead.velocity_y * gyrohead.gyro_dampeningeffect_y);
		gyrohead.velocity_z = (gyrohead.velocity_z * gyrohead.gyro_dampeningeffect_z);
		gyrohead.avelocity_x = (gyrohead.avelocity_x * gyrohead.gyro_adampeningeffect_x);
		gyrohead.avelocity_y = (gyrohead.avelocity_y * gyrohead.gyro_adampeningeffect_y);
		gyrohead.avelocity_z = (gyrohead.avelocity_z * gyrohead.gyro_adampeningeffect_z);
		gyrohead.velocity = (gyrohead.velocity + gyrohead.gyro_velocityeffect);
		gyrohead.avelocity = (gyrohead.avelocity + gyrohead.gyro_avelocityeffect);
		if (((gyrohead.gyro_antigravityeffect > 0) && (gyrohead.movetype != 9)))
		{
			if ((gyrohead.gyro_antigravityeffect > 1))
			{
				gyrohead.gyro_antigravityeffect = 1;
			}
			gyrohead.velocity_z = (gyrohead.velocity_z + ((gyrohead.gyro_antigravityeffect * gyro_framegrav) * GYRO_TICKRATE));
		}
		if (((gyrohead.flags & FL_ONGROUND) && (gyrohead.movetype != 3)))
		{
			movespeed = vlen(gyrohead.velocity);
			if ((movespeed > ((gyro_framegrav * GYRO_TICKRATE) * 1.2)))
			{
				if ((gyrohead.velocity_z < 0))
				{
					gyrohead.velocity_z = (0 - gyrohead.velocity_z);
				}
				if ((gyrohead.velocity_z < 100))
				{
					gyrohead.velocity_z = 100;
				}
				gyrohead.flags = (gyrohead.flags - FL_ONGROUND);
			}
			else
			{
				gyrohead.velocity = VEC_ORIGIN;
				gyrohead.avelocity = VEC_ORIGIN;
			}
		}
		if (GYRO_MOTIONCORRECTION)
		{
			if ((gyrohead.velocity_x > gyro_framemaxvel))
			{
				gyrohead.velocity = (gyrohead.velocity * (gyro_framemaxvel / gyrohead.velocity_x));
			}
			if ((gyrohead.velocity_x < gyro_framemaxvelneg))
			{
				gyrohead.velocity = (gyrohead.velocity * (gyro_framemaxvelneg / gyrohead.velocity_x));
			}
			if ((gyrohead.velocity_y > gyro_framemaxvel))
			{
				gyrohead.velocity = (gyrohead.velocity * (gyro_framemaxvel / gyrohead.velocity_y));
			}
			if ((gyrohead.velocity_y < gyro_framemaxvelneg))
			{
				gyrohead.velocity = (gyrohead.velocity * (gyro_framemaxvelneg / gyrohead.velocity_y));
			}
			if ((gyrohead.velocity_z > gyro_framemaxvel))
			{
				gyrohead.velocity = (gyrohead.velocity * (gyro_framemaxvel / gyrohead.velocity_z));
			}
			if ((gyrohead.velocity_z < gyro_framemaxvelneg))
			{
				gyrohead.velocity = (gyrohead.velocity * (gyro_framemaxvelneg / gyrohead.velocity_z));
			}
		}
		gyrohead.gyro_velocityeffect = VEC_ORIGIN;
		gyrohead.gyro_avelocityeffect = VEC_ORIGIN;
		gyrohead.gyro_dampeningeffect = '1 1 1';
		gyrohead.gyro_adampeningeffect = '1 1 1';
		gyrohead.gyro_antigravityeffect = 0;
		gyroheadcount = gyroheadcount + 1;
		gyrohead = gyrohead.gyro_objectlist_next;
	}
};
