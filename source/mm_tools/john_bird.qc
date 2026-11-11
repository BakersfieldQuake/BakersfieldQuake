/*
================
WINGED BREEZY-HAIR JOHN - FLYABLE VEHICLE IMPLEMENTATION (john_bird.qc)

Fast player-controllable flying bird-head vehicle:
  - Model: progs/john_bird_head.md3 (72 frames: fly, soar, hover, swoop, perch)
  - Flapping wingbeat SFX synced to flight state (sound/john_bird/flap1..4.wav)
  - Random "John" voice clips while flying (sound/john_bird/jv_fly00..13.wav)
  - 500 HP (exact 100 damage per direct rocket = 5 rockets to shoot him down!)
  - 3D tumbling feather bursts (progs/john_bird_feather.md3) on hit & shootdown
================
*/

void() JB_IdleThink;
void(entity attacker, float take) JB_Pain;
void() JB_Die;

void() JohnBird_Precache =
{
	if (jb_precached)
		return;
	jb_precached = TRUE;

	precache_model ("progs/john_bird_head.md3");
	precache_model ("progs/john_bird_feather.md3");
	precache_model ("progs/spike.mdl");

	precache_sound ("john_bird/flap1.wav");
	precache_sound ("john_bird/flap2.wav");
	precache_sound ("john_bird/flap3.wav");
	precache_sound ("john_bird/flap4.wav");
	precache_sound ("john_bird/takeoff.wav");
	precache_sound ("john_bird/swoop.wav");
	precache_sound ("john_bird/feather_hit.wav");
	precache_sound ("john_bird/shootdown.wav");
	precache_sound ("john_bird/jv_hurt.wav");

	precache_sound ("john_bird/jv_fly00.wav");
	precache_sound ("john_bird/jv_fly01.wav");
	precache_sound ("john_bird/jv_fly02.wav");
	precache_sound ("john_bird/jv_fly03.wav");
	precache_sound ("john_bird/jv_fly04.wav");
	precache_sound ("john_bird/jv_fly05.wav");
	precache_sound ("john_bird/jv_fly06.wav");
	precache_sound ("john_bird/jv_fly07.wav");
	precache_sound ("john_bird/jv_fly08.wav");
	precache_sound ("john_bird/jv_fly09.wav");
	precache_sound ("john_bird/jv_fly10.wav");
	precache_sound ("john_bird/jv_fly11.wav");
	precache_sound ("john_bird/jv_fly12.wav");
	precache_sound ("john_bird/jv_fly13.wav");
};

float(entity p) JohnBird_Flying =
{
	return p.jb_vehicle != world;
};

float(float a) JB_NormAngle =
{
	while (a > 180)
		a = a - 360;
	while (a < -180)
		a = a + 360;
	return a;
};

string(float idx) JB_VoiceSample =
{
	if (idx <= 0)  return "john_bird/jv_fly00.wav";
	if (idx == 1)  return "john_bird/jv_fly01.wav";
	if (idx == 2)  return "john_bird/jv_fly02.wav";
	if (idx == 3)  return "john_bird/jv_fly03.wav";
	if (idx == 4)  return "john_bird/jv_fly04.wav";
	if (idx == 5)  return "john_bird/jv_fly05.wav";
	if (idx == 6)  return "john_bird/jv_fly06.wav";
	if (idx == 7)  return "john_bird/jv_fly07.wav";
	if (idx == 8)  return "john_bird/jv_fly08.wav";
	if (idx == 9)  return "john_bird/jv_fly09.wav";
	if (idx == 10) return "john_bird/jv_fly10.wav";
	if (idx == 11) return "john_bird/jv_fly11.wav";
	if (idx == 12) return "john_bird/jv_fly12.wav";
	return "john_bird/jv_fly13.wav";
};

void(entity jb, float force_first) JB_PlayRandomVoice =
{
	local float pick, tries;
	local string wav;

	if (force_first)
		pick = 0;		// "Hmm... I'm floating!" on maiden takeoff (or random on subsequent)
	else
	{
		pick = floor (random () * JB_VOICE_COUNT);
		tries = 0;
		while ((pick == jb.jb_voice_last1 || pick == jb.jb_voice_last2) && tries < 8)
		{
			pick = floor (random () * JB_VOICE_COUNT);
			tries = tries + 1;
		}
	}
	if (pick >= JB_VOICE_COUNT)
		pick = JB_VOICE_COUNT - 1;

	jb.jb_voice_last2 = jb.jb_voice_last1;
	jb.jb_voice_last1 = pick;
	wav = JB_VoiceSample (pick);
	sound (jb, CHAN_VOICE, wav, 1, 0.55);
	jb.jb_voice_t = time + 4.2 + random () * 3.2;
};

void(entity jb, float vol, float pitch_pct) JB_PlayFlap =
{
	local string s;

	jb.jb_flap_idx = jb.jb_flap_idx + 1;
	if (jb.jb_flap_idx > 3)
		jb.jb_flap_idx = 0;

	if (jb.jb_flap_idx == 0)      s = "john_bird/flap1.wav";
	else if (jb.jb_flap_idx == 1) s = "john_bird/flap2.wav";
	else if (jb.jb_flap_idx == 2) s = "john_bird/flap3.wav";
	else                          s = "john_bird/flap4.wav";

	sound7 (jb, CHAN_BODY, s, vol, 0.65, pitch_pct);
};

