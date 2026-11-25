// BakersfieldQuake MenuQC - Classic Default Quake / Zircon Options, Graphics, Controls & Weapons

float OPT_TAB_VIDEO    = 0;
float OPT_TAB_GRAPHICS = 1;
float OPT_TAB_CONTROLS = 2;
float OPT_TAB_WEAPONS  = 3;
float OPT_TAB_COUNT    = 4;

float OPT_VID_COUNT    = 16;
float OPT_GFX_COUNT    = 27;
float OPT_CTRL_COUNT   = 21;
float OPT_VEH_COUNT    = 9;
float OPT_WEP_COUNT    = 20;

float OPT_RES_MAX      = 64;

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
float g_opt_res_count;
float g_opt_res_w[64];
float g_opt_res_h[64];

void(float w, float h) BM_Opt_AddRes =
{
	local float i;

	w = rint(w);
	h = rint(h);
	if (w < 800 || h < 600)
		return;
	for (i = 0; i < g_opt_res_count; i = i + 1)
	{
		if (g_opt_res_w[i] == w && g_opt_res_h[i] == h)
			return;
	}
	if (g_opt_res_count >= OPT_RES_MAX)
		return;
	g_opt_res_w[g_opt_res_count] = w;
	g_opt_res_h[g_opt_res_count] = h;
	g_opt_res_count = g_opt_res_count + 1;
};

void() BM_Opt_BuildResList =
{
	local float m, i, j, tw, th, cur_w, cur_h, best_i, best_d, d;
	local vector res;

	g_opt_res_count = 0;
	for (m = 0; m < 256; m = m + 1)
	{
		res = getresolution(m);
		if (res_x <= 0 || res_y <= 0)
			break;
		BM_Opt_AddRes(res_x, res_y);
	}

	// Clean fallback list if getresolution() returned nothing
	if (g_opt_res_count <= 0)
	{
		BM_Opt_AddRes(1280, 720);
		BM_Opt_AddRes(1280, 800);
		BM_Opt_AddRes(1366, 768);
		BM_Opt_AddRes(1600, 900);
		BM_Opt_AddRes(1680, 1050);
		BM_Opt_AddRes(1920, 1080);
		BM_Opt_AddRes(1920, 1200);
		BM_Opt_AddRes(2560, 1080);
		BM_Opt_AddRes(2560, 1440);
		BM_Opt_AddRes(2560, 1600);
		BM_Opt_AddRes(3440, 1440);
		BM_Opt_AddRes(3840, 1600);
		BM_Opt_AddRes(3840, 2160);
		BM_Opt_AddRes(5120, 1440);
	}

	cur_w = rint(stof(cvar_string("vid_width")));
	cur_h = rint(stof(cvar_string("vid_height")));
	if (cur_w >= 800 && cur_h >= 600)
		BM_Opt_AddRes(cur_w, cur_h);
	else
	{
		cur_w = 1920;
		cur_h = 1080;
	}

	// Sort ascending by (width, height)
	for (i = 0; i < g_opt_res_count - 1; i = i + 1)
	{
		for (j = i + 1; j < g_opt_res_count; j = j + 1)
		{
			if (g_opt_res_w[j] < g_opt_res_w[i] || (g_opt_res_w[j] == g_opt_res_w[i] && g_opt_res_h[j] < g_opt_res_h[i]))
			{
				tw = g_opt_res_w[i];
				th = g_opt_res_h[i];
				g_opt_res_w[i] = g_opt_res_w[j];
				g_opt_res_h[i] = g_opt_res_h[j];
				g_opt_res_w[j] = tw;
				g_opt_res_h[j] = th;
			}
		}
	}

	best_i = 0;
	best_d = 999999;
	for (i = 0; i < g_opt_res_count; i = i + 1)
	{
		d = fabs(g_opt_res_w[i] - cur_w) + fabs(g_opt_res_h[i] - cur_h);
		if (d < best_d)
		{
			best_d = d;
			best_i = i;
		}
	}
	g_opt_res_idx = best_i;
};

