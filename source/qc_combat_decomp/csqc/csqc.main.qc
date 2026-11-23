//Decompiled code. Please respect the original copyright.

void() BM_Veh_ClearBindmap2 =
{
	local float k;
	local string b;

	for (k = 1; k < 768; k = k + 1)
	{
		b = getkeybind_bindmap(k, 2);
		if (b != "")
			setkeybind_bindmap(k, "", 2);
	}
};

// TRUE if the Vehicle Config (bindmap 1) has at least one key for cmd (findkeysforcommand pads empty slots with -1).
float(string cmd) BM_Veh_HasVehKey =
{
	local string raw;
	local float n, i;

	raw = findkeysforcommand(cmd, 1);
	n = tokenize(raw);
	for (i = 0; i < n; i = i + 1)
		if (stof(argv(i)) > 0)
			return TRUE;
	return FALSE;
};

void(string cmd) BM_Veh_BlockFpsCmd =
{
	local string raw;
	local float n, i, kn;

	// Only hide the on-foot key when the vehicle config has its own key for this action; otherwise the player would
	// have no key at all for it in a vehicle (e.g. no way to get out). Audit 2026-11-23, CL-02.
	if (!BM_Veh_HasVehKey(cmd))
		return;
	raw = findkeysforcommand(cmd, 0);
	if (raw == "")
		return;
	n = tokenize(raw);
	for (i = 0; i < n; i = i + 1)
	{
		kn = stof(argv(i));
		if (kn > 0 && kn < 768)
			setkeybind_bindmap(kn, "_bm_nop", 2);
	}
};

void() BM_Veh_EnsureDefaults =
{
	local float k, has_any;
	local string b;

	has_any = FALSE;
	for (k = 1; k < 768; k = k + 1)
	{
		b = getkeybind_bindmap(k, 1);
		if (b != "")
		{
			has_any = TRUE;
			break;
		}
	}
	if (!has_any)
	{
		k = stringtokeynum("w"); if (k > 0) setkeybind_bindmap(k, "+forward", 1);
		k = stringtokeynum("s"); if (k > 0) setkeybind_bindmap(k, "+back", 1);
		k = stringtokeynum("a"); if (k > 0) setkeybind_bindmap(k, "+moveleft", 1);
		k = stringtokeynum("d"); if (k > 0) setkeybind_bindmap(k, "+moveright", 1);
		k = stringtokeynum("SPACE"); if (k > 0) setkeybind_bindmap(k, "+jump", 1);
		k = stringtokeynum("SHIFT"); if (k > 0) setkeybind_bindmap(k, "+button4", 1);
		k = stringtokeynum("MOUSE1"); if (k > 0) setkeybind_bindmap(k, "+attack", 1);
		k = stringtokeynum("h"); if (k > 0) setkeybind_bindmap(k, "impulse 86", 1);
		k = stringtokeynum("k"); if (k > 0) setkeybind_bindmap(k, "impulse 87", 1);
	}
	cvar_set("bm_veh_init", "1");
};

void(float enable) BM_Veh_ApplyBindMode =
{
	local float k;
	local string b;

	localcmd("-forward; -back; -moveleft; -moveright; -jump; -attack; -button4\n");
	BM_Veh_ClearBindmap2();
	if (!enable)
	{
		localcmd("in_bindmap 0 0\n");
		return;
	}

	// Block FPS keys for the 9 vehicle actions so old on-foot binds never bleed through
	BM_Veh_BlockFpsCmd("+forward");
	BM_Veh_BlockFpsCmd("+back");
	BM_Veh_BlockFpsCmd("+moveleft");
	BM_Veh_BlockFpsCmd("+moveright");
	BM_Veh_BlockFpsCmd("+jump");
	BM_Veh_BlockFpsCmd("+button4");
	BM_Veh_BlockFpsCmd("+attack");
	BM_Veh_BlockFpsCmd("impulse 86");
	BM_Veh_BlockFpsCmd("impulse 87");

	// Apply Vehicle Config (bindmap 1) on top
	for (k = 1; k < 768; k = k + 1)
	{
		b = getkeybind_bindmap(k, 1);
		if (b != "")
			setkeybind_bindmap(k, b, 2);
	}
	localcmd("in_bindmap 2 0\n");
};

void(float bm_intro) BM_Veh_UpdateBindMode =
{
	local float veh_cfg, hp, tmask, mmt_on, jb_on, want_veh, rev;

	veh_cfg = (cvar("bm_veh_config") != 0);
	if (veh_cfg && cvar("bm_veh_init") == 0)
	{
		BM_Veh_EnsureDefaults();
		return;
	}
	hp = getstati(STAT_HEALTH);
	tmask = getstati(BMST_TOYMASK);
	mmt_on = getstati(86);
	jb_on = getstati(93);
	want_veh = (veh_cfg && !bm_intro && hp > 0 && !intermission && (((tmask & 512) != 0) || mmt_on > 0 || jb_on > 0));
	rev = cvar("bm_veh_rev");
	if (want_veh != bm_veh_active || (want_veh && rev != bm_veh_last_rev))
	{
		bm_veh_active = want_veh;
		bm_veh_last_rev = rev;
		BM_Veh_ApplyBindMode(want_veh);
	}
};

