/*
================
WINGED JOHN COMBAT HUD, CROSSHAIR & 1ST-PERSON VISOR (john_bird_hud.qc)

Reads stats 93..102 sent from progs.dat (bm_match.qc BM_Stats):
	93 BMST_JB_ACTIVE   0=off, 1=3rd-person flight, 2=1st-person crown view
	94 BMST_JB_VARIANT  1=Unified Winged John
	95 BMST_JB_COMBAT   bitmask: 1=Hold-to-Combat, 2=primary (M1), 4=alt/match (M3/R), 16=SHIFT boost
	96 BMST_JB_STATUS   bitmask: 1=sticky-slowed, 2=burning, 4=bird low-HP (<=200); bits 1&2 work on foot too
	97 BMST_JB_BOOST    0..100 boost gauge
	98 BMST_JB_HP       0..500 bird HP
	99 BMST_JB_HIT      integer counter incremented on each landed hit
	100 BMST_JB_AMMO    0..8 hairspray cans remaining
	101 BMST_JB_AMMOPROG 0..100 restock progress for next can
	102 BMST_JB_SPEED   flight airspeed u/s

Called from CSQC_UpdateView in csqc.main.qc across all bm_hud_style modes (0..4).
================
*/

float	BMST_JB_ACTIVE		= 93;
float	BMST_JB_VARIANT		= 94;
float	BMST_JB_COMBAT		= 95;
float	BMST_JB_STATUS		= 96;
float	BMST_JB_BOOST		= 97;
float	BMST_JB_HP			= 98;
float	BMST_JB_HIT			= 99;
float	BMST_JB_AMMO		= 100;
float	BMST_JB_AMMOPROG	= 101;
float	BMST_JB_SPEED		= 102;

float	JB_HUD_MAX_AMMO		= 12;
float	JB_HUD_MAX_HP		= 140;
float	JB_HUD_LOW_HP		= 60;

float	jbh_prev_active;
float	jbh_enter_time;
float	jbh_prev_hit;
float	jbh_hit_until;

vector(float x, float y) JBH_Vec2 =
{
	local vector v;

	v_x = x;
	v_y = y;
	v_z = 0;
	return v;
};

void(vector pos, vector sz, vector bg, float bg_a, vector bd, float bd_a) JBH_Box =
{
	local float x, y, w, h;

	x = pos_x;
	y = pos_y;
	w = sz_x;
	h = sz_y;
	if (w < 2 || h < 2)
		return;

	if (bg_a > 0)
		drawfill(JBH_Vec2(x, y), JBH_Vec2(w, h), bg, bg_a, 0);
	if (bd_a > 0)
	{
		drawfill(JBH_Vec2(x, y), JBH_Vec2(w, 1), bd, bd_a, 0);
		drawfill(JBH_Vec2(x, y + h - 1), JBH_Vec2(w, 1), bd, bd_a, 0);
		if (h > 2)
		{
			drawfill(JBH_Vec2(x, y + 1), JBH_Vec2(1, h - 2), bd, bd_a, 0);
			drawfill(JBH_Vec2(x + w - 1, y + 1), JBH_Vec2(1, h - 2), bd, bd_a, 0);
		}
	}
};

float() JBH_TopLeftY =
{
	local float hs;

	hs = cvar("bm_hud_style");
	if (hs == 2)
		return 62;
	if (hs == 3)
		return 24;
	return 34;
};

void(float x, float y, string s, float sz, float a) JBH_ShadowLeft =
{
	local vector sc;
	local string plain;

	sc = JBH_Vec2(sz, sz);
	plain = strdecolorize(s);
	drawstring(JBH_Vec2(x + 0.7, y + 0.7), plain, sc, '0 0 0', 0.85 * a, 0);
	drawcolorcodedstring(JBH_Vec2(x, y), s, sc, a, 0);
};

