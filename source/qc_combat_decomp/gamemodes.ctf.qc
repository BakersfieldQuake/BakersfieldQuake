//Decompiled code. Please respect the original copyright.

.float ctf_color_side;	// set_team_color: the side whose topcolor/bottomcolor was last stuffed (0 = none yet)

void(string plrname, string msg) broadcast_string =
{
	local entity ent;

	if (((msg != "") && !plrname))
	{
		ent = find(world, classname, "player");
		while ((ent != world))
		{
			if ((ent.ishuman == 1))
			{
				centerprint(ent, msg);
			}
			ent = find(ent, classname, "player");
		}
	}
	else
	{
		ent = find(world, classname, "player");
		while ((ent != world))
		{
			if ((ent.ishuman == 1))
			{
				centerprint(ent, strcat(plrname, " ", msg));
			}
			ent = find(ent, classname, "player");
		}
	}
};

void() enable_ctf =
{
	if ((cvar("deathmatch") == 0))
	{
		cvar_set("deathmatch", "1");
	}
	if ((cvar("ctf") == 1))
	{
		CTF_ENABLED = 1;
	}
	else
	{
		CTF_ENABLED = 0;
	}
};

float(float player_team) checkSwapBalance =
{
	if (autocvar_ctf_autobalance)
	{
		if ((player_team == BLUE))
		{
			if ((RED_PLAYERS >= BLUE_PLAYERS))
			{
				return (0);
			}
			else
			{
				return (TRUE);
			}
		}
		else
		{
			if ((player_team == RED))
			{
				if ((BLUE_PLAYERS >= RED_PLAYERS))
				{
					return (0);
				}
				else
				{
					return (TRUE);
				}
			}
		}
	}
	else
	{
		return (TRUE);
	}
};

void() teamchange_respawn =
{
	self.health = 0;
	if (((random() * 100) < 50))
	{
		self.frame = 93;
	}
	else
	{
		self.frame = 102;
	}
	setmodel(self, "progs/player_id1.mdl");
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	self.deadflag = DEAD_DEAD;
	self.frags = (self.frags + -1);
	respawn();
};

void() swap_team =
{
	if ((self.side == BLUE))
	{
		if ((checkSwapBalance(BLUE) == TRUE))
		{
			self.side = RED;
			BLUE_PLAYERS = BLUE_PLAYERS + -1;
			RED_PLAYERS = RED_PLAYERS + 1;
			centerprint(self, "You are on RED TEAM");
			teamchange_respawn();
		}
		else
		{
			centerprint(self, "Teams are ^3balanced, ^7sorry!");
		}
	}
	else
	{
		if ((checkSwapBalance(RED) == TRUE))
		{
			self.side = BLUE;
			RED_PLAYERS = RED_PLAYERS + -1;
			BLUE_PLAYERS = BLUE_PLAYERS + 1;
			centerprint(self, "You are on BLUE TEAM");
			teamchange_respawn();
		}
		else
		{
			centerprint(self, "Teams are ^3balanced, ^7sorry!");
		}
	}
};

void() set_team_color =
{
	// the colour fields are set every frame (server side, free); the stuffcmds only go out when the side changes.
	// It used to stuff both every 0.1 s and reset .delay, which also starved PlayerPreThink's 0.3 s model refresh
	if ((self.side == RED))
	{
		if ((self.ctf_color_side != RED))
		{
			stuffcmd(self, "topcolor 4\n");
			stuffcmd(self, "bottomcolor 4\n");
			self.ctf_color_side = RED;
		}
		self.b_shirt = 4;
		self.b_pants = 4;
		self.clientcolors = 68;
		self.team = RED;
	}
	else
	{
		if ((self.side == BLUE))
		{
			if ((self.ctf_color_side != BLUE))
			{
				stuffcmd(self, "topcolor 13\n");
				stuffcmd(self, "bottomcolor 13\n");
				self.ctf_color_side = BLUE;
			}
			self.b_shirt = 13;
			self.b_pants = 13;
			self.clientcolors = 221;
			self.team = BLUE;
		}
	}
};

