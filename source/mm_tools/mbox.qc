/*
================
THE MYSTERY BOX (see mbox_defs.qc for the rules and numbers)

FunGun_ViewFrame calls MB_Throw MB_THROW_DELAY after the fire (the hand lets go at frame 207 of v_mysterybox.md3).
The box is a flying entity (MB_BoxThink, MB_BoxTouch) that bursts where it lands (MB_Burst) into confetti and
MB_SPAWNS monsters. A monster (classname "mbmonster") is a MOVETYPE_STEP entity that runs along the floor (no jumping):
MB_Think picks the nearest enemy, runs flat out at it and stops MB_FACE units from it, in its face; MB_Touch does the
damage every MB_HIT_GAP seconds; after MB_HITS hits, MB_LIFE seconds or a shot it blows up (MB_Explode). Damage is dealt
in the owner's name with fg_inflicting set, so frags and the obituary just work.
================
*/

string(float t) MB_TypeModel;
string(float t) MB_DriveSound;
string(float t) MB_ExplodeSound;
float(float t, float n) MB_InPool;

void(float t) MB_PrecacheType =
{
	local string s;

	s = MB_TypeModel (t);
	if (s != "")
		precache_model (s);
	s = MB_DriveSound (t);
	if (s != "")
		precache_sound (s);
	s = MB_ExplodeSound (t);
	if (s != "")
		precache_sound (s);
};

void() MB_Precache =
{
	local float n, t, f;

	precache_model ("progs/v_mysterybox.md3");
	precache_model ("progs/proj_mysterybox.md3");
	precache_sound ("misc/r_tele1.wav");
	precache_sound ("misc/r_tele3.wav");
	precache_sound ("misc/r_tele5.wav");
	precache_sound ("weapons/r_exp3.wav");
	precache_sound ("weapons/tink1.wav");
	precache_sound ("weapons/lstart.wav");
	f = cvar ("mb_force");
	n = tokenize (cvar_string ("mb_pool"));
	t = 1;
	while (t <= 28)
	{
		if (MB_InPool (t, n) || t == f)
			MB_PrecacheType (t);
		t = t + 1;
	}
};

// ---------------------------------------------------------------- the roster (the vote page's 22 characters + David Ojeda, 3 Pregnant Runners, Daniel & 4 AM Dad)
float	MB_ROSTER = 28;

string(float t) MB_TypeName =
{
	if (t == 1)		return "Mega Man";
	if (t == 2)		return "Suit Rider";
	if (t == 3)		return "Pink Supercar";
	if (t == 4)		return "Squat Rider";
	if (t == 5)		return "NetSend PC";
	if (t == 6)		return "Casino Horse";
	if (t == 7)		return "Big-Ears";
	if (t == 8)		return "Forklift";
	if (t == 9)		return "Wheelman";
	if (t == 10)	return "JessKart";
	if (t == 11)	return "Kyle";
	if (t == 12)	return "Earhead";
	if (t == 13)	return "Pickle";
	if (t == 14)	return "Friend Rob";
	if (t == 15)	return "John's Hand";
	if (t == 17)	return "Bryan & Demons";
	if (t == 18)	return "Dennis";
	if (t == 19)	return "Paul";
	if (t == 20)	return "QuakeGuy";
	if (t == 21)	return "Mr DIY";
	if (t == 22)	return "Rubber Finger";
	if (t == 23)	return "David Ojeda";
	if (t == 24)	return "Pregnant Runner 1";
	if (t == 25)	return "Pregnant Runner 2";
	if (t == 26)	return "Pregnant Runner 3";
	if (t == 27)	return "Daniel (CCC)";
	if (t == 28)	return "4 AM Dad";
	return "Rolling Wheelman";
};

