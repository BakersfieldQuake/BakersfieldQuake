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

	sz = min(128, max(64, min(px - 18, (g_vw - menu_right) - 18)));
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
	local float cx, top_y, px, mx, my, mw, mh, gap;
	local float in_match, count, i, act, hov, sel;
	local string label, cur_cname;

	in_match = BM_IsInLiveMatch();
	count = BM_Main_RowCount(in_match);

	cx = floor(g_vw * 0.5);
	top_y = max(20, floor((g_vh - 246) * 0.5));

	// Bakersfield Quake top header + classic Quake side plaque
	BM_DrawTextCentered(cx, top_y - 6, "BAKERSFIELD QUAKE", 18, COL_ACCENT, 0.99);
	BM_Fill(cx - 132, top_y + 16, 264, 2, COL_ACCENT_HOT, 0.88);
	BM_Fill(cx - 88, top_y + 18, 176, 1, COL_ACCENT, 0.55);

	px = cx - 144;
	drawpic(px * '1 0 0' + (top_y + 26) * '0 1 0', "gfx/qplaque.lmp", '32 144 0', '1 1 1', 1.0, 0);

	mx = cx - 84;
	mw = 200;
	my = top_y + 40;
	mh = 22;
	gap = 4;

	BM_Main_DrawCast(px, mx + mw, top_y);

	if (g_main_sel >= count) g_main_sel = count - 1;
	if (g_main_sel < 0) g_main_sel = 0;

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

		hov = BM_MouseIn(mx, my, mw, mh);
		if (hov && g_mouse_moved)
			g_main_sel = i;
		sel = (g_main_sel == i && g_focus_input == INPUT_NONE);

		if (sel || hov)
		{
			BM_Fill(mx, my, mw, mh, '0.58 0.08 0.04', 0.78);
			BM_DrawMenuDot(mx - 22, my + 3);
		}
		BM_DrawText(mx + 8, my + 5, label, 12, (sel || hov) ? '1 1 1' : COL_ACCENT, 0.98);

		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			if (g_focus_input == INPUT_PLAYERNAME)
				BM_CommitPlayerName(g_name_buf);
			g_focus_input = INPUT_NONE;
			BM_Main_Execute(act);
			return;
		}
		my = my + mh + gap;
	}

	// Clean inline Player Name row below main items
	my = my + 12;
	BM_DrawText(mx + 8, my + 5, "NAME", 8, COL_MUTED, 0.94);
	if (g_focus_input != INPUT_PLAYERNAME)
	{
		cur_cname = cvar_string("_cl_name");
		if (cur_cname != g_name_buf)
			g_name_buf = BM_ZoneSet(g_name_buf, cur_cname);
	}
	hov = BM_DrawInputBox(mx + 50, my, mw - 50, 18, g_name_buf, "Enter name...", (g_focus_input == INPUT_PLAYERNAME));
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
