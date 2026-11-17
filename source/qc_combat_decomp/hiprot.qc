//Decompiled code. Please respect the original copyright.

vector(vector ang) SUB_NormalizeAngles =
{
	while ((ang_x > 360))
	{
		ang_x = ang_x - 360;
	}
	while ((ang_x < 0))
	{
		ang_x = ang_x + 360;
	}
	while ((ang_y > 360))
	{
		ang_y = ang_y - 360;
	}
	while ((ang_y < 0))
	{
		ang_y = ang_y + 360;
	}
	while ((ang_z > 360))
	{
		ang_z = ang_z - 360;
	}
	while ((ang_z < 0))
	{
		ang_z = ang_z + 360;
	}
	return (ang);
};

void(entity ent, float amount) hurt_setdamage =
{
	ent.dmg = amount;
	if (!amount)
	{
		ent.solid = 0;
	}
	else
	{
		ent.solid = SOLID_TRIGGER;
	}
	ent.nextthink = -1;
};

void() info_rotate =
{
	self.nextthink = (time + 5);
	self.think = SUB_Remove;
};

void() RotateTargets =
{
	local entity ent;
	local vector vx;
	local vector vy;
	local vector vz;
	local vector org;

	makevectors(self.angles);
	ent = find(world, targetname, self.target);
	while (ent)
	{
		if ((ent.rotate_type == OBJECT_SETORIGIN))
		{
			org = ent.oldorigin;
			vx = v_forward * org_x;
			vy = v_right * 0;
			vy = vy * -1;
			vz = v_up * 0;
			ent.neworigin = ((vx + vy) + vz);
			setorigin(ent, (ent.neworigin + self.origin));
		}
		else
		{
			if ((ent.rotate_type == OBJECT_ROTATE))
			{
				ent.angles = self.angles;
				org = ent.oldorigin;
				vx = v_forward * org_x;
				vy = v_right * 0;
				vy = vy * -1;
				vz = v_up * 0;
				ent.neworigin = ((vx + vy) + vz);
				setorigin(ent, (ent.neworigin + self.origin));
			}
			else
			{
				org = ent.oldorigin;
				vx = v_forward * org_x;
				vy = v_right * 0;
				vy = vy * -1;
				vz = v_up * 0;
				ent.neworigin = ((vx + vy) + vz);
				ent.neworigin = ((self.origin - self.oldorigin) + (ent.neworigin - ent.oldorigin));
				ent.velocity = ((ent.neworigin - ent.origin) * 25);
			}
		}
		ent = find(ent, targetname, self.target);
	}
};

void() RotateTargetsFinal =
{
	local entity ent;

	ent = find(world, targetname, self.target);
	while (ent)
	{
		ent.velocity = VEC_ORIGIN;
		if ((ent.rotate_type == OBJECT_ROTATE))
		{
			ent.angles = self.angles;
		}
		ent = find(ent, targetname, self.target);
	}
};

void() SetTargetOrigin =
{
	local entity ent;

	ent = find(world, targetname, self.target);
	while (ent)
	{
		if ((ent.rotate_type == OBJECT_MOVEWALL))
		{
			setorigin(ent, ((self.origin - self.oldorigin) + (ent.neworigin - ent.oldorigin)));
		}
		else
		{
			setorigin(ent, (ent.neworigin + self.origin));
		}
		ent = find(ent, targetname, self.target);
	}
};

void() LinkRotateTargets =
{
	local entity ent;
	local vector tempvec;

	self.oldorigin = self.origin;
	ent = find(world, targetname, self.target);
	while (ent)
	{
		if ((ent.classname == "rotate_object"))
		{
			ent.rotate_type = 0;
			ent.oldorigin = (ent.origin - self.oldorigin);
			ent.neworigin = (ent.origin - self.oldorigin);
			ent.owner = self;
		}
		else
		{
			if ((ent.classname == "func_movewall"))
			{
				ent.rotate_type = OBJECT_MOVEWALL;
				tempvec = (ent.absmin + ent.absmax) * 0.5;
				ent.oldorigin = (tempvec - self.oldorigin);
				ent.neworigin = ent.oldorigin;
				ent.owner = self;
			}
			else
			{
				ent.rotate_type = OBJECT_SETORIGIN;
				ent.oldorigin = (ent.origin - self.oldorigin);
				ent.neworigin = (ent.origin - self.oldorigin);
			}
		}
		ent = find(ent, targetname, self.target);
	}
};

