/*
==============================================================================

ROB DOB  (the floating head, Combat+)

Inspired by Peeker, the Strogg & Peeker ability in Quake Champions: a drone leaves your body and you fly it round the map
from behind.  Here the drone is a big floating photo head (progs/floathead.mdl), and it is an electricity bomb.

  Fire the Rob Dob (fun gun 1, impulse 61 or 17)
      your body stays where it is (hidden, and nobody targets it) and the head launches out of you.  You see the head
      from behind.  The screen stays its normal colour: there is no Ring of Shadows tint.
  fly       forward / back / strafe = fly where you look (look down and go forward to dive), jump = up, crouch = down.
            It slides along walls and round corners, so it does not get wedged.
  fire      DASH: the head shoots off very fast.  You still steer it with the mouse while it goes.
  fire again while dashing: it blows up.
  hit body  an enemy it touches (cruising or dashing) sets it off at once.
  hit wall  a dash that runs straight into a wall sets it off.  A graze (a corner, a scrape along a wall) does not: it
            slides on, and only goes off if it keeps scraping for FD_GRACE seconds.  Just after a click (FD_DASH_ARM) it
            will not go off on a wall at all, so a click next to a wall is not wasted.
  blast     an electric blast: the stock rocket explosion, lightning arcs, and funny/heh.wav.  You watch it from behind for
            a moment before you are back in your body.
  shot down the head has 60 health: shoot it and it blows up the same way.
  runs out  no time limit: you fly it as long as you like, until it blows up (set fd_flight N to make it pop harmlessly after N seconds)
  recharge  one head per FG_DOB_REGEN seconds

Your body can be hurt the whole time and cannot move or shoot.

  fd_flight N     seconds of flight, 0 = no limit (autocvar_fd_flight)
  fd_dash N       speed of the dash (autocvar_fd_dash, default 2000)

Model:  python3 -E -P BakersfieldQuake\source\mm_tools\build_floathead.py          (floathead.mdl, v_robdob.mdl)
Sounds: python3 -E -P BakersfieldQuake\source\mm_tools\make_floathead_sounds.py BakersfieldQuake\source\mm_tools\out\sound\floathead_tts BakersfieldQuake\sound\floathead
Trails: BakersfieldQuake\source\mm_tools\fh_effectinfo.txt (appended to effectinfo.txt)

==============================================================================
*/

$frame idle1 idle2 idle3 idle4 idle5 idle6 idle7 idle8
$frame open1 open2 open3 open4
$frame rush1 rush2 rush3 rush4
$frame pain1 pain2 pain3 pain4

float	FD_IMPULSE		= 17;
float	FD_SPEED		= 320;		// cruising speed: as fast as a player can run (sv_maxspeed), no faster
float	FD_ACCEL		= 5;		// how fast it turns to a new course (a fraction of the gap per second)
float	FD_ARM			= 0.7;		// seconds after launch before the head may dash (so it cannot be wasted instantly)
float	FD_CAM_BACK		= 92;		// the camera sits this far behind the head...
float	FD_CAM_UP		= 16;		// ...and this far above it
float	FD_DASH_TIME	= 4;		// the dash fizzles out (back to cruising, no bang) after this long
float	FD_DASH_REST	= 0.5;		// seconds between one dash stopping and the next one
float	FD_STEER		= 6;		// how fast the dash turns to where the pilot looks (a fraction of the gap per second)
float	FD_DASH_ARM		= 0.3;		// seconds after the click when a wall cannot set it off (it slides instead)
float	FD_DASH_BOOM	= 0.25;		// seconds after the click before the second click may set it off (so a double click is not a pop)
float	FD_HEADON		= 0.7;		// a dash that hits a wall straight on (cos of the angle to the wall's normal) or more sets it off
float	FD_GRACE		= 1;		// seconds of unbroken scraping along walls before it goes off anyway
float	FD_WATCH		= 2;		// seconds you stay behind the blast, third person, before you are back in your body
float	FD_SONG_LEN		= 5;		// the calc song is cut into slices this long (sound/floathead/calc/c0..)
float	FD_SONG_N		= 60;		// how many slices there are
float	FD_SONG_CHAN	= 5;		// the song's own sound channel: CHAN_AUTO never replaces a sound, so it could not be cut off there
float	FD_SONG_VOL		= 0.2;		// quiet: it is the head's own little computer, not the music of the match
float	FD_HUM_LEN		= 1.36;		// floathead/idle.wav is this long: it is played again each time it ends, all the way through
float	FD_HUM_VOL		= 0.4;		// the constant hum while he is the head, under the calc song
vector	FD_MINS			= '-10 -10 -10';	// the head's own box, small so it fits round corners
vector	FD_MAXS			= '10 10 10';
var float	autocvar_fd_flight = 0;		// 0 = fly it as long as you want
var float	autocvar_fd_dash = 2000;	// speed of the dash
void(entity h, float big) FD_Shock;	// defined with the electricity code below, the blast needs it first
float	FD_CLIENTTYPE_REAL = 1;		// clienttype() result for a real player (the Combat+ defs have no name for it)

