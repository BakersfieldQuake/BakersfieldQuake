/*
================
THE NETSEND GUN (see netsend_defs.qc for the rules and numbers)

FunGun_ViewFrame calls NS_Throw NS_THROW_DELAY after the fire (the hand lets go at frame 44 of v_netsend.md3).
The disk is a flying entity (NS_DiskThink, NS_DiskTouch). Where it lands on a floor it turns into the PC in place
(NS_Stick): the PC's think (NS_Think) plays the frames of progs/netsend_pc.md3 and sends the NET SEND messages (NS_Send).
A PC never times out, but it can be shot to bits (NS_Die, NS_HEALTH); the only limit is NS_MAX_PCS live PCs per player
(NS_Count). Its damage is dealt in its owner's name with fg_inflicting set, so frags and the
obituary just work.
================
*/

void() NS_Precache =
{
	precache_model ("progs/v_netsend.md3");
	precache_model ("progs/netsend_disk.md3");
	precache_model ("progs/netsend_pc.md3");
	precache_model ("progs/netsend_arc.md3");
	precache_model ("progs/netsend_scr.md3");
	precache_sound ("netsend/ns_beep.wav");
	precache_sound ("weapons/turrset.wav");
	precache_sound ("weapons/goopop.wav");
	precache_sound ("netsend/wheres_disk.wav");
	precache_sound ("enforcer/enfire.wav");
	precache_model ("progs/netsend_laser.md3");
};

// the disk is lost in the sky, or never stuck: the magazine gets it back
void(entity who) NS_Refund =
{
	local float a;

	a = FunGun_Ammo (who, FG_NETSEND);
	if (a < FG_NETSEND_MAX)
		FunGun_SetAmmo (who, FG_NETSEND, a + 1);
};

// the CRT skin for a frame of netsend_pc.md3 (skins 0-6 are progs/netsend_pc.md3_0..6.skin): the boot text goes by with the frames
float(float f) NS_Skin =
{
	if (f < 10)
		return 1;		// black, powering up
	if (f < 12)
		return 2;		// white-noise warm-up
	if (f < 15)
		return 3;		// INITIALIZING BATCH FILE...
	if (f < 17)
		return 4;		// C:\> LOL.BAT
	if (f < 20)
		return 5;		// NET SEND * LOL
	if (f < 40)
		return 0;		// the hacking loop: hex, NET SEND, MESSAGE SENT [OK]
	if (f < 49)
		return 6;		// the collapse to a white dot
	return 1;			// off
};

// the line in the popup (the middle of the victim's screen)
string() NS_Line =
{
	local float r;

	r = random ();
	if (r < 0.34)
		return "WHERE'S THE DISK?\n";
	if (r < 0.67)
		return "NET SEND * LOL\n";
	return "MESSAGE SENT [OK]\n";
};

// how many PCs this player has standing (NS_MAX_PCS is the limit)
float(entity who) NS_Count =
{
	local entity e;
	local float n;

	n = 0;
	e = find (world, classname, "netsend_pc");
	while (e)
	{
		if (e.owner == who)
			n = n + 1;
		e = find (e, classname, "netsend_pc");
	}
	return n;
};

// a PC goes, with its screen and its lightning
void(entity pc) NS_RemovePC =
{
	if (pc.ns_scr)
		remove (pc.ns_scr);
	if (pc.ns_arc)
		remove (pc.ns_arc);
	remove (pc);
};

// FIFO replacement: when throwing beyond NS_MAX_PCS, pop the player's oldest active PC cleanly
void(entity who) NS_MakeRoom =
{
	local entity e, oldest;
	local float n;

	n = 0;
	oldest = world;
	e = find (world, classname, "netsend_pc");
	while (e)
	{
		if (e.owner == who)
		{
			n = n + 1;
			if (!oldest || e.fg_born < oldest.fg_born)
				oldest = e;
		}
		e = find (e, classname, "netsend_pc");
	}
	if (n >= NS_MAX_PCS && oldest != world)
	{
		pointparticles (particleeffectnum ("netsend_pop"), oldest.origin + '0 0 30', VEC_ORIGIN, 1);
		FG_Snd (oldest, CHAN_AUTO, "weapons/goopop.wav", 0.7, 1);
		NS_RemovePC (oldest);
	}
};

// ClientDisconnect: the leaver's PCs and disks in the air go too, else they keep shooting in an empty slot's name and the
// next player (or bot) in that slot inherits them
void(entity p) NS_ClientGone =
{
	local entity e, nx;

	e = find (world, classname, "netsend_pc");
	while (e)
	{
		nx = find (e, classname, "netsend_pc");
		if (e.owner == p)
			NS_RemovePC (e);
		e = nx;
	}
	e = find (world, classname, "netsend_disk");
	while (e)
	{
		nx = find (e, classname, "netsend_disk");
		if (e.owner == p)
			remove (e);
		e = nx;
	}
};

