/*
================
THE LAPTOP GUN - definitions (Combat+ only; it replaces the sniper rifle, which had replaced the nailgun)

Key 4 / IT_NAILGUN keeps its slot, item bit and nail magazine. You hold a laptop. Press fire and it types for a moment
(LTG_TYPE_TIME), then sends the big-eared head: a fast projectile that is steered by a laser, like the Half-Life
rocket launcher. A red dot (progs/sight.spr) sits wherever you aim and the head homes on it all the way. The head
wobbles left and right as it flies, is wrapped in network cables and wi-fi signals, and plays the "Canis Lupus" clip
(sound/ltgun/canis.wav) while it is in the air.
A hit does LTG_DAMAGE and shocks the victim for LTG_SHOCK_TIME seconds: they crawl at LTG_SHOCK_SPEED, cannot jump (like goo),
and are electrocuted LTG_ZAP_DMG every LTG_ZAP_EVERY seconds. Balance pass 2026-10-30: the head also homes on the nearest enemy it
sees (LTG_SEEK/LTG_CONE), ignoring the laser until it loses him for LTG_LOSE seconds.
Held model: progs/v_laptop.md3 (built by build_laptop_gun.py: 12 idle frames, 22 typing frames). cvar ltg_video 1 uses the video film instead
(progs/ltg_view.md3 + ltg_type_N.md3, build_ltgun_assets.py).
Other art: progs/ltg_view.md3 + ltg_view.md3 + ltg_type_N.md3 (held), ltg_p.md3 (in the hands), ltg_g.md3 (pickup), ltg_head.md3 (24 views
of the head, a card that turns to face each client), ltg_aura.md3 (cables and wi-fi); build_ltgun_assets.py.
================
*/

float	LTG_TYPE_TIME	= 0.8;		// seconds of typing before the head goes (the typing film: dial-up, typing, "HACKING 100%" at 0.8 s)
float	LTG_REFIRE		= 0.3;		// after the shot: the film's last 0.3 s (a hair short of its 0.34, so its first frame never flashes again), the laptop glowing hot
float	LTG_ANIM_FPS	= 42;		// the typing film: frames a second ...
float	LTG_ANIM_N		= 48;		// ... and frames in it (1.14 s: the video's 6 s at 5.25x). build_ltgun_assets.py writes the same numbers
float	LTG_VARIANTS	= 16;		// copies of the film, each starting at a different frame (see LtGun_VModel)
float	LTG_CLOCK_LAG	= 0.3;		// the client's shader clock runs about this far behind the server's `time` (measured on a local game)
float	LTG_SPEED		= 360;		// the head: a little faster than a running player (320), so a lock-on cannot simply be outrun
float	LTG_CANIS_VOL	= 0.6;
float	LTG_CANIS_GAP	= 8;		// one Canis Lupus at a time on the whole server: seven heads stacked it
float	ltg_canis_t;
float	LTG_SOUND_ATTN	= 1;		// "out of the projectile, not me": the clip comes from the head and fades with distance (ATTN_NONE played it in your own ears)
float	LTG_TURN			= 6;		// how hard it steers to the laser dot (per second)
float	LTG_TURN_LOCK	= 4;		// and to a locked enemy (a strafing player can still dodge at close range)
float	LTG_LIFE			= 8;
float	LTG_DAMAGE		= 40;		// was 12: the typing (0.8 s) has to buy something
float	LTG_RADIUS		= 80;		// anyone this close to the blast is shocked too
float	LTG_SHOCK_TIME	= 4;
float	LTG_SHOCK_SPEED	= 150;		// the shock now SLOWS: a shocked player crawls at this ground speed and cannot jump (like goo). Was a 700 sprint
float	LTG_ZAP_EVERY	= 0.5;
float	LTG_SEEK		= 1500;		// the head locks onto the nearest enemy this close that it can see ahead of it ...
float	LTG_CONE		= 0.5;		// ... within this cos of its heading (60 degrees each way)
float	LTG_LOSE		= 1.5;		// seconds without a line of sight before it gives its target up (then it follows the laser again)
float	LTG_ZAP_DMG		= 3;		// per zap (was 1)

float	ltg_fx_laser;		// the laser beam's particle effect
float	ltg_inflicting;		// TRUE while the laptop is dealing damage (obituary)

.float	ltg_phase;			// player: 1 while the laptop is typing
.float	ltg_t;				// player: when the typing is done
.float	ltg_sent;			// player: the head for this typing has gone
.float	ltg_var;			// player: which copy of the typing film is on (LtGun_Variant)
.float	ltg_shock;			// player: shocked until this time
.float	ltg_zap_t;			// player: next electrocution
.entity	ltg_by;				// player: who shocked them
.float	ltg_hint;			// player: shots so far that showed the "follow the laser" hint
.float	ltg_born;			// head: spawn time
.entity	ltg_dot;				// head: the laser dot
.entity	ltg_laser;			// head: the beam from the laptop to the dot
.entity	ltg_aura;			// head: the cables and wi-fi around it
.float	ltg_head;			// head: its heading in degrees (the customize function picks the picture from it)
.entity	ltg_lock;			// head: the enemy it is homing on (world = steer by the laser)
.float	ltg_blind;			// head: when it lost sight of ltg_lock
.float	ltg_wob;				// head: phase of the left-right wobble
.float	ltg_dot_t;				// head: throttle ltg_dot SVC particle rate

void() LtGun_Precache;
void() LtGun_Spawn;
void() LtGun_PlayerFrame;
float() LtGun_Frame;
string() LtGun_Death;
string(entity p) LtGun_VModel;
