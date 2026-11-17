//Decompiled code. Please respect the original copyright.

float bm_way_loading;	// TRUE while a .way file is being exec'd into saved1-4 (WaypointWatch)

void() bot_map_load =
{
	if ((mapname == "dm1"))
	{
		map_dm1();
	}
	else
	{
		if ((mapname == "dm2"))
		{
			map_dm2();
		}
		else
		{
			if ((mapname == "dm3"))
			{
				map_dm3();
			}
			else
			{
				if ((mapname == "dm4"))
				{
					map_dm4();
				}
				else
				{
					if ((mapname == "dm5"))
					{
						map_dm5();
					}
					else
					{
						if ((mapname == "dm6"))
						{
							map_dm6();
						}
						else
						{
							if ((mapname == "ctf8"))
							{
								map_ctf8();
							}
							else
							{
								BM_MapLoad();
							}
						}
					}
				}
			}
		}
	}
};
void (entity e, float chan, string samp, float vol, float atten) frik_sound = #8; 
void (entity client, string s) frik_stuffcmd = #21; 
void (...) frik_sprint = #24; 
vector (entity e, float speed) frik_aim = #44; 
void (entity client, string s, ...) frik_centerprint = #73; 
void (entity e) frik_setspawnparms = #78; 
void (float to, float f) frik_WriteByte = #52; 
void (float to, float f) frik_WriteChar = #53; 
void (float to, float f) frik_WriteShort = #54; 
void (float to, float f) frik_WriteLong = #55; 
void (float to, float f) frik_WriteCoord = #56; 
void (float to, float f) frik_WriteAngle = #57; 
void (float to, string s) frik_WriteString = #58; 
void (float to, entity s) frik_WriteEntity = #59; 
void (entity client, string s, ...) frik_big_centerprint = #73; 

void(entity client, string s) stuffcmd =
{
	if ((client.ishuman == 1))
	{
		frik_stuffcmd(client, s);
	}
	b_temp1 = player_head;
	while (b_temp1)
	{
		if ((b_temp1.classname == "botcam"))
		{
			if (((b_temp1.enemy == client) && b_temp1.ishuman))
			{
				frik_stuffcmd(b_temp1, s);
			}
		}
		b_temp1 = b_temp1._next;
	}
};

void(entity e) setspawnparms =
{
	if ((e.ishuman == 1))
	{
		frik_setspawnparms(e);
	}
	else
	{
		b_temp1 = player_head;
		while (b_temp1)
		{
			if (b_temp1.ishuman)
			{
				frik_setspawnparms(b_temp1);
				return;
			}
			b_temp1 = b_temp1._next;
		}
		SetNewParms();
	}
};

void(entity client, string s) sprint =
{
	if ((client.ishuman == 1))
	{
		frik_sprint(client, s);
	}
	b_temp1 = player_head;
	while (b_temp1)
	{
		if ((b_temp1.classname == "botcam"))
		{
			if (((b_temp1.enemy == client) && b_temp1.ishuman))
			{
				frik_sprint(b_temp1, s);
			}
		}
		b_temp1 = b_temp1._next;
	}
};

void(entity client, string s) centerprint =
{
	if ((client.ishuman == 1))
	{
		frik_centerprint(client, s);
	}
	b_temp1 = player_head;
	while (b_temp1)
	{
		if ((b_temp1.classname == "botcam"))
		{
			if (((b_temp1.enemy == client) && b_temp1.ishuman))
			{
				frik_centerprint(b_temp1, s);
			}
		}
		b_temp1 = b_temp1._next;
	}
};

void(entity e, float sped) aim =
{
	e.missile_speed = sped;
	return (frik_aim(e, sped));
};

void(entity e, float chan, string samp, float vol, float atten) sound =
{
	frik_sound(e, chan, samp, vol, atten);
	if ((samp == "items/inv3.wav"))
	{
		return;
	}
	else
	{
		if ((e.classname == "player"))
		{
			e.b_sound = (time + 1);
		}
		else
		{
			if ((other.classname == "player"))
			{
				other.b_sound = (time + 1);
			}
		}
	}
};

void(float to, float f) WriteByte =
{
	if (((to == MSG_ONE) && (msg_entity.ishuman != TRUE)))
	{
		return;
	}
	frik_WriteByte(to, f);
};

