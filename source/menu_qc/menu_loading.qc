// BakersfieldQuake MenuQC - Animated Borderless Multi-Scene Loading Screen

float LOAD_BG_COUNT = 6;

void() BM_Loading_Precache =
{
	precache_pic("gfx/loading/bg_1.png");
	precache_pic("gfx/loading/bg_2.png");
	precache_pic("gfx/loading/bg_3.png");
	precache_pic("gfx/loading/bg_4.png");
	precache_pic("gfx/loading/bg_5.png");
	precache_pic("gfx/loading/bg_6.png");
};

// Wall-clock seconds of the day for the elapsed readout. gettime() is the time the engine frame started; a map load
// blocks inside one frame for seconds (12 s for Downtown here), so it froze, the old bar sat at 2% and every time
// jump re-picked the backdrop (playtest 1.76). strftime reads the real clock (1 s steps).
float() BM_Loading_Clock =
{
	if (tokenize(strftime(TRUE, "%H %M %S")) < 3)
		return gettime();
	return stof(argv(0)) * 3600 + stof(argv(1)) * 60 + stof(argv(2));
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
	g_load_pending = TRUE;		// keep this backdrop for the load that is about to start
	g_load_active = FALSE;
};

// Called on m_newmap, which can fire in the middle of a load: keep the backdrop and the bar where they are.
void() BM_Loading_Reset =
{
};

