/*
================
BKLAN3 TVs (owner, 2026-10-31: "TVs that randomly play these videos with low volume"): bk_tv
	A flat screen drawn with progs/bk_tvscr.md3 (a 48 x 36 unit quad facing +x, "scale" makes it bigger) that plays the
	owner's clips, one after another in random order, with the sound of the clip at low volume.
	Key "angle" = the way the screen faces. The map brushes make the TV's casing (make_bklan_v4.py tv()).

How it plays (build_bklan_tv.py): there is no video in the world, so every clip is cut into chunks (62 new frames, 6.2 s
at 10 fps), each chunk is a shader (animmap of 64 frames: the last two are the next chunk's first two) and a skin of the
screen model. A shader's animmap clock starts when the client first gets the entity, so the TV does not change the skin
of one entity: every BKTV_CHUNK seconds it spawns a new screen entity with the next chunk's skin and removes the old one
(the same server frame, so the client swaps them without a blink), and the new one starts at frame 0. The two spare
frames let the swap be up to 0.2 s late without a jump. The clip's sound starts with its first chunk.
================
*/

float	BKTV_VOL	= 0.35;		// "low volume"
float	BKTV_ATTN	= 2.2;		// heard in the room, not across the map

.float	tv_vid;		// the clip that is playing
.float	tv_chunk;	// the chunk that goes on next
.float	tv_daniel_only;	// 1 = cycle exclusively through Daniel videos (clips 8..11)
.entity	tv_scr;		// the screen entity on show now

float(float not) BKTV_Pick =
{
	local float v;

	v = floor (random () * BKTV_CLIPS);
	if (v >= BKTV_CLIPS)
		v = BKTV_CLIPS - 1;
	if (v == not)
		v = v + 1;
	if (v >= BKTV_CLIPS)
		v = 0;
	return v;
};

// a screen entity with this skin, in place of the old one
void(float sk) BKTV_Screen =
{
	local entity e;

	e = spawn ();
	e.classname = "bk_tvscr";
	e.movetype = MOVETYPE_NONE;
	e.solid = SOLID_NOT;
	setmodel (e, "progs/bk_tvscr.md3");
	setsize (e, VEC_ORIGIN, VEC_ORIGIN);
	e.scale = self.scale;
	e.angles = self.angles;
	e.skin = sk;
	setorigin (e, self.origin);
	if (self.tv_scr)
		remove (self.tv_scr);
	self.tv_scr = e;
};

void() BKTV_Think =
{
	if (self.tv_chunk >= BKTV_Chunks (self.tv_vid))
	{
		// the clip is over: another one starts
		if (self.tv_daniel_only)
		{
			self.tv_vid = self.tv_vid + 1;
			if (self.tv_vid > 11 || self.tv_vid < 8)
				self.tv_vid = 8;
		}
		else
			self.tv_vid = BKTV_Pick (self.tv_vid);
		self.tv_chunk = 0;
	}
	BKTV_Screen (BKTV_First (self.tv_vid) + self.tv_chunk);
	if (bm_cvar_dev)
		dprint (strcat ("bktv: t=", ftos (time), " clip ", ftos (self.tv_vid), " chunk ", ftos (self.tv_chunk), "\n"));
	if (self.tv_chunk == 0)
		sound (self, CHAN_VOICE, BKTV_Sound (self.tv_vid), BKTV_VOL, BKTV_ATTN);
	self.tv_chunk = self.tv_chunk + 1;
	if (self.nextthink < time - 1)
		self.nextthink = time;
	self.nextthink = self.nextthink + BKTV_CHUNK;
};

void() bk_tv =
{
	BKTV_Precache ();
	self.classname = "bk_tv";
	self.movetype = MOVETYPE_NONE;
	self.solid = SOLID_NOT;
	if (self.scale <= 0)
		self.scale = 1;
	if (self.cnt >= 8 && self.cnt <= 11)
	{
		self.tv_daniel_only = TRUE;
		self.tv_vid = floor (self.cnt);
	}
	else
	{
		self.tv_vid = floor (random () * BKTV_CLIPS);
		if (self.tv_vid >= BKTV_CLIPS)
			self.tv_vid = BKTV_CLIPS - 1;
	}
	self.tv_chunk = 0;
	BKTV_Screen (BKTV_First (self.tv_vid));
	self.think = BKTV_Think;
	self.nextthink = time + 0.6 + random () * 2.4;
};

// ---------------------------------------------------------------- test aid (sv_cheats 1): impulse 91 puts a 2x TV 90 units in front of you
void() BKTV_Test =
{
	local entity e, oself;

	if (self.impulse != 91 || !cvar ("sv_cheats"))
		return;
	self.impulse = 0;
	makevectors (self.v_angle);
	e = spawn ();
	e.origin = self.origin + v_forward * 90 + '0 0 8';
	e.angles = '0 0 0';
	e.angles_y = self.angles_y + 180;
	e.scale = 2;
	oself = self;
	self = e;
	bk_tv ();
	self = oself;
};
