/*
================
HUD STYLE 2: "ROUTE 99" (Bakersfield Sunset / Arcade Diner Humor)

Bright, punchy Bakersfield Route 99 aesthetic:
  - Translucent slate cards ('0.07 0.08 0.11' @ 0.78) with bold 2.5px colored side bars
  - Warm sunset amber ('1.0 0.72 0.14'), neon mint ('0.20 0.96 0.68'),
    hot coral ('1.0 0.32 0.36'), and crisp cream-white ('0.98 0.96 0.90')
  - Bottom-left "EMPLOYEE BADGE" card with 34x34 Quake Head + witty live status
  - Bottom-right "AMMO RECEIPT" card (NO weapon list / gun menu!)
  - Top-left compact Frags + active Powerups/Leader/Warmup/Shield/Boost pill
================
*/

vector HUD2_BG     = '0.07 0.08 0.11';
vector HUD2_BORDER = '0.22 0.25 0.32';
vector HUD2_AMBER  = '1.00 0.72 0.14';
vector HUD2_MINT   = '0.20 0.96 0.68';
vector HUD2_CORAL  = '1.00 0.32 0.36';
vector HUD2_CREAM  = '0.98 0.96 0.90';
vector HUD2_MUTED  = '0.58 0.62 0.70';
vector HUD2_CYAN   = '0.32 0.88 1.00';

/*
================
HUD2_Text / HUD2_RightText
Crisp drop-shadowed strings so bright diner colors pop on any background.
================
*/
void(vector pos, string s, vector sc, vector rgb, float a) HUD2_Text =
{
	local float off;
	local vector p, sh, usc;

	usc = BM_UIScaleVec(sc);
	off = 0.8;
	if (usc_x >= 14)
		off = 1.2;
	p_x = pos_x;
	p_y = pos_y;
	p_z = 0;
	sh_x = pos_x + off;
	sh_y = pos_y + off;
	sh_z = 0;
	drawstring(sh, s, usc, '0 0 0', a * 0.88, 0);
	drawstring(p, s, usc, rgb, a, 0);
};

void(vector right_pos, string s, vector sc, vector rgb, float a) HUD2_RightText =
{
	local float off;
	local vector sh;

	off = 0.8;
	if (sc_x >= 14)
		off = 1.2;
	sh_x = right_pos_x + off;
	sh_y = right_pos_y + off;
	sh_z = 0;
	HUD_DrawRightText(sh, s, sc, '0 0 0', a * 0.88);
	HUD_DrawRightText(right_pos, s, sc, rgb, a);
};

/*
================
HUD2_Card
Draws a translucent slate card with a crisp 1px border and a bold 2.5px
colored side accent bar (side == 0: left edge, side == 1: right edge).
================
*/
void(vector pos, vector sz, vector accent, float side, float a_mul) HUD2_Card =
{
	local vector bar_pos, bar_sz;

	HUD_Box(pos, sz, HUD2_BG, 0.78 * a_mul, HUD2_BORDER, 0.62 * a_mul, 1);

	bar_sz_x = 2.5;
	bar_sz_y = sz_y;
	bar_sz_z = 0;
	if (side == 1)
		bar_pos_x = pos_x + sz_x - 2.5;
	else
		bar_pos_x = pos_x;
	bar_pos_y = pos_y;
	bar_pos_z = 0;
	drawfill(bar_pos, bar_sz, accent, 0.96 * a_mul, 0);
};

/*
================
HUD2_GetBadgeLine
Hilarious Route 99 live status line reacting to HP, powerups, and ammo.
================
*/
string(float hp, float armor, float it_flags, float ammo_disp, float is_leader) HUD2_GetBadgeLine =
{
	if (hp <= 0)
		return "PLOT ARMOR: 0";
	if ((it_flags & IT_INVULNERABILITY) && (it_flags & IT_INVISIBILITY))
		return "GHOST TRUCKER";
	if (it_flags & IT_INVULNERABILITY)
		return "666 HIGHWAY";
	if (it_flags & IT_QUAD)
		return "UNLEADED RAGE";
	if (it_flags & IT_INVISIBILITY)
		return "SMOG STEALTH";
	if (it_flags & IT_SUIT)
		return "HAZMAT SPECIAL";
	if (hp < 15)
		return "SEND MILK PLS";
	if (hp < 35)
		return "TIS A SCRATCH";
	if (ammo_disp <= 0)
		return "OUTTA GAS LOL";
	if (is_leader)
		return "EMPLOYEE #1";
	if (hp >= 100 && armor >= 150)
		return "SUPER SIZE ME";
	if (hp >= 80)
		return "FEELIN' 99";
	if (hp >= 50)
		return "CRUISIN' 99";
	return "NEED COFFEE";
};

