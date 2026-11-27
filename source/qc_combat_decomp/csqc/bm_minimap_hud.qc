/*
================
bm_minimap_hud.qc — Fully transparent live tactical minimap (bottom-left corner)

Features:
  - Fully transparent background (no dark opaque disc obscuring gameplay).
  - Live, accurate enemy coordinates and facing chevrons streamed from server.
  - Persistent directional guide arrow + nearest-enemy distance & direction indicator
    so you always know which way to move to find enemies.
  - Crisp height arrows (^ / v) and rim indicators for off-radar enemies.
================
*/

float	ENT_BM_RADAR		= 8;

float	BM_RPK_GUN			= 1;
float	BM_RPK_BLAST		= 2;
float	BM_RPK_KILL			= 3;
float	BM_RPK_MONSTER		= 4;

float	BM_MM_R				= 42;
float	BM_MM_PING_MAX		= 16;
float	BM_MM_PING_LIFE		= 2.2;
float	BM_MM_PU_MAX		= 36;
float	BM_MM_DEG2RAD		= 0.01745329;

float	BM_RPU_TRIPLE		= 1;
float	BM_RPU_FORELOCO		= 2;
float	BM_RPU_QUAD			= 3;
float	BM_RPU_PENT			= 4;
float	BM_RPU_TIME			= 5;
float	BM_RPU_SUIT			= 6;
float	BM_RPU_RING			= 7;

string	mm_cur_raw_map;
string	mm_cur_shader;
float	mm_has_pic;

float	mm_last_seq[4];
float	mm_p_next;
vector	mm_p_pos[16];
float	mm_p_kind[16];
float	mm_p_t[16];

float	mm_e_cnt;
float	mm_enemy_t;
vector	mm_e_pos[16];
float	mm_e_yaw[16];
float	mm_e_flg[16];

float	mm_a_cnt;
float	mm_ally_t;
vector	mm_a_pos[4];
float	mm_a_yaw[4];

float	mm_pu_cnt;
vector	mm_pu_pos[36];
float	mm_pu_kind[36];

float	mm_cx;
float	mm_cy;
float	mm_rad;
float	mm_alpha_cur;

float() MM_GetRadius =
{
	local float r;

	r = cvar ("bm_minimap_size");
	if (r <= 0)
		r = BM_MM_R;
	return bound (20, r, 72);
};

vector(float x, float y) MM_Vec2 =
{
	local vector v;

	v_x = x;
	v_y = y;
	v_z = 0;
	return v;
};

float(float x) MM_Sin =
{
	local float r;
	r = sin (x);
	return r;
};

float(float x) MM_Cos =
{
	local float r;
	r = cos (x);
	return r;
};

// Zircon drawline only renders segments where p1_y <= p0_y.
void(float wline, vector p0, vector p1, vector col, float a) MM_Line =
{
	if (a <= 0.01)
		return;
	if (p1_y > p0_y)
		drawline (wline, p1, p0, col, a, 0);
	else
		drawline (wline, p0, p1, col, a, 0);
};

void(string shd, vector p0, vector p1, vector p2, vector col, float a) MM_Tri2D =
{
	R_BeginPolygon (shd, 0, TRUE);
	R_PolygonVertex (p0, '0.5 0.5 0', col, a);
	R_PolygonVertex (p1, '0.5 0.5 0', col, a);
	R_PolygonVertex (p2, '0.5 0.5 0', col, a);
	R_EndPolygon ();
};

float mm_uc_ready;
float mm_uc_x[25];
float mm_uc_y[25];
float mm_base_precached;

void() MM_InitUnitCircle =
{
	local float i, ang;

	if (mm_uc_ready)
		return;
	mm_uc_ready = TRUE;
	i = 0;
	while (i <= 24)
	{
		ang = i * (6.2831853 / 24);
		mm_uc_x[i] = cos (ang);
		mm_uc_y[i] = sin (ang);
		i = i + 1;
	}
};

void(float cx, float cy, float rad, float segs, vector col, float a) MM_FillCircle =
{
	local float i, a0, step;
	local vector p;

	if (rad <= 0.5 || a <= 0.01)
		return;
	p_z = 0;
	if (segs == 32 || segs == 24)
	{
		MM_InitUnitCircle ();
		R_BeginPolygon ("gfx/minimap/white", 0, TRUE);
		p_x = cx;
		p_y = cy;
		R_PolygonVertex (p, '0.5 0.5 0', col, a);
		i = 0;
		while (i <= 24)
		{
			p_x = cx + mm_uc_x[i] * rad;
			p_y = cy + mm_uc_y[i] * rad;
			R_PolygonVertex (p, '0.5 0.5 0', col, a);
			i = i + 1;
		}
		R_EndPolygon ();
		return;
	}
	step = 6.2831853 / segs;
	R_BeginPolygon ("gfx/minimap/white", 0, TRUE);
	p_x = cx;
	p_y = cy;
	R_PolygonVertex (p, '0.5 0.5 0', col, a);
	i = 0;
	while (i <= segs)
	{
		a0 = i * step;
		p_x = cx + cos (a0) * rad;
		p_y = cy + sin (a0) * rad;
		R_PolygonVertex (p, '0.5 0.5 0', col, a);
		i = i + 1;
	}
	R_EndPolygon ();
};