void() CSQC_Init =
{

	mouse = cvar("sensitivity");
	if ((mouse <= 0))
	{
		mouse = 3;
		cvar_set("sensitivity", "3");
	}
	registercvar("hud_proxcount_big", "1");
	registercvar("hud_colored_ammo", "1");
	addlives = cvar("coop_lives");
	clonemonsters = cvar("clonemonsters");
	registercvar("hud_showtitle", "1");
	registercvar("bm_hud_style", "0");
	registercvar("bm_ui_font", "1");
	registercvar("bm_minimap", "1");
	registercvar("bm_minimap_range", "1400");
	registercvar("bm_minimap_size", "39");
	registercvar("bm_minimap_x", "8");
	registercvar("bm_minimap_y", "8");
	registercvar("bm_minimap_alpha", "0.62");
	registercvar("bm_minimap_bg_alpha", "0.42");
	registercvar("bm_minimap_rotate", "1");
	registercvar("bm_minimap_compass", "1");
	registercvar("bm_minimap_fov", "0.07");
	registercvar("bm_veh_config", "0");
	registercvar("bm_veh_init", "0");
	registercvar("bm_veh_rev", "0");
	bm_veh_active = FALSE;
	bm_veh_last_rev = cvar("bm_veh_rev");
	BM_Veh_ClearBindmap2();
	localcmd("in_bindmap 0 0\n");
	init_servercmds();
	BM_TraceCullSetup ();
	stGtype = gametype;
	precache_pic("gfx/milkdrips");
	precache_pic("textures/HUD/HUD_shells.png");
	precache_pic("textures/HUD/HUD_nails.png");
	precache_pic("textures/HUD/HUD_rockets.png");
	precache_pic("textures/HUD/HUD_cells.png");
	precache_pic("textures/HUD/HUD_Laser.png");
	precache_pic("textures/HUD/HUD_Laser_select");
	precache_pic("textures/HUD/HUD_saw");
	precache_pic("textures/HUD/HUD_saw_select");
	precache_pic("textures/HUD/HUD_prox.png");
	precache_pic("textures/HUD/HUD_prox_empty.png");
	precache_pic("textures/HUD/Fraglimit_banner.png");
	precache_pic("gfx/sb_quad");
	precache_pic("gfx/sb_invuln");
	precache_pic("gfx/sb_invis");
	precache_pic("gfx/sb_suit");
	precache_pic("gfx/inv_shotgun");
	precache_pic("gfx/inv_sshotgun");
	precache_pic("gfx/inv_nailgun");
	precache_pic("gfx/inv_snailgun");
	precache_pic("gfx/inv_rlaunch");
	precache_pic("gfx/inv_srlaunch");
	precache_pic("gfx/inv_lightng");
	precache_pic("gfx/inv2_shotgun");
	precache_pic("gfx/inv2_sshotgun");
	precache_pic("gfx/inv2_nailgun");
	precache_pic("gfx/inv2_snailgun");
	precache_pic("gfx/inv2_rlaunch");
	precache_pic("gfx/inv2_srlaunch");
	precache_pic("gfx/inv2_lightng");
	precache_sound("misc/menu1.wav");
	precache_sound("misc/menu2.wav");
	precache_sound("misc/menu3.wav");
	precache_sound("misc/corpsegib.wav");
	precache_model("progs/casing.mdl");
	precache_model("progs/nailcasing.mdl");
	precache_model("progs/missilecasing.mdl");
	precache_model("progs/s_smoke_muzz.spr");
	precache_sound("weapons/casings1.wav");
	precache_sound("weapons/casings2.wav");
	precache_sound("weapons/casings3.wav");
	precache_sound("weapons/nailcase1.wav");
	precache_sound("weapons/nailcase2.wav");
	precache_sound("weapons/nailcase3.wav");
	precache_sound("weapons/rockcase1.wav");
	precache_sound("weapons/rockcase.wav");
	precache_sound("robhead/key1.wav");
	precache_sound("robhead/key2.wav");
	precache_sound("robhead/key3.wav");
	precache_sound("robhead/key4.wav");
	precache_sound("robhead/key_enter.wav");
	precache_sound("robhead/key_beep.wav");
	mouse = cvar("sensitivity");
	mp_temp = maxplayers;
	if (!maxplayers)
	{
		maxplayers = 16;
	}
	if (isSingle())
	{
		maxplayers = 1;
	}
	if ((cvar("shells_small") > 20))
	{
		ammocap = "Double";
	}
	else
	{
		ammocap = "Normal";
	}
	canPause = isLocal();
	mp_change = maxplayers;
	check_gamemode();
	loadScreenSize();
	BM_IntroPrecache();
	HUD_CommonPrecache();
	precache_pic("progs/mmt_aim_beam");
};

void() CSQC_Shutdown =
{
	local float j;

	if (bm_veh_active)
	{
		bm_veh_active = FALSE;
		BM_Veh_ApplyBindMode(FALSE);
	}
	else
	{
		BM_Veh_ClearBindmap2();
		localcmd("in_bindmap 0 0\n");
	}
	if ((menu_was_open && (mouse > 0)))
		cvar_set("sensitivity", ftos(mouse));
	if (maplist_loaded)
	{
		j = 0;
		while ((j < mapcount))
		{
			strunzone(mapstring[j]);
			strunzone(maplist[j]);
			j = j + 1;
		}
		maplist_loaded = 0;
	}
	maxplayers = mp_temp;
};

// Mega Man Tank trajectory aiming line & impact reticle (stats 86..92 from mm_tank.qc; the server sends them as
// clientstat type 2 = whole numbers, so read them with getstati: getstatf would reinterpret the int bits as a float)
vector(vector a, vector b) MMT_Cross =
{
	local vector c;
	c_x = a_y * b_z - a_z * b_y;
	c_y = a_z * b_x - a_x * b_z;
	c_z = a_x * b_y - a_y * b_x;
	return c;
};

void() MMT_DrawAimLine3D =
{
	local float act, dist0, dist1, w0, w1, alpha;
	local vector p0, p1, cam_org, dir, s0, s1, col, c;

	act = getstati(86);
	if (act <= 0)
		return;

	p0_x = getstati(87);
	p0_y = getstati(88);
	p0_z = getstati(89);
	p1_x = getstati(90);
	p1_y = getstati(91);
	p1_z = getstati(92);
	if (vlen(p1 - p0) < 2)
		return;

	cam_org = getpropertyvec(VF_ORIGIN);
	dir = normalize(p1 - p0);
	s0 = MMT_Cross(dir, p0 - cam_org);
	if (vlen(s0) < 0.001)
		s0 = '0 1 0';
	else
		s0 = normalize(s0);
	s1 = MMT_Cross(dir, p1 - cam_org);
	if (vlen(s1) < 0.001)
		s1 = s0;
	else
		s1 = normalize(s1);

	dist0 = vlen(p0 - cam_org);
	dist1 = vlen(p1 - cam_org);
	w0 = bound(0.9, dist0 * 0.0022, 2.2);
	w1 = bound(1.2, dist1 * 0.0022, 6.0);

	if (act == 1)
	{
		col = '0.20 0.96 1.00';
		alpha = 0.85;
	}
	else
	{
		col = '1.00 0.62 0.16';
		alpha = 0.45;
		w0 = w0 * 0.75;
		w1 = w1 * 0.75;
	}
	c = col * alpha;

	R_BeginPolygon("progs/mmt_aim_beam", 0, FALSE);
	R_PolygonVertex(p0 - s0 * w0, '0 0 0', c, alpha);
	R_PolygonVertex(p0 + s0 * w0, '0 1 0', c, alpha);
	R_PolygonVertex(p1 + s1 * w1, '1 1 0', c, alpha);
	R_PolygonVertex(p1 - s1 * w1, '1 0 0', c, alpha);
	R_EndPolygon();
};