void(float w, float h) BM_Opt_SyncVideoDims =
{
	local float cw;
	local string ws, hs;

	w = rint(w);
	h = rint(h);
	if (w < 800 || h < 600)
	{
		w = 1920;
		h = 1080;
	}
	ws = ftos(w);
	hs = ftos(h);
	cw = bound(480, rint(360 * w / h), 1280);

	cvar_set("vid_width", ws);
	cvar_set("vid_height", hs);
	cvar_set("_vid_fullscreen_width", ws);
	cvar_set("_vid_fullscreen_height", hs);
	cvar_set("_vid_window_width", ws);
	cvar_set("_vid_window_height", hs);
	cvar_set("vid_conwidth", ftos(cw));
	cvar_set("vid_conheight", "360");
};

// 0 = Borderless, 1 = Fullscreen, 2 = Windowed
float() BM_Opt_GetDisplayMode =
{
	local float fs, dfs, bl;

	fs = (stof(cvar_string("vid_fullscreen")) != 0);
	dfs = (stof(cvar_string("vid_desktopfullscreen")) != 0);
	bl = (stof(cvar_string("vid_borderless")) != 0);

	if ((fs && dfs) || (!fs && bl))
		return 0;
	if (fs)
		return 1;
	return 2;
};

string(float mode) BM_Opt_DisplayModeLabel =
{
	if (mode == 0) return "Borderless";
	if (mode == 1) return "Fullscreen";
	return "Windowed";
};

void(float mode) BM_Opt_ApplyDisplayMode =
{
	local float w, h;

	if (mode == 0)
	{
		cvar_set("vid_fullscreen", "1");
		cvar_set("vid_desktopfullscreen", "1");
		cvar_set("vid_borderless", "0");
	}
	else if (mode == 1)
	{
		cvar_set("vid_fullscreen", "1");
		cvar_set("vid_desktopfullscreen", "0");
		cvar_set("vid_borderless", "0");
	}
	else
	{
		cvar_set("vid_fullscreen", "0");
		cvar_set("vid_desktopfullscreen", "0");
		cvar_set("vid_borderless", "0");
	}

	if (g_opt_res_count > 0)
	{
		g_opt_res_idx = bound(0, g_opt_res_idx, g_opt_res_count - 1);
		w = g_opt_res_w[g_opt_res_idx];
		h = g_opt_res_h[g_opt_res_idx];
	}
	else
	{
		w = stof(cvar_string("vid_width"));
		h = stof(cvar_string("vid_height"));
	}
	BM_Opt_SyncVideoDims(w, h);
	g_opt_vid_dirty = TRUE;
};

void() BM_Options_Open =
{
	g_page = PAGE_OPTIONS;
	g_focus_input = INPUT_NONE;
	g_bind_listen_idx = -1;
	g_opt_scroll = 0;
	g_opt_ctrl_veh = 0;
	g_active_slider = 0;

	BM_Opt_BuildResList();
};

string(float idx) BM_Opt_ResLabel =
{
	if (g_opt_res_count <= 0)
		return "1920x1080";
	idx = bound(0, rint(idx), g_opt_res_count - 1);
	return strcat(ftos(g_opt_res_w[idx]), "x", ftos(g_opt_res_h[idx]));
};

void(float idx) BM_Opt_ApplyRes =
{
	if (g_opt_res_count <= 0)
		return;
	idx = bound(0, rint(idx), g_opt_res_count - 1);
	g_opt_res_idx = idx;
	BM_Opt_SyncVideoDims(g_opt_res_w[idx], g_opt_res_h[idx]);
	g_opt_vid_dirty = TRUE;
};

void(string msg) BM_Opt_SetStatus =
{
	g_opt_status = BM_ZoneSet(g_opt_status, msg);
	g_opt_status_t = gettime() + 2.5;
};

void() BM_Opt_ApplyVideoAndSave =
{
	g_opt_vid_dirty = FALSE;
	// Zircon's saveconfig syncs vid_fullscreen/vid_width/vid_height back to the live window
	// before writing config.cfg, so vid_restart must apply the new mode first.
	localcmd("vid_restart; saveconfig\n");
	BM_Opt_SetStatus("VIDEO APPLIED & SAVED TO CONFIG.CFG");
};