void(float rx, float y, string s, float sz, float a) JBH_ShadowRight =
{
	local float wd;

	wd = stringwidth(s, TRUE, JBH_Vec2(sz, sz));
	JBH_ShadowLeft(rx - wd, y, s, sz, a);
};

void(float cx, float y, string s, float sz, float a) JBH_Centered =
{
	local float wd;

	wd = stringwidth(s, TRUE, JBH_Vec2(sz, sz));
	JBH_ShadowLeft(cx - wd * 0.5, y, s, sz, a);
};

void(float cx, float y, string s, float sz, vector rgb, float a) JBH_PlainCentered =
{
	local float wd;
	local vector sc;

	sc = JBH_Vec2(sz, sz);
	wd = stringwidth(s, FALSE, sc);
	drawstring(JBH_Vec2(cx - wd * 0.5 + 0.6, y + 0.6), s, sc, '0 0 0', 0.72 * a, 0);
	drawstring(JBH_Vec2(cx - wd * 0.5, y), s, sc, rgb, a, 0);
};

// Draws a crisp stepped diagonal slash from (x0,y0) by step (dx,dy) for len pixels
void(float x0, float y0, float dx, float dy, float len, float thick, vector rgb, float a) JBH_DiagTick =
{
	local float i;

	i = 0;
	while (i < len)
	{
		drawfill(JBH_Vec2(x0 + dx * i, y0 + dy * i), JBH_Vec2(thick, thick), rgb, a, 0);
		i = i + 1;
	}
};

/*
================
JBH_DrawCrosshair
Custom aerosol-spray / flame / mega-bangs combat reticle while piloting Winged John.
Reacts dynamically to firing (M1), match/alt fire (M3/R), and hit confirms.
================
*/
void(float w, float h, float jb_var, float combat, float ammo) JBH_DrawCrosshair =
{
	local float cx, cy, gap, arm, th, firing, hit_rem, hit_frac, kick;
	local vector col, shd;

	cx = w * 0.5;
	cy = h * 0.5;
	firing = (combat & 2);
	gap = firing ? 3.5 : 2.5;
	arm = firing ? 4.0 : 3.5;
	th = 1.0;

	// Compact crisp open-center red crosshair (~12u total, NO center dot)
	col = (ammo <= 0) ? '1.0 0.52 0.16' : '1.0 0.18 0.14';
	shd = '0.06 0.01 0.01';

	// Thin dark shadow behind the 4 arms so it stays readable over bright sky and dark concrete
	drawfill(JBH_Vec2(cx - gap - arm - 0.5, cy - th * 0.5 - 0.5), JBH_Vec2(arm + 1.0, th + 1.0), shd, 0.72, 0);
	drawfill(JBH_Vec2(cx + gap - 0.5, cy - th * 0.5 - 0.5), JBH_Vec2(arm + 1.0, th + 1.0), shd, 0.72, 0);
	drawfill(JBH_Vec2(cx - th * 0.5 - 0.5, cy - gap - arm - 0.5), JBH_Vec2(th + 1.0, arm + 1.0), shd, 0.72, 0);
	drawfill(JBH_Vec2(cx - th * 0.5 - 0.5, cy + gap - 0.5), JBH_Vec2(th + 1.0, arm + 1.0), shd, 0.72, 0);

	// 4 crisp red crosshair arms (center stays completely open)
	drawfill(JBH_Vec2(cx - gap - arm, cy - th * 0.5), JBH_Vec2(arm, th), col, 0.96, 0);
	drawfill(JBH_Vec2(cx + gap, cy - th * 0.5), JBH_Vec2(arm, th), col, 0.96, 0);
	drawfill(JBH_Vec2(cx - th * 0.5, cy - gap - arm), JBH_Vec2(th, arm), col, 0.96, 0);
	drawfill(JBH_Vec2(cx - th * 0.5, cy + gap), JBH_Vec2(th, arm), col, 0.96, 0);

	// Compact hit-confirm gold X-marker burst (0.22s whenever BMST_JB_HIT increments)
	if (time < jbh_hit_until)
	{
		hit_rem = (jbh_hit_until - time) / 0.22;
		hit_frac = 1 - hit_rem;
		kick = 2.5 + hit_frac * 3.0;
		JBH_DiagTick(cx - kick + 0.5, cy - kick + 0.5, -1, -1, 3, 1.0, '0 0 0', 0.75 * hit_rem);
		JBH_DiagTick(cx + kick + 0.5, cy - kick + 0.5, 1, -1, 3, 1.0, '0 0 0', 0.75 * hit_rem);
		JBH_DiagTick(cx - kick + 0.5, cy + kick + 0.5, -1, 1, 3, 1.0, '0 0 0', 0.75 * hit_rem);
		JBH_DiagTick(cx + kick + 0.5, cy + kick + 0.5, 1, 1, 3, 1.0, '0 0 0', 0.75 * hit_rem);
		JBH_DiagTick(cx - kick, cy - kick, -1, -1, 3, 1.0, '1.0 0.90 0.28', 0.98 * hit_rem);
		JBH_DiagTick(cx + kick, cy - kick, 1, -1, 3, 1.0, '1.0 0.90 0.28', 0.98 * hit_rem);
		JBH_DiagTick(cx - kick, cy + kick, -1, 1, 3, 1.0, '1.0 0.90 0.28', 0.98 * hit_rem);
		JBH_DiagTick(cx + kick, cy + kick, 1, 1, 3, 1.0, '1.0 0.90 0.28', 0.98 * hit_rem);
	}
	// NOZZLE DRY / LOW AMMO now sit on the bottom-right can rack (JBH_DrawCanRack), keeping the crosshair area clear
};