// Called at the top of every normal frame (m_draw). The engine draws no normal frames while it loads a map, so the
// first one after loading-screen draws means the load is over; the next loading draw starts a new load.
void() BM_Loading_GameFrame =
{
	if (g_load_active && cvar("bm_loading_preview") <= 0)
	{
		g_load_active = FALSE;
		g_load_pending = FALSE;
	}
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
	if (idx == 5) return "gfx/loading/bg_5.png";
	if (idx == 6) return "gfx/loading/bg_6.png";
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
	if (m == "bakersfieldish") return "BAKERSFIELD-ISH";
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
	if (idx == 4) return "Kyle's giant scissors cut through armor.";
	if (idx == 5) return "Eric's internet just lagged again.";
	if (idx == 6) return "Incoming Dookie projectile - take cover!";
	if (idx == 7) return "Wheelman & Mega Man cleared for takeoff.";
	if (idx == 8) return "Pickle Surprise awaits!";
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

// Monotonic left-to-right progress bar with percentage. The engine gives menu QC no real progress, so it moves on
// loading-screen redraws (the engine redraws after each load step: ~140 for Downtown) and on the wall clock.
// Never goes backwards within a load.
void(float elapsed, float x0, float y0, float w, float h) BM_Loading_DrawProgressBar =
{
	local float bar_w, frac, fill_w, pct;
	local string pct_str;

	frac = max(elapsed / (elapsed + 4), g_load_draws / (g_load_draws + 40));
	frac = bound(0.01, frac, 0.97);
	g_load_frac = max(g_load_frac, frac);
	frac = g_load_frac;
	pct = floor(frac * 100);

	bar_w = max(24, w - 32);
	BM_Fill(x0, y0, bar_w, h, '0.07 0.06 0.08', 0.96);
	BM_Outline(x0, y0, bar_w, h, '0.48 0.34 0.18', 0.88, 1.0);

	fill_w = max(2, (bar_w - 3) * frac);
	// Smooth warm Quake gold-orange fill from left to right
	BM_Fill(x0 + 1.5, y0 + 1.5, fill_w, h - 3, '0.88 0.44 0.10', 0.96);
	BM_Fill(x0 + 1.5, y0 + 1.5, fill_w, max(1, (h - 3) * 0.45), '0.98 0.74 0.22', 0.95);
	// Crisp bright leading edge
	BM_Fill(x0 + 1.5 + max(0, fill_w - 2.5), y0 + 1.5, min(2.5, fill_w), h - 3, '1.0 0.95 0.72', 0.98);

	pct_str = strcat(ftos(pct), "%");
	BM_DrawTextRight(x0 + w, y0 - 0.5, pct_str, 7, COL_HIGHLIGHT, 0.98);
};

void(float lw, float lh) BM_Loading_Draw =
{
	local float t, elapsed, prev_v, bg_idx, pulse;
	local float bx, by, bw, bh, tx, ty, tw, th, info_x, info_w, bar_x, bar_w;
	local float tip_idx, mins, secs;
	local string bg_pic, cur_map, map_cvar, map_title, mode_str, thumb, tip_str, time_str, stage_str, hdr_str;

	// One backdrop per load: picked when the load starts (or by BM_Loading_Begin just before it), never again until
	// a normal frame has been drawn (BM_Loading_GameFrame)
	if (!g_load_active)
	{
		g_load_start_t = BM_Loading_Clock();
		g_load_active = TRUE;
		g_load_draws = 0;
		g_load_frac = 0;
		if (!g_load_pending)
			g_load_bg_idx = BM_Loading_PickNextBg();
		g_load_pending = FALSE;
	}
	g_load_draws = g_load_draws + 1;
	t = gettime();
	elapsed = BM_Loading_Clock() - g_load_start_t;
	if (elapsed < 0)
		elapsed = elapsed + 86400;		// past midnight

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

	// 1. Full-bleed borderless loading artwork (1 of 4 scenes, 100% unobstructed)
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

	// 2. Ultra-slim bottom loading strip (sits cleanly in the bottom 9% below the karts)
	bx = lw * 0.015;
	by = lh * 0.905;
	bw = lw * 0.970;
	bh = lh * 0.086;

	pulse = 0.5 + 0.5 * sin(t * 5.0);
	BM_Fill(bx, by, bw, bh, '0.03 0.03 0.05', 0.80);
	BM_Outline(bx, by, bw, bh, '0.96 0.68 0.18', 0.45 + 0.35 * pulse, 1.0);
	BM_Fill(bx, by, bw, 1.5, COL_ACCENT_HOT, 0.90);

	// Compact map levelshot thumbnail on the far left
	th = bh - 6;
	tw = th * 1.6;
	tx = bx + 4;
	ty = by + 3;
	thumb = (cur_map != "") ? BM_LevelshotPic(cur_map) : BM_LevelshotUnknown();
	BM_Fill(tx, ty, tw, th, '0.02 0.02 0.03', 1.0);
	if (getimagesize(thumb) != '0 0 0')
		drawpic(tx * '1 0 0' + ty * '0 1 0', thumb, tw * '1 0 0' + th * '0 1 0', '1 1 1', 1.0, 0);
	BM_Outline(tx, ty, tw, th, COL_ACCENT, 0.80, 1.0);

	info_x = tx + tw + 8;
	info_w = (bx + bw - 8) - info_x;

	mode_str = (g_load_mode != "") ? g_load_mode : "LOADING";
	map_title = (g_load_title != "") ? g_load_title : BM_Loading_PrettyMap(cur_map);
	stage_str = strcat(BM_Loading_StageLabel(elapsed), BM_Loading_Dots(t));
	tip_idx = modulo(floor(elapsed / 3.2), 10);
	tip_str = BM_Loading_Tip(tip_idx);

	mins = floor(elapsed / 60);
	secs = floor(modulo(elapsed, 60));
	time_str = strcat(ftos(mins), ":", (secs < 10) ? "0" : "", ftos(secs));

	bar_x = info_x + info_w * 0.45;
	bar_w = info_w * 0.37;
	BM_Fill(info_x, by + 5.5, 6, 6, '0.28 0.98 0.42', 0.45 + 0.55 * pulse);
	hdr_str = strcat(mode_str, ": ", map_title, " - PLEASE WAIT", BM_Loading_Dots(t));
	BM_DrawTextClipped(info_x + 10, by + 4, max(16, (bar_x - (info_x + 10)) - 6), hdr_str, 7.5, COL_ACCENT, 0.98, FALSE);
	BM_Loading_DrawProgressBar(elapsed, bar_x, by + 4.5, bar_w, 7);

	BM_DrawTextRight(bx + bw - 26, by + 4, time_str, 7, COL_GOOD, 0.98);
	BM_DrawMenuDot(bx + bw - 21, by + 1);

	// Bottom row inside slim strip: stage label + rotating tip (aligned cleanly above/around engine stack text)
	BM_DrawTextClipped(info_x, by + 17, info_w * 0.46, stage_str, 6.5, COL_HIGHLIGHT, 0.92, FALSE);
	BM_DrawTextClipped(info_x + info_w * 0.48, by + 17, info_w * 0.52, tip_str, 6.5, COL_MUTED, 0.90, FALSE);
};
