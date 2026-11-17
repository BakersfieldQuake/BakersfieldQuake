//Decompiled code. Please respect the original copyright.

void(vector pos, float alpha) drawSelectArrow =
{
	blinktimer = blinktimer + 1;
	if ((blinktimer > 35))
	{
		Sbar_DrawCharacter(pos, 13, alpha);
	}
	if ((blinktimer > 65))
	{
		blinktimer = 0;
	}
};

void() menuItemSelector =
{
	local vector pos[16];
	local vector posoffset;
	local float i;
	local float j;
	local float j;
	local float j;
	local float j;

	posoffset = VEC_0;
	i = 0;
	while ((i <= 15))
	{
		pos[((i * 3) / 3)] = '-75 262 0';
		i = i + 1;
	}
	if ((inMenu == 1))
	{
		j = 0;
		while ((j <= 15))
		{
			if ((j >= 1))
			{
				posoffset = posoffset + '0 10 0';
			}
			if ((j == 4))
			{
				posoffset = posoffset + '0 30 0';
			}
			if ((j == 8))
			{
				posoffset = posoffset + '0 2 0';
			}
			if ((j == 9))
			{
				posoffset = posoffset + '0 8 0';
			}
			pos[((j * 3) / 3)] = (pos[((j * 3) / 3)] - posoffset);
			j = j + 1;
		}
		drawSelectArrow(pos[(((keySelect - 1) * 3) / 3)], 1);
		if ((keySelect == 9))
		{
			UIDraw = 1;
		}
		else
		{
			UIDraw = 0;
		}
	}
	else
	{
		if ((inMenu == 2))
		{
			j = 0;
			while ((j <= 15))
			{
				if ((j >= 1))
				{
					posoffset = posoffset + '0 10 0';
				}
				if ((j == 3))
				{
					posoffset = posoffset + '0 30 0';
				}
				if ((j == 8))
				{
					posoffset = posoffset + '0 20 0';
				}
				if ((j == 13))
				{
					posoffset = posoffset + '0 10 0';
				}
				pos[((j * 3) / 3)] = (pos[((j * 3) / 3)] - posoffset);
				j = j + 1;
			}
			drawSelectArrow(pos[(((keySelect - 1) * 3) / 3)], 1);
		}
		else
		{
			if ((inMenu == 3))
			{
				j = 0;
				while ((j <= 15))
				{
					if ((j >= 1))
					{
						posoffset = posoffset + '0 10 0';
					}
					if ((j == 14))
					{
						posoffset = posoffset + '0 50 0';
					}
					pos[((j * 3) / 3)] = (pos[((j * 3) / 3)] - posoffset);
					j = j + 1;
				}
				drawSelectArrow(pos[(((keySelect - 1) * 3) / 3)], 1);
			}
			else
			{
				if ((inMenu == 5))
				{
					j = 0;
					while ((j <= 14))
					{
						if ((j >= 1))
						{
							posoffset = posoffset + '0 10 0';
						}
						if ((j == 10))
						{
							posoffset = posoffset + '0 30 0';
						}
						pos[((j * 3) / 3)] = (pos[((j * 3) / 3)] - posoffset);
						j = j + 1;
					}
					drawSelectArrow(pos[(((keySelect - 1) * 3) / 3)], 1);
				}
			}
		}
	}
};

void() saveCFG =
{
	local float fedit;
	local string savedcvar[20];
	local float x;

	savedcvar[0] = strcat("'", ftos(cvar("redarmor_backpack")), "'");
	savedcvar[1] = strcat("'", ftos(cvar("chainsaw_drops")), "'");
	savedcvar[2] = strcat("'", ftos(cvar("soldier_nailgrunt")), "'");
	savedcvar[3] = strcat("'", ftos(cvar("enforcer_defender")), "'");
	savedcvar[4] = strcat("'", ftos(cvar("enforcer_defender_prox")), "'");
	savedcvar[5] = strcat("'", ftos(cvar("shalrath_mother")), "'");
	savedcvar[6] = strcat("'", ftos(cvar("wizardteleport")), "'");
	savedcvar[7] = strcat("'", ftos(cvar("nospinup")), "'");
	savedcvar[8] = strcat("'", ftos(cvar("yakman_replace_shambler")), "'");
	savedcvar[9] = strcat("'", ftos(cvar("hud_proxcount_big")), "'");
	savedcvar[10] = strcat("'", ftos(cvar("hud_showtitle")), "'");
	savedcvar[11] = strcat("'", ftos(cvar("qc_ssg")), "'");
	savedcvar[12] = strcat("'", ftos(cvar("centered_weapons")), "'");
	savedcvar[13] = strcat("'", ftos(cvar("flamestyle")), "'");
	savedcvar[14] = strcat("'", ftos(cvar("gibsduration")), "'");
	savedcvar[15] = strcat("'", ftos(cvar("slowmotion")), "'");
	savedcvar[16] = strcat("'", ftos(cvar("deathmatch_music")), "'");
	savedcvar[17] = strcat("'", ftos(cvar("slowmo_powerup")), "'");
	savedcvar[18] = strcat("'", ftos(maxplayers), "'");
	fedit = fopen("config_menu.cfg", FILE_WRITE);
	x = 0;
	while ((x <= 19))
	{
		fputs(fedit, strcat(" ", savedcvar[x]));
		x = x + 1;
	}
	fclose(fedit);
};

void() loadCFG =
{
	local float fedit;
	local string readcvar[20];
	local float x;

	fedit = fopen("config_menu.cfg", FILE_READ);
	if ((fedit < 0))
		return;
	tokenize(fgets(fedit));
	x = 0;
	while ((x <= 19))
	{
		readcvar[x] = argv(x);
		x = x + 1;
	}
	fclose(fedit);
	cvar_set("redarmor_backpack", readcvar[0]);
	cvar_set("chainsaw_drops", readcvar[1]);
	cvar_set("soldier_nailgrunt", readcvar[2]);
	cvar_set("enforcer_defender", readcvar[3]);
	cvar_set("enforcer_defender_prox", readcvar[4]);
	cvar_set("shalrath_mother", readcvar[5]);
	cvar_set("wizardteleport", readcvar[6]);
	cvar_set("nospinup", readcvar[7]);
	cvar_set("yakman_replace_shambler", readcvar[8]);
	cvar_set("hud_proxcount_big", readcvar[9]);
	cvar_set("hud_showtitle", readcvar[10]);
	cvar_set("qc_ssg", readcvar[11]);
	cvar_set("centered_weapons", readcvar[12]);
	cvar_set("flamestyle", readcvar[13]);
	cvar_set("gibsduration", readcvar[14]);
	cvar_set("slowmotion", readcvar[15]);
	cvar_set("deathmatch_music", readcvar[16]);
	cvar_set("slowmo_powerup", readcvar[17]);
	maxplayers = stof(readcvar[18]);
};

