/*
================
HUD STYLE 1: "DYNAMIC ISLAND" (Apple / Frosted Glass Pill)

Ultra-sleek frosted-glass capsules with crisp 1px ice-cyan top highlights,
mint/cyan/gold/coral accents, centered Quake head with pulsing status frame
and live mood caption, zero gun menu, and context-aware top Dynamic Island.
================
*/

/*
================
S1_Vec2
Builds a 2D HUD vector with z zeroed.
================
*/
vector(float x, float y) S1_Vec2 =
{
	local vector v;

	v_x = x;
	v_y = y;
	v_z = 0;
	return v;
};

/*
================
S1_DrawShadowText / S1_DrawRightShadowText
Crisp drop-shadowed text helpers for large frosted-glass numerals.
================
*/
void(vector pos, string s, vector sc, vector rgb, float a) S1_DrawShadowText =
{
	local vector usc;

	usc = BM_UIScaleVec(sc);
	drawstring(pos + '1 1 0', s, usc, '0 0 0', 0.72 * a, 0);
	drawstring(pos, s, usc, rgb, a, 0);
};

void(vector right_pos, string s, vector sc, vector rgb, float a) S1_DrawRightShadowText =
{
	HUD_DrawRightText(right_pos + '1 1 0', s, sc, '0 0 0', 0.72 * a);
	HUD_DrawRightText(right_pos, s, sc, rgb, a);
};

/*
================
S1_DrawGlassPill
Draws a rounded-corner frosted-glass capsule with a crisp 1px top highlight,
subtle inner upper sheen, and translucent glass border.
================
*/
void(vector pos, vector sz, vector bg, float bg_a, vector hi, float hi_a, vector bd, float bd_a) S1_DrawGlassPill =
{
	local float x, y, pw, ph, body_y, body_h, sheen_h;

	x = pos_x;
	y = pos_y;
	pw = sz_x;
	ph = sz_y;
	if (pw < 12 || ph < 8)
		return;

	// Rounded capsule body (3px corner bevels)
	if (bg_a > 0)
	{
		drawfill(S1_Vec2(x + 3, y), S1_Vec2(pw - 6, 1), bg, bg_a, 0);
		drawfill(S1_Vec2(x + 2, y + 1), S1_Vec2(pw - 4, 1), bg, bg_a, 0);
		drawfill(S1_Vec2(x + 1, y + 2), S1_Vec2(pw - 2, 1), bg, bg_a, 0);
		body_y = y + 3;
		body_h = ph - 6;
		if (body_h > 0)
			drawfill(S1_Vec2(x, body_y), S1_Vec2(pw, body_h), bg, bg_a, 0);
		drawfill(S1_Vec2(x + 1, y + ph - 3), S1_Vec2(pw - 2, 1), bg, bg_a, 0);
		drawfill(S1_Vec2(x + 2, y + ph - 2), S1_Vec2(pw - 4, 1), bg, bg_a, 0);
		drawfill(S1_Vec2(x + 3, y + ph - 1), S1_Vec2(pw - 6, 1), bg, bg_a, 0);

		// Frosted upper glass sheen
		sheen_h = floor(ph * 0.36);
		if (sheen_h > 2)
		{
			drawfill(S1_Vec2(x + 2, y + 2), S1_Vec2(pw - 4, 1), '0.78 0.94 1.0', bg_a * 0.08, 0);
			drawfill(S1_Vec2(x + 1, y + 3), S1_Vec2(pw - 2, sheen_h - 2), '0.78 0.94 1.0', bg_a * 0.05, 0);
		}
	}

	// Crisp 1px top ice-cyan highlight
	if (hi_a > 0)
	{
		drawfill(S1_Vec2(x + 3, y), S1_Vec2(pw - 6, 1), hi, hi_a, 0);
		drawfill(S1_Vec2(x + 2, y + 1), S1_Vec2(2, 1), hi, hi_a * 0.65, 0);
		drawfill(S1_Vec2(x + pw - 4, y + 1), S1_Vec2(2, 1), hi, hi_a * 0.65, 0);
	}

	// Subtle side & bottom glass rim
	if (bd_a > 0)
	{
		drawfill(S1_Vec2(x + 1, y + 2), S1_Vec2(1, 1), bd, bd_a * 0.8, 0);
		drawfill(S1_Vec2(x + pw - 2, y + 2), S1_Vec2(1, 1), bd, bd_a * 0.8, 0);
		if (ph > 6)
		{
			drawfill(S1_Vec2(x, y + 3), S1_Vec2(1, ph - 6), bd, bd_a * 0.65, 0);
			drawfill(S1_Vec2(x + pw - 1, y + 3), S1_Vec2(1, ph - 6), bd, bd_a * 0.65, 0);
		}
		drawfill(S1_Vec2(x + 1, y + ph - 3), S1_Vec2(1, 1), bd, bd_a * 0.5, 0);
		drawfill(S1_Vec2(x + pw - 2, y + ph - 3), S1_Vec2(1, 1), bd, bd_a * 0.5, 0);
		drawfill(S1_Vec2(x + 2, y + ph - 2), S1_Vec2(2, 1), bd, bd_a * 0.5, 0);
		drawfill(S1_Vec2(x + pw - 4, y + ph - 2), S1_Vec2(2, 1), bd, bd_a * 0.5, 0);
		drawfill(S1_Vec2(x + 3, y + ph - 1), S1_Vec2(pw - 6, 1), bd, bd_a * 0.65, 0);
	}
};

