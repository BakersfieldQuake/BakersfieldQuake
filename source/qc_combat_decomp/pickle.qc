#ifndef COMBATPLUS
#define COMBATPLUS
#endif
// ---------------------------------------------------------------- 3. PICKLE SURPRISE (fun gun 3, impulse 63)
// Fire and your armored gauntlet brutally choke-squeezes, winds back, and whips a screaming turquoise Pickle Surprise
// (progs/pickle_throw.md3) violently across the screen out of your snapping open claw; the instant it slaps onto any
// surface (floor, wall or ceiling), it sticks flat as a 360-degree turquoise gold-studded 3D Pickle Surprise
// (progs/pickle_bomb.md3) with an 8-expression live animated face.
// The moment anyone who is not you (or on your team) touches or nears it, it swells up into the giant 3D-deforming
// Pickle Surprise Diva balloon (progs/pickle.md3: 36-frame base-planted S-curve inflatable mesh + 64 360-degree
// expressive skins across Sing, Cheeky Pucker, Bug-Eyes + Pink Tongue, and Full 16-Angle Giant Scream), shouts a very
// loud "pickle surprise" (sound/pickle/surprise.wav), swells like an over-pressurized balloon, and blows up big & green!
// Compiled right after funguns.qc (Combat+ only).

float	PK_THROW		= 980;		// violent overhand whip-throw speed
float	PK_FLY			= 5;		// seconds in the air before it gives up and the charge comes back
float	PK_ARM			= 0.6;		// seconds after it sticks before it can go off
float	PK_RADIUS		= 105;		// generous trigger radius for fast strafe-jumping Quake players
float	PK_SAY			= 0.55;		// "pickle surprise" shout before blast (gives a split-second comedy double-take)
float	PK_SCREAM		= 0.24;		// the 360-degree giant scream & balloon swell right before the blast
float	PK_INFLATE		= 0.12;		// seconds to swell up and stand on end: it all but goes off in their face
float	PK_ROLL			= 90;		// roll that turns the 3D pickle's face (its +Z side) out of a wall
float	PK_BLAST		= 125;		// punchy explosion damage at the centre
float	PK_HEALTH		= 25;		// damage that sets a stuck pickle off
float	PK_MAX			= 3;		// pickles per player; a fourth removes the oldest
float	PK_GIBS			= 4;		// pickles thrown by the blast
float	PK_GIB_LIFE		= 1.2;		// seconds a loose pickle (and its flame trail) lasts: 8 was far too long
float	PK_PS			= 1.7;		// scale of the 3D pickle (13 units long at scale 1): the grenade lying on the floor, ~22 long
float	PK_S0			= 1;		// scale of the balloon mesh when it starts to swell (20 units tall at scale 1)
float	PK_S1			= 5.7;		// scale when erect: a player is 56 tall, so this is a little over twice that
.float	pk_safe;		// pickle: sitting out another pickle's blast
.float	pk_dropped;		// pickle: it had stuck, then fell off a moving surface (no charge back if it never re-sticks)
float	PK_HALF			= 10;		// half the height of the mesh at scale 1

// progs/v_pickle.md3 skin ranges (built by source/mm_tools/build_pickle_diva_overhaul.py)
float	PVM_IDLE_SKIN	= 0;		// 0..71:  72 optical-flow smoothed 24fps idle frames (ping-ponged = 142 steps)
float	PVM_IDLE_COUNT	= 72;
float	PVM_WIND_SKIN	= 72;		// 72..87: 16 choke-squeeze windup & violent cross-screen whip frames
float	PVM_PRE_COUNT	= 16;
float	PVM_POST_SKIN	= 88;		// 88..106: 19 splayed open-claw mid-screen recoil shudder & slash-down frames
float	PVM_POST_COUNT	= 19;
float	PVM_RELOAD_SKIN	= 107;		// 107..119: 13 aggressive belt-snatch fresh Pickle raise & cheek-squish frames
float	PVM_RELOAD_CNT	= 13;

void(vector org) Pk_Gib;
void(entity who) Pk_MakeRoom;
void(entity who) Pk_Trip;

