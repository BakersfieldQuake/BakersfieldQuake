//Decompiled code. Please respect the original copyright.

entity(string forcename, vector org) Gyro_Force_Create =
{
	local entity f;

	if (((autocvar_gyroset == 0) && !gyro_objectlist_head))
	{
		return (world);
	}
	if ((GYRO_FORCEDEBUG > 0))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Empty force entity \"");
		bprint(forcename);
		bprint("\" created\n");
	}
	f = spawn();
	Gyro_ForceList_Add(f);
	setorigin(f, org);
	f.classname = forcename;
	f.gyro_force_falloff_combine = 0;
	f.gyro_force_rangescale = 1;
	f.gyro_force_rangescalerate = 0;
	f.gyro_force_powerscale = 1;
	f.gyro_force_powerscalerate = 0;
	f.gyro_force_channels = 1;
	f.gyro_force_update = TRUE;
	return (f);
};

void(entity f) Gyro_Force_Remove =
{
	if (!f)
	{
		return;
	}
	if ((GYRO_FORCEDEBUG > 0))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Removed force entity \"");
		bprint(f.classname);
		bprint("\"\n");
	}
	remove(f);
};

void(entity f, vector fallaxis) Gyro_Force_Update_AreaBounds =
{
	fallaxis = fallaxis * f.gyro_force_rangescale;
	if ((fallaxis_x > 0))
	{
		if (((fallaxis_x < f.gyro_force_bounds_x) || (f.gyro_force_bounds_x == 0)))
		{
			f.gyro_force_bounds_x = fallaxis_x;
		}
	}
	if ((fallaxis_y > 0))
	{
		if (((fallaxis_y < f.gyro_force_bounds_y) || (f.gyro_force_bounds_y == 0)))
		{
			f.gyro_force_bounds_y = fallaxis_y;
		}
	}
	if ((fallaxis_z > 0))
	{
		if (((fallaxis_z < f.gyro_force_bounds_z) || (f.gyro_force_bounds_z == 0)))
		{
			f.gyro_force_bounds_z = fallaxis_z;
		}
	}
};

void(entity f, vector fallaxis, float rad1, float rad2) Gyro_Force_Update_ConeBounds =
{
	if ((f.gyro_force_rangescale != 1))
	{
		fallaxis = fallaxis * f.gyro_force_rangescale;
		rad1 = rad1 * f.gyro_force_rangescale;
		rad2 = rad2 * f.gyro_force_rangescale;
	}
	fallaxis_x = fabs(fallaxis_x) + rad2;
	fallaxis_y = fabs(fallaxis_y) + rad2;
	fallaxis_z = fabs(fallaxis_z) + rad2;
	if ((rad1 > fallaxis_x))
	{
		fallaxis_x = rad2;
	}
	if ((rad1 > fallaxis_y))
	{
		fallaxis_y = rad2;
	}
	if ((rad1 > fallaxis_z))
	{
		fallaxis_z = rad2;
	}
	if (((fallaxis_x < f.gyro_force_bounds_x) || (f.gyro_force_bounds_x == 0)))
	{
		f.gyro_force_bounds_x = fallaxis_x;
	}
	if (((fallaxis_y < f.gyro_force_bounds_y) || (f.gyro_force_bounds_y == 0)))
	{
		f.gyro_force_bounds_y = fallaxis_y;
	}
	if (((fallaxis_z < f.gyro_force_bounds_z) || (f.gyro_force_bounds_z == 0)))
	{
		f.gyro_force_bounds_z = fallaxis_z;
	}
};

void(entity f) Gyro_Force_Update =
{
	if ((f.gyro_force_rangescale == 0))
	{
		return;
	}
	f.gyro_force_bounds = VEC_ORIGIN;
	if ((f.gyro_force_falloff1_type & GYRO_FALLOFF_TYPE_AREA))
	{
		Gyro_Force_Update_AreaBounds(f, f.gyro_force_falloff1_axis);
	}
	else
	{
		if ((f.gyro_force_falloff1_type & GYRO_FALLOFF_TYPE_CONE))
		{
			Gyro_Force_Update_ConeBounds(f, f.gyro_force_falloff1_axis, f.gyro_force_falloff1_rad1, f.gyro_force_falloff1_rad2);
		}
	}
	if ((f.gyro_force_falloff2_type & GYRO_FALLOFF_TYPE_AREA))
	{
		Gyro_Force_Update_AreaBounds(f, f.gyro_force_falloff2_axis);
	}
	else
	{
		if ((f.gyro_force_falloff2_type & GYRO_FALLOFF_TYPE_CONE))
		{
			Gyro_Force_Update_ConeBounds(f, f.gyro_force_falloff2_axis, f.gyro_force_falloff2_rad1, f.gyro_force_falloff2_rad2);
		}
	}
	if ((f.gyro_force_falloff3_type & GYRO_FALLOFF_TYPE_AREA))
	{
		Gyro_Force_Update_AreaBounds(f, f.gyro_force_falloff3_axis);
	}
	else
	{
		if ((f.gyro_force_falloff3_type & GYRO_FALLOFF_TYPE_CONE))
		{
			Gyro_Force_Update_ConeBounds(f, f.gyro_force_falloff3_axis, f.gyro_force_falloff3_rad1, f.gyro_force_falloff3_rad2);
		}
	}
	if ((f.gyro_force_falloff4_type & GYRO_FALLOFF_TYPE_AREA))
	{
		Gyro_Force_Update_AreaBounds(f, f.gyro_force_falloff4_axis);
	}
	else
	{
		if ((f.gyro_force_falloff4_type & GYRO_FALLOFF_TYPE_CONE))
		{
			Gyro_Force_Update_ConeBounds(f, f.gyro_force_falloff4_axis, f.gyro_force_falloff4_rad1, f.gyro_force_falloff4_rad2);
		}
	}
	if (((GYRO_FORCEDEBUG > 1) && (f.gyro_force_rangescalerate == 0)))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Bounding box calculated for \"");
		bprint(f.classname);
		bprint("\"\nX: ");
		bprint(ftos(f.gyro_force_bounds_x));
		bprint(", Y: ");
		bprint(ftos(f.gyro_force_bounds_y));
		bprint(", Z: ");
		bprint(ftos(f.gyro_force_bounds_z));
		bprint("\n");
	}
};

