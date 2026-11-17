//Decompiled code. Please respect the original copyright.

void() Clone =
{
	local entity clone;
	local entity head;
	local float done;
	local float c;
	local float proceed;
	local vector ang;
	local vector pos;
	local vector checkforlavaslime;
	local float zufall;

	done = 0;
	c = 0;
	ang = self.angles;
	while ((done == 0))
	{
		makevectors(ang);
		pos = (self.origin + (60 * v_forward)) + ((crandom() * 33) * v_right);
		head = findradius(pos, 35);
		proceed = 1;
		while (head)
		{
			if (((head.health > 0) && (head.flags & 40)))
			{
				proceed = 0;
			}
			head = head.chain;
		}
		traceline(self.origin, pos, FALSE, self);
		if (((trace_fraction == 1) && (proceed == 1)))
		{
			traceline(self.origin, (pos - '40 40 0'), FALSE, self);
			if ((trace_fraction == 1))
			{
				traceline(self.origin, (pos + '40 40 0'), FALSE, self);
				if ((trace_fraction == 1))
				{
					traceline(self.origin, (pos + '0 0 64'), FALSE, self);
					if ((trace_fraction == 1))
					{
						traceline(self.origin, (pos - '0 0 64'), FALSE, self);
						if ((trace_fraction != 1))
						{
							traceline(pos, (pos - '0 0 64'), FALSE, self);
							checkforlavaslime = trace_endpos;
							if (((pointcontents(checkforlavaslime) != CONTENT_SLIME) && (pointcontents(checkforlavaslime) != CONTENT_LAVA)))
							{
								done = 1;
							}
						}
					}
				}
			}
		}
		if ((done == 0))
		{
			c = c + 1;
			if ((c == 10))
			{
				return;
			}
		}
	}
	clone = spawn();
	copyentity(self, clone);
	total_monsters = total_monsters + 1;
	setorigin(clone, pos);
	if ((clone.monstermodel == 2))
	{
		if ((clone.skin == 0))
		{
			clone.skin = 1;
		}
		else
		{
			clone.skin = 0;
		}
		return;
	}
	if ((clone.multiskin == 1))
	{
		if ((random() >= 0.5))
		{
			clone.skin = 0;
		}
		else
		{
			clone.skin = 1;
		}
	}
	else
	{
		if ((clone.multiskin == 2))
		{
			if ((random() >= 0.5))
			{
				if ((clone.monstermodel == 0))
				{
					return;
				}
				else
				{
					if ((clone.classname == "monster_demon1"))
					{
						setmodel(clone, "progs/demon.mdl");
						setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
					}
					else
					{
						if ((clone.classname == "monster_dog"))
						{
							setmodel(clone, "progs/dog.mdl");
							setsize(clone, VEC_HULL2_MIN, '32 32 40');
						}
						else
						{
							if ((clone.classname == "monster_enforcer"))
							{
								setmodel(clone, "progs/enforcer.mdl");
								setsize(clone, VEC_HULL_MIN, '16 16 40');
							}
							else
							{
								if ((clone.classname == "monster_hell_knight"))
								{
									setmodel(clone, "progs/hknight.mdl");
									setsize(clone, VEC_HULL_MIN, '16 16 40');
								}
								else
								{
									if ((clone.classname == "monster_knight"))
									{
										setmodel(clone, "progs/knight.mdl");
										setsize(clone, VEC_HULL_MIN, '16 16 40');
									}
									else
									{
										if ((clone.classname == "monster_ogre"))
										{
											setmodel(clone, "progs/ogre.mdl");
											setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
										}
										else
										{
											if ((clone.classname == "monster_shalrath"))
											{
												setmodel(clone, "progs/shalrath.mdl");
												setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
											}
											else
											{
												if ((clone.classname == "monster_shambler"))
												{
													setmodel(clone, "progs/shambler.mdl");
													setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
												}
												else
												{
													if ((clone.classname == "monster_army"))
													{
														setmodel(clone, "progs/soldier.mdl");
														setsize(clone, VEC_HULL_MIN, '16 16 40');
													}
													else
													{
														if ((clone.classname == "monster_tarbaby"))
														{
															setmodel(clone, "progs/tarbaby.mdl");
															setsize(clone, VEC_HULL_MIN, '16 16 40');
														}
														else
														{
															if ((clone.classname == "monster_zombie"))
															{
																setmodel(clone, "progs/zombie.mdl");
																setsize(clone, VEC_HULL_MIN, '16 16 40');
															}
															else
															{
																return;
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
					clone.monstermodel = 0;
				}
			}
			else
			{
				if ((clone.monstermodel == 1))
				{
					return;
				}
				else
				{
					if ((clone.classname == "monster_demon1"))
					{
						setmodel(clone, "progs/demon1.mdl");
						setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
					}
					else
					{
						if ((clone.classname == "monster_dog"))
						{
							setmodel(clone, "progs/dog1.mdl");
							setsize(clone, VEC_HULL2_MIN, '32 32 40');
						}
						else
						{
							if ((clone.classname == "monster_enforcer"))
							{
								setmodel(clone, "progs/enforcer1.mdl");
								setsize(clone, VEC_HULL_MIN, '16 16 40');
							}
							else
							{
								if ((clone.classname == "monster_hell_knight"))
								{
									setmodel(clone, "progs/hknight1.mdl");
									setsize(clone, VEC_HULL_MIN, '16 16 40');
								}
								else
								{
									if ((clone.classname == "monster_knight"))
									{
										setmodel(clone, "progs/knight1.mdl");
										setsize(clone, VEC_HULL_MIN, '16 16 40');
									}
									else
									{
										if ((clone.classname == "monster_ogre"))
										{
											setmodel(clone, "progs/ogre1.mdl");
											setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
										}
										else
										{
											if ((clone.classname == "monster_shalrath"))
											{
												setmodel(clone, "progs/shalrath1.mdl");
												setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
											}
											else
											{
												if ((clone.classname == "monster_shambler"))
												{
													setmodel(clone, "progs/shambler1.mdl");
													setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
												}
												else
												{
													if ((clone.classname == "monster_army"))
													{
														setmodel(clone, "progs/soldier1.mdl");
														setsize(clone, VEC_HULL_MIN, '16 16 40');
													}
													else
													{
														if ((clone.classname == "monster_tarbaby"))
														{
															setmodel(clone, "progs/tarbaby1.mdl");
															setsize(clone, VEC_HULL_MIN, '16 16 40');
														}
														else
														{
															if ((clone.classname == "monster_zombie"))
															{
																setmodel(clone, "progs/zombie1.mdl");
																setsize(clone, VEC_HULL_MIN, '16 16 40');
															}
															else
															{
																return;
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
					clone.monstermodel = 1;
				}
			}
		}
		else
		{
			if ((clone.multiskin == 3))
			{
				zufall = random();
				if ((zufall > 0.66))
				{
					if (((clone.monstermodel == 0) && (clone.skin == 0)))
					{
						return;
					}
					else
					{
						if ((clone.monstermodel == 0))
						{
							clone.skin = 0;
							return;
						}
						else
						{
							if ((clone.classname == "monster_demon1"))
							{
								setmodel(clone, "progs/demon.mdl");
								setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
							}
							else
							{
								if ((clone.classname == "monster_dog"))
								{
									setmodel(clone, "progs/dog.mdl");
									setsize(clone, VEC_HULL2_MIN, '32 32 40');
								}
								else
								{
									if ((clone.classname == "monster_enforcer"))
									{
										setmodel(clone, "progs/enforcer.mdl");
										setsize(clone, VEC_HULL_MIN, '16 16 40');
									}
									else
									{
										if ((clone.classname == "monster_hell_knight"))
										{
											setmodel(clone, "progs/hknight.mdl");
											setsize(clone, VEC_HULL_MIN, '16 16 40');
										}
										else
										{
											if ((clone.classname == "monster_knight"))
											{
												setmodel(clone, "progs/knight.mdl");
												setsize(clone, VEC_HULL_MIN, '16 16 40');
											}
											else
											{
												if ((clone.classname == "monster_ogre"))
												{
													setmodel(clone, "progs/ogre.mdl");
													setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
												}
												else
												{
													if ((clone.classname == "monster_shalrath"))
													{
														setmodel(clone, "progs/shalrath.mdl");
														setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
													}
													else
													{
														if ((clone.classname == "monster_shambler"))
														{
															setmodel(clone, "progs/shambler.mdl");
															setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
														}
														else
														{
															if ((clone.classname == "monster_army"))
															{
																setmodel(clone, "progs/soldier.mdl");
																setsize(clone, VEC_HULL_MIN, '16 16 40');
															}
															else
															{
																if ((clone.classname == "monster_tarbaby"))
																{
																	setmodel(clone, "progs/tarbaby.mdl");
																	setsize(clone, VEC_HULL_MIN, '16 16 40');
																}
																else
																{
																	if ((clone.classname == "monster_zombie"))
																	{
																		setmodel(clone, "progs/zombie.mdl");
																		setsize(clone, VEC_HULL_MIN, '16 16 40');
																	}
																	else
																	{
																		return;
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
							clone.monstermodel = 0;
						}
					}
				}
				else
				{
					if ((zufall < 0.34))
					{
						if (((clone.monstermodel == 0) && (clone.skin == 1)))
						{
							return;
						}
						else
						{
							if ((clone.monstermodel == 0))
							{
								clone.skin = 1;
								return;
							}
							else
							{
								if ((clone.classname == "monster_demon1"))
								{
									setmodel(clone, "progs/demon.mdl");
									setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
								}
								else
								{
									if ((clone.classname == "monster_dog"))
									{
										setmodel(clone, "progs/dog.mdl");
										setsize(clone, VEC_HULL2_MIN, '32 32 40');
									}
									else
									{
										if ((clone.classname == "monster_enforcer"))
										{
											setmodel(clone, "progs/enforcer.mdl");
											setsize(clone, VEC_HULL_MIN, '16 16 40');
										}
										else
										{
											if ((clone.classname == "monster_hell_knight"))
											{
												setmodel(clone, "progs/hknight.mdl");
												setsize(clone, VEC_HULL_MIN, '16 16 40');
											}
											else
											{
												if ((clone.classname == "monster_knight"))
												{
													setmodel(clone, "progs/knight.mdl");
													setsize(clone, VEC_HULL_MIN, '16 16 40');
												}
												else
												{
													if ((clone.classname == "monster_ogre"))
													{
														setmodel(clone, "progs/ogre.mdl");
														setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
													}
													else
													{
														if ((clone.classname == "monster_shalrath"))
														{
															setmodel(clone, "progs/shalrath.mdl");
															setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
														}
														else
														{
															if ((clone.classname == "monster_shambler"))
															{
																setmodel(clone, "progs/shambler.mdl");
																setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
															}
															else
															{
																if ((clone.classname == "monster_army"))
																{
																	setmodel(clone, "progs/soldier.mdl");
																	setsize(clone, VEC_HULL_MIN, '16 16 40');
																}
																else
																{
																	if ((clone.classname == "monster_tarbaby"))
																	{
																		setmodel(clone, "progs/tarbaby.mdl");
																		setsize(clone, VEC_HULL_MIN, '16 16 40');
																	}
																	else
																	{
																		if ((clone.classname == "monster_zombie"))
																		{
																			setmodel(clone, "progs/zombie.mdl");
																			setsize(clone, VEC_HULL_MIN, '16 16 40');
																		}
																		else
																		{
																			return;
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
								clone.monstermodel = 0;
								clone.skin = 1;
							}
						}
					}
					else
					{
						if (((clone.monstermodel == 1) && (clone.skin == 0)))
						{
							return;
						}
						else
						{
							if ((clone.classname == "monster_demon1"))
							{
								setmodel(clone, "progs/demon1.mdl");
								setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
							}
							else
							{
								if ((clone.classname == "monster_dog"))
								{
									setmodel(clone, "progs/dog1.mdl");
									setsize(clone, VEC_HULL2_MIN, '32 32 40');
								}
								else
								{
									if ((clone.classname == "monster_enforcer"))
									{
										setmodel(clone, "progs/enforcer1.mdl");
										setsize(clone, VEC_HULL_MIN, '16 16 40');
									}
									else
									{
										if ((clone.classname == "monster_hell_knight"))
										{
											setmodel(clone, "progs/hknight1.mdl");
											setsize(clone, VEC_HULL_MIN, '16 16 40');
										}
										else
										{
											if ((clone.classname == "monster_knight"))
											{
												setmodel(clone, "progs/knight1.mdl");
												setsize(clone, VEC_HULL_MIN, '16 16 40');
											}
											else
											{
												if ((clone.classname == "monster_ogre"))
												{
													setmodel(clone, "progs/ogre1.mdl");
													setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
												}
												else
												{
													if ((clone.classname == "monster_shalrath"))
													{
														setmodel(clone, "progs/shalrath1.mdl");
														setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
													}
													else
													{
														if ((clone.classname == "monster_shambler"))
														{
															setmodel(clone, "progs/shambler1.mdl");
															setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
														}
														else
														{
															if ((clone.classname == "monster_army"))
															{
																setmodel(clone, "progs/soldier1.mdl");
																setsize(clone, VEC_HULL_MIN, '16 16 40');
															}
															else
															{
																if ((clone.classname == "monster_tarbaby"))
																{
																	setmodel(clone, "progs/tarbaby1.mdl");
																	setsize(clone, VEC_HULL_MIN, '16 16 40');
																}
																else
																{
																	if ((clone.classname == "monster_zombie"))
																	{
																		setmodel(clone, "progs/zombie1.mdl");
																		setsize(clone, VEC_HULL_MIN, '16 16 40');
																	}
																	else
																	{
																		return;
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
							clone.monstermodel = 1;
							clone.skin = 0;
						}
					}
				}
			}
			else
			{
				if ((clone.multiskin == 4))
				{
					zufall = random();
					if ((zufall > 0.75))
					{
						if (((clone.monstermodel == 0) && (clone.skin == 0)))
						{
							return;
						}
						else
						{
							if ((clone.monstermodel == 0))
							{
								clone.skin = 0;
								return;
							}
							else
							{
								if ((clone.classname == "monster_demon1"))
								{
									setmodel(clone, "progs/demon.mdl");
									setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
								}
								else
								{
									if ((clone.classname == "monster_dog"))
									{
										setmodel(clone, "progs/dog.mdl");
										setsize(clone, VEC_HULL2_MIN, '32 32 40');
									}
									else
									{
										if ((clone.classname == "monster_enforcer"))
										{
											setmodel(clone, "progs/enforcer.mdl");
											setsize(clone, VEC_HULL_MIN, '16 16 40');
										}
										else
										{
											if ((clone.classname == "monster_hell_knight"))
											{
												setmodel(clone, "progs/hknight.mdl");
												setsize(clone, VEC_HULL_MIN, '16 16 40');
											}
											else
											{
												if ((clone.classname == "monster_knight"))
												{
													setmodel(clone, "progs/knight.mdl");
													setsize(clone, VEC_HULL_MIN, '16 16 40');
												}
												else
												{
													if ((clone.classname == "monster_ogre"))
													{
														setmodel(clone, "progs/ogre.mdl");
														setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
													}
													else
													{
														if ((clone.classname == "monster_shalrath"))
														{
															setmodel(clone, "progs/shalrath.mdl");
															setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
														}
														else
														{
															if ((clone.classname == "monster_shambler"))
															{
																setmodel(clone, "progs/shambler.mdl");
																setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
															}
															else
															{
																if ((clone.classname == "monster_army"))
																{
																	setmodel(clone, "progs/soldier.mdl");
																	setsize(clone, VEC_HULL_MIN, '16 16 40');
																}
																else
																{
																	if ((clone.classname == "monster_tarbaby"))
																	{
																		setmodel(clone, "progs/tarbaby.mdl");
																		setsize(clone, VEC_HULL_MIN, '16 16 40');
																	}
																	else
																	{
																		if ((clone.classname == "monster_zombie"))
																		{
																			setmodel(clone, "progs/zombie.mdl");
																			setsize(clone, VEC_HULL_MIN, '16 16 40');
																		}
																		else
																		{
																			return;
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
								clone.monstermodel = 0;
								clone.skin = 0;
							}
						}
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							if (((clone.monstermodel == 0) && (clone.skin == 1)))
							{
								return;
							}
							else
							{
								if ((clone.monstermodel == 0))
								{
									clone.skin = 1;
									return;
								}
								else
								{
									if ((clone.classname == "monster_demon1"))
									{
										setmodel(clone, "progs/demon.mdl");
										setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
									}
									else
									{
										if ((clone.classname == "monster_dog"))
										{
											setmodel(clone, "progs/dog.mdl");
											setsize(clone, VEC_HULL2_MIN, '32 32 40');
										}
										else
										{
											if ((clone.classname == "monster_enforcer"))
											{
												setmodel(clone, "progs/enforcer.mdl");
												setsize(clone, VEC_HULL_MIN, '16 16 40');
											}
											else
											{
												if ((clone.classname == "monster_hell_knight"))
												{
													setmodel(clone, "progs/hknight.mdl");
													setsize(clone, VEC_HULL_MIN, '16 16 40');
												}
												else
												{
													if ((clone.classname == "monster_knight"))
													{
														setmodel(clone, "progs/knight.mdl");
														setsize(clone, VEC_HULL_MIN, '16 16 40');
													}
													else
													{
														if ((clone.classname == "monster_ogre"))
														{
															setmodel(clone, "progs/ogre.mdl");
															setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
														}
														else
														{
															if ((clone.classname == "monster_shalrath"))
															{
																setmodel(clone, "progs/shalrath.mdl");
																setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
															}
															else
															{
																if ((clone.classname == "monster_shambler"))
																{
																	setmodel(clone, "progs/shambler.mdl");
																	setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
																}
																else
																{
																	if ((clone.classname == "monster_army"))
																	{
																		setmodel(clone, "progs/soldier.mdl");
																		setsize(clone, VEC_HULL_MIN, '16 16 40');
																	}
																	else
																	{
																		if ((clone.classname == "monster_tarbaby"))
																		{
																			setmodel(clone, "progs/tarbaby.mdl");
																			setsize(clone, VEC_HULL_MIN, '16 16 40');
																		}
																		else
																		{
																			if ((clone.classname == "monster_zombie"))
																			{
																				setmodel(clone, "progs/zombie.mdl");
																				setsize(clone, VEC_HULL_MIN, '16 16 40');
																			}
																			else
																			{
																				return;
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
									clone.monstermodel = 0;
									clone.skin = 1;
								}
							}
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								if (((clone.monstermodel == 1) && (clone.skin == 0)))
								{
									return;
								}
								else
								{
									if ((clone.monstermodel == 1))
									{
										clone.skin = 0;
										return;
									}
									else
									{
										if ((clone.classname == "monster_demon1"))
										{
											setmodel(clone, "progs/demon1.mdl");
											setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
										}
										else
										{
											if ((clone.classname == "monster_dog"))
											{
												setmodel(clone, "progs/dog1.mdl");
												setsize(clone, VEC_HULL2_MIN, '32 32 40');
											}
											else
											{
												if ((clone.classname == "monster_enforcer"))
												{
													setmodel(clone, "progs/enforcer1.mdl");
													setsize(clone, VEC_HULL_MIN, '16 16 40');
												}
												else
												{
													if ((clone.classname == "monster_hell_knight"))
													{
														setmodel(clone, "progs/hknight1.mdl");
														setsize(clone, VEC_HULL_MIN, '16 16 40');
													}
													else
													{
														if ((clone.classname == "monster_knight"))
														{
															setmodel(clone, "progs/knight1.mdl");
															setsize(clone, VEC_HULL_MIN, '16 16 40');
														}
														else
														{
															if ((clone.classname == "monster_ogre"))
															{
																setmodel(clone, "progs/ogre1.mdl");
																setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
															}
															else
															{
																if ((clone.classname == "monster_shalrath"))
																{
																	setmodel(clone, "progs/shalrath1.mdl");
																	setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
																}
																else
																{
																	if ((clone.classname == "monster_shambler"))
																	{
																		setmodel(clone, "progs/shambler1.mdl");
																		setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
																	}
																	else
																	{
																		if ((clone.classname == "monster_army"))
																		{
																			setmodel(clone, "progs/soldier1.mdl");
																			setsize(clone, VEC_HULL_MIN, '16 16 40');
																		}
																		else
																		{
																			if ((clone.classname == "monster_tarbaby"))
																			{
																				setmodel(clone, "progs/tarbaby1.mdl");
																				setsize(clone, VEC_HULL_MIN, '16 16 40');
																			}
																			else
																			{
																				if ((clone.classname == "monster_zombie"))
																				{
																					setmodel(clone, "progs/zombie1.mdl");
																					setsize(clone, VEC_HULL_MIN, '16 16 40');
																				}
																				else
																				{
																					return;
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
										clone.monstermodel = 1;
										clone.skin = 0;
									}
								}
							}
							else
							{
								if (((clone.monstermodel == 1) && (clone.skin == 1)))
								{
									return;
								}
								else
								{
									if ((clone.monstermodel == 1))
									{
										clone.skin = 1;
										return;
									}
									else
									{
										if ((clone.classname == "monster_demon1"))
										{
											setmodel(clone, "progs/demon1.mdl");
											setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
										}
										else
										{
											if ((clone.classname == "monster_dog"))
											{
												setmodel(clone, "progs/dog1.mdl");
												setsize(clone, VEC_HULL2_MIN, '32 32 40');
											}
											else
											{
												if ((clone.classname == "monster_enforcer"))
												{
													setmodel(clone, "progs/enforcer1.mdl");
													setsize(clone, VEC_HULL_MIN, '16 16 40');
												}
												else
												{
													if ((clone.classname == "monster_hell_knight"))
													{
														setmodel(clone, "progs/hknight1.mdl");
														setsize(clone, VEC_HULL_MIN, '16 16 40');
													}
													else
													{
														if ((clone.classname == "monster_knight"))
														{
															setmodel(clone, "progs/knight1.mdl");
															setsize(clone, VEC_HULL_MIN, '16 16 40');
														}
														else
														{
															if ((clone.classname == "monster_ogre"))
															{
																setmodel(clone, "progs/ogre1.mdl");
																setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
															}
															else
															{
																if ((clone.classname == "monster_shalrath"))
																{
																	setmodel(clone, "progs/shalrath1.mdl");
																	setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
																}
																else
																{
																	if ((clone.classname == "monster_shambler"))
																	{
																		setmodel(clone, "progs/shambler1.mdl");
																		setsize(clone, VEC_HULL2_MIN, VEC_HULL2_MAX);
																	}
																	else
																	{
																		if ((clone.classname == "monster_army"))
																		{
																			setmodel(clone, "progs/soldier1.mdl");
																			setsize(clone, VEC_HULL_MIN, '16 16 40');
																		}
																		else
																		{
																			if ((clone.classname == "monster_tarbaby"))
																			{
																				setmodel(clone, "progs/tarbaby1.mdl");
																				setsize(clone, VEC_HULL_MIN, '16 16 40');
																			}
																			else
																			{
																				if ((clone.classname == "monster_zombie"))
																				{
																					setmodel(clone, "progs/zombie1.mdl");
																					setsize(clone, VEC_HULL_MIN, '16 16 40');
																				}
																				else
																				{
																					return;
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
										clone.monstermodel = 1;
										clone.skin = 1;
									}
								}
							}
						}
					}
				}
				else
				{
				}
			}
		}
	}
};

void() do_the_cloning =
{
	if ((autocvar_clonemonsters <= self.clone_me))
	{
		return;
	}
	else
	{
		Clone();
	}
	self.clone_me = (self.clone_me + 1);
	do_the_cloning();
};

void() Clone_fly_swim =
{
	local entity clone;
	local entity head;
	local float done;
	local float c;
	local float proceed;
	local vector ang;
	local vector pos;
	local float zufall;

	done = 0;
	c = 0;
	ang = self.angles;
	while ((done == 0))
	{
		makevectors(ang);
		pos = ((self.origin + (60 * v_forward)) + ((crandom() * 33) * v_right)) + ((crandom() * 25) * v_up);
		head = findradius(pos, 35);
		proceed = 1;
		while (head)
		{
			if (((head.health > 0) && (head.flags & 40)))
			{
				proceed = 0;
			}
			head = head.chain;
		}
		traceline(self.origin, pos, FALSE, self);
		if (((trace_fraction == 1) && (proceed == 1)))
		{
			traceline(self.origin, (pos - '40 40 0'), FALSE, self);
			if ((trace_fraction == 1))
			{
				traceline(self.origin, (pos + '40 40 0'), FALSE, self);
				if ((trace_fraction == 1))
				{
					done = 1;
				}
			}
		}
		if ((done == 0))
		{
			c = c + 1;
			if ((c == 10))
			{
				return;
			}
		}
	}
	clone = spawn();
	copyentity(self, clone);
	total_monsters = total_monsters + 1;
	setorigin(clone, pos);
	if ((clone.multiskin == 1))
	{
		if ((random() >= 0.5))
		{
			clone.skin = 0;
		}
		else
		{
			clone.skin = 1;
		}
	}
	else
	{
		if ((clone.multiskin == 2))
		{
			if ((random() >= 0.5))
			{
				if ((clone.monstermodel == 0))
				{
					return;
				}
				else
				{
					if ((clone.classname == "monster_fish"))
					{
						setmodel(clone, "progs/fish.mdl");
						setsize(clone, VEC_HULL_MIN, '16 16 24');
					}
					else
					{
						if ((clone.classname == "monster_wizard"))
						{
							setmodel(clone, "progs/wizard.mdl");
							setsize(clone, VEC_HULL_MIN, '16 16 40');
						}
						else
						{
							return;
						}
					}
					clone.monstermodel = 0;
				}
			}
			else
			{
				if ((clone.monstermodel == 1))
				{
					return;
				}
				else
				{
					if ((clone.classname == "monster_fish"))
					{
						setmodel(clone, "progs/fish1.mdl");
						setsize(clone, VEC_HULL_MIN, '16 16 24');
					}
					else
					{
						if ((clone.classname == "monster_wizard"))
						{
							setmodel(clone, "progs/wizard1.mdl");
							setsize(clone, VEC_HULL_MIN, '16 16 40');
						}
						else
						{
							return;
						}
					}
					clone.monstermodel = 1;
				}
			}
		}
		else
		{
			if ((clone.multiskin == 3))
			{
				zufall = random();
				if ((zufall > 0.66))
				{
					if (((clone.monstermodel == 0) && (clone.skin == 0)))
					{
						return;
					}
					else
					{
						if ((clone.monstermodel == 0))
						{
							clone.skin = 0;
							return;
						}
						else
						{
							if ((clone.classname == "monster_fish"))
							{
								setmodel(clone, "progs/fish.mdl");
								setsize(clone, VEC_HULL_MIN, '16 16 24');
							}
							else
							{
								if ((clone.classname == "monster_wizard"))
								{
									setmodel(clone, "progs/wizard.mdl");
									setsize(clone, VEC_HULL_MIN, '16 16 40');
								}
								else
								{
									return;
								}
							}
							clone.monstermodel = 0;
						}
					}
				}
				else
				{
					if ((zufall < 0.34))
					{
						if (((clone.monstermodel == 0) && (clone.skin == 1)))
						{
							return;
						}
						else
						{
							if ((clone.monstermodel == 0))
							{
								clone.skin = 1;
								return;
							}
							else
							{
								if ((clone.classname == "monster_fish"))
								{
									setmodel(clone, "progs/fish.mdl");
									setsize(clone, VEC_HULL_MIN, '16 16 24');
								}
								else
								{
									if ((clone.classname == "monster_wizard"))
									{
										setmodel(clone, "progs/wizard.mdl");
										setsize(clone, VEC_HULL_MIN, '16 16 40');
									}
									else
									{
										return;
									}
								}
								clone.monstermodel = 0;
								clone.skin = 1;
							}
						}
					}
					else
					{
						if (((clone.monstermodel == 1) && (clone.skin == 0)))
						{
							return;
						}
						else
						{
							if ((clone.classname == "monster_fish"))
							{
								setmodel(clone, "progs/fish1.mdl");
								setsize(clone, VEC_HULL_MIN, '16 16 24');
							}
							else
							{
								if ((clone.classname == "monster_wizard"))
								{
									setmodel(clone, "progs/wizard1.mdl");
									setsize(clone, VEC_HULL_MIN, '16 16 40');
								}
								else
								{
									return;
								}
							}
							clone.monstermodel = 1;
							clone.skin = 0;
						}
					}
				}
			}
			else
			{
				if ((clone.multiskin == 4))
				{
					zufall = random();
					if ((zufall > 0.75))
					{
						if (((clone.monstermodel == 0) && (clone.skin == 0)))
						{
							return;
						}
						else
						{
							if ((clone.monstermodel == 0))
							{
								clone.skin = 0;
								return;
							}
							else
							{
								if ((clone.classname == "monster_fish"))
								{
									setmodel(clone, "progs/fish.mdl");
									setsize(clone, VEC_HULL_MIN, '16 16 24');
								}
								else
								{
									if ((clone.classname == "monster_wizard"))
									{
										setmodel(clone, "progs/wizard.mdl");
										setsize(clone, VEC_HULL_MIN, '16 16 40');
									}
									else
									{
										return;
									}
								}
								clone.monstermodel = 0;
								clone.skin = 0;
							}
						}
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							if (((clone.monstermodel == 0) && (clone.skin == 1)))
							{
								return;
							}
							else
							{
								if ((clone.monstermodel == 0))
								{
									clone.skin = 1;
									return;
								}
								else
								{
									if ((clone.classname == "monster_fish"))
									{
										setmodel(clone, "progs/fish.mdl");
										setsize(clone, VEC_HULL_MIN, '16 16 24');
									}
									else
									{
										if ((clone.classname == "monster_wizard"))
										{
											setmodel(clone, "progs/wizard.mdl");
											setsize(clone, VEC_HULL_MIN, '16 16 40');
										}
										else
										{
											return;
										}
									}
									clone.monstermodel = 0;
									clone.skin = 1;
								}
							}
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								if (((clone.monstermodel == 1) && (clone.skin == 0)))
								{
									return;
								}
								else
								{
									if ((clone.monstermodel == 1))
									{
										clone.skin = 0;
										return;
									}
									else
									{
										if ((clone.classname == "monster_fish"))
										{
											setmodel(clone, "progs/fish1.mdl");
											setsize(clone, VEC_HULL_MIN, '16 16 24');
										}
										else
										{
											if ((clone.classname == "monster_wizard"))
											{
												setmodel(clone, "progs/wizard1.mdl");
												setsize(clone, VEC_HULL_MIN, '16 16 40');
											}
											else
											{
												return;
											}
										}
										clone.monstermodel = 1;
										clone.skin = 0;
									}
								}
							}
							else
							{
								if (((clone.monstermodel == 1) && (clone.skin == 1)))
								{
									return;
								}
								else
								{
									if ((clone.monstermodel == 1))
									{
										clone.skin = 1;
										return;
									}
									else
									{
										if ((clone.classname == "monster_fish"))
										{
											setmodel(clone, "progs/fish1.mdl");
											setsize(clone, VEC_HULL_MIN, '16 16 24');
										}
										else
										{
											if ((clone.classname == "monster_wizard"))
											{
												setmodel(clone, "progs/wizard1.mdl");
												setsize(clone, VEC_HULL_MIN, '16 16 40');
											}
											else
											{
												return;
											}
										}
										clone.monstermodel = 1;
										clone.skin = 1;
									}
								}
							}
						}
					}
				}
				else
				{
				}
			}
		}
	}
};

void() do_the_cloning__fly_swim =
{
	if ((autocvar_clonemonsters <= self.clone_me))
	{
		return;
	}
	else
	{
		Clone_fly_swim();
	}
	self.clone_me = (self.clone_me + 1);
	do_the_cloning__fly_swim();
};