void(float amount) SetDamageOnTargets =
{
	local entity ent;

	ent = find(world, targetname, self.target);
	while (ent)
	{
		if ((ent.classname == "trigger_hurt"))
		{
			hurt_setdamage(ent, amount);
		}
		else
		{
			if ((ent.classname == "func_movewall"))
			{
				ent.dmg = amount;
			}
		}
		ent = find(ent, targetname, self.target);
	}
};

void() rotate_entity_think =
{
	local float t;

	t = time - self.ltime;
	self.ltime = time;
	if ((self.state == RSTATE_SPEEDINGUP))
	{
		self.count = (self.count + (self.cnt * t));
		if ((self.count > 1))
		{
			self.count = 1;
		}
		t = t * self.count;
	}
	else
	{
		if ((self.state == RSTATE_SLOWINGDOWN))
		{
			self.count = (self.count - (self.cnt * t));
			if ((self.count < 0))
			{
				RotateTargetsFinal();
				self.state = RSTATE_INACTIVE;
				self.think = SUB_Null;
				return;
			}
			t = t * self.count;
		}
	}
	self.angles = (self.angles + (self.rotate * t));
	self.angles = SUB_NormalizeAngles(self.angles);
	RotateTargets();
	self.nextthink = (time + 0.02);
};

void() rotate_entity_use =
{
	self.frame = (1 - self.frame);
	if ((self.state == RSTATE_ACTIVE))
	{
		if ((self.spawnflags & ROTENTITY_TOGGLE))
		{
			if (self.speed)
			{
				self.count = 1;
				self.state = RSTATE_SLOWINGDOWN;
			}
			else
			{
				self.state = RSTATE_INACTIVE;
				self.think = SUB_Null;
			}
		}
	}
	else
	{
		if ((self.state == RSTATE_INACTIVE))
		{
			self.think = rotate_entity_think;
			self.nextthink = (time + 0.02);
			self.ltime = time;
			if (self.speed)
			{
				self.count = 0;
				self.state = RSTATE_SPEEDINGUP;
			}
			else
			{
				self.state = 0;
			}
		}
		else
		{
			if ((self.state == RSTATE_SPEEDINGUP))
			{
				if ((self.spawnflags & ROTENTITY_TOGGLE))
				{
					self.state = RSTATE_SLOWINGDOWN;
				}
			}
			else
			{
				self.state = RSTATE_SPEEDINGUP;
			}
		}
	}
};

void() rotate_entity_firstthink =
{
	LinkRotateTargets();
	if ((self.spawnflags & ROTENTITY_START_ON))
	{
		self.state = 0;
		self.think = rotate_entity_think;
		self.nextthink = (time + 0.02);
		self.ltime = time;
	}
	else
	{
		self.state = RSTATE_INACTIVE;
		self.think = SUB_Null;
	}
	self.use = rotate_entity_use;
};

void() func_rotate_entity =
{
	self.solid = 0;
	self.movetype = 0;
	setmodel(self, self.model);
	setsize(self, self.mins, self.maxs);
	if ((self.speed != 0))
	{
		self.cnt = (1 / self.speed);
	}
	self.think = rotate_entity_firstthink;
	self.nextthink = (time + 0.1);
	self.ltime = time;
};

void() path_rotate =
{
	if (self.noise)
	{
		precache_sound(self.noise);
	}
	if (self.noise1)
	{
		precache_sound(self.noise1);
	}
};