/*
================
HUD2_DrawBadgeCard
Bottom-left "EMPLOYEE BADGE" card (220x52 at y = h - 66 .. h - 14, clearing JP_DrawHUD and showfps).
Features 34x34 Quake Head, ROUTE 99 ID header, live quip, colorized 17px HP/VEST numerals, and bars.
================
*/
void(float h, float hp, float armor, float ammo_disp, float is_leader, float a_mul) HUD2_DrawBadgeCard =
{
	local float x0, y0, cw, ch, hp_frac, arm_max, arm_frac, fl, sn;
	local vector accent, face_border, hp_col, arm_col, arm_bar_col;
	local string quip, face_pic;

	x0 = 10;
	cw = 220;
	ch = 52;
	y0 = h - 66;

	// Accent color reacts to urgency / powerups
	accent = HUD2_AMBER;
	if (hp <= 0 || hp < 35)
		accent = HUD2_CORAL;
	else if ((items & IT_QUAD) || (items & IT_INVULNERABILITY) || is_leader || hp > 100)
		accent = HUD2_MINT;

	HUD2_Card(x0 * '1 0 0' + y0 * '0 1 0', cw * '1 0 0' + ch * '0 1 0', accent, 0, a_mul);

	// Header row: ROUTE 99 ID + live quip
	HUD2_Text((x0 + 6) * '1 0 0' + (y0 + 3) * '0 1 0', "ROUTE 99 ID", '5 5 0', HUD2_AMBER, 0.96 * a_mul);
	quip = HUD2_GetBadgeLine(hp, armor, items, ammo_disp, is_leader);
	HUD2_RightText((x0 + cw - 5) * '1 0 0' + (y0 + 3) * '0 1 0', quip, '5 5 0', accent, 0.96 * a_mul);

	// 34x34 Quake Head (1:1 ratio) with status-colored frame
	face_border = HUD2_AMBER;
	if (hp <= 0 || hp < 35)
	{
		sn = sin(time * 8);
		fl = 0.65 + 0.35 * sn;
		face_border = HUD2_CORAL;
	}
	else
	{
		fl = 0.90;
		if (hp >= 80)
			face_border = HUD2_MINT;
	}
	HUD_Box((x0 + 6) * '1 0 0' + (y0 + 11) * '0 1 0', '36 36 0', '0.04 0.05 0.08', 0.92 * a_mul, face_border, fl * a_mul, 1);
	face_pic = HUD_GetFacePic(hp, items);
	HUD_DrawPic((x0 + 7) * '1 0 0' + (y0 + 12) * '0 1 0', '34 34 0', face_pic, '1 1 1', 0.98 * a_mul);

	// Health row (big colorized HP numeral: red <35, yellow 35..74, white >=75)
	hp_col = HUD_GetStatColor(hp, 35, 75);

	HUD2_Text((x0 + 46) * '1 0 0' + (y0 + 16) * '0 1 0', "HP", '5 5 0', HUD2_MUTED, 0.95 * a_mul);
	HUD2_Text((x0 + 68) * '1 0 0' + (y0 + 10) * '0 1 0', ftos(hp), '17 17 0', hp_col, 0.98 * a_mul);

	hp_frac = 0;
	if (hp > 0)
		hp_frac = hp / 100;
	if (hp_frac > 1)
		hp_frac = 1;
	HUD_Bar((x0 + 124) * '1 0 0' + (y0 + 16) * '0 1 0', '90 6 0', hp_frac, hp_col, 0.92 * a_mul, '0.14 0.16 0.22', 0.85 * a_mul);
	if (hp > 100)
	{
		// Overheal highlight strip
		hp_frac = (hp - 100) / 100;
		if (hp_frac > 1)
			hp_frac = 1;
		drawfill((x0 + 124) * '1 0 0' + (y0 + 16) * '0 1 0', (90 * hp_frac) * '1 0 0' + '0 2 0', HUD2_CYAN, 0.95 * a_mul, 0);
	}

	// Armor (VEST) row (big colorized VEST numeral + tier-colored bar)
	arm_max = HUD_GetArmorMax(items);
	if (arm_max <= 0)
		arm_max = 100;
	arm_frac = 0;
	if (armor > 0)
		arm_frac = armor / arm_max;
	if (arm_frac > 1)
		arm_frac = 1;

	arm_col = HUD_GetStatColor(armor, 30, 75);
	arm_bar_col = HUD_GetArmorColor(items);
	if (armor <= 0)
		arm_bar_col = HUD2_MUTED;

	HUD2_Text((x0 + 46) * '1 0 0' + (y0 + 36) * '0 1 0', "VEST", '5 5 0', HUD2_MUTED, 0.92 * a_mul);
	HUD2_Text((x0 + 68) * '1 0 0' + (y0 + 30) * '0 1 0', ftos(armor), '17 17 0', arm_col, 0.98 * a_mul);
	HUD_Bar((x0 + 124) * '1 0 0' + (y0 + 36) * '0 1 0', '90 5 0', arm_frac, arm_bar_col, 0.90 * a_mul, '0.14 0.16 0.22', 0.85 * a_mul);
};