/*
================
JBH_DrawCanRack
Compact 12-can Aqua Net aerosol rack in bottom-right showing finite ammo + recharge bar (no dark box).
================
*/
void(float w, float h, float ammo, float ammoprog, float is_1p) JBH_DrawCanRack =
{
	local float rx, ry, rw, rh, i, cx, cy, cw, ch, filled, sn, pulse, flav;
	local vector can_col, band_col, cap_col;
	local string lbl;

	rw = 110;
	rh = 33;
	rx = w - rw - 8;
	ry = BM_CornerBottomY(h) - rh;

	sn = sin(time * 11);
	pulse = 0.5 + 0.5 * sn;

	if (ammo <= 0)
		lbl = strcat("^1EMPTY 0/", ftos(JB_HUD_MAX_AMMO));
	else if (ammo <= 2)
		lbl = strcat("^3CANS ", ftos(ammo), "/", ftos(JB_HUD_MAX_AMMO));
	else
		lbl = strcat("^7CANS ^5", ftos(ammo), "/", ftos(JB_HUD_MAX_AMMO));
	JBH_ShadowRight(w - 8, ry, lbl, 5, (ammo <= 0) ? (0.60 + 0.40 * pulse) : 0.98);
	// out-of-ammo warning stacked just above the rack (was centred under the crosshair)
	if (ammo <= 0)
		JBH_ShadowRight(w - 8, ry - 8, "^1NOZZLE DRY (0/12)", 5, 0.92);
	else if (ammo <= 2)
		JBH_ShadowRight(w - 8, ry - 8, "^3LOW AMMO", 4.8, 0.85);

	// Draw 12 sleek slim Aqua Net spray cans cycling the 4 iconic flavors
	cw = 5.5;
	ch = 15;
	i = 0;
	while (i < JB_HUD_MAX_AMMO)
	{
		cx = rx + 8 + i * 8.0;
		cy = ry + 10;
		filled = (i < ammo);
		if (filled)
		{
			flav = i - 4 * floor(i / 4);
			if (flav == 0)
			{
				// White diamond + hot pink label
				can_col = '0.94 0.95 0.97';
				band_col = '0.92 0.36 0.68';
				cap_col = '0.98 0.98 1.0';
			}
			else if (flav == 1)
			{
				// 80s Navy polka + promo gold/pink band
				can_col = '0.16 0.28 0.58';
				band_col = '1.0 0.80 0.16';
				cap_col = '0.96 0.96 0.98';
			}
			else if (flav == 2)
			{
				// Magenta ultimate hold + cream label
				can_col = '0.84 0.18 0.44';
				band_col = '0.98 0.92 0.78';
				cap_col = '0.98 0.84 0.72';
			}
			else
			{
				// Metallic sky-blue + chrome dome & black spray nozzle
				can_col = '0.26 0.74 0.94';
				band_col = '0.92 0.96 1.0';
				cap_col = '0.72 0.76 0.82';
			}
			// Tapered spray nozzle + collar + cylinder body + label band + sheen
			drawfill(JBH_Vec2(cx + 2.0, cy), JBH_Vec2(1.5, 1.5), '0.12 0.14 0.18', 0.95, 0);
			drawfill(JBH_Vec2(cx + 1.0, cy + 1.5), JBH_Vec2(cw - 2.0, 1.5), cap_col, 0.95, 0);
			drawfill(JBH_Vec2(cx, cy + 3), JBH_Vec2(cw, ch - 3), can_col, 0.96, 0);
			drawfill(JBH_Vec2(cx, cy + 5.5), JBH_Vec2(cw, 4), band_col, 0.96, 0);
			drawfill(JBH_Vec2(cx + 1.0, cy + 3), JBH_Vec2(1.0, ch - 4), '1 1 1', 0.42, 0);
		}
		else
		{
			// Quiet spent silhouette outline (no dark box fill)
			drawfill(JBH_Vec2(cx + 1.0, cy + 1.5), JBH_Vec2(cw - 2.0, 1.5), '0.45 0.55 0.68', 0.28, 0);
			JBH_Box(JBH_Vec2(cx, cy + 3), JBH_Vec2(cw, ch - 3), '0 0 0', 0, '0.48 0.62 0.76', 0.35);
		}
		i = i + 1;
	}

	if (ammo < JB_HUD_MAX_AMMO)
	{
		drawfill(JBH_Vec2(rx + 8, ry + rh - 4), JBH_Vec2(rw - 16, 2), '0 0 0', 0.45, 0);
		if (ammoprog > 0)
			drawfill(JBH_Vec2(rx + 8, ry + rh - 4), JBH_Vec2((rw - 16) * bound(0, ammoprog / 100, 1), 2), '0.45 0.95 1.0', 0.95, 0);
	}
};

