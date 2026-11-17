//Decompiled code. Please respect the original copyright.

float(entity e1, entity e2) CheckLinked =
{
	if ((((e1 == e2) || (e2 == world)) || (e1 == world)))
	{
		return (0);
	}
	else
	{
		if ((e1.target1 == e2))
		{
			if ((e1.b_aiflags & AI_TELELINK_1))
			{
				return (2);
			}
			else
			{
				return (TRUE);
			}
		}
		else
		{
			if ((e1.target2 == e2))
			{
				if ((e1.b_aiflags & AI_TELELINK_2))
				{
					return (2);
				}
				else
				{
					return (TRUE);
				}
			}
			else
			{
				if ((e1.target3 == e2))
				{
					if ((e1.b_aiflags & AI_TELELINK_3))
					{
						return (2);
					}
					else
					{
						return (TRUE);
					}
				}
				else
				{
					if ((e1.target4 == e2))
					{
						if ((e1.b_aiflags & AI_TELELINK_4))
						{
							return (2);
						}
						else
						{
							return (TRUE);
						}
					}
					else
					{
						return (0);
					}
				}
			}
		}
	}
};

float(entity e1, entity e2) LinkWays =
{
	if ((((e1 == e2) || (e2 == world)) || (e1 == world)))
	{
		return (0);
	}
	else
	{
		if (CheckLinked(e1, e2))
		{
			return (0);
		}
	}
	if ((e1.target1 == world))
	{
		e1.target1 = e2;
		return (TRUE);
	}
	else
	{
		if ((e1.target2 == world))
		{
			e1.target2 = e2;
			return (TRUE);
		}
		else
		{
			if ((e1.target3 == world))
			{
				e1.target3 = e2;
				return (TRUE);
			}
			else
			{
				if ((e1.target4 == world))
				{
					e1.target4 = e2;
					return (TRUE);
				}
				else
				{
					return (0);
				}
			}
		}
	}
};

float(entity e1, entity e2) TeleLinkWays =
{
	if ((((e1 == e2) || (e2 == world)) || (e1 == world)))
	{
		return (0);
	}
	else
	{
		if (CheckLinked(e1, e2))
		{
			return (0);
		}
	}
	if ((e1.target1 == world))
	{
		e1.target1 = e2;
		e1.b_aiflags = (e1.b_aiflags | AI_TELELINK_1);
		return (TRUE);
	}
	else
	{
		if ((e1.target2 == world))
		{
			e1.target2 = e2;
			e1.b_aiflags = (e1.b_aiflags | AI_TELELINK_2);
			return (TRUE);
		}
		else
		{
			if ((e1.target3 == world))
			{
				e1.target3 = e2;
				e1.b_aiflags = (e1.b_aiflags | AI_TELELINK_3);
				return (TRUE);
			}
			else
			{
				if ((e1.target4 == world))
				{
					e1.target4 = e2;
					e1.b_aiflags = (e1.b_aiflags | AI_TELELINK_4);
					return (TRUE);
				}
				else
				{
					return (0);
				}
			}
		}
	}
};

void(entity e1, entity e2) UnlinkWays =
{
	if ((((e1 == e2) || (e2 == world)) || (e1 == world)))
	{
		return;
	}
	else
	{
		if (!CheckLinked(e1, e2))
		{
			return;
		}
	}
	if ((e1.target1 == e2))
	{
		e1.b_aiflags = (e1.b_aiflags - (e1.b_aiflags & AI_TELELINK_1));
		e1.target1 = world;
	}
	if ((e1.target2 == e2))
	{
		e1.b_aiflags = (e1.b_aiflags - (e1.b_aiflags & AI_TELELINK_2));
		e1.target2 = world;
	}
	if ((e1.target3 == e2))
	{
		e1.b_aiflags = (e1.b_aiflags - (e1.b_aiflags & AI_TELELINK_3));
		e1.target3 = world;
	}
	if ((e1.target4 == e2))
	{
		e1.b_aiflags = (e1.b_aiflags - (e1.b_aiflags & AI_TELELINK_4));
		e1.target4 = world;
	}
};

