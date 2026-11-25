/*
================
SHARED CSQC HUD FOUNDATION (hud_common.qc)

Shared precaching, face/quip logic, primitive drawing helpers, and
Bakersfield world/status overlays for bm_hud_style 1..4.
bm_hud_style 0 keeps the original stock + Combat+ + bm_hud.qc untouched.
================
*/

float hud_prev_hp;
float hud_pain_until;

/*
================
HUD_CommonPrecache
Precache Quake face icons, HUD ammo/weapon/powerup/key/armor/mode pics.
Called once from CSQC_Init.
================
*/
void() HUD_CommonPrecache =
{
	// Quake faces (quake15/q15.pk3 HD PNGs)
	precache_pic("textures/face1.png");
	precache_pic("textures/face2.png");
	precache_pic("textures/face3.png");
	precache_pic("textures/face4.png");
	precache_pic("textures/face5.png");
	precache_pic("textures/face_p1.png");
	precache_pic("textures/face_p2.png");
	precache_pic("textures/face_p3.png");
	precache_pic("textures/face_p4.png");
	precache_pic("textures/face_p5.png");
	precache_pic("textures/face_quad.png");
	precache_pic("textures/face_invis.png");
	precache_pic("textures/face_invul.png");
	precache_pic("textures/face_invul2.png");
	precache_pic("textures/face_inv2.png");

	// Ammo & prox icons
	precache_pic("textures/HUD/HUD_shells.png");
	precache_pic("textures/HUD/HUD_nails.png");
	precache_pic("textures/HUD/HUD_rockets.png");
	precache_pic("textures/HUD/HUD_cells.png");
	precache_pic("textures/HUD/HUD_prox.png");
	precache_pic("textures/HUD/HUD_prox_empty.png");

	// Bakersfield custom weapon tiles
	precache_pic("gfx/hud_m4.tga");
	precache_pic("gfx/hud_garand.tga");
	precache_pic("gfx/hud_tommy.tga");

	// Keys, powerups, armor, runes, flags & modes
	precache_pic("gfx/sb_key1");
	precache_pic("gfx/sb_key2");
	precache_pic("gfx/sb_invis");
	precache_pic("gfx/sb_invuln");
	precache_pic("gfx/sb_suit");
	precache_pic("gfx/sb_quad");
	precache_pic("gfx/sb_armor1");
	precache_pic("gfx/sb_armor2");
	precache_pic("gfx/sb_armor3");
	precache_pic("gfx/sb_sigil1");
	precache_pic("gfx/sb_sigil2");
	precache_pic("gfx/sb_sigil3");
	precache_pic("gfx/sb_sigil4");
	precache_pic("gfx/bluflag");
	precache_pic("gfx/redflag");
	precache_pic("gfx/tmrune");
	precache_pic("textures/HUD/HUD_lives.png");
	precache_pic("textures/HUD/HUD_ctf_blue.png");
	precache_pic("textures/HUD/HUD_ctf_red.png");
};

/*
================
HUD_GetFacePic
Returns the Quake face texture path for the given HP and STAT_ITEMS bitmask,
tracking damage pain flashes (0.35s) via hud_prev_hp / hud_pain_until.
================
*/
string(float hp, float it_flags) HUD_GetFacePic =
{
	local float in_pain;

	if (time < hud_pain_until - 1)
		hud_pain_until = 0;
	if (hud_prev_hp > 0 && hp < hud_prev_hp && hp > 0)
		hud_pain_until = time + 0.35;
	hud_prev_hp = hp;

	if ((it_flags & IT_INVULNERABILITY) && (it_flags & IT_INVISIBILITY))
		return "textures/face_inv2.png";
	if (it_flags & IT_INVULNERABILITY)
		return "textures/face_invul.png";
	if (it_flags & IT_INVISIBILITY)
		return "textures/face_invis.png";
	if (it_flags & IT_QUAD)
		return "textures/face_quad.png";

	in_pain = (time < hud_pain_until);
	if (hp >= 80)
	{
		if (in_pain)
			return "textures/face_p1.png";
		return "textures/face1.png";
	}
	if (hp >= 60)
	{
		if (in_pain)
			return "textures/face_p2.png";
		return "textures/face2.png";
	}
	if (hp >= 40)
	{
		if (in_pain)
			return "textures/face_p3.png";
		return "textures/face3.png";
	}
	if (hp >= 20)
	{
		if (in_pain)
			return "textures/face_p4.png";
		return "textures/face4.png";
	}
	if (in_pain)
		return "textures/face_p5.png";
	return "textures/face5.png";
};

