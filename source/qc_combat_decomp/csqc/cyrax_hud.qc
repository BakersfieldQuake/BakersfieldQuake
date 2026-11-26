/*
================
CYRAX NET CSQC HUD (cyrax_hud.qc)

Reads clientstats 128..132 sent from progs.dat (bm_match.qc BM_Stats):
	128 CYST_MODE   0=off, 1=charging Cyrax, 2=pulling target, 3=holding target ready to Bonk, 4=trapped in Cyrax net (victim)
	129 CYST_PROG   mode 1 -> 0..100 charge %; mode 2/3/4 -> remaining tenths of a second (0..300)
	130 CYST_FLASH  integer counter incremented on every new net capture
	131 CYST_KIND   0=player/bot, 1=Winged John Bird, 2=Milky Grenade
	132 CYST_DIST   distance in units to captured target

Strictly obeys CLAUDE.md HUD & Screen Overlay Rule:
- No opaque/dark drawfill panels or boxes in the middle of the viewport or behind overlays.
- Corner text overlays only (top-right stack via bm_topright_y) + perimeter-only edge pulse/vignette + thin open-center reticle chevrons.
Called from CSQC_UpdateView in csqc.main.qc across all bm_hud_style modes (0..4).
================
*/

float	CYST_MODE	= 128;
float	CYST_PROG	= 129;
float	CYST_FLASH	= 130;
float	CYST_KIND	= 131;
float	CYST_DIST	= 132;

float	CY_FLASH_DUR	= 0.90;

float	cy_flash_init;
float	cy_flash_prev;
float	cy_flash_until;

vector(float x, float y) CY_Vec2 =
{
	local vector v;

	v_x = x;
	v_y = y;
	v_z = 0;
	return v;
};

string(float kind) CY_TargetLabel =
{
	if (kind == 1)
		return "JOHN BIRD";
	if (kind == 2)
		return "MILKY GRENADE";
	return "PLAYER";
};

string(float tenths) CY_FormatTenths =
{
	local float rem, sec, dec;

	rem = floor (tenths + 0.5);
	if (rem < 0)
		rem = 0;
	sec = floor (rem / 10);
	dec = rem - sec * 10;
	return strcat (ftos (sec), ".", ftos (dec), "s");
};

// Draws a crisp thin diagonal line segment using stepped 2px pixels (no center fill)
void(float x0, float y0, float dx, float dy, float steps, float th, vector rgb, float a) CY_DiagSeg =
{
	local float i;

	i = 0;
	while (i < steps)
	{
		drawfill (CY_Vec2 (x0 + dx * i, y0 + dy * i), CY_Vec2 (th, th), rgb, a, 0);
		i = i + 1;
	}
};

