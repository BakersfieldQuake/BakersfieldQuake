// BakersfieldQuake MenuQC - Host LAN Game

float HOST_MAP_COUNT = 8;
float HOST_DBLCLICK_TIME = 0.5;

float g_host_map_idx;
float g_host_scroll;
float g_host_frag_idx;
float g_host_time_idx;
float g_host_maxp_idx;
float g_host_bots;
float g_host_public;
float g_host_last_click_idx;
float g_host_last_click_time;

string(float i) BM_Host_MapBsp =
{
	if (i == 0)  return "soi6";
	if (i == 1)  return "soicowboy_bkk";
	if (i == 2)  return "bakersfielddowntown";
	if (i == 3)  return "morrorock";
	if (i == 4)  return "bklan6";
	if (i == 5)  return "spruce";
	if (i == 6)  return "dm6";
	return "practice";
};

string(float i) BM_Host_MapTitle =
{
	if (i == 0)  return "Soi 6";
	if (i == 1)  return "Soi Cowboy BKK";
	if (i == 2)  return "Bakersfield Downtown";
	if (i == 3)  return "Morro Rock";
	if (i == 4)  return "BKLAN 6";
	if (i == 5)  return "Spruce";
	if (i == 6)  return "DM6";
	return "Practice Range";
};

float(float idx) BM_Host_FragVal =
{
	if (idx <= 0) return 0;
	if (idx == 1) return 10;
	if (idx == 2) return 15;
	if (idx == 3) return 20;
	if (idx == 4) return 25;
	if (idx == 5) return 30;
	if (idx == 6) return 50;
	if (idx == 7) return 75;
	return 100;
};

float(float idx) BM_Host_TimeVal =
{
	if (idx <= 0) return 0;
	if (idx == 1) return 5;
	if (idx == 2) return 10;
	if (idx == 3) return 15;
	if (idx == 4) return 20;
	if (idx == 5) return 30;
	if (idx == 6) return 45;
	return 60;
};

float(float idx) BM_Host_MaxpVal =
{
	if (idx <= 0) return 2;
	if (idx == 1) return 4;
	if (idx == 2) return 6;
	if (idx == 3) return 8;
	if (idx == 4) return 12;
	return 16;
};

void() BM_Host_Open =
{
	local string cur_host;

	g_page = PAGE_HOST;
	g_focus_input = INPUT_NONE;
	g_host_scroll = 0;
	g_host_last_click_idx = -1;
	g_host_last_click_time = 0;

	if (g_host_frag_idx == 0 && g_host_time_idx == 0 && g_host_maxp_idx == 0)
	{
		g_host_frag_idx = 4; // 25 frags
		g_host_time_idx = 3; // 15 min
		g_host_maxp_idx = 5; // 16 players
		g_host_bots = max(0, min(12, rint(stof(cvar_string("bm_botfill")))));
		g_host_public = 0;
	}

	cur_host = cvar_string("hostname");
	if (cur_host == "" || strtolower(cur_host) == "unnamed")
		cur_host = "Bakersfield LAN";
	if (g_host_buf == "")
		g_host_buf = BM_ZoneSet(g_host_buf, cur_host);
};

void() BM_Host_StartMatch =
{
	local string bsp, hname, cmd;
	local float fl, tl, mp;

	g_host_last_click_idx = -1;
	g_host_last_click_time = 0;

	bsp = BM_Host_MapBsp(g_host_map_idx);
	hname = BM_SanitizeCmdStr(g_host_buf);
	if (hname == "")
		hname = "Bakersfield LAN";
	fl = BM_Host_FragVal(g_host_frag_idx);
	tl = BM_Host_TimeVal(g_host_time_idx);
	mp = BM_Host_MaxpVal(g_host_maxp_idx);

	BM_PlaySound("sound/misc/menu2.wav");
	BM_Loading_Begin(bsp, BM_Host_MapTitle(g_host_map_idx), "HOSTING LAN");
	cvar_set("bm_menu_bg", "0");
	m_toggle(0);

	cmd = strcat("set bm_menu_bg 0; deathmatch 1; coop 0; ctf 0; sv_public ", ftos(g_host_public));
	// No longer turns sv_autodemo_perclient on (it is saved and was never turned off;
	// it filled demos/ with per-client files named with player addresses). Only the
	// name format is kept so demos recorded when it is enabled elsewhere still parse.
	cmd = strcat(cmd, "; sv_autodemo_perclient_nameformat \"demos/%Y-%m-%d_%H-%M\"");
	cmd = strcat(cmd, "; hostname \"", hname, "\"; fraglimit ", ftos(fl), "; timelimit ", ftos(tl));
	cmd = strcat(cmd, "; maxplayers ", ftos(mp), "; bm_botfill ", ftos(g_host_bots), "; map ", bsp, "\n");
	localcmd(cmd);
};

