/*
================
HUD STYLE 3: "CYBERPOP" (Vibrant Synthwave / Hero-Shooter Neon)

Owns ONLY hud_style_3.qc.
Electric Cyan ('0.08 0.92 1.0'), Hot Magenta ('1.0 0.20 0.68'),
Acid Lime ('0.55 1.0 0.25'), crisp white numerals on obsidian-blue
('0.05 0.06 0.14', alpha ~0.72) with chamfered drawfill bevels.
No weapon bar / menu of guns. Keeps Quake Head + cyber-quips.
================
*/

// Shadowed left-aligned text helper
void(vector pos, string s, vector sc, vector rgb, float a) HUD3_DrawShadowText =
{
	local vector p, sp, sz;

	if (a <= 0)
		return;
	sz = BM_UIScaleVec(sc);
	p_x = pos_x;
	p_y = pos_y;
	p_z = 0;
	sp_x = pos_x + 1;
	sp_y = pos_y + 1;
	sp_z = 0;
	drawstring(sp, s, sz, '0 0 0', a * 0.75, 0);
	drawstring(p, s, sz, rgb, a, 0);
};

// Shadowed right-aligned text helper
void(vector right_pos, string s, vector sc, vector rgb, float a) HUD3_DrawRightShadowText =
{
	local float wd;
	local vector p;

	if (a <= 0)
		return;
	wd = BM_UIStringWidth(s, FALSE, sc);
	p_x = right_pos_x - wd;
	p_y = right_pos_y;
	p_z = 0;
	HUD3_DrawShadowText(p, s, sc, rgb, a);
};

// Chamfered obsidian-blue sci-fi panel using stepped drawfill bevels + neon edge trim.
// cut_right == 1 bevels top-right corner; cut_right == 0 bevels top-left corner.
void(float x, float y, float pw, float ph, float cut, float cut_right, vector bg, float bg_a, vector top_col, vector bot_col, float a) HUD3_BevelPanel =
{
	local float i, row_x, row_w, body_y, body_h;

	if (a <= 0 || pw <= 0 || ph <= 0)
		return;

	if (cut < 0)
		cut = 0;
	if (cut > ph * 0.5)
		cut = ph * 0.5;
	if (cut > pw * 0.35)
		cut = pw * 0.35;

	// Stepped chamfered top rows
	i = 0;
	while (i < cut)
	{
		row_w = pw - (cut - i);
		if (cut_right)
			row_x = x;
		else
			row_x = x + (cut - i);
		drawfill(row_x * '1 0 0' + (y + i) * '0 1 0', row_w * '1 0 0' + '0 1 0', bg, bg_a * a, 0);
		// Diagonal chamfer neon pixel
		if (cut_right)
			drawfill((row_x + row_w - 1) * '1 0 0' + (y + i) * '0 1 0', '1.5 1 0', top_col, 0.90 * a, 0);
		else
			drawfill(row_x * '1 0 0' + (y + i) * '0 1 0', '1.5 1 0', top_col, 0.90 * a, 0);
		i = i + 1;
	}

	// Main lower body
	body_y = y + cut;
	body_h = ph - cut;
	if (body_h > 0)
		drawfill(x * '1 0 0' + body_y * '0 1 0', pw * '1 0 0' + body_h * '0 1 0', bg, bg_a * a, 0);

	// Top horizontal neon edge across un-beveled span
	if (cut_right)
		drawfill(x * '1 0 0' + y * '0 1 0', (pw - cut) * '1 0 0' + '0 1.5 0', top_col, 0.92 * a, 0);
	else
		drawfill((x + cut) * '1 0 0' + y * '0 1 0', (pw - cut) * '1 0 0' + '0 1.5 0', top_col, 0.92 * a, 0);

	// Subtle top inner gloss highlight
	if (pw - cut - 4 > 0)
	{
		if (cut_right)
			drawfill((x + 2) * '1 0 0' + (y + 2) * '0 1 0', (pw - cut - 4) * '1 0 0' + '0 1 0', '1 1 1', 0.10 * a, 0);
		else
			drawfill((x + cut + 2) * '1 0 0' + (y + 2) * '0 1 0', (pw - cut - 4) * '1 0 0' + '0 1 0', '1 1 1', 0.10 * a, 0);
	}

	// Vertical outer spine + opposite edge accent
	if (cut_right)
	{
		drawfill(x * '1 0 0' + y * '0 1 0', '2 0 0' + ph * '0 1 0', top_col, 0.92 * a, 0);
		if (body_h > 0)
			drawfill((x + pw - 1) * '1 0 0' + body_y * '0 1 0', '1 0 0' + body_h * '0 1 0', bot_col, 0.60 * a, 0);
	}
	else
	{
		drawfill((x + pw - 2) * '1 0 0' + y * '0 1 0', '2 0 0' + ph * '0 1 0', top_col, 0.92 * a, 0);
		if (body_h > 0)
			drawfill(x * '1 0 0' + body_y * '0 1 0', '1 0 0' + body_h * '0 1 0', bot_col, 0.60 * a, 0);
	}

	// Bottom neon trim strip
	drawfill(x * '1 0 0' + (y + ph - 1.5) * '0 1 0', pw * '1 0 0' + '0 1.5 0', bot_col, 0.85 * a, 0);
};