// Handles per-client sprite orientation & instant .skin selection (ZERO collapsed-card vertex shrinking!):
//   - pk_state == 1: flying Pickle Surprise tumble sprite (progs/pickle_throw.md3, skins 0..7)
//   - pk_state == 2..3: stuck 3D turquoise Pickle Surprise (progs/pickle_bomb.md3, surface-aligned)
//   - pk_state == 4: 36-frame deforming standing Diva balloon (progs/pickle.md3, skins 0..63 across 4x16 pose sets!)
float() Pk_Customize =
{
	local float v, a, dt, sk, view, expr, ec;

	if (self.pk_state == 1)
	{
		dt = time - self.fg_born;
		if (dt < 0)
			dt = 0;
		if (other.classname == "player")
		{
			self.angles_x = 0 - other.v_angle_x;		// camera-parallel billboard: never foreshortens at steep pitch
			self.angles_y = other.v_angle_y;
		}
		else
		{
			self.angles_x = 0;
			self.angles_y = vectoyaw (other.origin - self.origin) + 180;
		}
		self.angles_z = -28 - dt * 760;				// violent end-over-end spin matching the snapping claw release
		self.frame = 0;
		if (dt < 0.05)
			sk = 0;						// terrified bug-eyed pink-tongue front face leaving the claw
		else
		{
			sk = floor ((dt - 0.05) * 20);
			sk = sk - 8 * floor (sk / 8);
		}
		self.skin = sk;
		return TRUE;
	}

	if (self.pk_state != 4)
		return TRUE;

	v = vectoyaw (other.origin - self.origin);
	a = v - self.pk_front + bm_cvar_pk_ofs;		// pk_viewoffset N: test aid, shows everybody the view from N degrees round
	a = a - 360 * floor (a / 360);				// 0 to 360, anticlockwise from the face
	view = floor (a / 22.5 + 0.5);
	if (view > 15)
		view = 0;

	if (time >= self.pk_t - PK_SCREAM)
	{
		// Set 3 (skins 48..63): Full 360-degree Giant Pre-Blast Scream across ALL 16 angles!
		expr = 3;
	}
	else
	{
		// Cycle lively across Set 0 (Sing), Set 1 (Cheeky Pucker Wink), and Set 2 (Bug-Eyes + Pink Tongue Out)
		ec = floor ((time - self.pk_t0) * 11);
		ec = ec - 6 * floor (ec / 6);
		if (ec == 1 || ec == 5)
			expr = 1;
		else if (ec == 2 || ec == 4)
			expr = 2;
		else
			expr = 0;
	}
	// Keep self.frame untouched here so DarkPlaces hardware-lerps the 36-frame 3D S-curve wave & balloon swell smoothly!
	self.skin = expr * 16 + view;
	self.angles_y = v + 180;					// the mesh's face (-X) toward him
	return TRUE;
};
void() Pk_Touch;
void() Pk_GibTouch;
void() Pk_GibThink;

void() Pickle_Precache =
{
	precache_model ("progs/pickle.md3");
	precache_model ("progs/pickle_throw.md3");
	precache_model ("progs/pickle_gib.md3");
	precache_model ("progs/pickle_bomb.md3");
	precache_sound ("afrit/body_explode.wav");
	precache_sound ("weapons/goopop.wav");
	precache_sound ("weapons/ax1.wav");
	precache_sound ("pickle/throw.wav");
	precache_sound ("pickle/surprise.wav");
};

var float	autocvar_pk_test = 0;

// someone it should go off for: not the owner or a teammate. (set pk_test 1 and the owner counts too, to try it out alone:
// zz_picklesurprise.cfg)
float(entity e) Pk_IsEnemy =
{
	if (!((e.flags & FL_CLIENT) || (e.flags & FL_MONSTER)))
		return FALSE;
	if ((e == self.owner && !autocvar_pk_test) || !e.takedamage || e.health <= 0 || e.classname == "pickle" || e.classname == "pkgib")
		return FALSE;
	if (teamplay && e.team > 0 && e.team == self.owner.team)
		return FALSE;
	return TRUE;
};