/*
================
HUD2_DrawReceiptCard
Bottom-right "AMMO RECEIPT" compact card (220x52 at y = h - 66 .. h - 14, NO gun menu or weapon strip).
Shows active weapon label, big 22px colorized active ammo, M4/RL mag + reload bar,
and compact reserve counts (S / N / R / C + P if prox > 0).
================
*/
void(float w, float h, float hp, float active_ammo, float is_melee, float a_mul) HUD2_DrawReceiptCard =
{
	local float x0, y0, cw, ch, slot, mag, magmax, rlp, frac, sn;
	local vector accent, ammo_col, bar_col, c_s, c_n, c_r, c_c;
	local string wname, rtag, ammo_str, sub_lbl;

	if (hp <= 0)
		return;

	cw = 220;
	ch = 52;
	x0 = w - cw - 10;
	y0 = h - 66;

	slot = getstati(BMST_SLOT);
	mag = getstati(BMST_MAG);
	magmax = getstati(BMST_MAGMAX);
	rlp = getstati(BMST_RELOAD);

	accent = HUD2_AMBER;
	if (rlp > 0 || (!is_melee && active_ammo <= 0))
		accent = HUD2_CORAL;
	else if (is_melee || (magmax > 0 && mag >= magmax))
		accent = HUD2_MINT;

	HUD2_Card(x0 * '1 0 0' + y0 * '0 1 0', cw * '1 0 0' + ch * '0 1 0', accent, 1, a_mul);

	// Header row: Active weapon name + receipt/reload status
	wname = HUD_GetWeaponName(slot, currentweap);
	HUD2_Text((x0 + 6) * '1 0 0' + (y0 + 3) * '0 1 0', wname, '5 5 0', HUD2_CREAM, 0.98 * a_mul);
	if (rlp > 0)
	{
		rtag = strcat("RELOAD ", ftos(rlp), "%");
		HUD2_RightText((x0 + cw - 6) * '1 0 0' + (y0 + 3) * '0 1 0', rtag, '5 5 0', HUD2_CORAL, 0.98 * a_mul);
	}
	else
		HUD2_RightText((x0 + cw - 6) * '1 0 0' + (y0 + 3) * '0 1 0', "RECEIPT #99", '5 5 0', HUD2_AMBER, 0.90 * a_mul);

	// Big colorized active ammo readout ('22 22 0')
	if (is_melee)
	{
		ammo_str = "INF";
		ammo_col = HUD2_MINT;
	}
	else
	{
		ammo_str = ftos(active_ammo);
		ammo_col = HUD_GetAmmoColor(active_ammo, currentweap, magmax);
	}
	HUD2_Text((x0 + 6) * '1 0 0' + (y0 + 10) * '0 1 0', ammo_str, '22 22 0', ammo_col, 0.98 * a_mul);

	// Right of big number: Reload bar OR Mag bar OR Standard ammo bar
	if (rlp > 0)
	{
		frac = rlp / 100;
		sn = sin(time * 10);
		bar_col = HUD2_CORAL;
		if (sn > 0)
			bar_col = HUD2_AMBER;
		HUD_Bar((x0 + 78) * '1 0 0' + (y0 + 14) * '0 1 0', '134 6 0', frac, bar_col, 0.96 * a_mul, '0.14 0.16 0.22', 0.85 * a_mul);
		HUD2_Text((x0 + 78) * '1 0 0' + (y0 + 23) * '0 1 0', "SWAPPING MAG...", '5 5 0', HUD2_AMBER, 0.92 * a_mul);
	}
	else if (magmax > 0)
	{
		frac = mag / magmax;
		bar_col = HUD2_MINT;
		if (mag * 4 <= magmax)
			bar_col = HUD2_CORAL;
		else if (mag * 2 <= magmax)
			bar_col = HUD2_AMBER;
		HUD_Bar((x0 + 78) * '1 0 0' + (y0 + 14) * '0 1 0', '134 6 0', frac, bar_col, 0.94 * a_mul, '0.14 0.16 0.22', 0.85 * a_mul);
		if (mag <= 0)
			HUD2_Text((x0 + 78) * '1 0 0' + (y0 + 23) * '0 1 0', "EMPTY - HIT [R]", '5 5 0', HUD2_CORAL, 0.96 * a_mul);
		else
			HUD2_Text((x0 + 78) * '1 0 0' + (y0 + 23) * '0 1 0', strcat("MAG ", ftos(mag), "/", ftos(magmax)), '5 5 0', HUD2_CREAM, 0.88 * a_mul);
	}
	else
	{
		if (is_melee)
		{
			frac = 1;
			bar_col = HUD2_MINT;
			sub_lbl = "UNLIMITED SWING";
		}
		else if (currentweap == IT_NAILGUN || currentweap == IT_SUPER_NAILGUN)
		{
			frac = active_ammo / 200;
			bar_col = HUD2_MINT;
			sub_lbl = "NAILS";
		}
		else if (currentweap == IT_GRENADE_LAUNCHER || currentweap == IT_ROCKET_LAUNCHER)
		{
			frac = active_ammo / 100;
			bar_col = HUD2_CORAL;
			sub_lbl = "ROCKETS";
		}
		else if (currentweap == IT_LIGHTNING || currentweap == IT_LASER_CANNON)
		{
			frac = active_ammo / 100;
			bar_col = HUD2_CYAN;
			sub_lbl = "CELLS";
		}
		else
		{
			frac = active_ammo / 100;
			bar_col = HUD2_AMBER;
			sub_lbl = "SHELLS";
		}
		HUD_Bar((x0 + 78) * '1 0 0' + (y0 + 14) * '0 1 0', '134 5 0', frac, bar_col, 0.90 * a_mul, '0.14 0.16 0.22', 0.85 * a_mul);
		HUD2_Text((x0 + 78) * '1 0 0' + (y0 + 23) * '0 1 0', sub_lbl, '5 5 0', HUD2_MUTED, 0.90 * a_mul);
	}

	// Compact reserve counts footer: S / N / R / C (+ P if prox > 0)
	drawfill((x0 + 6) * '1 0 0' + (y0 + 35) * '0 1 0', '206 1 0', HUD2_BORDER, 0.50 * a_mul, 0);

	c_s = HUD2_MUTED;
	if (shell_ammo > 0)
		c_s = HUD2_AMBER;
	c_n = HUD2_MUTED;
	if (nail_ammo > 0)
		c_n = HUD2_MINT;
	c_r = HUD2_MUTED;
	if (rocket_ammo > 0)
		c_r = HUD2_CORAL;
	c_c = HUD2_MUTED;
	if (cell_ammo > 0)
		c_c = HUD2_CYAN;

	HUD2_Text((x0 + 6) * '1 0 0' + (y0 + 40) * '0 1 0', strcat("S:", ftos(shell_ammo)), '5 5 0', c_s, 0.95 * a_mul);
	HUD2_Text((x0 + 48) * '1 0 0' + (y0 + 40) * '0 1 0', strcat("N:", ftos(nail_ammo)), '5 5 0', c_n, 0.95 * a_mul);
	HUD2_Text((x0 + 90) * '1 0 0' + (y0 + 40) * '0 1 0', strcat("R:", ftos(rocket_ammo)), '5 5 0', c_r, 0.95 * a_mul);
	HUD2_Text((x0 + 132) * '1 0 0' + (y0 + 40) * '0 1 0', strcat("C:", ftos(cell_ammo)), '5 5 0', c_c, 0.95 * a_mul);
};

