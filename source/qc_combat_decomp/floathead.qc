#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
==============================================================================

ROB DOB  (the floating head, Combat+)

Inspired by Peeker, the Strogg & Peeker ability in Quake Champions: a drone leaves your body and you fly it round the map
from behind.  Here the drone is a live-action red-fedora Rob head sprite (progs/robhead_proj.spr32), and it is an electricity bomb.

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

Model:  python3 -E -P BakersfieldQuake\source\mm_tools\rob_head_weapon\bake_robhead_all.py  (robhead_proj.spr32, robhead_impact.spr32)
Sounds: python3 -E -P BakersfieldQuake\source\mm_tools\rob_head_sound_vote\apply_robhead_sounds.py
Trails: BakersfieldQuake\source\mm_tools\fh_effectinfo.txt (appended to effectinfo.txt)

==============================================================================
*/

float	FD_IMPULSE		= 17;
float	FD_PROJ_SCALE	= 0.40;		// 108x119 progs/robhead_proj.spr32 -> ~47u in world (matches old floathead.mdl)
float	FD_MINI_SCALE	= 0.16;		// bouncing mini-heads on pop
float	FD_IMP_SCALE	= 0.75;		// 153x153 progs/robhead_impact.spr32 fedora-pop burst
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
float	FD_WATCH		= 0.9;		// snappy post-blast watch before returning to your body (was 2s)
float	FD_SONG_LEN		= 5;		// the calc song is cut into slices this long (sound/floathead/calc/c0..)
float	FD_SONG_N		= 60;		// how many slices there are
float	FD_SONG_CHAN	= 5;		// the song's own sound channel: CHAN_AUTO never replaces a sound, so it could not be cut off there
float	FD_SONG_VOL		= 0.65;		// Pocket Calculator plays clearly as the main flight music
float	FD_HUM_LEN		= 1.20;		// robhead/idle.wav is this long: it is played again each time it ends, all the way through
float	FD_HUM_VOL		= 0.18;		// subtle FPV hover hum underneath Pocket Calculator
vector	FD_MINS			= '-10 -10 -10';	// the head's own box, small so it fits round corners
vector	FD_MAXS			= '10 10 10';
var float	autocvar_fd_flight = 0;		// 0 = fly as long as you want (set fd_flight N for a max duration)
var float	autocvar_fd_dash = 2000;	// speed of the dash
void(entity h, float big) FD_Shock;	// defined with the electricity code below, the blast needs it first
float	FD_CLIENTTYPE_REAL = 1;		// clienttype() result for a real player (the Combat+ defs have no name for it)

// .entity fd_head is declared in robhead_defs.qc so combat.qc can warn pilots when their body is hit
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

float	FD_ENT_XRAY_TARGET = 7;	// CSQC SendEntity type (matches ENT_RD_TARGET in csqc)
float	FD_XRAY_MAX		= 24;		// max simultaneous X-ray targets tracked per drone
.entity	fd_xray_mgr;		// head: 20Hz X-ray scanner thinker
.entity	fd_xray_head;		// head: linked list of active fd_xray_node trackers
.entity	fd_xray_next;		// node: next tracker in head's list
.entity	fd_xray_targ;		// node: tracked enemy/ally entity
.vector	fd_xray_pos;		// node: last synced target origin
.float	fd_xray_hp;			// node: last synced health
.float	fd_xray_flags;		// node: bit 1 = FL_MONSTER, bit 2 = ally
.string	fd_xray_mdl;		// node: target model path
.float	fd_xray_frame;		// node: target animation frame
.float	fd_xray_skin;		// node: target skin
.float	fd_xray_yaw;		// node: target yaw
.float	fd_xray_scale;		// node: target scale
.float	fd_xray_cnt;		// head: count of active tracker nodes
.float	fd_xray_sent_t;		// node: resend by this time even if nothing changed (CSQC drops a target after 0.6 s)
.float	fd_xray_scan_t;		// scanner: next monster findradius in deathmatch

void(entity h) FD_XRayStop;
void(entity pilot, entity h) FD_XRayStart;

// TRUE while p is flying the head or watching its blast (custom_effects.qc hides the held gun then)
float(entity p) FD_Flying =
{
	return (p.fd_head || p.fd_fade);
};

