// BakersfieldQuake MenuQC - Classic Default Quake / Zircon Options, Graphics, Controls & Weapons

float OPT_TAB_VIDEO    = 0;
float OPT_TAB_GRAPHICS = 1;
float OPT_TAB_CONTROLS = 2;
float OPT_TAB_WEAPONS  = 3;
float OPT_TAB_COUNT    = 4;

float OPT_VID_COUNT    = 15;
float OPT_GFX_COUNT    = 26;
float OPT_CTRL_COUNT   = 21;
float OPT_WEP_COUNT    = 20;

float SL_HDR      = 1;
float SL_GAMMA    = 2;
float SL_CONTRAST = 3;
float SL_BRIGHT   = 4;
float SL_FOV      = 5;
float SL_SENS     = 6;
float SL_VOL      = 7;
float SL_BGM      = 8;

float g_opt_vid_dirty;
float g_opt_res_idx;

void() BM_Options_Open =
{
	local float w;

	g_page = PAGE_OPTIONS;
	g_focus_input = INPUT_NONE;
	g_bind_listen_idx = -1;
	g_opt_scroll = 0;
	g_active_slider = 0;

	w = stof(cvar_string("vid_width"));
	if (stof(cvar_string("vid_desktopfullscreen")) != 0)
		g_opt_res_idx = 0;
	else if (w <= 1280)
		g_opt_res_idx = 1;
	else if (w <= 1600)
		g_opt_res_idx = 2;
	else if (w <= 1920)
		g_opt_res_idx = 3;
	else
		g_opt_res_idx = 4;
};

string(float idx) BM_Opt_ResLabel =
{
	if (idx <= 0) return "Desktop";
	if (idx == 1) return "1280x720";
	if (idx == 2) return "1600x900";
	if (idx == 3) return "1920x1080";
	return "2560x1440";
};

void(float idx) BM_Opt_ApplyRes =
{
	if (idx <= 0)
	{
		cvar_set("vid_desktopfullscreen", "1");
	}
	else
	{
		cvar_set("vid_desktopfullscreen", "0");
		if (idx == 1)      { cvar_set("vid_width", "1280"); cvar_set("vid_height", "720"); }
		else if (idx == 2) { cvar_set("vid_width", "1600"); cvar_set("vid_height", "900"); }
		else if (idx == 3) { cvar_set("vid_width", "1920"); cvar_set("vid_height", "1080"); }
		else               { cvar_set("vid_width", "2560"); cvar_set("vid_height", "1440"); }
	}
	g_opt_vid_dirty = TRUE;
};

void(string msg) BM_Opt_SetStatus =
{
	g_opt_status = BM_ZoneSet(g_opt_status, msg);
	g_opt_status_t = gettime() + 2.5;
};

void() BM_Opt_SaveConfig =
{
	localcmd("saveconfig\n");
	BM_Opt_SetStatus("SETTINGS SAVED TO CONFIG.CFG");
};

void() BM_Opt_ApplyVideoDefaults =
{
	cvar_set("r_hdr_scenebrightness", "1.45");
	cvar_set("v_gamma", "1.3125");
	cvar_set("v_contrast", "1.125");
	cvar_set("v_brightness", "0");
	cvar_set("v_glslgamma_2d", "1");
	cvar_set("fov", "100");
	cvar_set("sensitivity", "3");
	cvar_set("m_pitch", "0.022");
	cvar_set("m_filter", "0");
	cvar_set("cl_forwardspeed", "999");
	cvar_set("cl_backspeed", "999");
	cvar_set("cl_sidespeed", "999");
	cvar_set("volume", "0.7");
	cvar_set("bgmvolume", "0.2");
	cvar_set("vid_vsync", "0");
	cvar_set("cl_maxfps", "250");
	localcmd("saveconfig\n");
	BM_Opt_SetStatus("CLEAN VIDEO & AUDIO DEFAULTS APPLIED");
};

void(float enable_simple) BM_Opt_ApplySimpleMode =
{
	if (enable_simple)
	{
		cvar_set("lowspec", "1");
		cvar_set("r_bloom", "0");
		cvar_set("r_shadow_realtime_dlight", "0");
		cvar_set("r_shadow_realtime_dlight_shadows", "0");
		cvar_set("r_shadow_gloss", "0");
		cvar_set("r_shadow_glossexact", "0");
		cvar_set("r_shadow_shadowmapping", "0");
		cvar_set("r_glsl_offsetmapping", "0");
		cvar_set("r_glsl_offsetmapping_reliefmapping", "0");
		cvar_set("r_water", "0");
		cvar_set("r_coronas", "0");
		cvar_set("r_glsl_saturation", "1");
		cvar_set("cl_particles_quality", "0.5");
		cvar_set("cl_decals", "1");
		cvar_set("cl_decals_max", "128");
		cvar_set("cl_decals_time", "12");
		cvar_set("cl_decals_fadetime", "4");
		cvar_set("cl_decals_models", "0");
		cvar_set("cl_stainmaps", "0");
		cvar_set("r_minlight", "3");
		cvar_set("gl_overbright_models", "0");
	}
	else
	{
		cvar_set("lowspec", "0");
		cvar_set("r_bloom", "1");
		cvar_set("r_bloom_blur", "0.1");
		cvar_set("r_bloom_brighten", "0.1");
		cvar_set("r_shadow_realtime_dlight", "1");
		cvar_set("r_shadow_realtime_dlight_shadows", "1");
		cvar_set("r_shadow_gloss", "1");
		cvar_set("r_shadow_glossexact", "0");
		cvar_set("r_shadow_shadowmapping", "0");
		cvar_set("r_glsl_offsetmapping", "1");
		cvar_set("r_glsl_offsetmapping_reliefmapping", "0");
		cvar_set("r_water", "0");
		cvar_set("r_coronas", "0.6");
		cvar_set("r_glsl_saturation", "1");
		cvar_set("cl_particles_quality", "1");
		cvar_set("cl_decals", "1");
		cvar_set("cl_decals_max", "256");
		cvar_set("cl_decals_time", "16");
		cvar_set("cl_decals_fadetime", "4");
		cvar_set("cl_decals_models", "0");
		cvar_set("cl_stainmaps", "0");
		cvar_set("r_minlight", "3");
		cvar_set("gl_overbright_models", "0");
	}
};

