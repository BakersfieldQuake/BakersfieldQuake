#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BAKERSFIELD KILLER CAM - live 3rd-person killer-follow camera (SSQC)

On a Deathmatch/CTF kill by another player (human or bot), waits through a
short 0.5s death linger, then smoothly tracks the killer in 3rd-person (using
wall-checked chase offsets tailored for on-foot, vehicles, tank, and birds)
for 3.0s. Streams camera pose + killer/weapon labels via ENT_BM_KILLCAM (10)
and keeps p.clientcamera at the camera origin so server PVS tracks cleanly.
================
*/

float(float a, float b) KC_AngleDiff =
{
	local float d;

	d = b - a;
	while (d > 180)
		d = d - 360;
	while (d < -180)
		d = d + 360;
	return d;
};

float(float a) KC_PackShortAng =
{
	local float w;

	w = a - 360 * rint (a / 360);
	return rint (w * 64);
};

string(entity killer, entity inflictor) KC_WeaponLabel =
{
	local string cn;
	local float w, g;

	if (inflictor != world && inflictor != killer)
	{
		cn = inflictor.classname;
		if (cn == "bako_van" || cn == "bako_gokart")
			return (inflictor.veh_kind >= VEH_GOKART_1 && inflictor.veh_kind <= VEH_GOKART_6) ? "Go-Kart" : "Bakersfield Van";
		if (cn == "mm_tank")			return "Mega Man Tank";
		if (cn == "misc_vehicle_johnbird") return "Winged John";
		if (cn == "rocket_rider")		return "Rocket Rider";
		if (cn == "robdob")				return "Rob Dob Drone";
		if (cn == "megaman")			return "Mega Man";
		if (cn == "milky")				return "Milky Gun";
		if (cn == "dookie_shot")		return "Dookie Bazooka";
		if (cn == "wc_shot")			return "Wheelman Cannon";
		if (cn == "kyle_proj")			return "The Pocket Kyle";
		if (cn == "pickle")				return "Pickle Surprise";
		if (cn == "greenjar_proj" || cn == "greenguy_mini") return "Jar o' Green Guys";
		if (cn == "netsend_disk" || cn == "netsend_sentry") return "NetSend";
		if (cn == "bigbanana")			return "Banana";
		if (cn == "grenade")			return "Grenade Launcher";
		if (cn == "missile")			return "Rocket Launcher";
	}
	if (killer.veh_van != world)
		return (killer.veh_van.veh_kind >= VEH_GOKART_1 && killer.veh_van.veh_kind <= VEH_GOKART_6) ? "Go-Kart" : "Bakersfield Van";
	if (killer.mmt_tank != world)		return "Mega Man Tank";
	if (killer.jb_vehicle != world)		return "Winged John";
	if (killer.rr_vehicle != world)		return "Rocket Rider";
	if (killer.fd_head != world)		return "Rob Dob Drone";

	w = killer.weapon;
	if (w == IT_AXE)				return "Bonk Hammer";
	if (w == IT_SHOTGUN)			return "Shotgun";
	if (w == IT_SUPER_SHOTGUN)		return "Pump Shotgun";
	if (w == IT_NAILGUN)			return "Nailgun";
	if (w == IT_SUPER_NAILGUN)		return "Super Nailgun";
	if (w == IT_GRENADE_LAUNCHER)	return "Grenade Launcher";
	if (w == IT_ROCKET_LAUNCHER)	return "Rocket Launcher";
	if (w == IT_LIGHTNING)			return "Lightning Gun";
	if (w == IT_LASER_CANNON)		return "CCC Laser Cannon";
	if (w == IT_MEGAMAN)			return "Mega Man";
	if (w == IT_FUNGUN)
	{
		g = killer.fg_sel;
		if (g == FG_M4)				return "M4A1";
		if (g == FG_DOB)			return "Rob Dob";
		if (g == FG_PONG)			return "Jar o' Green Guys";
		if (g == FG_PICKLE)			return "Pickle Surprise";
		if (g == FG_NETSEND)		return "NetSend";
		if (g == FG_DOOKIE)			return "Dookie Bazooka";
		if (g == FG_WCANNON)		return "Wheelman Cannon";
		if (g == FG_KYLE)			return "The Pocket Kyle";
		if (g == FG_CYRAX)			return "Cyrax Net";
	}
	return "Weapon";
};

