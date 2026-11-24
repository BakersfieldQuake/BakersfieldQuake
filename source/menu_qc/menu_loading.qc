// BakersfieldQuake MenuQC - Animated Borderless Multi-Scene Loading Screen

float LOAD_BG_COUNT = 4;

void() BM_Loading_Precache =
{
	precache_pic("gfx/loading/bg_1.png");
	precache_pic("gfx/loading/bg_2.png");
	precache_pic("gfx/loading/bg_3.png");
	precache_pic("gfx/loading/bg_4.png");
	precache_pic("gfx/loading/rob_drone.png");
	precache_pic("gfx/loading/rocket_r.png");
	precache_pic("gfx/loading/rocket_l.png");
	precache_pic("gfx/loading/flame.png");
	precache_pic("gfx/loading/boom.png");
};

float() BM_Loading_PickNextBg =
{
	local float seed, pick;

	seed = floor(random() * 97 + gettime() * 13.7);
	pick = 1 + modulo(seed, LOAD_BG_COUNT);
	if (LOAD_BG_COUNT > 1 && pick == g_load_bg_idx)
		pick = 1 + modulo(pick, LOAD_BG_COUNT);
	return pick;
};

void(string mapname, string title, string mode) BM_Loading_Begin =
{
	local string clean_m;

	clean_m = BM_CleanMapName(mapname);
	g_load_map = BM_ZoneSet(g_load_map, clean_m);
	g_load_title = BM_ZoneSet(g_load_title, title);
	g_load_mode = BM_ZoneSet(g_load_mode, mode);
	g_load_bg_idx = BM_Loading_PickNextBg();
	g_load_start_t = gettime();
	g_load_last_t = g_load_start_t;
	g_load_active = TRUE;
};

void() BM_Loading_Reset =
{
	g_load_active = FALSE;
};

void() BM_Loading_Shutdown =
{
	g_load_active = FALSE;
	g_load_map = BM_ZoneSet(g_load_map, "");
	g_load_title = BM_ZoneSet(g_load_title, "");
	g_load_mode = BM_ZoneSet(g_load_mode, "");
};

string(float idx) BM_Loading_BgPic =
{
	if (idx == 2) return "gfx/loading/bg_2.png";
	if (idx == 3) return "gfx/loading/bg_3.png";
	if (idx == 4) return "gfx/loading/bg_4.png";
	return "gfx/loading/bg_1.png";
};

string(string bsp) BM_Loading_PrettyMap =
{
	local string m;

	m = BM_CleanMapName(bsp);
	if (m == "") return "BAKERSFIELD";
	if (m == "soi6") return "SOI 6";
	if (m == "soicowboy_bkk") return "SOI COWBOY BKK";
	if (m == "bakersfielddowntown") return "BAKERSFIELD DOWNTOWN";
	if (m == "morrorock") return "MORRO ROCK";
	if (m == "bklan6") return "BKLAN 6";
	if (m == "spruce") return "SPRUCE ST";
	if (m == "dm6") return "DM6";
	if (m == "practice") return "PRACTICE RANGE";
	if (m == "start") return "START HUB";
	return strtoupper(m);
};

string(float idx) BM_Loading_Tip =
{
	if (idx == 0) return "Fueling Go-Karts with ForeLoco...";
	if (idx == 1) return "Greenman's jar never washes off.";
	if (idx == 2) return "Rob Drone is judging your aim.";
	if (idx == 3) return "John Bird is circling overhead!";
	if (idx == 4) return "Hold crouch to drift Go-Karts!";
	if (idx == 5) return "Pumping eric.mdl to peak velocity...";
	if (idx == 6) return "Press G for questionable firepower.";
	if (idx == 7) return "Wheelman & Mega Man cleared for takeoff.";
	if (idx == 8) return "Tip: Don't ride an enemy rocket.";
	return "Warming up under the Bakersfield Sign...";
};

