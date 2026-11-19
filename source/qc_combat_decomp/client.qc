//Decompiled code. Please respect the original copyright.

.float bm_deathprompt_t;	// PlayerDeathThink: next time the single-player "Press FIRE" prompt may be resent
.string bm_cd_last;			// CheckPowerups (powerupcountdown 1): last countdown number centerprinted...
.float bm_cd_t;				// ...and until when the same one must not be sent again

void() UpdateGunFrames =
{
	// hand-repaired: the decompiler could not recover this weapon-to-model lookup
	if (self.owner.health <= 0 || self.owner.model != "progs/player_torso.mdl")
	{
		remove(self);
		return;
	}

	if (self.owner.weapon == IT_SHOTGUN)
		self.vwep = "progs/p_shot.md3";
	else if (self.owner.weapon == IT_SUPER_SHOTGUN)
	{
		if (autocvar_qc_ssg == 1)
			self.vwep = "progs/QC/p_ssg.md3";
		else
			self.vwep = "progs/p_ssg.md3";
	}
	else if (self.owner.weapon == IT_NAILGUN)
		self.vwep = "progs/ltg_p.md3";	// the sniper rifle rides p_shot's frames (build_srifle.py)
	else if (self.owner.weapon == IT_SUPER_NAILGUN)
		self.vwep = "progs/p_nail2.md3";
	else if (self.owner.weapon == IT_GRENADE_LAUNCHER)
		self.vwep = "progs/p_rock.md3";
	else if (self.owner.weapon == IT_ROCKET_LAUNCHER)
		self.vwep = "progs/p_rock2.md3";
	else if (self.owner.weapon == IT_LIGHTNING)
		self.vwep = "progs/p_light.md3";
	else if (self.owner.weapon == IT_LASER_CANNON)
		self.vwep = "progs/p_laser.md3";
	else if (self.owner.weapon == IT_MEGAMAN)
		self.vwep = "";	// the Mega Man gun has its own little Mega Man (MegaMan_UpdateVwep)
	else if (self.owner.weapon == IT_BANANA)
		self.vwep = "";	// the banana gun has its own little banana (Banana_UpdateVwep)
	else if (self.owner.weapon == IT_FUNGUN)
		self.vwep = "";

	if ((self.owner.items & IT_INVISIBILITY) || self.owner.fd_head || self.owner.fd_fade)
		self.alpha = 0.01;
	else
		self.alpha = 1;
	if (self.owner.items & IT_QUAD)
		self.effects = EF_NOSHADOW;
	else
		self.effects = 0;
	setmodel(self, self.vwep);
	self.frame = self.owner.frame;
	self.think = UpdateGunFrames;
	self.nextthink = time + 0.01;
};

void() UpdatePackFrames =
{
	if ((self.owner.health <= 0) || (self.owner.model != "progs/player_torso.mdl"))
	{
		remove(self);
		return;
	}
	if ((self.owner.items & IT_SUIT))
	{
		setmodel(self, "progs/pack_attach.mdl");
	}
	else
	{
		setmodel(self, string_null);
	}
	if ((self.owner.items & IT_INVISIBILITY) || self.owner.fd_head || self.owner.fd_fade)
	{
		self.alpha = 0.01;
	}
	else
	{
		self.alpha = 1;
	}
	self.frame = self.owner.frame;
	self.think = UpdatePackFrames;
	self.nextthink = (time + 0.01);
};

void() UpdateAxeFrames =
{
	if ((self.owner.health <= 0) || (self.owner.model != "progs/player_torso.mdl"))
	{
		remove(self);
		return;
	}
	if ((self.owner.items & IT_INVISIBILITY) || self.owner.fd_head || self.owner.fd_fade)
	{
		self.alpha = 0.01;
	}
	else
	{
		self.alpha = 1;
	}
	if ((self.owner.throwing == 0))
	{
		setmodel(self, "progs/p_axe.md3");
	}
	else
	{
		setmodel(self, "");
	}
	self.frame = self.owner.frame;
	self.think = UpdateAxeFrames;
	self.nextthink = (time + 0.01);
};

void() AttachVwep =
{
	local entity vwep;

	vwep = spawn();
	vwep.owner = self;
	vwep.solid = 0;
	vwep.movetype = MOVETYPE_NOCLIP;
	vwep.think = UpdateGunFrames;
	vwep.nextthink = (time + 0.01);
	makevectors(vwep.angles);
	setorigin(vwep, (vwep.origin + (v_forward * 5)));
	local float ti;
	ti = gettagindex(self, "Gun");
	if ((ti > 0))
		setattachment(vwep, self, /*22149i*/"Gun");
	else
		setattachment(vwep, self, "");
};

void() AttachPack =
{
	local entity pack;

	pack = spawn();
	pack.owner = self;
	pack.solid = 0;
	pack.movetype = MOVETYPE_NOCLIP;
	pack.think = UpdatePackFrames;
	pack.nextthink = (time + 0.01);
	makevectors(pack.angles);
	setorigin(pack, (pack.origin + (v_forward * 5)));
	local float ti;
	ti = gettagindex(self, "airpack");
	if ((ti > 0))
		setattachment(pack, self, /*39543i*/"airpack");
	else
		setattachment(pack, self, "");
};

void() AttachVAxe =
{
	local entity vwep2;

	vwep2 = spawn();
	vwep2.owner = self;
	vwep2.solid = 0;
	vwep2.movetype = MOVETYPE_NOCLIP;
	vwep2.think = UpdateAxeFrames;
	vwep2.nextthink = (time + 0.01);
	makevectors(vwep2.angles);
	setorigin(vwep2, (vwep2.origin + (v_forward * 5)));
	local float ti;
	ti = gettagindex(self, "Axe");
	if ((ti > 0))
		setattachment(vwep2, self, /*24094i*/"Axe");
	else
		setattachment(vwep2, self, "");
};

float(vector tor_ang) defineLmax =
{
	local float lmax;

	lmax = tor_ang_y + 90;
	if ((lmax > 360))
	{
		lmax = lmax - 360;
	}
	else
	{
		if ((lmax <= 0))
		{
			lmax = lmax + 360;
		}
	}
	if (((tor_ang_y >= 270) && (tor_ang_y <= 360)))
	{
		lmax = lmax + 360;
	}
	return (lmax);
};

float(vector tor_ang) defineRmax =
{
	local float rmax;

	rmax = tor_ang_y - 90;
	if ((rmax >= 360))
	{
		rmax = rmax - 360;
	}
	else
	{
		if ((rmax <= 0))
		{
			rmax = rmax + 360;
		}
	}
	if (((tor_ang_y <= 90) && (tor_ang_y >= 0)))
	{
		rmax = rmax - 360;
	}
	return (rmax);
};

void() DebugAngles =
{
	local vector plrang;
	local float lmax;
	local float rmax;

	if ((self.owner.angles_y >= 0))
	{
	}
	else
	{
	}
	lmax = defineLmax(plrang);
	rmax = defineRmax(plrang);
	if (autocvar_debug_frames)
	{
		ftos(checkUPS_forward(self.owner));
		vtos(plrang);
		ftos(lmax);
		strcat(" \n Legs right max: ", ftos(rmax));
		centerprint3(self.owner, strcat("player frame: ", ftos(self.owner.frame), " dummy leg frame: ", ftos(self.frame), "\n V_Right: ", ftos(checkUPS_right(self.owner)), "\n V_Forward: ", ftos(checkUPS_forward(self.owner))), strcat("\n legs angles: ", vtos(self.angles), "\n parent angles: ", vtos(plrang), "\n parent v_angle: ", vtos(self.owner.v_angle), "\n Legs left max: ", ftos(lmax)), strcat(" \n Legs right max: ", ftos(rmax)));
	}
};

void() overrideTP =
{
	self.owner.angles_x = (0 - self.owner.v_angle_x);
	self.owner.angles_y = self.owner.v_angle_y;
	self.owner.angles_z = self.owner.v_angle_z;
};

float() checkShootframes =
{
	local float framenum;

	if ((!checkSpeed(self.owner, 10) || self.owner.swing))
	{
		if (((self.owner.frame >= 113) && (self.owner.frame <= 118)))
		{
			framenum = -101;
		}
		if (((self.owner.frame >= 107) && (self.owner.frame <= 112)))
		{
			framenum = 148;
		}
	}
	else
	{
		if (checkSpeed(self.owner, 10))
		{
			if (((self.owner.frame >= 103) && (self.owner.frame <= 106)))
			{
				if (((time - self.delay) >= 0.1))
				{
					self.delay = time;
					self.walkframe = (self.walkframe + 1);
				}
				self.frame = self.walkframe;
				if (((self.walkframe > 11) || !self.walkframe))
				{
					self.walkframe = 6;
				}
			}
		}
	}
	return (framenum);
};

void() legsOriginCheck =
{

	if ((((self.frame >= 108) && (self.frame <= 112)) && checkSpeed(self.owner, 10)))
	{
		if ((self.frame == 108))
		{
			self.origin = (self.owner.origin + (v_forward * -8));
		}
		else
		{
			if ((self.frame == 109))
			{
				self.origin = (self.owner.origin + (v_forward * -10));
			}
			else
			{
				if ((self.frame == 110))
				{
					self.origin = (self.owner.origin + (v_forward * -9));
				}
				else
				{
					if ((self.frame == 111))
					{
						self.origin = (self.owner.origin + (v_forward * -8));
					}
					else
					{
						self.origin = (self.owner.origin + (v_forward * -6));
					}
				}
			}
		}
	}
	else
	{
		self.origin = self.owner.origin;
	}
};

float() swimCheck =
{
	if (((self.frame >= 207) && (self.frame <= 213)))
	{
		return (TRUE);
	}
	else
	{
		return (0);
	}
};

void() UpdateLegFrames =
{
	local float frameoff;
	local vector plranglemod;
	local vector playerang;
	local float lmax;
	local float rmax;
	local vector legmod;

	setmodel(self, "progs/player_low.mdl");
	if (((self.owner.health <= 0) || intermission_running))
	{
		remove(self);
		return;
	}
	if (((self.owner.model != "progs/player_torso.mdl") && (self.owner.health > 0)))
	{
		setmodel(self, string_null);
		return;
	}
	if ((self.owner.angles_y >= 0))
	{
	}
	else
	{
	}
	lmax = defineLmax(playerang);
	rmax = defineRmax(playerang);
	self.skin = self.owner.skin;
	if ((self.owner.items & IT_QUAD))
	{
		self.effects = EF_FULLBRIGHT;
	}
	else
	{
		self.effects = self.owner.effects;
	}
	self.colormod = self.owner.colormod;
	frameoff = checkShootframes();
	makevectors(self.owner.angles);
	if ((((self.owner.ishuman != 1) || (self.owner.health <= 0)) || swimCheck()))
	{
		self.colormap = self.owner.colormap;
		self.frame = (self.owner.frame + frameoff);
		self.origin = self.owner.origin;
		self.angles_y = self.owner.angles_y;
		self.think = UpdateLegFrames;
		self.nextthink = (time + 0.001);
		return;
	}
	DebugAngles();
	plranglemod = vectoangles(self.owner.velocity);
	legmod = vectoangles(self.velocity);
	if ((((self.owner.swing && !(self.owner.flags & FL_ONGROUND)) || self.owner.meleeing) || (!self.owner.velocity_x && !self.owner.velocity_y)))
	{
		self.angles = playerang;
	}
	else
	{
		if ((checkUPS_right(self.owner) > 240))
		{
			self.angles_y = rmax;
		}
		else
		{
			if ((checkUPS_right(self.owner) < -240))
			{
				self.angles_y = lmax;
			}
			else
			{
				if ((checkUPS_forward(self.owner) >= 0))
				{
					self.angles_y = 0;
					if ((self.angles_y > lmax))
					{
						self.angles_y = lmax;
					}
					else
					{
						if ((self.angles_y < rmax))
						{
							self.angles_y = rmax;
						}
					}
				}
				else
				{
					self.angles_y = (0 + 180);
				}
			}
		}
	}
	self.colormap = self.owner.colormap;
	if (!((self.owner.frame >= 103) && (self.owner.frame <= 106)))
	{
		self.frame = (self.owner.frame + frameoff);
	}
	legsOriginCheck();
	self.think = UpdateLegFrames;
	self.nextthink = (time + 0.001);
};

void() AttachLegs =
{
	local entity plegs;

	plegs = spawn();
	setmodel(plegs, "progs/player_low.mdl");
	plegs.owner = self;
	plegs.netname = "playerlegs";
	plegs.solid = 0;
	plegs.movetype = MOVETYPE_NOCLIP;
	plegs.think = UpdateLegFrames;
	plegs.exteriormodeltoclient = self;
	plegs.nextthink = time;
};

void() muzzle_emitter_think =
{
	self.frame = (self.frame + 1);
	self.ltime = (self.ltime + 1);
	self.alpha = (self.alpha - 0.02);
	self.scale = (self.scale - 0.01);
	self.velocity_z = (self.velocity_z + 1);
	self.think = muzzle_emitter_think;
	self.nextthink = (time + 0.1);
	if ((self.ltime > 35))
	{
		remove(self);
	}
};

void(entity e, string spritepath, float spscale, vector pos_mod, vector startvelocity, vector velocityrandom, float startalpha, float emittertype) Sprite_Emitter =
{
	newmis = spawn();
	newmis.movetype = MOVETYPE_NOCLIP;
	newmis.solid = 0;
	newmis.viewmodelforclient = e;
	newmis.owner = e;
	newmis.classname = "particle";
	setmodel(newmis, spritepath);
	newmis.scale = spscale;
	newmis.scale = (newmis.scale + ((random() * 0.2) + -0.1));
	newmis.alpha = startalpha;
	newmis.velocity = startvelocity;
	newmis.velocity_x = (newmis.velocity_x + ((random() * (velocityrandom_x - (0 - velocityrandom_x))) + (0 - velocityrandom_x)));
	newmis.velocity_y = (newmis.velocity_y + ((random() * (velocityrandom_y - (0 - velocityrandom_y))) + (0 - velocityrandom_y)));
	newmis.velocity_z = (newmis.velocity_z + ((random() * (velocityrandom_z - (0 - velocityrandom_z))) + (0 - velocityrandom_z)));
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, VEC_ORIGIN);
	if ((emittertype == TYPE_STANDARD))
	{
		pos_mod_x = pos_mod_x + ((random() * 1) + -0.5);
		pos_mod_y = pos_mod_y + ((random() * 0.6) + -0.3);
		pos_mod_z = pos_mod_z + ((random() * 0.6) + -0.3);
	}
	newmis.origin = (newmis.origin + pos_mod);
	if (autocvar_centered_weapons)
	{
		newmis.origin = (newmis.origin + '0 8 -2');
	}
	if ((emittertype == TYPE_SMOKE))
	{
		newmis.think = muzzle_smoke_think;
	}
	else
	{
		newmis.think = muzzle_emitter_think;
	}
	newmis.nextthink = (time + 0.01);
};

void() info_intermission =
{
};

void() SetChangeParms =
{
	if (self.bm_obs)
	{
		SetNewParms();
		parm11 = 1;		// observer: .bm_obs is wiped with the edict on a map change, parm11 carries it (ClientConnect)
		return;
	}
	if ((self.health <= 0))
	{
		SetNewParms();
		return;
	}
	self.items = (self.items - (self.items & 8257536));
	if ((self.health > 100))
	{
		self.health = 100;
	}
	if ((self.health < 50))
	{
		self.health = 50;
	}
	autocvar_berserkmode = 1;
	parm1 = self.items;
	parm2 = self.health;
	parm3 = self.armorvalue;
	if ((self.ammo_shells < 25))
	{
		parm4 = 25;
	}
	else
	{
		parm4 = self.ammo_shells;
	}
	parm5 = self.ammo_nails;
	parm6 = self.ammo_rockets;
	parm7 = self.ammo_cells;
	parm8 = self.weapon;
	parm9 = self.armortype * 100;
	parm10 = self.grenade_ammo;
	parm11 = 0;		// not an observer
};

void() SetNewParms =
{
	parm1 = 69759;		// all stock + Combat+ weapons except IT_CHAINSAW (was 8458367)
	parm2 = 100;
	parm3 = 0;
	parm4 = 60;
	parm5 = 150;
	parm6 = 20;
	parm7 = 100;
	parm8 = IT_ROCKET_LAUNCHER;
	parm9 = 0;
	parm10 = 0;	// grenade_ammo; was left over from whoever set parms last
	parm11 = 0;	// observer flag (SetChangeParms): a new client must never inherit the last one's
};

