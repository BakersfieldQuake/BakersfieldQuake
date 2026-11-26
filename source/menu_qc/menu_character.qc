// BakersfieldQuake MenuQC - 3D Character Customizer Studio
// Modular category/slot architecture designed for easy expansion (colors now; models, gear, emotes later).

float CHAR_TAB_COLORS = 0;
float CHAR_TAB_HATS   = 1;
float CHAR_TAB_COUNT  = 2;
float CHAR_HAT_COUNT  = 8;	// matches BM_HAT_COUNT in bm_hats_common.qc

float CHAR_COLOR_COUNT  = 14;
float CHAR_PRESET_COUNT = 8;
float CHAR_POSE_COUNT   = 3;

float g_char_tab;
float g_char_top;
float g_char_bot;
float g_char_pose;
float g_char_spin;
float g_char_yaw;
float g_char_pitch;
float g_char_zoom;
float g_char_target_zoom;
float g_char_vel_yaw;
float g_char_vel_pitch;
float g_char_dragging;
float g_char_prev_mx;
float g_char_prev_my;
float g_char_last_t;
float g_char_vp_x;
float g_char_vp_y;
float g_char_vp_w;
float g_char_vp_h;
float g_char_flash_t;
float g_char_loading;		// our backdrop map is loading: the engine closes the menu on its own then
float g_char_ready_t;
float g_char_load_t;
string g_char_status;

// ---------------------------------------------------------------- Color & Preset Tables

string(float idx) BM_Char_ColorName =
{
	if (idx == 0)  return "SILVER";
	if (idx == 1)  return "UMBER";
	if (idx == 2)  return "SLATE";
	if (idx == 3)  return "RANGER";
	if (idx == 4)  return "CRIMSON";
	if (idx == 5)  return "OCHRE";
	if (idx == 6)  return "EMBER";
	if (idx == 7)  return "SAND";
	if (idx == 8)  return "VIOLET";
	if (idx == 9)  return "MAGENTA";
	if (idx == 10) return "PEACH";
	if (idx == 11) return "SAGE";
	if (idx == 12) return "GOLD";
	return "COBALT";
};

// Calibrated to Quake's 14 player palette rows (gfx/palette.lmp) for crisp UI swatches
vector(float idx) BM_Char_ColorRGB =
{
	if (idx == 0)  return '0.72 0.72 0.72';
	if (idx == 1)  return '0.48 0.36 0.16';
	if (idx == 2)  return '0.46 0.46 0.68';
	if (idx == 3)  return '0.35 0.37 0.08';
	if (idx == 4)  return '0.62 0.10 0.08';
	if (idx == 5)  return '0.58 0.40 0.10';
	if (idx == 6)  return '0.82 0.52 0.20';
	if (idx == 7)  return '0.72 0.52 0.40';
	if (idx == 8)  return '0.54 0.38 0.48';
	if (idx == 9)  return '0.64 0.34 0.48';
	if (idx == 10) return '0.72 0.60 0.52';
	if (idx == 11) return '0.34 0.44 0.38';
	if (idx == 12) return '0.86 0.74 0.14';
	return '0.16 0.22 0.86';
};

string(float p) BM_Char_PresetName =
{
	if (p == 0) return "RANGER";
	if (p == 1) return "CRIMSON";
	if (p == 2) return "BAKO GOLD";
	if (p == 3) return "COBALT";
	if (p == 4) return "VIPER";
	if (p == 5) return "SYNTH";
	if (p == 6) return "DESERT";
	return "CHROME";
};

float(float p) BM_Char_PresetTop =
{
	if (p == 0) return 3;
	if (p == 1) return 4;
	if (p == 2) return 12;
	if (p == 3) return 13;
	if (p == 4) return 11;
	if (p == 5) return 9;
	if (p == 6) return 7;
	return 0;
};

float(float p) BM_Char_PresetBot =
{
	if (p == 0) return 1;
	if (p == 1) return 0;
	if (p == 2) return 1;
	if (p == 3) return 2;
	if (p == 4) return 3;
	if (p == 5) return 13;
	if (p == 6) return 5;
	return 2;
};

string(float pose) BM_Char_PoseLabel =
{
	if (pose == 0) return "STAND";
	if (pose == 1) return "RUN";
	return "ATTACK";
};

// Modular category registry (future categories: MODEL, HEADGEAR, EMOTES...)
string(float tab) BM_Char_TabLabel =
{
	if (tab == CHAR_TAB_COLORS) return "COLORS";
	if (tab == CHAR_TAB_HATS) return "HATS";
	return "CUSTOM";
};