void(float cx, float cy, float rad, float segs, float wline, vector col, float a) MM_Ring =
{
	local float i, a0, a1, step;
	local vector p0, p1;

	if (rad <= 0.5 || segs < 4 || a <= 0.01)
		return;
	step = 6.2831853 / segs;
	i = 0;
	while (i < segs)
	{
		a0 = i * step;
		a1 = (i + 1) * step;
		p0 = MM_Vec2 (cx + MM_Cos (a0) * rad, cy + MM_Sin (a0) * rad);
		p1 = MM_Vec2 (cx + MM_Cos (a1) * rad, cy + MM_Sin (a1) * rad);
		MM_Line (wline, p0, p1, col, a);
		i = i + 1;
	}
};

// Draw a filled arrow chevron with crisp dark outline. screen_deg = 0 points straight UP.
void(float cx, float cy, float screen_deg, float sz, vector col, float a) MM_Chevron =
{
	local float rad, fx, fy, rx, ry;
	local vector tip, wl, wr, notch, c_p, c_wl, c_wr, c_n;

	if (a <= 0.01)
		return;
	rad = screen_deg * BM_MM_DEG2RAD;
	// Screen UP is (0, -1); rotating clockwise by -screen_deg (since Quake yaw is CCW)
	fx = 0 - MM_Sin (rad);
	fy = 0 - MM_Cos (rad);
	rx = 0 - fy;
	ry = fx;

	// Dark outline slightly larger behind arrow
	c_p  = MM_Vec2 (cx + fx * (sz + 1.1), cy + fy * (sz + 1.1));
	c_wl = MM_Vec2 (cx - fx * (sz * 0.85 + 0.8) - rx * (sz * 0.85 + 1.0), cy - fy * (sz * 0.85 + 0.8) - ry * (sz * 0.85 + 1.0));
	c_wr = MM_Vec2 (cx - fx * (sz * 0.85 + 0.8) + rx * (sz * 0.85 + 1.0), cy - fy * (sz * 0.85 + 0.8) + ry * (sz * 0.85 + 1.0));
	c_n  = MM_Vec2 (cx - fx * (sz * 0.20), cy - fy * (sz * 0.20));
	MM_Tri2D ("gfx/minimap/white", c_p, c_wl, c_n, '0 0 0', 0.92 * a);
	MM_Tri2D ("gfx/minimap/white", c_p, c_n, c_wr, '0 0 0', 0.92 * a);

	tip   = MM_Vec2 (cx + fx * sz, cy + fy * sz);
	wl    = MM_Vec2 (cx - fx * (sz * 0.75) - rx * (sz * 0.76), cy - fy * (sz * 0.75) - ry * (sz * 0.76));
	wr    = MM_Vec2 (cx - fx * (sz * 0.75) + rx * (sz * 0.76), cy - fy * (sz * 0.75) + ry * (sz * 0.76));
	notch = MM_Vec2 (cx - fx * (sz * 0.28), cy - fy * (sz * 0.28));
	MM_Tri2D ("gfx/minimap/white", tip, wl, notch, col, a);
	MM_Tri2D ("gfx/minimap/white", tip, notch, wr, col, a);
};

void(float cx, float cy, float dz, vector col, float a) MM_HeightArrow =
{
	if (a <= 0.02)
		return;
	if (dz > 96)
	{
		MM_Line (1.2, MM_Vec2 (cx - 2.2, cy - 3.6), MM_Vec2 (cx, cy - 5.8), '0 0 0', 0.85 * a);
		MM_Line (1.2, MM_Vec2 (cx + 2.2, cy - 3.6), MM_Vec2 (cx, cy - 5.8), '0 0 0', 0.85 * a);
		MM_Line (1.0, MM_Vec2 (cx - 2.0, cy - 3.6), MM_Vec2 (cx, cy - 5.6), col, a);
		MM_Line (1.0, MM_Vec2 (cx + 2.0, cy - 3.6), MM_Vec2 (cx, cy - 5.6), col, a);
	}
	else if (dz < -96)
	{
		MM_Line (1.2, MM_Vec2 (cx - 2.2, cy + 3.6), MM_Vec2 (cx, cy + 5.8), '0 0 0', 0.85 * a);
		MM_Line (1.2, MM_Vec2 (cx + 2.2, cy + 3.6), MM_Vec2 (cx, cy + 5.8), '0 0 0', 0.85 * a);
		MM_Line (1.0, MM_Vec2 (cx - 2.0, cy + 3.6), MM_Vec2 (cx, cy + 5.6), col, a);
		MM_Line (1.0, MM_Vec2 (cx + 2.0, cy + 3.6), MM_Vec2 (cx, cy + 5.6), col, a);
	}
};

void(float cx, float cy, float rad, float sx, float sy, float sz, vector col, float a) MM_RimBlip =
{
	local float d, ux, uy, rx, ry, bx, by;
	local vector tip, b1, b2, o_tip, o_b1, o_b2;

	if (a <= 0.02)
		return;
	d = sqrt (sx * sx + sy * sy);
	if (d <= 0.001)
		return;
	ux = sx / d;
	uy = sy / d;
	rx = 0 - uy;
	ry = ux;

	bx = cx + ux * (rad - 1.0);
	by = cy + uy * (rad - 1.0);
	o_tip = MM_Vec2 (bx + ux * (sz + 1.0), by + uy * (sz + 1.0));
	o_b1  = MM_Vec2 (bx - ux * (sz * 0.85 + 0.6) - rx * (sz * 1.05 + 0.8), by - uy * (sz * 0.85 + 0.6) - ry * (sz * 1.05 + 0.8));
	o_b2  = MM_Vec2 (bx - ux * (sz * 0.85 + 0.6) + rx * (sz * 1.05 + 0.8), by - uy * (sz * 0.85 + 0.6) + ry * (sz * 1.05 + 0.8));
	MM_Tri2D ("gfx/minimap/white", o_tip, o_b1, o_b2, '0 0 0', 0.90 * a);

	tip = MM_Vec2 (bx + ux * sz, by + uy * sz);
	b1  = MM_Vec2 (bx - ux * (sz * 0.85) - rx * (sz * 1.0), by - uy * (sz * 0.85) - ry * (sz * 1.0));
	b2  = MM_Vec2 (bx - ux * (sz * 0.85) + rx * (sz * 1.0), by - uy * (sz * 0.85) + ry * (sz * 1.0));
	MM_Tri2D ("gfx/minimap/white", tip, b1, b2, col, a);
};

