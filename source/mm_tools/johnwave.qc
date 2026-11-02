// ---------------------------------------------------------------- 4. JOHN WAVE GRENADE
// From MegaKartArena. Hold fire: John sits in your hand (his hair sways faster the longer you hold). Let go: the
// throw plays (0.8 s) and John's head (a 3D model) flies out slowly, spinning, chattering. Where it lands a tidal wave spreads
// out and lifts everyone it passes into the air for a few seconds. It is deliberately bad at killing: the point is
// where everyone ends up. Compiled after friends.qc (Combat+ only).

float	JW_SPEED		= 520;		// the head: slower than a rocket
float	JW_RADIUS		= 420;		// how far the wave spreads
float	JW_WAVE_SPEED	= 220;		// units a second
float	JW_FLOAT		= 4;		// seconds in the air
float	JW_RISE			= 170;		// upward speed at the start; with low gravity it is a slow rise, then a hang
float	JW_OUT			= 120;		// pushed away from the impact
float	JW_DIRECT		= 30;
float	JW_BLAST		= 40;
float	JW_THROW_T		= 0.8;		// release to the head leaving

void() JW_Precache =
{
	precache_model ("progs/johnhead3d.md3");
	precache_model ("progs/fr_johnhand.spr32");
	precache_model ("progs/jw_wave.md3");
	precache_sound ("john/jwthrow.wav");
	precache_sound ("john/jv00.wav");
	precache_sound ("john/jv01.wav");
	precache_sound ("john/jv02.wav");
	precache_sound ("john/jv03.wav");
	precache_sound ("john/jv04.wav");
	precache_sound ("john/jv05.wav");
	precache_sound ("john/jv06.wav");
	precache_sound ("john/jv07.wav");
	precache_sound ("john/jv08.wav");
	precache_sound ("john/jv09.wav");
	precache_sound ("john/jv10.wav");
	precache_sound ("john/jv11.wav");
	precache_sound ("john/jv12.wav");
	precache_sound ("john/jv13.wav");
	precache_sound ("john/jv14.wav");
	precache_sound ("john/jv15.wav");
	precache_sound ("john/jv16.wav");
	precache_sound ("john/jv17.wav");
	precache_sound ("john/jv18.wav");
	precache_sound ("john/jv19.wav");
	precache_sound ("john/jv20.wav");
	precache_sound ("john/jv21.wav");
	precache_sound ("john/jv22.wav");
};

string() JW_Voice =
{
	local float r;

	r = floor (random () * 23);
	if (r < 1)
		return "john/jv00.wav";
	if (r < 2)
		return "john/jv01.wav";
	if (r < 3)
		return "john/jv02.wav";
	if (r < 4)
		return "john/jv03.wav";
	if (r < 5)
		return "john/jv04.wav";
	if (r < 6)
		return "john/jv05.wav";
	if (r < 7)
		return "john/jv06.wav";
	if (r < 8)
		return "john/jv07.wav";
	if (r < 9)
		return "john/jv08.wav";
	if (r < 10)
		return "john/jv09.wav";
	if (r < 11)
		return "john/jv10.wav";
	if (r < 12)
		return "john/jv11.wav";
	if (r < 13)
		return "john/jv12.wav";
	if (r < 14)
		return "john/jv13.wav";
	if (r < 15)
		return "john/jv14.wav";
	if (r < 16)
		return "john/jv15.wav";
	if (r < 17)
		return "john/jv16.wav";
	if (r < 18)
		return "john/jv17.wav";
	if (r < 19)
		return "john/jv18.wav";
	if (r < 20)
		return "john/jv19.wav";
	if (r < 21)
		return "john/jv20.wav";
	if (r < 22)
		return "john/jv21.wav";
	return "john/jv22.wav";
};

// ---- the wave: grows out from where the head landed, lifting everyone it reaches
void() JW_WaveThink =
{
	local entity e;
	local float r;
	local vector dir;

	self.nextthink = time + 0.05;
	r = JW_WAVE_SPEED * (time - self.fg_born);
	if (r > JW_RADIUS + 60)
	{
		remove (self);
		return;
	}
	self.scale = (r + 10) / 100;		// the model is 100 units wide

	e = findradius (self.origin, r);
	while (e)
	{
		if (e.classname == "player" && e.health > 0 && e.jw_wave != self)
		{
			e.jw_wave = self;
			e.jw_float_t = time + JW_FLOAT;
			dir = e.origin - self.origin;
			dir_z = 0;
			dir = normalize (dir);
			e.velocity = e.velocity + dir * JW_OUT;
			e.velocity_z = JW_RISE;
			e.flags = e.flags - (e.flags & FL_ONGROUND);
			FG_Snd (e, CHAN_ITEM, JW_Voice (), 1, 1);
			if (e.flags & FL_CLIENT)
				centerprint (e, "THE JOHN WAVE\nyou are floating\n");
		}
		e = e.chain;
	}
};