// ---------------------------------------------------------------- State & Cvar Sync

void() BM_Char_ReadSavedColors =
{
	local float packed;

	packed = floor(cvar("_cl_color"));
	g_char_top = bound(0, floor(packed / 16), CHAR_COLOR_COUNT - 1);
	g_char_bot = bound(0, modulo(packed, 16), CHAR_COLOR_COUNT - 1);
};

void() BM_Char_SyncCameraCvars =
{
	cvar_set("bm_char_yaw", ftos(g_char_yaw));
	cvar_set("bm_char_pitch", ftos(g_char_pitch));
	cvar_set("bm_char_zoom", ftos(g_char_zoom));
	cvar_set("bm_char_spin", ftos(g_char_spin));
	cvar_set("bm_char_pose", ftos(g_char_pose));
};

void(float top_c, float bot_c, string msg) BM_Char_ApplyColors =
{
	local float packed;

	g_char_top = bound(0, floor(top_c), CHAR_COLOR_COUNT - 1);
	g_char_bot = bound(0, floor(bot_c), CHAR_COLOR_COUNT - 1);
	packed = g_char_top * 16 + g_char_bot;
	cvar_set("_cl_color", ftos(packed));
	localcmd(strcat("color ", ftos(g_char_top), " ", ftos(g_char_bot), "\n"));
	g_char_flash_t = gettime();
	if (msg != "")
		g_char_status = BM_ZoneSet(g_char_status, msg);
};

void() BM_Char_ResetView =
{
	g_char_yaw = 152;
	g_char_pitch = 8;
	g_char_target_zoom = 1.0;
	g_char_zoom = 1.0;
	g_char_vel_yaw = 0;
	g_char_vel_pitch = 0;
	g_char_dragging = FALSE;
	BM_Char_SyncCameraCvars();
};

void() BM_Character_Init =
{
	registercvar("bm_char_open", "0", 0);
	registercvar("bm_char_bg_owned", "0", 0);
	registercvar("bm_char_vp_x", "0", 0);
	registercvar("bm_char_vp_y", "0", 0);
	registercvar("bm_char_vp_w", "320", 0);
	registercvar("bm_char_vp_h", "240", 0);
	registercvar("bm_char_yaw", "152", 0);
	registercvar("bm_char_pitch", "8", 0);
	registercvar("bm_char_zoom", "1.0", 0);
	registercvar("bm_char_spin", "1", 0);
	registercvar("bm_char_pose", "0", 0);
	registercvar("bm_char_model", "0", 0);
	registercvar("bm_hat", "0", 1);	// saved

	cvar_set("bm_char_open", "0");
	cvar_set("bm_char_bg_owned", "0");

	g_char_tab = CHAR_TAB_COLORS;
	g_char_pose = 0;
	g_char_spin = 1;
	BM_Char_ResetView();
	BM_Char_ReadSavedColors();
	g_char_status = BM_ZoneSet(g_char_status, "LIVE PREVIEW SYNCED");
};

void() BM_Character_Shutdown =
{
	g_char_loading = FALSE;
	cvar_set("bm_char_open", "0");
	cvar_set("bm_char_bg_owned", "0");
	g_char_status = BM_ZoneSet(g_char_status, "");
};

void() BM_Character_OnMenuHide =
{
	g_char_dragging = FALSE;
	if (g_char_loading)
		return;		// not the player leaving: `map` closes the menu, and BM_Character_Frame reopens it
	cvar_set("bm_char_open", "0");
	if (cvar("bm_char_bg_owned") > 0)
	{
		cvar_set("bm_char_bg_owned", "0");
		localcmd("set bm_menu_bg 0; disconnect\n");
	}
};

void() BM_Character_Open =
{
	BM_Char_ReadSavedColors();
	g_char_tab = CHAR_TAB_COLORS;
	g_char_dragging = FALSE;
	g_char_vel_yaw = 0;
	g_char_vel_pitch = 0;
	g_char_last_t = gettime();
	g_char_status = BM_ZoneSet(g_char_status, "DRAG CHARACTER TO ORBIT · SCROLL TO ZOOM");
	BM_Char_SyncCameraCvars();

	cvar_set("bm_char_open", "1");
	g_page = PAGE_CHARACTER;

	if (clientstate() < CS_CONNECTED)
	{
		cvar_set("bm_char_bg_owned", "1");
		g_char_loading = TRUE;
		g_char_ready_t = 0;
		g_char_load_t = gettime();
		localcmd("set bm_menu_bg 1; deathmatch 0; coop 0; ctf 0; maxplayers 1; map practice\n");
	}
	else
	{
		cvar_set("bm_char_bg_owned", "0");
	}
};