void() rotate_train_think =
{
	local float t;
	local float timeelapsed;

	t = time - self.ltime;
	self.ltime = time;
	if ((self.endtime && (time >= self.endtime)))
	{
		self.endtime = 0;
		if ((self.state == RSTATE_MOVE))
		{
			setorigin(self, self.finaldest);
			self.velocity = VEC_ORIGIN;
		}
		if (self.think1)
		{
			self.think1();
		}
	}
	else
	{
		timeelapsed = (time - self.cnt) * self.duration;
		if ((timeelapsed > 1))
		{
			timeelapsed = 1;
		}
		setorigin(self, (self.dest1 + (self.dest2 * timeelapsed)));
	}
	self.angles = (self.angles + (self.rotate * t));
	self.angles = SUB_NormalizeAngles(self.angles);
	RotateTargets();
	self.nextthink = (time + 0.02);
};

void() rotate_train_use =
{
	if ((self.think1 != rotate_train_find))
	{
		if ((self.velocity != VEC_ORIGIN))
		{
			return;
		}
		if (self.think1)
		{
			self.think1();
		}
	}
};

void() rotate_train_wait =
{
	self.state = 0;
	if (self.goalentity.noise)
	{
		sound(self, CHAN_VOICE, self.goalentity.noise, 1, ATTN_NORM);
	}
	else
	{
		sound(self, CHAN_VOICE, self.noise, 1, ATTN_NORM);
	}
	if ((self.goalentity.spawnflags & TRAIN_ANGLES))
	{
		self.rotate = VEC_ORIGIN;
		self.angles = self.finalangle;
	}
	if ((self.goalentity.spawnflags & TRAIN_NO_ROTATE))
	{
		self.rotate = VEC_ORIGIN;
	}
	self.endtime = (self.ltime + self.goalentity.wait);
	self.think1 = rotate_train_next;
};

void() rotate_train_stop =
{
	self.state = RSTATE_STOP;
	if (self.goalentity.noise)
	{
		sound(self, CHAN_VOICE, self.goalentity.noise, 1, ATTN_NORM);
	}
	else
	{
		sound(self, CHAN_VOICE, self.noise, 1, ATTN_NORM);
	}
	if ((self.goalentity.spawnflags & TRAIN_ANGLES))
	{
		self.rotate = VEC_ORIGIN;
		self.angles = self.finalangle;
	}
	if ((self.goalentity.spawnflags & TRAIN_NO_ROTATE))
	{
		self.rotate = VEC_ORIGIN;
	}
	self.dmg = 0;
	self.think1 = rotate_train_next;
};

