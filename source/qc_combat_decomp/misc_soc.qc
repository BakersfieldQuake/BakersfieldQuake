//Decompiled code. Please respect the original copyright.

void() misc_smoke_model =
{
	self.count = (self.count + 1);
	if ((self.count > 59))
	{
		self.count = 0;
	}
	self.frame = self.count;
	self.think = misc_smoke_model;
	self.nextthink = (time + 0.1);
};

void() misc_smoke_on =
{
	self.estate = ESTATE_ON;
	if (self.part_emitter)
	{
		misc_particle_on(self.part_emitter);
	}
	if (self.partname)
	{
		self.traileffectnum = BM_TrailEffect(self.partname);
	}
	if ((self.mdl != ""))
	{
		setmodel(self, self.mdl);
		setsize(self, VEC_ORIGIN, VEC_ORIGIN);
		self.skin = self.exactskin;
		self.count = rint((random() * 59));
		misc_smoke_model();
	}
};

void() misc_smoke_off =
{
	self.estate = ESTATE_OFF;
	if ((self.mdl != ""))
	{
		self.model = "";
	}
};

void() misc_smoke_setup =
{
	if ((self.target != ""))
	{
		if (!self.movetarget)
		{
			self.movetarget = find(world, targetname, self.target);
		}
		if (self.movetarget)
		{
			if (self.movetarget.bsporigin)
			{
				self.dest1 = bmodel_origin(self.movetarget);
			}
			else
			{
				self.dest1 = self.movetarget.origin;
			}
			self.movedir = normalize((self.dest1 - self.origin));
			self.angles = vectoangles(self.movedir);
			self.angles_y = (self.angles_y + 180);
			if (self.part_emitter)
			{
				self.part_emitter.dpp_vel = (self.movedir * self.height);
			}
		}
	}
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_on = misc_smoke_on;
	self.estate_off = misc_smoke_off;
	if ((self.spawnflags & 65))
	{
		entity_state_off();
	}
	else
	{
		entity_state_on();
	}
};

void() misc_smoke =
{

	self.mdl = "progs/misc_smoke.mdl";
	precache_model(self.mdl);
	self.classtype = CT_MISCSMOKE;
	self.classgroup = CG_MISCENT;
	self.solid = 0;
	self.movetype = 0;
	if (!self.exactskin)
	{
		self.exactskin = 0;
	}
	if ((self.wait < 0.1))
	{
		self.wait = 0.1;
	}
	if ((self.delay <= 0))
	{
		self.delay = 0.1;
	}
	if ((self.height <= 0))
	{
		self.height = (0.5 + (random() * 0.5));
	}
	if ((engine == ENG_DPEXT))
	{
		self.effects = (self.effects + EF_NOSHADOW);
	}
	else
	{
		if (!self.alpha)
		{
			self.alpha = (0.5 + (random() * 0.25));
		}
	}
	makevectors(self.angles);
	self.movedir = v_up;
	if (CheckZeroVector(self.angles))
	{
		self.angles_y = rint((random() * 360));
	}
	if (ext_dppart)
	{
		if ((self.spawnflags & MISC_SMOKENODPMDL))
		{
			self.mdl = "";
		}
		query_configflag(SVR_PARTICLES);
		if ((query_configflag(SVR_PARTICLES) && !(self.spawnflags & MISC_SMOKENODPFX)))
		{
			self.part_active = PARTICLE_STYLE_SMOKE;
			if ((self.spawnflags & 65))
			{
				self.part_emitter = spawn_pemitter(self, self, self.part_active, PARTICLE_START_OFF);
			}
			else
			{
				self.part_emitter = spawn_pemitter(self, self, self.part_active, PARTICLE_START_ON);
			}
		}
	}
	self.nextthink = ((time + 0.1) + (rint((random() * 10)) * 0.1));
	self.think = misc_smoke_setup;
};

void() misc_sparks_fade1 = [ 0, misc_sparks_fade2 ]
{
	self.alpha = 0.8;
	self.nextthink = (time + 0.05);
};

void() misc_sparks_fade2 = [ 0, misc_sparks_fade3 ]
{
	self.alpha = 0.6;
	self.nextthink = (time + 0.05);
};