// ---------------------------------------------------------------- 3D Fluttering Feather Debris

void() JB_FeatherThink =
{
	local float age;

	age = time - self.ltime;
	if (age >= self.wait)
	{
		remove (self);
		return;
	}
	// Gentle aerodynamic feather drag & sinusoidal side-to-side flutter
	makevectors ('0 1 0' * ((time * 360) + self.cnt));
	self.velocity_x = self.velocity_x * 0.90 + v_forward_x * 18;
	self.velocity_y = self.velocity_y * 0.90 + v_forward_y * 18;
	if (self.velocity_z < -78)
		self.velocity_z = -78;
	if (age > self.wait - 0.8)
		self.alpha = bound (0.05, (self.wait - age) / 0.8, 1);

	self.nextthink = time + 0.08;
};

void(vector org, float count, float boost) JB_SpawnFeathers =
{
	local float i;
	local entity f;

	i = 0;
	while (i < count)
	{
		f = spawn ();
		f.classname = "jb_feather";
		f.movetype = MOVETYPE_TOSS;
		f.solid = SOLID_NOT;
		setmodel (f, "progs/john_bird_feather.md3");
		setsize (f, '0 0 0', '0 0 0');
		setorigin (f, org + '1 0 0' * (crandom () * 24) + '0 1 0' * (crandom () * 28) + '0 0 1' * (crandom () * 16));
		f.velocity_x = crandom () * 220 * boost;
		f.velocity_y = crandom () * 220 * boost;
		f.velocity_z = (95 + random () * 185) * boost;
		f.avelocity_x = crandom () * 320;
		f.avelocity_y = crandom () * 360;
		f.avelocity_z = crandom () * 280;
		f.angles_x = random () * 360;
		f.angles_y = random () * 360;
		f.scale = 0.95 + random () * 0.55;
		f.alpha = 1;
		f.cnt = random () * 360;
		f.ltime = time;
		f.wait = 2.6 + random () * 1.4;
		f.think = JB_FeatherThink;
		f.nextthink = time + 0.08;
		i = i + 1;
	}
};

// ---------------------------------------------------------------- Pilot Camera & Mount / Dismount

void(entity p, entity jb) JB_UpdateCamera =
{
	local entity cam;
	local vector pivot, pos;

	cam = jb.jb_cam;
	if (cam == world)
		return;

	makevectors (p.v_angle);
	pivot = jb.origin + '0 0 44';
	if (p.jb_cam_mode == 1)
	{
		// First-person breezy-crown view (just ahead of John's brow)
		pos = jb.origin + '0 0 54' + v_forward * 22;
	}
	else
	{
		// Third-person avian chase camera showing flapping wings & breezy hair
		pos = pivot - v_forward * 148 + '0 0 26';
		traceline (pivot, pos, TRUE, jb);
		pos = trace_endpos;
		if (trace_fraction < 1)
			pos = pos + trace_plane_normal * 8;
	}
	setorigin (cam, pos);
	cam.angles = p.v_angle;
};

void(entity p, vector pos, vector vel, float yaw) JB_ReleasePlayer =
{
	p.jb_vehicle = world;
	if (p.ishuman == 1)
	{
		p.clientcamera = p;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, p);
	}
	p.alpha = 0;					// 0 = default opaque in DarkPlaces
	p.effects = p.effects - (p.effects & EF_NODRAW);
	if (p.health > 0)
	{
		p.movetype = p.jb_oldmove;
		if (p.movetype == MOVETYPE_NONE || p.movetype == 0)
			p.movetype = MOVETYPE_WALK;
		p.solid = p.jb_oldsolid;
		if (p.solid == SOLID_NOT || p.solid == 0)
			p.solid = SOLID_SLIDEBOX;
	}
	setorigin (p, pos);
	p.velocity = vel;
	p.flags = p.flags - (p.flags & FL_ONGROUND);
	p.angles = '0 0 0';
	p.angles_y = yaw;
	p.fixangle = TRUE;
};

void(entity jb) JB_Park =
{
	jb.jb_pilot = world;
	jb.jb_ai = FALSE;
	jb.velocity = '0 0 0';
	jb.angles_x = 0;
	jb.angles_z = 0;
	jb.movetype = MOVETYPE_TOSS;
	jb.solid = SOLID_BBOX;
	jb.takedamage = DAMAGE_AIM;
	setsize (jb, '-30 -38 -6', '30 38 56');
	setorigin (jb, jb.origin);
	jb.frame = 60;
	jb.think = JB_IdleThink;
	jb.nextthink = time + 0.08;
};

void(entity jb, vector exit_pos, vector exit_vel, float exploding) JB_Leave =
{
	local entity p;
	local float yaw;

	p = jb.jb_pilot;
	jb.jb_pilot = world;
	if (jb.jb_cam != world)
	{
		remove (jb.jb_cam);
		jb.jb_cam = world;
	}
	if (p != world && p.classname == "player")
	{
		yaw = p.v_angle_y;
		JB_ReleasePlayer (p, exit_pos, exit_vel, yaw);
	}
	if (!exploding)
		JB_Park (jb);
};

