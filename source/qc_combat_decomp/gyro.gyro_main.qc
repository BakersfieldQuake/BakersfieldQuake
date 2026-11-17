//Decompiled code. Please respect the original copyright.

void(entity e) Gyro_ObjectList_Add =
{
	if (e.gyro_objectlist_inlist)
	{
		return;
	}
	e.gyro_objectlist_inlist = TRUE;
	e.gyro_objectlist_next = gyro_objectlist_head;
	if (gyro_objectlist_head)
	{
		gyro_objectlist_head.gyro_objectlist_prev = e;
	}
	gyro_objectlist_head = e;
	gyro_objectlist_size = gyro_objectlist_size + 1;
};

void(entity e) Gyro_ObjectList_Remove =
{
	if (!e.gyro_objectlist_inlist)
	{
		return;
	}
	if (e.gyro_objectlist_prev)
	{
		e.gyro_objectlist_prev.gyro_objectlist_next = e.gyro_objectlist_next;
	}
	else
	{
		gyro_objectlist_head = e.gyro_objectlist_next;
	}
	if (e.gyro_objectlist_next)
	{
		e.gyro_objectlist_next.gyro_objectlist_prev = e.gyro_objectlist_prev;
	}
	e.gyro_objectlist_inlist = 0;
	e.gyro_objectlist_next = world;
	e.gyro_objectlist_prev = world;
	gyro_objectlist_size = gyro_objectlist_size - 1;
};

void(entity e) Gyro_ForceList_Add =
{
	if (e.gyro_forcelist_inlist)
	{
		return;
	}
	e.gyro_forcelist_inlist = TRUE;
	e.gyro_forcelist_next = gyro_forcelist_head;
	if (gyro_forcelist_head)
	{
		gyro_forcelist_head.gyro_forcelist_prev = e;
	}
	gyro_forcelist_head = e;
	gyro_forcelist_size = gyro_forcelist_size + 1;
};

void(entity e) Gyro_ForceList_Remove =
{
	if (!e.gyro_forcelist_inlist)
	{
		return;
	}
	if (e.gyro_forcelist_prev)
	{
		e.gyro_forcelist_prev.gyro_forcelist_next = e.gyro_forcelist_next;
	}
	else
	{
		gyro_forcelist_head = e.gyro_forcelist_next;
	}
	if (e.gyro_forcelist_next)
	{
		e.gyro_forcelist_next.gyro_forcelist_prev = e.gyro_forcelist_prev;
	}
	e.gyro_forcelist_inlist = 0;
	e.gyro_forcelist_next = world;
	e.gyro_forcelist_prev = world;
	gyro_forcelist_size = gyro_forcelist_size - 1;
};
float(string extname) Gyro_CheckExtension = #99; 
float(float value, float exp) Gyro_PowerAccurate = #97; 

float(float x, float y) Gyro_PowerEstimation =
{
	local float z;

	if (gyro_accuratepower)
	{
		return (Gyro_PowerAccurate(x, y));
	}
	z = 1 - x;
	z = (z * z) + z;
	z = 1 / ((y * z) + 1);
	return (z);
};
void (entity e) Gyro_RemoveEntity = #15; 

void(entity e) remove =
{
	Gyro_ObjectList_Remove(e);
	Gyro_ForceList_Remove(e);
	Gyro_RemoveEntity(e);
};

void() Gyro_Null =
{
	return;
};

void() Gyro_InitialiseVariables =
{
	Gyro_UserSettings();
	gyro_runtimer = 0;
	gyro_runcount = 0;
	gyro_displayintro = TRUE;
	gyro_accuratepower = 0;
	if (cvar("pr_checkextension"))
	{
		if (Gyro_CheckExtension("DP_QC_SINCOSSQRTPOW"))
		{
			gyro_accuratepower = TRUE;
		}
	}
};

void() Gyro_Run =
{
	if ((gyro_runcount == 0))
	{
		Gyro_InitialiseVariables();
	}
	else if ((!gyro_objectlist_head && !gyro_forcelist_head))
	{
		gyro_runtimer = time;
		return;
	}
	if (GYRO_AUTOTICKRATE)
	{
		GYRO_TICKRATE = frametime;
		gyro_runtimer = time - (GYRO_TICKRATE * 0.5);
	}
	while ((gyro_runtimer < time))
	{
		gyro_runtimer = gyro_runtimer + GYRO_TICKRATE;
		gyro_runcount = gyro_runcount + 1;
		gyro_framegrav = bm_cvar_grav;
		if (GYRO_MOTIONCORRECTION)
		{
			gyro_framemaxvel = bm_cvar_maxvel;
			gyro_framemaxvelneg = 0 - gyro_framemaxvel;
		}
		Gyro_RunForces();
		Gyro_RunPhysics();
		if (gyro_displayintro)
		{
			if (((GYRO_FORCEDEBUG > 0) || (GYRO_OBJECTDEBUG > 0)))
			{
				if (((time > 1.6) && (time < 2.4)))
				{
					bprint("Gyro 2.1a (April '07) is running\nTickrate (ms): ");
					if (GYRO_AUTOTICKRATE)
					{
						bprint("Auto");
					}
					else
					{
						bprint(ftos((GYRO_TICKRATE * 1000)));
					}
					bprint(", Force debug: ");
					bprint(ftos(GYRO_FORCEDEBUG));
					bprint(", Object debug: ");
					bprint(ftos(GYRO_OBJECTDEBUG));
					bprint("\n");
					if (gyro_accuratepower)
					{
						bprint("Engine power function is enabled\n");
					}
					gyro_displayintro = 0;
				}
			}
		}
		if (gyro_framedebug)
		{
			bprint("===== Output on Gyro frame: ");
			bprint(ftos(gyro_runcount));
			bprint(" =====\n");
			gyro_framedebug = 0;
		}
	}
};
