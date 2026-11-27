//Decompiled code. Please respect the original copyright.

.float bm_dropped;	// a Shotgun Shell Pack dropped by a dying player: goes after 180 s or once taken, never respawns

void() SUB_regen =
{
	self.model = self.mdl;
	self.solid = SOLID_TRIGGER;
	sound(self, CHAN_VOICE, "items/itembk2.wav", 1, ATTN_NORM);
	setorigin(self, self.origin);
	if (((((self.model == "maps/b_batt0.bsp") || (self.model == "maps/b_shell0.bsp")) || (self.model == "maps/b_nail0.bsp")) || (self.model == "maps/b_rock0.bsp")))
	{
		self.scale = 0.85;
		setsize(self, VEC_ORIGIN, '24 24 24');
	}
	if ((autocvar_armorspecialeffect == 1))
	{
		if ((((self.model == "progs/armor.mdl") || (self.model == "progs/armor1.mdl")) && (self.skin == 0)))
		{
			self.nextthink = (time + 0.2);
			self.think = dummyeffectblink1_green_armor;
		}
		if ((((self.model == "progs/armor.mdl") || (self.model == "progs/armor1.mdl")) && (self.skin == 1)))
		{
			self.nextthink = (time + 0.2);
			self.think = dummyeffectblink1_yellow_armor;
		}
		if ((((self.model == "progs/armor.mdl") || (self.model == "progs/armor1.mdl")) && (self.skin == 2)))
		{
			self.nextthink = (time + 0.2);
			self.think = dummyeffectblink1_red_armor;
		}
	}
	if ((self.model == "maps/b_bh100heart.bsp"))
	{
		self.movetype = MOVETYPE_FLY;
		self.scale = 1;
		if (autocvar_darkplaces_build)
		{
			self.traileffectnum = particleeffectnum(/*19866i*/"megahealth_heart_new");
		}
		else
		{
			self.traileffectnum = particleeffectnum(/*19887i*/"megahealth_heart_old");
		}
		self.nextthink = (time + 0.2);
		self.think = megahealth_heart_movement;
	}
	if ((self.model == "maps/b_bh100cross.bsp"))
	{
		self.movetype = MOVETYPE_FLY;
		self.scale = 1;
		if (autocvar_darkplaces_build)
		{
			self.traileffectnum = particleeffectnum(/*19930i*/"megahealth_cross_new");
		}
		else
		{
			self.traileffectnum = particleeffectnum(/*19951i*/"megahealth_cross_old");
		}
	}
	if ((self.model == "maps/b_bh10custom1.bsp"))
	{
		self.movetype = MOVETYPE_FLY;
		self.scale = 0.85;
	}
	if ((self.model == "maps/b_bh25custom1.bsp"))
	{
		self.movetype = MOVETYPE_FLY;
		self.scale = 1;
	}
	if ((self.model == "maps/b_bh25.bsp"))
	{
		self.movetype = MOVETYPE_FLY;
		self.scale = 1.15;
	}
	if ((self.model == "progs/g_mage1.mdl"))
	{
		self.movetype = MOVETYPE_FLY;
		self.nextthink = (time + 0.2);
		self.think = g_mage1_effect;
	}
};

void() noclass =
{
	dprint("noclass spawned at");
	dprint(vtos(self.origin));
	dprint("\n");
	remove(self);
};

void() PlaceItem =
{
	local float oldz;

	self.mdl = self.model;
	self.flags = FL_ITEM;
	self.solid = SOLID_TRIGGER;
	self.movetype = MOVETYPE_TOSS;
	self.velocity = VEC_ORIGIN;
	self.origin_z = (self.origin_z + 6);
	oldz = self.origin_z;
	if (!droptofloor())
	{
		dprint("Bonus item fell out of level at ");
		dprint(vtos(self.origin));
		dprint("\n");
		remove(self);
		return;
	}
	if (((((self.model == "maps/b_batt0.bsp") || (self.model == "maps/b_shell0.bsp")) || (self.model == "maps/b_nail0.bsp")) || (self.model == "maps/b_rock0.bsp")))
	{
		self.scale = 0.85;
		setsize(self, VEC_ORIGIN, '24 24 24');
	}
	if ((autocvar_armorspecialeffect == 1))
	{
		if ((((self.model == "progs/armor.mdl") || (self.model == "progs/armor1.mdl")) && (self.skin == 0)))
		{
			self.nextthink = (time + 0.2);
			self.think = dummyeffectblink1_green_armor;
		}
		if ((((self.model == "progs/armor.mdl") || (self.model == "progs/armor1.mdl")) && (self.skin == 1)))
		{
			self.nextthink = (time + 0.2);
			self.think = dummyeffectblink1_yellow_armor;
		}
		if ((((self.model == "progs/armor.mdl") || (self.model == "progs/armor1.mdl")) && (self.skin == 2)))
		{
			self.nextthink = (time + 0.2);
			self.think = dummyeffectblink1_red_armor;
		}
	}
	if ((self.model == "maps/b_bh100heart.bsp"))
	{
		self.origin = (self.origin + '12 12 0');
		self.movetype = MOVETYPE_FLY;
		self.scale = 1;
		if (autocvar_darkplaces_build)
		{
			self.traileffectnum = particleeffectnum(/*19866i*/"megahealth_heart_new");
		}
		else
		{
			self.traileffectnum = particleeffectnum(/*19887i*/"megahealth_heart_old");
		}
		self.nextthink = (time + 0.2);
		self.think = megahealth_heart_movement;
	}
	if ((self.model == "maps/b_bh100cross.bsp"))
	{
		self.origin = (self.origin + '12 12 0');
		self.movetype = MOVETYPE_FLY;
		self.scale = 1;
		if (autocvar_darkplaces_build)
		{
			self.traileffectnum = particleeffectnum(/*19930i*/"megahealth_cross_new");
		}
		else
		{
			self.traileffectnum = particleeffectnum(/*19951i*/"megahealth_cross_old");
		}
	}
	if ((self.model == "maps/b_bh10custom1.bsp"))
	{
		self.origin = (self.origin + '12 12 0');
		self.movetype = MOVETYPE_FLY;
		self.scale = 0.85;
	}
	if ((self.model == "maps/b_bh25custom1.bsp"))
	{
		self.origin = (self.origin + '12 12 0');
		self.movetype = MOVETYPE_FLY;
		self.scale = 1;
	}
	if ((self.model == "maps/b_bh25.bsp"))
	{
		self.origin = (self.origin + '12 12 0');
		self.movetype = MOVETYPE_FLY;
		self.scale = 1.15;
	}
	if ((self.model == "progs/g_mage1.mdl"))
	{
		self.origin = (self.origin + '0 0 33');
		self.movetype = MOVETYPE_FLY;
		self.scale = 0.7;
		self.nextthink = (time + 0.2);
		self.think = g_mage1_effect;
	}
	if (autocvar_ammo_health_boxes_angle_randomness)
	{
		if (((((((((self.model == "maps/b_shell1.bsp") || (self.model == "maps/b_shell0.bsp")) || (self.model == "maps/b_nail1.bsp")) || (self.model == "maps/b_nail0.bsp")) || (self.model == "maps/b_rock1.bsp")) || (self.model == "maps/b_rock0.bsp")) || (self.model == "maps/b_batt1.bsp")) || (self.model == "maps/b_batt0.bsp")))
		{
			self.angles_y = (self.angles_y + (crandom() * autocvar_ammo_health_boxes_angle_randomness));
		}
		if ((((self.model == "maps/b_bh10.bsp") || (self.model == "maps/b_bh25.bsp")) || (self.model == "maps/b_bh100.bsp")))
		{
			self.angles_y = (self.angles_y + (crandom() * autocvar_ammo_health_boxes_angle_randomness));
		}
	}
	self.flashtarg = "yes";
};

void() StartItem =
{
	self.nextthink = (time + 0.2);
	self.think = PlaceItem;
};

void() megahealth_heart_movement2 =
{
	if ((self.scale > 0.92))
	{
		self.nextthink = (time + 0.014);
		self.scale = (self.scale - 0.007);
		self.think = megahealth_heart_movement2;
	}
	else
	{
		sound(self, CHAN_WEAPON, "ambience/heartbeat.wav", 1, 3);
		self.nextthink = time;
		self.think = megahealth_heart_movement;
	}
};

void() megahealth_heart_movement =
{
	if ((self.scale < 1.08))
	{
		self.nextthink = (time + 0.014);
		self.scale = (self.scale + 0.007);
		self.think = megahealth_heart_movement;
	}
	else
	{
		self.nextthink = time;
		self.think = megahealth_heart_movement2;
	}
};

void() health_touch_delay =
{
	self.touch = health_touch;
};

float(entity e, entity selv, float ignore) T_Heal =
{
	if ((e.health <= 0))
	{
		return (0);
	}
	// the null sound only cuts the burning loop: send it when there is one, not on every touch of a health box by a
	// full-health player (a sound packet to every client per touch, for nothing)
	if (e.inflamed)
		sound(e, 120, "misc/null.wav", 1, ATTN_NORM);
	e.poisoned = 0;
	e.inflamed = 0;
	if ((!ignore && (e.health >= other.max_health)))
	{
		return (0);
	}
	selv.healamount = ceil(selv.healamount);
	e.health = (e.health + selv.healamount);
	if (autocvar_lossless_health_pickup)
	{
		if ((!ignore && (e.health >= other.max_health)))
		{
			selv.healamount = (e.health - other.max_health);
			if ((selv.healamount == 0))
			{
				selv.crate_is_empty = 1;
			}
			e.health = other.max_health;
		}
		else
		{
			if (!ignore)
			{
				selv.crate_is_empty = 1;
			}
		}
	}
	else
	{
		if ((!ignore && (e.health >= other.max_health)))
		{
			e.health = other.max_health;
		}
	}
	if ((e.health > 250))
	{
		e.health = 250;
	}
	return (1);
};