// a charge back for the owner (the pickle never stuck)
void(entity who) Pk_Refund =
{
	local float a;

	a = FunGun_Ammo (who, FG_PICKLE);
	if (a < FG_PICKLE_MAX)
		FunGun_SetAmmo (who, FG_PICKLE, a + 1);
};

// it just goes out with a little green puff, no blast
void() Pk_Fizzle =
{
	if (bm_cvar_dev)
		dprint (strcat ("pickle: fizzle at ", strcat (vtos (self.origin), strcat (" water ", strcat (ftos (self.waterlevel), strcat (" state ", strcat (ftos (self.pk_state), strcat (" age ", strcat (ftos (time - self.fg_born), strcat (" content ", strcat (ftos (pointcontents (self.origin)), strcat (" wt ", strcat (ftos (self.watertype), "\n")))))))))))));
	sendParticle ("pk_puff", self.origin, '0 0 0', 1, 0);
	remove (self);
};

// the finale: blast, a green burst and glow, and a shower of pickles
void() Pk_Explode =
{
	local vector org;
	local float i;
	local entity e;

	self.takedamage = DAMAGE_NO;		// its own blast must not finish it off twice
	self.solid = SOLID_NOT;
	org = self.origin;
	dprint (strcat ("pickle: blast at ", ftos (time), "\n"));

	// no chain reactions: the other pickles sit this blast out (they can still be shot, and other explosions still set them off)
	e = find (world, classname, "pickle");
	while (e)
	{
		if (e.takedamage == DAMAGE_YES)
		{
			e.pk_safe = TRUE;
			e.takedamage = DAMAGE_NO;
		}
		e = find (e, classname, "pickle");
	}
	fg_inflicting = FG_PICKLE;
	T_RadiusDamage (self, self.owner, PK_BLAST, world);
	fg_inflicting = 0;
	e = find (world, classname, "pickle");
	while (e)
	{
		if (e.pk_safe)
		{
			e.pk_safe = FALSE;
			e.takedamage = DAMAGE_YES;
		}
		e = find (e, classname, "pickle");
	}

	sendParticle ("pk_boom", org, '0 0 0', 1, 0);		// the green burst and light, with the orange fire in the same effect (effectinfo.txt)
	FG_Snd (self, CHAN_WEAPON, "afrit/body_explode.wav", 1, 1);		// the line has just ended: now the bang

	i = 0;
	while (i < PK_GIBS)
	{
		Pk_Gib (org);
		i = i + 1;
	}
	remove (self);
};

// a shot: in the air it fizzles, once it has stuck it goes off right now
void() Pk_Shot =
{
	if (bm_cvar_dev)
		dprint (strcat ("pickle: shot, state ", strcat (ftos (self.pk_state), strcat (" health ", strcat (ftos (self.health), "\n")))));
	if (self.pk_state < 2)
	{
		Pk_Fizzle ();
		return;
	}
	// this runs inside the T_RadiusDamage loop of whatever shot it: blowing up here ran a second findradius, which rewrote
	// .chain under that loop (players skipped or hit twice). Go off a moment later instead, as megaman.qc does.
	self.takedamage = DAMAGE_NO;
	self.think = Pk_Explode;
	self.nextthink = time;
};

