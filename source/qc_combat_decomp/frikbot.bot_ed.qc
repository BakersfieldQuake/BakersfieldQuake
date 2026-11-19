//Decompiled code. Please respect the original copyright.

void() bot_menu_display =
{
	local string s1;
	local string s2;
	local string s3;
	local string s4;
	local string s5;
	local string s6;
	local string s7;
	local string h;
	local entity t;

	if ((((self.impulse > 0) && (self.impulse < 11)) && self.b_menu))
	{
		if ((self.b_menu == MENU_MAIN))
		{
			if ((self.impulse == 1))
			{
				self.b_menu = MENU_WAYPOINTS;
				self.b_menu_time = time;
			}
			else
			{
				if ((self.impulse == 2))
				{
					self.b_menu = MENU_LINKS;
					self.b_menu_time = time;
				}
				else
				{
					if ((self.impulse == 3))
					{
						self.b_menu = MENU_FLAGS;
						self.b_menu_time = time;
					}
					else
					{
						if ((self.impulse == 4))
						{
							self.b_menu = MENU_BOTS;
							self.b_menu_time = time;
						}
						else
						{
							if ((self.impulse == 5))
							{
								self.b_menu = MENU_WAYLIST;
								self.b_menu_time = time;
							}
							else
							{
								if ((self.impulse == 6))
								{
									if ((self.movetype == MOVETYPE_NOCLIP))
									{
										self.movetype = MOVETYPE_WALK;
									}
									else
									{
										self.movetype = MOVETYPE_NOCLIP;
									}
									self.b_menu_time = time;
								}
								else
								{
									if ((self.impulse == 7))
									{
										if ((self.flags & FL_GODMODE))
										{
											self.flags = (self.flags - FL_GODMODE);
										}
										else
										{
											self.flags = (self.flags | FL_GODMODE);
										}
										self.b_menu_time = time;
									}
									else
									{
										if ((self.impulse == 8))
										{
											if ((self.b_aiflags & AI_HOLD_SELECT))
											{
												self.b_aiflags = (self.b_aiflags - AI_HOLD_SELECT);
											}
											else
											{
												self.b_aiflags = (self.b_aiflags | AI_HOLD_SELECT);
											}
											self.b_menu_time = time;
										}
										else
										{
											if ((self.impulse == 9))
											{
												self.b_menu = 14;
												self.b_menu_time = time;
											}
											else
											{
												if ((self.impulse == 10))
												{
													bot_way_edit();
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
		else
		{
			if ((self.b_menu == MENU_WAYPOINTS))
			{
				if ((self.impulse == 1))
				{
					if (self.current_way)
					{
						setorigin(self.current_way, (self.origin + self.view_ofs));
					}
				}
				else
				{
					if ((self.impulse == 2))
					{
						if (self.current_way)
						{
							self.b_menu = 15;
							self.b_menu_time = time;
							self.last_way = self.current_way;
						}
					}
					else
					{
						if ((self.impulse == 3))
						{
							make_waypoint((self.origin + self.view_ofs));
						}
						else
						{
							if ((self.impulse == 4))
							{
								t = make_waypoint((self.origin + self.view_ofs));
								if (!LinkWays(self.current_way, t))
								{
									sprint(self, "Unable to link them\n");
								}
							}
							else
							{
								if ((self.impulse == 5))
								{
									t = make_waypoint((self.origin + self.view_ofs));
									if (!LinkWays(self.current_way, t))
									{
										sprint(self, "Unable to link old to new\n");
									}
									LinkWays(t, self.current_way);
								}
								else
								{
									if ((self.impulse == 6))
									{
										t = make_waypoint((self.origin + self.view_ofs));
										if (!TeleLinkWays(self.current_way, t))
										{
											sprint(self, "Unable to link them\n");
										}
									}
									else
									{
										if ((self.impulse == 7))
										{
											if (self.current_way)
											{
												sprint(self, "\nwaypoint info for waypoint #");
												h = ftos(self.current_way.count);
												sprint(self, h);
												sprint(self, "\nAI Flag value: ");
												h = ftos(self.current_way.b_aiflags);
												sprint(self, h);
												if (self.current_way.target1)
												{
													h = ftos(self.current_way.target1.count);
													if ((self.current_way.b_aiflags & AI_TELELINK_1))
													{
														sprint(self, "\nTelelink1 to:");
													}
													else
													{
														sprint(self, "\nLink1 to:");
													}
													sprint(self, h);
												}
												if (self.current_way.target2)
												{
													h = ftos(self.current_way.target2.count);
													if ((self.current_way.b_aiflags & AI_TELELINK_2))
													{
														sprint(self, "\nTelelink2 to:");
													}
													else
													{
														sprint(self, "\nLink2 to:");
													}
													sprint(self, h);
												}
												if (self.current_way.target3)
												{
													h = ftos(self.current_way.target3.count);
													if ((self.current_way.b_aiflags & AI_TELELINK_3))
													{
														sprint(self, "\nTelelink3 to:");
													}
													else
													{
														sprint(self, "\nLink3 to:");
													}
													sprint(self, h);
												}
												if (self.current_way.target4)
												{
													h = ftos(self.current_way.target4.count);
													if ((self.current_way.b_aiflags & AI_TELELINK_4))
													{
														sprint(self, "\nTelelink4 to:");
													}
													else
													{
														sprint(self, "\nLink4 to:");
													}
													sprint(self, h);
												}
												sprint(self, "\n\n");
											}
										}
									}
								}
							}
						}
					}
				}
				if ((self.impulse == 8))
				{
					self.b_menu = MENU_LINKS;
					self.b_menu_time = time;
				}
				else
				{
					if ((self.impulse == 9))
					{
						self.b_menu = MENU_FLAGS;
						self.b_menu_time = time;
					}
					else
					{
						if ((self.impulse == 10))
						{
							self.b_menu = MENU_MAIN;
							self.b_menu_time = time;
						}
					}
				}
			}
			else
			{
				if ((self.b_menu == MENU_LINKS))
				{
					if ((self.impulse == 1))
					{
						self.b_menu = 16;
						self.b_menu_time = time;
						self.last_way = self.current_way;
					}
					else
					{
						if ((self.impulse == 2))
						{
							self.b_menu = 8;
							self.b_menu_time = time;
							self.last_way = self.current_way;
						}
						else
						{
							if ((self.impulse == 3))
							{
								self.b_menu = 9;
								self.b_menu_time = time;
								self.last_way = self.current_way;
							}
							else
							{
								if ((self.impulse == 4))
								{
									self.b_menu = 10;
									self.b_menu_time = time;
									self.last_way = self.current_way;
								}
								else
								{
									if ((self.impulse == 5))
									{
										self.b_menu = 11;
										self.b_menu_time = time;
										self.last_way = self.current_way;
									}
									else
									{
										if ((self.impulse == 6))
										{
											self.b_menu = 12;
											self.b_menu_time = time;
											self.last_way = self.current_way;
										}
										else
										{
											if ((self.impulse == 7))
											{
												make_waypoint((self.origin + self.view_ofs));
											}
											else
											{
												if ((self.impulse == 8))
												{
													self.b_menu = MENU_WAYPOINTS;
													self.b_menu_time = time;
												}
												else
												{
													if ((self.impulse == 9))
													{
														self.b_menu = MENU_FLAGS;
														self.b_menu_time = time;
													}
													else
													{
														if ((self.impulse == 10))
														{
															self.b_menu = MENU_MAIN;
															self.b_menu_time = time;
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
				else
				{
					if ((self.b_menu == MENU_FLAGS))
					{
						if (self.current_way)
						{
							if ((self.impulse == 1))
							{
								if ((self.current_way.b_aiflags & AI_DOORFLAG))
								{
									self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_DOORFLAG));
								}
								else
								{
									self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_DOORFLAG);
								}
								self.b_menu_time = time;
							}
							else
							{
								if ((self.impulse == 2))
								{
									if ((self.current_way.b_aiflags & AI_PRECISION))
									{
										self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_PRECISION));
									}
									else
									{
										self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_PRECISION);
									}
									self.b_menu_time = time;
								}
								else
								{
									if ((self.impulse == 3))
									{
										if ((self.current_way.b_aiflags & AI_SURFACE))
										{
											self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_SURFACE));
										}
										else
										{
											self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_SURFACE);
										}
										self.b_menu_time = time;
									}
									else
									{
										if ((self.impulse == 4))
										{
											if ((self.current_way.b_aiflags & AI_BLIND))
											{
												self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_BLIND));
											}
											else
											{
												self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_BLIND);
											}
											self.b_menu_time = time;
										}
										else
										{
											if ((self.impulse == 5))
											{
												if ((self.current_way.b_aiflags & AI_JUMP))
												{
													self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_JUMP));
												}
												else
												{
													self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_JUMP);
												}
												self.b_menu_time = time;
											}
											else
											{
												if ((self.impulse == 6))
												{
													if ((self.current_way.b_aiflags & AI_DIRECTIONAL))
													{
														self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_DIRECTIONAL));
													}
													else
													{
														self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_DIRECTIONAL);
													}
													self.b_menu_time = time;
												}
												else
												{
													if ((self.impulse == 7))
													{
														if ((self.current_way.b_aiflags & AI_SUPER_JUMP))
														{
															self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_SUPER_JUMP));
														}
														else
														{
															self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_SUPER_JUMP);
														}
														self.b_menu_time = time;
													}
												}
											}
										}
									}
								}
							}
						}
						if ((self.impulse == 9))
						{
							self.b_menu = MENU_FLAGS2;
							self.b_menu_time = time;
						}
						else
						{
							if ((self.impulse == 10))
							{
								self.b_menu = MENU_MAIN;
								self.b_menu_time = time;
							}
						}
					}
					else
					{
						if ((self.b_menu == MENU_FLAGS2))
						{
							if (self.current_way)
							{
								if ((self.impulse == 1))
								{
									if ((self.current_way.b_aiflags & AI_DIFFICULT))
									{
										self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_DIFFICULT));
									}
									else
									{
										self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_DIFFICULT);
									}
									self.b_menu_time = time;
								}
								else
								{
									if ((self.impulse == 2))
									{
										if ((self.current_way.b_aiflags & AI_PLAT_BOTTOM))
										{
											self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_PLAT_BOTTOM));
										}
										else
										{
											self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_PLAT_BOTTOM);
										}
										self.b_menu_time = time;
									}
									else
									{
										if ((self.impulse == 3))
										{
											if ((self.current_way.b_aiflags & AI_RIDE_TRAIN))
											{
												self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_RIDE_TRAIN));
											}
											else
											{
												self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_RIDE_TRAIN);
											}
											self.b_menu_time = time;
										}
										else
										{
											if ((self.impulse == 4))
											{
												if ((self.current_way.b_aiflags & AI_DOOR_NO_OPEN))
												{
													self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_DOOR_NO_OPEN));
												}
												else
												{
													self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_DOOR_NO_OPEN);
												}
												self.b_menu_time = time;
											}
											else
											{
												if ((self.impulse == 5))
												{
													if ((self.current_way.b_aiflags & AI_AMBUSH))
													{
														self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_AMBUSH));
													}
													else
													{
														self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_AMBUSH);
													}
													self.b_menu_time = time;
												}
												else
												{
													if ((self.impulse == 6))
													{
														if ((self.current_way.b_aiflags & AI_SNIPER))
														{
															self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_SNIPER));
														}
														else
														{
															self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_SNIPER);
														}
														self.b_menu_time = time;
													}
													else
													{
														if ((self.impulse == 7))
														{
															if ((self.current_way.b_aiflags & AI_TRACE_TEST))
															{
																self.current_way.b_aiflags = (self.current_way.b_aiflags - (self.current_way.b_aiflags & AI_TRACE_TEST));
															}
															else
															{
																self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_TRACE_TEST);
															}
															self.b_menu_time = time;
														}
													}
												}
											}
										}
									}
								}
							}
							if ((self.impulse == 9))
							{
								self.b_menu = MENU_FLAGS;
								self.b_menu_time = time;
							}
							else
							{
								if ((self.impulse == 10))
								{
									self.b_menu = MENU_MAIN;
									self.b_menu_time = time;
								}
							}
						}
						else
						{
							if ((self.b_menu == MENU_BOTS))
							{
								if ((self.impulse == 1))
								{
									self.impulse = 100;
									return;
								}
								else
								{
									if ((self.impulse == 2))
									{
										b_temp3 = self;
										self = player_head;
										while (self)
										{
											if (!self.ishuman)
											{
												target_add(b_temp3);
												bot_get_path(b_temp3, TRUE);
												self = world;
											}
											else
											{
												self = self._next;
											}
										}
										self = b_temp3;
									}
									else
									{
										if ((self.impulse == 3))
										{
											self.impulse = 102;
											return;
										}
										else
										{
											if ((self.impulse == 4))
											{
												b_temp1 = self;
												self = player_head;
												while (self)
												{
													if (!self.ishuman)
													{
														self.target4 = world;
														self.target3 = world;
														self.target2 = world;
														self.target1 = world;
														ClearRouteTable();
														route_table = world;
														busy_waypoints = 0;
														direct_route = 0;
													}
													self = self._next;
												}
												self = b_temp1;
											}
											else
											{
												if ((self.impulse == 5))
												{
													if (self.current_way)
													{
														b_temp1 = self;
														self = player_head;
														while (self)
														{
															if (!self.ishuman)
															{
																setorigin(self, b_temp1.current_way.origin);
															}
															self = self._next;
														}
														self = b_temp1;
													}
													else
													{
														sprint(self, "select a waypoint first\n");
													}
												}
												else
												{
													if ((self.impulse == 6))
													{
														self.b_menu = 14;
														self.b_menu_time = time;
													}
													else
													{
														if ((self.impulse == 10))
														{
															self.b_menu = MENU_MAIN;
															self.b_menu_time = time;
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
								if ((self.b_menu == MENU_WAYLIST))
								{
									if ((self.impulse == 1))
									{
										self.b_menu = 13;
										self.b_menu_time = time;
									}
									else
									{
										if ((self.impulse == 2))
										{
											if ((dump_mode == 0))
											{
												DumpWaypoints();
											}
											else
											{
												if ((dump_mode == 1))
												{
													QCDumpWaypoints();
												}
												else
												{
													if ((dump_mode == 2))
													{
														BSPDumpWaypoints();
													}
												}
											}
										}
										else
										{
											if ((self.impulse == 3))
											{
												t = way_head;
												while (t)
												{
													if (((((t.target1 == world) && (t.target2 == world)) && (t.target3 == world)) && (t.target4 == world)))
													{
														sprint(self, "Waypoint #");
														h = ftos(t.count);
														sprint(self, h);
														sprint(self, " has no outbound links\n");
													}
													if (((((t.target1 == t) || (t.target2 == t)) || (t.target3 == t)) || (t.target4 == t)))
													{
														sprint(self, "Waypoint #");
														h = ftos(t.count);
														sprint(self, h);
														sprint(self, " links to itself (??)\n");
													}
													t = t._next;
												}
												sprint(self, "Error check complete\n");
											}
											else
											{
												if ((self.impulse == 4))
												{
													self.b_menu = 17;
													self.b_menu_time = time;
												}
												else
												{
													if ((self.impulse == 5))
													{
														if ((waypoint_mode == WM_EDITOR_DYNAMIC))
														{
															waypoint_mode = WM_EDITOR;
														}
														else
														{
															waypoint_mode = WM_EDITOR_DYNAMIC;
														}
														self.b_menu_time = time;
													}
													else
													{
														if ((self.impulse == 6))
														{
															if ((waypoint_mode == WM_EDITOR_DYNLINK))
															{
																waypoint_mode = WM_EDITOR;
															}
															else
															{
																waypoint_mode = WM_EDITOR_DYNLINK;
															}
															self.b_menu_time = time;
														}
														else
														{
															if ((self.impulse == 7))
															{
																dump_mode = 0;
																self.b_menu_time = time;
															}
															else
															{
																if ((self.impulse == 8))
																{
																	dump_mode = 1;
																	self.b_menu_time = time;
																}
																else
																{
																	if ((self.impulse == 9))
																	{
																		dump_mode = 2;
																		self.b_menu_time = time;
																	}
																	else
																	{
																		if ((self.impulse == 10))
																		{
																			self.b_menu = MENU_MAIN;
																			self.b_menu_time = time;
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
								else
								{
									if ((self.b_menu == 8))
									{
										if ((self.impulse == 1))
										{
											if (self.current_way)
											{
												if (!LinkWays(self.last_way, self.current_way))
												{
													sprint(self, "Unable to link them\n");
												}
												self.b_menu = MENU_LINKS;
												self.b_menu_time = time;
											}
										}
										else
										{
											if ((self.impulse == 2))
											{
												self.b_menu = MENU_LINKS;
												self.b_menu_time = time;
											}
										}
									}
									else
									{
										if ((self.b_menu == 9))
										{
											if ((self.impulse == 1))
											{
												if (self.current_way)
												{
													if (!TeleLinkWays(self.last_way, self.current_way))
													{
														sprint(self, "Unable to link them\n");
													}
													self.b_menu = MENU_LINKS;
													self.b_menu_time = time;
												}
											}
											else
											{
												if ((self.impulse == 2))
												{
													self.b_menu = MENU_LINKS;
													self.b_menu_time = time;
												}
											}
										}
										else
										{
											if ((self.b_menu == 10))
											{
												if ((self.impulse == 1))
												{
													if (self.current_way)
													{
														UnlinkWays(self.last_way, self.current_way);
														self.b_menu = MENU_LINKS;
														self.b_menu_time = time;
													}
												}
												else
												{
													if ((self.impulse == 2))
													{
														self.b_menu = MENU_LINKS;
														self.b_menu_time = time;
													}
												}
											}
											else
											{
												if ((self.b_menu == 11))
												{
													if ((self.impulse == 1))
													{
														if (self.current_way)
														{
															if (!LinkWays(self.last_way, self.current_way))
															{
																sprint(self, "Unable to link 1 to 2\n");
															}
															if (!LinkWays(self.current_way, self.last_way))
															{
																sprint(self, "Unable to link 2 to 1\n");
															}
															self.b_menu = MENU_LINKS;
															self.b_menu_time = time;
														}
													}
													else
													{
														if ((self.impulse == 2))
														{
															self.b_menu = MENU_LINKS;
															self.b_menu_time = time;
														}
													}
												}
												else
												{
													if ((self.b_menu == 12))
													{
														if ((self.impulse == 1))
														{
															if (self.current_way)
															{
																UnlinkWays(self.last_way, self.current_way);
																UnlinkWays(self.current_way, self.last_way);
																self.b_menu = MENU_LINKS;
																self.b_menu_time = time;
															}
														}
														else
														{
															if ((self.impulse == 2))
															{
																self.b_menu = MENU_LINKS;
																self.b_menu_time = time;
															}
														}
													}
													else
													{
														if ((self.b_menu == 13))
														{
															if ((self.impulse == 1))
															{
																ClearAllWays();
																self.b_menu = MENU_WAYLIST;
																self.b_menu_time = time;
															}
															else
															{
																if ((self.impulse == 2))
																{
																	self.b_menu = MENU_WAYLIST;
																	self.b_menu_time = time;
																}
															}
														}
														else
														{
															if ((self.b_menu == 14))
															{
																if ((self.impulse == 10))
																{
																	self.impulse = 0;
																}
																self.b_menu_value = ((self.b_menu_value * 10) + self.impulse);
																self.b_menu_time = 0;
															}
															else
															{
																if ((self.b_menu == 15))
																{
																	if ((self.impulse == 1))
																	{
																		delete_waypoint(self.last_way);
																		self.b_menu = MENU_WAYPOINTS;
																		self.b_menu_time = time;
																	}
																	else
																	{
																		if ((self.impulse == 2))
																		{
																			self.b_menu = MENU_WAYPOINTS;
																			self.b_menu_time = time;
																		}
																	}
																}
																else
																{
																	if ((self.b_menu == 16))
																	{
																		if ((self.impulse == 1))
																		{
																			if (self.last_way)
																			{
																				self.last_way.target4 = world;
																				self.last_way.target3 = world;
																				self.last_way.target2 = world;
																				self.last_way.target1 = world;
																				self.last_way.b_aiflags = (self.last_way.b_aiflags - (self.last_way.b_aiflags & 15));
																			}
																			self.b_menu = MENU_LINKS;
																			self.b_menu_time = time;
																		}
																		else
																		{
																			if ((self.impulse == 2))
																			{
																				self.b_menu = MENU_LINKS;
																				self.b_menu_time = time;
																			}
																		}
																	}
																	else
																	{
																		if ((self.b_menu == 17))
																		{
																			if ((self.impulse == 1))
																			{
																				SaveWays();
																			}
																			if ((self.impulse < 3))
																			{
																				self.b_menu = MENU_WAYLIST;
																				self.b_menu_time = time;
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
		self.impulse = 0;
	}
	if ((self.b_menu_time <= time))
	{
		if ((self.b_menu == MENU_MAIN))
		{
			s1 = "­­ Ναιξ Νεξυ ­­\n >>Waypoint Management\n >>Link Management    \n >>AI Flag Management \n >>Bot Management     \n >>Waylist Management \n";
			if ((self.movetype == MOVETYPE_NOCLIP))
			{
				s2 = " … Noclip           \n";
			}
			else
			{
				s2 = "   Noclip           \n";
			}
			if ((self.flags & FL_GODMODE))
			{
				s3 = " … Godmode          \n";
			}
			else
			{
				s3 = "   Godmode          \n";
			}
			if ((self.b_aiflags & AI_HOLD_SELECT))
			{
				s4 = " … Hold Select      \n";
			}
			else
			{
				s4 = "   Hold Select      \n";
			}
			s5 = " Teleport to Way #    \n Close Menu           \n";
		}
		else
		{
			if ((self.b_menu == MENU_WAYPOINTS))
			{
				s1 = "­­ Χαωποιξτ Ναξαηενεξτ ­­\n Move Waypoint        \n Delete Waypoint      \n Make Waypoint        \n Make Way + Link      \n Make Way + Link X2   \n Make Way + Telelink  \n Show waypoint info   \n >>Link Management    \n >>AI Flag Management \n >>Main Menu          \n";
			}
			else
			{
				if ((self.b_menu == MENU_LINKS))
				{
					s1 = "­­ Μιξλ Ναξαηενεξτ ­­\n Unlink Waypoint      \n Create Link          \n Create Telelink      \n Delete Link          \n Create Link X2       \n Delete Link X2       \n >Make Waypoint       \n >>Waypoint Management\n >>AI Flag Management \n >>Main Menu          \n";
				}
				else
				{
					if ((self.b_menu == MENU_FLAGS))
					{
						if ((self.current_way.b_aiflags & AI_DOORFLAG))
						{
							s1 = "­­ ΑΙ Ζμαη Ναξαηενεξτ ­­\n … Door Flag        \n";
						}
						else
						{
							s1 = "­­ ΑΙ Ζμαη Ναξαηενεξτ ­­\n   Door Flag        \n";
						}
						if ((self.current_way.b_aiflags & AI_PRECISION))
						{
							s2 = " … Precision        \n";
						}
						else
						{
							s2 = "   Precision        \n";
						}
						if ((self.current_way.b_aiflags & AI_SURFACE))
						{
							s3 = " … Surface for air  \n";
						}
						else
						{
							s3 = "   Surface for air  \n";
						}
						if ((self.current_way.b_aiflags & AI_BLIND))
						{
							s4 = " … Blind mode       \n";
						}
						else
						{
							s4 = "   Blind mode       \n";
						}
						if ((self.current_way.b_aiflags & AI_JUMP))
						{
							s5 = " … Jump             \n";
						}
						else
						{
							s5 = "   Jump             \n";
						}
						if ((self.current_way.b_aiflags & AI_DIRECTIONAL))
						{
							s6 = " … Directional      \n";
						}
						else
						{
							s6 = "   Directional      \n";
						}
						if ((self.current_way.b_aiflags & AI_SUPER_JUMP))
						{
							s7 = " … Super Jump       \n\n >>AI Flags page 2    \n >>Main Menu          \n";
						}
						else
						{
							s7 = "   Super Jump       \n\n >>AI Flags page 2    \n >>Main Menu          \n";
						}
					}
					else
					{
						if ((self.b_menu == MENU_FLAGS2))
						{
							if ((self.current_way.b_aiflags & AI_DIFFICULT))
							{
								s1 = "­­ ΑΙ Ζμαησ πη® ²­­\n … Difficult        \n";
							}
							else
							{
								s1 = "­­ ΑΙ Ζμαησ πη® ²­­\n   Difficult        \n";
							}
							if ((self.current_way.b_aiflags & AI_PLAT_BOTTOM))
							{
								s2 = " … Wait for plat    \n";
							}
							else
							{
								s2 = "   Wait for plat    \n";
							}
							if ((self.current_way.b_aiflags & AI_RIDE_TRAIN))
							{
								s3 = " … Ride train       \n";
							}
							else
							{
								s3 = "   Ride train       \n";
							}
							if ((self.current_way.b_aiflags & AI_DOOR_NO_OPEN))
							{
								s4 = " … Door flag no open\n";
							}
							else
							{
								s4 = "   Door flag no open\n";
							}
							if ((self.current_way.b_aiflags & AI_AMBUSH))
							{
								s5 = " … Ambush           \n";
							}
							else
							{
								s5 = "   Ambush           \n";
							}
							if ((self.current_way.b_aiflags & AI_SNIPER))
							{
								s6 = " … Snipe            \n";
							}
							else
							{
								s6 = "   Snipe            \n";
							}
							if ((self.current_way.b_aiflags & AI_TRACE_TEST))
							{
								s7 = " … Trace Test       \n\n >>AI Flag Management \n >>Main Menu          \n";
							}
							else
							{
								s7 = "   Trace Test       \n\n >>AI Flag Management \n >>Main Menu          \n";
							}
						}
						else
						{
							if ((self.b_menu == MENU_BOTS))
							{
								s1 = "­­ Βοτ Ναξαηενεξτ ­­\n Add a Test Bot       \n Order Test Bot here  \n Remove Test Bot      \n Stop Test Bot        \n Teleport Bot here    \n Teleport to Way #    \n\n\n\n >>Main Menu          \n";
							}
							else
							{
								if ((self.b_menu == MENU_WAYLIST))
								{
									s1 = "­­ Χαωμιστ Ναξαηενεξτ ­­\n Delete ALL Waypoints \n Dump Waypoints       \n Check For Errors     \n Save Waypoints       \n";
									if ((waypoint_mode == WM_EDITOR_DYNAMIC))
									{
										s2 = " … Dynamic Mode     \n … Dynamic Link     \n";
									}
									else
									{
										if ((waypoint_mode == WM_EDITOR_DYNLINK))
										{
											s2 = "   Dynamic Mode     \n … Dynamic Link     \n";
										}
										else
										{
											s2 = "   Dynamic Mode     \n   Dynamic Link     \n";
										}
									}
									if ((dump_mode == 0))
									{
										s3 = " … WAY output       \n   QC output        \n   BSP ents output  \n Main Menu            \n";
									}
									else
									{
										if ((dump_mode == 1))
										{
											s3 = "   WAY output       \n … QC output        \n   BSP ents output  \n Main Menu            \n";
										}
										else
										{
											if ((dump_mode == 2))
											{
												s3 = "   WAY output       \n   QC output        \n … BSP ents output  \n Main Menu            \n";
											}
										}
									}
								}
								else
								{
									if ((self.b_menu == 8))
									{
										s1 = "­­ Μιξλ Χαωσ ­­\n\nSelect another way and push 1\nor press 2 to cancel";
									}
									else
									{
										if ((self.b_menu == 9))
										{
											s1 = "­­ Τεμεμιξλ Χαωσ ­­\n\nSelect another way and push 1\nor press 2 to cancel";
										}
										else
										{
											if ((self.b_menu == 10))
											{
												s1 = "­­ Δεμετε Μιξλ ­­\n\nSelect another way and push 1\nor press 2 to cancel";
											}
											else
											{
												if ((self.b_menu == 11))
												{
													s1 = "­­ Γςεατε Μιξλ Ψ² ­­\n\nSelect another way and push 1\nor press 2 to cancel";
												}
												else
												{
													if ((self.b_menu == 12))
													{
														s1 = "­­ Δεμετε Μιξλ Ψ² ­­\n\nSelect another way and push 1\nor press 2 to cancel";
													}
													else
													{
														if ((self.b_menu == 13))
														{
															s1 = "­­ Δεμετε ΑΜΜ Χαωσ ­­\n\nAre you sure? Push 1 to go\nthrough with it, 2 to cancel";
														}
														else
														{
															if ((self.b_menu == 14))
															{
																s1 = "­­ Τεμεποςτ το Χαω # ­­\n\nEnter way number and press\nimpulse 104 to warp\n\nWaypoint #";
																s2 = ftos(self.b_menu_value);
															}
															else
															{
																if ((self.b_menu == 15))
																{
																	s1 = "­­ Δεμετε Χαωποιξτ ­­\n\nAre you sure? Push 1 to go\nthrough with it, 2 to cancel";
																}
																else
																{
																	if ((self.b_menu == 16))
																	{
																		s1 = "­­ Υξμιξλ Χαωποιξτ ­­\n\nAre you sure? Push 1 to go\nthrough with it, 2 to cancel";
																	}
																	else
																	{
																		if ((self.b_menu == 17))
																		{
																			s1 = "­­ Σαφε Χαωποιξτσ ­­\n\nSave Waypoints requires\nFrikaC's file access tutorial from\nwww.quakesrc.org to be present\n in the engine code.\n Push 1 to continue, 2 to cancel";
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
		frik_big_centerprint(self, s1, s2, s3, s4, s5, s6, s7);
		self.b_menu_time = (time + 1.25);
	}
};

void() bot_way_edit =
{
	local entity t;
	local float f;

	if (self.b_menu_value)
	{
		if ((self.b_menu == 14))
		{
			t = WaypointForNum(self.b_menu_value);
			if (t)
			{
				setorigin(self, (t.origin - self.view_ofs));
			}
			else
			{
				sprint(self, "No waypoint with that number\n");
			}
			self.b_menu = MENU_MAIN;
			self.b_menu_time = time;
		}
		self.b_menu_value = 0;
		return;
	}
	if ((waypoint_mode < WM_EDITOR))
	{
		self.b_menu = MENU_MAIN;
		waypoint_mode = WM_EDITOR;
		self.b_menu_time = 0;
		cvar_set("saved2", "0");
		WriteByte(MSG_ALL, 8);
		WriteByte(MSG_ALL, 1);
		WriteString(MSG_ALL, "MAKE SURE THE FOLLOWING LINE CONTAINS -CONDEBUG BEFORE PROCEEDING\n");
		localcmd("cmdline\n");
		t = way_head;
		while (t)
		{
			setmodel(t, "progs/s_bubble.spr");
			t = t._next;
		}
		if (self.current_way)
		{
			setmodel(self.current_way, "progs/s_light.spr");
		}
	}
	else
	{
		saved2 = cvar("saved2");
		if ((saved2 != 0))
		{
			f = self.b_menu;
			self.b_menu = floor((saved2 / 16));
			self.impulse = (saved2 & 15);
			bot_menu_display();
			if ((self.b_menu == floor((saved2 / 16))))
			{
				self.b_menu = f;
			}
			cvar_set("saved2", "0");
			return;
		}
		self.b_menu = 0;
		waypoint_mode = WM_LOADED;
		t = way_head;
		while (t)
		{
			setmodel(t, string_null);
			t = t._next;
		}
	}
};

void() PrintWaypoint =
{
	local entity t;
	local float needcolon;
	local string h;

	if ((self.enemy == world))
	{
		t = way_head;
	}
	else
	{
		t = self.enemy._next;
	}
	if ((bytecounter >= 8000))
	{
		bprint("exec maps/");
		bprint(mapname);
		bprint(".wa");
		h = ftos(filecount);
		bprint(h);
		filecount = filecount + 1;
		bprint("\n// **** break here ****\n");
		bytecounter = 26;
	}
	if ((t == world))
	{
		remove(self);
		fixer = world;
		bprint("saved4 3\n// end waypoint dump\n");
		bytecounter = bytecounter + 27;
		return;
	}
	t.origin_x = rint(t.origin_x);
	t.origin_y = rint(t.origin_y);
	t.origin_z = rint(t.origin_z);
	if (((t.origin_x != saved1) || (t.count == 1)))
	{
		bprint("saved1 ");
		h = ftos(t.origin_x);
		bprint(h);
		saved1 = t.origin_x;
		bytecounter = bytecounter + 12;
		needcolon = TRUE;
	}
	if (((t.origin_y != saved2) || (t.count == 1)))
	{
		if (needcolon)
		{
			bprint("; ");
			bytecounter = bytecounter + 2;
		}
		else
		{
			needcolon = TRUE;
		}
		bprint("saved2 ");
		h = ftos(t.origin_y);
		bprint(h);
		bytecounter = bytecounter + 12;
		saved2 = t.origin_y;
	}
	if (((t.origin_z != saved3) || (t.count == 1)))
	{
		if (needcolon)
		{
			bprint("; ");
			bytecounter = bytecounter + 2;
		}
		else
		{
			needcolon = TRUE;
		}
		bprint("saved3 ");
		h = ftos(t.origin_z);
		bprint(h);
		bytecounter = bytecounter + 12;
		saved3 = t.origin_z;
	}
	if (needcolon)
	{
		bytecounter = bytecounter + 1;
		bprint("\n");
		needcolon = 0;
	}
	if (((scratch1 != t.target1.count) || (t.count == 1)))
	{
		needcolon = TRUE;
		bprint("scratch1 ");
		bytecounter = bytecounter + 14;
		h = ftos(t.target1.count);
		bprint(h);
		scratch1 = t.target1.count;
	}
	if (((scratch2 != t.target2.count) || (t.count == 1)))
	{
		if (needcolon)
		{
			bprint("; ");
			bytecounter = bytecounter + 2;
		}
		else
		{
			needcolon = TRUE;
		}
		bprint("scratch2 ");
		bytecounter = bytecounter + 14;
		h = ftos(t.target2.count);
		bprint(h);
		scratch2 = t.target2.count;
	}
	if (((scratch3 != t.target3.count) || (t.count == 1)))
	{
		if (needcolon)
		{
			bprint("; ");
			bytecounter = bytecounter + 2;
		}
		else
		{
			needcolon = TRUE;
		}
		bprint("scratch3 ");
		bytecounter = bytecounter + 14;
		h = ftos(t.target3.count);
		bprint(h);
		scratch3 = t.target3.count;
	}
	if (((scratch4 != t.target4.count) || (t.count == 1)))
	{
		if (needcolon)
		{
			bprint("; ");
			bytecounter = bytecounter + 2;
		}
		else
		{
			needcolon = TRUE;
		}
		bprint("scratch4 ");
		bytecounter = bytecounter + 14;
		h = ftos(t.target4.count);
		bprint(h);
		scratch4 = t.target4.count;
	}
	if (needcolon)
	{
		bprint("\n");
		needcolon = 0;
	}
	bprint("saved4 ");
	bytecounter = bytecounter + 19;
	if ((t.count != 1))
	{
		h = ftos(((t.b_aiflags * 4) + 2));
	}
	else
	{
		h = ftos(((t.b_aiflags * 4) + 1));
	}
	bprint(h);
	bprint("; wait\n");
	self.nextthink = (time + 0.01);
	self.enemy = t;
};

void() DumpWaypoints =
{
	bytecounter = 50;
	filecount = 1;
	bprint("// ");
	bprint(world.message);
	bprint(" - maps/");
	bprint(mapname);
	bprint(".way\n");
	bprint("// Ways by ");
	bprint(self.netname);
	bprint("\n");
	if (!fixer)
	{
		fixer = spawn();
		fixer.nextthink = (time + 0.01);
		fixer.think = PrintWaypoint;
		fixer.enemy = world;
	}
};

void() PrintQCWaypoint =
{
	local entity t;
	local string h;

	if ((self.enemy == world))
	{
		t = way_head;
	}
	else
	{
		t = self.enemy._next;
	}
	if ((t == world))
	{
		remove(self);
		fixer = world;
		bprint("};\n// End dump\n");
		return;
	}
	bprint("	make_way(");
	t.origin_x = rint(t.origin_x);
	t.origin_y = rint(t.origin_y);
	t.origin_z = rint(t.origin_z);
	h = vtos(t.origin);
	bprint(h);
	bprint(", '");
	h = ftos(t.target1.count);
	bprint(h);
	bprint(" ");
	h = ftos(t.target2.count);
	bprint(h);
	bprint(" ");
	h = ftos(t.target3.count);
	bprint(h);
	bprint("', ");
	h = ftos(t.target4.count);
	bprint(h);
	bprint(", ");
	h = ftos(t.b_aiflags);
	bprint(h);
	bprint(");\n");
	self.nextthink = (time + 0.01);
	self.enemy = t;
};

void() QCDumpWaypoints =
{
	bprint("/* QC Waypoint Dump - src/frikbot/map_");
	bprint(mapname);
	bprint(".qc\nFor instructions please read the\nreadme.html that comes with FrikBot */\n\nvoid(vector org, vector bit1, float bit4, float flargs) make_way;\n");
	bprint("// Ways by ");
	bprint(self.netname);
	bprint("\n\n");
	bprint("void() map_");
	bprint(mapname);
	bprint(" =\n{\n");
	if (!fixer)
	{
		fixer = spawn();
		fixer.nextthink = (time + 0.01);
		fixer.think = PrintQCWaypoint;
		fixer.enemy = world;
	}
};

void() PrintBSPWaypoint =
{
	local entity t;
	local string h;

	if ((self.enemy == world))
	{
		t = way_head;
	}
	else
	{
		t = self.enemy._next;
	}
	if ((t == world))
	{
		bprint("// End dump\n");
		remove(self);
		fixer = world;
		return;
	}
	bprint("{\n\"classname\" \"waypoint\"\n\"origin\" \"");
	t.origin_x = rint(t.origin_x);
	t.origin_y = rint(t.origin_y);
	t.origin_z = rint(t.origin_z);
	h = ftos(t.origin_x);
	bprint(h);
	bprint(" ");
	h = ftos(t.origin_y);
	bprint(h);
	bprint(" ");
	h = ftos(t.origin_z);
	bprint(h);
	if (t.target1.count)
	{
		bprint("\"\n\"b_pants\" \"");
		h = ftos(t.target1.count);
		bprint(h);
	}
	if (t.target2.count)
	{
		bprint("\"\n\"b_skill\" \"");
		h = ftos(t.target2.count);
		bprint(h);
	}
	if (t.target3.count)
	{
		bprint("\"\n\"b_shirt\" \"");
		h = ftos(t.target3.count);
		bprint(h);
	}
	if (t.target4.count)
	{
		bprint("\"\n\"b_frags\" \"");
		h = ftos(t.target4.count);
		bprint(h);
	}
	if (t.b_aiflags)
	{
		bprint("\"\n\"b_aiflags\" \"");
		h = ftos(t.b_aiflags);
		bprint(h);
	}
	bprint("\"\n}\n");
	self.nextthink = (time + 0.01);
	self.enemy = t;
};

void() BSPDumpWaypoints =
{
	bprint("/* BSP entities Dump - maps/");
	bprint(mapname);
	bprint(".ent\nFor instructions please read the\nreadme.html that comes with FrikBot */\n\n");
	if (!fixer)
	{
		fixer = spawn();
		fixer.nextthink = (time + 0.01);
		fixer.think = PrintBSPWaypoint;
		fixer.enemy = world;
	}
};

// Keep legacy builtin stubs matching defs_custom.qc forward declarations (unused; SaveWaypoint/SaveWays use dpextensions fopen/fclose/fputs).
string(string s1, optional string s2, optional string s3, optional string s4, optional string s5, optional string s6, optional string s7, optional string s8) strcat = #115; 
__variant(...) open = #86; 
void(entity killer, entity killee) zone = #79; 
string(entity e, string key) unzone = #80; 
__variant(...) close = #87; 
__variant(...) write = #89; 

void() SaveWaypoint =
{
	local entity t;
	local float needcolon;
	local string h;
	local string j;

	if ((self.enemy == world))
	{
		t = way_head;
	}
	else
	{
		t = self.enemy._next;
	}
	if ((bytecounter >= 8000))
	{
		j = ftos(filecount);
		h = strcat("maps/", mapname, ".wa", j);
		fputs(file, "exec ");
		fputs(file, h);
		fputs(file, "\n");
		filecount = filecount + 1;
		fclose(file);
		file = fopen(h, 2);
		if ((file < 0))
		{
			remove(self);
			fixer = world;
			bprint("Error: failed to save file\n");
			return;
		}
		bytecounter = 0;
	}
	if ((t == world))
	{
		remove(self);
		fixer = world;
		fputs(file, "saved4 3\n");
		fclose(file);
		bprint("waypoints saved.\n");
		bytecounter = bytecounter + 27;
		return;
	}
	t.origin_x = rint(t.origin_x);
	t.origin_y = rint(t.origin_y);
	t.origin_z = rint(t.origin_z);
	if (((t.origin_x != saved1) || (t.count == 1)))
	{
		fputs(file, /*7106i*/"saved1 ");
		h = ftos(t.origin_x);
		fputs(file, h);
		saved1 = t.origin_x;
		bytecounter = bytecounter + 12;
		needcolon = TRUE;
	}
	if (((t.origin_y != saved2) || (t.count == 1)))
	{
		if (needcolon)
		{
			fputs(file, /*7114i*/"; ");
			bytecounter = bytecounter + 2;
		}
		else
		{
			needcolon = TRUE;
		}
		fputs(file, /*7117i*/"saved2 ");
		h = ftos(t.origin_y);
		fputs(file, h);
		bytecounter = bytecounter + 12;
		saved2 = t.origin_y;
	}
	if (((t.origin_z != saved3) || (t.count == 1)))
	{
		if (needcolon)
		{
			fputs(file, /*7114i*/"; ");
			bytecounter = bytecounter + 2;
		}
		else
		{
			needcolon = TRUE;
		}
		fputs(file, /*7125i*/"saved3 ");
		h = ftos(t.origin_z);
		fputs(file, h);
		bytecounter = bytecounter + 12;
		saved3 = t.origin_z;
	}
	if (needcolon)
	{
		bytecounter = bytecounter + 1;
		fputs(file, /*1199i*/"\n");
		needcolon = 0;
	}
	if (((scratch1 != t.target1.count) || (t.count == 1)))
	{
		needcolon = TRUE;
		fputs(file, /*7133i*/"scratch1 ");
		bytecounter = bytecounter + 14;
		h = ftos(t.target1.count);
		fputs(file, h);
		scratch1 = t.target1.count;
	}
	if (((scratch2 != t.target2.count) || (t.count == 1)))
	{
		if (needcolon)
		{
			fputs(file, /*7114i*/"; ");
			bytecounter = bytecounter + 2;
		}
		else
		{
			needcolon = TRUE;
		}
		fputs(file, /*7143i*/"scratch2 ");
		bytecounter = bytecounter + 14;
		h = ftos(t.target2.count);
		fputs(file, h);
		scratch2 = t.target2.count;
	}
	if (((scratch3 != t.target3.count) || (t.count == 1)))
	{
		if (needcolon)
		{
			fputs(file, /*7114i*/"; ");
			bytecounter = bytecounter + 2;
		}
		else
		{
			needcolon = TRUE;
		}
		fputs(file, /*7153i*/"scratch3 ");
		bytecounter = bytecounter + 14;
		h = ftos(t.target3.count);
		fputs(file, h);
		scratch3 = t.target3.count;
	}
	if (((scratch4 != t.target4.count) || (t.count == 1)))
	{
		if (needcolon)
		{
			fputs(file, /*7114i*/"; ");
			bytecounter = bytecounter + 2;
		}
		else
		{
			needcolon = TRUE;
		}
		fputs(file, /*7163i*/"scratch4 ");
		bytecounter = bytecounter + 14;
		h = ftos(t.target4.count);
		fputs(file, h);
		scratch4 = t.target4.count;
	}
	if (needcolon)
	{
		fputs(file, /*1199i*/"\n");
		needcolon = 0;
	}
	fputs(file, /*7173i*/"saved4 ");
	bytecounter = bytecounter + 19;
	if ((t.count != 1))
	{
		h = ftos(((t.b_aiflags * 4) + 2));
	}
	else
	{
		h = ftos(((t.b_aiflags * 4) + 1));
	}
	fputs(file, h);
	fputs(file, /*7181i*/"; wait\n");
	self.nextthink = (time + 0.01);
	self.enemy = t;
};

void() SaveWays =
{
	local string h;

	bytecounter = 50;
	filecount = 1;
	h = strcat("maps/", mapname, ".way");
	file = fopen(h, 2);
	if ((file < 0))
	{
		bprint("Error: failed to open file\n");
		return;
	}
	if (!fixer)
	{
		fixer = spawn();
		fixer.nextthink = (time + 0.01);
		fixer.think = SaveWaypoint;
		fixer.enemy = world;
	}
};