.entity	fd_head;			// player: the head he is flying (world = he is not)
.entity	fd_cam;				// player: the camera that sits behind it
.float	fd_oldmove;			// player: his movetype before the head went out
.float	fd_oldsolid;		// player: his solid while the head is out (0 = unchanged)
.float	fd_notarget;		// player: the head set FL_NOTARGET on him (he did not have it), so it takes it off again
.float	fd_btn;				// player: fire was down last frame, it has to be let go before the next click counts
.float	fd_end;				// head: flight is over at this time (0 = no limit)
.float	fd_dashed;			// head: when the dash was clicked
.float	fd_blowing;			// head: ordered to go off, waiting for its think
.float	fd_scrape;			// head: when it started scraping along a wall (0 = not scraping)
.float	fd_fade;			// player: the blast went off, he watches from behind until this time (0 = not watching)
.vector	fd_boomat;			// player: where the blast went off, for the camera to look at
.float	fd_arm;				// head: may dash from this time
.float	fd_charging;		// head: dashing
.float	fd_rushend;			// head: the dash gives up at this time
.float	fd_boom;			// head: already gone off
.float	fd_hum;				// head: when the next hum is due
.float	fd_song_t;			// head: the next slice of the calc song is due at this time
.float	fd_song_n;			// head: which slice of the calc song is next
.entity	fd_hitent;			// head: what its last move ran into
vector	fd_normal;			// the plane the last FD_Move ran into (set whenever it returns FALSE)
.float	fd_big;				// shock: the big electric blast rather than a crackle

// TRUE while p is flying the head or watching its blast (custom_effects.qc hides the held gun then)
float(entity p) FD_Flying =
{
	return (p.fd_head || p.fd_fade);
};

void() FloatHead_Precache =
{
	local float i;

	precache_model ("progs/floathead.mdl");
	precache_model ("progs/v_robdob.mdl");
	precache_model ("progs/s_bubble.spr");
	precache_sound ("floathead/sight1.wav");
	precache_sound ("floathead/sight2.wav");
	precache_sound ("floathead/charge.wav");
	precache_sound ("floathead/pain.wav");
	precache_sound ("floathead/idle.wav");
	precache_sound ("floathead/pop.wav");
	precache_sound ("floathead/boing.wav");
	precache_sound ("weapons/lhit.wav");
	precache_sound ("hackmon/hm_launch.wav");
	precache_sound ("funny/heh.wav");
	i = 0;
	while (i < FD_SONG_N)
	{
		precache_sound (strcat ("floathead/calc/c", ftos (i), ".wav"));
		i = i + 1;
	}
};

float(float v, float lo, float hi) FD_Clamp =
{
	if (v < lo)
		return lo;
	if (v > hi)
		return hi;
	return v;
};

// ---------------------------------------------------------------- the player's side

// while the head is out his body is hidden (alpha, not the Ring of Shadows: that tints the whole screen) and not a target
void(entity p) FD_Hide =
{
	p.alpha = 0.01;
	if (!(p.flags & FL_NOTARGET))
	{
		p.flags = p.flags | FL_NOTARGET;
		p.fd_notarget = TRUE;
	}
};

void(entity p) FD_Unhide =
{
	p.alpha = 0;						// 0 = opaque
	if (p.fd_notarget)
	{
		p.fd_notarget = FALSE;
		if (p.flags & FL_NOTARGET)
			p.flags = p.flags - FL_NOTARGET;
	}
};