void() BM_Opt_ApplyPrettyPreset =
{
	BM_Opt_ApplySimpleMode(FALSE);
	cvar_set("r_glsl_offsetmapping_reliefmapping", "1");
	cvar_set("r_glsl_offsetmapping_scale", "0.04");
	cvar_set("r_shadow_shadowmapping", "1");
	cvar_set("r_shadow_shadowmapping_maxsize", "1024");
	cvar_set("r_shadow_glossexact", "1");
	cvar_set("r_shadow_usenormalmap", "1");
	cvar_set("r_water", "1");
	cvar_set("r_water_lowquality", "0");
	cvar_set("r_water_resolutionmultiplier", "0.75");
	cvar_set("r_wateralpha", "0.5");
	cvar_set("r_glsl_saturation", "1.1");
	cvar_set("cl_stainmaps", "0");
	cvar_set("cl_decals_max", "256");
	cvar_set("cl_decals_time", "16");
	cvar_set("cl_decals_fadetime", "4");
	cvar_set("cl_decals_models", "0");
};

void() BM_Opt_ApplyGraphicsDefaults =
{
	BM_Opt_ApplySimpleMode(FALSE);
	if (stof(cvar_string("gl_picmip")) != 0)
	{
		cvar_set("gl_picmip", "0");
		g_opt_vid_dirty = TRUE;
	}
	if (stof(cvar_string("vid_samples")) != 4)
	{
		cvar_set("vid_samples", "4");
		g_opt_vid_dirty = TRUE;
	}
	cvar_set("gl_texturemode", "GL_LINEAR_MIPMAP_LINEAR");
	cvar_set("gl_texture_anisotropy", "16");
	cvar_set("gl_texturecompression", "0");
	cvar_set("r_lerpsprites", "0");
	cvar_set("r_lerpmodels", "1");
	cvar_set("r_lerplightstyles", "1");
	cvar_set("r_nearest_conchars", "0");
	cvar_set("bright_skins", "1");
	cvar_set("centered_weapons", "0");
	cvar_set("cl_bob", "0");
	cvar_set("cl_rollangle", "0");
	cvar_set("crosshair", "5");
	cvar_set("bm_hud_style", "0");
	cvar_set("bm_bot_tags", "1");
	cvar_set("bm_player_tags", "1");
	cvar_set("showfps", "1");
	localcmd("saveconfig\n");
	BM_Opt_SetStatus("CLEAN GRAPHICS DEFAULTS APPLIED");
};

string(float tab, float idx) BM_Opt_BindLabel =
{
	if (tab == OPT_TAB_CONTROLS)
	{
		if (idx == 0)  return "Move Forward";
		if (idx == 1)  return "Move Back";
		if (idx == 2)  return "Strafe Left";
		if (idx == 3)  return "Strafe Right";
		if (idx == 4)  return "Jump";
		if (idx == 5)  return "Fire / Attack";
		if (idx == 6)  return "Reload Magazine";
		if (idx == 7)  return "Quick Melee";
		if (idx == 8)  return "Binoculars (Zoom)";
		if (idx == 9)  return "Jetpack On / Off";
		if (idx == 10) return "Vehicle Enter / Exit";
		if (idx == 11) return "Vehicle Camera";
		if (idx == 12) return "Summon Winged John";
		if (idx == 13) return "Scoreboard";
		if (idx == 14) return "Chat";
		if (idx == 15) return "Team Chat";
		if (idx == 16) return "Vote Yes";
		if (idx == 17) return "Vote No";
		if (idx == 18) return "Add Enemy Bot";
		if (idx == 19) return "Remove Bot";
		return "Quick Join LAN (F3)";
	}

	if (idx == 0)  return "Next Weapon";
	if (idx == 1)  return "Previous Weapon";
	if (idx == 2)  return "Slot 1: Hammer";
	if (idx == 3)  return "Slot 2: Shotgun";
	if (idx == 4)  return "Slot 3: Super Shotgun";
	if (idx == 5)  return "Slot 4: Nailgun";
	if (idx == 6)  return "Slot 5: Super Nailgun";
	if (idx == 7)  return "Slot 6: Grenade Launcher";
	if (idx == 8)  return "Slot 7: Rocket Launcher";
	if (idx == 9)  return "Slot 8: Lightning / CCC";
	if (idx == 10) return "Slot 9: Mega Man Gun";
	if (idx == 11) return "Slot 0: M4A1 Rifle";
	if (idx == 12) return "M1 Garand Rifle";
	if (idx == 13) return "Fun: Rob Dob";
	if (idx == 14) return "Fun: Jar o' Green Guys";
	if (idx == 15) return "Fun: Pickle Surprise";
	if (idx == 16) return "Fun: NetSend PC";
	if (idx == 17) return "Fun: Dookie Bazooka";
	if (idx == 18) return "Fun: Wheelman Cannon";
	return "Fun: Pocket Kyle";
};