void() item_health =
{
	self.touch = health_touch;
	if ((self.spawnflags & H_ROTTEN))
	{
		if (autocvar_health)
		{
			if ((world.worldtype == 2))
			{
				precache_model("maps/b_bh10.bsp");
				setmodel(self, "maps/b_bh10.bsp");
				precache_sound("items/r_item1.wav");
				self.noise = "items/r_item1.wav";
			}
			else
			{
				precache_model("maps/b_bh10custom1.bsp");
				setmodel(self, "maps/b_bh10custom1.bsp");
				precache_sound("items/r_item1_potion_small.wav");
				self.noise = "items/r_item1_potion_small.wav";
				self.traileffectnum = particleeffectnum(/*20278i*/"health_small");
			}
		}
		else
		{
			precache_model("maps/b_bh10.bsp");
			setmodel(self, "maps/b_bh10.bsp");
			precache_sound("items/r_item1.wav");
			self.noise = "items/r_item1.wav";
		}
		self.healamount = autocvar_medikit_small_health;
		self.healtype = 0;
	}
	else
	{
		if ((self.spawnflags & H_MEGA))
		{
			if ((autocvar_megahealth > 0))
			{
				if ((world.worldtype == 2))
				{
					precache_model("maps/b_bh100.bsp");
					setmodel(self, "maps/b_bh100.bsp");
					precache_sound("items/r_item2.wav");
					self.noise = "items/r_item2.wav";
				}
				else
				{
					precache_model("maps/b_bh100.bsp");
					precache_sound("items/r_item2.wav");
					precache_model("maps/b_bh100heart.bsp");
					precache_sound("ambience/heartbeat.wav");
					precache_sound("items/r_item2_heart_pickup.wav");
					if ((random() < 0.4))
					{
						setmodel(self, "maps/b_bh100.bsp");
						self.noise = "items/r_item2.wav";
					}
					else
					{
						setmodel(self, "maps/b_bh100heart.bsp");
						self.noise = "items/r_item2_heart_pickup.wav";
					}
				}
			}
			self.healamount = autocvar_medikit_mega_health;
			self.healtype = 2;
			self.traileffectnum = particleeffectnum(/*20340i*/"health_mega");
		}
		else
		{
			if (autocvar_health)
			{
				if ((world.worldtype == 2))
				{
					precache_model("maps/b_bh25.bsp");
					setmodel(self, "maps/b_bh25.bsp");
					precache_sound("items/health1.wav");
					self.noise = "items/health1.wav";
				}
				else
				{
					precache_model("maps/b_bh25custom1.bsp");
					setmodel(self, "maps/b_bh25custom1.bsp");
					precache_sound("items/health1_potion_medium.wav");
					self.noise = "items/health1_potion_medium.wav";
					self.traileffectnum = particleeffectnum(/*20402i*/"health_medium");
				}
			}
			else
			{
				precache_model("maps/b_bh25.bsp");
				setmodel(self, "maps/b_bh25.bsp");
				precache_sound("items/health1.wav");
				self.noise = "items/health1.wav";
			}
			self.healamount = autocvar_medikit_large_health;
			self.healtype = 1;
		}
	}
	self.initial_amount = self.healamount;
	setsize(self, VEC_ORIGIN, '20 20 12');
	StartItem();
};

void() health_touch =
{
	local string s;

	if ((other.classname != "player"))
	{
		return;
	}
	autocvar_lossless_health_pickup = 0;
	self.healamount_old = self.healamount;
	if ((self.healtype == 2))
	{
		if ((other.health >= 250))
		{
			return;
		}
		if (((self.model != "maps/b_bh100heart.bsp") && (autocvar_quadreplacer > 0)))
		{
			self.healamount = 50;
		}
		if (!T_Heal(other, self, 1))
		{
			return;
		}
		if ((coop && (autocvar_coop_life_pool == 1)))
		{
			LIFE_BONUS = PLR_CNT + -1;
			other.lives = (other.lives + 1);
			centerprint(other, "Life Bonus! ^2+1 lives ^8to all players");
		}
		if ((self.model != "maps/b_bh100heart.bsp"))
		{
			centerprint(other, "You got the Berserk Pack!");
			te_customflash(self.origin, 400, 500, '2 0 0');
			autocvar_berserkmode = 3.5;
		}
	}
	else
	{
		if (!T_Heal(other, self, 0))
		{
			return;
		}
	}
	if (autocvar_lossless_health_pickup)
	{
		sprint(other, "You received ");
		if ((!self.crate_is_empty && (self.healtype != 2)))
		{
			s = ftos((self.healamount_old - self.healamount));
		}
		else
		{
			s = ftos(self.healamount_old);
		}
		sprint(other, s);
		sprint(other, " health");
		if ((!self.crate_is_empty && (self.healtype != 2)))
		{
			sprint(other, ". Max health reached. ");
			s = ftos(self.healamount);
			sprint(other, s);
			sprint(other, " health remaining.");
		}
		sprint(other, "\n");
	}
	else
	{
		sprint(other, "You receive ");
		s = ftos(self.healamount);
		sprint(other, s);
		sprint(other, " health\n");
	}
	sound(other, CHAN_ITEM, self.noise, 1, ATTN_NORM);
	stuffcmd(other, "bf\n");
	if (autocvar_lossless_health_pickup)
	{
		if (((self.crate_is_empty == 1) || (self.healtype == 2)))
		{
			self.crate_is_empty = 0;
			self.healamount = self.initial_amount;
			if ((world.worldtype != 2))
			{
				if (((self.healtype == 0) && autocvar_health))
				{
					pointparticles(particleeffectnum(/*20568i*/"health10custom_touch"), self.origin, VEC_ORIGIN, 1);
				}
				else
				{
					if (((self.healtype == 1) && autocvar_health))
					{
						pointparticles(particleeffectnum(/*20589i*/"health25custom_touch"), self.origin, VEC_ORIGIN, 1);
					}
				}
			}
			self.model = string_null;
			self.solid = 0;
			if ((self.healtype == 2))
			{
				self.nextthink = (time + 5);
				self.think = item_megahealth_rot;
				self.owner = other;
			}
			else
			{
				if ((deathmatch != 2))
				{
					if (deathmatch)
					{
						self.nextthink = (time + 20);
					}
					self.think = SUB_regen;
				}
			}
			activator = other;
			SUB_UseTargets();
		}
		else
		{
			self.touch = SUB_Null;
			self.nextthink = (time + 1);
			self.think = health_touch_delay;
		}
	}
	else
	{
		if ((world.worldtype != 2))
		{
			if (((self.healtype == 0) && autocvar_health))
			{
				pointparticles(particleeffectnum(/*20568i*/"health10custom_touch"), self.origin, VEC_ORIGIN, 1);
			}
			else
			{
				if (((self.healtype == 1) && autocvar_health))
				{
					pointparticles(particleeffectnum(/*20589i*/"health25custom_touch"), self.origin, VEC_ORIGIN, 1);
				}
			}
		}
		self.model = string_null;
		self.solid = 0;
		if ((self.healtype == 2))
		{
			self.nextthink = (time + 5);
			self.think = item_megahealth_rot;
			self.owner = other;
		}
		else
		{
			if ((deathmatch != 2))
			{
				if (deathmatch)
				{
					self.nextthink = (time + 20);
				}
				self.think = SUB_regen;
			}
		}
		activator = other;
		SUB_UseTargets();
	}
};

void() item_megahealth_rot =
{
	other = self.owner;
	if ((other.health > other.max_health))
	{
		other.health = (other.health - 1);
		self.nextthink = (time + 1);
		return;
	}
	if ((deathmatch == 1))
	{
		self.nextthink = (time + 20);
		self.think = SUB_regen;
	}
};

void() armor_touch =
{
	local float type;
	local float value;
	local float bit;

	if ((other.health <= 0))
	{
		return;
	}
	if ((other.classname != "player"))
	{
		return;
	}
	if ((self.classname == "item_armor1"))
	{
		type = 0.3;
		value = autocvar_armor_green;
		bit = IT_ARMOR1;
	}
	if ((self.classname == "item_armor2"))
	{
		type = 0.6;
		value = autocvar_armor_yellow;
		bit = IT_ARMOR2;
	}
	if ((self.classname == "item_armorInv"))
	{
		type = 0.8;
		value = autocvar_armor_red;
		bit = IT_ARMOR3;
	}
	if (((other.armortype * other.armorvalue) >= (type * value)))
	{
		return;
	}
	other.armortype = type;
	other.armorvalue = value;
	other.items = ((other.items - (other.items & 57344)) + bit);
	self.solid = 0;
	self.model = string_null;
	if (deathmatch)
	{
		self.nextthink = (time + 20);
		self.think = SUB_regen;
	}
	else
	{
		self.think = SUB_Null;
		self.nextthink = -1;
	}
	sprint(other, "You got armor\n");
	sound(other, CHAN_ITEM, "items/armor1.wav", 1, ATTN_NORM);
	if ((autocvar_effects_explosion_shake != 0))
	{
		stuffcmd(other, "bf\n");
	}
	activator = other;
	SUB_UseTargets();
};

void() dummyeffectblink20_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20680i*/"armor_green_20");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink1_green_armor;
};

void() dummyeffectblink19_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20695i*/"armor_green_19");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink20_green_armor;
};

void() dummyeffectblink18_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20710i*/"armor_green_18");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink19_green_armor;
};

void() dummyeffectblink17_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20725i*/"armor_green_17");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink18_green_armor;
};

void() dummyeffectblink16_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20740i*/"armor_green_16");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink17_green_armor;
};

void() dummyeffectblink15_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20755i*/"armor_green_15");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink16_green_armor;
};

void() dummyeffectblink14_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20770i*/"armor_green_14");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink15_green_armor;
};

void() dummyeffectblink13_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20785i*/"armor_green_13");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink14_green_armor;
};

void() dummyeffectblink12_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20800i*/"armor_green_12");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink13_green_armor;
};

void() dummyeffectblink11_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20815i*/"armor_green_11");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink12_green_armor;
};

void() dummyeffectblink10_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20830i*/"armor_green_10");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink11_green_armor;
};

void() dummyeffectblink9_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20845i*/"armor_green_9");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink10_green_armor;
};

void() dummyeffectblink8_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20859i*/"armor_green_8");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink9_green_armor;
};

void() dummyeffectblink7_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20873i*/"armor_green_7");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink8_green_armor;
};

void() dummyeffectblink6_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20887i*/"armor_green_6");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink7_green_armor;
};

void() dummyeffectblink5_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20901i*/"armor_green_5");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink6_green_armor;
};

void() dummyeffectblink4_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20915i*/"armor_green_4");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink5_green_armor;
};