// put the player back behind his own eyes and make him visible again
void(entity p) FD_Restore =
{
	if (p.fd_cam)
	{
		remove (p.fd_cam);
		p.fd_cam = world;
	}
	p.clientcamera = p;
	msg_entity = p;
	WriteByte (MSG_ONE, 5);			// svc_setview
	WriteEntity (MSG_ONE, p);
	if (p.fd_oldsolid)
	{
		p.solid = p.fd_oldsolid;
		p.fd_oldsolid = 0;
	}
	if (p.health > 0)					// a body that died meanwhile keeps the death toss
	{
		p.movetype = p.fd_oldmove;
		if (p.movetype == MOVETYPE_NONE)
			p.movetype = MOVETYPE_WALK;
	}
	FD_Unhide (p);
};

// the flight is over (the head is dealt with by the caller)
void(entity p) FD_End =
{
	p.fd_head = world;
	FD_Restore (p);
};

// spawn (and respawn): no head, no camera
void(entity p) FD_Reset =
{
	if (p.fd_head)
	{
		remove (p.fd_head);
		FD_End (p);
	}
	p.fd_head = world;
	p.fd_btn = FALSE;
	FD_Unhide (p);
	if (p.fd_fade)
	{
		p.fd_fade = 0;
		FD_Restore (p);
	}
};

// the camera: behind and a little above the head, along the way the player is looking, pulled in if a wall is in the way
void(entity p) FD_Camera =
{
	local entity	h, c;
	local vector	pos;

	h = p.fd_head;
	c = p.fd_cam;
	makevectors (p.v_angle);
	pos = h.origin - v_forward * FD_CAM_BACK + '0 0 1' * FD_CAM_UP;
	traceline (h.origin, pos, TRUE, h);
	pos = trace_endpos;
	if (trace_fraction < 1)
		pos = pos + trace_plane_normal * 6;
	setorigin (c, pos);
	c.angles = p.v_angle;
};

// ---------------------------------------------------------------- the head

// the head's flight step: move `vel` for `dt` seconds, sliding along anything it runs into so it is never wedged in a
// corner. Returns FALSE if it touched something on the way (fd_hitent is the first thing it touched, fd_normal the plane).
float(entity h, vector vel, float dt) FD_Move =
{
	local vector	end;
	local float		i, hit;

	h.fd_hitent = world;
	hit = FALSE;
	i = 0;
	while (i < 4)
	{
		end = h.origin + vel * dt;
		tracebox (h.origin, FD_MINS, FD_MAXS, end, FALSE, h);
		if (trace_startsolid)
		{
			fd_normal = '0 0 0' - normalize (vel);		// as if head on
			h.velocity = '0 0 0';		// already inside something (a door shut on it): it cannot go anywhere
			return FALSE;
		}
		if (trace_fraction == 1)
		{
			setorigin (h, end);
			break;
		}
		if (!hit)
		{
			h.fd_hitent = trace_ent;
			fd_normal = trace_plane_normal;
		}
		hit = TRUE;
		setorigin (h, trace_endpos);
		dt = dt * (1 - trace_fraction);
		vel = vel - trace_plane_normal * (vel * trace_plane_normal);		// slide along the wall
		i = i + 1;
	}
	h.velocity = vel;
	return !hit;
};

void() FD_Minis_touch =
{
	if (other != world || self.cnt >= 2 || vlen (self.velocity) < 80)
		return;
	self.cnt = self.cnt + 1;
	sound (self, CHAN_BODY, "floathead/boing.wav", 0.7, ATTN_NORM);
};

// six little screaming heads tumble out and bounce about
void() FD_Minis =
{
	local float		i;
	local entity	e;

	i = 0;
	while (i < 6)
	{
		e = spawn ();
		e.classname = "fh_mini";
		e.movetype = MOVETYPE_BOUNCE;
		e.solid = SOLID_TRIGGER;
		setmodel (e, "progs/floathead.mdl");
		setsize (e, '0 0 0', '0 0 0');
		setorigin (e, self.origin);
		e.scale = 0.4;
		e.skin = 1;
		e.effects = EF_FULLBRIGHT;
		e.frame = $rush1 + i - 4 * floor (i / 4);
		e.velocity_x = crandom () * 300;
		e.velocity_y = crandom () * 300;
		e.velocity_z = 200 + random () * 250;
		e.avelocity_x = crandom () * 500;
		e.avelocity_y = crandom () * 700;
		e.avelocity_z = crandom () * 500;
		e.angles_y = random () * 360;
		e.touch = FD_Minis_touch;
		e.think = SUB_Remove;
		e.nextthink = time + 2.5 + random ();
		i = i + 1;
	}
};

