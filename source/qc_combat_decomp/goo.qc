#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE GOO GUN (see goo_defs.qc for the rules and numbers)

Hooks (patch_goo_combat.py): W_Attack fires Goo_Fire for IT_SHOTGUN, W_WeaponFrame runs Goo_PlayerFrame,
T_Damage runs damage through Goo_Damage, and the obituary checks goo_inflicting.
================
*/

void() Goo_Precache =
{
	precache_model ("progs/v_googun.md3");
	precache_model ("progs/p_googun.md3");
	precache_model ("progs/goo.md3");
	precache_sound ("weapons/goofire.wav");
	precache_sound ("weapons/goosplat.wav");
	precache_sound ("weapons/goopop.wav");
	precache_sound ("weapons/goostick.wav");
};

void(entity e, float chan, string samp, float vol, float pitch) Goo_Snd =
{
	sound7 (e, chan, samp, vol, ATTN_NORM, SNDSPD * pitch);
};

// ---------------------------------------------------------------- blobs

void() Goo_Remove =
{
	goo_count = goo_count - 1;
	remove (self);
};

void() Goo_ChunkThink =
{
	if (time > self.goo_t)		// lie there a while, then shrink away
		self.scale = self.scale - 0.07;
	if (self.scale <= 0.1)
	{
		goo_chunk_n = goo_chunk_n - 1;
		remove (self);
		return;
	}
	self.nextthink = time + 0.05;
};

// lumps of goo that bounce off and lie around for a few seconds
void(vector org) Goo_Chunks =
{
	local entity c;
	local float i;

	i = 0;
	while (i < GOO_CHUNKS && goo_chunk_n < 48)		// a room full of goo guns would otherwise pop hundreds of lumps a second
	{
		goo_chunk_n = goo_chunk_n + 1;
		c = spawn ();
		c.classname = "goo_chunk";
		c.movetype = MOVETYPE_BOUNCE;
		c.solid = SOLID_NOT;
		c.frame = 1;		// the small glob
		c.scale = 0.7 + random () * 0.7;
		c.angles = randomvec () * 180;
		c.avelocity = randomvec () * 500;
		c.velocity = randomvec () * 260 + '0 0 220';
		c.goo_t = time + 2.5 + random () * 2;
		c.think = Goo_ChunkThink;
		c.nextthink = time + 0.05;
		setmodel (c, "progs/goo.md3");
		setsize (c, VEC_ORIGIN, VEC_ORIGIN);
		setorigin (c, org + randomvec () * GOO_HALF * 0.6);
		i = i + 1;
	}
};

// shot apart, or made room for a newer one
void() Goo_Pop =
{
	if (self.goo_state == 5)
		return;		// two hits in one frame: popped already
	self.goo_state = 5;
	self.takedamage = DAMAGE_NO;
	sendParticle ("goo_burst", self.origin, VEC_ORIGIN, 1, 0);
	pointparticles (particleeffectnum ("goo_snow"), self.origin, VEC_ORIGIN, 1);
	Goo_Chunks (self.origin);
	Goo_Snd (self, CHAN_AUTO, "weapons/goopop.wav", 0.5, 0.85 + random () * 0.3);
	Goo_Remove ();
};

// every hit on a blob chips debris and snow off the side that was shot
void(entity b, entity from) Goo_HitFX =
{
	local vector dir;

	if (time < b.goo_fx)
		return;
	b.goo_fx = time + 0.06;
	dir = normalize (from.origin + from.view_ofs - b.origin);
	if (dir == VEC_ORIGIN)
		dir = '0 0 1';
	pointparticles (particleeffectnum ("goo_chip"), b.origin + dir * GOO_HALF * 0.85, dir, 1);
};

