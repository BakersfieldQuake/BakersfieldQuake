// JohnWave grenade (Combat+ port of BakersfieldMemes' jw_splash.qc): the grenade model is JohnWave's head
// (progs/grenade.mdl), and where it goes off there is a blue water splash instead of an explosion: a wavy splash
// sprite facing you, wavy rings spreading over the floor, droplets and spray (effectinfo.txt "johnwave_splash"), a
// blue flash and a splash sound.  The damage is unchanged.
// Sprites are made by BakersfieldQuake/source/mm_tools/build_splash_sprites.py.  Compiled before weapons.qc.
// Prefix JG_/jg_ (not JW_): BakersfieldQuake/source/mm_tools/johnwave.qc, the tidal-wave weapon, already owns JW_Splash.
// Hooks (weapons.qc): W_Precache -> JG_SplashPrecache, W_FireGrenade -> JG_GrenadeLaunch, GrenadeTouch ->
// JG_GrenadeBounce, GLhitboxes -> JG_GrenadeAnimate (its think runs the 2.5 s fuse), GrenadeExplode -> JG_Splash.
// ogre.qc: OgreGrenadeExplode -> JG_Splash.

float	jg_splash_fx;

// ---------------------------------------------------------------- the head in flight and on the floor
// In flight the face keeps looking back at the shooter's eyes (no spin).  Each bounce sets it tumbling; once it lies still it rolls
// over onto the back of its head, face up and tipped a little towards the nearest player, so people can see who
// is lying there.
// The grenade box stays a point (a real box gets stuck on Combat+ entities around the player), so a head that comes to rest is lifted
// JG_REST_LIFT units, instead of lying half sunk into the floor.

float	JG_REST_PITCH	= 70;		// 90 = face straight up; a bit less tips the face towards its yaw
float	JG_REST_LIFT	= 9;		// the head is about 22 units tall: its middle is this far above the floor when it lies on its back

.float	jg_bounced;					// hit something: from then on it tumbles
.float	jg_lifted;					// lying still: lifted off the floor and held there

// face the shooter's eyes (alias models take vectoangles' pitch as is: positive tips the face up)
void() JG_GrenadeFaceOwner =
{
	self.angles = vectoangles ((self.owner.origin + self.owner.view_ofs) - self.origin);
};

// the closest living player, so the face on the floor tips towards someone who can see it
entity() JG_NearestPlayer =
{
	local entity	e, best;
	local float		d, bd;

	best = world;
	bd = 100000;
	e = bm_player_head;
	while (e)
	{
		if (e.health > 0)
		{
			d = vlen (e.origin - self.origin);
			if (d < bd)
			{
				bd = d;
				best = e;
			}
		}
		e = e.bm_player_next;
	}
	return best;
};

// called every GLhitboxes tick (0.025 s): self is the grenade
void() JG_GrenadeAnimate =
{
	local entity	p;
	local float		d;

	if (!self.jg_bounced)
		JG_GrenadeFaceOwner ();
	else if ((self.flags & FL_ONGROUND) || vlen (self.velocity) < 4)
	{
		// lying still: ease over onto the back of the head, face up
		self.avelocity = '0 0 0';
		if (!self.jg_lifted && (self.flags & FL_ONGROUND))
		{
			self.jg_lifted = TRUE;
			self.movetype = MOVETYPE_NONE;
			setorigin (self, self.origin + '0 0 1' * JG_REST_LIFT);
		}
		self.angles_x = anglemod (self.angles_x + 180) - 180;
		self.angles_z = anglemod (self.angles_z + 180) - 180;
		// same settling speed as the 0.05 s tick the vanilla version used (0.4 / 0.6 / 0.3 per tick, here per 0.025 s)
		self.angles_x = self.angles_x + (JG_REST_PITCH - self.angles_x) * 0.225;
		self.angles_z = self.angles_z * 0.775;
		p = JG_NearestPlayer ();
		if (p)
		{
			d = anglemod (vectoyaw (p.origin - self.origin) - self.angles_y + 180) - 180;
			self.angles_y = self.angles_y + d * 0.16;
		}
	}
};

