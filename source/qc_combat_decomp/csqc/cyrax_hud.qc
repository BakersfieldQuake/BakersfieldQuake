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
- Corner text overlays only (top-right stack via bm_topright_y) + perimeter-only edge pulse/vignette.
Called from CSQC_UpdateView in csqc.main.qc across all bm_hud_style modes (0..4).
================
*/

float	CYST_MODE	= 128;
float	CYST_PROG	= 129;
float	CYST_FLASH	= 130;
float	CYST_KIND	= 131;
float	CYST_DIST	= 132;

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

// 0.65s neon-green perimeter edge pulse flash + corner brackets (keeps center 100% clear)
void(float w, float h, float rem) CY_DrawEdgeFlash =
{
	local float frac, sn, pulse, env, a, edge, glow, ins, arm, th, hi_a;
	local vector col, hi_col;

	frac = bound (0, rem / 0.65, 1);
	if (frac <= 0.01)
		return;

	sn = sin (time * 28);
	pulse = 0.72 + 0.28 * sn;
	env = bound (0, frac * 1.25, 1);
	a = env * frac * pulse;

	col = '0.20 1.0 0.42';
	hi_col = '0.72 1.0 0.80';
	edge = 2.5;
	glow = 7.0;

	// Thin glowing perimeter strips along all 4 outer screen edges
	drawfill ('0 0 0', CY_Vec2 (w, edge), col, 0.85 * a, 0);
	drawfill (CY_Vec2 (0, h - edge), CY_Vec2 (w, edge), col, 0.85 * a, 0);
	drawfill (CY_Vec2 (0, edge), CY_Vec2 (edge, h - edge * 2), col, 0.85 * a, 0);
	drawfill (CY_Vec2 (w - edge, edge), CY_Vec2 (edge, h - edge * 2), col, 0.85 * a, 0);

	// Soft neon-green inner perimeter halo (no center occlusion)
	drawfill (CY_Vec2 (0, edge), CY_Vec2 (w, glow), col, 0.16 * a, 0);
	drawfill (CY_Vec2 (0, h - edge - glow), CY_Vec2 (w, glow), col, 0.16 * a, 0);
	drawfill (CY_Vec2 (edge, edge + glow), CY_Vec2 (glow, h - (edge + glow) * 2), col, 0.16 * a, 0);
	drawfill (CY_Vec2 (w - edge - glow, edge + glow), CY_Vec2 (glow, h - (edge + glow) * 2), col, 0.16 * a, 0);

	// Glowing corner brackets that snap inward on capture
	ins = 6;
	arm = 20 + (1 - frac) * 10;
	th = 2.5;

	// Top-left bracket
	drawfill (CY_Vec2 (ins, ins), CY_Vec2 (arm, th), col, 0.95 * a, 0);
	drawfill (CY_Vec2 (ins, ins), CY_Vec2 (th, arm), col, 0.95 * a, 0);
	// Top-right bracket
	drawfill (CY_Vec2 (w - ins - arm, ins), CY_Vec2 (arm, th), col, 0.95 * a, 0);
	drawfill (CY_Vec2 (w - ins - th, ins), CY_Vec2 (th, arm), col, 0.95 * a, 0);
	// Bottom-left bracket
	drawfill (CY_Vec2 (ins, h - ins - th), CY_Vec2 (arm, th), col, 0.95 * a, 0);
	drawfill (CY_Vec2 (ins, h - ins - arm), CY_Vec2 (th, arm), col, 0.95 * a, 0);
	// Bottom-right bracket
	drawfill (CY_Vec2 (w - ins - arm, h - ins - th), CY_Vec2 (arm, th), col, 0.95 * a, 0);
	drawfill (CY_Vec2 (w - ins - th, h - ins - arm), CY_Vec2 (th, arm), col, 0.95 * a, 0);

	hi_a = bound (0, (frac - 0.45) / 0.55, 1) * 0.80;
	if (hi_a > 0.02)
	{
		drawfill (CY_Vec2 (ins + th, ins + th), CY_Vec2 (arm * 0.65, 1), hi_col, hi_a, 0);
		drawfill (CY_Vec2 (w - ins - th - arm * 0.65, ins + th), CY_Vec2 (arm * 0.65, 1), hi_col, hi_a, 0);
		drawfill (CY_Vec2 (ins + th, h - ins - th - 1), CY_Vec2 (arm * 0.65, 1), hi_col, hi_a, 0);
		drawfill (CY_Vec2 (w - ins - th - arm * 0.65, h - ins - th - 1), CY_Vec2 (arm * 0.65, 1), hi_col, hi_a, 0);
	}
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
	local float rx, ry, row_step, pw, frac, sn, pulse, a;
	local string targ, ts, lbl, col_code;
	local vector bar_col;

	w = vid_conwidth;
	h = vid_conheight;
	if (w <= 0)
		w = raw_w;
	if (h <= 0)
		h = raw_h;
	if (w <= 0 || h <= 0)
		return;

	if (time < cy_flash_until - 1.0)
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
		cy_flash_until = time + 0.65;
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

	if (time < cy_flash_until)
		CY_DrawEdgeFlash (w, h, cy_flash_until - time);

	mode = getstati (CYST_MODE);
	if (mode <= 0)
		return;

	prog = getstati (CYST_PROG);
	kind = getstati (CYST_KIND);
	dist = max (0, floor (getstati (CYST_DIST) + 0.5));

	rx = w - 8;
	ry = (bm_topright_y > 8) ? bm_topright_y : 8;
	row_step = (BM_GetUIFont () > 0) ? 10.5 : 9;

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

	targ = CY_TargetLabel (kind);
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