void() DecodeLevelParms =
{
	if (serverflags)
	{
		if ((world.model == "maps/start.bsp"))
		{
			SetNewParms();
		}
	}
	self.items = parm1;
	self.health = parm2;
	self.armorvalue = parm3;
	self.ammo_shells = parm4;
	self.ammo_nails = parm5;
	self.ammo_rockets = parm6;
	self.ammo_cells = parm7;
	self.weapon = parm8;
	self.armortype = (parm9 * 0.01);
	self.grenade_ammo = parm10;
};

entity() FindIntermission =
{
	local entity spot;
	local float cyc;

	spot = find(world, classname, "info_intermission");
	if (spot)
	{
		cyc = random() * 4;
		while ((cyc > 1))
		{
			spot = find(spot, classname, "info_intermission");
			if (!spot)
			{
				spot = find(spot, classname, "info_intermission");
			}
			cyc = cyc - 1;
		}
		return (spot);
	}
	spot = find(world, classname, "info_player_start");
	if (spot)
	{
		return (spot);
	}
	spot = find(world, classname, "testplayerstart");
	if (spot)
	{
		return (spot);
	}
	objerror("FindIntermission: no spot");
};

void() GotoNextMap =
{
	if (cvar("samelevel"))
	{
		changelevel(mapname);
	}
	else
	{
		changelevel(nextmap);
	}
};

void() ExitIntermission =
{
	if (deathmatch)
	{
		GotoNextMap();
		return;
	}
	intermission_exittime = time + 1;
	intermission_running = intermission_running + 1;
	if ((intermission_running == 2))
	{
		if ((world.model == "maps/e1m7.bsp"))
		{
			WriteByte(MSG_ALL, SVC_CDTRACK);
			WriteByte(MSG_ALL, 2);
			WriteByte(MSG_ALL, 3);
			if (!cvar("registered"))
			{
				WriteByte(MSG_ALL, SVC_FINALE);
				WriteString(MSG_ALL, "As the corpse of the monstrous entity\nChthon sinks back into the lava whence\nit rose, you grip the Rune of Earth\nMagic tightly. Now that you have\nconquered the Dimension of the Doomed,\nrealm of Earth Magic, you are ready to\ncomplete your task in the other three\nhaunted lands of Quake. Or are you? If\nyou don't register Quake, you'll never\nknow what awaits you in the Realm of\nBlack Magic, the Netherworld, and the\nElder World!");
			}
			else
			{
				WriteByte(MSG_ALL, SVC_FINALE);
				WriteString(MSG_ALL, "As the corpse of the monstrous entity\nChthon sinks back into the lava whence\nit rose, you grip the Rune of Earth\nMagic tightly. Now that you have\nconquered the Dimension of the Doomed,\nrealm of Earth Magic, you are ready to\ncomplete your task. A Rune of magic\npower lies at the end of each haunted\nland of Quake. Go forth, seek the\ntotality of the four Runes!");
			}
			return;
		}
		else
		{
			if ((world.model == "maps/e2m8.bsp"))
			{
				WriteByte(MSG_ALL, SVC_CDTRACK);
				WriteByte(MSG_ALL, 7);
				WriteByte(MSG_ALL, 8);
				WriteByte(MSG_ALL, SVC_FINALE);
				WriteString(MSG_ALL, "The Rune of Black Magic throbs evilly in\nyour hand and whispers dark thoughts\ninto your brain. You learn the inmost\nlore of the Hell-Mother; Shub-Niggurath!\nYou now know that she is behind all the\nterrible plotting which has led to so\nmuch death and horror. But she is not\ninviolate! Armed with this Rune, you\nrealize that once all four Runes are\ncombined, the gate to Shub-Niggurath's\nPit will open, and you can face the\nWitch-Goddess herself in her frightful\notherworld cathedral.");
				return;
			}
			else
			{
				if ((world.model == "maps/e3m8.bsp"))
				{
					WriteByte(MSG_ALL, SVC_CDTRACK);
					WriteByte(MSG_ALL, 2);
					WriteByte(MSG_ALL, 3);
					WriteByte(MSG_ALL, SVC_FINALE);
					WriteString(MSG_ALL, "The charred viscera of diabolic horrors\nbubble viscously as you seize the Rune\nof Hell Magic. Its heat scorches your\nhand, and its terrible secrets blight\nyour mind. Gathering the shreds of your\ncourage, you shake the devil's shackles\nfrom your soul, and become ever more\nhard and determined to destroy the\nhideous creatures whose mere existence\nthreatens the souls and psyches of all\nthe population of Earth.");
					return;
				}
				else
				{
					if ((world.model == "maps/e4m7.bsp"))
					{
						WriteByte(MSG_ALL, SVC_CDTRACK);
						WriteByte(MSG_ALL, 2);
						WriteByte(MSG_ALL, 3);
						WriteByte(MSG_ALL, SVC_FINALE);
						WriteString(MSG_ALL, "Despite the awful might of the Elder\nWorld, you have achieved the Rune of\nElder Magic, capstone of all types of\narcane wisdom. Beyond good and evil,\nbeyond life and death, the Rune\npulsates, heavy with import. Patient and\npotent, the Elder Being Shub-Niggurath\nweaves her dire plans to clear off all\nlife from the Earth, and bring her own\nfoul offspring to our world! For all the\ndwellers in these nightmare dimensions\nare her descendants! Once all Runes of\nmagic power are united, the energy\nbehind them will blast open the Gateway\nto Shub-Niggurath, and you can travel\nthere to foil the Hell-Mother's plots\nin person.");
						return;
					}
				}
			}
		}
		GotoNextMap();
	}
	if ((intermission_running == 3))
	{
		if (!cvar("registered"))
		{
			WriteByte(MSG_ALL, SVC_SELLSCREEN);
			return;
		}
		if (((serverflags & 15) == 15))
		{
			WriteByte(MSG_ALL, SVC_FINALE);
			WriteString(MSG_ALL, "Now, you have all four Runes. You sense\ntremendous invisible forces moving to\nunseal ancient barriers. Shub-Niggurath\nhad hoped to use the Runes Herself to\nclear off the Earth, but now instead,\nyou will use them to enter her home and\nconfront her as an avatar of avenging\nEarth-life. If you defeat her, you will\nbe remembered forever as the savior of\nthe planet. If she conquers, it will be\nas if you had never been born.");
			return;
		}
	}
	GotoNextMap();
};

void() IntermissionThink =
{
	if (BM_IntermissionThink())
	{
		return;
	}
	if ((time < intermission_exittime))
	{
		return;
	}
	if (((!self.button0 && !self.button1) && !self.button2))
	{
		return;
	}
	ExitIntermission();
};

void() intermission_delay =
{
	WriteByte(MSG_ALL, SVC_INTERMISSION);
};

void() execute_changelevel =
{
	local entity pos, e, me;

	intermission_running = 1;
	if (deathmatch)
	{
		intermission_exittime = time + 8;
	}
	else
	{
		intermission_exittime = time + 2;
	}
	if (((autocvar_deathmatch_music == 1) && deathmatch))
	{
		WriteByte(MSG_ALL, SVC_CDTRACK);
		WriteByte(MSG_ALL, 16);
		WriteByte(MSG_ALL, 17);
	}
	else
	{
		WriteByte(MSG_ALL, SVC_CDTRACK);
		WriteByte(MSG_ALL, 3);
		WriteByte(MSG_ALL, 3);
	}
	// release drivers / pilots / Rob Dob flyers first: their view stays on the vehicle camera
	// (clientcamera) otherwise, not on the intermission spot
	me = self;
	e = find(world, classname, "player");
	while (e != world)
	{
		self = e;
		Veh_ClientGone();
		JohnBird_ClientGone();
		EricCannon_ClientGone();
		MMTank_ClientGone();
		FD_Reset(e);
		e = find(e, classname, "player");
	}
	self = me;
	pos = FindIntermission();
	other = find(world, classname, "player");
	while ((other != world))
	{
		other.view_ofs = VEC_ORIGIN;
		other.angles = other.v_angle;
		other.fixangle = TRUE;
		other.nextthink = (time + 0.5);
		other.takedamage = 0;
		other.solid = 0;
		other.movetype = 0;
		other.modelindex = 0;
		setorigin(other, pos.origin);
		other = find(other, classname, "player");
	}
	self.think = intermission_delay;
	self.nextthink = (time + 0.1);
};

void() savepos_clevel =
{
	if ((!self.issaved && (self.ltime == 0)))
	{
		localcmd(strcat("save data/", world.model, ".state\n"));
		self.issaved = 1;
	}
	else
	{
		if ((self.issaved && (self.ltime > 0)))
		{
			self.touch = changelevel_touch;
		}
	}
	self.ltime = (self.ltime + 1);
};

void() changelevel_touch =
{

	if ((other.classname != "player"))
	{
		return;
	}
	if (((cvar("noexit") == 1) || ((cvar("noexit") == 2) && (mapname != "start"))))
	{
		T_Damage(other, self, self, 50000);
		return;
	}
	if ((coop || deathmatch))
	{
		bprint(other.netname);
		bprint(" exited the level\n");
	}
	nextmap = self.map;
	SUB_UseTargets();
	if (((self.spawnflags & 1) && (deathmatch == 0)))
	{
		GotoNextMap();
		return;
	}
	self.touch = SUB_Null;
	self.think = execute_changelevel;
	self.nextthink = (time + 0.1);
};