/*
================
S1_GetMoodCaption
Short punchy mood caption under the Quake head.
================
*/
string(float hp, float armor, float it_flags, float active_ammo, float is_melee, float is_leader) S1_GetMoodCaption =
{
	if (hp <= 0)
		return "FLATLINED";
	if ((it_flags & IT_INVULNERABILITY) && (it_flags & IT_INVISIBILITY))
		return "GHOST GOD";
	if (it_flags & IT_INVULNERABILITY)
		return "GOD MODE";
	if (it_flags & IT_QUAD)
		return "4X JUICE";
	if (it_flags & IT_INVISIBILITY)
		return "INCOGNITO";
	if (it_flags & IT_SUIT)
		return "HAZMAT OK";
	if (hp < 20)
		return "CALL 911";
	if (hp < 45)
		return "SWEATING";
	if (active_ammo <= 0 && !is_melee)
		return "NO AMMO LOL";
	if (is_leader)
		return "MAIN CHAR";
	if (hp >= 100 && armor >= 100)
		return "VIBING";
	if (hp >= 80)
		return "CHILLIN";
	return "LOCKED IN";
};

/*
================
S1_ShortWeaponName
Returns active weapon name trimmed only if needed to fit beside big ammo readout.
================
*/
string(float slot, float active_weap) S1_ShortWeaponName =
{
	if (slot != 16 && slot != 18)
	{
		if (active_weap == IT_GRENADE_LAUNCHER)
			return "GRENADE LNCH";
		if (active_weap == IT_ROCKET_LAUNCHER)
			return "ROCKET LNCH";
		if (active_weap == IT_SUPER_SHOTGUN)
			return "PUMP SHOTGUN";
		if (active_weap == IT_NAILGUN)
			return "CHAINGUN";
		if (active_weap == IT_SUPER_NAILGUN)
			return "SUPER NAILER";
	}
	return HUD_GetWeaponName(slot, active_weap);
};

/*
================
S1_DrawReserveChip
Draws a tiny color-coded reserve dot + count inside the right wing.
================
*/
void(float x, float y, float val, vector dot_col, float sc_sz, float a) S1_DrawReserveChip =
{
	local float chip_a, num_a;
	local string s;
	local vector sc;

	chip_a = a * 0.92;
	num_a = a * 0.90;
	if (val <= 0)
	{
		chip_a = a * 0.30;
		num_a = a * 0.38;
	}

	drawfill(S1_Vec2(x, y + 1), S1_Vec2(3, 3), dot_col, chip_a, 0);
	drawfill(S1_Vec2(x + 1, y + 2), S1_Vec2(1, 1), '1 1 1', chip_a * 0.7, 0);

	s = ftos(val);
	sc = S1_Vec2(sc_sz, sc_sz);
	S1_DrawShadowText(S1_Vec2(x + 4.5, y), s, sc, '0.90 0.95 1.0', num_a);
};

