/*
================
THE LAPTOP GUN (see ltgun_defs.qc for the rules and numbers)

Hooks (patch_ltgun_combat.py, which unhooks the sniper rifle): W_WeaponFrame runs LtGun_PlayerFrame every frame and lets
LtGun_Frame handle the fire button for IT_NAILGUN (it types, then sends the head, so W_Attack never sees the laptop),
PutClientInServer runs LtGun_Spawn, and the obituary checks ltg_inflicting.
================
*/

void() LtGun_PrecacheVideo =
{
	local float k;

	if (ltg_vid_precached)
		return;
	ltg_vid_precached = TRUE;
	precache_model ("progs/ltg_view.md3");
	k = 0;
	while (k < LTG_VARIANTS)
	{
		precache_model (strcat ("progs/ltg_type_", ftos (k), ".md3"));
		k = k + 1;
	}
};

void() LtGun_Precache =
{
	precache_model ("progs/ltg_v3d.md3");
	if (cvar ("ltg_video"))
		LtGun_PrecacheVideo ();
	precache_model ("progs/ltg_p.md3");
	precache_model ("progs/ltg_g.md3");
	precache_model ("progs/ltg_head.md3");
	precache_model ("progs/ltg_aura.md3");
	precache_sound ("ltgun/canis.wav");
	precache_sound ("ltgun/type.wav");
	precache_sound ("ltgun/send.wav");
	precache_sound ("ltgun/zap.wav");
	precache_sound ("ltgun/hit.wav");
	precache_sound ("ltgun/null.wav");
};

// the typing copy's model name as a constant: weaponmodel keeps the string, and a strcat () tempstring is overwritten by
// later QC before the engine reads it (wrong / flickering model, "not precached" warnings)
string(float v) LtGun_TypeModel =
{
	if (v == 0)		return "progs/ltg_type_0.md3";
	if (v == 1)		return "progs/ltg_type_1.md3";
	if (v == 2)		return "progs/ltg_type_2.md3";
	if (v == 3)		return "progs/ltg_type_3.md3";
	if (v == 4)		return "progs/ltg_type_4.md3";
	if (v == 5)		return "progs/ltg_type_5.md3";
	if (v == 6)		return "progs/ltg_type_6.md3";
	if (v == 7)		return "progs/ltg_type_7.md3";
	if (v == 8)		return "progs/ltg_type_8.md3";
	if (v == 9)		return "progs/ltg_type_9.md3";
	if (v == 10)		return "progs/ltg_type_10.md3";
	if (v == 11)		return "progs/ltg_type_11.md3";
	if (v == 12)		return "progs/ltg_type_12.md3";
	if (v == 13)		return "progs/ltg_type_13.md3";
	if (v == 14)		return "progs/ltg_type_14.md3";
	return "progs/ltg_type_15.md3";
};

// the held model: the typing one while the laptop is busy. The typing film is a shader animmap, which the engine runs on
// the clock, not from the moment you pressed fire: there are LTG_VARIANTS copies of it, each starting its loop at a
// different moment, and ltg_var (picked when fire was pressed) is the one whose first frame is showing right now
string(entity p) LtGun_VModel =
{
	if (!bm_cvar_ltg_video)
		return "progs/ltg_v3d.md3";		// the 3D laptop (build_laptop_gun.py): frames 0-11 idle, 12-33 typing and lightning
	LtGun_PrecacheVideo ();
	if (p.ltg_phase >= 1)
		return LtGun_TypeModel (p.ltg_var);
	return "progs/ltg_view.md3";
};

// which typing copy starts its film from the beginning at this very moment
float() LtGun_Variant =
{
	local float g;

	g = floor ((time - LTG_CLOCK_LAG) * LTG_ANIM_FPS);
	g = g - LTG_ANIM_N * floor (g / LTG_ANIM_N);		// the frame the clock is on
	g = floor (g / (LTG_ANIM_N / LTG_VARIANTS) + 0.5);
	if (g >= LTG_VARIANTS)
		g = 0;
	return g;
};

// ---------------------------------------------------------------- the head

// the cards (head and cables) turn to face whoever is looking at them; the head also shows the picture
// that matches the viewer's side of it (frame k = seen from k * 15 degrees anticlockwise of its face) and wobbles
float() LtGun_HeadCustomize =
{
	local float v, a, w;

	v = vectoyaw (other.origin - self.origin);
	a = v - self.ltg_head;
	a = a - 360 * floor (a / 360);
	self.frame = floor (a / 15 + 0.5);
	if (self.frame > 23)
		self.frame = 0;
	self.angles_y = v + 180;
	w = sin (time * 9 + self.ltg_wob);		// sin is a variant builtin: keep its result in a local
	self.angles_z = 26 * w;
	return TRUE;
};

