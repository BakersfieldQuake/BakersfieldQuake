//Decompiled code. Please respect the original copyright.

void() getItems =
{
	items = getstati(STAT_ITEMS, 0, 23);
	items2 = getstati(STAT_ITEMS, 23, 9);
	cl_items = getstati(STAT_ITEMS);
};

vector(vector v) sbar_align =
{
	v_x = v_x + (vid_conwidth / 2);
	v_y = vid_conheight - v_y;
	return (v);
};

void(vector pos, string pic, float alph, float scale) Sbar_DrawPic =
{
	local vector siz;

	siz = drawgetimagesize(pic);
	siz = siz * scale;
	siz_z = 0;		// DarkPlaces warns "VM_drawpic: z value from size discarded" every frame if this is not 0
	pos = sbar_align(pos);
	drawpic(pos, pic, siz, VEC_1, alph, DRAWFLAG_NORMAL);
};

void(vector pos, float char, float alph) Sbar_DrawCharacter =
{
	local float old_font;

	pos = sbar_align(pos);
	old_font = drawfont;
	drawfont = 0;
	drawcharacter(pos, char, '8 8 0', VEC_1, alph, DRAWFLAG_NORMAL);
	drawfont = old_font;
};

float bm_ui_font_cvar_val;
float bm_ui_font_cvar_t;

float() BM_GetUIFont =
{
	if (time >= bm_ui_font_cvar_t || bm_ui_font_cvar_t <= 0)
	{
		bm_ui_font_cvar_t = time + 0.25;
		bm_ui_font_cvar_val = cvar("bm_ui_font");
	}
	if (bm_ui_font_cvar_val == 0)
		return 0;
	if (!bm_ui_font_checked)
	{
		bm_ui_font_checked = TRUE;
		bm_ui_font_idx = loadfont("user1", "engine/fonts/Roboto-Medium.ttf", "8 12 16 24 32");
		if (bm_ui_font_idx <= 0)
			bm_ui_font_idx = findfont("Roboto");
		if (bm_ui_font_idx < 0)
			bm_ui_font_idx = 0;
	}
	return bm_ui_font_idx;
};

float(float sz) BM_UIScale =
{
	if (bm_ui_skip_scale || BM_GetUIFont() <= 0)
		return sz;
	if (sz <= 5.5)
		return sz * 1.36;
	if (sz <= 8.5)
		return sz * 1.28;
	if (sz <= 12)
		return sz * 1.18;
	return sz * 1.10;
};

vector(vector sc) BM_UIScaleVec =
{
	local vector out;

	out_x = BM_UIScale(sc_x);
	out_y = BM_UIScale(sc_y);
	out_z = 0;
	return out;
};

float(string s, float useColors, vector sc) BM_UIStringWidth =
{
	return stringwidth(s, useColors, BM_UIScaleVec(sc));
};

void(vector pos, string str, float alph, vector med, vector color) Sbar_DrawString =
{
	local vector sc;

	sc = BM_UIScaleVec(med);
	pos = sbar_align(pos);
	pos_y = pos_y - (sc_y - med_y) * 0.45;
	if (BM_GetUIFont() > 0)
		drawstring(pos + '0.7 0.7 0', str, sc, '0 0 0', alph * 0.80, DRAWFLAG_NORMAL);
	drawstring(pos, str, sc, color, alph, DRAWFLAG_NORMAL);
};

void(vector pos, float num, float digits, float color, float alpha) Sbar_DrawNum =
{
	local string pic;
	local string s;
	local string digit;
	local float i;
	local float len;
	local float cnt;
	local vector v;

	s = ftos(num);
	len = strlen(s);
	cnt = digits;
	if ((len < digits))
	{
		cnt = len;
	}
	i = 1;
	while ((i <= cnt))
	{
		digit = substring(s, (len - i), 1);
		if ((digit == "-"))
		{
			digit = "minus";
		}
		if (color)
		{
			pic = strcat("gfx/anum_", digit);
		}
		else
		{
			pic = strcat("gfx/num_", digit);
		}
		v = pos + ('24 0 0' * (digits - i));
		Sbar_DrawPic(v, pic, alpha, 1);
		i = i + 1;
	}
};

void(vector pos, string pic, float itemnum, float item2num, float transparency, float scale) DrawInventory =
{
	local vector v;

	v = pos;
	if ((((items & itemnum) || (cl_items & itemnum)) || (items2 & item2num)))
	{
		Sbar_DrawPic(v, pic, transparency, scale);
	}
};