void(entity f) Gyro_Force_Detach =
{
	if (!f)
		return;
	if (((f.gyro_force_attach.modelindex != 0) && (f.gyro_force_attach.origin != VEC_ORIGIN)))
	{
		f.origin = f.gyro_force_attach.origin;
	}
	f.gyro_force_attach = world;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Force has been detached \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f, entity e) Gyro_Force_Attach =
{
	if (!f)
		return;
	if ((e == world))
	{
		return (Gyro_Force_Detach(f));
	}
	f.gyro_force_attach = e;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Force has been attached \"");
		bprint(f.classname);
		bprint("\"\nOwner: \"");
		bprint(e.classname);
		bprint("\"\n");
	}
};

void(entity f, entity e) Gyro_Force_Ignore =
{
	if (!f)
		return;
	f.gyro_force_ignore = e;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Force is ignoring \"");
		bprint(f.classname);
		bprint("\"\nOwner: \"");
		bprint(e.classname);
		bprint("\"\n");
	}
};

void(entity f, float channels) Gyro_Force_SetChannels =
{
	if (!f)
		return;
	f.gyro_force_channels = channels;
};

void(entity f, float channels) Gyro_Force_AddChannels =
{
	if (!f)
		return;
	f.gyro_force_channels = (f.gyro_force_channels | channels);
};

void(entity f, float channels) Gyro_Force_RemoveChannels =
{
	if (!f)
		return;
	f.gyro_force_channels = (f.gyro_force_channels - (f.gyro_force_channels & channels));
};

void(entity f, float scale) Gyro_Force_SetRangeScale =
{
	if (!f)
		return;
	if ((scale <= 0))
	{
		if ((GYRO_FORCEDEBUG > 0))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Warning: Range scale not set for \"");
			bprint(f.classname);
			bprint("\"\nScale may not be a zero or negative value\n");
		}
		return;
	}
	f.gyro_force_rangescale = scale;
	f.gyro_force_update = TRUE;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Range scale set for \"");
		bprint(f.classname);
		bprint("\"\nScale: ");
		bprint(ftos(scale));
		bprint("\n");
	}
};

void(entity f, float scalerate) Gyro_Force_SetRangeScaleRate =
{
	if (!f)
		return;
	f.gyro_force_rangescalerate = scalerate;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Range scale rate set for \"");
		bprint(f.classname);
		bprint("\"\nScale rate: ");
		bprint(ftos(scalerate));
		bprint("\n");
	}
};

void(entity f, float scale) Gyro_Force_SetPowerScale =
{
	if (!f)
		return;
	if ((scale <= 0))
	{
		if ((GYRO_FORCEDEBUG > 0))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Warning: Power scale not set for \"");
			bprint(f.classname);
			bprint("\"\nScale may not be a zero or negative value\n");
		}
		return;
	}
	f.gyro_force_powerscale = scale;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Power scale set for \"");
		bprint(f.classname);
		bprint("\"\nScale: ");
		bprint(ftos(scale));
		bprint("\n");
	}
};

void(entity f, float scalerate) Gyro_Force_SetPowerScaleRate =
{
	if (!f)
		return;
	f.gyro_force_powerscalerate = scalerate;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Power scale rate set for \"");
		bprint(f.classname);
		bprint("\"\nScale rate: ");
		bprint(ftos(scalerate));
		bprint("\n");
	}
};

void(entity f) Gyro_Force_ClearProperties =
{
	if (!f)
		return;
	f.gyro_force_flags = 0;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: All properties removed from \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_AddProperty_Instant =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags | GYRO_FORCEFLAG_INSTANT);
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Instant property added to \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_RemoveProperty_Instant =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags - (f.gyro_force_flags & GYRO_FORCEFLAG_INSTANT));
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Instant property removed from \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_AddProperty_IgnoreWalls =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags | GYRO_FORCEFLAG_IGNOREWALLS);
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Ignore-walls property added to \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_RemoveProperty_IgnoreWalls =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags - (f.gyro_force_flags & GYRO_FORCEFLAG_IGNOREWALLS));
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Ignore-walls property removed from \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_AddProperty_AirOnly =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags | GYRO_FORCEFLAG_AIRONLY);
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Air-only property added to \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_RemoveProperty_AirOnly =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags - (f.gyro_force_flags & GYRO_FORCEFLAG_AIRONLY));
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Air-only property removed from \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_AddProperty_WaterOnly =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags | GYRO_FORCEFLAG_WATERONLY);
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Water-only property added to \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_RemoveProperty_WaterOnly =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags - (f.gyro_force_flags & GYRO_FORCEFLAG_WATERONLY));
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Water-only property removed from \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_AddProperty_GroundPound =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags | GYRO_FORCEFLAG_GROUNDPOUND);
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Ground-pound property added to \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_RemoveProperty_GroundPound =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags - (f.gyro_force_flags & GYRO_FORCEFLAG_GROUNDPOUND));
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Ground-pound property removed from \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_AddProperty_Persistent =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags | GYRO_FORCEFLAG_PERSISTENT);
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Persistent property added to \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