void(float to, float f) WriteChar =
{
	if (((to == MSG_ONE) && (msg_entity.ishuman != TRUE)))
	{
		return;
	}
	frik_WriteChar(to, f);
};

void(float to, float f) WriteShort =
{
	if (((to == MSG_ONE) && (msg_entity.ishuman != TRUE)))
	{
		return;
	}
	frik_WriteShort(to, f);
};

void(float to, float f) WriteLong =
{
	if (((to == MSG_ONE) && (msg_entity.ishuman != TRUE)))
	{
		return;
	}
	frik_WriteLong(to, f);
};

void(float to, float f) WriteCoord =
{
	if (((to == MSG_ONE) && (msg_entity.ishuman != TRUE)))
	{
		return;
	}
	frik_WriteCoord(to, f);
};

void(float to, float f) WriteAngle =
{
	if (((to == MSG_ONE) && (msg_entity.ishuman != TRUE)))
	{
		return;
	}
	frik_WriteAngle(to, f);
};

void(float to, string s) WriteString =
{
	if (((to == MSG_ONE) && (msg_entity.ishuman != TRUE)))
	{
		return;
	}
	frik_WriteString(to, s);
};

void(float to, entity s) WriteEntity =
{
	if (((to == MSG_ONE) && (msg_entity.ishuman != TRUE)))
	{
		return;
	}
	frik_WriteEntity(to, s);
};

float() botcam =
{
	if ((self.classname != "botcam"))
	{
		return (0);
	}
	setorigin(self, self.enemy.origin);
	self.items = self.enemy.items;
	self.weapon = self.enemy.weapon;
	self.weaponmodel = self.enemy.weaponmodel;
	self.currentammo = self.enemy.currentammo;
	self.weaponframe = self.enemy.weaponframe;
	self.ammo_shells = self.enemy.ammo_shells;
	self.ammo_nails = self.enemy.ammo_nails;
	self.ammo_rockets = self.enemy.ammo_rockets;
	self.ammo_cells = self.enemy.ammo_cells;
	self.view_ofs = self.enemy.view_ofs;
	self.health = self.enemy.health;
	self.armorvalue = self.enemy.armorvalue;
	self.dmg_take = self.enemy.dmg_take;
	self.dmg_save = self.enemy.dmg_save;
	self.dmg_inflictor = self.enemy.dmg_inflictor;
	self.punchangle = self.enemy.punchangle;
	self.deadflag = self.enemy.deadflag;
	msg_entity = self;
	WriteByte(MSG_ONE, 5);
	WriteEntity(MSG_ONE, self.enemy);
	WriteByte(MSG_ONE, 10);
	WriteAngle(MSG_ONE, self.enemy.v_angle_x);
	WriteAngle(MSG_ONE, self.enemy.v_angle_y);
	WriteAngle(MSG_ONE, self.enemy.v_angle_z);
	self.modelindex = 0;
	self.impulse = 0;
	return (TRUE);
};

void() botcam_u =
{
	if ((self.classname != "botcam"))
	{
		self.enemy = player_head;
	}
	else
	{
		do
		{
			self.enemy = self.enemy._next;

		} while ((self.enemy.classname == "botcam"));
	}
	if ((self.enemy == self))
	{
		do
		{
			self.enemy = self.enemy._next;

		} while ((self.enemy.classname == "botcam"));
	}
	self.classname = "botcam";
	self.solid = 0;
	self.movetype = 0;
	self.takedamage = 0;
	if (!self.enemy)
	{
		sprint(self, "No one left to track!\n");
		msg_entity = self;
		WriteByte(MSG_ONE, 5);
		WriteEntity(MSG_ONE, self);
		PutClientInServer();
		return;
	}
	if (!self.enemy.ishuman)
	{
		self.enemy.dmg_take = 0;
		self.enemy.dmg_save = 0;
	}
	sprint(self, "Now tracking ");
	sprint(self, self.enemy.netname);
	sprint(self, "\n");
};

void() ClientFixRankings =
{
	local float cno;

	if ((self.switch_wallhug > time))
	{
		return;
	}
	self.switch_wallhug = 0;
	b_temp2 = nextent(world);
	cno = 0;
	while ((cno < max_clients))
	{
		if ((!b_temp2.ishuman && (active_clients & ClientBitFlag(cno))))
		{
			UpdateClient(b_temp2);
		}
		cno = cno + 1;
		b_temp2 = nextent(b_temp2);
	}
};