float(entity p, vector pos) JB_SpotClear =
{
	tracebox (pos, VEC_HULL_MIN, VEC_HULL_MAX, pos, FALSE, p);
	if (trace_startsolid || trace_allsolid)
		return FALSE;
	return TRUE;
};

vector(entity jb, entity p) JB_FindExitPos =
{
	local vector cand;

	makevectors ('0 1 0' * jb.angles_y);
	cand = jb.origin + '0 0 28';
	if (JB_SpotClear (p, cand))
		return cand;
	cand = jb.origin - v_forward * 54 + '0 0 26';
	if (JB_SpotClear (p, cand))
		return cand;
	cand = jb.origin + v_right * 56 + '0 0 26';
	if (JB_SpotClear (p, cand))
		return cand;
	cand = jb.origin - v_right * 56 + '0 0 26';
	if (JB_SpotClear (p, cand))
		return cand;
	return jb.origin + '0 0 24';
};

void(entity p, entity jb) JB_Enter =
{
	local entity cam, oldself;

	if (p.health <= 0 || p.jb_vehicle != world || p.veh_van != world || p.fd_head != world)
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

	jb.jb_pilot = p;
	jb.jb_ai = FALSE;
	p.jb_vehicle = jb;
	p.jb_oldmove = p.movetype;
	p.jb_oldsolid = p.solid;
	p.jb_prev_yaw = p.v_angle_y;

	// Flight hull: generous rocket target box, smooth doorway/alley clearance
	jb.movetype = MOVETYPE_NONE;
	jb.solid = SOLID_BBOX;
	jb.takedamage = DAMAGE_AIM;
	setsize (jb, '-28 -36 -4', '28 36 58');
	setorigin (jb, jb.origin + '0 0 14');
	jb.velocity = '0 0 160';
	jb.angles_x = 0;
	jb.angles_y = p.v_angle_y;
	jb.angles_z = 0;
	jb.jb_flap_t = time + 0.12;
	jb.jb_voice_t = time + 0.24;		// plays a "John" line right after takeoff clap!
	jb.jb_swoop_until = 0;

	// Hide pilot body cleanly inside Winged John; keep takedamage so bots still target & shoot rockets!
	p.movetype = MOVETYPE_NONE;
	p.solid = SOLID_NOT;
	p.velocity = '0 0 0';
	p.alpha = 0.01;
	p.effects = p.effects | EF_NODRAW;
	setorigin (p, jb.origin + '0 0 20');

	cam = spawn ();
	cam.classname = "jb_cam";
	cam.movetype = MOVETYPE_NONE;
	cam.solid = SOLID_NOT;
	cam.alpha = 0.01;
	cam.scale = 0.01;
	setmodel (cam, "progs/spike.mdl");
	setsize (cam, '0 0 0', '0 0 0');
	setorigin (cam, jb.origin + '0 0 48');
	jb.jb_cam = cam;

	if (p.ishuman == 1)
	{
		p.clientcamera = cam;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, cam);
	}
	JB_UpdateCamera (p, jb);

	sound (jb, CHAN_ITEM, "john_bird/takeoff.wav", 1, 0.6);
	JB_SpawnFeathers (jb.origin + '0 0 28', 4, 0.7);
	if (!p.jb_hint_shown)
	{
		p.jb_hint_shown = TRUE;
		centerprint (p, "WASD+Mouse fly | SPACE climb | FIRE swoop | K cam | H exit");
	}
};

// ---------------------------------------------------------------- Collision & Dive-Ram

void(entity jb, entity pilot, entity hit) JB_CheckSwoopRam =
{
	local vector push;

	if (hit == world || hit == pilot || hit == jb)
		return;
	if (!hit.takedamage || hit.health <= 0)
		return;
	if (time < jb.jb_ram_cd)
		return;
	if (vlen (jb.velocity) < 720)
		return;

	jb.jb_ram_cd = time + 0.45;
	sound (jb, CHAN_AUTO, "john_bird/feather_hit.wav", 1, ATTN_NORM);
	JB_SpawnFeathers (jb.origin + '0 0 32', 6, 1.1);

	push = normalize (jb.velocity);
	push_z = 0.42;
	push = normalize (push);
	if (hit.movetype == MOVETYPE_WALK || hit.movetype == MOVETYPE_STEP || hit.movetype == MOVETYPE_TOSS)
	{
		hit.flags = hit.flags - (hit.flags & FL_ONGROUND);
		hit.velocity = hit.velocity + push * 520 + '0 0 220';
	}
	jb_inflicting = 2;
	if (pilot != world)
		T_Damage (hit, jb, pilot, 95);
	else
		T_Damage (hit, jb, jb, 95);
	jb_inflicting = 0;
};