/*
================
JBH_DrawFirstPersonJohnHUD
Minimal, clean 1st-person aviation readout tucked in bottom-left with drop shadow (no dark box).
================
*/
void(float w, float h, float combat, float status, float jb_hp, float ammo, float spd) JBH_DrawFirstPersonJohnHUD =
{
	local float px, py, bw, hp_frac;
	local vector hp_col;
	local string hp_lbl;

	bw = 96;
	px = JP_IsVisible() ? 36 : 10;
	py = BM_CornerBottomY(h) - 16;

	hp_frac = bound(0, jb_hp / JB_HUD_MAX_HP, 1);
	if (jb_hp <= JB_HUD_LOW_HP || (status & 4))
		hp_col = '1.0 0.28 0.22';
	else if (jb_hp <= 100)
		hp_col = '1.0 0.82 0.24';
	else
		hp_col = '0.34 0.96 0.54';

	hp_lbl = strcat("^7BIRD ", ftos(jb_hp), "   ^5", ftos(spd), "u/s");
	JBH_ShadowLeft(px, py, hp_lbl, 4.8, 0.98);
	drawfill(JBH_Vec2(px, py + 8), JBH_Vec2(bw, 2.5), '0 0 0', 0.45, 0);
	if (hp_frac > 0)
		drawfill(JBH_Vec2(px, py + 8), JBH_Vec2(bw * hp_frac, 2.5), hp_col, 0.96, 0);
};