// TRUE if a live player or monster is inside the blob's box
float() Goo_Overlapping =
{
	local entity e;
	local vector lo, hi;

	lo = self.origin - '1 1 1' * GOO_HALF;
	hi = self.origin + '1 1 1' * GOO_HALF;
	e = findradius (self.origin, GOO_HALF + 48);
	while (e)
	{
		if ((e.flags & (FL_CLIENT | FL_MONSTER)) && e.health > 0 && e.solid != SOLID_NOT)
		{
			if (e.absmin_x < hi_x && e.absmax_x > lo_x && e.absmin_y < hi_y && e.absmax_y > lo_y
				&& e.absmin_z < hi_z && e.absmax_z > lo_z)
				return TRUE;
		}
		e = e.chain;
	}
	return FALSE;
};

// a blob that finished swelling on top of someone lifts them onto its top (the box is already where they stand), if they
// fit there: shooting at your own feet climbs, a blob that grows under an enemy carries them up. TRUE if all were lifted
float() Goo_LiftOverlapping =
{
	local entity e;
	local vector lo, hi, o;

	lo = self.origin - '1 1 1' * GOO_HALF;
	hi = self.origin + '1 1 1' * GOO_HALF;
	e = findradius (self.origin, GOO_HALF + 48);
	while (e)
	{
		if ((e.flags & (FL_CLIENT | FL_MONSTER)) && e.health > 0 && e.solid != SOLID_NOT)
		{
			if (e.absmin_x < hi_x && e.absmax_x > lo_x && e.absmin_y < hi_y && e.absmax_y > lo_y
				&& e.absmin_z < hi_z && e.absmax_z > lo_z)
			{
				o = e.origin;
				o_z = hi_z - e.mins_z + 1;
				tracebox (o, e.mins, e.maxs, o, FALSE, e);
				if (trace_startsolid)
					return FALSE;		// no room up there: it stays soft and pops
				setorigin (e, o);
				if (e.velocity_z < 0)
					e.velocity_z = 0;
			}
		}
		e = e.chain;
	}
	return TRUE;
};

void() Goo_BlobThink =
{
	local float t;

	self.nextthink = time + 0.05;
	t = time - self.goo_t;
	if (self.goo_state == 1)		// swelling out of the glob: frames 2 3 4 5 then 0 (DarkPlaces lerps between them)
	{
		if (t < 0.05)
			self.frame = 2;
		else if (t < 0.1)
			self.frame = 3;
		else if (t < 0.16)
			self.frame = 4;
		else if (t < 0.22)
			self.frame = 5;
		else
		{
			self.frame = 0;
			self.goo_t = time;
			if (Goo_Overlapping () && !Goo_LiftOverlapping ())
				self.goo_state = 3;
			else
			{
				self.goo_state = 2;
				self.solid = SOLID_BBOX;
				setorigin (self, self.origin);		// relink with the new solid type
			}
		}
		return;
	}
	if (self.goo_state == 3)		// someone is inside: stay soft, and pop if they do not get out
	{
		if (!Goo_Overlapping ())
		{
			self.goo_state = 2;
			self.solid = SOLID_BBOX;
			setorigin (self, self.origin);
		}
		else if (t > GOO_OVERLAP)
			Goo_Pop ();
		return;
	}
	if (self.goo_state == 2)
	{
		if (time > self.goo_born + GOO_LIFE)
		{
			self.goo_state = 4;
			self.goo_t = time;
			self.solid = SOLID_NOT;
			self.takedamage = DAMAGE_NO;
			setorigin (self, self.origin);
		}
		else
			self.nextthink = time + 0.25;
		return;
	}
	// 4: shrinking away
	self.scale = GOO_SCALE * (1 - t / 0.5);
	if (self.scale <= 0.05)
		Goo_Remove ();
};

// the oldest solid blob pops to keep the count under GOO_MAX
void() Goo_MakeRoom =
{
	local entity e, old;

	if (goo_count < GOO_MAX)
		return;
	old = world;
	e = find (world, classname, "goo");
	while (e)
	{
		if (e.goo_state == 2 && (!old || e.goo_born < old.goo_born))
			old = e;
		e = find (e, classname, "goo");
	}
	if (old)
	{
		self = old;		// callers keep their own self in a local
		sendParticle ("goo_burst", self.origin, VEC_ORIGIN, 1, 0);		// made room quietly: no lumps, so a full cap doesn't cost edicts per shot
		Goo_Remove ();
	}
};