void(entity jb, entity pilot, float dt) JB_SlideMove =
{
	local vector start, dest, rem, n1;
	local float vn;

	if (vlen (jb.velocity) < 0.5)
		return;

	start = jb.origin;
	dest = start + jb.velocity * dt;
	tracebox (start, jb.mins, jb.maxs, dest, FALSE, jb);
	if (trace_allsolid || trace_startsolid)
	{
		// Gentle nudge upward if wedged against a lip
		tracebox (start + '0 0 8', jb.mins, jb.maxs, start + '0 0 8', TRUE, jb);
		if (!trace_startsolid)
			setorigin (jb, start + '0 0 8');
		return;
	}
	setorigin (jb, trace_endpos);
	if (trace_fraction >= 1)
		return;

	if (trace_ent != world)
		JB_CheckSwoopRam (jb, pilot, trace_ent);

	n1 = trace_plane_normal;
	vn = jb.velocity * n1;
	if (vn < 0)
		jb.velocity = jb.velocity - n1 * vn;

	// Second slide pass along wall/rooftop plane
	rem = jb.velocity * (dt * (1 - trace_fraction));
	if (vlen (rem) > 0.25)
	{
		tracebox (jb.origin, jb.mins, jb.maxs, jb.origin + rem, FALSE, jb);
		if (!trace_allsolid && !trace_startsolid)
		{
			setorigin (jb, trace_endpos);
			if (trace_fraction < 1)
			{
				vn = jb.velocity * trace_plane_normal;
				if (vn < 0)
					jb.velocity = jb.velocity - trace_plane_normal * vn;
			}
		}
	}
};

// ---------------------------------------------------------------- Animation & Audio Driver

void(entity jb, float dt, float thr_in, float climb_in, float swooping) JB_UpdateAnimAndAudio =
{
	local float hspd, clip_start, clip_len, fps, flap_gap, flap_vol, flap_pitch, idx;

	hspd = vlen (jb.velocity);
	if (swooping || jb.velocity_z < -420)
	{
		// Clip 4: Peregrine Swoop / Dive (frames 48..59)
		clip_start = 48;
		clip_len = 12;
		fps = 16;
		flap_gap = 0.52;
		flap_vol = 0.55;
		flap_pitch = 114;
	}
	else if (climb_in > 0.2 || hspd < 230)
	{
		// Clip 3: Rapid Hover Flutter / Vigorous Climb (frames 32..47)
		clip_start = 32;
		clip_len = 16;
		fps = 19;
		flap_gap = 0.22;
		flap_vol = 0.90;
		flap_pitch = 108;
	}
	else if (thr_in <= 0.05 && climb_in <= 0 && hspd > 340)
	{
		// Clip 2: Windy Thermal Soar / Outstretched Glide (frames 16..31)
		clip_start = 16;
		clip_len = 16;
		fps = 11;
		flap_gap = 1.05;
		flap_vol = 0.38;
		flap_pitch = 92;
	}
	else
	{
		// Clip 1: Fast Cruising Wingbeat & Breezy Hair (frames 0..15)
		clip_start = 0;
		clip_len = 16;
		fps = 14 + bound (0, hspd / 130, 8);
		flap_gap = bound (0.23, 0.36 - hspd * 0.00010, 0.35);
		flap_vol = 0.85;
		flap_pitch = 96 + bound (0, hspd * 0.012, 14);
	}

	jb.jb_anim_clock = jb.jb_anim_clock + dt * fps;
	idx = floor (jb.jb_anim_clock);
	idx = idx - clip_len * floor (idx / clip_len);
	jb.frame = clip_start + idx;

	// Synced wing-flapping sound
	if (time >= jb.jb_flap_t)
	{
		JB_PlayFlap (jb, flap_vol, flap_pitch + crandom () * 4);
		jb.jb_flap_t = time + flap_gap;
	}

	// Periodic random "John" audio while flying!
	if (time >= jb.jb_voice_t)
	{
		JB_PlayRandomVoice (jb, (jb.jb_voice_last1 < 0));
	}

	// Battle-damage smoke & singed embers when down to 1-2 rockets left (<= 200 HP)
	if (jb.health <= 200 && time >= jb.jb_smoke_t)
	{
		jb.jb_smoke_t = time + 0.09;
		if (veh_fx_smoke > 0)
			pointparticles (veh_fx_smoke, jb.origin + '0 0 34', '0 0 24', 1);
	}
};

// ---------------------------------------------------------------- Per-Frame Player Flight Loop