// the head goes off in an electric blast: self = the head. Its pilot is not sent back to his body yet: the camera stays
// behind the blast for FD_WATCH seconds (see FD_Frame), so he can see it
void() FD_Detonate =
{
	local entity	p;

	if (self.fd_boom)
		return;
	self.fd_boom = TRUE;
	p = self.owner;
	p.fd_head = world;
	p.fd_fade = time + FD_WATCH;
	p.fd_boomat = self.origin;
	self.classname = "fh_dead";
	sound (self, FD_SONG_CHAN, "misc/null.wav", 1, ATTN_NORM);		// cut the calc song off on the channel it plays on
	sound (self, CHAN_ITEM, "misc/null.wav", 1, ATTN_NORM);		// and the hum
	self.touch = SUB_Null;
	self.takedamage = DAMAGE_NO;
	FD_Shock (self, TRUE);				// an electricity bomb: big lightning arcs round the blast...
	sound (self, CHAN_WEAPON, "weapons/lhit.wav", 1, ATTN_NORM);
	sound (self, CHAN_VOICE, "funny/heh.wav", 1, ATTN_NORM);		// ...and a "heh" on top of the bang
	self.effects = 0;
	setmodel (self, "");
	fg_inflicting = FG_DOB;				// "got a big wet kiss from X's flying head"
	T_MissileTouch ();					// a regular explosion: the stock rocket's blast, damage, sprite and sound
	fg_inflicting = 0;
};

// a think has no 'other': an explosion in mid air
void() FD_Boom =
{
	other = world;
	FD_Detonate ();
};

// the second click: blow the head up from its own think, a moment later (the caller is the pilot, not the head)
void(entity h) FD_Blow =
{
	h.takedamage = DAMAGE_NO;
	h.fd_blowing = TRUE;			// FD_Frame holds it still until the think goes off
	h.fd_charging = FALSE;
	h.velocity = '0 0 0';
	h.think = FD_Boom;
	h.nextthink = time + 0.05;
};

// a teleporter (portal) took the head: self is the trigger, as in teleport_touch. It comes out of the target facing the
// way the target faces and keeps its speed, so a dash goes on through the portal.
void(entity h, entity trig) FD_Portal =
{
	local entity	t;
	local float		spd;

	if (h.teleport_time > time)
		return;
	t = find (world, targetname, trig.target);
	if (!t)
		return;
	SUB_UseTargets ();
	makevectors (t.mangle);
	spd = vlen (h.velocity);
	if (spd < FD_SPEED)
		spd = FD_SPEED;
	spawn_tfog (trig.origin);
	setorigin (h, t.origin + v_forward * 32);
	spawn_tfog (h.origin);
	h.velocity = v_forward * spd;
	h.angles = t.mangle;
	h.teleport_time = time + 0.7;
};

// out of time, or the pilot died: a harmless pop and he is back in his body
void() FD_Pop =
{
	if (self.fd_boom)
		return;
	self.fd_boom = TRUE;
	FD_End (self.owner);
	sound (self, FD_SONG_CHAN, "misc/null.wav", 1, ATTN_NORM);		// cut the calc song off
	sound (self, CHAN_ITEM, "misc/null.wav", 1, ATTN_NORM);		// the hum stops
	sound (self, CHAN_VOICE, "floathead/pop.wav", 1, ATTN_NORM);
	sound (self, CHAN_WEAPON, "floathead/pain.wav", 1, ATTN_NORM);
	SpawnBlood (self.origin, '0 0 120', 40);
	FD_Minis ();
	remove (self);
};

// shot down: Killed() calls this from inside T_Damage, maybe inside somebody's T_RadiusDamage, so go a moment later
void() FD_Die =
{
	self.takedamage = DAMAGE_NO;
	self.velocity = '0 0 0';
	self.movetype = MOVETYPE_NONE;
	self.think = FD_Boom;
	self.nextthink = time + 0.05;
};