// it hit something: swap from the tumbling throw sprite to the 3D turquoise Pickle Surprise lying flat on the surface
void() Pk_Touch =
{
	local vector v, n, hit_pos;

	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		dprint ("pickle: touched sky\n");
		if (!self.pk_dropped)		// a pickle that already stuck once was a used charge
			Pk_Refund (self.owner);
		remove (self);
		return;
	}
	if (self.pk_state == 3 && Pk_IsEnemy (other))		// touched: off it goes
	{
		Pk_Trip (other);
		return;
	}
	if (self.pk_state != 1 || other == self.owner)
		return;
	if (other != world && other.pc_kind > PC_KIND_NONE)
	{
		PC_HandlePair (self, other);
		return;
	}
	if (other.takedamage && other.health > 0 && (other.classname == "player" || (other.flags & FL_MONSTER)))
	{
		// a direct hit: it bounces off them and sticks to whatever it lands on next, never in mid-air
		v = normalize (self.velocity);
		self.velocity = '0 0 0' - v * 60;
		self.velocity_z = 80;
		return;
	}

	v = normalize (self.velocity);
	if (self.owner && vlen (self.velocity) < 1)
	{
		makevectors (self.owner.v_angle);		// it has stopped dead (thrown into a wall): stick to what is in front of the thrower
		v = v_forward;
	}
	n = '0 0 0' - v;
	hit_pos = self.origin;
	traceline (self.origin - v * 8, self.origin + v * 24, TRUE, self);
	if (trace_fraction < 1)
	{
		n = trace_plane_normal;
		hit_pos = trace_endpos + n * 4;		// the 3D pickle is about 4 units thick: it rests on the surface
	}

	self.traileffectnum = 0;
	setmodel (self, "progs/pickle_bomb.md3");
	setsize (self, '-5 -5 -5', '5 5 5');
	self.frame = 0;
	self.skin = 0;
	self.scale = PK_PS;
	setorigin (self, hit_pos);

	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.avelocity = '0 0 0';
	// the 3D pickle lies along the surface; the balloon mesh it will swell into faces out of it
	if (n_z > 0.7 || n_z < -0.7)
	{
		self.angles = '0 0 0';
		self.angles_y = random () * 360;		// flat, pointing any old way
		self.pk_a0 = '90 0 0';
		if (n_z < 0)
		{
			self.pk_a0 = '-90 0 0';
			self.angles_z = 180;		// on a ceiling its face looks down
		}
		self.pk_a0_y = self.angles_y;
	}
	else
	{
		self.angles = '0 0 0';
		self.angles_y = vectoyaw (n) + 90;		// along the wall
		self.angles_z = PK_ROLL;		// ... with its face (on the model's +Z side) turned out of the wall
		self.pk_a0 = vectoangles ('0 0 0' - n);
	}
	self.pk_n = n;
	self.pk_p0 = self.origin;
	self.takedamage = DAMAGE_YES;		// shootable again after it fell off a moving surface (the fall turned it off)
	self.pk_state = 2;
	self.pk_t = time + PK_ARM;
	dprint ("pickle: stuck\n");
	sendParticle ("pk_stick", self.origin, n * 40, 1, 0);
	FG_Snd (self, CHAN_AUTO, "weapons/goopop.wav", 0.55, 0.75);
};

// it is set off: work out where it will stand, swell up, turn to them, and talk
void(entity who) Pk_Trip =
{
	local vector st;

	// erect means straight up from a floor: the one under it, or in place if there is none
	st = self.pk_p0 + self.pk_n * 24;
	traceline (st, st - '0 0 800', TRUE, self);
	if (trace_fraction < 1)
		self.pk_p1 = trace_endpos + '0 0 1' * (PK_HALF * PK_S1);
	else
		self.pk_p1 = self.pk_p0 + self.pk_n * (PK_HALF * PK_S1);
	self.pk_state = 4;
	self.pk_who = who;
	self.pk_t0 = time;
	self.pk_t = time + PK_SAY;
	self.takedamage = DAMAGE_NO;
	setmodel (self, "progs/pickle.md3");		// the 3D pickle turns into the 36-frame deforming Pickle Diva balloon
	self.frame = 0;
	self.skin = 0;
	self.pk_front = self.angles_y + 180;
	self.customizeentityforclient = Pk_Customize;		// each client sees it from his own side
	setsize (self, '-6 -6 -6', '6 6 6');
	self.scale = PK_S0;
	FG_Snd (self, CHAN_VOICE, "pickle/surprise.wav", 1, 1);
};