string(float elapsed) BM_Loading_StageLabel =
{
	local float phase;

	if (elapsed < 1.2) return "INITIALIZING ARENA";
	if (elapsed < 3.5) return "LOADING MODELS & SKINS";
	if (elapsed < 6.5) return "PRECACHING SOUNDS & LIGHTMAPS";
	phase = modulo(floor(elapsed * 0.5), 3);
	if (phase == 0) return "STREAMING WORLD GEOMETRY";
	if (phase == 1) return "COMPILING SHADERS & TEXTURES";
	return "ARMING GO-KARTS & DRONES";
};

string(float t) BM_Loading_Dots =
{
	local float d;

	d = modulo(floor(t * 2.8), 4);
	if (d == 0) return "";
	if (d == 1) return ".";
	if (d == 2) return "..";
	return "...";
};

// Draw a 1x4 horizontal sprite sheet cell (4 frames across)
void(string pic, float x, float y, float w, float h, float frame_idx, float alpha) BM_Loading_DrawStrip4 =
{
	local float f;

	f = bound(0, floor(frame_idx), 3);
	drawsetcliparea(x, y, w, h);
	drawpic((x - f * w) * '1 0 0' + y * '0 1 0', pic, (w * 4) * '1 0 0' + h * '0 1 0', '1 1 1', alpha, 0);
	drawresetcliparea();
};

// Draw an animated flying rocket + 4-frame flickering exhaust flame across full screen
void(float t, float period, float phase, float dir_r, float y_norm, float arc_h, float scale_f, float lw, float lh) BM_Loading_DrawRocket =
{
	local float u, rx, ry, rw, rh, fw, fh, fx, fframe;
	local string rpic;

	u = modulo(t / period + phase, 1.0);
	rw = lw * 0.064 * scale_f;
	rh = rw * (40.0 / 96.0);
	fw = rw * 0.56;
	fh = fw;

	if (dir_r)
		rx = -rw * 1.6 + u * (lw + rw * 3.0);
	else
		rx = lw + rw * 0.6 - u * (lw + rw * 3.0);

	ry = lh * y_norm - sin(u * 3.1415927) * (lh * arc_h) + sin(t * 9.0 + phase * 12.0) * (lh * 0.004);
	rpic = dir_r ? "gfx/loading/rocket_r.png" : "gfx/loading/rocket_l.png";
	fframe = modulo(floor(t * 16.0 + phase * 7.0), 4);

	if (dir_r)
	{
		fx = rx - fw * 0.78;
		BM_Loading_DrawStrip4("gfx/loading/flame.png", fx, ry + (rh - fh) * 0.5, fw, fh, fframe, 0.92);
	}
	else
	{
		BM_Fill(rx + rw * 0.84, ry + rh * 0.22, fw * 0.55, rh * 0.56, '1.0 0.45 0.10', 0.72);
		BM_Fill(rx + rw * 0.88, ry + rh * 0.34, fw * 0.35, rh * 0.32, '1.0 0.90 0.35', 0.88);
	}
	drawpic(rx * '1 0 0' + ry * '0 1 0', rpic, rw * '1 0 0' + rh * '0 1 0', '1 1 1', 1.0, 0);
};

// Draw an animated 4-frame comic starburst explosion
void(float t, float period, float phase, float cx_n, float cy_n, float sz_n, float lw, float lh) BM_Loading_DrawBoom =
{
	local float u, fr, bsz, bx, by;

	u = modulo(t / period + phase, 1.0);
	if (u > 0.46)
		return;
	fr = floor((u / 0.46) * 4.0);
	bsz = lw * sz_n * (0.78 + 0.32 * sin((u / 0.46) * 3.1415927));
	bx = lw * cx_n - bsz * 0.5;
	by = lh * cy_n - bsz * 0.5;
	BM_Loading_DrawStrip4("gfx/loading/boom.png", bx, by, bsz, bsz, fr, 0.92);
};