// called every frame, menu open or not: keeps the studio up while its backdrop map loads
void() BM_Character_Frame =
{
	if (!g_char_loading)
		return;
	if (cvar("bm_char_open") <= 0 || gettime() - g_char_load_t > 90)
	{
		g_char_loading = FALSE;
		return;
	}
	if (clientstate() >= CS_CONNECTED)
	{
		if (!g_char_ready_t)
			g_char_ready_t = gettime() + 3;		// the engine may still close the menu as signon finishes
		else if (gettime() > g_char_ready_t && g_menu_open)
			g_char_loading = FALSE;
	}
	if (!g_menu_open)
	{
		g_page = PAGE_CHARACTER;
		m_toggle(1);
	}
};

void() BM_Character_Close =
{
	g_char_dragging = FALSE;
	g_char_loading = FALSE;
	g_active_slider = 0;
	BM_PlaySound("sound/misc/menu3.wav");
	cvar_set("bm_char_open", "0");
	if (cvar("bm_char_bg_owned") > 0)
	{
		cvar_set("bm_char_bg_owned", "0");
		localcmd("set bm_menu_bg 0; disconnect\n");
	}
	g_page = PAGE_MAIN;
};

// ---------------------------------------------------------------- Orbit & Camera Update

void(float vp_x, float vp_y, float vp_w, float vp_h, float in_controls, float clicked) BM_Char_UpdateViewportInput =
{
	local float now, dt, in_vp, dx, dy, damp, alpha;

	now = gettime();
	dt = (g_char_last_t > 0) ? bound(0.001, now - g_char_last_t, 0.05) : 0.016;
	g_char_last_t = now;

	in_vp = BM_MouseIn(vp_x, vp_y, vp_w, vp_h);
	if (clicked && in_vp && !in_controls)
	{
		g_click_consumed = TRUE;
		g_char_dragging = TRUE;
		g_char_prev_mx = g_mx;
		g_char_prev_my = g_my;
		g_char_vel_yaw = 0;
		g_char_vel_pitch = 0;
	}

	if (!g_mouse1_down)
		g_char_dragging = FALSE;

	if (g_char_dragging)
	{
		dx = g_mx - g_char_prev_mx;
		dy = g_my - g_char_prev_my;
		g_char_prev_mx = g_mx;
		g_char_prev_my = g_my;

		g_char_yaw = g_char_yaw + dx * 0.68;
		g_char_pitch = bound(-26, g_char_pitch + dy * 0.42, 42);

		// Exponential velocity smoothing for silky release inertia
		alpha = min(1, dt * 18);
		g_char_vel_yaw = g_char_vel_yaw * (1 - alpha) + (dx * 0.68 / dt) * alpha;
		g_char_vel_pitch = g_char_vel_pitch * (1 - alpha) + (dy * 0.42 / dt) * alpha;
	}
	else
	{
		damp = pow(0.004, dt);
		g_char_yaw = g_char_yaw + g_char_vel_yaw * dt;
		g_char_pitch = bound(-26, g_char_pitch + g_char_vel_pitch * dt, 42);
		g_char_vel_yaw = g_char_vel_yaw * damp;
		g_char_vel_pitch = g_char_vel_pitch * damp;
		if (fabs(g_char_vel_yaw) < 1.0)
			g_char_vel_yaw = 0;
		if (fabs(g_char_vel_pitch) < 0.5)
			g_char_vel_pitch = 0;
		if (g_char_spin && g_char_vel_yaw == 0)
			g_char_yaw = g_char_yaw + dt * 22;
	}

	// Keep yaw bounded for clean angle display & float stability
	while (g_char_yaw >= 360) g_char_yaw = g_char_yaw - 360;
	while (g_char_yaw < 0)    g_char_yaw = g_char_yaw + 360;

	// Smooth camera zoom interpolation
	g_char_zoom = g_char_zoom + (g_char_target_zoom - g_char_zoom) * min(1, dt * 12);

	g_char_vp_x = vp_x;
	g_char_vp_y = vp_y;
	g_char_vp_w = vp_w;
	g_char_vp_h = vp_h;
	cvar_set("bm_char_vp_x", ftos(vp_x));
	cvar_set("bm_char_vp_y", ftos(vp_y));
	cvar_set("bm_char_vp_w", ftos(vp_w));
	cvar_set("bm_char_vp_h", ftos(vp_h));
	BM_Char_SyncCameraCvars();
};