float() LtGun_AuraCustomize =
{
	self.angles_y = vectoyaw (other.origin - self.origin) + 180;
	self.angles_z = 0;
	return TRUE;
};

void() LtGun_Gone =
{
	if (self.ltg_aura)
		remove (self.ltg_aura);
	sound (self, CHAN_VOICE, "ltgun/null.wav", 1, ATTN_NORM);		// cuts the clip off
	remove (self);
};

// whoever is shocked runs about and is electrocuted a little (LtGun_PlayerFrame)
void(entity e, entity by) LtGun_Shock =
{
	if (e.classname != "player" || e.health <= 0 || e.bm_prot_t > time || time < e.ltg_immune_t)
		return;		// (spawn protection or post-shock immunity: no slow either)
	if ((e == by && !cvar ("ltg_test")) || (teamplay && by && e.team > 0 && e.team == by.team))
		return;
	e.ltg_shock = time + LTG_SHOCK_TIME;
	e.ltg_immune_t = time + LTG_SHOCK_TIME + 0.5;
	e.ltg_by = by;
	e.ltg_zap_t = time + 0.1;
	sound (e, CHAN_ITEM, "ltgun/zap.wav", 1, ATTN_NORM);
	centerprint (e, "ZAPPED!\n");
};

void() LtGun_Touch =
{
	local entity e;

	if (other == self.owner)
		return;
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		LtGun_Gone ();
		return;
	}
	if (other.takedamage)
	{
		ltg_inflicting = TRUE;
		T_Damage (other, self, self.owner, LTG_DAMAGE);
		ltg_inflicting = FALSE;
		LtGun_Shock (other, self.owner);
	}
	e = bm_player_head;
	while (e)
	{
		if (e != other && (e != self.owner || cvar ("ltg_test")) && vlen (e.origin - self.origin) <= LTG_RADIUS)		// ltg_test 1: the owner can be shocked too (a test aid)
			LtGun_Shock (e, self.owner);
		e = e.bm_player_next;
	}
	ltg_inflicting = TRUE;
	if (other.takedamage)
		T_RadiusDamage (self, self.owner, LTG_SPLASH_DMG, other);
	else
		T_RadiusDamage (self, self.owner, LTG_SPLASH_DMG, world);
	ltg_inflicting = FALSE;
	sound (self, CHAN_AUTO, "ltgun/hit.wav", 1, ATTN_NORM);
	sendParticle ("ltg_boom", self.origin, '0 0 0', 1, 0);
	LtGun_Gone ();
};

var float	autocvar_ltg_test = 0;

// the nearest enemy player the head can see ahead of it (inside the LTG_CONE cone, no wall between)
entity() LtGun_Seek =
{
	local entity e, best;
	local float d, bd;
	local vector dir, to;

	dir = normalize (self.velocity);
	best = world;
	bd = LTG_SEEK;
	e = bm_player_head;
	while (e)
	{
		if (e != self.owner && e.health > 0 && !(e.flags & FL_NOTARGET) && !(e.items & IT_INVISIBILITY) && !(teamplay && self.owner && e.team > 0 && e.team == self.owner.team))
		{
			to = e.origin - self.origin;
			d = vlen (to);
			if (d < bd && (normalize (to) * dir) > LTG_CONE)
			{
				traceline (self.origin, e.origin, TRUE, self);
				if (trace_fraction == 1)
				{
					best = e;
					bd = d;
				}
			}
		}
		e = e.bm_player_next;
	}
	return best;
};