void() misc_sparks_fade3 = [ 0, misc_sparks_fade4 ]
{
	self.alpha = 0.4;
	self.nextthink = (time + 0.05);
};

void() misc_sparks_fade4 = [ 0, SUB_Remove ]
{
	self.alpha = 0.2;
	self.nextthink = (time + 0.05);
};

void() misc_spark_switchoff =
{
	SUB_UseTargets();
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	if ((self.wait > 0))
	{
		self.think = misc_spark_spawn;
		self.nextthink = ((time + self.wait) + (random() * self.wait));
	}
};

void() misc_spark_spawn =
{
	local float loopvar;
	local entity spark;

	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	if ((self.fixangle > 0))
	{
		self.angles = VEC_ORIGIN;
		self.angles_y = rint((random() * 360));
		makevectors(self.angles);
		self.movedir = v_forward;
	}
	loopvar = (0.5 + (random() * 0.5)) * self.cnt;
	while ((loopvar > 0))
	{
		spark = spawn();
		spark.classtype = CT_TEMPSPARK;
		spark.classgroup = CG_TEMPENT;
		spark.owner = self;
		spark.movetype = MOVETYPE_BOUNCE;
		spark.solid = SOLID_TRIGGER;
		setmodel(spark, self.mdl);
		setorigin(spark, self.origin);
		setsize(spark, VEC_ORIGIN, VEC_ORIGIN);
		spark.gravity = 0.3;
		spark.velocity = vecrand(0, self.height, TRUE);
		spark.velocity = (spark.velocity + (self.movedir * self.speed));
		spark.avelocity = '300 300 300';
		spark.nextthink = ((time + 0.5) + (1.5 * random()));
		spark.think = misc_sparks_fade1;
		if ((engine == ENG_DPEXT))
		{
			spark.effects = (spark.effects + EF_NOSHADOW);
		}
		if ((random() < 0.33))
		{
			spark.skin = 0;
		}
		else
		{
			if ((random() < 0.5))
			{
				spark.skin = 1;
			}
			else
			{
				spark.skin = 2;
			}
		}
		if ((self.spawnflags & MISC_SPARKBLUE))
		{
			spark.skin = (spark.skin + 3);
		}
		else
		{
			if ((self.spawnflags & MISC_SPARKPALE))
			{
				spark.skin = (spark.skin + 6);
			}
			else
			{
				if ((self.spawnflags & MISC_SPARKRED))
				{
					spark.skin = (spark.skin + 9);
				}
			}
		}
		loopvar = loopvar - 1;
	}
	if ((self.noise != ""))
	{
		sound(self, CHAN_VOICE, self.noise, 1, ATTN_STATIC);
	}
	if (self.target)
	{
		SUB_UseTargets();
		self.nextthink = ((time + 0.1) + (random() * 0.2));
		self.think = misc_spark_switchoff;
	}
	else
	{
		if ((self.wait > 0))
		{
			self.nextthink = (((time + 0.2) + self.wait) + (random() * self.wait));
			self.think = misc_spark_spawn;
		}
	}
};

void() misc_spark_on =
{
	self.estate = ESTATE_ON;
	self.nextthink = ((time + 0.1) + random());
	self.think = misc_spark_spawn;
};

void() misc_spark =
{
	self.mdl = "progs/misc_spark.mdl";
	precache_model(self.mdl);
	if ((self.sounds == 1))
	{
		self.noise = "misc/spark.wav";
	}
	if ((self.noise != ""))
	{
		precache_sound(self.noise);
	}
	self.classtype = CT_MISCSPARK;
	self.classgroup = CG_MISCENT;
	self.solid = 0;
	self.movetype = 0;
	if (!self.wait)
	{
		self.wait = 2;
	}
	if (!self.cnt)
	{
		self.cnt = 16;
	}
	if (!self.speed)
	{
		self.speed = 40;
	}
	if (!self.height)
	{
		self.height = 20;
	}
	self.estate = ESTATE_OFF;
	if (CheckZeroVector(self.angles))
	{
		self.angles = '0 360 0';
	}
	self.mangle = self.angles;
	SetMovedir();
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_on = misc_spark_on;
	if ((self.spawnflags & 65))
	{
		entity_state_off();
	}
	else
	{
		entity_state_on();
	}
};

