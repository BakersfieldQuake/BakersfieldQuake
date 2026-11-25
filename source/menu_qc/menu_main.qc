// BakersfieldQuake MenuQC - Classic Default Quake Main Menu + Join/Host Game

float g_main_sel;

float MAIN_ACT_RESUME     = 1;
float MAIN_ACT_JOIN       = 2;
float MAIN_ACT_HOST       = 3;
float MAIN_ACT_REPLAYS    = 4;
float MAIN_ACT_OPTIONS    = 5;
float MAIN_ACT_DISCONNECT = 6;
float MAIN_ACT_QUIT       = 7;

void() BM_Browser_Open;
void() BM_Host_Open;
void() BM_Replays_Open;
void() BM_Options_Open;

void(string newname) BM_CommitPlayerName =
{
	local string clean;

	clean = BM_SanitizeCmdStr(newname);
	if (clean == "")
		clean = "player";
	g_name_buf = BM_ZoneSet(g_name_buf, clean);
	cvar_set("_cl_name", clean);
	localcmd(strcat("name \"", clean, "\"\n"));
};

float(float idx, float in_match) BM_Main_RowAction =
{
	local float row;

	row = 0;
	if (in_match)
	{
		if (idx == row) return MAIN_ACT_RESUME;
		row = row + 1;
	}
	if (idx == row) return MAIN_ACT_JOIN;
	row = row + 1;
	if (idx == row) return MAIN_ACT_HOST;
	row = row + 1;
	if (idx == row) return MAIN_ACT_REPLAYS;
	row = row + 1;
	if (idx == row) return MAIN_ACT_OPTIONS;
	row = row + 1;
	if (in_match)
	{
		if (idx == row) return MAIN_ACT_DISCONNECT;
		row = row + 1;
	}
	if (idx == row) return MAIN_ACT_QUIT;
	return 0;
};

float(float in_match) BM_Main_RowCount =
{
	return in_match ? 7 : 5;
};

void(float act) BM_Main_Execute =
{
	BM_PlaySound("sound/misc/menu2.wav");
	if (act == MAIN_ACT_RESUME)
		m_toggle(0);
	else if (act == MAIN_ACT_JOIN)
		BM_Browser_Open();
	else if (act == MAIN_ACT_HOST)
		BM_Host_Open();
	else if (act == MAIN_ACT_REPLAYS)
		BM_Replays_Open();
	else if (act == MAIN_ACT_OPTIONS)
		BM_Options_Open();
	else if (act == MAIN_ACT_DISCONNECT)
		localcmd("disconnect\n");
	else if (act == MAIN_ACT_QUIT)
		localcmd("quit\n");
};

string(float idx) BM_CastPic =
{
	if (idx == 0) return "gfx/menu_cast/greenguy.png";
	if (idx == 1) return "gfx/menu_cast/wheelman.png";
	if (idx == 2) return "gfx/menu_cast/bryan.png";
	if (idx == 3) return "gfx/menu_cast/david.png";
	if (idx == 4) return "gfx/menu_cast/daniel.png";
	if (idx == 5) return "gfx/menu_cast/beerguy.png";
	if (idx == 6) return "gfx/menu_cast/reeseice.png";
	if (idx == 7) return "gfx/menu_cast/rogerver.png";
	if (idx == 8) return "gfx/menu_cast/robeguy.png";
	return "gfx/menu_cast/jesskart.png";
};

string(float idx) BM_CastName =
{
	if (idx == 0) return "GREEN MAN";
	if (idx == 1) return "WHEELMAN";
	if (idx == 2) return "BRYAN";
	if (idx == 3) return "DAVID";
	if (idx == 4) return "DANIEL";
	if (idx == 5) return "BEER GUY";
	if (idx == 6) return "REESE ICE";
	if (idx == 7) return "ROGER VER";
	if (idx == 8) return "ROBE GUY";
	return "JESS KART";
};

float(float avoid_a, float avoid_b) BM_PickRandomCast =
{
	local float pick, guard;

	pick = modulo(floor(random() * CAST_COUNT), CAST_COUNT);
	guard = 0;
	while ((pick == avoid_a || pick == avoid_b) && guard < 16)
	{
		pick = modulo(pick + 1 + floor(random() * (CAST_COUNT - 1)), CAST_COUNT);
		guard = guard + 1;
	}
	return pick;
};

void(float idx, float cx, float top_y, float sz, float dir_col, float anim_row) BM_DrawCastSlot =
{
	local float dx, dy;
	local string pic, cname;

	dx = floor(cx - sz * 0.5);
	dy = floor(top_y);
	pic = BM_CastPic(idx);
	cname = BM_CastName(idx);

	BM_Fill(dx + floor(sz * 0.14), dy + sz - 10, floor(sz * 0.72), 8, '0.02 0.01 0.01', 0.42);

	drawsetcliparea(dx, dy, sz, sz);
	drawpic((dx - dir_col * sz) * '1 0 0' + (dy - anim_row * sz) * '0 1 0', pic, (sz * 8) * '1 0 0' + (sz * 6) * '0 1 0', '1 1 1', 1.0, 0);
	drawresetcliparea();

	BM_DrawTextCentered(cx, dy + sz + 4, cname, 8, COL_ACCENT, 0.92);
};