// ---------------------------------------------------------------- Sleek UI Primitives

void(float x, float y, float w, float h, vector col) BM_Char_DrawCornerBrackets =
{
	local float bl;

	bl = 12;
	// Top-left
	BM_Fill(x, y, bl, 1.5, col, 0.92);
	BM_Fill(x, y, 1.5, bl, col, 0.92);
	// Top-right
	BM_Fill(x + w - bl, y, bl, 1.5, col, 0.92);
	BM_Fill(x + w - 1.5, y, 1.5, bl, col, 0.92);
	// Bottom-left
	BM_Fill(x, y + h - 1.5, bl, 1.5, col, 0.92);
	BM_Fill(x, y + h - bl, 1.5, bl, col, 0.92);
	// Bottom-right
	BM_Fill(x + w - bl, y + h - 1.5, bl, 1.5, col, 0.92);
	BM_Fill(x + w - 1.5, y + h - bl, 1.5, bl, col, 0.92);
};

float(string str, float sz) BM_Char_TextWidth =
{
	local float f, old_font, wd, use_sz;

	f = BM_MenuFont();
	use_sz = BM_MenuScaleSz(sz);
	old_font = drawfont;
	if (f > 0)
		drawfont = f;
	wd = stringwidth(str, FALSE, use_sz * '1 1 0');
	drawfont = old_font;
	return wd;
};

// the menu enlarges small text, so labels are shrunk until they fit the width they are given
float(string str, float sz, float w) BM_Char_FitSize =
{
	while (sz > 4 && BM_Char_TextWidth(str, sz) > w)
		sz = sz - 0.5;
	return sz;
};

float(float x, float y, float w, float h, string label, float selected, float primary) BM_Char_Button =
{
	local float hov, active, sz;
	local vector bg, brd, txt;

	hov = BM_MouseIn(x, y, w, h);
	active = (hov || selected);
	if (active)
	{
		bg = '0.52 0.08 0.04';
		brd = COL_ACCENT;
		txt = '1 1 1';
	}
	else if (primary)
	{
		bg = '0.20 0.12 0.07';
		brd = '0.72 0.48 0.22';
		txt = COL_ACCENT;
	}
	else
	{
		bg = COL_GLASS_CARD;
		brd = COL_BORDER;
		txt = COL_TEXT;
	}
	BM_Fill(x, y, w, h, bg, active ? 0.85 : 0.72);
	BM_Outline(x, y, w, h, brd, active ? 0.95 : 0.55, 1);
	sz = BM_Char_FitSize(label, 8, w - 4);
	BM_DrawTextCentered(x + w * 0.5, y + floor((h - sz) * 0.5), label, sz, txt, 0.98);
	return hov;
};

// Shared 7x2 swatch grid helper (returns picked index 0..13 on click, or -1)
float(float gx, float gy, float gw, float sh, string title, float cur_idx, float clicked) BM_Char_DrawColorGrid =
{
	local float cols, gap, sw, i, r, c, sx, sy, hov, sel, picked;
	local vector col, brd;
	local string cname;

	picked = -1;
	BM_DrawText(gx, gy, title, 7, COL_MUTED, 0.95);
	cname = BM_Char_ColorName(cur_idx);
	BM_DrawTextRight(gx + gw, gy, cname, 7, COL_ACCENT, 0.98);

	gy = gy + 11;
	cols = 7;
	gap = 3;
	sw = floor((gw - gap * (cols - 1)) / cols);

	for (i = 0; i < CHAR_COLOR_COUNT; i = i + 1)
	{
		c = modulo(i, cols);
		r = floor(i / cols);
		sx = gx + c * (sw + gap);
		sy = gy + r * (sh + gap);

		col = BM_Char_ColorRGB(i);
		hov = BM_MouseIn(sx, sy, sw, sh);
		sel = (cur_idx == i);

		if (sel)
		{
			BM_Fill(sx - 1.5, sy - 1.5, sw + 3, sh + 3, COL_ACCENT, 0.95);
			BM_Fill(sx, sy, sw, sh, col, 1.0);
			BM_Fill(sx + 1, sy + 1, sw - 2, 3, '1 1 1', 0.34);
			BM_Outline(sx, sy, sw, sh, '0.04 0.03 0.02', 0.85, 1);
			BM_Fill(sx + floor(sw * 0.5) - 2, sy + floor(sh * 0.5) - 2, 4, 4, '1 1 1', 0.92);
			BM_Outline(sx + floor(sw * 0.5) - 2, sy + floor(sh * 0.5) - 2, 4, 4, '0.05 0.03 0.02', 0.9, 1);
		}
		else
		{
			BM_Fill(sx, sy, sw, sh, col, hov ? 1.0 : 0.88);
			BM_Fill(sx + 1, sy + 1, sw - 2, 2.5, '1 1 1', hov ? 0.32 : 0.16);
			BM_Fill(sx + 1, sy + sh - 3.5, sw - 2, 2.5, '0 0 0', 0.30);
			brd = hov ? '1 1 1' : COL_BORDER;
			BM_Outline(sx, sy, sw, sh, brd, hov ? 0.95 : 0.65, 1);
		}

		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			picked = i;
			BM_PlaySound("sound/misc/menu2.wav");
		}
	}
	return picked;
};