void(entity f) Gyro_Force_RemoveProperty_Persistent =
{
	if (!f)
		return;
	f.gyro_force_flags = (f.gyro_force_flags - (f.gyro_force_flags & GYRO_FORCEFLAG_PERSISTENT));
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Persistent property removed from \"");
		bprint(f.classname);
		bprint("\"\n");
	}
};

float(entity f, float falltype, vector fallaxis, float rad1, float rad2) Gyro_Force_ApplyFalloff =
{
	if (!f)
		return (0);
	if (!f.gyro_forcelist_inlist)
	{
		if ((GYRO_FORCEDEBUG > 0))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Warning: Falloff not applied to \"");
			bprint(f.classname);
			bprint("\"\nThe entity is not recognised as a force\n");
		}
		return (0);
	}
	if ((falltype & GYRO_FALLOFF_TYPE_AREA))
	{
		if ((fallaxis_x < 0))
		{
			fallaxis_x = 0 - fallaxis_x;
		}
		if ((fallaxis_y < 0))
		{
			fallaxis_y = 0 - fallaxis_y;
		}
		if ((fallaxis_z < 0))
		{
			fallaxis_z = 0 - fallaxis_z;
		}
	}
	if (!f.gyro_force_falloff1_type)
	{
		f.gyro_force_falloff1_type = falltype;
		f.gyro_force_falloff1_axis = fallaxis;
		f.gyro_force_falloff1_rad1 = rad1;
		f.gyro_force_falloff1_rad2 = rad2;
		f.gyro_force_update = TRUE;
		return (1);
	}
	else
	{
		if (!f.gyro_force_falloff2_type)
		{
			f.gyro_force_falloff2_type = falltype;
			f.gyro_force_falloff2_axis = fallaxis;
			f.gyro_force_falloff2_rad1 = rad1;
			f.gyro_force_falloff2_rad2 = rad2;
			f.gyro_force_update = TRUE;
			return (1);
		}
		else
		{
			if (!f.gyro_force_falloff3_type)
			{
				f.gyro_force_falloff3_type = falltype;
				f.gyro_force_falloff3_axis = fallaxis;
				f.gyro_force_falloff3_rad1 = rad1;
				f.gyro_force_falloff3_rad2 = rad2;
				f.gyro_force_update = TRUE;
				return (1);
			}
			else
			{
				if (!f.gyro_force_falloff4_type)
				{
					f.gyro_force_falloff4_type = falltype;
					f.gyro_force_falloff4_axis = fallaxis;
					f.gyro_force_falloff4_rad1 = rad1;
					f.gyro_force_falloff4_rad2 = rad2;
					f.gyro_force_update = TRUE;
					return (1);
				}
			}
		}
	}
	if ((GYRO_FORCEDEBUG > 0))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Warning: Falloff not applied to \"");
		bprint(f.classname);
		bprint("\"\nThe force cannot support more falloff controllers\n");
	}
	return (0);
};

void(entity f, vector falloff_area, float falloff_flags) Gyro_Force_ApplyFalloff_Area =
{
	if (Gyro_Force_ApplyFalloff(f, (GYRO_FALLOFF_TYPE_AREA | falloff_flags), falloff_area, 0, 0))
	{
		if ((GYRO_FORCEDEBUG > 1))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Debug: Area falloff applied to \"");
			bprint(f.classname);
			bprint("\"\nArea: ");
			bprint(vtos(falloff_area));
			bprint("\n");
		}
	}
};

void(entity f, vector falloff_dir, float rad1, float rad2, float falloff_flags) Gyro_Force_ApplyFalloff_Cone =
{
	if (Gyro_Force_ApplyFalloff(f, (GYRO_FALLOFF_TYPE_CONE | falloff_flags), falloff_dir, rad1, rad2))
	{
		if ((GYRO_FORCEDEBUG > 1))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Debug: Area falloff applied to \"");
			bprint(f.classname);
			bprint("\"\nVec: ");
			bprint(vtos(falloff_dir));
			bprint(", Start: ");
			bprint(ftos(rad1));
			bprint(", End: ");
			bprint(ftos(rad2));
			bprint("\n");
		}
	}
};

void(entity f, vector falloff_area) Gyro_Force_ApplyFalloff_AreaLinear =
{
	Gyro_Force_ApplyFalloff_Area(f, falloff_area, GYRO_FALLOFF_METHOD_LINEAR);
};

void(entity f, vector falloff_area) Gyro_Force_ApplyFalloff_AreaQuadratic =
{
	Gyro_Force_ApplyFalloff_Area(f, falloff_area, GYRO_FALLOFF_METHOD_QUADRATIC);
};

void(entity f, vector falloff_area) Gyro_Force_ApplyFalloff_AreaConstant =
{
	Gyro_Force_ApplyFalloff_Area(f, falloff_area, GYRO_FALLOFF_METHOD_CONSTANT);
};

void(entity f, vector falloff_dir, float rad1, float rad2) Gyro_Force_ApplyFalloff_ConeLinear =
{
	Gyro_Force_ApplyFalloff_Cone(f, falloff_dir, rad1, rad2, GYRO_FALLOFF_METHOD_LINEAR);
};

void(entity f, vector falloff_dir, float rad1, float rad2) Gyro_Force_ApplyFalloff_ConeQuadratic =
{
	Gyro_Force_ApplyFalloff_Cone(f, falloff_dir, rad1, rad2, GYRO_FALLOFF_METHOD_QUADRATIC);
};

