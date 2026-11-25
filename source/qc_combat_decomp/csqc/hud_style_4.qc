/*
================
HUD STYLE 4: "ZEN ZERO" (Ultra-Clean Floating Esports Minimalist + Face Buddy)

Zero chunky background boxes. Crisp drop-shadowed bright white, sunshine gold,
mint, and sky cyan readouts + ultra-thin 2.5px glowing bars floating cleanly
along the bottom edge, keeping >93% of the viewport completely open.
================
*/

/*
================
S4_Clamp01
================
*/
float(float v) S4_Clamp01 =
{
	if (v < 0)
		return 0;
	if (v > 1)
		return 1;
	return v;
};

/*
================
S4_TextShadow / S4_CenterShadow / S4_RightShadow
Crisp drop-shadowed plain text helpers (no background boxes).
================
*/
void(vector pos, string s, vector sc, vector rgb, float a) S4_TextShadow =
{
	local vector p, sv;

	if (a <= 0 || s == "")
		return;
	p = pos_x * '1 0 0' + pos_y * '0 1 0';
	sv = BM_UIScaleVec(sc);
	drawstring(p + '-0.5 -0.5 0', s, sv, '0 0 0', 0.45 * a, 0);
	drawstring(p + '0.9 0.9 0', s, sv, '0 0 0', 0.88 * a, 0);
	drawstring(p, s, sv, rgb, a, 0);
};

void(vector cpos, string s, vector sc, vector rgb, float a) S4_CenterShadow =
{
	local float wd;

	if (a <= 0 || s == "")
		return;
	wd = BM_UIStringWidth(s, FALSE, sc);
	S4_TextShadow((cpos_x - wd * 0.5) * '1 0 0' + cpos_y * '0 1 0', s, sc, rgb, a);
};

void(vector rpos, string s, vector sc, vector rgb, float a) S4_RightShadow =
{
	local float wd;

	if (a <= 0 || s == "")
		return;
	wd = BM_UIStringWidth(s, FALSE, sc);
	S4_TextShadow((rpos_x - wd) * '1 0 0' + rpos_y * '0 1 0', s, sc, rgb, a);
};

/*
================
S4_GlowBar
Ultra-thin floating glowing bar with faint hairline track and leading spark.
If rtl != 0, the fill anchors to the right edge and drains toward the right.
================
*/
void(vector pos, float bw, float bh, float frac, vector fg, float a, float rtl) S4_GlowBar =
{
	local float f, fw, fx;

	if (a <= 0 || bw <= 0 || bh <= 0)
		return;

	f = S4_Clamp01(frac);

	// Hairline translucent track (no heavy box)
	drawfill(pos_x * '1 0 0' + pos_y * '0 1 0', bw * '1 0 0' + bh * '0 1 0', '0.06 0.09 0.14', 0.34 * a, 0);

	if (f <= 0)
		return;

	fw = bw * f;
	if (rtl)
		fx = pos_x + bw - fw;
	else
		fx = pos_x;

	// Soft ambient glow halo
	drawfill((fx - 1) * '1 0 0' + (pos_y - 0.8) * '0 1 0', (fw + 2) * '1 0 0' + (bh + 1.6) * '0 1 0', fg, 0.20 * a, 0);
	// Crisp 2.5px core fill
	drawfill(fx * '1 0 0' + pos_y * '0 1 0', fw * '1 0 0' + bh * '0 1 0', fg, 0.96 * a, 0);

	// Bright leading spark tip
	if (fw >= 2)
	{
		if (rtl)
			drawfill(fx * '1 0 0' + pos_y * '0 1 0', 1.5 * '1 0 0' + bh * '0 1 0', '1 1 1', 0.88 * a, 0);
		else
			drawfill((fx + fw - 1.5) * '1 0 0' + pos_y * '0 1 0', 1.5 * '1 0 0' + bh * '0 1 0', '1 1 1', 0.88 * a, 0);
	}
};

