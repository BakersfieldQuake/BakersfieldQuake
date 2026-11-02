/*
================
THE MILKY GUN (see milky_defs.qc for the rules and numbers)

Hooks (patch_milky_combat.py): W_Attack fires Milky_Fire for IT_SUPER_NAILGUN, W_WeaponFrame runs Milky_PlayerFrame
(breadcrumbs and the slide), T_Damage runs damage through Milky_Damage (the lady keeps her own hit points), and the
obituary checks milky_inflicting.
================
*/

void() Milky_Precache =
{
	precache_model ("progs/pinklady.md3");
	precache_model ("progs/milksplat.md3");
	precache_model ("progs/v_milky.md3");
	precache_sound ("milky/song.ogg");
	precache_sound ("milky/fire.wav");
	precache_sound ("afrit/body_explode.wav");
	precache_sound ("misc/h2ohit1.wav");
	precache_sound ("misc/null.wav");
	precache_sound ("weapons/goostick.wav");
	precache_sound ("weapons/goosplat.wav");
	precache_sound ("weapons/goopop.wav");
};

void(entity e, float chan, string samp, float vol, float attn) Milky_Snd =
{
	sound7 (e, chan, samp, vol, attn, SNDSPD);
};

void(entity e, float chan, string samp, float vol, float attn, float pitch) Milky_SndP =
{
	sound7 (e, chan, samp, vol, attn, SNDSPD * pitch);
};

vector	milky_org;		// Milky_Room: where she would start

// ---------------------------------------------------------------- the lady's sprite

// run by the engine for every client before it sends her: the card turns to face him, and the frame is the view
// of her from where he stands (frame k: k * 22.5 degrees anticlockwise from her face), her face the way she flies
float() Milky_Customize =
{
	local float v, a, dt, k, face_yaw;
	local vector delta;

	dt = time - self.milky_born;
	if (other == self.milky_owner && dt < MILKY_EMERGE)		// lifts off the palm facing her shooter, then twirls 180 deg onto flight vector
	{
		if (dt < 0)
			dt = 0;
		k = dt / MILKY_EMERGE;
		k = k * k * (3 - 2 * k);
		a = 180 * k;
	}
	else
	{
		delta = (other.origin + other.view_ofs) - self.origin;
		delta_z = 0;
		if (vlen (delta) > 16)
			v = vectoyaw (delta);
		else
			v = other.v_angle_y + 180;
		face_yaw = vectoyaw (self.milky_dir);
		a = v - face_yaw;
	}
	a = a - 360 * floor (a / 360);
	self.frame = 0;
	self.skin = floor (a / 22.5 + 0.5);		// the picture is the skin (progs/pinklady.md3_K.skin): instant, no blending
	if (self.skin > 15)
		self.skin = 0;
	if (other.classname == "player")
	{
		self.angles_x = 0 - other.v_angle_x;		// camera-parallel billboard: never foreshortens or flips overhead
		self.angles_y = other.v_angle_y;
		self.angles_z = 0;
	}
	else
	{
		self.angles_x = 0;
		self.angles_y = vectoyaw (other.origin - self.origin) + 180;
		self.angles_z = 0;
	}
	return TRUE;
};

// someone she goes after: a live player who is not her shooter (milky_test 1: him too) or his teammate
float(entity e) Milky_IsEnemy =
{
	if (e.classname != "player" || e.health <= 0 || !e.takedamage || e.solid == SOLID_NOT)
		return FALSE;
	if (e == self.milky_owner)
		return (cvar ("milky_test") != 0 && time > self.milky_born + 1.5);	// test aid: she comes back for him, once clear of him
	if (teamplay && e.team > 0 && e.team == self.milky_owner.team)
		return FALSE;
	return TRUE;
};

float(entity e) Milky_Sees =
{
	traceline (self.origin, e.origin, TRUE, self);
	return (trace_fraction == 1);
};

// ---------------------------------------------------------------- milk on the walls

void() Milk_Remove =
{
	if (self.milk_qprev)
		self.milk_qprev.milk_qnext = self.milk_qnext;
	else if (milk_qhead == self)
		milk_qhead = self.milk_qnext;
	if (self.milk_qnext)
		self.milk_qnext.milk_qprev = self.milk_qprev;
	else if (milk_qtail == self)
		milk_qtail = self.milk_qprev;
	self.milk_qprev = world;
	self.milk_qnext = world;
	milk_count = milk_count - 1;
	remove (self);
};

void() Milk_RemoveOldest =
{
	local entity oself;

	if (milk_qhead)
	{
		oself = self;
		self = milk_qhead;
		Milk_Remove ();
		self = oself;
	}
};

void() Milk_SplatThink =
{
	local float t, a, k;
	local vector n, side, p;

	t = time - self.milk_born;
	self.nextthink = time + 0.05;
	k = t / 1.4;		// it splashes on, then oozes outward
	if (k > 1)
		k = 1;
	k = 1 - (1 - k) * (1 - k);
	k = 0.3 + 0.7 * k;
	if (self.classname == "milk_puddle")
	{
		a = t / 4;		// and a puddle keeps spreading, slowly, for a few seconds
		if (a > 1)
			a = 1;
		k = k * (1 + 0.35 * a);
		self.milk_r = self.milk_size * 9.6 * (1 + 0.35 * a);
	}
	self.scale = self.milk_size * k;
	if (t > MILK_LIFE)
	{
		a = 1 - (t - MILK_LIFE) / MILK_FADE;
		if (a <= 0.03)
		{
			Milk_Remove ();
			return;
		}
		self.alpha = a;
		return;
	}
	if (self.classname == "milk_puddle")
	{
		self.nextthink = time + 0.25;
		return;
	}
	if (time < self.milky_drip)
		return;
	// drip: off the bottom edge of a wall splat, anywhere off a ceiling one. It slows down as the milk dries
	n = self.milk_n;
	if (n_z < -0.7)
		p = self.origin + n * 2 + randomvec () * self.milk_size * 7;
	else
	{
		side_x = 0 - n_y;
		side_y = n_x;
		side_z = 0;
		side = normalize (side);
		p = self.origin + n * 2 + side * crandom () * self.milk_size * 7 - '0 0 1' * self.milk_size * (5 + random () * 5);
	}
	pointparticles (particleeffectnum ("milk_drip"), p, '0 0 0', 1);
	self.milky_drip = time + 0.12 + random () * 0.5 + t * 0.08;
};