void() dummyeffectblink3_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20929i*/"armor_green_3");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink4_green_armor;
};

void() dummyeffectblink2_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20943i*/"armor_green_2");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink3_green_armor;
};

void() dummyeffectblink1_green_armor =
{
	self.traileffectnum = particleeffectnum(/*20957i*/"armor_green_1");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink2_green_armor;
};

void() item_armor1 =
{
	self.touch = armor_touch;
	if (autocvar_armor_model)
	{
		if ((world.worldtype == 2))
		{
			precache_model("progs/armor.mdl");
			setmodel(self, "progs/armor.mdl");
		}
		else
		{
			precache_model("progs/armor1.mdl");
			setmodel(self, "progs/armor1.mdl");
		}
	}
	else
	{
		precache_model("progs/armor.mdl");
		setmodel(self, "progs/armor.mdl");
	}
	if ((autocvar_armorspecialeffect == 2))
	{
		self.traileffectnum = particleeffectnum(/*20971i*/"green_armor");
	}
	self.skin = 0;
	setsize(self, '-16 -16 0', '16 16 56');
	StartItem();
};

void() dummyeffectblink20_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*20983i*/"armor_yellow_20");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink1_yellow_armor;
};

void() dummyeffectblink19_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*20999i*/"armor_yellow_19");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink20_yellow_armor;
};

void() dummyeffectblink18_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21015i*/"armor_yellow_18");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink19_yellow_armor;
};

void() dummyeffectblink17_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21031i*/"armor_yellow_17");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink18_yellow_armor;
};

void() dummyeffectblink16_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21047i*/"armor_yellow_16");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink17_yellow_armor;
};

void() dummyeffectblink15_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21063i*/"armor_yellow_15");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink16_yellow_armor;
};

void() dummyeffectblink14_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21079i*/"armor_yellow_14");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink15_yellow_armor;
};

void() dummyeffectblink13_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21095i*/"armor_yellow_13");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink14_yellow_armor;
};

void() dummyeffectblink12_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21111i*/"armor_yellow_12");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink13_yellow_armor;
};

void() dummyeffectblink11_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21127i*/"armor_yellow_11");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink12_yellow_armor;
};

void() dummyeffectblink10_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21143i*/"armor_yellow_10");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink11_yellow_armor;
};

void() dummyeffectblink9_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21159i*/"armor_yellow_9");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink10_yellow_armor;
};

void() dummyeffectblink8_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21174i*/"armor_yellow_8");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink9_yellow_armor;
};

void() dummyeffectblink7_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21189i*/"armor_yellow_7");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink8_yellow_armor;
};

void() dummyeffectblink6_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21204i*/"armor_yellow_6");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink7_yellow_armor;
};

void() dummyeffectblink5_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21219i*/"armor_yellow_5");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink6_yellow_armor;
};

void() dummyeffectblink4_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21234i*/"armor_yellow_4");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink5_yellow_armor;
};

void() dummyeffectblink3_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21249i*/"armor_yellow_3");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink4_yellow_armor;
};

void() dummyeffectblink2_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21264i*/"armor_yellow_2");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink3_yellow_armor;
};

void() dummyeffectblink1_yellow_armor =
{
	self.traileffectnum = particleeffectnum(/*21279i*/"armor_yellow_1");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink2_yellow_armor;
};

void() item_armor2 =
{
	self.touch = armor_touch;
	if (autocvar_armor_model)
	{
		if ((world.worldtype == 2))
		{
			precache_model("progs/armor.mdl");
			setmodel(self, "progs/armor.mdl");
		}
		else
		{
			precache_model("progs/armor1.mdl");
			setmodel(self, "progs/armor1.mdl");
		}
	}
	else
	{
		precache_model("progs/armor.mdl");
		setmodel(self, "progs/armor.mdl");
	}
	if ((autocvar_armorspecialeffect == 2))
	{
		self.traileffectnum = particleeffectnum(/*21294i*/"yellow_armor");
	}
	self.skin = 1;
	setsize(self, '-16 -16 0', '16 16 56');
	StartItem();
	Jetpack_ForArmor(self);	// a jetpack beside every yellow armor (jetpack.qc)
};

void() dummyeffectblink20_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21307i*/"armor_red_20");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink1_red_armor;
};

void() dummyeffectblink19_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21320i*/"armor_red_19");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink20_red_armor;
};

void() dummyeffectblink18_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21333i*/"armor_red_18");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink19_red_armor;
};

void() dummyeffectblink17_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21346i*/"armor_red_17");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink18_red_armor;
};

void() dummyeffectblink16_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21359i*/"armor_red_16");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink17_red_armor;
};

void() dummyeffectblink15_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21372i*/"armor_red_15");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink16_red_armor;
};

void() dummyeffectblink14_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21385i*/"armor_red_14");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink15_red_armor;
};

void() dummyeffectblink13_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21398i*/"armor_red_13");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink14_red_armor;
};

void() dummyeffectblink12_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21411i*/"armor_red_12");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink13_red_armor;
};

void() dummyeffectblink11_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21424i*/"armor_red_11");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink12_red_armor;
};

void() dummyeffectblink10_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21437i*/"armor_red_10");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink11_red_armor;
};

void() dummyeffectblink9_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21450i*/"armor_red_9");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink10_red_armor;
};

void() dummyeffectblink8_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21462i*/"armor_red_8");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink9_red_armor;
};

void() dummyeffectblink7_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21474i*/"armor_red_7");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink8_red_armor;
};

void() dummyeffectblink6_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21486i*/"armor_red_6");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink7_red_armor;
};

void() dummyeffectblink5_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21498i*/"armor_red_5");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink6_red_armor;
};

void() dummyeffectblink4_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21510i*/"armor_red_4");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink5_red_armor;
};

void() dummyeffectblink3_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21522i*/"armor_red_3");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink4_red_armor;
};

void() dummyeffectblink2_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21534i*/"armor_red_2");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink3_red_armor;
};

void() dummyeffectblink1_red_armor =
{
	self.traileffectnum = particleeffectnum(/*21546i*/"armor_red_1");
	self.nextthink = (time + 0.12);
	self.think = dummyeffectblink2_red_armor;
};

void() packTouch =
{
	local entity stemp;

	if ((other.health <= 0))
	{
		return;
	}
	if ((other.classname != "player"))
	{
		return;
	}
	if ((random() > 0.7))
	{
		other.grenade_ammo = (other.grenade_ammo + 4);
		other.ammo_shells = (other.ammo_shells + 12);
		other.ammo_nails = (other.ammo_nails + 30);
		other.ammo_rockets = (other.ammo_rockets + 8);
		other.ammo_cells = (other.ammo_cells + 20);
		sprint(other, "You got a supply pack with 4 proximity grenades and more ammo\n");
		sound(other, CHAN_ITEM, "misc/backpack_ammo.wav", 1, ATTN_NORM);
	}
	else
	{
		other.grenade_ammo = (other.grenade_ammo + 3);
		other.ammo_shells = (other.ammo_shells + 10);
		other.ammo_nails = (other.ammo_nails + 20);
		other.ammo_rockets = (other.ammo_rockets + 6);
		other.ammo_cells = (other.ammo_cells + 15);
		if ((other.armortype < 0.6))
		{
			other.armortype = 0.6;
			other.items = ((other.items - (other.items & 57344)) + IT_ARMOR2);
		}
		other.armorvalue = (other.armorvalue + 30);
		if ((other.armorvalue > 200))
		{
			other.armorvalue = 200;
		}
		sprint(other, "You got a supply pack with 3 proximity grenades, ammo, and 30 yellow armor shards\n");
		sound(other, CHAN_ITEM, "misc/backpack_armour.wav", 1, ATTN_NORM);
	}
	bound_other_ammo();
	if ((autocvar_effects_explosion_shake != 0))
	{
		stuffcmd(other, "bf\n");
	}
	stemp = self;
	self = other;
	self.bm_full_refill = TRUE;
	W_SetCurrentAmmo();
	self = stemp;
	self.model = string_null;
	self.solid = 0;
	if (deathmatch)
	{
		self.nextthink = (time + 30);
		self.think = SUB_regen;
	}
	else
	{
		self.think = SUB_Null;
		self.nextthink = -1;
	}
	activator = other;
	SUB_UseTargets();
};

void() item_backpack =
{
	self.touch = packTouch;
	precache_model("progs/backpack.mdl");
	setmodel(self, "progs/backpack.mdl");
	setsize(self, '-16 -16 0', '16 16 56');
	StartItem();
};

void() item_armorInv =
{
	if (((autocvar_redarmor_backpack == 1) && (random() < 0.2)))
	{
		item_backpack();
		return;
	}
	self.touch = armor_touch;
	if (autocvar_armor_model)
	{
		if ((world.worldtype == 2))
		{
			precache_model("progs/armor.mdl");
			setmodel(self, "progs/armor.mdl");
		}
		else
		{
			precache_model("progs/armor1.mdl");
			setmodel(self, "progs/armor1.mdl");
		}
	}
	else
	{
		precache_model("progs/armor.mdl");
		setmodel(self, "progs/armor.mdl");
	}
	if ((autocvar_armorspecialeffect == 2))
	{
		self.traileffectnum = particleeffectnum(/*21771i*/"red_armor");
	}
	self.skin = 2;
	setsize(self, '-16 -16 0', '16 16 56');
	StartItem();
};

void() bound_other_ammo =
{
	if ((other.ammo_shells > autocvar_shells_max_capacity))
	{
		other.ammo_shells = autocvar_shells_max_capacity;
	}
	if ((other.ammo_nails > autocvar_nails_max_capacity))
	{
		other.ammo_nails = autocvar_nails_max_capacity;
	}
	if ((other.ammo_rockets > autocvar_rockets_max_capacity))
	{
		other.ammo_rockets = autocvar_rockets_max_capacity;
	}
	if ((other.ammo_cells > autocvar_cells_max_capacity))
	{
		other.ammo_cells = autocvar_cells_max_capacity;
	}
	if ((other.grenade_ammo > 6))
	{
		other.grenade_ammo = 6;
	}
};