void(float seq, float kind, vector org) MM_RecordPing =
{
	local float idx;

	idx = mm_p_next;
	mm_p_pos[idx] = org;
	mm_p_kind[idx] = kind;
	mm_p_t[idx] = time;
	idx = idx + 1;
	if (idx >= BM_MM_PING_MAX)
		idx = 0;
	mm_p_next = idx;
};

void(float isnew) BM_Radar_EntUpdate =
{
	local float flags, i, seq, kind, ecnt, acnt, pucnt, pyaw;
	local vector org;

	self.drawmask = 0;
	flags = ReadByte ();

	if (flags & 1)
	{
		i = 0;
		while (i < 4)
		{
			seq = ReadByte ();
			kind = ReadByte ();
			org_x = ReadCoord ();
			org_y = ReadCoord ();
			org_z = ReadCoord ();
			if (seq > 0 && seq != mm_last_seq[i])
			{
				mm_last_seq[i] = seq;
				if (!isnew || i == 0)
					MM_RecordPing (seq, kind, org);
			}
			i = i + 1;
		}
	}

	if (flags & 2)
	{
		ecnt = ReadByte ();
		if (ecnt > 16)
			ecnt = 16;
		i = 0;
		while (i < ecnt)
		{
			org_x = ReadCoord ();
			org_y = ReadCoord ();
			org_z = ReadCoord ();
			pyaw = ReadByte ();
			mm_e_pos[i] = org;
			mm_e_yaw[i] = pyaw * (360 / 255);
			mm_e_flg[i] = ReadByte ();
			i = i + 1;
		}
		mm_e_cnt = ecnt;
		mm_enemy_t = time;
	}

	if (flags & 4)
	{
		acnt = ReadByte ();
		if (acnt > 4)
			acnt = 4;
		i = 0;
		while (i < acnt)
		{
			org_x = ReadCoord ();
			org_y = ReadCoord ();
			org_z = ReadCoord ();
			pyaw = ReadByte ();
			mm_a_pos[i] = org;
			mm_a_yaw[i] = pyaw * (360 / 255);
			i = i + 1;
		}
		mm_a_cnt = acnt;
		mm_ally_t = time;
	}

	if (flags & 8)
	{
		pucnt = ReadByte ();
		if (pucnt > BM_MM_PU_MAX)
			pucnt = BM_MM_PU_MAX;
		i = 0;
		while (i < pucnt)
		{
			mm_pu_kind[i] = ReadByte ();
			org_x = ReadCoord ();
			org_y = ReadCoord ();
			org_z = ReadCoord ();
			mm_pu_pos[i] = org;
			i = i + 1;
		}
		mm_pu_cnt = pucnt;
	}
};

void() BM_Radar_EntRemove =
{
	local float i;

	mm_e_cnt = 0;
	mm_a_cnt = 0;
	mm_pu_cnt = 0;
	i = 0;
	while (i < 4)
	{
		mm_last_seq[i] = 0;
		i = i + 1;
	}
	remove (self);
};

string(string raw) MM_NormMapName =
{
	local string s;
	local float len;

	s = strtolower (raw);
	if (substring (s, 0, 5) == "maps/")
		s = substring (s, 5, strlen (s) - 5);
	len = strlen (s);
	if (len > 4 && substring (s, len - 4, 4) == ".bsp")
		s = substring (s, 0, len - 4);
	return s;
};

float(string m) MM_LoadFallbackBounds =
{
	local float fh, n;
	local string line;

	fh = fopen (strcat ("gfx/minimap/", m, ".txt"), FILE_READ);
	if (fh < 0)
		return FALSE;
	line = fgets (fh);
	fclose (fh);
	if (line == "")
		return FALSE;
	n = tokenize (line);
	if (n < 3)
		return FALSE;
	mm_map_cx = stof (argv (0));
	mm_map_cy = stof (argv (1));
	mm_map_half = stof (argv (2));
	return (mm_map_half > 0);
};

void() MM_EnsureMap =
{
	local string m, shd, png;
	local vector sz;

	if (!mm_base_precached)
	{
		mm_base_precached = TRUE;
		precache_pic ("gfx/minimap/white");
		precache_pic ("gfx/minimap/heat");
		precache_pic ("gfx/minimap/rim");
	}

	if (mapname == "")
		return;
	if (mm_cur_raw_map == mapname)
		return;

	if (mm_cur_raw_map != "")
		strunzone (mm_cur_raw_map);
	mm_cur_raw_map = strzone (mapname);

	if (mm_cur_shader != "")
	{
		strunzone (mm_cur_shader);
		mm_cur_shader = "";
	}
	mm_has_pic = FALSE;

	m = MM_NormMapName (mapname);
	if (m == "")
		return;

	if (!BM_MinimapLookupBounds (m))
	{
		if (!MM_LoadFallbackBounds (m))
			return;
	}

	png = strcat ("gfx/minimap/", m, ".png");
	shd = strcat ("gfx/minimap/", m);
	precache_pic (png);
	precache_pic (shd);
	sz = drawgetimagesize (png);
	if (sz_x > 0 && sz_y > 0)
	{
		mm_cur_shader = strzone (shd);
		mm_has_pic = TRUE;
	}
};