void(float w, float h) MMT_DrawAimReticle2D =
{
	local float act, r;
	local vector p1, sp, col;

	act = getstati(86);
	if (act <= 0)
		return;

	p1_x = getstati(90);
	p1_y = getstati(91);
	p1_z = getstati(92);
	sp = cs_project(p1);
	if (sp_z <= 0 || sp_x < 6 || sp_x > w - 6 || sp_y < 6 || sp_y > h - 6)
		return;

	if (act == 1)
	{
		col = '0.20 0.96 1.00';
		r = 6;
	}
	else
	{
		col = '1.00 0.62 0.16';
		r = 5;
	}
	// Four crisp corner ticks around the exact projectile impact point
	drawfill((sp_x - r) * '1 0 0' + (sp_y - 0.5) * '0 1 0', '3 1 0', col, 0.9, 0);
	drawfill((sp_x + r - 3) * '1 0 0' + (sp_y - 0.5) * '0 1 0', '3 1 0', col, 0.9, 0);
	drawfill((sp_x - 0.5) * '1 0 0' + (sp_y - r) * '0 1 0', '1 3 0', col, 0.9, 0);
	drawfill((sp_x - 0.5) * '1 0 0' + (sp_y + r - 3) * '0 1 0', '1 3 0', col, 0.9, 0);
};

void(float w, float h) CSQC_UpdateView =
{
	local float bm_intro, hud_style, cw, ch, fd_mode, jb_active;

	initConvars();
	clearscene();
	bm_intro = getstati(69);
	fd_mode = getstati(BMST_FD_MODE);
	jb_active = getstati(BMST_JB_ACTIVE);
	hud_style = cvar("bm_hud_style");
	if (bm_intro)
	{
		BM_UpdateIntroCam();
	}
	fixIntermission();
	BM_Veh_UpdateBindMode(bm_intro);
	setproperty(VF_DRAWWORLD, TRUE);
	if (!inMenu && !bm_intro)
	{
		if (fd_mode > 0)
		{
			setproperty(VF_DRAWCROSSHAIR, FALSE);
			setproperty(VF_DRAWENGINESBAR, FALSE);
		}
		else
		{
			if (jb_active > 0)
				setproperty(VF_DRAWCROSSHAIR, FALSE);
			else
				setproperty(VF_DRAWCROSSHAIR, TRUE);
			if (hud_style >= 1 && hud_style <= 4)
				setproperty(VF_DRAWENGINESBAR, FALSE);
			else
				setproperty(VF_DRAWENGINESBAR, TRUE);
		}
	}
	else
	{
		setproperty(VF_DRAWCROSSHAIR, FALSE);
		setproperty(VF_DRAWENGINESBAR, FALSE);
	}
	addentities(MASK_ENGINE);
	if (fd_mode == 1 || fd_mode == 2)
		RH_AddXRayEntities();
	if (!inMenu && !bm_intro)
		MMT_DrawAimLine3D();
	renderscene();
	bm_ui_skip_scale = FALSE;
	drawfont = BM_GetUIFont();
	if (bm_intro)
	{
		if (!inMenu)
		{
			BM_DrawIntroHUD(w, h);
		}
	}
	else
	{
		setHUDparms();
		getItems();
		cw = vid_conwidth;
		ch = vid_conheight;
		if (cw <= 0)
			cw = cvar("vid_conwidth");
		if (ch <= 0)
			ch = cvar("vid_conheight");
		if (cw <= 0)
			cw = w;
		if (ch <= 0)
			ch = h;
		if (((!intermission && !finale && !inMenu) || (UIDraw == 1)))
		{
			if (fd_mode > 0)
			{
				if (showHUD > 0 || UIDraw == 1)
					fade_camera();
				RH_DrawXRayHUD(w, h);	// also draws the bottom-left centerprint toast (BM_DrawCenterPrint), which the normal HUD path draws otherwise
			}
			else
			{
				if (!intermission && !finale && !inMenu)
					MMT_DrawAimReticle2D(cw, ch);
				if (showHUD > 0 || UIDraw == 1)
				{
					fade_camera();
					if (hud_style >= 1 && hud_style <= 4)
					{
						if (hud_style == 1)
							HUD_DrawStyle1(cw, ch);
						else if (hud_style == 2)
							HUD_DrawStyle2(cw, ch);
						else if (hud_style == 3)
							HUD_DrawStyle3(cw, ch);
						else
							HUD_DrawStyle4(cw, ch);
					}
					else
					{
						DrawHUD();
						BM_DrawHUD(w, h);	// Bakersfield LAN: reload bar, magazine, leader banner (bm_hud.qc)
					}
					displayIntro();
					DrawLevelName('0.9 0.1 0');
					spawnBots();
				}
				else
				{
					BM_DrawCenterPrint(cw, ch);
				}
				if (!intermission && !finale && !inMenu)
				{
					KY_DrawHUD(cw, ch);
					GK_DrawHUD(cw, ch);
					JB_DrawHUD(w, h);
					BM_DrawMinimap(w, h);
				}
			}
		}
	}
	if (!bm_intro)
	{
		DrawScoreboard();
		BM_DrawScoreKeys();
	}
	ShowMenu();
	ShowMapList();
	TogglePause();
	drawfont = 0;
};