// every 0.03 s: home on a visible enemy ahead, else weave smoothly along launch heading
void() LtGun_Think =
{
	local entity o, e;
	local vector tgt, want, dir;
	local float k, sw;

	o = self.owner;
	if (time > self.ltg_born + LTG_LIFE || o.classname != "player")
	{
		sendParticle ("ltg_boom", self.origin, '0 0 0', 1, 0);
		LtGun_Gone ();
		return;
	}
	if (autocvar_ltg_test >= 2)
	{
		self.velocity = '0 0 0';		// test aid: the head hangs where it was made, its face towards you, so you can walk round it
		self.ltg_born = time;
		self.nextthink = time + 0.1;
		return;
	}
	// lock-on: tracks a visible enemy until he stays out of sight for LTG_LOSE seconds
	e = self.ltg_lock;
	if (e && (e.health <= 0 || e.classname != "player" || vlen (e.origin - self.origin) > LTG_SEEK * 2))
		e = world;
	if (e)
	{
		traceline (self.origin, e.origin, TRUE, self);
		if (trace_fraction == 1)
			self.ltg_blind = 0;
		else if (!self.ltg_blind)
			self.ltg_blind = time;
		else if (time - self.ltg_blind > LTG_LOSE)
			e = world;
	}
	else
		e = LtGun_Seek ();
	if (e && !self.ltg_lock)
	{
		self.ltg_blind = 0;
		if (cvar ("ltg_test"))
			dprint (strcat ("ltg lock on ", e.netname, " at ", ftos (vlen (e.origin - self.origin)), "\n"));
		sound (self, CHAN_AUTO, "ltgun/zap.wav", 0.6, ATTN_NORM);
	}
	self.ltg_lock = e;

	dir = normalize (self.velocity);
	if (e)
	{
		// lead the target slightly so straight-line sprinting does not outrun the packet
		k = vlen (e.origin - self.origin) / LTG_SPEED * 0.55;
		tgt = e.origin + e.velocity * k;
		want = tgt - self.origin;
		if (vlen (want) > 24)
		{
			want = normalize (want);
			k = LTG_TURN_LOCK * 0.03;
			if (k > 1)
				k = 1;
			dir = normalize (dir + (want - dir) * k);
		}
	}
	else if (self.ltg_weave_amp != 0)
	{
		sw = sin ((time - self.ltg_born) * 11 + self.ltg_wob);
		dir = normalize (dir + self.ltg_weave_r * (sw * self.ltg_weave_amp * 0.0004));
	}
	self.velocity = dir * LTG_SPEED;
	self.angles = vectoangles (dir);
	self.ltg_head = vectoyaw (dir);
	if (self.ltg_aura)
		setorigin (self.ltg_aura, self.origin);
	self.nextthink = time + 0.03;
};

// launch one DDoS head (idx out of total) with symmetric fan spread & weave
void(float idx, float total) LtGun_Launch =
{
	local entity h, a;
	local vector org, launch_dir;
	local float k, slot, v_step;

	makevectors (self.v_angle);
	self.ammo_nails = self.ammo_nails - 1;		// the LAN magazine reads this back (bm_reload.qc)
	self.currentammo = self.ammo_nails;
	self.show_hostile = time + 1;
	player_shot1 ();
	sound7 (self, CHAN_WEAPON, "ltgun/send.wav", 0.9, ATTN_NORM, 95 + idx * 10);

	slot = idx - (total - 1) * 0.5;
	v_step = (idx - floor (idx / 2) * 2) - 0.5;
	if (total <= 1)
		launch_dir = v_forward;
	else
		launch_dir = normalize (v_forward + v_right * (slot * 0.095) + v_up * (v_step * 0.035));

	k = 28;
	if (cvar ("ltg_test") >= 2)
		k = 110;		// test aid: the head hangs 110 units away, still, so you can walk round it
	traceline (self.origin + '0 0 16', self.origin + '0 0 16' + launch_dir * k, TRUE, self);
	org = trace_endpos - launch_dir * 2;

	h = spawn ();
	h.owner = self;
	h.classname = "ltg_head";
	h.movetype = MOVETYPE_FLYMISSILE;
	h.solid = SOLID_BBOX;
	setmodel (h, "progs/ltg_head.md3");
	setsize (h, '-6 -6 -6', '6 6 6');
	setorigin (h, org);
	h.velocity = launch_dir * LTG_SPEED;
	h.angles = vectoangles (launch_dir);
	h.ltg_head = vectoyaw (launch_dir);
	if (cvar ("ltg_test") >= 2)
		h.ltg_head = h.ltg_head + 180;
	h.ltg_wob = random () * 6;
	h.ltg_weave_r = v_right;
	h.ltg_weave_amp = slot * 140;
	h.ltg_born = time;
	h.touch = LtGun_Touch;
	h.think = LtGun_Think;
	h.nextthink = time + 0.03;
	h.customizeentityforclient = LtGun_HeadCustomize;
	h.traileffectnum = particleeffectnum ("ltg_trail");

	if (cvar ("ltg_test") == 3)
	{
		sound (h, CHAN_VOICE, "ltgun/canis.wav", 1, LTG_SOUND_ATTN);
		return;		// test aid: the head alone, no cables
	}
	if (cvar ("ltg_aura"))		// the cables and wi-fi round the head: off unless ltg_aura 1 (the user asked for them off)
	{
		a = spawn ();
		a.owner = h;
		a.classname = "ltg_aura";
		a.movetype = MOVETYPE_NONE;
		a.solid = SOLID_NOT;
		setmodel (a, "progs/ltg_aura.md3");
		setorigin (a, org);
		a.customizeentityforclient = LtGun_AuraCustomize;
		h.ltg_aura = a;
	}

	if (time >= ltg_canis_t)
	{
		ltg_canis_t = time + LTG_CANIS_GAP;
		sound (h, CHAN_VOICE, "ltgun/canis.wav", LTG_CANIS_VOL, LTG_SOUND_ATTN);
	}
	if (self.ltg_hint < 1 && idx == 0)
	{
		self.ltg_hint = self.ltg_hint + 1;
		if (self.ishuman == 1)
			centerprint (self, "Hold fire to queue a DDoS salvo of homing heads!");
	}
};

