// BakersfieldQuake CSQC - 3D Character Customizer Studio Renderer
// Modular viewport renderer driven by MenuQC cvars (bm_char_* + _cl_color).

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
	registercvar("bm_char_yaw", "152");
	registercvar("bm_char_pitch", "8");
	registercvar("bm_char_zoom", "1.0");
	registercvar("bm_char_spin", "1");
	registercvar("bm_char_pose", "0");
	registercvar("bm_char_model", "0");
	registercvar("bm_hat", "0");

	precache_model("progs/player_id1.mdl");
	precache_model("progs/player_torso.mdl");
	precache_model("progs/player_low.mdl");

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

// Emit a double-sided quad so studio geometry never vanishes under default backface culling
void(vector p0, vector p1, vector p2, vector p3, vector c0, vector c1, vector c2, vector c3, float a) BM_Char_Quad =
{
	R_BeginPolygon("", 0, FALSE);
	R_PolygonVertex(p0, '0 0 0', c0, a);
	R_PolygonVertex(p1, '1 0 0', c1, a);
	R_PolygonVertex(p2, '1 1 0', c2, a);
	R_PolygonVertex(p3, '0 1 0', c3, a);
	R_EndPolygon();

	R_BeginPolygon("", 0, FALSE);
	R_PolygonVertex(p3, '0 1 0', c3, a);
	R_PolygonVertex(p2, '1 1 0', c2, a);
	R_PolygonVertex(p1, '1 0 0', c1, a);
	R_PolygonVertex(p0, '0 0 0', c0, a);
	R_EndPolygon();
};

void(vector p0, vector p1, vector p2, vector c0, vector c1, vector c2, float a) BM_Char_Tri =
{
	R_BeginPolygon("", 0, FALSE);
	R_PolygonVertex(p0, '0 0 0', c0, a);
	R_PolygonVertex(p1, '1 0 0', c1, a);
	R_PolygonVertex(p2, '0.5 1 0', c2, a);
	R_EndPolygon();

	R_BeginPolygon("", 0, FALSE);
	R_PolygonVertex(p2, '0.5 1 0', c2, a);
	R_PolygonVertex(p1, '1 0 0', c1, a);
	R_PolygonVertex(p0, '0 0 0', c0, a);
	R_EndPolygon();
};