void() rotate_train_next =
{
	local entity targ;
	local entity current;
	local vector vdestdelta;
	local float len;
	local float traveltime;
	local float div;
	local string temp;

	self.state = RSTATE_NEXT;
	current = self.goalentity;
	targ = find(world, targetname, self.path);
	if ((targ.classname != "path_rotate"))
	{
		objerror("Next target is not path_rotate");
	}
	if (self.goalentity.noise1)
	{
		self.noise1 = self.goalentity.noise1;
	}
	sound(self, CHAN_VOICE, self.noise1, 1, ATTN_NORM);
	self.goalentity = targ;
	self.path = targ.target;
	if (!self.path)
	{
		objerror("rotate_train_next: no next target");
	}
	if ((targ.spawnflags & TRAIN_STOP))
	{
		self.think1 = rotate_train_stop;
	}
	else
	{
		if (targ.wait)
		{
			self.think1 = rotate_train_wait;
		}
		else
		{
			self.think1 = rotate_train_next;
		}
	}
	if (current.event)
	{
		temp = self.target;
		self.target = current.event;
		self.message = current.message;
		SUB_UseTargets();
		self.target = temp;
		self.message = string_null;
	}
	if ((current.spawnflags & TRAIN_ANGLES))
	{
		self.rotate = VEC_ORIGIN;
		self.angles = self.finalangle;
	}
	if ((current.spawnflags & TRAIN_ROTATION))
	{
		self.rotate = current.rotate;
	}
	if ((current.spawnflags & TRAIN_DAMAGE))
	{
		self.dmg = current.dmg;
	}
	if ((current.spawnflags & TRAIN_SET_DAMAGE))
	{
		SetDamageOnTargets(current.dmg);
	}
	if ((current.speed == -1))
	{
		setorigin(self, targ.origin);
		self.endtime = (self.ltime + 0.01);
		SetTargetOrigin();
		if ((targ.spawnflags & TRAIN_ANGLES))
		{
			self.angles = targ.angles;
		}
		self.duration = 1;
		self.cnt = time;
		self.dest2 = VEC_ORIGIN;
		self.dest1 = self.origin;
		self.finaldest = self.origin;
	}
	else
	{
		self.state = RSTATE_MOVE;
		self.finaldest = targ.origin;
		if ((self.finaldest == self.origin))
		{
			self.velocity = VEC_ORIGIN;
			self.endtime = (self.ltime + 0.1);
			self.duration = 1;
			self.cnt = time;
			self.dest2 = VEC_ORIGIN;
			self.dest1 = self.origin;
			self.finaldest = self.origin;
			return;
		}
		vdestdelta = self.finaldest - self.origin;
		len = vlen(vdestdelta);
		if ((current.spawnflags & TRAIN_MOVETIME))
		{
			traveltime = current.speed;
		}
		else
		{
			if ((current.speed > 0))
			{
				self.speed = current.speed;
			}
			if (!self.speed)
			{
				objerror("No speed is defined!");
			}
			traveltime = len / self.speed;
		}
		if ((traveltime < 0.1))
		{
			self.velocity = VEC_ORIGIN;
			self.endtime = (self.ltime + 0.1);
			if ((targ.spawnflags & TRAIN_ANGLES))
			{
				self.angles = targ.angles;
			}
			return;
		}
		div = 1 / traveltime;
		if ((targ.spawnflags & TRAIN_ANGLES))
		{
			self.finalangle = SUB_NormalizeAngles(targ.angles);
			self.rotate = ((targ.angles - self.angles) * div);
		}
		self.endtime = (self.ltime + traveltime);
		self.velocity = (vdestdelta * div);
		self.duration = div;
		self.cnt = time;
		self.dest2 = vdestdelta;
		self.dest1 = self.origin;
	}
};

void() rotate_train_find =
{
	local entity targ;

	self.state = RSTATE_FIND;
	LinkRotateTargets();
	targ = find(world, targetname, self.path);
	if ((targ.classname != "path_rotate"))
	{
		objerror("Next target is not path_rotate");
	}
	self.goalentity = targ;
	if ((targ.spawnflags & TRAIN_ANGLES))
	{
		self.angles = targ.angles;
		self.finalangle = SUB_NormalizeAngles(targ.angles);
	}
	self.path = targ.target;
	setorigin(self, targ.origin);
	SetTargetOrigin();
	RotateTargetsFinal();
	self.think1 = rotate_train_next;
	if (!self.targetname)
	{
		self.endtime = (self.ltime + 0.1);
	}
	else
	{
		self.endtime = 0;
	}
	self.duration = 1;
	self.cnt = time;
	self.dest2 = VEC_ORIGIN;
	self.dest1 = self.origin;
};

void() rotate_train =
{
	objerror("rotate_train entities should be changed to rotate_object with\nfunc_rotate_train controllers\n");
};

void() func_rotate_train =
{
	if (!self.speed)
	{
		self.speed = 100;
	}
	if (!self.target)
	{
		objerror("rotate_train without a target");
	}
	if (!self.noise)
	{
		if ((self.sounds == 0))
		{
			self.noise = "misc/null.wav";
		}
		if ((self.sounds == 1))
		{
			self.noise = "plats/train2.wav";
		}
	}
	if (!self.noise1)
	{
		if ((self.sounds == 0))
		{
			self.noise1 = "misc/null.wav";
		}
		if ((self.sounds == 1))
		{
			self.noise1 = "plats/train1.wav";
		}
	}
	precache_sound(self.noise);
	precache_sound(self.noise1);
	self.cnt = 1;
	self.solid = 0;
	self.movetype = MOVETYPE_STEP;
	self.use = rotate_train_use;
	setmodel(self, self.model);
	setsize(self, self.mins, self.maxs);
	setorigin(self, self.origin);
	self.ltime = time;
	self.nextthink = (self.ltime + 0.1);
	self.endtime = (self.ltime + 0.1);
	self.think = rotate_train_think;
	self.think1 = rotate_train_find;
	self.state = RSTATE_FIND;
	self.duration = 1;
	self.cnt = 0.1;
	self.dest2 = VEC_ORIGIN;
	self.dest1 = self.origin;
	self.flags = (self.flags | FL_ONGROUND);
};