// shot to bits (th_die, self = the PC): a pop, then it is gone. The removal waits a frame: T_Damage/Killed still hold the entity
void() NS_Burst =
{
	pointparticles (particleeffectnum ("netsend_pop"), self.origin + '0 0 30', VEC_ORIGIN, 1);
	FG_Snd (self, CHAN_AUTO, "weapons/goopop.wav", 0.8, 1);
	NS_RemovePC (self);
};

void() NS_Die =
{
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.think = NS_Burst;
	self.nextthink = time + 0.05;
};

// the lightning crackling round the PC (netsend_arc.md3: additive, 8 frames, cycled in NS_Think)
void() NS_ArcOn =
{
	local entity a;

	a = spawn ();
	a.classname = "netsend_arc";
	a.movetype = MOVETYPE_NONE;
	a.solid = SOLID_NOT;
	setmodel (a, "progs/netsend_arc.md3");
	setorigin (a, self.origin);
	a.angles = self.angles;
	self.ns_arc = a;
};

// NS_Target (self = the PC): the nearest player it can see, other than its owner (world if there is none)
entity() NS_Target =
{
	local entity e, best;
	local float d, bd;

	best = world;
	bd = NS_RANGE + 1;
	e = bm_player_head;		// the players, rebuilt once a frame (BM_StartFrame): no scan over every edict
	while (e)
	{
		if (e != self.owner && e.classname == "player" && e.takedamage && e.health > 0 && !(e.flags & FL_NOTARGET) && !(e.items & IT_INVISIBILITY) && !(teamplay && self.owner && e.team > 0 && e.team == self.owner.team))
		{
			d = vlen (e.origin - self.origin);
			if (d < bd && visible (e))
			{
				best = e;
				bd = d;
			}
		}
		e = e.bm_player_next;
	}
	return best;
};

// NS_Send (self = the PC): the nearest player it can see, other than its owner, gets a NET SEND
void() NS_Send =
{
	local entity best;
	local vector top;

	best = NS_Target ();
	if (!best)
	{
		self.ns_next = time + 0.25;		// nobody in sight: look again soon
		return;
	}
	self.ns_next = time + NS_SHOT_GAP;

	top = self.origin + '0 0 62';		// the tip of the top rabbit ear
	trailparticles (self, particleeffectnum ("netsend_shot"), top, best.origin + '0 0 28');
	pointparticles (particleeffectnum ("netsend_zap"), top, VEC_ORIGIN, 1);
	FG_Snd (self, CHAN_WEAPON, "netsend/ns_beep.wav", 1, 1);
	dprint (strcat (strcat ("netsend: ", self.owner.netname), strcat (" -> ", best.netname)));
	dprint ("\n");
	centerprint (best, strcat (strcat ("Messages from ", self.owner.netname), strcat (":\n", NS_Line ())));

	fg_inflicting = FG_NETSEND;
	T_Damage (best, self, self.owner, NS_DAMAGE);
	fg_inflicting = 0;
};

// a green laser hit something: a player or monster takes NS_LASER_DMG in the PC owner's name
void() NS_LaserTouch =
{
	if (other == self.owner || other == self.enemy)
		return;		// its own PC, or its owner
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		remove (self);
		return;
	}
	if (other.takedamage)
	{
		fg_inflicting = FG_NETSEND;
		T_Damage (other, self, self.enemy, NS_LASER_DMG);
		fg_inflicting = 0;
	}
	pointparticles (particleeffectnum ("netsend_laserhit"), self.origin - normalize (self.velocity) * 4, VEC_ORIGIN, 1);
	remove (self);
};