// "" = not built yet (the draw skips it)
string(float t) MB_TypeModel =
{
	if (t == 1)		return "progs/megaman.md3";
	if (t == 2)		return "progs/mm_suit_rider.md3";
	if (t == 3)		return "progs/pink_supercar.md3";
	if (t == 4)		return "progs/mm_squat_rider.md3";
	if (t == 5)		return "progs/netsend_pc.md3";
	if (t == 6)		return "progs/gw_horse.md3";
	if (t == 7)		return "progs/bigears.md3";
	if (t == 8)		return "progs/bklan/sr_vehicle_forklift_orange_a01.md3";
	if (t == 9 || t == 16)	return "progs/wheelman.spr32";
	if (t == 10)	return "progs/jesskart.spr32";
	if (t == 11)	return "progs/fr_scissors.spr32";
	if (t == 14)	return "progs/fr_rob.spr32";
	if (t == 17)	return "progs/bryan.spr32";
	if (t == 18)	return "progs/fr_dennis.spr32";
	if (t == 19)	return "progs/fr_paul.spr32";
	if (t == 20)	return "progs/fr_quakeguy.spr32";
	if (t == 21)	return "progs/fr_mrdiy.spr32";
	if (t == 22)	return "progs/fr_finger.spr32";
	if (t == 23)	return "progs/david.spr32";
	if (t == 24)	return "progs/preg_1.spr32";
	if (t == 25)	return "progs/preg_2.spr32";
	if (t == 26)	return "progs/preg_3.spr32";
	if (t == 27)	return "progs/daniel.spr32";
	if (t == 28)	return "progs/daniel_dad.spr32";
	return "";
};

// Each monster's own sounds (the sound vote of 2026-10-31, mystery_box_sound_vote.html): what it plays again and again while it
// runs (a clip that is replayed when it has ended, MB_DriveLen seconds), and what it plays when it explodes. "" = no pick yet:
// no running sound, and the stock explosion.
string(float t) MB_DriveSound =
{
	if (t == 2)		return "john/jv15.wav";
	if (t == 9)		return "friends/gowewd.wav";
	if (t == 14)	return "floathead/calc/c2.wav";
	if (t == 17)	return "bryan/noway.wav";
	if (t == 22)	return "mbox/drv_boing_hop.wav";		// vote of 2026-11-01 (drv_boing_hop, made by make_mbox_sound_vote.py)
	if (t == 23)	return "david/shower_love.wav";
	if (t == 27)	return "daniel/ccc_chant.wav";
	if (t == 28)	return "daniel/dad_4am.wav";
	return "";
};

float(float t) MB_DriveLen =
{
	if (t == 2)		return 0.566;
	if (t == 9)		return 2.09;
	if (t == 14)	return 5.015;
	if (t == 17)	return 1.74;
	if (t == 22)	return 2;
	if (t == 23)	return 2.65;
	if (t == 27)	return 4.13;
	if (t == 28)	return 3.22;
	return 1;
};

string(float t) MB_ExplodeSound =
{
	if (t == 2)		return "john/jv11.wav";
	if (t == 9)		return "friends/no.wav";
	if (t == 14)	return "fungun/fg_bonk_hit.wav";
	if (t == 17)	return "grenade/boom_03_scream_launch.wav";		// vote of 2026-11-01
	if (t == 23)	return "david/slot_jackpot.wav";
	if (t == 27)	return "daniel/shaaa_scream.wav";
	if (t == 28)	return "daniel/sorry_table.wav";
	return "";
};

// the 56-frame sprites (0-7 idle by direction, 8 + d * 6 + k running; see wheelman.qc)
float(float t) MB_IsSprite =
{
	return (t == 9 || t == 10 || t == 11 || t == 14 || t == 16 || t == 17 || (t >= 18 && t <= 28));
};