// Segmented neon progress bar with partial frontier fill and top shimmer
void(float x, float y, float total_w, float seg_h, float segs, float gap, float frac, vector fg, vector fg_hi, vector bg, float a) HUD3_DrawSegBar =
{
	local float f, seg_w, filled_segs, i, sx, partial;

	if (segs <= 0 || total_w <= 0 || seg_h <= 0 || a <= 0)
		return;

	f = frac;
	if (f < 0)
		f = 0;
	if (f > 1)
		f = 1;

	seg_w = (total_w - (segs - 1) * gap) / segs;
	if (seg_w <= 0.5)
		return;

	filled_segs = f * segs;
	i = 0;
	while (i < segs)
	{
		sx = x + i * (seg_w + gap);
		drawfill(sx * '1 0 0' + y * '0 1 0', seg_w * '1 0 0' + seg_h * '0 1 0', bg, 0.72 * a, 0);

		if (filled_segs >= i + 1)
		{
			drawfill(sx * '1 0 0' + y * '0 1 0', seg_w * '1 0 0' + seg_h * '0 1 0', fg, 0.92 * a, 0);
			drawfill(sx * '1 0 0' + y * '0 1 0', seg_w * '1 0 0' + '0 1 0', fg_hi, 0.55 * a, 0);
		}
		else if (filled_segs > i)
		{
			partial = seg_w * (filled_segs - i);
			if (partial > 0.4)
			{
				drawfill(sx * '1 0 0' + y * '0 1 0', partial * '1 0 0' + seg_h * '0 1 0', fg, 0.92 * a, 0);
				drawfill(sx * '1 0 0' + y * '0 1 0', partial * '1 0 0' + '0 1 0', fg_hi, 0.55 * a, 0);
			}
		}
		i = i + 1;
	}
};

// Cyberpop mood quip for the Quake Head badge
string(float hp, float armor, float it_flags, float active_ammo, float is_melee, float is_leader) HUD3_GetCyberQuip =
{
	if (hp <= 0)
		return "SIGNAL LOST";
	if ((it_flags & IT_INVULNERABILITY) && (it_flags & IT_INVISIBILITY))
		return "GHOST.SYS";
	if (it_flags & IT_INVULNERABILITY)
		return "GOD_MODE.EXE";
	if (it_flags & IT_QUAD)
		return "OVERCLOCKED";
	if (it_flags & IT_INVISIBILITY)
		return "STEALTH.DLL";
	if (it_flags & IT_SUIT)
		return "HAZMAT_OS";
	if (hp <= 5)
		return "1HP DREAM";
	if (hp < 25)
		return "OOF.EXE";
	if (hp < 45)
		return "CRIT://SOS";
	if (!is_melee && active_ammo <= 0)
		return "OUTTA LEAD";
	if (is_leader)
		return "APEX // #1";
	if (hp > 100 || (hp >= 100 && armor >= 100))
		return "OVERCLOCKED";
	if (hp >= 75)
		return "LOCKED IN";
	return "SYNCED";
};