// ---------------------------------------------------------------- init / stats / commands

void() KC_Precache =
{
	registercvar ("bm_killcam", "1");
};

void() KC_Stats =
{
	clientstat (122, 2, kc_st_active);
	clientstat (123, 2, kc_st_seq);
};

void(entity attacker, entity targ, vector hitpos) KC_NoteHit =
{
	// No ring-buffer shot recording needed for live killer-follow mode
	if (!attacker || !targ || hitpos_x == 999999)
		return;
};

void(entity p) KC_ClearStrings =
{
	if (p.kc_kname != "")
	{
		strunzone (p.kc_kname);
		p.kc_kname = "";
	}
	if (p.kc_wname != "")
	{
		strunzone (p.kc_wname);
		p.kc_wname = "";
	}
};

void(entity p) KC_ClientConnect =
{
	p.kc_enabled = 1;
	p.kc_state = KC_NONE;
	p.kc_st_active = 0;
	p.kc_st_seq = 0;
	p.kc_killer = world;
	p.kc_kname = "";
	p.kc_wname = "";
	p.kc_cam_init = FALSE;
	p.kc_header_sent = FALSE;
	p.kc_relay = world;
	p.kc_cam = world;
};

void(entity p) KC_ClientDisconnect =
{
	if (p.kc_cam != world)
	{
		remove (p.kc_cam);
		p.kc_cam = world;
	}
	if (p.kc_relay != world)
	{
		remove (p.kc_relay);
		p.kc_relay = world;
	}
	KC_ClearStrings (p);
	p.kc_killer = world;
	p.kc_state = KC_NONE;
	p.kc_st_active = 0;
};

void(entity p, string val) KC_Command =
{
	local float v;

	v = (stof (val) != 0) ? 1 : 0;
	p.kc_enabled = v;
	if (!v && p.kc_state != KC_NONE)
		KC_Reset (p);
};

// ---------------------------------------------------------------- streaming

float(entity to, float sendflags) KC_RelaySend =
{
	if (to != self.owner || to.bm_obs || to.kc_state == KC_NONE)
		return FALSE;

	if (sendflags > 3)
		sendflags = 3;

	WriteByte (MSG_ENTITY, ENT_BM_KILLCAM);
	WriteByte (MSG_ENTITY, sendflags);
	WriteByte (MSG_ENTITY, to.kc_seq);

	if (sendflags & 1)
	{
		WriteString (MSG_ENTITY, (to.kc_kname != "") ? to.kc_kname : "Enemy");
		WriteString (MSG_ENTITY, (to.kc_wname != "") ? to.kc_wname : "Weapon");
	}
	if (sendflags & 2)
	{
		WriteCoord (MSG_ENTITY, to.kc_cam_org_x);
		WriteCoord (MSG_ENTITY, to.kc_cam_org_y);
		WriteCoord (MSG_ENTITY, to.kc_cam_org_z);
		WriteShort (MSG_ENTITY, KC_PackShortAng (to.kc_cam_ang_x));
		WriteShort (MSG_ENTITY, KC_PackShortAng (to.kc_cam_ang_y));
	}
	return TRUE;
};

void(entity p) KC_EnsureRelay =
{
	local entity r;

	if (p.kc_relay != world && !bm_wasfreed (p.kc_relay))
		return;
	r = spawn ();
	r.classname = "kc_relay";
	r.owner = p;
	setmodel (r, "progs/spike.mdl");
	setsize (r, '0 0 0', '0 0 0');
	r.alpha = 0.0001;
	r.scale = 0.01;
	r.SendEntity = KC_RelaySend;
	p.kc_relay = r;
};

// ---------------------------------------------------------------- 3rd-person camera

