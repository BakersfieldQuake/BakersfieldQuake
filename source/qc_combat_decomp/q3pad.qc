/*
================
Q3 JUMP PADS (Bakersfield Downtown)

Playtest 1.76: the Downtown jump pads (bare chevron slabs) looked cheap; dress them like Quake 3 Arena pads. The map
is not touched: after the map's entities spawn, every pad gets a model from zz_jumppads.pk3 (built by
source/mm_tools/build_jumppads_pk3.py) laid over its slab:
  plain jump pads (trigger_push up to 92 wide)   progs/q3pad.md3, scaled to the trigger
  kart boost pads (trigger_push 118-160 wide)    progs/q3kart60/66/72.md3, turned to the push direction
  SkyPads (info_skypad)                          progs/q3skypad.md3 (blue), replacing the old turret ring and dome
Ladders and wind columns (tall, slow pushes) are left alone.
================
*/

float	Q3PAD_SIZE	= 74;		// the model's plate edge in units

float() Q3Pad_MapWanted =
{
	return (mapname == "bakersfielddowntown" || mapname == "bakersfielddowntown_lite");
};

entity(string mdl, vector org) Q3Pad_Spawn =
{
	local entity p;

	p = spawn ();
	p.classname = "q3pad_visual";
	p.solid = SOLID_NOT;
	p.movetype = MOVETYPE_NONE;
	setmodel (p, mdl);
	setsize (p, '0 0 0', '0 0 0');
	setorigin (p, org);
	return p;
};

// kart boost pad: a deck with a lead-in ramp and two rails, 4 units proud of the road
void(entity t, vector sz) Q3Pad_PlaceKart =
{
	local entity p;
	local vector org, dir;
	local float across, half;

	dir = t.movedir;
	dir_z = 0;
	across = (fabs (dir_x) > fabs (dir_y)) ? sz_y : sz_x;
	half = (across - 2) * 0.5;
	org = (t.absmin + t.absmax) * 0.5;
	org_z = t.absmin_z + 30;
	traceline (org, org - '0 0 96', TRUE, world);
	if (trace_startsolid || trace_fraction == 1)
		return;
	org_z = trace_endpos_z - 4;		// the model is built from road level; its deck is at 4
	if (half < 63)
		p = Q3Pad_Spawn ("progs/q3kart60.md3", org);
	else if (half < 69)
		p = Q3Pad_Spawn ("progs/q3kart66.md3", org);
	else
		p = Q3Pad_Spawn ("progs/q3kart72.md3", org);
	p.angles_y = vectoyaw (dir);
};

void() Q3Pad_DressSkyPads =
{
	local entity t, p, e;
	local vector org;
	local float n;

	// the old turret base, pavement ring and vortex dome go; the launch-direction beam and glow stay
	e = find (world, classname, "skypad_fx");
	while (e)
	{
		t = find (e, classname, "skypad_fx");
		if (e.model == "progs/turrbase.mdl" || e.model == "progs/ltg_aura.md3" || e.model == "progs/aura.md3")
			remove (e);
		e = t;
	}
	n = 0;
	t = find (world, classname, "info_skypad");
	while (t)
	{
		org = t.origin;
		traceline (org, org - '0 0 64', TRUE, world);
		if (!trace_startsolid && trace_fraction < 1)
			org_z = trace_endpos_z;
		else
			org_z = org_z - 26;
		p = Q3Pad_Spawn ("progs/q3skypad.md3", org + '0 0 0.4');
		p.scale = 80 / Q3PAD_SIZE;		// covers the 72-unit slab
		n = n + 1;
		t = find (t, classname, "info_skypad");
	}
	dprint ("q3pad: dressed ", ftos (n), " sky pads\n");
};

void() Q3Pad_Place =
{
	local entity t, p;
	local vector sz, org;
	local float n, nk, edge;

	n = 0;
	nk = 0;
	t = find (world, classname, "trigger_push");
	while (t)
	{
		sz = t.absmax - t.absmin;
		if (sz_x >= 50 && sz_x <= 92 && sz_y >= 50 && sz_y <= 92 && sz_z <= 90 && t.speed >= 60)
		{
			org = (t.absmin + t.absmax) * 0.5;
			org_z = t.absmin_z + 2;
			// sit on whatever is under the trigger (the slab top); the trigger usually starts right on it
			traceline (org, org - '0 0 96', TRUE, world);
			if (!trace_startsolid && trace_fraction < 1)
				org_z = trace_endpos_z;
			else
				org_z = t.absmin_z;
			p = Q3Pad_Spawn ("progs/q3pad.md3", org + '0 0 0.4');
			// the slab under a trigger is 6 units wider than it: overhang it a little so no old slab top shows
			edge = min (sz_x, sz_y) + 7;
			p.scale = edge / Q3PAD_SIZE;
			n = n + 1;
		}
		else if ((sz_x > 92 || sz_y > 92) && sz_x <= 160 && sz_y <= 160 && sz_z <= 90 && t.speed >= 60)
		{
			Q3Pad_PlaceKart (t, sz);
			nk = nk + 1;
		}
		t = find (t, classname, "trigger_push");
	}
	dprint ("q3pad: dressed ", ftos (n), " jump pads, ", ftos (nk), " kart pads\n");
	Q3Pad_DressSkyPads ();
	remove (self);
};

// From worldspawn: precache, then place once the map's entities exist
void() Q3Pad_Init =
{
	local entity e;

	if (!Q3Pad_MapWanted ())
		return;
	precache_model ("progs/q3pad.md3");
	precache_model ("progs/q3skypad.md3");
	precache_model ("progs/q3kart60.md3");
	precache_model ("progs/q3kart66.md3");
	precache_model ("progs/q3kart72.md3");
	e = spawn ();
	e.classname = "q3pad_placer";
	e.think = Q3Pad_Place;
	e.nextthink = time + 0.3;
};
