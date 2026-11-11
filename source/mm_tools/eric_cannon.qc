/*
==============================================================================
THE ERIC DEASON CANNON — Implementation (Combat+)

  1. Walk around & inspect the 94u monument (`eric_tripod.md3` + `eric_yoke.md3` +
     `eric_cannon.md3`) as its giant fleshy ears radar-twitch continuously (`idle1..16`).
  2. Walk up within 145u -> `"Press H to man THE ERIC DEASON CANNON"`.
     Press `H` (`impulse 86`) to mount (or press `H` again before firing to dismount).
  3. Aim 360 deg yaw + elevation pitch in 3rd-person over-breech view.
  4. Click `MOUSE1` -> triggers hilarious ~0.86s `wew_cannon`-style rubber skyward bend,
     peristaltic belly bulge, flared muzzle trumpet, starburst + twin supersonic Mach
     shockwave rings AND plays `eric_cannon/canislupusfantasy2.wav` at modest volume!
  5. Launcher tube + strapped Eric Deason head + giant ears blast ~2600u high into the
     sky while the bolted 4-leg tripod + yoke stay anchored on the street (reloading a
     fresh cannon after 10s).
  6. 3rd-person free-orbit chase camera on mouse ("aim in around") while the cannon
     slowly banks & turns toward where you aim + WASD trim (`W` steeper dive,
     `S` cup giant ears wide to float slower, `A/D` bank) with wing-flapping giant ears!
  7. On impact: massive rocket explosion + 340 radius damage + 32 bouncing/clattering
     3D computer parts (whole CRT monitors, beige ATX PC towers, keyboards, mice,
     motherboards, CD-ROMs, floppies, fans, panels, copper yokes, CRT glass & gibs)
     + 2.2s elevated 3rd-person crater watch-cam before kamikaze death/respawn!
==============================================================================
*/

void() EC_BaseThink;

float(float deg) EC_Sin =
{
	local float r, s;
	r = deg * 0.01745329;
	s = sin (r);
	return s;
};

float(float deg) EC_Cos =
{
	local float r, c;
	r = deg * 0.01745329;
	c = cos (r);
	return c;
};

float(float a) EC_NormAng =
{
	while (a > 180)
		a = a - 360;
	while (a < -180)
		a = a + 360;
	return a;
};

float(float to_ang, float from_ang) EC_AngDelta =
{
	return EC_NormAng (to_ang - from_ang);
};

float(float cur, float targ, float step) EC_Approach =
{
	if (cur < targ)
	{
		cur = cur + step;
		if (cur > targ)
			cur = targ;
	}
	else
	{
		cur = cur - step;
		if (cur < targ)
			cur = targ;
	}
	return cur;
};

void() EricCannon_Precache =
{
	if (ec_precached)
		return;
	ec_precached = TRUE;

	precache_model ("progs/eric_tripod.md3");
	precache_model ("progs/eric_yoke.md3");
	precache_model ("progs/eric_cannon.md3");
	precache_model ("progs/spike.mdl");
	precache_model ("progs/s_explod.spr");
	precache_model ("progs/gib1.mdl");
	precache_model ("progs/gib2.mdl");
	precache_model ("progs/gib3.mdl");
	precache_model ("progs/h_player.mdl");

	// Precache all whole CRT monitors, beige ATX PCs, keyboards, mice, motherboards, CDs, floppies & crash sounds
	LanProps_Precache ();

	precache_sound ("eric_cannon/canislupusfantasy2.wav");
	precache_sound ("eric_cannon/mount.wav");
	precache_sound ("eric_cannon/windup.wav");
	precache_sound ("eric_cannon/fire_boom.wav");
	precache_sound ("eric_cannon/ear_flap1.wav");
	precache_sound ("eric_cannon/ear_flap2.wav");
	precache_sound ("eric_cannon/ear_flap3.wav");
	precache_sound ("eric_cannon/ear_flap4.wav");
	precache_sound ("eric_cannon/sky_wind.wav");
	precache_sound ("eric_cannon/doppler_scream.wav");
	precache_sound ("eric_cannon/dive_whistle.wav");

	precache_sound ("weapons/r_exp3.wav");
	precache_sound ("weapons/explodedist.wav");
	precache_sound ("weapons/tink1.wav");
	precache_sound ("items/itembk2.wav");
	precache_sound ("misc/null.wav");

	ec_fx_smoke = particleeffectnum ("TE_GUNSHOT");
	ec_fx_rocket = particleeffectnum ("rocket_explosion");
	ec_fx_rocket_classic = particleeffectnum ("rocket_explo_classic");
};

// TRUE while player is manning, launching, sky-flying, or watching the impact crater (hides viewmodel gun in custom_effects.qc)
float(entity p) EricCannon_Active =
{
	return (p.ec_cannon_ent != world || p.ec_watch_until > time);
};

// ---------------------------------------------------------------- Player Hide / Camera / Restore

void(entity p) EC_HidePlayer =
{
	p.alpha = 0.01;
	p.effects = p.effects | EF_NODRAW;
	p.weaponmodel = "";
	if (!(p.flags & FL_NOTARGET))
	{
		p.flags = p.flags | FL_NOTARGET;
		p.ec_notarget = TRUE;
	}
};

void(entity p) EC_UnhidePlayer =
{
	p.alpha = 0;
	p.effects = p.effects - (p.effects & EF_NODRAW);
	if (p.ec_notarget)
	{
		p.ec_notarget = FALSE;
		if (p.flags & FL_NOTARGET)
			p.flags = p.flags - FL_NOTARGET;
	}
};

void(entity p) EC_RestoreViewAndBody =
{
	local entity oldself;

	if (p.ec_cam != world)
	{
		if (!bm_wasfreed (p.ec_cam) && p.ec_cam.classname == "ec_cam")
			remove (p.ec_cam);
		p.ec_cam = world;
	}
	if (p.ishuman == 1)
	{
		p.clientcamera = p;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, p);
	}
	EC_UnhidePlayer (p);
	if (p.health > 0)
	{
		p.movetype = p.ec_oldmove;
		if (p.movetype == MOVETYPE_NONE || p.movetype == 0)
			p.movetype = MOVETYPE_WALK;
		p.solid = p.ec_oldsolid;
		if (p.solid == SOLID_NOT || p.solid == 0)
			p.solid = SOLID_SLIDEBOX;
		oldself = self;
		self = p;
		W_SetCurrentAmmo ();
		self = oldself;
	}
};

float(entity p, vector pos) EC_SpotClear =
{
	tracebox (pos, VEC_HULL_MIN, VEC_HULL_MAX, pos, FALSE, p);
	if (trace_startsolid || trace_allsolid)
		return FALSE;
	return TRUE;
};

