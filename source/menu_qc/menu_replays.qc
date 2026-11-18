// BakersfieldQuake MenuQC - Match Replays (Public Online Archive + Local Demos)

float REPLAY_TAB_ONLINE = 0;
float REPLAY_TAB_LOCAL  = 1;

float URI_ID_DEMOS = 101;
string BAKO_DEMO_BASE_URL = "http://72.62.241.93:8097/demos/";

float g_rep_tab;
float g_rep_sel;
float g_rep_scroll;

float g_rep_bufs_ready;
float g_rep_on_id;
float g_rep_on_date;
float g_rep_on_map;
float g_rep_on_dur;
float g_rep_on_size;
float g_rep_on_ready; // per row: "1" when demos/<id>.dem is already readable (set on refresh / download done)
float g_rep_on_count;
float g_rep_on_loading;
string g_rep_on_status;

float g_rep_loc_path;
float g_rep_loc_count;

string g_rep_dl_id;
float g_rep_dl_start;
float g_rep_dl_next_poll;
string g_rep_dl_status;

void() BM_Replays_EnsureBufs =
{
	if (g_rep_bufs_ready)
		return;
	g_rep_on_id   = buf_create();
	g_rep_on_date = buf_create();
	g_rep_on_map  = buf_create();
	g_rep_on_dur  = buf_create();
	g_rep_on_size = buf_create();
	g_rep_on_ready = buf_create();
	g_rep_loc_path = buf_create();
	g_rep_bufs_ready = TRUE;
};

void() BM_Replays_ClearOnline =
{
	if (!g_rep_bufs_ready)
		return;
	buf_del(g_rep_on_id);
	buf_del(g_rep_on_date);
	buf_del(g_rep_on_map);
	buf_del(g_rep_on_dur);
	buf_del(g_rep_on_size);
	buf_del(g_rep_on_ready);
	g_rep_on_id   = buf_create();
	g_rep_on_date = buf_create();
	g_rep_on_map  = buf_create();
	g_rep_on_dur  = buf_create();
	g_rep_on_size = buf_create();
	g_rep_on_ready = buf_create();
	g_rep_on_count = 0;
};

void() BM_Replays_ClearLocal =
{
	if (!g_rep_bufs_ready)
		return;
	buf_del(g_rep_loc_path);
	g_rep_loc_path = buf_create();
	g_rep_loc_count = 0;
};

void() BM_Replays_Shutdown =
{
	if (g_rep_bufs_ready)
	{
		buf_del(g_rep_on_id);
		buf_del(g_rep_on_date);
		buf_del(g_rep_on_map);
		buf_del(g_rep_on_dur);
		buf_del(g_rep_on_size);
		buf_del(g_rep_on_ready);
		buf_del(g_rep_loc_path);
		g_rep_bufs_ready = FALSE;
	}
	g_rep_on_count = 0;
	g_rep_loc_count = 0;
	g_rep_on_status = BM_ZoneSet(g_rep_on_status, "");
	g_rep_dl_id = BM_ZoneSet(g_rep_dl_id, "");
	g_rep_dl_status = BM_ZoneSet(g_rep_dl_status, "");
};

float(string relpath) BM_Replays_FileExists =
{
	local float fh;

	if (relpath == "")
		return FALSE;
	fh = fopen(relpath, FILE_READ);
	if (fh < 0)
		return FALSE;
	fclose(fh);
	return TRUE;
};

// Replay ids come from demos.txt over plain HTTP and end up in localcmd/paths:
// accept only [A-Za-z0-9_.-] (no spaces, quotes, ';', '/', newlines).
float(string id) BM_Replays_IdIsSafe =
{
	local float n, i, c;

	n = strlen(id);
	if (n <= 0 || n > 96)
		return FALSE;
	for (i = 0; i < n; i = i + 1)
	{
		c = str2chr(id, i);
		if (c >= 48 && c <= 57) continue;   // 0-9
		if (c >= 65 && c <= 90) continue;   // A-Z
		if (c >= 97 && c <= 122) continue;  // a-z
		if (c == 95 || c == 46 || c == 45) continue; // _ . -
		return FALSE;
	}
	return TRUE;
};

// Mark every online row with this id as ready (download finished).
void(string id) BM_Replays_MarkReady =
{
	local float i;

	if (!g_rep_bufs_ready || id == "")
		return;
	for (i = 0; i < g_rep_on_count; i = i + 1)
		if (bufstr_get(g_rep_on_id, i) == id)
			bufstr_set(g_rep_on_ready, i, "1");
};

