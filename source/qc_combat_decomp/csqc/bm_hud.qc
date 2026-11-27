/*
================
BAKERSFIELD LAN HUD OVERLAY (drawn on top of Combat+'s own HUD)

Reads the stats progs.dat sends with addstat (bm_match.qc BM_Stats):
	52 magazine rounds left   53 magazine size   54 reload progress 1..100 (0 = not reloading)
	55 spawn protection, tenths of a second       56 your lead over the pack
	57 your underdog boost 0..100                 58 1 while health is regenerating
	59 1 in the local warmup game                 60 the leader's lead       61 the leader's name

Called from CSQC_UpdateView right after DrawHUD().
================
*/

float	BMST_MAG		= 52;
float	BMST_MAGMAX		= 53;
float	BMST_RELOAD		= 54;
float	BMST_PROT		= 55;
float	BMST_HEAT		= 56;
float	BMST_BOOST		= 57;
float	BMST_REGEN		= 58;
float	BMST_WARMUP		= 59;
float	BMST_LHEAT		= 60;
float	BMST_LEADER		= 72;		// a string stat: 72-75 (on 61 it overlapped LX/LY/LZ)
float	BMST_LX			= 62;
float	BMST_LY			= 63;
float	BMST_LZ			= 64;
float	BMST_LSHOW		= 65;
float	BMST_JPFUEL		= 66;		// the jetpack's fuel left, tenths of a second (jetpack.qc)
float	BMST_JPMAX		= 67;		// a full tank, tenths of a second
float	BMST_MILK		= 68;		// milk on your screen: 60 just splashed, counting down in tenths of a second (milky.qc)
float	BMST_SLOT		= 71;		// active weapon slot (16 = BM_FG7 = M4A1)
float	BMST_BOTMASK		= 76;		// bitmask of live visible bots in slots 0..15
float	BMST_BOTCNT		= 77;		// active bot count
float	BMST_TOYMASK	= 78;		// bitmask of ready fun-gun superweapons & Winged John
float	BMST_TOYCD		= 79;		// Winged John summon cooldown remaining (seconds)
float	BMST_PLAYERMASK	= 80;		// bitmask of live visible human players in slots 0..15
float	BMST_INTRO		= 69;
float	BMST_BAKO_PADRE	= 120;		// Bakersfield-ish Padre Hotel structural integrity % (101=hidden, 1..99=damaged, 0=collapsed)
float	BMST_BAKO_EVENT	= 121;		// Bakersfield-ish active collapse/rebuild event code
void(float w) BM_DrawBakoDestructHUD;

// intro.dem screen milk drips (live gameplay bursts use 3D world milk only, with no white flash or HUD overlay)
void(float w, float h) Milk_DrawHUD =
{
	local float st, age, a, y;

	st = getstati (BMST_MILK);
	if (st <= 0)
		return;
	age = (60 - st) / 10;
	y = age * h * 0.07;		// the drips run down
	a = st / 25;
	if (a > 1)
		a = 1;
	drawpic ((y - h * 0.97) * '0 1 0', "gfx/milkdrips", w * '1 0 0' + h * '0 1 0', '1 1 1', a * 0.8, 0);
	drawpic (y * '0 1 0', "gfx/milkdrips", w * '1 0 0' + h * '0 1 0', '1 1 1', a * 0.95, 0);
};

float	jp_hud_prev;			// last frame's fuel, to notice it running out
float	jp_hud_empty_t;			// the EMPTY tank stays up until then

// the jetpack's clear glass fuel tank, on the left edge of the screen: orange fuel that drains, red and flashing when low,
// a flashing red EMPTY tank for 3 s once it has run out. Nothing while you have no jetpack.
void(float x, float y, string s, float sz, vector rgb, float a) BM_Centered;

void(float w, float h, float hp) JP_DrawHUD =
{
	local float f, mx, frac, x0, y0, tw, th, lvl, fl, empty, low, a, sn;
	local vector fuel, edge;
	local string s;

	f = getstati (BMST_JPFUEL);
	mx = getstati (BMST_JPMAX);
	if (jp_hud_prev > 0 && f <= 0 && hp > 0)
		jp_hud_empty_t = time + 3;
	jp_hud_prev = f;
	if (hp <= 0)
		return;
	empty = (f <= 0 && time < jp_hud_empty_t);
	if (f <= 0 && !empty)
		return;
	if (mx <= 0)
		mx = 300;
	frac = f / mx;
	if (frac > 1)
		frac = 1;
	low = (f > 0 && f <= 50);		// the last 5 seconds
	sn = sin (time * 10);		// sin is a __variant: keep the result in a local
	fl = 0.5 + 0.5 * sn;

	tw = 22;
	th = 92;
	x0 = 6;				// against the left edge of the screen, above Combat+'s status bar (which starts about 54 units from the bottom)
	if (cvar ("bm_hud_style") == 2 || cvar ("bm_hud_style") == 3)
		y0 = h - 180;
	else
		y0 = h - 167;

	// the glass: a faint blue inside, a white edge, a rim and cap
	edge = '0.8 0.95 1';
	if (empty || low)
		edge = '1 0.35 0.25';
	drawfill (x0 * '1 0 0' + y0 * '0 1 0', tw * '1 0 0' + th * '0 1 0', '0.45 0.65 0.8', 0.16, 0);
	drawfill (x0 * '1 0 0' + y0 * '0 1 0', tw * '1 0 0' + '0 1 0', edge, 0.75, 0);
	drawfill (x0 * '1 0 0' + (y0 + th - 1) * '0 1 0', tw * '1 0 0' + '0 1 0', edge, 0.75, 0);
	drawfill (x0 * '1 0 0' + y0 * '0 1 0', '1 0 0' + th * '0 1 0', edge, 0.75, 0);
	drawfill ((x0 + tw - 1) * '1 0 0' + y0 * '0 1 0', '1 0 0' + th * '0 1 0', edge, 0.75, 0);
	drawfill ((x0 + 6) * '1 0 0' + (y0 - 4) * '0 1 0', '10 0 0' + '0 4 0', '0.7 0.7 0.75', 0.9, 0);		// the filler cap

	// the fuel: from the bottom up
	lvl = (th - 4) * frac;
	if (lvl > 0)
	{
		fuel = '1 0.62 0.12';
		if (low)
			fuel = '1 0.2 0.1';
		a = 0.8;
		if (low)
			a = 0.45 + 0.4 * fl;
		drawfill ((x0 + 2) * '1 0 0' + (y0 + th - 2 - lvl) * '0 1 0', (tw - 4) * '1 0 0' + lvl * '0 1 0', fuel, a, 0);
		drawfill ((x0 + 2) * '1 0 0' + (y0 + th - 2 - lvl) * '0 1 0', (tw - 4) * '1 0 0' + '0 1 0', '1 0.92 0.55', 0.95, 0);		// the surface
	}

	// the glass catching the light, and the quarter marks
	drawfill ((x0 + 3) * '1 0 0' + (y0 + 4) * '0 1 0', '2 0 0' + (th - 8) * '0 1 0', '1 1 1', 0.22, 0);
	drawfill ((x0 + tw) * '1 0 0' + (y0 + th * 0.25) * '0 1 0', '4 0 0' + '0 1 0', edge, 0.7, 0);
	drawfill ((x0 + tw) * '1 0 0' + (y0 + th * 0.5) * '0 1 0', '6 0 0' + '0 1 0', edge, 0.7, 0);
	drawfill ((x0 + tw) * '1 0 0' + (y0 + th * 0.75) * '0 1 0', '4 0 0' + '0 1 0', edge, 0.7, 0);

	if (empty)
		BM_Centered (x0 + tw * 0.5 + 8, y0 + th + 5, "^1EMPTY", 8, '1 1 1', 0.35 + 0.65 * fl);		// nudged right: centred it hangs off the screen edge
	else
	{
		s = strcat (ftos (ceil (f / 10)), "s");
		if (low)
			s = strcat ("^1", s);
		BM_Centered (x0 + tw * 0.5, y0 + th + 5, s, 8, '1 1 1', 0.9);
	}
};

float	bm_topright_y;

float() JP_IsVisible =
{
	local float hp, jf;

	hp = getstati (STAT_HEALTH);
	if (hp <= 0)
		return FALSE;
	jf = getstati (BMST_JPFUEL);
	if (jf > 0)
		return TRUE;
	if (time < jp_hud_empty_t)
		return TRUE;
	return FALSE;
};

float(float h) BM_CornerBottomY =
{
	local float hs;

	hs = cvar ("bm_hud_style");
	if (hs == 2 || hs == 3)
		return h - 72;
	return h - 56;
};

void(float x, float y, string s, float sz, float a) BM_DrawColorShadowRaw =
{
	local vector sc;
	local string plain;

	sc = sz * '1 1 0';
	plain = strdecolorize (s);
	drawstring ((x + 0.7) * '1 0 0' + (y + 0.7) * '0 1 0', plain, sc, '0 0 0', 0.85 * a, 0);
	drawcolorcodedstring (x * '1 0 0' + y * '0 1 0', s, sc, a, 0);
};

void(float x, float y, string s, float sz, float a) BM_DrawColorShadow =
{
	BM_DrawColorShadowRaw (x, y, s, BM_UIScale (sz), a);
};

void(float rx, float y, string s, float sz, float a) BM_ShadowColorRight =
{
	local float wd;

	wd = BM_UIStringWidth (s, TRUE, sz * '1 1 0');
	BM_DrawColorShadow (rx - wd, y, s, sz, a);
};

// text centred on x
void(float x, float y, string s, float sz, vector rgb, float a) BM_Centered =
{
	local float wd;

	wd = BM_UIStringWidth (s, TRUE, sz * '1 1 0');	// variants: keep builtin results in locals
	BM_DrawColorShadow (x - wd * 0.5, y, s, sz, a);
};

// compact lower-screen toast replacing the engine's large mid-screen centerprints
string	bm_cp_l1;
string	bm_cp_l2;
string	bm_cp_l3;
string	bm_cp_l4;
string	bm_cp_l5;
string	bm_cp_l6;
string	bm_cp_l7;
float	bm_cp_n;
float	bm_cp_end;
float	bm_cp_top_y;		// top of this frame's bottom-left toast (its base when none shows), so other bottom-left text can stack above it

void() BM_ClearCenterPrint =
{
	if (bm_cp_n >= 1)
		strunzone (bm_cp_l1);
	if (bm_cp_n >= 2)
		strunzone (bm_cp_l2);
	if (bm_cp_n >= 3)
		strunzone (bm_cp_l3);
	if (bm_cp_n >= 4)
		strunzone (bm_cp_l4);
	if (bm_cp_n >= 5)
		strunzone (bm_cp_l5);
	if (bm_cp_n >= 6)
		strunzone (bm_cp_l6);
	if (bm_cp_n >= 7)
		strunzone (bm_cp_l7);
	bm_cp_l1 = "";
	bm_cp_l2 = "";
	bm_cp_l3 = "";
	bm_cp_l4 = "";
	bm_cp_l5 = "";
	bm_cp_l6 = "";
	bm_cp_l7 = "";
	bm_cp_n = 0;
	bm_cp_end = 0;
};

float(string s) CSQC_Parse_CenterPrint =
{
	local float len, nl, rlen, slen, hit1, hit2;
	local string rest, seg;

	if (intermission)
		return 0;
	if (getstati (BMST_INTRO) == 900 || cvar ("bm_menu_bg") > 0)
		return 1;

	BM_ClearCenterPrint ();
	len = strlen (s);
	if (len <= 0)
		return 1;

	hit1 = strstrofs (s, "Welcome to Quake 1.5");
	hit2 = strstrofs (s, "QQQ powerup died");
	if (hit1 >= 0 || hit2 >= 0)
		return 1;

	rest = s;
	while (rest != "" && bm_cp_n < 7)
	{
		nl = strstrofs (rest, "\n");
		rlen = strlen (rest);
		if (nl < 0)
		{
			seg = rest;
			rest = "";
		}
		else
		{
			seg = substring (rest, 0, nl);
			rest = substring (rest, nl + 1, rlen - nl - 1);
		}
		slen = strlen (seg);
		if (slen > 1 && substring (seg, 0, 1) == " ")
			seg = substring (seg, 1, slen - 1);
		if (seg != "" && seg != " ")
		{
			bm_cp_n = bm_cp_n + 1;
			if (bm_cp_n == 1)
				bm_cp_l1 = strzone (seg);
			else if (bm_cp_n == 2)
				bm_cp_l2 = strzone (seg);
			else if (bm_cp_n == 3)
				bm_cp_l3 = strzone (seg);
			else if (bm_cp_n == 4)
				bm_cp_l4 = strzone (seg);
			else if (bm_cp_n == 5)
				bm_cp_l5 = strzone (seg);
			else if (bm_cp_n == 6)
				bm_cp_l6 = strzone (seg);
			else if (bm_cp_n == 7)
				bm_cp_l7 = strzone (seg);
		}
	}

	if (bm_cp_n <= 0)
		return 1;
	if (bm_cp_n == 1)
		bm_cp_end = time + 1.35;
	else if (bm_cp_n == 2)
		bm_cp_end = time + 1.90;
	else
		bm_cp_end = time + 2.25;
	return 1;
};

float(float w, float h) BM_MinimapTopY;

void(float w, float h) BM_DrawCenterPrint =
{
	local float sz, wd, maxw, lim, step, x0, y0, ph, rem, a, base, mtop;

	base = BM_CornerBottomY (h);
	if (getstati (93) == 2)		// 1st-person Winged John readout fills BM_CornerBottomY(h) - 27 .. - 4 (john_bird_hud.qc): stack the toast above it
		base = base - 30;
	mtop = BM_MinimapTopY (w, h);
	if (mtop > 0 && mtop < base)
		base = mtop;
	bm_cp_top_y = base;
	if (bm_cp_n <= 0 || time >= bm_cp_end)
		return;

	sz = floor (h * 0.0145 + 0.5);
	if (sz < 5)
		sz = 5;
	if (sz > 7)
		sz = 7;
	sz = BM_UIScale (sz);

	maxw = stringwidth (bm_cp_l1, TRUE, sz * '1 1 0');
	if (bm_cp_n >= 2)
	{
		wd = stringwidth (bm_cp_l2, TRUE, sz * '1 1 0');
		if (wd > maxw) maxw = wd;
	}
	if (bm_cp_n >= 3)
	{
		wd = stringwidth (bm_cp_l3, TRUE, sz * '1 1 0');
		if (wd > maxw) maxw = wd;
	}
	if (bm_cp_n >= 4)
	{
		wd = stringwidth (bm_cp_l4, TRUE, sz * '1 1 0');
		if (wd > maxw) maxw = wd;
	}
	if (bm_cp_n >= 5)
	{
		wd = stringwidth (bm_cp_l5, TRUE, sz * '1 1 0');
		if (wd > maxw) maxw = wd;
	}
	if (bm_cp_n >= 6)
	{
		wd = stringwidth (bm_cp_l6, TRUE, sz * '1 1 0');
		if (wd > maxw) maxw = wd;
	}
	if (bm_cp_n >= 7)
	{
		wd = stringwidth (bm_cp_l7, TRUE, sz * '1 1 0');
		if (wd > maxw) maxw = wd;
	}

	x0 = JP_IsVisible () ? 36 : 10;
	lim = w * 0.48;
	if (maxw > lim && maxw > 0)
	{
		sz = sz * (lim / maxw);
		if (sz < 4)
			sz = 4;
	}

	rem = bm_cp_end - time;
	a = 0.94;
	if (rem < 0.30)
		a = 0.94 * (rem / 0.30);

	step = sz + 2;
	ph = bm_cp_n * step;
	y0 = base - ph;
	bm_cp_top_y = y0;

	BM_DrawColorShadowRaw (x0, y0, bm_cp_l1, sz, a);
	if (bm_cp_n >= 2)
		BM_DrawColorShadowRaw (x0, y0 + step, bm_cp_l2, sz, a);
	if (bm_cp_n >= 3)
		BM_DrawColorShadowRaw (x0, y0 + step * 2, bm_cp_l3, sz, a);
	if (bm_cp_n >= 4)
		BM_DrawColorShadowRaw (x0, y0 + step * 3, bm_cp_l4, sz, a);
	if (bm_cp_n >= 5)
		BM_DrawColorShadowRaw (x0, y0 + step * 4, bm_cp_l5, sz, a);
	if (bm_cp_n >= 6)
		BM_DrawColorShadowRaw (x0, y0 + step * 5, bm_cp_l6, sz, a);
	if (bm_cp_n >= 7)
		BM_DrawColorShadowRaw (x0, y0 + step * 6, bm_cp_l7, sz, a);
};

