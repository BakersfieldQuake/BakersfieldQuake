/*
==============================================================================
tim_cine.qc — Soi 6 In-Engine Cinematic Director for TimBlackburn
Activated ONLY when `tim_cine 1` is set before loading `map soi6`.
  Beat 1 (0..5.0s) : Tim walks East down center of Soi 6 holding a beer
  Beat 2 (5.0..10.2s): 20 Soi 6 girls rush out from bars on both sides and surround him
  Beat 3 (10.2..16.5s): Tim panics & sprints down Soi 6 while camera zooms out & up
==============================================================================
*/

var float autocvar_tim_cine = 0;
// soi6_cine_ang / soi6_cine_rad declared in soi6_npcs.qc

void(entity tim, float side_sgn, float want_n, float ang_start, float ang_step) Tim_CinePickSide =
{
	local entity e, best;
	local float picked, d, best_d, ring_ang;

	picked = 0;
	while (picked < want_n)
	{
		best = world;
		best_d = 99999;
		e = find (world, classname, "npc_soi6");
		while (e)
		{
			if (e.soi6_state != SOI6_DEAD && e.soi6_state != SOI6_GIB && e.soi6_target != tim)
			{
				if (e.origin_y * side_sgn > 10 && fabs (e.origin_z - tim.origin_z) < 64)
				{
					d = vlen (e.origin - tim.origin);
					if (d < 720 && d < best_d)
					{
						best_d = d;
						best = e;
					}
				}
			}
			e = find (e, classname, "npc_soi6");
		}
		if (!best)
			return;

		ring_ang = ang_start + picked * ang_step;
		best.soi6_target = tim;
		best.soi6_state_t = time + 18.0;
		best.soi6_cine_ang = ring_ang;
		if ((picked - 2 * floor (picked / 2)) == 0)
			best.soi6_cine_rad = 52;
		else
			best.soi6_cine_rad = 78;
		best.soi6_talk_t = time + 0.15 + random () * 1.4;
		Soi6_SetState (best, SOI6_SWARM);
		best.nextthink = time + 0.02;
		picked = picked + 1;
	}
};

void(entity tim) Tim_CineSummonGirls =
{
	// Balanced 360-deg ring: 10 North bar girls (18..162 deg) + 10 South bar girls (198..342 deg)
	Tim_CinePickSide (tim, 1, 10, 18, 16);
	Tim_CinePickSide (tim, -1, 10, 198, 16);
};

void(entity tim) Tim_CineSwitchToChase =
{
	local entity e;
	local float idx, ring_ang;

	idx = 0;
	e = find (world, classname, "npc_soi6");
	while (e)
	{
		if (e.soi6_target == tim && e.soi6_state == SOI6_SWARM)
		{
			// Pack trails behind Tim (-X hemisphere: 122..238 deg) so they visibly chase him
			ring_ang = 122 + (idx - 10 * floor (idx / 10)) * 12;
			e.soi6_cine_ang = ring_ang;
			e.soi6_cine_rad = 64 + 26 * floor (idx / 10);
			idx = idx + 1;
		}
		e = find (e, classname, "npc_soi6");
	}
};

entity() Tim_CineFindPlayer =
{
	local entity p;
	p = find (world, classname, "player");
	while (p)
	{
		if (p.ishuman == 1)
			return p;
		p = find (p, classname, "player");
	}
	return world;
};

// the cinematic is over (or tim_cine was switched off): the locked player gets a normal spawn back (movetype, health,
// model, view), beer_stay / beer_speed go back to what they were (they are saved cvars and outlived the map), and the
// director removes itself
void() Tim_CineEnd =
{
	local entity p, oself, g;

	if (self.cnt > 0)
	{
		cvar_set ("beer_stay", self.netname);
		cvar_set ("beer_speed", self.message);
		strunzone (self.netname);
		strunzone (self.message);
	}
	if (tim_soi6 != world && !bm_wasfreed (tim_soi6) && tim_soi6.health > 0)
		tim_soi6.takedamage = DAMAGE_AIM;
	g = find (world, classname, "npc_soi6");
	while (g)
	{
		if (g.soi6_cine_rad > 0)
			g.soi6_cine_rad = 0;
		g = find (g, classname, "npc_soi6");
	}
	p = self.enemy;
	if (self.cnt > 0 && p && !bm_wasfreed (p) && p.classname == "player")		// cnt > 0: the player really was locked
	{
		oself = self;
		self = p;
		Veh_ClientGone ();
		setspawnparms (self);
		PutClientInServer ();
		self = oself;
	}
	print ("Tim_CineEnd: Soi 6 cinematic finished.\n");
	remove (self);
};

