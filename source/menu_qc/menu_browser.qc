// BakersfieldQuake MenuQC - Join Game (LAN & Online Server Browser)

float TAB_LAN    = 0;
float TAB_ONLINE = 1;
float TAB_ALL    = 2;

string BAKO_ONLINE_ADDR = "72.62.241.93:26000";

float g_br_tab;
float g_br_sel;
float g_br_scroll;
float g_br_count;
float g_br_indices[256];
float g_br_next_rebuild;
float g_br_pinned_live;

void(string addr) BM_ConnectTo =
{
	local string clean;

	clean = BM_SanitizeCmdStr(addr);
	if (clean == "")
		return;
	BM_PlaySound("sound/misc/menu2.wav");
	if (!g_load_active)
		BM_Loading_Begin("", clean, "JOINING SERVER");
	cvar_set("bm_menu_bg", "0");
	m_toggle(0);
	localcmd(strcat("set bm_menu_bg 0; connect ", clean, "\n"));
};

float(string cname) BM_IsLanAddr =
{
	local float dot2, oct2;

	if (cname == "")
		return FALSE;
	if (strncmp(cname, "10.", 3) == 0)
		return TRUE;
	if (strncmp(cname, "192.168.", 8) == 0)
		return TRUE;
	if (strncmp(cname, "127.", 4) == 0)
		return TRUE;
	if (strncasecmp(cname, "localhost", 9) == 0)
		return TRUE;
	if (strncmp(cname, "[::1]", 5) == 0)
		return TRUE;
	if (strncmp(cname, "172.", 4) == 0)
	{
		dot2 = strstrofs(cname, ".", 4);
		if (dot2 > 4 && dot2 <= 6)
		{
			oct2 = stof(substring(cname, 4, dot2 - 4));
			if (oct2 >= 16 && oct2 <= 31)
				return TRUE;
		}
	}
	return FALSE;
};

void() BM_EnsureOnlineFavorite =
{
	local string favs;

	favs = cvar_string("net_slist_favorites");
	if (strstrofs(favs, BAKO_ONLINE_ADDR) < 0)
	{
		if (favs == "")
			cvar_set("net_slist_favorites", BAKO_ONLINE_ADDR);
		else
			cvar_set("net_slist_favorites", strcat(favs, " ", BAKO_ONLINE_ADDR));
	}
};

void() BM_InitServerListKeys =
{
	local float k;

	addwantedserverlistkey("cname");
	addwantedserverlistkey("ping");
	addwantedserverlistkey("map");
	addwantedserverlistkey("name");
	addwantedserverlistkey("maxplayers");
	addwantedserverlistkey("numplayers");
	addwantedserverlistkey("numbots");
	addwantedserverlistkey("isfavorite");

	k = getserverlistindexforkey("cname");      if (k >= 0) SLIST_CNAME = k;
	k = getserverlistindexforkey("ping");       if (k >= 0) SLIST_PING = k;
	k = getserverlistindexforkey("game");       if (k >= 0) SLIST_GAME = k;
	k = getserverlistindexforkey("mod");        if (k >= 0) SLIST_MOD = k;
	k = getserverlistindexforkey("map");        if (k >= 0) SLIST_MAP = k;
	k = getserverlistindexforkey("name");       if (k >= 0) SLIST_NAME = k;
	k = getserverlistindexforkey("maxplayers"); if (k >= 0) SLIST_MAXPLAYERS = k;
	k = getserverlistindexforkey("numplayers"); if (k >= 0) SLIST_NUMPLAYERS = k;
	k = getserverlistindexforkey("numbots");    if (k >= 0) SLIST_NUMBOTS = k;
	k = getserverlistindexforkey("isfavorite"); if (k >= 0) SLIST_ISFAVORITE = k;
};

void() BM_Browser_Refresh =
{
	BM_EnsureOnlineFavorite();
	if (stof(cvar_string("net_slist_timeout")) > 1.5)
		cvar_set("net_slist_timeout", "1.5");
	resetserverlistmasks();
	if (SLIST_PING >= 0)
		setserverlistsort(SLIST_PING, 0);
	refreshserverlist(1);
	g_br_next_rebuild = 0;
};

