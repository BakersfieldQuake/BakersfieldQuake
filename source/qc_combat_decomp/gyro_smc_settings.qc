//Decompiled code. Please respect the original copyright.

void(entity gibentity) GibPhysics =
{
	local float gibbouyancy;

	if ((autocvar_gyroset == 0))
	{
		return;
	}
	Gyro_Object_Activate(gibentity, autocvar_gibmass);
	gibbouyancy = autocvar_gibmass + 150;
	Gyro_Object_SetBouyancy(gibentity, gibbouyancy);
	Gyro_Object_SetResistance(gibentity, autocvar_gibmass);
	Gyro_Object_SetTurbulence(gibentity, 260, 0.98);
	Gyro_Object_SetGlobalTurb(gibentity, 160, 0.98);
};

void(entity hydraentity) HydraPhysics =
{
	local float hydrabouyancy;

	if ((autocvar_gyroset == 0))
	{
		return;
	}
	Gyro_Object_Activate(hydraentity, 3000);
	hydrabouyancy = 3300;
	Gyro_Object_SetBouyancy(hydraentity, hydrabouyancy);
	Gyro_Object_SetResistance(hydraentity, 10000);
	Gyro_Object_SetTurbulence(hydraentity, 260, 0.98);
	Gyro_Object_SetGlobalTurb(hydraentity, 160, 0.98);
};

void(entity monsterentity, float mass) MonsterPhysics =
{
	if ((autocvar_gyroset < 2))
	{
		return;
	}
	Gyro_Object_Activate(monsterentity, mass);
};

void(entity bagentity) BackpackPhysics =
{
	local float bagbouyancy;

	if ((autocvar_gyroset == 0))
	{
		return;
	}
	Gyro_Object_Activate(bagentity, autocvar_backpackmass);
	bagbouyancy = autocvar_backpackmass + 300;
	Gyro_Object_SetBouyancy(bagentity, bagbouyancy);
	Gyro_Object_SetResistance(bagentity, autocvar_backpackmass);
	Gyro_Object_SetTurbulence(bagentity, 260, 0.98);
	Gyro_Object_SetGlobalTurb(bagentity, 160, 0.98);
};