float(float w) RankForWeapon =
{
	if ((w == IT_LIGHTNING))
	{
		return (1);
	}
	if ((w == IT_ROCKET_LAUNCHER))
	{
		return (2);
	}
	if ((w == IT_LASER_CANNON))
	{
		return (3);
	}
	if ((w == IT_SUPER_NAILGUN))
	{
		return (3);
	}
	if ((w == IT_GRENADE_LAUNCHER))
	{
		return (4);
	}
	if ((w == IT_SUPER_SHOTGUN))
	{
		return (5);
	}
	if ((w == IT_NAILGUN))
	{
		return (6);
	}
	if ((w == IT_CHAINSAW))
	{
		return (6);
	}
	return (7);
};

void(float old, float new) Deathmatch_Weapon =
{
	local float or;
	local float nr;

	if (autocvar_bm_reload)
	{
		return;	// BM_NoPickupSwitch: everyone already has every gun
	}
	or = RankForWeapon(self.weapon);
	nr = RankForWeapon(new);
	if ((nr < or))
	{
		self.weapon = new;
	}
};

void() weapon_touch =
{
	local float hadammo;
	local float best;
	local float new;
	local float old;
	local entity stemp;
	local float leave;

	if (!(other.flags & FL_CLIENT))
	{
		return;
	}
	stemp = self;
	self = other;
	best = W_BestWeapon();
	self = stemp;
	if (((deathmatch == 2) || coop))
	{
		leave = 1;
	}
	else
	{
		leave = 0;
	}
		if ((self.classname == "weapon_supernailgun"))
		{
			if ((leave && (other.items & IT_SUPER_NAILGUN)))
			{
				return;
			}
			hadammo = other.ammo_rockets;
			new = IT_SUPER_NAILGUN;
			other.ammo_nails = (other.ammo_nails + 50);
		}
		else
		{
			if ((self.classname == "weapon_supershotgun"))
			{
				if ((leave && (other.items & IT_SUPER_SHOTGUN)))
				{
					return;
				}
				hadammo = other.ammo_rockets;
				new = IT_SUPER_SHOTGUN;
				other.ammo_shells = (other.ammo_shells + 10);
			}
			else
			{
				if ((self.classname == "weapon_rocketlauncher"))
				{
					if ((leave && (other.items & IT_ROCKET_LAUNCHER)))
					{
						return;
					}
					hadammo = other.ammo_rockets;
					new = IT_ROCKET_LAUNCHER;
					other.ammo_rockets = (other.ammo_rockets + 6);
				}
				else
				{
					if ((self.classname == "weapon_grenadelauncher"))
					{
						if ((leave && (other.items & IT_GRENADE_LAUNCHER)))
						{
							return;
						}
						hadammo = other.ammo_rockets;
						new = IT_GRENADE_LAUNCHER;
						other.ammo_rockets = (other.ammo_rockets + 6);
					}
					else
					{
						if ((self.classname == "weapon_lightning"))
						{
							if ((leave && (other.items & IT_LIGHTNING)))
							{
								return;
							}
							hadammo = other.ammo_rockets;
							new = IT_LIGHTNING;
							other.ammo_cells = (other.ammo_cells + 30);
						}
						else
						{
							if ((self.classname == "weapon_chainsaw"))
							{
								// Chainsaw was removed in favor of the Bonk Hammer (IT_AXE); don't equip an invisible dead slot
								return;
							}
							else
							{
								if ((self.classname == "weapon_laser_gun"))
								{
									if ((leave && (other.items & IT_LASER_CANNON)))
									{
										return;
									}
									hadammo = other.ammo_rockets;
									new = IT_LASER_CANNON;
									other.ammo_cells = (other.ammo_cells + 30);
								}
								else if ((self.classname == "weapon_proximity_gun"))
								{
									if ((other.grenade_ammo >= 6))
									{
										return;
									}
									other.grenade_ammo = (other.grenade_ammo + 2);
									new = other.items;
								}
								else
								{
									objerror("weapon_touch: unknown classname");
								}
							}
						}
					}
				}
			}
		}
	sprint(other, "You got the ");
	sprint(other, self.netname);
	sprint(other, "\n");
	if ((self.model == "progs/g_mage1.mdl"))
	{
		sound(other, CHAN_ITEM, "weapons/g_mage1.wav", 1, ATTN_NORM);
	}
	else
	{
		sound(other, CHAN_ITEM, "weapons/pkup.wav", 1, ATTN_NORM);
	}
	stuffcmd(other, "bf\n");
	bound_other_ammo();
	old = other.items;
	other.items = (other.items | new);
	stemp = self;
	self = other;
	if ((self.meleeing == 0))
	{
		if ((autocvar_weaponautoswitch == 0))
		{
			if (deathmatch)
			{
				Deathmatch_Weapon(old, new);
			}
		}
		else
		{
			if ((autocvar_weaponautoswitch == 2))
			{
				if (coop)
				{
					self.weapon = new;
				}
				else
				{
					Deathmatch_Weapon(old, new);
				}
			}
			else
			{
				if ((autocvar_weaponautoswitch == 3))
				{
					if (!(old & new))
					{
						if (!deathmatch)
						{
							self.weapon = new;
						}
						else
						{
							Deathmatch_Weapon(old, new);
						}
					}
				}
				else
				{
					if (!deathmatch)
					{
						self.weapon = new;
					}
					else
					{
						Deathmatch_Weapon(old, new);
					}
				}
			}
		}
	}
	if ((autocvar_weaponautoswitch != 0))
	{
		W_SetCurrentAmmo();
	}
	self = stemp;
	if (leave)
	{
		return;
	}
	if ((self.model == "progs/g_mage1.mdl"))
	{
		self.vanish = 1;
	}
	self.model = string_null;
	self.solid = 0;
	if ((deathmatch == 1))
	{
		self.nextthink = (time + 30);
	}
	if ((self.vanish != 1))
	{
		self.think = SUB_regen;
	}
	else
	{
		if ((deathmatch || coop))
		{
			self.think = SUB_regen;
		}
	}
	activator = other;
	SUB_UseTargets();
};

void() weapon_nailgun =
{
	remove(self);		// guns removed from maps: players start with small weapons
};

void() weapon_supernailgun =
{
	remove(self);
};

void() weapon_grenadelauncher =
{
	remove(self);
};

void() weapon_rocketlauncher =
{
	remove(self);
};

void() g_mage1_effect =
{
	self.frame = (self.frame + 1);
	if ((self.frame > 7))
	{
		self.frame = 0;
	}
	self.nextthink = (time + 0.15);
	self.think = g_mage1_effect;
};

void() weapon_lightning =
{
	remove(self);
};

void() weapon_chainsaw =
{
	remove(self);
};

void() weapon_laser_gun =
{
	remove(self);
};

void() prox_touch =
{
	if ((other.classname != "player"))
	{
		return;
	}
	else
	{
		if ((other.grenade_ammo >= 6))
		{
			return;
		}
	}
	other.grenade_ammo = (other.grenade_ammo + self.health);
	bound_other_ammo();
	sprint(other, "You got the proximity grenades\n");
	if ((autocvar_effects_explosion_shake != 0))
	{
		stuffcmd(other, "bf\n");
	}
	sound(other, CHAN_ITEM, "weapons/grenarm.wav", 1, ATTN_NORM);
	remove(self);
};

void() weapon_proximity_gun =
{
	remove(self);
};

void() ammo_touch_delay =
{
	self.touch = ammo_touch;
};

void() ammo_touch =
{
	local entity stemp;
	local float best;
	local string s;

	if ((other.classname != "player"))
	{
		return;
	}
	if ((other.health <= 0))
	{
		return;
	}
	stemp = self;
	self = other;
	best = W_BestWeapon();
	self = stemp;
	self.aflag_old = self.aflag;
	if ((self.weapon == 1))
	{
		if ((other.ammo_shells >= autocvar_shells_max_capacity))
		{
			return;
		}
		other.ammo_shells = (other.ammo_shells + self.aflag);
		if (autocvar_lossless_ammo_pickup)
		{
			if ((other.ammo_shells > autocvar_shells_max_capacity))
			{
				self.aflag = (other.ammo_shells - autocvar_shells_max_capacity);
			}
			else
			{
				self.crate_is_empty = 1;
			}
		}
	}
	if ((self.weapon == 2))
	{
		if ((other.ammo_nails >= autocvar_nails_max_capacity))
		{
			return;
		}
		other.ammo_nails = (other.ammo_nails + self.aflag);
		if (autocvar_lossless_ammo_pickup)
		{
			if ((other.ammo_nails > autocvar_nails_max_capacity))
			{
				self.aflag = (other.ammo_nails - autocvar_nails_max_capacity);
			}
			else
			{
				self.crate_is_empty = 1;
			}
		}
	}
	if ((self.weapon == 3))
	{
		if ((other.ammo_rockets >= autocvar_rockets_max_capacity))
		{
			return;
		}
		other.ammo_rockets = (other.ammo_rockets + self.aflag);
		if (autocvar_lossless_ammo_pickup)
		{
			if ((other.ammo_rockets > autocvar_rockets_max_capacity))
			{
				self.aflag = (other.ammo_rockets - autocvar_rockets_max_capacity);
			}
			else
			{
				self.crate_is_empty = 1;
			}
		}
	}
	if ((self.weapon == 4))
	{
		if ((other.ammo_cells >= autocvar_cells_max_capacity))
		{
			return;
		}
		other.ammo_cells = (other.ammo_cells + self.aflag);
		if (autocvar_lossless_ammo_pickup)
		{
			if ((other.ammo_cells > autocvar_cells_max_capacity))
			{
				self.aflag = (other.ammo_cells - autocvar_cells_max_capacity);
			}
			else
			{
				self.crate_is_empty = 1;
			}
		}
	}
	bound_other_ammo();
	if (autocvar_lossless_ammo_pickup)
	{
		sprint(other, "You got ");
		if (!self.crate_is_empty)
		{
			s = ftos((self.aflag_old - self.aflag));
		}
		else
		{
			s = ftos(self.aflag_old);
		}
		sprint(other, s);
		sprint(other, " ");
		sprint(other, self.netname);
		if (!self.crate_is_empty)
		{
			sprint(other, ". Max capacity reached. ");
			s = ftos(self.aflag);
			sprint(other, s);
			sprint(other, " ");
			sprint(other, self.netname);
			sprint(other, " remaining.");
		}
	}
	else
	{
		sprint(other, "You got the ");
		sprint(other, self.netname);
	}
	sprint(other, "\n");
	sound(other, CHAN_ITEM, "weapons/lock4.wav", 1, ATTN_NORM);
	if ((autocvar_effects_explosion_shake != 0))
	{
		stuffcmd(other, "bf\n");
	}
	stemp = self;
	self = other;
	self = stemp;
	if ((other.weapon == IT_SHOTGUN))
	{
		other.currentammo = other.ammo_shells;
		other.items = (other.items | IT_SHELLS);
	}
	else
	{
		if ((other.weapon == IT_SUPER_SHOTGUN))
		{
			other.currentammo = other.ammo_shells;
			other.items = (other.items | IT_SHELLS);
		}
		else
		{
			if ((other.weapon == IT_NAILGUN))
			{
				other.currentammo = other.ammo_nails;
				other.items = (other.items | IT_NAILS);
			}
			else
			{
				if ((other.weapon == IT_SUPER_NAILGUN))
				{
					other.currentammo = other.ammo_nails;
					other.items = (other.items | IT_NAILS);
				}
				else
				{
					if ((other.weapon == IT_GRENADE_LAUNCHER))
					{
						other.currentammo = other.ammo_rockets;
						other.items = (other.items | IT_ROCKETS);
					}
					else
					{
						if ((other.weapon == IT_ROCKET_LAUNCHER))
						{
							other.currentammo = other.ammo_rockets;
							other.items = (other.items | IT_ROCKETS);
						}
						else
						{
							if ((other.weapon == IT_LIGHTNING))
							{
								other.currentammo = other.ammo_cells;
								other.items = (other.items | IT_CELLS);
							}
							else
							{
								if ((other.weapon == IT_LASER_CANNON))
								{
									other.currentammo = other.ammo_cells;
									other.items = (other.items | IT_CELLS);
								}
							}
						}
					}
				}
			}
		}
	}
	if (autocvar_lossless_ammo_pickup)
	{
		if ((self.crate_is_empty == 1))
		{
			self.crate_is_empty = 0;
			self.aflag = self.initial_amount;
			self.model = string_null;
			self.solid = 0;
			if ((deathmatch == 1))
			{
				self.nextthink = (time + 30);
			}
			self.think = SUB_regen;
			activator = other;
			SUB_UseTargets();
		}
		else
		{
			self.touch = SUB_Null;
			self.nextthink = (time + 1);
			self.think = ammo_touch_delay;
		}
	}
	else
	{
		self.model = string_null;
		self.solid = 0;
		if ((deathmatch == 1))
		{
			self.nextthink = (time + 30);
		}
		self.think = SUB_regen;
		activator = other;
		SUB_UseTargets();
	}
};