/*
================
HUD_DrawPic
Safe wrapper around drawpic that zeroes sz_z to avoid DarkPlaces console spam.
================
*/
void(vector pos, vector sz, string pic, vector rgb, float a) HUD_DrawPic =
{
	local vector p, s;

	p_x = pos_x;
	p_y = pos_y;
	p_z = 0;
	s_x = sz_x;
	s_y = sz_y;
	s_z = 0;
	drawpic(p, pic, s, rgb, a, 0);
};

/*
================
HUD_Box
Draws a filled rectangle with an optional crisp 1px+ border via drawfill.
================
*/
void(vector pos, vector sz, vector bg, float bg_a, vector border, float border_a, float border_w) HUD_Box =
{
	local vector p, s;
	local float bw, inner_h;

	p_x = pos_x;
	p_y = pos_y;
	p_z = 0;
	s_x = sz_x;
	s_y = sz_y;
	s_z = 0;

	if (bg_a > 0)
		drawfill(p, s, bg, bg_a, 0);

	if (border_w <= 0 || border_a <= 0)
		return;

	bw = border_w;
	if (bw * 2 > s_x)
		bw = s_x * 0.5;
	if (bw * 2 > s_y)
		bw = s_y * 0.5;

	// Top and bottom borders
	drawfill(p, s_x * '1 0 0' + bw * '0 1 0', border, border_a, 0);
	drawfill(p_x * '1 0 0' + (p_y + s_y - bw) * '0 1 0', s_x * '1 0 0' + bw * '0 1 0', border, border_a, 0);

	// Left and right inner vertical borders
	inner_h = s_y - bw * 2;
	if (inner_h > 0)
	{
		drawfill(p_x * '1 0 0' + (p_y + bw) * '0 1 0', bw * '1 0 0' + inner_h * '0 1 0', border, border_a, 0);
		drawfill((p_x + s_x - bw) * '1 0 0' + (p_y + bw) * '0 1 0', bw * '1 0 0' + inner_h * '0 1 0', border, border_a, 0);
	}
};

/*
================
HUD_Bar
Draws a clamped progress bar [0..1] over a background track.
================
*/
void(vector pos, vector sz, float frac, vector fg, float fg_a, vector bg, float bg_a) HUD_Bar =
{
	local float f;
	local vector p, s;

	f = frac;
	if (f < 0)
		f = 0;
	if (f > 1)
		f = 1;

	p_x = pos_x;
	p_y = pos_y;
	p_z = 0;
	s_x = sz_x;
	s_y = sz_y;
	s_z = 0;

	if (bg_a > 0)
		drawfill(p, s, bg, bg_a, 0);
	if (f > 0 && fg_a > 0)
		drawfill(p, (s_x * f) * '1 0 0' + s_y * '0 1 0', fg, fg_a, 0);
};

/*
================
HUD_DrawRightText / HUD_DrawCenterText
Plain drawstring alignment helpers using stringwidth.
================
*/
void(vector right_pos, string s, vector sc, vector rgb, float a) HUD_DrawRightText =
{
	local float wd;
	local vector p, usc;

	usc = BM_UIScaleVec(sc);
	wd = stringwidth(s, FALSE, usc);
	p_x = right_pos_x - wd;
	p_y = right_pos_y;
	p_z = 0;
	drawstring(p, s, usc, rgb, a, 0);
};

void(vector center_pos, string s, vector sc, vector rgb, float a) HUD_DrawCenterText =
{
	local float wd;
	local vector p, usc;

	usc = BM_UIScaleVec(sc);
	wd = stringwidth(s, FALSE, usc);
	p_x = center_pos_x - wd * 0.5;
	p_y = center_pos_y;
	p_z = 0;
	if (BM_GetUIFont() > 0)
		drawstring(p + '0.7 0.7 0', s, usc, '0 0 0', 0.78 * a, 0);
	drawstring(p, s, usc, rgb, a, 0);
};

/*
================
HUD_DrawRightColorText / HUD_DrawCenterColorText
Color-coded (^1..^9, ^xRGB) drawstring alignment helpers.
================
*/
void(vector right_pos, string s, vector sc, float a) HUD_DrawRightColorText =
{
	local float wd;
	local vector p, usc;
	local string plain;

	usc = BM_UIScaleVec(sc);
	wd = stringwidth(s, TRUE, usc);
	p_x = right_pos_x - wd;
	p_y = right_pos_y;
	p_z = 0;
	if (BM_GetUIFont() > 0)
	{
		plain = strdecolorize(s);
		drawstring(p + '0.7 0.7 0', plain, usc, '0 0 0', 0.80 * a, 0);
	}
	drawcolorcodedstring(p, s, usc, a, 0);
};