void(vector cam_org, vector cam_fwd, vector cam_right, vector cam_up, float top_c) BM_Char_DrawStage =
{
	local vector bg_c, tl, tr, br, bl, c_top, c_bot;
	local float segs, i, a0, a1, r_in, r_out, r_rim, z_top, z_bot;
	local vector p0, p1, q0, q1, d0, d1, center_pt, col_in, col_out, col_rim;

	// 1. Far studio backdrop gradient plane facing the camera
	bg_c = cam_org + cam_fwd * 420;
	tl = bg_c - cam_right * 460 + cam_up * 320;
	tr = bg_c + cam_right * 460 + cam_up * 320;
	br = bg_c + cam_right * 460 - cam_up * 320;
	bl = bg_c - cam_right * 460 - cam_up * 320;
	c_top = '0.03 0.035 0.055';
	c_bot = '0.09 0.055 0.04';
	BM_Char_Quad(tl, tr, br, bl, c_top, c_top, c_bot, c_bot, 1.0);

	// 2. Sculpted 16-sided studio pedestal under character feet (z = -24.5)
	segs = 16;
	r_in = 17;
	r_out = 26;
	r_rim = 28;
	z_top = -24.5;
	z_bot = -31.0;
	center_pt = '0 0 -24.5';
	col_in = '0.20 0.14 0.10';
	col_out = '0.09 0.07 0.06';
	col_rim = '0.92 0.62 0.18';

	for (i = 0; i < segs; i = i + 1)
	{
		a0 = (i / segs) * 360;
		a1 = ((i + 1) / segs) * 360;

		p0 = BM_Char_CosDeg(a0) * r_in * '1 0 0' + BM_Char_SinDeg(a0) * r_in * '0 1 0' + z_top * '0 0 1';
		p1 = BM_Char_CosDeg(a1) * r_in * '1 0 0' + BM_Char_SinDeg(a1) * r_in * '0 1 0' + z_top * '0 0 1';
		q0 = BM_Char_CosDeg(a0) * r_out * '1 0 0' + BM_Char_SinDeg(a0) * r_out * '0 1 0' + z_top * '0 0 1';
		q1 = BM_Char_CosDeg(a1) * r_out * '1 0 0' + BM_Char_SinDeg(a1) * r_out * '0 1 0' + z_top * '0 0 1';
		d0 = BM_Char_CosDeg(a0) * r_rim * '1 0 0' + BM_Char_SinDeg(a0) * r_rim * '0 1 0' + z_bot * '0 0 1';
		d1 = BM_Char_CosDeg(a1) * r_rim * '1 0 0' + BM_Char_SinDeg(a1) * r_rim * '0 1 0' + z_bot * '0 0 1';

		// Inner disc & bevel ring
		BM_Char_Tri(center_pt, p0, p1, col_in, col_out, col_out, 1.0);
		BM_Char_Quad(p0, p1, q1, q0, col_out, col_out, col_rim * 0.55, col_rim * 0.55, 1.0);
		// Glowing gold side skirt
		BM_Char_Quad(q0, q1, d1, d0, col_rim * 0.72, col_rim * 0.72, '0.04 0.03 0.025', '0.04 0.03 0.025', 1.0);
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

void(float w, float h) BM_Char_Render =
{
	local float vp_x, vp_y, vp_w, vp_h, yaw, pitch, zoom, dist, pose;
	local float packed, top_c, bot_c, cmap, half_h, half_w, fovx, fovy;
	local float cw, ch;
	local vector target, cam_org, cam_ang, fov_ang, fwd, rgt, upv;
	local string body_mdl, legs_mdl;
	local float hat, extra, f1, f2, lf;
	local vector hmin, hmax;

	cw = cvar("vid_conwidth");
	ch = cvar("vid_conheight");
	if (cw <= 0) cw = w;
	if (ch <= 0) ch = h;
	if (cw <= 0 || ch <= 0)
		return;

	vp_x = cvar("bm_char_vp_x");
	vp_y = cvar("bm_char_vp_y");
	vp_w = cvar("bm_char_vp_w");
	vp_h = cvar("bm_char_vp_h");
	if (vp_w < 64 || vp_h < 64)
	{
		vp_x = 20;
		vp_y = 52;
		vp_w = floor(cw * 0.52);
		vp_h = ch - 72;
	}

	yaw = cvar("bm_char_yaw");
	pitch = bound(-26, cvar("bm_char_pitch"), 42);
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

	setorigin(bm_char_ent, '0 0 0');
	bm_char_ent.angles = '0 0 0';
	bm_char_ent.scale = 1.0;
	bm_char_ent.skin = 0;
	bm_char_ent.colormap = cmap;
	bm_char_ent.effects = BM_EF_NOSHADOW;
	BM_Char_UpdatePose(bm_char_ent, pose);

	// Optional Combat+ split legs when 3rd_person_visible_weapons is active
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
		setorigin(bm_char_legs, '0 0 0');
		bm_char_legs.angles = '0 0 0';
		bm_char_legs.scale = 1.0;
		bm_char_legs.skin = 0;
		bm_char_legs.colormap = cmap;
		bm_char_legs.effects = BM_EF_NOSHADOW;
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
		setorigin (bm_char_hat, BM_HatTagPos (f1) * (1 - lf) + BM_HatTagPos (f2) * lf);
		bm_char_hat.angles = BM_HatTagAng (f1);
		bm_char_hat.frame = BM_HatAnimFrame (hat, time);
		bm_char_hat.effects = BM_EF_NOSHADOW;
		hmin = bm_char_hat.mins;
		hmax = bm_char_hat.maxs;
		extra = max (0, hmax_z - 8);		// head top is about 26 up; make room for tall hats
	}

	// Orbit camera around character center ('0 0 3')
	target = '0 0 3';
	if (zoom < 0.85)
		target_z = 3 + (0.85 - zoom) * 28;	// smoothly tilt up toward helmet/chest on close-up zoom
	dist = (82 + extra * 1.5) * zoom;
	target_z = target_z + extra * 0.55;

	cam_org_x = target_x + dist * BM_Char_CosDeg(pitch) * BM_Char_CosDeg(yaw);
	cam_org_y = target_y + dist * BM_Char_CosDeg(pitch) * BM_Char_SinDeg(yaw);
	cam_org_z = target_z + dist * BM_Char_SinDeg(pitch);

	cam_ang = vectoangles(target - cam_org);
	makevectors(cam_ang);
	fwd = v_forward;
	rgt = v_right;
	upv = v_up;

	fovy = 44;
	half_h = 0.404026;
	half_w = half_h * (vp_w / vp_h);
	fov_ang = vectoangles('1 0 0' + '0 1 0' * half_w);
	if (fov_ang_y > 180)
		fov_ang_y = fov_ang_y - 360;
	fovx = fabs(fov_ang_y) * 2;

	clearscene();
	setproperty(BM_VF_MIN, vp_x * '1 0 0' + vp_y * '0 1 0');
	setproperty(BM_VF_SIZE, vp_w * '1 0 0' + vp_h * '0 1 0');
	setproperty(BM_VF_FOV, fovx * '1 0 0' + fovy * '0 1 0');
	setproperty(BM_VF_ORIGIN, cam_org);
	setproperty(BM_VF_ANGLES, cam_ang);
	setproperty(BM_VF_DRAWWORLD, FALSE);
	setproperty(BM_VF_DRAWENGINESBAR, FALSE);
	setproperty(BM_VF_DRAWCROSSHAIR, FALSE);

	// 3-point studio lighting: warm front key, cool rear rim, soft bounce fill
	adddynamiclight(cam_org + rgt * 54 + upv * 38, 290, '1.35 1.18 0.96');
	adddynamiclight(target - fwd * 68 - rgt * 52 + upv * 44, 260, '0.45 0.76 1.28');
	adddynamiclight('0 0 -16', 110, '0.75 0.52 0.20');

	BM_Char_DrawStage(cam_org, fwd, rgt, upv, top_c);
	addentity(bm_char_ent);
	if (hat)
		addentity(bm_char_hat);
	if (body_mdl == "progs/player_torso.mdl" && bm_char_legs)
		addentity(bm_char_legs);
	renderscene();
};
