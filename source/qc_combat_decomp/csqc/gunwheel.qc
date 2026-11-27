// ================================================================= Gun Wheel
// Hold the "+gunwheel" key: a ring of 19 guns opens, the view stops turning, the mouse direction picks a slice and
// letting go sends that gun's impulse. The server says what is owned and loaded (bm_gunwheel.qc, stats 133-151, 153).
// The translucent ring over the middle of the screen is the user's exception to the no-dark-panel HUD rule.

float GW_SLOTS = 19;
float GW_STAT = 133;			// first slot stat (slots 0..1 -> 133..134, slot 2 Chaingun -> 153, slots 3..18 -> 135..150)
float GW_HELD_STAT = 151;		// may open / held slot (1..19)
float GW_REACH = 150;			// mouse counts from the centre to the rim of the pointer's travel
float GW_DEAD = 35;			// counts around the centre that pick nothing

float(float i) GW_SlotStat =
{
	if (i == 2) return getstati (160);
	if (i > 2) return getstati (GW_STAT + i - 1);
	return getstati (GW_STAT + i);
};

float gw_open;
float gw_sel;					// highlighted slot, -1 = none
float gw_x, gw_y;				// pointer, mouse counts from the centre

float(float i) GW_Impulse =
{
	if (i == 0) return 1;		if (i == 1) return 3;		if (i == 2) return 4;
	if (i == 3) return 5;		if (i == 4) return 6;		if (i == 5) return 7;
	if (i == 6) return 18;		if (i == 7) return 16;		if (i == 8) return 14;
	if (i == 9) return 67;		if (i == 10) return 69;		if (i == 11) return 61;
	if (i == 12) return 62;		if (i == 13) return 63;		if (i == 14) return 64;
	if (i == 15) return 65;		if (i == 16) return 66;		if (i == 17) return 68;
	return 70;
};

string(float i) GW_Pic =
{
	if (i == 0) return "gfx/gunwheel/hammer";		if (i == 1) return "gfx/gunwheel/pump";
	if (i == 2) return "gfx/gunwheel/chaingun";		if (i == 3) return "gfx/gunwheel/milky";
	if (i == 4) return "gfx/gunwheel/grenade";		if (i == 5) return "gfx/gunwheel/rocket";
	if (i == 6) return "gfx/gunwheel/lightning";	if (i == 7) return "gfx/gunwheel/ccc";
	if (i == 8) return "gfx/gunwheel/megaman";		if (i == 9) return "gfx/gunwheel/m4";
	if (i == 10) return "gfx/gunwheel/garand";		if (i == 11) return "gfx/gunwheel/robdob";
	if (i == 12) return "gfx/gunwheel/jar";			if (i == 13) return "gfx/gunwheel/pickle";
	if (i == 14) return "gfx/gunwheel/netsend";		if (i == 15) return "gfx/gunwheel/dookie";
	if (i == 16) return "gfx/gunwheel/wheelman";	if (i == 17) return "gfx/gunwheel/kyle";
	return "gfx/gunwheel/cyrax";
};

string(float i) GW_Name =
{
	if (i == 0) return "Bonk Hammer";				if (i == 1) return "Pump Shotgun";
	if (i == 2) return "Chaingun Cannon";			if (i == 3) return "Milky Gun";
	if (i == 4) return "Grenade Launcher";			if (i == 5) return "Rocket Launcher";
	if (i == 6) return "Lightning Gun";				if (i == 7) return "CCC Laser Cannon";
	if (i == 8) return "Mega Man";					if (i == 9) return "M4A1";
	if (i == 10) return "M1 Garand";				if (i == 11) return "Rob Dob";
	if (i == 12) return "Jar o' Green Guys";		if (i == 13) return "Pickle Surprise";
	if (i == 14) return "NetSend";					if (i == 15) return "Dookie Bazooka";
	if (i == 16) return "Wheelman Cannon";			if (i == 17) return "The Pocket Kyle";
	return "Cyrax Net";
};