void(entity p, float snap) KC_UpdateChasePose =
{
	local entity k;
	local vector focus, want_ang, want_org;
	local float dist, up, dt, s_ang, s_pos;

	k = p.kc_killer;
	if (!k || k == world || bm_wasfreed (k) || k.classname != "player" || k.bm_obs)
		return;

	if (k.fd_head != world && !bm_wasfreed (k.fd_head))
	{
		focus = k.fd_head.origin;
		dist = 90;
		up = 22;
	}
	else if (k.mmt_tank != world && !bm_wasfreed (k.mmt_tank))
	{
		focus = k.mmt_tank.origin + '0 0 36';
		dist = 165;
		up = 52;
	}
	else if (k.veh_van != world && !bm_wasfreed (k.veh_van))
	{
		focus = k.veh_van.origin + '0 0 32';
		dist = 155;
		up = 46;
	}
	else if (k.jb_vehicle != world && !bm_wasfreed (k.jb_vehicle))
	{
		focus = k.jb_vehicle.origin + '0 0 28';
		dist = 140;
		up = 38;
	}
	else if (k.rr_vehicle != world && !bm_wasfreed (k.rr_vehicle))
	{
		focus = k.rr_vehicle.origin + '0 0 24';
		dist = 135;
		up = 34;
	}
	else
	{
		focus = k.origin + '0 0 28';
		dist = 110;
		up = 28;
	}

	want_ang_x = bound (-30, k.v_angle_x * 0.55 + 10, 35);
	want_ang_y = k.v_angle_y;
	want_ang_z = 0;

	if (p.kc_frame_t <= 0)
		dt = 0.02;
	else
		dt = bound (0.001, time - p.kc_frame_t, 0.1);
	p.kc_frame_t = time;

	if (!p.kc_cam_init || snap || vlen (focus - p.kc_cam_org) > 700)
		p.kc_cam_ang = want_ang;
	else
	{
		s_ang = min (1, dt * 7);
		p.kc_cam_ang_x = p.kc_cam_ang_x + (want_ang_x - p.kc_cam_ang_x) * s_ang;
		p.kc_cam_ang_y = p.kc_cam_ang_y + KC_AngleDiff (p.kc_cam_ang_y, want_ang_y) * s_ang;
		p.kc_cam_ang_z = 0;
	}

	makevectors (p.kc_cam_ang);
	want_org = focus - v_forward * dist + v_up * up + v_right * 12;
	traceline (focus, want_org, TRUE, k);
	if (trace_fraction < 1)
		want_org = focus + (want_org - focus) * max (0.18, trace_fraction - 0.08);

	if (!p.kc_cam_init || snap || vlen (want_org - p.kc_cam_org) > 700)
		p.kc_cam_org = want_org;
	else
	{
		s_pos = min (1, dt * 14);
		p.kc_cam_org = p.kc_cam_org + (want_org - p.kc_cam_org) * s_pos;
	}
	p.kc_cam_init = TRUE;
};

// ---------------------------------------------------------------- lifecycle

void(entity p) KC_Reset =
{
	if (!p || p == world)
		return;
	if (p.kc_cam != world)
	{
		if (!bm_wasfreed (p.kc_cam))
			remove (p.kc_cam);
		p.kc_cam = world;
	}
	if (p.clientcamera != p && p.ishuman == 1 && !p.bm_obs)
	{
		p.clientcamera = p;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, p);
	}
	p.kc_killer = world;
	p.kc_state = KC_NONE;
	p.kc_st_active = 0;
	p.kc_cam_init = FALSE;
	p.kc_header_sent = FALSE;
};

