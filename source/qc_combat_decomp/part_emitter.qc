//Decompiled code. Please respect the original copyright.

float(entity pe_ent) misc_particle_style =
{
	pe_ent.start_delay = (1 + (random() * 2));
	pe_ent.spr_frame = 1;
	pe_ent.dpp_name = "";
	pe_ent.dpp_wait = 0.1;
	pe_ent.dpp_rnd = 1;
	pe_ent.dpp_vel = VEC_ORIGIN;
	pe_ent.part_movetype = MOVETYPE_NOCLIP;
	if ((pe_ent.part_style == PARTICLE_STYLE_PORTAL))
	{
		pe_ent.spr_name1 = PART_DOTMED_GREY;
		pe_ent.spr_name2 = PART_DOTSML_WHITE;
		pe_ent.spr_name3 = PART_DOTSML_WHITE;
		pe_ent.spr_frame = 3;
		pe_ent.part_limit = 100;
		pe_ent.part_life = 3;
		pe_ent.part_ofs = VEC_ORIGIN;
		pe_ent.part_veltype = 0;
		if ((pe_ent.angles_y == -1))
		{
			pe_ent.part_vel = '0 0 20';
			pe_ent.dpp_name = DPP_PORTALUP;
		}
		else
		{
			if ((pe_ent.angles_y == -2))
			{
				pe_ent.part_vel = '0 0 -20';
				pe_ent.dpp_name = DPP_PORTALDOWN;
			}
			else
			{
				if (((pe_ent.angles_y == 90) || (pe_ent.angles_y == 270)))
				{
					if (!pe_ent.part_vol)
					{
						pe_ent.part_vol = '32 0 48';
					}
					pe_ent.dpp_name = DPP_PORTALSIDE;
				}
				else
				{
					if (!pe_ent.part_vol)
					{
						pe_ent.part_vol = '0 32 48';
					}
					pe_ent.dpp_name = DPP_PORTALFRONT;
				}
				makevectors(pe_ent.angles);
				pe_ent.part_vel = (v_forward * 20);
			}
		}
		if (!pe_ent.part_velrand)
		{
			pe_ent.part_velrand = '10 10 4';
		}
		if (!pe_ent.wakeup_dist)
		{
			pe_ent.wakeup_dist = 768;
		}
		pe_ent.wakeup_timer = 4;
		if (!pe_ent.spawn_base)
		{
			pe_ent.spawn_base = 0.1;
		}
		if (!pe_ent.spawn_rand)
		{
			pe_ent.spawn_rand = 0.1;
		}
		pe_ent.dpp_vel = normalize(pe_ent.part_vel);
	}
	else
	{
		if ((pe_ent.part_style == PARTICLE_STYLE_JUMPPAD))
		{
			pe_ent.spr_name1 = PART_DOTMED_GREY;
			pe_ent.spr_name2 = PART_DOTSML_WHITE;
			pe_ent.spr_name3 = PART_DOTSML_GOLD;
			pe_ent.part_limit = 100;
			pe_ent.part_life = 3;
			pe_ent.part_ofs = VEC_ORIGIN;
			pe_ent.part_velbase = '0 0 12';
			pe_ent.part_vel = '0 0 32';
			pe_ent.part_velrand = '8 8 0';
			pe_ent.part_vol = '24 24 0';
			pe_ent.part_veltype = 0;
			pe_ent.wakeup_dist = 1024;
			pe_ent.wakeup_timer = 2;
			pe_ent.spawn_base = 0.05;
			pe_ent.spawn_rand = 0.05;
			pe_ent.dpp_name = DPP_JUMPPAD;
		}
		else
		{
			if ((pe_ent.part_style == PARTICLE_STYLE_FCIRCLE))
			{
				pe_ent.spr_name1 = PART_TORCH1;
				pe_ent.spr_name2 = PART_TORCH2;
				pe_ent.spr_name3 = PART_DOTSML_GOLD;
				pe_ent.part_limit = 64;
				pe_ent.part_life = 5;
				pe_ent.part_ofs = '0 0 1';
				pe_ent.part_vel = '0 0 12';
				pe_ent.part_velrand = '4 4 0';
				if (CheckZeroVector(pe_ent.pemit_source.part_vol))
				{
					pe_ent.part_vol = '56 17 0';
				}
				pe_ent.part_veltype = PARTICLE_ORIGIN_RANDCIRCLE;
				pe_ent.wakeup_dist = 768;
				pe_ent.wakeup_timer = 0.5;
				if (!pe_ent.pemit_source.spawn_base)
				{
					pe_ent.spawn_base = 0.1;
				}
				if (!pe_ent.pemit_source.spawn_rand)
				{
					pe_ent.spawn_rand = 0.2;
				}
				pe_ent.dpp_name = DPP_FCIRCLE;
				pe_ent.dpp_rnd = 0.2;
			}
			else
			{
				if ((pe_ent.part_style == PARTICLE_STYLE_FFIELD))
				{
					if ((pe_ent.pemit_source.spr_frame == PARTICLE_BURST_YELLOW))
					{
						pe_ent.spr_name1 = PART_DOTSML_GOLD;
						pe_ent.spr_name2 = PART_DOTSML_YELLOW;
						pe_ent.spr_name3 = PART_DOTMED_YELLOW;
						pe_ent.dpp_name = DPP_FFIELDPARTY;
					}
					else
					{
						if ((pe_ent.pemit_source.spr_frame == PARTICLE_BURST_GREEN))
						{
							pe_ent.spr_name1 = PART_DOTSML_LGREEN;
							pe_ent.spr_name2 = PART_DOTSML_GREEN;
							pe_ent.spr_name3 = PART_DOTMED_GREEN;
							pe_ent.dpp_name = DPP_FFIELDPARTG;
						}
						else
						{
							if ((pe_ent.pemit_source.spr_frame == PARTICLE_BURST_RED))
							{
								pe_ent.spr_name1 = PART_DOTSML_GREY;
								pe_ent.spr_name2 = PART_DOTSML_RED;
								pe_ent.spr_name3 = PART_DOTMED_RED;
								pe_ent.dpp_name = DPP_FFIELDPARTR;
							}
							else
							{
								if ((pe_ent.pemit_source.spr_frame == PARTICLE_BURST_BLUE))
								{
									pe_ent.spr_name1 = PART_DOTSML_BLUE;
									pe_ent.spr_name2 = PART_DOTSML_GREY;
									pe_ent.spr_name3 = PART_DOTMED_BLUE;
									pe_ent.dpp_name = DPP_FFIELDPARTB;
								}
								else
								{
									if ((pe_ent.pemit_source.spr_frame == PARTICLE_BURST_PURPLE))
									{
										pe_ent.spr_name1 = PART_DOTSML_PURP;
										pe_ent.spr_name2 = PART_DOTSML_GREY;
										pe_ent.spr_name3 = PART_DOTMED_PURP;
										pe_ent.dpp_name = DPP_FFIELDPARTP;
									}
									else
									{
										if ((pe_ent.pemit_source.spr_frame == PARTICLE_BURST_FIRE))
										{
											pe_ent.spr_name1 = PART_TORCH1;
											pe_ent.spr_name2 = PART_DOTSML_GOLD;
											pe_ent.spr_name3 = PART_DOTMED_GREY;
											pe_ent.dpp_name = DPP_FFIELDPARTY;
										}
										else
										{
											pe_ent.spr_name1 = PART_DOTSML_WHITE;
											pe_ent.spr_name2 = PART_DOTSML_GREY;
											pe_ent.spr_name3 = PART_DOTMED_GREY;
											pe_ent.dpp_name = DPP_FFIELDPARTW;
										}
									}
								}
							}
						}
					}
					pe_ent.spr_frame = 0;
					if (!pe_ent.pemit_source.part_limit)
					{
						pe_ent.part_limit = 25;
					}
					else
					{
						pe_ent.part_limit = pe_ent.pemit_source.part_limit;
					}
					if (!pe_ent.pemit_source.part_life)
					{
						pe_ent.part_life = 2;
					}
					else
					{
						pe_ent.part_life = pe_ent.pemit_source.part_life;
					}
					if (!pe_ent.pemit_source.part_ofs)
					{
						pe_ent.part_ofs = VEC_ORIGIN;
					}
					else
					{
						pe_ent.part_ofs = pe_ent.pemit_source.part_ofs;
					}
					pe_ent.part_veltype = 0;
					if (!pe_ent.part_velrand)
					{
						pe_ent.part_velrand = '4 4 4';
					}
					if (CheckZeroVector(pe_ent.pemit_source.part_vol))
					{
						pe_ent.part_vol = '8 8 8';
					}
					else
					{
						pe_ent.part_vol = pe_ent.pemit_source.part_vol;
					}
					if (CheckZeroVector(pe_ent.pemit_source.part_vel))
					{
						pe_ent.part_vel = '0 0 4';
					}
					else
					{
						pe_ent.part_vel = pe_ent.pemit_source.part_vel;
					}
					if (!pe_ent.pemit_source.wakeup_dist)
					{
						pe_ent.wakeup_dist = 768;
					}
					pe_ent.wakeup_timer = 4;
					if (!pe_ent.pemit_source.spawn_base)
					{
						pe_ent.spawn_base = 0.05;
					}
					if ((pe_ent.spawn_base < 0.01))
					{
						pe_ent.spawn_base = 0.01;
					}
					if (!pe_ent.pemit_source.spawn_rand)
					{
						pe_ent.spawn_rand = 0.1;
					}
					pe_ent.dpp_vel = pe_ent.part_vel;
					pe_ent.dpp_wait = 0.01;
					pe_ent.dpp_rnd = 0.1;
				}
				else
				{
					if ((pe_ent.part_style == PARTICLE_STYLE_BOOK))
					{
						pe_ent.spr_name1 = PART_BOOKRUNE1;
						pe_ent.spr_name2 = PART_BOOKRUNE2;
						if ((random() < 0.5))
						{
							pe_ent.spr_name3 = PART_BOOKRUNE1;
						}
						else
						{
							pe_ent.spr_name3 = PART_BOOKRUNE2;
						}
						pe_ent.part_limit = 3;
						pe_ent.part_life = 7;
						pe_ent.part_ofs = '0 0 10';
						pe_ent.part_vel = '0 0 10';
						pe_ent.part_velrand = '4 4 0';
						pe_ent.part_velrot = 45;
						pe_ent.part_vol = '1 1 0';
						pe_ent.part_veltype = 0;
						pe_ent.wakeup_dist = 768;
						pe_ent.wakeup_timer = 8;
						pe_ent.spawn_base = 2;
						pe_ent.spawn_rand = 1;
						if ((pe_ent.pemit_source.style == MISCBOOK_BLUE))
						{
							pe_ent.dpp_name = DPP_BOOKBLUE;
						}
						else
						{
							if ((pe_ent.pemit_source.style == MISCBOOK_RED))
							{
								pe_ent.dpp_name = DPP_BOOKRED;
							}
							else
							{
								pe_ent.dpp_name = DPP_BOOKGOLD;
							}
						}
						pe_ent.dpp_wait = 1;
						pe_ent.dpp_rnd = 2;
					}
					else
					{
						if ((pe_ent.part_style == PARTICLE_STYLE_OPENBOOK))
						{
							if ((random() < 0.5))
							{
								pe_ent.spr_name1 = PART_BOOKRUNE1;
							}
							else
							{
								pe_ent.spr_name1 = PART_BOOKRUNE2;
							}
							if ((pe_ent.pemit_source.style == MISCBOOK_BLUE))
							{
								if ((random() < 0.5))
								{
									pe_ent.spr_name2 = PART_DOTMED_BLUE;
								}
								else
								{
									pe_ent.spr_name2 = PART_DOTSML_BLUE;
								}
								pe_ent.spr_name3 = PART_DOTSML_WHITE;
								pe_ent.dpp_name = DPP_OPENBOOKBLUE;
							}
							else
							{
								if ((pe_ent.pemit_source.style == MISCBOOK_RED))
								{
									if ((random() < 0.5))
									{
										pe_ent.spr_name2 = PART_DOTMED_RED;
									}
									else
									{
										pe_ent.spr_name2 = PART_DOTSML_RED;
									}
									pe_ent.spr_name3 = PART_DOTSML_GOLD;
									pe_ent.dpp_name = DPP_OPENBOOKRED;
								}
								else
								{
									if ((random() < 0.5))
									{
										pe_ent.spr_name2 = PART_DOTMED_YELLOW;
									}
									else
									{
										pe_ent.spr_name2 = PART_DOTSML_YELLOW;
									}
									pe_ent.spr_name3 = PART_DOTSML_GOLD;
									pe_ent.dpp_name = DPP_OPENBOOKGOLD;
								}
							}
							pe_ent.part_limit = 30;
							pe_ent.part_life = 7;
							pe_ent.part_ofs = '0 0 4';
							pe_ent.part_vel = '0 0 10';
							pe_ent.part_velrand = '4 4 0';
							pe_ent.part_velrot = 45;
							pe_ent.part_vol = '8 8 0';
							pe_ent.part_veltype = 0;
							pe_ent.wakeup_dist = 768;
							pe_ent.wakeup_timer = 4;
							pe_ent.spawn_base = 0.1;
							pe_ent.spawn_rand = 0.3;
							pe_ent.dpp_wait = 0.5;
							pe_ent.dpp_rnd = 2;
						}
						else
						{
							if ((pe_ent.part_style == PARTICLE_STYLE_ELECTRIC))
							{
								pe_ent.spr_name1 = PART_DOTMED_BLUE;
								pe_ent.spr_name2 = PART_DOTSML_GOLD;
								pe_ent.spr_name3 = PART_DOTSML_BLUE;
								pe_ent.part_limit = 100;
								pe_ent.part_life = 1;
								pe_ent.part_ofs = VEC_ORIGIN;
								pe_ent.part_vel = '50 0 0';
								pe_ent.part_velrand = '0 0 16';
								pe_ent.part_vol = '8 8 8';
								pe_ent.part_veltype = 0;
								pe_ent.wakeup_dist = 768;
								pe_ent.wakeup_timer = 0.2;
								pe_ent.spawn_base = 0.01;
								pe_ent.spawn_rand = 0;
								pe_ent.dpp_name = DPP_ELECTRIC;
								pe_ent.dpp_rnd = 0;
							}
							else
							{
								if ((pe_ent.part_style == PARTICLE_STYLE_FLAMET))
								{
									pe_ent.start_delay = (3 + (random() * 8));
									pe_ent.spr_name1 = PART_TORCH1;
									pe_ent.spr_name2 = PART_DOTSML_GOLD;
									pe_ent.spr_name3 = PART_DOTSML_GREY;
									pe_ent.part_limit = 8;
									pe_ent.part_life = 2;
									pe_ent.part_ofs = '0 0 12';
									pe_ent.part_vel = '0 0 10';
									pe_ent.part_velrand = '4 4 0';
									pe_ent.part_vol = '1 1 0';
									pe_ent.part_veltype = 0;
									if ((pe_ent.pemit_source.wakeup_dist < 1))
									{
										pe_ent.wakeup_dist = 384;
									}
									else
									{
										pe_ent.wakeup_dist = pe_ent.pemit_source.wakeup_dist;
									}
									if ((pe_ent.pemit_source.wakeup_timer < 1))
									{
										pe_ent.wakeup_timer = 8;
									}
									else
									{
										pe_ent.wakeup_timer = pe_ent.pemit_source.wakeup_timer;
									}
									pe_ent.spawn_base = 0.25;
									pe_ent.spawn_rand = 0.25;
									pe_ent.dpp_name = DPP_FLAMET;
									pe_ent.dpp_wait = 1;
								}
								else
								{
									if ((pe_ent.part_style == PARTICLE_STYLE_FLAMES))
									{
										pe_ent.start_delay = (3 + (random() * 8));
										pe_ent.spr_name1 = PART_TORCH1;
										pe_ent.spr_name2 = PART_DOTSML_GOLD;
										pe_ent.spr_name3 = PART_DOTSML_GREY;
										pe_ent.part_limit = 8;
										pe_ent.part_life = 2;
										pe_ent.part_ofs = VEC_ORIGIN;
										pe_ent.part_vel = '0 0 10';
										pe_ent.part_velrand = '4 4 0';
										pe_ent.part_vol = '1 1 0';
										pe_ent.part_veltype = 0;
										if ((pe_ent.pemit_source.wakeup_dist < 1))
										{
											pe_ent.wakeup_dist = 384;
										}
										else
										{
											pe_ent.wakeup_dist = pe_ent.pemit_source.wakeup_dist;
										}
										if ((pe_ent.pemit_source.wakeup_timer < 1))
										{
											pe_ent.wakeup_timer = 6;
										}
										else
										{
											pe_ent.wakeup_timer = pe_ent.pemit_source.wakeup_timer;
										}
										pe_ent.spawn_base = 0.25;
										pe_ent.spawn_rand = 0.25;
										pe_ent.dpp_name = DPP_FLAMES;
										pe_ent.dpp_wait = 1;
									}
									else
									{
										if ((pe_ent.part_style == PARTICLE_STYLE_FLAMEL))
										{
											pe_ent.spr_name1 = PART_TORCH1;
											pe_ent.spr_name2 = PART_DOTSML_GOLD;
											pe_ent.spr_name3 = PART_DOTSML_GREY;
											pe_ent.part_limit = 100;
											if ((pe_ent.pemit_source.part_life < 1))
											{
												pe_ent.part_life = 8;
											}
											else
											{
												pe_ent.part_life = pe_ent.pemit_source.part_life;
											}
											pe_ent.part_ofs = VEC_ORIGIN;
											pe_ent.part_vel = '0 0 12';
											pe_ent.part_velrand = '4 4 0';
											pe_ent.part_vol = '4 4 0';
											pe_ent.part_veltype = 0;
											if ((pe_ent.pemit_source.wakeup_dist < 1))
											{
												pe_ent.wakeup_dist = 768;
											}
											else
											{
												pe_ent.wakeup_dist = pe_ent.pemit_source.wakeup_dist;
											}
											if ((pe_ent.pemit_source.wakeup_timer < 1))
											{
												pe_ent.wakeup_timer = 1;
											}
											else
											{
												pe_ent.wakeup_timer = pe_ent.pemit_source.wakeup_timer;
											}
											pe_ent.spawn_base = 0.05;
											pe_ent.spawn_rand = 0.1;
											pe_ent.dpp_name = DPP_FLAMEL;
										}
										else
										{
											if ((pe_ent.part_style == PARTICLE_STYLE_SKILL))
											{
												pe_ent.spr_name1 = PART_DOTMED_RED;
												pe_ent.spr_name2 = PART_DOTSML_GOLD;
												pe_ent.spr_name3 = PART_DOTSML_RED;
												pe_ent.part_limit = 35;
												pe_ent.part_life = 2;
												pe_ent.part_ofs = VEC_ORIGIN;
												makevectors(pe_ent.pemit_source.angles);
												pe_ent.part_vel = (v_forward * 10);
												pe_ent.part_vol = '4 4 4';
												pe_ent.part_velrand = '4 4 8';
												pe_ent.part_veltype = 0;
												pe_ent.wakeup_dist = 768;
												pe_ent.wakeup_timer = 1;
												pe_ent.spawn_base = 0.01;
												pe_ent.spawn_rand = 0.2;
												pe_ent.dpp_name = DPP_SKILLPILLAR;
												pe_ent.dpp_rnd = 0;
												pe_ent.dpp_vel = normalize(v_forward);
											}
											else
											{
												if ((pe_ent.part_style == PARTICLE_STYLE_ALTAR))
												{
													if ((pe_ent.pemit_source.cnt == 1))
													{
														pe_ent.spr_name1 = PART_DOTMED_GREY;
														pe_ent.spr_name2 = PART_DOTSML_WHITE;
														pe_ent.spr_name3 = PART_DOTSML_GOLD;
														pe_ent.dpp_name = DPP_ALTARGREY;
													}
													else
													{
														pe_ent.spr_name1 = PART_DOTMED_RED;
														pe_ent.spr_name2 = PART_DOTSML_GOLD;
														pe_ent.spr_name3 = PART_DOTSML_RED;
														pe_ent.dpp_name = DPP_ALTARRED;
													}
													pe_ent.part_limit = 100;
													pe_ent.part_life = 5;
													pe_ent.part_ofs = VEC_ORIGIN;
													if (CheckZeroVector(pe_ent.pemit_source.part_vel))
													{
														pe_ent.part_vel = '0 0 12';
													}
													pe_ent.part_velrand = '4 4 12';
													pe_ent.part_vol = '64 64 0';
													if ((pe_ent.pemit_source.t_length > 0))
													{
														pe_ent.part_vol_x = pe_ent.pemit_source.t_length;
													}
													if ((pe_ent.pemit_source.t_width > 0))
													{
														pe_ent.part_vol_y = pe_ent.pemit_source.t_width;
													}
													pe_ent.part_veltype = 0;
													pe_ent.wakeup_dist = 768;
													pe_ent.wakeup_timer = 4;
													pe_ent.spawn_base = 0.1;
													pe_ent.spawn_rand = 0.1;
												}
												else
												{
													if ((pe_ent.part_style == PARTICLE_STYLE_SMOKE))
													{
														pe_ent.dpp_only = TRUE;
														if ((pe_ent.pemit_source.exactskin == 0))
														{
															pe_ent.dpp_name = DPP_VELSMOKEGREY1;
														}
														else
														{
															if ((pe_ent.pemit_source.exactskin == 1))
															{
																pe_ent.dpp_name = DPP_VELSMOKEGREY2;
															}
															else
															{
																if ((pe_ent.pemit_source.exactskin == 2))
																{
																	pe_ent.dpp_name = DPP_VELSMOKEWHITE;
																}
																else
																{
																	if ((pe_ent.pemit_source.exactskin == 3))
																	{
																		pe_ent.dpp_name = DPP_VELSMOKETOXIC;
																	}
																	else
																	{
																		if ((pe_ent.pemit_source.exactskin == 4))
																		{
																			pe_ent.dpp_name = DPP_VELSMOKEGREEN;
																		}
																		else
																		{
																			if ((pe_ent.pemit_source.exactskin == 5))
																			{
																				pe_ent.dpp_name = DPP_VELSMOKEPURPLE;
																			}
																			else
																			{
																				if ((pe_ent.pemit_source.exactskin == 6))
																				{
																					pe_ent.dpp_name = DPP_VELSMOKERED;
																				}
																				else
																				{
																					if ((pe_ent.pemit_source.exactskin == 7))
																					{
																						pe_ent.dpp_name = DPP_VELSMOKEFIRE;
																					}
																				}
																			}
																		}
																	}
																}
															}
														}
														pe_ent.dpp_rnd = pe_ent.pemit_source.delay;
														pe_ent.dpp_wait = pe_ent.pemit_source.wait;
														pe_ent.dpp_vel = (pe_ent.pemit_source.movedir * pe_ent.pemit_source.height);
													}
													else
													{
														if ((pe_ent.part_style == PARTICLE_STYLE_RESPAWN))
														{
															pe_ent.start_delay = 0.1;
															pe_ent.spr_name1 = PART_DOTSML_YELLOW;
															pe_ent.spr_name2 = PART_DOTSML_GREY;
															pe_ent.spr_name3 = PART_DOTSML_GOLD;
															pe_ent.part_limit = 25;
															pe_ent.part_life = 1;
															pe_ent.part_ofs = '0 0 1';
															pe_ent.part_vel = '0 0 10';
															pe_ent.part_vol = '16 16 0';
															pe_ent.part_velrand = '4 4 6';
															pe_ent.part_veltype = 0;
															pe_ent.wakeup_dist = 768;
															pe_ent.wakeup_timer = 1;
															pe_ent.spawn_base = 0.05;
															pe_ent.spawn_rand = 0;
															pe_ent.dpp_name = DPP_RESPAWN;
															pe_ent.dpp_rnd = 0;
														}
														else
														{
															if ((pe_ent.part_style == PARTICLE_STYLE_MEGAH))
															{
																pe_ent.spr_name1 = PART_DOTSML_WHITE;
																pe_ent.spr_name2 = PART_DOTMED_RED;
																pe_ent.spr_name3 = PART_DOTSML_GOLD;
																pe_ent.part_limit = 75;
																pe_ent.part_life = 3.5;
																pe_ent.part_ofs = '0 0 16';
																pe_ent.part_vel = '12 12 4';
																pe_ent.part_velrand = '0 0 8';
																pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																pe_ent.wakeup_dist = 768;
																pe_ent.wakeup_timer = 1;
																pe_ent.spawn_base = 0.05;
																pe_ent.spawn_rand = 0.1;
																pe_ent.dpp_name = DPP_MEGAH;
															}
															else
															{
																if ((pe_ent.part_style == PARTICLE_STYLE_ARMOR))
																{
																	if ((pe_ent.pemit_source.items & IT_ARMOR1))
																	{
																		pe_ent.spr_name1 = PART_DOTSML_LGREEN;
																		pe_ent.spr_name2 = PART_DOTMED_LGREEN;
																		pe_ent.spr_name3 = PART_DOTSML_GREY;
																		pe_ent.dpp_name = DPP_ARMOR1;
																	}
																	else
																	{
																		if ((pe_ent.pemit_source.items & IT_ARMOR2))
																		{
																			if ((pe_ent.pemit_source.spawnflags & ARMOR_BLUE))
																			{
																				pe_ent.spr_name1 = PART_DOTSML_BLUE;
																				pe_ent.spr_name2 = PART_DOTMED_BLUE;
																				pe_ent.spr_name3 = PART_DOTSML_GREY;
																				pe_ent.dpp_name = DPP_ARMOR2BLUE;
																			}
																			else
																			{
																				pe_ent.spr_name1 = PART_DOTSML_YELLOW;
																				pe_ent.spr_name2 = PART_DOTMED_YELLOW;
																				pe_ent.spr_name3 = PART_DOTSML_GOLD;
																				pe_ent.dpp_name = DPP_ARMOR2;
																			}
																		}
																		else
																		{
																			pe_ent.spr_name1 = PART_DOTSML_RED;
																			pe_ent.spr_name2 = PART_DOTSML_GOLD;
																			pe_ent.spr_name3 = PART_DOTMED_RED;
																			pe_ent.dpp_name = DPP_ARMOR3;
																		}
																	}
																	pe_ent.part_limit = 50;
																	pe_ent.part_life = 2.75;
																	pe_ent.part_ofs = '0 0 24';
																	pe_ent.part_vel = '6 6 4';
																	pe_ent.part_velbase = '0 0 12';
																	pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																	pe_ent.wakeup_dist = 768;
																	pe_ent.wakeup_timer = 1;
																	pe_ent.spawn_base = 0.1;
																	pe_ent.spawn_rand = 0.2;
																}
																else
																{
																	if ((pe_ent.part_style == PARTICLE_STYLE_KEYSILVER))
																	{
																		pe_ent.spr_name1 = PART_DOTSML_BLUE;
																		pe_ent.spr_name2 = PART_DOTSML_BLUE;
																		pe_ent.spr_name3 = PART_DOTSML_GREY;
																		pe_ent.part_limit = 50;
																		pe_ent.part_life = 2;
																		pe_ent.part_ofs = '0 0 20';
																		pe_ent.part_vel = '16 16 8';
																		pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																		pe_ent.wakeup_dist = 768;
																		pe_ent.wakeup_timer = 1;
																		pe_ent.spawn_base = 0.1;
																		pe_ent.spawn_rand = 0;
																		pe_ent.dpp_name = DPP_KEYSILVER;
																	}
																	else
																	{
																		if ((pe_ent.part_style == PARTICLE_STYLE_KEYGOLD))
																		{
																			pe_ent.spr_name1 = PART_DOTSML_GOLD;
																			pe_ent.spr_name2 = PART_DOTSML_GOLD;
																			pe_ent.spr_name3 = PART_DOTSML_YELLOW;
																			pe_ent.part_limit = 50;
																			pe_ent.part_life = 2;
																			pe_ent.part_ofs = '0 0 20';
																			pe_ent.part_vel = '16 16 8';
																			pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																			pe_ent.wakeup_dist = 768;
																			pe_ent.wakeup_timer = 1;
																			pe_ent.spawn_base = 0.1;
																			pe_ent.spawn_rand = 0;
																			pe_ent.dpp_name = DPP_KEYGOLD;
																		}
																		else
																		{
																			if ((pe_ent.part_style == PARTICLE_STYLE_KEYRED))
																			{
																				pe_ent.spr_name1 = PART_DOTSML_RED;
																				pe_ent.spr_name2 = PART_DOTMED_RED;
																				pe_ent.spr_name3 = PART_DOTSML_GOLD;
																				pe_ent.part_limit = 50;
																				pe_ent.part_life = 2;
																				pe_ent.part_ofs = '0 0 20';
																				pe_ent.part_vel = '16 16 8';
																				pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																				pe_ent.wakeup_dist = 768;
																				pe_ent.wakeup_timer = 1;
																				pe_ent.spawn_base = 0.1;
																				pe_ent.spawn_rand = 0;
																				pe_ent.dpp_name = DPP_KEYRED;
																			}
																			else
																			{
																				if ((pe_ent.part_style == PARTICLE_STYLE_KEYGREEN))
																				{
																					pe_ent.spr_name1 = PART_DOTSML_GREEN;
																					pe_ent.spr_name2 = PART_DOTMED_GREEN;
																					pe_ent.spr_name3 = PART_DOTSML_YELLOW;
																					pe_ent.part_limit = 50;
																					pe_ent.part_life = 2;
																					pe_ent.part_ofs = '0 0 20';
																					pe_ent.part_vel = '16 16 8';
																					pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																					pe_ent.wakeup_dist = 768;
																					pe_ent.wakeup_timer = 1;
																					pe_ent.spawn_base = 0.1;
																					pe_ent.spawn_rand = 0;
																					pe_ent.dpp_name = DPP_KEYGREEN;
																				}
																				else
																				{
																					if ((pe_ent.part_style == PARTICLE_STYLE_KEYPURPLE))
																					{
																						pe_ent.spr_name1 = PART_DOTSML_PURP;
																						pe_ent.spr_name2 = PART_DOTMED_PURP;
																						pe_ent.spr_name3 = PART_DOTSML_PURP;
																						pe_ent.part_limit = 50;
																						pe_ent.part_life = 2;
																						pe_ent.part_ofs = '0 0 20';
																						pe_ent.part_vel = '16 16 8';
																						pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																						pe_ent.wakeup_dist = 768;
																						pe_ent.wakeup_timer = 1;
																						pe_ent.spawn_base = 0.1;
																						pe_ent.spawn_rand = 0;
																						pe_ent.dpp_name = DPP_KEYPURPLE;
																					}
																					else
																					{
																						if ((pe_ent.part_style == PARTICLE_STYLE_KEYWHITE))
																						{
																							pe_ent.spr_name1 = PART_DOTSML_GREY;
																							pe_ent.spr_name2 = PART_DOTMED_GREY;
																							pe_ent.spr_name3 = PART_DOTSML_WHITE;
																							pe_ent.part_limit = 50;
																							pe_ent.part_life = 2;
																							pe_ent.part_ofs = '0 0 20';
																							pe_ent.part_vel = '16 16 8';
																							pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																							pe_ent.wakeup_dist = 768;
																							pe_ent.wakeup_timer = 1;
																							pe_ent.spawn_base = 0.1;
																							pe_ent.spawn_rand = 0;
																							pe_ent.dpp_name = DPP_KEYWHITE;
																						}
																						else
																						{
																							if ((pe_ent.part_style == PARTICLE_STYLE_SIGIL))
																							{
																								pe_ent.spr_name1 = PART_DOTMED_PURP;
																								pe_ent.spr_name2 = PART_DOTSML_PURP;
																								pe_ent.spr_name3 = PART_DOTSML_PURP;
																								pe_ent.part_limit = 50;
																								pe_ent.part_life = 1.5;
																								pe_ent.part_ofs = '0 0 16';
																								pe_ent.part_vel = '8 8 16';
																								pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																								pe_ent.wakeup_dist = 768;
																								pe_ent.wakeup_timer = 1;
																								pe_ent.spawn_base = 0.1;
																								pe_ent.spawn_rand = 0;
																								pe_ent.dpp_name = DPP_SIGIL;
																							}
																							else
																							{
																								if ((pe_ent.part_style == PARTICLE_STYLE_BACKPACK))
																								{
																									pe_ent.spr_name1 = PART_DOTMED_GREY;
																									pe_ent.spr_name2 = PART_DOTSML_WHITE;
																									pe_ent.spr_name3 = PART_DOTSML_GREY;
																									pe_ent.part_limit = 50;
																									pe_ent.part_life = 2;
																									pe_ent.part_ofs = '0 0 12';
																									pe_ent.part_vel = '16 16 8';
																									pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																									pe_ent.wakeup_dist = 768;
																									pe_ent.wakeup_timer = 1;
																									pe_ent.spawn_base = 0.1;
																									pe_ent.spawn_rand = 0;
																									pe_ent.dpp_name = DPP_BACKPACK;
																								}
																								else
																								{
																									if ((pe_ent.part_style == PARTICLE_STYLE_SUIT))
																									{
																										pe_ent.spr_name1 = PART_DOTSML_GREEN;
																										pe_ent.spr_name2 = PART_DOTMED_GREEN;
																										pe_ent.spr_name3 = PART_DOTSML_YELLOW;
																										pe_ent.part_limit = 75;
																										pe_ent.part_life = 2.75;
																										pe_ent.part_ofs = '0 0 28';
																										pe_ent.part_vel = '8 8 3';
																										pe_ent.part_velbase = '0 0 12';
																										pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																										pe_ent.wakeup_dist = 768;
																										pe_ent.wakeup_timer = 1;
																										pe_ent.spawn_base = 0.1;
																										pe_ent.spawn_rand = 0;
																										pe_ent.dpp_name = DPP_SUIT;
																										pe_ent.dpp_wait = 0.5;
																									}
																									else
																									{
																										if ((pe_ent.part_style == PARTICLE_STYLE_PENT))
																										{
																											pe_ent.spr_name1 = PART_DOTSML_RED;
																											pe_ent.spr_name2 = PART_DOTMED_RED;
																											pe_ent.spr_name3 = PART_DOTSML_GOLD;
																											pe_ent.part_limit = 75;
																											pe_ent.part_life = 2.5;
																											pe_ent.part_ofs = '0 0 16';
																											pe_ent.part_vel = '12 12 12';
																											pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																											pe_ent.wakeup_dist = 768;
																											pe_ent.wakeup_timer = 1;
																											pe_ent.spawn_base = 0.1;
																											pe_ent.spawn_rand = 0;
																											pe_ent.dpp_name = DPP_PENT;
																											pe_ent.dpp_wait = 1;
																										}
																										else
																										{
																											if ((pe_ent.part_style == PARTICLE_STYLE_SRING))
																											{
																												pe_ent.spr_name1 = PART_DOTSML_YELLOW;
																												pe_ent.spr_name2 = PART_DOTSML_WHITE;
																												pe_ent.spr_name3 = PART_DOTSML_GOLD;
																												pe_ent.part_limit = 35;
																												pe_ent.part_life = 2;
																												pe_ent.part_ofs = '0 0 6';
																												pe_ent.part_vel = '8 8 3';
																												pe_ent.part_velbase = '0 0 -12';
																												pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																												pe_ent.wakeup_dist = 768;
																												pe_ent.wakeup_timer = 1;
																												pe_ent.spawn_base = 0.1;
																												pe_ent.spawn_rand = 0.1;
																												pe_ent.dpp_name = DPP_SRING;
																											}
																											else
																											{
																												if ((pe_ent.part_style == PARTICLE_STYLE_QUAD))
																												{
																													pe_ent.spr_name1 = PART_DOTMED_BLUE;
																													pe_ent.spr_name2 = PART_DOTSML_WHITE;
																													pe_ent.spr_name3 = PART_DOTSML_BLUE;
																													pe_ent.part_limit = 75;
																													pe_ent.part_life = 1.5;
																													pe_ent.part_ofs = '0 0 16';
																													pe_ent.part_vel = '10 10 16';
																													pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																													pe_ent.wakeup_dist = 768;
																													pe_ent.wakeup_timer = 1;
																													pe_ent.spawn_base = 0.1;
																													pe_ent.spawn_rand = 0;
																													pe_ent.dpp_name = DPP_QUAD;
																												}
																												else
																												{
																													if ((pe_ent.part_style == PARTICLE_STYLE_TOMEOFP))
																													{
																														pe_ent.spr_name1 = PART_DOTSML_GOLD;
																														pe_ent.spr_name2 = PART_DOTSML_YELLOW;
																														pe_ent.spr_name3 = PART_DOTSML_GREY;
																														pe_ent.part_limit = 75;
																														pe_ent.part_life = 2;
																														pe_ent.part_ofs = '0 0 16';
																														pe_ent.part_vel = '16 16 8';
																														pe_ent.part_velbase = '0 0 -4';
																														pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																														pe_ent.wakeup_dist = 768;
																														pe_ent.wakeup_timer = 1;
																														pe_ent.spawn_base = 0.05;
																														pe_ent.spawn_rand = 0.05;
																														pe_ent.dpp_name = DPP_TOMEOFP;
																														pe_ent.dpp_wait = 0.5;
																													}
																													else
																													{
																														if ((pe_ent.part_style == PARTICLE_STYLE_SHARP))
																														{
																															pe_ent.spr_name1 = PART_DOTMED_PURP;
																															pe_ent.spr_name2 = PART_DOTSML_PURP;
																															pe_ent.spr_name3 = PART_DOTSML_GREY;
																															pe_ent.part_limit = 75;
																															pe_ent.part_life = 1.5;
																															pe_ent.part_ofs = '0 0 16';
																															pe_ent.part_vel = '10 10 16';
																															pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																															pe_ent.wakeup_dist = 768;
																															pe_ent.wakeup_timer = 1;
																															pe_ent.spawn_base = 0.1;
																															pe_ent.spawn_rand = 0;
																															pe_ent.dpp_name = DPP_SHARP;
																														}
																														else
																														{
																															if ((pe_ent.part_style == PARTICLE_STYLE_PIERCE))
																															{
																																pe_ent.spr_name1 = PART_DOTMED_PURP;
																																pe_ent.spr_name2 = PART_DOTSML_PURP;
																																pe_ent.spr_name3 = PART_DOTSML_GREY;
																																pe_ent.part_limit = 75;
																																pe_ent.part_life = 1.5;
																																pe_ent.part_ofs = '0 0 16';
																																pe_ent.part_vel = '8 8 4';
																																pe_ent.part_velbase = '0 0 12';
																																pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																																pe_ent.wakeup_dist = 768;
																																pe_ent.wakeup_timer = 1;
																																pe_ent.spawn_base = 0.1;
																																pe_ent.spawn_rand = 0;
																																pe_ent.dpp_name = DPP_PIERCE;
																															}
																															else
																															{
																																if ((pe_ent.part_style == PARTICLE_STYLE_WETSUIT))
																																{
																																	pe_ent.spr_name1 = PART_DOTSML_BLUE;
																																	pe_ent.spr_name2 = PART_DOTMED_BLUE;
																																	pe_ent.spr_name3 = PART_DOTSML_WHITE;
																																	pe_ent.part_limit = 75;
																																	pe_ent.part_life = 2.75;
																																	pe_ent.part_ofs = '0 0 28';
																																	pe_ent.part_vel = '8 8 3';
																																	pe_ent.part_velbase = '0 0 12';
																																	pe_ent.part_veltype = PARTICLE_ORIGIN_CENTER;
																																	pe_ent.wakeup_dist = 768;
																																	pe_ent.wakeup_timer = 1;
																																	pe_ent.spawn_base = 0.1;
																																	pe_ent.spawn_rand = 0;
																																	pe_ent.dpp_name = DPP_WETSUIT;
																																	pe_ent.dpp_wait = 0.5;
																																}
																																else
																																{
																																	if ((pe_ent.part_style == PARTICLE_STYLE_WEATHER))
																																	{
																																		pe_ent.part_limit = pe_ent.pemit_source.count;
																																		pe_ent.part_vel = VEC_ORIGIN;
																																		pe_ent.part_vel_z = pe_ent.pemit_source.speed;
																																		pe_ent.part_velrand = pe_ent.pemit_source.v_angle;
																																		pe_ent.wakeup_dist = pe_ent.pemit_source.wakeup_dist;
																																		pe_ent.wakeup_timer = pe_ent.pemit_source.wakeup_timer;
																																		pe_ent.spawn_base = 0.1;
																																		pe_ent.spawn_rand = 0;
																																	}
																																	else
																																	{
																																		dprint("€–≈Õ…‘‘≈“› Style no (");
																																		dprint(ftos(pe_ent.part_style));
																																		dprint(") not valid!!!");
																																		pe_ent.part_style = 0;
																																		spawn_marker(pe_ent.origin, SPNMARK_YELLOW);
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
				}
			}
		}
	}
	return (pe_ent.part_style);
};

void(entity pe_ent) misc_particle_off =
{
	if ((pe_ent.classtype != CT_PARTICLEEMIT))
	{
		return;
	}
	if ((pe_ent.state == STATE_OFF))
	{
		return;
	}
	if ((pe_ent.state == STATE_SETUP))
	{
		pe_ent.spawnflags = PARTICLE_START_OFF;
		return;
	}
	pe_ent.state = STATE_OFF;
	pe_ent.estate = ESTATE_OFF;
	if ((pe_ent.part_style == PARTICLE_STYLE_FCIRCLE))
	{
		particle_ring(pe_ent.origin, '0 0 4', '4 4 16', (pe_ent.part_vol_x + 8), pe_ent.part_limit, pe_ent.part_life, 4);
		particle_ring(pe_ent.origin, '0 0 4', '0 0 12', (pe_ent.part_vol_x + -4), pe_ent.part_limit, pe_ent.part_life, 1);
	}
};

void() misc_particle_use =
{
	if ((query_configflag(SVR_PARTICLES) != SVR_PARTICLES))
	{
		return;
	}
	if ((self.state == STATE_SETUP))
	{
		if ((self.spawnflags & PARTICLE_START_ON))
		{
			self.spawnflags = PARTICLE_START_OFF;
		}
		else
		{
			self.spawnflags = PARTICLE_START_ON;
		}
		return;
	}
	if ((self.part_style == PARTICLE_STYLE_EMPTY))
	{
		return;
	}
	if ((self.state == STATE_OFF))
	{
		self.state = STATE_ON;
		self.estate = ESTATE_ON;
		if ((ext_dppart || self.dpp_only))
		{
			if ((self.part_style == PARTICLE_STYLE_FCIRCLE))
			{
				emitdpp_fcircle();
			}
			else
			{
				if ((self.part_style == PARTICLE_STYLE_WEATHER))
				{
					if ((!ext_dpsnow || !ext_dprain))
					{
						return;
					}
					emitepp_weather();
				}
				else
				{
					emitdpp_particle();
				}
			}
		}
		else
		{
			if ((self.part_style == PARTICLE_STYLE_WEATHER))
			{
				return;
			}
			else
			{
				emit_particle();
			}
		}
	}
	else
	{
		misc_particle_off(self);
	}
};

void(entity pe_ent) misc_particle_on =
{
	if ((pe_ent.classtype != CT_PARTICLEEMIT))
	{
		return;
	}
	if ((pe_ent.state == STATE_ON))
	{
		return;
	}
	if ((pe_ent.state == STATE_SETUP))
	{
		pe_ent.spawnflags = PARTICLE_START_ON;
		return;
	}
	pe_ent.state = STATE_OFF;
	pe_ent.think = misc_particle_use;
	pe_ent.nextthink = (time + TIME_MINTICK);
};

void(entity pe_ent, float partemit_style) misc_particle_update =
{
	if ((pe_ent.classtype != CT_PARTICLEEMIT))
	{
		return;
	}
	if ((pe_ent.state == STATE_SETUP))
	{
		return;
	}
	if ((pe_ent.part_style == PARTICLE_STYLE_EMPTY))
	{
		return;
	}
	pe_ent.part_style = partemit_style;
	if ((misc_particle_style(pe_ent) == FALSE))
	{
		dprint("€Õ…”√ﬂ–¡“‘…√Ã≈› Error updating emitter!");
	}
};

void() misc_particle_switch_on =
{
	misc_particle_on(self);
};

void() misc_particle_switch_off =
{
	misc_particle_off(self);
};

void() misc_particle_switch_disable =
{
	self.state = STATE_OFF;
};

void() misc_particle_finishsetup =
{
	if ((self.part_style != PARTICLE_STYLE_EMPTY))
	{
		self.circular_angle = 0;
		self.state = STATE_OFF;
		self.estate = ESTATE_OFF;
		if ((self.targetname != ""))
		{
			self.use = entity_state_use;
		}
		else
		{
			self.use = misc_particle_use;
		}
		self.estate_on = misc_particle_switch_on;
		self.estate_off = misc_particle_switch_off;
		self.estate_disable = misc_particle_switch_disable;
		self.estate_use = misc_particle_use;
		if ((self.spawnflags & PARTICLE_START_ON))
		{
			misc_particle_use();
		}
	}
};

void() misc_particle_delay =
{
	if ((self.target != ""))
	{
		self.pemit_target = find(world, targetname, self.target);
	}
	if (!self.pemit_target)
	{
		self.target = "";
	}
	if (!self.start_delay)
	{
		self.start_delay = (1 + (random() * 2));
	}
	self.nextthink = (time + self.start_delay);
	self.think = misc_particle_finishsetup;
};

void() misc_particletemplate =
{
	self.classtype = CT_PARTICLETEMP;
	if ((self.spr_name1 != ""))
	{
		precache_model(self.spr_name1);
	}
	if ((self.spr_name2 != ""))
	{
		precache_model(self.spr_name2);
	}
	if ((self.spr_name3 != ""))
	{
		precache_model(self.spr_name3);
	}
};

void() misc_particle_copytemplate =
{
	local entity fdest;

	fdest = find(world, targetname, self.targetp2);
	while (fdest)
	{
		if ((fdest.classtype == CT_PARTICLETEMP))
		{
			self.owner = fdest;
			fdest = world;
		}
		else
		{
			fdest = find(fdest, targetname, self.targetp2);
		}
	}
	if (!self.owner)
	{
		dprint("€Õ…”√ﬂ–¡“‘…√Ã≈› Missing target template!\n");
		spawn_marker(self.origin, SPNMARK_YELLOW);
		return;
	}
	self.part_style = PARTICLE_STYLE_CUSTOM;
	if (self.owner.spr_name1)
	{
		self.spr_name1 = self.owner.spr_name1;
	}
	else
	{
		self.spr_name1 = PART_DOTMED_BLUE;
	}
	if (self.owner.spr_name2)
	{
		self.spr_name2 = self.owner.spr_name2;
	}
	else
	{
		self.spr_name2 = PART_DOTSML_WHITE;
	}
	if (self.owner.spr_name3)
	{
		self.spr_name3 = self.owner.spr_name3;
	}
	else
	{
		self.spr_name3 = PART_DOTSML_BLUE;
	}
	if (self.owner.part_movetype)
	{
		self.part_movetype = self.owner.part_movetype;
	}
	else
	{
		self.part_movetype = MOVETYPE_NOCLIP;
	}
	if (self.owner.part_limit)
	{
		self.part_limit = self.owner.part_limit;
	}
	else
	{
		self.part_limit = 25;
	}
	if (self.owner.part_life)
	{
		self.part_life = self.owner.part_life;
	}
	else
	{
		self.part_life = 1;
	}
	if (!!self.owner.part_ofs)
	{
		self.part_ofs = self.owner.part_ofs;
	}
	else
	{
		self.part_ofs = VEC_ORIGIN;
	}
	if (self.owner.part_veltype)
	{
		self.part_veltype = self.owner.part_veltype;
	}
	else
	{
		self.part_veltype = PARTICLE_ORIGIN_CENTER;
	}
	if (!!self.owner.part_vel)
	{
		self.part_vel = self.owner.part_vel;
	}
	if (!!self.owner.part_velbase)
	{
		self.part_velbase = self.owner.part_velbase;
	}
	if (!!self.owner.part_velrand)
	{
		self.part_velrand = self.owner.part_velrand;
	}
	if (self.owner.part_velrot)
	{
		self.part_velrot = self.owner.part_velrot;
	}
	if (!!self.owner.part_vol)
	{
		self.part_vol = self.owner.part_vol;
	}
	if (self.owner.wakeup_dist)
	{
		self.wakeup_dist = self.owner.wakeup_dist;
	}
	else
	{
		self.wakeup_dist = 1024;
	}
	if (self.owner.wakeup_timer)
	{
		self.wakeup_timer = self.owner.wakeup_timer;
	}
	else
	{
		self.wakeup_timer = 1;
	}
	if ((self.wakeup_timer < TIME_MINTICK))
	{
		self.wakeup_timer = TIME_MINTICK;
	}
	if (self.owner.spawn_base)
	{
		self.spawn_base = self.owner.spawn_base;
	}
	else
	{
		self.spawn_base = 0.1;
	}
	if ((self.spawn_base < TIME_MINTICK))
	{
		self.spawn_base = TIME_MINTICK;
	}
	if (self.owner.spawn_rand)
	{
		self.spawn_rand = self.owner.spawn_rand;
	}
	else
	{
		self.spawn_rand = 0;
	}
	if (self.owner.dpp_name)
	{
		self.dpp_name = self.owner.dpp_name;
	}
	else
	{
		self.dpp_name = "";
	}
	if (self.owner.dpp_wait)
	{
		self.dpp_wait = self.owner.dpp_wait;
	}
	else
	{
		self.dpp_wait = 0.1;
	}
	if ((self.dpp_wait < TIME_MINTICK))
	{
		self.dpp_wait = TIME_MINTICK;
	}
	if (self.owner.dpp_rnd)
	{
		self.dpp_rnd = self.owner.dpp_rnd;
	}
	else
	{
		self.dpp_rnd = 0;
	}
	if (!!self.owner.dpp_vel)
	{
		self.dpp_vel = self.owner.dpp_vel;
	}
	else
	{
		self.dpp_vel = VEC_ORIGIN;
	}
	misc_particle_delay();
};

void() misc_particle_setup =
{
	if ((misc_particle_style(self) != PARTICLE_STYLE_EMPTY))
	{
		misc_particle_delay();
	}
};

entity(entity pe_source, entity pe_target, float pe_style, float pe_spawnf) spawn_pemitter =
{
	local entity new_pe;

	new_pe = spawn();
	new_pe.classtype = CT_PARTICLEEMIT;
	new_pe.state = STATE_SETUP;
	new_pe.pemit_source = pe_source;
	if ((pe_source != pe_target))
	{
		new_pe.pemit_target = pe_target;
	}
	gen_unique_no(self);
	new_pe.entno_unique = self.entno_unique;
	if (pe_source.bsporigin)
	{
		new_pe.origin = bmodel_origin(pe_source);
	}
	else
	{
		new_pe.origin = pe_source.origin;
	}
	setorigin(new_pe, new_pe.origin);
	new_pe.part_style = pe_style;
	new_pe.spawnflags = pe_spawnf;
	new_pe.angles = pe_source.angles;
	new_pe.think = misc_particle_setup;
	new_pe.nextthink = ((time + 0.1) + random());
	return (new_pe);
};

void() misc_particle =
{
	if ((self.spawnflags & ENT_STARTOFF))
	{
		self.spawnflags = PARTICLE_START_OFF;
	}
	else
	{
		self.spawnflags = PARTICLE_START_ON;
	}
	self.classtype = CT_PARTICLEEMIT;
	self.pemit_source = self;
	gen_unique_no(self);
	self.state = STATE_SETUP;
	if ((self.targetname != ""))
	{
		self.use = misc_particle_use;
	}
	if ((self.targetp2 != ""))
	{
		self.nextthink = ((time + 0.1) + random());
		self.think = misc_particle_copytemplate;
		return;
	}
	if ((self.message == "ARMOR1"))
	{
		self.part_style = PARTICLE_STYLE_ARMOR;
		self.items = IT_ARMOR1;
	}
	else
	{
		if ((self.message == "ARMOR2"))
		{
			self.part_style = PARTICLE_STYLE_ARMOR;
			self.items = IT_ARMOR2;
		}
		else
		{
			if ((self.message == "ARMOR3"))
			{
				self.part_style = PARTICLE_STYLE_ARMOR;
				self.items = IT_ARMOR3;
			}
			else
			{
				if ((self.message == "BOOK"))
				{
					self.part_style = PARTICLE_STYLE_BOOK;
				}
				else
				{
					if ((self.message == "ELECTRIC"))
					{
						self.part_style = PARTICLE_STYLE_ELECTRIC;
					}
					else
					{
						if ((self.message == "FCIRCLE"))
						{
							self.part_style = PARTICLE_STYLE_FCIRCLE;
						}
						else
						{
							if ((self.message == "FLAMES"))
							{
								self.part_style = PARTICLE_STYLE_FLAMES;
							}
							else
							{
								if ((self.message == "FLAMEL"))
								{
									self.part_style = PARTICLE_STYLE_FLAMEL;
								}
								else
								{
									if ((self.message == "KEYGOLD"))
									{
										self.part_style = PARTICLE_STYLE_KEYGOLD;
									}
									else
									{
										if ((self.message == "KEYSILVER"))
										{
											self.part_style = PARTICLE_STYLE_KEYSILVER;
										}
										else
										{
											if ((self.message == "KEYRED"))
											{
												self.part_style = PARTICLE_STYLE_KEYRED;
											}
											else
											{
												if ((self.message == "KEYGREEN"))
												{
													self.part_style = PARTICLE_STYLE_KEYGREEN;
												}
												else
												{
													if ((self.message == "KEYPURPLE"))
													{
														self.part_style = PARTICLE_STYLE_KEYPURPLE;
													}
													else
													{
														if ((self.message == "KEYWHITE"))
														{
															self.part_style = PARTICLE_STYLE_KEYWHITE;
														}
														else
														{
															if ((self.message == "MEGAH"))
															{
																self.part_style = PARTICLE_STYLE_MEGAH;
															}
															else
															{
																if ((self.message == "PENT"))
																{
																	self.part_style = PARTICLE_STYLE_PENT;
																}
																else
																{
																	if ((self.message == "PORTAL"))
																	{
																		self.part_style = PARTICLE_STYLE_PORTAL;
																	}
																	else
																	{
																		if ((self.message == "JUMPPAD"))
																		{
																			self.part_style = PARTICLE_STYLE_JUMPPAD;
																		}
																		else
																		{
																			if ((self.message == "QUAD"))
																			{
																				self.part_style = PARTICLE_STYLE_QUAD;
																			}
																			else
																			{
																				if ((self.message == "SIGIL"))
																				{
																					self.part_style = PARTICLE_STYLE_SIGIL;
																				}
																				else
																				{
																					if ((self.message == "ALTAR"))
																					{
																						self.part_style = PARTICLE_STYLE_ALTAR;
																					}
																					else
																					{
																						if ((self.message == "SKILL"))
																						{
																							self.part_style = PARTICLE_STYLE_SKILL;
																						}
																						else
																						{
																							if ((self.message == "SRING"))
																							{
																								self.part_style = PARTICLE_STYLE_SRING;
																							}
																							else
																							{
																								if ((self.message == "SUIT"))
																								{
																									self.part_style = PARTICLE_STYLE_SUIT;
																								}
																								else
																								{
																									dprint("€Õ…”√ﬂ–¡“‘…√Ã≈› Missing particle style!\n");
																									spawn_marker(self.origin, SPNMARK_YELLOW);
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
	self.nextthink = ((time + 0.1) + random());
	self.think = misc_particle_setup;
};

void() misc_particle_burst_use =
{
	particle_explode((self.origin + self.part_ofs), self.count, self.part_life, self.part_style, self.part_movetype);
	if ((self.waitmin > 0))
	{
		if ((self.pausetime == 0))
		{
			if (!self.waitmin2)
			{
				self.waitmin2 = 0.1;
			}
			self.pausetime = (time + self.waitmin);
		}
		if ((self.pausetime > time))
		{
			self.think = misc_particle_burst_use;
			self.nextthink = (time + self.waitmin2);
		}
		else
		{
			self.pausetime = 0;
		}
	}
};

void() misc_particle_burst_setup =
{
	if (!self.pemit_tcount)
	{
		self.count = 20;
	}
	if (!self.part_life)
	{
		self.part_life = 2;
	}
	if (CheckZeroVector(self.part_ofs))
	{
		self.part_ofs = VEC_ORIGIN;
	}
	if ((self.part_style == 1))
	{
		self.part_style = PARTICLE_BURST_YELLOW;
	}
	else
	{
		if ((self.part_style == 2))
		{
			self.part_style = PARTICLE_BURST_GREEN;
		}
		else
		{
			if ((self.part_style == 3))
			{
				self.part_style = PARTICLE_BURST_RED;
			}
			else
			{
				if ((self.part_style == 4))
				{
					self.part_style = PARTICLE_BURST_BLUE;
				}
				else
				{
					if ((self.part_style == 5))
					{
						self.part_style = PARTICLE_BURST_PURPLE;
					}
					else
					{
						if ((self.part_style == 6))
						{
							self.part_style = PARTICLE_BURST_FIRE;
						}
						else
						{
							self.part_style = PARTICLE_BURST_WHITE;
						}
					}
				}
			}
		}
	}
	if ((self.part_movetype == 3))
	{
		self.part_movetype = PARTICLE_BURST_UPWARD;
	}
	else
	{
		if ((self.part_movetype == 4))
		{
			self.part_movetype = PARTICLE_BURST_SHOCKWAVE;
		}
		else
		{
			if ((self.part_movetype == 5))
			{
				self.part_movetype = PARTICLE_BURST_SKULLUP;
			}
			else
			{
				if ((self.part_movetype == 6))
				{
					self.part_movetype = PARTICLE_BURST_LOSTUP;
				}
				else
				{
					if ((self.part_movetype == 7))
					{
						self.part_movetype = PARTICLE_BURST_MINOTAUR;
					}
					else
					{
						self.part_movetype = PARTICLE_BURST_CENTER;
					}
				}
			}
		}
	}
};

void() misc_particle_burst =
{
	self.classtype = CT_PARTICLEEMIT;
	self.pemit_source = self;
	self.health = LARGE_TIMER;
	misc_particle_burst_setup();
	self.use = misc_particle_burst_use;
};

void() misc_weather =
{
	if ((self.spawnflags & ENT_STARTOFF))
	{
		self.spawnflags = (self.spawnflags | PARTICLE_START_OFF);
	}
	else
	{
		self.spawnflags = (self.spawnflags | PARTICLE_START_ON);
	}
	self.classtype = CT_PARTICLEEMIT;
	self.part_style = PARTICLE_STYLE_WEATHER;
	self.pemit_source = self;
	gen_unique_no(self);
	self.state = STATE_SETUP;
	InitTrigger();
	self.bbmins = self.mins;
	self.bbmaxs = self.maxs;
	self.oldorigin = bmodel_origin(self);
	spawn_marker(self.oldorigin, (entity)0i);
	self.solid = 0;
	if (!self.count)
	{
		self.count = rint((vlen((self.bbmaxs - self.bbmins)) * 0.1));
	}
	if (!self.speed)
	{
		self.speed = 30;
	}
	self.attack_speed = ((time + self.speed) + (random() * self.speed));
	if ((self.spawnflags & PARTICLE_WEATHER_SNOW))
	{
		if (CheckZeroVector(self.pos1))
		{
			self.pos1 = '8 15 0';
		}
		if (CheckZeroVector(self.pos2))
		{
			self.pos2 = '100 100 -100';
		}
	}
	else
	{
		if (CheckZeroVector(self.pos1))
		{
			self.pos1 = '1 15 0';
		}
		if (CheckZeroVector(self.pos2))
		{
			self.pos2 = '100 100 -500';
		}
	}
	if ((self.pos1_x > self.pos1_y))
	{
		self.pos1_z = self.pos1_x;
		self.pos1_x = self.pos1_y;
		self.pos1_y = self.pos1_z;
	}
	self.pos1_z = rint((self.pos1_y - self.pos1_x));
	if ((self.pos1_z < 1))
	{
		self.pos1_z = 1;
	}
	self.pos3_x = (crandom() * self.pos2_x);
	self.pos3_y = (crandom() * self.pos2_y);
	self.pos3_z = self.pos2_z;
	self.nextthink = ((time + 0.1) + random());
	self.think = misc_particle_setup;
};