float() BM_MinimapIsVisible =
{
	local float intro, fd;

	if (cvar ("bm_minimap") <= 0)
		return FALSE;
	if (inMenu || intermission || finale || showscores)
		return FALSE;
	intro = getstati (BMST_INTRO);
	if (intro > 0 || cvar ("bm_menu_bg") > 0)
		return FALSE;
	fd = getstati (BMST_FD_MODE);
	if (fd > 0)
		return FALSE;
	if (player_health <= 0)
		return FALSE;
	return TRUE;
};

void(float w, float h) MM_ComputeLayout =
{
	local float hs, jb, sl, x_left, x_ofs, y_ofs, base, rad;

	rad = MM_GetRadius ();
	mm_rad = rad;

	x_ofs = bound (0, cvar ("bm_minimap_x"), w * 0.45);
	y_ofs = bound (0, cvar ("bm_minimap_y"), h * 0.45);
	x_left = JP_IsVisible () ? max (34, x_ofs) : x_ofs;
	mm_cx = x_left + rad;
	hs = cvar ("bm_hud_style");
	jb = getstati (93);
	sl = getstati (BMST_SLOT);

	if (jb == 2)
	{
		base = BM_CornerBottomY (h) - 32 - max (0, y_ofs - 8);
		mm_cy = base - rad;
	}
	else if (hs == 2 || hs == 3)
	{
		// Clear the bottom-left Route 99 / Cyberpop card (h - 66 .. h - 14)
		mm_cy = h - 70 - rad - max (0, y_ofs - 8);
	}
	else if (hs == 1 && (x_left + rad * 2 + 4) > (w * 0.5 - 156))
	{
		// Narrow aspect (4:3 / 16:10): step cleanly above Style 1 bottom island pill
		mm_cy = h - 62 - rad - max (0, y_ofs - 8);
	}
	else if (hs == 4 && (x_left + rad * 2 + 4) > (w * 0.5 - 138))
	{
		// Narrow aspect (4:3 / 16:10): step cleanly above Style 4 bottom vitals bar
		mm_cy = h - 54 - rad - max (0, y_ofs - 8);
	}
	else if (hs == 0 && (sl == 16 || sl == 18) && (x_left + rad * 2) > (w * 0.5 - 222) && y_ofs < 46)
	{
		// Classic HUD with both Jetpack + M4/Garand tile active: step cleanly above the tile
		mm_cy = h - 46 - rad;
	}
	else
	{
		// Bottom-left corner (styles 0, 1, 4)
		mm_cy = h - y_ofs - rad;
	}
};

float(float w, float h) BM_MinimapTopY =
{
	if (!BM_MinimapIsVisible ())
		return 0;
	MM_ComputeLayout (w, h);
	return mm_cy - mm_rad - 22;
};

// Transparent tactical backdrop: no dark opaque disc unless user raises bm_minimap_bg_alpha / bm_minimap_map_alpha
void(float cx, float cy, float rad, float range, vector porg, float yaw_deg, float alpha_mul, float bg_alpha, float map_alpha) MM_DrawTransparentRadar =
{
	local float span, yrad, fwd_x, fwd_y, right_x, right_y, inv_span, r_in, k_uv;
	local float uc, vc, i, ux, uy, sx, sy, wx, wy, base_x, base_y;
	local vector p, uv;

	if (bg_alpha > 0.01)
		MM_FillCircle (cx, cy, rad - 0.5, 24, '0.03 0.04 0.05', bg_alpha * alpha_mul);

	if (map_alpha > 0.01 && mm_has_pic && mm_map_half > 0)
	{
		MM_InitUnitCircle ();
		span = 2 * mm_map_half;
		inv_span = 1.0 / span;
		yrad = yaw_deg * BM_MM_DEG2RAD;
		fwd_x = cos (yrad);
		fwd_y = sin (yrad);
		right_x = fwd_y;
		right_y = 0 - fwd_x;

		base_x = mm_map_cx - mm_map_half;
		base_y = mm_map_cy + mm_map_half;
		uc = (porg_x - base_x) * inv_span;
		vc = (base_y - porg_y) * inv_span;
		r_in = rad - 1.0;
		k_uv = (r_in / rad) * range;

		p_z = 0;
		uv_z = 0;
		R_BeginPolygon (mm_cur_shader, 0, TRUE);
		p_x = cx; p_y = cy;
		uv_x = uc; uv_y = vc;
		R_PolygonVertex (p, uv, '1 1 1', map_alpha * alpha_mul);
		i = 0;
		while (i <= 24)
		{
			ux = mm_uc_x[i];
			uy = mm_uc_y[i];
			sx = ux * r_in;
			sy = uy * r_in;
			wx = porg_x + (ux * right_x - uy * fwd_x) * k_uv;
			wy = porg_y + (ux * right_y - uy * fwd_y) * k_uv;
			p_x = cx + sx;
			p_y = cy + sy;
			uv_x = (wx - base_x) * inv_span;
			uv_y = (base_y - wy) * inv_span;
			R_PolygonVertex (p, uv, '1 1 1', map_alpha * alpha_mul);
			i = i + 1;
		}
		R_EndPolygon ();
	}

	// Crisp transparent-friendly radar reference rings & crosshairs
	MM_Ring (cx, cy, rad * 0.50, 24, 0.8, '0.75 0.85 0.95', 0.20 * alpha_mul);
	MM_Ring (cx, cy, rad - 0.5, 24, 1.1, '0.85 0.92 1.0', 0.52 * alpha_mul);
	MM_Line (0.7, MM_Vec2 (cx - rad * 0.85, cy), MM_Vec2 (cx + rad * 0.85, cy), '0.75 0.85 0.95', 0.14 * alpha_mul);
	MM_Line (0.7, MM_Vec2 (cx, cy - rad * 0.85), MM_Vec2 (cx, cy + rad * 0.85), '0.75 0.85 0.95', 0.14 * alpha_mul);
};

