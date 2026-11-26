// BakersfieldQuake CSQC - Character Studio preview
// Adds the preview player to the normal view, driven by MenuQC cvars (bm_char_*, bm_hat, _cl_color).

float BM_VF_MIN            = 1;
float BM_VF_SIZE           = 4;
float BM_VF_FOV            = 8;
float BM_VF_ORIGIN         = 11;
float BM_VF_ANGLES         = 15;
float BM_VF_DRAWWORLD      = 19;
float BM_VF_DRAWENGINESBAR = 20;
float BM_VF_DRAWCROSSHAIR  = 21;

float BM_EF_NOSHADOW       = 4096;
float BM_EF_FULLBRIGHT     = 512;

entity bm_char_ent;
entity bm_char_hat;
float bm_char_hat_shown;
float bm_char_anchored;		// the preview spot is picked once each time the editor opens
float bm_hat_sent;		// the choice last sent to the server
float bm_hat_send_t;
entity bm_char_legs;
string bm_char_cur_mdl;
string bm_char_cur_legs;

float(float deg) BM_Char_SinDeg =
{
	local float r;
	r = sin(deg * 0.0174532925);
	return r;
};

float(float deg) BM_Char_CosDeg =
{
	local float r;
	r = cos(deg * 0.0174532925);
	return r;
};

// Resolve active player model (ready for future selectable model registry)
string() BM_Char_ResolveBodyModel =
{
	if (cvar("3rd_person_visible_weapons") != 0 && cvar("player_model") == 5)
		return "progs/player_torso.mdl";
	return "progs/player_id1.mdl";
};

// Tell the server which hat this player picked. Resent now and then, so a command lost while joining, or a
// server that restarted the map, still learns it.
void() BM_Hat_SendChoice =
{
	local float h;
	h = bound (0, floor (cvar ("bm_hat")), BM_HAT_COUNT);
	if (h == bm_hat_sent && time < bm_hat_send_t && time > bm_hat_send_t - 6)
		return;
	bm_hat_sent = h;
	bm_hat_send_t = time + 5;
	localcmd (strcat ("cmd bm_hat ", ftos (h), "\n"));
};

void() BM_Char_Init =
{
	registercvar("bm_char_open", "0");
	registercvar("bm_char_bg_owned", "0");
	registercvar("bm_char_vp_x", "0");
	registercvar("bm_char_vp_y", "0");
	registercvar("bm_char_vp_w", "320");
	registercvar("bm_char_vp_h", "240");
	registercvar("bm_char_yaw", "25");
	registercvar("bm_char_pitch", "8");
	registercvar("bm_char_zoom", "1.0");
	registercvar("bm_char_spin", "1");
	registercvar("bm_char_pose", "0");
	registercvar("bm_char_model", "0");
	registercvar("bm_hat", "0");

	precache_model("progs/player_id1.mdl");
	precache_model("progs/player_torso.mdl");
	precache_model("progs/player_low.mdl");

	bm_char_anchored = FALSE;
	bm_char_ent = world;
	bm_char_hat = world;
	bm_char_hat_shown = 0;
	bm_hat_sent = -1;
	bm_char_legs = world;
	bm_char_cur_mdl = "";
	bm_char_cur_legs = "";
};

void() BM_Char_Shutdown =
{
	if (bm_char_hat)
	{
		remove(bm_char_hat);
		bm_char_hat = world;
		bm_char_hat_shown = 0;
	}
	if (bm_char_ent)
	{
		remove(bm_char_ent);
		bm_char_ent = world;
	}
	if (bm_char_legs)
	{
		remove(bm_char_legs);
		bm_char_legs = world;
	}
	if (bm_char_cur_mdl != "")
	{
		strunzone(bm_char_cur_mdl);
		bm_char_cur_mdl = "";
	}
	if (bm_char_cur_legs != "")
	{
		strunzone(bm_char_cur_legs);
		bm_char_cur_legs = "";
	}
};