float() JohnBird_Frame =
{
	local entity jb;
	local float dt, fwd_in, str_in, up_in, swooping, max_spd, yaw_rate, target_roll, k;
	local vector wish, dir_ang;

	jb = self.jb_vehicle;
	if (jb == world)
		return FALSE;
	if (jb.jb_pilot != self || jb.health <= 0 || self.health <= 0)
	{
		JB_ReleasePlayer (self, self.origin, '0 0 0', self.v_angle_y);
		return FALSE;
	}

	dt = frametime;
	if (dt < 0.001)
		dt = 0.001;
	if (dt > 0.05)
		dt = 0.05;

	// Handle dismount (H = 86, P = 98), camera toggle (K = 87), and on-demand John voice (V = 20)
	if (self.impulse == 86 || self.impulse == 98)
	{
		self.impulse = 0;
		JB_Leave (jb, JB_FindExitPos (jb, self), jb.velocity * 0.35, FALSE);
		return TRUE;
	}
	if (self.impulse == 87)
	{
		self.jb_cam_mode = 1 - self.jb_cam_mode;
		if (self.jb_cam_mode == 1)
			sprint (self, "Winged John camera: First-Person Breezy-Crown View\n");
		else
			sprint (self, "Winged John camera: Third-Person Avian Chase View\n");
	}
	else if (self.impulse == 20 && time >= jb.jb_voice_t - 6.0)
	{
		JB_PlayRandomVoice (jb, FALSE);
	}
	self.impulse = 0;

	self.flags = self.flags - (self.flags & FL_ONGROUND);
	self.velocity = '0 0 0';

	// Read 3D flight inputs
	makevectors (self.v_angle);
	fwd_in = bound (-1, self.movement_x / 200, 1);
	str_in = bound (-1, self.movement_y / 200, 1);
	up_in = 0;
	if (self.button2 || self.movement_z > 40)
		up_in = 1;
	else if (self.movement_z < -40)
		up_in = -1;

	// MOUSE1 (Fire): Supersonic Peregrine Falcon Swoop Boost!
	if (self.button0 && time >= jb.jb_swoop_cd)
	{
		jb.jb_swoop_until = time + 0.85;
		jb.jb_swoop_cd = time + 1.25;
		sound (jb, CHAN_ITEM, "john_bird/swoop.wav", 1, 0.6);
		if (random () < 0.45 && time >= jb.jb_voice_t - 5.2)
			JB_PlayRandomVoice (jb, FALSE);
	}
	swooping = (time < jb.jb_swoop_until);

	wish = '0 0 0';
	if (swooping)
	{
		wish = v_forward * JB_SPEED_SWOOP + v_right * (str_in * JB_SPEED_STRAFE * 0.7);
		max_spd = JB_SPEED_SWOOP;
	}
	else
	{
		if (fwd_in > 0)
			wish = wish + v_forward * (fwd_in * JB_SPEED_CRUISE);
		else if (fwd_in < 0)
			wish = wish + v_forward * (fwd_in * 300);

		wish = wish + v_right * (str_in * JB_SPEED_STRAFE);
		if (up_in > 0)
			wish_z = wish_z + JB_SPEED_CLIMB;
		else if (up_in < 0)
			wish_z = wish_z - 460;
		max_spd = JB_SPEED_CRUISE + 140;
	}

	if (fwd_in < -0.2 && !swooping)
	{
		// Flare wings to air-brake rapidly into a hover!
		k = bound (0, dt * 6.5, 1);
		jb.velocity = jb.velocity + (wish - jb.velocity) * k;
	}
	else if (vlen (wish) > 10)
	{
		// Responsive fast avian thrust toward wish velocity
		k = bound (0, dt * (swooping ? 7.5 : 4.6), 1);
		jb.velocity = jb.velocity + (wish - jb.velocity) * k;
	}
	else
	{
		// Coasting thermal glide: low horizontal drag + gentle sink
		jb.velocity_x = jb.velocity_x * bound (0, 1 - dt * 1.45, 1);
		jb.velocity_y = jb.velocity_y * bound (0, 1 - dt * 1.45, 1);
		jb.velocity_z = jb.velocity_z * bound (0, 1 - dt * 2.40, 1) - 38 * dt;
	}

	if (vlen (jb.velocity) > max_spd)
		jb.velocity = normalize (jb.velocity) * max_spd;

	// Slide-move Winged John through the 3D world
	JB_SlideMove (jb, self, dt);

	// Smooth 3D orientation + aerodynamic roll banking into turns!
	yaw_rate = JB_NormAngle (self.v_angle_y - self.jb_prev_yaw) / dt;
	self.jb_prev_yaw = self.v_angle_y;
	target_roll = bound (-34, (0 - yaw_rate * 0.13) + str_in * 20, 34);

	if (vlen (jb.velocity) > 140)
	{
		dir_ang = vectoangles (jb.velocity);
		jb.angles_x = bound (-52, dir_ang_x, 52);
	}
	else
	{
		jb.angles_x = bound (-38, 0 - self.v_angle_x * 0.55, 38);
	}
	jb.angles_y = self.v_angle_y;
	jb.angles_z = jb.angles_z + (target_roll - jb.angles_z) * bound (0, dt * 9.0, 1);

	// Keep hidden pilot synced inside bird hull for PVS, spatial audio, and bot rocket targeting
	setorigin (self, jb.origin + '0 0 20');
	JB_UpdateCamera (self, jb);
	JB_UpdateAnimAndAudio (jb, dt, (fwd_in > 0 ? fwd_in : 0), up_in, swooping);

	return TRUE;
};

// ---------------------------------------------------------------- Perched Idle, AI Autopilot & Respawn