// 0.90s dopamine lock-on surge: strobing green/white/gold perimeter flash, snapping corner brackets,
// and an open-center diamond/chevron lock-on reticle pulse (22..44px from crosshair, center 100% clear)
void(float w, float h, float rem) CY_DrawEdgeFlash =
{
	local float frac, age, sn, st, pulse, strobe, env, a, edge, glow, ins, arm, th, hi_a;
	local float cx, cy, snap, r, chev, d, tick;
	local vector col, gold_col, white_col, edge_col, chev_col;

	frac = bound (0, rem / CY_FLASH_DUR, 1);
	if (frac <= 0.01)
		return;
	age = 1 - frac;

	sn = sin (time * 28);
	st = sin (time * 42);
	pulse = 0.72 + 0.28 * sn;
	strobe = floor (time * 20);
	strobe = strobe - 3 * floor (strobe / 3);
	env = bound (0, frac * 1.35, 1);
	a = env * frac * pulse;

	col = '0.20 1.0 0.42';
	gold_col = '1.0 0.86 0.20';
	white_col = '0.88 1.0 0.90';

	if (strobe == 1 && age < 0.55)
		edge_col = gold_col;
	else if (strobe == 2 && age < 0.40)
		edge_col = white_col;
	else
		edge_col = col;

	edge = 3.0;
	glow = 8.0;

	// Strobing thin perimeter strips along all 4 outer screen edges
	drawfill ('0 0 0', CY_Vec2 (w, edge), edge_col, 0.90 * a, 0);
	drawfill (CY_Vec2 (0, h - edge), CY_Vec2 (w, edge), edge_col, 0.90 * a, 0);
	drawfill (CY_Vec2 (0, edge), CY_Vec2 (edge, h - edge * 2), edge_col, 0.90 * a, 0);
	drawfill (CY_Vec2 (w - edge, edge), CY_Vec2 (edge, h - edge * 2), edge_col, 0.90 * a, 0);

	// Soft neon-green inner perimeter halo (no center occlusion)
	drawfill (CY_Vec2 (0, edge), CY_Vec2 (w, glow), col, 0.18 * a, 0);
	drawfill (CY_Vec2 (0, h - edge - glow), CY_Vec2 (w, glow), col, 0.18 * a, 0);
	drawfill (CY_Vec2 (edge, edge + glow), CY_Vec2 (glow, h - (edge + glow) * 2), col, 0.18 * a, 0);
	drawfill (CY_Vec2 (w - edge - glow, edge + glow), CY_Vec2 (glow, h - (edge + glow) * 2), col, 0.18 * a, 0);

	// Expanding & snapping neon-green corner brackets with gold accent ticks
	snap = bound (0, age * 2.5, 1);
	snap = snap * (2 - snap);
	ins = 5 + 5 * (1 - snap);
	arm = 18 + 16 * snap;
	th = 2.5;

	// Top-left bracket
	drawfill (CY_Vec2 (ins, ins), CY_Vec2 (arm, th), col, 0.96 * a, 0);
	drawfill (CY_Vec2 (ins, ins), CY_Vec2 (th, arm), col, 0.96 * a, 0);
	// Top-right bracket
	drawfill (CY_Vec2 (w - ins - arm, ins), CY_Vec2 (arm, th), col, 0.96 * a, 0);
	drawfill (CY_Vec2 (w - ins - th, ins), CY_Vec2 (th, arm), col, 0.96 * a, 0);
	// Bottom-left bracket
	drawfill (CY_Vec2 (ins, h - ins - th), CY_Vec2 (arm, th), col, 0.96 * a, 0);
	drawfill (CY_Vec2 (ins, h - ins - arm), CY_Vec2 (th, arm), col, 0.96 * a, 0);
	// Bottom-right bracket
	drawfill (CY_Vec2 (w - ins - arm, h - ins - th), CY_Vec2 (arm, th), col, 0.96 * a, 0);
	drawfill (CY_Vec2 (w - ins - th, h - ins - arm), CY_Vec2 (th, arm), col, 0.96 * a, 0);

	hi_a = bound (0, (frac - 0.25) / 0.75, 1) * (0.70 + 0.25 * st);
	if (hi_a > 0.02)
	{
		drawfill (CY_Vec2 (ins + th + 1, ins + th + 1), CY_Vec2 (arm * 0.55, 1.5), gold_col, hi_a, 0);
		drawfill (CY_Vec2 (w - ins - th - 1 - arm * 0.55, ins + th + 1), CY_Vec2 (arm * 0.55, 1.5), gold_col, hi_a, 0);
		drawfill (CY_Vec2 (ins + th + 1, h - ins - th - 2.5), CY_Vec2 (arm * 0.55, 1.5), gold_col, hi_a, 0);
		drawfill (CY_Vec2 (w - ins - th - 1 - arm * 0.55, h - ins - th - 2.5), CY_Vec2 (arm * 0.55, 1.5), gold_col, hi_a, 0);
	}

	// Open-center diamond/chevron lock-on reticle pulse (22..44px from crosshair, center completely clear)
	cx = w * 0.5;
	cy = h * 0.5;
	r = 44 - 22 * snap + 1.5 * st * frac;
	chev = 8;
	chev_col = (strobe == 1) ? gold_col : col;

	// 4 diamond apex chevrons at top, bottom, left, right of the lock ring
	CY_DiagSeg (cx, cy - r, -1, 1, chev, 2.0, chev_col, 0.95 * a);
	CY_DiagSeg (cx, cy - r, 1, 1, chev, 2.0, chev_col, 0.95 * a);
	CY_DiagSeg (cx, cy + r, -1, -1, chev, 2.0, chev_col, 0.95 * a);
	CY_DiagSeg (cx, cy + r, 1, -1, chev, 2.0, chev_col, 0.95 * a);
	CY_DiagSeg (cx - r, cy, 1, -1, chev, 2.0, chev_col, 0.95 * a);
	CY_DiagSeg (cx - r, cy, 1, 1, chev, 2.0, chev_col, 0.95 * a);
	CY_DiagSeg (cx + r, cy, -1, -1, chev, 2.0, chev_col, 0.95 * a);
	CY_DiagSeg (cx + r, cy, -1, 1, chev, 2.0, chev_col, 0.95 * a);

	// 4 diagonal gold lock-on chevrons contracting inward outside the diamond
	d = (r + 5) * 0.7071;
	tick = 5;
	CY_DiagSeg (cx - d, cy - d, -1, -1, tick, 2.0, gold_col, 0.88 * a);
	CY_DiagSeg (cx + d, cy - d, 1, -1, tick, 2.0, gold_col, 0.88 * a);
	CY_DiagSeg (cx - d, cy + d, -1, 1, tick, 2.0, gold_col, 0.88 * a);
	CY_DiagSeg (cx + d, cy + d, 1, 1, tick, 2.0, gold_col, 0.88 * a);
};

