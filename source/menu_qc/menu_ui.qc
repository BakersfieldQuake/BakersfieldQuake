// BakersfieldQuake MenuQC shared dark-glass UI helpers, levelshots & background controls

// Palette (unezQuake dark-glass + BakersfieldQuake amber/gold)
vector COL_SCRIM       = '0.02 0.03 0.05';
vector COL_GLASS_DARK  = '0.04 0.06 0.10';
vector COL_GLASS_CARD  = '0.06 0.09 0.14';
vector COL_GLASS_HOVER = '0.10 0.14 0.22';
vector COL_BORDER      = '0.24 0.34 0.48';
vector COL_HIGHLIGHT   = '0.85 0.92 1.00';
vector COL_ACCENT      = '1.00 0.78 0.20';
vector COL_ACCENT_HOT  = '1.00 0.46 0.14';
vector COL_TEXT        = '0.95 0.97 1.00';
vector COL_MUTED       = '0.62 0.69 0.80';
vector COL_GOOD        = '0.32 0.92 0.56';
vector COL_WARN        = '1.00 0.78 0.22';
vector COL_BAD         = '1.00 0.34 0.28';

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
	BM_Fill(x + 1, y + 1, max(0, w - 2), 1, COL_HIGHLIGHT, 0.09);
	if (accent_top > 0)
		BM_Fill(x, y, w, accent_top, COL_ACCENT, 0.85);
};

void(float x, float y, string s, float sz, vector rgb, float a) BM_DrawText =
{
	local vector pos, sc;

	pos = x * '1 0 0' + y * '0 1 0';
	sc = sz * '1 1 0';
	drawstring(pos + '0.8 0.8 0', s, sc, '0 0 0', a * 0.72, 0);
	drawstring(pos, s, sc, rgb, a, 0);
};

