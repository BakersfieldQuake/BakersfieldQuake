//Decompiled code. Please respect the original copyright.

void(entity inflictor, entity attacker, float damage) SUB_Null_pain =
{
};

void(entity targ) gen_unique_no =
{

	if ((targ.entno_unique == 0))
	{
		targ.entno_unique = (rint((random() * 1000)) * rint((random() * 1000)));
	}
};

void(string target_strs, entity activator_ent) trigger_strs =
{
	local entity tself;
	local entity tother;
	local entity tactivator;
	local entity ent_list;

	dprint("шстрътригщ Str (");
	dprint(target_strs);
	dprint(") Activator (");
	dprint(activator_ent.classname);
	if ((target_strs == ""))
	{
		dprint(") - ERROR!!\n");
	}
	else
	{
		dprint(")\n");
	}
	if ((target_strs != ""))
	{
		tself = self;
		tother = other;
		tactivator = activator;
		if ((activator_ent.flags & FL_CLIENT))
		{
			activator = activator_ent;
		}
		ent_list = find(world, targetname, target_strs);
		while (ent_list)
		{
			self = ent_list;
			other = tself;
			if (self.use)
			{
				self.activate = activator_ent;
				self.use();
			}
			ent_list = find(ent_list, targetname, target_strs);
		}
		self = tself;
		other = tother;
		if ((activator_ent.flags & FL_CLIENT))
		{
			activator = tactivator;
		}
	}
};

float(vector check_vec) CheckZeroVector =
{
	if ((((check_vec_x == 0) && (check_vec_y == 0)) && (check_vec_z == 0)))
	{
		return (TRUE);
	}
	else
	{
		return (0);
	}
};

vector(float base, float rndmix, float plusminus) vecrand =
{
	local vector vecmix;

	if (plusminus)
	{
		vecmix_x = base + (crandom() * rndmix);
	}
	else
	{
		vecmix_x = base + (random() * rndmix);
	}
	return (vecmix);
};

void() model_fade =
{
	self.alpha = (1 - ((time - self.ltime) / 1));
	if ((self.alpha > 1))
	{
		self.alpha = 1;
	}
	else
	{
		if ((self.alpha <= 0))
		{
			self.alpha = 0;
			self.model = "";
			if (!self.height)
			{
				self.think = SUB_Remove;
				self.nextthink = (time + 1);
			}
			return;
		}
	}
	self.nextthink = (time + FADEMODEL_TIME);
};

vector(entity bmodel_ent) bmodel_origin =
{
	local vector vdiff;
	local vector vorigin;

	vdiff_x = (bmodel_ent.maxs_x - bmodel_ent.mins_x) / 2;
	vorigin = (bmodel_ent.origin + bmodel_ent.mins) + vdiff;
	return (vorigin);
};

void(entity targ) clear_trigstrs =
{
	if ((targ.target != ""))
	{
		targ.target = string_null;
	}
	if ((targ.killtarget != ""))
	{
		targ.killtarget = string_null;
	}
};

void(entity targ) entity_hide =
{
	targ.touch = SUB_Null;
	targ.use = SUB_Null;
	targ.think = SUB_Null;
	targ.nextthink = -1;
	targ.estate = ESTATE_OFF;
	setmodel(targ, "");
	targ.takedamage = 0;
	targ.movetype = 0;
	targ.solid = 0;
	setsize(targ, VEC_ORIGIN, VEC_ORIGIN);
	targ.avelocity = VEC_ORIGIN;
	targ.velocity = VEC_ORIGIN;
	targ.effects = 0;
	targ.spawnflags = 0;
	targ.waitmin = (time + LARGE_TIMER);
};

void(entity targ, float removetime) entity_remove =
{
	entity_hide(targ);
	targ.think = SUB_Remove;
	targ.nextthink = (time + removetime);
};

float(vector targ_origin) check_skycontent =
{
	local float surfnum;
	local string texturename;

	if (ext_dpsurf)
	{
		surfnum = getsurfacenearpoint(world, targ_origin);
		if ((surfnum >= 0))
		{
			texturename = getsurfacetexture(world, surfnum);
			if ((strncasecmp(texturename, /*14380i*/"SKY", 3) == 0))
			{
				return (TRUE);
			}
		}
	}
	else
	{
		if ((pointcontents(targ_origin) == CONTENT_SKY))
		{
			return (TRUE);
		}
	}
	return (0);
};