// Resolve a player's display name by 0-based slot index and 1-based entity number.
// A player's entity number is always its 0-based player slot + 1 here, so one lookup by slot (entno - 1) does it;
// a negative index would ask for a scoreboard rank instead of a slot.
string(float slot, float entno) BM_PlayerNameBySlot =
{
	if (entno >= 1)
		return getplayerkeyvalue (entno - 1, "name");
	return getplayerkeyvalue (slot, "name");
};

float	bm_tag_font;

// Draw a crisp, non-brown close/medium-range LOS nameplate for a bot or player
void(float w, float h, vector eye, float entno, float slot, float is_bot, float lshow, vector lpos) BM_DrawNameTag =
{
	local float act, dist, a, sz, wd, tx, ty, old_font, use_sz;
	local vector org, sp, sv, col, brd;
	local string pname;

	act = getentity (entno, 0);
	if (!act)
		return;

	org = getentityvec (entno, E_ORIGIN);
	if (!is_bot && lshow && vlen (org - lpos) < 28)
		return;

	dist = vlen (org - eye);
	if (dist <= 28 || dist >= 560)
		return;

	traceline (eye, org + '0 0 22', TRUE, world);
	if (trace_startsolid || trace_allsolid || trace_fraction < 0.995)
		return;

	sp = cs_project (org + '0 0 44');
	if (sp_z <= 0 || sp_x <= 16 || sp_x >= w - 16 || sp_y <= 16 || sp_y >= h - 32)
		return;

	pname = BM_PlayerNameBySlot (slot, entno);
	if (pname == "")
	{
		if (is_bot)
			pname = "[BOT]";
		else
			return;
	}
	pname = strdecolorize (pname);
	if (pname == "")
		return;

	a = 0.95;
	if (dist > 340)
		a = 0.95 * (1 - (dist - 340) / 220);
	if (a <= 0.04)
		return;

	old_font = drawfont;
	if (bm_tag_font > 0)
	{
		drawfont = bm_tag_font;
		sz = 8.5;
	}
	else
	{
		sz = 7;
	}
	use_sz = sz;
	sv = use_sz * '1 1 0';
	wd = stringwidth (pname, FALSE, sv);
	tx = sp_x - wd * 0.5;
	ty = sp_y - 13;

	col = is_bot ? '0.78 0.95 1.0' : '0.96 0.99 1.0';
	brd = is_bot ? '0.32 0.62 0.80' : '0.50 0.72 0.88';

	drawstring ((tx + 0.8) * '1 0 0' + (ty + 0.8) * '0 1 0', pname, sv, '0 0 0', 0.92 * a, 0);
	drawstring (tx * '1 0 0' + ty * '0 1 0', pname, sv, col, a, 0);
	drawfont = old_font;
};

// 3D-projected floating [BOT] <Name> overhead tags above nearby visible living enemy bots
void(float w, float h) BM_DrawBotTags =
{
	local float mask, i, bit, entno;
	local vector eye;

	if (showscores)
		return;
	mask = getstati (BMST_BOTMASK);
	if (mask <= 0)
		return;
	if (cvar ("bm_bot_tags") == 0)
		return;

	eye = getpropertyvec (VF_ORIGIN);
	i = 0;
	bit = 1;
	while (i < 16)
	{
		entno = i + 1;
		if ((mask & bit) && entno != player_localentnum)
			BM_DrawNameTag (w, h, eye, entno, i, TRUE, FALSE, '0 0 0');
		bit = bit * 2;
		i = i + 1;
	}
};

// Close-up 3D-projected overhead nameplates for nearby visible human players in multiplayer
void(float w, float h) BM_DrawPlayerTags =
{
	local float mask, i, bit, entno, lshow;
	local vector eye, lpos;

	if (!deathmatch && !coop)
		return;
	if (showscores)
		return;
	if (cvar ("bm_player_tags") == 0)
		return;
	mask = getstati (BMST_PLAYERMASK);
	if (mask <= 0)
		return;

	lshow = getstati (BMST_LSHOW);
	lpos = '0 0 0';
	if (lshow)
	{
		lpos_x = getstati (BMST_LX);
		lpos_y = getstati (BMST_LY);
		lpos_z = getstati (BMST_LZ);
	}

	eye = getpropertyvec (VF_ORIGIN);
	i = 0;
	bit = 1;
	while (i < 16)
	{
		entno = i + 1;
		if ((mask & bit) && entno != player_localentnum)
			BM_DrawNameTag (w, h, eye, entno, i, FALSE, lshow, lpos);
		bit = bit * 2;
		i = i + 1;
	}
};

// Cached keybind label resolver: avoids scanning 767 keybinds per call (up to 3,068 calls/frame in vehicles!)
string bm_bl_cmd[8];
float  bm_bl_bmap[8];
string bm_bl_val[8];
float  bm_bl_t[8];
float  bm_bl_rev;
float  bm_bl_next;

string(string cmd, string fallback) BM_ActiveBindLabel =
{
	local float bmap, n, i, kn, tmask, mmt_on, jb_on, rev, slot;
	local string raw, kname, kb, resolved;

	bmap = 0;
	if (cvar ("bm_veh_config") != 0)
	{
		tmask = getstati (BMST_TOYMASK);
		mmt_on = getstati (86);
		jb_on = getstati (93);
		if ((tmask & 512) != 0 || mmt_on > 0 || jb_on > 0)
			bmap = 1;
	}
	rev = cvar ("bm_veh_rev");
	if (rev != bm_bl_rev)
	{
		bm_bl_rev = rev;
		for (i = 0; i < 8; i = i + 1)
			bm_bl_t[i] = 0;
	}
	for (i = 0; i < 8; i = i + 1)
	{
		if (bm_bl_t[i] > time && bm_bl_bmap[i] == bmap && bm_bl_cmd[i] == cmd)
			return (bm_bl_val[i] != "") ? bm_bl_val[i] : fallback;
	}

	resolved = "";
	if (bmap != 0)
	{
		for (i = 1; i < 768; i = i + 1)
		{
			kb = getkeybind_bindmap (i, bmap);
			if (kb == cmd)
			{
				kname = keynumtostring (i);
				kname = strtoupper (kname);
				if (kname != "")
				{
					resolved = kname;
					break;
				}
			}
		}
	}
	else
	{
		raw = findkeysforcommand (cmd, 0);
		if (raw != "")
		{
			n = tokenize (raw);
			for (i = 0; i < n; i = i + 1)
			{
				kn = stof (argv (i));
				if (kn > 0)
				{
					kname = keynumtostring (kn);
					kname = strtoupper (kname);
					if (kname != "")
					{
						resolved = kname;
						break;
					}
				}
			}
		}
	}

	slot = bm_bl_next;
	bm_bl_next = slot + 1;
	if (bm_bl_next >= 8)
		bm_bl_next = 0;
	if (bm_bl_cmd[slot] != "")
		strunzone (bm_bl_cmd[slot]);
	if (bm_bl_val[slot] != "")
		strunzone (bm_bl_val[slot]);
	bm_bl_cmd[slot] = strzone (cmd);
	bm_bl_val[slot] = (resolved != "") ? strzone (resolved) : "";
	bm_bl_bmap[slot] = bmap;
	bm_bl_t[slot] = time + 0.50;
	return (resolved != "") ? resolved : fallback;
};

// top-right Flying Blue Shell ready banner & bottom-right vehicle Bail/Camera prompt (fun-gun toy dock bar removed)
void(float w, float h, float hp, float y0) BM_DrawToyDock =
{
	local float tmask, sn, hide_veh_hint, hit_nitro, jb_on;
	local string bs, exit_k, cam_k;

	if (hp <= 0 || showscores || cvar ("bm_hud_toys") == 0)
		return;
	tmask = getstati (BMST_TOYMASK);

	if (tmask & 128)
	{
		sn = sin (time * 9);
		bs = "^5[9] FLYING BLUE SHELL READY!";
		BM_ShadowColorRight (w - 8, y0, bs, 5, 0.75 + 0.25 * sn);
		bm_topright_y = y0 + ((BM_GetUIFont () > 0) ? 10.5 : 9);
	}
	hide_veh_hint = FALSE;
	jb_on = getstati (93);
	if (jb_on > 0)
		hide_veh_hint = TRUE;
	if (bm_cp_n > 0 && time < bm_cp_end)
	{
		hit_nitro = strstrofs (bm_cp_l1, "NITRO ");
		if (hit_nitro >= 0)
			hide_veh_hint = TRUE;
	}
	if ((tmask & 256) && !hide_veh_hint)
	{
		exit_k = BM_ActiveBindLabel ("impulse 86", "H");
		cam_k = BM_ActiveBindLabel ("impulse 87", "K");
		BM_ShadowColorRight (w - 8, BM_CornerBottomY (h) - 7, strcat ("^3[", exit_k, "]^7 Bail / Dive   ^3[", cam_k, "]^7 Camera"), 5, 0.90);
	}
};

// 2-line LAN Keybind Cheat-Sheet drawn at bottom of screen while holding TAB (+showscores)
void() BM_DrawScoreKeys =
{
	local float w, h, cx, y0, sz, w1, w2, pw;
	local string l1, l2;

	if (!showscores || inMenu || intermission)
		return;
	w = cvar ("vid_conwidth");
	h = cvar ("vid_conheight");
	cx = w * 0.5;
	sz = BM_UIScale (5);
	l1 = "^3GUNS: ^7Q^8:GunWheel  ^7C^8:M4  ^7M^8:Garand  ^79^8:MegaMan  ^75^8:Milky  ^71^8:Hammer  ^7R^8:Reload/Twirl";
	l2 = "^3TOYS: ^7F^8:RobDob  ^7I^8:Jar  ^7X^8:Pickle  ^7B^8:NetSend  ^7U^8:Dookie  ^7G^8:Wheelman  ^7Z^8:Kyle  ^7L^8:Cyrax  ^7H^8:Drive/Ride  ^7P^8:JohnBird  ^7J^8/2xSpace:Jetpack";
	w1 = stringwidth (l1, TRUE, sz * '1 1 0');
	w2 = stringwidth (l2, TRUE, sz * '1 1 0');
	pw = w1;
	if (w2 > pw)
		pw = w2;
	if (pw > w - 12 && pw > 0)
	{
		sz = sz * ((w - 12) / pw);
	}
	y0 = h - 65;
	w1 = stringwidth (l1, TRUE, sz * '1 1 0');
	w2 = stringwidth (l2, TRUE, sz * '1 1 0');
	BM_DrawColorShadowRaw (cx - w1 * 0.5, y0, l1, sz, 0.95);
	BM_DrawColorShadowRaw (cx - w2 * 0.5, y0 + sz + 2, l2, sz, 0.95);
};

void(float raw_w, float raw_h) KY_DrawHUD =
{
	local float w, h, hp, mode, prog, dist, cx, cy, bw, bh, x0, y0, r, arm, th, pulse, sx, sy;
	local vector wp, sp, col;
	local string lbl;

	hp = getstati (STAT_HEALTH);
	if (hp <= 0)
		return;
	mode = getstati (103);
	if (mode <= 0)
		return;
	w = vid_conwidth;
	h = vid_conheight;
	if (w <= 0)
		w = raw_w;
	if (h <= 0)
		h = raw_h;
	if (w <= 0 || h <= 0)
		return;
	prog = bound (0, getstati (104), 100);
	dist = getstati (105);
	cx = w * 0.5;
	cy = h * 0.5;

	// Mode 1: Throw Wind-Up Power Bar below crosshair
	if (mode == 1)
	{
		bw = 92;
		bh = 6;
		x0 = cx - bw * 0.5;
		y0 = cy + 26;
		drawfill ([x0 - 1, y0 - 1, 0], [bw + 2, bh + 2, 0], '0 0 0', 0.72, 0);
		col = (prog >= 95) ? '1 0.35 0.15' : ((prog >= 50) ? '1 0.78 0.15' : '0.35 0.85 1');
		drawfill ([x0, y0, 0], [bw * (prog / 100), bh, 0], col, 0.92, 0);
		if (prog >= 95)
			lbl = "^1MAX THROW WIND-UP!";
		else if (prog >= 45)
			lbl = strcat ("^3THROW POWER ", ftos (prog), "%");
		else
			lbl = strcat ("^7WINDING UP ", ftos (prog), "%");
		BM_Centered (cx, y0 + 9, lbl, 5.5, '1 1 1', 0.92);
		return;
	}

	// Modes 2, 3, 4: Bird / Sky-Vehicle Lock-On Targeting Reticle projected onto target's live 3D screen position!
	wp_x = getstati (106);
	wp_y = getstati (107);
	wp_z = getstati (108);
	sp = cs_project (wp);
	if (sp_z <= 0)
	{
		sx = cx;
		sy = cy;
	}
	else
	{
		sx = bound (24, sp_x, w - 24);
		sy = bound (24, sp_y, h - 24);
	}

	if (mode == 4)
	{
		// Bird spotted in aim, but outside hairspray-counter range (>780u)!
		r = 26;
		arm = 7;
		col = '0.75 0.65 0.45';
		drawfill ([sx - r, sy - r, 0], [arm, 1.5, 0], col, 0.75, 0);
		drawfill ([sx - r, sy - r, 0], [1.5, arm, 0], col, 0.75, 0);
		drawfill ([sx + r - arm, sy - r, 0], [arm, 1.5, 0], col, 0.75, 0);
		drawfill ([sx + r - 1.5, sy - r, 0], [1.5, arm, 0], col, 0.75, 0);
		drawfill ([sx - r, sy + r - 1.5, 0], [arm, 1.5, 0], col, 0.75, 0);
		drawfill ([sx - r, sy + r - arm, 0], [1.5, arm, 0], col, 0.75, 0);
		drawfill ([sx + r - arm, sy + r - 1.5, 0], [arm, 1.5, 0], col, 0.75, 0);
		drawfill ([sx + r - 1.5, sy + r - arm, 0], [1.5, arm, 0], col, 0.75, 0);
		lbl = strcat ("^8BIRD TOO FAR (", ftos (dist), "u > 780u)");
		BM_Centered (sx, sy + r + 5, lbl, 5.2, '1 1 1', 0.85);
		return;
	}

	if (mode == 3)
	{
		// LOCKED ON! Pulsing neon-green/red targeting brackets + torpedo prompt!
		pulse = sin (time * 18);
		pulse = 0.5 + 0.5 * pulse;
		r = 20 + 3 * pulse;
		arm = 10;
		th = 2.4;
		col = (pulse > 0.5) ? '0.2 1 0.45' : '1 0.25 0.2';
		// 4 crisp bold corner brackets
		drawfill ([sx - r, sy - r, 0], [arm, th, 0], col, 0.96, 0);
		drawfill ([sx - r, sy - r, 0], [th, arm, 0], col, 0.96, 0);
		drawfill ([sx + r - arm, sy - r, 0], [arm, th, 0], col, 0.96, 0);
		drawfill ([sx + r - th, sy - r, 0], [th, arm, 0], col, 0.96, 0);
		drawfill ([sx - r, sy + r - th, 0], [arm, th, 0], col, 0.96, 0);
		drawfill ([sx - r, sy + r - arm, 0], [th, arm, 0], col, 0.96, 0);
		drawfill ([sx + r - arm, sy + r - th, 0], [arm, th, 0], col, 0.96, 0);
		drawfill ([sx + r - th, sy + r - arm, 0], [th, arm, 0], col, 0.96, 0);
		// Inner lock ticks
		drawfill ([sx - 6, sy - 0.8, 0], [12, 1.6, 0], col, 0.95, 0);
		drawfill ([sx - 0.8, sy - 6, 0], [1.6, 12, 0], col, 0.95, 0);
		lbl = strcat ("^2TORPEDO LOCKED! ^7[", ftos (dist), "u]");
		BM_Centered (sx, sy - r - 11, lbl, 5.8, '1 1 1', 0.96);
		BM_Centered (sx, sy + r + 5, "^3RELEASE TO LAUNCH KYLE!", 5.5, '1 1 1', 0.96);
	}
	else
	{
		// Mode 2: Actively Locking On (brackets smoothly close in as prog goes 0..100!)
		r = 46 - 24 * (prog / 100);
		arm = 9;
		th = 2.0;
		col = '1 0.82 0.18';
		drawfill ([sx - r, sy - r, 0], [arm, th, 0], col, 0.92, 0);
		drawfill ([sx - r, sy - r, 0], [th, arm, 0], col, 0.92, 0);
		drawfill ([sx + r - arm, sy - r, 0], [arm, th, 0], col, 0.92, 0);
		drawfill ([sx + r - th, sy - r, 0], [th, arm, 0], col, 0.92, 0);
		drawfill ([sx - r, sy + r - th, 0], [arm, th, 0], col, 0.92, 0);
		drawfill ([sx - r, sy + r - arm, 0], [th, arm, 0], col, 0.92, 0);
		drawfill ([sx + r - arm, sy + r - th, 0], [arm, th, 0], col, 0.92, 0);
		drawfill ([sx + r - th, sy + r - arm, 0], [th, arm, 0], col, 0.92, 0);
		// Lock progress bar right beneath the brackets
		bw = 56;
		bh = 4;
		drawfill ([sx - bw * 0.5 - 1, sy + r + 4, 0], [bw + 2, bh + 2, 0], '0 0 0', 0.72, 0);
		drawfill ([sx - bw * 0.5, sy + r + 5, 0], [bw * (prog / 100), bh, 0], col, 0.94, 0);
		lbl = strcat ("^3LOCKING BIRD ", ftos (prog), "% ^7[", ftos (dist), "u]");
		BM_Centered (sx, sy - r - 10, lbl, 5.4, '1 1 1', 0.94);
	}
};