void(entity attacker, float damage) FD_Pain =
{
	if (self.pain_finished > time)
		return;
	self.pain_finished = time + 0.6;
	sound (self, CHAN_VOICE, "floathead/pain.wav", 1, ATTN_NORM);
};

// every 0.1 s while it floats: wobble, hum, and the safety nets
void() FD_HeadThink =
{
	local entity	p;

	p = self.owner;
	if (p.fd_head != self || p.health <= 0 || p.classname != "player")
	{
		FD_Pop ();
		return;
	}
	if (self.fd_end && time > self.fd_end)
	{
		centerprint (p, "the Rob Dob ran out of steam\n");
		FD_Pop ();
		return;
	}
	if (!self.fd_charging)
	{
		if (self.pain_finished - time > 0.2)
		{
			self.skin = 1;
			self.frame = $pain1 + FD_Clamp (floor ((0.6 - (self.pain_finished - time)) * 10), 0, 3);
		}
		else
		{
			self.skin = 0;
			self.cnt = self.cnt + 1;
			if (self.cnt > 7)
				self.cnt = 0;
			self.frame = $idle1 + self.cnt;
		}
	}
	if (time >= self.fd_hum)
		{
			// the hum: idle.wav, played again each time it ends, for as long as he is the head
			sound (self, CHAN_ITEM, "floathead/idle.wav", FD_HUM_VOL, ATTN_NORM);
			self.fd_hum = self.fd_hum + FD_HUM_LEN;
			if (self.fd_hum < time)
				self.fd_hum = time + FD_HUM_LEN;		// it fell far behind (a hitch): start again from now
		}
		if (time >= self.fd_song_t)
	{
		// the calc song, one slice every FD_SONG_LEN seconds, quietly, looping
		sound (self, FD_SONG_CHAN, strcat ("floathead/calc/c", ftos (self.fd_song_n), ".wav"), FD_SONG_VOL, ATTN_NORM);
		self.fd_song_n = self.fd_song_n + 1;
		if (self.fd_song_n >= FD_SONG_N)
			self.fd_song_n = 0;
		self.fd_song_t = self.fd_song_t + FD_SONG_LEN;
	}
	self.nextthink = time + 0.1;
};

// ---------------------------------------------------------------- electricity

// the electric arcs of the blast (eight wide arcs for over a second); a small crackle (three arcs) is the other kind.
// self = the arcs, they remove themselves when done
void() FD_ShockThink =
{
	local float		i, n, r, last;
	local vector	e;

	if (self.fd_big)
	{
		n = 8;
		r = 90;
		last = 12;
	}
	else
	{
		n = 3;
		r = 24;
		last = 5;
	}
	if (self.cnt >= last)
	{
		remove (self);
		return;
	}
	self.cnt = self.cnt + 1;
	i = 0;
	while (i < n)
	{
		e = self.origin + '1 0 0' * crandom () * r + '0 1 0' * crandom () * r + '0 0 1' * crandom () * r;
		WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte (MSG_BROADCAST, TE_LIGHTNING2);
		WriteEntity (MSG_BROADCAST, self);
		WriteCoord (MSG_BROADCAST, self.origin_x);
		WriteCoord (MSG_BROADCAST, self.origin_y);
		WriteCoord (MSG_BROADCAST, self.origin_z);
		WriteCoord (MSG_BROADCAST, e_x);
		WriteCoord (MSG_BROADCAST, e_y);
		WriteCoord (MSG_BROADCAST, e_z);
		i = i + 1;
	}
	self.nextthink = time + 0.1;
};

// start the electric arcs where the head is (big = the blast)
void(entity h, float big) FD_Shock =
{
	local entity	sh;

	sh = spawn ();
	sh.classname = "fh_shock";
	sh.movetype = MOVETYPE_NONE;
	sh.solid = SOLID_NOT;
	sh.fd_big = big;
	setorigin (sh, h.origin);
	sh.think = FD_ShockThink;
	sh.nextthink = time + 0.01;
};