void() Tim_CineThink =
{
	local entity p, tim;
	local vector desired_cam, desired_focus, dir, ang;
	local float t, u, s, orbit_yaw, rad, h, lerp_k;

	self.nextthink = time + 0.016666;
	if (!autocvar_tim_cine || (self.cnt > 0 && time - self.ltime >= 16.5))
	{
		Tim_CineEnd ();
		return;
	}

	// keep the same player locked (the one restored at the end); pick a new one only if they left
	p = self.enemy;
	if (!p || bm_wasfreed (p) || p.classname != "player" || p.ishuman != 1)
		p = Tim_CineFindPlayer ();
	self.enemy = p;
	tim = tim_soi6;
	if (!p || !tim || tim == world || bm_wasfreed (tim))
		return;
	if (p.health <= 0 || p.deadflag != 0 || p.bm_obs || Veh_Driving (p) || Veh_Riding (p))
		return;

	// Lock human player into silent noclip camera observer
	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.takedamage = DAMAGE_NO;
	p.flags = p.flags | FL_NOTARGET;
	p.view_ofs = '0 0 0';
	p.modelindex = 0;
	p.weaponmodel = "";
	p.health = 999;

	if (self.cnt == 0)
	{
		self.cnt = 1;
		self.ltime = time;
		self.netname = strzone (cvar_string ("beer_stay"));		// restored by Tim_CineEnd
		self.message = strzone (cvar_string ("beer_speed"));
		cvar_set ("beer_stay", "0");
		cvar_set ("beer_speed", "76");
		tim.beer_soi6 = 0;
		tim.beer_dir = 0;
		tim.ideal_yaw = 0;
		tim.angles_y = 0;
		tim.beer_state = 0;
		tim.beer_state_end = time + 6.0;
		tim.beer_steer_t = time + 6.0;

		self.pos1 = tim.origin + '142 -48 36';
		self.pos2 = tim.origin + '0 0 34';
	}

	t = time - self.ltime;

	if (t < 4.5)
	{
		// Beat 1: Tim casually walks East down neon Soi 6
		tim.beer_state = 0;
		tim.beer_state_end = time + 2.0;
		tim.beer_steer_t = time + 2.0;
		tim.ideal_yaw = 0;
		tim.angles_y = 0;

		u = t / 4.5;
		s = u * u * (3 - 2 * u);
		desired_focus = tim.origin + '0 0 34';
		desired_cam = tim.origin + ('148 -46 34' * (1 - s)) + ('128 38 40' * s);
		lerp_k = 0.24;
	}
	else if (t < 9.5)
	{
		// Beat 2: Tim stops to sip beer; 20 bar girls rush in & surround him
		if (self.cnt == 1)
		{
			self.cnt = 2;
			cvar_set ("beer_stay", "1");
			tim.beer_state = 1;
			tim.beer_state_end = time + 8.0;
			sound (tim, CHAN_VOICE, "beerguy/sip_ahh.wav", 0.9, ATTN_NORM);
			Tim_CineSummonGirls (tim);
		}
		tim.beer_state = 1;
		tim.beer_state_end = time + 2.0;

		u = (t - 4.5) / 5.0;
		s = u * u * (3 - 2 * u);
		// Elliptical orbit clamped to street corridor (|Y| <= 86) so sidewalk pillars never block view
		orbit_yaw = 16 + s * 158;
		rad = 136 + s * 44;
		h = 40 + s * 36;
		makevectors ('0 1 0' * orbit_yaw);
		desired_focus = tim.origin + '0 0 30';
		desired_cam = tim.origin + ('1 0 0' * (v_forward_x * rad)) + ('0 1 0' * (v_forward_y * 84)) + ('0 0 1' * h);
		lerp_k = 0.16;
	}
	else
	{
		// Beat 3: Tim panics & sprints East down Soi 6 with girls chasing; camera zooms out & up
		if (self.cnt == 2)
		{
			self.cnt = 3;
			sound (tim, CHAN_VOICE, "beerguy/pain_beer.wav", 1.0, ATTN_NORM);
			cvar_set ("beer_stay", "0");
			cvar_set ("beer_speed", "165");
			tim.beer_state = 2;
			tim.beer_state_end = time + 12.0;
			tim.beer_steer_t = time + 12.0;
			tim.ideal_yaw = 0;
			tim.angles_y = 0;
		}
		if (self.cnt == 3 && t >= 9.85)
		{
			self.cnt = 4;
			Tim_CineSwitchToChase (tim);
		}

		tim.beer_state = 2;
		tim.beer_state_end = time + 2.0;
		tim.beer_steer_t = time + 2.0;
		tim.ideal_yaw = 0;
		tim.angles_y = 0;

		u = (t - 9.5) / 5.5;
		if (u > 1)
			u = 1;
		s = u * u * (3 - 2 * u);

		orbit_yaw = 174 + s * 8;
		rad = 180 + s * 420;
		h = 76 + s * 215;
		makevectors ('0 1 0' * orbit_yaw);
		desired_focus = tim.origin + ('-75 0 26' * (0.45 + 0.55 * s));
		desired_cam = tim.origin + ('1 0 0' * (v_forward_x * rad)) + ('0 1 0' * (v_forward_y * 80)) + ('0 0 1' * h);
		lerp_k = 0.14;
	}

	self.pos1 = self.pos1 + (desired_cam - self.pos1) * lerp_k;
	self.pos2 = self.pos2 + (desired_focus - self.pos2) * lerp_k;

	// Never clip inside bar awnings/roofs during wide pullback
	traceline (self.pos2, self.pos1, TRUE, p);
	if (trace_fraction < 1.0)
		self.pos1 = trace_endpos + trace_plane_normal * 10;

	setorigin (p, self.pos1);
	dir = self.pos2 - self.pos1;
	ang = vectoangles (dir);
	ang_x = -ang_x;
	ang_z = 0;
	p.angles = ang;
	p.v_angle = ang;
	p.fixangle = TRUE;
};

void() Tim_CineStart =
{
	local entity dir, oself;

	if (!autocvar_tim_cine)
		return;
	if (!tim_soi6 || tim_soi6 == world)
		return;

	oself = self;
	self = tim_soi6;
	setorigin (self, '4780 0 32');
	droptofloor ();
	self.beer_soi6 = 0;
	self.beer_dir = 0;
	self.ideal_yaw = 0;
	self.angles_y = 0;
	self.beer_stuck = 0;
	self.beer_state = 0;
	self.beer_state_end = time + 10.0;
	self.beer_steer_t = time + 10.0;
	self.takedamage = DAMAGE_NO;
	self = oself;

	dir = spawn ();
	dir.classname = "tim_cine_dir";
	dir.cnt = 0;
	dir.think = Tim_CineThink;
	dir.nextthink = time + 0.02;
	print ("Tim_CineStart: Soi 6 cinematic director active.\n");
};