vector(float kind) MM_PowerupColor =
{
	if (kind == BM_RPU_TRIPLE)		return '0.22 1.0 0.58';		// electric mint green
	if (kind == BM_RPU_FORELOCO)	return '1.0 0.34 0.82';		// watermelon magenta
	if (kind == BM_RPU_QUAD)		return '0.34 0.68 1.0';		// electric quad blue
	if (kind == BM_RPU_PENT)		return '1.0 0.90 0.45';		// gold pentagram
	if (kind == BM_RPU_TIME)		return '0.76 0.44 1.0';		// violet time rune
	if (kind == BM_RPU_SUIT)		return '0.60 0.96 0.28';		// lime biosuit
	return '0.86 0.90 0.96';
};

void(float cx, float cy, float r, vector col, float a) MM_Diamond =
{
	local float ro;
	local vector p0, p1, p2, p3;

	if (r <= 0.4 || a <= 0.01)
		return;
	ro = r + 0.9;
	p0 = MM_Vec2 (cx, cy - ro);
	p1 = MM_Vec2 (cx + ro, cy);
	p2 = MM_Vec2 (cx, cy + ro);
	p3 = MM_Vec2 (cx - ro, cy);
	R_BeginPolygon ("gfx/minimap/white", 0, TRUE);
	R_PolygonVertex (p0, '0.5 0.5 0', '0 0 0', 0.85 * a);
	R_PolygonVertex (p1, '0.5 0.5 0', '0 0 0', 0.85 * a);
	R_PolygonVertex (p2, '0.5 0.5 0', '0 0 0', 0.85 * a);
	R_PolygonVertex (p3, '0.5 0.5 0', '0 0 0', 0.85 * a);
	R_EndPolygon ();

	p0 = MM_Vec2 (cx, cy - r);
	p1 = MM_Vec2 (cx + r, cy);
	p2 = MM_Vec2 (cx, cy + r);
	p3 = MM_Vec2 (cx - r, cy);
	R_BeginPolygon ("gfx/minimap/white", 0, TRUE);
	R_PolygonVertex (p0, '0.5 0.5 0', col, a);
	R_PolygonVertex (p1, '0.5 0.5 0', col, a);
	R_PolygonVertex (p2, '0.5 0.5 0', col, a);
	R_PolygonVertex (p3, '0.5 0.5 0', col, a);
	R_EndPolygon ();
};

// Draw all active power-up markers + small directional rim arrows toward each power-up
void(float cx, float cy, float rad, float range, vector porg, float yaw_deg) MM_DrawPowerups =
{
	local float yrad, fwd_x, fwd_y, right_x, right_y, px_per_u, i, ox, oy, sx, sy, dist, wdist;
	local float best_i, best_d, pulse, is_best, arrow_sz, rim_a;
	local vector pu_org, col;

	if (cvar ("bm_minimap_powerups") <= 0 || mm_pu_cnt <= 0)
		return;

	yrad = yaw_deg * BM_MM_DEG2RAD;
	fwd_x = MM_Cos (yrad);
	fwd_y = MM_Sin (yrad);
	right_x = fwd_y;
	right_y = 0 - fwd_x;
	px_per_u = rad / range;

	best_i = -1;
	best_d = 9999999;
	i = 0;
	while (i < mm_pu_cnt)
	{
		pu_org = mm_pu_pos[i];
		ox = pu_org_x - porg_x;
		oy = pu_org_y - porg_y;
		wdist = sqrt (ox * ox + oy * oy);
		if (wdist < best_d)
		{
			best_d = wdist;
			best_i = i;
		}
		i = i + 1;
	}

	pulse = 0.78 + 0.22 * MM_Sin (time * 5.2);
	i = 0;
	while (i < mm_pu_cnt)
	{
		pu_org = mm_pu_pos[i];
		ox = pu_org_x - porg_x;
		oy = pu_org_y - porg_y;
		sx = (ox * right_x + oy * right_y) * px_per_u;
		sy = 0 - (ox * fwd_x + oy * fwd_y) * px_per_u;
		dist = sqrt (sx * sx + sy * sy);
		col = MM_PowerupColor (mm_pu_kind[i]);
		is_best = (i == best_i);

		if (dist <= rad - 4.0)
		{
			MM_Diamond (cx + sx, cy + sy, is_best ? 2.6 : 2.1, col, (is_best ? 0.98 * pulse : 0.92) * mm_alpha_cur);
			MM_HeightArrow (cx + sx, cy + sy, pu_org_z - porg_z, col, 0.88 * mm_alpha_cur);
		}
		if (dist > 4.0)
		{
			arrow_sz = is_best ? 2.5 : 1.85;
			rim_a = (dist <= rad - 4.0) ? 0.78 : 0.92;
			if (is_best)
				rim_a = 0.98 * pulse;
			MM_RimBlip (cx, cy, rad, sx, sy, arrow_sz, col, rim_a * mm_alpha_cur);
		}
		i = i + 1;
	}
};