void(vector org, entity who) Goo_Blob =
{
	local entity b, oself;

	oself = self;
	Goo_MakeRoom ();
	self = oself;

	b = spawn ();
	b.classname = "goo";
	b.owner = world;		// solid to everyone, the shooter too
	b.enemy = who;
	b.movetype = MOVETYPE_NONE;
	b.solid = SOLID_NOT;	// soft while it swells
	b.takedamage = DAMAGE_AIM;
	b.health = GOO_HEALTH;
	b.max_health = GOO_HEALTH;
	b.th_die = Goo_Pop;
	b.dodge_finished = time + 999999;		// SpawnBlood: bullets puff off goo instead of drawing blood
	b.goo_born = time;
	b.goo_state = 1;
	b.goo_t = time;
	b.frame = 1;
	b.scale = GOO_SCALE;
	b.alpha = 1;		// solid, never see-through
	b.angles_x = random () * 360;
	b.angles_y = random () * 360;
	b.angles_z = random () * 360;
	b.think = Goo_BlobThink;
	b.nextthink = time + 0.05;
	setmodel (b, "progs/goo.md3");
	setsize (b, '-1 -1 -1' * GOO_HALF, '1 1 1' * GOO_HALF);
	setorigin (b, org);
	goo_count = goo_count + 1;
};

// ---------------------------------------------------------------- gummed-up players

void() Goo_StuckThink =
{
	local entity p;

	p = self.owner;
	if (p.goo_stuck != self || p.health <= 0 || time > p.goo_slow)
	{
		sendParticle ("goo_puff", p.origin, VEC_ORIGIN, 1, 0);
		if (p.goo_stuck == self)
			p.goo_stuck = world;
		remove (self);
		return;
	}
	if (self.frame != 0)
		self.frame = self.frame + 1;
	if (self.frame > 5)
		self.frame = 0;
	self.nextthink = time + 0.06;
};

void(entity p) Goo_StickTo =
{
	local entity g;

	if (p.bm_prot_t > time)
		return;		// spawn protection: no crawling out of the spawn
	if (time >= p.goo_slow)
	{
		if (time < p.goo_slow + 2)
			return;		// just got free: a stream of goo can't chain-lock someone
		p.goo_slow = time + GOO_SLOW_TIME;
	}
	if (p.goo_stuck)
		return;
	g = spawn ();
	g.classname = "goo_stuck";
	g.owner = p;
	g.movetype = MOVETYPE_NONE;
	g.solid = SOLID_NOT;
	g.scale = 0.25;		// goo.md3 is the big grown blob: shrink it to wrap a player
	g.frame = 2;
	g.angles_y = random () * 360;
	g.nodrawtoclient = p;		// the victim would only see the inside of it
	setmodel (g, "progs/goo.md3");
	setattachment (g, p, "");
	setorigin (g, '0 0 2');
	g.think = Goo_StuckThink;
	g.nextthink = time + 0.06;
	p.goo_stuck = g;
	if (p.flags & FL_CLIENT)
		centerprint (p, "GOOED!\n");
};

// every frame from W_WeaponFrame: gummed-up players crawl and cannot jump
void() Goo_PlayerFrame =
{
	local vector v;
	local float z;

	if (self.goo_slow <= time)
		return;
	v = self.velocity;
	z = v_z;
	v_z = 0;
	if (vlen (v) > GOO_SLOW_SPEED)
		v = normalize (v) * GOO_SLOW_SPEED;
	if (z > 90)
		z = 90;
	v_z = z;
	self.velocity = v;
};

// T_Damage, before armour: explosions tear goo apart
float(entity targ, entity inflictor, float damage) Goo_Damage =
{
	if (targ.classname != "goo")
		return damage;
	Goo_HitFX (targ, inflictor);
	if (inflictor.classname == "missile" || inflictor.classname == "grenade" || inflictor.classname == "proximity_grenade")
		return damage * GOO_EXPLOSIVE;
	return damage;
};

