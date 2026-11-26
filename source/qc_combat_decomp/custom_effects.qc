.float bm_xh_key;
.float bm_psycho_sent;

void(string r, string g, string b) BM_Crosshair =
{
	local float k;

	k = ((stof(r) * 10000) + (stof(g) * 100)) + stof(b) + 1;
	if ((k == self.bm_xh_key))
	{
		return;
	}
	self.bm_xh_key = k;
	stuffcmd(self, strcat("crosshair_color_red ", r, "\n"));
	stuffcmd(self, strcat("crosshair_color_green ", g, "\n"));
	stuffcmd(self, strcat("crosshair_color_blue ", b, "\n"));
};

void(float v) BM_Psycho =
{
	if ((v == self.bm_psycho_sent))
	{
		return;
	}
	self.bm_psycho_sent = v;
	stuffcmd(self, strcat("v_psycho ", ftos(v), "\n"));
};

//Decompiled code. Please respect the original copyright.

void() animate_mage_weapon =
{

	if (self.button0)
	{
		return;
	}
	self.animate_mage_weapon_frequence = (time + 0.1);
	if (((random() < 0.12) && !cvar("chase_active")))
	{
		sound(self, CHAN_AUTO, "weapons/v_mage1_idle.wav", 0.8, ATTN_NORM);
	}
	if ((self.animate_mage_weapon_helper == 0))
	{
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe > 12))
		{
			self.weaponframe = 11;
			self.animate_mage_weapon_helper = 1;
		}
	}
	else
	{
		self.weaponframe = (self.weaponframe - 1);
		if ((self.weaponframe < 0))
		{
			self.weaponframe = 1;
			self.animate_mage_weapon_helper = 0;
		}
	}
};

void() check_bodycount =
{
	self.check_bodycount_frequence = (time + 2);
	killed_monsters_old = killed_monsters;
	gibbed_monsters_old = gibbed_monsters;
};

void(float fPunchStrength, float fRadius) Monster_Animation_EarthQuake =
{
	local entity enFind;

	if ((self.flags & FL_ONGROUND))
	{
		if (autocvar_monstercorpsequake)
		{
			enFind = findradius(self.origin, fRadius);
			while (enFind)
			{
				if (((enFind.flags & FL_ONGROUND) && (enFind != self)))
				{
					if (((enFind.flags & FL_MONSTER) || (enFind.classname == "player")))
					{
						enFind.velocity_x = (autocvar_monstercorpsequake * (enFind.velocity_x + ((crandom() * fPunchStrength) * 5)));
						enFind.velocity_y = (autocvar_monstercorpsequake * (enFind.velocity_y + ((crandom() * fPunchStrength) * 5)));
						enFind.velocity_z = (autocvar_monstercorpsequake * ((enFind.velocity_z + (fPunchStrength * 10)) + (crandom() * 40)));
					}
					if ((enFind.classname == "player"))
					{
						enFind.punchangle = (enFind.punchangle + (randomvec() * (0.7 * fPunchStrength)));
					}
				}
				enFind = enFind.chain;
			}
		}
	}
};

void() shambler_walking_quake =
{
	local entity enFind;

	enFind = findradius(self.origin, 444);
	while (enFind)
	{
		if ((enFind.flags & FL_ONGROUND))
		{
			if ((enFind.classname == "player"))
			{
				enFind.punchangle = (enFind.punchangle + (randomvec() * 0.6));
			}
		}
		enFind = enFind.chain;
	}
};

void() start_earthquake_think =
{
	if ((quaketime <= 0))
	{
		quaketime = ((time + autocvar_earthquake_interval) + (200 * random()));
		return;
	}
	if ((time >= quaketime))
	{
		quaketime = ((time + autocvar_earthquake_interval) + (200 * random()));
		if ((random() >= 0.8))
		{
			self.earthquake_finished = (time + 3);
			sound(self, CHAN_AUTO, "ambience/rumblefade.wav", 0.8, ATTN_NORM);
		}
	}
};

void() start_earthquake =
{
	local entity enFind;

	enFind = findradius(self.origin, 666);
	while (enFind)
	{
		if ((enFind.flags & FL_ONGROUND))
		{
			if ((enFind.flags & FL_MONSTER))
			{
				enFind.velocity_x = (enFind.velocity_x + (crandom() * 15));
				enFind.velocity_y = (enFind.velocity_y + (crandom() * 15));
				enFind.velocity_z = (enFind.velocity_z + (crandom() * 40));
			}
			if ((enFind.classname == "player"))
			{
				enFind.punchangle = (enFind.punchangle + (randomvec() * 0.2));
			}
		}
		enFind = enFind.chain;
	}
};

void() PlayerHeartbeat_quick =
{
	self.playerheartbeat_finished = (time + 0.5);
	sound(self, CHAN_AUTO, "ambience/gibheartbeat.wav", (autocvar_player_wounded_heartbeat / 2), 3);
};

void() PlayerHeartbeat_slow =
{
	self.playerheartbeat_finished = (time + 0.666);
	sound(self, CHAN_AUTO, "ambience/gibheartbeat.wav", ((autocvar_player_wounded_heartbeat / 2) - 0.07), 3);
};

void() spawn_flying_dust =
{
	local float counta;

	counta = autocvar_flying_dust_quantity;
	self.flying_dust_finished = (time + 0.01);
	if (cvar("chase_active"))
	{
		while ((counta > 0))
		{
			if ((autocvar_flying_dust_type == 1))
			{
				particleeffectnum(/*11317i*/"flying_dust");
				pointparticles(particleeffectnum(/*11317i*/"flying_dust"), (((self.origin + self.view_ofs) + (v_up * 15)) + (v_forward * 20)), (self.velocity * 10), 1);
			}
			else
			{
				if ((autocvar_flying_dust_type == 2))
				{
					particleeffectnum(/*11329i*/"flying_ember");
					pointparticles(particleeffectnum(/*11329i*/"flying_ember"), (((self.origin + self.view_ofs) + (v_up * 15)) + (v_forward * 20)), (self.velocity * 10), 1);
				}
				else
				{
					if ((autocvar_flying_dust_type == 3))
					{
						particleeffectnum(/*11342i*/"flying_snow");
						pointparticles(particleeffectnum(/*11342i*/"flying_snow"), (((self.origin + self.view_ofs) + (v_up * 15)) + (v_forward * 20)), (self.velocity * 10), 1);
					}
					else
					{
						if ((autocvar_flying_dust_type == 4))
						{
							particleeffectnum(/*11354i*/"flying_rain");
							pointparticles(particleeffectnum(/*11354i*/"flying_rain"), (((self.origin + self.view_ofs) + (v_up * 15)) + (v_forward * 20)), (self.velocity * 10), 1);
						}
					}
				}
			}
			counta = counta - 1;
		}
	}
	else
	{
		while ((counta > 0))
		{
			if ((autocvar_flying_dust_type == 1))
			{
				particleeffectnum(/*11317i*/"flying_dust");
				pointparticles(particleeffectnum(/*11317i*/"flying_dust"), (((self.origin + self.view_ofs) + (v_up * 15)) + (v_forward * 20)), (self.velocity * 10), 1);
			}
			else
			{
				if ((autocvar_flying_dust_type == 2))
				{
					particleeffectnum(/*11329i*/"flying_ember");
					pointparticles(particleeffectnum(/*11329i*/"flying_ember"), (((self.origin + self.view_ofs) + (v_up * 15)) + (v_forward * 20)), (self.velocity * 10), 1);
				}
				else
				{
					if ((autocvar_flying_dust_type == 3))
					{
						particleeffectnum(/*11342i*/"flying_snow");
						pointparticles(particleeffectnum(/*11342i*/"flying_snow"), (((self.origin + self.view_ofs) + (v_up * 15)) + (v_forward * 20)), (self.velocity * 10), 1);
					}
					else
					{
						if ((autocvar_flying_dust_type == 4))
						{
							particleeffectnum(/*11354i*/"flying_rain");
							pointparticles(particleeffectnum(/*11354i*/"flying_rain"), (((self.origin + self.view_ofs) + (v_up * 15)) + (v_forward * 20)), (self.velocity * 10), 1);
						}
					}
				}
			}
			counta = counta - 1;
		}
	}
};

void() add_weapon =
{
	self.origin = VEC_ORIGIN;
	setmodel(self, self.owner.weaponmodel);
	self.alpha = 0.3;
	self.frame = self.owner.weaponframe;
	self.think = SUB_Remove;
	self.nextthink = time;
};

void(entity e) add_transparent_weaponmodel =
{
	newmis = spawn();
	newmis.owner = e;
	newmis.viewmodelforclient = self;
	newmis.think = add_weapon;
	newmis.nextthink = time;
};

void() Quake3_quad_effect_v_weapon_position_anim =
{
	if ((intermission_running || (self.owner.classname != "player")))	// owner left the game
	{
		remove(self);
		return;
	}
	if ((self.owner.meleeing == 1))
	{
		self.alpha = -1;
		self.think = Quake3_quad_effect_v_weapon_position_anim;
		self.nextthink = time;
		return;
	}
	else
	{
		self.alpha = 0.5;
	}
	if (!self.owner.super_damage_finished)
	{
		remove(self);
		return;
	}
	if ((autocvar_mage_weapon && (self.owner.weapon == IT_LIGHTNING)))
	{
		self.alpha = -1;
	}
	else
	{
		self.alpha = 0.5;
	}
	if ((self.owner.weapon == IT_SHOTGUN))
	{
		if (autocvar_centered_weapons)
			setmodel(self, "progs/centered/v_shot.mdl");
		else
			setmodel(self, "progs/v_shot.mdl");
		self.origin_x = autocvar_weapon_position_fully_adjustable_shot1_x_offset;
		self.origin_y = autocvar_weapon_position_fully_adjustable_shot1_y_offset;
		self.origin_z = autocvar_weapon_position_fully_adjustable_shot1_z_offset;
		self.angles_x = autocvar_weapon_position_fully_adjustable_shot1_x_angle;
		self.angles_y = autocvar_weapon_position_fully_adjustable_shot1_y_angle;
		self.angles_z = autocvar_weapon_position_fully_adjustable_shot1_z_angle;
	}
	else
	{
		if ((self.owner.weapon == IT_SUPER_SHOTGUN))
		{
			setmodel(self, "");
			self.origin_x = autocvar_weapon_position_fully_adjustable_shot2_x_offset;
			self.origin_y = autocvar_weapon_position_fully_adjustable_shot2_y_offset;
			self.origin_z = autocvar_weapon_position_fully_adjustable_shot2_z_offset;
			self.angles_x = autocvar_weapon_position_fully_adjustable_shot2_x_angle;
			self.angles_y = autocvar_weapon_position_fully_adjustable_shot2_y_angle;
			self.angles_z = autocvar_weapon_position_fully_adjustable_shot2_z_angle;
		}
		else
		{
				if ((self.owner.weapon == IT_SUPER_NAILGUN))
				{
					setmodel(self, "progs/v_milky.md3");	// the Milky Gun (milky.qc)
					self.origin_x = autocvar_weapon_position_fully_adjustable_nail2_x_offset;
					self.origin_y = autocvar_weapon_position_fully_adjustable_nail2_y_offset;
					self.origin_z = autocvar_weapon_position_fully_adjustable_nail2_z_offset;
					self.angles_x = autocvar_weapon_position_fully_adjustable_nail2_x_angle;
					self.angles_y = autocvar_weapon_position_fully_adjustable_nail2_y_angle;
					self.angles_z = autocvar_weapon_position_fully_adjustable_nail2_z_angle;
				}
				else
				{
					if ((self.owner.weapon == IT_GRENADE_LAUNCHER))
					{
						if (autocvar_centered_weapons)
							setmodel(self, "progs/centered/v_rock.mdl");
						else
							setmodel(self, "progs/v_rock.mdl");
						self.origin_x = autocvar_weapon_position_fully_adjustable_gren_x_offset;
						self.origin_y = autocvar_weapon_position_fully_adjustable_gren_y_offset;
						self.origin_z = autocvar_weapon_position_fully_adjustable_gren_z_offset;
						self.angles_x = autocvar_weapon_position_fully_adjustable_gren_x_angle;
						self.angles_y = autocvar_weapon_position_fully_adjustable_gren_y_angle;
						self.angles_z = autocvar_weapon_position_fully_adjustable_gren_z_angle;
					}
					else
					{
						if ((self.owner.weapon == IT_ROCKET_LAUNCHER))
						{
							if (autocvar_centered_weapons)
								setmodel(self, "progs/centered/v_rock2.mdl");
							else
								setmodel(self, "progs/v_rock2.mdl");
							self.origin_x = autocvar_weapon_position_fully_adjustable_rock_x_offset;
							self.origin_y = autocvar_weapon_position_fully_adjustable_rock_y_offset;
							self.origin_z = autocvar_weapon_position_fully_adjustable_rock_z_offset;
							self.angles_x = autocvar_weapon_position_fully_adjustable_rock_x_angle;
							self.angles_y = autocvar_weapon_position_fully_adjustable_rock_y_angle;
							self.angles_z = autocvar_weapon_position_fully_adjustable_rock_z_angle;
						}
						else
						{
							if ((self.owner.weapon == IT_LIGHTNING))
							{
								setmodel(self, "progs/v_light.mdl");
								if ((autocvar_weapon_position_fully_adjustable == 1))
								{
									self.origin_x = autocvar_weapon_position_fully_adjustable_light_x_offset;
									self.origin_y = autocvar_weapon_position_fully_adjustable_light_y_offset;
									self.origin_z = autocvar_weapon_position_fully_adjustable_light_z_offset;
									self.angles_x = autocvar_weapon_position_fully_adjustable_light_x_angle;
									self.angles_y = autocvar_weapon_position_fully_adjustable_light_y_angle;
									self.angles_z = autocvar_weapon_position_fully_adjustable_light_z_angle;
								}
								else
								{
									self.origin = VEC_ORIGIN;
									self.angles = VEC_ORIGIN;
								}
							}
							else
							{
								if ((self.owner.weapon == IT_AXE))
								{
									setmodel(self, "progs/v_hammer.mdl");
									self.origin_x = autocvar_weapon_position_fully_adjustable_axe_x_offset;
									self.origin_y = autocvar_weapon_position_fully_adjustable_axe_y_offset;
									self.origin_z = autocvar_weapon_position_fully_adjustable_axe_z_offset;
									self.angles_x = autocvar_weapon_position_fully_adjustable_axe_x_angle;
									self.angles_y = autocvar_weapon_position_fully_adjustable_axe_y_angle;
									self.angles_z = autocvar_weapon_position_fully_adjustable_axe_z_angle;
								}
								else if ((self.owner.weapon == IT_LASER_CANNON))
								{
									if (autocvar_centered_weapons)
										setmodel(self, "progs/centered/v_laserg.mdl");
									else
										setmodel(self, "progs/v_laserg.mdl");
									self.origin_x = autocvar_weapon_position_fully_adjustable_axe_x_offset;
									self.origin_y = autocvar_weapon_position_fully_adjustable_axe_y_offset;
									self.origin_z = autocvar_weapon_position_fully_adjustable_axe_z_offset;
									self.angles_x = autocvar_weapon_position_fully_adjustable_axe_x_angle;
									self.angles_y = autocvar_weapon_position_fully_adjustable_axe_y_angle;
									self.angles_z = autocvar_weapon_position_fully_adjustable_axe_z_angle;
								}
								else
								{
									setmodel(self, "progs/v_saw.mdl");
									self.origin_x = autocvar_weapon_position_fully_adjustable_axe_x_offset;
									self.origin_y = autocvar_weapon_position_fully_adjustable_axe_y_offset;
									self.origin_z = autocvar_weapon_position_fully_adjustable_axe_z_offset;
									self.angles_x = autocvar_weapon_position_fully_adjustable_axe_x_angle;
									self.angles_y = autocvar_weapon_position_fully_adjustable_axe_y_angle;
									self.angles_z = autocvar_weapon_position_fully_adjustable_axe_z_angle;
								}
							}
						}
					}
				}
		}
	}
	if ((self.owner.weapon == IT_MEGAMAN))
	{
		setmodel(self, MM_PickVModel());
		self.origin = '0 0 0';
		self.angles = '0 0 0';
	}
	if ((self.owner.weapon == IT_FUNGUN))
	{
		setmodel(self, FunGun_VModel(self.owner.fg_sel));
		self.origin = '0 0 0';
		self.angles = '0 0 0';
	}
	self.frame = self.owner.weaponframe;
	Pickle_ViewFrame (self, TRUE);	// sync articulated Pickle Surprise skin & pose on Quad overlay (pickle.qc)
	if ((self.owner.fl_phase == 1) || (self.owner.fl_phase == 2) || (self.owner.throwing == 1) || (self.owner.bm_rl_slot && self.owner.health > 0 && !(M4_ShowsReload (self.owner) || Garand_ShowsReload (self.owner))) || FD_Flying(self.owner) || Veh_Driving(self.owner) || JohnBird_Flying(self.owner) || RocketRider_Flying(self.owner) || EricCannon_Active(self.owner) || MMTank_Driving(self.owner) || Binoc_On(self.owner))
	{
		self.alpha = -1;
	}
	self.nextthink = time;
};