void() ClientInRankings =
{
	local float cno, n, inlist;
	local entity e, prev, succ;

	cno = self.colormap - 1;
	BotInvalidClientNo(cno);
	// A joining human gets the lowest free engine slot, and a FrikBot (fake client) there counts as free.
	// DP clears the edict before ClientConnect, so BotInvalidClientNo never sees the bot and it stays
	// linked; linking self again would close player_head into a ring that the print wrappers loop on forever.
	// Unlink it (its own _next was wiped: the successor is whoever still points back at it).
	inlist = FALSE;
	prev = world;
	e = player_head;
	n = 0;
	while (e != world && n <= max_clients)
	{
		if (e == self)
		{
			inlist = TRUE;
			break;
		}
		prev = e;
		e = e._next;
		n = n + 1;
	}
	if (inlist)
	{
		succ = world;
		e = nextent(world);
		n = 0;
		while (n < max_clients)
		{
			if (e != self && e._last == self && e.classname != "")
			{
				succ = e;
			}
			e = nextent(e);
			n = n + 1;
		}
		if (prev != world)
		{
			prev._next = succ;
		}
		else
		{
			player_head = succ;
		}
		if (succ != world)
		{
			succ._last = prev;
		}
		if (self.ishuman != 2)
		{
			// a human took over a bot's slot: recount the bots that are still linked
			bot_count = 0;
			current_bots = 0;
			e = player_head;
			n = 0;
			while (e != world && n <= max_clients)
			{
				if (!e.ishuman && e.b_clientno != -1)
				{
					bot_count = bot_count + 1;
					if (e.b_num > 0)
					{
						current_bots = current_bots | ClientBitFlag((e.b_num - 1));
					}
				}
				e = e._next;
				n = n + 1;
			}
			cvar_set("scratch1", ftos(current_bots));
		}
	}
	if (player_head)
	{
		player_head._last = self;
	}
	self._next = player_head;
	self._last = world;
	player_head = self;
	if (!self.phys_obj)
	{
		b_temp2 = phys_head;
		while (((b_temp2 != world) && (b_temp2.owner != self)))
		{
			b_temp2 = b_temp2._next;
		}
		self.phys_obj = b_temp2;
	}
	if ((self.ishuman == 2))
	{
		self.ishuman = 0;
		return;
	}
	active_clients = active_clients | ClientBitFlag(cno);
	self.b_clientno = cno;
	self.ishuman = TRUE;
	self.switch_wallhug = (time + 1);
};

void() ClientDisconnected =
{
	if ((player_head == self))
	{
		player_head = self._next;
	}
	if (self._next)
	{
		self._next._last = self._last;
	}
	if (self._last)
	{
		self._last._next = self._next;
	}
	active_clients = active_clients - (active_clients & ClientBitFlag(self.b_clientno));
};

float() BotPreFrame =
{
	if ((self.b_clientno == -1))
	{
		return (TRUE);
	}
	if (self.ishuman)
	{
		if (self.switch_wallhug)
		{
			ClientFixRankings();
		}
		if ((self.classname == "botcam"))
		{
			return (TRUE);
		}
	}
	if ((self.b_frags != self.frags))
	{
		if ((self.b_frags > self.frags))
		{
			if ((pointcontents(self.origin) == CONTENT_LAVA))
			{
				bot_start_topic(10);
			}
			else
			{
				bot_start_topic(9);
			}
		}
		else
		{
			bot_start_topic(2);
		}
		self.b_frags = self.frags;
	}
	if (CTF_ENABLED)
	{
		set_team_color();
	}
	DynamicWaypoint();
	return (0);
};

float() BotPostFrame =
{
	if ((self.b_clientno == -1))
	{
		return (TRUE);
	}
	if (self.ishuman)
	{
		if ((waypoint_mode > WM_LOADED))
		{
			bot_menu_display();
		}
		BotImpulses();
		if (botcam())
		{
			return (TRUE);
		}
	}
	return (0);
};

