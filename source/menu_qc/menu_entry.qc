// BakersfieldQuake MenuQC - Required Zircon entrypoints & draw/input dispatch

void() m_init =
{
	local float i;

	registercvar("bm_menu_bg", "0", 0);
	cvar_set("bm_menu_bg", "0");
	registercvar("bm_loading_preview", "0", 0);
	registercvar("bm_hud_style", "0", 1);
	registercvar("bm_ui_font", "1", 1);
	registercvar("bm_show_launcher", "0", 1);
	localcmd("loadfont menu engine/fonts/Roboto-Medium.ttf 8 12 16 24 32\n");
	registercvar("bm_bot_tags", "1", 1);
	registercvar("bm_player_tags", "1", 1);
	registercvar("lowspec", "0", 1);
	registercvar("bright_skins", "1", 1);
	registercvar("centered_weapons", "0", 1);
	registercvar("bm_veh_config", "0", 1);
	registercvar("bm_veh_init", "0", 1);
	registercvar("bm_veh_rev", "0", 0);
	localcmd("in_bindmap 0 0\n");
	for (i = 1; i < 768; i = i + 1)
	{
		if (getkeybind(i, 2) != "")
			setkeybind(i, "", 2);
	}

	precache_pic("gfx/conback.lmp");
	precache_pic("gfx/conback.png");
	precache_pic("gfx/qplaque.lmp");
	precache_pic("gfx/ttl_main.lmp");
	precache_pic("gfx/p_option.lmp");
	precache_pic("gfx/p_multi.lmp");
	precache_pic("gfx/loading.lmp");
	for (i = 1; i <= 6; i = i + 1)
		precache_pic(strcat("gfx/menudot", ftos(i), ".lmp"));
	precache_pic("gfx/menu_cast/greenguy.png");
	precache_pic("gfx/menu_cast/wheelman.png");
	precache_pic("gfx/menu_cast/bryan.png");
	precache_pic("gfx/menu_cast/david.png");
	precache_pic("gfx/menu_cast/daniel.png");
	precache_pic("gfx/menu_cast/beerguy.png");
	precache_pic("gfx/menu_cast/reeseice.png");
	precache_pic("gfx/menu_cast/rogerver.png");
	precache_pic("gfx/menu_cast/robeguy.png");
	precache_pic("gfx/menu_cast/jesskart.png");
	BM_Loading_Precache();
	if (cvar("scr_loadingscreen_maxfps") < 30)
		cvar_set("scr_loadingscreen_maxfps", "30");

	g_cast_left = 0; // Start left side with Green Man
	g_cast_right = 1 + modulo(floor(random() * (CAST_COUNT - 1)), CAST_COUNT - 1);
	g_cast_swap_start = gettime();
	g_cast_next_swap = g_cast_swap_start + 10.0;

	BM_InitServerListKeys();
	BM_InitLevelshots();

	g_page = PAGE_MAIN;
	g_focus_input = INPUT_NONE;
	g_bind_listen_idx = -1;
	g_active_slider = 0;
	g_mouse1_down = FALSE;
	g_name_buf = BM_ZoneSet(g_name_buf, cvar_string("_cl_name"));
	g_ip_buf = BM_ZoneSet(g_ip_buf, BAKO_ONLINE_ADDR);

	// Auto-open Main Menu on cold startup (unless +map / +connect was passed on CLI)
	if (clientstate() <= CS_DISCONNECTED && !isserver())
		m_toggle(1);
};

void() m_shutdown =
{
	g_menu_open = FALSE;
	g_mouse1_down = FALSE;
	g_active_slider = 0;
	g_levelshot_known = BM_ZoneSet(g_levelshot_known, "");
	g_name_buf = BM_ZoneSet(g_name_buf, "");
	g_ip_buf = BM_ZoneSet(g_ip_buf, "");
	g_host_buf = BM_ZoneSet(g_host_buf, "");
	g_opt_status = BM_ZoneSet(g_opt_status, "");
	BM_Loading_Shutdown();
	BM_Replays_Shutdown();
};