void(float px, float py, float pw, float ph, float clicked) BM_Char_DrawColorsTab =
{
	local float gx, gw, cy, p, cols, gap, cw, ch, sx, sy, hov, active_p, r, c;
	local float pick_top, pick_bot, btn_w, sh, fy;
	local vector c_top, c_bot;

	gx = px + 14;
	gw = pw - 28;
	cy = py;

	// ---- Quick 2-tone Presets
	// footer (buttons and status line) is fixed; presets and the two swatch grids share the rest
	sh = bound(9, floor((ph - 97) / 6.3), 20);
	fy = py + ph - 32;

	BM_DrawText(gx, cy, "PRESETS", 7, COL_MUTED, 0.95);
	cy = cy + 11;

	cols = 4;
	gap = 3;
	cw = floor((gw - gap * (cols - 1)) / cols);
	ch = floor(sh * 1.15);

	for (p = 0; p < CHAR_PRESET_COUNT; p = p + 1)
	{
		c = modulo(p, cols);
		r = floor(p / cols);
		sx = gx + c * (cw + gap);
		sy = cy + r * (ch + gap);

		c_top = BM_Char_ColorRGB(BM_Char_PresetTop(p));
		c_bot = BM_Char_ColorRGB(BM_Char_PresetBot(p));
		active_p = (g_char_top == BM_Char_PresetTop(p) && g_char_bot == BM_Char_PresetBot(p));
		hov = BM_MouseIn(sx, sy, cw, ch);

		BM_Fill(sx, sy, cw, ch, active_p ? '0.24 0.12 0.06' : (hov ? '0.18 0.11 0.08' : COL_GLASS_CARD), 0.92);
		// Dual-swatch badge on left of preset pill
		BM_Fill(sx + 2, sy + 2, 6, floor((ch - 4) * 0.5), c_top, 1.0);
		BM_Fill(sx + 2, sy + 2 + floor((ch - 4) * 0.5), 6, floor((ch - 4) * 0.5), c_bot, 1.0);

		BM_DrawText(sx + 10, sy + floor((ch - 6) * 0.5), BM_Char_PresetName(p), BM_Char_FitSize(BM_Char_PresetName(p), 6.5, cw - 12), (active_p || hov) ? '1 1 1' : COL_TEXT, 0.95);
		BM_Outline(sx, sy, cw, ch, active_p ? COL_ACCENT : (hov ? COL_HIGHLIGHT : COL_BORDER), active_p ? 0.95 : 0.65, active_p ? 1.5 : 1);

		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			BM_Char_ApplyColors(BM_Char_PresetTop(p), BM_Char_PresetBot(p), strcat("PRESET: ", BM_Char_PresetName(p)));
			BM_PlaySound("sound/misc/menu2.wav");
		}
	}

	cy = cy + 2 * (ch + gap) + 3;

	// ---- Primary / Armor (Shirt) Color Grid
	pick_top = BM_Char_DrawColorGrid(gx, cy, gw, sh, "ARMOR", g_char_top, clicked);
	if (pick_top >= 0)
		BM_Char_ApplyColors(pick_top, g_char_bot, strcat("ARMOR: ", BM_Char_ColorName(pick_top)));

	cy = cy + 11 + 2 * (sh + 3) + 4;

	// ---- Secondary / Trim (Pants) Color Grid
	pick_bot = BM_Char_DrawColorGrid(gx, cy, gw, sh, "LEGS", g_char_bot, clicked);
	if (pick_bot >= 0)
		BM_Char_ApplyColors(g_char_top, pick_bot, strcat("PANTS: ", BM_Char_ColorName(pick_bot)));

	// ---- Footer Actions: Randomize + Reset
	cy = fy;
	BM_Fill(gx, cy - 3, gw, 1, COL_BORDER, 0.45);
	btn_w = floor((gw - 8) * 0.5);

	hov = BM_Char_Button(gx, cy, btn_w, 17, "RANDOMIZE", FALSE, TRUE);
	if (clicked && hov)
	{
		local float rt, rb;
		g_click_consumed = TRUE;
		rt = modulo(floor(random() * CHAR_COLOR_COUNT), CHAR_COLOR_COUNT);
		rb = modulo(floor(random() * CHAR_COLOR_COUNT), CHAR_COLOR_COUNT);
		BM_Char_ApplyColors(rt, rb, strcat("RANDOM: ", BM_Char_ColorName(rt), " / ", BM_Char_ColorName(rb)));
		BM_PlaySound("sound/misc/menu2.wav");
	}

	hov = BM_Char_Button(gx + btn_w + 8, cy, btn_w, 17, "DEFAULT", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_Char_ApplyColors(3, 1, "RESET TO RANGER DEFAULT");
		BM_PlaySound("sound/misc/menu1.wav");
	}

	BM_DrawTextClipped(gx, cy + 21, gw, g_char_status, 6, COL_MUTED, 0.90, FALSE);
};

