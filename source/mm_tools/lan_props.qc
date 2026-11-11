/*
================
EXPLODABLE 3D LAN PARTY PROPS - implementation (Combat+)
================
*/

void() Lan_RespawnThink;
void() Lan_ExplodeNow;

void() LanProps_Precache =
{
	if (lan_precached)
		return;
	lan_precached = TRUE;

	precache_model ("progs/bklan/lan_mon1.md3");
	precache_model ("progs/bklan/lan_mon2.md3");
	precache_model ("progs/bklan/lan_mon3.md3");
	precache_model ("progs/bklan/lan_mon4.md3");

	precache_model ("progs/bklan/lan_pc1.md3");
	precache_model ("progs/bklan/lan_pc2.md3");
	precache_model ("progs/bklan/lan_pc3.md3");
	precache_model ("progs/bklan/lan_pc4.md3");

	precache_model ("progs/bklan/lan_chair1.md3");
	precache_model ("progs/bklan/lan_chair2.md3");
	precache_model ("progs/bklan/lan_chair3.md3");
	precache_model ("progs/bklan/lan_chair4.md3");

	precache_model ("progs/bklan/lan_table1.md3");
	precache_model ("progs/bklan/lan_table2.md3");
	precache_model ("progs/bklan/lan_table3.md3");
	precache_model ("progs/bklan/lan_table4.md3");
	precache_model ("progs/bklan/lan_table4s.md3");

	precache_model ("progs/bklan/lan_deb_glass.md3");
	precache_model ("progs/bklan/lan_deb_yoke.md3");
	precache_model ("progs/bklan/lan_deb_panel.md3");
	precache_model ("progs/bklan/lan_deb_fan.md3");
	precache_model ("progs/bklan/lan_deb_wheel.md3");
	precache_model ("progs/bklan/lan_deb_plank.md3");

	precache_model ("progs/hd_kbd.md3");
	precache_model ("progs/hd_mouse.md3");
	precache_model ("progs/hd_cd.md3");
	precache_model ("progs/hd_floppy.md3");
	precache_model ("progs/hd_board.md3");

	precache_sound ("lan/crt_implode.wav");
	precache_sound ("lan/pc_boom.wav");
	precache_sound ("lan/chair_break.wav");
	precache_sound ("lan/table_smash.wav");
	precache_sound ("lan/glass_tink.wav");
	precache_sound ("hackmon/hm_zap.wav");
	precache_sound ("vehicles/hit_metal1.wav");
	precache_sound ("larry/it_wont_boot.wav");
};

string(float kind, float var_id) Lan_ModelFor =
{
	if (kind == LAN_KIND_MONITOR)
	{
		if (var_id == 2) return "progs/bklan/lan_mon2.md3";
		if (var_id == 3) return "progs/bklan/lan_mon3.md3";
		if (var_id == 4) return "progs/bklan/lan_mon4.md3";
		return "progs/bklan/lan_mon1.md3";
	}
	if (kind == LAN_KIND_PC)
	{
		if (var_id == 2) return "progs/bklan/lan_pc2.md3";
		if (var_id == 3) return "progs/bklan/lan_pc3.md3";
		if (var_id == 4) return "progs/bklan/lan_pc4.md3";
		return "progs/bklan/lan_pc1.md3";
	}
	if (kind == LAN_KIND_CHAIR)
	{
		if (var_id == 2) return "progs/bklan/lan_chair2.md3";
		if (var_id == 3) return "progs/bklan/lan_chair3.md3";
		if (var_id == 4) return "progs/bklan/lan_chair4.md3";
		return "progs/bklan/lan_chair1.md3";
	}
	if (var_id == 2) return "progs/bklan/lan_table2.md3";
	if (var_id == 3) return "progs/bklan/lan_table3.md3";
	if (var_id == 4) return "progs/bklan/lan_table4.md3";
	if (var_id == 5) return "progs/bklan/lan_table4s.md3";
	return "progs/bklan/lan_table1.md3";
};

float(float kind) Lan_MaxHP =
{
	if (kind == LAN_KIND_MONITOR)
		return 35;
	if (kind == LAN_KIND_PC)
		return 55;
	if (kind == LAN_KIND_CHAIR)
		return 40;
	return 95;
};