void() Pk_Think =
{
	local entity e;
	local float k, ks, d, ty, sw, dt, step_f, u_s;		// sw: sin is a variant builtin, keep its result in a local

	self.nextthink = time + 0.05;

	if (self.pk_state == 1)		// in the air: smooth perspective settle off the snapping claw, then normal flight check
	{
		dt = time - self.fg_born;
		if (dt > 0.12 && vlen (self.velocity) < 40)
		{
			dprint ("pickle: stopped dead, sticking\n");
			other = world;
			Pk_Touch ();
			return;
		}
		if (dt < 0.14)
		{
			k = dt / 0.14;
			if (k < 0)
				k = 0;
			ks = k * k * (3 - 2 * k);
			self.scale = 1.92 - 0.76 * ks;
			self.nextthink = time + 0.02;
		}
		else
			self.scale = 1.16;
		if (time > self.fg_born + PK_FLY || pointcontents (self.origin) == CONTENT_WATER || pointcontents (self.origin) == CONTENT_SLIME || pointcontents (self.origin) == CONTENT_LAVA)
		{
			if (!self.pk_dropped)		// a pickle that already stuck once was a used charge
				Pk_Refund (self.owner);
			Pk_Fizzle ();
		}
		return;
	}

	if (pointcontents (self.origin) <= CONTENT_WATER)		// lava, slime or a lake (waterlevel is never set for a stuck pickle)
	{
		Pk_Fizzle ();
		return;
	}

	if (self.pk_state == 2)		// stuck, arming
	{
		if (time >= self.pk_t)
			self.pk_state = 3;
		return;
	}

	if (self.pk_state == 3)		// armed: watching who comes close
	{
		self.nextthink = time + 0.05;
		// If the door, lift, or van it stuck to moved away, fall & re-stick instead of floating in mid-air!
		traceline (self.origin + self.pk_n * 4, self.origin - self.pk_n * 10, TRUE, self);
		if (trace_fraction == 1)
		{
			self.pk_state = 1;
			self.pk_dropped = TRUE;
			self.movetype = MOVETYPE_TOSS;
			self.takedamage = DAMAGE_NO;
			setmodel (self, "progs/pickle_throw.md3");
			self.scale = 1;
			self.fg_born = time;
			return;
		}
		e = findradius (self.origin, PK_RADIUS);
		while (e)
		{
			if (Pk_IsEnemy (e))
			{
				traceline (self.origin + self.pk_n * 4, e.origin, TRUE, self);
				if (trace_fraction == 1)
				{
					Pk_Trip (e);
					return;
				}
			}
			e = e.chain;
		}
		return;
	}

	// tripped: swell up, stand planted on the floor, face them, S-curve wave (frames 0..23) -> balloon swell (frames 24..35)
	self.nextthink = time + 0.02;
	k = (time - self.pk_t0) / PK_INFLATE;
	if (k > 1)
		k = 1;
	ks = k * k * (3 - 2 * k);		// smooth in and out
	sw = sin (time * 18);
	self.scale = (PK_S0 + (PK_S1 - PK_S0) * ks) * (1 + 0.025 * ks * sw);
	setorigin (self, self.pk_p0 + (self.pk_p1 - self.pk_p0) * ks);

	if (time >= self.pk_t - PK_SCREAM)
	{
		u_s = (time - (self.pk_t - PK_SCREAM)) / PK_SCREAM;
		if (u_s < 0)
			u_s = 0;
		if (u_s > 0.999)
			u_s = 0.999;
		self.frame = 24 + floor (u_s * 12);		// frames 24..35: Pre-Blast Over-Inflation Balloon Swell & Shudder!
	}
	else
	{
		step_f = floor ((time - self.pk_t0) * 24);
		self.frame = step_f - 24 * floor (step_f / 24);	// frames 0..23: Wacky-Waving Inflatable Diva S-Curve Dance!
	}

	ty = self.pk_a0_y;
	if (self.pk_who != world && !bm_wasfreed (self.pk_who) && self.pk_who.health > 0)
		ty = vectoyaw (self.pk_who.origin - self.origin) + 180;		// its face (-X) toward them
	d = ty - self.pk_a0_y;
	d = d - 360 * floor ((d + 180) / 360);
	self.angles_x = self.pk_a0_x * (1 - ks);
	self.angles_y = self.pk_a0_y + d * ks;
	self.pk_front = self.angles_y + 180;		// where the pickle's own face looks (Pk_Customize shows the view from each client's side)
	self.angles_z = self.pk_a0_z * (1 - ks);	// base stays planted on the floor once upright (the 9x17 mesh waves organically!)

	if (time >= self.pk_t)
		Pk_Explode ();
};