// the bounce sound (replaces weapons/bounce.wav in GrenadeTouch)
void() JG_BounceSound =
{
	sound7 (self, CHAN_WEAPON, "grenade/bounce_08_rubber_ball.wav", 1, ATTN_NORM, SNDSPD);
};

// a bounce: tumble, harder the faster it hit
void() JG_GrenadeBounce =
{
	local float	s;

	self.jg_bounced = TRUE;
	s = vlen (self.velocity) / 400;
	if (s > 1)
		s = 1;
	self.avelocity_x = crandom () * 700 * s;
	self.avelocity_y = crandom () * 500 * s;
	self.avelocity_z = crandom () * 700 * s;
};

// called by W_FireGrenade once the velocity is set: face back at the shooter, no spin
void(entity gren, float shooter_yaw) JG_GrenadeLaunch =
{
	gren.avelocity = '0 0 0';
	gren.angles = '0 0 0';
	gren.angles_y = shooter_yaw + 180;
	gren.jg_bounced = FALSE;
	gren.jg_lifted = FALSE;
	gren.traileffectnum = 0;		// no smoke trail (the user asked for it gone; jg_trail is still in effectinfo.txt)
};

void() JG_SplashPrecache =
{
	precache_model ("progs/jw_splash.spr32");
	precache_model ("progs/jw_ripple.spr32");
	precache_sound ("grenade/boom_03_scream_launch.wav");	// voted sounds: make_grenade_sounds.py, grenade_sound_vote
	precache_sound ("funny/fart2.wav");
	precache_sound ("grenade/bounce_08_rubber_ball.wav");
	jg_splash_fx = particleeffectnum ("johnwave_splash");
};

void() jg_splash1	=	[0,		jg_splash2] {self.nextthink = time + 0.06;};
void() jg_splash2	=	[1,		jg_splash3] {self.nextthink = time + 0.06;};
void() jg_splash3	=	[2,		jg_splash4] {self.nextthink = time + 0.06;};
void() jg_splash4	=	[3,		jg_splash5] {self.nextthink = time + 0.06;};
void() jg_splash5	=	[4,		jg_splash6] {self.nextthink = time + 0.06;};
void() jg_splash6	=	[5,		jg_splash7] {self.nextthink = time + 0.06;};
void() jg_splash7	=	[6,		jg_splash8] {self.nextthink = time + 0.06;};
void() jg_splash8	=	[7,		SUB_Remove] {self.nextthink = time + 0.06;};

void() jg_ripple_think =
{
	self.frame = self.frame + 1;
	if (self.frame > 9)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.08;
};

// self is the grenade: it turns into the splash
void() JG_Splash =
{
	local entity	r;

	if (random () < 0.5)
		sound (self, CHAN_VOICE, "grenade/boom_03_scream_launch.wav", 1, ATTN_NORM);
	else
		sound (self, CHAN_VOICE, "funny/fart2.wav", 1, ATTN_NORM);
	pointparticles (jg_splash_fx, self.origin, '0 0 0', 1);

	// rings on the floor, if there is one close underneath
	traceline (self.origin, self.origin - '0 0 72', TRUE, self);
	if (trace_fraction < 1)
	{
		r = spawn ();
		r.movetype = MOVETYPE_NONE;
		r.solid = SOLID_NOT;
		setmodel (r, "progs/jw_ripple.spr32");
		setorigin (r, trace_endpos + '0 0 1');
		r.angles = '90 0 0';					// an oriented sprite: pitched flat onto the floor
		r.frame = 0;
		r.think = jg_ripple_think;
		r.nextthink = time + 0.08;
	}

	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.avelocity = '0 0 0';
	self.angles = '0 0 0';
	self.touch = SUB_Null;
	self.solid = SOLID_NOT;
	setmodel (self, "progs/jw_splash.spr32");
	jg_splash1 ();
};