void() item_shells =
{
	if (((random() < 0.07) && !(self.spawnflags & WEAPON_BIG2)))
	{
		prox_spawn(2);
		remove(self);
		return;
	}
	self.touch = ammo_touch;
	if ((self.spawnflags & WEAPON_BIG2))
	{
		precache_model("maps/b_shell1.bsp");
		setmodel(self, "maps/b_shell1.bsp");
		self.aflag = autocvar_shells_big;
		self.traileffectnum = particleeffectnum(/*22414i*/"shells_ammo_big");
		self.netname = "big shell box";
	}
	else
	{
		precache_model("maps/b_shell0.bsp");
		setmodel(self, "maps/b_shell0.bsp");
		self.aflag = autocvar_shells_small;
		self.traileffectnum = particleeffectnum(/*22444i*/"shells_ammo_small");
		self.netname = "small shell box";
	}
	self.initial_amount = self.aflag;
	self.weapon = 1;
	setsize(self, VEC_ORIGIN, '24 24 32');
	StartItem();
};

void() item_spikes =
{
	if (((random() < 0.05) && !(self.spawnflags & WEAPON_BIG2)))
	{
		prox_spawn(2);
		remove(self);
		return;
	}
	self.touch = ammo_touch;
	if ((self.spawnflags & WEAPON_BIG2))
	{
		precache_model("maps/b_nail1.bsp");
		setmodel(self, "maps/b_nail1.bsp");
		self.aflag = autocvar_nails_big;
		self.traileffectnum = particleeffectnum(/*22478i*/"nails_ammo_big");
		self.netname = "big nail box";
	}
	else
	{
		precache_model("maps/b_nail0.bsp");
		setmodel(self, "maps/b_nail0.bsp");
		self.aflag = autocvar_nails_small;
		self.traileffectnum = particleeffectnum(/*22506i*/"nails_ammo_small");
		self.netname = "small nail box";
	}
	self.initial_amount = self.aflag;
	self.weapon = 2;
	setsize(self, VEC_ORIGIN, '24 24 32');
	StartItem();
};

void() item_rockets =
{
	self.touch = ammo_touch;
	if ((self.spawnflags & WEAPON_BIG2))
	{
		precache_model("maps/b_rock1.bsp");
		setmodel(self, "maps/b_rock1.bsp");
		self.aflag = autocvar_rockets_big;
		self.traileffectnum = particleeffectnum(/*22538i*/"rockets_ammo_big");
		self.netname = "big rocket box";
	}
	else
	{
		precache_model("maps/b_rock0.bsp");
		setmodel(self, "maps/b_rock0.bsp");
		self.aflag = autocvar_rockets_small;
		self.traileffectnum = particleeffectnum(/*22570i*/"rockets_ammo_small");
		self.netname = "small rocket box";
	}
	self.initial_amount = self.aflag;
	self.weapon = 3;
	setsize(self, VEC_ORIGIN, '24 24 32');
	StartItem();
};

void() item_cells =
{
	self.touch = ammo_touch;
	if ((self.spawnflags & WEAPON_BIG2))
	{
		precache_model("maps/b_batt1.bsp");
		setmodel(self, "maps/b_batt1.bsp");
		self.aflag = autocvar_cells_big;
		self.traileffectnum = particleeffectnum(/*22606i*/"cells_ammo_big");
		self.netname = "big cell box";
	}
	else
	{
		precache_model("maps/b_batt0.bsp");
		setmodel(self, "maps/b_batt0.bsp");
		self.aflag = autocvar_cells_small;
		self.traileffectnum = particleeffectnum(/*22634i*/"cells_ammo_small");
		self.netname = "small cell box";
	}
	self.initial_amount = self.aflag;
	self.weapon = 4;
	setsize(self, VEC_ORIGIN, '24 24 32');
	StartItem();
};

void() item_weapon =
{
	self.touch = ammo_touch;
	if ((self.spawnflags & WEAPON_SHOTGUN))
	{
		if ((self.spawnflags & WEAPON_BIG))
		{
			precache_model("maps/b_shell1.bsp");
			setmodel(self, "maps/b_shell1.bsp");
			self.aflag = 40;
		}
		else
		{
			precache_model("maps/b_shell0.bsp");
			setmodel(self, "maps/b_shell0.bsp");
			self.aflag = 20;
		}
		self.weapon = 1;
		self.netname = "shells";
	}
	if ((self.spawnflags & WEAPON_SPIKES))
	{
		if ((self.spawnflags & WEAPON_BIG))
		{
			precache_model("maps/b_nail1.bsp");
			setmodel(self, "maps/b_nail1.bsp");
			self.aflag = 40;
		}
		else
		{
			precache_model("maps/b_nail0.bsp");
			setmodel(self, "maps/b_nail0.bsp");
			self.aflag = 20;
		}
		self.weapon = 2;
		self.netname = "spikes";
	}
	if ((self.spawnflags & WEAPON_ROCKET))
	{
		if ((self.spawnflags & WEAPON_BIG))
		{
			precache_model("maps/b_rock1.bsp");
			setmodel(self, "maps/b_rock1.bsp");
			self.aflag = 10;
		}
		else
		{
			precache_model("maps/b_rock0.bsp");
			setmodel(self, "maps/b_rock0.bsp");
			self.aflag = 5;
		}
		self.weapon = 3;
		self.netname = "rockets";
	}
	setsize(self, VEC_ORIGIN, '24 24 32');
	StartItem();
};

void() key_touch =
{
	if ((other.classname != "player"))
	{
		return;
	}
	if ((other.health <= 0))
	{
		return;
	}
	if ((other.items & self.items))
	{
		return;
	}
	if (((!coop && !deathmatch) && autocvar_auto_save))
	{
		stuffcmd(other, "Echo Checkpoint...\n");
		stuffcmd(other, "save autosaves/autosave\n");
	}
	sprint(other, "You got the ");
	sprint(other, self.netname);
	sprint(other, "\n");
	sound(other, CHAN_ITEM, self.noise, 1, ATTN_NORM);
	stuffcmd(other, "bf\n");
	other.items = (other.items | self.items);
	if (!coop)
	{
		self.solid = 0;
		self.model = string_null;
	}
	activator = other;
	SUB_UseTargets();
};

void() key_setsounds =
{
	if ((world.worldtype == 0))
	{
		precache_sound("misc/medkey.wav");
		self.noise = "misc/medkey.wav";
	}
	if ((world.worldtype == 1))
	{
		precache_sound("misc/runekey.wav");
		self.noise = "misc/runekey.wav";
	}
	if ((world.worldtype == 2))
	{
		precache_sound2("misc/basekey.wav");
		self.noise = "misc/basekey.wav";
	}
};

void() item_key1 =
{
	if ((world.worldtype == 0))
	{
		precache_model("progs/w_s_key.mdl");
		setmodel(self, "progs/w_s_key.mdl");
		self.netname = "silver key";
		self.traileffectnum = particleeffectnum(/*22812i*/"silver_key");
	}
	else
	{
		if ((world.worldtype == 1))
		{
			precache_model("progs/m_s_key.mdl");
			setmodel(self, "progs/m_s_key.mdl");
			self.netname = "silver runekey";
			self.traileffectnum = particleeffectnum(/*22856i*/"silver_rune_key");
		}
		else
		{
			if ((world.worldtype == 2))
			{
				precache_model2("progs/b_s_key.mdl");
				setmodel(self, "progs/b_s_key.mdl");
				self.netname = "silver keycard";
				self.traileffectnum = particleeffectnum(/*22905i*/"silver_key_card");
			}
		}
	}
	key_setsounds();
	self.touch = key_touch;
	self.items = IT_KEY1;
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	StartItem();
};

