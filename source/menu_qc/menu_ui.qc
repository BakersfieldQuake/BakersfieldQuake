// BakersfieldQuake MenuQC - Classic Default Quake / Zircon UI Helpers

// Classic Quake Palette (compatible with Browser & Host pages)
vector COL_SCRIM       = '0.02 0.01 0.01';
vector COL_GLASS_DARK  = '0.07 0.05 0.04';
vector COL_GLASS_CARD  = '0.12 0.08 0.06';
vector COL_GLASS_HOVER = '0.45 0.07 0.04';
vector COL_BORDER      = '0.44 0.30 0.18';
vector COL_HIGHLIGHT   = '0.94 0.86 0.72';
vector COL_ACCENT      = '0.96 0.72 0.24';
vector COL_ACCENT_HOT  = '0.92 0.22 0.10';
vector COL_TEXT        = '0.95 0.90 0.80';
vector COL_MUTED       = '0.72 0.62 0.50';
vector COL_GOOD        = '0.36 0.88 0.44';
vector COL_WARN        = '0.96 0.72 0.24';
vector COL_BAD         = '0.96 0.28 0.20';

string(string cur, string next) BM_ZoneSet =
{
	if (strlen(cur) > 0)
		strunzone(cur);
	if (strlen(next) <= 0)
		return "";
	return strzone(next);
};

string(string s) BM_SanitizeCmdStr =
{
	local float i, n, ch;
	local string out;

	if (strstrofs(s, "\"") < 0 && strstrofs(s, ";") < 0 && strstrofs(s, "$") < 0 && strstrofs(s, "\n") < 0)
		return s;
	out = "";
	n = strlen(s);
	for (i = 0; i < n; i = i + 1)
	{
		ch = str2chr(s, i);
		if (ch >= 32 && ch <= 126 && ch != 34 && ch != 59 && ch != 36)
			out = strcat(out, chr2str(ch));
	}
	return out;
};

void(string snd) BM_PlaySound =
{
	if (snd != "")
		localsound(snd);
};

float(float x, float y, float w, float h) BM_MouseIn =
{
	return (g_mx >= x && g_mx <= (x + w) && g_my >= y && g_my <= (y + h));
};

void(float x, float y, float w, float h, vector rgb, float a) BM_Fill =
{
	drawfill(x * '1 0 0' + y * '0 1 0', w * '1 0 0' + h * '0 1 0', rgb, a, 0);
};

void(float x, float y, float w, float h, vector rgb, float a, float thick) BM_Outline =
{
	BM_Fill(x, y, w, thick, rgb, a);
	BM_Fill(x, y + h - thick, w, thick, rgb, a);
	BM_Fill(x, y + thick, thick, max(0, h - thick * 2), rgb, a);
	BM_Fill(x + w - thick, y + thick, thick, max(0, h - thick * 2), rgb, a);
};

void(float x, float y, float w, float h, float bg_alpha, vector border_rgb, float border_alpha, float accent_top) BM_DrawGlassPanel =
{
	BM_Fill(x, y, w, h, COL_GLASS_DARK, bg_alpha);
	BM_Outline(x, y, w, h, border_rgb, border_alpha, 1);
	if (accent_top > 0)
		BM_Fill(x, y, w, accent_top, COL_ACCENT_HOT, 0.85);
};

void(float x, float y, string s, float sz, vector rgb, float a) BM_DrawText =
{
	local vector pos, sc;

	pos = x * '1 0 0' + y * '0 1 0';
	sc = sz * '1 1 0';
	drawstring(pos + '0.8 0.8 0', s, sc, '0 0 0', a * 0.78, 0);
	drawstring(pos, s, sc, rgb, a, 0);
};

void(float x, float y, string s, float sz, float a) BM_DrawColorText =
{
	local vector pos, sc;
	local string plain;

	pos = x * '1 0 0' + y * '0 1 0';
	sc = sz * '1 1 0';
	plain = strdecolorize(s);
	drawstring(pos + '0.8 0.8 0', plain, sc, '0 0 0', a * 0.78, 0);
	drawcolorcodedstring(pos, s, sc, a, 0);
};