void() JB_Respawn =
{
	self.jb_dying = FALSE;
	self.health = JB_MAX_HP;
	self.max_health = JB_MAX_HP;
	self.skin = 0;
	self.alpha = 1;
	self.effects = self.effects - (self.effects & EF_NODRAW);
	setmodel (self, "progs/john_bird_head.md3");
	setorigin (self, self.jb_spawn_org);
	self.angles = '0 0 0';
	self.angles_y = self.jb_spawn_yaw;
	JB_Park (self);
	sound (self, CHAN_ITEM, "items/itembk2.wav", 1, ATTN_NORM);
};

void() JB_AutopilotThink =
{
	local float dt, ang, rad, spd;
	local vector target_pos, delta, dir_ang;

	if (self.health <= 0)
		return;
	if (!self.jb_ai || self.jb_pilot != world)
	{
		self.think = JB_IdleThink;
		self.nextthink = time + 0.08;
		return;
	}

	dt = 0.05;
	self.jb_ai_phase = self.jb_ai_phase + dt * 78;
	if (self.jb_ai_phase >= 360)
		self.jb_ai_phase = self.jb_ai_phase - 360;
	rad = 290;
	ang = self.jb_ai_phase;
	// Fast banked orbit + vertical bob overhead so player can test shooting him down with 5 rockets!
	makevectors ('0 1 0' * ang);
	target_pos_x = self.jb_spawn_org_x + v_forward_x * rad;
	target_pos_y = self.jb_spawn_org_y + v_forward_y * rad * 0.82;
	makevectors ('0 1 0' * (ang * 2));
	target_pos_z = self.jb_spawn_org_z + v_forward_y * 42;

	delta = target_pos - self.origin;
	spd = 760;
	if (vlen (delta) > 8)
		self.velocity = normalize (delta) * spd;
	JB_SlideMove (self, world, dt);

	if (vlen (self.velocity) > 40)
	{
		dir_ang = vectoangles (self.velocity);
		self.angles_x = bound (-35, dir_ang_x, 35);
		self.angles_y = dir_ang_y;
		self.angles_z = -24;
	}
	JB_UpdateAnimAndAudio (self, dt, 1.0, 0, FALSE);
	self.nextthink = time + dt;
};

void() JB_IdleThink =
{
	local entity p;
	local float idx;

	if (self.health <= 0)
		return;

	p = self.jb_pilot;
	if (p != world)
	{
		// Safety watchdog: if pilot died or disconnected outside W_WeaponFrame
		if (p.classname != "player" || p.health <= 0 || p.jb_vehicle != self)
			JB_Leave (self, self.origin + '0 0 28', '0 0 0', FALSE);
		self.nextthink = time + 0.1;
		return;
	}

	if (self.jb_ai)
	{
		self.think = JB_AutopilotThink;
		self.nextthink = time + 0.05;
		return;
	}

	// Perched idle: play perch_breeze frames 60..71
	idx = floor (time * 9.0);
	idx = idx - 12 * floor (idx / 12);
	self.frame = 60 + idx;

	if (self.health <= 200 && veh_fx_smoke > 0 && time >= self.jb_smoke_t)
	{
		self.jb_smoke_t = time + 0.16;
		pointparticles (veh_fx_smoke, self.origin + '0 0 32', '0 0 18', 1);
	}
	self.nextthink = time + 0.1;
};

// ---------------------------------------------------------------- 5-Rocket Damage & Shootdown

void(entity attacker, float take) JB_Pain =
{
	local float r_left;
	local string msg;

	// feathers, the thud and the HP line at most 5 times a second: full-auto fire (11 hits/s) piled up hundreds of
	// thinking feathers and flooded the shooter's console
	if (time < self.jb_feather_t && self.health > JB_ROCKET_DMG)
		return;
	self.jb_feather_t = time + 0.2;
	JB_SpawnFeathers (self.origin + '0 0 34', 8, 1.0);
	sound (self, CHAN_AUTO, "john_bird/feather_hit.wav", 1, 0.55);

	if (self.health <= 200)
		self.skin = 1;		// scorched battle-damaged plumage + ember tips!

	if (random () < 0.45 && time >= self.pain_finished)
	{
		sound (self, CHAN_VOICE, "john_bird/jv_hurt.wav", 1, 0.55);
		self.pain_finished = time + 0.9;
		self.jb_voice_t = time + 3.2;
	}

	r_left = ceil (self.health / JB_ROCKET_DMG);
	if (r_left < 1)
		r_left = 1;

	msg = strcat ("Winged John hit! [", ftos (ceil (self.health)), "/500 HP — ", ftos (r_left));
	if (r_left == 1)
		msg = strcat (msg, " rocket left!]\n");
	else
		msg = strcat (msg, " rockets left]\n");

	if (attacker != world && attacker.classname == "player" && attacker.ishuman == 1)
		sprint (attacker, msg);
	if (self.jb_pilot != world && self.jb_pilot != attacker && self.jb_pilot.ishuman == 1)
		sprint (self.jb_pilot, msg);
};