void() FloatHead_Precache =
{
	local float i;

	precache_model ("progs/robhead_proj.spr32");
	precache_model ("progs/robhead_impact.spr32");
	precache_model ("progs/s_bubble.spr");
	precache_sound ("robhead/sight1.wav");
	precache_sound ("robhead/sight2.wav");
	precache_sound ("robhead/charge.wav");
	precache_sound ("robhead/pain.wav");
	precache_sound ("robhead/idle.wav");
	precache_sound ("robhead/pop.wav");
	precache_sound ("robhead/boing.wav");
	precache_sound ("weapons/lhit.wav");
	precache_sound ("robhead/launch.wav");
	precache_sound ("robhead/key1.wav");
	precache_sound ("robhead/key2.wav");
	precache_sound ("robhead/key3.wav");
	precache_sound ("robhead/key4.wav");
	precache_sound ("robhead/key_enter.wav");
	precache_sound ("robhead/key_beep.wav");
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

// while the head is out, the pilot body stays visible & vulnerable with a faint trance glow so rivals can punish unguarded launches!
void(entity p) FD_Hide =
{
	if (!(p.effects & EF_DIMLIGHT))
	{
		p.effects = p.effects | EF_DIMLIGHT;
		p.fd_notarget = TRUE;
	}
};

void(entity p) FD_Unhide =
{
	p.alpha = 0;						// 0 = opaque
	if (p.fd_notarget)
	{
		p.fd_notarget = FALSE;
		if (p.effects & EF_DIMLIGHT)
			p.effects = p.effects - EF_DIMLIGHT;
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
	if (p.ishuman == 1)
	{
		msg_entity = p;
		WriteByte (MSG_ONE, 5);			// svc_setview
		WriteEntity (MSG_ONE, p);
	}
	if (p.fd_oldsolid)
	{
		if (p.health > 0)
			p.solid = p.fd_oldsolid;	// a body that died meanwhile stays not solid (PlayerDie): it used to get a full player box back
		p.fd_oldsolid = 0;
	}
	if (p.health > 0)					// a body that died meanwhile keeps the death toss
	{
		p.movetype = p.fd_oldmove;
		if (p.movetype == MOVETYPE_NONE && p.ishuman == 1)
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
		FD_XRayStop (p.fd_head);
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

// Viewer-relative 64-frame sprite orientation for progs/robhead_proj.spr32:
//   0..15  horizontal 16-angle yaw turnaround
//   16..31 tumbling spin (unused for main drone; used by bouncing mini-heads)
//   32..47 above45 (30-60 deg overhead, 16 yaw angles)
//   48..63 above90 (>60 deg top-down, 16 yaw angles)
float() FD_Customize =
{
	local vector	vieworg, delta;
	local float		dz, hdist, base, rel, d;

	if (other.fd_cam)
		vieworg = other.fd_cam.origin;
	else
		vieworg = other.origin + other.view_ofs;

	delta = vieworg - self.origin;
	dz = delta_z;
	delta_z = 0;
	hdist = vlen (delta);

	if (dz > hdist * 1.73)
	{
		base = 48;
		if (hdist < 16)
			rel = (other.v_angle_y + 180) - self.angles_y;
		else
			rel = vectoyaw (delta) - self.angles_y;
	}
	else if (dz > hdist * 0.58)
	{
		base = 32;
		rel = vectoyaw (delta) - self.angles_y;
	}
	else
	{
		base = 0;
		rel = vectoyaw (delta) - self.angles_y;
	}

	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 22.5 + 0.5);
	if (d >= 16)
		d = 0;
	self.frame = base + d;
	return TRUE;
};

void() FD_ImpactThink =
{
	self.frame = self.frame + 1;
	if (self.frame >= 16)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.05;
};

void(vector org) FD_ImpactFX =
{
	local entity	fx;

	fx = spawn ();
	fx.classname = "fh_impact";
	fx.movetype = MOVETYPE_NONE;
	fx.solid = SOLID_NOT;
	fx.effects = EF_FULLBRIGHT;
	setmodel (fx, "progs/robhead_impact.spr32");
	setsize (fx, '0 0 0', '0 0 0');
	setorigin (fx, org);
	fx.scale = FD_IMP_SCALE;
	fx.frame = 0;
	fx.think = FD_ImpactThink;
	fx.nextthink = time + 0.05;
};

void() FD_Minis_touch =
{
	if (other != world || self.cnt >= 2 || vlen (self.velocity) < 80)
		return;
	self.cnt = self.cnt + 1;
	sound (self, CHAN_BODY, "robhead/boing.wav", 0.7, ATTN_NORM);
};

void() FD_Minis_think =
{
	local float	f;

	if (time >= self.fd_end)
	{
		remove (self);
		return;
	}
	f = self.frame - 16 + 1;
	if (f >= 16)
		f = 0;
	self.frame = 16 + f;
	self.nextthink = time + 0.05;
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
		setmodel (e, "progs/robhead_proj.spr32");
		setsize (e, '0 0 0', '0 0 0');
		setorigin (e, self.origin);
		e.scale = FD_MINI_SCALE;
		e.effects = EF_FULLBRIGHT;
		e.frame = 16 + (i * 3 - 16 * floor ((i * 3) / 16));
		e.velocity_x = crandom () * 300;
		e.velocity_y = crandom () * 300;
		e.velocity_z = 200 + random () * 250;
		e.angles_y = random () * 360;
		e.touch = FD_Minis_touch;
		e.fd_end = time + 2.5 + random ();
		e.think = FD_Minis_think;
		e.nextthink = time + 0.05;
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
	FD_XRayStop (self);
	sound (self, FD_SONG_CHAN, "misc/null.wav", 1, ATTN_NORM);		// cut the calc song off on the channel it plays on
	sound (self, CHAN_ITEM, "misc/null.wav", 1, ATTN_NORM);		// and the hum
	self.touch = SUB_Null;
	self.takedamage = DAMAGE_NO;
	FD_Shock (self, TRUE);				// an electricity bomb: big lightning arcs round the blast...
	FD_ImpactFX (self.origin);			// ...fedora-pop & comic stars burst
	sound (self, CHAN_WEAPON, "weapons/lhit.wav", 1, ATTN_NORM);
	sound (self, CHAN_VOICE, "funny/heh.wav", 1, ATTN_NORM);		// ...and a "heh" on top of the bang
	self.effects = 0;
	self.customizeentityforclient = SUB_Null;
	setmodel (self, "");
	fg_inflicting = FG_DOB;				// "got a big wet kiss from X's flying head"
	if (self.enemy && !bm_wasfreed (self.enemy) && self.enemy.health > 0 && self.enemy.takedamage)
	{
		T_Damage (self.enemy, self, p, 175);
		T_RadiusDamage (self, p, autocvar_player_rocket_radius + 15, self.enemy);
	}
	else
		T_RadiusDamage (self, p, autocvar_player_rocket_radius + 15, world);
	fg_inflicting = 0;
	sound (self, CHAN_AUTO, "weapons/r_exp3.wav", 1, ATTN_NORM);
	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, self.origin_x);
	WriteCoord (MSG_BROADCAST, self.origin_y);
	WriteCoord (MSG_BROADCAST, self.origin_z);
	BecomeExplosion ();
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
	FD_XRayStop (self);
	FD_End (self.owner);
	sound (self, FD_SONG_CHAN, "misc/null.wav", 1, ATTN_NORM);		// cut the calc song off
	sound (self, CHAN_ITEM, "misc/null.wav", 1, ATTN_NORM);		// the hum stops
	sound (self, CHAN_VOICE, "robhead/pop.wav", 1, ATTN_NORM);
	sound (self, CHAN_WEAPON, "robhead/pain.wav", 1, ATTN_NORM);
	SpawnBlood (self.origin, '0 0 120', 40);
	FD_ImpactFX (self.origin);
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
	sound (self, CHAN_VOICE, "robhead/pain.wav", 1, ATTN_NORM);
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
	if (time >= self.fd_hum)
		{
			// the hum: idle.wav, played again each time it ends, for as long as he is the head
			sound (self, CHAN_ITEM, "robhead/idle.wav", FD_HUM_VOL, ATTN_NORM);
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
		WriteEntity (MSG_BROADCAST, world);		// not self: the client merges beams with the same entity, so 8 arcs showed as 1
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
	{
		h.enemy = e;
		boom = TRUE;
	}
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
	if (p.fd_cam)
		org = p.fd_cam.origin;
	else
		org = h.origin;
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
	sound (h, CHAN_VOICE, "robhead/charge.wav", 1, ATTN_NORM);
};

// ---------------------------------------------------------------- X-Ray drone scanner (3D silhouettes + CSQC target stream)

float(entity to, float sendflags) FD_XRaySend =
{
	if (to != self.owner || to.fd_head == world)
		return FALSE;
	WriteByte (MSG_ENTITY, FD_ENT_XRAY_TARGET);
	WriteByte (MSG_ENTITY, sendflags);
	if (sendflags & 1)
	{
		WriteCoord (MSG_ENTITY, self.fd_xray_pos_x);
		WriteCoord (MSG_ENTITY, self.fd_xray_pos_y);
		WriteCoord (MSG_ENTITY, self.fd_xray_pos_z);
		WriteCoord (MSG_ENTITY, self.fd_xray_hp);
		WriteCoord (MSG_ENTITY, self.fd_xray_flags);
		WriteCoord (MSG_ENTITY, self.fd_xray_frame);
		WriteCoord (MSG_ENTITY, self.fd_xray_skin);
		WriteCoord (MSG_ENTITY, self.fd_xray_yaw);
		WriteCoord (MSG_ENTITY, self.fd_xray_scale);
		WriteString (MSG_ENTITY, self.fd_xray_mdl);
		WriteString (MSG_ENTITY, self.netname);
	}
	return TRUE;
};

void(entity h) FD_XRayStop =
{
	local entity	n, nxt;

	if (!h)
		return;
	n = h.fd_xray_head;
	while (n)
	{
		nxt = n.fd_xray_next;
		remove (n);
		n = nxt;
	}
	h.fd_xray_head = world;
	h.fd_xray_cnt = 0;
	if (h.fd_xray_mgr)
	{
		remove (h.fd_xray_mgr);
		h.fd_xray_mgr = world;
	}
};

void(entity h, entity pilot, entity targ) FD_XRayTrack =
{
	local entity	n;
	local float		ally, fl, hp, dyaw;
	local string	nm;

	if (!targ || targ == pilot || targ == h || targ.health <= 0 || !targ.takedamage)
		return;
	if (targ.classname != "player" && !(targ.flags & FL_MONSTER))
		return;

	ally = (teamplay && targ.classname == "player" && targ.team == pilot.team);
	fl = 0;
	if (targ.flags & FL_MONSTER)
		fl = fl | 1;
	if (ally)
		fl = fl | 2;

	n = h.fd_xray_head;
	while (n)
	{
		if (n.fd_xray_targ == targ)
			break;
		n = n.fd_xray_next;
	}
	if (!n)
	{
		if (h.fd_xray_cnt >= FD_XRAY_MAX)
			return;
		n = spawn ();
		n.classname = "fd_xray_node";
		n.owner = pilot;
		n.fd_xray_targ = targ;
		setmodel (n, "progs/s_bubble.spr");
		setsize (n, '0 0 0', '0 0 0');
		n.alpha = 0.0001;
		n.SendEntity = FD_XRaySend;
		n.fd_xray_next = h.fd_xray_head;
		h.fd_xray_head = n;
		h.fd_xray_cnt = h.fd_xray_cnt + 1;
	}

	n.cnt = 1;
	setorigin (n, h.origin);		// stay inside the drone camera's PVS leaf
	if (targ.netname != "")
		nm = targ.netname;
	else if (targ.classname != "")
		nm = targ.classname;
	else
		nm = "HOSTILE";
	hp = max (0, floor (targ.health));
	dyaw = targ.angles_y - n.fd_xray_yaw;
	dyaw = dyaw - 360 * rint (dyaw / 360);
	// ~75 bytes a target: resend only on a change (or the heartbeat), not 20 times a second.
	// The strings ride the same bit: the CSQC reader (robhead_xray.qc) expects them with every update
	if (time < n.fd_xray_sent_t && vlen (targ.origin - n.fd_xray_pos) <= 8 && n.fd_xray_hp == hp && n.fd_xray_flags == fl
		&& n.fd_xray_frame == targ.frame && n.fd_xray_skin == targ.skin && fabs (dyaw) <= 4 && n.fd_xray_scale == targ.scale
		&& n.fd_xray_mdl == targ.model && n.netname == nm)
		return;
	n.fd_xray_pos = targ.origin;
	n.fd_xray_hp = hp;
	n.fd_xray_flags = fl;
	n.fd_xray_mdl = targ.model;
	n.fd_xray_frame = targ.frame;
	n.fd_xray_skin = targ.skin;
	n.fd_xray_yaw = targ.angles_y;
	n.fd_xray_scale = targ.scale;
	n.netname = nm;
	n.fd_xray_sent_t = time + 0.4;	// CSQC hides a target not heard from for 0.6 s
	n.SendFlags = n.SendFlags | 1;
};

void() FD_XRayThink =
{
	local entity	h, p, e, n, prev, nxt;

	h = self.enemy;
	p = self.owner;
	if (!h || h.fd_boom || p.fd_head != h || p.health <= 0)
	{
		if (h)
			FD_XRayStop (h);
		else
			remove (self);
		return;
	}

	n = h.fd_xray_head;
	while (n)
	{
		n.cnt = 0;
		n = n.fd_xray_next;
	}

	e = bm_player_head;
	while (e)
	{
		FD_XRayTrack (h, p, e);
		e = e.bm_player_next;
	}

	// monsters: an 8192 findradius at 20 Hz is costly. In deathmatch (only summons / NPCs) look for
	// new ones every 0.5 s and keep the known ones fresh from their nodes in between
	if (!deathmatch || time >= self.fd_xray_scan_t)
	{
		self.fd_xray_scan_t = time + 0.5;
		e = findradius (h.origin, 8192);
		while (e)
		{
			if ((e.flags & FL_MONSTER) && e.classname != "player")
				FD_XRayTrack (h, p, e);
			e = e.chain;
		}
	}
	else
	{
		n = h.fd_xray_head;
		while (n)
		{
			e = n.fd_xray_targ;
			if (!n.cnt && (n.fd_xray_flags & 1) && !bm_wasfreed (e) && e.classname != "player")
				FD_XRayTrack (h, p, e);
			n = n.fd_xray_next;
		}
	}

	prev = world;
	n = h.fd_xray_head;
	while (n)
	{
		nxt = n.fd_xray_next;
		if (!n.cnt)
		{
			if (prev)
				prev.fd_xray_next = nxt;
			else
				h.fd_xray_head = nxt;
			remove (n);
			h.fd_xray_cnt = h.fd_xray_cnt - 1;
		}
		else
			prev = n;
		n = nxt;
	}

	self.nextthink = time + 0.05;
};

void(entity pilot, entity h) FD_XRayStart =
{
	local entity	m;

	if (pilot.ishuman != 1)
		return;
	m = spawn ();
	m.classname = "fd_xray_mgr";
	m.owner = pilot;
	m.enemy = h;
	m.think = FD_XRayThink;
	m.nextthink = time + 0.01;
	h.fd_xray_mgr = m;
};

// ---------------------------------------------------------------- the launch (called from FunGun_Attack, self = the player)

void() FD_Launch =
{
	local entity	h, c;
	local vector	eye;

	if (self.health <= 0 || self.deadflag || intermission_running || FD_Flying (self)
		|| self.veh_ride != world || Veh_Driving (self) || JohnBird_Flying (self)
		|| EricCannon_Active (self) || MMTank_Driving (self))
		return;
	KY_CamDetach (self);

	makevectors (self.v_angle);
	eye = self.origin + self.view_ofs;
	h = spawn ();
	h.classname = "robdob";
	h.owner = self;
	h.movetype = MOVETYPE_NONE;			// FD_Move flies it, not the engine
	h.solid = SOLID_BBOX;
	h.effects = EF_FULLBRIGHT;			// lit by itself: no glow and no dim light, so the view stays clear
	setmodel (h, "progs/robhead_proj.spr32");
	setsize (h, FD_MINS, FD_MAXS);
	tracebox (eye, FD_MINS, FD_MAXS, eye + v_forward * 56, TRUE, self);
	setorigin (h, trace_endpos - v_forward * 4);
	h.angles = vectoangles (v_forward);
	h.velocity = v_forward * FD_SPEED;
	h.scale = FD_PROJ_SCALE;
	h.frame = 0;
	h.customizeentityforclient = FD_Customize;
	h.health = 40;
	h.max_health = 40;
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
	sound (h, CHAN_VOICE, "robhead/launch.wav", 0.85, ATTN_NORM);	// a little computer booting up, not a voice

	self.fd_head = h;
	self.fd_btn = TRUE;
	local float rseq;
	rseq = 1 + floor (random () * 14);
	if (rseq > 14)
		rseq = 14;
	if (rseq == self.fd_st_seq)
	{
		rseq = rseq + 1;
		if (rseq > 14)
			rseq = 1;
	}
	self.fd_st_seq = rseq;
	self.fd_oldmove = self.movetype;
	self.fd_oldsolid = 0;				// keep pilot body SOLID_SLIDEBOX & hittable (h.owner == self already ignores pilot!)
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	FD_Hide (self);

	if (self.ishuman != 1)
	{
		self.fd_cam = world;
		if (h.fd_end == 0)
			h.fd_end = time + 9;
		return;
	}

	c = spawn ();
	c.classname = "robdob_cam";
	c.movetype = MOVETYPE_NONE;
	c.solid = SOLID_NOT;
	setmodel (c, "progs/s_bubble.spr");
	setsize (c, '0 0 0', '0 0 0');
	setorigin (c, eye);
	self.fd_cam = c;

	self.clientcamera = c;
	msg_entity = self;
	WriteByte (MSG_ONE, 5);			// svc_setview
	WriteEntity (MSG_ONE, c);
	FD_Camera (self);
	FD_XRayStart (self, h);
	if (!self.fd_hint_shown)
	{
		self.fd_hint_shown = TRUE;
		centerprint (self, "Rob Dob: mouse steers | FIRE dash | FIRE again detonate | H recall");
	}
};

// every frame from W_WeaponFrame (self = the player): TRUE while he is flying the head, which stops him doing anything else
float() FD_Frame =
{
	local entity	h, c, oldself;
	local vector	wish;
	local float		mx, my, mz, k;

	h = self.fd_head;
	if (!h)
	{
		if (!self.fd_fade)
			return FALSE;
		// the head went off: the camera stays where it was, looking at the blast, until the time is up; then he is back in his body
		if (time >= self.fd_fade || self.health <= 0 || self.impulse == 86)
		{
			if (self.impulse == 86)
				self.impulse = 0;
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

	if (self.impulse == 86)
	{
		self.impulse = 0;
		oldself = self;
		self = h;
		FD_Pop ();
		self = oldself;
		return FALSE;
	}

	FD_Hide (self);
	self.velocity = '0 0 0';
	if (self.ishuman != 1)
	{
		local entity foe, bestfoe;
		local float fd, bfd;
		local vector tofoe;

		bestfoe = world;
		bfd = 4500;
		foe = bm_player_head;
		while (foe)
		{
			if (foe != self && foe.health > 0 && foe.takedamage && !(foe.flags & FL_NOTARGET) && !(teamplay && foe.team == self.team))
			{
				fd = vlen (foe.origin - h.origin);
				if (fd < bfd)
				{
					bestfoe = foe;
					bfd = fd;
				}
			}
			foe = foe.bm_player_next;
		}
		self.button0 = 0;
		self.button2 = 0;
		self.movement = '200 0 0';
		if (bestfoe)
		{
			tofoe = (bestfoe.origin + '0 0 18') - h.origin;
			self.v_angle = vectoangles (tofoe);
			self.v_angle_x = 0 - self.v_angle_x;
			if (bestfoe.origin_z + 16 > h.origin_z + 10)
				self.button2 = 1;
			else if (bestfoe.origin_z + 24 < h.origin_z)
				self.movement_z = -200;
			traceline (h.origin, bestfoe.origin + '0 0 18', TRUE, h);
			if (!h.fd_charging && time > h.fd_arm && trace_fraction == 1 && bfd < 1250)
				self.button0 = 1;
			else if (h.fd_charging && time > h.fd_dashed + FD_DASH_BOOM && bfd < 90)
				self.button0 = 1;
		}
		else if (time > h.fd_arm + 3.5)
		{
			oldself = self;		// FD_Pop works on the head (as in the impulse 86 branch above): with self = the bot it set fd_boom on the bot and left the head out
			self = h;
			FD_Pop ();
			self = oldself;
			return FALSE;
		}
	}
	makevectors (self.v_angle);
	if (!self.button0)
		self.fd_btn = FALSE;

	if (h.fd_blowing)
	{
		// ordered to go off: it hangs still until its think fires, a few frames
	}
	else if (h.fd_charging)
	{
		if (self.button0 && !self.fd_btn && time > h.fd_dashed + FD_DASH_BOOM)
		{
			self.fd_btn = TRUE;
			FD_Blow (h);
		}
		else if (time > h.fd_rushend)
		{
			h.fd_charging = FALSE;
			h.velocity = h.movedir * FD_SPEED;
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
	if (self.fd_cam)
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