void(float x, float y, float w, string s, float sz, vector rgb, float a, float use_colors) BM_DrawTextClipped =
{
	drawsetcliparea(x, y - 1, w, sz + 3);
	if (use_colors)
		BM_DrawColorText(x, y, s, sz, a);
	else
		BM_DrawText(x, y, s, sz, rgb, a);
	drawresetcliparea();
};

void(float cx, float y, string s, float sz, vector rgb, float a) BM_DrawTextCentered =
{
	local float wd;

	wd = stringwidth(s, FALSE, sz * '1 1 0');
	BM_DrawText(cx - wd * 0.5, y, s, sz, rgb, a);
};

void(float rx, float y, string s, float sz, vector rgb, float a) BM_DrawTextRight =
{
	local float wd;

	wd = stringwidth(s, FALSE, sz * '1 1 0');
	BM_DrawText(rx - wd, y, s, sz, rgb, a);
};

// Spinning classic Quake Q cursor dot
void(float x, float y) BM_DrawMenuDot =
{
	local float f;
	local string pic;

	f = 1 + modulo(floor(gettime() * 10), 6);
	pic = strcat("gfx/menudot", ftos(f), ".lmp");
	drawpic(x * '1 0 0' + y * '0 1 0', pic, '16 16 0', '1 1 1', 1.0, 0);
};

float(float x, float y, float w, float h, string label, float sub_sel, float primary) BM_DrawButton =
{
	local float hov, active;
	local vector bg, brd, txt;

	hov = BM_MouseIn(x, y, w, h);
	active = (hov || sub_sel);

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
	BM_DrawText(x + 9, y + floor((h - 8) * 0.5), label, 8, txt, 0.98);
	return hov;
};

float(float x, float y, float w, float h, string label, float active) BM_DrawTab =
{
	local float hov;
	local vector bg, brd, txt;

	hov = BM_MouseIn(x, y, w, h);
	bg = active ? '0.46 0.09 0.05' : (hov ? '0.26 0.13 0.08' : COL_GLASS_CARD);
	brd = active ? COL_ACCENT : (hov ? COL_ACCENT_HOT : COL_BORDER);
	txt = active ? COL_ACCENT : (hov ? COL_TEXT : COL_MUTED);

	BM_Fill(x, y, w, h, bg, active ? 0.92 : 0.75);
	BM_Outline(x, y, w, h, brd, active ? 0.95 : 0.55, 1);
	BM_DrawTextCentered(x + w * 0.5, y + floor((h - 8) * 0.5), label, 8, txt, 0.98);
	return hov;
};

float(float x, float y, float w, float h, string val, string placeholder, float focused) BM_DrawInputBox =
{
	local float hov, blink;
	local vector bg, brd;
	local string shown;

	hov = BM_MouseIn(x, y, w, h);
	bg = focused ? '0.16 0.10 0.06' : (hov ? '0.14 0.09 0.06' : '0.06 0.04 0.03');
	brd = focused ? COL_ACCENT : (hov ? COL_ACCENT_HOT : COL_BORDER);

	BM_Fill(x, y, w, h, bg, 0.92);
	BM_Outline(x, y, w, h, brd, focused ? 0.98 : 0.65, 1);

	shown = val;
	if (focused)
	{
		blink = floor(gettime() * 2.5);
		if (modulo(blink, 2) == 0)
			shown = strcat(val, "|");
		BM_DrawTextClipped(x + 6, y + floor((h - 8) * 0.5), w - 12, shown, 8, COL_TEXT, 0.98, FALSE);
	}
	else if (val == "")
	{
		BM_DrawTextClipped(x + 6, y + floor((h - 8) * 0.5), w - 12, placeholder, 8, COL_MUTED, 0.75, FALSE);
	}
	else
	{
		BM_DrawTextClipped(x + 6, y + floor((h - 8) * 0.5), w - 12, val, 8, COL_TEXT, 0.95, FALSE);
	}
	return hov;
};