void(float raw_w, float raw_h) GK_DrawHUD =
{
	local float w, h, hp, mode, prog, nitro, cx, cy, gap, arm, th, pulse, r, brk;
	local float tick_h, tick_f, base, mtop, bw, bh, x0, y0, fill_f;
	local vector col, shd;
	local string lbl;

	hp = getstati (STAT_HEALTH);
	if (hp <= 0)
		return;
	mode = getstati (109);
	if (mode <= 0)
		return;
	w = vid_conwidth;
	h = vid_conheight;
	if (w <= 0)
		w = raw_w;
	if (h <= 0)
		h = raw_h;
	if (w <= 0 || h <= 0)
		return;

	prog = bound (0, getstati (110), 100);
	nitro = bound (0, getstati (111), 100);
	cx = w * 0.5;
	cy = h * 0.5;
	pulse = sin (time * 16);		// sin is a __variant: assign to a float local first
	pulse = 0.5 + 0.5 * pulse;
	shd = '0 0 0';

	if (mode == 2)
	{
		col = '0.24 1 0.44';
		gap = 2.6;
		arm = 4.0;
		th = 1.0;
		r = 7.5 + 0.8 * pulse;
		brk = 2.8;
		drawfill ([cx - r, cy - r, 0], [brk, 1.0, 0], col, 0.90, 0);
		drawfill ([cx - r, cy - r, 0], [1.0, brk, 0], col, 0.90, 0);
		drawfill ([cx + r - brk, cy - r, 0], [brk, 1.0, 0], col, 0.90, 0);
		drawfill ([cx + r - 1.0, cy - r, 0], [1.0, brk, 0], col, 0.90, 0);
		drawfill ([cx - r, cy + r - 1.0, 0], [brk, 1.0, 0], col, 0.90, 0);
		drawfill ([cx - r, cy + r - brk, 0], [1.0, brk, 0], col, 0.90, 0);
		drawfill ([cx + r - brk, cy + r - 1.0, 0], [brk, 1.0, 0], col, 0.90, 0);
		drawfill ([cx + r - 1.0, cy + r - brk, 0], [1.0, brk, 0], col, 0.90, 0);
	}
	else if (mode == 1)
	{
		col = (prog >= 55) ? '1 0.84 0.20' : '0.35 0.88 1';
		gap = 5.2 - 2.4 * (prog / 100);
		arm = 3.8;
		th = 1.0;
		// Micro side charge ticks right beside the reticle (no center bar or text clutter)
		tick_h = 7.0;
		tick_f = tick_h * (prog / 100);
		drawfill ([cx - 10.0, cy - tick_h * 0.5, 0], [1.2, tick_h, 0], shd, 0.55, 0);
		drawfill ([cx + 8.8, cy - tick_h * 0.5, 0], [1.2, tick_h, 0], shd, 0.55, 0);
		if (tick_f > 0.2)
		{
			drawfill ([cx - 10.0, cy + tick_h * 0.5 - tick_f, 0], [1.2, tick_f, 0], col, 0.92, 0);
			drawfill ([cx + 8.8, cy + tick_h * 0.5 - tick_f, 0], [1.2, tick_f, 0], col, 0.92, 0);
		}
	}
	else
	{
		col = (pulse > 0.45) ? '1 0.24 0.20' : '0.72 0.16 0.14';
		gap = 4.4;
		arm = 3.5;
		th = 1.0;
	}

	// Ultra-compact open-center 4-arm reticle (~12px footprint, center view stays clear)
	drawfill ([cx - gap - arm - 0.5, cy - th * 0.5 - 0.5, 0], [arm + 1.0, th + 1.0, 0], shd, 0.68, 0);
	drawfill ([cx + gap - 0.5, cy - th * 0.5 - 0.5, 0], [arm + 1.0, th + 1.0, 0], shd, 0.68, 0);
	drawfill ([cx - th * 0.5 - 0.5, cy - gap - arm - 0.5, 0], [th + 1.0, arm + 1.0, 0], shd, 0.68, 0);
	drawfill ([cx - th * 0.5 - 0.5, cy + gap - 0.5, 0], [th + 1.0, arm + 1.0, 0], shd, 0.68, 0);

	drawfill ([cx - gap - arm, cy - th * 0.5, 0], [arm, th, 0], col, 0.95, 0);
	drawfill ([cx + gap, cy - th * 0.5, 0], [arm, th, 0], col, 0.95, 0);
	drawfill ([cx - th * 0.5, cy - gap - arm, 0], [th, arm, 0], col, 0.95, 0);
	drawfill ([cx - th * 0.5, cy + gap, 0], [th, arm, 0], col, 0.95, 0);

	// heat-seeker lock: small brackets on the target itself
	if (getstati (124))
	{
		local vector wp, sp;
		wp_x = getstati (125);
		wp_y = getstati (126);
		wp_z = getstati (127);
		sp = cs_project (wp);
		if (sp_z > 0 && sp_x > 8 && sp_x < w - 8 && sp_y > 8 && sp_y < h - 8)
		{
			local float sx, sy;
			sx = sp_x;
			sy = sp_y;
			col = (pulse > 0.5) ? '1 0.30 0.22' : '1 0.75 0.20';
			r = 9 + 1.5 * pulse;
			drawfill ([sx - r, sy - r, 0], [5, 1.2, 0], col, 0.95, 0);
			drawfill ([sx - r, sy - r, 0], [1.2, 5, 0], col, 0.95, 0);
			drawfill ([sx + r - 5, sy - r, 0], [5, 1.2, 0], col, 0.95, 0);
			drawfill ([sx + r - 1.2, sy - r, 0], [1.2, 5, 0], col, 0.95, 0);
			drawfill ([sx - r, sy + r - 1.2, 0], [5, 1.2, 0], col, 0.95, 0);
			drawfill ([sx - r, sy + r - 5, 0], [1.2, 5, 0], col, 0.95, 0);
			drawfill ([sx + r - 5, sy + r - 1.2, 0], [5, 1.2, 0], col, 0.95, 0);
			drawfill ([sx + r - 1.2, sy + r - 5, 0], [1.2, 5, 0], col, 0.95, 0);
			BM_Centered (sx, sy + r + 2, "LOCKED", 5.0, col, 0.95);
		}
	}

	// Compact bottom-right status badge (keeps center driving view unobstructed; minimap is bottom-left)
	base = BM_CornerBottomY (h);
	bw = 74;
	bh = 3;
	x0 = w - bw - 8;
	y0 = base - 8;
	drawfill ([x0 - 1, y0 - 1, 0], [bw + 2, bh + 2, 0], shd, 0.68, 0);
	fill_f = (mode == 3) ? (nitro / 100) : (prog / 100);
	drawfill ([x0, y0, 0], [bw * bound (0, fill_f, 1), bh, 0], col, 0.92, 0);
	if (mode == 3)
		drawfill ([x0 + bw * 0.40 - 0.5, y0 - 1, 0], [1, bh + 2, 0], '1 1 1', 0.85, 0);

	if (mode == 2)
		lbl = "^2ROCKET READY";
	else if (mode == 1)
		lbl = strcat ("^3ROCKET ", ftos (prog), "%");
	else if (mode == 3)
		lbl = strcat ("^1LOW NITRO ", ftos (nitro), "/40%");
	else
		lbl = "^1RELOAD";
	BM_ShadowColorRight (w - 8, y0 - 7, lbl, 5.0, 0.94);
};

float fl_csqc_mode_prev;
float fl_csqc_t0;
float fl_csqc_bob_phase;

void() FL_PrecachePics =
{
	precache_pic("gfx/foreloco/vm_01.png");
	precache_pic("gfx/foreloco/vm_02.png");
	precache_pic("gfx/foreloco/vm_03.png");
	precache_pic("gfx/foreloco/vm_04.png");
	precache_pic("gfx/foreloco/vm_05.png");
	precache_pic("gfx/foreloco/vm_06.png");
	precache_pic("gfx/foreloco/vm_07.png");
	precache_pic("gfx/foreloco/vm_08.png");
	precache_pic("gfx/foreloco/vm_09.png");
	precache_pic("gfx/foreloco/vm_10.png");
	precache_pic("gfx/foreloco/vm_11.png");
	precache_pic("gfx/foreloco/vm_12.png");
	precache_pic("gfx/foreloco/vm_13.png");
	precache_pic("gfx/foreloco/vm_14.png");
	precache_pic("gfx/foreloco/vm_15.png");
	precache_pic("gfx/foreloco/vm_16.png");
	precache_pic("gfx/foreloco/vm_17.png");
	precache_pic("gfx/foreloco/vm_18.png");
	precache_pic("gfx/foreloco/vm_19.png");
	precache_pic("gfx/foreloco/vm_20.png");
	precache_pic("gfx/foreloco/vm_21.png");
	precache_pic("gfx/foreloco/vm_22.png");
	precache_pic("gfx/foreloco/vm_23.png");
	precache_pic("gfx/foreloco/vm_24.png");
	precache_pic("gfx/foreloco/vm_25.png");
	precache_pic("gfx/foreloco/vm_26.png");
	precache_pic("gfx/foreloco/vm_27.png");
	precache_pic("gfx/foreloco/vm_28.png");
	precache_pic("gfx/foreloco/vm_29.png");
	precache_pic("gfx/foreloco/vm_30.png");
	precache_pic("gfx/foreloco/vm_31.png");
	precache_pic("gfx/foreloco/vm_32.png");
	precache_pic("gfx/foreloco/vm_33.png");
	precache_pic("gfx/foreloco/vm_34.png");
	precache_pic("gfx/foreloco/vm_35.png");
	precache_pic("gfx/foreloco/vm_36.png");
	precache_pic("gfx/foreloco/pour_stream.png");
	precache_pic("gfx/foreloco/smear_pink.png");
	precache_pic("gfx/foreloco/smear_green.png");
	precache_pic("gfx/foreloco/smear_drips.png");
};

string(float fr) FL_VMFramePic =
{
	if (fr <= 1)	return "gfx/foreloco/vm_01.png";
	if (fr == 2)	return "gfx/foreloco/vm_02.png";
	if (fr == 3)	return "gfx/foreloco/vm_03.png";
	if (fr == 4)	return "gfx/foreloco/vm_04.png";
	if (fr == 5)	return "gfx/foreloco/vm_05.png";
	if (fr == 6)	return "gfx/foreloco/vm_06.png";
	if (fr == 7)	return "gfx/foreloco/vm_07.png";
	if (fr == 8)	return "gfx/foreloco/vm_08.png";
	if (fr == 9)	return "gfx/foreloco/vm_09.png";
	if (fr == 10)	return "gfx/foreloco/vm_10.png";
	if (fr == 11)	return "gfx/foreloco/vm_11.png";
	if (fr == 12)	return "gfx/foreloco/vm_12.png";
	if (fr == 13)	return "gfx/foreloco/vm_13.png";
	if (fr == 14)	return "gfx/foreloco/vm_14.png";
	if (fr == 15)	return "gfx/foreloco/vm_15.png";
	if (fr == 16)	return "gfx/foreloco/vm_16.png";
	if (fr == 17)	return "gfx/foreloco/vm_17.png";
	if (fr == 18)	return "gfx/foreloco/vm_18.png";
	if (fr == 19)	return "gfx/foreloco/vm_19.png";
	if (fr == 20)	return "gfx/foreloco/vm_20.png";
	if (fr == 21)	return "gfx/foreloco/vm_21.png";
	if (fr == 22)	return "gfx/foreloco/vm_22.png";
	if (fr == 23)	return "gfx/foreloco/vm_23.png";
	if (fr == 24)	return "gfx/foreloco/vm_24.png";
	if (fr == 25)	return "gfx/foreloco/vm_25.png";
	if (fr == 26)	return "gfx/foreloco/vm_26.png";
	if (fr == 27)	return "gfx/foreloco/vm_27.png";
	if (fr == 28)	return "gfx/foreloco/vm_28.png";
	if (fr == 29)	return "gfx/foreloco/vm_29.png";
	if (fr == 30)	return "gfx/foreloco/vm_30.png";
	if (fr == 31)	return "gfx/foreloco/vm_31.png";
	if (fr == 32)	return "gfx/foreloco/vm_32.png";
	if (fr == 33)	return "gfx/foreloco/vm_33.png";
	if (fr == 34)	return "gfx/foreloco/vm_34.png";
	if (fr == 35)	return "gfx/foreloco/vm_35.png";
	return "gfx/foreloco/vm_36.png";
};