void() BM_Opt_SaveConfig =
{
	if (g_opt_vid_dirty)
	{
		BM_Opt_ApplyVideoAndSave();
		return;
	}
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

void(string cname, float target_v, string val_str) BM_Opt_SetVidFloatCvar =
{
	local string cur;

	cur = cvar_string(cname);
	if (cur != "" && fabs(stof(cur) - target_v) > 0.001)
		g_opt_vid_dirty = TRUE;
	cvar_set(cname, val_str);
};

void() BM_Opt_ResetDietCvars =
{
	BM_Opt_SetVidFloatCvar("gl_picmip", 0, "0");
	BM_Opt_SetVidFloatCvar("gl_picmip_world", 0, "0");
	BM_Opt_SetVidFloatCvar("gl_picmip_other", 0, "0");
	BM_Opt_SetVidFloatCvar("gl_picmip_sprites", 0, "0");
	BM_Opt_SetVidFloatCvar("gl_picmip_force", 0, "0");
	BM_Opt_SetVidFloatCvar("gl_max_size", 2048, "2048");
	BM_Opt_SetVidFloatCvar("gl_texturecompression", 0, "0");
	cvar_set("r_dynamic", "1");
	cvar_set("menu_background", "1");
	cvar_set("r_lerpmodels", "1");
	cvar_set("r_lerplightstyles", "1");
	cvar_set("r_lerpsprites", "0");
	cvar_set("v_glslgamma_2d", "1");
};

void(float enable_simple) BM_Opt_ApplySimpleMode =
{
	BM_Opt_ResetDietCvars();
	if (enable_simple)
	{
		cvar_set("lowspec", "1");
		cvar_set("r_bloom", "0");
		cvar_set("r_shadow_realtime_dlight", "0");
		cvar_set("r_shadow_realtime_dlight_shadows", "0");
		cvar_set("r_shadow_gloss", "0");
		cvar_set("r_shadow_glossexact", "0");
		cvar_set("r_shadow_shadowmapping", "0");
		cvar_set("r_shadow_usenormalmap", "0");
		BM_Opt_SetVidFloatCvar("r_load_normalmap", 0, "0");
		BM_Opt_SetVidFloatCvar("r_load_gloss", 0, "0");
		cvar_set("r_glsl_offsetmapping", "0");
		cvar_set("r_glsl_offsetmapping_reliefmapping", "0");
		cvar_set("r_glsl_deluxemapping", "0");
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
		BM_Opt_SetVidFloatCvar("vid_samples", 1, "1");
		cvar_set("gl_texture_anisotropy", "4");
		cvar_set("gl_texturemode", "GL_LINEAR_MIPMAP_LINEAR");
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
		cvar_set("r_shadow_shadowmapping_texturesize", "4096");
		cvar_set("r_shadow_usenormalmap", "1");
		BM_Opt_SetVidFloatCvar("r_load_normalmap", 1, "1");
		BM_Opt_SetVidFloatCvar("r_load_gloss", 1, "1");
		cvar_set("r_glsl_offsetmapping", "1");
		cvar_set("r_glsl_offsetmapping_reliefmapping", "0");
		cvar_set("r_glsl_deluxemapping", "1");
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
		BM_Opt_SetVidFloatCvar("vid_samples", 4, "4");
		cvar_set("gl_texture_anisotropy", "16");
		cvar_set("gl_texturemode", "GL_LINEAR_MIPMAP_LINEAR");
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
	cvar_set("r_water", "1");
	cvar_set("r_water_lowquality", "0");
	cvar_set("r_water_resolutionmultiplier", "0.75");
	cvar_set("r_wateralpha", "0.5");
	cvar_set("r_glsl_saturation", "1.1");
};

void() BM_Opt_ApplyGraphicsDefaults =
{
	BM_Opt_ApplySimpleMode(FALSE);
	cvar_set("r_nearest_conchars", "0");
	cvar_set("bright_skins", "1");
	cvar_set("centered_weapons", "0");
	cvar_set("cl_bob", "0");
	cvar_set("cl_rollangle", "0");
	cvar_set("sv_rollangle", "0");
	cvar_set("crosshair", "5");
	cvar_set("bm_hud_style", "0");
	cvar_set("bm_ui_font", "1");
	cvar_set("bm_bot_tags", "1");
	cvar_set("bm_player_tags", "1");
	cvar_set("showfps", "1");
	localcmd("saveconfig\n");
	BM_Opt_SetStatus("CLEAN GRAPHICS DEFAULTS APPLIED");
};

string(float idx) BM_Opt_VehLabel =
{
	if (idx == 0) return "Accelerate";
	if (idx == 1) return "Brake / Reverse";
	if (idx == 2) return "Steer Left";
	if (idx == 3) return "Steer Right";
	if (idx == 4) return "Handbrake / Hop";
	if (idx == 5) return "Nitro Boost / Swoop";
	if (idx == 6) return "Horn / Fire";
	if (idx == 7) return "Vehicle Exit";
	return "Vehicle Camera";
};

string(float idx) BM_Opt_VehCmd =
{
	if (idx == 0) return "+forward";
	if (idx == 1) return "+back";
	if (idx == 2) return "+moveleft";
	if (idx == 3) return "+moveright";
	if (idx == 4) return "+jump";
	if (idx == 5) return "+button4";
	if (idx == 6) return "+attack";
	if (idx == 7) return "impulse 86";
	return "impulse 87";
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

string g_opt_bk_cmd[20];
string g_opt_bk_val[20];
float  g_opt_bk_t[20];
float  g_opt_bk_rev;
float  g_opt_bk_next;

string(string cmd, float bmap) BM_Opt_GetBoundKeys =
{
	local string raw, out, kname, kb;
	local float n, i, kn, rev, slot;

	if (bmap != 0)
	{
		rev = cvar("bm_veh_rev");
		if (rev != g_opt_bk_rev)
		{
			g_opt_bk_rev = rev;
			for (i = 0; i < 20; i = i + 1)
				g_opt_bk_t[i] = 0;
		}
		for (i = 0; i < 20; i = i + 1)
		{
			if (g_opt_bk_t[i] > time && g_opt_bk_cmd[i] == cmd)
				return g_opt_bk_val[i];
		}
		out = "";
		for (i = 1; i < 768; i = i + 1)
		{
			kb = getkeybind(i, bmap);
			if (kb == cmd)
			{
				kname = strtoupper(keynumtostring(i));
				if (kname != "")
				{
					if (out == "")
						out = kname;
					else
						out = strcat(out, " / ", kname);
				}
			}
		}
		if (out == "")
			out = "UNBOUND";
		slot = g_opt_bk_next;
		g_opt_bk_next = slot + 1;
		if (g_opt_bk_next >= 20)
			g_opt_bk_next = 0;
		if (g_opt_bk_cmd[slot] != "")
			strunzone(g_opt_bk_cmd[slot]);
		if (g_opt_bk_val[slot] != "")
			strunzone(g_opt_bk_val[slot]);
		g_opt_bk_cmd[slot] = strzone(cmd);
		g_opt_bk_val[slot] = strzone(out);
		g_opt_bk_t[slot] = time + 0.35;
		return out;
	}

	raw = findkeysforcommand(cmd, 0);
	if (raw == "")
	{
		if (cmd == "impulse 41")
			return BM_Opt_GetBoundKeys("reload", 0);
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
		return BM_Opt_GetBoundKeys("reload", 0);
	if (out == "")
		return "UNBOUND";
	return out;
};

void(string cmd, float bmap) BM_Opt_ClearCmdBinds =
{
	local string raw;
	local float n, i, kn, keys_to_clear[8], cnt;

	if (bmap != 0)
	{
		for (i = 1; i < 768; i = i + 1)
		{
			if (getkeybind(i, bmap) == cmd)
				setkeybind(i, "", bmap);
		}
		return;
	}

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
		BM_Opt_ClearCmdBinds("reload", 0);
};

void() BM_Opt_BumpVehRev =
{
	cvar_set("bm_veh_rev", ftos(cvar("bm_veh_rev") + 1));
};

void() BM_Opt_SaveVehConfig =
{
	local float fh, k;
	local string cmd, kn;

	fh = fopen("vehicle_binds.cfg", FILE_WRITE);
	if (fh >= 0)
	{
		fputs(fh, "// BakersfieldQuake Vehicle Config (bindmap 1) - managed by Options > Controls\n");
		for (k = 1; k < 768; k = k + 1)
		{
			cmd = getkeybind(k, 1);
			if (cmd != "")
			{
				kn = keynumtostring(k);
				if (kn != "" && kn != "\"")
					fputs(fh, strcat("in_bind 1 \"", kn, "\" \"", cmd, "\"\n"));
			}
		}
		fclose(fh);
	}
	BM_Opt_BumpVehRev();
	localcmd("saveconfig\n");
};

float() BM_Opt_HasAnyVehBind =
{
	local float k;

	for (k = 1; k < 768; k = k + 1)
	{
		if (getkeybind(k, 1) != "")
			return TRUE;
	}
	return FALSE;
};

void() BM_Opt_SeedVehicleDefaults =
{
	local float k;

	for (k = 1; k < 768; k = k + 1)
	{
		if (getkeybind(k, 1) != "")
			setkeybind(k, "", 1);
	}
	k = stringtokeynum("w"); if (k > 0) setkeybind(k, "+forward", 1);
	k = stringtokeynum("s"); if (k > 0) setkeybind(k, "+back", 1);
	k = stringtokeynum("a"); if (k > 0) setkeybind(k, "+moveleft", 1);
	k = stringtokeynum("d"); if (k > 0) setkeybind(k, "+moveright", 1);
	setkeybind(K_SPACE, "+jump", 1);
	setkeybind(K_SHIFT, "+button4", 1);
	setkeybind(K_MOUSE1, "+attack", 1);
	k = stringtokeynum("h"); if (k > 0) setkeybind(k, "impulse 86", 1);
	k = stringtokeynum("k"); if (k > 0) setkeybind(k, "impulse 87", 1);
	cvar_set("bm_veh_init", "1");
	BM_Opt_SaveVehConfig();
};

float() BM_Opt_IsLiveColorDrag =
{
	return (g_opt_tab == OPT_TAB_VIDEO && g_mouse1_down && g_active_slider >= SL_HDR && g_active_slider <= SL_BRIGHT);
};

void(float ix, float ry, float iw, float rh, float idx, float clicked) BM_Options_DrawVideoRow =
{
	local float st, nv, sens, mpitch, fv, gam, con, br, hdr, vol, bgm, dmode, vs_on;
	local float fps_v, fps_i, filt_on, run_on, lnch_on, next_idx;
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
		dmode = BM_Opt_GetDisplayMode();
		st = BM_DrawStepper(ix, ry, iw, rh, "DISPLAY MODE", BM_Opt_DisplayModeLabel(dmode), FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			dmode = modulo(dmode + st + 3, 3);
			BM_Opt_ApplyDisplayMode(dmode);
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 14)
	{
		st = BM_DrawStepper(ix, ry, iw, rh, "RESOLUTION", BM_Opt_ResLabel(g_opt_res_idx), FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			if (g_opt_res_count > 0)
			{
				next_idx = bound(0, g_opt_res_idx + st, g_opt_res_count - 1);
				if (next_idx != g_opt_res_idx)
					BM_Opt_ApplyRes(next_idx);
			}
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 15)
	{
		lnch_on = (stof(cvar_string("bm_show_launcher")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "LAUNCHER ON NEXT START", lnch_on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			if (!lnch_on)
			{
				cvar_set("bm_show_launcher", "1");
				localcmd("saveconfig\n");
				BM_Opt_SetStatus("DISPLAY SETUP WILL OPEN ON NEXT LAUNCH");
			}
			else
			{
				cvar_set("bm_show_launcher", "0");
				localcmd("saveconfig\n");
				BM_Opt_SetStatus("DISPLAY SETUP SKIPPED ON NEXT LAUNCH");
			}
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
};

void(float px, float py, float pw, float ph, float clicked) BM_Options_DrawVideo =
{
	local float ix, iy, iw, ih, rh, gap, vis, max_scroll, i, r, ry, live_drag, hov, sb_h, sb_y;
	local float in_clip, row_clicked;

	if (g_opt_res_count <= 0)
		BM_Opt_BuildResList();

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

	in_clip = BM_MouseIn(ix, iy, iw, ih);
	row_clicked = (clicked && !g_click_consumed && in_clip);

	BM_BeginClip(ix, iy, iw, ih);
	for (i = 0; i < OPT_VID_COUNT; i = i + 1)
	{
		r = i - g_opt_scroll;
		if (r >= 0 && r < vis)
		{
			ry = iy + r * (rh + gap);
			BM_Options_DrawVideoRow(ix, ry, iw, rh, i, row_clicked);
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
	if (clicked && !g_click_consumed && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu2.wav");
		BM_Opt_SaveConfig();
	}

	hov = BM_DrawButton(px + pw - 132, py + ph - 24, 118, 18, "RESET DEFAULTS", FALSE, FALSE);
	if (clicked && !g_click_consumed && hov)
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
		else if (stof(cvar_string("r_water")) != 0 || stof(cvar_string("r_shadow_glossexact")) != 0) { mi = 2; lbl = "High"; }
		else { mi = 1; lbl = "Normal"; }
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
		on = (stof(cvar_string("bm_ui_font")) != 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "UI FONT", on ? "Roboto" : "Classic", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("bm_ui_font", on ? "0" : "1");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 4)
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
	else if (idx == 5)
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
	else if (idx == 6)
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
	else if (idx == 7)
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
	else if (idx == 8)
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
	else if (idx == 9)
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
	else if (idx == 10)
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
	else if (idx == 11)
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
	else if (idx == 12)
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
	else if (idx == 13)
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
			if (v == 0)
			{
				cvar_set("gl_picmip_world", "0");
				cvar_set("gl_picmip_other", "0");
				cvar_set("gl_picmip_sprites", "0");
				cvar_set("gl_picmip_force", "0");
				cvar_set("gl_max_size", "2048");
			}
			g_opt_vid_dirty = TRUE;
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 14)
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
	else if (idx == 15)
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
	else if (idx == 16)
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
	else if (idx == 17)
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
	else if (idx == 18)
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
	else if (idx == 19)
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
	else if (idx == 20)
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
	else if (idx == 21)
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
	else if (idx == 22)
	{
		on = (stof(cvar_string("cl_bob")) > 0);
		st = BM_DrawStepper(ix, ry, iw, rh, "VIEW BOBBING", on ? "On" : "Off", FALSE, clicked);
		if (st != 0)
		{
			g_click_consumed = TRUE;
			cvar_set("cl_bob", on ? "0" : "0.02");
			cvar_set("cl_rollangle", on ? "0" : "2");
			cvar_set("sv_rollangle", on ? "0" : "2");
			BM_PlaySound("sound/misc/menu1.wav");
		}
	}
	else if (idx == 23)
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
	else if (idx == 24)
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
	else if (idx == 25)
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
	else if (idx == 26)
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
	local float in_clip, row_clicked;

	ix = px + 14;
	iy = py + 58;
	iw = pw - 36;
	ih = ph - 94;
	rh = 18;
	gap = 2;

	vis = max(1, floor((ih + gap) / (rh + gap)));
	max_scroll = max(0, OPT_GFX_COUNT - vis);
	g_opt_scroll = bound(0, g_opt_scroll, max_scroll);

	in_clip = BM_MouseIn(ix, iy, iw, ih);
	row_clicked = (clicked && !g_click_consumed && in_clip);

	BM_BeginClip(ix, iy, iw, ih);
	for (i = 0; i < OPT_GFX_COUNT; i = i + 1)
	{
		r = i - g_opt_scroll;
		if (r >= 0 && r < vis)
		{
			ry = iy + r * (rh + gap);
			BM_Options_DrawGraphicsRow(ix, ry, iw, rh, i, row_clicked);
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
	if (clicked && !g_click_consumed && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu2.wav");
		BM_Opt_SaveConfig();
	}

	hov = BM_DrawButton(px + pw - 132, py + ph - 24, 118, 18, "RESET DEFAULTS", FALSE, FALSE);
	if (clicked && !g_click_consumed && hov)
	{
		g_click_consumed = TRUE;
		BM_PlaySound("sound/misc/menu2.wav");
		BM_Opt_ApplyGraphicsDefaults();
	}
};

void(float px, float py, float pw, float ph, float clicked) BM_Options_DrawBindList =
{
	local float ix, iy, iw, ih, rh, gap, vis, total, max_scroll, i, r, ry, hov, listening;
	local float sb_h, sb_y, veh_on, bmap, in_clip;
	local string lbl, cmd, kstr;
	local vector bg, brd, kcol;

	ix = px + 14;
	iw = pw - 36;
	iy = py + 58;
	ih = ph - 94;
	veh_on = (cvar("bm_veh_config") != 0);

	if (g_opt_tab == OPT_TAB_CONTROLS)
	{
		if (!veh_on)
			g_opt_ctrl_veh = 0;

		hov = BM_DrawButton(ix, py + 56, 214, 18, veh_on ? "SEPARATE VEHICLE CONFIG: ON" : "SEPARATE VEHICLE CONFIG: OFF", veh_on, veh_on);
		if (clicked && !g_click_consumed && hov)
		{
			g_click_consumed = TRUE;
			g_bind_listen_idx = -1;
			g_opt_scroll = 0;
			BM_PlaySound("sound/misc/menu2.wav");
			if (!veh_on)
			{
				cvar_set("bm_veh_config", "1");
				veh_on = TRUE;
				if (cvar("bm_veh_init") == 0 || !BM_Opt_HasAnyVehBind())
					BM_Opt_SeedVehicleDefaults();
				else
				{
					BM_Opt_BumpVehRev();
					localcmd("saveconfig\n");
				}
				g_opt_ctrl_veh = 1;
			}
			else
			{
				cvar_set("bm_veh_config", "0");
				veh_on = FALSE;
				g_opt_ctrl_veh = 0;
				BM_Opt_BumpVehRev();
				localcmd("saveconfig\n");
			}
		}

		if (veh_on)
		{
			hov = BM_DrawTab(ix + iw - 144, py + 56, 70, 18, "ON FOOT", (g_opt_ctrl_veh == 0));
			if (clicked && !g_click_consumed && hov)
			{
				g_click_consumed = TRUE;
				g_bind_listen_idx = -1;
				g_opt_scroll = 0;
				g_opt_ctrl_veh = 0;
				BM_PlaySound("sound/misc/menu1.wav");
			}
			hov = BM_DrawTab(ix + iw - 70, py + 56, 70, 18, "VEHICLE", (g_opt_ctrl_veh == 1));
			if (clicked && !g_click_consumed && hov)
			{
				g_click_consumed = TRUE;
				g_bind_listen_idx = -1;
				g_opt_scroll = 0;
				g_opt_ctrl_veh = 1;
				BM_PlaySound("sound/misc/menu1.wav");
			}
		}

		iy = py + 79;
		ih = ph - 115;
	}

	bmap = (g_opt_tab == OPT_TAB_CONTROLS && g_opt_ctrl_veh) ? 1 : 0;
	total = (g_opt_tab == OPT_TAB_CONTROLS) ? (bmap ? OPT_VEH_COUNT : OPT_CTRL_COUNT) : OPT_WEP_COUNT;
	rh = 19;
	gap = 3;

	vis = max(1, floor((ih + gap) / (rh + gap)));
	max_scroll = max(0, total - vis);
	g_opt_scroll = bound(0, g_opt_scroll, max_scroll);
	in_clip = BM_MouseIn(ix, iy, iw, ih);

	BM_BeginClip(ix, iy, iw, ih);
	for (i = 0; i < total; i = i + 1)
	{
		r = i - g_opt_scroll;
		if (r >= 0 && r < vis)
		{
			ry = iy + r * (rh + gap);
			lbl = bmap ? BM_Opt_VehLabel(i) : BM_Opt_BindLabel(g_opt_tab, i);
			cmd = bmap ? BM_Opt_VehCmd(i) : BM_Opt_BindCmd(g_opt_tab, i);
			listening = (g_bind_listen_idx == i);
			hov = (in_clip && BM_MouseIn(ix, ry, iw, rh));

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
				kstr = BM_Opt_GetBoundKeys(cmd, bmap);
				kcol = (kstr == "UNBOUND") ? COL_BAD : COL_ACCENT;
			}
			BM_DrawTextRight(ix + iw - 8, ry + 5, kstr, 8, kcol, 0.96);

			if (clicked && !g_click_consumed && hov)
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
	if (clicked && !g_click_consumed && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		BM_PlaySound("sound/misc/menu2.wav");
		if (bmap == 1)
			BM_Opt_SeedVehicleDefaults();
		else
		{
			if (cvar("bm_veh_init") != 0)
				localcmd("exec bm_binds.cfg; exec data/vehicle_binds.cfg\n");	// fopen writes under data/ (MN-01)
			else
				localcmd("exec bm_binds.cfg\n");
			BM_Opt_BumpVehRev();
		}
	}
};

float() BM_Opt_CurrentMaxScroll =
{
	local float ph, ih, rh, gap, vis, total, bmap;

	ph = g_vh - 28;
	if (g_opt_tab == OPT_TAB_VIDEO)
	{
		ih = ph - 94;
		rh = 18;
		gap = 2;
		total = OPT_VID_COUNT;
	}
	else if (g_opt_tab == OPT_TAB_GRAPHICS)
	{
		ih = ph - 94;
		rh = 18;
		gap = 2;
		total = OPT_GFX_COUNT;
	}
	else if (g_opt_tab == OPT_TAB_CONTROLS)
	{
		ih = ph - 115;
		rh = 19;
		gap = 3;
		bmap = (g_opt_ctrl_veh && cvar("bm_veh_config") != 0) ? 1 : 0;
		total = bmap ? OPT_VEH_COUNT : OPT_CTRL_COUNT;
	}
	else
	{
		ih = ph - 94;
		rh = 19;
		gap = 3;
		total = OPT_WEP_COUNT;
	}
	vis = max(1, floor((ih + gap) / (rh + gap)));
	return max(0, total - vis);
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
			BM_PlaySound("sound/misc/menu2.wav");
			BM_Opt_ApplyVideoAndSave();
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
	local float bmap;

	if (g_bind_listen_idx >= 0)
	{
		bmap = (g_opt_tab == OPT_TAB_CONTROLS && g_opt_ctrl_veh && cvar("bm_veh_config") != 0) ? 1 : 0;
		cmd = bmap ? BM_Opt_VehCmd(g_bind_listen_idx) : BM_Opt_BindCmd(g_opt_tab, g_bind_listen_idx);
		if (key == K_ESCAPE)
		{
			g_bind_listen_idx = -1;
			BM_PlaySound("sound/misc/menu3.wav");
			return;
		}
		if (key == K_DEL || key == K_BACKSPACE)
		{
			BM_Opt_ClearCmdBinds(cmd, bmap);
			g_bind_listen_idx = -1;
			if (bmap == 1)
				BM_Opt_SaveVehConfig();
			else
				BM_Opt_BumpVehRev();
			BM_PlaySound("sound/misc/menu3.wav");
			return;
		}
		kname = keynumtostring(key);
		if (kname != "")
		{
			BM_Opt_ClearCmdBinds(cmd, bmap);
			setkeybind(key, cmd, bmap);
			g_bind_listen_idx = -1;
			if (bmap == 1)
				BM_Opt_SaveVehConfig();
			else
				BM_Opt_BumpVehRev();
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
		g_active_slider = 0;
		g_opt_scroll = 0;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	else if (key == K_MWHEELUP || key == K_PGUP || key == K_UPARROW)
	{
		g_opt_scroll = max(0, g_opt_scroll - 1);
	}
	else if (key == K_MWHEELDOWN || key == K_PGDN || key == K_DOWNARROW)
	{
		g_opt_scroll = bound(0, g_opt_scroll + 1, BM_Opt_CurrentMaxScroll());
	}
};
