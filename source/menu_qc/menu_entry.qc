// BakersfieldQuake MenuQC - Required Zircon entrypoints & draw/input dispatch

void() m_init =
{
	registercvar("menu_background", "1", 1);
	registercvar("menu_background_map", "soi6 soicowboy_bkk bakersfielddowntown little_st_james terminal21 goldenwest", 1);
	registercvar("bm_menu_bg", "0", 0);
	cvar_set("bm_menu_bg", "0");

	BM_InitServerListKeys();
	BM_InitLevelshots();
	BM_InitBackdrop();

	g_page = PAGE_MAIN;
	g_focus_input = INPUT_NONE;
	g_bind_listen_idx = -1;
	g_name_buf = BM_ZoneSet(g_name_buf, cvar_string("_cl_name"));
	g_ip_buf = BM_ZoneSet(g_ip_buf, BAKO_ONLINE_ADDR);

	// Auto-open Main Menu on cold startup (unless +map / +connect was passed on CLI)
	if (clientstate() <= CS_DISCONNECTED && !isserver())
		m_toggle(1);
};

void() m_shutdown =
{
	g_menu_open = FALSE;
	BM_ShutdownBackdrop();
	g_levelshot_known = BM_ZoneSet(g_levelshot_known, "");
	g_name_buf = BM_ZoneSet(g_name_buf, "");
	g_ip_buf = BM_ZoneSet(g_ip_buf, "");
	g_host_buf = BM_ZoneSet(g_host_buf, "");
};

void() m_newmap =
{
	// Entering a match/map closes the menu cleanly so gameplay has mouse focus
	if (g_menu_open)
		m_toggle(0);
};

float(float entry) m_gethostcachecategory =
{
	return 0;
};

void(float mode) m_toggle =
{
	if (mode == 1)
		g_menu_open = TRUE;
	else if (mode == 0)
		g_menu_open = FALSE;
	else
		g_menu_open = !g_menu_open;

	g_focus_input = INPUT_NONE;
	g_bind_listen_idx = -1;

	if (g_menu_open)
	{
		setkeydest(KEY_MENU);
		setmousetarget(MT_FREE);
	}
	else
	{
		setkeydest(KEY_GAME);
		setmousetarget(MT_FREE);
	}
};

void() m_draw =
{
	local vector mp;
	local float scrim_a;

	if (!g_menu_open)
		return;

	if (getmousetarget() != MT_FREE)
		setmousetarget(MT_FREE);

	g_vw = stof(cvar_string("vid_conwidth"));
	g_vh = stof(cvar_string("vid_conheight"));
	if (g_vw <= 0) g_vw = 640;
	if (g_vh <= 0) g_vh = 360;

	mp = getmousepos();
	g_mx = bound(0, mp_x, g_vw);
	g_my = bound(0, mp_y, g_vh);
	g_mouse_moved = (fabs(g_mx - g_last_mx) > 0.25 || fabs(g_my - g_last_my) > 0.25);
	g_last_mx = g_mx;
	g_last_my = g_my;

	// Lighter scrim on Main Menu so the panning levelshots backdrop shines through
	scrim_a = (g_page == PAGE_MAIN && clientstate() <= CS_DISCONNECTED) ? 0.34 : 0.62;
	BM_DrawBackdrop(scrim_a);

	if (g_page == PAGE_MAIN)
		BM_Main_Draw(FALSE);
	else if (g_page == PAGE_BROWSER)
		BM_Browser_Draw(FALSE);
	else if (g_page == PAGE_HOST)
		BM_Host_Draw(FALSE);
	else if (g_page == PAGE_OPTIONS)
		BM_Options_Draw(FALSE);

	BM_DrawMouseCursor();
};

void(float key, float ascii) m_keydown =
{
	local vector mp;

	if (!g_menu_open)
		return;

	g_vw = stof(cvar_string("vid_conwidth"));
	g_vh = stof(cvar_string("vid_conheight"));
	if (g_vw <= 0) g_vw = 640;
	if (g_vh <= 0) g_vh = 360;

	mp = getmousepos();
	g_mx = bound(0, mp_x, g_vw);
	g_my = bound(0, mp_y, g_vh);

	// While Options is listening for a keybind, capture any key/mouse click directly
	if (g_page == PAGE_OPTIONS && g_bind_listen_idx >= 0)
	{
		BM_Options_KeyDown(key, ascii);
		return;
	}

	if (key == K_MOUSE1)
	{
		g_click_consumed = FALSE;
		if (g_page == PAGE_MAIN)
			BM_Main_Draw(TRUE);
		else if (g_page == PAGE_BROWSER)
			BM_Browser_Draw(TRUE);
		else if (g_page == PAGE_HOST)
			BM_Host_Draw(TRUE);
		else if (g_page == PAGE_OPTIONS)
			BM_Options_Draw(TRUE);
		return;
	}

	// Never let text input trap console toggle
	if ((key == K_BACKQUOTE || key == K_TILDE) && g_focus_input != INPUT_NONE)
	{
		g_focus_input = INPUT_NONE;
		localcmd("toggleconsole\n");
		return;
	}

	if (g_page == PAGE_MAIN)
		BM_Main_KeyDown(key, ascii);
	else if (g_page == PAGE_BROWSER)
		BM_Browser_KeyDown(key, ascii);
	else if (g_page == PAGE_HOST)
		BM_Host_KeyDown(key, ascii);
	else if (g_page == PAGE_OPTIONS)
		BM_Options_KeyDown(key, ascii);
};

void(float key, float ascii) m_keyup =
{
};

void(float width, float height, float defwidth, float defheight) m_drawloading =
{
	local float lw, lh;

	lw = (defwidth > 0) ? defwidth : 640;
	lh = (defheight > 0) ? defheight : 360;
	BM_Fill(0, 0, lw, lh, COL_SCRIM, 0.88);
	BM_DrawGlassPanel(lw * 0.5 - 120, lh * 0.5 - 24, 240, 48, 0.90, COL_BORDER, 0.78, 2);
	BM_DrawTextCentered(lw * 0.5, lh * 0.5 - 8, "BAKOQUAKE", 11, COL_ACCENT, 0.98);
	BM_DrawTextCentered(lw * 0.5, lh * 0.5 + 8, "LOADING MAP...", 8, COL_MUTED, 0.92);
};