// Subtle perimeter-only green vignette while victim is trapped in Cyrax net (mode 4)
void(float w, float h) CY_DrawTrappedVignette =
{
	local float sn, pulse, a, band_y, band_x;
	local vector col;

	sn = sin (time * 7);
	pulse = 0.5 + 0.5 * sn;
	a = 0.10 + 0.06 * pulse;
	col = '0.16 0.96 0.38';
	band_y = h * 0.035;
	band_x = w * 0.025;

	drawfill ('0 0 0', CY_Vec2 (w, band_y), col, a, 0);
	drawfill (CY_Vec2 (0, h - band_y), CY_Vec2 (w, band_y), col, a, 0);
	drawfill (CY_Vec2 (0, band_y), CY_Vec2 (band_x, h - band_y * 2), col, a, 0);
	drawfill (CY_Vec2 (w - band_x, band_y), CY_Vec2 (band_x, h - band_y * 2), col, a, 0);

	// Crisp 1.5px outer neon-green border accent
	drawfill ('0 0 0', CY_Vec2 (w, 1.5), col, 0.42 + 0.22 * pulse, 0);
	drawfill (CY_Vec2 (0, h - 1.5), CY_Vec2 (w, 1.5), col, 0.42 + 0.22 * pulse, 0);
	drawfill ('0 1.5 0', CY_Vec2 (1.5, h - 3), col, 0.42 + 0.22 * pulse, 0);
	drawfill (CY_Vec2 (w - 1.5, 1.5), CY_Vec2 (1.5, h - 3), col, 0.42 + 0.22 * pulse, 0);
};