void() choose_team =
{
	if ((BLUE_PLAYERS < RED_PLAYERS))
	{
		self.side = BLUE;
		self.team = BLUE;
		BLUE_PLAYERS = BLUE_PLAYERS + 1;
		if ((self.ishuman == 1))
		{
			centerprint(self, "You are on BLUE TEAM");
		}
	}
	else
	{
		if ((RED_PLAYERS < BLUE_PLAYERS))
		{
			self.side = RED;
			self.team = RED;
			RED_PLAYERS = RED_PLAYERS + 1;
			if ((self.ishuman == 1))
			{
				centerprint(self, "You are on RED TEAM");
			}
		}
		else
		{
			if (((RED_PLAYERS == BLUE_PLAYERS) || !self.side))
			{
				if (((random() * 100) < 50))
				{
					self.side = BLUE;
					self.team = BLUE;
					BLUE_PLAYERS = BLUE_PLAYERS + 1;
					if ((self.ishuman == 1))
					{
						centerprint(self, "You are on BLUE TEAM");
					}
				}
				else
				{
					self.side = RED;
					self.team = RED;
					RED_PLAYERS = RED_PLAYERS + 1;
					if ((self.ishuman == 1))
					{
						centerprint(self, "You are on RED TEAM");
					}
				}
			}
		}
	}
};

void() capture =
{
	local entity flagspawn;

	if ((other.side == BLUE))
	{
		flagspawn = find(world, netname, "red flag");
	}
	else
	{
		flagspawn = find(world, netname, "blue flag");
	}
	setorigin(flagspawn, flagspawn.oldorigin);
	flagspawn.carrier = world;
	if (((other.side == BLUE) && (RED_CAP_COOLDOWN == 0)))
	{
		flagspawn.athome = 1;
		broadcast_string(other.netname, strcat("captured the ^1", flagspawn.netname, "^7!"));
		if (RED_CARRIED)
		{
			BLUE_CAPS = BLUE_CAPS + 1;
		}
		other.frags = (other.frags + 10);
		RED_CARRIED = 0;
		RED_CAP_COOLDOWN = 5;
		other.has_flag = 0;
		sound(flagspawn, CHAN_ITEM, flagspawn.noise1, 1, ATTN_NONE);
	}
	else
	{
		if (((other.side == RED) && (BLUE_CAP_COOLDOWN == 0)))
		{
			flagspawn.athome = 1;
			broadcast_string(other.netname, strcat("captured the ^4", flagspawn.netname, "^7!"));
			if (BLUE_CARRIED)
			{
				RED_CAPS = RED_CAPS + 1;
			}
			other.frags = (other.frags + 10);
			BLUE_CARRIED = 0;
			BLUE_CAP_COOLDOWN = 5;
			other.has_flag = 0;
			sound(flagspawn, CHAN_ITEM, flagspawn.noise1, 1, ATTN_NONE);
		}
	}
	self.nextthink = (time + 0.1);
};

void() flag_run_blue =
{

	if ((self.frame < 25))
	{
		self.frame = (self.frame + 0.5);
	}
	else
	{
		self.frame = 0;
	}
	self.angles = self.oldangles;
	if ((pointcontents((self.origin - '0 0 1')) != CONTENT_SOLID))
	{
		self.origin = (self.origin - '0 0 1');
	}
	if (((world.model == "maps/e1m2.bsp") && self.athome))
	{
		setsize(self, '-16 -16 -14', '16 16 42');
	}
	if (((self.owner.has_flag && (self.owner.items & IT_KEY1)) && (self.owner.health > 0)))
	{
		makevectors(self.owner.angles);
		setorigin(self, (((self.owner.origin + (v_forward * -20)) + (v_right * 5)) + (v_up * -10)));
		self.angles = self.owner.angles;
	}
	else
	{
		if (!self.athome)
		{
			self.carrier = world;
			BLUE_CARRIED = 0;
			if (((pointcontents(self.origin) == CONTENT_LAVA) || (pointcontents(self.origin) == CONTENT_SLIME)))
			{
				flag_return();
			}
			if (((time - self.delay) >= 30))
			{
				flag_return();
				self.delay = time;
			}
		}
	}
	if ((self.athome && (BLUE_CAP_COOLDOWN > 0)))
	{
		BLUE_CAP_COOLDOWN = BLUE_CAP_COOLDOWN + -1;
	}
	self.think = flag_run_blue;
	self.nextthink = (time + 0.03);
};