// a sprite shows the side of itself the viewer sees (the engine asks for every client)
float() MB_Customize =
{
	local float rel, d, k, cyc;

	rel = vectoyaw (other.origin - self.origin) - self.angles_y;
	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 45 + 0.5);
	if (d >= 8)
		d = 0;
	if (self.mb_run && (self.mb_type == 9 || self.mb_type == 16))
	{
		// the Wheelman sprite was rebuilt on 2026-10-31 (wheelman.qc): running frames are 8 + d * 12 + k, k = 0..11
		k = floor (time * 20 + self.origin_x * 0.05);
		k = k - 12 * floor (k / 12);
		self.frame = 8 + d * 12 + k;
	}
	else if (self.mb_run && self.mb_type == 23)
	{
		// David Ojeda hyper-sprint: alternates fast_run (8), turbo_sprint (56), and money_run (152) at 18 fps!
		k = floor (time * 18 + self.origin_x * 0.03);
		k = k - 6 * floor (k / 6);
		cyc = floor ((time - self.mb_born) * 0.65);
		cyc = cyc - 3 * floor (cyc / 3);
		if (cyc == 1)
			self.frame = 56 + d * 6 + k;
		else if (cyc == 2)
			self.frame = 152 + d * 6 + k;
		else
			self.frame = 8 + d * 6 + k;
	}
	else if (self.mb_run && self.mb_type == 27)
	{
		// Daniel 4 AM LAN chaos: alternates dragging 4AM table (56), CCC grin barrage (104), and hands-up "Sorry!" sprint (248)!
		k = floor (time * 18 + self.origin_x * 0.03);
		k = k - 6 * floor (k / 6);
		cyc = floor ((time - self.mb_born) * 0.70);
		cyc = cyc - 3 * floor (cyc / 3);
		if (cyc == 1)
			self.frame = 104 + d * 6 + k;
		else if (cyc == 2)
			self.frame = 248 + d * 6 + k;
		else
			self.frame = 56 + d * 6 + k;
	}
	else if (self.mb_run)
	{
		k = floor (time * 12 + self.origin_x);
		k = k - 6 * floor (k / 6);
		self.frame = 8 + d * 6 + k;
	}
	else
		self.frame = d;
	return TRUE;
};

// scale, hit box, running frames and facing of each character. They are all about a player tall (MB_HEIGHT units of
// picture) and about as bright: the scales come from the visible height of each picture (sprite frame 0 / model frame 0),
// the colormod from the average brightness of its texture (measured 2026-10-31: sprites 59-65 except Kyle's 121)
float	MB_HEIGHT = 56;
void(entity m, float t) MB_Setup =
{
	m.mb_yaw0 = 0;
	m.mb_fn = 0;
	m.skin = 0;
	m.colormod = '1 1 1';
	setsize (m, '-18 -18 0', '18 18 54');
	if (t == 1)
	{
		m.scale = 1.1;
		m.mb_f0 = 0;	m.mb_fn = 16;	m.mb_fps = 20;		// the wheel spin
	}
	else if (t == 2)
	{
		m.scale = 1.15;		// 48 units tall as modelled
		m.mb_f0 = 40;	m.mb_fn = 12;	m.mb_fps = 14;		// "charge": the slalom pursuit
	}
	else if (t == 3)
	{
		m.scale = 0.34;
		m.mb_f0 = 16;	m.mb_fn = 16;	m.mb_fps = 16;		// the cruise: spinning wheels
	}
	else if (t == 4)
	{
		m.scale = 1.15;
		m.skin = 1;		// the toothy grin
		m.colormod = '0.8 0.8 0.8';		// its shirt is a little lighter than the suit rider's
		m.mb_f0 = 40;	m.mb_fn = 12;	m.mb_fps = 14;
	}
	else if (t == 5)
	{
		m.scale = 0.9;
		m.mb_f0 = 20;	m.mb_fn = 20;	m.mb_fps = 10;		// the hacking loop
	}
	else if (t == 6)
		m.scale = 0.4;
	else if (t == 7)
		m.scale = 2.4;
	else if (t == 8)
	{
		m.scale = 0.62;
		m.mb_yaw0 = 90;		// the forklift's nose is along +Y
	}
	else if (t == 9 || t == 16)
		m.scale = 0.333;	// the rebuilt Wheelman picture (360x255) is 168 px tall
	else if (t == 10)
		m.scale = 0.5;		// JessKart 113 px
	else if (t == 11)
	{
		m.scale = 0.455;	// Kyle 123 px
		m.colormod = '0.5 0.5 0.5';		// his picture is twice as light as the others
	}
	else if (t == 17)
		m.scale = 0.31;		// Bryan & Demons 182 px Bryan height (320x288)
	else if (t == 18)
	{
		m.scale = 0.5;		// Dennis 112 px
		m.colormod = '1.45 1.45 1.45';		// his suit picture is darker than the others (mean 42, they are 55-65)
	}
	else if (t == 19 || t == 20)
		m.scale = 0.5;		// Paul 112 px, QuakeGuy 113 px
	else if (t == 21)
		m.scale = 0.45;		// Mr DIY 123 px
	else if (t == 22)
		m.scale = 0.43;		// Rubber Finger 117 px standing, 133 px running
	else if (t == 23)
		m.scale = 0.26;		// David Ojeda 216 px character height on 256x288 stage
	else if (t >= 24 && t <= 26)
		m.scale = 0.51;		// Pregnant Runners 1..3 108 px character height on 128x144 stage
	else if (t == 27)
		m.scale = 0.26;		// Daniel 216 px character height on 256x288 stage
	else if (t == 28)
		m.scale = 0.41;		// Angry 4 AM Dad 136 px character height on 160x192 stage
	else
		m.scale = 0.55;		// Friend Rob 102 px
};