void(float isnew) CSQC_Ent_Update =
{
	local float flags;
	local float wtype;

	self.enttype = ReadByte();
	if ((self.enttype == ET_WORLDSPAWN))
	{
		self.drawmask = 0;
		wtype = ReadByte();
		return;
	}
	if ((self.enttype == ENT_PARTICLE_EMITTER))
	{
		flags = ReadByte();
		if ((flags & 1))
		{
			Particle_Emitter(isnew);
		}
	}
	else
	{
		if ((self.enttype == ENT_SPRITE_EMITTER))
		{
			flags = ReadByte();
			if ((flags & 1))
			{
				Sprite_Spawner(isnew);
			}
		}
		else
		{
			if ((self.enttype == ENT_CASING))
			{
				flags = ReadByte();
				if ((flags & 1))
				{
					Casing_Spawner(isnew);
				}
			}
			else if ((self.enttype == ENT_RD_TARGET))
			{
				RH_XRay_EntUpdate(isnew);
			}
			else if ((self.enttype == ENT_BM_RADAR))
			{
				BM_Radar_EntUpdate(isnew);
			}
			else
			{
				print(/*11460i*/"ERR: Unhandled CSQC entity\n");
			}
		}
	}
};

void() CSQC_Ent_Remove =
{
	if ((self.enttype == ENT_RD_TARGET))
	{
		RH_XRay_EntRemove();
		return;
	}
	if ((self.enttype == ENT_BM_RADAR))
	{
		BM_Radar_EntRemove();
		return;
	}
	if ((self.classname != "sprite"))
	{
		remove(self);
	}
};

float(string strCommand) CSQC_ConsoleCommand =
{
	return (0);
};