// ---------------------------------------------------------------- Hats

string(float h) BM_Char_HatName =
{
	if (h == 1) return "RED FEDORA";
	if (h == 2) return "MAGA CAP";
	if (h == 3) return "WIZARD";
	if (h == 4) return "DISCO AFRO";
	if (h == 5) return "DILDO";
	if (h == 6) return "MEGA MAN";
	if (h == 7) return "GHOST SHEET";
	if (h == 8) return "ABE TOP HAT";
	return "NO HAT";
};

void(float h) BM_Char_PickHat =
{
	cvar_set("bm_hat", ftos(h));
	g_char_status = BM_ZoneSet(g_char_status, strcat("HAT: ", BM_Char_HatName(h)));
	BM_PlaySound("sound/misc/menu2.wav");
};

void(float px, float py, float pw, float ph, float clicked) BM_Char_DrawHatsTab =
{
	local float gx, gw, cy, h, cur, bw, bh, sx, sy, hov, fy;

	gx = px + 14;
	gw = pw - 28;
	cur = floor(cvar("bm_hat"));
	fy = py + ph - 32;

	BM_DrawText(gx, py, "PICK A HAT", 7, COL_MUTED, 0.95);
	cy = py + 11;
	bw = floor((gw - 4) * 0.5);
	bh = bound(12, floor((fy - 8 - cy) / 5) - 3, 24);	// five rows of two
	for (h = 0; h <= CHAR_HAT_COUNT; h = h + 1)
	{
		sx = gx + modulo(h, 2) * (bw + 4);
		sy = cy + floor(h / 2) * (bh + 3);
		hov = BM_Char_Button(sx, sy, bw, bh, BM_Char_HatName(h), (cur == h), FALSE);
		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			BM_Char_PickHat(h);
		}
	}

	BM_Fill(gx, fy - 3, gw, 1, COL_BORDER, 0.45);
	hov = BM_Char_Button(gx, fy, gw, 17, "SURPRISE ME", FALSE, TRUE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_Char_PickHat(1 + modulo(floor(random() * CHAR_HAT_COUNT), CHAR_HAT_COUNT));
	}
	BM_DrawTextClipped(gx, fy + 21, gw, g_char_status, 6, COL_MUTED, 0.90, FALSE);
};

// ---------------------------------------------------------------- Main Page Draw & Input