void(vector center_pos, string s, vector sc, float a) HUD_DrawCenterColorText =
{
	local float wd;
	local vector p, usc;
	local string plain;

	usc = BM_UIScaleVec(sc);
	wd = stringwidth(s, TRUE, usc);
	p_x = center_pos_x - wd * 0.5;
	p_y = center_pos_y;
	p_z = 0;
	if (BM_GetUIFont() > 0)
	{
		plain = strdecolorize(s);
		drawstring(p + '0.7 0.7 0', plain, usc, '0 0 0', 0.80 * a, 0);
	}
	drawcolorcodedstring(p, s, usc, a, 0);
};

/*
================
HUD_GetQuip
Short witty mood quip for the Quake head based on current combat state.
================
*/
string(float hp, float armor, float it_flags, float active_ammo, float is_leader) HUD_GetQuip =
{
	if (hp <= 0)
		return "Respawn time...";
	if ((it_flags & IT_INVULNERABILITY) && (it_flags & IT_INVISIBILITY))
		return "GHOST GOD MODE!";
	if (it_flags & IT_INVULNERABILITY)
		return "666! CANT TOUCH ME";
	if (it_flags & IT_QUAD)
		return "4X DAMAGE TIME!";
	if (it_flags & IT_INVISIBILITY)
		return "SHH... SNEAKY";
	if (it_flags & IT_SUIT)
		return "SLIME PROOF";
	if (hp < 20)
		return "SEND MEDKIT!!";
	if (hp < 40)
		return "THIS IS FINE.";
	if (active_ammo <= 0)
		return "CLICK! NO AMMO!";
	if (is_leader)
		return "TARGET #1 (+LEAD)";
	if (hp >= 100 && armor >= 150)
		return "TANKED UP!";
	if (hp >= 80 && armor >= 50)
		return "READY TO FRAG";
	return "LOCKED & LOADED";
};

/*
================
HUD_GetArmorColor / HUD_GetArmorMax / HUD_GetWeaponName / HUD_GetWeaponPic / HUD_IsLeader
Shared state helpers for armor tier, weapon identity, and leader status.
================
*/
vector(float it_flags) HUD_GetArmorColor =
{
	if (it_flags & IT_ARMOR3)
		return '0.95 0.28 0.22';
	if (it_flags & IT_ARMOR2)
		return '0.96 0.80 0.20';
	if (it_flags & IT_ARMOR1)
		return '0.28 0.88 0.38';
	return '0.52 0.56 0.62';
};

/*
================
HUD_GetStatColor / HUD_GetAmmoColor
Shared red/yellow/white stat colorization (red = low, yellow = med, white = high).
================
*/
vector(float val, float low_t, float med_t) HUD_GetStatColor =
{
	if (val < low_t)
		return '1.0 0.22 0.22';
	if (val < med_t)
		return '1.0 0.88 0.15';
	return '1.0 1.0 1.0';
};

vector(float ammo_val, float active_weap, float magmax) HUD_GetAmmoColor =
{
	local float low_t, med_t;

	if (magmax > 0)
	{
		low_t = floor(magmax * 0.25);
		if (low_t < 2)
			low_t = 2;
		med_t = floor(magmax * 0.55);
		if (med_t < 4)
			med_t = 4;
	}
	else if (active_weap == IT_ROCKET_LAUNCHER || active_weap == IT_GRENADE_LAUNCHER)
	{
		low_t = 3;
		med_t = 6;
	}
	else
	{
		low_t = 8;
		med_t = 18;
	}
	return HUD_GetStatColor(ammo_val, low_t, med_t);
};

float(float it_flags) HUD_GetArmorMax =
{
	if (it_flags & IT_ARMOR3)
		return 200;
	if (it_flags & IT_ARMOR2)
		return 150;
	return 100;
};