void() movewall_touch =
{
	if ((time < self.owner.attack_finished))
	{
		return;
	}
	if (self.dmg)
	{
		T_Damage(other, self, self.owner, self.dmg, DAMARMOR);
		self.owner.attack_finished = (time + 0.5);
	}
	else
	{
		if (self.owner.dmg)
		{
			T_Damage(other, self, self.owner, self.owner.dmg, DAMARMOR);
			self.owner.attack_finished = (time + 0.5);
		}
	}
};

void() movewall_blocked =
{
	local entity temp;

	if ((time < self.owner.attack_finished))
	{
		return;
	}
	self.owner.attack_finished = (time + 0.5);
	if ((self.owner.classname == "func_rotate_door"))
	{
		temp = self;
		self = self.owner;
		rotate_door_group_reversedirection();
		self = temp;
	}
	if (self.dmg)
	{
		T_Damage(other, self, self.owner, self.dmg, DAMARMOR);
		self.owner.attack_finished = (time + 0.5);
	}
	else
	{
		if (self.owner.dmg)
		{
			T_Damage(other, self, self.owner, self.owner.dmg, DAMARMOR);
			self.owner.attack_finished = (time + 0.5);
		}
	}
};

void() movewall_think =
{
	self.ltime = time;
	self.nextthink = (time + 0.02);
};

void() func_movewall =
{
	self.angles = VEC_ORIGIN;
	self.movetype = MOVETYPE_PUSH;
	if ((self.spawnflags & MOVEWALL_NONBLOCKING))
	{
		self.solid = 0;
	}
	else
	{
		self.solid = SOLID_BSP;
		self.blocked = movewall_blocked;
	}
	if ((self.spawnflags & MOVEWALL_TOUCH))
	{
		self.touch = movewall_touch;
	}
	setmodel(self, self.model);
	if (!(self.spawnflags & MOVEWALL_VISIBLE))
	{
		self.model = string_null;
	}
	self.dphitcontentsmask = 1;
	trace_dphitq3surfaceflags = Q3SURFACEFLAG_NOMARKS;
	self.think = movewall_think;
	self.nextthink = (time + 0.02);
	self.ltime = time;
};

void() rotobj_think =
{
	self.ltime = time;
	self.nextthink = (time + 0.02);
};

void() misc_blocked =
{
	T_Damage(other, self, self, self.dmg);
};

void() rotate_object =
{
	self.classname = "rotate_object";
	if ((self.spawnflags & 1))
	{
		self.solid = SOLID_BSP;
		self.movetype = MOVETYPE_PUSH;
		self.think = rotobj_think;
		self.blocked = misc_blocked;
		self.nextthink = time;
	}
	else
	{
		self.solid = 0;
		self.movetype = 0;
		self.think = SUB_Null;
	}
	setmodel(self, self.model);
	setsize(self, self.mins, self.maxs);
};

void() rotate_door_think2 =
{
	local float t;

	t = time - self.ltime;
	self.ltime = time;
	self.frame = (1 - self.frame);
	self.angles = self.dest;
	if ((self.state == RSTATE_OPENING))
	{
		self.state = RSTATE_OPEN;
	}
	else
	{
		if ((self.spawnflags & DOOR_STAYOPEN))
		{
			rotate_door_group_reversedirection();
			return;
		}
		self.state = RSTATE_CLOSED;
	}
	sound(self, CHAN_VOICE, self.noise3, 1, ATTN_NORM);
	self.think = SUB_Null;
	RotateTargetsFinal();
};

