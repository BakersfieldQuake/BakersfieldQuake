/*
================
bm_minimap_hud.qc — CoD-style circular anti-wallhack minimap (bottom-left corner)

Renders a compact circular rotating minimap anchored in the bottom-left corner:
  - Uses 2D R_BeginPolygon triangle fans for true circular clipping and smooth
    player-facing rotation (UP = player view direction).
  - Uses dark charcoal / slate / ivory BSP floorplans from zz_minimap.pk3
    (gfx/minimap/<map> shader) with a dark radar-disc fallback.
  - Anti-wallhack: gunfire/blasts/kills drop static fading blips (2.6s), while
    every 5s coarse ~320u fuzzy heat clouds hint where quiet enemies cluster.
================
*/

float	ENT_BM_RADAR		= 8;

float	BM_RPK_GUN			= 1;
float	BM_RPK_BLAST		= 2;
float	BM_RPK_KILL			= 3;
float	BM_RPK_MONSTER		= 4;

float	BM_MM_R				= 39;
float	BM_MM_PING_MAX		= 16;
float	BM_MM_PING_LIFE		= 2.6;
float	BM_MM_HEAT_LIFE		= 5.5;
float	BM_MM_DEG2RAD		= 0.01745329;

string	mm_cur_raw_map;
string	mm_cur_shader;
float	mm_has_pic;

float	mm_last_seq[4];
float	mm_p_next;
vector	mm_p_pos[16];
float	mm_p_kind[16];
float	mm_p_t[16];

float	mm_last_hseq;
float	mm_h_cnt;
float	mm_heat_t;
vector	mm_h_pos[4];
float	mm_h_int[4];

float	mm_a_cnt;
float	mm_ally_t;
vector	mm_a_pos[4];
float	mm_a_yaw[4];

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

// Draw a filled CoD-style arrow chevron. screen_deg = 0 points straight UP.
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
	c_p  = MM_Vec2 (cx + fx * (sz + 1.0), cy + fy * (sz + 1.0));
	c_wl = MM_Vec2 (cx - fx * (sz * 0.85 + 0.7) - rx * (sz * 0.85 + 0.9), cy - fy * (sz * 0.85 + 0.7) - ry * (sz * 0.85 + 0.9));
	c_wr = MM_Vec2 (cx - fx * (sz * 0.85 + 0.7) + rx * (sz * 0.85 + 0.9), cy - fy * (sz * 0.85 + 0.7) + ry * (sz * 0.85 + 0.9));
	c_n  = MM_Vec2 (cx - fx * (sz * 0.20), cy - fy * (sz * 0.20));
	MM_Tri2D ("gfx/minimap/white", c_p, c_wl, c_n, '0 0 0', 0.88 * a);
	MM_Tri2D ("gfx/minimap/white", c_p, c_n, c_wr, '0 0 0', 0.88 * a);

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
		MM_Line (1.1, MM_Vec2 (cx - 2.0, cy - 3.4), MM_Vec2 (cx, cy - 5.4), col, a);
		MM_Line (1.1, MM_Vec2 (cx + 2.0, cy - 3.4), MM_Vec2 (cx, cy - 5.4), col, a);
	}
	else if (dz < -96)
	{
		MM_Line (1.1, MM_Vec2 (cx - 2.0, cy + 3.4), MM_Vec2 (cx, cy + 5.4), col, a);
		MM_Line (1.1, MM_Vec2 (cx + 2.0, cy + 3.4), MM_Vec2 (cx, cy + 5.4), col, a);
	}
};

void(float cx, float cy, float rad, float sx, float sy, vector col, float a) MM_RimBlip =
{
	local float d, ux, uy, rx, ry, bx, by;
	local vector tip, b1, b2;

	if (a <= 0.02)
		return;
	d = sqrt (sx * sx + sy * sy);
	if (d <= 0.001)
		return;
	ux = sx / d;
	uy = sy / d;
	rx = 0 - uy;
	ry = ux;

	bx = cx + ux * (rad - 1.5);
	by = cy + uy * (rad - 1.5);
	tip = MM_Vec2 (bx + ux * 2.0, by + uy * 2.0);
	b1  = MM_Vec2 (bx - ux * 1.8 - rx * 2.4, by - uy * 1.8 - ry * 2.4);
	b2  = MM_Vec2 (bx - ux * 1.8 + rx * 2.4, by - uy * 1.8 + ry * 2.4);
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
	local float flags, i, seq, kind, hseq, hcnt, acnt, pyaw;
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
		hseq = ReadByte ();
		hcnt = ReadByte ();
		if (hcnt > 4)
			hcnt = 4;
		i = 0;
		while (i < hcnt)
		{
			org_x = ReadCoord ();
			org_y = ReadCoord ();
			org_z = ReadCoord ();
			mm_h_pos[i] = org;
			mm_h_int[i] = ReadByte ();
			i = i + 1;
		}
		if (hseq > 0 && hseq != mm_last_hseq)
		{
			mm_last_hseq = hseq;
			mm_h_cnt = hcnt;
			mm_heat_t = time;
		}
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
};