void(entity e) Lan_SetRotatedBounds =
{
	local float hl, hw, ht, rad, sn, cs, acs, asn, hx, hy;
	local vector bmin, bmax;

	if (e.lan_kind == LAN_KIND_MONITOR)
	{
		hl = 8.5;
		hw = 8.5;
		ht = 17.5;
	}
	else if (e.lan_kind == LAN_KIND_PC)
	{
		hl = 8.8;
		hw = 4.6;
		ht = 19.5;
		if (e.lan_variant == 2 || e.lan_variant == 4)
			ht = 21.5;
	}
	else if (e.lan_kind == LAN_KIND_CHAIR)
	{
		hl = 9.0;
		hw = 9.0;
		ht = 34.0;
	}
	else
	{
		hl = 48.0;
		if (e.lan_variant == 5)
			hl = 35.0;
		hw = 15.0;
		ht = 30.0;
	}

	rad = e.angles_y * 0.0174533;
	sn = sin (rad);
	cs = cos (rad);
	acs = fabs (cs);
	asn = fabs (sn);
	hx = acs * hl + asn * hw;
	hy = asn * hl + acs * hw;

	bmin_x = 0 - hx;
	bmin_y = 0 - hy;
	bmin_z = 0;
	bmax_x = hx;
	bmax_y = hy;
	bmax_z = ht;
	setsize (e, bmin, bmax);
};

// ---------------------------------------------------------------- Debris Pool (capped at 28 active chunks)

void() Lan_DebrisRemove =
{
	if (lan_debris_count > 0)
		lan_debris_count = lan_debris_count - 1;
	remove (self);
};

void() Lan_DebrisTouch =
{
	local float spd;

	if (other.takedamage)
		return;
	spd = vlen (self.velocity);
	if (spd < 55 || time < self.pain_finished)
		return;
	self.pain_finished = time + 0.14;
	if (self.cnt == 1)
		sound7 (self, CHAN_AUTO, "lan/glass_tink.wav", 0.45, ATTN_NORM, 92 + random () * 24);
	else
		sound7 (self, CHAN_AUTO, "vehicles/hit_metal1.wav", 0.32, ATTN_NORM, 110 + random () * 25);
};

void(string mdl, vector org, vector vel, float is_glass, float life) Lan_ThrowDebris =
{
	local entity d, e, oldest;

	if (lan_debris_count >= 28)
	{
		oldest = world;
		e = find (world, classname, "lan_debris");
		while (e != world)
		{
			if (oldest == world || e.nextthink < oldest.nextthink)
				oldest = e;
			e = find (e, classname, "lan_debris");
		}
		if (oldest != world)
		{
			remove (oldest);
			lan_debris_count = lan_debris_count - 1;
		}
	}

	d = spawn ();
	d.classname = "lan_debris";
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_NOT;
	d.cnt = is_glass;
	d.velocity = vel;
	d.avelocity_x = crandom () * 460;
	d.avelocity_y = crandom () * 460;
	d.avelocity_z = crandom () * 460;
	d.angles_y = random () * 360;
	d.touch = Lan_DebrisTouch;
	d.think = Lan_DebrisRemove;
	d.nextthink = time + life + random () * 1.8;
	setmodel (d, mdl);
	setsize (d, VEC_ORIGIN, VEC_ORIGIN);
	setorigin (d, org);
	lan_debris_count = lan_debris_count + 1;
};

// ---------------------------------------------------------------- Damage, Domino Collapse & Explosions

void(entity attacker, float take) Lan_Pain =
{
	local vector sp_org;

	if (self.lan_dead)
		return;

	sp_org = self.origin + '0 0 10';
	if (self.lan_kind == LAN_KIND_MONITOR)
	{
		// Crack the CRT glass & zap when below 55% HP!
		if (self.health < 20)
			self.skin = 6;
		particle (sp_org, '0 0 35', 244, 16);
		if (time > self.pain_finished)
		{
			self.pain_finished = time + 0.18;
			sound7 (self, CHAN_AUTO, "hackmon/hm_zap.wav", 0.55, ATTN_NORM, 95 + random () * 20);
		}
	}
	else if (self.lan_kind == LAN_KIND_PC)
	{
		particle (sp_org, '0 0 28', 104, 14);
		if (time > self.pain_finished)
		{
			self.pain_finished = time + 0.16;
			sound7 (self, CHAN_AUTO, "vehicles/hit_metal1.wav", 0.55, ATTN_NORM, 98 + random () * 18);
		}
	}
	else
	{
		particle (sp_org, '0 0 18', 12, 10);
	}
};