void(entity f, vector falloff_dir, float rad1, float rad2) Gyro_Force_ApplyFalloff_ConeConstant =
{
	Gyro_Force_ApplyFalloff_Cone(f, falloff_dir, rad1, rad2, GYRO_FALLOFF_METHOD_CONSTANT);
};

void(entity f) Gyro_Force_FalloffCombine_Multiply =
{
	if (!f)
		return;
	f.gyro_force_falloff_combine = 0;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Falloff combination set for \"");
		bprint(f.classname);
		bprint("\"\nCombination method: Multiply\n");
	}
};

void(entity f) Gyro_Force_FalloffCombine_Minimum =
{
	if (!f)
		return;
	f.gyro_force_falloff_combine = GYRO_FALLOFF_COMBINE_MINIMUM;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Falloff combination set for \"");
		bprint(f.classname);
		bprint("\"\nCombination method: Minimum\n");
	}
};

void(entity f) Gyro_Force_FalloffCombine_Subtract =
{
	if (!f)
		return;
	f.gyro_force_falloff_combine = GYRO_FALLOFF_COMBINE_SUBTRACT;
	if ((GYRO_FORCEDEBUG > 1))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Debug: Falloff combination set for \"");
		bprint(f.classname);
		bprint("\"\nCombination method: Subtract\n");
	}
};

float(entity f, float afftype, float affpower, float absolute, vector offset, vector axis, vector amodx, vector amody) Gyro_Force_ApplyAffector =
{
	local vector amodz;

	if (!f)
		return (0);
	amodz = '0 0 0';
	if (!f.gyro_forcelist_inlist)
	{
		if ((GYRO_FORCEDEBUG > 0))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Warning: Affector not applied to \"");
			bprint(f.classname);
			bprint("\"\nThe entity is not recognised as a force\n");
		}
		return (0);
	}
	if (!f.gyro_force_affector1_type)
	{
		f.gyro_force_affector1_type = afftype;
		f.gyro_force_affector1_power = affpower;
		f.gyro_force_affector1_absolute = absolute;
		f.gyro_force_affector1_offset = offset;
		f.gyro_force_affector1_axis = axis;
		f.gyro_force_affector1_modx = amodx;
		f.gyro_force_affector1_mody = amody;
		f.gyro_force_affector1_modz = amodz;
		f.gyro_force_update = TRUE;
		return (1);
	}
	else
	{
		if (!f.gyro_force_affector2_type)
		{
			f.gyro_force_affector2_type = afftype;
			f.gyro_force_affector2_power = affpower;
			f.gyro_force_affector2_absolute = absolute;
			f.gyro_force_affector2_offset = offset;
			f.gyro_force_affector2_axis = axis;
			f.gyro_force_affector2_modx = amodx;
			f.gyro_force_affector2_mody = amody;
			f.gyro_force_affector2_modz = amodz;
			f.gyro_force_update = TRUE;
			return (1);
		}
		else
		{
			if (!f.gyro_force_affector3_type)
			{
				f.gyro_force_affector3_type = afftype;
				f.gyro_force_affector3_power = affpower;
				f.gyro_force_affector3_absolute = absolute;
				f.gyro_force_affector3_offset = offset;
				f.gyro_force_affector3_axis = axis;
				f.gyro_force_affector3_modx = amodx;
				f.gyro_force_affector3_mody = amody;
				f.gyro_force_affector3_modz = amodz;
				f.gyro_force_update = TRUE;
				return (1);
			}
			else
			{
				if (!f.gyro_force_affector4_type)
				{
					f.gyro_force_affector4_type = afftype;
					f.gyro_force_affector4_power = affpower;
					f.gyro_force_affector4_absolute = absolute;
					f.gyro_force_affector4_offset = offset;
					f.gyro_force_affector4_axis = axis;
					f.gyro_force_affector4_modx = amodx;
					f.gyro_force_affector4_mody = amody;
					f.gyro_force_affector4_modz = amodz;
					f.gyro_force_update = TRUE;
					return (1);
				}
			}
		}
	}
	if ((GYRO_FORCEDEBUG > 0))
	{
		gyro_framedebug = TRUE;
		bprint("Gyro Warning: Affector not applied to \"");
		bprint(f.classname);
		bprint("\"\nThe force cannot support more affectors\n");
	}
	return (0);
};

void(entity f, vector org_offset, vector aff_axis, float aff_power, float absolute, vector modx, vector mody, vector modz) Gyro_Force_ApplyAffector_PointMod =
{
	if (Gyro_Force_ApplyAffector(f, GYRO_AFFECTOR_POINTMOD, aff_power, absolute, org_offset, aff_axis, modx, mody))
	{
		if ((GYRO_FORCEDEBUG > 1))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Debug: Point-Mod affector applied to \"");
			bprint(f.classname);
			bprint("\"\nStrength: ");
			bprint(ftos(aff_power));
			bprint("\n");
		}
	}
};

void(entity f, vector org_offset, vector aff_axis, float aff_power, float absolute) Gyro_Force_ApplyAffector_Point =
{
	if (Gyro_Force_ApplyAffector(f, GYRO_AFFECTOR_POINT, aff_power, absolute, org_offset, aff_axis, VEC_ORIGIN, VEC_ORIGIN))
	{
		if ((GYRO_FORCEDEBUG > 1))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Debug: Point affector applied to \"");
			bprint(f.classname);
			bprint("\"\nStrength: ");
			bprint(ftos(aff_power));
			bprint("\n");
		}
	}
};