void(entity ent, float pose) BM_Char_UpdatePose =
{
	local float f0, cnt, fps, tphase, idx, nidx;

	if (pose == 1)
	{
		// Run cycle (rockrun1..6)
		f0 = 6;
		cnt = 6;
		fps = 12;
	}
	else if (pose == 2)
	{
		// Attack cycle (shotatt1..6)
		f0 = 113;
		cnt = 6;
		fps = 9;
	}
	else
	{
		// Idle stand breathing (stand1..5)
		f0 = 12;
		cnt = 5;
		fps = 6;
	}

	tphase = time * fps;
	idx = floor(tphase);
	ent.lerpfrac = tphase - idx;
	idx = idx - cnt * floor(idx / cnt);
	nidx = idx + 1;
	if (nidx >= cnt)
		nidx = 0;

	ent.frame = f0 + idx;
	ent.frame2 = f0 + nidx;
};

float BM_CHAR_VF_FOV = 8;

vector bm_char_base;		// the preview player's origin
vector bm_char_fwd;			// flat direction from the camera to the preview
float bm_char_reach;		// how far ahead of the player the preview stands

// Pick a spot on the floor a little way ahead of the local player.
void() BM_Char_Anchor =
{
	local vector eye, ahead, pos;

	eye = getentityvec (player_localentnum, E_ORIGIN);
	makevectors (view_angles_y * '0 1 0');
	bm_char_fwd = v_forward;
	ahead = eye + '0 0 20';
	traceline (ahead, ahead + bm_char_fwd * 280, TRUE, world);
	bm_char_reach = bound (80, vlen (trace_endpos - ahead) - 24, 240);
	pos = eye + bm_char_fwd * bm_char_reach;
	traceline (pos + '0 0 40', pos - '0 0 400', TRUE, world);
	if (trace_fraction < 1)
		pos_z = trace_endpos_z + 24;
	bm_char_base = pos;
	bm_char_anchored = TRUE;
};