void(float raw_w, float raw_h) CY_DrawHUD =
{
	local float w, h, hp, mode, prog, flash, kind, dist;
	local float rx, ry, row_step, pw, frac, sn, pulse, a, cyc, flash_rem, flash_a;
	local string targ, ts, lbl, col_code, banner;
	local vector bar_col;

	w = vid_conwidth;
	h = vid_conheight;
	if (w <= 0)
		w = raw_w;
	if (h <= 0)
		h = raw_h;
	if (w <= 0 || h <= 0)
		return;

	if (time < cy_flash_until - 1.5)
		cy_flash_until = 0;

	flash = getstati (CYST_FLASH);
	if (!cy_flash_init)
	{
		cy_flash_init = 1;
		cy_flash_prev = flash;
	}
	else if (flash > cy_flash_prev)
	{
		cy_flash_prev = flash;
		cy_flash_until = time + CY_FLASH_DUR;
	}
	else if (flash < cy_flash_prev)
	{
		cy_flash_prev = flash;
	}

	hp = getstati (STAT_HEALTH);
	if (hp <= 0)
	{
		cy_flash_until = 0;
		return;
	}

	flash_rem = cy_flash_until - time;
	if (flash_rem > 0)
		CY_DrawEdgeFlash (w, h, flash_rem);

	mode = getstati (CYST_MODE);
	kind = getstati (CYST_KIND);
	targ = CY_TargetLabel (kind);

	rx = w - 8;
	ry = (bm_topright_y > 8) ? bm_topright_y : 8;
	row_step = (BM_GetUIFont () > 0) ? 10.5 : 9;

	// Animated top-right capture callout during the 0.90s dopamine burst
	if (flash_rem > 0 && mode != 4)
	{
		cyc = floor (time * 16);
		cyc = cyc - 3 * floor (cyc / 3);
		if (cyc == 0)
			banner = strcat ("^2*** ^7CAUGHT ", targ, "! ^2***");
		else if (cyc == 1)
			banner = strcat ("^3*** ^x3f6CAUGHT ", targ, "! ^3***");
		else
			banner = strcat ("^7*** ^3CAUGHT ", targ, "! ^7***");
		flash_a = bound (0, flash_rem / 0.22, 1);
		BM_ShadowColorRight (rx, ry, banner, 5.4, flash_a);
		ry = ry + row_step + 1;
		bm_topright_y = ry;
	}

	if (mode <= 0)
		return;

	prog = getstati (CYST_PROG);
	dist = max (0, floor (getstati (CYST_DIST) + 0.5));

	if (mode == 1)
	{
		prog = bound (0, floor (prog + 0.5), 100);
		frac = prog / 100;
		if (prog >= 80)
		{
			col_code = "^2";
			bar_col = '0.22 1.0 0.42';
		}
		else if (prog >= 40)
		{
			col_code = "^x9f4";
			bar_col = '0.62 0.96 0.24';
		}
		else
		{
			col_code = "^3";
			bar_col = '1.0 0.72 0.16';
		}
		lbl = strcat (col_code, "CYRAX NET CHARGING ^7", ftos (prog), "%");
		BM_ShadowColorRight (rx, ry, lbl, 5, 0.94);

		// Sleek compact green/amber progress bar tucked directly under corner text (no dark box)
		pw = 78;
		drawfill (CY_Vec2 (rx - pw, ry + row_step - 1), CY_Vec2 (pw, 2.5), bar_col, 0.22, 0);
		if (frac > 0)
			drawfill (CY_Vec2 (rx - pw, ry + row_step - 1), CY_Vec2 (pw * frac, 2.5), bar_col, 0.95, 0);
		bm_topright_y = ry + row_step + 4;
		return;
	}

	ts = CY_FormatTenths (bound (0, prog, 300));

	if (mode == 2)
	{
		lbl = strcat ("^2NET CAPTURED [^7", targ, "^2] - PULLING (^3", ftos (dist), "u^2) [^7", ts, "^2]");
		BM_ShadowColorRight (rx, ry, lbl, 5, 0.94);
		bm_topright_y = ry + row_step;
		return;
	}

	if (mode == 3)
	{
		sn = sin (time * 12);
		pulse = 0.5 + 0.5 * sn;
		a = 0.72 + 0.28 * pulse;
		col_code = (pulse > 0.5) ? "^x4f6" : "^2";
		lbl = strcat (col_code, "TARGET LOCKED [^7", targ, col_code, "] - CLICK TO BONK LAUNCH! [^7", ts, col_code, "]");
		BM_ShadowColorRight (rx, ry, lbl, 5, a);
		bm_topright_y = ry + row_step;
		return;
	}

	if (mode == 4)
	{
		CY_DrawTrappedVignette (w, h);
		sn = sin (time * 10);
		pulse = 0.5 + 0.5 * sn;
		lbl = strcat ("^2TRAPPED IN CYRAX NET [^7", ts, "^2] - ^1AXE LOCKED");
		BM_ShadowColorRight (rx, ry, lbl, 5, 0.78 + 0.22 * pulse);
		bm_topright_y = ry + row_step;
	}
};