// ---------------------------------------------------------------- the player side

// top of W_WeaponFrame, every frame: the held model, and the shock
void() LtGun_PlayerFrame =
{
	local vector v;
	local float z, sp, f;

	if (self.weapon != IT_NAILGUN || self.bm_rl_slot == BM_NG)
	{
		self.ltg_phase = 0;
		self.ltg_queue = 0;
		self.ltg_salvo_idx = 0;
		self.ltg_salvo_total = 0;
	}
	else if (self.meleeing != 1 && self.throwing != 1)
	{
		if (!self.v_weapon_position_helper)
			self.weaponmodel = LtGun_VModel (self);		// (with the sway helper, custom_effects.qc picks the model)
		if (!bm_cvar_ltg_video)
		{
			if (self.ltg_phase == 1)
			{
				// rapid typing loop (frames 12..29) while queuing DDoS packets
				f = floor (time * 24);
				self.weaponframe = 12 + (f - 18 * floor (f / 18));
			}
			else if (self.ltg_phase == 2)
			{
				// lightning surge glow (frames 30..33) while unleashing the salvo
				f = floor (time * 20);
				self.weaponframe = 30 + (f - 4 * floor (f / 4));
			}
			else
			{
				f = floor (time * 10);
				self.weaponframe = f - 12 * floor (f / 12);		// the idle loop
			}
		}
	}

	if (self.ltg_shock <= 0)
		return;
	if (self.health <= 0 || time >= self.ltg_shock)
	{
		self.ltg_shock = 0;
		return;
	}
	// the shock slows horizontal movement to LTG_SHOCK_SPEED while still letting players jump & rocket-jump!
	v = self.velocity;
	z = v_z;
	v_z = 0;
	sp = vlen (v);
	if (sp > LTG_SHOCK_SPEED)
		v = normalize (v) * LTG_SHOCK_SPEED;
	v_z = z;
	self.velocity = v;
	// the electrocution: a little damage and sparks (no screen flash: v_cshift is persistent client state and it stuck blue)
	if (time >= self.ltg_zap_t)
	{
		self.ltg_zap_t = time + LTG_ZAP_EVERY;
		if (cvar ("ltg_test"))
			dprint (strcat ("ltg zap: health ", ftos (self.health), " speed ", ftos (vlen (self.velocity)), "\n"));
		sendParticle ("ltg_zap", self.origin + '0 0 20', '0 0 0', 1, 0);
		sound (self, CHAN_ITEM, "ltgun/zap.wav", 0.7, ATTN_NORM);
		ltg_inflicting = TRUE;
		// the zapper left: no damage (self-damage made a death here a suicide, and a reused slot must not get the kill)
		if (self.ltg_by.classname == "player")
			T_Damage (self, self.ltg_by, self.ltg_by, LTG_ZAP_DMG);
		ltg_inflicting = FALSE;
	}
};