void() BM_Browser_Open =
{
	g_page = PAGE_BROWSER;
	g_focus_input = INPUT_NONE;
	g_br_tab = TAB_LAN;
	g_br_sel = 0;
	g_br_scroll = 0;
	if (g_ip_buf == "")
		g_ip_buf = BM_ZoneSet(g_ip_buf, BAKO_ONLINE_ADDR);
	BM_Browser_Refresh();
};

void() BM_Browser_Rebuild =
{
	local float total, i, islan, include_srv;
	local string cname;

	resortserverlist();
	total = getserverliststat(SLSTAT_VIEWCOUNT);
	g_br_count = 0;
	g_br_pinned_live = FALSE;

	// First check whether pinned Bakersfield Online has already replied
	for (i = 0; i < total; i = i + 1)
	{
		cname = getserverliststring(SLIST_CNAME, i);
		if (cname == BAKO_ONLINE_ADDR)
		{
			g_br_pinned_live = TRUE;
			break;
		}
	}

	// Pin Bakersfield Online at top of Online/All if not yet in hostcache
	if (!g_br_pinned_live && (g_br_tab == TAB_ONLINE || g_br_tab == TAB_ALL))
	{
		g_br_indices[g_br_count] = -1;
		g_br_count = g_br_count + 1;
	}

	for (i = 0; i < total && g_br_count < 256; i = i + 1)
	{
		cname = getserverliststring(SLIST_CNAME, i);
		if (cname == "")
			continue;
		islan = BM_IsLanAddr(cname);

		if (g_br_tab == TAB_LAN)
			include_srv = islan;
		else if (g_br_tab == TAB_ONLINE)
			include_srv = !islan;
		else
			include_srv = TRUE;

		if (include_srv)
		{
			g_br_indices[g_br_count] = i;
			g_br_count = g_br_count + 1;
		}
	}

	if (g_br_sel >= g_br_count)
		g_br_sel = max(0, g_br_count - 1);
};

