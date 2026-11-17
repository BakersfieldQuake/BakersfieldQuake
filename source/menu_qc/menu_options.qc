// BakersfieldQuake MenuQC - Self-Contained Options, Video/Audio, Controls & Weapons

float OPT_TAB_VIDEO    = 0;
float OPT_TAB_CONTROLS = 1;
float OPT_TAB_WEAPONS  = 2;

float OPT_CTRL_COUNT   = 21;
float OPT_WEP_COUNT    = 19;

float g_opt_vid_dirty;
float g_opt_res_idx;

void() BM_Options_Open =
{
	local float w;

	g_page = PAGE_OPTIONS;
	g_focus_input = INPUT_NONE;
	g_bind_listen_idx = -1;
	g_opt_scroll = 0;

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
	return "Fun: Wheelman Cannon";
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
	return "impulse 66";
};

string(string cmd) BM_Opt_GetBoundKeys =
{
	local string raw, out, kname;
	local float n, i, kn;

	raw = findkeysforcommand(cmd, 0);
	if (raw == "")
		return "UNBOUND";
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
	if (raw == "")
		return;
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
};

void(float px, float py, float pw, float ph, float clicked) BM_Options_DrawVideo =
{
	local float ix, iw, y, st, hov;
	local float sens, mpitch, fv, gam, vol, bgm, pct, bg_on, fs_on, vs_on;
	local string s_val;

	ix = px + 16;
	iw = pw - 32;
	y = py + 62;

	// Fullscreen + Resolution
	fs_on = (stof(cvar_string("vid_fullscreen")) != 0);
	st = BM_DrawStepper(ix, y, g_opt_vid_dirty ? (iw - 96) : iw, 19, "FULLSCREEN", fs_on ? "On" : "Off", FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		cvar_set("vid_fullscreen", fs_on ? "0" : "1");
		g_opt_vid_dirty = TRUE;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	if (g_opt_vid_dirty)
	{
		hov = BM_DrawButton(ix + iw - 90, y, 90, 19, "APPLY VIDEO", FALSE, TRUE);
		if (clicked && hov)
		{
			g_click_consumed = TRUE;
			g_opt_vid_dirty = FALSE;
			localcmd("vid_restart\n");
			return;
		}
	}
	y = y + 22;

	st = BM_DrawStepper(ix, y, iw, 19, "RESOLUTION", BM_Opt_ResLabel(g_opt_res_idx), FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		g_opt_res_idx = bound(0, g_opt_res_idx + st, 4);
		BM_Opt_ApplyRes(g_opt_res_idx);
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 22;

	vs_on = (stof(cvar_string("vid_vsync")) != 0);
	st = BM_DrawStepper(ix, y, iw, 19, "VSYNC", vs_on ? "On" : "Off", FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		cvar_set("vid_vsync", vs_on ? "0" : "1");
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 22;

	gam = stof(cvar_string("v_gamma"));
	if (gam <= 0) gam = 1.0;
	st = BM_DrawStepper(ix, y, iw, 19, "BRIGHTNESS (GAMMA)", sprintf("%.2f", gam), FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		gam = bound(0.8, rint((gam + st * 0.05) * 20) * 0.05, 1.8);
		cvar_set("v_gamma", sprintf("%.2f", gam));
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 22;

	fv = stof(cvar_string("fov"));
	st = BM_DrawStepper(ix, y, iw, 19, "FIELD OF VIEW (FOV)", ftos(rint(fv)), FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		fv = bound(75, rint(fv + st * 5), 120);
		cvar_set("fov", ftos(fv));
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 22;

	sens = stof(cvar_string("sensitivity"));
	s_val = sprintf("%.1f", sens);
	st = BM_DrawStepper(ix, y, iw, 19, "MOUSE SENSITIVITY", s_val, FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		sens = bound(0.5, rint((sens + st * 0.5) * 2) * 0.5, 15.0);
		cvar_set("sensitivity", sprintf("%.1f", sens));
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 22;

	mpitch = stof(cvar_string("m_pitch"));
	st = BM_DrawStepper(ix, y, iw, 19, "INVERT MOUSE Y", (mpitch < 0) ? "On" : "Off", FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		if (mpitch == 0) mpitch = 0.022;
		cvar_set("m_pitch", ftos(0 - mpitch));
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 22;

	vol = stof(cvar_string("volume"));
	pct = rint(vol * 100);
	if (pct <= 0) pct = 0;
	st = BM_DrawStepper(ix, y, iw, 19, "MASTER VOLUME", strcat(ftos(pct), "%"), FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		vol = bound(0, rint((vol + st * 0.1) * 10) * 0.1, 1.0);
		if (vol < 0.05) vol = 0;
		cvar_set("volume", sprintf("%.1f", vol));
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 22;

	bgm = stof(cvar_string("bgmvolume"));
	pct = rint(bgm * 100);
	if (pct <= 0) pct = 0;
	st = BM_DrawStepper(ix, y, iw, 19, "MUSIC VOLUME", strcat(ftos(pct), "%"), FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		bgm = bound(0, rint((bgm + st * 0.1) * 10) * 0.1, 1.0);
		if (bgm < 0.05) bgm = 0;
		cvar_set("bgmvolume", sprintf("%.1f", bgm));
		BM_PlaySound("sound/misc/menu1.wav");
	}
	y = y + 22;

	bg_on = (stof(cvar_string("menu_background")) != 0);
	st = BM_DrawStepper(ix, y, iw, 19, "LEVELSHOTS BACKDROP", bg_on ? "On" : "Off", FALSE, clicked);
	if (st != 0)
	{
		g_click_consumed = TRUE;
		cvar_set("menu_background", bg_on ? "0" : "1");
		BM_PlaySound("sound/misc/menu1.wav");
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
	iy = py + 62;
	iw = pw - 36;
	ih = ph - 98;
	rh = 20;
	gap = 3;

	vis = max(1, floor((ih + gap) / (rh + gap)));
	max_scroll = max(0, total - vis);
	g_opt_scroll = bound(0, g_opt_scroll, max_scroll);

	drawsetcliparea(ix, iy, iw, ih);
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

			bg = listening ? '0.24 0.16 0.04' : (hov ? COL_GLASS_HOVER : COL_GLASS_CARD);
			brd = listening ? COL_ACCENT_HOT : (hov ? COL_ACCENT : COL_BORDER);
			BM_Fill(ix, ry, iw, rh, bg, 0.85);
			BM_Outline(ix, ry, iw, rh, brd, (listening || hov) ? 0.94 : 0.50, 1);

			BM_DrawTextClipped(ix + 8, ry + 6, iw - 150, lbl, 8, listening ? COL_ACCENT : COL_TEXT, 0.96, FALSE);

			if (listening)
			{
				kstr = "PRESS KEY (ESC/DEL)";
				kcol = COL_ACCENT_HOT;
			}
			else
			{
				kstr = BM_Opt_GetBoundKeys(cmd);
				kcol = (kstr == "UNBOUND") ? COL_BAD : COL_ACCENT;
			}
			BM_DrawTextRight(ix + iw - 8, ry + 6, kstr, 8, kcol, 0.96);

			if (clicked && hov)
			{
				g_click_consumed = TRUE;
				g_bind_listen_idx = i;
				BM_PlaySound("sound/misc/menu1.wav");
				drawresetcliparea();
				return;
			}
		}
	}
	drawresetcliparea();

	if (max_scroll > 0)
	{
		BM_Fill(ix + iw + 4, iy, 4, ih, '0.03 0.04 0.07', 0.85);
		sb_h = max(18, ih * (vis / total));
		sb_y = iy + (ih - sb_h) * (g_opt_scroll / max_scroll);
		BM_Fill(ix + iw + 4, sb_y, 4, sb_h, COL_ACCENT, 0.85);
	}

	// Bottom bar: instructions + Reset Defaults
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
	local float px, py, pw, ph, hov;

	px = floor(g_vw * 0.10);
	py = 16;
	pw = g_vw - px * 2;
	ph = g_vh - 32;

	BM_DrawGlassPanel(px, py, pw, ph, 0.90, COL_BORDER, 0.78, 2.5);

	BM_DrawText(px + 14, py + 11, "OPTIONS", 12, COL_ACCENT, 0.98);
	BM_DrawTextClipped(px + 106, py + 14, pw - 184, "Video, Audio, Controls & Weapon Binds", 8, COL_MUTED, 0.92, FALSE);

	hov = BM_DrawButton(px + pw - 66, py + 9, 54, 18, "BACK", FALSE, FALSE);
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		BM_PlaySound("sound/misc/menu3.wav");
		g_page = PAGE_MAIN;
		return;
	}

	// Tabs
	hov = BM_DrawTab(px + 14, py + 34, 114, 18, "VIDEO & AUDIO", (g_opt_tab == OPT_TAB_VIDEO));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		g_opt_scroll = 0;
		g_opt_tab = OPT_TAB_VIDEO;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	hov = BM_DrawTab(px + 132, py + 34, 98, 18, "CONTROLS", (g_opt_tab == OPT_TAB_CONTROLS));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		g_opt_scroll = 0;
		g_opt_tab = OPT_TAB_CONTROLS;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	hov = BM_DrawTab(px + 234, py + 34, 98, 18, "WEAPONS", (g_opt_tab == OPT_TAB_WEAPONS));
	if (clicked && hov)
	{
		g_click_consumed = TRUE;
		g_bind_listen_idx = -1;
		g_opt_scroll = 0;
		g_opt_tab = OPT_TAB_WEAPONS;
		BM_PlaySound("sound/misc/menu1.wav");
	}

	if (g_opt_tab == OPT_TAB_VIDEO)
		BM_Options_DrawVideo(px, py, pw, ph, clicked);
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
		if (key == K_DEL)
		{
			BM_Opt_ClearCmdBinds(cmd);
			g_bind_listen_idx = -1;
			BM_PlaySound("sound/misc/menu1.wav");
			return;
		}
		kname = keynumtostring(key);
		if (kname != "" && kname != "<UNKNOWN KEYNUM>")
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
		BM_PlaySound("sound/misc/menu3.wav");
		g_page = PAGE_MAIN;
	}
	else if (key == K_LEFTARROW)
	{
		g_opt_tab = modulo(g_opt_tab - 1 + 3, 3);
		g_opt_scroll = 0;
		BM_PlaySound("sound/misc/menu1.wav");
	}
	else if (key == K_RIGHTARROW)
	{
		g_opt_tab = modulo(g_opt_tab + 1, 3);
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
