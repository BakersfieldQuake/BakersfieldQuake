// ---------------------------------------------------------------- ROB DOB DJI DRONE VIEWMODEL (FG_DOB, impulse 61 / 17)
//   Uses progs/v_robhead_drone.md3 and launches the steerable flying Rob Head drone via FD_Launch() (floathead.qc).

void() RobHead_Precache =
{
	precache_model ("progs/v_robhead_drone.md3");
	precache_sound ("robhead/launch.wav");
	precache_sound ("robhead/rd_grenade.wav");
	precache_sound ("funny/heh.wav");
	precache_sound ("weapons/pkup.wav");
};

void(entity p) RH_ResetPlayer =
{
	p.rh_charging = 0;
	p.rh_charge_gun = 0;
	p.rh_next_juggle = 0;
	p.rh_fire_t = 0;
	p.rh_throw_at = 0;
	p.rh_throw_gun = 0;
	p.rh_threw_t = 0;
	p.rh_reload_t = 0;
	p.rh_empty = FALSE;
};

void() RH_BeginDroneLaunch =
{
	local float a;

	if (self.health <= 0 || self.deadflag || intermission_running
		|| self.veh_ride != world || FD_Flying (self) || Veh_Driving (self)
		|| JohnBird_Flying (self) || RocketRider_Flying (self) || EricCannon_Active (self) || MMTank_Driving (self))
	{
		self.rh_charging = 0;
		self.rh_charge_gun = 0;
		return;
	}
	a = FunGun_Ammo (self, FG_DOB);
	if (a < 1)
	{
		self.rh_charging = 0;
		self.rh_charge_gun = 0;
		return;
	}
	self.rh_charging = 0;
	self.rh_charge_gun = 0;

	FunGun_SetAmmo (self, FG_DOB, a - 1);
	FunGun_Lock (FG_DOB);
	self.fg_fire_t = time;
	self.bm_lastshot = time + 0.9;
	self.rh_fire_t = time;
	self.rh_throw_gun = FG_DOB;
	self.rh_throw_at = time + RH_DRONE_DELAY;

	self.punchangle_x = -2.2;
	self.punchangle_z = 1.6;
	player_throw1 ();
	FG_Snd (self, CHAN_WEAPON, "weapons/pkup.wav", 0.85, 1.25);
	if (random () < 0.5)
		FG_Snd (self, CHAN_VOICE, "robhead/rd_grenade.wav", 0.90, 1.0);
	self.attack_finished = time + RH_DRONE_DELAY + (RH_FOLLOW_TIME + RH_RAISE_TIME) / RH_DRONE_ANIM_SPEED;
};

void() RH_DronePress =
{
	if (self.rh_charging > 0 || self.rh_throw_at > 0)
		return;
	if (FD_Flying (self) || Veh_Driving (self) || JohnBird_Flying (self) || RocketRider_Flying (self) || EricCannon_Active (self) || MMTank_Driving (self))
		return;
	if (self.veh_ride != world)
	{
		if (self.ishuman == 1)
			sprint (self, "Bail out of the vehicle (H) before launching Rob Dob!\n");
		self.attack_finished = time + 0.35;
		return;
	}
	self.rh_charging = time;
	self.rh_charge_gun = FG_DOB;
	self.rh_next_juggle = time + 0.32;
	FG_Snd (self, CHAN_VOICE, "funny/heh.wav", 0.85, 1.0);
	self.attack_finished = time + 0.08;
};

// Called every frame from FunGun_ViewFrame
void() RH_Frame =
{
	local float busy, ammo;

	busy = (self.health <= 0 || self.deadflag || intermission_running
		|| self.veh_ride != world || FD_Flying (self) || Veh_Driving (self)
		|| JohnBird_Flying (self) || RocketRider_Flying (self) || EricCannon_Active (self) || MMTank_Driving (self));
	if (busy)
	{
		if (self.rh_throw_at > 0 && self.health > 0 && !self.deadflag && !intermission_running)
		{
			ammo = FunGun_Ammo (self, FG_DOB);
			if (ammo < FunGun_Max (FG_DOB))
				FunGun_SetAmmo (self, FG_DOB, ammo + 1);
		}
		self.rh_charging = 0;
		self.rh_charge_gun = 0;
		self.rh_throw_at = 0;
		return;
	}

	// Launch steerable drone right at release frame 84
	if (self.rh_throw_at > 0 && time >= self.rh_throw_at)
	{
		self.rh_throw_at = 0;
		self.rh_threw_t = time;
		FD_Launch ();
	}

	if (self.weapon != IT_FUNGUN || self.fg_sel != FG_DOB)
	{
		self.rh_charging = 0;
		self.rh_charge_gun = 0;
		return;
	}

	if (self.rh_charging > 0)
	{
		if (self.rh_charge_gun != FG_DOB)
		{
			self.rh_charging = 0;
			self.rh_charge_gun = 0;
			return;
		}
		if (self.button0 && (time - self.rh_charging) < 0.55)
		{
			self.attack_finished = time + 0.08;
			if (time >= self.rh_next_juggle)
			{
				self.rh_next_juggle = time + 0.42;
				FG_Snd (self, CHAN_VOICE, "funny/heh.wav", 0.78, 1.0 + (time - self.rh_charging) * 0.14);
			}
			return;
		}
		if ((time - self.rh_charging) >= 0.06)
			RH_BeginDroneLaunch ();
		return;
	}
};