void(string relpath) BM_Replays_PlayFile =
{
	local string clean;

	clean = BM_SanitizeCmdStr(relpath);
	if (clean == "")
		return;
	BM_PlaySound("sound/misc/menu2.wav");
	cvar_set("bm_menu_bg", "0");
	m_toggle(0);
	localcmd(strcat("set bm_menu_bg 0; playdemo \"", clean, "\"\n"));
};

void() BM_Replays_ScanLocal =
{
	local float sh, n, i;
	local string fn;

	BM_Replays_EnsureBufs();
	BM_Replays_ClearLocal();

	sh = search_begin("demos/*.dem", TRUE, TRUE);
	if (sh >= 0)
	{
		n = search_getsize(sh);
		for (i = n - 1; i >= 0 && g_rep_loc_count < 256; i = i - 1)
		{
			fn = search_getfilename(sh, i);
			if (fn != "")
			{
				bufstr_set(g_rep_loc_path, g_rep_loc_count, fn);
				g_rep_loc_count = g_rep_loc_count + 1;
			}
		}
		search_end(sh);
	}

	sh = search_begin("*.dem", TRUE, TRUE);
	if (sh >= 0)
	{
		n = search_getsize(sh);
		for (i = n - 1; i >= 0 && g_rep_loc_count < 256; i = i - 1)
		{
			fn = search_getfilename(sh, i);
			if (fn != "" && strcasecmp(fn, "intro.dem") != 0 && strcasecmp(fn, "intro_movie_showcase.dem") != 0)
			{
				bufstr_set(g_rep_loc_path, g_rep_loc_count, fn);
				g_rep_loc_count = g_rep_loc_count + 1;
			}
		}
		search_end(sh);
	}

	if (g_rep_tab == REPLAY_TAB_LOCAL && g_rep_sel >= g_rep_loc_count)
		g_rep_sel = max(0, g_rep_loc_count - 1);
};

void() BM_Replays_RefreshOnline =
{
	BM_Replays_EnsureBufs();
	g_rep_on_loading = TRUE;
	g_rep_on_status = BM_ZoneSet(g_rep_on_status, "Loading online replay index...");
	uri_get(strcat(BAKO_DEMO_BASE_URL, "demos.txt"), URI_ID_DEMOS);
};

void(string line) BM_Replays_ParseLine =
{
	local float p1, p2, p3, p4, nlen;
	local string id, dt, mp, dur, sz;

	nlen = strlen(line);
	if (nlen <= 0)
		return;
	if (str2chr(line, nlen - 1) == 13)
		line = substring(line, 0, nlen - 1);
	if (line == "" || strncmp(line, "#", 1) == 0)
		return;

	p1 = strstrofs(line, "|", 0);
	if (p1 <= 0)
		return;
	p2 = strstrofs(line, "|", p1 + 1);
	if (p2 <= p1)
		return;
	p3 = strstrofs(line, "|", p2 + 1);
	if (p3 <= p2)
		return;
	p4 = strstrofs(line, "|", p3 + 1);
	if (p4 <= p3)
		return;

	id  = substring(line, 0, p1);
	dt  = substring(line, p1 + 1, p2 - p1 - 1);
	mp  = substring(line, p2 + 1, p3 - p2 - 1);
	dur = substring(line, p3 + 1, p4 - p3 - 1);
	sz  = substring(line, p4 + 1, strlen(line) - p4 - 1);
	if (!BM_Replays_IdIsSafe(id))
		return;

	bufstr_set(g_rep_on_id,   g_rep_on_count, id);
	bufstr_set(g_rep_on_date, g_rep_on_count, dt);
	bufstr_set(g_rep_on_map,  g_rep_on_count, mp);
	bufstr_set(g_rep_on_dur,  g_rep_on_count, dur);
	bufstr_set(g_rep_on_size, g_rep_on_count, sz);
	// Ready flag cached once per refresh instead of an fopen per card per frame.
	bufstr_set(g_rep_on_ready, g_rep_on_count, BM_Replays_FileExists(strcat("demos/", id, ".dem")) ? "1" : "");
	g_rep_on_count = g_rep_on_count + 1;
};