void() spawn_teleporter_particles_big =
{
	pointparticles(particleeffectnum(/*42590i*/"teleporter_particles_big"), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
	self.think = spawn_teleporter_particles_big;
};

void() spawn_slipgate_soak_in_effect =
{
	pointparticles(particleeffectnum(/*42615i*/"slipgate_soak_in_effect"), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
	self.think = spawn_slipgate_soak_in_effect;
};

void() spawn_slipgate_soak_in_and_fog =
{
	particleeffectnum(/*42615i*/"slipgate_soak_in_effect");
	pointparticles(particleeffectnum(/*42615i*/"slipgate_soak_in_effect"), (self.origin - '0 0 80'), VEC_ORIGIN, 1);
	pointparticles(particleeffectnum(/*42639i*/"slipgate_red_fog_effect"), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
	self.think = spawn_slipgate_soak_in_and_fog;
};

void() spawn_slipgate_rising_stars_effect =
{
	pointparticles(particleeffectnum(/*42663i*/"slipgate_rising_stars_effect"), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
	self.think = spawn_slipgate_rising_stars_effect;
};

void() spawn_slipgate_red_fog_and_stars =
{
	particleeffectnum(/*42663i*/"slipgate_rising_stars_effect");
	pointparticles(particleeffectnum(/*42663i*/"slipgate_rising_stars_effect"), (self.origin - '0 0 85'), VEC_ORIGIN, 1);
	pointparticles(particleeffectnum(/*42639i*/"slipgate_red_fog_effect"), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
	self.think = spawn_slipgate_red_fog_and_stars;
};

void() spawn_slipgate_red_fog_effect =
{
	pointparticles(particleeffectnum(/*42639i*/"slipgate_red_fog_effect"), self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.000650);
	self.think = spawn_slipgate_red_fog_effect;
};

void() spawn_slipgate_red_fog_detection =
{
	local float surfacenum;
	local string tex;

	traceline(self.origin, (self.origin + '0 0 200'), FALSE, self);
	if ((trace_fraction == 1))
	{
		return;
	}
	else
	{
		if (world_has_q1_surfs)
		{
			surfacenum = getsurfacenearpoint(world, trace_endpos);
			if ((surfacenum >= 0))
			{
				tex = getsurfacetexture(world, surfacenum);
				if (((tex == "+0sliptop") || (tex == "+0slipbot")))
				{
					self.origin = trace_endpos;
					if ((autocvar_teleporter_particles_slipgates == 4))
					{
						spawn_slipgate_soak_in_and_fog();
						return;
					}
					if ((autocvar_teleporter_particles_slipgates == 5))
					{
						spawn_slipgate_red_fog_and_stars();
						return;
					}
					spawn_slipgate_red_fog_effect();
					return;
				}
				else
				{
					spawn_teleporter_particles_big();
				}
			}
		}
		else
		{
			spawn_teleporter_particles_big();
		}
	}
};

void() select_slipgate_particle_effect =
{
	if ((autocvar_teleporter_particles_slipgates == 1))
	{
		spawn_slipgate_soak_in_effect();
	}
	else
	{
		if ((autocvar_teleporter_particles_slipgates == 2))
		{
			spawn_slipgate_rising_stars_effect();
		}
		else
		{
			if ((autocvar_teleporter_particles_slipgates > 2))
			{
				spawn_slipgate_red_fog_detection();
			}
			else
			{
				return;
			}
		}
	}
};

void() trigger_changelevel =
{
	local vector o;
	local entity particle_spawner;

	if (!self.map)
	{
		objerror("chagnelevel trigger doesn't have map");
	}
	InitTrigger();
	self.touch = changelevel_touch;
	o = (self.mins + self.maxs) * 0.5;
	if (CTF_ENABLED)
	{
		ctf_replacer(o);
	}
	if (((autocvar_teleporter_particles == 2) || (autocvar_teleporter_particles == 3)))
	{
		particle_spawner = spawn();
		if ((world.model == "maps/e1m2.bsp"))
		{
			particle_spawner.origin = '-720 -500 517';
		}
		else
		{
			if ((world.model == "maps/e1m3.bsp"))
			{
				particle_spawner.origin = '1340 1090 580';
			}
			else
			{
				if (((world.model == "maps/e1m4.bsp") && (self.map == "e1m5")))
				{
					particle_spawner.origin = '1205 1070 1430';
				}
				else
				{
					if ((world.model == "maps/e2m2.bsp"))
					{
						particle_spawner.origin = '2180 -180 225';
					}
					else
					{
						if (((world.model == "maps/e2m3.bsp") && (self.map == "e2m4")))
						{
							particle_spawner.origin = '-740 -324 110';
						}
						else
						{
							if ((world.model == "maps/e2m4.bsp"))
							{
								particle_spawner.origin = '-1650 1724 195';
							}
							else
							{
								if ((world.model == "maps/e2m5.bsp"))
								{
									particle_spawner.origin = '-1380 2940 -44';
								}
								else
								{
									if ((world.model == "maps/e4m2.bsp"))
									{
										particle_spawner.origin = '-1504 250 170';
									}
									else
									{
										if ((world.model == "maps/e4m3.bsp"))
										{
											particle_spawner.origin = '-1440 258 175';
										}
										else
										{
											if ((world.model == "maps/e4m4.bsp"))
											{
												particle_spawner.origin = '1375 -1488 56';
											}
											else
											{
												if (((world.model == "maps/e4m5.bsp") && (self.map == "e4m6")))
												{
													particle_spawner.origin = '1248 2535 140';
												}
												else
												{
													if ((world.model == "maps/e4m8.bsp"))
													{
														particle_spawner.origin = '2960 1160 217';
													}
													else
													{
														particle_spawner.origin = o;
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
		particle_spawner.velocity = VEC_ORIGIN;
		particle_spawner.movetype = 0;
		particle_spawner.solid = 0;
		setsize(particle_spawner, VEC_ORIGIN, VEC_ORIGIN);
		particle_spawner.touch = SUB_Null;
		particle_spawner.owner = self;
		if (((world.worldtype == 2) || (world.model == "maps/start.bsp")))
		{
			particle_spawner.think = select_slipgate_particle_effect;
		}
		else
		{
			particle_spawner.think = spawn_teleporter_particles_big;
		}
		particle_spawner.nextthink = (time + 0.1);
	}
};

void() respawn =
{
	if (autocvar_chasecam_death_view)
	{
		stuffcmd(self, strcat("chase_active ", ftos(chaseactive), "\n"));
		stuffcmd(self, strcat("chase_back ", ftos(chaseback), "\n"));
		stuffcmd(self, strcat("chase_up ", ftos(chaseup), "\n"));
		stuffcmd(self, strcat("chase_overhead ", ftos(chaseoverhead), "\n"));
	}
	if (coop)
	{
		if ((autocvar_coop_life_pool == 1))
		{
			if ((LIFE_BONUS >= 1))
			{
				self.lives = (self.lives + 1);
				lives_global = lives_global + 1;
				LIFE_BONUS = LIFE_BONUS - 1;
			}
			if (((self.lives <= 0) && (lives_global > 0)))
			{
				return;
			}
			if ((lives_global == 0))
			{
				changelevel(mapname);
			}
			stuffcmd(self, "chase_active 0\n");
		}
		CopyToBodyQue(self, 30);
		if ((self.musicstart == 0))
		{
			setspawnparms(self);
		}
		PutClientInServer();
	}
	else
	{
		if (deathmatch)
		{
			CopyToBodyQue(self, 30);
			SetNewParms();
			PutClientInServer();
			self.delay = time;
		}
		else
		{
			cvar_set("slowmo", "1");
			localcmd("restart\n");
		}
	}
};

void() ClientKill =
{
	local entity v;
	local vector pos;

	if ((self.health <= 0) || intermission_running)
	{
		return;
	}
	// get out of any vehicle first: T_Damage routes a driver's damage to the van/tank/bird,
	// so the 50000 would blow up the vehicle (and credit its last shooter) instead of killing him
	v = self.veh_van;
	if (((v != world) && (v.veh_driver == self)))
	{
		pos = v.origin + '0 0 40';
		if (Veh_ExitSpot(v, self))
		{
			pos = vd_exit;
		}
		Veh_Leave(v, pos, '0 0 0', (v.veh_state == VEH_STATE_WRECK));
	}
	self.veh_van = world;
	if (Veh_Riding(self))
	{
		Veh_LeavePassenger(self, FALSE);
	}
	v = self.mmt_tank;
	if (((v != world) && !bm_wasfreed(v) && (v.classname == "misc_mm_tank") && (v.mmt_driver == self)))
	{
		MMT_Leave(v, self, FALSE);
	}
	self.mmt_tank = world;
	v = self.jb_vehicle;
	if (((v != world) && (v.jb_pilot == self)))
	{
		JB_Leave(v, JB_FindExitPos(v, self), '0 0 0', FALSE);
	}
	self.jb_vehicle = world;
	if (EricCannon_Active(self))
	{
		EricCannon_Reset(self);	// also gives back takedamage, so the kill below lands
	}
	self.bm_prot_t = 0;
	self.invincible_finished = 0;
	self.deathtype = "suicide";
	T_Damage(self, world, world, 50000);
};

float(vector v) CheckSpawnPoint =
{
	return (0);
};

entity() SelectSpawnPoint =
{
	local entity spot;
	local entity thing;
	local float pcount;
	local entity firstspot;
	local float wraps;

	spot = find(world, classname, "testplayerstart");
	if (spot)
	{
		return (spot);
	}
	if (coop)
	{
		lastspawn = find(lastspawn, classname, "info_player_coop");
		if ((lastspawn == world))
		{
			lastspawn = find(lastspawn, classname, "info_player_start");
		}
		if ((lastspawn != world))
		{
			return (lastspawn);
		}
	}
	else
	{
		if (deathmatch)
		{
			spot = BM_PickSpawn();	// near the action on big maps (bm_match.qc)
			if (spot)
			{
				return (spot);
			}
			spot = lastspawn;
			firstspot = world;
			wraps = 0;
			do
			{
				spot = find(spot, classname, "info_player_deathmatch");
				if ((spot == world))
				{
					// bounded: after one full pass with no free spot, take the first one (telefrag);
					// lastspawn == world never matches below, so it used to spin forever
					wraps = wraps + 1;
					if (((wraps >= 2) || (lastspawn == world)))
					{
						if (firstspot)
						{
							lastspawn = firstspot;
							return (firstspot);
						}
						break;	// no info_player_deathmatch at all: use info_player_start below
					}
				}
				else
				{
					if ((spot == lastspawn))
					{
						return (lastspawn);
					}
					if (!firstspot)
					{
						firstspot = spot;
					}
					pcount = 0;
					thing = findradius(spot.origin, 32);
					while (thing)
					{
						if ((thing.classname == "player"))
						{
							pcount = pcount + 1;
						}
						thing = thing.chain;
					}
					if ((pcount == 0))
					{
						lastspawn = spot;
						return (spot);
					}
				}
			} while(1);
		}
	}
	if (serverflags)
	{
		spot = find(world, classname, "info_player_start2");
		if (spot)
		{
			return (spot);
		}
	}
	spot = find(world, classname, "info_player_start");
	if (!spot)
	{
		error("PutClientInServer: no info_player_start on level");
	}
	return (spot);
};

void() rebreather_think =
{
};

void() SpawnRebreather =
{
	local entity cammodel;
	local entity glass;

	if ((self.classname == "item_artifact_envirosuit"))
	{
		self.owner = other;
	}
	else
	{
		self.owner = self;
	}
	cammodel = spawn();
	cammodel.movetype = 0;
	cammodel.solid = 0;
	cammodel.viewmodelforclient = self.owner;
	cammodel.owner = self.owner;
	cammodel.classname = "gasmask";
	cammodel.effects = (cammodel.effects + EF_NOGUNBOB);
	setmodel(cammodel, "progs/rebreather.mdl");
	cammodel.scale = 0.5;
	setsize(cammodel, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(cammodel, '4 0 1');
	cammodel.think = SUB_Remove;
	cammodel.nextthink = (time + 30);
	glass = spawn();
	glass.movetype = 0;
	glass.solid = 0;
	glass.viewmodelforclient = self.owner;
	glass.owner = self.owner;
	glass.classname = "gasmask_glass";
	glass.effects = (glass.effects + EF_NOGUNBOB);
	glass.alpha = 0.1;
	setmodel(glass, "progs/rebr_glass.spr");
	setsize(glass, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(glass, '89 -80 97');
	glass.think = SUB_Remove;
	glass.nextthink = (time + 30);
};

void() music_changer =
{
	if ((((deathmatch && (self.musicstart == 0)) && (autocvar_deathmatch_music == 1)) && (self.ishuman == 1)))
	{
		if (((random() * 100) <= 20))
		{
			stuffcmd(self, "cd loop 12\n");
		}
		else
		{
			if (((random() * 100) <= 40))
			{
				stuffcmd(self, "cd loop 13\n");
			}
			else
			{
				if (((random() * 100) <= 60))
				{
					stuffcmd(self, "cd loop 14\n");
				}
				else
				{
					if (((random() * 100) <= 80))
					{
						stuffcmd(self, "cd loop 15\n");
					}
					else
					{
						stuffcmd(self, "cd loop 2\n");
					}
				}
			}
		}
		self.musicstart = 1;
	}
};

void() CTF_team_spawn =
{
	local entity teamspawn;

	if ((self.side == BLUE))
	{
		teamspawn = find(world, netname, "blue start");
	}
	else
	{
		teamspawn = find(world, netname, "red start");
	}
	if ((pointcontents(teamspawn.origin) != CONTENT_SOLID))
	{
		setorigin(self, teamspawn.origin);
	}
	else
	{
		if ((self.side == BLUE))
		{
			teamspawn = find(world, netname, "blue start");
		}
		else
		{
			teamspawn = find(world, netname, "red start");
		}
	}
};

void() PutClientInServer =
{
	local entity spot;
	local float bm_ct;

	if (self.bm_obs)
	{
		BM_ObsActivate(self);
		return;
	}

	if (((!deathmatch && !coop) || ((deathmatch || coop) && !IN_SLOWMO)))
	{
		localcmd("slowmo 1\n");
	}
	stuffcmd(self, "v_psycho 0\n");
	self.bm_psycho_sent = 0;
	self.bm_xh_key = 0;
	if (autocvar_chasecam_death_view)
	{
		stuffcmd(self, "chase_active 0\n");
		stuffcmd(self, "chase_back 65\n");
		stuffcmd(self, "chase_up 10\n");
		stuffcmd(self, "chase_overhead 0\n");
	}
	chaseactive = cvar("chase_active");
	chaseback = cvar("chase_back");
	chaseup = cvar("chase_up");
	chaseoverhead = cvar("chase_overhead");
	if (!CTF_ENABLED)
	{
		spot = SelectSpawnPoint();
	}
	self.classname = "player";
	self.health = 100;
	self.health_initial = 100;
	self.takedamage = DAMAGE_AIM;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_WALK;
	self.show_hostile = 0;
	self.max_health = 100;
	self.flags = FL_CLIENT;
	self.air_finished = (time + 12);
	self.dmg = 2;
	self.super_damage_finished = 0;
	self.radsuit_finished = 0;
	self.invisible_finished = 0;
	self.invincible_finished = 0;
	self.effects = 0;
	self.invincible_time = 0;
	self.wetsuit_finished = 0;
	self.inflamed = 0;
	self.shocked = 0;
	if (((((autocvar_coop_life_pool == 1) && coop) && (self.health > 0)) && (self.lives == 0)))
	{
		if ((self.ishuman == 1))
		{
			lives_global = lives_global + 1;
		}
		self.lives = autocvar_coop_lives;
		self.oldorigin = spot.origin;
	}
	DecodeLevelParms();
	MegaMan_Give(self);
	Banana_Give(self);
	FunGun_Give(self);
	self.items = (self.items | IT_LASER_CANNON);		// the CCC gun (key 8): every player has it, it is in no deathmatch map
	self.skypad_safe_t = 0;
	self.skypad_cool_t = 0;
	// BM: skypad_vel_sent is NOT cleared here any more (ClientConnect does it once per map): clearing it on every spawn re-sent sv_maxvelocity each respawn
	if (deathmatch)
	{
		self.items = (self.items | IT_ROCKET_LAUNCHER | IT_ROCKETS | IT_FUNGUN);
		if (self.ammo_rockets < 20)
			self.ammo_rockets = 20;
		if (autocvar_bm_dm_startgun <= 0)
		{
			self.weapon = IT_MEGAMAN;
		}
		else
		{
			if (autocvar_bm_dm_startgun == 2)
				self.bm_dm_gun_alt = 1;
			else if (autocvar_bm_dm_startgun == 3)
				self.bm_dm_gun_alt = 2;
			else if (autocvar_bm_dm_startgun == 4)
				self.bm_dm_gun_alt = 1;		// Thompson removed: fall back to RL
			else if (autocvar_bm_dm_startgun == 5)
				self.bm_dm_gun_alt = 3;
			else if (self.bm_dm_gun_alt >= 1 && self.bm_dm_gun_alt < 3)
				self.bm_dm_gun_alt = self.bm_dm_gun_alt + 1;
			else if (self.bm_dm_gun_alt >= 3)
				self.bm_dm_gun_alt = 1;
			else
			{
				bm_dm_gun_seed = bm_dm_gun_seed + 1;
				if (bm_dm_gun_seed > 3 || bm_dm_gun_seed < 1)
					bm_dm_gun_seed = 1;
				self.bm_dm_gun_alt = bm_dm_gun_seed;
			}
			bm_ct = clienttype(self);
			if (bm_ct == FD_CLIENTTYPE_REAL)
			{
				if (self.bm_dm_gun_alt == 2 && m4_ok)
				{
					self.weapon = IT_FUNGUN;
					self.fg_sel = FG_M4;
					self.m4_vf_t = -1;
				}
				else if (self.bm_dm_gun_alt == 3 && garand_ok)
				{
					self.weapon = IT_FUNGUN;
					self.fg_sel = FG_GARAND;
					self.gar_vf_t = -1;
				}
				else
				{
					self.weapon = IT_ROCKET_LAUNCHER;
				}
			}
			else
			{
				self.weapon = IT_ROCKET_LAUNCHER;
			}
		}
	}
	BM_Spawn();	// full magazines
	Jetpack_Spawn();	// no fuel left over (jetpack.qc)
	Veh_SpawnReset();	// not driving or riding (vehicle_drive.qc)
	EricCannon_Reset(self);	// restore camera/body if respawning after Eric Deason Cannon blast
	MMTank_Reset(self);	// restore camera/body if respawning after Mega Man Tank death
	JohnBird_Reset(self);	// clear sticky slow / burning / CSQC stats on spawn
	Practice_OnPlayerSpawn(self);
	Hammer_Spawn();	// no charge left over (hammer.qc)
	LtGun_Spawn();	// not shocked, not typing (ltgun.qc)
	W_SetCurrentAmmo();
	self.attack_finished = time;
	self.th_pain = player_pain;
	self.th_die = PlayerDie;
	self.deadflag = 0;
	self.pausetime = 0;
	self.origin = (spot.origin + '0 0 1');
	self.angles = spot.angles;
	self.fixangle = TRUE;
	if (((coop && (autocvar_coop_life_pool == 1)) && (autocvar_coop_revive == 1)))
	{
		if (((((pointcontents(self.oldorigin) != CONTENT_LAVA) && (pointcontents(self.oldorigin) != CONTENT_SLIME)) && (pointcontents(self.oldorigin) != CONTENT_SOLID)) && (pointcontents(self.oldorigin) != CONTENT_WATER)))
		{
			if (((((self.dmg_inflictor.classname != "trigger_hurt") && (self.dmg_inflictor.classname != "door")) && (self.dmg_inflictor.classname != "func_train")) && (self.dmg_inflictor.classname != "trap_gravity_well")))
			{
				self.origin = (self.oldorigin + '0 0 10');
			}
		}
	}
	setmodel(self, "progs/eyes.mdl");
	modelindex_eyes = self.modelindex;
	if (autocvar_3rd_person_visible_weapons)
	{
		setmodel(self, "progs/player_shot.mdl");
	}
	else
	{
		if ((autocvar_player_model == 1))
		{
			setmodel(self, "progs/player1.mdl");
		}
		else
		{
			if ((autocvar_player_model == 2))
			{
				setmodel(self, "progs/player2.mdl");
			}
			else
			{
				if ((autocvar_player_model == 3))
				{
					setmodel(self, "progs/player3.mdl");
				}
				else
				{
					if ((autocvar_player_model == 4))
					{
						setmodel(self, "progs/player4.mdl");
					}
					else
					{
						if ((autocvar_player_model == 5))
							setmodel(self, "progs/player_torso.mdl");
						else
							setmodel(self, "progs/player_id1.mdl");
					}
				}
			}
		}
	}
	modelindex_player = self.modelindex;
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	self.view_ofs = '0 0 22';
	if ((CTF_ENABLED && !self.side))
	{
		choose_team();
	}
	if (CTF_ENABLED)
	{
		self.has_flag = 0;
		self.gametype = CTF;
		CTF_team_spawn();
	}
	music_changer();
	if ((self.model == "progs/player_torso.mdl"))
	{
		AttachVwep();
		AttachVAxe();
		AttachLegs();
		AttachPack();
	}
	if ((self.ishuman == 1))
	{
		SNGHeater();
	}
	player_stand1();
	autocvar_berserkmode = 1;
	if (((self.grenade_ammo <= 0) && (world.model == "maps/start.bsp")))
	{
		if ((skill >= 2))
		{
			self.grenade_ammo = (self.grenade_ammo + 1);
		}
		else
		{
			self.grenade_ammo = (self.grenade_ammo + 2);
		}
	}
	else
	{
		if (deathmatch)
		{
			self.grenade_ammo = (self.grenade_ammo + 1);
		}
	}
	if ((deathmatch || coop))
	{
		makevectors(self.angles);
		spawn_tfog((self.origin + (v_forward * 20)));
	}
	self.bulletspeed = 900;
	PLR_CNT = PLR_CNT + 1;
	self.revivetimer = 0;
	if (((!coop && !deathmatch) && autocvar_auto_save))
	{
		stuffcmd(self, "wait 3000;save autosaves/autosave\n");
		stuffcmd(self, "Echo Autosaving...\n");
	}
	if ((!CTF_ENABLED && (self.ishuman == 1)))
	{
		spawn_tdeath(self.origin, self);
	}
	if (!autocvar_ent_fog)
	{
		localcmd("fog 0\n");
	}
	Underdog_Spawn();
	BM_PlayerSpawned();	// spawn protection
	FloatHead_StartSpawner();	// floating heads in deathmatch (floathead.qc)
};

void() info_player_start =
{
	if (CTF_ENABLED)
	{
		ctf_replacer(self.origin);
	}
};

void() info_player_start2 =
{
};

void() testplayerstart =
{
};

void() info_player_deathmatch =
{
};

void() info_player_coop =
{
};

void() NextLevel =
{
	local entity o;

	if (BM_NextLevel())
	{
		return;	// bm_maplist
	}
	if ((mapname == "start"))
	{
		if (!cvar("registered"))
		{
			mapname = "e1m1";
		}
		else
		{
			if (!(serverflags & 1))
			{
				mapname = "e1m1";
				serverflags = serverflags | 1;
			}
			else
			{
				if (!(serverflags & 2))
				{
					mapname = "e2m1";
					serverflags = serverflags | 2;
				}
				else
				{
					if (!(serverflags & 4))
					{
						mapname = "e3m1";
						serverflags = serverflags | 4;
					}
					else
					{
						if (!(serverflags & 8))
						{
							mapname = "e4m1";
							serverflags = serverflags - 7;
						}
					}
				}
			}
		}
		o = spawn();
		o.map = mapname;
	}
	else
	{
		o = find(world, classname, "trigger_changelevel");
		if (!o)
		{
			mapname = "start";
			o = spawn();
			o.map = mapname;
		}
	}
	nextmap = o.map;
	gameover = TRUE;
	if ((o.nextthink < time))
	{
		o.think = execute_changelevel;
		o.nextthink = (time + 0.1);
	}
};

void() CheckRules =
{
	local float timelimit;
	local float fraglimit;

	if (gameover)
	{
		return;
	}
	timelimit = cvar("timelimit") * 60;
	fraglimit = cvar("fraglimit");
	if (CTF_ENABLED)
	{
		capture_limit = cvar("ctf_capture_limit");
	}
	if ((timelimit && (time >= timelimit)))
	{
		NextLevel();
		return;
	}
	if (((fraglimit && (self.frags >= fraglimit)) && !CTF_ENABLED))
	{
		NextLevel();
		return;
	}
	if ((capture_limit && ((BLUE_CAPS >= capture_limit) || (RED_CAPS >= capture_limit))))
	{
		NextLevel();
		return;
	}
};

void() Spectate =
{
	local entity whospec;

	if (((time - self.delay) >= 0.5))
	{
		stuffcmd(self, "chase_active 1\n");
	}
	if (((self.button2 || self.button1) || self.button0))
	{
		self.cnt = (self.cnt + 1);
	}
	if ((self.clientcamera.health <= 0))
	{
		self.clientcamera = self;
	}
	if ((self.cnt == 0))
	{
		whospec = find(whospec, classname, "player");
	}
	if (((self.cnt == 2) && (whospec == self.clientcamera)))
	{
		whospec = find(whospec, classname, "player");
	}
	if ((self.cnt == 3))
	{
		if (((self.button2 || self.button1) || self.button0))
		{
			if ((self.clientcamera == self.enemy))
			{
				whospec = self.clientcamera.enemy;
			}
			else
			{
				whospec = find(world, classname, self.enemy.classname);
			}
			if ((self.cnt > 3))
			{
				self.cnt = 0;
			}
		}
	}
	if (((whospec.health > 0) && (whospec != self.clientcamera)))
	{
		self.clientcamera = whospec;
	}
};

void() PlayerDeathThink =
{
	local float forward;

	if ((self.flags & FL_ONGROUND))
	{
		forward = vlen(self.velocity);
		forward = forward - 20;
		if ((forward <= 0))
		{
			self.velocity = VEC_ORIGIN;
		}
		else
		{
			self.velocity = (forward * normalize(self.velocity));
		}
	}
	if (autocvar_coop_life_pool)
	{
		if ((self.ishuman == 1))
		{
			if (((time - self.delay) >= 1))
			{
				ftos(lives_global);
				centerprint3(self, "\n\n\n\n\n\n\n\n\n\n\n\nYou are ^1DEAD \n", "\n\n\n\n\n\n\n\n^3lives left: ^1", ftos(self.lives), "\n\n^2Players left: ^1", ftos(lives_global));
				self.delay = time;
			}
		}
		if ((self.lives == 0))
		{
			Spectate();
		}
	}
	autocvar_berserkmode = 1;
	if ((self.deadflag == DEAD_DEAD))
	{
		if (autocvar_coop_life_pool)
		{
			if (((self.ishuman == 1) && !((self.button2 || self.button1) || self.button0)))
			{
				self.lives = (self.lives - 1);
				autocvar_coop_lives = self.lives;
				if ((self.lives == 0))
				{
					lives_global = lives_global + -1;
					self.delay = time;
				}
			}
			self.oldorigin = self.origin;
			DED_PLR = DED_PLR + 1;
		}
		if (CTF_ENABLED)
		{
			self.has_flag = 0;
		}
		if (((self.button2 || self.button1) || self.button0))
		{
			return;
		}
		self.deadflag = DEAD_RESPAWNABLE;
		return;
	}
	bodyCheck();
	if ((!coop && !deathmatch))
	{
		if ((vlen(self.velocity) > 18))
		{
			return;
		}
		if ((time < self.bm_deathprompt_t))
		{
			// sent once a second (it stays up 2 s), not every frame
		}
		else if (autocvar_auto_save)
		{
			centerprint(self, "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n^9Press ^1FIRE^9 to load last autosave, ^3JUMP^9 to restart level,\nor ^1F9^9 to load last quicksave");
			self.bm_deathprompt_t = time + 1;
		}
		else
		{
			centerprint(self, "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n^9Press ^3FIRE ^9 to load last quicksave or ^3JUMP^9 to restart level");
			self.bm_deathprompt_t = time + 1;
		}
		if (self.button0)
		{
			cvar_set("slowmo", "1");
			if (autocvar_auto_save)
			{
				stuffcmd(self, "wait 100;disconnect;wait 50000;load autosaves/autosave\n");
			}
			else
			{
				stuffcmd(self, "wait 100;disconnect;wait 50000;load quick\nslowmo 1\n");
			}
		}
	}
	if (((!self.button2 && !self.button1) && !self.button0))
	{
		return;
	}
	self.button0 = 0;
	self.button1 = 0;
	self.button2 = 0;
	respawn();
};

void() PlayerJump =
{
	if ((self.flags & FL_WATERJUMP))
	{
		return;
	}
	if ((self.waterlevel >= 2))
	{
		if ((self.watertype == CONTENT_WATER))
		{
			self.velocity_z = 100;
		}
		else
		{
			if ((self.watertype == CONTENT_SLIME))
			{
				self.velocity_z = 80;
			}
			else
			{
				self.velocity_z = 50;
			}
		}
		if ((self.swim_flag < time))
		{
			self.swim_flag = (time + 1);
			if ((random() < 0.5))
			{
				sound7(self, CHAN_BODY, "misc/water1.wav", 1, ATTN_NORM, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_BODY, "misc/water2.wav", 1, ATTN_NORM, SNDSPD);
			}
		}
		return;
	}
	if (!(self.flags & FL_ONGROUND))
	{
		return;
	}
	if (!(self.flags & FL_JUMPRELEASED))
	{
		return;
	}
	self.flags = (self.flags - (self.flags & FL_JUMPRELEASED));
	self.flags = (self.flags - FL_ONGROUND);
	self.button2 = 0;
	sound7(self, CHAN_BODY, "player/plyrjmp8.wav", 1, ATTN_NORM, SNDSPD);
	player_jump();
	self.velocity_z = (self.velocity_z + 270);
};

void() WetsuitMove =
{
	if ((self.wetsuit_finished > time))
	{
		if ((self.waterlevel == 2))
		{
			self.velocity = (self.velocity * 1.25);
		}
		if ((self.waterlevel == 3))
		{
			self.velocity = (self.velocity * 1.5);
		}
		if ((self.waterlevel >= 2))
		{
			if ((self.swim_flag < time))
			{
				self.swim_flag = (time + 7);
				if ((cvar("slowmo") < 0.9))
				{
					sound7(self, CHAN_BODY, "misc/wetsuit.wav", 1, ATTN_NORM, SNDSPD);
				}
				else
				{
					sound(self, CHAN_BODY, "misc/wetsuit.wav", 1, ATTN_NORM);
				}
			}
			else
			{
				if ((fabs(((self.swim_flag - time) - 6)) < 0.04))
				{
					DeathBubbles(1);
				}
				else
				{
					if ((fabs(((self.swim_flag - time) - 5.5)) < 0.04))
					{
						DeathBubbles(1);
					}
					else
					{
						if ((fabs(((self.swim_flag - time) - 5)) < 0.04))
						{
							DeathBubbles(1);
						}
					}
				}
			}
		}
	}
};

void() WaterMove =
{
	if ((self.movetype == MOVETYPE_NOCLIP))
	{
		return;
	}
	if ((self.health < 0))
	{
		return;
	}
	if ((self.waterlevel != 3))
	{
		if ((self.air_finished < time))
		{
			sound7(self, CHAN_VOICE, "player/gasp2.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			if ((self.air_finished < (time + 9)))
			{
				sound7(self, CHAN_VOICE, "player/gasp1.wav", 1, ATTN_NORM, SNDSPD);
			}
		}
		self.air_finished = (time + 12);
		self.dmg = 2;
	}
	else
	{
		if ((self.air_finished < time))
		{
			if ((self.pain_finished < time))
			{
				self.dmg = (self.dmg + 2);
				if ((self.dmg > 15))
				{
					self.dmg = 10;
				}
				T_Damage(self, world, world, self.dmg);
				self.pain_finished = (time + 1);
			}
		}
	}
	if (!self.waterlevel)
	{
		if ((self.flags & FL_INWATER))
		{
			sound(self, CHAN_BODY, "misc/outwater.wav", 1, ATTN_NORM);
			self.flags = (self.flags - FL_INWATER);
		}
		return;
	}
	if ((self.waterlevel >= 3))
	{
		if ((self.items & IT_SUIT))
		{
			self.watertime = (self.watertime + 1);
			if ((self.watertime == 230))
			{
				if ((cvar("slowmo") < 0.9))
				{
					sound7(self, CHAN_AUTO, "misc/wetsuit.wav", 1, ATTN_NORM, SNDSPD);
				}
				else
				{
					sound(self, CHAN_AUTO, "misc/wetsuit.wav", 1, ATTN_NORM);
				}
			}
			if ((self.watertime == 305))
			{
				DeathBubbles(1);
				Sprite_Emitter(self, "progs/s_bubble.spr", 2, '20 0 -20', '320 30 -10', '25 18 10', 0.7, TYPE_SMOKE);
			}
			if ((self.watertime == 318))
			{
				DeathBubbles(1);
				Sprite_Emitter(self, "progs/s_bubble.spr", 2, '20 0 -20', '150 -10 -30', '25 18 10', 0.7, TYPE_SMOKE);
			}
			if ((self.watertime == 331))
			{
				DeathBubbles(1);
				Sprite_Emitter(self, "progs/s_bubble.spr", 2, '20 0 -20', '220 10 -40', '25 18 10', 0.7, TYPE_SMOKE);
			}
			if ((self.watertime == 342))
			{
				DeathBubbles(1);
				self.watertime = 0;
				Sprite_Emitter(self, "progs/s_bubble.spr", 2, '20 0 -20', '130 25 -20', '25 18 10', 0.7, TYPE_SMOKE);
			}
		}
	}
	if ((self.watertype == CONTENT_LAVA))
	{
		if ((autocvar_quadreplacer > 0))
		{
			if ((autocvar_fire_projectiles_and_lava_inflame_particles && (self.inflamed == 0)))
			{
				if (((time - self.delay) >= 1.5))
				{
					sound(self, CHAN_AUTO, "player/inflame.wav", 0.5, ATTN_NORM);
					sound(self, 120, "zombie/corpse_fire.wav", 1, ATTN_NORM);
					self.delay = time;
				}
			}
			self.inflamed = 1;
			self.inflametime = (time + 10);
			self.inflamepause = (time + autocvar_fire_projectiles_and_lava_inflame_frequence);
		}
		if ((self.dmgtime < time))
		{
			if ((self.radsuit_finished > time))
			{
				self.dmgtime = (time + 1);
			}
			else
			{
				self.dmgtime = (time + 0.2);
			}
			T_Damage(self, world, world, (10 * self.waterlevel));
		}
	}
	else
	{
		if ((self.watertype == CONTENT_SLIME))
		{
			if (autocvar_wizard_projectiles_and_slime_poison_time)
			{
				self.poisoned = 1;
				self.poisontime = (time + autocvar_wizard_projectiles_and_slime_poison_time);
				self.poisonpause = (time + autocvar_wizard_projectiles_and_slime_poison_frequence);
			}
			if (((self.dmgtime < time) && (self.radsuit_finished < time)))
			{
				self.dmgtime = (time + 1);
				T_Damage(self, world, world, (4 * self.waterlevel));
			}
		}
	}
	if (!(self.flags & FL_INWATER))
	{
		if ((self.watertype == CONTENT_LAVA))
		{
			sound7(self, CHAN_BODY, "player/inlava.wav", 1, ATTN_NORM, SNDSPD);
		}
		if ((self.watertype == CONTENT_WATER))
		{
			sound7(self, CHAN_BODY, "player/inh2o.wav", 1, ATTN_NORM, SNDSPD);
		}
		if ((self.watertype == CONTENT_SLIME))
		{
			sound7(self, CHAN_BODY, "player/slimbrn2.wav", 1, ATTN_NORM, SNDSPD);
		}
		self.flags = (self.flags + FL_INWATER);
		self.dmgtime = 0;
	}
	if (!(self.flags & FL_WATERJUMP))
	{
		self.velocity = (self.velocity - (((0.8 * self.waterlevel) * frametime) * self.velocity));
	}
};

void() CheckWaterJump =
{
	local vector start;
	local vector end;

	// water jump (rd): Quake's own test, which the decompile had flattened (both traces were the same line, so it never fired)
	makevectors('0 1 0' * self.angles_y);
	start = self.origin;
	start_z = (start_z + 8);
	end = start + (v_forward * 24);
	traceline(start, end, TRUE, self);
	if ((trace_fraction < 1))
	{
		start_z = ((start_z + self.maxs_z) - 8);
		end = start + (v_forward * 24);
		self.movedir = (trace_plane_normal * -50);
		traceline(start, end, TRUE, self);
		if ((trace_fraction == 1))
		{
			self.flags = (self.flags | FL_WATERJUMP);
			self.velocity_z = 225;
			self.flags = (self.flags - (self.flags & FL_JUMPRELEASED));
			self.teleport_time = (time + 2);
			return;
		}
	}
};

void() ChasecamInit =
{
	local vector pang;

	pang = vectoangles(self.velocity);
	if ((!(self.flags & FL_ONGROUND) && (self.health > 0)))
	{
		if ((!self.velocity_x && !self.velocity_y))
		{
			self.angles_y = self.v_angle_y;
		}
		else
		{
			if (((Dot(v_forward, self.velocity) < 160) && (Dot(v_forward, self.velocity) > -160)))
			{
				self.angles_y = 0;
			}
			else
			{
				self.angles = pang;
			}
		}
	}
	else
	{
		cvar("chase_active");
		if (((cvar("chase_active") && (self.ishuman == 1)) && (self.health > 0)))
		{
			if ((!self.velocity_x && !self.velocity_y))
			{
				self.angles_y = self.v_angle_y;
			}
			else
			{
				if ((!self.button0 && (self.weaponframe == 0)))
				{
					self.angles_y = 0;
				}
			}
		}
	}
};

void() NoclipMove =
{

	if ((self.movetype != MOVETYPE_NOCLIP))
	{
		return;
	}
	if (self.button2)
	{
		self.noclip = 1100;
	}
	else
	{
		self.noclip = 400;
	}
	if ((((Dot(v_forward, self.velocity) > 0.1) || (Dot(v_up, self.velocity) <= -319)) || (Dot(v_up, self.velocity) >= 319)))
	{
		self.velocity = (v_forward * self.noclip);
	}
	else
	{
		if ((((Dot(v_forward, self.velocity) < -0.1) || (Dot(v_up, self.velocity) <= -319)) || (Dot(v_up, self.velocity) >= 319)))
		{
			self.velocity = (v_forward * (0 - self.noclip));
		}
	}
};

void() LadderSound =
{
	if ((self.timeladder < time))
	{
		self.timeladder = (time + self.entladder.waitmin);
		if ((self.entladder.sounds != 4))
		{
			self.lip = random();
			if (((self.lip < 0.25) && self.entladder.noise1))
			{
				sound(self, CHAN_BODY, self.entladder.noise1, 1, ATTN_NORM);
			}
			else
			{
				if (((self.lip < 0.5) && self.entladder.noise2))
				{
					sound(self, CHAN_BODY, self.entladder.noise2, 1, ATTN_NORM);
				}
				else
				{
					if (((self.lip < 0.75) && self.entladder.noise3))
					{
						sound(self, CHAN_BODY, self.entladder.noise3, 1, ATTN_NORM);
					}
					else
					{
						if (self.entladder.noise4)
						{
							sound(self, CHAN_BODY, self.entladder.noise4, 1, ATTN_NORM);
						}
					}
				}
			}
		}
	}
};

void() Ladder_ClimbJump =
{
	self.velocity = VEC_ORIGIN;
	if ((self.v_angle_x < -25))
	{
		self.velocity_z = self.entladder.speed;
	}
	else
	{
		if ((self.v_angle_x > 25))
		{
			self.velocity_z = (0 - self.entladder.speed);
		}
		else
		{
			self.velocity = (v_forward * 215);
		}
	}
	LadderSound();
};

void() Ladder_ClimbMove =
{

	if ((((Dot(v_forward, self.velocity) > 2) || (Dot(v_up, self.velocity) < -20)) || (Dot(v_up, self.velocity) > 20)))
	{
		if ((self.v_angle_x < -25))
		{
			self.velocity_z = self.entladder.speed;
		}
		else
		{
			if ((self.v_angle_x > 25))
			{
				self.velocity = (v_forward * self.entladder.speed);
				self.velocity_z = (0 - self.entladder.speed);
			}
			else
			{
				self.velocity = VEC_ORIGIN;
			}
		}
		LadderSound();
	}
};

void() autosave_timer =
{
	if (((time - SAVE_TIMER) >= 320))
	{
		stuffcmd(self, "Echo Autosaving...\n");
		stuffcmd(self, "save autosaves/autosave\n");
		SAVE_TIMER = time;
	}
};

// TRUE while a vehicle (van, tank, Eric Cannon, Winged John) has hidden p's body; the quad/skin refresh and
// CheckPowerups must not undo its EF_NODRAW / alpha
float(entity p) CL_InVehicleHidden =
{
	return (Veh_Driving(p) || MMTank_Driving(p) || EricCannon_Active(p) || JohnBird_Flying(p));
};

void() PlayerPreThink =
{
	local float oldnodraw;
	local float psy;

	if (self.bm_obs)
	{
		BM_ObsFrame();
		return;
	}

	if (CTF_ENABLED)
	{
		set_team_color();
		self.blue_captures = BLUE_CAPS;
		self.red_captures = RED_CAPS;
	}
	if (BotPreFrame())
	{
		return;
	}
	if (intermission_running)
	{
		IntermissionThink();
		return;
	}
	if ((self.view_ofs == VEC_ORIGIN))
	{
		return;
	}
	makevectors(self.v_angle);
	if ((autocvar_slowmo_pitch == 1))
	{
		SNDSPD = 100 * autocvar_slowmo;
	}
	if (self.dmenu)
	{
		DebugMenu();
	}
	if ((((self.waterlevel >= 3) && (self.ishuman == 1)) && (autocvar_slowmo == 1)))
	{
		self.PLR_SNDSPD = 75;
		if ((!coop && !deathmatch))
		{
			SNDSPD = 75;
		}
	}
	else
	{
		if ((autocvar_slowmo_pitch == 1))
		{
			self.PLR_SNDSPD = (100 * autocvar_slowmo);
		}
		else
		{
			self.PLR_SNDSPD = 100;
		}
	}
	if ((autocvar_coop_life_pool && (self.health > 0)))
	{
		self.clientcamera = self;
	}
	if ((autocvar_player_reflection_fix && ((((self.waterlevel == 1) || (self.waterlevel == 2)) && !(deathmatch || coop)) && !autocvar_chase_active)))
	{
		self.model = "";
	}
	else
	{
		if (((time - self.delay) >= 0.3))
		{
			if (autocvar_3rd_person_visible_weapons)
			{
				switch_saw();
			}
			else
			{
				if ((autocvar_player_model == 1))
				{
					self.model = "progs/player1.mdl";
				}
				else
				{
					if ((autocvar_player_model == 2))
					{
						self.model = "progs/player2.mdl";
					}
					else
					{
						if ((autocvar_player_model == 3))
						{
							self.model = "progs/player3.mdl";
						}
						else
						{
							if ((autocvar_player_model == 4))
							{
								self.model = "progs/player4.mdl";
							}
							else
							{
								if ((self.health > 0))
								{
									if ((autocvar_player_model == 5))
										setmodel(self, "progs/player_torso.mdl");
									else
										setmodel(self, "progs/player_id1.mdl");
									if ((self.items & IT_SUIT))
									{
										if ((autocvar_player_model == 5))
											self.skin = 1;
										else
											self.skin = 0;
									}
									else
									{
										oldnodraw = (self.effects & EF_NODRAW);
										if ((self.items & IT_QUAD))
										{
											self.effects = 576;
											self.colormod = '0 0 6';
										}
										else
										{
											if (autocvar_bright_skins)
											{
												self.effects = (self.effects | EF_FULLBRIGHT);
											}
											else
											{
												self.effects = 0;
											}
											self.skin = 0;
											self.colormod = '1 1 1';
										}
										if ((oldnodraw && CL_InVehicleHidden(self)))
										{
											self.effects = (self.effects | EF_NODRAW);	// a vehicle hid him: keep it
										}
									}
									modelindex_player = self.modelindex;
									setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
								}
							}
						}
					}
				}
			}
			self.delay = time;
		}
	}
	CheckRules();
	Spruce_PlayerWaterPreThink(self);
	WaterMove();
	NoclipMove();
	WetsuitMove();
	if ((self.rammed == 1))
	{
		self.velocity = (self.velocity - (ramdirection * autocvar_warlord_ram_pushback));
		self.rammed = 0;
	}
	if (autocvar_player_wounded_bleeding)
	{
		if ((self.health <= 40))
		{
			if ((self.health <= 20))
			{
				Bleeding2(self);
			}
			else
			{
				Bleeding1(self);
			}
		}
		else
		{
			Bleedingnull(self);
		}
	}
	if (autocvar_player_wounded_heartbeat)
	{
		if (((self.health <= 30) && (self.health > 0)))
		{
			if ((self.health <= 15))
			{
				if ((self.playerheartbeat_finished < time))
				{
					PlayerHeartbeat_quick();
				}
			}
			else
			{
				if ((self.playerheartbeat_finished < time))
				{
					PlayerHeartbeat_slow();
				}
			}
		}
	}
	if (((autocvar_player_changes_shirt_color_according_to_used_armor && !deathmatch) && ((time - self.delay) > 1)))
	{
		if ((self.armortype == 0.3))
		{
			stuffcmd(self, "topcolor 3\n");
		}
		else
		{
			if ((self.armortype == 0.6))
			{
				stuffcmd(self, "topcolor 5\n");
			}
			else
			{
				if ((self.armortype == 0.8))
				{
					stuffcmd(self, "topcolor 4\n");
				}
				else
				{
					stuffcmd(self, "topcolor 2\n");
				}
			}
		}
		self.delay = time;
	}
	if ((autocvar_flying_dust && !deathmatch))
	{
		if ((world.worldtype == 2))
		{
			if ((autocvar_flying_dust == 2))
			{
				if ((self.flying_dust_finished < time))
				{
					spawn_flying_dust();
				}
			}
		}
		else
		{
			if ((self.flying_dust_finished < time))
			{
				spawn_flying_dust();
			}
		}
	}
	if (((self.poisoned == 1) && (self.health > 0)))
	{
		if (((((self.poisontime > time) && (self.poisonpause < time)) && (self.radsuit_finished < time)) && (self.invincible_finished < time)))
		{
			self.poisonpause = ((time + autocvar_wizard_projectiles_and_slime_poison_frequence) + (crandom() * 0.5));
			T_Damage(self, world, world, autocvar_wizard_projectiles_and_slime_poison_damage);
			stuffcmd(self, "bf\n");
			if (autocvar_wizard_projectiles_and_slime_poison_flicker)
			{
				te_customflash(self.origin, 5000, 0.33, '0 0.4 0.2');
			}
		}
		if ((self.watertype == CONTENT_WATER))
		{
			self.poisoned = 0;
		}
	}
	if (((self.inflamed == 1) && (self.health > 0)))
	{
		if (((((self.inflametime > time) && (self.inflamepause < time)) && (self.radsuit_finished < time)) && (self.invincible_finished < time)))
		{
			self.inflamepause = ((time + autocvar_fire_projectiles_and_lava_inflame_frequence) + (crandom() * 0.5));
			T_Damage(self, world, world, autocvar_fire_projectiles_and_lava_inflame_damage);
			if (autocvar_fire_projectiles_and_lava_inflame_flicker)
			{
				te_customflash(self.origin, 5000, 0.33, '0.4 0.1 0.1');
			}
		}
		if ((self.watertype == CONTENT_WATER))
		{
			self.inflamed = 0;
			sound(self, 120, "misc/null.wav", 1, ATTN_NORM);
		}
		if ((self.inflametime < time))
		{
			self.traileffectnum = 0;	// BM: was particleeffectnum(""), which is -1 and spams "Unknown effect number 65535"
			self.inflamed = 0;
			sound(self, 120, "misc/null.wav", 1, ATTN_NORM);
		}
		if ((autocvar_fire_projectiles_and_lava_inflame_particles && (self.inflamed == 1)))
		{
			self.traileffectnum = particleeffectnum(/*43670i*/"burning_player");
		}
	}
	else
	{
		self.traileffectnum = 0;	// BM: was particleeffectnum(""), which is -1 and spams "Unknown effect number 65535"
	}
	if (the_matrix)
	{
		if ((matrixcounter > time))
		{
			localcmd("slowmo ");
			localcmd(ftos(autocvar_slowmotion_intensity));
			localcmd("\n");
		}
		else
		{
			localcmd("slowmo 1\n");
			the_matrix = 0;
		}
	}
	if ((!matrixcounter && (autocvar_sv_cheats != 1)))
	{
		if ((!self.slowmo_timer && (autocvar_slowmo != 1)))
		{
			cvar_set("slowmo", "1");
		}
	}
	// one v_psycho value from all three sources (powerups, evil faces, ghost follower), sent once: when the sources
	// disagreed, each block called BM_Psycho with its own value and the cache flipped 1/0 every frame (2 stuffcmds)
	psy = -1;	// -1 = no source enabled, leave v_psycho alone
	if ((autocvar_psycho && time))
	{
		if (((pentpsycho && self.invincible_finished) || (quadpsycho && self.super_damage_finished)))
		{
			psy = 1;
		}
		else
		{
			psy = 0;
		}
		if ((time >= (self.delay + 0.3)))
		{
			self.delay = time;
		}
	}
	if (autocvar_evil_faces_psycho_effect)
	{
		if ((face_psycho > time))
		{
			psy = 1;
		}
		else if ((psy < 0))
		{
			psy = 0;
		}
	}
	if (autocvar_ghost_follower_psycho_effect)
	{
		if ((ghost_follower_psycho > time))
		{
			psy = 1;
		}
		else if ((psy < 0))
		{
			psy = 0;
		}
	}
	if ((psy >= 0))
	{
		BM_Psycho(psy);
	}
	if ((autocvar_taunt_sounds && (time >= (self.delay + 0.2))))
	{
		if ((self.check_bodycount_frequence < time))
		{
			check_bodycount();
		}
		self.delay = time;
	}
	if (((autocvar_mage_weapon && (self.weapon == IT_LIGHTNING)) && (self.health > 0)))
	{
		if (((self.animate_mage_weapon_frequence < time) && !self.button0))
		{
			animate_mage_weapon();
		}
	}
	else
	{
		if (((self.ishuman == 1) && (autocvar_weapon_position_fully_adjustable && !autocvar_weapon_position_right)))
		{
			if ((self.v_weapon_position_helper == 0))
			{
				self.v_weapon_position_helper = 1;
				v_weapon_position(self);
			}
			if (self.super_damage_finished)
			{
				if (autocvar_1st_person_extended_quad_effect)
				{
					if ((self.quad_v_weapon_position_helper == 0))
					{
						self.quad_v_weapon_position_helper = 1;
						add_Quake3_quad_effect_v_weapon_position(self);
					}
				}
			}
			else
			{
				self.quad_v_weapon_position_helper = 0;
			}
		}
		else
		{
			self.v_weapon_position_helper = 0;
		}
	}
	if ((((invisweapon == 1) && self.invisible_finished) && !autocvar_weapon_position_fully_adjustable))
	{
		add_transparent_weaponmodel(self);
	}
	if ((((autocvar_player_legs_visibility && !autocvar_chase_active) && !(deathmatch || coop)) && !self.invisible_finished))
	{
		if ((self.visible_legs_helper == 0))
		{
			self.visible_legs_helper = 1;
			player_legs(self);
		}
	}
	if (autocvar_earthquake_interval)
	{
		if ((self.earthquake_finished > time))
		{
			start_earthquake();
		}
		else
		{
			start_earthquake_think();
		}
	}
	if (view_zoom_out)
	{
		if ((self.viewzoom <= 1))
		{
			self.viewzoom = (self.viewzoom + 0.035);
		}
		else
		{
			view_zoom_out = 0;
			self.viewzoom = 1;
		}
	}
	if (((autocvar_weapon_range_crosshair && !autocvar_player_health_crosshair) && !autocvar_monster_health_crosshair))
	{
		if (autocvar_chase_active)
		{
			if ((autocvar_weapon_range_crosshair == 2))
			{
				update_weapon_range_crosshair();
			}
		}
		else
		{
			update_weapon_range_crosshair();
		}
	}
	if (((!autocvar_weapon_range_crosshair && autocvar_player_health_crosshair) && !autocvar_monster_health_crosshair))
	{
		update_player_health_crosshair();
	}
	if (((!autocvar_weapon_range_crosshair && !autocvar_player_health_crosshair) && autocvar_monster_health_crosshair))
	{
		update_monster_health_crosshair();
	}
	if ((self.waterlevel == 2))
	{
		CheckWaterJump();
	}
	if ((self.deadflag >= DEAD_DEAD))
	{
		PlayerDeathThink();
		return;
	}
	if ((self.deadflag == DEAD_DYING))
	{
		return;
	}
	if ((time < self.pausetime))
	{
		self.velocity = VEC_ORIGIN;
	}
	if (self.button2)
	{
		if ((self.flags & FL_ONGROUND))
		{
			self.flags = (self.flags | FL_JUMPRELEASED);	// hold jump = keep jumping
		}
		PlayerJump();
	}
	else
	{
		self.flags = (self.flags | FL_JUMPRELEASED);
	}
	if ((time < self.pausetime))
	{
		self.velocity = VEC_ORIGIN;
	}
	if (!autocvar_bm_reload && ((((time > self.attack_finished) && (self.currentammo == 0)) && (self.weapon != IT_AXE)) && (((self.weapon != IT_MEGAMAN) && (self.weapon != IT_BANANA)) && (self.weapon != IT_FUNGUN))))
	{
		self.weapon = W_BestWeapon();
		W_SetCurrentAmmo();
	}
	SemisolidPreThink();
	if (self.onladder)
	{
		self.onladder = 0;
		if (self.button2)
		{
			Ladder_ClimbJump();
			if ((self.health > 0))
			{
				self.gravity = 0.000000;
			}
		}
		else
		{
			self.flags = (self.flags | FL_JUMPRELEASED);
			self.velocity = (0.7 * self.velocity);
			self.velocity_z = 0;
			Ladder_ClimbMove();
			if ((self.health > 0))
			{
				self.gravity = 0.000000;
			}
		}
	}
	else
	{
		if (self.jp_on)
			self.gravity = JP_LOWGRAV;	// a lit jetpack hovers (jetpack.qc): 1 here, before the move, made every hover sink
		else if (self.spruce_swim_grav)
			self.gravity = 0.04;
		else
			self.gravity = 1;
	}
};

void() WetsuitTime =
{
	if (self.wetsuit_finished)
	{
		self.air_finished = (time + 12);
		if ((self.wetsuit_finished < (time + 3)))
		{
			if ((self.wetsuit_time == 1))
			{
				sprint(self, "Air supply in Wetsuit is running out\n");
				stuffcmd(self, "bf\n");
				sound(self, CHAN_AUTO, "items/suit2.wav", 1, ATTN_NORM);
				self.wetsuit_time = (time + 1);
			}
			if ((self.wetsuit_time < time))
			{
				self.wetsuit_time = (time + 1);
				stuffcmd(self, "bf\n");
			}
		}
		if ((self.wetsuit_finished < time))
		{
			self.items = (self.items - IT_SUIT);
			self.wetsuit_time = 0;
			self.wetsuit_finished = 0;
		}
	}
};

// powerupcountdown 1: each number's window is 0.2 s wide, so it used to be centerprinted every frame of it
void(string s) BM_CountdownPrint =
{
	if (((s == self.bm_cd_last) && (time < self.bm_cd_t)))
	{
		return;
	}
	self.bm_cd_last = s;
	self.bm_cd_t = time + 0.5;
	centerprint(self, s);
};

void() CheckPowerups =
{
	if ((self.health <= 0))
	{
		return;
	}
	if (self.invisible_finished)
	{
		if ((self.invisible_sound < time))
		{
			sound(self, CHAN_AUTO, "items/inv3.wav", 0.5, ATTN_IDLE);
			self.invisible_sound = (time + ((random() * 3) + 1));
		}
		if ((self.invisible_finished < (time + 3)))
		{
			if ((self.invisible_time == 1))
			{
				sprint(self, "Ring of Shadows magic is fading\n");
				stuffcmd(self, "bf\n");
				sound(self, CHAN_AUTO, "items/inv2.wav", 1, ATTN_NORM);
				self.invisible_time = (time + 1);
			}
			if ((self.invisible_time < time))
			{
				self.invisible_time = (time + 1);
				stuffcmd(self, "bf\n");
			}
		}
		if ((self.invisible_finished < time))
		{
			self.items = (self.items - IT_INVISIBILITY);
			self.invisible_finished = 0;
			self.invisible_time = 0;
		}
		if ((autocvar_powerupcountdown == 2))
		{
			if (((self.invisible_finished < (time + self.invisible_counter)) && (self.invisible_counter > 3)))
			{
				self.invisible_counter = (self.invisible_counter - 1);
				sprint(self, ftos(self.invisible_counter));
				sprint(self, "\n");
			}
		}
		else
		{
			if (((autocvar_powerupcountdown == 0) && (self.invisible_finished < (time + self.invisible_counter))))
			{
				self.invisible_counter = (self.invisible_counter - 1);
			}
		}
		if ((autocvar_powerupcountdown == 1))
		{
			if (((self.invisible_finished <= (time + 29.1)) && (self.invisible_finished >= (time + 28.9))))
			{
				BM_CountdownPrint("29");
			}
			if (((self.invisible_finished <= (time + 28.1)) && (self.invisible_finished >= (time + 27.9))))
			{
				BM_CountdownPrint("28");
			}
			if (((self.invisible_finished <= (time + 27.1)) && (self.invisible_finished >= (time + 26.9))))
			{
				BM_CountdownPrint("27");
			}
			if (((self.invisible_finished <= (time + 26.1)) && (self.invisible_finished >= (time + 25.9))))
			{
				BM_CountdownPrint("26");
			}
			if (((self.invisible_finished <= (time + 25.1)) && (self.invisible_finished >= (time + 24.9))))
			{
				BM_CountdownPrint("25");
			}
			if (((self.invisible_finished <= (time + 24.1)) && (self.invisible_finished >= (time + 23.9))))
			{
				BM_CountdownPrint("24");
			}
			if (((self.invisible_finished <= (time + 23.1)) && (self.invisible_finished >= (time + 22.9))))
			{
				BM_CountdownPrint("23");
			}
			if (((self.invisible_finished <= (time + 22.1)) && (self.invisible_finished >= (time + 21.9))))
			{
				BM_CountdownPrint("22");
			}
			if (((self.invisible_finished <= (time + 21.1)) && (self.invisible_finished >= (time + 20.9))))
			{
				BM_CountdownPrint("21");
			}
			if (((self.invisible_finished <= (time + 20.1)) && (self.invisible_finished >= (time + 19.9))))
			{
				BM_CountdownPrint("20");
			}
			if (((self.invisible_finished <= (time + 19.1)) && (self.invisible_finished >= (time + 18.9))))
			{
				BM_CountdownPrint("19");
			}
			if (((self.invisible_finished <= (time + 18.1)) && (self.invisible_finished >= (time + 17.9))))
			{
				BM_CountdownPrint("18");
			}
			if (((self.invisible_finished <= (time + 17.1)) && (self.invisible_finished >= (time + 16.9))))
			{
				BM_CountdownPrint("17");
			}
			if (((self.invisible_finished <= (time + 16.1)) && (self.invisible_finished >= (time + 15.9))))
			{
				BM_CountdownPrint("16");
			}
			if (((self.invisible_finished <= (time + 15.1)) && (self.invisible_finished >= (time + 14.9))))
			{
				BM_CountdownPrint("15");
			}
			if (((self.invisible_finished <= (time + 14.1)) && (self.invisible_finished >= (time + 13.9))))
			{
				BM_CountdownPrint("14");
			}
			if (((self.invisible_finished <= (time + 13.1)) && (self.invisible_finished >= (time + 12.9))))
			{
				BM_CountdownPrint("13");
			}
			if (((self.invisible_finished <= (time + 12.1)) && (self.invisible_finished >= (time + 11.9))))
			{
				BM_CountdownPrint("12");
			}
			if (((self.invisible_finished <= (time + 11.1)) && (self.invisible_finished >= (time + 10.9))))
			{
				BM_CountdownPrint("11");
			}
			if (((self.invisible_finished <= (time + 10.1)) && (self.invisible_finished >= (time + 9.9))))
			{
				BM_CountdownPrint("10");
			}
			if (((self.invisible_finished <= (time + 9.1)) && (self.invisible_finished >= (time + 8.9))))
			{
				BM_CountdownPrint("9");
			}
			if (((self.invisible_finished <= (time + 8.1)) && (self.invisible_finished >= (time + 7.9))))
			{
				BM_CountdownPrint("8");
			}
			if (((self.invisible_finished <= (time + 7.1)) && (self.invisible_finished >= (time + 6.9))))
			{
				BM_CountdownPrint("7");
			}
			if (((self.invisible_finished <= (time + 6.1)) && (self.invisible_finished >= (time + 5.9))))
			{
				BM_CountdownPrint("6");
			}
			if (((self.invisible_finished <= (time + 5.1)) && (self.invisible_finished >= (time + 4.9))))
			{
				BM_CountdownPrint("5");
			}
			if (((self.invisible_finished <= (time + 4.1)) && (self.invisible_finished >= (time + 3.9))))
			{
				BM_CountdownPrint("4");
			}
			if (((self.invisible_finished <= (time + 3.1)) && (self.invisible_finished >= (time + 2.9))))
			{
				BM_CountdownPrint("3");
			}
			if (((self.invisible_finished <= (time + 2.1)) && (self.invisible_finished >= (time + 1.9))))
			{
				BM_CountdownPrint("2");
			}
			if (((self.invisible_finished <= (time + 1.1)) && (self.invisible_finished >= (time + 0.9))))
			{
				BM_CountdownPrint("1");
			}
			if (((self.invisible_finished <= (time + 0.3)) && (self.invisible_finished >= (time + 0.1))))
			{
				BM_CountdownPrint("QQQ powerup died QQQ");
			}
		}
		if ((autocvar_3rd_person_extended_ring_effect && cvar("chase_active")))
		{
			self.alpha = autocvar_3rd_person_extended_ring_effect;
		}
		else
		{
			self.frame = 0;
			self.modelindex = modelindex_eyes;
		}
	}
	else if (self.fd_head || self.fd_fade)
	{
		// flying the Rob Dob: the body is in the ring of invisibility state (just a pair of eyes), so turning the camera
		// round never shows half a person standing there
		self.frame = 0;
		self.modelindex = modelindex_eyes;
		self.alpha = 1;
	}
	else if (!CL_InVehicleHidden(self))	// a vehicle keeps its own hide (alpha 0.01 + EF_NODRAW)
	{
		if (!autocvar_3rd_person_visible_weapons)
		{
			self.modelindex = modelindex_player;
		}
		self.alpha = 1;
	}
	if (self.invincible_finished)
	{
		self.poisoned = 0;
		if (self.inflamed)	// BM: only when there is a burning loop to cut. Was sent every server frame for the whole powerup (a sound packet per frame to everyone)
		{
			sound(self, 120, "misc/null.wav", 1, ATTN_NORM);
		}
		self.inflamed = 0;
		if ((self.has_fired == 1))
		{
			autocvar_berserkmode = 3.5;
		}
		if ((self.invincible_finished < (time + 3)))
		{
			if ((self.invincible_time == 1))
			{
				sprint(self, "Protection is almost burned out\n");
				stuffcmd(self, "bf\n");
				sound(self, CHAN_AUTO, "items/protect2.wav", 1, ATTN_NORM);
				self.invincible_time = (time + 1);
			}
			if ((self.invincible_time < time))
			{
				self.invincible_time = (time + 1);
				stuffcmd(self, "bf\n");
			}
		}
		if ((self.invincible_finished < time))
		{
			self.items = (self.items - IT_INVULNERABILITY);
			self.invincible_time = 0;
			self.invincible_finished = 0;
			self.has_fired = 0;
		}
		if ((self.invincible_finished > time))
		{
			self.effects = (self.effects | EF_DIMLIGHT);
		}
		else
		{
			self.effects = (self.effects - (self.effects & EF_DIMLIGHT));
		}
		if ((autocvar_powerupcountdown == 2))
		{
			if (((self.invincible_finished < (time + self.invincible_counter)) && (self.invincible_counter > 3)))
			{
				self.invincible_counter = (self.invincible_counter - 1);
				sprint(self, ftos(self.invincible_counter));
				sprint(self, "\n");
			}
		}
		else
		{
			if (((autocvar_powerupcountdown == 0) && (self.invincible_finished < (time + self.invincible_counter))))
			{
				self.invincible_counter = (self.invincible_counter - 1);
			}
		}
		if ((autocvar_powerupcountdown == 1))
		{
			if (((self.invincible_finished <= (time + 29.1)) && (self.invincible_finished >= (time + 28.9))))
			{
				BM_CountdownPrint("29");
			}
			if (((self.invincible_finished <= (time + 28.1)) && (self.invincible_finished >= (time + 27.9))))
			{
				BM_CountdownPrint("28");
			}
			if (((self.invincible_finished <= (time + 27.1)) && (self.invincible_finished >= (time + 26.9))))
			{
				BM_CountdownPrint("27");
			}
			if (((self.invincible_finished <= (time + 26.1)) && (self.invincible_finished >= (time + 25.9))))
			{
				BM_CountdownPrint("26");
			}
			if (((self.invincible_finished <= (time + 25.1)) && (self.invincible_finished >= (time + 24.9))))
			{
				BM_CountdownPrint("25");
			}
			if (((self.invincible_finished <= (time + 24.1)) && (self.invincible_finished >= (time + 23.9))))
			{
				BM_CountdownPrint("24");
			}
			if (((self.invincible_finished <= (time + 23.1)) && (self.invincible_finished >= (time + 22.9))))
			{
				BM_CountdownPrint("23");
			}
			if (((self.invincible_finished <= (time + 22.1)) && (self.invincible_finished >= (time + 21.9))))
			{
				BM_CountdownPrint("22");
			}
			if (((self.invincible_finished <= (time + 21.1)) && (self.invincible_finished >= (time + 20.9))))
			{
				BM_CountdownPrint("21");
			}
			if (((self.invincible_finished <= (time + 20.1)) && (self.invincible_finished >= (time + 19.9))))
			{
				BM_CountdownPrint("20");
			}
			if (((self.invincible_finished <= (time + 19.1)) && (self.invincible_finished >= (time + 18.9))))
			{
				BM_CountdownPrint("19");
			}
			if (((self.invincible_finished <= (time + 18.1)) && (self.invincible_finished >= (time + 17.9))))
			{
				BM_CountdownPrint("18");
			}
			if (((self.invincible_finished <= (time + 17.1)) && (self.invincible_finished >= (time + 16.9))))
			{
				BM_CountdownPrint("17");
			}
			if (((self.invincible_finished <= (time + 16.1)) && (self.invincible_finished >= (time + 15.9))))
			{
				BM_CountdownPrint("16");
			}
			if (((self.invincible_finished <= (time + 15.1)) && (self.invincible_finished >= (time + 14.9))))
			{
				BM_CountdownPrint("15");
			}
			if (((self.invincible_finished <= (time + 14.1)) && (self.invincible_finished >= (time + 13.9))))
			{
				BM_CountdownPrint("14");
			}
			if (((self.invincible_finished <= (time + 13.1)) && (self.invincible_finished >= (time + 12.9))))
			{
				BM_CountdownPrint("13");
			}
			if (((self.invincible_finished <= (time + 12.1)) && (self.invincible_finished >= (time + 11.9))))
			{
				BM_CountdownPrint("12");
			}
			if (((self.invincible_finished <= (time + 11.1)) && (self.invincible_finished >= (time + 10.9))))
			{
				BM_CountdownPrint("11");
			}
			if (((self.invincible_finished <= (time + 10.1)) && (self.invincible_finished >= (time + 9.9))))
			{
				BM_CountdownPrint("10");
			}
			if (((self.invincible_finished <= (time + 9.1)) && (self.invincible_finished >= (time + 8.9))))
			{
				BM_CountdownPrint("9");
			}
			if (((self.invincible_finished <= (time + 8.1)) && (self.invincible_finished >= (time + 7.9))))
			{
				BM_CountdownPrint("8");
			}
			if (((self.invincible_finished <= (time + 7.1)) && (self.invincible_finished >= (time + 6.9))))
			{
				BM_CountdownPrint("7");
			}
			if (((self.invincible_finished <= (time + 6.1)) && (self.invincible_finished >= (time + 5.9))))
			{
				BM_CountdownPrint("6");
			}
			if (((self.invincible_finished <= (time + 5.1)) && (self.invincible_finished >= (time + 4.9))))
			{
				BM_CountdownPrint("5");
			}
			if (((self.invincible_finished <= (time + 4.1)) && (self.invincible_finished >= (time + 3.9))))
			{
				BM_CountdownPrint("4");
			}
			if (((self.invincible_finished <= (time + 3.1)) && (self.invincible_finished >= (time + 2.9))))
			{
				BM_CountdownPrint("3");
			}
			if (((self.invincible_finished <= (time + 2.1)) && (self.invincible_finished >= (time + 1.9))))
			{
				BM_CountdownPrint("2");
			}
			if (((self.invincible_finished <= (time + 1.1)) && (self.invincible_finished >= (time + 0.9))))
			{
				BM_CountdownPrint("1");
			}
			if (((self.invincible_finished <= (time + 0.3)) && (self.invincible_finished >= (time + 0.1))))
			{
				BM_CountdownPrint("QQQ powerup died QQQ");
			}
		}
	}
	if (self.super_damage_finished)
	{
		if ((self.super_damage_finished < (time + 3)))
		{
			if ((self.super_time == 1))
			{
				sprint(self, "Quad Damage is wearing off\n");
				stuffcmd(self, "bf\n");
				sound(self, CHAN_AUTO, "items/damage2.wav", 1, ATTN_NORM);
				self.super_time = (time + 1);
			}
			if ((self.super_time < time))
			{
				self.super_time = (time + 1);
				stuffcmd(self, "bf\n");
			}
		}
		if ((self.super_damage_finished < time))
		{
			self.items = (self.items - IT_QUAD);
			self.super_damage_finished = 0;
			self.super_time = 0;
		}
		if ((self.super_damage_finished > time))
		{
			self.effects = (self.effects | EF_DIMLIGHT);
		}
		else
		{
			self.effects = (self.effects - (self.effects & EF_DIMLIGHT));
		}
		if ((autocvar_powerupcountdown == 2))
		{
			if (((self.super_damage_finished < (time + self.super_damage_counter)) && (self.super_damage_counter > 3)))
			{
				self.super_damage_counter = (self.super_damage_counter - 1);
				sprint(self, ftos(self.super_damage_counter));
				sprint(self, "\n");
			}
		}
		else
		{
			if (((autocvar_powerupcountdown == 0) && (self.super_damage_finished < (time + self.super_damage_counter))))
			{
				self.super_damage_counter = (self.super_damage_counter - 1);
			}
		}
		if ((autocvar_powerupcountdown == 1))
		{
			if (((self.super_damage_finished <= (time + 29.1)) && (self.super_damage_finished >= (time + 28.9))))
			{
				BM_CountdownPrint("29");
			}
			if (((self.super_damage_finished <= (time + 28.1)) && (self.super_damage_finished >= (time + 27.9))))
			{
				BM_CountdownPrint("28");
			}
			if (((self.super_damage_finished <= (time + 27.1)) && (self.super_damage_finished >= (time + 26.9))))
			{
				BM_CountdownPrint("27");
			}
			if (((self.super_damage_finished <= (time + 26.1)) && (self.super_damage_finished >= (time + 25.9))))
			{
				BM_CountdownPrint("26");
			}
			if (((self.super_damage_finished <= (time + 25.1)) && (self.super_damage_finished >= (time + 24.9))))
			{
				BM_CountdownPrint("25");
			}
			if (((self.super_damage_finished <= (time + 24.1)) && (self.super_damage_finished >= (time + 23.9))))
			{
				BM_CountdownPrint("24");
			}
			if (((self.super_damage_finished <= (time + 23.1)) && (self.super_damage_finished >= (time + 22.9))))
			{
				BM_CountdownPrint("23");
			}
			if (((self.super_damage_finished <= (time + 22.1)) && (self.super_damage_finished >= (time + 21.9))))
			{
				BM_CountdownPrint("22");
			}
			if (((self.super_damage_finished <= (time + 21.1)) && (self.super_damage_finished >= (time + 20.9))))
			{
				BM_CountdownPrint("21");
			}
			if (((self.super_damage_finished <= (time + 20.1)) && (self.super_damage_finished >= (time + 19.9))))
			{
				BM_CountdownPrint("20");
			}
			if (((self.super_damage_finished <= (time + 19.1)) && (self.super_damage_finished >= (time + 18.9))))
			{
				BM_CountdownPrint("19");
			}
			if (((self.super_damage_finished <= (time + 18.1)) && (self.super_damage_finished >= (time + 17.9))))
			{
				BM_CountdownPrint("18");
			}
			if (((self.super_damage_finished <= (time + 17.1)) && (self.super_damage_finished >= (time + 16.9))))
			{
				BM_CountdownPrint("17");
			}
			if (((self.super_damage_finished <= (time + 16.1)) && (self.super_damage_finished >= (time + 15.9))))
			{
				BM_CountdownPrint("16");
			}
			if (((self.super_damage_finished <= (time + 15.1)) && (self.super_damage_finished >= (time + 14.9))))
			{
				BM_CountdownPrint("15");
			}
			if (((self.super_damage_finished <= (time + 14.1)) && (self.super_damage_finished >= (time + 13.9))))
			{
				BM_CountdownPrint("14");
			}
			if (((self.super_damage_finished <= (time + 13.1)) && (self.super_damage_finished >= (time + 12.9))))
			{
				BM_CountdownPrint("13");
			}
			if (((self.super_damage_finished <= (time + 12.1)) && (self.super_damage_finished >= (time + 11.9))))
			{
				BM_CountdownPrint("12");
			}
			if (((self.super_damage_finished <= (time + 11.1)) && (self.super_damage_finished >= (time + 10.9))))
			{
				BM_CountdownPrint("11");
			}
			if (((self.super_damage_finished <= (time + 10.1)) && (self.super_damage_finished >= (time + 9.9))))
			{
				BM_CountdownPrint("10");
			}
			if (((self.super_damage_finished <= (time + 9.1)) && (self.super_damage_finished >= (time + 8.9))))
			{
				BM_CountdownPrint("9");
			}
			if (((self.super_damage_finished <= (time + 8.1)) && (self.super_damage_finished >= (time + 7.9))))
			{
				BM_CountdownPrint("8");
			}
			if (((self.super_damage_finished <= (time + 7.1)) && (self.super_damage_finished >= (time + 6.9))))
			{
				BM_CountdownPrint("7");
			}
			if (((self.super_damage_finished <= (time + 6.1)) && (self.super_damage_finished >= (time + 5.9))))
			{
				BM_CountdownPrint("6");
			}
			if (((self.super_damage_finished <= (time + 5.1)) && (self.super_damage_finished >= (time + 4.9))))
			{
				BM_CountdownPrint("5");
			}
			if (((self.super_damage_finished <= (time + 4.1)) && (self.super_damage_finished >= (time + 3.9))))
			{
				BM_CountdownPrint("4");
			}
			if (((self.super_damage_finished <= (time + 3.1)) && (self.super_damage_finished >= (time + 2.9))))
			{
				BM_CountdownPrint("3");
			}
			if (((self.super_damage_finished <= (time + 2.1)) && (self.super_damage_finished >= (time + 1.9))))
			{
				BM_CountdownPrint("2");
			}
			if (((self.super_damage_finished <= (time + 1.1)) && (self.super_damage_finished >= (time + 0.9))))
			{
				BM_CountdownPrint("1");
			}
			if (((self.super_damage_finished <= (time + 0.3)) && (self.super_damage_finished >= (time + 0.1))))
			{
				BM_CountdownPrint("QQQ powerup died QQQ");
			}
		}
	}
	if (self.radsuit_finished)
	{
		self.air_finished = (time + 12);
		self.poisoned = 0;
		if (self.inflamed)	// BM: only when there is a burning loop to cut. Was sent every server frame for the whole powerup (a sound packet per frame to everyone)
		{
			sound(self, 120, "misc/null.wav", 1, ATTN_NORM);
		}
		self.inflamed = 0;
		if ((self.radsuit_finished < (time + 3)))
		{
			if ((self.rad_time == 1))
			{
				sprint(self, "Air supply in Biosuit expiring\n");
				stuffcmd(self, "bf\n");
				sound(self, CHAN_AUTO, "items/suit2.wav", 1, ATTN_NORM);
				self.rad_time = (time + 1);
			}
			if ((self.rad_time < time))
			{
				self.rad_time = (time + 1);
				stuffcmd(self, "bf\n");
			}
		}
		if ((self.radsuit_finished < time))
		{
			self.items = (self.items - IT_SUIT);
			self.rad_time = 0;
			self.radsuit_finished = 0;
		}
		if ((autocvar_powerupcountdown == 2))
		{
			if (((self.radsuit_finished < (time + self.radsuit_counter)) && (self.radsuit_counter > 3)))
			{
				self.radsuit_counter = (self.radsuit_counter - 1);
				sprint(self, ftos(self.radsuit_counter));
				sprint(self, "\n");
			}
		}
		else
		{
			if (((autocvar_powerupcountdown == 0) && (self.radsuit_finished < (time + self.radsuit_counter))))
			{
				self.radsuit_counter = (self.radsuit_counter - 1);
			}
		}
		if ((autocvar_powerupcountdown == 1))
		{
			if (((self.radsuit_finished <= (time + 29.1)) && (self.radsuit_finished >= (time + 28.9))))
			{
				BM_CountdownPrint("29");
			}
			if (((self.radsuit_finished <= (time + 28.1)) && (self.radsuit_finished >= (time + 27.9))))
			{
				BM_CountdownPrint("28");
			}
			if (((self.radsuit_finished <= (time + 27.1)) && (self.radsuit_finished >= (time + 26.9))))
			{
				BM_CountdownPrint("27");
			}
			if (((self.radsuit_finished <= (time + 26.1)) && (self.radsuit_finished >= (time + 25.9))))
			{
				BM_CountdownPrint("26");
			}
			if (((self.radsuit_finished <= (time + 25.1)) && (self.radsuit_finished >= (time + 24.9))))
			{
				BM_CountdownPrint("25");
			}
			if (((self.radsuit_finished <= (time + 24.1)) && (self.radsuit_finished >= (time + 23.9))))
			{
				BM_CountdownPrint("24");
			}
			if (((self.radsuit_finished <= (time + 23.1)) && (self.radsuit_finished >= (time + 22.9))))
			{
				BM_CountdownPrint("23");
			}
			if (((self.radsuit_finished <= (time + 22.1)) && (self.radsuit_finished >= (time + 21.9))))
			{
				BM_CountdownPrint("22");
			}
			if (((self.radsuit_finished <= (time + 21.1)) && (self.radsuit_finished >= (time + 20.9))))
			{
				BM_CountdownPrint("21");
			}
			if (((self.radsuit_finished <= (time + 20.1)) && (self.radsuit_finished >= (time + 19.9))))
			{
				BM_CountdownPrint("20");
			}
			if (((self.radsuit_finished <= (time + 19.1)) && (self.radsuit_finished >= (time + 18.9))))
			{
				BM_CountdownPrint("19");
			}
			if (((self.radsuit_finished <= (time + 18.1)) && (self.radsuit_finished >= (time + 17.9))))
			{
				BM_CountdownPrint("18");
			}
			if (((self.radsuit_finished <= (time + 17.1)) && (self.radsuit_finished >= (time + 16.9))))
			{
				BM_CountdownPrint("17");
			}
			if (((self.radsuit_finished <= (time + 16.1)) && (self.radsuit_finished >= (time + 15.9))))
			{
				BM_CountdownPrint("16");
			}
			if (((self.radsuit_finished <= (time + 15.1)) && (self.radsuit_finished >= (time + 14.9))))
			{
				BM_CountdownPrint("15");
			}
			if (((self.radsuit_finished <= (time + 14.1)) && (self.radsuit_finished >= (time + 13.9))))
			{
				BM_CountdownPrint("14");
			}
			if (((self.radsuit_finished <= (time + 13.1)) && (self.radsuit_finished >= (time + 12.9))))
			{
				BM_CountdownPrint("13");
			}
			if (((self.radsuit_finished <= (time + 12.1)) && (self.radsuit_finished >= (time + 11.9))))
			{
				BM_CountdownPrint("12");
			}
			if (((self.radsuit_finished <= (time + 11.1)) && (self.radsuit_finished >= (time + 10.9))))
			{
				BM_CountdownPrint("11");
			}
			if (((self.radsuit_finished <= (time + 10.1)) && (self.radsuit_finished >= (time + 9.9))))
			{
				BM_CountdownPrint("10");
			}
			if (((self.radsuit_finished <= (time + 9.1)) && (self.radsuit_finished >= (time + 8.9))))
			{
				BM_CountdownPrint("9");
			}
			if (((self.radsuit_finished <= (time + 8.1)) && (self.radsuit_finished >= (time + 7.9))))
			{
				BM_CountdownPrint("8");
			}
			if (((self.radsuit_finished <= (time + 7.1)) && (self.radsuit_finished >= (time + 6.9))))
			{
				BM_CountdownPrint("7");
			}
			if (((self.radsuit_finished <= (time + 6.1)) && (self.radsuit_finished >= (time + 5.9))))
			{
				BM_CountdownPrint("6");
			}
			if (((self.radsuit_finished <= (time + 5.1)) && (self.radsuit_finished >= (time + 4.9))))
			{
				BM_CountdownPrint("5");
			}
			if (((self.radsuit_finished <= (time + 4.1)) && (self.radsuit_finished >= (time + 3.9))))
			{
				BM_CountdownPrint("4");
			}
			if (((self.radsuit_finished <= (time + 3.1)) && (self.radsuit_finished >= (time + 2.9))))
			{
				BM_CountdownPrint("3");
			}
			if (((self.radsuit_finished <= (time + 2.1)) && (self.radsuit_finished >= (time + 1.9))))
			{
				BM_CountdownPrint("2");
			}
			if (((self.radsuit_finished <= (time + 1.1)) && (self.radsuit_finished >= (time + 0.9))))
			{
				BM_CountdownPrint("1");
			}
			if (((self.radsuit_finished <= (time + 0.3)) && (self.radsuit_finished >= (time + 0.1))))
			{
				BM_CountdownPrint("QQQ powerup died QQQ");
			}
		}
		WetsuitTime();
	}
};

void() PlayerPostThink =
{
	local float rg_dt, rg_n;

	if (self.bm_obs)
		return;

	rg_dt = time - self.rg_last_t;
	self.rg_last_t = time;
	if (rg_dt > 0.2)
		rg_dt = 0.2;
	if (((self.health > 0) && (self.health < self.max_health) && !self.deadflag && (time > (self.rg_hurt_t + Underdog_RegenDelay()))))
	{
		self.rg_frac = (self.rg_frac + (Underdog_RegenRate() * rg_dt));
		if ((self.rg_frac >= 1))
		{
			rg_n = floor(self.rg_frac);
			self.rg_frac = (self.rg_frac - rg_n);
			self.health = self.health + rg_n;
			if ((self.health > self.max_health))
			{
				self.health = self.max_health;
			}
		}
	}
	else
	{
		self.rg_frac = 0;
	}
	Underdog_ArmorRegen(rg_dt);
	Underdog_UpdateBounty();
	if (BotPostFrame())
	{
		return;
	}
	SemisolidPostThink();
	if ((self.wetsuit_finished > time))
	{
		if ((self.waterlevel == 2))
		{
			self.velocity = (self.velocity * 0.8);
		}
		if ((self.waterlevel == 3))
		{
			self.velocity = (self.velocity * 0.66);
		}
	}
	if ((self.view_ofs == VEC_ORIGIN))
	{
		return;
	}
	if (self.deadflag)
	{
		return;
	}
	W_WeaponFrame();
	if ((((self.jump_flag < -300) && (self.flags & FL_ONGROUND)) && (self.health > 0)))
	{
		if ((self.watertype == CONTENT_WATER))
		{
			sound(self, CHAN_BODY, "player/h2ojump.wav", 1, ATTN_NORM);
		}
		else
		{
			if ((self.jump_flag < -650))
			{
				if ((time < self.skypad_safe_t))
				{
					self.skypad_safe_t = 0;
					SkyPad_LandWave();
					sound7(self, CHAN_VOICE, "player/land.wav", 1, ATTN_NORM, SNDSPD);
				}
				else
				{
					if (autocvar_bm_falldamage)
					{
						T_Damage(self, world, world, 5);
					}
					sound7(self, CHAN_VOICE, "player/land2.wav", 1, ATTN_NORM, SNDSPD);
					self.deathtype = "falling";
				}
			}
			else
			{
				sound7(self, CHAN_VOICE, "player/land.wav", 1, ATTN_NORM, SNDSPD);
			}
		}
		self.jump_flag = 0;
	}
	if (!(self.flags & FL_ONGROUND))
	{
		self.jump_flag = self.velocity_z;
	}
	CheckPowerups();
};

void() ClientConnect =
{
	self.bm_fx_sent = FALSE;
	self.bm_dm_gun_alt = 0;
	self.skypad_safe_t = 0;
	self.skypad_cool_t = 0;
	self.skypad_vel_sent = FALSE;
	ClientInRankings();
	// an observer stays one across map changes: parm11 is set by SetChangeParms (the engine loads
	// this client's spawn parms before ClientConnect); PutClientInServer then runs BM_ObsActivate
	if (parm11 == 1 && cvar_string("bm_obs_key") != "")
		self.bm_obs = 1;
	if (self.bm_obs)
	{
		self.ishuman = 3;
		return;
	}
	if (cvar("sv_autodemo_perclient_discardable") > 0)
		self.discardabledemo = 1;
	bprint(self.netname);
	bprint(" entered the game\n");
	if (intermission_running && !deathmatch)	// a friend joining during the scoreboard must not skip it for everybody
	{
		ExitIntermission();
	}
};

void() ClientDisconnect =
{
	if (self.bm_obs)
	{
		ClientDisconnected();
		self.bm_obs = 0;
		self.classname = "";
		self.health = 0;
		self.takedamage = DAMAGE_NO;
		self.solid = SOLID_NOT;
		self.movetype = MOVETYPE_NONE;
		self.modelindex = 0;
		return;
	}
	ClientDisconnected();
	Veh_ClientGone();	// a driver who drops leaves the van parked (vehicle_drive.qc)
	JohnBird_ClientGone();	// a flying Winged John pilot who drops leaves him perched (john_bird.qc)
	EricCannon_ClientGone();	// a rider who drops leaves Eric Deason Cannon reset (eric_cannon.qc)
	MMTank_ClientGone();	// a driver who drops leaves Mega Man Tank parked (mm_tank.qc)
	Underdog_ClearFx(self);		// the leader's glow / beacon / x-ray would stay behind
	Underdog_Reset(self);		// bots reuse their slot: the next one must not inherit this streak
	FD_Reset(self);				// a Rob Dob pilot's head would hum on, orphaned
	BM_ClientGone(self);		// NetSend PCs, armed pickles, Mega Men: they must not shoot on in an empty (or reused) slot's name
	BM_Radar_ClientGone(self);
	if (self.bm_aura)
	{
		if (!bm_wasfreed(self.bm_aura) && self.bm_aura.classname == "bm_aura" && self.bm_aura.owner == self)
			remove(self.bm_aura);
		self.bm_aura = world;
	}
	self.v_weapon_position_helper = 0;		// his viewmodel entities remove themselves; a newcomer in the slot spawns fresh ones
	self.quad_v_weapon_position_helper = 0;
	self.ctf_color_side = 0;		// CTF: the next client in this slot gets his team colours stuffed again
	self.classname = "";		// a leaver's body must not stay in every find(world, classname, "player") loop: frags, leader, player count
	self.health = 0;
	self.takedamage = DAMAGE_NO;	// nor be a body that can be shot, or homed on, until the slot is reused
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.modelindex = 0;
	if ((autocvar_player_changes_shirt_color_according_to_used_armor && !deathmatch))
	{
		stuffcmd(self, "topcolor 2\n");
	}
	if (autocvar_chasecam_death_view)
	{
		stuffcmd(self, "chase_active 0\n");
		stuffcmd(self, "chase_back 65\n");
		stuffcmd(self, "chase_up 10\n");
		stuffcmd(self, "chase_overhead 0\n");
	}
	if (((autocvar_weapon_range_crosshair || autocvar_player_health_crosshair) || autocvar_monster_health_crosshair))
	{
		stuffcmd(self, "crosshair_color_red 1\n");
		stuffcmd(self, "crosshair_color_green 0\n");
		stuffcmd(self, "crosshair_color_blue 0\n");
	}
	if (CTF_ENABLED)
	{
		if ((self.side == BLUE))
		{
			BLUE_PLAYERS = BLUE_PLAYERS + -1;
		}
		else
		{
			RED_PLAYERS = RED_PLAYERS + -1;
		}
	}
	if (gameover)
	{
		return;
	}
	bprint(self.netname);
	bprint(" left the game with ");
	bprint(ftos(self.frags));
	bprint(" frags\n");
	sound(self, CHAN_BODY, "player/tornoff2.wav", 1, ATTN_NONE);
	set_suicide_frame();
};

void(entity targ, entity attacker) ClientObituary =
{
	local float rnum;
	local string deathstring;
	local string deathstring2;

	rnum = random();
	if ((targ.classname == "player"))
	{
		if ((attacker.classname == "teledeath"))
		{
			bprint(targ.netname);
			bprint(" was telefragged by ");
			bprint(attacker.owner.netname);
			bprint("\n");
			attacker.owner.frags = (attacker.owner.frags + 1);
			return;
		}
		if ((attacker.classname == "teledeath2"))
		{
			bprint("Satan's power deflects ");
			bprint(targ.netname);
			bprint("'s telefrag\n");
			return;
		}
		if ((attacker.classname == "player"))
		{
			if ((deathmatch && (attacker.ishuman == 1) && (targ != attacker)))
			{
				if ((attacker.weapon == IT_AXE))
					centerprint(attacker, strcat("^1Humiliated ^7", targ.netname));
				else
					centerprint(attacker, strcat("^2Fragged ^7", targ.netname));
			}
			if (veh_runover)
			{
				bprint(targ.netname);
				bprint(" was run over by ");
				bprint(attacker.netname);
				bprint("'s van\n");
				if (deathmatch && (targ != attacker))
				{
					attacker.frags = (attacker.frags + 1);		// the run-over branch returned before the frag was counted
				}
				return;
			}
			if ((targ == attacker))
			{
				bprint(targ.netname);
				if (((targ.weapon == 64) && (targ.waterlevel > 1)))
				{
					bprint(" discharges into the water.\n");
					return;
				}
				if (mm_inflicting)
				{
					bprint(" got run over by their own Mega Man\n");
					return;
				}
				if (bn_inflicting)
				{
					bprint(" slipped on their own banana\n");
					return;
				}
				if (sg_inflicting)
				{
					bprint(" was mown down by their own sentry gun\n");
					return;
				}
				if (veh_inflicting)
				{
					bprint(" stood too close to a burning vehicle\n");
					return;
				}
				if (ec_inflicting)
				{
					bprint(" blasted sky-high inside THE ERIC DEASON CANNON and exploded into PC parts!\n");
					return;
				}
				if (mmt_inflicting)
				{
					bprint(" went down in a flaming Mega Man Tank explosion\n");
					return;
				}
				if ((fg_inflicting == FG_PICKLE))
				{
					bprint(" surprised themself\n");
					return;
				}
				if ((fg_inflicting == FG_DOB))
				{
					bprint(" blew their own head off\n");
					return;
				}
				if ((fg_inflicting == FG_DOOKIE))
				{
					bprint(" blew themself into a mud puddle\n");
					return;
				}
				if ((targ.weapon == IT_GRENADE_LAUNCHER))
				{
					bprint(" drowned in their own JohnWave\n");
				}
				else
				{
					bprint(" becomes bored with life\n");
				}
				return;
			}
			else
			{
				if ((((teamplay == 2) && (targ.team > 0)) && (targ.team == attacker.team)))
				{
					if ((rnum < 0.25))
					{
						deathstring = " mows down a teammate\n";
					}
					else
					{
						if ((rnum < 0.5))
						{
							deathstring = " checks his glasses\n";
						}
						else
						{
							if ((rnum < 0.75))
							{
								deathstring = " gets a frag for the other team\n";
							}
							else
							{
								deathstring = " loses another friend\n";
							}
						}
					}
					bprint(attacker.netname);
					bprint(deathstring);
					attacker.frags = (attacker.frags - 1);
					return;
				}
				else
				{
					attacker.frags = (attacker.frags + 1);
					if ((targ.dmg_inflictor.classname == "proximity_grenade"))
					{
						bprint(targ.netname);
						if ((random() < 0.5))
						{
							bprint(" got too friendly with ");
						}
						else
						{
							bprint(" did the rhumba with ");
						}
						bprint(attacker.netname);
						bprint("'s bomb\n");
						return;
					}
					rnum = attacker.weapon;
					deathstring = " was killed by ";
					deathstring2 = "\n";
					if (mm_inflicting)
					{
						rnum = IT_MEGAMAN;
						deathstring = " got run over by ";
						deathstring2 = "'s Mega Man\n";
					}
					if (bn_inflicting)
					{
						rnum = IT_BANANA;
						deathstring = " was peeled by ";
						deathstring2 = "'s banana\n";
					}
					if (ltg_inflicting)
					{
						rnum = IT_NAILGUN;
					}
					if (milky_inflicting)
					{
						rnum = IT_SUPER_NAILGUN;
					}
					if (sg_inflicting)
					{
						rnum = IT_SENTRY;
						deathstring = " is mown down by ";
						deathstring2 = "'s sentry gun\n";
					}
					if (veh_inflicting)
					{
						rnum = 999999;
						deathstring = " was blown sky-high by ";
						deathstring2 = "'s exploding vehicle\n";
					}
					if ((jb_inflicting == 1))
					{
						rnum = 999999;
						deathstring = " was shot out of the sky by ";
						deathstring2 = "\n";
					}
					if ((jb_inflicting == 2))
					{
						rnum = 999999;
						deathstring = " got falcon-swooped by ";
						deathstring2 = "'s Winged Breezy-Hair John\n";
					}
					if ((jb_inflicting == 3))
					{
						rnum = 999999;
						deathstring = " got frizzy-glued by ";
						deathstring2 = "'s John's Mega Hold hairspray\n";
					}
					if ((jb_inflicting == 4))
					{
						rnum = 999999;
						deathstring = " got hairspray-torched by ";
						deathstring2 = "'s Mega Hold flamethrower\n";
					}
					if ((jb_inflicting == 5))
					{
						rnum = 999999;
						deathstring = " ate a spinning bottle of ";
						deathstring2 = "'s John's Mega Hold\n";
					}
					if ((jb_inflicting == 6))
					{
						rnum = 999999;
						deathstring = " got pompadour-slapped by ";
						deathstring2 = "'s giant waving bangs\n";
					}
					if ((jb_inflicting == 7))
					{
						rnum = 999999;
						deathstring = " was blown away by ";
						deathstring2 = "'s pressurized aerosol bomb\n";
					}
					if ((ec_inflicting == 2))
					{
						rnum = 999999;
						deathstring = " was obliterated from orbit by ";
						deathstring2 = "'s ERIC DEASON CANNON!\n";
					}
					if ((mmt_inflicting == 1))
					{
						rnum = 999999;
						deathstring = " was blasted by ";
						deathstring2 = "'s Mega Man Tank silver bar!\n";
					}
					if ((mmt_inflicting == 2))
					{
						rnum = 999999;
						deathstring = " was blown up inside ";
						deathstring2 = "'s Mega Man Tank blast!\n";
					}
					if ((mmt_inflicting == 3))
					{
						rnum = 999999;
						deathstring = " was flattened under ";
						deathstring2 = "'s Mega Man Tank!\n";
					}
					if (fg_inflicting)
					{
						rnum = IT_FUNGUN;
						deathstring = FunGun_Death1(fg_inflicting);
						deathstring2 = FunGun_Death2(fg_inflicting);
					}
					if ((rnum == IT_AXE))
					{
						deathstring = " got bonked by ";	// Bonk Hammer
						deathstring2 = "'s hammer\n";
						if ((attacker.hm_tier == 3))
						{
							deathstring = " got sent flying by ";
						}
					}
					if ((rnum == IT_CHAINSAW))
					{
						deathstring = " was split by ";
						deathstring2 = "'s bloody chainsaw\n";
					}
					if ((rnum == IT_SHOTGUN))
					{
						deathstring = " chewed on ";
						deathstring2 = "'s boomstick\n";
					}
					if ((rnum == IT_SUPER_SHOTGUN))
					{
						deathstring = " ate 2 loads of ";
						deathstring2 = "'s buckshot\n";
					}
					if ((rnum == IT_NAILGUN))
					{
						deathstring = LtGun_Death();	// laptop gun
						deathstring2 = "\n";
					}
					if ((rnum == IT_SUPER_NAILGUN))
					{
						deathstring = " got milked by ";	// Milky Gun
						deathstring2 = "'s Pink Lady\n";
					}
					if ((rnum == IT_GRENADE_LAUNCHER))
					{
						deathstring = " got a face full of ";	// the grenade is JohnWave's head
						deathstring2 = "'s JohnWave\n";
						if ((targ.health < -40))
						{
							deathstring = " was washed away by ";
							deathstring2 = "'s JohnWave\n";
						}
					}
					if ((rnum == IT_ROCKET_LAUNCHER))
					{
						deathstring = " rides ";
						deathstring2 = "'s rocket\n";
						if ((targ.health < -40))
						{
							deathstring = " was gibbed by ";
							deathstring2 = "'s rocket\n";
						}
					}
					if ((rnum == IT_LIGHTNING))
					{
						deathstring = " accepts ";
						if ((attacker.waterlevel > 1))
						{
							deathstring2 = "'s discharge\n";
						}
						else
						{
							deathstring2 = "'s shaft\n";
						}
					}
					if ((rnum == IT_LASER_CANNON))
					{
						deathstring = " was CCC'd by ";
						deathstring2 = "\n";
					}
					bprint(targ.netname);
					bprint(deathstring);
					bprint(attacker.netname);
					bprint(deathstring2);
				}
			}
			return;
		}
		else
		{
			if ((targ.deathtype == "suicide"))
			{
				targ.deathtype = "";
				bprint(targ.netname, " suicides\n");
				return;
			}
			bprint(targ.netname);
			if (veh_inflicting)
			{
				bprint(" was blown sky-high by an exploding vehicle\n");
				return;
			}
			if (jb_inflicting)
			{
				if (jb_inflicting == 3)
					bprint(" got hairsprayed by AI Winged John\n");
				else if (jb_inflicting == 4)
					bprint(" was flame-broiled by AI Winged John\n");
				else if (jb_inflicting == 5)
					bprint(" was bonked by AI Winged John's hairspray bottle\n");
				else
					bprint(" went down in a storm of Winged John's feathers\n");
				return;
			}
			if (mmt_inflicting)
			{
				bprint(" was blown sky-high by a Mega Man Tank!\n");
				return;
			}
			if ((attacker.flags & FL_MONSTER))
			{
				if (((attacker.classname == "monster_floathead") || (attacker.classname == "fh_dead")))
				{
					bprint(" got a big wet kiss from a floating head\n");
				}
				if ((attacker.classname == "monster_army"))
				{
					bprint(" was shot by a Grunt\n");
				}
				if (((attacker.classname == "monster_demon1") || (attacker.netname == "monster_demon1")))
				{
					bprint(" was eviscerated by a Fiend\n");
				}
				if ((attacker.classname == "monster_dog"))
				{
					bprint(" was mauled by a Rottweiler\n");
				}
				if ((attacker.classname == "monster_dragon"))
				{
					bprint(" was fried by a Dragon\n");
				}
				if (((attacker.classname == "monster_enforcer") && ((attacker.skin == 1) && (autocvar_enforcer_defender == 1))))
				{
					bprint(" was blown away by a Defender\n");
				}
				else
				{
					if ((attacker.classname == "monster_enforcer"))
					{
						bprint(" was blasted by an Enforcer\n");
					}
				}
				if ((attacker.classname == "monster_fish"))
				{
					bprint(" was fed to the Rotfish\n");
				}
				if ((attacker.classname == "monster_hell_knight"))
				{
					bprint(" was slain by a Death Knight\n");
				}
				if ((attacker.classname == "monster_hydra"))
				{
					bprint(" was drowned by a Hydra\n");
				}
				if ((attacker.classname == "monster_knight"))
				{
					bprint(" was slashed by a Knight\n");
				}
				if ((attacker.classname == "monster_ogre"))
				{
					bprint(" was destroyed by an Ogre\n");
				}
				if ((attacker.classname == "monster_freddie"))
				{
					bprint(" was murdered by a Freddie\n");
				}
				if ((attacker.classname == "monster_oldone"))
				{
					bprint(" became one with Shub-Niggurath\n");
				}
				if (((attacker.classname == "monster_shalrath") || (attacker.netname == "monster_shalrath")))
				{
					bprint(" was exploded by a Vore\n");
				}
				if ((attacker.classname == "monster_shambler"))
				{
					bprint(" was smashed by a Shambler\n");
				}
				if ((attacker.classname == "monster_tarbaby"))
				{
					bprint(" was slimed by a Spawn\n");
				}
				if ((attacker.classname == "monster_vomit"))
				{
					bprint(" was vomited on by a Vomitus\n");
				}
				if (((attacker.classname == "monster_wizard") || (attacker.netname == "monster_wizard")))
				{
					bprint(" was scragged by a Scrag\n");
				}
				if (((attacker.classname == "monster_zombiek") || (attacker.netname == "monster_zombiek")))
				{
					bprint(" joins the Zombies\n");
				}
				if (((attacker.classname == "monster_zombie") || (attacker.netname == "monster_zombie")))
				{
					bprint(" joins the Zombies\n");
				}
				if ((attacker.classname == "monster_spider"))
				{
					bprint(" got eaten by a Spider\n");
				}
				if ((attacker.classname == "monster_afrit"))
				{
					bprint(" was burned down by a Afrit\n");
				}
				if ((attacker.classname == "monster_hell_knight2"))
				{
					bprint(" was crushed by a Warlord\n");
				}
				if ((attacker.classname == "monster_torment"))
				{
					bprint(" was gored by a Torment\n");
				}
				if ((attacker.classname == "monster_carnivean"))
				{
					bprint(" was sliced by a Carnivean\n");
				}
				if ((attacker.classname == "monster_yakman"))
				{
					bprint(" was crushed by a Yakman\n");
				}
				if ((attacker.classname == "monster_reiver"))
				{
					bprint(" was terrified by a Reiver\n");
				}
				if ((attacker.classname == "monster_dfury"))
				{
					bprint(" felt the fury like a whirlwind\n");
				}
				if ((attacker.classname == "monster_dfury_boss"))
				{
					bprint(" felt the fury like a whirlwind\n");
				}
				if ((attacker.classname == "monster_shalrath_boss"))
				{
					bprint(" is a permanent addition to the hive\n");
				}
				if (((attacker.classname == "monster_voreling") || (attacker.netname == "monster_voreling")))
				{
					bprint(" took one too many bites in the knee\n");
				}
				if ((attacker.classname == "monster_jim"))
				{
					bprint(" took the heat from jim\n");
				}
				return;
			}
			if ((attacker.classname == "explo_box"))
			{
				bprint(" blew up\n");
				return;
			}
			if (((attacker.solid == SOLID_BSP) && (attacker != world)))
			{
				if (attacker.deathtype)
				{
					bprint(" ");
					bprint(attacker.deathtype);
					bprint("\n");
					return;
				}
				else
				{
					bprint(" was squished\n");
					return;
				}
			}
			if (((attacker.classname == "trap_shooter") || (attacker.classname == "trap_spikeshooter")))
			{
				bprint(" was spiked\n");
				return;
			}
			if ((attacker.classname == "fireball"))
			{
				bprint(" ate a lavaball\n");
				return;
			}
			if ((attacker.classname == "trigger_changelevel"))
			{
				bprint(" tried to leave\n");
				return;
			}
			rnum = targ.watertype;
			if ((rnum == -3))
			{
				if ((random() < 0.5))
				{
					bprint(" sleeps with the fishes\n");
				}
				else
				{
					bprint(" sucks it down\n");
				}
				return;
			}
			else
			{
				if ((rnum == -4))
				{
					if ((random() < 0.5))
					{
						bprint(" gulped a load of slime\n");
					}
					else
					{
						bprint(" can't exist on slime alone\n");
					}
					return;
				}
				else
				{
					if ((rnum == -5))
					{
						if ((targ.health < -15))
						{
							bprint(" burst into flames\n");
							return;
						}
						if ((random() < 0.5))
						{
							bprint(" turned into hot slag\n");
						}
						else
						{
							bprint(" visits the Volcano God\n");
						}
						return;
					}
				}
			}
			if (((attacker.classname == "trigger_hurt") && attacker.deathtype))
			{
				bprint(" ");
				bprint(attacker.deathtype);
				bprint("\n");
				return;
			}
			else
			{
				if ((targ.deathtype == "falling"))
				{
					targ.deathtype = "";
					bprint(" fell to his death\n");
					return;
				}
			}
			bprint(" died\n");
		}
	}
};
