/*
================
THE LAPTOP GUN - definitions (Combat+ only; it replaces the sniper rifle, which had replaced the nailgun)

Key 4 / IT_NAILGUN keeps its slot, item bit and nail magazine. You hold a laptop. Tap fire to send a fast homing
big-eared head, or hold fire to queue up a DDoS Flood salvo of up to LTG_MAX_QUEUE packets (one added every
LTG_QUEUE_STEP seconds) and release (or fill the queue) to fan them out in a rapid burst. No laser guidance:
the heads weave through the air and auto-lock onto visible enemies ahead (LTG_SEEK / LTG_CONE), dealing
direct + splash damage and shocking/slowing anyone caught in the blast.
Held model: progs/v_laptop.md3 (built by build_laptop_gun.py: 12 idle frames, 22 typing frames). cvar ltg_video 1 uses the video film instead
(progs/ltg_view.md3 + ltg_type_N.md3, build_ltgun_assets.py).
Other art: progs/ltg_view.md3 + ltg_view.md3 + ltg_type_N.md3 (held), ltg_p.md3 (in the hands), ltg_g.md3 (pickup), ltg_head.md3 (24 views
of the head, a card that turns to face each client), ltg_aura.md3 (cables and wi-fi); build_ltgun_assets.py.
================
*/

float	LTG_TYPE_TIME	= 0.22;		// snappy initial typing windup before packet #1 is ready
float	LTG_QUEUE_STEP	= 0.18;		// seconds per additional queued DDoS packet while holding fire
float	LTG_MAX_QUEUE	= 3;		// maximum packets queued in one DDoS Flood salvo
float	LTG_SALVO_GAP	= 0.06;		// rapid-fire stagger between heads in a burst salvo
float	LTG_REFIRE		= 0.22;		// cooldown after the last head in a salvo launches
float	LTG_ANIM_FPS	= 42;		// the typing film: frames a second ...
float	LTG_ANIM_N		= 48;		// ... and frames in it (1.14 s: the video's 6 s at 5.25x). build_ltgun_assets.py writes the same numbers
float	LTG_VARIANTS	= 16;		// copies of the film, each starting at a different frame (see LtGun_VModel)
float	LTG_CLOCK_LAG	= 0.3;		// the client's shader clock runs about this far behind the server's `time` (measured on a local game)
float	LTG_SPEED		= 880;		// fast fire-and-forget DDoS packet speed (was 620)
float	LTG_CANIS_VOL	= 0.6;
float	LTG_CANIS_GAP	= 8;		// one Canis Lupus at a time on the whole server: seven heads stacked it
float	ltg_canis_t;
float	LTG_SOUND_ATTN	= 1;		// "out of the projectile, not me": the clip comes from the head and fades with distance (ATTN_NONE played it in your own ears)
float	LTG_TURN_LOCK	= 7.0;		// homing turn rate onto a locked enemy (strong curve without laser babysitting)
float	LTG_LIFE		= 7;
float	LTG_DAMAGE		= 32;		// direct hit damage per head (full 5-head salvo = 160 direct + shock)
float	LTG_SPLASH_DMG	= 24;		// radius splash damage on wall/floor/target impact
float	LTG_RADIUS		= 110;		// anyone this close to the blast is shocked too
float	LTG_SHOCK_TIME	= 1.1;		// lag shock duration (snappy slow without feeling stuck in mud)
float	LTG_SHOCK_SPEED	= 215;		// ground slow while still allowing jumps & rocket-jumps
float	LTG_ZAP_EVERY	= 0.45;
float	LTG_SEEK		= 1600;		// the head locks onto the nearest enemy this close that it can see ahead of it ...
float	LTG_CONE		= 0.35;		// ... within this cos of its heading (~70 degrees each way)
float	LTG_LOSE		= 1.5;		// seconds without a line of sight before it drops lock
float	LTG_ZAP_DMG		= 4;		// per zap (was 3)

float	ltg_inflicting;		// TRUE while the laptop is dealing damage (obituary)

.float	ltg_phase;			// player: 0 idle, 1 queuing packets, 2 unleashing DDoS salvo
.float	ltg_t;				// player: earliest fire time (phase 1) / refire end time (phase 2)
.float	ltg_queue;			// player: packets currently queued for this salvo
.float	ltg_qmax;			// player: max packets available for this salvo
.float	ltg_qnext;			// player: next queue tick (phase 1) / next burst head time (phase 2)
.float	ltg_salvo_idx;		// player: index of current head launching in salvo
.float	ltg_salvo_total;	// player: total heads in the releasing salvo
.float	ltg_var;			// player: which copy of the typing film is on (LtGun_Variant)
.float	ltg_shock;			// player: shocked until this time
.float	ltg_immune_t;		// player: post-shock re-stun immunity until this time
.float	ltg_zap_t;			// player: next electrocution
.entity	ltg_by;				// player: who shocked them
.float	ltg_hint;			// player: shots so far that showed the DDoS Flood hint
.float	ltg_born;			// head: spawn time
.entity	ltg_aura;			// head: the cables and wi-fi around it
.float	ltg_head;			// head: its heading in degrees (the customize function picks the picture from it)
.entity	ltg_lock;			// head: the enemy it is homing on
.float	ltg_blind;			// head: when it lost sight of ltg_lock
.float	ltg_wob;			// head: phase of the left-right wobble
.vector	ltg_weave_r;		// head: lateral axis for unlocked packet S-curve weave
.float	ltg_weave_amp;		// head: weave strength while seeking (0 = dead straight)

void() LtGun_Precache;
void() LtGun_Spawn;
void() LtGun_PlayerFrame;
float() LtGun_Frame;
string() LtGun_Death;
string(entity p) LtGun_VModel;