// what it does, two short lines
string(float i, float line) GW_Desc =
{
	if (i == 0) return line ? "Hold fire to charge" : "Melee bonk";
	if (i == 1) return line ? "shotgun blast" : "Close range";
	if (i == 2) return line ? "rotary ripper" : "Triple-barrel";
	if (i == 3) return line ? "chases them down" : "A Pink Lady";
	if (i == 4) return line ? "grenades" : "Bouncing";
	if (i == 5) return line ? "big splash" : "Rockets,";
	if (i == 6) return line ? "electric beam" : "Continuous";
	if (i == 7) return line ? "laser bolts" : "Rapid twin";
	if (i == 8) return line ? "and blows them up" : "Hunts them down";
	if (i == 9) return line ? "rifle" : "Automatic";
	if (i == 10) return line ? "hits hard" : "Semi-auto rifle,";
	if (i == 11) return line ? "fire to dash or blow" : "Steer his head,";
	if (i == 12) return line ? "release to swarm" : "Hold to shake,";
	if (i == 13) return line ? "booby trap" : "Throw a sticky";
	if (i == 14) return line ? "a sentry PC" : "Throw a disk,";
	if (i == 15) return line ? "release to splatter" : "Hold to wind up,";
	if (i == 16) return line ? "launch the Wheelman" : "Hold to charge,";
	if (i == 17) return line ? "release to yeet" : "Hold to lock on,";
	return line ? "then click to bonk" : "Net them,";
};

void() GW_Precache =
{
	local float i;

	for (i = 0; i < GW_SLOTS; i = i + 1)
		precache_pic (GW_Pic (i));
};

float() GW_Allowed =
{
	local float intro, demo, hp, owned;	// builtins are __variant: compare floats (Windows fteqcc emits double ops)

	intro = getstati (69);
	demo = isdemo ();
	if (inMenu || intermission || finale || intro != 0 || demo == TRUE || cvar ("bm_char_open") > 0)
		return FALSE;
	hp = getstati (STAT_HEALTH);
	owned = getstati (GW_HELD_STAT);
	return hp > 0 && owned > 0;
};

void() GW_Close =
{
	if (!gw_open)
		return;
	gw_open = FALSE;
	setsensitivityscale (1);
};

void() GW_Open =
{
	if (gw_open || !GW_Allowed ())
		return;
	gw_open = TRUE;
	gw_x = 0;
	gw_y = 0;
	gw_sel = -1;
	setsensitivityscale (0);
	localcmd ("-attack\n");		// fire held while opening kept shooting under the frozen view
};

// the key came up (or a click): equip the highlighted gun
void() GW_Pick =
{
	local float v;

	if (!gw_open)
		return;
	GW_Close ();
	if (gw_sel < 0 || !GW_Allowed ())
		return;
	v = GW_SlotStat (gw_sel);
	if (v < 2)
		return;				// not owned, not installed or out of ammo
	v = getstati (GW_HELD_STAT);
	if (v == gw_sel + 1)
		return;				// already in hand (asking again would inspect the Mega Man)
	localcmd (strcat ("impulse ", ftos (GW_Impulse (gw_sel)), "\n"));
};

// pointer movement in mouse counts; the slot under it, clockwise from 12 o'clock
void(float dx, float dy) GW_Move =
{
	local float len, ang;
	local vector v;

	if (!gw_open)
		return;
	gw_x = gw_x + dx;
	gw_y = gw_y + dy;
	len = sqrt (gw_x * gw_x + gw_y * gw_y);
	if (len > GW_REACH)
	{
		gw_x = gw_x * GW_REACH / len;
		gw_y = gw_y * GW_REACH / len;
		len = GW_REACH;
	}
	if (len < GW_DEAD)
	{
		gw_sel = -1;
		return;
	}
	v_x = 0 - gw_y;			// "forward" = up the screen
	v_y = gw_x;				// "left" in yaw terms = clockwise on screen
	v_z = 0;
	ang = vectoyaw (v) + 180 / GW_SLOTS;
	if (ang >= 360)
		ang = ang - 360;
	gw_sel = floor (ang * GW_SLOTS / 360);
};