void() JB_Die =
{
	local entity pilot, killer;
	local vector boom_org, eject_vel;

	// a flying John is MOVETYPE_NONE, so Killed does not clear takedamage: without this his own blast below finds him
	// again, kills him again and recurses until the QC stack overflows (server error). A perched (TOSS) John arrives
	// here with takedamage already cleared by Killed, so the guard is a flag of its own, not takedamage
	if (self.jb_dying)
		return;
	self.jb_dying = TRUE;
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;

	killer = self.enemy;
	if (killer == world)
		killer = damage_attacker;

	boom_org = self.origin + '0 0 32';
	pilot = self.jb_pilot;

	// Eject pilot cleanly BEFORE blast so camera & solid state are restored
	if (pilot != world)
	{
		pilot.jb_cooldown_t = time + 2.0;
		eject_vel = self.velocity * 0.45 + '0 0 240';
		JB_Leave (self, JB_FindExitPos (self, pilot), eject_vel, TRUE);
	}

	// Spectacular 5th-rocket shootdown fireball + 28 fluttering 3D feathers + John death cry!
	sound (self, CHAN_VOICE, "john_bird/shootdown.wav", 1, 0.45);
	sound (self, CHAN_AUTO, "weapons/r_exp3.wav", 1, 0.50);
	JB_SpawnFeathers (boom_org, 28, 1.45);

	WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte (MSG_BROADCAST, TE_EXPLOSION);
	WriteCoord (MSG_BROADCAST, boom_org_x);
	WriteCoord (MSG_BROADCAST, boom_org_y);
	WriteCoord (MSG_BROADCAST, boom_org_z);
	if (veh_fx_explode > 0)
		pointparticles (veh_fx_explode, boom_org, '0 0 0', 1);

	if (killer != world && killer.classname == "player" && killer.ishuman == 1)
		sprint (killer, "BOOM! Shot down Winged Breezy-Hair John! (5/5 Rockets)\n");

	// Blast damage to ejected pilot & nearby enemies (credited to shooter!)
	jb_inflicting = 1;
	if (pilot != world && pilot.health > 0)
	{
		if (killer != world && killer != pilot)
			T_Damage (pilot, self, killer, 165);
		else
			T_Damage (pilot, self, self, 115);
	}
	if (killer != world)
		T_RadiusDamage (self, killer, 120, pilot);
	else
		T_RadiusDamage (self, self, 120, pilot);
	jb_inflicting = 0;

	if (self.jb_temp)
	{
		self.solid = SOLID_NOT;
		self.takedamage = DAMAGE_NO;
		self.movetype = MOVETYPE_NONE;
		self.model = string_null;
		self.think = SUB_Remove;
		self.nextthink = time + 1.5;		// keep entity alive 1.5s so shootdown.wav finishes playing!
	}
	else
	{
		// Map-placed perched Winged John respawns after 22s!
		self.solid = SOLID_NOT;
		self.takedamage = DAMAGE_NO;
		self.movetype = MOVETYPE_NONE;
		self.effects = self.effects | EF_NODRAW;
		self.velocity = '0 0 0';
		self.think = JB_Respawn;
		self.nextthink = time + 22;
	}
};

// ---------------------------------------------------------------- Entity Spawn, Prompts & Impulses

void(entity jb, float is_temp) JB_InitEntity =
{
	JohnBird_Precache ();
	jb_has_birds = TRUE;

	jb.classname = "misc_vehicle_johnbird";
	jb.netname = "Winged Breezy-Hair John";
	jb.jb_temp = is_temp;
	jb.jb_pilot = world;
	jb.jb_cam = world;
	jb.jb_voice_last1 = -1;
	jb.jb_voice_last2 = -1;
	jb.health = JB_MAX_HP;
	jb.max_health = JB_MAX_HP;
	jb.skin = 0;
	jb.th_pain = JB_Pain;
	jb.th_die = JB_Die;

	setmodel (jb, "progs/john_bird_head.md3");
	jb.jb_spawn_org = jb.origin;
	jb.jb_spawn_yaw = jb.angles_y;
	JB_Park (jb);
};

// Map entity: misc_vehicle_johnbird
void() misc_vehicle_johnbird =
{
	setorigin (self, self.origin + '0 0 8');
	JB_InitEntity (self, FALSE);
};