// Add the preview player (and hat) to the view that is about to be rendered, and point the camera at it.
// This deliberately uses the game's normal scene: a separate render of its own crashed the engine.
void() BM_Char_AddToView =
{
	local float vp_x, vp_y, vp_w, vp_h, yaw, pitch, zoom, dist, pose;
	local float packed, top_c, bot_c, cmap, cw, ch, hat, extra, f1, f2, lf;
	local float tan_x, tan_y, ndc_x, ndc_y, turn;
	local vector fov, target, cam_org, cam_ang, right, ofs, hmax, shift;
	local string body_mdl, legs_mdl;

	cw = cvar("vid_conwidth");
	ch = cvar("vid_conheight");
	vp_x = cvar("bm_char_vp_x");
	vp_y = cvar("bm_char_vp_y");
	vp_w = cvar("bm_char_vp_w");
	vp_h = cvar("bm_char_vp_h");
	if (cw <= 0 || ch <= 0 || vp_w < 64 || vp_h < 64)
		return;
	if (!bm_char_anchored)
		BM_Char_Anchor();

	yaw = cvar("bm_char_yaw");
	pitch = bound(-4, cvar("bm_char_pitch"), 42);
	zoom = bound(0.62, cvar("bm_char_zoom"), 1.55);
	pose = floor(cvar("bm_char_pose"));

	packed = floor(cvar("_cl_color"));
	top_c = bound(0, floor(packed / 16), 13);
	bot_c = bound(0, packed - top_c * 16, 13);
	cmap = 1024 + top_c * 16 + bot_c;

	body_mdl = BM_Char_ResolveBodyModel();
	if (!bm_char_ent)
		bm_char_ent = spawn();
	if (bm_char_cur_mdl != body_mdl)
	{
		if (bm_char_cur_mdl != "")
			strunzone(bm_char_cur_mdl);
		precache_model(body_mdl);
		setmodel(bm_char_ent, body_mdl);
		bm_char_cur_mdl = strzone(body_mdl);
	}

	// the model turns on the spot; the camera only tilts and zooms
	turn = vectoyaw(bm_char_fwd * -1) + yaw;
	setorigin(bm_char_ent, bm_char_base);
	bm_char_ent.angles = turn * '0 1 0';
	bm_char_ent.colormap = cmap;
	BM_Char_UpdatePose(bm_char_ent, pose);

	if (body_mdl == "progs/player_torso.mdl")
	{
		legs_mdl = "progs/player_low.mdl";
		if (!bm_char_legs)
			bm_char_legs = spawn();
		if (bm_char_cur_legs != legs_mdl)
		{
			if (bm_char_cur_legs != "")
				strunzone(bm_char_cur_legs);
			precache_model(legs_mdl);
			setmodel(bm_char_legs, legs_mdl);
			bm_char_cur_legs = strzone(legs_mdl);
		}
		setorigin(bm_char_legs, bm_char_base);
		bm_char_legs.angles = turn * '0 1 0';
		bm_char_legs.colormap = cmap;
		BM_Char_UpdatePose(bm_char_legs, pose);
	}

	// The picked hat, on the head socket of the pose being shown
	hat = bound (0, floor (cvar ("bm_hat")), BM_HAT_COUNT);
	if (body_mdl != "progs/player_id1.mdl")
		hat = 0;		// the head table is for the classic model only
	extra = 0;
	if (hat)
	{
		if (!bm_char_hat)
			bm_char_hat = spawn ();
		if (bm_char_hat_shown != hat)
		{
			precache_model (BM_HatModel (hat));
			setmodel (bm_char_hat, BM_HatModel (hat));
			bm_char_hat_shown = hat;
		}
		f1 = bm_char_ent.frame;
		f2 = bm_char_ent.frame2;
		lf = bm_char_ent.lerpfrac;
		ofs = BM_HatTagPos (f1) * (1 - lf) + BM_HatTagPos (f2) * lf;
		makevectors (bm_char_ent.angles);
		setorigin (bm_char_hat, bm_char_base + v_forward * ofs_x - v_right * ofs_y + '0 0 1' * ofs_z);
		bm_char_hat.angles = BM_HatTagAng (f1) + turn * '0 1 0';
		bm_char_hat.frame = BM_HatAnimFrame (hat, time);
		hmax = bm_char_hat.maxs;
		extra = max (0, hmax_z - 8);		// make room for tall hats
	}

	// Frame the model (feet to hat) inside the editor's preview rectangle, which sits left of the screen centre
	fov = getpropertyvec(BM_CHAR_VF_FOV);
	tan_x = sin(fov_x * 0.00872665) / cos(fov_x * 0.00872665);
	tan_y = sin(fov_y * 0.00872665) / cos(fov_y * 0.00872665);
	dist = (64 + extra) / (2 * tan_y * 0.78 * (vp_h / ch));
	dist = min(dist * zoom, bm_char_reach - 20);

	target = bm_char_base + '0 0 1' * (4 + extra * 0.5);
	if (zoom < 0.85)
		target_z = target_z + (0.85 - zoom) * 40;
	cam_org = target - bm_char_fwd * (dist * cos(pitch * 0.01745329)) + '0 0 1' * (dist * sin(pitch * 0.01745329));

	makevectors(vectoyaw(bm_char_fwd) * '0 1 0');
	right = v_right;
	ndc_x = ((vp_x + vp_w * 0.5) / cw) * 2 - 1;
	ndc_y = 1 - ((vp_y + vp_h * 0.5) / ch) * 2;
	shift = right * (0 - ndc_x * dist * tan_x) + '0 0 1' * (0 - ndc_y * dist * tan_y);
	cam_org = cam_org + shift;
	target = target + shift;

	cam_ang = vectoangles(target - cam_org);
	cam_ang_x = 0 - cam_ang_x;		// view angles pitch the other way round
	if (cam_ang_x < -180)
		cam_ang_x = cam_ang_x + 360;

	setproperty(VF_ORIGIN, cam_org);
	setproperty(VF_ANGLES, cam_ang);
	setproperty(VF_DRAWCROSSHAIR, FALSE);
	setproperty(VF_DRAWENGINESBAR, FALSE);
	adddynamiclight(cam_org + right * 30 + '0 0 30', dist + 120, '0.9 0.8 0.65');

	addentity(bm_char_ent);
	if (body_mdl == "progs/player_torso.mdl" && bm_char_legs)
		addentity(bm_char_legs);
	if (hat)
		addentity(bm_char_hat);
};