// one green laser from the screen of the PC (self) along 'dir'
void(vector dir) NS_Laser =
{
	local entity l;
	local vector org;

	org = self.origin + '0 0 34';
	l = spawn ();
	l.classname = "netsend_laser";
	l.owner = self;			// it never hits its own PC
	l.enemy = self.owner;	// frags go to whoever threw the disk
	l.movetype = MOVETYPE_FLY;
	l.solid = SOLID_BBOX;
	setmodel (l, "progs/netsend_laser.md3");		// an additive green bolt (laser.mdl's orange is fullbright: colormod never greened it)
	setsize (l, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (l, org + dir * 18);
	l.traileffectnum = particleeffectnum ("netsend_laser");
	l.velocity = dir * NS_LASER_SPEED;
	l.angles = vectoangles (l.velocity);
	l.touch = NS_LaserTouch;
	l.think = SUB_Remove;
	l.nextthink = time + 3;
};

// the sentry's head: 'cur' turned toward 'want' (degrees), at most 'step' of it, the short way round
float(float cur, float want, float step) NS_Turn =
{
	local float d;

	d = want - cur;
	d = d - 360 * floor ((d + 180) / 360);
	if (d > step)
		d = step;
	if (d < 0 - step)
		d = 0 - step;
	return cur + d;
};

// NS_Sentry (self = the PC, sending), every think: like the TF sentry it turns to face the nearest player it can see and
// shoots green lasers at them while it faces them; with nobody in sight it sweeps the room and holds fire. It never spins.
void() NS_Sentry =
{
	local entity e;
	local float want, off, sw;
	local vector dir;

	// looking for a target (a trace per player in range) 5 times a second is plenty; in between keep the last one while it lives
	e = self.ns_target;
	if (time >= self.ns_scan_t || (e && (e.health <= 0 || !e.takedamage || e.classname != "player")))
	{
		e = NS_Target ();
		self.ns_target = e;
		self.ns_scan_t = time + 0.2;
	}
	if (e)
	{
		dir = e.origin + '0 0 16' - (self.origin + '0 0 34');
		want = vectoyaw (dir);
		self.angles_y = NS_Turn (self.angles_y, want, NS_TURN * 0.05);
		off = want - self.angles_y;
		off = off - 360 * floor ((off + 180) / 360);
		if (off < NS_AIM && off > 0 - NS_AIM && time >= self.ns_laser_t)
		{
			dir = normalize (dir);
			dir = normalize (dir + (random () - 0.5) * '0.05 0 0' + (random () - 0.5) * '0 0.05 0');
			NS_Laser (dir);
			FG_Snd (self, CHAN_AUTO, "enforcer/enfire.wav", 0.5, 1.4);
			self.ns_laser_t = time + NS_LASER_GAP;
		}
		return;
	}
	sw = sin (time * NS_SCAN_RATE);
	self.angles_y = NS_Turn (self.angles_y, self.ns_yaw0 + sw * NS_SCAN_ARC, NS_TURN * 0.025);
};

// the CRT screen is a model of its own (progs/netsend_scr.md3, see build_netsend_screen.py: the screen surface inside
// netsend_pc.md3 is drawn with wrong texture coordinates by DarkPlaces): it has the PC's frame, skin, origin and angles
void() NS_ScreenSync =
{
	local entity s;

	s = self.ns_scr;
	if (!s)
		return;
	if (s.origin != self.origin)
		setorigin (s, self.origin);		// the PC never moves: this only happens once, when it lands
	s.angles = self.angles;
	s.frame = self.frame;
	s.skin = self.skin;
};

// the PC's think: frames 0-9 materialize, 10-19 boot, 20-39 sending (a loop, for good)
void() NS_Think =
{
	local float age, f;

	if (self.owner.classname != "player")
	{
		NS_RemovePC (self);		// its owner left (NS_ClientGone normally got it first): nobody to credit, and the slot gets reused
		return;
	}
	if (self.fg_born > 0 && time - self.fg_born > NS_LIFE)
	{
		NS_Die ();
		return;
	}
	self.nextthink = time + 0.05;
	age = time - self.ns_t;
	if (self.ns_state == 2)
	{
		f = min (9, floor (age * 10));
		if (age >= 1)
		{
			self.ns_state = 3;
			self.ns_t = time;
			FG_Snd (self, CHAN_VOICE, "weapons/turrset.wav", 1, 1);		// the whirr of it powering up
		}
	}
	else if (self.ns_state == 3)
	{
		f = 10 + min (9, floor (age * 10));
		if (age >= 1)
		{
			self.ns_state = 4;
			self.ns_t = time;
			self.ns_next = time + 0.5;
			NS_ArcOn ();
		}
	}
	else if (self.ns_state == 4)
	{
		f = floor (age * 10);
		f = 20 + f - 20 * floor (f / 20);		// the loop: 20 frames, 2 seconds
		NS_Sentry ();		// it turns to its target and shoots, like the TF sentry (it does not spin)
		if (time >= self.ns_next)
			NS_Send ();
	}
	self.frame = f;
	self.skin = NS_Skin (f);
	NS_ScreenSync ();
	if (self.ns_arc)
	{
		self.ns_arc.angles = self.angles;		// its origin was set once, in NS_ArcOn
		f = floor (time * 15);
		self.ns_arc.frame = f - 8 * floor (f / 8);		// the 8 arcs, cycled
	}
};

// the disk lies on the floor at 'spot': it turns into the PC right there (the PC's frame 0 is the disk stuck in the floor)
void(vector spot) NS_Stick =
{
	if (self.owner.classname != "player")
	{
		remove (self);
		return;
	}
	if (NS_Count (self.owner) >= NS_MAX_PCS)
		NS_MakeRoom (self.owner);
	self.fg_born = time;
	self.classname = "netsend_pc";
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.avelocity = '0 0 0';
	self.touch = SUB_Null;
	self.think = NS_Think;
	self.nextthink = time + 0.05;
	self.ns_state = 2;
	self.ns_t = time;
	setmodel (self, "progs/netsend_pc.md3");
	setsize (self, '-14 -14 0', '14 14 38');		// low enough to JUMP onto (a jump is 45): the PC is solid like the TF sentry, review 2026-11-01
	setorigin (self, spot);
	self.angles = '0 0 0';
	self.angles_y = self.owner.v_angle_y + 180;		// its front (+X) looks back at whoever threw it
	self.ns_yaw0 = self.angles_y;					// the middle of its sweep
	self.solid = SOLID_BBOX;
	self.takedamage = DAMAGE_AIM;		// never times out, but it can be shot to bits (NS_Die)
	self.health = NS_HEALTH;
	self.th_die = NS_Die;
	self.view_ofs = '0 0 50';		// where it looks from, for visible ()
	self.frame = 0;
	self.skin = 1;
	self.ns_scr = spawn ();
	self.ns_scr.classname = "netsend_screen";
	self.ns_scr.movetype = MOVETYPE_NONE;
	self.ns_scr.solid = SOLID_NOT;
	setmodel (self.ns_scr, "progs/netsend_scr.md3");
	NS_ScreenSync ();
	pointparticles (particleeffectnum ("netsend_pop"), spot + '0 0 8', VEC_ORIGIN, 1);
	FG_Snd (self, CHAN_AUTO, "weapons/goopop.wav", 0.6, 1);
};

// the disk in the air: lost if it has not stuck after NS_LIFE_DISK seconds (the magazine gets it back)
void() NS_DiskThink =
{
	self.nextthink = time + 0.1;
	if (self.owner.classname != "player")
	{
		remove (self);
		return;
	}
	if (time - self.fg_born > NS_LIFE_DISK)
	{
		NS_Refund (self.owner);
		remove (self);
	}
};

// the disk hit something. Only the world takes it: a monster, a player or a door bounces it (the engine does that).
// A floor is where it sticks; a wall or a ceiling is just another bounce
void() NS_DiskTouch =
{
	local vector v, n, spot;

	if (other != world)
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		NS_Refund (self.owner);
		remove (self);
		return;
	}
	v = normalize (self.velocity);
	traceline (self.origin - v * 8, self.origin + v * 24, TRUE, self);
	n = trace_plane_normal;
	spot = trace_endpos;
	if (trace_fraction == 1 || n_z < 0.7)
		return;
	NS_Stick (spot);
};