string(float tab, float idx) BM_Opt_BindCmd =
{
	if (tab == OPT_TAB_CONTROLS)
	{
		if (idx == 0)  return "+forward";
		if (idx == 1)  return "+back";
		if (idx == 2)  return "+moveleft";
		if (idx == 3)  return "+moveright";
		if (idx == 4)  return "+jump";
		if (idx == 5)  return "+attack";
		if (idx == 6)  return "impulse 41";
		if (idx == 7)  return "impulse 20";
		if (idx == 8)  return "+button3";
		if (idx == 9)  return "impulse 71";
		if (idx == 10) return "impulse 86";
		if (idx == 11) return "impulse 87";
		if (idx == 12) return "impulse 98";
		if (idx == 13) return "+showscores";
		if (idx == 14) return "messagemode";
		if (idx == 15) return "messagemode2";
		if (idx == 16) return "cmd vote yes";
		if (idx == 17) return "cmd vote no";
		if (idx == 18) return "addbotenemy";
		if (idx == 19) return "removebot";
		return "exec lan_server.cfg";
	}

	if (idx == 0)  return "impulse 10";
	if (idx == 1)  return "impulse 12";
	if (idx == 2)  return "impulse 1";
	if (idx == 3)  return "impulse 2";
	if (idx == 4)  return "impulse 3";
	if (idx == 5)  return "impulse 4";
	if (idx == 6)  return "impulse 5";
	if (idx == 7)  return "impulse 6";
	if (idx == 8)  return "impulse 7";
	if (idx == 9)  return "impulse 8";
	if (idx == 10) return "impulse 14";
	if (idx == 11) return "impulse 67";
	if (idx == 12) return "impulse 69";
	if (idx == 13) return "impulse 61";
	if (idx == 14) return "impulse 62";
	if (idx == 15) return "impulse 63";
	if (idx == 16) return "impulse 64";
	if (idx == 17) return "impulse 65";
	if (idx == 18) return "impulse 66";
	return "impulse 68";
};

string(string cmd) BM_Opt_GetBoundKeys =
{
	local string raw, out, kname;
	local float n, i, kn;

	raw = findkeysforcommand(cmd, 0);
	if (raw == "")
	{
		if (cmd == "impulse 41")
			return BM_Opt_GetBoundKeys("reload");
		return "UNBOUND";
	}
	n = tokenize(raw);
	out = "";
	for (i = 0; i < n; i = i + 1)
	{
		kn = stof(argv(i));
		if (kn > 0)
		{
			kname = strtoupper(keynumtostring(kn));
			if (out == "")
				out = kname;
			else
				out = strcat(out, " / ", kname);
		}
	}
	if (out == "" && cmd == "impulse 41")
		return BM_Opt_GetBoundKeys("reload");
	if (out == "")
		return "UNBOUND";
	return out;
};

void(string cmd) BM_Opt_ClearCmdBinds =
{
	local string raw;
	local float n, i, kn, keys_to_clear[8], cnt;

	raw = findkeysforcommand(cmd, 0);
	if (raw != "")
	{
		n = tokenize(raw);
		cnt = 0;
		for (i = 0; i < n && cnt < 8; i = i + 1)
		{
			kn = stof(argv(i));
			if (kn > 0)
			{
				keys_to_clear[cnt] = kn;
				cnt = cnt + 1;
			}
		}
		for (i = 0; i < cnt; i = i + 1)
			setkeybind(keys_to_clear[i], "", 0);
	}
	if (cmd == "impulse 41")
		BM_Opt_ClearCmdBinds("reload");
};

float() BM_Opt_IsLiveColorDrag =
{
	return (g_opt_tab == OPT_TAB_VIDEO && g_mouse1_down && g_active_slider >= SL_HDR && g_active_slider <= SL_BRIGHT);
};

