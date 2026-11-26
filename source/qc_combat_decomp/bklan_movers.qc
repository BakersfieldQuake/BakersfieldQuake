#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BKLAN3 MOVERS (owner's review of bklan2, 2026-10-31 16:03): things that drive and fly round the map by themselves

	bk_cruiser	a vehicle that drives the route of bk_route points (key "target" = the first one) for ever.
				"cnt" 1 = the hot pink supercar ("It's not pink"): fast, plays music while someone rides it, and now and
				then says "it's not pink!" in a high voice. "cnt" 2 = the Podracer Sky-Chariot: slower.
				You can jump on top and ride it. It runs you over if you stand in its way.
	bk_route	a point of the route: "target" = the next one, "speed" = a multiplier for the leg that starts here
				(0.4 through the park: "slowly driving through this park")
	bk_trashcan	shoot it: it explodes in fire and shoots straight up into the sky (and comes back later)

How they move: the vehicle is a MOVETYPE_PUSH entity with a SOLID_BBOX (DarkPlaces pushes and carries players with a
bbox pusher, and moves it through the world without colliding), drawn with its own model. A pusher thinks on
.ltime, not time. The box is square (a box cannot turn with the model): the model's length and width averaged.
================
*/

float	BK_PINK		= 1;
float	BK_POD		= 2;

float	BK_PINK_SPEED	= 560;		// units a second: "this car goes quite fast"
float	BK_POD_SPEED	= 300;
float	BK_TURN			= 120;		// degrees a second the cruisers turn at most
float	BK_MUSIC_LEN	= 19.2;		// sound/bklan/pinkcar.wav (make_bklan_sounds.py)

.entity	bk_goal;		// mover: the route point it is heading for
.float	bk_kind;
.float	bk_spd;			// mover: its top speed
.float	bk_mul;			// mover: speed multiplier of the current leg
.float	bk_music;		// pink car: when the music ends (0: not playing)
.float	bk_voice;		// pink car: next "it's not pink"
.vector	bk_home;		// trash can: where it stands
.float	bk_fr0;			// mover: first frame of the animation it plays
.float	bk_frn;			// mover: number of frames in it
.float	bk_fps;

// the route points only have to exist; legacy biplane entities in compiled BSPs remove themselves cleanly
void() bk_route = { };
void() bk_landing = { remove (self); };
void() bk_flyer = { remove (self); };

float(float a) BK_Norm =
{
	a = a - 360 * floor (a / 360);
	if (a > 180)
		a = a - 360;
	return a;
};

// play frames bk_fr0 .. bk_fr0 + bk_frn - 1
void() BK_Animate =
{
	local float f;

	f = floor (time * self.bk_fps);
	self.frame = self.bk_fr0 + f - self.bk_frn * floor (f / self.bk_frn);
};

// it ran into someone standing in the road: they are knocked flying, and hurt
void() BK_Blocked =
{
	local vector d;

	if (!other.takedamage)
		return;
	d = other.origin - self.origin;
	d_z = 0;
	d = normalize (d);
	if (d == VEC_ORIGIN)
		d = '1 0 0';
	other.velocity = d * 500 + '0 0 300';
	other.flags = other.flags - (other.flags & FL_ONGROUND);
	// blocked fires every push frame: someone pinned against a wall was shredded (Traffic_Blocked rate-limits the same way)
	if (time < other.veh_hit_t)
		return;
	other.veh_hit_t = time + 0.65;
	T_Damage (other, self, self, 15);
};

// TRUE while a player stands on it
float() BK_Ridden =
{
	local entity p;

	p = bm_player_head;
	while (p)
	{
		if (p.health > 0 && p.groundentity == self)
			return TRUE;
		p = p.bm_player_next;
	}
	return FALSE;
};

// turn the box toward yaw 'want', at most BK_TURN a second (the riders turn with it)
void(float want, float rate) BK_Steer =
{
	local float d;

	d = BK_Norm (want - self.angles_y);
	if (d > rate)
		d = rate;
	if (d < 0 - rate)
		d = 0 - rate;
	self.avelocity = '0 1 0' * (d * 10);		// one think (0.1 s) to get there
};

// ---------------------------------------------------------------- cruisers