// Draw all live enemies accurately + persistent directional guide toward nearest enemy
void(float cx, float cy, float rad, float range, vector porg, float yaw_deg) MM_DrawEnemies =
{
	local float yrad, fwd_x, fwd_y, right_x, right_y, px_per_u, i, ox, oy, sx, sy, dist, wdist;
	local float best_idx, best_d, best_sx, best_sy, best_dz, best_ang, pulse, gr, gx, gy;
	local vector eorg, col, gcol, lsc;
	local string lbl;

	if (mm_e_cnt <= 0)
	{
		local float sw_no;
		lsc = BM_UIScaleVec ('5.0 5.0 0');
		lbl = "NO ENEMIES";
		sw_no = stringwidth (lbl, FALSE, lsc);
		drawstring (MM_Vec2 (cx - sw_no * 0.5 + 0.6, cy - rad - 18.4), lbl, lsc, '0 0 0', 0.72 * mm_alpha_cur, 0);
		drawstring (MM_Vec2 (cx - sw_no * 0.5, cy - rad - 19.0), lbl, lsc, '0.72 0.78 0.85', 0.80 * mm_alpha_cur, 0);
		return;
	}

	yrad = yaw_deg * BM_MM_DEG2RAD;
	fwd_x = MM_Cos (yrad);
	fwd_y = MM_Sin (yrad);
	right_x = fwd_y;
	right_y = 0 - fwd_x;
	px_per_u = rad / range;

	best_idx = -1;
	best_d = 9999999;
	best_sx = 0;
	best_sy = 0;
	best_dz = 0;

	// First pass: find nearest enemy and draw guide vector beneath markers
	i = 0;
	while (i < mm_e_cnt)
	{
		eorg = mm_e_pos[i];
		ox = eorg_x - porg_x;
		oy = eorg_y - porg_y;
		wdist = sqrt (ox * ox + oy * oy);
		if (wdist < best_d)
		{
			best_d = wdist;
			best_idx = i;
			best_sx = (ox * right_x + oy * right_y) * px_per_u;
			best_sy = 0 - (ox * fwd_x + oy * fwd_y) * px_per_u;
			best_dz = eorg_z - porg_z;
		}
		i = i + 1;
	}

	// Draw directional guide line + pulsing beacon toward nearest enemy
	if (best_idx >= 0)
	{
		dist = sqrt (best_sx * best_sx + best_sy * best_sy);
		pulse = 0.75 + 0.25 * MM_Sin (time * 6.5);
		gcol = '1.0 0.72 0.16';
		if (dist > 2.0)
		{
			gr = min (dist, rad - 2.0);
			gx = cx + (best_sx / dist) * gr;
			gy = cy + (best_sy / dist) * gr;
			MM_Line (1.6, MM_Vec2 (cx, cy), MM_Vec2 (gx, gy), '0 0 0', 0.45 * mm_alpha_cur);
			MM_Line (1.0, MM_Vec2 (cx, cy), MM_Vec2 (gx, gy), gcol, 0.72 * pulse * mm_alpha_cur);

			// Prominent rim pointer arrow showing exact direction to move toward nearest enemy
			best_ang = atan2 (best_sx, 0 - best_sy) / BM_MM_DEG2RAD;
			MM_Chevron (cx + (best_sx / dist) * (rad + 1.5), cy + (best_sy / dist) * (rad + 1.5), best_ang, 4.2, gcol, 0.98 * pulse * mm_alpha_cur);
		}
	}

	// Second pass: draw all live enemy positions accurately
	i = 0;
	while (i < mm_e_cnt)
	{
		eorg = mm_e_pos[i];
		ox = eorg_x - porg_x;
		oy = eorg_y - porg_y;
		sx = (ox * right_x + oy * right_y) * px_per_u;
		sy = 0 - (ox * fwd_x + oy * fwd_y) * px_per_u;
		dist = sqrt (sx * sx + sy * sy);

		col = (i == best_idx) ? '1.0 0.20 0.14' : '1.0 0.34 0.26';
		if (mm_e_flg[i] & 4)
			col = '1.0 0.55 0.12';	// recently firing enemy highlighted bright orange-red

		if (dist <= rad - 3.5)
		{
			MM_Chevron (cx + sx, cy + sy, mm_e_yaw[i] - yaw_deg, (i == best_idx) ? 3.8 : 3.2, col, 0.98 * mm_alpha_cur);
			MM_HeightArrow (cx + sx, cy + sy, eorg_z - porg_z, col, 0.92 * mm_alpha_cur);
		}
		else
		{
			MM_RimBlip (cx, cy, rad, sx, sy, (i == best_idx) ? 3.0 : 2.3, col, 0.92 * mm_alpha_cur);
		}
		i = i + 1;
	}

	// Clean nearest-enemy bearing & distance label above the radar
	if (best_idx >= 0)
	{
		local string htag, dstr, dplain;
		local float meters, sw_en;

		meters = floor (best_d / 32 + 0.5);
		if (best_dz > 96)
			htag = " UP";
		else if (best_dz < -96)
			htag = " DN";
		else
			htag = "";
		dplain = strcat ("ENEMY ", ftos (meters), "m", htag);
		dstr = strcat ("^1ENEMY ^3", ftos (meters), "m^5", htag);
		lsc = BM_UIScaleVec ('5.0 5.0 0');
		sw_en = stringwidth (dplain, FALSE, lsc);
		drawstring (MM_Vec2 (cx - sw_en * 0.5 + 0.7, cy - rad - 18.3), dplain, lsc, '0 0 0', 0.90 * mm_alpha_cur, 0);
		drawcolorcodedstring (MM_Vec2 (cx - sw_en * 0.5, cy - rad - 19.0), dstr, lsc, 0.98 * mm_alpha_cur, 0);
	}
};