void(float w, float h, float el) FL_DrawLiquidSmear =
{
	local float pour_a, smear_p, smear_fade, cascade, sx, sy, px, py, dy, sn, sn2, sn_g, gx, stream_a, gulp_mod, pour_env, mist_s;

	if (el < 0.72)
		return;

	// 1. Tab-pop pressurized CO2 spray mist strictly 0.72..1.05s
	if (el < 1.05)
	{
		mist_s = sin (((el - 0.72) / 0.33) * 3.14159);
		pour_a = max (0, mist_s) * 0.24;
		if (pour_a > 0.005)
		{
			sn = sin (time * 5.5);
			px = sn * 6;
			drawpic ((px - 8) * '1 0 0', "gfx/foreloco/smear_pink.png", (w + 16) * '1 0 0' + h * '0 1 0', '1 1 1', pour_a * 0.45, 0);
			drawpic ((0 - px - 8) * '1 0 0', "gfx/foreloco/smear_green.png", (w + 16) * '1 0 0' + h * '0 1 0', '1 1 1', pour_a * 0.40, 0);
		}
		return;
	}

	// 2. Cascading pour ribbons strictly during active chug (1.24..2.22s), never during upright crush
	pour_env = bound (0, (el - 1.24) / 0.14, 1) * (1 - bound (0, (el - 2.08) / 0.14, 1));
	if (pour_env > 0.005)
	{
		cascade = (el * 1.72) - floor (el * 1.72);
		py = cascade * h;
		sn = sin (time * 8.5);
		sx = sn * 14;
		sn_g = sin ((el - 1.24) * 19.2);
		gulp_mod = 0.85 + 0.22 * sn_g;
		stream_a = 0.42 * pour_env * gulp_mod;
		if (stream_a > 0.01)
		{
			drawpic (sx * '1 0 0' + (py - h) * '0 1 0', "gfx/foreloco/pour_stream.png", w * '1 0 0' + h * '0 1 0', '1 1 1', stream_a, 0);
			drawpic (sx * '1 0 0' + py * '0 1 0', "gfx/foreloco/pour_stream.png", w * '1 0 0' + h * '0 1 0', '1 1 1', stream_a, 0);
		}
	}

	// 3. Edge-framed watermelon-pink & sour-green smears + drips: build during chug, decay cleanly for crush/yeet
	smear_p = bound (0, (el - 1.18) / 0.78, 1);
	smear_fade = 1 - bound (0, (el - 2.22) / 0.55, 1) * 0.58;
	pour_a = (0.18 + smear_p * 0.72) * smear_fade;
	if (smear_p > 0.01 && pour_a > 0.01)
	{
		sn = sin (time * 4.2);
		sn2 = sin (time * 3.6);
		px = sn * 12 * smear_p;
		gx = (0 - sn2) * 14 * smear_p;
		sy = smear_p * (h * 0.08);
		drawpic ((px - 16) * '1 0 0' + (sy - h * 0.08) * '0 1 0', "gfx/foreloco/smear_pink.png", (w + 32) * '1 0 0' + (h * 1.08) * '0 1 0', '1 1 1', pour_a * 0.62, 0);
		drawpic ((gx - 16) * '1 0 0' + (sy * 1.2 - h * 0.10) * '0 1 0', "gfx/foreloco/smear_green.png", (w + 32) * '1 0 0' + (h * 1.10) * '0 1 0', '1 1 1', pour_a * 0.56, 0);
		dy = (0 - h * 0.32) * (1 - smear_p);
		drawpic ((px * 0.4 - 8) * '1 0 0' + dy * '0 1 0', "gfx/foreloco/smear_drips.png", (w + 16) * '1 0 0' + h * '0 1 0', '1 1 1', pour_a * 0.76, 0);
	}
};

void(float w, float h) FL_DrawViewmodel =
{
	local float mode, fr, srv_fr, el, srv_el, drift, frac, ph, pw, px, py, bx, by, amp, sn, cs2, dt, sn_g, sn_cr, gulp_y, chug_env, cr_env, vm_a;
	local string vpic;

	mode = getstati (115);
	if (mode != fl_csqc_mode_prev)
	{
		fl_csqc_mode_prev = mode;
		fl_csqc_t0 = time;
		fl_csqc_bob_phase = 0;
	}
	if (mode != 1)
		return;
	if (inMenu || intermission || finale)
		return;
	if (getstati (STAT_HEALTH) <= 0)
		return;

	el = max (0, time - fl_csqc_t0);
	srv_fr = getstati (119);
	if (srv_fr >= 1 && srv_fr <= 36)
	{
		srv_el = (srv_fr - 0.5) * (2.85 / 36);
		drift = srv_el - el;
		if (drift > 0.22 || drift < -0.22)
		{
			fl_csqc_t0 = fl_csqc_t0 - drift * 0.25;
			el = max (0, time - fl_csqc_t0);
		}
	}

	FL_DrawLiquidSmear (w, h, el);

	if (cvar ("r_drawviewmodel") <= 0 || cvar ("chase_active") > 0)
		return;

	frac = bound (0, el / 2.85, 0.9995);
	fr = bound (1, 1 + floor (frac * 36), 36);
	vpic = FL_VMFramePic (fr);

	// Downward-only figure-8 bob + smooth chug gulp / crush tremor envelopes (wrist stays anchored bottom-right)
	dt = frametime;
	if (dt < 0 || dt > 0.1)
		dt = 0.016;
	fl_csqc_bob_phase = fl_csqc_bob_phase + dt * 7.2;

	sn = sin (fl_csqc_bob_phase);
	cs2 = cos (fl_csqc_bob_phase * 2);
	chug_env = bound (0, (el - 1.18) / 0.14, 1) * (1 - bound (0, (el - 2.16) / 0.12, 1));
	cr_env = bound (0, (el - 2.22) / 0.08, 1) * (1 - bound (0, (el - 2.50) / 0.10, 1));

	amp = 3.0 + 1.6 * chug_env - 0.8 * cr_env;
	sn_g = sin ((el - 1.24) * 19.2);
	sn_cr = sin (time * 44.0);
	gulp_y = ((0.5 + 0.5 * sn_g) * 3.2) * chug_env + ((0.5 + 0.5 * sn_cr) * 2.0) * cr_env;

	bx = sn * amp;
	by = amp * 0.45 * (1 - cs2) + gulp_y;

	ph = h * 0.98;
	pw = ph * 1.333333;
	px = w - pw + 8 + bx;
	py = (h - ph) + by + 5;
	vm_a = 1 - bound (0, (el - 2.68) / 0.17, 1);
	if (vm_a > 0.005)
		drawpic (px * '1 0 0' + py * '0 1 0', vpic, pw * '1 0 0' + ph * '0 1 0', '1 1 1', vm_a, 0);
};

void(float w, float h) FL_DrawHUD =
{
	local float blk, mode, rem, spd, fl_flags, invuln, orbit, boosted, hits;
	local float y0, sec, dec, mph, el;
	local string ts, s1, s2, tags, lbl;

	FL_DrawViewmodel (w, h);

	mode = getstati (115);
	blk = getstati (114);
	rem = getstati (116);
	spd = getstati (117);
	fl_flags = getstati (118);

	y0 = 36;
	if (cvar ("bm_hud_style") == 2)
		y0 = 64;

	if (mode == 2)
		FL_DrawLiquidSmear (w, h, 2.80);

	if (mode == 3)
	{
		invuln = fl_flags & 1;
		orbit = fl_flags & 2;
		boosted = fl_flags & 4;
		hits = floor (fl_flags / 16);

		sec = floor (rem / 10);
		dec = rem - sec * 10;
		ts = strcat (ftos (sec), ".", ftos (dec), "s");
		mph = floor (spd * 0.085 + 0.5);

		tags = "";
		if (orbit)
			tags = strcat (tags, "  ^3[360 REVEAL]");
		if (invuln)
		{
			if ((floor (time * 8) & 1) == 0)
				tags = strcat (tags, "  ^3[INVULNERABLE!]");
			else
				tags = strcat (tags, "  ^2[INVULNERABLE!]");
		}
		if (hits > 0)
			tags = strcat (tags, "  ^1RAM KOs: ", ftos (hits));

		s1 = strcat ("^2FORELOCO: ^3ERIC HOSPITAL BED  ^7", ts, tags);
		s2 = strcat ("^3SPEED: ^7", ftos (mph), " MPH", boosted ? " ^2[TURBO!]" : "", "  ^3[SHIFT]^7 TURBO  ^3[SPACE]^7 JUMP  ^3[M1]^7 BEDPANS/HORN  ^3[H]^7 BAIL");
		local float fl_sc2, fl_w2;
		fl_sc2 = 6.0;
		fl_w2 = BM_UIStringWidth (s2, TRUE, [fl_sc2, fl_sc2, 0]);
		if (fl_w2 > w - 20 && fl_w2 > 0)
			fl_sc2 = max (3.8, fl_sc2 * ((w - 20) / fl_w2));
		BM_DrawColorShadow (10, y0, s1, 6.4, 0.98);
		BM_DrawColorShadow (10, y0 + 12, s2, fl_sc2, 0.96);
	}
	else if (mode == 1)
	{
		el = max (0, time - fl_csqc_t0);
		if (el < 0.68)
			lbl = "^3WATERMELON FORELOCO  ^712% ALC/VOL";
		else if (el < 1.12)
			lbl = "^3WATERMELON FORELOCO  ^2CRACKING TAB!";
		else if (el < 2.22)
			lbl = "^3WATERMELON FORELOCO  ^2CHUGGING!!";
		else
			lbl = "^3WATERMELON FORELOCO  ^1CRUSH & YEET!";
		BM_DrawColorShadow (10, y0, lbl, 6.2, 0.96);
	}

	if (blk > 0)
	{
		drawfill ('0 0 0', w * '1 0 0' + h * '0 1 0', '0 0 0', bound (0, blk / 100, 1), 0);
		if (mode == 2)
			BM_DrawColorShadow (10, y0, "^3VEGAS BABY!!", 7.2, 0.98);
	}
};

string(float code) TW_HudWepName =
{
	if (code == 1) return "ROCKET LAUNCHER";
	if (code == 2) return "GRENADE LNCHR";
	if (code == 3) return "DN3D SHOTGUN";
	if (code == 4) return "LASER CANNON";
	if (code == 5) return "THUNDERBOLT";
	if (code == 6) return "MEGA MAN";
	if (code == 7) return "MILKY GUN";
	if (code == 8) return "M4A1 CARBINE";
	if (code == 9) return "M1 GARAND";
	if (code == 10) return "WHEELMAN";
	if (code == 11) return "DOOKIE BAZOOKA";
	if (code == 12) return "PICKLE SURPRISE";
	if (code == 13) return "GREEN JAR";
	if (code == 14) return "NETSEND";
	if (code == 15) return "POCKET KYLE";
	if (code == 16) return "CYRAX NET";
	if (code == 17) return "BONK AXE";
	if (code == 18) return "ROB HEAD";
	if (code == 19) return "BANANA";
	return "CHAOS GUN";
};

void(float x, float y, float cw, float ch, string tag, float wcode, float fired, float queued) TW_DrawSlotCell =
{
	local string s;
	local vector bg;

	if (fired)
	{
		bg = '1.0 0.45 0.05';
		drawfill (x * '1 0 0' + y * '0 1 0', cw * '1 0 0' + ch * '0 1 0', bg, 0.55, 0);
		s = strcat ("^3", tag, " ^7", TW_HudWepName (wcode));
	}
	else if (queued)
	{
		drawfill (x * '1 0 0' + y * '0 1 0', cw * '1 0 0' + ch * '0 1 0', '0.18 0.32 0.12', 0.48, 0);
		s = strcat ("^2", tag, " ^7", TW_HudWepName (wcode));
	}
	else
	{
		drawfill (x * '1 0 0' + y * '0 1 0', cw * '1 0 0' + ch * '0 1 0', '0.06 0.06 0.09', 0.45, 0);
		s = strcat ("^5", tag, " ^7", TW_HudWepName (wcode));
	}
	BM_DrawColorShadow (x + 3, y + 2.5, s, 4.4, 0.96);
};

void(float w, float h) TW_DrawHUD =
{
	local float rem, w0, w1, w2, w3, st, next_s, sec, dec;
	local float pw, ph, x0, y0, colw, rowh, warn_red;
	local string hdr, ts;
	local vector bcol;

	rem = getstati (152);
	if (rem <= 0)
		return;

	w0 = getstati (153);
	w1 = getstati (154);
	w2 = getstati (155);
	w3 = getstati (156);
	st = getstati (157);
	next_s = floor (st / 16);

	sec = floor (rem / 10);
	dec = rem - sec * 10;
	ts = strcat (ftos (sec), ".", ftos (dec), "s");

	pw = 252;
	ph = 44;
	x0 = w * 0.5 - pw * 0.5;
	y0 = 8;
	colw = 118;
	rowh = 11;

	warn_red = (rem < 30 && (floor (time * 8) & 1) == 0);
	bcol = warn_red ? '1.0 0.2 0.1' : '1.0 0.68 0.1';

	// Backing panel + glowing border
	drawfill (x0 * '1 0 0' + y0 * '0 1 0', pw * '1 0 0' + ph * '0 1 0', '0.04 0.04 0.06', 0.68, 0);
	drawfill (x0 * '1 0 0' + y0 * '0 1 0', pw * '1 0 0' + '0 1 0', bcol, 0.85, 0);
	drawfill (x0 * '1 0 0' + (y0 + ph - 1) * '0 1 0', pw * '1 0 0' + '0 1 0', bcol, 0.85, 0);

	if (warn_red)
		hdr = strcat ("^1B. TRIPLE WHEELED  ^3[", ts, "] ^1(4 GUNS!)");
	else
		hdr = strcat ("^3B. TRIPLE WHEELED  ^7[", ts, "] ^2(4 GUNS!)");
	BM_Centered (w * 0.5, y0 + 3, hdr, 5.4, '1 1 1', 0.98);

	// Top row (upside-down ceiling guns): Slot 3 Top-Left, Slot 2 Top-Right
	TW_DrawSlotCell (x0 + 6, y0 + 15, colw, rowh, "[TL INV]", w3, (st & 8), (next_s == 3));
	TW_DrawSlotCell (x0 + 6 + colw + 4, y0 + 15, colw, rowh, "[TR INV]", w2, (st & 4), (next_s == 2));

	// Bottom row (upright guns): Slot 1 Bottom-Left, Slot 0 Main Bottom-Right
	TW_DrawSlotCell (x0 + 6, y0 + 28, colw, rowh, "[BL]", w1, (st & 2), (next_s == 1));
	TW_DrawSlotCell (x0 + 6 + colw + 4, y0 + 28, colw, rowh, "[MAIN]", w0, (st & 1), 0);
};