void(float clicked) BM_Character_Draw =
{
	local float ox, oy, ow, oh, hdr_h, body_y, body_h, vp_x, vp_y, vp_w, vp_h, rp_x, rp_w;
	local float hov, bar_y, bx, bw, i, in_ctrl, tab_x, tab_w, zoom_pct, k, sx;
	local string pname;

	ox = 16;
	oy = 12;
	ow = g_vw - 32;
	oh = g_vh - 24;
	hdr_h = 34;

	body_y = oy + hdr_h + 6;
	body_h = oh - hdr_h - 6;

	vp_x = ox + 4;
	vp_y = body_y;
	vp_w = floor(ow * 0.54) - 6;
	vp_h = body_h - 4;

	rp_x = vp_x + vp_w + 8;
	rp_w = (ox + ow - 4) - rp_x;

	// Draw outer studio frame *around* the 3D viewport rectangle so the CSQC 3D scene stays 100% unobstructed!
	BM_Fill(0, 0, g_vw, vp_y, '0.025 0.02 0.02', 0.94);
	BM_Fill(0, vp_y + vp_h, g_vw, g_vh - (vp_y + vp_h), '0.025 0.02 0.02', 0.94);
	BM_Fill(0, vp_y, vp_x, vp_h, '0.025 0.02 0.02', 0.94);
	BM_Fill(vp_x + vp_w, vp_y, g_vw - (vp_x + vp_w), vp_h, '0.025 0.02 0.02', 0.94);

	// Outer accent bar & border
	BM_Fill(ox, oy, ow, 2, COL_ACCENT_HOT, 0.90);
	BM_Outline(ox, oy, ow, oh, COL_BORDER, 0.75, 1);

	// ---- Header Bar
	BM_Fill(ox + 1, oy + 2, ow - 2, hdr_h - 2, COL_GLASS_DARK, 0.92);
	BM_DrawText(ox + 14, oy + 9, "CHARACTER STUDIO", 13, COL_ACCENT, 0.99);

	pname = cvar_string("_cl_name");
	if (pname == "")
		pname = "player";
	sx = ox + 14 + BM_Char_TextWidth("CHARACTER STUDIO", 13) + 14;
	BM_DrawTextClipped(sx, oy + 12, ox + ow - 128 - sx, strtoupper(BM_SanitizeCmdStr(pname)), 8, COL_TEXT, 0.90, FALSE);

	// Live dual-swatch preview pill in header
	BM_Fill(ox + ow - 120, oy + 8, 12, 9, BM_Char_ColorRGB(g_char_top), 1.0);
	BM_Fill(ox + ow - 120, oy + 17, 12, 9, BM_Char_ColorRGB(g_char_bot), 1.0);
	BM_Outline(ox + ow - 120, oy + 8, 12, 18, COL_ACCENT, 0.90, 1);

	hov = BM_Char_Button(ox + ow - 96, oy + 7, 84, 20, "BACK", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_Character_Close();
		return;
	}

	// ---- Viewport Frame & Interactive Toolbar
	BM_Outline(vp_x, vp_y, vp_w, vp_h, COL_BORDER, 0.85, 1);
	BM_Char_DrawCornerBrackets(vp_x + 5, vp_y + 5, vp_w - 10, vp_h - 10, COL_ACCENT);

	BM_DrawText(vp_x + 12, vp_y + 12, "DRAG TO TURN", 6, COL_ACCENT, 0.92);

	// If studio map is still connecting on first frame, show a clean loading message inside the viewport
	if (clientstate() < CS_CONNECTED)
	{
		BM_Fill(vp_x + 1, vp_y + 1, vp_w - 2, vp_h - 2, '0.04 0.03 0.03', 0.95);
		BM_DrawTextCentered(vp_x + vp_w * 0.5, vp_y + vp_h * 0.5 - 6, "INITIALIZING 3D STUDIO...", 10, COL_ACCENT, 0.96);
	}

	// Bottom viewport control bar (Pose switcher + Spin + Zoom + Reset)
	in_ctrl = FALSE;
	bar_y = vp_y + vp_h - 28;
	BM_Fill(vp_x + 8, bar_y - 3, vp_w - 16, 24, '0.04 0.03 0.03', 0.78);
	BM_Outline(vp_x + 8, bar_y - 3, vp_w - 16, 24, COL_BORDER, 0.65, 1);

	k = min(1, (vp_w - 24) / 285);
	bx = vp_x + 12;
	bw = floor(46 * k);
	for (i = 0; i < CHAR_POSE_COUNT; i = i + 1)
	{
		hov = BM_Char_Button(bx, bar_y, bw, 18, BM_Char_PoseLabel(i), (g_char_pose == i), FALSE);
		if (hov) in_ctrl = TRUE;
		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			g_char_pose = i;
			BM_PlaySound("sound/misc/menu1.wav");
		}
		bx = bx + bw + 3;
	}

	// Right side of viewport toolbar: Spin, Zoom -, Zoom +, Reset
	bx = vp_x + vp_w - 12;

	bx = bx - floor(48 * k);
	hov = BM_Char_Button(bx, bar_y, floor(48 * k), 18, "RESET", FALSE, FALSE);
	if (hov) in_ctrl = TRUE;
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_Char_ResetView();
		BM_PlaySound("sound/misc/menu1.wav");
	}

	bx = bx - floor(22 * k);
	hov = BM_Char_Button(bx, bar_y, floor(19 * k), 18, "+", FALSE, FALSE);
	if (hov) in_ctrl = TRUE;
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_char_target_zoom = bound(0.62, g_char_target_zoom - 0.14, 1.55);
		BM_PlaySound("sound/misc/menu1.wav");
	}

	bx = bx - floor(22 * k);
	hov = BM_Char_Button(bx, bar_y, floor(19 * k), 18, "-", FALSE, FALSE);
	if (hov) in_ctrl = TRUE;
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_char_target_zoom = bound(0.62, g_char_target_zoom + 0.14, 1.55);
		BM_PlaySound("sound/misc/menu1.wav");
	}

	bx = bx - floor(46 * k);
	hov = BM_Char_Button(bx, bar_y, floor(43 * k), 18, g_char_spin ? "SPIN" : "HOLD", g_char_spin, FALSE);
	if (hov) in_ctrl = TRUE;
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_char_spin = !g_char_spin;
		BM_PlaySound("sound/misc/menu1.wav");
	}

	zoom_pct = rint((1.0 / max(0.5, g_char_zoom)) * 100);
	BM_DrawTextRight(vp_x + vp_w - 12, vp_y + 12, strcat("ZOOM ", ftos(zoom_pct), "%"), 6, COL_MUTED, 0.90);

	// Update orbit / inertia / zoom & push exact viewport coordinates to CSQC
	BM_Char_UpdateViewportInput(vp_x, vp_y, vp_w, vp_h, in_ctrl, clicked);

	// ---- Right Customization Dock (Glass Panel + Category Tabs)
	BM_DrawGlassPanel(rp_x, body_y, rp_w, body_h - 4, 0.92, COL_BORDER, 0.80, 2);

	tab_x = rp_x + 12;
	tab_w = 88;
	for (i = 0; i < CHAR_TAB_COUNT; i = i + 1)
	{
		hov = BM_DrawTab(tab_x, body_y + 10, tab_w, 18, BM_Char_TabLabel(i), (g_char_tab == i));
		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			g_char_tab = i;
			BM_PlaySound("sound/misc/menu1.wav");
		}
		tab_x = tab_x + tab_w + 4;
	}
	BM_Fill(rp_x + 12, body_y + 29, rp_w - 24, 1, COL_BORDER, 0.65);

	if (g_char_tab == CHAR_TAB_COLORS)
		BM_Char_DrawColorsTab(rp_x, body_y + 38, rp_w, body_h - 42, clicked);
	else if (g_char_tab == CHAR_TAB_HATS)
		BM_Char_DrawHatsTab(rp_x, body_y + 38, rp_w, body_h - 42, clicked);
};