void(entity e) add_Quake3_quad_effect_v_weapon_position =
{
	newmis = spawn();
	newmis.owner = e;
	newmis.skin = 1;
	newmis.alpha = 0.5;
	newmis.colormod = '0 0 0.5';
	newmis.viewmodelforclient = self;
	newmis.think = Quake3_quad_effect_v_weapon_position_anim;
	newmis.nextthink = time;
};

void(float x_offset, float y_offset, float z_offset, float x_angle, float y_angle, float z_angle) idle_weapon_animation =
{
	local float randy_x_off;
	local float randy_y_off;
	local float randy_z_off;
	local float randy_x_ang;
	local float randy_y_ang;
	local float randy_z_ang;

	if (!autocvar_weapon_position_fully_adjustable_idle_animation)
	{
		return;
	}
	self.v_weapon_animation = (time + (autocvar_weapon_position_fully_adjustable_idle_animation_speed + (crandom() * 0.007)));
	self.origin_x_old = self.origin_x;
	self.origin_y_old = self.origin_y;
	self.origin_z_old = self.origin_z;
	self.angles_x_old = self.angles_x;
	self.angles_y_old = self.angles_y;
	self.angles_z_old = self.angles_z;
	if ((self.weapon_anim_x_offset_downwards == 0))
	{
		if (((self.origin_x_old + 0.006) < (x_offset + (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 0.5))))
		{
			self.origin_x = (self.origin_x_old + 0.006);
		}
		else
		{
			self.weapon_anim_x_offset_downwards = 1;
		}
		if (((self.origin_x > (x_offset - 0.004)) && (self.origin_x < (x_offset + 0.004))))
		{
			self.weapon_anim_x_offset_downwards = 2;
		}
	}
	else
	{
		if ((self.weapon_anim_x_offset_downwards == 1))
		{
			if (((self.origin_x_old - 0.006) > (x_offset - (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 0.8))))
			{
				self.origin_x = (self.origin_x_old - 0.006);
			}
			else
			{
				self.weapon_anim_x_offset_downwards = 0;
			}
			if (((self.origin_x > (x_offset - 0.004)) && (self.origin_x < (x_offset + 0.004))))
			{
				self.weapon_anim_x_offset_downwards = 2;
			}
		}
		else
		{
			randy_x_off = random();
			if ((randy_x_off < autocvar_weapon_position_fully_adjustable_idle_animation_pause))
			{
				self.weapon_anim_x_offset_downwards = 0;
			}
			else
			{
				if ((randy_x_off < (2 * autocvar_weapon_position_fully_adjustable_idle_animation_pause)))
				{
					self.weapon_anim_x_offset_downwards = 1;
				}
			}
		}
	}
	if ((self.weapon_anim_y_offset_downwards == 0))
	{
		if (((self.origin_y_old + 0.006) < (y_offset + (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 0.5))))
		{
			self.origin_y = (self.origin_y_old + 0.006);
		}
		else
		{
			self.weapon_anim_y_offset_downwards = 1;
		}
		if (((self.origin_y > (y_offset - 0.004)) && (self.origin_y < (y_offset + 0.004))))
		{
			self.weapon_anim_y_offset_downwards = 2;
		}
	}
	else
	{
		if ((self.weapon_anim_y_offset_downwards == 1))
		{
			if (((self.origin_y_old - 0.006) > (y_offset - (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 0.7))))
			{
				self.origin_y = (self.origin_y_old - 0.006);
			}
			else
			{
				self.weapon_anim_y_offset_downwards = 0;
			}
			if (((self.origin_y > (y_offset - 0.004)) && (self.origin_y < (y_offset + 0.004))))
			{
				self.weapon_anim_y_offset_downwards = 2;
			}
		}
		else
		{
			randy_y_off = random();
			if ((randy_y_off < autocvar_weapon_position_fully_adjustable_idle_animation_pause))
			{
				self.weapon_anim_y_offset_downwards = 0;
			}
			else
			{
				if ((randy_y_off < (2 * autocvar_weapon_position_fully_adjustable_idle_animation_pause)))
				{
					self.weapon_anim_y_offset_downwards = 1;
				}
			}
		}
	}
	if ((self.weapon_anim_z_offset_downwards == 0))
	{
		if (((self.origin_z_old + 0.006) < (z_offset + (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 0.7))))
		{
			self.origin_z = (self.origin_z_old + 0.006);
		}
		else
		{
			self.weapon_anim_z_offset_downwards = 1;
		}
		if (((self.origin_z > (z_offset - 0.004)) && (self.origin_z < (z_offset + 0.004))))
		{
			self.weapon_anim_z_offset_downwards = 2;
		}
	}
	else
	{
		if ((self.weapon_anim_z_offset_downwards == 1))
		{
			if (((self.origin_z_old - 0.006) > (z_offset - (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 0.7))))
			{
				self.origin_z = (self.origin_z_old - 0.006);
			}
			else
			{
				self.weapon_anim_z_offset_downwards = 0;
			}
			if (((self.origin_z > (z_offset - 0.004)) && (self.origin_z < (z_offset + 0.004))))
			{
				self.weapon_anim_z_offset_downwards = 2;
			}
		}
		else
		{
			randy_z_off = random();
			if ((randy_z_off < autocvar_weapon_position_fully_adjustable_idle_animation_pause))
			{
				self.weapon_anim_z_offset_downwards = 0;
			}
			else
			{
				if ((randy_z_off < (2 * autocvar_weapon_position_fully_adjustable_idle_animation_pause)))
				{
					self.weapon_anim_z_offset_downwards = 1;
				}
			}
		}
	}
	if ((self.weapon_anim_x_angles_downwards == 0))
	{
		if (((self.angles_x_old + 0.025) < (x_angle + (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 3))))
		{
			self.angles_x = (self.angles_x_old + 0.025);
		}
		else
		{
			self.weapon_anim_x_angles_downwards = 1;
		}
		if (((self.angles_x > (x_angle - 0.015)) && (self.angles_x < (x_angle + 0.015))))
		{
			self.weapon_anim_x_angles_downwards = 2;
		}
	}
	else
	{
		if ((self.weapon_anim_x_angles_downwards == 1))
		{
			if (((self.angles_x_old - 0.035) > (x_angle - (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 3))))
			{
				self.angles_x = (self.angles_x_old - 0.035);
			}
			else
			{
				self.weapon_anim_x_angles_downwards = 0;
			}
			if (((self.angles_x > (x_angle - 0.02)) && (self.angles_x < (x_angle + 0.02))))
			{
				self.weapon_anim_x_angles_downwards = 2;
			}
		}
		else
		{
			randy_x_ang = random();
			if ((randy_x_ang < autocvar_weapon_position_fully_adjustable_idle_animation_pause))
			{
				self.weapon_anim_x_angles_downwards = 0;
			}
			else
			{
				if ((randy_x_ang < (2 * autocvar_weapon_position_fully_adjustable_idle_animation_pause)))
				{
					self.weapon_anim_x_angles_downwards = 1;
				}
			}
		}
	}
	if ((self.weapon_anim_y_angles_downwards == 0))
	{
		if (((self.angles_y_old + 0.05) < (y_angle + (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 5))))
		{
			self.angles_y = (self.angles_y_old + 0.05);
		}
		else
		{
			self.weapon_anim_y_angles_downwards = 1;
		}
		if (((self.angles_y > (y_angle - 0.04)) && (self.angles_y < (y_angle + 0.04))))
		{
			self.weapon_anim_y_angles_downwards = 2;
		}
	}
	else
	{
		if ((self.weapon_anim_y_angles_downwards == 1))
		{
			if (((self.angles_y_old - 0.05) > (y_angle - (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 5))))
			{
				self.angles_y = (self.angles_y_old - 0.05);
			}
			else
			{
				self.weapon_anim_y_angles_downwards = 0;
			}
			if (((self.angles_y > (y_angle - 0.04)) && (self.angles_y < (y_angle + 0.04))))
			{
				self.weapon_anim_y_angles_downwards = 2;
			}
		}
		else
		{
			randy_y_ang = random();
			if ((randy_y_ang < autocvar_weapon_position_fully_adjustable_idle_animation_pause))
			{
				self.weapon_anim_y_angles_downwards = 0;
			}
			else
			{
				if ((randy_y_ang < (2 * autocvar_weapon_position_fully_adjustable_idle_animation_pause)))
				{
					self.weapon_anim_y_angles_downwards = 1;
				}
			}
		}
	}
	if ((self.weapon_anim_z_angles_downwards == 0))
	{
		if (((self.angles_z_old + 0.05) < (z_angle + (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 3))))
		{
			self.angles_z = (self.angles_z_old + 0.05);
		}
		else
		{
			self.weapon_anim_z_angles_downwards = 1;
		}
		if (((self.angles_z > (z_angle - 0.04)) && (self.angles_z < (z_angle + 0.04))))
		{
			self.weapon_anim_z_angles_downwards = 2;
		}
	}
	else
	{
		if ((self.weapon_anim_z_angles_downwards == 1))
		{
			if (((self.angles_z_old - 0.05) > (z_angle - (autocvar_weapon_position_fully_adjustable_idle_animation_vigor * 6))))
			{
				self.angles_z = (self.angles_z_old - 0.05);
			}
			else
			{
				self.weapon_anim_z_angles_downwards = 0;
			}
			if (((self.angles_z > (z_angle - 0.04)) && (self.angles_z < (z_angle + 0.04))))
			{
				self.weapon_anim_z_angles_downwards = 2;
			}
		}
		else
		{
			randy_z_ang = random();
			if ((randy_z_ang < autocvar_weapon_position_fully_adjustable_idle_animation_pause))
			{
				self.weapon_anim_z_angles_downwards = 0;
			}
			else
			{
				if ((randy_z_ang < (2 * autocvar_weapon_position_fully_adjustable_idle_animation_pause)))
				{
					self.weapon_anim_z_angles_downwards = 1;
				}
			}
		}
	}
	self.owner.gunof = self.origin;
	self.owner.gunang = self.angles;
	self.owner.gunidleof_x = autocvar_weapon_position_fully_adjustable_nail2_x_offset;
	self.owner.gunidleof_y = autocvar_weapon_position_fully_adjustable_nail2_y_offset;
	self.owner.gunidleof_z = autocvar_weapon_position_fully_adjustable_nail2_z_offset;
	self.owner.gunidleang_x = autocvar_weapon_position_fully_adjustable_nail2_x_angle;
	self.owner.gunidleang_y = autocvar_weapon_position_fully_adjustable_nail2_y_angle;
	self.owner.gunidleang_z = autocvar_weapon_position_fully_adjustable_nail2_z_angle;
};

