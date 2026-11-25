#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
SHOOTABLE / EXPLODABLE 3D VEHICLES - implementation (Combat+)

Models & sounds built by:
  - source/mm_tools/blender_build_vehicles.py
  - source/mm_tools/veh_textures.py
  - source/mm_tools/veh_physics_sim.py
  - source/mm_tools/build_vehicles_assets.py
  - source/mm_tools/make_vehicle_sounds.py
================
*/

void() Veh_Think;
void() Veh_Explode;
void() Veh_ExplodeNow;
void(entity attacker, float take) Veh_Pain;
void(entity v, float kind) Veh_InitEntity;

// ---------------------------------------------------------------- Precache

void() Veh_PrecacheEffects =
{
	veh_fx_fire = particleeffectnum ("veh_fire");
	veh_fx_smoke = particleeffectnum ("veh_smoke");
	veh_fx_explode = particleeffectnum ("veh_explode");
	veh_fx_explode_sec = particleeffectnum ("veh_explode_sec");
	veh_fx_wreck = particleeffectnum ("veh_wreck_fire");
	veh_fx_sparks = particleeffectnum ("veh_sparks");
	veh_fx_boost = particleeffectnum ("veh_boost");
	veh_fx_drift = particleeffectnum ("veh_drift");
	gk_fx_smoke = particleeffectnum ("gk_tire_smoke");
};

void() Vehicles_Precache =
{
	if (vehicles_precached)
		return;
	vehicles_precached = TRUE;
	// The bodies, wrecks and loose parts are precached per kind in Veh_InitEntity: a map loads only the kinds it spawns
	// (soi6 has three tuk-tuks and used to load all eight kinds, about 60 models).

	// go-kart models (~42 MB) are precached by GK_Precache, only on maps that really spawn a kart

	precache_model ("progs/veh_shrap1.md3");
	precache_model ("progs/veh_shrap2.md3");
	precache_model ("progs/veh_shrap3.md3");
	precache_model ("progs/veh_shrap4.md3");
	precache_model ("progs/s_explodbig.spr");
	precache_sound ("weapons/explodedist.wav");

	precache_sound ("vehicles/idle_truck.wav");
	precache_sound ("vehicles/idle_sedan.wav");
	precache_sound ("vehicles/idle_van.wav");
	precache_sound ("vehicles/idle_coupe.wav");
	precache_sound ("vehicles/hit_metal1.wav");
	precache_sound ("vehicles/hit_metal2.wav");
	precache_sound ("vehicles/fire_burn.wav");
	precache_sound ("vehicles/car_boom1.wav");
	precache_sound ("vehicles/car_boom2.wav");
	precache_sound ("vehicles/clang1.wav");
	precache_sound ("vehicles/clang2.wav");
	precache_sound ("vehicles/tire_thud1.wav");
	precache_sound ("vehicles/tire_thud2.wav");

	// driving the van (vehicle_drive.qc)
	precache_model ("progs/spike.mdl");
	precache_sound ("vehicles/engine_grain.wav");
	precache_sound ("vehicles/engine_grain_tuktuk.wav");
	precache_sound ("vehicles/idle_tuktuk.wav");
	precache_sound ("vehicles/tire_squeal.wav");
	precache_sound ("vehicles/horn.wav");
	precache_sound ("vehicles/horn_tuktuk.wav");
	precache_sound ("vehicles/ignition.wav");
	precache_sound ("vehicles/lanvan.wav");
	precache_sound ("misc/null.wav");
	precache_sound ("bikes/tire_bounce.wav");
	precache_sound ("ambience/windfly.wav");
	precache_sound ("skypad/launch.wav");

	Veh_PrecacheEffects ();
};

// Kart-only assets: called from Veh_InitEntity for kart kinds (misc_gokart*, misc_vehicle kart kinds, Veh_SpawnDynamic);
// each kart body (gokart_N.md3) is precached there per kind, so a map only loads the karts it places
float	gk_precached;
void() GK_Precache =
{
	if (gk_precached)
		return;
	gk_precached = TRUE;
	precache_model ("progs/gokart_driver.md3");
	precache_sound ("bikes/spoke_ping.wav");
	precache_sound ("john_bird/swoop.wav");
};

// ---------------------------------------------------------------- Geometry & Asset Lookup Helpers

float(float a) Veh_NormYaw =
{
	while (a >= 360)
		a = a - 360;
	while (a < 0)
		a = a + 360;
	return a;
};

float(float kind) Veh_IsKart =
{
	return ((kind >= VEH_GOKART_1 && kind <= VEH_GOKART_6) || kind == VEH_FORELOCO);
};

float(float kind) Veh_IsForeLoco =
{
	return (kind == VEH_FORELOCO);
};

string(float kind) Veh_DisplayName =
{
	if (kind == VEH_TRUCK)
		return "4x4 Pickup";
	if (kind == VEH_SEDAN)
		return "Street Sedan";
	if (kind == VEH_VAN)
		return "6-Man LAN Van";
	if (kind == VEH_HDTRUCK)
		return "Diesel Dually Rig";
	if (kind == VEH_SCHOOLBUS)
		return "Party School Bus";
	if (kind == VEH_GTCAR)
		return "V8 Muscle GT";
	if (kind == VEH_GOLFCART)
		return "Island Golf Cart";
	if (kind == VEH_TUKTUK)
		return "Bangkok Tuk-Tuk";
	if (kind == VEH_GOKART_1)
		return "Bakersfield Tubular Classic";
	if (kind == VEH_GOKART_2)
		return "Cyber-Nitro Aero GT";
	if (kind == VEH_GOKART_3)
		return "Baja Dune Scrambler";
	if (kind == VEH_GOKART_4)
		return "Mega Man Classic Bar-Racer";
	if (kind == VEH_GOKART_5)
		return "Mega Man Twin-Dish Interceptor";
	if (kind == VEH_GOKART_6)
		return "Mega Man Heavy Fat-Tire Rammer";
	if (kind == VEH_FORELOCO)
		return "Eric's Runaway Hospital Bed";
	return "Tuner Coupe";
};

float(float kind) Veh_HalfLen =
{
	if (kind == VEH_SCHOOLBUS) return 165;
	if (kind == VEH_HDTRUCK)   return 124;
	if (kind == VEH_TRUCK)     return 116;
	if (kind == VEH_VAN)       return 110;
	if (kind == VEH_GTCAR)     return 99;
	if (kind == VEH_SEDAN)     return 98;
	if (kind == VEH_TUKTUK)    return 58;
	if (kind == VEH_GOLFCART)  return 50;
	if (Veh_IsKart (kind))     return 50;
	return 93;
};

float(float kind) Veh_HalfWid =
{
	if (kind == VEH_SCHOOLBUS) return 47;
	if (kind == VEH_TRUCK)     return 46;
	if (kind == VEH_HDTRUCK)   return 45;
	if (kind == VEH_VAN)       return 44;
	if (kind == VEH_TUKTUK)    return 28;
	if (kind == VEH_GOLFCART)  return 26;
	if (Veh_IsKart (kind))     return 34;
	return 39;
};

float(float kind) Veh_BodyHeight =
{
	if (kind == VEH_SCHOOLBUS) return 104;
	if (kind == VEH_VAN)       return 89;
	if (kind == VEH_TRUCK)     return 84;
	if (kind == VEH_HDTRUCK)   return 84;
	if (kind == VEH_GOLFCART)  return 72;
	if (kind == VEH_TUKTUK)    return 70;
	if (kind == VEH_SEDAN)     return 55;
	if (kind == VEH_GTCAR)     return 53;
	if (Veh_IsKart (kind))     return 36;
	return 50;
};

string(float kind) Veh_IntactModel =
{
	if (kind == VEH_TRUCK)
		return "progs/veh_truck.md3";
	if (kind == VEH_SEDAN)
		return "progs/veh_sedan.md3";
	if (kind == VEH_VAN)
		return "progs/veh_van.md3";
	if (kind == VEH_HDTRUCK)
		return "progs/veh_hdtruck.md3";
	if (kind == VEH_SCHOOLBUS)
		return "progs/veh_schoolbus.md3";
	if (kind == VEH_GTCAR)
		return "progs/veh_gtcar.md3";
	if (kind == VEH_GOLFCART)
		return "progs/lsj/lsj_golfcart.md3";
	if (kind == VEH_TUKTUK)
		return "progs/veh_tuktuk.md3";
	if (kind == VEH_GOKART_1)
		return "progs/gokart_1.md3";
	if (kind == VEH_GOKART_2)
		return "progs/gokart_2.md3";
	if (kind == VEH_GOKART_3)
		return "progs/gokart_3.md3";
	if (kind == VEH_GOKART_4)
		return "progs/gokart_4.md3";
	if (kind == VEH_GOKART_5)
		return "progs/gokart_5.md3";
	if (kind == VEH_GOKART_6)
		return "progs/gokart_6.md3";
	if (kind == VEH_FORELOCO)
		return "progs/crowd_c1.spr32";
	return "progs/veh_coupe.md3";
};

string(float kind) Veh_WreckModel =
{
	if (kind == VEH_TRUCK)
		return "progs/veh_truck_wreck.md3";
	if (kind == VEH_SEDAN)
		return "progs/veh_sedan_wreck.md3";
	if (kind == VEH_VAN)
		return "progs/veh_van_wreck.md3";
	if (kind == VEH_HDTRUCK)
		return "progs/veh_hdtruck_wreck.md3";
	if (kind == VEH_SCHOOLBUS)
		return "progs/veh_schoolbus_wreck.md3";
	if (kind == VEH_GTCAR)
		return "progs/veh_gtcar_wreck.md3";
	if (kind == VEH_TUKTUK)
		return "progs/veh_tuktuk_wreck.md3";
	return "progs/veh_coupe_wreck.md3";
};

string(float kind) Veh_WheelModel =
{
	if (kind == VEH_TRUCK)
		return "progs/veh_truck_wheel.md3";
	if (kind == VEH_SEDAN)
		return "progs/veh_sedan_wheel.md3";
	if (kind == VEH_VAN)
		return "progs/veh_van_wheel.md3";
	if (kind == VEH_HDTRUCK)
		return "progs/veh_hdtruck_wheel.md3";
	if (kind == VEH_SCHOOLBUS)
		return "progs/veh_schoolbus_wheel.md3";
	if (kind == VEH_GTCAR)
		return "progs/veh_gtcar_wheel.md3";
	if (kind == VEH_TUKTUK)
		return "progs/veh_tuktuk_wheel.md3";
	return "progs/veh_coupe_wheel.md3";
};

string(float kind) Veh_HoodModel =
{
	if (kind == VEH_TRUCK)
		return "progs/veh_truck_hood.md3";
	if (kind == VEH_SEDAN)
		return "progs/veh_sedan_hood.md3";
	if (kind == VEH_VAN)
		return "progs/veh_van_hood.md3";
	if (kind == VEH_HDTRUCK)
		return "progs/veh_hdtruck_hood.md3";
	if (kind == VEH_SCHOOLBUS)
		return "progs/veh_schoolbus_hood.md3";
	if (kind == VEH_GTCAR)
		return "progs/veh_gtcar_hood.md3";
	if (kind == VEH_TUKTUK)
		return "progs/veh_tuktuk_hood.md3";
	return "progs/veh_coupe_hood.md3";
};