void() BM_Radar_EntRemove =
{
	local float i;

	mm_h_cnt = 0;
	mm_a_cnt = 0;
	i = 0;
	while (i < 4)
	{
		mm_last_seq[i] = 0;
		i = i + 1;
	}
	mm_last_hseq = 0;
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
	return mm_cy - mm_rad - 14;
};

// Rotated & circularly-clipped CoD floorplan blueprint via precomputed 24-slice 2D polygon fan
void(float cx, float cy, float rad, float range, vector porg, float yaw_deg, float alpha_mul, float bg_alpha) MM_DrawRotatedBlueprint =
{
	local float span, yrad, fwd_x, fwd_y, right_x, right_y, inv_span, r_in, k_uv;
	local float uc, vc, i, ux, uy, sx, sy, wx, wy, map_a, base_x, base_y;
	local vector p, uv;

	// Dark smoky circular disc backing
	if (bg_alpha > 0.01)
		MM_FillCircle (cx, cy, rad - 0.5, 24, '0.05 0.06 0.07', bg_alpha);

	if (!mm_has_pic || mm_map_half <= 0)
	{
		MM_Ring (cx, cy, rad * 0.52, 24, 1, '0.45 0.48 0.52', 0.22 * alpha_mul);
		return;
	}

	MM_InitUnitCircle ();
	map_a = 0.92 * alpha_mul;
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
	R_PolygonVertex (p, uv, '1 1 1', map_a);
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
		R_PolygonVertex (p, uv, '1 1 1', map_a);
		i = i + 1;
	}
	R_EndPolygon ();
};