// When a LAN table blows up, any intact monitors/PCs sitting on top of it either chain-explode or tumble to the floor!
void(entity tbl, entity atk) Lan_DropTabletopProps =
{
	local entity e;
	local float minx, maxx, miny, maxy, topz;

	minx = tbl.origin_x + tbl.mins_x - 5;
	maxx = tbl.origin_x + tbl.maxs_x + 5;
	miny = tbl.origin_y + tbl.mins_y - 5;
	maxy = tbl.origin_y + tbl.maxs_y + 5;
	topz = tbl.origin_z + 30.0;

	e = nextent (world);
	while (e != world)
	{
		if (!e.lan_dead && (e.lan_kind == LAN_KIND_MONITOR || e.lan_kind == LAN_KIND_PC))
		{
			if (e.origin_x >= minx && e.origin_x <= maxx && e.origin_y >= miny && e.origin_y <= maxy)
			{
				if (fabs (e.origin_z - topz) < 8.0)
				{
					if (random () < 0.45)
					{
						e.lan_attacker = atk;
						e.takedamage = DAMAGE_NO;
						e.think = Lan_ExplodeNow;
						e.nextthink = time + 0.06 + random () * 0.14;
					}
					else
					{
						// Tumble off the smashed table onto the concrete floor, still shootable!
						e.movetype = MOVETYPE_TOSS;
						e.flags = e.flags - (e.flags & FL_ONGROUND);
						e.velocity_x = crandom () * 65;
						e.velocity_y = crandom () * 65;
						e.velocity_z = 75 + random () * 55;
					}
				}
			}
		}
		else if (!e.lan_kind && e.classname == "misc_model")
		{
			// Drop any soda cans, cups, bottles, or extinguishers resting on the smashed table!
			if (e.origin_x >= minx && e.origin_x <= maxx && e.origin_y >= miny && e.origin_y <= maxy)
			{
				if (fabs (e.origin_z - topz) < 8.0)
				{
					e.movetype = MOVETYPE_TOSS;
					e.flags = e.flags - (e.flags & FL_ONGROUND);
					e.velocity_x = crandom () * 80;
					e.velocity_y = crandom () * 80;
					e.velocity_z = 90 + random () * 60;
				}
			}
		}
		e = nextent (e);
	}
};