/*
================
S4_GetWeaponTag
Compact esports short tag for the active weapon.
================
*/
string(float slot, float active_weap) S4_GetWeaponTag =
{
	if (slot == 9)
		return "MEGA";
	if (slot == 10)
		return "ROBDob";
	if (slot == 11)
		return "G-JAR";
	if (slot == 12)
		return "PICKLE";
	if (slot == 13)
		return "NETSND";
	if (slot == 14)
		return "DOOKIE";
	if (slot == 15)
		return "WHEELS";
	if (slot == 16)
		return "M4A1";
	if (slot == 17)
		return "KYLE";
	if (slot == 18)
		return "GARAND";
	if (active_weap == IT_CHAINSAW)
		return "SAW";
	if (active_weap == IT_AXE)
		return "BONK";
	if (active_weap == IT_SHOTGUN)
		return "SG";
	if (active_weap == IT_SUPER_SHOTGUN)
		return "PUMP";
	if (active_weap == IT_NAILGUN)
		return "LAPTOP";
	if (active_weap == IT_SUPER_NAILGUN)
		return "MILKY";
	if (active_weap == IT_GRENADE_LAUNCHER)
		return "GL";
	if (active_weap == IT_ROCKET_LAUNCHER)
		return "RL";
	if (active_weap == IT_LIGHTNING)
		return "LG";
	if (active_weap == IT_LASER_CANNON)
		return "LASER";
	if (active_weap == 131072)
		return "BANANA";
	return "WEAP";
};

/*
================
S4_GetFaceVibe
Tiny emoticon + 1-word vibe floating right above the Quake head.
================
*/
string(float hp, float armor, float it_flags, float active_ammo, float is_melee, float prot, float is_leader) S4_GetFaceVibe =
{
	if (hp <= 0)
		return "[x_x] DED";
	if ((it_flags & IT_INVULNERABILITY) && (it_flags & IT_INVISIBILITY))
		return "[*_*] GHOST";
	if (it_flags & IT_INVULNERABILITY)
		return "[>_<] GODLIKE";
	if (it_flags & IT_QUAD)
		return "[*_*] JUICED";
	if (it_flags & IT_INVISIBILITY)
		return "[^_^] SNEAKY";
	if (it_flags & IT_SUIT)
		return "[O_O] HAZMAT";
	if (hp < 20)
		return "[x_x] HALP";
	if (hp < 40)
		return "[O_O] YIKES";
	if (!is_melee && active_ammo <= 0)
		return "[._.] EMPTY";
	if (prot > 0)
		return "[^_^] SHIELD";
	if (is_leader)
		return "[B-] KING";
	if (hp >= 60)
		return "[:D] VIBING";
	return "[o_o] CHILL";
};

/*
================
S4_DrawReserveChip
Draws an ultra-minimal reserve letter + count (muted when 0).
================
*/
void(float x, float y, string tag, float val, vector tag_col, float is_active, float a) S4_DrawReserveChip =
{
	local vector tc, vc;
	local float ta, va;
	local string num_s;

	if (val <= 0)
	{
		tc = '0.62 0.68 0.76';
		vc = '0.62 0.68 0.76';
		ta = 0.50 * a;
		va = 0.48 * a;
		num_s = "0";
	}
	else
	{
		tc = tag_col;
		vc = '0.98 0.99 1.0';
		if (is_active)
		{
			ta = 0.98 * a;
			va = 1.00 * a;
		}
		else
		{
			ta = 0.86 * a;
			va = 0.90 * a;
		}
		num_s = ftos(val);
	}

	S4_TextShadow(x * '1 0 0' + y * '0 1 0', tag, '5.5 5.5 0', tc, ta);
	S4_TextShadow((x + 7) * '1 0 0' + y * '0 1 0', num_s, '5.5 5.5 0', vc, va);
};

/*
================
S4_AppendToken
Appends a spaced badge token only when the second part is non-empty.
================
*/
string(string base, string tok) S4_AppendToken =
{
	if (tok == "")
		return base;
	if (base == "")
		return tok;
	return strcat(base, "   ", tok);
};