float(float flEventType, float flKey, float flCharacter) CSQC_InputEvent =
{
	local float holder;

	if ((inMenu == 1))
	{
		if ((flKey == K_DEL))
		{
			if (((flEventType == INPUT_KEYDOWN) && !bindMode))
			{
				clearKey();
			}
		}
	}
	if ((bindMode == 1))
	{
		if ((keySelect == 1))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				bindMode = 0;
				if ((((getkeybind(flKey) != "togglekeybinds") && (flKey != K_ESCAPE)) && (flKey != K_BACKSPACE)))
				{
					clearKey();
					setkeybind_bindmap(flKey, /*8963i*/"ThrowGrenade", 0);
				}
			}
		}
		else
		{
			if ((keySelect == 2))
			{
				if ((flEventType == INPUT_KEYDOWN))
				{
					bindMode = 0;
					if ((((getkeybind(flKey) != "togglekeybinds") && (flKey != K_ESCAPE)) && (flKey != K_BACKSPACE)))
					{
						clearKey();
						setkeybind_bindmap(flKey, /*8976i*/"quickkick", 0);
					}
				}
			}
			else
			{
				if ((keySelect == 3))
				{
					if ((flEventType == INPUT_KEYDOWN))
					{
						bindMode = 0;
						if ((((getkeybind(flKey) != "togglekeybinds") && (flKey != K_ESCAPE)) && (flKey != K_BACKSPACE)))
						{
							clearKey();
							setkeybind_bindmap(flKey, /*8986i*/"flashlight", 0);
						}
					}
				}
				else
				{
					if ((keySelect == 4))
					{
						if ((flEventType == INPUT_KEYDOWN))
						{
							bindMode = 0;
							if ((((getkeybind(flKey) != "togglekeybinds") && (flKey != K_ESCAPE)) && (flKey != K_BACKSPACE)))
							{
								clearKey();
								setkeybind_bindmap(flKey, /*8997i*/"chasecam", 0);
							}
						}
					}
					else
					{
						if ((keySelect == 5))
						{
							if ((flEventType == INPUT_KEYDOWN))
							{
								bindMode = 0;
								if ((((getkeybind(flKey) != "togglekeybinds") && (flKey != K_ESCAPE)) && (flKey != K_BACKSPACE)))
								{
									clearKey();
									setkeybind_bindmap(flKey, /*9006i*/"addbot", 0);
									keybound5 = flKey;
								}
							}
						}
						else
						{
							if ((keySelect == 6))
							{
								if ((flEventType == INPUT_KEYDOWN))
								{
									bindMode = 0;
									if ((((getkeybind(flKey) != "togglekeybinds") && (flKey != K_ESCAPE)) && (flKey != K_BACKSPACE)))
									{
										clearKey();
										setkeybind_bindmap(flKey, /*9013i*/"addbotenemy", 0);
										keybound6 = flKey;
									}
								}
							}
							else
							{
								if ((keySelect == 7))
								{
									if ((flEventType == INPUT_KEYDOWN))
									{
										bindMode = 0;
										if ((((getkeybind(flKey) != "togglekeybinds") && (flKey != K_ESCAPE)) && (flKey != K_BACKSPACE)))
										{
											clearKey();
											setkeybind_bindmap(flKey, /*9025i*/"removebot", 0);
											keybound7 = flKey;
										}
									}
								}
								else
								{
									if ((keySelect == 8))
									{
										if ((flEventType == INPUT_KEYDOWN))
										{
											bindMode = 0;
											if ((((getkeybind(flKey) != "togglekeybinds") && (flKey != K_ESCAPE)) && (flKey != K_BACKSPACE)))
											{
												clearKey();
												setkeybind_bindmap(flKey, /*9035i*/"+hook", 0);
												keybound8 = flKey;
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	if ((inMenu == 2))
	{
		if ((flKey == K_ENTER))
		{
			if ((((flEventType == INPUT_KEYDOWN) && (keySelect != 15)) && (keySelect != 16)))
			{
				sound(self, CHAN_AUTO, "misc/menu3.wav", 1, ATTN_NONE);
			}
			if ((keySelect == 1))
			{
				if ((flEventType == INPUT_KEYDOWN))
				{
					if ((cvar("lowspec") == 0))
					{
						cvar_set("cl_decals_max", "128");
						cvar_set("cl_decals_time", "12");
						cvar_set("cl_decals_fadetime", "4");
						cvar_set("cl_stainmaps", "0");
						cvar_set("cl_decals_models", "0");
						cvar_set("lowspec", "1");
					}
					else
					{
						if ((cvar("lowspec") == 1))
						{
							cvar_set("cl_decals_max", "256");
							cvar_set("cl_decals_time", "16");
							cvar_set("cl_decals_fadetime", "4");
							cvar_set("cl_stainmaps", "0");
							cvar_set("cl_decals_models", "0");
							cvar_set("lowspec", "0");
						}
					}
				}
			}
			else
			{
				if ((keySelect == 2))
				{
					if ((flEventType == INPUT_KEYDOWN))
					{
						if ((cvar("cl_decals_max") >= 512))
						{
							cvar_set("cl_decals_max", "128");
						}
						else
						{
							if ((cvar("cl_decals_max") <= 128))
							{
								cvar_set("cl_decals_max", "256");
							}
							else
							{
								cvar_set("cl_decals_max", "512");
							}
						}
					}
				}
				else
				{
					if ((keySelect == 3))
					{
						if ((flEventType == INPUT_KEYDOWN))
						{
							cvar_set("cl_decals_fadetime", "4");
							if ((cvar("cl_decals_time") >= 30))
							{
								cvar_set("cl_decals_time", "10");
							}
							else
							{
								if ((cvar("cl_decals_time") <= 10))
								{
									cvar_set("cl_decals_time", "16");
								}
								else
								{
									cvar_set("cl_decals_time", "30");
								}
							}
						}
					}
					else
					{
						if ((keySelect == 4))
						{
							if ((flEventType == INPUT_KEYDOWN))
							{
								if ((cvar("coop_life_pool") == 0))
								{
									cvar_set("coop_life_pool", "1");
								}
								else
								{
									cvar_set("coop_life_pool", "0");
								}
							}
						}
						else
						{
							if ((keySelect == 5))
							{
								if ((flEventType == INPUT_KEYDOWN))
								{
									if ((cvar("coop_lives") < 50))
									{
										addlives = addlives + 1;
										cvar_set("coop_lives", ftos(addlives));
									}
									else
									{
										if ((cvar("coop_lives") >= 50))
										{
											addlives = 1;
											cvar_set("coop_lives", ftos(addlives));
										}
									}
								}
							}
							else
							{
								if ((keySelect == 6))
								{
									if ((flEventType == INPUT_KEYDOWN))
									{
										if ((cvar("clonemonsters") < 10))
										{
											clonemonsters = clonemonsters + 1;
											cvar_set("clonemonsters", ftos(clonemonsters));
										}
										else
										{
											clonemonsters = 0;
											cvar_set("clonemonsters", ftos(clonemonsters));
										}
									}
								}
								else
								{
									if ((keySelect == 7))
									{
										if ((flEventType == INPUT_KEYDOWN))
										{
											if ((cvar("gibsduration") > 99))
											{
												gibtime = 0;
												cvar_set("gibsduration", ftos(gibtime));
											}
											else
											{
												gibtime = gibtime + 1;
												cvar_set("gibsduration", ftos(gibtime));
											}
										}
									}
									else
									{
										if ((keySelect == 8))
										{
											if ((flEventType == INPUT_KEYDOWN))
											{
												if ((cvar("auto_save") == 1))
												{
													cvar_set("auto_save", "0");
													cvar_set("savedgamecfg", ftos(cvar("auto_save")));
												}
												else
												{
													cvar_set("auto_save", "1");
													cvar_set("savedgamecfg", ftos(cvar("auto_save")));
												}
											}
										}
										else
										{
											if ((keySelect == 9))
											{
												if ((flEventType == INPUT_KEYDOWN))
												{
													if ((cvar("hud_proxcount_big") == 1))
													{
														cvar_set("hud_proxcount_big", "0");
													}
													else
													{
														cvar_set("hud_proxcount_big", "1");
													}
												}
											}
											else
											{
												if ((keySelect == 10))
												{
													if ((flEventType == INPUT_KEYDOWN))
													{
														if ((cvar("hud_showtitle") == 1))
														{
															cvar_set("hud_showtitle", "0");
														}
														else
														{
															cvar_set("hud_showtitle", "1");
														}
													}
												}
												else
												{
													if ((keySelect == 11))
													{
														if ((flEventType == INPUT_KEYDOWN))
														{
															if ((cvar("qc_ssg") == 1))
															{
																cvar_set("qc_ssg", "0");
															}
															else
															{
																cvar_set("qc_ssg", "1");
															}
														}
													}
													else
													{
														if ((keySelect == 12))
														{
															if ((flEventType == INPUT_KEYDOWN))
															{
																if ((cvar("centered_weapons") == 1))
																{
																	cvar_set("centered_weapons", "0");
																}
																else
																{
																	cvar_set("centered_weapons", "1");
																}
															}
														}
														else
														{
															if ((keySelect == 13))
															{
																if ((flEventType == INPUT_KEYDOWN))
																{
																	if ((cvar("flamestyle") == 2))
																	{
																		cvar_set("flamestyle", "0");
																	}
																	else
																	{
																		cvar_set("flamestyle", "2");
																	}
																}
															}
															else
															{
																if ((keySelect == 14))
																{
																	if ((flEventType == INPUT_KEYDOWN))
																	{
																		localcmd("restart\n");
																	}
																}
															}
														}
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
			if ((keySelect == 15))
			{
				if ((flEventType == INPUT_KEYDOWN))
				{
					sound(self, CHAN_ITEM, "misc/menu2.wav", 1, ATTN_NONE);
					if ((inMenu == 2))
					{
						inMenu = 1;
					}
					keySelect = 9;
					return (TRUE);
				}
			}
		}
	}
	if ((inMenu == 3))
	{
		if ((flKey == K_ENTER))
		{
			if (((flEventType == INPUT_KEYDOWN) && (keySelect != 15)))
			{
				sound(self, CHAN_AUTO, "misc/menu3.wav", 1, ATTN_NONE);
			}
			if ((keySelect == 1))
			{
				if ((flEventType == INPUT_KEYDOWN))
				{
					if ((cvar("redarmor_backpack") == 0))
					{
						cvar_set("redarmor_backpack", "1");
					}
					else
					{
						cvar_set("redarmor_backpack", "0");
					}
				}
			}
			else
			{
				if ((keySelect == 2))
				{
					if ((flEventType == INPUT_KEYDOWN))
					{
						if ((cvar("chainsaw_drops") == 0))
						{
							cvar_set("chainsaw_drops", "1");
						}
						else
						{
							cvar_set("chainsaw_drops", "0");
						}
					}
				}
				else
				{
					if ((keySelect == 3))
					{
						if ((flEventType == INPUT_KEYDOWN))
						{
							if ((cvar("sv_stopspeed") == 100))
							{
								cvar_set("sv_stopspeed", "150");
								cvar_set("saved4", "150");
							}
							else
							{
								if ((cvar("sv_stopspeed") == 150))
								{
									cvar_set("sv_stopspeed", "200");
									cvar_set("saved4", "200");
								}
								else
								{
									cvar_set("sv_stopspeed", "100");
									cvar_set("saved4", "100");
								}
							}
						}
					}
					else
					{
						if ((keySelect == 4))
						{
							if ((flEventType == INPUT_KEYDOWN))
							{
								if ((cvar("enforcer_defender") == 0))
								{
									cvar_set("enforcer_defender", "1");
								}
								else
								{
									cvar_set("enforcer_defender", "0");
								}
							}
						}
						else
						{
							if ((keySelect == 5))
							{
								if ((flEventType == INPUT_KEYDOWN))
								{
									if ((cvar("weaponautoswitch") == 0))
									{
										cvar_set("weaponautoswitch", "3");
										cvar_set("enforcer_defender_prox", ftos(cvar("weaponautoswitch")));
									}
									else
									{
										cvar_set("weaponautoswitch", "0");
										cvar_set("enforcer_defender_prox", ftos(cvar("weaponautoswitch")));
									}
								}
							}
							else
							{
								if ((keySelect == 6))
								{
									if ((flEventType == INPUT_KEYDOWN))
									{
										if ((cvar("vanilla_ssg") == 0))
										{
											cvar_set("vanilla_ssg", "1");
											cvar_set("saved3", "1");
										}
										else
										{
											cvar_set("vanilla_ssg", "0");
											cvar_set("saved3", "0");
										}
									}
								}
								else
								{
									if ((keySelect == 7))
									{
										if ((flEventType == INPUT_KEYDOWN))
										{
											if ((cvar("shalrath_mother") == 1))
											{
												cvar_set("shalrath_mother", "0");
											}
											else
											{
												cvar_set("shalrath_mother", "1");
											}
										}
									}
									else
									{
										if ((keySelect == 8))
										{
											if ((flEventType == INPUT_KEYDOWN))
											{
												if ((cvar("nospinup") == 1))
												{
													cvar_set("nospinup", "0");
												}
												else
												{
													cvar_set("nospinup", "1");
												}
											}
										}
										else
										{
											if ((keySelect == 9))
											{
												if ((flEventType == INPUT_KEYDOWN))
												{
													if ((cvar("yakman_replace_shambler") > 0))
													{
														cvar_set("yakman_replace_shambler", "0");
													}
													else
													{
														cvar_set("yakman_replace_shambler", "15");
													}
												}
											}
											else
											{
												if ((keySelect == 10))
												{
													if ((flEventType == INPUT_KEYDOWN))
													{
														if ((cvar("effects_explosion_shake") > 0))
														{
															cvar_set("effects_explosion_shake", "0");
															cvar_set("soldier_nailgrunt", "0");
														}
														else
														{
															cvar_set("effects_explosion_shake", "1");
															cvar_set("soldier_nailgrunt", "1");
														}
													}
												}
												else
												{
													if ((keySelect == 11))
													{
														if ((flEventType == INPUT_KEYDOWN))
														{
															if ((cvar("quadreplacer") > 0))
															{
																cvar_set("quadreplacer", "0");
																cvar_set("slowmo_powerup", ftos(cvar("quadreplacer")));
															}
															else
															{
																cvar_set("quadreplacer", "1.001");
																cvar_set("slowmo_powerup", ftos(cvar("quadreplacer")));
															}
														}
													}
													else
													{
														if ((keySelect == 12))
														{
															if ((flEventType == INPUT_KEYDOWN))
															{
																if ((cvar("slowmotion") == 1))
																{
																	cvar_set("slowmotion", "0");
																}
																else
																{
																	cvar_set("slowmotion", "1");
																}
															}
														}
														else
														{
															if ((keySelect == 13))
															{
																if ((flEventType == INPUT_KEYDOWN))
																{
																	if ((cvar("deathmatch_music") == 1))
																	{
																		cvar_set("deathmatch_music", "0");
																	}
																	else
																	{
																		cvar_set("deathmatch_music", "1");
																	}
																}
															}
															else
															{
																if ((keySelect == 14))
																{
																	if ((flEventType == INPUT_KEYDOWN))
																	{
																		if ((cvar("qtips") >= 1.4))
																		{
																			cvar_set("qtips", "-0.05");
																		}
																		holder = cvar("qtips");
																		holder = holder + 0.1;
																		cvar_set("qtips", ftos(holder));
																		if ((cvar("qtips") >= 1.4))
																		{
																			sound(self, CHAN_AUTO, "misc/corpsegib.wav", 0.6, ATTN_NONE);
																		}
																	}
																}
																else
																{
																	if ((keySelect == 15))
																	{
																		if ((flEventType == INPUT_KEYDOWN))
																		{
																			localcmd("restart\n");
																		}
																	}
																}
															}
														}
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
			if ((keySelect == 16))
			{
				if ((flEventType == INPUT_KEYDOWN))
				{
					sound(self, CHAN_ITEM, "misc/menu2.wav", 1, ATTN_NONE);
					if ((inMenu == 3))
					{
						inMenu = 1;
					}
				}
			}
		}
	}
	if ((inMenu == 5))
	{
		if ((((flKey == K_ENTER) || (flKey == K_RIGHTARROW)) || (flKey == K_LEFTARROW)))
		{
			if (((flEventType == INPUT_KEYDOWN) && (keySelect != 15)))
			{
				sound(self, CHAN_AUTO, "misc/menu3.wav", 1, ATTN_NONE);
			}
			if ((keySelect == 1))
			{
				if ((flEventType == INPUT_KEYDOWN))
				{
					if (!isSingle())
					{
						if ((maxplayers < 32))
						{
							maxplayers = maxplayers + 1;
						}
						else
						{
							maxplayers = 1;
						}
						mp_temp = maxplayers;
					}
				}
			}
			else
			{
				if ((keySelect == 2))
				{
					if ((flEventType == INPUT_KEYDOWN))
					{
						if ((gt_cycle == 0))
						{
							setDeathmatch();
							gt_cycle = gt_cycle + 1;
						}
						else
						{
							if ((gt_cycle == 1))
							{
								setCTF();
								if ((cvar("teamplay") == 0))
								{
									cvar_set("teamplay", "1");
								}
								gt_cycle = gt_cycle + 1;
							}
							else
							{
								if ((gt_cycle == 2))
								{
									gt_cycle = gt_cycle + 1;
									setDefaults();
									setCoop();
								}
								else
								{
									if ((gt_cycle == 3))
									{
										setSP();
										gt_cycle = 0;
									}
								}
							}
						}
					}
				}
				else
				{
					if ((keySelect == 3))
					{
						if ((flEventType == INPUT_KEYDOWN))
						{
							if (!weaponstay)
							{
								weaponstay = 1;
							}
							else
							{
								weaponstay = 0;
							}
						}
					}
					else
					{
						if ((keySelect == 4))
						{
							if ((flEventType == INPUT_KEYDOWN))
							{
								if ((scorelimit < 10))
								{
									scorelimit = scorelimit + 1;
								}
								else
								{
									if ((scorelimit >= 100))
									{
										scorelimit = 0;
									}
									else
									{
										scorelimit = scorelimit + 5;
									}
								}
								if ((gametype == "Capture the Flag"))
								{
									cvar_set("ctf_capture_limit", ftos(scorelimit));
								}
								else
								{
									cvar_set("fraglimit", ftos(scorelimit));
								}
							}
						}
						else
						{
							if ((keySelect == 5))
							{
								if ((flEventType == INPUT_KEYDOWN))
								{
									if ((timelimit < 10))
									{
										timelimit = timelimit + 1;
									}
									else
									{
										if ((timelimit >= 100))
										{
											timelimit = 0;
										}
										else
										{
											timelimit = timelimit + 5;
										}
									}
									cvar_set("timelimit", ftos(timelimit));
								}
							}
							else
							{
								if ((keySelect == 6))
								{
									if ((flEventType == INPUT_KEYDOWN))
									{
										setTeamplay();
									}
								}
								else
								{
									if ((keySelect == 7))
									{
										if ((flEventType == INPUT_KEYDOWN))
										{
											if ((isCTF() || isDeathmatch()))
											{
												if (!cvar("ctf_autobalance"))
												{
													cvar_set("ctf_autobalance", "1");
												}
												else
												{
													cvar_set("ctf_autobalance", "0");
												}
											}
											else
											{
												if ((cvar("coop_life_pool") == 0))
												{
													cvar_set("coop_life_pool", "1");
												}
												else
												{
													cvar_set("coop_life_pool", "0");
												}
											}
										}
									}
									else
									{
										if ((keySelect == 8))
										{
											if ((flEventType == INPUT_KEYDOWN))
											{
												SkillSelect();
											}
										}
										else
										{
											if ((keySelect == 9))
											{
												if ((flEventType == INPUT_KEYDOWN))
												{
													if ((isCTF() || isDeathmatch()))
													{
														setBots();
													}
													else
													{
														setAmmoCap();
													}
												}
											}
											else
											{
												if ((keySelect == 10))
												{
													if ((flEventType == INPUT_KEYDOWN))
													{
														setHook();
													}
													return (TRUE);
												}
												else
												{
													if ((keySelect == 11))
													{
														if ((flEventType == INPUT_KEYDOWN))
														{
															if ((inMenu == 5))
															{
																inMenu = 4;
															}
														}
														return (TRUE);
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	if ((flKey == K_ENTER))
	{
		if (((keySelect == 9) && (inMenu == 1)))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				sound(self, CHAN_ITEM, "misc/menu3.wav", 1, ATTN_NONE);
				if ((sliderPos < 0))
				{
					sliderPos = 0;
				}
				else if ((sliderPos < 7))
				{
					sliderPos = sliderPos + 1;
				}
				else
				{
					sliderPos = 0;
				}
				updateScreenSize();
			}
		}
		if (((keySelect == 10) && (inMenu != 3)))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				sound(self, CHAN_ITEM, "misc/menu2.wav", 1, ATTN_NONE);
				if ((inMenu == 1))
				{
					inMenu = 2;
				}
				keySelect = 15;
			}
		}
		if (((keySelect == 11) && (inMenu == 1)))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				sound(self, CHAN_ITEM, "misc/menu2.wav", 1, ATTN_NONE);
				if ((inMenu == 1))
				{
					inMenu = 3;
				}
				keySelect = 16;
			}
		}
		if (((keySelect == 15) && (inMenu == 2)))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				keySelect = 10;
			}
		}
		if ((keySelect == 16))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				keySelect = 10;
			}
		}
		if (((inMenu == 1) && (((((keySelect != 9) && (keySelect != 10)) && (keySelect != 11)) && (keySelect != 15)) && (keySelect != 16))))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				sound(self, CHAN_AUTO, "misc/menu2.wav", 1, ATTN_NONE);
				if ((bindMode == 0))
				{
					bindMode = 1;
				}
				else
				{
					if ((bindMode == 1))
					{
						bindMode = 0;
					}
				}
			}
		}
		if ((inMenu == 4))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				loadMap();
			}
		}
	}
	if (((inMenu == 1) && (keySelect == 9)))
	{
		if ((flKey == K_RIGHTARROW))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				sound(self, CHAN_ITEM, "misc/menu3.wav", 1, ATTN_NONE);
				if ((sliderPos < 0))
				{
					sliderPos = 0;
				}
				else if ((sliderPos < 7))
				{
					sliderPos = sliderPos + 1;
				}
				updateScreenSize();
			}
		}
		if ((flKey == K_LEFTARROW))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				sound(self, CHAN_ITEM, "misc/menu3.wav", 1, ATTN_NONE);
				if ((sliderPos < 0))
				{
					sliderPos = 0;
				}
				else if ((sliderPos > 0))
				{
					sliderPos = sliderPos - 1;
				}
				updateScreenSize();
			}
		}
	}
	if ((flKey == K_LEFTARROW))
	{
		if ((flEventType == INPUT_KEYDOWN))
		{
			if (((inMenu == 4) && (mapcount > 0) && (arrowPos > 0)))
			{
				sound(self, CHAN_ITEM, "misc/menu3.wav", 0.5, ATTN_NONE);
				arrowPos = bound(0, (arrowPos - 10), (mapcount - 1));
				posveclist_y = 292 + (arrowPos * 10);
			}
		}
	}
	if ((flKey == K_RIGHTARROW))
	{
		if ((flEventType == INPUT_KEYDOWN))
		{
			if (((inMenu == 4) && (mapcount > 0) && (arrowPos < (mapcount - 1))))
			{
				sound(self, CHAN_ITEM, "misc/menu3.wav", 0.5, ATTN_NONE);
				arrowPos = bound(0, (arrowPos + 10), (mapcount - 1));
				posveclist_y = 292 + (arrowPos * 10);
			}
		}
	}
	if ((flKey == K_DOWNARROW))
	{
		if (inMenu)
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				sound(self, CHAN_AUTO, "misc/menu1.wav", 1, ATTN_NONE);
				if ((bindMode == 0))
				{
					if ((inMenu == 1))
					{
						keySelect = keySelect + 1;
						if ((keySelect == 12))
						{
							keySelect = 1;
						}
					}
					else
					{
						if ((inMenu == 2))
						{
							keySelect = keySelect + 1;
							if ((keySelect == 16))
							{
								keySelect = 1;
							}
						}
						else
						{
							if ((inMenu == 3))
							{
								keySelect = keySelect + 1;
								if ((keySelect == 17))
								{
									keySelect = 1;
								}
							}
							else
							{
								if (((inMenu == 4) && (mapcount > 0)))
								{
									keytimer = keytimer + 1;
									if ((keytimer >= 30))
									{
										arrowPos = arrowPos + 3;
									}
									else if (!POINTS_TO_BSP)
									{
										arrowPos = arrowPos + 20;
									}
									else
									{
										arrowPos = arrowPos + 1;
									}
									arrowPos = bound(0, arrowPos, (mapcount - 1));
									posveclist_y = 292 + (arrowPos * 10);
								}
								else
								{
									if ((inMenu == 5))
									{
										keySelect = keySelect + 1;
										if ((keySelect == 12))
										{
											keySelect = 1;
										}
									}
								}
							}
						}
					}
				}
			}
			if ((flEventType == INPUT_KEYUP))
			{
				keytimer = 0;
			}
		}
	}
	if ((flKey == K_UPARROW))
	{
		if (inMenu)
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				sound(self, CHAN_AUTO, "misc/menu1.wav", 1, ATTN_NONE);
				if ((bindMode == 0))
				{
					if ((inMenu == 1))
					{
						keySelect = keySelect - 1;
						if ((keySelect == 0))
						{
							keySelect = 11;
						}
					}
					else
					{
						if ((inMenu == 2))
						{
							keySelect = keySelect - 1;
							if ((keySelect == 0))
							{
								keySelect = 15;
							}
						}
						else
						{
							if ((inMenu == 3))
							{
								keySelect = keySelect - 1;
								if ((keySelect == 0))
								{
									keySelect = 16;
								}
							}
							else
							{
								if (((inMenu == 4) && (mapcount > 0) && (arrowPos > 0)))
								{
									keytimer = keytimer + 1;
									if (((keytimer >= 30) && (arrowPos >= 10)))
									{
										arrowPos = arrowPos - 3;
									}
									else if ((!POINTS_TO_BSP && (arrowPos >= 20)))
									{
										arrowPos = arrowPos - 20;
									}
									else
									{
										arrowPos = arrowPos - 1;
									}
									arrowPos = bound(0, arrowPos, (mapcount - 1));
									posveclist_y = 292 + (arrowPos * 10);
								}
								else
								{
									if ((inMenu == 5))
									{
										keySelect = keySelect - 1;
										if ((keySelect == 0))
										{
											keySelect = 11;
										}
									}
								}
							}
						}
					}
				}
			}
			if ((flEventType == INPUT_KEYUP))
			{
				keytimer = 0;
			}
		}
	}
	if ((flKey == K_END))
	{
		if ((inMenu == 4))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				sound(self, CHAN_AUTO, "misc/menu1.wav", 1, ATTN_NONE);
				SkillSelect();
			}
		}
	}
	if (((getkeybind(flKey) == "togglekeybinds") || (inMenu && (flKey == K_HOME))))
	{
		if ((flEventType == INPUT_KEYUP))
		{
			sound(self, CHAN_AUTO, "misc/menu2.wav", 1, ATTN_NONE);
			if (!inMenu)
			{
				keySelect = 1;
				inMenu = 1;
			}
			else
			{
				if ((inMenu == 4))
				{
					keySelect = 1;
					inMenu = 5;
				}
				else
				{
					if ((inMenu == 5))
					{
						inMenu = 4;
					}
					else
					{
						if ((bindMode == 1))
						{
							bindMode = 0;
						}
						else
						{
							if (inMenu)
							{
								inMenu = 0;
							}
						}
					}
				}
			}
		}
	}
	if ((inMenu && (flKey == K_BACKSPACE)))
	{
		if ((flEventType == INPUT_KEYDOWN))
		{
			sound(self, CHAN_AUTO, "misc/menu2.wav", 1, ATTN_NONE);
			if ((inMenu == 5))
			{
				inMenu = 4;
			}
			else
			{
				inMenu = 0;
			}
		}
	}
	if (inMenu)
	{
		if ((flKey == K_ESCAPE))
		{
			if ((flEventType == INPUT_KEYDOWN))
			{
				inMenu = 0;
			}
		}
		return (TRUE);
	}
	if ((getkeybind(flKey) == "+showscores"))
	{
		if ((flEventType == INPUT_KEYDOWN))
		{
			showscores = TRUE;
			return (0);
		}
		if ((flEventType == INPUT_KEYUP))
		{
			showscores = 0;
			return (0);
		}
	}
	else
	{
		return (0);
	}
};
