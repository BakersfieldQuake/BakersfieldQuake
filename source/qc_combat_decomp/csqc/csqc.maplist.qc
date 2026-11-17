//Decompiled code. Please respect the original copyright.

void() create_maplist =
{
	local float j;

	mapindex = search_begin(/*11180i*/"maps/*.bsp", TRUE, TRUE);
	mapcount = search_getsize(mapindex);
	posveclist = '-60 292 0';
	j = 0;
	while ((j < mapcount))
	{
		mapstring[j] = strzone(search_getfilename(mapindex, j));
		maplist[j] = strzone(substring(mapstring[j], 5, (strlen(mapstring[j]) - FILE_EXT)));
		j = j + 1;
	}
	search_end(mapindex);
};

void() draw_cursor =
{
	drawSelectArrow('-80 282 0', 1);
};

void() loadMap =
{
	local float IS_MODEL;

	IS_MODEL = strstrofs(maplist[arrowPos], /*11191i*/"b_", 0);
	if ((IS_MODEL == -1))
	{
		if (((cvar("deathmatch") == 0) && (cvar("coop") == 0)))
		{
			updateServerMaxPlayers();
			localcmd(strcat("map ", maplist[arrowPos], "\n"));
		}
		else
		{
			if ((mp_change != maxplayers))
			{
				updateServerMaxPlayers();
				localcmd(strcat("map ", maplist[arrowPos], "\n"));
			}
			else
			{
				updateServerMaxPlayers();
				localcmd(strcat("changelevel ", maplist[arrowPos], "\n"));
			}
		}
	}
};

void() SkillSelect =
{
	if ((cvar("skill") == 0))
	{
		cvar_set("skill", "1");
	}
	else
	{
		if ((cvar("skill") == 1))
		{
			cvar_set("skill", "2");
		}
		else
		{
			if ((cvar("skill") == 2))
			{
				cvar_set("skill", "3");
			}
			else
			{
				if ((cvar("skill") == 3))
				{
					cvar_set("skill", "0");
				}
			}
		}
	}
};

void() ShowMapList =
{
	local vector posvecoff;
	local float j;
	local float IS_MODEL;

	if ((inMenu == 4))
	{
		if (!maplist_loaded)
		{
			maplist_loaded = 1;
			create_maplist();
		}
		SkillCheck();
		POINTS_TO_BSP = strstrofs(maplist[arrowPos], /*11191i*/"b_", 0);
		Sbar_DrawPic('-115 330 0', "gfx/cust_maps", 1, 1);
		posvecoff = VEC_0;
		draw_cursor();
		Sbar_DrawString('80 42 0', "Skill:", 1, '8 8 0', VEC_1);
		if ((whatskill == 3))
		{
			Sbar_DrawString('140 42 0', skill[whatskill], 1, '8 8 0', '1 0 0');
		}
		else
		{
			if ((whatskill == 0))
			{
				Sbar_DrawString('140 42 0', skill[whatskill], 1, '8 8 0', '0 1 0.5');
			}
			else
			{
				Sbar_DrawString('140 42 0', skill[whatskill], 1, '8 8 0', '1 0.6 0');
			}
		}
		Sbar_DrawString('80 32 0', "(END to change)", 1, '8 8 0', '0.7 0.7 0.7');
		j = 0;
		while ((j < mapcount))
		{
			IS_MODEL = strstrofs(maplist[j], /*11191i*/"b_", 0);
			posvecoff = posvecoff + '0 -10 0';
			if ((((posveclist_y + posvecoff_y) <= 292) && ((posveclist_y + posvecoff_y) >= 70)))
			{
				if ((IS_MODEL == -1))
				{
					Sbar_DrawString((posveclist + posvecoff), maplist[j], 1, '8 8 0', '1 0.6 0.3');
				}
				else
				{
					Sbar_DrawString((posveclist + posvecoff), maplist[j], 1, '8 8 0', '0.6 0.6 0.6');
				}
			}
			j = j + 1;
		}
		Sbar_DrawString('-80 42 0', strcat(ftos((mapcount - 19)), " maps found"), 1, '8 8 0', '1 0.3 0.1');
		if (!POINTS_TO_BSP)
		{
			Sbar_DrawString('70 22 0', "!BSP MODEL, NOT A MAP!", 1, '8 8 0', '1 0 0');
		}
		Sbar_DrawString('80 62 0', "Start Server/Botmatch", 1, '8 8 0', '0 1 0');
		Sbar_DrawString('80 52 0', "(HOME)", 1, '8 8 0', '0 1 0.5');
		Sbar_DrawString('-150 12 0', "Up and Down arrow to scroll, left and right to skip", 1, '8 8 0', '0.7 0.7 0.7');
	}
};




