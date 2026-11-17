//Decompiled code. Please respect the original copyright.

void() W_Precache =
{
	MegaMan_Precache();
	BM_Precache();
	JG_SplashPrecache();	// JohnWave grenade: splash sprites and sound (jg_splash.qc)
	FloatHead_Precache();	// the floating head monster (floathead.qc)
	if (cvar("br_mode"))
		Bryan_Precache();	// Tinfoil-Hat Bryan & His Demons (bryan.qc)
	if (cvar("dv_mode"))
		David_Precache();	// David Ojeda & 3 Running Pregnant Hispanic Women (david.qc)
	HitSound_Precache();
	FunGun_Precache();
	Milky_Precache();	// the Milky Gun replaces the super nailgun (milky.qc)
	Hammer_Precache();	// the Bonk Hammer replaces the axe (hammer.qc)
	LtGun_Precache();	// the laptop gun replaces the sniper rifle (ltgun.qc)
	Goo_Precache();	// the Goo Gun replaces the shotgun (goo.qc)
	LanProps_Precache();
	precache_sound("weapons/r_exp3.wav");
	precache_sound("weapons/xpld_wat.wav");
	precache_sound(SOUND_REXP3);
	precache_sound("weapons/rocket1i.wav");
	precache_sound("weapons/rocket2i.wav");
	precache_sound("weapons/ngslow.wav");
	precache_sound("weapons/sngslow.wav");
	precache_sound("weapons/sgun1.wav");
	precache_sound("weapons/guncock.wav");
	precache_sound("weapons/ric1.wav");
	precache_sound("weapons/ric2.wav");
	precache_sound("weapons/ric3.wav");
	precache_sound("weapons/spike2.wav");
	precache_sound("weapons/spikespn.wav");
	precache_sound("weapons/tink1.wav");
	precache_sound("weapons/grenade.wav");
	precache_sound("weapons/bounce.wav");
	precache_sound("weapons/shotgn2.wav");
	precache_sound("weapons/lg_hum.wav");
	precache_sound("weapons/rockload.wav");
	precache_sound("weapons/grenarm.wav");
	precache_sound("weapons/grenthrow.wav");
	precache_sound("weapons/proxexp.wav");
	precache_sound("weapons/ssg2.wav");
	precache_sound("hipweap/laserg.wav");
	precache_sound("hipweap/laserric.wav");
	precache_sound("ccc/shoot.wav");
	precache_sound("floathead/boing.wav");
	precache_sound("weapons/goostick.wav");
	precache_model("progs/ccc.md3");
	precache_sound2("enforcer/enfstop.wav");
	precache_sound("hipweap/proxwarn.wav");
	precache_sound("hipweap/proxbomb.wav");
	precache_sound("hipweap/proxstick.wav");
	precache_sound("hipweap/hipmelt.wav");
	precache_sound("hipweap/hipmelt2.wav");
	precache_sound("weapons/sawatck.wav");
	precache_sound("weapons/sawguts.wav");
	precache_sound("weapons/saw_metal.wav");
	precache_sound("weapons/sawridle.wav");
	precache_sound("weapons/sawidle.wav");
	precache_sound("shambler/smack.wav");
	precache_sound("hook/chain1.wav");
	precache_sound("hook/chain2.wav");
	precache_sound("hook/launch.wav");
	precache_sound("hook/retract.wav");
};

void() gib_stuck_think =
{
	setorigin(self, ((self.pos1 + self.owner.origin) - self.pos2));
	self.think = gib_stuck_think;
	self.nextthink = time;
};

void() stickgib_touch =
{
	if ((other.classname == "player"))
	{
		return;
	}
	else
	{
		if ((other.solid != SOLID_BSP))
		{
			return;
		}
		else
		{
			if ((other.classname == "func_breakable"))
			{
				self.gravity = 1;
			}
			else
			{
				self.movetype = MOVETYPE_FLY;
			}
		}
	}
	self.solid = 0;
	self.velocity = VEC_ORIGIN;
	self.traileffectnum = particleeffectnum(/*24250i*/"gibd");
	if ((((other.solid == SOLID_BSP) && (other != world)) && (other.classname != "func_breakable")))
	{
		self.owner = other;
		self.pos1 = self.origin;
		self.pos2 = other.origin;
		self.think = gib_stuck_think;
		self.nextthink = time;
	}
};

void(string gibname, float skintype) StickGib =
{
	local vector dir;
	local entity new;

	new = spawn();
	new.origin = self.origin;
	if ((self.classname == "player"))
	{
		new.colormap = self.colormap;
	}
	setmodel(new, gibname);
	setsize(new, VEC_ORIGIN, VEC_ORIGIN);
	dir = normalize(v_forward);
	makevectors(self.enemy.v_angle);
	if ((((gibname == "progs/gib_enforcer_torso_sng2.mdl") || (gibname == "progs/gib_enforcer_torso_nail.mdl")) || (gibname == "progs/gib_soldhead.mdl")))
	{
		new.origin_z = (new.origin_z + 15);
	}
	new.velocity = aim(self.enemy, 2);
	if ((cvar("slowmo") > 0.7))
	{
		new.gravity = 0.8;
		new.velocity = (v_forward * 3000);
	}
	else
	{
		new.gravity = 0.5;
		new.velocity = (v_forward * 1000);
	}
	new.movetype = MOVETYPE_TOSS;
	new.angles = vectoangles((VEC_ORIGIN - new.velocity));
	new.traileffectnum = particleeffectnum(/*25442i*/"hldecalB");
	if ((skintype == 1))
	{
		new.skin = 1;
	}
	else
	{
		new.skin = 0;
	}
	new.solid = SOLID_TRIGGER;
	new.touch = stickgib_touch;
	new.frame = 0;
};

void() laserdie =
{
	local entity spark;

	spark = spawn();
	setmodel(spark, "progs/s_plasma.spr");
	setorigin(spark, self.origin);
	spark.think = exploderun;
	spark.scale = 0.7;
	if ((self.model == "progs/ccc.md3"))
	{
		spark.colormod = '1 0.85 0';
	}
	else if (((self.classname == "hiplaser") || (self.model == "progs/lasrspik.mdl")))
	{
		spark.colormod = '1 0 0';
	}
	else
	{
		spark.colormod = '1 0.4 0';
	}
	spark.effects = (spark.effects + EF_ADDITIVE);
	spark.nextthink = time;
};

void() HIP_LaserTouch =
{
	local vector org;
	local vector spot1;
	local vector spot2;
	local vector oldvel;
	local float r;

	self.owner = world;
	self.cnt = (self.cnt + 1);
	if (((pointcontents(self.origin) == CONTENT_SKY) || (pointcontents(self.origin) == CONTENT_SOLID)))
	{
		remove(self);
		return;
	}
	oldvel = normalize(self.old_velocity);
	spot1 = self.origin - (16 * oldvel);
	spot2 = self.origin + (16 * oldvel);
	traceline(spot1, spot2, FALSE, self);
	self.origin = trace_endpos;
	org = self.origin;
	if (other.health)
	{
		if ((self.lastvictim == other))
		{
			self.dmg = (self.dmg / 2);
		}
		spawn_touchblood(self.dmg);
		if ((other.health < 22))
		{
			T_Damage(other, self, self.lastvictim, (self.dmg * 10));
		}
		else
		{
			T_Damage(other, self, self.lastvictim, self.dmg);
		}
		sendParticle("ccc_impact", org, VEC_ORIGIN, 1);
		laserdie();
	}
	else
	{
		if (((self.cnt == 3) || (random() < 0.15)))
		{
			sendParticle("ccc_impact", org, VEC_ORIGIN, 1);
			laserdie();
		}
		else
		{
			self.dmg = (0.9 * self.dmg);
			self.velocity = (oldvel + (2 * trace_plane_normal));
			self.velocity = normalize(self.velocity);
			self.velocity = (self.speed * self.velocity);
			self.old_velocity = self.velocity;
			if ((self.flags & FL_ONGROUND))
			{
				self.flags = (self.flags - FL_ONGROUND);
			}
			r = random();
			sound7(self, CHAN_WEAPON, "floathead/boing.wav", 1, ATTN_STATIC, SNDSPD);
			return;
		}
	}
	sound(self, CHAN_WEAPON, "weapons/goostick.wav", 1, ATTN_STATIC);
	remove(self);
};

void() HIP_LaserThink =
{
	local vector a;

	if ((time > self.attack_finished))
	{
		remove(self);
		return;
	}
	if ((self.flags & FL_ONGROUND))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
	self.velocity = self.old_velocity;
	a = vectoangles(self.velocity);
	self.angles_x = a_x;		// aim only: keep the roll, it is the C spinning
	self.angles_y = a_y;
	self.nextthink = (time + 0.1);
};

void(vector org, vector vec, float light) HIP_LaunchLaser =
{
	sound7(self, CHAN_WEAPON, "ccc/shoot.wav", 1, ATTN_NORM, SNDSPD);
	vec = normalize(vec);
	newmis = spawn();
	newmis.owner = self;
	newmis.classname = "hiplaser";
	newmis.lastvictim = self;
	newmis.movetype = MOVETYPE_FLYMISSILE;
	newmis.solid = SOLID_BBOX;
	setmodel(newmis, "progs/ccc.md3");		// the CCC gun: a spinning yellow letter C
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, org);
	newmis.effects = EF_FULLBRIGHT;
	newmis.traileffectnum = particleeffectnum("ccc_trail");
	newmis.speed = 1500;
	newmis.dmg = 18;
	newmis.velocity = (vec * newmis.speed);
	newmis.old_velocity = newmis.velocity;
	newmis.angles = vectoangles(newmis.velocity);
	newmis.avelocity = '0 0 400';
	newmis.nextthink = time;
	newmis.attack_finished = (time + 5);
	newmis.think = HIP_LaserThink;
	newmis.touch = HIP_LaserTouch;
	newmis.count = 0;
};

void(float stat) HIP_FireLaser =
{
	local vector org;
	local vector dir;
	local vector out;
	local float ofs;
	local float aofs;

	if (!self.button0)
	{
		self.weaponframe = (self.weaponframe + 1);
		self.nextthink = (time + 0.1);
		player_run();
		return;
	}
	self.weaponframe = (self.weaponframe + 1);
	if ((self.weaponframe >= 7))
	{
		self.weaponframe = 1;
	}
	if ((self.ammo_cells < 1))
	{
		BM_OutOfAmmo();
		return;
	}
	SuperDamageSound();
	self.effects = (self.effects | EF_MUZZLEFLASH);
	makevectors(self.v_angle);
	ofs = 6;
	out = v_forward;
	out = normalize(out);
	if (autocvar_centered_weapons)
	{
		org = (self.origin + ((12 - ofs) * v_up)) + (12 * out);
	}
	else
	{
		org = ((self.origin + ((12 - ofs) * v_up)) + (12 * out)) + (v_right * 5);
	}
	dir = aim(self, 1000);
	aofs = ofs * 0.707;
	if (((stat == 0) && ((self.weaponframe == 1) || (self.weaponframe == 4))))
	{
		self.ammo_cells = (self.ammo_cells - 1);
		self.currentammo = (self.ammo_cells - 1);
		org = org + (aofs * v_right);
		org = org - (aofs * v_up);
		HIP_LaunchLaser(org, dir, 0);
		org = org - ((2 * aofs) * v_right);
		HIP_LaunchLaser(org, dir, 0);
		if (!autocvar_centered_weapons)
		{
			SpawnSmoke_Flash(0.3, '0 35 -17', 1, VEC_ORIGIN, 0.5);
			SpawnSpark_Flash(1.1, '15 -6 -10', '1 0 0.1', 1);
			SpawnSNGFlash('0 23 -18', '1 0.1 0.1');
		}
	}
	else
	{
		if (((stat == 1) && ((self.weaponframe == 1) || (self.weaponframe == 4))))
		{
			if (!autocvar_centered_weapons)
			{
				SpawnSpark_Flash(0.9, '15 -8 11', '1 0 0.1', 1);
				SpawnSmoke_Flash(0.3, '0 24 -15', 1, VEC_ORIGIN, 0.7);
				SpawnSNGFlash('0 17 -13', '1 0.1 0.1');
			}
			self.ammo_cells = (self.ammo_cells - 1);
			self.currentammo = (self.ammo_cells - 1);
			org = org + (ofs * v_up);
			if ((random() < 0.1))
			{
				HIP_LaunchLaser(org, dir, 1);
				newmis.dmg = 25;
			}
			else
			{
				HIP_LaunchLaser(org, dir, 0);
			}
		}
	}
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = (-1.5 - random());
	}
	self.nextthink = (time + 0.035);
};

float() crandom =
{
	return ((2 * (random() - 0.5)));
};