entity(entity start) FindWayPoint =
{
	local entity t;
	local vector org;
	local float dst;
	local float tdst;
	local entity best;

	org = realorigin(self);
	t = way_head;
	if ((start != world))
	{
		dst = vlen((start.origin - org));
		best = start;
	}
	else
	{
		dst = 100000;
		best = world;
	}
	while (t)
	{
		if ((dst < 20))
		{
			return (best);
		}
		if ((!(t.b_aiflags & AI_IGNORE_TYPES) || self.ishuman))
		{
			tdst = vlen((t.origin - org));
			if ((tdst < dst))
			{
				if (sisible(t))
				{
					dst = tdst;
					best = t;
				}
			}
		}
		t = t._next;
	}
	return (best);
};

entity(vector org) make_waypoint =
{
	local entity point;

	point = spawn();
	point.classname = "waypoint";
	point.solid = SOLID_TRIGGER;
	point.movetype = 0;
	point.items = -1;
	setorigin(point, org);
	setsize(point, VEC_HULL_MIN, VEC_HULL_MAX);
	waypoints = waypoints + 1;
	if (!way_head)
	{
		way_head = point;
		way_foot = point;
	}
	else
	{
		way_foot._next = point;
		point._last = way_foot;
		way_foot = point;
	}
	point.count = waypoints;
	if ((waypoint_mode > WM_LOADED))
	{
		setmodel(point, "progs/s_bubble.spr");
	}
	return (point);
};

void() DynamicWaypoint =
{
	local entity t;
	local float dist;
	local float dynlink;
	local float dynpoint;
	local float editor;

	if ((self.teleport_time > self.portal_time))
	{
		if (!(self.flags & FL_WATERJUMP))
		{
			self.dyn_flags = 2;
			if (!self.ishuman)
			{
				bot_lost(self.target1, TRUE);
				self.enemy = world;
			}
		}
		self.portal_time = self.teleport_time;
	}
	if ((waypoint_mode > WM_LOADED))
	{
		if (self.ishuman)
		{
			if ((waypoint_mode == WM_EDITOR_DYNLINK))
			{
				dynlink = 1;
			}
			else
			{
				if ((waypoint_mode == WM_EDITOR_DYNAMIC))
				{
					dynpoint = 1;
					dynlink = 1;
				}
			}
			editor = 1;
		}
	}
	else
	{
		if ((waypoint_mode == WM_DYNAMIC))
		{
			dynpoint = 1;
			dynlink = 1;
		}
	}
	if (!dynpoint)
	{
		if (!editor)
		{
			return;
		}
	}
	if (!self.ishuman)
	{
		if (coop)
		{
			return;
		}
	}
	if ((max_clients < 2))
	{
		return;
	}
	else
	{
		if ((self.health <= 0))
		{
			if (dynpoint)
			{
				if (self.current_way)
				{
					if ((pointcontents(self.origin) < -4))
					{
						if ((self.current_way.b_aiflags & AI_BLIND))
						{
							self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_PRECISION);
						}
						else
						{
							self.current_way.b_aiflags = (self.current_way.b_aiflags | AI_BLIND);
						}
					}
				}
			}
			self.dyn_dest = VEC_ORIGIN;
			self.current_way = world;
			self.dyn_flags = 0;
			return;
		}
	}
	if (dynpoint)
	{
		if (!((self.flags & FL_ONGROUND) || (self.waterlevel == 3)))
		{
			if ((self.dyn_flags != 2))
			{
				self.dyn_flags = 1;
			}
			return;
		}
	}
	if ((self.dyn_time > time))
	{
		return;
	}
	self.dyn_time = (time + 0.2);
	if (editor)
	{
		if (self.current_way)
		{
			if (self.current_way.target1)
			{
				DeveloperLightning(self.current_way, self.current_way.target1, (self.current_way.b_aiflags & AI_TELELINK_1));
			}
			if (self.current_way.target2)
			{
				DeveloperLightning(self.current_way, self.current_way.target2, (self.current_way.b_aiflags & AI_TELELINK_2));
			}
			if (self.current_way.target3)
			{
				DeveloperLightning(self.current_way, self.current_way.target3, (self.current_way.b_aiflags & AI_TELELINK_3));
			}
			if (self.current_way.target4)
			{
				DeveloperLightning(self.current_way, self.current_way.target4, (self.current_way.b_aiflags & AI_TELELINK_4));
			}
		}
		if ((self.b_aiflags & AI_HOLD_SELECT))
		{
			return;
		}
	}
	t = FindWayPoint(self.current_way);
	if (t)
	{
		dist = vlen((self.origin - t.origin));
		if ((dist < 192))
		{
			if ((dist < 64))
			{
				if ((t != self.current_way))
				{
					if (dynlink)
					{
						if (!self.dyn_flags)
						{
							if (wisible(t, self.current_way))
							{
								LinkWays(t, self.current_way);
							}
						}
						if ((self.dyn_flags == 2))
						{
							TeleLinkWays(self.current_way, t);
						}
						else
						{
							if (wisible(t, self.current_way))
							{
								LinkWays(self.current_way, t);
							}
						}
					}
					if (editor)
					{
						setmodel(t, "progs/s_light.spr");
						if (self.current_way)
						{
							setmodel(self.current_way, "progs/s_bubble.spr");
						}
					}
				}
				self.current_way = t;
				self.dyn_flags = 0;
			}
			self.dyn_dest = (self.origin + self.view_ofs);
			return;
		}
	}
	if (frik_recognize_plat(FALSE))
	{
		if ((vlen(trace_ent.velocity) > 0))
		{
			if (self.dyn_plat)
			{
				return;
			}
			self.dyn_plat = TRUE;
			if (!self.dyn_flags)
			{
				self.dyn_flags = 1;
			}
		}
		else
		{
			self.dyn_plat = 0;
		}
	}
	else
	{
		self.dyn_plat = 0;
	}
	if ((self.dyn_flags == 2))
	{
		self.dyn_dest = (self.origin + self.view_ofs);
	}
	else
	{
		if ((self.dyn_dest == VEC_ORIGIN))
		{
			self.dyn_dest = (self.origin + self.view_ofs);
		}
	}
	if (!dynpoint)
	{
		return;
	}
	t = make_waypoint(self.dyn_dest);
	if (!self.dyn_flags)
	{
		if (wisible(t, self.current_way))
		{
			LinkWays(t, self.current_way);
		}
	}
	if ((self.dyn_flags == 2))
	{
		TeleLinkWays(self.current_way, t);
	}
	else
	{
		if (wisible(t, self.current_way))
		{
			LinkWays(self.current_way, t);
		}
	}
	if (editor)
	{
		setmodel(t, "progs/s_light.spr");
		if (self.current_way)
		{
			setmodel(self.current_way, "progs/s_bubble.spr");
		}
	}
	self.current_way = t;
	self.dyn_flags = 0;
	self.dyn_dest = (self.origin + self.view_ofs);
	if (frik_recognize_plat(FALSE))
	{
		if ((trace_ent.classname == "door"))
		{
			t.b_aiflags = (t.b_aiflags | AI_DOORFLAG);
		}
	}
};