void(vector spawn_org) spawn_marker =
{
	local entity brokend;

	if (developer)
	{
		brokend = spawn();
		brokend.classtype = CT_DEVMARKER;
		brokend.movetype = 0;
		brokend.solid = 0;
		setmodel(brokend, MODEL_BROKEN);
		setorigin(brokend, spawn_org);
		setsize(brokend, VEC_ORIGIN, VEC_ORIGIN);
		if ((engine == ENG_DPEXT))
		{
			brokend.effects = (brokend.effects + EF_NOSHADOW);
		}
	}
};

void(entity target_ent, entity activator_ent) trigger_ent =
{
	local entity tself;
	local entity tother;
	local entity tactivator;

	dprint("шентътригщ Ent (");
	dprint(ftos(target_ent.classtype));
	dprint(") Activator (");
	dprint(activator_ent.classname);
	if (!target_ent)
	{
		dprint(") - ERROR!!\n");
	}
	else
	{
		dprint(")\n");
	}
	if ((target_ent && target_ent.use))
	{
		tself = self;
		tother = other;
		tactivator = activator;
		if ((activator_ent.flags & FL_CLIENT))
		{
			activator = activator_ent;
		}
		self = target_ent;
		other = tself;
		if (self.use)
		{
			self.activate = activator_ent;
			self.use();
		}
		self = tself;
		other = tother;
		if ((activator_ent.flags & FL_CLIENT))
		{
			activator = tactivator;
		}
	}
};

float(entity targ, float flat2d) range_distance =
{
	local vector spot1;
	local vector spot2;
	local float r;

	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	if (flat2d)
	{
	}
	r = vlen((spot1 - spot2));
	return (r);
};

float(vector pc_org) entity_pcontent =
{
	local float pcontent;

	pcontent = pointcontents(pc_org);
	if ((pcontent == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if (check_skycontent(pc_org))
	{
		return (TRUE);
	}
	return (0);
};

vector(vector attack_dir) attack_vector =
{
	local vector retvec;

	retvec = v_forward * attack_dir_x;
	retvec = retvec + (v_right * attack_dir_y);
	retvec = retvec + (v_up * attack_dir_z);
	return (retvec);
};

void(vector org, float velrnd, float upbase, float uprnd) SpawnProjectileSmoke =
{
	newmis = spawn();
	newmis.classgroup = CG_TEMPENT;
	newmis.movetype = MOVETYPE_TOSS;
	newmis.solid = 0;
	setmodel(newmis, "progs/proj_smoke.mdl");
	setorigin(newmis, org);
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	if ((velrnd > 0))
	{
		newmis.velocity = vecrand(0, velrnd, TRUE);
	}
	else
	{
		newmis.velocity = VEC_ORIGIN;
	}
	newmis.velocity_z = (upbase + (random() * uprnd));
	newmis.nextthink = ((time + 1) + (random() * 3));
	newmis.think = SUB_Remove;
};

void() monster_start =
{
	self.flags = FL_MONSTER;
	self.skin_override = self.skin;
	self.frame_override = self.frame;
	if (self.effects)
	{
		dprint("шмонстерщ Effects flag active\n");
		self.savedeffects = self.effects;
	}
	self.effects = 0;
	self.oldorigin = self.origin;
	self.max_health = self.health;
	if (!self.gibhealth)
	{
		self.gibhealth = (0 - self.health);
	}
	if (((self.turrethealth < 0) || (self.turrethealth > 1)))
	{
		self.turrethealth = 0.5;
	}
	if ((self.jump_flag < 0))
	{
		self.jump_flag = LARGE_TIMER;
	}
	spawn_marker((self.origin + '0 0 32'));
	if (((self.spawnflags & MON_SPAWN_DELAY) && (self.targetname == "")))
	{
		dprint("шмонстерщ Cannot delay spawn without targetname!\n");
		remove(self);
		return;
	}
	if (!self.nomonstercount)
	{
		total_monsters = total_monsters + 1;
	}
	else
	{
		dprint("шмонстерщ (");
		dprint(self.targetname);
		dprint(") - no monster count\n");
	}
	if ((self.armorvalue || self.armortype))
	{
		dprint("шмапхацксщ Using armor on monsters, use health key instead!\n");
	}
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, self.mdl);
	self.skin = self.skin_override;
	self.frame = self.frame_override;
	walkmonster_start();
};