/*
================
JBH_DrawTopSwitcher
Compact top-left text overlay showing bird HP, airspeed, can ammo, and smoking warning (no dark box).
================
*/
void(float w, float h, float jb_active, float jb_var, float combat, float status, float jb_hp, float ammo, float spd) JBH_DrawTopSwitcher =
{
	local float x0, y0, hp_frac, sn;
	local string s, hp_tag;
	local vector hp_col;

	x0 = 10;
	y0 = JBH_TopLeftY() + 11;

	hp_frac = bound(0, jb_hp / JB_HUD_MAX_HP, 1);
	if (jb_hp <= JB_HUD_LOW_HP || (status & 4))
	{
		hp_col = '1.0 0.26 0.20';
		hp_tag = "^1";
	}
	else if (jb_hp <= 100)
	{
		hp_col = '1.0 0.80 0.22';
		hp_tag = "^3";
	}
	else
	{
		hp_col = '0.28 0.94 0.48';
		hp_tag = "^2";
	}

	s = strcat(hp_tag, "JOHN ", ftos(jb_hp), "  ^5", ftos(spd), "u/s");
	s = strcat(s, "  ", (ammo <= 0) ? "^10/12" : ((ammo <= 2) ? strcat("^3", ftos(ammo), "/12") : strcat("^5", ftos(ammo), "/12")));
	if (combat & 7)
		s = strcat(s, " ^1ATK");
	JBH_ShadowLeft(x0, y0, s, 5, 0.96);

	drawfill(JBH_Vec2(x0, y0 + 8), JBH_Vec2(72, 2), '0 0 0', 0.45, 0);
	if (hp_frac > 0)
		drawfill(JBH_Vec2(x0, y0 + 8), JBH_Vec2(72 * hp_frac, 2), hp_col, 0.94, 0);

	// Low-HP smoking alert directly under top-left telemetry
	if (jb_hp > 0 && (jb_hp <= JB_HUD_LOW_HP || (status & 4)))
	{
		sn = sin(time * 10);
		sn = 0.65 + 0.35 * sn;
		JBH_ShadowLeft(x0, y0 + 13, "^1! WINGED JOHN SMOKING !", 5, sn);
	}
};

/*
================
JBH_DrawControlsStrip
Bright drop-shadowed keybind reference in the top-left corner, auto-fading after 4s of flight.
================
*/
void(float w, float h, float jb_active) JBH_DrawControlsStrip =
{
	local float px, py, age, a;
	local string s;

	if (showscores)
		return;

	age = time - jbh_enter_time;
	if (age >= 5.5)
		return;
	a = (age <= 4.0) ? 1.0 : bound(0, (5.5 - age) / 1.5, 1.0);

	px = 10;
	py = JBH_TopLeftY();
	if (jb_active == 2)
		s = "^3CLICK^7 Shoot  ^3MOUSE^7 Carve Speed  ^3K^7 Cam(^51P^7)  ^3P/H^7 Exit";
	else
		s = "^3CLICK^7 Shoot  ^3MOUSE^7 Carve Speed  ^3K^7 Cam(^53P^7)  ^3P/H^7 Exit";

	JBH_ShadowLeft(px, py, s, 6, a);
};