void(float cx, float cy, float cw, float ch, float idx, float sel, float clicked) BM_DrawServerCard =
{
	local float hov, ping, nump, maxp, bots, tw, th;
	local string cname, sname, smap, thumb, pstr, ping_str, slot_str;
	local vector pcol, brd, bg;

	if (idx < 0)
	{
		cname = BAKO_ONLINE_ADDR;
		sname = "BAKERSFIELD ONLINE (PINNED)";
		smap = "soi6";
		ping = -1;
		nump = 0;
		maxp = 16;
		bots = 0;
	}
	else
	{
		cname = getserverliststring(SLIST_CNAME, idx);
		sname = getserverliststring(SLIST_NAME, idx);
		smap = getserverliststring(SLIST_MAP, idx);
		ping = getserverlistnumber(SLIST_PING, idx);
		nump = getserverlistnumber(SLIST_NUMPLAYERS, idx);
		maxp = getserverlistnumber(SLIST_MAXPLAYERS, idx);
		bots = getserverlistnumber(SLIST_NUMBOTS, idx);
		if (sname == "")
			sname = cname;
	}

	hov = BM_MouseIn(cx, cy, cw, ch);
	bg = (hov || sel) ? COL_GLASS_HOVER : COL_GLASS_CARD;
	brd = hov ? COL_ACCENT : (sel ? '0.68 0.56 0.24' : COL_BORDER);

	BM_Fill(cx, cy, cw, ch, bg, (hov || sel) ? 0.90 : 0.78);
	BM_Outline(cx, cy, cw, ch, brd, (hov || sel) ? 0.92 : 0.55, 1);
	if (hov || sel)
		BM_Fill(cx, cy, 2.5, ch, hov ? COL_ACCENT_HOT : COL_ACCENT, 0.95);

	// 16:10 Levelshot thumbnail
	tw = 74;
	th = 46;
	thumb = BM_LevelshotPic(smap);
	drawpic((cx + 6) * '1 0 0' + (cy + 8) * '0 1 0', thumb, tw * '1 0 0' + th * '0 1 0', '1 1 1', 0.98, 0);
	BM_Outline(cx + 6, cy + 8, tw, th, COL_BORDER, 0.65, 1);

	// Ping badge (top-right)
	if (ping < 0)
	{
		ping_str = "PIN";
		pcol = COL_ACCENT;
	}
	else
	{
		if (fabs(ping) < 0.5)
			ping_str = "0ms";
		else
			ping_str = strcat(ftos(rint(ping)), "ms");
		if (ping < 50)
			pcol = COL_GOOD;
		else if (ping < 120)
			pcol = COL_WARN;
		else
			pcol = COL_BAD;
	}
	BM_Fill(cx + cw - 49, cy + 5, 44, 13, '0.03 0.04 0.07', 0.92);
	BM_Outline(cx + cw - 49, cy + 5, 44, 13, pcol, 0.65, 1);
	BM_DrawTextCentered(cx + cw - 27, cy + 7.5, ping_str, 8, pcol, 0.98);

	// Hostname
	BM_DrawTextClipped(cx + 86, cy + 6, cw - 139, sname, 8, COL_TEXT, 0.98, TRUE);

	// Map & player counts
	if (smap == "")
		smap = "unknown";
	if (idx < 0)
		pstr = "1-click public server";
	else
	{
		slot_str = strcat(ftos(nump), "/", ftos(maxp), " players");
		if (bots > 0)
			slot_str = strcat(slot_str, " (", ftos(bots), "b)");
		pstr = slot_str;
	}
	BM_DrawTextClipped(cx + 86, cy + 19, cw - 92, strcat("MAP: ", smap), 8, COL_ACCENT, 0.94, FALSE);
	BM_DrawTextClipped(cx + 86, cy + 32, cw - 92, pstr, 8, COL_TEXT, 0.88, FALSE);

	// IP & 1-click JOIN pill
	BM_DrawTextClipped(cx + 86, cy + 46, cw - 138, cname, 8, COL_MUTED, 0.85, FALSE);

	BM_Fill(cx + cw - 47, cy + ch - 17, 42, 13, hov ? COL_ACCENT : '0.14 0.19 0.28', hov ? 0.96 : 0.88);
	BM_DrawTextCentered(cx + cw - 26, cy + ch - 14.5, "JOIN", 8, hov ? '0.05 0.05 0.06' : COL_ACCENT, 0.98);

	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_Loading_Begin(smap, sname, "JOINING SERVER");
		BM_ConnectTo(cname);
	}
};