/*
================
HUD2_DrawTopPill
Top-left compact Route 99 pill: Frags (plus CTF/Coop/Keys/Runes when active)
and a second compact row right below it ONLY when Powerups / Leader / Warmup /
Shield / Boost / Regen are active. Stays top-left to clear DrawLevelName & ToyDock.
================
*/
void(float hp, float is_leader, float a_mul) HUD2_DrawTopPill =
{
	local float frags, prot, boost, regen, warm, lheat, has_keys, has_runes;
	local float pw, px, bx, bw, has_status, ny;
	local string leader, main_s, status_s, warm_s;
	local vector accent;

	frags = getstati(STAT_FRAGS);
	prot = getstati(BMST_PROT);
	boost = getstati(BMST_BOOST);
	regen = getstati(BMST_REGEN);
	warm = getstati(BMST_WARMUP);
	lheat = getstati(BMST_LHEAT);
	leader = getstats(BMST_LEADER);

	// Primary Frags / Mode string
	if (ctf)
		main_s = strcat("B:", ftos(BLUE_CAPS), " R:", ftos(RED_CAPS), "  FRAGS ", ftos(frags));
	else if (coop && life_count > 0)
		main_s = strcat("LIVES ", ftos(life_count), "  FRAGS ", ftos(frags));
	else if (frag_limit > 0)
		main_s = strcat("FRAGS ", ftos(frags), "/", ftos(frag_limit));
	else
		main_s = strcat("FRAGS ", ftos(frags));

	has_keys = ((items & IT_KEY1) || (items & IT_KEY2));
	has_runes = ((items2 & RUNE_EP1) || (items2 & RUNE_EP2) || (items2 & RUNE_EP3) || (items2 & RUNE_EP4));

	pw = BM_UIStringWidth(main_s, FALSE, '5.5 5.5 0') + 14;
	if (has_keys)
	{
		if (items & IT_KEY1) pw = pw + 12;
		if (items & IT_KEY2) pw = pw + 12;
	}
	if (has_runes)
		pw = pw + 26;

	HUD2_Card('10 8 0', pw * '1 0 0' + '0 16 0', HUD2_AMBER, 0, a_mul);
	HUD2_Text('17 12.3 0', main_s, '5.5 5.5 0', HUD2_CREAM, 0.98 * a_mul);

	px = 17 + BM_UIStringWidth(main_s, FALSE, '5.5 5.5 0') + 4;
	if (items & IT_KEY1)
	{
		if (ctf)
			HUD_DrawPic(px * '1 0 0' + '0 11 0', '10 10 0', "gfx/bluflag", '1 1 1', 0.95 * a_mul);
		else
			HUD_DrawPic(px * '1 0 0' + '0 11 0', '10 10 0', "gfx/sb_key1", '1 1 1', 0.95 * a_mul);
		px = px + 12;
	}
	if (items & IT_KEY2)
	{
		if (ctf)
			HUD_DrawPic(px * '1 0 0' + '0 11 0', '10 10 0', "gfx/redflag", '1 1 1', 0.95 * a_mul);
		else
			HUD_DrawPic(px * '1 0 0' + '0 11 0', '10 10 0', "gfx/sb_key2", '1 1 1', 0.95 * a_mul);
		px = px + 12;
	}
	if (has_runes)
	{
		if (items2 & RUNE_EP1) HUD_DrawPic(px * '1 0 0' + '0 11 0', '6 10 0', "gfx/sb_sigil1", '1 1 1', 0.95 * a_mul);
		if (items2 & RUNE_EP2) HUD_DrawPic((px + 6) * '1 0 0' + '0 11 0', '6 10 0', "gfx/sb_sigil2", '1 1 1', 0.95 * a_mul);
		if (items2 & RUNE_EP3) HUD_DrawPic((px + 12) * '1 0 0' + '0 11 0', '6 10 0', "gfx/sb_sigil3", '1 1 1', 0.95 * a_mul);
		if (items2 & RUNE_EP4) HUD_DrawPic((px + 18) * '1 0 0' + '0 11 0', '6 10 0', "gfx/sb_sigil4", '1 1 1', 0.95 * a_mul);
	}

	// Second compact pill row (only when Powerups / Leader / Warmup / Shield / Boost / Regen are active)
	status_s = "";
	has_status = 0;
	accent = HUD2_MINT;

	if (quad_count > 0 || (items & IT_QUAD))
	{
		status_s = strcat(status_s, "^5QUAD ", ftos(quad_count), "s  ");
		has_status = 1;
	}
	if (pent_count > 0 || (items & IT_INVULNERABILITY))
	{
		status_s = strcat(status_s, "^1PENT ", ftos(pent_count), "s  ");
		accent = HUD2_CORAL;
		has_status = 1;
	}
	if (invis_count > 0 || (items & IT_INVISIBILITY))
	{
		status_s = strcat(status_s, "^3INVIS ", ftos(invis_count), "s  ");
		has_status = 1;
	}
	if (bio_count > 0 || (items & IT_SUIT))
	{
		status_s = strcat(status_s, "^2SUIT ", ftos(bio_count), "s  ");
		has_status = 1;
	}
	if (slow_count > 0)
	{
		status_s = strcat(status_s, "^6SLOW ", ftos(slow_count), "s  ");
		has_status = 1;
	}
	if (prot > 0 && hp > 0)
	{
		status_s = strcat(status_s, "^5SHIELD ", ftos(ceil(prot / 10)), "s  ");
		has_status = 1;
	}
	if (boost >= 15 && hp > 0)
	{
		status_s = strcat(status_s, "^2BOOST +", ftos(boost), "%  ");
		has_status = 1;
	}
	if (regen && hp > 0)
	{
		status_s = strcat(status_s, "^2+REGEN  ");
		has_status = 1;
	}
	if (leader != "" && lheat >= 4)
	{
		if (is_leader)
			status_s = strcat(status_s, "^3#1 LEAD +", ftos(lheat), "  ");
		else
			status_s = strcat(status_s, "^3LEAD:", leader, "(+", ftos(lheat), ")  ");
		accent = HUD2_AMBER;
		has_status = 1;
	}

	ny = 28;
	if (has_status)
	{
		bw = BM_UIStringWidth(status_s, TRUE, '5 5 0');
		bx = bw + 14;
		HUD2_Card('10 28 0', bx * '1 0 0' + '0 14 0', accent, 0, a_mul);
		BM_DrawColorShadow(17, 31.5, status_s, 5, 0.96 * a_mul);
		ny = 45;
	}

	if (warm)
	{
		warm_s = "^xfb2WARMUP  ^7F1^8+Bot  ^7F2^8-Bot  ^7F3^8LAN";
		bw = BM_UIStringWidth(warm_s, TRUE, '5 5 0');
		bx = bw + 14;
		HUD2_Card('10 0 0' + ny * '0 1 0', bx * '1 0 0' + '0 14 0', HUD2_AMBER, 0, a_mul);
		BM_DrawColorShadow(17, ny + 3.5, warm_s, 5, 0.94 * a_mul);
	}
};

