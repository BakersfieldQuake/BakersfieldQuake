/*
================
THE JETPACK (see jetpack_defs.qc for the rules and numbers)

Hooks (patch_jetpack_combat.py): item_armor2 calls Jetpack_ForArmor (a pickup beside every yellow armor),
W_WeaponFrame runs Jetpack_Frame, PutClientInServer runs Jetpack_Spawn.
================
*/

void() Jetpack_Precache =
{
	if (jetpack_precached)
		return;
	jetpack_precached = TRUE;
	precache_model ("progs/jetpack.md3");
	precache_sound ("jetpack/swoosh.wav");
	precache_sound ("jetpack/floating.wav");		// funny/imfloating.wav ("I'm floating"), quiet, smoothed copy (build_jetpack_assets.py)
	precache_sound ("items/armor1.wav");
	precache_sound ("items/itembk2.wav");
	jp_fx_fire = particleeffectnum ("jp_fire");		// effectinfo.txt, from jetpack_effectinfo.txt
	jp_fx_smoke = particleeffectnum ("jp_smoke");
	jp_fx_dust = particleeffectnum ("jp_dust");
	jp_fx_burst = particleeffectnum ("jp_burst");
	jp_fx_blaze = particleeffectnum ("jp_blaze");		// the long streaming flame at speed
	jp_fx_glow = particleeffectnum ("jp_glow");
};

// ---------------------------------------------------------------- the pickup

void() Jetpack_Spin =
{
	local float f;

	f = floor (time * 10);		// idle animation: frames 8-15 of progs/jetpack.md3 (0-7 are the thrust)
	self.frame = 8 + (f - 8 * floor (f / 8));
	self.nextthink = time + 0.1;
	self.think = Jetpack_Spin;
};

void() Jetpack_Regen =
{
	self.model = self.mdl;
	self.solid = SOLID_TRIGGER;
	self.movetype = MOVETYPE_NOCLIP;
	self.avelocity = '0 120 0';
	setorigin (self, self.oldorigin);
	sound (self, CHAN_VOICE, "items/itembk2.wav", 1, ATTN_NORM);
	Jetpack_Spin ();
};

void() Jetpack_Touch =
{
	if (other.classname != "player" || other.health <= 0)
		return;
	if (other.jp_fuel >= autocvar_jp_fuel)
		return;		// tank already full: leave it for someone else
	other.jp_fuel = autocvar_jp_fuel;
	other.jp_low = FALSE;
	dprint ("jetpack picked up\n");
	sound (other, CHAN_ITEM, "items/armor1.wav", 1, ATTN_NORM);
	stuffcmd (other, "bf\n");
	if (!other.jp_hint_shown)
	{
		other.jp_hint_shown = TRUE;
		centerprint (other, "Jetpack: double-tap SPACE in air (or press J) to fly!");
	}
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.avelocity = '0 0 0';
	self.model = string_null;
	self.think = Jetpack_Regen;
	self.nextthink = time + autocvar_jp_respawn;
};

// 0.5 s after the armor settled: put the jetpack on the floor beside it, on the first side with room
void() Jetpack_Place =
{
	local entity armor;
	local float i, z0;
	local vector org, base;

	armor = self.jp_armor;
	base = armor.origin;
	self.scale = 3;		// the model is only 24 units tall at scale 1 (origin near its middle, bottom at -11); armor is 56
	setsize (self, '-26 -26 -46', '26 26 22');
	i = 0;
	while (i < 8)
	{
		makevectors ('0 1 0' * (i * 45));
		org = base + v_forward * 60 + '0 0 48';
		traceline (base + '0 0 20', org + '0 0 8', TRUE, armor);
		if (trace_fraction == 1)
		{
			tracebox (org, '-26 -26 -46', '26 26 22', org, TRUE, self);
			if (!trace_startsolid && !trace_allsolid)
			{
				setorigin (self, org);
				z0 = org_z;
				if (droptofloor () && z0 - self.origin_z < 48)
				{
					self.mdl = self.model;
					self.solid = SOLID_TRIGGER;
					self.movetype = MOVETYPE_NOCLIP;
					self.avelocity = '0 120 0';
					self.oldorigin = self.origin;		// the bob's centre
					self.touch = Jetpack_Touch;
					dprint ("jetpack placed at ");
					dprint (vtos (self.origin));
					dprint ("\n");
					Jetpack_Spin ();
					return;
				}
			}
		}
		i = i + 1;
	}
	dprint ("no room for a jetpack beside the armor at ");
	dprint (vtos (base));
	dprint ("\n");
	remove (self);
};