void() weapon_swap_anim =
{
	self.origin_x = self.owner.switchtimer;
	self.origin_z = self.owner.switchtimer;
	if (self.owner.button0)
	{
		self.owner.switchtimer = 0;
	}
	if ((self.owner.idletimer == 1))
	{
		if ((self.origin_z <= -2))
		{
			self.owner.switchtimer = (self.owner.switchtimer + 0.4);
		}
		else
		{
			if ((self.origin_z <= 0))
			{
				self.owner.switchtimer = (self.owner.switchtimer + 0.1);
			}
			else
			{
				self.owner.idletimer = 0;
			}
		}
	}
};

void() v_weapon_position_think =
{
	if ((self.owner.classname != "player"))
	{
		// the owner left (ClientDisconnect clears classname): don't stamp this gun onto whoever reuses the slot
		remove(self);
		return;
	}
	weapon_swap_anim();
	if ((self.owner.v_weapon_position_helper == 0))
	{
		self.owner.weaponmodel = self.model;
		remove(self);
		return;
	}
	if (intermission_running)
	{
		remove(self);
		return;
	}
	if ((self.owner.meleeing == 1))
	{
		self.initial_weapon_position_shot1 = 0;
		self.initial_weapon_position_shot2 = 0;
		self.initial_weapon_position_nail1 = 0;
		self.initial_weapon_position_nail2 = 0;
		self.initial_weapon_position_gren = 0;
		self.initial_weapon_position_rock = 0;
		self.initial_weapon_position_light = 0;
		if (!autocvar_zombieaxeanimation)
		{
			setmodel(self, "progs/v_boot.mdl");
		}
		else
		{
			setmodel(self, "progs/v_hammer.mdl");
		}
		self.owner.weaponmodel = "";
		self.colormap = self.owner.colormap;
		if ((self.owner.items & IT_SUIT))
		{
			self.skin = 1;
		}
		else
		{
			self.skin = 0;
		}
		self.frame = self.owner.weaponframe;
		if ((invisweapon && self.owner.invisible_finished))
		{
			self.alpha = 0.3;
		}
		else
		{
			if ((!invisweapon && self.owner.invisible_finished))
			{
				self.alpha = -1;
			}
			else
			{
				self.alpha = 1;
			}
		}
		self.nextthink = time;
		return;
	}
	self.colormap = 0;
	if ((self.owner.throwing == 1))
	{
		self.initial_weapon_position_shot1 = 0;
		self.initial_weapon_position_shot2 = 0;
		self.initial_weapon_position_nail1 = 0;
		self.initial_weapon_position_nail2 = 0;
		self.initial_weapon_position_gren = 0;
		self.initial_weapon_position_rock = 0;
		self.initial_weapon_position_light = 0;
		setmodel(self, "progs/v_nade.mdl");
		self.owner.weaponmodel = "";
		self.frame = self.owner.weaponframe;
		if ((invisweapon && self.owner.invisible_finished))
		{
			self.alpha = 0.3;
		}
		else
		{
			if ((!invisweapon && self.owner.invisible_finished))
			{
				self.alpha = -1;
			}
			else
			{
				self.alpha = 1;
			}
		}
		self.nextthink = time;
		return;
	}
	if ((self.owner.weapon == IT_SHOTGUN))
	{
		self.initial_weapon_position_axe = 0;
		self.initial_weapon_position_shot2 = 0;
		self.initial_weapon_position_nail1 = 0;
		self.initial_weapon_position_nail2 = 0;
		self.initial_weapon_position_gren = 0;
		self.initial_weapon_position_rock = 0;
		self.initial_weapon_position_light = 0;
		if (autocvar_centered_weapons)
		{
			setmodel(self, "progs/centered/v_shot.mdl");
		}
		else
		{
			setmodel(self, "progs/v_shot.mdl");
		}
		if (((self.owner.button0 || ((self.owner.velocity != VEC_ORIGIN) && (self.owner.earthquake_finished < time))) || self.owner.super_damage_finished))
		{
			if ((self.owner.idletimer == 0))
			{
				self.origin_x = autocvar_weapon_position_fully_adjustable_shot1_x_offset;
				self.origin_y = autocvar_weapon_position_fully_adjustable_shot1_y_offset;
				self.origin_z = autocvar_weapon_position_fully_adjustable_shot1_z_offset;
				self.angles_x = autocvar_weapon_position_fully_adjustable_shot1_x_angle;
				self.angles_y = autocvar_weapon_position_fully_adjustable_shot1_y_angle;
				self.angles_z = autocvar_weapon_position_fully_adjustable_shot1_z_angle;
				if ((random() < 0.5))
				{
					self.weapon_anim_x_offset_downwards = 0;
				}
				else
				{
					self.weapon_anim_x_offset_downwards = 1;
				}
				if ((random() < 0.5))
				{
					self.weapon_anim_y_offset_downwards = 0;
				}
				else
				{
					self.weapon_anim_y_offset_downwards = 1;
				}
				if ((random() < 0.5))
				{
					self.weapon_anim_z_offset_downwards = 0;
				}
				else
				{
					self.weapon_anim_z_offset_downwards = 1;
				}
				if ((random() < 0.5))
				{
					self.weapon_anim_x_angles_downwards = 0;
				}
				else
				{
					self.weapon_anim_x_angles_downwards = 1;
				}
				if ((random() < 0.5))
				{
					self.weapon_anim_y_angles_downwards = 0;
				}
				else
				{
					self.weapon_anim_y_angles_downwards = 1;
				}
				if ((random() < 0.5))
				{
					self.weapon_anim_z_angles_downwards = 0;
				}
				else
				{
					self.weapon_anim_z_angles_downwards = 1;
				}
			}
		}
		else
		{
			if ((self.initial_weapon_position_shot1 == 0))
			{
				self.initial_weapon_position_shot1 = 1;
				if ((random() < 0.5))
				{
					self.weapon_anim_x_offset_downwards = 0;
				}
				else
				{
					self.weapon_anim_x_offset_downwards = 1;
				}
				if ((random() < 0.5))
				{
					self.weapon_anim_y_offset_downwards = 0;
				}
				else
				{
					self.weapon_anim_y_offset_downwards = 1;
				}
				if ((random() < 0.5))
				{
					self.weapon_anim_z_offset_downwards = 0;
				}
				else
				{
					self.weapon_anim_z_offset_downwards = 1;
				}
				if ((random() < 0.5))
				{
					self.weapon_anim_x_angles_downwards = 0;
				}
				else
				{
					self.weapon_anim_x_angles_downwards = 1;
				}
				if ((random() < 0.5))
				{
					self.weapon_anim_y_angles_downwards = 0;
				}
				else
				{
					self.weapon_anim_y_angles_downwards = 1;
				}
				if ((random() < 0.5))
				{
					self.weapon_anim_z_angles_downwards = 0;
				}
				else
				{
					self.weapon_anim_z_angles_downwards = 1;
				}
				self.origin_x = autocvar_weapon_position_fully_adjustable_shot1_x_offset;
				self.origin_y = autocvar_weapon_position_fully_adjustable_shot1_y_offset;
				self.origin_z = autocvar_weapon_position_fully_adjustable_shot1_z_offset;
				self.angles_x = autocvar_weapon_position_fully_adjustable_shot1_x_angle;
				self.angles_y = autocvar_weapon_position_fully_adjustable_shot1_y_angle;
				self.angles_z = autocvar_weapon_position_fully_adjustable_shot1_z_angle;
			}
			else
			{
				if ((self.v_weapon_animation < time))
				{
					idle_weapon_animation(autocvar_weapon_position_fully_adjustable_shot1_x_offset, autocvar_weapon_position_fully_adjustable_shot1_y_offset, autocvar_weapon_position_fully_adjustable_shot1_z_offset, autocvar_weapon_position_fully_adjustable_shot1_x_angle, autocvar_weapon_position_fully_adjustable_shot1_y_angle, autocvar_weapon_position_fully_adjustable_shot1_z_angle);
				}
			}
		}
	}
	else
	{
		if ((self.owner.weapon == IT_SUPER_SHOTGUN))
		{
			self.initial_weapon_position_axe = 0;
			self.initial_weapon_position_shot1 = 0;
			self.initial_weapon_position_nail1 = 0;
			self.initial_weapon_position_nail2 = 0;
			self.initial_weapon_position_gren = 0;
			self.initial_weapon_position_rock = 0;
			self.initial_weapon_position_light = 0;
			setmodel(self, "");
			if (((self.owner.button0 || ((self.owner.velocity != VEC_ORIGIN) && (self.owner.earthquake_finished < time))) || self.owner.super_damage_finished))
			{
				if ((self.owner.idletimer == 0))
				{
					self.origin_x = autocvar_weapon_position_fully_adjustable_shot2_x_offset;
					self.origin_y = autocvar_weapon_position_fully_adjustable_shot2_y_offset;
					self.origin_z = autocvar_weapon_position_fully_adjustable_shot2_z_offset;
					self.angles_x = autocvar_weapon_position_fully_adjustable_shot2_x_angle;
					self.angles_y = autocvar_weapon_position_fully_adjustable_shot2_y_angle;
					self.angles_z = autocvar_weapon_position_fully_adjustable_shot2_z_angle;
					if ((random() < 0.5))
					{
						self.weapon_anim_x_offset_downwards = 0;
					}
					else
					{
						self.weapon_anim_x_offset_downwards = 1;
					}
					if ((random() < 0.5))
					{
						self.weapon_anim_y_offset_downwards = 0;
					}
					else
					{
						self.weapon_anim_y_offset_downwards = 1;
					}
					if ((random() < 0.5))
					{
						self.weapon_anim_z_offset_downwards = 0;
					}
					else
					{
						self.weapon_anim_z_offset_downwards = 1;
					}
					if ((random() < 0.5))
					{
						self.weapon_anim_x_angles_downwards = 0;
					}
					else
					{
						self.weapon_anim_x_angles_downwards = 1;
					}
					if ((random() < 0.5))
					{
						self.weapon_anim_y_angles_downwards = 0;
					}
					else
					{
						self.weapon_anim_y_angles_downwards = 1;
					}
					if ((random() < 0.5))
					{
						self.weapon_anim_z_angles_downwards = 0;
					}
					else
					{
						self.weapon_anim_z_angles_downwards = 1;
					}
				}
			}
			else
			{
				if ((self.initial_weapon_position_shot2 == 0))
				{
					self.initial_weapon_position_shot2 = 1;
					if ((random() < 0.5))
					{
						self.weapon_anim_x_offset_downwards = 0;
					}
					else
					{
						self.weapon_anim_x_offset_downwards = 1;
					}
					if ((random() < 0.5))
					{
						self.weapon_anim_y_offset_downwards = 0;
					}
					else
					{
						self.weapon_anim_y_offset_downwards = 1;
					}
					if ((random() < 0.5))
					{
						self.weapon_anim_z_offset_downwards = 0;
					}
					else
					{
						self.weapon_anim_z_offset_downwards = 1;
					}
					if ((random() < 0.5))
					{
						self.weapon_anim_x_angles_downwards = 0;
					}
					else
					{
						self.weapon_anim_x_angles_downwards = 1;
					}
					if ((random() < 0.5))
					{
						self.weapon_anim_y_angles_downwards = 0;
					}
					else
					{
						self.weapon_anim_y_angles_downwards = 1;
					}
					if ((random() < 0.5))
					{
						self.weapon_anim_z_angles_downwards = 0;
					}
					else
					{
						self.weapon_anim_z_angles_downwards = 1;
					}
					self.origin_x = autocvar_weapon_position_fully_adjustable_shot2_x_offset;
					self.origin_y = autocvar_weapon_position_fully_adjustable_shot2_y_offset;
					self.origin_z = autocvar_weapon_position_fully_adjustable_shot2_z_offset;
					self.angles_x = autocvar_weapon_position_fully_adjustable_shot2_x_angle;
					self.angles_y = autocvar_weapon_position_fully_adjustable_shot2_y_angle;
					self.angles_z = autocvar_weapon_position_fully_adjustable_shot2_z_angle;
				}
				else
				{
					if ((self.v_weapon_animation < time))
					{
						idle_weapon_animation(autocvar_weapon_position_fully_adjustable_shot2_x_offset, autocvar_weapon_position_fully_adjustable_shot2_y_offset, autocvar_weapon_position_fully_adjustable_shot2_z_offset, autocvar_weapon_position_fully_adjustable_shot2_x_angle, autocvar_weapon_position_fully_adjustable_shot2_y_angle, autocvar_weapon_position_fully_adjustable_shot2_z_angle);
					}
				}
			}
		}
		else
		{
				if ((self.owner.weapon == IT_SUPER_NAILGUN))
				{
					self.initial_weapon_position_axe = 0;
					self.initial_weapon_position_shot1 = 0;
					self.initial_weapon_position_shot2 = 0;
					self.initial_weapon_position_nail1 = 0;
					self.initial_weapon_position_gren = 0;
					self.initial_weapon_position_rock = 0;
					self.initial_weapon_position_light = 0;
					if (autocvar_centered_weapons)
					{
						setmodel(self, "progs/v_milky.md3");
					}
					else
					{
						setmodel(self, "progs/v_milky.md3");	// the Milky Gun (milky.qc)
					}
					if (((self.owner.button0 || ((self.owner.velocity != VEC_ORIGIN) && (self.owner.earthquake_finished < time))) || self.owner.super_damage_finished))
					{
						if ((self.owner.idletimer == 0))
						{
							self.origin_x = autocvar_weapon_position_fully_adjustable_nail2_x_offset;
							self.origin_y = autocvar_weapon_position_fully_adjustable_nail2_y_offset;
							self.origin_z = autocvar_weapon_position_fully_adjustable_nail2_z_offset;
							self.angles_x = autocvar_weapon_position_fully_adjustable_nail2_x_angle;
							self.angles_y = autocvar_weapon_position_fully_adjustable_nail2_y_angle;
							self.angles_z = autocvar_weapon_position_fully_adjustable_nail2_z_angle;
							if ((random() < 0.5))
							{
								self.weapon_anim_x_offset_downwards = 0;
							}
							else
							{
								self.weapon_anim_x_offset_downwards = 1;
							}
							if ((random() < 0.5))
							{
								self.weapon_anim_y_offset_downwards = 0;
							}
							else
							{
								self.weapon_anim_y_offset_downwards = 1;
							}
							if ((random() < 0.5))
							{
								self.weapon_anim_z_offset_downwards = 0;
							}
							else
							{
								self.weapon_anim_z_offset_downwards = 1;
							}
							if ((random() < 0.5))
							{
								self.weapon_anim_x_angles_downwards = 0;
							}
							else
							{
								self.weapon_anim_x_angles_downwards = 1;
							}
							if ((random() < 0.5))
							{
								self.weapon_anim_y_angles_downwards = 0;
							}
							else
							{
								self.weapon_anim_y_angles_downwards = 1;
							}
							if ((random() < 0.5))
							{
								self.weapon_anim_z_angles_downwards = 0;
							}
							else
							{
								self.weapon_anim_z_angles_downwards = 1;
							}
						}
					}
					else
					{
						if ((self.initial_weapon_position_nail2 == 0))
						{
							self.initial_weapon_position_nail2 = 1;
							if ((random() < 0.5))
							{
								self.weapon_anim_x_offset_downwards = 0;
							}
							else
							{
								self.weapon_anim_x_offset_downwards = 1;
							}
							if ((random() < 0.5))
							{
								self.weapon_anim_y_offset_downwards = 0;
							}
							else
							{
								self.weapon_anim_y_offset_downwards = 1;
							}
							if ((random() < 0.5))
							{
								self.weapon_anim_z_offset_downwards = 0;
							}
							else
							{
								self.weapon_anim_z_offset_downwards = 1;
							}
							if ((random() < 0.5))
							{
								self.weapon_anim_x_angles_downwards = 0;
							}
							else
							{
								self.weapon_anim_x_angles_downwards = 1;
							}
							if ((random() < 0.5))
							{
								self.weapon_anim_y_angles_downwards = 0;
							}
							else
							{
								self.weapon_anim_y_angles_downwards = 1;
							}
							if ((random() < 0.5))
							{
								self.weapon_anim_z_angles_downwards = 0;
							}
							else
							{
								self.weapon_anim_z_angles_downwards = 1;
							}
							self.origin_x = autocvar_weapon_position_fully_adjustable_nail2_x_offset;
							self.origin_y = autocvar_weapon_position_fully_adjustable_nail2_y_offset;
							self.origin_z = autocvar_weapon_position_fully_adjustable_nail2_z_offset;
							self.angles_x = autocvar_weapon_position_fully_adjustable_nail2_x_angle;
							self.angles_y = autocvar_weapon_position_fully_adjustable_nail2_y_angle;
							self.angles_z = autocvar_weapon_position_fully_adjustable_nail2_z_angle;
						}
						else
						{
							if ((self.v_weapon_animation < time))
							{
								idle_weapon_animation(autocvar_weapon_position_fully_adjustable_nail2_x_offset, autocvar_weapon_position_fully_adjustable_nail2_y_offset, autocvar_weapon_position_fully_adjustable_nail2_z_offset, autocvar_weapon_position_fully_adjustable_nail2_x_angle, autocvar_weapon_position_fully_adjustable_nail2_y_angle, autocvar_weapon_position_fully_adjustable_nail2_z_angle);
							}
						}
					}
				}
				else
				{
					if ((self.owner.weapon == IT_GRENADE_LAUNCHER))
					{
						self.initial_weapon_position_axe = 0;
						self.initial_weapon_position_shot1 = 0;
						self.initial_weapon_position_shot2 = 0;
						self.initial_weapon_position_nail1 = 0;
						self.initial_weapon_position_nail2 = 0;
						self.initial_weapon_position_rock = 0;
						self.initial_weapon_position_light = 0;
						if (autocvar_centered_weapons)
						{
							setmodel(self, "progs/centered/v_rock.mdl");
						}
						else
						{
							setmodel(self, "progs/v_rock.mdl");
						}
						if (((self.owner.button0 || ((self.owner.velocity != VEC_ORIGIN) && (self.owner.earthquake_finished < time))) || self.owner.super_damage_finished))
						{
							if ((self.owner.idletimer == 0))
							{
								self.origin_x = autocvar_weapon_position_fully_adjustable_gren_x_offset;
								self.origin_y = autocvar_weapon_position_fully_adjustable_gren_y_offset;
								self.origin_z = autocvar_weapon_position_fully_adjustable_gren_z_offset;
								self.angles_x = autocvar_weapon_position_fully_adjustable_gren_x_angle;
								self.angles_y = autocvar_weapon_position_fully_adjustable_gren_y_angle;
								self.angles_z = autocvar_weapon_position_fully_adjustable_gren_z_angle;
								if ((random() < 0.5))
								{
									self.weapon_anim_x_offset_downwards = 0;
								}
								else
								{
									self.weapon_anim_x_offset_downwards = 1;
								}
								if ((random() < 0.5))
								{
									self.weapon_anim_y_offset_downwards = 0;
								}
								else
								{
									self.weapon_anim_y_offset_downwards = 1;
								}
								if ((random() < 0.5))
								{
									self.weapon_anim_z_offset_downwards = 0;
								}
								else
								{
									self.weapon_anim_z_offset_downwards = 1;
								}
								if ((random() < 0.5))
								{
									self.weapon_anim_x_angles_downwards = 0;
								}
								else
								{
									self.weapon_anim_x_angles_downwards = 1;
								}
								if ((random() < 0.5))
								{
									self.weapon_anim_y_angles_downwards = 0;
								}
								else
								{
									self.weapon_anim_y_angles_downwards = 1;
								}
								if ((random() < 0.5))
								{
									self.weapon_anim_z_angles_downwards = 0;
								}
								else
								{
									self.weapon_anim_z_angles_downwards = 1;
								}
							}
						}
						else
						{
							if ((self.initial_weapon_position_gren == 0))
							{
								self.initial_weapon_position_gren = 1;
								if ((random() < 0.5))
								{
									self.weapon_anim_x_offset_downwards = 0;
								}
								else
								{
									self.weapon_anim_x_offset_downwards = 1;
								}
								if ((random() < 0.5))
								{
									self.weapon_anim_y_offset_downwards = 0;
								}
								else
								{
									self.weapon_anim_y_offset_downwards = 1;
								}
								if ((random() < 0.5))
								{
									self.weapon_anim_z_offset_downwards = 0;
								}
								else
								{
									self.weapon_anim_z_offset_downwards = 1;
								}
								if ((random() < 0.5))
								{
									self.weapon_anim_x_angles_downwards = 0;
								}
								else
								{
									self.weapon_anim_x_angles_downwards = 1;
								}
								if ((random() < 0.5))
								{
									self.weapon_anim_y_angles_downwards = 0;
								}
								else
								{
									self.weapon_anim_y_angles_downwards = 1;
								}
								if ((random() < 0.5))
								{
									self.weapon_anim_z_angles_downwards = 0;
								}
								else
								{
									self.weapon_anim_z_angles_downwards = 1;
								}
								self.origin_x = autocvar_weapon_position_fully_adjustable_gren_x_offset;
								self.origin_y = autocvar_weapon_position_fully_adjustable_gren_y_offset;
								self.origin_z = autocvar_weapon_position_fully_adjustable_gren_z_offset;
								self.angles_x = autocvar_weapon_position_fully_adjustable_gren_x_angle;
								self.angles_y = autocvar_weapon_position_fully_adjustable_gren_y_angle;
								self.angles_z = autocvar_weapon_position_fully_adjustable_gren_z_angle;
							}
							else
							{
								if ((self.v_weapon_animation < time))
								{
									idle_weapon_animation(autocvar_weapon_position_fully_adjustable_gren_x_offset, autocvar_weapon_position_fully_adjustable_gren_y_offset, autocvar_weapon_position_fully_adjustable_gren_z_offset, autocvar_weapon_position_fully_adjustable_gren_x_angle, autocvar_weapon_position_fully_adjustable_gren_y_angle, autocvar_weapon_position_fully_adjustable_gren_z_angle);
								}
							}
						}
					}
					else
					{
						if ((self.owner.weapon == IT_ROCKET_LAUNCHER))
						{
							self.initial_weapon_position_axe = 0;
							self.initial_weapon_position_shot1 = 0;
							self.initial_weapon_position_shot2 = 0;
							self.initial_weapon_position_nail1 = 0;
							self.initial_weapon_position_nail2 = 0;
							self.initial_weapon_position_gren = 0;
							self.initial_weapon_position_light = 0;
							if (autocvar_centered_weapons)
							{
								setmodel(self, "progs/centered/v_rock2.mdl");
							}
							else
							{
								setmodel(self, "progs/v_rock2.mdl");
							}
							if (((self.owner.button0 || ((self.owner.velocity != VEC_ORIGIN) && (self.owner.earthquake_finished < time))) || self.owner.super_damage_finished))
							{
								if ((self.owner.idletimer == 0))
								{
									self.origin_x = autocvar_weapon_position_fully_adjustable_rock_x_offset;
									self.origin_y = autocvar_weapon_position_fully_adjustable_rock_y_offset;
									self.origin_z = autocvar_weapon_position_fully_adjustable_rock_z_offset;
									self.angles_x = autocvar_weapon_position_fully_adjustable_rock_x_angle;
									self.angles_y = autocvar_weapon_position_fully_adjustable_rock_y_angle;
									self.angles_z = autocvar_weapon_position_fully_adjustable_rock_z_angle;
									if ((random() < 0.5))
									{
										self.weapon_anim_x_offset_downwards = 0;
									}
									else
									{
										self.weapon_anim_x_offset_downwards = 1;
									}
									if ((random() < 0.5))
									{
										self.weapon_anim_y_offset_downwards = 0;
									}
									else
									{
										self.weapon_anim_y_offset_downwards = 1;
									}
									if ((random() < 0.5))
									{
										self.weapon_anim_z_offset_downwards = 0;
									}
									else
									{
										self.weapon_anim_z_offset_downwards = 1;
									}
									if ((random() < 0.5))
									{
										self.weapon_anim_x_angles_downwards = 0;
									}
									else
									{
										self.weapon_anim_x_angles_downwards = 1;
									}
									if ((random() < 0.5))
									{
										self.weapon_anim_y_angles_downwards = 0;
									}
									else
									{
										self.weapon_anim_y_angles_downwards = 1;
									}
									if ((random() < 0.5))
									{
										self.weapon_anim_z_angles_downwards = 0;
									}
									else
									{
										self.weapon_anim_z_angles_downwards = 1;
									}
								}
							}
							else
							{
								if ((self.initial_weapon_position_rock == 0))
								{
									self.initial_weapon_position_rock = 1;
									if ((random() < 0.5))
									{
										self.weapon_anim_x_offset_downwards = 0;
									}
									else
									{
										self.weapon_anim_x_offset_downwards = 1;
									}
									if ((random() < 0.5))
									{
										self.weapon_anim_y_offset_downwards = 0;
									}
									else
									{
										self.weapon_anim_y_offset_downwards = 1;
									}
									if ((random() < 0.5))
									{
										self.weapon_anim_z_offset_downwards = 0;
									}
									else
									{
										self.weapon_anim_z_offset_downwards = 1;
									}
									if ((random() < 0.5))
									{
										self.weapon_anim_x_angles_downwards = 0;
									}
									else
									{
										self.weapon_anim_x_angles_downwards = 1;
									}
									if ((random() < 0.5))
									{
										self.weapon_anim_y_angles_downwards = 0;
									}
									else
									{
										self.weapon_anim_y_angles_downwards = 1;
									}
									if ((random() < 0.5))
									{
										self.weapon_anim_z_angles_downwards = 0;
									}
									else
									{
										self.weapon_anim_z_angles_downwards = 1;
									}
									self.origin_x = autocvar_weapon_position_fully_adjustable_rock_x_offset;
									self.origin_y = autocvar_weapon_position_fully_adjustable_rock_y_offset;
									self.origin_z = autocvar_weapon_position_fully_adjustable_rock_z_offset;
									self.angles_x = autocvar_weapon_position_fully_adjustable_rock_x_angle;
									self.angles_y = autocvar_weapon_position_fully_adjustable_rock_y_angle;
									self.angles_z = autocvar_weapon_position_fully_adjustable_rock_z_angle;
								}
								else
								{
									if ((self.v_weapon_animation < time))
									{
										idle_weapon_animation(autocvar_weapon_position_fully_adjustable_rock_x_offset, autocvar_weapon_position_fully_adjustable_rock_y_offset, autocvar_weapon_position_fully_adjustable_rock_z_offset, autocvar_weapon_position_fully_adjustable_rock_x_angle, autocvar_weapon_position_fully_adjustable_rock_y_angle, autocvar_weapon_position_fully_adjustable_rock_z_angle);
									}
								}
							}
						}
						else
						{
							if ((self.owner.weapon == IT_LIGHTNING))
							{
								self.initial_weapon_position_axe = 0;
								self.initial_weapon_position_shot1 = 0;
								self.initial_weapon_position_shot2 = 0;
								self.initial_weapon_position_nail1 = 0;
								self.initial_weapon_position_nail2 = 0;
								self.initial_weapon_position_gren = 0;
								self.initial_weapon_position_rock = 0;
								setmodel(self, "progs/v_light.mdl");
								if (((self.owner.button0 || ((self.owner.velocity != VEC_ORIGIN) && (self.owner.earthquake_finished < time))) || self.owner.super_damage_finished))
								{
									if ((self.owner.idletimer == 0))
									{
										if ((autocvar_weapon_position_fully_adjustable == 1))
										{
											self.origin_x = autocvar_weapon_position_fully_adjustable_light_x_offset;
											self.origin_y = autocvar_weapon_position_fully_adjustable_light_y_offset;
											self.origin_z = autocvar_weapon_position_fully_adjustable_light_z_offset;
											self.angles_x = autocvar_weapon_position_fully_adjustable_light_x_angle;
											self.angles_y = autocvar_weapon_position_fully_adjustable_light_y_angle;
											self.angles_z = autocvar_weapon_position_fully_adjustable_light_z_angle;
										}
										else
										{
											self.origin = VEC_ORIGIN;
											self.angles = VEC_ORIGIN;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_x_offset_downwards = 0;
										}
										else
										{
											self.weapon_anim_x_offset_downwards = 1;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_y_offset_downwards = 0;
										}
										else
										{
											self.weapon_anim_y_offset_downwards = 1;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_z_offset_downwards = 0;
										}
										else
										{
											self.weapon_anim_z_offset_downwards = 1;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_x_angles_downwards = 0;
										}
										else
										{
											self.weapon_anim_x_angles_downwards = 1;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_y_angles_downwards = 0;
										}
										else
										{
											self.weapon_anim_y_angles_downwards = 1;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_z_angles_downwards = 0;
										}
										else
										{
											self.weapon_anim_z_angles_downwards = 1;
										}
									}
								}
								else
								{
									if (((self.initial_weapon_position_light == 0) && !autocvar_mage_weapon))
									{
										self.initial_weapon_position_light = 1;
										if ((random() < 0.5))
										{
											self.weapon_anim_x_offset_downwards = 0;
										}
										else
										{
											self.weapon_anim_x_offset_downwards = 1;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_y_offset_downwards = 0;
										}
										else
										{
											self.weapon_anim_y_offset_downwards = 1;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_z_offset_downwards = 0;
										}
										else
										{
											self.weapon_anim_z_offset_downwards = 1;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_x_angles_downwards = 0;
										}
										else
										{
											self.weapon_anim_x_angles_downwards = 1;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_y_angles_downwards = 0;
										}
										else
										{
											self.weapon_anim_y_angles_downwards = 1;
										}
										if ((random() < 0.5))
										{
											self.weapon_anim_z_angles_downwards = 0;
										}
										else
										{
											self.weapon_anim_z_angles_downwards = 1;
										}
										if ((autocvar_weapon_position_fully_adjustable == 1))
										{
											self.origin_x = autocvar_weapon_position_fully_adjustable_light_x_offset;
											self.origin_y = autocvar_weapon_position_fully_adjustable_light_y_offset;
											self.origin_z = autocvar_weapon_position_fully_adjustable_light_z_offset;
											self.angles_x = autocvar_weapon_position_fully_adjustable_light_x_angle;
											self.angles_y = autocvar_weapon_position_fully_adjustable_light_y_angle;
											self.angles_z = autocvar_weapon_position_fully_adjustable_light_z_angle;
										}
										else
										{
											self.origin = VEC_ORIGIN;
											self.angles = VEC_ORIGIN;
										}
									}
									else
									{
										if (((self.v_weapon_animation < time) && !autocvar_mage_weapon))
										{
											if ((autocvar_weapon_position_fully_adjustable == 1))
											{
												idle_weapon_animation(autocvar_weapon_position_fully_adjustable_light_x_offset, autocvar_weapon_position_fully_adjustable_light_y_offset, autocvar_weapon_position_fully_adjustable_light_z_offset, autocvar_weapon_position_fully_adjustable_light_x_angle, autocvar_weapon_position_fully_adjustable_light_y_angle, autocvar_weapon_position_fully_adjustable_light_z_angle);
											}
											else
											{
												idle_weapon_animation(0, 0, 0, 0, 0, 0);
											}
										}
									}
								}
							}
							else
							{
								if ((self.owner.weapon == IT_AXE))
								{
									self.initial_weapon_position_shot1 = 0;
									self.initial_weapon_position_shot2 = 0;
									self.initial_weapon_position_nail1 = 0;
									self.initial_weapon_position_nail2 = 0;
									self.initial_weapon_position_gren = 0;
									self.initial_weapon_position_rock = 0;
									self.initial_weapon_position_light = 0;
									if (!autocvar_zombieaxeanimation)
									{
										setmodel(self, "progs/v_hammer.mdl");
									}
									else
									{
										if ((self.owner.weaponmodel != ""))
										{
											setmodel(self, self.owner.weaponmodel);
										}
									}
									if (((self.owner.button0 || ((self.owner.velocity != VEC_ORIGIN) && (self.owner.earthquake_finished < time))) || self.owner.super_damage_finished))
									{
										if ((self.owner.idletimer == 0))
										{
											self.origin_x = autocvar_weapon_position_fully_adjustable_axe_x_offset;
											self.origin_y = autocvar_weapon_position_fully_adjustable_axe_y_offset;
											self.origin_z = autocvar_weapon_position_fully_adjustable_axe_z_offset;
											self.angles_x = autocvar_weapon_position_fully_adjustable_axe_x_angle;
											self.angles_y = autocvar_weapon_position_fully_adjustable_axe_y_angle;
											self.angles_z = autocvar_weapon_position_fully_adjustable_axe_z_angle;
											if ((random() < 0.5))
											{
												self.weapon_anim_x_offset_downwards = 0;
											}
											else
											{
												self.weapon_anim_x_offset_downwards = 1;
											}
											if ((random() < 0.5))
											{
												self.weapon_anim_y_offset_downwards = 0;
											}
											else
											{
												self.weapon_anim_y_offset_downwards = 1;
											}
											if ((random() < 0.5))
											{
												self.weapon_anim_z_offset_downwards = 0;
											}
											else
											{
												self.weapon_anim_z_offset_downwards = 1;
											}
											if ((random() < 0.5))
											{
												self.weapon_anim_x_angles_downwards = 0;
											}
											else
											{
												self.weapon_anim_x_angles_downwards = 1;
											}
											if ((random() < 0.5))
											{
												self.weapon_anim_y_angles_downwards = 0;
											}
											else
											{
												self.weapon_anim_y_angles_downwards = 1;
											}
											if ((random() < 0.5))
											{
												self.weapon_anim_z_angles_downwards = 0;
											}
											else
											{
												self.weapon_anim_z_angles_downwards = 1;
											}
										}
									}
									else
									{
										if ((self.initial_weapon_position_axe == 0))
										{
											self.initial_weapon_position_axe = 1;
											if ((random() < 0.5))
											{
												self.weapon_anim_x_offset_downwards = 0;
											}
											else
											{
												self.weapon_anim_x_offset_downwards = 1;
											}
											if ((random() < 0.5))
											{
												self.weapon_anim_y_offset_downwards = 0;
											}
											else
											{
												self.weapon_anim_y_offset_downwards = 1;
											}
											if ((random() < 0.5))
											{
												self.weapon_anim_z_offset_downwards = 0;
											}
											else
											{
												self.weapon_anim_z_offset_downwards = 1;
											}
											if ((random() < 0.5))
											{
												self.weapon_anim_x_angles_downwards = 0;
											}
											else
											{
												self.weapon_anim_x_angles_downwards = 1;
											}
											if ((random() < 0.5))
											{
												self.weapon_anim_y_angles_downwards = 0;
											}
											else
											{
												self.weapon_anim_y_angles_downwards = 1;
											}
											if ((random() < 0.5))
											{
												self.weapon_anim_z_angles_downwards = 0;
											}
											else
											{
												self.weapon_anim_z_angles_downwards = 1;
											}
											self.origin_x = autocvar_weapon_position_fully_adjustable_axe_x_offset;
											self.origin_y = autocvar_weapon_position_fully_adjustable_axe_y_offset;
											self.origin_z = autocvar_weapon_position_fully_adjustable_axe_z_offset;
											self.angles_x = autocvar_weapon_position_fully_adjustable_axe_x_angle;
											self.angles_y = autocvar_weapon_position_fully_adjustable_axe_y_angle;
											self.angles_z = autocvar_weapon_position_fully_adjustable_axe_z_angle;
										}
										else
										{
											if ((self.v_weapon_animation < time))
											{
												idle_weapon_animation(autocvar_weapon_position_fully_adjustable_axe_x_offset, autocvar_weapon_position_fully_adjustable_axe_y_offset, autocvar_weapon_position_fully_adjustable_axe_z_offset, autocvar_weapon_position_fully_adjustable_axe_x_angle, autocvar_weapon_position_fully_adjustable_axe_y_angle, autocvar_weapon_position_fully_adjustable_axe_z_angle);
											}
										}
									}
								}
								else
								{
									if ((self.owner.weapon == IT_CHAINSAW))
									{
										self.initial_weapon_position_shot1 = 0;
										self.initial_weapon_position_shot2 = 0;
										self.initial_weapon_position_nail1 = 0;
										self.initial_weapon_position_nail2 = 0;
										self.initial_weapon_position_gren = 0;
										self.initial_weapon_position_rock = 0;
										self.initial_weapon_position_light = 0;
										if (!autocvar_zombieaxeanimation)
										{
											setmodel(self, "progs/v_saw.mdl");
										}
										else
										{
											if ((self.owner.weaponmodel != ""))
											{
												setmodel(self, self.owner.weaponmodel);
											}
										}
										if (((self.owner.button0 || ((self.owner.velocity != VEC_ORIGIN) && (self.owner.earthquake_finished < time))) || self.owner.super_damage_finished))
										{
											if ((self.owner.idletimer == 0))
											{
												self.origin_x = autocvar_weapon_position_fully_adjustable_axe_x_offset;
												self.origin_y = autocvar_weapon_position_fully_adjustable_axe_y_offset;
												self.origin_z = autocvar_weapon_position_fully_adjustable_axe_z_offset;
												self.angles_x = autocvar_weapon_position_fully_adjustable_axe_x_angle;
												self.angles_y = autocvar_weapon_position_fully_adjustable_axe_y_angle;
												self.angles_z = autocvar_weapon_position_fully_adjustable_axe_z_angle;
												if ((random() < 0.5))
												{
													self.weapon_anim_x_offset_downwards = 0;
												}
												else
												{
													self.weapon_anim_x_offset_downwards = 1;
												}
												if ((random() < 0.5))
												{
													self.weapon_anim_y_offset_downwards = 0;
												}
												else
												{
													self.weapon_anim_y_offset_downwards = 1;
												}
												if ((random() < 0.5))
												{
													self.weapon_anim_z_offset_downwards = 0;
												}
												else
												{
													self.weapon_anim_z_offset_downwards = 1;
												}
												if ((random() < 0.5))
												{
													self.weapon_anim_x_angles_downwards = 0;
												}
												else
												{
													self.weapon_anim_x_angles_downwards = 1;
												}
												if ((random() < 0.5))
												{
													self.weapon_anim_y_angles_downwards = 0;
												}
												else
												{
													self.weapon_anim_y_angles_downwards = 1;
												}
												if ((random() < 0.5))
												{
													self.weapon_anim_z_angles_downwards = 0;
												}
												else
												{
													self.weapon_anim_z_angles_downwards = 1;
												}
											}
										}
										else
										{
											if ((self.initial_weapon_position_axe == 0))
											{
												self.initial_weapon_position_axe = 1;
												if ((random() < 0.5))
												{
													self.weapon_anim_x_offset_downwards = 0;
												}
												else
												{
													self.weapon_anim_x_offset_downwards = 1;
												}
												if ((random() < 0.5))
												{
													self.weapon_anim_y_offset_downwards = 0;
												}
												else
												{
													self.weapon_anim_y_offset_downwards = 1;
												}
												if ((random() < 0.5))
												{
													self.weapon_anim_z_offset_downwards = 0;
												}
												else
												{
													self.weapon_anim_z_offset_downwards = 1;
												}
												if ((random() < 0.5))
												{
													self.weapon_anim_x_angles_downwards = 0;
												}
												else
												{
													self.weapon_anim_x_angles_downwards = 1;
												}
												if ((random() < 0.5))
												{
													self.weapon_anim_y_angles_downwards = 0;
												}
												else
												{
													self.weapon_anim_y_angles_downwards = 1;
												}
												if ((random() < 0.5))
												{
													self.weapon_anim_z_angles_downwards = 0;
												}
												else
												{
													self.weapon_anim_z_angles_downwards = 1;
												}
												self.origin_x = autocvar_weapon_position_fully_adjustable_axe_x_offset;
												self.origin_y = autocvar_weapon_position_fully_adjustable_axe_y_offset;
												self.origin_z = autocvar_weapon_position_fully_adjustable_axe_z_offset;
												self.angles_x = autocvar_weapon_position_fully_adjustable_axe_x_angle;
												self.angles_y = autocvar_weapon_position_fully_adjustable_axe_y_angle;
												self.angles_z = autocvar_weapon_position_fully_adjustable_axe_z_angle;
											}
											else
											{
												if ((self.v_weapon_animation < time))
												{
													idle_weapon_animation(autocvar_weapon_position_fully_adjustable_axe_x_offset, autocvar_weapon_position_fully_adjustable_axe_y_offset, autocvar_weapon_position_fully_adjustable_axe_z_offset, autocvar_weapon_position_fully_adjustable_axe_x_angle, autocvar_weapon_position_fully_adjustable_axe_y_angle, autocvar_weapon_position_fully_adjustable_axe_z_angle);
												}
											}
										}
									}
									else
									{
										if ((self.owner.weapon == IT_LASER_CANNON))
										{
											self.initial_weapon_position_shot1 = 0;
											self.initial_weapon_position_shot2 = 0;
											self.initial_weapon_position_nail1 = 0;
											self.initial_weapon_position_nail2 = 0;
											self.initial_weapon_position_gren = 0;
											self.initial_weapon_position_rock = 0;
											self.initial_weapon_position_light = 0;
											if (!autocvar_zombieaxeanimation)
											{
												if (autocvar_centered_weapons)
												{
													setmodel(self, "progs/centered/v_laserg.mdl");
												}
												else
												{
													setmodel(self, "progs/v_laserg.mdl");
												}
											}
											else
											{
												if ((self.owner.weaponmodel != ""))
												{
													setmodel(self, self.owner.weaponmodel);
												}
											}
											if (((self.owner.button0 || ((self.owner.velocity != VEC_ORIGIN) && (self.owner.earthquake_finished < time))) || self.owner.super_damage_finished))
											{
												if ((self.owner.idletimer == 0))
												{
													self.origin_x = autocvar_weapon_position_fully_adjustable_axe_x_offset;
													self.origin_y = autocvar_weapon_position_fully_adjustable_axe_y_offset;
													self.origin_z = autocvar_weapon_position_fully_adjustable_axe_z_offset;
													self.angles_x = autocvar_weapon_position_fully_adjustable_axe_x_angle;
													self.angles_y = autocvar_weapon_position_fully_adjustable_axe_y_angle;
													self.angles_z = autocvar_weapon_position_fully_adjustable_axe_z_angle;
													if ((random() < 0.5))
													{
														self.weapon_anim_x_offset_downwards = 0;
													}
													else
													{
														self.weapon_anim_x_offset_downwards = 1;
													}
													if ((random() < 0.5))
													{
														self.weapon_anim_y_offset_downwards = 0;
													}
													else
													{
														self.weapon_anim_y_offset_downwards = 1;
													}
													if ((random() < 0.5))
													{
														self.weapon_anim_z_offset_downwards = 0;
													}
													else
													{
														self.weapon_anim_z_offset_downwards = 1;
													}
													if ((random() < 0.5))
													{
														self.weapon_anim_x_angles_downwards = 0;
													}
													else
													{
														self.weapon_anim_x_angles_downwards = 1;
													}
													if ((random() < 0.5))
													{
														self.weapon_anim_y_angles_downwards = 0;
													}
													else
													{
														self.weapon_anim_y_angles_downwards = 1;
													}
													if ((random() < 0.5))
													{
														self.weapon_anim_z_angles_downwards = 0;
													}
													else
													{
														self.weapon_anim_z_angles_downwards = 1;
													}
												}
											}
											else
											{
												if ((self.initial_weapon_position_axe == 0))
												{
													self.initial_weapon_position_axe = 1;
													if ((random() < 0.5))
													{
														self.weapon_anim_x_offset_downwards = 0;
													}
													else
													{
														self.weapon_anim_x_offset_downwards = 1;
													}
													if ((random() < 0.5))
													{
														self.weapon_anim_y_offset_downwards = 0;
													}
													else
													{
														self.weapon_anim_y_offset_downwards = 1;
													}
													if ((random() < 0.5))
													{
														self.weapon_anim_z_offset_downwards = 0;
													}
													else
													{
														self.weapon_anim_z_offset_downwards = 1;
													}
													if ((random() < 0.5))
													{
														self.weapon_anim_x_angles_downwards = 0;
													}
													else
													{
														self.weapon_anim_x_angles_downwards = 1;
													}
													if ((random() < 0.5))
													{
														self.weapon_anim_y_angles_downwards = 0;
													}
													else
													{
														self.weapon_anim_y_angles_downwards = 1;
													}
													if ((random() < 0.5))
													{
														self.weapon_anim_z_angles_downwards = 0;
													}
													else
													{
														self.weapon_anim_z_angles_downwards = 1;
													}
													self.origin_x = autocvar_weapon_position_fully_adjustable_axe_x_offset;
													self.origin_y = autocvar_weapon_position_fully_adjustable_axe_y_offset;
													self.origin_z = autocvar_weapon_position_fully_adjustable_axe_z_offset;
													self.angles_x = autocvar_weapon_position_fully_adjustable_axe_x_angle;
													self.angles_y = autocvar_weapon_position_fully_adjustable_axe_y_angle;
													self.angles_z = autocvar_weapon_position_fully_adjustable_axe_z_angle;
												}
												else
												{
													if ((self.v_weapon_animation < time))
													{
														idle_weapon_animation(autocvar_weapon_position_fully_adjustable_axe_x_offset, autocvar_weapon_position_fully_adjustable_axe_y_offset, autocvar_weapon_position_fully_adjustable_axe_z_offset, autocvar_weapon_position_fully_adjustable_axe_x_angle, autocvar_weapon_position_fully_adjustable_axe_y_angle, autocvar_weapon_position_fully_adjustable_axe_z_angle);
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
	if ((self.owner.weapon == IT_MEGAMAN))
	{
		setmodel(self, MM_PickVModel());
		self.origin = '0 0 0';
		self.angles = '0 0 0';
	}
	if ((self.owner.weapon == IT_FUNGUN))
	{
		setmodel(self, FunGun_VModel(self.owner.fg_sel));
		self.origin = '0 0 0';
		self.angles = '0 0 0';
	}
	self.owner.weaponmodel = "";
	self.frame = self.owner.weaponframe;
	if ((invisweapon && self.owner.invisible_finished))
	{
		self.alpha = 0.3;
	}
	else
	{
		if ((!invisweapon && self.owner.invisible_finished))
		{
			self.alpha = -1;
		}
		else
		{
			self.alpha = 1;
		}
	}
	Milky_ViewFrame (self);	// which Milky Gun clip, and when the hand is put away (milky.qc)
	Pickle_ViewFrame (self, FALSE);	// articulated Pickle Surprise idle, throw, follow-through & reload (pickle.qc)
	if ((self.owner.fl_phase == 1) || (self.owner.fl_phase == 2) || (self.owner.bm_rl_slot && self.owner.health > 0 && !(M4_ShowsReload (self.owner) || Garand_ShowsReload (self.owner))) || FD_Flying(self.owner) || Veh_Driving(self.owner) || JohnBird_Flying(self.owner) || RocketRider_Flying(self.owner) || EricCannon_Active(self.owner) || MMTank_Driving(self.owner) || Binoc_On(self.owner))
	{
		self.alpha = -1;	// the gun is put away while it reloads (bm_reload.qc), and while flying a Rob Dob head
	}
	self.nextthink = time;
	self.owner.gunof = self.origin;
	self.owner.gunang = self.angles;
	self.gunidleof_x = self.weapon_anim_y_offset_downwards;
	self.gunidleof_y = self.weapon_anim_y_offset_downwards;
	self.gunidleof_z = self.weapon_anim_y_offset_downwards;
	self.gunidleang_x = self.weapon_anim_y_angles_downwards;
	self.gunidleang_y = self.weapon_anim_y_angles_downwards;
	self.gunidleang_z = self.weapon_anim_z_angles_downwards;
};

void(entity e) v_weapon_position =
{
	newmis = spawn();
	newmis.owner = e;
	newmis.viewmodelforclient = self;
	newmis.think = v_weapon_position_think;
	newmis.nextthink = time;
};

void() update_weapon_range_crosshair =
{
	local vector source;

	makevectors(self.v_angle);
	source = self.origin + '0 0 16';
	if ((self.weapon == IT_AXE))
	{
		traceline(source, (source + (v_forward * 72)), FALSE, self);
	}
	else
	{
		if ((self.weapon == IT_SHOTGUN))
		{
			traceline(source, (source + (v_forward * 2048)), FALSE, self);
		}
		else
		{
			if ((self.weapon == IT_SUPER_SHOTGUN))
			{
				traceline(source, (source + (v_forward * 2048)), FALSE, self);
			}
			else
			{
				if ((self.weapon == IT_NAILGUN))
				{
					traceline(source, (source + (v_forward * 2048)), FALSE, self);
				}
				else
				{
					if ((self.weapon == IT_SUPER_NAILGUN))
					{
						traceline(source, (source + (v_forward * 2048)), FALSE, self);
					}
					else
					{
						if ((self.weapon == IT_GRENADE_LAUNCHER))
						{
							traceline(source, (source + (v_forward * 777)), FALSE, self);
						}
						else
						{
							if ((self.weapon == IT_ROCKET_LAUNCHER))
							{
								traceline(source, (source + (v_forward * 2048)), FALSE, self);
							}
							else
							{
								if ((self.weapon == IT_LIGHTNING))
								{
									traceline(source, (source + (v_forward * 600)), FALSE, self);
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
	if ((((trace_ent.takedamage == DAMAGE_AIM) && (trace_ent.health > 0)) && !trace_ent.i_am_a_corpse))
	{
		BM_Crosshair("0", "1", "0");
	}
	else
	{
		BM_Crosshair("1", "0", "0");
	}
};

void() update_player_health_crosshair =
{
	if ((self.health >= 80))
	{
		BM_Crosshair("0", "1", "0");
	}
	else
	{
		if ((self.health >= 60))
		{
			BM_Crosshair("0.7", "1.1", "0");
		}
		else
		{
			if ((self.health >= 40))
			{
				BM_Crosshair("1.1", "0.93", "0");
			}
			else
			{
				if ((self.health >= 20))
				{
					BM_Crosshair("1", "0.55", "0");
				}
				else
				{
					BM_Crosshair("1", "0", "0");
				}
			}
		}
	}
};

void() update_monster_health_crosshair =
{
	local vector source;

	makevectors(self.v_angle);
	source = self.origin + '0 0 16';
	traceline(source, (source + (v_forward * 2048)), FALSE, self);
	if ((((((trace_ent.takedamage == DAMAGE_AIM) && (trace_ent.health > 0)) && !trace_ent.i_am_a_corpse) && (trace_ent.model != "maps/b_explob.bsp")) && (trace_ent.model != "maps/b_exbox2.bsp")))
	{
		if ((trace_ent.classname != "monster_zombie"))
		{
			local float hmax, hfrac;
			hmax = trace_ent.health_initial;
			if ((hmax <= 0))
				hmax = trace_ent.max_health;
			if ((hmax <= 0))
				hmax = trace_ent.health;
			hfrac = trace_ent.health / hmax;
			if ((hfrac >= 0.85))
			{
				BM_Crosshair("0", "1", "0");
			}
			else if ((hfrac >= 0.63))
			{
				BM_Crosshair("0.7", "1.1", "0");
			}
			else if ((hfrac >= 0.4))
			{
				BM_Crosshair("1.1", "0.93", "0");
			}
			else if ((hfrac >= 0.15))
			{
				BM_Crosshair("1", "0.55", "0");
			}
			else
			{
				BM_Crosshair("1", "0", "0");
			}
		}
		else
		{
			BM_Crosshair("0", "1", "0");
		}
	}
	else
	{
		BM_Crosshair("1", "0", "0");
	}
};

void() player_legs_animation =
{
	if (!autocvar_player_legs_visibility)
	{
		self.owner.visible_legs_helper = 0;
		remove(self);
		return;
	}
	cvar("chase_active");
	if ((cvar("chase_active") || self.owner.invisible_finished))
	{
		self.alpha = -1;
	}
	else
	{
		self.alpha = 1;
	}
	makevectors(self.owner.angles);
	if (((self.owner.angles_x <= -9) && (self.owner.health >= 0)))
	{
		if ((autocvar_player_legs_visibility == 3))
		{
			self.origin = ((self.owner.origin + (v_up * 7)) + (v_forward * -20));
		}
		else
		{
			if ((autocvar_player_legs_visibility == 2))
			{
				self.origin = ((self.owner.origin + (v_up * 7)) + (v_forward * -15));
			}
			else
			{
				self.origin = ((self.owner.origin + (v_up * 7)) + (v_forward * -10));
			}
		}
		self.angles = self.owner.angles;
		self.angles_x = 15;
		if ((autocvar_player_legs_model == 1))
		{
			if ((self.owner.items & IT_SUIT))
			{
				setmodel(self, "progs/player_legs1_suit.mdl");
			}
			else
			{
				setmodel(self, "progs/player_legs1.mdl");
			}
		}
		else
		{
			setmodel(self, "progs/player_legs2.mdl");
		}
		setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	}
	else
	{
		setmodel(self, "");
	}
	self.solid = 0;
	self.frame = self.owner.frame;
	self.think = player_legs_animation;
	self.nextthink = time;
};

void(entity e) player_legs =
{
	local entity shaderrr;

	shaderrr = spawn();
	shaderrr.skin = 0;
	shaderrr.owner = e;
	shaderrr.think = player_legs_animation;
	shaderrr.colormap = e.colormap;
	shaderrr.nextthink = time;
};

void() switch_saw =
{
	setmodel(self, "progs/player_id1.mdl");
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
};

void() switch_vweps =
{
	if ((self.health >= -40))
	{
		if ((self.weapon == IT_AXE))
		{
			setmodel(self, "progs/player_shot.mdl");
			setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
		}
		else
		{
			if ((self.weapon == IT_SHOTGUN))
			{
				setmodel(self, "progs/player_shot.mdl");
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
			}
			else
			{
				if ((self.weapon == IT_SUPER_SHOTGUN))
				{
					setmodel(self, "progs/player_shot2.mdl");
					setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				}
				else
				{
					if ((self.weapon == IT_NAILGUN))
					{
						setmodel(self, "progs/player_nail.mdl");
						setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
					}
					else
					{
						if ((self.weapon == IT_SUPER_NAILGUN))
						{
							setmodel(self, "progs/player_nail2.mdl");
							setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
						}
						else
						{
							if ((self.weapon == IT_GRENADE_LAUNCHER))
							{
								setmodel(self, "progs/player_rock.mdl");
								setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
							}
							else
							{
								if ((self.weapon == IT_ROCKET_LAUNCHER))
								{
									setmodel(self, "progs/player_rock2.mdl");
									setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
								}
								else
								{
									if ((self.weapon == IT_LIGHTNING))
									{
										setmodel(self, "progs/player_light.mdl");
										setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
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

void() Quake3_quad_effect_3rd_think =
{
	if (intermission_running)
	{
		remove(self);
		return;
	}
	if (!cvar("chase_active"))
	{
		remove(self);
		return;
	}
	if (!self.owner.super_damage_finished)
	{
		remove(self);
		return;
	}
	setmodel(self, self.owner.model);
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	self.origin = self.owner.origin;
	self.frame = self.owner.frame;
	self.angles = self.owner.angles;
	self.think = Quake3_quad_effect_3rd_think;
	self.nextthink = time;
};

void(entity e) add_Quake3_quad_effect_3rd =
{
	local entity shaderr;

	shaderr = spawn();
	shaderr.skin = 1;
	shaderr.owner = e;
	shaderr.alpha = 0.5;
	shaderr.colormod = '0 0 0.5';
	shaderr.think = Quake3_quad_effect_3rd_think;
	shaderr.nextthink = time;
};

void() Quake3_quad_effect_1st_think =
{
	if (intermission_running)
	{
		remove(self);
		return;
	}
	if ((self.owner.meleeing == 1))
	{
		self.alpha = -1;
		self.think = Quake3_quad_effect_1st_think;
		self.nextthink = time;
		return;
	}
	else
	{
		self.alpha = 0.5;
	}
	if (cvar("chase_active"))
	{
		remove(self);
		return;
	}
	if (!self.owner.super_damage_finished)
	{
		remove(self);
		return;
	}
	if ((!invisweapon && self.owner.invisible_finished))
	{
		remove(self);
		return;
	}
	setmodel(self, self.owner.weaponmodel);
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	self.solid = 0;
	self.frame = self.owner.weaponframe;
	self.think = Quake3_quad_effect_1st_think;
	self.nextthink = time;
};

void(entity e) add_Quake3_quad_effect_1st =
{
	local entity shaderr;

	shaderr = spawn();
	shaderr.skin = 1;
	shaderr.owner = e;
	shaderr.alpha = 0.5;
	shaderr.colormod = '0 0 0.5';
	shaderr.viewmodelforclient = self;
	shaderr.think = Quake3_quad_effect_1st_think;
	shaderr.nextthink = time;
};

void() add_Quake3_quad_effect_1st_legs_think =
{
	if (!self.owner.super_damage_finished)
	{
		remove(self);
		return;
	}
	cvar("chase_active");
	if ((cvar("chase_active") || self.owner.invisible_finished))
	{
		self.alpha = -1;
	}
	else
	{
		self.alpha = 1;
	}
	makevectors(self.owner.angles);
	if (((self.owner.angles_x <= -9) && (self.owner.health >= 0)))
	{
		if ((autocvar_player_legs_visibility == 3))
		{
			self.origin = ((self.owner.origin + (v_up * 7)) + (v_forward * -20));
		}
		else
		{
			if ((autocvar_player_legs_visibility == 2))
			{
				self.origin = ((self.owner.origin + (v_up * 7)) + (v_forward * -15));
			}
			else
			{
				self.origin = ((self.owner.origin + (v_up * 7)) + (v_forward * -10));
			}
		}
		self.angles = self.owner.angles;
		self.angles_x = 15;
		if ((autocvar_player_legs_model == 1))
		{
			setmodel(self, "progs/player_legs1.mdl");
		}
		else
		{
			setmodel(self, "progs/player_legs2.mdl");
		}
		setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	}
	else
	{
		setmodel(self, "");
	}
	self.solid = 0;
	self.frame = self.owner.frame;
	self.think = add_Quake3_quad_effect_1st_legs_think;
	self.nextthink = time;
};

void(entity e) add_Quake3_quad_effect_1st_legs =
{
	local entity shaderrrr;

	shaderrrr = spawn();
	shaderrrr.skin = 1;
	shaderrrr.owner = e;
	shaderrrr.alpha = 0.5;
	shaderrrr.colormod = '0 0 0.5';
	shaderrrr.think = add_Quake3_quad_effect_1st_legs_think;
	shaderrrr.nextthink = time;
};

void() lightninggun_death_fade1 =
{
	local float countdown;

	self.magiccounter = (self.magiccounter - 1);
	countdown = 1 / (autocvar_coaled_monster_fadetime * 10);
	if ((self.magiccounter >= 0))
	{
		self.alpha = (self.alpha - countdown);
		self.think = lightninggun_death_fade1;
		self.nextthink = (time + 0.1);
	}
	else
	{
		self.think = SUB_Remove;
		self.nextthink = time;
	}
};

void() lightninggun_death_fade =
{
	self.solid = 0;
	self.colormod = '0.25 0.22 0.22';
	self.alpha = 1;
	self.magiccounter = (autocvar_coaled_monster_fadetime * 10);
	if (self.backpack_thrower)
	{
		DropBackpack();
	}
	lightninggun_death_fade1();
};

void() corpse_burn_out =
{
	local float countdown;

	self.magiccounter = (self.magiccounter - 1);
	countdown = 1 / (autocvar_burning_monsters_fade_animation_time * 12);
	if ((self.magiccounter >= 0))
	{
		if ((self.colormod_x >= 0.12))
		{
			self.colormod_x = (self.colormod_x - countdown);
			self.colormod_y = (self.colormod_y - countdown);
			self.colormod_z = (self.colormod_z - countdown);
		}
		self.think = corpse_burn_out;
		self.nextthink = (time + 0.1);
	}
	else
	{
		sound(self, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
		self.traileffectnum = particleeffectnum(/*12483i*/"corpse_charred");
		self.colormod = '0.14 0.14 0.14';
	}
};

void() inflamed_die =
{
	local vector check;

	check = (self.origin - '0 0 20') + '0 0 1';
	if (((pointcontents(check) != CONTENT_WATER) && (pointcontents(check) != CONTENT_SLIME)))
	{
		self.traileffectnum = particleeffectnum(/*12498i*/"corpse_burn");
		sound(self, CHAN_WEAPON, "zombie/corpse_fire.wav", 1, ATTN_NORM);
		self.alpha = 1;
		self.magiccounter = (autocvar_burning_monsters_fade_animation_time * 10);
		self.think = corpse_burn_out;
		self.nextthink = time;
		return;
	}
};

void() protective_shield_entity_think =
{
	self.scale = 11;
	self.alpha = 1;
	self.protective_shield_spawned = 1;
	if ((self.owner.health < 0))
	{
		remove(self);
		return;
	}
	makevectors(self.angles);
	setorigin(self, ('0 0 -68' + (v_forward * -7)));
	self.think = protective_shield_entity_think;
	self.nextthink = (time + 0.01);
};

float() motion_blur_owner_alive =
{
	if (!autocvar_demon_jump_motion_blur || (self.owner == world) || bm_wasfreed(self.owner) || (self.owner.health <= 0) || ((self.owner.classname != "monster_demon1") && (self.owner.classname != "monster_warlord")))
	{
		remove(self);
		return FALSE;
	}
	return TRUE;
};

void() motion_blur_entity_think =
{
	if (!motion_blur_owner_alive())
		return;
	if (self.owner.tail_visible)
	{
		self.alpha = (0.6 - (0.6 * (autocvar_demon_jump_motion_blur / 10)));
	}
	else
	{
		self.alpha = -1;
	}
	self.frame = self.owner.frame;
	self.scale = 1.07;
	makevectors(self.angles);
	setorigin(self, (VEC_ORIGIN + (v_forward * -5)));
	self.think = motion_blur_entity_think;
	self.nextthink = (time + 0.01);
};

void() motion_blur_entity1_think =
{
	if (!motion_blur_owner_alive())
		return;
	if (self.owner.tail_visible)
	{
		self.alpha = (0.5 - (0.5 * (autocvar_demon_jump_motion_blur / 10)));
	}
	else
	{
		self.alpha = -1;
	}
	self.frame = self.owner.frame;
	self.scale = 1.14;
	makevectors(self.angles);
	setorigin(self, (VEC_ORIGIN + (v_forward * -10)));
	self.think = motion_blur_entity1_think;
	self.nextthink = (time + 0.01);
};

void() motion_blur_entity2_think =
{
	if (!motion_blur_owner_alive())
		return;
	if (self.owner.tail_visible)
	{
		self.alpha = (0.4 - (0.4 * (autocvar_demon_jump_motion_blur / 10)));
	}
	else
	{
		self.alpha = -1;
	}
	self.frame = self.owner.frame;
	self.scale = 1.2;
	makevectors(self.angles);
	setorigin(self, (VEC_ORIGIN + (v_forward * -15)));
	self.think = motion_blur_entity2_think;
	self.nextthink = (time + 0.01);
};

void() motion_blur_entity3_think =
{
	if (!motion_blur_owner_alive())
		return;
	if (self.owner.tail_visible)
	{
		self.alpha = (0.3 - (0.3 * (autocvar_demon_jump_motion_blur / 10)));
	}
	else
	{
		self.alpha = -1;
	}
	self.frame = self.owner.frame;
	self.scale = 1.27;
	makevectors(self.angles);
	setorigin(self, (VEC_ORIGIN + (v_forward * -20)));
	self.think = motion_blur_entity3_think;
	self.nextthink = (time + 0.01);
};

void() motion_blur_entity4_think =
{
	if (!motion_blur_owner_alive())
		return;
	if (self.owner.tail_visible)
	{
		self.alpha = (0.2 - (0.2 * (autocvar_demon_jump_motion_blur / 10)));
	}
	else
	{
		self.alpha = -1;
	}
	self.frame = self.owner.frame;
	self.scale = 1.33;
	makevectors(self.angles);
	setorigin(self, (VEC_ORIGIN + (v_forward * -25)));
	self.think = motion_blur_entity4_think;
	self.nextthink = (time + 0.01);
};

void() motion_blur_entity5_think =
{
	if (!motion_blur_owner_alive())
		return;
	if (self.owner.tail_visible)
	{
		self.alpha = (0.1 - (0.1 * (autocvar_demon_jump_motion_blur / 10)));
	}
	else
	{
		self.alpha = -1;
	}
	self.frame = self.owner.frame;
	self.scale = 1.4;
	makevectors(self.angles);
	setorigin(self, (VEC_ORIGIN + (v_forward * -30)));
	self.think = motion_blur_entity5_think;
	self.nextthink = (time + 0.01);
};

void() pain_skin_entity_think =
{
	if (((autocvar_painskin_transparency == 0) || (self.owner == world) || bm_wasfreed(self.owner) || (self.owner.delete_painskin == 1)))
	{
		remove(self);
		return;
	}
	self.frame = self.owner.frame;
	self.alpha = autocvar_painskin_transparency;
	if ((self.owner.health < self.owner.health_initial))
	{
		if ((self.owner.health < (0.5 * self.owner.health_initial)))
		{
			if ((self.owner.painskin_helper == 2))
			{
				self.skin = 9;
			}
			else
			{
				if ((self.owner.painskin_helper == 3))
				{
					self.skin = 6;
					if (((self.owner.skin == 1) || (self.owner.skin == 2)))
					{
						self.alpha = (autocvar_painskin_transparency - 0.1);
					}
				}
				else
				{
					self.skin = 3;
				}
			}
		}
		else
		{
			if ((self.owner.painskin_helper == 2))
			{
				self.skin = 8;
			}
			else
			{
				if ((self.owner.painskin_helper == 3))
				{
					self.skin = 5;
					if (((self.owner.skin == 1) || (self.owner.skin == 2)))
					{
						self.alpha = (autocvar_painskin_transparency - 0.1);
					}
				}
				else
				{
					self.skin = 2;
				}
			}
		}
	}
	if ((self.owner.painskin_helper == 1))
	{
		self.skin = 4;
	}
	self.think = pain_skin_entity_think;
	self.nextthink = time;
};

void() pain_skin_entity_corpse_think =
{
	if (((autocvar_painskin_transparency == 0) || (self.owner == world) || bm_wasfreed(self.owner) || (self.owner.delete_painskin == 1) || (self.owner.model == "") || (self.model != self.owner.model)))
	{
		remove(self);
		return;
	}
	self.frame = self.owner.frame;
	self.alpha = autocvar_painskin_transparency;
	if ((self.owner.painskin_helper == 1))
	{
		self.skin = 4;
	}
	else
	{
		if ((self.owner.painskin_helper == 2))
		{
			self.skin = 9;
		}
		else
		{
			if ((self.owner.painskin_helper == 3))
			{
				self.skin = 6;
				if (((self.owner.skin == 1) || (self.owner.skin == 2)))
				{
					self.alpha = (autocvar_painskin_transparency - 0.1);
				}
			}
			else
			{
				self.skin = 3;
			}
		}
	}
	self.think = pain_skin_entity_corpse_think;
	self.nextthink = time;
};

void() player_teleporter_entity_think =
{
	local vector front_pos;
	local vector vec;

	if ((self.owner.health < 1))
	{
		self.owner.personal_teleporter_spawned = 0;
		self.owner.personal_teleporter_start_beam = 0;
		remove(self);
		return;
	}
	if ((self.maxlifetime < time))
	{
		self.owner.personal_teleporter_spawned = 0;
		self.owner.personal_teleporter_start_beam = 0;
		remove(self);
		return;
	}
	self.frame = (self.frame + 1);
	if ((self.owner.weapon == IT_AXE))
	{
		if ((self.frame >= 6))
		{
			self.frame = 0;
		}
	}
	else
	{
		if ((self.frame >= 12))
		{
			self.frame = 6;
		}
	}
	if ((self.owner == world) || bm_wasfreed(self.owner) || (self.owner.classname != "player") || (self.owner.health <= 0))
	{
		remove(self);
		return;
	}
	if (self.owner.personal_teleporter_start_beam)
	{
		local vector dest;
		dest = self.origin + '0 0 1';
		self.owner.personal_teleporter_spawned = 0;
		self.owner.personal_teleporter_start_beam = 0;
		tracebox(dest, VEC_HULL_MIN, VEC_HULL_MAX, dest, FALSE, self.owner);
		if (trace_startsolid || trace_allsolid)
		{
			if (self.owner.ishuman == 1)
				sprint(self.owner, "Teleporter destination blocked!\n");
			remove(self);
			return;
		}
		setorigin(self.owner, dest);
		if ((random() < 0.5))
		{
			sound(self.owner, CHAN_AUTO, "misc/r_tele1.wav", 1, ATTN_NORM);
		}
		else
		{
			sound(self.owner, CHAN_AUTO, "misc/r_tele2.wav", 1, ATTN_NORM);
		}
		if (!deathmatch && !coop)
		{
			view_zoom_out = 1;
			self.owner.viewzoom = 0.01;
		}
		remove(self);
		return;
	}
	self.alpha = autocvar_personal_player_teleporter_transparency;
	if (autocvar_personal_player_teleporter_guiding)
	{
		makevectors(self.owner.v_angle);
	}
	else
	{
		makevectors(self.angles);
	}
	vec = normalize(v_forward);
	self.velocity = (vec * 250);
	self.velocity_z = 0;
	self.angles = vectoangles(self.velocity);
	self.angles_x = 0;
	traceline(self.origin, (self.origin - '0 0 100'), TRUE, self);
	if ((trace_fraction < 1) && ((self.origin_z - trace_endpos_z) > 30))
	{
		setorigin(self, (self.origin - '0 0 15'));
	}
	makevectors(self.angles);
	front_pos = self.origin + (v_forward * 45);
	traceline(front_pos, (front_pos - '0 0 100'), TRUE, self);
	if ((trace_fraction < 1) && ((self.origin_z - trace_endpos_z) < 22))
	{
		setorigin(self, (self.origin + '0 0 20'));
	}
	self.nextthink = (time + 0.1);
	self.think = player_teleporter_entity_think;
};

void(vector spawn_pos, vector spawn_vel) launch_player_teleporter_entity =
{
	local entity player_teleporter_entity;

	player_teleporter_entity = spawn();
	player_teleporter_entity.owner = self;
	player_teleporter_entity.enemy = self;
	player_teleporter_entity.solid = SOLID_SLIDEBOX;
	player_teleporter_entity.movetype = MOVETYPE_FLY;
	player_teleporter_entity.velocity = (spawn_vel * 250);
	player_teleporter_entity.angles = vectoangles(player_teleporter_entity.velocity);
	player_teleporter_entity.angles_x = 0;
	if ((self.weapon == IT_AXE))
	{
		player_teleporter_entity.frame = 0;
	}
	else
	{
		player_teleporter_entity.frame = 6;
	}
	player_teleporter_entity.alpha = autocvar_personal_player_teleporter_transparency;
	player_teleporter_entity.skin = 2;
	player_teleporter_entity.colormod = '0.9 0.5 0.2';
	player_teleporter_entity.classname = "player_teleporter_entity";
	player_teleporter_entity.think = player_teleporter_entity_think;
	player_teleporter_entity.nextthink = time;
	player_teleporter_entity.maxlifetime = (time + 5);
	player_teleporter_entity.health = 1;
	setmodel(player_teleporter_entity, "progs/player_id1.mdl");
	setsize(player_teleporter_entity, VEC_HULL_MIN, VEC_HULL_MAX);
	setorigin(player_teleporter_entity, spawn_pos);
};

void() player_teleport =
{
	local vector org;
	local vector vec;

	makevectors(self.v_angle);
	org = self.origin + '0 0 1';
	vec = normalize(v_forward);
	sound(self, CHAN_AUTO, "player/personal_player_teleport.wav", 1, ATTN_NORM);
	self.personal_teleporter_spawned = 1;
	launch_player_teleporter_entity(org, vec);
};

void() seven_think_old =
{
	self.nextthink = (time + 0.000650);
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
};

void() seven_think1 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think2 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think3 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think4 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think5 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think6 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think7 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think8 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think9 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think10 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think11 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think12 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think13 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think14 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think15 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think16 =
{
	pointparticles(particleeffectnum(self.model), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
};

void() seven_think_new =
{
	seven_think1();
	seven_think2();
	seven_think3();
	seven_think4();
	seven_think5();
	seven_think6();
	seven_think7();
	seven_think8();
	seven_think9();
	seven_think10();
	seven_think11();
	seven_think12();
	seven_think13();
	seven_think14();
	seven_think15();
	seven_think16();
};

void() seven_think =
{
	if (!autocvar_cl_particles_custom_effects)
	{
		return;
	}
	if (autocvar_darkplaces_build)
	{
		self.think = seven_think_new;
	}
	else
	{
		self.think = seven_think_old;
	}
	self.nextthink = (time + 0.01);
};

void() seven_init =
{
	if ((((((((((((autocvar_ent_00 == 1) && (self.cnt == 0)) || ((autocvar_ent_01 == 1) && (self.cnt == 1))) || ((autocvar_ent_02 == 1) && (self.cnt == 2))) || ((autocvar_ent_03 == 1) && (self.cnt == 3))) || ((autocvar_ent_04 == 1) && (self.cnt == 4))) || ((autocvar_ent_05 == 1) && (self.cnt == 5))) || ((autocvar_ent_06 == 1) && (self.cnt == 6))) || ((autocvar_ent_07 == 1) && (self.cnt == 7))) || ((autocvar_ent_08 == 1) && (self.cnt == 8))) || ((autocvar_ent_09 == 1) && (self.cnt == 9))))
	{
		self.think = seven_think;
		self.nextthink = (time + 0.01);
	}
	else
	{
		remove(self);
	}
};

void() eruption_touch =
{
	if ((other.classname != "player"))
	{
		return;
	}
	if (other.health)
	{
		T_Damage(other, self, self, 7);
		self.touch = SUB_Null;
		remove(self);
	}
};

void() spawn_lava_eruption =
{
	local float dX;
	local float dY;
	local float Xparticle;
	local float Yparticle;
	local float Zparticle;
	local float zufall;
	local vector eruption;
	local entity eruptiondamage;

	dX = self.Xbig - self.Xsmall;
	dY = self.Ybig - self.Ysmall;
	Xparticle = self.Xsmall + (random() * dX);
	Yparticle = self.Ysmall + (random() * dY);
	Zparticle = self.Zheight;
	eruption_x = Xparticle;
	eruption_y = Yparticle;
	eruption_z = Zparticle;
	eruptiondamage = spawn();
	setorigin(eruptiondamage, eruption);
	eruptiondamage.velocity = VEC_ORIGIN;
	eruptiondamage.movetype = 0;
	eruptiondamage.solid = SOLID_TRIGGER;
	eruptiondamage.touch = eruption_touch;
	eruptiondamage.think = SUB_Remove;
	if (!self.variation)
	{
		self.variation = 5;
	}
	if ((self.variation == 1))
	{
		pointparticles(particleeffectnum(/*12628i*/"lava_eruption_small"), eruption, VEC_ORIGIN, 1);
		pointsound(eruption, /*12648i*/"ambience/lava_eruption_small.wav", 1, ATTN_NORM);
		setsize(eruptiondamage, '-15 -15 0', '15 15 45');
		eruptiondamage.nextthink = (time + 1);
	}
	else
	{
		if ((self.variation == 2))
		{
			pointparticles(particleeffectnum(/*12681i*/"lava_eruption_medium"), eruption, VEC_ORIGIN, 1);
			pointsound(eruption, /*12702i*/"ambience/lava_eruption_medium.wav", 1, ATTN_NORM);
			setsize(eruptiondamage, '-22 -22 0', '22 22 75');
			eruptiondamage.nextthink = (time + 1.3);
		}
		else
		{
			if ((self.variation == 3))
			{
				pointparticles(particleeffectnum(/*12736i*/"lava_eruption_large"), eruption, VEC_ORIGIN, 1);
				pointsound(eruption, /*12756i*/"ambience/lava_eruption_large.wav", 1, ATTN_NORM);
				setsize(eruptiondamage, '-30 -30 0', '30 30 115');
				eruptiondamage.nextthink = (time + 1.6);
			}
			else
			{
				if ((self.variation == 4))
				{
					zufall = random();
					if ((zufall < 0.5))
					{
						pointparticles(particleeffectnum(/*12628i*/"lava_eruption_small"), eruption, VEC_ORIGIN, 1);
						pointsound(eruption, /*12648i*/"ambience/lava_eruption_small.wav", 1, ATTN_NORM);
						setsize(eruptiondamage, '-15 -15 0', '15 15 45');
						eruptiondamage.nextthink = (time + 1);
					}
					else
					{
						pointparticles(particleeffectnum(/*12681i*/"lava_eruption_medium"), eruption, VEC_ORIGIN, 1);
						pointsound(eruption, /*12702i*/"ambience/lava_eruption_medium.wav", 1, ATTN_NORM);
						setsize(eruptiondamage, '-22 -22 0', '22 22 75');
						eruptiondamage.nextthink = (time + 1.3);
					}
				}
				else
				{
					zufall = random();
					if ((zufall < 0.33))
					{
						pointparticles(particleeffectnum(/*12628i*/"lava_eruption_small"), eruption, VEC_ORIGIN, 1);
						pointsound(eruption, /*12648i*/"ambience/lava_eruption_small.wav", 1, ATTN_NORM);
						setsize(eruptiondamage, '-15 -15 0', '15 15 45');
						eruptiondamage.nextthink = (time + 1);
					}
					else
					{
						if ((zufall > 0.66))
						{
							pointparticles(particleeffectnum(/*12681i*/"lava_eruption_medium"), eruption, VEC_ORIGIN, 1);
							pointsound(eruption, /*12702i*/"ambience/lava_eruption_medium.wav", 1, ATTN_NORM);
							setsize(eruptiondamage, '-22 -22 0', '22 22 75');
							eruptiondamage.nextthink = (time + 1.3);
						}
						else
						{
							pointparticles(particleeffectnum(/*12736i*/"lava_eruption_large"), eruption, VEC_ORIGIN, 1);
							pointsound(eruption, /*12756i*/"ambience/lava_eruption_large.wav", 1, ATTN_NORM);
							setsize(eruptiondamage, '-30 -30 0', '30 30 115');
							eruptiondamage.nextthink = (time + 1.6);
						}
					}
				}
			}
		}
	}
};

void() lava_think =
{
	self.nextthink = ((time + self.count) + (random() * 3));
	spawn_lava_eruption();
};

void() lava_init =
{
	if ((((((((((((autocvar_ent_00 == 1) && (self.cnt == 0)) || ((autocvar_ent_01 == 1) && (self.cnt == 1))) || ((autocvar_ent_02 == 1) && (self.cnt == 2))) || ((autocvar_ent_03 == 1) && (self.cnt == 3))) || ((autocvar_ent_04 == 1) && (self.cnt == 4))) || ((autocvar_ent_05 == 1) && (self.cnt == 5))) || ((autocvar_ent_06 == 1) && (self.cnt == 6))) || ((autocvar_ent_07 == 1) && (self.cnt == 7))) || ((autocvar_ent_08 == 1) && (self.cnt == 8))) || ((autocvar_ent_09 == 1) && (self.cnt == 9))))
	{
		precache_sound("ambience/lava_eruption_small.wav");
		precache_sound("ambience/lava_eruption_medium.wav");
		precache_sound("ambience/lava_eruption_large.wav");
		self.think = lava_think;
		self.nextthink = (time + 0.01);
	}
	else
	{
		remove(self);
	}
};

void() func_lava =
{
	precache_sound("ambience/lava_eruption_small.wav");
	precache_sound("ambience/lava_eruption_medium.wav");
	precache_sound("ambience/lava_eruption_large.wav");
	self.think = lava_think;
	self.nextthink = (time + 0.01);
};

void() callsound =
{
	pointsound(self.origin, self.model, self.alpha, ATTN_NORM);
};

void() sound_think =
{
	self.nextthink = (time + self.count);
	callsound();
};

void() sound_init =
{
	if ((((((((((((autocvar_ent_00 == 1) && (self.cnt == 0)) || ((autocvar_ent_01 == 1) && (self.cnt == 1))) || ((autocvar_ent_02 == 1) && (self.cnt == 2))) || ((autocvar_ent_03 == 1) && (self.cnt == 3))) || ((autocvar_ent_04 == 1) && (self.cnt == 4))) || ((autocvar_ent_05 == 1) && (self.cnt == 5))) || ((autocvar_ent_06 == 1) && (self.cnt == 6))) || ((autocvar_ent_07 == 1) && (self.cnt == 7))) || ((autocvar_ent_08 == 1) && (self.cnt == 8))) || ((autocvar_ent_09 == 1) && (self.cnt == 9))))
	{
		if (self.model != "")
			precache_sound(self.model);
		self.think = sound_think;
		self.nextthink = (time + 0.01);
	}
	else
	{
		remove(self);
	}
};

void() func_sound =
{
	self.think = sound_think;
	self.nextthink = (time + 0.01);
};