void() ClearAllWays =
{
	local entity t;
	local entity n;

	t = way_head;
	while (t)
	{
		n = t._next;
		remove(t);
		t = n;
	}
	way_head = world;
	way_foot = world;
	waypoints = 0;
};

entity(float num) WaypointForNum =
{
	local entity t;

	if (!num)
	{
		return (world);
	}
	t = way_head;
	while (t)
	{
		if ((t.count == num))
		{
			return (t);
		}
		t = t._next;
	}
	return (world);
};

void() FixThisWaypoint =
{

	self.enemy.target1 = WaypointForNum(self.enemy.b_pants);
	self.enemy.target2 = WaypointForNum(self.enemy.b_skill);
	self.enemy.target3 = WaypointForNum(self.enemy.b_shirt);
	self.enemy.target4 = WaypointForNum(self.enemy.b_frags);
	self.enemy = self.enemy._next;
	self.nextthink = time;
	if ((self.enemy == world))
	{
		remove(self);
		fixer = world;
	}
};

void() FixWaypoints =
{
	if (!fixer)
	{
		fixer = spawn();
	}
	fixer.nextthink = time;
	fixer.think = FixThisWaypoint;
	fixer.enemy = way_head;
};

void(entity what) delete_waypoint =
{
	local entity t;

	if ((way_head == what))
	{
		way_head = what._next;
	}
	if ((way_foot == what))
	{
		way_foot = what._last;
	}
	if (what._last)
	{
		what._last._next = what._next;
	}
	if (what._next)
	{
		what._next._last = what._last;
	}
	waypoints = 0;
	t = way_head;
	while (t)
	{
		waypoints = waypoints + 1;
		t.count = waypoints;
		if (CheckLinked(t, what))
		{
			UnlinkWays(t, what);
		}
		t = t._next;
	}
	if ((self.current_way == what))
	{
		self.current_way = world;
	}
	remove(what);
};