// Standalone map entity: item_jetpack
void() item_jetpack =
{
	Jetpack_Precache ();
	self.classname = "item_jetpack";
	self.scale = 3;
	setmodel (self, "progs/jetpack.md3");
	setsize (self, '-26 -26 -46', '26 26 22');
	setorigin (self, self.origin + '0 0 24');
	droptofloor ();
	self.mdl = self.model;
	self.solid = SOLID_TRIGGER;
	self.movetype = MOVETYPE_NOCLIP;
	self.avelocity = '0 120 0';
	self.oldorigin = self.origin;
	self.touch = Jetpack_Touch;
	Jetpack_Spin ();
};

// item_armor2 calls this: spawn the jetpack that stands beside it
void(entity armor) Jetpack_ForArmor =
{
	local entity j;

	Jetpack_Precache ();
	j = spawn ();
	j.classname = "item_jetpack";
	j.jp_armor = armor;
	setorigin (j, armor.origin);
	setmodel (j, "progs/jetpack.md3");
	j.solid = SOLID_NOT;
	j.movetype = MOVETYPE_NONE;
	j.nextthink = time + 0.5;
	j.think = Jetpack_Place;
};

// ---------------------------------------------------------------- the pack

void() Jetpack_Off =
{
	if (self.jp_on)
	{
		self.jp_on = FALSE;
		dprint ("jetpack off at ");
		dprint (vtos (self.origin));
		dprint (" fuel=");
		dprint (ftos (self.jp_fuel));
		dprint ("\n");
		sound (self, CHAN_ITEM, "misc/null.wav", 1, ATTN_NORM);		// cuts the swoosh
	}
	self.gravity = 1;
	self.jp_boost = 0;
	self.jp_fast = 0;
};

void() Jetpack_On =
{
	self.jp_on = TRUE;
	dprint ("jetpack on at ");
	dprint (vtos (self.origin));
	dprint ("\n");
	self.jp_t0 = time;
	self.jp_snd = 0;
	self.jp_boost = 0;
	self.jp_fast = 0;
	self.gravity = JP_LOWGRAV;
	pointparticles (jp_fx_burst, self.origin - '0 0 20', '0 0 0', 1);		// the flash as it lights
	if (time >= self.jp_voice)
	{
		sound (self, CHAN_VOICE, "jetpack/floating.wav", 0.4, ATTN_NORM);		// "I'm floating": one channel, quiet and smooth (2026-11-02, was 1.0 on two channels)
		self.jp_voice = time + 4;
	}
};

void() Jetpack_Spawn =
{
	self.jp_fuel = 0;
	self.jp_st_fuel = 0;
	self.jp_on = FALSE;
	self.jp_jump = FALSE;
	self.jp_air_tap = 0;
	self.jp_low = FALSE;
	self.gravity = 1;
};

// sv_cheats test: impulse 73 stands you 100 units from the first jetpack looking at it, 74 puts you on it
void() Jetpack_TestTeleport =
{
	local entity j;
	local vector d;

	if (!cvar ("sv_cheats"))
		return;
	if (self.impulse == 76)
	{
		// the middle of an open map, facing +x: room for the chase camera behind you
		setorigin (self, '0 0 40');
		self.angles = '0 0 0';
		self.fixangle = TRUE;
		self.velocity = '0 0 0';
		return;
	}
	if (self.impulse == 75)
	{
		// start has no armor at all: a stand-in 200 units ahead, then the real Jetpack_ForArmor places a jetpack beside it
		makevectors ('0 1 0' * self.v_angle_y);
		j = spawn ();
		j.classname = "test_armor";
		setorigin (j, self.origin + v_forward * 200 - '0 0 24');
		Jetpack_ForArmor (j);
		jp_test = j;
		return;
	}
	j = find (world, classname, "item_jetpack");
	while (jp_test != world && j != world && j.jp_armor != jp_test)
		j = find (j, classname, "item_jetpack");		// the stand-in's, else just the first
	if (j == world)
		return;
	d = normalize (j.origin - j.jp_armor.origin);
	d_z = 0;
	if (self.impulse == 74)
		setorigin (self, j.origin + '0 0 8');
	else
	{
		jp_side = jp_side + 1;		// each press looks from the next side (sv_cheats test)
		if (jp_side > 3)
			jp_side = 0;
		makevectors ('0 1 0' * (jp_side * 90));
		d = v_forward * 64;
		d_z = 0;
		setorigin (self, j.origin + d + '0 0 24');
		self.angles = vectoangles ('0 0 0' - d);
		self.fixangle = TRUE;
	}
	self.velocity = '0 0 0';
};