void(float id, float status, string data) URI_Get_Callback =
{
	local float pos, nl, total_len;
	local string line;

	if (id != URI_ID_DEMOS)
		return;

	BM_Replays_EnsureBufs();
	g_rep_on_loading = FALSE;

	if ((status != 0 && status != 200) || data == "")
	{
		if (g_rep_on_count == 0)
			g_rep_on_status = BM_ZoneSet(g_rep_on_status, "Could not load online archive (no demos or offline).");
		else
			g_rep_on_status = BM_ZoneSet(g_rep_on_status, "Refresh failed - showing previous list.");
		return;
	}

	BM_Replays_ClearOnline();
	pos = 0;
	total_len = strlen(data);
	while (pos < total_len && g_rep_on_count < 256)
	{
		nl = strstrofs(data, "\n", pos);
		if (nl < 0)
		{
			line = substring(data, pos, total_len - pos);
			pos = total_len;
		}
		else
		{
			line = substring(data, pos, nl - pos);
			pos = nl + 1;
		}
		BM_Replays_ParseLine(line);
	}

	if (g_rep_on_count == 0)
		g_rep_on_status = BM_ZoneSet(g_rep_on_status, "No public multiplayer demos recorded yet.");
	else
		g_rep_on_status = BM_ZoneSet(g_rep_on_status, strcat(ftos(g_rep_on_count), " public demos available (last 12 months)."));

	if (g_rep_tab == REPLAY_TAB_ONLINE && g_rep_sel >= g_rep_on_count)
		g_rep_sel = max(0, g_rep_on_count - 1);
};

void(float idx) BM_Replays_Activate =
{
	local string id, rel;

	if (g_rep_tab == REPLAY_TAB_LOCAL)
	{
		if (idx < 0 || idx >= g_rep_loc_count)
			return;
		rel = bufstr_get(g_rep_loc_path, idx);
		BM_Replays_PlayFile(rel);
		return;
	}

	if (idx < 0 || idx >= g_rep_on_count || g_rep_dl_id != "")
		return;
	id = bufstr_get(g_rep_on_id, idx);
	if (!BM_Replays_IdIsSafe(id))
		return;
	rel = strcat("demos/", id, ".dem");
	if (BM_Replays_FileExists(rel))
	{
		bufstr_set(g_rep_on_ready, idx, "1");
		BM_Replays_PlayFile(rel);
		return;
	}

	BM_PlaySound("sound/misc/menu2.wav");
	g_rep_dl_id = BM_ZoneSet(g_rep_dl_id, id);
	g_rep_dl_start = gettime();
	g_rep_dl_next_poll = 0;
	g_rep_dl_status = BM_ZoneSet(g_rep_dl_status, strcat("Downloading ", id, ".pk3 ..."));
	// cl_curl_enabled stays: the engine's `curl` console command refuses to run while
	// it is 0 ("curl support not enabled"), and a temporary set is not possible here.
	localcmd(strcat("cl_curl_enabled 1\ncurl --pak ", BAKO_DEMO_BASE_URL, id, ".pk3\n"));
};

void() BM_Replays_Open =
{
	g_page = PAGE_REPLAYS;
	g_focus_input = INPUT_NONE;
	g_rep_sel = 0;
	g_rep_scroll = 0;
	BM_Replays_EnsureBufs();
	BM_Replays_ScanLocal();
	BM_Replays_RefreshOnline();
};

string(string path) BM_Replays_MapFromLocalPath =
{
	local float us1, us2, dot, slash, p, last_us, prev_us, i, c, numeric;
	local string base, rest;

	slash = strstrofs(path, "/", 0);
	base = (slash >= 0) ? substring(path, slash + 1, strlen(path) - slash - 1) : path;
	dot = strstrofs(base, ".", 0);
	if (dot > 0)
		base = substring(base, 0, dot);
	// Format: YYYY-MM-DD_HH-MM_mapname(_slot_address)?  The map name itself may
	// contain '_' (little_st_james), so strip the date/time prefix, then drop the
	// last two '_' fields only when the first of them is a numeric client slot.
	us1 = strstrofs(base, "_", 0);
	if (us1 <= 0)
		return "";
	us2 = strstrofs(base, "_", us1 + 1);
	if (us2 <= us1)
		return "";
	rest = substring(base, us2 + 1, strlen(base) - us2 - 1);

	last_us = -1;
	prev_us = -1;
	p = strstrofs(rest, "_", 0);
	while (p >= 0)
	{
		prev_us = last_us;
		last_us = p;
		p = strstrofs(rest, "_", p + 1);
	}
	if (prev_us > 0)
	{
		numeric = (last_us - prev_us > 1);
		for (i = prev_us + 1; i < last_us; i = i + 1)
		{
			c = str2chr(rest, i);
			if (c < 48 || c > 57)
				numeric = FALSE;
		}
		if (numeric)
			return substring(rest, 0, prev_us);
	}
	return rest;
};