void() misc_shake_think =
{
	local entity plyr;
	local float d;

	if (((self.attack_finished < time) || (self.estate & ESTATE_BLOCK)))
	{
		if (self.noise2)
		{
			sound(self, CHAN_VOICE, self.noise2, 1, ATTN_NORM);
		}
		if ((self.estate == ESTATE_ON))
		{
			self.estate = ESTATE_OFF;
		}
		return;
	}
	plyr = findradius(self.origin, self.count);
	while (plyr)
	{
		if ((plyr.flags & FL_CLIENT))
		{
			d = vlen((self.origin - plyr.origin));
			d = (self.count - d) / self.count;
			if ((d > 0))
			{
				random();
				plyr.punchangle_x = (-1 * (random() + ((0.025 * self.dmg) * d)));
				random();
				plyr.punchangle_y = (-1 * (random() + ((0.025 * self.dmg) * d)));
				random();
				plyr.punchangle_z = (-1 * (random() + ((0.025 * self.dmg) * d)));
				if (((plyr.flags & FL_ONGROUND) && !(self.spawnflags & MISC_SHAKEVIEWONLY)))
				{
					d = self.dmg * d;
					plyr.velocity_x = (plyr.velocity_x + (((random() * d) * 2) - d));
					plyr.velocity_y = (plyr.velocity_y + (((random() * d) * 2) - d));
					plyr.velocity_z = (plyr.velocity_z + (random() * d));
				}
			}
		}
		plyr = plyr.chain;
	}
	self.nextthink = (time + 0.1);
	self.think = misc_shake_think;
};

void() misc_shake_on =
{
	self.estate = ESTATE_ON;
	if (self.noise1)
	{
		sound(self, CHAN_VOICE, self.noise1, 1, ATTN_NORM);
	}
	self.attack_finished = (time + self.wait);
	self.nextthink = (time + 0.1);
	self.think = misc_shake_think;
};

void() misc_shake =
{
	if ((self.sounds == 1))
	{
		self.noise1 = "misc/rumbleloop.wav";
		self.noise2 = "misc/rumbleoff.wav";
	}
	else
	{
		if ((self.noise1 == ""))
		{
			self.noise1 = SOUND_EMPTY;
		}
		if ((self.noise2 == ""))
		{
			self.noise2 = SOUND_EMPTY;
		}
	}
	precache_sound(self.noise1);
	precache_sound(self.noise2);
	self.classtype = CT_MISCSHAKE;
	self.classgroup = CG_MISCENT;
	if (!self.dmg)
	{
		self.dmg = 120;
	}
	if ((self.count <= 0))
	{
		self.count = 200;
	}
	if ((self.wait <= 0))
	{
		self.wait = 2;
	}
	self.attack_finished = 0;
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_on = misc_shake_on;
	self.estate = ESTATE_OFF;
};

void() misc_model_loop =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	self.height = (self.height + self.lip);
	if (((self.lip > 0) && (self.height > self.pos1_y)))
	{
		self.height = self.pos1_x;
	}
	else
	{
		if (((self.lip < 0) && (self.height < self.pos1_y)))
		{
			self.height = self.pos1_x;
		}
	}
	self.frame = self.height;
	self.think = misc_model_loop;
	self.nextthink = (time + self.speed);
};

void() misc_model_on =
{
	self.estate = ESTATE_ON;
	if ((self.spawnflags & MISC_COLLISION))
	{
		self.solid = SOLID_BBOX;
	}
	setmodel(self, self.mdl);
	if (wasfreed(self))
		return;
	setsize(self, self.mins, self.maxs);
	setorigin(self, (self.oldorigin + self.view_ofs));
	self.skin = self.pos2_z;
	if (self.partname)
	{
		self.traileffectnum = BM_TrailEffect(self.partname);
	}
	if ((self.pos1_z == -1))
	{
		self.height = self.pos1_x;
		if ((self.pos1_x < self.pos1_y))
		{
			self.lip = 1;
		}
		else
		{
			self.lip = -1;
		}
		misc_model_loop();
	}
	else
	{
		self.frame = self.pos1_z;
		// props with a distance cull (misc_model_indoor_customize) stay networked: a static entity ignores it, and the
		// client then occlusion-traces every indoor chair and stool in view of the street each frame (2026-11-26)
		if (!self.solid && self.targetname == "" && !self.partname && !(self.spawnflags & 65) && !self.customizeentityforclient &&
		    (!self.scale || self.scale == 1) && (!self.alpha || self.alpha == 1) && !self.effects &&
		    self.mdl != "progs/bklan/soda_can.md3" && self.mdl != "progs/bklan/soda_bottle.md3" && self.mdl != "progs/bklan/cup.md3")
		{
			makestatic(self);
		}
	}
};