void(float cx, float cy, float rad, float range, vector porg, float yaw_deg) MM_DrawAllies =
{
	local float yrad, fwd_x, fwd_y, right_x, right_y, px_per_u, i, ox, oy, sx, sy, dist;
	local vector aorg, col;

	if (mm_a_cnt <= 0 || (time - mm_ally_t) > 1.5)
		return;

	yrad = yaw_deg * BM_MM_DEG2RAD;
	fwd_x = MM_Cos (yrad);
	fwd_y = MM_Sin (yrad);
	right_x = fwd_y;
	right_y = 0 - fwd_x;
	px_per_u = rad / range;
	col = '0.24 0.82 1.0';

	i = 0;
	while (i < mm_a_cnt)
	{
		aorg = mm_a_pos[i];
		ox = aorg_x - porg_x;
		oy = aorg_y - porg_y;
		sx = (ox * right_x + oy * right_y) * px_per_u;
		sy = 0 - (ox * fwd_x + oy * fwd_y) * px_per_u;
		dist = sqrt (sx * sx + sy * sy);
		if (dist <= rad - 4)
		{
			MM_Chevron (cx + sx, cy + sy, mm_a_yaw[i] - yaw_deg, 3.4, col, 0.98 * mm_alpha_cur);
			MM_HeightArrow (cx + sx, cy + sy, aorg_z - porg_z, col, 0.88 * mm_alpha_cur);
		}
		else
		{
			MM_RimBlip (cx, cy, rad, sx, sy, 2.4, col, 0.90 * mm_alpha_cur);
		}
		i = i + 1;
	}
};

void(float cx, float cy, float rad, float range, vector porg, float yaw_deg) MM_DrawLeader =
{
	local float lshow, yrad, fwd_x, fwd_y, right_x, right_y, px_per_u, ox, oy, sx, sy, dist, pulse;
	local vector lpos, col;

	lshow = getstati (BMST_LSHOW);
	if (!lshow)
		return;
	lpos_x = getstati (BMST_LX);
	lpos_y = getstati (BMST_LY);
	lpos_z = getstati (BMST_LZ);
	if (vlen (lpos - porg) < 24)
		return;

	yrad = yaw_deg * BM_MM_DEG2RAD;
	fwd_x = MM_Cos (yrad);
	fwd_y = MM_Sin (yrad);
	right_x = fwd_y;
	right_y = 0 - fwd_x;
	px_per_u = rad / range;

	ox = lpos_x - porg_x;
	oy = lpos_y - porg_y;
	sx = (ox * right_x + oy * right_y) * px_per_u;
	sy = 0 - (ox * fwd_x + oy * fwd_y) * px_per_u;
	dist = sqrt (sx * sx + sy * sy);
	pulse = 0.72 + 0.28 * MM_Sin (time * 6);
	col = '1.0 0.86 0.22';

	if (dist <= rad - 4)
	{
		MM_Ring (cx + sx, cy + sy, 4.4, 8, 1.1, col, 0.90 * pulse * mm_alpha_cur);
	}
};

void(float cx, float cy, float rad, float range, vector porg, float yaw_deg) MM_DrawPings =
{
	local float yrad, fwd_x, fwd_y, right_x, right_y, px_per_u;
	local float i, age, frac, ox, oy, sx, sy, dist, mx, my, kind, r;
	local vector org, col;

	yrad = yaw_deg * BM_MM_DEG2RAD;
	fwd_x = MM_Cos (yrad);
	fwd_y = MM_Sin (yrad);
	right_x = fwd_y;
	right_y = 0 - fwd_x;
	px_per_u = rad / range;

	i = 0;
	while (i < BM_MM_PING_MAX)
	{
		if (mm_p_t[i] > 0)
		{
			age = time - mm_p_t[i];
			if (age >= 0 && age < BM_MM_PING_LIFE)
			{
				frac = (1 - (age / BM_MM_PING_LIFE)) * mm_alpha_cur;
				org = mm_p_pos[i];
				kind = mm_p_kind[i];
				ox = org_x - porg_x;
				oy = org_y - porg_y;
				sx = (ox * right_x + oy * right_y) * px_per_u;
				sy = 0 - (ox * fwd_x + oy * fwd_y) * px_per_u;
				dist = sqrt (sx * sx + sy * sy);

				col = '1.0 0.35 0.20';
				if (kind == BM_RPK_BLAST)
					col = '1.0 0.62 0.16';
				else if (kind == BM_RPK_KILL)
					col = '1.0 0.18 0.32';
				else if (kind == BM_RPK_MONSTER)
					col = '1.0 0.32 0.48';

				if (dist <= rad - 3.2)
				{
					mx = cx + sx;
					my = cy + sy;
					if (age < 0.45)
					{
						r = 2.0 + (age / 0.45) * 5.2;
						MM_Ring (mx, my, r, 10, 1.0, col, 0.72 * (1 - age / 0.45));
					}
					if (kind == BM_RPK_KILL)
					{
						MM_Line (1.3, MM_Vec2 (mx - 2.0, my - 2.0), MM_Vec2 (mx + 2.0, my + 2.0), col, 0.95 * frac);
						MM_Line (1.3, MM_Vec2 (mx + 2.0, my - 2.0), MM_Vec2 (mx - 2.0, my + 2.0), col, 0.95 * frac);
					}
				}
			}
		}
		i = i + 1;
	}
};