vector(entity base, entity p) EC_FindExitPos =
{
	local vector cand;

	makevectors ('0 1 0' * base.ec_yaw);
	cand = base.origin - v_forward * 74 + '0 0 28';
	if (EC_SpotClear (p, cand))
		return cand;
	cand = base.origin - v_right * 68 + '0 0 28';
	if (EC_SpotClear (p, cand))
		return cand;
	cand = base.origin + v_right * 68 + '0 0 28';
	if (EC_SpotClear (p, cand))
		return cand;
	cand = base.origin + v_forward * 74 + '0 0 28';
	if (EC_SpotClear (p, cand))
		return cand;
	return base.origin + '0 0 98';
};

// Seat the tube back onto the street yoke (on spawn, dismount before firing, or 10s reload)
void(entity base) EC_SeatTubeOnPedestal =
{
	local entity yoke, tube;

	yoke = base.ec_yoke;
	tube = base.ec_tube;
	base.ec_pilot = world;
	base.ec_state = EC_STATE_IDLE;
	base.ec_boomed = FALSE;
	base.ec_screamed = FALSE;

	if (yoke != world)
	{
		setorigin (yoke, base.origin + '0 0 1' * EC_YOKE_Z);
		yoke.angles = '0 1 0' * base.ec_yaw;
	}
	if (tube != world)
	{
		tube.movetype = MOVETYPE_NONE;
		tube.solid = SOLID_NOT;
		tube.velocity = '0 0 0';
		tube.effects = tube.effects - (tube.effects & EF_NODRAW);
		setmodel (tube, "progs/eric_cannon.md3");
		setsize (tube, '0 0 0', '0 0 0');
		setorigin (tube, base.origin + '0 0 1' * EC_CANNON_Z);
		tube.angles_x = base.ec_pitch;
		tube.angles_y = base.ec_yaw;
		tube.angles_z = 0;
		tube.frame = 1;
	}
	base.think = EC_BaseThink;
	base.nextthink = time + 0.08;
};

// Clean dismount while still on pedestal (before firing)
void(entity base) EC_DismountPedestal =
{
	local entity p;
	local vector exit_p;
	local float yaw_out;

	p = base.ec_pilot;
	base.ec_pilot = world;
	if (p != world && p.classname == "player")
	{
		exit_p = EC_FindExitPos (base, p);
		yaw_out = p.v_angle_y;
		p.ec_cannon_ent = world;
		EC_RestoreViewAndBody (p);
		setorigin (p, exit_p);
		p.velocity = '0 0 0';
		p.angles = '0 1 0' * yaw_out;
		p.fixangle = TRUE;
		sound (base, CHAN_ITEM, "eric_cannon/mount.wav", 0.7, ATTN_NORM);
	}
	EC_SeatTubeOnPedestal (base);
};

// Mount player onto an idle Eric Deason Cannon
void(entity p, entity base) EC_Mount =
{
	local entity cam, oldself;

	if (p.health <= 0 || EricCannon_Active (p) || p.veh_van != world || p.jb_vehicle != world || p.fd_head != world)
		return;
	if (base.ec_state != EC_STATE_IDLE || base.ec_pilot != world)
		return;

	if (p.jp_on)
	{
		oldself = self;
		self = p;
		Jetpack_Off ();
		self = oldself;
	}
	if (p.wc_charging)
	{
		p.wc_charging = 0;
		sound (p, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
	}
	p.ltg_phase = 0;
	p.milky_wind = 0;
	p.pk_throw_at = 0;
	p.ns_throw_at = 0;
	p.mb_throw_at = 0;

	base.ec_pilot = p;
	base.ec_state = EC_STATE_MOUNTED;
	base.ec_boomed = FALSE;
	p.ec_cannon_ent = base;
	p.ec_watch_until = 0;
	p.ec_btn = TRUE;				// require fresh click so a held button does not auto-fire
	p.ec_oldmove = p.movetype;
	p.ec_oldsolid = p.solid;

	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.velocity = '0 0 0';
	EC_HidePlayer (p);
	setorigin (p, base.origin + '0 0 46');

	// Align initial player view smoothly with the cannon's current street heading
	p.angles = '0 0 0';
	p.angles_x = 0 - (base.ec_pitch - 12);
	p.angles_y = base.ec_yaw;
	p.v_angle = p.angles;
	p.fixangle = TRUE;

	if (p.ishuman == 1)
	{
		cam = spawn ();
		cam.classname = "ec_cam";
		cam.movetype = MOVETYPE_NONE;
		cam.solid = SOLID_NOT;
		cam.alpha = 0.01;
		cam.scale = 0.01;
		setmodel (cam, "progs/spike.mdl");
		setsize (cam, '0 0 0', '0 0 0');
		setorigin (cam, base.origin + '0 0 92');
		p.ec_cam = cam;

		p.clientcamera = cam;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, cam);
	}

	sound (base, CHAN_ITEM, "eric_cannon/mount.wav", 0.95, ATTN_NORM);
	centerprint (p, "THE ERIC DEASON CANNON\nMouse: Aim 360 | FIRE: Blast Off! | H: Dismount");
};

// ---------------------------------------------------------------- Camera Positioning

vector(vector from_pos, vector to_pos) EC_LookViewAngles =
{
	local vector a;
	local float px;

	a = vectoangles (to_pos - from_pos);
	px = a_x;
	if (px > 180)
		px = px - 360;
	a_x = 0 - px;		// Quake client viewangles: +x looks DOWN, -x looks UP
	a_z = 0;
	return a;
};

void(entity p, vector pivot, vector desired_pos, vector look_angles, float force_view) EC_PlaceCam =
{
	local entity cam;
	local vector pos;

	cam = p.ec_cam;
	if (cam == world)
		return;
	traceline (pivot, desired_pos, TRUE, p);
	pos = trace_endpos;
	if (trace_fraction < 1)
		pos = pos + trace_plane_normal * 8;
	setorigin (cam, pos);
	if (force_view)
	{
		look_angles = EC_LookViewAngles (pos, pivot);
		p.angles = look_angles;
		p.fixangle = TRUE;
	}
	cam.angles = look_angles;
};

// ---------------------------------------------------------------- Computer-Parts & CRT/PC Explosion Fountain

void() EC_PartRemove =
{
	if (ec_debris_count > 0)
		ec_debris_count = ec_debris_count - 1;
	remove (self);
};

void() EC_PartBounceTouch =
{
	local float spd;

	if (other != world)
		return;
	spd = vlen (self.velocity);
	if (spd < 75 || self.cnt >= 3)
		return;
	self.cnt = self.cnt + 1;
	if (self.ec_temp == 1)
		sound (self, CHAN_AUTO, "lan/glass_tink.wav", 0.60, ATTN_NORM);
	else if (self.ec_temp == 2)
		sound (self, CHAN_AUTO, "vehicles/hit_metal1.wav", 0.65, ATTN_NORM);
	else
		sound (self, CHAN_AUTO, "weapons/tink1.wav", 0.55, ATTN_NORM);
};