/*
================
S4_DrawTopBadges
Top-center minimal floating badges — rendered ONLY when active.
================
*/
void(float w, float hp, float a) S4_DrawTopBadges =
{
	local float cx, top_y, warm, prot, boost, regen, lheat, frags, is_lead, f, stat_colored;
	local string leader, pwr_s, stat_s, s;
	local vector pwr_col, stat_col;

	cx = w * 0.5;
	top_y = 6;

	warm = getstati(BMST_WARMUP);
	prot = getstati(BMST_PROT);
	boost = getstati(BMST_BOOST);
	regen = getstati(BMST_REGEN);
	lheat = getstati(BMST_LHEAT);
	leader = getstats(BMST_LEADER);
	frags = getstati(STAT_FRAGS);
	is_lead = HUD_IsLeader();

	// Warmup banner (ultra-clean floating line)
	if (warm)
	{
		f = sin(time * 3);
		S4_CenterShadow(cx * '1 0 0' + top_y * '0 1 0', "WARMUP  F1 +BOT  F2 -BOT  F3 LAN", '6 6 0', '1.0 0.85 0.25', (0.76 + 0.18 * f) * a);
		top_y = top_y + 10;
	}

	// Active Powerups
	pwr_s = "";
	pwr_col = '0.30 0.88 1.0';
	if (quad_count > 0 || (items & IT_QUAD))
	{
		if (quad_count > 0)
			s = strcat("QUAD ", ftos(quad_count), "s");
		else
			s = "QUAD";
		pwr_s = S4_AppendToken(pwr_s, s);
		pwr_col = '1.0 0.85 0.25';
	}
	if (pent_count > 0 || (items & IT_INVULNERABILITY))
	{
		if (pent_count > 0)
			s = strcat("PENT ", ftos(pent_count), "s");
		else
			s = "PENT";
		pwr_s = S4_AppendToken(pwr_s, s);
		pwr_col = '1.0 0.85 0.25';
	}
	if (invis_count > 0 || (items & IT_INVISIBILITY))
	{
		if (invis_count > 0)
			s = strcat("INVIS ", ftos(invis_count), "s");
		else
			s = "INVIS";
		pwr_s = S4_AppendToken(pwr_s, s);
	}
	if (bio_count > 0 || (items & IT_SUIT))
	{
		if (bio_count > 0)
			s = strcat("SUIT ", ftos(bio_count), "s");
		else
			s = "SUIT";
		pwr_s = S4_AppendToken(pwr_s, s);
	}
	if (slow_count > 0)
		pwr_s = S4_AppendToken(pwr_s, strcat("SLOW ", ftos(slow_count), "s"));

	if (pwr_s != "")
	{
		S4_CenterShadow(cx * '1 0 0' + top_y * '0 1 0', pwr_s, '6 6 0', pwr_col, 0.96 * a);
		drawfill((cx - 18) * '1 0 0' + (top_y + 7.5) * '0 1 0', '36 1 0', pwr_col, 0.70 * a, 0);
		top_y = top_y + 11;
	}

	// Leader / Shield / Boost / Regen / Frags / CTF / Coop / Keys (only when active)
	stat_s = "";
	stat_col = '0.98 0.99 1.0';
	stat_colored = 0;

	if (leader != "" && lheat >= 4)
	{
		if (is_lead)
			stat_s = S4_AppendToken(stat_s, strcat("IN LEAD +", ftos(lheat)));
		else
			stat_s = S4_AppendToken(stat_s, strcat("LEADER ", leader, " +", ftos(lheat)));
		stat_col = '1.0 0.85 0.25';
		stat_colored = 1;
	}
	if (prot > 0 && hp > 0)
	{
		stat_s = S4_AppendToken(stat_s, strcat("SHIELD ", ftos(ceil(prot / 10)), "s"));
		if (!stat_colored)
		{
			stat_col = '0.30 0.88 1.0';
			stat_colored = 1;
		}
	}
	if (boost >= 15 && hp > 0)
	{
		stat_s = S4_AppendToken(stat_s, strcat("BOOST +", ftos(boost), "%"));
		if (!stat_colored)
		{
			stat_col = '0.25 1.0 0.70';
			stat_colored = 1;
		}
	}
	if (regen && hp > 0)
		stat_s = S4_AppendToken(stat_s, "+REGEN");
	if (ctf)
		stat_s = S4_AppendToken(stat_s, strcat("BLU ", ftos(BLUE_CAPS), "  RED ", ftos(RED_CAPS)));
	else if (deathmatch && frags > 0)
	{
		if (frag_limit > 0)
			stat_s = S4_AppendToken(stat_s, strcat("FRAGS ", ftos(frags), "/", ftos(frag_limit)));
		else
			stat_s = S4_AppendToken(stat_s, strcat("FRAGS ", ftos(frags)));
	}
	if (coop && life_count > 0)
		stat_s = S4_AppendToken(stat_s, strcat("LIVES ", ftos(life_count)));
	if (!ctf && (items & IT_KEY1))
		stat_s = S4_AppendToken(stat_s, "SILVER KEY");
	if (!ctf && (items & IT_KEY2))
		stat_s = S4_AppendToken(stat_s, "GOLD KEY");

	if (stat_s != "")
		S4_CenterShadow(cx * '1 0 0' + top_y * '0 1 0', stat_s, '6 6 0', stat_col, 0.94 * a);
};