void(vector org, vector vel) SpawnMeatSpray_eviltexture =
{
	local entity missile;
	local float zufall;

	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = 0;
	makevectors(self.angles);
	missile.velocity_x = ((vel_x * crandom()) * 2.5);
	missile.velocity_y = ((vel_y * crandom()) * 2.5);
	missile.velocity_z = ((vel_z + 130) + (100 * random()));
	missile.avelocity = '3000 1000 2000';
	zufall = random();
	if ((zufall > 0.8))
	{
		missile.scale = 1.6;
	}
	else
	{
		if ((zufall > 0.6))
		{
			missile.scale = 1.3;
		}
		else
		{
			if ((zufall > 0.4))
			{
				missile.scale = 1;
			}
			else
			{
				if ((zufall > 0.2))
				{
					missile.scale = 0.7;
				}
				else
				{
					missile.scale = 0.4;
				}
			}
		}
	}
	missile.nextthink = (time + 1);
	missile.think = SUB_Remove;
	setmodel(missile, "progs/zom_gib.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(missile, org);
};

void() meleeaxe =
{
	self.weaponmodel = "progs/v_boot.mdl";
	sound7(self, CHAN_WEAPON, "weapons/ax1.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
	self.attack_finished = (time + 0.5);
	self.meleeing = 1;
	self.attack_timer = 0;
	if ((random() < 0.5))
	{
		if ((self.weapon == IT_AXE))
		{
			melee_kickax1();
		}
		else
		{
			melee_kick1();
		}
	}
	else
	{
		if ((self.weapon == IT_AXE))
		{
			melee_kickax6();
		}
		else
		{
			melee_kick6();
		}
	}
	W_FireAxe2();
};

void() W_FireAxe =
{
	local vector source;
	local vector org;
	local float zufall;
	local vector pushback1;
	local vector direc;
	local entity axeforce;
	local vector axevec;
	local vector dir;
	local float berserkrand;
	local float extraforce;
	local float surfnum;
	local float zu;
	local string s;
	local vector face_spawn_pos;
	local vector face_spawn_vel;
	local float surfacenum;
	local string tex;

	direc = aim(self, 100);
	traceline(self.origin, (self.origin + (direc * 2)), FALSE, self);
	pushback1 = trace_endpos - self.origin;
	if ((self.velocity_z >= 0))
	{
		if (!(self.flags & FL_ONGROUND))
		{
			pushback1 = pushback1 * 1.5;
		}
	}
	else
	{
		if (((self.velocity_z < -5) && (self.velocity_z > -400)))
		{
		}
		else
		{
		}
	}
	makevectors(self.v_angle);
	source = self.origin + '0 0 20';
	tracebox(source, '-1 -1 -2', '1 1 2', (source + (v_forward * 75)), FALSE, self);
	if ((trace_fraction == 1))
	{
		traceline(source, (source + (v_forward * 75)), FALSE, self);
		if ((trace_fraction == 1))
		{
			return;
		}
	}
	if (((0 > (trace_ent.origin_z + 16)) && (trace_ent != world)))
	{
		trace_ent.hitbox_pos = HEAD_SHOT;
	}
	dir = aim(self, 1000);
	axevec = (trace_endpos - self.origin) + (normalize(dir) * 80);
	axeforce = Gyro_Force_Create("axe_hit", self.origin);
	Gyro_Force_ApplyFalloff_ConeLinear(axeforce, axevec, 20, 20);
	if ((self.meleeing == 1))
	{
		if ((autocvar_berserkmode > 1))
		{
			extraforce = 35;
		}
		if (!(self.flags & FL_ONGROUND))
		{
			extraforce = extraforce + 15;
		}
		self.velocity = (self.velocity - (pushback1 * 35));
		if ((trace_ent.flags & FL_MONSTER))
		{
			setorigin(trace_ent, (trace_ent.origin + '0 0 5'));
			trace_ent.flags = (trace_ent.flags - FL_ONGROUND);
			trace_ent.velocity = ((trace_ent.velocity + (v_forward * (70 + extraforce))) + (v_up * 100));
			if (((trace_ent.classname == "monster_shalrath") && (random() < 0.5)))
			{
			}
			else
			{
				if ((trace_ent.pain_finished > (time + (3.6 + random()))))
				{
				}
				else
				{
					trace_ent.pain_finished = (time - 1.5);
				}
			}
		}
		if (!(self.flags & FL_ONGROUND))
		{
			Gyro_Force_ApplyAffector_Directional(axeforce, axevec, (1500 + (autocvar_berserkmode * 195)), FALSE);
		}
		else
		{
			Gyro_Force_ApplyAffector_Directional(axeforce, axevec, (1400 + (autocvar_berserkmode * 150)), FALSE);
		}
	}
	else
	{
		if ((trace_ent.flags & FL_MONSTER))
		{
			random();
			if ((random() < (0.3 + (autocvar_berserkmode * 0.05))))
			{
				trace_ent.pain_finished = (time - 1.5);
			}
		}
		Gyro_Force_ApplyAffector_Directional(axeforce, axevec, 5, FALSE);
	}
	Gyro_Force_AddProperty_Instant(axeforce);
	Gyro_Force_Ignore(axeforce, self);
	org = trace_endpos - (v_forward * 4);
	if ((autocvar_berserkmode > 1))
	{
		berserkrand = random();
		if (((self.weapon == IT_AXE) && (self.meleeing == 0)))
		{
			berserkrand = berserkrand + -0.16;
			if ((random() < 0.9))
			{
				berserkrand = berserkrand - (random() * 0.2);
			}
		}
	}
	else
	{
		berserkrand = 0;
		if (((self.weapon == IT_AXE) && (self.meleeing == 0)))
		{
			berserkrand = -0.16;
			if ((random() < 0.9))
			{
				berserkrand = berserkrand - (random() * 0.2);
			}
		}
	}
	if ((trace_ent.inflamed == 1))
	{
		sound7(other, CHAN_WEAPON, "kickgib/gib_hit.wav", 1, ATTN_NORM, SNDSPD);
	}
	if (trace_ent.takedamage)
	{
		if ((autocvar_shootablebuttonsandsecrets != 0))
		{
			if ((trace_ent.classtype == CT_FUNCBREAK))
			{
				if (((trace_ent.noise == "boss2/pop2.wav") || (trace_ent.noise == "blob/death1.wav")))
				{
					sound(self, CHAN_WEAPON, "player/axeflesh3.wav", 1, ATTN_NORM);
				}
				if ((trace_ent.style == BTYPE_WOOD))
				{
					sound(self, CHAN_AUTO, SOUND_AXE_WOOD, 1, ATTN_NORM);
				}
				else
				{
					if ((trace_ent.style == BTYPE_GLASS))
					{
						sound(self, CHAN_WEAPON, SOUND_AXE_GLASS, 1, ATTN_NORM);
					}
					else
					{
						if ((trace_ent.style == BTYPE_METAL))
						{
							sound(self, CHAN_WEAPON, SOUND_AXE_METAL, 1, ATTN_NORM);
						}
						else
						{
							sound(self, CHAN_WEAPON, SOUND_AXE_STONE, 1, ATTN_NORM);
						}
					}
				}
			}
			if ((((((trace_ent.takedamage != DAMAGE_AIM) && (trace_ent.classname != "monster_hell_knight")) && (trace_ent.classname != "monster_enforcer")) && (trace_ent.classname != "monster_reiver")) && (trace_ent.classname != "monster_oldone")))
			{
				if ((autocvar_shootablebuttonsandsecrets == 1))
				{
					sendParticle("secret", org, VEC_ORIGIN, 1);
				}
				else
				{
					sendParticle("TE_GUNSHOT", org, VEC_ORIGIN, 1);
				}
				if ((trace_ent.classtype != CT_FUNCBREAK))
				{
					sound(self, CHAN_WEAPON, "player/axhit2.wav", 1, ATTN_NORM);
				}
				T_Damage(trace_ent, self, self, (autocvar_player_axe * (autocvar_berserkmode - berserkrand)));
				return;
			}
			if (((trace_ent.model == "maps/b_explob.bsp") || (trace_ent.model == "maps/b_exbox2.bsp")))
			{
				sound(self, CHAN_WEAPON, "player/axhit2.wav", 1, ATTN_NORM);
				T_Damage(trace_ent, self, self, (autocvar_player_axe * (autocvar_berserkmode - berserkrand)));
				return;
			}
		}
		trace_ent.axhitme = 1;
		SpawnBlood(org, VEC_ORIGIN, 20);
		SpawnMeatSpray(((self.origin + (v_forward * 30)) + (v_up * -10)), ((v_right * -75) + (v_up * -10)));
		sound7(other, CHAN_WEAPON, "kickgib/gib_hit.wav", 1, ATTN_NORM, SNDSPD);
		if ((autocvar_zombienewmodelproperties >= 1))
		{
			if (((trace_ent.classname == "monster_zombie") && (trace_ent.monstermodel == 2)))
			{
				if ((trace_ent.axehitcount < 2))
				{
					T_Damage(trace_ent, self, self, (autocvar_player_axe * (autocvar_berserkmode - berserkrand)));
				}
				else
				{
					T_Damage(trace_ent, self, self, 500);
				}
			}
			else
			{
				T_Damage(trace_ent, self, self, (autocvar_player_axe * (autocvar_berserkmode - berserkrand)));
			}
		}
		else
		{
			T_Damage(trace_ent, self, self, (autocvar_player_axe * (autocvar_berserkmode - berserkrand)));
		}
		zufall = random();
		if ((self.meleeing == 1))
		{
			if ((zufall > 0.66))
			{
				sound7(self, CHAN_WEAPON, "player/kickflesh.wav", 0.7, ATTN_NORM);
			}
			else
			{
				sound7(self, CHAN_WEAPON, "player/kickflesh2.wav", 0.7, ATTN_NORM, SNDSPD);
			}
		}
		else
		{
			if ((zufall > 0.66))
			{
				sound7(self, CHAN_WEAPON, "player/axeflesh1.wav", 0.7, ATTN_NORM, SNDSPD);
			}
			else
			{
				if ((zufall < 0.34))
				{
					sound7(self, CHAN_WEAPON, "player/axeflesh2.wav", 0.7, ATTN_NORM, SNDSPD);
				}
				else
				{
					sound7(self, CHAN_WEAPON, "player/axeflesh3.wav", 0.7, ATTN_NORM, SNDSPD);
				}
			}
		}
		if ((autocvar_fleshsplat == 1))
		{
			ThrowBloodSplat(dir, trace_endpos, trace_ent);
			ThrowBloodSplat(dir, trace_endpos, trace_ent);
		}
	}
	else
	{
		if (autocvar_evil_faces)
		{
			surfnum = getsurfacenearpoint(world, trace_endpos);
			if ((surfnum >= 0))
			{
				s = getsurfacetexture(world, surfnum);
				if (((((((s == "altarb_1") || (s == "altarb_2")) || (s == "dem4_1")) || (s == "dem4_4")) || (s == "dem5_3")) || (s == "demc4_4")))
				{
					SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
					SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
					SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
					SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
					SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
					SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
					SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
					SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
					SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
					SpawnBlood(org, VEC_ORIGIN, 20);
					zu = random();
					if ((zu > 0.66))
					{
						sound(self, CHAN_WEAPON, "player/axeflesh1.wav", 0.7, ATTN_NORM);
					}
					else
					{
						if ((zu < 0.34))
						{
							sound(self, CHAN_WEAPON, "player/axeflesh2.wav", 0.7, ATTN_NORM);
						}
						else
						{
							sound(self, CHAN_WEAPON, "player/axeflesh3.wav", 0.7, ATTN_NORM);
						}
					}
					if ((facetime < time))
					{
						facetime = time + 2;
						face_spawn_pos = trace_endpos - (trace_plane_normal * 20);
						face_spawn_vel = normalize(trace_plane_normal);
						face_spawn_vel = face_spawn_vel * 10;
						spawn_face(face_spawn_pos, face_spawn_vel, 1);
					}
					return;
				}
			}
		}
		if (((trace_ent.inflamed == 1) && (trace_ent.inflamekillafterdeath == 0)))
		{
			trace_ent.health = -1;
			trace_ent.inflamekillafterdeath = 1;
			random();
			if ((random() < (0.15 + ((autocvar_player_axe * (autocvar_berserkmode - berserkrand)) * 0.005))))
			{
				trace_ent.health = (-25 - (autocvar_player_axe * (autocvar_berserkmode - berserkrand)));
			}
			else
			{
				trace_ent.health = -1;
			}
			spawn_touchblood(9);
			trace_ent.nextthink = time;
			trace_ent.think = trace_ent.th_die;
			sound7(trace_ent, CHAN_WEAPON, "kickgib/gib_hit.wav", 1, ATTN_NORM, SNDSPD);
			return;
		}
		surfacenum = getsurfacenearpoint(world, org);
		if ((surfacenum >= 0))
		{
			tex = getsurfacetexture(world, surfacenum);
			if ((returnsurface(tex) == GROUND))
			{
				sendParticle("TE_DIRT", org, VEC_ORIGIN, 1);
				sound7(self, CHAN_AUTO, "player/kickhitw.wav", 1, ATTN_NORM, SNDSPD);
				return;
			}
			else
			{
				if ((returnsurface(tex) == MEAT))
				{
					sendParticle("TE_BLOOD", org, VEC_ORIGIN, 1);
					sound7(self, CHAN_WEAPON, "kickgib/gib_hit.wav", 1, ATTN_NORM, SNDSPD);
					return;
				}
				else
				{
					if ((returnsurface(tex) == VOID))
					{
						return;
					}
				}
			}
		}
		if ((self.meleeing == 1))
		{
			sound7(self, CHAN_AUTO, "player/kickhitw.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_WEAPON, "player/axhit2.wav", 1, ATTN_NORM, SNDSPD);
		}
		if ((self.meleeing == 1))
		{
			sendParticle("TE_DIRT", org, VEC_ORIGIN, 1);
		}
		else
		{
			WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
			WriteByte(MSG_BROADCAST, TE_GUNSHOT);
			WriteCoord(MSG_BROADCAST, org_x);
			WriteCoord(MSG_BROADCAST, 0);
			WriteCoord(MSG_BROADCAST, 0);
		}
	}
};

void() W_FireAxe2 =
{
	local vector source;
	local vector org;
	local float berserkrand;
	local float zufall;

	makevectors(self.v_angle);
	source = self.origin + '0 0 16';
	traceline(source, (source + (v_forward * 75)), FALSE, self);
	if ((trace_fraction == 1))
	{
		return;
	}
	org = trace_endpos - (v_forward * 4);
	if ((autocvar_berserkmode > 1))
	{
		berserkrand = random();
		if (((self.weapon == IT_AXE) && (self.meleeing == 0)))
		{
			berserkrand = berserkrand + -0.16;
		}
	}
	else
	{
		berserkrand = 0;
		if (((self.weapon == IT_AXE) && (self.meleeing == 0)))
		{
			berserkrand = -0.16;
		}
	}
	if (trace_ent.i_am_a_corpse)
	{
		SpawnBlood(org, VEC_ORIGIN, 20);
		T_Damage(trace_ent, self, self, (autocvar_player_axe * (autocvar_berserkmode - berserkrand)));
		zufall = random();
		if ((zufall > 0.66))
		{
			sound7(self, CHAN_WEAPON, "player/axeflesh1.wav", 0.7, ATTN_NORM, SNDSPD);
		}
		else
		{
			if ((zufall < 0.34))
			{
				sound7(self, CHAN_WEAPON, "player/axeflesh2.wav", 0.7, ATTN_NORM, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_WEAPON, "player/axeflesh3.wav", 0.7, ATTN_NORM, SNDSPD);
			}
		}
	}
};

vector() wall_velocity =
{
	local vector vel;

	vel = normalize(self.velocity);
	vel = normalize(((vel + (v_up * (random() - 0.5))) + (v_right * (random() - 0.5))));
	vel = vel + (2 * trace_plane_normal);
	vel = vel * 200;
	return (vel);
};

void(vector org, vector vel) SpawnMeatSpray =
{
	local entity missile;

	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = 0;
	makevectors(self.angles);
	missile.velocity = vel;
	missile.velocity_z = ((missile.velocity_z + 250) + (50 * random()));
	missile.avelocity = '3000 1000 2000';
	missile.nextthink = (time + 1);
	missile.think = SUB_Remove;
	setmodel(missile, "progs/zom_gib.mdl");
	missile.traileffectnum = particleeffectnum(/*25826i*/"gibnull");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(missile, org);
};

void(vector org, vector vel, float damage) SpawnBlood =
{
	if (trace_ent.veh_kind)
	{
		sendParticle("TE_GUNSHOT", org, VEC_ORIGIN, 1);
		return;
	}
	if ((((trace_ent.classname == "ShalrathMissile") || (trace_ent.classname == "monster_jim")) || (trace_ent.classname == "func_breakable")))
	{
		sendParticle("TE_GUNSHOT", org, VEC_ORIGIN, 1);
		return;
	}
	if ((trace_ent.dodge_finished < time))
	{
		particle(org, (vel * 0.1), 73, (damage * 2));
	}
};

void(float damage) spawn_touchblood =
{
	local vector vel;

	vel = wall_velocity() * 0.2;
	SpawnBlood((self.origin + (vel * 0.01)), vel, damage);
};

void(vector org, vector vel) SpawnChunk =
{
	particle(org, (vel * 0.02), 0, 10);
};

.entity	chsaw_enemy;		// player: the living thing the saw has bitten, he is stuck to it (world = not stuck)
.float	chsaw_end;			// player: the stuck saw lets go at this time whatever happens
.vector	chsaw_dir;			// player: the horizontal direction he is stuck from, away from the enemy

void() W_FireSaw =
{
	local vector source;
	local vector org;
	local float surfacenum;
	local string tex;

	makevectors(self.v_angle);
	source = self.origin + '0 0 16';
	traceline(source, (source + (v_forward * 82)), FALSE, self);
	if ((trace_fraction == 1))
	{
		return;
	}
	if (((0 > (trace_ent.origin_z + 16)) && (trace_ent != world)))
	{
		trace_ent.hitbox_pos = HEAD_SHOT;
	}
	org = trace_endpos - (v_forward * 4);
	if (trace_ent.takedamage)
	{
		trace_ent.axhitme = 2;
		if (((trace_ent.health > 0) && ((trace_ent.classname == "player") || (trace_ent.flags & FL_MONSTER))) && (self.chsaw_enemy == world))
		{
			// the saw has bitten something alive: he is stuck to it, chainsawing it, until it dies (see Saw_LockFrame)
			self.chsaw_enemy = trace_ent;
			self.chsaw_end = time + 15;
			self.chsaw_dir = self.origin - trace_ent.origin;
			self.chsaw_dir_z = 0;
			self.chsaw_dir = normalize (self.chsaw_dir);
		}
		if (((trace_ent.classname == "func_breakable") || (trace_ent.classname == "light_fluoropost")))
		{
			sendParticle("TE_SUPERSPIKE", org, VEC_ORIGIN, 1);
		}
		else
		{
			if (((random() < 0.825) && (((((trace_ent.classname == "monster_hell_knight") || (trace_ent.classname == "monster_hell_knight2")) || (((trace_ent.classname == "monster_ogre") && (trace_ent.skin == 1)) && (trace_ent.hitbox_pos != HEAD_SHOT))) || (trace_ent.classname == "monster_jim")) || (trace_ent.classname == "monster_freddie"))))
			{
				sound7(self, CHAN_ITEM, "weapons/saw_metal.wav", 0.6, ATTN_NORM, SNDSPD);
				WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
				WriteByte(MSG_BROADCAST, TE_SPIKE);
				WriteCoord(MSG_BROADCAST, org_x);
				WriteCoord(MSG_BROADCAST, 0);
				WriteCoord(MSG_BROADCAST, 0);
				ThrowBloodSplat((v_forward * 2), trace_endpos, trace_ent);
				SpawnMeatSpray((self.origin + (v_forward * 16)), ((((random() * 300) - 150) * v_right) + (100 * v_forward)));
			}
			else
			{
				SpawnBlood(trace_endpos, '0 0 5', 20);
				ThrowBloodSplat((v_forward * 2), trace_endpos, trace_ent);
				SpawnMeatSpray((self.origin + (v_forward * 16)), ((((random() * 300) - 150) * v_right) + (100 * v_forward)));
				if ((random() > 0.5))
				{
					CeilSplat();
				}
				sendParticle("blood_saw", org, VEC_ORIGIN, 1);
			}
		}
		if (((((trace_ent.model == "progs/zombie_noarms.mdl") || (trace_ent.model == "progs/zombie1_noarms.mdl")) || (trace_ent.model == "progs/zombie_new.mdl")) || (trace_ent.meleeattack > 7)))
		{
			T_Damage(trace_ent, self, self, 65);
		}
		if ((deathmatch == 1))
		{
			T_Damage(trace_ent, self, self, 25);
		}
		else
		{
			if ((((trace_ent.classname == "monster_hell_knight") || (trace_ent.classname == "monster_hell_knight2")) || ((trace_ent.classname == "monster_ogre") && (trace_ent.skin == 1))))
			{
				if ((random() < 0.08))
				{
					trace_ent.pain_finished = (time - 1.5);
				}
				T_Damage(trace_ent, self, self, 10);
			}
			else
			{
				if ((random() < 0.22))
				{
					trace_ent.pain_finished = (time - 1.5);
				}
				T_Damage(trace_ent, self, self, 13);
			}
		}
		if ((trace_ent != world))
		{
			trace_ent.velocity = (trace_ent.velocity * 0.5);
		}
		if (((trace_ent.classname != "func_breakable") && (trace_ent.classname != "light_fluoropost")))
		{
			sound7(self, CHAN_WEAPON, "weapons/sawguts.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
		}
	}
	else
	{
		surfacenum = getsurfacenearpoint(world, org);
		if ((surfacenum >= 0))
		{
			tex = getsurfacetexture(world, surfacenum);
			if ((returnsurface(tex) == GROUND))
			{
				sendParticle("TE_DIRT", org, VEC_ORIGIN, 1);
				return;
			}
			else
			{
				if ((returnsurface(tex) == MEAT))
				{
					sendParticle("TE_BLOOD", org, VEC_ORIGIN, 1);
					return;
				}
				else
				{
					if ((returnsurface(tex) == VOID))
					{
						return;
					}
				}
			}
		}
		sound7(self, CHAN_ITEM, "weapons/saw_metal.wav", 0.6, ATTN_NORM, SNDSPD);
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte(MSG_BROADCAST, TE_SPIKE);
		WriteCoord(MSG_BROADCAST, org_x);
		WriteCoord(MSG_BROADCAST, 0);
		WriteCoord(MSG_BROADCAST, 0);
	}
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -2;
	}
	self.attack_finished = (time + 0.1);
};

// stuck to a chainsawed enemy: he stays beside it, faces it and keeps sawing it on his own, until it dies, he switches away
// from the saw, he dies, or 15 s pass. TRUE while he is stuck (W_WeaponFrame does nothing else then).
float() Saw_LockFrame =
{
	local entity	e;
	local vector	pos;

	e = self.chsaw_enemy;
	if (e == world)
		return FALSE;
	if (self.weapon != IT_CHAINSAW || self.health <= 0 || e.health <= 0 || time > self.chsaw_end)
	{
		self.chsaw_enemy = world;
		return FALSE;
	}
	pos = e.origin + self.chsaw_dir * 40;
	pos_z = self.origin_z;
	setorigin (self, pos);
	self.velocity = '0 0 0';
	self.v_angle_y = vectoyaw (e.origin - self.origin);
	self.fixangle = TRUE;
	if (time >= self.attack_finished)
		W_FireSaw ();
	return TRUE;
};

void() ClearMultiDamage =
{
	multi_ent = world;
	multi_damage = 0;
};

void() ApplyMultiDamage =
{
	if (!multi_ent)
	{
		return;
	}
	T_Damage(multi_ent, self, self, multi_damage);
};

void(entity hit, float damage) AddMultiDamage =
{
	if (!hit)
	{
		return;
	}
	if ((hit != multi_ent))
	{
		ApplyMultiDamage();
		multi_damage = damage;
		multi_ent = hit;
	}
	else
	{
		multi_damage = multi_damage + damage;
	}
};

void(float damage, vector dir) TraceAttack =
{
	local vector vel;
	local vector org;
	local entity ric2;
	local float resist;
	local float surfnum;
	local string s;
	local vector face_spawn_pos;
	local vector face_spawn_vel;
	local float surfacenum;
	local string tex;
	local entity ric;

	vel = normalize(((dir + (v_up * crandom())) + (v_right * crandom())));
	vel = vel + (2 * trace_plane_normal);
	vel = vel * 200;
	org = trace_endpos - (dir * 4);
	if (trace_ent.takedamage)
	{
		if (trace_ent.veh_kind)
		{
			sendParticle("TE_GUNSHOT", org, VEC_ORIGIN, 1);
			AddMultiDamage(trace_ent, damage);
			return;
		}
		if ((0 > (trace_ent.origin_z + 16)))
		{
			trace_ent.hitbox_pos = HEAD_SHOT;
		}
		if (((random() < 0.01) && (self.weapon == IT_SHOTGUN)))
		{
			trace_ent.pain_finished = (time - 1.5);
			damage = damage + 8;
		}
		if ((autocvar_shootablebuttonsandsecrets != 0))
		{
			if ((((((trace_ent.takedamage != DAMAGE_AIM) && (trace_ent.classname != "monster_hell_knight2")) && (trace_ent.classname != "monster_enforcer")) && (trace_ent.classname != "monster_reiver")) && (trace_ent.classname != "monster_oldone")))
			{
				if ((autocvar_shootablebuttonsandsecrets == 1))
				{
					if ((self.weapon == IT_SUPER_SHOTGUN))
					{
						sendParticle("secret_shot2", org, VEC_ORIGIN, 1);
					}
					else
					{
						sendParticle("secret_shot1", org, VEC_ORIGIN, 1);
					}
				}
				else
				{
					sendParticle("TE_GUNSHOT", org, VEC_ORIGIN, 1);
				}
				AddMultiDamage(trace_ent, damage);
				return;
			}
			if (((trace_ent.model == "maps/b_explob.bsp") || (trace_ent.model == "maps/b_exbox2.bsp")))
			{
				AddMultiDamage(trace_ent, damage);
				return;
			}
		}
		if (!(coop & !deathmatch))
		{
			ric2 = spawn();
			ric2.origin = (trace_endpos + '0 0 24');
			ric2.think = SUB_Remove;
			ric2.nextthink = (time + 0.1);
			sound7(ric2, CHAN_ITEM, "player/kickflesh2.wav", 0.9, ATTN_NORM, SNDSPD);
		}
		if ((trace_ent.classname == "monster_spider"))
		{
			resist = autocvar_spider_attack_resistance * 0.01;
			if ((random() > resist))
			{
				SpawnBlood(org, (vel * 0.2), damage);
				AddMultiDamage(trace_ent, damage);
			}
			else
			{
				return;
			}
		}
		else
		{
			SpawnBlood(org, (vel * 0.2), damage);
			AddMultiDamage(trace_ent, damage);
		}
		if ((autocvar_fleshsplat == 1))
		{
			if ((trace_ent.classname == "monster_wizard"))
			{
				ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1065353216i, (entity)0i);
			}
			else
			{
				if ((trace_ent.classname == "monster_army"))
				{
					ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1073741824i, (entity)0i);
				}
				else
				{
					if ((trace_ent.classname == "monster_ogre"))
					{
						ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1073741824i, (entity)0i);
					}
					else
					{
						if ((trace_ent.classname == "monster_hell_knight"))
						{
							ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1073741824i, (entity)0i);
							sendParticle("sparks", org, VEC_ORIGIN, 1);
						}
						else
						{
							if ((trace_ent.classname == "monster_hell_knight2"))
							{
								sendParticle("sparks", org, VEC_ORIGIN, 1);
								if ((trace_ent.dodge_finished < time))
								{
									ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1073741824i, (entity)0i);
								}
							}
							else
							{
								if ((trace_ent.classname == "monster_enforcer"))
								{
									if ((trace_ent.dodge_finished < time))
									{
										ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1073741824i, (entity)0i);
									}
								}
								else
								{
									if ((trace_ent.classname == "monster_reiver"))
									{
										if ((trace_ent.dodge_finished < time))
										{
											ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1073741824i, (entity)0i);
										}
									}
									else
									{
										if ((trace_ent.classname == "monster_knight"))
										{
											ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1073741824i, (entity)0i);
											sendParticle("sparks", org, VEC_ORIGIN, 1);
										}
										else
										{
											if ((trace_ent.classname == "monster_demon1"))
											{
												ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1077936128i, (entity)0i);
											}
											else
											{
												if ((trace_ent.classname == "monster_dog"))
												{
													ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1073741824i, (entity)0i);
												}
												else
												{
													if ((trace_ent.classname == "monster_shalrath"))
													{
														ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1082130432i, (entity)0i);
													}
													else
													{
														if ((trace_ent.classname == "monster_tarbaby"))
														{
															ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1084227584i, (entity)0i);
														}
														else
														{
															if ((trace_ent.classname == "monster_shambler"))
															{
																ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1073741824i, (entity)0i);
															}
															else
															{
																ThrowBloodSplat(dir, trace_endpos, trace_ent, (entity)1073741824i, (entity)0i);
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
			ThrowBloodSplat(dir, trace_endpos, trace_ent);
		}
	}
	else
	{
		if (autocvar_evil_faces)
		{
			surfnum = getsurfacenearpoint(world, trace_endpos);
			if ((surfnum >= 0))
			{
				s = getsurfacetexture(world, surfnum);
				if (((((((s == "altarb_1") || (s == "altarb_2")) || (s == "dem4_1")) || (s == "dem4_4")) || (s == "dem5_3")) || (s == "demc4_4")))
				{
					SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
					SpawnBlood(org, VEC_ORIGIN, 5);
					if ((facetime < time))
					{
						facetime = time + 2;
						face_spawn_pos = trace_endpos - (trace_plane_normal * 20);
						face_spawn_vel = normalize(trace_plane_normal);
						face_spawn_vel = face_spawn_vel * 10;
						spawn_face(face_spawn_pos, face_spawn_vel, 1);
					}
					return;
				}
			}
		}
		surfacenum = getsurfacenearpoint(world, trace_endpos);
		if ((surfacenum >= 0))
		{
			tex = getsurfacetexture(world, surfacenum);
			if (((tex == "sky1") || (tex == "sky4")))
			{
				return;
			}
		}
		if (((trace_ent.inflamed == 1) && (trace_ent.inflamekillafterdeath == 0)))
		{
			trace_ent.health = -1;
			trace_ent.inflamekillafterdeath = 1;
			random();
			if ((random() < (0.15 + (damage * 0.005))))
			{
				trace_ent.health = (-25 - damage);
			}
			else
			{
				trace_ent.health = -1;
			}
			spawn_touchblood(9);
			trace_ent.nextthink = time;
			trace_ent.think = trace_ent.th_die;
			sound7(trace_ent, CHAN_WEAPON, "kickgib/gib_hit.wav", 1, ATTN_NORM, SNDSPD);
			return;
		}
		surfacenum = getsurfacenearpoint(world, org);
		if ((surfacenum >= 0))
		{
			tex = getsurfacetexture(world, surfacenum);
			if ((returnsurface(tex) == GROUND))
			{
				sendParticle("TE_DIRT", org, VEC_ORIGIN, 1);
				return;
			}
			else
			{
				if ((returnsurface(tex) == MEAT))
				{
					sendParticle("TE_BLOOD", org, VEC_ORIGIN, 1);
					return;
				}
				else
				{
					if ((returnsurface(tex) == VOID))
					{
						return;
					}
				}
			}
		}
		if ((!coop && !deathmatch))
		{
			ric = spawn();
			ric.origin = trace_endpos;
			ric.think = SUB_Remove;
			ric.nextthink = (time + 0.1);
			if ((random() < 0.5))
			{
				sound7(ric, CHAN_AUTO, "weapons/ric1.wav", 0.7, ATTN_NORM, SNDSPD);
			}
			else
			{
				sound7(ric, CHAN_AUTO, "weapons/ric3.wav", 0.7, ATTN_NORM, SNDSPD);
			}
		}
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte(MSG_BROADCAST, TE_GUNSHOT);
		WriteCoord(MSG_BROADCAST, org_x);
		WriteCoord(MSG_BROADCAST, 0);
		WriteCoord(MSG_BROADCAST, 0);
	}
};

void(vector org) spawn_splash =
{
	local entity en;

	en = spawn();
	setorigin(en, org);
	en.nextthink = (time + 1);
	en.think = SUB_Remove;
	sendParticle("watersplash", org, VEC_ORIGIN, 1);
	precache_sound("player/watersplash.wav");
	sound(en, CHAN_VOICE, "player/watersplash.wav", 0.8, ATTN_IDLE);
};

void(vector org) spawn_lavasplash =
{
	local entity en;

	en = spawn();
	setorigin(en, org);
	en.nextthink = (time + 1);
	en.think = SUB_Remove;
	sendParticle("lavasplash", org, VEC_ORIGIN, 1);
	precache_sound("ambience/lavasplash_shotgun.wav");
	sound(en, CHAN_VOICE, "ambience/lavasplash_shotgun.wav", 0.8, ATTN_IDLE);
};

void(vector dir) W_BulletSplash =
{
	local vector shot_src;
	local float steps;
	local float stepsize;
	local float shot_length;
	local float old_contents;

	shot_length = 2048;
	stepsize = 2;
	steps = shot_length / stepsize;
	shot_src = self.origin + (v_forward * 10);
	if ((((pointcontents(shot_src) == CONTENT_WATER) || (pointcontents(shot_src) == CONTENT_SLIME)) || (pointcontents(shot_src) == CONTENT_LAVA)))
	{
		return;
	}
	old_contents = pointcontents(shot_src);
	traceline(shot_src, (shot_src + (dir * shot_length)), FALSE, self);
	if (trace_inwater)
	{
		while ((steps > 0))
		{
			shot_src = shot_src + (dir * stepsize);
			if ((((pointcontents(shot_src) == CONTENT_WATER) || (pointcontents(shot_src) == CONTENT_SLIME)) && (old_contents != CONTENT_WATER)))
			{
				spawn_splash(shot_src);
				return;
			}
			if (((pointcontents(shot_src) == CONTENT_LAVA) && (old_contents != CONTENT_WATER)))
			{
				spawn_lavasplash(shot_src);
				return;
			}
			steps = steps - 1;
		}
	}
};

void(vector org, vector dir) launch_bullet =
{

	newmis = spawn();
	newmis.cansplash = TRUE;
	newmis.owner = self;
	newmis.movetype = MOVETYPE_FLYMISSILE;
	newmis.solid = SOLID_BBOX;
	newmis.angles = vectoangles(dir);
	newmis.touch = bullet_enemy_touch;
	newmis.classname = "playershot";
	newmis.think = SUB_Remove;
	newmis.nextthink = (time + 20);
	newmis.traileffectnum = particleeffectnum(/*26067i*/"spike_bubble_trail");
	newmis.nextthink = (time + 6);
	newmis.effects = EF_FULLBRIGHT;
	setmodel(newmis, "progs/bullettr.mdl");
	if (((self.waterlevel >= 3) && (cvar("slowmo") > 0.9)))
	{
		newmis.alpha = 0.01;
	}
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, org);
	if ((cvar("slowmo") > 0.7))
	{
		newmis.velocity = (dir * 2000);
	}
	else
	{
		newmis.velocity = (dir * self.bulletspeed);
	}
};

void() FireBullets_Projectile =
{
	local vector dir;
	local vector org;
	local float randomdir1;
	local float randomdir2;
	local float randomdir3;
	local entity buckshot;
	local vector align;
	local vector shotvec;

	if (autocvar_centered_weapons)
	{
		org = (self.origin + self.view_ofs) + (v_up * -8);
	}
	else
	{
		org = ((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * 9);
	}
	dir = aim(self, 1000);
	randomdir1 = (random() * -0.04) + 0.02;
	randomdir2 = (random() * -0.09) + 0.05;
	randomdir3 = (random() * 0.03) + -0.03;
	if ((self.weapon == IT_SUPER_SHOTGUN))
	{
		launch_bullet(org, (dir + (v_right * 0.1)));
		launch_bullet(org, (dir + (v_right * -0.1)));
		launch_bullet(org, ((dir + (v_up * 0.06)) + (v_right * randomdir1)));
		launch_bullet(org, ((dir + (v_up * -0.03)) + (v_right * 0.01)));
		launch_bullet(org, (dir + (v_up * 0.01)));
		launch_bullet(org, ((dir + (v_up * -0.02)) + (v_right * randomdir1)));
		launch_bullet(org, (dir + (v_right * 0.1)));
		launch_bullet(org, (dir + (v_right * -0.1)));
		launch_bullet(org, ((dir + (v_up * 0.06)) + (v_right * randomdir2)));
		launch_bullet(org, ((dir + (v_up * -0.03)) + (v_right * (0 - randomdir3))));
		launch_bullet(org, (dir + (v_up * -0.03)));
		launch_bullet(org, ((dir + (v_up * -0.02)) + (v_right * randomdir2)));
		launch_bullet(org, (dir + (v_up * randomdir2)));
		launch_bullet(org, (dir + (v_right * (0 - randomdir2))));
	}
	else
	{
		launch_bullet(org, (dir + (v_right * (0 - randomdir3))));
		launch_bullet(org, (dir + (v_right * randomdir3)));
		launch_bullet(org, (dir + (v_right * -0.02)));
		launch_bullet(org, (dir + v_right));
		launch_bullet(org, ((dir + (v_up * randomdir2)) + (v_right * randomdir1)));
		launch_bullet(org, ((dir + (v_up * randomdir2)) + (v_right * 0.01)));
		launch_bullet(org, (dir + (v_up * 0.01)));
		launch_bullet(org, ((dir + (v_up * (0 - randomdir3))) + (v_right * (0 - randomdir3))));
	}
	makevectors(self.v_angle);
	align = dir + (v_up * 0.27);
	traceline(self.origin, (self.origin + (align * 200)), FALSE, self);
	shotvec = (trace_endpos - self.origin) + (normalize(dir) * 80);
	buckshot = Gyro_Force_Create("shothit", self.origin);
	Gyro_Force_ApplyFalloff_ConeLinear(buckshot, shotvec, 16, 16);
	Gyro_Force_ApplyAffector_Directional(buckshot, shotvec, 2, FALSE);
	Gyro_Force_AddProperty_Instant(buckshot);
	Gyro_Force_Ignore(buckshot, self);
};

void(float shotcount, vector dir, vector spread) FireBullets =
{
	local vector direction;
	local vector src;
	local float crit;
	local entity shot;
	local vector shotvector;
	local vector align;

	makevectors(self.v_angle);
	if ((((cvar("slowmo") < 0.9) || (autocvar_bullet_projectiles == 1)) || (self.waterlevel >= 3)))
	{
		FireBullets_Projectile();
		return;
	}
	src = self.origin + (v_forward * 10);
	if ((random() <= 0.01))
	{
		crit = 1;
	}
	ClearMultiDamage();
	while ((shotcount > 0))
	{
		direction = (dir + ((crandom() * spread_x) * v_right)) + ((crandom() * spread_y) * v_up);
		traceline(src, (src + (direction * 2048)), FALSE, self);
		if ((trace_fraction != 1))
		{
			TraceAttack((autocvar_player_shotgun_pellets + crit), direction);
		}
		shotcount = shotcount - 1;
		if ((trace_ent.classname == "monster_reiver"))
		{
		}
		else
		{
			W_BulletSplash(direction);
			align = dir + (v_up * 0.25);
			traceline(self.origin, (self.origin + (align * 200)), FALSE, self);
			shotvector = (trace_endpos - self.origin) + (normalize(dir) * 80);
			shot = Gyro_Force_Create("gunshot", self.origin);
			Gyro_Force_ApplyFalloff_ConeLinear(shot, shotvector, 18, 18);
			if ((self.weapon == IT_SUPER_SHOTGUN))
			{
				Gyro_Force_ApplyAffector_Directional(shot, shotvector, 85, FALSE);
			}
			else
			{
				Gyro_Force_ApplyAffector_Directional(shot, shotvector, 105, FALSE);
			}
			Gyro_Force_AddProperty_Instant(shot);
			Gyro_Force_Ignore(shot, self);
		}
	}
	ApplyMultiDamage();
};

void() FireBullets_Projectiles_Enemy =
{
	local vector dir;
	local vector org;
	local entity en;

	ai_face();
	en = self.enemy;
	if (autocvar_skill_adjusted_soldier_aiming)
	{
		if ((skill == 2))
		{
			dir = en.origin + (en.velocity * 0.1);
		}
		else
		{
			dir = en.origin + (en.velocity * 0.05);
		}
	}
	else
	{
		dir = en.origin;
	}
	org = ((self.origin + (v_up * 12)) - (v_right * 12)) + (v_forward * 19);
	dir = normalize((dir - org));
	makevectors(self.angles);
	if ((self.classname == "monster_army"))
	{
		launch_enemy_bullet(org, (dir + (v_right * 0.1)));
		launch_enemy_bullet(org, (dir + (v_right * -0.1)));
		launch_enemy_bullet(org, ((dir + (v_up * 0.06)) + (v_right * -0.02)));
		launch_enemy_bullet(org, ((dir + (v_up * -0.03)) + (v_right * 0.01)));
	}
	else
	{
		if ((self.classname == "monster_enforcer"))
		{
			launch_enemy_bullet((org + (v_right * 17)), (dir + (v_right * 0.1)));
			launch_enemy_bullet((org + (v_right * 17)), (dir + (v_right * -0.1)));
			launch_enemy_bullet((org + (v_right * 17)), ((dir + (v_up * 0.06)) + (v_right * -0.02)));
			launch_enemy_bullet((org + (v_right * 17)), ((dir + (v_up * -0.03)) + (v_right * 0.01)));
			launch_enemy_bullet((org + (v_right * 17)), (dir + (v_right * 0.12)));
			launch_enemy_bullet((org + (v_right * 17)), (dir + (v_right * -0.07)));
			launch_enemy_bullet((org + (v_right * 17)), ((dir + (v_up * 0.09)) + (v_right * -0.03)));
			launch_enemy_bullet((org + (v_right * 17)), ((dir + (v_up * -0.05)) + (v_right * 0.03)));
		}
	}
};

void(float shotcount, vector dir, vector spread) FireBullets_soldier =
{
	local vector direction;
	local vector src;
	local entity shot;
	local vector shotvector;
	local vector align;

	if (((cvar("slowmo") < 0.9) || (autocvar_bullet_projectiles == 1)))
	{
		FireBullets_Projectiles_Enemy();
		return;
	}
	makevectors(self.v_angle);
	src = self.origin + (v_forward * 10);
	ClearMultiDamage();
	while ((shotcount > 0))
	{
		direction = (dir + ((crandom() * spread_x) * v_right)) + ((crandom() * spread_y) * v_up);
		traceline(src, (src + (direction * 2048)), FALSE, self);
		if ((trace_fraction != 1))
		{
			if ((autocvar_soldier_size_influenced_attack == 1))
			{
				TraceAttack((autocvar_soldier_gun * self.scale), direction);
			}
			else
			{
				TraceAttack(autocvar_soldier_gun, direction);
			}
		}
		W_BulletSplash(direction);
		shotcount = shotcount - 1;
		align = dir + (v_up * 0.25);
		traceline(self.origin, (self.origin + (align * 200)), FALSE, self);
		shotvector = (trace_endpos - self.origin) + (normalize(dir) * 80);
		shot = Gyro_Force_Create("gunshot", self.origin);
		Gyro_Force_ApplyFalloff_ConeLinear(shot, shotvector, 18, 18);
		if ((self.weapon == IT_SUPER_SHOTGUN))
		{
			Gyro_Force_ApplyAffector_Directional(shot, shotvector, 88, FALSE);
		}
		else
		{
			Gyro_Force_ApplyAffector_Directional(shot, shotvector, 130, FALSE);
		}
		Gyro_Force_AddProperty_Instant(shot);
		Gyro_Force_Ignore(shot, self);
	}
	ApplyMultiDamage();
};

void() updateSNG =
{
	if (((self.owner.health <= 0) || intermission_running))
	{
		remove(self);
		return;
	}
	if ((((self.owner.weapon == IT_SUPER_NAILGUN) && (self.owner.meleeing == 0)) && (self.owner.throwing == 0)))
	{
		if (autocvar_centered_weapons)
		{
			setmodel(self, string_null);	// v_nail2_barrel_cleared
		}
		else
		{
			setmodel(self, string_null);
		}
	}
	else
	{
		setmodel(self, string_null);
	}
	if ((self.owner.weapon == IT_SUPER_NAILGUN))
	{
		if (((self.owner.button0 && (self.alpha < 1)) && (self.owner.waterlevel != 3)))
		{
			self.alpha = (self.alpha + 0.002);
		}
		else
		{
			if ((self.alpha >= 0))
			{
				self.alpha = (self.alpha - 0.001);
				if ((self.owner.waterlevel == 3))
				{
					self.alpha = (self.alpha - 0.0125);
				}
			}
		}
	}
	if ((!self.owner.button0 && (self.owner.weapon == IT_SUPER_NAILGUN)))
	{
		if ((((random() * 100) < 2) && (self.alpha > 0.6)))
		{
			Sprite_Emitter(self.owner, "progs/s_smoke_muzz.spr", ((random() * 0.02) + 0.02), '23 -5 -6', '1 1 0.2', '5 1 0.3', 0.4, TYPE_STANDARD);
		}
		if ((((random() * 100) < 7) && (self.alpha > 0.5)))
		{
			Sprite_Emitter(self.owner, "progs/s_gunsmoke.spr", ((random() * 0.05) + 0.1), '36 -5 -9', '0 0 1', VEC_ORIGIN, 0.4, TYPE_STANDARD);
		}
	}
	if (((self.owner.button0 || ((self.owner.velocity != VEC_ORIGIN) && (self.owner.earthquake_finished < time))) || self.owner.super_damage_finished))
	{
		self.origin = self.owner.gunof;
		self.angles = self.owner.gunang;
		self.weapon_anim_x_offset_downwards = self.owner.weapon_anim_x_offset_downwards;
		self.weapon_anim_y_offset_downwards = self.owner.weapon_anim_y_offset_downwards;
		self.weapon_anim_z_offset_downwards = self.owner.weapon_anim_z_offset_downwards;
		self.weapon_anim_x_angles_downwards = self.owner.weapon_anim_x_angles_downwards;
		self.weapon_anim_y_angles_downwards = self.owner.weapon_anim_y_angles_downwards;
		self.weapon_anim_z_angles_downwards = self.owner.weapon_anim_z_angles_downwards;
	}
	else
	{
		self.origin = self.owner.gunof;
		self.angles = self.owner.gunang;
		self.weapon_anim_x_offset_downwards = self.owner.weapon_anim_x_offset_downwards;
		self.weapon_anim_y_offset_downwards = self.owner.weapon_anim_y_offset_downwards;
		self.weapon_anim_z_offset_downwards = self.owner.weapon_anim_z_offset_downwards;
		self.weapon_anim_x_angles_downwards = self.owner.weapon_anim_x_angles_downwards;
		self.weapon_anim_y_angles_downwards = self.owner.weapon_anim_y_angles_downwards;
		self.weapon_anim_z_angles_downwards = self.owner.weapon_anim_z_angles_downwards;
	}
	self.frame = self.owner.weaponframe;
	self.think = updateSNG;
	self.nextthink = time;
};

void() SNGHeater =
{
	local entity sngb;

	sngb = spawn();
	sngb.movetype = 0;
	sngb.solid = 0;
	sngb.viewmodelforclient = self;
	sngb.owner = self;
	sngb.classname = "barrelheat";
	if ((self.weapon == IT_SUPER_NAILGUN))
	{
		if (autocvar_centered_weapons)
		{
			setmodel(sngb, string_null);
		}
		else
		{
			setmodel(sngb, string_null);
		}
	}
	sngb.alpha = 0.01;
	sngb.scale = 1;
	setsize(sngb, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(sngb, '4 -6 5');
	sngb.think = updateSNG;
	sngb.nextthink = (time + 0.01);
};

void() W_FireShotgun =
{
	local vector dir;
	local vector pushback1;
	local vector direc;

	sound7(self, CHAN_WEAPON, "weapons/shotgn2.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
	if (((autocvar_muzzleflash == 1) && !autocvar_centered_weapons))
	{
		if (cvar("chase_active"))
		{
			sendParticle("shotgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -10.5)) + (v_right * 4)) + (v_forward * 15)), (self.velocity * 50), 1);
		}
		else
		{
			if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
			{
				sendParticle("shotgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_forward * 30)) + (v_right * 7)), (self.velocity * 50), 1);
			}
			else
			{
				if ((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable))
				{
					sendParticle("shotgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_forward * 30)) + (v_right * autocvar_weapon_position_adjustable_muzzleflash_shot1_offset)), (self.velocity * 50), 1);
				}
				else
				{
					sendParticle("shotgun_muzzleflash", (((self.origin + self.view_ofs) + (v_up * -8)) + (v_forward * 30)), (self.velocity * 50), 1);
				}
			}
		}
	}
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -3.3;
	}
	SpawnMuzzleFlash();
	SpawnSpark_Flash(1, '15 -13 25', '1 0.7 0.4', 1);
	if ((self.waterlevel >= 3))
	{
		Sprite_Emitter(self, "progs/s_bubble.spr", 2, '20 -13 -20', '320 30 -10', '25 18 10', 0.7, TYPE_SMOKE);
		Sprite_Emitter(self, "progs/s_bubble.spr", 2, '20 -13 -20', '150 -10 -30', '25 18 10', 0.7, TYPE_SMOKE);
	}
	if ((autocvar_pushback != 0))
	{
		direc = aim(self, 100);
		traceline(self.origin, (self.origin + (direc * autocvar_pushbackshot1)), FALSE, self);
		pushback1 = trace_endpos - self.origin;
		self.velocity = (self.velocity - pushback1);
	}
	self.ammo_shells = (self.ammo_shells - 1);
	self.currentammo = (self.ammo_shells - 1);
	dir = aim(self, 100000);
	FireBullets(8, dir, '0.04 0.04 0');
};

void() W_FireSuperShotgun =
{
	local vector dir;
	local vector pushback1;
	local vector direc;

	if ((self.currentammo == 1))
	{
		W_FireShotgun();
		return;
	}
	if (autocvar_qc_ssg)
	{
		sound7(self, CHAN_WEAPON, "weapons/ssg2.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
	}
	else
	{
		sound7(self, CHAN_WEAPON, "weapons/shotgn2.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
	}
	if (((autocvar_muzzleflash == 1) && !autocvar_centered_weapons))
	{
		if (cvar("chase_active"))
		{
			sendParticle("double_shotgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_right * -1.5)) + (v_forward * 17)) + (v_up * -5)), (self.velocity * 50), 1);
		}
		else
		{
			if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
			{
				sendParticle("double_shotgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_forward * 20)) + (v_right * 6)), (self.velocity * 50), 1);
			}
			else
			{
				if ((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable))
				{
					sendParticle("double_shotgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_forward * 20)) + (v_right * autocvar_weapon_position_adjustable_muzzleflash_shot2_offset)), (self.velocity * 50), 1);
				}
				else
				{
					sendParticle("double_shotgun_muzzleflash", (((self.origin + self.view_ofs) + (v_up * -8)) + (v_forward * 20)), (self.velocity * 50), 1);
				}
			}
		}
	}
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -5;
	}
	SpawnSSGFlash();
	SpawnSpark_Flash(1, '15 -18 19', '1 0.8 1', 1);
	SpawnSmoke_Flash(1, '5 0 13', 1, '0.5 0.5 0.5', 0.5);
	if ((self.waterlevel >= 3))
	{
		Sprite_Emitter(self, "progs/s_bubble.spr", 2, '20 -18 -20', '320 30 -10', '25 18 10', 0.7, TYPE_SMOKE);
		Sprite_Emitter(self, "progs/s_bubble.spr", 2, '20 -18 -20', '150 -10 -30', '25 18 10', 0.7, TYPE_SMOKE);
	}
	if ((autocvar_pushback != 0))
	{
		direc = aim(self, 100);
		traceline(self.origin, (self.origin + (direc * autocvar_pushbackshot2)), FALSE, self);
		pushback1 = trace_endpos - self.origin;
		self.velocity = (self.velocity - (pushback1 * 0.5));
	}
	self.ammo_shells = (self.ammo_shells - 2);
	self.currentammo = (self.ammo_shells - 2);
	dir = aim(self, 100000);
	FireBullets(14, dir, '0.11 0.08 0');
};

void() s_explode1 = [ 0, s_explode2 ]
{
};

void() s_explode2 = [ 1, s_explode3 ]
{
};

void() s_explode3 = [ 2, s_explode4 ]
{
};

void() s_explode4 = [ 3, s_explode5 ]
{
};

void() s_explode5 = [ 4, s_explode6 ]
{
};

void() s_explode6 = [ 5, SUB_Remove ]
{
};

void() exploderun =
{
	self.frame = (self.frame + 1);
	self.think = exploderun;
	if ((self.frame <= 2))
	{
		exp_check_collision();
	}
	if ((self.model == "progs/s_explodbigp.spr"))
	{
		self.nextthink = (time + 0.05);
		if ((self.frame >= 13))
		{
			remove(self);
		}
	}
	else
	{
		if ((self.model == "progs/s_plasma.spr"))
		{
			self.nextthink = (time + 0.08);
			if ((self.frame >= 6))
			{
				remove(self);
			}
		}
		else
		{
			self.nextthink = (time + 0.055);
			if ((self.frame >= 16))
			{
				remove(self);
			}
		}
	}
};

void() screenshake =
{
	local entity plyr;
	local float d;

	if ((autocvar_effects_explosion_shake == 0))
	{
		return;
	}
	if ((self.attack_finished < time))
	{
		return;
	}
	plyr = findradius(self.origin, 600);
	while (plyr)
	{
		if ((plyr.flags & FL_CLIENT))
		{
			d = vlen((self.origin - plyr.origin));
			d = (1300 - d) / 180;
			if ((d > 0))
			{
				plyr.punchangle_x = (-1 * (((random() * 2) + -1) + (0.05 * d)));
				plyr.punchangle_y = (-1 * (((random() * 2) + -1) + (0.05 * d)));
				plyr.punchangle_z = (-1 * (((random() * 4) + -2) + (0.05 * d)));
			}
		}
		plyr = plyr.chain;
	}
	self.nextthink = (time + 0.1);
	self.think = screenshake;
};

void() BecomeExplosion =
{
	local entity explod;
	local entity shake;

	explod = spawn();
	explod.movetype = MOVETYPE_NOCLIP;
	explod.velocity = '0 0 60';
	explod.touch = SUB_Null;
	explod.solid = 0;
	if ((((pointcontents(self.origin) == CONTENT_WATER) || (pointcontents(self.origin) == CONTENT_SLIME)) || (pointcontents(self.origin) == CONTENT_LAVA)))
	{
		explod.alpha = 0.3;
	}
	else
	{
		explod.alpha = 0.8;
	}
	explod.scale = 1.1;
	if ((self.classname != "light_destruct"))
	{
		shake = spawn();
		setorigin(shake, (self.origin + '0 0 15'));
		shake.think = screenshake;
		shake.attack_finished = (time + 0.3);
		shake.nextthink = (time + 0.1);
		if ((self.classname == "resistexp"))
		{
			setmodel(explod, "progs/s_smoke.spr");
		}
		else
		{
			if ((self.classname == "misc_explobox"))
			{
				if ((random() > 0.3))
				{
					setmodel(explod, "progs/s_explodbigp.spr");
				}
				else
				{
					setmodel(explod, "progs/s_explodbig.spr");
				}
				explod.scale = 1.4;
			}
			else
			{
				setmodel(explod, "progs/s_explodbig.spr");
				if ((self.classname == "proximity_grenade"))
				{
					explod.scale = 1.3;
				}
				else
				{
					explod.scale = 1.05;
				}
			}
		}
		if (((self.classname == "slimeball") || (self.netname == "slimeball")))
		{
			setmodel(explod, "progs/s_explodbigp.spr");
			explod.colormod = '1 2 0';
			explod.scale = 0.6;
			explod.alpha = 0.7;
			explod.velocity = '0 0 40';
		}
		if ((self.classname == "monster_tarbaby"))
		{
			setmodel(explod, "progs/s_explodbigp.spr");
			explod.colormod = '0.3 0 2';
			explod.scale = 0.9;
			explod.alpha = 0.7;
		}
	}
	setorigin(explod, (self.origin + '0 0 15'));
	explod.frame = 0;
	explod.think = exploderun;
	explod.nextthink = (time + 0.1);
	self.movetype = 0;
	self.velocity = VEC_ORIGIN;
	self.touch = SUB_Null;
	setmodel(self, "progs/s_explod.spr");
	self.solid = 0;
	s_explode1();
};

void() T_MissileTouch =
{
	local float damg;
	local vector detonate;
	local float surfacenum;
	local string tex;
	local float surfnum;
	local string s;
	local vector backwards;
	local vector face_spawn_pos;
	local vector face_spawn_vel;

	if ((other == self.owner))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	surfacenum = getsurfacenearpoint(world, self.origin);
	if ((surfacenum >= 0))
	{
		tex = getsurfacetexture(world, surfacenum);
		if (((tex == "sky1") || (tex == "sky4")))
		{
			remove(self);
			return;
		}
	}
	if ((other.inflamed == 1))
	{
		other.health = -100;
		other.enemy = self.owner;
		other.nextthink = time;
		other.think = other.th_die;
	}
	if (((random() * 100) < 20))
	{
		spawn_fire();
	}
	if (autocvar_evil_faces)
	{
		surfnum = getsurfacenearpoint(world, self.origin);
		if ((surfnum >= 0))
		{
			s = getsurfacetexture(world, surfnum);
			if (((((((s == "altarb_1") || (s == "altarb_2")) || (s == "dem4_1")) || (s == "dem4_4")) || (s == "dem5_3")) || (s == "demc4_4")))
			{
				backwards = self.origin;
				backwards = backwards - (8 * normalize(self.velocity));
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnBlood(backwards, VEC_ORIGIN, 17);
				sound(self, CHAN_AUTO, "zombie/z_hit.wav", 1, ATTN_NORM);
				if ((facetime < time))
				{
					facetime = time + 2;
					face_spawn_vel = normalize(trace_plane_normal);
					face_spawn_vel = face_spawn_vel * 10;
					makevectors(self.angles);
					face_spawn_pos = self.origin - (trace_plane_normal * 20);
					spawn_face(face_spawn_pos, face_spawn_vel, 0);
				}
				remove(self);
				return;
			}
		}
	}
	damg = 100 + (random() * 20);
	if ((autocvar_explosiondebris == 0))
	{
		if (other.health)
		{
			if (((other.classname == "monster_shambler") || (other.classname == "monster_hell_knight2")))
			{
				damg = damg * 0.65;
			}
			T_Damage(other, self, self.owner, damg);
			detonate = self.origin;
			detonate = detonate - (8 * normalize(self.velocity));
			if (((other.classname == "monster_shambler") || (other.classname == "monster_hell_knight2")))
			{
				sendParticle("rocket_resist", self.origin, VEC_ORIGIN, 1);
				self.classname = "resistexp";
				sparklers(1);
			}
			else
			{
				if ((autocvar_effects_classic_explosion == 1))
				{
					sendParticle("rocket_explo_classic", detonate, VEC_ORIGIN, 1);
				}
				else
				{
					sendParticle("rocket_explosion_nodebris", detonate, VEC_ORIGIN, 1);
				}
			}
		}
		else
		{
			detonate = self.origin;
			detonate = detonate - (8 * normalize(self.velocity));
			if ((pointcontents(self.origin) == CONTENT_SLIME))
			{
				sendParticle("slimesplash", detonate, VEC_ORIGIN, 1);
			}
			else
			{
				if ((autocvar_effects_classic_explosion == 1))
				{
					sendParticle("rocket_explo_classic", detonate, VEC_ORIGIN, 1);
				}
				else
				{
					sendParticle("rocket_explosion", detonate, VEC_ORIGIN, 1);
				}
			}
		}
	}
	else
	{
		if (other.health)
		{
			if (((other.classname == "monster_shambler") || (other.classname == "monster_hell_knight2")))
			{
				sendParticle("rocket_resist", self.origin, VEC_ORIGIN, 1);
				sparklers(1);
				sparklers(1);
				self.classname = "resistexp";
				damg = damg * 0.65;
			}
			else
			{
				sparklers(2);
			}
			if ((self.classname != "jimrocket"))
			{
				T_Damage(other, self, self.owner, damg);
			}
		}
		detonate = self.origin;
		detonate = detonate - (8 * normalize(self.velocity));
		if ((pointcontents(self.origin) == CONTENT_SLIME))
		{
			sendParticle("slimesplash", detonate, VEC_ORIGIN, 1);
		}
		else
		{
			if ((autocvar_effects_classic_explosion == 1))
			{
				sendParticle("rocket_explo_classic", detonate, VEC_ORIGIN, 1);
			}
			else
			{
				sendParticle("rocket_explosion", detonate, VEC_ORIGIN, 1);
			}
		}
	}
	if ((self.classname == "jimrocket"))
	{
		T_RadiusDamage(self, self.owner, 49, world);
	}
	else
	{
		T_RadiusDamage(self, self.owner, autocvar_player_rocket_radius, other);
	}
	if ((((pointcontents(self.origin) == CONTENT_WATER) || (pointcontents(self.origin) == CONTENT_SLIME)) || (pointcontents(self.origin) == CONTENT_LAVA)))
	{
		sound7(self, CHAN_WEAPON, "weapons/xpld_wat.wav", 1, ATTN_NORM, (SNDSPD - 10));
		sound7(self, CHAN_AUTO, "weapons/explodedist.wav", 0.5, ATTN_NONE, (SNDSPD - 10));
	}
	else
	{
		if ((self.classname == "jimrocket"))
		{
			sound7(self, CHAN_WEAPON, "weapons/proxexp.wav", 1, ATTN_NORM, SNDSPD);
			sound7(self, CHAN_AUTO, "weapons/explodedist.wav", 0.3, ATTN_NONE, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
			sound7(self, CHAN_AUTO, "weapons/explodedist.wav", 0.3, ATTN_NONE, SNDSPD);
		}
	}
	sparklers();
	BecomeExplosion();
};

void() T_MissileTouch_chton =
{
	local float damg;
	local vector detonate;
	local float surfacenum;
	local string tex;
	local float surfnum;
	local string s;
	local vector backwards;
	local vector face_spawn_pos;
	local vector face_spawn_vel;

	if ((other == self.owner))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	surfacenum = getsurfacenearpoint(world, self.origin);
	if ((surfacenum >= 0))
	{
		tex = getsurfacetexture(world, surfacenum);
		if (((tex == "sky1") || (tex == "sky4")))
		{
			remove(self);
			return;
		}
	}
	if (((random() * 100) < 10))
	{
		spawn_fire();
	}
	if (autocvar_evil_faces)
	{
		surfnum = getsurfacenearpoint(world, self.origin);
		if ((surfnum >= 0))
		{
			s = getsurfacetexture(world, surfnum);
			if (((((((s == "altarb_1") || (s == "altarb_2")) || (s == "dem4_1")) || (s == "dem4_4")) || (s == "dem5_3")) || (s == "demc4_4")))
			{
				backwards = self.origin;
				backwards = backwards - (8 * normalize(self.velocity));
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnBlood(backwards, VEC_ORIGIN, 17);
				sound(self, CHAN_AUTO, "zombie/z_hit.wav", 1, ATTN_NORM);
				if ((facetime < time))
				{
					facetime = time + 2;
					face_spawn_vel = normalize(trace_plane_normal);
					face_spawn_vel = face_spawn_vel * 10;
					makevectors(self.angles);
					face_spawn_pos = self.origin - (trace_plane_normal * 20);
					spawn_face(face_spawn_pos, face_spawn_vel, 0);
				}
				remove(self);
				return;
			}
		}
	}
	damg = autocvar_chton_lavaballs + (random() * 20);
	if ((autocvar_explosiondebris == 0))
	{
		if (other.health)
		{
			if (((other.classname == "monster_shambler") || (other.classname == "monster_hell_knight2")))
			{
				damg = damg * 0.65;
			}
			T_Damage(other, self, self.owner, damg);
			detonate = self.origin;
			detonate = detonate - (8 * normalize(self.velocity));
			sendParticle("cthon_fireball", detonate, VEC_ORIGIN, 1);
		}
		else
		{
			detonate = self.origin;
			detonate = detonate - (8 * normalize(self.velocity));
			sendParticle("cthon_fireball", detonate, VEC_ORIGIN, 1);
		}
	}
	else
	{
		if (other.health)
		{
			if (((other.classname == "monster_shambler") || (other.classname == "monster_hell_knight2")))
			{
				damg = damg * 0.65;
			}
			T_Damage(other, self, self.owner, damg);
		}
		detonate = self.origin;
		detonate = detonate - (8 * normalize(self.velocity));
		sendParticle("cthon_fireball", detonate, VEC_ORIGIN, 1);
	}
	T_RadiusDamage(self, self.owner, 120, other);
	sound(self, CHAN_WEAPON, "boss1/fireball.wav", 1, ATTN_NORM);
	BecomeExplosion();
};

void() W_FireRocket =
{
	local entity missile;
	local vector pushback1;
	local vector direc;

	self.ammo_rockets = (self.ammo_rockets - 1);
	self.currentammo = (self.ammo_rockets - 1);
	sound7(self, CHAN_WEAPON, "weapons/sgun1.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
	sound7(self, CHAN_ITEM, "weapons/rocket2i.wav", 0.9, ATTN_NORM, self.PLR_SNDSPD);
	if ((autocvar_pushback != 0))
	{
		direc = aim(self, 100);
		traceline(self.origin, (self.origin + (direc * autocvar_pushbackrocket)), FALSE, self);
		pushback1 = trace_endpos - self.origin;
		self.velocity = (self.velocity - pushback1);
	}
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -3;
	}
	missile = spawn();
	missile.cansplash = TRUE;
	missile.owner = self;
	missile.movetype = MOVETYPE_FLYMISSILE;
	missile.solid = SOLID_BBOX;
	missile.classname = "missile";
	makevectors(self.v_angle);
	missile.velocity = aim(self, 1000);
	missile.velocity = (missile.velocity * 1000);
	missile.angles = vectoangles(missile.velocity);
	missile.touch = T_MissileTouch;
	missile.nextthink = (time + 5);
	missile.think = SUB_Remove;
	SpawnSpark_Flash(1.3, '5 0 0', '1 0.5 0', 1);
	SpawnRockFlash('5 -15 48', '1 1 0.7');
	setmodel(missile, "progs/missile.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	if (((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
	{
		setorigin(missile, ((((self.origin + self.view_ofs) + (v_forward * 8)) + (v_up * -8)) + (v_right * 6)));
	}
	else
	{
		if (autocvar_centered_weapons)
		{
			setorigin(missile, (((self.origin + self.view_ofs) + (v_forward * 8)) + (v_up * -8)));
		}
		else
		{
			if (((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
			{
				setorigin(missile, ((((self.origin + self.view_ofs) + (v_forward * 8)) + (v_up * -8)) + (v_right * autocvar_weapon_position_adjustable_projectile_rocket_offset)));
			}
			else
			{
				setorigin(missile, ((self.origin + (v_forward * 8)) + '0 0 16'));
			}
		}
	}
};

void(vector p1, vector p2, entity from, float damage) LightningDamage =
{
	local entity e1;
	local entity e2;
	local vector f;
	local vector ziel;
	local entity lightforce;
	local vector lightvec;
	local vector dir;
	local vector align;
	local float surfacenum;
	local string tex;

	f = p2 - p1;
	normalize(f);
	f_x = 0 - 0;
	f = f * 16;
	e2 = world;
	e1 = world;
	traceline(p1, p2, FALSE, self);
	if (trace_ent.takedamage)
	{
		if ((autocvar_shootablebuttonsandsecrets != 0))
		{
			ziel = trace_endpos + '0 0 2';
			if ((((((trace_ent.takedamage != DAMAGE_AIM) && (trace_ent.classname != "monster_hell_knight2")) && (trace_ent.classname != "monster_enforcer")) && (trace_ent.classname != "monster_reiver")) && (trace_ent.classname != "monster_oldone")))
			{
				if ((autocvar_shootablebuttonsandsecrets == 1))
				{
					sendParticle("secret", ziel, VEC_ORIGIN, 1);
				}
				else
				{
					sendParticle("Lightning_gun_impact", ziel, VEC_ORIGIN, 1);
				}
				T_Damage(trace_ent, from, from, damage);
				return;
			}
			if (((trace_ent.model == "maps/b_explob.bsp") || (trace_ent.model == "maps/b_exbox2.bsp")))
			{
				T_Damage(trace_ent, from, from, damage);
				return;
			}
		}
		if (((!coop && !deathmatch) && (self.weapon == IT_LIGHTNING)))
		{
			sound7(self, CHAN_AUTO, "weapons/saw_metal.wav", 0.9, ATTN_NORM, (SNDSPD + -10));
		}
		if (((trace_ent.classname != "ShalrathMissile") && (trace_ent.dodge_finished < time)))
		{
			particle(trace_endpos, '0 0 100', 225, damage);
		}
		T_Damage(trace_ent, from, from, damage);
		if ((self.classname == "player"))
		{
			if ((other.classname == "player"))
			{
				trace_ent.velocity_z = (trace_ent.velocity_z + 400);
			}
		}
		dir = aim(self, 10000);
		align = dir + (v_up * 0.33);
		traceline(p1, (p2 + (align * 200)), FALSE, self);
		lightvec = (trace_endpos - self.origin) + (normalize(dir) * 80);
		lightforce = Gyro_Force_Create("light_hit", self.origin);
		Gyro_Force_ApplyFalloff_ConeLinear(lightforce, lightvec, 20, 20);
		Gyro_Force_ApplyAffector_Directional(lightforce, lightvec, 666, FALSE);
		Gyro_Force_AddProperty_Instant(lightforce);
		Gyro_Force_Ignore(lightforce, self);
	}
	else
	{
		if (((trace_fraction != 1) && !trace_ent.health))
		{
			surfacenum = getsurfacenearpoint(world, trace_endpos);
			if ((surfacenum >= 0))
			{
				tex = getsurfacetexture(world, surfacenum);
				if (((tex == "sky1") || (tex == "sky4")))
				{
					return;
				}
				else
				{
					ziel = trace_endpos;
					sendParticle("Lightning_gun_impact", ziel, VEC_ORIGIN, 1);
				}
			}
		}
	}
	if (((trace_ent.inflamed == 1) && (trace_ent.inflamekillafterdeath == 0)))
	{
		trace_ent.inflamekillafterdeath = 1;
		if ((random() < 0.5))
		{
			trace_ent.health = -80;
		}
		else
		{
			trace_ent.health = -1;
		}
		trace_ent.nextthink = time;
		trace_ent.think = trace_ent.th_die;
		spawn_touchblood(9);
		return;
	}
	e1 = trace_ent;
	traceline((p1 + f), (p2 + f), FALSE, self);
	if (((trace_ent != e1) && trace_ent.takedamage))
	{
		particle(trace_endpos, '0 0 100', 225, (damage * 2));
		T_Damage(trace_ent, from, from, damage);
	}
	e2 = trace_ent;
	traceline((p1 - f), (p2 - f), FALSE, self);
	if ((((trace_ent != e1) && (trace_ent != e2)) && trace_ent.takedamage))
	{
		particle(trace_endpos, '0 0 100', 225, (damage * 2));
		T_Damage(trace_ent, from, from, damage);
	}
};

void() ChainLightningHit =
{
	local vector org;
	local float damage;
	local entity head;

	damage = 0;
	org = self.origin + '0 0 16';
	head = findradius(self.origin, 200);
	while (head)
	{
		if ((head.takedamage && (head.baked != 1)))
		{
			if ((head != self.owner))
			{
				if ((((((((head.classname != "monster_shambler") && (head.classname != "monster_afrit")) && (head.classname != "door")) && (head.classname != "func_breakable")) && (head.classname != "button")) && (head.classname != "trigger_multiple")) && (head.classname != "monster_dfury_boss")))
				{
					WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
					WriteByte(MSG_BROADCAST, TE_LIGHTNING2);
					WriteEntity(MSG_BROADCAST, head);
					WriteCoord(MSG_BROADCAST, org_x);
					WriteCoord(MSG_BROADCAST, 0);
					WriteCoord(MSG_BROADCAST, 0);
					WriteCoord(MSG_BROADCAST, head.origin_x);
					WriteCoord(MSG_BROADCAST, head.origin_y);
					WriteCoord(MSG_BROADCAST, head.origin_z);
					sound7(head, CHAN_WEAPON, "weapons/lhit.wav", 1, ATTN_NORM, SNDSPD);
					damage = 3;
					T_Damage(head, self, self.owner, damage);
				}
			}
		}
		head = head.chain;
	}
	lg_shock_player();
	remove(self);
};

void() W_FireLightning2 =
{
	local entity thunderbolt;

	thunderbolt = spawn();
	thunderbolt.owner = self;
	thunderbolt.movetype = MOVETYPE_FLYMISSILE;
	thunderbolt.solid = SOLID_BBOX;
	thunderbolt.classname = "thunderbolt";
	makevectors(self.v_angle);
	thunderbolt.velocity = aim(self, 10000);
	thunderbolt.velocity = (thunderbolt.velocity * 100000);
	thunderbolt.angles = vectoangles(thunderbolt.velocity);
	thunderbolt.touch = ChainLightningHit;
	thunderbolt.nextthink = (time + 0.5);
	thunderbolt.think = SUB_Remove;
	setsize(thunderbolt, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(thunderbolt, ((self.origin + (v_forward * 8)) + '0 0 4'));
};

void() W_FireLightning =
{
	local vector org;
	local float cells;
	local vector pushback1;
	local vector direc;
	local float surfnum;
	local string s;
	local vector face_spawn_pos;
	local vector face_spawn_vel;

	if ((self.ammo_cells < 1))
	{
		BM_OutOfAmmo();
		return;
	}
	if ((self.waterlevel > 1))
	{
		cells = self.ammo_cells;
		self.ammo_cells = 0;
		W_SetCurrentAmmo();
		T_RadiusDamage(self, self, (35 * cells), world);
		return;
	}
	if ((self.t_width < time))
	{
		sound7(self, CHAN_WEAPON, "weapons/lhit.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
		self.t_width = (time + 0.6);
	}
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -1.1;
	}
	if ((autocvar_pushback != 0))
	{
		direc = aim(self, 100);
		traceline(self.origin, (self.origin + (direc * autocvar_pushbacklight)), FALSE, self);
		pushback1 = trace_endpos - self.origin;
		self.velocity = (self.velocity - pushback1);
	}
	self.ammo_cells = (self.ammo_cells - 0.6);
	self.currentammo = (self.ammo_cells - 0.6);
	if ((((autocvar_weapon_position_right == 1) && !autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
	{
		org = (((self.origin + self.view_ofs) + (v_forward * 8)) + (v_up * -6.5)) + (v_right * 6);
	}
	else
	{
		if (((!autocvar_weapon_position_right && (autocvar_weapon_position_fully_adjustable == 1)) && !cvar("chase_active")))
		{
			org = (((self.origin + self.view_ofs) + (v_forward * 8)) + (v_up * -6.5)) + (v_right * autocvar_weapon_position_adjustable_projectile_lighting_offset);
		}
		else
		{
			org = self.origin + '0 0 16';
		}
	}
	if (!deathmatch)
	{
		traceline(org, (org + (v_forward * 1800)), TRUE, self);
	}
	else
	{
		traceline(org, (org + (v_forward * 600)), TRUE, self);
	}
	if (autocvar_evil_faces)
	{
		surfnum = getsurfacenearpoint(world, trace_endpos);
		if ((surfnum >= 0))
		{
			s = getsurfacetexture(world, surfnum);
			if (((((((s == "altarb_1") || (s == "altarb_2")) || (s == "dem4_1")) || (s == "dem4_4")) || (s == "dem5_3")) || (s == "demc4_4")))
			{
				SpawnMeatSpray_eviltexture(trace_endpos, '50 50 50');
				SpawnBlood(trace_endpos, VEC_ORIGIN, 2);
				if ((facetime < time))
				{
					facetime = time + 2;
					face_spawn_pos = trace_endpos - (trace_plane_normal * 20);
					face_spawn_vel = normalize(trace_plane_normal);
					face_spawn_vel = face_spawn_vel * 10;
					spawn_face(face_spawn_pos, face_spawn_vel, 1);
				}
			}
		}
	}
	if ((autocvar_mage_weapon && !cvar("chase_active")))
	{
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte(MSG_BROADCAST, TE_BEAM);
		WriteEntity(MSG_BROADCAST, self);
		WriteCoord(MSG_BROADCAST, org_x);
		WriteCoord(MSG_BROADCAST, 0);
		WriteCoord(MSG_BROADCAST, 0);
		WriteCoord(MSG_BROADCAST, trace_endpos_x);
		WriteCoord(MSG_BROADCAST, 0);
		WriteCoord(MSG_BROADCAST, 0);
	}
	else
	{
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte(MSG_BROADCAST, TE_LIGHTNING2);
		WriteEntity(MSG_BROADCAST, self);
		WriteCoord(MSG_BROADCAST, org_x);
		WriteCoord(MSG_BROADCAST, 0);
		WriteCoord(MSG_BROADCAST, 0);
		WriteCoord(MSG_BROADCAST, trace_endpos_x);
		WriteCoord(MSG_BROADCAST, 0);
		WriteCoord(MSG_BROADCAST, 0);
	}
	if ((vlen((trace_endpos - self.origin)) > 1200))
	{
		LightningDamage((self.origin + '0 0 12'), (trace_endpos + (v_forward * 4)), self, (autocvar_player_lightninggun * 0.8));
	}
	else
	{
		LightningDamage((self.origin + '0 0 12'), (trace_endpos + (v_forward * 4)), self, autocvar_player_lightninggun);
	}
};

void() GrenadeExplode =
{

	T_RadiusDamage(self, self.owner, (autocvar_player_grenades + 5), world);
	if (((((random() * 100) < 20) && (other.classname != "monster_shambler")) && (other.classname != "monster_hell_knight2")))
	{
		spawn_fire();
	}
	JG_Splash();	// JohnWave's head goes off as a water splash (jg_splash.qc)
	return;
	if (((other.classname == "monster_shambler") || (other.classname == "monster_hell_knight2")))
	{
		sendParticle("rocket_resist", self.origin, VEC_ORIGIN, 1);
		sparklers(1);
		sparklers(1);
	}
	else
	{
		sparklers();
		sparklers(2);
		if ((autocvar_explosiondebris == 0))
		{
			if ((pointcontents(self.origin) == CONTENT_SLIME))
			{
				sendParticle("slimesplash", self.origin, VEC_ORIGIN, 1);
			}
			else
			{
				if ((autocvar_effects_classic_explosion == 1))
				{
					sendParticle("rocket_explo_classic", self.origin, VEC_ORIGIN, 1);
				}
				else
				{
					if (other.health)
					{
						sendParticle("grenade_explosion_nodebris", self.origin, VEC_ORIGIN, 1);
					}
					else
					{
						sendParticle("grenade_explosion", self.origin, VEC_ORIGIN, 1);
					}
				}
			}
		}
		else
		{
			if ((pointcontents(self.origin) == CONTENT_SLIME))
			{
				sendParticle("slimesplash", self.origin, VEC_ORIGIN, 1);
			}
			else
			{
				if ((autocvar_effects_classic_explosion == 1))
				{
					sendParticle("rocket_explo_classic", self.origin, VEC_ORIGIN, 1);
				}
				else
				{
					sendParticle("grenade_explosion", self.origin, VEC_ORIGIN, 1);
				}
			}
		}
	}
	if ((((pointcontents(self.origin) == CONTENT_WATER) || (pointcontents(self.origin) == CONTENT_SLIME)) || (pointcontents(self.origin) == CONTENT_LAVA)))
	{
		sound7(self, CHAN_WEAPON, "weapons/xpld_wat.wav", 1, ATTN_NORM, (SNDSPD - 10));
		sound7(self, CHAN_AUTO, "weapons/explodedist.wav", 0.5, ATTN_NONE, (SNDSPD - 10));
	}
	else
	{
		sound7(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM, SNDSPD);
		sound7(self, CHAN_AUTO, "weapons/explodedist.wav", 0.3, ATTN_NONE, SNDSPD);
	}
	if (((other.classname == "monster_shambler") || (other.classname == "monster_hell_knight2")))
	{
		setmodel(self, "progs/s_smoke.spr");
		self.classname = "resistexp";
		BecomeExplosion();
	}
	else
	{
		BecomeExplosion();
	}
};

void() GrenadeTouch =
{
	local float surfnum;
	local string s;
	local vector backwards;
	local vector face_spawn_pos;
	local vector face_spawn_vel;

	if ((other == self.owner))
	{
		return;
	}
	if ((other.inflamed == 1))
	{
		other.health = -100;
		other.enemy = self.owner;
		other.nextthink = time;
		other.think = other.th_die;
		GrenadeExplode();
		return;
	}
	if ((other.takedamage == DAMAGE_AIM))
	{
		GrenadeExplode();
		return;
	}
	if (autocvar_evil_faces)
	{
		surfnum = getsurfacenearpoint(world, self.origin);
		if ((surfnum >= 0))
		{
			s = getsurfacetexture(world, surfnum);
			if (((((((s == "altarb_1") || (s == "altarb_2")) || (s == "dem4_1")) || (s == "dem4_4")) || (s == "dem5_3")) || (s == "demc4_4")))
			{
				backwards = self.origin;
				backwards = backwards - (8 * normalize(self.velocity));
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnBlood(backwards, VEC_ORIGIN, 17);
				sound(self, CHAN_AUTO, "zombie/z_hit.wav", 1, ATTN_NORM);
				if ((facetime < time))
				{
					facetime = time + 2;
					face_spawn_vel = normalize(trace_plane_normal);
					face_spawn_vel = face_spawn_vel * 10;
					makevectors(self.angles);
					face_spawn_pos = self.origin - (trace_plane_normal * 20);
					spawn_face(face_spawn_pos, face_spawn_vel, 0);
				}
				remove(self);
				return;
			}
		}
	}
	JG_BounceSound();	// voted rubber-ball bounce (jg_splash.qc)
	JG_GrenadeBounce();	// tumble
	if ((self.velocity == VEC_ORIGIN))
	{
		self.avelocity = VEC_ORIGIN;
	}
};

void() GLhitboxes =
{
	local entity glhb;

	JG_GrenadeAnimate();	// face the shooter / lie face up (jg_splash.qc)
	glhb = findradius(self.origin, 12);
	while (glhb)
	{
		if (((glhb.flags & FL_MONSTER) && (glhb.health > 0)))
		{
			glhb.health = (glhb.health - 30);
			self.nextthink = (time + 0.000010);
			self.think = GrenadeExplode;
			return;
		}
		glhb = glhb.chain;
	}
	self.attack_timer = (self.attack_timer + 1);
	self.nextthink = (time + 0.025);
	self.think = GLhitboxes;
	if ((self.attack_timer >= 100))
	{
		self.nextthink = (time + 0.000010);
		self.think = GrenadeExplode;
	}
};

void() W_FireGrenade =
{
	local entity missile;
	local vector pushback1;
	local vector direc;

	self.ammo_rockets = (self.ammo_rockets - 1);
	self.currentammo = (self.ammo_rockets - 1);
	sound7(self, CHAN_WEAPON, "weapons/grenade.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -3;
	}
	if ((autocvar_pushback != 0))
	{
		direc = aim(self, 100);
		traceline(self.origin, (self.origin + (direc * autocvar_pushbackgrenade)), FALSE, self);
		pushback1 = trace_endpos - self.origin;
		self.velocity = (self.velocity - pushback1);
	}
	missile = spawn();
	missile.cansplash = TRUE;
	missile.owner = self;
	missile.movetype = MOVETYPE_BOUNCE;
	missile.solid = SOLID_BBOX;
	missile.classname = "grenade";
	missile.nextthink = (time + 0.1);
	missile.think = GLhitboxes;
	makevectors(self.v_angle);
	if (self.v_angle_x)
	{
		missile.velocity = ((((v_forward * 720) + (v_up * 190)) + ((crandom() * v_right) * 10)) + ((crandom() * v_up) * 10));
	}
	else
	{
		missile.velocity = aim(self, 10000);
		missile.velocity = (missile.velocity * 730);
		missile.velocity_z = 190;
	}
	missile.touch = GrenadeTouch;
	JG_GrenadeLaunch(missile, self.v_angle_y);	// face looks back at you (jg_splash.qc)
	setmodel(missile, "progs/grenade.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	// no barrel smoke on the grenade launcher (was SpawnSmoke_Flash(1.3, VEC_ORIGIN, 1, VEC_ORIGIN, 0.7))
	if (((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
	{
		setorigin(missile, (((self.origin + self.view_ofs) + (v_up * -13)) + (v_right * 6)));
	}
	else
	{
		if (autocvar_centered_weapons)
		{
			setorigin(missile, self.origin);
		}
		else
		{
			if (((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
			{
				setorigin(missile, (((self.origin + self.view_ofs) + (v_up * -13)) + (v_right * autocvar_weapon_position_adjustable_projectile_grenade_offset)));
			}
			else
			{
				setorigin(missile, self.origin);
			}
		}
	}
};

void() ProximityExplode =
{

	if ((self.enemy.sticky && (self.enemy.classname != "player")))
	{
		T_Damage(self.enemy, self, self.owner, 30);
	}
	T_RadiusDamage(self, self.owner, 125, world);
	if ((self.owner.classname == "player"))
	{
		T_RadiusDamage(self, self.owner, 125, self.owner);
	}
	if ((pointcontents(self.origin) == CONTENT_SLIME))
	{
		sendParticle("slimesplash", self.origin, VEC_ORIGIN, 1);
	}
	else
	{
		if ((autocvar_effects_classic_explosion == 1))
		{
			sendParticle("rocket_explo_classic", self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			sendParticle("grenade_explosion", self.origin, VEC_ORIGIN, 1);
		}
	}
	if ((((pointcontents(self.origin) == CONTENT_WATER) || (pointcontents(self.origin) == CONTENT_SLIME)) || (pointcontents(self.origin) == CONTENT_LAVA)))
	{
		sound7(self, CHAN_WEAPON, "weapons/xpld_wat.wav", 1, ATTN_NORM, (SNDSPD - 10));
	}
	else
	{
		sound7(self, CHAN_WEAPON, "weapons/proxexp.wav", 0.8, ATTN_NORM, (SNDSPD - 10));
	}
	sound7(self, CHAN_AUTO, "weapons/explodedist.wav", 0.4, ATTN_NONE, SNDSPD);
	sparklers();
	sparklers(2);
	sparklers(2);
	self.origin_z = (self.origin_z + 5);
	BecomeExplosion();
};

void() ProximityGrenadeExplode =
{
	self.takedamage = 0;
	NumProximityGrenades = NumProximityGrenades - 1;
	self.deathtype = "exploding";
	self.nextthink = (time + 0.5);
	self.owner = self.lastvictim;
	self.think = ProximityExplode;
};

void() ProximityStuckEnemy =
{
	self.ltime = (self.ltime + 1);
	if ((self.ltime == 1))
	{
		sound7(self, CHAN_WEAPON, "hipweap/proxstick.wav", 1, ATTN_NORM, SNDSPD);
		self.enemy.sticky = 1;
		self.movetype = MOVETYPE_BOUNCE;
		self.velocity = (self.velocity * (0.15 + (random() * 0.1)));
		if ((random() < 0.2))
		{
			self.velocity = (self.velocity * (1 + random()));
		}
		self.velocity_z = (self.velocity_z + (20 + (random() * 50)));
		if ((random() < 0.1))
		{
			self.velocity_z = (self.velocity_z + (10 + (random() * 50)));
		}
	}
	if ((self.ltime < 12))
	{
		self.think = ProximityStuckEnemy;
		self.nextthink = (time + 0.1);
		if ((self.ltime == 5))
		{
			sound7(self, CHAN_WEAPON, "hipweap/proxwarn.wav", 0.9, ATTN_NORM, SNDSPD);
		}
	}
	else
	{
		ProximityGrenadeExplode();
		self.think();
		return;
	}
};

void() ProximityGrenadeTouch =
{
	if ((other == self))
	{
		return;
	}
	if ((other.classname == self.classname))
	{
		return;
	}
	self.movetype = MOVETYPE_TOSS;
	if ((self.state == 1))
	{
		return;
	}
	if (((vlen(other.velocity) > 0) && (other.health < 1)))
	{
		ProximityGrenadeExplode();
		self.think();
		return;
	}
	if (((other.takedamage == DAMAGE_AIM) && (other.health > 1)))
	{
		self.enemy = other;
		T_Damage(other, self, self.owner, 10);
		self.enemy.pain_finished = (time - 1.5);
		self.think = ProximityStuckEnemy;
		self.nextthink = (time + 0.04);
		return;
	}
	sound7(self, CHAN_WEAPON, "weapons/bounce.wav", 1, ATTN_NORM, SNDSPD);
	self.movetype = 0;
	setsize(self, '-8 -8 -8', '8 8 8');
	self.state = 1;
	self.spawnmaster = other;
};

void() ProximityBomb =
{
	local entity head;
	local float blowup;

	if (self.has_fired)
	{
		sound(self, CHAN_WEAPON, "hipweap/proxwarn.wav", 0.75, ATTN_IDLE, (SNDSPD + 20));
	}
	self.has_fired = !self.has_fired;
	if ((((time > self.delay) || (NumProximityGrenades > 15)) || (vlen(self.spawnmaster.velocity) > 0)))
	{
		ProximityGrenadeExplode();
		self.think();
		return;
	}
	self.owner = world;
	self.takedamage = DAMAGE_YES;
	head = findradius(self.origin, 140);
	blowup = 0;
	while (head)
	{
		if (((((head != self) && (head.health > 0)) && (head.flags & 40)) && (head.classname != self.classname)))
		{
			blowup = 1;
		}
		if (((head.classname == self.classname) && (head.state == 0)))
		{
			blowup = 1;
		}
		traceline(self.origin, head.origin, TRUE, self);
		if (((trace_fraction != 1) || (head == self.owner)))
		{
			blowup = 0;
		}
		if ((blowup == 1))
		{
			sound7(self, CHAN_WEAPON, "hipweap/proxwarn.wav", 0.9, ATTN_NORM, SNDSPD);
			ProximityGrenadeExplode();
			self.nextthink = (time + 0.5);
			return;
		}
		head = head.chain;
	}
	self.nextthink = (time + 0.3);
};

void() W_FireProximityGrenade =
{
	local entity missile;

	NumProximityGrenades = NumProximityGrenades + 1;
	self.grenade_ammo = (self.grenade_ammo - 1);
	missile = spawn();
	missile.owner = self;
	missile.lastvictim = self;
	missile.movetype = MOVETYPE_TOSS;
	missile.solid = SOLID_BBOX;
	missile.classname = "proximity_grenade";
	missile.takedamage = 0;
	missile.health = 5;
	missile.state = 0;
	missile.scale = 0.9;
	makevectors(self.v_angle);
	if (self.v_angle_x)
	{
		missile.velocity = ((((v_forward * 720) + (v_up * 190)) + ((crandom() * v_right) * 10)) + ((crandom() * v_up) * 10));
	}
	else
	{
		missile.velocity = aim(self, 10000);
		missile.velocity = (missile.velocity * 720);
		missile.velocity_z = 190;
	}
	missile.avelocity = '100 600 100';
	missile.angles = vectoangles(missile.velocity);
	missile.touch = ProximityGrenadeTouch;
	missile.nextthink = (time + 2);
	missile.delay = ((time + 15) + (10 * random()));
	missile.think = ProximityBomb;
	missile.th_die = ProximityGrenadeExplode;
	setmodel(missile, "progs/proxbomb.mdl");
	setorigin(missile, (self.origin + (v_right * 8)));
	setsize(missile, '-1 -1 -1', '1 1 1');
};

void(vector org, vector dir) launch_enemy_spike =
{
	newmis = spawn();
	newmis.owner = self;
	newmis.movetype = MOVETYPE_FLY;
	newmis.solid = SOLID_BBOX;
	newmis.angles = vectoangles(dir);
	newmis.touch = spike_enemy_touch;
	newmis.classname = "spike";
	newmis.think = SUB_Remove;
	newmis.nextthink = (time + 6);
	setmodel(newmis, "progs/spike.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, org);
	newmis.velocity = (dir * 1000);
};

void() bullet_enemy_touch =
{
	local float crit;
	local float surfacenum;
	local string tex;

	if ((other == self.owner))
	{
		return;
	}
	if ((other.solid == SOLID_TRIGGER))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	if (other.takedamage)
	{
		if ((random() <= 0.01))
		{
			crit = 1;
		}
		if (((other.flags & FL_MONSTER) || (other.flags & FL_CLIENT)))
		{
			if ((other.flags & FL_MONSTER))
			{
				spawn_touchblood(13);
			}
			else
			{
				spawn_touchblood(9);
			}
		}
		if ((self.classname == "playershot"))
		{
			T_Damage(other, self, self.owner, (autocvar_player_shotgun_pellets + crit));
		}
		else
		{
			T_Damage(other, self, self.owner, 5);
		}
	}
	else
	{
		surfacenum = getsurfacenearpoint(world, self.origin);
		if ((surfacenum >= 0))
		{
			tex = getsurfacetexture(world, surfacenum);
			if ((returnsurface(tex) == GROUND))
			{
				sendParticle("TE_DIRT", self.origin, VEC_ORIGIN, 1);
				remove(self);
				return;
			}
			else
			{
				if ((returnsurface(tex) == MEAT))
				{
					sendParticle("TE_BLOOD", self.origin, VEC_ORIGIN, 1);
					remove(self);
					return;
				}
				else
				{
					if ((returnsurface(tex) == VOID))
					{
						remove(self);
						return;
					}
					else
					{
						if ((other.flags & FL_MONSTER))
						{
							sendParticle("TE_BLOOD", self.origin, VEC_ORIGIN, 1);
						}
						else
						{
							sendParticle("TE_GUNSHOT", self.origin, VEC_ORIGIN, 1);
						}
					}
				}
			}
		}
		if ((random() < 0.5))
		{
			sound7(self, CHAN_AUTO, "weapons/ric1.wav", 0.7, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_AUTO, "weapons/ric3.wav", 0.7, ATTN_NORM, SNDSPD);
		}
	}
	remove(self);
};

void(vector org, vector dir) launch_enemy_bullet =
{
	local entity bullet;

	bullet = spawn();
	bullet.owner = self;
	bullet.movetype = MOVETYPE_FLYMISSILE;
	bullet.solid = SOLID_BBOX;
	bullet.angles = vectoangles(dir);
	bullet.touch = bullet_enemy_touch;
	bullet.classname = "gruntshot";
	bullet.think = SUB_Remove;
	bullet.nextthink = (time + 10);
	setmodel(bullet, "progs/bullettr.mdl");
	bullet.effects = EF_FULLBRIGHT;
	setsize(bullet, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(bullet, org);
	if ((cvar("slowmo") < 0.7))
	{
		bullet.velocity = (dir * 600);
	}
	else
	{
		bullet.velocity = (dir * 1000);
	}
};

void(vector org, vector dir) launch_spike =
{
	newmis = spawn();
	newmis.cansplash = TRUE;
	newmis.owner = self;
	if ((skill == 3))
	{
		newmis.movetype = MOVETYPE_FLY;
	}
	else
	{
		newmis.movetype = MOVETYPE_FLYMISSILE;
	}
	newmis.solid = SOLID_BBOX;
	newmis.angles = vectoangles(dir);
	newmis.touch = spike_touch;
	newmis.classname = "spike";
	newmis.think = SUB_Remove;
	newmis.scale = 1.3;
	newmis.colormod = '2.5 2 1';
	newmis.traileffectnum = particleeffectnum(/*26067i*/"spike_bubble_trail");
	newmis.nextthink = (time + 10);
	setmodel(newmis, "progs/spike.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	newmis.effects = EF_FULLBRIGHT;
	setorigin(newmis, org);
	if ((cvar("slowmo") > 0.7))
	{
		if ((self.weapon == IT_NAILGUN))
		{
			newmis.velocity = (dir * 3600);
		}
		else
		{
			newmis.velocity = (dir * 2400);
		}
	}
	else
	{
		if ((self.weapon == IT_NAILGUN))
		{
			newmis.velocity = (dir * self.bulletspeed);
		}
		else
		{
			newmis.velocity = ((dir * self.bulletspeed) * 0.666667);
		}
	}
};

void() W_FireSuperSpikes =
{
	local vector dir;
	local vector pushback1;
	local vector direc;
	local entity nail;
	local vector align;
	local vector nailvec;

	if (((cvar("slowmo") < 0.7) && (cvar("slowmo") >= 0.3)))
	{
		sound(self, CHAN_AUTO, "weapons/sngslow.wav", 0.7, ATTN_NORM);
	}
	else
	{
		sound7(self, CHAN_WEAPON, "weapons/spike2.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
	}
	self.weapontimer = (self.weapontimer + 1.2);
	if (((autocvar_muzzleflash == 1) && !autocvar_centered_weapons))
	{
		if (cvar("chase_active"))
		{
			sendParticle("supernailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -7)) + (v_right * -1.5)) + (v_forward * 14)), (self.velocity * 50), 1);
		}
		else
		{
			if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
			{
				sendParticle("supernailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_forward * 20)) + (v_right * 7)), (self.velocity * 50), 1);
			}
			else
			{
				if ((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable))
				{
					sendParticle("supernailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_forward * 20)) + (v_right * autocvar_weapon_position_adjustable_muzzleflash_nail2_offset)), (self.velocity * 50), 1);
				}
				else
				{
					sendParticle("supernailgun_muzzleflash", (((self.origin + self.view_ofs) + (v_up * -8)) + (v_forward * 20)), (self.velocity * 50), 1);
				}
			}
		}
	}
	self.attack_finished = (time + 0.2);
	self.ammo_nails = (self.ammo_nails - 2);
	self.currentammo = (self.ammo_nails - 2);
	dir = aim(self, 1000);
	if (cvar("chase_active"))
	{
		launch_spike((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * -2)), dir);
	}
	else
	{
		if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
		{
			launch_spike((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * 9)), dir);
		}
		else
		{
			if (autocvar_centered_weapons)
			{
				launch_spike(((self.origin + self.view_ofs) + (v_up * -8)), dir);
			}
			else
			{
				if ((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable))
				{
					launch_spike((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * autocvar_weapon_position_adjustable_projectile_nail2_offset)), dir);
				}
				else
				{
					launch_spike(((self.origin + self.view_ofs) + (v_up * -8)), dir);
				}
			}
		}
	}
	newmis.touch = superspike_touch;
	setmodel(newmis, "progs/s_spike.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = (-1.7 - (random() * 0.6));
		if ((self.viewzoom > 0))
		{
			self.viewzoom = 0;
		}
		else
		{
			self.viewzoom = 1.017;
		}
	}
	newmis.scale = 1.3;
	newmis.effects = EF_FULLBRIGHT;
	newmis.colormod = '9.5 2.3 0';
	SpawnSNGFlash();
	SpawnHLFlash();
	SpawnSmoke_Flash(0.6, '5 15 5', 0, VEC_ORIGIN, 0.7);
	if ((autocvar_nospinup != 0))
	{
		self.nextthink = (time + 0.1);
	}
	else
	{
		if ((self.weapontimer <= 2.5))
		{
			self.nextthink = (time + 0.17);
		}
		else
		{
			if ((self.weapontimer <= 4.5))
			{
				self.nextthink = (time + 0.15);
			}
			else
			{
				if ((self.weapontimer <= 7.5))
				{
					self.nextthink = (time + 0.125);
				}
				else
				{
					self.nextthink = (time + 0.09);
				}
			}
		}
	}
	if ((autocvar_pushback != 0))
	{
		direc = aim(self, 100);
		traceline(self.origin, (self.origin + (direc * autocvar_pushbacknail2)), FALSE, self);
		pushback1 = trace_endpos - self.origin;
		self.velocity = (self.velocity - pushback1);
	}
	makevectors(self.v_angle);
	align = dir + (v_up * 0.27);
	traceline(self.origin, (self.origin + (align * 200)), FALSE, self);
	nailvec = (trace_endpos - self.origin) + (normalize(dir) * 80);
	nail = Gyro_Force_Create("nailhit", self.origin);
	Gyro_Force_ApplyFalloff_ConeLinear(nail, nailvec, 16, 16);
	Gyro_Force_ApplyAffector_Directional(nail, nailvec, 2, FALSE);
	Gyro_Force_AddProperty_Instant(nail);
	Gyro_Force_Ignore(nail, self);
	self.spindown = 1;
	self.spintimer = 0;
};

void(float ox) W_FireSpikes =
{
	local vector dir;
	local vector muzzoff;
	local float naila;
	local float nailb;
	local vector pushback1;
	local vector direc;
	local entity nail;
	local vector align;
	local vector nailvec;

	naila = autocvar_weapon_position_adjustable_projectile_nail1a_offset;
	nailb = autocvar_weapon_position_adjustable_projectile_nail1b_offset;
	makevectors(self.v_angle);
	if (((self.ammo_nails >= 2) && (self.weapon == IT_SUPER_NAILGUN)))
	{
		W_FireSuperSpikes();
		return;
	}
	if ((self.ammo_nails < 1))
	{
		BM_OutOfAmmo();
		return;
	}
	if (!self.button0)
	{
		self.weaponframe = (self.weaponframe + 1);
		player_run();
		return;
	}
	self.weaponframe = (self.weaponframe + 1);
	if ((self.weaponframe >= 5))
	{
		self.weaponframe = 1;
	}
	if (((autocvar_muzzleflash == 1) && !autocvar_centered_weapons))
	{
		if (cvar("chase_active"))
		{
			sendParticle("nailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * 2)) + (v_forward * 13)), (self.velocity * 50), 1);
			sendParticle("nailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * -4.6)) + (v_forward * 13)), (self.velocity * 50), 1);
		}
		else
		{
			if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
			{
				if ((self.weaponframe == 1))
				{
					sendParticle("nailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * 10)) + (v_forward * 19)), (self.velocity * 50), 1);
				}
				if ((self.weaponframe == 3))
				{
					sendParticle("nailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * 5.5)) + (v_forward * 19)), (self.velocity * 50), 1);
				}
			}
			else
			{
				if ((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable))
				{
					if ((self.weaponframe == 1))
					{
						sendParticle("nailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * autocvar_weapon_position_adjustable_muzzleflash_nail1a_offset)) + (v_forward * 19)), (self.velocity * 50), 1);
					}
					if ((self.weaponframe == 3))
					{
						sendParticle("nailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * autocvar_weapon_position_adjustable_muzzleflash_nail1b_offset)) + (v_forward * 19)), (self.velocity * 50), 1);
					}
				}
				else
				{
					sendParticle("nailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * 3.3)) + (v_forward * 20)), (self.velocity * 50), 1);
					sendParticle("nailgun_muzzleflash", ((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * -3.3)) + (v_forward * 20)), (self.velocity * 50), 1);
				}
			}
		}
	}
	self.attack_finished = (time + 0.1);
	self.nextthink = (time + 0.053);
	dir = aim(self, 1000);
	if ((self.weaponframe == 1))
	{
		muzzoff = '0 -20 0';
		if (((cvar("slowmo") < 0.7) && (cvar("slowmo") >= 0.3)))
		{
			sound(self, CHAN_AUTO, "weapons/ngslow.wav", 0.7, ATTN_NORM);
		}
		else
		{
			sound7(self, CHAN_WEAPON, "weapons/rocket1i.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
		}
		if (autocvar_centered_weapons)
		{
			launch_spike((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * 5)), dir);
		}
		else
		{
			launch_spike((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * 9)), dir);
		}
		SpawnNailgunFlash(muzzoff);
		SpawnSmoke_Flash(0.8, (muzzoff + '0 10 -15'), 0, VEC_ORIGIN, 0.7);
		self.ammo_nails = (self.ammo_nails - 1);
		self.currentammo = (self.ammo_nails - 1);
		if (((autocvar_shellcasing == 1) && (autocvar_casingejectframe >= 1)))
		{
			nailcasing(0);
		}
	}
	else
	{
		if ((self.weaponframe == 3))
		{
			muzzoff = '0 12 0';
			if (((cvar("slowmo") < 0.7) && (cvar("slowmo") >= 0.3)))
			{
				sound(self, CHAN_AUTO, "weapons/ngslow.wav", 0.7, ATTN_NORM);
			}
			else
			{
				sound7(self, CHAN_WEAPON, "weapons/rocket1i.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
			}
			if (autocvar_centered_weapons)
			{
				launch_spike((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * -6)), dir);
			}
			else
			{
				launch_spike((((self.origin + self.view_ofs) + (v_up * -8)) + (v_right * 2)), dir);
			}
			SpawnNailgunFlash(muzzoff);
			SpawnSmoke_Flash(0.8, (muzzoff + '0 20 -15'), 0, VEC_ORIGIN, 0.7);
			self.ammo_nails = (self.ammo_nails - 1);
			self.currentammo = (self.ammo_nails - 1);
			if (((autocvar_shellcasing == 1) && (autocvar_casingejectframe >= 1)))
			{
				nailcasing(0);
			}
		}
	}
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = (-1.5 - (random() * 0.6));
		if ((self.viewzoom > 0))
		{
			self.viewzoom = 0;
		}
		else
		{
			self.viewzoom = 1.017;
		}
	}
	if ((autocvar_pushback != 0))
	{
		direc = aim(self, 100);
		traceline(self.origin, (self.origin + (direc * autocvar_pushbacknail1)), FALSE, self);
		pushback1 = trace_endpos - self.origin;
		self.velocity = (self.velocity - pushback1);
	}
	makevectors(self.v_angle);
	align = dir + (v_up * 0.27);
	traceline(self.origin, (self.origin + (align * 200)), FALSE, self);
	nailvec = (trace_endpos - self.origin) + (normalize(dir) * 80);
	nail = Gyro_Force_Create("nailhit", self.origin);
	Gyro_Force_ApplyFalloff_ConeLinear(nail, nailvec, 16, 16);
	Gyro_Force_ApplyAffector_Directional(nail, nailvec, 2, FALSE);
	Gyro_Force_AddProperty_Instant(nail);
	Gyro_Force_Ignore(nail, self);
};

void() spike_stuck_think =
{
	if ((self.aflag <= time))
	{
		remove(self);
		return;
	}
	setorigin(self, ((self.pos1 + self.owner.origin) - self.pos2));
	self.nextthink = time;
};

void() spike_enemy_touch =
{
	local float zufall;

	if ((other == self.owner))
	{
		return;
	}
	if ((other.solid == SOLID_TRIGGER))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	if (other.takedamage)
	{
		spawn_touchblood(9);
		if ((self.classname == "gruntshot"))
		{
			T_Damage(other, self, self.owner, 5);
		}
		else
		{
			if ((self.classname == "wizspike"))
			{
				if ((autocvar_wizard_size_influenced_attack == 1))
				{
					T_Damage(other, self, self.owner, (autocvar_wizard_missile * self.owner.scale));
				}
				else
				{
					T_Damage(other, self, self.owner, autocvar_wizard_missile);
				}
				if ((skill == 3))
				{
					zufall = random() * 100;
					if ((zufall <= 20))
					{
						other.poisoned = 1;
						other.poisontime = (time + autocvar_wizard_projectiles_and_slime_poison_time);
						other.poisonpause = (time + autocvar_wizard_projectiles_and_slime_poison_frequence);
						stuffcmd(other, "v_cshift 1 0 1 0\n");
					}
				}
			}
			else
			{
				if ((self.classname == "knightspike"))
				{
					if ((autocvar_hknight_size_influenced_attack == 1))
					{
						T_Damage(other, self, self.owner, (autocvar_hellknight_missile * self.owner.scale));
					}
					else
					{
						T_Damage(other, self, self.owner, autocvar_hellknight_missile);
					}
				}
				else
				{
					if ((self.classname == "furyspike"))
					{
						if ((other.classname != "monster_knight"))
						{
							T_Damage(other, self, self.owner, autocvar_hellknight_missile);
						}
					}
					else
					{
						if ((self.classname == "furyspike"))
						{
							if ((other.classname != "monster_knight"))
							{
								T_Damage(other, self, self.owner, autocvar_hellknight_missile);
							}
						}
						else
						{
							if (((self.classname == "gruntspike") || (self.classname == "freddiespike")))
							{
								T_Damage(other, self, self.owner, 7);
							}
							else
							{
								T_Damage(other, self, self.owner, autocvar_warlord_missile);
							}
						}
					}
				}
			}
		}
	}
	else
	{
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		if ((self.classname == "wizspike"))
		{
			WriteByte(MSG_BROADCAST, TE_WIZSPIKE);
		}
		else
		{
			if (((self.classname == "knightspike") || (self.classname == "knight2spike")))
			{
				WriteByte(MSG_BROADCAST, TE_KNIGHTSPIKE);
			}
			else
			{
				WriteByte(MSG_BROADCAST, TE_SPIKE);
			}
		}
		WriteCoord(MSG_BROADCAST, self.origin_x);
		WriteCoord(MSG_BROADCAST, self.origin_y);
		WriteCoord(MSG_BROADCAST, self.origin_z);
	}
	remove(self);
};

void() spike_touch =
{
	local float surfacenum;
	local string tex;
	local float resist;
	local float surfnum;
	local string s;
	local vector backwards;
	local vector face_spawn_pos;
	local vector face_spawn_vel;

	if ((other == self.owner))
	{
		return;
	}
	if ((other.solid == SOLID_TRIGGER))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	if ((other != world))
	{
		if ((0 > (trace_ent.origin_z + 16)))
		{
			trace_ent.hitbox_pos = HEAD_SHOT;
		}
	}
	surfacenum = getsurfacenearpoint(world, self.origin);
	self.effects = 0;
	if ((surfacenum >= 0))
	{
		tex = getsurfacetexture(world, surfacenum);
		if (((tex == "sky1") || (tex == "sky4")))
		{
			remove(self);
			return;
		}
	}
	if (((other.inflamed == 1) && (other.inflamekillafterdeath == 0)))
	{
		other.inflamekillafterdeath = 1;
		if ((random() < 0.15))
		{
			other.health = -41;
		}
		else
		{
			other.health = -1;
		}
		other.nextthink = time;
		other.think = other.th_die;
		spawn_touchblood(9);
	}
	if (other.takedamage)
	{
		if ((autocvar_shootablebuttonsandsecrets != 0))
		{
			if ((((((trace_ent.takedamage != DAMAGE_AIM) && (trace_ent.classname != "monster_hell_knight2")) && (trace_ent.classname != "monster_enforcer")) && (trace_ent.classname != "monster_reiver")) && (trace_ent.classname != "monster_oldone")))
			{
				if ((autocvar_shootablebuttonsandsecrets == 1))
				{
					sendParticle("secret", self.origin, VEC_ORIGIN, 1);
				}
				else
				{
					sendParticle("TE_SPIKE", self.origin, VEC_ORIGIN, 1);
				}
				T_Damage(other, self, self.owner, autocvar_player_nailgun);
				remove(self);
				return;
			}
			if (((trace_ent.model == "maps/b_explob.bsp") || (trace_ent.model == "maps/b_exbox2.bsp")))
			{
				T_Damage(other, self, self.owner, autocvar_player_nailgun);
				remove(self);
				return;
			}
		}
		if ((self.owner.super_damage_finished > time))
		{
			if ((((random() < 0.1) && (other.health < 45)) && (other.health_initial < 400)))
			{
				T_Damage(other, self, self.owner, ((autocvar_player_nailgun * 2.2) + random()));
			}
		}
		if ((other.classname == "monster_spider"))
		{
			resist = autocvar_spider_attack_resistance * 0.01;
			if ((random() > resist))
			{
				spawn_touchblood(9);
				T_Damage(other, self, self.owner, autocvar_player_nailgun);
			}
			else
			{
				return;
			}
		}
		else
		{
			if (((((other.classname != "monster_jim") && (other.classname != "monster_ogre")) && (other.classname != "monster_hell_knight")) && (other.classname != "monster_hell_knight2")))
			{
				pointparticles(particleeffectnum(/*25865i*/"blood_saw"), self.origin, VEC_ORIGIN, 1);
				spawn_touchblood(14);
			}
			T_Damage(other, self, self.owner, autocvar_player_nailgun);
		}
		if ((autocvar_fleshsplat == 1))
		{
			self.angles_x = (self.angles_x * -1);
			makevectors(self.angles);
			if ((other.classname == "monster_wizard"))
			{
				ThrowBloodSplat(v_forward, self.origin, other, (entity)1065353216i, (entity)1065353216i);
			}
			else
			{
				if ((other.classname == "monster_army"))
				{
					ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
				}
				else
				{
					if ((other.classname == "monster_ogre"))
					{
						ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
						if (((random() * 100) < 40))
						{
							sendParticle("TE_SPIKE", self.origin, VEC_ORIGIN, 1);
						}
						else
						{
							pointparticles(particleeffectnum(/*25865i*/"blood_saw"), self.origin, VEC_ORIGIN, 1);
						}
					}
					else
					{
						if ((other.classname == "monster_hell_knight"))
						{
							ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
							if (((random() * 100) < 60))
							{
								sendParticle("TE_SPIKE", self.origin, VEC_ORIGIN, 1);
							}
							else
							{
								pointparticles(particleeffectnum(/*25865i*/"blood_saw"), self.origin, VEC_ORIGIN, 1);
							}
						}
						else
						{
							if ((other.classname == "monster_hell_knight2"))
							{
								if (((random() * 100) < 70))
								{
									sendParticle("TE_SPIKE", self.origin, VEC_ORIGIN, 1);
								}
								else
								{
									pointparticles(particleeffectnum(/*25865i*/"blood_saw"), self.origin, VEC_ORIGIN, 1);
								}
								ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
							}
							else
							{
								if ((other.classname == "monster_enforcer"))
								{
									if ((other.dodge_finished < time))
									{
										ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
									}
								}
								else
								{
									if ((other.classname == "monster_reiver"))
									{
										if ((other.dodge_finished < time))
										{
											ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
										}
									}
									else
									{
										if ((other.classname == "monster_knight"))
										{
											ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
											if (((random() * 100) < 40))
											{
												sendParticle("TE_SPIKE", self.origin, VEC_ORIGIN, 1);
											}
										}
										else
										{
											if ((other.classname == "monster_demon1"))
											{
												ThrowBloodSplat(v_forward, self.origin, other, (entity)1077936128i, (entity)1065353216i);
											}
											else
											{
												if ((other.classname == "monster_dog"))
												{
													ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
												}
												else
												{
													if ((other.classname == "monster_shalrath"))
													{
														ThrowBloodSplat(v_forward, self.origin, other, (entity)1082130432i, (entity)1065353216i);
													}
													else
													{
														if ((other.classname == "monster_tarbaby"))
														{
															ThrowBloodSplat(v_forward, self.origin, other, (entity)1084227584i, (entity)1065353216i);
														}
														else
														{
															if ((other.classname == "monster_shambler"))
															{
																ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
															}
															else
															{
																ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
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
		remove(self);
		return;
	}
	else
	{
		if ((other.solid != SOLID_BSP))
		{
			remove(self);
			return;
		}
	}
	if (autocvar_evil_faces)
	{
		surfnum = getsurfacenearpoint(world, self.origin);
		if ((surfnum >= 0))
		{
			s = getsurfacetexture(world, surfnum);
			if (((((((s == "altarb_1") || (s == "altarb_2")) || (s == "dem4_1")) || (s == "dem4_4")) || (s == "dem5_3")) || (s == "demc4_4")))
			{
				backwards = self.origin;
				backwards = backwards - (8 * normalize(self.velocity));
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnBlood(backwards, VEC_ORIGIN, 5);
				if ((facetime < time))
				{
					facetime = time + 2;
					face_spawn_vel = normalize(trace_plane_normal);
					face_spawn_vel = face_spawn_vel * 10;
					face_spawn_pos = self.origin - (trace_plane_normal * 20);
					spawn_face(face_spawn_pos, face_spawn_vel, 0);
				}
				remove(self);
				return;
			}
		}
	}
	if ((self.classname == "wizspike"))
	{
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte(MSG_BROADCAST, TE_WIZSPIKE);
		WriteCoord(MSG_BROADCAST, self.origin_x);
		WriteCoord(MSG_BROADCAST, self.origin_y);
		WriteCoord(MSG_BROADCAST, self.origin_z);
	}
	else
	{
		if ((self.classname == "knightspike"))
		{
			WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
			WriteByte(MSG_BROADCAST, TE_KNIGHTSPIKE);
			WriteCoord(MSG_BROADCAST, self.origin_x);
			WriteCoord(MSG_BROADCAST, self.origin_y);
			WriteCoord(MSG_BROADCAST, self.origin_z);
		}
		else
		{
			if ((cvar("slowmo") < 0.9))
			{
				sendParticle("TE_SPIKE", self.origin, VEC_ORIGIN, 1);
				if ((random() < 0.8))
				{
					sound7(self, CHAN_WEAPON, "weapons/ric1.wav", 0.7, ATTN_NORM, SNDSPD);
				}
				else
				{
					if ((random() < 0.4))
					{
						sound7(self, CHAN_ITEM, "weapons/ric2.wav", 0.7, ATTN_NORM, SNDSPD);
					}
					else
					{
						sound7(self, CHAN_BODY, "weapons/ric3.wav", 0.7, ATTN_NORM, SNDSPD);
					}
				}
			}
			else
			{
				surfacenum = getsurfacenearpoint(world, self.origin);
				if ((surfacenum >= 0))
				{
					tex = getsurfacetexture(world, surfacenum);
					if ((returnsurface(tex) == GROUND))
					{
						sendParticle("TE_DIRT", self.origin, VEC_ORIGIN, 1);
						remove(self);
						return;
					}
					else
					{
						if ((returnsurface(tex) == MEAT))
						{
							sendParticle("TE_BLOOD", self.origin, VEC_ORIGIN, 1);
							remove(self);
							return;
						}
						else
						{
							if ((returnsurface(tex) == VOID))
							{
								remove(self);
								return;
							}
						}
					}
				}
				WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
				WriteByte(MSG_BROADCAST, TE_SPIKE);
				WriteCoord(MSG_BROADCAST, self.origin_x);
				WriteCoord(MSG_BROADCAST, self.origin_y);
				WriteCoord(MSG_BROADCAST, self.origin_z);
			}
		}
	}
	self.solid = 0;
	self.movetype = 0;
	self.colormod = '1 1 1';
	setorigin(self, (self.origin - (normalize(self.velocity) * 3)));
	self.velocity = VEC_ORIGIN;
	if (((other.solid == SOLID_BSP) && (other != world)))
	{
		self.owner = other;
		self.pos1 = self.origin;
		self.pos2 = other.origin;
		self.aflag = (time + 10);
		self.think = spike_stuck_think;
		self.nextthink = time;
	}
	else
	{
		self.nextthink = (time + autocvar_spikelifetime);
		self.think = SUB_Remove;
	}
};

void() superspike_touch =
{
	local float surfacenum;
	local string tex;
	local float resist;
	local float surfnum;
	local string s;
	local vector backwards;
	local vector face_spawn_pos;
	local vector face_spawn_vel;

	if ((other == self.owner))
	{
		return;
	}
	if ((other.solid == SOLID_TRIGGER))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	if ((other != world))
	{
		if ((0 > (trace_ent.origin_z + 16)))
		{
			trace_ent.hitbox_pos = HEAD_SHOT;
		}
	}
	self.effects = 0;
	surfacenum = getsurfacenearpoint(world, self.origin);
	if ((surfacenum >= 0))
	{
		tex = getsurfacetexture(world, surfacenum);
		if (((tex == "sky1") || (tex == "sky4")))
		{
			remove(self);
			return;
		}
	}
	if (((other.inflamed == 1) && (other.inflamekillafterdeath == 0)))
	{
		other.inflamekillafterdeath = 1;
		if ((random() < 0.5))
		{
			other.health = -41;
		}
		else
		{
			other.health = -1;
		}
		other.nextthink = time;
		other.think = other.th_die;
		spawn_touchblood(9);
	}
	if (other.takedamage)
	{
		if ((autocvar_shootablebuttonsandsecrets != 0))
		{
			if ((((((trace_ent.takedamage != DAMAGE_AIM) && (trace_ent.classname != "monster_hell_knight2")) && (trace_ent.classname != "monster_enforcer")) && (trace_ent.classname != "monster_reiver")) && (trace_ent.classname != "monster_oldone")))
			{
				if ((autocvar_shootablebuttonsandsecrets == 1))
				{
					sendParticle("secret", self.origin, VEC_ORIGIN, 1);
				}
				else
				{
					sendParticle("TE_SUPERSPIKE", self.origin, VEC_ORIGIN, 1);
				}
				T_Damage(other, self, self.owner, autocvar_player_supernailgun);
				remove(self);
				return;
			}
			if (((trace_ent.model == "maps/b_explob.bsp") || (trace_ent.model == "maps/b_exbox2.bsp")))
			{
				T_Damage(other, self, self.owner, autocvar_player_supernailgun);
				remove(self);
				return;
			}
		}
		if ((other.classname == "monster_spider"))
		{
			resist = autocvar_spider_attack_resistance * 0.01;
			if ((random() > resist))
			{
				spawn_touchblood(18);
				T_Damage(other, self, self.owner, autocvar_player_supernailgun);
			}
			else
			{
				return;
			}
		}
		else
		{
			if ((other.classname == "monster_dfury_boss"))
			{
				self.velocity_x = (0 - self.velocity_x);
				self.velocity_y = (0 - self.velocity_y);
				T_Damage(other, self, self.owner, (autocvar_player_supernailgun / 2));
				sendParticle("sparks", self.origin, VEC_ORIGIN, 1);
			}
			else
			{
				if ((other.classname != "monster_jim"))
				{
					pointparticles(particleeffectnum(/*25865i*/"blood_saw"), self.origin, VEC_ORIGIN, 1);
					spawn_touchblood(16);
				}
				T_Damage(other, self, self.owner, autocvar_player_supernailgun);
			}
		}
		if ((autocvar_fleshsplat == 1))
		{
			self.angles_x = (self.angles_x * -1);
			makevectors(self.angles);
			if ((other.classname == "monster_wizard"))
			{
				ThrowBloodSplat(v_forward, self.origin, other, (entity)1065353216i, (entity)1065353216i);
			}
			else
			{
				if ((other.classname == "monster_army"))
				{
					ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
				}
				else
				{
					if ((other.classname == "monster_ogre"))
					{
						ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
						if (((random() * 100) < 40))
						{
							sendParticle("TE_SUPERSPIKE", self.origin, VEC_ORIGIN, 1);
						}
					}
					else
					{
						if ((other.classname == "monster_hell_knight"))
						{
							ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
							if (((random() * 100) < 40))
							{
								sendParticle("TE_SUPERSPIKE", self.origin, VEC_ORIGIN, 1);
							}
						}
						else
						{
							if ((other.classname == "monster_hell_knight2"))
							{
								if (((random() * 100) < 40))
								{
									sendParticle("TE_SUPERSPIKE", self.origin, VEC_ORIGIN, 1);
								}
								if ((other.dodge_finished < time))
								{
									ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
								}
							}
							else
							{
								if ((other.classname == "monster_enforcer"))
								{
									if ((other.dodge_finished < time))
									{
										ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
									}
								}
								else
								{
									if ((other.classname == "monster_reiver"))
									{
										if ((other.dodge_finished < time))
										{
											ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
										}
									}
									else
									{
										if ((other.classname == "monster_knight"))
										{
											ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
											if (((random() * 100) < 40))
											{
												sendParticle("TE_SUPERSPIKE", self.origin, VEC_ORIGIN, 1);
											}
										}
										else
										{
											if ((other.classname == "monster_demon1"))
											{
												ThrowBloodSplat(v_forward, self.origin, other, (entity)1077936128i, (entity)1065353216i);
											}
											else
											{
												if ((other.classname == "monster_dog"))
												{
													ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
												}
												else
												{
													if ((other.classname == "monster_shalrath"))
													{
														ThrowBloodSplat(v_forward, self.origin, other, (entity)1082130432i, (entity)1065353216i);
													}
													else
													{
														if ((other.classname == "monster_tarbaby"))
														{
															ThrowBloodSplat(v_forward, self.origin, other, (entity)1084227584i, (entity)1065353216i);
														}
														else
														{
															if ((other.classname == "monster_shambler"))
															{
																ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
															}
															else
															{
																ThrowBloodSplat(v_forward, self.origin, other, (entity)1073741824i, (entity)1065353216i);
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
		remove(self);
		return;
	}
	else
	{
		if ((other.solid != SOLID_BSP))
		{
			remove(self);
			return;
		}
	}
	if (autocvar_evil_faces)
	{
		surfnum = getsurfacenearpoint(world, self.origin);
		if ((surfnum >= 0))
		{
			s = getsurfacetexture(world, surfnum);
			if (((((((s == "altarb_1") || (s == "altarb_2")) || (s == "dem4_1")) || (s == "dem4_4")) || (s == "dem5_3")) || (s == "demc4_4")))
			{
				backwards = self.origin;
				backwards = backwards - (8 * normalize(self.velocity));
				SpawnMeatSpray_eviltexture(backwards, '50 50 50');
				SpawnBlood(backwards, VEC_ORIGIN, 5);
				if ((facetime < time))
				{
					facetime = time + 2;
					face_spawn_vel = normalize(trace_plane_normal);
					face_spawn_vel = face_spawn_vel * 10;
					face_spawn_pos = self.origin - (trace_plane_normal * 20);
					spawn_face(face_spawn_pos, face_spawn_vel, 0);
				}
				remove(self);
				return;
			}
		}
	}
	if ((cvar("slowmo") < 0.9))
	{
		sendParticle("TE_SUPERSPIKE", self.origin, VEC_ORIGIN, 1);
		if ((random() < 0.8))
		{
			sound7(self, CHAN_WEAPON, "weapons/ric1.wav", 0.7, ATTN_NORM, SNDSPD);
		}
		else
		{
			if ((random() < 0.4))
			{
				sound7(self, CHAN_ITEM, "weapons/ric2.wav", 0.7, ATTN_NORM, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_BODY, "weapons/ric3.wav", 0.7, ATTN_NORM, SNDSPD);
			}
		}
	}
	else
	{
		surfacenum = getsurfacenearpoint(world, self.origin);
		if ((surfacenum >= 0))
		{
			tex = getsurfacetexture(world, surfacenum);
			if ((returnsurface(tex) == GROUND))
			{
				sendParticle("TE_DIRT", self.origin, VEC_ORIGIN, 1);
				remove(self);
				return;
			}
			else
			{
				if ((returnsurface(tex) == MEAT))
				{
					sendParticle("TE_BLOOD", self.origin, VEC_ORIGIN, 1);
					remove(self);
					return;
				}
				else
				{
					if ((returnsurface(tex) == VOID))
					{
						return;
					}
				}
			}
		}
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte(MSG_BROADCAST, TE_SUPERSPIKE);
		WriteCoord(MSG_BROADCAST, self.origin_x);
		WriteCoord(MSG_BROADCAST, self.origin_y);
		WriteCoord(MSG_BROADCAST, self.origin_z);
	}
	self.solid = 0;
	self.movetype = 0;
	setorigin(self, (self.origin - (normalize(self.velocity) * 3)));
	self.velocity = VEC_ORIGIN;
	self.colormod = '1.6 1.3 1';
	if (((other.solid == SOLID_BSP) && (other != world)))
	{
		self.owner = other;
		self.pos1 = self.origin;
		self.pos2 = other.origin;
		self.aflag = (time + 10);
		self.think = spike_stuck_think;
		self.nextthink = time;
	}
	else
	{
		self.nextthink = (time + autocvar_spikelifetime);
		self.think = SUB_Remove;
	}
};

void() W_SetCurrentAmmo =
{
	BM_SwapIn();	// LAN magazines: bank the old gun's, load the new one's
	player_run();
	self.items = (self.items - (self.items & 3840));
	self.alpha = (autocvar_weaponandplayertransparency * 0.01);
	if ((self.has_fired == 1))
	{
		self.weapon = IT_AXE;
	}
	if ((self.weapon == IT_AXE))
	{
		self.currentammo = 0;
		if ((autocvar_zombieaxeanimation == 1))
		{
			self.weaponmodel = "progs/v_hammer.mdl";
		}
		else
		{
			self.weaponmodel = "progs/v_hammer.mdl";
		}
		self.weaponframe = 0;
		axeequipped = 1;
	}
	else
	{
		if ((self.weapon == IT_CHAINSAW))
		{
			self.skin = 1;
			self.weaponmodel = "progs/v_saw.mdl";
			sound7(self, 6, "weapons/sawidle.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
			self.weaponframe = 0;
			self.items = (self.items | IT_ROCKETS);
		}
		else
		{
			if ((self.weapon == IT_SHOTGUN))
			{
				self.currentammo = self.ammo_shells;
				if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
				{
					self.weaponmodel = "progs/v_googun.md3";	// Goo Gun
				}
				else
				{
					if (autocvar_centered_weapons)
					{
						self.weaponmodel = "progs/v_googun.md3";
					}
					else
					{
						self.weaponmodel = "progs/v_googun.md3";
					}
				}
				self.weaponframe = 0;
				self.items = (self.items | IT_SHELLS);
				axeequipped = 0;
			}
			else
			{
				if ((self.weapon == IT_SUPER_SHOTGUN))
				{
					self.currentammo = self.ammo_shells;
					if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
					{
						self.weaponmodel = "progs/v_shot2_right.mdl";
					}
					else
					{
						if ((autocvar_centered_weapons && !autocvar_qc_ssg))
						{
							self.weaponmodel = "progs/centered/v_shot2.mdl";
						}
						else
						{
							if ((autocvar_qc_ssg && autocvar_centered_weapons))
							{
								self.weaponmodel = "progs/centered/QC/v_shot2.mdl";
							}
							else
							{
								if (autocvar_qc_ssg)
								{
									self.weaponmodel = "progs/QC/v_shot2.mdl";
								}
								else
								{
									self.weaponmodel = "progs/v_shot2.mdl";
								}
							}
						}
					}
					self.weaponframe = 0;
					self.items = (self.items | IT_SHELLS);
					axeequipped = 0;
				}
				else
				{
					if ((self.weapon == IT_NAILGUN))
					{
						self.currentammo = self.ammo_nails;
						if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
						{
							self.weaponmodel = "progs/ltg_view.md3";	// laptop gun
						}
						else
						{
							self.weaponmodel = "progs/ltg_view.md3";
						}
						self.weaponframe = 0;
						self.items = (self.items | IT_NAILS);
						axeequipped = 0;
					}
					else
					{
						if ((self.weapon == IT_SUPER_NAILGUN))
						{
							self.currentammo = self.ammo_nails;
							if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
							{
								self.weaponmodel = "progs/v_nail2_right.mdl";
							}
							else
							{
								self.weaponmodel = "progs/v_nail2.mdl";
							}
							self.weaponframe = 0;
							self.items = (self.items | IT_NAILS);
							axeequipped = 0;
						}
						else
						{
							if ((self.weapon == IT_GRENADE_LAUNCHER))
							{
								self.currentammo = self.ammo_rockets;
								if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
								{
									self.weaponmodel = "progs/v_rock_right.mdl";
								}
								else
								{
									self.weaponmodel = "progs/v_rock.mdl";
								}
								self.weaponframe = 0;
								self.items = (self.items | IT_ROCKETS);
								axeequipped = 0;
							}
							else
							{
								if ((self.weapon == IT_ROCKET_LAUNCHER))
								{
									self.currentammo = self.ammo_rockets;
									if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
									{
										self.weaponmodel = "progs/v_rock2_right.mdl";
									}
									else
									{
										self.weaponmodel = "progs/v_rock2.mdl";
									}
									self.weaponframe = 0;
									self.items = (self.items | IT_ROCKETS);
									axeequipped = 0;
								}
								else
								{
									if ((self.weapon == IT_LIGHTNING))
									{
										self.currentammo = self.ammo_cells;
										if (((autocvar_weapon_position_right == 1) && !autocvar_weapon_position_fully_adjustable))
										{
											cvar_set("cl_beams_quakepositionhack", "0");
											self.weaponmodel = "progs/v_light_right.mdl";
										}
										else
										{
											if (((autocvar_weapon_position_right == 2) && !autocvar_weapon_position_fully_adjustable))
											{
												cvar_set("cl_beams_quakepositionhack", "1");
												self.weaponmodel = "progs/v_light.mdl";
											}
											else
											{
												cvar_set("cl_beams_quakepositionhack", "1");
												self.weaponmodel = "progs/v_light.mdl";
											}
										}
										if (autocvar_mage_weapon)
										{
											cvar_set("cl_beams_quakepositionhack", "1");
											self.weaponmodel = "progs/v_mage1.mdl";
										}
										self.weaponframe = 0;
										self.items = (self.items | IT_CELLS);
										axeequipped = 0;
									}
									else
									{
										if ((self.weapon == IT_LASER_CANNON))
										{
											self.currentammo = self.ammo_cells;
											self.weaponmodel = "progs/v_laserg.mdl";
											self.weaponframe = 0;
											self.items = (self.items | IT_CELLS);
										}
										else if ((self.weapon == IT_FUNGUN))
										{
											self.currentammo = FunGun_Ammo(self, self.fg_sel);
											self.weaponmodel = FunGun_VModel(self.fg_sel);
											self.weaponframe = 0;
											axeequipped = 0;
										}
										else if ((self.weapon == IT_BANANA))
										{
											self.currentammo = self.bn_ammo;
											self.weaponmodel = "";
											self.weaponframe = 0;
											axeequipped = 0;
										}
										else if ((self.weapon == IT_MEGAMAN))
										{
											self.currentammo = self.mm_ammo;
											self.weaponmodel = MM_PickVModel();
											self.weaponframe = 0;
											axeequipped = 0;
										}
										else
										{
											self.currentammo = 0;
											self.weaponmodel = "";
											self.weaponframe = 0;
											axeequipped = 0;
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
};

float() W_BestWeapon =
{
	local float it;

	it = self.items;
	if ((((self.waterlevel <= 1) && (self.ammo_cells >= 1)) && (it & IT_LIGHTNING)))
	{
		return (IT_LIGHTNING);
	}
	if (((self.ammo_nails >= 2) && (it & IT_SUPER_NAILGUN)))
	{
		return (IT_SUPER_NAILGUN);
	}
	if (((self.ammo_shells >= 2) && (it & IT_SUPER_SHOTGUN)))
	{
		return (IT_SUPER_SHOTGUN);
	}
	if (((self.ammo_nails >= 1) && (it & IT_NAILGUN)))
	{
		return (IT_NAILGUN);
	}
	if (((self.ammo_shells >= 1) && (it & IT_SHOTGUN)))
	{
		return (IT_SHOTGUN);
	}
	if ((it & IT_CHAINSAW))
	{
		return (IT_CHAINSAW);
	}
	return (IT_AXE);
};

float() W_CheckNoAmmo =
{
	if (BM_CurSlot())
	{
		return (BM_CheckNoAmmo());	// empty magazine: reload, don't switch
	}
	if ((self.currentammo > 0))
	{
		return (TRUE);
	}
	if ((((self.weapon == IT_MEGAMAN) || (self.weapon == IT_BANANA)) || (self.weapon == IT_FUNGUN)))
	{
		return (TRUE);
	}
	if ((self.weapon == IT_AXE))
	{
		return (TRUE);
	}
	if ((self.weapon == IT_CHAINSAW))
	{
		return (TRUE);
	}
	BM_OutOfAmmo();
	return (0);
};

void() shellcasing_touch =
{
	local float zufall;

	if ((other.solid == SOLID_BSP))
	{
		self.velocity = (self.velocity * 0.9);
		if (autocvar_casingdropsound)
		{
			zufall = random();
			if ((zufall <= 0.4))
			{
				sound7(self, CHAN_WEAPON, "weapons/casings1.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
			}
			else
			{
				if ((zufall >= 0.6))
				{
					sound7(self, CHAN_WEAPON, "weapons/casings2.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
				}
				else
				{
					sound7(self, CHAN_WEAPON, "weapons/casings3.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
				}
			}
		}
		self.touch = SUB_Null;
	}
};

void() nailcasing_touch =
{
	local float zufall;

	if ((other.solid == SOLID_BSP))
	{
		if (autocvar_casingdropsound)
		{
			zufall = random();
			if ((self.owner.waterlevel >= 3))
			{
				if ((zufall <= 0.4))
				{
					sound7(self, CHAN_WEAPON, "weapons/nailcase1.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
				}
				else
				{
					if ((zufall >= 0.6))
					{
						sound7(self, CHAN_WEAPON, "weapons/nailcase2.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
					}
					else
					{
						sound7(self, CHAN_WEAPON, "weapons/nailcase3.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
					}
				}
			}
			else
			{
				if ((zufall <= 0.4))
				{
					sound7(self, CHAN_WEAPON, "weapons/nailcase1.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
				}
				else
				{
					if ((zufall >= 0.6))
					{
						sound7(self, CHAN_WEAPON, "weapons/nailcase2.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
					}
					else
					{
						sound7(self, CHAN_WEAPON, "weapons/nailcase3.wav", autocvar_casingdropsound, ATTN_NORM, SNDSPD);
					}
				}
			}
		}
		self.touch = SUB_Null;
	}
};

void() rockcasing_touch =
{
	local float zufall;

	if ((other.solid == SOLID_BSP))
	{
		if (autocvar_casingdropsound)
		{
			zufall = random();
			if ((self.waterlevel >= 3))
			{
				if ((zufall <= 0.2))
				{
					sound7(self, CHAN_WEAPON, "weapons/rockcase1.wav", (autocvar_casingdropsound / 2), ATTN_NORM, SNDSPD);
				}
				else
				{
					sound7(self, CHAN_WEAPON, "weapons/rockcase.wav", (autocvar_casingdropsound / 2), ATTN_NORM, SNDSPD);
				}
			}
			else
			{
				if ((zufall <= 0.2))
				{
					sound7(self, CHAN_WEAPON, "weapons/rockcase1.wav", (autocvar_casingdropsound / 3), ATTN_NORM, ((random() * 10) + 90));
				}
				else
				{
					sound7(self, CHAN_WEAPON, "weapons/rockcase.wav", (autocvar_casingdropsound / 3), ATTN_NORM, ((random() * 10) + 90));
				}
			}
		}
	}
};

float(entity to, float sendFlags) casing_sendtocsqc =
{
	WriteByte(MSG_ENTITY, ENT_CASING);
	WriteByte(MSG_ENTITY, sendFlags);
	if ((sendFlags & 1))
	{
		WriteCoord(MSG_ENTITY, self.origin_x);
		WriteCoord(MSG_ENTITY, self.origin_y);
		WriteCoord(MSG_ENTITY, self.origin_z);
		WriteCoord(MSG_ENTITY, self.velocity_x);
		WriteCoord(MSG_ENTITY, self.velocity_y);
		WriteCoord(MSG_ENTITY, self.velocity_z);
		WriteCoord(MSG_ENTITY, self.casetype);
	}
	return (TRUE);
};

void() casing_placement =
{
	if ((self.flags & FL_ONGROUND))
	{
		self.angles_x = (crandom() * 10);
		if ((autocvar_casingusegyro == 1))
		{
			MonsterPhysics(self, autocvar_casingmass);
		}
		self.nextthink = (time + autocvar_casinglifetime);
		self.think = gibsfade_noblood;
		return;
	}
	self.nextthink = (time + 0.1);
};

void(float checkgrunt) casing =
{
	local entity shellcasing;
	local vector ejectpos;
	local float correction;

	shellcasing = spawn();
	correction = autocvar_casingejectpos - 8;
	if ((checkgrunt == 0))
	{
		if (((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
		{
			ejectpos = (((self.origin + self.view_ofs) + (v_forward * 10)) + (v_right * 8)) + (v_up * correction);
		}
		else
		{
			if (((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
			{
				ejectpos = (((self.origin + self.view_ofs) + (v_forward * 10)) + (v_right * autocvar_weapon_position_adjustable_projectile_casing_offset)) + (v_up * correction);
			}
			else
			{
				ejectpos = (((self.origin + self.view_ofs) + (v_forward * 10)) + (v_right * 2)) + (v_up * correction);
			}
		}
		shellcasing.angles = self.v_angle;
		shellcasing.angles_x = (shellcasing.angles_x * -1);
	}
	else
	{
		makevectors(self.angles);
		ejectpos = ((self.origin + (v_up * 13)) + (v_right * 7)) + (v_forward * 8);
		shellcasing.angles = self.angles;
	}
	setorigin(shellcasing, ejectpos);
	setmodel(shellcasing, "progs/casing.mdl");
	shellcasing.scale = 0.9;
	setsize(shellcasing, '0 0 -2', VEC_ORIGIN);
	shellcasing.alpha = 1;
	shellcasing.movetype = MOVETYPE_BOUNCE;
	shellcasing.solid = SOLID_TRIGGER;
	shellcasing.touch = shellcasing_touch;
	shellcasing.takedamage = 0;
	shellcasing.velocity = ((((((self.velocity * 2.5) * 0.25) + (v_right * 97)) + (v_up * 143)) + (v_forward * 20)) + (randomvec() * 22));
	if ((coop || deathmatch))
	{
		shellcasing.casetype = CASING_SHELL;
		shellcasing.SendEntity = casing_sendtocsqc;
		shellcasing.SendFlags = (shellcasing.SendFlags | 1);
		shellcasing.think = SUB_Remove;
		shellcasing.nextthink = (time + 0.01);
		return;
	}
	shellcasing.avelocity = ('390 322 290' + (randomvec() * 44));
	shellcasing.nextthink = time;
	shellcasing.think = casing_placement;
	shellcasing.cansplash = TRUE;
	shellcasing.gravity = 1.3;
};

void(float checkgrunt) nailcasing =
{
	local entity nailcasing;
	local vector ejectpos;
	local float correction;

	nailcasing = spawn();
	correction = autocvar_casingejectpos - 8;
	if ((checkgrunt == 0))
	{
		if (((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
		{
			ejectpos = (((self.origin + self.view_ofs) + (v_forward * 8)) + (v_right * 8)) + (v_up * correction);
		}
		else
		{
			if (((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
			{
				ejectpos = (((self.origin + self.view_ofs) + (v_forward * 8)) + (v_right * autocvar_weapon_position_adjustable_projectile_casing_offset)) + (v_up * correction);
			}
			else
			{
				ejectpos = (((self.origin + self.view_ofs) + (v_forward * 8)) + (v_right * 2)) + (v_up * correction);
			}
		}
		nailcasing.angles = self.v_angle;
		nailcasing.angles_x = (nailcasing.angles_x * -1);
	}
	else
	{
		makevectors(self.angles);
		ejectpos = ((self.origin + (v_up * 13)) + (v_right * 7)) + (v_forward * 8);
		nailcasing.angles = self.angles;
	}
	setorigin(nailcasing, ejectpos);
	setmodel(nailcasing, "progs/nailcasing.mdl");
	nailcasing.scale = 0.7;
	setsize(nailcasing, VEC_ORIGIN, VEC_ORIGIN);
	nailcasing.alpha = 1;
	nailcasing.movetype = MOVETYPE_BOUNCE;
	nailcasing.solid = SOLID_TRIGGER;
	nailcasing.touch = nailcasing_touch;
	nailcasing.takedamage = 0;
	nailcasing.velocity = ((((((self.velocity * 3) * 0.25) + (v_right * 87)) + (v_up * 103)) + (v_forward * 40)) + (randomvec() * 22));
	if ((coop || deathmatch))
	{
		nailcasing.casetype = CASING_NAIL;
		nailcasing.SendEntity = casing_sendtocsqc;
		nailcasing.SendFlags = (nailcasing.SendFlags | 1);
		nailcasing.think = SUB_Remove;
		nailcasing.nextthink = (time + 0.01);
		return;
	}
	nailcasing.avelocity = ('390 222 400' + (randomvec() * 44));
	nailcasing.nextthink = time;
	nailcasing.think = casing_placement;
	nailcasing.cansplash = TRUE;
	nailcasing.gravity = 1.3;
};

void(float checkgrunt) missilecase =
{
	local entity rocketcase;
	local vector ejectpos;
	local float correction;

	rocketcase = spawn();
	correction = autocvar_casingejectpos - 8;
	if ((checkgrunt == 0))
	{
		if (((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
		{
			ejectpos = (((self.origin + self.view_ofs) + (v_forward * 10)) + (v_right * 8)) + (v_up * correction);
		}
		else
		{
			if (((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable) && !cvar("chase_active")))
			{
				ejectpos = (((self.origin + self.view_ofs) + (v_forward * 10)) + (v_right * autocvar_weapon_position_adjustable_projectile_casing_offset)) + (v_up * correction);
			}
			else
			{
				ejectpos = (((self.origin + self.view_ofs) + (v_forward * 10)) + (v_right * 2)) + (v_up * correction);
			}
		}
		rocketcase.angles = self.v_angle;
		rocketcase.angles_x = (rocketcase.angles_x * -1);
	}
	else
	{
		makevectors(self.angles);
		ejectpos = ((self.origin + (v_up * 13)) + (v_right * 7)) + (v_forward * 8);
		rocketcase.angles = self.angles;
	}
	setorigin(rocketcase, ejectpos);
	setmodel(rocketcase, "progs/missilecasing.mdl");
	rocketcase.scale = 1;
	setsize(rocketcase, VEC_ORIGIN, VEC_ORIGIN);
	rocketcase.alpha = 1;
	rocketcase.movetype = MOVETYPE_BOUNCE;
	rocketcase.solid = SOLID_TRIGGER;
	rocketcase.touch = rockcasing_touch;
	rocketcase.takedamage = 0;
	rocketcase.velocity = (((((self.velocity * 2.5) * 0.25) + (v_right * 77)) + (v_up * 33)) + (randomvec() * 22));
	if ((coop || deathmatch))
	{
		rocketcase.casetype = CASING_ROCKET;
		rocketcase.SendEntity = casing_sendtocsqc;
		rocketcase.SendFlags = (rocketcase.SendFlags | 1);
		rocketcase.think = SUB_Remove;
		rocketcase.nextthink = (time + 0.03);
		return;
	}
	rocketcase.avelocity = ('0 22 0' + (randomvec() * 44));
	rocketcase.nextthink = time;
	rocketcase.think = casing_placement;
	rocketcase.cansplash = TRUE;
};

void() W_Attack =
{
	local float r;

	if (!W_CheckNoAmmo())
	{
		return;
	}
	if (((self.meleeing == 1) || (self.throwing == 1)))
	{
		return;
	}
	makevectors(self.v_angle);
	self.show_hostile = (time + 1);
	if ((self.weapon == IT_MEGAMAN))
	{
		MegaMan_Attack();
		return;
	}
	if ((self.weapon == IT_BANANA))
	{
		Banana_Attack();
		return;
	}
	if ((self.weapon == IT_FUNGUN))
	{
		FunGun_Attack();
		return;
	}
	if ((self.weapon == IT_AXE))
	{
		sound7(self, CHAN_WEAPON, "weapons/ax1.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
		if ((self.waterlevel >= 2))
		{
			player_axes1();
		}
		else
		{
			r = random();
			if ((r < 0.25))
			{
				player_axe1();
			}
			else
			{
				if ((r < 0.5))
				{
					player_axeb1();
				}
				else
				{
					if ((r < 0.75))
					{
						player_axec1();
					}
					else
					{
						player_axed1();
					}
				}
			}
		}
		W_FireAxe2();
		self.attack_timer = 1;
		self.attack_finished = (time + 0.475);
	}
	else
	{
		if ((self.weapon == IT_SHOTGUN))
		{
			if ((self.waterlevel >= 2))
			{
				player_shotswim1();
			}
			else
			{
				player_shot1();
			}
			Goo_Fire();	// the Goo Gun (goo.qc), full auto
			self.attack_timer = 1;
			if ((self.rapid_timer > 0))
			{
				self.attack_finished = (time + GOO_REFIRE_RAPID);
			}
			else
			{
				self.attack_finished = (time + GOO_REFIRE);
			}
			if ((autocvar_effects_explosion_shake != 0))
			{
				self.viewzoom = 1.017;
			}
		}
		else
		{
			if ((self.weapon == IT_SUPER_SHOTGUN))
			{
				if ((self.waterlevel >= 2))
				{
					player_shotswim1();
				}
				else
				{
					player_shot1();
				}
				W_FireSuperShotgun();
				self.attack_timer = 1;
				if ((autocvar_effects_explosion_shake != 0))
				{
					self.viewzoom = 1.02;
				}
				if ((autocvar_vanilla_ssg != 0))
				{
					self.attack_finished = (time + 0.63);
				}
				else
				{
					BM_FiredSSG();
				}
			}
			else
			{
				if ((self.weapon == IT_NAILGUN))
				{
					if ((self.waterlevel >= 2))
					{
						player_swimnail1();
					}
					else
					{
						player_nail1();
					}
					self.attack_timer = 1;
				}
				else
				{
					if ((self.weapon == IT_SUPER_NAILGUN))
					{
						if (Milky_CanFire())
						{
							Milky_Fire();	// the Milky Gun winds up and throws the Pink Lady (milky.qc)
						}
					}
					else
					{
						if ((self.weapon == IT_GRENADE_LAUNCHER))
						{
							if ((self.waterlevel >= 2))
							{
								player_shotswim1();
							}
							else
							{
								player_rocket1();
							}
							W_FireGrenade();
							self.attack_timer = 1;
							if ((autocvar_cheat_crazyexplosives == 1))
							{
								self.attack_finished = (time + 0.07);
							}
							else
							{
								self.attack_finished = (time + 0.55);
							}
						}
						else
						{
							if ((self.weapon == IT_ROCKET_LAUNCHER))
							{
								if ((self.waterlevel >= 2))
								{
									player_shotswim1();
								}
								else
								{
									player_rocket1();
								}
								W_FireRocket();
								self.attack_timer = 1;
								if ((autocvar_cheat_crazyexplosives == 1))
								{
									self.attack_finished = (time + 0.07);
								}
								else
								{
									self.attack_finished = (time + 0.8);
								}
							}
							else
							{
								if ((self.weapon == IT_LIGHTNING))
								{
									if ((autocvar_mage_weapon && !cvar("chase_active")))
									{
										player_mage1();
										self.attack_finished = (time + 0.1);
									}
									else
									{
										player_light1();
										self.attack_finished = (time + 0.1);
										sound7(self, CHAN_AUTO, "weapons/lstart.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
									}
								}
								else
								{
									if ((self.weapon == IT_CHAINSAW))
									{
										if ((self.waterlevel >= 2))
										{
											player_swimsaw1();
										}
										else
										{
											player_chainsaw1();
										}
										if (!trace_ent.takedamage)
										{
											sound7(self, CHAN_WEAPON, "weapons/sawatck.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
										}
										self.attack_finished = (time + 0.45);
									}
									else
									{
										if ((self.weapon == IT_LASER_CANNON))
										{
											player_laser1();
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
};

void() W_ChangeWeapon =
{
	local float it;
	local float am;
	local float fl;

	if ((self.has_fired == 1))
	{
		return;
	}
	it = self.items;
	am = 0;
	self.idletimer = 1;
	self.switchtimer = -5;
	if ((self.impulse == 1))
	{
		if ((self.weapon == IT_AXE))
		{
			fl = IT_CHAINSAW;
			if ((self.items & IT_CHAINSAW))
			{
				sprint(self, "Chainsaw\n");
			}
		}
		else
		{
			fl = IT_AXE;
		}
	}
	else
	{
		if ((self.impulse == 2))
		{
			fl = IT_SHOTGUN;
			if ((self.ammo_shells < 1))
			{
				am = 1;
			}
		}
		else
		{
			if ((self.impulse == 3))
			{
				if (((autocvar_vanilla_ssg == 0) && (self.bm_ssgburst == 15)))
				{
					self.bm_ssgburst = 16;
				}
				fl = IT_SUPER_SHOTGUN;
				if ((self.ammo_shells < 2))
				{
					am = 1;
				}
			}
			else
			{
				if ((self.impulse == 4))
				{
					fl = IT_NAILGUN;
					if ((self.ammo_nails < 1))
					{
						am = 1;
					}
				}
				else
				{
					if ((self.impulse == 5))
					{
						fl = IT_SUPER_NAILGUN;
						if ((self.ammo_nails < 2))
						{
							am = 1;
						}
					}
					else
					{
						if ((self.impulse == 6))
						{
							fl = IT_GRENADE_LAUNCHER;
							if ((self.ammo_rockets < 1))
							{
								am = 1;
							}
						}
						else
						{
							if ((self.impulse == 7))
							{
								fl = IT_ROCKET_LAUNCHER;
								if ((self.ammo_rockets < 1))
								{
									am = 1;
								}
							}
							else
							{
								if ((self.impulse == 8))
								{
									if (((self.items == IT_LASER_CANNON) && (self.items != IT_LIGHTNING)))
									{
										fl = IT_LASER_CANNON;
										if ((self.ammo_cells < 1))
										{
											am = 1;
										}
									}
									else
									{
										if ((self.items == IT_LIGHTNING))
										{
											fl = IT_LIGHTNING;
											if ((self.ammo_cells < 1))
											{
												am = 1;
											}
										}
										else
										{
											if ((self.weapon == IT_LIGHTNING))
											{
												fl = IT_LASER_CANNON;
												if ((self.ammo_cells < 1))
												{
													am = 1;
												}
											}
											else
											{
												fl = IT_LIGHTNING;
												if (!(self.items & IT_LIGHTNING))
												{
													fl = IT_LASER_CANNON;		// no lightning gun (it is not in every map): the key picks the CCC gun
												}
												if ((self.ammo_cells < 1))
												{
													am = 1;
												}
											}
										}
									}
								}
								else
								{
									if ((self.impulse == 252))
									{
										fl = IT_CHAINSAW;
										if ((self.items & IT_CHAINSAW))
										{
											sprint(self, "Chainsaw\n");
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
	if (!(self.items & fl))
	{
		sprint(self, "no weapon.\n");
		return;
	}
	if (autocvar_bm_reload)
	{
		am = 0;
	}
	if (am)
	{
		sprint(self, "not enough ammo.\n");
		return;
	}
	self.weapon = fl;
	W_SetCurrentAmmo();
	if ((autocvar_changeweaponsounds && (self.ishuman == TRUE)))
	{
		if ((fl == IT_AXE))
		{
			sound7(self, CHAN_VOICE, "weapons/weapon1.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
		}
		else
		{
			if ((fl == IT_SHOTGUN))
			{
				sound7(self, CHAN_VOICE, "weapons/weapon2.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
			}
			else
			{
				if ((fl == IT_SUPER_SHOTGUN))
				{
					sound7(self, CHAN_VOICE, "weapons/weapon3.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
				}
				else
				{
					if ((fl == IT_NAILGUN))
					{
						sound7(self, CHAN_VOICE, "weapons/weapon4.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
					}
					else
					{
						if ((fl == IT_SUPER_NAILGUN))
						{
							sound7(self, CHAN_VOICE, "weapons/weapon5.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
						}
						else
						{
							if ((fl == IT_GRENADE_LAUNCHER))
							{
								sound7(self, CHAN_VOICE, "weapons/weapon6.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
							}
							else
							{
								if ((fl == IT_ROCKET_LAUNCHER))
								{
									sound7(self, CHAN_VOICE, "weapons/weapon7.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
								}
								else
								{
									if ((fl == IT_LIGHTNING))
									{
										if ((!autocvar_mage_weapon || cvar("chase_active")))
										{
											sound7(self, CHAN_VOICE, "weapons/weapon8.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
										}
									}
									else
									{
										if ((fl == IT_LASER_CANNON))
										{
											sound7(self, CHAN_VOICE, "hipweap/weapon9.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
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
};

void() CheatCommand =
{
	if ((deathmatch || coop))
	{
		return;
	}
	self.ammo_rockets = autocvar_rockets_max_capacity;
	self.ammo_nails = autocvar_nails_max_capacity;
	self.ammo_shells = autocvar_shells_max_capacity;
	self.items = (((((((((((self.items | IT_AXE) | IT_SHOTGUN) | IT_SUPER_SHOTGUN) | IT_NAILGUN) | IT_SUPER_NAILGUN) | IT_GRENADE_LAUNCHER) | IT_ROCKET_LAUNCHER) | IT_CHAINSAW) | IT_LASER_CANNON) | IT_KEY1) | IT_KEY2);
	self.ammo_cells = autocvar_cells_max_capacity;
	self.items = (self.items | IT_LIGHTNING);
	self.grenade_ammo = 6;
	MegaMan_Give(self);
	Banana_Give(self);
	FunGun_Give(self);
	self.weapon = IT_ROCKET_LAUNCHER;
	self.impulse = 0;
	W_SetCurrentAmmo();
};

void() CycleWeaponCommand =
{
	local float it;
	local float am;

	it = (self.items | IT_FUNGUN);
	self.impulse = 0;
	self.idletimer = 1;
	self.switchtimer = -8;
	do
	{
		am = 0;
		if ((self.weapon == IT_FUNGUN))
		{
			if (!FunGun_CycleNext())
			{
				self.weapon = IT_AXE;
			}
		}
		else if ((self.weapon == IT_BANANA))
		{
			self.weapon = IT_FUNGUN;
			self.fg_sel = 1;
		}
		else if ((self.weapon == IT_MEGAMAN))
		{
			self.weapon = IT_BANANA;
		}
		else if ((self.weapon == IT_LASER_CANNON))
		{
			self.weapon = IT_MEGAMAN;
		}
		else
		{
			if ((self.weapon == IT_AXE))
			{
				self.weapon = IT_CHAINSAW;
			}
			else
			{
				if ((self.weapon == IT_CHAINSAW))
				{
					self.weapon = IT_SHOTGUN;
					if ((self.ammo_shells < 1))
					{
						am = 1;
					}
				}
				else
				{
					if ((self.weapon == IT_SHOTGUN))
					{
						self.weapon = IT_SUPER_SHOTGUN;
						if ((self.ammo_shells < 2))
						{
							am = 1;
						}
					}
					else
					{
						if ((self.weapon == IT_SUPER_SHOTGUN))
						{
							self.weapon = IT_NAILGUN;
							if ((self.ammo_nails < 1))
							{
								am = 1;
							}
						}
						else
						{
							if ((self.weapon == IT_NAILGUN))
							{
								self.weapon = IT_SUPER_NAILGUN;
								if ((self.ammo_nails < 2))
								{
									am = 1;
								}
							}
							else
							{
								if ((self.weapon == IT_SUPER_NAILGUN))
								{
									self.weapon = IT_GRENADE_LAUNCHER;
									if ((self.ammo_rockets < 1))
									{
										am = 1;
									}
								}
								else
								{
									if ((self.weapon == IT_GRENADE_LAUNCHER))
									{
										self.weapon = IT_ROCKET_LAUNCHER;
										if ((self.ammo_rockets < 1))
										{
											am = 1;
										}
									}
									else
									{
										if ((self.weapon == IT_ROCKET_LAUNCHER))
										{
											self.weapon = IT_LIGHTNING;
											if ((self.ammo_cells < 1))
											{
												am = 1;
											}
										}
										else
										{
											if ((self.weapon == IT_LIGHTNING))
											{
												self.weapon = IT_LASER_CANNON;
												if ((self.ammo_cells < 1))
												{
													am = 1;
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
		if (((it & self.weapon) && (am == 0)))
		{
			W_SetCurrentAmmo();
			if (autocvar_changeweaponsounds)
			{
				if ((self.weapon == IT_AXE))
				{
					sound7(self, CHAN_VOICE, "weapons/weapon1.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
				}
				else
				{
					if ((self.weapon == IT_SHOTGUN))
					{
						sound7(self, CHAN_VOICE, "weapons/weapon2.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
					}
					else
					{
						if ((self.weapon == IT_SUPER_SHOTGUN))
						{
							sound7(self, CHAN_VOICE, "weapons/weapon3.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
						}
						else
						{
							if ((self.weapon == IT_NAILGUN))
							{
								sound7(self, CHAN_VOICE, "weapons/weapon4.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
							}
							else
							{
								if ((self.weapon == IT_SUPER_NAILGUN))
								{
									sound7(self, CHAN_VOICE, "weapons/weapon5.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
								}
								else
								{
									if ((self.weapon == IT_GRENADE_LAUNCHER))
									{
										sound7(self, CHAN_VOICE, "weapons/weapon6.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
									}
									else
									{
										if ((self.weapon == IT_ROCKET_LAUNCHER))
										{
											sound7(self, CHAN_VOICE, "weapons/weapon7.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
										}
										else
										{
											if ((self.weapon == IT_LIGHTNING))
											{
												if ((!autocvar_mage_weapon || cvar("chase_active")))
												{
													sound7(self, CHAN_VOICE, "weapons/weapon8.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
												}
											}
											else
											{
												if ((self.weapon == IT_LASER_CANNON))
												{
													sound7(self, CHAN_VOICE, "hipweap/weapon9.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
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
			return;
		}
	} while(1);
};

void() CycleWeaponReverseCommand =
{
	local float it;
	local float am;

	it = (self.items | IT_FUNGUN);
	self.impulse = 0;
	self.idletimer = 1;
	self.switchtimer = -8;
	do
	{
		am = 0;
		if ((self.weapon == IT_FUNGUN))
		{
			if (!FunGun_CyclePrev())
			{
				self.weapon = IT_BANANA;
			}
		}
		else if ((self.weapon == IT_BANANA))
		{
			self.weapon = IT_MEGAMAN;
		}
		else if ((self.weapon == IT_MEGAMAN))
		{
			self.weapon = IT_LASER_CANNON;
			if ((self.ammo_cells < 1))
			{
				am = 1;
			}
		}
		else if ((self.weapon == IT_LASER_CANNON))
		{
			self.weapon = IT_LIGHTNING;
			if ((self.ammo_cells < 1))
			{
				am = 1;
			}
		}
		else
		{
			if ((self.weapon == IT_LIGHTNING))
			{
				self.weapon = IT_ROCKET_LAUNCHER;
				if ((self.ammo_rockets < 1))
				{
					am = 1;
				}
			}
			else
			{
				if ((self.weapon == IT_ROCKET_LAUNCHER))
				{
					self.weapon = IT_GRENADE_LAUNCHER;
					if ((self.ammo_rockets < 1))
					{
						am = 1;
					}
				}
				else
				{
					if ((self.weapon == IT_GRENADE_LAUNCHER))
					{
						self.weapon = IT_SUPER_NAILGUN;
						if ((self.ammo_nails < 2))
						{
							am = 1;
						}
					}
					else
					{
						if ((self.weapon == IT_SUPER_NAILGUN))
						{
							self.weapon = IT_NAILGUN;
							if ((self.ammo_nails < 1))
							{
								am = 1;
							}
						}
						else
						{
							if ((self.weapon == IT_NAILGUN))
							{
								self.weapon = IT_SUPER_SHOTGUN;
								if ((self.ammo_shells < 2))
								{
									am = 1;
								}
							}
							else
							{
								if ((self.weapon == IT_SUPER_SHOTGUN))
								{
									self.weapon = IT_SHOTGUN;
									if ((self.ammo_shells < 1))
									{
										am = 1;
									}
								}
								else
								{
									if ((self.weapon == IT_SHOTGUN))
									{
										self.weapon = IT_CHAINSAW;
									}
									else
									{
										if ((self.weapon == IT_CHAINSAW))
										{
											self.weapon = IT_AXE;
										}
										else
										{
											if ((self.weapon == IT_AXE))
											{
												self.weapon = IT_FUNGUN;
												self.fg_sel = FG_COUNT;
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
		if (((it & self.weapon) && (am == 0)))
		{
			W_SetCurrentAmmo();
			if (autocvar_changeweaponsounds)
			{
				if ((self.weapon == IT_AXE))
				{
					sound7(self, CHAN_VOICE, "weapons/weapon1.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
				}
				else
				{
					if ((self.weapon == IT_SHOTGUN))
					{
						sound7(self, CHAN_VOICE, "weapons/weapon2.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
					}
					else
					{
						if ((self.weapon == IT_SUPER_SHOTGUN))
						{
							sound7(self, CHAN_VOICE, "weapons/weapon3.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
						}
						else
						{
							if ((self.weapon == IT_NAILGUN))
							{
								sound7(self, CHAN_VOICE, "weapons/weapon4.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
							}
							else
							{
								if ((self.weapon == IT_SUPER_NAILGUN))
								{
									sound7(self, CHAN_VOICE, "weapons/weapon5.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
								}
								else
								{
									if ((self.weapon == IT_GRENADE_LAUNCHER))
									{
										sound7(self, CHAN_VOICE, "weapons/weapon6.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
									}
									else
									{
										if ((self.weapon == IT_ROCKET_LAUNCHER))
										{
											sound7(self, CHAN_VOICE, "weapons/weapon7.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
										}
										else
										{
											if ((self.weapon == IT_LIGHTNING))
											{
												if ((!autocvar_mage_weapon || cvar("chase_active")))
												{
													sound7(self, CHAN_VOICE, "weapons/weapon8.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
												}
											}
											else
											{
												if ((self.weapon == IT_LASER_CANNON))
												{
													sound7(self, CHAN_VOICE, "hipweap/weapon9.wav", autocvar_changeweaponsounds, ATTN_NORM, self.PLR_SNDSPD);
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
			return;
		}
	} while(1);
};

void() ServerflagsCommand =
{
	serverflags = (serverflags * 2) + 1;
};

void() QuadCheat =
{
	if ((deathmatch || coop))
	{
		return;
	}
	precache_sound("items/damage.wav");
	precache_sound("items/damage2.wav");
	precache_sound("items/damage3.wav");
	sound7(self, CHAN_ITEM, "items/damage.wav", 1, ATTN_NORM, SNDSPD);
	sprint(self, "You got the ");
	sprint(self, "Quad Damage");
	sprint(self, "\n");
	self.super_time = 1;
	self.super_damage_finished = (time + 30);
	self.super_damage_counter = 30;
	self.items = (self.items | IT_QUAD);
};

void() RingCheat =
{
	if ((deathmatch || coop))
	{
		return;
	}
	precache_sound("items/inv1.wav");
	precache_sound("items/inv2.wav");
	precache_sound("items/inv3.wav");
	sound(self, CHAN_ITEM, "items/inv1.wav", 1, ATTN_NORM);
	sprint(self, "You got the ");
	sprint(self, "Ring of Shadows");
	sprint(self, "\n");
	self.invisible_time = 1;
	self.invisible_finished = (time + 30);
	self.invisible_counter = 30;
	self.items = (self.items | IT_INVISIBILITY);
};

void() PentCheat =
{
	if ((deathmatch || coop))
	{
		return;
	}
	precache_sound("items/protect.wav");
	precache_sound("items/protect2.wav");
	precache_sound("items/protect3.wav");
	sound(self, CHAN_ITEM, "items/protect.wav", 1, ATTN_NORM);
	sprint(self, "You got the ");
	sprint(self, "Pentagram of Protection");
	sprint(self, "\n");
	self.invincible_time = 1;
	self.invincible_finished = (time + 30);
	self.invincible_counter = 30;
	self.items = (self.items | IT_INVULNERABILITY);
};

void() BiosuitCheat =
{
	if ((deathmatch || coop))
	{
		return;
	}
	precache_sound("items/suit.wav");
	precache_sound("items/suit2.wav");
	sound(self, CHAN_ITEM, "items/suit.wav", 1, ATTN_NORM);
	sprint(self, "You got the ");
	sprint(self, "Biosuit");
	sprint(self, "\n");
	self.rad_time = 1;
	self.radsuit_finished = (time + 30);
	self.radsuit_counter = 30;
	self.items = (self.items | IT_SUIT);
};

void() Genocide =
{
	local entity head;

	if ((deathmatch || coop))
	{
		return;
	}
	if ((self.classname == "player"))
	{
		bprint("Genocide!\n");
	}
	head = nextent(world);
	while ((head != world))
	{
		if (((head.health > 0) && (head.flags & FL_MONSTER)))
		{
			if ((self.classname == "monster_dfury_boss"))
			{
				T_Damage(head, world, world, head.health);
			}
			else
			{
				T_Damage(head, world, world, (head.health + 10));
			}
		}
		head = nextent(head);
	}
};

void() ChaseCam =
{
	if (cvar("chase_active"))
	{
		stuffcmd(self, "chase_active 0\n");
	}
	else
	{
		stuffcmd(self, "chase_active 1\n");
	}
};

void() ImpulseCommands =
{
	Vehicles_Impulse();
	LanProps_Impulse();
	if ((self.impulse == MM_IMPULSE))
	{
		MegaMan_Select();
	}
	if ((self.impulse == BN_IMPULSE))
	{
		Banana_Select();
	}
	if (((self.impulse >= FG_IMPULSE) && (self.impulse < (FG_IMPULSE + FG_COUNT))))
	{
		FunGun_Select(((self.impulse - FG_IMPULSE) + 1));
	}
	if ((self.impulse == 3))
	{
		if (((((self.weapon == IT_SUPER_SHOTGUN) && (autocvar_vanilla_ssg == 0)) && (self.bm_ssgburst == 15)) && ((time - 0.45) < self.attack_finished)))
		{
			self.impulse = 0;
			return;
		}
	}
	if (((self.impulse >= 1) && (self.impulse <= 8)))
	{
		W_ChangeWeapon();
	}
	if ((self.impulse == 9))
	{
		CheatCommand();
	}
	if ((self.impulse == 10))
	{
		CycleWeaponCommand();
	}
	if ((self.impulse == 11))
	{
		ServerflagsCommand();
	}
	if ((self.impulse == 12))
	{
		CycleWeaponReverseCommand();
	}
	if (((self.impulse == 13) && cvar("sv_cheats")))
	{
		swap_team();
	}
	if ((self.impulse == 20))
	{
		self.impulse = 0;
		meleeaxe();
	}
	if (((self.impulse == 21) && cvar("sv_cheats")))
	{
		saw_spawn();
	}
	if ((self.impulse == 30))
	{
		if ((autocvar_flashlight_type == 1))
		{
			flash_toggle();
		}
		else
		{
			if ((autocvar_flashlight_type == 2))
			{
				flash_toggle_cubemap();
			}
		}
	}
	if ((self.impulse == 40))
	{
		if (self.personal_teleporter_spawned)
		{
			self.personal_teleporter_start_beam = 1;
		}
		else
		{
			player_teleport();
		}
	}
	if ((self.impulse == 204))
	{
		self.dmenu = TRUE;
	}
	if ((self.impulse == 205))
	{
		Genocide();
	}
	if ((self.impulse == 206))
	{
		ChaseCam();
	}
	if (((self.impulse == 215) && (self.attack_timer == 0)))
	{
		self.impulse = 0;
		self.attack_timer = 0;
		// the proximity grenade (ThrowNade) is removed: impulse 215 does nothing
	}
	if (((self.impulse == 250) && cvar("sv_cheats")))
	{
		TimeRuneCheat();
	}
	if ((self.impulse == 251))
	{
		RingCheat();
	}
	if ((self.impulse == 253))
	{
		PentCheat();
	}
	if ((self.impulse == 254))
	{
		SpawnRebreather();
		BiosuitCheat();
	}
	if ((self.impulse == 255))
	{
		QuadCheat();
	}
	if ((self.impulse == 17))
	{
		FloatHead_Summon();	// a floating head right in front of you (floathead.qc)
	}
	if (((self.impulse == 19) && cvar("sv_cheats")))
	{
		Bryan_Summon();		// Tinfoil-Hat Bryan & His Demons (bryan.qc)
	}
	if (((self.impulse == 22) && cvar("sv_cheats")))
	{
		David_SummonSquad();	// David Ojeda + all 3 Running Pregnant Hispanic Women (david.qc)
	}
	if (((self.impulse == 23) && cvar("sv_cheats")))
	{
		David_Summon();		// Solo Fast-Running David Ojeda (david.qc)
	}
	if (((self.impulse == 24) && cvar("sv_cheats")))
	{
		David_SummonSlot();	// David Ojeda Playing 360° Vegas Slot Machine (david.qc)
	}
	if (((self.impulse == 25) && cvar("sv_cheats")))
	{
		PregRunners_Summon();	// 3 Running Pregnant Hispanic Women (david.qc)
	}
	if (((self.impulse == 26) && cvar("sv_cheats")))
	{
		Daniel_Summon4AM();		// 4 AM Daniel + Angry 4 AM Dad + Framed Meme Poster (daniel.qc)
	}
	if (((self.impulse == 27) && cvar("sv_cheats")))
	{
		Daniel_Summon();		// Solo Autonomous Daniel (daniel.qc)
	}
	if (((self.impulse == 28) && cvar("sv_cheats")))
	{
		Daniel_SummonLAN();		// 360° Bakersfield LAN Station Daniel (daniel.qc)
	}
	if (((self.impulse == 29) && cvar("sv_cheats")))
	{
		Dad4AM_Summon();		// Angry 4 AM Dad (daniel.qc)
	}
	self.impulse = 0;
};

void() checkzombie =
{
	local vector source;

	makevectors(self.v_angle);
	source = self.origin + '0 0 16';
	traceline(source, (source + (v_forward * 777)), FALSE, self);
	if (((trace_ent.model == "progs/zombie_new.mdl") || (trace_ent.model == "progs/zombie_new_headless.mdl")))
	{
		self.weaponmodel = "progs/v_hammer.mdl";
		self.glow_color = 75;
		self.glow_size = 888;
	}
	else
	{
		self.weaponmodel = "progs/v_hammer.mdl";
		self.glow_color = 0;
		self.glow_size = 0;
	}
};

void() W_WeaponFrame =
{
	BM_Frame();
	BM_LifeFrame();
	BM_TestImpulses();
	MegaMan_ViewFrame();
	FunGun_ViewFrame();
	Goo_PlayerFrame();	// gummed-up players crawl
	Milky_PlayerFrame();	// breadcrumbs for the ladies, sliding on milk (milky.qc)
	Jetpack_Frame();	// switch on/off, hover, climb (jetpack.qc)
	Hammer_PlayerFrame();	// charge, swing, spin (hammer.qc)
	LtGun_PlayerFrame();	// the laptop's held model and the shock (ltgun.qc)
	if (FD_Frame())
	{
		return;	// flying a Rob Dob head: nothing else happens (floathead.qc)
	}
	if (Veh_DriveFrame())
	{
		return;	// driving the van: nothing else happens (vehicle_drive.qc)
	}
	if (JohnBird_Frame())
	{
		return;	// flying Winged Breezy-Hair John (john_bird.qc)
	}
	if (Saw_LockFrame())
	{
		return;	// stuck to a chainsawed enemy: the saw keeps going on its own (Saw_LockFrame)
	}
	if (((deathmatch || coop) && (mapstart == 0)))
	{
		if ((autocvar_z_coopconfig == 0))
		{
			stuffcmd(self, "exec q15_config_coop.cfg\n");
			cvar_set("z_coopconfig", "1");
			stuffcmd(self, "restart\n");
		}
		mapstart = 1;
	}
	else
	{
		if (((!deathmatch || !coop) && (mapstart == 0)))
		{
			if ((autocvar_z_coopconfig == 1))
			{
				stuffcmd(self, "exec q15_config.cfg\n");
				cvar_set("z_coopconfig", "0");
				stuffcmd(self, "restart\n");
			}
			mapstart = 1;
		}
	}
	if (!(deathmatch || coop))
	{
		if ((world.model == "maps/start.bsp"))
		{
			if ((welcomenote == 1))
			{
				if ((self.welcomeshown <= 20))
				{
					if ((time > self.welcomeshown))
					{
						if ((self.welcomeshown == 0))
						{
							self.welcomeshown = (time + 1);
						}
						else
						{
							self.welcomeshown = (time + 1.9);
							centerprint(self, "Welcome to Quake 1.5, \n\n\n forked from Seven's Small Mod Compilation 5.30\n\n\n\nPress the ^2'Home'^7 key to access mod menus for keybinds and game options\n");
						}
					}
				}
			}
		}
	}
	if ((autocvar_zombieaxeanimation == 1))
	{
		if ((autocvar_zombienewmodelproperties >= 1))
		{
			if ((self.weapon == IT_AXE))
			{
				checkzombie();
			}
			else
			{
				self.glow_color = 0;
				self.glow_size = 0;
			}
		}
	}
	if (((self.impulse == 20) || (self.impulse == 215)))
	{
		if ((((self.meleeing == 0) && (self.attack_timer > 0)) && (self.throwing == 0)))
		{
			if ((self.weapon == IT_SUPER_SHOTGUN))
			{
				if ((autocvar_vanilla_ssg > 0))
				{
					if (((time + 0.375) > self.attack_finished))
					{
						if ((self.impulse == 215))
						{
							ThrowNade();
							self.impulse = 0;
							return;
						}
						else
						{
							meleeaxe();
							self.impulse = 0;
						}
					}
				}
				else
				{
					if ((autocvar_pushbacklight == 16))
					{
						if (((time + 0.65) > self.attack_finished))
						{
							if ((self.impulse == 215))
							{
								ThrowNade();
								self.impulse = 0;
								return;
							}
							else
							{
								meleeaxe();
								self.impulse = 0;
							}
						}
					}
					else
					{
						if ((autocvar_pushbacklight == 15))
						{
							if (((time - 0.225) > self.attack_finished))
							{
								if ((self.impulse == 215))
								{
									ThrowNade();
									self.impulse = 0;
									return;
								}
								else
								{
									meleeaxe();
									self.impulse = 0;
								}
							}
							else
							{
								return;
							}
						}
					}
				}
			}
			else
			{
				if ((self.weapon == IT_SHOTGUN))
				{
					if (((time + 0.2) > self.attack_finished))
					{
						if ((self.impulse == 215))
						{
							ThrowNade();
							self.impulse = 0;
							return;
						}
						else
						{
							meleeaxe();
							self.impulse = 0;
						}
					}
				}
				else
				{
					if ((((self.weapon == IT_NAILGUN) || (self.weapon == IT_SUPER_NAILGUN)) && ((time + 0.05) > self.attack_finished)))
					{
						if ((self.impulse == 215))
						{
							ThrowNade();
							self.impulse = 0;
							return;
						}
						else
						{
							meleeaxe();
							self.impulse = 0;
						}
					}
					else
					{
						if ((self.weapon == IT_AXE))
						{
							if (((time + 0.285) > self.attack_finished))
							{
								if ((self.impulse == 215))
								{
									ThrowNade();
									self.impulse = 0;
									return;
								}
								else
								{
									meleeaxe();
									self.impulse = 0;
								}
							}
						}
						else
						{
							if ((((self.weapon == IT_ROCKET_LAUNCHER) || (self.weapon == IT_GRENADE_LAUNCHER)) && ((time + 0.3) > self.attack_finished)))
							{
								if ((self.impulse == 215))
								{
									ThrowNade();
									self.impulse = 0;
									return;
								}
								else
								{
									meleeaxe();
									self.impulse = 0;
								}
							}
						}
					}
				}
			}
		}
	}
	if ((time < self.attack_finished))
	{
		return;
	}
	self.attack_timer = 0;
	ImpulseCommands();
	if (self.weapon == IT_AXE)
	{
		return;	// the Bonk Hammer charges and swings by itself (hammer.qc)
	}
	if (LtGun_Frame())
	{
		return;	// the sniper rifle charges while fire is held and shoots on release (sniper.qc)
	}
	if (self.button0)
	{
		SuperDamageSound();
		W_Attack();
	}
};

void() SuperDamageSound =
{
	if ((self.super_damage_finished > time))
	{
		if ((self.super_sound < time))
		{
			self.super_sound = (time + 1);
			sound7(self, CHAN_BODY, "items/damage3.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
	return;
};