// W_WeaponFrame, once attack_finished has passed: TRUE = the laptop is in hand and took care of the fire button
float() LtGun_Frame =
{
	if (self.weapon != IT_NAILGUN)
	{
		self.ltg_phase = 0;
		self.ltg_queue = 0;
		self.ltg_salvo_idx = 0;
		self.ltg_salvo_total = 0;
		return FALSE;
	}
	if (self.health <= 0)
	{
		self.ltg_phase = 0;
		self.ltg_queue = 0;
		return TRUE;
	}
	if (self.ltg_phase == 1)
	{
		// holding fire queues extra DDoS packets up to ltg_qmax; releasing (or filling max + 1 beat) unleashes the salvo
		if (self.button0)
		{
			if (time >= self.ltg_qnext && self.ltg_queue < self.ltg_qmax)
			{
				self.ltg_queue = self.ltg_queue + 1;
				self.ltg_qnext = time + LTG_QUEUE_STEP;
				sound7 (self, CHAN_WEAPON, "ltgun/type.wav", 0.85, ATTN_NORM, 100 + self.ltg_queue * 14);
				if (self.ishuman == 1)
					centerprint (self, strcat ("DDoS FLOOD: ", ftos (self.ltg_queue), " / ", ftos (self.ltg_qmax), " PACKETS\n"));
			}
		}
		if (time >= self.ltg_t && (!self.button0 || self.ltg_queue >= self.ltg_qmax))
		{
			self.ltg_phase = 2;
			self.ltg_salvo_total = self.ltg_queue;
			self.ltg_salvo_idx = 0;
			self.ltg_qnext = time;
			self.ltg_t = time + LTG_REFIRE;
			if (self.ishuman == 1 && self.ltg_salvo_total >= 2)
				centerprint (self, strcat ("SENT ", ftos (self.ltg_salvo_total), "-PACKET DDoS FLOOD!\n"));
		}
		return TRUE;
	}
	if (self.ltg_phase == 2)
	{
		// rapid-fire burst stream of all queued heads
		while (self.ltg_salvo_idx < self.ltg_salvo_total && time >= self.ltg_qnext)
		{
			if (self.ammo_nails < 1)
			{
				self.ltg_salvo_idx = self.ltg_salvo_total;
				self.ltg_t = time + LTG_REFIRE;
				self.attack_finished = time + 0.25;
			}
			else
			{
				SuperDamageSound ();
				LtGun_Launch (self.ltg_salvo_idx, self.ltg_salvo_total);
				self.ltg_salvo_idx = self.ltg_salvo_idx + 1;
				self.ltg_qnext = self.ltg_qnext + LTG_SALVO_GAP;
				if (self.ltg_salvo_idx >= self.ltg_salvo_total)
				{
					self.ltg_t = time + LTG_REFIRE;
					self.attack_finished = time + 0.25;
				}
			}
		}
		if (self.ltg_salvo_idx >= self.ltg_salvo_total && time >= self.ltg_t)
		{
			self.ltg_phase = 0;
			self.ltg_queue = 0;
			self.ltg_salvo_idx = 0;
			self.ltg_salvo_total = 0;
		}
		return TRUE;
	}
	if (self.button0 && W_CheckNoAmmo ())
	{
		self.ltg_phase = 1;
		self.ltg_queue = 1;
		self.ltg_qmax = floor (self.ammo_nails);
		if (self.ltg_qmax > LTG_MAX_QUEUE)
			self.ltg_qmax = LTG_MAX_QUEUE;
		if (self.ltg_qmax < 1)
			self.ltg_qmax = 1;
		self.ltg_var = LtGun_Variant ();
		self.ltg_t = time + LTG_TYPE_TIME;
		self.ltg_qnext = time + LTG_TYPE_TIME + LTG_QUEUE_STEP;
		sound7 (self, CHAN_WEAPON, "ltgun/type.wav", 0.8, ATTN_NORM, 105);
	}
	return TRUE;
};

// PutClientInServer: a fresh life is not shocked and not typing
void() LtGun_Spawn =
{
	self.ltg_phase = 0;
	self.ltg_queue = 0;
	self.ltg_salvo_idx = 0;
	self.ltg_salvo_total = 0;
	self.ltg_shock = 0;
	self.ltg_immune_t = 0;
	if (self.ishuman == 1)
		stuffcmd (self, "v_cshift 0 0 0 0\n");		// clears a blue tint left by older builds
};

// obituary text
string() LtGun_Death =
{
	local float r;

	r = random ();
	if (r < 0.25)
		return " downloads a virus from ";
	if (r < 0.5)
		return " gets hacked by ";
	if (r < 0.75)
		return " is DDoS'd by ";
	return " loses connection to ";
};