entity(string s) FindThing =
{
	local entity t;
	local float tdst;
	local float dst;
	local entity best;

	dst = 100000;
	best = world;
	t = find(world, classname, s);
	while ((t != world))
	{
		tdst = vlen((((t.absmin + t.absmax) * 0.5) - self.origin));
		if ((tdst < dst))
		{
			dst = tdst;
			best = t;
		}
		t = find(t, classname, s);
	}
	return (best);
};

entity(entity lastone) FindRoute =
{
	local entity t;
	local entity best;
	local float dst;
	local float tdst;
	local float flag;

	flag = ClientBitFlag(self.b_clientno);
	if (lastone)
	{
		if ((lastone.target1.b_sound & flag))
		{
			return (lastone.target1);
		}
		else
		{
			if ((lastone.target2.b_sound & flag))
			{
				return (lastone.target2);
			}
			else
			{
				if ((lastone.target3.b_sound & flag))
				{
					return (lastone.target3);
				}
				else
				{
					if ((lastone.target4.b_sound & flag))
					{
						return (lastone.target4);
					}
				}
			}
		}
	}
	t = way_head;
	dst = 100000;
	best = world;
	while (t)
	{
		tdst = vlen((t.origin - self.origin));
		if (((tdst < dst) && (t.b_sound & flag)))
		{
			dst = tdst;
			best = t;
		}
		t = t._next;
	}
	return (best);
};

void() ClearRouteTable =
{
	local entity t;

	t = way_head;
	while (t)
	{
		t.keys = 0;
		t.enemy = world;
		t.items = -1;
		t = t._next;
	}
};

void() ClearMyRoute =
{
	local float flag;
	local entity t;

	flag = ClientBitFlag(self.b_clientno);
	t = way_head;
	while (t)
	{
		t.b_sound = (t.b_sound - (t.b_sound & flag));
		t = t._next;
	}
};

void(entity this) mark_path =
{
	local entity t;
	local entity oself;
	local float flag;

	ClearMyRoute();
	oself = self;
	self = this;
	t = FindWayPoint(this.current_way);
	self = oself;
	if ((this.classname != "player"))
	{
		this.current_way = t;
	}
	if ((t.enemy == world))
	{
		bot_lost(this, FALSE);
		self.route_failed = TRUE;
		return;
	}
	flag = ClientBitFlag(self.b_clientno);
	while (t)
	{
		if ((t.b_sound & flag))
		{
			return;
		}
		if ((t == self.last_way))
		{
			return;
		}
		t.b_sound = (t.b_sound | flag);
		t = t.enemy;
	}
};

void(entity e2, float b_bit) FollowLink =
{
	local float dist;

	if ((self.b_aiflags & b_bit))
	{
		dist = self.items;
	}
	else
	{
		dist = vlen((self.origin - e2.origin)) + self.items;
	}
	if ((e2.b_aiflags & AI_SUPER_JUMP))
	{
		if (!bot_can_rj(route_table))
		{
			return;
		}
	}
	if ((e2.b_aiflags & AI_DIFFICULT))
	{
		dist = dist + 1000;
	}
	if (((dist < e2.items) || (e2.items == -1)))
	{
		if (!e2.keys)
		{
			busy_waypoints = busy_waypoints + 1;
		}
		e2.keys = TRUE;
		e2.items = dist;
		e2.think = WaypointThink;
		e2.nextthink = time;
		e2.enemy = self;
	}
};