void(string h) BotSay =
{
	WriteByte(MSG_ALL, 8);
	WriteByte(MSG_ALL, 1);
	WriteString(MSG_ALL, self.netname);
	WriteByte(MSG_ALL, 8);
	WriteByte(MSG_ALL, 2);
	WriteString(MSG_ALL, h);
};

void() BotSayInit =
{
	WriteByte(MSG_ALL, 8);
	WriteByte(MSG_ALL, 1);
	WriteString(MSG_ALL, self.netname);
};

void(string h) BotSay2 =
{
	WriteByte(MSG_ALL, 8);
	WriteByte(MSG_ALL, 2);
	WriteString(MSG_ALL, h);
};

void(string h) BotSayTeam =
{
	local entity t;

	if (!teamplay)
	{
		return;
	}
	t = player_head;
	while (t)
	{
		if ((t.team == self.team))
		{
			msg_entity = t;
			WriteByte(MSG_ONE, 8);
			WriteByte(MSG_ONE, 1);
			WriteByte(MSG_ONE, 40);
			WriteString(MSG_ONE, self.netname);
			WriteByte(MSG_ONE, 8);
			WriteByte(MSG_ONE, 2);
			WriteByte(MSG_ONE, 41);
			WriteString(MSG_ONE, h);
		}
		t = t._next;
	}
};

void() BotInit =
{
	local entity ent;
	local entity fisent;
	local float numents;

	ent = nextent(world);
	max_clients = 0;
	while ((ent != world))
	{
		max_clients = max_clients + 1;
		ent = nextent(ent);
	}
	if ((max_clients > 16))
	{
		max_clients = 16;
	}
	ent = nextent(world);
	fisent = world;
	while ((numents < max_clients))
	{
		phys_head = spawn();
		if (fisent)
		{
			fisent._next = phys_head;
		}
		phys_head._last = fisent;
		fisent = phys_head;
		ent.phys_obj = phys_head;
		phys_head.classname = "phys_obj";
		phys_head.owner = ent;
		numents = numents + 1;
		ent = nextent(ent);
	}
	precache_model("progs/s_light.spr");
	precache_model("progs/s_bubble.spr");
};

void(entity who) UpdateClient =
{
	WriteByte(MSG_ALL, SVC_UPDATENAME);
	WriteByte(MSG_ALL, who.b_clientno);
	WriteString(MSG_ALL, who.netname);
	WriteByte(MSG_ALL, SVC_UPDATECOLORS);
	WriteByte(MSG_ALL, who.b_clientno);
	WriteByte(MSG_ALL, ((who.b_shirt * 16) + who.b_pants));
	WriteByte(MSG_ALL, SVC_UPDATEFRAGS);
	WriteByte(MSG_ALL, who.b_clientno);
	WriteShort(MSG_ALL, who.frags);
};