void() m_newmap =
{
	BM_Loading_Reset();
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

	if (g_focus_input == INPUT_PLAYERNAME)
		BM_CommitPlayerName(g_name_buf);
	g_focus_input = INPUT_NONE;
	g_bind_listen_idx = -1;
	g_active_slider = 0;
	g_mouse1_down = FALSE;

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

	if (cvar("bm_loading_preview") > 0)
	{
		BM_Loading_Draw(g_vw, g_vh);
		return;
	}

	if (g_page == PAGE_OPTIONS && g_opt_tab == 0)
		scrim_a = 0.0;
	else if (g_page == PAGE_MAIN && clientstate() < CS_CONNECTED)
		scrim_a = 0.0;
	else if (clientstate() >= CS_CONNECTED)
		scrim_a = 0.40;
	else
		scrim_a = 0.25;
	BM_DrawBackdrop(scrim_a);

	if (g_page == PAGE_MAIN)
		BM_Main_Draw(FALSE);
	else if (g_page == PAGE_BROWSER)
		BM_Browser_Draw(FALSE);
	else if (g_page == PAGE_HOST)
		BM_Host_Draw(FALSE);
	else if (g_page == PAGE_REPLAYS)
		BM_Replays_Draw(FALSE);
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

	if (g_page == PAGE_OPTIONS && g_bind_listen_idx >= 0)
	{
		BM_Options_KeyDown(key, ascii);
		return;
	}

	if (key == K_MOUSE1)
	{
		if (stof(cvar_string("bm_loading_preview")) != 0)
			return;
		g_mouse1_down = TRUE;
		g_click_consumed = FALSE;
		if (g_page == PAGE_MAIN)
			BM_Main_Draw(TRUE);
		else if (g_page == PAGE_BROWSER)
			BM_Browser_Draw(TRUE);
		else if (g_page == PAGE_HOST)
			BM_Host_Draw(TRUE);
		else if (g_page == PAGE_REPLAYS)
			BM_Replays_Draw(TRUE);
		else if (g_page == PAGE_OPTIONS)
			BM_Options_Draw(TRUE);
		return;
	}

	if ((key == K_BACKQUOTE || key == K_TILDE) && g_focus_input != INPUT_NONE)
	{
		if (g_focus_input == INPUT_PLAYERNAME)
			BM_CommitPlayerName(g_name_buf);
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
	else if (g_page == PAGE_REPLAYS)
		BM_Replays_KeyDown(key, ascii);
	else if (g_page == PAGE_OPTIONS)
		BM_Options_KeyDown(key, ascii);
};

void(float key, float ascii) m_keyup =
{
	if (key == K_MOUSE1)
	{
		g_mouse1_down = FALSE;
		g_active_slider = 0;
	}
};

float(vector screensize, float opaque) m_drawloading =
{
	local float lw, lh, minify;

	// Zircon binds the 2D ortho viewport to (scale_width_360, scale_height_360)
	// before SCR_DrawLoadingScreen(), then sets vid_conwidth/screensize to
	// (vid.width, vid.height) without calling R_SetViewport. Scale back via
	// vid_minification_factor so the loading screen fills 100% of the canvas.
	minify = stof(cvar_string("vid_minification_factor"));
	if (minify > 0 && minify <= 1.0 && screensize_x > 0 && screensize_y > 0)
	{
		lw = floor(screensize_x * minify);
		lh = floor(screensize_y * minify);
	}
	else
	{
		lw = (g_vw > 0) ? g_vw : ((screensize_x > 0) ? screensize_x : stof(cvar_string("vid_conwidth")));
		lh = (g_vh > 0) ? g_vh : ((screensize_y > 0) ? screensize_y : stof(cvar_string("vid_conheight")));
	}
	if (lw <= 0) lw = 640;
	if (lh <= 0) lh = 360;
	BM_Loading_Draw(lw, lh);
	return 1;
};