void(float clicked) BM_Host_Draw =
{
	local float px, py, pw, ph, gx, gy, gw, gh, sx, sw;
	local float cols, cw, ch, gap_x, gap_y, rows, vis_rows, max_scroll;
	local float i, r, c, cx, cy, hov, sel, sb_h, sb_y, tw, th;
	local float y, st, fl, tl, mp, now;
	local string bsp, title, thumb, s_val;
	local vector brd, bg;

	px = 20;
	py = 16;
	pw = g_vw - 40;
	ph = g_vh - 32;

	BM_DrawGlassPanel(px, py, pw, ph, 0.88, COL_BORDER, 0.78, 2.5);

	// Header
	BM_DrawText(px + 14, py + 11, "BAKERSFIELD QUAKE", 12, COL_ACCENT, 0.98);
	BM_DrawText(px + 228, py + 14, "HOST LAN GAME", 9, COL_TEXT, 0.92);
	BM_DrawTextClipped(px + 356, py + 14, pw - 432, "Double-click a map to start", 8, COL_MUTED, 0.92, FALSE);

	hov = BM_DrawButton(px + pw - 66, py + 9, 54, 18, "BACK", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu3.wav");
		g_focus_input = INPUT_NONE;
		g_page = PAGE_MAIN;
		return;
	}

	// Left Map Thumbnail Grid
	sw = bound(190, floor(pw * 0.35), 224);
	gx = px + 14;
	gy = py + 38;
	gw = pw - sw - 38;
	gh = ph - 50;

	cols = 3;
	gap_x = 7;
	gap_y = 7;
	cw = floor((gw - gap_x * (cols - 1)) / cols);
	th = floor(cw * 0.56); // compact 16:9-ish thumbnail so 3 full rows fit cleanly
	ch = th + 17;

	vis_rows = max(1, floor((gh + gap_y) / (ch + gap_y)));
	rows = ceil(HOST_MAP_COUNT / cols);
	max_scroll = max(0, rows - vis_rows);
	g_host_scroll = bound(0, g_host_scroll, max_scroll);

	BM_BeginClip(gx, gy, gw, gh);
	for (i = 0; i < HOST_MAP_COUNT; i = i + 1)
	{
		r = floor(i / cols) - g_host_scroll;
		c = modulo(i, cols);
		if (r >= 0 && r < vis_rows + 1)
		{
			cx = gx + c * (cw + gap_x);
			cy = gy + r * (ch + gap_y);
			if (cy + ch <= gy + gh + 6)
			{
				bsp = BM_Host_MapBsp(i);
				title = BM_Host_MapTitle(i);
				thumb = BM_LevelshotPic(bsp);
				sel = (g_host_map_idx == i);
				hov = BM_MouseIn(cx, cy, cw, ch);

				bg = sel ? '0.18 0.14 0.05' : (hov ? COL_GLASS_HOVER : COL_GLASS_CARD);
				brd = sel ? COL_ACCENT : (hov ? '0.60 0.72 0.88' : COL_BORDER);
				BM_Fill(cx, cy, cw, ch, bg, 0.90);
				BM_Outline(cx, cy, cw, ch, brd, sel ? 0.98 : 0.58, sel ? 1.5 : 1);

				drawpic((cx + 3) * '1 0 0' + (cy + 3) * '0 1 0', thumb, (cw - 6) * '1 0 0' + (th - 3) * '0 1 0', '1 1 1', 0.98, 0);
				BM_DrawTextClipped(cx + 4, cy + th + 4, cw - 8, title, 8, sel ? COL_ACCENT : COL_TEXT, 0.96, FALSE);

				if (clicked && hov)
				{
					g_click_consumed = TRUE;
					g_host_map_idx = i;
					now = gettime();
					if (g_host_last_click_idx == i && now >= g_host_last_click_time && (now - g_host_last_click_time) <= HOST_DBLCLICK_TIME)
					{
						BM_EndClip();
						BM_Host_StartMatch();
						return;
					}
					g_host_last_click_idx = i;
					g_host_last_click_time = now;
					BM_PlaySound("sound/misc/menu1.wav");
				}
			}
		}
	}
	BM_EndClip();
	if (clicked && !g_click_consumed)
	{
		g_host_last_click_idx = -1;
		g_host_last_click_time = 0;
	}

	if (max_scroll > 0)
	{
		BM_Fill(gx + gw + 4, gy, 4, gh, '0.03 0.04 0.07', 0.85);
		sb_h = max(18, gh * (vis_rows / rows));
		sb_y = gy + (gh - sb_h) * (g_host_scroll / max_scroll);
		BM_Fill(gx + gw + 4, sb_y, 4, sb_h, COL_ACCENT, 0.85);
	}

	// Right Sidebar: Selected Map + Match Settings
	sx = px + pw - sw - 14;
	y = gy;
	BM_Fill(sx, y, sw, gh, '0.04 0.06 0.10', 0.72);
	BM_Outline(sx, y, sw, gh, COL_BORDER, 0.55, 1);

	bsp = BM_Host_MapBsp(g_host_map_idx);
	title = BM_Host_MapTitle(g_host_map_idx);
	thumb = BM_LevelshotPic(bsp);
	tw = sw - 14;
	th = min(74, floor(tw * 0.50));

	drawpic((sx + 7) * '1 0 0' + (y + 7) * '0 1 0', thumb, tw * '1 0 0' + th * '0 1 0', '1 1 1', 0.98, 0);
	BM_Outline(sx + 7, y + 7, tw, th, COL_ACCENT, 0.72, 1);
	BM_Fill(sx + 7, y + 7 + th - 16, tw, 16, '0.02 0.03 0.05', 0.84);
	BM_DrawTextClipped(sx + 11, y + 7 + th - 12, tw - 8, strtoupper(bsp), 8, COL_ACCENT, 0.98, FALSE);
	y = y + th + 12;

	// Server hostname
	BM_DrawText(sx + 7, y, "SERVER NAME", 8, COL_MUTED, 0.92);
	y = y + 10;
	hov = BM_DrawInputBox(sx + 7, y, sw - 14, 18, g_host_buf, "Bakersfield LAN", (g_focus_input == INPUT_HOSTNAME));
	if (clicked && hov)
	{
		g_focus_input = INPUT_HOSTNAME;
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	else if (clicked && g_focus_input == INPUT_HOSTNAME && !hov)
	{
		g_focus_input = INPUT_NONE;
	}
	y = y + 23;

	// Fraglimit
	fl = BM_Host_FragVal(g_host_frag_idx);
	s_val = (fl == 0) ? "None" : ftos(fl);
	st = BM_DrawStepper(sx + 7, y, sw - 14, 19, "FRAGLIMIT", s_val, FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		g_host_frag_idx = bound(0, g_host_frag_idx + st, 8);
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 23;

	// Timelimit
	tl = BM_Host_TimeVal(g_host_time_idx);
	s_val = (tl == 0) ? "None" : strcat(ftos(tl), "m");
	st = BM_DrawStepper(sx + 7, y, sw - 14, 19, "TIMELIMIT", s_val, FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		g_host_time_idx = bound(0, g_host_time_idx + st, 7);
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 23;

	// Maxplayers
	mp = BM_Host_MaxpVal(g_host_maxp_idx);
	st = BM_DrawStepper(sx + 7, y, sw - 14, 19, "MAXPLAYERS", ftos(mp), FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		g_host_maxp_idx = bound(0, g_host_maxp_idx + st, 5);
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 23;

	// Bot Fill (bm_botfill)
	st = BM_DrawStepper(sx + 7, y, sw - 14, 19, "BOT FILL", (g_host_bots == 0) ? "Off" : ftos(g_host_bots), FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		g_host_bots = bound(0, g_host_bots + st, 12);
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 23;

	// LAN vs Public toggle
	st = BM_DrawStepper(sx + 7, y, sw - 14, 19, "VISIBILITY", g_host_public ? "Public" : "LAN", FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		g_host_public = !g_host_public;
		BM_PlaySound("sound/misc/menu1.wav");
	}

	// Start LAN Match CTA
	hov = BM_DrawButton(sx + 7, gy + gh - 28, sw - 14, 22, "START LAN MATCH", FALSE, TRUE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_Host_StartMatch();
	}
};

float() BM_Host_VisRows =
{
	local float pw, ph, sw, gw, gh, cw, th, ch;

	pw = g_vw - 40;
	ph = g_vh - 32;
	sw = bound(190, floor(pw * 0.35), 224);
	gw = pw - sw - 38;
	gh = ph - 50;
	cw = floor((gw - 14) / 3);
	th = floor(cw * 0.56);
	ch = th + 17;
	return max(1, floor((gh + 7) / (ch + 7)));
};

void() BM_Host_EnsureVisible =
{
	local float row, vis_rows, rows, max_scroll;

	row = floor(g_host_map_idx / 3);
	vis_rows = BM_Host_VisRows();
	rows = ceil(HOST_MAP_COUNT / 3);
	max_scroll = max(0, rows - vis_rows);
	if (row < g_host_scroll)
		g_host_scroll = row;
	else if (row >= g_host_scroll + vis_rows)
		g_host_scroll = row - vis_rows + 1;
	g_host_scroll = bound(0, g_host_scroll, max_scroll);
};

void(float key, float ascii) BM_Host_KeyDown =
{
	g_host_last_click_idx = -1;
	g_host_last_click_time = 0;

	if (g_focus_input == INPUT_HOSTNAME)
	{
		if (key == K_ESCAPE || key == K_ENTER || key == K_KP_ENTER || key == K_TAB)
		{
			g_focus_input = INPUT_NONE;
			return;
		}
		g_host_buf = BM_ZoneSet(g_host_buf, BM_EditString(g_host_buf, 28, key, ascii, TRUE));
		return;
	}

	if (key == K_ESCAPE)
	{
		BM_PlaySound("sound/misc/menu3.wav");
		g_page = PAGE_MAIN;
	}
	else if (key == K_MWHEELUP || key == K_PGUP)
	{
		g_host_scroll = max(0, g_host_scroll - 1);
	}
	else if (key == K_MWHEELDOWN || key == K_PGDN)
	{
		g_host_scroll = g_host_scroll + 1;
	}
	else if (key == K_LEFTARROW)
	{
		g_host_map_idx = max(0, g_host_map_idx - 1);
		BM_Host_EnsureVisible();
	}
	else if (key == K_RIGHTARROW)
	{
		g_host_map_idx = min(HOST_MAP_COUNT - 1, g_host_map_idx + 1);
		BM_Host_EnsureVisible();
	}
	else if (key == K_UPARROW)
	{
		g_host_map_idx = max(0, g_host_map_idx - 3);
		BM_Host_EnsureVisible();
	}
	else if (key == K_DOWNARROW)
	{
		g_host_map_idx = min(HOST_MAP_COUNT - 1, g_host_map_idx + 3);
		BM_Host_EnsureVisible();
	}
	else if (key == K_ENTER || key == K_KP_ENTER)
	{
		BM_Host_StartMatch();
	}
};