/*
================
HUD_DrawStyle2
Main entrypoint for Style 2 ("ROUTE 99").
================
*/
void(float w, float h) HUD_DrawStyle2 =
{
	local float hp, armor, active_ammo, slot, is_melee, is_leader, a_mul;

	// Normalize to virtual console units (CSQC_UpdateView passes window pixels)
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
	is_leader = HUD_IsLeader();

	is_melee = 0;
	if (slot != 16 && slot != 18 && (currentweap == IT_AXE || currentweap == IT_CHAINSAW))
		is_melee = 1;

	// World & Bakersfield overlays (HUD_DrawWorldTagsAndVignette also draws BM_DrawCenterPrint)
	JP_DrawHUD(w, h, hp);
	HUD_DrawWorldTagsAndVignette(w, h, hp);
	HUD_DrawTopRightToys(w, h, hp);

	if (showscores)
		return;

	a_mul = sbar_alpha;
	if (a_mul <= 0)
		a_mul = 1;
	if (a_mul > 1)
		a_mul = 1;

	if (is_melee)
		HUD2_DrawBadgeCard(h, hp, armor, 1, is_leader, a_mul);
	else
		HUD2_DrawBadgeCard(h, hp, armor, active_ammo, is_leader, a_mul);

	HUD2_DrawReceiptCard(w, h, hp, active_ammo, is_melee, a_mul);
	HUD2_DrawTopPill(hp, is_leader, a_mul);
};