// the head ran into something (FD_Move returned FALSE; fd_hitent and fd_normal say what). Sets it off, or lets it slide on.
//   a living enemy                  always goes off, cruising or dashing
//   a wall hit straight on (dash)   goes off, once the click is FD_DASH_ARM old
//   a graze, a corner (dash)        slides on; only FD_GRACE seconds of unbroken scraping set it off
void(entity p, entity h) FD_Touched =
{
	local entity	e;
	local float		boom;

	e = h.fd_hitent;
	boom = FALSE;
	if (e && e != p && e.health > 0 && e.takedamage && (e.classname == "player" || (e.flags & FL_MONSTER)))
		boom = TRUE;
	else if (h.fd_charging)
	{
		if (time > h.fd_dashed + FD_DASH_ARM && 0 - (h.movedir * fd_normal) >= FD_HEADON)
			boom = TRUE;
		else if (!h.fd_scrape)
			h.fd_scrape = time;
		else if (time - h.fd_scrape > FD_GRACE)
			boom = TRUE;
	}
	if (boom)
		FD_Blow (h);
};

// fire pressed: the head shoots off to whatever is under the crosshair; from now on it steers to where the pilot looks
void(entity p) FD_Dash =
{
	local entity	h;
	local vector	org, dir;

	h = p.fd_head;
	makevectors (p.v_angle);
	org = p.fd_cam.origin;
	traceline (org, org + v_forward * 4096, FALSE, h);
	dir = trace_endpos - h.origin;
	if (vlen (dir) < 80)
		dir = v_forward;
	dir = normalize (dir);
	h.movedir = dir;
	h.velocity = dir * autocvar_fd_dash;
	h.angles = vectoangles (dir);
	h.fd_charging = TRUE;
	h.fd_dashed = time;
	h.fd_scrape = 0;
	h.fd_rushend = time + FD_DASH_TIME;
	h.skin = 1;						// mouth open
	sound (h, CHAN_VOICE, "floathead/charge.wav", 1, ATTN_NORM);
};

// ---------------------------------------------------------------- the launch (called from FunGun_Attack, self = the player)

void() FD_Launch =
{
	local entity	h, c;
	local vector	eye;

	makevectors (self.v_angle);
	eye = self.origin + self.view_ofs;
	h = spawn ();
	h.classname = "robdob";
	h.owner = self;
	h.movetype = MOVETYPE_NONE;			// FD_Move flies it, not the engine
	h.solid = SOLID_BBOX;
	h.effects = EF_FULLBRIGHT;			// lit by itself: no glow and no dim light, so the view stays clear
	setmodel (h, "progs/floathead.mdl");
	setsize (h, FD_MINS, FD_MAXS);
	tracebox (eye, FD_MINS, FD_MAXS, eye + v_forward * 56, TRUE, self);
	setorigin (h, trace_endpos - v_forward * 4);
	h.angles = vectoangles (v_forward);
	h.velocity = v_forward * FD_SPEED;
	h.skin = 0;
	h.frame = $idle1;
	h.health = 60;
	h.max_health = 60;
	h.takedamage = DAMAGE_AIM;
	h.th_die = FD_Die;
	h.th_pain = FD_Pain;
	h.netname = "Rob Dob";
	if (autocvar_fd_flight > 0)
		h.fd_end = time + autocvar_fd_flight;
	else
		h.fd_end = 0;
	h.fd_arm = time + FD_ARM;
	h.fd_song_t = time;
	h.fd_song_n = 0;
	h.fd_hum = time;
	h.traileffectnum = particleeffectnum ("fd_trail");
	h.think = FD_HeadThink;
	h.nextthink = time + 0.1;
	sound (h, CHAN_VOICE, "hackmon/hm_launch.wav", 0.6, ATTN_NORM);	// a little computer booting up, not a voice

	c = spawn ();
	c.classname = "robdob_cam";
	c.movetype = MOVETYPE_NONE;
	c.solid = SOLID_NOT;
	setmodel (c, "progs/s_bubble.spr");
	setsize (c, '0 0 0', '0 0 0');
	setorigin (c, eye);

	self.fd_head = h;
	self.fd_cam = c;
	self.fd_btn = TRUE;
	self.fd_oldmove = self.movetype;
	self.fd_oldsolid = self.solid;
	self.movetype = MOVETYPE_NONE;
	self.solid = SOLID_NOT;				// his own body is no wall for the head to fly back into
	self.velocity = '0 0 0';
	FD_Hide (self);

	self.clientcamera = c;
	msg_entity = self;
	WriteByte (MSG_ONE, 5);			// svc_setview
	WriteEntity (MSG_ONE, c);
	FD_Camera (self);
	centerprint (self, "ROB DOB\n\nmove = fly where you look   jump = up   crouch = down\nFIRE = dash (steer with the mouse)   FIRE again = blow up\n");
};