// Bottom-left Hero Portrait (38x38 Quake Head) + Vitals + Cyber-Quip
void(float w, float h, float hp, float armor, float it_flags, float active_ammo, float is_melee, float is_leader, float a) HUD3_DrawVitalsCluster =
{
	local float lx, ly, lw, lh, fx, fy, vx, vw, sn, pulse, hp_frac, ap_frac, armormax, in_pain;
	local vector c_bg, c_bg_deep, c_cyan, c_mag, c_lime, c_amber, c_white, c_rim1, c_rim2, c_hp, c_ap, hp_col, arm_col;
	local string quip, face_pic, ap_tag;

	c_bg = '0.05 0.06 0.14';
	c_bg_deep = '0.02 0.03 0.08';
	c_cyan = '0.08 0.92 1.0';
	c_mag = '1.0 0.20 0.68';
	c_lime = '0.55 1.0 0.25';
	c_amber = '1.0 0.78 0.18';
	c_white = '1 1 1';

	lx = 10;
	ly = h - 66;
	lw = min(232, floor((w - 28) * 0.5));
	lh = 52;

	// Outer chamfered obsidian-blue shell (top-right angled bevel)
	HUD3_BevelPanel(lx, ly, lw, lh, 6, 1, c_bg, 0.74, c_cyan, c_mag, a);

	// 38x38 1:1 Hero Portrait frame (double-rimmed neon cyan / magenta)
	fx = lx + 5;
	fy = ly + 7;
	sn = sin(time * 7);
	pulse = 0.5 + 0.5 * sn;
	in_pain = (time < hud_pain_until);

	c_rim1 = c_cyan;
	c_rim2 = c_mag;
	if (it_flags & (IT_QUAD | IT_INVULNERABILITY))
	{
		c_rim1 = c_mag;
		c_rim2 = c_lime;
	}
	else if (hp < 25 || in_pain)
	{
		c_rim1 = c_mag;
		c_rim2 = c_amber;
	}

	// Outer neon rim (42x42)
	drawfill((fx - 2) * '1 0 0' + (fy - 2) * '0 1 0', '42 42 0', c_rim1, (0.72 + 0.24 * pulse) * a, 0);
	// Inner obsidian mat (40x40)
	drawfill((fx - 1) * '1 0 0' + (fy - 1) * '0 1 0', '40 40 0', c_bg_deep, 0.94 * a, 0);
	// Corner neon accent brackets (top-left & bottom-right)
	drawfill((fx - 2) * '1 0 0' + (fy - 2) * '0 1 0', '10 1.5 0', c_rim2, 0.95 * a, 0);
	drawfill((fx - 2) * '1 0 0' + (fy - 2) * '0 1 0', '1.5 10 0', c_rim2, 0.95 * a, 0);
	drawfill((fx + 30) * '1 0 0' + (fy + 38.5) * '0 1 0', '10 1.5 0', c_rim2, 0.95 * a, 0);
	drawfill((fx + 38.5) * '1 0 0' + (fy + 30) * '0 1 0', '1.5 10 0', c_rim2, 0.95 * a, 0);

	// Keep the Quake Head (1:1 38x38)
	face_pic = HUD_GetFacePic(hp, it_flags);
	HUD_DrawPic(fx * '1 0 0' + fy * '0 1 0', '38 38 0', face_pic, '1 1 1', a);

	// Right interior column inside left panel
	vx = fx + 44;
	vw = lw - 54;

	// Row 1: Cyber-Quip badge (dark inset + bright neon-tinted text for crisp contrast)
	quip = HUD3_GetCyberQuip(hp, armor, it_flags, active_ammo, is_melee, is_leader);
	drawfill(vx * '1 0 0' + (ly + 4) * '0 1 0', (vw - 6) * '1 0 0' + '0 8.5 0', c_bg_deep, 0.82 * a, 0);
	if (hp < 25 || (!is_melee && active_ammo <= 0))
	{
		drawfill(vx * '1 0 0' + (ly + 4) * '0 1 0', (vw - 6) * '1 0 0' + '0 8.5 0', c_mag, 0.22 * a, 0);
		drawfill(vx * '1 0 0' + (ly + 4) * '0 1 0', '2.5 8.5 0', c_mag, 0.98 * a, 0);
		HUD3_DrawShadowText((vx + 5) * '1 0 0' + (ly + 5.5) * '0 1 0', quip, '5 5 0', '1.0 0.62 0.86', 1.0 * a);
	}
	else if ((it_flags & IT_QUAD) || (it_flags & IT_INVULNERABILITY) || hp > 100)
	{
		drawfill(vx * '1 0 0' + (ly + 4) * '0 1 0', (vw - 6) * '1 0 0' + '0 8.5 0', c_lime, 0.16 * a, 0);
		drawfill(vx * '1 0 0' + (ly + 4) * '0 1 0', '2.5 8.5 0', c_lime, 0.98 * a, 0);
		HUD3_DrawShadowText((vx + 5) * '1 0 0' + (ly + 5.5) * '0 1 0', quip, '5 5 0', '0.80 1.0 0.58', 1.0 * a);
	}
	else
	{
		drawfill(vx * '1 0 0' + (ly + 4) * '0 1 0', (vw - 6) * '1 0 0' + '0 8.5 0', c_cyan, 0.14 * a, 0);
		drawfill(vx * '1 0 0' + (ly + 4) * '0 1 0', '2.5 8.5 0', c_cyan, 0.98 * a, 0);
		HUD3_DrawShadowText((vx + 5) * '1 0 0' + (ly + 5.5) * '0 1 0', quip, '5 5 0', '0.65 0.98 1.0', 1.0 * a);
	}

	// Row 2: Big bold colorized HP & Armor numerals ('18 18 0')
	c_hp = c_lime;
	if (hp < 25)
		c_hp = c_mag;
	else if (hp < 60)
		c_hp = c_amber;
	else if (hp > 100)
		c_hp = c_cyan;

	hp_col = HUD_GetStatColor(hp, 35, 75);
	arm_col = HUD_GetStatColor(armor, 30, 75);

	HUD3_DrawShadowText(vx * '1 0 0' + (ly + 15.5) * '0 1 0', "HP", '4.5 4.5 0', c_hp, 0.92 * a);
	HUD3_DrawShadowText((vx + 11) * '1 0 0' + (ly + 14.5) * '0 1 0', ftos(hp), '18 18 0', hp_col, 0.98 * a);

	// Armor tier color & label
	ap_tag = "AP";
	c_ap = c_cyan;
	if (it_flags & IT_ARMOR3)
	{
		ap_tag = "RA";
		c_ap = c_mag;
	}
	else if (it_flags & IT_ARMOR2)
	{
		ap_tag = "YA";
		c_ap = c_amber;
	}
	else if (it_flags & IT_ARMOR1)
	{
		ap_tag = "GA";
		c_ap = c_lime;
	}

	if (armor > 0)
	{
		HUD3_DrawShadowText((vx + min(110, vw - 52)) * '1 0 0' + (ly + 15.5) * '0 1 0', ap_tag, '4.5 4.5 0', c_ap, 0.95 * a);
		HUD3_DrawRightShadowText((vx + vw) * '1 0 0' + (ly + 14.5) * '0 1 0', ftos(armor), '18 18 0', arm_col, 0.98 * a);
	}
	else
	{
		HUD3_DrawShadowText((vx + min(110, vw - 52)) * '1 0 0' + (ly + 15.5) * '0 1 0', "AP", '4.5 4.5 0', '0.42 0.48 0.64', 0.65 * a);
		HUD3_DrawRightShadowText((vx + vw) * '1 0 0' + (ly + 14.5) * '0 1 0', "0", '18 18 0', arm_col, 0.72 * a);
	}

	// Row 3: 10-segment neon health bar (with >100 overcharge tint)
	hp_frac = hp / 100;
	if (hp_frac < 0)
		hp_frac = 0;
	if (hp_frac > 1)
		hp_frac = 1;
	HUD3_DrawSegBar(vx, ly + 36, vw, 5, 10, 2, hp_frac, c_hp, c_white, c_bg_deep, a);
	if (hp > 100)
	{
		hp_frac = (hp - 100) / 100;
		if (hp_frac > 1)
			hp_frac = 1;
		HUD3_DrawSegBar(vx, ly + 36, vw, 2, 10, 2, hp_frac, c_mag, c_white, c_bg_deep, 0.90 * a);
	}

	// Row 4: Sleek cyan armor bar
	armormax = HUD_GetArmorMax(it_flags);
	if (armormax <= 0)
		armormax = 100;
	ap_frac = armor / armormax;
	if (ap_frac < 0)
		ap_frac = 0;
	if (ap_frac > 1)
		ap_frac = 1;
	HUD_Bar(vx * '1 0 0' + (ly + 44) * '0 1 0', vw * '1 0 0' + '0 3 0', ap_frac, c_cyan, 0.92 * a, c_bg_deep, 0.78 * a);
};