void(float cx, float cy, float cw, float ch, float idx, float sel, float clicked) BM_DrawReplayCard =
{
	local float hov, tw, th, cached;
	local string id, dt, mp, dur, sz, thumb, badge, sub;
	local vector brd, bg, bcol;

	if (g_rep_tab == REPLAY_TAB_ONLINE)
	{
		id  = bufstr_get(g_rep_on_id, idx);
		dt  = bufstr_get(g_rep_on_date, idx);
		mp  = bufstr_get(g_rep_on_map, idx);
		dur = bufstr_get(g_rep_on_dur, idx);
		sz  = bufstr_get(g_rep_on_size, idx);
		cached = (bufstr_get(g_rep_on_ready, idx) == "1");
		badge = cached ? "READY" : sz;
		bcol = cached ? COL_GOOD : COL_ACCENT;
		sub = strcat(dt, "   |   ", dur);
	}
	else
	{
		id = bufstr_get(g_rep_loc_path, idx);
		mp = BM_Replays_MapFromLocalPath(id);
		dt = id;
		badge = "LOCAL";
		bcol = COL_TEXT;
		sub = (mp != "") ? strcat("MAP: ", mp) : "Local demo recording";
	}

	hov = BM_MouseIn(cx, cy, cw, ch);
	bg = (hov || sel) ? COL_GLASS_HOVER : COL_GLASS_CARD;
	brd = hov ? COL_ACCENT : (sel ? '0.68 0.56 0.24' : COL_BORDER);

	BM_Fill(cx, cy, cw, ch, bg, (hov || sel) ? 0.90 : 0.78);
	BM_Outline(cx, cy, cw, ch, brd, (hov || sel) ? 0.92 : 0.55, 1);
	if (hov || sel)
		BM_Fill(cx, cy, 2.5, ch, hov ? COL_ACCENT_HOT : COL_ACCENT, 0.95);

	tw = 74;
	th = 44;
	thumb = BM_LevelshotPic(mp);
	drawpic((cx + 6) * '1 0 0' + (cy + 5) * '0 1 0', thumb, tw * '1 0 0' + th * '0 1 0', '1 1 1', 0.98, 0);
	BM_Outline(cx + 6, cy + 5, tw, th, COL_BORDER, 0.65, 1);

	BM_Fill(cx + cw - 54, cy + 5, 48, 13, '0.03 0.04 0.07', 0.92);
	BM_Outline(cx + cw - 54, cy + 5, 48, 13, bcol, 0.65, 1);
	BM_DrawTextCentered(cx + cw - 30, cy + 7.5, badge, 8, bcol, 0.98);

	if (g_rep_tab == REPLAY_TAB_ONLINE)
	{
		BM_DrawTextClipped(cx + 88, cy + 7, cw - 150, strcat("MAP: ", mp), 9, COL_ACCENT, 0.98, FALSE);
		BM_DrawTextClipped(cx + 88, cy + 21, cw - 98, sub, 8, COL_TEXT, 0.92, FALSE);
		BM_DrawTextClipped(cx + 88, cy + 34, cw - 98, cached ? "Click to watch immediately" : "Click to download & watch", 8, COL_MUTED, 0.85, FALSE);
	}
	else
	{
		BM_DrawTextClipped(cx + 88, cy + 7, cw - 150, dt, 8, COL_TEXT, 0.98, FALSE);
		BM_DrawTextClipped(cx + 88, cy + 21, cw - 98, sub, 8, COL_ACCENT, 0.92, FALSE);
		BM_DrawTextClipped(cx + 88, cy + 34, cw - 98, "Click to play demo", 8, COL_MUTED, 0.85, FALSE);
	}

	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_rep_sel = idx;
		BM_Replays_Activate(idx);
	}
};

// Number of fully visible replay cards; shared by BM_Replays_Draw and the
// keyboard navigation (list height = (g_vh - 36) - 98, card 54, gap 6).
float() BM_Replays_VisCount =
{
	local float lh, ch, gap;

	lh = (g_vh - 36) - 98;
	ch = 54;
	gap = 6;
	return max(1, floor((lh + gap) / (ch + gap)));
};