// ---------------------------------------------------------------- the shot

void() Goo_ShotTouch =
{
	local vector dir, n, org, d;

	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	dir = normalize (self.velocity);
	if (dir == VEC_ORIGIN)
		dir = '0 0 -1';

	if (other.takedamage && other.classname != "goo" && (other.flags & (FL_CLIENT | FL_MONSTER)))
	{
		goo_inflicting = TRUE;
		T_Damage (other, self, self.owner, GOO_HIT_DAMAGE);
		goo_inflicting = FALSE;
		if (other.health > 0 && (other.flags & FL_CLIENT))
			Goo_StickTo (other);
		sendParticle ("goo_splat", self.origin, VEC_ORIGIN, 1, 0);
		if (time >= self.owner.goo_snd_t)
		{
			self.owner.goo_snd_t = time + 0.25;
			Goo_Snd (other, CHAN_AUTO, "weapons/goostick.wav", 0.5, 0.9 + random () * 0.2);
		}
		remove (self);
		return;
	}

	if (other.classname == "goo")
	{
		// stack on the blob it hit: out of the face it struck (top, or a side), so towers and ladders come out square
		d = self.origin - other.origin;
		if (fabs (d_z) >= fabs (d_x) && fabs (d_z) >= fabs (d_y))
		{
			n = '0 0 1';
			if (d_z < 0)
				n_z = -1;
			d_z = 0;
		}
		else if (fabs (d_x) >= fabs (d_y))
		{
			n = '1 0 0';
			if (d_x < 0)
				n_x = -1;
			d_x = 0;
		}
		else
		{
			n = '0 1 0';
			if (d_y < 0)
				n_y = -1;
			d_y = 0;
		}
		org = other.origin + n * GOO_HALF * GOO_STACK + d * 0.5;
	}
	else
	{
		traceline (self.origin - dir * 24, self.origin + dir * 24, TRUE, self);
		if (trace_fraction < 1)
		{
			n = trace_plane_normal;
			org = trace_endpos;
		}
		else
		{
			n = dir * -1;
			org = self.origin;
		}
		org = org + n * GOO_HALF * GOO_SINK;		// mostly sunk into the surface, like it splatted there
	}
	sendParticle ("goo_splat", org, VEC_ORIGIN, 1, 0);
	if (time >= self.owner.goo_snd_t)
	{
		self.owner.goo_snd_t = time + 0.25;
		Goo_Snd (self, CHAN_AUTO, "weapons/goosplat.wav", 0.5, 0.85 + random () * 0.3);
	}
	Goo_Blob (org, self.owner);
	remove (self);
};

// W_Attack with the Goo Gun out (the player_shot animation is already running)
void() Goo_Fire =
{
	local entity g;
	local vector dir, org;

	Goo_Snd (self, CHAN_WEAPON, "weapons/goofire.wav", 0.7, 0.93 + random () * 0.14);
	self.punchangle_x = -1.6;
	self.ammo_shells = self.ammo_shells - 1;
	self.currentammo = self.ammo_shells;

	makevectors (self.v_angle);
	dir = aim (self, 1000);
	dir = normalize (dir + v_right * crandom () * 0.012 + v_up * crandom () * 0.012);
	traceline (self.origin + '0 0 16', self.origin + '0 0 16' + v_forward * 18 + v_right * 6 - v_up * 5, TRUE, self);
	org = trace_endpos - v_forward * 2;

	g = spawn ();
	g.owner = self;
	g.classname = "gooshot";
	g.movetype = MOVETYPE_TOSS;
	g.solid = SOLID_BBOX;
	g.gravity = GOO_GRAVITY;
	g.velocity = dir * GOO_SPEED + v_up * 40;
	g.avelocity_x = crandom () * 400;
	g.avelocity_y = crandom () * 400;
	g.angles_y = random () * 360;
	g.frame = 1;		// the small glob
	g.touch = Goo_ShotTouch;
	g.think = SUB_Remove;
	g.nextthink = time + 6;
	setmodel (g, "progs/goo.md3");
	setsize (g, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (g, org);
};