string(float kind) Veh_DoorModel =
{
	if (kind == VEH_TRUCK)
		return "progs/veh_truck_door.md3";
	if (kind == VEH_SEDAN)
		return "progs/veh_sedan_door.md3";
	if (kind == VEH_VAN)
		return "progs/veh_van_door.md3";
	if (kind == VEH_HDTRUCK)
		return "progs/veh_hdtruck_door.md3";
	if (kind == VEH_SCHOOLBUS)
		return "progs/veh_schoolbus_door.md3";
	if (kind == VEH_GTCAR)
		return "progs/veh_gtcar_door.md3";
	if (kind == VEH_TUKTUK)
		return "progs/veh_tuktuk_door.md3";
	return "progs/veh_coupe_door.md3";
};

string(float kind) Veh_ExtraModel =
{
	if (kind == VEH_TRUCK)
		return "progs/veh_truck_extra.md3";
	if (kind == VEH_SEDAN)
		return "progs/veh_sedan_extra.md3";
	if (kind == VEH_VAN)
		return "progs/veh_van_extra.md3";
	if (kind == VEH_HDTRUCK)
		return "progs/veh_hdtruck_extra.md3";
	if (kind == VEH_SCHOOLBUS)
		return "progs/veh_schoolbus_extra.md3";
	if (kind == VEH_GTCAR)
		return "progs/veh_gtcar_extra.md3";
	if (kind == VEH_TUKTUK)
		return "progs/veh_tuktuk_extra.md3";
	return "progs/veh_coupe_extra.md3";
};

string(float kind) Veh_BumperModel =
{
	if (kind == VEH_TRUCK)
		return "progs/veh_truck_bumper.md3";
	if (kind == VEH_SEDAN)
		return "progs/veh_sedan_bumper.md3";
	if (kind == VEH_VAN)
		return "progs/veh_van_bumper.md3";
	if (kind == VEH_HDTRUCK)
		return "progs/veh_hdtruck_bumper.md3";
	if (kind == VEH_SCHOOLBUS)
		return "progs/veh_schoolbus_bumper.md3";
	if (kind == VEH_GTCAR)
		return "progs/veh_gtcar_bumper.md3";
	if (kind == VEH_TUKTUK)
		return "progs/veh_tuktuk_bumper.md3";
	return "progs/veh_coupe_bumper.md3";
};

string(float kind) Veh_IdleSound =
{
	if (kind == VEH_TRUCK || kind == VEH_HDTRUCK)
		return "vehicles/idle_truck.wav";
	if (kind == VEH_SEDAN)
		return "vehicles/idle_sedan.wav";
	if (kind == VEH_VAN || kind == VEH_SCHOOLBUS)
		return "vehicles/idle_van.wav";
	if (kind == VEH_TUKTUK || Veh_IsKart (kind))
		return "vehicles/idle_tuktuk.wav";
	return "vehicles/idle_coupe.wav";
};

float(float kind) Veh_MaxHP =
{
	if (kind == VEH_SCHOOLBUS)
		return 400;
	if (kind == VEH_HDTRUCK)
		return 380;
	if (kind == VEH_TRUCK)
		return 300;
	if (kind == VEH_VAN)
		return 320;
	if (kind == VEH_GTCAR)
		return 250;
	if (kind == VEH_SEDAN)
		return 230;
	if (kind == VEH_GOLFCART)
		return 200;
	if (kind == VEH_TUKTUK)
		return 190;
	if (Veh_IsForeLoco (kind))
		return 600;
	if (Veh_IsKart (kind))
		return 220;
	return 210;
};

// Local engine-bay / hood-seam offset (x forward, z up) where flames & smoke pour out
vector(float kind) Veh_HoodFireOfs =
{
	if (kind == VEH_TRUCK)
		return '82 0 45';
	if (kind == VEH_SEDAN)
		return '68 0 34';
	if (kind == VEH_VAN)
		return '91 0 45';
	if (kind == VEH_HDTRUCK)
		return '82 0 47';
	if (kind == VEH_SCHOOLBUS)
		return '126 0 48';
	if (kind == VEH_GTCAR)
		return '64 0 32';
	if (kind == VEH_GOLFCART)
		return '34 0 28';
	if (kind == VEH_TUKTUK)
		return '36 0 35';
	if (Veh_IsKart (kind))
		return '-24 0 18';
	return '62 0 29';
};

// Compute rotated world-aligned AABB for SOLID_BBOX at arbitrary map yaw
void(entity v, float kind, float is_wreck) Veh_SetRotatedBounds =
{
	local float hl, hw, ht, rad, sn, cs, acs, asn, hx, hy;
	local vector bmin, bmax;

	if (kind == VEH_TRUCK)
	{
		hl = 116;
		hw = 46;
		ht = 84;
		if (is_wreck)
			ht = 54;
	}
	else if (kind == VEH_SEDAN)
	{
		hl = 98;
		hw = 39;
		ht = 55;
		if (is_wreck)
			ht = 37;
	}
	else if (kind == VEH_VAN)
	{
		hl = 110;
		hw = 44;
		ht = 89;
		if (is_wreck)
			ht = 56;
	}
	else if (kind == VEH_HDTRUCK)
	{
		hl = 124;
		hw = 45;
		ht = 84;
		if (is_wreck)
			ht = 52;
	}
	else if (kind == VEH_SCHOOLBUS)
	{
		hl = 165;
		hw = 47;
		ht = 104;
		if (is_wreck)
			ht = 68;
	}
	else if (kind == VEH_GTCAR)
	{
		hl = 99;
		hw = 39;
		ht = 53;
		if (is_wreck)
			ht = 35;
	}
	else if (kind == VEH_GOLFCART)
	{
		hl = 50;
		hw = 26;
		ht = 72;
		if (is_wreck)
			ht = 28;
	}
	else if (kind == VEH_TUKTUK)
	{
		hl = 58;
		hw = 28;
		ht = 70;
		if (is_wreck)
			ht = 44;
	}
	else if (Veh_IsKart (kind))
	{
		hl = 50;
		hw = 34;
		ht = 36;
		if (is_wreck)
			ht = 22;
	}
	else
	{
		hl = 93;
		hw = 39;
		ht = 50;
		if (is_wreck)
			ht = 34;
	}

	rad = v.angles_y * 0.0174533;
	sn = sin (rad);
	cs = cos (rad);
	acs = fabs (cs);
	asn = fabs (sn);
	hx = acs * hl + asn * hw;
	hy = asn * hl + acs * hw;

	bmin_x = 0 - hx;
	bmin_y = 0 - hy;
	bmin_z = 0;
	bmax_x = hx;
	bmax_y = hy;
	bmax_z = ht;
	setsize (v, bmin, bmax);
};

// ---------------------------------------------------------------- Walk-In Van Interior & Collision Architecture

void(entity attacker, float take) Veh_ClipPain =
{
	local entity v, oldself;
	self.health = 1000000;
	v = self.owner;
	if (v != world)
	{
		if (v.veh_state == VEH_STATE_WRECK)
			return;
		oldself = self;
		v.health = v.health - take;
		if (v.health <= 0)
		{
			damage_attacker = attacker;
			self = v;
			self.th_die ();
		}
		else
		{
			self = v;
			self.th_pain (attacker, take);
		}
		self = oldself;
	}
};

// standing in the cab shows the prompt; impulse 86 (H) then gets him in (Veh_EnterKey in vehicle_drive.qc finds the seat
// by position)
void() Veh_CockpitTouch =
{
	if (other.classname != "player" || other.ishuman != 1 || other.health <= 0)
		return;
	if (self.owner.veh_state == VEH_STATE_WRECK || self.owner.veh_driver != world || other.veh_van != world || other.veh_ride != world)
		return;

	if (!other.veh_hint_shown && time > other.veh_prompt_t)
	{
		other.veh_prompt_van = self.owner;
		other.veh_prompt_t = time + 4.0;
		centerprint (other, "Press H to drive 6-Man LAN Van");
	}
};

void(entity v, float x0, float x1, float y0, float y1, float z0, float z1, float is_trigger) Veh_Van_AddBox =
{
	local entity c;
	local vector mins, maxs, fwd, lft, upv;
	local float cx, cy, cz, hl, hw, hz, rad, sn, cs, acs, asn, hx, hy;

	makevectors ('0 1 0' * v.angles_y);
	fwd = v_forward;
	lft = '0 0 0' - v_right;
	upv = '0 0 1';

	cx = (x0 + x1) * 0.5;
	cy = (y0 + y1) * 0.5;
	cz = (z0 + z1) * 0.5;

	hl = (x1 - x0) * 0.5;
	hw = (y1 - y0) * 0.5;
	hz = (z1 - z0) * 0.5;

	rad = v.angles_y * 0.0174533;
	sn = sin (rad);
	cs = cos (rad);
	acs = fabs (cs);
	asn = fabs (sn);
	hx = acs * hl + asn * hw;
	hy = asn * hl + acs * hw;

	c = spawn ();
	c.classname = "veh_van_clip";
	c.owner = v;
	c.movetype = MOVETYPE_NONE;
	if (is_trigger)
	{
		c.solid = SOLID_TRIGGER;
		c.touch = Veh_CockpitTouch;
	}
	else
	{
		c.solid = SOLID_BBOX;
		c.takedamage = DAMAGE_AIM;
		c.th_pain = Veh_ClipPain;
		// T_Damage runs Killed() (and so th_die) on anything whose health reaches 0: the box's damage is passed to the
		// van by Veh_ClipPain, so the box itself must never die (a rocket splash or a ramming van used to crash the server)
		c.health = 1000000;
		c.max_health = 1000000;
		c.th_die = SUB_Null;
	}
	c.angles = v.angles;

	setorigin (c, v.origin + fwd * cx + lft * cy + upv * cz);
	mins_x = 0 - hx;
	mins_y = 0 - hy;
	mins_z = 0 - hz;
	maxs_x = hx;
	maxs_y = hy;
	maxs_z = hz;
	setsize (c, mins, maxs);

	// Chain into linked list on v
	c.enemy = v.veh_clip_head;
	v.veh_clip_head = c;
};