void(vector valor, string pic1, string pic2, float itemnum, float blink) DrawInventoryWeapon =
{
	local vector v;
	local string pic;
	local float wb;

	v = valor;
	if ((blink > 0))
	{
		wb = time - blink;
		if (((wb >= 0.5) && (wb < 1)))
		{
			wb = wb - 0.5;
		}
		if ((wb < 0.1))
			pic = strcat("gfx/inva1_", substring(pic1, 8, (strlen(pic1) - 8)));
		else if ((wb < 0.2))
			pic = strcat("gfx/inva2_", substring(pic1, 8, (strlen(pic1) - 8)));
		else if ((wb < 0.3))
			pic = strcat("gfx/inva3_", substring(pic1, 8, (strlen(pic1) - 8)));
		else if ((wb < 0.4))
			pic = strcat("gfx/inva4_", substring(pic1, 8, (strlen(pic1) - 8)));
		else if ((wb < 0.5))
			pic = strcat("gfx/inva5_", substring(pic1, 8, (strlen(pic1) - 8)));
		else
			return;
		Sbar_DrawPic(v, pic, sbar_alpha, 1);
	}
	else
	{
		if (((items & itemnum) || (cl_items & itemnum)))
		{
			if ((currentweap == itemnum))
			{
				pic = pic2;
			}
			else
			{
				pic = pic1;
			}
			Sbar_DrawPic(v, pic, sbar_alpha, 1);
		}
	}
};

void() displayIntro =
{
	local vector optioncol;
	local vector mapcol;

	if ((!isLocal() || hasRunes()))
	{
		return;
	}
	if ((introtimer < 2))
	{
		introtimer = introtimer + 0.01;
	}
	else
	{
		introtimer = 0;
	}
	optioncol_x = 0;
	mapcol_x = 0;
};

void() setHUDparms =
{
	grenade_ammo = getstati(40);
	shell_ammo = getstati(STAT_SHELLS);
	nail_ammo = getstati(STAT_NAILS);
	rocket_ammo = getstati(STAT_ROCKETS);
	cell_ammo = getstati(STAT_CELLS);
	player_health = getstati(STAT_HEALTH);
	time_limit = getstati(STAT_TIMELIMIT);
	if (ctf)
	{
		frag_limit = cvar("ctf_capture_limit");
	}
	else
	{
		frag_limit = cvar("fraglimit");
	}
	life_count = getstati(45);
	BLUE_CAPS = getstati(49);
	RED_CAPS = getstati(50);
	ctf = getstati(51);
	invis_count = getstati(41);
	quad_count = getstati(42);
	bio_count = getstati(43);
	pent_count = getstati(44);
	slow_count = getstati(46);
	SNDSPD = getstati(47);
	currentweap = getstati(STAT_ACTIVEWEAPON);
};

void() fixIntermission =
{
	local float bm_i, sens, sway;

	bm_i = getstati(69);
	if ((bm_i > 0))
		return;
	sens = cvar("sensitivity");
	if (!intermission)
	{
		if (finale)
			finale = 0;
		if ((sens > 0) && !menu_was_open)
			mouse = sens;
		return;
	}
	finale = 2;
	viewpos = getentityvec(player_localentnum, E_ORIGINANDVECTORS);
	viewang = vectoangles2(v_forward, v_up);
	viewang_x = 0 - viewang_x;
	sway = sin((time * 0.5));
	viewang_x = viewang_x + (sway * 0.75);
	viewang_x = viewang_x + 1;
	setproperty(VF_ORIGIN, viewpos);
	setproperty(VF_ANGLES, viewang);
};

void() wepFlash =
{
	if (((items & IT_AXE) && (axe == 0)))
	{
		axe = time;
	}
	if (((items & IT_SHOTGUN) && (sg == 0)))
	{
		sg = time;
	}
	if (((items & IT_SUPER_SHOTGUN) && (ssg == 0)))
	{
		ssg = time;
	}
	if (((items & IT_NAILGUN) && (ng == 0)))
	{
		ng = time;
	}
	if (((items & IT_SUPER_NAILGUN) && (sng == 0)))
	{
		sng = time;
	}
	if (((items & IT_GRENADE_LAUNCHER) && (gl == 0)))
	{
		gl = time;
	}
	if (((items & IT_ROCKET_LAUNCHER) && (rl == 0)))
	{
		rl = time;
	}
	if (((items & IT_LIGHTNING) && (lg == 0)))
	{
		lg = time;
	}
	if (((axe > 0) && ((time - axe) >= 1)))
	{
		axe = -1;
	}
	if (((sg > 0) && ((time - sg) >= 1)))
	{
		sg = -1;
	}
	if (((ssg > 0) && ((time - ssg) >= 1)))
	{
		ssg = -1;
	}
	if (((ng > 0) && ((time - ng) >= 1)))
	{
		ng = -1;
	}
	if (((sng > 0) && ((time - sng) >= 1)))
	{
		sng = -1;
	}
	if (((gl > 0) && ((time - gl) >= 1)))
	{
		gl = -1;
	}
	if (((rl > 0) && ((time - rl) >= 1)))
	{
		rl = -1;
	}
	if (((lg > 0) && ((time - lg) >= 1)))
	{
		lg = -1;
	}
};