// sv_cheats test: impulse 80 stands a PC on the floor 70 units ahead of you, facing you (no throw needed); called from Jetpack_Frame
void() NS_Test =
{
	local entity d, me;

	if (self.impulse != 80 || !autocvar_sv_cheats)
		return;
	self.impulse = 0;
	makevectors ('0 1 0' * self.v_angle_y);
	traceline (self.origin + v_forward * 70, self.origin + v_forward * 70 - '0 0 120', TRUE, self);
	d = spawn ();
	d.owner = self;
	d.classname = "netsend_disk";
	me = self;
	self = d;
	NS_Stick (trace_endpos);
	self = me;
};

// the hand lets go (FunGun_ViewFrame): the disk flies out of the muzzle, spinning like a frisbee
void() NS_Throw =
{
	local entity d;

	makevectors (self.v_angle);
	d = spawn ();
	d.owner = self;
	d.classname = "netsend_disk";
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_BBOX;
	d.fg_born = time;
	d.velocity = v_forward * NS_THROW + v_up * 60;
	d.avelocity_y = 900;
	d.bouncefactor = 0.35;		// DarkPlaces: keeps this much of its speed at each bounce (default 0.5)
	d.bouncestop = 0.1;
	d.touch = NS_DiskTouch;
	d.think = NS_DiskThink;
	d.nextthink = time + 0.1;
	setmodel (d, "progs/netsend_disk.md3");		// frame 0: the disk, flying flat
	setsize (d, '-5 -5 -1', '5 5 1');
	setorigin (d, FG_Muzzle (24));
	self.punchangle_x = -4;
};