void(entity f, float aff_power, float absolute) Gyro_Force_ApplyAffector_Sphere =
{
	Gyro_Force_ApplyAffector_Point(f, VEC_ORIGIN, '1 1 1', aff_power, absolute);
};

void(entity f, vector aff_axis, float aff_power, float absolute) Gyro_Force_ApplyAffector_Directional =
{
	aff_axis = normalize(aff_axis);
	if (Gyro_Force_ApplyAffector(f, GYRO_AFFECTOR_DIRECTIONAL, aff_power, absolute, VEC_ORIGIN, aff_axis, VEC_ORIGIN, VEC_ORIGIN))
	{
		if ((GYRO_FORCEDEBUG > 1))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Debug: Directional affector applied to \"");
			bprint(f.classname);
			bprint("\"\nStrength: ");
			bprint(ftos(aff_power));
			bprint("\n");
		}
	}
};

void(entity f, float gravpower, float absolute) Gyro_Force_ApplyAffector_AntiGravity =
{
	if (Gyro_Force_ApplyAffector(f, GYRO_AFFECTOR_ANTIGRAVITY, gravpower, absolute, VEC_ORIGIN, '1 1 1', VEC_ORIGIN, VEC_ORIGIN))
	{
		if ((GYRO_FORCEDEBUG > 1))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Debug: Anti-gravity affector applied to \"");
			bprint(f.classname);
			bprint("\"\nStrength: ");
			bprint(ftos(gravpower));
			bprint("\n");
		}
	}
};

void(entity f, vector aff_axis, float respower, float absolute) Gyro_Force_ApplyAffector_Resistance =
{
	if (Gyro_Force_ApplyAffector(f, GYRO_AFFECTOR_RESISTANCE, respower, absolute, VEC_ORIGIN, aff_axis, VEC_ORIGIN, VEC_ORIGIN))
	{
		if ((GYRO_FORCEDEBUG > 1))
		{
			gyro_framedebug = TRUE;
			bprint("Gyro Debug: Resistance affector applied to \"");
			bprint(f.classname);
			bprint("\"\nStrength: ");
			bprint(ftos(respower));
			bprint("\n");
		}
	}
};

float(vector org_diff, float fall_type, vector fall_vector) Gyro_Force_Solver_Falloff =
{
	local float fallout;

	if ((fall_type & GYRO_FALLOFF_TYPE_AREA))
	{
		if ((fall_vector == VEC_ORIGIN))
		{
			return (1);
		}
		if ((fall_vector_x == 0))
		{
			org_diff_x = 0;
		}
		else
		{
			org_diff_x = org_diff_x / fall_vector_x;
		}
		if ((fall_vector_y == 0))
		{
			org_diff_y = 0;
		}
		else
		{
			org_diff_y = org_diff_y / fall_vector_y;
		}
		if ((fall_vector_z == 0))
		{
			org_diff_z = 0;
		}
		else
		{
			org_diff_z = org_diff_z / fall_vector_z;
		}
		fallout = 1 - vlen(org_diff);
		if ((fallout < 0))
		{
			return (0);
		}
		if ((fall_type & GYRO_FALLOFF_METHOD_CONSTANT))
		{
			return (1);
		}
		else
		{
			if ((fall_type & GYRO_FALLOFF_METHOD_QUADRATIC))
			{
				return ((fallout * fallout));
			}
		}
		return (fallout);
	}
};

float(vector org_diff, float fall_type, vector fall_vector) Gyro_Force_Solver_AreaFalloff =
{
	local float fallout;

	if ((fall_vector == VEC_ORIGIN))
	{
		return (1);
	}
	if ((fall_vector_x == 0))
	{
		org_diff_x = 0;
	}
	else
	{
		org_diff_x = org_diff_x / fall_vector_x;
	}
	if ((fall_vector_y == 0))
	{
		org_diff_y = 0;
	}
	else
	{
		org_diff_y = org_diff_y / fall_vector_y;
	}
	if ((fall_vector_z == 0))
	{
		org_diff_z = 0;
	}
	else
	{
		org_diff_z = org_diff_z / fall_vector_z;
	}
	fallout = 1 - vlen(org_diff);
	if ((fallout < 0))
	{
		return (0);
	}
	if ((fall_type & GYRO_FALLOFF_METHOD_CONSTANT))
	{
		return (1);
	}
	else
	{
		if ((fall_type & GYRO_FALLOFF_METHOD_QUADRATIC))
		{
			return ((fallout * fallout));
		}
	}
	return (fallout);
};

float(vector org_diff, float fall_type, vector fall_vector, float rad1, float rad2) Gyro_Force_Solver_ConeFalloff =
{
	local float dotprodlen;
	local float axisdistperc;
	local float perpdist;
	local float radlen;
	local float fallout;

	if ((fall_vector == VEC_ORIGIN))
	{
		return (0);
	}
	dotprodlen = org_diff * normalize(fall_vector);
	if ((dotprodlen < 0))
	{
		return (0);
	}
	axisdistperc = dotprodlen / vlen(fall_vector);
	if ((axisdistperc > 1))
	{
		return (0);
	}
	perpdist = vlen(((fall_vector * axisdistperc) - org_diff));
	radlen = (rad1 * (1 - axisdistperc)) + (rad2 * axisdistperc);
	if ((perpdist > radlen))
	{
		return (0);
	}
	fallout = 1 - (perpdist / radlen);
	if ((fall_type & GYRO_FALLOFF_METHOD_CONSTANT))
	{
		return (1);
	}
	else
	{
		if ((fall_type & GYRO_FALLOFF_METHOD_QUADRATIC))
		{
			return ((fallout * fallout));
		}
	}
	return (fallout);
};