void(float clicked) BM_Browser_Draw =
{
	local float px, py, pw, ph, gx, gy, gw, gh, cw, ch, gap_x, gap_y;
	local float rows, vis_rows, max_scroll, i, r, c, cx, cy, hov, s_idx;
	local float total_all, srv_q, srv_rep, sb_h, sb_y;
	local string stat_txt;

	if (gettime() >= g_br_next_rebuild)
	{
		BM_Browser_Rebuild();
		g_br_next_rebuild = gettime() + 0.25;
	}

	px = 20;
	py = 16;
	pw = g_vw - 40;
	ph = g_vh - 32;

	BM_DrawGlassPanel(px, py, pw, ph, 0.88, COL_BORDER, 0.78, 2.5);

	// Header
	BM_DrawText(px + 14, py + 11, "BAKERSFIELD QUAKE", 12, COL_ACCENT, 0.98);
	BM_DrawText(px + 228, py + 14, "JOIN GAME", 9, COL_TEXT, 0.92);
	total_all = getserverliststat(SLSTAT_TOTALCOUNT);
	srv_q = getserverliststat(SLSTAT_SERVERQUERY);
	srv_rep = getserverliststat(SLSTAT_SERVERREPLY);
	if (srv_q > srv_rep)
		stat_txt = strcat("Scanning... ", ftos(g_br_count), " shown (", ftos(total_all), " total)");
	else
		stat_txt = strcat(ftos(g_br_count), " shown (", ftos(total_all), " found)");
	BM_DrawTextClipped(px + 324, py + 14, pw - 474, stat_txt, 8, COL_MUTED, 0.92, FALSE);

	hov = BM_DrawButton(px + pw - 142, py + 9, 70, 18, "REFRESH", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
		BM_Browser_Refresh();
	}

	hov = BM_DrawButton(px + pw - 66, py + 9, 54, 18, "BACK", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu3.wav");
		g_focus_input = INPUT_NONE;
		g_page = PAGE_MAIN;
		return;
	}

	// Tabs
	hov = BM_DrawTab(px + 14, py + 34, 72, 18, "LAN", (g_br_tab == TAB_LAN));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
		g_br_tab = TAB_LAN;
		g_br_scroll = 0;
		g_br_sel = 0;
		BM_Browser_Rebuild();
	}
	hov = BM_DrawTab(px + 90, py + 34, 82, 18, "ONLINE", (g_br_tab == TAB_ONLINE));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
		g_br_tab = TAB_ONLINE;
		g_br_scroll = 0;
		g_br_sel = 0;
		BM_Browser_Rebuild();
	}
	hov = BM_DrawTab(px + 176, py + 34, 68, 18, "ALL", (g_br_tab == TAB_ALL));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
		g_br_tab = TAB_ALL;
		g_br_scroll = 0;
		g_br_sel = 0;
		BM_Browser_Rebuild();
	}

	// Card grid area
	gx = px + 14;
	gy = py + 58;
	gw = pw - 34;
	gh = ph - 98;
	gap_x = 8;
	gap_y = 6;
	cw = floor((gw - gap_x) * 0.5);
	ch = 62;

	vis_rows = max(1, floor((gh + gap_y) / (ch + gap_y)));
	rows = ceil(g_br_count * 0.5);
	max_scroll = max(0, rows - vis_rows);
	g_br_scroll = bound(0, g_br_scroll, max_scroll);

	if (g_br_count == 0)
	{
		BM_Fill(gx, gy, gw, gh, '0.04 0.05 0.09', 0.65);
		BM_Outline(gx, gy, gw, gh, COL_BORDER, 0.45, 1);
		if (g_br_tab == TAB_LAN)
		{
			BM_DrawTextCentered(gx + gw * 0.5, gy + gh * 0.40, "NO LAN SERVERS FOUND YET", 10, COL_TEXT, 0.90);
			BM_DrawTextCentered(gx + gw * 0.5, gy + gh * 0.54, "Click REFRESH, try ONLINE, or HOST LAN GAME.", 8, COL_MUTED, 0.85);
		}
		else
		{
			BM_DrawTextCentered(gx + gw * 0.5, gy + gh * 0.44, "QUERYING MASTER SERVERS...", 10, COL_TEXT, 0.90);
		}
	}
	else
	{
		BM_BeginClip(gx, gy, gw, gh);
		for (i = 0; i < g_br_count; i = i + 1)
		{
			r = floor(i * 0.5) - g_br_scroll;
			c = modulo(i, 2);
			if (r >= 0 && r < vis_rows + 1)
			{
				cx = gx + c * (cw + gap_x);
				cy = gy + r * (ch + gap_y);
				if (cy + ch <= gy + gh + 4)
				{
					s_idx = g_br_indices[i];
					if (BM_MouseIn(cx, cy, cw, ch) && g_mouse_moved)
						g_br_sel = i;
					BM_DrawServerCard(cx, cy, cw, ch, s_idx, (g_br_sel == i), clicked);
				}
			}
		}
		BM_EndClip();

		// Scrollbar
		if (max_scroll > 0)
		{
			BM_Fill(gx + gw + 4, gy, 4, gh, '0.03 0.04 0.07', 0.85);
			sb_h = max(18, gh * (vis_rows / rows));
			sb_y = gy + (gh - sb_h) * (g_br_scroll / max_scroll);
			BM_Fill(gx + gw + 4, sb_y, 4, sb_h, COL_ACCENT, 0.85);
		}
	}

	// Bottom Direct IP bar
	BM_Fill(px + 14, py + ph - 34, pw - 28, 1, COL_BORDER, 0.45);
	BM_DrawText(px + 14, py + ph - 21, "DIRECT IP:", 8, COL_MUTED, 0.95);
	hov = BM_DrawInputBox(px + 102, py + ph - 26, pw - 194, 19, g_ip_buf, "ip:port (e.g. 72.62.241.93:26000)", (g_focus_input == INPUT_DIRECTIP));
	if (clicked && hov)
	{
		g_focus_input = INPUT_DIRECTIP;
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	else if (clicked && g_focus_input == INPUT_DIRECTIP && !hov)
	{
		g_focus_input = INPUT_NONE;
	}

	hov = BM_DrawButton(px + pw - 86, py + ph - 26, 74, 19, "CONNECT", FALSE, TRUE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_ConnectTo(g_ip_buf);
	}
};