// Bottom-right Weapon & Ammo Cluster (NO menu of guns!)
void(float w, float h, float slot, float active_weap, float active_ammo, float is_melee, float mag, float magmax, float rlp, float a) HUD3_DrawAmmoCluster =
{
	local float rw, rh, rx, ry, ix, iw, sn, pulse, bar_frac, cx_x, chip_w, chip_step, disp_ammo;
	local vector c_bg, c_bg_deep, c_cyan, c_mag, c_lime, c_amber, c_white, c_muted, ammo_col, bar_col, c_shl, c_nl, c_rkt, c_cel;
	local string wname, ammo_str, mag_str;

	c_bg = '0.05 0.06 0.14';
	c_bg_deep = '0.02 0.03 0.08';
	c_cyan = '0.08 0.92 1.0';
	c_mag = '1.0 0.20 0.68';
	c_lime = '0.55 1.0 0.25';
	c_amber = '1.0 0.78 0.18';
	c_white = '1 1 1';
	c_muted = '0.42 0.48 0.64';

	rw = min(232, floor((w - 28) * 0.5));
	rh = 52;
	rx = w - rw - 10;
	ry = h - 66;
	ix = rx + 8;
	iw = rw - 16;

	// Opposite chamfered obsidian-blue panel (top-left angled bevel)
	HUD3_BevelPanel(rx, ry, rw, rh, 6, 0, c_bg, 0.74, c_mag, c_cyan, a);

	// Row 1: Active weapon name badge (dark inset for crisp text contrast)
	wname = HUD_GetWeaponName(slot, active_weap);
	drawfill((ix + 2) * '1 0 0' + (ry + 4) * '0 1 0', (iw - 2) * '1 0 0' + '0 8.5 0', c_bg_deep, 0.82 * a, 0);
	drawfill((ix + 2) * '1 0 0' + (ry + 4) * '0 1 0', (iw - 2) * '1 0 0' + '0 8.5 0', c_mag, 0.16 * a, 0);
	drawfill((rx + rw - 4.5) * '1 0 0' + (ry + 4) * '0 1 0', '2.5 8.5 0', c_mag, 0.98 * a, 0);
	HUD3_DrawRightShadowText((ix + iw - 4) * '1 0 0' + (ry + 5.5) * '0 1 0', wname, '5 5 0', '0.65 0.98 1.0', 1.0 * a);

	// Reload or Mag/Reserve badge on left side of Row 1
	if (rlp > 0)
	{
		sn = sin(time * 10);
		pulse = 0.5 + 0.5 * sn;
		HUD3_DrawShadowText((ix + 4) * '1 0 0' + (ry + 5.5) * '0 1 0', strcat("RELOAD ", ftos(rlp), "%"), '4.5 4.5 0', c_mag, (0.72 + 0.28 * pulse) * a);
	}
	else if (magmax > 0)
	{
		mag_str = strcat("MAG ", ftos(mag), "/", ftos(magmax));
		if (mag <= magmax * 0.25)
			HUD3_DrawShadowText((ix + 4) * '1 0 0' + (ry + 5.5) * '0 1 0', mag_str, '4.5 4.5 0', c_mag, 0.96 * a);
		else
			HUD3_DrawShadowText((ix + 4) * '1 0 0' + (ry + 5.5) * '0 1 0', mag_str, '4.5 4.5 0', c_lime, 0.95 * a);
	}

	// Row 2: Giant colorized active ammo readout ('22 22 0')
	sn = sin(time * 9);
	pulse = 0.5 + 0.5 * sn;
	if (is_melee)
	{
		ammo_str = "INF";
		ammo_col = c_lime;
	}
	else
	{
		ammo_str = ftos(active_ammo);
		if (magmax > 0)
			disp_ammo = mag;
		else
			disp_ammo = active_ammo;
		ammo_col = HUD_GetAmmoColor(disp_ammo, active_weap, magmax);
	}

	if (magmax > 0 && !is_melee)
	{
		// Show mag count huge + reserve total beside it
		HUD3_DrawShadowText((ix + 2) * '1 0 0' + (ry + 14) * '0 1 0', ftos(mag), '22 22 0', ammo_col, 0.98 * a);
		HUD3_DrawRightShadowText((ix + iw) * '1 0 0' + (ry + 22) * '0 1 0', strcat("RES ", ammo_str), '7 7 0', c_cyan, 0.90 * a);
	}
	else
	{
		HUD3_DrawRightShadowText((ix + iw) * '1 0 0' + (ry + 14) * '0 1 0', ammo_str, '22 22 0', ammo_col, 0.98 * a);
		if (!is_melee)
			HUD3_DrawShadowText((ix + 2) * '1 0 0' + (ry + 22) * '0 1 0', "AMMO", '5.5 5.5 0', c_muted, 0.85 * a);
		else
			HUD3_DrawShadowText((ix + 2) * '1 0 0' + (ry + 22) * '0 1 0', "MELEE", '5.5 5.5 0', c_lime, 0.88 * a);
	}

	// Row 3: Thin segmented mag / reload / charge bar
	if (rlp > 0)
	{
		bar_frac = rlp / 100;
		bar_col = c_mag;
		HUD3_DrawSegBar(ix, ry + 38.5, iw, 3.5, 12, 1.5, bar_frac, bar_col, c_white, c_bg_deep, (0.75 + 0.25 * pulse) * a);
	}
	else if (magmax > 0)
	{
		bar_frac = mag / magmax;
		bar_col = c_lime;
		if (bar_frac <= 0.25)
			bar_col = c_mag;
		else if (bar_frac <= 0.5)
			bar_col = c_cyan;
		HUD3_DrawSegBar(ix, ry + 38.5, iw, 3.5, 12, 1.5, bar_frac, bar_col, c_white, c_bg_deep, a);
	}
	else if (is_melee)
	{
		HUD3_DrawSegBar(ix, ry + 38.5, iw, 3.5, 12, 1.5, 1, c_lime, c_white, c_bg_deep, 0.75 * a);
	}
	else
	{
		bar_frac = active_ammo / 100;
		if (bar_frac > 1)
			bar_frac = 1;
		bar_col = c_cyan;
		if (active_ammo <= 0)
			bar_col = c_mag;
		HUD3_DrawSegBar(ix, ry + 38.5, iw, 3.5, 12, 1.5, bar_frac, bar_col, c_white, c_bg_deep, a);
	}

	// Row 4: Minimal color-coded reserve chips (SHL / NL / RKT / CEL)
	chip_step = (iw + 2) / 4;
	chip_w = chip_step - 2;

	c_shl = c_muted;
	if (shell_ammo > 0) c_shl = c_amber;
	c_nl = c_muted;
	if (nail_ammo > 0) c_nl = c_lime;
	c_rkt = c_muted;
	if (rocket_ammo > 0) c_rkt = c_mag;
	c_cel = c_muted;
	if (cell_ammo > 0) c_cel = c_cyan;

	// SHL chip
	cx_x = ix;
	drawfill(cx_x * '1 0 0' + (ry + 44) * '0 1 0', '2 5.5 0', c_shl, 0.90 * a, 0);
	HUD3_DrawShadowText((cx_x + 4) * '1 0 0' + (ry + 44.5) * '0 1 0', strcat("S ", ftos(shell_ammo)), '4.5 4.5 0', c_shl, 0.92 * a);

	// NL chip
	cx_x = ix + chip_step;
	drawfill(cx_x * '1 0 0' + (ry + 44) * '0 1 0', '2 5.5 0', c_nl, 0.90 * a, 0);
	HUD3_DrawShadowText((cx_x + 4) * '1 0 0' + (ry + 44.5) * '0 1 0', strcat("N ", ftos(nail_ammo)), '4.5 4.5 0', c_nl, 0.92 * a);

	// RKT chip
	cx_x = ix + chip_step * 2;
	drawfill(cx_x * '1 0 0' + (ry + 44) * '0 1 0', '2 5.5 0', c_rkt, 0.90 * a, 0);
	HUD3_DrawShadowText((cx_x + 4) * '1 0 0' + (ry + 44.5) * '0 1 0', strcat("R ", ftos(rocket_ammo)), '4.5 4.5 0', c_rkt, 0.92 * a);

	// CEL chip
	cx_x = ix + chip_step * 3;
	drawfill(cx_x * '1 0 0' + (ry + 44) * '0 1 0', '2 5.5 0', c_cel, 0.90 * a, 0);
	HUD3_DrawShadowText((cx_x + 4) * '1 0 0' + (ry + 44.5) * '0 1 0', strcat("C ", ftos(cell_ammo)), '4.5 4.5 0', c_cel, 0.92 * a);
};