/*
================
S1_DrawBottomIsland
Draws the centered bottom frosted-glass Dynamic Island capsule:
Left wing: Side-by-side big Health & Armor numerals + progress bars.
Center: 34x34 Quake head with pulsing status border + funny mood caption.
Right wing: Active weapon name + big active ammo + mag/reload bar + reserve dots.
================
*/
void(float w, float h, float hp, float armor, float active_ammo, float is_melee, float is_leader, float slot, float mag, float magmax, float rlp, float a) S1_DrawBottomIsland =
{
	local float cx, pill_w, pill_h, pill_x, pill_y, wing_w, lx, rx;
	local float col_gap, col_w, ax, info_w;
	local float hp_disp, hp_frac, over_frac, arm_disp, arm_max, arm_frac;
	local float disp_ammo, mood_ammo, num_sc, ammo_sc;
	local float pulse, pulse_spd, bd_a, head_sz, face_x, face_y;
	local float has_quad_pent, wd, w_sc, mag_frac, mag_low, rlp_frac, step_x, res_sc;
	local string face_pic, mood, wname, hp_str, arm_str, ammo_str, mag_str;
	local vector glass_bg, top_hi, glass_bd, hp_col, hp_bar_col, arm_col, tier_col, head_bd, mood_col, ammo_col, bar_col;

	cx = w * 0.5;
	pill_w = 400;
	if (pill_w > w - 16)
		pill_w = w - 16;
	if (pill_w < 240)
		return;

	pill_h = 52;
	pill_x = cx - pill_w * 0.5;
	pill_y = h - 55;
	wing_w = (pill_w - 96) * 0.5;
	lx = pill_x + 10;
	rx = pill_x + pill_w - 10 - wing_w;

	glass_bg = '0.06 0.09 0.15';
	top_hi = '0.70 0.94 1.0';
	glass_bd = '0.40 0.72 0.92';

	has_quad_pent = ((items & IT_QUAD) || (items & IT_INVULNERABILITY) || quad_count > 0 || pent_count > 0);
	if (has_quad_pent)
		top_hi = '0.84 0.56 1.0';

	// Outer frosted-glass pill
	S1_DrawGlassPill(S1_Vec2(pill_x, pill_y), S1_Vec2(pill_w, pill_h), glass_bg, 0.78 * a, top_hi, 0.65 * a, glass_bd, 0.34 * a);

	// Hairline frosted vertical dividers flanking the Quake head pod
	drawfill(S1_Vec2(cx - 34, pill_y + 6), S1_Vec2(1, pill_h - 12), '0.75 0.92 1.0', 0.16 * a, 0);
	drawfill(S1_Vec2(cx + 33, pill_y + 6), S1_Vec2(1, pill_h - 12), '0.75 0.92 1.0', 0.16 * a, 0);

	// ---------------- CENTERPIECE: QUAKE HEAD + MOOD CAPTION ----------------
	head_sz = 34;
	face_x = cx - head_sz * 0.5;
	face_y = pill_y + 3;

	pulse_spd = 4.5;
	if (has_quad_pent || (hp > 0 && hp < 25))
		pulse_spd = 9.0;
	pulse = sin(time * pulse_spd);
	bd_a = (0.72 + 0.25 * pulse) * a;

	if (has_quad_pent)
		head_bd = '0.78 0.36 1.0';
	else if (hp <= 0 || hp < 25)
		head_bd = '1.0 0.30 0.36';
	else if (hp < 50)
		head_bd = '1.0 0.76 0.22';
	else if (hp >= 80)
		head_bd = '0.24 0.95 0.68';
	else
		head_bd = '0.24 0.88 1.0';

	// Pulsing status frame (1:1 aspect ratio)
	HUD_Box(S1_Vec2(face_x - 1, face_y - 1), S1_Vec2(head_sz + 2, head_sz + 2), '0.03 0.05 0.09', 0.85 * a, head_bd, bd_a, 1);

	face_pic = HUD_GetFacePic(hp, items);
	HUD_DrawPic(S1_Vec2(face_x, face_y), S1_Vec2(head_sz, head_sz), face_pic, '1 1 1', a);

	mood_ammo = active_ammo;
	if (magmax > 0 && mag > mood_ammo)
		mood_ammo = mag;
	mood = S1_GetMoodCaption(hp, armor, items, mood_ammo, is_melee, is_leader);
	mood_col = head_bd;
	if (mood_ammo <= 0 && !is_melee && hp >= 45 && !has_quad_pent)
		mood_col = '1.0 0.74 0.26';
	HUD_DrawCenterText(S1_Vec2(cx, pill_y + 41.5), mood, '4.5 4.5 0', mood_col, 0.94 * a);

	// ---------------- LEFT WING: HEALTH & ARMOR (SIDE-BY-SIDE BIG NUMERALS) ----------------
	col_gap = 10;
	col_w = (wing_w - col_gap) * 0.5;
	ax = lx + col_w + col_gap;

	// Subtle vertical divider between HP and Armor columns
	drawfill(S1_Vec2(lx + col_w + col_gap * 0.5, pill_y + 8), S1_Vec2(1, pill_h - 16), '0.75 0.92 1.0', 0.10 * a, 0);

	hp_disp = hp;
	if (hp_disp < 0)
		hp_disp = 0;
	hp_col = HUD_GetStatColor(hp, 35, 75);
	hp_str = ftos(hp_disp);
	num_sc = 19;
	wd = BM_UIStringWidth(hp_str, FALSE, S1_Vec2(num_sc, num_sc));
	if (wd > col_w && wd > 0)
		num_sc = num_sc * (col_w / wd);

	S1_DrawShadowText(S1_Vec2(lx, pill_y + 5.5), "HP", '5.5 5.5 0', '0.62 0.82 0.96', 0.88 * a);
	S1_DrawShadowText(S1_Vec2(lx, pill_y + 15), hp_str, S1_Vec2(num_sc, num_sc), hp_col, 0.99 * a);

	hp_frac = 0;
	if (hp > 0)
		hp_frac = hp / 100;
	if (hp_frac > 1)
		hp_frac = 1;
	hp_bar_col = hp_col;
	if (hp > 100)
		hp_bar_col = '0.26 0.92 1.0';
	HUD_Bar(S1_Vec2(lx, pill_y + 40), S1_Vec2(col_w, 4), hp_frac, hp_bar_col, 0.95 * a, '0.14 0.20 0.30', 0.75 * a);
	if (hp > 100)
	{
		over_frac = (hp - 100) / 100;
		if (over_frac > 1)
			over_frac = 1;
		drawfill(S1_Vec2(lx, pill_y + 40), S1_Vec2(col_w * over_frac, 4), '0.88 0.98 1.0', 0.85 * a, 0);
	}

	arm_disp = armor;
	if (arm_disp < 0)
		arm_disp = 0;
	if (arm_disp <= 0)
		arm_col = '0.55 0.30 0.30';
	else
		arm_col = HUD_GetStatColor(arm_disp, 30, 75);

	tier_col = HUD_GetArmorColor(items);
	arm_max = HUD_GetArmorMax(items);
	if (arm_max <= 0)
		arm_max = 100;
	arm_frac = 0;
	if (arm_disp > 0)
		arm_frac = arm_disp / arm_max;

	arm_str = ftos(arm_disp);
	num_sc = 19;
	wd = BM_UIStringWidth(arm_str, FALSE, S1_Vec2(num_sc, num_sc));
	if (wd > col_w && wd > 0)
		num_sc = num_sc * (col_w / wd);

	drawfill(S1_Vec2(ax, pill_y + 6), S1_Vec2(3, 5.5), tier_col, 0.95 * a, 0);
	S1_DrawShadowText(S1_Vec2(ax + 5, pill_y + 5.5), "ARMOR", '5.5 5.5 0', '0.62 0.82 0.96', 0.86 * a);
	S1_DrawShadowText(S1_Vec2(ax, pill_y + 15), arm_str, S1_Vec2(num_sc, num_sc), arm_col, 0.99 * a);
	HUD_Bar(S1_Vec2(ax, pill_y + 40), S1_Vec2(col_w, 4), arm_frac, tier_col, 0.95 * a, '0.14 0.20 0.30', 0.75 * a);

	// ---------------- RIGHT WING: ACTIVE WEAPON, BIG AMMO, MAG/RELOAD & RESERVES ----------------
	info_w = wing_w - 66;
	wname = S1_ShortWeaponName(slot, currentweap);
	w_sc = 5.2;
	wd = BM_UIStringWidth(wname, FALSE, S1_Vec2(w_sc, w_sc));
	if (wd > info_w && wd > 0)
	{
		w_sc = w_sc * (info_w / wd);
		if (w_sc < 3.5)
			w_sc = 3.5;
	}
	S1_DrawShadowText(S1_Vec2(rx, pill_y + 5.5), wname, S1_Vec2(w_sc, w_sc), '0.66 0.90 1.0', 0.94 * a);

	if (is_melee)
	{
		ammo_str = "--";
		ammo_col = '0.26 0.95 0.70';
	}
	else
	{
		disp_ammo = active_ammo;
		if (magmax > 0)
			disp_ammo = mag;
		if (disp_ammo < 0)
			disp_ammo = 0;
		ammo_str = ftos(disp_ammo);
		ammo_col = HUD_GetAmmoColor(disp_ammo, currentweap, magmax);
	}
	ammo_sc = 20;
	wd = BM_UIStringWidth(ammo_str, FALSE, S1_Vec2(ammo_sc, ammo_sc));
	if (wd > 62 && wd > 0)
		ammo_sc = ammo_sc * (62 / wd);
	S1_DrawRightShadowText(S1_Vec2(rx + wing_w, pill_y + 5), ammo_str, S1_Vec2(ammo_sc, ammo_sc), ammo_col, 0.99 * a);

	// Middle left bar: Reload progress takes priority, else M4/Garand mag bar, else subtle glass divider
	if (rlp > 0 && hp > 0)
	{
		rlp_frac = rlp / 100;
		S1_DrawShadowText(S1_Vec2(rx, pill_y + 14), "RELOAD", '4.5 4.5 0', '1.0 0.82 0.28', 0.95 * a);
		HUD_DrawRightText(S1_Vec2(rx + info_w - 2, pill_y + 14), strcat(ftos(rlp), "%"), '4.5 4.5 0', '1.0 0.88 0.48', 0.95 * a);
		HUD_Bar(S1_Vec2(rx, pill_y + 21.5), S1_Vec2(info_w - 2, 3.5), rlp_frac, '1.0 0.80 0.24', 0.96 * a, '0.14 0.20 0.30', 0.80 * a);
	}
	else if (magmax > 0)
	{
		mag_frac = mag / magmax;
		mag_low = max(1, floor(magmax * 0.25));
		bar_col = '0.26 0.88 1.0';
		if (mag <= mag_low)
			bar_col = '1.0 0.34 0.36';
		mag_str = strcat(ftos(mag), "/", ftos(magmax));
		S1_DrawShadowText(S1_Vec2(rx, pill_y + 14), strcat("RES ", ftos(active_ammo)), '4.5 4.5 0', '0.62 0.82 0.96', 0.88 * a);
		HUD_DrawRightText(S1_Vec2(rx + info_w - 2, pill_y + 14), mag_str, '4.5 4.5 0', '0.94 0.98 1.0', 0.92 * a);
		HUD_Bar(S1_Vec2(rx, pill_y + 21.5), S1_Vec2(info_w - 2, 3.5), mag_frac, bar_col, 0.95 * a, '0.14 0.20 0.30', 0.80 * a);
	}
	else
	{
		drawfill(S1_Vec2(rx, pill_y + 22), S1_Vec2(info_w - 2, 1), '0.72 0.90 1.0', 0.14 * a, 0);
	}

	// Subtle horizontal separator above reserve chips
	drawfill(S1_Vec2(rx, pill_y + 31), S1_Vec2(wing_w, 1), '0.72 0.90 1.0', 0.10 * a, 0);

	// Compact tiny color-coded reserve dots (S N R C)
	step_x = wing_w / 4;
	res_sc = 5.0;

	S1_DrawReserveChip(rx, pill_y + 38, shell_ammo, '1.0 0.78 0.26', res_sc, a);
	S1_DrawReserveChip(rx + step_x, pill_y + 38, nail_ammo, '0.24 0.88 1.0', res_sc, a);
	S1_DrawReserveChip(rx + step_x * 2, pill_y + 38, rocket_ammo, '1.0 0.36 0.38', res_sc, a);
	S1_DrawReserveChip(rx + step_x * 3, pill_y + 38, cell_ammo, '0.26 0.96 0.68', res_sc, a);
};