void() BK_CruiserThink =
{
	local vector d;
	local float dist, spd, n;

	self.nextthink = self.ltime + 0.1;
	BK_Animate ();
	if (!self.bk_goal)
	{
		self.velocity = VEC_ORIGIN;
		return;
	}
	d = self.bk_goal.origin - self.origin;
	dist = vlen (d);
	spd = self.bk_spd * self.bk_mul;
	if (dist < spd * 0.12 + 8)
	{
		self.bk_mul = self.bk_goal.speed;
		if (self.bk_mul <= 0)
			self.bk_mul = 1;
		if (self.bk_goal.target == "")
			self.bk_goal = world;		// the route ends here: find (..., "") would match the first entity with no name (a player)
		else
			self.bk_goal = find (world, targetname, self.bk_goal.target);
		if (!self.bk_goal)
			return;
		dprint (strcat ("bk: cruiser ", ftos (self.bk_kind), " -> ", self.bk_goal.targetname, " at ", vtos (self.origin), "\n"));
		d = self.bk_goal.origin - self.origin;
		dist = vlen (d);
	}
	n = vectoyaw (d);
	// slow down for a sharp corner ahead: the box turns at BK_TURN a second
	if (fabs (BK_Norm (n - self.angles_y)) > 50)
		spd = spd * 0.35;
	self.velocity = normalize (d) * spd;
	BK_Steer (n, BK_TURN * 0.1);

	if (self.bk_kind == BK_PINK)
	{
		// the music plays while someone rides it, from the car (everyone near hears it)
		if (BK_Ridden ())
		{
			if (time >= self.bk_music)
			{
				if (!self.bk_music)
				{
					sound (self, CHAN_ITEM, "bklan/notpink.wav", 1, ATTN_NORM);		// hopping on
					self.bk_voice = time + 60 + random () * 60;
				}
				sound (self, CHAN_VOICE, "bklan/pinkcar.wav", 1, 0.6);
				self.bk_music = time + BK_MUSIC_LEN;
				dprint ("bk: pink car music on\n");
			}
		}
		else if (self.bk_music && time >= self.bk_music - BK_MUSIC_LEN + 2)
		{
			sound (self, CHAN_VOICE, "misc/null.wav", 1, ATTN_NORM);		// nobody on it: the music stops
			self.bk_music = 0;
		}
		if (time >= self.bk_voice)		// every few minutes, a high voice: "it's not pink!"
		{
			sound (self, CHAN_ITEM, "bklan/notpink.wav", 1, 0.5);
			self.bk_voice = time + 90 + random () * 90;
		}
	}
};

void() bk_cruiser =
{
	local entity g;

	if (BM_NoMapTraffic ())		// clear streets unless bm_traffic 1 (2026-11-26)
	{
		remove (self);
		return;
	}
	self.bk_kind = self.cnt;
	if (self.bk_kind != BK_POD)
	{
		self.bk_kind = BK_PINK;
		precache_model ("progs/pink_supercar.md3");
		precache_sound ("bklan/pinkcar.wav");
		precache_sound ("bklan/notpink.wav");
		precache_sound ("misc/null.wav");
	}
	else
		precache_model ("progs/skyveh_v3.md3");
	self.classname = "bk_cruiser";
	self.movetype = MOVETYPE_PUSH;
	self.solid = SOLID_BBOX;
	self.blocked = BK_Blocked;
	if (self.bk_kind == BK_PINK)
	{
		setmodel (self, "progs/pink_supercar.md3");
		setsize (self, '-70 -70 0', '70 70 50');
		self.bk_spd = BK_PINK_SPEED;
		self.bk_fr0 = 16;		// cruise_drive: spinning wheels
		self.bk_frn = 16;
		self.bk_fps = 16;
		self.bk_voice = time + 30 + random () * 60;
	}
	else
	{
		setmodel (self, "progs/skyveh_v3.md3");		// its wheels hang 24 units under the body: the box starts there
		setsize (self, '-105 -105 24', '105 105 142');
		self.bk_spd = BK_POD_SPEED;
		self.bk_fr0 = 0;		// fly_cruise: rotors and flapping
		self.bk_frn = 16;
		self.bk_fps = 12;
	}
	setorigin (self, self.origin);
	self.bk_mul = 1;
	g = world;
	if (self.target != "")
		g = find (world, targetname, self.target);
	self.bk_goal = g;
	if (g)
		self.angles_y = vectoyaw (g.origin - self.origin);
	self.think = BK_CruiserThink;
	self.nextthink = self.ltime + 0.5 + random () * 0.2;
};

// ---------------------------------------------------------------- the trash can