void(entity v) Veh_Van_InitCollision =
{
	local entity clp, nxt;

	// Clean up any existing clips
	clp = v.veh_clip_head;
	while (clp != world)
	{
		nxt = clp.enemy;
		remove (clp);
		clp = nxt;
	}
	v.veh_clip_head = world;

	// 1. Rear walk-in non-slip step bumper (z: 0 .. 16.5 <= 18u Quake stepheight - walk right in!)
	Veh_Van_AddBox (v, -114, -108, -33, 33, 0, 16.5, FALSE);

	// 2. Cargo & Cab Main Corrugated Floor (z: 0 .. 19.5 -> 3.0u step up from rear step bumper!)
	Veh_Van_AddBox (v, -108, 68, -39, 39, 0, 19.5, FALSE);

	// 3. Left Outer Cargo & Cab Wall (z: 19.5 .. 101, y: 38 .. 43 -> 76u clear interior width!)
	Veh_Van_AddBox (v, -108, 68, 38, 43, 19.5, 101.0, FALSE);

	// 4. Right Outer Cargo & Cab Wall (z: 19.5 .. 101, y: -43 .. -38)
	Veh_Van_AddBox (v, -108, 68, -43, -38, 19.5, 101.0, FALSE);

	// 5. Swung-Open 126-deg Left Rear Barn Door (leaves 66u rear doorway y: -33 .. +33 wide open!)
	Veh_Van_AddBox (v, -128, -108, 34, 56, 19.5, 97.0, FALSE);

	// 6. Swung-Open 126-deg Right Rear Barn Door
	Veh_Van_AddBox (v, -128, -108, -56, -34, 19.5, 97.0, FALSE);

	// 7. Crowned H2 High-Roof & Ceiling Cross-Bows (z: 96.5 .. 103.5 -> 77u standing headroom!)
	Veh_Van_AddBox (v, -108, 48, -40, 40, 96.5, 103.5, FALSE);

	// 8. Front Dashboard, Windshield Cowl, Hood & Bull-Nose Bumper (x: 68 .. 113)
	Veh_Van_AddBox (v, 68, 113, -43, 43, 0.0, 52.0, FALSE);

	// 9. Left Rounded Wheel Arch Housing in Cargo Bay (x: -85 .. -51, y: 29 .. 39, z: 19.5 .. 38.5 -> 58u clear aisle!)
	Veh_Van_AddBox (v, -85, -51, 29, 39, 19.5, 38.5, FALSE);

	// 10. Right Rounded Wheel Arch Housing in Cargo Bay (x: -85 .. -51, y: -39 .. -29, z: 19.5 .. 38.5)
	Veh_Van_AddBox (v, -85, -51, -39, -29, 19.5, 38.5, FALSE);

	// 11. Left Bulkhead Partition Wing & Driver Seat Base (y: 17.5 .. 39 -> 35u central walk-through aisle!)
	Veh_Van_AddBox (v, 30, 36, 17.5, 39, 19.5, 82.0, FALSE);

	// 12. Right Bulkhead Partition Wing & Passenger Seat Base (y: -39 .. -17.5)
	Veh_Van_AddBox (v, 30, 36, -39, -17.5, 19.5, 82.0, FALSE);

	// 13. Cockpit Driver Interaction Trigger (x: 36 .. 66, y: -16 .. 34, z: 19.5 .. 76)
	Veh_Van_AddBox (v, 36, 66, -16, 34, 19.5, 76.0, TRUE);

	// Root entity bbox stays strictly beneath z=19.5 cargo floor at ANY yaw angle so cargo bay is 100% open:
	setsize (v, '-16 -16 0', '16 16 19.5');
};

// ---------------------------------------------------------------- Blown-Off Debris & 4-Wheel Gyroscopic Rolling Physics

void(entity e, float spd) Veh_TireSound =
{
	local float vol;

	vol = 0.50 + spd / 650;
	if (vol > 1)
		vol = 1;
	if (random () < 0.5)
		sound7 (e, CHAN_AUTO, "vehicles/tire_thud1.wav", vol, ATTN_NORM, 88 + random () * 26);
	else
		sound7 (e, CHAN_AUTO, "vehicles/tire_thud2.wav", vol, ATTN_NORM, 88 + random () * 26);
};

void() Veh_DebrisTouch =
{
	local float spd, vol;

	if (other.takedamage)
		return;
	spd = vlen (self.velocity);
	if (self.classname == "veh_wheel")
	{
		if (time < self.mm_bouncetime + 0.25 || spd < 55)
			return;
		self.mm_bouncetime = time;
		self.mm_bounces = self.mm_bounces + 1;
		Veh_TireSound (self, spd);
		return;
	}
	if (time < self.mm_bouncetime + 0.25 || spd < 75)
		return;
	self.mm_bouncetime = time;
	self.mm_bounces = self.mm_bounces + 1;
	if (veh_fx_sparks > 0)
		pointparticles (veh_fx_sparks, self.origin, '0 0 0', 1);
	vol = 0.48 + spd / 850;
	if (vol > 0.95)
		vol = 0.95;
	if (random () < 0.5)
		sound7 (self, CHAN_AUTO, "vehicles/clang1.wav", vol, ATTN_NORM, 86 + random () * 30);
	else
		sound7 (self, CHAN_AUTO, "vehicles/clang2.wav", vol, ATTN_NORM, 86 + random () * 30);
};