void(float cx, float cy, float rad, float yaw_deg) MM_DrawCompass =
{
	local float step_deg, rel, rrad, ux, uy, r_in, r_out, tx, ty;
	local string lbl;
	local vector col;

	// Tick marks + N/E/S/W labels rotating around the upper outer arc
	step_deg = 0;
	while (step_deg < 360)
	{
		rel = step_deg - yaw_deg;
		rrad = rel * BM_MM_DEG2RAD;
		ux = 0 - MM_Sin (rrad);
		uy = 0 - MM_Cos (rrad);

		if (uy <= 0.25)
		{
			r_in = rad + 0.8;
			r_out = rad + ((step_deg == 0 || step_deg == 90 || step_deg == 180 || step_deg == 270) ? 3.2 : 2.1);
			MM_Line (1.0, MM_Vec2 (cx + ux * r_in, cy + uy * r_in),
				MM_Vec2 (cx + ux * r_out, cy + uy * r_out), '0.88 0.92 0.96', 0.60 * mm_alpha_cur);

			lbl = "";
			col = '0.92 0.94 0.98';
			if (step_deg == 90) { lbl = "N"; col = '1.0 0.86 0.28'; }
			else if (step_deg == 0) lbl = "E";
			else if (step_deg == 270) lbl = "S";
			else if (step_deg == 180) lbl = "W";
			if (lbl != "")
			{
				local vector lsc;
				local float sw_c;
				lsc = BM_UIScaleVec ('4.5 4.5 0');
				sw_c = stringwidth (lbl, FALSE, lsc);
				tx = cx + ux * (rad + 5.4) - sw_c * 0.5;
				ty = cy + uy * (rad + 5.4) - lsc_y * 0.5;
				drawstring (MM_Vec2 (tx + 0.6, ty + 0.6), lbl, lsc, '0 0 0', 0.88 * mm_alpha_cur, 0);
				drawstring (MM_Vec2 (tx, ty), lbl, lsc, col, 0.96 * mm_alpha_cur, 0);
			}
		}
		step_deg = step_deg + 30;
	}
};

void(float cx, float cy, float yaw_screen_deg, float fov_alpha, float alpha_mul) MM_DrawPlayer =
{
	local float r1, r2, fx1, fy1, fx2, fy2;

	// Subtle forward FOV cone
	if (fov_alpha > 0.005)
	{
		r1 = (yaw_screen_deg - 30) * BM_MM_DEG2RAD;
		r2 = (yaw_screen_deg + 30) * BM_MM_DEG2RAD;
		fx1 = 0 - MM_Sin (r1) * 18;
		fy1 = 0 - MM_Cos (r1) * 18;
		fx2 = 0 - MM_Sin (r2) * 18;
		fy2 = 0 - MM_Cos (r2) * 18;
		MM_Tri2D ("gfx/minimap/white",
			MM_Vec2 (cx, cy),
			MM_Vec2 (cx + fx1, cy + fy1),
			MM_Vec2 (cx + fx2, cy + fy2),
			'0.92 0.95 0.98', fov_alpha * alpha_mul);
	}

	// Crisp bright player arrow
	MM_Chevron (cx, cy, yaw_screen_deg, 4.3, '1.0 0.86 0.20', 0.98 * alpha_mul);
};

void(float w, float h) BM_DrawMinimap =
{
	local float cx, cy, rad, range, ent_ok, alpha_mul, bg_alpha, map_alpha, map_yaw, plr_sdeg, fov_a;
	local vector porg, pang;

	w = vid_conwidth;
	h = vid_conheight;
	if (w <= 0) w = cvar ("vid_conwidth");
	if (h <= 0) h = cvar ("vid_conheight");
	if (w <= 0 || h <= 0)
		return;
	if (!BM_MinimapIsVisible ())
		return;

	MM_EnsureMap ();
	MM_ComputeLayout (w, h);
	cx = mm_cx;
	cy = mm_cy;
	rad = mm_rad;

	range = cvar ("bm_minimap_range");
	if (range <= 0)
		range = 1600;
	range = bound (600, range, 4000);

	alpha_mul = bound (0.10, cvar ("bm_minimap_alpha"), 1.0);
	mm_alpha_cur = alpha_mul;
	bg_alpha = bound (0.0, cvar ("bm_minimap_bg_alpha"), 1.0);
	map_alpha = bound (0.0, cvar ("bm_minimap_map_alpha"), 1.0);
	fov_a = bound (0.0, cvar ("bm_minimap_fov"), 0.5);

	ent_ok = FALSE;
	if (player_localentnum >= 1)
		ent_ok = getentity (player_localentnum, 0);
	if (ent_ok)
		porg = getentityvec (player_localentnum, E_ORIGIN);
	else
		porg = getpropertyvec (VF_ORIGIN);
	pang = getpropertyvec (VF_ANGLES);

	if (cvar ("bm_minimap_rotate") != 0)
	{
		map_yaw = pang_y;
		plr_sdeg = 0;
	}
	else
	{
		map_yaw = 90;
		plr_sdeg = pang_y - 90;
	}

	MM_DrawTransparentRadar (cx, cy, rad, range, porg, map_yaw, alpha_mul, bg_alpha, map_alpha);
	MM_DrawPings (cx, cy, rad, range, porg, map_yaw);
	MM_DrawPowerups (cx, cy, rad, range, porg, map_yaw);
	MM_DrawAllies (cx, cy, rad, range, porg, map_yaw);
	MM_DrawLeader (cx, cy, rad, range, porg, map_yaw);
	MM_DrawEnemies (cx, cy, rad, range, porg, map_yaw);
	MM_DrawPlayer (cx, cy, plr_sdeg, fov_a, alpha_mul);

	if (cvar ("bm_minimap_compass") != 0)
		MM_DrawCompass (cx, cy, rad, map_yaw);
};