// ---------------------------------------------------------------- the box

// the magazine gets a box back (it was lost in the sky)
void(entity who) MB_Refund =
{
	local float a;

	a = FunGun_Ammo (who, FG_MBOX);
	if (a < FG_MBOX_MAX)
		FunGun_SetAmmo (who, FG_MBOX, a + 1);
};

// someone the monster (self) should go for: a player or monster that is not its owner, a teammate or another monster
float(entity e) MB_IsEnemy =
{
	if (!e || e == self.owner || e == self || !e.takedamage || e.health <= 0)
		return FALSE;
	if (e.classname == "mbmonster" || e.classname == "mbox")
		return FALSE;
	if (!(e.flags & FL_CLIENT) && !(e.flags & FL_MONSTER))
		return FALSE;
	if (e.flags & FL_NOTARGET)
		return FALSE;
	if (teamplay && e.team > 0 && e.team == self.owner.team)
		return FALSE;
	return TRUE;
};

// the nearest enemy anywhere in range, one it can see counting as nearer
entity() MB_FindEnemy =
{
	local entity e, best;
	local float d, bd;

	best = world;
	bd = 100000;
	e = findradius (self.origin, 4000);
	while (e)
	{
		if (MB_IsEnemy (e))
		{
			d = vlen (e.origin - self.origin);
			traceline (self.origin, e.origin + '0 0 16', TRUE, self);
			if (trace_fraction < 1 && trace_ent != e)
				d = d * 1.6 + 200;
			if (d < bd)
			{
				bd = d;
				best = e;
			}
		}
		e = e.chain;
	}
	return best;
};

// is roster number t one of the first n numbers of the tokenized pool (n < 1 = no pool: everything is)
float(float t, float n) MB_InPool =
{
	local float j;

	if (n < 1)
		return TRUE;
	j = 0;
	while (j < n)
	{
		if (stof (argv (j)) == t)
			return TRUE;
		j = j + 1;
	}
	return FALSE;
};

// a monster of the roster, drawn from mb_pool (the vote page's cvar line), skipping the ones that are not built yet
// and (when there is a choice) the one 'avoid'
float(float avoid) MB_PickType =
{
	local float n, t, count, pick, pass;

	if (cvar ("mb_force") > 0)
		return cvar ("mb_force");		// test aid: every monster is this roster number
	n = tokenize (cvar_string ("mb_pool"));		// a variant builtin: keep its result in a local
	pass = 0;
	count = 0;
	while (pass < 3)
	{
		count = 0;
		t = 1;
		while (t <= MB_ROSTER)
		{
			if (MB_TypeModel (t) != "" && t != avoid && MB_InPool (t, n))
				count = count + 1;
			t = t + 1;
		}
		if (count > 0)
			break;
		avoid = 0;		// a pool of one: the same monster twice is fine
		if (pass == 1)
			n = 0;		// a pool of nothing that is built: everything that is
		pass = pass + 1;
	}
	if (count < 1)
		return 1;
	pick = floor (random () * count);
	t = 1;
	while (t <= MB_ROSTER)
	{
		if (MB_TypeModel (t) != "" && t != avoid && MB_InPool (t, n))
		{
			if (pick < 1)
				return t;
			pick = pick - 1;
		}
		t = t + 1;
	}
	return 1;
};