void() Lan_ExplodeNow =
{
	local vector blast_org, v;
	local entity inf, atk;
	local float rad_dmg, i;

	if (self.lan_dead)
		return;
	self.lan_dead = TRUE;
	self.takedamage = DAMAGE_NO;

	atk = self.lan_attacker;
	if (atk == world)
		atk = self;

	if (self.lan_kind == LAN_KIND_MONITOR)
	{
		blast_org = self.origin + '0 0 10';
		rad_dmg = 44;

		WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte (MSG_BROADCAST, TE_EXPLOSION);
		WriteCoord (MSG_BROADCAST, blast_org_x);
		WriteCoord (MSG_BROADCAST, blast_org_y);
		WriteCoord (MSG_BROADCAST, blast_org_z);

		// Electric blue/white phosphor implosion burst!
		particle (blast_org, '0 0 55', 244, 48);
		particle (blast_org, '0 0 25', 108, 32);
		sound7 (self, CHAN_VOICE, "lan/crt_implode.wav", 1.0, ATTN_NORM, 92 + random () * 16);

		Lan_ThrowDebris ("progs/bklan/lan_deb_yoke.md3", blast_org,
			'1 0 0' * (crandom () * 210) + '0 1 0' * (crandom () * 210) + '0 0 1' * (220 + random () * 140), FALSE, 6.5);
		i = 0;
		while (i < 3)
		{
			v = '1 0 0' * (crandom () * 290) + '0 1 0' * (crandom () * 290) + '0 0 1' * (180 + random () * 180);
			Lan_ThrowDebris ("progs/bklan/lan_deb_glass.md3", blast_org, v, TRUE, 5.5);
			i = i + 1;
		}
		if (random () < 0.65)
			Lan_ThrowDebris ("progs/hd_kbd.md3", blast_org + '0 0 -4',
				'1 0 0' * (crandom () * 180) + '0 1 0' * (crandom () * 180) + '0 0 1' * (190 + random () * 110), FALSE, 6.5);
		if (random () < 0.65)
			Lan_ThrowDebris ("progs/hd_mouse.md3", blast_org + '0 0 -4',
				'1 0 0' * (crandom () * 240) + '0 1 0' * (crandom () * 240) + '0 0 1' * (210 + random () * 120), FALSE, 6.0);
	}
	else if (self.lan_kind == LAN_KIND_PC)
	{
		blast_org = self.origin + '0 0 11';
		rad_dmg = 54;

		WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte (MSG_BROADCAST, TE_EXPLOSION);
		WriteCoord (MSG_BROADCAST, blast_org_x);
		WriteCoord (MSG_BROADCAST, blast_org_y);
		WriteCoord (MSG_BROADCAST, blast_org_z);

		particle (blast_org, '0 0 45', 104, 45);
		sound7 (self, CHAN_VOICE, "lan/pc_boom.wav", 1.0, ATTN_NORM, 92 + random () * 16);
		if (random () < 0.12)
			sound7 (self, CHAN_ITEM, "larry/it_wont_boot.wav", 0.85, ATTN_NORM, 100);

		Lan_ThrowDebris ("progs/bklan/lan_deb_panel.md3", blast_org,
			'1 0 0' * (crandom () * 240) + '0 1 0' * (crandom () * 240) + '0 0 1' * (220 + random () * 140), FALSE, 7.0);
		Lan_ThrowDebris ("progs/bklan/lan_deb_fan.md3", blast_org,
			'1 0 0' * (crandom () * 280) + '0 1 0' * (crandom () * 280) + '0 0 1' * (250 + random () * 140), FALSE, 6.5);
		Lan_ThrowDebris ("progs/hd_board.md3", blast_org,
			'1 0 0' * (crandom () * 220) + '0 1 0' * (crandom () * 220) + '0 0 1' * (230 + random () * 130), FALSE, 7.0);
		Lan_ThrowDebris ("progs/hd_cd.md3", blast_org + '0 0 4',
			'1 0 0' * (crandom () * 340) + '0 1 0' * (crandom () * 340) + '0 0 1' * (240 + random () * 160), TRUE, 6.0);
		Lan_ThrowDebris ("progs/hd_floppy.md3", blast_org + '0 0 2',
			'1 0 0' * (crandom () * 290) + '0 1 0' * (crandom () * 290) + '0 0 1' * (220 + random () * 150), FALSE, 6.0);
	}
	else if (self.lan_kind == LAN_KIND_CHAIR)
	{
		blast_org = self.origin + '0 0 16';
		rad_dmg = 30;

		WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte (MSG_BROADCAST, TE_EXPLOSION);
		WriteCoord (MSG_BROADCAST, blast_org_x);
		WriteCoord (MSG_BROADCAST, blast_org_y);
		WriteCoord (MSG_BROADCAST, blast_org_z);

		sound7 (self, CHAN_VOICE, "lan/chair_break.wav", 0.95, ATTN_NORM, 92 + random () * 18);
		i = 0;
		while (i < 3)
		{
			v = '1 0 0' * (crandom () * 260) + '0 1 0' * (crandom () * 260) + '0 0 1' * (190 + random () * 150);
			Lan_ThrowDebris ("progs/bklan/lan_deb_wheel.md3", blast_org, v, FALSE, 6.0);
			i = i + 1;
		}
		Lan_ThrowDebris ("progs/bklan/lan_deb_panel.md3", blast_org + '0 0 6',
			'1 0 0' * (crandom () * 200) + '0 1 0' * (crandom () * 200) + '0 0 1' * (220 + random () * 120), FALSE, 6.0);
	}
	else
	{
		// LAN_KIND_TABLE: collapse table, drop/detonate tabletop PCs & monitors, fling planks & legs!
		blast_org = self.origin + '0 0 24';
		rad_dmg = 48;
		Lan_DropTabletopProps (self, atk);

		WriteByte (MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte (MSG_BROADCAST, TE_EXPLOSION);
		WriteCoord (MSG_BROADCAST, blast_org_x);
		WriteCoord (MSG_BROADCAST, blast_org_y);
		WriteCoord (MSG_BROADCAST, blast_org_z);

		sound7 (self, CHAN_VOICE, "lan/table_smash.wav", 1.0, ATTN_NORM, 92 + random () * 16);
		i = 0;
		while (i < 4)
		{
			v = '1 0 0' * (crandom () * 250) + '0 1 0' * (crandom () * 250) + '0 0 1' * (180 + random () * 160);
			Lan_ThrowDebris ("progs/bklan/lan_deb_plank.md3", blast_org + '1 0 0' * (crandom () * 22), v, FALSE, 7.0);
			i = i + 1;
		}
		Lan_ThrowDebris ("progs/bklan/lan_deb_wheel.md3", blast_org - '0 0 8',
			'1 0 0' * (crandom () * 220) + '0 1 0' * (crandom () * 220) + '0 0 1' * (200 + random () * 120), FALSE, 6.0);
	}

	// Hide destroyed prop before dealing radius splash so it doesn't block its own blast!
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	setmodel (self, "");

	// Deal splash damage from center of prop (staggering chain reactions cleanly!)
	inf = spawn ();
	inf.classname = "lan_blast_inflictor";
	setorigin (inf, blast_org);
	lan_inflicting = lan_inflicting + 1;
	// Dampen secondary chain radius slightly so 1 rocket wrecks a cluster of 2-4 rigs without wiping the whole hall!
	if (lan_inflicting > 1)
		rad_dmg = rad_dmg * 0.68;
	T_RadiusDamage (inf, atk, rad_dmg, self);
	lan_inflicting = lan_inflicting - 1;
	remove (inf);

	if (self.lan_temp)
	{
		remove (self);
		return;
	}

	if (autocvar_lan_prop_respawn > 0)
	{
		self.think = Lan_RespawnThink;
		self.nextthink = time + autocvar_lan_prop_respawn + random () * 4.0;
	}
	else
	{
		self.nextthink = 0;
	}
};

void() Lan_Die =
{
	if (self.lan_dead)
		return;
	if (damage_attacker != world && damage_attacker != self && !damage_attacker.lan_kind)
		self.lan_attacker = damage_attacker;
	else if (damage_attacker.lan_kind && damage_attacker.lan_attacker != world)
		self.lan_attacker = damage_attacker.lan_attacker;
	else
		self.lan_attacker = self;

	// Stagger domino chain explosions by 70..200 ms so adjacent monitors & towers pop in a cinematic cascade!
	// always on a think of its own: blowing up inside the T_RadiusDamage that killed it would rewrite the .chain list
	// that loop is walking
	self.takedamage = DAMAGE_NO;
	self.think = Lan_ExplodeNow;
	if (lan_inflicting > 0)
		self.nextthink = time + 0.07 + random () * 0.13;
	else
		self.nextthink = time;
};

// ---------------------------------------------------------------- Initialization & Deathmatch Respawn

void(entity e) Lan_RestoreProp =
{
	e.lan_dead = FALSE;
	e.lan_attacker = world;
	e.angles = e.lan_spawn_ang;
	e.velocity = '0 0 0';
	e.movetype = MOVETYPE_NONE;
	e.solid = SOLID_BBOX;
	e.takedamage = DAMAGE_AIM;
	e.max_health = Lan_MaxHP (e.lan_kind);
	e.health = e.max_health;
	e.skin = e.lan_init_skin;
	e.th_pain = Lan_Pain;
	e.th_die = Lan_Die;
	e.nextthink = 0;

	setmodel (e, Lan_ModelFor (e.lan_kind, e.lan_variant));
	Lan_SetRotatedBounds (e);
	setorigin (e, e.lan_spawn_org);
};

void() Lan_RespawnThink =
{
	local entity p;
	local vector wmin, wmax;

	// Temporarily compute bounds at spawn origin to verify no live player is standing inside
	self.angles = self.lan_spawn_ang;
	Lan_SetRotatedBounds (self);
	wmin = self.lan_spawn_org + self.mins - '4 4 4';
	wmax = self.lan_spawn_org + self.maxs + '4 4 4';

	p = find (world, classname, "player");
	while (p != world)
	{
		if (p.health > 0)
		{
			if (p.absmax_x > wmin_x && p.absmin_x < wmax_x &&
				p.absmax_y > wmin_y && p.absmin_y < wmax_y &&
				p.absmax_z > wmin_z && p.absmin_z < wmax_z)
			{
				setsize (self, VEC_ORIGIN, VEC_ORIGIN);
				self.nextthink = time + 5.0;
				return;
			}
		}
		p = find (p, classname, "player");
	}

	// If this is a monitor or PC that originally sat on a table, wait if its table is still blown up!
	if ((self.lan_kind == LAN_KIND_MONITOR || self.lan_kind == LAN_KIND_PC) && self.lan_spawn_org_z > 20)
	{
		p = nextent (world);
		while (p != world)
		{
			if (p.lan_kind == LAN_KIND_TABLE && p.lan_dead)
			{
				if (fabs (self.lan_spawn_org_x - p.lan_spawn_org_x) < 50 &&
					fabs (self.lan_spawn_org_y - p.lan_spawn_org_y) < 50 &&
					fabs (self.lan_spawn_org_z - (p.lan_spawn_org_z + 30)) < 8)
				{
					setsize (self, VEC_ORIGIN, VEC_ORIGIN);
					self.nextthink = time + 3.0;
					return;
				}
			}
			p = nextent (p);
		}
	}

	Lan_RestoreProp (self);
};

void(entity e, float kind) Lan_InitProp =
{
	local float v, h;

	LanProps_Precache ();
	e.lan_kind = kind;

	v = floor (e.cnt);
	h = floor (fabs (e.origin_x * 0.037 + e.origin_y * 0.053));
	if (kind == LAN_KIND_TABLE)
	{
		if (v < 1 || v > 5)
			v = (h - 4 * floor (h / 4)) + 1;
	}
	else
	{
		if (v < 1 || v > 4)
			v = (h - 4 * floor (h / 4)) + 1;
	}
	e.lan_variant = v;

	if (kind == LAN_KIND_MONITOR)
	{
		// Preserve explicit map "skin" (0..5), or auto-vary across Q3A, CS 1.5, and Win98 if cnt was omitted!
		if (e.cnt == 0 && e.skin == 0)
			e.lan_init_skin = h - 6 * floor (h / 6);
		else
			e.lan_init_skin = floor (e.skin);
	}
	else
	{
		e.lan_init_skin = 0;
	}

	// Keep map LAN props tagged as "misc_model" after spawn so intro_director stage sweeps keep LAN halls populated
	if (e.lan_temp)
		e.classname = "lan_showcase";
	else
		e.classname = "misc_model";

	// Nudge floor-level props +0.2u so DarkPlaces lightpoint always samples above the BSP floor plane
	e.lan_spawn_org = e.origin + '0 0 0.2';
	e.lan_spawn_ang = e.angles;
	Lan_RestoreProp (e);
};

// ---------------------------------------------------------------- Map Entity Entrypoints

void() misc_lan_monitor =
{
	self.classname = "misc_lan_monitor";
	Lan_InitProp (self, LAN_KIND_MONITOR);
};

void() misc_lan_pc =
{
	self.classname = "misc_lan_pc";
	Lan_InitProp (self, LAN_KIND_PC);
};

void() misc_lan_chair =
{
	self.classname = "misc_lan_chair";
	Lan_InitProp (self, LAN_KIND_CHAIR);
};

void() misc_lan_table =
{
	self.classname = "misc_lan_table";
	Lan_InitProp (self, LAN_KIND_TABLE);
};

// ---------------------------------------------------------------- Cheat Showcase & Detonate Impulses (95, 96)

entity(float kind, float var_id, float sk, vector org, float yaw_deg) Lan_SpawnTemp =
{
	local entity e;

	e = spawn ();
	if (kind == LAN_KIND_MONITOR) e.classname = "misc_lan_monitor";
	else if (kind == LAN_KIND_PC) e.classname = "misc_lan_pc";
	else if (kind == LAN_KIND_CHAIR) e.classname = "misc_lan_chair";
	else e.classname = "misc_lan_table";

	e.lan_temp = TRUE;
	e.cnt = var_id;
	e.skin = sk;
	e.angles = '0 0 0';
	e.angles_y = yaw_deg;
	setorigin (e, org);
	Lan_InitProp (e, kind);
	return e;
};

void() LanProps_Impulse =
{
	local vector fwd, rgt, base, st_org;
	local float face_yaw, tbl_yaw, flr_z, i;
	local entity e, best;
	local float d, best_d;

	if (self.impulse != 95 && self.impulse != 96)
		return;
	if (!cvar ("sv_cheats"))
		return;

	if (self.impulse == 96)
	{
		self.impulse = 0;
		best = world;
		best_d = 450;
		e = nextent (world);
		while (e != world)
		{
			if (e.lan_kind > 0 && !e.lan_dead)
			{
				d = vlen ((e.origin + '0 0 16') - self.origin);
				if (d < best_d)
				{
					best_d = d;
					best = e;
				}
			}
			e = nextent (e);
		}
		if (best != world)
		{
			best.lan_attacker = self;
			e = self;
			self = best;
			Lan_ExplodeNow ();
			self = e;
		}
		return;
	}

	// impulse 95: Clear prior temp LAN showcase props & spawn 4 stations ahead of player!
	self.impulse = 0;
	e = nextent (world);
	while (e != world)
	{
		best = nextent (e);
		if (e.lan_temp)
			remove (e);
		e = best;
	}

	makevectors ('0 1 0' * self.v_angle_y);
	fwd = v_forward;
	rgt = v_right;
	face_yaw = self.v_angle_y + 180;
	tbl_yaw = self.v_angle_y + 90;

	// Snap showcase floor height under point ahead of player
	base = self.origin + fwd * 145;
	traceline (base + '0 0 32', base - '0 0 128', TRUE, self);
	if (trace_fraction < 1)
		flr_z = trace_endpos_z;
	else
		flr_z = self.origin_z - 24;

	base_z = flr_z;
	// Spawn 4 unique 8-ft tables + 4 monitors, 4 PCs, 4 chairs, and Q3A/CS/Win98 screens!
	Lan_SpawnTemp (LAN_KIND_TABLE, 1, 0, base - rgt * 52, tbl_yaw);
	Lan_SpawnTemp (LAN_KIND_TABLE, 2, 0, base + rgt * 52, tbl_yaw);
	Lan_SpawnTemp (LAN_KIND_TABLE, 3, 0, base + fwd * 64 - rgt * 52, tbl_yaw);
	Lan_SpawnTemp (LAN_KIND_TABLE, 4, 0, base + fwd * 64 + rgt * 52, tbl_yaw);

	i = 0;
	while (i < 4)
	{
		st_org = base + '0 0 30' + rgt * ((i - 1.5) * 52);
		// Skins 0=Q3A, 1=Counter-Strike, 2=Win98 Desktop+Winamp, 5=Win98 GameSpy+BSOD
		if (i == 3)
			Lan_SpawnTemp (LAN_KIND_MONITOR, i + 1, 5, st_org - rgt * 6, face_yaw);
		else
			Lan_SpawnTemp (LAN_KIND_MONITOR, i + 1, i, st_org - rgt * 6, face_yaw);
		Lan_SpawnTemp (LAN_KIND_PC, i + 1, 0, st_org + rgt * 11, face_yaw);
		Lan_SpawnTemp (LAN_KIND_CHAIR, i + 1, 0, st_org - '0 0 30' - fwd * 28, self.v_angle_y);
		i = i + 1;
	}
	// Extra row on back tables showing Q3A q3dm6 (skin 3) & CS AWP scope (skin 4)!
	Lan_SpawnTemp (LAN_KIND_MONITOR, 2, 3, base + '0 0 30' + fwd * 64 - rgt * 52, face_yaw);
	Lan_SpawnTemp (LAN_KIND_MONITOR, 1, 4, base + '0 0 30' + fwd * 64 + rgt * 52, face_yaw);
	sprint (self, "Spawned 4x4 Explodable LAN Party Showcase (Q3A, CS, Win98)!\n");
};
