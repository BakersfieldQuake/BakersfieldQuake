/*
================
THE WHEELMAN CANNON (fun gun 6, impulse 66, key G). Replaced the old impulse-18 Wheelman monster (2026-11-01).

Hold fire: the cannon charges for WC_CHARGE_TIME seconds (it fires by itself at full charge; let go earlier for a weaker shot).
It blasts a Wheelman along your aim, screaming (the Fire-Wheels frames of progs/wheelman.spr32; no fire effects of its own: the
trail of fire, the burning floor and the burn were removed 2026-11-01 because they hid the projectile). Where he crashes he blows up
with a normal rocket explosion (plus flying wheels, bars, gibs and sparks), and immediately bursts out running around at crazy speed
playing all 8 wild 360-degree Wheelman animations (progs/wheelman_dance.spr32).

Frames of progs/wheelman.spr32 (224 frames, 144x102 tight-cropped, type 2 SPR_VP_PARALLEL, see build_wheelman_sprite.py):
  0..7 idle   8 + d*6 + k driving   56 + d*4 + k screaming   88 + d*3 + k above90 (centered)
  112 + d*3 + k below90   136 + d*4 + k fire-wheels   168 + d*4 + k long bar   200 + d*3 + k above45 (centered)
  (d = 0..7: 0 = seen from the front, 4 = seen from behind)

Hooks: funguns.qc (tables, FunGun_Attack, FunGun_ViewFrame), bm_reload.qc (BM_FG6 magazine). Damage is dealt in the shooter's
name with fg_inflicting = FG_WCANNON, so frags and the obituary just work (wcannon.qc).
================
*/

float	WC_CHARGE_TIME	= 1.5;		// seconds of holding fire for a full charge
float	WC_MIN_CHARGE	= 0.12;		// let go before this and the shot is a fizzle (no Wheelman, no ammo spent)
float	WC_SPEED_MIN	= 600;		// units a second at the lowest charge (a rocket is 1000; was 1300 before the 2026-11-01 review)
float	WC_SPEED_MAX	= 1200;		// at full charge (was 2700)
float	WC_LIFE			= 6;		// a Wheelman that has not crashed by then blows up where he is
float	WC_HEALTH		= 80;		// he can be shot (he is a driving projectile, not a rocket): shot down, he blows up where he is
float	WC_STEPUP		= 32;		// he drives over curbs and downtown steps this high
float	WC_COOLDOWN		= 1.1;		// seconds after a shot for frames 26..47 (blast, recoil & breech lock) before reload/next charge
float	WC_DMG_DIRECT	= 75;		// extra damage to whatever he hits head-on
float	WC_DMG_BASE		= 145;		// radius damage of the smallest explosion (strong punch even on quick taps)
float	WC_DMG_STEP		= 35;		// more per tier (tier 3 = 250 splash, 325 direct)
float	WC_RADIUS_BASE	= 185;
float	WC_RADIUS_STEP	= 35;
float	WC_DOWN			= 0.7;		// aim this steeply down (the sine of the pitch) near the floor and he crashes at once under you: a rocket jump
float	WC_DANCE_LIFE	= 2.5;		// seconds Larry tears around playing crazy animations & shouting lines after exploding (progs/wheelman_dance.spr32)
float	WC_DANCE_SPEED	= 540;		// how fast he sprints around after crashing (a player runs at 320)
float	WC_SCALE		= 1.0417;	// the projectile sprite's scale (0.5 * 300/144; old 300x212 monster was 0.64 -> 1.3333)

float	WC_LINE_VOL		= 0.55;		// Larry's explosion clips and shouted lines
float	WC_SCREAM_VOL	= 0.5;		// his scream in flight
float	WC_SCREAM_GAP	= 3;		// seconds from one scream to the next (the clip is 1.4)
.float	wc_charging;	// player: when this charge began (0 = not charging)
.float	wc_msg;			// player: when the charge bar was last printed
.float	wc_cool;		// player: next charge may start at this time

.float	wc_air;			// shot: no floor under him (he screams)
.float	wc_speed;		// shot / survivor: his driving or sprinting speed
.float	wc_t;			// shot / survivor: when his physics last ran
.float	wc_anim;		// shot: 0..3; survivor: 0..7 (the 8 crazy post-crash animations)
.float	wc_dbg;			// shot: next position log line (cvar wc_debug)
.float	wc_anim_t;		// shot / survivor: when the animation is picked again
.vector	wc_dir;			// shot / survivor: the way he is heading (horizontal, unit)
.float	wc_tier;		// shot: 0..3 charge tier
.float	wc_t0;			// survivor: when the current crazy animation started
.float	wc_snd;			// shot / debris / survivor: when the next sound may play
.float	wc_until;		// debris / survivor: lifetime end

void() WC_Precache;
void() WC_PrecacheSprites;
void() WC_Press;
void() WC_Frame;