void(entity f, entity e, float atype, float apower, float absolute, vector aoffset, vector aaxis, vector amodx) Gyro_Force_Solver_Affector =
{
	local vector amody;
	local vector amodz;
	local vector off_diff;
	local vector off_diff_temp;
	local float resistpower;

	amody = '0 0 0';
	amodz = '0 0 0';
	if (((atype == GYRO_AFFECTOR_POINT) || (atype == GYRO_AFFECTOR_POINTMOD)))
	{
		if ((apower == 0))
		{
			return;
		}
		if ((aaxis == VEC_ORIGIN))
		{
			return;
		}
		off_diff = normalize((e.origin - (f.origin + aoffset)));
		if ((aaxis != '1 1 1'))
		{
			off_diff_x = off_diff_x * aaxis_x;
		}
		if ((atype == GYRO_AFFECTOR_POINTMOD))
		{
			off_diff_temp_x = ((off_diff_x * amodx_x) + ((0 * aaxis_y) * amodx_y)) + ((0 * aaxis_z) * amodx_z);
			off_diff = off_diff_temp;
		}
		if (absolute)
		{
			apower = apower * e.gyro_object_mass;
		}
		if ((f.gyro_force_flags & GYRO_FORCEFLAG_INSTANT))
		{
			e.gyro_velocityeffect = (e.gyro_velocityeffect + (((off_diff * (apower / e.gyro_object_mass)) * f.gyro_force_powerscale) * GYRO_POWERCONSTANT));
		}
		else
		{
			e.gyro_velocityeffect = (e.gyro_velocityeffect + ((((off_diff * (apower / e.gyro_object_mass)) * f.gyro_force_powerscale) * GYRO_POWERCONSTANT) * GYRO_TICKRATE));
		}
	}
	else
	{
		if ((atype == GYRO_AFFECTOR_DIRECTIONAL))
		{
			if ((apower == 0))
			{
				return;
			}
			if ((aaxis == VEC_ORIGIN))
			{
				return;
			}
			if (absolute)
			{
				apower = apower * e.gyro_object_mass;
			}
			if ((f.gyro_force_flags & GYRO_FORCEFLAG_INSTANT))
			{
				e.gyro_velocityeffect = (e.gyro_velocityeffect + (((aaxis * (apower / e.gyro_object_mass)) * f.gyro_force_powerscale) * GYRO_POWERCONSTANT));
			}
			else
			{
				e.gyro_velocityeffect = (e.gyro_velocityeffect + ((((aaxis * (apower / e.gyro_object_mass)) * f.gyro_force_powerscale) * GYRO_POWERCONSTANT) * GYRO_TICKRATE));
			}
		}
		else
		{
			if ((atype == GYRO_AFFECTOR_ANTIGRAVITY))
			{
				if ((apower <= 0))
				{
					return;
				}
				if (absolute)
				{
					apower = apower * e.gyro_object_mass;
				}
				e.gyro_antigravityeffect = (e.gyro_antigravityeffect + ((apower / e.gyro_object_mass) * f.gyro_force_powerscale));
			}
			else
			{
				if ((atype == GYRO_AFFECTOR_RESISTANCE))
				{
					if ((apower <= 0))
					{
						return;
					}
					if (absolute)
					{
						apower = apower * e.gyro_object_mass;
					}
					resistpower = 1 / (((apower / e.gyro_object_mass) * 8) + 1);
					if (!(f.gyro_force_flags & GYRO_FORCEFLAG_INSTANT))
					{
						resistpower = Gyro_PowerEstimation(resistpower, GYRO_TICKRATE);
					}
					e.gyro_dampeningeffect_x = (e.gyro_dampeningeffect_x * (1 - ((1 - resistpower) * aaxis_x)));
					e.gyro_dampeningeffect_y = (e.gyro_dampeningeffect_y * (1 - ((1 - resistpower) * aaxis_y)));
					e.gyro_dampeningeffect_z = (e.gyro_dampeningeffect_z * (1 - ((1 - resistpower) * aaxis_z)));
					e.gyro_adampeningeffect = (e.gyro_adampeningeffect * resistpower);
				}
			}
		}
	}
};