void() BK_TrashBack =
{
	// do not drop the solid can onto someone standing on its spot: try again in a second
	tracebox (self.bk_home, '-20 -20 0', '20 20 50', self.bk_home, FALSE, self);
	if (trace_ent != world)
	{
		self.think = BK_TrashBack;
		self.nextthink = time + 1;
		return;
	}
	setmodel (self, "progs/bklan/trashcan.md3");		// a green slatted park drum, 4 ft tall (build_trashcan.py)
	self.scale = 1;
	self.movetype = MOVETYPE_NONE;
	self.solid = SOLID_BBOX;
	setsize (self, '-20 -20 0', '20 20 50');
	setorigin (self, self.bk_home);
	self.velocity = VEC_ORIGIN;
	self.avelocity = VEC_ORIGIN;
	self.angles = '0 0 0';
	self.traileffectnum = 0;
	self.effects = self.effects - (self.effects & EF_DIMLIGHT);
	self.takedamage = DAMAGE_AIM;
	self.health = 25;
	self.enemy = world;		// the last life's shooter gets no credit for this one
	self.think = SUB_Null;
	self.nextthink = 0;
};

// up in the sky: the second bang, and it is gone for a while
void() BK_TrashSky =
{
	pointparticles (particleeffectnum ("TE_EXPLOSION"), self.origin, VEC_ORIGIN, 1);
	pointparticles (particleeffectnum ("pk_boom"), self.origin, VEC_ORIGIN, 1);
	sound (self, CHAN_AUTO, "weapons/r_exp3.wav", 1, 0.3);
	setmodel (self, "");
	self.movetype = MOVETYPE_NONE;
	self.velocity = VEC_ORIGIN;
	self.traileffectnum = 0;
	self.effects = self.effects - (self.effects & EF_DIMLIGHT);
	self.think = BK_TrashBack;
	self.nextthink = time + 30;
};

// the blast, on a think of its own (BK_TrashDie)
void() BK_TrashBlow =
{
	pointparticles (particleeffectnum ("TE_EXPLOSION"), self.origin + '0 0 20', VEC_ORIGIN, 1);
	sound (self, CHAN_AUTO, "weapons/r_exp3.wav", 1, ATTN_NORM);
	sound (self, CHAN_WEAPON, "weapons/rocket1i.wav", 1, 0.5);
	if (!self.enemy || self.enemy.classname != "player")
		self.enemy = self;
	T_RadiusDamage (self, self.enemy, 40, self);
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NOCLIP;
	self.velocity = '0 0 1100';
	self.avelocity = '0 400 120';
	self.traileffectnum = particleeffectnum ("TR_ROCKET");
	self.effects = self.effects | EF_DIMLIGHT;
	self.think = BK_TrashSky;
	self.nextthink = time + 2.6;
};

// shot: a fireball, and up it goes, burning. Not inside the T_RadiusDamage that killed it (its own would rewrite the .chain
// list that loop walks), and the kill is the killer's: a one-shot kill never ran BK_TrashPain
void() BK_TrashDie =
{
	if (!self.takedamage)
		return;
	self.takedamage = DAMAGE_NO;
	if (damage_attacker != world && damage_attacker != self)
		self.enemy = damage_attacker;
	self.think = BK_TrashBlow;
	self.nextthink = time;
};

void(entity attacker, float take) BK_TrashPain =
{
	self.enemy = attacker;
};

void() bk_trashcan =
{
	precache_model ("progs/bklan/trashcan.md3");
	precache_sound ("weapons/r_exp3.wav");
	precache_sound ("weapons/rocket1i.wav");
	self.classname = "bk_trashcan";
	self.bk_home = self.origin;
	self.th_die = BK_TrashDie;
	self.th_pain = BK_TrashPain;
	BK_TrashBack ();
};

// ---------------------------------------------------------------- test aid (sv_cheats 1)
// impulse 77 puts you on the roof of the pink car, 78 on the Podracer (called every frame from Jetpack_Frame)
void() BK_Impulse =
{
	local entity e;

	BKTV_Test ();
	if (self.impulse < 77 || self.impulse > 78 || !autocvar_sv_cheats)
		return;
	e = find (world, classname, "bk_cruiser");
	while (e && e.bk_kind != self.impulse - 76)
		e = find (e, classname, "bk_cruiser");
	self.impulse = 0;
	if (!e)
		return;
	setorigin (self, e.origin + '0 0 1' * (e.maxs_z + 25));		// feet a unit over its roof
	self.velocity = VEC_ORIGIN;
	dprint (strcat ("bk: put on ", e.classname, " at ", vtos (e.origin), "\n"));
};