// at most MB_MAX monsters per player: the oldest go
void(entity who, float room) MB_MakeRoom =
{
	local entity e, oldest;
	local float n;

	n = 99;
	while (n > MB_MAX - room)
	{
		n = 0;
		oldest = world;
		e = find (world, classname, "mbmonster");
		while (e)
		{
			if (e.owner == who)
			{
				n = n + 1;
				if (!oldest || e.mb_born < oldest.mb_born)
					oldest = e;
			}
			e = find (e, classname, "mbmonster");
		}
		if (n <= MB_MAX - room || !oldest)
			return;
		pointparticles (particleeffectnum ("mb_spawn"), oldest.origin + '0 0 20', VEC_ORIGIN, 1);
		remove (oldest);
	}
};

// a monster of roster number t for 'who', with its model, size and look (not placed or started yet)
entity(entity who, float t) MB_Make =
{
	local entity m;

	m = spawn ();
	m.classname = "mbmonster";
	m.owner = who;
	m.mb_type = t;
	m.mb_born = time;
	m.movetype = MOVETYPE_STEP;
	m.solid = SOLID_SLIDEBOX;
	MB_PrecacheType (t);
	setmodel (m, MB_TypeModel (t));
	MB_Setup (m, t);
	if (MB_IsSprite (t))
	{
		m.customizeentityforclient = MB_Customize;
		if (t == 16)
			m.mb_run = 1;		// the rolling Wheelman always rolls
	}
	return m;
};

// one monster out of the burst at 'org' (the surface normal there is 'n'); self = the box
void(float t, vector org, vector n, float side) MB_Spawn =
{
	local entity m, old;
	local vector spot, c;
	local float a;

	m = MB_Make (self.owner, t);
	m.takedamage = DAMAGE_AIM;
	m.health = MB_HEALTH;
	m.th_die = MB_Shot;
	m.touch = MB_Touch;
	m.think = MB_Think;
	m.nextthink = time + 0.3;		// it pops out first
	m.traileffectnum = particleeffectnum ("mb_mtrail");

	// out of the box on either side of the burst (side 0 one way, side 1 the opposite), 40 units apart from the middle where there is
	// room, else as near as it goes (a monster must never start inside a wall: it could not move)
	a = random () * 360 + side * 180;
	makevectors ('0 1 0' * a);
	c = org + n * 24;
	spot = c + v_forward * 40;
	tracebox (c, m.mins, m.maxs, spot, TRUE, m);
	if (trace_startsolid)
		setorigin (m, org + n * 8 + v_forward * 16);
	else
		setorigin (m, trace_endpos);
	m.angles_y = a;
	old = self;
	self = m;
	droptofloor ();
	self = old;
	pointparticles (particleeffectnum ("mb_spawn"), m.origin + '0 0 20', VEC_ORIGIN, 1);
	dprint (strcat ("mbox: spawn ", MB_TypeName (t)));
	dprint ("\n");
};

// the box has landed: confetti, magic, and the monsters (self = the box)
void() MB_Burst =
{
	local vector org, n, v;
	local float i, t, last;
	local entity who;

	who = self.owner;
	org = self.origin;
	n = '0 0 1';
	v = normalize (self.velocity);
	traceline (org - v * 8, org + v * 24, TRUE, self);
	if (trace_fraction < 1)
	{
		n = trace_plane_normal;
		org = trace_endpos + n * 4;
	}
	dprint ("mbox: burst\n");
	pointparticles (particleeffectnum ("mb_confetti"), org + n * 6, VEC_ORIGIN, 1);
	FG_Snd (self, CHAN_AUTO, "misc/r_tele1.wav", 1, 1.25);
	FG_Snd (self, CHAN_VOICE, "weapons/lstart.wav", 0.5, 1.6);

	MB_MakeRoom (who, MB_SPAWNS);
	last = 0;
	i = 0;
	while (i < MB_SPAWNS)
	{
		t = MB_PickType (last);
		last = t;
		MB_Spawn (t, org, n, i);
		i = i + 1;
	}
	remove (self);
};