void() WaypointThink =
{
	local entity oself;

	if ((self.items == -1))
	{
		return;
	}
	if ((self.b_aiflags & AI_TRACE_TEST))
	{
		if (self.target1)
		{
			traceline(self.origin, self.target1.origin, TRUE, self);
			if ((trace_fraction == 1))
			{
				FollowLink(self.target1, AI_TELELINK_1);
			}
		}
		if (self.target2)
		{
			traceline(self.origin, self.target2.origin, TRUE, self);
			if ((trace_fraction == 1))
			{
				FollowLink(self.target2, AI_TELELINK_2);
			}
		}
		if (self.target3)
		{
			traceline(self.origin, self.target3.origin, TRUE, self);
			if ((trace_fraction == 1))
			{
				FollowLink(self.target3, AI_TELELINK_3);
			}
		}
		if (self.target4)
		{
			traceline(self.origin, self.target4.origin, TRUE, self);
			if ((trace_fraction == 1))
			{
				FollowLink(self.target4, AI_TELELINK_4);
			}
		}
	}
	else
	{
		if (self.target1)
		{
			FollowLink(self.target1, AI_TELELINK_1);
		}
		if (self.target2)
		{
			FollowLink(self.target2, AI_TELELINK_2);
		}
		if (self.target3)
		{
			FollowLink(self.target3, AI_TELELINK_3);
		}
		if (self.target4)
		{
			FollowLink(self.target4, AI_TELELINK_4);
		}
	}
	busy_waypoints = busy_waypoints - 1;
	self.keys = 0;
	if ((busy_waypoints <= 0))
	{
		if (direct_route)
		{
			oself = self;
			self = route_table;
			bot_get_path(self.target1, FALSE);
			self = oself;
			direct_route = 0;
		}
	}
};

float() begin_route =
{

	if ((busy_waypoints > 0))
	{
		return (0);
	}
	if ((route_table != world))
	{
		if (!route_table.ishuman)
		{
			if ((route_table.b_clientno != -1))
			{
				return (0);
			}
		}
	}
	route_table = self;
	ClearRouteTable();
	self.last_way = FindWayPoint(self.current_way);
	if ((self.last_way != world))
	{
		self.last_way.items = vlen((self.last_way.origin - self.origin));
		self.last_way.nextthink = time;
		self.last_way.think = WaypointThink;
		self.last_way.keys = TRUE;
		busy_waypoints = 1;
		return (TRUE);
	}
	else
	{
		route_table = world;
		busy_waypoints = 0;
		return (0);
	}
};

void(entity this, float direct) bot_get_path =
{
	if ((this == world))
	{
		return;
	}
	if ((route_table == self))
	{
		if ((busy_waypoints <= 0))
		{
			route_table = world;
			mark_path(this);
		}
		return;
	}
	if (direct)
	{
		if (begin_route())
		{
			direct_route = TRUE;
		}
		else
		{
			bot_lost(this, FALSE);
		}
		return;
	}
};

void() waypoint =
{
	self.solid = SOLID_TRIGGER;
	self.movetype = 0;
	setorigin(self, self.origin);
	setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	waypoints = waypoints + 1;
	if (!way_head)
	{
		way_head = self;
		way_foot = self;
	}
	else
	{
		way_foot._next = self;
		self._last = way_foot;
		way_foot = self;
	}
	self.count = waypoints;
	waypoint_mode = WM_LOADED;
	if ((self.count == 1))
	{
		localcmd("echo BSP waypoints detected\n");
		self.think = FixWaypoints;
		self.nextthink = time;
	}
};

void(vector org, vector bit1, float bit4, float flargs) make_way =
{
	local entity y;

	waypoint_mode = WM_LOADED;
	y = make_waypoint(org);
	y.b_aiflags = flargs;
	y.b_pants = bit1_x;
	y.b_skill = bit1_y;
	y.b_shirt = bit1_z;
	y.b_frags = bit4;
	if ((y.count == 1))
	{
		localcmd("echo QuakeC waypoints detected\n");
		y.think = FixWaypoints;
		y.nextthink = time;
	}
};

void(vector org) SpawnTempWaypoint =
{
	local entity tep;

	if (!self.temp_way)
	{
		tep = spawn();
		self.temp_way = tep;
	}
	else
	{
		tep = self.temp_way;
	}
	tep.classname = "temp_waypoint";
	tep.solid = SOLID_TRIGGER;
	tep.movetype = MOVETYPE_NOCLIP;
	setorigin(tep, org);
	target_add(tep);
	setsize(tep, VEC_HULL_MIN, VEC_HULL_MAX);
};