void() item_key2 =
{
	if ((world.worldtype == 0))
	{
		precache_model("progs/w_g_key.mdl");
		setmodel(self, "progs/w_g_key.mdl");
		self.netname = "gold key";
		self.traileffectnum = particleeffectnum(/*22948i*/"gold_key");
	}
	if ((world.worldtype == 1))
	{
		precache_model("progs/m_g_key.mdl");
		setmodel(self, "progs/m_g_key.mdl");
		self.netname = "gold runekey";
		self.traileffectnum = particleeffectnum(/*22988i*/"gold_rune_key");
	}
	if ((world.worldtype == 2))
	{
		precache_model2("progs/b_g_key.mdl");
		setmodel(self, "progs/b_g_key.mdl");
		self.netname = "gold keycard";
		self.traileffectnum = particleeffectnum(/*23033i*/"gold_key_card");
	}
	key_setsounds();
	self.touch = key_touch;
	self.items = IT_KEY2;
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	StartItem();
};

void() sigil_touch =
{
	if ((other.classname != "player"))
	{
		return;
	}
	if ((other.health <= 0))
	{
		return;
	}
	centerprint(other, "You got the rune!");
	sound(other, CHAN_ITEM, self.noise, 1, ATTN_NORM);
	stuffcmd(other, "bf\n");
	self.solid = 0;
	self.model = string_null;
	serverflags = serverflags | (self.spawnflags & 15);
	self.classname = "";
	activator = other;
	SUB_UseTargets();
};

void() item_sigil =
{
	if (!self.spawnflags)
	{
		objerror("no spawnflags");
	}
	precache_sound("misc/runekey.wav");
	self.noise = "misc/runekey.wav";
	if ((self.spawnflags & 1))
	{
		precache_model("progs/end1.mdl");
		setmodel(self, "progs/end1.mdl");
	}
	if ((self.spawnflags & 2))
	{
		precache_model2("progs/end2.mdl");
		setmodel(self, "progs/end2.mdl");
	}
	if ((self.spawnflags & 4))
	{
		precache_model2("progs/end3.mdl");
		setmodel(self, "progs/end3.mdl");
	}
	if ((self.spawnflags & 8))
	{
		precache_model2("progs/end4.mdl");
		setmodel(self, "progs/end4.mdl");
	}
	self.traileffectnum = particleeffectnum(/*23139i*/"rune");
	self.touch = sigil_touch;
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	StartItem();
};

void() powerup_touch =
{
	local entity selftemp;

	if ((other.classname != "player"))
	{
		return;
	}
	if ((other.health <= 0))
	{
		return;
	}
	sprint(other, "You got the ");
	sprint(other, self.netname);
	sprint(other, "\n");
	if (deathmatch)
	{
		self.mdl = self.model;
		if (((self.classname == "item_artifact_invulnerability") || (self.classname == "item_artifact_invisibility")))
		{
			self.nextthink = (time + 300);
		}
		else
		{
			self.nextthink = (time + 90);
		}
		self.think = SUB_regen;
	}
	if (self.bm_dropped)
	{
		self.think = SUB_Remove;	// it piled up for good on long-running servers (respawned every 90 s)
		self.nextthink = time + 0.1;
	}
	sound(other, CHAN_VOICE, self.noise, 1, ATTN_NORM);
	stuffcmd(other, "bf\n");
	self.solid = 0;
	other.items = (other.items | self.items);
	self.model = string_null;
	if ((self.classname == "item_artifact_envirosuit"))
	{
		other.rad_time = 1;
		other.radsuit_finished = (time + 30);
		other.radsuit_counter = 30;
		SpawnRebreather();
	}
	if ((self.classname == "item_artifact_invulnerability"))
	{
		other.invincible_time = 1;
		other.invincible_finished = (time + 30);
		other.invincible_counter = 30;
	}
	if ((self.classname == "item_artifact_invulnerability2"))
	{
		other.invincible_time = 1;
		other.invincible_finished = (time + 25);
		other.invincible_counter = 25;
		autocvar_berserkmode = 3.5;
		other.attack_finished = (time + 0.3);
		other.button0 = 0;
		other.has_fired = 1;
		selftemp = self;
		self = other;
		self.weapon = IT_AXE;
		W_SetCurrentAmmo();
		self = selftemp;
		centerprint(other, "You got the Berserk Pentagram!");
		te_customflash(self.origin, 400, 500, '2 0 0');
		self.effects = 0;
	}
	if ((self.classname == "item_sfshotgun"))
	{
		other.attack_finished = (time + 0.2);
		other.button0 = 0;
		sound(other, CHAN_ITEM, "weapons/pkup.wav", 1, ATTN_NORM);
		other.ammo_shells = (other.ammo_shells + 12);
		selftemp = self;
		self = other;
		self.weapon = IT_SUPER_SHOTGUN;
		W_SetCurrentAmmo();
		self = selftemp;
		centerprint(other, "You got a Shotgun Shell Pack!");
		self.effects = 0;
	}
	if ((self.classname == "item_artifact_invisibility"))
	{
		other.invisible_time = 1;
		other.invisible_finished = (time + 30);
		other.invisible_counter = 30;
	}
	if ((self.classname == "item_artifact_super_damage"))
	{
		other.super_time = 1;
		other.super_damage_finished = (time + 30);
		other.super_damage_counter = 30;
	}
	activator = other;
	SUB_UseTargets();
};

void() item_artifact_invulnerability =
{
	if (((autocvar_slowmo_powerup == 4) && deathmatch))
	{
		self.dmg = 2;
		item_artifact_timerune();
		return;
	}
	self.touch = powerup_touch;
	precache_model("progs/invulner.mdl");
	self.noise = "items/protect.wav";
	setmodel(self, "progs/invulner.mdl");
	if ((world.model == "maps/e1m8.bsp"))
	{
		self.traileffectnum = particleeffectnum(/*23332i*/"pentagram_low_gravity");
	}
	else
	{
		self.traileffectnum = particleeffectnum(/*23354i*/"pentagram_normal_gravity");
	}
	self.netname = "Pentagram of Protection";
	self.items = IT_INVULNERABILITY;
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	StartItem();
};

void() item_sfshotgun =
{
	self.touch = powerup_touch;
	self.noise = "weapons/pkup.wav";
	setmodel(self, "progs/backpack.mdl");
	self.avelocity_y = 500;
	self.traileffectnum = particleeffectnum(/*21958i*/"g_weaponeffect");
	self.classname = "item_sfshotgun";
	self.netname = "Shotgun Shell Pack";
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	StartItem();
};

void() weapon_supershotgun =
{
	remove(self);		// guns removed from maps: players start with small weapons
};

void() item_artifact_invulnerability2 =
{
	self.touch = powerup_touch;
	self.noise = "items/protect.wav";
	setmodel(self, "progs/invulner.mdl");
	self.avelocity_y = 500;
	self.colormod = '0.2 0.05 0.05';
	self.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
	self.classname = "item_artifact_invulnerability2";
	self.netname = "Berserk Pentagram";
	self.items = IT_INVULNERABILITY;
	if ((self.has_fired == 1))
	{
		setsize(self, '-8 -8 -24', '8 8 32');
	}
	else
	{
		setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	}
	StartItem();
};

void() item_artifact_envirosuit =
{
	if (((autocvar_slowmo_powerup == 3) && deathmatch))
	{
		self.dmg = 2;
		item_artifact_timerune();
		return;
	}
	else
	{
		if ((self.dmg == 1))
		{
			self.classname = "item_artifact_envirosuit";
			self.touch = powerup_touch;
			precache_model("progs/wetsuit.mdl");
			precache_sound("misc/wetsuit.wav");
			precache_sound("misc/weton.wav");
			precache_sound("items/suit2.wav");
			self.noise = "misc/weton.wav";
			setmodel(self, "progs/wetsuit.mdl");
			self.netname = "Wetsuit";
			self.items = IT_SUIT;
			setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
			StartItem();
		}
		else
		{
			self.touch = powerup_touch;
			precache_model("progs/suit.mdl");
			precache_sound("items/suit.wav");
			precache_sound("items/suit2.wav");
			precache_sound("misc/wetsuit.wav");
			self.noise = "items/suit.wav";
			setmodel(self, "progs/suit.mdl");
			self.traileffectnum = particleeffectnum(/*23617i*/"biosuit");
			self.netname = "Biosuit";
			self.items = IT_SUIT;
			setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
			StartItem();
		}
	}
};

void() slowmo_counter =
{
	if ((((!self.owner || bm_wasfreed(self.owner)) || (self.owner.classname != "player")) || ((self.owner.health <= 0) || (self.owner.slowmo_timer <= 0))))
	{
		cvar_set("slowmo", "1");
		IN_SLOWMO = 0;
		if ((self.owner && !bm_wasfreed(self.owner)))
		{
			self.owner.slowmo_timer = 0;
			self.owner.bulletspeed = 900;
			if ((self.owner.classname == "player"))
			{
				stuffcmd(self.owner, "bf\n");
			}
		}
		if (deathmatch)
		{
			self.think = SUB_regen;
			self.nextthink = (time + 80);
		}
		else
		{
			self.think = SUB_Null;
			self.nextthink = -1;
		}
	}
	else
	{
		self.think = slowmo_counter;
		self.nextthink = (time + 1);
		self.owner.slowmo_timer = (self.owner.slowmo_timer - 1);
		if ((self.owner.slowmo_timer == 1))
		{
			stuffcmd(self.owner, "bf\n");
			sprint(self.owner, "the Time Dilation Rune is wearing off...\n");
			sound(world, CHAN_AUTO, "items/slowmo_expire.wav", 1, ATTN_NONE);
		}
	}
};