void() misc_model_off =
{
	self.estate = ESTATE_OFF;
	self.model = string_null;
	self.solid = 0;
};

float() misc_model_indoor_customize =
{
	local vector vorg;
	local float dx, dy, dz;

	if (other.ishuman != 1)
		return FALSE;
	vorg = (other.clientcamera != world) ? other.clientcamera.origin : other.origin;
	dx = vorg_x - self.origin_x;
	if (dx > 1800 || dx < -1800)
		return FALSE;
	dy = vorg_y - self.origin_y;
	if (dy > 1800 || dy < -1800)
		return FALSE;
	dz = vorg_z - self.origin_z;
	if (dz > 650 || dz < -650)
		return FALSE;
	return TRUE;
};

void() misc_model =
{

	if (!self.mdl)
	{
		dprint("ÛÍÉÓÃÍÄÌÝ Missing model to load\n");
		spawn_marker(self.origin, SPNMARK_YELLOW);
		remove(self);
		return;
	}
	precache_model(self.mdl);
	self.classtype = CT_MISCMODEL;
	self.classgroup = CG_MISCENT;
	self.solid = 0;
	self.movetype = 0;
	self.oldorigin = self.origin;
	if ((self.angles_y < 0))
	{
		self.angles_y = rint((random() * 360));
	}
	self.mangle = self.angles;
	if (!self.speed)
	{
		self.speed = 0.1;
	}
	if ((self.pos1_x != self.pos1_y))
	{
		if ((self.pos1_x > self.pos1_y))
		{
			self.frame_box = self.pos1_x;
			self.pos1_x = self.pos1_y;
			self.pos1_y = self.frame_box;
		}
		if ((self.pos1_z == 0))
		{
			if ((self.pos1_x < 0))
			{
				self.pos1_x = 0;
			}
			self.frame_box = fabs((self.pos1_y - self.pos1_x));
			self.pos1_z = (self.pos1_x + rint((random() * self.frame_box)));
			if ((self.pos1_z < self.pos1_x))
			{
				self.pos1_z = self.pos1_x;
			}
			if ((self.pos1_z > self.pos1_y))
			{
				self.pos1_z = self.pos1_y;
			}
		}
		else
		{
			self.pos1_z = -1;
		}
	}
	else
	{
		if ((self.pos1_z < 1))
		{
			self.pos1 = VEC_ORIGIN;
		}
	}
	if ((self.pos2_x != self.pos2_y))
	{
		random();
		self.pos2_z = rint((random() * fabs((self.pos2_y - self.pos2_x))));
	}
	else
	{
		if ((self.pos2_z < 1))
		{
			self.pos2 = VEC_ORIGIN;
		}
	}
	if (((self.ideal_yaw > 0) && (query_configflag(SVR_ITEMROTATE) == FALSE)))
	{
		self.angles_y = rint((random() * 359));
	}
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	if (substring(self.mdl, 0, 14) == "progs/fox/pad_" || substring(self.mdl, 0, 20) == "progs/fox/fox_chande")
		self.customizeentityforclient = misc_model_indoor_customize;
	// the warehouse LAN gear and the G FUEL shop shelf on the two Bakersfield maps are indoors too
	else if ((mapname == "bakersfieldish" || mapname == "bakersfielddowntown") && (substring(self.mdl, 0, 12) == "progs/bklan/" || substring(self.mdl, 0, 12) == "progs/gfuel/"))
		self.customizeentityforclient = misc_model_indoor_customize;
	self.estate_on = misc_model_on;
	self.estate_off = misc_model_off;
	if ((self.spawnflags & 65))
	{
		entity_state_off();
	}
	else
	{
		entity_state_on();
	}
};

void() misc_gtkmodel =
{
	misc_model();
};

