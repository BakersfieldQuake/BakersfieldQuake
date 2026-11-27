//Decompiled code. Please respect the original copyright.

void() SUB_Null =
{
};

void() SUB_Remove =
{
	remove(self);
};

void() SetMovedir =
{
	if ((self.angles == '0 -1 0'))
	{
		self.movedir = '0 0 1';
	}
	else
	{
		if ((self.angles == '0 -2 0'))
		{
			self.movedir = '0 0 -1';
		}
		else
		{
			makevectors(self.angles);
			self.movedir = v_forward;
		}
	}
	self.angles = VEC_ORIGIN;
};

void() InitTrigger =
{
	if ((self.angles != VEC_ORIGIN))
	{
		SetMovedir();
	}
	self.solid = SOLID_TRIGGER;
	setmodel(self, self.model);
	self.movetype = 0;
	self.modelindex = 0;
	self.model = "";
};

void(entity ent, vector tdest, float tspeed, void() func) SUB_CalcMoveEnt =
{
	local entity stemp;

	stemp = self;
	self = ent;
	SUB_CalcMove(tdest, tspeed, func);
	self = stemp;
};

void(vector tdest, float tspeed, void() func) SUB_CalcMove =
{
	local vector vdestdelta;
	local float len;
	local float traveltime;

	if (!tspeed)
	{
		objerror("No speed is defined!");
	}
	self.think1 = func;
	self.finaldest = tdest;
	self.think = SUB_CalcMoveDone;
	if ((tdest == self.origin))
	{
		self.velocity = VEC_ORIGIN;
		self.nextthink = (self.ltime + 0.1);
		return;
	}
	vdestdelta = tdest - self.origin;
	len = vlen(vdestdelta);
	traveltime = len / tspeed;
	if ((traveltime < 0.1))
	{
		self.velocity = VEC_ORIGIN;
		self.nextthink = (self.ltime + 0.1);
		return;
	}
	self.nextthink = (self.ltime + traveltime);
	self.velocity = (vdestdelta * (1 / traveltime));
};

void() SUB_CalcMoveDone =
{
	setorigin(self, self.finaldest);
	self.velocity = VEC_ORIGIN;
	self.nextthink = -1;
	if (self.think1)
	{
		self.think1();
	}
};

void(entity ent, vector destangle, float tspeed, void() func) SUB_CalcAngleMoveEnt =
{
	local entity stemp;

	stemp = self;
	self = ent;
	SUB_CalcAngleMove(destangle, tspeed, func);
	self = stemp;
};

void(vector destangle, float tspeed, void() func) SUB_CalcAngleMove =
{
	local vector destdelta;
	local float len;
	local float traveltime;

	if (!tspeed)
	{
		objerror("No speed is defined!");
	}
	destdelta = destangle - self.angles;
	len = vlen(destdelta);
	traveltime = len / tspeed;
	self.nextthink = (self.ltime + traveltime);
	self.avelocity = (destdelta * (1 / traveltime));
	self.think1 = func;
	self.finalangle = destangle;
	self.think = SUB_CalcAngleMoveDone;
};

void() SUB_CalcAngleMoveDone =
{
	self.angles = self.finalangle;
	self.avelocity = VEC_ORIGIN;
	self.nextthink = -1;
	if (self.think1)
	{
		self.think1();
	}
};

void() DelayThink =
{
	activator = self.enemy;
	SUB_UseTargets();
	remove(self);
};

void() SUB_UseTargets =
{
	local entity t;
	local entity stemp;
	local entity otemp;
	local entity act;

	if (self.delay)
	{
		t = spawn();
		t.classname = "DelayedUse";
		t.nextthink = (time + self.delay);
		t.think = DelayThink;
		t.enemy = activator;
		t.message = self.message;
		t.killtarget = self.killtarget;
		t.target = self.target;
		return;
	}
	if (((activator.classname == "player") && (self.message != "")))
	{
		centerprint(activator, self.message);
		if (!self.noise)
		{
			sound(activator, CHAN_VOICE, "misc/talk.wav", 1, ATTN_NORM);
		}
	}
	if (self.killtarget)
	{
		t = world;
		do
		{
			t = find(t, targetname, self.killtarget);
			if (!t)
			{
				return;
			}
			remove(t);
		} while(1);
	}
	if (self.target)
	{
		act = activator;
		t = world;
		do
		{
			t = find(t, targetname, self.target);
			if (!t)
			{
				return;
			}
			stemp = self;
			otemp = other;
			self = t;
			other = stemp;
			if ((self.use != SUB_Null))
			{
				if (self.use)
				{
					self.use();
				}
			}
			self = stemp;
			other = otemp;
			activator = act;
		} while(1);
	}
};

void(float normal) SUB_AttackFinished =
{
	self.cnt = 0;
	if ((self.flags & FL_MONSTER))
		BM_Radar_Ping(self, self.origin, BM_RPK_MONSTER);
	if ((skill != 3))
	{
		self.attack_finished = (time + normal);
	}
};

void(void() thinkst) SUB_CheckRefire =
{
	if ((skill != 3))
	{
		return;
	}
	if ((self.cnt == 1))
	{
		return;
	}
	if (!visible(self.enemy))
	{
		return;
	}
	self.cnt = 1;
	self.think = thinkst;
};

vector(vector iorg, vector org_offset, entity targ, float zspeed) SUB_Tracking =
{
	local vector vec;
	local vector org;
	local float diff;

	makevectors(self.angles);
	org = ((self.origin + (org_offset_x * v_forward)) + (org_offset_y * v_right)) + (org_offset_z * v_up);
	diff = vlen((iorg - org)) / zspeed;
	vec = targ.velocity;
	if ((targ.flags & FL_MONSTER))
	{
	}
	else
	{
	}
	iorg = targ.origin + (diff * vec);
	return (iorg);
};

// A trail effect number for .traileffectnum. particleeffectnum() answers -1 for a name effectinfo.txt does not have,
// and -1 goes over the network as 65535: every client that can see the entity then prints "Unknown effect number
// 65535 received from server" each frame. 0 means no trail.
float(string fxname) BM_TrailEffect =
{
	local float n;

	if (fxname == "")
		return 0;
	n = particleeffectnum(fxname);
	if (n < 0)
		return 0;
	return n;
};

// Remove a one-shot (PUSH_ONCE) trigger_push. It has to leave the bm_push_head list first: the karts and vans walk that
// list, and a removed pad left in it cut off every pad after it once its edict was reused, and made whatever took the
// edict act as a jump pad.
void(entity pad) BM_PushRemove =
{
	local entity e;

	if (bm_push_head == pad)
		bm_push_head = pad.bm_push_next;
	else
	{
		e = bm_push_head;
		while (e != world)
		{
			if (e.bm_push_next == pad)
			{
				e.bm_push_next = pad.bm_push_next;
				break;
			}
			e = e.bm_push_next;
		}
	}
	pad.bm_push_next = world;
	remove(pad);
};