// Fired at PK_THROW_DELAY right as the armored gauntlet whips across screen and snaps wide open:
// launches the screaming Pickle Surprise sprite along a fast violent arc straight onto the crosshair target!
void() Pk_Launch =
{
	local entity f;
	local vector eye, aim_pt, hand_want, start_org, dir;

	makevectors (self.v_angle);
	TW_TriggerSequence ();
	Pk_MakeRoom (self);

	eye = self.origin + self.view_ofs;
	traceline (eye, eye + v_forward * 960, FALSE, self);
	if (trace_fraction < 0.14)
		aim_pt = eye + v_forward * 280;
	else
		aim_pt = trace_endpos;

	hand_want = eye + v_forward * 24 + v_right * 2.5 + v_up * 1.0;
	tracebox (eye, '-5 -5 -5', '5 5 5', hand_want, TRUE, self);
	start_org = trace_endpos;
	// never start inside a wall or the floor (running along a wall, or throwing at your feet): a pickle born in the world could not move or
	// touch anything and just vanished (review 2026-11-01: "sometimes nothing is thrown")
	tracebox (start_org, '-5 -5 -5', '5 5 5', start_org, TRUE, self);
	if (trace_startsolid)
	{
		start_org = eye;
		tracebox (start_org, '-5 -5 -5', '5 5 5', start_org, TRUE, self);
		if (trace_startsolid)
			start_org = self.origin + '0 0 8';
	}

	dir = normalize (aim_pt - start_org);
	if (dir == VEC_ORIGIN)
		dir = v_forward;

	dprint (strcat ("pickle: launch vel ", strcat (vtos (self.velocity), "\n")));
	f = spawn ();
	f.owner = self;
	f.classname = "pickle";
	f.movetype = MOVETYPE_TOSS;
	f.solid = SOLID_BBOX;
	f.fg_born = time;
	f.pk_state = 1;
	f.velocity = dir * PK_THROW + v_up * 36;
	f.angles_y = vectoyaw (dir);
	f.scale = 1.92;
	f.takedamage = DAMAGE_YES;		// shoot it to set it off
	f.health = PK_HEALTH;
	f.th_die = Pk_Shot;
	f.touch = Pk_Touch;
	f.think = Pk_Think;
	f.nextthink = time + 0.02;
	f.customizeentityforclient = Pk_Customize;
	setmodel (f, "progs/pickle_throw.md3");
	f.traileffectnum = particleeffectnum ("pk_throw_trail");
	setsize (f, '-5 -5 -5', '5 5 5');
	setorigin (f, start_org);
	PC_Register (f, PC_KIND_LIGHT, 20);

	FG_Snd (self, CHAN_WEAPON, "weapons/ax1.wav", 0.92, 1.18);
	self.punchangle_x = 5.5;		// violent downward/forward slam kick as the claw whips across screen!
	self.punchangle_z = -3.4;
};

// a third one removes the oldest of this player's
void(entity t) Pk_Pop =
{
	local entity oself;

	oself = self;
	self = t;
	Pk_Fizzle ();
	self = oself;
};

void(entity who) Pk_MakeRoom =
{
	local entity t, oldest;
	local float n;

	n = 0;
	oldest = world;
	t = find (world, classname, "pickle");
	while (t)
	{
		if (t.owner == who && t.pk_state != 4)		// one mid-surprise is never cut off by a new throw
		{
			n = n + 1;
			if (!oldest || t.fg_born < oldest.fg_born)
				oldest = t;
		}
		t = find (t, classname, "pickle");
	}
	if (n >= PK_MAX)
		Pk_Pop (oldest);
};

// ---------------------------------------------------------------- the held Pickle Surprise gauntlet (v_pickle.md3)