// Top-center neon status strip (ONLY when active): Powerups, Leader crown, Warmup, Shield, Regen, Boost.
// Also draws compact top-left Frags/Mode + Keys/Runes badge when active.
void(float w, float h, float hp, float it_flags, float is_leader, float a) HUD3_DrawTopStrip =
{
	local float cx, sx, sy, sw, prot, boost, regen, warm, lheat, has_pwr, has_mode, frags, kx, sn, pulse;
	local string leader, strip, mode_s;
	local vector c_bg, c_cyan, c_mag, c_lime, c_amber, c_white;

	c_bg = '0.05 0.06 0.14';
	c_cyan = '0.08 0.92 1.0';
	c_mag = '1.0 0.20 0.68';
	c_lime = '0.55 1.0 0.25';
	c_amber = '1.0 0.78 0.18';
	c_white = '0.98 0.99 1.0';

	cx = w * 0.5;
	prot = getstati(BMST_PROT);
	boost = getstati(BMST_BOOST);
	regen = getstati(BMST_REGEN);
	warm = getstati(BMST_WARMUP);
	lheat = getstati(BMST_LHEAT);
	leader = getstats(BMST_LEADER);
	sn = sin(time * 6);
	pulse = 0.5 + 0.5 * sn;

	// Compact top-left Frags / CTF / Coop Lives + Keys/Runes
	mode_s = "";
	has_mode = 0;
	if (ctf)
	{
		mode_s = strcat("^4BLU ", ftos(BLUE_CAPS), "  ^7|  ^1RED ", ftos(RED_CAPS));
		has_mode = 1;
	}
	else if (coop && life_count > 0)
	{
		mode_s = strcat("^2LIVES ", ftos(life_count));
		has_mode = 1;
	}
	else if (deathmatch)
	{
		frags = getstati(STAT_FRAGS);
		mode_s = strcat("^5FRAGS ^7", ftos(frags));
		if (frag_limit > 0)
			mode_s = strcat(mode_s, "^8/", ftos(frag_limit));
		has_mode = 1;
	}

	if (has_mode)
	{
		sw = BM_UIStringWidth(mode_s, TRUE, '5 5 0') + 14;
		HUD3_BevelPanel(10, 6, sw, 13, 3, 1, c_bg, 0.70, c_cyan, c_mag, a);
		BM_DrawColorShadow(16, (BM_GetUIFont() > 0) ? 9.1 : 10, mode_s, 5, 0.95 * a);
		kx = 10 + sw + 4;
	}
	else
	{
		kx = 10;
	}

	// Keys / CTF Flag / Episode Runes beside top-left chip (only when held)
	if (it_flags & IT_KEY1)
	{
		if (ctf)
			HUD_DrawPic(kx * '1 0 0' + '0 6 0', '13 13 0', "gfx/bluflag", '1 1 1', a);
		else
			HUD_DrawPic(kx * '1 0 0' + '0 6 0', '13 13 0', "gfx/sb_key1", '1 1 1', a);
		kx = kx + 15;
	}
	if (it_flags & IT_KEY2)
	{
		if (ctf)
			HUD_DrawPic(kx * '1 0 0' + '0 6 0', '13 13 0', "gfx/redflag", '1 1 1', a);
		else
			HUD_DrawPic(kx * '1 0 0' + '0 6 0', '13 13 0', "gfx/sb_key2", '1 1 1', a);
		kx = kx + 15;
	}
	if (items2 & RUNE_EP1) { HUD_DrawPic(kx * '1 0 0' + '0 6 0', '8 13 0', "gfx/sb_sigil1", c_cyan, a); kx = kx + 10; }
	if (items2 & RUNE_EP2) { HUD_DrawPic(kx * '1 0 0' + '0 6 0', '8 13 0', "gfx/sb_sigil2", c_cyan, a); kx = kx + 10; }
	if (items2 & RUNE_EP3) { HUD_DrawPic(kx * '1 0 0' + '0 6 0', '8 13 0', "gfx/sb_sigil3", c_cyan, a); kx = kx + 10; }
	if (items2 & RUNE_EP4) { HUD_DrawPic(kx * '1 0 0' + '0 6 0', '8 13 0', "gfx/sb_sigil4", c_cyan, a); kx = kx + 10; }

	// Build Top-Center Neon Status Strip (only when active)
	strip = "";
	has_pwr = 0;

	if ((it_flags & IT_QUAD) || quad_count > 0)
	{
		strip = strcat(strip, "  ^5QUAD:", ftos(quad_count), "s");
		has_pwr = 1;
	}
	if ((it_flags & IT_INVULNERABILITY) || pent_count > 0)
	{
		strip = strcat(strip, "  ^1PENT:", ftos(pent_count), "s");
		has_pwr = 1;
	}
	if ((it_flags & IT_INVISIBILITY) || invis_count > 0)
	{
		strip = strcat(strip, "  ^6INVIS:", ftos(invis_count), "s");
		has_pwr = 1;
	}
	if ((it_flags & IT_SUIT) || bio_count > 0)
	{
		strip = strcat(strip, "  ^2SUIT:", ftos(bio_count), "s");
		has_pwr = 1;
	}
	if (slow_count > 0)
	{
		strip = strcat(strip, "  ^3SLOW:", ftos(slow_count), "s");
		has_pwr = 1;
	}
	if (prot > 0 && hp > 0)
	{
		strip = strcat(strip, "  ^5SHIELD:", ftos(ceil(prot / 10)), "s");
		has_pwr = 1;
	}
	if (regen && hp > 0)
	{
		strip = strcat(strip, "  ^2+REGEN");
		has_pwr = 1;
	}
	if (boost >= 15 && hp > 0)
	{
		strip = strcat(strip, "  ^2BOOST+", ftos(boost), "%");
		has_pwr = 1;
	}
	if (leader != "" && lheat >= 4)
	{
		if (is_leader)
			strip = strcat(strip, "  ^3[CROWN] YOU +", ftos(lheat));
		else
			strip = strcat(strip, "  ^3[CROWN] ", leader, " ^3+", ftos(lheat));
		has_pwr = 1;
	}

	sy = 6;
	if (has_pwr)
	{
		// Trim leading 2 spaces
		if (strlen(strip) > 2)
			strip = substring(strip, 2, strlen(strip) - 2);
		sw = BM_UIStringWidth(strip, TRUE, '5 5 0') + 18;
		sx = cx - sw * 0.5;
		HUD3_BevelPanel(sx, sy, sw, 14, 3, 1, c_bg, 0.76, c_mag, c_cyan, (0.85 + 0.15 * pulse) * a);
		HUD_DrawCenterColorText(cx * '1 0 0' + (sy + ((BM_GetUIFont() > 0) ? 3.6 : 4.5)) * '0 1 0', strip, '5 5 0', 0.98 * a);
		sy = sy + 16;
	}

	if (warm)
	{
		strip = "^6WARMUP^7  //  ^5F1^7 +Bot  ^5F2^7 -Bot  ^5F3^7 Join LAN";
		sw = BM_UIStringWidth(strip, TRUE, '5 5 0') + 18;
		sx = cx - sw * 0.5;
		HUD3_BevelPanel(sx, sy, sw, 13, 3, 0, c_bg, 0.72, c_cyan, c_mag, (0.70 + 0.25 * pulse) * a);
		HUD_DrawCenterColorText(cx * '1 0 0' + (sy + ((BM_GetUIFont() > 0) ? 3.1 : 4)) * '0 1 0', strip, '5 5 0', 0.95 * a);
	}
};