// TRUE = the wheel used this input
float(float evtype, float key, float chr) GW_InputEvent =
{
	local float sens;

	if (evtype == 2)		// relative mouse motion: key and chr are dx, dy
	{
		if (!gw_open)
			return FALSE;
		sens = cvar ("bm_gunwheel_sens");
		if (sens <= 0)
			sens = 1;
		GW_Move (key * sens, chr * sens);
		return TRUE;
	}
	if (!gw_open || evtype != INPUT_KEYDOWN)
		return FALSE;
	if (key == K_ESCAPE)
	{
		GW_Close ();
		return TRUE;
	}
	if (key == K_MOUSE1)
	{
		GW_Pick ();
		return TRUE;
	}
	if (key == K_MWHEELUP || key == K_MWHEELDOWN)
		return TRUE;		// no weapon cycling under the open wheel
	return FALSE;
};

// before the scene is drawn: shut when no longer allowed, else keep the view still
void() GW_Frame =
{
	if (!gw_open)
		return;
	if (!GW_Allowed ())
	{
		GW_Close ();
		return;
	}
	setsensitivityscale (0);
};

// ---------------------------------------------------------------- drawing
// a point on the ring: angle clockwise from 12 o'clock, radius in screen-height units, xk keeps it round
vector(vector c, float deg, float r, float xk) GW_Point =
{
	local vector p;
	local float rad;

	rad = deg * 3.14159265 / 180;
	p_x = c_x + sin (rad) * r * xk;
	p_y = c_y - cos (rad) * r;
	p_z = 0;
	return p;
};

// an arc band from a0 to a1 degrees, between radii r0 and r1, with its own alpha at each radius
void(vector c, float a0, float a1, float r0, float r1, float xk, vector rgb, float al0, float al1) GW_Band =
{
	local float i, b0, b1, steps;

	steps = 4;
	for (i = 0; i < steps; i = i + 1)
	{
		b0 = a0 + (a1 - a0) * i / steps;
		b1 = a0 + (a1 - a0) * (i + 1) / steps;
		R_BeginPolygon ("", 0, TRUE);
		R_PolygonVertex (GW_Point (c, b0, r1, xk), '0 0 0', rgb, al1);
		R_PolygonVertex (GW_Point (c, b1, r1, xk), '1 0 0', rgb, al1);
		R_PolygonVertex (GW_Point (c, b1, r0, xk), '1 1 0', rgb, al0);
		R_PolygonVertex (GW_Point (c, b0, r0, xk), '0 1 0', rgb, al0);
		R_EndPolygon ();
	}
};

// centred, outlined, shrunk to fit maxw
void(vector c, float y, string s, float size, float maxw, vector rgb) GW_Text =
{
	local float w;
	local vector sz, pos;

	sz = '1 1 0' * size;
	w = stringwidth (s, TRUE, sz);
	if (w > maxw)
	{
		sz = sz * (maxw / w);
		w = maxw;
	}
	pos_x = c_x - w * 0.5;
	pos_y = y;
	pos_z = 0;
	drawstring (pos + '0.6 0.6 0', s, sz, '0 0 0', 0.9, 0);
	drawstring (pos, s, sz, rgb, 1, 0);
};