void(float key, float ascii) BM_Character_KeyDown =
{
	if (key == K_ESCAPE)
	{
		BM_Character_Close();
		return;
	}
	if (key == K_MWHEELUP)
	{
		g_char_target_zoom = bound(0.62, g_char_target_zoom - 0.10, 1.55);
		return;
	}
	if (key == K_MWHEELDOWN)
	{
		g_char_target_zoom = bound(0.62, g_char_target_zoom + 0.10, 1.55);
		return;
	}
	if (key == K_LEFTARROW)
	{
		g_char_vel_yaw = -110;
		return;
	}
	if (key == K_RIGHTARROW)
	{
		g_char_vel_yaw = 110;
		return;
	}
	if (key == K_UPARROW)
	{
		g_char_pitch = bound(-26, g_char_pitch - 6, 42);
		return;
	}
	if (key == K_DOWNARROW)
	{
		g_char_pitch = bound(-26, g_char_pitch + 6, 42);
		return;
	}
	if (key == K_SPACE)
	{
		g_char_spin = !g_char_spin;
		BM_PlaySound("sound/misc/menu1.wav");
		return;
	}
	if (key == K_TAB)
	{
		g_char_pose = modulo(g_char_pose + 1, CHAR_POSE_COUNT);
		BM_PlaySound("sound/misc/menu1.wav");
		return;
	}
};