void() misc_deadbody_on =
{
	if ((self.gibbed == TRUE))
	{
		return;
	}
	self.estate = ESTATE_ON;
	self.solid = 0;
	self.movetype = 0;
	setmodel(self, self.mdl);
	setsize(self, self.bbmins, self.bbmaxs);
	self.bodyonflr = MON_ONFLR;
};

void() misc_deadbody_off =
{
	if ((self.gibbed == TRUE))
	{
		return;
	}
	self.estate = ESTATE_OFF;
	self.solid = 0;
	self.movetype = 0;
	setmodel(self, "");
	setsize(self, VEC_ORIGIN, VEC_ORIGIN);
	self.bodyonflr = "";
};

void() misc_deadbody_setup =
{
	self.classtype = CT_MISCMODEL;
	self.classgroup = CG_MISCENT;
	self.oldorigin = self.origin;
	self.takedamage = 0;
	self.deadflag = DEAD_DEAD;
	self.max_health = -1;
	self.health = -1;
	self.blockudeath = TRUE;
	self.gibbed = 0;
	if ((self.angles_y < 0))
	{
		self.angles_y = rint((random() * 360));
	}
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_on = misc_deadbody_on;
	self.estate_off = misc_deadbody_off;
	if ((self.spawnflags & ENT_STARTOFF))
	{
		entity_state_off();
	}
	else
	{
		entity_state_on();
	}
};

void() misc_drip_reset =
{
	self.touch = SUB_Null;
	self.flags = 0;
	self.frame = 0;
	setmodel(self, "");
	self.solid = 0;
	self.movetype = 0;
	setsize(self, VEC_ORIGIN, VEC_ORIGIN);
	self.avelocity = VEC_ORIGIN;
	self.velocity = VEC_ORIGIN;
	self.nextthink = ((time + random()) + self.wait);
	self.think = misc_drip_spawn;
};

void() s_splash1 = [ 0, s_splash2 ]
{
	self.nextthink = (time + 0.05);
};

void() s_splash2 = [ 1, s_splash3 ]
{
	self.nextthink = (time + 0.05);
};

void() s_splash3 = [ 2, s_splash4 ]
{
	self.nextthink = (time + 0.05);
};

void() s_splash4 = [ 3, s_splash5 ]
{
	self.nextthink = (time + 0.05);
};

void() s_splash5 = [ 4, s_splash6 ]
{
	self.nextthink = (time + 0.05);
};

void() s_splash6 = [ 5, misc_drip_reset ]
{
	self.nextthink = (time + 0.05);
};

void() misc_drip_touch =
{
	self.touch = SUB_Null;
	self.solid = 0;
	self.movetype = 0;
	if (self.cnt)
	{
		self.origin = self.pos1;
	}
	setorigin(self, (self.origin + '0 0 12'));
	if (!(self.spawnflags & MISC_DRIPSILENT))
	{
		self.lip = (random() * 3);
		if ((self.lip < 1))
		{
			sound(self, CHAN_AUTO, self.noise1, 1, ATTN_STATIC);
		}
		else
		{
			if ((self.lip < 2))
			{
				sound(self, CHAN_AUTO, self.noise2, 1, ATTN_STATIC);
			}
			else
			{
				sound(self, CHAN_AUTO, self.noise3, 1, ATTN_STATIC);
			}
		}
	}
	particle((self.origin + '0 0 1'), '0 0 0.5', (self.aflag + (random() * 4)), (5 + (random() * 5)));
	setmodel(self, self.headmdl);
	s_splash1();
};

void() misc_drip_water =
{
	if ((self.attack_finished < time))
	{
		misc_drip_reset();
	}
	if ((self.origin_z < self.pos1_z))
	{
		misc_drip_touch();
	}
	self.nextthink = (time + 0.1);
};