entity(entity p) JohnBird_NearPerched =
{
	local entity e, best;
	local float d, bd;

	if (!jb_has_birds)
		return world;
	best = world;
	bd = 170;
	e = findradius (p.origin, 170);
	while (e != world)
	{
		if (e.classname == "misc_vehicle_johnbird" && e.health > 0 && e.jb_pilot == world && !e.jb_ai)
		{
			d = vlen (e.origin - p.origin);
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

void() JohnBird_NearPrompt =
{
	local entity jb;

	if (!jb_has_birds || self.ishuman != 1 || self.health <= 0 || self.jb_vehicle != world || self.veh_van != world || self.classname != "player")
		return;
	if (time < self.jb_prompt_scan_t)
		return;
	self.jb_prompt_scan_t = time + 0.12;
	jb = JohnBird_NearPerched (self);
	if (jb == world)
	{
		if (time > self.jb_prompt_t)
			self.jb_prompt_ent = world;
		return;
	}
	if (self.jb_hint_shown || time < self.jb_prompt_t)
		return;
	if (self.jb_prompt_ent == jb)
	{
		self.jb_prompt_t = time + 35;
		return;
	}
	self.jb_prompt_ent = jb;
	self.jb_prompt_t = time + 35;
	centerprint (self, "Press H to fly Winged John");
};

// Called on H (impulse 86) on foot: mounts nearest perched Winged John if within reach!
float() JohnBird_TryEnterKey =
{
	local entity jb, van;

	if (self.health <= 0 || self.jb_vehicle != world || self.veh_van != world)
		return FALSE;
	jb = JohnBird_NearPerched (self);
	if (jb == world)
		return FALSE;

	// If also beside a van, pick whichever vehicle is physically closer
	van = Veh_SeatOf (self);
	if (van != world && vlen (van.origin - self.origin) < vlen (jb.origin - self.origin))
		return FALSE;

	JB_Enter (self, jb);
	return TRUE;
};

// the player's own summoned Winged John, or world once he was shot down and freed (the edict may since be reused by
// anything else, so jb_my_temp alone must never be trusted for a remove)
entity(entity p) JB_MyTemp =
{
	local entity e;

	e = p.jb_my_temp;
	if (e != world && (bm_wasfreed (e) || e.classname != "misc_vehicle_johnbird" || !e.jb_temp || e.jb_summoner != p))
	{
		p.jb_my_temp = world;
		e = world;
	}
	return e;
};

void() JohnBird_ClientGone =
{
	local entity jb;

	jb = self.jb_vehicle;
	if (jb != world && jb.jb_pilot == self)
		JB_Leave (jb, jb.origin + '0 0 28', '0 0 0', FALSE);
	self.jb_vehicle = world;
	jb = JB_MyTemp (self);
	if (jb != world && jb.jb_pilot == world)
		remove (jb);
	self.jb_my_temp = world;
};

void() JB_PruneTempBirds =
{
	local entity e, oldest;
	local float n;

	n = 0;
	oldest = world;
	e = find (world, classname, "misc_vehicle_johnbird");
	while (e != world)
	{
		if (e.jb_temp && e.jb_pilot == world && e.health > 0)
		{
			n = n + 1;
			if (oldest == world)
				oldest = e;
		}
		e = find (e, classname, "misc_vehicle_johnbird");
	}
	if (n > 5 && oldest != world)
		remove (oldest);
};

void() JohnBird_Impulse =
{
	local entity jb;
	local vector org;

	JohnBird_NearPrompt ();
	if (self.impulse < 97 || self.impulse > 99)
		return;

	// P (impulse 98): Summon & immediately fly Winged Breezy-Hair John anywhere!
	if (self.impulse == 98)
	{
		self.impulse = 0;
		if (self.health <= 0 || self.veh_van != world || self.fd_head != world)
			return;
		if (time < self.jb_cooldown_t)
		{
			sprint (self, "Winged John is recovering feathers...\n");
			return;
		}
		// Recycle player's previous unoccupied personal temp bird so edicts never accumulate
		jb = JB_MyTemp (self);
		if (jb != world && jb.jb_pilot == world && jb.health > 0)
		{
			remove (jb);
			self.jb_my_temp = world;
		}
		jb = spawn ();
		jb.angles = '0 0 0';
		jb.angles_y = self.v_angle_y;
		setorigin (jb, self.origin + '0 0 12');
		JB_InitEntity (jb, TRUE);
		jb.jb_summoner = self;
		self.jb_my_temp = jb;
		JB_Enter (self, jb);
		return;
	}

	if (!autocvar_sv_cheats)
		return;

	// impulse 97: Spawn perched Winged Breezy-Hair John 180 units ahead (mount with H or test 5-rocket shootdown!)
	if (self.impulse == 97)
	{
		self.impulse = 0;
		JB_PruneTempBirds ();
		makevectors ('0 1 0' * self.v_angle_y);
		org = self.origin + v_forward * 180 + '0 0 18';
		jb = spawn ();
		jb.angles = '0 0 0';
		jb.angles_y = JB_NormAngle (self.v_angle_y + 180);
		setorigin (jb, org);
		JB_InitEntity (jb, TRUE);
		sprint (self, "Spawned perched Winged Breezy-Hair John (500 HP — Press H to fly, or 5 rockets to shoot down!)\n");
		return;
	}

	// impulse 99: Spawn fast-circling Autopilot Winged John overhead for 5-rocket target practice!
	if (self.impulse == 99)
	{
		self.impulse = 0;
		JB_PruneTempBirds ();
		makevectors ('0 1 0' * self.v_angle_y);
		org = self.origin + v_forward * 280 + '0 0 190';
		jb = spawn ();
		jb.angles = '0 0 0';
		jb.angles_y = self.v_angle_y;
		setorigin (jb, org);
		JB_InitEntity (jb, TRUE);
		jb.movetype = MOVETYPE_NONE;
		setsize (jb, '-28 -36 -4', '28 36 58');
		jb.jb_spawn_org = org;
		jb.jb_ai = TRUE;
		jb.jb_flap_t = time + 0.1;
		jb.jb_voice_t = time + 0.35;
		jb.think = JB_AutopilotThink;
		jb.nextthink = time + 0.05;
		sprint (self, "Launched fast-flying Autopilot Winged John overhead! Shoot him with 5 rockets!\n");
		return;
	}
};