/*
================
HUD_DrawStyle4
Main entry point for Style 4: "ZEN ZERO".
================
*/
void(float w, float h) HUD_DrawStyle4 =
{
	local float hp, armor, ap_max, ap_frac, hp_frac, active_ammo, ammo_cap, ammo_frac;
	local float slot, mag, magmax, rlp, prot, is_lead, is_melee, a, pulse, low_pulse;
	local float cx, face_x, face_y, left_x, right_x, bar_w, bar_y, ammo_disp, ammo_w, res_x;
	local string face_pic, vibe, weap_tag, ammo_s;
	local vector c_white, c_gold, c_mint, c_cyan, c_red;
	local vector accent_col, hp_col, hp_bar_col, arm_col, ap_bar_col, ammo_col, ammo_bar_col, vibe_col;

	// 2D CSQC draw primitives use virtual console units (vid_conwidth x vid_conheight),
	// whereas CSQC_UpdateView(w, h) passes physical window pixels.
	w = vid_conwidth;
	h = vid_conheight;
	if (w <= 0)
		w = cvar("vid_conwidth");
	if (h <= 0)
		h = cvar("vid_conheight");
	if (w <= 0 || h <= 0)
		return;

	hp = player_health;

	// World tags, BM_DrawCenterPrint (bottom at h - 58), low-HP vignette, 3D leader marker, jetpack & top-right toys
	HUD_DrawWorldTagsAndVignette(w, h, hp);
	JP_DrawHUD(w, h, hp);
	HUD_DrawTopRightToys(w, h, hp);

	// Default sbar_alpha <= 0 to 1.0 (Zircon may not define sbar_alpha_fg)
	a = sbar_alpha;
	if (a <= 0)
		a = 1.0;
	if (a > 1)
		a = 1.0;
	if (showscores)
		return;

	c_white = '0.98 0.99 1.0';
	c_gold  = '1.0 0.85 0.25';
	c_mint  = '0.25 1.0 0.70';
	c_cyan  = '0.30 0.88 1.0';
	c_red   = '1.0 0.30 0.28';

	// Top-center minimal floating badges (only when active)
	S4_DrawTopBadges(w, hp, a);

	// Guard against hp <= 0 (Deathmatch opens scoreboard automatically when dead)
	if (hp <= 0)
		return;

	armor = getstati(STAT_ARMOR);
	if (armor < 0)
		armor = 0;
	ap_max = HUD_GetArmorMax(items);
	if (ap_max <= 0)
		ap_max = 100;
	ap_frac = S4_Clamp01(armor / ap_max);

	active_ammo = getstati(STAT_AMMO);
	if (active_ammo < 0)
		active_ammo = 0;

	slot = getstati(BMST_SLOT);
	mag = getstati(BMST_MAG);
	magmax = getstati(BMST_MAGMAX);
	rlp = getstati(BMST_RELOAD);
	prot = getstati(BMST_PROT);
	is_lead = HUD_IsLeader();
	is_melee = (currentweap == IT_AXE || currentweap == IT_CHAINSAW);

	pulse = sin(time * 7);
	low_pulse = 0.72 + 0.28 * pulse;

	// Layout anchors: everything floats cleanly along h - 53 .. h - 6 (well below BM_DrawCenterPrint at h - 58)
	cx = w * 0.5;
	face_x = cx - 17;
	face_y = h - 44;
	left_x = cx - 28;
	right_x = cx + 28;
	bar_w = 120;
	bar_y = h - 8.5;

	// ---- Center Quake Head (34x34 1:1) + Soft Halo + 2px Underline + Emoticon Vibe ----
	accent_col = c_mint;
	if (hp < 35)
		accent_col = c_red;
	else if ((items & (IT_QUAD | IT_INVULNERABILITY)) || is_lead)
		accent_col = c_gold;
	else if (hp < 75)
		accent_col = c_gold;
	else if ((items & IT_INVISIBILITY) || prot > 0)
		accent_col = c_cyan;

	// Subtle soft halo behind the head (zero chunky box)
	drawfill((face_x - 3) * '1 0 0' + (face_y - 3) * '0 1 0', '40 40 0', accent_col, 0.08 * a, 0);
	drawfill((face_x - 1) * '1 0 0' + (face_y - 1) * '0 1 0', '36 36 0', accent_col, 0.14 * a, 0);

	face_pic = HUD_GetFacePic(hp, items);
	HUD_DrawPic(face_x * '1 0 0' + face_y * '0 1 0', '34 34 0', face_pic, '1 1 1', 0.96 * a);

	// Crisp glowing 2px color underline beneath the head
	drawfill((cx - 21) * '1 0 0' + (h - 8.5) * '0 1 0', '42 3 0', accent_col, 0.22 * a, 0);
	drawfill((cx - 19) * '1 0 0' + (h - 8) * '0 1 0', '38 2 0', accent_col, 0.96 * a, 0);

	// Emoticon + 1-word vibe floating right above the head
	vibe = S4_GetFaceVibe(hp, armor, items, active_ammo, is_melee, prot, is_lead);
	vibe_col = accent_col;
	if (!is_melee && active_ammo <= 0 && hp >= 35)
		vibe_col = c_gold;
	S4_CenterShadow(cx * '1 0 0' + (h - 53) * '0 1 0', vibe, '6 6 0', vibe_col, 0.98 * a);

	// ---- Left of Quake Head: Armor + Health ----
	arm_col = HUD_GetStatColor(armor, 30, 75);
	if (armor > 0)
	{
		ap_bar_col = HUD_GetArmorColor(items);
		S4_GlowBar((left_x - bar_w) * '1 0 0' + (h - 44) * '0 1 0', 70, 2, ap_frac, ap_bar_col, 0.92 * a, 1);
		S4_RightShadow(left_x * '1 0 0' + (h - 50) * '0 1 0', ftos(armor), '14 14 0', arm_col, 0.98 * a);
	}
	else
	{
		S4_GlowBar((left_x - bar_w) * '1 0 0' + (h - 44) * '0 1 0', 70, 2, 0, c_cyan, 0.35 * a, 1);
		S4_RightShadow(left_x * '1 0 0' + (h - 50) * '0 1 0', "0", '14 14 0', arm_col, 0.55 * a);
	}

	hp_frac = S4_Clamp01(hp / 100);
	hp_col = HUD_GetStatColor(hp, 35, 75);
	hp_bar_col = c_mint;
	if (hp < 35)
		hp_bar_col = c_red;
	else if (hp > 100)
		hp_bar_col = c_cyan;
	else if (hp < 75)
		hp_bar_col = c_gold;

	S4_TextShadow((left_x - bar_w) * '1 0 0' + (h - 19) * '0 1 0', "HP", '6 6 0', hp_bar_col, 0.92 * a);
	if (hp < 35)
		S4_RightShadow(left_x * '1 0 0' + (h - 32) * '0 1 0', ftos(hp), '22 22 0', hp_col, low_pulse * a);
	else
		S4_RightShadow(left_x * '1 0 0' + (h - 32) * '0 1 0', ftos(hp), '22 22 0', hp_col, 0.98 * a);

	S4_GlowBar((left_x - bar_w) * '1 0 0' + bar_y * '0 1 0', bar_w, 2.5, hp_frac, hp_bar_col, 0.96 * a, 1);

	// ---- Right of Quake Head: Weapon Tag + Active Ammo + Mag/Reload Bar + Minimal Reserves ----
	weap_tag = S4_GetWeaponTag(slot, currentweap);
	if (slot == 16 || slot == 18)
		S4_TextShadow(right_x * '1 0 0' + (h - 46) * '0 1 0', weap_tag, '6 6 0', c_gold, 0.98 * a);
	else
		S4_TextShadow(right_x * '1 0 0' + (h - 46) * '0 1 0', weap_tag, '6 6 0', c_cyan, 0.96 * a);

	if (rlp > 0)
		S4_TextShadow((right_x + 44) * '1 0 0' + (h - 46) * '0 1 0', "RLD", '6 6 0', c_gold, low_pulse * a);

	// Primary Ammo readout + 2.5px Mag/Reload/Ammo bar
	if (is_melee)
	{
		ammo_s = "--";
		ammo_col = c_mint;
		ammo_bar_col = c_mint;
		ammo_frac = 1;
	}
	else
	{
		if (magmax > 0)
		{
			ammo_disp = mag;
			if (ammo_disp < 0)
				ammo_disp = 0;
			if (rlp > 0)
				ammo_frac = S4_Clamp01(rlp / 100);
			else
				ammo_frac = S4_Clamp01(ammo_disp / magmax);
		}
		else
		{
			ammo_disp = active_ammo;
			ammo_cap = 100;
			if (currentweap == IT_NAILGUN || currentweap == IT_SUPER_NAILGUN)
				ammo_cap = 200;
			ammo_frac = S4_Clamp01(ammo_disp / ammo_cap);
		}

		ammo_s = ftos(ammo_disp);
		ammo_col = HUD_GetAmmoColor(ammo_disp, currentweap, magmax);
		if (magmax > 0 && rlp > 0)
			ammo_bar_col = c_gold;
		else if (ammo_col_x == 1 && ammo_col_y < 0.5)
			ammo_bar_col = c_red;
		else if (ammo_col_z < 0.5)
			ammo_bar_col = c_gold;
		else
			ammo_bar_col = c_cyan;
	}

	S4_TextShadow(right_x * '1 0 0' + (h - 32) * '0 1 0', ammo_s, '22 22 0', ammo_col, 0.98 * a);
	if (is_melee)
		S4_GlowBar(right_x * '1 0 0' + bar_y * '0 1 0', bar_w, 2.5, ammo_frac, ammo_bar_col, 0.36 * a, 0);
	else
		S4_GlowBar(right_x * '1 0 0' + bar_y * '0 1 0', bar_w, 2.5, ammo_frac, ammo_bar_col, 0.96 * a, 0);

	// Ultra-minimal reserve numbers (S N R C, muted when 0; offset safely past large active ammo)
	ammo_w = BM_UIStringWidth(ammo_s, FALSE, '22 22 0');
	res_x = right_x + 68;
	if (right_x + ammo_w + 6 > res_x)
		res_x = right_x + ammo_w + 6;
	S4_DrawReserveChip(res_x, h - 28, "S", shell_ammo, c_gold, (items & IT_SHELLS), a);
	S4_DrawReserveChip(res_x + 27, h - 28, "N", nail_ammo, c_cyan, (items & IT_NAILS), a);
	S4_DrawReserveChip(res_x, h - 18, "R", rocket_ammo, c_red, (items & IT_ROCKETS), a);
	S4_DrawReserveChip(res_x + 27, h - 18, "C", cell_ammo, c_mint, (items & IT_CELLS), a);
};