void(float w, float h) BM_DrawHUD =
{
	local float cx, cy, mag, magmax, rlp, prot, heat, boost, regen, warm, lheat, hp, i, px, pw, a, f, sl, low, botcnt, intro_on, ty, row_step, rlp_step;
	local string leader, s, hpic, hkey;
	local vector col;

	w = cvar ("vid_conwidth");		// 2D drawing is in virtual console units, not window pixels
	h = cvar ("vid_conheight");
	cx = w * 0.5;
	cy = h * 0.5;
	row_step = (BM_GetUIFont () > 0) ? 10.5 : 9;
	rlp_step = (BM_GetUIFont () > 0) ? 13.5 : 12;
	mag = getstati (BMST_MAG);
	magmax = getstati (BMST_MAGMAX);
	rlp = getstati (BMST_RELOAD);
	prot = getstati (BMST_PROT);
	heat = getstati (BMST_HEAT);
	boost = getstati (BMST_BOOST);
	regen = getstati (BMST_REGEN);
	warm = getstati (BMST_WARMUP);
	lheat = getstati (BMST_LHEAT);
	leader = getstats (BMST_LEADER);
	hp = getstati (STAT_HEALTH);

	bm_topright_y = 8;
	JP_DrawHUD (w, h, hp);		// the jetpack's fuel tank
	intro_on = getstati (BMST_INTRO);
	if (intro_on <= 0 && !intermission)
	{
		BM_DrawBotTags (w, h);
		BM_DrawPlayerTags (w, h);
		botcnt = getstati (BMST_BOTCNT);
		ty = 8;
		if (deathmatch && (botcnt > 0 || time < 20))
		{
			if (botcnt > 0)
				s = strcat ("^xfa3BOTS: ^7", ftos (botcnt), "  ^8(^3F1^8 +  ^3F2^8 -)");
			else
				s = "^8Press ^3F1^8 +Bot  ^3F2^8 -Bot";
			BM_ShadowColorRight (w - 8, 8, s, 5, 0.88);
			ty = 8 + row_step;
		}
		bm_topright_y = ty;
		if (deathmatch)
			BM_DrawToyDock (w, h, hp, ty);
	}
	BM_DrawCenterPrint (w, h);

	// low health: red edges, pulsing, fading out as you heal
	if (hp > 0 && hp < 40)
	{
		f = sin (time * 6);
		a = (1 - hp / 40) * (0.5 + 0.12 * f);
		drawfill ('0 0 0', w * '1 0 0' + (h * 0.12) * '0 1 0', '0.8 0 0', a, 0);
		drawfill ((h * 0.88) * '0 1 0', w * '1 0 0' + (h * 0.12) * '0 1 0', '0.8 0 0', a, 0);
		drawfill ('0 0 0', (w * 0.08) * '1 0 0' + h * '0 1 0', '0.8 0 0', a, 0);
		drawfill ((w * 0.92) * '1 0 0', (w * 0.08) * '1 0 0' + h * '0 1 0', '0.8 0 0', a, 0);
	}


	// CS 1.6 M4A1 weapon tile flush left of [2] on the status bar weapon strip (unobstructed by forearm or prox bar)
	sl = getstati (BMST_SLOT);	if ((sl == 16 || sl == 18) && hp > 0 && getstati (93) <= 0)
	{
		px = cx - 220;
		pw = 58;
		hpic = "gfx/hud_m4";	hkey = "^xfb3C";	low = 6;	if (sl == 18) { hpic = "gfx/hud_garand"; hkey = "^xfb3M"; low = 2; }	col = '1 0.72 0.18';
		if (mag <= low || rlp > 0)
			col = '1 0.28 0.18';
		drawfill (px * '1 0 0' + (h - 42) * '0 1 0', pw * '1 0 0' + '0 18 0', '0.07 0.05 0.03', 0.76, 0);
		drawfill (px * '1 0 0' + (h - 42) * '0 1 0', pw * '1 0 0' + '0 1 0', col, 0.90, 0);
		drawfill (px * '1 0 0' + (h - 25) * '0 1 0', pw * '1 0 0' + '0 1 0', col, 0.55, 0);
		drawfill (px * '1 0 0' + (h - 42) * '0 1 0', '1 0 0' + '0 18 0', col, 0.88, 0);
		drawfill ((px + pw - 1) * '1 0 0' + (h - 42) * '0 1 0', '1 0 0' + '0 18 0', col, 0.55, 0);
		drawpic ((px + 9) * '1 0 0' + (h - 41) * '0 1 0', hpic, '47 16 0', col, 0.98, 0);
		BM_DrawColorShadow (px + 2, h - 32, hkey, 6, 0.95);
		BM_Centered (px + pw * 0.5, h - 51, strcat ("^xfc5", ftos (mag)), 7, '1 1 1', 0.92);
	}

	// reloading: drop-shadowed label on the top-right stack with a thin bright fill line under it (no dark bar), only while a gun reloads
	if (rlp > 0 && hp > 0)
	{
		f = sin (time * 9);
		BM_ShadowColorRight (w - 8, bm_topright_y, "^xfe4RELOADING", 5, 0.80 + 0.15 * f);
		pw = 42;
		drawfill ((w - 8 - pw) * '1 0 0' + (bm_topright_y + row_step - 1) * '0 1 0', pw * '1 0 0' + '0 1 0', '1 0.85 0.3', 0.22, 0);
		drawfill ((w - 8 - pw) * '1 0 0' + (bm_topright_y + row_step - 1) * '0 1 0', (pw * rlp / 100) * '1 0 0' + '0 1 0', '1 0.85 0.3', 0.95, 0);
		bm_topright_y = bm_topright_y + rlp_step;
	}

	// Top-right corner text stack for match/status overlays (never slapped across center screen)
	if (warm)
	{
		f = sin (time * 3);
		a = 0.78 + 0.18 * f;
		if (time > 15)
			a = 0.65;
		BM_ShadowColorRight (w - 8, bm_topright_y, "^xfd0WARMUP^7 - ^3F1^7 +Bot  ^3F2^7 -Bot  ^3F3^7 LAN", 5, a);
		bm_topright_y = bm_topright_y + row_step;
	}

	if (leader != "" && lheat >= 4)
	{
		if (heat >= 4 && heat == lheat)
			s = strcat ("^3In the lead (+", ftos (lheat), ")");
		else
			s = strcat ("^3Leader: ", leader, "^3 (+", ftos (lheat), ")");
		BM_ShadowColorRight (w - 8, bm_topright_y, s, 5, 0.88);
		bm_topright_y = bm_topright_y + row_step;
	}

	// a marker on the leader, wherever they are (only once they show through walls)
	if (getstati (BMST_LSHOW) && leader != "")
	{
		local vector lp, sp;

		lp_x = getstati (BMST_LX);
		lp_y = getstati (BMST_LY);
		lp_z = getstati (BMST_LZ);
		lp_z = lp_z + 44;
		sp = cs_project (lp);
		if (sp_z > 0 && sp_x > 0 && sp_x < w && sp_y > 0 && sp_y < h)
		{
			f = sin (time * 8);
			BM_Centered (sp_x, sp_y - 10, strcat ("^3", leader), 5, '1 1 1', 0.82);
			BM_Centered (sp_x, sp_y - 3, "^3v", 6, '1 1 1', 0.70 + 0.25 * f);
		}
	}

	if (boost >= 15 && hp > 0)
	{
		BM_ShadowColorRight (w - 8, bm_topright_y, strcat ("^2boost +", ftos (boost), "%"), 5, 0.86);
		bm_topright_y = bm_topright_y + row_step;
	}

	if (prot > 0 && hp > 0)
	{
		BM_ShadowColorRight (w - 8, bm_topright_y, strcat ("^5SHIELD ", ftos (ceil (prot / 10))), 5, 0.88);
		bm_topright_y = bm_topright_y + row_step;
	}

	if (regen && hp > 0)
	{
		f = sin (time * 5);
		BM_ShadowColorRight (w - 8, bm_topright_y, "^2+ regen", 5, 0.65 + 0.25 * f);
		bm_topright_y = bm_topright_y + row_step;
	}
	BM_DrawBakoDestructHUD (w);
};

// Top-right corner text-only status & milestone toasts for Bakersfield-ish destructibles
// (pure ASCII, zero boxes, stacks cleanly on bm_topright_y completely clear of center & minimap)
void(float w) BM_DrawBakoDestructHUD =
{
	local float pct, ev, pw, row_step, cw;
	local string col, s, msg;
	local vector bar_col;

	cw = cvar ("vid_conwidth");
	if (cw > 0)
		w = cw;
	pct = getstati (BMST_BAKO_PADRE);
	ev = getstati (BMST_BAKO_EVENT);
	row_step = (BM_GetUIFont () > 0) ? 11 : 9;

	if (pct >= 1 && pct <= 99)
	{
		if (pct <= 25)
		{
			col = "^1";
			bar_col = '1 0.25 0.18';
		}
		else if (pct <= 50)
		{
			col = "^xf82";
			bar_col = '1 0.56 0.15';
		}
		else
		{
			col = "^3";
			bar_col = '1 0.85 0.30';
		}
		s = strcat (col, "PADRE HOTEL ^7", ftos (pct), "%");
		BM_ShadowColorRight (w - 8, bm_topright_y, s, 5, 0.92);
		pw = 54;
		drawfill ((w - 8 - pw) * '1 0 0' + (bm_topright_y + row_step - 1) * '0 1 0', pw * '1 0 0' + '0 1 0', bar_col, 0.24, 0);
		drawfill ((w - 8 - pw) * '1 0 0' + (bm_topright_y + row_step - 1) * '0 1 0', (pw * pct / 100) * '1 0 0' + '0 1 0', bar_col, 0.94, 0);
		bm_topright_y = bm_topright_y + row_step + 3;
	}

	msg = "";
	if (ev == 1)
		msg = "^3FOX CLOCK HIT - TOWER COLLAPSING!";
	else if (ev == 2)
		msg = "^1PADRE HOTEL GOING DOWN!";
	else if (ev == 3)
		msg = "^3BAKERSFIELD SIGN TOPPLING!";
	else if (ev == 4)
		msg = "^3FOX COLLAPSED - CLIMB THE RUBBLE!";
	else if (ev == 5)
		msg = "^1PADRE FALLEN - WATCH FOR BOULDERS!";
	else if (ev == 6)
		msg = "^3SIGN DOWN ON H ST - RAMP OVER IT!";
	else if (ev == 7)
		msg = "^2FOX THEATER RESTORED!";
	else if (ev == 8)
		msg = "^2PADRE HOTEL RESTORED!";
	else if (ev == 9)
		msg = "^2BAKERSFIELD SIGN RESTORED!";
	else if (ev == 11)
		msg = "^3PADRE FACADE CRACKING (75%)";
	else if (ev == 12)
		msg = "^xf82PADRE STRUCTURE WEAKENING (50%)";
	else if (ev == 13)
		msg = "^1PADRE CRITICAL - ABOUT TO FALL!";
	else if (ev >= 100 && ev <= 200)
		msg = strcat ("^2FOX REBUILDING ^7", ftos (ev - 100), "%");

	if (msg != "")
	{
		BM_ShadowColorRight (w - 8, bm_topright_y, msg, 5, 0.92);
		bm_topright_y = bm_topright_y + row_step;
	}
};


// ---------------------------------------------------------------- intro.dem showcase camera, viewmodels & HUD (stats 69..70)

float	BMST_INTRO_T0		= 70;
.float	renderflags;
entity	intro_vm;
string	intro_vm_mdl;
float	intro_prev_card;
float	intro_card_t;
float	intro_cur_t;

void() BM_IntroPrecache =
{
	registercvar ("bm_bot_tags", "1");
	registercvar ("bm_player_tags", "1");
	registercvar ("bm_hud_toys", "1");
	registercvar ("bm_menu_bg", "0");
	bm_tag_font = findfont ("Roboto");
	if (bm_tag_font < 0)
		bm_tag_font = 0;
	precache_model ("progs/v_pickle.md3");
	precache_model ("progs/v_wewcannon.md3");
	precache_model ("progs/v_milky.md3");
	precache_model ("progs/v_hammer.mdl");
	precache_model ("progs/v_netsend.md3");
	precache_model ("progs/ltg_v3d.md3");
	precache_model ("progs/v_mm_cannon.md3");
	precache_model ("progs/v_mm_slingshot.md3");
	precache_model ("progs/v_m4.md3");
};

float(float u) BM_IntroSmooth =
{
	if (u <= 0)
		return 0;
	if (u >= 1)
		return 1;
	return u * u * (3 - 2 * u);
};

float(float t, float t_in, float t_out) BM_IntroWindow =
{
	local float a, b;
	a = BM_IntroSmooth ((t - t_in) / 0.26);
	b = 1 - BM_IntroSmooth ((t - (t_out - 0.30)) / 0.30);
	if (b < a)
		return b;
	return a;
};

vector(vector a, vector b, float u) BM_IntroLerp =
{
	local float s;
	s = BM_IntroSmooth (u);
	return a + (b - a) * s;
};

float(float x) BM_Sin =
{
	local float r;
	r = sin (x);
	return r;
};

float(float x) BM_Cos =
{
	local float r;
	r = cos (x);
	return r;
};

vector(vector from, vector to) BM_IntroLook =
{
	local vector a;
	local float px;

	a = vectoangles (to - from);
	px = a_x;
	if (px > 180)
		px = px - 360;
	a_x = 0 - px;
	a_z = 0;
	return a;
};

// Third-person action-comedy movie mode: weapons are wielded in 3rd-person by the 3 Deathmatch fighters
void(float card, float t) BM_UpdateIntroVM =
{
	if (card < 0 && t < 0)
		return;
};

// Native refresh-rate (150+ Hz) zero-shake movie camera across downtown locked to SSQC (stats 69..70)
vector(float s) BM_LsjVanRaw =
{
	local float a;

	if (s < 0) s = 0;
	if (s > 1) s = 1;
	if (s <= 0.04110) {
		a = s / 0.04110;
		return BM_IntroLerp ('-12681.1 -7559.1 608.3', '-11889.8 -7244.1 608.3', a);
	} else if (s <= 0.28612) {
		a = (s - 0.04110) / 0.24502;
		return BM_IntroLerp ('-11889.8 -7244.1 608.3', '-7677.2 -4409.4 771.7', a);
	} else if (s <= 0.49639) {
		a = (s - 0.28612) / 0.21027;
		return BM_IntroLerp ('-7677.2 -4409.4 771.7', '-4015.7 -2047.2 886.6', a);
	} else if (s <= 0.58760) {
		a = (s - 0.49639) / 0.09121;
		return BM_IntroLerp ('-4015.7 -2047.2 886.6', '-2126.0 -2007.9 898.4', a);
	} else if (s <= 0.60780) {
		a = (s - 0.58760) / 0.02020;
		return BM_IntroLerp ('-2126.0 -2007.9 898.4', '-1909.4 -1649.6 898.4', a);
	} else if (s <= 0.62569) {
		a = (s - 0.60780) / 0.01789;
		return BM_IntroLerp ('-1909.4 -1649.6 898.4', '-1929.1 -1279.5 898.4', a);
	} else if (s <= 0.74449) {
		a = (s - 0.62569) / 0.11880;
		return BM_IntroLerp ('-1929.1 -1279.5 898.4', '-2007.9 1181.1 885.8', a);
	} else if (s <= 0.76615) {
		a = (s - 0.74449) / 0.02166;
		return BM_IntroLerp ('-2007.9 1181.1 885.8', '-1653.5 1456.7 885.8', a);
	} else if (s <= 0.78707) {
		a = (s - 0.76615) / 0.02092;
		return BM_IntroLerp ('-1653.5 1456.7 885.8', '-1633.9 1889.8 885.8', a);
	} else if (s <= 0.94650) {
		a = (s - 0.78707) / 0.15943;
		return BM_IntroLerp ('-1633.9 1889.8 885.8', '1574.8 2677.2 570.9', a);
	} else {
		a = (s - 0.94650) / 0.05350;
		return BM_IntroLerp ('1574.8 2677.2 570.9', '2677.2 2795.3 574.0', a);
	}
};

vector(float s) BM_LsjVanPos =
{
	return BM_LsjVanRaw (s - 0.015) * 0.25 + BM_LsjVanRaw (s) * 0.50 + BM_LsjVanRaw (s + 0.015) * 0.25;
};

vector(float s) BM_LsjVanFwd =
{
	local vector d;

	d = BM_LsjVanRaw (s + 0.015) - BM_LsjVanRaw (s - 0.015);
	d_z = 0;
	if (vlen (d) < 0.001)
		return '1 0 0';
	return normalize (d);
};