void(float px, float menu_right, float top_y) BM_Main_DrawCast =
{
	local float t, phase, dir_col, anim_row, sz, lx_c, rx_c, sy;

	t = gettime();
	if (g_cast_next_swap <= 0)
	{
		g_cast_left = 0;
		g_cast_right = BM_PickRandomCast(0, -1);
		g_cast_swap_start = t;
		g_cast_next_swap = t + 10.0;
	}
	else if (t >= g_cast_next_swap)
	{
		g_cast_left = BM_PickRandomCast(g_cast_left, -1);
		g_cast_right = BM_PickRandomCast(g_cast_left, g_cast_right);
		g_cast_swap_start = t;
		g_cast_next_swap = t + 10.0;
	}

	phase = bound(0, (t - g_cast_swap_start) / 10.0, 0.9999);
	dir_col = modulo(floor(phase * 8), 8);
	anim_row = modulo(floor(t * 7.5), 6);

	sz = min(128, min(px - 18, (g_vw - menu_right) - 18));
	if (sz < 64)
		return;

	lx_c = floor(px * 0.5);
	rx_c = floor((menu_right + g_vw) * 0.5);
	sy = top_y + 38;

	BM_DrawCastSlot(g_cast_left, lx_c, sy, sz, dir_col, anim_row);
	BM_DrawCastSlot(g_cast_right, rx_c, sy, sz, dir_col, anim_row);
};