void() slowmo_touch =
{
	local entity e;

	if ((other.classname != "player"))
	{
		return;
	}
	if ((other.health <= 0))
	{
		return;
	}
	// cancel any other rune currently ticking down on this player so they don't double-decrement slowmo_timer
	e = nextent(world);
	while (e)
	{
		if (((e != self) && (e.think == slowmo_counter) && (e.owner == other)))
		{
			if (deathmatch)
			{
				e.think = SUB_regen;
				e.nextthink = (time + 80);
			}
			else
			{
				e.think = SUB_Null;
				e.nextthink = -1;
			}
		}
		e = nextent(e);
	}
	sprint(other, "You got the ");
	sprint(other, self.netname);
	sprint(other, "\n");
	sound(other, CHAN_VOICE, self.noise, 1, ATTN_NORM);
	stuffcmd(other, "bf\n");
	self.solid = 0;
	self.model = string_null;
	IN_SLOWMO = 1;
	self.effects = 0;
	cvar_set("slowmo", ".55");
	self.owner = other;
	self.owner.bulletspeed = 1200;
	other.slowmo_timer = 13;
	self.think = slowmo_counter;
	self.nextthink = (time + 1);
	activator = other;
	SUB_UseTargets();
};

void() item_artifact_timerune =
{
	precache_model("progs/timerune.mdl");
	self.noise = "items/slowmo_pickup.wav";
	setmodel(self, "progs/timerune.mdl");
	self.touch = slowmo_touch;
	self.traileffectnum = particleeffectnum(/*23753i*/"time_rune");
	self.effects = 40;
	self.netname = "Time Dilation Rune";
	if ((self.has_fired == 1))
	{
		setsize(self, '-6 -6 -24', '6 6 32');
	}
	else
	{
		setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	}
	StartItem();
};

void() item_artifact_invisibility =
{
	{
		if ((((autocvar_slowmo_powerup == 1) && deathmatch) || (((autocvar_slowmo_powerup == 1) && !deathmatch) && (random() > 0.8))))
		{
			self.dmg = 2;
			item_artifact_timerune();
		}
		else
		{
			self.touch = powerup_touch;
			precache_model("progs/invisibl.mdl");
			self.noise = "items/inv1.wav";
			setmodel(self, "progs/invisibl.mdl");
			self.traileffectnum = particleeffectnum(/*23816i*/"ring");
			self.netname = "Ring of Shadows";
			self.items = IT_INVISIBILITY;
			if ((self.has_fired == 1))
			{
				setsize(self, '-8 -8 -24', '8 8 32');
			}
			else
			{
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
			}
			StartItem();
		}
	}
};

void() item_artifact_super_damage =
{
	local entity item;

	if (((autocvar_quadreplacer > 0) && (random() <= 0.35)))
	{
		item = spawn();
		item.origin = self.origin;
		item.flags = FL_ITEM;
		item.solid = SOLID_TRIGGER;
		item.movetype = MOVETYPE_TOSS;
		item.think = item_artifact_invulnerability2;
		item.nextthink = (time + 0.0001);
		remove(self);
		return;
	}
	if ((((autocvar_slowmo_powerup == 2) && deathmatch) || (((autocvar_slowmo_powerup == 2) && !deathmatch) && (random() > 0.5))))
	{
		self.dmg = 2;
		item_artifact_timerune();
		return;
	}
	self.touch = powerup_touch;
	self.noise = "items/damage.wav";
	precache_model("progs/quaddama.mdl");
	precache_sound("items/damage.wav");
	precache_sound("items/damage2.wav");
	precache_sound("items/damage3.wav");
	setmodel(self, "progs/quaddama.mdl");
	self.traileffectnum = particleeffectnum(/*23873i*/"quad");
	self.netname = "Quad Damage";
	self.items = IT_QUAD;
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	StartItem();
};

void() backpack_touch_delay =
{
	self.touch = BackpackTouch;
	self.nextthink = (time + 180);
	self.think = SUB_Remove;
};