void() misc_drip_spawn =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	self.effects = EF_LOWPRECISION;
	setorigin(self, self.oldorigin);
	setmodel(self, self.mdl);
	self.solid = SOLID_TRIGGER;
	if (self.cnt)
	{
		self.movetype = MOVETYPE_NOCLIP;
	}
	else
	{
		self.movetype = MOVETYPE_FLY;
	}
	setsize(self, VEC_ORIGIN, VEC_ORIGIN);
	if ((self.netname == "gibsplat"))
	{
		self.velocity = VEC_ORIGIN;
		self.frame = 1;
		self.movetype = MOVETYPE_TOSS;
		self.gravity = 0.8;
		self.colormod = '0.3 0 0';
		if ((BLD >= MAX_DRIPS))
		{
			BLD = BLD + -1;
			remove(self);
			return;
		}
	}
	else
	{
		self.velocity_z = -500;
	}
	if ((self.spawnflags & MISC_RAIN))
	{
		self.velocity = '-70 -40 -500';
	}
	self.think = misc_drip_reset;
	self.nextthink = (time + 3);
	self.touch = misc_drip_touch;
	if (self.cnt)
	{
		self.attack_finished = self.nextthink;
		self.nextthink = (time + 0.1);
		self.think = misc_drip_water;
	}
};

void() misc_drip_on =
{
	self.estate = ESTATE_ON;
	self.nextthink = ((time + random()) + self.wait);
	self.think = misc_drip_spawn;
};

void() misc_drip =
{
	if ((self.spawnflags & MISC_DRIPBLOOD))
	{
		self.mdl = SBLOOD_DRIP;
		self.headmdl = SBLOOD_SPLASH;
		self.aflag = 64;
	}
	else
	{
		if ((self.spawnflags & MISC_DRIPSLIME))
		{
			self.mdl = SSLIME_DRIP;
			self.headmdl = SSLIME_SPLASH;
			self.aflag = 48;
		}
		else
		{
			self.mdl = SWATER_DRIP;
			self.headmdl = SWATER_SPLASH;
			self.aflag = 0;
		}
	}
	self.noise1 = "misc/drip1.wav";
	self.noise2 = "misc/drip2.wav";
	self.noise3 = "misc/drip3.wav";
	if ((self.netname == "gibsplat"))
	{
		self.noise1 = "gib/gibhit4.wav";
		self.noise2 = "gib/gibhit4.wav";
		self.noise3 = "gib/gibhit4.wav";
		self.mdl = "progs/s_dripsplred.spr";
		sendParticle("hldecal", (self.origin - '0 0 10'), '0 0 -100', 2);
	}
	precache_model(self.mdl);
	precache_model(self.headmdl);
	precache_sound(self.noise1);
	precache_sound(self.noise2);
	precache_sound(self.noise3);
	if ((self.wait <= 0))
	{
		self.wait = 3;
	}
	if ((self.spawnflags & MISC_RAIN))
	{
		self.gravity = 0;
		if ((coop || deathmatch))
		{
			remove(self);
			return;
		}
	}
	self.classtype = CT_MISCDRIP;
	self.classgroup = CG_MISCENT;
	self.solid = 0;
	self.movetype = 0;
	setsize(self, VEC_ORIGIN, VEC_ORIGIN);
	self.height = pointcontents(self.origin);
	if ((self.height < CONTENT_SOLID))
	{
		dprint("ÛÍÉÓÃÄÒÉÐÝ Spawned inside liquid!\n");
		spawn_marker(self.origin, SPNMARK_YELLOW);
		remove(self);
		return;
	}
	else
	{
		if ((self.height == CONTENT_SOLID))
		{
			self.origin_z = (self.origin_z - 2);
		}
	}
	self.oldorigin = self.origin;
	setorigin(self, self.origin);
	self.pos1 = self.origin;
	traceline(self.pos1, (self.pos1 + '0 0 -4096'), TRUE, self);
	self.pos2 = trace_endpos;
	self.count = 8;
	if (trace_inwater)
	{
		self.cnt = TRUE;
	}
	else
	{
		self.count = 0;
	}
	while ((self.count > 0))
	{
		if ((fabs((self.pos2_z - self.pos1_z)) < 8))
		{
			self.count = 0;
		}
		self.pos3 = self.pos1;
		self.pos3_z = (self.pos1_z + ((self.pos2_z - self.pos1_z) * 0.5));
		traceline(self.pos1, self.pos3, TRUE, self);
		if (trace_inwater)
		{
			self.pos2 = self.pos3;
		}
		else
		{
			self.pos1 = self.pos3;
		}
		self.count = (self.count - 1);
	}
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_on = misc_drip_on;
	if ((self.spawnflags & 65))
	{
		entity_state_off();
	}
	else
	{
		entity_state_on();
	}
};

void() fx_drip =
{
	misc_drip();
};