float(float x, float y, float w, float h, string label, string val_str, float selected, float clicked) BM_DrawStepper =
{
	local float bw, vw, bx1, bx2, h1, h2, hov, lbl_w;

	hov = BM_MouseIn(x, y, w, h);
	BM_Fill(x, y, w, h, (hov || selected) ? '0.32 0.08 0.05' : COL_GLASS_CARD, 0.72);

	bw = 15;
	vw = (w < 235) ? 58 : 82;
	bx2 = x + w - bw - 3;
	bx1 = bx2 - bw - vw;
	lbl_w = max(24, bx1 - x - 10);
	BM_DrawTextClipped(x + 6, y + floor((h - 8) * 0.5), lbl_w, label, 8, (hov || selected) ? '1 1 1' : COL_TEXT, 0.95, FALSE);

	h1 = BM_MouseIn(bx1, y + 2, bw, h - 4);
	h2 = BM_MouseIn(bx2, y + 2, bw, h - 4);

	BM_Fill(bx1, y + 2, bw, h - 4, h1 ? '0.52 0.12 0.06' : '0.16 0.11 0.07', 0.90);
	BM_Outline(bx1, y + 2, bw, h - 4, h1 ? COL_ACCENT : COL_BORDER, 0.75, 1);
	BM_DrawTextCentered(bx1 + bw * 0.5, y + floor((h - 8) * 0.5), "<", 8, h1 ? COL_ACCENT : COL_TEXT, 0.95);

	BM_DrawTextCentered(bx1 + bw + vw * 0.5, y + floor((h - 8) * 0.5), val_str, 8, COL_ACCENT, 0.98);

	BM_Fill(bx2, y + 2, bw, h - 4, h2 ? '0.52 0.12 0.06' : '0.16 0.11 0.07', 0.90);
	BM_Outline(bx2, y + 2, bw, h - 4, h2 ? COL_ACCENT : COL_BORDER, 0.75, 1);
	BM_DrawTextCentered(bx2 + bw * 0.5, y + floor((h - 8) * 0.5), ">", 8, h2 ? COL_ACCENT : COL_TEXT, 0.95);

	if (clicked)
	{
		if (h1) return -1;
		if (h2) return 1;
	}
	return 0;
};

// Classic Quake slider bar
float(float sid, float x, float y, float w, float h, string label, float val, float min_v, float max_v, float step, float fmt_mode, float clicked) BM_DrawSlider =
{
	local float tx, tw, ty, t_norm, kx, hov_track, hov_row, dragging, new_v;
	local string vstr;

	tw = bound(80, floor(w * 0.34), 140);
	tx = x + w - tw - 54;
	ty = y + floor(h * 0.5);

	hov_row = BM_MouseIn(x, y, w, h);
	hov_track = BM_MouseIn(tx - 6, y + 1, tw + 12, h - 2);

	if (clicked && hov_track)
	{
		g_click_consumed = TRUE;
		g_active_slider = sid;
		g_mouse1_down = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
	}

	dragging = (g_mouse1_down && g_active_slider == sid);
	if (dragging)
	{
		t_norm = bound(0, (g_mx - tx) / max(1, tw), 1);
		new_v = min_v + t_norm * (max_v - min_v);
		if (step > 0)
			new_v = rint(new_v / step) * step;
		new_v = bound(min_v, new_v, max_v);
	}
	else
	{
		new_v = bound(min_v, val, max_v);
	}

	t_norm = (max_v > min_v) ? bound(0, (new_v - min_v) / (max_v - min_v), 1) : 0;

	if (hov_row || dragging)
		BM_Fill(x, y, w, h, '0.45 0.08 0.04', 0.72);

	BM_DrawText(x + 6, y + floor((h - 8) * 0.5), label, 8, (hov_row || dragging) ? '1 1 1' : COL_TEXT, 0.96);

	// Classic Quake brown slider rail
	BM_Fill(tx, ty - 2, tw, 4, '0.18 0.11 0.07', 0.95);
	BM_Outline(tx, ty - 2, tw, 4, '0.52 0.36 0.22', 0.85, 1);
	BM_Fill(tx + 1, ty - 1, max(0, (tw - 2) * t_norm), 2, '0.78 0.42 0.16', 0.92);

	// Classic Quake sliding notch
	kx = tx + t_norm * tw - 3;
	BM_Fill(kx, y + 3, 6, h - 6, dragging ? COL_ACCENT : '0.88 0.72 0.42', 0.98);
	BM_Outline(kx, y + 3, 6, h - 6, '0.20 0.10 0.04', 0.90, 1);

	if (fmt_mode == 0)
		vstr = ftos(rint(new_v));
	else if (fmt_mode == 1)
		vstr = sprintf("%.2f", new_v);
	else if (fmt_mode == 2)
		vstr = sprintf("%.1f", new_v);
	else if (fmt_mode == 3)
		vstr = strcat(ftos(rint(new_v * 100)), "%");
	else
		vstr = (new_v >= 0.005) ? sprintf("+%.2f", new_v) : sprintf("%.2f", new_v);

	BM_DrawTextRight(x + w - 6, y + floor((h - 8) * 0.5), vstr, 8, COL_ACCENT, 0.98);
	return new_v;
};