void() fade_camera =
{
	if ((((((world.message == "the Slipgate Complex") || (world.message == "Introduction")) || (world.message == "Termination Central")) || (world.message == "the Sewage System")) || (world.message == "the Installation")))
	{
		if ((cltime < 2))
		{
			drawfill('-70 -70 0', '2000 2000 0', VEC_0, 2, 0);
		}
		else
		{
			if ((cltime < 2.1))
			{
				drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.98, 0);
			}
			else
			{
				if ((time < 2.15))
				{
					drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.95, 0);
				}
				else
				{
					if ((time < 2.2))
					{
						drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.9, 0);
					}
					else
					{
						if ((time < 2.25))
						{
							drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.85, 0);
						}
						else
						{
							if ((time < 2.3))
							{
								drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.8, 0);
							}
							else
							{
								if ((time < 2.35))
								{
									drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.75, 0);
								}
								else
								{
									if ((time < 2.4))
									{
										drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.7, 0);
									}
									else
									{
										if ((time < 2.45))
										{
											drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.65, 0);
										}
										else
										{
											if ((time < 2.5))
											{
												drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.6, 0);
											}
											else
											{
												if ((time < 2.55))
												{
													drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.55, 0);
												}
												else
												{
													if ((time < 2.6))
													{
														drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.5, 0);
													}
													else
													{
														if ((time < 2.65))
														{
															drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.45, 0);
														}
														else
														{
															if ((time < 2.7))
															{
																drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.4, 0);
															}
															else
															{
																if ((time < 2.75))
																{
																	drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.35, 0);
																}
																else
																{
																	if ((time < 2.8))
																	{
																		drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.3, 0);
																	}
																	else
																	{
																		if ((time < 2.85))
																		{
																			drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.25, 0);
																		}
																		else
																		{
																			if ((time < 2.9))
																			{
																				drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.2, 0);
																			}
																			else
																			{
																				if ((time < 2.95))
																				{
																					drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.18, 0);
																				}
																				else
																				{
																					if ((time < 3))
																					{
																						drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.17, 0);
																					}
																					else
																					{
																						if ((time < 3.05))
																						{
																							drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.15, 0);
																						}
																						else
																						{
																							if ((time < 3.1))
																							{
																								drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.13, 0);
																							}
																							else
																							{
																								if ((time < 3.15))
																								{
																									drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.1, 0);
																								}
																								else
																								{
																									if ((time < 3.2))
																									{
																										drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.09, 0);
																									}
																									else
																									{
																										if ((time < 3.25))
																										{
																											drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.07, 0);
																										}
																										else
																										{
																											if ((time < 3.3))
																											{
																												drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.05, 0);
																											}
																											else
																											{
																												if ((time < 3.35))
																												{
																													drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.03, 0);
																												}
																												else
																												{
																													if ((time < 3.4))
																													{
																														drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.01, 0);
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
};

void(vector color) DrawLevelName =
{
	local float w, h, l, st, warm, sz, wd, maxw, a, y;
	local vector sv, pos;

	st = cvar("hud_showtitle");
	if ((time < 0.4) || (time >= 3.6) || !st)
		return;
	l = strlen(world.message);
	if (l <= 0)
		return;

	w = cvar("vid_conwidth");
	h = cvar("vid_conheight");
	sz = floor((h * 0.0155) + 0.5);
	if (sz < 5)
		sz = 5;
	if (sz > 8)
		sz = 8;

	sz = BM_UIScale(sz);
	sv = sz * '1 1 0';
	wd = stringwidth(world.message, FALSE, sv);
	maxw = w * 0.84;
	if ((wd > maxw) && (wd > 0))
	{
		sz = sz * (maxw / wd);
		if (sz < 4)
			sz = 4;
		sv = sz * '1 1 0';
		wd = stringwidth(world.message, FALSE, sv);
	}

	if (time < 0.8)
		a = ((time - 0.4) / 0.4) * 0.75;
	else if (time > 2.9)
		a = ((3.6 - time) / 0.7) * 0.75;
	else
		a = 0.75;

	warm = getstati(59);
	y = 12;
	if (warm)
		y = 22;
	pos = ((w - wd) * 0.5) * '1 0 0' + y * '0 1 0';
	drawstring(pos + '0.7 0.7 0', world.message, sv, '0 0 0', a * 0.85, DRAWFLAG_NORMAL);
	drawstring(pos, world.message, sv, '0.94 0.82 0.52', a, DRAWFLAG_NORMAL);
};

void() DrawScoreboard =
{
	if ((!ctf && (((deathmatch && showscores) || (deathmatch && (player_health < 1))) || (deathmatch && intermission))))
	{
		Sbar_DrawPic('100 252 0', "textures/HUD/Fraglimit_banner.png", sbar_alpha, 1);
		Sbar_DrawNum('120 220 0', frag_limit, 4, 0, 1);
	}
	else
	{
		if ((((ctf && showscores) || (ctf && (player_health < 1))) || (ctf && intermission)))
		{
			Sbar_DrawPic('90 252 0', "textures/HUD/caplimit_banner.png", sbar_alpha, 0.8);
			Sbar_DrawPic('110 163 0', "textures/HUD/HUD_ctf_blue.png", sbar_alpha, 0.5);
			Sbar_DrawNum('170 163 0', BLUE_CAPS, 2, 1, sbar_alpha);
			Sbar_DrawPic('110 113 0', "textures/HUD/HUD_ctf_red.png", sbar_alpha, 0.5);
			Sbar_DrawNum('170 113 0', RED_CAPS, 2, 1, sbar_alpha);
			Sbar_DrawNum('120 220 0', frag_limit, 4, 0, 1);
		}
	}
};

void() DrawHUD =
{

	setHUDparms();
	if ((player_health < 1))
	{
		return;
	}
	if (showscores)
	{
		return;
	}
	if (coop)
	{
		if ((life_count > 0))
		{
			Sbar_DrawPic('-34 350 0', "textures/HUD/HUD_lives.png", sbar_alpha, 0.95);
			if ((life_count >= 100))
			{
				Sbar_DrawNum('-13 350 0', life_count, 3, 1, sbar_alpha);
			}
			else
			{
				if ((life_count > 10))
				{
					Sbar_DrawNum('-27 350 0', life_count, 3, 1, sbar_alpha);
				}
				else
				{
					Sbar_DrawNum('-33 350 0', life_count, 3, 1, sbar_alpha);
				}
			}
		}
	}
	if (ctf)
	{
		ctfbar_offset_x = 0;
		Sbar_DrawPic(('0 353 0' + ctfbar_offset), "textures/HUD/HUD_ctf_blue.png", sbar_alpha, 0.5);
		Sbar_DrawNum(('22 351 0' + ctfbar_offset), BLUE_CAPS, 2, 1, sbar_alpha);
		Sbar_DrawPic(('-32 353 0' + ctfbar_offset), "textures/HUD/HUD_ctf_red.png", sbar_alpha, 0.5);
		Sbar_DrawNum(('-91 351 0' + ctfbar_offset), RED_CAPS, 2, 1, sbar_alpha);
	}
	wepFlash();
	getItems();
	if ((showHUD == 1))
	{
		if (ctf)
		{
			DrawInventory(('270 68 0' + wepbar_offset), "gfx/bluflag", IT_KEY1, 0, sbar_alpha, 1.3);
			DrawInventory(('270 68 0' + wepbar_offset), "gfx/redflag", IT_KEY2, 0, sbar_alpha, 1.3);
		}
		else
		{
			DrawInventory(('270 68 0' + wepbar_offset), "gfx/sb_key1", IT_KEY1, 0, sbar_alpha, 1.2);
			DrawInventory(('290 68 0' + wepbar_offset), "gfx/sb_key2", IT_KEY2, 0, sbar_alpha, 1.2);
		}
		DrawInventory(('270 98 0' + wepbar_offset), "gfx/sb_invis", IT_INVISIBILITY, 0, sbar_alpha, 1.2);
		if ((items & IT_INVISIBILITY))
		{
			if ((invis_count > 8))
			{
				Sbar_DrawString(('263 89 0' + wepbar_offset), ftos(invis_count), 1, '8 8 0', '1 0.8 0.1');
			}
			else
			{
				if ((invis_count > 0))
				{
					Sbar_DrawString(('263 89 0' + wepbar_offset), ftos(invis_count), 1, '8 8 0', '1 0.1 0');
				}
			}
		}
		DrawInventory(('270 128 0' + wepbar_offset), "gfx/sb_invuln", IT_INVULNERABILITY, 0, sbar_alpha, 1.2);
		if ((items & IT_INVULNERABILITY))
		{
			if ((pent_count > 8))
			{
				Sbar_DrawString(('263 119 0' + wepbar_offset), ftos(pent_count), 1, '8 8 0', '1 0.8 0.1');
			}
			else
			{
				if ((pent_count > 0))
				{
					Sbar_DrawString(('263 119 0' + wepbar_offset), ftos(pent_count), 1, '8 8 0', '1 0.1 0');
				}
			}
		}
		DrawInventory(('270 158 0' + wepbar_offset), "gfx/sb_suit", IT_SUIT, 0, sbar_alpha, 1.2);
		if ((items & IT_SUIT))
		{
			if ((bio_count > 8))
			{
				Sbar_DrawString(('263 149 0' + wepbar_offset), ftos(bio_count), 1, '8 8 0', '1 0.8 0.1');
			}
			else
			{
				if ((bio_count > 0))
				{
					Sbar_DrawString(('263 149 0' + wepbar_offset), ftos(bio_count), 1, '8 8 0', '1 0.1 0');
				}
			}
		}
		DrawInventory(('270 188 0' + wepbar_offset), "gfx/sb_quad", IT_QUAD, 0, sbar_alpha, 1.2);
		if ((items & IT_QUAD))
		{
			if ((quad_count > 8))
			{
				Sbar_DrawString(('263 179 0' + wepbar_offset), ftos(quad_count), 1, '8 8 0', '1 0.8 0.1');
			}
			else
			{
				if ((quad_count > 0))
				{
					Sbar_DrawString(('263 179 0' + wepbar_offset), ftos(quad_count), 1, '8 8 0', '1 0.1 0');
				}
			}
		}
		if ((slow_count > 0))
		{
			Sbar_DrawPic(('-283 179 0' - wepbar_offset), "gfx/tmrune", 1, 1);
			Sbar_DrawString(('-281 170 0' - wepbar_offset), ftos(slow_count), 1, '8 8 0', '1 0.8 0.1');
		}
		DrawInventory(('270 40 0' + wepbar_offset), "gfx/sb_sigil1", 0, RUNE_EP1, sbar_alpha, 1.3);
		DrawInventory(('280 40 0' + wepbar_offset), "gfx/sb_sigil2", 0, RUNE_EP2, sbar_alpha, 1.3);
		DrawInventory(('290 40 0' + wepbar_offset), "gfx/sb_sigil3", 0, RUNE_EP3, sbar_alpha, 1.3);
		DrawInventory(('300 40 0' + wepbar_offset), "gfx/sb_sigil4", 0, RUNE_EP4, sbar_alpha, 1.3);
		DrawInventoryWeapon(('280 231 0' + wepbar_offset), "gfx/inv_shotgun", "gfx/inv2_shotgun", IT_SHOTGUN, sg);
		DrawInventoryWeapon(('280 248 0' + wepbar_offset), "gfx/inv_sshotgun", "gfx/inv2_sshotgun", IT_SUPER_SHOTGUN, ssg);
		DrawInventoryWeapon(('280 265 0' + wepbar_offset), "gfx/inv_nailgun", "gfx/inv2_nailgun", IT_NAILGUN, ng);
		DrawInventoryWeapon(('280 282 0' + wepbar_offset), "gfx/inv_snailgun", "gfx/inv2_snailgun", IT_SUPER_NAILGUN, sng);
		DrawInventoryWeapon(('280 299 0' + wepbar_offset), "gfx/inv_rlaunch", "gfx/inv2_rlaunch", IT_GRENADE_LAUNCHER, gl);
		DrawInventoryWeapon(('280 316 0' + wepbar_offset), "gfx/inv_srlaunch", "gfx/inv2_srlaunch", IT_ROCKET_LAUNCHER, rl);
		DrawInventoryWeapon(('260 333 0' + wepbar_offset), "gfx/inv_lightng", "gfx/inv2_lightng", IT_LIGHTNING, lg);
		DrawInventoryWeapon(('260 350 0' + wepbar_offset), "textures/HUD/HUD_Laser.png", "textures/HUD/HUD_Laser_select", IT_LASER_CANNON, -1);
	}
	if ((((showHUD > 0) && (cvar("hud_colored_ammo") == 1)) || ((showHUD > 1) && (cvar("hud_colored_ammo") == 0))))
	{
		Sbar_DrawPic('-119 48 0', "textures/HUD/HUD_shells.png", sbar_alpha, 0.4);
		Sbar_DrawPic('-72 48 0', "textures/HUD/HUD_nails.png", sbar_alpha, 0.4);
		Sbar_DrawPic('-22 48 0', "textures/HUD/HUD_rockets.png", sbar_alpha, 0.4);
		Sbar_DrawPic('23 48 0', "textures/HUD/HUD_cells.png", sbar_alpha, 0.4);
		if ((showHUD == 1))
		{
			if ((shell_ammo < 10))
			{
				Sbar_DrawString('-135 48 0', ftos(shell_ammo), 1, '8 8 0', '1 0.1 0');
			}
			else
			{
				if ((shell_ammo < 15))
				{
					Sbar_DrawString('-139 48 0', ftos(shell_ammo), 1, '8 8 0', '1 0.1 0');
				}
				else
				{
					if ((shell_ammo < 50))
					{
						Sbar_DrawString('-139 48 0', ftos(shell_ammo), 1, '8 8 0', '1 0.5 0.2');
					}
					else
					{
						if ((shell_ammo >= 100))
						{
							Sbar_DrawString('-147 48 0', ftos(shell_ammo), 1, '8 8 0', '0.7 0.8 0.2');
						}
						else
						{
							Sbar_DrawString('-139 48 0', ftos(shell_ammo), 1, '8 8 0', '0.7 0.8 0.2');
						}
					}
				}
			}
			if ((nail_ammo < 25))
			{
				Sbar_DrawString('-91 48 0', ftos(nail_ammo), 1, '8 8 0', '1 0.1 0');
			}
			else
			{
				if ((nail_ammo < 100))
				{
					Sbar_DrawString('-91 48 0', ftos(nail_ammo), 1, '8 8 0', '1 0.5 0.2');
				}
				else
				{
					Sbar_DrawString('-99 48 0', ftos(nail_ammo), 1, '8 8 0', '0.7 0.8 0.2');
				}
			}
			if ((rocket_ammo < 15))
			{
				Sbar_DrawString('-42 48 0', ftos(rocket_ammo), 1, '8 8 0', '1 0.1 0');
			}
			else
			{
				if ((rocket_ammo < 30))
				{
					Sbar_DrawString('-42 48 0', ftos(rocket_ammo), 1, '8 8 0', '1 0.5 0.2');
				}
				else
				{
					if ((rocket_ammo >= 60))
					{
						Sbar_DrawString('-50 48 0', ftos(rocket_ammo), 1, '8 8 0', '0.7 0.8 0.2');
					}
					else
					{
						Sbar_DrawString('-42 48 0', ftos(rocket_ammo), 1, '8 8 0', '0.7 0.8 0.2');
					}
				}
			}
			if ((cell_ammo < 25))
			{
				Sbar_DrawString('3 48 0', ftos(cell_ammo), 1, '8 8 0', '1 0.1 0');
			}
			else
			{
				if ((cell_ammo < 50))
				{
					Sbar_DrawString('3 48 0', ftos(cell_ammo), 1, '8 8 0', '1 0.5 0.2');
				}
				else
				{
					if ((cell_ammo >= 100))
					{
						Sbar_DrawString('-5 48 0', ftos(cell_ammo), 1, '8 8 0', '0.7 0.8 0.2');
					}
					else
					{
						Sbar_DrawString('3 48 0', ftos(cell_ammo), 1, '8 8 0', '0.7 0.8 0.2');
					}
				}
			}
		}
	}
};

void() initConvars =
{
	local float vs;

	vid_conwidth = cvar("vid_conwidth");
	vid_conheight = cvar("vid_conheight");
	sbar_alpha = cvar("sbar_alpha_fg");
	csqc_slowmo = cvar("slowmo");
	vs = cvar("viewsize");
	if ((vs >= 120))
	{
		showHUD = 0;
	}
	else if ((vs >= 110))
	{
		showHUD = 1;
	}
	else
	{
		showHUD = 2;
	}
};