void(float clicked) BM_Replays_Draw =
{
	local float px, py, pw, ph, lx, ly, lw, lh, ch, gap, vis, max_scroll;
	local float count, i, y, hov, sb_h, sb_y;
	local string ready_path, play_id, msg;

	// Poll active pk3 download until VFS sees the .dem inside it (at most every 0.5 s)
	if (g_rep_dl_id != "" && gettime() >= g_rep_dl_next_poll)
	{
		g_rep_dl_next_poll = gettime() + 0.5;
		ready_path = strcat("demos/", g_rep_dl_id, ".dem");
		if (BM_Replays_FileExists(ready_path))
		{
			play_id = strzone(g_rep_dl_id);
			BM_Replays_MarkReady(play_id);
			g_rep_dl_id = BM_ZoneSet(g_rep_dl_id, "");
			g_rep_dl_status = BM_ZoneSet(g_rep_dl_status, "");
			BM_Replays_PlayFile(strcat("demos/", play_id, ".dem"));
			strunzone(play_id);
			return;
		}
		if (gettime() - g_rep_dl_start > 45)
		{
			g_rep_dl_status = BM_ZoneSet(g_rep_dl_status, "Download failed or timed out (check console).");
			g_rep_dl_id = BM_ZoneSet(g_rep_dl_id, "");
		}
	}

	px = 24;
	py = 18;
	pw = g_vw - 48;
	ph = g_vh - 36;

	BM_DrawGlassPanel(px, py, pw, ph, 0.88, COL_BORDER, 0.78, 2.5);

	BM_DrawText(px + 14, py + 11, "BAKERSFIELD QUAKE", 12, COL_ACCENT, 0.98);
	BM_DrawText(px + 228, py + 14, "MATCH REPLAYS", 9, COL_TEXT, 0.92);
	BM_DrawTextClipped(px + 340, py + 14, pw - 420, "Public VPS archive & local demos", 8, COL_MUTED, 0.92, FALSE);

	hov = BM_DrawButton(px + pw - 66, py + 9, 54, 18, "BACK", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu3.wav");
		g_rep_dl_id = BM_ZoneSet(g_rep_dl_id, "");
		g_page = PAGE_MAIN;
		return;
	}

	// Tabs + Refresh
	hov = BM_DrawTab(px + 14, py + 36, 126, 18, "ONLINE ARCHIVE", (g_rep_tab == REPLAY_TAB_ONLINE));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
		g_rep_tab = REPLAY_TAB_ONLINE;
		g_rep_sel = 0;
		g_rep_scroll = 0;
	}
	hov = BM_DrawTab(px + 146, py + 36, 114, 18, "LOCAL DEMOS", (g_rep_tab == REPLAY_TAB_LOCAL));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
		g_rep_tab = REPLAY_TAB_LOCAL;
		g_rep_sel = 0;
		g_rep_scroll = 0;
		BM_Replays_ScanLocal();
	}
	hov = BM_DrawButton(px + pw - 96, py + 36, 84, 18, "REFRESH", FALSE, TRUE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
		if (g_rep_tab == REPLAY_TAB_ONLINE)
			BM_Replays_RefreshOnline();
		else
			BM_Replays_ScanLocal();
	}

	// List area
	lx = px + 14;
	ly = py + 62;
	lw = pw - 28;
	lh = ph - 98;
	ch = 54;
	gap = 6;
	vis = BM_Replays_VisCount(); // same as max(1, floor((lh + gap) / (ch + gap)))

	count = (g_rep_tab == REPLAY_TAB_ONLINE) ? g_rep_on_count : g_rep_loc_count;
	max_scroll = max(0, count - vis);
	g_rep_scroll = bound(0, g_rep_scroll, max_scroll);
	if (g_rep_sel >= count)
		g_rep_sel = max(0, count - 1);

	if (count <= 0)
	{
		BM_Fill(lx, ly, lw, lh, '0.05 0.04 0.03', 0.65);
		BM_Outline(lx, ly, lw, lh, COL_BORDER, 0.45, 1);
		if (g_rep_tab == REPLAY_TAB_ONLINE)
			msg = (g_rep_on_status != "") ? g_rep_on_status : "No public demos found.";
		else
			msg = "No local .dem files in BakersfieldQuake/demos/";
		BM_DrawTextCentered(lx + lw * 0.5, ly + lh * 0.5 - 6, msg, 9, COL_MUTED, 0.92);
	}
	else
	{
		drawsetcliparea(lx, ly, lw, lh);
		for (i = g_rep_scroll; i < count && (i - g_rep_scroll) < vis + 1; i = i + 1)
		{
			y = ly + (i - g_rep_scroll) * (ch + gap);
			if (y + ch <= ly + lh + 2)
				BM_DrawReplayCard(lx, y, lw - ((max_scroll > 0) ? 10 : 0), ch, i, (g_rep_sel == i), clicked);
		}
		drawresetcliparea();

		if (max_scroll > 0)
		{
			BM_Fill(lx + lw - 6, ly, 4, lh, '0.08 0.06 0.04', 0.80);
			sb_h = max(20, floor(lh * (vis / count)));
			sb_y = ly + floor((lh - sb_h) * (g_rep_scroll / max_scroll));
			BM_Fill(lx + lw - 6, sb_y, 4, sb_h, COL_ACCENT, 0.85);
		}
	}

	// Footer status bar
	BM_Fill(px + 14, py + ph - 26, pw - 28, 18, '0.05 0.04 0.03', 0.82);
	BM_Outline(px + 14, py + ph - 26, pw - 28, 18, COL_BORDER, 0.45, 1);
	if (g_rep_dl_id != "")
	{
		BM_DrawTextClipped(px + 22, py + ph - 21, pw - 120, g_rep_dl_status, 8, COL_ACCENT, 0.98, FALSE);
		hov = BM_DrawButton(px + pw - 86, py + ph - 25, 68, 16, "CANCEL", FALSE, FALSE);
		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			localcmd("curl --cancel\n");
			g_rep_dl_id = BM_ZoneSet(g_rep_dl_id, "");
			g_rep_dl_status = BM_ZoneSet(g_rep_dl_status, "Download cancelled.");
		}
	}
	else if (g_rep_dl_status != "")
	{
		BM_DrawTextClipped(px + 22, py + ph - 21, pw - 44, g_rep_dl_status, 8, COL_WARN, 0.95, FALSE);
	}
	else if (g_rep_tab == REPLAY_TAB_ONLINE && g_rep_on_status != "")
	{
		BM_DrawTextClipped(px + 22, py + ph - 21, pw - 44, g_rep_on_status, 8, COL_MUTED, 0.92, FALSE);
	}
	else
	{
		BM_DrawTextClipped(px + 22, py + ph - 21, pw - 44, "Enter: Watch   |   R: Refresh   |   Esc: Back", 8, COL_MUTED, 0.92, FALSE);
	}
};