// it hit something: a floor, a wall or someone is where it bursts
void() MB_BoxTouch =
{
	if (other == self.owner)
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		MB_Refund (self.owner);
		remove (self);
		return;
	}
	MB_Burst ();
};

// the box in the air: it tumbles (frames 0-31 of proj_mysterybox.md3), points along its flight and is lost if it never lands
void() MB_BoxThink =
{
	local float f;

	self.nextthink = time + 0.05;
	if (time - self.mb_born > MB_LIFE_BOX)
	{
		MB_Refund (self.owner);
		remove (self);
		return;
	}
	f = floor ((time - self.mb_born) * 24);
	self.frame = f - 32 * floor (f / 32);
	self.angles = vectoangles (self.velocity);
};

// test aid (mb_test 2): one of every monster in the pool in a row 300 units ahead, standing still, to compare their sizes and looks
void() MB_Lineup =
{
	local entity m, old;
	local float t, i, n;
	local vector p;

	old = self;
	n = tokenize (cvar_string ("mb_pool"));
	makevectors ('0 1 0' * self.v_angle_y);
	i = 0;
	t = 1;
	while (t <= MB_ROSTER)
	{
		if (MB_TypeModel (t) != "" && MB_InPool (t, n))
		{
			m = MB_Make (old, t);
			m.movetype = MOVETYPE_NONE;
			m.takedamage = DAMAGE_NO;
			m.mb_run = FALSE;
			p = old.origin + v_forward * 300 + v_right * (i * 70 - 210);
			setorigin (m, p);
			m.angles_y = old.v_angle_y + 180 + m.mb_yaw0;
			i = i + 1;
		}
		t = t + 1;
	}
};

// the hand lets go (FunGun_ViewFrame): the box flies out of the muzzle, spraying rainbow glitter
void() MB_Throw =
{
	local entity b;

	makevectors (self.v_angle);
	b = spawn ();
	b.owner = self;
	b.classname = "mbox";
	b.movetype = MOVETYPE_TOSS;
	b.solid = SOLID_BBOX;
	b.gravity = MB_GRAVITY;
	b.mb_born = time;
	b.velocity = v_forward * MB_THROW + v_up * 140;
	b.touch = MB_BoxTouch;
	b.think = MB_BoxThink;
	b.nextthink = time + 0.05;
	b.traileffectnum = particleeffectnum ("mb_trail");
	setmodel (b, "progs/proj_mysterybox.md3");
	setsize (b, '-6 -6 -6', '6 6 6');
	setorigin (b, FG_Muzzle (24));
	b.angles = vectoangles (b.velocity);
	if (cvar ("mb_test") == 2)
	{
		MB_Lineup ();
		remove (b);
		return;
	}
	if (cvar ("mb_test"))
	{
		// test aid: the box drops at the player's feet-ish, 150 units ahead, so the monsters can be looked at close up
		b.velocity = '0 0 -400';
		setorigin (b, self.origin + v_forward * 150 + '0 0 40');
	}
	self.punchangle_x = -4;
	FG_Snd (self, CHAN_WEAPON, "misc/r_tele5.wav", 0.7, 1.5);
};

// ---------------------------------------------------------------- the monsters

