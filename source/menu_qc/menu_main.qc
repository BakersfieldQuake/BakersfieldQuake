// BakersfieldQuake MenuQC - Main Menu

float g_main_sel;

float MAIN_ACT_RESUME     = 1;
float MAIN_ACT_JOIN       = 2;
float MAIN_ACT_HOST       = 3;
float MAIN_ACT_OPTIONS    = 4;
float MAIN_ACT_DISCONNECT = 5;
float MAIN_ACT_QUIT       = 6;

void() BM_Browser_Open;
void() BM_Host_Open;
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
	return in_match ? 6 : 4;
};

void(float act) BM_Main_Execute =
{
	BM_PlaySound("sound/misc/menu2.wav");
	if (act == MAIN_ACT_RESUME)
	{
		m_toggle(0);
	}
	else if (act == MAIN_ACT_JOIN)
	{
		BM_Browser_Open();
	}
	else if (act == MAIN_ACT_HOST)
	{
		BM_Host_Open();
	}
	else if (act == MAIN_ACT_OPTIONS)
	{
		BM_Options_Open();
	}
	else if (act == MAIN_ACT_DISCONNECT)
	{
		localcmd("disconnect\n");
	}
	else if (act == MAIN_ACT_QUIT)
	{
		localcmd("quit\n");
	}
};

void(float clicked) BM_Main_Draw =
{
	local float rx, ry, rw, rh, ix, iw, y, bh, gap;
	local float in_match, bg_on, count, i, act, hov;
	local string label, bgmap, status_txt, thumb;
	local vector status_col;
	local float cw, ch, cx, cy, half_w;

	in_match = BM_IsInLiveMatch();
	bg_on = (stof(cvar_string("menu_background")) != 0);

	rx = 18;
	ry = 16;
	rw = bound(216, floor(g_vw * 0.34), 248);
	rh = g_vh - 32;

	BM_DrawGlassPanel(rx, ry, rw, rh, 0.86, COL_BORDER, 0.75, 2.5);

	ix = rx + 12;
	iw = rw - 24;
	y = ry + 14;

	// Hero title
	BM_DrawText(ix, y, "BAKOQUAKE", 16, COL_ACCENT, 0.98);
	y = y + 19;
	BM_DrawTextClipped(ix, y, iw, "BAKERSFIELD LAN // COMBAT+", 8, COL_MUTED, 0.90, FALSE);
	y = y + 13;

	// Status pill
	BM_Fill(ix, y, iw, 17, '0.03 0.04 0.07', 0.88);
	BM_Outline(ix, y, iw, 17, COL_BORDER, 0.48, 1);
	bgmap = BM_CurrentBackdropMap();
	if (in_match)
	{
		local string cmap;
		cmap = BM_CleanMapName(cvar_string("mapname"));
		if (cmap == "") cmap = "match";
		status_col = COL_GOOD;
		status_txt = strcat("IN MATCH: ", strtoupper(cmap));
	}
	else
	{
		status_col = COL_ACCENT;
		status_txt = "READY FOR LAN";
	}
	BM_Fill(ix + 6, y + 6, 5, 5, status_col, 0.95);
	BM_DrawTextClipped(ix + 15, y + 4.5, iw - 20, status_txt, 8, COL_TEXT, 0.92, FALSE);
	y = y + 23;

	// Inline Player Name badge
	BM_DrawText(ix, y, "PLAYER NAME", 8, COL_MUTED, 0.92);
	y = y + 10;
	if (g_focus_input != INPUT_PLAYERNAME)
	{
		local string cur_cname;
		cur_cname = cvar_string("_cl_name");
		if (cur_cname != g_name_buf)
			g_name_buf = BM_ZoneSet(g_name_buf, cur_cname);
	}
	hov = BM_DrawInputBox(ix, y, iw, 19, g_name_buf, "Enter name...", (g_focus_input == INPUT_PLAYERNAME));
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
	y = y + 25;

	// Divider
	BM_Fill(ix, y, iw, 1, COL_BORDER, 0.45);
	y = y + 8;

	// Primary navigation buttons
	count = BM_Main_RowCount(in_match);
	if (g_main_sel >= count)
		g_main_sel = count - 1;
	if (g_main_sel < 0)
		g_main_sel = 0;

	bh = 21;
	gap = 4;
	for (i = 0; i < count; i = i + 1)
	{
		act = BM_Main_RowAction(i, in_match);
		if (act == MAIN_ACT_RESUME) label = "RESUME GAME";
		else if (act == MAIN_ACT_JOIN) label = "JOIN GAME";
		else if (act == MAIN_ACT_HOST) label = "HOST LAN GAME";
		else if (act == MAIN_ACT_OPTIONS) label = "OPTIONS";
		else if (act == MAIN_ACT_DISCONNECT) label = "DISCONNECT";
		else label = "QUIT";

		hov = BM_DrawButton(ix, y, iw, bh, label, (g_main_sel == i && g_focus_input == INPUT_NONE), (act == MAIN_ACT_JOIN && !in_match) || (act == MAIN_ACT_RESUME));
		if (hov && g_mouse_moved)
			g_main_sel = i;
		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			g_focus_input = INPUT_NONE;
			BM_Main_Execute(act);
			return;
		}
		y = y + bh + gap;
	}

	// Bottom quick backdrop controls
	y = ry + rh - 54;
	BM_Fill(ix, y - 7, iw, 1, COL_BORDER, 0.40);
	BM_DrawText(ix, y, "MENU BACKDROP", 8, COL_MUTED, 0.90);
	y = y + 11;

	half_w = floor((iw - 5) * 0.5);
	hov = BM_DrawButton(ix, y, half_w, 18, bg_on ? "BG: ON" : "BG: OFF", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
		cvar_set("menu_background", bg_on ? "0" : "1");
	}

	hov = BM_DrawButton(ix + half_w + 5, y, iw - half_w - 5, 18, "NEXT SCENE", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu2.wav");
		cvar_set("menu_background", "1");
		BM_NextBackdrop();
	}

	BM_DrawTextClipped(ix, ry + rh - 14, iw, "JOIN GAME scans local LAN", 8, COL_MUTED, 0.80, FALSE);

	// Bottom-right floating scene badge when viewing levelshots backdrop
	if (!in_match && bg_on && g_vw >= 520)
	{
		cw = 224;
		ch = 60;
		cx = g_vw - cw - 18;
		cy = g_vh - ch - 18;
		BM_DrawGlassPanel(cx, cy, cw, ch, 0.78, COL_BORDER, 0.65, 0);

		thumb = BM_LevelshotPic(bgmap);
		drawpic((cx + 6) * '1 0 0' + (cy + 7) * '0 1 0', thumb, '72 46 0', '1 1 1', 0.95, 0);
		BM_Outline(cx + 6, cy + 7, 72, 46, COL_BORDER, 0.65, 1);

		BM_DrawTextClipped(cx + 84, cy + 9, cw - 90, "FEATURED MAP", 8, COL_ACCENT, 0.95, FALSE);
		BM_DrawTextClipped(cx + 84, cy + 23, cw - 90, strtoupper(bgmap), 8, COL_TEXT, 0.96, FALSE);
		BM_DrawTextClipped(cx + 84, cy + 38, cw - 90, "Bakersfield Maps", 8, COL_MUTED, 0.88, FALSE);
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
		BM_CommitPlayerName(g_name_buf);
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