// ---------------------------------------------------------------- the pack on your back, and its fire and smoke

// the pack other people see on your back (and you in chase view): idle while you carry it, thrust frames while it burns
void() Jetpack_WornThink =
{
	local entity p;
	local float f;

	p = self.owner;
	if (p.jp_worn != self || p.classname != "player" || p.health <= 0 || p.jp_fuel <= 0)
	{
		if (p.jp_worn == self)
			p.jp_worn = world;
		remove (self);
		return;
	}
	self.nextthink = time + 0.05;
	f = floor (time * 16);
	if (p.jp_on)
		self.frame = f - 8 * floor (f / 8);				// frames 0-7: thrust, with the flame plumes
	else
		self.frame = 8 + f - 8 * floor (f / 8);		// frames 8-15: standby
};

void() Jetpack_WornFrame =
{
	local entity e;

	if (self.health <= 0 || self.jp_fuel <= 0 || (self.items & IT_INVISIBILITY))
	{
		if (self.jp_worn)
		{
			remove (self.jp_worn);
			self.jp_worn = world;
		}
		return;
	}
	if (self.jp_worn)
		return;
	e = spawn ();
	e.classname = "jp_worn";
	e.owner = self;
	e.movetype = MOVETYPE_NONE;
	e.solid = SOLID_NOT;
	e.exteriormodeltoclient = self;		// not drawn in your own first-person view (it would hang in your face), but others and your chase view see it
	e.scale = JP_WORN_SCALE;
	setattachment (e, self, "");
	e.origin = JP_WORN_OFS;
	e.angles = '0 0 0';
	e.think = Jetpack_WornThink;
	e.nextthink = time + 0.05;
	setmodel (e, "progs/jetpack.md3");
	self.jp_worn = e;
};

// fire and smoke out of both nozzles every 0.04 s, a dust blast off the floor when you are low
void(float climbing) Jetpack_Exhaust =
{
	local vector org, dust, o;
	local float yo, f, n, i, gap;

	if (time < self.jp_flame)
		return;
	self.jp_flame = time + 0.13;		// sent to every client: 15 effects each 0.065 s was about 3.7 KB/s per flier
	makevectors ('0 1 0' * self.v_angle_y);
	yo = JP_NOZZLE_Y;
	org = self.origin + v_forward * JP_NOZZLE_X + v_up * JP_NOZZLE_Z;
	pointparticles (jp_fx_fire, org + v_right * yo, '0 0 0', 1);
	pointparticles (jp_fx_fire, org - v_right * yo, '0 0 0', 1);
	if (time >= self.jp_puff)
	{
		self.jp_puff = time + 0.12 - 0.08 * self.jp_fast;		// a thin wisp, a third as often as the flame (more at speed)
		pointparticles (jp_fx_smoke, org + v_right * yo, '0 0 0', 1);
		pointparticles (jp_fx_smoke, org - v_right * yo, '0 0 0', 1);
	}
	if (climbing)
	{
		pointparticles (jp_fx_fire, org + v_right * yo, '0 0 0', 1);		// a bigger plume while you climb
		pointparticles (jp_fx_fire, org - v_right * yo, '0 0 0', 1);
	}
	f = self.jp_fast;
	if (f > 0.04)
	{
		// the faster you go the more flame: more plumes per puff, and they are strung along the path flown since the last puff so a
		// fast pack leaves a continuous streak instead of one blob every 0.04 s (1700 units/s is 68 units between puffs)
		n = 1 + floor (f * 3);
		i = 0;
		while (i < n)
		{
			o = self.velocity * (0 - 0.13 * i / n);
			gap = 0 - 1;
			pointparticles (jp_fx_blaze, org + o + v_right * yo, self.velocity * gap, 1);
			pointparticles (jp_fx_blaze, org + o - v_right * yo, self.velocity * gap, 1);
			i = i + 1;
		}
		if (f > 0.25)
		{
			pointparticles (jp_fx_glow, org + v_right * yo, '0 0 0', 1);
			pointparticles (jp_fx_glow, org - v_right * yo, '0 0 0', 1);
		}
	}
	traceline (org, org - '0 0 150', TRUE, self);
	if (trace_fraction < 1)
	{
		dust = trace_endpos + '0 0 6';
		pointparticles (jp_fx_dust, dust, '0 0 0', 1);
	}
	makevectors (self.v_angle);		// W_WeaponFrame goes on to use v_forward / v_up
};