void(float clicked) BM_Main_Draw =
{
	local float cx, pw, px, py, ph, pad_top, sub_h, rh, gap, rows_h, pad_mid, name_h, pad_bot;
	local float qp_h, qp_w, rx, rw, my, in_match, count, i, act, hov, sel, f_dot;
	local string label, cur_cname, ver_str, dot_pic;

	in_match = BM_IsInLiveMatch();
	count = BM_Main_RowCount(in_match);

	cx = floor(g_vw * 0.5);

	// On launch (disconnected), display the borderless 1992 SNES Grand Prix artwork full-screen
	if (!in_match && getimagesize("gfx/loading/main_menu_bg.png") != '0 0 0')
		drawpic('0 0 0', "gfx/loading/main_menu_bg.png", g_vw * '1 0 0' + g_vh * '0 1 0', '1 1 1', 1.0, 0);

	pw = bound(210, floor(g_vw * 0.34), g_vw - 76);
	px = floor((g_vw - pw) * 0.5);
	pad_top = 6;
	sub_h = 12;
	rh = in_match ? 17 : 18;
	gap = 3;
	rows_h = count * rh + max(0, count - 1) * gap;
	pad_mid = 6;
	name_h = 18;
	pad_bot = 6;
	ph = pad_top + sub_h + 5 + rows_h + pad_mid + name_h + pad_bot;

	if (!in_match && getimagesize("gfx/loading/main_menu_bg.png") != '0 0 0')
		py = floor(g_vh * 0.955) - ph;
	else
	{
		py = max(48, floor((g_vh - ph) * 0.5) + 12);
		BM_DrawTextCentered(cx, py - 28, "BAKERSFIELD QUAKE", 18, COL_ACCENT, 0.99);
		BM_Fill(cx - 132, py - 8, 264, 2, COL_ACCENT_HOT, 0.88);
		BM_Fill(cx - 88, py - 6, 176, 1, COL_ACCENT, 0.55);
	}

	// Classic Quake side plaque scaled cleanly beside the Grand Prix SNES box
	qp_h = min(136, max(48, ph - 8));
	qp_w = max(14, floor(qp_h * (32 / 144)));
	drawpic((px - qp_w - 5) * '1 0 0' + (py + floor((ph - qp_h) * 0.5)) * '0 1 0', "gfx/qplaque.lmp", qp_w * '1 0 0' + qp_h * '0 1 0', '1 1 1', 1.0, 0);

	// SNES Grand Prix beveled gold-and-espresso cartridge plaque
	BM_Fill(px, py, pw, ph, '0.07 0.045 0.035', 0.92);
	BM_Outline(px, py, pw, ph, '0.84 0.59 0.21', 0.96, 1.5);
	BM_Outline(px + 2, py + 2, pw - 4, ph - 4, '0.30 0.14 0.05', 0.90, 1.0);
	BM_Fill(px + 2, py + 1.5, pw - 4, 1.5, '1.0 0.88 0.58', 0.55);

	ver_str = cvar_string("showdate_format");
	if (ver_str == "" || ver_str == "0")
		ver_str = "DEV";
	BM_DrawText(px + 8, py + pad_top, in_match ? "MATCH PAUSED" : "1P / LAN GRAND PRIX", 7, COL_ACCENT, 0.95);
	BM_DrawTextRight(px + pw - 8, py + pad_top, ver_str, 7, COL_MUTED, 0.90);
	BM_Fill(px + 6, py + pad_top + sub_h, pw - 12, 1, '0.84 0.59 0.21', 0.42);

	rx = px + 8;
	rw = pw - 16;
	my = py + pad_top + sub_h + 5;

	if (g_main_sel >= count) g_main_sel = count - 1;
	if (g_main_sel < 0) g_main_sel = 0;

	f_dot = 1 + modulo(floor(gettime() * 10), 6);
	dot_pic = strcat("gfx/menudot", ftos(f_dot), ".lmp");

	for (i = 0; i < count; i = i + 1)
	{
		act = BM_Main_RowAction(i, in_match);
		if (act == MAIN_ACT_RESUME) label = "RESUME GAME";
		else if (act == MAIN_ACT_JOIN) label = "JOIN GAME";
		else if (act == MAIN_ACT_HOST) label = "HOST GAME";
		else if (act == MAIN_ACT_REPLAYS) label = "REPLAYS";
		else if (act == MAIN_ACT_OPTIONS) label = "OPTIONS";
		else if (act == MAIN_ACT_DISCONNECT) label = "DISCONNECT";
		else label = "QUIT";

		hov = BM_MouseIn(rx, my, rw, rh);
		if (hov && g_mouse_moved)
			g_main_sel = i;
		sel = (g_main_sel == i && g_focus_input == INPUT_NONE);

		if (sel || hov)
		{
			BM_Fill(rx, my, rw, rh, '0.58 0.09 0.04', 0.88);
			BM_Outline(rx, my, rw, rh, COL_ACCENT, 0.72, 1.0);
			drawpic((rx + 4) * '1 0 0' + (my + floor((rh - 12) * 0.5)) * '0 1 0', dot_pic, '12 12 0', '1 1 1', 1.0, 0);
		}
		else
		{
			BM_Fill(rx, my, rw, rh, '0.12 0.08 0.06', 0.52);
		}
		BM_DrawText(rx + 20, my + floor((rh - 10) * 0.5), label, 10, (sel || hov) ? '1 1 1' : COL_ACCENT, 0.98);

		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			if (g_focus_input == INPUT_PLAYERNAME)
				BM_CommitPlayerName(g_name_buf);
			g_focus_input = INPUT_NONE;
			BM_Main_Execute(act);
			return;
		}
		my = my + rh + gap;
	}

	// Clean inline Player Name row at bottom of plaque
	my = my + (pad_mid - gap);
	BM_Fill(px + 6, my - 3, pw - 12, 1, '0.84 0.59 0.21', 0.35);
	BM_DrawText(rx + 2, my + 5, "NAME", 7.5, COL_MUTED, 0.95);
	if (g_focus_input != INPUT_PLAYERNAME)
	{
		cur_cname = cvar_string("_cl_name");
		if (cur_cname != g_name_buf)
			g_name_buf = BM_ZoneSet(g_name_buf, cur_cname);
	}
	hov = BM_DrawInputBox(rx + 40, my, rw - 40, name_h, g_name_buf, "Enter name...", (g_focus_input == INPUT_PLAYERNAME));
	if (clicked && hov)
	{
		g_focus_input = INPUT_PLAYERNAME;
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	else if (clicked && g_focus_input == INPUT_PLAYERNAME && !hov)
	{
		g_focus_input = INPUT_NONE;
		BM_CommitPlayerName(g_name_buf);
	}
};

void(float key, float ascii) BM_Main_KeyDown =
{
	local float in_match, count, act;

	if (g_focus_input == INPUT_PLAYERNAME)
	{
		if (key == K_ESCAPE || key == K_ENTER || key == K_KP_ENTER || key == K_TAB)
		{
			g_focus_input = INPUT_NONE;
			BM_CommitPlayerName(g_name_buf);
			BM_PlaySound("sound/misc/menu1.wav");
			return;
		}
		g_name_buf = BM_ZoneSet(g_name_buf, BM_EditString(g_name_buf, 22, key, ascii, TRUE));
		return;
	}

	in_match = BM_IsInLiveMatch();
	count = BM_Main_RowCount(in_match);

	if (key == K_UPARROW)
	{
		g_main_sel = modulo(g_main_sel - 1 + count, count);
		BM_PlaySound("sound/misc/menu1.wav");
	}
	else if (key == K_DOWNARROW)
	{
		g_main_sel = modulo(g_main_sel + 1, count);
		BM_PlaySound("sound/misc/menu1.wav");
	}
	else if (key == K_ENTER || key == K_KP_ENTER)
	{
		act = BM_Main_RowAction(g_main_sel, in_match);
		if (act > 0)
			BM_Main_Execute(act);
	}
	else if (key == K_ESCAPE)
	{
		if (in_match)
		{
			BM_PlaySound("sound/misc/menu3.wav");
			m_toggle(0);
		}
	}
};