// ================================================================
// FIRST-PERSON VIEWMODEL ANIMATOR (progs/v_robhead_drone.md3)
// ================================================================

void(entity vm, float is_quad) RobHead_ViewFrame =
{
	local entity p;
	local float ammo, u, ease, idx, sw1, sw2, sw3, spd, follow_t, raise_t;
	local vector vxy;

	p = vm.owner;
	if (p.weapon != IT_FUNGUN || p.fg_sel != FG_DOB)
	{
		if (vm.rhvm_on)
		{
			if (is_quad)
				vm.skin = 1;
			else
				vm.skin = 0;
			vm.origin = '0 0 0';
			vm.angles = '0 0 0';
			vm.rhvm_on = 0;
		}
		return;
	}

	follow_t = RH_FOLLOW_TIME / RH_DRONE_ANIM_SPEED;
	raise_t = RH_RAISE_TIME / RH_DRONE_ANIM_SPEED;

	if (is_quad && vm.alpha < 0)
		vm.alpha = 0.5;

	vm.frame = 0;
	vm.origin = '0 0 0';
	vm.angles = '0 0 0';
	ammo = FunGun_Ammo (p, FG_DOB);

	if (vm.rhvm_on != FG_DOB)
	{
		vm.rhvm_on = FG_DOB;
		if (ammo >= 1 && p.rh_throw_at <= 0 && (!p.rh_threw_t || time >= p.rh_threw_t + follow_t))
		{
			if (!is_quad)
				p.rh_reload_t = time;
		}
		else if (ammo < 1)
			p.rh_empty = TRUE;
	}

	// 1. Target-Lock Loop (skins 60..75 @ 32 FPS * 1.45)
	if (p.rh_charging > 0 && p.rh_charge_gun == FG_DOB)
	{
		p.rh_empty = FALSE;
		idx = floor ((time - p.rh_charging) * 32 * RH_DRONE_ANIM_SPEED);
		idx = idx - RH_VM_WIND_COUNT * floor (idx / RH_VM_WIND_COUNT);
		vm.skin = RH_VM_WIND_SKIN + idx;
		sw1 = sin (time * 32.0);
		sw2 = sin (time * 26.0);
		vm.origin_z = sw1 * 0.25 * RH_DRONE_BOB_SCALE;
		vm.origin_y = sw2 * 0.20 * RH_DRONE_BOB_SCALE;
		return;
	}

	// 2. Thumb Press Launch (skins 76..83)
	if (p.rh_throw_at > 0 && p.rh_throw_gun == FG_DOB)
	{
		p.rh_empty = FALSE;
		u = (time - p.rh_fire_t) / RH_DRONE_DELAY;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * RH_VM_PRE_COUNT);
		vm.skin = RH_VM_PRE_SKIN + idx;
		return;
	}

	// 3. Remote Lower Follow-Through (skins 84..93)
	if (p.rh_threw_t > 0 && p.rh_throw_gun == FG_DOB && time < p.rh_threw_t + follow_t)
	{
		u = (time - p.rh_threw_t) / follow_t;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * RH_VM_POST_COUNT);
		vm.skin = RH_VM_POST_SKIN + idx;
		if (ammo < 1)
			p.rh_empty = TRUE;
		else if (!is_quad)
			p.rh_reload_t = p.rh_threw_t + follow_t;
		return;
	}

	// 4. Out of ammo: hide viewmodel until next charge finishes recharging
	if (ammo < 1)
	{
		p.rh_empty = TRUE;
		vm.alpha = -1;
		return;
	}
	if (p.rh_empty)
	{
		p.rh_empty = FALSE;
		p.rh_reload_t = time;
	}

	// 5. Raise / Reset Reload (skins 94..111)
	if (p.rh_reload_t > 0 && time >= p.rh_reload_t && time < p.rh_reload_t + raise_t)
	{
		u = (time - p.rh_reload_t) / raise_t;
		if (u < 0)
			u = 0;
		if (u > 0.999)
			u = 0.999;
		idx = floor (u * RH_VM_RELOAD_COUNT);
		vm.skin = RH_VM_RELOAD_SKIN + idx;
		ease = 1 - u;
		vm.origin_z = -1.8 * ease * ease * RH_DRONE_BOB_SCALE;
		return;
	}

	// 6. Idle Loop (skins 0..59 @ 24 FPS * 1.45)
	idx = floor (time * 24 * RH_DRONE_ANIM_SPEED);
	idx = idx - RH_VM_IDLE_COUNT * floor (idx / RH_VM_IDLE_COUNT);
	vm.skin = RH_VM_IDLE_SKIN + idx;

	vxy = p.velocity;
	vxy_z = 0;
	spd = vlen (vxy) / 320;
	if (spd > 1)
		spd = 1;
	sw1 = sin (time * 2.4);
	sw2 = sin (time * 4.8);
	sw3 = sin (time * 8.2);
	vm.origin_y = (0.20 * sw1 + 0.50 * spd * sw3) * RH_DRONE_BOB_SCALE;
	vm.origin_z = (0.16 * sw2 - 0.38 * spd * fabs (sw3)) * RH_DRONE_BOB_SCALE;
	vm.angles_z = (0.40 * sw1 + 0.95 * spd * sw3) * RH_DRONE_BOB_SCALE;
};
