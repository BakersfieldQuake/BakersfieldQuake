// TEST HARNESS ONLY (build_vmtest*.py). Not part of the mod.
// +set vm_test 1 : view model + throw at a dummy target (hop, leap, hit), screenshots, quit
// +set vm_test 2 : throw with nobody around and log the drive (cornering), quit
// +set vm_test 3 : third person: the little Mega Man in your hand, quit

.float	vt_t0;
.float	vt_step;
.float	vt_log;

void() W_SetCurrentAmmo;

void(entity p) VT_Give =
{
	local entity oself;

	MegaMan_Give (p);
	p.weapon = IT_MEGAMAN;
	oself = self;
	self = p;
	W_SetCurrentAmmo ();
	self = oself;
};

void(entity p, string name) VT_Shot =
{
	stuffcmd (p, strcat ("screenshot ", strcat (name, "\n")));
};

void() VT_DummyDie =
{
	dprint ("VT dummy killed\n");
	remove (self);
};

void() VT_DummyIdle =
{
	self.nextthink = time + 0.1;
};

void(entity p) VT_SpawnDummy =
{
	local entity d;
	local vector pos;

	makevectors ('0 1 0' * p.v_angle_y);
	traceline (p.origin, p.origin + v_forward * 420, TRUE, p);
	pos = trace_endpos - v_forward * 40;
	traceline (pos, pos + v_right * 110, TRUE, p);
	pos = trace_endpos - v_right * 20;
	d = spawn ();
	d.classname = "vt_dummy";
	d.netname = "dummy";
	d.flags = FL_MONSTER;
	d.health = 1000;
	d.takedamage = DAMAGE_AIM;
	d.solid = SOLID_SLIDEBOX;
	d.movetype = MOVETYPE_STEP;
	d.th_die = VT_DummyDie;
	d.th_run = d.th_stand = d.th_walk = VT_DummyIdle;
	setmodel (d, "progs/player.mdl");
	setsize (d, VEC_HULL_MIN, VEC_HULL_MAX);
	setorigin (d, pos);
	dprint ("VT dummy at ", vtos (pos), " player at ", vtos (p.origin), "\n");
};

void() VMTest_Think =
{
	local entity p, m;
	local float t, d, mode;

	self.nextthink = time + 0.01;
	p = find (world, classname, "player");
	if (!p)
		return;
	if (!self.vt_t0)
	{
		self.vt_t0 = time;
		return;
	}
	t = time - self.vt_t0;
	mode = cvar ("vm_test");

	if (t > 1.0 && self.vt_step == 0) { VT_Give (p); self.vt_step = 1; }

	if (mode == 3)
	{
		if (t > 1.2 && self.vt_step == 1) { stuffcmd (p, "chase_active 1; chase_back 90; chase_up 16\n"); self.vt_step = 2; }
		if (t > 2.0 && self.vt_step == 2) { VT_Shot (p, "vm_3rd0.png"); self.vt_step = 3; }
		if (t > 2.5 && self.vt_step == 3) { stuffcmd (p, "chase_back 50; cl_yawspeed 140; +right\n"); self.vt_step = 4; }
		if (t > 3.3 && self.vt_step == 4) { stuffcmd (p, "-right\n"); VT_Shot (p, "vm_3rd1.png"); self.vt_step = 5; }
		if (t > 3.8 && self.vt_step == 5) { stuffcmd (p, "condump vm_log.txt\nquit\n"); self.vt_step = 6; }
		return;
	}

	if (t > 2.0 && self.vt_step == 1) { VT_Shot (p, "vm_idle0.png"); self.vt_step = 2; }
	if (t > 2.35 && self.vt_step == 2) { VT_Shot (p, "vm_idle1.png"); self.vt_step = 3; }
	if (t > 2.6 && self.vt_step == 3) { if (mode == 1) VT_SpawnDummy (p); self.vt_step = 4; }
	if (t > 3.0 && self.vt_step == 4) { stuffcmd (p, "+attack\n"); self.vt_step = 5; }
	if (t > 3.03 && self.vt_step == 5) { stuffcmd (p, "-attack\n"); self.vt_step = 6; }

	if (p.mm_fire_t && self.vt_step >= 6)
	{
		d = time - p.mm_fire_t;
		if (mode == 1)
		{
			if (d > 0.05 && self.vt_step == 6) { VT_Shot (p, "vm_t1.png"); self.vt_step = 7; }
			if (d > 0.12 && self.vt_step == 7) { VT_Shot (p, "vm_t2.png"); self.vt_step = 8; }
			if (d > 0.17 && self.vt_step == 8) { VT_Shot (p, "vm_t3.png"); self.vt_step = 9; }
			if (d > 0.23 && self.vt_step == 9) { VT_Shot (p, "vm_t4.png"); self.vt_step = 10; }
			if (d > 0.32 && self.vt_step == 10) { VT_Shot (p, "vm_t5.png"); self.vt_step = 11; }
			if (d > 0.45 && self.vt_step == 11) { VT_Shot (p, "vm_t6.png"); self.vt_step = 12; }
			if (d > 0.65 && self.vt_step == 12) { VT_Shot (p, "vm_t7.png"); self.vt_step = 13; }
			if (d > 0.9 && self.vt_step == 13) { VT_Shot (p, "vm_t8.png"); self.vt_step = 14; }
			if (d > 1.3 && self.vt_step == 14) { VT_Shot (p, "vm_t9.png"); self.vt_step = 15; }
			if (d > 1.7 && self.vt_step == 15) { VT_Shot (p, "vm_t10.png"); self.vt_step = 16; }
			if (d > 2.1 && self.vt_step == 16) { VT_Shot (p, "vm_t11.png"); self.vt_step = 17; }
			if (d > 2.6 && self.vt_step == 17) { VT_Shot (p, "vm_t12.png"); self.vt_step = 18; }
			if (d > 6.0 && self.vt_step == 18) { stuffcmd (p, "condump vm_log.txt\n"); self.vt_step = 19; }
			if (d > 6.5 && self.vt_step == 19) { stuffcmd (p, "quit\n"); self.vt_step = 20; }
		}
		else
		{
			if (d > 12.0 && self.vt_step == 6) { stuffcmd (p, "condump vm_log.txt\n"); self.vt_step = 7; }
			if (d > 12.5 && self.vt_step == 7) { stuffcmd (p, "quit\n"); self.vt_step = 8; }
		}
	}

	if (time >= self.vt_log)
	{
		self.vt_log = time + 0.1;
		m = find (world, classname, "megaman");
		if (m)
			dprint (strcat ("MM ", ftos (time - p.mm_fire_t)), " org=", vtos (m.origin), " yaw=", ftos (floor (m.angles_y)), strcat (" st=", ftos (m.mm_state)), "\n");
	}
};

void() VMTest_Start =
{
	local entity e;

	if (!cvar ("vm_test"))
		return;
	precache_model ("progs/player.mdl");
	e = spawn ();
	e.classname = "vmtest";
	e.think = VMTest_Think;
	e.nextthink = time + 0.1;
};