// it goes off: confetti and a small blast on every enemy near it (never its owner, who is not an enemy)
void() MB_Explode =
{
	local vector org;
	local entity e;
	local float d;

	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	dprint (strcat ("mbox: ", MB_TypeName (self.mb_type)));
	dprint (" explodes\n");
	org = self.origin + '0 0 20';
	fg_inflicting = FG_MBOX;
	e = findradius (org, MB_BLAST + 40);
	while (e)
	{
		if (MB_IsEnemy (e))
		{
			d = vlen (e.origin + '0 0 16' - org);
			T_Damage (e, self, self.owner, MB_BLAST * (1 - 0.5 * d / (MB_BLAST + 40)));
		}
		e = e.chain;
	}
	fg_inflicting = 0;
	pointparticles (particleeffectnum ("mb_boom"), org, VEC_ORIGIN, 1);
	if (MB_ExplodeSound (self.mb_type) != "")
		FG_Snd (self, CHAN_VOICE, MB_ExplodeSound (self.mb_type), 1, 1);		// its own sound, on the channel of its running sound: that stops
	else
		FG_Snd (self, CHAN_AUTO, "weapons/r_exp3.wav", 0.8, 1.3);
	remove (self);
};

// shot to bits: it goes off at once
void() MB_Shot =
{
	MB_Explode ();
};

// self (the monster) hits 'e' in the face: MB_HIT_DMG, once every MB_HIT_GAP seconds. TRUE = that was its last hit and it exploded
// (self is gone). Walking into someone does not call touch (only a flying move does), so MB_Think calls this itself.
float(entity e) MB_Hit =
{
	if (!MB_IsEnemy (e))
		return FALSE;
	if (time < self.mb_next_hit)
		return FALSE;
	self.mb_next_hit = time + MB_HIT_GAP;
	fg_inflicting = FG_MBOX;
	T_Damage (e, self, self.owner, MB_HIT_DMG);
	fg_inflicting = 0;
	pointparticles (particleeffectnum ("mb_hit"), self.origin + '0 0 24', VEC_ORIGIN, 1);
	FG_Snd (self, CHAN_AUTO, "weapons/tink1.wav", 0.8, 1.4 + random () * 0.6);
	self.mb_hits = self.mb_hits + 1;
	dprint (strcat ("mbox: ", MB_TypeName (self.mb_type)));
	dprint (strcat (" hit ", e.netname));
	dprint ("\n");
	if (self.mb_hits >= MB_HITS)
	{
		MB_Explode ();
		return TRUE;
	}
	return FALSE;
};

// it touched something (self = the monster)
void() MB_Touch =
{
	MB_Hit (other);
};

// nobody to go for: it does not stand there like a statue. It strolls a few steps one way, stops, turns to look around, strolls on
void() MB_Wander =
{
	local float d, step;

	if (self.mb_glide)
	{
		self.mb_glide = FALSE;		// it was gliding through a wall at someone who has gone: back on its feet
		self.movetype = MOVETYPE_STEP;
		self.velocity = '0 0 0';
		setorigin (self, self.origin);
		self.flags = self.flags - (self.flags & FL_ONGROUND);
	}
	self.mb_pos_t = 0;		// the stuck check starts again when it has someone to run at
	if (time >= self.mb_wt)
	{
		if (random () < 0.55)
		{
			self.mb_wgo = TRUE;
			self.mb_wy = self.mb_wy + crandom () * 100;
			self.mb_wt = time + 1 + random () * 1.6;
		}
		else
		{
			self.mb_wgo = FALSE;
			self.mb_wy = random () * 360;
			self.mb_wt = time + 0.8 + random () * 1.4;
		}
	}
	d = self.mb_wy - (self.angles_y - self.mb_yaw0);
	d = d - 360 * floor ((d + 180) / 360);
	step = 150 * 0.05;
	if (self.mb_wgo)
		step = 400 * 0.05;
	if (d > step)
		d = step;
	if (d < 0 - step)
		d = 0 - step;
	self.angles_y = self.angles_y + d;
	self.mb_run = self.mb_wgo;
	if (self.mb_wgo && (self.flags & FL_ONGROUND))
	{
		if (!walkmove (self.angles_y - self.mb_yaw0, MB_WANDER * 0.05))
			self.mb_wt = 0;		// a wall or a drop: pick another way next think
	}
};