string(string cur, float maxlen, float key, float ascii, float allow_space) BM_EditString =
{
	local float len;

	if (key == K_BACKSPACE)
	{
		len = strlen(cur);
		if (len > 0)
			return substring(cur, 0, len - 1);
		return cur;
	}
	if (ascii >= 32 && ascii <= 126)
	{
		if (!allow_space && ascii == 32)
			return cur;
		if (ascii == 34 || ascii == 59)
			return cur;
		if (strlen(cur) >= maxlen)
			return cur;
		return strcat(cur, chr2str(ascii));
	}
	return cur;
};

// Levelshots for Host / Join map cards only
void() BM_InitLevelshots =
{
	local float sh, cnt, i, slash, dot;
	local string fn, nm, acc;

	precache_pic("levelshots/_unknown.jpg");
	sh = search_begin("levelshots/*.jpg", 1, 1);
	acc = " ";
	if (sh >= 0)
	{
		cnt = search_getsize(sh);
		for (i = 0; i < cnt; i = i + 1)
		{
			fn = strtolower(search_getfilename(sh, i));
			slash = strstrofs(fn, "/");
			if (slash >= 0)
				fn = substring(fn, slash + 1, strlen(fn) - slash - 1);
			dot = strstrofs(fn, ".jpg");
			if (dot > 0)
			{
				nm = substring(fn, 0, dot);
				acc = strcat(acc, nm, " ");
				precache_pic(strcat("levelshots/", nm, ".jpg"));
			}
		}
		search_end(sh);
	}
	g_levelshot_known = BM_ZoneSet(g_levelshot_known, acc);
};

string(string mapname) BM_CleanMapName =
{
	local string m;
	local float p;

	m = strtolower(mapname);
	if (m == "")
		return "";
	p = strstrofs(m, "maps/");
	if (p == 0)
		m = substring(m, 5, strlen(m) - 5);
	p = strstrofs(m, ".bsp");
	if (p > 0)
		m = substring(m, 0, p);
	return m;
};

string(string mapname) BM_LevelshotPic =
{
	local string m, path;

	m = BM_CleanMapName(mapname);
	if (m == "")
		return "levelshots/_unknown.jpg";
	if (g_levelshot_known != "" && strstrofs(g_levelshot_known, strcat(" ", m, " ")) >= 0)
		return strcat("levelshots/", m, ".jpg");
	path = strcat("levelshots/", m, ".jpg");
	if (getimagesize(path) != '0 0 0')
		return path;
	return "levelshots/_unknown.jpg";
};

// Classic Quake backdrop: live game with light dark tint when connected, gfx/conback.lmp when disconnected
void(float scrim_a) BM_DrawBackdrop =
{
	if (clientstate() >= CS_CONNECTED)
	{
		BM_Fill(0, 0, g_vw, g_vh, '0 0 0', scrim_a);
		return;
	}

	drawpic('0 0 0', "gfx/conback.lmp", g_vw * '1 0 0' + g_vh * '0 1 0', '1 1 1', 1.0, 0);
	BM_Fill(0, 0, g_vw, g_vh, '0 0 0', scrim_a);
};

float() BM_IsInLiveMatch =
{
	return (clientstate() >= CS_CONNECTED);
};

void() BM_DrawMouseCursor =
{
	BM_Fill(g_mx, g_my, 9, 1.5, COL_ACCENT, 0.95);
	BM_Fill(g_mx, g_my, 1.5, 9, COL_ACCENT, 0.95);
	BM_Fill(g_mx + 1.5, g_my + 1.5, 4, 4, COL_TEXT, 0.90);
};