void(entity vm, float is_quad) Pickle_ViewFrame =
{
	local entity p;
	local float ammo, u, k, ease, idx, step, cycle_len, sw1, sw2, sw3, spd;
	local vector vxy;

	GreenJar_ViewFrame (vm, is_quad);
	Dookie_ViewFrame (vm, is_quad);
	RobHead_ViewFrame (vm, is_quad);
	NS_DiskViewFrame (vm, is_quad);		// the NetSend gun's THE DISK (netsend.qc)
	Kyle_ViewFrame (vm, is_quad);

	p = vm.owner;
	if (p.weapon != IT_FUNGUN || p.fg_sel != FG_PICKLE)
	{
		if (vm.pvm_on)
		{
			if (is_quad)
				vm.skin = 1;
			else
				vm.skin = 0;
			vm.origin = '0 0 0';
			vm.angles = '0 0 0';
			vm.pvm_on = FALSE;
		}
		return;
	}

	if (is_quad && vm.alpha < 0)
		vm.alpha = 0.5;

	vm.frame = 0;
	vm.origin = '0 0 0';
	vm.angles = '0 0 0';
	ammo = FunGun_Ammo (p, FG_PICKLE);

	if (!vm.pvm_on)
	{
		vm.pvm_on = TRUE;
		if (ammo >= 1 && p.pk_throw_at <= 0 && (!p.pk_threw_t || time >= p.pk_threw_t + PK_FOLLOW_TIME))
		{
			if (!is_quad)
				p.pk_reload_t = time;		// crisp raise from below when drawing the Pickle Surprise
		}
		else if (ammo < 1)
			p.pk_empty = TRUE;
	}

	// 1. Brutal choke-squeeze windup & blistering cross-screen whip (skins 72..87, before Pk_Launch() fires!)
	if (p.pk_throw_at > 0)
	{
		p.pk_empty = FALSE;
		u = (time - p.pk_fire_t) / PK_THROW_DELAY;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * PVM_PRE_COUNT);
		vm.skin = PVM_WIND_SKIN + idx;
		if (u < 0.62)
		{
			sw1 = sin ((u / 0.62) * 1.57079);
			vm.origin_x = -2.2 * sw1;
			vm.origin_y = -1.8 * sw1;
			vm.origin_z = 1.3 * sw1;
			vm.angles_x = 3.8 * sw1;
			vm.angles_z = 2.4 * sw1;
		}
		else
		{
			k = (u - 0.62) / 0.38;
			ease = k * k * (3 - 2 * k);
			vm.origin_x = -2.2 * (1 - ease) + 3.8 * ease;
			vm.origin_y = -1.8 * (1 - ease) + 4.2 * ease;
			vm.origin_z = 1.3 * (1 - ease) - 1.2 * ease;
			vm.angles_x = 3.8 * (1 - ease) - 5.0 * ease;
			vm.angles_z = 2.4 * (1 - ease) - 3.6 * ease;
		}
		return;
	}

	// 2. High-impact splayed open-claw recoil shudder + slash down off bottom-left (skins 88..106)
	if (p.pk_threw_t > 0 && time < p.pk_threw_t + PK_FOLLOW_TIME)
	{
		u = (time - p.pk_threw_t) / PK_FOLLOW_TIME;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * PVM_POST_COUNT);
		vm.skin = PVM_POST_SKIN + idx;
		ease = 1 - u;
		vm.origin_x = 3.8 * ease * ease;
		vm.origin_y = 4.2 * ease;
		vm.origin_z = -1.2 - 3.2 * u * u;
		vm.angles_x = -5.0 * ease;
		vm.angles_z = -3.6 * ease;
		if (ammo < 1)
			p.pk_empty = TRUE;
		else if (!is_quad)
			p.pk_reload_t = p.pk_threw_t + PK_FOLLOW_TIME;
		return;
	}

	// 3. Out of charges after follow-through finished: keep hand cleanly put away until next pickle recharges
	if (ammo < 1)
	{
		p.pk_empty = TRUE;
		vm.alpha = -1;
		return;
	}
	if (p.pk_empty)
	{
		p.pk_empty = FALSE;
		p.pk_reload_t = time;
	}

	// 4. Aggressive belt-snatch fresh Pickle raise & elastic cheek-squish catch (skins 107..119)
	if (p.pk_reload_t > 0 && time >= p.pk_reload_t && time < p.pk_reload_t + PK_RAISE_TIME)
	{
		u = (time - p.pk_reload_t) / PK_RAISE_TIME;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * PVM_RELOAD_CNT);
		vm.skin = PVM_RELOAD_SKIN + idx;
		ease = 1 - u;
		vm.origin_z = -2.2 * ease * ease;
		return;
	}

	// 5. Silky-smooth 24fps optical-flow Idle loop (skins 0..71 ping-ponged = 142 steps) + organic breathing/walk sway
	cycle_len = PVM_IDLE_COUNT * 2 - 2;		// 142 steps (5.9 s full ping-pong, zero hard cuts!)
	step = floor (time * 24);
	step = step - cycle_len * floor (step / cycle_len);
	if (step >= PVM_IDLE_COUNT)
		idx = cycle_len - step;
	else
		idx = step;
	vm.skin = PVM_IDLE_SKIN + idx;

	vxy = p.velocity;
	vxy_z = 0;
	spd = vlen (vxy) / 320;
	if (spd > 1)
		spd = 1;
	sw1 = sin (time * 2.4);
	sw2 = sin (time * 4.8);
	sw3 = sin (time * 8.2);
	vm.origin_y = 0.22 * sw1 + 0.55 * spd * sw3;
	vm.origin_z = 0.18 * sw2 - 0.42 * spd * fabs (sw3);
	vm.angles_z = 0.45 * sw1 + 1.10 * spd * sw3;
};