void(float key, float ascii) BM_Replays_KeyDown =
{
	local float count, vis;

	count = (g_rep_tab == REPLAY_TAB_ONLINE) ? g_rep_on_count : g_rep_loc_count;
	vis = BM_Replays_VisCount();

	if (key == K_ESCAPE)
	{
		BM_PlaySound("sound/misc/menu3.wav");
		g_rep_dl_id = BM_ZoneSet(g_rep_dl_id, "");
		g_page = PAGE_MAIN;
		return;
	}
	if (key == K_UPARROW && count > 0)
	{
		g_rep_sel = max(0, g_rep_sel - 1);
		if (g_rep_sel < g_rep_scroll)
			g_rep_scroll = g_rep_sel;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	else if (key == K_DOWNARROW && count > 0)
	{
		g_rep_sel = min(count - 1, g_rep_sel + 1);
		if (g_rep_sel >= g_rep_scroll + vis)
			g_rep_scroll = g_rep_sel - vis + 1;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	else if (key == K_MWHEELUP)
	{
		g_rep_scroll = max(0, g_rep_scroll - 1);
	}
	else if (key == K_MWHEELDOWN)
	{
		g_rep_scroll = min(max(0, count - vis), g_rep_scroll + 1);
	}
	else if (key == K_ENTER || key == K_KP_ENTER)
	{
		if (count > 0)
			BM_Replays_Activate(g_rep_sel);
	}
	else if (ascii == 114 || ascii == 82) // 'r' / 'R'
	{
		BM_PlaySound("sound/misc/menu1.wav");
		if (g_rep_tab == REPLAY_TAB_ONLINE)
			BM_Replays_RefreshOnline();
		else
			BM_Replays_ScanLocal();
	}
};
