//Decompiled code. Please respect the original copyright.

string(float r) BotName =
{
	self.b_num = r;
	if ((r == 1))
	{
		self.b_pants = 11;
		self.b_shirt = 0;
		return ("[BOT] Vincent");
	}
	if ((r == 2))
	{
		self.b_pants = 1;
		self.b_shirt = 3;
		return ("[BOT] Bishop");
	}
	if ((r == 3))
	{
		self.b_pants = 13;
		self.b_shirt = 2;
		return ("[BOT] Nomad");
	}
	if ((r == 4))
	{
		self.b_pants = 7;
		self.b_shirt = 6;
		return ("[BOT] Hudson");
	}
	if ((r == 5))
	{
		self.b_pants = 12;
		self.b_shirt = 6;
		return ("[BOT] Lore");
	}
	if ((r == 6))
	{
		self.b_pants = 4;
		self.b_shirt = 4;
		return ("[BOT] Servo");
	}
	if ((r == 7))
	{
		self.b_pants = 2;
		self.b_shirt = 5;
		return ("[BOT] Gort");
	}
	if ((r == 8))
	{
		self.b_pants = 10;
		self.b_shirt = 3;
		return ("[BOT] Kryten");
	}
	if ((r == 9))
	{
		self.b_pants = 9;
		self.b_shirt = 4;
		return ("[BOT] PimpBot");
	}
	if ((r == 10))
	{
		self.b_pants = 4;
		self.b_shirt = 7;
		return ("[BOT] Max");
	}
	if ((r == 11))
	{
		self.b_pants = 3;
		self.b_shirt = 11;
		return ("[BOT] Marvin");
	}
	if ((r == 12))
	{
		self.b_pants = 13;
		self.b_shirt = 12;
		return ("[BOT] Erwin");
	}
	if ((r == 13))
	{
		self.b_pants = 11;
		self.b_shirt = 2;
		return ("[BOT] FrikBot");
	}
	if ((r == 14))
	{
		self.b_pants = 0;
		self.b_shirt = 2;
		return ("[BOT] Krosis");
	}
	if ((r == 15))
	{
		self.b_pants = 8;
		self.b_shirt = 9;
		return ("[BOT] Gypsy");
	}
	self.b_pants = 5;
	self.b_shirt = 10;
	return ("[BOT] Hal");
};

string() PickARandomName =
{
	local float y;
	local float test;
	local string h;
	local entity t;

	if ((bot_count > 16))
	{
		return ("player");
	}
	y = TRUE;
	while (y)
	{
		test = ceil((random() * 16));
		h = BotName(test);
		t = find(world, netname, h);
		if ((t == world))
		{
			y = 0;
		}
	}
	return (h);
};

void(float tpic) bot_start_topic =
{
	if ((random() < 0.2))
	{
		b_topic = tpic;
		b_originator = self;
	}
	else
	{
		b_topic = 0;
	}
};