// Slow, silent scenic camera flyover for the Main Menu background (bm_menu_bg 1, stat 69 == 900)
void() BM_UpdateMenuBgCam =
{
	local float u, rad, custom_ang;
	local vector cpos, look, cang;

	custom_ang = FALSE;
	if (mapname == "soi6" || world.model == "maps/soi6.bsp")
	{
		u = 0.5 - 0.5 * BM_Cos (time * 0.08);
		cpos = BM_IntroLerp ('300 -16 155', '9200 16 175', u);
		cpos_z = cpos_z + 16 * BM_Sin (time * 0.21);
		look = cpos + '1400 0 -42';
		look_y = look_y + 180 * BM_Sin (time * 0.14);
	}
	else if (mapname == "soicowboy_bkk" || world.model == "maps/soicowboy_bkk.bsp")
	{
		u = 0.5 - 0.5 * BM_Cos (time * 0.085);
		cpos = BM_IntroLerp ('3250 -1417 165', '9100 -1417 175', u);
		cpos_y = cpos_y + 20 * BM_Sin (time * 0.19);
		cpos_z = cpos_z + 14 * BM_Cos (time * 0.17);
		look = cpos + '1200 0 -48';
		look_y = -1417 + 180 * BM_Sin (time * 0.13);
	}
	else if (mapname == "bakersfielddowntown" || world.model == "maps/bakersfielddowntown.bsp"
		|| mapname == "bakersfieldish" || world.model == "maps/bakersfieldish.bsp")
	{
		u = 0.5 - 0.5 * BM_Cos (time * 0.10);
		cpos = BM_IntroLerp ('-8380 1780 210', '-8490 2440 340', u);
		cpos_z = cpos_z + 18 * BM_Sin (time * 0.19);
		look = '-9260 2440 235';
	}
	else if (mapname == "little_st_james" || world.model == "maps/little_st_james.bsp")
	{
		rad = time * 0.065;
		cpos_x = -3740 + BM_Cos (rad) * 9000;
		cpos_y = 1378 + BM_Sin (rad) * 8400;
		cpos_z = 1950 + 160 * BM_Sin (rad);
		look = '-3740 1378 560';
	}
	else if (mapname == "terminal21" || world.model == "maps/terminal21.bsp")
	{
		u = 0.5 - 0.5 * BM_Cos (time * 0.08);
		cpos = BM_IntroLerp ('2200 -4100 380', '-2150 -1600 320', u);
		cpos_z = cpos_z + 32 * BM_Sin (time * 0.18);
		look = '0 -750 460';
	}
	else if (mapname == "goldenwest" || world.model == "maps/goldenwest.bsp")
	{
		u = 0.5 - 0.5 * BM_Cos (time * 0.085);
		cpos = BM_IntroLerp ('2650 -1600 340', '2750 1100 420', u);
		cpos_z = cpos_z + 24 * BM_Sin (time * 0.17);
		look = '650 -120 140';
	}
	else if (mapname == "lolmap1" || world.model == "maps/lolmap1.bsp")
	{
		u = 0.5 - 0.5 * BM_Cos (time * 0.085);
		cpos = BM_IntroLerp ('-1300 -1450 360', '1300 -1350 420', u);
		look = '0 0 260';
	}
	else if (mapname == "fox" || world.model == "maps/fox.bsp")
	{
		u = 0.5 - 0.5 * BM_Cos (time * 0.09);
		cpos = BM_IntroLerp ('-2600 -6250 320', '-2600 -5300 460', u);
		look = '-3800 -5800 220';
	}
	else if (mapname == "morrorock" || world.model == "maps/morrorock.bsp")
	{
		u = 0.5 - 0.5 * BM_Cos (time * 0.08);
		cpos = BM_IntroLerp ('1200 1800 260', '-1200 4200 320', u);
		look = '-5500 500 280';
	}
	else if (mapname == "slo_bike_kitchen" || world.model == "maps/slo_bike_kitchen.bsp")
	{
		u = 0.5 - 0.5 * BM_Cos (time * 0.09);
		cpos = BM_IntroLerp ('2340 -1500 180', '2200 -400 240', u);
		look = '1200 -700 110';
	}
	else
	{
		cpos = getpropertyvec (VF_ORIGIN);
		cpos = cpos + '0 0 18';
		cang_x = -4 + 3 * BM_Sin (time * 0.25);
		cang_y = time * 6;
		cang_z = 0;
		custom_ang = TRUE;
	}

	if (!custom_ang)
		cang = BM_IntroLook (cpos, look);
	setproperty (VF_ORIGIN, cpos);
	setproperty (VF_ANGLES, cang);
	makevectors (cang);
	SetListener (cpos, v_forward, v_right, v_up);
};

void() BM_UpdateIntroCam =
{
	local float card, t0_ms, t, u, u_orb, deg, rad, e, s, blend, sway;
	local vector cpos, look, cang, vpos, vfwd, vright, orb_pos;

	card = getstati (BMST_INTRO);
	if (card <= 0)
		return;
	if (card == 900)
	{
		BM_UpdateMenuBgCam ();
		return;
	}

	t0_ms = getstati (BMST_INTRO_T0);
	t = 0;
	if (t0_ms > 0)
		t = time - (t0_ms * 0.001);
	if (t < 0)
		t = 0;
	intro_cur_t = t;

	// V4 LITTLE SAINT JAMES ISLAND PLAYFUL INTRO (cards 401..404, 60.0s)
	if (card >= 401)
	{
		if (t < 13.5)
		{
			u = t / 13.5;
			if (u < 0) u = 0;
			if (u > 1) u = 1;
			if (u <= 0.56)
			{
				e = BM_IntroSmooth (u / 0.56);
				cpos = BM_IntroLerp ('-12020 -8340 1020', '-12180 -8020 860', e);
				look = BM_IntroLerp ('-12622 -8850 740', '-12560 -8350 660', e);
			}
			else
			{
				e = BM_IntroSmooth ((u - 0.56) / 0.44);
				cpos = BM_IntroLerp ('-12180 -8020 860', '-11850 -7640 800', e);
				look = BM_IntroLerp ('-12560 -8350 660', '-12680 -7680 640', e);
			}
		}
		else if (t < 32.5)
		{
			u = (t - 13.5) / 19.0;
			if (u < 0) u = 0;
			if (u > 1) u = 1;
			s = 0.20 * u + 0.80 * BM_IntroSmooth (u);
			vpos = BM_LsjVanPos (s);
			vfwd = BM_LsjVanFwd (s);
			vright_x = vfwd_y;
			vright_y = 0 - vfwd_x;
			vright_z = 0;
			sway = BM_Sin (u * 6.2831853);
			cpos = vpos - vfwd * (365 - 25 * u) + vright * (105 * sway + 55);
			cpos_z = vpos_z + 145 + 22 * BM_Sin (u * 3.14159265);
			look = vpos + vfwd * 55;
			look_z = vpos_z + 56;
		}
		else if (t < 46.5)
		{
			u = (t - 32.5) / 14.0;
			if (u < 0) u = 0;
			if (u > 1) u = 1;
			if (u <= 0.50)
			{
				e = BM_IntroSmooth (u / 0.50);
				cpos = BM_IntroLerp ('2278.7 2687.2 708.8', '3110 2450 665', e);
				look = BM_IntroLerp ('2654.6 2792.9 625.8', '2790 2790 625', e);
			}
			else
			{
				e = BM_IntroSmooth ((u - 0.50) / 0.50);
				cpos = BM_IntroLerp ('3110 2450 665', '3140 3080 690', e);
				look = '2790 2790 625';
			}
		}
		else
		{
			u_orb = (t - 46.5) / 13.5;
			if (u_orb < 0) u_orb = 0;
			if (u_orb > 1) u_orb = 1;
			deg = 12 + 360 * (0.15 * u_orb + 0.85 * BM_IntroSmooth (u_orb));
			rad = deg * 0.0174532925;
			orb_pos_x = -3740 + BM_Cos (rad) * 9400;
			orb_pos_y = 1378 + BM_Sin (rad) * 8800;
			orb_pos_z = 2150 + 180 * BM_Sin (rad);
			if (u_orb < 0.18)
				blend = BM_IntroSmooth (u_orb / 0.18);
			else
				blend = 1;
			cpos = BM_IntroLerp ('3140 3080 690', orb_pos, blend);
			look = BM_IntroLerp ('2790 2790 625', '-3740 1378 560', blend);
		}
		cang = BM_IntroLook (cpos, look);
		setproperty (VF_ORIGIN, cpos);
		setproperty (VF_ANGLES, cang);
		makevectors (cang);
		SetListener (cpos, v_forward, v_right, v_up);
		BM_UpdateIntroVM (card, t);
		return;
	}

	// V3 ESCALATING MOVIE-LIKE MOD SHOWCASE AT THE HISTORIC FOX THEATER (cards 301..308, 48.0s)
	if (card >= 301)
	{
		if (t < 2.2)
		{
			u = t / 2.2;
			cpos = BM_IntroLerp ('-8590 2115 128', '-8695 2182 64', u);
			look = BM_IntroLerp ('-9340 2485 310', '-9030 2435 88', u);
		}
		else if (t < 5.5)
		{
			u = (t - 2.2) / 3.3;
			cpos = BM_IntroLerp ('-8695 2182 64', '-8752 2224 55', u);
			look = BM_IntroLerp ('-9030 2435 88', '-8990 2382 62', u);
		}
		else if (t < 11.0)
		{
			u = (t - 5.5) / 5.5;
			cpos = BM_IntroLerp ('-8720 2205 50', '-8758 2235 56', u);
			look = BM_IntroLerp ('-8890 2320 48', '-8875 2310 56', u);
		}
		else if (t < 17.0)
		{
			u = (t - 11.0) / 6.0;
			cpos = BM_IntroLerp ('-8645 2152 68', '-8595 2118 88', u);
			look = BM_IntroLerp ('-8925 2345 58', '-8910 2335 72', u);
		}
		else if (t < 24.0)
		{
			u = (t - 17.0) / 7.0;
			cpos = BM_IntroLerp ('-8565 2095 76', '-8465 2025 162', u);
			look = BM_IntroLerp ('-9060 2375 96', '-9240 2420 205', u);
		}
		else if (t < 27.4)
		{
			u = (t - 24.0) / 3.4;
			cpos = BM_IntroLerp ('-8635 2145 78', '-8725 2210 92', u);
			look = BM_IntroLerp ('-8975 2375 96', '-9045 2415 112', u);
		}
		else if (t < 31.0)
		{
			u = (t - 27.4) / 3.6;
			if (u < 0)
				u = 0;
			if (u > 1)
				u = 1;
			u_orb = 0.72 * u + 0.28 * BM_IntroSmooth (u);
			deg = -48 + 360 * u_orb;
			rad = deg * 0.01745329;
			cpos_x = -9990 + BM_Cos (rad) * 1420;
			cpos_y = 3440 + BM_Sin (rad) * 2010;
			cpos_z = 450 + 150 * BM_Sin (u * 3.1415927);
			look_x = -9990 + BM_Cos (rad) * 140;
			look_y = 3440 + BM_Sin (rad) * 200;
			look_z = 415;
		}
		else if (t < 36.2)
		{
			u = (t - 31.0) / 5.2;
			cpos = BM_IntroLerp ('-8860 2050 815', '-8920 2290 860', u);
			look = BM_IntroLerp ('-9565 2525 875', '-9565 2525 890', u);
		}
		else if (t < 40.5)
		{
			u = (t - 36.2) / 4.3;
			cpos = BM_IntroLerp ('-8920 2290 860', '-8820 2090 835', u);
			look = BM_IntroLerp ('-9565 2525 890', '-9565 2525 885', u);
		}
		else
		{
			u = (t - 40.5) / 7.5;
			cpos = BM_IntroLerp ('-8985 2285 285', '-9050 2348 302', u);
			look = BM_IntroLerp ('-9485 2545 375', '-9505 2565 410', u);
		}
		cang = BM_IntroLook (cpos, look);
		setproperty (VF_ORIGIN, cpos);
		setproperty (VF_ANGLES, cang);
		makevectors (cang);
		SetListener (cpos, v_forward, v_right, v_up);
		BM_UpdateIntroVM (card, t);
		return;
	}

	// V2 SHORTER UP-CLOSE SPRITE-ONLY FOX 360 -> 50-SWARM -> BURNING FOX + FLOATING CCCs, DAN & ROB (cards 201..204, 22.5s)
	if (card >= 201)
	{
		if (t < 6.6)
		{
			u = t / 6.6;
			if (u > 1)
				u = 1;
			u_orb = 0.72 * u + 0.28 * BM_IntroSmooth (u);
			deg = -48 + 360 * u_orb;
			rad = deg * 0.01745329;
			cpos_x = -9990 + BM_Cos (rad) * 1420;
			cpos_y = 3440 + BM_Sin (rad) * 2010;
			cpos_z = 450 + 150 * BM_Sin (u * 3.1415927);
			look_x = -9990 + BM_Cos (rad) * 140;
			look_y = 3440 + BM_Sin (rad) * 200;
			look_z = 415;
		}
		else if (t < 11.8)
		{
			u = (t - 6.6) / 5.2;
			cpos = BM_IntroLerp ('-8860 2050 815', '-8920 2290 860', u);
			look = BM_IntroLerp ('-9565 2525 875', '-9565 2525 890', u);
		}
		else if (t < 15.3)
		{
			u = (t - 11.8) / 3.5;
			cpos = BM_IntroLerp ('-8920 2290 860', '-8820 2090 835', u);
			look = BM_IntroLerp ('-9565 2525 890', '-9565 2525 885', u);
		}
		else
		{
			u = (t - 15.3) / 7.2;
			cpos = BM_IntroLerp ('-8985 2285 285', '-9045 2345 300', u);
			look = BM_IntroLerp ('-9485 2545 375', '-9505 2565 410', u);
		}
		cang = BM_IntroLook (cpos, look);
		setproperty (VF_ORIGIN, cpos);
		setproperty (VF_ANGLES, cang);
		makevectors (cang);
		SetListener (cpos, v_forward, v_right, v_up);
		BM_UpdateIntroVM (card, t);
		return;
	}

	// FOX 360 ORBIT (3 MILKYS + 3 WHEELMANS) -> 50-SWARM CLOCK TOWER SPIN & MASS EXPLOSION (cards 101..105)
	if (card >= 101)
	{
		if (t < 14.5)
		{
			u = t / 14.5;
			if (u > 1)
				u = 1;
			u_orb = 0.65 * u + 0.35 * BM_IntroSmooth (u);
			deg = -48 + 360 * u_orb;
			rad = deg * 0.01745329;
			cpos_x = -9990 + BM_Cos (rad) * 1450;
			cpos_y = 3440 + BM_Sin (rad) * 2040;
			cpos_z = 455 + 185 * BM_Sin (u * 3.1415927);
			look_x = -9990 + BM_Cos (rad) * 145;
			look_y = 3440 + BM_Sin (rad) * 204;
			look_z = 420;
		}
		else if (t < 17.0)
		{
			u = (t - 14.5) / 2.5;
			cpos = BM_IntroLerp ('-8420 1740 500', '-8510 1830 530', u);
			look = BM_IntroLerp ('-9565 2525 880', '-9565 2525 910', u);
		}
		else if (t < 25.0)
		{
			u = (t - 17.0) / 8.0;
			cpos = BM_IntroLerp ('-8510 1830 530', '-8490 2380 575', u);
			look = BM_IntroLerp ('-9565 2525 910', '-9565 2525 920', u);
		}
		else if (t < 31.0)
		{
			u = (t - 25.0) / 6.0;
			cpos = BM_IntroLerp ('-8490 2380 575', '-8380 2040 540', u);
			look = BM_IntroLerp ('-9565 2525 920', '-9565 2525 890', u);
		}
		else
		{
			u = (t - 31.0) / 5.0;
			cpos = BM_IntroLerp ('-8380 2040 540', '-8640 2090 148', u);
			look = BM_IntroLerp ('-9565 2525 760', '-9320 2420 140', u);
		}
		cang = BM_IntroLook (cpos, look);
		setproperty (VF_ORIGIN, cpos);
		setproperty (VF_ANGLES, cang);
		makevectors (cang);
		SetListener (cpos, v_forward, v_right, v_up);
		BM_UpdateIntroVM (card, t);
		return;
	}

	// 01. (0.0s .. 2.5s) FOX CURB CLOSE-UP: WHITE VAN + WHEELMAN ARRIVAL
	if (t < 2.5)
	{
		u = t / 2.5;
		cpos = BM_IntroLerp ('-8715 2195 58', '-8755 2225 56', u);
		look = BM_IntroLerp ('-9020 2430 58', '-8995 2385 62', u);
	}
	// 02. (2.5s .. 7.5s) WHEELMAN CLOSE-UP SHOWTIME!
	else if (t < 7.5)
	{
		u = (t - 2.5) / 5.0;
		cpos = BM_IntroLerp ('-8720 2205 50', '-8758 2235 56', u);
		look = BM_IntroLerp ('-8890 2320 48', '-8875 2310 56', u);
	}
	// 03. (7.5s .. 12.0s) HISTORIC FOX THEATER EXTERIOR & SIDEWALK RACE
	else if (t < 12.0)
	{
		u = (t - 7.5) / 4.5;
		cpos = BM_IntroLerp ('-8580 2105 64', '-8480 2040 175', u);
		look = BM_IntroLerp ('-9180 2390 130', '-9360 2445 365', u);
	}
	// 04. (12.0s .. 16.4s) FOX GRAND LOBBY: PAINTER & THINKER WHEELMAN
	else if (t < 16.4)
	{
		u = (t - 12.0) / 4.4;
		cpos = BM_IntroLerp ('-10150 2560 72', '-10085 2536 76', u);
		look = BM_IntroLerp ('-9975 2485 64', '-9975 2505 86', u);
	}
	// 05. (16.4s .. 20.8s) FOX SUNBURST STAGE: OPERATIC TENOR WHEELMAN
	else if (t < 20.8)
	{
		u = (t - 16.4) / 4.4;
		cpos = BM_IntroLerp ('-10086 3915 108', '-10086 4025 102', u);
		look = BM_IntroLerp ('-10086 4195 104', '-10086 4205 116', u);
	}
	// 06. (20.8s .. 25.0s) FOX CLOCK TOWER BELFRY: ZEN WHEEL-GURU & JETPACK
	else if (t < 25.0)
	{
		u = (t - 20.8) / 4.2;
		cpos = BM_IntroLerp ('-9635 2525 956', '-9585 2525 956', u);
		look = BM_IntroLerp ('-9200 2525 940', '-8800 2525 915', u);
	}
	// 07. (25.0s .. 29.4s) NILE THEATER & TEVIS BLOCK: DJ WHEELMAN
	else if (t < 29.4)
	{
		u = (t - 25.0) / 4.4;
		cpos = BM_IntroLerp ('-10540 -2310 68', '-10660 -2285 112', u);
		look = BM_IntroLerp ('-11028 -2510 125', '-11028 -2545 180', u);
	}
	// 08. (29.4s .. 33.8s) NILE CONCERT HALL: TITAN WHEELMAN & MEGA MAN
	else if (t < 33.8)
	{
		u = (t - 29.4) / 4.4;
		cpos = BM_IntroLerp ('-11028 -3650 72', '-11028 -3745 68', u);
		look = BM_IntroLerp ('-11028 -3940 82', '-11028 -3955 92', u);
	}
	// 09. (33.8s .. 38.2s) HISTORIC PADRE HOTEL TOWER: PIPE-JET RACE
	else if (t < 38.2)
	{
		u = (t - 33.8) / 4.4;
		cpos = BM_IntroLerp ('-8640 -6310 74', '-8520 -6430 440', u);
		look = BM_IntroLerp ('-9010 -6020 195', '-9105 -5950 860', u);
	}
	// 10. (38.2s .. 42.4s) PADRE ART DECO LOBBY: 777 JACKPOT & WHEEL-FU
	else if (t < 42.4)
	{
		u = (t - 38.2) / 4.2;
		cpos = BM_IntroLerp ('-9829 -5740 64', '-9829 -5625 60', u);
		look = BM_IntroLerp ('-9829 -5430 54', '-9829 -5405 62', u);
	}
	// 11. (42.4s .. 50.8s) MIDPOINT SHOWSTOPPER: 10 MILKY MILKY GRENADES FLOATING AROUND!
	else if (t < 50.8)
	{
		u = (t - 42.4) / 8.4;
		cpos = BM_IntroLerp ('-8790 -5620 76', '-8790 -5360 88', u);
		look = BM_IntroLerp ('-8810 -5220 108', '-8810 -4980 114', u);
	}
	// 12. (50.8s .. 55.2s) 18TH & EYE PARKING GARAGE: BUILDER WHEELMAN & MR. DIY
	else if (t < 55.2)
	{
		u = (t - 50.8) / 4.4;
		cpos = BM_IntroLerp ('-4660 -6410 68', '-4760 -6490 136', u);
		look = BM_IntroLerp ('-5040 -6030 138', '-5310 -5930 265', u);
	}
	// 13. (55.2s .. 59.6s) GARAGE LEVEL 6 OVERLOOK: ROOFTOP DANCE-OFF
	else if (t < 59.6)
	{
		u = (t - 55.2) / 4.4;
		cpos = BM_IntroLerp ('-7020 -5370 712', '-7320 -5390 736', u);
		look = BM_IntroLerp ('-9040 -5780 680', '-9090 -5820 760', u);
	}
	// 14. (59.6s .. 64.0s) DAGNY'S COFFEE & JAMES BUILDING: MATRIX HACKER & TABLE FLIP
	else if (t < 64.0)
	{
		u = (t - 59.6) / 4.4;
		cpos = BM_IntroLerp ('-4530 1830 68', '-4610 1900 128', u);
		look = BM_IntroLerp ('-4960 2260 106', '-5050 2320 185', u);
	}
	// 15. (64.0s .. 68.4s) SANDRINI'S & EYE ST: PICKLE SURPRISE & GOO TRAP
	else if (t < 68.4)
	{
		u = (t - 64.0) / 4.4;
		cpos = BM_IntroLerp ('-4465 460 68', '-4455 200 98', u);
		look = BM_IntroLerp ('-4130 -35 98', '-4090 -175 132', u);
	}
	// 16. (68.4s .. 72.8s) GUTHRIE'S ALLEY CAT: BONK FRYING PAN LAUNCH
	else if (t < 72.8)
	{
		u = (t - 68.4) / 4.4;
		cpos = BM_IntroLerp ('-2520 -4415 70', '-2810 -4415 84', u);
		look = BM_IntroLerp ('-3120 -4490 102', '-3250 -4495 132', u);
	}
	// 17. (72.8s .. 77.2s) JERRY'S PIZZA & CHESTER AVE: FLAMBE CHEF WHEELMAN
	else if (t < 77.2)
	{
		u = (t - 72.8) / 4.4;
		cpos = BM_IntroLerp ('-430 -3820 68', '-400 -3930 112', u);
		look = BM_IntroLerp ('-685 -4035 112', '-700 -4075 162', u);
	}
	// 18. (77.2s .. 81.6s) S. H. KRESS BUILDING: PINK SUPERCAR DRAG RACE
	else if (t < 81.6)
	{
		u = (t - 77.2) / 4.4;
		cpos = BM_IntroLerp ('4880 -2140 72', '4690 -2205 138', u);
		look = BM_IntroLerp ('4080 -2520 145', '4020 -2540 225', u);
	}
	// 19. (81.6s .. 85.8s) THE MINT BAR & BAKERSFIELD HOTEL: ROCKET TRASH CAN
	else if (t < 85.8)
	{
		u = (t - 81.6) / 4.2;
		cpos = BM_IntroLerp ('11140 -2340 70', '11270 -2280 124', u);
		look = BM_IntroLerp ('11540 -2810 112', '11575 -2825 158', u);
	}
	// 20. (85.8s .. 90.0s) HISTORIC FOX THEATER WHEELMAN & MILKY GRAND FINALE
	else
	{
		u = (t - 85.8) / 4.2;
		cpos = BM_IntroLerp ('-8560 2095 72', '-8340 1965 235', u);
		look = BM_IntroLerp ('-9140 2375 165', '-9320 2425 340', u);
	}

	cang = BM_IntroLook (cpos, look);
	setproperty (VF_ORIGIN, cpos);
	setproperty (VF_ANGLES, cang);
	makevectors (cang);
	SetListener (cpos, v_forward, v_right, v_up);
	BM_UpdateIntroVM (card, t);
};