/*
================
HUD_DrawStyle3
Entrypoint called from CSQC_UpdateView when bm_hud_style == 3.
================
*/
void(float w, float h) HUD_DrawStyle3 =
{
	local float hp, armor, active_ammo, slot, mag, magmax, rlp, is_leader, is_melee, alpha_mul;

	// Normalize to virtual console coordinates (drawfill/drawpic/drawstring use vid_conwidth x vid_conheight)
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

	hp = getstati(STAT_HEALTH);
	if (hp <= 0)
		hp = player_health;
	armor = getstati(STAT_ARMOR);
	active_ammo = getstati(STAT_AMMO);
	slot = getstati(BMST_SLOT);
	mag = getstati(BMST_MAG);
	magmax = getstati(BMST_MAGMAX);
	rlp = getstati(BMST_RELOAD);
	is_leader = HUD_IsLeader();
	is_melee = (slot != 16 && slot != 18 && (currentweap == IT_AXE || currentweap == IT_CHAINSAW));

	// Shared Bakersfield world overlays (bot/player tags, centerprint, jetpack, low-HP vignette, toy dock)
	HUD_DrawWorldTagsAndVignette(w, h, hp);
	JP_DrawHUD(w, h, hp);
	HUD_DrawTopRightToys(w, h, hp);

	// Guard against sbar_alpha == 0 (e.g. Zircon where sbar_alpha_fg is unregistered) and hide main clusters when dead or holding TAB
	alpha_mul = sbar_alpha;
	if (alpha_mul <= 0)
		alpha_mul = 1;
	if (alpha_mul > 1)
		alpha_mul = 1;
	if (hp <= 0 || showscores)
		return;

	HUD3_DrawVitalsCluster(w, h, hp, armor, items, active_ammo, is_melee, is_leader, alpha_mul);
	HUD3_DrawAmmoCluster(w, h, slot, currentweap, active_ammo, is_melee, mag, magmax, rlp, alpha_mul);
	HUD3_DrawTopStrip(w, h, hp, items, is_leader, alpha_mul);
};