string(float slot, float active_weap) HUD_GetWeaponName =
{
	if (slot == 16)
		return "M4A1";
	if (slot == 18)
		return "GARAND";
	if (active_weap == IT_CHAINSAW)
		return "CHAINSAW";
	if (active_weap == IT_AXE)
		return "AXE";
	if (active_weap == IT_SHOTGUN)
		return "SHOTGUN";
	if (active_weap == IT_SUPER_SHOTGUN)
		return "PUMP SHOTGUN";
	if (active_weap == IT_NAILGUN)
		return "NAILGUN";
	if (active_weap == IT_SUPER_NAILGUN)
		return "SUPER NAILGUN";
	if (active_weap == IT_GRENADE_LAUNCHER)
		return "GRENADE LAUNCHER";
	if (active_weap == IT_ROCKET_LAUNCHER)
		return "ROCKET LAUNCHER";
	if (active_weap == IT_LIGHTNING)
		return "THUNDERBOLT";
	if (active_weap == IT_LASER_CANNON)
		return "LASER CANNON";
	return "WEAPON";
};

string(float slot, float active_weap) HUD_GetWeaponPic =
{
	if (slot == 16)
		return "gfx/hud_m4.tga";
	if (slot == 18)
		return "gfx/hud_garand.tga";
	if (active_weap == IT_CHAINSAW)
		return "textures/HUD/HUD_saw_select";
	if (active_weap == IT_SHOTGUN)
		return "gfx/inv2_shotgun";
	if (active_weap == IT_SUPER_SHOTGUN)
		return "gfx/dn3sg/hud_icon.png";
	if (active_weap == IT_NAILGUN)
		return "gfx/inv2_nailgun";
	if (active_weap == IT_SUPER_NAILGUN)
		return "gfx/inv2_snailgun";
	if (active_weap == IT_GRENADE_LAUNCHER)
		return "gfx/inv2_rlaunch";
	if (active_weap == IT_ROCKET_LAUNCHER)
		return "gfx/inv2_srlaunch";
	if (active_weap == IT_LIGHTNING)
		return "gfx/inv2_lightng";
	if (active_weap == IT_LASER_CANNON)
		return "textures/HUD/HUD_Laser_select";
	return "";
};

float() HUD_IsLeader =
{
	local string leader;
	local float heat, lheat;

	leader = getstats(BMST_LEADER);
	lheat = getstati(BMST_LHEAT);
	heat = getstati(BMST_HEAT);
	if (leader != "" && lheat >= 4 && heat >= 4 && heat == lheat)
		return 1;
	return 0;
};

/*
================
HUD_DrawWorldTagsAndVignette
3D bot/player tags, 3D leader wall marker, low-HP vignette, and lower centerprint toast.
================
*/
void(float w, float h, float hp) HUD_DrawWorldTagsAndVignette =
{
	local float intro_on, f, a;
	local string leader;
	local vector lp, sp;

	intro_on = getstati(BMST_INTRO);
	if (intro_on <= 0 && !intermission)
	{
		BM_DrawBotTags(w, h);
		BM_DrawPlayerTags(w, h);
	}
	BM_DrawCenterPrint(w, h);

	// Low health red vignette
	if (hp > 0 && hp < 40)
	{
		f = sin(time * 6);
		a = (1 - hp / 40) * (0.5 + 0.12 * f);
		drawfill('0 0 0', w * '1 0 0' + (h * 0.12) * '0 1 0', '0.8 0 0', a, 0);
		drawfill((h * 0.88) * '0 1 0', w * '1 0 0' + (h * 0.12) * '0 1 0', '0.8 0 0', a, 0);
		drawfill('0 0 0', (w * 0.08) * '1 0 0' + h * '0 1 0', '0.8 0 0', a, 0);
		drawfill((w * 0.92) * '1 0 0', (w * 0.08) * '1 0 0' + h * '0 1 0', '0.8 0 0', a, 0);
	}

	// Leader 3D wall marker
	leader = getstats(BMST_LEADER);
	if (getstati(BMST_LSHOW) && leader != "")
	{
		lp_x = getstati(BMST_LX);
		lp_y = getstati(BMST_LY);
		lp_z = getstati(BMST_LZ);
		lp_z = lp_z + 44;
		sp = cs_project(lp);
		if (sp_z > 0 && sp_x > 0 && sp_x < w && sp_y > 0 && sp_y < h)
		{
			f = sin(time * 8);
			BM_Centered(sp_x, sp_y - 10, strcat("^3", leader), 5, '1 1 1', 0.82);
			BM_Centered(sp_x, sp_y - 3, "^3v", 6, '1 1 1', 0.70 + 0.25 * f);
		}
	}
};