float(float clientno) ClientBitFlag =
{
	if ((clientno == 0))
	{
		return (1);
	}
	else
	{
		if ((clientno == 1))
		{
			return (2);
		}
		else
		{
			if ((clientno == 2))
			{
				return (4);
			}
			else
			{
				if ((clientno == 3))
				{
					return (8);
				}
				else
				{
					if ((clientno == 4))
					{
						return (16);
					}
					else
					{
						if ((clientno == 5))
						{
							return (32);
						}
						else
						{
							if ((clientno == 6))
							{
								return (64);
							}
							else
							{
								if ((clientno == 7))
								{
									return (128);
								}
								else
								{
									if ((clientno == 8))
									{
										return (256);
									}
									else
									{
										if ((clientno == 9))
										{
											return (512);
										}
										else
										{
											if ((clientno == 10))
											{
												return (1024);
											}
											else
											{
												if ((clientno == 11))
												{
													return (2048);
												}
												else
												{
													if ((clientno == 12))
													{
														return (4096);
													}
													else
													{
														if ((clientno == 13))
														{
															return (8192);
														}
														else
														{
															if ((clientno == 14))
															{
																return (16384);
															}
															else
															{
																if ((clientno == 15))
																{
																	return (32768);
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
	return (0);
};

float() ClientNextAvailable =
{
	local float clientno;

	clientno = max_clients;
	while ((clientno > 0))
	{
		clientno = clientno - 1;
		if (!(active_clients & ClientBitFlag(clientno)))
		{
			return (clientno);
		}
	}
	return (-1);
};

void(entity e1, entity e2, float flag) DeveloperLightning =
{
	WriteByte(MSG_BROADCAST, 23);
	if (flag)
	{
		WriteByte(MSG_BROADCAST, 6);
	}
	else
	{
		WriteByte(MSG_BROADCAST, 13);
	}
	WriteEntity(MSG_BROADCAST, e2);
	WriteCoord(MSG_BROADCAST, e1.origin_x);
	WriteCoord(MSG_BROADCAST, e1.origin_y);
	WriteCoord(MSG_BROADCAST, e1.origin_z);
	WriteCoord(MSG_BROADCAST, e2.origin_x);
	WriteCoord(MSG_BROADCAST, e2.origin_y);
	WriteCoord(MSG_BROADCAST, e2.origin_z);
};

float(float tcolor) FindAnotherColor =
{
	local float bestbet;
	local float scolor;
	local float pcount;
	local float bestp;

	bestbet = -1;
	bestp = 16;
	while ((scolor < 14))
	{
		if ((scolor != tcolor))
		{
			b_temp2 = player_head;
			pcount = 0;
			while ((b_temp2 != world))
			{
				if ((b_temp2.team == (scolor + 1)))
				{
					pcount = pcount + 1;
				}
				b_temp2 = b_temp2._next;
			}
			if (((pcount < bestp) && pcount))
			{
				bestbet = scolor;
				bestp = pcount;
			}
		}
		scolor = scolor + 1;
	}
	if ((bestbet < 0))
	{
		bestbet = tcolor;
		while ((bestbet == tcolor))
		{
			bestbet = floor((random() * 13));
		}
	}
	return (bestbet);
};

entity(float num) GetClientEntity =
{
	local entity upsy;

	upsy = world;
	num = num + 1;
	while ((num > 0))
	{
		num = num - 1;
		upsy = nextent(upsy);
	}
	return (upsy);
};

void(float whichteam, float whatbot, float whatskill) BotConnect =
{
	local float f;
	local string h;
	local entity uself;
	local entity teamspawn;

	f = ClientNextAvailable();
	uself = self;
	if ((f == -1))
	{
		bprint("Unable to connect a bot, server is full.\n");
		return;
	}
	bot_count = bot_count + 1;
	self = GetClientEntity(f);
	if (!saved_bots)
	{
		bot_start_topic(1);
	}
	self.b_clientno = f;
	if (!CTF_ENABLED)
	{
		self.colormap = (f + 1);
	}
	if (whatbot)
	{
		self.netname = BotName(whatbot);
	}
	else
	{
		self.netname = PickARandomName();
	}
	if (CTF_ENABLED)
	{
		self.bot_flagrunner = 1;
	}
	whatskill = rint(whatskill);
	if ((whatskill > 3))
	{
		whatskill = 3;
	}
	else
	{
		if ((whatskill < 0))
		{
			whatskill = 0;
		}
	}
	if (autocvar_bm_bot_easy)
	{
		whatskill = 2;
	}
	self.b_skill = whatskill;
	if (((teamplay && !coop) && !CTF_ENABLED))
	{
		if (whichteam)
		{
			self.b_pants = FindAnotherColor((uself.team - 1));
		}
		else
		{
			self.b_pants = (uself.team - 1);
		}
	}
	else
	{
		defineflags_ctf();
	}
	if (!CTF_ENABLED)
	{
		self.team = (self.b_pants + 1);
	}
	UpdateClient(self);
	SetNewParms();
	self.ishuman = 2;
	ClientConnect();
	PutClientInServer();
	active_clients = active_clients | ClientBitFlag(f);
	BM_BotConnected(uself);
	f = ClientBitFlag((self.b_num - 1));
	current_bots = current_bots | f;
	if ((self.b_num <= 8))
	{
		saved_skills1 = (saved_skills1 & (65536 - (3 * f))) | (self.b_skill * f);
	}
	else
	{
		f = ClientBitFlag((self.b_num - 9));
		saved_skills2 = (saved_skills2 & (65536 - (3 * f))) | (self.b_skill * f);
	}
	h = ftos(current_bots);
	cvar_set("scratch1", h);
	h = ftos(saved_skills1);
	cvar_set("scratch2", h);
	h = ftos(saved_skills2);
	cvar_set("scratch3", h);
	self = uself;
	if ((CTF_ENABLED && (self.ishuman != 1)))
	{
		choose_team();
		if ((self.side == RED))
		{
			teamspawn = find(world, netname, "red start");
		}
		else
		{
			teamspawn = find(world, netname, "blue start");
		}
		self.origin = teamspawn.origin;
	}
};

void(entity bot) BotDisconnect =
{
	local string h;
	local entity uself;

	uself = self;
	self = bot;
	bot_count = bot_count - 1;
	current_bots = current_bots - (current_bots & ClientBitFlag((self.b_num - 1)));
	h = ftos(current_bots);
	cvar_set("scratch1", h);
	ClientDisconnect();
	if ((self.b_clientno != -1))
	{
		self.frags = 0;
		self.b_frags = 0;
		self.netname = "";
		self.classname = "";
		self.health = 0;
		self.items = 0;
		self.armorvalue = 0;
		self.weaponmodel = "";
		self.b_pants = 0;
		self.b_shirt = 0;
		self.ammo_cells = 0;
		self.ammo_rockets = 0;
		self.ammo_nails = 0;
		self.ammo_shells = 0;
		UpdateClient(self);
		active_clients = active_clients - (active_clients & ClientBitFlag(self.b_clientno));
		self.b_clientno = -1;
	}
	self = uself;
};

void(float clientno) BotInvalidClientNo =
{
	local entity bot;

	bot = GetClientEntity(clientno);
	if ((bot.b_clientno > 0))
	{
		if ((active_clients & ClientBitFlag(self.b_clientno)))
		{
			bot.b_clientno = -1;
			BotDisconnect(bot);
			active_clients = active_clients | ClientBitFlag(self.b_clientno);
			BotConnect(0, bot.b_num, bot.b_skill);
			return;
		}
	}
};

void() LoadWaypoint =
{
	local vector org;
	local entity tep;
	local float r;

	org_x = cvar("saved1");
	org_y = cvar("saved2");
	org_z = cvar("saved3");
	tep = make_waypoint(org);
	r = cvar("saved4");
	tep.b_aiflags = floor((r / 4));
	tep.b_pants = cvar("scratch1");
	tep.b_skill = cvar("scratch2");
	tep.b_shirt = cvar("scratch3");
	tep.b_frags = cvar("scratch4");
};

void() bot_return =
{
	if ((time > 2))
	{
		if (((waypoint_mode == WM_DYNAMIC) || (waypoint_mode == WM_LOADED)))
		{
			if ((saved_bots & 1))
			{
				BotConnect(0, 1, (saved_skills1 & 3));
			}
			if ((saved_bots & 2))
			{
				BotConnect(0, 2, ((saved_skills1 & 12) / 4));
			}
			if ((saved_bots & 4))
			{
				BotConnect(0, 3, ((saved_skills1 & 48) / 16));
			}
			if ((saved_bots & 8))
			{
				BotConnect(0, 4, ((saved_skills1 & 192) / 64));
			}
			if ((saved_bots & 16))
			{
				BotConnect(0, 5, ((saved_skills1 & 768) / 256));
			}
			if ((saved_bots & 32))
			{
				BotConnect(0, 6, ((saved_skills1 & 3072) / 1024));
			}
			if ((saved_bots & 64))
			{
				BotConnect(0, 7, ((saved_skills1 & 12288) / 4096));
			}
			if ((saved_bots & 128))
			{
				BotConnect(0, 8, ((saved_skills1 & 49152) / 16384));
			}
			if ((saved_bots & 256))
			{
				BotConnect(0, 9, (saved_skills2 & 3));
			}
			if ((saved_bots & 512))
			{
				BotConnect(0, 10, ((saved_skills2 & 12) / 4));
			}
			if ((saved_bots & 1024))
			{
				BotConnect(0, 11, ((saved_skills2 & 48) / 16));
			}
			if ((saved_bots & 2048))
			{
				BotConnect(0, 12, ((saved_skills2 & 192) / 64));
			}
			if ((saved_bots & 4096))
			{
				BotConnect(0, 13, ((saved_skills2 & 768) / 256));
			}
			if ((saved_bots & 8192))
			{
				BotConnect(0, 14, ((saved_skills2 & 3072) / 1024));
			}
			if ((saved_bots & 16384))
			{
				BotConnect(0, 15, ((saved_skills2 & 12288) / 4096));
			}
			if ((saved_bots & 32768))
			{
				BotConnect(0, 16, ((saved_skills2 & 49152) / 16384));
			}
			saved_bots = 0;
		}
	}
};

void() WaypointWatch =
{
	local float bigboobs;
	local string h;

	if ((framecount < 4))
	{
		return;
	}
	if ((max_clients < 2))
	{
		return;
	}
	if ((waypoint_mode != WM_UNINIT))
	{
		bigboobs = cvar("saved4");
		// saved4 is shared with the CSQC stopspeed setting (100/150/200, archived; CSQC_Init and the menu write it on
		// a listen server). Only a .way file being exec'd may drive the loader: it starts with a clear line (&3 == 1),
		// then waypoints (&3 == 2), and ends with 3. Anything else, or outside a load, is left alone: it made a junk
		// waypoint and left waypoint_mode stuck at WM_LOADING, where bots with a failed route stand still.
		if (((bigboobs & 3) == 1))
		{
			bm_way_loading = TRUE;
		}
		if ((bigboobs != 0) && (bigboobs & 3) && bm_way_loading)
		{
			if (((bigboobs & 3) == 1))
			{
				ClearAllWays();
			}
			else
			{
				if (((bigboobs & 3) == 3))
				{
					FixWaypoints();
					h = ftos(b_options);
					cvar_set("saved1", h);
					cvar_set("saved4", "0");
					cvar_set("scratch1", "0");
					waypoint_mode = WM_LOADED;
					bm_way_loading = FALSE;
					return;
				}
			}
			LoadWaypoint();
			waypoint_mode = WM_LOADING;
			cvar_set("saved4", "0");
		}
	}
	else
	{
		b_options = cvar("saved1");
		if ((coop || (b_options & OPT_SAVEBOTS)))
		{
			saved_bots = cvar("scratch1");
			saved_skills1 = cvar("scratch2");
			saved_skills2 = cvar("scratch3");
		}
		// clear only a stale loader start/end value: keep the player's stopspeed setting (100/150/200) in saved4
		bigboobs = cvar("saved4");
		if ((((bigboobs & 3) == 1) || ((bigboobs & 3) == 3)))
		{
			cvar_set("saved4", "0");
		}
		if ((max_clients > 1))
		{
			localcmd("exec maps/");
			localcmd(mapname);
			localcmd(".way\n");
			waypoint_mode = WM_DYNAMIC;
			bot_map_load();
		}
		else
		{
			waypoint_mode = WM_LOADED;
		}
	}
};

void() BotFrame =
{
	local float num;

	sv_maxspeed = autocvar_sv_maxspeed;
	sv_gravity = autocvar_sv_gravity;
	sv_friction = autocvar_sv_friction;
	sv_accelerate = autocvar_sv_accelerate;
	sv_stopspeed = autocvar_sv_stopspeed;
	real_frametime = frametime;
	self = nextent(world);
	num = 0;
	while ((num < max_clients))
	{
		if ((self.ishuman == FALSE))
		{
			if ((active_clients & ClientBitFlag(num)))
			{
				frik_obstacles();
				CL_KeyMove();
				SV_ClientThink();
				SV_Physics_Client();
			}
		}
		self = nextent(self);
		num = num + 1;
	}
	WaypointWatch();
	if (saved_bots)
	{
		bot_return();
	}
};

void() BotImpulses =
{
	local float f;

	if (BM_BotImpulses())
	{
		self.impulse = 0;
		return;
	}
	if (!cvar("sv_cheats"))
	{
		return;		// impulses 103-104 botcam & waypoint editor require sv_cheats
	}

	if ((self.impulse == 100))
	{
		f = cvar("skill");
		BotConnect(0, 0, f);
	}
	else
	{
		if ((self.impulse == 101))
		{
			f = cvar("skill");
			BotConnect(1, 0, f);
		}
		else
		{
			if ((self.impulse == 102))
			{
				KickABot();
			}
			else
			{
				if ((self.impulse == 103))
				{
					botcam_u();
				}
				else
				{
					if ((self.impulse == 104))
					{
						bot_way_edit();
					}
					else
					{
						return;
					}
				}
			}
		}
	}
	self.impulse = 0;
};