/*
================
JBH_DrawStatusFeedback
Sticky-slowed / Burning / Turbo-boost screen feedback in top-right corner (no dark boxes across screen).
Sticky & Burning also render on foot and in vehicles when hit by Winged John's hairspray or fire!
================
*/
void(float w, float h, float jb_active, float combat, float status) JBH_DrawStatusFeedback =
{
	local float sn, fl, rx, ry, i, sy, lx, lw, s1, s2;

	s1 = sin(time * 9);
	s2 = sin(time * 16);
	sn = 0.5 + 0.5 * s1;
	fl = 0.5 + 0.5 * s2;

	// Subtle cyan speed-lines at outer edges when SHIFT boosting
	if (jb_active > 0 && (combat & 16))
	{
		i = 0;
		while (i < 6)
		{
			s1 = sin(time * 24 + i * 2.1);
			s2 = sin(time * 30 + i * 1.7);
			sy = h * (0.14 + 0.14 * i) + s1 * 6;
			lw = 14 + 12 * (0.5 + 0.5 * s2);
			lx = (time * 90 + i * 17) - floor((time * 90 + i * 17) / 18) * 18;
			drawfill(JBH_Vec2(4 + lx * 0.4, sy), JBH_Vec2(lw, 1), '0.55 0.94 1.0', 0.42, 0);
			drawfill(JBH_Vec2(w - 4 - lx * 0.4 - lw, sy), JBH_Vec2(lw, 1), '0.55 0.94 1.0', 0.42, 0);
			i = i + 1;
		}
	}

	rx = w - 8;
	ry = (bm_topright_y > 8) ? bm_topright_y : 8;

	// Sticky-slowed by hairspray (top-right text only; the pulse that tinted full-width edge strips now pulses the text)
	if (status & 1)
	{
		JBH_ShadowRight(rx, ry, "^5STICKY HAIRSPRAY (SLOWED)", 5, 0.80 + 0.15 * sn);
		ry = ry + 9;
	}

	// Burning from match-lit hairspray fire (top-right text only; flickers instead of full-height edge strips)
	if (status & 2)
	{
		JBH_ShadowRight(rx, ry, "^1HAIR ON FIRE (BURNING)", 5, 0.80 + 0.18 * fl);
		ry = ry + 9;
	}
	bm_topright_y = ry;
};

/*
================
JB_DrawHUD
Entry point called every frame from CSQC_UpdateView when not in menu/intro/intermission/RobHead.
================
*/
void(float raw_w, float raw_h) JB_DrawHUD =
{
	local float w, h, jb_active, jb_var, combat, status, jb_hp, hit_cnt, ammo, ammoprog, spd, hp;

	w = vid_conwidth;
	h = vid_conheight;
	if (w <= 0)
		w = raw_w;
	if (h <= 0)
		h = raw_h;
	if (w <= 0 || h <= 0)
		return;

	hp = getstati(STAT_HEALTH);
	if (hp <= 0)
	{
		jbh_prev_active = 0;
		return;
	}

	jb_active = getstati(BMST_JB_ACTIVE);
	jb_var = getstati(BMST_JB_VARIANT);
	combat = getstati(BMST_JB_COMBAT);
	status = getstati(BMST_JB_STATUS);
	jb_hp = getstati(BMST_JB_HP);
	hit_cnt = getstati(BMST_JB_HIT);
	ammo = getstati(BMST_JB_AMMO);
	ammoprog = getstati(BMST_JB_AMMOPROG);
	spd = getstati(BMST_JB_SPEED);

	if (jb_active > 0)
	{
		if (jbh_prev_active == 0)
		{
			jbh_enter_time = time;
			jbh_prev_hit = hit_cnt;
			jbh_hit_until = 0;
		}
		else if (hit_cnt != jbh_prev_hit)
		{
			jbh_prev_hit = hit_cnt;
			jbh_hit_until = time + 0.22;
		}
		jbh_prev_active = jb_active;

		if (jb_var < 1 || jb_var > 3)
			jb_var = 1;

		if (jb_active == 2)
			JBH_DrawFirstPersonJohnHUD(w, h, combat, status, jb_hp, ammo, spd);
		else
			JBH_DrawTopSwitcher(w, h, jb_active, jb_var, combat, status, jb_hp, ammo, spd);

		JBH_DrawCrosshair(w, h, jb_var, combat, ammo);
		JBH_DrawCanRack(w, h, ammo, ammoprog, (jb_active == 2));
		JBH_DrawControlsStrip(w, h, jb_active);
	}
	else
	{
		jbh_prev_active = 0;
	}

	if ((status & 3) || (jb_active > 0 && (combat & 16)))
		JBH_DrawStatusFeedback(w, h, jb_active, combat, status);
};