// cw, ch: 2D drawing units; pw, ph: window pixels
void(float cw, float ch, float pw, float ph) GW_Draw =
{
	local float i, v, ang, r0, r1, rm, xk, icon, alpha, held, px;
	local vector c, p, size, rgb, centre_rgb;
	local string pic, ammo;

	if (!gw_open)
		return;
	xk = 1;
	if (pw > 0 && ph > 0)
		xk = (cw / pw) / (ch / ph);
	c_x = cw * 0.5;
	c_y = ch * 0.5;
	c_z = 0;
	r0 = ch * 0.250;
	r1 = ch * 0.475;
	if (r1 * xk > cw * 0.48)		// very narrow windows
	{
		r0 = r0 * cw * 0.48 / (r1 * xk);
		r1 = cw * 0.48 / xk;
	}
	rm = (r0 + r1) * 0.5;
	icon = rm * 2 * 3.14159265 / GW_SLOTS * 1.10;
	px = 1;						// soft edge, 2D units
	if (ph > 0)
		px = 1.2 * ch / ph;
	held = getstati (GW_HELD_STAT);
	held = held - 1;

	for (i = 0; i < GW_SLOTS; i = i + 1)
	{
		ang = i * 360 / GW_SLOTS;
		v = GW_SlotStat (i);
		if (i == gw_sel)
		{
			rgb = '1 0.76 0.08';
			alpha = (v >= 2) ? 0.92 : 0.50;
		}
		else
		{
			rgb = (v >= 2) ? '0.10 0.17 0.30' : '0.05 0.06 0.09';
			alpha = 0.76;
		}
		GW_Band (c, ang - 8.8, ang + 8.8, r0, r1, xk, rgb, alpha, alpha);
		GW_Band (c, ang - 8.8, ang + 8.8, r1, r1 + px, xk, rgb, alpha, 0);
		GW_Band (c, ang - 8.8, ang + 8.8, r0 - px, r0, xk, rgb, 0, alpha);
		if (i == held)
			GW_Band (c, ang - 8.8, ang + 8.8, r1 + px * 2, r1 + ch * 0.014, xk, '1 1 1', 0.95, 0.95);
	}

	// a darker hub so the text reads over a busy scene
	for (i = 0; i < GW_SLOTS; i = i + 1)
	{
		ang = i * 360 / GW_SLOTS;
		GW_Band (c, ang - 9.5, ang + 9.5, 0, r0 - ch * 0.014, xk, '0.03 0.05 0.09', 0.62, 0.62);
	}

	size_x = icon * xk;
	size_y = icon;
	size_z = 0;
	for (i = 0; i < GW_SLOTS; i = i + 1)
	{
		v = GW_SlotStat (i);
		p = GW_Point (c, i * 360 / GW_SLOTS, rm, xk);
		pic = GW_Pic (i);
		rgb = (v >= 2) ? '1 1 1' : '0.35 0.35 0.4';
		alpha = (v >= 2) ? 1 : 0.7;
		if (draw_getimagesize (pic) == '0 0 0')
			GW_Text (p, p_y - ch * 0.011, GW_Name (i), ch * 0.022, icon * xk * 1.3, rgb);
		else
			drawpic (p - size * 0.5, pic, size, rgb, alpha, 0);
		// empty: a red 0 (a reloading gun with an empty magazine can still be drawn)
		if (v == 1 || v == 10)
			GW_Text (p, p_y + icon * 0.12, "0", ch * 0.036, icon, '1 0.2 0.15');
	}

	// the middle: what is under the pointer, else what is in hand
	i = gw_sel;
	if (i < 0)
		i = held;
	centre_rgb = '1 1 1';
	if (i >= 0 && i < GW_SLOTS)
	{
		v = GW_SlotStat (i);
		if (v == 0)
		{
			ammo = (i == 9 || i == 10) ? "NOT INSTALLED" : "NOT CARRIED";
			centre_rgb = '0.65 0.65 0.7';
		}
		else if (v == 1 || (v == 10 && i == 8))
		{
			ammo = "OUT OF AMMO";
			centre_rgb = '1 0.35 0.25';
		}
		else if (v == 2)
			ammo = "";
		else if (v == 10)
		{
			ammo = "EMPTY - reloads";
			centre_rgb = '1 0.55 0.3';
		}
		else
			ammo = strcat ("Ammo ", ftos (v - 10));
		GW_Text (c, c_y - ch * 0.110, GW_Name (i), ch * 0.060, r0 * xk * 1.7, '1 0.82 0.2');
		GW_Text (c, c_y - ch * 0.036, ammo, ch * 0.044, r0 * xk * 1.7, centre_rgb);
		GW_Text (c, c_y + ch * 0.030, GW_Desc (i, 0), ch * 0.040, r0 * xk * 1.65, '0.92 0.95 1');
		GW_Text (c, c_y + ch * 0.078, GW_Desc (i, 1), ch * 0.040, r0 * xk * 1.55, '0.92 0.95 1');
	}
	else
		GW_Text (c, c_y - ch * 0.018, "Pick a gun", ch * 0.040, r0 * xk * 1.7, '0.92 0.95 1');

	// where the mouse is pointing
	p_x = c_x + gw_x / GW_REACH * r0 * 0.9 * xk;
	p_y = c_y + gw_y / GW_REACH * r0 * 0.9;
	p_z = 0;
	GW_Band (p, 0, 180, 0, ch * 0.008, xk, '1 0.82 0.2', 0.95, 0.95);
	GW_Band (p, 180, 360, 0, ch * 0.008, xk, '1 0.82 0.2', 0.95, 0.95);
};
