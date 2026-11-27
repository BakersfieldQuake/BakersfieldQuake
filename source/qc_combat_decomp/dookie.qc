#ifndef COMBATPLUS
#define COMBATPLUS
#endif
// ---------------------------------------------------------------- 5. DOOKIE BAZOOKA MK-IV (fun gun 5, impulse 65, key U)

.float dk_msg;		// next time the charge centerprint may be re-sent (every frame flooded the reliable channel)

void() Dookie_Precache =
{
	precache_model ("progs/v_dookie.md3");
	precache_model ("progs/dookie_proj.spr32");
	precache_model ("progs/dookie_splat.spr32");
	precache_model ("progs/dookie_wall.md3");

	precache_sound ("dookie/dk_charge.wav");
	precache_sound ("dookie/dk_fire.wav");
	precache_sound ("dookie/dk_music.wav");
	precache_sound ("dookie/dk_dotdot.wav");
	precache_sound ("dookie/dk_yell1.wav");
	precache_sound ("dookie/dk_yell2.wav");
	precache_sound ("dookie/dk_yell3.wav");
	precache_sound ("dookie/dk_scream.wav");
	precache_sound ("dookie/dk_splat.wav");
	precache_sound ("dookie/dk_flies.wav");
};

void(entity p) DK_ResetPlayer =
{
	if (p.dk_charging)
		sound (p, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
	p.dk_charging = 0;
	p.dk_cool = 0;
	p.dk_fire_t = 0;
	p.dk_reload_t = 0;
	p.dk_empty = FALSE;
};

void(entity e) DK_PlayFlightYell =
{
	local float r, pitch;

	r = random ();
	pitch = 0.95 + random () * 0.14;
	if (r < 0.25)
		FG_Snd (e, CHAN_VOICE, "dookie/dk_yell1.wav", 1.0, pitch);
	else if (r < 0.50)
		FG_Snd (e, CHAN_VOICE, "dookie/dk_yell2.wav", 1.0, pitch);
	else if (r < 0.75)
		FG_Snd (e, CHAN_VOICE, "dookie/dk_yell3.wav", 1.0, pitch);
	else
		FG_Snd (e, CHAN_VOICE, "dookie/dk_scream.wav", 0.95, pitch);
};

// 16-angle x 8-frame viewer-relative sprite orientation (matches dookie_rig turn_16 convention)
// Frames 0..127:   horizontal (16 angles x 8 waving frames)
// Frames 128..255: above45 (30-60 deg jetpack view, 16 angles x 8 waving frames)
// Frames 256..383: above90 (>60 deg straight-down hover, 16 angles x 8 waving frames)
float() DK_ProjCustomize =
{
	local float rel, d, k, dz, hdist, base;
	local vector delta;

	delta = (other.origin + other.view_ofs) - self.origin;
	dz = delta_z;
	delta_z = 0;
	hdist = vlen (delta);

	if (dz > hdist * 1.73)
	{
		base = 256;
		if (hdist < 16)
			rel = (other.v_angle_y + 180) - self.angles_y;
		else
			rel = vectoyaw (delta) - self.angles_y;
	}
	else if (dz > hdist * 0.58)
	{
		base = 128;
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
	k = floor ((time - self.fg_born) * 16);
	k = k - 8 * floor (k / 8);
	self.frame = base + d * 8 + k;
	return TRUE;
};

void() DK_SplatFXThink =
{
	self.frame = self.frame + 1;
	if (self.frame >= 16)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.05;
};

void(vector org, vector norm) DK_SpawnSplatFX =
{
	local entity fx;

	fx = spawn ();
	fx.classname = "dookie_splat_fx";
	fx.movetype = MOVETYPE_NONE;
	fx.solid = SOLID_NOT;
	setmodel (fx, "progs/dookie_splat.spr32");
	fx.scale = DK_SPLAT_SCALE;
	setorigin (fx, org + norm * 8);
	fx.frame = 0;
	fx.think = DK_SplatFXThink;
	fx.nextthink = time + 0.05;
};

// ---------------------------------------------------------------- poop on the walls (like Milky Grenade)

void() DK_WallSplatRemove =
{
	if (self.dk_splat_qprev)
		self.dk_splat_qprev.dk_splat_qnext = self.dk_splat_qnext;
	else if (dk_splat_qhead == self)
		dk_splat_qhead = self.dk_splat_qnext;
	if (self.dk_splat_qnext)
		self.dk_splat_qnext.dk_splat_qprev = self.dk_splat_qprev;
	else if (dk_splat_qtail == self)
		dk_splat_qtail = self.dk_splat_qprev;
	self.dk_splat_qprev = world;
	self.dk_splat_qnext = world;
	dk_splat_count = dk_splat_count - 1;
	remove (self);
};

void() DK_WallSplatRemoveOldest =
{
	local entity oself;

	if (dk_splat_qhead)
	{
		oself = self;
		self = dk_splat_qhead;
		DK_WallSplatRemove ();
		self = oself;
	}
};

void() DK_WallSplatThink =
{
	local float t, a, k;
	local vector n, side, p;

	t = time - self.dk_splat_born;
	self.nextthink = time + 0.05;
	k = t / 1.2;		// splashes on, then oozes outward
	if (k > 1)
		k = 1;
	k = 1 - (1 - k) * (1 - k);
	k = 0.35 + 0.65 * k;
	self.scale = self.dk_splat_size * k;

	if (t > DK_SPLAT_LIFE)
	{
		a = 1 - (t - DK_SPLAT_LIFE) / DK_SPLAT_FADE;
		if (a <= 0.03)
		{
			DK_WallSplatRemove ();
			return;
		}
		self.alpha = a;
		return;
	}

	// floor splats don't drip downward; once full size, sleep until fade
	n = self.dk_splat_n;
	if (n_z > 0.7)
	{
		if (t > 1.2)
			self.nextthink = self.dk_splat_born + DK_SPLAT_LIFE;
		return;
	}

	if (t > 1.2)
		self.nextthink = max (time + 0.08, min (self.dk_splat_drip, self.dk_splat_born + DK_SPLAT_LIFE));
	if (time < self.dk_splat_drip)
		return;

	if (n_z < -0.7)
		p = self.origin + n * 2 + randomvec () * self.dk_splat_size * 7;
	else
	{
		side_x = 0 - n_y;
		side_y = n_x;
		side_z = 0;
		side = normalize (side);
		p = self.origin + n * 2 + side * crandom () * self.dk_splat_size * 7 - '0 0 1' * self.dk_splat_size * (5 + random () * 5);
	}
	pointparticles (particleeffectnum ("dookie_drip"), p, '0 0 0', 1);
	self.dk_splat_drip = time + 0.18 + random () * 0.65 + t * 0.10;
};

void(vector pos, vector n, float size) DK_WallSplat =
{
	local entity sp;

	if (dk_splat_count >= DK_SPLAT_MAX)
		DK_WallSplatRemoveOldest ();
	sp = spawn ();
	sp.classname = "dookie_wall_splat";
	sp.movetype = MOVETYPE_NONE;
	sp.solid = SOLID_NOT;
	sp.dk_splat_n = n;
	sp.angles = vectoangles (n);		// card's +X faces along surface normal
	if (n_z > 0.7 || n_z < -0.7)
	{
		sp.frame = floor (random () * 3);		// chunky round splats on floors & ceilings
		if (sp.frame > 2)
			sp.frame = 2;
		sp.angles_z = random () * 360;
	}
	else
	{
		sp.frame = 3 + floor (random () * 3);	// dripping vertical runs on walls
		if (sp.frame > 5)
			sp.frame = 5;
	}
	setmodel (sp, "progs/dookie_wall.md3");
	setsize (sp, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (sp, pos + n * (0.5 + random () * 0.6));
	sp.dk_splat_size = size;
	sp.scale = size * 0.35;
	sp.dk_splat_born = time;
	sp.dk_splat_drip = time + 0.14 + random () * 0.40;
	sp.think = DK_WallSplatThink;
	sp.nextthink = time + 0.03;
	sp.dk_splat_qprev = dk_splat_qtail;
	sp.dk_splat_qnext = world;
	if (dk_splat_qtail)
		dk_splat_qtail.dk_splat_qnext = sp;
	else
		dk_splat_qhead = sp;
	dk_splat_qtail = sp;
	dk_splat_count = dk_splat_count + 1;
};

void(vector org, vector to, float size) DK_WallSplatAlong =
{
	traceline (org, to, TRUE, self);
	if (trace_fraction == 1 || trace_startsolid || trace_ent != world)
		return;
	if (pointcontents (trace_endpos - trace_plane_normal * 2) == CONTENT_SKY)
		return;
	DK_WallSplat (trace_endpos, trace_plane_normal, size);
};

void() DK_GlobTouch =
{
	local vector dir;

	if ((self.owner != world && other == self.owner) || other.classname == "dookie_shot" || other.classname == "dookie_glob")
		return;
	dir = normalize (self.velocity);
	if (dir == VEC_ORIGIN)
		dir = '0 0 -1';
	if (other == world)
		DK_WallSplatAlong (self.origin - dir * 16, self.origin + dir * 24, 1.2 + random () * 1.4);
	else
		DK_WallSplatAlong (self.origin, self.origin - '0 0 96', 1.0 + random () * 1.1);
	pointparticles (particleeffectnum ("dookie_drip"), self.origin, '0 0 0', 2);
	remove (self);
};

void(vector org, vector norm, float charge) DK_Splatter =
{
	local float i, ntraces, nglobs, reach;
	local vector dir;
	local entity g;

	reach = DK_SPLAT_RANGE * (0.60 + 0.40 * bound (0, charge, 1));
	ntraces = floor (DK_SPLAT_TRACES * (0.70 + 0.30 * bound (0, charge, 1)));
	nglobs = floor (DK_SPLAT_GLOBS * (0.70 + 0.30 * bound (0, charge, 1)));

	// stamp a central cluster directly around the impacted wall/floor face
	for (i = 0; i < 8; i = i + 1)
	{
		dir = normalize ('0 0 0' - norm + randomvec () * 0.65);
		DK_WallSplatAlong (org, org + dir * 96, 2.5 + random () * 2.2);
	}

	// radial spray coating surrounding walls, floors, and ceilings
	for (i = 0; i < ntraces; i = i + 1)
	{
		dir = randomvec ();
		dir_z = dir_z - 0.15;
		if (dir == VEC_ORIGIN)
			dir = '0 0 -1';
		DK_WallSplatAlong (org, org + normalize (dir) * reach * (0.35 + random () * 0.65), 2.0 + random () * 2.6);
	}

	// arcing physical poop globs that leave brown trails and splat on distant surfaces
	for (i = 0; i < nglobs; i = i + 1)
	{
		g = spawn ();
		g.classname = "dookie_glob";
		g.movetype = MOVETYPE_TOSS;
		g.solid = SOLID_BBOX;
		g.frame = floor (random () * 3);
		if (g.frame > 2)
			g.frame = 2;
		g.scale = 0.60 + random () * 0.65;
		g.angles = randomvec () * 180;
		g.avelocity = randomvec () * 600;
		g.velocity = norm * 240 + randomvec () * 960 + '0 0 400';
		g.traileffectnum = particleeffectnum ("dookie_glob");
		g.touch = DK_GlobTouch;
		g.think = SUB_Remove;
		g.nextthink = time + 4;
		setmodel (g, "progs/dookie_wall.md3");
		setsize (g, VEC_ORIGIN, VEC_ORIGIN);
		setorigin (g, org + norm * 8 + randomvec () * 4);	// start outside the wall (was half inside: "Unstuck entity" spam)
	}
};

// Returns 0..1 launch factor if the shooter hit walkable ground near their feet; 0 otherwise.
float(entity hit, float is_ground) DK_GroundBoltFrac =
{
	local entity p;
	local vector owner_ctr;
	local float dist;

	if (!is_ground)
		return 0;
	if (hit && hit != world && hit.takedamage)
		return 0;
	p = self.owner;
	if (!p || p == world || p.classname != "player" || p.health <= 0 || p.deadflag != 0)
		return 0;
	if (p.jb_vehicle != world || p.rr_vehicle != world || p.veh_van != world || p.mmt_tank != world || p.veh_ride != world || p.fd_head != world)
		return 0;
	if (p.movetype != MOVETYPE_WALK && (p.ishuman == 1 || p.movetype != MOVETYPE_NONE))
		return 0;

	owner_ctr = p.origin + (p.mins + p.maxs) * 0.5;
	dist = vlen (self.origin - owner_ctr);
	if (dist >= DK_BOLT_RADIUS)
		return 0;
	if (!CanDamage (p, self))
		return 0;
	if (dist <= DK_BOLT_FULL_DIST)
		return 1.0;
	return (DK_BOLT_RADIUS - dist) / (DK_BOLT_RADIUS - DK_BOLT_FULL_DIST);
};

// Bolts the shooter straight skyward (~3x a rocket jump) with light RJ-sized self-damage.
void(entity p, float frac) DK_ApplyGroundBolt =
{
	local float vz, pre_vz;
	local vector prev_vel, dxy;

	prev_vel = p.velocity;
	pre_vz = prev_vel_z;

	T_Damage (p, self, self.owner, DK_BOLT_SELF_DMG * frac);

	if (p.health <= 0 || p.deadflag != 0)
		return;

	vz = (DK_BOLT_VZ_BASE + DK_BOLT_VZ_CHARGE * self.dk_charge) * frac;
	if (pre_vz > 0)
		vz = vz + min (pre_vz * 0.25, 120);

	// Keep horizontal momentum mostly intact (tiny outward nudge only) so you bolt straight up.
	dxy = p.origin - self.origin;
	dxy_z = 0;
	if (vlen (dxy) > 4)
		dxy = normalize (dxy) * (60 * frac);
	else
		dxy = '0 0 0';

	p.flags = p.flags - (p.flags & FL_ONGROUND);
	p.jump_flag = 0;
	p.velocity_x = prev_vel_x + dxy_x;
	p.velocity_y = prev_vel_y + dxy_y;
	if (pre_vz > vz)
		p.velocity_z = pre_vz;
	else
		p.velocity_z = vz;

	p.punchangle_x = -8 * frac;
	FG_Snd (p, CHAN_AUTO, "dookie/dk_scream.wav", 0.95, 1.08 + random () * 0.12);
};

void(entity hit, vector norm, float is_ground) DK_Detonate =
{
	local float splash_dmg, bolt_frac;
	local vector blast_org;

	if (self.dk_done)
		return;
	self.dk_done = TRUE;
	self.takedamage = DAMAGE_NO;

	sound (self, CHAN_VOICE, "misc/null.wav", 1, ATTN_NONE);
	sound (self, CHAN_BODY, "misc/null.wav", 1, ATTN_NONE);

	splash_dmg = DK_DAMAGE_BASE + DK_DAMAGE_CHARGE * self.dk_charge;
	bolt_frac = DK_GroundBoltFrac (hit, is_ground);
	fg_inflicting = FG_DOOKIE;
	if (hit && hit != world && hit.takedamage)
	{
		T_Damage (hit, self, self.owner, splash_dmg + DK_DIRECT_BONUS);
		T_RadiusDamage (self, self.owner, splash_dmg, hit);
	}
	else if (bolt_frac > 0)
	{
		// Skip normal self-splash knockback/damage on owner so the sky-bolt handles both cleanly.
		T_RadiusDamage (self, self.owner, splash_dmg, self.owner);
		DK_ApplyGroundBolt (self.owner, bolt_frac);
	}
	else
	{
		T_RadiusDamage (self, self.owner, splash_dmg, world);
	}
	fg_inflicting = 0;

	blast_org = self.origin + norm * 6;
	DK_SpawnSplatFX (self.origin, norm);
	DK_Splatter (blast_org, norm, self.pc_pinata ? 1.35 : self.dk_charge);
	if (self.pc_pinata)
		PC_DookiePinata (self, blast_org, self.pc_killer);
	pointparticles (particleeffectnum ("dookie_boom"), blast_org, '0 0 0', 1);
	FG_Snd (self, CHAN_VOICE, "dookie/dk_splat.wav", 1.0, 0.96 + random () * 0.08);
	FG_Snd (self, CHAN_BODY, "dookie/dk_flies.wav", 0.78, 0.98 + random () * 0.06);

	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_TAREXPLOSION);
	WriteCoord (MSG_BROADCAST, self.origin_x);
	WriteCoord (MSG_BROADCAST, self.origin_y);
	WriteCoord (MSG_BROADCAST, self.origin_z);

	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.touch = SUB_Null;
	setmodel (self, string_null);
	self.think = SUB_Remove;
	self.nextthink = time + 1.6;		// keep entity alive long enough for splat + buzz audio to finish
};

void() DK_ProjDieThink =
{
	DK_Detonate (world, '0 0 1', FALSE);
};

void() DK_ProjDie =
{
	// this runs inside the T_RadiusDamage loop of whatever shot it: blowing up here ran a second findradius, which rewrote
	// .chain under that loop (players skipped or hit twice). Go off a moment later instead, as pickle.qc / megaman.qc do.
	self.pc_pinata = TRUE;
	PC_NoteKilled (self, damage_attacker);
	self.takedamage = DAMAGE_NO;
	self.touch = SUB_Null;
	self.think = DK_ProjDieThink;
	self.nextthink = time;
};

void() DK_ProjTouch =
{
	local vector norm;
	local float is_ground, surf_ok;

	if (other == self.owner)
		return;
	if (other != world && other.pc_kind > PC_KIND_NONE)
	{
		PC_HandlePair (self, other);
		return;
	}
	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		sound (self, CHAN_VOICE, "misc/null.wav", 1, ATTN_NONE);
		sound (self, CHAN_BODY, "misc/null.wav", 1, ATTN_NONE);
		remove (self);
		return;
	}
	surf_ok = (other == world || other.solid == SOLID_BSP || !other.takedamage);
	if (vlen (trace_plane_normal) >= 0.1)
	{
		norm = trace_plane_normal;
		is_ground = (surf_ok && norm_z > 0.55 && self.velocity_z < 0);
	}
	else
	{
		norm = '0 0 1';
		is_ground = (surf_ok && self.velocity_z < -0.5 * vlen (self.velocity));
	}
	DK_Detonate (other, norm, is_ground);
};

void() DK_ProjThink =
{
	if (self.dk_done)
		return;
	if (time - self.fg_born > DK_LIFE)
	{
		DK_Detonate (world, '0 0 1', FALSE);
		return;
	}
	if (self.takedamage == DAMAGE_NO && time >= self.fg_born + 0.18)
		self.takedamage = DAMAGE_YES;
	if (time >= self.dk_yell_t)
	{
		self.dk_yell_t = time + 1.45 + random () * 0.45;
		DK_PlayFlightYell (self);
	}
	self.angles_y = vectoyaw (self.velocity);
	self.nextthink = time + 0.05;
};

void() DK_Press =
{
	if (self.dk_charging > 0)
		return;
	if (time < self.dk_cool)
		return;
	self.dk_charging = time;
	self.dk_msg = 0;
	self.attack_finished = time + 0.08;
	FG_Snd (self, CHAN_WEAPON, "dookie/dk_charge.wav", 1.0, 1.0);
	dprint ("dookie: windup start\n");
};

void(float c) DK_Launch =
{
	local entity p;
	local float a, spd;
	local vector org, dir, eye;

	a = FunGun_Ammo (self, FG_DOOKIE);
	self.dk_charging = 0;
	centerprint (self, "");
	sound (self, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);		// stop windup wobble sound

	if (a < 1)
	{
		self.dk_cool = time + 0.3;
		return;
	}

	c = bound (0.15, c, 1.0);
	self.dk_cool = time + DK_COOLDOWN;
	self.attack_finished = time + DK_COOLDOWN;
	self.fg_fire_t = time;
	TW_TriggerSequence ();
	self.dk_fire_t = time;
	self.bm_lastshot = time + 0.6;
	FunGun_SetAmmo (self, FG_DOOKIE, a - 1);
	FunGun_Lock (FG_DOOKIE);

	spd = DK_SPEED_MIN + (DK_SPEED_MAX - DK_SPEED_MIN) * c;
	makevectors (self.v_angle);
	dir = aim (self, 1000);
	eye = self.origin + self.view_ofs;
	org = eye + v_forward * 8 + v_up * -4;
	traceline (eye, org, TRUE, self);
	if (trace_fraction < 1)
		org = eye + (org - eye) * max (0, trace_fraction - 0.1);

	p = spawn ();
	p.classname = "dookie_shot";
	p.owner = self;
	p.movetype = MOVETYPE_FLYMISSILE;
	p.solid = SOLID_BBOX;
	p.takedamage = DAMAGE_NO;
	p.health = DK_HEALTH;
	p.th_die = DK_ProjDie;
	p.fg_born = time;
	p.dk_charge = c;
	p.dk_done = FALSE;
	p.angles_y = vectoyaw (dir);
	setmodel (p, "progs/dookie_proj.spr32");
	p.scale = DK_SCALE;
	setsize (p, VEC_ORIGIN, VEC_ORIGIN);	// point hull like Rocket Launcher: clears ledges and walls cleanly
	setorigin (p, org);
	p.velocity = dir * spd;
	p.traileffectnum = particleeffectnum ("dookie_glob");
	p.customizeentityforclient = DK_ProjCustomize;
	p.touch = DK_ProjTouch;
	p.think = DK_ProjThink;
	p.nextthink = time + 0.05;
	p.dk_yell_t = time + 1.35;
	PC_Register (p, PC_KIND_DOOKIE, 32);

	FG_Snd (self, CHAN_WEAPON, "dookie/dk_fire.wav", 1.0, 1.0);
	if (random () < 0.30)
		FG_Snd (p, CHAN_BODY, "dookie/dk_dotdot.wav", 0.85, 1.0);
	else
		FG_Snd (p, CHAN_BODY, "dookie/dk_music.wav", 0.85, 1.0);
	DK_PlayFlightYell (p);

	self.punchangle_x = -4.5 - 3.5 * c;
	player_mm1 ();
};

// Called every frame from FunGun_ViewFrame
void() DK_Frame =
{
	local float c, pct;

	if (!self.dk_charging)
		return;
	if (self.health <= 0 || self.deadflag || intermission_running
		|| self.weapon != IT_FUNGUN || self.fg_sel != FG_DOOKIE
		|| FD_Flying (self) || Veh_Driving (self) || JohnBird_Flying (self) || RocketRider_Flying (self)
		|| EricCannon_Active (self) || MMTank_Driving (self))
	{
		sound (self, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
		self.dk_charging = 0;
		centerprint (self, "");
		return;
	}
	c = (time - self.dk_charging) / DK_CHARGE_TIME;
	if (!self.button0 || c >= 1.0)
	{
		DK_Launch (c);
		return;
	}
	self.attack_finished = time + 0.08;
	if (time < self.dk_msg)
		return;
	self.dk_msg = time + 0.25;		// throttle: a reliable centerprint every frame floods remote clients
	pct = floor (c * 100);
	centerprint (self, strcat ("DOOKIE PRESSURE: ", strcat (ftos (pct), "%\n")));
};

void(entity vm, float is_quad) Dookie_ViewFrame =
{
	local entity p;
	local float ammo, u, ease, idx, sw1, sw2, sw3, spd;
	local vector vxy;

	p = vm.owner;
	if (p.weapon != IT_FUNGUN || p.fg_sel != FG_DOOKIE)
	{
		if (vm.dkvm_on)
		{
			if (is_quad)
				vm.skin = 1;
			else
				vm.skin = 0;
			vm.origin = '0 0 0';
			vm.angles = '0 0 0';
			vm.dkvm_on = FALSE;
		}
		return;
	}

	if (is_quad && vm.alpha < 0)
		vm.alpha = 0.5;

	vm.frame = 0;
	vm.origin = '0 0 0';
	vm.angles = '0 0 0';
	ammo = FunGun_Ammo (p, FG_DOOKIE);

	if (!vm.dkvm_on)
	{
		vm.dkvm_on = TRUE;
		if (ammo >= 1 && (!p.dk_fire_t || time >= p.dk_fire_t + DK_FOLLOW_TIME))
		{
			if (!is_quad)
				p.dk_reload_t = time;
		}
		else if (ammo < 1)
			p.dk_empty = TRUE;
	}

	// 1. Overpressure Reactor Windup (skins 60..75)
	if (p.dk_charging > 0)
	{
		p.dk_empty = FALSE;
		u = (time - p.dk_charging) / DK_CHARGE_TIME;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * DK_VM_CHARGE_COUNT);
		vm.skin = DK_VM_CHARGE_SKIN + idx;
		sw1 = sin (time * 36.0);
		sw2 = sin (time * 29.0);
		vm.origin_y = sw1 * (0.20 + 0.35 * u);
		vm.origin_z = sw2 * (0.16 + 0.30 * u);
		return;
	}

	// 2. Blast Fire & Mud Recoil (skins 76..95 over DK_FOLLOW_TIME)
	if (p.dk_fire_t > 0 && time < p.dk_fire_t + DK_FOLLOW_TIME)
	{
		u = (time - p.dk_fire_t) / DK_FOLLOW_TIME;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * DK_VM_FIRE_COUNT);
		vm.skin = DK_VM_FIRE_SKIN + idx;
		ease = sin (u * 3.14159);
		vm.origin_x = -1.6 * ease;
		vm.origin_z = -0.6 * ease;
		if (ammo < 1)
			p.dk_empty = TRUE;
		return;
	}

	// 3. Recharging (keep launcher visible in hand if not hidden by bm_reload)
	if (ammo < 1)
	{
		p.dk_empty = TRUE;
	}
	else if (p.dk_empty)
	{
		p.dk_empty = FALSE;
		p.dk_reload_t = time;
	}

	// 4. Reload / Canister Raise (skins 96..113)
	if (p.dk_reload_t > 0 && time >= p.dk_reload_t && time < p.dk_reload_t + DK_RAISE_TIME)
	{
		u = (time - p.dk_reload_t) / DK_RAISE_TIME;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * DK_VM_RELOAD_COUNT);
		vm.skin = DK_VM_RELOAD_SKIN + idx;
		ease = 1 - u;
		vm.origin_z = -1.5 * ease * ease;
		return;
	}

	// 5. 30 FPS Caged 5-Head Reactor + Flies Idle Loop (skins 0..59 = 2.0s cycle)
	idx = floor (time * 30);
	idx = idx - DK_VM_IDLE_COUNT * floor (idx / DK_VM_IDLE_COUNT);
	vm.skin = DK_VM_IDLE_SKIN + idx;

	vxy = p.velocity;
	vxy_z = 0;
	spd = vlen (vxy) / 320;
	if (spd > 1)
		spd = 1;
	sw1 = sin (time * 2.2);
	sw2 = sin (time * 4.4);
	sw3 = sin (time * 8.0);
	vm.origin_y = 0.14 * sw1 + 0.36 * spd * sw3;
	vm.origin_z = 0.12 * sw2 - 0.30 * spd * fabs (sw3);
	vm.angles_z = 0.25 * sw1 + 0.65 * spd * sw3;
};