void() flag_run_red =
{

	if ((self.frame < 25))
	{
		self.frame = (self.frame + 0.5);
	}
	else
	{
		self.frame = 0;
	}
	if ((pointcontents((self.origin - '0 0 1')) != CONTENT_SOLID))
	{
		self.origin = (self.origin - '0 0 1');
	}
	self.angles = self.oldangles;
	if (((self.owner.has_flag && (self.owner.items & IT_KEY2)) && (self.owner.health > 0)))
	{
		makevectors(self.owner.angles);
		setorigin(self, (((self.owner.origin + (v_forward * -20)) + (v_right * 5)) + (v_up * -10)));
		self.angles = self.owner.angles;
	}
	else
	{
		if (!self.athome)
		{
			self.carrier = world;
			RED_CARRIED = 0;
			if (((pointcontents(self.origin) == CONTENT_LAVA) || (pointcontents(self.origin) == CONTENT_SLIME)))
			{
				flag_return();
			}
			if (((time - self.delay) >= 30))
			{
				flag_return();
				self.delay = time;
			}
		}
	}
	if ((self.athome && (RED_CAP_COOLDOWN > 0)))
	{
		RED_CAP_COOLDOWN = RED_CAP_COOLDOWN + -1;
	}
	self.think = flag_run_red;
	self.nextthink = (time + 0.03);
};

void() flag_return =
{
	if ((self.carrier != world))
	{
		return;
	}
	if ((self.owner.has_flag == 1))
	{
		return;
	}
	if ((self.athome == 0))
	{
		self.athome = 1;
	}
	if ((self.origin == self.oldorigin))
	{
		return;
	}
	setorigin(self, self.oldorigin);
	if ((self.netname == "blue flag"))
	{
		if (!BLUE_CAP_COOLDOWN)
		{
			self.think = flag_run_blue;
			BLUE_CARRIED = 0;
			broadcast_string("", strcat("^4", self.netname, "^7 has been returned!"));
			self.touch = flag_touch_blue;
			sound(self, CHAN_AUTO, self.noise, 1, ATTN_NONE);
		}
	}
	else
	{
		if (!RED_CAP_COOLDOWN)
		{
			self.think = flag_run_red;
			RED_CARRIED = 0;
			broadcast_string("", strcat("^1", self.netname, "^7 has been returned!"));
			self.touch = flag_touch_red;
			sound(self, CHAN_AUTO, self.noise, 1, ATTN_NONE);
		}
	}
	self.nextthink = (time + 0.1);
};

void() flag_touch_blue =
{
	if ((self.carrier != world))
	{
		return;
	}
	if ((other.classname != "player"))
	{
		return;
	}
	if ((((((self.origin != self.oldorigin) && (other.side == BLUE)) && (self.athome == 0)) && !self.owner.has_flag) && !BLUE_CARRIED))
	{
		if ((self.carrier != other))
		{
			self.think = flag_return;
			self.nextthink = (time + 0.1);
		}
	}
	if (((other.side == BLUE) && !other.has_flag))
	{
		return;
	}
	if (((other.side == RED) && (other.classname == "player")))
	{
		self.owner = other;
	}
	if (((other.team == BLUE) && (other.ishuman != 1)))
	{
		other.bot_flagrunner = 1;
	}
	if (((((!other.has_flag && (other.health > 0)) && (other.side != self.side)) && !BLUE_CARRIED) || (((other.ishuman != 1) && !BLUE_CARRIED) && (other.team != self.side))))
	{
		self.athome = 0;
		other.items = (other.items + IT_KEY1);
		self.carrier = other;
		stuffcmd(other, "bf\n");
		other.has_flag = 1;
		if ((BLUE_CAP_COOLDOWN == 0))
		{
			broadcast_string(other.netname, strcat("stole the ^4", self.netname, "^7!"));
			sound(self, CHAN_ITEM, self.noise2, 1, ATTN_NONE);
		}
		BLUE_CARRIED = 1;
	}
	else
	{
		if (((other.has_flag && (other.side == BLUE)) && (self.athome == 1)))
		{
			self.nextthink = (time + 0.1);
			capture();
			other.items = (other.items - IT_KEY2);
			other.has_flag = 0;
		}
	}
};