void(float x, float y, string s, float sz, float a) BM_DrawColorText =
{
	local vector pos, sc;
	local string plain;

	pos = x * '1 0 0' + y * '0 1 0';
	sc = sz * '1 1 0';
	plain = strdecolorize(s);
	drawstring(pos + '0.8 0.8 0', plain, sc, '0 0 0', a * 0.72, 0);
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

// Returns TRUE if clicked this frame
float(float x, float y, float w, float h, string label, float sub_sel, float primary) BM_DrawButton =
{
	local float hov, active;
	local vector bg, brd, txt;
	local float tsz;

	hov = BM_MouseIn(x, y, w, h);
	active = (hov || sub_sel);

	if (primary)
	{
		bg = active ? '0.22 0.16 0.05' : '0.14 0.11 0.04';
		brd = active ? COL_ACCENT : '0.78 0.56 0.14';
		txt = active ? '1 0.94 0.76' : COL_ACCENT;
	}
	else
	{
		bg = active ? COL_GLASS_HOVER : COL_GLASS_CARD;
		brd = active ? COL_ACCENT : COL_BORDER;
		txt = active ? COL_TEXT : '0.84 0.88 0.94';
	}

	BM_Fill(x, y, w, h, bg, active ? 0.90 : 0.78);
	BM_Outline(x, y, w, h, brd, active ? 0.92 : 0.58, 1);
	if (active)
		BM_Fill(x, y, 2.5, h, primary ? COL_ACCENT_HOT : COL_ACCENT, 0.98);
	else if (primary)
		BM_Fill(x, y, 2.5, h, COL_ACCENT, 0.75);

	tsz = 8;
	BM_DrawText(x + 9, y + floor((h - tsz) * 0.5), label, tsz, txt, 0.98);
	return hov;
};

float(float x, float y, float w, float h, string label, float active) BM_DrawTab =
{
	local float hov;
	local vector bg, brd, txt;

	hov = BM_MouseIn(x, y, w, h);
	bg = active ? '0.12 0.16 0.24' : (hov ? COL_GLASS_HOVER : COL_GLASS_CARD);
	brd = active ? COL_ACCENT : (hov ? '0.45 0.58 0.76' : COL_BORDER);
	txt = active ? COL_ACCENT : (hov ? COL_TEXT : COL_MUTED);

	BM_Fill(x, y, w, h, bg, active ? 0.95 : 0.76);
	BM_Outline(x, y, w, h, brd, active ? 0.95 : 0.55, 1);
	if (active)
		BM_Fill(x, y + h - 2, w, 2, COL_ACCENT, 1.0);
	BM_DrawTextCentered(x + w * 0.5, y + floor((h - 8) * 0.5), label, 8, txt, 0.98);
	return hov;
};

float(float x, float y, float w, float h, string val, string placeholder, float focused) BM_DrawInputBox =
{
	local float hov, blink;
	local vector bg, brd;
	local string shown;

	hov = BM_MouseIn(x, y, w, h);
	bg = focused ? '0.07 0.10 0.16' : (hov ? '0.06 0.08 0.13' : '0.03 0.05 0.08');
	brd = focused ? COL_ACCENT : (hov ? '0.45 0.58 0.76' : COL_BORDER);

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

// Returns: -1 if minus clicked, +1 if plus clicked, 0 otherwise
float(float x, float y, float w, float h, string label, string val_str, float selected, float clicked) BM_DrawStepper =
{
	local float bw, vw, bx1, bx2, h1, h2, hov;

	hov = BM_MouseIn(x, y, w, h);
	BM_Fill(x, y, w, h, (hov || selected) ? COL_GLASS_HOVER : COL_GLASS_CARD, 0.78);
	BM_Outline(x, y, w, h, selected ? COL_ACCENT : COL_BORDER, selected ? 0.90 : 0.52, 1);

	BM_DrawText(x + 6, y + floor((h - 8) * 0.5), label, 8, selected ? COL_TEXT : COL_MUTED, 0.95);

	bw = 16;
	vw = 76;
	bx2 = x + w - bw - 3;
	bx1 = bx2 - bw - vw;
	h1 = BM_MouseIn(bx1, y + 2, bw, h - 4);
	h2 = BM_MouseIn(bx2, y + 2, bw, h - 4);

	BM_Fill(bx1, y + 2, bw, h - 4, h1 ? '0.20 0.28 0.40' : '0.09 0.13 0.20', 0.92);
	BM_Outline(bx1, y + 2, bw, h - 4, h1 ? COL_ACCENT : COL_BORDER, 0.75, 1);
	BM_DrawTextCentered(bx1 + bw * 0.5, y + floor((h - 8) * 0.5), "<", 8, h1 ? COL_ACCENT : COL_TEXT, 0.95);

	BM_DrawTextCentered(bx1 + bw + vw * 0.5, y + floor((h - 8) * 0.5), val_str, 8, COL_ACCENT, 0.98);

	BM_Fill(bx2, y + 2, bw, h - 4, h2 ? '0.20 0.28 0.40' : '0.09 0.13 0.20', 0.92);
	BM_Outline(bx2, y + 2, bw, h - 4, h2 ? COL_ACCENT : COL_BORDER, 0.75, 1);
	BM_DrawTextCentered(bx2 + bw * 0.5, y + floor((h - 8) * 0.5), ">", 8, h2 ? COL_ACCENT : COL_TEXT, 0.95);

	if (clicked)
	{
		if (h1)
			return -1;
		if (h2)
			return 1;
	}
	return 0;
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

// Scan levelshots/*.jpg once at init so missing thumbnails never spam console
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

void() BM_InitBackdrop =
{
	local string list_str, tok;
	local float n, i;

	if (g_bg_buf > 0)
		buf_del(g_bg_buf);
	g_bg_buf = buf_create();
	g_bg_slide_count = 0;

	list_str = cvar_string("menu_background_map");
	if (list_str == "")
		list_str = "soi6 soicowboy_bkk bakersfielddowntown little_st_james terminal21 goldenwest";
	n = tokenize(list_str);
	for (i = 0; i < n && g_bg_slide_count < 24; i = i + 1)
	{
		tok = BM_CleanMapName(argv(i));
		if (tok != "")
		{
			bufstr_add(g_bg_buf, tok, 0);
			g_bg_slide_count = g_bg_slide_count + 1;
		}
	}
	if (g_bg_slide_count <= 0)
	{
		bufstr_add(g_bg_buf, "soi6", 0);
		g_bg_slide_count = 1;
	}
	g_bg_slide_idx = floor(random() * g_bg_slide_count);
	if (g_bg_slide_idx >= g_bg_slide_count)
		g_bg_slide_idx = 0;
	g_bg_slide_prev = g_bg_slide_idx;
	g_bg_slide_t = gettime();
};

void() BM_ShutdownBackdrop =
{
	if (g_bg_buf > 0)
		buf_del(g_bg_buf);
	g_bg_buf = 0;
	g_bg_slide_count = 0;
};

void() BM_NextBackdrop =
{
	if (g_bg_slide_count <= 0)
		BM_InitBackdrop();
	g_bg_slide_prev = g_bg_slide_idx;
	g_bg_slide_idx = modulo(g_bg_slide_idx + 1, max(1, g_bg_slide_count));
	g_bg_slide_t = gettime();
};

string() BM_CurrentBackdropMap =
{
	if (g_bg_slide_count <= 0 || g_bg_buf <= 0)
		return "soi6";
	return bufstr_get(g_bg_buf, bound(0, g_bg_slide_idx, g_bg_slide_count - 1));
};

void(string pic_path, float phase, float alpha) BM_DrawPanPic =
{
	local vector isz;
	local float iw, ih, scale, dw, dh, slack_x, slack_y, px, py;

	isz = getimagesize(pic_path);
	iw = (isz_x > 0) ? isz_x : 16;
	ih = (isz_y > 0) ? isz_y : 10;

	scale = max(g_vw / iw, g_vh / ih) * 1.12;
	dw = iw * scale;
	dh = ih * scale;
	slack_x = max(0, dw - g_vw);
	slack_y = max(0, dh - g_vh);

	px = -0.5 * slack_x + 0.45 * slack_x * sin(phase * 0.35);
	py = -0.5 * slack_y + 0.45 * slack_y * cos(phase * 0.27);
	drawpic(px * '1 0 0' + py * '0 1 0', pic_path, dw * '1 0 0' + dh * '0 1 0', '1 1 1', alpha, 0);
};

void(float scrim_a) BM_DrawBackdrop =
{
	local float now, elapsed, fade, slide_dur;
	local string cur_pic, prev_pic;

	if (clientstate() >= CS_CONNECTED)
	{
		BM_Fill(0, 0, g_vw, g_vh, COL_SCRIM, scrim_a);
		return;
	}

	BM_Fill(0, 0, g_vw, g_vh, '0.02 0.03 0.05', 1.0);
	if (stof(cvar_string("menu_background")) != 0 && g_bg_slide_count > 0 && g_bg_buf > 0)
	{
		slide_dur = 8.0;
		now = gettime();
		elapsed = now - g_bg_slide_t;
		if (elapsed >= slide_dur)
		{
			BM_NextBackdrop();
			elapsed = 0;
		}
		drawsetcliparea(0, 0, g_vw, g_vh);
		cur_pic = BM_LevelshotPic(bufstr_get(g_bg_buf, g_bg_slide_idx));
		if (elapsed < 1.2 && g_bg_slide_prev != g_bg_slide_idx)
		{
			fade = elapsed / 1.2;
			prev_pic = BM_LevelshotPic(bufstr_get(g_bg_buf, g_bg_slide_prev));
			BM_DrawPanPic(prev_pic, now, 1.0);
			BM_DrawPanPic(cur_pic, now + 2.0, fade);
		}
		else
		{
			BM_DrawPanPic(cur_pic, now + 2.0, 1.0);
		}
		drawresetcliparea();
	}
	BM_Fill(0, 0, g_vw, g_vh, COL_SCRIM, scrim_a);
};

float() BM_IsInLiveMatch =
{
	return (clientstate() >= CS_CONNECTED);
};

void() BM_DrawMouseCursor =
{
	// Subtle sharp vector cursor at getmousepos() so menu pointer is always crisp
	BM_Fill(g_mx, g_my, 9, 1.5, COL_ACCENT, 0.95);
	BM_Fill(g_mx, g_my, 1.5, 9, COL_ACCENT, 0.95);
	BM_Fill(g_mx + 1.5, g_my + 1.5, 4, 4, COL_TEXT, 0.90);
};