void() Veh_DebrisThink =
{
	local float age, rem;

	self.nextthink = time + 0.08;
	if (time > self.mm_born + self.mm_life || pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	age = time - self.mm_born;
	rem = self.mm_life - age;
	if (rem < 0.8)
		self.alpha = rem / 0.8;

	if (self.flags & FL_ONGROUND)
	{
		self.avelocity = self.avelocity * 0.45;
		if (vlen (self.avelocity) < 25)
			self.avelocity = '0 0 0';
	}
	if (age < 2.2 && random () < (0.45 - age * 0.16))
		if (veh_fx_sparks > 0)
		pointparticles (veh_fx_sparks, self.origin, '0 0 0', 1);
	if (self.dmg > 0 && age < 3.5)
	{
		if (self.dmg >= 2 && veh_fx_fire > 0)
			pointparticles (veh_fx_fire, self.origin, '0 0 0', 1);
		else if (veh_fx_smoke > 0)
			pointparticles (veh_fx_smoke, self.origin, '0 0 0', 1);
	}
};

entity(string mdl, vector org, vector vel, vector ang, float life) Veh_SpawnDebris =
{
	local entity d;

	d = spawn ();
	d.classname = "veh_debris";
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_TRIGGER;		// collides with world BSP cleanly without snagging players
	d.bouncefactor = 0.44;
	d.bouncestop = 0.08;
	d.alpha = 1;
	d.velocity = vel;
	d.angles = ang;
	d.avelocity_x = crandom () * 520;
	d.avelocity_y = crandom () * 520;
	d.avelocity_z = crandom () * 520;
	d.mm_born = time;
	d.mm_life = life;
	d.touch = Veh_DebrisTouch;
	d.think = Veh_DebrisThink;
	d.nextthink = time + 0.06;
	setmodel (d, mdl);
	setsize (d, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (d, org);
	return d;
};

/*
================
Veh_WheelThink

All 4 unique wheels blast outward, bounce elastically on rubber tread while spinning via
their 16 MD3 frames, then catch traction on the pavement and roll in banked gyroscopic
curves, bounce off walls, drop off ledges, enter Euler's-disk coin-wobble precession as
they lose momentum, and flop flat onto their sidewalls!
================
*/
void() Veh_WheelThink =
{
	local float age, rem, dt, step, f, rad, sn, cs, zh, spd_frac, target_lean, wob, ndot, wr;
	local vector fwd, next_xy, refl;

	dt = 0.04;
	self.nextthink = time + dt;
	if (time > self.mm_born + self.mm_life || pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	age = time - self.mm_born;
	rem = self.mm_life - age;
	if (rem < 0.8)
		self.alpha = rem / 0.8;

	wr = self.veh_wheel_r;

	if (self.mm_state == 0)
	{
		// Airborne elastic bounce phase: spin tread via self.frame, keep pitch = 0
		self.angles_x = 0;
		self.mm_dist = self.mm_dist + 16;
		f = self.mm_dist / self.veh_wheel_step;
		self.frame = floor (f - 16 * floor (f / 16));

		if (vlen (self.velocity) > 38)
			self.mm_roll_yaw = vectoyaw (self.velocity);
		self.angles_y = self.mm_roll_yaw;
		self.mm_lean = self.mm_lean + self.mm_side * 52 * dt;
		if (self.mm_lean > 44)
			self.mm_lean = 44;
		if (self.mm_lean < -44)
			self.mm_lean = -44;
		self.angles_z = self.mm_lean;

		if ((self.flags & FL_ONGROUND) || (self.mm_bounces >= 2 && fabs (self.velocity_z) < 95))
		{
			traceline (self.origin + '0 0 20', self.origin - '0 0 1' * (wr + 16), TRUE, self);
			if (trace_fraction < 1 && trace_plane_normal_z > 0.7)
			{
				self.mm_state = 1;
				self.movetype = MOVETYPE_NONE;
				self.avelocity = '0 0 0';
				self.mm_speed = vlen (self.velocity - '0 0 1' * self.velocity_z);
				if (self.mm_speed < 210)
					self.mm_speed = 210 + random () * 110;
				if (self.mm_speed > 460)
					self.mm_speed = 460;
				self.velocity = '0 0 0';
				self.mm_lean = self.mm_side * (18 + random () * 15);
				self.angles_x = 0;
				self.angles_y = self.mm_roll_yaw;
				self.angles_z = self.mm_lean;
			}
		}
		return;
	}

	// Ground banked gyroscopic rolling & coin-wobble phase
	if (self.mm_speed > 2)
	{
		step = self.mm_speed * dt;
		makevectors ('0 1 0' * self.mm_roll_yaw);
		fwd = v_forward;

		// Reflect off walls/curbs cleanly
		traceline (self.origin + '0 0 4', self.origin + '0 0 4' + fwd * (step + wr + 2), TRUE, self);
		if (trace_fraction < 1 && trace_plane_normal_z < 0.65)
		{
			ndot = fwd * trace_plane_normal;
			refl = fwd - trace_plane_normal * (2 * ndot);
			self.mm_roll_yaw = vectoyaw (refl);
			self.mm_speed = self.mm_speed * 0.76;
			Veh_TireSound (self, self.mm_speed);
			makevectors ('0 1 0' * self.mm_roll_yaw);
			fwd = v_forward;
			step = self.mm_speed * dt;
		}

		next_xy = self.origin + fwd * step;
		traceline (next_xy + '0 0 22', next_xy - '0 0 1' * (wr + 28), TRUE, self);
		if (trace_fraction == 1)
		{
			// Rolled off a ledge or curb: go airborne & bounce again!
			self.mm_state = 0;
			self.movetype = MOVETYPE_BOUNCE;
			self.flags = self.flags - (self.flags & FL_ONGROUND);
			self.mm_bounces = 1;
			self.velocity = fwd * self.mm_speed + '0 0 -30';
			return;
		}

		self.mm_dist = self.mm_dist + step;
		f = self.mm_dist / self.veh_wheel_step;
		self.frame = floor (f - 16 * floor (f / 16));

		self.mm_roll_yaw = Veh_NormYaw (self.mm_roll_yaw - self.mm_lean * 0.15);
		self.mm_speed = self.mm_speed * 0.972 - 2.1;
		if (self.mm_speed < 0)
			self.mm_speed = 0;

		spd_frac = self.mm_speed / 240;
		if (spd_frac > 1)
			spd_frac = 1;
		target_lean = 20 + (1 - spd_frac) * (1 - spd_frac) * 68;
		wob = sin (time * (13 + (1 - spd_frac) * 12));
		self.mm_lean = self.mm_side * target_lean + wob * 8 * spd_frac;
		if (self.mm_speed < 52)
			self.mm_roll_yaw = Veh_NormYaw (self.mm_roll_yaw - self.mm_side * 11);

		rad = fabs (self.mm_lean) * 0.0174533;
		sn = sin (rad);
		cs = cos (rad);
		zh = wr * cs + self.veh_wheel_hw * sn;

		self.angles_x = 0;
		self.angles_y = self.mm_roll_yaw;
		self.angles_z = self.mm_lean;
		setorigin (self, trace_endpos + '0 0 1' * zh);
	}
	else
	{
		// Settled flat onto rubber sidewall
		self.mm_lean = self.mm_side * 88;
		self.angles_x = 0;
		self.angles_z = self.mm_lean;
	}
};

entity(float kind, vector org, vector vel, float side_sgn) Veh_SpawnWheel =
{
	local entity w;
	local float wr, whw;

	if (kind == VEH_TRUCK)
	{
		wr = 16.5;
		whw = 6.2;
	}
	else if (kind == VEH_SEDAN)
	{
		wr = 13.0;
		whw = 4.6;
	}
	else if (kind == VEH_VAN)
	{
		wr = 14.8;
		whw = 5.4;
	}
	else if (kind == VEH_HDTRUCK)
	{
		wr = 18.0;
		whw = 6.1;
	}
	else if (kind == VEH_SCHOOLBUS)
	{
		wr = 17.5;
		whw = 5.5;
	}
	else if (kind == VEH_GTCAR)
	{
		wr = 13.8;
		whw = 5.1;
	}
	else if (kind == VEH_TUKTUK)
	{
		wr = 11.8;
		whw = 2.9;
	}
	else
	{
		wr = 12.6;
		whw = 5.0;
	}

	w = Veh_SpawnDebris (Veh_WheelModel (kind), org, vel, '0 0 0', 11.0);
	if ((kind >= VEH_HDTRUCK && kind <= VEH_GTCAR) || kind == VEH_TUKTUK)
	{
		w.bouncefactor = 0.78;
		w.mm_life = 13.5;
	}
	else
		w.bouncefactor = 0.73;
	w.classname = "veh_wheel";
	w.bouncestop = 0.08;
	w.avelocity = '0 0 0';
	w.veh_wheel_r = wr;
	w.veh_wheel_hw = whw;
	w.veh_wheel_step = (6.283185 * wr) / 16.0;
	w.mm_state = 0;
	w.mm_side = side_sgn;
	w.mm_lean = side_sgn * (14 + random () * 10);
	w.mm_roll_yaw = vectoyaw (vel);
	w.angles = '0 0 0';
	w.angles_y = w.mm_roll_yaw;
	w.think = Veh_WheelThink;
	w.nextthink = time + 0.04;
	return w;
};

// 20-frame 3D core shatter-burst + additive shock starburst at detonation center
void() Veh_BlastThink =
{
	self.frame = self.frame + 1;
	if (self.frame >= 20)
	{
		remove (self);
		return;
	}
	if (self.frame >= 14)
		self.alpha = (20 - self.frame) / 6.0;
	self.nextthink = time + 0.035;
};

// ---------------------------------------------------------------- Camera & On-Foot Screen Shake

void(entity p, float amp, float dur) Veh_AddShake =
{
	local float rem, span, cur_amp;

	if (autocvar_effects_explosion_shake == 0)
		return;
	if (p == world || p.classname != "player" || dur <= 0 || amp <= 0)
		return;

	cur_amp = 0;
	if (time < p.veh_shake_end)
	{
		span = p.veh_shake_end - p.veh_shake_t0;
		if (span > 0.01)
		{
			rem = (p.veh_shake_end - time) / span;
			cur_amp = p.veh_shake_amp * rem;
		}
	}
	if (amp >= cur_amp)
		p.veh_shake_amp = amp;
	else
		p.veh_shake_amp = cur_amp;
	p.veh_shake_t0 = time;
	p.veh_shake_end = max (p.veh_shake_end, time + dur);
};

void(entity p, entity cam, entity veh) Veh_ApplyCamShake =
{
	local float span, frac, mag, jx, jy, jz;
	local vector base_pos, shake_pos;

	if (autocvar_effects_explosion_shake == 0 || time >= p.veh_shake_end)
		return;
	span = p.veh_shake_end - p.veh_shake_t0;
	if (span <= 0.01)
		return;
	frac = bound (0, (p.veh_shake_end - time) / span, 1);
	mag = p.veh_shake_amp * frac * frac;
	if (mag <= 0.05)
		return;

	jx = crandom () * mag;
	jy = crandom () * mag * 0.75;
	jz = crandom () * mag * 1.15;

	cam.angles_x = cam.angles_x + jx;
	cam.angles_y = cam.angles_y + jy;
	cam.angles_z = cam.angles_z + jz;

	base_pos = cam.origin;
	shake_pos = base_pos + randomvec () * min (8, mag * 0.85);
	traceline (base_pos, shake_pos, 3, veh);
	if (trace_fraction < 1)
		shake_pos = trace_endpos + trace_plane_normal * 4;
	setorigin (cam, shake_pos);

	p.punchangle_x = p.punchangle_x + jx * 0.65;
	p.punchangle_y = p.punchangle_y + jy * 0.5;
	p.punchangle_z = p.punchangle_z + jz * 0.75;
};

void() Veh_OnFootShakeThink =
{
	local entity plyr;
	local float span, frac, dist, sh;

	if (autocvar_effects_explosion_shake == 0 || time >= self.veh_wreck_t)
	{
		remove (self);
		return;
	}
	span = self.veh_wreck_t - self.mm_born;
	if (span <= 0.01)
	{
		remove (self);
		return;
	}
	frac = bound (0, (self.veh_wreck_t - time) / span, 1);
	frac = frac * frac;

	plyr = bm_player_head;
	while (plyr != world)
	{
		if (plyr.health > 0 && plyr.veh_van == world && !JohnBird_Flying (plyr) && !RocketRider_Flying (plyr))
		{
			dist = vlen (self.origin - plyr.origin);
			if (dist < self.dmg)
			{
				sh = self.veh_shake_amp * frac * (1.0 - dist / self.dmg);
				plyr.punchangle_x = plyr.punchangle_x + crandom () * sh;
				plyr.punchangle_y = plyr.punchangle_y + crandom () * (sh * 0.7);
				plyr.punchangle_z = plyr.punchangle_z + crandom () * (sh * 1.1);
			}
		}
		plyr = plyr.bm_player_next;
	}
	self.nextthink = time + 0.04;
};

void(vector boom_org, float max_rad, float max_amp, float dur) Veh_ShakeNearby =
{
	local entity plyr, qk;
	local float dist, sh;

	if (autocvar_effects_explosion_shake == 0)
		return;

	plyr = bm_player_head;
	while (plyr != world)
	{
		dist = vlen (boom_org - plyr.origin);
		if (dist < max_rad)
		{
			sh = max_amp * (1.0 - dist / max_rad);
			if (plyr.veh_van != world)
				Veh_AddShake (plyr, sh, dur);
			else
			{
				plyr.punchangle_x = plyr.punchangle_x + crandom () * sh;
				plyr.punchangle_y = plyr.punchangle_y + crandom () * (sh * 0.7);
				plyr.punchangle_z = plyr.punchangle_z + crandom () * (sh * 1.1);
			}
		}
		plyr = plyr.bm_player_next;
	}

	qk = spawn ();
	qk.classname = "veh_quake";
	qk.movetype = MOVETYPE_NONE;
	qk.solid = SOLID_NOT;
	setorigin (qk, boom_org);
	qk.mm_born = time;
	qk.veh_wreck_t = time + dur;
	qk.veh_shake_amp = max_amp;
	qk.dmg = max_rad;
	qk.think = Veh_OnFootShakeThink;
	qk.nextthink = time + 0.04;
};

void() Veh_SecBlastThink =
{
	local entity fb;

	if (veh_fx_explode_sec > 0)
		pointparticles (veh_fx_explode_sec, self.origin, '0 0 0', 1);
	fb = spawn ();
	fb.classname = "veh_fireball";
	fb.movetype = MOVETYPE_NONE;
	fb.solid = SOLID_NOT;
	fb.scale = self.scale;
	setmodel (fb, "progs/s_explodbig.spr");
	setsize (fb, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (fb, self.origin);
	fb.frame = 0;
	fb.think = exploderun;
	fb.nextthink = time + 0.055;
	sound7 (self, CHAN_AUTO, "weapons/r_exp3.wav", 0.92, ATTN_NORM, 68 + random () * 10);
	remove (self);
};

// ---------------------------------------------------------------- State Transitions: Pain, Catch Fire, Explode, Wreck

void(entity v) Veh_StartFire =
{
	if (v.veh_state != VEH_STATE_IDLE)
		return;
	v.veh_state = VEH_STATE_FIRE;
	if (v.veh_kind == VEH_GOLFCART || Veh_IsKart (v.veh_kind))
	{
		v.skin = 0;
		if (v.veh_kind == VEH_GOLFCART)
			v.frame = 0;
	}
	else
	{
		v.skin = 1;						// instant swap to scorched/blistered paint + glowing seams!
		v.colormod = '0 0 0';
		v.frame = 22;
	}
	v.veh_anim = 0;
	v.veh_snd_t = 0;
	v.veh_fx_t = 0;
	v.veh_smoke_t = 0;
	v.veh_cook_t = time + 0.25;
	sound7 (v, CHAN_VOICE, "vehicles/hit_metal2.wav", 0.95, ATTN_NORM, 92 + random () * 14);
};

void(entity attacker, float take) Veh_Pain =
{
	if (self.veh_state == VEH_STATE_WRECK)
		return;
	if (self.veh_kind == VEH_FORELOCO)
	{
		if (time >= self.veh_pain_snd_t)
		{
			self.veh_pain_snd_t = time + 0.16;
			sound7 (self, CHAN_BODY, "foreloco/boing_hit.wav", 0.72, ATTN_NORM, 98 + random () * 18);
		}
		return;
	}
	if (attacker != world && attacker != self && !attacker.veh_kind)
		self.veh_igniter = attacker;
	else if (attacker.veh_kind && attacker.veh_igniter != world)
		self.veh_igniter = attacker.veh_igniter;

	if (time >= self.veh_pain_snd_t)
	{
		self.veh_pain_snd_t = time + 0.09;
		if (random () < 0.5)
			sound7 (self, CHAN_BODY, "vehicles/hit_metal1.wav", 0.75, ATTN_NORM, 92 + random () * 20);
		else
			sound7 (self, CHAN_BODY, "vehicles/hit_metal2.wav", 0.78, ATTN_NORM, 92 + random () * 20);
	}

	if (self.veh_state == VEH_STATE_IDLE)
	{
		if (self.health <= self.max_health * 0.48)
			Veh_StartFire (self);
		else if (take >= 6)
		{
			self.veh_flinch_end = time + 0.30;
			self.veh_anim = 0;
			// MOVETYPE_PUSH (Spruce bus) thinks on its own .ltime clock: a time-based nextthink would stall it for ~map uptime
			if (self.movetype == MOVETYPE_PUSH)
				self.nextthink = self.ltime + 0.02;
			else
				self.nextthink = time + 0.02;
		}
	}
};

void() Veh_ExplodeNow =
{
	local float kind, fx, rx, wy, wz, dx, dy, dz, ex, ez, bfx, brx, bz, i, cspd;
	local vector fwd, lft, upv, wpos, wvel, ang_opp, blast_org, crash_vel;
	local entity atk, inf, b, fb, deb, drv;

	if (self.veh_state == VEH_STATE_WRECK)
		return;

	kind = self.veh_kind;
	if (kind == VEH_FORELOCO)
	{
		self.veh_state = VEH_STATE_WRECK;
		drv = self.veh_driver;
		if (drv != world)
			FL_Reset (drv);
		Veh_Leave (self, self.origin + '0 0 24', '0 0 180', TRUE);
		return;
	}
	self.veh_state = VEH_STATE_WRECK;
	self.veh_chain_t = 0;
	self.veh_coast_until = 0;
	self.takedamage = DAMAGE_NO;
	self.skin = 0;
	self.colormod = '0 0 0';

	// Preserve moving crash momentum for flying debris & secondary blast before bailing clears state
	crash_vel = self.velocity * 0.42;
	cspd = vlen (crash_vel);
	if (cspd > 650)
		crash_vel = normalize (crash_vel) * 650;

	atk = self.veh_igniter;
	if (atk == world)
		atk = self;
	drv = self.veh_driver;
	if (drv != world && (atk == drv || atk == self || atk == world))
	{
		drv.veh_last_van = self;
		drv.veh_bail_safe_t = time + 1.0;		// self-crash blasts fling the driver clear instead of 195-dmg instakill
	}

	// Whoever is driving / riding goes out at the seat, with the vehicle's speed, into the blast
	Veh_AllPassengersBail (self, TRUE);
	Veh_DriverBail (self);
	if (self.veh_driverent != world)
	{
		remove (self.veh_driverent);
		self.veh_driverent = world;
	}

	// Clean up child collision clips if this vehicle had a walk-in interior
	local entity clp, nxt_clp;
	clp = self.veh_clip_head;
	while (clp != world)
	{
		nxt_clp = clp.enemy;
		remove (clp);
		clp = nxt_clp;
	}
	self.veh_clip_head = world;

	// Stop burning loop on CHAN_ITEM, fire huge layered fuel-tank detonation sound!
	sound (self, CHAN_ITEM, "misc/null.wav", 1, ATTN_NORM);
	if (random () < 0.5)
		sound7 (self, CHAN_VOICE, "vehicles/car_boom1.wav", 1.0, 0.55, 92 + random () * 12);
	else
		sound7 (self, CHAN_VOICE, "vehicles/car_boom2.wav", 1.0, 0.55, 92 + random () * 12);
	sound7 (self, CHAN_BODY, "weapons/r_exp3.wav", 1.0, 0.55, 72 + random () * 10);
	sound7 (self, CHAN_AUTO, "weapons/explodedist.wav", 0.95, 0.22, 92 + random () * 10);

	makevectors ('0 1 0' * self.angles_y);
	fwd = v_forward;
	lft = '0 0 0' - v_right;		// +Y in model space = left / driver side!
	upv = '0 0 1';

	blast_org = self.origin + '0 0 38';
	if (veh_fx_explode > 0)
		pointparticles (veh_fx_explode, blast_org, '0 0 0', 1);

	// Fiery non-whiteout explosion fireball (replaces the blinding additive veh_blast_flash polygon dome)
	fb = spawn ();
	fb.classname = "veh_fireball";
	fb.movetype = MOVETYPE_NONE;
	fb.solid = SOLID_NOT;
	fb.scale = Veh_IsKart (kind) ? 1.55 : 2.15;
	setmodel (fb, "progs/s_explodbig.spr");
	setsize (fb, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (fb, blast_org + '0 0 12');
	fb.frame = 0;
	fb.think = exploderun;
	fb.nextthink = time + 0.055;

	// Staggered secondary fuel-tank blast 0.14s later along crash momentum
	b = spawn ();
	b.classname = "veh_sec_blast";
	b.movetype = MOVETYPE_NONE;
	b.solid = SOLID_NOT;
	b.scale = Veh_IsKart (kind) ? 1.2 : 1.75;
	setsize (b, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (b, blast_org + crash_vel * 0.10 + '0 0 28');
	b.think = Veh_SecBlastThink;
	b.nextthink = time + 0.14;

	// Seismic camera & on-foot screen shake across the street
	Veh_ShakeNearby (blast_org, 1050, 10.5, 0.65);

	// Per-vehicle exact sub-part coordinates (matching blender_build_vehicles.py & blender_build_wild_vehicles.py)
	local float wy_in, wild_mul, shrap_cnt, rad_dmg;
	wy_in = 0;
	wild_mul = 1.0;
	shrap_cnt = 6;
	rad_dmg = 175;
	if (kind == VEH_TRUCK)
	{
		fx = 68;  rx = -64;  wy = 36.5; wz = 18;
		dx = 18;  dy = 40;   dz = 44;
		ex = -68; ez = 53;
		bfx = 113; brx = -115; bz = 18;
	}
	else if (kind == VEH_SEDAN)
	{
		fx = 57;  rx = -55;  wy = 32.5; wz = 15;
		dx = 14;  dy = 34;   dz = 33;
		ex = -71; ez = 36;
		bfx = 96; brx = -96; bz = 15;
	}
	else if (kind == VEH_VAN)
	{
		fx = 80;  rx = -68;  wy = 38.2; wz = 15.2;
		dx = 57.5; dy = 45.0; dz = 45.3;
		ex = -123; ez = 58;
		bfx = 100; brx = -99; bz = 24;
		wild_mul = 1.25;
		shrap_cnt = 8;
		rad_dmg = 195;
	}
	else if (kind == VEH_HDTRUCK)
	{
		fx = 78;  rx = -70;  wy = 39.5; wy_in = 29.0; wz = 18;
		dx = 22;  dy = 44.5; dz = 48;
		ex = -75; ez = 52;
		bfx = 120; brx = -124; bz = 20;
		wild_mul = 1.78;
		shrap_cnt = 10;
		rad_dmg = 215;
	}
	else if (kind == VEH_SCHOOLBUS)
	{
		fx = 110; rx = -92;  wy = 40.5; wy_in = 30.5; wz = 17.5;
		dx = 81;  dy = 46.5; dz = 54;
		ex = -140; ez = 82;
		bfx = 152; brx = -174; bz = 20;
		wild_mul = 1.72;
		shrap_cnt = 12;
		rad_dmg = 240;
	}
	else if (kind == VEH_GTCAR)
	{
		fx = 58.5; rx = -56.5; wy = 34.2; wz = 14;
		dx = 6;    dy = 38.0;  dz = 31;
		ex = -79;  ez = 38;
		bfx = 97;  brx = -97;  bz = 14;
		wild_mul = 1.85;
		shrap_cnt = 10;
		rad_dmg = 195;
	}
	else if (kind == VEH_GOLFCART)
	{
		fx = 34;  rx = -34;  wy = 22.0; wz = 12;
		dx = 0;   dy = 24.0; dz = 24;
		ex = -40; ez = 34;
		bfx = 48; brx = -48; bz = 12;
		rad_dmg = 160;
	}
	else if (kind == VEH_TUKTUK)
	{
		fx = 43;  rx = -34;  wy = 24.5; wz = 12;
		dx = 0;   dy = 25.0; dz = 32;
		ex = -14; ez = 66;
		bfx = 48; brx = -52; bz = 13;
		wild_mul = 1.95;
		shrap_cnt = 10;
		rad_dmg = 190;
	}
	else
	{
		fx = 54;  rx = -52;  wy = 32.8; wz = 15;
		dx = 5;   dy = 33.5; dz = 29;
		ex = -82; ez = 40;
		bfx = 91; brx = -90; bz = 12;
	}

	// 1. Launch ALL 3 (Tuk-Tuk), 4, or 6 (dually!) UNIQUE WHEELS with fierce skyward/outward arcs & banked rolling!
	// Go-karts use their built-in MD3 explode animation (frames 44..63) + shrapnel instead of car sub-part models.
	if (Veh_IsKart (kind))
	{
		wild_mul = 1.25;
		shrap_cnt = 6;
		rad_dmg = 160;
	}
	else
	{
	if (kind == VEH_TUKTUK)
	{
		// Single Front Center Wheel (+X, 0)
		wpos = self.origin + fwd * fx + upv * wz;
		wvel = (fwd * (215 + random () * 115) + lft * (crandom () * 125) + upv * (340 + random () * 145)) * wild_mul + crash_vel;
		Veh_SpawnWheel (kind, wpos, wvel, 1);
	}
	else
	{
		// Front-Left (+X, +Y)
		wpos = self.origin + fwd * fx + lft * wy + upv * wz;
		wvel = (fwd * (145 + random () * 110) + lft * (215 + random () * 120) + upv * (350 + random () * 150)) * wild_mul + crash_vel;
		Veh_SpawnWheel (kind, wpos, wvel, 1);

		// Front-Right (+X, -Y)
		wpos = self.origin + fwd * fx - lft * wy + upv * wz;
		wvel = (fwd * (135 + random () * 115) - lft * (215 + random () * 120) + upv * (340 + random () * 155)) * wild_mul + crash_vel;
		Veh_SpawnWheel (kind, wpos, wvel, -1);
	}

	// Rear-Left (-X, +Y)
	wpos = self.origin + fwd * rx + lft * wy + upv * wz;
	wvel = (fwd * (-145 - random () * 110) + lft * (210 + random () * 125) + upv * (330 + random () * 160)) * wild_mul + crash_vel;
	Veh_SpawnWheel (kind, wpos, wvel, -1);

	// Rear-Right (-X, -Y)
	wpos = self.origin + fwd * rx - lft * wy + upv * wz;
	wvel = (fwd * (-135 - random () * 115) - lft * (210 + random () * 125) + upv * (360 + random () * 150)) * wild_mul + crash_vel;
	Veh_SpawnWheel (kind, wpos, wvel, 1);

	// Extra Dually Inner Rear Wheels (6-wheel Heavy-Duty Diesel Rig & School Bus!)
	if (wy_in > 0)
	{
		wpos = self.origin + fwd * rx + lft * wy_in + upv * wz;
		wvel = (fwd * (-95 - random () * 95) + lft * (265 + random () * 130) + upv * (385 + random () * 155)) * wild_mul + crash_vel;
		Veh_SpawnWheel (kind, wpos, wvel, 1);

		wpos = self.origin + fwd * rx - lft * wy_in + upv * wz;
		wvel = (fwd * (85 + random () * 95) - lft * (265 + random () * 130) + upv * (395 + random () * 155)) * wild_mul + crash_vel;
		Veh_SpawnWheel (kind, wpos, wvel, -1);
	}

	// 2. Launch Blown-Off Scorched Hood (high spinning flip with fire trail!)
	wpos = self.origin + fwd * (fx + 10) + upv * (dz + 4);
	wvel = (fwd * (110 + crandom () * 90) + lft * (crandom () * 120) + upv * (510 + random () * 150)) * wild_mul + crash_vel;
	deb = Veh_SpawnDebris (Veh_HoodModel (kind), wpos, wvel, self.angles, 11.5);
	deb.dmg = 2;

	// 3. Launch Left & Right Doors + Mirrors (or STOP Sign / Bi-Fold Bus Doors) sideways!
	ang_opp = self.angles;
	ang_opp_y = Veh_NormYaw (self.angles_y + 180);

	wpos = self.origin + fwd * dx + lft * dy + upv * dz;
	wvel = (fwd * (crandom () * 95) + lft * (290 + random () * 130) + upv * (295 + random () * 130)) * wild_mul + crash_vel;
	Veh_SpawnDebris (Veh_DoorModel (kind), wpos, wvel, self.angles, 11.0);

	wpos = self.origin + fwd * dx - lft * dy + upv * dz;
	wvel = (fwd * (crandom () * 95) - lft * (290 + random () * 130) + upv * (295 + random () * 130)) * wild_mul + crash_vel;
	Veh_SpawnDebris (Veh_DoorModel (kind), wpos, wvel, ang_opp, 11.0);

	// 4. Launch Signature Extra Part (Stacks+HeadacheRack / EmergencyDoor+Hatches / Trunk+Wing) with smoke trail
	wpos = self.origin + fwd * ex + upv * ez;
	wvel = (fwd * (-175 + crandom () * 80) + lft * (crandom () * 130) + upv * (420 + random () * 140)) * wild_mul + crash_vel;
	deb = Veh_SpawnDebris (Veh_ExtraModel (kind), wpos, wvel, self.angles, 11.5);
	deb.dmg = 1;

	// 5. Launch Front & Rear Bumpers
	wpos = self.origin + fwd * bfx + upv * bz;
	wvel = (fwd * (310 + random () * 110) + lft * (crandom () * 95) + upv * (230 + random () * 110)) * wild_mul + crash_vel;
	Veh_SpawnDebris (Veh_BumperModel (kind), wpos, wvel, self.angles, 10.5);

	wpos = self.origin + fwd * brx + upv * bz;
	wvel = (fwd * (-310 - random () * 110) + lft * (crandom () * 95) + upv * (230 + random () * 110)) * wild_mul + crash_vel;
	Veh_SpawnDebris (Veh_BumperModel (kind), wpos, wvel, ang_opp, 10.5);
	}

	// 6. Scatter Twisted Scorched Shrapnel Chunks. In a chain reaction (another car went up in the last 3 s) each car
	// throws fewer: a parking-lot domino used to leave hundreds of thinking, networked chunks
	if (time - veh_boom_t < 3)
		veh_boom_n = veh_boom_n + 1;
	else
		veh_boom_n = 1;
	veh_boom_t = time;
	shrap_cnt = max (2, floor (shrap_cnt / veh_boom_n));
	i = 0;
	while (i < shrap_cnt)
	{
		wpos = blast_org + fwd * (crandom () * 38) + lft * (crandom () * 28);
		wvel = (fwd * (crandom () * 390) + lft * (crandom () * 390) + upv * (280 + random () * 260)) * wild_mul + crash_vel;
		if ((i & 3) == 0)
			deb = Veh_SpawnDebris ("progs/veh_shrap1.md3", wpos, wvel, '0 0 0', 8.5);
		else if ((i & 3) == 1)
			deb = Veh_SpawnDebris ("progs/veh_shrap2.md3", wpos, wvel, '0 0 0', 8.5);
		else if ((i & 3) == 2)
			deb = Veh_SpawnDebris ("progs/veh_shrap3.md3", wpos, wvel, '0 0 0', 8.5);
		else
			deb = Veh_SpawnDebris ("progs/veh_shrap4.md3", wpos, wvel, '0 0 0', 8.5);
		if (i < 2)
			deb.dmg = 2;
		i = i + 1;
	}

	// 7. Transform vehicle entity into its leaping/flipping/rolling crumpled charred wreck!
	if (Veh_IsKart (kind))
	{
		self.solid = SOLID_NOT;
		setsize (self, '-16 -16 0', '16 16 16');
		// blown up mid-air: drop the wreck to the floor instead of hovering for 8 s (MOVETYPE_NONE)
		tracebox (self.origin, self.mins, self.maxs, self.origin - '0 0 4096', TRUE, self);
		if (!trace_startsolid && !trace_allsolid && trace_fraction < 1)
			setorigin (self, trace_endpos + '0 0 0.5');
		else
			setorigin (self, self.origin);
		self.veh_air = FALSE;
		self.frame = 44;
		self.veh_anim = 44;
		self.veh_wreck_t = time + 8.0;
		self.veh_fx_t = time + 0.5;
		self.think = Veh_Think;
		self.nextthink = time + 0.05;
	}
	else
	{
		setmodel (self, Veh_WreckModel (kind));
		if (kind == VEH_GOLFCART)
			self.scale = 0.65;
		Veh_SetRotatedBounds (self, kind, TRUE);
		setorigin (self, self.origin);
		if (self.veh_air)
		{
			self.movetype = MOVETYPE_TOSS;
			self.flags = self.flags - (self.flags & FL_ONGROUND);
			self.velocity = crash_vel * 0.55 + '0 0 140';
			self.veh_air = FALSE;
		}
		self.frame = 0;
		self.veh_anim = 0;
		self.veh_wreck_t = time + 15.0;
		self.veh_fx_t = time + 0.9;
		self.think = Veh_Think;
		self.nextthink = time + 0.055;
	}

	// 8. Deal explosion radius damage (triggers chain reactions on neighboring parked cars!)
	inf = spawn ();
	inf.classname = "veh_blast_inflictor";
	setorigin (inf, blast_org);
	veh_inflicting = TRUE;
	T_RadiusDamage (inf, atk, rad_dmg, self);
	veh_inflicting = FALSE;
	remove (inf);
};

void() Veh_Explode =
{
	if (self.veh_state == VEH_STATE_WRECK)
		return;
	if (damage_attacker != world && damage_attacker != self && !damage_attacker.veh_kind)
		self.veh_igniter = damage_attacker;
	else if (damage_attacker.veh_kind && damage_attacker.veh_igniter != world)
		self.veh_igniter = damage_attacker.veh_igniter;

	// Domino chain reaction: if killed by a neighboring car's blast, ignite & detonate 0.22s later!
	if (veh_inflicting && self.veh_chain_t == 0)
	{
		if (self.veh_state == VEH_STATE_IDLE)
			Veh_StartFire (self);
		self.health = 1;
		self.takedamage = DAMAGE_NO;
		self.veh_chain_t = time + 0.18 + random () * 0.14;
		self.think = Veh_Think;
		self.nextthink = time + 0.05;
		return;
	}

	// not right here: a rocket's T_RadiusDamage may be what killed it, and its own findradius would rewrite the .chain
	// list that loop is still walking (players further out got no splash, others two). It goes off on its next think.
	self.health = 1;
	self.takedamage = DAMAGE_NO;
	self.veh_chain_t = time;
	self.think = Veh_Think;
	self.nextthink = time;
};

// ---------------------------------------------------------------- Main Per-Vehicle State Machine Think

void() Veh_TryRespawn =
{
	local float hl, hw, ht, rad, acs, asn, hx, hy;
	local vector bmin, bmax;

	if (Veh_IsKart (self.veh_kind))
		tracebox (self.veh_spawn_org + '0 0 2', '-48 -36 0', '48 36 36', self.veh_spawn_org + '0 0 2', FALSE, self);
	else
	{
		hl = Veh_HalfLen (self.veh_kind);
		hw = Veh_HalfWid (self.veh_kind);
		ht = Veh_BodyHeight (self.veh_kind);
		rad = self.veh_spawn_ang_y * 0.0174533;
		acs = fabs (cos (rad));
		asn = fabs (sin (rad));
		hx = acs * hl + asn * hw;
		hy = asn * hl + acs * hw;
		bmin = '0 0 0';
		bmax = '0 0 0';
		bmin_x = 0 - hx;
		bmin_y = 0 - hy;
		bmax_x = hx;
		bmax_y = hy;
		bmax_z = ht;
		tracebox (self.veh_spawn_org + '0 0 2', bmin, bmax, self.veh_spawn_org + '0 0 2', FALSE, self);
	}
	if (trace_startsolid || trace_allsolid || trace_ent != world)
	{
		// Wait until player/monster steps clear of the parking spot
		self.nextthink = time + 2.0;
		return;
	}
	setorigin (self, self.veh_spawn_org);
	self.angles = self.veh_spawn_ang;
	Veh_InitEntity (self, self.veh_kind);
	sound (self, CHAN_VOICE, "items/itembk2.wav", 0.8, ATTN_NORM);
};

void() Veh_Think =
{
	local vector hofs, fpos;
	local float rate, f;

	if (self.veh_chain_t > 0 && time >= self.veh_chain_t)
	{
		Veh_ExplodeNow ();
		return;
	}

	// a driver who died or dropped is let go of (vehicle_drive.qc)
	if (self.veh_driver != world)
		Veh_DriveWatch (self);
	else if (self.veh_state != VEH_STATE_WRECK && self.veh_coast_until > 0)
	{
		Veh_CoastStep (self, 0.05);
		if (self.veh_state == VEH_STATE_WRECK)
			return;
	}

	// ---- STATE 2: Crumpled Charred Wreck (frames 0..19 or 0..39 wild airborne-flip -> ground barrel-roll -> smolder)
	if (self.veh_state == VEH_STATE_WRECK)
	{
		if (self.movetype == MOVETYPE_TOSS && (self.flags & FL_ONGROUND))
		{
			self.movetype = MOVETYPE_NONE;
			self.velocity = '0 0 0';
			sound7 (self, CHAN_BODY, "vehicles/clang2.wav", 0.95, ATTN_NORM, 74 + random () * 12);
			if (veh_fx_sparks > 0)
				pointparticles (veh_fx_sparks, self.origin + '0 0 10', '0 0 0', 1);
		}
		if (Veh_IsKart (self.veh_kind))
		{
			if (self.frame < 63)
			{
				self.frame = self.frame + 1;
				if (self.frame == 52)
				{
					sound7 (self, CHAN_BODY, "vehicles/clang2.wav", 0.90, ATTN_NORM, 84 + random () * 14);
					if (veh_fx_sparks > 0)
						pointparticles (veh_fx_sparks, self.origin + '0 0 10', '0 0 0', 1);
				}
				self.nextthink = time + 0.05;
				return;
			}
			if (time < self.veh_wreck_t)
			{
				makevectors ('0 1 0' * self.angles_y);
				hofs = Veh_HoodFireOfs (self.veh_kind);
				fpos = self.origin + v_forward * hofs_x + '0 0 1' * hofs_z;
				if (veh_fx_wreck > 0)
					pointparticles (veh_fx_wreck, fpos, '0 0 0', 1);
				self.nextthink = time + 0.22;
				return;
			}
			if (!self.veh_temp && autocvar_veh_respawn > 0)
			{
				self.think = Veh_TryRespawn;
				self.nextthink = time + min (autocvar_veh_respawn, 15);
				return;
			}
			self.nextthink = -1;
			return;
		}
		local float max_wf, is_wild;
		is_wild = ((self.veh_kind >= VEH_HDTRUCK && self.veh_kind <= VEH_GTCAR) || self.veh_kind == VEH_TUKTUK);
		max_wf = 19;
		if (is_wild)
			max_wf = 39;

		if (self.frame < max_wf)
		{
			self.frame = self.frame + 1;
			if (is_wild)
			{
				if (self.frame == 7)
				{
					// Mid-air secondary fuel-cell blast while flipping high in the sky!
					sound7 (self, CHAN_BODY, "weapons/r_exp3.wav", 0.72, ATTN_NORM, 96 + random () * 12);
					pointparticles (veh_fx_explode, self.origin + '0 0 180', '0 0 0', 1);
				}
				else if (self.frame == 15 || self.frame == 23 || self.frame == 31)
				{
					// Airborne car crashes down & barrel-rolls across the pavement showering sparks!
					sound7 (self, CHAN_BODY, "vehicles/clang2.wav", 0.95, ATTN_NORM, 76 + random () * 16);
					pointparticles (veh_fx_sparks, self.origin + '0 0 14', '0 0 0', 1);
				}
			}
			else if (self.frame == 10)
			{
				// Heavy chassis hulk slams back onto the asphalt!
				sound7 (self, CHAN_BODY, "vehicles/clang2.wav", 0.92, ATTN_NORM, 78 + random () * 12);
				pointparticles (veh_fx_sparks, self.origin + '0 0 10', '0 0 0', 1);
			}
			if (is_wild)
				self.nextthink = time + 0.085;
			else
				self.nextthink = time + 0.055;
			return;
		}

		// Settled at frame 19: emit lingering wreck flames & thin smoke for 14 seconds
		if (time < self.veh_wreck_t)
		{
			makevectors ('0 1 0' * self.angles_y);
			hofs = Veh_HoodFireOfs (self.veh_kind);
			fpos = self.origin + v_forward * (hofs_x * 0.55) + '0 0 1' * (hofs_z * 0.65);
			pointparticles (veh_fx_wreck, fpos, '0 0 0', 1);
			self.nextthink = time + 0.20;
			return;
		}

		if (!self.veh_temp && autocvar_veh_respawn > 0)
		{
			self.think = Veh_TryRespawn;
			self.nextthink = time + autocvar_veh_respawn;
			return;
		}
		self.nextthink = -1;
		return;
	}

	// Safety check in case pain callback was ever skipped
	if (self.veh_state == VEH_STATE_IDLE && self.health <= self.max_health * 0.48)
		Veh_StartFire (self);

	// ---- STATE 1: Catching Fire / Cooking Off (skin 1 + frames 22..35 popped rattling hood)
	if (self.veh_state == VEH_STATE_FIRE)
	{
		self.nextthink = time + 0.05;
		if (Veh_IsKart (self.veh_kind))
			GK_ThinkAnim (self);
		else
		{
			self.veh_anim = self.veh_anim + 0.95;
			f = floor (self.veh_anim);
			if (self.veh_kind == VEH_GOLFCART)
				self.frame = 0;
			else
				self.frame = 22 + (f - 14 * floor (f / 14));
		}

		makevectors ('0 1 0' * self.angles_y);
		hofs = Veh_HoodFireOfs (self.veh_kind);
		fpos = self.origin + v_forward * hofs_x + '0 0 1' * hofs_z;

		if (time >= self.veh_fx_t)
		{
			self.veh_fx_t = time + 0.06;
			if (veh_fx_fire > 0)
				pointparticles (veh_fx_fire, fpos, '0 0 0', 1);
		}
		if (time >= self.veh_smoke_t)
		{
			self.veh_smoke_t = time + 0.12;
			if (veh_fx_smoke > 0)
				pointparticles (veh_fx_smoke, fpos + '0 0 6', '0 0 0', 1);
		}
		if (time >= self.veh_snd_t)
		{
			self.veh_snd_t = time + 0.98;
			sound7 (self, CHAN_ITEM, "vehicles/fire_burn.wav", 0.78, ATTN_NORM, 98 + random () * 6);
		}
		if (self.veh_chain_t == 0 && time >= self.veh_cook_t)
		{
			self.veh_cook_t = time + 0.25;
			self.health = self.health - 6;
			if (self.health <= 0)
			{
				Veh_ExplodeNow ();
				return;
			}
		}
		return;
	}

	// ---- STATE 0: Intact Running Idle (frames 0..15, or 16..21 during bullet hit flinch)
	if (self.veh_driver == world && self.veh_coast_until <= 0 && time >= self.veh_flinch_end)
	{
		if (Veh_IsKart (self.veh_kind))
		{
			self.frame = 0;
			self.nextthink = time + 0.5;
			return;
		}
		local entity hp;
		local float near_plr;
		near_plr = FALSE;
		hp = bm_player_head;
		while (hp)
		{
			if (hp.ishuman == 1 && vlen (hp.origin - self.origin) < 700)
			{
				near_plr = TRUE;
				break;
			}
			hp = hp.bm_player_next;
		}
		if (!near_plr)
		{
			self.nextthink = time + 0.5;
			return;
		}
	}
	if (self.veh_coast_until > 0 || (Veh_IsKart (self.veh_kind) && self.veh_driver != world))
		self.nextthink = time + 0.05;
	else
		self.nextthink = time + 0.06;
	if (Veh_IsKart (self.veh_kind))
		GK_ThinkAnim (self);
	else if (self.veh_kind == VEH_GOLFCART)
		self.frame = 0;
	else if (time < self.veh_flinch_end)
	{
		f = floor ((0.30 - (self.veh_flinch_end - time)) * 20.0);
		if (f < 0)
			f = 0;
		if (f > 5)
			f = 5;
		self.frame = 16 + f;
	}
	else
	{
		if (self.veh_kind == VEH_SCHOOLBUS)
			rate = 0.56;
		else if (self.veh_kind == VEH_HDTRUCK)
			rate = 0.60;
		else if (self.veh_kind == VEH_TRUCK)
			rate = 0.62;
		else if (self.veh_kind == VEH_VAN)
			rate = 0.68;
		else if (self.veh_kind == VEH_SEDAN)
			rate = 0.76;
		else if (self.veh_kind == VEH_GTCAR)
			rate = 0.96;
		else if (self.veh_kind == VEH_TUKTUK)
			rate = 1.15;
		else
			rate = 0.92;
		if (self.veh_driver != world)
			rate = 0.9 + self.veh_rpm * 1.6;		// the body shudders faster as the revs climb
		self.veh_anim = self.veh_anim + rate;
		f = floor (self.veh_anim);
		self.frame = f - 16 * floor (f / 16);
	}

	if (time >= self.veh_snd_t)
	{
		self.veh_snd_t = time + 1.0;
		if (self.veh_driver == world && self.veh_kind != VEH_FORELOCO)		// the driven van plays its own engine note
			sound7 (self, CHAN_ITEM, Veh_IdleSound (self.veh_kind), 0.26, ATTN_STATIC, 100);
	}
};

// ---------------------------------------------------------------- Initialization & Map Spawn Functions

// Fast box distance cull so parked high-poly vehicles & go-karts (11k-21k tris each) across huge maps
// do not send/animate/trace for distant players or bots.
float() Veh_Customize =
{
	local vector vorg;
	local float lim, dx, dy;

	if (other.ishuman == 0)		// bots see nothing; humans (1) and observers (3) see vehicles (audit 2026-11-26)
		return FALSE;
	if (other.veh_van == self || other.veh_ride == self)
		return TRUE;
	vorg = (other.clientcamera != world) ? other.clientcamera.origin : other.origin;
	if (self.veh_driver != world)
		lim = 4800;
	else if (Veh_IsKart (self.veh_kind))
		lim = 2400;
	else
		lim = 3200;
	dx = vorg_x - self.origin_x;
	if (dx > lim || dx < (0 - lim))
		return FALSE;
	dy = vorg_y - self.origin_y;
	if (dy > lim || dy < (0 - lim))
		return FALSE;
	return TRUE;
};

void(entity v, float kind) Veh_InitEntity =
{
	local vector org_top;

	if (!v.veh_temp || time <= 1.1)
	{
		Vehicles_Precache ();
		if (Veh_IsKart (kind))
			GK_Precache ();
		// only the kinds this map actually spawns: the body, its wreck and the parts it throws when it blows up
		// (kinds without parts of their own, the golf cart and the karts, use the coupe's)
		precache_model (Veh_IntactModel (kind));
		precache_model (Veh_WreckModel (kind));
		precache_model (Veh_WheelModel (kind));
		precache_model (Veh_HoodModel (kind));
		precache_model (Veh_DoorModel (kind));
		precache_model (Veh_ExtraModel (kind));
		precache_model (Veh_BumperModel (kind));
	}
	veh_has_vans = TRUE;
	v.veh_kind = kind;
	v.veh_state = VEH_STATE_IDLE;
	v.scale = 1;
	v.skin = 0;
	if (kind == VEH_TUKTUK)
	{
		v.veh_orig_colormod = '0 0 0';
		v.veh_has_cm = TRUE;
	}
	else if (!v.veh_has_cm)
	{
		v.veh_orig_colormod = v.colormod;
		v.veh_has_cm = TRUE;
	}
	v.colormod = v.veh_orig_colormod;
	if (kind == VEH_GOLFCART || kind == VEH_FORELOCO)
		v.frame = 0;
	else if (Veh_IsKart (kind))
		v.frame = floor (random () * 12);
	else
		v.frame = floor (random () * 16);
	v.veh_anim = v.frame;
	if (Veh_IsKart (kind))
		GK_InitKart (v);
	v.veh_flinch_end = 0;
	v.veh_chain_t = 0;
	v.veh_coast_until = 0;
	v.veh_pad_cool = 0;
	if (kind != VEH_FORELOCO)
		v.customizeentityforclient = Veh_Customize;
	v.veh_pad_scan_t = 0;
	v.veh_pad_spin = FALSE;
	v.veh_pad_launch_t = 0;
	v.veh_pad_horn_t = 0;
	v.veh_spin_yaw = 0;
	v.veh_spin_pitch = 0;
	v.veh_spin_roll = 0;
	v.veh_igniter = world;
	v.veh_snd_t = time + random () * 0.8;

	v.movetype = MOVETYPE_NONE;
	v.solid = SOLID_BBOX;
	v.takedamage = DAMAGE_AIM;
	v.max_health = Veh_MaxHP (kind);
	v.health = v.max_health;
	v.th_pain = Veh_Pain;
	v.th_die = Veh_Explode;

	setmodel (v, Veh_IntactModel (kind));

	// Snap tire contact patch cleanly onto map floor (+0.5u above BSP plane so splash traces never snag floor)
	// Must run BEFORE Veh_Van_InitCollision so all 13 child clip/trigger boxes align with the snapped floor origin.
	org_top = v.origin + '0 0 36';
	traceline (org_top, v.origin - '0 0 256', TRUE, v);
	if (trace_fraction < 1 && !trace_startsolid)
		setorigin (v, trace_endpos + '0 0 0.5');
	else
		setorigin (v, v.origin);

	if (kind == VEH_VAN)
	{
		local float snap, dy;
		v.customizeentityforclient = Veh_VanCustomize;
		snap = floor ((v.angles_y + 45) / 90) * 90;
		dy = v.angles_y - snap;
		while (dy > 180)
			dy = dy - 360;
		while (dy < -180)
			dy = dy + 360;
		if (fabs (dy) <= 5)
		{
			v.angles_y = Veh_NormYaw (snap);
			Veh_Van_InitCollision (v);
		}
		else
			Veh_SetRotatedBounds (v, kind, FALSE);
	}
	else
		Veh_SetRotatedBounds (v, kind, FALSE);

	v.veh_spawn_org = v.origin;
	v.veh_spawn_ang = v.angles;
	v.think = Veh_Think;
	v.nextthink = time + 0.05 + random () * 0.05;
};

void() misc_vehicle_truck =
{
	Vehicles_Precache ();
	self.classname = "misc_vehicle_truck";
	Veh_InitEntity (self, VEH_TRUCK);
};

void() misc_vehicle_sedan =
{
	Vehicles_Precache ();
	self.classname = "misc_vehicle_sedan";
	Veh_InitEntity (self, VEH_SEDAN);
};

void() misc_vehicle_van =
{
	Vehicles_Precache ();
	self.classname = "misc_vehicle_van";
	Veh_InitEntity (self, VEH_VAN);
};

void() misc_vehicle_coupe =
{
	Vehicles_Precache ();
	self.classname = "misc_vehicle_coupe";
	Veh_InitEntity (self, VEH_COUPE);
};

void() misc_vehicle_hdtruck =
{
	Vehicles_Precache ();
	self.classname = "misc_vehicle_hdtruck";
	Veh_InitEntity (self, VEH_HDTRUCK);
};

void() misc_vehicle_schoolbus =
{
	Vehicles_Precache ();
	self.classname = "misc_vehicle_schoolbus";
	Veh_InitEntity (self, VEH_SCHOOLBUS);
};

void() misc_vehicle_gtcar =
{
	Vehicles_Precache ();
	self.classname = "misc_vehicle_gtcar";
	Veh_InitEntity (self, VEH_GTCAR);
};

void() misc_vehicle_golfcart =
{
	Vehicles_Precache ();
	self.classname = "misc_vehicle_golfcart";
	Veh_InitEntity (self, VEH_GOLFCART);
};

void() misc_vehicle_tuktuk =
{
	Vehicles_Precache ();
	self.classname = "misc_vehicle_tuktuk";
	Veh_InitEntity (self, VEH_TUKTUK);
};

void() misc_gokart_1 =
{
	Vehicles_Precache ();
	self.classname = "misc_gokart_1";
	Veh_InitEntity (self, VEH_GOKART_1);
};

void() misc_gokart_2 =
{
	Vehicles_Precache ();
	self.classname = "misc_gokart_2";
	Veh_InitEntity (self, VEH_GOKART_2);
};

void() misc_gokart_3 =
{
	Vehicles_Precache ();
	self.classname = "misc_gokart_3";
	Veh_InitEntity (self, VEH_GOKART_3);
};

void() misc_gokart_4 =
{
	Vehicles_Precache ();
	self.classname = "misc_gokart_4";
	Veh_InitEntity (self, VEH_GOKART_4);
};

void() misc_gokart_5 =
{
	Vehicles_Precache ();
	self.classname = "misc_gokart_5";
	Veh_InitEntity (self, VEH_GOKART_5);
};

void() misc_gokart_6 =
{
	Vehicles_Precache ();
	self.classname = "misc_gokart_6";
	Veh_InitEntity (self, VEH_GOKART_6);
};

void() misc_gokart =
{
	local float k;

	Vehicles_Precache ();
	k = floor (self.cnt);
	if (k < 1 || k > 6)
	{
		gokart_spawn_cycle = gokart_spawn_cycle + 1;
		if (gokart_spawn_cycle > 6)
			gokart_spawn_cycle = 1;
		k = gokart_spawn_cycle;
	}
	self.classname = "misc_gokart";
	Veh_InitEntity (self, VEH_GOKART_1 + k - 1);
};

void() misc_vehicle =
{
	local float k;

	Vehicles_Precache ();
	k = floor (self.cnt);
	if (k < 1 || k > VEH_GOKART_6)
	{
		k = floor (fabs (self.origin_x * 0.013 + self.origin_y * 0.017)) + 1;
		k = k - 4 * floor ((k - 1) / 4);
	}
	Veh_InitEntity (self, k);
};

// ---------------------------------------------------------------- Dynamic Spawn / Test Impulses (81..85)

void() Veh_PruneTempWrecks =
{
	local entity e, oldest;
	local float n;

	n = 0;
	oldest = world;
	e = nextent (world);
	while (e != world)
	{
		if (e.veh_temp && e.veh_driver == world)
		{
			n = n + 1;
			if (oldest == world || (e.veh_state == VEH_STATE_WRECK && oldest.veh_state != VEH_STATE_WRECK))
				oldest = e;
		}
		e = nextent (e);
	}
	if (n > 14 && oldest != world)
	{
		Veh_FreeClips (oldest);		// else its walk-in boxes stay as invisible walls, owned by a freed (reused) edict
		if (oldest.veh_cament != world)
			remove (oldest.veh_cament);
		remove (oldest);
	}
};

entity(float kind, vector org, float yaw_deg) Veh_SpawnDynamic =
{
	local entity v;

	Veh_PruneTempWrecks ();
	v = spawn ();
	if (Veh_IsKart (kind))
		v.classname = "misc_gokart";
	else
		v.classname = "misc_vehicle";
	v.veh_temp = TRUE;
	v.angles = '0 0 0';
	v.angles_y = Veh_NormYaw (yaw_deg);
	setorigin (v, org);
	Veh_InitEntity (v, kind);
	return v;
};

void() Vehicles_Impulse =
{
	local vector fwd, rgt, base;
	local float yaw_car, k;

	Veh_NearPrompt ();
	JohnBird_Impulse ();
	RocketRider_Impulse ();
	EricCannon_Impulse ();
	MMTank_Impulse ();
	BakoDestruct_Impulse ();
	if (!self.impulse)
		return;
	// 86 = get in (when standing beside Eric Deason Cannon, Mega Man Tank, Classic Quake Rocket, perched Winged John, or van driver's seat), 87 = camera,
	// 88 = a running van right here, nose the way you face, 89 = (sv_cheats) into the cab of the nearest van
	if (self.impulse == 86)
	{
		self.impulse = 0;
		if (!EricCannon_TryEnterKey ())
			if (!MMTank_TryEnterKey ())
				if (!RocketRider_TryEnterKey ())
					if (!JohnBird_TryEnterKey ())
						Veh_EnterKey ();
		return;
	}
	if (self.impulse == 87)
	{
		self.impulse = 0;
		return;
	}
	if (self.impulse == 88 && autocvar_sv_cheats)	// test aid: unlimited vans would overflow the edicts
	{
		self.impulse = 0;
		Veh_SpawnAndEnter ();
		return;
	}
	if (self.impulse == 89)
	{
		self.impulse = 0;
		Veh_TestSeat ();
		return;
	}
	if (self.impulse == 90)
	{
		self.impulse = 0;
		Veh_TestTarget ();
		return;
	}
	if (!autocvar_sv_cheats)	// 81-85, 91-95 & 136-138 spawn vehicles out of thin air: sv_cheats only
		return;
	if (self.impulse == 136)
	{
		self.impulse = 0;
		GK_SpawnAndEnter ();
		return;
	}
	if (self.impulse == 137)
	{
		self.impulse = 0;
		GK_SpawnAll6 ();
		return;
	}
	if (self.impulse == 138)
	{
		self.impulse = 0;
		GK_SpawnNext ();
		return;
	}
	if (!((self.impulse >= 81 && self.impulse <= 85) || (self.impulse >= 91 && self.impulse <= 95)))
		return;

	makevectors ('0 1 0' * self.v_angle_y);
	fwd = v_forward;
	rgt = v_right;
	yaw_car = Veh_NormYaw (self.v_angle_y + 90);

	if (self.impulse >= 81 && self.impulse <= 84)
	{
		k = self.impulse - 80;
		base = self.origin + fwd * 195 + '0 0 16';
		Veh_SpawnDynamic (k, base, yaw_car);
		if (k == VEH_TRUCK)
			sprint (self, "Spawned 4x4 Pickup Truck\n");
		else if (k == VEH_SEDAN)
			sprint (self, "Spawned 90s Street Sedan\n");
		else if (k == VEH_VAN)
			sprint (self, "Spawned White Econoline Cargo Van\n");
		else
			sprint (self, "Spawned 2000s Tuner Sport Coupe\n");
		self.impulse = 0;
		return;
	}

	if (self.impulse == 85)
	{
		// Spawn all 4 unique vehicles lined up side-by-side ahead of player!
		base = self.origin + fwd * 260 + '0 0 16';
		Veh_SpawnDynamic (VEH_TRUCK, base - rgt * 195, self.v_angle_y + 180);
		Veh_SpawnDynamic (VEH_SEDAN, base - rgt * 65, self.v_angle_y + 180);
		Veh_SpawnDynamic (VEH_VAN,   base + rgt * 65, self.v_angle_y + 180);
		Veh_SpawnDynamic (VEH_COUPE, base + rgt * 195, self.v_angle_y + 180);
		sprint (self, "Spawned all 4 unique vehicles!\n");
		self.impulse = 0;
		return;
	}

	if (self.impulse >= 91 && self.impulse <= 93)
	{
		k = self.impulse - 86;		// 91 -> 5 (HDTRUCK), 92 -> 6 (SCHOOLBUS), 93 -> 7 (GTCAR)
		base = self.origin + fwd * 235 + '0 0 16';
		Veh_SpawnDynamic (k, base, yaw_car);
		if (k == VEH_HDTRUCK)
			sprint (self, "Spawned Heavy-Duty Diesel Dually Rig!\n");
		else if (k == VEH_SCHOOLBUS)
			sprint (self, "Spawned Yellow Type-C School Bus!\n");
		else
			sprint (self, "Spawned V8 Street Muscle Fastback Car!\n");
		self.impulse = 0;
		return;
	}

	if (self.impulse == 94)
	{
		// Spawn all 3 wild-explosion vehicles lined up ahead of player!
		base = self.origin + fwd * 300 + '0 0 16';
		Veh_SpawnDynamic (VEH_HDTRUCK,   base - rgt * 165, self.v_angle_y + 180);
		Veh_SpawnDynamic (VEH_SCHOOLBUS, base,             self.v_angle_y + 180);
		Veh_SpawnDynamic (VEH_GTCAR,     base + rgt * 165, self.v_angle_y + 180);
		sprint (self, "Spawned all 3 WILD vehicles (Diesel Rig, School Bus, V8 Muscle Car)!\n");
		self.impulse = 0;
		return;
	}

	if (self.impulse == 95)
	{
		base = self.origin + fwd * 185 + '0 0 16';
		Veh_SpawnDynamic (VEH_TUKTUK, base, yaw_car);
		sprint (self, "Spawned Bangkok Tuk-Tuk!\n");
		self.impulse = 0;
	}
};