void() BM_Browser_EnsureVisible =
{
	local float gh, vis_rows, rows, max_scroll, row;

	gh = (g_vh - 32) - 98;
	vis_rows = max(1, floor((gh + 6) / 68));
	rows = ceil(g_br_count * 0.5);
	max_scroll = max(0, rows - vis_rows);
	row = floor(g_br_sel * 0.5);
	if (row < g_br_scroll)
		g_br_scroll = row;
	else if (row >= g_br_scroll + vis_rows)
		g_br_scroll = row - vis_rows + 1;
	g_br_scroll = bound(0, g_br_scroll, max_scroll);
};

void(float key, float ascii) BM_Browser_KeyDown =
{
	local float s_idx;
	local string cname;

	if (g_focus_input == INPUT_DIRECTIP)
	{
		if (key == K_ESCAPE || key == K_TAB)
		{
			g_focus_input = INPUT_NONE;
			return;
		}
		if (key == K_ENTER || key == K_KP_ENTER)
		{
			g_focus_input = INPUT_NONE;
			BM_ConnectTo(g_ip_buf);
			return;
		}
		g_ip_buf = BM_ZoneSet(g_ip_buf, BM_EditString(g_ip_buf, 48, key, ascii, FALSE));
		return;
	}

	if (key == K_ESCAPE)
	{
		BM_PlaySound("sound/misc/menu3.wav");
		g_page = PAGE_MAIN;
	}
	else if (key == K_MWHEELUP || key == K_PGUP)
	{
		g_br_scroll = max(0, g_br_scroll - 1);
	}
	else if (key == K_MWHEELDOWN || key == K_PGDN)
	{
		g_br_scroll = g_br_scroll + 1;
	}
	else if (key == K_LEFTARROW && g_br_count > 0)
	{
		g_br_sel = max(0, g_br_sel - 1);
		BM_Browser_EnsureVisible();
	}
	else if (key == K_RIGHTARROW && g_br_count > 0)
	{
		g_br_sel = min(g_br_count - 1, g_br_sel + 1);
		BM_Browser_EnsureVisible();
	}
	else if (key == K_UPARROW && g_br_count > 0)
	{
		g_br_sel = max(0, g_br_sel - 2);
		BM_Browser_EnsureVisible();
	}
	else if (key == K_DOWNARROW && g_br_count > 0)
	{
		g_br_sel = min(g_br_count - 1, g_br_sel + 2);
		BM_Browser_EnsureVisible();
	}
	else if ((key == K_ENTER || key == K_KP_ENTER) && g_br_count > 0)
	{
		s_idx = g_br_indices[g_br_sel];
		if (s_idx < 0)
		{
			cname = BAKO_ONLINE_ADDR;
			BM_Loading_Begin("", "Bakersfield Online", "JOINING SERVER");
		}
		else
		{
			cname = getserverliststring(SLIST_CNAME, s_idx);
			BM_Loading_Begin(getserverliststring(SLIST_MAP, s_idx), getserverliststring(SLIST_NAME, s_idx), "JOINING SERVER");
		}
		BM_ConnectTo(cname);
	}
};