// the monster's think: pick the enemy, run flat out at it along the floor (no jumping) and stay in its face
void() MB_Think =
{
	local vector dir;
	local float d, f, yaw, spd;

	self.nextthink = time + 0.05;
	if (time - self.mb_born > MB_LIFE || pointcontents (self.origin) == CONTENT_LAVA || pointcontents (self.origin) == CONTENT_SLIME)
	{
		MB_Explode ();
		return;
	}

	// its look: running frames
	if (self.mb_fn)
	{
		f = floor ((time - self.mb_born) * self.mb_fps);
		self.frame = self.mb_f0 + f - self.mb_fn * floor (f / self.mb_fn);
	}

	if (!MB_IsEnemy (self.mb_target) || time >= self.mb_next_look)
	{
		self.mb_target = MB_FindEnemy ();
		self.mb_next_look = time + MB_RETARGET;
		if (cvar ("mb_debug"))
		{
			dprint (strcat ("mbox: ", MB_TypeName (self.mb_type)));
			dprint (strcat (" target ", self.mb_target.netname));
			dprint (strcat (" ground ", ftos (self.flags & FL_ONGROUND)));
			dprint (strcat (" at ", vtos (self.origin)));
			dprint ("\n");
		}
	}
	if (!self.mb_target)
	{
		MB_Wander ();		// nobody to chase: it strolls and looks about until its time is up
		if (self.mb_type == 16)
			self.mb_run = TRUE;		// the rolling Wheelman always rolls
		return;
	}

	dir = self.mb_target.origin - self.origin;
	dir_z = 0;
	d = vlen (dir);
	if (d > 1)
		dir = dir * (1 / d);
	yaw = vectoyaw (dir);
	self.angles_y = yaw + self.mb_yaw0;
	self.mb_run = TRUE;
	if (!self.mb_pos_t)
	{
		self.mb_pos = self.origin;
		self.mb_pos_t = time;
	}
	if (time >= self.mb_snd_t && MB_DriveSound (self.mb_type) != "")
	{
		FG_Snd (self, CHAN_VOICE, MB_DriveSound (self.mb_type), 0.9, 1);		// its running sound, again when the last one has ended
		self.mb_snd_t = time + MB_DriveLen (self.mb_type);
	}
	if (d <= MB_REACH && fabs (self.mb_target.origin_z - self.origin_z) < 56)
	{
		if (MB_Hit (self.mb_target))
			return;		// that was the last one: it has gone off
	}
	if (d <= MB_FACE)
		return;		// in their face: it stays put
	// stuck (a wall, a pit, no way across): after MB_STUCK seconds without getting anywhere it glides straight at them through
	// the geometry (noclip, still shootable). It never gives up on the rush.
	if (!self.mb_glide)
	{
		if (time >= self.mb_pos_t + MB_STUCK)
		{
			if (vlen (self.origin - self.mb_pos) < 48 && d > MB_FACE)
			{
				self.mb_glide = TRUE;
				self.movetype = MOVETYPE_NOCLIP;
				self.flags = self.flags - (self.flags & FL_ONGROUND);
				dprint ("mbox: glide\n");
			}
			self.mb_pos = self.origin;
			self.mb_pos_t = time;
		}
	}
	spd = MB_SPEED;
	if (self.mb_type == 23)
		spd = MB_SPEED * 1.45;		// David Ojeda runs extra fast!
	if (self.mb_glide)
	{
		dir = self.mb_target.origin + self.mb_target.mins_z * '0 0 1' - self.origin;
		dir_z = dir_z - self.mins_z;
		if (vlen (dir) > MB_FACE)
			self.velocity = normalize (dir) * spd;
		else
			self.velocity = '0 0 0';
		return;
	}
	// run at them. On the floor that is a walk (it climbs stairs); where the walk is refused (a ledge, a wall) it is pushed along
	// instead, so it drops off ledges and slides along walls. Off the ground it keeps its heading until it lands.
	if (self.flags & FL_ONGROUND)
	{
		if (walkmove (yaw, spd * 0.05))
			return;
		self.flags = self.flags - (self.flags & FL_ONGROUND);
		self.velocity_x = dir_x * spd;
		self.velocity_y = dir_y * spd;
		self.velocity_z = 0;
	}
	else
	{
		self.velocity_x = dir_x * spd;
		self.velocity_y = dir_y * spd;
	}
};