/*
================
HUD_DrawTopRightToys
Top-right bot count/hint and Party Toy Dock (calls BM_DrawToyDock).
================
*/
void(float w, float h, float hp) HUD_DrawTopRightToys =
{
	local float intro_on, botcnt, ty;
	local string s;

	bm_topright_y = 8;
	intro_on = getstati(BMST_INTRO);
	if (intro_on > 0 || intermission)
		return;

	botcnt = getstati(BMST_BOTCNT);
	ty = 8;
	if (deathmatch && (botcnt > 0 || time < 20))
	{
		if (botcnt > 0)
			s = strcat("^xfa3BOTS: ^7", ftos(botcnt), "  ^8(^3F1^8 +  ^3F2^8 -)");
		else
			s = "^8Press ^3F1^8 +Bot  ^3F2^8 -Bot";
		BM_ShadowColorRight(w - 8, 8, s, 5, 0.88);
		ty = 17;
	}
	bm_topright_y = ty;
	if (deathmatch)
		BM_DrawToyDock(w, h, hp, ty);
};

/*
================
HUD_DrawStatusBanners
Warmup banner, leader banner, comeback boost, spawn shield, regen, and reload bar.
================
*/
void(float w, float h, float hp) HUD_DrawStatusBanners =
{
	local float cx, cy, rlp, prot, heat, boost, regen, warm, lheat, f, pw, a;
	local string leader, s;

	cx = w * 0.5;
	cy = h * 0.5;
	rlp = getstati(BMST_RELOAD);
	prot = getstati(BMST_PROT);
	heat = getstati(BMST_HEAT);
	boost = getstati(BMST_BOOST);
	regen = getstati(BMST_REGEN);
	warm = getstati(BMST_WARMUP);
	lheat = getstati(BMST_LHEAT);
	leader = getstats(BMST_LEADER);

	if (rlp > 0 && hp > 0)
	{
		f = sin(time * 9);
		BM_Centered(cx, cy + h * 0.11, "^xfe4RELOADING", 6, '1 1 1', 0.80 + 0.15 * f);
		pw = 42;
		drawfill((cx - pw * 0.5) * '1 0 0' + (cy + h * 0.11 + 8) * '0 1 0', pw * '1 0 0' + '0 2 0', '0 0 0', 0.55, 0);
		drawfill((cx - pw * 0.5) * '1 0 0' + (cy + h * 0.11 + 8) * '0 1 0', (pw * rlp / 100) * '1 0 0' + '0 2 0', '1 0.85 0.3', 0.95, 0);
	}

	if (warm)
	{
		f = sin(time * 3);
		a = 0.78 + 0.18 * f;
		if (time > 15)
			a = 0.65;
		BM_ShadowColorRight(w - 8, bm_topright_y, "^xfd0WARMUP^7 - ^3F1^7 +Bot  ^3F2^7 -Bot  ^3F3^7 LAN", 5, a);
		bm_topright_y = bm_topright_y + 9;
	}

	if (leader != "" && lheat >= 4)
	{
		if (heat >= 4 && heat == lheat)
			s = strcat("^3In the lead (+", ftos(lheat), ")");
		else
			s = strcat("^3Leader: ", leader, "^3 (+", ftos(lheat), ")");
		BM_ShadowColorRight(w - 8, bm_topright_y, s, 5, 0.88);
		bm_topright_y = bm_topright_y + 9;
	}

	if (boost >= 15 && hp > 0)
	{
		BM_ShadowColorRight(w - 8, bm_topright_y, strcat("^2boost +", ftos(boost), "%"), 5, 0.86);
		bm_topright_y = bm_topright_y + 9;
	}

	if (prot > 0 && hp > 0)
	{
		BM_ShadowColorRight(w - 8, bm_topright_y, strcat("^5SHIELD ", ftos(ceil(prot / 10))), 5, 0.88);
		bm_topright_y = bm_topright_y + 9;
	}

	if (regen && hp > 0)
	{
		f = sin(time * 5);
		BM_ShadowColorRight(w - 8, bm_topright_y, "^2+ regen", 5, 0.65 + 0.25 * f);
		bm_topright_y = bm_topright_y + 9;
	}
	BM_DrawBakoDestructHUD(w);
};

/*
================
HUD_DrawWorldOverlays
Draws all essential Bakersfield world & status overlays (tags, centerprint,
jetpack tank, low-HP vignette, toy dock, leader marker, warmup/shield/regen/boost/reload)
WITHOUT drawing the old dark HUD, gun menu, ammo strip, or legacy M4/Garand tile.
================
*/
void(float w, float h, float hp) HUD_DrawWorldOverlays =
{
	JP_DrawHUD(w, h, hp);
	HUD_DrawWorldTagsAndVignette(w, h, hp);
	HUD_DrawTopRightToys(w, h, hp);
	HUD_DrawStatusBanners(w, h, hp);
};