/*
================
S1_DrawTopIsland
Top-center Dynamic Island pill (appears ONLY when Quad/Pent/Invis/Suit/Slowmo/
Warmup/Shield/Regen/Boost/Leader is active) plus a sleek Frags pill tucked nearby.
================
*/
void(float w, float h, float hp, float a) S1_DrawTopIsland =
{
	local float cx, prot, heat, boost, regen, warm, lheat, frags;
	local float has_status, iw, fw, ix, fx, txt_sc, wd, max_iw, has_key;
	local string leader, s, fstr;
	local vector hi_col, bd_col;

	cx = w * 0.5;
	prot = getstati(BMST_PROT);
	heat = getstati(BMST_HEAT);
	boost = getstati(BMST_BOOST);
	regen = getstati(BMST_REGEN);
	warm = getstati(BMST_WARMUP);
	lheat = getstati(BMST_LHEAT);
	leader = getstats(BMST_LEADER);
	frags = getstati(STAT_FRAGS);

	s = "";
	has_status = 0;
	hi_col = '0.70 0.94 1.0';
	bd_col = '0.40 0.72 0.92';

	if (quad_count > 0 || (items & IT_QUAD))
	{
		has_status = 1;
		hi_col = '0.82 0.50 1.0';
		s = strcat("^6QUAD ", ftos(quad_count), "s");
	}
	if (pent_count > 0 || (items & IT_INVULNERABILITY))
	{
		if (has_status) s = strcat(s, "  ^8|  ");
		has_status = 1;
		hi_col = '1.0 0.44 0.52';
		s = strcat(s, "^1PENT ", ftos(pent_count), "s");
	}
	if (invis_count > 0 || (items & IT_INVISIBILITY))
	{
		if (has_status) s = strcat(s, "  ^8|  ");
		has_status = 1;
		s = strcat(s, "^5INVIS ", ftos(invis_count), "s");
	}
	if (bio_count > 0 || (items & IT_SUIT))
	{
		if (has_status) s = strcat(s, "  ^8|  ");
		has_status = 1;
		s = strcat(s, "^2SUIT ", ftos(bio_count), "s");
	}
	if (slow_count > 0)
	{
		if (has_status) s = strcat(s, "  ^8|  ");
		has_status = 1;
		s = strcat(s, "^5SLOW ", ftos(slow_count), "s");
	}
	if (prot > 0 && hp > 0)
	{
		if (has_status) s = strcat(s, "  ^8|  ");
		has_status = 1;
		s = strcat(s, "^5SHIELD ", ftos(ceil(prot / 10)), "s");
	}
	if (regen && hp > 0)
	{
		if (has_status) s = strcat(s, "  ^8|  ");
		has_status = 1;
		s = strcat(s, "^2+REGEN");
	}
	if (boost >= 15 && hp > 0)
	{
		if (has_status) s = strcat(s, "  ^8|  ");
		has_status = 1;
		s = strcat(s, "^2BOOST +", ftos(boost), "%");
	}
	if (leader != "" && lheat >= 4)
	{
		if (has_status) s = strcat(s, "  ^8|  ");
		has_status = 1;
		if (heat >= 4 && heat == lheat)
			s = strcat(s, "^3LEAD +", ftos(lheat));
		else
			s = strcat(s, "^3LDR: ", leader, " +", ftos(lheat));
	}
	if (warm)
	{
		if (has_status) s = strcat(s, "  ^8|  ");
		has_status = 1;
		s = strcat(s, "^xfd0WARMUP ^3F1^7+ ^3F2^7- ^3F3^7LAN");
	}

	if (has_status)
	{
		txt_sc = 5;
		wd = BM_UIStringWidth(s, TRUE, S1_Vec2(txt_sc, txt_sc));
		max_iw = w - 120;
		if (max_iw < 140)
			max_iw = w - 20;
		if (wd > max_iw - 16 && wd > 0)
		{
			txt_sc = txt_sc * ((max_iw - 16) / wd);
			if (txt_sc < 3.8)
				txt_sc = 3.8;
			wd = BM_UIStringWidth(s, TRUE, S1_Vec2(txt_sc, txt_sc));
		}
		iw = wd + 18;
		ix = cx - iw * 0.5;
		S1_DrawGlassPill(S1_Vec2(ix, 5), S1_Vec2(iw, 13), '0.05 0.08 0.14', 0.80 * a, hi_col, 0.72 * a, bd_col, 0.36 * a);
		HUD_DrawCenterColorText(S1_Vec2(cx, (BM_GetUIFont() > 0) ? (5 + (13 - BM_UIScale(txt_sc)) * 0.5) : (9.2 - txt_sc * 0.1)), s, S1_Vec2(txt_sc, txt_sc), 0.96 * a);
	}

	// Frags / Mode / Keys pill tucked cleanly beside the Dynamic Island (or centered when idle)
	has_key = (items & (IT_KEY1 | IT_KEY2));
	if (deathmatch || ctf || coop || frags != 0 || has_key)
	{
		if (ctf)
			fstr = strcat("^5B:", ftos(BLUE_CAPS), " ^1R:", ftos(RED_CAPS), " ^8FRAGS ^7", ftos(frags));
		else if (coop)
			fstr = strcat("^3LIVES:", ftos(life_count), " ^8FRAGS ^7", ftos(frags));
		else
			fstr = strcat("^8FRAGS ^7", ftos(frags));

		if (items & IT_KEY1)
			fstr = strcat(fstr, " ^5[K1]");
		if (items & IT_KEY2)
			fstr = strcat(fstr, " ^3[K2]");

		wd = BM_UIStringWidth(fstr, TRUE, '5 5 0');
		fw = wd + 14;
		if (has_status)
		{
			fx = ix - fw - 6;
			if (fx < 6)
				fx = 6;
			// Avoid overlapping the island if screen is very narrow
			if (fx + fw > ix - 2)
			{
				S1_DrawGlassPill(S1_Vec2(6, 21), S1_Vec2(fw, 13), '0.06 0.09 0.15', 0.76 * a, '0.70 0.94 1.0', 0.58 * a, '0.40 0.72 0.92', 0.32 * a);
				HUD_DrawCenterColorText(S1_Vec2(6 + fw * 0.5, (BM_GetUIFont() > 0) ? 24.1 : 25), fstr, '5 5 0', 0.95 * a);
				return;
			}
		}
		else
		{
			fx = cx - fw * 0.5;
		}
		S1_DrawGlassPill(S1_Vec2(fx, 5), S1_Vec2(fw, 13), '0.06 0.09 0.15', 0.76 * a, '0.70 0.94 1.0', 0.58 * a, '0.40 0.72 0.92', 0.32 * a);
		HUD_DrawCenterColorText(S1_Vec2(fx + fw * 0.5, 9), fstr, '5 5 0', 0.95 * a);
	}
};