// one splat of milk on a surface: floors get puddles (you slide on them), walls and ceilings get drippy splats
void(vector pos, vector n, float size) Milk_Splat =
{
	local entity sp;

	if (milk_count >= MILK_MAX)
		Milk_RemoveOldest ();
	sp = spawn ();
	if (n_z > 0.7)
		sp.classname = "milk_puddle";
	else
		sp.classname = "milk_splat";
	sp.movetype = MOVETYPE_NONE;
	sp.solid = SOLID_NOT;
	sp.effects = EF_FULLBRIGHT;
	sp.milk_n = n;
	sp.angles = vectoangles (n);		// the card's X along the normal: it lies flat on the surface
	if (n_z > 0.7 || n_z < -0.7)
	{
		sp.frame = floor (random () * 3);		// round splats, any way round
		if (sp.frame > 2)
			sp.frame = 2;
		sp.angles_z = random () * 360;
	}
	else
	{
		sp.frame = 3 + floor (random () * 3);	// splats with runs down them: kept upright
		if (sp.frame > 5)
			sp.frame = 5;
	}
	setmodel (sp, "progs/milksplat.md3");
	setsize (sp, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (sp, pos + n * (0.5 + random () * 0.6));		// a little off the surface, a little apart from each other
	sp.milk_size = size;
	sp.scale = size * 0.3;
	sp.milk_r = size * 12 * 0.8;		// the card is 24 units across
	sp.milk_born = time;
	sp.milky_drip = time + 0.12 + random () * 0.35;
	sp.think = Milk_SplatThink;
	sp.nextthink = time + 0.03;
	sp.milk_qprev = milk_qtail;
	sp.milk_qnext = world;
	if (milk_qtail)
		milk_qtail.milk_qnext = sp;
	else
		milk_qhead = sp;
	milk_qtail = sp;
	milk_count = milk_count + 1;
};

// where a line from org hits the world, a splat (not on sky, not on doors and lifts)
void(vector org, vector to, float size) Milk_SplatAlong =
{
	traceline (org, to, TRUE, self);
	if (trace_fraction == 1 || trace_startsolid || trace_ent != world)
		return;
	if (pointcontents (trace_endpos - trace_plane_normal * 2) == CONTENT_SKY)
		return;
	Milk_Splat (trace_endpos, trace_plane_normal, size);
};

void() Milk_GlobTouch =
{
	local vector dir;

	if (other == self.owner || other.classname == "milky" || other.classname == "milk_glob")
		return;
	dir = normalize (self.velocity);
	if (dir == VEC_ORIGIN)
		dir = '0 0 -1';
	if (other == world)
		Milk_SplatAlong (self.origin - dir * 16, self.origin + dir * 24, 0.6 + random () * 0.7);
	else
		Milk_SplatAlong (self.origin, self.origin - '0 0 96', 0.6 + random () * 0.5);	// hit someone: it runs off him onto the floor
	remove (self);
};

// physical falling milk drop shed from beneath the Pink Lady while she floats
void(entity lady, vector drop_org, vector base_vel) Milk_SpawnFlightDrop =
{
	local entity g;

	g = spawn ();
	g.classname = "milk_glob";
	g.owner = lady;
	g.movetype = MOVETYPE_TOSS;
	g.solid = SOLID_BBOX;
	g.effects = EF_FULLBRIGHT;
	g.frame = floor (random () * 3);
	if (g.frame > 2)
		g.frame = 2;
	g.scale = 0.28 + random () * 0.28;
	g.angles = randomvec () * 180;
	g.avelocity = randomvec () * 420;
	g.velocity = base_vel * 0.25 + randomvec () * 34 - '0 0 65';
	g.traileffectnum = particleeffectnum ("milk_glob");
	g.touch = Milk_GlobTouch;
	g.think = SUB_Remove;
	g.nextthink = time + 3.5;
	setmodel (g, "progs/milksplat.md3");
	setsize (g, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (g, drop_org);
};

// the burst: milk straight out onto everything round it, and globs flung further that splat where they land
void(vector org) Milk_Splatter =
{
	local float i;
	local vector dir;
	local entity g;

	i = 0;
	while (i < MILK_TRACES)
	{
		dir = randomvec ();
		dir_z = dir_z - 0.25;		// a bit more of it goes down: puddles
		if (dir == VEC_ORIGIN)
			dir = '0 0 -1';
		Milk_SplatAlong (org, org + normalize (dir) * MILK_RANGE * (0.45 + random () * 0.55), 1.6 + random () * 2.2);
		i = i + 1;
	}
	i = 0;
	while (i < MILK_GLOBS)
	{
		g = spawn ();
		g.classname = "milk_glob";
		g.movetype = MOVETYPE_TOSS;
		g.solid = SOLID_BBOX;
		g.effects = EF_FULLBRIGHT;
		g.frame = floor (random () * 3);
		g.scale = 0.45 + random () * 0.45;
		g.angles = randomvec () * 180;
		g.avelocity = randomvec () * 600;
		g.velocity = randomvec () * 1000 + '0 0 420';
		g.traileffectnum = particleeffectnum ("milk_glob");
		g.touch = Milk_GlobTouch;
		g.think = SUB_Remove;
		g.nextthink = time + 4;
		setmodel (g, "progs/milksplat.md3");
		setsize (g, VEC_ORIGIN, VEC_ORIGIN);
		setorigin (g, org + randomvec () * 16);
		i = i + 1;
	}
};

// the burst's afterwards: milk keeps raining down round the spot for a few seconds
void() Milk_RainThink =
{
	local float i;

	i = 0;
	while (i < 4)
	{
		pointparticles (particleeffectnum ("milk_rain"), self.origin + randomvec () * 260 + '0 0 150', '0 0 0', 1);
		i = i + 1;
	}
	if (time > self.milk_born + 3.2)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.07;
};

void(vector org) Milk_Rain =
{
	local entity r;

	r = spawn ();
	r.classname = "milk_rain";
	r.movetype = MOVETYPE_NONE;
	r.solid = SOLID_NOT;
	r.milk_born = time;
	r.think = Milk_RainThink;
	r.nextthink = time + 0.1;
	setorigin (r, org);
};

// TRUE if a puddle is under p's feet
float(entity p) Milk_Under =
{
	local entity e;
	local vector d;

	if (time < p.milk_under_t)
		return p.milk_under_cached;
	p.milk_under_t = time + 0.08;
	e = find (world, classname, "milk_puddle");
	while (e)
	{
		d = p.origin - e.origin;
		if (d_z > 8 && d_z < 40)		// a player's origin is 24 above his feet
		{
			d_z = 0;
			if (vlen (d) < e.milk_r)
			{
				p.milk_under_cached = TRUE;
				return TRUE;
			}
		}
		e = find (e, classname, "milk_puddle");
	}
	p.milk_under_cached = FALSE;
	return FALSE;
};

// review 2026-11-01: no screen flash or HUD overlay on burst (players only see the 3D milk explosion in the world);
// when she catches someone (not shot down), those in the blast are frozen for MILKY_FREEZE seconds, then slide on the milk
void(vector org, float caught) Milk_Flash =
{
	local entity p;
	local float d;

	if (!caught)
		return;
	p = bm_player_head;
	while (p)
	{
		if (p.health > 0 && p.bm_prot_t <= time)		// spawn protection: no freeze either
		{
			d = vlen (p.origin + p.view_ofs - org);
			traceline (org, p.origin + p.view_ofs, TRUE, world);
			if (d < MILKY_BLAST + 40 && (trace_fraction == 1 || d < 200))
				p.milk_freeze = time + MILKY_FREEZE;
		}
		p = p.bm_player_next;
	}
};

// ---------------------------------------------------------------- the lady

void() Milky_Hush =
{
	Milky_Snd (self, CHAN_VOICE, "misc/null.wav", 1, ATTN_NORM);	// the song stops with her (it would play on after remove)
};

void() Milky_Burst =
{
	local vector org;
	local entity who;

	org = self.origin;
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.touch = SUB_Null;
	Milky_Hush ();
	who = self.enemy;		// whoever shot her down gets the credit (like a barrel); else her shooter
	if (!who || who.classname != "player")
		who = self.milky_owner;
	milky_inflicting = TRUE;
	T_RadiusDamage (self, who, MILKY_BLAST, world);
	milky_inflicting = FALSE;
	pointparticles (particleeffectnum ("milky_boom"), org, '0 0 0', 1);
	Milky_SndP (self, CHAN_AUTO, "afrit/body_explode.wav", 0.55, 1.4, 0.8);
	Milky_SndP (self, CHAN_AUTO, "misc/h2ohit1.wav", 0.55, 1.4, 0.6);		// a big wet splash
	Milky_SndP (self, CHAN_AUTO, "weapons/goopop.wav", 0.55, 1.4, 0.55);	// and a slimy burst
	Milky_SndP (self, CHAN_AUTO, "weapons/goosplat.wav", 0.6, 1.4, 0.7);
	Milk_Splatter (org);
	Milk_Rain (org);
	Milk_Flash (org, (self.milky_hp > 0));
	if (cvar ("milky_debug"))
		bprint ("milky: burst after ", ftos (floor (time - self.milky_born)), " s at ", vtos (org), ", ", ", target ", ftos (floor (vlen (self.milky_target.origin - org))), "\n");
	milky_count = milky_count - 1;
	remove (self);
};

void() Milky_Vanish =
{
	if (cvar ("milky_debug"))
		bprint ("milky: vanished into the sky at ", vtos (self.origin), "\n");
	Milky_Hush ();
	milky_count = milky_count - 1;
	remove (self);
};

void() Milky_Touch =
{
	if (Milky_IsEnemy (other))
		Milky_Burst ();
};

// a crumb she can get to in a straight line (she is player-sized, like the feet that dropped it)
float(entity c) Milky_Reaches =
{
	tracebox (self.origin, MILKY_MIN, MILKY_MAX, c.origin, TRUE, self);
	return (trace_fraction == 1 && !trace_startsolid);
};

// her target is out of sight. In order: the newest of his own crumbs she can get to; else the crumb she can get to
// (anybody's: every crumb is a place a player has been, so together they map out the ways round) that is nearest
// him and nearer than she is; else straight at him, sliding along whatever is in the way
void() Milky_Trail =
{
	local entity c, best, near;
	local float bt, bd, d;
	local vector tg;

	tg = self.milky_target.origin;
	best = world;
	bt = self.milky_goal_t;
	near = world;
	bd = vlen (tg - self.origin) - 48;
	c = find (world, classname, "milk_crumb");
	while (c)
	{
		if (vlen (c.origin - self.origin) < 1200)
		{
			if (c.owner == self.milky_target && c.milk_t > bt && Milky_Reaches (c))
			{
				best = c;
				bt = c.milk_t;
			}
			else if (!best)
			{
				d = vlen (tg - c.origin);
				if (d < bd && vlen (c.origin - self.origin) > 40 && Milky_Reaches (c))
				{
					near = c;
					bd = d;
				}
			}
		}
		c = find (c, classname, "milk_crumb");
	}
	if (best)
	{
		self.milky_goal = best.origin;
		self.milky_goal_t = best.milk_t;
		self.milky_seen = time;
		if (cvar ("milky_debug") > 1)
			bprint ("milky: on ", self.milky_target.netname, "'s trail, crumb ", ftos (floor (vlen (best.origin - self.origin))), " away\n");
	}
	else if (near)
	{
		self.milky_goal = near.origin;
		if (cvar ("milky_debug") > 1)
			bprint ("milky: making her way to ", self.milky_target.netname, ", ", ftos (floor (bd)), " from him\n");
	}
	else
		self.milky_goal = tg;
};

// look round: keep a target she can see, else take the nearest enemy she can see, else hunt the nearest enemy anywhere
// (she always knows roughly where you are) by his trail
void() Milky_Look =
{
	local entity e, best, near;
	local float d, bd, nd;

	if (self.milky_target && !Milky_IsEnemy (self.milky_target))
		self.milky_target = world;
	if (self.milky_target && Milky_Sees (self.milky_target))
	{
		self.milky_goal = self.milky_target.origin;
		self.milky_goal_t = time;
		self.milky_seen = time;
		return;
	}
	best = world;
	bd = MILKY_SEEK;
	near = world;
	nd = 999999;
	e = find (world, classname, "player");
	while (e)
	{
		if (Milky_IsEnemy (e))
		{
			d = vlen (e.origin - self.origin);
			if (d < bd && Milky_Sees (e))
			{
				best = e;
				bd = d;
			}
			if (d < nd)
			{
				near = e;
				nd = d;
			}
		}
		e = find (e, classname, "player");
	}
	if (best)
	{
		if (best != self.milky_target && cvar ("milky_debug"))
			bprint ("milky: sees ", best.netname, "\n");
		self.milky_target = best;
		self.milky_goal = best.origin;
		self.milky_goal_t = time;
		self.milky_seen = time;
		return;
	}
	if (near && (!self.milky_target || time > self.milky_seen + MILKY_LOST))
	{
		// nobody in sight and no fresh trail: go after whoever is nearest, wherever he is
		if (near != self.milky_target && cvar ("milky_debug"))
			bprint ("milky: hunting ", near.netname, "\n");
		self.milky_target = near;
		self.milky_goal_t = 0;
		self.milky_seen = time;
	}
	if (self.milky_target)
		Milky_Trail ();
};

// dir turned toward want by at most deg degrees, in yaw and in pitch
vector(vector dir, vector want, float deg) Milky_TurnToward =
{
	local vector a, b;
	local float d;

	a = vectoangles (dir);
	b = vectoangles (want);
	d = b_y - a_y;
	d = d - 360 * floor ((d + 180) / 360);		// -180 to 180
	if (d > deg)
		d = deg;
	else if (d < 0 - deg)
		d = 0 - deg;
	a_y = a_y + d;
	d = b_x - a_x;
	d = d - 360 * floor ((d + 180) / 360);
	if (d > deg)
		d = deg;
	else if (d < 0 - deg)
		d = 0 - deg;
	a_x = 0 - (a_x + d);		// vectoangles gives pitch up, makevectors takes it down
	makevectors (a);
	return v_forward;
};

void() Milky_Think =
{
	local entity e;
	local vector want, v, pod_side;
	local float spd, turn, sw, a, dt, ease;

	self.nextthink = time + 0.05;
	if (time > self.milky_born + MILKY_LIFE)
	{
		Milky_Burst ();
		return;
	}
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		Milky_Vanish ();
		return;
	}
	if (!self.milky_emerged)
	{
		dt = time - self.milky_born;
		if (dt < MILKY_EMERGE)
		{
			self.nextthink = time + 0.02;
			e = find (world, classname, "player");
			while (e)
			{
				if (Milky_IsEnemy (e) && vlen (e.origin - self.origin) < MILKY_REACH && Milky_Sees (e))
				{
					Milky_Burst ();
					return;
				}
				e = find (e, classname, "player");
			}
			if (dt < 0)
				dt = 0;
			a = dt / MILKY_EMERGE;
			ease = 1.375 * a - 0.375 * a * a;
			self.scale = 2.1 + (MILKY_SCALE - 2.1) * a;
			setorigin (self, self.milky_from + (self.milky_to - self.milky_from) * ease);
			self.velocity = (self.milky_to - self.milky_from) * ((1.375 - 0.75 * a) / MILKY_EMERGE);
			if (dt > 0.08 && time >= self.milky_drip)
			{
				pointparticles (particleeffectnum ("milk_drip"), self.origin + randomvec () * (self.scale * 1.2) - '0 0 1' * (self.scale * 2.9), '0 0 0', 1);
				self.milky_drip = time + 0.06;
			}
			return;
		}
		self.milky_emerged = TRUE;
		self.owner = world;		// now clear of her shooter: solid to everyone, him too
		self.movetype = MOVETYPE_FLY;
		self.scale = MILKY_SCALE;
		self.traileffectnum = particleeffectnum ("milky_trail");		// start the long milk trail once clear of the camera
		setsize (self, MILKY_MIN, MILKY_MAX);
		setorigin (self, self.milky_to);
		self.velocity = self.milky_dir * MILKY_SPEED;
		self.milky_last = self.origin;
		self.milky_lastt = time;
	}
	if (!self.milky_song2 && time > self.milky_born + MILKY_SONG_LEN)		// the song once more
	{
		self.milky_song2 = TRUE;
		Milky_Snd (self, CHAN_VOICE, "milky/song.ogg", MILKY_SONG_VOL, MILKY_SONG_ATTN);
	}

	// close enough to someone: burst
	e = bm_player_head;
	while (e)
	{
		if (Milky_IsEnemy (e) && vlen (e.origin - self.origin) < MILKY_REACH && Milky_Sees (e))
		{
			Milky_Burst ();
			return;
		}
		e = e.bm_player_next;
	}

	if (time > self.milky_scan)
	{
		self.milky_scan = time + 0.3;
		Milky_Look ();
	}

	spd = MILKY_SPEED;
	turn = MILKY_TURN * 0.05;
	if (self.milky_target)
	{
		want = self.milky_goal + '0 0 1' * (MILKY_HOVER - 24) - self.origin;		// a player's origin is 24 over his feet: she goes for his face
		if (vlen (want) < 24)		// at the last place she knew of: hang there and turn about, looking
		{
			a = (vectoyaw (self.milky_dir) + 9) * (3.14159 / 180);
			sw = cos (a);		// sin and cos are variant builtins: their results go through a float local
			self.milky_dir_x = sw;
			sw = sin (a);
			self.milky_dir_y = sw;
			self.milky_dir_z = 0;
			want = VEC_ORIGIN;
			spd = 0;
		}
	}
	else
	{
		want = self.milky_dir;		// nobody to go after: drift on
		if (time > self.milky_born + 3)
			spd = MILKY_SPEED_LOST;
	}

	// stuck on something for a second: shove off sideways and up for a moment
	if (time > self.milky_lastt + 1)
	{
		if (spd > 0 && vlen (self.origin - self.milky_last) < 30)
		{
			v = randomvec ();
			v_z = fabs (v_z) * 0.5 + 0.3;
			self.movedir = normalize (v);
			self.milky_dodge = time + 0.8;
			if (!self.milky_target)
				self.milky_dir = self.movedir;
		}
		self.milky_last = self.origin;
		self.milky_lastt = time;
	}
	if (time < self.milky_dodge)
	{
		want = self.movedir;
		turn = 12.5;
	}

	if (want != VEC_ORIGIN)
		self.milky_dir = Milky_TurnToward (self.milky_dir, normalize (want), turn);
	sw = sin (time * 2.2 + self.milky_phase);
	self.velocity = self.milky_dir * spd + '0 0 1' * sw * 6;		// the bounce is in her picture now (the video), this is only a drift

	// she floats: never lower than MILKY_HOVER over the floor (her picture reaches 94 below her middle), and she drifts
	// back up when she has sunk, instead of pressing into the ground and sticking there
	traceline (self.origin, self.origin - '0 0 400', TRUE, self);
	a = self.origin_z - trace_endpos_z;
	if (trace_fraction < 1 && a < MILKY_HOVER)
	{
		if (self.velocity_z < 0)
			self.velocity_z = 0;
		self.velocity_z = self.velocity_z + (MILKY_HOVER - a) * 3 + 20;
		if (self.milky_dir_z < 0)
			self.milky_dir_z = 0;
	}

	// continuous multi-stream milk drips & falling physical milk droplets from beneath both pods and her tie-ribbon
	pod_side_x = self.milky_dir_y;
	pod_side_y = 0 - self.milky_dir_x;
	pod_side_z = 0;
	if (pod_side != VEC_ORIGIN)
		pod_side = normalize (pod_side);
	if (random () < 0.12)		// review 2026-11-01: "less milk coming out of her"
		pointparticles (particleeffectnum ("milk_ooze"), self.origin + pod_side * (crandom () * 28) + randomvec () * 10 - '0 0 38', '0 0 0', 1);
	if (time >= self.milky_drip)
	{
		pointparticles (particleeffectnum ("milk_drip"), self.origin - pod_side * (15 + random () * 15) - '0 0 44', '0 0 0', 1);
		pointparticles (particleeffectnum ("milk_drip"), self.origin + pod_side * (15 + random () * 15) - '0 0 44', '0 0 0', 1);
		if (random () < 0.55)
			pointparticles (particleeffectnum ("milk_drip"), self.origin + randomvec () * 6 - '0 0 62', '0 0 0', 1);
		self.milky_drip = time + 0.3 + random () * 0.25;
	}
	if (time > self.milky_ptrail)		// fat 3D milk droplets fall off her pods and splash into slippery puddles below
	{
		Milk_SpawnFlightDrop (self, self.origin + pod_side * (crandom () * 26) - '0 0 54', self.velocity);
		if (random () < 0.35)
			Milk_SplatAlong (self.origin + pod_side * (crandom () * 20), self.origin - '0 0 500', 0.6 + random () * 0.5);
		self.milky_ptrail = time + 0.9 + random () * 0.6;
	}
};

// T_Damage: she keeps her own hit points (her .health never goes down, so she is never Killed like a monster);
// every hit spurts milk off the side that was shot
float(entity targ, entity inflictor, entity attacker, float damage) Milky_Damage =
{
	local vector dir;

	if (targ.classname != "milky")
		return damage;
	if (targ.milky_hp <= 0)
		return 0;
	dir = normalize (inflictor.origin - targ.origin);
	if (dir == VEC_ORIGIN)
		dir = '0 0 1';
	pointparticles (particleeffectnum ("milky_hit"), targ.origin + dir * 14, dir, 1);
	targ.milky_hp = targ.milky_hp - damage;
	if (cvar ("milky_debug"))
		bprint ("milky: hit for ", ftos (floor (damage)), ", ", ftos (floor (targ.milky_hp)), " left\n");
	if (targ.milky_hp <= 0)
	{
		targ.enemy = attacker;
		targ.takedamage = DAMAGE_NO;
		targ.think = Milky_Burst;
		targ.nextthink = time;
	}
	return 0;
};

// ---------------------------------------------------------------- the gun

// room in front of him for her (she is as big as two players). She floats, so stairs or a ledge ahead: try her higher up.
// self is the player; milky_org is where she would start
float() Milky_Room =
{
	local vector flat, org;
	local float n;

	makevectors (self.v_angle);
	flat = v_forward;
	flat_z = 0;
	flat = normalize (flat);
	if (flat == VEC_ORIGIN)
		flat = v_right;
	n = 0;
	while (n < 3)
	{
		tracebox (self.origin + '0 0 72', MILKY_MIN, MILKY_MAX, self.origin + '0 0 1' * (72 + n * 24), TRUE, self);
		org = trace_endpos;
		tracebox (org, MILKY_MIN, MILKY_MAX, org + flat * 72, TRUE, self);
		if (!trace_startsolid && trace_fraction >= 0.75)
		{
			milky_org = trace_endpos;
			return TRUE;
		}
		n = n + 1;
	}
	return FALSE;
};

// TRUE while one of p's ladies is out there (alive)
float(entity p) Milky_Out =
{
	local entity e;

	e = p.milky_active;
	return (e != world && e.classname == "milky" && e.milky_owner == p && e.milky_hp > 0 && e.takedamage);
};

// W_Attack, before anything is shown: one lady at a time. TRUE if he may start a throw
float() Milky_CanFire =
{
	if (self.milky_wind > time)
		return FALSE;		// the last one is still in the fist
	if (Milky_Out (self))
	{
		self.attack_finished = time + 0.4;		// look again in a moment
		if (time > self.milky_msg)
		{
			self.milky_msg = time + 2.5;
			centerprint (self, "She's still out there.\nThrow the next one when she explodes.\n");
			Milky_Snd (self, CHAN_WEAPON, "weapons/goostick.wav", 0.5, ATTN_NORM);
			if (cvar ("milky_debug"))
				bprint ("milky: refused, one is still out\n");
		}
		return FALSE;
	}
	return TRUE;
};

// W_Attack with the Milky Gun out: the fist winds up (the held model plays the shot clip, Milky_ViewFrame) and the song
// line starts; MILKY_WIND later she is thrown (Milky_Launch, from Milky_PlayerFrame)
void() Milky_Fire =
{
	if (!Milky_CanFire ())
		return;
	if (!Milky_Room ())
	{
		Milky_Snd (self, CHAN_WEAPON, "weapons/goostick.wav", 0.6, ATTN_NORM);
		centerprint (self, "No room for her here\n");
		self.attack_finished = time + 0.5;
		return;
	}
	self.ammo_nails = self.ammo_nails - 1;
	self.currentammo = self.ammo_nails;
	self.milky_fire_t = time;
	self.milky_wind = time + MILKY_WIND;
	self.attack_timer = 1;
	self.attack_finished = time + MILKY_WIND + MILKY_REFIRE;		// the windup, then the cool-down
	self.milky_hide = self.milky_wind + MILKY_FLYOUT + MILKY_HIDE;
	Milky_Snd (self, CHAN_WEAPON, "milky/fire.wav", 0.8, ATTN_NORM);		// the gun itself, not the song: it was at the song volume and range
	if (cvar ("milky_debug"))
		bprint ("milky: winding up at ", ftos (time), ", nails left ", ftos (self.ammo_nails), "\n");
};

// self is the player: she leaves his open palm
void() Milky_Launch =
{
	local entity m, e, old, oself;
	local float n, rem;
	local vector flat, eye, hand_want, launch_dir, start_org, end_org;

	if (!Milky_Room ())
	{
		self.ammo_nails = self.ammo_nails + 1;		// a wall in the way by now: she squirmed out of the throw
		self.currentammo = self.ammo_nails;
		self.milky_threw = 0;
		self.milky_hide = 0;
		Milky_Snd (self, CHAN_WEAPON, "weapons/goostick.wav", 0.6, ATTN_NORM);
		return;
	}
	self.milky_threw = time;
	player_mm1 ();
	makevectors (self.v_angle);
	eye = self.origin + self.view_ofs;
	flat = v_forward;
	flat_z = 0;
	flat = normalize (flat);
	if (flat == VEC_ORIGIN)
		flat = v_right;

	// his oldest lady bursts if he has too many out
	n = 0;
	old = world;
	e = find (world, classname, "milky");
	while (e)
	{
		if (e.milky_owner == self && e.takedamage)
		{
			n = n + 1;
			if (!old || e.milky_born < old.milky_born)
				old = e;
		}
		e = find (e, classname, "milky");
	}
	if (n >= MILKY_PER_PLAYER && old)
	{
		oself = self;
		self = old;
		Milky_Burst ();
		self = oself;
	}

	self.punchangle_x = -2.5;
	if (cvar ("milky_debug"))
		bprint ("milky: thrown at ", ftos (time), "\n");

	launch_dir = v_forward;
	if (launch_dir_z > 0.55)
	{
		launch_dir = flat + '0 0 0.66';
		launch_dir = normalize (launch_dir);
	}
	else if (launch_dir_z < -0.25)
	{
		launch_dir = flat - '0 0 0.26';
		launch_dir = normalize (launch_dir);
	}
	tracebox (milky_org, MILKY_MIN, MILKY_MAX, milky_org + launch_dir * 108, TRUE, self);
	end_org = trace_endpos;
	rem = 1 - trace_fraction;
	if (trace_plane_normal_z < -0.3 && launch_dir_z > 0)
		launch_dir = flat;		// low ceiling ahead: cruise down the hall instead of into the ceiling
	if (rem > 0.15)
	{
		tracebox (end_org, MILKY_MIN, MILKY_MAX, end_org + flat * (108 * rem), TRUE, self);
		end_org = trace_endpos;
	}

	// match the exact screen ray and height of the Pink Lady standing on the open right palm at release
	hand_want = eye + v_forward * 48 + v_right * 23 - v_up * 4.5;
	if (hand_want_z > end_org_z + 4)
		hand_want_z = end_org_z + 4;
	tracebox (eye, '-10 -10 -16', '10 10 16', hand_want, TRUE, self);
	start_org = trace_endpos;

	m = spawn ();
	m.classname = "milky";
	m.milky_owner = self;
	self.milky_active = m;
	m.owner = self;		// passes through her shooter during the palm emergence, then becomes world
	m.movetype = MOVETYPE_NOCLIP;
	m.solid = SOLID_BBOX;
	m.effects = EF_FULLBRIGHT;
	m.takedamage = DAMAGE_AIM;
	m.health = MILKY_HEALTH;
	m.max_health = MILKY_HEALTH;
	m.milky_hp = MILKY_HEALTH;
	m.dodge_finished = time + 999999;		// SpawnBlood: bullets puff off her (she spurts milk instead, Milky_Damage)
	m.milky_dir = launch_dir;
	m.milky_born = time;
	m.milky_seen = time;
	m.milky_scan = time + 0.2;
	m.milky_from = start_org;
	m.milky_to = end_org;
	m.milky_emerged = FALSE;
	m.milky_last = end_org;
	m.milky_lastt = time;
	m.milky_phase = random () * 6.28;
	m.milky_drip = time + 0.08;
	m.milky_ptrail = time + 0.28;
	m.scale = 2.1;
	m.customizeentityforclient = Milky_Customize;
	m.touch = Milky_Touch;
	m.think = Milky_Think;
	m.nextthink = time + 0.02;
	setmodel (m, "progs/pinklady.md3");
	setsize (m, '-14 -14 -24', '14 14 20');
	setorigin (m, start_org);
	m.velocity = (end_org - start_org) * (1.375 / MILKY_EMERGE);
	// quieter single-channel song, only audible when kinda close (MILKY_SONG_ATTN)
	Milky_Snd (m, CHAN_VOICE, "milky/song.ogg", MILKY_SONG_VOL, MILKY_SONG_ATTN);
	milky_count = milky_count + 1;
};

// ---------------------------------------------------------------- every player, every frame

void() Milky_Crumb =
{
	local entity c;

	c = spawn ();
	c.classname = "milk_crumb";
	c.owner = self;
	c.milk_t = time;
	c.movetype = MOVETYPE_NONE;
	c.solid = SOLID_NOT;
	setorigin (c, self.origin);
	c.think = SUB_Remove;
	c.nextthink = time + MILK_CRUMB_LIFE;
	self.milk_crumbat = self.origin;
	self.milk_crumbt = time;
};

// from W_WeaponFrame: breadcrumbs for the ladies to follow, and sliding on milk. On a puddle the ground hardly grips:
// what the engine's friction and your own pushing changed since last frame only counts for MILK_GRIP of it
void() Milky_PlayerFrame =
{
	local vector h, p, d;

	if (self.health <= 0 || self.solid == SOLID_NOT)
	{
		self.milk_st = 0;
		self.milk_scr = 0;
		self.milk_freeze = 0;
		self.milky_wind = 0;
		self.milk_slip = FALSE;
		self.milk_v = self.velocity;
		return;
	}
	if (self.milky_wind && time >= self.milky_wind)
	{
		self.milky_wind = 0;
		Milky_Launch ();
	}
	self.milk_st = 0;
	if (self.milk_scr && time < self.milk_scr + 6)
		self.milk_st = ceil ((self.milk_scr + 6 - time) * 10);		// 60 just hit, down to 0
	if (time < self.milk_freeze)		// frozen in the blast: you hang where you are
	{
		self.velocity_x = 0;
		self.velocity_y = 0;
		if (self.velocity_z > 0)
			self.velocity_z = 0;
		self.milk_v = VEC_ORIGIN;
	}
	// one crumb per 48 units walking; a jetpacker doing 1000+ u/s drops one per 160, or a few fliers fill the edicts
	if (milky_count > 0 && vlen (self.origin - self.milk_crumbat) > 48 + 112 * (vlen (self.velocity) > 600))
		Milky_Crumb ();
	if (milk_count > 0 && (self.flags & FL_ONGROUND) && Milk_Under (self))
		self.milk_last = time;
	if (milk_count > 0 && (self.flags & FL_ONGROUND) && time < self.milk_last + MILK_COAST)
	{
		if (self.milk_slip)
		{
			h = self.velocity;
			h_z = 0;
			p = self.milk_v;
			p_z = 0;
			d = h - p;
			if (vlen (d) < MILK_PASS)
			{
				h = p * (1 - MILK_DRAG * frametime) + d * MILK_GRIP;
				if (vlen (h) > MILK_TOPSPEED)
					h = normalize (h) * MILK_TOPSPEED;
				self.velocity_x = h_x;
				self.velocity_y = h_y;
			}
			if (time > self.milk_fx && vlen (h) > 120)
			{
				pointparticles (particleeffectnum ("milk_skid"), self.origin - '0 0 22', h * 0.3, 1);
				self.milk_fx = time + 0.12;
				if (cvar ("milky_debug"))
					bprint ("milky: ", self.netname, " sliding at ", ftos (floor (vlen (h))), "\n");
			}
		}
		self.milk_slip = TRUE;
	}
	else
		self.milk_slip = FALSE;
	self.milk_v = self.velocity;
};

// ---------------------------------------------------------------- the held model

// every think of the view model entity (custom_effects.qc), after it has set its model, frame and alpha.
// progs/v_milky.md3 uses per-frame .skin files (0..95 idle A, 96..191 idle B, 192..247 shot windup & open-hand follow-through)
// so frame timing is 100% deterministic from QuakeC with zero shader-clock drift or vertex interpolation jumps.
void(entity vm) Milky_ViewFrame =
{
	local entity p;
	local float u, k, ease, idx, step, total_steps, sw1, sw2, spd;

	p = vm.owner;
	if (p.weapon != IT_SUPER_NAILGUN)
	{
		if (vm.mv_on)
		{
			vm.skin = 0;		// the next gun's model has its own skins
			vm.origin = '0 0 0';
			vm.angles = '0 0 0';
		}
		vm.mv_on = FALSE;
		return;
	}
	vm.frame = 0;
	vm.origin = '0 0 0';
	vm.angles = '0 0 0';
	if (!vm.mv_on)		// just drawn: raise smoothly from below unless a lady is already out
	{
		vm.mv_on = TRUE;
		if (Milky_Out (p) || time < p.milky_hide)
		{
			vm.mv_state = 2;
			vm.alpha = -1;
			return;
		}
		vm.mv_state = 0;
		vm.mv_clip = (random () < 0.5);
		vm.mv_t = time;
		vm.mv_raise = time + MILKY_RAISE;
	}
	if (p.milky_wind > 0)		// winding up & uncurling fingers (mvm_f_00..35, skins 192..227)
	{
		vm.mv_state = 2;
		vm.mv_raise = 0;
		u = (time - p.milky_fire_t) / MILKY_WIND;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * MILKY_WIND_FRAMES);
		vm.skin = MILKY_SKIN_F + idx;
		if (u < 0.38)		// brief cock-back anticipation before hurling her forward
		{
			k = sin ((u / 0.38) * 3.14159);
			vm.origin_x = -1.2 * k;
			vm.origin_y = -1.2 * k;
			vm.origin_z = -1.8 * k;
			vm.angles_x = 2.5 * k;
			vm.angles_z = 2.2 * k;
		}
		else		// smooth forward, inward, and upward toss into the release point
		{
			k = (u - 0.38) / 0.62;
			ease = k * k * (3 - 2 * k);
			vm.origin_x = 2.6 * ease;
			vm.origin_y = 4.2 * ease;
			vm.origin_z = 2.2 * ease;
			vm.angles_x = -4.0 * ease;
		}
		return;
	}
	if (vm.mv_state == 2 && p.milky_threw > 0 && time < p.milky_threw + MILKY_FLYOUT)
	{
		// she has just left the palm: empty open hand follows through and glides smoothly off the bottom
		u = (time - p.milky_threw) / MILKY_FLYOUT;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = MILKY_WIND_FRAMES + floor (u * MILKY_FOLLOW_FRAMES);
		vm.skin = MILKY_SKIN_F + idx;
		ease = u * u;
		vm.origin_x = 2.6 * (1 - u);
		vm.origin_y = 4.2 * (1 - 0.6 * u);
		vm.origin_z = 2.2 - 16.0 * ease;
		vm.angles_x = -4.0 + 12.0 * ease;
		return;
	}
	if (Milky_Out (p) || time < p.milky_hide)
	{
		// she has been thrown and is out there: only one at a time, so there is nothing in the hand
		vm.mv_state = 2;
		vm.alpha = -1;
		return;
	}
	if (vm.mv_state == 2)		// she is gone (exploded): raise a fresh one smoothly into view on the other idle clip
	{
		vm.mv_state = 0;
		vm.mv_clip = 1 - vm.mv_clip;
		vm.mv_t = time;
		vm.mv_raise = time + MILKY_RAISE;
	}
	total_steps = 2 * MILKY_IDLE_FRAMES - 2;
	step = floor ((time - vm.mv_t) * MILKY_IDLE_FPS);
	if (step < 0)
		step = 0;
	if (step >= total_steps)		// finished one smooth forward-and-back cycle: switch to the other idle at neutral pose
	{
		vm.mv_clip = 1 - vm.mv_clip;
		vm.mv_t = time;
		step = 0;
	}
	if (step < MILKY_IDLE_FRAMES)
		idx = step;
	else
		idx = total_steps - step;
	vm.skin = idx + vm.mv_clip * MILKY_SKIN_B;

	// gentle organic breathing & walk sway
	sw1 = sin (time * 2.1);
	sw2 = cos (time * 1.4);
	spd = vlen (p.velocity);
	if (spd > 320)
		spd = 320;
	k = 0.25 + 0.55 * (spd / 320);
	sw1 = sw1 * k;
	sw2 = sw2 * k;
	vm.origin_y = sw2 * 0.45;
	vm.origin_z = sw1 * 0.55;
	if (time < vm.mv_raise)
	{
		u = 1 - (vm.mv_raise - time) / MILKY_RAISE;
		if (u < 0)
			u = 0;
		ease = 1 - (1 - u) * (1 - u);
		vm.origin_z = vm.origin_z - 22.0 * (1 - ease);
	}
};