void(float cx, float cy, float rad, float range, vector porg, float yaw_deg) MM_DrawHeatZones =
{
	local float age, fade, yrad, fwd_x, fwd_y, right_x, right_y;
	local float px_per_u, rad_px, i, ox, oy, sx, sy, dist, mx, my, inten, pulse, max_d;
	local vector horg, col;

	if (mm_h_cnt <= 0)
		return;
	age = time - mm_heat_t;
	if (age < 0 || age >= BM_MM_HEAT_LIFE)
		return;

	fade = 1 - (age / BM_MM_HEAT_LIFE);
	if (fade > 0.85)
		fade = 0.85 + 0.15 * ((1 - fade) / 0.15);

	yrad = yaw_deg * BM_MM_DEG2RAD;
	fwd_x = MM_Cos (yrad);
	fwd_y = MM_Sin (yrad);
	right_x = fwd_y;
	right_y = 0 - fwd_x;

	px_per_u = rad / range;
	rad_px = bound (8, 320 * px_per_u, rad * 0.56);
	pulse = 0.80 + 0.20 * MM_Sin (time * 4.5);

	i = 0;
	while (i < mm_h_cnt)
	{
		horg = mm_h_pos[i];
		inten = bound (0.7, mm_h_int[i] / 64, 1.3);
		ox = horg_x - porg_x;
		oy = horg_y - porg_y;
		sx = (ox * right_x + oy * right_y) * px_per_u;
		sy = 0 - (ox * fwd_x + oy * fwd_y) * px_per_u;
		dist = sqrt (sx * sx + sy * sy);

		max_d = rad - rad_px * 0.45;
		if (dist > max_d && dist > 0.001)
		{
			sx = (sx / dist) * max_d;
			sy = (sy / dist) * max_d;
		}
		mx = cx + sx;
		my = cy + sy;

		col = '0.96 0.22 0.16';
		if (mm_h_int[i] >= 96)
			col = '1.0 0.14 0.14';

		R_BeginPolygon ("gfx/minimap/heat", 0, TRUE);
		R_PolygonVertex (MM_Vec2 (mx - rad_px, my - rad_px), '0 0 0', col, 0.44 * fade * pulse * inten * mm_alpha_cur);
		R_PolygonVertex (MM_Vec2 (mx + rad_px, my - rad_px), '1 0 0', col, 0.44 * fade * pulse * inten * mm_alpha_cur);
		R_PolygonVertex (MM_Vec2 (mx + rad_px, my + rad_px), '1 1 0', col, 0.44 * fade * pulse * inten * mm_alpha_cur);
		R_PolygonVertex (MM_Vec2 (mx - rad_px, my + rad_px), '0 1 0', col, 0.44 * fade * pulse * inten * mm_alpha_cur);
		R_EndPolygon ();
		i = i + 1;
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
	col = '0.24 0.80 1.0';

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
			MM_Chevron (cx + sx, cy + sy, mm_a_yaw[i] - yaw_deg, 3.4, col, 0.96 * mm_alpha_cur);
			MM_HeightArrow (cx + sx, cy + sy, aorg_z - porg_z, col, 0.82 * mm_alpha_cur);
		}
		else
		{
			MM_RimBlip (cx, cy, rad, sx, sy, col, 0.88 * mm_alpha_cur);
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
		MM_Ring (cx + sx, cy + sy, 3.2, 8, 1.2, col, 0.92 * pulse);
		MM_FillCircle (cx + sx, cy + sy, 1.3, 8, col, 0.95 * pulse);
	}
	else
	{
		MM_RimBlip (cx, cy, rad, sx, sy, col, 0.90 * pulse);
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

				col = '0.98 0.22 0.18';
				if (kind == BM_RPK_BLAST)
					col = '1.0 0.56 0.14';
				else if (kind == BM_RPK_KILL)
					col = '1.0 0.16 0.28';
				else if (kind == BM_RPK_MONSTER)
					col = '0.98 0.28 0.44';

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
					else if (kind == BM_RPK_BLAST)
					{
						MM_FillCircle (mx, my, 2.5, 10, '0 0 0', 0.82 * frac);
						MM_FillCircle (mx, my, 1.8, 10, col, 0.98 * frac);
					}
					else
					{
						MM_FillCircle (mx, my, 2.2, 10, '0 0 0', 0.82 * frac);
						MM_FillCircle (mx, my, 1.5, 10, col, 0.98 * frac);
					}
					MM_HeightArrow (mx, my, org_z - porg_z, col, 0.88 * frac);
				}
				else
				{
					MM_RimBlip (cx, cy, rad, sx, sy, col, 0.84 * frac);
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

	// Tick marks + N/E/S/W labels rotating around the upper outer arc like CoD
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
				MM_Vec2 (cx + ux * r_out, cy + uy * r_out), '0.88 0.90 0.92', 0.55 * mm_alpha_cur);

			lbl = "";
			col = '0.90 0.92 0.94';
			if (step_deg == 90) { lbl = "N"; col = '1.0 0.86 0.28'; }
			else if (step_deg == 0) lbl = "E";
			else if (step_deg == 270) lbl = "S";
			else if (step_deg == 180) lbl = "W";
			if (lbl != "")
			{
				local vector lsc;
				lsc = BM_UIScaleVec ('4.5 4.5 0');
				tx = cx + ux * (rad + 5.6) - stringwidth (lbl, FALSE, lsc) * 0.5;
				ty = cy + uy * (rad + 5.6) - lsc_y * 0.5;
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

	// Crisp CoD warm-gold player arrow
	MM_Chevron (cx, cy, yaw_screen_deg, 4.3, '1.0 0.84 0.18', 0.98 * alpha_mul);
};

void(float w, float h) BM_DrawMinimap =
{
	local float cx, cy, rad, range, ent_ok, alpha_mul, bg_alpha, map_yaw, plr_sdeg, fov_a;
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
		range = 1400;
	range = bound (600, range, 4000);

	alpha_mul = bound (0.10, cvar ("bm_minimap_alpha"), 1.0);
	mm_alpha_cur = alpha_mul;
	bg_alpha = bound (0.0, cvar ("bm_minimap_bg_alpha"), 1.0);
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

	MM_DrawRotatedBlueprint (cx, cy, rad, range, porg, map_yaw, alpha_mul, bg_alpha);
	MM_DrawHeatZones (cx, cy, rad, range, porg, map_yaw);
	MM_DrawAllies (cx, cy, rad, range, porg, map_yaw);
	MM_DrawLeader (cx, cy, rad, range, porg, map_yaw);
	MM_DrawPings (cx, cy, rad, range, porg, map_yaw);
	MM_DrawPlayer (cx, cy, plr_sdeg, fov_a, alpha_mul);

	// Anti-aliased CoD outer circular bezel
	R_BeginPolygon ("gfx/minimap/rim", 0, TRUE);
	R_PolygonVertex (MM_Vec2 (cx - rad, cy - rad), '0 0 0', '1 1 1', 0.96 * alpha_mul);
	R_PolygonVertex (MM_Vec2 (cx + rad, cy - rad), '1 0 0', '1 1 1', 0.96 * alpha_mul);
	R_PolygonVertex (MM_Vec2 (cx + rad, cy + rad), '1 1 0', '1 1 1', 0.96 * alpha_mul);
	R_PolygonVertex (MM_Vec2 (cx - rad, cy + rad), '0 1 0', '1 1 1', 0.96 * alpha_mul);
	R_EndPolygon ();

	if (cvar ("bm_minimap_compass") != 0)
		MM_DrawCompass (cx, cy, rad, map_yaw);
};