void(float x, float y, string s, float sz, vector rgb, float a) BM_ShadowCentered =
{
	local float wd;
	local vector sv, pv, off;

	sv = BM_UIScale (sz) * '1 1 0';
	wd = stringwidth (s, FALSE, sv);
	pv = (x - wd * 0.5) * '1 0 0' + y * '0 1 0';
	off = (sz * 0.13) * '1 1 0';
	drawstring (pv + off, s, sv, '0 0 0', a * 0.92, 0);
	drawstring (pv, s, sv, rgb, a, 0);
};

void(float w, float h) BM_DrawIntroHUD =
{
	local float card, cx, bh, age, pop, slide, hero, wt, ws, pw, ph, py, pulse;
	local string title, sub, topbar;
	local vector col, sv1, sv2;

	card = getstati (BMST_INTRO);
	if (card <= 0 || card == 900)
		return;

	w = cvar ("vid_conwidth");
	h = cvar ("vid_conheight");
	cx = w * 0.5;

	// Splash white milk drips down the camera lens during Card 11's triple Milky detonation!
	Milk_DrawHUD (w, h);

	bh = floor (h * 0.082);
	if (bh < 22)
		bh = 22;

	// Widescreen cinema letterbox bars + Bakersfield gold trim
	drawfill ('0 0 0', w * '1 0 0' + bh * '0 1 0', '0.02 0.02 0.03', 0.92, 0);
	drawfill ((h - bh) * '0 1 0', w * '1 0 0' + bh * '0 1 0', '0.02 0.02 0.03', 0.92, 0);
	drawfill ((bh - 1) * '0 1 0', w * '1 0 0' + '0 1 0', '1 0.80 0.18', 0.58, 0);
	drawfill ((h - bh) * '0 1 0', w * '1 0 0' + '0 1 0', '1 0.80 0.18', 0.58, 0);

	if (card != intro_prev_card)
	{
		intro_prev_card = card;
		intro_card_t = time;
	}
	age = time - intro_card_t;
	if (age < 0)
		age = 0;
	pop = 0.68 + 0.32 * BM_IntroSmooth (age / 0.18);
	slide = (1 - BM_IntroSmooth (age / 0.18)) * 5;
	pulse = sin (time * 6);

	// On architectural comedy scenes (cards 3..19 except the 10-Milky midpoint showstopper), fade lower-third after 2.5s
	if (card >= 3 && card <= 19 && card != 11 && age > 2.50)
		pop = pop * (1 - BM_IntroSmooth ((age - 2.50) / 0.60));
	else if (card == 11 && age > 4.60)
		pop = pop * (1 - BM_IntroSmooth ((age - 4.60) / 0.80));
	else if ((card == 101 || card == 103) && age > 3.60)
		pop = pop * (1 - BM_IntroSmooth ((age - 3.60) / 0.70));
	else if ((card == 201 || card == 202) && age > 3.00)
		pop = pop * (1 - BM_IntroSmooth ((age - 3.00) / 0.55));
	else if (card == 204 && age > 4.20)
		pop = pop * (1 - BM_IntroSmooth ((age - 4.20) / 0.65));
	else if (card >= 301 && card <= 306 && age > 3.20)
		pop = pop * (1 - BM_IntroSmooth ((age - 3.20) / 0.60));
	else if (card == 308 && age > 4.60)
		pop = pop * (1 - BM_IntroSmooth ((age - 4.60) / 0.70));
	else if (card >= 401 && card <= 403 && age > 3.40)
		pop = pop * (1 - BM_IntroSmooth ((age - 3.40) / 0.65));
	else if (card == 404 && age > 4.20)
		pop = pop * (1 - BM_IntroSmooth ((age - 4.20) / 0.70));

	hero = 0;
	title = "";
	sub = "";
	col = '1 0.84 0.18';
	topbar = "BAKERSFIELD QUAKE  //  WHEELMAN & DOWNTOWN COMEDY TOUR";

	if (card == 1)
	{
		hero = 1;
		title = "BAKERSFIELD QUAKE";
		sub = "WHITE LAN VAN SCREECHES UP TO THE FOX WITH WHEELMAN!";
		col = '1 0.84 0.18';
		topbar = "HISTORIC FOX THEATER  //  20TH & H ST  -  WHEELMAN ARRIVAL";
	}
	else if (card == 2)
	{
		hero = 1;
		title = "WHEELMAN CLOSE-UP SHOWTIME!";
		sub = "FIRE-WHEELS BURNOUT  ->  B-BOY HEADSPIN  ->  PIPE-JET AFTERBURNER!";
		col = '1 0.48 0.20';
		topbar = "STARRING WHEELMAN  //  UP-CLOSE IN FRONT OF THE FOX THEATER";
	}
	else if (card == 3)
	{
		title = "THE HISTORIC FOX THEATER  (1930)";
		sub = "3D SEATED ROLLER WHEELMAN RACES JESSKART PAST SCISSORS KYLE!";
		col = '1 0.80 0.28';
		topbar = "2001 H STREET  //  SPANISH COLONIAL CLOCK TOWER & SIDEWALK RACE";
	}
	else if (card == 4)
	{
		title = "FOX GRAND LOBBY  -  LE PENSEUR A ROUES";
		sub = "FRENCH BERET PAINTER WHEELMAN & 3D MARBLE THINKER SCULPTURE";
		col = '0.95 0.82 0.42';
		topbar = "FOX THEATER INTERIOR  //  FINE ART & HIGH CULTURE ON TIRES";
	}
	else if (card == 5)
	{
		title = "FOX 1930 SUNBURST STAGE  -  OPERA TENOR";
		sub = "OPERATIC WHEELMAN BELTS HIGH C WITH FLAMINGO FIEND!";
		col = '1 0.78 0.34';
		topbar = "FOX AUDITORIUM  //  LIVE FROM THE GILDED PROSCENIUM ARCH";
	}
	else if (card == 6)
	{
		title = "FOX CLOCK TOWER BELFRY  -  ZEN WHEEL-GURU";
		sub = "LEVITATING LOTUS WHEELMAN, JETPACK FIGHTER & WINGED JOHN-BIRD";
		col = '0.92 0.86 0.56';
		topbar = "74-FT FOX BELFRY  //  ENLIGHTENMENT ABOVE H STREET";
	}
	else if (card == 7)
	{
		title = "THE NILE THEATER  -  DJ PELVIC-TIRE SET";
		sub = "WHEELMAN SCRATCHES VINYL ON HIS OWN TIRES FOR 19TH ST!";
		col = '0.46 0.88 1';
		topbar = "1721 19TH STREET  //  THE NILE NEON MARQUEE & TEVIS BLOCK";
	}
	else if (card == 8)
	{
		title = "NILE CONCERT HALL  -  TITAN WHEELMAN";
		sub = "3D OVERHEAD AXLE TITAN WHEELMAN & MEGA MAN DOME BLAST!";
		col = '0.52 0.84 1';
		topbar = "THE NILE INTERIOR  //  1924 MAIN FLOOR CONCERT STAGE";
	}
	else if (card == 9)
	{
		title = "THE HISTORIC PADRE HOTEL  (1928)";
		sub = "SUPERSONIC PIPE-JET WHEELMAN RACES JETPACK UP ALL 8 STORIES!";
		col = '1 0.78 0.28';
		topbar = "1702 18TH STREET  //  8-STORY SPANISH REVIVAL SKYSCRAPER RACE";
	}
	else if (card == 10)
	{
		title = "PADRE HOTEL LOBBY  -  777 JACKPOT!";
		sub = "DAVID HITS TRIPLE SEVENS BESIDE SHAOLIN WHEEL-FU & HORSE!";
		col = '1 0.84 0.36';
		topbar = "PADRE ART DECO FOYER  //  HIGH ROLLERS & FLYING TIRES";
	}
	else if (card == 11)
	{
		hero = 1;
		title = "10 MILKY MILKY GRENADES!";
		sub = "FLOATING, SINGING, SLIPPING IN MILK PUDDLES & TRIPLE SPLATTER BOOM!";
		col = '1 0.62 0.88';
		topbar = "MIDPOINT SHOWSTOPPER  //  10 MILKY MILKY GRENADES FLOATING ON H ST!";
	}
	else if (card == 12)
	{
		title = "18TH & EYE GARAGE  -  BUILDER WHEELMAN";
		sub = "HARD-HAT ANVIL WHEELMAN HAMMERS SPARKS WITH MR. DIY & FORKLIFT!";
		col = '0.52 0.94 0.72';
		topbar = "1600 EYE STREET  //  OSHA HAS COMPLETELY LEFT THE CHAT";
	}
	else if (card == 13)
	{
		title = "GARAGE LEVEL 6  -  ROOFTOP DANCE-OFF";
		sub = "CRAZED WHEELMAN DANCER, 3D ROLLER & BRYAN OVERLOOKING THE PADRE";
		col = '0.64 0.92 0.98';
		topbar = "54-FT LEVEL 6 DECK  //  1818 H ST & PADRE SKYLINE VISTA";
	}
	else if (card == 14)
	{
		title = "DAGNY'S COFFEE  -  300-WPM MATRIX HACKER";
		sub = "CYBER-DESK WHEELMAN & 4 AM DANIEL FLIPPING HIS TABLE AT DAD!";
		col = '0.58 0.96 0.88';
		topbar = "20TH & EYE CORNER  //  DAGNY'S CAFE & THE JAMES BUILDING";
	}
	else if (card == 15)
	{
		title = "SANDRINI'S & EYE ST  -  PICKLE SURPRISE!";
		sub = "SHAOLIN WHEEL-FU KICKS A GIANT BOUNCING PICKLE & GOO FOAM TRAP!";
		col = '0.72 0.96 0.56';
		topbar = "1918 EYE STREET  //  SANDRINI'S PUBLIC HOUSE & ARTS PLAZA";
	}
	else if (card == 16)
	{
		title = "GUTHRIE'S ALLEY CAT  -  FRYING PAN *CLANG!*";
		sub = "HEADSPIN WHEELMAN WATCHES BONK HAMMER LAUNCH GOLD FIGHTER!";
		col = '1 0.78 0.34';
		topbar = "1525 WALL STREET ALLEY  //  BRICK MURALS & CAST-IRON COMEDY";
	}
	else if (card == 17)
	{
		title = "JERRY'S PIZZA  -  5-STAR FLAMBE CHEF";
		sub = "CHEF TOQUE WHEELMAN SEARS STEAK BESIDE A HOPPING MYSTERY BOX!";
		col = '1 0.58 0.42';
		topbar = "1817 CHESTER AVENUE  //  HISTORIC STOREFRONTS & FLAMBE";
	}
	else if (card == 18)
	{
		title = "S. H. KRESS  -  IT'S NOT PINK! DRAG RACE";
		sub = "3D SEATED ROLLER WHEELMAN DRAG-RACES THE SALMON SUPERCAR!";
		col = '1 0.80 0.32';
		topbar = "19TH & K STREET  //  ART DECO TERRA-COTTA & FULL THROTTLE";
	}
	else if (card == 19)
	{
		title = "THE MINT BAR  -  ROCKET TRASH CAN LIFTOFF";
		sub = "DJ WHEELMAN, JOHNWAVE TIDAL RING & ORBITAL MUNICIPAL TRASH!";
		col = '0.52 0.90 1';
		topbar = "1207 19TH STREET  //  THE MINT BAR & BAKERSFIELD HOTEL";
	}
	else if (card == 101)
	{
		hero = 1;
		title = "HISTORIC FOX THEATER  -  360 ORBIT";
		sub = "3 MILKY MILKY GRENADES & 3 WHEELMAN SPRITES FLOATING ALL AROUND!";
		col = '1 0.84 0.18';
		topbar = "BAKERSFIELD QUAKE  //  360 FOX THEATER ORBIT  -  3 MILKYS & 3 WHEELMANS";
	}
	else if (card == 102)
	{
		hero = 1;
		title = "WAIT... 50 MILKYS & WHEELMANS?!";
		sub = "25 MILKYS + 25 WHEELMANS SUDDENLY SWARMING THE FOX CLOCK TOWER!";
		col = '1 0.56 0.88';
		topbar = "2001 H STREET  //  SUDDEN 50-ENTITY SWARM ON THE FOX CLOCK TOWER!";
	}
	else if (card == 103)
	{
		title = "50-ENTITY CLOCK TOWER CYCLONE!";
		sub = "ALL 50 MILKYS & WHEELMANS SPINNING FASTER & FASTER AROUND THE SPIRE!";
		col = '0.52 0.92 1';
		topbar = "FOX CLOCK TOWER VORTEX  //  SUPERSONIC MILKY & WHEELMAN TORNADO";
	}
	else if (card == 104)
	{
		hero = 1;
		title = "ALL 50 EXPLODE AT ONCE!!";
		sub = "25 MILKY GEYSERS + 25 WHEELMAN FIREBALLS ERUPT UP THE CLOCK TOWER!";
		col = '1 0.42 0.22';
		topbar = "TOTAL DAIRY & TIRE DETONATION  //  50-ENTITY TOWER APOCALYPSE!";
	}
	else if (card == 201)
	{
		hero = 1;
		title = "FOX THEATER 360  -  MILKY & WHEELMAN!";
		sub = "3 MILKYS + 3 WHEELMAN SPRITES FLOATING UP CLOSE ALL AROUND THE FOX!";
		col = '1 0.84 0.18';
		topbar = "BAKERSFIELD QUAKE  //  UP-CLOSE 360 FOX ORBIT  -  MILKY SONG NON-STOP!";
	}
	else if (card == 202)
	{
		hero = 1;
		title = "50 MILKYS & WHEELMANS ON THE TOWER!!";
		sub = "25 MILKYS + 25 WHEELMAN SPRITES SPINNING UP CLOSE AROUND THE BELFRY!";
		col = '1 0.56 0.88';
		topbar = "2001 H STREET  //  UP-CLOSE 50-SPRITE FOX CLOCK TOWER CYCLONE!";
	}
	else if (card == 203)
	{
		hero = 1;
		title = "ALL 50 EXPLODE IN YOUR FACE!!";
		sub = "25 MILKY GEYSERS + 25 360-DEG WHEELMAN SPRITE FIREBALLS ERUPT!";
		col = '1 0.42 0.22';
		topbar = "TOTAL TOWER DETONATION  //  50 MILKYS & WHEELMAN SPRITES GO BOOM!";
	}
	else if (card == 204)
	{
		hero = 1;
		title = "FOX ON FIRE!  CCCs, DAN & ROB!";
		sub = "I'M FLOATING!!   AH, I CAN'T SEE!!   C-C-C-C-C-C!!";
		col = '1 0.90 0.18';
		topbar = "BLAZING FOX THEATER  //  FLOATING DAN + ROB + CCCCCCs  -  AH I CAN'T SEE!";
	}
	else if (card == 301)
	{
		hero = 1;
		title = "BAKERSFIELD QUAKE: THE MOVIE";
		sub = "A QUIET NIGHT AT THE FOX THEATER... UNTIL THE WHITE VAN ARRIVES!";
		col = '1 0.84 0.18';
		topbar = "ACT I  //  HISTORIC FOX THEATER  (20TH & H ST)  -  ENTER THE WHITE VAN";
	}
	else if (card == 302)
	{
		hero = 1;
		title = "WHEELMAN UNLEASHED!";
		sub = "BARN DOORS BLOW OFF!  FIRE-WHEELS -> HEADSPIN -> PIPE-JET!";
		col = '1 0.48 0.20';
		topbar = "ACT II  //  STARRING WHEELMAN  -  3D ROOF SCULPTURE & GREEN-SUIT WHEELMAN";
	}
	else if (card == 303)
	{
		title = "HOW MANY PEOPLE ARE IN THAT WHITE VAN?!";
		sub = "4AM TABLE FLIP + NETSEND + LAPTOP HEAD + PICKLE SURPRISE + BONK CLANG!";
		col = '0.52 0.94 0.78';
		topbar = "ACT III  //  CLOWN-CAR CAST PILEOUT & CUSTOM FUN-GUN ARSENAL";
	}
	else if (card == 304)
	{
		title = "RUSH HOUR ON H STREET  -  EVERY GUN & VEHICLE!";
		sub = "NOT-PINK SUPERCAR + BUS + BIKES + MEGA MAN + GARAND + ROCKET TRASH CANS!";
		col = '0.48 0.88 1';
		topbar = "ACT IV  //  20TH & H STAMPEDE  -  ROB DOB, SENTRY, JOHN-BIRDS & JETPACKS";
	}
	else if (card == 305)
	{
		hero = 1;
		title = "MILKY INVASION & FOX 360!";
		sub = "SINGING PINK LADIES, SLIPPERY MILK PUDDLES & 360 FOX ORBIT!";
		col = '1 0.60 0.88';
		topbar = "ACT V  //  MILKY MILKY GRENADE SWARM  -  SLIPPING & 360 AERIAL ORBIT";
	}
	else if (card == 306)
	{
		hero = 1;
		title = "50-ENTITY TOWER TORNADO!!";
		sub = "NO WAY!!  50 WHEELMANS, MILKYS, PICKLES & MEGA MEN ON THE SPIRE!";
		col = '0.52 0.92 1';
		topbar = "ACT VI  //  74-FT FOX CLOCK TOWER  -  CATEGORY-5 BAKERSFIELD CYCLONE";
	}
	else if (card == 307)
	{
		hero = 1;
		title = "ALL 50 EXPLODE AT ONCE!!";
		sub = "DAIRY GEYSERS + 360 WHEELMAN FIREBALLS + TIRES + LENS MILK SPLAT!";
		col = '1 0.42 0.22';
		topbar = "ACT VII  //  TOTAL THERMONUCLEAR DAIRY & TIRE APOCALYPSE!";
	}
	else if (card == 308)
	{
		hero = 1;
		title = "FOX ON FIRE!  CCCs, DAN & ROB!";
		sub = "I'M FLOATING!!   AH, I CAN'T SEE!!   WRECKED VAN & 24 YELLOW Cs!";
		col = '1 0.90 0.18';
		topbar = "ACT VIII  //  GRAND FINALE  -  BURNING FOX + FLOATING DAN, WHEELMAN & ROB";
	}
	else if (card == 105)
	{
		hero = 1;
		title = "BAKERSFIELD QUAKE  -  FOX AFTERMATH";
		sub = "RAINING TIRES, MILK-DRENCHED H STREET & LENS SPLATTER FINALE!";
		col = '1 0.84 0.18';
		topbar = "DOWNTOWN BAKERSFIELD  //  HISTORIC FOX THEATER SURVIVES";
	}
	else if (card == 401)
	{
		hero = 1;
		title = "LITTLE SAINT JAMES ISLAND";
		sub = "MILKY JESS GRENADES & A DOZEN GREEN WHEEL GUYS AT THE TEMPLE!";
		col = '0.48 0.88 1';
		topbar = "ACT I  //  LITTLE SAINT JAMES  -  BLUE-STRIPED TEMPLE & GREEN WHEEL GUYS";
	}
	else if (card == 402)
	{
		hero = 0;
		title = "WHITE VAN ISLAND CRUISE";
		sub = "MILKY JESS GRENADES CHASING THE WHITE VAN ACROSS EPSTEIN ISLAND!";
		col = '1 0.72 0.88';
		topbar = "ACT II  //  ISLAND HIGHWAY  -  WHITE VAN PURSUED BY MILKY JESS GRENADES";
	}
	else if (card == 403)
	{
		hero = 1;
		title = "EVERYBODY OUT!!";
		sub = "SHOOTING, JUMPING & COMEDY SOUND MEDLEY ON THE ISLAND LAWN!";
		col = '1 0.86 0.22';
		topbar = "ACT III  //  CAST PILEOUT  -  SHOOTING, JUMPING & FUNNY SOUNDS";
	}
	else if (card == 404)
	{
		hero = 1;
		title = "BAKERSFIELD QUAKE";
		sub = "360 AERIAL TOUR OF EPSTEIN ISLAND  -  PRESS FIRE OR JUMP TO PLAY!";
		col = '0.52 0.94 0.78';
		topbar = "ACT IV  //  LITTLE SAINT JAMES  -  360 ISLAND ORBIT FINALE";
	}
	else
	{
		hero = 1;
		title = "BAKERSFIELD QUAKE  -  DOWNTOWN";
		sub = "WHEELMAN ALL-STARS, FLOATING MILKY & CREW AT THE HISTORIC FOX!";
		col = '1 0.84 0.18';
		topbar = "DOWNTOWN BAKERSFIELD  //  WHEELMAN & MILKY GRAND FINALE";
	}

	BM_ShadowCentered (cx, floor ((bh - 7) * 0.5), topbar, 7, '0.95 0.82 0.42', 0.88);

	if (title == "" || pop <= 0.02)
		return;

	if (hero)
	{
		sv1 = BM_UIScaleVec ('17 17 0');
		sv2 = BM_UIScaleVec ('8 8 0');
		wt = stringwidth (title, FALSE, sv1);
		ws = stringwidth (sub, FALSE, sv2);
		pw = wt;
		if (ws > pw)
			pw = ws;
		pw = pw + 34;
		ph = 40;
		py = h - bh - 28 + slide;
		drawfill ((cx - pw * 0.5) * '1 0 0' + py * '0 1 0', pw * '1 0 0' + ph * '0 1 0', '0.05 0.04 0.07', 0.90 * pop, 0);
		drawfill ((cx - pw * 0.5) * '1 0 0' + py * '0 1 0', pw * '1 0 0' + '0 2 0', col, (0.82 + 0.15 * pulse) * pop, 0);
		drawfill ((cx - pw * 0.5) * '1 0 0' + (py + ph - 2) * '0 1 0', pw * '1 0 0' + '0 2 0', col, (0.82 + 0.15 * pulse) * pop, 0);
		drawfill ((cx - pw * 0.5) * '1 0 0' + py * '0 1 0', '4 0 0' + ph * '0 1 0', '1 0.35 0.12', 0.95 * pop, 0);
		drawfill ((cx + pw * 0.5 - 4) * '1 0 0' + py * '0 1 0', '4 0 0' + ph * '0 1 0', '1 0.35 0.12', 0.95 * pop, 0);
		BM_ShadowCentered (cx, py + 4, title, 17, col, pop);
		BM_ShadowCentered (cx, py + 25, sub, 8, '1 1 1', 0.96 * pop);
	}
	else
	{
		sv1 = BM_UIScaleVec ('11 11 0');
		sv2 = BM_UIScaleVec ('7 7 0');
		wt = stringwidth (title, FALSE, sv1);
		ws = stringwidth (sub, FALSE, sv2);
		pw = wt;
		if (ws > pw)
			pw = ws;
		pw = pw + 26;
		ph = 29;
		py = h - bh - 16 + slide;
		drawfill ((cx - pw * 0.5) * '1 0 0' + py * '0 1 0', pw * '1 0 0' + ph * '0 1 0', '0.05 0.05 0.08', 0.88 * pop, 0);
		drawfill ((cx - pw * 0.5) * '1 0 0' + py * '0 1 0', pw * '1 0 0' + '0 1 0', col, 0.80 * pop, 0);
		drawfill ((cx - pw * 0.5) * '1 0 0' + py * '0 1 0', '3 0 0' + ph * '0 1 0', col, 0.95 * pop, 0);
		drawfill ((cx + pw * 0.5 - 3) * '1 0 0' + py * '0 1 0', '3 0 0' + ph * '0 1 0', col, 0.95 * pop, 0);
		BM_ShadowCentered (cx, py + 3, title, 11, col, pop);
		BM_ShadowCentered (cx, py + 17, sub, 7, '0.96 0.96 0.98', 0.95 * pop);
	}
};