// ---------------------------------------------------------------- the pickles thrown by the blast

// one pickle on a bouncing ride; it does its 2% to the first living thing it touches
void(vector org) Pk_Gib =
{
	local entity g;
	local vector d;

	g = spawn ();
	g.classname = "pkgib";
	g.owner = self.owner;
	g.movetype = MOVETYPE_BOUNCE;
	g.solid = SOLID_BBOX;
	d_x = crandom ();
	d_y = crandom ();
	d_z = 0.8 + random ();
	d = normalize (d);
	g.velocity = d * (420 + random () * 520);		// fast: they ricochet round the whole room
	g.avelocity_x = crandom () * 600;
	g.avelocity_y = crandom () * 600;
	g.avelocity_z = crandom () * 600;
	g.bouncefactor = 0.5;		// DarkPlaces: loses half its speed at each bounce (was 0.9: they rattled round the room)
	g.bouncestop = 0.03;		// ... and only comes to rest on something nearly flat and slow
	g.fg_born = time;
	g.scale = 1.1 + random () * 0.7;		// the model is 13 units long: pickles of 14 to 23
	setmodel (g, "progs/pickle_gib.md3");
	g.traileffectnum = particleeffectnum ("pk_flame");		// burning pickles: a flame trail
	setsize (g, '-4 -4 -4', '4 4 4');
	setorigin (g, org + d * 8);
	g.touch = Pk_GibTouch;
	g.think = Pk_GibThink;
	g.nextthink = time + 0.1;
};

void() Pk_GibTouch =
{
	local float dmg;
	local vector push;

	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	if (!other.takedamage || other.health <= 0)
		return;
	if (other == self.owner && !autocvar_pk_test)
		return;
	dmg = 14;
	if (other.movetype == MOVETYPE_WALK || other.movetype == MOVETYPE_STEP)
	{
		push = normalize (self.velocity);
		if (vlen (push) < 0.1)
			push = '0 0 1';
		other.flags = other.flags - (other.flags & FL_ONGROUND);
		other.velocity = other.velocity + push * 220 + '0 0 160';
	}
	fg_inflicting = FG_PICKLE;
	T_Damage (other, self, self.owner, dmg);
	fg_inflicting = 0;
	remove (self);
};

void() Pk_GibThink =
{
	if (time > self.fg_born + PK_GIB_LIFE)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.1;
};