void(entity hit) JW_Splash =
{
	local entity w;
	local vector org;

	org = self.origin;
	if (vlen (self.velocity) > 1)
		org = org - normalize (self.velocity) * 8;

	fg_inflicting = FG_JOHN;
	if (hit.takedamage)
		T_Damage (hit, self, self.owner, JW_DIRECT + random () * 10);
	T_RadiusDamage (self, self.owner, JW_BLAST, hit);
	fg_inflicting = 0;

	FG_Snd (self, CHAN_WEAPON, "weapons/r_exp3.wav", 0.7, 0.8);

	w = spawn ();
	w.classname = "jwwave";
	w.owner = self.owner;
	w.movetype = MOVETYPE_NONE;
	w.solid = SOLID_NOT;
	w.effects = 544;		// fullbright + additive
	w.fg_born = time;
	setmodel (w, "progs/jw_wave.md3");
	setsize (w, VEC_ORIGIN, VEC_ORIGIN);
	w.scale = 0.1;
	setorigin (w, org + '0 0 2');
	w.think = JW_WaveThink;
	w.nextthink = time + 0.05;
	remove (self);
};

void() JW_HeadTouch =
{
	if (other == self.owner)
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	JW_Splash (other);
};

// in flight: John talks
void() JW_HeadThink =
{
	self.nextthink = time + 0.1;
	if (time > self.fg_born + 8)
	{
		remove (self);
		return;
	}
	if (time >= self.hm_beep_t)
	{
		FG_Snd (self, CHAN_VOICE, JW_Voice (), 0.9, 1);
		self.hm_beep_t = time + 0.8 + random () * 0.4;
	}
};

// the head leaves the hand
void() JW_Release =
{
	local entity h;
	local vector dir;
	local float a;

	self.fg_throw_t = 0;
	self.fg_hold = 0;
	a = FunGun_Ammo (self, FG_JOHN);
	if (a < 1)
		return;
	FunGun_SetAmmo (self, FG_JOHN, a - 1);
	self.fg_fire_t = time;
	self.attack_finished = time + 1;
	self.punchangle_x = -4;
	player_mm1 ();

	makevectors (self.v_angle);
	dir = aim (self, 1000);

	h = spawn ();
	h.owner = self;
	h.classname = "jwhead";
	h.movetype = MOVETYPE_FLYMISSILE;
	h.solid = SOLID_BBOX;
	h.velocity = dir * JW_SPEED;
	h.angles = vectoangles (dir);
	h.angles_x = 0;
	h.avelocity = '0 360 0';		// spins as it flies
	h.scale = 1.5;				// about 40 units across
	h.fg_born = time;
	h.hm_beep_t = time + 0.4;
	h.touch = JW_HeadTouch;
	h.think = JW_HeadThink;
	h.nextthink = time + 0.1;
	setmodel (h, "progs/johnhead3d.md3");		// 3D head rebuilt from the MegaKart turntable clip (build_john_head3d.py)
	setsize (h, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (h, FG_Muzzle (28));

	FG_Snd (self, CHAN_WEAPON, "john/jwthrow.wav", 1, 1);
	FG_Snd (h, CHAN_VOICE, JW_Voice (), 0.9, 1);
};

// ---- the hand: John in your view
void() JW_HandThink =
{
	local entity p;

	p = self.owner;
	if (p.health <= 0 || p.weapon != IT_FUNGUN || p.fg_sel != FG_JOHN || p.fg_hand != self)
	{
		if (p.fg_hand == self)
			p.fg_hand = world;
		remove (self);
		return;
	}
	self.nextthink = time + 0.1;
};

void() JW_MakeHand =
{
	local entity e;

	e = spawn ();
	e.classname = "jw_hand";
	e.owner = self;
	e.movetype = MOVETYPE_NONE;
	e.solid = SOLID_NOT;
	e.viewmodelforclient = self;
	e.effects = EF_NOGUNBOB;
	setmodel (e, "progs/fr_johnhand.spr32");
	setsize (e, VEC_ORIGIN, VEC_ORIGIN);
	e.scale = 0.15;
	setorigin (e, '24 7 -7');
	e.think = JW_HandThink;
	e.nextthink = time + 0.1;
	self.fg_hand = e;
};

// switching away cancels a hold for free
void() JW_DropHand =
{
	if (self.fg_hand)
	{
		remove (self.fg_hand);
		self.fg_hand = world;
	}
	self.fg_hold = 0;
	self.fg_throw_t = 0;
};

// every frame while John is selected: the hold / throw state machine and the hand's animation
// frames 0-7 idle sway (pingpong, faster the longer you hold), 8-48 the throw
void() JW_Frame =
{
	local float f, el, fps, p;

	if (!self.fg_hand)
		JW_MakeHand ();
	self.weaponframe = 0;
	if (self.fg_throw_t)
	{
		f = 8 + floor ((time - self.fg_throw_start) * 34);
		if (f > 48)
			f = 48;
		self.fg_hand.frame = f;
		if (time >= self.fg_throw_t)
			JW_Release ();
		return;
	}
	fps = 5;
	if (self.fg_hold)
	{
		if (!self.button0 || time > self.fg_hold + 3)
		{
			self.fg_throw_start = time;
			self.fg_throw_t = time + JW_THROW_T;
			return;
		}
		el = time - self.fg_hold;
		if (el > 2)
			el = 2;
		fps = 5 + el * 11;
	}
	p = floor (time * fps);
	p = p - 14 * floor (p / 14);
	if (p > 7)
		p = 14 - p;
	self.fg_hand.frame = p;
};