// Lakitu-style Rob Drone hovering in top-left sky dangling a pulsing 3-light stoplight
void(float t, float elapsed, float lw, float lh) BM_Loading_DrawLakituRob =
{
	local float rx, ry, rsz, lx, ly, lw_b, lh_b, lit, bulb_h;

	rsz = lw * 0.058;
	rx = lw * 0.022 + sin(t * 2.2) * (lw * 0.008);
	ry = lh * 0.045 + cos(t * 3.1) * (lh * 0.014);

	lx = rx + rsz * 0.80;
	ly = ry + rsz * 0.72;
	lw_b = lw * 0.018;
	lh_b = lh * 0.090;

	BM_Fill(rx + rsz * 0.62, ry + rsz * 0.42, (lx + lw_b * 0.5) - (rx + rsz * 0.62), 1.5, '0.88 0.80 0.56', 0.92);
	BM_Fill(lx + lw_b * 0.5 - 0.6, ry + rsz * 0.42, 1.2, ly - (ry + rsz * 0.42), '0.88 0.88 0.92', 0.84);

	BM_Fill(lx, ly, lw_b, lh_b, '0.06 0.06 0.08', 0.92);
	BM_Outline(lx, ly, lw_b, lh_b, '0.85 0.72 0.28', 0.90, 1.0);

	lit = modulo(floor(elapsed * 0.85), 3);
	bulb_h = (lh_b - 10) / 3;
	BM_Fill(lx + 2.5, ly + 2.5, lw_b - 5, bulb_h, (lit == 0) ? '1.0 0.22 0.16' : '0.28 0.07 0.06', (lit == 0) ? 1.0 : 0.65);
	BM_Fill(lx + 2.5, ly + 5.0 + bulb_h, lw_b - 5, bulb_h, (lit == 1) ? '1.0 0.82 0.16' : '0.28 0.22 0.05', (lit == 1) ? 1.0 : 0.65);
	BM_Fill(lx + 2.5, ly + 7.5 + 2 * bulb_h, lw_b - 5, bulb_h, (lit == 2) ? '0.24 0.98 0.36' : '0.06 0.24 0.09', (lit == 2) ? 1.0 : 0.65);

	if (getimagesize("gfx/loading/rob_drone.png") != '0 0 0')
		drawpic(rx * '1 0 0' + ry * '0 1 0', "gfx/loading/rob_drone.png", rsz * '1 0 0' + rsz * '0 1 0', '1 1 1', 1.0, 0);
};

// Animated chunky energy meter + sweeping pulse + racing cast sprite so user clearly sees live loading activity
void(float t, float rx0, float rail_y, float rail_w, float lh) BM_Loading_DrawActivityBar =
{
	local float bar_h, n_seg, i, seg_w, gap, phase, sx, pulse_x, pulse_w;
	local float u, rx, rsz, row, col, cast_i, fframe, f_sz;
	local string cpic;
	local vector scol;

	bar_h = 8;
	BM_Fill(rx0, rail_y, rail_w, bar_h, '0.07 0.06 0.08', 0.96);
	BM_Outline(rx0, rail_y, rail_w, bar_h, '0.44 0.30 0.16', 0.85, 1.0);

	// Animated marching segmented blocks (unmistakable live motion even on slow frames)
	n_seg = 28;
	gap = 2;
	seg_w = (rail_w - 4 - (n_seg - 1) * gap) / n_seg;
	phase = modulo(t * 10.0, n_seg);
	for (i = 0; i < n_seg; i = i + 1)
	{
		local float dist;
		dist = modulo(i - phase + n_seg, n_seg);
		if (dist < 8)
		{
			scol = (dist < 2) ? '1.0 0.86 0.28' : ((dist < 5) ? '0.96 0.56 0.14' : '0.82 0.24 0.10');
			sx = rx0 + 2 + i * (seg_w + gap);
			BM_Fill(sx, rail_y + 1.5, max(1, seg_w), bar_h - 3, scol, 0.95);
		}
		else
		{
			sx = rx0 + 2 + i * (seg_w + gap);
			BM_Fill(sx, rail_y + 2, max(1, seg_w), bar_h - 4, '0.16 0.14 0.17', 0.65);
		}
	}

	// Sweeping bright scanner highlight
	u = modulo(t * 0.26, 1.0);
	pulse_w = rail_w * 0.16;
	pulse_x = rx0 + u * (rail_w - pulse_w);
	BM_Fill(pulse_x, rail_y + 1, pulse_w, 2.0, '1.0 0.94 0.62', 0.85);

	// Racing cast sprite + flame boost riding on top of the active bar
	rsz = max(20, lh * 0.060);
	rx = rx0 + u * (rail_w - rsz);
	fframe = modulo(floor(t * 18.0), 4);
	f_sz = rsz * 0.72;
	BM_Loading_DrawStrip4("gfx/loading/flame.png", max(rx0, rx - f_sz * 0.62), rail_y - f_sz * 0.72, f_sz, f_sz, fframe, 0.90);

	cast_i = modulo(floor(t * 0.26), 3);
	if (cast_i == 0)
		cpic = "gfx/menu_cast/greenguy.png";
	else if (cast_i == 1)
		cpic = "gfx/menu_cast/jesskart.png";
	else
		cpic = "gfx/menu_cast/wheelman.png";

	if (getimagesize(cpic) != '0 0 0')
	{
		col = 2;
		row = modulo(floor(t * 14.0), 6);
		drawsetcliparea(rx, rail_y - rsz + 3, rsz, rsz);
		drawpic((rx - col * rsz) * '1 0 0' + (rail_y - rsz + 3 - row * rsz) * '0 1 0', cpic, (rsz * 8) * '1 0 0' + (rsz * 6) * '0 1 0', '1 1 1', 1.0, 0);
		drawresetcliparea();
	}
};