void() flag_touch_red =
{
	if ((self.carrier != world))
	{
		return;
	}
	if ((other.classname != "player"))
	{
		return;
	}
	if ((((((self.origin != self.oldorigin) && ((other.side == RED) && (other.ishuman == 1))) && (self.athome == 0)) && !self.owner.has_flag) && !RED_CARRIED))
	{
		if ((self.carrier != other))
		{
			self.think = flag_return;
			self.nextthink = (time + 0.1);
		}
	}
	if (((other.side == RED) && !other.has_flag))
	{
		return;
	}
	if (((other.side == BLUE) && (other.classname == "player")))
	{
		self.owner = other;
	}
	if (((other.team == BLUE) && (other.ishuman != 1)))
	{
		other.bot_flagrunner = 1;
	}
	if (((((!other.has_flag && (other.health > 0)) && (other.side != self.side)) && !RED_CARRIED) || (((other.ishuman != 1) && !RED_CARRIED) && (other.team != self.side))))
	{
		self.athome = 0;
		other.items = (other.items + IT_KEY2);
		self.carrier = other;
		stuffcmd(other, "bf\n");
		other.has_flag = 1;
		if ((RED_CAP_COOLDOWN == 0))
		{
			broadcast_string(other.netname, strcat("stole the ^1", self.netname, "^7!"));
			sound(self, CHAN_ITEM, self.noise2, 1, ATTN_NONE);
		}
		RED_CARRIED = 1;
	}
	else
	{
		if (((other.has_flag && (other.side == RED)) && (self.athome == 1)))
		{
			self.nextthink = (time + 0.1);
			capture();
			other.items = (other.items - IT_KEY1);
			other.has_flag = 0;
		}
	}
};

void() CTF_Precache =
{
	precache_sound("doors/runetry.wav");
	precache_sound("ctf/flag/flagcap.wav");
	precache_sound("ctf/flag/flagtk.wav");
	precache_model("progs/flag.mdl");
};

void() item_flagblue =
{
	FLAG_COUNT = FLAG_COUNT + 1;
	if ((FLAG_COUNT > 2))
	{
		remove(self);
	}
	CTF_Precache();
	self.touch = flag_touch_blue;
	self.items = IT_KEY1;
	self.oldorigin = self.origin;
	self.netname = "blue flag";
	setmodel(self, "progs/flag.mdl");
	self.side = BLUE;
	self.oldangles = self.angles;
	self.scale = 1.3;
	self.noise = "doors/runetry.wav";
	self.noise1 = "ctf/flag/flagcap.wav";
	self.noise2 = "ctf/flag/flagtk.wav";
	self.effects = 4194816;
	self.solid = SOLID_TRIGGER;
	self.movetype = MOVETYPE_STEP;
	if ((world.model == "maps/e1m2.bsp"))
	{
		setorigin(self, (self.origin + '0 0 20'));
		setsize(self, '-16 -16 -14', '16 16 42');
	}
	self.traileffectnum = particleeffectnum(/*14129i*/"blue_flag");
	self.athome = 1;
	self.think = flag_run_blue;
	self.nextthink = time;
};

void() item_flagred =
{
	FLAG_COUNT = FLAG_COUNT + 1;
	if ((FLAG_COUNT > 2))
	{
		remove(self);
	}
	CTF_Precache();
	self.touch = flag_touch_red;
	self.items = IT_KEY2;
	self.oldorigin = self.origin;
	self.netname = "red flag";
	setmodel(self, "progs/flag.mdl");
	self.skin = 1;
	self.side = RED;
	self.oldangles = self.angles;
	self.scale = 1.3;
	self.noise = "doors/runetry.wav";
	self.noise1 = "ctf/flag/flagcap.wav";
	self.noise2 = "ctf/flag/flagtk.wav";
	self.solid = SOLID_TRIGGER;
	self.movetype = MOVETYPE_STEP;
	setsize(self, VEC_HULL_MIN, '16 16 42');
	self.effects = 4194816;
	self.traileffectnum = particleeffectnum(/*14139i*/"red_flag");
	self.athome = 1;
	self.think = flag_run_red;
	self.nextthink = time;
};