// every frame from W_WeaponFrame (self = the player): TRUE while he is flying the head, which stops him doing anything else
float() FD_Frame =
{
	local entity	h, c;
	local vector	wish;
	local float		mx, my, mz, k, f;

	h = self.fd_head;
	if (!h)
	{
		if (!self.fd_fade)
			return FALSE;
		// the head went off: the camera stays where it was, looking at the blast, until the time is up; then he is back in his body
		if (time >= self.fd_fade || self.health <= 0)
		{
			self.fd_fade = 0;
			FD_Restore (self);
			return FALSE;
		}
		FD_Hide (self);
		self.velocity = '0 0 0';
		c = self.fd_cam;
		if (c)
			c.angles = vectoangles (self.fd_boomat - c.origin);
		return TRUE;
	}

	FD_Hide (self);
	self.velocity = '0 0 0';
	makevectors (self.v_angle);
	if (!self.button0)
		self.fd_btn = FALSE;

	if (h.fd_blowing)
	{
		// ordered to go off: it hangs still until its think fires, a few frames
	}
	else if (h.fd_charging)
	{
		// dashing: jaw drops & fedora pops into the slipstream (open1-4), then chomps wildly while hat floats overhead (rush1-4)
		if (time - h.fd_dashed < 0.16)
			h.frame = $open1 + FD_Clamp (floor ((time - h.fd_dashed) * 25), 0, 3);
		else
		{
			f = floor (time * 20);
			f = f - 4 * floor (f / 4);
			h.frame = $rush1 + f;
		}
		if (self.button0 && !self.fd_btn && time > h.fd_dashed + FD_DASH_BOOM)
		{
			self.fd_btn = TRUE;
			FD_Blow (h);
		}
		else if (time > h.fd_rushend)
		{
			h.fd_charging = FALSE;
			h.velocity = h.movedir * FD_SPEED;
			h.skin = 0;
			h.fd_arm = time + FD_DASH_REST;
		}
		else
		{
			k = FD_Clamp (frametime * FD_STEER, 0, 1);
			h.movedir = normalize (h.movedir + (v_forward - h.movedir) * k);
			h.velocity = h.movedir * autocvar_fd_dash;
			h.angles = vectoangles (h.movedir);
			if (FD_Move (h, h.velocity, frametime))
				h.fd_scrape = 0;		// a clear step: the scrape (if any) is over
			else
				FD_Touched (self, h);
		}
	}
	else
	{
		mx = FD_Clamp (self.movement_x / 200, -1, 1);
		my = FD_Clamp (self.movement_y / 200, -1, 1);
		mz = 0;
		if (self.button2)
			mz = 1;
		if (self.movement_z < 0)
			mz = mz - 1;
		wish = v_forward * mx + v_right * my + '0 0 1' * mz;
		if (vlen (wish) > 1)
			wish = normalize (wish);
		k = FD_Clamp (frametime * FD_ACCEL, 0, 1);
		h.velocity = h.velocity + (wish * FD_SPEED - h.velocity) * k;
		if (!FD_Move (h, h.velocity, frametime))		// it slides off walls: a bump just turns it...
			FD_Touched (self, h);						// ...but a living enemy sets it off
		h.angles = vectoangles (v_forward);
		if (self.button0 && !self.fd_btn && time > h.fd_arm && !h.fd_blowing)
		{
			self.fd_btn = TRUE;
			FD_Dash (self);
		}
	}
	FD_Camera (self);
	return TRUE;
};

// ---------------------------------------------------------------- hooks the old floating head monster had

// impulse 17: pick the Rob Dob
void() FloatHead_Summon =
{
	FunGun_Select (FG_DOB);
};

// the deathmatch spawner is gone (the head is the player's now)
void() FloatHead_StartSpawner =
{
};