void(float lw, float lh) BM_Loading_Draw =
{
	local float t, elapsed, prev_v, bg_idx, pulse;
	local float bx, by, bw, bh, tx, ty, tw, th, info_x, info_w;
	local float tip_idx, mins, secs, tenths;
	local string bg_pic, cur_map, map_cvar, map_title, mode_str, thumb, tip_str, time_str, stage_str, hdr_str;

	t = gettime();
	if (!g_load_active || (t - g_load_last_t) > 1.2)
	{
		g_load_start_t = t;
		g_load_active = TRUE;
		g_load_bg_idx = BM_Loading_PickNextBg();
	}
	g_load_last_t = t;
	elapsed = max(0, t - g_load_start_t);

	// Allow bm_loading_preview 1..4 to preview each specific backdrop
	prev_v = floor(cvar("bm_loading_preview"));
	bg_idx = (prev_v >= 1 && prev_v <= LOAD_BG_COUNT) ? prev_v : g_load_bg_idx;
	if (bg_idx < 1 || bg_idx > LOAD_BG_COUNT)
		bg_idx = 1;

	cur_map = g_load_map;
	map_cvar = BM_CleanMapName(cvar_string("mapname"));
	if (map_cvar != "" && cur_map == "")
	{
		cur_map = map_cvar;
		g_load_map = BM_ZoneSet(g_load_map, cur_map);
	}

	// 1. Full-bleed borderless loading artwork (1 of 4 scenes)
	bg_pic = BM_Loading_BgPic(bg_idx);
	if (getimagesize(bg_pic) != '0 0 0')
	{
		drawpic('0 0 0', bg_pic, lw * '1 0 0' + lh * '0 1 0', '1 1 1', 1.0, 0);
	}
	else
	{
		BM_Fill(0, 0, lw, lh, '0.05 0.05 0.06', 1.0);
		drawpic((lw * 0.5 - 80) * '1 0 0' + (lh * 0.4 - 20) * '0 1 0', "gfx/loading.lmp", '160 40 0', '1 1 1', 1.0, 0);
	}

	// 2. Full-bleed animated rockets, starburst explosions (clear of character faces), and Lakitu Rob Drone
	drawsetcliparea(0, 0, lw, lh);

	BM_Loading_DrawBoom(t, 1.45, 0.14, 0.09, 0.45, 0.072, lw, lh);
	BM_Loading_DrawBoom(t, 1.85, 0.62, 0.91, 0.46, 0.072, lw, lh);

	BM_Loading_DrawRocket(t, 2.40, 0.08, TRUE,  0.405, 0.022, 0.90, lw, lh);
	BM_Loading_DrawRocket(t, 3.00, 0.51, FALSE, 0.365, 0.018, 0.82, lw, lh);
	BM_Loading_DrawRocket(t, 3.55, 0.78, TRUE,  0.560, 0.015, 0.72, lw, lh);

	if (bg_idx <= 2)
		BM_Loading_DrawLakituRob(t, elapsed, lw, lh);

	drawresetcliparea();

	// 3. Prominent floating translucent bottom loading HUD bar (unmistakable live loading indicator)
	bx = lw * 0.025;
	by = lh * 0.812;
	bw = lw * 0.950;
	bh = lh * 0.162;

	pulse = 0.5 + 0.5 * sin(t * 5.0);
	BM_Fill(bx, by, bw, bh, '0.03 0.03 0.05', 0.88);
	BM_Outline(bx, by, bw, bh, '0.96 0.68 0.18', 0.55 + 0.35 * pulse, 1.2);
	BM_Fill(bx, by, bw, 2.5, COL_ACCENT_HOT, 0.95);

	// Left side of bar: Levelshot thumbnail with subtle "LOADING" pill
	th = bh - 12;
	tw = th * 1.6;
	tx = bx + 6;
	ty = by + 6;
	thumb = (cur_map != "") ? BM_LevelshotPic(cur_map) : "levelshots/_unknown.jpg";
	BM_Fill(tx, ty, tw, th, '0.02 0.02 0.03', 1.0);
	if (getimagesize(thumb) != '0 0 0')
		drawpic(tx * '1 0 0' + ty * '0 1 0', thumb, tw * '1 0 0' + th * '0 1 0', '1 1 1', 1.0, 0);
	BM_Outline(tx, ty, tw, th, COL_ACCENT, 0.85, 1.0);

	// Right of thumbnail: Clear "LOADING ... PLEASE WAIT" header + animated progress meter + stage + tips
	info_x = tx + tw + 12;
	info_w = (bx + bw - 12) - info_x;

	mode_str = (g_load_mode != "") ? g_load_mode : "LOADING";
	map_title = (g_load_title != "") ? g_load_title : BM_Loading_PrettyMap(cur_map);
	stage_str = strcat(BM_Loading_StageLabel(elapsed), BM_Loading_Dots(t));
	tip_idx = modulo(floor(elapsed / 3.2), 10);
	tip_str = BM_Loading_Tip(tip_idx);

	mins = floor(elapsed / 60);
	secs = floor(modulo(elapsed, 60));
	tenths = floor(modulo(elapsed * 10, 10));
	time_str = strcat(ftos(mins), ":", (secs < 10) ? "0" : "", ftos(secs), ".", ftos(tenths));

	// Pulsing green/amber live status beacon + unmistakable "LOADING <MAP> - PLEASE WAIT..."
	BM_Fill(info_x, by + 8, 7, 7, '0.28 0.98 0.42', 0.45 + 0.55 * pulse);
	hdr_str = strcat(mode_str, ": ", map_title, " - PLEASE WAIT", BM_Loading_Dots(t));
	BM_DrawTextClipped(info_x + 12, by + 6, info_w * 0.72, hdr_str, 8.5, COL_ACCENT, 0.98, FALSE);
	BM_DrawTextRight(bx + bw - 30, by + 7, strcat("ELAPSED ", time_str), 7, COL_GOOD, 0.98);
	BM_DrawMenuDot(bx + bw - 24, by + 3);

	// Prominent animated segmented progress bar + racing cast sprite
	BM_Loading_DrawActivityBar(t, info_x, by + 23, info_w, lh);

	// Stage status (left) + funny Bakersfield tip (right) right above Zircon's engine stack text
	BM_DrawTextClipped(info_x, by + 35, info_w * 0.48, stage_str, 7, COL_HIGHLIGHT, 0.95, FALSE);
	BM_DrawTextClipped(info_x + info_w * 0.49, by + 35, info_w * 0.51, tip_str, 7, COL_MUTED, 0.95, FALSE);
};