void(string mdl, vector org, vector vel, float snd_kind, float skin_idx, float life) EC_ThrowComputerPart =
{
	local entity d, e, oldest;

	if (ec_debris_count >= 42)
	{
		oldest = world;
		e = find (world, classname, "ec_debris");
		while (e != world)
		{
			if (oldest == world || e.nextthink < oldest.nextthink)
				oldest = e;
			e = find (e, classname, "ec_debris");
		}
		if (oldest != world)
		{
			remove (oldest);
			ec_debris_count = ec_debris_count - 1;
		}
	}

	d = spawn ();
	d.classname = "ec_debris";
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_NOT;
	d.cnt = 0;
	d.ec_temp = snd_kind;			// 1 = CRT glass/plastic tink, 2 = heavy PC/CRT clang, 0 = circuit/key clatter
	d.skin = skin_idx;
	d.velocity = vel;
	d.avelocity_x = (random () - 0.5) * 680;
	d.avelocity_y = (random () - 0.5) * 680;
	d.avelocity_z = (random () - 0.5) * 680;
	d.angles_x = random () * 360;
	d.angles_y = random () * 360;
	d.touch = EC_PartBounceTouch;
	d.think = EC_PartRemove;
	d.nextthink = time + life + random () * 2.0;
	setmodel (d, mdl);
	setsize (d, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (d, org);
	ec_debris_count = ec_debris_count + 1;
};

void(string mdl, vector org, vector vel) EC_ThrowKamikazeGib =
{
	local entity g;

	g = spawn ();
	g.classname = "gib";
	g.movetype = MOVETYPE_BOUNCE;
	g.solid = SOLID_NOT;
	g.velocity = vel;
	g.avelocity_x = random () * 560;
	g.avelocity_y = random () * 560;
	g.avelocity_z = random () * 560;
	g.think = SUB_Remove;
	g.nextthink = time + 7.0 + random () * 2.5;
	setmodel (g, mdl);
	setsize (g, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (g, org);
};

vector(float hmin, float hmax, float zmin, float zmax) EC_RandBurstVel =
{
	local float ang, hspd;
	local vector v;

	ang = random () * 360;
	hspd = hmin + random () * (hmax - hmin);
	v_x = EC_Cos (ang) * hspd;
	v_y = EC_Sin (ang) * hspd;
	v_z = zmin + random () * (zmax - zmin);
	return v;
};

void(vector boom_org) EC_SpawnComputerExplosion =
{
	local float i;
	local vector org;

	org = boom_org + '0 0 18';

	// 1. 4 Whole Tumbling CRT Monitors (cracked phosphor screens + beige cases!)
	EC_ThrowComputerPart ("progs/bklan/lan_mon1.md3", org + '8 0 6',  EC_RandBurstVel (190, 380, 290, 520), 2, 6, 7.5);
	EC_ThrowComputerPart ("progs/bklan/lan_mon2.md3", org + '-8 6 8', EC_RandBurstVel (190, 380, 290, 520), 2, 0, 7.5);
	EC_ThrowComputerPart ("progs/bklan/lan_mon3.md3", org + '0 -8 8', EC_RandBurstVel (190, 380, 290, 520), 2, 6, 7.5);
	EC_ThrowComputerPart ("progs/bklan/lan_mon4.md3", org + '6 6 10', EC_RandBurstVel (190, 380, 290, 520), 2, 0, 7.5);

	// 2. 4 Whole Tumbling Beige ATX PC Towers!
	EC_ThrowComputerPart ("progs/bklan/lan_pc1.md3", org + '-6 -6 6', EC_RandBurstVel (170, 350, 270, 490), 2, 0, 7.5);
	EC_ThrowComputerPart ("progs/bklan/lan_pc2.md3", org + '6 -6 10', EC_RandBurstVel (170, 350, 270, 490), 2, 0, 7.5);
	EC_ThrowComputerPart ("progs/bklan/lan_pc3.md3", org + '-8 4 12', EC_RandBurstVel (170, 350, 270, 490), 2, 0, 7.5);
	EC_ThrowComputerPart ("progs/bklan/lan_pc4.md3", org + '4 8 12',  EC_RandBurstVel (170, 350, 270, 490), 2, 0, 7.5);

	// 3. Keyboards, Mice, Motherboards, CD-ROMs, Floppies, Fans, Case Panels, Copper Yokes & CRT Glass!
	i = 0;
	while (i < 4)
	{
		EC_ThrowComputerPart ("progs/hd_kbd.md3",   org, EC_RandBurstVel (220, 470, 250, 560), 0, 0, 7.0);
		EC_ThrowComputerPart ("progs/hd_board.md3", org, EC_RandBurstVel (230, 490, 260, 580), 0, 0, 7.0);
		i = i + 1;
	}
	i = 0;
	while (i < 3)
	{
		EC_ThrowComputerPart ("progs/hd_mouse.md3",          org, EC_RandBurstVel (250, 520, 240, 540), 0, 0, 6.5);
		EC_ThrowComputerPart ("progs/hd_cd.md3",             org, EC_RandBurstVel (280, 590, 280, 620), 1, 0, 6.5);
		EC_ThrowComputerPart ("progs/hd_floppy.md3",         org, EC_RandBurstVel (260, 550, 260, 580), 0, 0, 6.5);
		EC_ThrowComputerPart ("progs/bklan/lan_deb_glass.md3", org, EC_RandBurstVel (270, 560, 250, 570), 1, 0, 6.0);
		i = i + 1;
	}
	i = 0;
	while (i < 2)
	{
		EC_ThrowComputerPart ("progs/bklan/lan_deb_panel.md3", org, EC_RandBurstVel (210, 430, 260, 530), 2, 0, 7.0);
		EC_ThrowComputerPart ("progs/bklan/lan_deb_fan.md3",   org, EC_RandBurstVel (260, 540, 280, 590), 0, 0, 6.5);
		EC_ThrowComputerPart ("progs/bklan/lan_deb_yoke.md3",  org, EC_RandBurstVel (230, 470, 260, 550), 2, 0, 6.8);
		i = i + 1;
	}

	// 4. Kamikaze Rider Gibs flying out with the computer hardware!
	EC_ThrowKamikazeGib ("progs/h_player.mdl", org + '0 0 12', EC_RandBurstVel (180, 360, 320, 540));
	EC_ThrowKamikazeGib ("progs/gib1.mdl",     org + '0 0 8',  EC_RandBurstVel (220, 460, 280, 520));
	EC_ThrowKamikazeGib ("progs/gib2.mdl",     org + '0 0 8',  EC_RandBurstVel (220, 460, 280, 520));
	EC_ThrowKamikazeGib ("progs/gib3.mdl",     org + '0 0 8',  EC_RandBurstVel (220, 460, 280, 520));
};

// Spawn classic Quake rocket explosion sprite + rocket_explosion particles + sounds
void(vector boom_org, entity pilot, entity base) EC_Detonate =
{
	local entity exp_ent, inf_ent, oldself;
	local vector cam_des, back_dir, look_ang;

	// Stop looping wind/dive channels on tube
	if (base.ec_tube != world)
	{
		sound (base.ec_tube, CHAN_ITEM, "misc/null.wav", 1, ATTN_NORM);
		sound (base.ec_tube, CHAN_BODY, "misc/null.wav", 1, ATTN_NORM);
		base.ec_tube.effects = base.ec_tube.effects | EF_NODRAW;
		base.ec_tube.solid = SOLID_NOT;
		base.ec_tube.velocity = '0 0 0';
	}

	// 1. Stock Quake Rocket Explosion (`TE_EXPLOSION` + `rocket_explosion` particles + `BecomeExplosion` + `r_exp3.wav`)
	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, boom_org_x);
	WriteCoord (MSG_BROADCAST, boom_org_y);
	WriteCoord (MSG_BROADCAST, boom_org_z + 12);

	if (autocvar_effects_classic_explosion == 1)
	{
		if (ec_fx_rocket_classic > 0)
			pointparticles (ec_fx_rocket_classic, boom_org + '0 0 12', VEC_ORIGIN, 1);
	}
	else
	{
		if (ec_fx_rocket > 0)
			pointparticles (ec_fx_rocket, boom_org + '0 0 12', VEC_ORIGIN, 1);
	}
	// Phosphor & spark burst
	particle (boom_org + '0 0 22', '0 0 65', 244, 64);
	particle (boom_org + '0 0 18', '0 0 45', 104, 64);

	exp_ent = spawn ();
	exp_ent.classname = "eric_cannon_exp";
	exp_ent.movetype = MOVETYPE_NONE;
	exp_ent.solid = SOLID_NOT;
	setorigin (exp_ent, boom_org + '0 0 16');
	sound (exp_ent, CHAN_WEAPON, "weapons/r_exp3.wav", 1.0, 0.35);
	sound (exp_ent, CHAN_AUTO,   "weapons/explodedist.wav", 0.75, 0.25);
	sound (exp_ent, CHAN_VOICE,  "lan/crt_implode.wav", 1.0, 0.45);
	sound (exp_ent, CHAN_ITEM,   "lan/pc_boom.wav", 1.0, 0.45);
	oldself = self;
	self = exp_ent;
	BecomeExplosion ();
	self = oldself;

	// 2. Massive Computer-Parts + CRT Monitor + Beige ATX PC Fountain!
	EC_SpawnComputerExplosion (boom_org);

	// 3. Nuke-tier 340 Radius Damage to nearby enemies, monsters, LAN props & vehicles (credited to pilot!)
	inf_ent = spawn ();
	inf_ent.classname = "eric_cannon_blast";
	setorigin (inf_ent, boom_org + '0 0 20');
	ec_inflicting = 2;
	if (pilot != world && pilot.classname == "player")
		T_RadiusDamage (inf_ent, pilot, 340, pilot);
	else
		T_RadiusDamage (inf_ent, inf_ent, 340, world);
	ec_inflicting = 0;
	remove (inf_ent);

	// 4. Transition street tripod to 10s reload & transition pilot to 2.2s elevated 3rd-person crater watch-cam!
	base.ec_pilot = world;
	base.ec_state = EC_STATE_RELOAD;
	base.think = EC_BaseThink;
	base.nextthink = time + EC_RELOAD_TIME;

	if (pilot != world && pilot.classname == "player")
	{
		pilot.ec_cannon_ent = world;
		pilot.ec_boomat = boom_org + '0 0 16';
		pilot.ec_watch_until = time + EC_WATCH_TIME;
		setorigin (pilot, boom_org + '0 0 28');
		pilot.velocity = '0 0 0';

		if (pilot.ec_cam != world)
		{
			makevectors ('0 1 0' * pilot.v_angle_y);
			back_dir = '0 0 0' - v_forward;
			cam_des = boom_org + back_dir * 195 + '0 0 112';
			look_ang = EC_LookViewAngles (cam_des, boom_org + '0 0 18');
			EC_PlaceCam (pilot, boom_org + '0 0 18', cam_des, look_ang, TRUE);
		}
	}
};

// ---------------------------------------------------------------- Sky-Ceiling Check & Airborne Step

float(vector pt) EC_PointNearSky =
{
	local float sn;
	local string tex;

	if (pointcontents (pt) == CONTENT_SKY)
		return TRUE;
	sn = getsurfacenearpoint (world, pt);
	if (sn >= 0)
	{
		tex = getsurfacetexture (world, sn);
		if (tex == "sky1" || tex == "sky4" || substring (tex, 0, 3) == "sky")
			return TRUE;
	}
	return FALSE;
};

// Moves airborne `tube` for `dt`, cushioning below `CONTENT_SKY` and returning TRUE if an impact should detonate!
float(entity tube, entity pilot, float dt, float flight_age) EC_StepFlight =
{
	local vector start, dest, nrm;
	local float headon, hit_sky;

	start = tube.origin;

	// Soft sky-ceiling guard: never vanish into CONTENT_SKY! Cushion 96u underneath skybox roof.
	if (tube.velocity_z > 0)
	{
		traceline (start, start + '0 0 110', TRUE, tube);
		if (trace_fraction < 1 && EC_PointNearSky (trace_endpos))
			tube.velocity_z = -25;
		else if (pointcontents (start + '0 0 85') == CONTENT_SKY)
			tube.velocity_z = -35;
	}

	dest = start + tube.velocity * dt;
	tracebox (start, '-16 -16 -12', '16 16 16', dest, FALSE, tube);

	if (trace_startsolid || trace_allsolid)
	{
		if (flight_age < 0.45)
		{
			setorigin (tube, start + '0 0 10');
			return FALSE;
		}
		tube.ec_hitnorm = '0 0 1';
		return TRUE;
	}

	if (trace_fraction >= 1)
	{
		if (pointcontents (dest) == CONTENT_SKY)
		{
			tube.velocity_z = -45;
			return FALSE;
		}
		setorigin (tube, dest);
		return FALSE;
	}

	// Hit something! First check if we brushed a sky surface — slide along sky instead of deleting or premature boom
	hit_sky = EC_PointNearSky (trace_endpos);
	setorigin (tube, trace_endpos + trace_plane_normal * 2);
	nrm = trace_plane_normal;
	tube.ec_hitnorm = nrm;

	if (hit_sky)
	{
		if (tube.velocity * nrm < 0)
			tube.velocity = tube.velocity - nrm * (tube.velocity * nrm);
		if (tube.velocity_z > -20)
			tube.velocity_z = -35;
		return FALSE;
	}

	// Direct hit on living enemy/monster/vehicle/prop after 0.20s -> BOOM!
	if (trace_ent != world && trace_ent != pilot && trace_ent != tube.ec_base && flight_age > 0.20)
	{
		if (trace_ent.takedamage)
			return TRUE;
	}

	// During initial 0.45s liftoff climb, slide past tight nearby walls/roof overhangs without wasting the launch
	if (flight_age < 0.45)
	{
		if (tube.velocity * nrm < 0)
			tube.velocity = tube.velocity - nrm * (tube.velocity * nrm);
		return FALSE;
	}

	// Landing on any floor/ground/rooftop (`nrm_z > 0.35`) or solid impact while descending -> BOOM!
	if (nrm_z > 0.35 && (tube.velocity_z <= 80 || flight_age > 0.90))
		return TRUE;

	// Head-on wall/building impact after 0.75s -> BOOM! Glancing wall graze slides along building facade!
	headon = 0 - (normalize (tube.velocity) * nrm);
	if (flight_age > 0.75 && headon > 0.52)
		return TRUE;

	// Glancing graze: slide velocity along wall plane
	if (tube.velocity * nrm < 0)
		tube.velocity = tube.velocity - nrm * (tube.velocity * nrm);
	return FALSE;
};

// ---------------------------------------------------------------- Per-Frame Player Control (`EricCannon_Frame`)

void(entity tube, float vol) EC_PlayEarFlap =
{
	local float r;
	r = random () * 4;
	if (r < 1)
		sound (tube, CHAN_AUTO, "eric_cannon/ear_flap1.wav", vol, ATTN_NORM);
	else if (r < 2)
		sound (tube, CHAN_AUTO, "eric_cannon/ear_flap2.wav", vol, ATTN_NORM);
	else if (r < 3)
		sound (tube, CHAN_AUTO, "eric_cannon/ear_flap3.wav", vol, ATTN_NORM);
	else
		sound (tube, CHAN_AUTO, "eric_cannon/ear_flap4.wav", vol, ATTN_NORM);
};

float() EricCannon_Frame =
{
	local entity base, yoke, tube, inf;
	local float dt, el, idx, fwd_in, str_in, yaw_err, max_turn, turn_step, roll_t, hspd_t, sink_t, cur_h, k;
	local vector pivot, cam_des, look_ang, fwd_v, rgt_v, vel_xy, dir_ang;

	// 1. Post-impact 3rd-person crater watch-cam (`ec_watch_until`)
	if (self.ec_cannon_ent == world)
	{
		if (self.ec_watch_until <= 0)
			return FALSE;

		if (time < self.ec_watch_until && self.health > 0)
		{
			EC_HidePlayer (self);
			self.velocity = '0 0 0';
			self.impulse = 0;
			if (self.ec_cam != world)
			{
				// Elevated 3rd-person view pointed right at the smoking crater & bouncing CRT monitors!
				makevectors ('0 1 0' * self.v_angle_y);
				cam_des = self.ec_boomat - v_forward * 195 + '0 0 112';
				look_ang = EC_LookViewAngles (cam_des, self.ec_boomat);
				EC_PlaceCam (self, self.ec_boomat, cam_des, look_ang, TRUE);
			}
			return TRUE;
		}

		// Watch-cam finished -> restore camera & execute kamikaze blast death on rider!
		self.ec_watch_until = 0;
		EC_RestoreViewAndBody (self);
		setorigin (self, self.ec_boomat + '0 0 12');
		if (self.health > 0 && !(self.flags & FL_GODMODE))
		{
			self.bm_prot_t = 0;
			self.invincible_finished = 0;
			inf = spawn ();
			inf.classname = "eric_cannon_blast";
			setorigin (inf, self.origin);
			ec_inflicting = 1;
			T_Damage (self, inf, self, 50000);
			ec_inflicting = 0;
			remove (inf);
		}
		return FALSE;
	}

	base = self.ec_cannon_ent;
	if (bm_wasfreed (base) || base.classname != "misc_eric_cannon" || base.ec_pilot != self || self.health <= 0)
	{
		self.ec_cannon_ent = world;
		EC_RestoreViewAndBody (self);
		return FALSE;
	}

	dt = frametime;
	if (dt < 0.001)
		dt = 0.001;
	if (dt > 0.05)
		dt = 0.05;

	EC_HidePlayer (self);
	self.velocity = '0 0 0';
	self.flags = self.flags - (self.flags & FL_ONGROUND);
	if (!self.button0)
		self.ec_btn = FALSE;

	yoke = base.ec_yoke;
	tube = base.ec_tube;

	// =========================================================================
	// STATE 1: MOUNTED ON PEDESTAL — 360 Aiming & Dismount (`H`) or Shoot (`MOUSE1`)
	// =========================================================================
	if (base.ec_state == EC_STATE_MOUNTED)
	{
		if (self.impulse == 86)
		{
			self.impulse = 0;
			EC_DismountPedestal (base);
			return TRUE;
		}
		self.impulse = 0;

		base.ec_yaw = self.v_angle_y;
		base.ec_pitch = bound (-6, (0 - self.v_angle_x) + 12, 62);

		if (yoke != world)
			yoke.angles = '0 1 0' * base.ec_yaw;
		if (tube != world)
		{
			tube.angles_x = base.ec_pitch;
			tube.angles_y = base.ec_yaw;
			tube.angles_z = 0;
			base.ec_anim_clock = base.ec_anim_clock + dt * 14.0;
			idx = floor (base.ec_anim_clock);
			idx = idx - 16 * floor (idx / 16);
			tube.frame = 1 + idx;
		}

		// Over-breech 3rd-person aiming camera
		makevectors (self.v_angle);
		pivot = base.origin + '0 0 76';
		cam_des = pivot - v_forward * 142 + v_right * 20 + '0 0 24';
		EC_PlaceCam (self, pivot, cam_des, self.v_angle, FALSE);

		// Click FIRE (`MOUSE1`) -> Start hilarious Wew-Cannon wind-up & play modest-volume canislupusfantasy2.wav!
		if (self.button0 && !self.ec_btn)
		{
			self.ec_btn = TRUE;
			base.ec_state = EC_STATE_WINDUP;
			base.ec_phase_t = time;
			base.ec_boomed = FALSE;

			if (tube != world)
				sound (tube, CHAN_WEAPON, "eric_cannon/windup.wav", 0.90, ATTN_NORM);
			// Modest-volume canislupusfantasy2.wav on both rider channel 5 (follows rider into sky) & street pedestal!
			sound (self, 5, "eric_cannon/canislupusfantasy2.wav", 0.40, ATTN_NORM);
			sound (base, CHAN_AUTO, "eric_cannon/canislupusfantasy2.wav", 0.36, ATTN_NORM);
			centerprint (self, "WINDING UP THE ERIC DEASON CANNON!!");
		}
		return TRUE;
	}

	// =========================================================================
	// STATE 2: FUNNY WEW-CANNON WIND-UP, BELLY BULGE & SUPERSONIC BLAST (~0.86s)
	// =========================================================================
	if (base.ec_state == EC_STATE_WINDUP)
	{
		self.impulse = 0;
		el = time - base.ec_phase_t;

		if (el < 0.58)
		{
			// Frames 17..25 (`windup1..9`): +38.5 deg rubber skyward bend + pinned ears + surging belly bulge!
			idx = floor ((el / 0.58) * 9);
			if (idx > 8)
				idx = 8;
			if (tube != world)
				tube.frame = 17 + idx;
		}
		else if (el < 0.86)
		{
			if (!base.ec_boomed)
			{
				base.ec_boomed = TRUE;
				sound (base, CHAN_VOICE, "eric_cannon/fire_boom.wav", 1.0, 0.35);
				sound (base, CHAN_ITEM,  "weapons/r_exp3.wav", 0.70, 0.45);
				if (ec_fx_smoke > 0)
					pointparticles (ec_fx_smoke, base.origin + '0 0 68', '0 0 40', 4);
			}
			// Frames 26..29 (`blast1..4`): flared muzzle bell + snapped giant ears + starburst + twin Mach shockrings!
			idx = floor (((el - 0.58) / 0.28) * 4);
			if (idx > 3)
				idx = 3;
			if (tube != world)
				tube.frame = 26 + idx;
		}
		else
		{
			// LIFTOFF! Launcher tube + strapped Eric head + giant ears blast sky-high while tripod & yoke stay on street!
			base.ec_state = EC_STATE_FLYING;
			base.ec_phase_t = time;
			base.ec_screamed = FALSE;
			if (tube != world)
			{
				tube.ec_fly_yaw = base.ec_yaw;
				tube.ec_prev_yaw = base.ec_yaw;
				tube.ec_wind_snd_t = time + 0.25;
				tube.ec_flap_snd_t = time + 0.35;
				tube.ec_dive_snd_t = 0;
				tube.ec_smoke_t = time;
				tube.ec_anim_clock = 0;
				tube.frame = 30;			// liftoff1

				makevectors ('0 1 0' * base.ec_yaw);
				tube.velocity = v_forward * (650 + EC_Cos (base.ec_pitch) * 120);
				tube.velocity_z = 1210 + EC_Sin (bound (15, base.ec_pitch, 62)) * 180;
				setorigin (tube, base.origin + '0 0 74');
			}
			// Snap chase camera cleanly behind the ascending cannon once at liftoff; free mouse orbit from next frame on!
			self.angles = '0 0 0';
			self.angles_x = 8;
			self.angles_y = base.ec_yaw;
			self.v_angle = self.angles;
			self.fixangle = TRUE;
			centerprint (self, "SKY-HIGH! Mouse: Look & Aim | WASD: Steer / Dive (W) / Ear-Float (S)");
			return TRUE;
		}

		// Dramatic 3/4 side-angle launch camera during wind-up so you see the full rubber bend, bulge & shockrings!
		makevectors ('0 1 0' * base.ec_yaw);
		pivot = base.origin + v_forward * 10 + '0 0 68';
		cam_des = base.origin - v_forward * 135 - v_right * 115 + '0 0 84';
		look_ang = EC_LookViewAngles (cam_des, pivot);
		EC_PlaceCam (self, pivot, cam_des, look_ang, TRUE);
		return TRUE;
	}

	// =========================================================================
	// STATE 3: SKY-HIGH 3RD-PERSON GUIDED FLIGHT & EAR-GLIDING DESCENT
	// =========================================================================
	if (base.ec_state == EC_STATE_FLYING && tube != world)
	{
		self.impulse = 0;
		el = time - base.ec_phase_t;
		fwd_in = bound (-1, self.movement_x / 160, 1);
		str_in = bound (-1, self.movement_y / 160, 1);

		// Slow guided yaw steering toward player's mouse look (`~62 deg/s`) + A/D trim (`~38 deg/s`)
		yaw_err = EC_AngDelta (self.v_angle_y, tube.ec_fly_yaw);
		max_turn = 62.0 * dt;
		turn_step = bound (0 - max_turn, yaw_err * bound (0, dt * 3.2, 1), max_turn) + (0 - str_in) * 38.0 * dt;
		tube.ec_fly_yaw = EC_NormAng (tube.ec_fly_yaw + turn_step);

		makevectors ('0 1 0' * tube.ec_fly_yaw);
		fwd_v = v_forward;
		rgt_v = v_right;

		// Horizontal speed control: enough range (~8500u) to fly all the way between Fox Theater & Padre Hotel!
		if (fwd_in > 0.2)
			hspd_t = 930;
		else if (fwd_in < -0.2)
			hspd_t = 320;
		else
			hspd_t = 760;

		vel_xy = tube.velocity;
		vel_xy_z = 0;
		cur_h = vlen (vel_xy);
		cur_h = cur_h + (hspd_t - cur_h) * bound (0, dt * 2.8, 1);
		vel_xy = fwd_v * cur_h + rgt_v * (str_in * 145);
		tube.velocity_x = vel_xy_x;
		tube.velocity_y = vel_xy_y;

		// Vertical sky-arc physics:
		//   - First 3.1s climb (`velocity_z > 0`): low rocket-assisted gravity (`365 u/s^2`) -> soars ~2450-2650u sky-high!
		//   - Apex & descent: controlled slow descent (`-285 u/s` neutral wing-glide, `-155 u/s` S-key ear-flare, `-880 u/s` W-key dive!)
		if (tube.velocity_z > 0 && el < 3.4)
		{
			tube.velocity_z = tube.velocity_z - 365 * dt;
			if (fwd_in > 0.35 && el > 1.0)
				tube.velocity_z = tube.velocity_z - 520 * dt;		// W lets pilot nose over early if desired!
		}
		else
		{
			if (!base.ec_screamed && el > 1.2)
			{
				base.ec_screamed = TRUE;
				sound (tube, CHAN_VOICE, "eric_cannon/doppler_scream.wav", 0.68, 0.45);
			}
			if (fwd_in > 0.2 || self.v_angle_x > 46)
				sink_t = -880;
			else if (fwd_in < -0.2)
				sink_t = -155;
			else
				sink_t = -285;

			k = bound (0, dt * 2.6, 1);
			tube.velocity_z = tube.velocity_z + (sink_t - tube.velocity_z) * k;
		}

		// Step airborne collision & check impact
		if (EC_StepFlight (tube, self, dt, el) || el > 24.0)
		{
			EC_Detonate (tube.origin, self, base);
			return TRUE;
		}

		// Smooth 3D pitch, yaw & banked roll
		roll_t = bound (-34, (0 - (turn_step / dt) * 0.36) + str_in * 18, 34);
		dir_ang = vectoangles (tube.velocity);
		tube.angles_x = tube.angles_x + (bound (-78, dir_ang_x, 76) - tube.angles_x) * bound (0, dt * 8.0, 1);
		tube.angles_y = tube.ec_fly_yaw;
		tube.angles_z = tube.angles_z + (roll_t - tube.angles_z) * bound (0, dt * 7.5, 1);

		// Animation & Flight Audio selection:
		//   - `liftoff1..3` (30..32) for first 0.22s
		//   - `boost1..12`  (33..44) while climbing (`velocity_z > 140`)
		//   - `dive1..8`    (61..68) when diving (`W` or `velocity_z < -480`)
		//   - `flare1..8`   (69..76) when cupping giant ears wide (`S`)
		//   - `glide1..16`  (45..60) rhythmic wing-flapping giant ears during sky glide!
		if (el < 0.22)
		{
			idx = floor ((el / 0.22) * 3);
			if (idx > 2)
				idx = 2;
			tube.frame = 30 + idx;
		}
		else if (tube.velocity_z > 140)
		{
			tube.ec_anim_clock = tube.ec_anim_clock + dt * 18.0;
			idx = floor (tube.ec_anim_clock);
			idx = idx - 12 * floor (idx / 12);
			tube.frame = 33 + idx;
			if (ec_fx_smoke > 0 && time >= tube.ec_smoke_t)
			{
				tube.ec_smoke_t = time + 0.06;
				pointparticles (ec_fx_smoke, tube.origin - fwd_v * 68, '0 0 -40', 1);
			}
		}
		else if (fwd_in > 0.2 || tube.velocity_z < -480)
		{
			tube.ec_anim_clock = tube.ec_anim_clock + dt * 16.0;
			idx = floor (tube.ec_anim_clock);
			idx = idx - 8 * floor (idx / 8);
			tube.frame = 61 + idx;
			if (time >= tube.ec_dive_snd_t)
			{
				tube.ec_dive_snd_t = time + 2.4;
				sound (tube, CHAN_BODY, "eric_cannon/dive_whistle.wav", 0.62, ATTN_NORM);
			}
		}
		else if (fwd_in < -0.2)
		{
			tube.ec_anim_clock = tube.ec_anim_clock + dt * 12.0;
			idx = floor (tube.ec_anim_clock);
			idx = idx - 8 * floor (idx / 8);
			tube.frame = 69 + idx;
			if (time >= tube.ec_flap_snd_t)
			{
				tube.ec_flap_snd_t = time + 0.42;
				EC_PlayEarFlap (tube, 0.72);
			}
		}
		else
		{
			tube.ec_anim_clock = tube.ec_anim_clock + dt * 14.5;
			idx = floor (tube.ec_anim_clock);
			idx = idx - 16 * floor (idx / 16);
			tube.frame = 45 + idx;
			if (time >= tube.ec_flap_snd_t)
			{
				tube.ec_flap_snd_t = time + 0.34;
				EC_PlayEarFlap (tube, 0.80);
			}
		}

		if (time >= tube.ec_wind_snd_t)
		{
			tube.ec_wind_snd_t = time + 2.45;
			sound (tube, CHAN_ITEM, "eric_cannon/sky_wind.wav", 0.48, ATTN_NORM);
		}

		// Sync hidden pilot inside flying cannon for PVS + spatial audio + channel-5 canislupusfantasy2.wav!
		setorigin (self, tube.origin);

		// Free-orbit 3rd-person chase camera controlled by mouse (`v_angle`)
		makevectors (self.v_angle);
		pivot = tube.origin + '0 0 14';
		cam_des = pivot - v_forward * 168 + '0 0 38';
		EC_PlaceCam (self, pivot, cam_des, self.v_angle, FALSE);
		return TRUE;
	}

	return FALSE;
};

// ---------------------------------------------------------------- Street Pedestal Idle & Reload Think

void() EC_BaseThink =
{
	local entity p, tube;
	local float idx;

	if (self.ec_state == EC_STATE_RELOAD)
	{
		self.ec_pitch = EC_REST_PITCH;
		EC_SeatTubeOnPedestal (self);
		sound (self, CHAN_ITEM, "items/itembk2.wav", 0.9, ATTN_NORM);
		return;
	}

	p = self.ec_pilot;
	if (p != world)
	{
		// Safety watchdog if rider died externally or disconnected
		if (p.classname != "player" || p.health <= 0 || p.ec_cannon_ent != self)
		{
			if (self.ec_state == EC_STATE_MOUNTED)
				EC_SeatTubeOnPedestal (self);
			else
			{
				self.ec_pilot = world;
				self.ec_state = EC_STATE_RELOAD;
				self.nextthink = time + EC_RELOAD_TIME;
				if (self.ec_tube != world)
					self.ec_tube.effects = self.ec_tube.effects | EF_NODRAW;
				return;
			}
		}
		self.nextthink = time + 0.1;
		return;
	}

	// Idle monument: continuously animate radar-twitching giant ears (`idle1..16`, frames 1..16)!
	tube = self.ec_tube;
	if (tube != world && self.ec_state == EC_STATE_IDLE)
	{
		idx = floor (time * 10.5);
		idx = idx - 16 * floor (idx / 16);
		tube.frame = 1 + idx;
	}
	self.nextthink = time + 0.08;
};

// ---------------------------------------------------------------- Spawn, Proximity Prompt, H-Key & Impulses

void(entity base) EC_FreeParts =
{
	if (base.ec_yoke != world)
	{
		remove (base.ec_yoke);
		base.ec_yoke = world;
	}
	if (base.ec_tube != world)
	{
		remove (base.ec_tube);
		base.ec_tube = world;
	}
};

void(entity base, float is_temp) EC_InitMonument =
{
	local entity yoke, tube;

	EricCannon_Precache ();
	ec_has_cannons = TRUE;

	// Snap cleanly onto floor/street below spawn point
	traceline (base.origin + '0 0 28', base.origin - '0 0 192', TRUE, base);
	if (trace_fraction < 1 && !trace_startsolid)
		base.origin_z = trace_endpos_z;

	base.classname = "misc_eric_cannon";
	base.netname = "THE ERIC DEASON CANNON";
	base.ec_temp = is_temp;
	base.ec_yaw = base.angles_y;
	base.ec_pitch = EC_REST_PITCH;
	base.angles = '0 1 0' * base.ec_yaw;
	base.movetype = MOVETYPE_NONE;
	base.solid = SOLID_BBOX;
	base.takedamage = DAMAGE_NO;
	setmodel (base, "progs/eric_tripod.md3");
	setsize (base, '-26 -26 0', '26 26 88');
	setorigin (base, base.origin);

	yoke = spawn ();
	yoke.classname = "ec_yoke";
	yoke.ec_base = base;
	yoke.movetype = MOVETYPE_NONE;
	yoke.solid = SOLID_NOT;
	setmodel (yoke, "progs/eric_yoke.md3");
	setsize (yoke, '0 0 0', '0 0 0');
	base.ec_yoke = yoke;

	tube = spawn ();
	tube.classname = "ec_tube";
	tube.ec_base = base;
	tube.movetype = MOVETYPE_NONE;
	tube.solid = SOLID_NOT;
	setmodel (tube, "progs/eric_cannon.md3");
	setsize (tube, '0 0 0', '0 0 0');
	base.ec_tube = tube;

	EC_SeatTubeOnPedestal (base);
};

// Map entity: misc_eric_cannon
void() misc_eric_cannon =
{
	EC_InitMonument (self, FALSE);
};

entity(entity p) EricCannon_NearIdle =
{
	local entity e, best;
	local float d, bd;

	if (!ec_has_cannons)
		return world;
	best = world;
	bd = 148;
	e = find (world, classname, "misc_eric_cannon");
	while (e != world)
	{
		if (e.ec_state == EC_STATE_IDLE && e.ec_pilot == world)
		{
			d = vlen ((e.origin + '0 0 36') - (p.origin + '0 0 22'));
			if (d < bd)
			{
				bd = d;
				best = e;
			}
		}
		e = find (e, classname, "misc_eric_cannon");
	}
	return best;
};

void() EricCannon_NearPrompt =
{
	local entity c;

	if (!ec_has_cannons || self.ishuman != 1 || self.health <= 0 || EricCannon_Active (self) || self.veh_van != world || self.jb_vehicle != world || self.classname != "player")
		return;
	if (time < self.ec_prompt_scan_t)
		return;
	self.ec_prompt_scan_t = time + 0.12;

	c = EricCannon_NearIdle (self);
	if (c == world)
	{
		if (time > self.ec_prompt_t)
			self.ec_prompt_ent = world;
		return;
	}
	if (self.ec_prompt_ent == c && time < self.ec_prompt_t)
		return;
	self.ec_prompt_ent = c;
	self.ec_prompt_t = time + 6.0;
	centerprint (self, "Press H to man THE ERIC DEASON CANNON");
};

// Called on H (impulse 86) on foot: mounts nearest Eric Deason Cannon if closer than any van/Winged John!
float() EricCannon_TryEnterKey =
{
	local entity c, jb, van;
	local float dc;

	if (self.health <= 0 || EricCannon_Active (self) || self.veh_van != world || self.jb_vehicle != world)
		return FALSE;
	c = EricCannon_NearIdle (self);
	if (c == world)
		return FALSE;

	dc = vlen (c.origin - self.origin);
	jb = JohnBird_NearPerched (self);
	if (jb != world && vlen (jb.origin - self.origin) < dc)
		return FALSE;
	van = Veh_SeatOf (self);
	if (van != world && vlen (van.origin - self.origin) < dc)
		return FALSE;

	EC_Mount (self, c);
	return TRUE;
};

entity(entity p) EC_MyTemp =
{
	local entity e;
	e = p.ec_my_temp;
	if (e != world && (bm_wasfreed (e) || e.classname != "misc_eric_cannon" || !e.ec_temp || e.ec_summoner != p))
	{
		p.ec_my_temp = world;
		e = world;
	}
	return e;
};

// Reset on respawn (`PutClientInServer`)
void(entity p) EricCannon_Reset =
{
	local entity base;

	sound (p, 5, "misc/null.wav", 1, ATTN_NORM);
	base = p.ec_cannon_ent;
	if (base != world && !bm_wasfreed (base) && base.classname == "misc_eric_cannon" && base.ec_pilot == p)
		EC_SeatTubeOnPedestal (base);
	p.ec_cannon_ent = world;
	p.ec_watch_until = 0;
	p.ec_btn = FALSE;
	if (p.ec_cam != world)
		EC_RestoreViewAndBody (p);
	else
		EC_UnhidePlayer (p);
};

// Clean up when a player disconnects
void() EricCannon_ClientGone =
{
	local entity tmp;

	EricCannon_Reset (self);
	tmp = EC_MyTemp (self);
	if (tmp != world && tmp.ec_pilot == world)
	{
		EC_FreeParts (tmp);
		remove (tmp);
	}
	self.ec_my_temp = world;
};

void() EricCannon_Impulse =
{
	local entity c, start_e;
	local vector org, look_dir, look_a;

	EricCannon_NearPrompt ();
	if (self.impulse < 128 || self.impulse > 131)
		return;
	if (!autocvar_sv_cheats)
		return;

	// impulse 130 (3/4 hero angle) / impulse 131 (direct front closeup): cycle-teleport to map cannons!
	if (self.impulse == 130 || self.impulse == 131)
	{
		start_e = self.ec_prompt_ent;
		c = find (start_e, classname, "misc_eric_cannon");
		if (c == world)
			c = find (world, classname, "misc_eric_cannon");
		if (c != world)
		{
			self.ec_prompt_ent = c;
			makevectors ('0 1 0' * c.ec_yaw);
			if (self.impulse == 130)
				org = c.origin + v_forward * 116 - v_right * 84 + '0 0 28';
			else
				org = c.origin + v_forward * 122 + '0 0 28';
			setorigin (self, org);
			self.velocity = '0 0 0';
			self.angles = EC_LookViewAngles (org + '0 0 22', c.origin + v_forward * 34 + '0 0 64');
			self.fixangle = TRUE;
			centerprint (self, "Press H to man THE ERIC DEASON CANNON");
		}
		self.impulse = 0;
		return;
	}

	// Recycle player's previous unoccupied temp cannon so edicts never pile up
	c = EC_MyTemp (self);
	if (c != world && c.ec_pilot == world)
	{
		EC_FreeParts (c);
		remove (c);
		self.ec_my_temp = world;
	}

	if (self.impulse == 128)
	{
		self.impulse = 0;
		makevectors ('0 1 0' * self.v_angle_y);
		org = self.origin + v_forward * 145 + '0 0 16';
		c = spawn ();
		c.angles = '0 1 0' * self.v_angle_y;
		setorigin (c, org);
		EC_InitMonument (c, TRUE);
		c.ec_summoner = self;
		self.ec_my_temp = c;
		sprint (self, "Spawned THE ERIC DEASON CANNON ahead! Walk around to inspect, then press H to mount!\n");
		return;
	}

	if (self.impulse == 129)
	{
		self.impulse = 0;
		if (self.health <= 0 || EricCannon_Active (self) || self.veh_van != world || self.jb_vehicle != world)
			return;
		makevectors ('0 1 0' * self.v_angle_y);
		org = self.origin + v_forward * 48 + '0 0 16';
		c = spawn ();
		c.angles = '0 1 0' * self.v_angle_y;
		setorigin (c, org);
		EC_InitMonument (c, TRUE);
		c.ec_summoner = self;
		self.ec_my_temp = c;
		EC_Mount (self, c);
		return;
	}
};