// every frame from W_WeaponFrame: switch it on and off, fly
void() Jetpack_Fly =
{
	local float up, vz, tgt, dv, mx, my, k, spd;
	local vector wish, hv;

	// flying Winged John, driving the van or steering a Rob Dob head: SPACE is theirs (John's climb key), and John clears
	// FL_ONGROUND every frame, so it lit the pack (fuel, flames, voice) from inside the bird
	if (self.jb_vehicle != world || self.veh_van != world || self.veh_ride != world || self.fd_head != world || self.ec_cannon_ent != world || self.ec_watch_until > time)	// + the Eric Deason Cannon: it clears FL_ONGROUND every frame too, so the pack lit inside it and burned the tank
	{
		if (self.jp_on)
			Jetpack_Off ();
		self.jp_jump = self.button2;
		return;
	}
	if (self.health <= 0)
	{
		Jetpack_Off ();
		self.jp_fuel = 0;
		return;
	}
	if (self.flags & FL_ONGROUND)
		self.jp_air_tap = 0;
	up = self.button2;
	if (self.impulse >= 73 && self.impulse <= 76)
	{
		Jetpack_TestTeleport ();
		self.impulse = 0;
	}
	if (self.impulse == 71)
	{
		self.impulse = 0;
		if (self.jp_on)
			Jetpack_Off ();
		else if (self.jp_fuel > 0)
			Jetpack_On ();
		else
			sprint (self, "You have no jetpack fuel.\n");
	}
	else if (up && !self.jp_jump && !self.jp_on && self.jp_fuel > 0 && !(self.flags & FL_ONGROUND) && self.waterlevel < 2)
	{
		// Require a deliberate double-tap of SPACE in mid-air so bunnyhops, rocket-jumps & SkyPads don't waste fuel!
		if (time - self.jp_air_tap < JP_DTAP)
		{
			Jetpack_On ();
			self.jp_air_tap = 0;
			self.jp_tap = 0;
		}
		else
			self.jp_air_tap = time;
	}
	else if (up && !self.jp_jump && self.jp_on)
	{
		if (time - self.jp_tap < JP_DTAP)
		{
			Jetpack_Off ();		// double tap: out of it, you fall
			self.jp_jump = up;
			return;
		}
		self.jp_tap = time;
	}
	self.jp_jump = up;
	if (!self.jp_on)
		return;

	if (self.waterlevel >= 2 || (!up && (self.flags & FL_ONGROUND) && time > self.jp_t0 + 0.6))
	{
		Jetpack_Off ();		// landed (or fell in the water)
		return;
	}

	// steer: Quake's air control can't do it (it caps your push at about 30), so while the pack burns it flies you where you push
	// at JP_SPEED, and slows you to a hover when you let go
	makevectors ('0 1 0' * self.v_angle_y);
	mx = self.movement_x / 200;
	my = self.movement_y / 200;
	if (mx > 1)
		mx = 1;
	if (mx < -1)
		mx = -1;
	if (my > 1)
		my = 1;
	if (my < -1)
		my = -1;
	k = self.v_angle_x;		// looking down or up: less of the forward push goes sideways (the rest climbs or dives, below)
	if (k > 180)
		k = k - 360;
	k = cos (k * 0.0174533);
	wish = v_forward * mx * k + v_right * my;
	if (vlen (wish) > 1)
		wish = normalize (wish);

	// hold forward and the pack winds up: slowly at first, then faster and faster (jp_boost is the timer, jp_fast the eased 0-1)
	hv = self.velocity;
	hv_z = 0;
	if (mx > 0)
	{
		self.jp_boost = self.jp_boost + frametime * mx / JP_RAMP;
		if (self.jp_boost > 0.2 && vlen (hv) < 0.3 * (JP_SPEED + (JP_MAXSPEED - JP_SPEED) * self.jp_fast) * vlen (wish) && time > self.jp_t0 + 0.5)
			self.jp_boost = self.jp_boost - frametime * 4;		// flew into a wall: lose it
	}
	else
		self.jp_boost = self.jp_boost - frametime / JP_COAST;
	if (self.jp_boost > 1)
		self.jp_boost = 1;
	if (self.jp_boost < 0)
		self.jp_boost = 0;
	self.jp_fast = self.jp_boost * self.jp_boost;
	spd = JP_SPEED + (JP_MAXSPEED - JP_SPEED) * self.jp_fast;
	wish = wish * spd;
	k = frametime * JP_BRAKE;
	if (mx != 0 || my != 0)
		k = frametime * JP_STEER;
	if (k > 1)
		k = 1;
	self.velocity_x = self.velocity_x + (wish_x - self.velocity_x) * k;
	self.velocity_y = self.velocity_y + (wish_y - self.velocity_y) * k;
	makevectors (self.v_angle);		// W_WeaponFrame goes on to use v_forward / v_up

	// climb on jump, sink on crouch; moving forward or back follows where you look (look down, go down);
	// with no keys held you slowly sink
	tgt = 0;
	if (mx != 0)
	{
		k = self.v_angle_x;
		if (k > 180)
			k = k - 360;
		k = sin (k * 0.0174533);		// a variant builtin: keep it in a local
		tgt = 0 - k * mx * spd;
	}
	else if (my == 0)
		tgt = 0 - JP_SINK;
	if (up)
		tgt = JP_CLIMB;
	if (self.movement_z < 0)
		tgt = tgt - JP_DOWN;
	vz = self.velocity_z;
	dv = JP_ACCEL * frametime * spd / JP_SPEED;
	if (vz < tgt - dv)
		vz = vz + dv;
	else if (vz > tgt + dv)
		vz = vz - dv;
	else
		vz = tgt;
	self.velocity_z = vz;
	if (vz > 0)
		self.flags = self.flags - (self.flags & FL_ONGROUND);

	// fuel: 1 a second climbing, autocvar_jp_hover a second hovering
	if (up)
		self.jp_fuel = self.jp_fuel - frametime;
	else
		self.jp_fuel = self.jp_fuel - frametime * autocvar_jp_hover;
	if (self.jp_fuel <= 5 && !self.jp_low)
		self.jp_low = TRUE;
	if (self.jp_fuel <= 0)
	{
		self.jp_fuel = 0;
		Jetpack_Off ();
		return;
	}

	// the engine sound (a 2 s seamless loop, restarted on the beat) and the fire and smoke
	if (up != self.jp_sndup)
	{
		self.jp_sndup = up;
		self.jp_snd = 0;		// restart at once when you start or stop climbing: the level and pitch change with it
	}
	if (time >= self.jp_snd)
	{
		self.jp_snd = time + 2;		// the loop is 2 s and seamless
		sound7 (self, CHAN_ITEM, "jetpack/swoosh.wav", 0.35 + 0.15 * up + 0.15 * self.jp_fast, ATTN_NORM, 100 + 18 * up + 30 * self.jp_fast);		// a clear but soft engine bed under the voice; higher when climbing
	}
	Jetpack_Exhaust (up);
};

// every frame from W_WeaponFrame
void() BK_Impulse;		// bklan_movers.qc: sv_cheats test impulses 77-78
void() NS_Test;			// netsend.qc: sv_cheats test impulse 80

void() Jetpack_Frame =
{
	if (self.impulse)
	{
		BK_Impulse ();
		NS_Test ();
	}
	Jetpack_Fly ();
	Jetpack_WornFrame ();
	if (self.ishuman == 1)
	{
		self.jp_st_fuel = ceil (self.jp_fuel * 10);		// the HUD's glass tank (csqc/bm_hud.qc, stats 66 and 67)
		self.jp_st_max = autocvar_jp_fuel * 10;
	}
};