/*
================
HUD_DrawStyle1
Main entry point for Style 1 ("DYNAMIC ISLAND").
================
*/
void(float w, float h) HUD_DrawStyle1 =
{
	local float hp, armor, active_ammo, slot, mag, magmax, rlp, is_melee, is_leader, a;

	// Normalize to virtual console units (CSQC_UpdateView passes physical window pixels)
	if (vid_conwidth > 0)
		w = vid_conwidth;
	else
		w = cvar("vid_conwidth");
	if (vid_conheight > 0)
		h = vid_conheight;
	else
		h = cvar("vid_conheight");
	if (w <= 0 || h <= 0)
		return;

	hp = player_health;
	armor = getstati(STAT_ARMOR);
	active_ammo = getstati(STAT_AMMO);
	slot = getstati(BMST_SLOT);
	mag = getstati(BMST_MAG);
	magmax = getstati(BMST_MAGMAX);
	rlp = getstati(BMST_RELOAD);

	is_melee = ((currentweap == IT_AXE || currentweap == IT_CHAINSAW) && slot != 16 && slot != 18);
	is_leader = HUD_IsLeader();

	// Bakersfield world overlays & centerprint (HUD_DrawWorldTagsAndVignette calls BM_DrawCenterPrint)
	HUD_DrawWorldTagsAndVignette(w, h, hp);
	JP_DrawHUD(w, h, hp);
	HUD_DrawTopRightToys(w, h, hp);

	if (showscores)
		return;

	a = sbar_alpha;
	if (a <= 0)
		a = 1;
	if (a > 1)
		a = 1;

	S1_DrawTopIsland(w, h, hp, a);
	S1_DrawBottomIsland(w, h, hp, armor, active_ammo, is_melee, is_leader, slot, mag, magmax, rlp, a);
};