void(entity targ, entity attacker, entity inflictor) KC_OnPlayerKilled =
{
	if (!deathmatch || !autocvar_bm_killcam || intermission_running)
		return;
	if (!targ || targ.classname != "player" || targ.ishuman != 1 || targ.bm_obs)
		return;
	if (!attacker || attacker.classname != "player" || attacker == targ || attacker.bm_obs)
		return;
	if (!targ.kc_enabled)
		return;

	KC_EnsureRelay (targ);
	KC_ClearStrings (targ);

	targ.kc_seq = targ.kc_seq + 1;
	if (targ.kc_seq > 255 || targ.kc_seq < 1)
		targ.kc_seq = 1;

	targ.kc_killer = attacker;
	targ.kc_kname = strzone ((attacker.netname != "") ? attacker.netname : "Enemy");
	targ.kc_wname = strzone (KC_WeaponLabel (attacker, inflictor));
	targ.kc_state = KC_LINGER;
	targ.kc_linger_end = time + KC_LINGER_SEC;
	targ.kc_end = targ.kc_linger_end + KC_PLAY_SEC;
	targ.kc_skip_armed = FALSE;
	targ.kc_cam_init = FALSE;
	targ.kc_header_sent = FALSE;
	targ.kc_frame_t = time;
	targ.kc_st_active = KC_LINGER;
	targ.kc_st_seq = targ.kc_seq;

	KC_UpdateChasePose (targ, TRUE);
	setorigin (targ.kc_relay, targ.origin);
	targ.kc_relay.SendFlags = targ.kc_relay.SendFlags | 3;
};

void(entity p) KC_StreamForPlayer =
{
	local entity cam;

	if (p.kc_state == KC_NONE)
		return;
	if (intermission_running || !p.kc_enabled || !autocvar_bm_killcam)
	{
		KC_Reset (p);
		return;
	}

	KC_UpdateChasePose (p, FALSE);

	if (p.kc_state == KC_LINGER && time >= p.kc_linger_end)
	{
		p.kc_state = KC_PLAYING;
		p.kc_end = time + KC_PLAY_SEC;
		p.kc_st_active = KC_PLAYING;

		cam = p.kc_cam;
		if (!cam || bm_wasfreed (cam))
		{
			cam = spawn ();
			cam.classname = "kc_cam";
			cam.movetype = MOVETYPE_NONE;
			cam.solid = SOLID_NOT;
			cam.alpha = 0.01;
			cam.scale = 0.01;
			setmodel (cam, "progs/spike.mdl");
			setsize (cam, '0 0 0', '0 0 0');
			p.kc_cam = cam;
		}
		setorigin (cam, p.kc_cam_org);
		p.clientcamera = cam;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, cam);
	}
	else if (p.kc_state == KC_PLAYING && p.kc_cam != world && !bm_wasfreed (p.kc_cam))
		setorigin (p.kc_cam, p.kc_cam_org);

	if (p.kc_relay != world && !bm_wasfreed (p.kc_relay))
	{
		setorigin (p.kc_relay, (p.clientcamera != world && p.clientcamera != p) ? p.clientcamera.origin : p.origin);
		if (!p.kc_header_sent)
		{
			p.kc_header_sent = TRUE;
			p.kc_relay.SendFlags = p.kc_relay.SendFlags | 3;
		}
		else
			p.kc_relay.SendFlags = p.kc_relay.SendFlags | 2;
	}
};

void() KC_Tick =
{
	local entity p;

	if (!deathmatch || !autocvar_bm_killcam || intermission_running)
	{
		p = bm_player_head;
		while (p)
		{
			if (p.ishuman == 1 && p.kc_state != KC_NONE)
				KC_Reset (p);
			p = p.bm_player_next;
		}
		return;
	}

	p = bm_player_head;
	while (p)
	{
		if (p.ishuman == 1 && p.kc_state != KC_NONE)
			KC_StreamForPlayer (p);
		p = p.bm_player_next;
	}
};

// Called from PlayerDeathThink in client.qc; returns TRUE if killer cam owns death input/respawn right now
float(entity p) KC_DeathThink =
{
	if (p.kc_state == KC_NONE)
		return FALSE;

	if (!(p.button0 || p.button1 || p.button2))
		p.kc_skip_armed = TRUE;

	if ((p.kc_skip_armed && (p.button0 || p.button2)) || time >= p.kc_end)
	{
		p.button0 = 0;
		p.button1 = 0;
		p.button2 = 0;
		KC_Reset (p);
		respawn ();
		return TRUE;
	}
	return TRUE;
};