vector(vector org) createspawn =
{
	local vector orgf;
	local vector orgb;
	local vector orgl;
	local vector orgr;

	makevectors(self.angles);
	orgf = org + (v_forward * 400);
	orgb = VEC_ORIGIN - orgf;
	orgr = org + (v_right * 400);
	orgl = VEC_ORIGIN - orgr;
	if ((pointcontents(orgf) != CONTENT_SOLID))
	{
		return (orgf);
	}
	else
	{
		if ((pointcontents(orgb) != CONTENT_SOLID))
		{
			return (orgb);
		}
		else
		{
			if ((pointcontents(orgr) != CONTENT_SOLID))
			{
				return (orgr);
			}
			else
			{
				if ((pointcontents(orgl) != CONTENT_SOLID))
				{
					return (orgl);
				}
				else
				{
					return (org);
				}
			}
		}
	}
};

void(vector spawnorg) makeTeamSpawns =
{
	local entity spawnblue;
	local entity spawnred;
	local entity findstart;
	local vector distance;

	if ((self.classname == "info_player_start"))
	{
		findstart = spawn();
		findstart = find(world, classname, "info_player_deathmatch");
		distance = self.origin - findstart.origin;
		if (!findstart)
		{
			findstart = find(world, classname, "path_corner");
		}
		distance = self.origin - findstart.origin;
		if ((findstart && (vlen(distance) < 2700)))
		{
			print(strcat("converting ", findstart.classname, " to red spawn\n\n"));
			spawnred = spawn();
			spawnred.origin = findstart.origin;
			spawnred.think = info_player_team1;
			spawnred.nextthink = time;
		}
		else
		{
			spawnred = spawn();
			spawnred.origin = createspawn(spawnorg);
			spawnred.think = info_player_team1;
			spawnred.nextthink = time;
		}
	}
	else
	{
		if ((self.classname == "trigger_changelevel"))
		{
			findstart = find(world, classname, "info_player_deathmatch");
			distance = self.origin - findstart.origin;
			if (!findstart)
			{
				findstart = find(world, classname, "path_corner");
			}
			distance = self.origin - findstart.origin;
			if ((findstart && (vlen(distance) < 2700)))
			{
				print(strcat("converting ", findstart.classname, " to blue spawn\n\n"));
				spawnblue = spawn();
				spawnblue.origin = findstart.origin;
				spawnblue.think = info_player_team2;
				spawnblue.nextthink = time;
			}
			else
			{
				spawnblue = spawn();
				spawnblue.origin = createspawn(spawnorg);
				spawnblue.think = info_player_team2;
				spawnblue.nextthink = time;
			}
		}
	}
	remove(self);
};

void(vector loc) ctf_replacer =
{
	local entity findred;
	local entity replacerred;
	local entity replacerblue;

	if ((self.classname == "info_player_start"))
	{
		findred = find(world, netname, "red flag");
		if (!findred)
		{
			replacerred = spawn();
			replacerred.origin = loc;
			replacerred.think = item_flagred;
			replacerred.nextthink = time;
			makeTeamSpawns(replacerred.origin);
		}
	}
	else
	{
		if ((self.classname == "trigger_changelevel"))
		{
			replacerblue = spawn();
			replacerblue.origin = loc;
			replacerblue.think = item_flagblue;
			replacerblue.nextthink = time;
			makeTeamSpawns(replacerblue.origin);
		}
	}
};

void() item_flag_team1 =
{
	if ((world.model == "maps/ctf8.bsp"))
	{
		self.origin = (self.origin + '0 0 16');
	}
	item_flagred();
};

void() item_flag_team2 =
{
	if ((world.model == "maps/ctf8.bsp"))
	{
		self.origin = (self.origin + '0 0 16');
	}
	item_flagblue();
};

void() info_player_team1 =
{
	self.side = RED;
	self.netname = "red start";
};

void() info_player_team2 =
{
	self.side = BLUE;
	self.netname = "blue start";
};