void() rotate_door_think =
{
	local float t;

	t = time - self.ltime;
	self.ltime = time;
	if ((time < self.endtime))
	{
		self.angles = (self.angles + (self.rotate * t));
		RotateTargets();
	}
	else
	{
		self.angles = self.dest;
		RotateTargets();
		self.think = rotate_door_think2;
	}
	self.nextthink = (time + 0.01);
};

void() rotate_door_reversedirection =
{
	local vector start;

	self.frame = (1 - self.frame);
	if ((self.state == RSTATE_CLOSING))
	{
		start = self.dest1;
		self.dest = self.dest2;
		self.state = RSTATE_OPENING;
	}
	else
	{
		start = self.dest2;
		self.dest = self.dest1;
		self.state = RSTATE_CLOSING;
	}
	sound(self, CHAN_VOICE, self.noise2, 1, ATTN_NORM);
	self.rotate = ((self.dest - start) * (1 / self.speed));
	self.think = rotate_door_think;
	self.nextthink = (time + 0.02);
	self.endtime = ((time + self.speed) - (self.endtime - time));
	self.ltime = time;
};

void() rotate_door_group_reversedirection =
{
	local string name;

	if (self.group)
	{
		name = self.group;
		self = find(world, group, name);
		while (self)
		{
			rotate_door_reversedirection();
			self = find(self, group, name);
		}
	}
	else
	{
		rotate_door_reversedirection();
	}
};

void() rotate_door_use =
{
	local vector start;

	if (((self.state != RSTATE_OPEN) && (self.state != RSTATE_CLOSED)))
	{
		return;
	}
	if (!self.cnt)
	{
		self.cnt = 1;
		LinkRotateTargets();
	}
	self.frame = (1 - self.frame);
	if ((self.state == RSTATE_CLOSED))
	{
		start = self.dest1;
		self.dest = self.dest2;
		self.state = RSTATE_OPENING;
	}
	else
	{
		start = self.dest2;
		self.dest = self.dest1;
		self.state = RSTATE_CLOSING;
	}
	sound(self, CHAN_VOICE, self.noise2, 1, ATTN_NORM);
	self.rotate = ((self.dest - start) * (1 / self.speed));
	self.think = rotate_door_think;
	self.nextthink = (time + 0.01);
	self.endtime = (time + self.speed);
	self.ltime = time;
};

void() func_rotate_door =
{
	if (!self.target)
	{
		objerror("rotate_door without target.");
	}
	self.dest1 = VEC_ORIGIN;
	self.dest2 = self.angles;
	self.angles = self.dest1;
	if (!self.speed)
	{
		self.speed = 2;
	}
	self.cnt = 0;
	if (!self.dmg)
	{
		self.dmg = 2;
	}
	else
	{
		if ((self.dmg < 0))
		{
			self.dmg = 0;
		}
	}
	if ((self.sounds == 0))
	{
		self.sounds = 1;
	}
	if ((self.sounds == 1))
	{
		precache_sound("doors/latch2.wav");
		precache_sound("doors/winch2.wav");
		precache_sound("doors/drclos4.wav");
		self.noise1 = "doors/latch2.wav";
		self.noise2 = "doors/winch2.wav";
		self.noise3 = "doors/drclos4.wav";
	}
	if ((self.sounds == 2))
	{
		precache_sound("doors/airdoor1.wav");
		precache_sound("doors/airdoor2.wav");
		self.noise2 = "doors/airdoor1.wav";
		self.noise1 = "doors/airdoor2.wav";
		self.noise3 = "doors/airdoor2.wav";
	}
	if ((self.sounds == 3))
	{
		precache_sound("doors/basesec1.wav");
		precache_sound("doors/basesec2.wav");
		self.noise2 = "doors/basesec1.wav";
		self.noise1 = "doors/basesec2.wav";
		self.noise3 = "doors/basesec2.wav";
	}
	self.solid = 0;
	self.movetype = 0;
	setmodel(self, self.model);
	setorigin(self, self.origin);
	setsize(self, self.mins, self.maxs);
	self.state = RSTATE_CLOSED;
	self.use = rotate_door_use;
	self.think = SUB_Null;
};
