// Player hats, server side. A hat is attached to its player and placed on the head socket of the current frame
// (bm_hat_tags.qc), so it moves with the player without lagging behind. The engine hides it from its wearer's
// first-person view, and it shows for everyone else and in third person.

void() BM_Hats_Precache =
{
	local float h;
	for (h = 1; h <= BM_HAT_COUNT; h = h + 1)
		precache_model (BM_HatModel (h));
};

void(entity p) BM_Hat_Clear =
{
	local entity e;
	e = p.bm_hat_ent;
	p.bm_hat_ent = world;
	if (e && !bm_wasfreed (e) && e.classname == "bm_hat" && e.owner == p)
		remove (e);
};

// the head socket only exists for the classic player model's standard frames; hide the hat anywhere else
float(entity p) BM_Hat_Visible =
{
	if (p.bm_hat < 1 || p.health <= 0 || p.deadflag || p.bm_obs)
		return FALSE;
	if (p.model != "progs/player_id1.mdl" || p.frame >= BM_HAT_TAG_FRAMES)
		return FALSE;
	if ((p.items & IT_INVISIBILITY) || (p.effects & EF_NODRAW))
		return FALSE;
	return TRUE;
};

void() BM_Hat_Think =
{
	local entity p;
	p = self.owner;
	if (!p || bm_wasfreed (p) || p.bm_hat_ent != self || p.classname != "player" || !BM_Hat_Visible (p))
	{
		if (p && !bm_wasfreed (p) && p.bm_hat_ent == self)
			p.bm_hat_ent = world;
		remove (self);
		return;
	}
	self.nextthink = time + 0.1;
};

// called with self = the player, every frame after its animation has advanced
void() BM_Hat_Update =
{
	local entity e;
	local float af;

	if (!BM_Hat_Visible (self))
	{
		BM_Hat_Clear (self);
		return;
	}
	e = self.bm_hat_ent;
	if (!e || bm_wasfreed (e) || e.classname != "bm_hat" || e.owner != self)
	{
		e = spawn ();
		e.classname = "bm_hat";
		e.owner = self;
		e.exteriormodeltoclient = self;
		e.solid = SOLID_NOT;
		e.movetype = MOVETYPE_NOCLIP;
		setattachment (e, self, "");
		e.think = BM_Hat_Think;
		e.nextthink = time + 0.1;
		e.bm_hat_lastpf = -1;
		e.bm_hat_lastaf = -1;
		self.bm_hat_ent = e;
	}
	if (e.model != BM_HatModel (self.bm_hat))
	{
		setmodel (e, BM_HatModel (self.bm_hat));
		e.bm_hat_lastpf = -1;
		e.bm_hat_lastaf = -1;
	}
	// Attached via setattachment() so origin/angles are local offsets; only touch when player frame changes
	if (self.frame != e.bm_hat_lastpf)
	{
		e.bm_hat_lastpf = self.frame;
		setorigin (e, BM_HatTagPos (self.frame));
		e.angles = BM_HatTagAng (self.frame);
	}
	af = BM_HatAnimFrame (self.bm_hat, time);
	if (af != e.bm_hat_lastaf)
	{
		e.bm_hat_lastaf = af;
		e.frame = af;
	}
};

// "cmd bm_hat N" from a client
void(string s) BM_Hat_Command =
{
	self.bm_hat = bound (0, floor (stof (s)), BM_HAT_COUNT);
};
