//Decompiled code. Please respect the original copyright.

float() isLocal =
{

	if ((((cvar("deathmatch") == 0) && (cvar("coop") == 0)) && !ctf))
	{
		return (TRUE);
	}
	else
	{
		return (0);
	}
};

float() hasRunes =
{
	if (((((items2 & RUNE_EP1) || (items2 & RUNE_EP2)) || (items2 & RUNE_EP3)) || (items2 & RUNE_EP4)))
	{
		return (TRUE);
	}
	else
	{
		return (0);
	}
};

float() autobalance =
{
	if (!cvar("ctf_autobalance"))
	{
		return (0);
	}
	else
	{
		return (TRUE);
	}
};

void() check_gamemode =
{

	if ((((cvar("deathmatch") == 1) || (cvar("deathmatch") == 2)) && (cvar("ctf") == 0)))
	{
		gt_cycle = 1;
	}
	else
	{
		if ((cvar("ctf") == 1))
		{
			gt_cycle = 1;
		}
		else
		{
			if ((cvar("coop") == 1))
			{
				gt_cycle = 3;
			}
			else
			{
				gt_cycle = 0;
			}
		}
	}
	if ((gt_cycle == 0))
	{
		mp_change = 1;
	}
};

void() init_servercmds =
{
	if ((cvar("deathmatch") == 2))
	{
		weaponstay = 1;
	}
};

void() updateServerMaxPlayers =
{
	if (weaponstay)
	{
		localcmd(strcat("maxplayers ", ftos(maxplayers), ";deathmatch 2\n"));
	}
	else
	{
		localcmd(strcat("maxplayers ", ftos(maxplayers), "\n"));
	}
};

void() setDefaults =
{
	cvar_set("coop", "0");
	cvar_set("ctf", "0");
	cvar_set("deathmatch", "0");
	ammocap = "Normal";
};

void() setSP =
{
	setDefaults();
	mp_change = 1;
	maxplayers = 1;
};

void() setCoop =
{
	if ((cvar("coop") == 0))
	{
		cvar_set("coop", "1");
		maxplayers = mp_temp;
		if ((maxplayers == 1))
		{
			maxplayers = 16;
		}
	}
	else
	{
		cvar_set("coop", "0");
	}
};

void() setCTF =
{
	if ((cvar("ctf") == 0))
	{
		cvar_set("ctf", "1");
		cvar_set("coop", "0");
		maxplayers = mp_temp;
		if ((maxplayers == 1))
		{
			maxplayers = 16;
		}
	}
	else
	{
		cvar_set("ctf", "0");
	}
};

void() setDeathmatch =
{
	if ((cvar("deathmatch") == 0))
	{
		cvar_set("deathmatch", "1");
		cvar_set("coop", "0");
		maxplayers = mp_temp;
		if ((maxplayers == 1))
		{
			maxplayers = 16;
		}
	}
};

float() isDeathmatch =
{
	if ((cvar("deathmatch") == 0))
	{
		return (0);
	}
	else
	{
		return (TRUE);
	}
};

float() isCTF =
{
	if ((cvar("ctf") == 0))
	{
		return (0);
	}
	else
	{
		return (TRUE);
	}
};

float() isCoop =
{
	if ((cvar("coop") == 0))
	{
		return (0);
	}
	else
	{
		return (TRUE);
	}
};

float() isSingle =
{

	if (((!isCoop() && !isCTF()) && !isDeathmatch()))
	{
		return (TRUE);
	}
	else
	{
		return (0);
	}
};

float() checkHook =
{
	if ((cvar("mp_grapple") == 1))
	{
		return (SWING);
	}
	else
	{
		if ((cvar("mp_grapple") == 2))
		{
			return (REEL);
		}
		else
		{
			return (0);
		}
	}
};

void() setHook =
{
	if ((checkHook() == FALSE))
	{
		cvar_set("mp_grapple", "1");
	}
	else
	{
		if ((checkHook() == SWING))
		{
			cvar_set("mp_grapple", "2");
		}
		else
		{
			cvar_set("mp_grapple", "0");
		}
	}
};

void() setTeamplay =
{
	if (isCTF())
	{
		if ((cvar("teamplay") == 1))
		{
			cvar_set("teamplay", "2");
		}
		else
		{
			if ((cvar("teamplay") == 2))
			{
				cvar_set("teamplay", "1");
			}
		}
	}
	else
	{
		if ((cvar("teamplay") == 0))
		{
			cvar_set("teamplay", "1");
		}
		else
		{
			if ((cvar("teamplay") == 1))
			{
				cvar_set("teamplay", "2");
			}
			else
			{
				cvar_set("teamplay", "0");
			}
		}
	}
};

void() setAmmoCap =
{
	if ((ammocap == "Normal"))
	{
		ammocap = "Double";
		localcmd("exec ammobox.cfg\n");
	}
	else
	{
		if ((ammocap == "Double"))
		{
			ammocap = "Normal";
			localcmd("exec ammobox_default.cfg\n");
		}
	}
};

void() spawnBots =
{

	if ((!isSingle() && !isCoop()))
	{
		botcount = cvar("bot_count");
		if ((botcount == minplayers))
			return;
		if ((botcount != 0))
		{
			if (cvar("teamplay"))
			{
				while ((minplayers < botcount))
				{
					if (!MP_FLAG)
					{
						localcmd(strcat("addbotenemy\n", server_wait));
						MP_FLAG = 1;
					}
					else
					{
						localcmd(strcat("addbot\n", server_wait));
						MP_FLAG = 0;
					}
					minplayers = minplayers + 1;
				}
			}
			else
			{
				while ((minplayers < botcount))
				{
					localcmd(strcat("addbotenemy\n", server_wait));
					minplayers = minplayers + 1;
				}
			}
		}
		else
		{
			while ((minplayers > botcount))
			{
				localcmd(strcat("removebot\n", server_wait));
				minplayers = minplayers + -1;
			}
		}
	}
};

void() setBots =
{
	if ((botcount < maxplayers))
	{
		botcount = botcount + 1;
		cvar_set("bot_count", ftos(botcount));
	}
	else
	{
		botcount = 0;
		cvar_set("bot_count", ftos(botcount));
	}
};

void() SkillCheck =
{

	if (((cvar("skill") >= 0) && (cvar("skill") <= 3)))
	{
		whatskill = cvar("skill");
	}
};
float indexs___;
vector value___;
float __indexg;