// ---- Visibility rays for models and dynamic lights, chosen per map.
// The engine decides whether a model or a dynamic light is hidden by firing rays at it. With
// r_cullentities_trace_entityocclusion 1 (the engine default) each ray tests wall faces one by one, and these maps keep
// thousands of faces on one BSP node. Measured 2026-11-18 on a recorded 15-bot match: terminal21 played at 46 fps with
// dips to 10; with the classic world-only test (0) at 311 fps with dips to 121. No other map lost anything.
// The world-only test is blocked by see-through faces that sit on SOLID world brushes (fire-escape gratings, window
// panes): it could hide a player standing behind one. So it is switched on only for maps that have no such face.
// source/mm_tools/perf/fence_solid.py lists them per map; run it before adding a map here. Every other map keeps the
// engine default. bm_tracecull_auto 0 leaves the engine setting alone.
float(string n) BM_MapIs =
{
	if (mapname == n)
		return TRUE;
	if (mapname == strcat ("maps/", n))
		return TRUE;
	if (mapname == strcat ("maps/", n, ".bsp"))
		return TRUE;
	return FALSE;
};

void() BM_TraceCullSetup =
{
	registercvar ("bm_tracecull_auto", "1");
	if (!cvar ("bm_tracecull_auto"))
		return;
	if (BM_MapIs ("terminal21") || BM_MapIs ("morrorock") || BM_MapIs ("soi6") || BM_MapIs ("soicowboy_bkk")
	 || BM_MapIs ("lolmap1") || BM_MapIs ("little_st_james") || BM_MapIs ("ooika_lawrenceville") || BM_MapIs ("slo_bike_kitchen"))
		cvar_set ("r_cullentities_trace_entityocclusion", "0");
	else
		cvar_set ("r_cullentities_trace_entityocclusion", "1");
};