void(float ix, float ry, float iw, float rh, float idx, float clicked) BM_Options_DrawVideoRow =
{
	local float st, nv, sens, mpitch, fv, gam, con, br, hdr, vol, bgm, fs_on, vs_on;
	local float fps_v, fps_i, filt_on, run_on;
	local string lbl;

	if (idx == 0)
	{
		hdr = stof(cvar_string("r_hdr_scenebrightness"));
		if (hdr <= 0) hdr = 1.45;
		nv = BM_DrawSlider(SL_HDR, ix, ry, iw, rh, "SCENE BRIGHTNESS", hdr, 0.60, 2.40, 0.05, 1, clicked);
		if (fabs(nv - hdr) > 0.005) cvar_set("r_hdr_scenebrightness", sprintf("%.2f", nv));
	}
	else if (idx == 1)
	{
		gam = stof(cvar_string("v_gamma"));
		if (gam <= 0) gam = 1.0;
		nv = BM_DrawSlider(SL_GAMMA, ix, ry, iw, rh, "GAMMA", gam, 0.70, 2.20, 0.05, 1, clicked);
		if (fabs(nv - gam) > 0.005) cvar_set("v_gamma", sprintf("%.2f", nv));
	}
	else if (idx == 2)
	{
		con = stof(cvar_string("v_contrast"));
		if (con <= 0) con = 1.0;
		nv = BM_DrawSlider(SL_CONTRAST, ix, ry, iw, rh, "CONTRAST", con, 0.70, 1.80, 0.05, 1, clicked);
		if (fabs(nv - con) > 0.005) cvar_set("v_contrast", sprintf("%.2f", nv));
	}
	else if (idx == 3)
	{
		br = stof(cvar_string("v_brightness"));
		nv = BM_DrawSlider(SL_BRIGHT, ix, ry, iw, rh, "BRIGHTNESS", br, -0.20, 0.40, 0.02, 4, clicked);
		if (fabs(nv - br) > 0.002) cvar_set("v_brightness", sprintf("%.2f", nv));
	}
	else if (idx == 4)
	{
		fv = stof(cvar_string("fov"));
		if (fv < 60) fv = 100;
		nv = BM_DrawSlider(SL_FOV, ix, ry, iw, rh, "FIELD OF VIEW", fv, 75, 130, 1, 0, clicked);
		if (fabs(nv - fv) > 0.01) cvar_set("fov", ftos(rint(nv)));
	}
	else if (idx == 5)
	{
		sens = stof(cvar_string("sensitivity"));
		nv = BM_DrawSlider(SL_SENS, ix, ry, iw, rh, "MOUSE SPEED", sens, 0.5, 15.0, 0.2, 2, clicked);
		if (fabs(nv - sens) > 0.05) cvar_set("sensitivity", sprintf("%.1f", nv));
	}
	else if (idx == 6)
	{
		vol = stof(cvar_string("volume"));
		nv = BM_DrawSlider(SL_VOL, ix, ry, iw, rh, "SOUND VOLUME", vol, 0.0, 1.0, 0.05, 3, clicked);
		if (fabs(nv - vol) > 0.005) cvar_set("volume", sprintf("%.2f", nv));
	}
	else if (idx == 7)
	{
		bgm = stof(cvar_string("bgmvolume"));
		nv = BM_DrawSlider(SL_BGM, ix, ry, iw, rh, "MUSIC VOLUME", bgm, 0.0, 1.0, 0.05, 3, clicked);
		if (fabs(nv - bgm) > 0.005) cvar_set("bgmvolume", sprintf("%.2f", nv));
	}
	else if (idx == 8)
	{
		mpitch = stof(cvar_string("m_pitch"));
		st = BM_DrawStepper(ix, ry, iw, rh, "INVERT MOUSE", (mpitch < 0) ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			if (mpitch == 0) mpitch = 0.022;
			cvar_set("m_pitch", ftos(0 - mpitch));
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 9)
	{
		filt_on = (stof(cvar_string("m_filter")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "MOUSE SMOOTHING", filt_on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("m_filter", filt_on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 10)
	{
		run_on = (stof(cvar_string("cl_forwardspeed")) > 250);
		st = BM_DrawStepper(ix, ry, iw, rh, "ALWAYS RUN", run_on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			lbl = run_on ? "200" : "999";
			cvar_set("cl_forwardspeed", lbl);
			cvar_set("cl_backspeed", lbl);
			cvar_set("cl_sidespeed", lbl);
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 11)
	{
		vs_on = (stof(cvar_string("vid_vsync")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "V-SYNC", vs_on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("vid_vsync", vs_on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 12)
	{
		fps_v = stof(cvar_string("cl_maxfps"));
		if (fps_v <= 0) { fps_i = 5; lbl = "Uncapped"; }
		else if (fps_v <= 60) { fps_i = 0; lbl = "60"; }
		else if (fps_v <= 120) { fps_i = 1; lbl = "120"; }
		else if (fps_v <= 144) { fps_i = 2; lbl = "144"; }
		else if (fps_v <= 200) { fps_i = 3; lbl = "200"; }
		else if (fps_v <= 300) { fps_i = 4; lbl = "250"; }
		else { fps_i = 5; lbl = "Uncapped"; }
		st = BM_DrawStepper(ix, ry, iw, rh, "MAX FPS", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			fps_i = modulo(fps_i + st + 6, 6);
			if (fps_i == 0) cvar_set("cl_maxfps", "60");
			else if (fps_i == 1) cvar_set("cl_maxfps", "120");
			else if (fps_i == 2) cvar_set("cl_maxfps", "144");
			else if (fps_i == 3) cvar_set("cl_maxfps", "200");
			else if (fps_i == 4) cvar_set("cl_maxfps", "250");
			else cvar_set("cl_maxfps", "0");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 13)
	{
		fs_on = (stof(cvar_string("vid_fullscreen")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "FULLSCREEN", fs_on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("vid_fullscreen", fs_on ? "0" : "1");
			g_opt_vid_dirty = TRUE;
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else
	{
		st = BM_DrawStepper(ix, ry, iw, rh, "RESOLUTION", BM_Opt_ResLabel(g_opt_res_idx), FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			g_opt_res_idx = bound(0, g_opt_res_idx + st, 4);
			BM_Opt_ApplyRes(g_opt_res_idx);
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
};

void(float px, float py, float pw, float ph, float clicked) BM_Options_DrawVideo =
{
	local float ix, iy, iw, ih, rh, gap, vis, max_scroll, i, r, ry, live_drag, hov, sb_h, sb_y;

	ix = px + 14;
	iy = py + 58;
	iw = pw - 36;
	ih = ph - 94;
	rh = 18;
	gap = 2;
	live_drag = BM_Opt_IsLiveColorDrag();
	// v_glslgamma_2d is no longer forced here every frame; RESET DEFAULTS sets it.

	vis = max(1, floor((ih + gap) / (rh + gap)));
	max_scroll = max(0, OPT_VID_COUNT - vis);
	g_opt_scroll = bound(0, g_opt_scroll, max_scroll);

	if (live_drag)
	{
		i = g_active_slider - 1;
		r = i - g_opt_scroll;
		ry = iy + bound(0, r, vis - 1) * (rh + gap);
		BM_Options_DrawVideoRow(ix, ry, iw, rh, i, clicked);
		BM_DrawTextCentered(px + pw * 0.5, py + 42, "LIVE PREVIEW - RELEASE MOUSE TO RETURN TO OPTIONS", 8, COL_ACCENT, 0.88);
		return;
	}

	BM_BeginClip(ix, iy, iw, ih);
	for (i = 0; i < OPT_VID_COUNT; i = i + 1)
	{
		r = i - g_opt_scroll;
		if (r >= 0 && r < vis)
		{
			ry = iy + r * (rh + gap);
			BM_Options_DrawVideoRow(ix, ry, iw, rh, i, clicked);
		}
	}
	BM_EndClip();

	if (max_scroll > 0)
	{
		BM_Fill(ix + iw + 4, iy, 4, ih, COL_GLASS_DARK, 0.85);
		sb_h = max(18, ih * (vis / OPT_VID_COUNT));
		sb_y = iy + (ih - sb_h) * (g_opt_scroll / max_scroll);
		BM_Fill(ix + iw + 4, sb_y, 4, sb_h, COL_ACCENT, 0.85);
	}

	BM_Fill(px + 14, py + ph - 30, pw - 28, 1, COL_BORDER, 0.40);
	if (g_opt_status != "" && gettime() < g_opt_status_t)
		BM_DrawTextClipped(px + 14, py + ph - 20, pw - 246, g_opt_status, 8, COL_GOOD, 0.96, FALSE);
	else
		BM_DrawTextClipped(px + 14, py + ph - 20, pw - 246, "Drag sliders or click arrows  |  Wheel scrolls", 8, COL_MUTED, 0.88, FALSE);

	hov = BM_DrawButton(px + pw - 228, py + ph - 24, 90, 18, "SAVE CONFIG", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu2.wav");
		BM_Opt_SaveConfig();
	}

	hov = BM_DrawButton(px + pw - 132, py + ph - 24, 118, 18, "RESET DEFAULTS", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu2.wav");
		BM_Opt_ApplyVideoDefaults();
	}
};

// Simple Mode is judged from the render cvars BM_Opt_ApplySimpleMode turns off,
// not from `lowspec` (the old Combat+ CSQC menu toggles lowspec for decals only).
float() BM_Opt_IsSimpleMode =
{
	if (stof(cvar_string("r_bloom")) != 0) return FALSE;
	if (stof(cvar_string("r_shadow_realtime_dlight")) != 0) return FALSE;
	if (stof(cvar_string("r_shadow_gloss")) != 0) return FALSE;
	if (stof(cvar_string("r_glsl_offsetmapping")) != 0) return FALSE;
	if (stof(cvar_string("r_water")) != 0) return FALSE;
	return TRUE;
};

void(float ix, float ry, float iw, float rh, float idx, float clicked) BM_Options_DrawGraphicsRow =
{
	local float st, v, mi, on;
	local string lbl, sv;

	if (idx == 0)
	{
		on = BM_Opt_IsSimpleMode();
		st = BM_DrawStepper(ix, ry, iw, rh, "SIMPLE MODE", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			BM_Opt_ApplySimpleMode(!on);
			BM_PlaySound("sound/misc/menu2.wav");
		}
	}
	else if (idx == 1)
	{
		if (BM_Opt_IsSimpleMode()) { mi = 0; lbl = "Simple"; }
		else if (stof(cvar_string("r_water")) != 0 || stof(cvar_string("r_shadow_glossexact")) != 0) { mi = 2; lbl = "Pretty"; }
		else { mi = 1; lbl = "Default"; }
		st = BM_DrawStepper(ix, ry, iw, rh, "GRAPHICS PRESET", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			mi = modulo(mi + st + 3, 3);
			if (mi == 0) BM_Opt_ApplySimpleMode(TRUE);
			else if (mi == 1) BM_Opt_ApplySimpleMode(FALSE);
			else BM_Opt_ApplyPrettyPreset();
			BM_PlaySound("sound/misc/menu2.wav");
		}
	}
	else if (idx == 2)
	{
		v = bound(0, rint(stof(cvar_string("bm_hud_style"))), 4);
		if (v == 0) lbl = "Classic";
		else if (v == 1) lbl = "Island";
		else if (v == 2) lbl = "Route 99";
		else if (v == 3) lbl = "Cyberpop";
		else lbl = "Zen Zero";
		st = BM_DrawStepper(ix, ry, iw, rh, "HUD STYLE", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			v = modulo(v + st + 5, 5);
			cvar_set("bm_hud_style", ftos(v));
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 3)
	{
		on = (stof(cvar_string("r_shadow_realtime_dlight")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "DYNAMIC LIGHTS", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("r_shadow_realtime_dlight", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 4)
	{
		on = (stof(cvar_string("r_shadow_realtime_dlight_shadows")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "DYNAMIC SHADOWS", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("r_shadow_realtime_dlight_shadows", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 5)
	{
		on = (stof(cvar_string("r_bloom")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "BLOOM GLOW", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("r_bloom", on ? "0" : "1");
			cvar_set("r_bloom_blur", "0.1");
			cvar_set("r_bloom_brighten", "0.1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 6)
	{
		if (stof(cvar_string("r_glsl_offsetmapping_reliefmapping")) != 0) { mi = 2; lbl = "Relief"; }
		else if (stof(cvar_string("r_shadow_gloss")) != 0 || stof(cvar_string("r_glsl_offsetmapping")) != 0) { mi = 1; lbl = "Normal"; }
		else { mi = 0; lbl = "Off"; }
		st = BM_DrawStepper(ix, ry, iw, rh, "GLOSS & RELIEF", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			mi = modulo(mi + st + 3, 3);
			if (mi == 0)
			{
				cvar_set("r_shadow_gloss", "0");
				cvar_set("r_glsl_offsetmapping", "0");
				cvar_set("r_glsl_offsetmapping_reliefmapping", "0");
			}
			else if (mi == 1)
			{
				cvar_set("r_shadow_gloss", "1");
				cvar_set("r_glsl_offsetmapping", "1");
				cvar_set("r_glsl_offsetmapping_reliefmapping", "0");
			}
			else
			{
				cvar_set("r_shadow_gloss", "1");
				cvar_set("r_glsl_offsetmapping", "1");
				cvar_set("r_glsl_offsetmapping_reliefmapping", "1");
			}
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 7)
	{
		on = (stof(cvar_string("r_water")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "WATER REFLECTIONS", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("r_water", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 8)
	{
		v = stof(cvar_string("cl_particles_quality"));
		if (v <= 0.6) { mi = 0; lbl = "Low"; }
		else if (v <= 0.85) { mi = 1; lbl = "Medium"; }
		else { mi = 2; lbl = "Full"; }
		st = BM_DrawStepper(ix, ry, iw, rh, "PARTICLE DETAIL", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			mi = modulo(mi + st + 3, 3);
			if (mi == 0) cvar_set("cl_particles_quality", "0.5");
			else if (mi == 1) cvar_set("cl_particles_quality", "0.8");
			else cvar_set("cl_particles_quality", "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 9)
	{
		on = (stof(cvar_string("cl_decals")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "IMPACT DECALS", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("cl_decals", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 10)
	{
		v = stof(cvar_string("cl_decals_max"));
		if (v <= 64) { mi = 0; lbl = "64"; }
		else if (v <= 128) { mi = 1; lbl = "128"; }
		else if (v <= 256) { mi = 2; lbl = "256"; }
		else { mi = 3; lbl = "512"; }
		st = BM_DrawStepper(ix, ry, iw, rh, "MAX DECALS", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			mi = modulo(mi + st + 4, 4);
			if (mi == 0) cvar_set("cl_decals_max", "64");
			else if (mi == 1) cvar_set("cl_decals_max", "128");
			else if (mi == 2) cvar_set("cl_decals_max", "256");
			else cvar_set("cl_decals_max", "512");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 11)
	{
		v = stof(cvar_string("cl_decals_time"));
		if (v <= 8) { mi = 0; lbl = "10s"; }
		else if (v <= 12) { mi = 1; lbl = "16s"; }
		else if (v <= 18) { mi = 2; lbl = "20s"; }
		else { mi = 3; lbl = "30s"; }
		st = BM_DrawStepper(ix, ry, iw, rh, "DECAL LIFETIME", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			mi = modulo(mi + st + 4, 4);
			cvar_set("cl_decals_fadetime", "4");
			if (mi == 0) cvar_set("cl_decals_time", "6");
			else if (mi == 1) cvar_set("cl_decals_time", "12");
			else if (mi == 2) cvar_set("cl_decals_time", "16");
			else cvar_set("cl_decals_time", "26");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 12)
	{
		v = bound(0, rint(stof(cvar_string("gl_picmip"))), 2);
		if (v == 0) lbl = "Full";
		else if (v == 1) lbl = "Medium";
		else lbl = "Low";
		st = BM_DrawStepper(ix, ry, iw, rh, "TEXTURE QUALITY", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			v = modulo(v + st + 3, 3);
			cvar_set("gl_picmip", ftos(v));
			g_opt_vid_dirty = TRUE;
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 13)
	{
		sv = strtoupper(cvar_string("gl_texturemode"));
		on = (strstrofs(sv, "NEAREST") >= 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "TEXTURE FILTER", on ? "Retro" : "Smooth", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("gl_texturemode", on ? "GL_LINEAR_MIPMAP_LINEAR" : "GL_NEAREST_MIPMAP_LINEAR");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 14)
	{
		v = stof(cvar_string("gl_texture_anisotropy"));
		if (v <= 1) { mi = 0; lbl = "1x"; }
		else if (v <= 4) { mi = 1; lbl = "4x"; }
		else if (v <= 8) { mi = 2; lbl = "8x"; }
		else { mi = 3; lbl = "16x"; }
		st = BM_DrawStepper(ix, ry, iw, rh, "ANISOTROPIC", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			mi = modulo(mi + st + 4, 4);
			if (mi == 0) cvar_set("gl_texture_anisotropy", "1");
			else if (mi == 1) cvar_set("gl_texture_anisotropy", "4");
			else if (mi == 2) cvar_set("gl_texture_anisotropy", "8");
			else cvar_set("gl_texture_anisotropy", "16");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 15)
	{
		v = stof(cvar_string("vid_samples"));
		if (v <= 1) { mi = 0; lbl = "Off"; }
		else if (v <= 2) { mi = 1; lbl = "2x"; }
		else if (v <= 4) { mi = 2; lbl = "4x"; }
		else { mi = 3; lbl = "8x"; }
		st = BM_DrawStepper(ix, ry, iw, rh, "ANTI-ALIASING", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			mi = modulo(mi + st + 4, 4);
			if (mi == 0) cvar_set("vid_samples", "1");
			else if (mi == 1) cvar_set("vid_samples", "2");
			else if (mi == 2) cvar_set("vid_samples", "4");
			else cvar_set("vid_samples", "8");
			g_opt_vid_dirty = TRUE;
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 16)
	{
		v = stof(cvar_string("r_minlight"));
		if (v <= 0) { mi = 0; lbl = "Off"; }
		else if (v <= 3) { mi = 1; lbl = "Default (3)"; }
		else if (v <= 6) { mi = 2; lbl = "Medium (6)"; }
		else { mi = 3; lbl = "Bright (10)"; }
		st = BM_DrawStepper(ix, ry, iw, rh, "MIN MODEL LIGHT", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			mi = modulo(mi + st + 4, 4);
			if (mi == 0) cvar_set("r_minlight", "0");
			else if (mi == 1) cvar_set("r_minlight", "3");
			else if (mi == 2) cvar_set("r_minlight", "6");
			else cvar_set("r_minlight", "10");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 17)
	{
		on = (stof(cvar_string("gl_overbright_models")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "OVERBRIGHT MODELS", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("gl_overbright_models", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 18)
	{
		on = (stof(cvar_string("r_nearest_conchars")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "SHARP CONSOLE TEXT", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("r_nearest_conchars", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 19)
	{
		on = (stof(cvar_string("bright_skins")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "BRIGHT PLAYER SKINS", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("bright_skins", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 20)
	{
		on = (stof(cvar_string("centered_weapons")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "CENTERED WEAPONS", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("centered_weapons", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 21)
	{
		on = (stof(cvar_string("cl_bob")) > 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "VIEW BOBBING", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("cl_bob", on ? "0" : "0.02");
			cvar_set("cl_rollangle", on ? "0" : "2");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 22)
	{
		v = bound(0, rint(stof(cvar_string("crosshair"))), 7);
		lbl = (v == 0) ? "Off" : strcat("Style ", ftos(v));
		st = BM_DrawStepper(ix, ry, iw, rh, "CROSSHAIR", lbl, FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			v = modulo(v + st + 8, 8);
			cvar_set("crosshair", ftos(v));
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 23)
	{
		on = (stof(cvar_string("bm_bot_tags")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "BOT NAMEPLATES", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("bm_bot_tags", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 24)
	{
		on = (stof(cvar_string("bm_player_tags")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "PLAYER NAMEPLATES", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("bm_player_tags", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else
	{
		on = (stof(cvar_string("showfps")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "SHOW FPS", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("showfps", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
};

void(float px, float py, float pw, float ph, float clicked) BM_Options_DrawGraphics =
{
	local float ix, iy, iw, ih, rh, gap, vis, max_scroll, i, r, ry, hov, sb_h, sb_y;

	ix = px + 14;
	iy = py + 58;
	iw = pw - 36;
	ih = ph - 94;
	rh = 18;
	gap = 2;

	vis = max(1, floor((ih + gap) / (rh + gap)));
	max_scroll = max(0, OPT_GFX_COUNT - vis);
	g_opt_scroll = bound(0, g_opt_scroll, max_scroll);

	BM_BeginClip(ix, iy, iw, ih);
	for (i = 0; i < OPT_GFX_COUNT; i = i + 1)
	{
		r = i - g_opt_scroll;
		if (r >= 0 && r < vis)
		{
			ry = iy + r * (rh + gap);
			BM_Options_DrawGraphicsRow(ix, ry, iw, rh, i, clicked);
		}
	}
	BM_EndClip();

	if (max_scroll > 0)
	{
		BM_Fill(ix + iw + 4, iy, 4, ih, COL_GLASS_DARK, 0.85);
		sb_h = max(18, ih * (vis / OPT_GFX_COUNT));
		sb_y = iy + (ih - sb_h) * (g_opt_scroll / max_scroll);
		BM_Fill(ix + iw + 4, sb_y, 4, sb_h, COL_ACCENT, 0.85);
	}

	BM_Fill(px + 14, py + ph - 30, pw - 28, 1, COL_BORDER, 0.40);
	if (g_opt_status != "" && gettime() < g_opt_status_t)
		BM_DrawTextClipped(px + 14, py + ph - 20, pw - 246, g_opt_status, 8, COL_GOOD, 0.96, FALSE);
	else
		BM_DrawTextClipped(px + 14, py + ph - 20, pw - 246, "Simple Mode for max FPS  |  Wheel scrolls", 8, COL_MUTED, 0.88, FALSE);

	hov = BM_DrawButton(px + pw - 228, py + ph - 24, 90, 18, "SAVE CONFIG", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu2.wav");
		BM_Opt_SaveConfig();
	}

	hov = BM_DrawButton(px + pw - 132, py + ph - 24, 118, 18, "RESET DEFAULTS", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu2.wav");
		BM_Opt_ApplyGraphicsDefaults();
	}
};

void(float px, float py, float pw, float ph, float clicked) BM_Options_DrawBindList =
{
	local float ix, iy, iw, ih, rh, gap, vis, total, max_scroll, i, r, ry, hov, listening;
	local float sb_h, sb_y;
	local string lbl, cmd, kstr;
	local vector bg, brd, kcol;

	total = (g_opt_tab == OPT_TAB_CONTROLS) ? OPT_CTRL_COUNT : OPT_WEP_COUNT;
	ix = px + 14;
	iy = py + 58;
	iw = pw - 36;
	ih = ph - 94;
	rh = 19;
	gap = 3;

	vis = max(1, floor((ih + gap) / (rh + gap)));
	max_scroll = max(0, total - vis);
	g_opt_scroll = bound(0, g_opt_scroll, max_scroll);

	BM_BeginClip(ix, iy, iw, ih);
	for (i = 0; i < total; i = i + 1)
	{
		r = i - g_opt_scroll;
		if (r >= 0 && r < vis)
		{
			ry = iy + r * (rh + gap);
			lbl = BM_Opt_BindLabel(g_opt_tab, i);
			cmd = BM_Opt_BindCmd(g_opt_tab, i);
			listening = (g_bind_listen_idx == i);
			hov = BM_MouseIn(ix, ry, iw, rh);

			bg = listening ? '0.52 0.14 0.04' : (hov ? COL_GLASS_HOVER : COL_GLASS_CARD);
			brd = listening ? COL_ACCENT : (hov ? COL_ACCENT : COL_BORDER);
			BM_Fill(ix, ry, iw, rh, bg, 0.85);
			BM_Outline(ix, ry, iw, rh, brd, (listening || hov) ? 0.94 : 0.45, 1);

			BM_DrawTextClipped(ix + 8, ry + 5, iw - 150, lbl, 8, listening ? COL_ACCENT : COL_TEXT, 0.96, FALSE);

			if (listening)
			{
				kstr = "PRESS KEY (ESC/DEL)";
				kcol = COL_ACCENT;
			}
			else
			{
				kstr = BM_Opt_GetBoundKeys(cmd);
				kcol = (kstr == "UNBOUND") ? COL_BAD : COL_ACCENT;
			}
			BM_DrawTextRight(ix + iw - 8, ry + 5, kstr, 8, kcol, 0.96);

			if (clicked && hov)
			{
				g_click_consumed = TRUE;
				g_bind_listen_idx = i;
				BM_PlaySound("sound/misc/menu1.wav");
				BM_EndClip();
				return;
			}
		}
	}
	BM_EndClip();

	if (max_scroll > 0)
	{
		BM_Fill(ix + iw + 4, iy, 4, ih, COL_GLASS_DARK, 0.85);
		sb_h = max(18, ih * (vis / total));
		sb_y = iy + (ih - sb_h) * (g_opt_scroll / max_scroll);
		BM_Fill(ix + iw + 4, sb_y, 4, sb_h, COL_ACCENT, 0.85);
	}

	BM_Fill(px + 14, py + ph - 30, pw - 28, 1, COL_BORDER, 0.40);
	if (g_bind_listen_idx >= 0)
		BM_DrawTextClipped(px + 14, py + ph - 20, pw - 164, "Press key/mouse to bind | DEL clear | ESC cancel", 8, COL_ACCENT, 0.95, FALSE);
	else
		BM_DrawTextClipped(px + 14, py + ph - 20, pw - 164, "Click row to rebind  |  Mouse wheel scrolls", 8, COL_MUTED, 0.88, FALSE);

	hov = BM_DrawButton(px + pw - 144, py + ph - 24, 130, 18, "RESET DEFAULTS", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		BM_PlaySound("sound/misc/menu2.wav");
		localcmd("exec bm_binds.cfg\n");
	}
};

void(float clicked) BM_Options_Draw =
{
	local float px, py, pw, ph, hov, live_drag;
	local vector tsz;

	px = floor(g_vw * 0.12);
	py = 14;
	pw = g_vw - px * 2;
	ph = g_vh - 28;
	live_drag = BM_Opt_IsLiveColorDrag();

	if (live_drag)
	{
		BM_Options_DrawVideo(px, py, pw, ph, clicked);
		return;
	}

	// Classic Quake side plaque + OPTIONS title plaque
	drawpic((px - 36) * '1 0 0' + (py + 2) * '0 1 0', "gfx/qplaque.lmp", '32 144 0', '1 1 1', 1.0, 0);
	BM_DrawGlassPanel(px, py, pw, ph, 0.82, COL_BORDER, 0.65, 2);

	tsz = getimagesize("gfx/p_option.lmp");
	if (tsz_x <= 0) tsz = '96 24 0';
	drawpic((px + 12) * '1 0 0' + (py + 5) * '0 1 0', "gfx/p_option.lmp", tsz * 0.85, '1 1 1', 1.0, 0);

	if (g_opt_vid_dirty)
	{
		hov = BM_DrawButton(px + pw - 162, py + 7, 90, 18, "APPLY VIDEO", FALSE, TRUE);
		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			g_opt_vid_dirty = FALSE;
			BM_PlaySound("sound/misc/menu2.wav");
			localcmd("saveconfig; vid_restart\n");
			return;
		}
	}

	hov = BM_DrawButton(px + pw - 66, py + 7, 54, 18, "BACK", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		g_active_slider = 0;
		BM_PlaySound("sound/misc/menu3.wav");
		g_page = PAGE_MAIN;
		return;
	}

	// Tabs
	hov = BM_DrawTab(px + 14, py + 32, 112, 18, "VIDEO & AUDIO", (g_opt_tab == OPT_TAB_VIDEO));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		g_active_slider = 0;
		g_opt_scroll = 0;
		g_opt_tab = OPT_TAB_VIDEO;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	hov = BM_DrawTab(px + 130, py + 32, 86, 18, "GRAPHICS", (g_opt_tab == OPT_TAB_GRAPHICS));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		g_active_slider = 0;
		g_opt_scroll = 0;
		g_opt_tab = OPT_TAB_GRAPHICS;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	hov = BM_DrawTab(px + 220, py + 32, 86, 18, "CONTROLS", (g_opt_tab == OPT_TAB_CONTROLS));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		g_active_slider = 0;
		g_opt_scroll = 0;
		g_opt_tab = OPT_TAB_CONTROLS;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	hov = BM_DrawTab(px + 310, py + 32, 86, 18, "WEAPONS", (g_opt_tab == OPT_TAB_WEAPONS));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		g_active_slider = 0;
		g_opt_scroll = 0;
		g_opt_tab = OPT_TAB_WEAPONS;
		BM_PlaySound("sound/misc/menu1.wav");
	}

	if (g_opt_tab == OPT_TAB_VIDEO)
		BM_Options_DrawVideo(px, py, pw, ph, clicked);
	else if (g_opt_tab == OPT_TAB_GRAPHICS)
		BM_Options_DrawGraphics(px, py, pw, ph, clicked);
	else
		BM_Options_DrawBindList(px, py, pw, ph, clicked);
};

void(float key, float ascii) BM_Options_KeyDown =
{
	local string cmd, kname;

	if (g_bind_listen_idx >= 0)
	{
		cmd = BM_Opt_BindCmd(g_opt_tab, g_bind_listen_idx);
		if (key == K_ESCAPE)
		{
			g_bind_listen_idx = -1;
			BM_PlaySound("sound/misc/menu3.wav");
			return;
		}
		if (key == K_DEL || key == K_BACKSPACE)
		{
			BM_Opt_ClearCmdBinds(cmd);
			g_bind_listen_idx = -1;
			BM_PlaySound("sound/misc/menu3.wav");
			return;
		}
		kname = keynumtostring(key);
		if (kname != "")
		{
			BM_Opt_ClearCmdBinds(cmd);
			setkeybind(key, cmd, 0);
			g_bind_listen_idx = -1;
			BM_PlaySound("sound/misc/menu2.wav");
		}
		return;
	}

	if (key == K_ESCAPE)
	{
		g_active_slider = 0;
		BM_PlaySound("sound/misc/menu3.wav");
		g_page = PAGE_MAIN;
	}
	else if (key == K_TAB)
	{
		g_opt_tab = modulo(g_opt_tab + 1, OPT_TAB_COUNT);
		g_opt_scroll = 0;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	else if (key == K_MWHEELUP || key == K_PGUP || key == K_UPARROW)
	{
		g_opt_scroll = max(0, g_opt_scroll - 1);
	}
	else if (key == K_MWHEELDOWN || key == K_PGDN || key == K_DOWNARROW)
	{
		g_opt_scroll = g_opt_scroll + 1;
	}
};