void() bot_chat =
{
	local float r;

	if ((b_options & OPT_NOCHAT))
	{
		return;
	}
	r = ceil((random() * 6));
	if ((self.b_chattime > time))
	{
		if ((self.b_skill < 2))
		{
			self.button2 = 0;
			self.button0 = 0;
			self.keys = 0;
		}
		return;
	}
	else
	{
		if (self.b_chattime)
		{
			if ((b_topic == 1))
			{
				if ((b_originator == self))
				{
					if ((r == 1))
					{
						BotSay(": lo all\n");
						bot_start_topic(8);
					}
					else
					{
						if ((r == 2))
						{
							BotSay(": hey everyone\n");
							bot_start_topic(8);
						}
						else
						{
							if ((r == 3))
							{
								BotSay(": prepare to be fragged!\n");
								bot_start_topic(0);
							}
							else
							{
								if ((r == 4))
								{
									BotSay(": boy this is laggy\n");
									bot_start_topic(11);
								}
								else
								{
									if ((r == 5))
									{
										BotSay(": #mm getting some lag here\n");
										bot_start_topic(11);
									}
									else
									{
										BotSay(": hi everyone\n");
										bot_start_topic(8);
									}
								}
							}
						}
					}
				}
			}
			else
			{
				if ((b_topic == 2))
				{
					if ((b_originator == self))
					{
						if ((r == 1))
						{
							BotSay(": take that\n");
						}
						else
						{
							if ((r == 2))
							{
								BotSay(": yehaww!\n");
							}
							else
							{
								if ((r == 3))
								{
									BotSay(": wh00p\n");
								}
								else
								{
									if ((r == 4))
									{
										BotSay(": j00_sawk();\n");
									}
									else
									{
										if ((r == 5))
										{
											BotSay(": i rule\n");
										}
										else
										{
											BotSay(": eat that\n");
										}
									}
								}
							}
						}
						bot_start_topic(0);
					}
				}
				else
				{
					if ((b_topic == 3))
					{
						if ((b_originator == self))
						{
							if ((r < 3))
							{
								BotSayTeam(": friendly eyes\n");
							}
							else
							{
								BotSayTeam(": team eyes\n");
							}
							bot_start_topic(0);
						}
					}
					else
					{
						if ((b_topic == 4))
						{
							if ((b_originator == self))
							{
								if ((r < 3))
								{
									BotSayTeam(": on your back\n");
								}
								else
								{
									BotSayTeam(": I'm with you\n");
								}
								bot_start_topic(0);
							}
						}
						else
						{
							if ((b_topic == 5))
							{
								if ((b_originator == self))
								{
									if ((r < 3))
									{
										BotSayTeam(": I need help\n");
									}
									else
									{
										BotSayTeam(": need backup\n");
									}
									bot_start_topic(0);
								}
							}
							else
							{
								if ((b_topic == 6))
								{
									if ((b_originator == self))
									{
										if ((r == 1))
										{
											BotSay(": sun got in my eyes\n");
											bot_start_topic(0);
										}
										else
										{
											if ((r == 2))
											{
												BotSay(": mouse needs cleaning\n");
												bot_start_topic(0);
											}
											else
											{
												if ((r == 3))
												{
													BotSay(": i meant to do that\n");
													bot_start_topic(0);
												}
												else
												{
													if ((r == 4))
													{
														BotSay(": lag\n");
														bot_start_topic(11);
													}
													else
													{
														if ((r == 5))
														{
															BotSay(": killer lag\n");
															bot_start_topic(11);
														}
														else
														{
															BotSay(": 100% lag\n");
															bot_start_topic(11);
														}
													}
												}
											}
										}
									}
								}
								else
								{
									if ((b_topic == 7))
									{
										if ((r == 1))
										{
											BotSay(": gg\n");
										}
										else
										{
											if ((r == 2))
											{
												BotSay(": gg all\n");
											}
											else
											{
												if ((r == 3))
												{
													BotSay(": that was fun\n");
												}
												else
												{
													if ((r == 4))
													{
														BotSay(": good game\n");
													}
													else
													{
														if ((r == 5))
														{
															BotSay(": pah\n");
														}
														else
														{
															BotSay(": hrm\n");
														}
													}
												}
											}
										}
										bot_start_topic(0);
									}
									else
									{
										if ((b_topic == 8))
										{
											if ((b_originator != self))
											{
												if ((r == 1))
												{
													BotSay(": heya\n");
													bot_start_topic(0);
												}
												else
												{
													if ((r == 2))
													{
														BotSay(": welcome\n");
														bot_start_topic(0);
													}
													else
													{
														if ((r == 3))
														{
															BotSayInit();
															BotSay2(": hi ");
															BotSay2(b_originator.netname);
															BotSay2("\n");
															bot_start_topic(0);
														}
														else
														{
															if ((r == 4))
															{
																BotSayInit();
																BotSay2(": hey ");
																BotSay2(b_originator.netname);
																BotSay2("\n");
																bot_start_topic(0);
															}
															else
															{
																if ((r == 5))
																{
																	BotSay(": howdy\n");
																	bot_start_topic(0);
																}
																else
																{
																	BotSay(": lo\n");
																	bot_start_topic(0);
																}
															}
														}
													}
												}
											}
										}
										else
										{
											if ((b_topic == 9))
											{
												if ((b_originator != self))
												{
													if ((r == 1))
													{
														BotSay(": hah\n");
													}
													else
													{
														if ((r == 2))
														{
															BotSay(": heheh\n");
														}
														else
														{
															if ((r == 3))
															{
																BotSayInit();
																BotSay2(": good work ");
																BotSay2(b_originator.netname);
																BotSay2("\n");
															}
															else
															{
																if ((r == 4))
																{
																	BotSayInit();
																	BotSay2(": nice1 ");
																	BotSay2(b_originator.netname);
																	BotSay2("\n");
																}
																else
																{
																	if ((r == 5))
																	{
																		BotSay(": lol\n");
																	}
																	else
																	{
																		BotSay(": :)\n");
																	}
																}
															}
														}
													}
													b_topic = 6;
												}
											}
											else
											{
												if ((b_topic == 10))
												{
													if ((b_originator != self))
													{
														if ((r == 1))
														{
															BotSay(": have a nice dip?\n");
														}
														else
														{
															if ((r == 2))
															{
																BotSay(": bah I hate levels with lava\n");
															}
															else
															{
																if ((r == 3))
																{
																	BotSayInit();
																	BotSay2(": good job ");
																	BotSay2(b_originator.netname);
																	BotSay2("\n");
																}
																else
																{
																	if ((r == 4))
																	{
																		BotSayInit();
																		BotSay2(": nice backflip ");
																		BotSay2(b_originator.netname);
																		BotSay2("\n");
																	}
																	else
																	{
																		if ((r == 5))
																		{
																			BotSay(": watch your step\n");
																		}
																		else
																		{
																			BotSay(": hehe\n");
																		}
																	}
																}
															}
														}
														b_topic = 6;
													}
												}
												else
												{
													if ((b_topic == 11))
													{
														if ((b_originator != self))
														{
															if ((r == 1))
															{
																BotSayInit();
																BotSay2(": yeah right ");
																BotSay2(b_originator.netname);
																BotSay2("\n");
																bot_start_topic(0);
															}
															else
															{
																if ((r == 2))
																{
																	BotSay(": ping\n");
																	bot_start_topic(0);
																}
																else
																{
																	if ((r == 3))
																	{
																		BotSay(": shuddup, you're an lpb\n");
																		bot_start_topic(0);
																	}
																	else
																	{
																		if ((r == 4))
																		{
																			BotSay(": lag my eye\n");
																			bot_start_topic(0);
																		}
																		else
																		{
																			if ((r == 5))
																			{
																				BotSay(": yeah\n");
																				bot_start_topic(11);
																			}
																			else
																			{
																				BotSay(": totally\n");
																				bot_start_topic(11);
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
			self.b_chattime = 0;
		}
		else
		{
			if (b_topic)
			{
				if ((random() < 0.5))
				{
					if ((self == b_originator))
					{
						if ((b_topic <= 7))
						{
							self.b_chattime = (time + 2);
						}
					}
					else
					{
						if ((b_topic >= 7))
						{
							self.b_chattime = (time + 2);
						}
					}
				}
			}
		}
	}
};

void() KickABot =
{
	local entity ty, oself;
	local string kname;

	ty = find(world, classname, "player");
	while ((ty != world))
	{
		if (!ty.ishuman)
		{
			kname = ty.netname;
			oself = self;
			self = ty;
			Jetpack_Off();
			self = oself;
			FD_Reset(ty);
			setmodel(ty, string_null);
			ty.solid = SOLID_NOT;
			ty.movetype = MOVETYPE_NONE;
			ty.takedamage = DAMAGE_NO;
			BotDisconnect(ty);
			ty.ishuman = TRUE;
			BM_BotNotifyKick(kname);
			ty = world;
		}
		else
		{
			ty = find(ty, classname, "player");
		}
	}
};

vector(entity ent) realorigin =
{
	return (((ent.absmin + ent.absmax) * 0.5));
};

float(entity targ) fisible =
{
	local vector spot1;
	local vector org;
	local float thruwater;
	local float pc1;
	local float pc2;

	org = realorigin(targ);
	spot1 = self.origin + self.view_ofs;
	if ((targ.solid == SOLID_BSP))
	{
		traceline(spot1, org, TRUE, self);
		if ((trace_ent == targ))
		{
			return (TRUE);
		}
		else
		{
			if ((trace_fraction == 1))
			{
				return (TRUE);
			}
		}
		return (0);
	}
	else
	{
		pc1 = pointcontents(org);
		pc2 = pointcontents(spot1);
		if ((targ.classname == "player"))
		{
			thruwater = 0;
		}
		else
		{
			if ((pc1 == CONTENT_LAVA))
			{
				return (0);
			}
			else
			{
				thruwater = TRUE;
			}
		}
	}
	if ((pc1 < -1))
	{
		if ((pc2 != pc1))
		{
			traceline(spot1, (org + targ.mins), TRUE, self);
			if (trace_inopen)
			{
				if (trace_inwater)
				{
					if (!thruwater)
					{
						return (0);
					}
				}
			}
			if ((trace_ent == targ))
			{
				return (TRUE);
			}
			else
			{
				if ((trace_fraction == 1))
				{
					return (TRUE);
				}
			}
			return (0);
		}
	}
	else
	{
		if ((pc2 != pc1))
		{
			traceline(spot1, (org + targ.maxs), TRUE, self);
			if (trace_inopen)
			{
				if (trace_inwater)
				{
					if (!thruwater)
					{
						return (0);
					}
				}
			}
			if ((trace_ent == targ))
			{
				return (TRUE);
			}
			else
			{
				if ((trace_fraction == 1))
				{
					return (TRUE);
				}
			}
			return (0);
		}
	}
	traceline(spot1, org, TRUE, self);
	if ((trace_ent == targ))
	{
		return (TRUE);
	}
	else
	{
		if ((trace_fraction == 1))
		{
			return (TRUE);
		}
	}
	traceline(spot1, (org + targ.maxs), TRUE, self);
	if ((trace_ent == targ))
	{
		return (TRUE);
	}
	else
	{
		if ((trace_fraction == 1))
		{
			return (TRUE);
		}
	}
	traceline(spot1, (org + targ.mins), TRUE, self);
	if ((trace_ent == targ))
	{
		return (TRUE);
	}
	else
	{
		if ((trace_fraction == 1))
		{
			return (TRUE);
		}
	}
	return (0);
};

float(entity targ1, entity targ2) wisible =
{
	local vector spot1;
	local vector spot2;
	local entity ignore;
	local float hops;

	spot1 = targ1.origin;
	spot2 = realorigin(targ2);
	ignore = self;
	// Each pass restarts the trace from the middle of the brush entity it hit, ignoring only that one. Two brush entities
	// in line (spruce has them) send it back and forth for ever: "server runaway loop counter hit limit of 10000000 jumps",
	// which ends the match for everyone. Eight hops are plenty; past that the answer is "not visible".
	hops = 0;
	do
	{
		traceline(spot1, spot2, TRUE, ignore);
		spot1 = realorigin(trace_ent);
		ignore = trace_ent;
		hops = hops + 1;

	} while (((trace_ent != world) && (trace_fraction != 1) && (hops < 8)));
	if ((trace_endpos == spot2))
	{
		return (TRUE);
	}
	else
	{
		return (0);
	}
};

float(entity targ) sisible =
{
	traceline(self.origin, targ.origin, TRUE, self);
	if ((trace_ent == targ))
	{
		return (TRUE);
	}
	else
	{
		if ((trace_fraction == 1))
		{
			return (TRUE);
		}
	}
};

float(float y1, float y2) angcomp =
{
	local float answer;

	y1 = frik_anglemod(y1);
	y2 = frik_anglemod(y2);
	answer = y1 - y2;
	if ((answer > 180))
	{
		answer = answer - 360;
	}
	else
	{
		if ((answer < -180))
		{
			answer = answer + 360;
		}
	}
	return (answer);
};

float(entity targ) fov =
{
	local vector yawn;
	local float g;

	yawn = realorigin(targ);
	yawn = (yawn + targ.view_ofs) - (self.origin + self.view_ofs);
	yawn = normalize(yawn);
	yawn = vectoangles(yawn);
	g = angcomp(self.v_angle_x, yawn_x);
	if ((fabs(g) > 45))
	{
		return (0);
	}
	g = angcomp(self.v_angle_y, yawn_y);
	if ((fabs(g) > 60))
	{
		return (0);
	}
	return (TRUE);
};

float(float v) frik_anglemod =
{
	return ((v - (floor((v / 360)) * 360)));
};