void() BackpackTouch =
{
	local string s;
	local float best;
	local float old;
	local float new;
	local float oldwep;
	local entity stemp;
	local float acount;

	if ((other.classname != "player"))
	{
		return;
	}
	if ((other.health <= 0))
	{
		return;
	}
	if (cvar("coop_life_pool"))
	{
		if (((self.owner.classname == "player") && (other != self.owner)))
		{
			return;
		}
	}
	if (autocvar_lossless_backpack_pickup)
	{
		if (!(deathmatch || coop))
		{
			if ((self.ammo_shells && (other.ammo_shells >= autocvar_shells_max_capacity)))
			{
				return;
			}
			if ((self.ammo_nails && (other.ammo_nails >= autocvar_nails_max_capacity)))
			{
				return;
			}
			if ((self.ammo_rockets && (other.ammo_rockets >= autocvar_rockets_max_capacity)))
			{
				return;
			}
			if ((self.ammo_cells && (other.ammo_cells >= autocvar_cells_max_capacity)))
			{
				return;
			}
		}
	}
	acount = 0;
	sprint(other, "You got ");
	if (self.items)
	{
		if (((other.items & self.items) == 0))
		{
			acount = 1;
			sprint(other, "the ");
			sprint(other, self.netname);
		}
	}
	stemp = self;
	self = other;
	best = W_BestWeapon();
	self = stemp;
	self.ammo_shells_old = self.ammo_shells;
	self.ammo_nails_old = self.ammo_nails;
	self.ammo_rockets_old = self.ammo_rockets;
	self.ammo_cells_old = self.ammo_cells;
	other.ammo_shells = (other.ammo_shells + self.ammo_shells);
	if (autocvar_lossless_backpack_pickup)
	{
		if ((other.ammo_shells > autocvar_shells_max_capacity))
		{
			self.ammo_shells = (other.ammo_shells - autocvar_shells_max_capacity);
		}
		else
		{
			self.shells_are_empty = 1;
		}
	}
	other.ammo_nails = (other.ammo_nails + self.ammo_nails);
	if (autocvar_lossless_backpack_pickup)
	{
		if ((other.ammo_nails > autocvar_nails_max_capacity))
		{
			self.ammo_nails = (other.ammo_nails - autocvar_nails_max_capacity);
		}
		else
		{
			self.nails_are_empty = 1;
		}
	}
	other.ammo_rockets = (other.ammo_rockets + self.ammo_rockets);
	if (autocvar_lossless_backpack_pickup)
	{
		if ((other.ammo_rockets > autocvar_rockets_max_capacity))
		{
			self.ammo_rockets = (other.ammo_rockets - autocvar_rockets_max_capacity);
		}
		else
		{
			self.rockets_are_empty = 1;
		}
	}
	other.ammo_cells = (other.ammo_cells + self.ammo_cells);
	if (autocvar_lossless_backpack_pickup)
	{
		if ((other.ammo_cells > autocvar_cells_max_capacity))
		{
			self.ammo_cells = (other.ammo_cells - autocvar_cells_max_capacity);
		}
		else
		{
			self.cells_are_empty = 1;
		}
	}
	new = self.items;
	if (!new)
	{
		new = other.weapon;
	}
	old = other.items;
	other.items = (other.items | new);
	other.bm_full_refill = TRUE;
	bound_other_ammo();
	if (self.ammo_shells)
	{
		if (acount)
		{
			sprint(other, ", ");
		}
		acount = 1;
		if (autocvar_lossless_backpack_pickup)
		{
			if (!self.shells_are_empty)
			{
				s = ftos((self.ammo_shells_old - self.ammo_shells));
			}
			else
			{
				s = ftos(self.ammo_shells_old);
			}
		}
		else
		{
			s = ftos(self.ammo_shells);
		}
		sprint(other, s);
		sprint(other, " shells");
	}
	if (self.ammo_nails)
	{
		if (acount)
		{
			sprint(other, ", ");
		}
		acount = 1;
		if (autocvar_lossless_backpack_pickup)
		{
			if (!self.nails_are_empty)
			{
				s = ftos((self.ammo_nails_old - self.ammo_nails));
			}
			else
			{
				s = ftos(self.ammo_nails_old);
			}
		}
		else
		{
			s = ftos(self.ammo_nails);
		}
		sprint(other, s);
		sprint(other, " nails");
	}
	if (self.ammo_rockets)
	{
		if (acount)
		{
			sprint(other, ", ");
		}
		acount = 1;
		if (autocvar_lossless_backpack_pickup)
		{
			if (!self.rockets_are_empty)
			{
				s = ftos((self.ammo_rockets_old - self.ammo_rockets));
			}
			else
			{
				s = ftos(self.ammo_rockets_old);
			}
		}
		else
		{
			s = ftos(self.ammo_rockets);
		}
		sprint(other, s);
		sprint(other, " rockets");
	}
	if (self.ammo_cells)
	{
		if (acount)
		{
			sprint(other, ", ");
		}
		acount = 1;
		if (autocvar_lossless_backpack_pickup)
		{
			if (!self.cells_are_empty)
			{
				s = ftos((self.ammo_cells_old - self.ammo_cells));
			}
			else
			{
				s = ftos(self.ammo_cells_old);
			}
		}
		else
		{
			s = ftos(self.ammo_cells);
		}
		sprint(other, s);
		sprint(other, " cells");
	}
	if ((!(deathmatch || coop) && autocvar_lossless_backpack_pickup))
	{
		if ((((!self.shells_are_empty || !self.nails_are_empty) || !self.rockets_are_empty) || !self.cells_are_empty))
		{
			sprint(other, ". Max capacity reached.");
		}
	}
	sprint(other, "\n");
	if ((self.backpack_sound == 1))
	{
		sound(other, CHAN_ITEM, "ambience/backpack_soldier.wav", 1, ATTN_NORM);
	}
	else
	{
		if ((self.backpack_sound == 2))
		{
			sound(self, CHAN_ITEM, "misc/null.wav", 1, ATTN_NORM);
			sound(other, CHAN_ITEM, "ambience/backpack_enforcer.wav", 1, ATTN_NORM);
		}
		else
		{
			if ((self.backpack_sound == 3))
			{
				sound(other, CHAN_ITEM, "ambience/backpack_ogre.wav", 1, ATTN_NORM);
			}
			else
			{
				sound(other, CHAN_ITEM, "weapons/lock4.wav", 1, ATTN_NORM);
			}
		}
	}
	if ((autocvar_effects_explosion_shake != 0))
	{
		stuffcmd(other, "bf\n");
	}
	if ((!(deathmatch || coop) && autocvar_lossless_backpack_pickup))
	{
		if (((((self.shells_are_empty == 1) && (self.nails_are_empty == 1)) && (self.rockets_are_empty == 1)) && (self.cells_are_empty == 1)))
		{
			remove(self);
			self = other;
			if (!deathmatch)
			{
				self.weapon = new;
			}
			else
			{
				Deathmatch_Weapon(old, new);
			}
			W_SetCurrentAmmo();
		}
		else
		{
			self.touch = SUB_Null;
			self.nextthink = (time + 1);
			self.think = backpack_touch_delay;
			stemp = self;
			self = other;
			self = stemp;
		}
	}
	else
	{
		remove(self);
		self = other;
		oldwep = self.weapon;
		if (!deathmatch)
		{
			self.weapon = new;
		}
		else
		{
			Deathmatch_Weapon(old, new);
		}
		if ((self.weapon != oldwep))
		{
			W_SetCurrentAmmo();
		}
		if ((self.weapon == IT_SHOTGUN))
		{
			self.currentammo = self.ammo_shells;
			self.items = (self.items | IT_SHELLS);
		}
		else
		{
			if ((self.weapon == IT_SUPER_SHOTGUN))
			{
				self.currentammo = self.ammo_shells;
				self.items = (self.items | IT_SHELLS);
			}
			else
			{
				if ((self.weapon == IT_NAILGUN))
				{
					self.currentammo = self.ammo_nails;
					self.items = (self.items | IT_NAILS);
				}
				else
				{
					if ((self.weapon == IT_SUPER_NAILGUN))
					{
						self.currentammo = self.ammo_nails;
						self.items = (self.items | IT_NAILS);
					}
					else
					{
						if ((self.weapon == IT_GRENADE_LAUNCHER))
						{
							self.currentammo = self.ammo_rockets;
							self.items = (self.items | IT_ROCKETS);
						}
						else
						{
							if ((self.weapon == IT_ROCKET_LAUNCHER))
							{
								self.currentammo = self.ammo_rockets;
								self.items = (self.items | IT_ROCKETS);
							}
							else
							{
								if ((self.weapon == IT_LIGHTNING))
								{
									self.currentammo = self.ammo_cells;
									self.items = (self.items | IT_CELLS);
								}
								else
								{
									if ((self.weapon == IT_LASER_CANNON))
									{
										self.currentammo = self.ammo_cells;
										self.items = (self.items | IT_CELLS);
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

void() backpack_enforcer_movement =
{
	self.movetype = MOVETYPE_FLY;
	self.velocity = '0 0 0.1';
	self.avelocity = ((randomvec() * 333) + '100 100 100');
	self.nextthink = (time + 180);
	self.think = SUB_Remove;
};

void() backpackchildren_touch =
{
	if ((other.classname != "player"))
	{
		return;
	}
	sound(other, CHAN_ITEM, "ambience/backpack_enforcer.wav", 1, ATTN_NORM);
	remove(self);
};

void(vector dir, float num) spawn_more_backpack_cells =
{
	backpackchildren = spawn();
	if ((num == 1))
	{
		backpackchildren.origin = self.origin;
		backpackchildren.velocity = (dir + '5 5 5');
	}
	if ((num == 2))
	{
		backpackchildren.origin = self.origin;
		backpackchildren.velocity = (dir - '5 5 5');
	}
	if ((num == 3))
	{
		backpackchildren.origin = self.origin;
		backpackchildren.velocity = (dir + '3 3 3');
	}
	if ((num == 4))
	{
		backpackchildren.origin = self.origin;
		backpackchildren.velocity = (dir - '3 3 3');
	}
	backpackchildren.solid = SOLID_TRIGGER;
	backpackchildren.movetype = MOVETYPE_TOSS;
	setmodel(backpackchildren, "progs/backpack_enforcer.mdl");
	setsize(backpackchildren, '-24 -24 -20', '24 24 24');
	backpackchildren.scale = 0.9;
	backpackchildren.touch = backpackchildren_touch;
	backpackchildren.owner = self;
	backpackchildren.traileffectnum = particleeffectnum(/*24076i*/"backpack_enforcer");
	backpackchildren.nextthink = (time + 0.65);
	backpackchildren.think = backpack_enforcer_movement;
};

void() followowner =
{
	if ((self.owner.health > 0))
	{
		setorigin(self, self.owner.origin);
	}
	self.think = followowner;
	self.nextthink = (time + 0.2);
};

void() BM_DroppedShellPackPlace =
{
	PlaceItem();
	if (!bm_wasfreed(self))
	{
		self.think = SUB_Remove;	// like a backpack
		self.nextthink = time + 180;
	}
};

void() BM_DroppedShellPack =
{
	self.bm_dropped = TRUE;
	item_sfshotgun();
	self.think = BM_DroppedShellPackPlace;
};

void() DropBackpack =
{
	local entity item;
	local vector direction;

	if (!(((self.ammo_shells + self.ammo_nails) + self.ammo_rockets) + self.ammo_cells))
	{
		return;
	}
	if ((random() < 0.005))
	{
		item = spawn();
		item.origin = (self.origin - '0 0 8');
		item.flags = FL_ITEM;
		item.solid = SOLID_TRIGGER;
		item.movetype = MOVETYPE_TOSS;
		item.think = BM_DroppedShellPack;
		item.nextthink = (time + 0.0001);
		item.target = self.target;
		return;
	}
	item = spawn();
	item.origin = (self.origin - '0 0 24');
	if ((self.classname == "player"))
	{
		item.colormap = self.colormap;
	}
	if (cvar("coop_life_pool"))
	{
		item.owner = self;
	}
	item.items = self.weapon;
	if ((((item.items == IT_MEGAMAN) || (item.items == IT_BANANA)) || (item.items == IT_FUNGUN)))
	{
		item.items = 0;
	}
	if ((item.items == IT_AXE))
	{
		item.netname = "Axe";
	}
	else
	{
		if ((item.items == IT_SHOTGUN))
		{
			item.netname = "Shotgun";
		}
		else
		{
			if ((item.items == IT_SUPER_SHOTGUN))
			{
				item.netname = "Double-barrelled Shotgun";
			}
			else
			{
				if ((item.items == IT_NAILGUN))
				{
					item.netname = "Nailgun";
				}
				else
				{
					if ((item.items == IT_SUPER_NAILGUN))
					{
						item.netname = "Milky Gun";
					}
					else
					{
						if ((item.items == IT_GRENADE_LAUNCHER))
						{
							item.netname = "Grenade Launcher";
						}
						else
						{
							if ((item.items == IT_ROCKET_LAUNCHER))
							{
								item.netname = "Rocket Launcher";
							}
							else
							{
								if ((item.items == IT_LIGHTNING))
								{
									item.netname = "Thunderbolt";
								}
								else
								{
									if ((item.items == IT_CHAINSAW))
									{
										item.netname = "Chainsaw";
									}
									else
									{
										if ((item.items == IT_LASER_CANNON))
										{
											item.netname = "CCC Gun";
										}
										else
										{
											item.netname = "";
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
	item.ammo_shells = self.ammo_shells;
	item.ammo_nails = self.ammo_nails;
	item.ammo_rockets = self.ammo_rockets;
	item.ammo_cells = self.ammo_cells;
	item.velocity_z = 300;
	item.velocity_x = (-100 + (random() * 200));
	item.velocity_y = (-100 + (random() * 200));
	item.flags = FL_ITEM;
	item.solid = SOLID_TRIGGER;
	item.movetype = MOVETYPE_TOSS;
	if ((autocvar_backpack == 1))
	{
		setmodel(item, "progs/backpack1.mdl");
		setsize(item, '-16 -16 -16', VEC_HULL_MAX);
		BackpackPhysics(item);
	}
	else
	{
		if ((autocvar_backpack == 2))
		{
			if ((self.backpack_thrower == 1))
			{
				if (autocvar_backpack_soldier_custom)
				{
					setmodel(item, "progs/backpack_soldier.mdl");
					setsize(item, '-16 -16 -7', VEC_HULL_MAX);
					item.avelocity = '0 250 0';
					item.backpack_sound = 1;
				}
				else
				{
					setmodel(item, "progs/backpack.mdl");
					setsize(item, '-16 -16 0', '16 16 56');
				}
			}
			else
			{
				if ((self.backpack_thrower == 2))
				{
					if (autocvar_backpack_enforcer_custom)
					{
						setmodel(item, "progs/backpack_enforcer.mdl");
						setsize(item, '-16 -16 0', '16 16 48');
						item.scale = 0.9;
						item.traileffectnum = particleeffectnum(/*24076i*/"backpack_enforcer");
						direction = item.velocity;
						spawn_more_backpack_cells(direction, 1);
						spawn_more_backpack_cells(direction, 2);
						item.touch = BackpackTouch;
						item.backpack_sound = 2;
						item.nextthink = (time + 0.62);
						item.think = backpack_enforcer_movement;
						sound(item, CHAN_ITEM, "ambience/backpack_enforcer_ambience.wav", 1, ATTN_NORM);
						return;
					}
					else
					{
						setmodel(item, "progs/backpack.mdl");
						setsize(item, '-16 -16 0', '16 16 56');
					}
				}
				else
				{
					if ((self.backpack_thrower == 3))
					{
						if (autocvar_backpack_ogre_custom)
						{
							setmodel(item, "progs/backpack_ogre.mdl");
							setsize(item, '-16 -16 -6', VEC_HULL_MAX);
							item.scale = 0.8;
							item.avelocity = '0 250 0';
							item.backpack_sound = 3;
						}
						else
						{
							setmodel(item, "progs/backpack.mdl");
							setsize(item, '-16 -16 0', '16 16 56');
						}
					}
					else
					{
						if ((self.backpack_thrower == 4))
						{
							setmodel(item, "progs/backpack.mdl");
							setsize(item, '-16 -16 0', '16 16 56');
						}
						else
						{
							setmodel(item, "progs/backpack.mdl");
							setsize(item, '-16 -16 0', '16 16 56');
						}
					}
				}
			}
		}
		else
		{
			setmodel(item, "progs/backpack.mdl");
			setsize(item, '-16 -16 0', '16 16 56');
		}
	}
	if ((autocvar_backpackspin == 0))
	{
		item.effects = EF_NOMODELFLAGS;
	}
	item.touch = BackpackTouch;
	item.flashtarg = "yes";
	item.cansplash = TRUE;
	if ((coop && cvar("coop_life_pool")))
	{
		item.think = followowner;
		item.effects = (item.effects | EF_FULLBRIGHT);
		item.nextthink = (time + 0.1);
	}
	else
	{
		item.nextthink = (time + 180);
		item.think = SUB_Remove;
	}
};