void() infoMenu1 =
{
	if ((((keySelect != 8) && (keySelect != 9)) && (keySelect != 10)))
	{
		Sbar_DrawString('-150 62 0', "Press DELETE to clear keybinds", 1, '8 8 0', '1 0.8 0');
	}
	if ((keySelect == 1))
	{
		Sbar_DrawString('-120 92 0', "Throws Proximity Grenade", 1, '8 8 0', '0.7 0.7 0.7');
		Sbar_DrawString('-60 82 0', "Default: G", 1, '8 8 0', '1 0 0');
	}
	if ((keySelect == 2))
	{
		Sbar_DrawString('-140 92 0', "Quick Melee Kick, knocks back enemies", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-60 82 0', "Default: Shift", 1, '8 8 0', '1 0 0');
	}
	if ((keySelect == 3))
	{
		Sbar_DrawString('-90 92 0', "Toggle Flashlight", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-60 82 0', "Default: F", 1, '8 8 0', '1 0 0');
	}
	if ((keySelect == 4))
	{
		Sbar_DrawString('-115 92 0', "Toggle 3rd person camera", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-60 82 0', "Default: C", 1, '8 8 0', '1 0 0');
	}
	if ((keySelect == 5))
	{
		Sbar_DrawString('-145 92 0', "Add bot (friendly bot in team games)", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-60 82 0', "Default: F1", 1, '8 8 0', '1 0 0');
	}
	if ((keySelect == 6))
	{
		Sbar_DrawString('-120 92 0', "Add enemy bot in team games", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-60 82 0', "Default: F2", 1, '8 8 0', '1 0 0');
	}
	if ((keySelect == 7))
	{
		Sbar_DrawString('-60 92 0', "Remove a bot", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-60 82 0', "Default: F3", 1, '8 8 0', '1 0 0');
	}
	if ((keySelect == 8))
	{
		Sbar_DrawString('-145 92 0', "Use offhand grapple (MP games only)", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-60 82 0', "Default: Q", 1, '8 8 0', '1 0 0');
	}
	if ((keySelect == 9))
	{
		Sbar_DrawString('-90 92 0', "Scale HUD/UI up and down", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 10))
	{
		Sbar_DrawString('-120 92 0', "Visuals, HUD, and Server options", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 11))
	{
		Sbar_DrawString('-120 92 0', "Tweak additional monster/item settings", 1, '8 8 0', '0.6 0.6 0.6');
	}
};

void() infoMenu2 =
{
	if ((keySelect == 1))
	{
		Sbar_DrawString('-180 42 0', "Determines quality of particles, gib lifetime, ", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-180 32 0', "and other settings defined in q15_config_coop.cfg", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-180 22 0', "(low) and q15_config.cfg (high)", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-110 12 0', "-- REQUIRES MAP RESTART --", 1, '8 8 0', '1 0.1 0');
	}
	if ((keySelect == 2))
	{
		Sbar_DrawString('-140 42 0', "Determines the maximum amount of", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-140 32 0', "decals (blood, bullet holes, etc.)", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-140 22 0', "active before removing old ones", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-130 12 0', "Min: 1500", 1, '8 8 0', '1 0 0');
		Sbar_DrawString('-40 12 0', "Medium: 2800", 1, '8 8 0', '1 0.8 0');
		Sbar_DrawString('70 12 0', "Max: 4500", 1, '8 8 0', '0 1 0');
	}
	if ((keySelect == 3))
	{
		Sbar_DrawString('-140 42 0', "Determines the maximum amount of", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-160 32 0', "time (in seconds) decals remain before being removed", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-130 12 0', "Min: 200", 1, '8 8 0', '1 0 0');
		Sbar_DrawString('-40 12 0', "Medium: 900", 1, '8 8 0', '1 0.8 0');
		Sbar_DrawString('70 12 0', "Max: 4500", 1, '8 8 0', '0 1 0');
	}
	if ((keySelect == 4))
	{
		Sbar_DrawString('-180 42 0', "Enables lives in cooperative play - players respawn ", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-180 32 0', "where they died, megahealth gives a bonus life to all", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-180 22 0', "and the map restarts once all players are dead", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 5))
	{
		Sbar_DrawString('-150 42 0', "Amount of lives per player in coop -", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-160 32 0', "configurable with coop_lives in console", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 6))
	{
		Sbar_DrawString('-150 42 0', "Spawns additional monsters in a level based on", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-150 32 0', "the amount specified - good for coop scaling", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-110 22 0', "-- REQUIRES MAP RESTART --", 1, '8 8 0', '1 0.1 0');
	}
	if ((keySelect == 7))
	{
		Sbar_DrawString('-150 42 0', "Gibs stay for specified amount of time, lowering", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-150 32 0', "will help improve network performance in netgames ", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-150 22 0', "if set to forever, gibs will never be cleaned up ", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 8))
	{
		Sbar_DrawString('-300 42 0', "If enabled, autosaves when using or picking up keys and discovering secrets", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-300 32 0', "WARNING: only reliable per session; when exiting game make a manual save.", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 9))
	{
		Sbar_DrawString('-130 42 0', "Choose size of proximity grenade indicator", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-130 32 0', "Large - same size as health/current ammo", 1, '8 8 0', '0 1 0');
		Sbar_DrawString('-130 22 0', "Tiny - aligned with ammo bar", 1, '8 8 0', '1 0 0');
	}
	if ((keySelect == 10))
	{
		Sbar_DrawString('-130 42 0', "Display level title on map start", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-130 32 0', "with a fancy fade/twitching effect", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 11))
	{
		Sbar_DrawString('-130 42 0', "Choose whether to use the old Q15", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-130 32 0', "SSG Model or the new Quake Champions design", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 12))
	{
		Sbar_DrawString('-180 42 0', "Modified weapon models inspired by classic Quake -", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-70 32 0', "centered on screen with tweaked animations", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 13))
	{
		Sbar_DrawString('-180 42 0', "If enabled, utilize particle effects for torches ", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-210 32 0', "and _flame light entities - otherwise use enhanced 3d variants", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-110 22 0', "-- REQUIRES MAP RESTART --", 1, '8 8 0', '1 0.1 0');
		Sbar_DrawString('-160 12 0', "-- Disabling can improve network performance --", 1, '8 8 0', '1 0.8 0');
	}
	if ((keySelect == 14))
	{
		Sbar_DrawString('-120 42 0', "Restart level and apply config changes", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 15))
	{
		Sbar_DrawString('-100 42 0', "Back to keybinds menu", 1, '8 8 0', '0.6 0.6 0.6');
	}
};

void() infoMenu3 =
{
	if ((keySelect == 1))
	{
		Sbar_DrawString('-200 42 0', "When enabled, there's a 20% chance for a backpack with", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-200 32 0', "proximity grenades and ammo to spawn instead of red armor.", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-200 22 0', "Can also give you more than max ammo if you have enough. ", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-110 12 0', "-- REQUIRES MAP RESTART --", 1, '8 8 0', '1 0.1 0');
	}
	if ((keySelect == 2))
	{
		Sbar_DrawString('-190 42 0', "When enabled, a small chance the chainsaw weapon will ", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-190 32 0', "randomly drop from gibbed ogres.", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-190 22 0', "Refer to TIPS below for further chainsaw information.", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 3))
	{
		Sbar_DrawString('-300 42 0', "The speed at which you come to a stop after running. The faster it", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-300 32 0', "is the more fine control you have, helpful e.g when platforming", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 4))
	{
		Sbar_DrawString('-290 42 0', "When enabled, turns the green enforcer variant into a Defender - uses", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-290 32 0', "shotgun up close, rapid fire laser, and sets proximity grenade traps", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-290 22 0', "Overhauled behaviour in Combat+", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 5))
	{
		Sbar_DrawString('-300 42 0', "If enabled: will automatically switch when obtaining weapons, if new.", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-300 32 0', "All other instances of auto weapon switching is removed in Combat+", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-300 22 0', "with the exception of running out of ammo", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 6))
	{
		Sbar_DrawString('-310 42 0', "If enabled, Super Shotgun behaves like vanilla albiet with slightly faster", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-310 32 0', "rate of fire. If disabled, Combat+ double shot that incentivises kicking &", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-310 22 0', "managing shot timing. Both also have slightly increased accuracy and recoil", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 7))
	{
		Sbar_DrawString('-290 42 0', "Gives a low chance for a vore to become a vore mother - spawns vorelings", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 8))
	{
		Sbar_DrawString('-290 42 0', "When disabled, SNG has no spin-up delay and vanilla ROF, however with", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-290 32 0', "spin-up on ROF is slightly faster when the barrel enters full spin cycle", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 9))
	{
		Sbar_DrawString('-300 42 0', "When enabled, there is a small chance to replace shamblers with the Yakman", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-300 32 0', "from Hexen II ", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-300 22 0', "Overhauled Behaviour in Combat+", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 10))
	{
		Sbar_DrawString('-260 42 0', "Toggle weapon recoil effects & screenshake from explosions On/Off", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 11))
	{
		Sbar_DrawString('-315 52 0', "For the hardcore whom think nightmare difficulty is just not enough:", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-300 40 0', "-Enemy spawn rates increased + blast radius of select enemy attacks increased", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-300 30 0', "-Berserk Packs only grant 50 health", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-300 20 0', "-35% chance quad damages will be replaced by a berserk pentagram", 1, '8 8 0', '0.6 0.6 0.6');
		Sbar_DrawString('-300 10 0', "-Souls of demons you've slain seek revenge. Avoid!", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 12))
	{
		Sbar_DrawString('-230 42 0', "Small chance to slow down time on enemy gibbed", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 13))
	{
		Sbar_DrawString('-230 42 0', "Enable unused Quake 3 songs during deathmatch games", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 14))
	{
		Sbar_DrawString('-310 57 0', "Press [enter] for next tip.", 1, '8 8 0', '1 0.3 0.2');
		if ((cvar("qtips") < 0.1))
		{
			Sbar_DrawString('-310 42 0', "Melee Combat: Axe deals the most damage per hit and has low chance to stun.", 1, '8 8 0', '0.6 0.6 0.6');
			Sbar_DrawString('-310 32 0', "Chainsaw has the most reach and can kill zombies. Not affected by berserk.", 1, '8 8 0', '0.6 0.6 0.6');
			Sbar_DrawString('-310 22 0', "Kick has high chance to stun and knocks enemies back. Can also combo attack.", 1, '8 8 0', '0.6 0.6 0.6');
		}
		else
		{
			if ((cvar("qtips") < 0.2))
			{
				Sbar_DrawString('-310 42 0', "Shamblers have 35% explosive resistance now, not 50%. Explosives are a little", 1, '8 8 0', '0.6 0.6 0.6');
				Sbar_DrawString('-310 32 0', "more viable, but it's still often not a good idea.", 1, '8 8 0', '0.6 0.6 0.6');
			}
			else
			{
				if ((cvar("qtips") < 0.3))
				{
					Sbar_DrawString('-310 42 0', "The berserk pack increases melee damage, stun chance and knockback. Berserk", 1, '8 8 0', '0.6 0.6 0.6');
					Sbar_DrawString('-310 32 0', "is only present for the current life. Die or even Load game and it is gone.", 1, '8 8 0', '0.6 0.6 0.6');
				}
				else
				{
					if ((cvar("qtips") < 0.4))
					{
						Sbar_DrawString('-310 42 0', "Manually reload the Super Shotgun by pressing '3'. Cycling next/prev weapon", 1, '8 8 0', '0.6 0.6 0.6');
						Sbar_DrawString('-310 32 0', "will not reload the weapon, only the hotkey.", 1, '8 8 0', '0.6 0.6 0.6');
						Sbar_DrawString('-310 22 0', "Dislike the new SSG functioning? Reenable vanilla SSG from the options above.", 1, '8 8 0', '0.6 0.6 0.6');
					}
					else
					{
						if ((cvar("qtips") < 0.5))
						{
							Sbar_DrawString('-310 42 0', "The flashlight [default: F] helps find secrets and in checking dark corners", 1, '8 8 0', '0.6 0.6 0.6');
						}
						else
						{
							if ((cvar("qtips") < 0.6))
							{
								Sbar_DrawString('-310 42 0', "Proximity Grenades: You can shoot prox grenades, and stick them to surfaces.", 1, '8 8 0', '0.6 0.6 0.6');
								Sbar_DrawString('-310 32 0', "They are rare in Combat+, sometimes replacing an ammo pickup of equal value.", 1, '8 8 0', '0.6 0.6 0.6');
								Sbar_DrawString('-310 22 0', "You can combo them (use between weapon animations such as between SSG shots).", 1, '8 8 0', '0.6 0.6 0.6');
							}
							else
							{
								if ((cvar("qtips") < 0.7))
								{
									Sbar_DrawString('-310 42 0', "Monster Info: Reivers are a pressure demon that always closes in on you. At a", 1, '8 8 0', '0.6 0.6 0.6');
									Sbar_DrawString('-310 32 0', "distance they can be managed. Up close they drain health from you and explode", 1, '8 8 0', '0.6 0.6 0.6');
									Sbar_DrawString('-310 22 0', "when killed. Will also phase through walls and catch you off guard.", 1, '8 8 0', '0.6 0.6 0.6');
								}
								else
								{
									if ((cvar("qtips") < 0.8))
									{
										Sbar_DrawString('-310 42 0', "Combat+ comes with 2016's Episode 5 installed by default. Press [Backspace]", 1, '8 8 0', '0.6 0.6 0.6');
										Sbar_DrawString('-310 32 0', "in-game to access maplist and start it from there: 'E5M1'.", 1, '8 8 0', '0.6 0.6 0.6');
										Sbar_DrawString('-310 22 0', "You can also change difficulty from this map select menu.", 1, '8 8 0', '0.6 0.6 0.6');
										Sbar_DrawString('-310 12 0', "Any custom maps you place in your 'Maps' folder will also appear here.", 1, '8 8 0', '0.6 0.6 0.6');
									}
									else
									{
										if ((cvar("qtips") < 0.9))
										{
											Sbar_DrawString('-310 42 0', "Do you have what it takes? Nightmare difficulty is considerably overhauled in", 1, '8 8 0', '0.6 0.6 0.6');
											Sbar_DrawString('-310 32 0', "in Combat+. You've not faced a Quake horde like this.", 1, '8 8 0', '0.6 0.6 0.6');
										}
										else
										{
											if ((cvar("qtips") < 1))
											{
												Sbar_DrawString('-310 42 0', "All of the lower tier weapons (Axe, Shotgun, Nailgun, Grenade Launcher) are", 1, '8 8 0', '0.6 0.6 0.6');
												Sbar_DrawString('-310 32 0', "more effective in some way in Combat+ -- don't underestimate them!", 1, '8 8 0', '0.6 0.6 0.6');
											}
											else
											{
												if ((cvar("qtips") < 1.1))
												{
													Sbar_DrawString('-310 42 0', "Monster Info: Warlords have explosive resistance just like shamblers, rarely", 1, '8 8 0', '0.6 0.6 0.6');
													Sbar_DrawString('-310 32 0', "infight with other monsters, are deadly at close-medium ranges, and have a", 1, '8 8 0', '0.6 0.6 0.6');
													Sbar_DrawString('-310 22 0', "low chance to drop new powerups when killed.", 1, '8 8 0', '0.6 0.6 0.6');
												}
												else
												{
													if ((cvar("qtips") < 1.2))
													{
														Sbar_DrawString('-310 42 0', "Compatible with custom maps! Combat+ balance stays relatively close to", 1, '8 8 0', '0.6 0.6 0.6');
														Sbar_DrawString('-310 32 0', "vanilla overall, a little harder but nothing you can't handle, right?", 1, '8 8 0', '0.6 0.6 0.6');
														Sbar_DrawString('-310 22 0', "Note: only compatible with custom content that does not modify Progs.dat.", 1, '8 8 0', '0.6 0.6 0.6');
														Sbar_DrawString('-310 12 0', "Download maps for free at Quaddicted.com.", 1, '8 8 0', '0.6 0.6 0.6');
													}
													else
													{
														if ((cvar("qtips") < 1.3))
														{
															Sbar_DrawString('-310 42 0', "Vanilla tip: armor still drains when you have a pentagram of protection. It's", 1, '8 8 0', '0.6 0.6 0.6');
															Sbar_DrawString('-310 32 0', "not some mindless god mode trip. Keep dodging and playing effectively!", 1, '8 8 0', '0.6 0.6 0.6');
														}
														else
														{
															if ((cvar("qtips") < 1.4))
															{
																Sbar_DrawString('-310 42 0', "Poisoned? Weigh the risks first, and if inclined, jump in water or grab a", 1, '8 8 0', '0.6 0.6 0.6');
																Sbar_DrawString('-310 32 0', "medkit to instantly remove this effect. Poison is nightmare skill-exclusive", 1, '8 8 0', '0.6 0.6 0.6');
															}
															else
															{
																Sbar_DrawString('-280 47 0', "Enemies infight less often on nightmare difficulty. It may take multiple", 1, '8 8 0', '0.6 0.6 0.6');
																Sbar_DrawString('-280 37 0', "attempts to get them to attack eachother.", 1, '8 8 0', '0.6 0.6 0.6');
																Sbar_DrawString('-280 19 0', "This is the end of the tips cycle", 1, '8 8 0', '0.45 0.45 0.45');
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
		Sbar_DrawString('-120 42 0', "Restart level and apply config changes", 1, '8 8 0', '0.6 0.6 0.6');
	}
	if ((keySelect == 16))
	{
		Sbar_DrawString('-100 42 0', "Back to keybinds menu", 1, '8 8 0', '0.6 0.6 0.6');
	}
};

void() infoPanel =
{
	if ((inMenu == 1))
	{
		infoMenu1();
	}
	if ((inMenu == 2))
	{
		infoMenu2();
	}
	if ((inMenu == 3))
	{
		infoMenu3();
	}
};

void() prepKeybinds =
{
	binds[0] = findkeysforcommand(/*8963i*/"ThrowGrenade", 0);
	binds[1] = findkeysforcommand(/*8976i*/"quickkick", 0);
	binds[2] = findkeysforcommand(/*8986i*/"flashlight", 0);
	binds[3] = findkeysforcommand(/*8997i*/"chasecam", 0);
	binds[4] = findkeysforcommand(/*9006i*/"addbot", 0);
	binds[5] = findkeysforcommand(/*9013i*/"addbotenemy", 0);
	binds[6] = findkeysforcommand(/*9025i*/"removebot", 0);
	binds[7] = findkeysforcommand(/*9035i*/"+hook", 0);
};

void() clearKey =
{
	local string binding;
	local string keycode;

	if ((keySelect == 9))
	{
		return;
	}
	prepKeybinds();
	if ((keySelect == 1))
	{
		binding = binds[0];
	}
	else
	{
		if ((keySelect == 2))
		{
			binding = binds[1];
		}
		else
		{
			if ((keySelect == 3))
			{
				binding = binds[2];
			}
			else
			{
				if ((keySelect == 4))
				{
					binding = binds[3];
				}
				else
				{
					if ((keySelect == 5))
					{
						binding = binds[4];
					}
					else
					{
						if ((keySelect == 6))
						{
							binding = binds[5];
						}
						else
						{
							if ((keySelect == 7))
							{
								binding = binds[6];
							}
							else
							{
								if ((keySelect == 8))
								{
									binding = binds[7];
								}
							}
						}
					}
				}
			}
		}
	}
	keycode = keynumtostring(stof(substring(binding, 2, 3)));
	if ((keycode != "<KEY NOT FOUND>"))
	{
		localcmd("unbind ", keycode, /*48i*/"\n");
	}
	sound(self, CHAN_AUTO, "misc/menu2.wav", 1, ATTN_NONE);
};

void() ShowKeybinds =
{
	local string keystr[8];
	local vector col[8];
	local vector pos[8];
	local vector posoffset;
	local float i;
	local float j;
	local float x;

	posoffset = '0 10 0';
	prepKeybinds();
	i = 0;
	while ((i <= 7))
	{
		keystr[i] = keynumtostring(stof(substring(binds[i], 2, 3)));
		pos[((i * 3) / 3)] = '170 272 0';
		i = i + 1;
	}
	j = 0;
	while ((j <= 7))
	{
		if ((j >= 1))
		{
			posoffset = posoffset + '0 10 0';
		}
		if ((j == 4))
		{
			posoffset = posoffset + '0 30 0';
		}
		pos[((j * 3) / 3)] = (pos[((j * 3) / 3)] - posoffset);
		j = j + 1;
	}
	x = 0;
	while ((x <= 7))
	{
		if ((keystr[x] == "<KEY NOT FOUND>"))
		{
			keystr[x] = "???";
			col[((x * 3) / 3)] = '1 0 0';
		}
		else
		{
			col[((x * 3) / 3)] = VEC_1;
		}
		col[((x * 3) / 3)];
		Sbar_DrawString(pos[((x * 3) / 3)], keystr[x], 1, '8 8 0', col[((x * 3) / 3)]);
		x = x + 1;
	}
};

void() loadScreenSize =
{

	if (((cvar("vid_width") / cvar("vid_height")) != 1.33333))
	{
		if ((cvar("vid_conwidth") == 624))
		{
			sliderPos = 0;
		}
		if ((cvar("vid_conwidth") == 640))
		{
			sliderPos = 1;
		}
		if ((cvar("vid_conwidth") == 672))
		{
			sliderPos = 2;
		}
		if ((cvar("vid_conwidth") == 688))
		{
			sliderPos = 3;
		}
		if ((cvar("vid_conwidth") == 720))
		{
			sliderPos = 4;
		}
		if ((cvar("vid_conwidth") == 752))
		{
			sliderPos = 5;
		}
		if ((cvar("vid_conwidth") == 816))
		{
			sliderPos = 6;
		}
		if ((cvar("vid_conwidth") == 1116))
		{
			sliderPos = 7;
		}
	}
};

void() updateScreenSize =
{

	if (((cvar("vid_width") / cvar("vid_height")) != 1.33333))
	{
		if ((sliderPos == 0))
		{
			wepbar_offset = VEC_0;
			cvar_set("vid_conwidth", "624");
			cvar_set("vid_conheight", "351");
		}
		else
		{
			if ((sliderPos == 1))
			{
				wepbar_offset = '10 5 0';
				cvar_set("vid_conwidth", "640");
				cvar_set("vid_conheight", "360");
			}
			else
			{
				if ((sliderPos == 2))
				{
					wepbar_offset = '25 10 0';
					cvar_set("vid_conwidth", "672");
					cvar_set("vid_conheight", "378");
				}
				else
				{
					if ((sliderPos == 3))
					{
						wepbar_offset = '35 15 0';
						cvar_set("vid_conwidth", "688");
						cvar_set("vid_conheight", "387");
					}
					else
					{
						if ((sliderPos == 4))
						{
							wepbar_offset = '50 20 0';
							cvar_set("vid_conwidth", "720");
							cvar_set("vid_conheight", "405");
						}
						else
						{
							if ((sliderPos == 5))
							{
								wepbar_offset = '65 25 0';
								cvar_set("vid_conwidth", "752");
								cvar_set("vid_conheight", "423");
							}
							else
							{
								if ((sliderPos == 6))
								{
									wepbar_offset = '95 35 0';
									cvar_set("vid_conwidth", "816");
									cvar_set("vid_conheight", "459");
								}
								else
								{
									if ((sliderPos == 7))
									{
										wepbar_offset = '245 85 0';
										cvar_set("vid_conwidth", "1116");
										cvar_set("vid_conheight", "630");
									}
								}
							}
						}
					}
				}
			}
		}
	}
	else
	{
		if ((sliderPos == 0))
		{
			wepbar_offset = '0 90 0';
			cvar_set("vid_conwidth", "632");
			cvar_set("vid_conheight", "471");
		}
		else
		{
			if ((sliderPos == 1))
			{
				wepbar_offset = '10 115 0';
				cvar_set("vid_conwidth", "640");
				cvar_set("vid_conheight", "480");
			}
			else
			{
				if ((sliderPos == 2))
				{
					wepbar_offset = '25 130 0';
					cvar_set("vid_conwidth", "672");
					cvar_set("vid_conheight", "504");
				}
				else
				{
					if ((sliderPos == 3))
					{
						wepbar_offset = '35 145 0';
						cvar_set("vid_conwidth", "688");
						cvar_set("vid_conheight", "516");
					}
					else
					{
						if ((sliderPos == 4))
						{
							wepbar_offset = '50 160 0';
							cvar_set("vid_conwidth", "720");
							cvar_set("vid_conheight", "540");
						}
						else
						{
							if ((sliderPos == 5))
							{
								wepbar_offset = '65 185 0';
								cvar_set("vid_conwidth", "752");
								cvar_set("vid_conheight", "564");
							}
							else
							{
								if ((sliderPos == 6))
								{
									wepbar_offset = '80 200 0';
									cvar_set("vid_conwidth", "784");
									cvar_set("vid_conheight", "588");
								}
								else
								{
									if ((sliderPos == 7))
									{
										wepbar_offset = '95 225 0';
										cvar_set("vid_conwidth", "816");
										cvar_set("vid_conheight", "612");
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

void() ShowSlider =
{
	local vector pos[8];
	local vector offsetMod;
	local float i;
	local float j;

	i = 0;
	while ((i <= 7))
	{
		pos[((i * 3) / 3)] = '150 148 0';
		i = i + 1;
	}
	j = 0;
	while ((j <= 7))
	{
		if ((j == 0))
		{
			offsetMod = '5 0 0';
		}
		else
		{
			offsetMod = offsetMod + '5 0 0';
		}
		pos[((j * 3) / 3)] = (pos[((j * 3) / 3)] + offsetMod);
		j = j + 1;
	}
	Sbar_DrawCharacter(pos[((sliderPos * 3) / 3)], 131, 1);
	updateScreenSize();
};

void() DrawSliderSlot =
{
	Sbar_DrawCharacter('150 148 0', 128, 1);
	Sbar_DrawCharacter('155 148 0', 129, 1);
	Sbar_DrawCharacter('160 148 0', 129, 1);
	Sbar_DrawCharacter('165 148 0', 129, 1);
	Sbar_DrawCharacter('170 148 0', 129, 1);
	Sbar_DrawCharacter('175 148 0', 129, 1);
	Sbar_DrawCharacter('180 148 0', 129, 1);
	Sbar_DrawCharacter('185 148 0', 129, 1);
	Sbar_DrawCharacter('190 148 0', 129, 1);
	Sbar_DrawCharacter('195 148 0', 130, 1);
};

void() TogglePause =
{
	local float cur;

	cur = cvar("slowmo");
	if ((cur > 0))
		GSPEED_SAV = cur;
	if ((canPause && inMenu))
	{
		if ((cur > 0))
		{
			pause_was_active = 1;
			cvar_set("slowmo", "0");
		}
	}
	else if (pause_was_active)
	{
		pause_was_active = 0;
		if ((GSPEED_SAV <= 0))
			GSPEED_SAV = 1;
		cvar_set("slowmo", ftos(GSPEED_SAV));
	}
};

void() bindingsMenu =
{
	ShowKeybinds();
	Sbar_DrawString('-70 282 0', "Singleplayer Keybinds", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-70 280 0', "_____________________", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-60 262 0', "Throw Grenade", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('-60 252 0', "Melee Kick", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('-60 242 0', "Flashlight", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('-60 232 0', "Chasecam", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('-70 212 0', "Multiplayer Keybinds", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-70 210 0', "____________________", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-60 192 0', "Add Bot", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('-60 182 0', "Add Enemy Bot (teamplay)", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('-60 172 0', "Remove Bot", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('-60 162 0', "Hook", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('-60 148 0', "UI Scale:", 1, '8 8 0', '1 0.6 0.3');
	DrawSliderSlot();
	ShowSlider();
	Sbar_DrawString('-60 132 0', "General Options", 1, '8 8 0', VEC_1);
	Sbar_DrawString('-60 122 0', "Game Tweaks", 1, '8 8 0', VEC_1);
	menuItemSelector();
};

void() gameplayMenu =
{
	Sbar_DrawString('-70 282 0', "General Options", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-70 280 0', "_______________", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-60 262 0', "Quality:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("lowspec") == 0))
	{
		Sbar_DrawString('120 262 0', "High", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("lowspec") == 1))
		{
			Sbar_DrawString('120 262 0', "Low", 1, '8 8 0', '1 0 0');
		}
	}
	Sbar_DrawString('-60 252 0', "Max Active Decals:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("cl_decals_max") > 4400))
	{
		Sbar_DrawString('120 252 0', "Max", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("cl_decals_max") >= 2800))
		{
			Sbar_DrawString('120 252 0', "Medium", 1, '8 8 0', '1 0.8 0');
		}
		else
		{
			if ((cvar("cl_decals_max") < 2800))
			{
				Sbar_DrawString('120 252 0', "Min", 1, '8 8 0', '1 0 0');
			}
		}
	}
	Sbar_DrawString('-60 242 0', "Decal Time:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("cl_decals_time") > 4100))
	{
		Sbar_DrawString('120 242 0', "Max", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("cl_decals_time") >= 700))
		{
			Sbar_DrawString('120 242 0', "Medium", 1, '8 8 0', '1 0.8 0');
		}
		else
		{
			if ((cvar("cl_decals_time") < 300))
			{
				Sbar_DrawString('120 242 0', "Min", 1, '8 8 0', '1 0 0');
			}
		}
	}
	Sbar_DrawString('-70 222 0', "Server Options", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-70 220 0', "______________", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-60 202 0', "Coop - Lives System:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("coop_life_pool") == 0))
	{
		Sbar_DrawString('120 202 0', "Disabled", 1, '8 8 0', '1 0 0');
	}
	else
	{
		Sbar_DrawString('120 202 0', "Enabled", 1, '8 8 0', '0 1 0');
	}
	Sbar_DrawString('-60 192 0', "Coop - Life Count:", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('120 192 0', ftos(cvar("coop_lives")), 1, '8 8 0', '1 0 0');
	Sbar_DrawString('-60 182 0', "Clone Monsters:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("clonemonsters") == 0))
	{
		Sbar_DrawString('120 182 0', "Disabled", 1, '8 8 0', '1 0 0');
	}
	else
	{
		Sbar_DrawString('120 182 0', ftos(cvar("clonemonsters")), 1, '8 8 0', '1 0 0');
	}
	Sbar_DrawString('-60 172 0', "Gib Duration:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("gibsduration") == 0))
	{
		Sbar_DrawString('120 172 0', "Forever", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("gibsduration") == 1))
		{
			Sbar_DrawString('120 172 0', strcat(ftos(cvar("gibsduration")), " Second"), 1, '8 8 0', '1 0 0');
		}
		else
		{
			if ((cvar("gibsduration") == 10))
			{
				Sbar_DrawString('120 172 0', strcat(ftos(cvar("gibsduration")), " Seconds (Q1 Default)"), 1, '7 7 0', '1 0.5 0');
			}
			else
			{
				if ((cvar("gibsduration") < 15))
				{
					Sbar_DrawString('120 172 0', strcat(ftos(cvar("gibsduration")), " Seconds"), 1, '8 8 0', '1 0 0');
				}
				else
				{
					Sbar_DrawString('120 172 0', strcat(ftos(cvar("gibsduration")), " Seconds"), 1, '8 8 0', '1 0.9 0');
				}
			}
		}
	}
	Sbar_DrawString('-60 162 0', "Autosaving (SP):", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("auto_save") == 0))
	{
		Sbar_DrawString('120 162 0', "Disabled", 1, '8 8 0', '1 0 0');
	}
	else
	{
		Sbar_DrawString('120 162 0', "Enabled", 1, '8 8 0', '0 1 0');
	}
	Sbar_DrawString('-70 148 0', "HUD/Misc Options", 1, '7 7 0', '0.7 1 0.1');
	Sbar_DrawString('-70 146 0', "________________", 1, '7 7 0', '0.7 1 0.1');
	Sbar_DrawString('-60 132 0', "Grenade icon size:", 1, '8 8 0', '1 0.6 0.3');
	if (!cvar("hud_proxcount_big"))
	{
		Sbar_DrawString('120 132 0', "Tiny", 1, '8 8 0', '1 0 0');
	}
	else
	{
		Sbar_DrawString('120 132 0', "Large", 1, '8 8 0', '0 1 0');
	}
	Sbar_DrawString('-60 122 0', "Show Level Name:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("hud_showtitle") == 0))
	{
		Sbar_DrawString('120 122 0', "No", 1, '8 8 0', '1 0 0');
	}
	else
	{
		Sbar_DrawString('120 122 0', "Yes", 1, '8 8 0', '0 1 0');
	}
	Sbar_DrawString('-60 112 0', "Alternate SSG:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("qc_ssg") == 0))
	{
		Sbar_DrawString('120 112 0', "No", 1, '8 8 0', '1 0 0');
	}
	else
	{
		Sbar_DrawString('120 112 0', "Yes", 1, '8 8 0', '0 1 0');
	}
	Sbar_DrawString('-60 102 0', "Centered Weapons:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("centered_weapons") == 0))
	{
		Sbar_DrawString('120 102 0', "No", 1, '8 8 0', '1 0 0');
	}
	else
	{
		Sbar_DrawString('120 102 0', "Yes", 1, '8 8 0', '0 1 0');
	}
	Sbar_DrawString('-60 92 0', "Particle Flames:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("flamestyle") != 2))
	{
		Sbar_DrawString('120 92 0', "No", 1, '8 8 0', '1 0 0');
	}
	else
	{
		Sbar_DrawString('120 92 0', "Yes", 1, '8 8 0', '0 1 0');
	}
	Sbar_DrawString('-60 72 0', "Restart Map", 1, '8 8 0', VEC_1);
	Sbar_DrawString('-60 62 0', "Keybinds Menu", 1, '8 8 0', VEC_1);
	menuItemSelector();
};

void() MonMenu =
{
	local string tele;
	local string burner;
	local vector percolor;
	local vector percolor2;

	tele = ftos(cvar("wizardteleport"));
	burner = ftos(cvar("nospinup"));
	if ((cvar("wizardteleport") > 50))
	{
		percolor = '0 1 0';
	}
	else
	{
		if ((cvar("wizardteleport") > 10))
		{
			percolor = '1 0.8 0';
		}
		else
		{
			percolor = '1 0 0';
		}
	}
	if ((cvar("fire_projectiles_and_lava_inflame_time") >= 50))
	{
		percolor2 = '0 1 0';
	}
	else
	{
		if ((cvar("fire_projectiles_and_lava_inflame_time") > 10))
		{
			percolor2 = '1 0.8 0';
		}
		else
		{
			percolor2 = '1 0 0';
		}
	}
	Sbar_DrawString('-70 282 0', "Gameplay Options", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-70 280 0', "________________", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-60 262 0', "Ammo pack spawns:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("redarmor_backpack") == 1))
	{
		Sbar_DrawString('140 262 0', "On", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("redarmor_backpack") == 0))
		{
			Sbar_DrawString('140 262 0', "Off", 1, '8 8 0', '1 0 0');
		}
	}
	Sbar_DrawString('-60 252 0', "Chainsaw Drops:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("chainsaw_drops") == 1))
	{
		Sbar_DrawString('140 252 0', "On", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("chainsaw_drops") == 0))
		{
			Sbar_DrawString('140 252 0', "Off", 1, '8 8 0', '1 0 0');
		}
	}
	Sbar_DrawString('-60 242 0', "Stop Speed:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("sv_stopspeed") == 100))
	{
		Sbar_DrawString('140 242 0', "Vanilla", 1, '8 8 0', '1 0 0');
	}
	else
	{
		if ((cvar("sv_stopspeed") == 150))
		{
			Sbar_DrawString('140 242 0', "+50%", 1, '8 8 0', '0 1 0');
		}
		else
		{
			if ((cvar("sv_stopspeed") == 200))
			{
				Sbar_DrawString('140 242 0', "Double", 1, '8 8 0', '0 0 1');
			}
		}
	}
	Sbar_DrawString('-60 232 0', "Defenders:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("enforcer_defender") == 1))
	{
		Sbar_DrawString('140 232 0', "On", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("enforcer_defender") == 0))
		{
			Sbar_DrawString('140 232 0', "Off", 1, '8 8 0', '1 0 0');
		}
	}
	Sbar_DrawString('-60 222 0', "Weapon Auto Switch:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("weaponautoswitch") == 3))
	{
		Sbar_DrawString('140 222 0', "On", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("weaponautoswitch") == 0))
		{
			Sbar_DrawString('140 222 0', "Off", 1, '8 8 0', '1 0 0');
		}
	}
	Sbar_DrawString('-60 212 0', "Vanilla SSG:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("vanilla_ssg") > 0))
	{
		Sbar_DrawString('140 212 0', "On", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("vanilla_ssg") == 0))
		{
			Sbar_DrawString('140 212 0', "Off", 1, '8 8 0', '1 0 0');
		}
	}
	Sbar_DrawString('-60 202 0', "Shalrath Mother:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("shalrath_mother") == 1))
	{
		Sbar_DrawString('140 202 0', "On", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("shalrath_mother") == 0))
		{
			Sbar_DrawString('140 202 0', "Off", 1, '8 8 0', '1 0 0');
		}
	}
	Sbar_DrawString('-60 192 0', "Super Nailgun Spin-up:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("nospinup") == 0))
	{
		Sbar_DrawString('140 192 0', "On", 1, '8 8 0', '0 1 0');
	}
	else
	{
		if ((cvar("nospinup") > 0))
		{
			Sbar_DrawString('140 192 0', "Off", 1, '8 8 0', '1 0 0');
		}
	}
	Sbar_DrawString('-60 182 0', "Yakman Replacer:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("yakman_replace_shambler") > 0))
	{
		Sbar_DrawString('140 182 0', "On", 1, '8 8 0', '0 1 0');
	}
	else
	{
		Sbar_DrawString('140 182 0', "Off", 1, '8 8 0', '1 0 0');
	}
	Sbar_DrawString('-60 172 0', "Screenshake:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("effects_explosion_shake") > 0))
	{
		Sbar_DrawString('140 172 0', "On", 1, '8 8 0', '0 1 0');
	}
	else
	{
		Sbar_DrawString('140 172 0', "Off", 1, '8 8 0', '1 0 0');
	}
	Sbar_DrawString('-60 162 0', "Nightmare+:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("quadreplacer") == 0))
	{
		Sbar_DrawString('140 162 0', "Off", 1, '8 8 0', '1 0 0');
	}
	else
	{
		Sbar_DrawString('140 162 0', "On", 1, '8 8 0', '0 1 0');
	}
	Sbar_DrawString('-60 152 0', "Slowmo Kills:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("slowmotion") == 1))
	{
		Sbar_DrawString('140 152 0', "Enabled", 1, '8 8 0', '0 1 0');
	}
	else
	{
		Sbar_DrawString('140 152 0', "Disabled", 1, '8 8 0', '1 0 0');
	}
	Sbar_DrawString('-60 142 0', "Deathmatch Music:", 1, '8 8 0', '1 0.6 0.3');
	if ((cvar("deathmatch_music") == 1))
	{
		Sbar_DrawString('140 142 0', "Enabled", 1, '8 8 0', '0 1 0');
	}
	else
	{
		Sbar_DrawString('140 142 0', "Disabled", 1, '8 8 0', '1 0 0');
	}
	Sbar_DrawString('-60 132 0', "Q TIPS Q", 1, '8 8 0', '0.3 0.7 0.9');
	Sbar_DrawString('-60 72 0', "Restart Map", 1, '8 8 0', VEC_1);
	Sbar_DrawString('-60 62 0', "Keybinds Menu", 1, '8 8 0', VEC_1);
	menuItemSelector();
};

void() MPMenu =
{

	teamplay = cvar("teamplay");
	SkillCheck();
	if ((cvar("deathmatch") && (cvar("ctf") == 0)))
	{
		if ((cvar("teamplay") > 0))
		{
			gametype = "Team Deathmatch";
		}
		else
		{
			gametype = "Deathmatch";
		}
	}
	else
	{
		if ((cvar("ctf") == 1))
		{
			gametype = "Capture the Flag";
		}
		else
		{
			if (((cvar("coop") == 1) && (cvar("deathmatch") == 0)))
			{
				gametype = "Cooperative";
			}
			else
			{
				gametype = "Single Player";
			}
		}
	}
	Sbar_DrawString('-60 282 0', "Game Setup", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-60 280 0', "__________", 1, '8 8 0', '0.7 1 0.1');
	Sbar_DrawString('-60 262 0', "Max Players:", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('110 262 0', ftos(maxplayers), 1, '8 8 0', '1 0.6 0.4');
	Sbar_DrawString('-60 252 0', "Gametype:", 1, '8 8 0', '1 0.6 0.3');
	Sbar_DrawString('110 252 0', gametype, 1, '8 8 0', VEC_1);
	Sbar_DrawString('-60 242 0', "Weapons Stay:", 1, '8 8 0', '1 0.6 0.3');
	if ((!isSingle() && !isCoop()))
	{
		if (!weaponstay)
		{
			Sbar_DrawString('110 242 0', "Off", 1, '8 8 0', '1 0 0');
		}
		else
		{
			Sbar_DrawString('110 242 0', "On", 1, '8 8 0', '0 1 0');
		}
	}
	else
	{
		Sbar_DrawString('110 242 0', "N/A", 1, '8 8 0', '1 0 0');
	}
	if ((gametype != "Capture the Flag"))
	{
		Sbar_DrawString('-60 232 0', "Fraglimit:", 1, '8 8 0', '1 0.6 0.3');
	}
	else
	{
		Sbar_DrawString('-60 232 0', "Capture limit:", 1, '8 8 0', '1 0.6 0.3');
	}
	if ((!isSingle() && !isCoop()))
	{
		Sbar_DrawString('110 232 0', ftos(scorelimit), 1, '8 8 0', VEC_1);
	}
	else
	{
		Sbar_DrawString('110 232 0', "N/A", 1, '8 8 0', '1 0 0');
	}
	Sbar_DrawString('-60 222 0', "Timelimit:", 1, '8 8 0', '1 0.6 0.3');
	if ((!isSingle() && !isCoop()))
	{
		Sbar_DrawString('110 222 0', ftos(timelimit), 1, '8 8 0', VEC_1);
	}
	else
	{
		Sbar_DrawString('110 222 0', "N/A", 1, '8 8 0', '1 0 0');
	}
	Sbar_DrawString('-60 212 0', "Teamplay mode:", 1, '8 8 0', '1 0.6 0.3');
	if (!isSingle())
	{
		if ((teamplay == 1))
		{
			Sbar_DrawString('110 212 0', "No Friendly Fire", 1, '8 8 0', VEC_1);
		}
		else
		{
			if ((teamplay == 2))
			{
				Sbar_DrawString('110 212 0', "Friendly Fire", 1, '8 8 0', VEC_1);
			}
			else
			{
				Sbar_DrawString('110 212 0', "No Teams", 1, '8 8 0', '0.8 0.8 0.8');
			}
		}
	}
	else
	{
		Sbar_DrawString('110 212 0', "N/A", 1, '8 8 0', '1 0 0');
	}
	if ((isCTF() || isDeathmatch()))
	{
		Sbar_DrawString('-60 202 0', "Balance Teams:", 1, '8 8 0', '1 0.6 0.3');
	}
	else
	{
		Sbar_DrawString('-60 202 0', "Lives mode:", 1, '8 8 0', '1 0.6 0.3');
	}
	if (isCTF())
	{
		if (autobalance())
		{
			Sbar_DrawString('110 202 0', "On", 1, '8 8 0', '0 1 0');
		}
		else
		{
			Sbar_DrawString('110 202 0', "Off", 1, '8 8 0', '1 0 0');
		}
	}
	else
	{
		if ((isDeathmatch() || isSingle()))
		{
			Sbar_DrawString('110 202 0', "N/A", 1, '8 8 0', '1 0 0');
		}
		else
		{
			if (cvar("coop_life_pool"))
			{
				Sbar_DrawString('110 202 0', "On", 1, '8 8 0', '0 1 0');
			}
			else
			{
				Sbar_DrawString('110 202 0', "Off", 1, '8 8 0', '1 0 0');
			}
		}
	}
	if ((isCTF() || isDeathmatch()))
	{
		Sbar_DrawString('-60 192 0', "Bot Skill:", 1, '8 8 0', '1 0.6 0.3');
	}
	else
	{
		Sbar_DrawString('-60 192 0', "Difficulty:", 1, '8 8 0', '1 0.6 0.3');
	}
	if ((whatskill == 3))
	{
		Sbar_DrawString('110 192 0', skill[whatskill], 1, '8 8 0', '1 0 0');
	}
	else
	{
		if ((whatskill == 0))
		{
			Sbar_DrawString('110 192 0', skill[whatskill], 1, '8 8 0', '0 1 0.5');
		}
		else
		{
			Sbar_DrawString('110 192 0', skill[whatskill], 1, '8 8 0', '1 0.6 0');
		}
	}
	if ((!isSingle() && !isCoop()))
	{
		Sbar_DrawString('-60 182 0', "Bots:", 1, '8 8 0', '1 0.6 0.3');
	}
	else
	{
		Sbar_DrawString('-60 182 0', "Ammo Boxes:", 1, '8 8 0', '1 0.6 0.3');
	}
	if ((!isSingle() && !isCoop()))
	{
		Sbar_DrawString('110 182 0', ftos(botcount), 1, '8 8 0', VEC_1);
	}
	else
	{
		Sbar_DrawString('110 182 0', ammocap, 1, '8 8 0', '1 0 0');
	}
	Sbar_DrawString('-60 172 0', "Grapple:", 1, '8 8 0', '1 0.6 0.3');
	if ((!isSingle() && !isCoop()))
	{
		if ((checkHook() == SWING))
		{
			Sbar_DrawString('110 172 0', "Swinging Hook", 1, '8 8 0', '0 1 0');
		}
		else
		{
			if ((checkHook() == REEL))
			{
				Sbar_DrawString('110 172 0', "Classic Hook", 1, '8 8 0', '1 1 0');
			}
			else
			{
				Sbar_DrawString('110 172 0', "OFF", 1, '8 8 0', '1 0 0');
			}
		}
	}
	else
	{
		Sbar_DrawString('110 172 0', "N/A", 1, '8 8 0', '1 0 0');
	}
	Sbar_DrawString('-60 132 0', "Level Select", 1, '8 8 0', VEC_1);
	menuItemSelector();
};

void() menuSetup =
{
	if (!menu_was_open)
	{
		menu_was_open = 1;
		if ((cvar("sensitivity") > 0))
			mouse = cvar("sensitivity");
		cvar_set("sensitivity", "0");
	}
	drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.7, 0);
	if (((inMenu == 1) || (inMenu == 5)))
	{
		Sbar_DrawPic('-100 330 0', "gfx/ttl_cstm", 1, 1);
	}
	else
	{
		if (((inMenu > 0) && (inMenu < 4)))
		{
			Sbar_DrawPic('-80 330 0', "gfx/p_option", 1, 1);
		}
	}
	Sbar_DrawPic('-160 270 0', "gfx/qplaque", 1, 1);
	infoPanel();
};

void() showKeybindOverlay =
{
	drawfill('-70 -70 0', '2000 2000 0', VEC_0, 0.6, 0);
	if ((keySelect == 1))
	{
		Sbar_DrawString('-150 222 0', "Set custom keybind for Throw Grenade", 1, '8 8 0', '1 0.7 0');
	}
	else
	{
		if ((keySelect == 2))
		{
			Sbar_DrawString('-150 222 0', "Set custom keybind for Melee Kick", 1, '8 8 0', '1 0.7 0');
		}
		else
		{
			if ((keySelect == 3))
			{
				Sbar_DrawString('-150 222 0', "Set custom keybind for Flashlight", 1, '8 8 0', '1 0.7 0');
			}
			else
			{
				if ((keySelect == 4))
				{
					Sbar_DrawString('-150 222 0', "Set custom keybind for Chasecam", 1, '8 8 0', '1 0.7 0');
				}
				else
				{
					if ((keySelect == 5))
					{
						Sbar_DrawString('-150 222 0', "Set custom keybind for Add Bot", 1, '8 8 0', '1 0.7 0');
					}
					else
					{
						if ((keySelect == 6))
						{
							Sbar_DrawString('-150 222 0', "Set custom keybind for Add Enemy Bot", 1, '8 8 0', '1 0.7 0');
						}
						else
						{
							if ((keySelect == 7))
							{
								Sbar_DrawString('-150 222 0', "Set custom keybind for Remove Bot", 1, '8 8 0', '1 0.7 0');
							}
							else
							{
								if ((keySelect == 8))
								{
									Sbar_DrawString('-150 222 0', "Set custom keybind for offhand grappling hook", 1, '8 8 0', '1 0.7 0');
								}
							}
						}
					}
				}
			}
		}
	}
};

void() disableMouse =
{
	if (menu_was_open)
	{
		menu_was_open = 0;
		if ((mouse > 0))
			cvar_set("sensitivity", ftos(mouse));
	}
};

void() ShowMenu =
{
	if (inMenu)
	{
		menuSetup();
	}
	else
	{
		disableMouse();
	}
	if ((inMenu == 1))
	{
		bindingsMenu();
	}
	if ((bindMode == 1))
	{
		showKeybindOverlay();
	}
	if ((inMenu == 2))
	{
		gameplayMenu();
	}
	if ((inMenu == 3))
	{
		MonMenu();
	}
	if ((inMenu == 5))
	{
		MPMenu();
	}
};








float indexs___;
vector value___;
float __indexg;