void(entity f, entity e) Gyro_Force_Solver =
{
	local float pconts1;
	local float pconts2;
	local float totalfalloff;
	local float fall1;
	local float fall2;
	local float fall3;
	local float fall4;
	local vector org_diff;
	local vector oldveleffect;

	if ((e == f.gyro_force_ignore))
	{
		return;
	}
	if ((f.gyro_force_flags & GYRO_FORCEFLAG_AIRONLY))
	{
		pconts1 = pointcontents(e.origin);
		if ((((pconts1 == -3) || (pconts1 == -4)) || (pconts1 == -5)))
		{
			return;
		}
	}
	if ((f.gyro_force_flags & GYRO_FORCEFLAG_WATERONLY))
	{
		pconts2 = pointcontents(e.origin);
		if (!(((pconts2 == -3) || (pconts2 == -4)) || (pconts2 == -5)))
		{
			return;
		}
	}
	if ((f.gyro_force_flags & GYRO_FORCEFLAG_GROUNDPOUND))
	{
		if (!(e.flags & FL_ONGROUND))
		{
			return;
		}
	}
	if ((f.gyro_force_rangescale == 0))
	{
		return;
	}
	if ((f.gyro_force_powerscale == 0))
	{
		return;
	}
	if (!(f.gyro_force_flags & GYRO_FORCEFLAG_IGNOREWALLS))
	{
		traceline(f.origin, e.origin, TRUE, world);
		if ((trace_fraction < 1))
		{
			return;
		}
	}
	org_diff = e.origin - f.origin;
	fall1 = 1;
	fall2 = 1;
	fall3 = 1;
	fall4 = 1;
	if ((f.gyro_force_falloff1_type & GYRO_FALLOFF_TYPE_AREA))
	{
		fall1 = Gyro_Force_Solver_AreaFalloff(org_diff, f.gyro_force_falloff1_type, (f.gyro_force_falloff1_axis * f.gyro_force_rangescale));
	}
	else
	{
		if ((f.gyro_force_falloff1_type & GYRO_FALLOFF_TYPE_CONE))
		{
			fall1 = Gyro_Force_Solver_ConeFalloff(org_diff, f.gyro_force_falloff1_type, (f.gyro_force_falloff1_axis * f.gyro_force_rangescale), (f.gyro_force_falloff1_rad1 * f.gyro_force_rangescale), (f.gyro_force_falloff1_rad2 * f.gyro_force_rangescale));
		}
	}
	if ((f.gyro_force_falloff2_type & GYRO_FALLOFF_TYPE_AREA))
	{
		fall2 = Gyro_Force_Solver_AreaFalloff(org_diff, f.gyro_force_falloff2_type, (f.gyro_force_falloff2_axis * f.gyro_force_rangescale));
	}
	else
	{
		if ((f.gyro_force_falloff2_type & GYRO_FALLOFF_TYPE_CONE))
		{
			fall2 = Gyro_Force_Solver_ConeFalloff(org_diff, f.gyro_force_falloff1_type, (f.gyro_force_falloff2_axis * f.gyro_force_rangescale), (f.gyro_force_falloff2_rad1 * f.gyro_force_rangescale), (f.gyro_force_falloff2_rad2 * f.gyro_force_rangescale));
		}
	}
	if ((f.gyro_force_falloff3_type & GYRO_FALLOFF_TYPE_AREA))
	{
		fall3 = Gyro_Force_Solver_AreaFalloff(org_diff, f.gyro_force_falloff3_type, (f.gyro_force_falloff3_axis * f.gyro_force_rangescale));
	}
	else
	{
		if ((f.gyro_force_falloff3_type & GYRO_FALLOFF_TYPE_CONE))
		{
			fall3 = Gyro_Force_Solver_ConeFalloff(org_diff, f.gyro_force_falloff3_type, (f.gyro_force_falloff3_axis * f.gyro_force_rangescale), (f.gyro_force_falloff3_rad1 * f.gyro_force_rangescale), (f.gyro_force_falloff3_rad2 * f.gyro_force_rangescale));
		}
	}
	if ((f.gyro_force_falloff4_type & GYRO_FALLOFF_TYPE_AREA))
	{
		fall4 = Gyro_Force_Solver_AreaFalloff(org_diff, f.gyro_force_falloff4_type, (f.gyro_force_falloff4_axis * f.gyro_force_rangescale));
	}
	else
	{
		if ((f.gyro_force_falloff4_type & GYRO_FALLOFF_TYPE_CONE))
		{
			fall4 = Gyro_Force_Solver_ConeFalloff(org_diff, f.gyro_force_falloff4_type, (f.gyro_force_falloff4_axis * f.gyro_force_rangescale), (f.gyro_force_falloff4_rad1 * f.gyro_force_rangescale), (f.gyro_force_falloff4_rad2 * f.gyro_force_rangescale));
		}
	}
	if ((f.gyro_force_falloff_combine == GYRO_FALLOFF_COMBINE_MULTIPLY))
	{
		totalfalloff = ((fall1 * fall2) * fall3) * fall4;
	}
	else
	{
		if ((f.gyro_force_falloff_combine == GYRO_FALLOFF_COMBINE_MINIMUM))
		{
			if ((fall1 > fall2))
			{
				fall1 = fall2;
			}
			if ((fall3 > fall4))
			{
				fall3 = fall4;
			}
			if ((fall1 < fall3))
			{
				totalfalloff = fall1;
			}
			else
			{
				totalfalloff = fall3;
			}
		}
		else
		{
			if ((f.gyro_force_falloff_combine == GYRO_FALLOFF_COMBINE_SUBTRACT))
			{
				totalfalloff = (((fall1 + fall2) + fall3) + fall4) - 3;
			}
		}
	}
	if ((totalfalloff <= 0))
	{
		return;
	}
	oldveleffect = e.gyro_velocityeffect;
	if (f.gyro_force_affector1_type)
	{
		Gyro_Force_Solver_Affector(f, e, f.gyro_force_affector1_type, (f.gyro_force_affector1_power * totalfalloff), f.gyro_force_affector1_absolute, f.gyro_force_affector1_offset, f.gyro_force_affector1_axis, f.gyro_force_affector1_modx);
	}
	if (f.gyro_force_affector2_type)
	{
		Gyro_Force_Solver_Affector(f, e, f.gyro_force_affector2_type, (f.gyro_force_affector2_power * totalfalloff), f.gyro_force_affector2_absolute, f.gyro_force_affector2_offset, f.gyro_force_affector2_axis, f.gyro_force_affector2_modx);
	}
	if (f.gyro_force_affector3_type)
	{
		Gyro_Force_Solver_Affector(f, e, f.gyro_force_affector3_type, (f.gyro_force_affector3_power * totalfalloff), f.gyro_force_affector3_absolute, f.gyro_force_affector3_offset, f.gyro_force_affector3_axis, f.gyro_force_affector3_modx);
	}
	if (f.gyro_force_affector4_type)
	{
		Gyro_Force_Solver_Affector(f, e, f.gyro_force_affector4_type, (f.gyro_force_affector4_power * totalfalloff), f.gyro_force_affector4_absolute, f.gyro_force_affector4_offset, f.gyro_force_affector4_axis, f.gyro_force_affector4_modx);
	}
	if (e.gyro_feedback)
	{
		gyro_feedback_name = f.classname;
		gyro_feedback_channels = f.gyro_force_channels & e.gyro_object_channels;
		if ((f.gyro_force_flags & GYRO_FORCEFLAG_INSTANT))
		{
			gyro_feedback_power = (vlen((oldveleffect - e.gyro_velocityeffect)) / GYRO_POWERCONSTANT) * e.gyro_object_mass;
		}
		else
		{
			gyro_feedback_power = ((vlen((oldveleffect - e.gyro_velocityeffect)) / GYRO_TICKRATE) / GYRO_POWERCONSTANT) * e.gyro_object_mass;
		}
		Gyro_Object_CallFeedback(e);
	}
};

float(entity f, entity e) Gyro_Force_CheckBounds =
{
	if ((f.gyro_force_bounds_x > 0))
	{
		if ((e.origin_x > f.gyro_force_boundsmax_x))
		{
			return (0);
		}
		if ((e.origin_x < f.gyro_force_boundsmin_x))
		{
			return (0);
		}
	}
	if ((f.gyro_force_bounds_y > 0))
	{
		if ((e.origin_y > f.gyro_force_boundsmax_y))
		{
			return (0);
		}
		if ((e.origin_y < f.gyro_force_boundsmin_y))
		{
			return (0);
		}
	}
	if ((f.gyro_force_bounds_z > 0))
	{
		if ((e.origin_z > f.gyro_force_boundsmax_z))
		{
			return (0);
		}
		if ((e.origin_z < f.gyro_force_boundsmin_z))
		{
			return (0);
		}
	}
	return (1);
};

void() Gyro_RunForces =
{
	local entity forcehead;
	local entity gyrohead;
	local entity oldforce;
	local float forceheadcount;

	forcehead = gyro_forcelist_head;
	while (forcehead)
	{
			if (forcehead.gyro_force_update)
			{
				Gyro_Force_Update(forcehead);
				forcehead.gyro_force_update = 0;
			}
			if (forcehead.gyro_force_attach)
			{
				if (((forcehead.gyro_force_attach.origin == VEC_ORIGIN) && (forcehead.gyro_force_attach.modelindex == 0)))
				{
					if ((forcehead.gyro_force_flags & GYRO_FORCEFLAG_PERSISTENT))
					{
						Gyro_Force_Detach(forcehead);
					}
					else
					{
						oldforce = forcehead;
						forceheadcount = forceheadcount + 1;
						forcehead = forcehead.gyro_forcelist_next;
						Gyro_Force_Remove(oldforce);
					continue;
					}
				}
			}
			else
			{
				forcehead.origin = forcehead.gyro_force_attach.origin;
			}
		if (forcehead.gyro_force_ignore)
		{
			if (((forcehead.gyro_force_ignore.origin == VEC_ORIGIN) && (forcehead.gyro_force_ignore.modelindex == 0)))
			{
				forcehead.gyro_force_ignore = world;
			}
		}
		forcehead.gyro_force_boundsmax = (forcehead.origin + forcehead.gyro_force_bounds);
		forcehead.gyro_force_boundsmin = (forcehead.origin - forcehead.gyro_force_bounds);
		gyrohead = gyro_objectlist_head;
		while (gyrohead)
		{
			if ((forcehead.gyro_force_channels & gyrohead.gyro_object_channels))
			{
				if (Gyro_Force_CheckBounds(forcehead, gyrohead))
				{
					Gyro_Force_Solver(forcehead, gyrohead);
				}
			}
			gyrohead = gyrohead.gyro_objectlist_next;
		}
		if ((forcehead.gyro_force_powerscalerate != 0))
		{
			forcehead.gyro_force_powerscale = (forcehead.gyro_force_powerscale + (forcehead.gyro_force_powerscalerate * GYRO_TICKRATE));
		}
		if ((forcehead.gyro_force_rangescalerate != 0))
		{
			forcehead.gyro_force_rangescale = (forcehead.gyro_force_rangescale + (forcehead.gyro_force_rangescalerate * GYRO_TICKRATE));
			forcehead.gyro_force_update = TRUE;
		}
		oldforce = forcehead;
		forceheadcount = forceheadcount + 1;
		forcehead = forcehead.gyro_forcelist_next;
		if ((oldforce.gyro_force_flags & GYRO_FORCEFLAG_INSTANT))
		{
			Gyro_Force_Remove(oldforce);
		}
		else
		{
			if (!(oldforce.gyro_force_flags & GYRO_FORCEFLAG_PERSISTENT))
			{
				if ((oldforce.gyro_force_rangescale <= 0))
				{
					Gyro_Force_Remove(oldforce);
				}
				else
				{
					if ((oldforce.gyro_force_powerscale <= 0))
					{
						Gyro_Force_Remove(oldforce);
					}
				}
			}
			else
			{
				if ((oldforce.gyro_force_rangescale < 0))
				{
					oldforce.gyro_force_rangescale = 0;
				}
				else
				{
					if ((oldforce.gyro_force_powerscale < 0))
					{
						oldforce.gyro_force_powerscale = 0;
					}
				}
			}
		}
	}
};
